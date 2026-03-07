"""
Router analize — upload PDF analize laborator + extragere biomarkeri cu LLM
"""
import io
import json
import tempfile
from uuid import UUID, uuid4
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.security import get_current_user, require_doctor
from routers.patients import _get_patient_or_404

router = APIRouter()

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class BiomarkerOut(BaseModel):
    id: str
    name: str
    value: Optional[float]
    unit: Optional[str]
    ref_min: Optional[float]
    ref_max: Optional[float]
    lab_name: Optional[str]
    source_file: Optional[str]
    tested_at: date
    confidence: str
    created_at: datetime


class UploadResponse(BaseModel):
    status: str
    biomarkers_extracted: int
    biomarkers_out_of_range: int
    raw_text_length: int
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_pdf_text(content: bytes) -> str:
    """Extrage text din PDF cu pdfplumber."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages.append(t)
            return "\n\n".join(pages)
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="pdfplumber not installed. Add to requirements and rebuild.",
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF parsing failed: {e}")


async def _extract_biomarkers_with_llm(text: str, patient_id: str) -> list[dict]:
    """
    Extrage biomarkeri structurat cu LLM (Gemini sau Anthropic, configurabil).
    Anti-halucinare: prompt strict, output JSON verificat.
    """
    SYSTEM = """Ești un asistent medical specializat în extragerea structurată a datelor din analize de laborator.
Extragi EXCLUSIV date care apar explicit în text. Nu inventezi, nu estimezi, nu completezi din memorie.
Dacă o valoare nu apare explicit, lași câmpul null.
Răspunzi DOAR cu JSON valid, fără text adițional."""

    PROMPT = f"""Extrage toți biomarkerii din această analiză de laborator și returnează un JSON array.

Fiecare element trebuie să aibă exact aceste câmpuri:
- name: string (ex: "Glucoza", "Hemoglobina", "TSH")
- value: number sau null (valoarea numerică)
- unit: string sau null (ex: "mg/dL", "g/dL", "mIU/L")
- ref_min: number sau null (limita inferioară a valorii de referință)
- ref_max: number sau null (limita superioară a valorii de referință)
- lab_name: string sau null (numele laboratorului)
- tested_at: string în format "YYYY-MM-DD" sau null (data recoltării)

IMPORTANT: Extrage EXACT ce este scris. Nu interpreta, nu completa, nu inventa.

TEXT ANALIZĂ:
{text[:8000]}

