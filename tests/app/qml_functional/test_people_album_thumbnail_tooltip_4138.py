"""#4138 — az Emberek-album indexképtételének súgója valódi menüben.

A súgó a `faceheaderpaneltext.xml` „Set as People Album Thumbnail”
szövegét használja. A kép helyi menüje külön felugró ablakban él, ezért a
rámutatást annak a QQuickWindow-jára küldjük, nem a főablakra.
"""

from __future__ import annotations

import time

from PySide6.QtCore import (
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    QTranslator,
    Qt,
    QUrl,
)
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlComponent
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from picasapy.ini import parse_document, update_document
import picasapy.app.application as app_module


_ANGOL = "Set as People Album Thumbnail"
_MAGYAR = "Beállítás az Emberek album indexképeként"
_SUGO_MAGYAR = "Beállítás indexképként az Emberek albumban"
_ARCOK_INI = (
    "[Contacts2]\n"
    "1111111111111111=Anna;;\n"
    "[a.jpg]\n"
    "faces=rect64(1e00280045006e00),1111111111111111\n"
)
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


def _elso_belyegkep_eger(ablak: QObject) -> QQuickItem:
    gyoker = ablak.contentItem()
    varakozo = [gyoker]
    talalatok: list[QQuickItem] = []
    while varakozo:
        elem = varakozo.pop()
        if (
            elem.objectName() == "thumbMouseArea"
            and elem.parentItem() is not None
            and elem.parentItem().property("index") == 0
        ):
            talalatok.append(elem)
        varakozo.extend(elem.childItems())
    assert len(talalatok) == 1, (
        "az első, kirajzolt fényképhez tartozó valódi egérterület nem egyértelmű: "
        f"{len(talalatok)} találat"
    )
    return talalatok[0]


def _buborek_proba(engine, cel: QObject) -> QObject:
    komponens = QQmlComponent(engine)
    komponens.setData(
        b"""import QtQuick
import QtQuick.Controls
Item {
    property var targetItem
    readonly property bool tooltipVisible:
        targetItem && targetItem.ToolTip.toolTip
            ? targetItem.ToolTip.toolTip.visible : false
    readonly property string tooltipText:
        targetItem && targetItem.ToolTip.toolTip
            ? String(targetItem.ToolTip.toolTip.text) : ""
    readonly property string attachedText:
        targetItem ? String(targetItem.ToolTip.text) : ""
    readonly property int tooltipDelay:
        targetItem && targetItem.ToolTip.toolTip
            ? targetItem.ToolTip.toolTip.delay : -1
}""",
        QUrl(),
    )
    assert komponens.isReady(), [hiba.toString() for hiba in komponens.errors()]
    proba = komponens.createWithInitialProperties({"targetItem": cel})
    assert proba is not None, [hiba.toString() for hiba in komponens.errors()]
    _KEEP_ALIVE.extend((komponens, proba))
    return proba


def _popup_ablak_proba(engine, menu: QObject) -> QObject:
    komponens = QQmlComponent(engine)
    komponens.setData(
        b"""import QtQuick
Item {
    property var targetMenu
    readonly property var popupWindow:
        targetMenu && targetMenu.contentItem
            ? targetMenu.contentItem.Window.window : null
    readonly property string popupTypeName:
        targetMenu ? String(targetMenu.popupType) : ""
}""",
        QUrl(),
    )
    assert komponens.isReady(), [hiba.toString() for hiba in komponens.errors()]
    proba = komponens.createWithInitialProperties({"targetMenu": menu})
    assert proba is not None, [hiba.toString() for hiba in komponens.errors()]
    _KEEP_ALIVE.extend((komponens, proba))
    return proba


def _menutetelt_megnyit(ablak: QObject, qt_app) -> tuple[QObject, QObject]:
    kep = _elso_belyegkep_eger(ablak)
    pont = kep.mapToScene(QPointF(kep.width() / 2, kep.height() / 2)).toPoint()
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(pont.x(), pont.y()),
    )
    menu = _gyerek(ablak, "photoContextMenu")
    tetel = ablak.findChild(QQuickItem, "contextMenuSetAsPeopleAlbumThumbnail")
    assert tetel is not None, "az indexkép-menütétel nem QQuickItem"
    assert _varj(
        qt_app,
        lambda: menu.property("visible") is True and tetel.isVisible(),
    ), (
        "a valódi jobb kattintás nem nyitotta meg az Emberek-album képmenüjét"
    )
    return menu, tetel


