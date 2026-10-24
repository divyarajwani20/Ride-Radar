from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Zone, ZoneMetricSnapshot
from app.schemas.schemas import ReliabilityRiskResponse
from app.services.hot_zones import calculate_hot_zone_metric
from app.services.reliability_risk import assess_ride_failure_risk

router = APIRouter()

@router.get("/reliability/risk", response_model=ReliabilityRiskResponse)
def get_reliability_risk(
    zone_id: str = Query(..., description="Target Zone ID"),
    time_window: str = Query(default="last_hour"),
    candidate_eta: int = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Returns explainable ride failure risk prediction (Section 20 & 30).
    Estimates probability of non-pickup / cancellation with reasons and sample size.
    """
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    snapshot = db.query(ZoneMetricSnapshot).filter(
        ZoneMetricSnapshot.zone_id == zone.id
    ).order_by(ZoneMetricSnapshot.created_at.desc()).first()

    z_data = {
        "id": zone.id,
        "city": zone.city,
        "zone_name": zone.zone_name,
        "cell_id": zone.cell_id,
        "center_lat": zone.center_lat,
        "center_lng": zone.center_lng,
        "available_ride_count": snapshot.available_ride_count if snapshot else 0,
        "eligible_request_count": snapshot.eligible_request_count if snapshot else 0,
        "driver_cancel_count": snapshot.driver_cancel_count if snapshot else 0,
        "passenger_cancel_count": snapshot.passenger_cancel_count if snapshot else 0,
        "provider_cancel_count": snapshot.provider_cancel_count if snapshot else 0,
        "demand_estimate": snapshot.demand_estimate if snapshot else None,
        "data_freshness_seconds": snapshot.data_freshness_seconds if snapshot else 60,
        "source_type": "demo"
    }

    zone_metric = calculate_hot_zone_metric(z_data, time_window=time_window)
    assessment = assess_ride_failure_risk(
        zone_metrics=zone_metric,
        candidate_eta=candidate_eta,
        time_window=time_window
    )

    return ReliabilityRiskResponse(**assessment)
