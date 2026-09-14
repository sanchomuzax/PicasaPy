"""A szerkesztő-panel felirat-fokozatai az EREDETI abszolút értékeit veszik át (#2990).

## A döntés, amit ez a lap rögzít

A #815 mérése két fokozatot hozott a Picasa saját betű-makróiból
(`fontmacros_win.tre`), és a #2990 azt a kérdést tette fel, hogy az
ABSZOLÚT értékeket vegyük-e át, vagy a viszonyt tartsuk a saját alapunkhoz.

**Az abszolút értékek** — mert a tulajdonos szabálya „pontosan úgy, mint az
eredeti Picasa", és mert a #422 felhasználói döntése így is teljesül
(11 < 12, tehát az effekt-csempe felirata KISEBB marad, nem nagyobb).

## A három makró és a nálunk megfelelő elem — MÉRVE

| makró | `fontsize` | `fontweight` | az eredeti eleme | nálunk |
|---|---:|---:|---|---|
| `m_fxlabel` | **11** | **700** | `editpanel/fxlabelN` (effekt-csempe) | `PanelButton`, ha van bélyegképe |
| `m_buttonfontCbelow` | **12** | 400 | `editpanel/crop-label` (eszköz-csempe) | `ToolTile` |
| `m_buttonfontC` | **12** | 400 | `editpanel/croprotatecrop-label` (sima gomb) | `PanelButton` bélyegkép nélkül |

A hozzárendelés nem feltevés: az `editpanel.tre` minden elem alatt
NÉVSZERINT hivatkozik a makróra (`m_fxlabel` a tizenkét `fxlabelN`-en,
`m_buttonfontCbelow` a `crop`/`redeye`/`retouch`/… címkéjén).

## Amit ez a lap NEM mér

A felirat-fokozat nem ugyanaz, mint a KIRAJZOLT magasság: a `PanelButton`
rögzített magasságnál a fokozatot lejjebb illesztheti (#2597). Ezért a
csempéken az ALAP fokozatot (`labelAlapFokozat`) is állítjuk, és a
kirajzolt `font.pixelSize`-t is megnézzük ott, ahol nincs illesztés. A
geometriát a #2494 és a #741 lapjai őrzik.
"""

from __future__ import annotations

import pytest

from tests.app.qml_functional.test_effect_tile_grid_704 import _child, _render

#: `m_fxlabel` — az effekt-csempe felirata (bélyegképes `PanelButton`).
CSEMPE_FOKOZAT = 11
CSEMPE_SULY = 700

#: `m_buttonfontC` / `m_buttonfontCbelow` — minden más felirat a panelen.
GOMB_FOKOZAT = 12


def _alap_fokozat(elem) -> int:
    return int(elem.property("labelAlapFokozat"))


class TestAzEffektCsempe:
    """`m_fxlabel`: 11 képpont, félkövér."""

    def test_az_alapfokozat_11(self, qt_app) -> None:
        gyoker = _render(qt_app, 3)
        csempe = _child(gyoker, "effectIr")
        assert _alap_fokozat(csempe) == CSEMPE_FOKOZAT

    def test_a_felirat_felkover(self, qt_app) -> None:
        """`Property fontweight 700` — az egyetlen félkövér felirat a panelen."""
        gyoker = _render(qt_app, 3)
        cimke = _child(gyoker, "effectIrLabel")
        assert cimke.property("font").bold()


class TestAzEszkozCsempe:
    """`m_buttonfontCbelow`: 12 képpont, normál."""

    def test_a_kirajzolt_fokozat_12(self, qt_app) -> None:
        gyoker = _render(qt_app, 1)
        cimke = _child(gyoker, "editToolCropLabel")
        assert cimke.property("font").pixelSize() == GOMB_FOKOZAT

    def test_a_felirat_NEM_felkover(self, qt_app) -> None:
        gyoker = _render(qt_app, 1)
        cimke = _child(gyoker, "editToolCropLabel")
        assert not cimke.property("font").bold()


class TestASimaGomb:
    """`m_buttonfontC`: 12 képpont — a bélyegkép nélküli `PanelButton`."""

    def test_az_alapfokozat_12(self, qt_app) -> None:
        gyoker = _render(qt_app, 1)
        gomb = _child(gyoker, "editUndoButton")
        assert _alap_fokozat(gomb) == GOMB_FOKOZAT


class TestA422Dontese:
    """⛔ A felhasználó döntése: az effekt-csempe felirata NEM lehet nagyobb
    az eszköz-csempéénél.

    *„az effekt-csempék felirata nagyobb volt, mint az eszköz-csempéké — a
    kisebb a helyes."* (#422) Az abszolút átvétel ezt TELJESÍTI (11 < 12), a
    fordított irány viszont visszahozná a panaszt, ezért kell rá kikötés."""

    def test_a_csempefelirat_kisebb_az_eszkozcsempeenel(self, qt_app) -> None:
        effekt = _child(_render(qt_app, 3), "effectIr")
        eszkoz = _child(_render(qt_app, 1), "editToolCropLabel")
        assert _alap_fokozat(effekt) < eszkoz.property("font").pixelSize()


class TestADontesEgyHelyenEl:
    """A jegy kikötése: a fokozat a `Theme`-ben él, nem elemenként beírva."""

    @pytest.mark.parametrize(
        "fajl,tiltott",
        [
            ("PanelButton.qml", "Theme.fontSize - 2"),
            ("ToolTile.qml", "Theme.fontSize - 2"),
        ],
    )
    def test_a_panel_feliratai_nem_a_fontSize_eltolasabol_jonnek(
        self, fajl: str, tiltott: str
    ) -> None:
        from picasapy.app import application as app_module

        forras = (app_module._APP_DIR / "qml" / "PicasaPy" / fajl).read_text(
            encoding="utf-8"
        )
        assert tiltott not in forras, (
            f"{fajl}: a felirat-fokozat még mindig a `{tiltott}` eltolásból "
            "jön — a #2990 szerint a döntés a Theme-ben, egy helyen él"
        )

    def test_a_theme_mind_a_ket_fokozatot_nevesiti(self) -> None:
        from picasapy.app import application as app_module

        forras = (app_module._APP_DIR / "qml" / "PicasaPy" / "Theme.qml").read_text(
            encoding="utf-8"
        )
        assert f"tileLabelSize: {CSEMPE_FOKOZAT}" in forras
        assert f"buttonLabelSize: {GOMB_FOKOZAT}" in forras
