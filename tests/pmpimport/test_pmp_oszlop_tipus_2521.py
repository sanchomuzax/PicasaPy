"""#2521 — a `.pmp` oszlop TÍPUSA a regisztrált oszlopéhoz mérve.

## A hiba, amit ez megelőz

A `read_pmp_column` a típuskódot a fájl SAJÁT fejlécéből veszi, és csak azt
nézi, hogy a fejléc két típusmezője egyezik-e. **Nincs ellenőrzés arra,
hogy az adott OSZLOPNAK ez-e a helyes típusa.** Egy sérült vagy összekevert
`.pmp` így NÉMÁN rossz értéket ad — a #2106 pontosan ilyen volt: a
`0x07`-es `imagedata_edit_width` oszlopot előjel NÉLKÜL olvastuk, és −86
helyett 4 294 967 210 jött ki.

## A hiteles forrás

A Picasa 3.9 binárisából mostantól megvan mind a 44 `imagedata` oszlop
típusa — nem adatból következtetve, hanem a regisztráló hívás célcíméből
(`docs/specs/picasa-imagedata-rekord.md`, PR #2520). A nyolc `CColumn<…>`
konstruktor RTTI-vel azonosítva; a sablon harmadik paramétere
`0x13320000 + típuskód`.

## ⚠️ A `star` KIVÉTEL — és ez nem lazaság

A 3.9 az `imagedata_star.pmp`-t **nem regisztrálja**: a csillagozást a
`starlist.txt`-ből olvassa (#2335). Nálunk az oszlop olvasása MEGMARAD (a
régebbi adatbázisok miatt), de típus-elvárás nélkül — különben egy örökölt,
jogos fájlt utasítanánk el.
"""

from __future__ import annotations

import struct

import pytest

from picasapy.pmpimport.pmp_column import (
    PmpFormatError,
    read_pmp_column,
)

MAGIC = 0x3FCCCCCD
CONST_1332 = 0x1332
CONST_2 = 0x00000002


def _pmp(tmp_path, nev: str, field_type: int, body: bytes, count: int):
    fej = struct.pack(
        "<IHHIHHI", MAGIC, field_type, CONST_1332, CONST_2,
        field_type, CONST_1332, count,
    )
    ut = tmp_path / nev
    ut.write_bytes(fej + body)
    return ut


class TestATablaTeljes:
    def test_mind_a_kilenc_importalt_oszlop_szerepel(self):
        from picasapy.pmpimport.importer import _COLUMNS
        from picasapy.pmpimport.pmp_column import OSZLOP_TIPUSOK

        for nev in _COLUMNS:
            assert nev in OSZLOP_TIPUSOK, (
                f"a(z) `{nev}` oszlopnak nincs bejegyzése a típus-táblában"
            )

    def test_a_MERT_tipusok(self):
        from picasapy.pmpimport.pmp_column import OSZLOP_TIPUSOK

        assert OSZLOP_TIPUSOK["caption"] == 0x00
        assert OSZLOP_TIPUSOK["rotate"] == 0x00
        assert OSZLOP_TIPUSOK["filters"] == 0x00
        assert OSZLOP_TIPUSOK["deferredregion"] == 0x00
        assert OSZLOP_TIPUSOK["tags"] == 0x06
        assert OSZLOP_TIPUSOK["crop64"] == 0x04
        assert OSZLOP_TIPUSOK["lat"] == 0x02
        assert OSZLOP_TIPUSOK["long"] == 0x02

    def test_a_star_OROKOLT_tipus_elvaras_nelkul(self):
        """A 3.9 nem regisztrálja; a `starlist.txt`-ből olvas (#2335)."""
        from picasapy.pmpimport.pmp_column import OSZLOP_TIPUSOK

        assert "star" in OSZLOP_TIPUSOK
        assert OSZLOP_TIPUSOK["star"] is None


class TestAzEltéresBESZEDES:
    def test_a_lat_oszlop_ROSSZ_tipussal_hibat_ad(self, tmp_path):
        """A jegy nevesített próbája: `imagedata_lat.pmp` `0x01` fejléccel
        a mért `0x02` helyett. MA ez némán u32-t olvasna."""
        ut = _pmp(tmp_path, "imagedata_lat.pmp", 0x01, struct.pack("<I", 7), 1)

        with pytest.raises(PmpFormatError) as hiba:
            read_pmp_column(ut, oszlop="lat")

        uzenet = str(hiba.value)
        assert "lat" in uzenet
        assert "0x2" in uzenet or "0x02" in uzenet, uzenet
        assert "0x1" in uzenet or "0x01" in uzenet, uzenet

    def test_a_HELYES_tipus_atmegy(self, tmp_path):
        ut = _pmp(tmp_path, "imagedata_lat.pmp", 0x02, struct.pack("<d", 1.5), 1)
        assert read_pmp_column(ut, oszlop="lat").values == (1.5,)

    def test_a_star_BARMILYEN_tipussal_atmegy(self, tmp_path):
        """Örökölt oszlop — nincs mihez mérni."""
        ut = _pmp(tmp_path, "imagedata_star.pmp", 0x03, bytes([1]), 1)
        assert read_pmp_column(ut, oszlop="star").values == (1,)

    def test_ISMERETLEN_oszlopnevre_nincs_elvaras(self, tmp_path):
        """A táblán kívüli oszlop olvasása a régi úton megy — nem
        utasítunk el olyat, amiről nincs mért állításunk."""
        ut = _pmp(tmp_path, "valami.pmp", 0x01, struct.pack("<I", 3), 1)
        assert read_pmp_column(ut, oszlop="nincs_ilyen").values == (3,)

    def test_oszlopnev_NELKUL_a_regi_viselkedes(self, tmp_path):
        """A paraméter opcionális — a meglévő hívók változatlanok."""
        ut = _pmp(tmp_path, "imagedata_lat.pmp", 0x01, struct.pack("<I", 7), 1)
        assert read_pmp_column(ut).values == (7,)


class TestABeolvasoHASZNALJA:
    def test_a_tabla_olvasoja_atadja_az_oszlopnevet(self):
        """Enélkül a tábla ott volna, de senki nem nézné meg.

        A hívás a `table.read_pmp_table`-ben van (az `importer` ezen át jut
        az oszlopokhoz) — ott kell átmennie az oszlopnévnek.
        """
        import inspect

        from picasapy.pmpimport import table as importer

        forras = inspect.getsource(importer)
        kod = "\n".join(
            sor for sor in forras.splitlines()
            if not sor.lstrip().startswith("#")
        )
        assert "oszlop=" in kod, (
            "az importőr a `read_pmp_column`-t oszlopnév NÉLKÜL hívja — a "
            "típus-tábla így soha nem fut le"
        )
