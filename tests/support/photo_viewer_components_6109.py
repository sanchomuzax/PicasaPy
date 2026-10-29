"""A fotónéző összetartozó QML-forrásai a #6109 bontása után."""

from __future__ import annotations

from pathlib import Path

_QML = (
    Path(__file__).resolve().parents[2]
    / "src/picasapy/app/qml/PicasaPy"
)


def photo_viewer_sources() -> dict[str, str]:
    """A fotónéző teljes, név szerint megőrzött komponenscsaládja."""
    return {
        fajl.name: fajl.read_text(encoding="utf-8")
        for fajl in sorted(_QML.glob("PhotoViewer*.qml"))
    }


def photo_viewer_source_text() -> str:
    """A forrásőröknek együtt kereshető fotónéző-forrás."""
    return "\n".join(photo_viewer_sources().values())
