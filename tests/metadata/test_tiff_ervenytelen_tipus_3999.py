"""Az áthelyezés a 0-s (érvénytelen) típusú bejegyzést nem mozdítja előre (#3999).

Az érvénytelen típusú bejegyzés a forrásban ELŐTTE álló érvényes sor után marad
(a forrás végén állók a végén), csak az érvényes tagek rendeződnek tag szerint —
így az IFD elejére csak az kerülhet, ami a forrásban is elöl állt. (A spec ezt a
szabályt nem rögzíti; ez a mi döntésünk, az exiftool olvashatósága miatt.)
Az exiftool az IFD ELEJÉN álló 0-s típusra „Bad format (0)" hibával az egész
Exif IFD-t eldobja; a forrás végén álló szemét ártalmatlan."""

from __future__ import annotations

import shutil
import struct
import subprocess

import pytest

from picasapy.metadata import tiff_helyben as th

_EXIFTOOL = shutil.which("exiftool")


def _ifd(bejegyzesek, kezdet, kovetkezo=0):
    """Forrássorrendben, NEM rendezve: (tag, típus, darab, érték)."""
    n = len(bejegyzesek)
    adat_kezdet = kezdet + 2 + 12 * n + 4
    fej, adat = struct.pack("<H", n), b""
    for tag, tipus, darab, ertek in bejegyzesek:
        if len(ertek) <= 4:
            mezo = ertek.ljust(4, b"\x00")
        else:
            mezo = struct.pack("<I", adat_kezdet + len(adat))
            adat += ertek
        fej += struct.pack("<HHI", tag, tipus, darab) + mezo
    return fej + struct.pack("<I", kovetkezo) + adat


_DT = b"2020:01:02 03:04:05\x00"


def _forras(szemet_elol=False, exif_b=None):
    """IFD0 → Exif IFD [0x9000 UNDEFINED, 0x9003 ASCII, 0x0001 típus 0 a végén],
    vagy a megadott (forrássorrendű) Exif-bejegyzések."""
    if exif_b is None:
        szemet = (0x0001, 0, 1, b"\x00\x00\x00\x00")
        exif_b = [(0x9000, 7, 4, b"0230"), (0x9003, 2, len(_DT), _DT)]
        exif_b = [szemet, *exif_b] if szemet_elol else [*exif_b, szemet]
    ifd0_hossz = len(_ifd([(0x010F, 2, 5, b"Test\x00"), (0x8769, 4, 1, b"\0\0\0\0")], 8))
    exif_off = 8 + ifd0_hossz
    ifd0 = _ifd([(0x010F, 2, 5, b"Test\x00"), (0x8769, 4, 1, struct.pack("<I", exif_off))], 8)
    return b"II" + struct.pack("<HI", 42, 8) + ifd0 + _ifd(exif_b, exif_off)


def _exif_sorrend(tiff):
    """Az Exif IFD (tag, típus) párjai a fájlbeli sorrendben."""
    (ifd0_n,) = struct.unpack_from("<H", tiff, 8)
    mutato = next(
        struct.unpack_from("<I", tiff, 8 + 2 + 12 * i + 8)[0]
        for i in range(ifd0_n)
        if struct.unpack_from("<H", tiff, 8 + 2 + 12 * i)[0] == 0x8769
    )
    (n,) = struct.unpack_from("<H", tiff, mutato)
    return [struct.unpack_from("<HH", tiff, mutato + 2 + 12 * i) for i in range(n)]


def _uj_tag():
    return [th.Valtozas("Exif", 0x9286, th.Ertek(7, b"ASCII\x00\x00\x00hi"))]


def test_szemet_a_forrasbeli_helyen_marad():
    kimenet = th.frissitett_tiff(_forras(), _uj_tag())
    assert _exif_sorrend(kimenet) == [(0x9000, 7), (0x9003, 2), (0x9286, 7), (0x0001, 0)]


def test_szemet_elol_a_forrasban_elol_marad():
    kimenet = th.frissitett_tiff(_forras(szemet_elol=True), _uj_tag())
    assert _exif_sorrend(kimenet) == [(0x0001, 0), (0x9000, 7), (0x9003, 2), (0x9286, 7)]


def test_ervenyes_tagek_tovabbra_is_rendezettek():
    kimenet = th.frissitett_tiff(
        _forras(), [th.Valtozas("Exif", 0x8000, th.Ertek(7, b"abcd"))]
    )
    tagek = [t for t, ty in _exif_sorrend(kimenet) if ty != 0]
    assert tagek == sorted(tagek)


@pytest.mark.skipif(_EXIFTOOL is None, reason="nincs exiftool")
def test_exiftool_hiba_nelkul_olvassa(tmp_path):
    kimenet = th.frissitett_tiff(_forras(), _uj_tag())
    _exiftool_olvassa(tmp_path, kimenet)


def _exiftool_olvassa(tmp_path, tiff):
    fajl = tmp_path / "exif.tif"
    fajl.write_bytes(tiff)

    def futtat(*kapcsolok):
        ki = subprocess.run(
            [_EXIFTOOL, *kapcsolok, str(fajl)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        )
        return ki.stdout + ki.stderr

    # a `-validate -warning` sorolja fel a figyelmeztetéseket, a tagek külön futásban
    assert "entry 0" not in futtat("-validate", "-warning", "-a")
    tagek = futtat("-a", "-G1", "-s")
    for tag in ("DateTimeOriginal", "ExifVersion", "UserComment"):
        assert tag in tagek


# rendezetlen forrás (a valódi Exif IFD-k ~18%-a): a szemét a forrásbeli
# ELŐZŐ érvényes sorhoz tapad, így nem kerülhet a 0. helyre
_RENDEZETLEN = [
    [(0x9003, 2, len(_DT), _DT), (0x0001, 0, 1, b"\0\0\0\0"), (0x9000, 7, 4, b"0230")],
    [(0x9003, 2, len(_DT), _DT), (0xFFFF, 0, 1, b"\0\0\0\0"), (0x9000, 7, 4, b"0230")],
]


@pytest.mark.parametrize("exif_b", _RENDEZETLEN)
def test_rendezetlen_forrasnal_a_szemet_nem_kerul_elore(exif_b):
    szemet_tag = exif_b[1][0]
    kimenet = th.frissitett_tiff(_forras(exif_b=exif_b), _uj_tag())
    sorrend = _exif_sorrend(kimenet)
    assert sorrend[0][1] != 0
    assert sorrend == [(0x9000, 7), (0x9003, 2), (szemet_tag, 0), (0x9286, 7)]


@pytest.mark.skipif(_EXIFTOOL is None, reason="nincs exiftool")
@pytest.mark.parametrize("exif_b", _RENDEZETLEN)
def test_rendezetlen_forrast_az_exiftool_olvassa(tmp_path, exif_b):
    _exiftool_olvassa(tmp_path, th.frissitett_tiff(_forras(exif_b=exif_b), _uj_tag()))
