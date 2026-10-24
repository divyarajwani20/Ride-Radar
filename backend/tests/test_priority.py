import pytest
from app.services.priority_dispatch import (
    rank_priority_candidates,
    can_transition,
    get_last_resort_mobility_options
)

def test_candidate_ranking_prioritizes_eta_and_reliability():
    """Emergency candidate ranking scores closest and most reliable drivers highest."""
    candidates = [
        {
            "id": "cand_far",
            "display_name": "Far Driver",
            "eta_minutes": 14,
            "distance_km": 4.5,
            "verified_driver_cancel_count": 8,
            "eligible_ride_count": 50
        },
        {
            "id": "cand_close_reliable",
            "display_name": "Rapid Hospital Responder",
            "eta_minutes": 3,
            "distance_km": 1.0,
            "verified_driver_cancel_count": 2,
            "eligible_ride_count": 120
        }
    ]
    ranked = rank_priority_candidates(candidates)
    assert ranked[0]["id"] == "cand_close_reliable"
    assert ranked[0]["score"] > ranked[1]["score"]
    assert "Immediate proximity" in ranked[0]["ranking_reason"]

def test_state_machine_valid_and_invalid_transitions():
    """State machine allows only authorized lifecycle transitions (Section 28)."""
    assert can_transition("draft", "quoted") is True
    assert can_transition("quoted", "searching") is True
    assert can_transition("searching", "driver_offered") is True
    assert can_transition("driver_offered", "driver_accepted") is True
    assert can_transition("driver_accepted", "driver_arriving") is True
    assert can_transition("driver_arriving", "completed") is True

    # Invalid transitions
    assert can_transition("completed", "searching") is False  # Completed cannot revert!
    assert can_transition("cancelled", "searching") is False
    assert can_transition("draft", "completed") is False

def test_last_resort_mobility_options():
    """When dispatch cannot secure a cab, verified alternatives must be provided."""
    options = get_last_resort_mobility_options("SMS Hospital", "Jaipur")
    assert len(options) >= 3
    categories = [o["category"] for o in options]
    assert "auto_rickshaw" in categories
    assert "metro_transit" in categories
    assert "smart_pickup_relocation" in categories
