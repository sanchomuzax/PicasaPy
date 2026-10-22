"""#5546: a diaidő egyes számban „1 second”, többesben „N seconds”.

Az eredeti vetítő sávja (`oneup`) a kijelzési időt egyes és többes számmal írja
ki: a `0x0080304c` `cmp esi, 1` után 1-nél a `OneUpUI::second`, különben a
`OneUpUI::seconds` fordítási kulcsot veszi. Nálunk a `SlideshowView.qml` mindig
a többes számot írta, angol felületen tehát „1 seconds” jelent meg.

A magyar felületen mindkét alak „másodperc” marad, ezt a második osztály őrzi.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QTranslator, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_APP = Path(picasapy.app.__file__).parent
_QML = _APP / "qml"
_I18N = _APP / "i18n"


def _nevvel(gyoker, nev: str):
    """A `QObject.children()` a QML-fát is bejárja (nem csak a vizuálisat)."""

    def walk(item):
        for gy in item.children():
            yield gy
            yield from walk(gy)

    for it in walk(gyoker):
        if (it.objectName() or "") == nev:
            return it
    return None


def _kiirt_szoveg(elem, masodperc: int) -> str:
    elem.setProperty("seconds", masodperc)
    return _nevvel(elem, "slideshowTimeValue").property("text")


@pytest.fixture
def vetito(qt_app):
    motor = QQmlEngine()
    motor.addImportPath(str(_QML))
    komponens = QQmlComponent(
        motor, QUrl.fromLocalFile(str(_QML / "PicasaPy" / "SlideshowView.qml"))
    )
    elem = komponens.create()
    assert elem is not None, komponens.errorString()
    yield elem
    elem.deleteLater()


@pytest.fixture
def magyar_vetito(qt_app):
    forditó = QTranslator(qt_app)
    assert forditó.load("picasapy_hu", str(_I18N)), "a magyar .qm nem tölthető be"
    qt_app.installTranslator(forditó)
    motor = QQmlEngine()
    motor.addImportPath(str(_QML))
    komponens = QQmlComponent(
        motor, QUrl.fromLocalFile(str(_QML / "PicasaPy" / "SlideshowView.qml"))
    )
    try:
        elem = komponens.create()
        assert elem is not None, komponens.errorString()
        yield elem
        elem.deleteLater()
    finally:
        qt_app.removeTranslator(forditó)


class TestAngolFelulet:
    def test_1_masodperc_EGYES_szamban_second(self, vetito):
        assert _kiirt_szoveg(vetito, 1) == "1 second"

    def test_2_masodperc_TOBBES_szamban_seconds(self, vetito):
        assert _kiirt_szoveg(vetito, 2) == "2 seconds"


class TestMagyarFelulet:
    """A magyar szöveg nem változhat: mindkét alak „másodperc”."""

    def test_1_masodperc_magyarul(self, magyar_vetito):
        assert _kiirt_szoveg(magyar_vetito, 1) == "1 másodperc"

    def test_2_masodperc_magyarul(self, magyar_vetito):
        assert _kiirt_szoveg(magyar_vetito, 2) == "2 másodperc"
