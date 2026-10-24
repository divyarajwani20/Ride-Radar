import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from app.db.session import get_db
from app.models.models import (
    PriorityRequest, PriorityZone, Zone, Driver, DriverOfferAttempt,
    RideRecoveryEvent, ReserveCapacity, PickupSuggestion, FareQuote
)
from app.schemas.schemas import (
    PriorityQuoteRequest, PriorityQuoteResponse, PriorityDispatchRequest,
    PriorityStatusResponse, CandidateMatchExplain, DriverDetail
)
from app.services.priority_dispatch import (
    rank_priority_candidates, can_transition, get_last_resort_mobility_options
)
from app.core.config import settings

router = APIRouter()

@router.get("/priority/zones")
def list_priority_zones(db: Session = Depends(get_db)):
    """Lists configured high-need priority pickup zones (hospitals, railway stations, airport)."""
    p_zones = db.query(PriorityZone).join(Zone).all()
    res = []
    for pz in p_zones:
        z = pz.zone
        res.append({
            "id": pz.id,
            "zone_id": pz.zone_id,
            "zone_name": z.zone_name if z else "Unknown Zone",
            "category": pz.category,
            "is_enabled": pz.is_enabled,
            "center_lat": z.center_lat if z else 0,
            "center_lng": z.center_lng if z else 0,
            "verification_source": pz.verification_source,
            "coverage_notes": pz.coverage_notes
        })
    return res

@router.post("/priority/requests", response_model=PriorityQuoteResponse)
def request_priority_quote(req: PriorityQuoteRequest, db: Session = Depends(get_db)):
    """
    Validates a priority ride request, checks designated zone status,
    and returns a transparent fare quote and conditional commitment terms.
    """
    pickup_zone = db.query(Zone).filter(Zone.id == req.pickup_zone_id).first()
    dest_zone = db.query(Zone).filter(Zone.id == req.destination_zone_id).first()

    if not pickup_zone or not dest_zone:
        raise HTTPException(status_code=404, detail="Invalid pickup or destination zone ID")

    # Check whether pickup is designated priority zone
    priority_zone = db.query(PriorityZone).filter(
        PriorityZone.zone_id == pickup_zone.id,
        PriorityZone.is_enabled == True
    ).first()

    is_designated = priority_zone is not None
    priority_cat = priority_zone.category if priority_zone else None

    # Calculate transparent fare quote
    base_estimate = 180.0
    priority_fee = 50.0
    total_payable = base_estimate + priority_fee
    max_acceptable = max(req.max_acceptable_fare or 350.0, total_payable)

    if is_designated:
        explanation = f"Pickup is a verified high-need {priority_cat.replace('_', ' ')} zone. Eligible for priority dispatch channel and rapid fallback routing."
        eta_min, eta_max = 3, 6
    else:
        explanation = "Pickup is a non-designated location. Emergency priority dispatch will be attempted based on available nearby driver supply."
        eta_min, eta_max = 5, 10

    request_id = f"req_{uuid.uuid4().hex[:12]}"
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Store PriorityRequest record in 'quoted' status
    pr = PriorityRequest(
        id=request_id,
        passenger_id="demo_passenger",
        pickup_zone_id=pickup_zone.id,
        destination_zone_id=dest_zone.id,
        urgency_category=req.urgency_category or "medical",
        priority_fee=priority_fee,
        base_fare=base_estimate,
        max_total_fare=max_acceptable,
        commitment_type="priority_dispatch",
        policy_version="v1.0",
        status="quoted",
        current_attempt=0,
        max_attempts=3,
        refund_status="none"
    )
    db.add(pr)

    # Store FareQuote
    fq = FareQuote(
        id=f"fq_{uuid.uuid4().hex[:8]}",
        request_id=request_id,
        base_estimate=base_estimate,
        priority_fee=priority_fee,
        maximum_total=max_acceptable,
        currency="INR",
        terms_version="v1.0",
        refund_terms="100% priority fee refund if no verified ride is secured within dispatch budget.",
        expires_at=expires_at,
        source_type="demo"
    )
    db.add(fq)
    db.commit()

    return PriorityQuoteResponse(
        request_id=request_id,
        pickup_zone_name=pickup_zone.zone_name,
        is_designated_priority_zone=is_designated,
        priority_category=priority_cat,
        eligibility_explanation=explanation,
        base_estimate=base_estimate,
        priority_fee=priority_fee,
        total_payable=total_payable,
        max_acceptable_fare=max_acceptable,
        currency="INR",
        estimated_pickup_range_min=eta_min,
        estimated_pickup_range_max=eta_max,
        commitment_type="priority_dispatch",
        refund_terms="100% priority fee refund or void if no driver accepts within dispatch time budget.",
        policy_version="v1.0",
        expires_at=expires_at,
        is_demo=True
    )

