"""#4449 — a két egyértelmű Általános felületi beállítás hatása kattintásra."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, QMetaObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtTest import QTest
from support.varakozas import var_feltetelre


_KEEP_ALIVE: list[QObject] = []


def _elem(gyoker: QObject, nev: str) -> QObject:
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _ablakmagassag(ablak: QObject, qt_app, elteres: int) -> None:
    alap = ablak.height()
    ablak.setHeight(alap + elteres)
    assert _varj(qt_app, lambda: ablak.height() == alap + elteres), (
        f"a főablak nem vette fel a {elteres:+d} px magasságeltolást"
    )


def _kattints(ablak: QObject, qt_app, elem: QObject) -> None:
    assert _varj(
        qt_app,
        lambda: elem.isVisible()
        and elem.property("width") > 0
        and elem.property("height") > 0,
    ), f"{elem.objectName()} nem látható vagy nincs mérete"
    pont = elem.mapToScene(
        QPointF(elem.property("width") / 2, elem.property("height") / 2)
    ).toPoint()
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(pont.x(), pont.y()),
    )
    qt_app.processEvents()


def _nyisd_meg_beallitasokat(ablak: QObject, qt_app) -> QObject:
    menu = _elem(ablak, "menuToolsOptions")
    QMetaObject.invokeMethod(menu, "triggered", Qt.ConnectionType.DirectConnection)
    assert _varj(
        qt_app,
        lambda: ablak.findChild(QObject, "optionsDialog") is not None
        and ablak.findChild(QObject, "optionsDialog").property("visible"),
    ), "a Beállítások párbeszédablak nem nyílt meg"
    return _elem(ablak, "optionsDialog")


def _zar_beallitasokat(ablak: QObject, qt_app, options: QObject) -> None:
    QMetaObject.invokeMethod(options, "close", Qt.ConnectionType.DirectConnection)
    assert _varj(
        qt_app,
        lambda: not ablak.findChild(QObject, "optionsDialog").property("visible"),
    ), "a Beállítások párbeszédablak nem zárult be"


def _tooltip_probe(engine, cel: QObject) -> QObject:
    komponens = QQmlComponent(engine)
    komponens.setData(
        b"""import QtQuick
