import pytest
from app.services.reliability_risk import assess_ride_failure_risk

def test_risk_assessment_insufficient_data():
    """Zone with < 5 samples returns Insufficient data and low confidence."""
    zone_metrics = {
        "zone_id": "zone_small",
        "zone_name": "Small Hamlet",
        "eligible_request_count": 2,
        "driver_cancel_rate": 0.5,
        "passenger_cancel_rate": 0.0,
        "available_ride_count": 1,
        "demand_estimate": 2,
        "demand_to_availability_ratio": 2.0
    }
    risk = assess_ride_failure_risk(zone_metrics)
    assert risk["risk_level"] == "Insufficient data"
    assert risk["confidence"] == "low"
    assert "Insufficient historical observations" in risk["reasons"][0]

def test_risk_assessment_high_cancellation():
    """Zone with 25% driver cancellation and high demand ratio returns High risk."""
    zone_metrics = {
        "zone_id": "zone_busy_junction",
        "zone_name": "Congested Station",
        "eligible_request_count": 80,
        "driver_cancel_rate": 0.25,
        "passenger_cancel_rate": 0.12,
        "available_ride_count": 5,
        "demand_estimate": 40,
        "demand_to_availability_ratio": 2.2
    }
    risk = assess_ride_failure_risk(zone_metrics, candidate_eta=14)
    assert risk["risk_score"] >= 65.0
    assert risk["risk_level"] == "High"
    assert risk["confidence"] == "high"
    assert len(risk["reasons"]) >= 2
