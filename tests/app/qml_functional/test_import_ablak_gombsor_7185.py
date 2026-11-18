"""#7185: az importpanel alsó gombsora látható közeli főablak-méreteken."""

from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.varakozas import var_feltetelre

_GOMBOK = (
    "importSourceStartButton",
    "importSourceSelectedButton",
    "importSourceCloseButton",
)


def _bejar(gyoker):
    yield gyoker
    if hasattr(gyoker, "childItems"):
        for gyermek in gyoker.childItems():
            yield from _bejar(gyermek)


def _elem(gyoker, nev: str):
    talalat = gyoker.findChild(QObject, nev)
    if talalat is None:
        talalat = next((i for i in _bejar(gyoker) if i.objectName() == nev), None)
    assert talalat is not None, f"{nev} nem található"
    return talalat


def _kattint(ablak, elem, qt_app) -> None:
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        elem.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _gombok_az_ablakban(ablak) -> None:
    for nev in _GOMBOK:
        gomb = _elem(ablak, nev)
        also = gomb.mapToItem(ablak, QPointF(0, gomb.height())).y()
        assert gomb.property("visible") is True, f"{nev} rejtett"
        assert also <= ablak.height(), (
            f"{nev} alsó éle ({also:.0f}) kilóg az {ablak.height()} magas panelből"
        )


def test_a_gombsor_alapmeretben_es_kozeli_ablakmagassagokon_latszik(qml_app, qt_app):
    fo, _vezerlo, _engine = qml_app
    fo.resize(1280, 800)
    fo.show()
    qt_app.processEvents()
    _kattint(fo, _elem(fo, "toolbarImportButton"), qt_app)
    ablak = _elem(fo, "importSourceDialog")
    assert var_feltetelre(qt_app, lambda: ablak.property("visible"), 10)
    qt_app.processEvents()

    eredeti_magassag = fo.height()
    for elteres in (-5, 0, 5):
        fo.setProperty("height", eredeti_magassag + elteres)
        qt_app.processEvents()
        _gombok_az_ablakban(ablak)

    # a Close valódi kattintással elérhető, és bezárja az ablakot
    _kattint(ablak, _elem(ablak, "importSourceCloseButton"), qt_app)
    assert var_feltetelre(qt_app, lambda: not ablak.property("visible"), 5)
