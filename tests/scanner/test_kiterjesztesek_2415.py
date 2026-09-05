"""#2415: `.jpe`, `.mpeg`, `.ty` — a Picasa binárisa mindhármat regisztrálja.

## A bizonyíték

A fájltípus-tábla egy 30 ágú ugrótáblás kapcsoló (`0x004fadb0`, tábla
`0x004fb948`); minden ága kiterjesztés-sztringeket regisztrál. A `.jpe` a
0. ágban (`.jpg`/`.jpeg` mellett, `0x004fadc1`), a `.mpeg` és a `.ty` a
8. ágban (`.mpg` mellett, `0x004fb0f1`).

Nálunk mindhárom hiányzott, tehát egy `foto.jpe` NÉMÁN kimaradt a
beolvasásból — ugyanaz a hibaosztály, mint a #2344-es `.webp`.

## Amit ez a fájl SZÁNDÉKOSAN nem állít

Hogy a nálunk szereplő, de a táblában literálként nem látszó videó-
kiterjesztések (`.3g2` … `.tod`) rosszak volnának. A 16. ág **dinamikusan**
tölti a listáját (`call 0x00a4c720`), tehát a literál-hiány ott **nem**
negatív bizonyíték. Ezért az alábbi őr azt is kimondja, hogy ezek
megmaradnak — a javítás nem vehet el semmit.
"""

from __future__ import annotations

import pytest

from picasapy.scanner.filetypes import (
    PHOTO_EXTENSIONS,
    VIDEO_EXTENSIONS,
    media_kind_of,
)

#: a #2415-ben kimért három hiányzó kiterjesztés, a várt besorolásával
HIANYZOTT = (
    ("a.jpe", "photo"),
    ("b.mpeg", "video"),
    ("c.ty", "video"),
)

#: a 16. ág dinamikus listájából — ezeket a javítás NEM veheti el
DINAMIKUS_AG = (
    ".3g2", ".3gp", ".m2t", ".m2ts", ".m4v", ".mkv", ".mmv", ".mod",
    ".mts", ".tod",
)


class TestAHaromHianyzoKiterjesztes:
    @pytest.mark.parametrize(("nev", "fajta"), HIANYZOTT)
    def test_a_fajl_a_helyes_fajtat_kapja(self, nev, fajta):
        assert media_kind_of(nev) == fajta, (
            f"a(z) {nev} némán kimaradna a beolvasásból (#2415)"
        )

    @pytest.mark.parametrize(("nev", "fajta"), HIANYZOTT)
    def test_a_NAGYBETUS_alak_is_atmegy(self, nev, fajta):
        assert media_kind_of(nev.upper()) == fajta

    def test_a_jpe_a_fenykep_halmazban_van(self):
        assert ".jpe" in PHOTO_EXTENSIONS

    def test_a_mpeg_es_a_ty_a_video_halmazban_van(self):
        assert {".mpeg", ".ty"} <= VIDEO_EXTENSIONS


class TestSemmiNemVeszettEl:
    """A 16. ág dinamikus listája nem cáfolható literál-hiánnyal."""

    @pytest.mark.parametrize("kiterjesztes", DINAMIKUS_AG)
    def test_a_dinamikus_ag_kiterjesztesei_megmaradtak(self, kiterjesztes):
        assert kiterjesztes in VIDEO_EXTENSIONS

    def test_a_webp_is_megmaradt(self):
        assert media_kind_of("d.webp") == "photo"

    def test_az_ismeretlen_tovabbra_is_None(self):
        assert media_kind_of("e.exe") is None


class TestAForrasMegnevezi_a_binaris_tablat:
    """A modul fejléce eddig CSAK a súgót nevezte meg forrásként."""

    def test_a_fejlec_hivatkozik_a_kapcsolotablara(self):
        from picasapy.scanner import filetypes

        fejlec = filetypes.__doc__ or ""
        assert "0x004fadb0" in fejlec and "0x004fb948" in fejlec, (
            "a fejléc nem nevezi meg a mért kapcsolótáblát (#2415)"
        )
