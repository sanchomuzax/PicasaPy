"""Picasa-kompatibilis fájltípus-felismerés (forrás: NotebookLM / Picasa help)."""

import pytest

from picasapy.scanner import media_kind_of
from picasapy.scanner.filetypes import PHOTO_EXTENSIONS


class TestMediaKind:
    @pytest.mark.parametrize("name", ["a.jpg", "b.JPEG", "c.png", "d.tif", "e.psd", "f.tga"])
    def test_photos(self, name):
        assert media_kind_of(name) == "photo"

    @pytest.mark.parametrize("name", ["a.cr2", "b.NEF", "c.dng", "d.arw", "e.rw2", "f.x3f"])
    def test_raw(self, name):
        assert media_kind_of(name) == "raw"

    @pytest.mark.parametrize("name", ["a.mp4", "b.AVI", "c.mov", "d.mkv", "e.m2ts", "f.3gp"])
    def test_video(self, name):
        assert media_kind_of(name) == "video"

    @pytest.mark.parametrize(
        "name", ["a.txt", ".picasa.ini", "c.pdf", "noextension", "d.jpg.bak"]
    )
    def test_non_media(self, name):
        # #2344: a `b.webp` KIKERÜLT innen. A lista a téves feltevést
        # kódolta („a Picasa nem támogatta"), és ezzel az ÉLES hibát is
        # zölden tartotta: a WebP-képek némán eltűntek a beolvasásból.
        # A valóság: `SupportWEBP` alapértéke 1, a bináris ismeri a
        # kiterjesztést, és a tulajdonos katalógusában van ilyen fájl.
        assert media_kind_of(name) is None

    def test_case_insensitive(self):
        assert media_kind_of("KÉP.JPG") == "photo"


class TestWebp2344:
    """#2344: a Picasa alapból indexeli a WebP-t — nálunk kimaradt.

    A modul fejléce korábban azt állította, hogy „a Picasa nem támogatta".
    Ez téves volt: a `SupportWEBP` beállítás alapértéke **1**, a bináris
    ismeri a kiterjesztést (`.webp` a `0x00467ca0`-n, `*.webp;` a
    fájlszűrő-listában), és a tulajdonos valódi `thumbindex.db`-jében van
    ilyen fájl. A WebP-képek emiatt némán eltűntek a beolvasásból.
    """

    @pytest.mark.parametrize(
        "nev", ["kep.webp", "kep.WEBP", "kep.WebP", "mappa/alkonyat.webp"]
    )
    def test_a_webp_fotokent_ismerodik_fel(self, nev):
        assert media_kind_of(nev) == "photo"

    def test_a_webp_benne_van_a_keszletben(self):
        assert ".webp" in PHOTO_EXTENSIONS

    def test_a_tobbi_fotokiterjesztes_erintetlen(self):
        """A foga: a bővítés nem vehet el semmit."""
        for kiterjesztes in (
            ".jpeg", ".jpg", ".tif", ".tiff", ".bmp", ".gif", ".psd",
            ".png", ".tga",
        ):
            assert kiterjesztes in PHOTO_EXTENSIONS, kiterjesztes

    def test_a_nem_kep_tovabbra_sem_foto(self):
        assert media_kind_of("dokumentum.webpx") is None
        assert media_kind_of("archivum.zip") is None
