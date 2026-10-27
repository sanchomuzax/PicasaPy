"""A mappafa QML-forráskészlete a #6019 szerkezeti bontása után."""

from __future__ import annotations

from pathlib import Path

_QML = (
    Path(__file__).resolve().parents[2]
    / "src/picasapy/app/qml/PicasaPy"
)
_COMPONENTS = (
    "FolderPane.qml",
    "FolderPaneContent.qml",
    "FolderPaneMenus.qml",
    "FolderPaneTreeRow.qml",
)


def folder_pane_sources() -> dict[str, str]:
    """A mappafa mind a négy, együtt viselkedő QML-fájlja név szerint."""
    return {
        name: (_QML / name).read_text(encoding="utf-8")
        for name in _COMPONENTS
    }


def folder_pane_source_text() -> str:
    """A forrásőröknek közösen kereshető mappafa-forrásszöveg."""
    return "\n".join(folder_pane_sources().values())
