"""
Feature Inference Utility
Infers features for places based on existing attributes.
"""
from typing import List, Dict, Any, Set


# Mapping rules: amenity -> feature label
AMENITY_TO_FEATURE = {
    "outdoor_seating": "Outdoor Seating",
    "wifi": "Free WiFi",
    "parking": "Parking Available",
    "wheelchair_accessible": "Wheelchair Accessible",
    "accepts_reservations": "Reservations",
    "live_music": "Live Music",
    "pet_friendly": "Pet Friendly",
    "family_friendly": "Family Friendly",
    "romantic_atmosphere": "Romantic Atmosphere",
    "good_for_groups": "Good for Groups",
    "takeout": "Takeout Available",
    "delivery": "Delivery",
    "vegan_options": "Vegan Options",
    "vegetarian_friendly": "Vegetarian Friendly",
    "full_bar": "Full Bar",
    "beer_wine": "Beer & Wine",
    "happy_hour": "Happy Hour",
    "late_night": "Late Night",
    "rooftop": "Rooftop",
    "waterfront": "Waterfront",
    "private_room": "Private Room Available",
    "dj": "DJ",
    "dance_floor": "Dance Floor",
    "karaoke": "Karaoke",
    "pool_table": "Pool Table",
    "tv_screens": "TV Screens",
    "sports_bar": "Sports Bar",
    "craft_cocktails": "Craft Cocktails",
    "wine_selection": "Wine Selection",
    "specialty_coffee": "Specialty Coffee",
    "brunch": "Brunch",
    "breakfast": "Breakfast",
    "lunch": "Lunch",
    "dinner": "Dinner",
}

# Category-based features
CATEGORY_FEATURES = {
    "restaurant": ["Table Service", "Menu Available"],
    "bar": ["Bar Seating", "Drinks Menu"],
    "cafe": ["Coffee & Pastries", "Quick Service"],
    "night_club": ["Nightlife", "Dance Floor"],
    "lounge": ["Lounge Seating", "Relaxed Atmosphere"],
}

# Vibe-based features
VIBE_FEATURES = {
    "romantic": ["Intimate Setting", "Great for Dates", "Romantic Ambiance"],
    "energetic": ["Lively Atmosphere", "High Energy", "Social Scene"],
    "sophisticated": ["Upscale", "Premium Experience", "Elegant Decor"],
    "casual": ["Relaxed Vibe", "No Dress Code", "Laid Back"],
    "chill": ["Quiet Atmosphere", "Comfortable Seating", "Peaceful"],
    "fun": ["Entertaining", "Social", "Good Vibes"],
}

# Price level features
PRICE_LEVEL_FEATURES = {
    1: ["Budget-Friendly", "Good Value", "Affordable"],
    2: ["Moderate Pricing", "Fair Prices"],
    3: ["Upscale", "Premium", "Fine Dining"],
    4: ["Luxury", "High-End", "Exclusive"],
}

# Rating-based features
RATING_FEATURES = {
    (4.5, 5.0): ["Highly Rated", "Excellent Reviews", "Top Rated"],
    (4.0, 4.5): ["Well Reviewed", "Popular Choice"],
    (3.5, 4.0): ["Good Reviews"],
}

# Opening hours features
HOURS_FEATURES = {
    "24_hours": "Open 24 Hours",
    "late_night": "Late Night",
    "early_morning": "Early Morning",
    "weekend_only": "Weekend Hours",
}


def infer_features_from_amenities(amenities: List[str]) -> Set[str]:
    """Infer features from amenities list."""
    features = set()
    
    if not amenities:
        return features
    
    # Normalize amenities to lowercase for matching
    amenities_lower = [a.lower() for a in amenities]
    
    for amenity_key, feature_label in AMENITY_TO_FEATURE.items():
        amenity_words = amenity_key.replace("_", " ")
        if any(amenity_words in a or a in amenity_words for a in amenities_lower):
            features.add(feature_label)
    
    return features


def infer_features_from_category(category: str) -> Set[str]:
    """Infer features from place category."""
    features = set()
    
    if not category:
        return features
    
    category_lower = category.lower()
    
    # Check direct matches
    for cat_key, cat_features in CATEGORY_FEATURES.items():
        if cat_key in category_lower:
            features.update(cat_features)
    
    return features


