"""One-line excerpts of lyrics for search results. No I/O."""

import re

ELLIPSIS = "…"
LINE_BREAK = re.compile(r"\s*\n\s*")
SPACES = re.compile(r"[ \t]+")


def make_snippet(text: str, query: str, radius: int = 40) -> str:
    """An excerpt around the first match, with lines joined by " / "."""
    flat = SPACES.sub(" ", LINE_BREAK.sub(" / ", text.replace("\r\n", "\n").strip()))
    match = re.search(re.escape(query), flat, re.IGNORECASE)
    if match is None:
        head = flat[: radius * 2]
        return head + (ELLIPSIS if len(head) < len(flat) else "")
    start = max(0, match.start() - radius)
    end = min(len(flat), match.end() + radius)
    return (ELLIPSIS if start > 0 else "") + flat[start:end] + (ELLIPSIS if end < len(flat) else "")
