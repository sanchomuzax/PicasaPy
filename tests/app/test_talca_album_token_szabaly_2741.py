"""#2741 — MIKOR mutatja a tálca az összecsukott tokent (a mért szabály).

Az eredetiben ez nem parancs, hanem minden frissítéskor újraértékelt
állapot: a `scratch/album` réteg küldöttje (`0x00572ba4` → `0x00563530`)
akkor mutat (`4`), ha

* van album-/mappa-kijelölés (`CThumbUI+0xEAC` nem NULL), ÉS
* annak tömbje nem üres, ÉS
* a KÉP-kijelölés (`CThumbUI+0xEA4`) üres.

A 230. kutatói kör (PR #2789) fordította le a mi fogalmainkra: a `+0xeac`
az eredetiben is EXPLICIT kijelölés (hét hívója közt a kollázs és a
feltöltési kijelölés), nem „hol vagyok" állapot — nálunk ennek a
`currentAlbumToken` felel meg. Tehát:

    a token látszik  ⇔  currentAlbumToken !== ""  ÉS  nincs kijelölt kép

⚠️ Ez szándékosan NEM a megnyitott mappára szól: a mindennapi
mappanézetben a tálca megszokott kinézete nem változik.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

import picasapy.app
from support.jpeg_factory import make_jpeg

_TRAYBAR = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "TrayBar.qml"
).read_text(encoding="utf-8")


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    mappa = root / "a"
    mappa.mkdir(parents=True)
    make_jpeg(mappa / "x.jpg", size=(320, 240))
    make_jpeg(mappa / "y.jpg", size=(320, 240))
    return root, mappa


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    root, _mappa = library
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
    return ctl


def _album(controller, mappa):
    """Album a két képből — a token-szabály album-kijelölésre szól."""
    controller.selectFolder(str(mappa))
    token = controller.createAlbum("Nyár", [0, 1])
    assert token, "az album nem jött létre"
    return token


class TestASzabaly:
    def test_album_kijelolesre_MEGJELENIK(self, controller, library):
        _root, mappa = library
        token = _album(controller, mappa)
        assert controller.showSelectedAlbumToken(token) is True
        tokenek = controller.trayAlbumTokens
        assert len(tokenek) == 1
        assert tokenek[0]["key"] == token
        assert tokenek[0]["isAlbum"] is True
        assert tokenek[0]["photoCount"] == 2

    def test_URES_tokenre_ELTUNIK(self, controller, library):
        _root, mappa = library
        token = _album(controller, mappa)
        controller.showSelectedAlbumToken(token)
        assert controller.showSelectedAlbumToken("") is False
        assert controller.trayAlbumTokens == []

    def test_kep_kijelolesre_ELTUNIK(self, controller, library):
        """A mért szabály: amint egy kép ki van jelölve, a bélyegképek
        veszik át a token helyét. A tálca-mag ezt magától megteszi — az
        automatikus token NEM `held`."""
        _root, mappa = library
        token = _album(controller, mappa)
        controller.showSelectedAlbumToken(token)
        controller.syncSelection([0])
        assert controller.trayAlbumTokens == []

    def test_masik_albumra_CSERELODIK(self, controller, library):
        _root, mappa = library
        token = _album(controller, mappa)
        controller.showSelectedAlbumToken(token)
        controller.selectFolder(str(mappa))
        masik = controller.createAlbum("Tél", [0])
        assert masik and masik != token
        controller.showSelectedAlbumToken(masik)
        tokenek = controller.trayAlbumTokens
        assert len(tokenek) == 1, "két album-token egyszerre nem állhat ki"
        assert tokenek[0]["key"] == masik

    def test_ures_albumra_NEM_tesz_ki_semmit(self, controller):
        """Üres token üres dobozként jelenne meg — semmit nem mondana."""
        assert controller.showSelectedAlbumToken("nincs-ilyen") is False
        assert controller.trayAlbumTokens == []

    def test_a_KEZZEL_osszecsukott_mappa_tokent_NEM_viszi_el(
        self, controller, library
    ):
        """A #1919 kézi belépője `held` tokent tesz ki — az szándékos
        gyűjtés, azt a szabály nem söpörheti el."""
        _root, mappa = library
        assert controller.collapseFolderIntoTray(str(mappa)) is True
        controller.showSelectedAlbumToken("")
        kulcsok = [t["key"] for t in controller.trayAlbumTokens]
        assert kulcsok == [str(mappa)]


class TestABekotes:
    def test_a_savon_all_a_szabaly_nem_a_fooblak_fajlban(self):
        """A tálca a sáv felelőssége (#455 mintája) — a forró `Main.qml`-hez
        nem nyúlunk."""
        assert "showSelectedAlbumToken" in _TRAYBAR

    def test_MIND_A_KET_bemenetre_ujraertekel(self):
        """A mért szabály két feltételt figyel; ha csak az egyikre
        frissítenénk, a token hazug állapotban ragadna."""
        assert "onAlbumTokenOrEmptyChanged" in _TRAYBAR
        blokk = _TRAYBAR[_TRAYBAR.index("function syncAlbumToken()") :][:700]
        assert "selectedIndexesOrEmpty.length === 0" in blokk
        assert "albumTokenOrEmpty" in blokk
