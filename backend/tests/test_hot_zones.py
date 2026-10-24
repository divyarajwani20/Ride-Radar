import pytest
from app.services.hot_zones import calculate_hot_zone_metric, sort_hot_zones

def test_zero_denominator_cancellation_rates():
    """Zero eligible ride requests must return None for cancellation rates, never 0% or divide by zero."""
    zone_data = {
        "id": "zone_test",
        "city": "Jaipur",
        "zone_name": "Test Zone",
        "cell_id": "JPR-TEST-01",
        "center_lat": 26.9,
        "center_lng": 75.8,
        "available_ride_count": 0,
        "eligible_request_count": 0,  # Zero denominator!
        "driver_cancel_count": 0,
        "passenger_cancel_count": 0,
        "provider_cancel_count": 0,
        "completed_count": 0,
        "demand_estimate": None
    }
    metric = calculate_hot_zone_metric(zone_data)
    assert metric["driver_cancel_rate"] is None
    assert metric["passenger_cancel_rate"] is None
    assert metric["provider_cancel_rate"] is None
    assert metric["confidence"] == "insufficient_data"
    assert "Low confidence" in metric["tags"]

def test_separate_cancellation_rates():
    """Driver and passenger cancellations must be calculated separately from eligible requests."""
    zone_data = {
        "id": "zone_junction",
        "city": "Jaipur",
        "zone_name": "Railway Station",
        "cell_id": "JPR-02",
        "center_lat": 26.92,
        "center_lng": 75.78,
        "available_ride_count": 15,
        "eligible_request_count": 100,
        "driver_cancel_count": 20,
        "passenger_cancel_count": 10,
        "provider_cancel_count": 2,
        "completed_count": 68,
        "demand_estimate": 80
    }
    metric = calculate_hot_zone_metric(zone_data)
    assert metric["driver_cancel_rate"] == 0.20
    assert metric["passenger_cancel_rate"] == 0.10
    assert metric["provider_cancel_rate"] == 0.02
    assert "Driver cancellation hotspot" in metric["tags"]
    assert "High demand" in metric["tags"]
    assert metric["confidence"] == "high"

def test_sort_hot_zones():
    """Sorting by metric works accurately."""
    zones = [
        {"zone_id": "z1", "zone_score": 40.0, "available_ride_count": 5, "driver_cancel_rate": 0.05, "passenger_cancel_rate": 0.02, "demand_estimate": 10},
        {"zone_id": "z2", "zone_score": 85.0, "available_ride_count": 25, "driver_cancel_rate": 0.25, "passenger_cancel_rate": 0.15, "demand_estimate": 50},
        {"zone_id": "z3", "zone_score": 60.0, "available_ride_count": 12, "driver_cancel_rate": 0.10, "passenger_cancel_rate": 0.05, "demand_estimate": 20}
    ]
    by_score = sort_hot_zones(zones, metric="zone_score")
    assert by_score[0]["zone_id"] == "z2"

    by_avail = sort_hot_zones(zones, metric="availability")
    assert by_avail[0]["zone_id"] == "z2"

    by_cancels = sort_hot_zones(zones, metric="driver_cancels")
    assert by_cancels[0]["zone_id"] == "z2"
