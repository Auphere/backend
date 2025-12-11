"""
Amenities Mapper Utility
Maps Google Places types and attributes to standardized amenities.
"""
from typing import List, Dict, Any, Set


# Mapping from Google Places types to amenities
GOOGLE_TYPE_TO_AMENITIES = {
    "restaurant": ["Dining", "Table Service"],
    "bar": ["Bar", "Drinks"],
    "cafe": ["Coffee", "Quick Service"],
    "night_club": ["Nightlife", "Dance Floor"],
    "park": ["Outdoor Space", "Green Space"],
    "gym": ["Fitness", "Exercise Equipment"],
    "spa": ["Wellness", "Relaxation"],
    "parking": ["Parking"],
    "lodging": ["Accommodation"],
    "movie_theater": ["Entertainment", "Cinema"],
    "bowling_alley": ["Entertainment", "Games"],
    "museum": ["Culture", "Educational"],
    "art_gallery": ["Art", "Culture"],
    "library": ["Quiet Space", "Books"],
    "store": ["Shopping"],
    "supermarket": ["Groceries", "Shopping"],
}

# Specific amenity keywords from Google Places attributes
GOOGLE_AMENITY_KEYWORDS = {
    # Accessibility
    "wheelchair": ["Wheelchair Accessible"],
    "accessible": ["Wheelchair Accessible"],
    
    # Dining options
    "takeout": ["Takeout Available"],
    "delivery": ["Delivery"],
    "reservations": ["Reservations"],
    "reservable": ["Reservations"],
    
    # Seating & atmosphere
    "outdoor": ["Outdoor Seating"],
    "seating": ["Seating Available"],
    "rooftop": ["Rooftop"],
    "terrace": ["Terrace"],
    "patio": ["Patio"],
    "garden": ["Garden"],
    
    # Payment & services
    "credit_card": ["Credit Cards Accepted"],
    "wifi": ["Free WiFi"],
    "internet": ["WiFi Available"],
    "parking": ["Parking Available"],
    "valet": ["Valet Parking"],
    "free_parking": ["Free Parking"],
    
    # Food & drink
    "vegetarian": ["Vegetarian Friendly"],
    "vegan": ["Vegan Options"],
    "gluten_free": ["Gluten-Free Options"],
    "halal": ["Halal Options"],
    "kosher": ["Kosher Options"],
    "organic": ["Organic Options"],
    "breakfast": ["Breakfast"],
    "brunch": ["Brunch"],
    "lunch": ["Lunch"],
    "dinner": ["Dinner"],
    "happy_hour": ["Happy Hour"],
    "late_night": ["Late Night"],
    "full_bar": ["Full Bar"],
    "wine": ["Wine Selection"],
    "beer": ["Beer Selection"],
    "cocktails": ["Cocktails"],
    "craft": ["Craft Drinks"],
    
    # Entertainment
    "live_music": ["Live Music"],
    "music": ["Music"],
    "dj": ["DJ"],
    "karaoke": ["Karaoke"],
    "pool": ["Pool Table"],
    "billiards": ["Pool Table"],
    "games": ["Games"],
    "sports": ["Sports Viewing"],
    "tv": ["TV Screens"],
    
    # Family & social
    "kid": ["Family Friendly"],
    "child": ["Family Friendly"],
    "family": ["Family Friendly"],
    "pet": ["Pet Friendly"],
    "dog": ["Pet Friendly"],
    "group": ["Good for Groups"],
    "private": ["Private Room Available"],
    
    # Ambiance
    "romantic": ["Romantic Atmosphere"],
    "intimate": ["Intimate Setting"],
    "cozy": ["Cozy Atmosphere"],
    "elegant": ["Elegant Decor"],
    "modern": ["Modern Design"],
    "vintage": ["Vintage Decor"],
}

