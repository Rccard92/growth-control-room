from connectors.base import BaseConnector
from connectors.providers.ga4 import Ga4Connector
from connectors.providers.google_ads import GoogleAdsConnector
from connectors.providers.gsc import GscConnector
from connectors.providers.klaviyo import KlaviyoConnector
from connectors.providers.merchant_center import MerchantCenterConnector
from connectors.providers.meta_ads import MetaAdsConnector
from connectors.providers.shopify import ShopifyConnector
from connectors.providers.tiktok import TikTokConnector
from connectors.types import IntegrationType

CONNECTOR_REGISTRY: dict[IntegrationType, type[BaseConnector]] = {
    IntegrationType.SHOPIFY: ShopifyConnector,
    IntegrationType.META_ADS: MetaAdsConnector,
    IntegrationType.GOOGLE_ADS: GoogleAdsConnector,
    IntegrationType.KLAVIYO: KlaviyoConnector,
    IntegrationType.GSC: GscConnector,
    IntegrationType.GA4: Ga4Connector,
    IntegrationType.MERCHANT_CENTER: MerchantCenterConnector,
    IntegrationType.TIKTOK: TikTokConnector,
}


def get_connector(integration_type: IntegrationType) -> BaseConnector:
    connector_cls = CONNECTOR_REGISTRY.get(integration_type)
    if connector_cls is None:
        raise ValueError(f"Connector non registrato per: {integration_type}")
    return connector_cls()


def list_connectors() -> list[IntegrationType]:
    return list(CONNECTOR_REGISTRY.keys())
