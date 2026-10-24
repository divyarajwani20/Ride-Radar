from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Zone
from app.services.priority_dispatch import get_last_resort_mobility_options

router = APIRouter()

@router.get("/mobility/alternatives")
def get_mobility_alternatives(
    zone_id: str = Query(default="zone_sms_hospital"),
    db: Session = Depends(get_db)
):
    """
    Returns supported last-resort mobility alternatives (Section 21.2):
    Prepaid auto-rickshaw stands, metro station access, and smart pickup relocations.
    """
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    zone_name = zone.zone_name if zone else "Jaipur Central"

    alternatives = get_last_resort_mobility_options(zone_name=zone_name, city=zone.city if zone else "Jaipur")
    return {
        "zone_id": zone_id,
        "zone_name": zone_name,
        "alternatives": alternatives,
        "notice": "DEMO DATA: Transit stations and prepaid auto stands are verified Jaipur municipal landmarks.",
        "is_demo": True
    }
