"""A teljes Picasa-exportok összevető eszközének őr-tesztjei (#1143)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest


_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "compare_effect_exports.py"
)


def _load_module():
    """A scripts/ alatti modul fájlútvonalas betöltése."""
    spec = importlib.util.spec_from_file_location("compare_effect_exports", _MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("compare_effect_exports", module)
    spec.loader.exec_module(module)
    return module


cee = _load_module()


def _write_image(path: Path, value: int, shape: tuple[int, int] = (3, 4)) -> None:
    """Kis, veszteségmentes RGB minta kiírása a méréshez."""
    image = np.full((*shape, 3), value, dtype=np.uint8)
    ok = cv2.imwrite(str(path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    assert ok


def _write_rgba_image(path: Path, color: int, alpha: int) -> None:
    """Kis RGBA PNG kiírása, hogy az alfa is a mérés része legyen."""
    image = np.full((3, 4, 4), (color, color, color, alpha), dtype=np.uint8)
    ok = cv2.imwrite(str(path), cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA))
    assert ok


def _write_uint16_image(path: Path, value: int) -> None:
    """16 bites PNG, hogy a különbségszámítás ne csordulhasson túl."""
    image = np.full((3, 4, 3), value, dtype=np.uint16)
    ok = cv2.imwrite(str(path), image)
    assert ok


class TestCompareExports:
    def test_meres_effektenkent_es_variansonkent_determinisztikus(self, tmp_path: Path) -> None:
        original = tmp_path / "picasa"
        rendered = tmp_path / "picasapy"
        original.mkdir()
        rendered.mkdir()
        _write_image(original / "zeta__max.png", 10)
        _write_image(rendered / "zeta__max.png", 16)
        _write_image(original / "alfa__alap.png", 50)
        _write_image(rendered / "alfa__alap.png", 50)

        report = cee.compare_exports(original, rendered, threshold=3.0)

        assert [row["effekt"] for row in report["effektenkent"]] == ["alfa", "zeta"]
        assert report["osszegzes"] == {
            "eredeti_fajlok": 2,
            "picasapy_fajlok": 2,
            "parok": 2,
            "egyezik": 1,
            "elter": 1,
            "hianyzik": 0,
        }
        zeta = report["effektenkent"][1]["valtozatok"][0]
        assert zeta["valtozat"] == "max"
        assert zeta["atlagos_abszolut_csatornaelteres"] == pytest.approx(6.0)
        assert zeta["verdikt"] == "ELTÉR"

    def test_mereteltetest_hangosan_es_elteteskent_jelzi(self, tmp_path: Path) -> None:
        original = tmp_path / "picasa"
        rendered = tmp_path / "picasapy"
        original.mkdir()
        rendered.mkdir()
        _write_image(original / "polaroid__alap.png", 0, shape=(3, 4))
        _write_image(rendered / "polaroid__alap.png", 0, shape=(4, 5))

        report = cee.compare_exports(original, rendered, threshold=3.0)

        row = report["effektenkent"][0]["valtozatok"][0]
        assert row["verdikt"] == "ELTÉR"
        assert row["atlagos_abszolut_csatornaelteres"] is None
        assert row["megjegyzes"] == "MÉRET 4x3 vs 5x4"

    def test_hianyzo_fajlt_is_jelzi(self, tmp_path: Path) -> None:
        original = tmp_path / "picasa"
        rendered = tmp_path / "picasapy"
        original.mkdir()
        rendered.mkdir()
        _write_image(original / "tint__hex8.png", 10)

        report = cee.compare_exports(original, rendered, threshold=3.0)

        row = report["effektenkent"][0]["valtozatok"][0]
        assert row["verdikt"] == "HIÁNYZIK"
        assert row["megjegyzes"] == "A PicasaPy-exportból hiányzik"

    def test_png_alfa_elterest_is_mer(self, tmp_path: Path) -> None:
        original = tmp_path / "picasa"
        rendered = tmp_path / "picasapy"
        original.mkdir()
        rendered.mkdir()
        _write_rgba_image(original / "frame__alap.png", color=42, alpha=255)
        _write_rgba_image(rendered / "frame__alap.png", color=42, alpha=0)

        report = cee.compare_exports(original, rendered, threshold=3.0)

        row = report["effektenkent"][0]["valtozatok"][0]
        assert row["verdikt"] == "ELTÉR"
        assert row["atlagos_abszolut_csatornaelteres"] == pytest.approx(63.75)

    def test_16_bites_png_kulonbsege_nem_csordul_tul(self, tmp_path: Path) -> None:
        original = tmp_path / "picasa"
        rendered = tmp_path / "picasapy"
        original.mkdir()
        rendered.mkdir()
        _write_uint16_image(original / "hdr__alap.png", 65_535)
        _write_uint16_image(rendered / "hdr__alap.png", 0)

        report = cee.compare_exports(original, rendered, threshold=3.0)

        row = report["effektenkent"][0]["valtozatok"][0]
        assert row["verdikt"] == "ELTÉR"
        assert row["atlagos_abszolut_csatornaelteres"] == pytest.approx(65_535.0)

    @pytest.mark.parametrize("threshold", [-0.1, float("nan"), "nem-szam"])
    def test_ervenytelen_kuszob_hibauzenete_vilagos(self, tmp_path: Path, threshold: object) -> None:
        with pytest.raises(ValueError, match="nemnegatív"):
            cee.compare_exports(tmp_path, tmp_path, threshold=threshold)
