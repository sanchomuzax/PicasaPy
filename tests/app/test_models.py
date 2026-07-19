"""QML-modellek: mappa-lista és fotórács az SQLite indexből."""

import pytest

from picasapy.index import open_index, photos_in_folder, sync_tree

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    (root / "telek").mkdir()
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg", taken_at="2025:05:01 07:00:00")
    make_jpeg(root / "nyaralas" / "IMG_0002.jpg")
    make_jpeg(root / "telek" / "IMG_0100.jpg")
    (root / "nyaralas" / ".picasa.ini").write_text("[IMG_0001.jpg]\nstar=yes\n", encoding="utf-8")
    return root


@pytest.fixture
def conn(tmp_path, library):
    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, library)
        yield connection


class TestFolderListModel:
    def test_lists_folders_with_counts(self, qt_app, conn, library):
        from picasapy.app.models import FolderListModel

        model = FolderListModel()
        model.load(conn)
        # dátum-rendezés: a 2025-ös nyaralas évsort kap és elöl áll,
        # a dátumtalan telek a lista végére kerül
        assert model.rowCount() == 3
        assert model.data(model.index(0, 0), FolderListModel.KindRole) == "year"
        first = model.index(1, 0)
        assert model.data(first, FolderListModel.NameRole) == "nyaralas"
        assert model.data(first, FolderListModel.CountRole) == 2
        assert model.data(first, FolderListModel.PathRole).endswith("nyaralas")

    def test_year_separator_rows(self, qt_app, conn):
        # Picasa: évszám-elválasztó sorok az év-prefixű mappák előtt.
        from picasapy.app.models import FolderListModel

        for path in ("/k/2025-05-xx", "/k/2025-07-xx", "/k/2026-01-xx", "/k/egyeb"):
            conn.execute("INSERT INTO folders(path) VALUES (?)", (path,))
        conn.commit()
        model = FolderListModel()
        model.load(conn)
        rows = [
            (
                model.data(model.index(i, 0), FolderListModel.KindRole),
                model.data(model.index(i, 0), FolderListModel.NameRole),
            )
            for i in range(model.rowCount())
        ]
        assert ("year", "2025") in rows
        assert ("year", "2026") in rows
        assert rows.index(("year", "2025")) < rows.index(("folder", "2025-05-xx"))
        assert rows.index(("year", "2026")) < rows.index(("folder", "2026-01-xx"))
        # nem év-prefixű mappa nem kap elválasztót maga elé
        assert ("year", "egye") not in rows

    def test_default_sort_is_date_desc(self, qt_app, conn):
        # Picasa-alapértelmezés: létrehozási dátum szerint, legújabb elöl;
        # az évszám-elválasztók a mappa-DÁTUM évéből jönnek.
        from picasapy.app.models import FolderListModel

        for path, date in (
            ("/k/regi", "2020-03-01T10:00:00"),
            ("/k/uj", "2025-01-15T08:00:00"),
            ("/k/kozep", "2023-06-01T08:00:00"),
        ):
            conn.execute(
                "INSERT INTO folders(path, date) VALUES (?, ?)", (path, date)
            )
        conn.commit()
        model = FolderListModel()
        model.load(conn)
        rows = [
            (
                model.data(model.index(i, 0), FolderListModel.KindRole),
                model.data(model.index(i, 0), FolderListModel.NameRole),
            )
            for i in range(model.rowCount())
        ]
        folder_order = [n for k, n in rows if k == "folder" and n.startswith(("regi", "uj", "kozep"))]
        assert folder_order == ["uj", "kozep", "regi"]
        assert rows.index(("year", "2025")) < rows.index(("folder", "uj"))

    def test_sort_by_name(self, qt_app, conn):
        from picasapy.app.models import FolderListModel

        for path, date in (("/k/b", "2025-01-01T00:00:00"), ("/k/a", "2020-01-01T00:00:00")):
            conn.execute("INSERT INTO folders(path, date) VALUES (?, ?)", (path, date))
        conn.commit()
        model = FolderListModel()
        model.load(conn, sort_mode="name")
        names = [
            model.data(model.index(i, 0), FolderListModel.NameRole)
            for i in range(model.rowCount())
            if model.data(model.index(i, 0), FolderListModel.KindRole) == "folder"
        ]
        assert names.index("a") < names.index("b")

    def test_sort_reversed(self, qt_app, conn):
        from picasapy.app.models import FolderListModel

        for path, date in (("/k/b", "2025-01-01T00:00:00"), ("/k/a", "2020-01-01T00:00:00")):
            conn.execute("INSERT INTO folders(path, date) VALUES (?, ?)", (path, date))
        conn.commit()
        model = FolderListModel()
        model.load(conn, sort_mode="date", reverse=True)
        names = [
            model.data(model.index(i, 0), FolderListModel.NameRole)
            for i in range(model.rowCount())
            if model.data(model.index(i, 0), FolderListModel.KindRole) == "folder"
        ]
        assert names.index("a") < names.index("b")  # legrégebbi elöl

    def test_windows_path_folder_name(self, qt_app, conn):
        # Importált (Windows-os) útvonal is értelmes nevet adjon.
        from picasapy.app.models import FolderListModel

        conn.execute(
            "INSERT INTO folders(path) VALUES ('C:\\Users\\sancho\\Pictures')"
        )
        conn.commit()
        model = FolderListModel()
        model.load(conn)
        names = [
            model.data(model.index(i, 0), FolderListModel.NameRole)
            for i in range(model.rowCount())
        ]
        assert "Pictures" in names

    def test_empty_model(self, qt_app):
        from picasapy.app.models import FolderListModel

        assert FolderListModel().rowCount() == 0


