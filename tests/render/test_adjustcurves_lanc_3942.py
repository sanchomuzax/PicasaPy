"""#3942: az `AdjustCurves`-tábla két, eddig rögzítetlen részlete.

* a kerekítés `trunc(x + 0,5)` (nem `rint`, ami a ,5-ös döntetlent párosra
  kerekíti) — a mai görbéken egyetlen helyen látszik: Orton, `brightness=25`;
* a mestergörbe és a csatornagörbe KÖZÖTT nincs kerekítés és vágás — a
  Cinemascope táblája ezt rögzíti (a Sixties-t a saját tesztje fogja).
"""

from __future__ import annotations

import numpy as np

from picasapy.render.glimmer_creative import _CINEMA_BLUE, _CINEMA_MASTER, _CINEMA_RED
from picasapy.render.glimmer_ops import adjust_curves


def _tabla(**gorbek) -> np.ndarray:
    """A 256 bemenetre kapott kimenet csatornánként: alak `(256, 3)`."""
    szintek = np.arange(256, dtype=np.uint8)
    kep = np.repeat(szintek[None, :, None], 3, axis=2)
    return adjust_curves(kep, **gorbek)[0]


def test_a_felesre_eso_ertek_felfele_kerekul_nem_parosra():
    """Orton `brightness=25` → `mid = 128 + (25−50)·75/50 = 90,5`; a
    görbe a 128-as töréspontján pontosan 90,5 → `trunc(90,5 + 0,5) = 91`
    (a `rint` 90-et adna)."""
    tabla = _tabla(master=((0.0, 0.0), (128.0, 90.5), (255.0, 255.0)))
    assert tabla[128].tolist() == [91, 91, 91]


def test_a_kozepponti_felesre_esik_ket_pontos_gorbe_is_felfele_kerekul():
    """Kétpontos görbe `(0; 0,5)–(2; 1,5)` → a
    kimenet `0,5 / 1,0 / 1,5` → `trunc(+0,5)` = `1 / 1 / 2`."""
    tabla = _tabla(master=((0.0, 0.5), (2.0, 1.5)))
    assert tabla[:3, 0].tolist() == [1, 1, 2]


def test_a_cinemascope_tabla_nem_kerekit_a_mester_utan():
    """A köztes `rint` + vágás a mestergörbe után ezeken az elemeken
    eltérne (piros: 1, 3, 8, 9, 12; kék: 17, 23, 25, 40)."""
    tabla = _tabla(master=_CINEMA_MASTER, red=_CINEMA_RED, blue=_CINEMA_BLUE)
    assert tabla[[1, 3, 8, 9, 12], 0].tolist() == [1, 2, 6, 6, 9]
    assert tabla[[17, 23, 25, 40], 2].tolist() == [8, 11, 13, 26]
