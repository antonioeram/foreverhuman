"""
Router senzori — ingestion date Withings, Ultrahuman, Apple Health
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Literal
from datetime import datetime, date

from core.database import get_db
from core.security import get_current_user

router = APIRouter()


class SensorReading(BaseModel):
    source: Literal["withings", "ultrahuman", "apple_health"]
    metric: str
    value: Optional[float] = None
    value_json: Optional[dict] = None
    unit: Optional[str] = None
    recorded_at: datetime


class SensorBulkIngestion(BaseModel):
    patient_id: UUID
    readings: list[SensorReading]


@router.post("/ingest")
async def ingest_sensor_data(
    body: SensorBulkIngestion,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Ingestion bulk date senzori — apelat de n8n pipelines (sensor-agent).
    Fiecare reading trece prin validated_write() → audit_log.

    Alertele sunt evaluate automat după ingestion:
    - HRV < 20ms → alert
    - Recovery < 30 → alert
    - Tensiune systolică > 140 → alert
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{patient_id}/latest")
async def get_latest_sensor_data(
    patient_id: UUID,
    metrics: Optional[str] = None,    # "HRV,weight,sleep_score" — CSV
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Cele mai recente valori per metric — pentru dashboard pacient."""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{patient_id}/trend")
async def get_sensor_trend(
    patient_id: UUID,
    metric: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Date istorice pentru un metric — pentru grafice în mobile app."""
    raise HTTPException(status_code=501, detail="Not implemented yet")
