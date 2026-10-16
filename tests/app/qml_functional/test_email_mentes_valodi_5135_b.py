"""A maradék „egyéb" tételei VALÓDI egérkattintással (#5135, 4. rész, b).

Az első fájl (`test_email_mentes_valodi_5135.py`) az E-mail és a Mentés
tételeit viszi; ez a fájl a többit, ugyanazzal a mintával:

- `publishUploadModeLabelClick1/2/3` - a feltöltési mód címkéi (MouseArea):
  a címkére kattintás átállítja a panel módját (1/2/3);
- `batchEditPanelCancel` - a köteges szerkesztés Mégse: a megszakítás jele;
- `openWithCancelButton` - az „Open With" Mégse: bezárul, nem nyit meg semmit;
- `initialScanContinue` - az első keresés Folytatás: alkalmazza a választást
  és bezárul (a `applyInitialScan` a Python-oldali helyettesítő);
- `revertCancelButton` - a visszaállítás megerősítésének Mégse: bezárul,
  és nem fut le a visszaállítás (a `revertRowsToOriginal` helyettesítője).

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated`
hívás és nincs `.emit()` a tesztelt vezérlőkön. A párbeszédek megnyitása
(állapot-előkészítés) a `open` hívás; a tesztelt műveletet a kattintás
indítja. A takarításban `close` szabad.

Nincs teszt: a `batchEditPanelCancel` kattintása a `cancelRequested` jelet
bocsátja ki, a Main-beli bekötést (`controller.cancelBatchEdit()`) ez a
standalone panel-teszt nem látja.
"""

from __future__ import annotations

import picasapy.app.application as app_module
import pytest
from conftest import _build_qml_app
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QSignalSpy, QTest

from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._fomenu_4420_menu import _megnyit

