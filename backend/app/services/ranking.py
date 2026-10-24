import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

GLOBAL_RATING_MEAN = 4.5
PRIOR_STRENGTH_M = 10.0

DEFAULT_WEIGHTS = {
    "rating": 0.45,
    "reliability": 0.25,
    "eta": 0.15,
    "fare": 0.10,
    "freshness": 0.05
}

def calculate_adjusted_rating(
    driver_mean: float,
    rating_count: int,
    global_mean: float = GLOBAL_RATING_MEAN,
    prior_strength: float = PRIOR_STRENGTH_M
) -> float:
    """
    Bayesian shrinkage adjustment:
    adjusted_rating = (n * driver_mean + m * global_mean) / (n + m)
    Prevents a driver with 1 single 5-star review from beating a consistently strong driver with 500 reviews.
    """
    if rating_count <= 0:
        return global_mean
    return round((rating_count * driver_mean + prior_strength * global_mean) / (rating_count + prior_strength), 2)

def calculate_smoothed_cancel_rate(
    driver_cancels: int,
    eligible_rides: int
) -> float:
    """
    Laplace-smoothed cancellation rate to avoid 0% with 1 ride or 100% with 1 cancellation.
    smoothed_rate = (cancels + 1) / (eligible_rides + 10)
    """
    if eligible_rides <= 0:
        return 0.08  # Default conservative assumption (8%)
    return round((driver_cancels + 1.0) / (eligible_rides + 10.0), 4)

def get_rating_confidence(rating_count: int) -> Tuple[str, str]:
    """Returns (confidence_tier, confidence_label)."""
    if rating_count >= 50:
        return ("high", "High confidence")
    elif rating_count >= 10:
        return ("medium", "Moderate sample size")
    elif rating_count > 0:
        return ("low", "Limited rating history")
    else:
        return ("none", "No verified history")

