"""DataForSEO API constants and conservative cost estimates."""

DATAFORSEO_BASE_URL = "https://api.dataforseo.com/v3"

ENDPOINT_USER_DATA = "/appendix/user_data"
ENDPOINT_SEARCH_VOLUME_LIVE = "/keywords_data/google_ads/search_volume/live"
ENDPOINT_KEYWORDS_FOR_KEYWORDS_LIVE = "/keywords_data/google_ads/keywords_for_keywords/live"
ENDPOINT_SERP_ORGANIC_LIVE_ADVANCED = "/serp/google/organic/live/advanced"

RAW_PREVIEW_MAX_BYTES = 2048

TEST_COST_ESTIMATES: dict[str, float] = {
    "search_volume": 0.05,
    "keyword_ideas": 0.10,
    "serp": 0.10,
    "micro_bundle": 0.25,
}

UNIT_COST_ESTIMATES: dict[str, float] = {
    "search_volume": 0.05,
    "keyword_ideas": 0.10,
    "serp": 0.10,
}

ESTIMATE_MODE_PRESETS: dict[str, dict[str, int | None]] = {
    "single_page": {
        "product_pages_count": 1,
        "seed_queries_per_page": 3,
        "keyword_ideas_per_seed": 10,
        "serp_queries_per_page": 1,
    },
    "top_10_products": {
        "product_pages_count": 10,
        "seed_queries_per_page": 3,
        "keyword_ideas_per_seed": 10,
        "serp_queries_per_page": 2,
    },
    "full_site": {
        "product_pages_count": None,
        "seed_queries_per_page": 5,
        "keyword_ideas_per_seed": 20,
        "serp_queries_per_page": 3,
    },
}

DEFAULT_LOCATION_CODE = 2380
DEFAULT_LANGUAGE_CODE = "it"
