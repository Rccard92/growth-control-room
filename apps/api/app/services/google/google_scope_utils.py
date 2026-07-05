"""Google OAuth scope mapping and provider resolution."""

from __future__ import annotations

GOOGLE_PROVIDER_SCOPES: dict[str, list[str]] = {
    "google_search_console": ["https://www.googleapis.com/auth/webmasters.readonly"],
    "ga4": ["https://www.googleapis.com/auth/analytics.readonly"],
    "google_ads": ["https://www.googleapis.com/auth/adwords"],
    "merchant_center": ["https://www.googleapis.com/auth/content"],
}

CONTENT_SCOPE = "https://www.googleapis.com/auth/content"

GOOGLE_OAUTH_SCOPES = [
    scope
    for provider_scopes in GOOGLE_PROVIDER_SCOPES.values()
    for scope in provider_scopes
]

# Frontend / legacy service aliases → backend provider keys
GOOGLE_SERVICE_ALIAS_TO_PROVIDER: dict[str, str] = {
    "search_console": "google_search_console",
    "google_search_console": "google_search_console",
    "analytics": "ga4",
    "ga4": "ga4",
    "google_ads": "google_ads",
    "merchant_center": "merchant_center",
    "all": "all",
}

VALID_OAUTH_MODES = frozenset({"connect", "reconnect", "add_scope"})
VALID_OAUTH_PROVIDERS = frozenset(
    {"google_search_console", "ga4", "google_ads", "merchant_center", "all"}
)

SIBLING_OAUTH_PROVIDERS = ("google_search_console", "ga4", "google_ads")


def normalize_oauth_provider(provider: str | None) -> str:
    if not provider:
        return "all"
    normalized = GOOGLE_SERVICE_ALIAS_TO_PROVIDER.get(provider.strip().lower(), provider.strip())
    if normalized not in VALID_OAUTH_PROVIDERS:
        return "all"
    return normalized


def normalize_oauth_mode(mode: str | None) -> str:
    if not mode:
        return "connect"
    normalized = mode.strip().lower()
    if normalized not in VALID_OAUTH_MODES:
        return "connect"
    return normalized


def parse_scope_string(scope: str | None) -> set[str]:
    if not scope or not isinstance(scope, str):
        return set()
    return {part.strip() for part in scope.split() if part.strip()}


def get_google_scopes_for_provider(provider: str) -> list[str]:
    normalized = normalize_oauth_provider(provider)
    if normalized == "all":
        return list(GOOGLE_OAUTH_SCOPES)
    return list(GOOGLE_PROVIDER_SCOPES.get(normalized, []))


def get_google_scopes_for_reconnect(provider: str | None) -> list[str]:
    """Return scopes to request during OAuth (incremental auth via include_granted_scopes)."""
    normalized = normalize_oauth_provider(provider)
    # Always request full supported scope set; Google incremental auth grants only new ones.
    return list(GOOGLE_OAUTH_SCOPES)


def providers_covered_by_scopes(scopes: set[str]) -> set[str]:
    covered: set[str] = set()
    for provider, required_scopes in GOOGLE_PROVIDER_SCOPES.items():
        if all(scope in scopes for scope in required_scopes):
            covered.add(provider)
    return covered


def resolve_oauth_prompt(mode: str) -> str:
    if mode in {"reconnect", "add_scope"}:
        return "consent"
    return "consent"


def resolve_persist_targets(
    token_scopes: set[str],
    *,
    requested_provider: str | None,
    mode: str,
) -> set[str]:
    normalized_provider = normalize_oauth_provider(requested_provider)
    normalized_mode = normalize_oauth_mode(mode)

    if token_scopes:
        targets = providers_covered_by_scopes(token_scopes)
    elif normalized_provider != "all":
        # Safe fallback for add_scope when Google omits scope in token response.
        targets = {normalized_provider}
    elif normalized_mode == "connect":
        targets = set(GOOGLE_PROVIDER_SCOPES.keys())
    else:
        targets = set()

    if normalized_provider != "all":
        if token_scopes:
            provider_scopes = set(GOOGLE_PROVIDER_SCOPES.get(normalized_provider, []))
            if provider_scopes & token_scopes:
                targets = {normalized_provider}
            else:
                targets = set()
        else:
            targets = {normalized_provider}

    return targets