# Service attributes that indicate amenities
SERVICE_ATTRIBUTES = {
    "dine_in": "Dine-in",
    "serves_breakfast": "Breakfast",
    "serves_brunch": "Brunch",
    "serves_lunch": "Lunch",
    "serves_dinner": "Dinner",
    "serves_beer": "Beer",
    "serves_wine": "Wine",
    "serves_vegetarian_food": "Vegetarian Friendly",
    "outdoor_seating": "Outdoor Seating",
    "live_music": "Live Music",
    "wheelchair_accessible_entrance": "Wheelchair Accessible",
    "wheelchair_accessible_parking": "Accessible Parking",
    "wheelchair_accessible_restroom": "Accessible Restroom",
    "wheelchair_accessible_seating": "Accessible Seating",
    "gender_neutral_restroom": "Gender Neutral Restroom",
    "restroom": "Restrooms Available",
    "wi_fi": "WiFi",
    "free_wi_fi": "Free WiFi",
}


def extract_amenities_from_types(types: List[str]) -> Set[str]:
    """
    Extract amenities from Google Places types.
    
    Args:
        types: List of Google Places types
        
    Returns:
        Set of amenity strings
    """
    amenities = set()
    
    if not types:
        return amenities
    
    for place_type in types:
        place_type_lower = place_type.lower().replace("_", " ")
        
        # Direct mapping
        for google_type, type_amenities in GOOGLE_TYPE_TO_AMENITIES.items():
            if google_type in place_type_lower:
                amenities.update(type_amenities)
    
    return amenities


def extract_amenities_from_attributes(attributes: Dict[str, Any]) -> Set[str]:
    """
    Extract amenities from place attributes/custom fields.
    
    Args:
        attributes: Dictionary of place attributes
        
    Returns:
        Set of amenity strings
    """
    amenities = set()
    
    if not attributes:
        return amenities
    
    # Check service attributes
    for attr_key, amenity_name in SERVICE_ATTRIBUTES.items():
        if attributes.get(attr_key) is True:
            amenities.add(amenity_name)
    
    # Check text fields for keywords
    text_fields = [
        attributes.get("description", ""),
        attributes.get("editorial_summary", ""),
        " ".join(attributes.get("types", [])),
    ]
    
    combined_text = " ".join(str(field) for field in text_fields if field).lower()
    
    for keyword, keyword_amenities in GOOGLE_AMENITY_KEYWORDS.items():
        if keyword in combined_text:
            amenities.update(keyword_amenities)
    
    return amenities


def extract_amenities_from_reviews(reviews: List[Dict[str, Any]]) -> Set[str]:
    """
    Extract amenities mentioned in reviews.
    
    Args:
        reviews: List of review dictionaries
        
    Returns:
        Set of amenity strings
    """
    amenities = set()
    
    if not reviews:
        return amenities
    
    # Combine all review text
    review_text = " ".join(
        review.get("text", "").lower() 
        for review in reviews[:10]  # Limit to first 10 reviews
    ).lower()
    
    # Look for amenity keywords in reviews
    for keyword, keyword_amenities in GOOGLE_AMENITY_KEYWORDS.items():
        if keyword in review_text:
            amenities.update(keyword_amenities)
    
    return amenities


def extract_amenities_from_google(place_data: Dict[str, Any]) -> List[str]:
    """
    Main function to extract all amenities from Google Places data.
    
    Args:
        place_data: Dictionary containing place information from Google Places
        
    Returns:
        List of unique amenity strings
    """
    all_amenities: Set[str] = set()
    
    # 1. From types
    types = place_data.get("types", [])
    if not types:
        # Also check main_categories (auphere-places format)
        types = place_data.get("main_categories", [])
    all_amenities.update(extract_amenities_from_types(types))
    
    # 2. From attributes
    # Check both root level and custom_attributes
    attributes = place_data.get("custom_attributes", {})
    if not attributes:
        attributes = place_data
    all_amenities.update(extract_amenities_from_attributes(attributes))
    
    # 3. From reviews
    reviews = place_data.get("reviews", [])
    all_amenities.update(extract_amenities_from_reviews(reviews))
    
    # 4. From existing amenities field (merge don't replace)
    existing_amenities = place_data.get("amenities", [])
    if existing_amenities:
        all_amenities.update(existing_amenities)
    
    # Convert to sorted list for consistency
    return sorted(list(all_amenities))


def enrich_place_with_amenities(place_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich place data with extracted amenities.
    
    Args:
        place_data: Original place data dictionary
        
    Returns:
        Place data with 'amenities' field added/updated
    """
    # Extract amenities
    amenities = extract_amenities_from_google(place_data)
    
    # Update place data
    place_data["amenities"] = amenities
    
    return place_data
