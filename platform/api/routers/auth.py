"""
Router autentificare — login, refresh, logout
"""
import hashlib
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login pentru doctori și admini. Returnează pereche JWT access + refresh."""
    result = await db.execute(
        text(
            "SELECT id, email, hashed_password, role, clinic_id, is_active "
            "FROM public.users WHERE email = :email"
        ),
        {"email": body.email},
    )
    user = result.fetchone()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email sau parolă incorecte",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Contul este dezactivat",
        )

    access_token  = create_access_token(str(user.id), user.role, str(user.clinic_id))
    refresh_tok   = create_refresh_token(str(user.id))
    tok_hash      = _hash_token(refresh_tok)
    expires_at    = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Stochează refresh token (hash) în DB
    await db.execute(
        text(
            "INSERT INTO public.refresh_tokens (id, user_id, token_hash, expires_at) "
            "VALUES (:id, :user_id, :token_hash, :expires_at)"
        ),
        {
            "id": str(uuid4()),
            "user_id": str(user.id),
            "token_hash": tok_hash,
            "expires_at": expires_at,
        },
    )

    # Actualizează last_login_at
    await db.execute(
        text("UPDATE public.users SET last_login_at = NOW() WHERE id = :id"),
        {"id": str(user.id)},
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_tok)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Rotație refresh token — verifică token-ul în DB, emite pereche nouă, revocă vechiul.
    """
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tip greșit")

    tok_hash = _hash_token(body.refresh_token)

    # Verifică că token-ul există și nu e revocat
    result = await db.execute(
        text(
            "SELECT id, user_id, expires_at, revoked FROM public.refresh_tokens "
            "WHERE token_hash = :tok_hash"
        ),
        {"tok_hash": tok_hash},
    )
    rec = result.fetchone()

    if not rec:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalid sau revocat")
    if rec.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocat")
    if rec.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirat")

    # Revocă token-ul vechi
    await db.execute(
        text("UPDATE public.refresh_tokens SET revoked = true WHERE id = :id"),
        {"id": str(rec.id)},
    )

    # Obține datele user-ului pentru noul token
    user_res = await db.execute(
        text("SELECT id, role, clinic_id FROM public.users WHERE id = :id"),
        {"id": str(rec.user_id)},
    )
    user = user_res.fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inexistent")

    # Emite pereche nouă
    new_access   = create_access_token(str(user.id), user.role, str(user.clinic_id))
    new_refresh  = create_refresh_token(str(user.id))
    new_hash     = _hash_token(new_refresh)
    new_expires  = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    await db.execute(
        text(
            "INSERT INTO public.refresh_tokens (id, user_id, token_hash, expires_at) "
            "VALUES (:id, :user_id, :token_hash, :expires_at)"
        ),
        {
            "id": str(uuid4()),
            "user_id": str(rec.user_id),
            "token_hash": new_hash,
            "expires_at": new_expires,
        },
    )

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Revocă refresh token-ul curent. Frontend trebuie să șteargă local token-urile."""
    tok_hash = _hash_token(body.refresh_token)
    await db.execute(
        text("UPDATE public.refresh_tokens SET revoked = true WHERE token_hash = :tok_hash"),
        {"tok_hash": tok_hash},
    )
    # Nu aruncă eroare dacă token-ul nu există (idempotent)


@router.get("/me")
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Returnează profilul utilizatorului autentificat."""
    result = await db.execute(
        text(
            "SELECT id, email, first_name, last_name, role, clinic_id, last_login_at "
            "FROM public.users WHERE id = :id"
        ),
        {"id": current_user["sub"]},
    )
    user = result.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User negăsit")

    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "clinic_id": str(user.clinic_id),
        "last_login_at": user.last_login_at,
    }
