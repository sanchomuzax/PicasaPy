"""Címke megjelenítése albumként (#1406).

MÉRVE (`0x005d8330`, 869 bájt): a parancs bekéri egy címkét, és abból
**rendes albumot** készít — nem élő szűrőt. Három külön szöveg tartozik
hozzá, mindegyik a saját helyén:

| kulcs | magyar |
|---|---|
| `eMenuTools::ID_SEARCHTOKEN` | „&Címke megjelenítése albumként…" (menüfelirat) |
| `ThumbUI::addsearchtoken` | „Keresési címke hozzáadása" (a párbeszéd címe) |
| `CAlbumState::addsearchprompt` | „Írja be az albumként megjelenítendő címkét" |

A színkeresés (#1399) fordítottja: ott a menüpont a keresőmezőbe ír, itt a
címkéből album lesz.
"""

from __future__ import annotations

import pytest
from support.jpeg_factory import make_jpeg

from picasapy.index import open_index, photos_with_keyword, sync_tree


@pytest.fixture
def konyvtar(tmp_path):
    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    make_jpeg(gyoker / "a.jpg")
    make_jpeg(gyoker / "b.jpg")
    make_jpeg(gyoker / "c.jpg")
    (gyoker / ".picasa.ini").write_text(
        "[a.jpg]\nkeywords=nyár,tenger\n[b.jpg]\nkeywords=Nyár\n"
        "[c.jpg]\nkeywords=nyaralás\n",
        encoding="utf-8",
    )
    return gyoker


class TestALekerdezes:
    def test_TETELENKENT_egyezik_nem_reszszora(self, konyvtar, tmp_path):
        """A „nyár" ne húzza be a „nyaralás"-t.

        Ez a lényeg: a `keywords` oszlop vesszővel tagolt lista, és egy
        `LIKE '%nyár%'` a „nyaralás"-t is találatnak vennék."""
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, konyvtar)
            nevek = {r.name for r in photos_with_keyword(conn, "nyár")}

        assert nevek == {"a.jpg", "b.jpg"}, (
            f"a részszavas egyezés hibás találatot ad: {nevek}"
        )

    def test_kis_nagybetu_nem_szamit(self, konyvtar, tmp_path):
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, konyvtar)
            assert {r.name for r in photos_with_keyword(conn, "NYÁR")} == {
                "a.jpg",
                "b.jpg",
            }

    def test_ures_cimkere_nincs_talalat(self, konyvtar, tmp_path):
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, konyvtar)
            assert photos_with_keyword(conn, "   ") == ()


class TestAzAlbum:
    @pytest.fixture
    def vezerlo(self, qt_app, tmp_path, konyvtar):
        from PySide6.QtCore import QSettings

        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache

        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, konyvtar)
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        ctl = AppController(
            tmp_path / "index.db",
            (str(konyvtar),),
            provider,
            settings=settings,
            watched_file=tmp_path / "WatchedFolders.txt",
        )
        yield ctl
        ctl.shutdown()

    def test_a_cimkebol_RENDES_album_lesz(self, vezerlo, konyvtar):
        token = vezerlo.showTagAsAlbum("nyár")

        assert token, "nem jött létre album"
        nevek = [a["name"] for a in vezerlo.albums]
        assert "nyár" in nevek, f"az album neve a címke legyen: {nevek}"
        # a tagság az ini-be került (rendes album, nem élő szűrő)
        ini = (konyvtar / ".picasa.ini").read_text(encoding="utf-8")
        assert token[:8] in ini, (
            "az albumtagság nem került a `.picasa.ini`-be — akkor ez élő "
            "szűrő, nem rendes album"
        )

    def test_ismeretlen_cimkere_nem_keszul_album(self, vezerlo):
        assert vezerlo.showTagAsAlbum("nincs-ilyen-cimke") == ""

    def test_ures_cimkere_sem(self, vezerlo):
        assert vezerlo.showTagAsAlbum("  ") == ""
