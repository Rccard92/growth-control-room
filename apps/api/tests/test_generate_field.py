"""Field-level SEO constants (no OpenAI import required)."""

FIELD_MAP = {
    "title": ("product_title", "collection_title"),
    "handle": ("handle", "handle"),
    "seoTitle": ("seo_title", "seo_title"),
    "metaDescription": ("meta_description", "meta_description"),
    "descriptionHtml": ("description_html", "description_html"),
    "imageAlt": ("image_alts", "image_alt"),
}


def test_field_map_meta_description() -> None:
    assert FIELD_MAP["metaDescription"] == ("meta_description", "meta_description")


def test_field_map_image_alt_product_vs_collection() -> None:
    assert FIELD_MAP["imageAlt"][0] == "image_alts"
    assert FIELD_MAP["imageAlt"][1] == "image_alt"
