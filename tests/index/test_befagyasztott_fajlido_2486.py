"""#2486: BEFAGYASZTOTT (első látáskori) fájlidő a `photos` táblában.

## A hibaosztály, amit ez az őr fog meg

A rács dátum-rendezése EXIF felvételi idő hiányában a fájl idejére esik
vissza. Amíg ez az ÉLŐ `mtime` volt, a sorrend attól függött, mikor
nyúlt hozzá bárki a fájlhoz utoljára — és nyúlt hozzá: a #2304 mérése
szerint a tulajdonos `AI` mappájában **19 fájlnak íródott át az mtime-ja**
egyetlen időpontra (`2026-07-19 20:05:39`), és pontosan ez a 19 fájl
csúszott el a Picasa sorrendjétől. A #2491 óta a SAJÁT ini-írásunk
(`ini/photo_touch.py`) is átírja a szerkesztett képek `mtime`-ját, tehát
a jelenség nem külső balesetre korlátozódik: minden szerkesztés
elmozdítja a saját képünket a rácsban.

## Amit az eredeti csinál

A Picasa a képhez tartozó dátumot a beolvasáskor a katalógusába
FAGYASZTJA (`thumbindex` 1. FILETIME-ja), és a pásztázó soha nem
frissíti — a pásztázás csak a 2. mezőt (az élő `mtime`-ot) írja.
Metaadat-dátum hiányában az 1. mező a 2.-kal egyenlő marad, azaz a
BEOLVASÁSKORI fájlidővel. Bizonyíték: `docs/specs/pmp-database.md`
10.1 (kimerítő negatív a frissítésre), 10.3 (a beállító egyetlen
hívója), 10.4 (mérés 140 758 rekordon). Döntés:
`docs/decisions/befagyasztott-fajlido.md`.

## Az őr magja

`TestAtirtMtime::test_az_atirt_mtime_nem_rendezi_at_a_racsot` — a jegy
kifejezett kérése. Mutációval igazolva: ha a `photo_sort.photo_date`
tartaléka visszaáll `record.mtime_ns`-re, vagy ha az `_upsert_photo`
`COALESCE`-a lekerül, ez a teszt BUKIK.
"""

from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path

import pytest

from picasapy.app.photo_sort import photo_date, sort_folder_blocks
from picasapy.index import SCHEMA_VERSION, open_index, photos_in_folder, sync_tree
from picasapy.index.queries import PhotoRecord
from picasapy.index.schema import DDL
from picasapy.timeline import record_date
from support.jpeg_factory import make_jpeg

#: A három kép EREDETI fájlideje — külön napokon, tehát a dátum-rendezés
#: egyértelmű. A nevek ábécésorrendje SZÁNDÉKOSAN ellentétes a dátumokéval:
#: így a „dátum" rendezés eredménye nem eshet véletlenül egybe a
#: névsorral, és a teszt tényleg a dátum-kulcsot méri.
_EREDETI = (
    ("c.jpg", (2023, 11, 14, 17, 49, 15)),
    ("b.jpg", (2024, 3, 2, 8, 30, 0)),
    ("a.jpg", (2025, 6, 21, 12, 0, 0)),
)

#: Az „elrontás": MINDEN fájl ugyanazt az új időt kapja, ráadásul a
#: jövőben. Ez a #2304-en mért valódi eset alakja (19 fájl, egyetlen
#: időbélyeg) — élő `mtime` mellett a három kép sorrendje ilyenkor a
#: dátum-kulcson eldönthetetlenné válik, és a névsorra esik vissza,
#: vagyis MEGFORDUL.
_ATIRT = (2026, 7, 19, 20, 5, 39)


def _idore(path: Path, mezok: tuple[int, ...]) -> None:
    ido = time.mktime((*mezok, 0, 0, -1))
    os.utime(path, (ido, ido))


def _nevek(records) -> tuple[str, ...]:
    return tuple(r.name for r in sort_folder_blocks(records, "date"))


@pytest.fixture
def mappa(tmp_path: Path) -> Path:
    """EXIF felvételi idő NÉLKÜLI képek, eltérő fájlidőkkel."""
    gyoker = tmp_path / "AI"
    gyoker.mkdir()
    for nev, mikor in _EREDETI:
        kep = gyoker / nev
        make_jpeg(kep)  # a gyár nem ír EXIF felvételi időt
        _idore(kep, mikor)
    return gyoker


def _atir_minden_mtime_ot(mappa: Path) -> None:
    for nev, _ in _EREDETI:
        _idore(mappa / nev, _ATIRT)


