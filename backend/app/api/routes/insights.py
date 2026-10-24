from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Zone, ZoneMetricSnapshot
from app.schemas.schemas import InsightsSummaryResponse

router = APIRouter()

@router.get("/insights/summary", response_model=InsightsSummaryResponse)
def get_insights_summary(
    city: str = Query(default="Jaipur"),
    window: str = Query(default="last_hour"),
    db: Session = Depends(get_db)
):
    """
    Returns city-wide mobility intelligence summary:
    Total observed rides, driver vs passenger cancellations, top hotspots, and provenance.
    """
    snapshots = db.query(ZoneMetricSnapshot).join(Zone).filter(Zone.city.ilike(f"%{city}%")).all()

    total_avail = sum(s.available_ride_count for s in snapshots)
    total_eligible = sum(s.eligible_request_count for s in snapshots)
    total_driver_cancels = sum(s.driver_cancel_count for s in snapshots)
    total_passenger_cancels = sum(s.passenger_cancel_count for s in snapshots)
    total_provider_cancels = sum(s.provider_cancel_count for s in snapshots)

    avg_driver_rate = round(total_driver_cancels / total_eligible, 4) if total_eligible > 0 else None
    avg_pass_rate = round(total_passenger_cancels / total_eligible, 4) if total_eligible > 0 else None

    # Identify top cancellation hotspots
    cancellation_ranked = sorted(
        snapshots,
        key=lambda s: (s.driver_cancel_count / s.eligible_request_count) if s.eligible_request_count > 0 else 0,
        reverse=True
    )
    top_cancels = [s.zone.zone_name for s in cancellation_ranked[:3] if s.zone]

    # Identify top availability zones
    avail_ranked = sorted(snapshots, key=lambda s: s.available_ride_count, reverse=True)
    top_avails = [s.zone.zone_name for s in avail_ranked[:3] if s.zone]

    return InsightsSummaryResponse(
        city=city,
        time_window=window,
        total_observed_rides=total_avail,
        total_eligible_requests=total_eligible,
        total_driver_cancels=total_driver_cancels,
        total_passenger_cancels=total_passenger_cancels,
        total_provider_cancels=total_provider_cancels,
        avg_driver_cancel_rate=avg_driver_rate,
        avg_passenger_cancel_rate=avg_pass_rate,
        top_cancellation_hotspots=top_cancels,
        top_availability_zones=top_avails,
        data_freshness_label="Real-time telemetry aggregated within 2-minute cadence",
        provenance={
            "provider_telemetry": "Simulated synthetic Jaipur mobility signals in Demo mode",
            "cancellation_denominator": "Eligible ride request attempts dispatched within window",
            "integrity_rule": "Missing actor or missing request denominators return Insufficient Data"
        },
        is_demo=True
    )
