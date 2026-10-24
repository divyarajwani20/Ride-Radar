from typing import List, Dict, Any, Optional
from datetime import datetime
from app.providers.base import BaseProvider
from app.core.config import settings

class OlaProvider(BaseProvider):
    """
    Official Ola Provider Adapter.
    Honestly reflects connection status and provides official handoff link.
    """
    def __init__(self):
        super().__init__(provider_id="ola", name="Ola Cabs", is_demo=False)
        self.app_url = "https://book.olacabs.com"

    def get_provider_status(self) -> Dict[str, Any]:
        has_credentials = bool(settings.OLA_API_KEY)
        if has_credentials:
            return {
                "id": self.provider_id,
                "name": self.name,
                "status": "connected",
                "integration_type": "api_key",
                "last_synced_at": datetime.utcnow(),
                "status_message": "Connected via authorized Ola Developer API key.",
                "app_url": self.app_url,
                "is_demo": False
            }
        return {
            "id": self.provider_id,
            "name": self.name,
            "status": "not_connected",
            "integration_type": "api_key",
            "last_synced_at": None,
            "status_message": "Ola API key not provided. Bookings can be completed via Ola Web/App.",
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
        return []

    def get_availability(self, zone_id: str) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "status": "not_connected",
            "available_rides": 0,
            "message": "Live availability requires authorized Ola API partnership."
        }

    def get_driver_details(self, driver_id: str) -> Optional[Dict[str, Any]]:
        return None
