"""A kollázs-piszkozat VISSZATÖLTÉSE — a felajánlás bekötése (#1051).

Spec: `docs/specs/picasa-create-features.md` **1.5** és
`docs/specs/picasa-kollazs-felulet.md` **9.2/b**.

## Miért kellett ez a teszt

A vezérlőben mind a négy tag KÉSZ volt és működött — `restoreCollageDraft`,
`collageDraftAvailable`, `refreshCollageDraft`, `discardCollageDraft` —,
a QML mégis **egyetlen helyen sem hívta meg** egyiket sem. Ez a
„megvan, de nem hat" harmadik állapot: a kód létezik, a tesztek zöldek, a
funkció mégsem létezik a felhasználó számára. A tulajdonos gépén egy
valódi, 2026-08-18-i `autosave.cxf` állt elérhetetlenül a lemezen.

Ezért ez a fájl a SIKERKRITÉRIUMOKAT állítja, nem a bekötés alakját:
indulás után van-e felajánlás, és a két ág tényleg elvégzi-e, amit ígér.

## Miért a beállításfájlba írjuk a piszkozat mappáját

A piszkozat helye a `collage/outputDir` beállítás, tartaléka pedig a
VALÓDI `~/Pictures/Picasa/Kollázsok`. Egy teszt, ami ezt nem téríti el,
a felhasználó saját piszkozatát olvasná — és a „nem" ágon TÖRÖLNÉ is.
A `qml_app` a `tmp_path/settings.ini`-ből építi a `QSettings`-et, ezért a
mappát oda írjuk be, MIELŐTT a `qml_app` felállna (a fixture-sorrendet a
tesztek szignatúrája rögzíti: `draft_dir` mindig előbb szerepel).

## Miért az indulási állapotot nézzük

A kritérium szó szerint az, hogy a program **induláskor** ajánlja fel. Ha
a tesztek a felajánlást utólag, kézzel nyitnák meg, pontosan azt a hibát
nem fognák meg, ami miatt a jegy megszületett: hogy senki nem kérdezi meg
a `collageDraftAvailable`-t.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt

from picasapy.collage.autosave import AUTOSAVE_NAME, write_autosave
from picasapy.collage.cxf import CxfBackground, CxfNode, CxfProject

#: A felajánlás párbeszéde és a két ága.
PARBESZED = "collageDraftDialog"
VISSZAALLIT = "collageDraftRestoreButton"
ELVET = "collageDraftDiscardButton"

#: A négy vezérlő-tag, aminek a jegy szerint hívóra kell találnia.
BEKOTENDO_TAGOK = (
    "restoreCollageDraft",
    "collageDraftAvailable",
    "refreshCollageDraft",
    "discardCollageDraft",
)


def _projekt(lib: Path) -> CxfProject:
    """Kétképes kupac VALÓDI képútvonalakkal — a visszatöltés a lemezről
    olvassa a csempéket, kitalált útvonalról nem tudna képet rakni."""
    return CxfProject(
        aspect_ratio="15:10",
        orientation="portrait",
        theme="picturepile",
        shadows=True,
        captions=True,
        album_uid="a4ef8e0fd2dbb152d25d79eb2bd2a28b",
        album_title="Tegnap esti munka",
        album_date="2026. augusztus",
        background=CxfBackground(type="solid", color="FF203040"),
        spacing=0.25,
        nodes=(
            CxfNode(
                x=0.25, y=0.5, w=0.3, h=0.2, theta=0.4, scale=512.0,
                theme="polaroid", src=str(lib / "a.jpg"),
            ),
            CxfNode(
                x=0.75, y=0.5, w=0.3, h=0.2, theta=-0.4, scale=640.0,
                theme="whiteborder", src=str(lib / "b.jpg"),
            ),
        ),
    )


@pytest.fixture
def draft_dir(tmp_path):
    """A piszkozat mappája, a `qml_app` beállításfájlján át eltérítve.

    ⚠️ A beállítást **`QSettings`-szel** írjuk ki, nem nyers szövegként. Az
    INI-formátumban a `\\` ESCAPE-karakter, tehát a windowsos útvonal
    (`C:\\Users\\...`) nyersen kiírva összetörik: a program más mappát
    keresne, és a felajánlás soha nem jönne elő. A windows-CI-lábon
    pontosan ezen bukott el ez a fájl."""
    from PySide6.QtCore import QSettings

    mappa = tmp_path / "kollazsok"
    mappa.mkdir()
    beallitasok = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    beallitasok.setValue("collage/outputDir", str(mappa))
    beallitasok.sync()
    return mappa


@pytest.fixture
def draft(draft_dir, tmp_path):
    """Ép piszkozat a mappában, még az alkalmazás felállása ELŐTT."""
    write_autosave(draft_dir, _projekt(tmp_path / "kepek"))
    return draft_dir / AUTOSAVE_NAME


@pytest.fixture
def serult_draft(draft_dir):
    """Csonk piszkozat — a felajánlás NEM jöhet elő rá."""
    (draft_dir / AUTOSAVE_NAME).write_bytes(b"<collage")
    return draft_dir / AUTOSAVE_NAME


def _parbeszed(window):
    return window.findChild(QObject, PARBESZED)


def _gomb(window, nev):
    parbeszed = _parbeszed(window)
    assert parbeszed is not None, "nincs felajánlás-párbeszéd"
    gomb = parbeszed.findChild(QObject, nev)
    assert gomb is not None, f"nincs {nev} gomb a felajánlásban"
    return gomb


def _kattints(window, nev):
    QMetaObject.invokeMethod(
        _gomb(window, nev), "clicked", Qt.ConnectionType.DirectConnection
    )


class TestAFelajanlas:
    """Indulás után a program szól, ha van visszaállítható munka."""

    def test_indulaskor_felajanlja_ha_van_piszkozat(self, draft, qml_app):
        window, _controller, _engine = qml_app

        parbeszed = _parbeszed(window)

        assert parbeszed is not None
        assert parbeszed.property("visible") is True

    def test_piszkozat_nelkul_nincs_felajanlas(self, draft_dir, qml_app):
        window, _controller, _engine = qml_app

        parbeszed = _parbeszed(window)

        assert parbeszed is None or parbeszed.property("visible") is False

    def test_serult_piszkozatra_nincs_felajanlas(self, serult_draft, qml_app):
        window, controller, _engine = qml_app

        parbeszed = _parbeszed(window)

        assert controller.collageDraftAvailable is False
        assert parbeszed is None or parbeszed.property("visible") is False


class TestAVisszaallitasAga:
    """„Igen": a piszkozat lapja nyílik meg, a tegnapi tartalommal."""

    def test_a_kollazs_lap_megnyilik(self, draft, qml_app):
        window, controller, _engine = qml_app

        _kattints(window, VISSZAALLIT)

        assert controller.collageOpen is True

    def test_a_piszkozat_csomopontjai_visszajonnek(self, draft, qml_app):
        window, controller, _engine = qml_app

        _kattints(window, VISSZAALLIT)

        assert controller.collageClipCount == 2

    def test_a_tema_es_a_tajolas_a_piszkozate(self, draft, qml_app):
        window, controller, _engine = qml_app

        _kattints(window, VISSZAALLIT)

        assert controller.collageTheme == "picturepile"
        assert controller.collageOrientation == "portrait"

    def test_az_arnyek_a_kepfelirat_es_a_cim_visszajon(self, draft, qml_app):
        window, controller, _engine = qml_app

        _kattints(window, VISSZAALLIT)

        assert controller.collageShadows is True
        assert controller.collageCaptions is True
        assert controller.collageTitle == "Tegnap esti munka"

    def test_a_kollazs_ful_lesz_az_aktiv(self, draft, qml_app):
        window, _controller, _engine = qml_app

        _kattints(window, VISSZAALLIT)

        sav = window.findChild(QObject, "documentTabStrip")
        assert sav is not None
        assert sav.property("activeTabId") == window.property("collageTabId")

    def test_a_felajanlas_bezarul(self, draft, qml_app):
        window, _controller, _engine = qml_app

        _kattints(window, VISSZAALLIT)

        assert _parbeszed(window).property("visible") is False


