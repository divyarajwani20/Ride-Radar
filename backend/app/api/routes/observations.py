from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from app.db.session import get_db
from app.models.models import UserObservation, Zone, Provider
from app.schemas.schemas import ObservationCreate, ObservationOut

router = APIRouter()

@router.post("/observations", response_model=ObservationOut)
def submit_observation(obs: ObservationCreate, db: Session = Depends(get_db)):
    """
    Optional, consent-based passenger observation submission (Section 9.B).
    Reports event type (available, cancelled, etc.) without collecting exact passenger GPS or private chats.
    """
    provider = db.query(Provider).filter(Provider.id == obs.provider_id).first()
    zone = db.query(Zone).filter(Zone.id == obs.zone_id).first()
    if not provider or not zone:
        raise HTTPException(status_code=400, detail="Invalid provider or zone ID")

    record = UserObservation(
        provider_id=obs.provider_id,
        zone_id=obs.zone_id,
        event_type=obs.event_type,
        cancellation_actor=obs.cancellation_actor,
        observed_at=datetime.utcnow(),
        optional_fare=obs.optional_fare,
        optional_eta=obs.optional_eta,
        validation_status="community_observation",
        consent_recorded=obs.consent_recorded
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ObservationOut(
        id=record.id,
        provider_id=record.provider_id,
        zone_id=record.zone_id,
        event_type=record.event_type,
        cancellation_actor=record.cancellation_actor,
        observed_at=record.observed_at,
        validation_status=record.validation_status,
        is_demo=True
    )

@router.get("/observations", response_model=List[ObservationOut])
def list_observations(db: Session = Depends(get_db)):
    records = db.query(UserObservation).order_by(UserObservation.created_at.desc()).limit(50).all()
    return [
        ObservationOut(
            id=r.id,
            provider_id=r.provider_id,
            zone_id=r.zone_id,
            event_type=r.event_type,
            cancellation_actor=r.cancellation_actor,
            observed_at=r.observed_at,
            validation_status=r.validation_status,
            is_demo=True
        )
        for r in records
    ]
