import pytest
from app.services.ranking import (
    calculate_adjusted_rating,
    calculate_smoothed_cancel_rate,
    rank_ride_options
)

def test_bayesian_adjusted_rating_small_sample():
    """A driver with 2 reviews at 5.0 stars should be pulled towards the global mean (4.5)."""
    adj = calculate_adjusted_rating(driver_mean=5.0, rating_count=2, global_mean=4.5, prior_strength=10.0)
    # (2 * 5.0 + 10 * 4.5) / 12 = 55 / 12 = 4.58
    assert adj == 4.58
    assert adj < 5.0

def test_bayesian_adjusted_rating_large_sample():
    """A driver with 340 reviews at 4.88 stars should retain their score."""
    adj = calculate_adjusted_rating(driver_mean=4.88, rating_count=340, global_mean=4.5, prior_strength=10.0)
    # (340 * 4.88 + 10 * 4.5) / 350 = 4.87
    assert adj >= 4.86
    # Confirms a 4.88 driver with 340 reviews beats a 5.0 driver with 2 reviews!
    small_sample_adj = calculate_adjusted_rating(driver_mean=5.0, rating_count=2)
    assert adj > small_sample_adj

def test_smoothed_cancel_rate():
    """Laplace smoothing prevents extreme 0% or 100% rates from tiny counts."""
    # 0 cancels out of 0 rides returns conservative 8%
    assert calculate_smoothed_cancel_rate(0, 0) == 0.08
    # 0 cancels out of 2 rides: (0 + 1) / (2 + 10) = 1/12 = 0.0833
    rate_small = calculate_smoothed_cancel_rate(0, 2)
    assert rate_small > 0.05
    # 2 cancels out of 100 rides: (2 + 1) / (100 + 10) = 3/110 = 0.0273
    rate_large = calculate_smoothed_cancel_rate(2, 100)
    assert rate_large < 0.035

def test_missing_data_weight_renormalization():
    """When ETA or fare is missing, remaining weights must renormalize to 1.0 (100%)."""
    options = [
        {
            "id": "opt_test_missing_eta",
            "provider": "Uber",
            "provider_id": "uber",
            "ride_type": "sedan",
            "estimated_fare": 200.0,
            "pickup_eta_minutes": None,  # Missing ETA!
            "availability_status": "available",
            "driver": {
                "id": "d1",
                "display_name": "Test Driver",
                "rating_mean": 4.8,
                "rating_count": 100,
                "verified_driver_cancel_count": 2,
                "eligible_ride_count": 100
            },
            "observed_at": "2026-10-24T00:00:00Z",
            "is_demo": True
        }
    ]
    ranked = rank_ride_options(options)
    assert len(ranked) == 1
    active_weights = ranked[0]["score_breakdown"]["active_weights"]
    assert "eta" not in active_weights
    total_w = sum(active_weights.values())
    assert abs(total_w - 1.0) < 0.01  # Sums to 1.0
    assert ranked[0]["score"] > 0

def test_sorting_modes():
    """Tests that sort_by accurately re-orders options."""
    options = [
        {
            "id": "opt_cheap",
            "provider": "QuickRide",
            "provider_id": "quickride",
            "ride_type": "economy",
            "estimated_fare": 100.0,
            "pickup_eta_minutes": 10,
            "driver": {"id": "d1", "rating_mean": 4.2, "rating_count": 20, "verified_driver_cancel_count": 3, "eligible_ride_count": 20}
        },
        {
            "id": "opt_fast",
            "provider": "Rapido",
            "provider_id": "rapido",
            "ride_type": "auto",
            "estimated_fare": 150.0,
            "pickup_eta_minutes": 2,
            "driver": {"id": "d2", "rating_mean": 4.4, "rating_count": 40, "verified_driver_cancel_count": 2, "eligible_ride_count": 40}
        },
        {
            "id": "opt_best_driver",
            "provider": "Uber",
            "provider_id": "uber",
            "ride_type": "sedan",
            "estimated_fare": 220.0,
            "pickup_eta_minutes": 5,
            "driver": {"id": "d3", "rating_mean": 4.95, "rating_count": 300, "verified_driver_cancel_count": 1, "eligible_ride_count": 300}
        }
    ]

    by_rating = rank_ride_options(options, sort_by="best_driver_rating")
    assert by_rating[0]["id"] == "opt_best_driver"

    by_fare = rank_ride_options(options, sort_by="lowest_fare")
    assert by_fare[0]["id"] == "opt_cheap"

    by_eta = rank_ride_options(options, sort_by="fastest_pickup")
    assert by_eta[0]["id"] == "opt_fast"
