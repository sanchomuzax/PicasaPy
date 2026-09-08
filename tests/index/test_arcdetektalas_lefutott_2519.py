"""„Az arc-detektálás LEFUTOTT" jelölés (#2519).

## Miért kell

A `face` tábla csak a MEGTALÁLT arcokat tárolja, ezért egy arc nélküli fotó
megkülönböztethetetlen a még sosem vizsgálttól: mindkettő nulla sort ad. A
detektálás emiatt minden szkennelésnél újrafutott rajtuk.

## Az eredeti megoldása (mérve, `docs/specs/picasa-imagedata-rekord.md`)

A Picasa `imagedata.facerect` oszlopa háromfelé ágazik: **0** = „még nem
dolgoztuk fel", **1** = „feldolgozva, szándékosan nincs téglalap", egyéb =
valódi `rect64`. A téglalap írója (`FUN_00480040`) **csak nulla értékre ír**
(`0x00480de7`–`0x00480df1`), tehát az `1` megvédi a képet az
újra-detektálástól; a jelzőt a Mappakezelő arcfelismerés-kizárása teszi ki.

## Amit ez a lap őriz

A nálunk ennek megfelelő `face_scan` tábla: fotónkénti nyom a fájl
azonosságával (`mtime_ns`, `size`) együtt — a MEGVÁLTOZOTT fotó újra
vizsgálandó —, és egy `reason` mező, amelyben a `kizarva` **erősebb**: azt a
fájl változása sem oldja fel (ez az eredeti „1"-es jelzőjének megfelelője).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from picasapy.index import SCHEMA_VERSION, open_index
from picasapy.index.faces_detected import (
    OK_DETEKTALVA,
    OK_KIZARVA,
    face_scan_done,
    forget_face_scan,
    mark_face_scan,
    mark_folder_excluded,
)
from picasapy.index.schema import DDL

MTIME = 1_699_984_155_000_000_000
MERET = 1234


def _index(tmp_path: Path) -> Path:
    """Négy fotót tartalmazó, üres index — a `sync_tree` nélkül, mert ez a lap
    az index RÉTEGÉT méri, nem a beolvasót."""
    path = tmp_path / "index.db"
    with open_index(path) as conn:
        conn.execute("INSERT INTO folders(id, path, has_ini) VALUES (1, '/kepek', 0)")
        conn.execute("INSERT INTO folders(id, path, has_ini) VALUES (2, '/masik', 0)")
        # ALFA: a kizárás a mappára ÉS az alfáira szól (#449)
        conn.execute("INSERT INTO folders(id, path, has_ini) VALUES (3, '/kepek/2011', 0)")
        for azonosito, (mappa, nev) in enumerate(
            ((1, "a.jpg"), (1, "b.jpg"), (2, "c.jpg"), (3, "d.jpg")), start=1
        ):
            conn.execute(
                "INSERT INTO photos(id, folder_id, name, kind, size, mtime_ns)"
                " VALUES (?, ?, ?, 'photo', ?, ?)",
                (azonosito, mappa, nev, MERET, MTIME),
            )
        conn.commit()
    return path


class TestSema:
    def test_a_friss_index_ismeri_a_tablat(self, tmp_path: Path) -> None:
        with open_index(tmp_path / "uj.db") as conn:
            sorok = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='face_scan'"
            ).fetchall()
        assert sorok, "a friss index sémájából hiányzik a `face_scan` tábla"

    def test_a_regi_index_migralodik(self, tmp_path: Path) -> None:
        """A tábla nélküli (v17) index megnyitáskor megkapja a táblát, és a
        meglévő adatai megmaradnak."""
        path = tmp_path / "regi.db"
        raw = sqlite3.connect(path)
        raw.executescript(DDL)
        raw.executescript("DROP TABLE face_scan;\nPRAGMA user_version = 17;")
        raw.execute("INSERT INTO folders(id, path, has_ini) VALUES (1, '/kepek', 0)")
        raw.execute(
            "INSERT INTO photos(id, folder_id, name, kind, size, mtime_ns)"
            " VALUES (1, 1, 'a.jpg', 'photo', 10, 5)"
        )
        raw.commit()
        raw.close()

        with open_index(path) as conn:
            verzio = conn.execute("PRAGMA user_version").fetchone()[0]
            van_tabla = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='face_scan'"
            ).fetchall()
            fotok = conn.execute("SELECT name FROM photos").fetchall()
        assert verzio == SCHEMA_VERSION
        assert van_tabla, "a migráció nem hozta létre a `face_scan` táblát"
        assert [sor[0] for sor in fotok] == ["a.jpg"], "a migráció elvesztette az adatot"


class TestJeloles:
    def test_jeloles_nelkul_meg_nem_futott(self, tmp_path: Path) -> None:
        with open_index(_index(tmp_path)) as conn:
            assert not face_scan_done(conn, 1, mtime_ns=MTIME, size=MERET)

    def test_a_jeloles_utan_lefutottnak_szamit(self, tmp_path: Path) -> None:
        with open_index(_index(tmp_path)) as conn:
            mark_face_scan(conn, 1, mtime_ns=MTIME, size=MERET)
            assert face_scan_done(conn, 1, mtime_ns=MTIME, size=MERET)
            # a másik fotóra NEM hat
            assert not face_scan_done(conn, 2, mtime_ns=MTIME, size=MERET)

    def test_a_megvaltozott_fajlt_ujra_kell_vizsgalni(self, tmp_path: Path) -> None:
        """A jelölés a fájl AZONOSSÁGÁHOZ kötött: ha a kép megváltozott,
        a régi eredmény nem érvényes (a `photo_hashes` ugyanezt teszi)."""
        with open_index(_index(tmp_path)) as conn:
            mark_face_scan(conn, 1, mtime_ns=MTIME, size=MERET)
            assert not face_scan_done(conn, 1, mtime_ns=MTIME + 1, size=MERET)
            assert not face_scan_done(conn, 1, mtime_ns=MTIME, size=MERET + 1)

    def test_ujrajeloles_nem_duplikal(self, tmp_path: Path) -> None:
        with open_index(_index(tmp_path)) as conn:
            mark_face_scan(conn, 1, mtime_ns=MTIME, size=MERET)
            mark_face_scan(conn, 1, mtime_ns=MTIME + 9, size=MERET)
            darab = conn.execute(
                "SELECT COUNT(*) FROM face_scan WHERE photo_id = 1"
            ).fetchone()[0]
            assert darab == 1
            assert face_scan_done(conn, 1, mtime_ns=MTIME + 9, size=MERET)

    def test_a_fotó_torlese_a_jelolest_is_viszi(self, tmp_path: Path) -> None:
        """ON DELETE CASCADE — különben a jelölés túlélné a fotót, és egy új,
        azonos azonosítójú sor örökölné (a `face` tábla is így van)."""
        with open_index(_index(tmp_path)) as conn:
            mark_face_scan(conn, 1, mtime_ns=MTIME, size=MERET)
            conn.execute("DELETE FROM photos WHERE id = 1")
            conn.commit()
            darab = conn.execute("SELECT COUNT(*) FROM face_scan").fetchone()[0]
        assert darab == 0


class TestKizaras:
    def test_a_kizarast_a_fajl_valtozasa_sem_oldja_fel(self, tmp_path: Path) -> None:
        """Ez az eredeti `facerect = 1` jelzőjének megfelelője: a kizárt
        fotót akkor sem vizsgáljuk újra, ha közben megváltozott. Enélkül egy
        szerkesztés visszahozná az arcokat egy szándékosan kizárt mappában."""
        with open_index(_index(tmp_path)) as conn:
            mark_face_scan(conn, 1, mtime_ns=MTIME, size=MERET, ok=OK_KIZARVA)
            assert face_scan_done(conn, 1, mtime_ns=MTIME + 5, size=MERET + 5)

    def test_mappa_kizarasa_a_fotoit_jeloli(self, tmp_path: Path) -> None:
        with open_index(_index(tmp_path)) as conn:
            erintett = mark_folder_excluded(conn, "/kepek")
            assert erintett == 3  # a.jpg, b.jpg és az alfa d.jpg-je
            assert face_scan_done(conn, 1, mtime_ns=MTIME + 1, size=MERET)
            assert face_scan_done(conn, 2, mtime_ns=MTIME + 1, size=MERET)
            # a másik mappa fotója érintetlen
            assert not face_scan_done(conn, 3, mtime_ns=MTIME, size=MERET)
            okok = {
                sor[0]
                for sor in conn.execute("SELECT ok FROM face_scan").fetchall()
            }
            assert okok == {OK_KIZARVA}

    def test_a_kizaras_felulirja_a_korabbi_detektalast(self, tmp_path: Path) -> None:
        with open_index(_index(tmp_path)) as conn:
            mark_face_scan(conn, 1, mtime_ns=MTIME, size=MERET, ok=OK_DETEKTALVA)
            mark_folder_excluded(conn, "/kepek")
            ok = conn.execute(
                "SELECT ok FROM face_scan WHERE photo_id = 1"
            ).fetchone()[0]
        assert ok == OK_KIZARVA

    def test_a_felejtes_visszaadja_az_ujra_vizsgalhatosagot(self, tmp_path: Path) -> None:
        """A visszaengedés (a felhasználó megerősítő válasza után) törli a
        jelölést — ettől a következő szkennelés újra megnézi a fotókat."""
        with open_index(_index(tmp_path)) as conn:
            mark_folder_excluded(conn, "/kepek")
            torolt = forget_face_scan(conn, folder_path="/kepek")
            assert torolt == 3  # az alfa fotója is
            assert not face_scan_done(conn, 1, mtime_ns=MTIME, size=MERET)
            assert not face_scan_done(conn, 2, mtime_ns=MTIME, size=MERET)


    def test_a_kizaras_az_ALFAKRA_is_vonatkozik(self, tmp_path: Path) -> None:
        """A Mappakezelő kapcsolója a mappára ÉS az alfáira szól (#449) — a
        jelölésnek követnie kell, különben az alfák képei a következő
        szkennelésnél újra végigfutnának a detektoron."""
        with open_index(_index(tmp_path)) as conn:
            assert mark_folder_excluded(conn, "/kepek") == 3
            assert face_scan_done(conn, 4, mtime_ns=MTIME + 1, size=MERET)
            assert not face_scan_done(conn, 3, mtime_ns=MTIME, size=MERET)

    def test_a_hasonlo_nevu_TESTVER_mappa_nem_erintett(self, tmp_path: Path) -> None:
        """`/kepek` kizárása nem érintheti a `/kepek-masolat`-ot — a
        LIKE-minta a záró `/`-jel miatt nem csúszhat át rá."""
        path = _index(tmp_path)
        with open_index(path) as conn:
            conn.execute("INSERT INTO folders(id, path, has_ini) VALUES (4, '/kepek-masolat', 0)")
            conn.execute(
                "INSERT INTO photos(id, folder_id, name, kind, size, mtime_ns)"
                " VALUES (5, 4, 'e.jpg', 'photo', ?, ?)",
                (MERET, MTIME),
            )
            conn.commit()
            mark_folder_excluded(conn, "/kepek")
            assert not face_scan_done(conn, 5, mtime_ns=MTIME, size=MERET)
