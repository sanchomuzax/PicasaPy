"""A futó PicasaPy-példány mappájának meghatározása."""

from __future__ import annotations

import sys
from pathlib import Path


def program_location() -> str:
    """A csomagolt exe vagy a forráscsomag mappáját adja vissza."""
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable).resolve().parent)
    return str(Path(__file__).resolve().parents[1])
