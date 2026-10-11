"""#4591 — a Picasa-átvétel a videók módosított dátumát és geotagjét is átveszi.

Spec: `docs/specs/pmp-database.md` 15. szakasz (15.6 „Kész, ha").

Szintetikus db3-mintán (thumbindex + imagedata-oszlopok), a teljes láncon:
`iter_photo_records` → `rekordokat_atvesz` → index (`taken_at_override`) /
`.picasa.ini` (`geotag=`).

Amit ez a lap NEM mér: az egyedi képsorrendet (#4884), és azt, hogy az
eredeti Picasa tényleg így módosít (az a 15.1 bináris-bizonyíték).
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from picasapy.index.database import open_index
from picasapy.index.sync import sync_tree
from picasapy.pmpimport import PathRemapper, iter_photo_records
from picasapy.pmpimport.db3_atvetel import rekordokat_atvesz
from picasapy.pmpimport.videodatum import atveendo_datum, filetime_helyi_iso
from support.pmp_factory import build_pmp_column, build_thumb_index

#: 2024-03-05 10:20:30 UTC / 2023-11-12 08:09:10 UTC FILETIME-ban
_EPOCH = datetime(1601, 1, 1, tzinfo=UTC)


def _ft(ev, ho, nap, ora, perc, mp) -> int:
    delta = datetime(ev, ho, nap, ora, perc, mp, tzinfo=UTC) - _EPOCH
    return (delta.days * 86400 + delta.seconds) * 10_000_000


MODOSITOTT = _ft(2023, 11, 12, 8, 9, 10)
FAJLIDO = _ft(2024, 3, 5, 10, 20, 30)
MP4 = 10  # mérve: .mp4 = 10 (15.1)
JPEG = 2


def _helyi(ft: int) -> str:
    return filetime_helyi_iso(ft)


def _db3(tmp_path: Path, fajlok, *, hely: dict[int, tuple[float, float]] | None = None):
    """Szintetikus db3: 1 könyvtár + a megadott fájlok.

    `fajlok`: (név, kind, creation, modified). A sor-index 1-től indul.
    `hely`: sorindex → (lat, long); a `geoview` ezeknél nem üres.
    """
    db3 = tmp_path / "db3"
    db3.mkdir()
    bejegyzesek = [("C:\\Fotok", None)] + [
        (nev, 0, kind, 1, creation, modified)
        for nev, kind, creation, modified in fajlok
    ]
    (db3 / "thumbindex.db").write_bytes(build_thumb_index(bejegyzesek))
    n = len(bejegyzesek)
    (db3 / "imagedata_caption.pmp").write_bytes(build_pmp_column(0x0, [""] * n))
    hely = hely or {}
    (db3 / "imagedata_lat.pmp").write_bytes(
        build_pmp_column(0x2, [hely.get(i, (0.0, 0.0))[0] for i in range(n)])
    )
    (db3 / "imagedata_long.pmp").write_bytes(
        build_pmp_column(0x2, [hely.get(i, (0.0, 0.0))[1] for i in range(n)])
    )
    (db3 / "imagedata_geoview.pmp").write_bytes(
        build_pmp_column(0x0, ["geo" if i in hely else "" for i in range(n)])
    )
    return db3


@pytest.fixture
def fotomappa(tmp_path):
    mappa = tmp_path / "fotok"
    mappa.mkdir()
    for nev in ("film.mp4", "film2.mp4", "kep.jpg"):
        (mappa / nev).write_bytes(b"x")
    return mappa


@pytest.fixture
def index_ut(tmp_path, fotomappa):
    ut = tmp_path / "index.db"
    with open_index(ut) as conn:
        sync_tree(conn, tmp_path / "fotok")
    return ut


def _rekordok(db3, fotomappa):
    return iter_photo_records(db3, PathRemapper.from_dict({"C:\\Fotok": str(fotomappa)}))


def _override(index_ut, nev):
    with open_index(index_ut) as conn:
        sor = conn.execute(
            "SELECT taken_at_override FROM photos WHERE name = ?", (nev,)
        ).fetchone()
    assert sor is not None, f"{nev} nincs az indexben"
    return sor[0]


def test_mp4_eltero_filetime_atveszi(tmp_path, fotomappa, index_ut):
    db3 = _db3(tmp_path, [("film.mp4", MP4, MODOSITOTT, FAJLIDO)])
    jelentes = rekordokat_atvesz(_rekordok(db3, fotomappa), index_path=index_ut)
    assert _override(index_ut, "film.mp4") == _helyi(MODOSITOTT)
    assert jelentes.videodatum == 1
    # a videófájl és a .picasa.ini érintetlen
    assert (fotomappa / "film.mp4").read_bytes() == b"x"
    assert not (fotomappa / ".picasa.ini").exists()


def test_az_atvett_datum_a_picasa_modositotta_helyi_ido(tmp_path, fotomappa, index_ut):
    db3 = _db3(tmp_path, [("film.mp4", MP4, MODOSITOTT, FAJLIDO)])
    rekordokat_atvesz(_rekordok(db3, fotomappa), index_path=index_ut)
    vart = (
        datetime(2023, 11, 12, 8, 9, 10, tzinfo=UTC)
        .astimezone()
        .replace(tzinfo=None)
        .isoformat(timespec="seconds")
    )
    assert _override(index_ut, "film.mp4") == vart


def test_mp4_egyenlo_filetime_nem_ir(tmp_path, fotomappa, index_ut):
    db3 = _db3(tmp_path, [("film.mp4", MP4, FAJLIDO, FAJLIDO)])
    jelentes = rekordokat_atvesz(_rekordok(db3, fotomappa), index_path=index_ut)
    assert _override(index_ut, "film.mp4") is None
    assert jelentes.videodatum == 0


def test_jpg_eltero_filetime_nem_ir(tmp_path, fotomappa, index_ut):
    db3 = _db3(tmp_path, [("kep.jpg", JPEG, MODOSITOTT, FAJLIDO)])
    jelentes = rekordokat_atvesz(_rekordok(db3, fotomappa), index_path=index_ut)
    assert _override(index_ut, "kep.jpg") is None
    assert jelentes.videodatum == 0


def test_meglevo_override_nem_ir_felul(tmp_path, fotomappa, index_ut):
    with open_index(index_ut) as conn:
        conn.execute(
            "UPDATE photos SET taken_at_override = '2000-01-01T00:00:00' "
            "WHERE name = 'film.mp4'"
        )
        conn.commit()
    db3 = _db3(
        tmp_path,
        [
            ("film.mp4", MP4, MODOSITOTT, FAJLIDO),
            ("film2.mp4", MP4, MODOSITOTT, FAJLIDO),
        ],
    )
    jelentes = rekordokat_atvesz(_rekordok(db3, fotomappa), index_path=index_ut)
    assert _override(index_ut, "film.mp4") == "2000-01-01T00:00:00"
    assert _override(index_ut, "film2.mp4") == _helyi(MODOSITOTT)
    assert jelentes.videodatum == 1


def test_a_szinkron_megtartja_az_atvett_datumot(tmp_path, fotomappa, index_ut):
    db3 = _db3(tmp_path, [("film.mp4", MP4, MODOSITOTT, FAJLIDO)])
    rekordokat_atvesz(_rekordok(db3, fotomappa), index_path=index_ut)
    (fotomappa / "film.mp4").write_bytes(b"xyz")  # a fájl változik
    with open_index(index_ut) as conn:
        sync_tree(conn, fotomappa.parent)
    assert _override(index_ut, "film.mp4") == _helyi(MODOSITOTT)


def test_index_nelkul_nincs_videodatum(tmp_path, fotomappa, index_ut):
    db3 = _db3(tmp_path, [("film.mp4", MP4, MODOSITOTT, FAJLIDO)])
    jelentes = rekordokat_atvesz(_rekordok(db3, fotomappa))
    assert _override(index_ut, "film.mp4") is None
    assert jelentes.videodatum == 0


def test_mp4_helyadata_geotagkent_az_ini_be_kerul(tmp_path, fotomappa):
    db3 = _db3(
        tmp_path,
        [("film.mp4", MP4, FAJLIDO, FAJLIDO)],
        hely={1: (47.497912, 19.040235)},
    )
    jelentes = rekordokat_atvesz(_rekordok(db3, fotomappa))
    ini = (fotomappa / ".picasa.ini").read_text(encoding="utf-8")
    assert "[film.mp4]" in ini
    assert "geotag=47.497912,19.040235" in ini
    assert jelentes.hely == 1


def test_mp4_geoview_nelkul_nincs_geotag(tmp_path, fotomappa):
    db3 = _db3(tmp_path, [("film.mp4", MP4, FAJLIDO, FAJLIDO)])
    rekordokat_atvesz(_rekordok(db3, fotomappa))
    assert not (fotomappa / ".picasa.ini").exists()


def test_atveendo_datum_hataresetek(tmp_path, fotomappa):
    db3 = _db3(
        tmp_path,
        [
            ("film.mp4", MP4, 0, FAJLIDO),
            ("film2.mp4", MP4, MODOSITOTT, FAJLIDO),
        ],
    )
    nulla, jo = _rekordok(db3, fotomappa)
    assert atveendo_datum(nulla) is None
    assert atveendo_datum(jo) == _helyi(MODOSITOTT)


# --- #4591 átnézés utáni javítások -------------------------------------


def test_hibas_index_mellett_az_ini_atvetel_lefut(tmp_path, fotomappa):
    """J1/A6: a sérült index nem viszi el az ini-átvételt; a hiba számolva."""
    rossz = tmp_path / "rossz.db"
    rossz.write_bytes(b"ez nem sqlite adatbazis" * 50)
    db3 = _db3(
        tmp_path,
        [("film.mp4", MP4, MODOSITOTT, FAJLIDO)],
        hely={1: (47.497912, 19.040235)},
    )
    jelentes = rekordokat_atvesz(_rekordok(db3, fotomappa), index_path=rossz)
    ini = (fotomappa / ".picasa.ini").read_text(encoding="utf-8")
    assert "geotag=47.497912,19.040235" in ini
    assert jelentes.hely == 1
    assert jelentes.videodatum == 0
    assert jelentes.videodatum_hiba == 1


def test_a_mappa_datuma_az_atvett_datum_lesz(tmp_path, fotomappa, index_ut):
    """J2: a mappa dátuma a legrégebbi fotó effektív dátuma."""
    db3 = _db3(tmp_path, [("film.mp4", MP4, MODOSITOTT, FAJLIDO)])
    rekordokat_atvesz(_rekordok(db3, fotomappa), index_path=index_ut)
    with open_index(index_ut) as conn:
        datum = conn.execute("SELECT date FROM folders").fetchone()[0]
    assert datum == _helyi(MODOSITOTT)


def test_a_mappa_datum_kezi_felulirasa_megmarad(tmp_path, fotomappa, index_ut):
    (fotomappa / ".picasa.ini").write_text(
        "[Picasa]\ndate=2001-02-03\n", encoding="utf-8"
    )
    with open_index(index_ut) as conn:
        sync_tree(conn, fotomappa.parent)
        elotte = conn.execute("SELECT date FROM folders").fetchone()[0]
    db3 = _db3(tmp_path, [("film.mp4", MP4, MODOSITOTT, FAJLIDO)])
    rekordokat_atvesz(_rekordok(db3, fotomappa), index_path=index_ut)
    with open_index(index_ut) as conn:
        utana = conn.execute("SELECT date FROM folders").fetchone()[0]
    assert elotte == "2001-02-03"
    assert utana == elotte


def test_metaadat_datumos_nem_jpeg_nem_kap_felulirast(tmp_path, fotomappa, index_ut):
    """J3: ha az 1. FILETIME = `taken_at` (metaadat-dátum), nem ír."""
    with open_index(index_ut) as conn:
        conn.execute(
            "UPDATE photos SET taken_at = ? WHERE name = 'kep.jpg'",
            (_helyi(MODOSITOTT),),
        )
        conn.commit()
    db3 = _db3(tmp_path, [("kep.jpg", 6, MODOSITOTT, FAJLIDO)])  # 6 = nem JPEG
    jelentes = rekordokat_atvesz(_rekordok(db3, fotomappa), index_path=index_ut)
    assert _override(index_ut, "kep.jpg") is None
    assert jelentes.videodatum == 0


def test_eltero_taken_at_mellett_a_videodatum_ir(tmp_path, fotomappa, index_ut):
    with open_index(index_ut) as conn:
        conn.execute(
            "UPDATE photos SET taken_at = '1999-01-01T00:00:00' WHERE name = 'film.mp4'"
        )
        conn.commit()
    db3 = _db3(tmp_path, [("film.mp4", MP4, MODOSITOTT, FAJLIDO)])
    jelentes = rekordokat_atvesz(_rekordok(db3, fotomappa), index_path=index_ut)
    assert _override(index_ut, "film.mp4") == _helyi(MODOSITOTT)
    assert jelentes.videodatum == 1


@pytest.mark.skipif(not hasattr(time, "tzset"), reason="POSIX időzóna-váltás")
def test_filetime_helyi_ido_rogzitett_zonaval(monkeypatch):
    """A1: nyári 10:00Z → 12:00, téli 10:00Z → 11:00 (Europe/Budapest)."""
    monkeypatch.setenv("TZ", "Europe/Budapest")
    time.tzset()
    try:
        assert filetime_helyi_iso(_ft(2024, 7, 1, 10, 0, 0)) == "2024-07-01T12:00:00"
        assert filetime_helyi_iso(_ft(2024, 1, 15, 10, 0, 0)) == "2024-01-15T11:00:00"
    finally:
        monkeypatch.undo()
        time.tzset()


def test_a_mappa_nem_pontos_utegyezessel_is_megtalalhato(tmp_path, fotomappa, index_ut):
    """A2: az index más alakban tárolja a mappa útját (`.` szegmens)."""
    with open_index(index_ut) as conn:
        conn.execute("UPDATE folders SET path = path || '/.'")
        conn.commit()
    db3 = _db3(tmp_path, [("film.mp4", MP4, MODOSITOTT, FAJLIDO)])
    jelentes = rekordokat_atvesz(_rekordok(db3, fotomappa), index_path=index_ut)
    assert _override(index_ut, "film.mp4") == _helyi(MODOSITOTT)
    assert jelentes.videodatum == 1


def test_a_helyi_ido_atalakitas_hibaja_naplozva(tmp_path, fotomappa, caplog, monkeypatch):
    """A3: az `astimezone()` OSError-ja nem némán nyelődik el."""
    import picasapy.pmpimport.videodatum as vd

    def rossz(_ft):
        raise OSError("tz")

    monkeypatch.setattr(vd, "filetime_helyi_iso", rossz)
    db3 = _db3(tmp_path, [("film.mp4", MP4, MODOSITOTT, FAJLIDO)])
    (rek,) = _rekordok(db3, fotomappa)
    with caplog.at_level("WARNING"):
        assert vd.atveendo_datum(rek) is None
    assert "helyi időre" in caplog.text
