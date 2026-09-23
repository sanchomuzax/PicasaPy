"""A GPU-út új szűrőinek LUT-ja — a CPU kimenetéből, KÉPPONTRA (#22).

## A jegy kikötése

*„a LUT-ok a MAI CPU-implementációból származzanak (nem újraszámolt
képlet): ugyanaz a kimenet, képpontra"*.

Ez a próbasor ezt méri: a négy szűrőt lefuttatja a CPU-lánc kezelőjével,
kinyeri a csatornánkénti LUT-ot a VALÓDI kimenetéből, majd a LUT-tal
újraszámolja a képet — és **bitre azonos** eredményt követel.

## A szűrők MÉRÉSBŐL jönnek

| szűrő | CPU-idő a célgépen | LUT-tal kifejezhető |
|---|---:|---|
| `autocontrast` | 146 ms | igen |
| `colortemp` | 702 ms | igen |
| `crossprocess` | 863 ms | **nem** (#3452) |
| `enhance` | 174 ms | igen |
| `warm` | 104 ms | igen |

⛔ Az `invert` szándékosan kimarad: 5,6 ms, a 100 ms-os küszöb alatt.
⛔ A `crossprocess` is kimarad (#3452): a záró fényesség-tartó `Tint`
csatornák közötti, tehát csatornánkénti LUT-tal nem fejezhető ki.

## Amit ez a próbasor NEM mér

A GPU-t. Itt egyetlen shader sem fut: a LUT-os út CPU-oldali mása
(`lut_alkalmaz`) az, amit a `PointFilter.frag` három textúra-mintavétele
megvalósít. Hogy a SHADER is ugyanezt adja, a #3070 óta a
tesztkörnyezetben nem mérhető (nincs RHI-kontextus), és a jegy sem ígér
GPU-időt.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import FilterOp
from picasapy.render.chain import _HANDLERS
from picasapy.render.gpu_point_pipeline import (
    GPU_PONT_SZUROK,
    csatorna_lut_a_kimenetbol,
    lut_alkalmaz,
)

#: a mért paraméter-alakok (a lánc-kezelők ezt kapják a `.picasa.ini`-ből)
PARAMETEREK: dict[str, tuple[str, ...]] = {
    "autocontrast": ("1",),
    "colortemp": ("1", "0.5"),
    "enhance": ("1",),
    "warm": ("1",),
}


def _proba_kep(magvet: int = 7, magassag: int = 24, szelesseg: int = 32):
    """Véletlen kép — MINDEN szint jelenlétét nem feltételezzük."""
    rng = np.random.default_rng(magvet)
    return rng.integers(0, 256, size=(magassag, szelesseg, 3), dtype=np.uint8)


def test_az_ot_szuro_a_MERT_halmaz() -> None:
    assert GPU_PONT_SZUROK == frozenset(PARAMETEREK)
    assert "invert" not in GPU_PONT_SZUROK, (
        "az invert 5,6 ms — a küszöb alatt, GPU-ra vinni nyereség nélküli")


@pytest.mark.parametrize("nev", sorted(PARAMETEREK))
def test_a_LUT_bitre_ugyanazt_adja(nev: str) -> None:
    kep = _proba_kep()
    cpu = _HANDLERS[nev](kep, FilterOp(name=nev, params=PARAMETEREK[nev]))
    lut = csatorna_lut_a_kimenetbol(kep, cpu)
    assert np.array_equal(lut_alkalmaz(kep, lut), cpu), (
        f"{nev}: a LUT-os út eltér a CPU kimenetétől")


@pytest.mark.parametrize("nev", sorted(PARAMETEREK))
def test_MAS_kepen_is_bitre_egyezik(nev: str) -> None:
    """Másik magvetés, más hisztogram — a statisztika-függő szűrőknél ez a
    lényeg: a LUT ahhoz a képhez tartozik, amiből kinyertük."""
    kep = _proba_kep(magvet=99, magassag=40, szelesseg=17)
    cpu = _HANDLERS[nev](kep, FilterOp(name=nev, params=PARAMETEREK[nev]))
    lut = csatorna_lut_a_kimenetbol(kep, cpu)
    assert np.array_equal(lut_alkalmaz(kep, lut), cpu)


def test_a_nem_pontonkenti_szuro_HIBAT_ad() -> None:
    """Ellenpróba: ha a leképezés nem egyértelmű, nem csendben rontunk.

    A `blur` szomszéd-képpontokat keverve ugyanahhoz a bemeneti szinthez
    több kimenetet ad — a LUT-os GPU-út némán MÁS képet adna.
    """
    kep = _proba_kep()
    elmosott = _HANDLERS["blur"](kep, FilterOp(name="blur", params=("1", "2.0")))
    with pytest.raises(ValueError, match="NEM pontonkénti"):
        csatorna_lut_a_kimenetbol(kep, elmosott)


def test_a_hianyzo_szinteket_interpolalja() -> None:
    """Szegényes hisztogram: a LUT-nak mind a 256 szintre kell érték."""
    kep = np.zeros((4, 4, 3), dtype=np.uint8)
    kep[..., 0] = 10
    kep[0, 0, 0] = 200
    eredmeny = kep.copy()
    eredmeny[..., 0] = np.where(kep[..., 0] == 10, 20, 100)
    lut = csatorna_lut_a_kimenetbol(kep, eredmeny)
    assert lut.shape == (256, 3)
    assert lut[10, 0] == 20 and lut[200, 0] == 100
    #: a két mért pont KÖZÖTT lineáris, a szélein a szélső érték ismétlődik
    assert lut[0, 0] == 20 and lut[255, 0] == 100
    assert 20 < int(lut[105, 0]) < 100


def test_a_rossz_alaku_LUT_hibat_ad() -> None:
    with pytest.raises(ValueError, match=r"\(256, 3\)"):
        lut_alkalmaz(_proba_kep(), np.zeros((128, 3), dtype=np.uint8))


def test_kulonbozo_alaku_be_es_kimenet_hibat_ad() -> None:
    with pytest.raises(ValueError, match="azonos alakú"):
        csatorna_lut_a_kimenetbol(_proba_kep(), _proba_kep(magassag=8))
