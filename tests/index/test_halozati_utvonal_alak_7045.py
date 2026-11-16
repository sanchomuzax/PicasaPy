"""#7045 / #7044: ugyanaz a hálózati (UNC) mappa nem kerülhet kétszer az indexbe.

## A hiba

A tulajdonos Windowson látta: a `\\\\DS215j\\photo\\2026\\2026-xx-xx` mappa a bal
hasábban KÉTSZER szerepel (a második, félkövér sor a frissen beolvasott,
`unread`), a súgója csupa kisbetűs (`\\\\ds215j\\...`). Az index `folders.path`
oszlopa kis-nagybetű-érzékeny, a szinkron pedig a gyökeret a `normalize_path`
(`Path.resolve()`) alakjában írta, ami eltérhetett a korábban beírt alaktól. Az
induláskori egyesítés (#507) a keletkező párt összevonta, de a megmaradó sor
az ELSŐ (más) alakot tartotta, a következő szinkron tehát megint újat írt:
minden indításnál újabb beolvasás, lassú indulás és üres rács.

## A rögzítés módja

A Windows-viselkedést a `paths._platform` fogantyúval rögzítjük (#1217). A
szinkron Path-részét `PureWindowsPath`-ra cseréljük, a bejárót pedig kézzel
írt, a kapott gyökérből építkező hamis bejárással, mert Linuxon nincs hálózati
mappa; a fájlrendszeri ágak (elérhetőség) a szinkron saját fogantyúin át
helyettesítettek."""

from __future__ import annotations

import os
import threading
import time
from pathlib import PureWindowsPath

import pytest

from picasapy import paths
from picasapy.index import open_index, sync
from picasapy.index.dedup_folders import (
    merge_duplicate_folders,
    merge_duplicate_folders_under,
)
from picasapy.index.folder_spelling import adopt_indexed_spelling
from picasapy.index.sync_photos import _FolderSyncResult
from picasapy.scanner import FolderScan

EREDETI_GYOKER = "\\\\DS215j\\photo"
KISBETUS_GYOKER = "\\\\ds215j\\photo"
MAPPA = "\\2026\\2026-11-14"
SZERVER = "ds215j"


@pytest.fixture
def windows(monkeypatch):
    monkeypatch.setattr(paths, "_platform", lambda: "win32")


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as connection:
        yield connection


def _folder(conn, path: str, has_ini: int = 1) -> int:
    return conn.execute(
        "INSERT INTO folders(path, has_ini) VALUES (?, ?) RETURNING id",
        (path, has_ini),
    ).fetchone()[0]


def _photo(conn, folder_id: int, name: str, **fields) -> int:
    ertekek = dict(
        kind="image", size=10, mtime_ns=1, star=0, hidden=0, caption_ini=None,
        keywords_ini=None, rotate_steps=0, filters=None, taken_at=None,
        orientation=1, width=None, height=None, caption_file=None,
        keywords_file=None, geotag_ini=None, exif_lat=None, exif_lon=None,
    )
    ertekek.update(fields)
    oszlopok = ["folder_id", "name", *ertekek]
    return conn.execute(
        f"INSERT INTO photos({', '.join(oszlopok)}) "
        f"VALUES ({', '.join('?' for _ in oszlopok)}) RETURNING id",
        [folder_id, name, *ertekek.values()],
    ).fetchone()[0]


def _utak(conn) -> list[str]:
    return [sor["path"] for sor in conn.execute("SELECT path FROM folders ORDER BY id")]


# -- az indexben ismert alak átvétele -----------------------------------------


def test_a_gyoker_az_indexben_latott_alakot_veszi_at(windows, conn):
    _folder(conn, EREDETI_GYOKER + MAPPA)
    assert adopt_indexed_spelling(conn, KISBETUS_GYOKER + "\\") == EREDETI_GYOKER + "\\"
    assert adopt_indexed_spelling(conn, KISBETUS_GYOKER) == EREDETI_GYOKER
    assert adopt_indexed_spelling(conn, KISBETUS_GYOKER + MAPPA) == EREDETI_GYOKER + MAPPA


def test_az_uj_mappa_a_testver_alakjat_orokli_a_maradek_marad(windows, conn):
    _folder(conn, EREDETI_GYOKER + "\\2026\\regi")
    assert (
        adopt_indexed_spelling(conn, KISBETUS_GYOKER + "\\2026\\UJ")
        == EREDETI_GYOKER + "\\2026\\UJ"
    )


def test_ismeretlen_utvonal_valtozatlan_marad(windows, conn):
    _folder(conn, "\\\\MAS\\kepek\\a")
    assert adopt_indexed_spelling(conn, KISBETUS_GYOKER + MAPPA) == KISBETUS_GYOKER + MAPPA


