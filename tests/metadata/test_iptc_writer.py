"""IPTC-felirat írása JPEG-be — bájt-megőrző szegmens-műtét.

Picasa-viselkedés (spec, írási szabály #3): JPEG-nél a caption az IPTC-be
kerül, nem a .picasa.ini-be. Minden más bájt (képadat, EXIF, egyéb IPTC
mezők) érintetlen marad.
"""

import os
import stat

import pytest

from picasapy.metadata import (
    read_file_metadata,
    write_iptc_caption,
    write_iptc_keywords,
)

from support.jpeg_factory import make_jpeg

_PHOTOSHOP = b"Photoshop 3.0\x00"
# Egy APP13 payload max 65533 bájt, elejét a Photoshop-azonosító foglalja.
_MAX_SEGMENT_BODY = 65535 - 2 - len(_PHOTOSHOP)


def _dataset(record: int, tag: int, value: bytes) -> bytes:
    return b"\x1c" + bytes((record, tag)) + len(value).to_bytes(2, "big") + value


def _extended_dataset(record: int, tag: int, value: bytes) -> bytes:
    # Kiterjesztett hossz: a 2 bájtos hosszmező felső bitje 1, alsó 15
    # bitje a következő (itt 4 bájtos) valódi hosszmező mérete.
    return (
        b"\x1c"
        + bytes((record, tag))
        + (0x8000 | 4).to_bytes(2, "big")
        + len(value).to_bytes(4, "big")
        + value
    )


def _resource(resource_id: int, data: bytes) -> bytes:
    block = b"8BIM" + resource_id.to_bytes(2, "big") + b"\x00\x00"
    block += len(data).to_bytes(4, "big") + data
    if len(data) % 2:
        block += b"\x00"
    return block


def _photoshop_app13(body: bytes) -> bytes:
    """APP13 szegmens(ek) — 64 KB felett az írókkal azonos darabolással."""
    segments = b""
    for offset in range(0, len(body), _MAX_SEGMENT_BODY):
        payload = _PHOTOSHOP + body[offset : offset + _MAX_SEGMENT_BODY]
        segments += b"\xff\xed" + (len(payload) + 2).to_bytes(2, "big") + payload
    return segments


def _insert_after_soi(path, segment_bytes: bytes) -> None:
    raw = path.read_bytes()
    path.write_bytes(raw[:2] + segment_bytes + raw[2:])


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

        import picasapy.ioutil as ioutil_module

        photo = make_jpeg(tmp_path / "a.jpg")
        original_replace = os_module.replace
        calls = {"n": 0}

        def flaky_replace(src, dst):
            calls["n"] += 1
            if calls["n"] < 3:
                raise PermissionError(13, "Access is denied")
            return original_replace(src, dst)

        monkeypatch.setattr(ioutil_module.os, "replace", flaky_replace)
        assert write_iptc_caption(photo, "zárolt közben")
        assert read_file_metadata(photo).caption == "zárolt közben"

    def test_replace_falls_back_to_direct_write(self, tmp_path, monkeypatch):
        # Ha a zár nem enged fel, nem-atomikus közvetlen írás (a képfájlnál
        # ez elfogadható fallback; az ini-nél nem — ott nincs ilyen).
        import picasapy.ioutil as ioutil_module
        import picasapy.metadata.iptc_writer as writer_module

        photo = make_jpeg(tmp_path / "a.jpg")

        def always_denied(src, dst):
            raise PermissionError(13, "Access is denied")

        monkeypatch.setattr(ioutil_module.os, "replace", always_denied)
        monkeypatch.setattr(writer_module, "_RETRY_DELAY", 0.001)
        assert write_iptc_caption(photo, "fallback felirat")
        assert read_file_metadata(photo).caption == "fallback felirat"
        assert not list(tmp_path.glob("*.jpgtmp"))  # temp kitakarítva

    def test_no_temp_leftovers(self, tmp_path):
        photo = make_jpeg(tmp_path / "a.jpg")
        write_iptc_caption(photo, "felirat")
        leftovers = [p for p in tmp_path.iterdir() if p.suffix == ".tmp"]
        assert leftovers == []


