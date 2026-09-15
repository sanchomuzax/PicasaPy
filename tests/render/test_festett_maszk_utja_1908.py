"""#1908: a festett (ecset-)maszk ÚTJA a szűrőláncon.

A render-oldal a #1605 óta tudja fogadni a maszkot
(`apply_reanimated_eye_color(mask=…)`), de a **lánc** nem tudta átadni:
az `apply_filters` szignatúrájában nem volt maszk, ezért az öt festhető
effekt (`Boost`, `Pixelate`, `Soften`, `PicnikTint`, `ReanimatedEyeColor`)
mindig a teljes képre futott — vagy a `ReanimatedEyeColor` esetén sosem
hatott.

A mért szemantika (`filterdesc.xml` 1269–1295., #1605): a maszk a külső
`NestedImageOperation`-ön áll (`Mask="{_mctr.mask}"`), tehát az effekt a
TELJES képen lefut, és az eredménye a maszkon át kerül a képre —
`base·(1−mask) + effekt·mask`.

⚠️ Amit ez a lap NEM mér: az ecset-FELÜLETET. Az a jegy következő lépése; a
maszk tárolása pedig mérve nem létezik a Picasában (munkamenet-élettartamú).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.chain_glimmer_handlers import PAINTABLE_MASK_OPS


def _kep(h: int = 24, w: int = 32) -> np.ndarray:
    """TEXTURÁLT próbakép: lapos színen több effekt (Boost, Pixelate)
    azonosságot ad, tehát a lapos kép nem mérné a maszkot."""
    ys, xs = np.mgrid[0:h, 0:w]
    kep = np.zeros((h, w, 3), dtype=np.uint8)
    kep[..., 0] = (40 + 6 * (xs % 12) + 3 * (ys % 7)).clip(0, 255)
    kep[..., 1] = (90 + 5 * (ys % 9)).clip(0, 255)
    kep[..., 2] = (200 - 4 * (xs % 15)).clip(0, 255)
    return kep


def _fel_maszk(h: int = 24, w: int = 32) -> np.ndarray:
    """A kép BAL fele befestve (1.0), a jobb fele érintetlen (0.0)."""
    maszk = np.zeros((h, w), dtype=np.float32)
    maszk[:, : w // 2] = 1.0
    return maszk


class TestAMaszkEljutALancig:
    @pytest.mark.parametrize(
        "lanc",
        [
            "Boost=1,80.000000;",
            "Pixelate=1,20.000000;",
            "Soften=1,80.000000,0.000000;",
            "PicnikTint=1,0.000000,80cfff;",
            "ReanimatedEyeColor=1,6.000000,20.000000;",
        ],
    )
    def test_a_befestett_oldal_valtozik_a_masik_NEM(self, lanc):
        kep = _kep()
        maszk = _fel_maszk()
        jelentes = apply_filters(kep, parse_filters(lanc), paint_mask=maszk)
        ki = jelentes.image
        assert ki is not None
        bal_be, bal_ki = kep[:, :16], ki[:, :16]
        jobb_be, jobb_ki = kep[:, 16:], ki[:, 16:]
        assert not np.array_equal(bal_be, bal_ki), (
            f"{lanc}: a BEFESTETT oldal nem változott — a maszk nem jutott el"
        )
        assert np.array_equal(jobb_be, jobb_ki), (
            f"{lanc}: a NEM festett oldal is változott — a maszk nem szűr"
        )

    def test_maszk_NELKUL_a_mai_viselkedes_marad(self):
        """Visszafelé kompatibilitás: a paraméter nélküli hívás változatlan."""
        kep = _kep()
        nelkul = apply_filters(kep, parse_filters("Boost=1,80.000000;"))
        assert nelkul.image is not None
        # a teljes kép változik (a mai, maszk nélküli viselkedés)
        assert not np.array_equal(kep[:, 16:], nelkul.image[:, 16:])

    def test_a_ghoul_eye_URES_maszkkal_azonossag(self):
        """#688: az üres maszkkal induló effekt befestés nélkül nem hat —
        ez a maszk-út bevezetése UTÁN is igaz."""
        kep = _kep()
        ures = np.zeros(kep.shape[:2], dtype=np.float32)
        jelentes = apply_filters(
            kep, parse_filters("ReanimatedEyeColor=1,6.000000,20.000000;"),
            paint_mask=ures,
        )
        assert np.array_equal(kep, jelentes.image)

    def test_a_figyelmeztetes_CSAK_maszk_nelkul_jon(self):
        """A „nincs ecset-eszköz" figyelmeztetés a maszk megadásakor elavult —
        akkor nem szabad kimennie."""
        kep = _kep()
        lanc = parse_filters("PicnikTint=1,0.000000,80cfff;")
        nelkul = apply_filters(kep, lanc)
        assert any("ecset" in w for w in nelkul.range_warnings), (
            "maszk nélkül elvárjuk a figyelmeztetést"
        )
        maszkkal = apply_filters(kep, lanc, paint_mask=_fel_maszk())
        assert not any("ecset" in w for w in maszkkal.range_warnings), (
            "maszkkal megadott hívásnál a figyelmeztetés félrevezető"
        )

    def test_mind_az_OT_op_a_halmazban_van(self):
        assert PAINTABLE_MASK_OPS == {
            "boost", "pixelate", "soften", "picniktint", "reanimatedeyecolor",
        }

    def test_a_nem_festheto_op_a_maszkot_FIGYELMEN_kivul_hagyja(self):
        """A maszk csak az öt festhető effektre hat — a `sepia` nem közülük."""
        kep = _kep()
        lanc = parse_filters("sepia=1;")
        maszkkal = apply_filters(kep, lanc, paint_mask=_fel_maszk())
        nelkul = apply_filters(kep, lanc)
        assert np.array_equal(maszkkal.image, nelkul.image)
