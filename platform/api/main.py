"""
foreverhuman.health — FastAPI Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from core.config import settings
from core.database import engine, Base
from routers import auth, patients, doctors, analyses, chat, sensors, directives


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown logic."""
    # Startup
    async with engine.begin() as conn:
        # Alembic gestionează migrările în prod; auto-create doar în dev
        if settings.ENVIRONMENT == "development":
            await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="foreverhuman.health API",
    version="0.1.0",
    description="Personal health monitoring platform — clinic API",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=[settings.DOMAIN, f"*.{settings.DOMAIN}"])

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router,       prefix="/api/v1/auth",       tags=["auth"])
app.include_router(patients.router,   prefix="/api/v1/patients",   tags=["patients"])
app.include_router(doctors.router,    prefix="/api/v1/doctors",    tags=["doctors"])
app.include_router(analyses.router,   prefix="/api/v1/analyses",   tags=["analyses"])
app.include_router(chat.router,       prefix="/api/v1/chat",       tags=["chat"])
app.include_router(sensors.router,    prefix="/api/v1/sensors",    tags=["sensors"])
app.include_router(directives.router, prefix="/api/v1/directives", tags=["directives"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": "0.1.0", "clinic_id": settings.CLINIC_ID}
