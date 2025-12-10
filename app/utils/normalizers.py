"""
Data normalizers to ensure consistent data structure across the application.
These normalizers ensure that Place and Plan data is always in the same format
regardless of the source (agent, Google Places, internal DB).
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

IMAGE_PLACEHOLDER = "https://images.unsplash.com/photo-1504674900247-0877df9cc836"


def normalize_place(raw_place: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize place data to a consistent frontend-friendly format.
    
    Frontend PlaceCard and ChatPlaceCard expect:
    - id (string)
    - place_id (string, optional)
    - name (string)
    - category (string): restaurant, bar, club, cafe, activity, lounge
    - description (string, optional)
    - vibe (list of strings, optional): romantic, casual, energetic, chill, sophisticated, fun
    - crowdLevel (string, optional): empty, quiet, moderate, busy, packed
    - musicType (string, optional): live, dj, ambient, none, jazz, electronic, latin, pop
    - priceLevel (number): 1-4
    - rating (number, optional)
    - reviewCount (number, optional)
    - address (string, optional)
    - neighborhood (string, optional)
    - distance (number, optional)
    - openNow (boolean, optional)
    - images (list of strings)
    - location (object with lat, lon, optional)
    - currentStatus (string, optional)
    """
    if not raw_place or not raw_place.get("name"):
        return None
    
    # Extract ID - prioritize DB ID over Google Place ID
    # The agent now saves places to DB and returns db_id
    place_id = (
        raw_place.get("db_id") or  # DB ID from agent
        raw_place.get("id") or  # Could be DB ID or Google ID
        raw_place.get("place_id") or  # Google Place ID
        raw_place.get("_id")
    )
    
    # Keep Google Place ID separate for reference
    google_place_id = (
        raw_place.get("place_id") or
        raw_place.get("google_place_id") or
        (raw_place.get("id") if not raw_place.get("db_id") else None)
    )
    
    # Extract category - prioritize single category over array
    category = raw_place.get("category")
    if not category:
        types = raw_place.get("types", [])
        if types:
            category = _map_type_to_category(types[0] if isinstance(types, list) else types)
        else:
            category = "place"
    
    # Extract rating
    rating = (
        raw_place.get("rating") or 
        raw_place.get("google_rating") or 
        raw_place.get("googleRating") or 
        0
    )
    
    # Extract review count
    review_count = (
        raw_place.get("reviewCount") or
        raw_place.get("user_ratings_total") or
        raw_place.get("google_rating_count") or
        raw_place.get("googleReviewCount") or
        0
    )
    
    # Extract address
    address = (
        raw_place.get("address") or
        raw_place.get("formatted_address") or
        raw_place.get("vicinity") or
        ""
    )
    
    # Extract neighborhood
    neighborhood = (
        raw_place.get("neighborhood") or
        raw_place.get("neighbourhood") or
        _extract_neighborhood_from_address(address) or
        None
    )
    
    # Extract price level (1-4)
    price_level = raw_place.get("priceLevel") or raw_place.get("price_level") or 2
    if not isinstance(price_level, int) or price_level < 1:
        price_level = 2
    elif price_level > 4:
        price_level = 4
    
    # Extract open now
    open_now = raw_place.get("openNow")
    if open_now is None:
        open_now = raw_place.get("open_now")
    if open_now is None:
        opening_hours = raw_place.get("opening_hours", {})
        if isinstance(opening_hours, dict):
            open_now = opening_hours.get("open_now", True)
        else:
            open_now = True
    
    # Extract images - convert photo references to URLs if needed
    images = []
    if raw_place.get("images"):
        images = raw_place["images"] if isinstance(raw_place["images"], list) else [raw_place["images"]]
        # Filter out photo_reference strings (they need conversion)
        images = [img for img in images if not (isinstance(img, str) and len(img) > 50 and not img.startswith("http"))]
    elif raw_place.get("photo_url"):
        images = [raw_place["photo_url"]]
    elif raw_place.get("primary_photo_url"):
        images = [raw_place["primary_photo_url"]]
    elif raw_place.get("primary_photo_thumbnail_url"):
        images = [raw_place["primary_photo_thumbnail_url"]]
    elif raw_place.get("photos"):
        # Google Places format
        photos = raw_place["photos"]
        if isinstance(photos, list) and photos:
            # Extract photo URLs, skip photo_references (they need API conversion)
            for p in photos[:3]:
                if isinstance(p, str):
                    if p.startswith("http"):
                        images.append(p)
                elif isinstance(p, dict):
                    url = p.get("url") or p.get("photo_url")
                    if url and url.startswith("http"):
                        images.append(url)
                    # Skip photo_reference - would need Google Places API to convert
    
    # Extract location
    location = raw_place.get("location")
    if not location:
        geometry = raw_place.get("geometry", {})
        if isinstance(geometry, dict) and "location" in geometry:
            location = geometry["location"]
    
    # Normalize location format
    if location:
        if "lng" in location and "lon" not in location:
            location["lon"] = location["lng"]
        elif "lon" in location and "lng" not in location:
            location["lng"] = location["lon"]
    
    # Extract vibe
    vibe = raw_place.get("vibe") or raw_place.get("vibe_descriptor") or []
    if not isinstance(vibe, list):
        vibe = [vibe] if vibe else []
    
    # Extract crowd level
    crowd_level = raw_place.get("crowdLevel") or raw_place.get("crowd_level") or "moderate"
    
    # Extract music type
    music_type = raw_place.get("musicType") or raw_place.get("music_type") or "ambient"
    
    # Extract description
    description = (
        raw_place.get("description") or
        raw_place.get("editorial_summary", {}).get("overview") if isinstance(raw_place.get("editorial_summary"), dict) else None or
        raw_place.get("summary") or
        ""
    )
    
    # Extract current status
    current_status = raw_place.get("currentStatus") or raw_place.get("current_status")
    
    # Build normalized place
    normalized = {
        "id": str(place_id) if place_id else None,
        "place_id": str(google_place_id) if google_place_id else str(place_id) if place_id else None,
        "name": raw_place["name"],
        "category": category,
        "description": description,
        "vibe": vibe,
        "crowdLevel": crowd_level,
        "musicType": music_type,
        "priceLevel": price_level,
        "rating": float(rating) if rating else 0,
        "reviewCount": int(review_count) if review_count else 0,
        "address": address,
        "neighborhood": neighborhood,
        "distance": raw_place.get("distance"),
        "openNow": bool(open_now),
        "images": images if images else [IMAGE_PLACEHOLDER],
        "location": location,
    }
    
    # Add optional fields that PlaceDetail needs
    if current_status:
        normalized["currentStatus"] = current_status
    if raw_place.get("phone"):
        normalized["phone"] = raw_place["phone"]
    if raw_place.get("website"):
        normalized["website"] = raw_place["website"]
    if raw_place.get("email"):
        normalized["email"] = raw_place["email"]
    if raw_place.get("opening_hours"):
        normalized["openingHours"] = raw_place["opening_hours"]
    if raw_place.get("weekly_hours"):
        normalized["weeklyHours"] = raw_place["weekly_hours"]
    if raw_place.get("amenities"):
        normalized["amenities"] = raw_place["amenities"]
    if raw_place.get("features"):
        normalized["features"] = raw_place["features"]
    if raw_place.get("reviews"):
        normalized["reviews"] = raw_place["reviews"]
    if raw_place.get("socialMedia"):
        normalized["socialMedia"] = raw_place["socialMedia"]
    
    return {k: v for k, v in normalized.items() if v is not None}


