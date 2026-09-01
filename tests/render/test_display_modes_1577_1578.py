"""A két sötétítő mód (#1577) és a lineáris gamma (#1578) képpont-szabálya.

Bizonyíték: `docs/specs/picasa-megjelenitesi-modok.md` 5.4, 5.5 és 5.9 — a
#1409 feltárása a `Picasa3.exe`-ből.

| mód | rutin | szabály |
|---|---|---|
| `projector` | `0x009e8a10` | `c' = (c · 220) >> 8` mindhárom csatornára |
| `lcd` | `0x009e8a70` | `c' = (c · 246) >> 8` mindhárom csatornára |
| `linear` | `0x009e8b60` → `0x00aa3f80` | 256 bájtos, a binárisból MÉRT tábla |

⚠️ **Minden várt érték KIÍRT LITERÁL**, nem a termékbeli konstansról
olvasva. Ha a teszt a `PROJECTOR_MULTIPLIER`-ből vagy a `LINEAR_GAMMA_LUT`-ból
számolná a várt értéket, önmagát igazolná: a szorzó vagy a tábla elrontása
zöld maradna. Ez a „szabad paraméter elnyeli a hibát" csapda (#1462).

⚠️ **A gamma-tábla NEM `x^(1/2.2)`.** A `2.2f` float a binárisban a tábla
KIVÁLASZTÓ KULCSA; a tábla előre kitöltve érkezik (`0x00d32bd0`). A legjobb
hatványillesztés `p = 0,6944` (gamma ≈ 1,44), és még az is 37 helyen téved
±1-gyel. Az alábbi `SPEC_LUT` ezért a spec táblájának FÜGGETLEN átirata — a
`TestNemKeplet` osztály tételesen bizonyítja, hogy képlettel nem pótolható.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import numpy as np
import pytest

from picasapy.render.display_modes import (
    LCD_MODE,
    LCD_MULTIPLIER,
    LINEAR_GAMMA_LUT,
    LINEAR_GAMMA_MODE,
    PROJECTOR_MODE,
    PROJECTOR_MULTIPLIER,
    apply_display_mode,
    apply_linear_gamma,
    darken,
    display_mode_changes_pixels,
)

SPEC = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "specs"
    / "picasa-megjelenitesi-modok.md"
)

#: A spec 5.9 táblája KIÍRVA, soronként 16 érték — a bináris `0x00d32bd0`
#: címén mért 256 bájt. A tábla elrontása így a termékben BUKÁST okoz.
SPEC_LUT: tuple[int, ...] = (
      0,   5,   9,  11,  14,  16,  19,  21,  23,  25,  27,  29,  30,  32,  34,  36,
     37,  39,  40,  42,  44,  45,  47,  48,  49,  51,  52,  54,  55,  56,  58,  59,
     60,  62,  63,  64,  66,  67,  68,  69,  71,  72,  73,  74,  75,  77,  78,  79,
     80,  81,  82,  84,  85,  86,  87,  88,  89,  90,  91,  92,  94,  95,  96,  97,
     98,  99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113,
    114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129,
    129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 140, 141, 142, 143,
    144, 145, 146, 147, 148, 149, 149, 150, 151, 152, 153, 154, 155, 155, 156, 157,
    158, 159, 160, 161, 161, 162, 163, 164, 165, 166, 166, 167, 168, 169, 170, 171,
    171, 172, 173, 174, 175, 176, 176, 177, 178, 179, 180, 180, 181, 182, 183, 184,
    184, 185, 186, 187, 188, 188, 189, 190, 191, 192, 192, 193, 194, 195, 195, 196,
    197, 198, 199, 199, 200, 201, 202, 202, 203, 204, 205, 205, 206, 207, 208, 208,
    209, 210, 211, 211, 212, 213, 214, 214, 215, 216, 217, 217, 218, 219, 220, 220,
    221, 222, 223, 223, 224, 225, 225, 226, 227, 228, 228, 229, 230, 231, 231, 232,
    233, 233, 234, 235, 236, 236, 237, 238, 238, 239, 240, 241, 241, 242, 243, 243,
    244, 245, 245, 246, 247, 248, 248, 249, 250, 250, 251, 252, 252, 253, 254, 255,
)  # fmt: skip

#: Tizenkét mintaérték, KIÍRVA: `(bemenet, projektor, lcd, lineáris gamma)`.
#: A projektor/LCD oszlop a `(c·220)>>8` illetve `(c·246)>>8` egész
#: aritmetikából, a gamma oszlop a spec táblájából.
MINTAK: tuple[tuple[int, int, int, int], ...] = (
    (0, 0, 0, 0),
    (1, 0, 0, 5),
    (2, 1, 1, 9),
    (16, 13, 15, 37),
    (32, 27, 30, 60),
    (64, 55, 61, 98),
    (100, 85, 96, 133),
    (128, 110, 123, 158),
    (160, 137, 153, 184),
    (200, 171, 192, 215),
    (254, 218, 244, 254),
    (255, 219, 245, 255),
)


def _raszter(*szinek: tuple[int, int, int]) -> np.ndarray:
    """`(1, N, 3)` uint8 kép a megadott színekből."""
    return np.array([list(szinek)], dtype=np.uint8)


def _spec_tablaja() -> tuple[int, ...]:
    """A spec 5.9 kódblokkjának beolvasása — `index: v v v …` sorok."""
    szoveg = SPEC.read_text(encoding="utf-8")
    blokk = szoveg[szoveg.index("### 5.9 ") : szoveg.index("### 5.10 ")]
    kod = re.search(r"```\n(.*?)```", blokk, re.S)
    assert kod is not None, "a spec 5.9 szakaszában nincs kódblokk"
    ertekek: list[int] = []
    for sor in kod.group(1).strip().splitlines():
        index, _, maradek = sor.partition(":")
        assert int(index.strip()) == len(ertekek), f"kihagyott sor: {sor!r}"
        ertekek.extend(int(v) for v in maradek.split())
    return tuple(ertekek)


class TestSpecAtirat:
    """A tesztbeli `SPEC_LUT` tényleg a spec táblája — átírási hiba kizárva."""

    def test_a_teszt_tablaja_a_spec_tablaja(self):
        assert SPEC_LUT == _spec_tablaja()

    def test_a_termek_tablaja_a_spec_tablaja(self):
        assert tuple(LINEAR_GAMMA_LUT) == _spec_tablaja()

    def test_a_termek_tablaja_a_kiirt_literal(self):
        assert tuple(LINEAR_GAMMA_LUT) == SPEC_LUT
        assert len(LINEAR_GAMMA_LUT) == 256


class TestSzorzokKiirva:
    """A két szorzó a specből: `0xDC` = 220 és `0xF6` = 246."""

    def test_projektor_szorzo(self):
        assert PROJECTOR_MULTIPLIER == 220

    def test_lcd_szorzo(self):
        assert LCD_MULTIPLIER == 246

    def test_a_modazonositok(self):
        assert (PROJECTOR_MODE, LCD_MODE, LINEAR_GAMMA_MODE) == (
            "projector",
            "lcd",
            "linear",
        )


class TestSotetites:
    """`darken` — az egyenletes, csatornaazonos szorzás (5.4/5.5)."""

    @pytest.mark.parametrize("be,projektor,_lcd,_gamma", MINTAK)
    def test_projektor_mintaertekek(self, be, projektor, _lcd, _gamma):
        eredmeny = darken(_raszter((be, be, be)), 220)
        assert tuple(int(c) for c in eredmeny[0, 0]) == (
            projektor,
            projektor,
            projektor,
        )

    @pytest.mark.parametrize("be,_projektor,lcd,_gamma", MINTAK)
    def test_lcd_mintaertekek(self, be, _projektor, lcd, _gamma):
        eredmeny = darken(_raszter((be, be, be)), 246)
        assert tuple(int(c) for c in eredmeny[0, 0]) == (lcd, lcd, lcd)

    def test_csatornankent_azonos_szorzo_nincs_szineltolas(self):
        """A három szorzó AZONOS — az „LCD fehérpont" NEM tol színt."""
        be = _raszter((200, 200, 200))
        ki = darken(be, 246)
        assert ki[0, 0, 0] == ki[0, 0, 1] == ki[0, 0, 2] == 192

    def test_a_szinek_aranya_megmarad(self):
        """Vegyes képpont: mindhárom csatorna a SAJÁT értékéből számol."""
        ki = darken(_raszter((255, 128, 0)), 220)
        assert tuple(int(c) for c in ki[0, 0]) == (219, 110, 0)

    def test_a_bemenetet_nem_irja_at(self):
        be = _raszter((255, 255, 255))
        masolat = be.copy()
        darken(be, 220)
        assert np.array_equal(be, masolat), (
            "a sötétítés helyben írta át a bemenetet — az edit-előnézet "
            "gyorsítótárazott képet ad át, annak megmérgezése a mód "
            "kikapcsolása után is sötét képet hagyna"
        )

    def test_uj_tombot_ad(self):
        be = _raszter((10, 10, 10))
        assert darken(be, 220) is not be

    def test_alak_es_tipus(self):
        be = np.zeros((4, 6, 3), dtype=np.uint8)
        ki = darken(be, 246)
        assert ki.shape == be.shape
        assert ki.dtype == np.uint8

    def test_nem_folyik_tul(self):
        """A szorzat 16 biten fut — 255·246 = 62730 nem csordulhat 8 bitre."""
        ki = darken(np.full((2, 2, 3), 255, dtype=np.uint8), 246)
        assert ki.min() == 245 and ki.max() == 245

    def test_a_nem_osszefuggo_tombot_is_kezeli(self):
        """A hívó szeletelt (nem összefüggő) nézetet is átadhat."""
        nagy = np.full((4, 8, 3), 255, dtype=np.uint8)
        ki = darken(nagy[:, ::2], 220)
        assert ki.shape == (4, 4, 3)
        assert ki.min() == 219 and ki.max() == 219