def infer_features_from_vibes(vibes: List[str]) -> Set[str]:
    """Infer features from place vibes/tags."""
    features = set()
    
    if not vibes:
        return features
    
    for vibe in vibes:
        vibe_lower = vibe.lower()
        for vibe_key, vibe_features in VIBE_FEATURES.items():
            if vibe_key in vibe_lower:
                features.update(vibe_features)
    
    return features


def infer_features_from_price_level(price_level: int) -> Set[str]:
    """Infer features from price level (1-4)."""
    features = set()
    
    if not price_level or price_level < 1 or price_level > 4:
        return features
    
    price_features = PRICE_LEVEL_FEATURES.get(price_level, [])
    features.update(price_features)
    
    return features


def infer_features_from_rating(rating: float, rating_count: int = 0) -> Set[str]:
    """Infer features from rating score."""
    features = set()
    
    if not rating:
        return features
    
    # Only add rating features if there are enough reviews
    if rating_count < 10:
        return features
    
    for (min_rating, max_rating), rating_features in RATING_FEATURES.items():
        if min_rating <= rating <= max_rating:
            features.update(rating_features)
            break
    
    return features


def infer_features_from_opening_hours(opening_hours: Dict[str, Any]) -> Set[str]:
    """Infer features from opening hours data."""
    features = set()
    
    if not opening_hours:
        return features
    
    # Check for 24 hours
    if opening_hours.get("open_24_hours"):
        features.add(HOURS_FEATURES["24_hours"])
    
    # Check for late night (open past midnight)
    periods = opening_hours.get("periods", [])
    for period in periods:
        close_time = period.get("close", {}).get("time")
        if close_time and int(close_time) >= 2400 or int(close_time) <= 400:
            features.add(HOURS_FEATURES["late_night"])
            break
    
    return features


def infer_features_from_photos(photos: List[Dict[str, Any]]) -> Set[str]:
    """Infer features from number and quality of photos."""
    features = set()
    
    if not photos:
        return features
    
    photo_count = len(photos)
    
    if photo_count >= 10:
        features.add("Well Documented")
    if photo_count >= 50:
        features.add("Popular Venue")
    
    return features


def infer_features(place_data: Dict[str, Any]) -> List[str]:
    """
    Main function to infer features from all available place data.
    
    Args:
        place_data: Dictionary containing place information
        
    Returns:
        List of inferred feature strings
    """
    all_features: Set[str] = set()
    
    # 1. From amenities/attributes
    amenities = place_data.get("amenities", [])
    all_features.update(infer_features_from_amenities(amenities))
    
    # 2. From category/type
    category = place_data.get("type") or place_data.get("category")
    if category:
        all_features.update(infer_features_from_category(category))
    
    # Also check main_categories
    main_categories = place_data.get("main_categories", [])
    for cat in main_categories:
        all_features.update(infer_features_from_category(cat))
    
    # 3. From vibes/tags
    vibes = place_data.get("tags", [])
    all_features.update(infer_features_from_vibes(vibes))
    
    # Also check vibe_descriptor
    vibe_descriptor = place_data.get("vibe_descriptor")
    if vibe_descriptor:
        all_features.update(infer_features_from_vibes([vibe_descriptor]))
    
    # 4. From price level (not currently in auphere-places, but could be added)
    price_level = place_data.get("price_level")
    if price_level:
        all_features.update(infer_features_from_price_level(price_level))
    
    # 5. From rating
    rating = place_data.get("google_rating")
    rating_count = place_data.get("google_rating_count", 0)
    if rating:
        all_features.update(infer_features_from_rating(rating, rating_count))
    
    # 6. From opening hours (not currently available, but could be enriched)
    opening_hours = place_data.get("opening_hours")
    if opening_hours:
        all_features.update(infer_features_from_opening_hours(opening_hours))
    
    # 7. From photos
    photos = place_data.get("photos", [])
    all_features.update(infer_features_from_photos(photos))
    
    # Convert set to sorted list for consistency
    return sorted(list(all_features))


def enrich_place_with_features(place_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich place data with inferred features.
    
    Args:
        place_data: Original place data dictionary
        
    Returns:
        Place data with 'features' field added/updated
    """
    # Check if features already exist
    existing_features = place_data.get("features", [])
    
    # Infer new features
    inferred_features = infer_features(place_data)
    
    # Merge existing and inferred (prioritize existing)
    all_features = list(set(existing_features + inferred_features))
    
    # Update place data
    place_data["features"] = all_features
    
    return place_data
