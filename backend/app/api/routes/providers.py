from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.models import Provider
from app.schemas.schemas import ProviderOut, DataSourceSettingsOut
from app.core.config import settings
from app.providers import UberProvider, OlaProvider, RapidoProvider, DemoProvider

router = APIRouter()

@router.get("/providers", response_model=List[ProviderOut])
def get_providers(db: Session = Depends(get_db)):
    """Returns status and provenance for all registered mobility providers."""
    providers = db.query(Provider).all()
    res = []
    for p in providers:
        res.append(ProviderOut(
            id=p.id,
            name=p.name,
            status=p.status,
            integration_type=p.integration_type,
            last_synced_at=p.last_synced_at,
            status_message=p.status_message,
            app_url=p.app_url,
            is_demo=p.status == "demo"
        ))
    return res

@router.get("/settings/data-sources", response_model=DataSourceSettingsOut)
def get_data_sources_settings(db: Session = Depends(get_db)):
    """
    Transparently reveals provider connection status and missing credentials without leaking secrets.
    """
    providers = db.query(Provider).all()
    prov_out = [
        ProviderOut(
            id=p.id,
            name=p.name,
            status=p.status,
            integration_type=p.integration_type,
            last_synced_at=p.last_synced_at,
            status_message=p.status_message,
            app_url=p.app_url,
            is_demo=p.status == "demo"
        )
        for p in providers
    ]

    credential_status = {
        "UBER_CLIENT_ID": "Configured" if settings.UBER_CLIENT_ID else "Missing (Operating in Demo/Handoff mode)",
        "OLA_API_KEY": "Configured" if settings.OLA_API_KEY else "Missing (Operating in Demo/Handoff mode)",
        "RAPIDO_API_KEY": "Configured" if settings.RAPIDO_API_KEY else "Missing (Operating in Demo/Handoff mode)"
    }

    return DataSourceSettingsOut(
        providers=prov_out,
        demo_mode=settings.DEMO_MODE,
        data_retention_policy="Non-identifying aggregated metrics retained for 24 hours. No exact passenger GPS coordinates or personal chats are stored.",
        privacy_notice="RideRadar respects user privacy and provider intellectual property. Real-time access to driver inventory and exact live rates requires official provider authorization. Demo data is explicitly fictional and deterministic for testing.",
        credential_status=credential_status
    )
