"""Stub connector — implementazione reale in fase successiva."""

from connectors.base import BaseConnector, SyncResult
from connectors.types import IntegrationType


class GscConnector(BaseConnector):
    integration_type = IntegrationType.GSC

    async def validate_credentials(self, credentials: dict) -> bool:
        raise NotImplementedError("GSC OAuth non ancora implementato")

    async def sync(self, project_id: str) -> SyncResult:
        raise NotImplementedError("GSC sync non ancora implementato")
