"""Exportálás mappába (issue #16): forgatás beleégetése + átméretezés OpenCV-vel."""

import os

import cv2
import numpy as np
import piexif
import pytest
from PIL.IptcImagePlugin import getiptcinfo
from PIL import Image

from picasapy.export import (
    ExportItem,
    ExportSettings,
    export_photos,
    resolve_export_quality,
)
from support.jpeg_factory import make_jpeg


def _make_half_and_half(path, width=40, height=20):
    """Bal fele fehér, jobb fele fekete — a forgásirány pixelszintű próbájához.

    A `cv2.imwrite` Windowson ékezetes útvonalon némán elhasal (#65), ezért
    — mint az export modul dekódolása — bájt-alapon írunk (`imencode` +
    `ndarray.tofile`), hogy az ékezetes fájlnevek is működjenek."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, : width // 2] = 255
    ok, encoded = cv2.imencode(path.suffix, image)
    assert ok
    encoded.tofile(str(path))
    return path


def _read_image(path):
    """Bájt-alapú visszaolvasás: a `cv2.imread` Windowson ékezetes útvonalon
    (pl. `forgó.jpg`) némán None-t ad (#65), ezért `fromfile` + `imdecode`."""
    payload = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(payload, cv2.IMREAD_COLOR)


class TestBasicExport:
    def test_exports_jpeg_with_same_stem(self, tmp_path):
        source = make_jpeg(tmp_path / "nyaralás.jpg")
        target_dir = tmp_path / "out"
        report = export_photos([ExportItem(source)], target_dir)
        assert [p.name for p in report.exported] == ["nyaralás.jpg"]
        assert (target_dir / "nyaralás.jpg").exists()
        assert report.failed == ()

    def test_non_jpeg_source_is_reencoded_as_jpeg(self, tmp_path):
        source = _make_half_and_half(tmp_path / "kép.png")
        report = export_photos([ExportItem(source)], tmp_path / "out")
        assert [p.suffix for p in report.exported] == [".jpg"]

    def test_name_collision_gets_numbered_suffix(self, tmp_path):
        (tmp_path / "a").mkdir()
        (tmp_path / "b").mkdir()
        first = make_jpeg(tmp_path / "a" / "kép.jpg")
        second = make_jpeg(tmp_path / "b" / "kép.jpg")
        target_dir = tmp_path / "out"
        report = export_photos([ExportItem(first), ExportItem(second)], target_dir)
        assert [p.name for p in report.exported] == ["kép.jpg", "kép-1.jpg"]

    def test_export_order_follows_input_order(self, tmp_path):
        sources = [make_jpeg(tmp_path / f"{i}.jpg") for i in (3, 1, 2)]
        report = export_photos([ExportItem(s) for s in sources], tmp_path / "out")
        assert [p.stem for p in report.exported] == ["3", "1", "2"]


class TestResize:
    def test_longest_side_is_capped(self, tmp_path):
        source = _make_half_and_half(tmp_path / "nagy.png", width=40, height=20)
        report = export_photos(
            [ExportItem(source)], tmp_path / "out", ExportSettings(max_dimension=10)
        )
        exported = _read_image(report.exported[0])
        assert exported.shape[:2] == (5, 10)  # (magasság, szélesség)

    def test_no_upscale_beyond_original(self, tmp_path):
        source = _make_half_and_half(tmp_path / "kicsi.png", width=40, height=20)
        report = export_photos(
            [ExportItem(source)], tmp_path / "out", ExportSettings(max_dimension=1000)
        )
        exported = _read_image(report.exported[0])
        assert exported.shape[:2] == (20, 40)


class TestRotation:
    def test_one_step_rotates_90_clockwise(self, tmp_path):
        # A Picasa/Qt konvenció: 1 lépés = 90° órairányban → a bal (fehér)
        # szél felülre kerül.
        source = _make_half_and_half(tmp_path / "forgó.png", width=40, height=20)
        report = export_photos(
            [ExportItem(source, rotate_steps=1)], tmp_path / "out"
        )
        exported = _read_image(report.exported[0])
        assert exported.shape[:2] == (40, 20)  # oldalak felcserélve
        assert exported[:10].mean() > 200  # felső negyed: fehér
        assert exported[-10:].mean() < 50  # alsó negyed: fekete

    def test_two_steps_rotate_180(self, tmp_path):
        source = _make_half_and_half(tmp_path / "forgó.png", width=40, height=20)
        report = export_photos(
            [ExportItem(source, rotate_steps=2)], tmp_path / "out"
        )
        exported = _read_image(report.exported[0])
        assert exported.shape[:2] == (20, 40)
        assert exported[:, :20].mean() < 50  # bal fél: fekete lett
        assert exported[:, 20:].mean() > 200

    def test_steps_wrap_modulo_four(self, tmp_path):
        source = _make_half_and_half(tmp_path / "forgó.png")
        report = export_photos(
            [ExportItem(source, rotate_steps=4)], tmp_path / "out"
        )
        exported = _read_image(report.exported[0])
        assert exported.shape[:2] == (20, 40)
        assert exported[:, :20].mean() > 200  # változatlan


class TestFallbacksAndErrors:
    def test_video_is_copied_verbatim(self, tmp_path):
        payload = "nem igazi mp4, de bitre pontosan másolandó".encode("utf-8")
        source = tmp_path / "videó.mp4"
        source.write_bytes(payload)
        report = export_photos([ExportItem(source)], tmp_path / "out")
        assert [p.name for p in report.exported] == ["videó.mp4"]
        assert report.exported[0].read_bytes() == payload

    def test_missing_source_goes_to_failed(self, tmp_path):
        report = export_photos(
            [ExportItem(tmp_path / "nincs.jpg")], tmp_path / "out"
        )
        assert report.exported == ()
        assert [p.name for p in report.failed] == ["nincs.jpg"]

    def test_undecodable_image_goes_to_failed(self, tmp_path):
        source = tmp_path / "rossz.jpg"
        source.write_bytes(b"ez nem JPEG")
        report = export_photos([ExportItem(source)], tmp_path / "out")
        assert [p.name for p in report.failed] == ["rossz.jpg"]

    def test_failure_does_not_stop_batch(self, tmp_path):
        bad = tmp_path / "rossz.jpg"
        bad.write_bytes(b"x")
        good = make_jpeg(tmp_path / "jó.jpg")
        report = export_photos(
            [ExportItem(bad), ExportItem(good)], tmp_path / "out"
        )
        assert [p.name for p in report.exported] == ["jó.jpg"]
        assert [p.name for p in report.failed] == ["rossz.jpg"]


class TestNoopCopy:
    """#136: ha nincs se forgatás, se átméretezés, se filters-lánc, bájthű
    másolás történik — nincs felesleges generációs veszteség."""

    def test_jpeg_bytes_are_identical_when_nothing_to_burn_in(self, tmp_path):
        source = make_jpeg(tmp_path / "kép.jpg", caption="felirat")
        original = source.read_bytes()
        report = export_photos([ExportItem(source)], tmp_path / "out")
        assert report.exported[0].read_bytes() == original

    def test_mtime_is_preserved(self, tmp_path):
        source = make_jpeg(tmp_path / "kép.jpg")
        past = 1_600_000_000
        os.utime(source, (past, past))
        report = export_photos([ExportItem(source)], tmp_path / "out")
        assert report.exported[0].stat().st_mtime == pytest.approx(past)

    def test_rotation_disables_noop_copy(self, tmp_path):
        source = _make_half_and_half(tmp_path / "forgó.jpg")
        original = source.read_bytes()
        report = export_photos(
            [ExportItem(source, rotate_steps=1)], tmp_path / "out"
        )
        assert report.exported[0].read_bytes() != original

    def test_resize_setting_disables_noop_copy(self, tmp_path):
        source = _make_half_and_half(tmp_path / "kép.jpg", width=400, height=200)
        original = source.read_bytes()
        report = export_photos(
            [ExportItem(source)], tmp_path / "out", ExportSettings(max_dimension=10)
        )
        assert report.exported[0].read_bytes() != original

    def test_filters_disable_noop_copy(self, tmp_path):
        source = _make_half_and_half(tmp_path / "kép.jpg")
        original = source.read_bytes()
        report = export_photos(
            [ExportItem(source, filters="bw=1;")], tmp_path / "out"
        )
        assert report.exported[0].read_bytes() != original


class TestVideoExport:
    def test_video_mtime_is_preserved(self, tmp_path):
        source = tmp_path / "videó.mp4"
        source.write_bytes(b"nem igazi mp4")
        past = 1_600_000_000
        os.utime(source, (past, past))
        report = export_photos([ExportItem(source)], tmp_path / "out")
        assert report.exported[0].stat().st_mtime == pytest.approx(past)


class TestMetadataTransfer:
    """#136: az EXIF/IPTC a Picasa exportjához hasonlóan átkerül az
    újrakódolt (forgatott/átméretezett/szerkesztett) célfájlba is."""

    def test_exif_datetime_survives_reencode(self, tmp_path):
        source = make_jpeg(
            tmp_path / "kép.jpg", datetime_0th="2020:05:17 12:00:00"
        )
        report = export_photos(
            [ExportItem(source, rotate_steps=1)], tmp_path / "out"
        )
        exif = piexif.load(str(report.exported[0]))
        assert exif["0th"][piexif.ImageIFD.DateTime] == b"2020:05:17 12:00:00"

    def test_iptc_caption_and_keywords_survive_reencode(self, tmp_path):
        source = make_jpeg(
            tmp_path / "kép.jpg",
            caption="Nyaralás",
            keywords=("tenger", "nyár"),
        )
        report = export_photos(
            [ExportItem(source, rotate_steps=2)], tmp_path / "out"
        )
        with Image.open(report.exported[0]) as image:
            iptc = getiptcinfo(image) or {}
        assert iptc.get((2, 120)) == "Nyaralás".encode("utf-8")
        keywords = iptc.get((2, 25))
        keywords = keywords if isinstance(keywords, list) else [keywords]
        assert {k.decode("utf-8") for k in keywords} == {"tenger", "nyár"}

    def test_resize_also_transfers_metadata(self, tmp_path):
        source = make_jpeg(
            tmp_path / "kép.jpg", size=(400, 200), caption="Cím"
        )
        report = export_photos(
            [ExportItem(source)], tmp_path / "out", ExportSettings(max_dimension=10)
        )
        with Image.open(report.exported[0]) as image:
            iptc = getiptcinfo(image) or {}
        assert iptc.get((2, 120)) == "Cím".encode("utf-8")


class TestFiltersChain:
    """#136: a `filters=` lánc beleég a célfájlba a meglévő render-lánccal."""

    def test_bw_filter_is_burned_in(self, tmp_path):
        source = _make_half_and_half(tmp_path / "kép.jpg", width=40, height=20)
        report = export_photos(
            [ExportItem(source, filters="bw=1;")], tmp_path / "out"
        )
        exported = _read_image(report.exported[0])
        # bw után minden csatorna azonos (szürkeárnyalat), a fehér/fekete
        # kontraszt megmarad, de a csatornák közti eltérés eltűnik.
        diff = exported.max(axis=2).astype(int) - exported.min(axis=2).astype(int)
        assert diff.max() <= 2  # JPEG-kvantálási tolerancia

    def test_unknown_filter_falls_back_to_unfiltered_export(self, tmp_path):
        # #73-elv: idegen/hibás lánc-bejegyzés nem buktathatja meg az exportot.
        source = _make_half_and_half(tmp_path / "kép.jpg")
        report = export_photos(
            [ExportItem(source, filters="ismeretlen_szuro=1;")], tmp_path / "out"
        )
        assert report.failed == ()
        assert report.exported != ()


class TestNoSilentDeath:
    """#136: az export_photos sosem hal el némán — kivételnél is strukturált
    hibaeredményt ad vissza."""

    def test_target_dir_creation_failure_is_reported_not_raised(self, tmp_path):
        # A célmappa helyén egy sima FÁJL áll — a mkdir(parents=True) itt
        # OSError-t dob, amit korábban semmi nem fogott el.
        blocked = tmp_path / "cél"
        blocked.write_text("nem könyvtár")
        source = make_jpeg(tmp_path / "kép.jpg")
        report = export_photos([ExportItem(source)], blocked)
        assert report.exported == ()
        assert [p.name for p in report.failed] == ["kép.jpg"]


class TestSettingsValidation:
    @pytest.mark.parametrize("quality", [0, 101, -5])
    def test_invalid_quality_raises(self, quality):
        with pytest.raises(ValueError):
            ExportSettings(jpeg_quality=quality)

    @pytest.mark.parametrize("dimension", [0, -1])
    def test_invalid_max_dimension_raises(self, dimension):
        with pytest.raises(ValueError):
            ExportSettings(max_dimension=dimension)

    def test_quality_is_respected(self, tmp_path):
        source = _make_half_and_half(tmp_path / "kép.png", width=400, height=200)
        low = export_photos(
            [ExportItem(source)], tmp_path / "low", ExportSettings(jpeg_quality=10)
        )
        high = export_photos(
            [ExportItem(source)], tmp_path / "high", ExportSettings(jpeg_quality=95)
        )
        assert low.exported[0].stat().st_size < high.exported[0].stat().st_size


class TestAddNumbers:
    """#369 (export.fen paritás): „Add numbers to file names to preserve
    order" — a fájlnevek elé 3 jegyű sorszám kerül, bemeneti sorrendben."""

    def test_numbers_are_prefixed_in_input_order(self, tmp_path):
        sources = [make_jpeg(tmp_path / name) for name in ("c.jpg", "a.jpg", "b.jpg")]
        report = export_photos(
            [ExportItem(s) for s in sources],
            tmp_path / "out",
            ExportSettings(add_numbers=True),
        )
        assert [p.name for p in report.exported] == [
            "001-c.jpg", "002-a.jpg", "003-b.jpg",
        ]

    def test_disabled_by_default_keeps_original_names(self, tmp_path):
        source = make_jpeg(tmp_path / "kép.jpg")
        report = export_photos([ExportItem(source)], tmp_path / "out")
        assert [p.name for p in report.exported] == ["kép.jpg"]

    def test_numbering_still_deduplicates_collisions(self, tmp_path):
        (tmp_path / "a").mkdir()
        (tmp_path / "b").mkdir()
        first = make_jpeg(tmp_path / "a" / "kép.jpg")
        second = make_jpeg(tmp_path / "b" / "kép.jpg")
        report = export_photos(
            [ExportItem(first), ExportItem(second)],
            tmp_path / "out",
            ExportSettings(add_numbers=True),
        )
        assert [p.name for p in report.exported] == ["001-kép.jpg", "002-kép.jpg"]

    def test_width_grows_for_large_batches(self, tmp_path):
        # 1000+ elemnél a 3-jegyű séma nem lenne elég — a szélesség a teljes
        # kötegméretből számolt, hogy sorrend szerint rendezve maradjon.
        sources = [make_jpeg(tmp_path / f"{i}.jpg") for i in range(1000)]
        report = export_photos(
            [ExportItem(s) for s in sources],
            tmp_path / "out",
            ExportSettings(add_numbers=True),
        )
        assert report.exported[0].name == "0001-0.jpg"
        assert report.exported[999].name == "1000-999.jpg"


class TestWatermark:
    """#369 (export.fen paritás): vízjel-szöveg a jobb alsó sarokban, fehér,
    félig átlátszó — a Picasa mintáját közelítve."""

    def test_watermark_brightens_bottom_right_corner(self, tmp_path):
        # Sötét (fekete) forráskép — a fehér, félig átlátszó szöveg a jobb
        # alsó sarokban észrevehetően felfényesíti azt a régiót.
        image = np.zeros((200, 300, 3), dtype=np.uint8)
        source = tmp_path / "sötét.png"
        ok, encoded = cv2.imencode(".png", image)
        assert ok
        encoded.tofile(str(source))
        report = export_photos(
            [ExportItem(source)],
            tmp_path / "out",
            ExportSettings(watermark_text="PicasaPy"),
        )
        exported = _read_image(report.exported[0])
        corner = exported[-40:, -100:]
        assert corner.mean() > 5  # a szöveg felfényesíti a sarkot
        # a bal felső sarok érintetlen marad (fekete)
        assert exported[:40, :100].mean() < 2

    def test_no_watermark_by_default_leaves_image_untouched(self, tmp_path):
        source = _make_half_and_half(tmp_path / "kép.png")
        report = export_photos([ExportItem(source)], tmp_path / "out")
        exported = _read_image(report.exported[0])
        assert exported[:, 20:].mean() < 5  # jobb fél változatlanul fekete

    def test_watermark_disables_noop_copy(self, tmp_path):
        source = make_jpeg(tmp_path / "kép.jpg")
        original = source.read_bytes()
        report = export_photos(
            [ExportItem(source)],
            tmp_path / "out",
            ExportSettings(watermark_text="PicasaPy"),
        )
        assert report.exported[0].read_bytes() != original


class TestQualityPresets:
    """#369 / #1139 (export.fen paritás): a minőség-lenyíló preset→JPEG-
    minőség leképezése (`resolve_export_quality`). A három fix fokozat
    értéke a #1139 óta a binárisból ismert (ugrótábla `0x00739ef4`), nem
    közelítés; csak az „Automatikus" maradt közelítés."""

    def test_normal_maximum_minimum_map_to_documented_values(self):
        assert resolve_export_quality("normal", 50) == 85
        assert resolve_export_quality("maximum", 50) == 100
        # #1139: az eredetiben 65 (`0x41`, `0x00739ca8`) — nálunk 70 volt.
        assert resolve_export_quality("minimum", 50) == 65

    def test_minimum_matches_the_binary_jump_table(self):
        """#1139 őre: a „Minimális" fokozat pontosan 65, csúszkától
        függetlenül — a `0x00739ef4` ugrótábla `0x00739ca8` ága."""
        assert resolve_export_quality("minimum", 0) == 65
        assert resolve_export_quality("MINIMUM", 100) == 65

    def test_automatic_maps_to_high_approximation(self):
        assert resolve_export_quality("automatic", 50) == 92

    def test_custom_uses_the_given_value(self):
        assert resolve_export_quality("custom", 42) == 42

    def test_custom_out_of_range_raises(self):
        with pytest.raises(ValueError):
            resolve_export_quality("custom", 0)
        with pytest.raises(ValueError):
            resolve_export_quality("custom", 101)

    def test_unknown_preset_falls_back_to_automatic(self):
        assert resolve_export_quality("???", 50) == 92
