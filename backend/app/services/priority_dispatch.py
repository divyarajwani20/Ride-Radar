import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

PRIORITY_DISPATCH_WEIGHTS = {
    "eta": 0.35,
    "reliability": 0.30,
    "distance": 0.20,
    "acceptance_history": 0.10,
    "freshness": 0.05
}

def rank_priority_candidates(
    candidates: List[Dict[str, Any]],
    requested_category: str = "sedan"
) -> List[Dict[str, Any]]:
    """
    Ranks eligible drivers for emergency priority allocation (Section 19.5 & 28).
    Weights: 35% ETA, 30% reliability, 20% distance, 10% acceptance history, 5% freshness.
    """
    if not candidates:
        return []

    scored = []
    min_eta = min((c.get("eta_minutes", 10) for c in candidates), default=5)
    min_dist = min((c.get("distance_km", 2.0) for c in candidates), default=1.0)

    for c in candidates:
        eta = max(1, c.get("eta_minutes", 5))
        dist = max(0.2, c.get("distance_km", 1.5))
        cancels = c.get("verified_driver_cancel_count", 1)
        eligible = c.get("eligible_ride_count", 50)
        
        # Smoothed reliability
        smoothed_cancel_rate = (cancels + 1.0) / (eligible + 10.0)
        score_reliability = max(0.0, min(100.0, 100.0 * (1.0 - smoothed_cancel_rate)))

        # ETA score (relative to closest)
        score_eta = max(0.0, min(100.0, 100.0 * (min_eta / eta)))

        # Proximity score (relative to closest)
        score_distance = max(0.0, min(100.0, 100.0 * (min_dist / dist)))

        # Acceptance history score (default 90 for demo)
        score_acceptance = c.get("acceptance_rate_score", 90.0)

        # Freshness (100 if updated in last 5 mins)
        score_freshness = 95.0

        total_score = (
            PRIORITY_DISPATCH_WEIGHTS["eta"] * score_eta +
            PRIORITY_DISPATCH_WEIGHTS["reliability"] * score_reliability +
            PRIORITY_DISPATCH_WEIGHTS["distance"] * score_distance +
            PRIORITY_DISPATCH_WEIGHTS["acceptance_history"] * score_acceptance +
            PRIORITY_DISPATCH_WEIGHTS["freshness"] * score_freshness
        )

        reasons = []
        if score_eta >= 85:
            reasons.append(f"Immediate proximity ({eta} min arrival)")
        if score_reliability >= 88:
            reasons.append("Top-tier verified driver reliability")
        if dist <= 1.5:
            reasons.append(f"Within {dist} km radius")

        scored.append({
            **c,
            "score": round(total_score, 1),
            "eta_minutes": eta,
            "distance_km": dist,
            "reliability_rate": round((1.0 - smoothed_cancel_rate) * 100, 1),
            "ranking_reason": "; ".join(reasons) if reasons else "Eligible nearby driver",
            "score_breakdown": {
                "eta": round(score_eta, 1),
                "reliability": round(score_reliability, 1),
                "distance": round(score_distance, 1),
                "acceptance": round(score_acceptance, 1),
                "freshness": round(score_freshness, 1)
            }
        })

    # Sort descending by score, tie-breaking by ETA, distance, and driver ID
    scored.sort(key=lambda x: (-x["score"], x["eta_minutes"], x["distance_km"], str(x["id"])))
    return scored


# State transition validation
VALID_TRANSITIONS = {
    "draft": ["quoted", "cancelled"],
    "quoted": ["searching", "cancelled", "expired"],
    "searching": ["driver_offered", "retrying", "alternative_search", "unavailable", "cancelled"],
    "driver_offered": ["driver_accepted", "retrying", "alternative_search", "unavailable", "cancelled"],
    "driver_accepted": ["driver_arriving", "retrying", "alternative_search", "completed", "cancelled"],
    "driver_arriving": ["completed", "retrying", "alternative_search", "cancelled"],
    "retrying": ["driver_offered", "alternative_search", "fallback_offered", "unavailable", "cancelled"],
    "alternative_search": ["fallback_offered", "driver_offered", "unavailable", "cancelled"],
    "fallback_offered": ["completed", "unavailable", "cancelled"],
    "completed": [],
    "unavailable": [],
    "cancelled": [],
    "expired": []
}

def can_transition(current_status: str, target_status: str) -> bool:
    """Validates allowed state machine transitions for priority dispatch."""
    allowed = VALID_TRANSITIONS.get(current_status, [])
    return target_status in allowed

def get_last_resort_mobility_options(zone_name: str, city: str = "Jaipur") -> List[Dict[str, Any]]:
    """
    Returns verified/permitted last-resort mobility alternatives when cab dispatch fails (Section 21.2).
    """
    return [
        {
            "category": "auto_rickshaw",
            "title": "Government Prepaid Auto-Rickshaw Stand",
            "location_name": f"{zone_name} Main Circle Auto Stand",
            "walking_distance_m": 160,
            "walking_time_mins": 2,
            "availability": "Readily Available (On-demand physical boarding)",
            "estimated_fare": "₹90 - ₹120 (Standard Meter)",
            "action_text": "View Stand Location & Walking Route",
            "is_demo": True
        },
        {
            "category": "metro_transit",
            "title": "Jaipur Metro Rail (Pink Line)",
            "location_name": "Nearest Station: Railway Station / Sindhi Camp",
            "walking_distance_m": 450,
            "walking_time_mins": 6,
            "availability": "Trains every 8 minutes (Operational until 22:30)",
            "estimated_fare": "₹20 (Direct token/SmartCard)",
            "action_text": "Show Metro Schedule & Platform Access",
            "is_demo": True
        },
        {
            "category": "smart_pickup_relocation",
            "title": "Congestion-Free Main Road Pickup Bay",
            "location_name": f"{zone_name} Arterial Road Gate #2 Taxi Bay",
            "walking_distance_m": 120,
            "walking_time_mins": 2,
            "availability": "4 Drivers reported within 3 mins approach",
            "estimated_fare": "Standard fare applies (No surge)",
            "action_text": "Accept Relocation & Re-dispatch",
            "is_demo": True
        }
    ]
