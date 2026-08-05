"""Parse Telegram Desktop export message text fields."""


def flatten_text(text) -> str | None:
    """Convert Telegram export text (str, list, or null) to plain string."""
    if text is None:
        return None
    if isinstance(text, str):
        stripped = text.strip()
        return stripped or None
    if isinstance(text, list):
        parts: list[str] = []
        for item in text:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
        result = "".join(parts).strip()
        return result or None
    return None
