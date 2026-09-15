"""#3110: a `linblur` sugara a korong X koordinátája, nem állandó.

## A mérés

`docs/specs/filters-decoded.md` → „⛳ A `linblur` NEM érhető el a
felületről…" (a #2772 303. köre):

- a feldolgozó (`0x008f99c0`) `fld st(0)` másolata a két `ftol` után az
  FPU-verem tetején marad, és a `0x008f9a40 fstp dword [esp]` ezt teszi a
  natív mag harmadik veremargumentumába — vagyis **a korong X-ét**;
- a mag (`0x0090de10`) betölti (`0x0090de9b`), és **mindkét** `0x009dd0d0`
  IIR-hívásnak ugyanazt adja át (`0x0090dec6`, `0x0090def6`);
- a „Mennyiség" csúszkát a feldolgozó **sehol nem olvassa** — a #2736
  mérésének kódoldali igazolása.

## Miért nem látszik a referencián

Mind a **három** referencia-láncunk `x = 0,5`
(`linblur=1,0.5,0.5,{2,10,0}`), tehát a korong X-e ott épp egyenlő a
korábbi állandóval (`LINBLUR_MERT_SUGAR = 0,5`). A csere a referencián
ezért **mérhetően semleges** — a különbség csak más korong-állásokon
jelentkezik, amire nincs exportunk. Ezt a lap ki is mondja: a `0,5`-ös
egyezés nem bizonyíték az `x`-függésre, a bizonyíték a binárisból jön.

⚠️ **Amit ez a lap NEM mér:** a negatív X-et. A `filters=` érték a #2702
szerint `[-1, +1]`-ben áll, a natív együttható-képlet
(`trunc((1 − 0,1^(1/R))·32767)`) negatív sugárra nem értelmes, és
referencia sincs rá. A mi elmosónk `radius > 0` esetén mos, tehát negatív
értéknél nem mos — ezt a viselkedést a lap **rögzíti**, de nem állítja,
hogy az eredeti ezt teszi.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.linear_blur import apply_linblur, linblur_blur_radius


def _minta(meret: int = 64) -> np.ndarray:
    generator = np.random.default_rng(3110)
    return generator.integers(0, 256, size=(meret, meret, 3), dtype=np.uint8)


class TestASugarAKorongXe:
    @pytest.mark.parametrize("x", [0.0, 0.25, 0.5, 0.75, 1.0])
    def test_a_sugar_egyenlo_az_X_szel(self, x: float) -> None:
        assert linblur_blur_radius(960, x, 2.0) == pytest.approx(x)

    @pytest.mark.parametrize("amount", [0.0, 2.0, 10.0, 1000.0, -5.0])
    def test_a_mennyiseg_tovabbra_sem_hat(self, amount: float) -> None:
        """A #2736 mérése változatlanul áll — a csere nem vezet be függést."""
        assert linblur_blur_radius(960, 0.5, amount) == pytest.approx(0.5)

    def test_a_szelessegtol_sem_fugg(self) -> None:
        assert linblur_blur_radius(120, 0.5, 2.0) == linblur_blur_radius(
            4000, 0.5, 2.0
        )

    def test_a_referencia_allasan_valtozatlan(self) -> None:
        """A KONTROLL: `x = 0,5`-nél a mért sugár egyezik a régi állandóval,
        tehát a referencia-ΔE nem változhat."""
        assert linblur_blur_radius(960, 0.5, 2.0) == pytest.approx(0.5)


class TestAKimenetAKorongtolFugg:
    def test_kisebb_X_kevesebbet_mos(self) -> None:
        """A sugár-függés a KIMENETEN is látszódjon — enélkül a próba csak
        egy visszaadott számot mér."""
        kep = _minta()
        #: ugyanaz az y, hogy a korong-közép viszony (és így a vetület)
        #: mindkét futásban azonos legyen — csak a sugár térjen el
        kicsi = apply_linblur(kep, 0.2, 0.9, 2.0)
        nagy = apply_linblur(kep, 0.9, 0.9, 2.0)
        assert not np.array_equal(kicsi, nagy), (
            "a korong X-e nem hat a kimenetre"
        )

    def test_nulla_X_nem_mos(self) -> None:
        """A mért alak következménye: `x = 0`-nál a sugár 0, tehát nincs
        elmosás — az elmosott és az éles puffer egybeesik.

        ⚠️ Ez KÖVETKEZTETÉS a mért alakból, nem önálló mérés: referencia
        `x = 0`-ra nincs. A lap azért állítja, hogy a viselkedés ne
        csússzon el némán."""
        kep = _minta()
        eredmeny = apply_linblur(kep, 0.0, 0.9, 2.0)
        assert np.array_equal(eredmeny, kep), (
            "nulla sugárnál a kimenet nem a változatlan kép"
        )

    def test_negativ_X_sem_mos(self) -> None:
        """A `[-1, +1]`-es tartomány negatív fele: a mi elmosónk `radius > 0`
        esetén mos, tehát itt nem. Rögzített viselkedés, nem mért állítás."""
        kep = _minta()
        eredmeny = apply_linblur(kep, -0.5, 0.9, 2.0)
        assert np.array_equal(eredmeny, kep)
