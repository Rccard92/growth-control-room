"""Stub connector — implementazione reale in fase successiva."""

from connectors.base import BaseConnector, SyncResult
from connectors.types import IntegrationType


class KlaviyoConnector(BaseConnector):
    integration_type = IntegrationType.KLAVIYO

    async def validate_credentials(self, credentials: dict) -> bool:
        raise NotImplementedError("Klaviyo OAuth non ancora implementato")

    async def sync(self, project_id: str) -> SyncResult:
        raise NotImplementedError("Klaviyo sync non ancora implementato")
