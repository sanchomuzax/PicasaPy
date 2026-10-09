"""#4639: a Súgó ▸ Billentyűkódok a bekötött gyorsbillentyűket mutatja."""

from __future__ import annotations

import re
from pathlib import Path

import picasapy.app
from PySide6.QtCore import QMetaObject, QObject, Qt


_QML_DIR = Path(picasapy.app.__file__).parent / "qml"


def _shortcut_blocks():
    """A QML Shortcut-blokkjai, a beágyazott kezelőkapcsos zárójelekkel."""
    for path in _QML_DIR.rglob("*.qml"):
        source = path.read_text(encoding="utf-8")
        for match in re.finditer(r"\bShortcut\s*\{", source):
            start = match.end() - 1
            depth = 0
            for end in range(start, len(source)):
                if source[end] == "{":
                    depth += 1
                elif source[end] == "}":
                    depth -= 1
                    if depth == 0:
                        yield source[start : end + 1]
                        break


def _megnyit_billentyu_sugot(window, qt_app):
    menu = window.findChild(QObject, "menuHelpKeyboardShortcuts")
    assert menu is not None, "hiányzik a Súgó ▸ Billentyűkódok menüpont"
    assert menu.property("enabled") is True
    assert menu.property("placeholder") is not True
    QMetaObject.invokeMethod(menu, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()

    dialog = window.findChild(QObject, "helpDialog")
    assert dialog is not None and dialog.property("visible") is True
    assert dialog.property("topic") == "features/billentyuk.md"
    return window.findChild(QObject, "helpTopicText")


def test_billentyu_menu_a_helyi_sugo_bekotott_listajat_nyitja(qml_app, qt_app):
    window, _controller, _engine = qml_app
    szoveg = _megnyit_billentyu_sugot(window, qt_app)

    assert szoveg is not None
    tartalom = str(szoveg.property("text"))
    assert "Ctrl+N" in tartalom
    assert "Ctrl+Shift+O" in tartalom
    assert "## File" in tartalom
    assert "## Edit" in tartalom
    assert "## View" in tartalom


def test_a_sugo_minden_listazott_billentyujehez_van_aktivalt_kezelo(
    qml_app, qt_app
):
    window, _controller, _engine = qml_app
    szoveg = _megnyit_billentyu_sugot(window, qt_app)
    tartalom = str(szoveg.property("text"))
    billentyuk = re.findall(r"^- `([^`]+)`$", tartalom, re.MULTILINE)

    assert billentyuk, "a súgó nem állított elő gyorsbillentyű-listát"
    blokkok = list(_shortcut_blocks())
    for billentyu in billentyuk:
        billentyu = billentyu.strip()
        assert any(
            f'sequence: "{billentyu}"' in blokk and "onActivated:" in blokk
            for blokk in blokkok
        ), f"a súgóban szereplő {billentyu!r} billentyűnek nincs QML-kezelője"