class TestLinearisGamma:
    """`apply_linear_gamma` — a MÉRT tábla csatornánként (5.9)."""

    @pytest.mark.parametrize("be,_projektor,_lcd,gamma", MINTAK)
    def test_mintaertekek(self, be, _projektor, _lcd, gamma):
        ki = apply_linear_gamma(_raszter((be, be, be)))
        assert tuple(int(c) for c in ki[0, 0]) == (gamma, gamma, gamma)

    def test_mind_a_256_ertek(self):
        """A teljes értékkészlet tételesen, a KIÍRT táblához mérve."""
        be = np.arange(256, dtype=np.uint8).reshape((1, 256, 1))
        ki = apply_linear_gamma(np.repeat(be, 3, axis=2))
        assert list(ki[0, :, 0]) == list(SPEC_LUT)
        assert list(ki[0, :, 1]) == list(SPEC_LUT)
        assert list(ki[0, :, 2]) == list(SPEC_LUT)

    def test_csatornankent_kulon(self):
        ki = apply_linear_gamma(_raszter((0, 128, 255)))
        assert tuple(int(c) for c in ki[0, 0]) == (0, 158, 255)

    def test_vilagosit(self):
        """A csoport EGYETLEN világosító módja — a sötét részletek nyílnak."""
        assert SPEC_LUT[1] > 1 and SPEC_LUT[64] > 64 and SPEC_LUT[200] > 200

    def test_a_bemenetet_nem_irja_at(self):
        be = _raszter((10, 20, 30))
        masolat = be.copy()
        apply_linear_gamma(be)
        assert np.array_equal(be, masolat)

    def test_alak_es_tipus(self):
        be = np.zeros((4, 6, 3), dtype=np.uint8)
        ki = apply_linear_gamma(be)
        assert ki.shape == be.shape
        assert ki.dtype == np.uint8