_KEEP_ALIVE: list = []


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _gyerek(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(window, qt_app, elem) -> None:
    assert elem.property("visible") is True, f"{elem.objectName()} nem látszik"
    assert elem.property("enabled") is True, f"{elem.objectName()} tiltott"
    pont = elem.mapToScene(
        QPointF(elem.property("width") / 2, elem.property("height") / 2)
    ).toPoint()
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def _zar(qt_app, objektum) -> None:
    QMetaObject.invokeMethod(objektum, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _nyit(qt_app, objektum) -> None:
    """Állapot-előkészítés: a párbeszéd megnyitása (nem a tesztelt művelet)."""
    QMetaObject.invokeMethod(objektum, "open", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


@pytest.fixture(scope="module")
def motor(qt_app):
    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _komponens_ablak(motor, qt_app, qml_fajl: str, tulajdonsagok: dict | None = None):
    """Egy QML-komponens a saját ablakában, `betolto.item` aliasszal."""
    url = QUrl.fromLocalFile(str(app_module._APP_DIR / "qml" / "PicasaPy" / qml_fajl))
    qml = f"""import QtQuick
import QtQuick.Window
Window {{
    width: 1024
    height: 420
    visible: true
    Loader {{
        id: betolto
        anchors.fill: parent
        source: "{url.toString()}"
    }}
    property alias panel: betolto.item
}}"""
    comp = QQmlComponent(motor)
    comp.setData(qml.encode(), QUrl())
    ablak = comp.create()
    assert comp.errors() == [], comp.errors()
    assert ablak is not None
    panel = ablak.property("panel")
    assert panel is not None, f"a(z) {qml_fajl} nem töltődött be"
    for kulcs, ertek in (tulajdonsagok or {}).items():
        panel.setProperty(kulcs, ertek)
    _KEEP_ALIVE.extend((comp, ablak, panel))
    qt_app.processEvents()
    return ablak, panel


# --------------------------------------------- Feltöltési mód címkéi

@pytest.fixture
def publish_ablak(motor, qt_app):
    ablak, panel = _komponens_ablak(
        motor, qt_app, "PublishPanel.qml", {"uzemmod": "upload"}
    )
    yield ablak, panel
    ablak.close()
    qt_app.processEvents()


class TestFeltoltesiModCimkek:
    def test_a_masodik_cimke_valodi_kattintassal_a_2_modra_all_at(
        self, publish_ablak, qt_app
    ):
        ablak, panel = publish_ablak
        assert panel.property("feltoltesMod") == 1, "a próba feltétele: 1-es mód"

        _kattints(ablak, qt_app, _gyerek(ablak, "publishUploadModeLabelClick2"))

        assert panel.property("feltoltesMod") == 2, (
            "a 2. címke kattintása nem állította a 2. módra"
        )

    def test_a_harmadik_cimke_valodi_kattintassal_a_3_modra_all_at(
        self, publish_ablak, qt_app
    ):
        ablak, panel = publish_ablak
        assert panel.property("feltoltesMod") == 1, "a próba feltétele: 1-es mód"

        _kattints(ablak, qt_app, _gyerek(ablak, "publishUploadModeLabelClick3"))

        assert panel.property("feltoltesMod") == 3, (
            "a 3. címke kattintása nem állította a 3. módra"
        )

    def test_az_elso_cimke_valodi_kattintassal_visszaallitja_az_1_modot(
        self, publish_ablak, qt_app
    ):
        ablak, panel = publish_ablak
        _kattints(ablak, qt_app, _gyerek(ablak, "publishUploadModeLabelClick3"))
        assert panel.property("feltoltesMod") == 3, "a próba feltétele: 3-as mód"

        _kattints(ablak, qt_app, _gyerek(ablak, "publishUploadModeLabelClick1"))

        assert panel.property("feltoltesMod") == 1, (
            "az 1. címke kattintása nem állította az 1. módra"
        )


# ------------------------------------------------- Köteges szerkesztés

class TestKotegesSzerkesztes:
    def test_a_megse_valodi_kattintassal_jelzi_a_megszakitast(self, motor, qt_app):
        ablak, panel = _komponens_ablak(
            motor, qt_app, "BatchEditProgressPanel.qml",
            {"folderName": "fotok", "doneCount": 1, "totalCount": 4},
        )
        jelzes = QSignalSpy(panel.cancelRequested)
        try:
            assert jelzes.count() == 0
            _kattints(ablak, qt_app, _gyerek(panel, "batchEditPanelCancel"))

            assert jelzes.count() == 1, (
                "a Mégse kattintás nem jelezte a megszakítást"
            )
        finally:
            ablak.close()
            qt_app.processEvents()


# ------------------------------------------------------- Megnyitás más

class TestMegnyitasMas:
    def test_a_megse_valodi_kattintassal_bezarja_es_nem_nyit_meg_semmit(
        self, motor, qt_app
    ):
        ablak, panel = _komponens_ablak(
            motor, qt_app, "OpenWithDialog.qml", {"photoPath": "/nincs/kep.jpg"},
        )
        _nyit(qt_app, panel)
        assert _varj(qt_app, lambda: panel.property("opened") is True), (
            "a próba feltétele: a párbeszédnek nyitva kell lennie"
        )
        elfogadva = QSignalSpy(panel.accepted)

        try:
            _kattints(ablak, qt_app, _gyerek(panel, "openWithCancelButton"))

            assert _varj(qt_app, lambda: panel.property("opened") is False), (
                "az Open With Mégse nem zárta be a párbeszédet"
            )
            assert elfogadva.count() == 0, "a Mégse mégis elfogadta a párbeszédet"
        finally:
            ablak.close()
            qt_app.processEvents()


# ----------------------------------------------------- Első keresés

@pytest.fixture
def app_ablak(qt_app, tmp_path):
    for window, controller, engine in _build_qml_app(qt_app, tmp_path):
        window.show()
        window.requestActivate()
        qt_app.processEvents()
        yield window, controller, engine


class TestElsoKereses:
    def test_a_folytatas_valodi_kattintassal_alkalmazza_a_valasztast_es_zar(
        self, app_ablak, qt_app, monkeypatch
    ):
        window, controller, _engine = app_ablak
        hivasok: list[str] = []
        monkeypatch.setattr(
            type(controller), "applyInitialScan",
            lambda self, choice: hivasok.append(choice), raising=False,
        )
        parbeszed = _gyerek(window, "initialScanDialog")
        parbeszed.setProperty("migrationStep", False)
        parbeszed.setProperty("updateChosen", False)
        parbeszed.setProperty("choice", "narrow")
        _nyit(qt_app, parbeszed)
        assert _varj(qt_app, lambda: parbeszed.property("opened") is True), (
            "a próba feltétele: az első keresés párbeszédének nyitva kell lennie"
        )

        _kattints(window, qt_app, _gyerek(parbeszed, "initialScanContinue"))

        assert hivasok == ["narrow"], (
            "a Folytatás nem alkalmazta a választott keresési módot"
        )
        assert _varj(qt_app, lambda: parbeszed.property("opened") is False), (
            "a Folytatás nem zárta be az első keresés párbeszédét"
        )


# ------------------------------------------------------ Visszaállítás

class TestVisszaallitasMegerosites:
    def test_a_megse_valodi_kattintassal_bezarja_es_nem_allitja_vissza(
        self, app_ablak, qt_app, monkeypatch
    ):
        window, controller, _engine = app_ablak
        visszaallitott: list = []
        monkeypatch.setattr(
            type(controller), "revertRowsToOriginal",
            lambda self, rows: visszaallitott.append(rows), raising=False,
        )
        # Állapot-előkészítés: a „Visszaállítás" csak mentett képnél él, ezért
        # a mentettség-lekérdezést igennek mutatjuk. A menüpontot és a
        # párbeszédet már valódi kattintás nyitja.
        monkeypatch.setattr(
            type(controller), "hasSavedBackup", lambda self, rows: True,
            raising=False,
        )
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()

        menu_bar = window.property("menuBar")
        _megnyit(menu_bar, qt_app, "&File")
        _kattints(window, qt_app, _gyerek(window, "menuFileRevert"))
        parbeszed = _gyerek(window, "revertConfirmDialog")
        assert _varj(qt_app, lambda: parbeszed.property("opened") is True), (
            "a Fájl ▸ Revert kattintás nem nyitotta meg a visszaállítás megerősítését"
        )

        _kattints(window, qt_app, _gyerek(parbeszed, "revertCancelButton"))

        assert _varj(qt_app, lambda: parbeszed.property("opened") is False), (
            "a visszaállítás Mégse nem zárta be a megerősítést"
        )
        assert visszaallitott == [], "a Mégse mégis visszaállított fájlokat"
