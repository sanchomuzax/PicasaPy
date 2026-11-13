"""Recently Updated (#6884): a hétnapos tagság dátumkulcsa.

Az eredeti Picasa a `]updated` hétnapos kapujában a rekord ELSŐ dátumpárját
vizsgálja, amelyet érvényes EXIF `DateTimeOriginal` esetén a felvétel dátuma
ír felül (spec: `docs/specs/picasa-idorend-bemutato-kutatas.md` 38.2.121/b);
a kézi dátumállítás ugyanide ír, ezért az előbbre való. Hiányzó vagy hibás
EXIF-dátumnál marad a fájl módosítási ideje.

A tesztek az indexsorokat közvetlenül állítják (ahogy a #6851 tesztjei), a
legvégén pedig egy valódi JPEG-fájlokkal futó szinkron igazolja, hogy a
`taken_at` az EXIF-ből jön, és EXIF nélkül üres.
"""

import os
from datetime import datetime, timedelta

import piexif
import pytest
from PIL import Image

from picasapy.index import open_index, sync_tree
from picasapy.index.albums import album_photos
from picasapy.index.queries import (
    count_recently_updated_photos,
    recently_updated_photos,
)

_NS = 1_000_000_000
_NAP_NS = 86400 * _NS

#: Rögzített „most": nyár közepe, hogy a helyi idő órakorrekciója (DST) a
#: tesztet semmilyen időzónában ne érintse.
_MOST = datetime(2026, 6, 15, 12, 0, 0)
_MOST_NS = int(_MOST.timestamp() * _NS)
_KUSZOB_NS = _MOST_NS - 7 * _NAP_NS


def _iso(delta: timedelta) -> str:
    """A rögzített „most" + delta, EXIF-alakú ISO helyi idő."""
    return (_MOST + delta).isoformat(timespec="seconds")