def normalize_places(raw_places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize a list of places."""
    if not raw_places:
        return []
    
    normalized = []
    for place in raw_places:
        norm = normalize_place(place)
        if norm:
            normalized.append(norm)
    
    return normalized


def _parse_duration_string(duration_str: str) -> int:
    """Convert duration strings like '6h 00m' to minutes."""
    try:
        duration_str = duration_str.lower()
        hours = 0
        minutes = 0
        if "h" in duration_str:
            parts = duration_str.split("h")
            hours = int(parts[0].strip())
            rest = parts[1]
            if "m" in rest:
                minutes = int(rest.split("m")[0].strip() or 0)
        elif "m" in duration_str:
            minutes = int(duration_str.replace("m", "").strip())
        return hours * 60 + minutes
    except Exception:
        return 0


def _normalize_new_plan_format(raw_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize the structured plan produced by generate_plan_json_tool.
    This keeps rich fields (stopsDetailed, summary, execution, vibes, tags).
    """
    plan_id = raw_plan.get("planId") or raw_plan.get("id") or raw_plan.get("_id")

    # Map top-level fields
    name = raw_plan.get("title") or raw_plan.get("name") or "Untitled Plan"
    description = raw_plan.get("description", "")
    category = raw_plan.get("category")
    vibes = raw_plan.get("vibes", [])
    tags = raw_plan.get("tags", [])
    execution = raw_plan.get("execution")
    summary = raw_plan.get("summary")
    final_recommendations = raw_plan.get("finalRecommendations", [])

    # Stops detailed - normalize each stop's structure
    raw_stops = raw_plan.get("stops", [])
    stops_detailed = []
    for stop in raw_stops:
        # Normalize vibes within stop details
        if stop.get("details") and stop["details"].get("vibes"):
            vibes_field = stop["details"]["vibes"]
            if not isinstance(vibes_field, list):
                stop["details"]["vibes"] = [vibes_field] if vibes_field else []
        stops_detailed.append(stop)

    # Derive lightweight stops array for backward compatibility
    stops_simple = []
    for stop in stops_detailed:
        timing = stop.get("timing", {})
        stops_simple.append(
            {
                "place": {  # minimal placeholder; UI mainly uses stopsDetailed
                    "id": stop.get("localId") or stop.get("name"),
                    "name": stop.get("name"),
                    "address": stop.get("location", {}).get("address"),
                },
                "duration": int(timing.get("suggestedDurationMinutes", 60)),
                "startTime": timing.get("recommendedStart") or "19:00",
                "activity": stop.get("typeLabel") or stop.get("category") or "Visit",
            }
        )

    # Compute numeric totals if available
    total_duration_minutes = 0
    if summary and summary.get("totalDuration"):
        total_duration_minutes = _parse_duration_string(summary["totalDuration"])
    total_distance_km = None
    if summary and summary.get("totalDistanceKm") is not None:
        total_distance_km = float(summary["totalDistanceKm"])

    normalized = {
        "id": str(plan_id) if plan_id else None,
        "name": name,
        "description": description,
        "category": category,
        "vibes": vibes if isinstance(vibes, list) else [vibes] if vibes else [],
        "tags": tags,
        "execution": execution,
        "stops": stops_simple,
        "stopsDetailed": stops_detailed,
        "summary": summary,
        "finalRecommendations": final_recommendations,
        # Legacy numeric fields for components that still rely on them
        "totalDuration": total_duration_minutes,
        "totalDistance": total_distance_km,
    }

    return {k: v for k, v in normalized.items() if v is not None}


def _normalize_legacy_plan_format(raw_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize the legacy plan format (name/description/vibe + stops with place).
    """
    plan_id = raw_plan.get("id") or raw_plan.get("_id")
    stops = raw_plan.get("stops", [])

    normalized_stops = []
    for stop in stops:
        if not stop:
            continue

        place_data = stop.get("place", {})
        normalized_place = normalize_place(place_data) if place_data else None

        if not normalized_place:
            continue

        normalized_stop = {
            "place": normalized_place,
            "duration": int(stop.get("duration", 60)),
            "startTime": stop.get("startTime") or stop.get("start_time") or "19:00",
            "activity": stop.get("activity", "Visit"),
        }
        normalized_stops.append(normalized_stop)

    vibe = raw_plan.get("vibe", "casual")
    if isinstance(vibe, list):
        vibe = vibe[0] if vibe else "casual"

    normalized = {
        "id": str(plan_id) if plan_id else None,
        "name": raw_plan.get("name", "Unnamed Plan"),
        "description": raw_plan.get("description", ""),
        "vibe": vibe,
        "totalDuration": int(raw_plan.get("totalDuration") or raw_plan.get("total_duration", 0)),
        "totalDistance": float(raw_plan.get("totalDistance") or raw_plan.get("total_distance", 0)),
        "stops": normalized_stops,
    }

    return {k: v for k, v in normalized.items() if v is not None}


def normalize_plan(raw_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize plan data to a consistent frontend-friendly format.

    Supports both the new structured plan JSON (generate_plan_json_tool) and the
    legacy simple plan format.
    """
    if not raw_plan:
        return None

    # New format detection: presence of planId and rich stop fields
    if raw_plan.get("planId") or (raw_plan.get("stops") and raw_plan.get("summary")):
        try:
            return _normalize_new_plan_format(raw_plan)
        except Exception:
            # Fallback to legacy if anything goes wrong
            return _normalize_legacy_plan_format(raw_plan)

    # Legacy format fallback
    return _normalize_legacy_plan_format(raw_plan)


def _map_type_to_category(place_type: str) -> str:
    """Map Google Places types to frontend categories."""
    type_lower = place_type.lower()
    
    if any(t in type_lower for t in ["restaurant", "food", "meal", "dining"]):
        return "restaurant"
    elif any(t in type_lower for t in ["bar", "pub", "tavern"]):
        return "bar"
    elif any(t in type_lower for t in ["night_club", "club", "disco"]):
        return "club"
    elif any(t in type_lower for t in ["cafe", "coffee"]):
        return "cafe"
    elif any(t in type_lower for t in ["lounge", "cocktail"]):
        return "lounge"
    else:
        return "activity"


def _extract_neighborhood_from_address(address: str) -> Optional[str]:
    """Try to extract neighborhood from address string."""
    if not address:
        return None
    
    # Simple heuristic: take the first part before comma
    parts = address.split(",")
    if len(parts) >= 2:
        return parts[0].strip()
    
    return None

