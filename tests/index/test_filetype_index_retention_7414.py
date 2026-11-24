"""#7414: Fájltípus kikapcsolásakor az index sorai maradnak meg,

és visszakapcsoláskor a fájlok újraolvasás nélkül jelennek meg.
"""

from __future__ import annotations

from picasapy.index import open_index, sync_tree
from picasapy.scanner.filetypes import FILETYPE_GROUPS
import picasapy.index.sync_photos as sync_photos_module


def test_kikapcsolt_tipus_sora_megmarad_az_indexben_es_valodi_torles_torlodik(tmp_path):
    root = tmp_path / "kepek"
    folder = root / "nyaralas"
    folder.mkdir(parents=True)
    (folder / "kep.jpg").write_bytes(b"jpeg-adat")
    (folder / "kep.cr2").write_bytes(b"raw-adat")
    (folder / "film.mp4").write_bytes(b"movie-adat")
    (folder / "torolt.mp4").write_bytes(b"torlendo-film")

    db_path = tmp_path / "index.db"
    with open_index(db_path) as conn:
        # 1. Teljes kezdő szinkron, minden típus engedélyezett
        sync_tree(
            conn,
            root,
            incremental=False,
            enabled_filetypes=set(FILETYPE_GROUPS),
        )
        nevek_elejen = {
            row["name"] for row in conn.execute("SELECT name FROM photos").fetchall()
        }
        assert nevek_elejen == {"kep.jpg", "kep.cr2", "film.mp4", "torolt.mp4"}

        # 2. torolt.mp4-et ténylegesen letöröljük a lemezről
        (folder / "torolt.mp4").unlink()

        # 3. Szinkron kikapcsolt 'movies' és 'raw' típusokkal
        sync_tree(
            conn,
            root,
            incremental=True,
            enabled_filetypes=set(FILETYPE_GROUPS) - {"raw", "movies"},
        )

        nevek_kikapcsolas_utan = {
            row["name"] for row in conn.execute("SELECT name FROM photos").fetchall()
        }
        # Kész 1: a lemezen megmaradt kep.cr2 és film.mp4 sora MEGMARAD az indexben!
        # A ténylegesen törölt torolt.mp4 sora viszont TÖRLŐDIK!
        assert "kep.cr2" in nevek_kikapcsolas_utan
        assert "film.mp4" in nevek_kikapcsolas_utan
        assert "torolt.mp4" not in nevek_kikapcsolas_utan
        assert nevek_kikapcsolas_utan == {"kep.jpg", "kep.cr2", "film.mp4"}


def test_visszakapcsolaskor_nem_olvas_ujra_metaadatot(tmp_path, monkeypatch):
    root = tmp_path / "kepek"
    folder = root / "nyaralas"
    folder.mkdir(parents=True)
    (folder / "kep.jpg").write_bytes(b"jpeg-adat")
    (folder / "film.mp4").write_bytes(b"movie-adat")

    db_path = tmp_path / "index.db"
    with open_index(db_path) as conn:
        sync_tree(
            conn,
            root,
            incremental=False,
            enabled_filetypes=set(FILETYPE_GROUPS),
        )
        # Kikapcsoljuk a filmet
        sync_tree(
            conn,
            root,
            incremental=True,
            enabled_filetypes=set(FILETYPE_GROUPS) - {"movies"},
        )
        assert {r["name"] for r in conn.execute("SELECT name FROM photos")} == {
            "kep.jpg",
            "film.mp4",
        }

        # Figyeljük, hogy a visszakapcsoláskor meghívja-e az upsert_values-t a film.mp4-re
        eredeti_photo_upsert_values = sync_photos_module._photo_upsert_values
        olvasott_nevek = []

        def spy_photo_upsert_values(folder_id, scan, media, ini_fields):
            olvasott_nevek.append(media.name)
            return eredeti_photo_upsert_values(folder_id, scan, media, ini_fields)

        monkeypatch.setattr(
            sync_photos_module, "_photo_upsert_values", spy_photo_upsert_values
        )

        # Visszakapcsoljuk a filmet
        sync_tree(
            conn,
            root,
            incremental=True,
            enabled_filetypes=set(FILETYPE_GROUPS),
        )

        # Kész 2: a változatlan film.mp4-hez nem kell újraolvasni a metaadatot
        assert "film.mp4" not in olvasott_nevek


