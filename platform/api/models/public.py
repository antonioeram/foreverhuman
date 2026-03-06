"""
SQLAlchemy ORM models — schema public (clinics, users, patients, refresh_tokens)
Folosite de Base.metadata.create_all în dev (nu în prod — acolo e schema.sql).
"""
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, String, Date, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


def _now():
    return datetime.now(timezone.utc)


class Clinic(Base):
    __tablename__ = "clinics"
    __table_args__ = {"schema": "public"}

    id:         Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    name:       Mapped[str] = mapped_column(String(255))
    slug:       Mapped[str] = mapped_column(String(100), unique=True)
    country:    Mapped[str] = mapped_column(String(2),   default="RO")
    timezone:   Mapped[str] = mapped_column(String(50),  default="Europe/Bucharest")
    plan:       Mapped[str] = mapped_column(String(50),  default="standard")
    is_active:  Mapped[bool] = mapped_column(Boolean, default=True)
    settings:   Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id:              Mapped[str]           = mapped_column(PGUUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    clinic_id:       Mapped[str | None]   = mapped_column(PGUUID(as_uuid=False), ForeignKey("public.clinics.id", ondelete="CASCADE"))
    email:           Mapped[str]           = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str]           = mapped_column(String(255))
    first_name:      Mapped[str | None]   = mapped_column(String(100))
    last_name:       Mapped[str | None]   = mapped_column(String(100))
    role:            Mapped[str]           = mapped_column(String(50))
    is_active:       Mapped[bool]          = mapped_column(Boolean, default=True)
    last_login_at:   Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_now)
    updated_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = {"schema": "public"}

    id:              Mapped[str]           = mapped_column(PGUUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    clinic_id:       Mapped[str]           = mapped_column(PGUUID(as_uuid=False), ForeignKey("public.clinics.id", ondelete="CASCADE"))
    email:           Mapped[str | None]   = mapped_column(String(255))
    first_name:      Mapped[str | None]   = mapped_column(String(100))
    last_name:       Mapped[str | None]   = mapped_column(String(100))
    date_of_birth:   Mapped[datetime | None] = mapped_column(Date)
    sex:             Mapped[str | None]   = mapped_column(String(1))
    phone:           Mapped[str | None]   = mapped_column(String(30))
    is_active:       Mapped[bool]          = mapped_column(Boolean, default=True)
    consent_at:      Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consent_version: Mapped[str | None]   = mapped_column(String(20))
    created_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_now)
    updated_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": "public"}

    id:         Mapped[str]      = mapped_column(PGUUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id:    Mapped[str]      = mapped_column(PGUUID(as_uuid=False), ForeignKey("public.users.id", ondelete="CASCADE"))
    token_hash: Mapped[str]      = mapped_column(String(255), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked:    Mapped[bool]     = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ConsentLog(Base):
    __tablename__ = "consent_log"
    __table_args__ = {"schema": "public"}

    id:              Mapped[str]         = mapped_column(PGUUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    patient_id:      Mapped[str]         = mapped_column(PGUUID(as_uuid=False), ForeignKey("public.patients.id", ondelete="CASCADE"))
    action:          Mapped[str]         = mapped_column(String(20))
    consent_version: Mapped[str | None] = mapped_column(String(20))
    ip_address:      Mapped[str | None] = mapped_column(String(45))
    user_agent:      Mapped[str | None] = mapped_column(Text)
    created_at:      Mapped[datetime]    = mapped_column(DateTime(timezone=True), default=_now)
