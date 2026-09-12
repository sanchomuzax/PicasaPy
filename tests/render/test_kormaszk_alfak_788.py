"""A körmaszk `innerAlpha`/`outerAlpha`-ja és a „Fordított" jelölő (#788).

A `glimmer::CircularGradientImageMask` hét attribútumát és mind a hét
tartalék értékét a 283. kutatói kör kiolvasta
(`docs/specs/filters-decoded.md`, „MEGVAN a körmaszk MIND A HÉT tartalék
értéke"):

| attribútum | tartalék |
|---|---|
| `aspectRatio` | **1,0** ⇒ a maszk KÖR, nem ellipszis |
| `innerRadius` · `outerRadius` | `0,0` · `100,0` |
| `innerAlpha` · `outerAlpha` | `0,0` · `1,0` |
| `xCenter` · `yCenter` | `0,0` · `0,0` |

Az `innerAlpha`/`outerAlpha` ezen felül **`[0,1]`-re vágódik**
(`0x00bd0391`–`0x00bd03bd`, `0x00bd03e1`–`0x00bd040a`).

A `PicnikFocalPixelate` „Fordított" jelölője a `filterdesc.xml`-ben
**pontosan az alfák cseréje** (`filterdesc-registry.md`:342):
`outerAlpha = Reverse ? 0 : 1`, `innerAlpha = Reverse ? 1 : 0`.

⚠️ Az `aspectRatio` SZÁNDÉKOSAN nem lett paraméter: mérve mindig `1,0`, és
a nem 1,0-s eset geometriája NINCS kimérve — a paraméter csak találgatást
tudna hordozni.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.focal import apply_focal_pixelate, focal_mask
from picasapy.render.glimmer_ops import circular_gradient_mask


class TestFocalMaskAlfak:
    def test_az_alapertelmezes_a_mert_tartalek(self):
        """Alapból `innerAlpha = 0`, `outerAlpha = 1` — a mai viselkedés."""
        maszk = focal_mask(60, 90, 0.5, 0.5, radius=20.0, hardness=50.0)
        assert maszk.min() == pytest.approx(0.0, abs=1e-6)
        assert maszk.max() == pytest.approx(1.0, abs=1e-6)

    def test_forditott_alfak_tukorkepet_adnak(self):
        """`innerAlpha = 1`, `outerAlpha = 0`: pontosan `1 − maszk`."""
        alap = focal_mask(60, 90, 0.5, 0.5, radius=20.0, hardness=50.0)
        forditott = focal_mask(
            60, 90, 0.5, 0.5, radius=20.0, hardness=50.0,
            inner_alpha=1.0, outer_alpha=0.0,
        )
        assert np.allclose(forditott, 1.0 - alap, atol=1e-6)

    def test_az_alfak_a_tartomanyra_vagodnak(self):
        """A natív olvasó `[0,1]`-re vág (`0x00bd0391`, `0x00bd03e1`)."""
        maszk = focal_mask(
            40, 40, 0.5, 0.5, radius=10.0, hardness=50.0,
            inner_alpha=-3.0, outer_alpha=7.0,
        )
        assert maszk.min() >= 0.0 and maszk.max() <= 1.0

    def test_azonos_alfak_allando_maszkot_adnak(self):
        maszk = focal_mask(
            30, 30, 0.5, 0.5, radius=8.0, hardness=50.0,
            inner_alpha=0.25, outer_alpha=0.25,
        )
        assert np.allclose(maszk, 0.25, atol=1e-6)


class TestKormaszkAlfak:
    def test_alapertelmezes_valtozatlan(self):
        maszk = circular_gradient_mask(50, 70, 5.0, 25.0)
        assert maszk.min() == pytest.approx(0.0, abs=1e-6)
        assert maszk.max() == pytest.approx(1.0, abs=1e-6)

    def test_forditott_alfak(self):
        alap = circular_gradient_mask(50, 70, 5.0, 25.0)
        forditott = circular_gradient_mask(
            50, 70, 5.0, 25.0, inner_alpha=1.0, outer_alpha=0.0
        )
        assert np.allclose(forditott, 1.0 - alap, atol=1e-6)

    def test_elfajult_sugarnal_is_hat_az_alfa(self):
        """`outer <= inner`: kemény lépcső, de az alfák akkor is érvényesek."""
        maszk = circular_gradient_mask(
            20, 20, 10.0, 4.0, inner_alpha=0.2, outer_alpha=0.8
        )
        ertekek = sorted(float(v) for v in np.unique(maszk))
        assert len(ertekek) == 2
        assert ertekek[0] == pytest.approx(0.2, abs=1e-6)
        assert ertekek[1] == pytest.approx(0.8, abs=1e-6)


class TestFordítottJelolo:
    def _kep(self) -> np.ndarray:
        rng = np.random.default_rng(1725)
        return rng.integers(0, 256, size=(48, 64, 3), dtype=np.uint8)

    def test_forditva_a_kor_KOZEPE_pixeles(self):
        """`Reverse = 1`: a hatás a körön BELÜL jelentkezik.

        Alaphelyzetben a kör közepe marad éles és a kép nagy része
        pixeles (`filterdesc-registry.md`:332); fordítva épp ellenkezőleg.
        """
        kep = self._kep()
        alap = apply_focal_pixelate(
            kep, impact=8.0, radius=12.0, hardness=50.0
        )
        forditott = apply_focal_pixelate(
            kep, impact=8.0, radius=12.0, hardness=50.0, reverse=True
        )
        kozep = (slice(20, 28), slice(28, 36))
        sarok = (slice(0, 6), slice(0, 6))
        assert np.array_equal(alap[kozep], kep[kozep]), (
            "alaphelyzetben a kör közepének élesnek kell maradnia"
        )
        assert not np.array_equal(forditott[kozep], kep[kozep]), (
            "fordítva a kör közepét kell pixelesíteni"
        )
        assert np.array_equal(forditott[sarok], kep[sarok]), (
            "fordítva a saroknak érintetlennek kell maradnia"
        )
        assert not np.array_equal(alap[sarok], kep[sarok])

    def test_a_jelolo_alapbol_ki_van(self):
        kep = self._kep()
        assert np.array_equal(
            apply_focal_pixelate(kep, impact=8.0, radius=12.0),
            apply_focal_pixelate(kep, impact=8.0, radius=12.0, reverse=False),
        )
