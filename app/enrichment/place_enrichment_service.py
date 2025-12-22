"""
Enrichment service for adding Foursquare and social media data to places.

This service adds additional context from external sources to places
returned by the agent, including:
- Foursquare POI data (ratings, tips, photos)
- Instagram engagement metrics
- TikTok viral content
- TripAdvisor reviews
"""

from typing import Dict, List, Optional, Any
import asyncio
import httpx
from app.config import settings

import logging

logger = logging.getLogger(__name__)


class PlaceEnrichmentService:
    """Service for enriching place data with external sources."""
    
    def __init__(self):
        self.foursquare_api_key = getattr(settings, 'FOURSQUARE_API_KEY', None)
        self.apify_api_key = getattr(settings, 'APIFY_API_KEY', None)
    
    async def enrich_place(self, place: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a single place with additional data from external sources.
        
        Args:
            place: Place dictionary from agent
            
        Returns:
            Enriched place dictionary with additional fields
        """
        enriched = place.copy()
        
        # Add enrichment metadata
        enriched["enrichment"] = {
            "sources": [],
            "last_updated": None,
        }
        
        # Get coordinates
        location = place.get("location", {})
        lat = location.get("lat")
        lon = location.get("lon")
        name = place.get("name", "")
        
        # Try to enrich with Foursquare
        if self.foursquare_api_key and lat and lon:
            try:
                fsq_data = await self._get_foursquare_data(name, lat, lon)
                if fsq_data:
                    enriched["foursquare"] = fsq_data
                    enriched["enrichment"]["sources"].append("foursquare")
            except Exception as exc:
                logger.warning(f"Foursquare enrichment failed: {exc}")
        
        # Try to get social media metrics summary
        if name:
            try:
                social_data = await self._get_social_media_metrics(name, place.get("city", ""))
                if social_data:
                    enriched["social_media"] = social_data
                    enriched["enrichment"]["sources"].append("social_media")
            except Exception as exc:
                logger.warning(f"Social media enrichment failed: {exc}")
        
        return enriched
    
    async def enrich_places(self, places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich multiple places in parallel.
        
        Args:
            places: List of place dictionaries
            
        Returns:
            List of enriched place dictionaries
        """
        if not places:
            return []
        
        # Enrich in parallel (max 5 at a time to avoid rate limits)
        batch_size = 5
        enriched_places = []
        
        for i in range(0, len(places), batch_size):
            batch = places[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[self.enrich_place(place) for place in batch],
                return_exceptions=True
            )
            
            # Filter out exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Place enrichment failed: {result}")
                else:
                    enriched_places.append(result)
        
        return enriched_places
    
    async def _get_foursquare_data(
        self,
        name: str,
        lat: float,
        lon: float
    ) -> Optional[Dict[str, Any]]:
        """
        Get Foursquare data for a place.
        
        Args:
            name: Place name
            lat: Latitude
            lon: Longitude
            
        Returns:
            Foursquare data dict or None
        """
        if not self.foursquare_api_key:
            return None
        
        base_url = "https://api.foursquare.com/v3"
        headers = {
            "Authorization": self.foursquare_api_key,
            "Accept": "application/json",
        }
        
        params = {
            "query": name,
            "ll": f"{lat},{lon}",
            "radius": 500,  # 500m radius
            "limit": 1,
            "fields": "fsq_id,name,rating,popularity,price,hours,photos,tips",
        }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{base_url}/places/search",
                    headers=headers,
                    params=params,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    if results:
                        place_data = results[0]
                        
                        # Get tips if we have an ID
                        fsq_id = place_data.get("fsq_id")
                        if fsq_id:
                            tips = await self._get_foursquare_tips(fsq_id)
                            if tips:
                                place_data["tips"] = tips
                        
                        return place_data
                        
        except Exception as exc:
            logger.warning(f"Foursquare API error: {exc}")
        
        return None
    
    async def _get_foursquare_tips(self, fsq_id: str) -> List[str]:
        """Get tips for a Foursquare place."""
        if not self.foursquare_api_key:
            return []
        
        base_url = "https://api.foursquare.com/v3"
        headers = {
            "Authorization": self.foursquare_api_key,
            "Accept": "application/json",
        }
        
        params = {
            "limit": 5,
            "sort": "POPULAR",
        }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{base_url}/places/{fsq_id}/tips",
                    headers=headers,
                    params=params,
                )
                
                if response.status_code == 200:
                    tips_data = response.json()
                    return [tip.get("text", "") for tip in tips_data if tip.get("text")]
                        
        except Exception as exc:
            logger.warning(f"Foursquare tips error: {exc}")
        
        return []
    
    async def _get_social_media_metrics(
        self,
        place_name: str,
        city: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get simplified social media metrics without full scraping.
        
        In production, this could:
        - Query a cache of recent scraping results
        - Use lightweight APIs
        - Return pre-computed metrics
        
        For now, returns mock data to demonstrate the concept.
        """
        # TODO: Implement actual social media metrics retrieval
        # Options:
        # 1. Query cached Apify results from database
        # 2. Use Instagram/TikTok lightweight APIs
        # 3. Pre-compute and store metrics
        
        # For now, return None (no data)
        # In production, this would return:
        # {
        #     "instagram": {"posts": 120, "avg_likes": 450, "recent_hashtags": [...]},
        #     "tiktok": {"videos": 45, "avg_views": 12000, "trending": true},
        #     "tripadvisor": {"rating": 4.5, "reviews": 234}
        # }
        
        return None


# Singleton instance
place_enrichment_service = PlaceEnrichmentService()