class TestPhotoGridModel:
    def test_photo_roles(self, qt_app, conn, library):
        from picasapy.app.models import PhotoGridModel

        model = PhotoGridModel()
        model.set_photos(photos_in_folder(conn, library / "nyaralas"))
        assert model.rowCount() == 2
        first = model.index(0, 0)
        assert model.data(first, PhotoGridModel.NameRole) == "IMG_0001.jpg"
        assert model.data(first, PhotoGridModel.StarRole) is True
        assert model.data(first, PhotoGridModel.ThumbUrlRole).startswith(
            "image://thumbs/"
        )
        assert model.data(first, PhotoGridModel.IsVideoRole) is False
        assert model.data(first, PhotoGridModel.FileUrlRole).startswith("file://")
        assert model.data(first, PhotoGridModel.FileUrlRole).endswith(
            "/nyaralas/IMG_0001.jpg"
        )

    def test_keywords_and_resolution_roles(self, qt_app, conn, library):
        from picasapy.app.models import PhotoGridModel

        model = PhotoGridModel()
        model.set_photos(photos_in_folder(conn, library / "nyaralas"))
        first = model.index(0, 0)
        assert model.data(first, PhotoGridModel.ResolutionRole) == "8x6"
        assert model.data(first, PhotoGridModel.KeywordsRole) == ""

    def test_folder_path_role(self, qt_app, conn, library):
        # #7: a rács mappánkénti csoportosításához (GridView section) kell
        # a mappa-útvonal szerepkörként.
        from picasapy.app.models import PhotoGridModel

        model = PhotoGridModel()
        model.set_photos(photos_in_folder(conn, library / "nyaralas"))
        first = model.index(0, 0)
        assert model.data(first, PhotoGridModel.FolderPathRole) == str(
            library / "nyaralas"
        )

    def test_thumb_url_versioned_by_rotation(self, qt_app, conn, library):
        # A forgatás lépésszáma az URL-ben van, hogy a QML kép-cache frissüljön.
        from picasapy.app.models import PhotoGridModel

        model = PhotoGridModel()
        model.set_photos(photos_in_folder(conn, library / "nyaralas"))
        url = model.data(model.index(0, 0), PhotoGridModel.ThumbUrlRole)
        assert "?r=0" in url  # #59 óta a filters-tag is az URL része

    def test_rotate_at(self, qt_app, conn, library):
        from picasapy.app.models import PhotoGridModel

        model = PhotoGridModel()
        model.set_photos(photos_in_folder(conn, library / "nyaralas"))
        assert model.rotateAt(0) == 0
        assert model.rotateAt(-1) == 0

    def test_star_at(self, qt_app, conn, library):
        from picasapy.app.models import PhotoGridModel

        model = PhotoGridModel()
        model.set_photos(photos_in_folder(conn, library / "nyaralas"))
        assert model.starAt(0) is True
        assert model.starAt(1) is False
        assert model.starAt(-1) is False

    def test_thumb_url_at(self, qt_app, conn, library):
        from picasapy.app.models import PhotoGridModel

        model = PhotoGridModel()
        model.set_photos(photos_in_folder(conn, library / "nyaralas"))
        assert model.thumbUrlAt(0).startswith("image://thumbs/")
        assert model.thumbUrlAt(-1) == ""

    def test_caption_at(self, qt_app, conn, library):
        from picasapy.app.models import PhotoGridModel

        model = PhotoGridModel()
        model.set_photos(photos_in_folder(conn, library / "nyaralas"))
        assert model.captionAt(0) == ""
        assert model.captionAt(-1) == ""

    def test_set_photos_resets(self, qt_app, conn, library):
        from picasapy.app.models import PhotoGridModel

        model = PhotoGridModel()
        model.set_photos(photos_in_folder(conn, library / "nyaralas"))
        model.set_photos(photos_in_folder(conn, library / "telek"))
        assert model.rowCount() == 1
        assert (
            model.data(model.index(0, 0), PhotoGridModel.NameRole) == "IMG_0100.jpg"
        )


