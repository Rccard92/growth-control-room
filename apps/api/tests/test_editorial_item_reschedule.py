"""Editorial item reschedule service tests."""

import asyncio
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.content_seo_editorial import ContentSeoEditorialItem
from app.schemas.content_seo_editorial import EditorialItemRescheduleRequest
from app.services.content.editorial_item_service import reschedule_editorial_item


def _make_item(
    project_id,
    item_id,
    planned: date,
    *,
    title: str = "Test item",
) -> ContentSeoEditorialItem:
    return ContentSeoEditorialItem(
        id=item_id,
        project_id=project_id,
        title=title,
        content_type="educational_article",
        planned_date=planned,
        status="idea",
    )


def test_reschedule_cascade_false_only_current_item() -> None:
    project_id = uuid4()
    item_id = uuid4()
    row = _make_item(project_id, item_id, date(2026, 6, 14))
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    async def run():
        with (
            patch(
                "app.services.content.editorial_item_service.get_editorial_item",
                new=AsyncMock(return_value=row),
            ),
            patch(
                "app.services.content.editorial_item_service._duplicate_planned_date_warning",
                new=AsyncMock(return_value=None),
            ),
        ):
            request = EditorialItemRescheduleRequest.model_validate(
                {"plannedDate": "2026-06-15", "cascade": False}
            )
            updated, delta, warning = await reschedule_editorial_item(
                mock_session, project_id, item_id, request
            )

        assert delta == 1
        assert warning is None
        assert len(updated) == 1
        assert row.planned_date == date(2026, 6, 15)
        mock_session.execute.assert_not_called()

    asyncio.run(run())


def test_reschedule_cascade_true_moves_following_items() -> None:
    project_id = uuid4()
    item_id = uuid4()
    following_id = uuid4()
    row = _make_item(project_id, item_id, date(2026, 6, 14))
    following = _make_item(project_id, following_id, date(2026, 6, 16), title="Next")
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    following_result = MagicMock()
    following_result.scalars.return_value.all.return_value = [following]

    async def run():
        with (
            patch(
                "app.services.content.editorial_item_service.get_editorial_item",
                new=AsyncMock(return_value=row),
            ),
            patch(
                "app.services.content.editorial_item_service._duplicate_planned_date_warning",
                new=AsyncMock(return_value=None),
            ),
        ):
            mock_session.execute = AsyncMock(return_value=following_result)
            request = EditorialItemRescheduleRequest.model_validate(
                {"plannedDate": "2026-06-15", "cascade": True}
            )
            updated, delta, warning = await reschedule_editorial_item(
                mock_session, project_id, item_id, request
            )

        assert delta == 1
        assert warning is None
        assert row.planned_date == date(2026, 6, 15)
        assert following.planned_date == date(2026, 6, 17)
        assert len(updated) == 2

    asyncio.run(run())


def test_reschedule_negative_delta() -> None:
    project_id = uuid4()
    item_id = uuid4()
    following_id = uuid4()
    row = _make_item(project_id, item_id, date(2026, 6, 16))
    following = _make_item(project_id, following_id, date(2026, 6, 18), title="Next")
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    following_result = MagicMock()
    following_result.scalars.return_value.all.return_value = [following]

    async def run():
        with (
            patch(
                "app.services.content.editorial_item_service.get_editorial_item",
                new=AsyncMock(return_value=row),
            ),
            patch(
                "app.services.content.editorial_item_service._duplicate_planned_date_warning",
                new=AsyncMock(return_value=None),
            ),
        ):
            mock_session.execute = AsyncMock(return_value=following_result)
            request = EditorialItemRescheduleRequest.model_validate(
                {"plannedDate": "2026-06-14", "cascade": True}
            )
            updated, delta, _warning = await reschedule_editorial_item(
                mock_session, project_id, item_id, request
            )

        assert delta == -2
        assert row.planned_date == date(2026, 6, 14)
        assert following.planned_date == date(2026, 6, 16)
        assert len(updated) == 2

    asyncio.run(run())


def test_reschedule_duplicate_date_warning() -> None:
    project_id = uuid4()
    item_id = uuid4()
    row = _make_item(project_id, item_id, date(2026, 6, 14))
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    async def run():
        with (
            patch(
                "app.services.content.editorial_item_service.get_editorial_item",
                new=AsyncMock(return_value=row),
            ),
            patch(
                "app.services.content.editorial_item_service._duplicate_planned_date_warning",
                new=AsyncMock(
                    return_value="Alcuni contenuti potrebbero cadere nello stesso giorno."
                ),
            ),
        ):
            request = EditorialItemRescheduleRequest.model_validate(
                {"plannedDate": "2026-06-15", "cascade": False}
            )
            _updated, _delta, warning = await reschedule_editorial_item(
                mock_session, project_id, item_id, request
            )

        assert warning == "Alcuni contenuti potrebbero cadere nello stesso giorno."

    asyncio.run(run())


def test_reschedule_item_not_found() -> None:
    project_id = uuid4()
    item_id = uuid4()
    mock_session = AsyncMock()

    async def run():
        with patch(
            "app.services.content.editorial_item_service.get_editorial_item",
            new=AsyncMock(
                side_effect=HTTPException(
                    status_code=404, detail="Contenuto editoriale non trovato."
                )
            ),
        ):
            request = EditorialItemRescheduleRequest.model_validate(
                {"plannedDate": "2026-06-15", "cascade": False}
            )
            with pytest.raises(HTTPException) as exc:
                await reschedule_editorial_item(
                    mock_session, project_id, item_id, request
                )
            assert exc.value.status_code == 404

    asyncio.run(run())
