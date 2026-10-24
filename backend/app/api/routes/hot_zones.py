from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from app.db.session import get_db
from app.models.models import Zone, ZoneMetricSnapshot, Provider
from app.schemas.schemas import HotZonesResponse, HotZoneMetricOut, ZoneDetailResponse, TimeSeriesPoint
from app.services.hot_zones import calculate_hot_zone_metric, sort_hot_zones
from app.core.config import settings

router = APIRouter()

@router.get("/hot-zones", response_model=HotZonesResponse)
def get_hot_zones(
    city: str = Query(default="Jaipur"),
    window: str = Query(default="last_hour"),  # now, last_15_mins, last_hour, today
    metric: str = Query(default="zone_score"),  # zone_score, availability, driver_cancels, passenger_cancels, demand
    db: Session = Depends(get_db)
):
    """
    Returns calculated hot-zone metrics for the chosen city and time window.
    Calculates availability, separate driver/passenger/provider cancellation rates,
    demand pressure, confidence, and tags.
    """
    zones = db.query(Zone).filter(Zone.city.ilike(f"%{city}%")).all()
    calculated_zones = []

    for z in zones:
        snapshot = db.query(ZoneMetricSnapshot).filter(
            ZoneMetricSnapshot.zone_id == z.id
        ).order_by(ZoneMetricSnapshot.created_at.desc()).first()

        # Adjust metrics according to time window simulation
        mult = 1.0
        if window == "now":
            mult = 0.25
        elif window == "last_15_mins":
            mult = 0.40
        elif window == "today":
            mult = 4.0

        if snapshot:
            z_data = {
                "id": z.id,
                "city": z.city,
                "zone_name": z.zone_name,
                "cell_id": z.cell_id,
                "center_lat": z.center_lat,
                "center_lng": z.center_lng,
                "radius_meters": z.radius_meters,
                "is_priority_designated": z.is_priority_designated,
                "priority_category": z.priority_category,
                "description": z.description,
                "available_ride_count": max(1, int(snapshot.available_ride_count * (0.8 if window == 'now' else 1.0))),
                "eligible_request_count": max(0, int(snapshot.eligible_request_count * mult)),
                "driver_cancel_count": max(0, int(snapshot.driver_cancel_count * mult)),
                "passenger_cancel_count": max(0, int(snapshot.passenger_cancel_count * mult)),
                "provider_cancel_count": max(0, int(snapshot.provider_cancel_count * mult)),
                "completed_count": max(0, int(snapshot.completed_count * mult)),
                "demand_estimate": int(snapshot.demand_estimate * mult) if snapshot.demand_estimate else None,
                "data_freshness_seconds": snapshot.data_freshness_seconds,
                "source_type": snapshot.source_type,
                "is_demo": True
            }
        else:
            z_data = {
                "id": z.id,
                "city": z.city,
                "zone_name": z.zone_name,
                "cell_id": z.cell_id,
                "center_lat": z.center_lat,
                "center_lng": z.center_lng,
                "radius_meters": z.radius_meters,
                "is_priority_designated": z.is_priority_designated,
                "priority_category": z.priority_category,
                "description": z.description,
                "available_ride_count": 0,
                "eligible_request_count": 0,
                "driver_cancel_count": 0,
                "passenger_cancel_count": 0,
                "provider_cancel_count": 0,
                "completed_count": 0,
                "demand_estimate": None,
                "data_freshness_seconds": 3600,
                "source_type": "demo",
                "is_demo": True
            }

        calculated = calculate_hot_zone_metric(z_data, time_window=window)
        calculated_zones.append(calculated)

    sorted_zones = sort_hot_zones(calculated_zones, metric=metric)

    return HotZonesResponse(
        zones=[HotZoneMetricOut(**z) for z in sorted_zones],
        time_window=window,
        selected_metric=metric,
        city=city,
        data_freshness="Observed within last 2 minutes",
        demo_notice="DEMO DATA: Hot-zone metrics, cancellation rates, and coordinates are simulated for Jaipur demonstration.",
        timestamp=datetime.utcnow()
    )

@router.get("/hot-zones/{zone_id}", response_model=ZoneDetailResponse)
def get_zone_detail(
    zone_id: str,
    window: str = Query(default="last_hour"),
    db: Session = Depends(get_db)
):
    """
    Returns detailed zone breakdown with time-series history for charts.
    """
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    snapshot = db.query(ZoneMetricSnapshot).filter(
        ZoneMetricSnapshot.zone_id == zone.id
    ).order_by(ZoneMetricSnapshot.created_at.desc()).first()

    avail = snapshot.available_ride_count if snapshot else 10
    eligible = snapshot.eligible_request_count if snapshot else 20
    driver_cancels = snapshot.driver_cancel_count if snapshot else 2
    pass_cancels = snapshot.passenger_cancel_count if snapshot else 1
    demand = snapshot.demand_estimate if snapshot else 25

    z_data = {
        "id": zone.id,
        "city": zone.city,
        "zone_name": zone.zone_name,
        "cell_id": zone.cell_id,
        "center_lat": zone.center_lat,
        "center_lng": zone.center_lng,
        "radius_meters": zone.radius_meters,
        "is_priority_designated": zone.is_priority_designated,
        "priority_category": zone.priority_category,
        "description": zone.description,
        "available_ride_count": avail,
        "eligible_request_count": eligible,
        "driver_cancel_count": driver_cancels,
        "passenger_cancel_count": pass_cancels,
        "provider_cancel_count": 0,
        "completed_count": max(0, eligible - driver_cancels - pass_cancels),
        "demand_estimate": demand,
        "data_freshness_seconds": 45,
        "source_type": "demo",
        "is_demo": True
    }

    zone_metric = calculate_hot_zone_metric(z_data, time_window=window)

    # Generate synthetic time-series points for the last 6 time buckets
    now = datetime.utcnow()
    time_series = []
    for i in range(6, 0, -1):
        point_time = (now - timedelta(minutes=i * 10)).strftime("%H:%M")
        factor = 0.8 + (i * 0.05)
        time_series.append(TimeSeriesPoint(
            timestamp=point_time,
            available_rides=max(2, int(avail * factor)),
            driver_cancels=max(0, int(driver_cancels * (1.2 if i % 2 == 0 else 0.8))),
            passenger_cancels=max(0, int(pass_cancels * 0.9)),
            demand=int(demand * factor) if demand else None,
            zone_score=round(max(10.0, min(100.0, zone_metric["zone_score"] * (0.9 + (i * 0.03)))), 1)
        ))

    # Provider breakdown in this zone
    providers = db.query(Provider).all()
    prov_breakdown = []
    for p in providers:
        prov_breakdown.append({
            "provider_name": p.name,
            "provider_id": p.id,
            "status": p.status,
            "estimated_available_cabs": max(1, int(avail * 0.35)),
            "avg_pickup_eta": 4 if p.id == "uber" else (6 if p.id == "ola" else 8)
        })

    return ZoneDetailResponse(
        zone=HotZoneMetricOut(**zone_metric),
        time_series=time_series,
        provider_breakdown=prov_breakdown,
        active_scenario=settings.ACTIVE_DEMO_SCENARIO,
        demo_notice="DEMO DATA: Time-series observations and provider distributions are simulated for Jaipur demonstration."
    )