class TestFolderListModelStability:
    def test_reload_unchanged_no_reset(self, qt_app, conn):
        # 10-es issue: a háttér-szinkron minden körben újratöltötte a
        # modellt akkor is, ha semmi sem változott — a reset eldobja a
        # delegate-eket és nullázza a görgetést (a lista "ugrál").
        from picasapy.app.models import FolderListModel

        model = FolderListModel()
        model.load(conn)
        resets = []
        model.modelReset.connect(lambda: resets.append(1))
        counts = []
        model.folderCountChanged.connect(lambda: counts.append(1))
        model.load(conn)
        assert resets == [], "változatlan adatnál nem szabad resetelni"
        assert counts == []

    def test_reload_changed_still_resets(self, qt_app, conn):
        from picasapy.app.models import FolderListModel

        model = FolderListModel()
        model.load(conn)
        conn.execute("INSERT INTO folders(path) VALUES ('/k/uj-mappa')")
        conn.commit()
        resets = []
        model.modelReset.connect(lambda: resets.append(1))
        model.load(conn)
        assert resets == [1]


class TestFolderListNavigation:
    """#77: kurzor/görgő léptetés a mappalistán — modell-szintű navigáció."""

    def test_neighbor_folder_steps_over_year_rows(self, qt_app, conn):
        # Az évszám-elválasztó sorok nem léptethetők — a szomszéd mindig
        # valódi mappa.
        from picasapy.app.models import FolderListModel

        model = FolderListModel()
        model.load(conn)
        folders = list(model.folder_paths())
        assert len(folders) >= 2
        assert model.neighborFolder(folders[0], 1) == folders[1]
        assert model.neighborFolder(folders[1], -1) == folders[0]

    def test_neighbor_folder_clamps_at_edges(self, qt_app, conn):
        from picasapy.app.models import FolderListModel

        model = FolderListModel()
        model.load(conn)
        folders = list(model.folder_paths())
        assert model.neighborFolder(folders[0], -1) == folders[0]
        assert model.neighborFolder(folders[-1], 1) == folders[-1]

    def test_neighbor_folder_unknown_path_gives_first(self, qt_app, conn):
        from picasapy.app.models import FolderListModel

        model = FolderListModel()
        model.load(conn)
        folders = list(model.folder_paths())
        assert model.neighborFolder("", 1) == folders[0]
        assert model.neighborFolder("/nincs/ilyen", -1) == folders[0]

    def test_neighbor_folder_empty_model(self, qt_app):
        from picasapy.app.models import FolderListModel

        assert FolderListModel().neighborFolder("/x", 1) == ""

    def test_row_of_path(self, qt_app, conn):
        from picasapy.app.models import FolderListModel

        model = FolderListModel()
        model.load(conn)
        folders = list(model.folder_paths())
        row = model.rowOfPath(folders[0])
        assert row >= 0
        assert model.data(model.index(row, 0), FolderListModel.PathRole) == folders[0]
        assert model.rowOfPath("/nincs/ilyen") == -1


