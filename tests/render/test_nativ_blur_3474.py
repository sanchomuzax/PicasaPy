"""#3474: a natív `DropShadow`-elmosás (`0x00bc5680`, skalár ág) bitre pontosan.

A golden-készlet (`tests/support/native_filter_reference/nativ_blur_3474.json`)
a `Picasa3.exe` natív kódjának unicorn-emulátorban futtatott KIMENETE — nem
a mi modellünkből számolt érték. A CI-n nincs unicorn, ezért a teszt csak a
rögzített bájtokat hasonlítja; az eltérő bájtok száma mindenhol 0 kell legyen.

A készlet lefedi a tört súlyú (`k > 0`) ágat, a tengelyenként eltérő és a
fél képméretre vágott sugarat, valamint az `n ≥ 64`-es, `ceilf`-es ágat
(`0x00bc539d`; egy `floor`-os változat itt keskenyebb dobozt adna: h = 35 a 36 helyett).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

from picasapy.render.nativ_blur import (
    nativ_blur_bgra,
    nativ_blur_csatorna,
    sugar_egyutthatok,
)

_GOLDEN = (
    Path(__file__).resolve().parents[1]
    / "support"
    / "native_filter_reference"
    / "nativ_blur_3474.json"
)


@lru_cache(maxsize=1)
def _adat() -> dict:
    return json.loads(_GOLDEN.read_text(encoding="utf-8"))


def _kep(eset: dict, kulcs: str) -> np.ndarray:
    nyers = np.frombuffer(bytes.fromhex(eset[kulcs]), dtype=np.uint8)
    return nyers.reshape(eset["magas"], eset["szeles"], 4)


def _esetek() -> list[dict]:
    return _adat()["esetek"]


@pytest.mark.parametrize("eset", _esetek(), ids=lambda e: e["nev"])
def test_bitre_egyezik_az_emulalt_nativ_kimenettel(eset):
    be = _kep(eset, "be_hex")
    vart = _kep(eset, "ki_hex")
    kapott = nativ_blur_bgra(be, eset["sugar_x"], eset["sugar_y"], eset["quality"])
    assert kapott.dtype == np.uint8
    assert int(np.count_nonzero(kapott != vart)) == 0


def test_a_golden_valoban_elmos():
    """Fog-ellenőrzés: a várt kimenet nem a bemenet másolata."""
    for eset in _esetek():
        assert int(np.count_nonzero(_kep(eset, "be_hex") != _kep(eset, "ki_hex"))) > 0


@pytest.mark.parametrize("sor", _adat()["egyutthatok"], ids=lambda s: f"r={s['sugar']}")
def test_egyutthatok_a_0x00bc5360_szerint(sor):
    assert list(sugar_egyutthatok(sor["sugar"])) == sor["k_h_w_oszto"]


def test_az_oszto_a_sulyok_osszege():
    """`osztó = (2h−1)·2^k + 2w` — ettől marad az állandó szín állandó."""
    for sor in _adat()["egyutthatok"]:
        k, h, w, oszto = sor["k_h_w_oszto"]
        if sor["sugar"] > 1.0:
            assert oszto == (2 * h - 1) * (1 << k) + 2 * w


def test_allando_szin_valtozatlan_marad():
    """A `DropShadow` rétegén az RGB mindenhol az árnyékszín — a blur nem mozdítja."""
    kep = np.zeros((20, 30, 4), np.uint8)
    kep[..., :3] = (17, 128, 250)
    kep[5:15, 8:22, 3] = 255
    ki = nativ_blur_bgra(kep, 6.5, 6.5, 3)
    assert np.array_equal(ki[..., :3], kep[..., :3])
    assert not np.array_equal(ki[..., 3], kep[..., 3])


def test_egy_csatorna_ugyanaz_mint_a_negy():
    eset = _esetek()[3]
    be = _kep(eset, "be_hex")
    teljes = nativ_blur_bgra(be, eset["sugar_x"], eset["sugar_y"], 3)
    for c in range(4):
        egy = nativ_blur_csatorna(
            np.ascontiguousarray(be[..., c]), eset["sugar_x"], eset["sugar_y"], 3
        )
        assert np.array_equal(egy, teljes[..., c])


@pytest.mark.parametrize("rx, ry", [(1.0, 1.0), (0.5, 0.0), (-3.0, 1.0)])
def test_egy_alatti_sugar_masol(rx, ry):
    kep = _kep(_esetek()[0], "be_hex")
    assert np.array_equal(nativ_blur_bgra(kep, rx, ry, 3), kep)


def test_hibas_bemenet():
    with pytest.raises(ValueError):
        nativ_blur_bgra(np.zeros((4, 4, 3), np.uint8), 2.0, 2.0)
    with pytest.raises(ValueError):
        nativ_blur_csatorna(np.zeros((4, 4), np.float32), 2.0, 2.0)
