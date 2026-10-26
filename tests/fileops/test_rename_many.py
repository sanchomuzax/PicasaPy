"""rename_photos_many / preview_name: tömeges átnevezés a `rename.fen`
szerint (#366) — alapnév + opcionális dátum-/felbontás-utótag, Picasa-
mintájú sorszámozás (`név`, `név-1`, `név-2`…), ütközés-kezelés, és az
egyfájlos `rename_photo` (ini-átvitel!) újrafelhasználása fájlonként."""

import pytest
from PySide6.QtCore import QLocale

import picasapy.fileops.rename as rename_module
from picasapy.fileops.rename import (
    RenameItem,
    format_taken_at,
    preview_name,
    rename_photos_many,
)
from picasapy.ini import load_document

EN_US = QLocale("en_US")
HU_HU = QLocale("hu_HU")
DE_DE = QLocale("de_DE")


class TestFormatTakenAt:
    """#4879: a felvétel dátuma + ideje a területi beállítás szerint, a
    tiltott fájlnév-karakterek `-`-re cserélve (rename.fen)."""

    def test_en_us_matches_spec_shape(self):
        assert format_taken_at("2004-08-01T14:30:45", EN_US) == "8-1-2004 2-30-45 PM"

    def test_hu_hu(self):
        assert format_taken_at("2004-08-01T14:30:45", HU_HU) == "2004. 08. 01. 14-30-45"

    def test_de_de(self):
        assert format_taken_at("2004-08-01T14:30:45", DE_DE) == "01.08.2004 14-30-45"

    def test_date_only_when_time_missing(self):
        assert format_taken_at("2004-08-01", EN_US) == "8-1-2004"
        assert format_taken_at("2004-08-01", HU_HU) == "2004. 08. 01."

    def test_result_has_no_forbidden_characters_or_nbsp(self):
        for locale in (EN_US, HU_HU, DE_DE):
            text = format_taken_at("2004-08-01T14:30:45", locale)
            assert not set(text) & set('\\/:*?"<>|\u202f\u00a0')

    def test_arabic_locale_has_no_bidi_marks_and_ascii_digits(self):
        text = format_taken_at("2004-08-01T14:30:45", QLocale("ar_EG"))
        assert not set(text) & set("\u200e\u200f\u061c\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")
        assert "2004" in text
        assert all(not c.isdigit() or c.isascii() for c in text)

    def test_persian_locale_digits_are_ascii(self):
        text = format_taken_at("2004-08-01T14:30:45", QLocale("fa_IR"))
        assert all(not c.isdigit() or c.isascii() for c in text)
        assert "2004" in text

    def test_trailing_dot_of_date_only_is_kept(self):
        assert format_taken_at("2004-08-01", HU_HU) == "2004. 08. 01."

    def test_dot_of_am_pm_marker_is_kept(self):
        assert format_taken_at("2004-08-01T14:30:45", QLocale("en_CA")).endswith("p.m.")

    def test_seconds_separator_follows_the_minutes_separator(self):
        assert format_taken_at("2004-08-01T14:30:45", QLocale("fi_FI")) == "1.8.2004 14.30.45"

    def test_seconds_added_even_with_single_digit_minutes_pattern(self):
        assert format_taken_at("2004-08-01T14:30:45", QLocale("yo_NG")) == "1-8-2004 14-30-45"

    def test_unparsable_text_falls_back_to_first_ten_chars(self):
        assert format_taken_at("valami", EN_US) == "valami"


class TestPreviewName:
    def test_base_name_only(self):
        item = RenameItem(path=None, date="2025-05-01", width=800, height=600)
        assert (
            preview_name(
                "nyaralas", item, include_date=False, include_size=False,
                sequence=0, ext=".jpg",
            )
            == "nyaralas.jpg"
        )

    def test_with_date_suffix(self):
        item = RenameItem(path=None, date="2025-05-01T07:00:00", width=800, height=600)
        assert (
            preview_name(
                "nyaralas", item, include_date=True, include_size=False,
                sequence=0, ext=".jpg", locale=EN_US,
            )
            == "nyaralas 5-1-2025 7-00-00 AM.jpg"
        )

    def test_with_size_suffix(self):
        item = RenameItem(path=None, date=None, width=800, height=600)
        assert (
            preview_name(
                "nyaralas", item, include_date=False, include_size=True,
                sequence=0, ext=".jpg",
            )
            == "nyaralas 800x600.jpg"
        )

    def test_with_both_suffixes(self):
        item = RenameItem(path=None, date="2025-05-01", width=800, height=600)
        assert (
            preview_name(
                "nyaralas", item, include_date=True, include_size=True,
                sequence=0, ext=".jpg", locale=EN_US,
            )
            == "nyaralas 5-1-2025 800x600.jpg"
        )

    def test_missing_metadata_is_silently_skipped(self):
        # ha a kép nem ismert dátumot/felbontást, a hiányzó utótag kimarad
        # (nem "None" vagy hibás szöveg kerül a névbe)
        item = RenameItem(path=None, date=None, width=None, height=None)
        assert (
            preview_name(
                "nev", item, include_date=True, include_size=True,
                sequence=0, ext=".png",
            )
            == "nev.png"
        )

    def test_sequence_zero_has_no_suffix_further_ones_do(self):
        item = RenameItem(path=None)
        assert preview_name("nev", item, sequence=0, ext=".jpg") == "nev.jpg"
        assert preview_name("nev", item, sequence=1, ext=".jpg") == "nev-001.jpg"
        assert preview_name("nev", item, sequence=2, ext=".jpg") == "nev-002.jpg"


