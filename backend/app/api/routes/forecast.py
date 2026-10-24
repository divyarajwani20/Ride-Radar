from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Zone, ZoneMetricSnapshot
from app.schemas.schemas import DemandForecastResponse
from app.services.forecasting import generate_zone_demand_forecast

router = APIRouter()

@router.get("/demand/forecast", response_model=DemandForecastResponse)
def get_demand_forecast(
    city: str = Query(default="Jaipur"),
    horizon_minutes: int = Query(default=30),  # 15 or 30 minutes
    db: Session = Depends(get_db)
):
    """
    Returns baseline demand & supply forecast and detects demand shocks (Section 22.1 & 30).
    Directional estimates, explicitly labeled as simulated in Demo mode.
    """
    zones = db.query(Zone).filter(Zone.city.ilike(f"%{city}%")).all()
    zone_data_list = []

    for z in zones:
        snap = db.query(ZoneMetricSnapshot).filter(
            ZoneMetricSnapshot.zone_id == z.id
        ).order_by(ZoneMetricSnapshot.created_at.desc()).first()

        zone_data_list.append({
            "id": z.id,
            "zone_id": z.id,
            "zone_name": z.zone_name,
            "is_priority_designated": z.is_priority_designated,
            "available_ride_count": snap.available_ride_count if snap else 10,
            "demand_estimate": snap.demand_estimate if snap else 12,
            "eligible_request_count": snap.eligible_request_count if snap else 20
        })

    forecast_data = generate_zone_demand_forecast(zone_data_list, horizon_minutes=horizon_minutes)
    return DemandForecastResponse(**forecast_data)
