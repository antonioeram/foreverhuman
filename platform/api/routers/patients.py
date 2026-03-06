"""
Router pacienți — CRUD + export GDPR + delete GDPR
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from core.database import get_db
from core.security import get_current_user, require_doctor, require_clinic_admin

router = APIRouter()


class PatientCreate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    phone: Optional[str] = None


class PatientOut(BaseModel):
    id: UUID
    email: Optional[str]
    first_name: str
    last_name: str
    date_of_birth: Optional[date]
    sex: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/", dependencies=[Depends(require_doctor)])
async def list_patients(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Lista pacienților clinicii curente. RLS asigură izolarea automată."""
    # TODO: query SELECT * FROM public.patients WHERE clinic_id = $1
    return {"patients": [], "total": 0}


@router.post("/", dependencies=[Depends(require_clinic_admin)])
async def create_patient(body: PatientCreate, db: AsyncSession = Depends(get_db)):
    """Creare pacient nou + creare automată schema PostgreSQL dedicată."""
    # TODO:
    # 1. INSERT INTO public.patients (...)
    # 2. Trigger PostgreSQL creează patient_{uuid} schema automat
    # 3. Returnează pacientul creat
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{patient_id}", dependencies=[Depends(require_doctor)])
async def get_patient(patient_id: UUID, db: AsyncSession = Depends(get_db)):
    """Profil complet pacient (date din patient_{uuid}.profile + ultimii biomarkeri)."""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{patient_id}/export")
async def export_patient_data(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    GDPR Art. 20 — Export complet date pacient în format JSON.
    Pacientul poate accesa propriile date; doctorul poate exporta pentru pacienții clinicii.
    """
    # TODO: extrage tot din patient_{uuid}.* și returnează JSON structurat
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/{patient_id}", dependencies=[Depends(require_clinic_admin)])
async def delete_patient_gdpr(patient_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    GDPR Art. 17 — Ștergere completă date pacient.
    Apelează funcția PostgreSQL delete_patient_gdpr() — cascade pe toată schema.
    """
    # TODO: EXECUTE delete_patient_gdpr($1)
    # TODO: șterge namespace LanceDB patient_{uuid}
    # TODO: loghează în audit: GDPR_DELETE cu timestamp
    raise HTTPException(status_code=501, detail="Not implemented yet")
