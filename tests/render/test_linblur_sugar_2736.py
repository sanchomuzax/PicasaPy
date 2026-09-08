"""#2736: a linblur elmosási sugara — a „Mennyiség" NEM hat rá.

## A mérés, ami eldöntötte

A mérőszett három `linblur` referenciája (`/mnt/nas/My Pictures/PicasaPy
meroszett/`) UGYANARRÓL a forrásképről készült, és a láncuk csak a negyedik
paraméterben tér el:

```
linblur=1,0.5,0.5,2.0     (alap)
linblur=1,0.5,0.5,10.0    (max)
linblur=1,0.5,0.5,0.0     (min)
```

A valódi windowsos Picasa három kimenete **bitre azonos** (max eltérés 0,
átlag 0,000), miközben a forrástól mindhárom láthatóan eltér (átlag 12,21)
— tehát a szűrő lefutott, csak a „Mennyiség" **nem hat rá**.

A binárisban ugyanez: a burkoló (`0x008f99c0`) egyetlen lebegőpontos
argumentumot ad a magnak (`0x0090de10`, `fstp dword [esp]` a
`call 0x0090de10` előtt), a mag pedig azt továbbadja a közös elmosónak
(`0x009dd0d0`, `0x0090dec6` és `0x0090def6`, mindkét tengelyre ugyanazt).
A negyedik lánc-érték ebbe a láncba nem kerül be.

## A sugár MÉRT értéke

A saját (`iir_blur`) paraméterezésünkben a referenciát **1,5** adja vissza:

| eset | ΔE a mai képlettel (`szélesség/100·(Mennyiség+1)`) | ΔE 1,5-tel |
|---|---:|---:|
| alap (2,0) | 13,147 | **0,279** |
| max (10,0) | 17,849 | **0,279** |
| min (0,0) | 6,814 | **0,279** |

A 0,279 a JPEG-zaj nagyságrendje.

⛔ **A HATÓKÖR kimondva:** a mérés EGY korong-álláson (`0,5; 0,5`) készült,
mert csak ehhez van referencia-exportunk. Az tehát MÉRVE van, hogy a
„Mennyiség" nem hat, és hogy ezen az álláson 1,5 a sugár; az NINCS mérve,
hogy a sugár függ-e a korong helyétől. Amíg második referencia-pont nincs,
a konstans a minimális állítás — egy `1+|x|` alakú képlet ugyanezt az egy
pontot találná el, de olyan függést állítana, amire nincs bizonyíték.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.linear_blur import (
    LINBLUR_MERT_SUGAR,
    apply_linblur,
    linblur_blur_radius,
)


def _minta(meret: int = 48) -> np.ndarray:
    """Nem konstans kép — konstans képen minden sugár ugyanazt adná."""
    generator = np.random.default_rng(2736)
    return generator.integers(0, 256, size=(meret, meret, 3), dtype=np.uint8)


class TestASugarNemFuggAMennyisegtol:
    @pytest.mark.parametrize("amount", [0.0, 2.0, 10.0, 1000.0, -5.0])
    def test_a_sugar_minden_mennyisegre_ugyanaz(self, amount: float) -> None:
        assert linblur_blur_radius(960, amount) == LINBLUR_MERT_SUGAR

    def test_a_sugar_a_szelessegtol_sem_fugg(self) -> None:
        """A mai képlet a szélességgel skálázott; a mérés ezt sem támogatja."""
        assert linblur_blur_radius(120, 2.0) == linblur_blur_radius(4000, 2.0)

    def test_a_kimenet_azonos_harom_mennyisegre(self) -> None:
        """A referencia-exportok bitre azonosak — a mi kimenetünk is legyen az."""
        kep = _minta()
        alap = apply_linblur(kep, 0.5, 0.5, 2.0)
        maximum = apply_linblur(kep, 0.5, 0.5, 10.0)
        minimum = apply_linblur(kep, 0.5, 0.5, 0.0)
        assert np.array_equal(alap, maximum)
        assert np.array_equal(alap, minimum)

    def test_a_mert_sugar_erteke(self) -> None:
        """A szám maga is őrizve: elírás vagy „finomhangolás" ne menjen át
        némán, mert a 0,279-es ΔE ehhez az egy értékhez tartozik."""
        assert LINBLUR_MERT_SUGAR == 1.5


class TestAHatasMegvan:
    def test_az_effekt_tovabbra_is_elmos(self) -> None:
        """A sugár 28,8-ról 1,5-re csökkent — az effektnek MEGMARAD a hatása
        (a korong felőli oldal éles, a közép felőli homályos)."""
        kep = _minta(64)
        eredmeny = apply_linblur(kep, 0.5, 0.5, 2.0)
        assert not np.array_equal(eredmeny, kep), "a szűrő nem tett semmit"

        def elesseg(sav: np.ndarray) -> float:
            szurke = sav.mean(axis=2)
            return float(np.abs(np.diff(szurke, axis=1)).mean())

        bal = elesseg(eredmeny[:, :16])
        jobb = elesseg(eredmeny[:, -16:])
        assert jobb > bal, (
            "a korong (0,75 W) felőli, JOBB oldalnak élesebbnek kell lennie "
            f"(bal={bal:.2f}, jobb={jobb:.2f})"
        )