class TestAtirtMtime:
    def test_az_atirt_mtime_nem_rendezi_at_a_racsot(
        self, tmp_path: Path, mappa: Path
    ) -> None:
        """A JEGY MAGJA: a fájlidők átírása után a sorrend VÁLTOZATLAN."""
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, mappa, incremental=False)
            elotte = _nevek(photos_in_folder(conn, mappa))
            assert elotte == ("c.jpg", "b.jpg", "a.jpg"), elotte

            _atir_minden_mtime_ot(mappa)
            sync_tree(conn, mappa, incremental=False)
            utana = _nevek(photos_in_folder(conn, mappa))

        assert utana == elotte, (
            "az átírt mtime átrendezte a rácsot — a befagyasztás nem hatott"
        )

    def test_a_befagyasztott_ertek_az_ELSO_latasi_ido_marad(
        self, tmp_path: Path, mappa: Path
    ) -> None:
        """Nem csak a sorrend: maga a tárolt érték sem mozdul."""
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, mappa, incremental=False)
            elso = {r.name: r.first_seen_mtime_ns for r in photos_in_folder(conn, mappa)}
            _atir_minden_mtime_ot(mappa)
            sync_tree(conn, mappa, incremental=False)
            masodik = {
                r.name: r.first_seen_mtime_ns for r in photos_in_folder(conn, mappa)
            }
        assert masodik == elso
        assert all(ertek is not None for ertek in elso.values())

    def test_az_ELO_mtime_tovabbra_is_koveti_a_fajlt(
        self, tmp_path: Path, mappa: Path
    ) -> None:
        """A befagyasztás NEM veheti el az élő `mtime`-ot: arra épül a
        változás-detektálás, a bélyegkép-gyorstár kulcsa és a bal hasáb
        „legutóbbi változtatás" rendezése."""
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, mappa, incremental=False)
            elotte = {r.name: r.mtime_ns for r in photos_in_folder(conn, mappa)}
            _atir_minden_mtime_ot(mappa)
            sync_tree(conn, mappa, incremental=False)
            utana = {r.name: r.mtime_ns for r in photos_in_folder(conn, mappa)}
        assert utana != elotte, "az élő mtime nem követte a fájlt"
        assert len(set(utana.values())) == 1, "mindhárom fájl ugyanazt az időt kapta"

    def test_a_mappa_datuma_sem_ugrik_el(self, tmp_path: Path, mappa: Path) -> None:
        """A #2304 mappa-dátum tartaléka ugyanezt a befagyasztott időt
        használja — különben a fejléc és a bal hasáb évcsoportja elmozdulna
        egy mentés vagy egy szerkesztés hatására."""
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, mappa, incremental=False)
            elotte = conn.execute(
                "SELECT date FROM folders WHERE path = ?", (str(mappa),)
            ).fetchone()["date"]
            _atir_minden_mtime_ot(mappa)
            sync_tree(conn, mappa, incremental=False)
            utana = conn.execute(
                "SELECT date FROM folders WHERE path = ?", (str(mappa),)
            ).fetchone()["date"]
        assert elotte is not None and elotte.startswith("2023-11-14"), elotte
        assert utana == elotte

    def test_az_EXIF_datum_erosebb_marad(self, tmp_path: Path) -> None:
        """A befagyasztás nem veheti át a helyet ott, ahol van felvételi
        idő — a tartalék tartalék marad."""
        gyoker = tmp_path / "Nyaralas"
        gyoker.mkdir()
        kep = gyoker / "IMG_1.jpg"
        make_jpeg(kep, taken_at="2019:07:04 10:00:00")
        _idore(kep, _ATIRT)
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, gyoker, incremental=False)
            rekord = photos_in_folder(conn, gyoker)[0]
        assert photo_date(rekord) == "2019-07-04T10:00:00"


class TestVisszaeses:
    """A #2486 3. követelménye: a befagyasztott érték ELVESZTÉSE nem
    ronthat el semmit — a `.picasa.ini` az igazságforrás, az index
    eldobható és újraépíthető."""

    def _rekord(self, **kwargs) -> PhotoRecord:
        mezok = dict(
            id=1,
            folder_path="/kepek",
            name="a.jpg",
            kind="photo",
            size=10,
            mtime_ns=1_700_000_000_000_000_000,
            star=False,
            caption=None,
            keywords=None,
            rotate_steps=0,
            filters=None,
            taken_at=None,
            orientation=1,
            width=None,
            height=None,
        )
        mezok.update(kwargs)
        return PhotoRecord(**mezok)

    def test_hianyzo_befagyasztott_ertekre_az_elo_mtime_jon(self) -> None:
        rekord = self._rekord()
        assert rekord.first_seen_mtime_ns is None
        assert rekord.sort_mtime_ns == rekord.mtime_ns
        assert photo_date(rekord) == photo_date(self._rekord())

    def test_a_befagyasztott_ertek_nyer_ha_van(self) -> None:
        rekord = self._rekord(first_seen_mtime_ns=1_600_000_000_000_000_000)
        assert rekord.sort_mtime_ns == 1_600_000_000_000_000_000
        assert photo_date(rekord) < photo_date(self._rekord())

    def test_a_torolt_index_ujraepitese_a_mai_idot_fagyasztja(
        self, tmp_path: Path, mappa: Path
    ) -> None:
        """Ha az indexet eldobjuk, az „első látás" újrakezdődik — a mai
        fájlidőkkel. Ez NEM regresszió: pontosan azt adja, amit a #2486
        előtti kód is adott volna."""
        _atir_minden_mtime_ot(mappa)
        with open_index(tmp_path / "friss.db") as conn:
            sync_tree(conn, mappa, incremental=False)
            rekordok = photos_in_folder(conn, mappa)
        assert all(r.first_seen_mtime_ns == r.mtime_ns for r in rekordok)


