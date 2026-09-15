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


class TestAFocalZoom:
    """A jegy harmadik effektje — a MÉRT feliratok és a képfüggő sugár.

    | `filterdesc.xml:894–897` | mért |
    |---|---|
    | `_sldrImpact` | 1–100, alap 50 · felirat `ImageFilters::Zoominess` |
    | `_sldrRadius` | **min 10, max `min(W,H)/2`**, alap a tartomány FELEZŐPONTJA · felirat `ImageFilters::FocalSize` |
    | `_sldrHardness` | 0–100, alap 50 |
    | `_sldrFade` | 0–100, alap 0 |

    A feliratok forrása: `referencia/stringres-en-hu.tsv:1852` (Focal Size
    / „Fókuszméret") és `:1877`-hez tartozó `ImageFilters::Zoominess`
    („Suhanás", `panel-feliratok-hu.tsv:1422`).
    """

    def test_mind_a_HAT_vezerlo_megvan(self):
        assert _kulcsok("focalzoom") == [
            "x", "y", "impact", "radius", "hardness", "fade",
        ]

    def test_a_ket_felirat_a_MERT(self):
        assert _felirat("focalzoom", "impact") == "Zoominess"
        assert _felirat("focalzoom", "radius") == "Focal Size"

    def test_a_regi_feliratok_MAR_NINCSENEK(self):
        feliratok = {p.label for p in EFFECT_PARAMS["focalzoom"]}
        assert "Impact" not in feliratok
        assert "Radius" not in feliratok

    def test_a_sugar_maximuma_KEPMERET_fuggo(self):
        from picasapy.app.effect_params import resolve_effect_params

        szeles = resolve_effect_params("focalzoom", 1000.0, 800.0)
        sugar = next(p for p in szeles if p.key == "radius")
        assert sugar.maximum == pytest.approx(400.0), "min(1000, 800) / 2"

        keskeny = resolve_effect_params("focalzoom", 600.0, 1200.0)
        sugar2 = next(p for p in keskeny if p.key == "radius")
        assert sugar2.maximum == pytest.approx(300.0), "min(600, 1200) / 2"

    def test_a_sugar_alapertele_a_tartomany_FELEZOPONTJA(self):
        from picasapy.app.effect_params import resolve_effect_params

        felold = resolve_effect_params("focalzoom", 1000.0, 800.0)
        sugar = next(p for p in felold if p.key == "radius")
        # `value="{… ((max − min) / 2) + min}"` = (400 − 10) / 2 + 10
        assert sugar.default == pytest.approx(205.0)
        assert sugar.minimum == pytest.approx(10.0)

    def test_a_tobbi_csuszka_tartomanya_VALTOZATLAN(self):
        """A képfüggés CSAK a sugárra vonatkozik — a többi fix marad."""
        from picasapy.app.effect_params import resolve_effect_params

        felold = {p.key: p for p in resolve_effect_params("focalzoom", 1000.0, 800.0)}
        assert (felold["impact"].minimum, felold["impact"].maximum) == (1.0, 100.0)
        assert felold["hardness"].default == pytest.approx(50.0)
        assert felold["fade"].default == pytest.approx(0.0)


class TestAFeliratokAFeluleten:
    """A katalógus felirata csak akkor ér valamit, ha a panel is ismeri."""

    def test_a_panel_fordit_mindket_uj_feliratot(self):
        from pathlib import Path

        import picasapy.app

        qml = (
            Path(picasapy.app.__file__).parent
            / "qml" / "PicasaPy" / "EditorParamPanel.qml"
        ).read_text(encoding="utf-8")
        assert 'case "Zoominess": return qsTr("Zoominess")' in qml
        assert 'case "Focal Size": return qsTr("Focal Size")' in qml

    def test_a_magyar_forditas_a_MERT(self):
        from pathlib import Path

        import picasapy.app

        ts = (
            Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
        ).read_text(encoding="utf-8")
        kezd = ts.index("<name>EditorParamPanel</name>")
        blokk = ts[kezd:ts.index("</context>", kezd)]
        assert "<translation>Suhanás</translation>" in blokk
        assert "<translation>Fókuszméret</translation>" in blokk
