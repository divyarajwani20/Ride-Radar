from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class BaseProvider(ABC):
    """
    Abstract Provider Adapter Interface for RideRadar.
    Ensures clear separation between real provider integrations and demo/simulated data.
    Never scrapes undocumented endpoints or fakes live connections.
    """
    def __init__(self, provider_id: str, name: str, is_demo: bool = True):
        self.provider_id = provider_id
        self.name = name
        self.is_demo = is_demo

    @abstractmethod
    def get_provider_status(self) -> Dict[str, Any]:
        """Returns connection status, integration type, and sync info."""
        pass

    @abstractmethod
    def get_ride_estimates(
        self,
        origin_zone_id: str,
        destination_zone_id: str,
        departure_time: Optional[datetime] = None,
        ride_type: Optional[str] = "all"
    ) -> List[Dict[str, Any]]:
        """Returns normalized ride option estimates."""
        pass

    @abstractmethod
    def get_availability(self, zone_id: str) -> Dict[str, Any]:
        """Returns zone-level ride availability if supported."""
        pass

    @abstractmethod
    def get_driver_details(self, driver_id: str) -> Optional[Dict[str, Any]]:
        """Returns driver rating and reliability details if explicitly permitted."""
        pass
