"""#4890: a mappa rendezése egyszeri, a rács a kézi sorrendet olvassa.

A régi globális rendezési QSettings-kulcsok elavultak, az AppController
nem teszi többé QML-ből állíthatóvá őket. A „Rendezés alapja” menü
`sortFolderBy` parancsa egyszer rendezi át a célmappát, majd az ini
`priority=` értékeiben tárolja az eredményt. A tesztek a régi kulcsok
eltávolítását és a belső rácsmodell mappa-feedre korlátozott működését őrzik.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from support.jpeg_factory import make_jpeg


# A mappán belül a FÁJLNÉV-sorrend és a FELVÉTELI DÁTUM sorrendje
# szándékosan ELTÉR — csak így látszik, melyiket követi a rács.
_NYARALAS = (
    # fájlnév, felvétel, képméret (a fájlméret-rendezéshez)
    ("a_2024.jpg", "2024:06:01 10:00:00", (8, 6)),
    ("b_2010.jpg", "2010:06:01 10:00:00", (64, 48)),
    ("c_2018.jpg", "2018:06:01 10:00:00", (32, 24)),
)


@pytest.fixture
def library(tmp_path):
    """Két mappa: a `nyaralas` három képével és egy másik, `zebra`."""
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    for name, taken, size in _NYARALAS:
        make_jpeg(root / "nyaralas" / name, size=size, taken_at=taken)
    (root / "zebra").mkdir(parents=True)
    make_jpeg(root / "zebra" / "z1.jpg", taken_at="2022:01:01 10:00:00")
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


def _photo_names(controller, folder: str) -> list[str]:
    """A mappa képeinek sorrendje a rácsban — EZ a menü hatóköre."""
    return [
        photo.name
        for photo in controller.photos.photos
        if Path(photo.folder_path).name == folder
    ]


class TestARacsModellKapuja:
    """A `PhotoGridModel` csak akkor rendez át, ha a nézet megengedi."""

    def test_kikapcsolt_kapunal_erintetlen_marad_a_sorrend(self, qt_app):
        from picasapy.app.models import PhotoGridModel

        model = PhotoGridModel()
        model.set_folder_photo_sort("date", False, is_active=lambda: False)
        eredeti = _minta_kepek()
        model.set_photos(eredeti)
        assert [p.name for p in model.photos] == [p.name for p in eredeti]

    def test_bekapcsolt_kapunal_a_blokkon_belul_rendez(self, qt_app):
        from picasapy.app.models import PhotoGridModel

        model = PhotoGridModel()
        model.set_folder_photo_sort("date", False, is_active=lambda: True)
        model.set_photos(_minta_kepek())
        assert [p.name for p in model.photos] == [
            "b_2010.jpg",
            "c_2018.jpg",
            "a_2024.jpg",
        ]

    def test_a_beallitas_a_MAR_lathato_kepekre_azonnal_ervenyesul(self, qt_app):
        from picasapy.app.models import PhotoGridModel

        model = PhotoGridModel()
        model.set_photos(_minta_kepek())
        model.set_folder_photo_sort("date", False, is_active=lambda: True)
        assert [p.name for p in model.photos][0] == "b_2010.jpg"


def _minta_kepek() -> tuple:
    """Egy mappa három képe: a fájlnév- és a dátumsorrend eltér."""
    from picasapy.index import PhotoRecord

    return tuple(
        PhotoRecord(
            id=i,
            folder_path="/kepek/nyaralas",
            name=name,
            kind="photo",
            size=10,
            mtime_ns=0,
            star=False,
            caption=None,
            keywords=None,
            rotate_steps=0,
            filters=None,
            taken_at=taken,
            orientation=1,
            width=8,
            height=6,
        )
        for i, (name, taken) in enumerate(
            (
                ("a_2024.jpg", "2024-06-01T10:00:00"),
                ("b_2010.jpg", "2010-06-01T10:00:00"),
                ("c_2018.jpg", "2018-06-01T10:00:00"),
            )
        )
    )


class TestAzUjrainditasNemOrziAGlobalModot:
    def test_a_globalis_racsmod_vezerlopontok_megszuntek(self, controller):
        assert not hasattr(controller, "folderPhotoSort")
        assert not hasattr(controller, "folderPhotoSortReverse")
        assert not hasattr(controller, "setFolderPhotoSort")
        assert not hasattr(controller, "toggleFolderPhotoSortReverse")

    def test_a_regi_globalis_mod_nem_rendezi_at_minden_mappat(
        self, qt_app, tmp_path, library
    ):
        """A sorrend a priority értékekben él, a régi nézetmód kulcsai elavultak."""
        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import open_index, sync_tree
        from picasapy.thumbs import ThumbnailCache

        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library)
        beallitas_fajl = str(tmp_path / "settings.ini")
        settings = QSettings(beallitas_fajl, QSettings.Format.IniFormat)
        settings.setValue("view/folderPhotoSort", "date")
        settings.setValue("view/folderPhotoSortReverse", True)
        settings.sync()

        def _uj_vezerlo():
            ctl = AppController(
                tmp_path / "index.db",
                (str(library),),
                ThumbnailProvider(
                    ThumbnailCache(tmp_path / "thumbs", size=32)
                ),
                settings=QSettings(
                    beallitas_fajl, QSettings.Format.IniFormat
                ),
                watched_file=tmp_path / "WatchedFolders.txt",
            )
            ctl._reload()
            ctl.selectFolder(str(library / "nyaralas"))
            return ctl

        elso = _uj_vezerlo()
        assert settings.value("view/folderPhotoSort") is None
        assert settings.value("view/folderPhotoSortReverse") is None
        assert _photo_names(elso, "nyaralas") == [
            "a_2024.jpg",
            "b_2010.jpg",
            "c_2018.jpg",
        ]
        assert elso.sortFolderBy(str(library / "nyaralas"), "date") is True
        assert _photo_names(elso, "nyaralas") == [
            "b_2010.jpg",
            "c_2018.jpg",
            "a_2024.jpg",
        ]

        masodik = _uj_vezerlo()
        assert settings.value("view/folderPhotoSort") is None
        assert settings.value("view/folderPhotoSortReverse") is None
        assert _photo_names(masodik, "nyaralas") == [
            "b_2010.jpg",
            "c_2018.jpg",
            "a_2024.jpg",
        ]
