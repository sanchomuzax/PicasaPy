"""#4177 — a Közzététel panel eredeti szövegei és buboréksúgói.

A súgó-próba a valódi `Main.qml` ablakban jeleníti meg a panelt. A feltöltési
ág ma nincs a főablakhoz kötve (a webes szolgáltatás nem cél), ezért a már
megépült panelcsoportot csak a próba idejére kapcsoljuk át. A kattintás és a
ráállás ettől még valódi, jelenet-koordinátás egérművelet.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, QMetaObject, QTranslator, Qt, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtTest import QTest

import picasapy.app

_APP_DIR = Path(picasapy.app.__file__).parent
_PANEL_FORRAS = (
    _APP_DIR / "qml" / "PicasaPy" / "PublishPanel.qml"
).read_text(encoding="utf-8")
_KEEP_ALIVE: list[QObject] = []

# `publish_text.tre` és a hivatalos magyar `tooltips.xml` alapján.
_SUGOK = {
    "publishUploadMode1": (
        1,
        "Selected folder and/or albums will be uploaded",
        "A program feltölti a kijelölt mappákat és/vagy albumokat",
    ),
    "publishUploadMode2": (
        2,
        "Selected folders and/or albums will be updated online with the options specified in the menus to the right",
        "A program a jobb oldali menükben választott opciókkal frissíti a kijelölt mappákat és/vagy albumokat az interneten",
    ),
    "publishUploadMode3": (
        3,
        "Selected folders and/or albums will be removed from Picasa Web Albums",
        "A program eltávolítja a kijelölt mappákat és/vagy albumokat a Picasa Webalbumokból",
    ),
}


def _elem(gyoker: QObject, nev: str) -> QObject:
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található a főablakban"
    return elem


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _tooltip_probe(engine, target: QObject) -> QObject:
    komponens = QQmlComponent(engine)
    komponens.setData(
        b"""import QtQuick