def test_a_sugo_a_felugro_menu_sajat_ablakaban_megjelenik(
    qml_app, qt_app, tmp_path
):
    ablak, vezerlo, engine = qml_app
    lib = tmp_path / "kepek"
    update_document(
        lib / ".picasa.ini",
        lambda _regi: parse_document(_ARCOK_INI),
        backup=False,
    )
    with open_index(tmp_path / "index.db") as kapcsolat:
        sync_tree(kapcsolat, lib)
    vezerlo._reload_after_sync()
    vezerlo.showPerson("Anna")
    assert _varj(qt_app, lambda: vezerlo.currentPersonName == "Anna"), (
        "az Emberek-nézet nem váltott Anna albumára"
    )

    fordito = QTranslator(qt_app)
    assert fordito.load("picasapy_hu", str(app_module._APP_DIR / "i18n")), (
        "a hivatalos magyar fordítás nem tölthető be"
    )
    qt_app.installTranslator(fordito)
    engine.retranslate()

    eredeti_magassag = ablak.height()
    try:
        for eltolás in (-5, 0, 5):
            ablak.setHeight(eredeti_magassag + eltolás)
            assert _varj(
                qt_app,
                lambda eltolás=eltolás: ablak.height()
                == eredeti_magassag + eltolás,
            ), f"a főablak magassága nem állt be ({eltolás:+} px)"

            menu, tetel = _menutetelt_megnyit(ablak, qt_app)
            assert tetel.property("text") == _MAGYAR

            popup_proba = _popup_ablak_proba(engine, menu)
            popup = popup_proba.property("popupWindow")
            assert isinstance(popup, QQuickWindow), (
                "a Menü contentItem.Window.window nem adott QQuickWindow-t; "
                f"popupType={popup_proba.property('popupTypeName')!r}, "
                f"contentItem.window={menu.property('contentItem').window()!r}, "
                f"item.window={tetel.window()!r}"
            )
            assert popup.winId() != ablak.winId(), (
                "a Menü contentItem.Window.window nem külön popup ablak"
            )

            proba = _buborek_proba(engine, tetel)
            assert proba.property("tooltipDelay") == 600, (
                "a súgó nem a mért Theme.tooltipDelay késleltetést használja"
            )

            popup.requestActivate()
            assert _varj(qt_app, lambda popup=popup: popup.isActive()), (
                "a menü saját popup ablaka nem vált aktívvá"
            )
            QTest.mouseMove(popup, QPoint(1, 1), 10)
            qt_app.processEvents()
            kozep = tetel.mapToScene(
                QPointF(tetel.width() / 2, tetel.height() / 2)
            ).toPoint()
            QTest.mouseMove(popup, kozep, 10)
            assert _varj(
                qt_app, lambda tetel=tetel: tetel.property("hovered") is True
            ), (
                "a popup ablakára küldött QTest.mouseMove nem érte el a menüpontot; "
                f"hoverEnabled={tetel.property('hoverEnabled')!r}, "
                f"pont={kozep}, popup={popup.size()}"
            )
            assert _varj(
                qt_app, lambda proba=proba: proba.property("tooltipVisible")
            ), (
                "a buboréksúgó nem jelent meg a menü saját ablakán; "
                f"attached={proba.property('attachedText')!r}, "
                f"hovered={tetel.property('hovered')!r}"
            )
            assert proba.property("tooltipText") == _SUGO_MAGYAR
            assert proba.property("attachedText") == _SUGO_MAGYAR

            QTest.mouseMove(popup, QPoint(1, 1), 10)
            assert _varj(
                qt_app, lambda proba=proba: not proba.property("tooltipVisible")
            ), (
                "a buboréksúgó az egér elmozdítása után is látható maradt"
            )
            QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
            assert _varj(
                qt_app, lambda menu=menu: menu.property("visible") is False
            ), (
                "a próba végén nem záródott be a helyi menü"
            )
    finally:
        qt_app.removeTranslator(fordito)
        engine.retranslate()
        ablak.setHeight(eredeti_magassag)
