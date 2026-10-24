from typing import List, Dict, Any, Optional
from datetime import datetime
from app.providers.base import BaseProvider
from app.core.config import settings

class UberProvider(BaseProvider):
    """
    Official Uber Provider Adapter.
    In accordance with Section 2, if no official partner API credentials are provided,
    this adapter honestly returns status 'not_connected' and offers the official web/app handoff link.
    """
    def __init__(self):
        super().__init__(provider_id="uber", name="Uber", is_demo=False)
        self.app_url = "https://m.uber.com/looking"

    def get_provider_status(self) -> Dict[str, Any]:
        has_credentials = bool(settings.UBER_CLIENT_ID and settings.UBER_CLIENT_SECRET)
        if has_credentials:
            return {
                "id": self.provider_id,
                "name": self.name,
                "status": "connected",
                "integration_type": "official_oauth",
                "last_synced_at": datetime.utcnow(),
                "status_message": "Connected via official Uber Rides API partner credentials.",
                "app_url": self.app_url,
                "is_demo": False
            }
        return {
            "id": self.provider_id,
            "name": self.name,
            "status": "not_connected",
            "integration_type": "official_oauth",
            "last_synced_at": None,
            "status_message": "Official Uber partner API credentials not configured. Direct web booking link available.",
            "app_url": self.app_url,
            "is_demo": False
        }

    def get_ride_estimates(
        self,
        origin_zone_id: str,
        destination_zone_id: str,
        departure_time: Optional[datetime] = None,
        ride_type: Optional[str] = "all"
    ) -> List[Dict[str, Any]]:
        # If not connected, return empty list (or fallback handoff option)
        # Never fabricate live data as official API data.
        return []

    def get_availability(self, zone_id: str) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "status": "not_connected",
            "available_rides": 0,
            "message": "Live availability requires approved Uber Fleet/Partner API access."
        }

    def get_driver_details(self, driver_id: str) -> Optional[Dict[str, Any]]:
        return None
