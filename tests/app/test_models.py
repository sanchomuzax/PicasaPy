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
    (root / "nyaralas" / ".picasa.ini").write_text("[IMG_0001.jpg]\nstar=yes\n")
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
        assert model.rowCount() == 2
        first = model.index(0, 0)
        assert model.data(first, FolderListModel.NameRole) == "nyaralas"
        assert model.data(first, FolderListModel.CountRole) == 2
        assert model.data(first, FolderListModel.PathRole).endswith("nyaralas")

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

    def test_set_photos_resets(self, qt_app, conn, library):
        from picasapy.app.models import PhotoGridModel

        model = PhotoGridModel()
        model.set_photos(photos_in_folder(conn, library / "nyaralas"))
        model.set_photos(photos_in_folder(conn, library / "telek"))
        assert model.rowCount() == 1
        assert (
            model.data(model.index(0, 0), PhotoGridModel.NameRole) == "IMG_0100.jpg"
        )
