from app.core.config import settings


def is_pagespeed_configured() -> bool:
    return bool(settings.google_pagespeed_api_key and settings.google_pagespeed_api_key.strip())


def is_crux_configured() -> bool:
    return bool(settings.google_crux_api_key and settings.google_crux_api_key.strip())


def is_google_oauth_configured() -> bool:
    return settings.google_oauth_configured


def is_google_ads_developer_token_configured() -> bool:
    return bool(
        settings.google_ads_developer_token and settings.google_ads_developer_token.strip()
    )


def get_google_config_status() -> dict[str, dict[str, bool]]:
    return {
        "pagespeed": {"configured": is_pagespeed_configured()},
        "crux": {"configured": is_crux_configured()},
        "oauth": {"configured": is_google_oauth_configured()},
        "googleAdsDeveloperToken": {
            "configured": is_google_ads_developer_token_configured(),
        },
    }