class TestWriteKeywords:
    """IPTC Keywords (2:25) írása — a #12-es Címkék-panel írási útja."""

    def test_keywords_written_and_readable(self, tmp_path):
        photo = make_jpeg(tmp_path / "a.jpg")
        assert write_iptc_keywords(photo, ("balaton", "nyár"))
        assert read_file_metadata(photo).keywords == ("balaton", "nyár")

    def test_unicode_keywords(self, tmp_path):
        photo = make_jpeg(tmp_path / "a.jpg")
        write_iptc_keywords(photo, ("őszi túra", "árvíztűrő"))
        assert read_file_metadata(photo).keywords == ("őszi túra", "árvíztűrő")

    def test_overwrite_replaces_old_keywords(self, tmp_path):
        photo = make_jpeg(tmp_path / "a.jpg", keywords=("régi", "másik"))
        write_iptc_keywords(photo, ("új",))
        assert read_file_metadata(photo).keywords == ("új",)

    def test_keywords_keep_caption(self, tmp_path):
        photo = make_jpeg(
            tmp_path / "a.jpg", caption="felirat", keywords=("régi",)
        )
        write_iptc_keywords(photo, ("balaton", "nyár"))
        meta = read_file_metadata(photo)
        assert meta.caption == "felirat"
        assert meta.keywords == ("balaton", "nyár")

    def test_caption_write_keeps_new_keywords(self, tmp_path):
        # a két író nem ronthatja el egymás mezőit (oda-vissza)
        photo = make_jpeg(tmp_path / "a.jpg")
        write_iptc_keywords(photo, ("címke",))
        write_iptc_caption(photo, "felirat")
        meta = read_file_metadata(photo)
        assert meta.caption == "felirat"
        assert meta.keywords == ("címke",)

    def test_empty_keywords_removes_datasets(self, tmp_path):
        photo = make_jpeg(tmp_path / "a.jpg", keywords=("törlendő",))
        write_iptc_keywords(photo, ())
        assert read_file_metadata(photo).keywords == ()

    def test_roundtrip_restores_original_bytes(self, tmp_path):
        # címkék rá, címkék le → bitre azonos fájl (nem volt IPTC előtte)
        photo = make_jpeg(tmp_path / "a.jpg")
        original = photo.read_bytes()
        write_iptc_keywords(photo, ("ideiglenes",))
        write_iptc_keywords(photo, ())
        assert photo.read_bytes() == original

    def test_other_segments_byte_identical(self, tmp_path):
        photo = make_jpeg(
            tmp_path / "a.jpg", taken_at="2025:05:01 07:23:10", orientation=6
        )
        before = _segments(photo)
        write_iptc_keywords(photo, ("címke",))
        assert _segments(photo) == before
        meta = read_file_metadata(photo)
        assert meta.taken_at == "2025-05-01T07:23:10"
        assert meta.orientation == 6

    def test_non_jpeg_rejected(self, tmp_path):
        from PIL import Image

        png = tmp_path / "kep.png"
        Image.new("RGB", (8, 6), "blue").save(png, "PNG")
        assert write_iptc_keywords(png, ("x",)) is False

    def test_corrupt_file_rejected(self, tmp_path):
        bad = tmp_path / "rossz.jpg"
        bad.write_bytes(b"nem jpeg")
        assert write_iptc_keywords(bad, ("x",)) is False

    def test_long_keyword_truncated_on_utf8_boundary(self, tmp_path):
        # az IPTC 2:25 mező 64 bájtos; a vágás nem törhet szét UTF-8
        # karaktert (a visszaolvasás érvényes szöveget kapjon)
        photo = make_jpeg(tmp_path / "a.jpg")
        long_keyword = "ő" * 40  # 80 bájt UTF-8-ban
        write_iptc_keywords(photo, (long_keyword,))
        (read_back,) = read_file_metadata(photo).keywords
        assert read_back == "ő" * 32  # 64 bájt = 32 kétbájtos karakter
        assert long_keyword.startswith(read_back)


