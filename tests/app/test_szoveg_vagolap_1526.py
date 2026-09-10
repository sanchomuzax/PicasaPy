"""#1526 — a Szerkesztés menü „Szöveg másolása / beillesztése" a FELIRATRA hat.

A jegy hét vágólap-parancsot mért ki két névtérben; a fájl-vágólap
(`Cut`/`Copy`/`Paste`) és a szövegmező hét tételes helyi menüje már elkészült.
Ez a szelet a maradék kettő: a `Copy Text` / `Paste Text`, ami az eredetiben
NEM a fájlra, hanem a **felirat szövegére** hat.

⚠️ Ez a próba nem a rendszervágólapot méri — fej nélküli környezetben
(`offscreen`/`minimal`) nincs vágólap-tulajdonos, és a Qt-hívás a CI-n
szegmenshibával állította meg a tesztfájlt (ld. a `fileops_controller`
figyelmeztetését). A vezérlő ezért egy eltéríthető szövegtárat használ, és a
próba AZT méri, amit feltennénk / amit olvasnánk.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QSettings

from support.jpeg_factory import make_jpeg
from tests.support.qt_wait import wait_for_photo_op

_MENU = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
).read_text(encoding="utf-8")
_MAIN = (
    Path(picasapy.app.__file__).parent / "qml" / "Main.qml"
).read_text(encoding="utf-8")


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
    """Több képre menő írás TÖBB `photoOpFinished`-et ad — egyetlen jelzésre
    várni versenyhelyzet volna, ezért a VÉGÁLLAPOTRA várunk."""
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

    def test_a_jelzo_MUTATJA_hogy_van_e_szoveg(self, controller):
        controller.setCaptionClipboardText("")
        assert controller.hasCaptionTextClipboard is False
        controller.setCaptionClipboardText("valami")
        assert controller.hasCaptionTextClipboard is True


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

    def test_a_jel_ELJUT_a_vezerlohoz(self):
        """A #1153 osztálya: a menü jelet ad, de senki nem veszi fel."""
        assert "onCopyTextRequested" in _MAIN
        assert "onPasteTextRequested" in _MAIN
        assert "copyCaptionText(" in _MAIN
        assert "pasteCaptionText(" in _MAIN

    def test_a_beillesztes_csak_szoveggel_ELERHETO(self):
        kezd = _MENU.index('objectName: "menuEditPasteText"')
        assert "hasCaptionTextClipboard" in _MENU[kezd : kezd + 400], (
            "a Szöveg beillesztése üres vágólappal is kattintható — "
            "hatástalan menütétel"
        )
