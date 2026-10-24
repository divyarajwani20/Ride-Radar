from typing import List, Dict, Any
from datetime import datetime, timedelta

def generate_zone_demand_forecast(
    zones: List[Dict[str, Any]],
    horizon_minutes: int = 30
) -> Dict[str, Any]:
    """
    Demand shock detector and directional demand/supply forecasting (Section 22.1 & 30).
    Uses synthetic Jaipur time series with documented thresholds.
    Directional estimates, explicitly labeled as simulated in demo mode.
    """
    now = datetime.utcnow()
    forecast_end = now + timedelta(minutes=horizon_minutes)

    forecast_results = []
    shocks = []

    for zone in zones:
        zone_id = zone.get("id") or zone.get("zone_id")
        zone_name = zone.get("zone_name")
        curr_avail = zone.get("available_ride_count", 10)
        curr_demand = zone.get("demand_estimate", 12) or 12
        
        # Synthetic forecast trend
        is_priority = zone.get("is_priority_designated", False)
        if is_priority or "Station" in zone_name or "Airport" in zone_name or "Hospital" in zone_name:
            pred_demand = int(curr_demand * 1.35)
            pred_supply = max(2, int(curr_avail * 0.85))
        else:
            pred_demand = int(curr_demand * 1.05)
            pred_supply = max(3, int(curr_avail * 0.95))

        ratio = round(pred_demand / max(1, pred_supply), 2)
        has_shock = ratio >= 1.6 or (pred_demand - curr_demand >= 15)

        entry = {
            "zone_id": zone_id,
            "zone_name": zone_name,
            "forecast_start": now,
            "forecast_end": forecast_end,
            "horizon_minutes": horizon_minutes,
            "current_demand": curr_demand,
            "current_supply": curr_avail,
            "predicted_demand": pred_demand,
            "predicted_supply": pred_supply,
            "demand_supply_ratio": ratio,
            "demand_shock_detected": has_shock,
            "confidence": "high" if zone.get("eligible_request_count", 0) > 20 else "medium",
            "source_type": "demo",
            "is_demo": True
        }
        forecast_results.append(entry)

        if has_shock:
            shocks.append({
                "zone_id": zone_id,
                "zone_name": zone_name,
                "ratio": ratio,
                "severity": "High" if ratio >= 2.0 else "Moderate",
                "recommended_action": "Recommend earlier booking; dispatch voluntary reserve capacity.",
                "explanation": f"Demand projected to exceed available supply by {int(ratio * 100)}% over the next {horizon_minutes} minutes."
            })

    return {
        "city": "Jaipur",
        "horizon_minutes": horizon_minutes,
        "forecasts": forecast_results,
        "demand_shocks": shocks,
        "confidence": "medium",
        "source_type": "demo",
        "is_demo": True,
        "generated_at": now
    }