class TestDurabilityAndPermissions:
    """#129: fsync a csere előtt + a fotó jogainak megőrzése (NAS)."""

    def test_fsync_before_replace(self, tmp_path, monkeypatch):
        # Crash közben sem maradhat csonka az eredeti fotó: a temp fájl
        # tartalma fsync-kel lemezen van, MIELŐTT a rename a helyére teszi.
        import picasapy.ioutil as ioutil_module

        photo = make_jpeg(tmp_path / "a.jpg")
        events = []
        original_fsync, original_replace = os.fsync, os.replace

        def spy_fsync(fd):
            events.append("fsync")
            return original_fsync(fd)

        def spy_replace(src, dst):
            events.append("replace")
            return original_replace(src, dst)

        monkeypatch.setattr(ioutil_module.os, "fsync", spy_fsync)
        monkeypatch.setattr(ioutil_module.os, "replace", spy_replace)
        assert write_iptc_caption(photo, "tartós felirat")
        assert "fsync" in events
        assert events.index("fsync") < events.index("replace")

    @pytest.mark.skipif(
        os.name != "posix",
        reason="Windowson a chmod csak a read-only bitet kezeli",
    )
    def test_file_mode_preserved(self, tmp_path):
        # NAS-on más kliens (az eredeti Picasa is) olvassa a fotót: az írás
        # nem szűkítheti a jogokat a mkstemp-féle 0600-ra.
        photo = make_jpeg(tmp_path / "a.jpg")
        photo.chmod(0o664)
        write_iptc_caption(photo, "jogok maradnak")
        assert stat.S_IMODE(photo.stat().st_mode) == 0o664
        write_iptc_keywords(photo, ("balaton",))
        assert stat.S_IMODE(photo.stat().st_mode) == 0o664


