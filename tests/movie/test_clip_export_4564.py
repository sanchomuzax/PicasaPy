"""#4564: a videó exportja csak a megadott vágási szakaszt tartalmazza."""

from __future__ import annotations

import cv2
import pytest

from tests.support.video_factory import make_mp4


def _duration_seconds(path):
    capture = cv2.VideoCapture(str(path))
    try:
        assert capture.isOpened(), f"A kimeneti videó nem nyitható meg: {path}"
        fps = capture.get(cv2.CAP_PROP_FPS)
        frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        assert fps > 0
        return frames / fps
    finally:
        capture.release()


def test_a_kimeneti_fajl_csak_a_vagott_szakaszt_tartalmazza(tmp_path):
    from picasapy.movie.clip_export import export_clip

    source = make_mp4(tmp_path / "eredeti.mp4", frames=30, fps=10)
    output_dir = tmp_path / "Exportált videoklipek"

    output = export_clip(source, output_dir, start_ms=500, end_ms=1500)

    assert output.is_file()
    assert output.parent == output_dir
    assert output.suffix == ".mp4"
    assert _duration_seconds(output) == pytest.approx(1.0, abs=0.15)


def test_ismetelt_export_nem_irja_felul_a_meglevo_klipet(tmp_path):
    from picasapy.movie.clip_export import export_clip

    source = make_mp4(tmp_path / "eredeti.mp4", frames=30, fps=10)
    output_dir = tmp_path / "Exportált videoklipek"

    elso = export_clip(source, output_dir, start_ms=500, end_ms=1500)
    masodik = export_clip(source, output_dir, start_ms=500, end_ms=1500)

    assert elso.is_file()
    assert masodik.is_file()
    assert masodik != elso
    assert _duration_seconds(masodik) == pytest.approx(1.0, abs=0.15)
