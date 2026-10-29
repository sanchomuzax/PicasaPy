"""A Létrehozás párbeszédablakainak QML-forráskészlete a #6051 után."""

from __future__ import annotations

from pathlib import Path

_QML = (
    Path(__file__).resolve().parents[2]
    / "src/picasapy/app/qml/PicasaPy"
)
_COMPONENTS = (
    "CreateDialogs.qml",
    "PosterCreateDialog.qml",
    "CollageCreateDialog.qml",
    "MovieMakerDialog.qml",
    "MovieMakerActions.qml",
    "MovieMakerTabs.qml",
    "MovieMakerOptions.qml",
    "MovieMakerPreview.qml",
    "MovieMakerPreviewLogic.qml",
    "MovieMakerPreviewRuntime.qml",
    "MovieMakerFilmstrip.qml",
    "MovieMakerSlideLogic.qml",
    "MovieMakerDialogs.qml",
    "CreateResultDialog.qml",
)


def create_dialogs_sources() -> dict[str, str]:
    """A Létrehozás menü összetartozó QML-fájljai név szerint."""
    return {
        name: (_QML / name).read_text(encoding="utf-8")
        for name in _COMPONENTS
    }


def create_dialogs_source_text() -> str:
    """A forrásőröknek közösen kereshető QML-forrásszöveg."""
    return "\n".join(create_dialogs_sources().values())
