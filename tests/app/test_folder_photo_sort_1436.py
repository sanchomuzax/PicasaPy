"""#1436: a „Mappa rendezésének alapja ▸" a mappa TARTALMÁT rendezi.

A tulajdonos éles használatban jelezte, hogy a menüpont nálunk „mintha a
MAPPÁKAT rendezné, nem a mappa TARTALMÁT". A mérés igazolta: a menü a
`setFolderSort`-ot hívta, ami a rács MAPPA-sorrendjét állítja (#321) — a
mappán belüli képsorrend MINDEN beállításnál fájlnév szerinti maradt.

Ez a fájl az az ŐR, amelyik KIMONDJA a hatókört és az irányt, hogy a
„mappa vs. tartalom" tévesztés ne tudjon csendben visszatérni:

* HATÓKÖR — a `Folder::SortFolderBy` menü a mappa KÉPEIT rendezi; a mappák
  egymáshoz viszonyított sorrendjét NEM mozdítja (azt a Nézet ▸ Mappanézet
  `folderSort`-ja és a bal hasáb `paneSort`-ja állítja).
* IRÁNY — az alapérték NÖVEKVŐ: dátumnál a legrégebbi elöl, a LEGÚJABB a
  VÉGÉN (a tulajdonos megfigyelése a Picasa 3-ról); a „Fordított sorrend"
  fordítja meg.
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


def _folder_order(controller) -> list[str]:
    """A MAPPÁK sorrendje a rácsban — ehhez a menünek NEM szabad nyúlnia."""
    seen: list[str] = []
    for photo in controller.photos.photos:
        name = Path(photo.folder_path).name
        if name not in seen:
            seen.append(name)
    return seen


class TestAHatokorAMappaTartalma:
    """A menü a mappa KÉPEIT rendezi, nem a mappákat."""

    def test_a_datum_a_mappa_KEPEIT_rendezi(self, controller):
        controller.setFolderPhotoSort("date")
        # a legrégebbi (2010) elöl, a LEGÚJABB (2024) a VÉGÉN
        assert _photo_names(controller, "nyaralas") == [
            "b_2010.jpg",
            "c_2018.jpg",
            "a_2024.jpg",
        ]

    def test_a_datum_a_MAPPAK_sorrendjet_nem_mozditja(self, controller):
        before = _folder_order(controller)
        controller.setFolderPhotoSort("date")
        assert _folder_order(controller) == before
        controller.setFolderPhotoSort("size")
        assert _folder_order(controller) == before

    def test_a_nev_a_mappa_kepeit_rendezi_novekvo_sorrendben(self, controller):
        # a dátumon ÁT vissza a névre — így a próba tényleg a váltást méri,
        # nem az alapállapotot
        controller.setFolderPhotoSort("date")
        controller.setFolderPhotoSort("name")
        assert _photo_names(controller, "nyaralas") == [
            "a_2024.jpg",
            "b_2010.jpg",
            "c_2018.jpg",
        ]

    def test_a_meret_a_mappa_kepeit_rendezi_a_legkisebbtol(self, controller):
        controller.setFolderPhotoSort("size")
        sizes = [
            photo.size
            for photo in controller.photos.photos
            if Path(photo.folder_path).name == "nyaralas"
        ]
        assert sizes == sorted(sizes)


class TestAzIranyNovekvo:
    """Az alapérték NÖVEKVŐ; a „Fordított sorrend" fordítja meg."""

    def test_a_datum_alapbol_a_legujabbat_teszi_a_VEGERE(self, controller):
        controller.setFolderPhotoSort("date")
        assert _photo_names(controller, "nyaralas")[-1] == "a_2024.jpg"

    def test_a_forditott_sorrend_a_legujabbat_hozza_ELORE(self, controller):
        controller.setFolderPhotoSort("date")
        controller.toggleFolderPhotoSortReverse()
        assert _photo_names(controller, "nyaralas") == [
            "a_2024.jpg",
            "c_2018.jpg",
            "b_2010.jpg",
        ]

    def test_a_forditas_sem_mozditja_a_MAPPAK_sorrendjet(self, controller):
        controller.setFolderPhotoSort("date")
        before = _folder_order(controller)
        controller.toggleFolderPhotoSortReverse()
        assert _folder_order(controller) == before


class TestAKetRendezesFuggetlen:
    """A mappa-menü (tartalom) és a Mappanézet (mappák) két külön beállítás."""

    def test_a_kepsorrend_valtasa_nem_irja_at_a_folderSortot(self, controller):
        before = controller.folderSort
        controller.setFolderPhotoSort("date")
        assert controller.folderSort == before

    def test_a_mappanezet_valtasa_nem_irja_at_a_kepsorrendet(self, controller):
        controller.setFolderPhotoSort("date")
        controller.setFolderSort("name")
        assert controller.folderPhotoSort == "date"
        assert _photo_names(controller, "nyaralas") == [
            "b_2010.jpg",
            "c_2018.jpg",
            "a_2024.jpg",
        ]


class TestAHatokorNemLepiTulAMappaFeedet:
    """A mappa-menü rendezése a rácsra (mappa-feed) szól — máshova nem.

    A keresési találatoknál ez nem ízlés kérdése: a `groups_to_qml` a
    sorindexeket a rendezetlen rekordokból számolja, tehát ha a modell
    átrendezné a találatokat, a néző MÁS képet nyitna meg, mint amire a
    felhasználó kattintott.
    """

    def test_a_keresesi_talalatok_sorrendjet_nem_irja_at(self, controller):
        controller.setFolderPhotoSort("date")
        # a mappanévre keresve a mappa MINDEN képe találat — így a
        # dátum- és a névsorrend eltérése tényleg látszana
        controller.search("nyaralas")
        nevek = [photo.name for photo in controller.photos.photos]
        assert nevek == ["a_2024.jpg", "b_2010.jpg", "c_2018.jpg"]

    def test_a_kereses_sorindexei_a_racs_soraira_mutatnak(self, controller):
        controller.setFolderPhotoSort("date")
        controller.search("nyaralas")
        racs = controller.photos.photos
        assert len(racs) == 3
        parok = [
            (elem["row"], elem["name"])
            for csoport in controller.searchGroups
            for elem in csoport["photos"]
        ]
        assert len(parok) == 3
        for row, name in parok:
            assert racs[row].name == name


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


class TestAzUjrainditasMegorziABeallitast:
    def test_a_kepsorrend_a_kovetkezo_inditaskor_is_ervenyes(
        self, qt_app, tmp_path, library
    ):
        """A menüpont hatása perzisztens — különben minden indítás után
        visszaesne a fájlnév-sorrendre."""
        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import open_index, sync_tree
        from picasapy.thumbs import ThumbnailCache

        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library)
        beallitas_fajl = str(tmp_path / "settings.ini")

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
        elso.setFolderPhotoSort("date")
        elso.toggleFolderPhotoSortReverse()

        masodik = _uj_vezerlo()
        assert masodik.folderPhotoSort == "date"
        assert masodik.folderPhotoSortReverse is True
        # a legújabb elöl — a fordított irány is visszatért
        assert _photo_names(masodik, "nyaralas") == [
            "a_2024.jpg",
            "c_2018.jpg",
            "b_2010.jpg",
        ]