@pytest.fixture
def conn(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    with open_index(tmp_path / "index.db") as connection:
        yield connection, root


def _felvesz(connection, root, sorok):
    """Képeket vesz az indexbe, majd beállítja a vizsgált mezőket.

    `sorok`: név -> (taken_at, taken_at_override, mtime_ns). A felvétel
    sorrendje a dict sorrendje (növekvő `id`)."""
    for nev in sorok:
        (root / nev).write_bytes(nev.encode())
        sync_tree(connection, root)
    for nev, (taken_at, override, mtime_ns) in sorok.items():
        connection.execute(
            "UPDATE photos SET taken_at = ?, taken_at_override = ?, mtime_ns = ?"
            " WHERE name = ?",
            (taken_at, override, mtime_ns, nev),
        )
    connection.commit()


def _nevek(connection, **kwargs):
    return [
        p.name
        for p in recently_updated_photos(connection, cutoff_ns=_KUSZOB_NS, **kwargs)
    ]


def test_regi_exif_es_friss_mtime_kimarad(conn):
    connection, root = conn
    _felvesz(connection, root, {
        "arc04.jpg": ("2017-05-01T12:00:00", None, _MOST_NS - _NAP_NS),
    })
    assert _nevek(connection) == []
    assert count_recently_updated_photos(connection, cutoff_ns=_KUSZOB_NS) == 0


def test_friss_exif_es_friss_mtime_bekerul(conn):
    connection, root = conn
    _felvesz(connection, root, {
        "friss.jpg": (_iso(-timedelta(days=2)), None, _MOST_NS - _NAP_NS),
    })
    assert _nevek(connection) == ["friss.jpg"]
    assert count_recently_updated_photos(connection, cutoff_ns=_KUSZOB_NS) == 1


def test_friss_exif_regi_mtime_is_bekerul(conn):
    """A dátumkulcs az EXIF-dátum, nem a fájlidő: a régi fájlidő nem zárja ki."""
    connection, root = conn
    _felvesz(connection, root, {
        "friss.jpg": (_iso(-timedelta(days=2)), None, _MOST_NS - 30 * _NAP_NS),
    })
    assert _nevek(connection) == ["friss.jpg"]


def test_exif_nelkul_friss_mtime_bekerul(conn):
    connection, root = conn
    _felvesz(connection, root, {
        "arc01.jpg": (None, None, _MOST_NS - _NAP_NS),
    })
    assert _nevek(connection) == ["arc01.jpg"]
    assert count_recently_updated_photos(connection, cutoff_ns=_KUSZOB_NS) == 1


def test_exif_nelkul_regi_mtime_kimarad(conn):
    connection, root = conn
    _felvesz(connection, root, {
        "regi.jpg": (None, None, _MOST_NS - 8 * _NAP_NS),
    })
    assert _nevek(connection) == []


def test_hibas_exif_szoveg_a_fajlidore_esik_vissza(conn):
    connection, root = conn
    _felvesz(connection, root, {
        "hibas_friss.jpg": ("nem-datum", None, _MOST_NS - _NAP_NS),
        "hibas_regi.jpg": ("nem-datum", None, _MOST_NS - 8 * _NAP_NS),
    })
    assert _nevek(connection) == ["hibas_friss.jpg"]


def test_kezi_datum_elsobbseget_elvez_friss_override_bekerul(conn):
    """A dátumállító az első párba ír: a friss kézi dátum a régi EXIF-et is felülírja."""
    connection, root = conn
    _felvesz(connection, root, {
        "kezi.jpg": (
            "2017-05-01T12:00:00", _iso(-timedelta(days=1)), _MOST_NS - 30 * _NAP_NS
        ),
    })
    assert _nevek(connection) == ["kezi.jpg"]
    assert count_recently_updated_photos(connection, cutoff_ns=_KUSZOB_NS) == 1


def test_kezi_datum_elsobbseget_elvez_regi_override_kizar(conn):
    """A régi kézi dátum a friss EXIF-dátumot és a friss fájlidőt is felülírja."""
    connection, root = conn
    _felvesz(connection, root, {
        "kezi.jpg": (
            _iso(-timedelta(days=1)), "2017-05-01T12:00:00", _MOST_NS - _NAP_NS
        ),
    })
    assert _nevek(connection) == []
    assert count_recently_updated_photos(connection, cutoff_ns=_KUSZOB_NS) == 0


def test_kezi_datum_exif_nelkuli_kepnel_is_szamit(conn):
    connection, root = conn
    _felvesz(connection, root, {
        "kezi.jpg": (None, _iso(-timedelta(days=1)), _MOST_NS - 30 * _NAP_NS),
        "regi_kezi.jpg": (None, "2017-05-01T12:00:00", _MOST_NS - _NAP_NS),
    })
    assert _nevek(connection) == ["kezi.jpg"]


def test_hibas_kezi_datum_az_exif_re_esik_vissza(conn):
    """Hibás override nem tünteti el a képet: az EXIF-dátum, majd a fájlidő dönt."""
    connection, root = conn
    _felvesz(connection, root, {
        "exif_friss.jpg": (_iso(-timedelta(days=1)), "nem-datum", _MOST_NS - 30 * _NAP_NS),
        "exif_regi.jpg": ("2017-05-01T12:00:00", "nem-datum", _MOST_NS - _NAP_NS),
    })
    assert _nevek(connection) == ["exif_friss.jpg"]


def test_hatar_szigoru_nagyobb_mint(conn):
    """A küszöb pontosan a határon kizár (szigorú >), egy másodperccel utána bent van."""
    connection, root = conn
    _felvesz(connection, root, {
        "hataron.jpg": (_iso(-timedelta(days=7)), None, _MOST_NS - 30 * _NAP_NS),
        "hatar_utan.jpg": (
            _iso(-timedelta(days=7) + timedelta(seconds=1)), None, _MOST_NS - 30 * _NAP_NS
        ),
    })
    assert _nevek(connection) == ["hatar_utan.jpg"]


def test_sorrend_es_korlat_a_datumkulcs_mellett_valtozatlan(conn):
    """Vegyes tagság mellett a sorrend a rekordsorrend fordítottja, a korlát a tagokra áll."""
    connection, root = conn
    _felvesz(connection, root, {
        "a_exif_friss.jpg": (_iso(-timedelta(days=1)), None, _MOST_NS - 30 * _NAP_NS),
        "b_exif_regi.jpg": ("2017-05-01T12:00:00", None, _MOST_NS - _NAP_NS),
        "c_exif_nelkul.jpg": (None, None, _MOST_NS - _NAP_NS),
        "d_kezi.jpg": ("2017-05-01T12:00:00", _iso(-timedelta(days=3)), _MOST_NS - 30 * _NAP_NS),
        "e_exif_friss.jpg": (_iso(-timedelta(days=6)), None, _MOST_NS - _NAP_NS),
    })
    assert _nevek(connection) == [
        "e_exif_friss.jpg", "d_kezi.jpg", "c_exif_nelkul.jpg", "a_exif_friss.jpg",
    ]
    # a korlát a tagokra vonatkozik: a kizárt b_exif_regi nem foglal helyet
    assert _nevek(connection, limit=3) == [
        "e_exif_friss.jpg", "d_kezi.jpg", "c_exif_nelkul.jpg",
    ]
    assert count_recently_updated_photos(connection, cutoff_ns=_KUSZOB_NS) == 4
    assert count_recently_updated_photos(connection, cutoff_ns=_KUSZOB_NS, limit=3) == 3


def test_alapertelmezett_kuszob_is_a_datumkulcsot_hasznalja(conn):
    """A `]updated` album (alapértelmezett, élő küszöb) ugyanazt a kulcsot követi."""
    connection, root = conn
    most = datetime.now()
    _felvesz(connection, root, {
        "regi_exif.jpg": ("2017-05-01T12:00:00", None, int(most.timestamp() * _NS)),
        "friss_exif.jpg": (
            (most - timedelta(days=1)).isoformat(timespec="seconds"),
            None,
            int((most - timedelta(days=30)).timestamp() * _NS),
        ),
        "exif_nelkul.jpg": (None, None, int(most.timestamp() * _NS)),
    })
    assert [p.name for p in album_photos(connection, "]updated")] == [
        "exif_nelkul.jpg", "friss_exif.jpg",
    ]
    assert [p.name for p in recently_updated_photos(connection)] == [
        "exif_nelkul.jpg", "friss_exif.jpg",
    ]


def _jpeg(path, exif_datum: bytes | None):
    kep = Image.new("RGB", (8, 8), (10, 20, 30))
    if exif_datum is None:
        kep.save(path, "JPEG")
        return
    exif = piexif.dump({"Exif": {piexif.ExifIFD.DateTimeOriginal: exif_datum}})
    kep.save(path, "JPEG", exif=exif)


def test_valodi_szinkron_a_taken_at_az_exif_bol_jon_es_exif_nelkul_ures(conn):
    """Végig a valódi úton: JPEG-ek EXIF-fel és anélkül, friss fájlidővel."""
    connection, root = conn
    most = datetime.now()
    frissfajl = (most - timedelta(hours=1)).timestamp()
    friss_exif = (most - timedelta(days=2)).strftime("%Y:%m:%d %H:%M:%S").encode()

    _jpeg(root / "arc04.jpg", b"2017:05:01 12:00:00")
    _jpeg(root / "friss.jpg", friss_exif)
    _jpeg(root / "arc01.jpg", None)
    _jpeg(root / "hibas.jpg", b"nem datum       ")
    for nev in ("arc04.jpg", "friss.jpg", "arc01.jpg", "hibas.jpg"):
        os.utime(root / nev, (frissfajl, frissfajl))
    sync_tree(connection, root)

    taken = {
        r["name"]: r["taken_at"]
        for r in connection.execute("SELECT name, taken_at FROM photos")
    }
    assert taken["arc04.jpg"] == "2017-05-01T12:00:00"
    assert taken["friss.jpg"] is not None
    assert taken["arc01.jpg"] is None
    assert taken["hibas.jpg"] is None

    # az mtime_ns a változásérzékelésé marad: a fájlidőt tükrözi
    for r in connection.execute("SELECT mtime_ns FROM photos"):
        assert abs(r["mtime_ns"] / _NS - frissfajl) < 2

    nevek = {p.name for p in recently_updated_photos(connection)}
    assert nevek == {"friss.jpg", "arc01.jpg", "hibas.jpg"}
    assert "arc04.jpg" not in nevek
