"""A PhotoRecord példányonkénti tárigénye (#6699)."""

from picasapy.index import open_index, photos_in_folder, sync_tree
from support.jpeg_factory import make_jpeg


def test_photo_record_nem_tarol_peldany_szintu_dictet():
    from picasapy.index import PhotoRecord

    assert not hasattr(PhotoRecord.__new__(PhotoRecord), "__dict__")


def test_egy_mappaban_a_rekordok_megosztjak_a_folder_path_szoveget(tmp_path):
    folder = tmp_path / "kepek"
    folder.mkdir()
    make_jpeg(folder / "a.jpg", size=(8, 8))
    make_jpeg(folder / "b.jpg", size=(8, 8))

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, folder)
        records = photos_in_folder(conn, folder)

    assert len(records) == 2
    assert records[0].folder_path is records[1].folder_path
