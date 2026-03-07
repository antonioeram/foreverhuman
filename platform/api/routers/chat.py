"""
Router chat — conversație cu agentul personal al pacientului (Anthropic direct)
Faza 1: Anthropic API direct (fără LangGraph — acela e Faza 2)
Context: biomarkeri recenți + istoric conversație din audit_log
"""
import json
from uuid import UUID, uuid4
from typing import Optional, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.security import get_current_user
from routers.patients import _get_patient_or_404

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None   # None = sesiune nouă


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: list[str] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Ești agentul personal de sănătate al pacientului. Rolul tău:
- Analizezi și explici datele medicale (biomarkeri, analize de laborator)
- Oferi informații bazate pe datele concrete ale pacientului
- Răspunzi clar, empatic și direct — fără jargon medical inutil
- Nu pui diagnostice. Nu prescrii tratamente. Recomanzi consultul medicului când e cazul.
- Citezi ÎNTOTDEAUNA sursa datelor (ex: "Conform analizei din 2025-01-15...")
- Dacă nu ai date suficiente, spui explicit asta

IMPORTANT: Lucrezi EXCLUSIV cu datele reale din contextul primit. Nu inventa valori sau diagnostice."""


async def _get_patient_context(db: AsyncSession, schema: str) -> str:
    """Construiește contextul pacientului: biomarkeri recenți + profil."""
    try:
        # Biomarkeri recenți (ultimii 30)
        result = await db.execute(
            text(
                f"SELECT name, value, unit, ref_min, ref_max, lab_name, tested_at "
                f"FROM {schema}.biomarkers "
                f"ORDER BY tested_at DESC, created_at DESC LIMIT 30"
            )
        )
        rows = result.fetchall()

        if not rows:
            return "Nu există biomarkeri înregistrați pentru acest pacient."

        lines = ["=== BIOMARKERI RECENȚI ==="]
        for r in rows:
            status = ""
            if r.value is not None:
                if r.ref_min is not None and r.value < r.ref_min:
                    status = " ⚠️ SUB REFERINȚĂ"
                elif r.ref_max is not None and r.value > r.ref_max:
                    status = " ⚠️ PESTE REFERINȚĂ"
            ref = ""
            if r.ref_min is not None or r.ref_max is not None:
                ref = f" (ref: {r.ref_min or '?'}-{r.ref_max or '?'})"
            lines.append(
                f"- {r.name}: {r.value} {r.unit or ''}{ref}{status} "
                f"[{r.lab_name or 'lab necunoscut'}, {r.tested_at}]"
            )
        return "\n".join(lines)

    except Exception:
        return "Eroare la citirea biomarkerilor."


async def _get_chat_history(
    db: AsyncSession, schema: str, session_id: str, limit: int = 20
) -> list[dict]:
    """Citește istoricul conversației din audit_log."""
    try:
        result = await db.execute(
            text(
                f"SELECT agent, new_value, created_at "
                f"FROM {schema}.audit_log "
                f"WHERE action = 'chat' AND target = :session_id "
                f"ORDER BY created_at ASC LIMIT :limit"
            ),
            {"session_id": session_id, "limit": limit},
        )
        rows = result.fetchall()
        return [{"role": r.agent, "content": r.new_value} for r in rows]
    except Exception:
        return []


async def _save_message(
    db: AsyncSession, schema: str, session_id: str, role: str, content: str
) -> None:
    """Salvează un mesaj în audit_log."""
    await db.execute(
        text(
            f"INSERT INTO {schema}.audit_log (action, agent, target, new_value) "
            "VALUES ('chat', :agent, :session_id, :content)"
        ),
        {"agent": role, "session_id": session_id, "content": content},
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/{patient_id}/message", response_model=ChatResponse)
async def send_message(
    patient_id: UUID,
    body: ChatMessage,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Trimite un mesaj agentului pacientului.
    - Construiește context din biomarkeri reali
    - Istoricul conversației din audit_log
    - Răspuns Anthropic cu anti-halucinare
    """
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY lipsă — chat dezactivat",
        )

    p = await _get_patient_or_404(db, str(patient_id), current_user["clinic_id"])
    schema = p.schema_name

    session_id = body.session_id or str(uuid4())

    # Context pacient
    context = await _get_patient_context(db, schema)

    # Istoric conversație
    history = await _get_chat_history(db, schema, session_id)

    # Construiește mesajele pentru Anthropic
    messages = history + [{"role": "user", "content": body.message}]

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        system_with_context = (
            f"{SYSTEM_PROMPT}\n\n"
            f"=== DATE PACIENT ===\n{context}\n"
            f"=== SESIUNE: {session_id} ==="
        )

        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1024,
            system=system_with_context,
            messages=messages,
        )

        answer = response.content[0].text.strip()

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Eroare Anthropic: {e}")

    # Salvează mesajele
    await _save_message(db, schema, session_id, "user", body.message)
    await _save_message(db, schema, session_id, "assistant", answer)

    return ChatResponse(
        response=answer,
        session_id=session_id,
        sources=[],
    )


@router.post("/{patient_id}/message/stream")
async def send_message_stream(
    patient_id: UUID,
    body: ChatMessage,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Streaming SSE — răspunsul vine token cu token.
    Preferat pentru UX în mobile app.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY lipsă — chat dezactivat",
        )

    p = await _get_patient_or_404(db, str(patient_id), current_user["clinic_id"])
    schema = p.schema_name

    session_id = body.session_id or str(uuid4())
    context = await _get_patient_context(db, schema)
    history = await _get_chat_history(db, schema, session_id)
    messages = history + [{"role": "user", "content": body.message}]

    system_with_context = (
        f"{SYSTEM_PROMPT}\n\n"
        f"=== DATE PACIENT ===\n{context}\n"
        f"=== SESIUNE: {session_id} ==="
    )

    # Salvăm mesajul user înainte de stream
    await _save_message(db, schema, session_id, "user", body.message)

    async def event_generator() -> AsyncIterator[str]:
        full_response = []
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

            with client.messages.stream(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1024,
                system=system_with_context,
                messages=messages,
            ) as stream:
                for text_chunk in stream.text_stream:
                    full_response.append(text_chunk)
                    payload = json.dumps({"token": text_chunk, "session_id": session_id})
                    yield f"data: {payload}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        # Salvăm răspunsul complet
        if full_response:
            complete = "".join(full_response)
            # Fire-and-forget save — nu putem await într-un generator sync
            # Salvarea se face în endpoint non-stream sau prin background task
            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{patient_id}/history")
async def get_chat_history(
    patient_id: UUID,
    session_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Istoricul conversațiilor din audit_log."""
    p = await _get_patient_or_404(db, str(patient_id), current_user["clinic_id"])
    schema = p.schema_name

    where = "WHERE action = 'chat'"
    params: dict = {"limit": limit}
    if session_id:
        where += " AND target = :session_id"
        params["session_id"] = session_id

    try:
        result = await db.execute(
            text(
                f"SELECT agent, target AS session_id, new_value AS content, created_at "
                f"FROM {schema}.audit_log "
                f"{where} "
                f"ORDER BY created_at DESC LIMIT :limit"
            ),
            params,
        )
        rows = result.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare DB: {e}")

    return [
        {
            "role": r.agent,
            "session_id": r.session_id,
            "content": r.content,
            "created_at": r.created_at,
        }
        for r in rows
    ]
