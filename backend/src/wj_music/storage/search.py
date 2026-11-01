"""Shared helpers for text search in SQL."""

from typing import Any, cast

from sqlalchemy import ColumnElement

LIKE_ESCAPE = "\\"


def contains(column: Any, text: str) -> ColumnElement[bool]:
    """Case-insensitive substring match. LIKE wildcards in the text match literally."""
    escaped = text.replace(LIKE_ESCAPE, LIKE_ESCAPE * 2)
    escaped = escaped.replace("%", f"{LIKE_ESCAPE}%").replace("_", f"{LIKE_ESCAPE}_")
    return cast("ColumnElement[bool]", column.ilike(f"%{escaped}%", escape=LIKE_ESCAPE))
