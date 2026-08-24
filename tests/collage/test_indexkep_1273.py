"""Az Indexkép Picasa-hű fejléce, geometriája és élő frissítése (#1273).

A számok a valódi ``AI6.cxf``-ből és a Picasa ``CContactSheetTheme``
dekompilált rajzolójából származnak.  Az őrök szándékosan a megfigyelhető
kimenetet mérik: a csomópontok helyét és a kirajzolt fejléc szövegeit.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.collage.contact_sheet import header_lines
from picasapy.collage.picasa_render import (
    PicasaCollageSettings,
    _unicode_font,
    layout_nodes_for_aspects,
    render_nodes,
)
from picasapy.collage.themes import CONTACTSHEET, WHITEBORDER


AI6_ASPECTS = (0.8, 0.8, 0.5625, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8)


def _bal_felso(node, width: int, height: int) -> tuple[float, float, float, float]:
    """A lapegységes csomópontot a ``.cxf`` normalizált alakjára hozza."""
    x = (node.center_x - node.width / 2.0) / 1024.0
    y = (node.center_y - node.height / 2.0) / (1024.0 * height / width)
    return x, y, node.width / 1024.0, node.height / (1024.0 * height / width)


def test_a_fejlec_tartalma_az_AI6_projektmezoibol_jon():
    assert header_lines("AI", "2023. november", 9) == (
        "AI",
        "9 kép, 2023. november",
    )


def test_a_hianyzo_datum_nem_hagy_logó_vesszot():
    assert header_lines("Kollázs", "", 3) == ("Kollázs", "3 kép")


def test_a_fejlec_betuje_valoban_ismeri_a_magyar_ekezetet():
    font = _unicode_font(24)
    ekezet = font.getmask("é")
    hianyjel = font.getmask("□")
    assert (ekezet.size, bytes(ekezet)) != (hianyjel.size, bytes(hianyjel))


def test_az_AI6_racsa_margot_hezzagot_aranyt_es_feher_keretet_kap():
    settings = PicasaCollageSettings(
        theme=CONTACTSHEET,
        border=WHITEBORDER,
        width=3841,
        height=5120,
        album_title="AI",
        album_date="2023. november",
    )
    paths = tuple(Path(f"{index}.png") for index in range(9))
    nodes = layout_nodes_for_aspects(AI6_ASPECTS, paths, settings)
    mert = [_bal_felso(node, settings.width, settings.height) for node in nodes]

    # AI6.cxf: első x=0,087891; osztás=0,292969; első y=0,166300;
    # sorosztás=0,263004. A kerekítési és a forrás-aspektus eltérésére
    # legfeljebb egy század laparány marad.
    assert mert[0][0] == pytest.approx(0.087891, abs=0.01)
    assert mert[1][0] - mert[0][0] == pytest.approx(0.292969, abs=0.01)
    assert mert[0][1] == pytest.approx(0.166300, abs=0.01)
    assert mert[3][1] - mert[0][1] == pytest.approx(0.263004, abs=0.01)
    assert mert[0][2] == pytest.approx(0.236328, abs=0.005)
    assert mert[0][3] == pytest.approx(0.221612, abs=0.01)
    assert mert[2][2] == pytest.approx(0.151367, abs=0.01)

    assert all(node.border == WHITEBORDER for node in nodes)
    assert mert[0][2] < 0.292969, "a csempe nem töltheti ki a teljes osztást"
    assert mert[0][3] < 0.263004, "a sorok között is résnek kell maradnia"
    assert mert[2][2] < mert[0][2], "a keskeny képnek keskenyebbnek kell maradnia"


def test_az_elo_render_minden_szerkesztesnel_ujrarajzolja_a_fejlecet(tmp_path):
    image = np.full((40, 32, 3), (30, 80, 150), dtype=np.uint8)
    source = tmp_path / "kep.png"
    assert cv2.imwrite(str(source), image)
    settings = PicasaCollageSettings(
        theme=CONTACTSHEET,
        border=WHITEBORDER,
        width=320,
        height=400,
        album_title="AI",
        album_date="2023. november",
    )
    nodes = layout_nodes_for_aspects((0.8,), (source,), settings)
    first = render_nodes(nodes, settings).image
    second = render_nodes(
        nodes,
        PicasaCollageSettings(
            theme=CONTACTSHEET,
            border=WHITEBORDER,
            width=320,
            height=400,
            album_title="Átírva",
            album_date="2024. január",
        ),
    ).image

    assert not np.array_equal(first, second)
