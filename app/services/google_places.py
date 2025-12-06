"""Client to interact with the internal Auphere Places microservice."""
from typing import Any, Dict, Optional

import httpx

from app.config import settings


class PlacesServiceClient:
    """HTTP client wrapper for the auphere-places microservice."""

    def __init__(self) -> None:
        self.base_url = settings.places_service_url.rstrip("/")
        self.admin_token = settings.places_service_admin_token
        self.timeout = settings.places_service_timeout

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.admin_token:
            headers["X-Admin-Token"] = self.admin_token
        return headers

    async def search_places(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy search requests to the places service."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/places/search",
                params=params,
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get place detail (photos + reviews) from the places service."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/places/{place_id}",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()


# Global instance
places_service = PlacesServiceClient()