@router.post("/priority/requests/{request_id}/dispatch", response_model=PriorityStatusResponse)
def dispatch_priority_request(
    request_id: str,
    dispatch_req: PriorityDispatchRequest,
    db: Session = Depends(get_db)
):
    """
    Executes emergency priority dispatch algorithm with idempotency protection.
    Ranks eligible drivers, sends offers, and handles declines/timeouts/cancellations with retries.
    """
    pr = db.query(PriorityRequest).filter(PriorityRequest.id == request_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Priority request not found")

    # Idempotency check: if request has already been dispatched with this key, return current state
    if pr.idempotency_key and pr.idempotency_key == dispatch_req.idempotency_key:
        return build_status_response(pr, db, "Idempotent dispatch request received: returning existing match state.")

    # Record idempotency key
    pr.idempotency_key = dispatch_req.idempotency_key

    # Fetch available drivers
    drivers = db.query(Driver).filter(Driver.is_available == True).all()
    candidates_raw = []
    for d in drivers:
        candidates_raw.append({
            "id": d.id,
            "display_name": d.display_name,
            "rating_mean": d.rating_mean,
            "rating_count": d.rating_count,
            "verified_driver_cancel_count": d.verified_driver_cancel_count,
            "eligible_ride_count": d.eligible_ride_count,
            "vehicle_model": d.vehicle_model,
            "vehicle_number": d.vehicle_number,
            "eta_minutes": 3 if "veteran" in d.id else (5 if "perfect" in d.id else 8),
            "distance_km": 1.2 if "veteran" in d.id else (2.0 if "perfect" in d.id else 3.5),
            "acceptance_rate_score": 92.0
        })

    ranked_candidates = rank_priority_candidates(candidates_raw)

    # Determine scenario behavior (from active scenario or parameter)
    scenario = dispatch_req.simulate_outcome or settings.ACTIVE_DEMO_SCENARIO

    now = datetime.utcnow()

    # Clear prior attempts for a fresh dispatch
    db.query(DriverOfferAttempt).filter(DriverOfferAttempt.request_id == pr.id).delete()
    db.query(RideRecoveryEvent).filter(RideRecoveryEvent.request_id == pr.id).delete()

    if scenario == "scenario_2_first_declines" or scenario == "force_decline":
        # Candidate 1 declines; Candidate 2 accepts
        cand1 = ranked_candidates[0]
        att1 = DriverOfferAttempt(
            request_id=pr.id,
            driver_id=cand1["id"],
            attempt_number=1,
            offered_at=now - timedelta(seconds=15),
            response_deadline=now - timedelta(seconds=5),
            responded_at=now - timedelta(seconds=8),
            outcome="declined",
            failure_reason="Driver unavailable / on another trip",
            source_type="demo"
        )
        db.add(att1)

        # Recovery event
        rec = RideRecoveryEvent(
            request_id=pr.id,
            event_type="retry_triggered",
            from_status="driver_offered",
            to_status="retrying",
            reason=f"Candidate {cand1['display_name']} declined offer. Retrying candidate #2.",
            created_at=now - timedelta(seconds=7)
        )
        db.add(rec)

        cand2 = ranked_candidates[1] if len(ranked_candidates) > 1 else cand1
        att2 = DriverOfferAttempt(
            request_id=pr.id,
            driver_id=cand2["id"],
            attempt_number=2,
            offered_at=now - timedelta(seconds=5),
            response_deadline=now + timedelta(seconds=20),
            responded_at=now - timedelta(seconds=1),
            outcome="accepted",
            source_type="demo"
        )
        db.add(att2)

        pr.status = "driver_accepted"
        pr.current_attempt = 2
        pr.confirmed_driver_id = cand2["id"]
        msg = f"Candidate #1 declined. Automatic recovery engaged: Candidate #2 ({cand2['display_name']}) accepted!"

    elif scenario == "scenario_3_first_times_out" or scenario == "force_timeout":
        cand1 = ranked_candidates[0]
        att1 = DriverOfferAttempt(
            request_id=pr.id,
            driver_id=cand1["id"],
            attempt_number=1,
            offered_at=now - timedelta(seconds=25),
            response_deadline=now - timedelta(seconds=5),
            responded_at=None,
            outcome="timed_out",
            failure_reason="Response deadline exceeded (20s timeout)",
            source_type="demo"
        )
        db.add(att1)

        rec = RideRecoveryEvent(
            request_id=pr.id,
            event_type="retry_triggered",
            from_status="driver_offered",
            to_status="retrying",
            reason="Offer timed out with candidate #1. Recorded in accountability ledger.",
            created_at=now - timedelta(seconds=4)
        )
        db.add(rec)

        cand2 = ranked_candidates[1] if len(ranked_candidates) > 1 else cand1
        att2 = DriverOfferAttempt(
            request_id=pr.id,
            driver_id=cand2["id"],
            attempt_number=2,
            offered_at=now - timedelta(seconds=3),
            response_deadline=now + timedelta(seconds=20),
            responded_at=now,
            outcome="accepted",
            source_type="demo"
        )
        db.add(att2)

        pr.status = "driver_accepted"
        pr.current_attempt = 2
        pr.confirmed_driver_id = cand2["id"]
        msg = f"Candidate #1 timed out after 20s. Automatic recovery dispatched Candidate #2 ({cand2['display_name']})."

    elif scenario == "scenario_4_accepted_cancels" or scenario == "force_cancel_after_accept":
        cand1 = ranked_candidates[0]
        att1 = DriverOfferAttempt(
            request_id=pr.id,
            driver_id=cand1["id"],
            attempt_number=1,
            offered_at=now - timedelta(minutes=2),
            response_deadline=now - timedelta(minutes=2),
            responded_at=now - timedelta(minutes=2),
            outcome="cancelled_after_accept",
            failure_reason="Driver vehicle flat tire / breakdown",
            source_type="demo"
        )
        db.add(att1)

        rec = RideRecoveryEvent(
            request_id=pr.id,
            event_type="recovery_dispatched",
            from_status="driver_accepted",
            to_status="retrying",
            reason="Driver cancelled after initial acceptance. Dispatched backup candidate without fare increment.",
            created_at=now - timedelta(minutes=1)
        )
        db.add(rec)

        cand2 = ranked_candidates[1] if len(ranked_candidates) > 1 else cand1
        att2 = DriverOfferAttempt(
            request_id=pr.id,
            driver_id=cand2["id"],
            attempt_number=2,
            offered_at=now - timedelta(seconds=45),
            response_deadline=now + timedelta(seconds=15),
            responded_at=now - timedelta(seconds=10),
            outcome="accepted",
            source_type="demo"
        )
        db.add(att2)

        pr.status = "driver_arriving"
        pr.current_attempt = 2
        pr.confirmed_driver_id = cand2["id"]
        msg = "Initial driver had a vehicle issue. Backup driver successfully secured and en route."

    elif scenario == "scenario_5_all_candidates_fail" or scenario == "force_all_fail":
        # All 3 attempts fail
        for i in range(1, 4):
            c = ranked_candidates[i - 1] if len(ranked_candidates) >= i else ranked_candidates[0]
            att = DriverOfferAttempt(
                request_id=pr.id,
                driver_id=c["id"],
                attempt_number=i,
                offered_at=now - timedelta(seconds=30 * (4 - i)),
                response_deadline=now - timedelta(seconds=30 * (4 - i) - 20),
                responded_at=now - timedelta(seconds=30 * (4 - i) - 15),
                outcome="declined",
                failure_reason="Nearby driver unavailable in heavy traffic",
                source_type="demo"
            )
            db.add(att)

        rec = RideRecoveryEvent(
            request_id=pr.id,
            event_type="alternative_search",
            from_status="retrying",
            to_status="unavailable",
            reason="Maximum dispatch retry budget reached (3 attempts). Priority fee refunded 100%.",
            created_at=now
        )
        db.add(rec)

        pr.status = "unavailable"
        pr.current_attempt = 3
        pr.confirmed_driver_id = None
        pr.refund_status = "refunded"
        msg = "All nearby candidates currently busy. Request marked unavailable; priority fee (₹50) refunded 100%."

    else:
        # Default: scenario_1_successful_match (immediate success with top candidate)
        top_cand = ranked_candidates[0]
        att1 = DriverOfferAttempt(
            request_id=pr.id,
            driver_id=top_cand["id"],
            attempt_number=1,
            offered_at=now - timedelta(seconds=10),
            response_deadline=now + timedelta(seconds=20),
            responded_at=now - timedelta(seconds=2),
            outcome="accepted",
            source_type="demo"
        )
        db.add(att1)

        pr.status = "driver_accepted"
        pr.current_attempt = 1
        pr.confirmed_driver_id = top_cand["id"]
        msg = f"Top-ranked priority candidate ({top_cand['display_name']}) accepted within 8 seconds!"

    db.commit()
    return build_status_response(pr, db, msg, ranked_candidates)

@router.get("/priority/requests/{request_id}/status", response_model=PriorityStatusResponse)
def get_priority_status(request_id: str, db: Session = Depends(get_db)):
    """Returns current state, candidate ranking, attempt ledger, and alternatives for a priority request."""
    pr = db.query(PriorityRequest).filter(PriorityRequest.id == request_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Priority request not found")

    return build_status_response(pr, db, f"Status: {pr.status.upper()}")

@router.post("/priority/requests/{request_id}/cancel")
def cancel_priority_request(request_id: str, db: Session = Depends(get_db)):
    """
    Cancels a priority request with validated state transition and executes refund policy.
    """
    pr = db.query(PriorityRequest).filter(PriorityRequest.id == request_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Priority request not found")

    if not can_transition(pr.status, "cancelled"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel request in current status '{pr.status}'. Invalid state transition."
        )

    pr.status = "cancelled"
    pr.refund_status = "refunded"
    
    rec = RideRecoveryEvent(
        request_id=pr.id,
        event_type="passenger_cancelled",
        from_status=pr.status,
        to_status="cancelled",
        reason="Passenger cancelled request prior to pickup. Priority fee refunded 100% per disclosed policy.",
        created_at=datetime.utcnow()
    )
    db.add(rec)
    db.commit()

    return {
        "request_id": pr.id,
        "status": "cancelled",
        "refund_status": "refunded",
        "message": "Priority ride request cancelled successfully. 100% priority fee has been refunded/voided."
    }

@router.post("/priority/requests/{request_id}/pickup-suggestions")
def get_pickup_suggestions(request_id: str, db: Session = Depends(get_db)):
    """
    Returns smart pickup relocation suggestions to bypass local bottleneck points (Section 21.3).
    """
    pr = db.query(PriorityRequest).filter(PriorityRequest.id == request_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Priority request not found")

    pickup_zone = db.query(Zone).filter(Zone.id == pr.pickup_zone_id).first()
    zone_name = pickup_zone.zone_name if pickup_zone else "Selected Pickup"

    suggestions = [
        {
            "id": 1,
            "suggested_name": f"{zone_name} - Main Arterial Gate #1 Taxi Bay",
            "walking_distance_m": 120,
            "walking_time_mins": 2,
            "eta_saved_mins": 4,
            "reason": "Allows incoming drivers to avoid congested internal drop-off loops and reach you 4 minutes faster.",
            "is_recommended": True
        },
        {
            "id": 2,
            "suggested_name": f"{zone_name} - Metro Link Pedestrian Subway",
            "walking_distance_m": 250,
            "walking_time_mins": 3,
            "eta_saved_mins": 6,
            "reason": "Clear curb space on opposite dual carriageway with safe, well-lit covered pedestrian subway access.",
            "is_recommended": False
        }
    ]
    return {
        "request_id": request_id,
        "current_pickup": zone_name,
        "suggestions": suggestions,
        "is_demo": True
    }

@router.get("/priority/reserve-capacity")
def get_reserve_capacity(zone_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns emergency mobility reserve fleet capacity (Section 22.2)."""
    query = db.query(ReserveCapacity).join(Zone)
    if zone_id:
        query = query.filter(ReserveCapacity.zone_id == zone_id)
    
    records = query.all()
    res = []
    for rc in records:
        res.append({
            "id": rc.id,
            "zone_id": rc.zone_id,
            "zone_name": rc.zone.zone_name if rc.zone else "Zone",
            "fleet_or_demo_source": rc.fleet_or_demo_source,
            "vehicle_category": rc.vehicle_category,
            "available_count": rc.available_count,
            "coverage_hours": f"{rc.coverage_start} - {rc.coverage_end}",
            "is_demo": rc.is_demo,
            "last_updated": rc.updated_at
        })
    return res

def build_status_response(
    pr: PriorityRequest,
    db: Session,
    message: str,
    ranked_candidates: Optional[List[Dict[str, Any]]] = None
) -> PriorityStatusResponse:
    """Helper to assemble rich status response with timeline, candidate ranking, and recovery events."""
    pickup_zone = db.query(Zone).filter(Zone.id == pr.pickup_zone_id).first()
    dest_zone = db.query(Zone).filter(Zone.id == pr.destination_zone_id).first()
    
    confirmed_driver_detail = None
    if pr.confirmed_driver_id:
        d = db.query(Driver).filter(Driver.id == pr.confirmed_driver_id).first()
        if d:
            from app.services.ranking import calculate_adjusted_rating, calculate_smoothed_cancel_rate, get_rating_confidence
            adj_rating = calculate_adjusted_rating(d.rating_mean, d.rating_count)
            smoothed_cancel = calculate_smoothed_cancel_rate(d.verified_driver_cancel_count, d.eligible_ride_count)
            _, conf_lbl = get_rating_confidence(d.rating_count)
            confirmed_driver_detail = DriverDetail(
                id=d.id,
                display_name=d.display_name,
                rating_mean=d.rating_mean,
                rating_count=d.rating_count,
                adjusted_rating=adj_rating,
                verified_driver_cancel_count=d.verified_driver_cancel_count,
                eligible_ride_count=d.eligible_ride_count,
                smoothed_driver_cancel_rate=smoothed_cancel,
                vehicle_model=d.vehicle_model,
                vehicle_number=d.vehicle_number,
                confidence_label=conf_lbl,
                is_demo=d.is_demo
            )

    # Timeline step: 0: Quoted, 1: Searching, 2: Driver Contacted, 3: Accepted, 4: Arriving, 5: Completed
    timeline_steps = {
        "quoted": 0,
        "searching": 1,
        "driver_offered": 2,
        "driver_accepted": 3,
        "driver_arriving": 4,
        "completed": 5,
        "retrying": 2,
        "alternative_search": 2,
        "fallback_offered": 3,
        "unavailable": 1,
        "cancelled": 0
    }

    # Fetch attempts
    attempts = db.query(DriverOfferAttempt).filter(DriverOfferAttempt.request_id == pr.id).all()
    att_list = [
        {
            "attempt_number": a.attempt_number,
            "driver_name": a.driver.display_name if a.driver else "Driver",
            "outcome": a.outcome,
            "failure_reason": a.failure_reason,
            "offered_at": a.offered_at,
            "responded_at": a.responded_at
        }
        for a in attempts
    ]

    # Fetch recovery events
    recoveries = db.query(RideRecoveryEvent).filter(RideRecoveryEvent.request_id == pr.id).all()
    rec_list = [
        {
            "event_type": r.event_type,
            "from_status": r.from_status,
            "to_status": r.to_status,
            "reason": r.reason,
            "timestamp": r.created_at
        }
        for r in recoveries
    ]

    # Mobility alternatives (shown especially if unavailable or retrying)
    alternatives = get_last_resort_mobility_options(
        pickup_zone.zone_name if pickup_zone else "Jaipur Central"
    )

    # Candidate ranking list
    cand_explain_list = []
    if ranked_candidates:
        for c in ranked_candidates[:3]:
            cand_explain_list.append(CandidateMatchExplain(
                driver_id=c["id"],
                driver_name=c["display_name"],
                score=c["score"],
                eta_minutes=c["eta_minutes"],
                distance_km=c["distance_km"],
                reliability_rate=c["reliability_rate"],
                vehicle=c.get("vehicle_model", "Sedan"),
                ranking_reason=c["ranking_reason"]
            ))

    return PriorityStatusResponse(
        request_id=pr.id,
        status=pr.status,
        urgency_category=pr.urgency_category,
        pickup_zone=pickup_zone.zone_name if pickup_zone else "Pickup Zone",
        destination_zone=dest_zone.zone_name if dest_zone else "Destination Zone",
        base_fare=pr.base_fare,
        priority_fee=pr.priority_fee,
        total_fare=pr.base_fare + pr.priority_fee,
        refund_status=pr.refund_status,
        current_attempt=pr.current_attempt,
        max_attempts=pr.max_attempts,
        confirmed_driver=confirmed_driver_detail,
        candidate_ranking=cand_explain_list,
        attempt_history=att_list,
        recovery_events=rec_list,
        mobility_alternatives=alternatives,
        status_timeline_step=timeline_steps.get(pr.status, 1),
        message=message,
        is_demo=True,
        updated_at=pr.updated_at or datetime.utcnow()
    )
