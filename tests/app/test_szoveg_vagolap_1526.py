"""#1526 - a képfelirat vágólap-API-ja; a menüút #5877 óta Text-réteget visz.

A fájl-vágólap (`Cut`/`Copy`/`Paste`) és a szövegmező hét tételes helyi
menüje már elkészült. Az #1526-os controller-API a képfelirat szövegét
másolja, de a #5877-ben visszaállított eredeti `Copy Text` / `Paste Text`
menüparancsok ettől külön a Text eszköz `text=` rétegét kezelik. A menüsor
nem hívja ezeket a felirat-API-kat.

⚠️ Ez a próba nem a rendszervágólapot méri — fej nélküli környezetben
(`offscreen`/`minimal`) nincs vágólap-tulajdonos, és a Qt-hívás a CI-n
szegmenshibával állította meg a tesztfájlt (ld. a `fileops_controller`
figyelmeztetését). A vezérlő ezért egy eltéríthető szövegtárat használ, és a
próba AZT méri, amit feltennénk / amit olvasnánk.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from support.jpeg_factory import make_jpeg
from tests.support.qt_wait import wait_for_photo_op
from support.menubar_components_6016 import main_sources, menu_sources

_MENU = menu_sources()
_MAIN = main_sources()


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    mappa = root / "a"
    mappa.mkdir(parents=True)
    make_jpeg(mappa / "egy.png", size=(120, 90))
    make_jpeg(mappa / "ketto.png", size=(120, 90))
    return root, mappa


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    root, mappa = library
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    ctl = AppController(
        tmp_path / "index.db",
        (str(root),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(mappa))
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def _varj(qt_app, feltetel, masodperc: float = 15.0) -> bool:
    """Több képre menő írásnál a teljes nézetállapotra várunk."""
    import time

    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        if feltetel():
            return True
        qt_app.processEvents()
        time.sleep(0.01)
    return False


def _sor(controller, nev: str) -> int:
    for i, photo in enumerate(controller.photos.photos):
        if photo.name == nev:
            return i
    raise AssertionError(f"nincs ilyen kép a rácson: {nev}")


class TestASzovegMasolasa:
    def test_a_felirat_a_vagolapra_kerul(self, controller):
        sor = _sor(controller, "egy.png")
        wait_for_photo_op(
            controller, lambda: controller.setCaption(sor, "Nyári kirándulás")
        )

        assert controller.copyCaptionText(sor) is True
        assert controller.captionClipboardText() == "Nyári kirándulás"

    def test_felirat_NELKUL_nem_tesz_fel_semmit(self, controller):
        """Ismert negatív: üres feliratot feltenni annyi, mint kiürítni a
        vágólapot — a felhasználó azt nem kérte."""
        sor = _sor(controller, "ketto.png")
        assert controller.copyCaptionText(sor) is False
        assert controller.captionClipboardText() == ""

    def test_ervenytelen_sorra_NEM_hibazik(self, controller):
        assert controller.copyCaptionText(999) is False


class TestASzovegBeillesztese:
    def test_a_vagolap_szovege_a_feliratba_kerul(self, controller, qt_app):
        sor = _sor(controller, "egy.png")
        controller.setCaptionClipboardText("Tengerpart")

        assert controller.pasteCaptionText([sor]) == 1
        assert _varj(
            qt_app, lambda: controller.photos.captionAt(sor) == "Tengerpart"
        ), "a felirat nem íródott ki"

    def test_MINDEN_kijelolt_kep_megkapja(self, controller, qt_app):
        """Az eredetiben a parancs a KIJELÖLÉSRE hat, nem egy képre."""
        sorok = [_sor(controller, "egy.png"), _sor(controller, "ketto.png")]
        controller.setCaptionClipboardText("Közös felirat")

        assert controller.pasteCaptionText(sorok) == 2
        assert _varj(
            qt_app,
            lambda: all(
                controller.photos.captionAt(sor) == "Közös felirat"
                for sor in sorok
            ),
        ), "nem mindegyik kép kapta meg a feliratot"

    def test_a_kijelolesre_EGYETLEN_hatterszal_indul(self, controller):
        """#2915: képenként egy szál helyett EGY soros köteg.

        Két, ugyanabban a mappában levő kép ugyanabba a `.picasa.ini`-be és
        ugyanabba az indexbe ír. Képenként külön szálat indítva ez
        versenyhelyzet: a windowsos CI-n a kijelölés egy része felirat
        nélkül maradt (a hiba nem időzítési türelemmel oldódik, hanem a
        párhuzamosság megszüntetésével)."""
        sorok = [_sor(controller, "egy.png"), _sor(controller, "ketto.png")]
        controller.setCaptionClipboardText("Közös felirat")
        inditasok = []
        controller._start_background = lambda *a, **k: inditasok.append(a)

        assert controller.pasteCaptionText(sorok) == 2
        assert len(inditasok) == 1, (
            f"{len(inditasok)} háttérszál indult két képre — "
            "a köteg soros útja hiányzik"
        )

    def test_URES_vagolapra_nem_tesz_semmit(self, controller):
        """Az üres vágólap ne törölje le a meglévő feliratokat — az néma
        adatvesztés lenne."""
        sor = _sor(controller, "egy.png")
        wait_for_photo_op(
            controller, lambda: controller.setCaption(sor, "Megmaradok")
        )
        controller.setCaptionClipboardText("")

        assert controller.pasteCaptionText([sor]) == 0
        assert controller.photos.captionAt(sor) == "Megmaradok"

class TestAMenuBekotes:
    def test_a_ket_tetel_mar_NEM_helyfoglalo(self):
        for nev in ("menuEditCopyText", "menuEditPasteText"):
            assert f'objectName: "{nev}"' in _MENU, f"{nev} hiányzik"
            kezd = _MENU.index(f'objectName: "{nev}"')
            blokk = _MENU[kezd : kezd + 400]
            assert "placeholder: true" not in blokk, (
                f"{nev} még helyfoglaló — a felirat ígéret, a hiányzó "
                "funkció pedig hazugság (#1526)"
            )

    def test_a_menutetel_a_szovegreteg_vezerlohoz_kot(self):
        assert "onCopyTextRequested" in _MAIN
        assert "onPasteTextRequested" in _MAIN
        assert "copyTextLayer(" in _MAIN
        assert "pasteTextLayer(" in _MAIN
        assert "copyCaptionText(" not in _MAIN
        assert "pasteCaptionText(" not in _MAIN

    def test_a_beillesztes_a_szovegreteg_pufferet_figyeli(self):
        kezd = _MENU.index('objectName: "menuEditPasteText"')
        blokk = _MENU[kezd : kezd + 500]
        assert "hasTextLayerClipboard" in blokk, (
            "a Paste Text nem a Text-réteg vágólapját figyeli"
        )
        assert "hasSelectedTextLayer" in blokk, (
            "a Text eszközből származó aktuális rétegpuffer nem érhető el"
        )
