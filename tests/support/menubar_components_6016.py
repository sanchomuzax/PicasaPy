"""Forrásnézet a #6016 után menünként külön QML-fájlokhoz."""

from pathlib import Path

import picasapy.app

_MENU_DIR = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_QML_DIR = _MENU_DIR.parent
_MENU_FILES = (
    "MainMenuBar.qml",
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


def main_sources() -> str:
    """A főablak forráscsaládja a külön Main-komponensekkel együtt."""
    files = [_QML_DIR / "Main.qml", *_MENU_DIR.glob("Main*.qml")]
    return "\n".join(path.read_text(encoding="utf-8") for path in files)
