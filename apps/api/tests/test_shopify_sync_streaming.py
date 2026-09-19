"""The product sync must stream and persist progressively, not buffer the catalogue."""

import asyncio
from unittest.mock import AsyncMock, patch

from app.services.shopify.client import ShopifyGraphQLClient


def _page(start: int, size: int) -> dict:
    return {
        "products": {
            "pageInfo": {"hasNextPage": start + size < 250, "endCursor": f"cur-{start + size}"},
            "edges": [
                {"node": {"id": f"gid://shopify/Product/{i}"}} for i in range(start, start + size)
            ],
        }
    }


def test_iter_products_yields_one_page_at_a_time() -> None:
    pages = [_page(0, 100), _page(100, 100), _page(200, 50)]
    execute = AsyncMock(side_effect=pages)

    async def run() -> list[int]:
        client = ShopifyGraphQLClient("shop.myshopify.com", "shpat_x")
        with patch.object(ShopifyGraphQLClient, "execute", new=execute):
            return [len(page) async for page in client.iter_products()]

    sizes = asyncio.run(run())
    assert sizes == [100, 100, 50]
    assert execute.await_count == 3


def test_iter_products_stops_without_a_cursor() -> None:
    body = {
        "products": {
            "pageInfo": {"hasNextPage": True, "endCursor": None},
            "edges": [{"node": {"id": "gid://shopify/Product/1"}}],
        }
    }

    async def run() -> list[list[dict]]:
        client = ShopifyGraphQLClient("shop.myshopify.com", "shpat_x")
        with patch.object(ShopifyGraphQLClient, "execute", new=AsyncMock(return_value=body)):
            return [page async for page in client.iter_products()]

    assert len(asyncio.run(run())) == 1


def test_iter_products_passes_the_cursor_forward() -> None:
    execute = AsyncMock(side_effect=[_page(0, 100), _page(100, 100), _page(200, 50)])

    async def run() -> None:
        client = ShopifyGraphQLClient("shop.myshopify.com", "shpat_x")
        with patch.object(ShopifyGraphQLClient, "execute", new=execute):
            async for _ in client.iter_products():
                pass

    asyncio.run(run())
    cursors = [call.args[1]["after"] for call in execute.await_args_list]
    assert cursors == [None, "cur-100", "cur-200"]
