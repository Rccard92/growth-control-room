import os
import uuid
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.services.shopify.metafield_utils import merged_metafield_item


def test_merged_empty_definition_slot() -> None:
    definition = SimpleNamespace(
        id=uuid.uuid4(),
        namespace="custom",
        key="domanda_1",
        type_name="single_line_text_field",
        name="Domanda 1",
        description="FAQ domanda",
    )
    item = merged_metafield_item(definition=definition, value_row=None)
    assert item["definition_id"] == str(definition.id)
    assert item["metafield_id"] is None
    assert item["exists_on_product"] is False
    assert item["is_empty"] is True
    assert item["editable"] is True
    assert item["ai_generatable"] is True
    assert item["display_value"] == ""


def test_merged_definition_with_value() -> None:
    def_id = uuid.uuid4()
    mf_id = uuid.uuid4()
    definition = SimpleNamespace(
        id=def_id,
        namespace="custom",
        key="domanda_1",
        type_name="single_line_text_field",
        name="Domanda 1",
        description=None,
    )
    value_row = SimpleNamespace(
        id=mf_id,
        namespace="custom",
        key="domanda_1",
        type="single_line_text_field",
        value="Quanto dura?",
        definition_name="Domanda 1",
        definition_description=None,
        updated_at=None,
    )
    item = merged_metafield_item(definition=definition, value_row=value_row)
    assert item["metafield_id"] == str(mf_id)
    assert item["exists_on_product"] is True
    assert item["is_empty"] is False
    assert item["display_value"] == "Quanto dura?"


def test_merged_orphan_value_without_definition() -> None:
    mf_id = uuid.uuid4()
    value_row = SimpleNamespace(
        id=mf_id,
        namespace="legacy",
        key="old_field",
        type="number_integer",
        value="42",
        definition_name=None,
        definition_description=None,
        updated_at=None,
    )
    item = merged_metafield_item(definition=None, value_row=value_row)
    assert item["metafield_id"] == str(mf_id)
    assert item["exists_on_product"] is True
    assert not item["editable"]
