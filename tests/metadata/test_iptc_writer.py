"""IPTC-felirat írása JPEG-be — bájt-megőrző szegmens-műtét.

Picasa-viselkedés (spec, írási szabály #3): JPEG-nél a caption az IPTC-be
kerül, nem a .picasa.ini-be. Minden más bájt (képadat, EXIF, egyéb IPTC
mezők) érintetlen marad.
"""

import pytest

from picasapy.metadata import read_file_metadata, write_iptc_caption

from support.jpeg_factory import make_jpeg


def _segments(path):
    """A JPEG nem-APP13 szegmenseinek nyers bájtjai (összevetéshez)."""
    data = path.read_bytes()
    parts, pos = [], 2
    while pos < len(data) - 1 and data[pos] == 0xFF:
        marker = data[pos + 1]
        if marker == 0xDA:  # SOS — innen entrópia-adat
            parts.append(data[pos:])
            break
        length = int.from_bytes(data[pos + 2 : pos + 4], "big")
        if marker != 0xED:  # APP13 kihagyva
            parts.append(data[pos : pos + 2 + length])
        pos += 2 + length
    return parts


class TestWriteCaption:
    def test_caption_written_and_readable(self, tmp_path):
        photo = make_jpeg(tmp_path / "a.jpg")
        assert write_iptc_caption(photo, "balatoni naplemente")
        assert read_file_metadata(photo).caption == "balatoni naplemente"

    def test_unicode_caption(self, tmp_path):
        photo = make_jpeg(tmp_path / "a.jpg")
        write_iptc_caption(photo, "őszi túra — árvíztűrő tükörfúrógép")
        assert (
            read_file_metadata(photo).caption == "őszi túra — árvíztűrő tükörfúrógép"
        )

    def test_overwrite_keeps_keywords(self, tmp_path):
        photo = make_jpeg(
            tmp_path / "a.jpg", caption="régi", keywords=("balaton", "nyár")
        )
        write_iptc_caption(photo, "új felirat")
        meta = read_file_metadata(photo)
        assert meta.caption == "új felirat"
        assert meta.keywords == ("balaton", "nyár")

    def test_empty_caption_removes_dataset(self, tmp_path):
        photo = make_jpeg(tmp_path / "a.jpg", caption="törlendő")
        write_iptc_caption(photo, "")
        assert read_file_metadata(photo).caption is None

    def test_other_segments_byte_identical(self, tmp_path):
        # EXIF-fel és kép-adattal együtt: csak az APP13 változhat.
        photo = make_jpeg(
            tmp_path / "a.jpg", taken_at="2025:05:01 07:23:10", orientation=6
        )
        before = _segments(photo)
        write_iptc_caption(photo, "felirat")
        assert _segments(photo) == before
        meta = read_file_metadata(photo)
        assert meta.taken_at == "2025-05-01T07:23:10"
        assert meta.orientation == 6

    def test_roundtrip_restores_original_bytes(self, tmp_path):
        # felirat rá, felirat le → bitre azonos fájl (nem volt IPTC előtte)
        photo = make_jpeg(tmp_path / "a.jpg")
        original = photo.read_bytes()
        write_iptc_caption(photo, "ideiglenes")
        write_iptc_caption(photo, "")
        assert photo.read_bytes() == original

    def test_non_jpeg_rejected(self, tmp_path):
        from PIL import Image

        png = tmp_path / "kep.png"
        Image.new("RGB", (8, 6), "blue").save(png, "PNG")
        assert write_iptc_caption(png, "x") is False

    def test_corrupt_file_rejected(self, tmp_path):
        bad = tmp_path / "rossz.jpg"
        bad.write_bytes(b"nem jpeg")
        assert write_iptc_caption(bad, "x") is False

    def test_replace_retried_then_succeeds(self, tmp_path, monkeypatch):
        # Windows: a célfájl átmenetileg zárolt (a néző tölti) → retry.
        import os as os_module

        import picasapy.metadata.iptc_writer as writer_module

        photo = make_jpeg(tmp_path / "a.jpg")
        original_replace = os_module.replace
        calls = {"n": 0}

        def flaky_replace(src, dst):
            calls["n"] += 1
            if calls["n"] < 3:
                raise PermissionError(13, "Access is denied")
            return original_replace(src, dst)

        monkeypatch.setattr(writer_module.os, "replace", flaky_replace)
        assert write_iptc_caption(photo, "zárolt közben")
        assert read_file_metadata(photo).caption == "zárolt közben"

    def test_replace_falls_back_to_direct_write(self, tmp_path, monkeypatch):
        # Ha a zár nem enged fel, nem-atomikus közvetlen írás (a képfájlnál
        # ez elfogadható fallback; az ini-nél nem — ott nincs ilyen).
        import picasapy.metadata.iptc_writer as writer_module

        photo = make_jpeg(tmp_path / "a.jpg")

        def always_denied(src, dst):
            raise PermissionError(13, "Access is denied")

        monkeypatch.setattr(writer_module.os, "replace", always_denied)
        monkeypatch.setattr(writer_module, "_RETRY_DELAY", 0.001)
        assert write_iptc_caption(photo, "fallback felirat")
        assert read_file_metadata(photo).caption == "fallback felirat"
        assert not list(tmp_path.glob("*.jpgtmp"))  # temp kitakarítva

    def test_no_temp_leftovers(self, tmp_path):
        photo = make_jpeg(tmp_path / "a.jpg")
        write_iptc_caption(photo, "felirat")
        leftovers = [p for p in tmp_path.iterdir() if p.suffix == ".tmp"]
        assert leftovers == []