def test_tobb_alak_eseten_a_legregebbi_sor_alakja_nyer(windows, conn):
    _folder(conn, EREDETI_GYOKER + MAPPA)
    _folder(conn, KISBETUS_GYOKER + MAPPA)
    assert adopt_indexed_spelling(conn, "\\\\Ds215J\\PHOTO" + MAPPA) == EREDETI_GYOKER + MAPPA


def test_a_nem_ascii_nevu_gyoker_is_azonosul(windows, conn):
    _folder(conn, "\\\\DS215j\\Képek\\Ékszer\\a")
    assert (
        adopt_indexed_spelling(conn, "\\\\ds215j\\képek\\ékszer\\a")
        == "\\\\DS215j\\Képek\\Ékszer\\a"
    )


def test_posixon_az_atvetel_semmihez_nem_nyul(monkeypatch):
    monkeypatch.setattr(paths, "_platform", lambda: "linux")
    # `conn=None`: bármilyen adatbázis-hozzáférés kivételt dobna
    assert adopt_indexed_spelling(None, KISBETUS_GYOKER + MAPPA) == KISBETUS_GYOKER + MAPPA
    assert adopt_indexed_spelling(None, "/mnt/nas/Kepek") == "/mnt/nas/Kepek"


def test_helyi_windowsos_utvonal_nem_kerul_az_atvetelbe(windows):
    # a helyi `resolve()` már a lemez kis-nagybetűjét adja; nincs mit átvenni
    assert adopt_indexed_spelling(None, "C:\\Kepek\\a") == "C:\\Kepek\\a"


# -- a meglévő duplikátum egyesítése ------------------------------------------


def test_a_ket_alak_egy_sorra_egyesul_es_az_eredeti_alak_marad(windows, conn):
    regi = _folder(conn, EREDETI_GYOKER + MAPPA)
    uj = _folder(conn, KISBETUS_GYOKER + MAPPA)
    _photo(conn, regi, "a.jpg", star=1, caption_ini="felirat")
    # az ÚJ sorban több a fotó: az eredeti alaknak akkor is maradnia kell
    _photo(conn, uj, "a.jpg")
    _photo(conn, uj, "b.jpg", keywords_ini="nyar")
    _photo(conn, uj, "c.jpg")

    jelentes = merge_duplicate_folders(conn)

    assert jelentes.skipped == ()
    assert _utak(conn) == [EREDETI_GYOKER + MAPPA]
    sorok = {
        sor["name"]: sor
        for sor in conn.execute(
            "SELECT p.* FROM photos p JOIN folders f ON f.id = p.folder_id"
        )
    }
    assert set(sorok) == {"a.jpg", "b.jpg", "c.jpg"}
    assert sorok["a.jpg"]["star"] == 1
    assert sorok["a.jpg"]["caption_ini"] == "felirat"
    assert sorok["b.jpg"]["keywords_ini"] == "nyar"


def test_az_egyesites_a_megmarado_sor_scan_allapotat_az_eredeti_alakra_kulcsolja(windows, conn):
    regi = _folder(conn, EREDETI_GYOKER + MAPPA)
    uj = _folder(conn, KISBETUS_GYOKER + MAPPA)
    _photo(conn, uj, "a.jpg")
    _photo(conn, uj, "b.jpg")
    _photo(conn, regi, "a.jpg")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS folder_scan_state ("
        "path TEXT PRIMARY KEY, mtime_ns INTEGER NOT NULL, ini_mtime_ns INTEGER)"
    )
    conn.execute(
        "INSERT INTO folder_scan_state(path, mtime_ns) VALUES (?, 1), (?, 2)",
        (EREDETI_GYOKER + MAPPA, KISBETUS_GYOKER + MAPPA),
    )

    merge_duplicate_folders(conn)

    allapotok = [sor["path"] for sor in conn.execute("SELECT path FROM folder_scan_state")]
    assert allapotok == [EREDETI_GYOKER + MAPPA]


