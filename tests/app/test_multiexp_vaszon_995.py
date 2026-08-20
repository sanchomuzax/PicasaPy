r"""A Többszörös exponálás vászna UGYANAZT keveri, mint a mentés (#995).

## A tulajdonos panasza

A vászon a csempéket **egymásra rakja** (takarják egymást), a mentés viszont
**egyenlő súllyal keveri**. A felhasználó a PANELEN dolgozik, tehát számára
a funkció „nem működik" — a mentés jósága ezen nem segít.

## ⚠️ A jegyben javasolt `1/k` MEGDŐLT — mérve

Három egyszínű képre (255 / 0 / 0), fekete lapon:

| út | eredmény |
|---|---|
| a mentés (`blend_multi_exposure`, egyenlő súlyú átlag) | **85** |
| Qt source-over, **fix `1/k`** minden csempén (a jegy javaslata) | 37,8 ❌ |
| Qt source-over, az **i-edik csempén `1/(i+1)`** | **85** ✅ |

A futó átlag azonossága miatt:

    v_i = 1/(i+1) · kép_i + i/(i+1) · v_(i−1)

ami lépésenként pontosan az addigi képek számtani átlaga. A fix `1/k` a
korábbi rétegeket ismételten csökkenti, ezért a legelső képek súlya
`(1−1/k)` hatványaival fogy.

Ez a fájl **magát az azonosságot** állítja (számolással, platformfüggetlenül)
és a modell-szerepet, ami a felületnek átadja.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.app.collage_model import CollageNode, CollageNodeModel
from picasapy.collage.multi_exposure import blend_multi_exposure


def _modell(darab: int, *, multiexp: bool) -> CollageNodeModel:
    modell = CollageNodeModel()
    modell.set_multi_exposure(multiexp)
    modell.set_nodes(
        [
            CollageNode(
                path=f"{i}.jpg", center_x=1.0, center_y=1.0,
                width=1.0, height=1.0, theta=0.0,
            )
            for i in range(darab)
        ]
    )
    return modell


class TestAzAzonossag:
    """A rétegzés matematikailag az egyenlő súlyú átlagot adja."""

    @pytest.mark.parametrize("szinek", [(255, 0, 0), (10, 200, 90, 30), (7,)])
    def test_a_retegzes_az_ATLAGOT_adja(self, szinek):
        kepek = [np.full((4, 4, 3), ertek, np.uint8) for ertek in szinek]
        vart = blend_multi_exposure(kepek, 4, 4)

        vaszon = np.zeros((4, 4, 3), np.float64)
        for i, kep in enumerate(kepek):
            alfa = 1.0 / (i + 1)
            vaszon = alfa * kep.astype(np.float64) + (1.0 - alfa) * vaszon

        assert np.allclose(vaszon, vart.astype(np.float64), atol=1.0)

    def test_a_FIX_1_per_k_NEM_adja(self):
        """A jegy javaslatának cáfolata — ha ez egyszer megfordul, a
        docstring indoklása is elavult."""
        kepek = [np.full((4, 4, 3), ertek, np.uint8) for ertek in (255, 0, 0)]
        vart = blend_multi_exposure(kepek, 4, 4)

        vaszon = np.zeros((4, 4, 3), np.float64)
        for kep in kepek:
            alfa = 1.0 / len(kepek)
            vaszon = alfa * kep.astype(np.float64) + (1.0 - alfa) * vaszon

        assert not np.allclose(vaszon, vart.astype(np.float64), atol=1.0)


class TestAModellSzerep:
    def test_multiexpnel_a_retegsorrend_szerint(self):
        modell = _modell(4, multiexp=True)

        assert [modell.tile_opacity(i) for i in range(4)] == [1.0, 0.5, 1 / 3, 0.25]

    def test_mas_temanal_MINDIG_egy(self):
        modell = _modell(4, multiexp=False)

        assert [modell.tile_opacity(i) for i in range(4)] == [1.0, 1.0, 1.0, 1.0]

    def test_a_szerep_neve_tileOpacity(self):
        nevek = {bytes(n).decode() for n in CollageNodeModel().roleNames().values()}

        assert "tileOpacity" in nevek

    def test_a_szerepen_at_is_ugyanazt_adja(self):
        modell = _modell(3, multiexp=True)

        ertekek = [
            modell.data(modell.index(sor, 0), CollageNodeModel.OpacityRole)
            for sor in range(3)
        ]

        assert ertekek == [1.0, 0.5, 1 / 3]


class TestAFeluletHasznalja:
    """A szerep hiába van meg, ha a QML nem köti be (#1051 hibaosztálya)."""

    def test_a_delegalt_koti_a_tileOpacity_t(self):
        from pathlib import Path

        import picasapy.app

        qml = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
        lap = (qml / "CollageSheet.qml").read_text(encoding="utf-8")
        csempe = (qml / "CollageNode.qml").read_text(encoding="utf-8")

        assert "tileOpacity: model.tileOpacity" in lap
        assert "node.tileOpacity" in csempe
