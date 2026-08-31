"""#1642 — a „Másolat mentése" kimenete metaadat-aláírást kap.

A tulajdonos referencia-mérése (`research/testdata/1557-masolat-mentese/`,
valódi Picasa 3.9) szerint a másolat EXIF-et és XMP-t is kap, a forrás
viszont érintetlen marad:

| | forrás | másolat |
|---|---|---|
| EXIF | nincs egyáltalán | `Software`, `Artist`, `DateTime` |
| XMP | nincs | `dc:creator`, `xmp:ModifyDate`, `exif:DateTimeOriginal` |

⚠️ **A dátum-megőrzés a lényeg.** Az `exif:DateTimeOriginal` a mintában a
FORRÁS eredeti ideje (2026-07-16 20:04:11), miközben a `ModifyDate` a
másolás pillanata.

⚠️ **Egy szándékos eltérés:** az eredeti mindhárom név-mezőbe a `Picasa`
szót írja; mi a sajátunkat (`PicasaPy`). Nem adjuk ki magunkat a Google
termékének — a jegy ezt kifejezetten előírja, és ezt külön teszt őrzi.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import numpy as np

from picasapy.edit.save_copy import save_copy
from picasapy.edit.session import EditSession
from picasapy.metadata.copy_signature import ALAIRAS

#: a forrás „felvételi ideje" a próbákban — szándékosan RÉGI, hogy a
#: megőrzés ne legyen összetéveszthető a mostani idővel
REGI_IDO = datetime(2019, 7, 16, 20, 4, 11)


def _kep(path, ertek: int = 128) -> None:
    import cv2

    cv2.imwrite(str(path), np.full((8, 8, 3), ertek, dtype=np.uint8))


def _forras(tmp_path: Path) -> Path:
    forras = tmp_path / "kep.jpg"
    _kep(forras)
    os.utime(forras, (REGI_IDO.timestamp(), REGI_IDO.timestamp()))
    return forras


def _masol(forras: Path) -> Path:
    return save_copy(
        forras,
        np.full((8, 8, 3), 200, dtype=np.uint8),
        EditSession.from_value("autolight=1;"),
    ).target_path


class TestExifAlairas:
    def test_a_masolat_exifje_tartalmazza_a_harom_mezot(self, tmp_path):
        import piexif

        cel = _masol(_forras(tmp_path))
        adat = piexif.load(str(cel))
        zeroth = adat["0th"]
        for cimke, nev in (
            (piexif.ImageIFD.Software, "Software"),
            (piexif.ImageIFD.Artist, "Artist"),
            (piexif.ImageIFD.DateTime, "DateTime"),
        ):
            assert cimke in zeroth, f"hiányzik az EXIF {nev} mező (#1642)"

    def test_a_nev_a_MIENK_nem_Picasa(self, tmp_path):
        """Nem adjuk ki magunkat a Google termékének."""
        import piexif

        cel = _masol(_forras(tmp_path))
        zeroth = piexif.load(str(cel))["0th"]
        for cimke in (piexif.ImageIFD.Software, piexif.ImageIFD.Artist):
            ertek = zeroth[cimke].decode("ascii", "ignore").strip("\x00 ")
            assert ertek == ALAIRAS == "PicasaPy", (
                f"az aláírás {ertek!r} — a sajátunknak kell lennie, nem "
                "„Picasa”-nak (#1642)"
            )

    def test_az_eredeti_datum_atkerul_a_masolatba(self, tmp_path):
        """A jegy lényegi kérése: a FORRÁS ideje őrződjön meg."""
        import piexif

        cel = _masol(_forras(tmp_path))
        nyers = piexif.load(str(cel))["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
        assert nyers, "hiányzik a DateTimeOriginal — a dátum nem őrződött meg"
        assert nyers.decode("ascii").strip("\x00 ") == REGI_IDO.strftime(
            "%Y:%m:%d %H:%M:%S"
        ), "a másolat a MOSTANI időt kapta, nem a forrásét (#1642)"


class TestXmpAlairas:
    def test_a_masolat_xmpje_tartalmazza_a_harom_mezot(self, tmp_path):
        cel = _masol(_forras(tmp_path))
        bajtok = cel.read_bytes()
        assert b"http://ns.adobe.com/xap/1.0/" in bajtok, (
            "nincs XMP-szegmens a másolatban (#1642)"
        )
        szoveg = bajtok.decode("latin-1")
        for mezo in ("dc:creator", "xmp:ModifyDate", "exif:DateTimeOriginal"):
            assert mezo in szoveg, f"hiányzik az XMP {mezo} mező (#1642)"
        assert ALAIRAS in szoveg

    def test_az_xmp_eredeti_datuma_a_forrase(self, tmp_path):
        cel = _masol(_forras(tmp_path))
        szoveg = cel.read_bytes().decode("latin-1")
        assert f'exif:DateTimeOriginal="{REGI_IDO.year:04d}-' in szoveg, (
            "az XMP DateTimeOriginal nem a forrás évét viseli (#1642)"
        )

    def test_a_kep_megnyithato_marad(self, tmp_path):
        """A szegmens-beszúrás nem ronthatja el a JPEG-et."""
        import cv2

        cel = _masol(_forras(tmp_path))
        kep = cv2.imread(str(cel))
        assert kep is not None, "a metaadattal ellátott JPEG nem olvasható"
        assert kep.shape == (8, 8, 3)


class TestAForrasErintetlen:
    def test_a_forras_bajtra_valtozatlan(self, tmp_path):
        forras = _forras(tmp_path)
        elotte = forras.read_bytes()
        _masol(forras)
        assert forras.read_bytes() == elotte, (
            "a másolás megváltoztatta a FORRÁS fájlt (#1642)"
        )
