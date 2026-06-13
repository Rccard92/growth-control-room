"""Product Knowledge items apply-import-proposal tests."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.schemas.brand_product_knowledge import BrandProductKnowledgeItemProposal
from app.services.brand_intelligence.product_knowledge_item_service import (
    apply_items_import_proposal,
)


def _proposal(**kwargs: object) -> BrandProductKnowledgeItemProposal:
    base = {
        "productName": "Miele di Limone",
        "origin": "Sicilia",
        "tasteNotes": "Agrumato",
    }
    base.update(kwargs)
    return BrandProductKnowledgeItemProposal.model_validate(base)


def test_apply_creates_ai_import_item() -> None:
    added: list[SimpleNamespace] = []
    project_id = uuid4()

    async def run() -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: [])))
        )

        def capture_add(row: SimpleNamespace) -> None:
            added.append(row)

        async def fake_refresh(row: SimpleNamespace) -> None:
            row.id = uuid4()
            row.project_id = project_id
            row.created_at = datetime.now(UTC)
            row.updated_at = datetime.now(UTC)

        mock_session.add = capture_add
        mock_session.flush = AsyncMock()
        mock_session.refresh = fake_refresh
        mock_session.commit = AsyncMock()

        result = await apply_items_import_proposal(mock_session, project_id, [_proposal()])
        assert len(result.saved) == 1
        assert len(added) == 1
        assert added[0].source_type == "ai_import"
        assert added[0].origin == "Sicilia"

    asyncio.run(run())


def test_apply_skips_duplicate_shopify_id() -> None:
    existing_id = uuid4()
    shopify_id = uuid4()
    store_id = uuid4()
    existing = SimpleNamespace(
        id=existing_id,
        project_id=uuid4(),
        shopify_product_id=shopify_id,
        shopify_title="Miele di Limone",
        shopify_handle="miele-limone",
        product_name="Miele di Limone",
        strategic_description="Già compilata",
        origin="Sicilia",
        ingredients=None,
        production_process=None,
        usage_suggestions=None,
        objections=None,
        faq=None,
        allowed_claims=None,
        forbidden_claims=None,
        seo_notes=None,
    )
    shopify_product = SimpleNamespace(
        id=shopify_id,
        shopify_gid="gid://1",
        handle="miele-limone",
        title="Miele di Limone",
        shopify_store_id=store_id,
    )

    async def run() -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one_or_none=lambda: shopify_product),
                MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: [existing]))),
            ]
        )
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        with patch(
            "app.services.brand_intelligence.product_knowledge_item_service.get_shopify_store_for_project",
            new=AsyncMock(return_value=SimpleNamespace(id=store_id)),
        ):
            proposal = _proposal(shopifyProductId=shopify_id)
            result = await apply_items_import_proposal(mock_session, uuid4(), [proposal])

        assert len(result.saved) == 0
        assert len(result.skipped) == 1
        assert result.skipped[0].duplicate_candidates
        mock_session.add.assert_not_called()

    asyncio.run(run())


def test_apply_skips_duplicate_product_name() -> None:
    existing = SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        shopify_product_id=None,
        shopify_title=None,
        shopify_handle=None,
        product_name="Miele di Limone",
        strategic_description=None,
        origin=None,
        ingredients=None,
        production_process=None,
        usage_suggestions=None,
        objections=None,
        faq=None,
        allowed_claims=None,
        forbidden_claims=None,
        seo_notes=None,
    )

    async def run() -> None:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: [existing])))
        )
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        result = await apply_items_import_proposal(mock_session, uuid4(), [_proposal()])
        assert len(result.saved) == 0
        assert len(result.skipped) == 1
        mock_session.add.assert_not_called()

    asyncio.run(run())
