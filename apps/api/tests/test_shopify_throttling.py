"""Shopify throttling must be retried, not treated as a hard failure."""

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.shopify.client import ShopifyAPIError, ShopifyGraphQLClient

THROTTLED_BODY = {
    "errors": [
        {
            "message": "Throttled",
            "extensions": {"code": "THROTTLED"},
        }
    ]
}
OK_BODY = {"data": {"shop": {"name": "Solmielato"}}}


def _response(status: int, body: dict | None = None, headers: dict | None = None):
    return httpx.Response(
        status,
        json=body if body is not None else {},
        headers=headers or {},
        request=httpx.Request("POST", "https://shop.myshopify.com/admin"),
    )


def _client() -> ShopifyGraphQLClient:
    return ShopifyGraphQLClient("shop.myshopify.com", "shpat_token")


def _run(coro):
    return asyncio.run(coro)


def test_throttled_graphql_response_is_retried_until_success() -> None:
    responses = [
        _response(200, THROTTLED_BODY),
        _response(200, THROTTLED_BODY),
        _response(200, OK_BODY),
    ]
    post = AsyncMock(side_effect=responses)

    with (
        patch("httpx.AsyncClient.post", new=post),
        patch("asyncio.sleep", new=AsyncMock()),
    ):
        client = _client()
        result = _run(client.execute("query { shop { name } }"))

    assert result == {"shop": {"name": "Solmielato"}}
    assert post.await_count == 3
    assert client.throttle_retries == 2


def test_http_429_is_retried_and_honours_retry_after() -> None:
    post = AsyncMock(
        side_effect=[_response(429, {}, {"Retry-After": "2"}), _response(200, OK_BODY)]
    )
    sleep = AsyncMock()

    with patch("httpx.AsyncClient.post", new=post), patch("asyncio.sleep", new=sleep):
        client = _client()
        _run(client.execute("query { shop { name } }"))

    assert post.await_count == 2
    assert sleep.await_args.args[0] == 2.0


def test_server_errors_are_retried() -> None:
    post = AsyncMock(side_effect=[_response(503), _response(200, OK_BODY)])
    with patch("httpx.AsyncClient.post", new=post), patch("asyncio.sleep", new=AsyncMock()):
        _run(_client().execute("query { shop { name } }"))
    assert post.await_count == 2


def test_persistent_throttling_eventually_reports_a_clear_error() -> None:
    post = AsyncMock(return_value=_response(429))
    with patch("httpx.AsyncClient.post", new=post), patch("asyncio.sleep", new=AsyncMock()):
        with pytest.raises(ShopifyAPIError, match="rate limit"):
            _run(_client().execute("query { shop { name } }"))


def test_network_errors_are_retried_before_giving_up() -> None:
    post = AsyncMock(side_effect=[httpx.ConnectError("boom"), _response(200, OK_BODY)])
    with patch("httpx.AsyncClient.post", new=post), patch("asyncio.sleep", new=AsyncMock()):
        _run(_client().execute("query { shop { name } }"))
    assert post.await_count == 2


def test_auth_errors_are_not_retried() -> None:
    post = AsyncMock(return_value=_response(401))
    with patch("httpx.AsyncClient.post", new=post), patch("asyncio.sleep", new=AsyncMock()):
        with pytest.raises(ShopifyAPIError):
            _run(_client().execute("query { shop { name } }"))
    assert post.await_count == 1
