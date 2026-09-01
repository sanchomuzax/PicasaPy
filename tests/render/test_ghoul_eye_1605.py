"""#1605 — a Ghoul Eye színe, keverési módjai és a hiányzó görbe.

## A lelet

Az effekt négy ponton tért el a `filterdesc.xml` 1269–1295. sorától, és
a négyből három **ellentétes irányba** vitte a képet:

| # | eredeti | nálunk volt |
|---|---|---|
| szín | `eyeColor = kclrGreen = 0xC2FF9E` = RGB(194, 255, 158) | `(200, 255, 0)` — a kék csatorna teljesen hiányzott |
| elmosás | `BlendMode.LIGHTEN`-nel keveredik vissza | nem keveredett, közvetlenül használtuk |
| színezés | `BlendMode.SCREEN` — **világosít** | `multiply` — **sötétít** |
| görbe | `{0→20, 255→255}` a színezés ELŐTT | nem volt |

A `color` paraméter docstringje „dokumentáltan ÖNKÉNYES alapértéknek"
nevezte a színt. Nem az: a `filterdesc.xml` megadja, csak nem a csúszka-
táblázatban, hanem nevesített változóként.

## Amit ez az őr rögzít

Nem képpontpontos golden-összevetés (ahhoz Picasa-export kellene erre az
effektre, ami nincs) — hanem a négy eltérés **IRÁNYA és jelenléte**, ami
mind a négyre eldönthető szintetikus képen:

1. a szín mindhárom komponense a mért `0xC2FF9E`;
2. a görbe miatt a **fekete bemenet sem marad fekete** (a `{0→20}` tag);
3. a SCREEN miatt a kimenet **nem lehet sötétebb** a bemenetnél — a
   korábbi `multiply` épp ezt csinálta;
4. maszk nélkül továbbra is **azonosság** (#688) — ezt nem szabad elrontani.

⚠️ A 3. pont a legfontosabb: egy `multiply` → `screen` csere zöld marad
minden olyan teszten, ami csak azt nézi, hogy „a kép megváltozott".
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.glimmer_focal import (
    GHOUL_EYE_COLOR,
    GHOUL_EYE_CURVE,
    apply_reanimated_eye_color,
)


@pytest.fixture
def kep() -> np.ndarray:
    """Közepes szürke, egy sötét és egy világos folttal — a SCREEN/multiply
    irány mindkét végén eldönthető legyen."""
    k = np.full((16, 16, 3), 128, dtype=np.uint8)
    k[:4, :4] = 0
    k[-4:, -4:] = 240
    return k


@pytest.fixture
def maszk() -> np.ndarray:
    return np.ones((16, 16), dtype=np.float32)


class TestASzin:
    def test_a_mert_ertek(self):
        """`eyeColor = kclrGreen = 0xC2FF9E` (filterdesc.xml 1269–1295)."""
        assert GHOUL_EYE_COLOR == (0xC2, 0xFF, 0x9E) == (194, 255, 158)

    def test_a_kek_csatorna_nem_nulla(self):
        """Ez volt a hiba: `(200, 255, 0)` — élénk sárgászöld a halvány
        helyett."""
        assert GHOUL_EYE_COLOR[2] > 0


class TestAGorbe:
    def test_a_mert_pontok(self):
        assert GHOUL_EYE_CURVE == ((0, 20), (255, 255))

    def test_a_feketet_megemeli(self, kep, maszk):
        """A `{0→20}` tag miatt a tiszta fekete folt sem maradhat fekete —
        görbe nélkül a színezés a nullát nullán hagyná."""
        ki = apply_reanimated_eye_color(kep, blur=1e-6, fade=0.0, mask=maszk)
        assert ki[:4, :4].max() > 0


class TestAKeveresIranya:
    def test_a_screen_nem_sotetit(self, kep, maszk):
        """A SCREEN sosem ad a bemenetnél sötétebb képpontot. A korábbi
        `multiply` PONTOSAN ezt csinálta — ez a teszt foga."""
        ki = apply_reanimated_eye_color(kep, blur=1e-6, fade=0.0, mask=maszk)
        assert np.all(ki.astype(np.int16) >= kep.astype(np.int16) - 1), (
            "a kimenet sötétebb lett a bemenetnél — ez multiply, nem SCREEN"
        )

    def test_tenylegesen_vilagosit(self, kep, maszk):
        ki = apply_reanimated_eye_color(kep, blur=1e-6, fade=0.0, mask=maszk)
        assert ki.mean() > kep.mean() + 1.0


class TestAmitNEM_szabad_elrontani:
    def test_maszk_nelkul_azonossag(self, kep):
        """#688: ecset-maszk nélkül az effekt bitre érintetlenül hagy."""
        assert np.array_equal(apply_reanimated_eye_color(kep), kep)

    def test_fade_100_nal_nincs_valtozas(self, kep, maszk):
        """`BlendAlpha = 1 − Fade/100` → Fade=100-nál a súly 0."""
        ki = apply_reanimated_eye_color(kep, fade=100.0, mask=maszk)
        assert np.array_equal(ki, kep)

    def test_nulla_maszk_bitre_azonos(self, kep):
        ures = np.zeros((16, 16), dtype=np.float32)
        assert np.array_equal(apply_reanimated_eye_color(kep, mask=ures), kep)
