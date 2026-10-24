from fastapi import APIRouter
from datetime import datetime
from app.core.config import settings
from app.schemas.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health():
    return HealthResponse(
        status="healthy",
        demo_mode=settings.DEMO_MODE,
        version=settings.VERSION,
        city=settings.DEFAULT_CITY,
        active_scenario=settings.ACTIVE_DEMO_SCENARIO,
        timestamp=datetime.utcnow()
    )
