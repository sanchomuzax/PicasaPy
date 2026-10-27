"""Forrásnézet a #6016 után menünként külön QML-fájlokhoz."""

from pathlib import Path

import picasapy.app

_MENU_DIR = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_MENU_FILES = (
    "PicasaMenuBar.qml",
    "PicasaFileMenu.qml",
    "PicasaEditMenu.qml",
    "PicasaViewMenu.qml",
    "PicasaFolderMenu.qml",
    "PicasaPictureMenu.qml",
    "PicasaCreateMenu.qml",
    "PicasaToolsMenu.qml",
    "PicasaHelpMenu.qml",
    "PicasaFolderViewMenu.qml",
)


def menu_sources() -> str:
    """A felső menüsor forrása egy szövegként, a komponenseket is beleértve."""
    return "\n".join(
        (_MENU_DIR / name).read_text(encoding="utf-8") for name in _MENU_FILES
    )


def menu_component_source(name: str) -> str:
    """Egy menükomponens QML-forrása."""
    return (_MENU_DIR / name).read_text(encoding="utf-8")
