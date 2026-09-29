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
from picasapy.render.glimmer_ops import (
    _kormaszk_pozicio,
    _kormaszk_tavolsag,
    circular_gradient_mask,
)


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
        # #3958: a megálló-tábla csonkol és a keverés `>> 8`-cal oszt, ezért a
        # fordított rámpa nem tükrözi bitre az alapot — legfeljebb 2 szint.
        assert np.allclose(forditott, 1.0 - alap, atol=2.0 / 255.0)

    def test_elfajult_sugarnal_is_hat_az_alfa(self):
        """`outer <= inner`: kemény lépcső, de az alfák akkor is érvényesek."""
        maszk = circular_gradient_mask(
            20, 20, 10.0, 4.0, inner_alpha=0.2, outer_alpha=0.8
        )
        ertekek = sorted(float(v) for v in np.unique(maszk))
        assert len(ertekek) == 2
        assert ertekek[0] == pytest.approx(0.2, abs=1e-6)
        assert ertekek[1] == pytest.approx(0.8, abs=1e-6)


class TestKormaszkKepponkent3958:
    """#3958: 16 bites pozíció, egész koordináta, megálló-tábla (spec:
    „A körmaszk képpontonként”, #3957)."""

    @staticmethod
    def _bajt(y: int, x: int) -> int:
        maszk = circular_gradient_mask(640, 960, 240.0, 720.0)
        return int(np.rint(maszk[y, x] * 255.0))

    @pytest.mark.parametrize(
        ("x", "y", "alfa"),
        [(480, 320, 0), (0, 320, 127), (0, 0, 178), (100, 100, 105)],
    )
    def test_a_spec_peldai(self, x, y, alfa):
        assert self._bajt(y, x) == alfa

    @pytest.mark.parametrize(
        ("belso_alfa", "kulso_alfa"), [(0.0, 1.0), (0.3, 1.0), (1.0, 0.0)]
    )
    def test_kepponkent_egyezik_a_spec_szerinti_skalar_szamitassal(
        self, belso_alfa, kulso_alfa
    ):
        """Független, egész aritmetikás modell a spec képletéből: egész
        koordináta, 16 bites (LEGKÖZELEBBRE kerekített), float32-ben számolt
        pozíció, csonkolt megálló-tábla (fordított alfára is). Lebegőpontos
        pozíció vagy `+0,5` képpontközép, csonkolt pozíció itt pirosat ad."""
        f32 = np.float32
        h, w, inner, outer = 40, 60, 15.0, 45.0
        a0 = int(255 * belso_alfa)
        a1 = int(255 * kulso_alfa)
        p1 = int(255 * inner / outer)
        tabla = [a0] * 257
        for i in range(p1, 255):
            tort = float(f32((i - p1) / (255 - p1)))
            tabla[i] = int(a0 + (a1 - a0) * tort)
        tabla[255] = tabla[256] = a1
        maszk = circular_gradient_mask(
            h, w, inner, outer, inner_alpha=belso_alfa, outer_alpha=kulso_alfa
        )
        for y in range(h):
            for x in range(w):
                u = f32((x - w / 2.0) * 65280 / outer)
                v = f32((y - h / 2.0) * 65280 / outer)
                pozicio = min(int(np.rint(np.sqrt(u * u + v * v))), 0xFF00)
                i, f = pozicio >> 8, pozicio & 0xFF
                alfa = (tabla[i + 1] * f + tabla[i] * (256 - f)) >> 8
                assert round(float(maszk[y, x]) * 255.0) == alfa, (x, y)

    def test_a_gyok_egyszeres_pontossagu(self):
        """A spec: `sqrtps` (float32). A (0, 320) képpontban `u = −43 520`,
        `v = 0`, így `√ = 43 520`, `P = 43 520`; a float32-es köztes érték
        float32 típusú. (A spec `43 519,996`-ja az `u` más alakjából jön —
        az `u`/`v` alakja nem rögzített, ld. a docstringet.)"""
        tavolsag = _kormaszk_tavolsag(640, 960, 480.0, 320.0, 720.0)
        assert tavolsag.dtype == np.float32
        assert float(tavolsag[320, 0]) == pytest.approx(43520.0, abs=0.01)
        assert _kormaszk_pozicio(640, 960, 480.0, 320.0, 720.0)[320, 0] == int(
            np.rint(tavolsag[320, 0])
        )

    def test_a_pozicio_a_float32_gyok_kerekitese_nem_a_float64e(self):
        """A (347, 0) és (613, 0) képpontban a float32-es és a float64-es
        `√` MÁS egészre kerekít; a kód a float32-eset adja. Float64-es `√`-nél
        ez piros."""
        u = ((np.arange(960) - 480.0) * (65280 / 720.0)).astype(np.float32)
        v = ((np.arange(640) - 320.0) * (65280 / 720.0)).astype(np.float32)
        p32 = np.rint(np.sqrt(v[:, None] * v[:, None] + u[None, :] * u[None, :]))
        u64, v64 = u.astype(np.float64), v.astype(np.float64)
        p64 = np.rint(np.sqrt(v64[:, None] ** 2 + u64[None, :] ** 2))
        kulonbseg = p32 != p64
        assert kulonbseg.any()
        pozicio = _kormaszk_pozicio(640, 960, 480.0, 320.0, 720.0)
        assert np.array_equal(pozicio[kulonbseg], p32[kulonbseg].astype(np.int64))
        assert not np.array_equal(pozicio[kulonbseg], p64[kulonbseg].astype(np.int64))

    def test_egesz_bajtra_esik_a_maszk(self):
        maszk = circular_gradient_mask(64, 96, 24.0, 72.0)
        assert np.array_equal(maszk, np.rint(maszk * 255.0) / 255.0)


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
