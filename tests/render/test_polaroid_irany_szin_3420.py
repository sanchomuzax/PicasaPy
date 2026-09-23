"""#3420: a Polaroid forgatási IRÁNYA és a képkeret SZÍNE az eredeti szerint.

A 684-es golden-készlet (`\\\\DS215j\\lemez\\My Pictures\\684-merokeszlet`)
három Polaroid-exportja mellett a renderünk ΔE-je 18,7–22,7 volt, pedig a
kimenet mérete képpontra egyezett (#1144). Az egymás melletti kép két
szerkezeti eltérést mutatott, és a szállított `filterdesc.xml` mindkettőt
kimondja:

1. `SimpleBorderImageOperation ... color="0xffffff"` — a képkeret FEHÉR; a
   paraméter színe (`_cpkrOuter`, alap `E2E2E2`) csak az árnyék hátterére és
   a forgatás kitöltésére megy.
2. `RotateImageOperation degAngle="{_sldrRotate.value}"` — a Picasa pozitív
   szöge az óramutató JÁRÁSA szerint dönt (az exporton `Rotate = 5`-nél a
   keret felső éle jobbra LEJT); az OpenCV pozitív szöge fordítva forgat.

⚠️ A golden-képek a NAS-on vannak, ezért ez a próba szintetikus képen méri
a két szerkezeti tulajdonságot; a golden-ΔE a PR-ben áll.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.glimmer_frames import apply_polaroid

HATTER = (0xE2, 0xE2, 0xE2)


def _kep() -> np.ndarray:
    # sötét, egyszínű fénykép — a fehér keret így egyértelműen elválik tőle
    return np.full((400, 600, 3), 40, dtype=np.uint8)


def _felso_feher_sor(kep: np.ndarray, oszlop: int) -> int:
    """Az adott oszlop első TISZTA fehér képpontjának sora (a keret teteje)."""
    feher = np.all(kep[:, oszlop] >= 250, axis=-1)
    sorok = np.flatnonzero(feher)
    assert sorok.size, f"a(z) {oszlop}. oszlopban nincs fehér keret"
    return int(sorok[0])


class TestKeretSzin:
    def test_a_kepkeret_feher_a_hatter_a_megadott_szin(self):
        ki = apply_polaroid(_kep(), 0.0, HATTER)
        h, w = ki.shape[:2]
        # a felirat-sáv közepe: a keret alsó, széles része
        assert tuple(int(c) for c in ki[int(h * 0.85), w // 2]) == (255, 255, 255)
        # a vászon sarka: a háttér (árnyék-margó)
        assert tuple(int(c) for c in ki[0, 0]) == HATTER

    def test_a_szin_parameter_nem_festi_at_a_keretet(self):
        ki = apply_polaroid(_kep(), 0.0, (0x20, 0x40, 0x80))
        h, w = ki.shape[:2]
        assert tuple(int(c) for c in ki[int(h * 0.85), w // 2]) == (255, 255, 255)


class TestForgatasIranya:
    @pytest.mark.parametrize("szog", [5.0, 10.0])
    def test_pozitiv_szognel_a_felso_el_jobbra_lejt(self, szog):
        ki = apply_polaroid(_kep(), szog, HATTER)
        w = ki.shape[1]
        bal, jobb = _felso_feher_sor(ki, w // 3), _felso_feher_sor(ki, 2 * w // 3)
        assert jobb > bal, (bal, jobb)

    def test_negativ_szognel_jobbra_emelkedik(self):
        ki = apply_polaroid(_kep(), -10.0, HATTER)
        w = ki.shape[1]
        bal, jobb = _felso_feher_sor(ki, w // 3), _felso_feher_sor(ki, 2 * w // 3)
        assert jobb < bal, (bal, jobb)
