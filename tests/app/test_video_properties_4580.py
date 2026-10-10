"""#4580: a videó hossza, képkockasebessége és formátuma indexelődik."""

import os

import pytest
from PySide6.QtCore import QLocale

from picasapy.app.formatting import properties_entries
from picasapy.index import open_index, photos_in_folder, sync_tree
from support.video_factory import make_mp4


def test_a_videometaadatok_az_indexben_es_a_tulajdonsagok_panelen_megjelennek(
    tmp_path,
):
    library = tmp_path / "kepek"
    library.mkdir()
    make_mp4(library / "proba.mp4", frames=50, fps=25)

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
        photo = photos_in_folder(conn, library)[0]

        assert photo.movie_format == "MP4"
        assert photo.frame_rate == pytest.approx(25.0)
        assert photo.duration_seconds == pytest.approx(2.0)

        rows = properties_entries(photo, QLocale("en"), lambda text: text)
        assert rows[-3:] == [
            ("Movie Info", "MP4"),
            ("Movie Rate", "25 fps"),
            ("Movie Length", "0:02"),
        ]


def test_a_v20_as_index_videofelvetele_incrementalis_szinkronnal_frissul(
    tmp_path,
):
    library = tmp_path / "kepek"
    library.mkdir()
    make_mp4(library / "proba.mp4", frames=50, fps=25)
    database = tmp_path / "index.db"

    with open_index(database) as conn:
        sync_tree(conn, library)
        # Az elavult indexet utánozzuk: a v21-es videóoszlopok hiányoznak,
        # miközben a változatlan mappa inkrementális kihagyási pecsétje él.
        conn.execute("DROP INDEX idx_photos_video_metadata_missing")
        conn.execute("ALTER TABLE photos DROP COLUMN movie_format")
        conn.execute("ALTER TABLE photos DROP COLUMN frame_rate")
        conn.execute("ALTER TABLE photos DROP COLUMN duration_seconds")
        conn.execute("PRAGMA user_version = 20")
        past = 1_700_000_000_000_000_000
        os.utime(library, ns=(past, past))
        conn.execute(
            "UPDATE folder_scan_state SET mtime_ns = ?, ini_mtime_ns = NULL"
            " WHERE path = ?",
            (library.stat().st_mtime_ns, str(library)),
        )
        conn.commit()

    with open_index(database) as conn:
        sync_tree(conn, library, incremental=True)
        photo = photos_in_folder(conn, library)[0]

        assert photo.movie_format == "MP4"
        assert photo.frame_rate == pytest.approx(25.0)
        assert photo.duration_seconds == pytest.approx(2.0)
