"""
Perplexity Search Service
Uses Perplexity API for real-time web enrichment of place data.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import httpx
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


class PerplexitySearchResult(BaseModel):
    """Result from Perplexity search."""
    content: str
    sources: List[str] = []
    timestamp: str


class PerplexitySearchService:
    """Service for searching and enriching place data using Perplexity AI."""
    
    def __init__(self):
        # Perplexity API key should be in settings
        # For now, we'll use web search as fallback
        self.api_key = getattr(settings, 'perplexity_api_key', None)
        self.base_url = "https://api.perplexity.ai"
        self.model = "llama-3.1-sonar-small-128k-online"  # Fast online model
        
    async def search_place_info(
        self,
        place_name: str,
        city: str,
        info_types: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Search for updated information about a place.
        
        Args:
            place_name: Name of the place
            city: City where the place is located
            info_types: Types of info to search for (reviews, social_media, hours, events, etc.)
            
        Returns:
            Dictionary with enriched information or None if unavailable
        """
        if not self.api_key:
            logger.warning("Perplexity API key not configured, using fallback search")
            return await self._fallback_search(place_name, city, info_types)
        
        if not info_types:
            info_types = ["reviews", "social_media", "popular_times"]
        
        try:
            # Build query
            query = self._build_query(place_name, city, info_types)
            
            # Search using Perplexity
            result = await self._perplexity_search(query)
            
            if result:
                # Parse and structure the result
                return self._parse_result(result, info_types)
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching place info: {e}")
            return None
    
    def _build_query(
        self,
        place_name: str,
        city: str,
        info_types: List[str]
    ) -> str:
        """Build an optimized query for Perplexity."""
        query_parts = [f"{place_name} {city}"]
        
        # Add specific info type requests
        if "reviews" in info_types:
            query_parts.append("recent reviews")
        if "social_media" in info_types:
            query_parts.append("Instagram handle")
        if "events" in info_types:
            query_parts.append("upcoming events")
        if "popular_times" in info_types:
            query_parts.append("busy hours")
        if "contact" in info_types:
            query_parts.append("contact information email")
        
        return " ".join(query_parts)
    
    async def _perplexity_search(self, query: str) -> Optional[str]:
        """Execute search using Perplexity API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides accurate, up-to-date information about places and businesses. Be concise and cite sources."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": 500,
            "temperature": 0.1,
            "top_p": 0.9,
            "return_citations": True,
            "search_recency_filter": "month",  # Recent data only
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract content
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                return content
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Perplexity API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error calling Perplexity: {e}")
            return None
    
    def _parse_result(
        self,
        content: str,
        info_types: List[str]
    ) -> Dict[str, Any]:
        """Parse Perplexity result into structured data."""
        result = {
            "raw_content": content,
            "extracted_info": {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        content_lower = content.lower()
        
        # Extract Instagram handle
        if "social_media" in info_types:
            # Look for @username pattern
            import re
            instagram_pattern = r'@([a-zA-Z0-9._]+)'
            matches = re.findall(instagram_pattern, content)
            if matches:
                result["extracted_info"]["instagram"] = f"@{matches[0]}"
        
        # Extract email
        if "contact" in info_types:
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            matches = re.findall(email_pattern, content)
            if matches:
                result["extracted_info"]["email"] = matches[0]
        
        # Extract sentiment from reviews
        if "reviews" in info_types:
            positive_words = ["excellent", "great", "amazing", "fantastic", "love", "best"]
            negative_words = ["bad", "terrible", "awful", "disappointing", "worst"]
            
            positive_count = sum(1 for word in positive_words if word in content_lower)
            negative_count = sum(1 for word in negative_words if word in content_lower)
            
            if positive_count > negative_count:
                result["extracted_info"]["review_sentiment"] = "positive"
            elif negative_count > positive_count:
                result["extracted_info"]["review_sentiment"] = "negative"
            else:
                result["extracted_info"]["review_sentiment"] = "neutral"
        
        return result
    
    async def _fallback_search(
        self,
        place_name: str,
        city: str,
        info_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Fallback search using DuckDuckGo when Perplexity is unavailable.
        
        This provides basic web enrichment without requiring API keys.
        """
        query = f"{place_name} {city}"
        
        if "reviews" in (info_types or []):
            query += " reviews"
        
        try:
            # Use DuckDuckGo instant answers
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                abstract = data.get("Abstract", "")
                related = data.get("RelatedTopics", [])
                
                if abstract or related:
                    return {
                        "raw_content": abstract,
                        "extracted_info": {
                            "source": "DuckDuckGo",
                            "related_topics": len(related)
                        },
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                
                return {
                    "raw_content": "No additional information found",
                    "extracted_info": {},
                    "timestamp": datetime.utcnow().isoformat(),
                }
                
        except Exception as e:
            logger.error(f"Fallback search error: {e}")
            return None
    
    async def get_instagram_handle(
        self,
        place_name: str,
        city: str
    ) -> Optional[str]:
        """
        Get Instagram handle for a place.
        
        Args:
            place_name: Name of the place
            city: City where the place is located
            
        Returns:
            Instagram handle (@username) or None
        """
        result = await self.search_place_info(
            place_name,
            city,
            info_types=["social_media"]
        )
        
        if result and "extracted_info" in result:
            return result["extracted_info"].get("instagram")
        
        return None


# Global instance
perplexity_service = PerplexitySearchService()
