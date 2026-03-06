"""
Router analize — upload PDF analize laborator + procesare + stocare biomarkeri
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from core.database import get_db
from core.security import get_current_user, require_doctor

router = APIRouter()


class BiomarkerOut(BaseModel):
    name: str
    value: Optional[float]
    unit: Optional[str]
    ref_min: Optional[float]
    ref_max: Optional[float]
    lab_name: Optional[str]
    tested_at: date
    confidence: str


class AnalysisUploadResponse(BaseModel):
    job_id: str
    status: str
    message: str


@router.post("/{patient_id}/upload", response_model=AnalysisUploadResponse)
async def upload_analysis(
    patient_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload PDF analiză de laborator.
    Pipeline:
    1. Validare fișier (PDF, max 10MB)
    2. Salvare temporară
    3. Extragere text (pdfplumber / docling)
    4. Identificare biomarkeri cu LLM (structurat, nu halucinare)
    5. validated_write() în patient_{uuid}.biomarkers
    6. Generare notificare doctor dacă există valori out-of-range
    """
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Only PDF, JPEG, PNG accepted")

    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # TODO: trimite la queue Redis pentru procesare asincronă
    # job_id = await analysis_queue.enqueue(patient_id, file)
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{patient_id}/biomarkers", response_model=list[BiomarkerOut])
async def get_biomarkers(
    patient_id: UUID,
    name: Optional[str] = None,     # filtru după nume biomarker
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Returnează biomarkerii pacientului din patient_{uuid}.biomarkers.
    Ordonat: cele mai recente mai întâi.
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{patient_id}/biomarkers/{name}/trend")
async def get_biomarker_trend(
    patient_id: UUID,
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Trend temporal pentru un biomarker specific — date pentru grafic în mobile app."""
    raise HTTPException(status_code=501, detail="Not implemented yet")
