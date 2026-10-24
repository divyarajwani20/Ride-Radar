from typing import List, Dict, Any, Optional
from datetime import datetime
from app.providers.base import BaseProvider

class DemoProvider(BaseProvider):
    """
    Demo Provider Adapter.
    Generates realistic, deterministic seeded demo ride data explicitly labeled as 'demo'.
    Allows full hackathon demonstration of cross-provider comparison, driver ratings,
    and availability without pretending to have private API access.
    """
    def __init__(self, provider_id: str = "demo_uber", name: str = "Uber (Demo Mode)"):
        super().__init__(provider_id=provider_id, name=name, is_demo=True)
        self.app_url = "https://m.uber.com"

    def get_provider_status(self) -> Dict[str, Any]:
        return {
            "id": self.provider_id,
            "name": self.name,
            "status": "demo",
            "integration_type": "simulated_seeded",
            "last_synced_at": datetime.utcnow(),
            "status_message": "Seeded synthetic data for demonstration. All drivers and fares are fictional.",
            "app_url": self.app_url,
            "is_demo": True
        }

    def get_ride_estimates(
        self,
        origin_zone_id: str,
        destination_zone_id: str,
        departure_time: Optional[datetime] = None,
        ride_type: Optional[str] = "all"
    ) -> List[Dict[str, Any]]:
        # This will query seeded demo ride options from the database
        return []

    def get_availability(self, zone_id: str) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "status": "demo",
            "available_rides": 12,
            "message": "Demo simulated availability."
        }

    def get_driver_details(self, driver_id: str) -> Optional[Dict[str, Any]]:
        return None
