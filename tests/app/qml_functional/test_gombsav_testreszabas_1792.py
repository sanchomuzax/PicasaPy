"""#1792 — a „Gombok konfigurálása…" párbeszéd és a fejléc együtt.

A jegy „Kész, ha" listáját őrzi: a menütétel valódi párbeszédet nyit, a
párbeszéd kétlistás, sorrendezhető, van alaphelyzet, a Mégse elvet, és a
fejléc TÉNYLEG eszerint épül fel — újraindítás után is.

⚠️ A `findChild` a `Repeater` delegáltjait nem találja meg, ezért a fejléc
négy gombja a helyén maradt, és a SORRENDET a vízszintes pozíció adja
(`gombX`). A próba ezért az `x` szerint olvassa ki a sorrendet — ez az,
amit a felhasználó is lát.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app.application as app_module
import pytest
from PySide6.QtCore import QObject, QSettings, QUrl
from PySide6.QtQml import QQmlComponent

from picasapy.app.gombsav_beallitas import ALAP_SORREND
from picasapy.app.gombsav_bridge import GombsavBridge

_KEEP_ALIVE: list = []


@pytest.fixture
def hid(tmp_path):
    return GombsavBridge(
        QSettings(str(tmp_path / "proba.ini"), QSettings.Format.IniFormat)
    )


def _fejlec(engine, hid, **props):
    engine.rootContext().setContextProperty("gombsav", hid)
    comp = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "LightboxHeader.qml")
        ),
    )
    _KEEP_ALIVE.append(comp)
    fejlec = comp.createWithInitialProperties(props)
    assert comp.errors() == [], comp.errors()
    assert fejlec is not None
    _KEEP_ALIVE.append(fejlec)
    return fejlec


def _parbeszed(engine, hid):
    engine.rootContext().setContextProperty("gombsav", hid)
    comp = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy"
                / "ConfigureButtonsDialog.qml")
        ),
    )
    _KEEP_ALIVE.append(comp)
    p = comp.create()
    assert comp.errors() == [], comp.errors()
    assert p is not None
    _KEEP_ALIVE.append(p)
    return p


def _lista(elem, nev: str) -> list[str]:
    """A QML `property var` tömbje Pythonban `QJSValue` — a
    `toVariant()` adja vissza listaként."""
    ertek = elem.property(nev)
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return [str(x) for x in (ertek or [])]


def _lathato_sorrend(fejlec) -> list[str]:
    """A fejléc gombjai BALRÓL JOBBRA — ahogy a felhasználó látja."""
    elemek = []
    for nev in ALAP_SORREND:
        gomb = fejlec.findChild(QObject, nev)
        assert gomb is not None, nev
        if gomb.property("visible"):
            elemek.append((gomb.property("x"), nev))
    return [nev for _, nev in sorted(elemek)]


class TestAMenutetel:
    def test_mar_nem_helyfoglalo(self):
        """A jegy első pontja: a menütétel valódi párbeszédet nyit."""
        menu = (
            Path(app_module.__file__).parent
            / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
        ).read_text(encoding="utf-8")

        assert 'text: qsTr("Configure Buttons..."); placeholder: true' not in menu
        assert "configureButtonsRequested()" in menu

    def test_a_gazda_megnyitja(self):
        fo = (
            Path(app_module.__file__).parent / "qml" / "Main.qml"
        ).read_text(encoding="utf-8")

        assert "onConfigureButtonsRequested: configureButtonsDialog.open()" in fo


class TestAFejlecKoveti:
    def test_alapbol_mind_a_negy_latszik(self, qml_app, hid):
        _, _, engine = qml_app

        fejlec = _fejlec(engine, hid, folderName="Nyaralás")

        assert _lathato_sorrend(fejlec) == list(ALAP_SORREND)

    def test_az_eltavolitott_gomb_ELTUNIK(self, qml_app, hid):
        """A jegy utolsó „Kész, ha" pontja."""
        _, _, engine = qml_app
        hid.mentsd([n for n in ALAP_SORREND if n != "headerCollageButton"])

        fejlec = _fejlec(engine, hid, folderName="Nyaralás")

        gomb = fejlec.findChild(QObject, "headerCollageButton")
        assert gomb is not None, "a gomb a fában marad, csak nem látszik"
        assert gomb.property("visible") is False
        assert "headerCollageButton" not in _lathato_sorrend(fejlec)

    def test_a_SORREND_is_kovet(self, qml_app, hid):
        _, _, engine = qml_app
        forditott = list(reversed(ALAP_SORREND))
        hid.mentsd(forditott)

        fejlec = _fejlec(engine, hid, folderName="Nyaralás")

        assert _lathato_sorrend(fejlec) == forditott

    def test_TULELI_az_ujrainditast(self, qml_app, hid, tmp_path):
        """A beállítás a tárolóból jön, nem a példány memóriájából: egy
        ÚJ híd ugyanazt a tárolót olvasva ugyanazt adja."""
        _, _, engine = qml_app
        hid.mentsd(["headerPlayButton"])

        ujraindult = GombsavBridge(
            QSettings(str(tmp_path / "proba.ini"), QSettings.Format.IniFormat)
        )
        fejlec = _fejlec(engine, ujraindult, folderName="Nyaralás")

        assert _lathato_sorrend(fejlec) == ["headerPlayButton"]