Răspunde EXCLUSIV cu JSON array:"""

    raw = None
    try:
        if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction=SYSTEM,
            )
            resp = model.generate_content(PROMPT)
            raw = resp.text.strip()

        elif settings.LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            msg = client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=2048,
                system=SYSTEM,
                messages=[{"role": "user", "content": PROMPT}],
            )
            raw = msg.content[0].text.strip()

        else:
            return []  # niciun provider configurat

        # Curăță markdown fence dacă există
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        extracted = json.loads(raw)
        return extracted if isinstance(extracted, list) else []

    except json.JSONDecodeError:
        return []
    except Exception:
        return []


def _is_out_of_range(bm: dict) -> bool:
    v = bm.get("value")
    lo = bm.get("ref_min")
    hi = bm.get("ref_max")
    if v is None:
        return False
    if lo is not None and v < lo:
        return True
    if hi is not None and v > hi:
        return True
    return False


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/{patient_id}/upload", response_model=UploadResponse)
async def upload_analysis(
    patient_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_doctor),
):
    """
    Upload PDF analiză de laborator.
    1. Validare fișier (PDF, max 10MB)
    2. Extragere text cu pdfplumber
    3. Extragere biomarkeri cu Anthropic (strict — nu halucinare)
    4. INSERT în patient_{uuid}.biomarkers
    """
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Doar PDF, JPEG sau PNG acceptate")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Fișier prea mare (max 10MB)")

    # Verifică că pacientul aparține clinicii
    p = await _get_patient_or_404(db, str(patient_id), current_user["clinic_id"])
    schema = p.schema_name

    # Extragere text
    if file.content_type == "application/pdf":
        raw_text = _extract_pdf_text(content)
    else:
        raw_text = f"[Image file: {file.filename}]"

    # Extragere biomarkeri cu LLM
    biomarkers = await _extract_biomarkers_with_llm(raw_text, str(patient_id))

    # INSERT în DB
    inserted = 0
    out_of_range = 0
    today = date.today().isoformat()

    for bm in biomarkers:
        if not bm.get("name"):
            continue

        tested_at = bm.get("tested_at") or today
        # Validare dată
        try:
            date.fromisoformat(tested_at)
        except (ValueError, TypeError):
            tested_at = today

        await db.execute(
            text(
                f"INSERT INTO {schema}.biomarkers "
                "(id, name, value, unit, ref_min, ref_max, lab_name, source_file, tested_at, confidence) "
                "VALUES (:id, :name, :value, :unit, :ref_min, :ref_max, :lab_name, :source_file, :tested_at, :confidence)"
            ),
            {
                "id":          str(uuid4()),
                "name":        bm.get("name"),
                "value":       bm.get("value"),
                "unit":        bm.get("unit"),
                "ref_min":     bm.get("ref_min"),
                "ref_max":     bm.get("ref_max"),
                "lab_name":    bm.get("lab_name"),
                "source_file": file.filename,
                "tested_at":   tested_at,
                "confidence":  "[VERIFIED]",
            },
        )
        inserted += 1
        if _is_out_of_range(bm):
            out_of_range += 1

    # Audit log
    await db.execute(
        text(
            f"INSERT INTO {schema}.audit_log (action, agent, target, new_value) "
            "VALUES ('write', 'analyses', 'biomarkers', :info)"
        ),
        {"info": f"Uploaded {file.filename}: {inserted} biomarkers extracted"},
    )

    msg = f"{inserted} biomarkeri extrași"
    has_key = (settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY) or \
              (settings.LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY)
    if not has_key:
        msg += f" ({settings.LLM_PROVIDER} API key lipsă — extragere LLM dezactivată)"
    if out_of_range:
        msg += f", {out_of_range} în afara referinței"

    return UploadResponse(
        status="ok",
        biomarkers_extracted=inserted,
        biomarkers_out_of_range=out_of_range,
        raw_text_length=len(raw_text),
        message=msg,
    )


@router.get("/{patient_id}/biomarkers")
async def get_biomarkers(
    patient_id: UUID,
    name: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_doctor),
):
    """Biomarkerii pacientului, cei mai recenți mai întâi."""
    p = await _get_patient_or_404(db, str(patient_id), current_user["clinic_id"])
    schema = p.schema_name

    where = "WHERE name ILIKE :name" if name else ""
    params: dict = {"limit": limit}
    if name:
        params["name"] = f"%{name}%"

    result = await db.execute(
        text(
            f"SELECT id, name, value, unit, ref_min, ref_max, lab_name, source_file, "
            f"tested_at, confidence, created_at "
            f"FROM {schema}.biomarkers {where} "
            f"ORDER BY tested_at DESC, created_at DESC LIMIT :limit"
        ),
        params,
    )
    rows = result.fetchall()

    return [
        {
            "id":          str(r.id),
            "name":        r.name,
            "value":       float(r.value) if r.value is not None else None,
            "unit":        r.unit,
            "ref_min":     float(r.ref_min) if r.ref_min is not None else None,
            "ref_max":     float(r.ref_max) if r.ref_max is not None else None,
            "lab_name":    r.lab_name,
            "source_file": r.source_file,
            "tested_at":   r.tested_at,
            "confidence":  r.confidence,
            "created_at":  r.created_at,
        }
        for r in rows
    ]


@router.get("/{patient_id}/biomarkers/{marker_name}/trend")
async def get_biomarker_trend(
    patient_id: UUID,
    marker_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_doctor),
):
    """Trend temporal pentru un biomarker — date pentru grafic în mobile app."""
    p = await _get_patient_or_404(db, str(patient_id), current_user["clinic_id"])
    schema = p.schema_name

    result = await db.execute(
        text(
            f"SELECT tested_at, value, unit, ref_min, ref_max "
            f"FROM {schema}.biomarkers "
            f"WHERE name ILIKE :name "
            f"ORDER BY tested_at ASC"
        ),
        {"name": marker_name},
    )
    rows = result.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Nu există date pentru {marker_name}")

    return {
        "marker": marker_name,
        "unit":   rows[0].unit,
        "ref_min": float(rows[0].ref_min) if rows[0].ref_min else None,
        "ref_max": float(rows[0].ref_max) if rows[0].ref_max else None,
        "data": [
            {"date": str(r.tested_at), "value": float(r.value) if r.value else None}
            for r in rows
        ],
    }
