"""Places API router consuming the internal Auphere Places service."""
import logging
import math
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.models.places import PlaceResponse, PlaceSearchRequest, PlaceSearchResponse
from app.services.google_places import places_service

# ⚠️ TEMPORARY: Enrichment should be in auphere-places, not here
# TODO: Remove these imports once enrichment is moved to Rust
from app.enrichment import (
    enrich_place_with_features,
    enrich_place_with_amenities,
    popular_times_service,
    perplexity_service,
)

router = APIRouter(prefix="/places", tags=["places"])


@router.post("/search", response_model=PlaceSearchResponse)
async def search_places(request: PlaceSearchRequest):
    """
    Proxy place searches to the internal `auphere-places` microservice.
    
    The Rust service aplica FTS, filtros geoespaciales y ranking. Este endpoint
    solamente traduce el request del frontend y homologa la respuesta a nuestro contrato.
    """
    params = _build_search_params(request)

    try:
        raw_response = await places_service.search_places(params)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Places service error: {exc.response.text}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach places service: {exc}",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc

    raw_places = raw_response.get("data", [])
    mapped_places = [
        _map_place_record(place, request.latitude, request.longitude)
        for place in raw_places
    ]

    total = int(raw_response.get("total_count", len(mapped_places)))
    limit = int(raw_response.get("limit") or request.per_page)
    page = int(raw_response.get("page") or request.page)
    total_pages = max(1, math.ceil(total / limit)) if limit else 1

    return PlaceSearchResponse(
        places=mapped_places,
        total=total,
        page=page,
        per_page=limit,
        total_pages=total_pages,
    )


@router.get("/{place_id}", response_model=PlaceResponse)
async def get_place_details(place_id: str):
    """
    Retrieve a place (with photos & reviews) from the internal service.
    
    `place_id` corresponde al UUID generado en `auphere-places`.
    
    ⚠️ ARCHITECTURAL NOTE:
    This endpoint currently includes enrichment logic that should be in auphere-places.
    The enrichment calls below are TEMPORARY and will be removed once moved to Rust.
    
    Target architecture:
    - Backend: Pure proxy (no enrichment)
    - auphere-places: Handles ALL place data including enrichment
    """
    try:
        place_data = await places_service.get_place_details(place_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Place not found") from exc
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Places service error: {exc.response.text}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach places service: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to get place details: {exc}"
        ) from exc

    # ⚠️ TEMPORARY: Enrichment logic (should be in auphere-places)
    # TODO: Remove these calls once enrichment is moved to Rust
    
    # ✨ ENRICH: Extract and expand amenities
    place_data = enrich_place_with_amenities(place_data)
    
    # ✨ ENRICH: Infer features from existing data
    place_data = enrich_place_with_features(place_data)
    
    # ✨ ENRICH: Get popular times from Google Places
    google_place_id = place_data.get("google_place_id")
    popular_times = None
    if google_place_id:
        try:
            popular_times = await popular_times_service.get_popular_times(google_place_id)
        except Exception as e:
            # Don't fail the request if popular times fetch fails
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to fetch popular times: {e}")
    
    place_response = _map_place_record(place_data)

    # Attach photos and reviews for consumers that expect them
    photos = place_data.get("photos")
    reviews = place_data.get("reviews")
    if photos:
        place_response.custom_attributes["photos"] = photos
    if reviews:
        place_response.custom_attributes["reviews"] = reviews
    
    # Attach enriched features
    features = place_data.get("features", [])
    if features:
        place_response.custom_attributes["features"] = features
    
    # Attach enriched amenities
    amenities = place_data.get("amenities", [])
    if amenities:
        place_response.custom_attributes["amenities"] = amenities
    
    # Attach popular times
    if popular_times:
        place_response.custom_attributes["popular_times"] = popular_times

    return place_response


