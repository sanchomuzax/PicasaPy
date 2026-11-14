"""Az albumsor Időrend-dátuma az első tagságkor rögzül (#6914)."""

from picasapy.index import albums_in_index, open_index, sync_tree
from support.jpeg_factory import make_jpeg

_TOKEN = "69146914691469146914691469146914"


def _album_ini(folder, members):
    lines = [
        f"[.album:{_TOKEN}]",
        "name=Utazás",
        f"token={_TOKEN}",
        "date=2018-01-02T03:04:05",
    ]
    for name in members:
        lines.extend((f"[{name}]", f"albums={_TOKEN}"))
    (folder / ".picasa.ini").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _album(conn):
    return next(album for album in albums_in_index(conn) if album.token == _TOKEN)


def test_album_timeline_date_freezes_at_first_membership_across_add_and_delete(
    tmp_path,
):
    library = tmp_path / "library"
    folder = library / "album"
    folder.mkdir(parents=True)
    make_jpeg(folder / "2020.jpg", taken_at="2020:06:15 10:00:00")
    _album_ini(folder, ("2020.jpg",))

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library, incremental=False)
        assert _album(conn).date == "2018-01-02T03:04:05"
        assert _album(conn).timeline_date.startswith("2020-06-15")

        make_jpeg(folder / "2010.jpg", taken_at="2010:04:03 08:00:00")
        _album_ini(folder, ("2020.jpg", "2010.jpg"))
        sync_tree(conn, library, incremental=False)
        assert _album(conn).timeline_date.startswith("2020-06-15")

        (folder / "2020.jpg").unlink()
        _album_ini(folder, ("2010.jpg",))
        sync_tree(conn, library, incremental=False)
        assert _album(conn).timeline_date.startswith("2020-06-15")


def test_empty_album_date_is_set_when_first_membership_arrives(tmp_path):
    library = tmp_path / "library"
    folder = library / "album"
    folder.mkdir(parents=True)
    make_jpeg(folder / "2020.jpg", taken_at="2020:06:15 10:00:00")
    _album_ini(folder, ())

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library, incremental=False)
        assert _album(conn).timeline_date is None

        _album_ini(folder, ("2020.jpg",))
        sync_tree(conn, library, incremental=False)
        assert _album(conn).timeline_date.startswith("2020-06-15")


def test_schema_migration_backfills_current_nonempty_album_date(tmp_path):
    library = tmp_path / "library"
    folder = library / "album"
    folder.mkdir(parents=True)
    make_jpeg(folder / "2020.jpg", taken_at="2020:06:15 10:00:00")
    _album_ini(folder, ("2020.jpg",))
    database = tmp_path / "index.db"

    with open_index(database) as conn:
        sync_tree(conn, library, incremental=False)
        conn.execute("DROP TABLE album_timeline_dates")
        conn.execute("PRAGMA user_version = 27")
        conn.commit()

    with open_index(database) as conn:
        assert _album(conn).timeline_date.startswith("2020-06-15")
