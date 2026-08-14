"""#623: `linblur` („Lineáris homályosítás") — a natív `0x0090de10` mag.

**Nem mozgáshomály**, hanem ÁTMENETES (graduált) életlenítés: két pont ad
egy fókuszvonalat, és a köztük futó köbös B-spline súly keveri az elmosott
és az éles képet. A két pontot a burkoló (`0x008f99c0`) adja:

| pont | mi | hatás |
|---|---|---|
| `p1` | a korong (puck) helye | `t = +65536` → `alpha ≈ 250` → **éles** |
| `p0` | a kép közepe (`W>>1`, `H>>1`) | `t = −65536` → `alpha ≈ 5` → **homályos** |

Ld. `docs/specs/picasa-native-filter-workers.md` 3.3 és a #623 jegy
kutatási frissítése.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.iir_blur import apply_picasa_blur
from picasapy.render.linear_blur import (
    LINBLUR_TABLE_SIZE,
    apply_linblur,
    linblur_blur_radius,
    linblur_weight_table,
)


def _zajos(height: int = 60, width: int = 160) -> np.ndarray:
    rng = np.random.default_rng(3)
    return rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)


class TestWeightTable:
    """A 384 elemű köbös B-spline súlytábla (`t` 0-tól 1,5-ig, 1/256-onként).

    ```
    -0.5 < t <= 0.5  → f = 1/2 − (3t/4 − t³/3)
    t > 0.5          → f = 9/16 − (9t/8 + (t³/6 − 3t²/4))
    tábla[i] = (1 − 2f) · 255,9999
    ```
    """

    def test_a_tabla_merete(self) -> None:
        assert LINBLUR_TABLE_SIZE == 0x180
        assert len(linblur_weight_table()) == 0x180

    def test_a_kezdopont_nulla(self) -> None:
        """`t = 0` → `f = 1/2` → `1 − 2f = 0`: a fókuszvonalon a súly nulla,
        azaz félig elmosott, félig éles."""
        assert linblur_weight_table()[0] == 0

    def test_monoton_no(self) -> None:
        table = linblur_weight_table()
        assert np.all(np.diff(table) >= 0)

    def test_a_vegpontok_sulya(self) -> None:
        """A `t = 1` (idx = 256) a korong/közép helye: `f = 1/6·(1/2)³`,
        innen `tábla[256] = 245`, tehát `alpha = (245+255)/2 = 250` a korong
        és `(−245+255)/2 = 5` a közép felől — pontosan a jegyben leírt
        számok."""
        table = linblur_weight_table()
        assert table[256] == 245
        assert (table[256] + 255) // 2 == 250
        assert (-table[256] + 255) // 2 == 5

    def test_a_tabla_vege_255(self) -> None:
        """`t → 1,5` esetén `f → 0`, tehát a súly a 255-ös maximumra fut ki
        (a natív bájt-túlcsordulás nélkül, ld. a modul docstringjét)."""
        assert linblur_weight_table()[-1] == 255


class TestBlurRadius:
    def test_a_kepszelessegbol_szamol(self) -> None:
        """A testvér `radblur` burkolójának mintája:
        `sugár = szélesség/100 · (Mennyiség + 1) + 0,001` — KÖZELÍTÉS."""
        assert linblur_blur_radius(800, 2.0) == pytest.approx(24.001)
        assert linblur_blur_radius(1600, 0.0) == pytest.approx(16.001)


class TestApplyLinblur:
    def test_a_kozepre_tett_korong_azonossag(self) -> None:
        """A natív mag maga zárja ki: `if (p1 != p0)` — a csúszka
        alapállásában (0,5; 0,5) a kép VÁLTOZATLAN."""
        image = _zajos()
        assert np.array_equal(apply_linblur(image, 0.5, 0.5, 2.0), image)

    def test_a_bemenetet_nem_modositja(self) -> None:
        image = _zajos()
        eredeti = image.copy()
        apply_linblur(image, 0.75, 0.5, 2.0)
        assert np.array_equal(image, eredeti)

    def test_a_korong_feloli_oldal_eles_a_kozep_feloli_homalyos(self) -> None:
        image = _zajos()
        result = apply_linblur(image, 0.75, 0.5, 2.0).astype(float)
        original = image.astype(float)
        # helyi szórás: az éles oldalon marad, a homályos oldalon eltűnik
        eles_oldal = result[:, 140:].std()
        homalyos_oldal = result[:, :20].std()
        assert eles_oldal > 3.0 * homalyos_oldal
        assert eles_oldal == pytest.approx(original[:, 140:].std(), rel=0.05)

    def test_a_szakaszon_TUL_teljesen_eles(self) -> None:
        """`idx >= +384` → a mag a NYERS forrást írja (`*puVar9 = *local_1a8`).

        A korong (0,75·W) és a közép (0,5·W) felezőpontja 0,625·W, a
        fél-szakasz 0,125·W; az éles tartomány ezen 1,5-szeresével kezdődik,
        tehát `x >= 0,8125·W`.
        """
        image = _zajos()
        result = apply_linblur(image, 0.75, 0.5, 2.0)
        assert np.array_equal(result[:, 131:], image[:, 131:])

    def test_a_szakasz_ELOTT_teljesen_homalyos(self) -> None:
        """`idx <= −384` → a mag NEM ír: marad a helyben elmosott puffer.

        Az elmosás a közös IIR-mag KÉTSZER lefuttatva (a natív burkoló két
        egymás utáni `FUN_009dd0d0` hívása).
        """
        image = _zajos()
        radius = linblur_blur_radius(image.shape[1], 2.0)
        homalyos = apply_picasa_blur(
            apply_picasa_blur(image, radius, radius), radius, radius
        )
        result = apply_linblur(image, 0.75, 0.5, 2.0)
        assert np.array_equal(result[:, :70], homalyos[:, :70])

    def test_az_atmenet_monoton(self) -> None:
        """A két végpont között a köbös B-spline súly monoton nő, tehát a
        képpontok egyre közelebb kerülnek az élesekhez."""
        image = _zajos()
        result = apply_linblur(image, 0.75, 0.5, 2.0).astype(float)
        radius = linblur_blur_radius(image.shape[1], 2.0)
        homalyos = apply_picasa_blur(
            apply_picasa_blur(image, radius, radius), radius, radius
        ).astype(float)
        eltavolodas = np.abs(result - homalyos).mean(axis=(0, 2))
        # 10 képpontos ablakokban átlagolva a növekedés monoton
        ablakok = eltavolodas[:130].reshape(13, 10).mean(axis=1)
        assert np.all(np.diff(ablakok) >= 0)

    def test_a_fuggoleges_korong_fuggoleges_atmenetet_ad(self) -> None:
        """A fókuszvonal a korong és a közép ÖSSZEKÖTŐ egyenesére merőleges:
        függőlegesen eltolt koronggal a felső és az alsó sáv válik szét."""
        image = _zajos(height=160, width=60)
        result = apply_linblur(image, 0.5, 0.75, 2.0).astype(float)
        assert result[140:, :].std() > 3.0 * result[:20, :].std()

    def test_ervenytelen_bemenet(self) -> None:
        with pytest.raises(ValueError):
            apply_linblur(np.zeros((4, 4), dtype=np.uint8), 0.75, 0.5, 2.0)
