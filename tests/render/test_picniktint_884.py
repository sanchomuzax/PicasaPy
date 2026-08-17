"""#884 — a `PicnikTint` (Színezés) a fényesség-tartó `TintImageOperation`-re.

A régi modell egy TÖMÖR SZÍNRÉTEGET kevert a képre `normal` módban, tehát
`Fade = 0`-nál a kimenet egyetlen egyszínű felület lett. A #685 mérőszettjén
ez ΔE 33,45 / SSIM 0,63 („ROSSZ").

A helyes művelet a #878-ban megfejtett `tint_luma_preserving`: a bemenet
luminanciáját bájtra megőrzi, és csak a krómát cseréli. Ugyanazt a
`TintImageOperation`-t használja a `Neon` záró lépése is.

A mérőszett képei nem kerülhetnek a publikus repóba, ezért az őrök a
csővezeték szerkezeti állításait rögzítik, plusz a golden párból MÉRT
számhármasokat.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.glimmer_focal import apply_picnik_tint
from picasapy.render.glimmer_ops import luma

#: `PicnikTint=1,0.000000,0080cfff;` — a filterdesc alapértéke, és a #685
#: mérőszettjének esete is ez.
SZIN = (0x80, 0xCF, 0xFF)


def _lapos(ertek: int, magassag: int = 16, szelesseg: int = 24) -> np.ndarray:
    return np.full((magassag, szelesseg, 3), ertek, dtype=np.uint8)


def _atmenet(szelesseg: int = 64) -> np.ndarray:
    sav = np.linspace(0, 255, szelesseg, dtype=np.uint8)
    return np.tile(sav[np.newaxis, :, np.newaxis], (32, 1, 3))


class TestFenyessegTartas:
    @pytest.mark.parametrize("ertek", [0, 16, 64, 128, 200, 255])
    def test_a_luminancia_megmarad(self, ertek):
        eredmeny = apply_picnik_tint(_lapos(ertek), color=SZIN, fade=0.0)
        assert abs(float(luma(eredmeny.astype(np.float32)).mean()) - ertek) <= 1.5

    def test_a_kep_NEM_lesz_egyszinu(self):
        """A régi modell pont ezt csinálta: `Fade = 0`-nál tömör színfelület.
        A valódi Színezés megtartja a kép rajzolatát."""
        eredmeny = apply_picnik_tint(_atmenet(), color=SZIN, fade=0.0)
        assert eredmeny[..., 0].std() > 40.0, "a kimenetnek meg kell tartania a tónusmenetet"
        assert len(np.unique(eredmeny.reshape(-1, 3), axis=0)) > 20

    @pytest.mark.parametrize(
        ("bemenet", "vart"),
        [(16, (0, 16, 65)), (128, (69, 147, 195)), (248, (231, 255, 255))],
    )
    def test_mert_golden_harmasok(self, bemenet, vart):
        """A #685 `picniktint__alap.jpg` golden párjából mért mediánok."""
        eredmeny = apply_picnik_tint(_lapos(bemenet), color=SZIN, fade=0.0)[0, 0]
        assert np.allclose(eredmeny, vart, atol=3), f"{tuple(int(c) for c in eredmeny)} != {vart}"


class TestFade:
    def test_fade_100_bajtra_valtozatlan(self):
        kep = _atmenet()
        np.testing.assert_array_equal(apply_picnik_tint(kep, color=SZIN, fade=100.0), kep)

    def test_a_fade_monoton_halvanyit(self):
        kep = _atmenet()
        forras = kep.astype(np.int32)
        tavolsagok = [
            float(np.abs(apply_picnik_tint(kep, color=SZIN, fade=f).astype(np.int32) - forras).mean())
            for f in (0.0, 25.0, 50.0, 75.0, 100.0)
        ]
        assert tavolsagok == sorted(tavolsagok, reverse=True), tavolsagok
        assert tavolsagok[-1] == 0.0


class TestSzin:
    def test_a_szin_kromaja_latszik(self):
        """Kék színnel a kék csatorna vezet, pirossal a piros."""
        kek = apply_picnik_tint(_lapos(128), color=(0, 0, 255), fade=0.0)[0, 0].astype(int)
        assert kek[2] > kek[0] and kek[2] > kek[1]
        piros = apply_picnik_tint(_lapos(128), color=(255, 0, 0), fade=0.0)[0, 0].astype(int)
        assert piros[0] > piros[1] and piros[0] > piros[2]

    def test_semleges_szurke_szinnel_alig_valtozik(self):
        """Szürke színnek nincs krómája — a kép lényegében a lumája marad."""
        kep = _atmenet()
        eredmeny = apply_picnik_tint(kep, color=(128, 128, 128), fade=0.0)
        varhato = luma(kep.astype(np.float32))
        assert float(np.abs(eredmeny[..., 0].astype(np.float32) - varhato).mean()) <= 1.5

    def test_nem_mutalja_a_bemenetet(self):
        kep = _atmenet()
        eredeti = kep.copy()
        apply_picnik_tint(kep, color=SZIN, fade=0.0)
        np.testing.assert_array_equal(kep, eredeti)
