"""Az „Asztali háttérkép" tényleg beállítja a hátteret (#1005).

## A mért viselkedés

Az eredeti ága (`0x0057aa10`) két lépést végez: BMP-t ír a
`<Képek>/Picasa/<Hátterek>/picasabackground.bmp` útvonalra (a mappanév
honosított: `CThumbUI::BackgroundsFolder`), majd beállítja a rendszer
háttérképét **középre, nyújtás nélkül** (`WallpaperStyle=0`,
`TileWallpaper=0`).

Linuxon a registry-írásnak nincs értelme, ezért a jegy kimondottan az asztali
környezet saját beállítását kéri. Amit ez a fájl mér: a BMP a MÉRT nevet és
helyet kapja, a beállító lánc **középre** illesztést kér, és a sikertelenség
NEM néma — a felhasználó megtudja, hova került a kép.
"""

from __future__ import annotations

import subprocess

import pytest
from support.jpeg_factory import make_jpeg

from picasapy.app import wallpaper


class _Futtato:
    """A `subprocess.run` helyettesítője — a próba nem nyúl a valódi asztalhoz."""

    def __init__(self, hibas: set[str] | None = None):
        self.hivasok: list[list[str]] = []
        self._hibas = hibas or set()

    def __call__(self, parancs, **_kwargs):
        self.hivasok.append(list(parancs))
        kod = 1 if parancs[0] in self._hibas else 0
        return subprocess.CompletedProcess(parancs, kod, "", "hiba" if kod else "")


class TestABmp:
    def test_a_MERT_nevet_es_helyet_kapja(self, tmp_path):
        kep = tmp_path / "kollazs.jpg"
        make_jpeg(kep)
        hatterek = tmp_path / "Picasa" / "Hátterek"

        bmp = wallpaper.write_background_bmp(kep, hatterek)

        assert bmp == hatterek / "picasabackground.bmp", (
            "az eredeti EZT a fájlnevet írja a Hátterek mappába"
        )
        assert bmp.exists() and bmp.stat().st_size > 0
        assert bmp.read_bytes()[:2] == b"BM", "BMP-t kell írni, nem JPEG-et"

    def test_a_mappa_letrejon(self, tmp_path):
        kep = tmp_path / "k.jpg"
        make_jpeg(kep)
        assert wallpaper.write_background_bmp(kep, tmp_path / "uj" / "mappa").exists()

    def test_olvashatatlan_kepre_hibat_dob(self, tmp_path):
        rossz = tmp_path / "nem-kep.jpg"
        rossz.write_bytes(b"nem kep")
        with pytest.raises(OSError):
            wallpaper.write_background_bmp(rossz, tmp_path / "hatterek")


class TestABeallitas:
    """#3026: minden próba KIMONDJA, melyik platform ágát méri.

    A #2985 óta a beállító platform szerint ágazik el. Ez a szakasz a
    LINUX láncot méri (`gsettings` → `pcmanfm` → `feh` → …), tehát a
    `platform="linux"` nem díszítés: nélküle a windowsos futtatón mind a
    négy próba a windowsos ágra fut, és a main CI windows-lába pirosra
    vált — pontosan ez történt a v0.8.417-nél."""

    def test_a_lanc_KOZEPRE_illeszt(self, tmp_path):
        """A mért `WallpaperStyle=0`/`TileWallpaper=0` párja: középre, nyújtás
        nélkül. Ha valaki „szebb" kitöltésre írja át, itt bukik el."""
        futtato = _Futtato()
        eszkoz = wallpaper.set_desktop_background(
            tmp_path / "h.bmp", runner=futtato, platform="linux",
            which=lambda nev: "/usr/bin/" + nev
        )

        assert eszkoz == "gsettings", "a lánc első elérhető eszköze nyer"
        parancsok = [" ".join(h) for h in futtato.hivasok]
        assert any("picture-options centered" in p for p in parancsok), (
            f"a középre illesztést KÉRNI kell: {parancsok}"
        )

    def test_a_kovetkezo_eszkozre_lep_ha_az_elso_elbukik(self, tmp_path):
        futtato = _Futtato(hibas={"gsettings"})

        eszkoz = wallpaper.set_desktop_background(
            tmp_path / "h.bmp", runner=futtato, platform="linux",
            which=lambda nev: "/usr/bin/" + nev
        )

        assert eszkoz == "pcmanfm"
        assert any("--wallpaper-mode=center" in " ".join(h) for h in futtato.hivasok)

    def test_a_nem_letezo_eszkozt_meg_sem_probalja(self, tmp_path):
        futtato = _Futtato()

        eszkoz = wallpaper.set_desktop_background(
            tmp_path / "h.bmp",
            runner=futtato,
            platform="linux",
            which=lambda nev: "/usr/bin/feh" if nev == "feh" else None,
        )

        assert eszkoz == "feh"
        assert [h[0] for h in futtato.hivasok] == ["feh"], (
            "csak a MEGLÉVŐ eszközt hívjuk"
        )
        assert "--bg-center" in futtato.hivasok[0]

    def test_ha_EGYIK_sincs_meg_None(self, tmp_path):
        """A hívó ebből tudja, hogy meg kell mondani a felhasználónak, hova
        került a kép — a néma sikertelenség a legrosszabb kimenet."""
        futtato = _Futtato()
        assert (
            wallpaper.set_desktop_background(
                tmp_path / "h.bmp", runner=futtato, platform="linux",
                which=lambda _nev: None
            )
            is None
        )
        assert futtato.hivasok == []


