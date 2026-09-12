"""#1730 — a `Mac gamma (1.6)` megjelenítési mód.

## A mért lelet (#1580, a tulajdonos felvételei)

A `Mac gamma (1.6)` **világosít**:

| terület | változás |
|---|---|
| teljes képernyő (luma) | **+3,32 %** (RGB átlag +7,1/255) |
| a központi fotó | **+15,7 %** (luma 133,5 → 154,5) |
| a felület elemei | +1,3 … +4,2 % |

A világosítás **konzisztens az `x^(1/1,6)` gammával** (0,625-ös kitevő).

## ⛔ HELYESBÍTVE (#3068): a tábla MÉRT, nem számított

A fájl eredetileg azt írta, hogy a `MAC_GAMMA_LUT` a képernyőkép-mérésből
ILLESZTETT képlet. Azóta a `0x00d32bd0` beégetett tábla megvan (spec 5.9 és
12.4), és a Mac gamma azt kapja. A képernyőkép-mérés így **kereszt-ellenőrzés**
maradt: az irányt és a nagyságrendet igazolja, a pontos bájtokat nem.

A bájtra menő egyeztetést a `test_gamma_tablak_felcserelve_3068.py` végzi; ez
a fájl azt őrzi, amit a #1580 mérése mond — **hogy világosít, és mekkora
nagyságrendben.**

A menüfelirat („1,6") és a tábla effektív gammája (≈1,44) eltér; ez az
EREDETI sajátossága.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.display_modes import (
    MAC_GAMMA_SCREENSHOT_PAIR,
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


class TestAMertTabla:
    def test_a_kepernyokep_parja_a_TABLAVAL_is_egyezik_nagysagrendben(self):
        """A #1580 felvételén a központi fotó lumája 133,5 → 154,5 (+15,7 %).
        A mért tábla ugyanerre a bemenetre +20 % körül ad — ugyanaz az
        irány és nagyságrend, tehát a tábla és a felvétel nem mond ellent
        egymásnak. A pontos bájtokat a tábla adja, nem a felvétel."""
        be, ki = MAC_GAMMA_SCREENSHOT_PAIR
        felvetelen = (ki - be) / be
        tablaval = (int(apply_mac_gamma(_szurke(int(be)))[0, 0, 0]) - be) / be
        assert 0.10 <= felvetelen <= 0.25
        assert 0.10 <= tablaval <= 0.25

    def test_a_docstring_KIMONDJA_hogy_mert(self):
        """A fokozat a kódban is álljon: aki ide nyúl, tudja, hogy mért
        táblát mozgat, nem illesztett képletet."""
        from picasapy.render import display_modes

        szoveg = " ".join((apply_mac_gamma.__doc__ or "").split())
        assert "MÉRT adat" in szoveg
        assert "0x00d32bd0" in szoveg
        assert len(display_modes.MAC_GAMMA_LUT) == 256
