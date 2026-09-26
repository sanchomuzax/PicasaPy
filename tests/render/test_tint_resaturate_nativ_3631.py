"""#3631: a `Tint` `Resaturate`-táblája (`0x00bce2f0`) bitre pontosan.

A golden-készlet (`tests/support/native_filter_reference/
tint_resaturate_3631.json`) a `Picasa3.exe` natív táblaelemének
unicorn-emulátorban futtatott KIMENETE (`~/picasapy-agent/eszkozok/
nativ_emu/tint_lut.py`) 54 színre, színenként mind a 256 fényességszintre —
nem a mi modellünkből számolt érték. A CI-n nincs unicorn, ezért a teszt
csak a rögzített bájtokat hasonlítja; az eltérő bájtok száma mindenhol 0.

A készletben ott van a két korábban 71 szintig eltérő telített szín
(`0x0000ff`, `0xffff00`), a `PicnikTint` alapszíne (`0x80cfff`), a
`CrossProcess` sárgája (`0xfcff00`), a Ghoul Eye zöldje (`0xc2ff9e`), egy
neutrális szürke és 40 véletlen szín.

A súlyok utolsó jegyének ±1-es rontása az 54 színből 16–34-en ad eltérő
táblát (mind a hat irányban mérve), tehát a bitre egyező mérce elkapja.
"""

# rontás-kontroll: glimmer_ops._HAEBERLI_WEIGHTS = (0.3087, 0.6094, 0.0820) → 1 failed (-x; 27 szín eltér)

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

import picasapy.render.glimmer_ops as glimmer_ops
from picasapy.render.glimmer_ops import _resaturate_table

_GOLDEN = (
    Path(__file__).resolve().parents[1]
    / "support"
    / "native_filter_reference"
    / "tint_resaturate_3631.json"
)


@lru_cache(maxsize=1)
def _adat() -> dict:
    return json.loads(_GOLDEN.read_text(encoding="utf-8"))


def _szin(kulcs: str) -> tuple[int, int, int]:
    ertek = int(kulcs, 16)
    return (ertek >> 16) & 255, (ertek >> 8) & 255, ertek & 255


def _vart(kulcs: str) -> np.ndarray:
    nyers = np.frombuffer(bytes.fromhex(_adat()["szinek"][kulcs]), dtype=np.uint8)
    return nyers.reshape(256, 3)


def _kulcsok() -> list[str]:
    return list(_adat()["szinek"])


def test_a_golden_ep_es_eleg_szint_fed_le():
    adat = _adat()
    lenyomat = hashlib.sha256(
        "".join(k + v for k, v in adat["szinek"].items()).encode()
    ).hexdigest()
    assert lenyomat == adat["sha256"]
    assert len(adat["szinek"]) >= 8
    for kulcs in ("0x0000ff", "0xffff00", "0x80cfff", "0xfcff00", "0xc2ff9e"):
        assert kulcs in adat["szinek"]


@pytest.mark.parametrize("kulcs", _kulcsok())
def test_bitre_egyezik_az_emulalt_nativ_tablaval(kulcs):
    kapott = _resaturate_table(_szin(kulcs))
    vart = _vart(kulcs)
    elteres = np.nonzero((kapott != vart).any(axis=1))[0]
    assert elteres.size == 0, (
        f"{kulcs}: {elteres.size} eltérő sor, pl. "
        + ", ".join(f"L={i}: {kapott[i].tolist()} != {vart[i].tolist()}" for i in elteres[:3])
    )


def _elteres_sulyokkal(sulyok: tuple[float, float, float]) -> int:
    """Az eltérő táblasorok száma a teljes készleten, rontott súlyokkal."""
    eredeti = glimmer_ops._HAEBERLI_WEIGHTS
    glimmer_ops._HAEBERLI_WEIGHTS = sulyok
    glimmer_ops._resaturate_table.cache_clear()
    try:
        return sum(
            int((_resaturate_table(_szin(k)) != _vart(k)).any(axis=1).sum()) for k in _kulcsok()
        )
    finally:
        glimmer_ops._HAEBERLI_WEIGHTS = eredeti
        glimmer_ops._resaturate_table.cache_clear()


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("irany", [-1, 1])
def test_a_sulyok_utolso_jegyenek_rontasat_elkapja(index, irany):
    """Fog-ellenőrzés: egyetlen súly negyedik tizedesjegyének ±1-es
    elcsúszása a bitre egyező mércén már látszik."""
    rontott = list(glimmer_ops._HAEBERLI_WEIGHTS)
    rontott[index] = round(rontott[index] + irany * 0.0001, 4)
    assert _elteres_sulyokkal(tuple(rontott)) > 0


def test_a_golden_valoban_szinez():
    """Fog-ellenőrzés: a várt tábla nem a szürke azonosság."""
    vart = _vart("0x80cfff")
    azonossag = np.repeat(np.arange(256, dtype=np.uint8)[:, None], 3, axis=1)
    assert int((vart != azonossag).any(axis=1).sum()) > 200
