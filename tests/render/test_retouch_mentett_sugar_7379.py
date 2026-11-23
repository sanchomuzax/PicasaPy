"""#7379: az ecset-osztó módosítása nem érinti a már elmentett retusált képeket.

A `.picasa.ini` foltja a sugarat a kép rövidebb oldalához mért RELATÍV értékként
tárolja (`retouch=2,<patch>`), nem csúszkaértékként; a renderelő ezt a tárolt
értéket használja, az ecset-osztót (`_BRUSH_SIZE_TO_RELATIVE_DIVISOR`) csak az
ÚJ folt létrehozásakor a vezérlő alkalmazza. Ez a teszt számol és képpontot
hasonlít (nem lát): a mentett kép renderelésének változatlanságát bizonyítja, a
kinézetét nem.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.retouch import (
    RetouchPatch,
    build_retouch_patches_op,
    decode_patch,
    encode_patch,
)
from picasapy.render.chain_ops import _apply_retouch_op

#: A korábbi osztóval (1000) írt folt: 60 egységnyi csúszkaállás -> 0,06 relatív sugár
#: (a 120 képpontos próbaképen 7 képpont; 2 képpontos körnél a klónozás nem módosít semmit).
_RÉGI_OSZTÓ = 1000.0
_RÉGI_CSÚSZKA = 60


def _próbakép() -> np.ndarray:
    # Egyenetlen, de determinisztikus tartalom: a klónozás látható változást ad.
    rng = np.random.default_rng(7)
    return rng.integers(0, 256, size=(120, 160, 3), dtype=np.uint8)


def _régi_folt() -> RetouchPatch:
    return RetouchPatch(
        target_x=0.3,
        target_y=0.5,
        source_x=0.7,
        source_y=0.5,
        radius=_RÉGI_CSÚSZKA / _RÉGI_OSZTÓ,
    )


def test_mentett_folt_sugara_relativ_ertekkent_tarolodik() -> None:
    folt = _régi_folt()
    visszaolvasott = decode_patch(encode_patch(folt))
    assert visszaolvasott.radius == pytest.approx(0.06, abs=1.0 / 65536)


@pytest.mark.parametrize("uj_oszto", (494.0, 250.0, 2000.0))
def test_a_mentett_folt_renderelese_nem_fugg_az_ecset_osztotol(
    monkeypatch: pytest.MonkeyPatch, uj_oszto: float
) -> None:
    kep = _próbakép()
    op = build_retouch_patches_op((_régi_folt(),))
    regi = _apply_retouch_op(kep, op)
    # a próba nem üres: a folt tényleg módosít képpontokat
    assert int(np.count_nonzero(regi != kep)) > 0

    from picasapy.app import edit_controller_retouch_mixin, edit_controller_shared

    monkeypatch.setattr(edit_controller_shared, "_BRUSH_SIZE_TO_RELATIVE_DIVISOR", uj_oszto)
    monkeypatch.setattr(edit_controller_retouch_mixin, "_BRUSH_SIZE_TO_RELATIVE_DIVISOR", uj_oszto)

    uj = _apply_retouch_op(kep, op)
    assert np.array_equal(regi, uj)


def test_a_renderelo_nem_importalja_az_ecset_osztot() -> None:
    import picasapy.render.chain_ops as lanc
    import picasapy.render.retouch as retus

    for modul in (lanc, retus):
        assert not hasattr(modul, "_BRUSH_SIZE_TO_RELATIVE_DIVISOR")
        assert not hasattr(modul, "_DEFAULT_BRUSH_SIZE")
