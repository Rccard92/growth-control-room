"""Stub connector — implementazione reale in fase successiva."""

from connectors.base import BaseConnector, SyncResult
from connectors.types import IntegrationType


class GoogleAdsConnector(BaseConnector):
    integration_type = IntegrationType.GOOGLE_ADS

    async def validate_credentials(self, credentials: dict) -> bool:
        raise NotImplementedError("Google Ads OAuth non ancora implementato")

    async def sync(self, project_id: str) -> SyncResult:
        raise NotImplementedError("Google Ads sync non ancora implementato")
