"""
Router pacienți — CRUD + export GDPR + delete GDPR
"""
from uuid import UUID, uuid4
from typing import Optional
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db, set_clinic_context
from core.security import get_current_user, require_doctor, require_clinic_admin

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PatientCreate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None          # M / F / O
    phone: Optional[str] = None
    consent_version: Optional[str] = "1.0"


class PatientUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class PatientOut(BaseModel):
    id: str
    clinic_id: str
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[date]
    sex: Optional[str]
    phone: Optional[str]
    is_active: bool
    schema_name: str
    consent_at: Optional[datetime]
    created_at: datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_patient_or_404(db: AsyncSession, patient_id: str, clinic_id: str):
    result = await db.execute(
        text(
            "SELECT id, clinic_id, email, first_name, last_name, date_of_birth, sex, "
            "phone, is_active, schema_name, consent_at, created_at "
            "FROM public.patients WHERE id = :id AND clinic_id = :clinic_id"
        ),
        {"id": patient_id, "clinic_id": clinic_id},
    )
    p = result.fetchone()
    if not p:
        raise HTTPException(status_code=404, detail="Pacient negăsit în această clinică")
    return p


def _row_to_dict(p) -> dict:
    return {
        "id":            str(p.id),
        "clinic_id":     str(p.clinic_id),
        "email":         p.email,
        "first_name":    p.first_name,
        "last_name":     p.last_name,
        "date_of_birth": p.date_of_birth,
        "sex":           p.sex,
        "phone":         p.phone,
        "is_active":     p.is_active,
        "schema_name":   p.schema_name,
        "consent_at":    p.consent_at,
        "created_at":    p.created_at,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/")
async def list_patients(
    active_only: bool = True,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_doctor),
):
    """Lista pacienților clinicii curente. RLS filtrează automat după clinic_id din JWT."""
    await set_clinic_context(db, current_user["clinic_id"])

    result = await db.execute(
        text(
            "SELECT id, clinic_id, email, first_name, last_name, date_of_birth, sex, "
            "phone, is_active, schema_name, consent_at, created_at "
            "FROM public.patients "
            "WHERE clinic_id = :clinic_id "
            + ("AND is_active = true " if active_only else "")
            + "ORDER BY last_name, first_name "
            "LIMIT :limit OFFSET :offset"
        ),
        {"clinic_id": current_user["clinic_id"], "limit": limit, "offset": offset},
    )
    rows = result.fetchall()

    count_res = await db.execute(
        text(
            "SELECT COUNT(*) FROM public.patients WHERE clinic_id = :clinic_id"
            + (" AND is_active = true" if active_only else "")
        ),
        {"clinic_id": current_user["clinic_id"]},
    )
    total = count_res.scalar()

    return {"patients": [_row_to_dict(r) for r in rows], "total": total}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_patient(
    body: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_clinic_admin),
):
    """
    Creare pacient nou.
    Trigger-ul PostgreSQL `after_patient_insert` creează automat schema `patient_{uuid}`.
    """
    new_id = str(uuid4())
    now    = datetime.now(timezone.utc)

    await db.execute(
        text(
            "INSERT INTO public.patients "
            "(id, clinic_id, email, first_name, last_name, date_of_birth, sex, phone, "
            " consent_at, consent_version) "
            "VALUES (:id, :clinic_id, :email, :first_name, :last_name, :dob, :sex, :phone, "
            "        :consent_at, :consent_version)"
        ),
        {
            "id":              new_id,
            "clinic_id":       current_user["clinic_id"],
            "email":           body.email,
            "first_name":      body.first_name,
            "last_name":       body.last_name,
            "dob":             body.date_of_birth,
            "sex":             body.sex,
            "phone":           body.phone,
            "consent_at":      now,
            "consent_version": body.consent_version,
        },
    )

    # Loghează consimțământul (schema reală: consent_type, granted, doc_version)
    await db.execute(
        text(
            "INSERT INTO public.consent_log (id, patient_id, consent_type, granted, doc_version, ip_address) "
            "VALUES (:id, :patient_id, 'data_processing', true, :version, '127.0.0.1')"
        ),
        {"id": str(uuid4()), "patient_id": new_id, "version": body.consent_version},
    )

    return _row_to_dict(await _get_patient_or_404(db, new_id, current_user["clinic_id"]))


