"""#4527: a tálca ★ gombjának súgója a ★ fölött jelenik meg, nem a More… fölött.

A hibás kötés: a `ToolTip.visible` a `trayMoreBtn.hovered`-re volt kötve, így
a súgó a ★ fölött soha nem jött, a More… fölé húzva viszont a ★ mellett villant.

A teszt VALÓDI egérmozgatással méri (QTest.mouseMove a főablakon). A súgó
állapotát a gomb SAJÁT csatolt `ToolTip.visible`-jéről olvassa: a Qt a
felugró-ablakot a gombok között megosztja, ezért a látszó buborék szövegéből
nem lehet megmondani, melyik gombé.
A mérés három magasságon fut (−5 / 0 / +5 px), szűk ablakban, ahol a
More… gomb látszik (ahogy a #4537 tesztje is teszi).
"""

from __future__ import annotations

import time

from PySide6.QtCore import (
    Q_ARG,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    QTranslator,
    Qt,
    QUrl,
)
from PySide6.QtQml import QQmlComponent
from PySide6.QtTest import QTest

import picasapy.app.application as app_module

_MAGYAR_CSILLAG_SUGO = "Csillag hozzáadása/eltávolítása"
_SZUK_SZELESSEG = 400
_KEEP_ALIVE: list[QObject] = []


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _gyerek(ablak: QObject, nev: str) -> QObject:
    elem = ablak.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található a főablakban"
    return elem


def _sugo_proba(engine, cel: QObject) -> QObject:
    """A `cel` gomb SAJÁT súgója: látszik-e (`ToolTip.visible`), és mi a szövege."""
    komponens = QQmlComponent(engine)
    komponens.setData(
        b"""import QtQuick
import QtQuick.Controls
Item {
    property var targetItem
    readonly property bool sugoLathato:
        targetItem ? targetItem.ToolTip.visible : false
    readonly property string sugoSzoveg:
        targetItem ? String(targetItem.ToolTip.text) : ""
}""",
        QUrl(),
    )
    assert komponens.isReady(), [hiba.toString() for hiba in komponens.errors()]
    proba = komponens.createWithInitialProperties({"targetItem": cel})
    assert proba is not None, [hiba.toString() for hiba in komponens.errors()]
    _KEEP_ALIVE.extend((komponens, proba))
    return proba


def _ratolyt_ratesz(ablak, qt_app, elem: QObject) -> None:
    """Az egeret előbb kiviszi a sarokba, majd az elem közepére viszi."""
    QTest.mouseMove(ablak, QPoint(1, 1), 10)
    qt_app.processEvents()
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseMove(ablak, pont.toPoint(), 10)


def _egyes_kijeloles(ablak, qt_app) -> None:
    QMetaObject.invokeMethod(
        ablak,
        "handleThumbClick",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 0),
        Q_ARG("QVariant", 0),
    )
    qt_app.processEvents()


def test_a_csillag_folott_a_csillag_sugoja_jelenik_meg_a_more_folott_nem(
    qml_app, qt_app
):
    ablak, _vezerlo, engine = qml_app
    _egyes_kijeloles(ablak, qt_app)
    ablak.requestActivate()
    assert QTest.qWaitForWindowActive(ablak, 3000), "a főablak nem lett aktív"
    # A More… gomb csak akkor látszik, ha van kiszorult tálcagomb: szűk ablak kell.
    ablak.setWidth(_SZUK_SZELESSEG)
    qt_app.processEvents()

    csillag = _gyerek(ablak, "trayStarButton")
    more = _gyerek(ablak, "trayMoreButton")
    assert csillag.property("enabled") is True, "a ★ gomb nincs engedélyezve"
    # Az offscreen platform alapból `hoverEnabled: false`-t ad a Button-okra;
    # a valódi képernyőn a hover él (a jegy is így írja le). A tesztben ezért
    # a két gombon bekapcsoljuk, hogy a valódi egérmozgás eljusson a `hovered`-ig.
    csillag.setProperty("hoverEnabled", True)
    more.setProperty("hoverEnabled", True)

    fordito = QTranslator(qt_app)
    assert fordito.load("picasapy_hu", str(app_module._APP_DIR / "i18n")), (
        "a hivatalos magyar fordítás nem tölthető be"
    )
    qt_app.installTranslator(fordito)
    try:
        engine.retranslate()
        csillag_sugo = _sugo_proba(engine, csillag)
        more_sugo = _sugo_proba(engine, more)

        eredeti_magassag = ablak.height()
        for eltolas in (-5, 0, 5):
            ablak.setHeight(eredeti_magassag + eltolas)
            assert _varj(
                qt_app,
                lambda eltolas=eltolas: ablak.height()
                == eredeti_magassag + eltolas,
            ), f"a főablak magassága nem állt be ({eltolas:+} px)"

            _ratolyt_ratesz(ablak, qt_app, csillag)
            assert _varj(
                qt_app, lambda: csillag.property("hovered") is True
            ), f"a ★ gombot nem érte el az egér ({eltolas:+} px)"
            assert _varj(
                qt_app, lambda: csillag_sugo.property("sugoLathato") is True
            ), f"a ★ fölött nem jelent meg a súgó ({eltolas:+} px)"
            assert csillag_sugo.property("sugoSzoveg") == _MAGYAR_CSILLAG_SUGO

            _ratolyt_ratesz(ablak, qt_app, more)
            assert _varj(
                qt_app, lambda: more.property("hovered") is True
            ), f"a More… gombot nem érte el az egér ({eltolas:+} px)"
            assert _varj(
                qt_app, lambda: more_sugo.property("sugoLathato") is True
            ), f"a More… fölött nem jelent meg a saját súgója ({eltolas:+} px)"
            # A ★ súgója a már elhagyott gombról lassan záródik (kilépő
            # átmenet), ezért a várakozás a mérce, nem az azonnali állapot.
            assert _varj(
                qt_app,
                lambda: csillag_sugo.property("sugoLathato") is False,
            ), f"a More… fölött a ★ súgója is látszik ({eltolas:+} px)"
    finally:
        qt_app.removeTranslator(fordito)