import QtQuick.Controls
Item {
    property var targetItem
    readonly property bool latszik:
        targetItem && targetItem.ToolTip.toolTip
            ? targetItem.ToolTip.toolTip.visible : false
    readonly property bool engedelyezett:
        targetItem && targetItem.ToolTip.toolTip
            ? targetItem.ToolTip.toolTip.enabled : false
}""",
        QUrl(),
    )
    assert komponens.isReady(), komponens.errors()
    probe = komponens.createWithInitialProperties({"targetItem": cel})
    assert probe is not None, komponens.errors()
    _KEEP_ALIVE.extend((komponens, probe))
    return probe


@pytest.fixture
def szondak(qml_app, qt_app):
    """A szondák a QML-motor bontása ELŐTT válnak le a célról (#4871).

    A motor a lebontáskor valóban megszűnik; a cél nélkül maradt szonda
    `targetItem.ToolTip` kötése különben TypeError-t adna (#1260-as őr).
    """
    yield
    for obj in _KEEP_ALIVE:
        if obj.property("targetItem") is not None:
            obj.setProperty("targetItem", None)
        obj.deleteLater()
    _KEEP_ALIVE.clear()
    qt_app.processEvents()


def _kapcsold_at(ablak: QObject, qt_app, object_name: str) -> None:
    options = _nyisd_meg_beallitasokat(ablak, qt_app)
    checkbox = _elem(ablak, object_name)
    _kattints(options, qt_app, checkbox)
    _zar_beallitasokat(ablak, qt_app, options)


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_tooltip_kapcsolo_kattintasra_elrejti_es_visszahozza(
    qml_app, qt_app, szondak, magassageltolas
):
    ablak, controller, engine = qml_app
    _ablakmagassag(ablak, qt_app, magassageltolas)
    host = _elem(ablak, "giftCdHost")
    host.setProperty("nyitva", True)
    assert _varj(qt_app, lambda: host.isVisible()), "az Ajándék-CD panel nem nyílt meg"
    panel = _elem(host, "publishPanel")
    panel.setProperty("uzemmod", "upload")
    assert _varj(
        qt_app, lambda: _elem(ablak, "publishReplicationGroup").isVisible()
    ), "a feltöltési panelcsoport nem jelent meg"
    cel = _elem(ablak, "publishUploadMode1")
    probe = _tooltip_probe(engine, cel)

    assert controller.showTooltipsEnabled is True
    QTest.mouseMove(ablak, QPoint(1, 1))
    qt_app.processEvents()
    QTest.mouseMove(
        ablak,
        cel.mapToScene(
            QPointF(cel.property("width") / 2, cel.property("height") / 2)
        ).toPoint(),
    )
    assert _varj(qt_app, lambda: cel.property("hovered")), (
        "az egér nem érte el a buboréksúgó gombját"
    )
    assert _varj(qt_app, lambda: probe.property("latszik")), (
        "a bekapcsolt buboréksúgó nem jelent meg"
    )

    QTest.mouseMove(ablak, QPoint(1, 1))
    options = _nyisd_meg_beallitasokat(ablak, qt_app)
    checkbox = _elem(ablak, "optionsShowTooltipsCheck")
    assert checkbox.property("checked") is True
    _kattints(options, qt_app, checkbox)
    assert controller.showTooltipsEnabled is False
    assert probe.property("engedelyezett") is False
    _zar_beallitasokat(ablak, qt_app, options)

    QTest.mouseMove(
        ablak,
        cel.mapToScene(
            QPointF(cel.property("width") / 2, cel.property("height") / 2)
        ).toPoint(),
    )
    assert not _varj(qt_app, lambda: probe.property("latszik"), 0.9), (
        "a buboréksúgó a kikapcsolás után is megjelent"
    )

    QTest.mouseMove(ablak, QPoint(1, 1))
    _kapcsold_at(ablak, qt_app, "optionsShowTooltipsCheck")
    assert controller.showTooltipsEnabled is True
    QTest.mouseMove(
        ablak,
        cel.mapToScene(
            QPointF(cel.property("width") / 2, cel.property("height") / 2)
        ).toPoint(),
    )
    assert _varj(qt_app, lambda: probe.property("latszik")), (
        "a buboréksúgó a visszakapcsolás után nem jelent meg"
    )


def _figyeld_az_eltolast(viewer) -> list[float]:
    """A fiók-eltolás minden változása (#4449 — pelyhes volt Windowson).

    A korábbi őr 50 ms-onként mintavételezett, és lassú gépen két minta
    között az egész átmenet lefuthatott, így köztes értéket sosem látott.
    A változásjelzés minden animációs képkockán szól, tehát a köztes érték
    akkor is rögzül, ha a mintavétel lemaradna."""
    ertekek: list[float] = []
    viewer.editorDrawerOffsetChanged.connect(
        lambda: ertekek.append(viewer.property("editorDrawerOffset"))
    )
    return ertekek


def _volt_koztes(ertekek: list[float]) -> bool:
    return any(-279 < e < 0 for e in ertekek)


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_ui_atmenet_kapcsolo_ki_es_be_kattinthatoan_vezerli_a_fiok_atmenetet(
    qml_app, qt_app, magassageltolas
):
    ablak, controller, _engine = qml_app
    _ablakmagassag(ablak, qt_app, magassageltolas)
    ablak.setProperty("viewerOpen", True)
    assert _varj(
        qt_app,
        lambda: ablak.findChild(QObject, "photoViewer") is not None
        and ablak.findChild(QObject, "photoViewer").isVisible(),
    ), "a képnéző nem nyílt meg"
    viewer = _elem(ablak, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    fiok = _elem(ablak, "toggle_left_drawer")

    assert controller.uiTransitionsEnabled is True
    ertekek = _figyeld_az_eltolast(viewer)
    _kattints(ablak, qt_app, fiok)
    assert controller.editorControlsVisible is False, (
        "a szerkesztőfiók valódi gombja nem váltotta az állapotot"
    )
    assert _varj(
        qt_app,
        lambda: viewer.property("editorDrawerOffset") == -279,
    ), "a szerkesztőfiók átmenete nem ért véget"
    assert _volt_koztes(ertekek), (
        f"bekapcsolt átmenet mellett a szerkesztőfiók nem animálódott: {ertekek}"
    )

    _kapcsold_at(ablak, qt_app, "optionsUiTransitionsCheck")
    assert controller.uiTransitionsEnabled is False
    _kattints(ablak, qt_app, fiok)
    assert viewer.property("editorDrawerOffset") == 0

    _kapcsold_at(ablak, qt_app, "optionsUiTransitionsCheck")
    assert controller.uiTransitionsEnabled is True
    ertekek.clear()
    _kattints(ablak, qt_app, fiok)
    assert _varj(qt_app, lambda: _volt_koztes(ertekek)), (
        f"a visszakapcsolt átmenet nem indult el: {ertekek}"
    )
