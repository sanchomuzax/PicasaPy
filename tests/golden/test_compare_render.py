"""A golden-összehasonlító harness (`tools/golden/compare_render.py`) tesztjei.

A harness LOGIKÁJÁT szintetikus adatokkal teszteljük — a valódi golden-kitek
(`research/golden-kit*/`) a fejlesztői gépen élnek, a repóban nincsenek.
Alapelvek:
  - a saját render-kimenet önmagával összevetve = pixelhű;
  - mesterségesen torzított kimenet = küszöb felett (eltér);
  - kis, egyenletes eltolás = közelítés (SSIM magas, ΔE kicsi, de nem pixelhű).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render import apply_filters

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "tools" / "golden" / "compare_render.py"
)


def _load_module():
    """A tools/golden/compare_render.py betöltése fájlútvonalról (nincs a
    pythonpath-on — szándékosan eszköz, nem csomag)."""
    spec = importlib.util.spec_from_file_location("compare_render", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("compare_render", module)
    spec.loader.exec_module(module)
    return module


cr = _load_module()


def _gradient_image(width: int = 64, height: int = 48) -> np.ndarray:
    """Determinisztikus szürke átmenet RGB képként."""
    row = np.linspace(20, 235, width).astype(np.uint8)
    gray = np.tile(row, (height, 1))
    return np.stack([gray, gray, gray], axis=-1)


def _color_image(width: int = 64, height: int = 48) -> np.ndarray:
    """Determinisztikus színes tesztkép."""
    image = np.zeros((height, width, 3), np.uint8)
    image[..., 0] = np.tile(np.linspace(0, 255, width).astype(np.uint8), (height, 1))
    image[..., 1] = 128
    image[..., 2] = np.tile(
        np.linspace(255, 0, width).astype(np.uint8), (height, 1)
    )
    return image


class TestSsim:
    def test_azonos_kep_ssim_egy(self) -> None:
        image = _gradient_image()
        assert cr.ssim(image, image) == pytest.approx(1.0)

    def test_zajos_kep_ssim_kisebb(self) -> None:
        image = _gradient_image()
        rng = np.random.default_rng(42)
        noisy = np.clip(
            image.astype(np.int16) + rng.integers(-60, 60, image.shape), 0, 255
        ).astype(np.uint8)
        value = cr.ssim(image, noisy)
        assert value < 0.9

    def test_ssim_szimmetrikus(self) -> None:
        first = _gradient_image()
        second = np.clip(first.astype(np.int16) + 15, 0, 255).astype(np.uint8)
        assert cr.ssim(first, second) == pytest.approx(cr.ssim(second, first))

    def test_elter_alaku_kepek_hibat_dobnak(self) -> None:
        with pytest.raises(ValueError):
            cr.ssim(_gradient_image(64, 48), _gradient_image(32, 48))


class TestDeltaE:
    def test_azonos_kep_nulla(self) -> None:
        image = _color_image()
        assert float(cr.delta_e_cie76(image, image).max()) == pytest.approx(0.0)

    def test_fekete_vs_feher_nagy(self) -> None:
        black = np.zeros((4, 4, 3), np.uint8)
        white = np.full((4, 4, 3), 255, np.uint8)
        value = float(cr.delta_e_cie76(black, white).mean())
        assert value == pytest.approx(100.0, abs=1.0)

    def test_kis_eltolas_kis_delta_e(self) -> None:
        image = _color_image()
        shifted = np.clip(image.astype(np.int16) + 2, 0, 255).astype(np.uint8)
        assert float(cr.delta_e_cie76(image, shifted).mean()) < 3.0


class TestPixelDiffStats:
    def test_azonos_kep_nulla_diff(self) -> None:
        image = _gradient_image()
        stats = cr.pixel_diff_stats(image, image, tolerance=1)
        assert stats["max_diff"] == 0
        assert stats["mean_diff"] == pytest.approx(0.0)
        assert stats["over_tolerance_ratio"] == pytest.approx(0.0)

    def test_eltolt_kep_diff_aranya(self) -> None:
        image = _gradient_image()
        shifted = np.clip(image.astype(np.int16) + 5, 0, 255).astype(np.uint8)
        stats = cr.pixel_diff_stats(image, shifted, tolerance=1)
        assert stats["max_diff"] == 5
        assert stats["over_tolerance_ratio"] > 0.9


class TestVerdict:
    def test_pixelhu(self) -> None:
        metrics = {
            "ssim": 1.0,
            "delta_e_mean": 0.0,
            "delta_e_p99": 0.0,
            "max_diff": 1,
            "over_tolerance_ratio": 0.0,
        }
        assert cr.verdict(metrics, cr.Thresholds()) == "pixelhű"

    def test_kozelites(self) -> None:
        metrics = {
            "ssim": 0.995,
            "delta_e_mean": 1.2,
            "delta_e_p99": 2.5,
            "max_diff": 4,
            "over_tolerance_ratio": 0.6,
        }
        assert cr.verdict(metrics, cr.Thresholds()) == "közelítés"

    def test_elter(self) -> None:
        metrics = {
            "ssim": 0.6,
            "delta_e_mean": 15.0,
            "delta_e_p99": 40.0,
            "max_diff": 90,
            "over_tolerance_ratio": 0.9,
        }
        assert cr.verdict(metrics, cr.Thresholds()) == "eltér"


class TestComparePair:
    """Render vs „golden": a saját kimenet önmagával pixelhű kell legyen."""

    def test_sajat_render_onmagaval_pixelhu(self, tmp_path: Path) -> None:
        image = _color_image()
        ops = parse_filters("bw=1;fill=1,0.500000;")
        rendered, _ = apply_filters(image, ops)
        original = tmp_path / "eredeti.png"
        golden = tmp_path / "golden.png"
        cv2.imwrite(str(original), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(golden), cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR))

        result = cr.compare_pair(
            original, "bw=1;fill=1,0.500000;", golden, cr.Thresholds()
        )
        assert result.verdict == "pixelhű"
        assert result.metrics["max_diff"] == 0
        assert result.skipped == ()

    def test_torzitott_golden_elter(self, tmp_path: Path) -> None:
        image = _color_image()
        ops = parse_filters("fill=1,0.500000;")
        rendered, _ = apply_filters(image, ops)
        torzitott = np.clip(rendered.astype(np.int16) + 60, 0, 255).astype(np.uint8)
        original = tmp_path / "eredeti.png"
        golden = tmp_path / "golden.png"
        cv2.imwrite(str(original), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(golden), cv2.cvtColor(torzitott, cv2.COLOR_RGB2BGR))

        result = cr.compare_pair(original, "fill=1,0.500000;", golden, cr.Thresholds())
        assert result.verdict == "eltér"

    def test_kis_eltolas_kozelites(self, tmp_path: Path) -> None:
        image = _gradient_image()
        rendered, _ = apply_filters(image, parse_filters("bw=1;"))
        kozeli = np.clip(rendered.astype(np.int16) + 3, 0, 253).astype(np.uint8)
        original = tmp_path / "eredeti.png"
        golden = tmp_path / "golden.png"
        cv2.imwrite(str(original), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(golden), cv2.cvtColor(kozeli, cv2.COLOR_RGB2BGR))

        result = cr.compare_pair(original, "bw=1;", golden, cr.Thresholds())
        assert result.verdict == "közelítés"

    def test_meret_elteres_hibauzenettel_elter(self, tmp_path: Path) -> None:
        """Ha a golden mérete eltér (pl. rossz crop), az „eltér" + megjegyzés."""
        image = _color_image()
        original = tmp_path / "eredeti.png"
        golden = tmp_path / "golden.png"
        cv2.imwrite(str(original), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        cv2.imwrite(
            str(golden), cv2.cvtColor(image[:20, :20], cv2.COLOR_RGB2BGR)
        )
        result = cr.compare_pair(original, "bw=1;", golden, cr.Thresholds())
        assert result.verdict == "eltér"
        assert "méret" in result.note


class TestLutOverrides:
    def test_hianyzo_konyvtar_ures_override(self, tmp_path: Path) -> None:
        luts = cr.load_luts(tmp_path / "nincs-ilyen")
        assert not luts.has_any()

    def test_hianyzo_fajl_tiszta_kihagyas(self, tmp_path: Path) -> None:
        # üres könyvtár: nincs luts*.json → nincs override, nincs hiba
        luts = cr.load_luts(tmp_path)
        assert not luts.has_any()
        assert luts.fill2d is None

    def test_fill2d_betoltes_es_hasznalat(self, tmp_path: Path) -> None:
        """A mért fill 2D LUT felülírja a beépített közelítést."""
        konstans = [100.0] * 256
        (tmp_path / "luts3.json").write_text(
            json.dumps({"fill2d": {"0.5": konstans}, "hs": {}, "temp": {}})
        )
        luts = cr.load_luts(tmp_path)
        assert luts.has_any()

        image = _gradient_image()
        rendered, skipped, lut_ops = cr.render_chain(
            image, parse_filters("fill=1,0.500000;"), luts
        )
        assert skipped == ()
        assert "fill" in lut_ops
        assert int(rendered.min()) == 100 and int(rendered.max()) == 100

    def test_fill2d_interpolacio_kozbulso_s(self, tmp_path: Path) -> None:
        (tmp_path / "luts3.json").write_text(
            json.dumps(
                {
                    "fill2d": {"0.25": [50.0] * 256, "0.75": [150.0] * 256},
                    "hs": {},
                    "temp": {},
                }
            )
        )
        luts = cr.load_luts(tmp_path)
        rendered, _, _ = cr.render_chain(
            _gradient_image(), parse_filters("fill=1,0.500000;"), luts
        )
        assert int(rendered[0, 0, 0]) == 100  # a két görbe fele-fele keveréke

    def test_lut_nelkuli_szuro_a_beepitett_renderrel_fut(self, tmp_path: Path) -> None:
        (tmp_path / "luts3.json").write_text(
            json.dumps({"fill2d": {"0.5": [100.0] * 256}, "hs": {}, "temp": {}})
        )
        luts = cr.load_luts(tmp_path)
        image = _color_image()
        rendered, skipped, lut_ops = cr.render_chain(
            image, parse_filters("bw=1;"), luts
        )
        expected, _ = apply_filters(image, parse_filters("bw=1;"))
        assert lut_ops == ()
        assert skipped == ()
        assert np.array_equal(rendered, expected)

    def test_temp_offszet_alkalmazasa(self, tmp_path: Path) -> None:
        """A temp-LUT [ΔB, ΔG, ΔR] eltolás — finetune2 p5-re alkalmazva."""
        (tmp_path / "luts3.json").write_text(
            json.dumps(
                {
                    "fill2d": {},
                    "hs": {},
                    # tp100 = +1.0 színhő; [B, G, R] sorrend (cv2-mérés)
                    "temp": {"tp100": [-20.0, 0.0, 10.0]},
                }
            )
        )
        luts = cr.load_luts(tmp_path)
        image = np.full((4, 4, 3), 128, np.uint8)
        chain = "finetune2=1,0.000000,0.000000,0.000000,00000000,1.000000;"
        rendered, _, lut_ops = cr.render_chain(image, parse_filters(chain), luts)
        assert "finetune2" in lut_ops
        assert int(rendered[0, 0, 0]) == 138  # R: +10
        assert int(rendered[0, 0, 1]) == 128  # G: 0
        assert int(rendered[0, 0, 2]) == 108  # B: −20

    def test_render_chain_luts_nelkul_egyezik_az_apply_filtersszel(self) -> None:
        image = _color_image()
        chain = "warm=1;sat=1,0.250000;crop64=1,19991999e666e666;"
        ops = parse_filters(chain)
        rendered, skipped, lut_ops = cr.render_chain(image, ops, cr.load_luts(None))
        expected, expected_skipped = apply_filters(image, ops)
        assert np.array_equal(rendered, expected)
        assert skipped == expected_skipped
        assert lut_ops == ()


class TestKitMode:
    """Mini golden-kit szintetikus felépítése és lefuttatása."""

    def _build_kit(self, kit: Path, torzit: bool = False) -> None:
        folder = kit / "05-tone"
        export = kit / "export" / "05-tone"
        folder.mkdir(parents=True)
        export.mkdir(parents=True)
        image = _color_image()
        name = "chart__bw.jpg"
        cv2.imwrite(str(folder / name), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        rendered, _ = apply_filters(image, parse_filters("bw=1;"))
        if torzit:
            rendered = np.clip(
                rendered.astype(np.int16) + 70, 0, 255
            ).astype(np.uint8)
        # PNG-be írjuk az „exportot", hogy a JPEG-zaj ne zavarjon a tesztben
        golden = export / "chart__bw.png"
        cv2.imwrite(str(golden), cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR))
        (folder / ".picasa.ini").write_text(
            f"[{name}]\nfilters=bw=1;\n", encoding="utf-8"
        )

    def test_kit_futtatas_pixelhu(self, tmp_path: Path) -> None:
        self._build_kit(tmp_path)
        results = cr.run_kit(tmp_path, cr.Thresholds(), cr.load_luts(None))
        assert len(results) == 1
        assert results[0].verdict == "pixelhű"
        assert results[0].name == "05-tone/chart__bw.jpg"

    def test_kit_futtatas_torzitott_elter(self, tmp_path: Path) -> None:
        self._build_kit(tmp_path, torzit=True)
        results = cr.run_kit(tmp_path, cr.Thresholds(), cr.load_luts(None))
        assert results[0].verdict == "eltér"

    def test_hianyzo_export_kihagyva_megjegyzessel(self, tmp_path: Path) -> None:
        self._build_kit(tmp_path)
        (tmp_path / "export" / "05-tone" / "chart__bw.png").unlink()
        results = cr.run_kit(tmp_path, cr.Thresholds(), cr.load_luts(None))
        assert results[0].verdict == "hiányzik"


class TestReport:
    def test_json_riport_szerkezete(self, tmp_path: Path) -> None:
        image = _color_image()
        rendered, _ = apply_filters(image, parse_filters("bw=1;"))
        original = tmp_path / "eredeti.png"
        golden = tmp_path / "golden.png"
        cv2.imwrite(str(original), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(golden), cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR))
        result = cr.compare_pair(original, "bw=1;", golden, cr.Thresholds())

        report = cr.build_report([result], cr.Thresholds(), cr.load_luts(None))
        assert report["osszegzes"]["pixelhű"] == 1
        assert report["eredmenyek"][0]["szurok"] == ["bw"]
        assert "kuszobok" in report
        # JSON-szerializálható kell legyen
        json.dumps(report)

    def test_szurtonkenti_osszegzes(self, tmp_path: Path) -> None:
        image = _color_image()
        rendered, _ = apply_filters(image, parse_filters("bw=1;sat=1,0.500000;"))
        original = tmp_path / "eredeti.png"
        golden = tmp_path / "golden.png"
        cv2.imwrite(str(original), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(golden), cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR))
        result = cr.compare_pair(
            original, "bw=1;sat=1,0.500000;", golden, cr.Thresholds()
        )
        report = cr.build_report([result], cr.Thresholds(), cr.load_luts(None))
        assert report["szuronkent"]["bw"] == "pixelhű"
        assert report["szuronkent"]["sat"] == "pixelhű"

    def test_ember_olvashato_riport(self, tmp_path: Path) -> None:
        image = _color_image()
        rendered, _ = apply_filters(image, parse_filters("bw=1;"))
        original = tmp_path / "eredeti.png"
        golden = tmp_path / "golden.png"
        cv2.imwrite(str(original), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(golden), cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR))
        result = cr.compare_pair(original, "bw=1;", golden, cr.Thresholds())
        report = cr.build_report([result], cr.Thresholds(), cr.load_luts(None))
        text = cr.format_report(report)
        assert "pixelhű" in text
        assert "SSIM" in text


