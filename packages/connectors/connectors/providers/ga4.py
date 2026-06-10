"""Stub connector — implementazione reale in fase successiva."""

from connectors.base import BaseConnector, SyncResult
from connectors.types import IntegrationType


class Ga4Connector(BaseConnector):
    integration_type = IntegrationType.GA4

    async def validate_credentials(self, credentials: dict) -> bool:
        raise NotImplementedError("GA4 OAuth non ancora implementato")

    async def sync(self, project_id: str) -> SyncResult:
        raise NotImplementedError("GA4 sync non ancora implementato")
