from typing import List, Dict, Any, Optional
from datetime import datetime

def assess_ride_failure_risk(
    zone_metrics: Dict[str, Any],
    candidate_eta: Optional[int] = None,
    candidate_driver_cancel_rate: Optional[float] = None,
    time_window: str = "last_hour"
) -> Dict[str, Any]:
    """
    Transparent, explainable rule-based ride failure risk estimation (Section 20 & 30).
    Estimates probability that a ride request fails to result in a successful pickup.
    Returns numeric score, category, confidence, and specific reason codes.
    """
    eligible = zone_metrics.get("eligible_request_count", 0)
    driver_cancel_rate = zone_metrics.get("driver_cancel_rate")
    passenger_cancel_rate = zone_metrics.get("passenger_cancel_rate")
    avail = zone_metrics.get("available_ride_count", 0)
    demand = zone_metrics.get("demand_estimate")
    demand_ratio = zone_metrics.get("demand_to_availability_ratio")

    reasons = []

    # Handle insufficient data guardrail
    if eligible < 5 or driver_cancel_rate is None:
        return {
            "zone_id": zone_metrics.get("zone_id", "unknown"),
            "zone_name": zone_metrics.get("zone_name", "Unknown Zone"),
            "risk_score": 50.0,
            "risk_level": "Insufficient data",
            "confidence": "low",
            "sample_size": eligible,
            "time_window": time_window,
            "reasons": ["Insufficient historical observations in this zone to reliably forecast failure risk."],
            "model_version": "rule_engine_v1.0",
            "observed_at": datetime.utcnow(),
            "source_type": zone_metrics.get("source_type", "demo"),
            "is_demo": True
        }

    # Base risk starts from zone driver cancellation rate
    # E.g. 10% cancellation rate translates to ~40 baseline risk
    risk_score = (driver_cancel_rate / 0.30) * 45.0  # Up to 45 points

    if driver_cancel_rate >= 0.18:
        reasons.append(f"Elevated driver cancellation rate in {zone_metrics.get('zone_name')} ({int(driver_cancel_rate * 100)}%)")
    elif driver_cancel_rate <= 0.05:
        reasons.append(f"Consistently low driver cancellation rate ({int(driver_cancel_rate * 100)}%)")

    # Demand pressure impact (Up to 25 points)
    if demand_ratio is not None and demand_ratio >= 1.5:
        risk_score += min(25.0, (demand_ratio - 1.0) * 20.0)
        reasons.append(f"High demand pressure relative to available vehicles ({demand_ratio}x ratio)")
    elif avail <= 2:
        risk_score += 20.0
        reasons.append("Very few observed available cabs in immediate area")

    # Candidate driver specific signals (Up to 20 points)
    if candidate_driver_cancel_rate is not None:
        if candidate_driver_cancel_rate >= 0.15:
            risk_score += 15.0
            reasons.append(f"Offered driver has history of higher cancellations ({int(candidate_driver_cancel_rate * 100)}%)")
        elif candidate_driver_cancel_rate <= 0.04:
            risk_score -= 10.0
            reasons.append("Offered driver has high reliability track record")

    # Candidate ETA impact (Up to 10 points)
    if candidate_eta is not None:
        if candidate_eta > 12:
            risk_score += 15.0
            reasons.append(f"Long approach ETA ({candidate_eta} mins) increases decline probability")
        elif candidate_eta <= 4:
            risk_score -= 8.0
            reasons.append("Immediate proximity (<4 mins) drastically lowers failure chance")

    # Passenger cancellation feedback (Up to 10 points)
    if passenger_cancel_rate is not None and passenger_cancel_rate >= 0.15:
        risk_score += 10.0
        reasons.append("Zone displays high passenger frustration/re-booking cancellations")

    # Bound risk score between 5.0 and 95.0
    risk_score = round(max(5.0, min(95.0, risk_score)), 1)

    if risk_score >= 65.0:
        risk_level = "High"
    elif risk_score >= 35.0:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    # Confidence calculation based on sample size and freshness
    if eligible >= 30:
        confidence = "high"
    elif eligible >= 10:
        confidence = "medium"
    else:
        confidence = "low"

    if not reasons:
        reasons.append("Typical booking conditions with balanced supply and demand.")

    return {
        "zone_id": zone_metrics.get("zone_id", "unknown"),
        "zone_name": zone_metrics.get("zone_name", "Unknown Zone"),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "confidence": confidence,
        "sample_size": eligible,
        "time_window": time_window,
        "reasons": reasons,
        "model_version": "rule_engine_v1.0",
        "observed_at": datetime.utcnow(),
        "source_type": zone_metrics.get("source_type", "demo"),
        "is_demo": True
    }
