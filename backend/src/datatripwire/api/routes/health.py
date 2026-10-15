"""Health check endpoints for DataTripwire."""

from fastapi import APIRouter
from datatripwire.config import settings
from datatripwire.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def root_health():
    """Unversioned health check."""
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.env,
    )


@router.get("/api/v1/health", response_model=HealthResponse)
def api_v1_health():
    """Versioned API v1 health check."""
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.env,
    )
