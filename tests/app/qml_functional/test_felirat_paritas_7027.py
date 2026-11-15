"""#7027 - a nézőbeli képaláírás-szerkesztés az eredeti Picasa szerint.

J1: a kuka gomb megerősítő kérdést nyit (`0x005f8c00`): a szöveg
`IDS_CONFIRM_CAPTION_TRASH`, az igen-gomb `IDS_CONFIRM_CAPTION_YES_BUTTON`,
a nem-gomb `il_No`, a cím `ytApp::ConfirmTitle`. Csak igenre törlődik a
felirat.

J2: a mezőn kívüli kattintás, a fókusz elvesztése és a szerkesztési kapuk
(képváltás, eszközmegnyitás, a néző bezárása, menü) a begépelt szöveget
mentik (`0x0067ed05-0x0067edaa` -> `0x005f89a0`); az Esc továbbra is elvet.

Minden próba valódi egérkattintást és valódi billentyűleütést használ; a
mentést a modellen, a JPEG IPTC-jén és a fájl bájtjain mérjük.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QMetaObject, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.metadata import read_file_metadata
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    gyerek,
    kattints,
    varj,
)
from tests.support.qt_wait import wait_for_photo_op

_KERDES = "Are you sure you want to delete the caption for this image?"
_RÉGI_NS = 1_000_000_000_000_000_000


def _mappa(controller) -> Path:
    return Path(str(controller.watchedFolders[0]))


def _felirat_beallit(controller, qt_app, sor: int, szoveg: str) -> None:
    wait_for_photo_op(
        controller, lambda: controller.setCaption(sor, szoveg), qt_app=qt_app
    )


def _nyisd_a_nezot(window, qt_app, sor: int = 0):
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    window.setProperty("viewerOpen", True)
    nezo = gyerek(window, "photoViewer")
    nezo.setProperty("currentIndex", sor)
    for _ in range(5):
        qt_app.processEvents()
    return nezo


def _gepelj(window, qt_app, szoveg: str) -> None:
    for karakter in szoveg:
        QTest.keyClick(window, Qt.Key(ord(karakter.upper())))
        qt_app.processEvents()


def _fokuszt_ad_a_mezonek(window, qt_app):
    mezo = gyerek(window, "captionField")
    kattints(window, qt_app, mezo)
    assert varj(qt_app, lambda: mezo.property("activeFocus") is True), (
        "a feliratmező a kattintás után nem kapott fókuszt"
    )
    return mezo


def _ures_kattintas(window, qt_app) -> None:
    """Valódi kattintás a felső sáv üres részén (a Vissza gomb és a lapozó
    sor között): nincs ott vezérlő, és nem kér fókuszt."""
    sav = gyerek(window, "viewerTopBar")
    pont = sav.mapToScene(QPointF(300, sav.height() / 2))
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont.toPoint()
    )
    qt_app.processEvents()


def _lenyomat(*utvonalak: Path) -> dict:
    """A fájlok tartalma, régire állított módosítási idővel: egy későbbi írás
    ettől megkülönböztethető (a durva kernel-időbélyeg két közeli írást
    azonosnak mutatna)."""
    ki = {}
    for utvonal in utvonalak:
        if utvonal.exists():
            os.utime(utvonal, ns=(_RÉGI_NS, _RÉGI_NS))
            ki[utvonal] = (utvonal.read_bytes(), utvonal.stat().st_mtime_ns)
    return ki


def _valtozatlan(lenyomat: dict) -> bool:
    return all(
        utvonal.exists()
        and utvonal.read_bytes() == bajtok
        and utvonal.stat().st_mtime_ns == ido
        for utvonal, (bajtok, ido) in lenyomat.items()
    )


def _kuka_kattintas(window, qt_app):
    kattints(window, qt_app, gyerek(window, "captionTrashButton"))
    parbeszed = gyerek(window, "captionTrashDialog")
    assert varj(qt_app, lambda: parbeszed.property("opened") is True), (
        "a kuka gomb nem nyitott megerősítő kérdést"
    )
    return parbeszed


class TestAKukaMegerositestKer:
    """J1: `0x005f8c00` - a törlés csak igenre fut le."""

    @staticmethod
    def _felirattal_nyitott_nezo(window, controller, qt_app):
        _felirat_beallit(controller, qt_app, 0, "Nyaralás")
        _nyisd_a_nezot(window, qt_app, 0)
        mezo = gyerek(window, "captionField")
        assert varj(qt_app, lambda: mezo.property("text") == "Nyaralás"), (
            "a próba feltétele: a felirat látszik a mezőben"
        )
        assert varj(
            qt_app,
            lambda: gyerek(window, "captionTrashButton").property("enabled") is True,
        )
        return mezo

    def test_a_kuka_a_hivatalos_kerdest_mutatja_es_meg_nem_torol(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        self._felirattal_nyitott_nezo(window, controller, qt_app)

        parbeszed = _kuka_kattintas(window, qt_app)

        assert gyerek(parbeszed, "captionTrashMessageLabel").property("text") == _KERDES
        assert (
            gyerek(parbeszed, "captionTrashYesButton").property("text")
            == "Delete Caption"
        )
        assert gyerek(parbeszed, "captionTrashNoButton").property("text") == "No"
        assert parbeszed.property("title") == "Confirm"
        assert controller.photos.captionAt(0) == "Nyaralás", (
            "a kérdés megjelenésekor a felirat már törlődött"
        )

    def test_a_nem_gomb_a_feliratot_a_jpeg_et_es_az_init_valtozatlanul_hagyja(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        mezo = self._felirattal_nyitott_nezo(window, controller, qt_app)
        mappa = _mappa(controller)
        elotte = _lenyomat(mappa / "a.jpg", mappa / ".picasa.ini")
        parbeszed = _kuka_kattintas(window, qt_app)

        kattints(window, qt_app, gyerek(parbeszed, "captionTrashNoButton"))

        assert varj(qt_app, lambda: parbeszed.property("opened") is False)
        assert controller.waitForBackgroundWorkers(30.0)
        qt_app.processEvents()
        assert mezo.property("text") == "Nyaralás"
        assert controller.photos.captionAt(0) == "Nyaralás"
        assert read_file_metadata(mappa / "a.jpg").caption == "Nyaralás"
        assert _valtozatlan(elotte), "a Nem gomb után a JPEG vagy az ini írásra került"

    def test_az_escape_is_nemet_jelent(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        self._felirattal_nyitott_nezo(window, controller, qt_app)
        mappa = _mappa(controller)
        elotte = _lenyomat(mappa / "a.jpg", mappa / ".picasa.ini")
        parbeszed = _kuka_kattintas(window, qt_app)

        QTest.keyClick(window, Qt.Key.Key_Escape)
        qt_app.processEvents()

        assert varj(qt_app, lambda: parbeszed.property("opened") is False)
        assert controller.waitForBackgroundWorkers(30.0)
        assert controller.photos.captionAt(0) == "Nyaralás"
        assert _valtozatlan(elotte)

    def test_a_kepfelirat_torlese_gomb_torli_a_feliratot_es_tiltottá_valik(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        mezo = self._felirattal_nyitott_nezo(window, controller, qt_app)
        mappa = _mappa(controller)
        parbeszed = _kuka_kattintas(window, qt_app)

        kattints(window, qt_app, gyerek(parbeszed, "captionTrashYesButton"))

        assert varj(qt_app, lambda: controller.photos.captionAt(0) == ""), (
            "az igen gomb nem törölte a feliratot"
        )
        assert varj(qt_app, lambda: mezo.property("text") == "")
        assert not read_file_metadata(mappa / "a.jpg").caption
        assert varj(
            qt_app,
            lambda: gyerek(window, "captionTrashButton").property("enabled") is False,
        ), "a törlés után a kuka gomb nem vált tiltottá"


class TestAFeliratMentodikFokuszvesztesnel:
    """J2: a begépelt szöveg a kapuknál és a fókuszvesztésnél mentődik."""

    def test_a_mezon_kivuli_kattintas_menti_a_szoveget(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _nyisd_a_nezot(window, qt_app, 0)
        mezo = _fokuszt_ad_a_mezonek(window, qt_app)
        _gepelj(window, qt_app, "kutya")
        assert varj(qt_app, lambda: mezo.property("text") == "kutya")

        _ures_kattintas(window, qt_app)

        assert varj(qt_app, lambda: controller.photos.captionAt(0) == "kutya"), (
            "a mezőn kívüli kattintás nem mentette a begépelt szöveget"
        )
        assert varj(
            qt_app,
            lambda: read_file_metadata(_mappa(controller) / "a.jpg").caption == "kutya",
        )

    def test_a_nezo_bezarasa_gepeles_utan_menti_a_szoveget(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _nyisd_a_nezot(window, qt_app, 0)
        _fokuszt_ad_a_mezonek(window, qt_app)
        _gepelj(window, qt_app, "macska")

        kattints(window, qt_app, gyerek(window, "viewerBackButton"))

        assert varj(qt_app, lambda: controller.photos.captionAt(0) == "macska"), (
            "a néző bezárása elvesztette a begépelt feliratot"
        )

    def test_az_eszkoz_megnyitasa_menti_a_szoveget(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _nyisd_a_nezot(window, qt_app, 0)
        _fokuszt_ad_a_mezonek(window, qt_app)
        _gepelj(window, qt_app, "lo")

        # a Vágás eszköz gombja nem kér fókuszt: csak a kapu viheti el a szöveget
        kattints(window, qt_app, gyerek(window, "editToolCrop"))

        assert varj(qt_app, lambda: controller.photos.captionAt(0) == "lo"), (
            "az eszköz megnyitása előtt a begépelt szöveg nem mentődött"
        )

    def test_a_menu_megnyitasa_menti_a_szoveget(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _nyisd_a_nezot(window, qt_app, 0)
        _fokuszt_ad_a_mezonek(window, qt_app)
        _gepelj(window, qt_app, "ember")

        _megnyit(window.property("menuBar"), qt_app, "&File")

        assert varj(qt_app, lambda: controller.photos.captionAt(0) == "ember"), (
            "a menü megnyitása előtt a begépelt szöveg nem mentődött"
        )

    def test_kepvaltas_a_regi_kepre_ment_es_az_uj_a_sajat_feliratat_mutatja(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _felirat_beallit(controller, qt_app, 1, "masodik")
        nezo = _nyisd_a_nezot(window, qt_app, 0)
        mezo = _fokuszt_ad_a_mezonek(window, qt_app)
        _gepelj(window, qt_app, "elso")
        assert varj(qt_app, lambda: mezo.property("text") == "elso")

        # a lapozás a mező fókuszának elvesztése nélkül is menti a szöveget
        QMetaObject.invokeMethod(nezo, "next", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        assert varj(qt_app, lambda: controller.photos.captionAt(0) == "elso"), (
            "a képváltás nem mentette a régi képre a begépelt szöveget"
        )
        assert varj(qt_app, lambda: mezo.property("text") == "masodik"), (
            "a következő kép mezője nem a saját feliratát mutatja"
        )
        assert controller.photos.captionAt(1) == "masodik", (
            "a begépelt szöveg a MÁSIK kép feliratát írta felül"
        )

    def test_a_lapozas_gomb_valodi_kattintassal_is_menti_a_regi_kepre(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _felirat_beallit(controller, qt_app, 1, "masodik")
        _nyisd_a_nezot(window, qt_app, 0)
        mezo = _fokuszt_ad_a_mezonek(window, qt_app)
        _gepelj(window, qt_app, "elso")

        kattints(window, qt_app, gyerek(window, "viewerNextButton"))

        assert varj(qt_app, lambda: controller.photos.captionAt(0) == "elso")
        assert varj(qt_app, lambda: mezo.property("text") == "masodik")
        assert controller.photos.captionAt(1) == "masodik"

    def test_az_escape_elveti_a_begepelt_szoveget(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _nyisd_a_nezot(window, qt_app, 0)
        mezo = _fokuszt_ad_a_mezonek(window, qt_app)
        mappa = _mappa(controller)
        elotte = _lenyomat(mappa / "a.jpg", mappa / ".picasa.ini")
        _gepelj(window, qt_app, "eldobott")
        assert varj(qt_app, lambda: mezo.property("text") == "eldobott")

        QTest.keyClick(window, Qt.Key.Key_Escape)
        qt_app.processEvents()
        # utána egy mezőn kívüli kattintás sem mentheti vissza
        _ures_kattintas(window, qt_app)

        assert varj(qt_app, lambda: mezo.property("text") == "")
        assert controller.waitForBackgroundWorkers(30.0)
        assert controller.photos.captionAt(0) == ""
        assert _valtozatlan(elotte), "az Esc után a fájl vagy az ini mégis íródott"

    def test_az_enter_ment_es_a_fokuszvesztes_nem_ir_masodszor(
        self, qml_app, qt_app
    ):
        import picasapy.app.photo_ops_write_text_mixin as modul

        window, controller, _engine = qml_app
        _nyisd_a_nezot(window, qt_app, 0)
        _fokuszt_ad_a_mezonek(window, qt_app)
        irasok = []
        eredeti = modul.write_iptc_caption

        def szamol(utvonal, szoveg):
            irasok.append(szoveg)
            return eredeti(utvonal, szoveg)

        modul.write_iptc_caption = szamol
        try:
            _gepelj(window, qt_app, "egyszer")
            QTest.keyClick(window, Qt.Key.Key_Return)
            assert varj(qt_app, lambda: controller.photos.captionAt(0) == "egyszer")
            _ures_kattintas(window, qt_app)
            assert controller.waitForBackgroundWorkers(30.0)
            qt_app.processEvents()
        finally:
            modul.write_iptc_caption = eredeti

        assert irasok == ["egyszer"], f"a fájlba {len(irasok)}-szor írt: {irasok}"

    def test_gepeles_nelkuli_fokuszvesztes_nem_ir(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _nyisd_a_nezot(window, qt_app, 0)
        mappa = _mappa(controller)
        elotte = _lenyomat(mappa / "a.jpg", mappa / ".picasa.ini")
        _fokuszt_ad_a_mezonek(window, qt_app)

        _ures_kattintas(window, qt_app)

        assert controller.waitForBackgroundWorkers(30.0)
        for _ in range(5):
            qt_app.processEvents()
        assert _valtozatlan(elotte), "gépelés nélkül is írásra került a fájl vagy az ini"