class TestAzElvetesAga:
    """„Nem": a piszkozat eltűnik, és a kérdés nem tér vissza."""

    def test_torlodik_az_autosave_fajl(self, draft, qml_app):
        window, _controller, _engine = qml_app

        _kattints(window, ELVET)

        assert not draft.exists()

    def test_a_felajanlas_nem_ter_vissza(self, draft, qml_app):
        window, controller, _engine = qml_app

        _kattints(window, ELVET)
        controller.refreshCollageDraft()

        assert controller.collageDraftAvailable is False
        assert _parbeszed(window).property("visible") is False

    def test_a_kollazs_lap_nem_nyilik_meg(self, draft, qml_app):
        window, controller, _engine = qml_app

        _kattints(window, ELVET)

        assert controller.collageOpen is False


class TestANegyTagHivoja:
    """A jegy tulajdonképpeni lelete: a QML EGYIKET SEM hívta.

    Szövegkeresés, mert pont az a hiba osztálya, hogy a futó kód sosem ér
    el a tagokig — egy zöld egységteszt ezt nem venné észre."""

    @pytest.mark.parametrize("tag", BEKOTENDO_TAGOK)
    def test_a_tagnak_van_qml_hivoja(self, tag):
        import picasapy.app

        qml_gyoker = Path(picasapy.app.__file__).parent / "qml"
        talalatok = [
            p.name
            for p in qml_gyoker.rglob("*.qml")
            if tag in p.read_text(encoding="utf-8")
        ]

        assert talalatok, f"a(z) {tag} tagot a QML sehol nem használja"
