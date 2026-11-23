"""#7400: A Hangolás finetune2 színsemlegesítése és Színhőmérséklete."""

from __future__ import annotations

from pathlib import Path
from PIL import Image
import numpy as np
import pytest

from picasapy.render.tone import (
    apply_color_temperature,
    apply_finetune2,
    apply_neutral_pipette,
    parse_neutral_argb,
)
from picasapy.render.gpu_point_pipeline import build_finetune2_lut
from picasapy.ini.filters import FilterOp
from picasapy.edit.session import EditSession


def _uniform_image(color: tuple[int, int, int], size: int = 40) -> np.ndarray:
    return np.full((size, size, 3), color, dtype=np.uint8)


class TestFinetune2Neutral7400:
    def test_j5a_15_kocka_pipetta_semlegesites(self) -> None:
        """A J5a bézs foltja [200, 151, 121] pipetta (ffc89779) után a1a1a1 [161, 161, 161]."""
        image = _uniform_image((200, 151, 121))
        neutral = parse_neutral_argb("ffc89779")
        assert neutral == (200, 151, 121)
        result = apply_neutral_pipette(image, neutral)
        mean = result.mean(axis=(0, 1))
        # Eredeti Picasa 15. kocka mért értéke: [161, 161, 161] (hiba: 0)
        np.testing.assert_allclose(mean, [161.0, 161.0, 161.0], atol=3.0)

    def test_j5a_25_kocka_pipetta_es_homerseklet(self) -> None:
        """A J5a bézs foltja pipetta és temp 1.0 után aba088 [171, 160, 136]."""
        image = _uniform_image((200, 151, 121))
        neutral = parse_neutral_argb("ffc89779")
        result = apply_finetune2(
            image, fill=0.0, highlights=0.0, shadows=0.0, neutral=neutral, temperature=1.0
        )
        mean = result.mean(axis=(0, 1))
        # Eredeti Picasa 25. kocka mért értéke: [171, 160, 136] (hiba: 0)
        np.testing.assert_allclose(mean, [171.0, 160.0, 136.0], atol=3.0)

    def test_j5a_23_kocka_szinhomerseklet(self) -> None:
        """Csak temp 1.0: a MAI kimenet rögzítése (d29766), NEM az eredeti egyezése.

        Az eredeti 23. kocka `cf9c54`-et mutat; az eltérés nyitott kérdés, külön
        jegy viszi. Ez a próba csak azt őrzi, hogy a #7400 a hőmérséklet-ághoz
        nem nyúlt."""
        image = _uniform_image((200, 151, 121))
        result = apply_color_temperature(image, 1.0)
        mean = result.mean(axis=(0, 1))
        np.testing.assert_allclose(mean, [210.0, 151.0, 102.0], atol=3.0)

    def test_semleges_pipetta_es_nulla_szin_azonossag(self) -> None:
        """(0,0,0) vagy szürke pipetta nem torzítja a semleges képet."""
        image = _uniform_image((128, 128, 128))
        np.testing.assert_array_equal(apply_neutral_pipette(image, (0, 0, 0)), image)
        np.testing.assert_array_equal(apply_neutral_pipette(image, (128, 128, 128)), image)

    def test_build_finetune2_lut_nem_nulla_neutral_elutasitva(self) -> None:
        """A 3x3-as CAT mátrix nem adható 1D LUT-tal -> ValueError (#7400)."""
        with pytest.raises(ValueError, match="neutral"):
            build_finetune2_lut(neutral=(200, 151, 121))

    def test_edit_session_gpu_finetune_prefix_neutral_eseten_none(self) -> None:
        """A finetune2 pipetta esetén a GPU élő-előnézet CPU-ra esik vissza (#7400)."""
        # Semleges pipetta nélkül (csak highlights): prefix elérhető
        s_sima = EditSession(ops=(FilterOp("finetune2", ("1", "0.0", "0.2", "0.0", "00000000", "0.0")),))
        assert s_sima.gpu_finetune_prefix() == ()

        # Nem semleges pipettával (p4=ffc89779): prefix None -> CPU visszahullás
        s_pipetta = EditSession(ops=(FilterOp("finetune2", ("1", "0.0", "0.2", "0.0", "ffc89779", "0.0")),))
        assert s_pipetta.gpu_finetune_prefix() is None

    def test_job_852_kepernyokepek_40x40_atlag_paritas(self) -> None:
        """Összevetés a .tmp/job-852 15. és 25. kockájának képernyőképével."""
        job_dir = Path(__file__).resolve().parents[2] / ".tmp" / "job-852"
        if not (job_dir / "kepernyo__15.png").exists():
            pytest.skip(".tmp/job-852 képernyőképek nem találhatók")

        # A bézs folt közepe a képernyőképen (620, 528), 40x40 méretben
        im15 = np.array(Image.open(job_dir / "kepernyo__15.png").convert("RGB"))
        patch15 = im15[508:548, 600:640].mean(axis=(0, 1))

        im25 = np.array(Image.open(job_dir / "kepernyo__25.png").convert("RGB"))
        patch25 = im25[508:548, 600:640].mean(axis=(0, 1))

        # A PicasaPy render kimenete az eredeti [200, 151, 121] bemenetre:
        image = _uniform_image((200, 151, 121), size=40)
        out15 = apply_finetune2(image, fill=0.0, highlights=0.0, shadows=0.0, neutral=(200, 151, 121), temperature=0.0)
        out25 = apply_finetune2(image, fill=0.0, highlights=0.0, shadows=0.0, neutral=(200, 151, 121), temperature=1.0)

        # ±3 szinten belüli egyezés a 15. és 25. kockán:
        np.testing.assert_allclose(out15.mean(axis=(0, 1)), patch15, atol=3.0)
        np.testing.assert_allclose(out25.mean(axis=(0, 1)), patch25, atol=3.0)
