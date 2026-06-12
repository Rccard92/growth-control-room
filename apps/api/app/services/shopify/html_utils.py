from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if stripped:
            self._parts.append(stripped)

    def get_text(self) -> str:
        return " ".join(self._parts)


def html_to_text(html: str | None) -> str | None:
    if not html or not html.strip():
        return None
    parser = _TextExtractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return None
    text = parser.get_text().strip()
    return text or None
