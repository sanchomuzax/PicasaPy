"""#958: a `finetune` (v1) színhőmérséklete a SAJÁT natív workerét kapja.

## A lelet

A v1 és a v2 ugyanazt a négy csúszkát adja, de a színhőmérséklet
**két külön natív függvény**: a v2 a `0x0090e9d0`-t (feketetest-tábla +
3×3-as mátrix), a v1 a **`0x0090ea10`**-et (középtónus-parabolás worker,
ugyanaz, ami a `colortemp` szűrőé).

⛔ A „a v1 ugyanaz a görbe kétszeres skálán" hipotézis **MEGDŐLT**
(`filters-decoded.md`): a golden-eltérés 15,82 lett volna ~0 helyett.

## A MÉRT v1 képlet (`filters-decoded.md`, „A `finetune` v1 színága")

```c
t = trunc(temperature * 256.0);       // 0x0090ead6, konstans 0x00cf39d8
t_green = (t >= 1) ? t : 0;
r2 = clamp(r + (r * (256 - r) * t >> 15));
g2 = clamp(g + (g * (256 - g) * t_green >> 17));
b2 = clamp(b - (b * (256 - b) * t >> 15));
```

A v1 a worker fehérváltás-argumentumába **mindkét ágon 0,0**-t tesz
(`fldz`, `0x008f7e3e` és `0x008f7e67`), és a semlegesítő menet
**KÜLÖN képpontmenet** — a kettő között megmarad a 8 bites kvantálás,
tehát nem vonhatók össze egyetlen lebegőpontos menetté
(`push esi; push esi`, `0x008f7e4e`).

⭐ **A csonkolás NULLA FELÉ történik** (`cvttsd2si`, `0x00c299a5`) — ez
NEM ugyanaz, mint a v2 `0x0090e9d0`-ének legközelebbi-egészre kerekítése
(az a #956 helyesbítése). A két út rounding-ja szándékosan különbözik.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.native_colortemp import apply_native_colortemp
from picasapy.render.tone import apply_finetune2


def _proba_kep() -> np.ndarray:
    """Középtónus-gazdag próbakép — a parabola ott hat a legjobban."""
    sor = np.linspace(0, 255, 64, dtype=np.uint8)
    racs = np.stack(np.meshgrid(sor, sor), axis=-1)
    return np.stack(
        [racs[..., 0], racs[..., 1], (racs[..., 0] // 2 + racs[..., 1] // 2)],
        axis=-1,
    ).astype(np.uint8)


class TestAWorkerCsonkolasa:
    """A skálázás NULLA FELÉ csonkol, nem kerekít (`cvttsd2si`)."""

    def test_a_tort_lepes_LEFELE_csonkol(self):
        kep = _proba_kep()
        # 0,4/256 → 102,4 lépés: csonkolva 102, kerekítve 102 — egyezik.
        # 0,400391 × 256 = 102,5 → csonkolva 102, kerekítve 102 (bankár) …
        # a tiszta eset: 0,402344 × 256 = 103,0 pontosan; alatta 102,99…
        alatta = apply_native_colortemp(kep, 102.99 / 256.0, 0.0)
        pontos = apply_native_colortemp(kep, 102.0 / 256.0, 0.0)
        assert np.array_equal(alatta, pontos), (
            "a 102,99 lépés nem 102-re csonkolódott — kerekítés maradt"
        )

    def test_a_NEGATIV_oldal_is_nulla_fele_csonkol(self):
        kep = _proba_kep()
        felette = apply_native_colortemp(kep, -102.99 / 256.0, 0.0)
        pontos = apply_native_colortemp(kep, -102.0 / 256.0, 0.0)
        assert np.array_equal(felette, pontos), (
            "a −102,99 lépés nem −102-re csonkolódott (nulla FELÉ)"
        )

    def test_a_nulla_kozeli_ertek_no_op(self):
        kep = _proba_kep()
        assert np.array_equal(apply_native_colortemp(kep, 0.9 / 256.0, 0.0), kep)


class TestALancBekotese:
    """A v1 a natív workert kapja, a v2 változatlanul a sajátját."""

    def test_a_v1_NEM_a_v2_modelljet_futtatja(self):
        kep = _proba_kep()
        v1, _ = apply_filters(kep, parse_filters("finetune=1,0.0,0.0,0.0,00000000,0.500000;"))
        v2, _ = apply_filters(kep, parse_filters("finetune2=1,0.0,0.0,0.0,00000000,0.500000;"))
        assert not np.array_equal(v1, v2), (
            "a v1 és a v2 azonos kimenetet ad — a közös út maradt"
        )

    def test_a_v1_a_MERT_workert_futtatja(self):
        kep = _proba_kep()
        v1, _ = apply_filters(kep, parse_filters("finetune=1,0.0,0.0,0.0,00000000,0.500000;"))
        vart = apply_native_colortemp(kep, 0.5, 0.0)
        assert np.array_equal(v1, vart)

    def test_a_v1_a_semlegesito_UTAN_futtatja(self):
        """Két külön képpontmenet — a semlegesítő 8 bites kimenetére."""
        kep = _proba_kep()
        v1, _ = apply_filters(
            kep, parse_filters("finetune=1,0.300000,0.0,0.0,00000000,0.500000;")
        )
        kozbenso = apply_finetune2(
            kep, fill=0.3, highlights=0.0, shadows=0.0,
            neutral=None, temperature=0.0,
        )
        assert np.array_equal(v1, apply_native_colortemp(kozbenso, 0.5, 0.0))

    def test_a_TOBBI_csuszka_valtozatlanul_kozos(self):
        """#879: a Derítőfény/Csúcsfények/Árnyékok ág AZONOS a két verzióban."""
        kep = _proba_kep()
        v1, _ = apply_filters(kep, parse_filters("finetune=1,0.400000,0.200000,0.100000,00000000,0.000000;"))
        v2, _ = apply_filters(kep, parse_filters("finetune2=1,0.400000,0.200000,0.100000,00000000,0.000000;"))
        assert np.array_equal(v1, v2)

    def test_semleges_homerseklet_nem_valtoztat(self):
        kep = _proba_kep()
        v1, _ = apply_filters(kep, parse_filters("finetune=1,0.0,0.0,0.0,00000000,0.000000;"))
        assert np.array_equal(v1, kep)

    @pytest.mark.parametrize("homerseklet", ["0.5", "-0.5", "0.25", "-0.25"])
    def test_a_v1_a_sajat_tengelyen_hat(self, homerseklet):
        """A v1 tengelye `[−0,5 … +0,5]` — mind a négy álláson VÁLTOZIK."""
        kep = _proba_kep()
        v1, _ = apply_filters(
            kep, parse_filters(f"finetune=1,0.0,0.0,0.0,00000000,{homerseklet};")
        )
        assert not np.array_equal(v1, kep)


