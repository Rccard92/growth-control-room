"""ShopifyQL must actually reach Shopify.

Every ShopifyQL entry point used to call `get_shopify_client_for_store(store, session)`
against a one-argument helper. The TypeError was swallowed by a broad `except`, so the
dashboard reported "ShopifyQL non disponibile" and blamed the OAuth scopes on a token
that had read_reports all along.
"""

import ast
import inspect
from pathlib import Path

from app.services.shopify.connect import get_shopify_client_for_store

API_ROOT = Path(__file__).resolve().parents[1] / "app"


def test_helper_takes_only_the_store() -> None:
    params = list(inspect.signature(get_shopify_client_for_store).parameters)
    assert params == ["store"]


def test_every_call_site_passes_exactly_one_argument() -> None:
    expected = len(inspect.signature(get_shopify_client_for_store).parameters)
    offenders: list[str] = []

    for path in API_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if name != "get_shopify_client_for_store":
                continue
            if len(node.args) + len(node.keywords) != expected:
                offenders.append(f"{path.name}:{node.lineno} ({len(node.args)} argomenti)")

    assert not offenders, "Chiamate con arità sbagliata:\n" + "\n".join(offenders)