class TestCli:
    def test_pair_mod_json_kimenettel(self, tmp_path: Path) -> None:
        image = _color_image()
        rendered, _ = apply_filters(image, parse_filters("bw=1;"))
        original = tmp_path / "eredeti.png"
        golden = tmp_path / "golden.png"
        out_json = tmp_path / "riport.json"
        cv2.imwrite(str(original), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(golden), cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR))

        exit_code = cr.main(
            [
                "pair",
                str(original),
                str(golden),
                "--filters",
                "bw=1;",
                "--json",
                str(out_json),
            ]
        )
        assert exit_code == 0
        # encoding kötelező: Windowson a default cp1252 elrontaná az "ű"-t
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["osszegzes"]["pixelhű"] == 1

    def test_pair_mod_elteresnel_nem_nulla_kilepes(self, tmp_path: Path) -> None:
        image = _color_image()
        torzitott = np.clip(image.astype(np.int16) + 80, 0, 255).astype(np.uint8)
        original = tmp_path / "eredeti.png"
        golden = tmp_path / "golden.png"
        cv2.imwrite(str(original), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(golden), cv2.cvtColor(torzitott, cv2.COLOR_RGB2BGR))
        exit_code = cr.main(
            ["pair", str(original), str(golden), "--filters", "bw=1;"]
        )
        assert exit_code == 1
