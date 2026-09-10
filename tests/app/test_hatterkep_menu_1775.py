"""„Beállítás asztali háttérképként" — a menüparancs bekötése (#1775).

## A mérés

`eMenuCreate::ID_WALLPAPER` (`0x9cd2`), kezelő `0x0057aa10` (1143 b): a parancs
**MÁSOLATOT** ír — `picasabackground.bmp` a `Picasa/Backgrounds` mappába —, nem
az eredeti fájlra mutat, majd KÖZÉPRE teszi (`WallpaperStyle=0`,
`TileWallpaper=0`).

A másolat nem apróság: így a kép átnevezése vagy törlése nem viszi el az
asztal hátterét.

A motor közös a Kollázs-panel „Asztali háttérkép" gombjáéval (#1005) — ez a
fájl azt méri, hogy a MENÜ-út is odaér.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings
from support.jpeg_factory import make_jpeg

from picasapy.app import collage_prefs, wallpaper
from picasapy.index import open_index, sync_tree


@pytest.fixture
def vezerlo(qt_app, tmp_path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    make_jpeg(gyoker / "a.jpg")
    make_jpeg(gyoker / "b.jpg")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, gyoker)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    # a Hátterek mappa a KOLLÁZS-célmappa szomszédja — a próba ezt téríti el,
    # hogy a valódi képmappa érintetlen maradjon (#1054)
    settings.setValue(
        collage_prefs.OUTPUT_DIR_KEY, str(tmp_path / "picasa" / "Kollázsok")
    )
    ctl = AppController(
        tmp_path / "index.db",
        (str(gyoker),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl.selectFolder(str(gyoker))
    yield ctl, gyoker, tmp_path / "picasa"
    ctl.shutdown()


class TestAMenuParancs:
    def test_MASOLATOT_ir_a_Hatterek_mappaba(self, vezerlo, monkeypatch):
        ctl, gyoker, picasa = vezerlo
        monkeypatch.setattr(wallpaper, "set_desktop_background", lambda b: "feh")
        eszkozok = []
        ctl.desktopBackgroundApplied.connect(eszkozok.append)

        assert ctl.setPhotoAsDesktopBackground(0) is True

        talalatok = list(picasa.glob("*/picasabackground.bmp"))
        assert talalatok, (
            f"a BMP-másolat nem jött létre: {list(picasa.rglob('*'))}"
        )
        assert talalatok[0].parent.name in ("Hátterek", "Backgrounds")
        assert talalatok[0].read_bytes()[:2] == b"BM"
        assert eszkozok == ["feh"]

    def test_az_EREDETI_fajl_erintetlen(self, vezerlo, monkeypatch):
        """Másolat, nem hivatkozás — a mérés szerint az eredeti is így teszi."""
        ctl, gyoker, _picasa = vezerlo
        monkeypatch.setattr(wallpaper, "set_desktop_background", lambda b: "feh")
        elotte = (gyoker / "a.jpg").read_bytes()

        ctl.setPhotoAsDesktopBackground(0)

        assert (gyoker / "a.jpg").read_bytes() == elotte

    def test_ervenytelen_sorra_nem_tesz_semmit(self, vezerlo, monkeypatch):
        ctl, _gyoker, picasa = vezerlo
        monkeypatch.setattr(wallpaper, "set_desktop_background", lambda b: "feh")

        assert ctl.setPhotoAsDesktopBackground(99) is False
        assert not list(picasa.rglob("picasabackground.bmp"))

    def test_sikertelen_beallitasnal_a_BMP_utjat_adja(self, vezerlo, monkeypatch):
        ctl, _gyoker, _picasa = vezerlo
        monkeypatch.setattr(wallpaper, "set_desktop_background", lambda b: None)
        utak = []
        ctl.desktopBackgroundFailed.connect(utak.append)

        assert ctl.setPhotoAsDesktopBackground(0) is True
        assert utak and utak[0].endswith("picasabackground.bmp")


class TestAMenutetel:
    def test_a_menutetel_NEM_helyfoglalo(self):
        import picasapy.app

        forras = (
            Path(picasapy.app.__file__).parent
            / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
        ).read_text(encoding="utf-8")
        i = forras.index('text: qsTr("Set as Desktop Background...")')
        blokk = forras[i - 400 : i + 200]

        assert "menuCreateWallpaper" in blokk, "a tételnek objectName-t kell kapnia"
        assert "placeholder: true" not in blokk.split("MenuItem {")[-1], (
            "a tétel már nem helyfoglaló — a parancs megvan (#1775)"
        )
