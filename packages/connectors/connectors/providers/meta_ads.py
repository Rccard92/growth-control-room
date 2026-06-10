"""Stub connector — implementazione reale in fase successiva."""

from connectors.base import BaseConnector, SyncResult
from connectors.types import IntegrationType


class MetaAdsConnector(BaseConnector):
    integration_type = IntegrationType.META_ADS

    async def validate_credentials(self, credentials: dict) -> bool:
        raise NotImplementedError("Meta Ads OAuth non ancora implementato")

    async def sync(self, project_id: str) -> SyncResult:
        raise NotImplementedError("Meta Ads sync non ancora implementato")