class TestIdorend:
    """Az Időrend nézet ugyanazt a fájlidőt datálja, mint a rács.

    A `TimelineController` Qt-t igényel, ezért a döntés a Qt-mentes
    `picasapy.timeline.record_date`-ben él — a controller csak azt hívja.
    Így az őr QML-motor nélkül is fut."""

    def test_az_atirt_mtime_nem_viszi_masik_korszakba(
        self, tmp_path: Path, mappa: Path
    ) -> None:
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, mappa, incremental=False)
            elotte = {r.name: record_date(r) for r in photos_in_folder(conn, mappa)}
            _atir_minden_mtime_ot(mappa)
            sync_tree(conn, mappa, incremental=False)
            utana = {r.name: record_date(r) for r in photos_in_folder(conn, mappa)}
        assert utana == elotte
        assert elotte["c.jpg"].year == 2023, elotte

    def test_a_racs_es_az_idorend_ugyanazt_a_napot_mondja(
        self, tmp_path: Path, mappa: Path
    ) -> None:
        """A #2486 mellékhaszna: két nézet nem mondhat mást ugyanarról a
        képről. Élő `mtime` mellett ez az egyezés véletlen volt — most
        SZERZŐDÉS."""
        _atir_minden_mtime_ot(mappa)
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, mappa, incremental=False)
            rekordok = photos_in_folder(conn, mappa)
            _idore(mappa / "c.jpg", (2019, 1, 1, 0, 0, 0))
            sync_tree(conn, mappa, incremental=False)
            rekordok = photos_in_folder(conn, mappa)
        for rekord in rekordok:
            assert photo_date(rekord)[:10] == record_date(rekord).isoformat()


def _oszlopok(conn: sqlite3.Connection) -> set[str]:
    return {sor[1] for sor in conn.execute("PRAGMA table_info(photos)")}


class TestMigracio:
    """v16 → v17. A meglévő sorok NEM NULL-lal indulnak."""

    def _v16_adatbazis(self, tmp_path: Path) -> Path:
        path = tmp_path / "regi.db"
        raw = sqlite3.connect(path)
        raw.executescript(DDL)
        # a v17 oszlopának eltávolítása = a v16-os alak visszaállítása
        raw.executescript(
            "ALTER TABLE photos DROP COLUMN first_seen_mtime_ns;\n"
            "PRAGMA user_version = 16;"
        )
        raw.execute("INSERT INTO folders(id, path, has_ini) VALUES (1, '/kepek', 0)")
        raw.execute(
            "INSERT INTO photos(folder_id, name, kind, size, mtime_ns)"
            " VALUES (1, 'a.jpg', 'photo', 10, 1699984155000000000)"
        )
        raw.commit()
        raw.close()
        return path

    def test_a_verzio_emelkedik_es_az_oszlop_megjelenik(self, tmp_path: Path) -> None:
        path = self._v16_adatbazis(tmp_path)
        with open_index(path) as conn:
            assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
            assert "first_seen_mtime_ns" in _oszlopok(conn)

    def test_a_meglevo_sorok_a_MAI_mtime_ot_kapjak_nem_NULL_t(
        self, tmp_path: Path
    ) -> None:
        """A döntés kimondott ára (ld. az ADR-t): a migráció a MAI — akár
        már átírt — `mtime`-ot fagyasztja be.

        A NULL-os változat rosszabb lenne: a szinkron a VÁLTOZATLAN fotóra
        nem futtat UPSERT-et, tehát a sor épp a fájl KÖVETKEZŐ átírásakor
        töltődne fel — vagyis már a romlott idővel."""
        path = self._v16_adatbazis(tmp_path)
        with open_index(path) as conn:
            sor = conn.execute(
                "SELECT mtime_ns, first_seen_mtime_ns FROM photos"
            ).fetchone()
        assert sor["first_seen_mtime_ns"] == sor["mtime_ns"] == 1699984155000000000

    def test_a_migralt_es_a_friss_sema_oszlopai_azonosak(
        self, tmp_path: Path
    ) -> None:
        """A két útnak — friss telepítés kontra migrálás — ugyanoda kell
        érkeznie; enélkül a séma csendben kettéválna."""
        migralt = self._v16_adatbazis(tmp_path)
        with open_index(migralt) as conn:
            regi = _oszlopok(conn)
        with open_index(tmp_path / "friss.db") as conn:
            uj = _oszlopok(conn)
        assert regi == uj

    def test_a_migralt_indexen_a_lekerdezes_is_mukodik(self, tmp_path: Path) -> None:
        path = self._v16_adatbazis(tmp_path)
        with open_index(path) as conn:
            rekord = photos_in_folder(conn, "/kepek")[0]
        assert rekord.first_seen_mtime_ns == 1699984155000000000
        assert rekord.sort_mtime_ns == 1699984155000000000
