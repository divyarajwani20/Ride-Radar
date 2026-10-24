from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

HOT_ZONE_WEIGHTS = {
    "availability": 0.35,
    "demand_pressure": 0.25,
    "driver_cancels": 0.20,
    "passenger_cancels": 0.15,
    "freshness": 0.05
}

def calculate_hot_zone_metric(
    zone_data: Dict[str, Any],
    time_window: str = "last_hour"
) -> Dict[str, Any]:
    """
    Computes zone scores, separate driver/passenger/provider cancellation rates,
    demand pressure, confidence, and hotspot tags.
    Missing denominators NEVER fabricate percentages.
    """
    avail = zone_data.get("available_ride_count", 0)
    eligible = zone_data.get("eligible_request_count", 0)
    driver_cancels = zone_data.get("driver_cancel_count", 0)
    passenger_cancels = zone_data.get("passenger_cancel_count", 0)
    provider_cancels = zone_data.get("provider_cancel_count", 0)
    completed = zone_data.get("completed_count", 0)
    demand = zone_data.get("demand_estimate")
    freshness_sec = zone_data.get("data_freshness_seconds", 60)

    # 1. Cancellation rates (Only compute if eligible denominator > 0)
    if eligible > 0:
        driver_cancel_rate = round(driver_cancels / eligible, 4)
        passenger_cancel_rate = round(passenger_cancels / eligible, 4)
        provider_cancel_rate = round(provider_cancels / eligible, 4)
    else:
        driver_cancel_rate = None
        passenger_cancel_rate = None
        provider_cancel_rate = None

    # 2. Demand-to-availability ratio
    if demand is not None and demand > 0 and avail > 0:
        demand_to_avail_ratio = round(demand / avail, 2)
    elif demand is not None and demand > 0 and avail == 0:
        demand_to_avail_ratio = 9.99  # Extreme demand pressure
    else:
        demand_to_avail_ratio = None

    # 3. Normalized Component Scores (0 to 100)
    # Availability score: 0 to 40+ rides mapped to 0-100
    norm_avail = max(0.0, min(100.0, (avail / 30.0) * 100.0))

    # Demand pressure: ratio 1.0 = 50, ratio 2.0+ = 100
    if demand_to_avail_ratio is not None:
        norm_demand = max(0.0, min(100.0, (demand_to_avail_ratio / 2.0) * 100.0))
    else:
        norm_demand = None

    # Driver cancellation severity: 25%+ = 100
    if driver_cancel_rate is not None:
        norm_driver_cancels = max(0.0, min(100.0, (driver_cancel_rate / 0.25) * 100.0))
    else:
        norm_driver_cancels = None

    # Passenger cancellation severity: 20%+ = 100
    if passenger_cancel_rate is not None:
        norm_passenger_cancels = max(0.0, min(100.0, (passenger_cancel_rate / 0.20) * 100.0))
    else:
        norm_passenger_cancels = None

    # Freshness: decay over 60 minutes
    norm_freshness = max(0.0, min(100.0, 100.0 * max(0, 1 - (freshness_sec / 3600.0))))

    # 4. Renormalize weights across available metrics
    active_weights = {}
    active_scores = {}

    active_weights["availability"] = HOT_ZONE_WEIGHTS["availability"]
    active_scores["availability"] = norm_avail

    if norm_demand is not None:
        active_weights["demand_pressure"] = HOT_ZONE_WEIGHTS["demand_pressure"]
        active_scores["demand_pressure"] = norm_demand

    if norm_driver_cancels is not None:
        active_weights["driver_cancels"] = HOT_ZONE_WEIGHTS["driver_cancels"]
        active_scores["driver_cancels"] = norm_driver_cancels

    if norm_passenger_cancels is not None:
        active_weights["passenger_cancels"] = HOT_ZONE_WEIGHTS["passenger_cancels"]
        active_scores["passenger_cancels"] = norm_passenger_cancels

    active_weights["freshness"] = HOT_ZONE_WEIGHTS["freshness"]
    active_scores["freshness"] = norm_freshness

    total_weight = sum(active_weights.values())
    zone_score = sum((w / total_weight) * active_scores[k] for k, w in active_weights.items())
    zone_score = round(zone_score, 1)

    # 5. Determine Tags based on real thresholds
    tags = []
    if avail >= 15:
        tags.append("High availability")
    elif avail <= 3:
        tags.append("Scare supply")

    if driver_cancel_rate is not None and driver_cancel_rate >= 0.14:
        tags.append("Driver cancellation hotspot")

    if passenger_cancel_rate is not None and passenger_cancel_rate >= 0.12:
        tags.append("Passenger cancellation hotspot")

    if demand_to_avail_ratio is not None and demand_to_avail_ratio >= 1.4:
        tags.append("High demand")

    if eligible < 10 or driver_cancel_rate is None:
        tags.append("Low confidence")

    # Confidence tier
    if eligible >= 40 and freshness_sec < 600:
        confidence = "high"
    elif eligible >= 10:
        confidence = "medium"
    elif eligible > 0:
        confidence = "low"
    else:
        confidence = "insufficient_data"

    time_labels = {
        "now": "Current Live Window",
        "last_15_mins": "Last 15 minutes",
        "last_hour": "Past 60 minutes",
        "today": "Today's Aggregated Timeline"
    }

    return {
        "zone_id": zone_data["id"],
        "city": zone_data["city"],
        "zone_name": zone_data["zone_name"],
        "cell_id": zone_data["cell_id"],
        "center_lat": zone_data["center_lat"],
        "center_lng": zone_data["center_lng"],
        "radius_meters": zone_data.get("radius_meters", 1500),
        "is_priority_designated": zone_data.get("is_priority_designated", False),
        "priority_category": zone_data.get("priority_category"),
        "description": zone_data.get("description"),
        
        "available_ride_count": avail,
        "demand_estimate": demand,
        "eligible_request_count": eligible,
        "completed_count": completed,
        "driver_cancel_count": driver_cancels,
        "passenger_cancel_count": passenger_cancels,
        "provider_cancel_count": provider_cancels,
        
        "driver_cancel_rate": driver_cancel_rate,
        "passenger_cancel_rate": passenger_cancel_rate,
        "provider_cancel_rate": provider_cancel_rate,
        "demand_to_availability_ratio": demand_to_avail_ratio,
        
        "zone_score": zone_score,
        "tags": tags,
        "confidence": confidence,
        "data_freshness_seconds": freshness_sec,
        "source_type": zone_data.get("source_type", "demo"),
        "is_demo": zone_data.get("is_demo", True),
        "time_window_label": time_labels.get(time_window, time_window)
    }

def sort_hot_zones(zones: List[Dict[str, Any]], metric: str = "zone_score") -> List[Dict[str, Any]]:
    """Sorts hot zones by selected metric."""
    if metric == "availability":
        return sorted(zones, key=lambda z: -z["available_ride_count"])
    elif metric == "driver_cancels":
        return sorted(zones, key=lambda z: -(z["driver_cancel_rate"] or -1))
    elif metric == "passenger_cancels":
        return sorted(zones, key=lambda z: -(z["passenger_cancel_rate"] or -1))
    elif metric == "demand":
        return sorted(zones, key=lambda z: -(z["demand_estimate"] or 0))
    else:  # default zone_score
        return sorted(zones, key=lambda z: -z["zone_score"])
