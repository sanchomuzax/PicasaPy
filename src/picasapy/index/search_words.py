"""Az EXIF keresőmezők szóalakjának közös előállítója."""

from __future__ import annotations

import re

_WORD = re.compile(r"[^\W_]+", re.UNICODE)


def exif_search_words(value: str | None) -> str | None:
    """Elválasztójelek mentén szavakra bont, kisbetűsít, egyjegyű számot dob."""
    if not value:
        return None
    words = (
        word.casefold()
        for word in _WORD.findall(value)
        if not (len(word) == 1 and word.isdecimal())
    )
    result = " ".join(words)
    return result or None
