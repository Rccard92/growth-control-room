"""Stub connector — implementazione reale in fase successiva."""

from connectors.base import BaseConnector, SyncResult
from connectors.types import IntegrationType


class MerchantCenterConnector(BaseConnector):
    integration_type = IntegrationType.MERCHANT_CENTER

    async def validate_credentials(self, credentials: dict) -> bool:
        raise NotImplementedError("Merchant Center OAuth non ancora implementato")

    async def sync(self, project_id: str) -> SyncResult:
        raise NotImplementedError("Merchant Center sync non ancora implementato")