def test_mappaszamlalo_kikapcsolt_tipus_eseten_helyes(tmp_path):
    from picasapy.app.folder_list_model import FolderListModel

    root = tmp_path / "kepek"
    folder1 = root / "vegyes"
    folder2 = root / "csak_film"
    folder1.mkdir(parents=True)
    folder2.mkdir(parents=True)
    (folder1 / "kep.jpg").write_bytes(b"jpeg")
    (folder1 / "film.mp4").write_bytes(b"movie")
    (folder2 / "film.mp4").write_bytes(b"movie")

    db_path = tmp_path / "index.db"
    with open_index(db_path) as conn:
        sync_tree(conn, root, incremental=False, enabled_filetypes=set(FILETYPE_GROUPS))

        # 1. Bekapcsolt filmekkel: vegyes mappa = 2 elem, csak_film mappa = 1 elem
        model = FolderListModel()
        model.load(conn, enabled_filetypes=set(FILETYPE_GROUPS))
        counts = {row[2]: row[3] for row in model._rows if row[0] == "folder"}
        assert counts[str(folder1)] == 2
        assert counts[str(folder2)] == 1

        # 2. Kikapcsolt filmekkel: vegyes mappa = 1 elem (csak a jpg), csak_film mappa nem látszik
        model_szurt = FolderListModel()
        model_szurt.load(conn, enabled_filetypes=set(FILETYPE_GROUPS) - {"movies"})
        counts_szurt = {
            row[2]: row[3] for row in model_szurt._rows if row[0] == "folder"
        }
        assert counts_szurt[str(folder1)] == 1
        assert str(folder2) not in counts_szurt


def test_mappaszamlalo_rejtett_kikapcsolt_tipust_nem_von_le_ketszer(tmp_path):
    """A mappaszám csak a látható képeket számolja: a rejtett, kikapcsolt típusú
    kép nem csökkentheti, és a mappa nem tűnhet el miatta."""
    from picasapy.app.folder_list_model import FolderListModel

    root = tmp_path / "kepek"
    folder = root / "vegyes"
    folder.mkdir(parents=True)
    (folder / "kep.jpg").write_bytes(b"jpeg")
    (folder / "film.mp4").write_bytes(b"movie")

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root, incremental=False, enabled_filetypes=set(FILETYPE_GROUPS))
        conn.execute("UPDATE photos SET hidden = 1 WHERE name = 'film.mp4'")
        conn.commit()

        model = FolderListModel()
        model.load(conn, enabled_filetypes=set(FILETYPE_GROUPS) - {"movies"})
        counts = {row[2]: row[3] for row in model._rows if row[0] == "folder"}

    assert counts[str(folder)] == 1


def test_albumszamlalo_es_recently_updated_levonja_a_kikapcsolt_tipust(tmp_path):
    """A bal sáv album- és Recently Updated számlálója ugyanazt a látható
    halmazt számolja, mint a rács: a kikapcsolt típus sora az indexben marad,
    a számlálóba viszont nem kerülhet bele."""
    from picasapy.index import albums_in_index, count_recently_updated_photos

    token = "604c294a68b0de9cc9222c4714f289d5"
    root = tmp_path / "kepek"
    folder = root / "nyaralas"
    folder.mkdir(parents=True)
    (folder / "kep.jpg").write_bytes(b"jpeg")
    (folder / "film.mp4").write_bytes(b"movie")
    (folder / ".picasa.ini").write_text(
        f"[.album:{token}]\nname=Nyar\ntoken={token}\n"
        f"[kep.jpg]\nalbums={token}\n[film.mp4]\nalbums={token}\n",
        encoding="utf-8",
    )
    mind = set(FILETYPE_GROUPS)
    film_nelkul = mind - {"movies"}

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root, incremental=False, enabled_filetypes=mind)
        conn.execute("UPDATE photos SET mtime_ns = ?", (10**18,))
        conn.commit()

        assert [a.photo_count for a in albums_in_index(conn)] == [2]
        assert (
            [a.photo_count for a in albums_in_index(conn, enabled_filetypes=mind)]
            == [2]
        )
        assert (
            [a.photo_count for a in albums_in_index(conn, enabled_filetypes=film_nelkul)]
            == [1]
        )
        osszes = count_recently_updated_photos(conn, cutoff_ns=0)
        assert osszes == 2
        assert (
            count_recently_updated_photos(
                conn, cutoff_ns=0, enabled_filetypes=film_nelkul
            )
            == 1
        )
        # az index sora végig megmarad
        assert conn.execute("SELECT count(*) FROM photos").fetchone()[0] == 2


def test_kereses_szuri_a_kikapcsolt_tipusokat(tmp_path):
    from picasapy.app.search_controller import SearchMixin
    from picasapy.index.queries import PhotoRecord

    class DummySearchController(SearchMixin):
        def __init__(self, enabled_types):
            self._filetype_scan_snapshot = enabled_types
            self.showHidden = False

    controller = DummySearchController(enabled_types=frozenset({"bmp"}))
    rec1 = PhotoRecord(
        id=1,
        folder_path="/k",
        name="kep.jpg",
        kind="photo",
        size=10,
        mtime_ns=10,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=None,
        orientation=1,
        width=100,
        height=100,
    )
    rec2 = PhotoRecord(
        id=2,
        folder_path="/k",
        name="film.mp4",
        kind="video",
        size=20,
        mtime_ns=20,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=None,
        orientation=1,
        width=100,
        height=100,
    )

    filtered = controller._filter_search_hidden([rec1, rec2])
    # A film.mp4 ki van kapcsolva (csak a bmp csoport engedélyezett; a JPEG
    # nem kapcsolható ki, ezért a kep.jpg mindig látszik)
    assert [r.name for r in filtered] == ["kep.jpg"]

