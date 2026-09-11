"""#671 4. pont: a kilépés NEM kérdez — kivéve futó háttérműveletnél.

Az eredeti Picasa a kilépést **nem blokkolja**, de ha folyamatban van munka,
rákérdez: *„Uploads are in progress. Would you like to exit now? (Uploads will
resume next time you run Picasa.)"* — két gombbal (`Exit Now` / `Keep Going`).

Nálunk a „feltöltés" megfelelője **bármelyik** nyilvántartott háttérmunka
(export, webexport, kötegelt effekt, arc-szkennelés), és az **nem** folytatódik
legközelebb — ezért a szöveg a mi valóságunkat mondja, nem az eredetit
fordítja. A gombpár az eredeti alakját követi.

⚠️ Ez az őr a FORRÁST méri (a kötések helyét), nem élő ablakot zár be: a
`Qt.quit()` a próba processzét vinné magával.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest

_QML_DIR = Path(picasapy.app.__file__).parent / "qml"
_MAIN = (_QML_DIR / "Main.qml").read_text(encoding="utf-8")
_MENU = (_QML_DIR / "PicasaPy" / "PicasaMenuBar.qml").read_text(encoding="utf-8")


class TestAKilepesEgyHelyenDolEl:
    def test_a_menutetel_NEM_hivja_kozvetlenul_a_kilepest(self):
        """Korábban a Fájl ▸ Kilépés közvetlenül zárta az appot — az
        megkerülte volna a kérdést.

        ⚠️ A vizsgálat az `onTriggered` SORÁRA szűkít, nem a blokkra: a
        blokk kommentje megnevezi a régi hívást, és a forrás-szintű őr a
        kommentet is olvassa (a teszt első alakja épp ezen bukott el)."""
        kezd = _MENU.index('objectName: "menuFileExit"')
        blokk = _MENU[kezd : kezd + 500]
        trigger_sor = next(
            sor for sor in blokk.split("\n") if "onTriggered:" in sor
        )
        assert "Qt.quit()" not in trigger_sor
        assert "exitRequested()" in trigger_sor

    def test_a_menusav_JELZI_a_kilepesi_kerest(self):
        assert "signal exitRequested()" in _MENU

    def test_a_gazda_a_KOZOS_utra_koti(self):
        assert "onExitRequested: window.kilepes()" in _MAIN

    def test_az_ablak_X_e_is_ugyanide_fut(self):
        """Ha csak a menü kérdezne, az „X" némán elvinné a futó munkát."""
        kezd = _MAIN.index("onClosing:")
        blokk = _MAIN[kezd : kezd + 400]
        assert "backgroundWorkRunning()" in blokk
        assert "close.accepted = false" in blokk
        assert "kilepesDialog.askExit()" in blokk


class TestAKerdesFeltetele:
    def test_a_kilepes_a_HATTERMUNKAT_kerdezi(self):
        kezd = _MAIN.index("function kilepes()")
        blokk = _MAIN[kezd : kezd + 400]
        assert "controller.backgroundWorkRunning()" in blokk
        assert "Qt.quit()" in blokk, "munka nélkül azonnal kilép"

    def test_a_null_or_ott_van(self):
        """#305: a leépülő motor is újraértékelheti a kötést."""
        kezd = _MAIN.index("function kilepes()")
        assert "controller &&" in _MAIN[kezd : kezd + 400]

    @pytest.mark.parametrize("felirat", ["Exit Now", "Keep Going"])
    def test_a_MERT_gombpar(self, felirat):
        assert felirat in _MAIN

    def test_a_kerdes_NEM_elnyomhato(self):
        """A `decisionKey` üres: adatvesztéssel járó kérdést nem lehet
        „ne kérdezze újra"-val elhallgattatni."""
        kezd = _MAIN.index("function askExit()")
        assert 'ensure().ask("", qsTr(' in _MAIN[kezd : kezd + 500]

    def test_a_szoveg_KIMONDJA_hogy_nem_folytatodik(self):
        """Az eredeti azt ígéri, hogy a feltöltés legközelebb folytatódik —
        a mi háttérmunkánk NEM, tehát ezt nem fordíthatjuk le."""
        assert "does not" in _MAIN and "resume later" in _MAIN
        assert "resume next time" not in _MAIN


class TestAVezerloOldal:
    def test_a_slot_a_GLOBALIS_nyilvantartast_kerdezi(self):
        """A futó munka lehet a webexport vagy az arc-szkennelés
        vezérlőjében is — a saját mixin csak a magáét látná."""
        from picasapy.app import controller as controller_modul

        forras = Path(controller_modul.__file__).read_text(encoding="utf-8")
        kezd = forras.index("def backgroundWorkRunning")
        blokk = forras[kezd : kezd + 900]
        assert "running_background_workers" in blokk

    def test_ures_nyilvantartasnal_hamis(self, qt_app):
        """Friss vezérlőn nincs futó munka — a kilépés ilyenkor nem kérdez."""
        from picasapy.app.worker_thread import running_background_workers

        assert running_background_workers() == ()