class TestTrailingDotOfWholeName:
    def test_no_extension_does_not_trim_the_name(self):
        item = RenameItem(path=None)
        assert preview_name("nev. ", item, sequence=0, ext="") == "nev. "

    def test_no_extension_keeps_a_trailing_dot_in_a_suffix(self):
        item = RenameItem(path=None, date="2004-08-01", width=None, height=None)
        name = preview_name(
            "nev", item, include_date=True, sequence=0, ext="", locale=HU_HU
        )
        assert name == "nev 2004. 08. 01."

    def test_with_extension_dot_is_kept(self):
        item = RenameItem(path=None, date="2004-08-01", width=None, height=None)
        name = preview_name(
            "nev", item, include_date=True, sequence=0, ext=".jpg", locale=HU_HU
        )
        assert name == "nev 2004. 08. 01..jpg"


class TestRenamePhotosMany:
    def test_renames_with_picasa_sequence_pattern(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        c = tmp_path / "c.jpg"
        for f in (a, b, c):
            f.write_bytes(b"kep")
        items = [RenameItem(path=a), RenameItem(path=b), RenameItem(path=c)]
        results = rename_photos_many(items, "nyaralas")
        assert results == [
            tmp_path / "nyaralas.jpg",
            tmp_path / "nyaralas-001.jpg",
            tmp_path / "nyaralas-002.jpg",
        ]
        for path in results:
            assert path.exists()
        assert not a.exists()
        assert not b.exists()
        assert not c.exists()

    def test_date_and_size_suffix_applied_per_file(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        a.write_bytes(b"kep")
        b.write_bytes(b"kep")
        items = [
            RenameItem(path=a, date="2025-05-01", width=800, height=600),
            RenameItem(path=b, date="2025-06-02", width=1024, height=768),
        ]
        results = rename_photos_many(
            items, "nyar", include_date=True, include_size=True, locale=EN_US,
        )
        assert results == [
            tmp_path / "nyar 5-1-2025 800x600.jpg",
            tmp_path / "nyar 6-2-2025 1024x768.jpg",
        ]

    def test_ini_sections_follow_each_renamed_file(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        a.write_bytes(b"kep")
        b.write_bytes(b"kep")
        ini = tmp_path / ".picasa.ini"
        ini.write_text(
            "[a.jpg]\nstar=yes\n[b.jpg]\ncaption=nyar\n", encoding="utf-8"
        )
        items = [RenameItem(path=a), RenameItem(path=b)]
        rename_photos_many(items, "nyaralas")
        document = load_document(ini)
        assert document.section("a.jpg") is None
        assert document.section("b.jpg") is None
        assert document.section("nyaralas.jpg").get("star") == "yes"
        assert document.section("nyaralas-001.jpg").get("caption") == "nyar"

    def test_runtime_failure_reports_partial_progress(self, tmp_path, monkeypatch):
        a, b, c = (tmp_path / f"{name}.jpg" for name in "abc")
        for photo in (a, b, c):
            photo.write_bytes(photo.stem.encode())
        originals = tmp_path / ".picasaoriginals"
        originals.mkdir()
        for photo in (a, b, c):
            (originals / photo.name).write_bytes(f"{photo.stem}-original".encode())
            (originals / f"{photo.stem}.1.jpg").write_bytes(
                f"{photo.stem}-snapshot".encode()
            )
        ini = tmp_path / ".picasa.ini"
        ini.write_text(
            "[a.jpg]\ncaption=A\n[b.jpg]\ncaption=B\n[c.jpg]\ncaption=C\n",
            encoding="utf-8",
        )

        real_rename = rename_module._rename
        calls = 0

        def fail_on_third(source, target):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise PermissionError("injected third-file failure")
            real_rename(source, target)

        monkeypatch.setattr(rename_module, "_rename", fail_on_third)
        with pytest.raises(RuntimeError) as caught:
            rename_photos_many([RenameItem(path=p) for p in (a, b, c)], "trip")

        error = caught.value
        assert type(error).__name__ == "PartialRenameError"
        assert error.completed_paths == (
            tmp_path / "trip.jpg", tmp_path / "trip-001.jpg"
        )
        assert error.renamed_paths == error.completed_paths
        assert error.failed_source == c
        assert error.failed_target == tmp_path / "trip-002.jpg"
        assert isinstance(error.cause, PermissionError)
        assert all(path.exists() for path in error.completed_paths)
        assert a.exists() is False
        assert b.exists() is False
        assert c.exists()
        assert (originals / "trip.jpg").read_bytes() == b"a-original"
        assert (originals / "trip-001.jpg").read_bytes() == b"b-original"
        assert (originals / "trip.1.jpg").read_bytes() == b"a-snapshot"
        assert (originals / "trip-001.1.jpg").read_bytes() == b"b-snapshot"
        assert (originals / "c.jpg").read_bytes() == b"c-original"
        assert (originals / "c.1.jpg").read_bytes() == b"c-snapshot"

        document = load_document(ini)
        assert document.section("trip.jpg").get("caption") == "A"
        assert document.section("trip-001.jpg").get("caption") == "B"
        assert document.section("c.jpg").get("caption") == "C"
        assert "trip.jpg" in str(error)
        assert "trip-001.jpg" in str(error)
        assert "c.jpg" in str(error)

    def test_no_op_when_new_name_equals_current_name(self, tmp_path):
        # egyetlen fájlnál, ha az utótagok nélküli alapnév megegyezik a
        # jelenlegi (kiterjesztés nélküli) névvel, nincs tényleges átnevezés
        photo = tmp_path / "nyaralas.jpg"
        photo.write_bytes(b"kep")
        results = rename_photos_many([RenameItem(path=photo)], "nyaralas")
        assert results == [photo]
        assert photo.exists()

    def test_empty_batch_returns_empty_list(self):
        assert rename_photos_many([], "nev") == []

    def test_invalid_base_name_raises(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        with pytest.raises(ValueError):
            rename_photos_many([RenameItem(path=photo)], "al/nev")

    def test_occupied_single_file_target_uses_001(self, tmp_path):
        a = tmp_path / "a.jpg"
        existing = tmp_path / "nyaralas.jpg"
        a.write_bytes(b"kep")
        existing.write_bytes(b"mar-van")
        results = rename_photos_many([RenameItem(path=a)], "nyaralas")
        assert results == [tmp_path / "nyaralas-001.jpg"]
        assert results[0].read_bytes() == b"kep"
        assert existing.read_bytes() == b"mar-van"

    def test_occupied_existing_numeric_suffix_continues(self, tmp_path):
        source = tmp_path / "source.jpg"
        occupied = tmp_path / "trip-7.jpg"
        source.write_bytes(b"kep")
        occupied.write_bytes(b"mar-van")

        result = rename_photos_many([RenameItem(path=source)], "trip-7")

        assert result == [tmp_path / "trip-008.jpg"]
        assert result[0].read_bytes() == b"kep"
        assert occupied.read_bytes() == b"mar-van"

    def test_suffix_is_padded_through_999_and_four_digits_at_1000(self, tmp_path):
        source = tmp_path / "source.jpg"
        source.write_bytes(b"kep")
        for number in range(1000):
            target_name = "trip.jpg" if number == 0 else f"trip-{number:03d}.jpg"
            (tmp_path / target_name).write_bytes(b"foglalt")

        result = rename_photos_many([RenameItem(path=source)], "trip")

        assert result == [tmp_path / "trip-1000.jpg"]
        assert result[0].read_bytes() == b"kep"

    def test_search_ends_after_the_4096th_candidate(self, tmp_path):
        source = tmp_path / "source.jpg"
        source.write_bytes(b"kep")
        for number in range(4096):
            target_name = "trip.jpg" if number == 0 else f"trip-{number:03d}.jpg"
            (tmp_path / target_name).write_bytes(b"foglalt")

        with pytest.raises(FileExistsError, match="4096") as caught:
            rename_photos_many([RenameItem(path=source)], "trip")

        assert "trip-4095.jpg" in str(caught.value)
        assert source.read_bytes() == b"kep"

    def test_extension_case_is_preserved_on_collision(self, tmp_path):
        source = tmp_path / "source.JpG"
        occupied = tmp_path / "trip.JpG"
        source.write_bytes(b"kep")
        occupied.write_bytes(b"mar-van")

        result = rename_photos_many([RenameItem(path=source)], "trip")

        assert result == [tmp_path / "trip-001.JpG"]

    def test_extensionless_collision_adds_no_dot(self, tmp_path):
        source = tmp_path / "source"
        occupied = tmp_path / "trip"
        source.write_bytes(b"kep")
        occupied.write_bytes(b"mar-van")

        result = rename_photos_many([RenameItem(path=source)], "trip")

        assert result == [tmp_path / "trip-001"]
        assert result[0].read_bytes() == b"kep"

    def test_batch_occupant_forces_suffix_then_own_name_is_noop(self, tmp_path):
        a = tmp_path / "a.jpg"
        other = tmp_path / "nyaralas.jpg"
        a.write_bytes(b"kep")
        other.write_bytes(b"mar-van")
        items = [RenameItem(path=a), RenameItem(path=other)]
        results = rename_photos_many(items, "nyaralas")
        assert results == [tmp_path / "nyaralas-001.jpg", other]
        assert results[0].read_bytes() == b"kep"
        assert other.exists()

    def test_extension_preserved_per_file(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.mov"
        a.write_bytes(b"kep")
        b.write_bytes(b"video")
        items = [RenameItem(path=a), RenameItem(path=b)]
        results = rename_photos_many(items, "nyaralas")
        assert results == [
            tmp_path / "nyaralas.jpg",
            tmp_path / "nyaralas.mov",
        ]
