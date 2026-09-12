"""#723: a `Soften` és a `Neon` vezérlő-készlete az EREDETIÉ.

## A mérés (`filterdesc.xml`, Picasa 3.9.141.259)

| effekt | az eredeti vezérlői |
|---|---|
| `Soften` | `_sldrImpact` → **Softness** (0–100, alap 50) · `_sldrFade` → **Fade** (0–100, alap 50) |
| `Neon` | `_clrsw` → **Neon Color** (alap `#ff0000`) · `_sldrFade` → **Fade** |

## A hiba, amit ez a próba fog

A katalógus (`effect_params.py`) MÁS készletet hirdetett, mint amit a
lánc kiolvas (`chain_glimmer_handlers.py`):

| effekt | katalógus (rossz) | a lánc olvasata |
|---|---|---|
| `soften` | `amount`, **`radius`** | 0. = impact, **1. = fade** |
| `neon` | **`intensity`** | **0. = fade**, 1. = szín |

⇒ A „Radius" feliratú csúszka valójában a **fokozatot** állította, a
színválasztó pedig teljesen hiányzott. Ez nem felirat-hiba: a
felhasználó MÁST állított, mint amit a felirat ígért.

⚠️ Ezért a próba a katalógus és a LÁNC egyezését méri, nem csak a
feliratokat.
"""

from __future__ import annotations

import pytest

from picasapy.app.effect_params import _CATALOGUE as EFFECT_PARAMS


def _kulcsok(effekt: str) -> list[str]:
    return [p.key for p in EFFECT_PARAMS[effekt]]


def _felirat(effekt: str, kulcs: str) -> str:
    for p in EFFECT_PARAMS[effekt]:
        if p.key == kulcs:
            return p.label
    raise AssertionError(f"nincs ilyen paraméter: {effekt}.{kulcs}")


class TestASoften:
    def test_a_KET_csuszka_a_mert(self):
        assert _kulcsok("soften") == ["impact", "fade"]

    def test_a_feliratok_a_mertek(self):
        assert _felirat("soften", "impact") == "Softness"
        assert _felirat("soften", "fade") == "Fade"

    def test_NINCS_radius_csuszka(self):
        """Az eredetiben ilyen nincs — és a lánc sem olvas radiust."""
        assert "radius" not in _kulcsok("soften")

    def test_az_alapertekek_a_mertek(self):
        for p in EFFECT_PARAMS["soften"]:
            assert p.default == 50.0, f"{p.key} alapértéke {p.default}"


class TestANeon:
    def test_van_SZINVALASZTO(self):
        assert "color" in _kulcsok("neon")

    def test_a_szin_alapja_a_mert_piros(self):
        szin = next(p for p in EFFECT_PARAMS["neon"] if p.key == "color")
        assert szin.color.lower() == "#ff0000"
        assert szin.label == "Neon Color"

    def test_a_FOKOZAT_az_elso_rekesz(self):
        """A lánc a 0. rekeszt olvassa fokozatnak, az 1.-et színnek."""
        assert _kulcsok("neon") == ["fade", "color"]

    def test_NINCS_intensity(self):
        assert "intensity" not in _kulcsok("neon")


class TestAKatalogusEsALanc:
    """A katalógus SORRENDJE a lánc olvasatát követi — ez a hiba magja."""

    @pytest.mark.parametrize(
        "effekt, vart",
        [("soften", ["impact", "fade"]), ("neon", ["fade", "color"])],
    )
    def test_a_sorrend_egyezik(self, effekt, vart):
        assert _kulcsok(effekt) == vart