@router.get("/{place_id}/enrich")
async def enrich_place_from_web(
    place_id: str,
    info_types: List[str] = Query(
        default=["reviews", "social_media"],
        description="Types of info to enrich: reviews, social_media, events, contact"
    )
):
    """
    Enrich a place with real-time web data using Perplexity AI.
    
    ⚠️ ARCHITECTURAL NOTE:
    This endpoint should either be:
    A) In auphere-places (if it's data enrichment)
    B) In auphere-agent (if it's AI context gathering)
    
    Currently in backend as temporary location.
    
    This endpoint fetches up-to-date information from the web including:
    - Recent reviews and sentiment
    - Social media handles (Instagram, Facebook)
    - Current events or specials
    - Contact information
    
    Args:
        place_id: The place UUID
        info_types: List of information types to fetch
        
    Returns:
        Enriched information from the web
    """
    try:
        # First get the place details
        place_data = await places_service.get_place_details(place_id)
        
        place_name = place_data.get("name")
        city = place_data.get("city", settings.places_service_default_city)
        
        if not place_name:
            raise HTTPException(status_code=400, detail="Place name not found")
        
        # Enrich with web data
        web_info = await perplexity_service.search_place_info(
            place_name=place_name,
            city=city,
            info_types=info_types
        )
        
        if not web_info:
            return {
                "place_id": place_id,
                "place_name": place_name,
                "enriched": False,
                "message": "No additional web information found"
            }
        
        return {
            "place_id": place_id,
            "place_name": place_name,
            "enriched": True,
            "web_info": web_info,
            "requested_types": info_types
        }
        
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Place not found")
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Places service error: {exc.response.text}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enrich place: {exc}"
        )


def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers using Haversine formula."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return round(R * c, 2)


def _build_search_params(request: PlaceSearchRequest) -> Dict[str, Any]:
    """Translate PlaceSearchRequest into query params for the places service."""
    params: Dict[str, Any] = {
        "page": request.page,
        "limit": request.per_page,
    }

    city = request.city or settings.places_service_default_city
    if city:
        params["city"] = city

    if request.query:
        params["q"] = request.query

    if request.latitude is not None:
        params["lat"] = request.latitude
    if request.longitude is not None:
        params["lon"] = request.longitude

    if request.radius:
        params["radius_km"] = max(request.radius / 1000.0, 0.1)

    if request.categories:
        params["type"] = request.categories[0].value

    if request.vibes:
        params["tags"] = request.vibes

    if request.min_rating is not None:
        params["min_rating"] = request.min_rating

    return params


def _map_place_record(
    place_data: Dict[str, Any],
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
) -> PlaceResponse:
    """Normalize the places microservice payload into the public response."""
    location = place_data.get("location") or []
    longitude = location[0] if len(location) > 0 else None
    latitude = location[1] if len(location) > 1 else None

    distance_km = None
    if (
        user_lat is not None
        and user_lon is not None
        and latitude is not None
        and longitude is not None
    ):
        distance_km = _calculate_distance(user_lat, user_lon, latitude, longitude)

    types: List[str] = []
    primary_type = place_data.get("type")
    if primary_type:
        types.append(primary_type)
    for category in place_data.get("main_categories") or []:
        if category not in types:
            types.append(category)

    custom_attributes = {
        "city": place_data.get("city"),
        "district": place_data.get("district"),
        "main_categories": place_data.get("main_categories"),
        "tags": place_data.get("tags"),
        "vibe_descriptor": place_data.get("vibe_descriptor"),
        "primary_photo_url": place_data.get("primary_photo_url"),
        "primary_photo_thumbnail_url": place_data.get("primary_photo_thumbnail_url"),
        "google_place_id": place_data.get("google_place_id"),
    }
    # Remove null values but keep empty dicts/lists if explicitly provided
    custom_attributes = {
        key: value
        for key, value in custom_attributes.items()
        if value is not None
    }

    place_identifier = place_data.get("id") or place_data.get("google_place_id")
    if not place_identifier:
        raise ValueError("Place payload missing identifier fields")

    formatted_address = place_data.get("description") or place_data.get("city")

    return PlaceResponse(
        place_id=str(place_identifier),
        name=place_data.get("name", "Unknown Place"),
        formatted_address=formatted_address,
        vicinity=place_data.get("district"),
        latitude=latitude,
        longitude=longitude,
        types=types,
        rating=place_data.get("google_rating"),
        user_ratings_total=place_data.get("google_rating_count"),
        price_level=None,
        phone_number=place_data.get("phone"),
        website=place_data.get("website"),
        opening_hours=None,
        custom_attributes=custom_attributes,
        distance_km=distance_km,
    )

