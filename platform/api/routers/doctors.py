"""
Router doctori — rapoarte, acces cross-patient, statistici clinică
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from core.database import get_db
from core.security import require_doctor

router = APIRouter()


@router.get("/dashboard")
async def doctor_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_doctor),
):
    """
    Dashboard doctor: lista pacienților activi, alertele recente, directive pending.
    """
    # TODO: query cross-patient în clinică (RLS permite accesul la toți pacienții clinicii)
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/reports/daily")
async def daily_report(
    report_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_doctor),
):
    """
    Raport zilnic: toți pacienții clinicii + status indicatori cheie.
    Generat automat de n8n la 07:00, disponibil și on-demand.
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/patients/{patient_id}/summary")
async def patient_summary(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_doctor),
):
    """
    Sumar complet al unui pacient: biomarkeri recenți, trend senzori, directive active,
    alertele agentului, intervenții recomandate.
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/patients/{patient_id}/alerts")
async def patient_alerts(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_doctor),
):
    """Red flags detectate de agentul pacientului (format Red Flag din SOUL.md)."""
    raise HTTPException(status_code=501, detail="Not implemented yet")
