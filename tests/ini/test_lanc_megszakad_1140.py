"""A `filters=` lánc a HIBÁS TAGNÁL megszakad (#1140).

## A lelet

Az eredeti Picasa lánc-bejárója **az első hibás tagnál megáll**, és ami
előtte volt, azt alkalmazza. Nálunk két dolog tér el:

1. a hibás tagot **elejtettük**, és a mögötte állókat is lefuttattuk;
2. az `=` NÉLKÜLI tag **kivételt dobott**, és ettől a kép **egyáltalán nem
   exportálódott**.

A második a súlyosabb: nem romlott kép, hanem **hiányzó** kép.

## A mért bizonyíték (mérőkit-3, ugyanarról a képről)

| lánc | a Picasa kimenete |
|---|---|
| `sepia=1;bw=1;` | mindkettő lefut |
| `nincsilyen=1;bw=1;` | **a forrás, érintetlenül** — a `bw` NEM fut le |
| `sepia=1;nincsilyen=1;` | a `sepia` lefut |
| `grain2=1,0.500000;bw=1;` (rossz paraméterszám) | **a forrás** |
| `sepia;bw=1;` (nincs `=`) | **a forrás — de EXPORTÁL** |

Vagyis mindegyik eset ugyanaz a szabály: **a lánc a hibás tagnál elvágódik,
a művelet pedig soha nem hiúsul meg tőle.**
"""

from __future__ import annotations

import pytest

from picasapy.ini.filters import parse_filters, parse_filters_prefix


class TestSzigoruParser:
    """A szigorú parser marad — az ÍRÓ ágnak tudnia kell a hibáról."""

    def test_ervenytelen_tagra_hibat_dob(self):
        with pytest.raises(ValueError):
            parse_filters("sepia;bw=1;")


class TestLancElvagas:
    """A RENDERELŐ/EXPORTÁLÓ ág: elvágás, soha nem kivétel."""

    def test_ep_lanc_valtozatlan(self):
        ops = parse_filters_prefix("sepia=1;bw=1;")
        assert [op.name for op in ops] == ["sepia", "bw"]

    def test_egyenlosegjel_nelkuli_tagnal_elvag(self):
        """⚠️ Ez az eset buktatta el az EGÉSZ exportot."""
        assert parse_filters_prefix("sepia;bw=1;") == ()

    def test_a_hibas_tag_MOGOTTIT_sem_futtatjuk(self):
        """A hibás tag után álló `bw` NEM futhat le.

        A régi viselkedés a hibás tagot elejtette és továbbment — a mérés
        szerint az eredeti ilyenkor a FORRÁST adja vissza."""
        ops = parse_filters_prefix("sepia=1;nincs;bw=1;")
        assert [op.name for op in ops] == ["sepia"]

    def test_ures_lanc_ures_eredmeny(self):
        assert parse_filters_prefix("") == ()


def test_az_EXPORT_nem_hiusul_meg_hibas_lanctol(tmp_path):
    """A tulajdonos felé ez a jegy lényege: nem hiányozhat kép.

    ⚠️ A régi ág `ValueError`-t dobott az `=` nélküli tagra, és a kép a
    `failed` listára került — a felhasználó KEVESEBB képet kapott, mint
    amennyit kijelölt, és nem is tudta, miért."""
    import numpy as np
    import cv2

    from picasapy.export import exporter

    forras = tmp_path / "kep.jpg"
    cv2.imwrite(str(forras), np.full((60, 80, 3), 128, np.uint8))
    cel = tmp_path / "ki"
    cel.mkdir()

    tetel = exporter.ExportItem(source=forras, filters="sepia;bw=1;")
    eredmeny = exporter.export_photos([tetel], cel, exporter.ExportSettings())

    assert not eredmeny.failed, f"a kép nem exportálódott: {eredmeny.failed}"
    assert list(cel.glob("*.jpg")), "nem született kimeneti fájl"
