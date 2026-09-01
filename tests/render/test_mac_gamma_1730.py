"""#1730 — a `Mac gamma (1.6)` megjelenítési mód.

## A mért lelet (#1580, a tulajdonos felvételei)

A `Mac gamma (1.6)` **világosít**:

| terület | változás |
|---|---|
| teljes képernyő (luma) | **+3,32 %** (RGB átlag +7,1/255) |
| a központi fotó | **+15,7 %** (luma 133,5 → 154,5) |
| a felület elemei | +1,3 … +4,2 % |

A világosítás **konzisztens az `x^(1/1,6)` gammával** (0,625-ös kitevő).

## ⚠️ Ez SZÁMÍTOTT tábla, nem MÉRT — a különbség számít

A `LINEAR_GAMMA_LUT` (2.2) a **binárisból kiolvasott** adat: minden
bájtja mérés. A `MAC_GAMMA_LUT` **nem az** — a képlet a képpont-mérés
IRÁNYÁBÓL és NAGYSÁGÁBÓL következtetett, a bináris táblát nem láttuk.

Ezért a teszt nem bájtra egyeztet, hanem azt méri, amit a mérés
tényleg megmond: **hogy világosít, és mekkora nagyságrendben.**
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.display_modes import (
    MAC_GAMMA_EXPONENT,
    MAC_GAMMA_MEASURED_PAIR,
    MAC_MODE,
    apply_display_mode,
    apply_mac_gamma,
    display_mode_changes_pixels,
    luma,
)


def _szurke(ertek: int, meret: int = 32) -> np.ndarray:
    return np.full((meret, meret, 3), ertek, dtype=np.uint8)


class TestAzIrany:
    @pytest.mark.parametrize("ertek", [1, 32, 64, 128, 192, 240])
    def test_MINDEN_kozbenso_ertek_vilagosodik(self, ertek: int):
        eredmeny = apply_mac_gamma(_szurke(ertek))
        assert eredmeny[0, 0, 0] > ertek, (
            f"{ertek} → {eredmeny[0, 0, 0]}: a Mac gamma VILÁGOSÍT (#1580)"
        )

    @pytest.mark.parametrize("ertek", [0, 255])
    def test_a_ket_veget_HELYBEN_hagyja(self, ertek: int):
        """A gamma a 0-t és a 255-öt fixen hagyja — enélkül a fekete
        szürkévé mosódna, a fehér pedig kicsordulna."""
        assert apply_mac_gamma(_szurke(ertek))[0, 0, 0] == ertek


class TestANagysagrend:
    def test_a_kozepszurke_a_MERT_savba_esik(self):
        """A #1580 központi fotóján a luma 133,5 → 154,5 (+15,7 %).
        A 133-as középszürkére ugyanennek a nagyságrendnek kell jönnie."""
        elotte = 133
        utana = int(apply_mac_gamma(_szurke(elotte))[0, 0, 0])
        novekmeny = (utana - elotte) / elotte
        assert 0.10 <= novekmeny <= 0.22, (
            f"{elotte} → {utana} ({novekmeny:.1%}) — a mért +15,7 %-tól "
            "túl messze (#1580)"
        )

    def test_egy_valodi_kepen_a_luma_no(self):
        rng = np.random.default_rng(1730)
        kep = rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)
        elotte = float(luma(kep).mean())
        utana = float(luma(apply_mac_gamma(kep)).mean())
        assert utana > elotte
        assert (utana - elotte) / elotte >= 0.03, (
            "a teljes képre vetített világosodás a mért +3,32 % alatt van"
        )


class TestABekotes:
    def test_az_apply_display_mode_MAR_NEM_ereszti_at(self):
        kep = _szurke(100)
        eredmeny = apply_display_mode(kep, MAC_MODE)
        assert eredmeny is not None
        assert not np.array_equal(eredmeny, kep), (
            "a `mac` mód még mindig áteresztés — a felhasználó nem kapja "
            "meg a Mac gammát (#1730)"
        )

    def test_a_mod_KEPPONTOT_MOZDITONAK_szamit(self):
        """A `display_mode_changes_pixels` szerződése: aki gyorstáraz,
        ebből tudja, hogy újra kell renderelni."""
        assert display_mode_changes_pixels(MAC_MODE) is True

    def test_ures_kepre_nem_szall_el(self):
        ures = np.zeros((0, 0, 3), dtype=np.uint8)
        assert apply_mac_gamma(ures).shape == ures.shape

    def test_None_re_None(self):
        assert apply_display_mode(None, MAC_MODE) is None


class TestASzamitottTabla:
    def test_a_kitevo_a_MERT_parbol_jon_nem_a_feliratbol(self):
        """⚠️ A jegy szerint a mérés „konzisztens az `x^(1/1,6)`
        gammával" — SZÁMSZERŰEN NEM AZ. A mért pár (133,5 → 154,5)
        kitevője 0,7743 (gamma 1,292); az `1/1,6 = 0,625` ugyanerre
        170,2-t adna. A mérést követjük, nem a menüfeliratot."""
        import math

        be, ki = MAC_GAMMA_MEASURED_PAIR
        mert_kitevo = math.log(ki / 255) / math.log(be / 255)
        assert MAC_GAMMA_EXPONENT == pytest.approx(mert_kitevo, abs=0.001)
        assert MAC_GAMMA_EXPONENT != pytest.approx(1.0 / 1.6, abs=0.01), (
            "a kitevő visszacsúszott a menüfelirat 1,6-os értékére — az "
            "a mértnél jóval világosabb képet adna (#1730)"
        )

    def test_a_docstring_KIMONDJA_hogy_szamitott(self):
        """A `LINEAR_GAMMA_LUT` mért adat; ez nem az. Ha a kód ezt
        elhallgatná, egy későbbi kör mérésnek hinné."""
        from picasapy.render import display_modes

        szoveg = " ".join((apply_mac_gamma.__doc__ or "").split())
        assert "SZÁMÍTOTT" in szoveg or "számított" in szoveg
        assert "nem mért" in szoveg or "NEM mért" in szoveg
        assert display_modes.MAC_GAMMA_LUT, "a tábla üres"
