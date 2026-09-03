"""#2031: a projekt-mappa CSAK a Projektek alatt látszik.

A #1033 bizonyítékkal eldöntötte: a `P2category` **kizáró** — az
eredetiben egy projekt-mappa a `Folders on Disk` gyűjtőben nem szerepel
(`docs/specs/export-parbeszed.md` 12.5). Nálunk a #1029 óta MINDKÉT
helyen ott volt.

⚠️ **Amit ez NEM tesz:** a mappát nem veszi ki az indexből. A kategória
megjelenítési besorolás, nem törlés — a fotóknak, a keresésnek és a
darabszámoknak érintetlenül kell maradniuk.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.collage_output import PROJECTS_CATEGORY
from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    """Egy hétköznapi és egy PROJEKT-mappa, mindkettőben képpel."""
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "a.jpg")
    (root / "Kollázsok").mkdir(parents=True)
    make_jpeg(root / "Kollázsok" / "k1.jpg")
    make_jpeg(root / "Kollázsok" / "k2.jpg")
    (root / "Kollázsok" / ".picasa.ini").write_text(
        f"[Picasa]\nP2category={PROJECTS_CATEGORY}\n", encoding="utf-8"
    )
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db", (str(library),), provider, settings=settings
    )
    # a hasáb-gyűjtemények betöltése adja a projekt-útvonalakat, és az
    # `_apply_side_pane` frissíti újra a Mappák listát (#2031)
    with open_index(tmp_path / "index.db") as conn:
        ctl._load_side_pane(conn)
    return ctl


def _mappa_utak(controller) -> list[str]:
    modell = controller.folders
    return [
        modell.data(modell.index(i, 0), modell.PathRole)
        for i in range(modell.rowCount())
        if modell.data(modell.index(i, 0), modell.KindRole) == "folder"
    ]


class TestAProjektMappaKimaradAMappakbol:
    def test_a_hetkoznapi_mappa_OTT_van(self, controller, library):
        assert str(library / "nyaralas") in _mappa_utak(controller)

    def test_a_projekt_mappa_NINCS_a_listaban(self, controller, library):
        assert str(library / "Kollázsok") not in _mappa_utak(controller), (
            "a projekt-mappa a Mappák listában is szerepel — a P2category "
            "az eredetiben KIZÁRÓ (#1033)"
        )

    def test_PONTOSAN_EGY_csomopont_alatt_szerepel(self, controller, library):
        """A jegy őr-tesztje: se kétszer, se sehol."""
        ut = str(library / "Kollázsok")
        mappakban = _mappa_utak(controller).count(ut)
        projektekben = sum(1 for m in controller.projectFolders if m["path"] == ut)
        assert (mappakban, projektekben) == (0, 1)


class TestSEMMI_NEM_VESZ_EL:
    """A kategória megjelenítési besorolás, nem törlés."""

    def test_a_mappa_az_INDEXBEN_marad(self, controller, library, tmp_path):
        from picasapy.index import open_index
        from picasapy.index.queries import photos_in_folder

        with open_index(tmp_path / "index.db") as conn:
            fotok = photos_in_folder(conn, library / "Kollázsok")
        assert len(fotok) == 2

    def test_a_projekt_mappa_MEGNYITHATO(self, controller, library):
        """A Projektek alól ugyanaz a rács nyílik.

        ⚠️ A rács a TELJES könyvtár-feedet mutatja, és a választott
        mappához csak ODAGÖRGET (#64) — tehát nem a sorszám a mérce,
        hanem hogy a mappa képei ott vannak-e, és a nézet rá áll-e."""
        controller.selectFolder(str(library / "Kollázsok"))
        assert controller.currentFolder == str(library / "Kollázsok")
        nevek = {
            controller.photos.data(
                controller.photos.index(i, 0), controller.photos.NameRole
            )
            for i in range(controller.photos.rowCount())
        }
        assert {"k1.jpg", "k2.jpg"} <= nevek

    def test_a_DARABSZAM_a_projektek_alatt_helyes(self, controller, library):
        ut = str(library / "Kollázsok")
        tetel = next(m for m in controller.projectFolders if m["path"] == ut)
        assert tetel["count"] == 2

    def test_a_KERESES_tovabbra_is_megtalalja(self, controller, library, tmp_path):
        from picasapy.index import open_index
        from picasapy.index.queries import photos_in_folder

        with open_index(tmp_path / "index.db") as conn:
            nevek = {f.name for f in photos_in_folder(conn, library / "Kollázsok")}
        assert nevek == {"k1.jpg", "k2.jpg"}
