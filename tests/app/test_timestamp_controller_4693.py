"""A dátumállítás EXIF- és fájlidő-ágai (#4693)."""

from __future__ import annotations

import os
from datetime import datetime

import piexif
import pytest

from picasapy.app import timestamp_controller
from support.jpeg_factory import make_jpeg


CEL_DATUM = datetime(2020, 2, 3, 4, 5, 6)
REGI_DATUM = datetime(2020, 1, 1, 4, 5, 6)


def _timestamp_ns(ertek: datetime) -> int:
    return round(ertek.timestamp() * 1_000_000_000)


def _fajlido_beallitasa(path, atime: datetime, mtime: datetime) -> None:
    os.utime(path, ns=(_timestamp_ns(atime), _timestamp_ns(mtime)))


def _fajlido(path) -> tuple[int, int, int]:
    stat = path.stat()
    return stat.st_atime_ns, stat.st_mtime_ns, stat.st_ctime_ns


@pytest.mark.parametrize(
    "datetime_0th",
    [None, "invalid date"],
    ids=["hianyzik", "ervenytelen"],
)
def test_hianyzo_vagy_hibas_datetime_megoriz_minden_fajlidot(
    tmp_path, datetime_0th
):
    path = make_jpeg(
        tmp_path / "kep.jpg",
        taken_at="2019:02:03 04:05:06",
        datetime_0th=datetime_0th,
    )
    _fajlido_beallitasa(
        path,
        datetime(2018, 1, 2, 3, 4, 5),
        datetime(2018, 2, 3, 4, 5, 6),
    )
    before = _fajlido(path)

    timestamp_controller._adjust_photo_file_date(path, CEL_DATUM)

    after = _fajlido(path)
    assert after[:2] == before[:2]
    if os.name == "nt":
        assert after[2] == before[2]
    exif = piexif.load(str(path))
    assert exif["Exif"][piexif.ExifIFD.DateTimeOriginal] == b"2020:02:03 04:05:06"
    assert not path.with_suffix(path.suffix + ".tmp").exists()


def test_sikeres_exif_iras_datetime_alapjan_modositja_a_fajlidoket(tmp_path):
    path = make_jpeg(
        tmp_path / "kep.jpg",
        taken_at="2019:02:03 04:05:06",
        datetime_0th="2020:01:01 04:05:06",
    )
    _fajlido_beallitasa(
        path,
        datetime(2018, 1, 2, 3, 4, 5),
        datetime(2018, 2, 3, 4, 5, 6),
    )
    before = _fajlido(path)
    delta = CEL_DATUM - REGI_DATUM

    timestamp_controller._adjust_photo_file_date(path, CEL_DATUM)

    after = _fajlido(path)
    assert after[0] == before[0] + round(delta.total_seconds() * 1_000_000_000)
    assert after[1] == before[1] + round(delta.total_seconds() * 1_000_000_000)
    if os.name == "nt":
        assert after[2] == before[2]
    exif = piexif.load(str(path))
    assert exif["Exif"][piexif.ExifIFD.DateTimeOriginal] == b"2020:02:03 04:05:06"
    assert exif["0th"][piexif.ImageIFD.DateTime] == b"2020:01:01 04:05:06"
    assert not path.with_suffix(path.suffix + ".tmp").exists()


def test_sikertelen_exif_irasnal_a_tartalek_csak_a_letrehozasi_idot_allitja(
    tmp_path, monkeypatch
):
    path = make_jpeg(
        tmp_path / "kep.jpg",
        taken_at="2019:02:03 04:05:06",
        datetime_0th="2020:01:01 04:05:06",
    )
    _fajlido_beallitasa(
        path,
        datetime(2018, 1, 2, 3, 4, 5),
        datetime(2018, 2, 3, 4, 5, 6),
    )
    before = _fajlido(path)
    creation_times = []

    def exif_iras_hiba(_path, _target):
        raise OSError("EXIF írási hiba")

    monkeypatch.setattr(
        timestamp_controller, "_write_exif_datetime_original", exif_iras_hiba
    )
    if os.name != "nt":
        monkeypatch.setattr(
            timestamp_controller,
            "_set_creation_time_ns",
            lambda _path, value: creation_times.append(value),
        )

    timestamp_controller._adjust_photo_file_date(path, CEL_DATUM)

    after = _fajlido(path)
    # A tartalékág a hozzáférési és a módosítási időt nem írja; a hozzáférési
    # időt viszont a fájl olvasása a rendszer beállításától függően frissítheti
    # (Linuxon relatime), ezért itt csak a módosítási időt vetjük össze.
    assert after[1] == before[1]
    if os.name == "nt":
        assert after[2] == _timestamp_ns(CEL_DATUM)
    else:
        assert creation_times == [_timestamp_ns(CEL_DATUM)]
    assert (
        piexif.load(str(path))["Exif"][piexif.ExifIFD.DateTimeOriginal]
        == b"2019:02:03 04:05:06"
    )