def test_az_arc_es_az_album_tagsag_nem_vesz_el_az_egyesiteskor(windows, conn):
    regi = _folder(conn, EREDETI_GYOKER + MAPPA)
    uj = _folder(conn, KISBETUS_GYOKER + MAPPA)
    megmarado = _photo(conn, regi, "a.jpg")
    # ugyanaz a fájl az új sorban: ott van a névvel ellátott arc és a tagság
    veszto = _photo(conn, uj, "a.jpg")
    _photo(conn, uj, "b.jpg")
    conn.execute(
        "INSERT INTO face(photo_id, rect_left, rect_top, rect_right, rect_bottom,"
        " det_conf, right_eye_x, right_eye_y, left_eye_x, left_eye_y, nose_x,"
        " nose_y, mouth_right_x, mouth_right_y, mouth_left_x, mouth_left_y,"
        " state, person_name) VALUES (?, 0,0,1,1, 0.9, 0,0,0,0,0,0,0,0,0,0,"
        " 'named', 'Anna')",
        (veszto,),
    )
    conn.execute(
        "INSERT INTO face_scan(photo_id, mtime_ns, size, ok) VALUES (?, 1, 10, 'detektalva')",
        (veszto,),
    )
    conn.execute(
        "INSERT INTO albums(folder_id, token, name) VALUES (?, 'tok1', 'Nyar')", (uj,)
    )
    conn.execute(
        "INSERT INTO photo_albums(photo_id, token, place) VALUES (?, 'tok1', 0)", (veszto,)
    )

    assert merge_duplicate_folders(conn).skipped == ()

    arcok = conn.execute("SELECT photo_id, person_name FROM face").fetchall()
    assert [(sor["photo_id"], sor["person_name"]) for sor in arcok] == [(megmarado, "Anna")]
    assert conn.execute("SELECT photo_id FROM face_scan").fetchall()[0]["photo_id"] == megmarado
    assert conn.execute("SELECT photo_id FROM photo_albums").fetchall()[0]["photo_id"] == megmarado


def test_a_megmarado_foto_sajat_arca_elsobbseget_elvez(windows, conn):
    regi = _folder(conn, EREDETI_GYOKER + MAPPA)
    uj = _folder(conn, KISBETUS_GYOKER + MAPPA)
    megmarado = _photo(conn, regi, "a.jpg")
    veszto = _photo(conn, uj, "a.jpg")
    for fotoid, nev in ((megmarado, "Bela"), (veszto, "Anna")):
        conn.execute(
            "INSERT INTO face(photo_id, rect_left, rect_top, rect_right, rect_bottom,"
            " det_conf, right_eye_x, right_eye_y, left_eye_x, left_eye_y, nose_x,"
            " nose_y, mouth_right_x, mouth_right_y, mouth_left_x, mouth_left_y,"
            " state, person_name) VALUES (?, 0,0,1,1, 0.9, 0,0,0,0,0,0,0,0,0,0,"
            " 'named', ?)",
            (fotoid, nev),
        )

    merge_duplicate_folders(conn)

    nevek = [sor["person_name"] for sor in conn.execute("SELECT person_name FROM face")]
    assert nevek == ["Bela"]


def test_a_foto_nelkuli_helyi_album_a_megmarado_sor_utvonalara_kerul(windows, conn):
    _folder(conn, EREDETI_GYOKER + MAPPA)
    _folder(conn, KISBETUS_GYOKER + MAPPA)
    conn.execute(
        "INSERT INTO local_empty_albums(token, folder_path, name) VALUES ('t1', ?, 'Uj album')",
        (KISBETUS_GYOKER + MAPPA,),
    )

    merge_duplicate_folders(conn)

    sor = conn.execute("SELECT folder_path FROM local_empty_albums WHERE token = 't1'").fetchone()
    assert sor["folder_path"] == EREDETI_GYOKER + MAPPA


def test_az_egyesites_nem_er_halozatot(windows, conn, monkeypatch):
    hivasok: list[int] = []
    eredeti = paths._feloldas

    def lassu(szoveg):
        if SZERVER in szoveg.lower():
            hivasok.append(threading.get_ident())
            time.sleep(0.05)
        return eredeti(szoveg)

    monkeypatch.setattr(paths, "_feloldas", lassu)
    for szam in range(60):
        _folder(conn, f"{EREDETI_GYOKER}\\2026\\nap{szam:03d}")
        _folder(conn, f"{KISBETUS_GYOKER}\\2026\\nap{szam:03d}")

    kezdet = time.monotonic()
    merge_duplicate_folders(conn)
    eltelt = time.monotonic() - kezdet

    assert hivasok == []
    assert eltelt < 1.0, f"az egyesítés {eltelt:.2f} s-ig várt a hálózatra"
    assert conn.execute("SELECT COUNT(*) FROM folders").fetchone()[0] == 60


def test_az_ellentmondo_szerkesztes_tovabbra_sem_vesz_el_adatot(windows, conn):
    regi = _folder(conn, EREDETI_GYOKER + MAPPA)
    uj = _folder(conn, KISBETUS_GYOKER + MAPPA)
    _photo(conn, regi, "a.jpg", star=1)
    _photo(conn, uj, "a.jpg", star=5)

    jelentes = merge_duplicate_folders(conn)

    assert len(jelentes.skipped) == 1
    assert len(_utak(conn)) == 2


