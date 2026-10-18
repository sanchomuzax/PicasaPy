"""A Helyek betöltő állapota az eredeti `geopanel` elrendezést követi (#5275).

A `docs/specs/jobb-fiok-meretek.md` 4. szakasza szerint a betöltő felirat
(213 × 25) y 117-nél, az ikon (64 × 52) y 153-nál áll a geopanel vásznán. A
térkép és a `loading_base` y 28-nál kezdődik, tehát a betöltő területhez képest
a felirat y 89-nél, az ikon y 125-nél van. Az ikon képpontjait a renderelt
ablakon vetjük össze az eredeti `loading_icon` PNG-jével.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.support.varakozas import hibaturo_feltetel, var_feltetelre

IKON = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/assets/tools/loading_icon.png"
)
#: A `loading_base` szélessége a spec szerint (264 × 284).
ALAP_SZELESSEG = 264


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _item(window, object_name: str) -> QQuickItem:
    for item in _walk(window.contentItem()):
        if item.objectName() == object_name:
            return item
    raise AssertionError(f"A főablakból hiányzik: {object_name}")


def _var(qt_app, predicate, timeout: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(predicate, (AttributeError, RuntimeError, TypeError)), timeout)


def _kattint(window, item: QQuickItem, qt_app) -> None:
    assert _var(qt_app, lambda: item.width() > 0 and item.height() > 0)
    center = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _nyugszik(qt_app, item: QQuickItem, timeout: float = 10.0) -> None:
    """Megvárja, míg a fiók nyitó animációja véget ér: a pozíció tíz mintán át nem változik."""
    utolso = None
    azonos = 0

    def _allando() -> bool:
        nonlocal utolso, azonos
        aktualis = item.mapToScene(QPointF(0, 0))
        azonos = azonos + 1 if aktualis == utolso else 0
        utolso = aktualis
        return azonos >= 10

    assert _var(qt_app, _allando, timeout)


def _js_kerekites(szam: float) -> int:
    """A QML `Math.round` szerint kerekít: a .5 felfelé megy (Pythonban a `round` a párosra)."""
    return math.floor(szam + 0.5)


def _betoltes_alatt(qml_app, qt_app, tmp_path):
    """A Helyek panel megnyitása, a térkép betöltés közbeni állapotban."""
    window, _controller, _engine = qml_app
    teszt_terkep = tmp_path / "TesztHelyterkep.qml"
    teszt_terkep.write_text(
        """import QtQuick
Item {
    property var markers: []
    property var mapTypeNames: []
    property int activeMapTypeIndex: 0
    property bool mapLoading: true
    property bool offline: false
    signal markerActivated(int row)
    signal markerSearchRequested(var rows)
    signal markerEraseRequested(var rows)
    signal placePicked(real latitude, real longitude)
    function selectMapType(index) {}
}
""",
        encoding="utf-8",
    )
    loader = _item(window, "placesMapLoader")
    assert loader.setProperty("source", QUrl.fromLocalFile(str(teszt_terkep)))
    _kattint(window, _item(window, "trayPanelToggle_places"), qt_app)
    assert _var(qt_app, lambda: loader.property("item") is not None)
    ikon = _item(window, "placesMapLoadingIndicator")
    # A `status` enum PySide-ból nem olvasható ki; a `progress` 1.0 a teljes betöltés.
    assert _var(qt_app, lambda: ikon.isVisible() and ikon.property("progress") == 1.0)
    _nyugszik(qt_app, ikon)
    return window, loader, ikon


def _relativ(item: QQuickItem, alap: QQuickItem) -> QPointF:
    return item.mapToItem(alap, QPointF(0, 0))


def test_felirat_es_ikon_meret_es_hely_a_specen_belul(qml_app, qt_app, tmp_path):
    window, loader, ikon = _betoltes_alatt(qml_app, qt_app, tmp_path)
    overlay = _item(window, "placesMapStatusOverlay")
    felirat = _item(window, "placesMapLoadingTitle")

    assert (felirat.width(), felirat.height()) == (213, 25)
    assert (ikon.width(), ikon.height()) == (64, 52)
    assert ikon.property("source").toString().endswith("assets/tools/loading_icon.png")

    # A térkép teteje a betöltő terület teteje; a spec y 117/153 értékei
    # a 28-as térkép-kezdettől 89 és 125 lefelé.
    assert _relativ(felirat, loader).y() == pytest.approx(117 - 28)
    assert _relativ(ikon, loader).y() == pytest.approx(153 - 28)

    # Vízszintesen a 264-es alap középen van (a QML egész pixelre kerekít);
    # az ikon az alap közepén ül, tehát a betöltő terület közepén is.
    alap_x = _js_kerekites((overlay.width() - ALAP_SZELESSEG) / 2)
    assert _relativ(felirat, overlay).x() == pytest.approx(alap_x + 27)
    assert _relativ(ikon, overlay).x() == pytest.approx(alap_x + 100)
    assert _relativ(ikon, overlay).x() + ikon.width() / 2 == pytest.approx(
        overlay.width() / 2, abs=0.5
    )


def test_ikon_kepponti_egyezese_a_renderelt_ablakon(qml_app, qt_app, tmp_path):
    window, _loader, _ikon = _betoltes_alatt(qml_app, qt_app, tmp_path)
    assert window.devicePixelRatio() == pytest.approx(1.0)

    png = QImage(str(IKON)).convertToFormat(QImage.Format.Format_ARGB32)
    assert (png.width(), png.height()) == (64, 52)
    kep = window.grabWindow()
    # A HELYET a spec adja (térkép-teteje + 125, az alap + 100), nem az elem
    # saját pozíciója: így a rossz hely a renderelt képen is megbukik.
    overlay = _item(window, "placesMapStatusOverlay")
    alap_x = _js_kerekites((overlay.width() - ALAP_SZELESSEG) / 2)
    origo = overlay.mapToScene(QPointF(0, 0))
    x0 = round(origo.x() + alap_x + 100)
    y0 = round(origo.y() + 125)

    egyezo = elteres = 0
    for y in range(png.height()):
        for x in range(png.width()):
            # A PySide az ARGB-t előjeles int-ként adja, ezért maszkolunk.
            if (png.pixel(x, y) & 0xFF000000) != 0xFF000000:
                continue
            if (kep.pixel(x0 + x, y0 + y) & 0xFFFFFF) == (png.pixel(x, y) & 0xFFFFFF):
                egyezo += 1
            else:
                elteres += 1

    assert elteres == 0, f"{elteres} képpont tér el a renderelt ikontól"
    assert egyezo > 2000, f"túl kevés átlátszatlan képpont: {egyezo}"
