"""Stub connector — implementazione reale in fase successiva."""

from connectors.base import BaseConnector, SyncResult
from connectors.types import IntegrationType


class TikTokConnector(BaseConnector):
    integration_type = IntegrationType.TIKTOK

    async def validate_credentials(self, credentials: dict) -> bool:
        raise NotImplementedError("TikTok OAuth non ancora implementato")

    async def sync(self, project_id: str) -> SyncResult:
        raise NotImplementedError("TikTok sync non ancora implementato")