class TestAHely:
    def test_a_Hatterek_a_KOLLAZSOK_mappa_szomszedja(self, tmp_path, qt_app):
        """A BMP a kollázs-célmappa mellé kerül, nem a rendszer képmappájába.

        Alapállapotban a kettő UGYANAZ (`<Képek>/Picasa/Hátterek` — ez a mért
        útvonal), de ha a felhasználó máshova állította a kollázs-célmappát, a
        háttér is oda tartozik. Ez egyben a próbák elszigetelése: az első
        változatom a rendszer képmappájából számolt, és a CI őre (#1054) meg is
        fogta — egy meglévő teszt a VALÓDI `~/Pictures/Picasa/Backgrounds`-ba
        írt."""
        from PySide6.QtCore import QSettings

        from picasapy.app import collage_prefs, collage_save

        kollazsok = tmp_path / "sajat-hely" / "Kollázsok"
        kollazsok.mkdir(parents=True)
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        settings.setValue(collage_prefs.OUTPUT_DIR_KEY, str(kollazsok))
        kep = tmp_path / "kollazs.jpg"
        make_jpeg(kep)

        from PySide6.QtCore import QObject

        class _Gazda(collage_save.CollageSaveMixin, QObject):
            """A mixin önmagában nem QObject — a jelzések csak a végső
            osztályban élnek, ezért a próba is így példányosítja."""

            def _get_settings(self):
                return settings

        gazda = _Gazda()
        gazda._allitsd_be_hatterkepnek(str(kep))

        # a mappanév a FELÜLET nyelve szerint honosított (#1131) — a próba
        # ezért mindkét ismert alakot elfogadja, a HELYET méri
        talalatok = list(
            (kollazsok.parent).glob("*/picasabackground.bmp")
        )
        assert talalatok, (
            "a BMP a kollázs-célmappa SZOMSZÉDJÁBA kerül: "
            f"{list(kollazsok.parent.iterdir())}"
        )
        assert talalatok[0].parent.name in ("Hátterek", "Backgrounds")


class TestABekotes:
    """A kollázs-ág tényleg meghívja a láncot, és jelez a végén.

    A #1895 pontosan azért tiltotta le a gombot, mert a lánc a
    `collageDesktopBackgroundReady` jelzésnél véget ért — a felhasználó „kész"
    értesítést kapott, és az asztala változatlan maradt. Ez a próba ezt a
    hibaosztályt zárja ki."""

    @pytest.fixture
    def vezerlo(self, qt_app, tmp_path):
        from PySide6.QtCore import QSettings

        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import open_index, sync_tree
        from picasapy.thumbs import ThumbnailCache

        gyoker = tmp_path / "kepek"
        gyoker.mkdir()
        make_jpeg(gyoker / "a.jpg")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, gyoker)
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        ctl = AppController(
            tmp_path / "index.db",
            (str(gyoker),),
            provider,
            settings=settings,
            watched_file=tmp_path / "WatchedFolders.txt",
        )
        yield ctl, gyoker
        ctl.shutdown()

    def test_siker_eseten_MEGNEVEZI_az_eszkozt(self, vezerlo, tmp_path, monkeypatch):
        ctl, gyoker = vezerlo
        kep = gyoker / "a.jpg"
        monkeypatch.setattr(
            wallpaper, "write_background_bmp", lambda k, m: tmp_path / "h.bmp"
        )
        monkeypatch.setattr(wallpaper, "set_desktop_background", lambda b: "pcmanfm")
        eszkozok = []
        ctl.desktopBackgroundApplied.connect(eszkozok.append)

        ctl._allitsd_be_hatterkepnek(str(kep))

        assert eszkozok == ["pcmanfm"]

    def test_sikertelenseg_eseten_a_BMP_UTJAT_adja(self, vezerlo, tmp_path, monkeypatch):
        """Néma sikertelenség helyett: a felhasználó megtudja, hova került."""
        ctl, gyoker = vezerlo
        monkeypatch.setattr(
            wallpaper, "write_background_bmp", lambda k, m: tmp_path / "h.bmp"
        )
        monkeypatch.setattr(wallpaper, "set_desktop_background", lambda b: None)
        utak = []
        ctl.desktopBackgroundFailed.connect(utak.append)

        ctl._allitsd_be_hatterkepnek(str(gyoker / "a.jpg"))

        assert utak and utak[0].endswith("h.bmp")