class TestNemKeplet:
    """A tábla képlettel NEM pótolható — a jegy legfontosabb lelete."""

    def test_nem_x_az_egy_per_2_2_hatvanyon(self):
        """A kézenfekvő `x^(1/2.2)` durván mellémegy."""
        elteres = [
            abs(round((i / 255) ** (1 / 2.2) * 255) - SPEC_LUT[i])
            for i in range(256)
        ]
        assert max(elteres) > 10, (
            "az `x^(1/2.2)` képlet közel jár a mért táblához — ha ez "
            "teljesül, a spec 5.9 lelete megdőlt, nézd újra a mérést"
        )

    def test_a_legjobb_hatvanyillesztes_sem_pontos(self):
        """`p = 0,6944` (gamma ≈ 1,44) a legjobb — még az is 37-szer téved."""
        rossz = sum(
            1 for i in range(256) if round((i / 255) ** 0.6944 * 255) != SPEC_LUT[i]
        )
        assert rossz == 37, (
            "a legjobb hatványillesztés eltéréseinek száma megváltozott — a "
            "tábla nem a mért adat"
        )

    def test_a_2_2_csak_kivalaszto_kulcs(self):
        """Forrás-őr: a modul nem számol hatványt a táblához."""
        from picasapy.render import display_modes

        forras = inspect.getsource(display_modes)
        for tiltott in ("** (1 / 2.2)", "np.power", "math.pow", "** (1/2.2)"):
            assert tiltott not in forras, (
                f"a modul hatványt számol ({tiltott!r}) — a tábla MÉRT adat, "
                "képlettel helyettesítve mérhetően rossz eredményt ad"
            )

    def test_a_kod_kimondja_hogy_nem_keplet(self):
        """A következő olvasó ne „javítsa ki" a táblát képletre."""
        from picasapy.render import display_modes

        forras = inspect.getsource(display_modes)
        assert "MÉRT" in forras or "MÉRVE" in forras
        assert "nem" in forras and "1/2.2" in forras.replace(" ", "")


