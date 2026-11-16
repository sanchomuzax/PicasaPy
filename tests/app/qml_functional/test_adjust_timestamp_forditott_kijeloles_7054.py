"""#7054: a dátumállító ablak több kijelölt képnél a rácsban első kép dátumával nyíljon.

Több kép kijelölésekor (fordított kattintási sorrendben is) az ablak kiinduló
dátuma a rácssorrend szerinti legelső kép dátuma kell legyen (Picasa 3.9: 0x0057d7f0).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent, QPointingDevice
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre

DATUMOK = (
    ("a.jpg", "2020:01:01 10:00:00"),
    ("b.jpg", "2020:01:03 12:00:00"),
    ("c.jpg", "2020:01:05 14:00:00"),
)

_ORA = [1000]


def _kepek(lib: Path) -> None:
    for nev, taken_at in DATUMOK:
        make_jpeg(lib / nev, taken_at=taken_at, datetime_0th=taken_at)


@pytest.fixture
def timestamp_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_kepek)


def _var(qt_app, feltetel, leiras: str, ido: float = 10.0) -> None:
    assert var_feltetelre(qt_app, feltetel, ido), f"időtúllépés: {leiras}"


def _elem(window, nev: str) -> QObject:
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"nem található: {nev}"
    return elem


def _kattints_elem(elem, qt_app, window=None) -> None:
    pont = elem.mapToScene(
        QPointF(float(elem.property("width")) / 2, float(elem.property("height")) / 2)
    ).toPoint()
    ablak = window if window is not None else elem.window()
    assert ablak is not None, f"{elem.objectName()} nem látható ablakban"
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(pont.x(), pont.y()),
    )
    qt_app.processEvents()


def _bejar(root):
    sor = [root]
    while sor:
        elem = sor.pop(0)
        yield elem
        sor.extend(elem.childItems())


def _indexkep(window, sor: int):
    for elem in _bejar(window.contentItem()):
        if elem.objectName() == "thumbMouseArea":
            cella = elem.parentItem()
            if cella is not None and cella.property("index") == sor:
                return elem
    return None


def _kozeppont(window, sor: int) -> QPointF:
    terulet = _indexkep(window, sor)
    assert terulet is not None, f"a(z) {sor}. sor indexképe nem található"
    return terulet.mapToScene(
        QPointF(terulet.width() / 2, terulet.height() / 2)
    )


def _kattints_indexkepre(
    window, qt_app, sor: int, mods: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier
) -> None:
    """Valódi kattintás az indexképre — időközökkel a kettős kattintás ellen."""
    kozep = _kozeppont(window, sor)
    for tipus in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
        _ORA[0] += 1000
        esemeny = QMouseEvent(
            tipus,
            kozep,
            kozep,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton
            if tipus == QEvent.Type.MouseButtonPress
            else Qt.MouseButton.NoButton,
            mods,
            QPointingDevice.primaryPointingDevice(),
        )
        esemeny.setTimestamp(_ORA[0])
        qt_app.sendEvent(window, esemeny)
    qt_app.processEvents()
    assert not window.property("viewerOpen"), "a kattintás nem nyithatja meg a nézőt"


def _selected_indexes(window) -> list[int]:
    val = window.property("selectedIndexes")
    if hasattr(val, "toVariant"):
        val = val.toVariant()
    return [int(x) for x in (val or [])]


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_forditott_sorrendu_kijelolesnel_racssorrend_szerinti_elso_kep_datuma_nyilik_7054(
    timestamp_app, qt_app, magassag_eltolas
) -> None:
    """Több kijelölt képnél (fordított sorrendben kattintva: 1, majd Ctrl+0)
    az Eszközök -> Dátum és idő beállítása ablak a rácsban legelöl álló (0. sor)
    kép dátumával ('2020-01-01') nyílik meg (#7054)."""
    window, controller, _engine = timestamp_app
    window.setHeight(window.height() + magassag_eltolas)
    assert controller.sortFolderBy(controller.currentFolder, "date")
    window.show()
    qt_app.processEvents()

    # Valódi kattintás fordított sorrendben: először az 1. sor (b.jpg),
    # majd Ctrl-lel a 0. sor (a.jpg).
    _kattints_indexkepre(window, qt_app, 1)
    _kattints_indexkepre(window, qt_app, 0, Qt.KeyboardModifier.ControlModifier)

    # A belső kijelölési tömb a kattintási sorrendet követi: [1, 0]
    kijeloles = _selected_indexes(window)
    assert kijeloles == [1, 0], f"a várt kattintási sorrend [1, 0], ehelyett: {kijeloles}"

    eszkozok = _elem(window, "menuTools")
    eszkozok.open()
    _var(qt_app, lambda: eszkozok.property("visible"), "az Eszközök menü megnyitása")

    menu_item = _elem(window, "menuToolsAdjustTimestamp")
    assert menu_item.property("enabled"), "a menüpont engedélyezett kell legyen"
    _kattints_elem(menu_item, qt_app, window)

    dialog = _elem(window, "adjustTimestampDialog")
    _var(qt_app, lambda: dialog.property("visible"), "a dátumállító ablak megnyílása")

    assert dialog.property("title") == "Adjust Photo Date - 2 items"
    # A rácsban legelöl álló kép az a.jpg (0. sor, '2020-01-01 10:00:00'),
    # nem pedig a kattintási sorrend szerinti első (b.jpg, 1. sor, '2020-01-03 12:00:00').
    datum_mezo = _elem(window, "adjustTimestampCurrentDateField")
    ido_mezo = _elem(window, "adjustTimestampCurrentTimeField")

    assert datum_mezo.property("text") == "2020-01-01"
    assert ido_mezo.property("displayText") == "10:00:00"

    cancel_btn = _elem(window, "adjustTimestampCancel")
    _kattints_elem(cancel_btn, qt_app, window)
    _var(qt_app, lambda: not dialog.property("visible"), "a dialógus bezáródik")


def test_egy_kep_kijelolese_es_nezoi_megnyitas_valtozatlan_7054(
    timestamp_app, qt_app
) -> None:
    """Egy kép kijelölésekor az ablak a kiválasztott kép dátumával nyílik (#7054)."""
    window, controller, _engine = timestamp_app
    assert controller.sortFolderBy(controller.currentFolder, "date")
    window.show()
    qt_app.processEvents()

    # Egyetlen kép kijelölése: 1. sor (b.jpg, '2020-01-03 12:00:00')
    _kattints_indexkepre(window, qt_app, 1)
    kijeloles = _selected_indexes(window)
    assert kijeloles == [1]

    eszkozok = _elem(window, "menuTools")
    eszkozok.open()
    _var(qt_app, lambda: eszkozok.property("visible"), "az Eszközök menü megnyitása")

    menu_item = _elem(window, "menuToolsAdjustTimestamp")
    assert menu_item.property("enabled"), "a menüpont engedélyezett kell legyen"
    _kattints_elem(menu_item, qt_app, window)

    dialog = _elem(window, "adjustTimestampDialog")
    _var(qt_app, lambda: dialog.property("visible"), "a dátumállító ablak megnyílása")

    assert dialog.property("title") == "Adjust Photo Date"
    assert _elem(window, "adjustTimestampCurrentDateField").property("text") == "2020-01-03"
    assert _elem(window, "adjustTimestampCurrentTimeField").property("displayText") == "12:00:00"

    cancel_btn = _elem(window, "adjustTimestampCancel")
    _kattints_elem(cancel_btn, qt_app, window)
    _var(qt_app, lambda: not dialog.property("visible"), "a dialógus bezáródik")
