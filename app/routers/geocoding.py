"""
Geocoding and Places Autocomplete Proxy Router
Proxies Google Maps API calls to hide API key from frontend
"""
import logging
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.config import settings

router = APIRouter(prefix="/geocoding", tags=["geocoding"])
logger = logging.getLogger(__name__)


@router.get("/autocomplete")
async def autocomplete_places(
    input: str = Query(..., description="Search query"),
    types: str = Query("(cities)", description="Place types to search"),
    components: str = Query("country:es", description="Component restrictions"),
):
    """
    Proxy for Google Places Autocomplete API.
    
    This endpoint hides the API key from the frontend and adds caching.
    
    Args:
        input: Search query string
        types: Place types filter (default: cities)
        components: Component restrictions (default: Spain only)
        
    Returns:
        Autocomplete predictions from Google Places API
    """
    if not settings.google_places_api_key:
        raise HTTPException(status_code=503, detail="Google Places API not configured")
    
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "input": input,
        "types": types,
        "components": components,
        "key": settings.google_places_api_key,
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                logger.warning(f"Google Autocomplete API status: {data.get('status')}")
                return {"predictions": [], "status": data.get("status")}
            
            return data
            
    except httpx.HTTPError as e:
        logger.error(f"Google Autocomplete API error: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch autocomplete results")


@router.get("/place-details/{place_id}")
async def get_place_details(
    place_id: str,
    fields: str = Query(
        "name,geometry,formatted_address,photos",
        description="Fields to retrieve"
    ),
):
    """
    Proxy for Google Places Details API.
    
    Args:
        place_id: Google Place ID
        fields: Comma-separated list of fields to retrieve
        
    Returns:
        Place details from Google Places API
    """
    if not settings.google_places_api_key:
        raise HTTPException(status_code=503, detail="Google Places API not configured")
    
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": fields,
        "key": settings.google_places_api_key,
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                logger.warning(f"Google Place Details API status: {data.get('status')}")
                raise HTTPException(status_code=404, detail="Place not found")
            
            return data
            
    except httpx.HTTPError as e:
        logger.error(f"Google Place Details API error: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch place details")


@router.get("/reverse-geocode")
async def reverse_geocode(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
):
    """
    Proxy for Google Geocoding API (reverse geocoding).
    
    Converts coordinates to address/city name.
    
    Args:
        lat: Latitude
        lng: Longitude
        
    Returns:
        Geocoding results from Google Geocoding API
    """
    if not settings.google_places_api_key:
        raise HTTPException(status_code=503, detail="Google Places API not configured")
    
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lng}",
        "key": settings.google_places_api_key,
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                logger.warning(f"Google Geocoding API status: {data.get('status')}")
                return {"results": [], "status": data.get("status")}
            
            return data
            
    except httpx.HTTPError as e:
        logger.error(f"Google Geocoding API error: {e}")
        raise HTTPException(status_code=502, detail="Failed to reverse geocode")


@router.get("/photo-proxy")
async def photo_proxy(
    photo_reference: str = Query(..., description="Google photo reference"),
    maxwidth: int = Query(800, description="Maximum width in pixels"),
):
    """
    Proxy for Google Places Photo API.
    
    This endpoint fetches photos from Google and returns them,
    hiding the API key from the frontend.
    
    Args:
        photo_reference: Photo reference from Google Places
        maxwidth: Maximum width in pixels
        
    Returns:
        Photo binary data
    """
    if not settings.google_places_api_key:
        raise HTTPException(status_code=503, detail="Google Places API not configured")
    
    url = "https://maps.googleapis.com/maps/api/place/photo"
    params = {
        "photoreference": photo_reference,
        "maxwidth": maxwidth,
        "key": settings.google_places_api_key,
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            # Return the image with proper content type
            from fastapi.responses import Response
            return Response(
                content=response.content,
                media_type=response.headers.get("content-type", "image/jpeg"),
                headers={
                    "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                }
            )
            
    except httpx.HTTPError as e:
        logger.error(f"Google Photo API error: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch photo")