class TestAParbeszed:
    def test_ket_listaja_van(self, qml_app, hid):
        _, _, engine = qml_app
        p = _parbeszed(engine, hid)

        for nev in ("configButtonsAvailableList", "configButtonsCurrentList"):
            assert p.findChild(QObject, nev) is not None, nev

    def test_a_negy_muvelet_gombja_megvan(self, qml_app, hid):
        _, _, engine = qml_app
        p = _parbeszed(engine, hid)

        for nev in ("configButtonsAddButton", "configButtonsRemoveButton",
                    "configButtonsUpButton", "configButtonsDownButton",
                    "configButtonsResetButton"):
            assert p.findChild(QObject, nev) is not None, nev

    def test_az_eltavolitas_a_MUNKAPELDANYON_dolgozik(self, qml_app, hid, qt_app):
        """A Mégse akkor tud elvetni, ha a szerkesztés nem a tárolóban
        folyik — ezt méri: a lista változik, a tároló nem."""
        _, _, engine = qml_app
        p = _parbeszed(engine, hid)
        p.setProperty("jelenlegi", list(ALAP_SORREND))
        lista = p.findChild(QObject, "configButtonsCurrentList")
        lista.setProperty("currentIndex", 0)
        qt_app.processEvents()

        p.eltavolit()
        qt_app.processEvents()

        assert len(_lista(p, "jelenlegi")) == len(ALAP_SORREND) - 1
        assert hid.sorrend == list(ALAP_SORREND), "a tároló még érintetlen"

    def test_az_OK_ment(self, qml_app, hid, qt_app):
        _, _, engine = qml_app
        p = _parbeszed(engine, hid)
        p.setProperty("jelenlegi", ["headerPlayButton"])

        p.accept()
        qt_app.processEvents()

        assert hid.sorrend == ["headerPlayButton"]

    def test_a_MEGSE_elvet(self, qml_app, hid, qt_app):
        _, _, engine = qml_app
        p = _parbeszed(engine, hid)
        p.setProperty("jelenlegi", ["headerPlayButton"])

        p.reject()
        qt_app.processEvents()

        assert hid.sorrend == list(ALAP_SORREND)

    def test_a_mozgatas_sorrendet_valt(self, qml_app, hid, qt_app):
        _, _, engine = qml_app
        p = _parbeszed(engine, hid)
        p.setProperty("jelenlegi", list(ALAP_SORREND))
        p.findChild(QObject, "configButtonsCurrentList").setProperty(
            "currentIndex", 1
        )
        qt_app.processEvents()

        p.mozgat(-1)
        qt_app.processEvents()

        assert _lista(p, "jelenlegi")[0] == ALAP_SORREND[1]

    def test_az_alaphelyzet_visszaallit(self, qml_app, hid, qt_app):
        _, _, engine = qml_app
        p = _parbeszed(engine, hid)
        p.setProperty("jelenlegi", [])

        p.alaphelyzet()
        qt_app.processEvents()

        assert _lista(p, "jelenlegi") == list(ALAP_SORREND)
