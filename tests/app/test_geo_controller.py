"""A geo-szelet (#30) vezérlő-tesztjei: szűrő, jelölők, `geotag=` írás."""

import pytest
from PySide6.QtCore import QSettings

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "exif.jpg", gps=(47.4979, 19.0402))
    make_jpeg(root / "nyaralas" / "sehol.jpg")
    (root / "varos").mkdir()
    make_jpeg(root / "varos" / "ini.jpg")
    (root / "varos" / ".picasa.ini").write_text(
        "[ini.jpg]\ngeotag=10.5,20.25\n", encoding="utf-8"
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
    return AppController(
        tmp_path / "index.db", (str(library),), provider, settings=settings
    )


class TestShowGeotagged:
    def test_filter_shows_only_located_photos(self, controller):
        controller.showGeotagged()
        names = {photo.name for photo in controller.photos.photos}
        assert names == {"exif.jpg", "ini.jpg"}

    def test_filter_is_active_with_status(self, controller):
        controller.showGeotagged()
        assert controller.filterActive is True
        assert controller.filterStatusText

    def test_clear_filter_returns_to_library(self, controller):
        controller.showGeotagged()
        controller.clearFilter()
        assert controller.filterActive is False


class TestGeoMarkers:
    def test_markers_follow_the_visible_photos(self, controller, library):
        """A rács a teljes feedet mutatja (#64) — a jelölők is azt tükrözik:
        minden LÁTSZÓ kép, amelynek van helye, jelölőt kap."""
        controller.selectFolder(str(library / "varos"))
        markers = {m["name"]: m for m in controller.geoMarkers}
        assert set(markers) == {"exif.jpg", "ini.jpg"}
        assert markers["ini.jpg"]["latitude"] == pytest.approx(10.5)
        photos = controller.photos.photos
        # a jelölő sorindexe a rács tényleges sorára mutat
        assert photos[markers["ini.jpg"]["row"]].name == "ini.jpg"

    def test_photos_without_location_are_not_markers(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        names = {m["name"] for m in controller.geoMarkers}
        assert "sehol.jpg" not in names
        assert controller.geoMarkerCount == len(names)

    def test_markers_are_a_list_for_qml(self, controller):
        # #232 tanulsága: a tuple QML-ben NEM tömb
        assert isinstance(controller.geoMarkers, list)

    def test_location_of_row(self, controller, library):
        controller.selectFolder(str(library / "varos"))
        row = next(
            index
            for index, photo in enumerate(controller.photos.photos)
            if photo.name == "ini.jpg"
        )
        assert controller.locationOfRow(row)["longitude"] == pytest.approx(20.25)
        assert controller.locationOfRow(999) is None


class TestSetGeotag:
    def test_writes_ini_and_updates_index(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        rows = [
            index
            for index, photo in enumerate(controller.photos.photos)
            if photo.name == "sehol.jpg"
        ]
        controller.setGeotagRows(rows, 12.5, -7.25)
        ini = (library / "nyaralas" / ".picasa.ini").read_text(encoding="utf-8")
        assert "geotag=12.5,-7.25" in ini
        located = {
            photo.name
            for photo in controller.photos.photos
            if photo.location is not None
        }
        assert "sehol.jpg" in located

    def test_many_rows_at_once(self, controller, library):
        """Több kijelölt kép — akkor is, ha KÜLÖNBÖZŐ mappában vannak.

        A rács a #64 óta a teljes könyvtárat mutatja (végtelen feed), ezért a
        sorindexek nem a kiválasztott mappán belül értendők: a köteg több
        mappa ini-jét is érintheti. A teszt korábban egyetlen mappa ini-jét
        nézte, és emiatt hibásan „elveszett írást" jelzett (#331).
        """
        controller.selectFolder(str(library / "nyaralas"))
        rows_by_folder = {}
        for row, photo in enumerate(controller.photos.photos):
            rows_by_folder.setdefault(photo.folder_path, []).append(row)
        assert len(rows_by_folder) >= 2, "a feed több mappát fog át"

        picked = [rows[0] for rows in rows_by_folder.values()][:2]
        controller.setGeotagRows(picked, 1.0, 2.0)

        written = sum(
            (library / folder / ".picasa.ini").read_text(encoding="utf-8").count(
                "geotag=1,2"
            )
            for folder in ("nyaralas", "varos")
        )
        assert written == 2, "mindkét kijelölt kép megkapta a helyet"

    def test_many_rows_in_the_same_folder(self, controller, library):
        """Ugyanabban a mappában lévő két kép: egyetlen ini, két bejegyzés."""
        controller.selectFolder(str(library / "nyaralas"))
        rows = [
            row
            for row, photo in enumerate(controller.photos.photos)
            if photo.folder_path.endswith("nyaralas")
        ]
        assert len(rows) == 2
        controller.setGeotagRows(rows, 1.0, 2.0)
        ini = (library / "nyaralas" / ".picasa.ini").read_text(encoding="utf-8")
        assert ini.count("geotag=1,2") == 2

    def test_invalid_coordinates_are_reported(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        seen = []
        controller.geoWriteFailed.connect(seen.append)
        controller.setGeotagRows([0], 120.0, 0.0)
        assert seen and seen[0]
        ini = library / "nyaralas" / ".picasa.ini"
        assert not ini.exists() or "geotag" not in ini.read_text(encoding="utf-8")

    def test_empty_selection_writes_nothing(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.setGeotagRows([], 1.0, 2.0)
        ini = library / "nyaralas" / ".picasa.ini"
        assert not ini.exists() or "geotag" not in ini.read_text(encoding="utf-8")


class TestClearGeotag:
    def test_removes_the_key_only(self, controller, library):
        controller.selectFolder(str(library / "varos"))
        row = next(
            index
            for index, photo in enumerate(controller.photos.photos)
            if photo.name == "ini.jpg"
        )
        controller.clearGeotagRows([row])
        ini = (library / "varos" / ".picasa.ini").read_text(encoding="utf-8")
        assert "geotag" not in ini
        photo = {p.name: p for p in controller.photos.photos}["ini.jpg"]
        assert photo.location is None

    def test_exif_location_survives_clearing(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        rows = [
            index
            for index, photo in enumerate(controller.photos.photos)
            if photo.name == "exif.jpg"
        ]
        controller.setGeotagRows(rows, 1.0, 2.0)
        controller.clearGeotagRows(rows)
        photo = {p.name: p for p in controller.photos.photos}["exif.jpg"]
        assert photo.location is not None
        assert photo.location.latitude == pytest.approx(47.4979, abs=1e-4)
