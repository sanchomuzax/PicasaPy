"""#567 — `autobacklight` és a kisbetűs `focalpixelate` a natív regiszter
fényében.

Két korábbi feltételezést pontosít a Picasa effekt-regisztrációs táblájának
visszafejtése:

- az `autobacklight` NEM adaptív képelemzés, hanem FIX 25%-os derítőfény (a
  render callback ugyanazt a magot hívja, mint a `backlight`/`fill`, fix
  0,25 argumentummal);
- a kisbetűs `focalpixelate` HALOTT konfigurációs maradvány — nincs hozzá se
  render-callback, se névregisztráció —, és NEM azonos az élő
  `PicnikFocalPixelate` Glimmer-effekttel.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters, serialize_filters
from picasapy.render.chain import (
    DEAD_LEGACY_OPS,
    KNOWN_UNRENDERED_OPS,
    apply_filters,
)
from picasapy.render.tone import apply_fill


@pytest.fixture
def sample() -> np.ndarray:
    rng = np.random.default_rng(29)
    return rng.integers(10, 245, size=(48, 64, 3), dtype=np.uint8)


class TestAutobacklight:
    def test_renders_and_is_no_longer_skipped(self, sample):
        report = apply_filters(sample, parse_filters("autobacklight=1;"))
        assert report.skipped == ()
        assert "autobacklight" not in KNOWN_UNRENDERED_OPS
        assert not np.array_equal(report.image, sample)

    def test_output_equals_a_fixed_25_percent_fill(self, sample):
        report = apply_filters(sample, parse_filters("autobacklight=1;"))
        np.testing.assert_array_equal(report.image, apply_fill(sample, 0.25))

    def test_no_image_analysis_happens(self, sample):
        """Nincs hisztogram- vagy fényesség-vizsgálat: két, egymástól
        gyökeresen eltérő eloszlású képen UGYANAZ a fix 25%-os görbe fut —
        az eredmény mindkettőn pontosan a `fill(0,25)` kimenete."""
        dark = np.full_like(sample, 20)
        bright = np.full_like(sample, 235)
        for image in (dark, bright):
            report = apply_filters(image, parse_filters("autobacklight=1;"))
            np.testing.assert_array_equal(report.image, apply_fill(image, 0.25))

    def test_parameters_are_ignored(self, sample):
        """Nincs szabad paramétere — egy odaírt érték sem változtat rajta
        (és nem is dob kivételt)."""
        plain = apply_filters(sample, parse_filters("autobacklight=1;")).image
        with_param = apply_filters(
            sample, parse_filters("autobacklight=1,0.900000;")
        ).image
        np.testing.assert_array_equal(plain, with_param)


class TestDeadLegacyFocalPixelate:
    def test_is_registered_as_dead_legacy(self):
        assert "focalpixelate" in DEAD_LEGACY_OPS

    def test_render_report_says_it_is_legacy(self, sample):
        report = apply_filters(sample, parse_filters("focalpixelate=1;"))
        assert np.array_equal(report.image, sample)
        assert report.skipped == ("focalpixelate",)
        assert len(report.legacy_warnings) == 1
        assert "legacy" in report.legacy_warnings[0].casefold()

    def test_not_confused_with_the_live_picnik_effect(self, sample):
        """A két név KÜLÖN kulcs: a kisbetűs halott bejegyzés jelzést kap, az
        élő `PicnikFocalPixelate` viszont nem — az a saját (#570-ben
        pontosítandó) útján megy."""
        live = apply_filters(
            sample, parse_filters("PicnikFocalPixelate=1,50.000000;")
        )
        assert live.legacy_warnings == ()
        assert "picnikfocalpixelate" not in DEAD_LEGACY_OPS

    def test_a_regular_unrendered_name_gets_no_legacy_warning(self, sample):
        """A „még nincs modellünk" és a „halott bejegyzés" két külön ok — a
        `skipped` mindkettőt tartalmazza, a `legacy_warnings` csak az
        utóbbit."""
        report = apply_filters(sample, parse_filters("rainbow=1;"))
        assert report.skipped == ("rainbow",)
        assert report.legacy_warnings == ()


class TestRoundTrip:
    @pytest.mark.parametrize("key", ["autobacklight", "focalpixelate"])
    def test_both_names_survive_the_ini_round_trip(self, key):
        value = f"{key}=1,0.500000;"
        assert serialize_filters(parse_filters(value)) == value
