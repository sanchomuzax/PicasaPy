"""#4370: a Border minden RGB-pixelje egyezzen a három natív goldennel."""

from __future__ import annotations

import hashlib

import numpy as np
import pytest

from picasapy.render.glimmer_frame_ops import draw_border


_GOLDENEK = (
    (
        "5x5",
        5,
        5,
        2,
        1,
        1,
        "6cc49f17dd4f3df6c5129b74a20a98277d646180949584f971564e4f42143d3b",
        """
        ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000
        ff000000 ffb4b4b4 ffffffff ffffffff ffffffff ffffffff ffffffff ffa6a6a6 ff000000
        ff000000 ffffffff ff6b8095 ff204060 ff204060 ff204060 ff798c9f ffffffff ff000000
        ff000000 ffffffff ff204060 ff204060 ff204060 ff204060 ff2e4c6a ffffffff ff000000
        ff000000 ffffffff ff204060 ff204060 ff204060 ff204060 ff204060 ffffffff ff000000
        ff000000 ffffffff ff6b8095 ff204060 ff204060 ff204060 ff798c9f ffffffff ff000000
        ff000000 ffb4b4b4 ffffffff ffbac4ce ff204060 ffbfc8d1 ffffffff ffa6a6a6 ff000000
        ff000000 ff000000 ff868686 ffd9d9d9 ffffffff ffd6d6d6 ff7e7e7e ff000000 ff000000
        ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000
        """,
    ),
    (
        "7x7",
        7,
        7,
        3,
        1,
        2,
        "9aae624f6d8749515ccd1379cf3c613624dc9f2ba6df8c445dee1181a971010d",
        """
        ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000
        ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000
        ff000000 ff000000 ff474747 ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff fffbfbfb ff393939 ff000000 ff000000
        ff000000 ff000000 ffe7e7e7 ffd3d9df ff234262 ff204060 ff204060 ff204060 ff2b4968 ffe1e5e9 ffd9d9d9 ff000000 ff000000
        ff000000 ff000000 ffffffff ff4d6680 ff204060 ff204060 ff204060 ff204060 ff204060 ff5b728a ffffffff ff000000 ff000000
        ff000000 ff000000 ffffffff ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff2e4c6a ffffffff ff000000 ff000000
        ff000000 ff000000 ffffffff ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ffffffff ff000000 ff000000
        ff000000 ff000000 ffffffff ff4d6680 ff204060 ff204060 ff204060 ff204060 ff204060 ff5b728a ffffffff ff000000 ff000000
        ff000000 ff000000 ffe7e7e7 ffd3d9df ff234262 ff204060 ff204060 ff204060 ff2b4968 ffe1e5e9 ffd9d9d9 ff000000 ff000000
        ff000000 ff000000 ff474747 ffffffff ffffffff ffacb8c4 ff204060 ffafbac6 ffffffff fffbfbfb ff393939 ff000000 ff000000
        ff000000 ff000000 ff000000 ff252525 ffa3a3a3 ffe1e1e1 ffffffff ffdfdfdf ff9d9d9d ff1b1b1b ff000000 ff000000 ff000000
        ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000
        ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000
        """,
    ),
    (
        "9x8",
        9,
        8,
        4,
        2,
        1,
        "2d354156d605e7fc7fdbf5a5f41d6703b3f21770f50e3d24f80d2b1b2c75c33c",
        """
        ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000
        ff000000 ff000000 ff2d2d2d ffd6d6d6 ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff ffcdcdcd ff212121 ff000000 ff000000
        ff000000 ff191919 ffededed ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff ffe1e1e1 ff0a0a0a ff000000
        ff000000 ffaeaeae ffffffff ffffffff ff8294a6 ff204060 ff204060 ff204060 ff204060 ff204060 ff8c9cad ffffffff ffffffff ffa0a0a0 ff000000
        ff000000 ffffffff ffffffff ffa0aebb ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ffaebac5 ffffffff ffffffff ff000000
        ff000000 ffffffff ffffffff ff405b77 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff4e6781 ffffffff ffffffff ff000000
        ff000000 ffffffff ffffffff ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff2e4c6a ffffffff ffffffff ff000000
        ff000000 ffffffff ffffffff ff405b77 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff4e6781 ffffffff ffffffff ff000000
        ff000000 ffffffff ffffffff ffa0aebb ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ffaebac5 ffffffff ffffffff ff000000
        ff000000 ffaeaeae ffffffff ffffffff ff8294a6 ff204060 ff204060 ff204060 ff204060 ff204060 ff8c9cad ffffffff ffffffff ffa0a0a0 ff000000
        ff000000 ff191919 ffededed ffffffff ffffffff ffe4e8ec ffa6b3c0 ff204060 ffa8b4c1 ffeaedf0 ffffffff ffffffff ffe1e1e1 ff0a0a0a ff000000
        ff000000 ff000000 ff2d2d2d ffd6d6d6 ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff ffffffff ffcdcdcd ff212121 ff000000 ff000000
        ff000000 ff000000 ff000000 ff000000 ff6a6a6a ffbebebe ffe8e8e8 ffffffff ffe6e6e6 ffbababa ff646464 ff000000 ff000000 ff000000 ff000000
        ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000
        """,
    ),
)


def _rgb(arbg: np.ndarray) -> np.ndarray:
    return np.stack(
        ((arbg >> 16) & 0xFF, (arbg >> 8) & 0xFF, arbg & 0xFF), axis=-1
    ).astype(np.uint8)


@pytest.mark.parametrize(
    ("nev", "szelesseg", "magassag", "sugar", "belso", "kulso", "sha256", "sorok"),
    _GOLDENEK,
    ids=[eset[0] for eset in _GOLDENEK],
)
def test_a_teljes_rgb_kimenet_bajtra_egyezik_a_nativ_goldennel(
    nev, szelesseg, magassag, sugar, belso, kulso, sha256, sorok
):
    natív = np.array(
        [[int(pixel, 16) for pixel in sor.split()] for sor in sorok.splitlines() if sor.strip()],
        dtype="<u4",
    )
    assert hashlib.sha256(natív.tobytes()).hexdigest() == sha256

    kep = np.full((magassag, szelesseg, 3), (0x20, 0x40, 0x60), dtype=np.uint8)
    eredmeny = draw_border(kep, (0, 0, 0), (255, 255, 255), kulso, belso, sugar)
    vart = _rgb(natív)

    assert eredmeny.shape == vart.shape
    elteresek = np.argwhere(eredmeny != vart)
    if elteresek.size:
        pixelek = np.unique(elteresek[:, :2], axis=0)
        elso = [
            (int(y), int(x), int(csatorna), int(eredmeny[y, x, csatorna]), int(vart[y, x, csatorna]))
            for y, x, csatorna in elteresek[:12]
        ]
        pytest.fail(
            f"{nev}: {len(pixelek)} eltérő pixel / {elteresek.shape[0]} eltérő RGB-csatorna; "
            f"első eltérések (y,x,csatorna,tényleges,várt): {elso}"
        )
