"""Stub connector — implementazione reale in fase successiva."""

from connectors.base import BaseConnector, SyncResult
from connectors.types import IntegrationType


class ShopifyConnector(BaseConnector):
    integration_type = IntegrationType.SHOPIFY

    async def validate_credentials(self, credentials: dict) -> bool:
        raise NotImplementedError("Shopify OAuth non ancora implementato")

    async def sync(self, project_id: str) -> SyncResult:
        raise NotImplementedError("Shopify sync non ancora implementato")