def rank_ride_options(
    options: List[Dict[str, Any]],
    sort_by: str = "best_overall",
    custom_weights: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    Ranks ride options using transparent, explainable normalized scores.
    Handles missing metrics with dynamic weight renormalization.
    """
    if not options:
        return []

    weights = custom_weights or DEFAULT_WEIGHTS.copy()
    
    # 1. Find best valid fare and best valid ETA in this result set for relative scoring
    valid_fares = [opt.get("estimated_fare") for opt in options if opt.get("estimated_fare") is not None and opt.get("estimated_fare") > 0]
    valid_etas = [opt.get("pickup_eta_minutes") for opt in options if opt.get("pickup_eta_minutes") is not None and opt.get("pickup_eta_minutes") > 0]
    
    best_fare = min(valid_fares) if valid_fares else None
    best_eta = min(valid_etas) if valid_etas else None
    
    now = datetime.now(timezone.utc)
    ranked = []

    for opt in options:
        driver = opt.get("driver") or {}
        rating_mean = driver.get("rating_mean", GLOBAL_RATING_MEAN)
        rating_count = driver.get("rating_count", 0)
        driver_cancels = driver.get("verified_driver_cancel_count", 0)
        eligible_rides = driver.get("eligible_ride_count", 0)
        
        # Bayesian adjusted rating
        adjusted_rating = calculate_adjusted_rating(rating_mean, rating_count)
        smoothed_cancel_rate = calculate_smoothed_cancel_rate(driver_cancels, eligible_rides)
        conf_tier, conf_label = get_rating_confidence(rating_count)

        driver_info = {
            "id": driver.get("id", "fictional_demo_driver"),
            "display_name": driver.get("display_name", "Demo Driver"),
            "rating_mean": rating_mean,
            "rating_count": rating_count,
            "adjusted_rating": adjusted_rating,
            "verified_driver_cancel_count": driver_cancels,
            "eligible_ride_count": eligible_rides,
            "smoothed_driver_cancel_rate": smoothed_cancel_rate,
            "vehicle_model": driver.get("vehicle_model", "Sedan Prime"),
            "vehicle_number": driver.get("vehicle_number", "RJ-14-EA-1024"),
            "confidence_label": conf_label,
            "is_demo": opt.get("is_demo", True)
        }

        # Raw component evaluations (0 to 100)
        # 1. Rating score (convert 1-5 scale to 0-100)
        score_rating = max(0.0, min(100.0, ((adjusted_rating - 1.0) / 4.0) * 100.0))
        
        # 2. Reliability score: 100 * (1 - smoothed_driver_cancel_rate)
        score_reliability = max(0.0, min(100.0, 100.0 * (1.0 - smoothed_cancel_rate)))
        
        # 3. ETA score
        eta_val = opt.get("pickup_eta_minutes")
        has_eta = eta_val is not None and eta_val > 0
        if has_eta and best_eta:
            score_eta = max(0.0, min(100.0, 100.0 * (best_eta / max(eta_val, best_eta, 1))))
        else:
            score_eta = None

        # 4. Fare score
        fare_val = opt.get("estimated_fare")
        has_fare = fare_val is not None and fare_val > 0
        if has_fare and best_fare:
            score_fare = max(0.0, min(100.0, 100.0 * (best_fare / max(fare_val, best_fare, 1))))
        else:
            score_fare = None

        # 5. Freshness score (decay as data ages)
        obs_time = opt.get("observed_at")
        if isinstance(obs_time, str):
            try:
                obs_dt = datetime.fromisoformat(obs_time.replace("Z", "+00:00"))
            except Exception:
                obs_dt = now
        elif isinstance(obs_time, datetime):
            obs_dt = obs_time if obs_time.tzinfo else obs_time.replace(tzinfo=timezone.utc)
        else:
            obs_dt = now

        age_seconds = max(0, (now - obs_dt).total_seconds())
        # Halflife of 30 minutes (1800 seconds)
        score_freshness = max(0.0, min(100.0, 100.0 * math.exp(-age_seconds / 1800.0)))

        # Dynamic weight renormalization for available components
        active_weights = {}
        active_components = {}
        
        active_weights["rating"] = weights["rating"]
        active_components["rating"] = score_rating
        
        active_weights["reliability"] = weights["reliability"]
        active_components["reliability"] = score_reliability
        
        if score_eta is not None:
            active_weights["eta"] = weights["eta"]
            active_components["eta"] = score_eta
            
        if score_fare is not None:
            active_weights["fare"] = weights["fare"]
            active_components["fare"] = score_fare
            
        active_weights["freshness"] = weights["freshness"]
        active_components["freshness"] = score_freshness

        total_weight = sum(active_weights.values())
        renormalized_weights = {k: round(v / total_weight, 4) for k, v in active_weights.items()}

        total_score = sum(renormalized_weights[k] * active_components[k] for k in active_components)
        total_score = round(total_score, 1)

        # Generate clear, human-readable explainability reason
        explanation_parts = []
        if adjusted_rating >= 4.7:
            explanation_parts.append("Exceptional driver rating")
        elif adjusted_rating >= 4.4:
            explanation_parts.append("Strong driver rating")
        elif adjusted_rating < 4.0:
            explanation_parts.append("Below-average driver rating")

        if smoothed_cancel_rate <= 0.05:
            explanation_parts.append("very low cancellation risk")
        elif smoothed_cancel_rate >= 0.15:
            explanation_parts.append("elevated driver cancellation history")

        if has_eta and best_eta:
            if eta_val <= best_eta + 1:
                explanation_parts.append("fastest pickup ETA")
            elif eta_val > best_eta + 5:
                explanation_parts.append("longer pickup wait")

        if has_fare and best_fare:
            if fare_val <= best_fare + 10:
                explanation_parts.append("competitive fare")
            elif fare_val > best_fare + 50:
                explanation_parts.append("premium fare")

        explanation = "; ".join(explanation_parts) if explanation_parts else "Balanced score across all metrics."
        if conf_tier == "low":
            explanation += " (Note: Limited review sample)."

        ranked.append({
            **opt,
            "driver": driver_info,
            "score": total_score,
            "score_breakdown": {
                "rating": round(score_rating, 1),
                "reliability": round(score_reliability, 1),
                "eta": round(score_eta, 1) if score_eta is not None else 0.0,
                "fare": round(score_fare, 1) if score_fare is not None else 0.0,
                "freshness": round(score_freshness, 1),
                "active_weights": renormalized_weights
            },
            "ranking_explanation": explanation,
            "confidence": conf_tier
        })

    # Sort according to selected criteria with deterministic tie-breaking
    if sort_by == "best_driver_rating":
        ranked.sort(
            key=lambda x: (
                -(x["driver"]["adjusted_rating"] if x.get("driver") else 0),
                -(x["score_breakdown"]["reliability"]),
                x.get("pickup_eta_minutes") or 999,
                x.get("estimated_fare") or 9999,
                str(x.get("id"))
            )
        )
    elif sort_by == "lowest_fare":
        ranked.sort(
            key=lambda x: (
                x.get("estimated_fare") or 9999,
                -x["score"],
                x.get("pickup_eta_minutes") or 999,
                str(x.get("id"))
            )
        )
    elif sort_by == "fastest_pickup":
        ranked.sort(
            key=lambda x: (
                x.get("pickup_eta_minutes") or 999,
                -x["score"],
                x.get("estimated_fare") or 9999,
                str(x.get("id"))
            )
        )
    else:  # default: best_overall (driver-first)
        ranked.sort(
            key=lambda x: (
                -x["score"],
                -(x["driver"]["adjusted_rating"] if x.get("driver") else 0),
                x.get("pickup_eta_minutes") or 999,
                x.get("estimated_fare") or 9999,
                str(x.get("id"))
            )
        )

    return ranked
