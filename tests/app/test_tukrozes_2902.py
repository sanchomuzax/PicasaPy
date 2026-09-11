"""#2902: tükrözés — a kijelölésre hat, veszteségmentes, és nincs menüpontja.

Az eredeti két billentyűt szán rá (`Ctrl+Shift+H` vízszintes,
`Ctrl+Shift+V` függőleges), menüpontot nem. Ez az őr a láncot méri: a
vezérlő átváltja a jelzőt az indexben, a bélyegkép-URL változik (különben a
Qt a régi képet mutatná), az export beégeti, és a menüben nem jelenik meg
semmi.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import picasapy.app
import pytest
from PySide6.QtCore import QSettings

from picasapy.render.flip import FLIP_HORIZONTAL, FLIP_VERTICAL
from support.jpeg_factory import make_jpeg

_QML = Path(picasapy.app.__file__).parent / "qml"
_MENU = (_QML / "PicasaPy" / "PicasaMenuBar.qml").read_text(encoding="utf-8")


@pytest.fixture
def controller(qt_app, tmp_path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    gyoker = tmp_path / "kepek"
    mappa = gyoker / "a"
    mappa.mkdir(parents=True)
    make_jpeg(mappa / "egy.jpg", size=(120, 90))
    make_jpeg(mappa / "ketto.jpg", size=(120, 90))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, gyoker)
    ctl = AppController(
        tmp_path / "index.db",
        (str(gyoker),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(mappa))
    yield ctl
    ctl.waitForBackgroundWorkers(20.0)


def _sor(controller, nev: str) -> int:
    for index, photo in enumerate(controller.photos.photos):
        if photo.name == nev:
            return index
    raise AssertionError(f"nincs ilyen kép: {nev}")


def _jelzo(controller, nev: str) -> int:
    return controller.photos.photos[_sor(controller, nev)].flip_flags


class TestAKijelolesreHat:
    def test_a_vizszintes_a_MERT_erteket_allitja(self, controller):
        controller.flipHorizontalMany([_sor(controller, "egy.jpg")])
        assert _jelzo(controller, "egy.jpg") == FLIP_HORIZONTAL

    def test_MINDEN_kijelolt_kep_megkapja(self, controller):
        controller.flipVerticalMany([0, 1])
        assert [p.flip_flags for p in controller.photos.photos] == [
            FLIP_VERTICAL, FLIP_VERTICAL
        ]

    def test_ketszer_ugyanaz_VISSZAALLIT(self, controller):
        """A tükrözés önmaga inverze — ezért nem kell külön „vissza"."""
        sor = _sor(controller, "egy.jpg")
        controller.flipHorizontalMany([sor])
        controller.flipHorizontalMany([sor])
        assert _jelzo(controller, "egy.jpg") == 0

    def test_a_ket_irany_egymas_mellett_all(self, controller):
        sor = _sor(controller, "egy.jpg")
        controller.flipHorizontalMany([sor])
        controller.flipVerticalMany([sor])
        assert _jelzo(controller, "egy.jpg") == FLIP_HORIZONTAL | FLIP_VERTICAL

    def test_ures_kijelolesnel_a_MERT_uzenet_jon(self, controller):
        """Az eredeti megmondja (`IDS_MUST_SELECT_TO_ROT`); a forgatásnál már
        bevált jelzést használjuk, nem némán térünk vissza."""
        kapott = []
        controller.rotationNeedsSelection.connect(lambda: kapott.append(True))
        controller.flipHorizontalMany([])
        assert kapott == [True]


class TestAJelzoTOVABBEL:
    def test_az_ujraszkenneles_MEGORZI(self, controller, tmp_path):
        """A jelző az indexben él; egy mappa-resync nem írja felül (nem
        ini-eredetű mező). Ha ez elromlik, a tükrözés minden szkennelésnél
        elvesznék."""
        from picasapy.index import open_index, sync_tree

        sor = _sor(controller, "egy.jpg")
        controller.flipHorizontalMany([sor])
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, tmp_path / "kepek")
        controller.selectFolder(str(tmp_path / "kepek" / "a"))
        assert _jelzo(controller, "egy.jpg") == FLIP_HORIZONTAL


class TestABelyegkepUrl:
    def test_a_jelzo_BENNE_van(self, controller):
        """A Qt az URL alapján gyorstáraz: ha a jelző nem látszik benne, a
        tükrözött kép helyett a régi maradna a rácson."""
        from picasapy.app.models import _thumb_url

        sor = _sor(controller, "egy.jpg")
        elotte = _thumb_url(controller.photos.photos[sor])
        controller.flipHorizontalMany([sor])
        utana = _thumb_url(controller.photos.photos[sor])
        assert elotte != utana
        assert f"fl={FLIP_HORIZONTAL}" in utana


class TestAzExportBeegeti:
    def test_a_kimenet_tukrozott(self, tmp_path):
        """A mentett/exportált fájl egyezzen azzal, amit a rácson látunk."""
        from picasapy.export.exporter import ExportItem, ExportSettings, export_photos
        from picasapy.lazy_cv2 import cv2

        mappa = tmp_path / "be"
        mappa.mkdir()
        forras = mappa / "a.jpg"
        make_jpeg(forras, size=(64, 32))
        eredeti = cv2.imread(str(forras))

        cel = tmp_path / "ki"
        report = export_photos(
            (ExportItem(source=forras, flip_flags=FLIP_HORIZONTAL),),
            cel,
            ExportSettings(),
        )
        assert report.exported, report.reasons
        kimenet = cv2.imread(str(report.exported[0]))
        assert kimenet.shape == eredeti.shape
        # a JPEG újratömörít, ezért nem bitre, hanem MINTÁRA mérünk: a
        # tükrözött kimenet bal széle az eredeti JOBB széléhez áll közelebb
        bal = kimenet[:, :4].astype(float)
        assert np.abs(bal - eredeti[:, -4:][:, ::-1].astype(float)).mean() < 12.0


def test_a_menuben_NINCS_tukrozes():
    """A 3.9 menüiben nincs ilyen parancs — nálunk sem lehet (a jegy 4.
    pontja kimondottan tiltja)."""
    for szo in ("Flip Horizontal", "Flip Vertical", "Tükrözés"):
        assert szo not in _MENU
