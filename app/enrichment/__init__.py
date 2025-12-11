"""
Enrichment Module - TEMPORARY LOCATION
========================================

⚠️ WARNING: This module contains business logic that should eventually be moved to auphere-places (Rust).

This is a TEMPORARY organization to separate concerns while maintaining Python implementation.

Migration Plan:
1. Keep this module isolated from routers
2. Eventually rewrite in Rust and move to auphere-places
3. auphere-backend should only proxy, not enrich

Current responsibilities:
- Feature inference from place data
- Amenities mapping from Google Places
- Popular times integration
- Web enrichment (Perplexity)

TODO: Migrate to auphere-places/src/services/enrichment/
"""

from .feature_inference import (
    infer_features,
    enrich_place_with_features,
)
from .amenities_mapper import (
    extract_amenities_from_google,
    enrich_place_with_amenities,
)
from .google_places_popular_times import (
    GooglePlacesPopularTimesService,
    popular_times_service,
)
from .perplexity_search import (
    PerplexitySearchService,
    perplexity_service,
)

__all__ = [
    "infer_features",
    "enrich_place_with_features",
    "extract_amenities_from_google",
    "enrich_place_with_amenities",
    "GooglePlacesPopularTimesService",
    "popular_times_service",
    "PerplexitySearchService",
    "perplexity_service",
]
