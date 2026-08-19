"""A KIMENETI `.cxf` háttérképe (#1009).

A `render_collage` a JPEG mellé kiírja a `.cxf` párt (spec 9.1). Ha a
háttérkép csak a piszkozatba kerülne bele, a Kollázsok albumba mentett
projektfájl más kollázst írna le, mint amit a felhasználó látott.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.app import collage_output as output
from picasapy.collage.cxf import loads
from picasapy.collage.nodes import CollageNode
from picasapy.collage.themes import NOBORDER, PICTUREPILE

from support.jpeg_factory import make_jpeg


@pytest.fixture
def kepek(tmp_path):
    mappa = tmp_path / "Nyaralás 2026"
    mappa.mkdir()
    utak = [mappa / "a.jpg", mappa / "b.jpg"]
    for ut in utak:
        make_jpeg(ut, size=(80, 60))
    return utak


def _settings():
    return output.render_settings(
        theme=PICTUREPILE,
        border=NOBORDER,
        spacing=0.0,
        shadows=False,
        page_ratio=0.75,
        background_rgb=(255, 255, 255),
        frame_center=-1,
        seed=1,
        width=256,
    )


def _nodes(utak):
    return tuple(
        CollageNode(
            path=str(ut),
            center_x=250.0 + 250.0 * index,
            center_y=300.0,
            width=180.0,
            height=140.0,
        )
        for index, ut in enumerate(utak)
    )


def test_a_kimeneti_cxf_orzi_a_hatterkepet(tmp_path, kepek):
    cel = tmp_path / "Nyaralás.jpg"
    output.render_collage(
        _nodes(kepek), _settings(), cel, background_image=str(kepek[0])
    )
    projekt = loads(cel.with_suffix(".cxf").read_bytes())
    assert projekt.background.type == "image"
    assert Path(projekt.background.src).name == "a.jpg"


def test_hatterkep_nelkul_egyszinu_marad(tmp_path, kepek):
    cel = tmp_path / "Nyaralás.jpg"
    output.render_collage(_nodes(kepek), _settings(), cel)
    projekt = loads(cel.with_suffix(".cxf").read_bytes())
    assert projekt.background.type == "solid"
