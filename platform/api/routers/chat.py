"""
Router chat — conversație cu agentul personal al pacientului (LangGraph + Mem0)
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from core.security import get_current_user

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None   # None = sesiune nouă


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: list[str] = []            # surse citate de agent


@router.post("/{patient_id}/message", response_model=ChatResponse)
async def send_message(
    patient_id: UUID,
    body: ChatMessage,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Trimite un mesaj agentului pacientului.
    - Rulează Session Boot Protocol la sesiune nouă
    - LangGraph procesează în noduri (citire MEMORY → interpretare → răspuns)
    - Mem0 persistă memoria între sesiuni
    - Răspunsul include surse citate (conform SOUL.md — Regula sursei)
    """
    # TODO:
    # 1. Verifică că patient_id aparține clinicii din JWT
    # 2. Inițializează LangGraph agent pentru patient_id
    # 3. Dacă session_id e nou → rulează session_boot()
    # 4. Procesează mesajul prin LangGraph
    # 5. Returnează răspunsul cu surse
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{patient_id}/message/stream")
async def send_message_stream(
    patient_id: UUID,
    body: ChatMessage,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Streaming SSE — răspunsul agentului vine token cu token.
    Preferat pentru UX în mobile app.
    """
    async def event_generator():
        # TODO: LangGraph streaming output
        yield "data: {\"token\": \"Not implemented yet\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{patient_id}/history")
async def get_chat_history(
    patient_id: UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Istoricul conversațiilor (din Mem0 + PostgreSQL checkpoints LangGraph)."""
    raise HTTPException(status_code=501, detail="Not implemented yet")