class TestModValaszto:
    """`apply_display_mode` — a három új mód a közös belépési ponton."""

    def test_projektor(self):
        ki = apply_display_mode(_raszter((255, 128, 0)), "projector")
        assert tuple(int(c) for c in ki[0, 0]) == (219, 110, 0)

    def test_lcd(self):
        ki = apply_display_mode(_raszter((255, 128, 0)), "lcd")
        assert tuple(int(c) for c in ki[0, 0]) == (245, 123, 0)

    def test_linearis_gamma(self):
        ki = apply_display_mode(_raszter((0, 128, 255)), "linear")
        assert tuple(int(c) for c in ki[0, 0]) == (0, 158, 255)

    def test_a_ket_sotetites_kulonbozik(self):
        """Kontroll: a két mód NEM ugyanaz — a szorzó tényleg eltér."""
        be = _raszter((255, 255, 255))
        assert not np.array_equal(
            apply_display_mode(be, "projector"), apply_display_mode(be, "lcd")
        )

    @pytest.mark.parametrize(
        "mode", ["projector", "lcd", "linear", "overflow"]
    )
    def test_a_kepponthatas_lekerdezheto(self, mode):
        assert display_mode_changes_pixels(mode) is True

    @pytest.mark.parametrize(
        "mode",
        ["auto", "normal", "dither16", "rdesk", "", "ismeretlen"],
    )
    def test_a_tobbi_mod_meg_atenged(self, mode):
        """A `dither16`/`rdesk` a #1579 szerint KIHAGYANDÓ (nincs 16 bites
        képernyő, ill. RDP-specifikus).

        A `sepia` és a `bw` a #1657 óta KIKERÜLT innen; a `mac` a #1730
        óta — a képpont-szabályukat a saját tesztfájljuk őrzi
        (`test_display_modes_szepia_bw_1657.py`, `test_mac_gamma_1730.py`).
        """
        forras = _raszter((255, 255, 255), (0, 0, 0), (128, 64, 32))
        assert np.array_equal(apply_display_mode(forras, mode), forras)
        assert display_mode_changes_pixels(mode) is False

    def test_a_none_kepet_atengedi(self):
        for mode in ("projector", "lcd", "linear"):
            assert apply_display_mode(None, mode) is None
