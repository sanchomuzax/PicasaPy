"""Picasa-kompatibilis fájltípus-felismerés (forrás: NotebookLM / Picasa help)."""

import pytest

from picasapy.scanner import media_kind_of


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
        "name", ["a.txt", "b.webp", ".picasa.ini", "c.pdf", "noextension", "d.jpg.bak"]
    )
    def test_non_media(self, name):
        # A WebP-t a Picasa nem támogatta — mi is csak később, tudatosan vesszük fel.
        assert media_kind_of(name) is None

    def test_case_insensitive(self):
        assert media_kind_of("KÉP.JPG") == "photo"
