"""Az „Egyéb" tételei VALÓDI egérkattintással (#5150, 10. rész, 2. fájl).

Adatbázis-áthelyezés, a Beállítások párbeszéd fülsora és bezárása, valamint
az E-mail fül. Minden tétel valódi `QTest.mouseClick`-kel indul; a hatást a
párbeszéd és a vezérlő állapotán mérjük.

Lefedve:
- `MoveDatabaseDialog` (Eszközök ▸ Experimental ▸ Move Database…): a
  `moveDatabaseDefaultButton`, `moveDatabaseMoveButton`,
  `moveDatabaseUndoScheduleButton`, `moveDatabaseCloseButton`. A költözés
  vezérlőjét helyettesítjük: a valódi a felhasználó gépén rögzítené a
  következő indulásra szóló költözést; a teszt ezt nem engedi.
- `OptionsDialog`: a fülsor öt fülének (`optionsTabGeneral`, `optionsTabEmail`,
  `optionsTabNetwork`, `optionsTabWebAlbums`, `optionsTabNameTags`), a
  `optionsCloseButton`-nek és a fülsor két nyilának (`optionsTabScrollLeftButton`,
  `optionsTabScrollRightButton`) a kattintása.
- `OptionsTabEmail`: `optionsMailChooseRadio`, `optionsMailDefaultRadio`,
  `optionsMailSingleSameRadio`, `optionsMailSingleOriginalRadio`; a tiltott
  `optionsMailGoogleRadio` és `optionsMailUseHtmlCheck` nem vált.

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated`
hívás és nincs `.emit()`. A párbeszédek takarításához a `close` hívás szabad.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, Property, QObject, Signal, Slot

from conftest import _build_qml_app
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135 import (
    _almenu_megnyitasa,
    _menupont_kattintasa,
)
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
    _gyerek,
    _keszits_konyvtarat,
    _klikk_ablakban,
    _latszik,
    _varj,
    _zar,
)


@pytest.fixture
def parbeszed_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
    )


@pytest.fixture
def email_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
        email_vezerlo=True,
    )


class _FakeRelocate(QObject):
    """A költözés-vezérlő helyettesítője: a valódi a következő indulásra rögzítené a költözést."""

    relocateScheduled = Signal(str)  # noqa: N815 - a QML-oldal neve
    relocateFailed = Signal(str)  # noqa: N815

    def __init__(self, aktualis: str) -> None:
        super().__init__()
        self._aktualis = aktualis
        self.inditasok: list[str] = []
        self.visszavonasok = 0

    @Property(str)
    def currentLocation(self) -> str:  # noqa: N802 - QML-tulajdonság
        return self._aktualis

    @Slot(str)
    def startRelocate(self, uj: str) -> None:  # noqa: N802 - QML-hívás
        self.inditasok.append(uj)

    @Slot()
    def cancelScheduledRelocate(self) -> None:  # noqa: N802 - QML-hívás
        self.visszavonasok += 1


def _athelyezes_megnyit(window, qt_app, engine, tmp_path: Path):
    """Eszközök ▸ Experimental ▸ Move Database… valódi kattintásokkal.

    Visszaadja a párbeszédet és a helyettesítő költözés-vezérlőt. A vezérlőt a
    párbeszéd megnyitása ELŐTT kell bekötni: a párbeszéd a betöltéskor olvassa.
    """
    fake = _FakeRelocate(str(tmp_path / "jelenlegi"))
    engine.rootContext().setContextProperty("relocateController", fake)
    menu_bar = window.property("menuBar")
    menu = _megnyit(menu_bar, qt_app, "&Tools")
    _almenu_megnyitasa(menu_bar, qt_app, menu, "Experimental")
    _menupont_kattintasa(window, qt_app, "menuToolsMoveDatabase")
    assert _varj(qt_app, lambda: _latszik(window, "moveDatabaseDialog")), (
        "az Eszközök ▸ Experimental ▸ Move Database nem nyitotta meg a párbeszédet"
    )
    return _gyerek(window, "moveDatabaseDialog"), fake


class TestAdatbazisAthelyezes:
    def test_alapertek_valodi_kattintassal_a_jelenlegi_helyet_irja_be(
        self, parbeszed_app, qt_app, tmp_path
    ):
        window, controller, engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog, fake = _athelyezes_megnyit(window, qt_app, engine, tmp_path)
        assert dialog.property("newLocation") == "", "a próba feltétele: nincs új hely"

        _klikk_ablakban(qt_app, dialog, _gyerek(dialog, "moveDatabaseDefaultButton"))

        assert _varj(
            qt_app, lambda: dialog.property("newLocation") == fake.currentLocation
        ), "az Alapértelmezett kattintás nem a jelenlegi helyet írta be"
        _zar(qt_app, dialog)

    def test_athelyezes_gomb_valodi_kattintassal_az_uj_helyet_adja_at(
        self, parbeszed_app, qt_app, tmp_path
    ):
        window, controller, engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog, fake = _athelyezes_megnyit(window, qt_app, engine, tmp_path)
        gomb = _gyerek(dialog, "moveDatabaseMoveButton")
        assert gomb.property("enabled") is False, "új hely nélkül a Mozgatás tiltott"
        _klikk_ablakban(qt_app, dialog, _gyerek(dialog, "moveDatabaseDefaultButton"))
        assert _varj(qt_app, lambda: gomb.property("enabled") is True)

        _klikk_ablakban(qt_app, dialog, gomb)

        assert _varj(qt_app, lambda: len(fake.inditasok) == 1), (
            "a Mozgatás kattintás nem adta át a költözésnek az új helyet"
        )
        assert Path(fake.inditasok[0]) == Path(fake.currentLocation)
        _zar(qt_app, dialog)

    def test_a_visszavonas_gomb_valodi_kattintassal_visszavonja_az_elojegyzest(
        self, parbeszed_app, qt_app, tmp_path
    ):
        window, controller, engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog, fake = _athelyezes_megnyit(window, qt_app, engine, tmp_path)
        gomb = _gyerek(dialog, "moveDatabaseUndoScheduleButton")
        assert gomb.property("visible") is False, "előjegyzés nélkül nincs visszavonás"
        # előkészítés: van előjegyzett költözés (a párbeszéd saját állapota)
        dialog.setProperty("scheduledLocation", str(tmp_path / "uj"))
        assert _varj(qt_app, lambda: gomb.property("visible") is True)

        _klikk_ablakban(qt_app, dialog, gomb)

        assert _varj(qt_app, lambda: fake.visszavonasok == 1), (
            "a Visszavonás kattintás nem hívta a költözés visszavonását"
        )
        assert _varj(qt_app, lambda: dialog.property("scheduledLocation") == "")
        _zar(qt_app, dialog)

    def test_bezaras_valodi_kattintassal_zarja_az_adatbazis_athelyezest(
        self, parbeszed_app, qt_app, tmp_path
    ):
        window, controller, engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog, _fake = _athelyezes_megnyit(window, qt_app, engine, tmp_path)

        _klikk_ablakban(qt_app, dialog, _gyerek(dialog, "moveDatabaseCloseButton"))

        assert _varj(qt_app, lambda: dialog.property("visible") is False), (
            "a Bezárás kattintás nem zárta be a párbeszédet"
        )


def _beallitasok_megnyit(window, qt_app):
    """Eszközök ▸ Options… valódi kattintással; visszaadja a párbeszédet."""
    menu_bar = window.property("menuBar")
    _megnyit(menu_bar, qt_app, "&Tools")
    _menupont_kattintasa(window, qt_app, "menuToolsOptions")
    assert _varj(qt_app, lambda: _latszik(window, "optionsDialog")), (
        "az Eszközök ▸ Options… nem nyitotta meg a beállításokat"
    )
    beallitasok = _gyerek(window, "optionsDialog")
    # aktív ablak kell: aktiválás nélkül az első kattintást az ablak-váltás emészti
    beallitasok.requestActivate()
    assert _varj(qt_app, lambda: beallitasok.property("active") is True)
    return beallitasok


def _fulre_kattint(qt_app, beallitasok, nev: str, index: int) -> None:
    """Valódi kattintás a fülön; várja, hogy a fülsor a `index`-edik lapra váltson."""
    _klikk_ablakban(qt_app, beallitasok, _gyerek(beallitasok, nev))
    assert _varj(
        qt_app,
        lambda: _gyerek(beallitasok, "optionsTabStack").property("currentIndex") == index,
    ), f"a(z) {nev} kattintás nem váltott a(z) {index}. fülre"


class TestBeallitasok:
    @pytest.mark.parametrize(
        ("nev", "index"),
        [
            ("optionsTabGeneral", 0),
            ("optionsTabEmail", 1),
            ("optionsTabNetwork", 5),
            ("optionsTabWebAlbums", 6),
            ("optionsTabNameTags", 7),
        ],
    )
    def test_a_fulre_kattintas_valtja_a_lapot(self, parbeszed_app, qt_app, nev, index):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _beallitasok_megnyit(window, qt_app)
        _fulre_kattint(qt_app, beallitasok, "optionsTabFileTypes", 2)  # innen indulunk

        _fulre_kattint(qt_app, beallitasok, nev, index)

        _zar(qt_app, beallitasok)

    def test_bezar_valodi_kattintassal_elrejti_a_beallitasokat(self, parbeszed_app, qt_app):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _beallitasok_megnyit(window, qt_app)

        _klikk_ablakban(qt_app, beallitasok, _gyerek(beallitasok, "optionsCloseButton"))

        assert _varj(qt_app, lambda: beallitasok.property("visible") is False), (
            "a Bezárás kattintás nem rejtette el a beállításokat"
        )

    def test_a_fulsor_nyilai_valodi_kattintassal_gorgetnek(self, parbeszed_app, qt_app):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _beallitasok_megnyit(window, qt_app)
        # keskeny ablak: a fülsor túlcsordul, és megjelennek a görgető nyilak
        beallitasok.setProperty("width", 480)
        beallitasok.requestActivate()
        jobb = _gyerek(beallitasok, "optionsTabScrollRightButton")
        bal = _gyerek(beallitasok, "optionsTabScrollLeftButton")
        assert _varj(qt_app, lambda: jobb.property("visible") is True), (
            "keskeny ablakban nem jelent meg a jobbra görgető nyíl"
        )
        sav = _gyerek(beallitasok, "optionsTabBar").property("contentItem")
        # a fülsor a 0-s lapra igazítása (Qt.callLater) lefusson, mielőtt mérünk
        assert _varj(qt_app, lambda: beallitasok.property("active") is True)
        qt_app.processEvents()
        x_kezdo = sav.property("contentX")

        _klikk_ablakban(qt_app, beallitasok, jobb)

        assert _varj(qt_app, lambda: sav.property("contentX") > x_kezdo), (
            "a jobbra görgető nyíl kattintása nem görgette a fülsort"
        )
        x_jobb = sav.property("contentX")
        _klikk_ablakban(qt_app, beallitasok, bal)
        assert _varj(qt_app, lambda: sav.property("contentX") < x_jobb), (
            "a balra görgető nyíl kattintása nem görgette vissza a fülsort"
        )
        _zar(qt_app, beallitasok)


def _email_fulon(window, qt_app):
    """A Beállítások párbeszéd E-mail fülén, valódi kattintással."""
    beallitasok = _beallitasok_megnyit(window, qt_app)
    _fulre_kattint(qt_app, beallitasok, "optionsTabEmail", 1)
    return beallitasok


class TestEmailFul:
    @pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
    def test_a_valasztas_radio_valodi_kattintassal_a_sajat_levelezot_kapcsolja(
        self, email_app, qt_app, magassag_elteres
    ):
        window, controller, engine = email_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _email_fulon(window, qt_app)
        beallitasok.setProperty(
            "height", beallitasok.property("height") + magassag_elteres
        )
        qt_app.processEvents()
        levelezo = engine.rootContext().contextProperty("emailController")
        valasztas = _gyerek(beallitasok, "optionsMailChooseRadio")
        alapertelmezett = _gyerek(beallitasok, "optionsMailDefaultRadio")
        google = _gyerek(beallitasok, "optionsMailGoogleRadio")
        valasztas_y = valasztas.mapToScene(
            QPointF(valasztas.width() / 2, valasztas.height() / 2)
        ).y()
        alapertelmezett_y = alapertelmezett.mapToScene(
            QPointF(alapertelmezett.width() / 2, alapertelmezett.height() / 2)
        ).y()
        google_y = google.mapToScene(
            QPointF(google.width() / 2, google.height() / 2)
        ).y()
        assert valasztas_y < alapertelmezett_y < google_y, (
            "az e-mail rádiók nem a sablon szerinti választás, alapértelmezett, Google sorrendben állnak"
        )
        assert valasztas.property("checked") is True, (
            "kulcs hiányában az első e-mail rádiónak kell kijelölve lennie"
        )
        assert google.property("enabled") is False

        _klikk_ablakban(qt_app, beallitasok, _gyerek(beallitasok, "optionsMailDefaultRadio"))
        assert _varj(qt_app, lambda: levelezo.property("useDefaultClient") is True)
        assert levelezo._settings.value("mail/useDefaultClient") in (
            True,
            "true",
        )

        _klikk_ablakban(qt_app, beallitasok, valasztas)

        assert _varj(qt_app, lambda: levelezo.property("useDefaultClient") is False), (
            "a Választás radio kattintása nem állította át a levelezőt"
        )
        assert levelezo._settings.value("mail/useDefaultClient") in (
            False,
            "false",
        )
        _zar(qt_app, beallitasok)

    def test_az_alapertelmezett_radio_valodi_kattintassal_visszavalt(self, email_app, qt_app):
        window, controller, engine = email_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _email_fulon(window, qt_app)
        levelezo = engine.rootContext().contextProperty("emailController")
        _klikk_ablakban(qt_app, beallitasok, _gyerek(beallitasok, "optionsMailChooseRadio"))
        assert _varj(qt_app, lambda: levelezo.property("useDefaultClient") is False)

        _klikk_ablakban(qt_app, beallitasok, _gyerek(beallitasok, "optionsMailDefaultRadio"))

        assert _varj(qt_app, lambda: levelezo.property("useDefaultClient") is True), (
            "az Alapértelmezett radio kattintása nem állította vissza a levelezőt"
        )
        _zar(qt_app, beallitasok)

    def test_az_eredeti_meret_radio_valodi_kattintassal_az_eredetit_kuldi(self, email_app, qt_app):
        window, controller, engine = email_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _email_fulon(window, qt_app)
        levelezo = engine.rootContext().contextProperty("emailController")
        assert levelezo.property("singlePictureOriginal") is False, "a próba feltétele: kicsinyített"

        _klikk_ablakban(qt_app, beallitasok, _gyerek(beallitasok, "optionsMailSingleOriginalRadio"))

        assert _varj(qt_app, lambda: levelezo.property("singlePictureOriginal") is True), (
            "az Eredeti méret radio kattintása nem állította át a küldést"
        )
        _zar(qt_app, beallitasok)

    def test_az_egy_kep_meretenek_radio_valodi_kattintassal_visszavalt(self, email_app, qt_app):
        window, controller, engine = email_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _email_fulon(window, qt_app)
        levelezo = engine.rootContext().contextProperty("emailController")
        _klikk_ablakban(qt_app, beallitasok, _gyerek(beallitasok, "optionsMailSingleOriginalRadio"))
        assert _varj(qt_app, lambda: levelezo.property("singlePictureOriginal") is True)

        _klikk_ablakban(qt_app, beallitasok, _gyerek(beallitasok, "optionsMailSingleSameRadio"))

        assert _varj(qt_app, lambda: levelezo.property("singlePictureOriginal") is False), (
            "a Mint a többi radio kattintása nem állította vissza a küldést"
        )
        _zar(qt_app, beallitasok)

    def test_a_google_fiok_radio_tiltott_a_kattintas_nem_valt(self, email_app, qt_app):
        window, controller, engine = email_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _email_fulon(window, qt_app)
        levelezo = engine.rootContext().contextProperty("emailController")
        radio = _gyerek(beallitasok, "optionsMailGoogleRadio")
        assert radio.property("enabled") is False, "a Google-fiók radiónak tiltottnak kell lennie"
        elotte = levelezo.property("useDefaultClient")

        _klikk_ablakban(qt_app, beallitasok, radio)

        assert radio.property("checked") is False, "a tiltott Google-fiók radio átváltott"
        assert levelezo.property("useDefaultClient") == elotte
        _zar(qt_app, beallitasok)

    def test_a_html_jelolo_tiltott_a_kattintas_nem_valt(self, email_app, qt_app):
        window, controller, engine = email_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _email_fulon(window, qt_app)
        jelolo = _gyerek(beallitasok, "optionsMailUseHtmlCheck")
        assert jelolo.property("enabled") is False, "a HTML-jelölőnek tiltottnak kell lennie"
        elotte = jelolo.property("checked")

        _klikk_ablakban(qt_app, beallitasok, jelolo)

        assert jelolo.property("checked") == elotte, "a tiltott HTML-jelölő átváltott"
        _zar(qt_app, beallitasok)
