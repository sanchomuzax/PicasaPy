"""„Olvasatlan" mappajelölő — #1644.

A tulajdonos élő megfigyelése (2026-08-27): *„amikor létrejött egy új kép,
a másolat, és a Picasa észrevette és importálta, a mappa neve a bal sávban
kövér (bold) szövegű lett."*

A db3-ban van hozzá oszlop: **`albumdata_unread`** (PMP-típus `0x03`, 1
bájt/rekord; a tulajdonos valódi adatában 330 az 1-es a 2366-ból).

## ⚠️ Amit a jegy HATÓKÖRÖN KÍVÜLRE tett

Hogy az eredeti pontosan MIKOR állítja vissza a jelölőt, **nincs kimérve**.
A jegy a mappa megnyitását írja elő ésszerű alapértelmezésként, és
kimondja: ha egy későbbi kör mást mér, a mérés győz. A forrás ezt a
bizonytalanságot ki is mondja — ezt itt teszt őrzi, hogy egy későbbi kör ne
higgye mértnek.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QSettings

from picasapy.index import open_index, sync_tree
from picasapy.index.schema import MIGRATIONS, SCHEMA_VERSION
from support.jpeg_factory import make_jpeg

_CTL = (
    Path(picasapy.app.__file__).parent / "controller.py"
).read_text(encoding="utf-8")
_PANE = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "FolderPane.qml"
).read_text(encoding="utf-8")


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "a.jpg")
    return root


def _unread(db_path, folder) -> bool:
    with open_index(db_path) as conn:
        sor = conn.execute(
            "SELECT unread FROM folders WHERE path = ?", (str(folder),)
        ).fetchone()
    return bool(sor["unread"]) if sor is not None else False


class TestAzIndex:
    def test_a_sema_ismeri_az_oszlopot(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            oszlopok = {
                sor[1]
                for sor in conn.execute("PRAGMA table_info(folders)")
            }
        assert "unread" in oszlopok

    def test_a_semaverzio_lepett(self):
        """A #1644 lépése MEGVAN — de nem rögzítjük a MAI verziószámot.

        Az egzakt egyenlőség (`== 15`) minden későbbi sémabővítéstől
        elbukott volna, holott ennek a jegynek a lépéséhez semmi köze:
        a #1494 v16-ra emelése például pontosan ezen akadt el. A
        MAI verziót szándékosan EGY helyen rögzítjük
        (`tests/index/test_hashes.py`); itt az a kérdés, hogy a saját
        migrációnk a helyén van-e.
        """
        assert 14 in MIGRATIONS, "a #1644 migrációs lépése eltűnt"
        assert "unread" in MIGRATIONS[14]
        assert SCHEMA_VERSION >= 15


class TestAJelolo:
    def test_uj_kep_utan_OLVASATLAN(self, tmp_path, library):
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, library)
        assert _unread(db, library / "nyaralas") is True

    def test_valtozatlan_mappa_ujraolvasasa_NEM_allitja_be(
        self, tmp_path, library
    ):
        """A jelölő az ÚJDONSÁGRÓL szól. Ha egy második szinkron minden
        mappát újra megjelölne, a kövér szedés elveszítené a jelentését."""
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, library)
            conn.execute("UPDATE folders SET unread = 0")
            conn.commit()
        with open_index(db) as conn:
            sync_tree(conn, library)
        assert _unread(db, library / "nyaralas") is False

    def test_MASODIK_uj_kep_ujra_megjeloli(self, tmp_path, library):
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, library)
            conn.execute("UPDATE folders SET unread = 0")
            conn.commit()
        make_jpeg(library / "nyaralas" / "b.jpg")
        with open_index(db) as conn:
            sync_tree(conn, library)
        assert _unread(db, library / "nyaralas") is True


class TestAVisszaallas:
    @pytest.fixture
    def controller(self, qt_app, tmp_path, library):
        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache

        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library)
        provider = ThumbnailProvider(
            ThumbnailCache(tmp_path / "thumbs", size=32)
        )
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        ctl = AppController(
            tmp_path / "index.db",
            (str(library),),
            provider,
            settings=settings,
            watched_file=tmp_path / "WatchedFolders.txt",
        )
        ctl._reload()
        yield ctl
        assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"

    def test_a_mappa_megnyitasa_TORLI(self, controller, tmp_path, library):
        mappa = library / "nyaralas"
        # ⚠️ A jelölőt ITT állítjuk vissza 1-re, nem a fixture-re hagyjuk:
        # a vezérlő indulása MAGA is megnyit egy mappát (session/lastFolder),
        # tehát a friss indexelés jelölőjét már törölhette. A teszt tárgya a
        # MEGNYITÁS hatása, nem az indulásé.
        with open_index(tmp_path / "index.db") as conn:
            conn.execute(
                "UPDATE folders SET unread = 1 WHERE path = ?", (str(mappa),)
            )
            conn.commit()
        assert _unread(tmp_path / "index.db", mappa) is True

        controller.selectFolder(str(mappa))

        assert _unread(tmp_path / "index.db", mappa) is False

    def test_ures_utvonalra_nem_esik_szet(self, controller):
        controller._clear_unread("")  # nem dobhat kivételt

    def test_ismeretlen_mappara_sem(self, controller, tmp_path):
        controller._clear_unread(str(tmp_path / "nincs-ilyen"))


class TestAFelulet:
    def test_a_szerep_eljut_a_sorig(self):
        assert "required property bool unread" in _PANE

    def test_a_nev_KOVER_ha_olvasatlan(self):
        assert "font.bold: unread" in _PANE

    def test_a_modell_adja_a_szerepet(self):
        modellek = (
            Path(picasapy.app.__file__).parent / "models.py"
        ).read_text(encoding="utf-8")
        assert "UnreadRole" in modellek
        assert 'self.UnreadRole: b"unread"' in modellek


class TestAKimondottBizonytalansag:
    def test_a_forras_kimondja_hogy_a_visszaallas_NINCS_kimerve(self):
        """A jegy hatókörön kívülre tette; a kód ne állítsa mértnek."""
        kezd = _CTL.index("self._clear_unread(folder_path)")
        elotte = _CTL[max(0, kezd - 700) : kezd]
        assert "NINCS" in elotte and "kimérve" in elotte
        assert "a mérés győz" in elotte