class TestAKepletFUGGETLEN_ujraszamolasa:
    """A termékkód a `native_colortemp` workert hívja; ez a próba a MÉRT
    képletet **önállóan** számolja újra, és a kettőt veti össze.

    ⚠️ Ez a formulát őrzi, nem a látható egyezést az eredetivel. A
    golden-egyezés (négy pár, átlagos ΔE76 **0,3940 … 0,6585**, a határ
    0,67) a gitignore-olt `research/testdata/PicasaPy-merokit` készleten
    mérve, a PR-ban rögzítve — a CI-n nem futhat.
    """

    @staticmethod
    def _mert_keplet(kep: np.ndarray, homerseklet: float) -> np.ndarray:
        t = int(homerseklet * 256.0)  # trunc, nulla felé (`cvttsd2si`)
        t_green = t if t >= 1 else 0
        ertek = kep.astype(np.int64)
        r, g, b = ertek[..., 0], ertek[..., 1], ertek[..., 2]
        return np.stack(
            [
                np.clip(r + ((r * (256 - r) * t) >> 15), 0, 255),
                np.clip(g + ((g * (256 - g) * t_green) >> 17), 0, 255),
                np.clip(b - ((b * (256 - b) * t) >> 15), 0, 255),
            ],
            axis=-1,
        ).astype(np.uint8)

    @pytest.mark.parametrize("homerseklet", [0.5, -0.5, 0.25, -0.25, 0.1])
    def test_a_lanc_a_MERT_kepletet_adja(self, homerseklet):
        kep = _proba_kep()
        lanc, kihagyott = apply_filters(
            kep,
            parse_filters(
                f"finetune=1,0.000000,0.000000,0.000000,00000000,{homerseklet:.6f};"
            ),
        )
        assert kihagyott == ()
        assert np.array_equal(lanc, self._mert_keplet(kep, homerseklet))

    def test_a_ZOLD_csak_melegiteskor_mozdul(self):
        """`t_green = (t >= 1) ? t : 0` — hűtéskor a zöld érintetlen."""
        kep = _proba_kep()
        hutve, _ = apply_filters(
            kep,
            parse_filters("finetune=1,0.000000,0.000000,0.000000,00000000,-0.500000;"),
        )
        assert np.array_equal(hutve[..., 1], kep[..., 1]), (
            "hűtéskor a zöld csatorna elmozdult"
        )

    def test_a_szelso_ertekek_ERINTETLENEK(self):
        """Középtónus-súlyozás: `P[0] = P[256] = 0` — a fekete és a fehér áll."""
        kep = np.zeros((2, 2, 3), dtype=np.uint8)
        kep[0, 0] = 0
        kep[0, 1] = 255
        eredmeny, _ = apply_filters(
            kep,
            parse_filters("finetune=1,0.000000,0.000000,0.000000,00000000,0.500000;"),
        )
        assert tuple(eredmeny[0, 0]) == (0, 0, 0)
        assert tuple(eredmeny[0, 1]) == (255, 255, 255)