import QtQuick.Controls
Item {
    property var targetItem
    function attachedTip() {
        return targetItem ? targetItem.ToolTip.toolTip : null
    }
    readonly property bool tooltipVisible:
        attachedTip() ? attachedTip().visible : false
    readonly property string tooltipText:
        attachedTip() ? String(attachedTip().text) : ""
    readonly property string tooltipAttachedText:
        targetItem ? String(targetItem.ToolTip.text) : ""
    readonly property int tooltipDelay:
        attachedTip() ? attachedTip().delay : -1
}""",
        QUrl(),
    )
    assert komponens.isReady(), komponens.errors()
    probe = komponens.createWithInitialProperties({"targetItem": target})
    assert probe is not None, komponens.errors()
    _KEEP_ALIVE.extend((komponens, probe))
    return probe


def _feltoltesi_panel(window: QObject, qt_app):
    # A GiftCdHost a valódi Main.qml alján él. Az upload ág itt tesztelt,
    # de a termék menüje nem nyitja meg, mert a webes szolgáltatás nem cél.
    host = _elem(window, "giftCdHost")
    host.setProperty("nyitva", True)
    assert _varj(qt_app, lambda: host.isVisible()), "az Ajándék-CD panel nem látszik"
    panel = _elem(host, "publishPanel")
    panel.setProperty("uzemmod", "upload")
    assert _varj(
        qt_app,
        lambda: _elem(window, "publishReplicationGroup").isVisible(),
    ), "a feltöltési panelcsoport nem jelent meg"
    return host, panel


def _kattints(window, qt_app, elem: QObject) -> QPoint:
    assert elem.isVisible(), f"{elem.objectName()} nem látható"
    pont = elem.mapToScene(
        QPointF(elem.property("width") / 2, elem.property("height") / 2)
    ).toPoint()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(pont.x(), pont.y()),
    )
    qt_app.processEvents()
    return pont


def _sugo_megjelenit(window, qt_app, elem: QObject, probe: QObject, vart: str):
    QTest.mouseMove(window, QPoint(1, 1))
    qt_app.processEvents()
    pont = elem.mapToScene(
        QPointF(elem.property("width") / 2, elem.property("height") / 2)
    ).toPoint()
    QTest.mouseMove(window, pont)
    assert _varj(qt_app, lambda: elem.property("hovered") is True), (
        f"{elem.objectName()}: a mapToScene pont nem vitte az egeret a gombra; "
        f"pont={pont}, szöveg={probe.property('tooltipAttachedText')!r}"
    )
    assert _varj(qt_app, lambda: probe.property("tooltipVisible")), (
        f"{elem.objectName()}: a buboréksúgó nem jelent meg; "
        f"szöveg={probe.property('tooltipText')!r}, "
        f"attached={probe.property('tooltipAttachedText')!r}, pont={pont}"
    )
    assert probe.property("tooltipText") == vart
    QTest.mouseMove(window, QPoint(1, 1))
    assert _varj(qt_app, lambda: not probe.property("tooltipVisible")), (
        f"{elem.objectName()}: a buboréksúgó az egér elmozdítása után is látszik"
    )


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_a_feltoltesi_sugok_a_foablakban_kattinthatoak_es_megjelennek(
    qml_app, qt_app, magassageltolas
):
    window, _controller, engine = qml_app
    alapmagassag = window.height()
    window.setHeight(alapmagassag + magassageltolas)
    assert _varj(
        qt_app,
        lambda: window.height() == alapmagassag + magassageltolas,
    ), "a főablak nem vette fel a kért magasságot"
    window.requestActivate()
    assert _varj(qt_app, lambda: window.isActive()), "a főablak nem lett aktív"

    _host, panel = _feltoltesi_panel(window, qt_app)
    assert panel.property("feltoltesMod") == 1
    for nev, (mod, angol, _magyar) in _SUGOK.items():
        gomb = _elem(window, nev)
        pont = _kattints(window, qt_app, gomb)
        assert panel.property("feltoltesMod") == mod, (
            f"{nev}: a kattintás nem a(z) {mod}. módot választotta; pont={pont}"
        )
        probe = _tooltip_probe(engine, gomb)
        assert probe.property("tooltipDelay") == 600, (
            f"{nev}: a késleltetés nem a Theme.tooltipDelay értéke"
        )
        _sugo_megjelenit(window, qt_app, gomb, probe, angol)


def test_a_feliratok_es_a_sugok_hivatalos_magyarul_latszanak(
    qml_app, qt_app
):
    window, _controller, engine = qml_app
    gift_host = _elem(window, "giftCdHost")
    gift_host.setProperty("nyitva", True)
    assert _varj(qt_app, lambda: gift_host.isVisible())
    ajandek = _elem(window, "publishGiftCdText")
    assert ajandek.property("text").startswith(
        "The items selected with a checkmark above"
    )

    gift_host.setProperty("nyitva", False)
    backup_host = _elem(window, "backupHost")
    backup_host.setProperty("nyitva", True)
    assert _varj(qt_app, lambda: backup_host.isVisible())
    fejlec = _elem(window, "publishBackupCdHeader2")
    utmutato = _elem(window, "publishBackupText3")
    assert fejlec.property("text") == "Choose folders & albums to back up"
    assert utmutato.property("text").startswith("Check the folders you want to back up")

    translator = QTranslator(qt_app)
    assert translator.load("picasapy_hu", str(_APP_DIR / "i18n")), (
        "a magyar .qm nem tölthető be"
    )
    qt_app.installTranslator(translator)
    try:
        engine.retranslate()
        assert _varj(
            qt_app,
            lambda: fejlec.property("text")
            == "Mappák és albumok kijelölése biztonsági másolat készítéséhez",
        )
        assert ajandek.property("text") == (
            'A program a fent pipával kijelölt elemeket másolja az ajándék CD-re. '
            'További elemek felvételéhez kattintson az alábbi "Továbbiak '
            'hozzáadása" gombra.'
        )
        assert utmutato.property("text") == (
            'Jelölje ki azokat a mappákat, amelyekről biztonsági másolatot '
            'szeretne készíteni, vagy "Az összes kijelölése" gombra kattintva '
            'az összes elemet jelölje ki.'
        )

        gift_host.setProperty("nyitva", True)
        assert _varj(qt_app, lambda: gift_host.isVisible())
        panel = _elem(gift_host, "publishPanel")
        panel.setProperty("uzemmod", "upload")
        assert _varj(
            qt_app,
            lambda: _elem(window, "publishReplicationGroup").isVisible(),
        )
        for nev, (_mod, _angol, magyar) in _SUGOK.items():
            gomb = _elem(window, nev)
            probe = _tooltip_probe(engine, gomb)
            _sugo_megjelenit(window, qt_app, gomb, probe, magyar)

        QMetaObject.invokeMethod(
            window, "openContactSheetPrint", Qt.ConnectionType.DirectConnection
        )
        assert _varj(qt_app, lambda: _elem(window, "printDialog").isVisible())
        nyomatmeret = _elem(window, "printSizeBox")
        assert nyomatmeret.property("displayText") == "Indexképek"
    finally:
        qt_app.removeTranslator(translator)
        engine.retranslate()
