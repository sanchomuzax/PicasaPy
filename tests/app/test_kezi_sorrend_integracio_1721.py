"""#1721 — a kézi sorrend a VALÓDI vezérlőn: húzás → ini → rács.

A `test_kezi_sorrend_1721.py` a számítást méri Qt nélkül; ez a fájl azt,
hogy a lánc a végén ÖSSZEÁLL: a `reorderPhotos` hívás után a mappa
`.picasa.ini`-jében ott a `priority=`, a rács SORRENDJE a húzást követi, és
a rendezés „kézi sorrend"-re állt.

A fixture a `test_folder_photo_sort_1436.py` mintája (valódi index, valódi
JPEG-ek, valódi ini — mock nélkül).
"""

from __future__ import annotations


import pytest
from PySide6.QtCore import QSettings

from picasapy.ini.document import parse_document
from picasapy.ini.priority import olvasd_a_prioritasokat
from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    for nev in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / "nyaralas" / nev, size=(8, 6))
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(library / "nyaralas"))
    return ctl


def _nevek(controller) -> list[str]:
    return [p.name for p in controller.photos.photos]


def _ini_prioritasok(library) -> dict:
    ini = library / "nyaralas" / ".picasa.ini"
    if not ini.exists():
        return {}
    return olvasd_a_prioritasokat(parse_document(ini.read_text(encoding="utf-8")))


class TestAHuzasHatasa:
    def test_alapallapotban_fajlnev_sorrend(self, controller):
        assert _nevek(controller) == ["a.jpg", "b.jpg", "c.jpg"]

    def test_az_utolso_kep_az_elejere_huzva_ott_is_marad(self, controller, library):
        # a `c.jpg` (2. sor) az `a.jpg` (0. sor) ELÉ
        controller.reorderPhotos([2], 0)

        assert _nevek(controller) == ["c.jpg", "a.jpg", "b.jpg"]

    def test_az_ini_megkapja_a_kezi_helyeket(self, controller, library):
        controller.reorderPhotos([2], 0)

        prioritasok = _ini_prioritasok(library)
        assert set(prioritasok) == {"a.jpg", "b.jpg", "c.jpg"}, (
            "az első húzás a mappát kézi rendbe teszi (bootstrap)"
        )
        assert prioritasok["c.jpg"] < prioritasok["a.jpg"] < prioritasok["b.jpg"]

    def test_a_rendezes_kezi_sorrendre_all(self, controller):
        controller.reorderPhotos([2], 0)

        assert controller.folderPhotoSort == "priority"

    def test_a_masodik_huzas_MAR_csak_egy_kulcsot_ir(self, controller, library):
        """Az ADR szabálya: egy áthelyezés nem írja át az egész mappát. A
        bootstrap után a felezőpontos beszúrás EGY kulcsot mozdít."""
        controller.reorderPhotos([2], 0)          # bootstrap: c, a, b
        elotte = _ini_prioritasok(library)

        controller.reorderPhotos([0], 2)          # a `c.jpg` a `b.jpg` elé

        utana = _ini_prioritasok(library)
        valtozott = {nev for nev in utana if utana[nev] != elotte.get(nev)}
        assert valtozott == {"c.jpg"}, f"csak a mozgatott kulcs változhat: {valtozott}"
        assert _nevek(controller) == ["a.jpg", "c.jpg", "b.jpg"]

    def test_a_sorrend_ujratoltes_utan_is_megmarad(self, controller, library):
        controller.reorderPhotos([2], 0)
        controller._reload()
        controller.selectFolder(str(library / "nyaralas"))

        assert _nevek(controller) == ["c.jpg", "a.jpg", "b.jpg"]

    def test_ures_kijelolesre_nem_ir(self, controller, library):
        controller.reorderPhotos([], 0)

        assert _ini_prioritasok(library) == {}
        assert _nevek(controller) == ["a.jpg", "b.jpg", "c.jpg"]

    def test_tobb_kep_egyutt_huzva_egymas_mellett_marad(self, controller, library):
        controller.reorderPhotos([1, 2], 0)

        assert _nevek(controller) == ["b.jpg", "c.jpg", "a.jpg"]