class TestPhotoGridNavigation:
    """#77: kurzorgombos léptetés célsora a rács-feedben (mappánkénti
    csoportok, rácssor-ugrás fel/le, folytonos balra/jobbra)."""

    @pytest.fixture
    def feed_model(self, qt_app, tmp_path):
        # A mappa: 5 kép (3 oszlopnál sorok: [0,1,2], [3,4]);
        # B mappa: 3 kép (start=5, egyetlen sor: [5,6,7]).
        from picasapy.app.models import PhotoGridModel

        root = tmp_path / "feedlib"
        (root / "a-mappa").mkdir(parents=True)
        (root / "b-mappa").mkdir()
        for i in range(5):
            make_jpeg(root / "a-mappa" / f"a{i}.jpg")
        for i in range(3):
            make_jpeg(root / "b-mappa" / f"b{i}.jpg")
        with open_index(tmp_path / "feed.db") as connection:
            sync_tree(connection, root)
            photos = photos_in_folder(
                connection, root / "a-mappa"
            ) + photos_in_folder(connection, root / "b-mappa")
        model = PhotoGridModel()
        model.set_photos(photos)
        return model

    def test_left_right_are_continuous_across_groups(self, feed_model):
        assert feed_model.navigate(0, "right", 3) == 1
        assert feed_model.navigate(4, "right", 3) == 5  # átlép a B mappába
        assert feed_model.navigate(5, "left", 3) == 4
        assert feed_model.navigate(0, "left", 3) == 0   # elején megáll
        assert feed_model.navigate(7, "right", 3) == 7  # végén megáll

    def test_down_within_group_jumps_a_row(self, feed_model):
        assert feed_model.navigate(1, "down", 3) == 4
        # csonka utolsó sor: az oszlop alatt nincs kép → az utolsóra lép
        assert feed_model.navigate(2, "down", 3) == 4

    def test_down_crosses_group_keeps_column(self, feed_model):
        assert feed_model.navigate(3, "down", 3) == 5
        assert feed_model.navigate(4, "down", 3) == 6
        assert feed_model.navigate(6, "down", 3) == 6  # utolsó csoport alja

    def test_up_within_and_across_groups(self, feed_model):
        assert feed_model.navigate(4, "up", 3) == 1
        assert feed_model.navigate(5, "up", 3) == 3  # az A utolsó sorába
        assert feed_model.navigate(7, "up", 3) == 4  # oszlop-csonkolással
        assert feed_model.navigate(0, "up", 3) == 0

    def test_invalid_row_starts_at_first_photo(self, feed_model):
        # Kijelölés nélkül (−1) az első képre lép — a rács-navigáció innen
        # indul.
        assert feed_model.navigate(-1, "down", 3) == 0
        assert feed_model.navigate(99, "right", 3) == 0

    def test_empty_model_and_bad_direction(self, qt_app, feed_model):
        from picasapy.app.models import PhotoGridModel

        assert PhotoGridModel().navigate(0, "down", 3) == -1
        assert feed_model.navigate(2, "semerre", 3) == 2
        assert feed_model.navigate(2, "down", 0) == 3  # oszlopszám min. 1


class TestFolderListMatches:
    """#49: keresés közben a mappalista csak a találatos mappákat mutatja,
    a darabszám a találatok száma."""

    def _groups(self):
        from picasapy.app.search_results import SearchGroup

        return (
            SearchGroup("/k/nyaralas", "nyaralas", 0, None, ("r1", "r2")),
            SearchGroup("/k/telek", "telek", 2, None, ("r3",)),
        )

    def test_load_matches_rows_and_counts(self, qt_app):
        from picasapy.app.models import FolderListModel

        model = FolderListModel()
        model.load_matches(self._groups())
        assert model.rowCount() == 2
        first = model.index(0, 0)
        assert model.data(first, FolderListModel.KindRole) == "folder"
        assert model.data(first, FolderListModel.NameRole) == "nyaralas"
        assert model.data(first, FolderListModel.CountRole) == 2
        assert model.folderCount == 2

    def test_load_matches_unchanged_no_reset(self, qt_app):
        from picasapy.app.models import FolderListModel

        model = FolderListModel()
        model.load_matches(self._groups())
        resets = []
        model.modelReset.connect(lambda: resets.append(1))
        model.load_matches(self._groups())
        assert resets == []
