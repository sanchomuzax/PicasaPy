"""A korábbi telepítésből származó Picasa-adat felderítése — #1622.

Az eredeti Picasa induláskor **magától megnézi**, hogy egy korábbi
Windows-telepítés maradványaiban van-e Picasa-adat, és átveszi. Két
útvonalat próbál (`0x00406770` — mind a négy literál ugyanabban a
függvényben; a `$$` a felhasználónévre álló helyettesítő):

```
C:\\Windows.old\\Documents and Settings\\$$\\Local Settings\\Application Data\\Google\\
C:\\Windows.old\\Users\\$$\\AppData\\Local\\Google\\
```

Aki új Windowsra frissített, annak az albumai és arcadatai **maguktól
előkerültek**. Nálunk ugyanez a felhasználó nulláról kezdett.

## Két különbség az eredetihez képest — mindkettő szándékos

1. **Kérdezünk, nem veszünk át némán.** Hogy az eredeti kérdez-e, NINCS
   kimérve (a jegy hatókörön kívülre tette); adatátvételnél a némaság a
   kockázatosabb irány.
2. **A felajánlás egyszer fut le.** Aki elutasította, azt ne kérdezzük meg
   minden indításkor — a felderítés a Mappakezelő gombjából bármikor
   újraindítható.

## Nincs `skipif`

A windowsos útvonalakat a `windows_old` paraméteren át **Linuxon is
végigmérjük** (a #1217 mintája). A #1560 hibája épp az volt, hogy egy
windowsra kötött ág a CI ubuntu-lábán üresen zölden maradt.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QSettings

from picasapy.scanner.discovery import discover_installations

_MAIN = (
    Path(picasapy.app.__file__).parent / "qml" / "Main.qml"
).read_text(encoding="utf-8")
_DIALOG = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "PicasaImportDialog.qml"
).read_text(encoding="utf-8")


def _telepites(gyoker: Path, rel: str, felhasznalo: str = "sancho") -> Path:
    """Egy hiteles `Windows.old`-profil a megadott alakban."""
    appdata = gyoker / rel.format(felhasznalo=felhasznalo)
    (appdata / "Google" / "Picasa2Albums").mkdir(parents=True)
    (appdata / "Google" / "Picasa2").mkdir(parents=True)
    return appdata


class TestAKetMertUtvonal:
    def test_a_VISTA_alakot_megtalalja(self, tmp_path):
        gyoker = tmp_path / "Windows.old"
        _telepites(gyoker, "Users/{felhasznalo}/AppData/Local")
        talalat = discover_installations(
            home=tmp_path / "nincs-home", windows_old=gyoker
        )
        assert len(talalat) == 1

    def test_az_XP_alakot_is_megtalalja(self, tmp_path):
        gyoker = tmp_path / "Windows.old"
        _telepites(
            gyoker,
            "Documents and Settings/{felhasznalo}/Local Settings/"
            "Application Data",
        )
        talalat = discover_installations(
            home=tmp_path / "nincs-home", windows_old=gyoker
        )
        assert len(talalat) == 1

    def test_TOBB_profilt_is_végigjár(self, tmp_path):
        """A felhasználónevet nem találgatjuk — a `$$` bármi lehet."""
        gyoker = tmp_path / "Windows.old"
        _telepites(gyoker, "Users/{felhasznalo}/AppData/Local", "anna")
        _telepites(gyoker, "Users/{felhasznalo}/AppData/Local", "bela")
        talalat = discover_installations(
            home=tmp_path / "nincs-home", windows_old=gyoker
        )
        assert len(talalat) == 2

    def test_a_cimke_megnevezi_a_profilt(self, tmp_path):
        gyoker = tmp_path / "Windows.old"
        _telepites(gyoker, "Users/{felhasznalo}/AppData/Local", "anna")
        talalat = discover_installations(
            home=tmp_path / "nincs-home", windows_old=gyoker
        )
        assert "anna" in talalat[0].label


class TestNincsTalalat:
    def test_hianyzo_gyokerre_URES(self, tmp_path):
        assert (
            discover_installations(
                home=tmp_path / "nincs-home",
                windows_old=tmp_path / "nincs-ilyen",
            )
            == ()
        )

    def test_ures_Windows_old_ra_URES(self, tmp_path):
        gyoker = tmp_path / "Windows.old"
        gyoker.mkdir()
        assert (
            discover_installations(
                home=tmp_path / "nincs-home", windows_old=gyoker
            )
            == ()
        )

    def test_Picasa_adat_NELKULI_profil_nem_talalat(self, tmp_path):
        gyoker = tmp_path / "Windows.old"
        (gyoker / "Users" / "anna" / "AppData" / "Local").mkdir(parents=True)
        assert (
            discover_installations(
                home=tmp_path / "nincs-home", windows_old=gyoker
            )
            == ()
        )


class TestAzInduláskoriFelajanlas:
    @pytest.fixture
    def ctl(self, qt_app, tmp_path):
        from picasapy.app.discovery_controller import DiscoveryController

        settings = QSettings(
            str(tmp_path / "s.ini"), QSettings.Format.IniFormat
        )
        return DiscoveryController(
            add_folder=lambda _p: None, settings=settings
        )

    def test_masodszor_MAR_NEM_fut_le(self, ctl, qt_app):
        """Aki elutasította, azt ne kérdezzük minden indításkor.

        ⚠️ A `processEvents()` NEM kényelmi lépés: a jelzés a worker-
        szálról jön, a Qt pedig SORBA ÁLLÍTJA a GUI-szálra. Enélkül a
        `kaptunk` mindkét körben üres marad, és a teszt akkor is zöld,
        ha a felajánlás minden induláskor lefut — az első változatom
        pontosan így volt fogatlan (mutációval kiderült)."""
        kaptunk: list[int] = []
        ctl.startupDiscoveryFinished.connect(
            lambda _f, darab: kaptunk.append(darab)
        )
        ctl.discoverAtStartup()
        assert ctl.waitForBackgroundWorkers(30.0)
        qt_app.processEvents()
        elso = len(kaptunk)
        assert elso == 1, "az első felajánlás jelzése nem érkezett meg"

        ctl.discoverAtStartup()
        assert ctl.waitForBackgroundWorkers(30.0)
        qt_app.processEvents()

        assert len(kaptunk) == elso, "a felajánlás másodszor is lefutott"

    def test_a_jelolo_a_beallitasba_kerul(self, ctl):
        """A „már felajánlottuk" TARTÓS — túléli az újraindítást."""
        from picasapy.app.discovery_controller import DiscoveryController

        beallitas = ctl._settings
        assert not beallitas.value(DiscoveryController.STARTUP_OFFER_KEY, False)
        ctl.discoverAtStartup()
        assert ctl.waitForBackgroundWorkers(30.0)
        assert beallitas.value(DiscoveryController.STARTUP_OFFER_KEY)

    def test_beallitas_nelkul_sem_dol_el(self, qt_app):
        """A `settings=None` (próbák, beágyazott használat) nem hibázhat."""
        from picasapy.app.discovery_controller import DiscoveryController

        ctl = DiscoveryController(add_folder=lambda _p: None)
        ctl.discoverAtStartup()
        assert ctl.waitForBackgroundWorkers(30.0)


class TestABekotes:
    def test_az_indulas_HIVJA(self):
        assert "discoveryController.discoverAtStartup()" in _MAIN

    def test_a_dialogus_FELVESZI_a_jelzest(self):
        assert "function onStartupDiscoveryFinished(" in _DIALOG

    def test_talalat_NELKUL_semmi_nem_jelenik_meg(self):
        """A jegy záró pontja: nincs találat ⇒ semmi nem történik."""
        kezd = _DIALOG.index("function onStartupDiscoveryFinished(")
        blokk = _DIALOG[kezd : kezd + 700]
        assert "if (installationsFound <= 0)" in blokk
        assert "return" in blokk
        # a `return` a megnyitás ELŐTT áll
        assert blokk.index("return") < blokk.index("importDialog.open()")

    def test_a_MEGLEVO_felderito_uton_megy(self):
        """A jegy kiköti: a beolvasás a meglévő PMP-importálón, nem újon."""
        ctl = (
            Path(picasapy.app.__file__).parent / "discovery_controller.py"
        ).read_text(encoding="utf-8")
        kezd = ctl.index("def _felderites(")
        assert "discover_installations()" in ctl[kezd : kezd + 700]
        assert "propose_watched_folders(" in ctl[kezd : kezd + 700]