@router.get("/{patient_id}")
async def get_patient(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_doctor),
):
    """Profil pacient + ultimii biomarkeri din schema dedicată."""
    p = await _get_patient_or_404(db, str(patient_id), current_user["clinic_id"])
    data = _row_to_dict(p)

    # Obține ultimii biomarkeri din schema dedicată pacientului
    try:
        schema = p.schema_name
        bm_res = await db.execute(
            text(
                f"SELECT marker_name, value, unit, measured_at "
                f"FROM {schema}.biomarkers "
                f"ORDER BY measured_at DESC LIMIT 20"
            )
        )
        biomarkers = [
            {
                "marker": r.marker_name,
                "value":  r.value,
                "unit":   r.unit,
                "at":     r.measured_at,
            }
            for r in bm_res.fetchall()
        ]
    except Exception:
        biomarkers = []

    data["recent_biomarkers"] = biomarkers
    return data


@router.patch("/{patient_id}")
async def update_patient(
    patient_id: UUID,
    body: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_clinic_admin),
):
    """Actualizare date demografice pacient."""
    # Verifică că pacientul există
    await _get_patient_or_404(db, str(patient_id), current_user["clinic_id"])

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nicio modificare furnizată")

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["patient_id"] = str(patient_id)
    updates["clinic_id"]  = current_user["clinic_id"]

    await db.execute(
        text(
            f"UPDATE public.patients SET {set_clause}, updated_at = NOW() "
            f"WHERE id = :patient_id AND clinic_id = :clinic_id"
        ),
        updates,
    )

    return _row_to_dict(await _get_patient_or_404(db, str(patient_id), current_user["clinic_id"]))


@router.get("/{patient_id}/export")
async def export_patient_data(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    GDPR Art. 20 — Export complet date pacient în format JSON.
    Doctor poate exporta pentru pacienții clinicii sale.
    """
    p = await _get_patient_or_404(db, str(patient_id), current_user["clinic_id"])
    schema = p.schema_name

    export: dict = {"patient": _row_to_dict(p), "data": {}}

    # Exportă toate tabelele din schema pacientului
    tables = [
        "biomarkers", "sensor_readings", "supplements",
        "medications", "daily_logs", "directives",
    ]
    for table in tables:
        try:
            res = await db.execute(text(f"SELECT * FROM {schema}.{table} LIMIT 10000"))
            cols = res.keys()
            rows = res.fetchall()
            export["data"][table] = [dict(zip(cols, r)) for r in rows]
        except Exception:
            export["data"][table] = []

    # Consent log
    consent_res = await db.execute(
        text("SELECT * FROM public.consent_log WHERE patient_id = :pid ORDER BY created_at"),
        {"pid": str(patient_id)},
    )
    export["consent_log"] = [dict(zip(consent_res.keys(), r)) for r in consent_res.fetchall()]

    export["exported_at"] = datetime.now(timezone.utc).isoformat()
    export["gdpr_basis"]  = "Art. 20 GDPR — Dreptul la portabilitatea datelor"

    return export


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient_gdpr(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_clinic_admin),
):
    """
    GDPR Art. 17 — Ștergere completă și ireversibilă a tuturor datelor pacientului.
    Apelează funcția PostgreSQL care face cascade delete pe schema dedicată.
    """
    # Verifică că pacientul aparține clinicii
    await _get_patient_or_404(db, str(patient_id), current_user["clinic_id"])

    # Funcția PostgreSQL face tot: șterge schema + tabela publică + consent_log
    await db.execute(
        text("SELECT delete_patient_gdpr(:patient_id)"),
        {"patient_id": str(patient_id)},
    )

    # TODO: șterge namespace LanceDB patient_{uuid} (implementat în Faza 2 cu vector store)