class TestRoundTripPreservation:
    """#129: amit nem értünk, változatlanul visszaírjuk (round-trip elv)."""

    def test_datasets_after_extended_length_survive(self, tmp_path):
        # A kiterjesztett hosszú (>32767 bájt) mező UTÁN álló mezők nem
        # veszhetnek el az újraépítésnél.
        photo = make_jpeg(tmp_path / "a.jpg")
        extended = _extended_dataset(2, 202, b"\xab" * 40000)
        headline = _dataset(2, 105, "fontos cím".encode("utf-8"))
        iptc = _dataset(1, 90, b"\x1b%G") + extended + headline
        _insert_after_soi(photo, _photoshop_app13(_resource(0x0404, iptc)))

        write_iptc_caption(photo, "új felirat")
        raw = photo.read_bytes()
        assert extended in raw  # a kiterjesztett mező bitre pontosan megvan
        assert headline in raw  # az utána álló mező sem veszett el
        # A Pillow olvasója egy patológiás (kiterjesztett hosszú) mezőt
        # tartalmazó rekordot nem tud parseolni (SyntaxError → üres olvasás);
        # ezt a round-trip elv megőrzése kikényszeríti. A garancia itt a helyes
        # ÍRÁS: a felirat szabványos adatmezőként bekerül. A tiszta esetek
        # visszaolvasását a többi teszt fedi.
        assert _dataset(2, 120, "új felirat".encode("utf-8")) in raw

    def test_extended_length_roundtrip_bit_exact(self, tmp_path):
        # felirat rá, felirat le → bitre azonos fájl, kiterjesztett hosszú
        # és ismeretlen mezőkkel a rekordban.
        photo = make_jpeg(tmp_path / "a.jpg")
        iptc = (
            _dataset(1, 90, b"\x1b%G")
            + _extended_dataset(2, 202, b"\xcd" * 40000)
            + _dataset(2, 105, b"headline")
        )
        _insert_after_soi(photo, _photoshop_app13(_resource(0x0404, iptc)))
        original = photo.read_bytes()

        write_iptc_caption(photo, "ideiglenes")
        write_iptc_caption(photo, "")
        assert photo.read_bytes() == original

    def test_unparseable_dataset_tail_preserved(self, tmp_path):
        # Nem 0x1C-vel kezdődő (nem érthető) maradék a rekord végén:
        # nyersen, változatlanul íródik vissza.
        photo = make_jpeg(tmp_path / "a.jpg")
        tail = b"\xde\xad\xbe\xef ismeretlen maradek"
        iptc = _dataset(1, 90, b"\x1b%G") + _dataset(2, 105, b"headline") + tail
        _insert_after_soi(photo, _photoshop_app13(_resource(0x0404, iptc)))

        write_iptc_caption(photo, "felirat")
        assert tail in photo.read_bytes()
        # Értelmezhetetlen (nem 0x1C-vel kezdődő) dataset-farokkal a Pillow a
        # rekordot nem parseolja; a megőrzött nyers maradék ezt kikényszeríti.
        # A garancia a helyes írás: a felirat adatmezője bekerül a fájlba.
        assert _dataset(2, 120, "felirat".encode("utf-8")) in photo.read_bytes()

    def test_caption_in_second_app13_segment_replaced(self, tmp_path):
        # Több Photoshop-APP13 szegmens: a másodikban ülő IPTC-t is le kell
        # cserélni (nem maradhat duplán a régi felirat).
        photo = make_jpeg(tmp_path / "a.jpg")
        other_resource = _resource(0x03EB, b"egyeb eroforras adat")
        old_caption = _dataset(2, 120, b"regi felirat")
        first = _photoshop_app13(other_resource)
        second = _photoshop_app13(_resource(0x0404, old_caption))
        _insert_after_soi(photo, first + second)

        write_iptc_caption(photo, "új felirat")
        raw = photo.read_bytes()
        assert read_file_metadata(photo).caption == "új felirat"
        assert b"regi felirat" not in raw  # nincs ott maradt duplikátum
        assert other_resource in raw  # a másik szegmens erőforrása megvan

    def test_oversized_resources_split_and_roundtrip_bit_exact(self, tmp_path):
        # 64 KB-nál nagyobb erőforrás-blokk: az eredeti két APP13 szegmensre
        # oszlik (az erőforrás szegmenshatáron át folytatódik). Írásnál a
        # tartalom összefűzve épül újra és ismét darabolódik; fel-le után a
        # fájl bitre azonos.
        photo = make_jpeg(tmp_path / "a.jpg")
        big_resource = _resource(0x0FA0, b"\x5a" * 70000)
        _insert_after_soi(photo, _photoshop_app13(big_resource))
        original = photo.read_bytes()
        assert original.count(b"\xff\xed") >= 2  # tényleg több szegmens

        write_iptc_caption(photo, "ideiglenes")
        # A nagy erőforrás az IPTC-t a második APP13 szegmensbe tolja, amit a
        # Pillow már nem olvas — a garancia a helyes írás (a felirat adatmezője
        # bekerül) és a lenti bit-pontos round-trip.
        assert _dataset(2, 120, "ideiglenes".encode("utf-8")) in photo.read_bytes()
        write_iptc_caption(photo, "")
        assert photo.read_bytes() == original

    def test_non_photoshop_app13_untouched(self, tmp_path):
        # Nem-Photoshop azonosítójú APP13 (pl. Adobe CM): bájtra pontosan
        # a helyén marad.
        photo = make_jpeg(tmp_path / "a.jpg")
        payload = b"Adobe_CM\x00egyedi adat"
        foreign = b"\xff\xed" + (len(payload) + 2).to_bytes(2, "big") + payload
        _insert_after_soi(photo, foreign)

        write_iptc_caption(photo, "felirat")
        assert foreign in photo.read_bytes()
        assert read_file_metadata(photo).caption == "felirat"

    def test_unknown_resource_tail_preserved(self, tmp_path):
        # Nem 8BIM szignatúrájú (nem érthető) maradék az erőforrás-blob
        # végén: nyersen, változatlanul íródik vissza.
        photo = make_jpeg(tmp_path / "a.jpg")
        tail = b"8B64\x00\x01ismeretlen szignatura"
        _insert_after_soi(
            photo, _photoshop_app13(_resource(0x03EB, b"adat") + tail)
        )

        write_iptc_caption(photo, "felirat")
        assert tail in photo.read_bytes()
        assert read_file_metadata(photo).caption == "felirat"