def test_a_gyoker_alatti_egyesites_csak_a_gyokerre_szorit_es_alakot_valasztott(windows, conn):
    _folder(conn, EREDETI_GYOKER + MAPPA)
    _folder(conn, KISBETUS_GYOKER + MAPPA)
    masik_regi = _folder(conn, "\\\\MAS\\kepek\\x")
    masik_uj = _folder(conn, "\\\\mas\\kepek\\x")

    merge_duplicate_folders_under(conn, KISBETUS_GYOKER)

    assert _utak(conn) == [EREDETI_GYOKER + MAPPA, "\\\\MAS\\kepek\\x", "\\\\mas\\kepek\\x"]
    assert masik_regi != masik_uj


# -- a szinkron a már ismert alakon ír ----------------------------------------


@pytest.fixture
def hamis_halozat(monkeypatch):
    """A szinkron Path-ja Windows-alakú, a bejáró a kapott gyökérből épít."""
    monkeypatch.setattr(paths, "_platform", lambda: "win32")
    monkeypatch.setattr(sync, "Path", PureWindowsPath)
    monkeypatch.setattr(sync, "elerheto", lambda _ut: True)
    beirt: list[str] = []

    def bejaro(gyoker, **_kwargs):
        mappa = PureWindowsPath(str(gyoker) + MAPPA)
        return (FolderScan(path=mappa, has_ini=True, files=()),)

    def egy_mappa(mappa, **_kwargs):
        return FolderScan(path=PureWindowsPath(str(mappa)), has_ini=True, files=())

    def mappa_sync(conn, scan):
        beirt.append(str(scan.path))
        conn.execute(
            "INSERT INTO folders(path, has_ini) VALUES (?, 1) ON CONFLICT(path) DO NOTHING",
            (str(scan.path),),
        )
        return _FolderSyncResult(0, False)

    monkeypatch.setattr(sync, "_scan_tree_for_index", bejaro)
    monkeypatch.setattr(sync, "_scan_folder_for_index", egy_mappa)
    monkeypatch.setattr(sync, "_sync_folder", mappa_sync)
    return beirt


def test_a_masik_alakkal_felvett_gyoker_ugyanazt_a_sort_hasznalja(conn, hamis_halozat):
    sync.sync_tree(conn, EREDETI_GYOKER)
    sync.sync_tree(conn, KISBETUS_GYOKER)
    sync.sync_tree(conn, "\\\\Ds215J\\PHOTO\\")

    assert _utak(conn) == [EREDETI_GYOKER + MAPPA]
    assert set(hamis_halozat) == {EREDETI_GYOKER + MAPPA}


def test_a_szinkron_a_mar_meglevo_duplikatumot_egyesiti(conn, hamis_halozat):
    regi = _folder(conn, EREDETI_GYOKER + MAPPA)
    uj = _folder(conn, KISBETUS_GYOKER + MAPPA)
    _photo(conn, regi, "a.jpg", star=1)
    _photo(conn, uj, "b.jpg")

    sync.sync_tree(conn, KISBETUS_GYOKER)

    assert _utak(conn) == [EREDETI_GYOKER + MAPPA]
    assert conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0] == 2


def test_az_egymappas_szinkron_is_az_ismert_alakon_ir(conn, hamis_halozat):
    _folder(conn, EREDETI_GYOKER + MAPPA)

    sync.sync_folder(conn, KISBETUS_GYOKER, KISBETUS_GYOKER + MAPPA)

    assert hamis_halozat == [EREDETI_GYOKER + MAPPA]
    assert _utak(conn) == [EREDETI_GYOKER + MAPPA]


# -- a takarítás nem törli a másik alakú sort ----------------------------------


@pytest.mark.skipif(os.name != "posix", reason="Linux-viselkedést mér (POSIX-útvonal, /proc/mounts), Windowson nem érvényes (#7096)")
def test_a_takaritas_a_csak_kis_nagybetuben_eltero_sort_nem_torli(windows, conn):
    from picasapy.index import sync_cleanup

    sync._ensure_scan_state(conn)
    _folder(conn, "/r/Kepek/a")
    _folder(conn, "/r/Kepek/torolt")

    sync_cleanup._prune_folders(conn, PosixRoot("/r/Kepek"), {"/r/kepek/a"})

    assert _utak(conn) == ["/r/Kepek/a"]


class PosixRoot:
    """A `_under_root_query` csak `str(root)`-ot használ."""

    def __init__(self, szoveg: str) -> None:
        self._szoveg = szoveg

    def __str__(self) -> str:
        return self._szoveg
