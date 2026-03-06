"""
Router directive — doctor → agent pacient
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal, Any

from core.database import get_db
from core.security import require_doctor, get_current_user

router = APIRouter()


class DirectiveCreate(BaseModel):
    patient_id: UUID
    directive_type: Literal["protocol_change", "flag", "note", "recommendation"]
    content: dict[str, Any]   # structura depinde de tip


class DirectiveOut(BaseModel):
    id: UUID
    directive_type: str
    content: dict
    status: str
    patient_notified: bool
    agent_applied: bool


@router.post("/", response_model=DirectiveOut)
async def create_directive(
    body: DirectiveCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_doctor),
):
    """
    Doctorul emite o directivă pentru agentul unui pacient.

    Tipuri:
    - protocol_change: modificare protocol (supliment, dietă, obiectiv)
    - flag: marchează o valoare pentru monitorizare specială
    - note: notă clinică — apare în contextul agentului
    - recommendation: recomandare formală cu deadline

    Flow după creare:
    1. Salvare în patient_{uuid}.directives
    2. Push notification → pacient
    3. Agent primește directiva la next session boot
    4. Agent confirmă implementarea (agent_applied = true)
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/patient/{patient_id}", response_model=list[DirectiveOut])
async def list_patient_directives(
    patient_id: UUID,
    status: str = "pending",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_doctor),
):
    """Lista directivelor pentru un pacient, filtrate după status."""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.patch("/{directive_id}/acknowledge")
async def acknowledge_directive(
    directive_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Pacientul sau agentul confirmă că directiva a fost procesată."""
    raise HTTPException(status_code=501, detail="Not implemented yet")
