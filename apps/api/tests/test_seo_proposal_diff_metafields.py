import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.content.seo_proposal_diff import compute_changed_proposed


def test_diff_metafields_partial() -> None:
    current = {
        "metafields": [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "namespace": "custom",
                "key": "subtitle",
                "type": "single_line_text_field",
                "value": "Vecchio",
            },
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "namespace": "custom",
                "key": "badge",
                "type": "single_line_text_field",
                "value": "Invariato",
            },
        ]
    }
    proposed = {
        "metafields": [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "namespace": "custom",
                "key": "subtitle",
                "type": "single_line_text_field",
                "value": "Nuovo sottotitolo",
            },
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "namespace": "custom",
                "key": "badge",
                "type": "single_line_text_field",
                "value": "Invariato",
            },
        ]
    }
    delta, fields = compute_changed_proposed(current, proposed)
    assert fields == ["metafields"]
    assert len(delta["metafields"]) == 1
    assert delta["metafields"][0]["value"] == "Nuovo sottotitolo"


def test_diff_metafields_unchanged_excluded() -> None:
    current = {
        "metafields": [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "namespace": "custom",
                "key": "subtitle",
                "type": "single_line_text_field",
                "value": "Stesso",
            }
        ]
    }
    proposed = {"metafields": current["metafields"]}
    delta, fields = compute_changed_proposed(current, proposed)
    assert "metafields" not in fields
    assert delta == {}


def test_diff_metafields_new_slot_without_id() -> None:
    current = {"metafields": []}
    proposed = {
        "metafields": [
            {
                "id": None,
                "metafieldId": None,
                "definitionId": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "namespace": "custom",
                "key": "domanda_1",
                "type": "single_line_text_field",
                "value": "Quanto costa?",
            }
        ]
    }
    delta, fields = compute_changed_proposed(current, proposed)
    assert fields == ["metafields"]
    assert len(delta["metafields"]) == 1
    assert delta["metafields"][0]["namespace"] == "custom"
    assert delta["metafields"][0]["key"] == "domanda_1"
    assert delta["metafields"][0]["value"] == "Quanto costa?"
