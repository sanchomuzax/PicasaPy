"""#422: szövegmező-kontextusmenü (a Picasa `Address` menüosztálya).

Az eredetiben MINDEN szövegmező alatt ott van a hét tételes jobbklikk-menü;
nálunk eddig egyetlen mezőben sem volt. A menü a `TextFieldContextArea`-n
át kerül a mezőkbe — a teszt azt is őrzi, hogy ne maradjon kimaradt mező.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_QML_DIR = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy"
)
_KEEPALIVE: list = []

# #422: a jelszó-mezőben SZÁNDÉKOSAN nincs menü — a „Másolás" ott a jelszót
# tenné a vágólapra. (A Qt jelszó-módban amúgy sem másol, de a tétel puszta
# felkínálása is félrevezető lenne.)
_INTENTIONALLY_WITHOUT_MENU = ("echoMode: TextInput.Password",)


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _load(engine, source):
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), QUrl())
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    obj = component.create()
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((component, obj))
    return obj


class TestMenuItems:
    _MENU = (
        "import QtQuick\n"
        "import QtQuick.Controls\n"
        "import PicasaPy 1.0\n"
        "Item {\n"
        '  TextField { id: field; objectName: "field"; text: "abc" }\n'
        '  TextFieldContextMenu { objectName: "menu"; target: field }\n'
        "}\n"
    )

    ITEMS = (
        "textMenuUndo", "textMenuCut", "textMenuCopy", "textMenuPaste",
        "textMenuDelete", "textMenuSelectAll", "textMenuAutoComplete",
    )

    def test_all_seven_items_exist(self, qml_engine, qt_app):
        root = _load(qml_engine, self._MENU)
        qt_app.processEvents()
        menu = root.findChild(QObject, "menu")
        for name in self.ITEMS:
            assert menu.findChild(QObject, name) is not None, name

    def test_disabled_items_are_not_removed_from_the_menu(
        self, qml_engine, qt_app
    ):
        """#422 1. viselkedési szabály: az inaktív tétel a menüben MARAD,
        szürkén — nem tűnik el, hogy a menü magassága állandó maradjon és az
        izommemória működjön. (A `visible` a Qt-ban a popup megnyitásáig
        hamis, ezért a tétel MEGLÉTÉT és a `count`-ot mérjük.)"""
        root = _load(qml_engine, self._MENU)
        qt_app.processEvents()
        menu = root.findChild(QObject, "menu")
        cut = menu.findChild(QObject, "textMenuCut")
        assert cut.property("enabled") is False   # nincs kijelölés
        # 7 tétel + 2 elválasztó, a tiltottakkal EGYÜTT
        assert menu.property("count") == 9

    def test_selection_enables_the_clipboard_items(self, qml_engine, qt_app):
        root = _load(qml_engine, self._MENU)
        qt_app.processEvents()
        field = root.findChild(QObject, "field")
        field.selectAll()
        qt_app.processEvents()
        menu = root.findChild(QObject, "menu")
        for name in ("textMenuCut", "textMenuCopy", "textMenuDelete"):
            assert menu.findChild(QObject, name).property("enabled") is True, name

    def test_auto_complete_is_a_real_toggle(self, qml_engine, qt_app):
        """#1526: a tétel ÉLŐ kapcsoló lett (a `controller.autoComplete`
        perzisztens beállítására kötve) — a #422-es helyfoglaló megszűnt.

        Itt, `controller` nélkül betöltve a tétel szándékosan tiltott: a
        menü önmagában is betölthető kell legyen (`typeof`-őr), de kapcsolni
        csak a valódi alkalmazásban lehet — azt a
        `test_automatikus_kitoltes_1526.py` méri, a teljes appon."""
        root = _load(qml_engine, self._MENU)
        qt_app.processEvents()
        item = root.findChild(QObject, "menu").findChild(
            QObject, "textMenuAutoComplete"
        )
        assert not item.property("placeholder")
        assert item.property("checkable") is True
        assert item.property("enabled") is False  # nincs controller


class TestEveryTextFieldHasTheMenu:
    """Ne maradjon kimaradt mező: minden `TextField`/`TextArea` alatt ott
    kell lennie a `TextFieldContextArea`-nak."""

    def test_no_text_field_is_left_without_a_context_menu(self):
        missing = []
        for path in sorted(_QML_DIR.glob("*.qml")):
            if path.name.startswith("TextFieldContext"):
                continue
            source = path.read_text(encoding="utf-8")
            fields = len(re.findall(r"\b(?:TextField|TextArea)\s*\{", source))
            skipped = sum(source.count(m) for m in _INTENTIONALLY_WITHOUT_MENU)
            areas = source.count("TextFieldContextArea {}")
            if fields - skipped > areas:
                missing.append(
                    f"{path.name}: {fields} mező, {skipped} kivétel, {areas} menü"
                )
        assert not missing, "menü nélküli szövegmezők:\n" + "\n".join(missing)
