"""
Router autentificare — login, refresh, logout
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import verify_password, create_access_token, create_refresh_token, decode_token

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


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login pentru doctori și admini."""
    # TODO: interogare DB pentru user
    # user = await get_user_by_email(db, body.email)
    # if not user or not verify_password(body.password, user.hashed_password):
    #     raise HTTPException(status_code=401, detail="Invalid credentials")
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Rotație refresh token — returnează pereche nouă de token-uri."""
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    # TODO: verificare în DB că token-ul nu e revocat + generare pereche nouă
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/logout")
async def logout(db: AsyncSession = Depends(get_db)):
    """Revocă refresh token-ul curent."""
    # TODO: marchează token-ul ca revocat în DB
    return {"detail": "Logged out successfully"}
