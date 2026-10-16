"""#4447 — a Beállítások fájltípus-csoportjai a scan eredményét vezérlik."""

from __future__ import annotations

from picasapy.scanner import scan_tree


def test_kikapcsolt_fajltipusok_nem_kerulnek_a_konyvtarba(tmp_path):
    root = tmp_path / "kepek"
    folder = root / "nyaralas"
    folder.mkdir(parents=True)
    (folder / "kep.jpg").write_bytes(b"jpeg")
    (folder / "kep.cr2").write_bytes(b"raw")
    (folder / "film.mov").write_bytes(b"quicktime")
    (folder / "film.mp4").write_bytes(b"movie")
    (folder / ".picasa.ini").write_text(
        "[kep.jpg]\nstar=yes\n[kep.cr2]\ncaption=megmarad\n",
        encoding="utf-8",
    )

    scans = scan_tree(root, enabled_filetypes={"movies"})

    assert [file.name for file in scans[0].files] == ["film.mp4", "kep.jpg"]
    assert scans[0].has_ini is True


def test_minden_spec_csoport_a_sajat_kiterjeszteseit_eri_el(tmp_path):
    root = tmp_path / "kepek"
    folder = root / "formatumok"
    folder.mkdir(parents=True)
    (folder / "kep.jpg").write_bytes(b"jpeg")
    csoport_fajlok = {
        "bmp": "kep.bmp",
        "gif": "kep.gif",
        "png": "kep.png",
        "tga": "kep.tga",
        "tiff": "kep.tiff",
        "webp": "kep.webp",
        "psd": "kep.psd",
        "raw": "kep.cr2",
        "movies": "film.mp4",
        "quicktime": "film.mov",
    }
    for name in csoport_fajlok.values():
        (folder / name).write_bytes(b"formatum")

    for group, name in csoport_fajlok.items():
        scans = scan_tree(root, enabled_filetypes={group})
        assert {file.name for file in scans[0].files} == {"kep.jpg", name}


def test_csak_kikapcsolt_media_eseten_is_visszaadja_a_mappat(tmp_path):
    root = tmp_path / "kepek"
    folder = root / "csak-raw"
    folder.mkdir(parents=True)
    (folder / "kep.cr2").write_bytes(b"raw")

    scans = scan_tree(root, enabled_filetypes=set())

    assert len(scans) == 1
    assert scans[0].path == folder
    assert scans[0].files == ()


def test_regi_scan_cache_tabla_kiegeszul_a_fajltipus_alairassal(tmp_path):
    from picasapy.index import open_index, sync_tree

    root = tmp_path / "kepek"
    folder = root / "nyaralas"
    folder.mkdir(parents=True)
    (folder / "kep.jpg").write_bytes(b"jpeg")
    adatbazis = tmp_path / "index.db"

    with open_index(adatbazis) as conn:
        conn.execute(
            "CREATE TABLE folder_scan_state ("
            "path TEXT PRIMARY KEY, mtime_ns INTEGER NOT NULL, ini_mtime_ns INTEGER)"
        )
        sync_tree(conn, root, incremental=False, enabled_filetypes={"raw"})
        oszlopok = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(folder_scan_state)")
        }

    assert "filetype_signature" in oszlopok


def test_filetipusvaltas_invalidatealja_az_inkrementalis_kiolvasast(
    tmp_path, monkeypatch
):
    from picasapy.index import open_index, sync_tree
    from picasapy.index import sync as sync_module
    from picasapy.scanner.filetypes import FILETYPE_GROUPS
    from support.jpeg_factory import make_jpeg

    monkeypatch.setattr(sync_module, "_SKIP_SAFETY_NS", 0)
    root = tmp_path / "kepek"
    folder = root / "nyaralas"
    folder.mkdir(parents=True)
    make_jpeg(folder / "kep.jpg", size=(12, 8))
    (folder / "kep.cr2").write_bytes(b"raw-data")
    ini = folder / ".picasa.ini"
    ini_tartalom = "[kep.jpg]\nstar=yes\n[kep.cr2]\ncaption=megmarad\n"
    ini.write_text(ini_tartalom, encoding="utf-8")
    adatbazis = tmp_path / "index.db"

    with open_index(adatbazis) as conn:
        sync_tree(
            conn,
            root,
            incremental=False,
            enabled_filetypes=set(FILETYPE_GROUPS),
        )
        sync_tree(
            conn,
            root,
            incremental=True,
            enabled_filetypes=set(FILETYPE_GROUPS) - {"raw"},
        )
        nevek = {
            sor["name"] for sor in conn.execute("SELECT name FROM photos").fetchall()
        }

    assert nevek == {"kep.jpg"}
    assert ini.read_text(encoding="utf-8") == ini_tartalom
