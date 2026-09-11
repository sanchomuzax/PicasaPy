"""#619: a szépia TELJES algoritmusa, egész aritmetikával.

A szűrő visszafejtése (#617) zárt képletet adott — **nincs benne illesztés, se
kalibrációs bizonytalanság**, csak egész szorzók:

1. `gray = (77R + 151G + 28B) >> 8` — az együtthatók összege pontosan 256;
2. `base = 255 − (((255 − gray) * 218) >> 8)` — invertálás, halványítás,
   visszainvertálás; a `gray = 0` így **38**-at ad (a feketék megemelve);
3. OVERLAY-keverés a fix `(155, 125, 99)` tintával: `base < 128` esetén
   multiply, egyébként screen.

⚠️ **Az egész aritmetika a lényeg.** A `>> 8` és a `* 218` lebegőpontos
megfelelője máshol kerekít, és a kimenet ±1-gyel elcsúszik — ezért mér ez a
lap MINTAPONTRA PONTOS egyezést, nem tűréssel.

A referenciaképes egyezést a `test_szepia_referencia_619` méri (privát
referencia-készlet kell hozzá), ez a lap a KÉPLETET.
"""

from __future__ import annotations

import numpy as np
import pytest
from picasapy.render.color import apply_sepia, sepia_lut_array

#: A jegyben megadott öt mintapont — a tábla ezeket PONTOSAN adja.
MINTAPONTOK = (
    (0, (46, 37, 29)),
    (64, (112, 90, 71)),
    (128, (171, 146, 124)),
    (192, (214, 202, 191)),
    (255, (255, 255, 255)),
)


def _folt(szin, meret=(4, 4)) -> np.ndarray:
    kep = np.zeros((*meret, 3), np.uint8)
    kep[:, :] = szin
    return kep


class TestATabla:
    @pytest.mark.parametrize("gray,vart", MINTAPONTOK)
    def test_az_ot_mintapont_PONTOS(self, gray, vart):
        assert tuple(int(v) for v in sepia_lut_array()[gray]) == vart

    def test_a_tabla_alakja(self):
        tabla = sepia_lut_array()
        assert tabla.shape == (256, 3)
        assert tabla.dtype == np.uint8

    def test_MONOTON_mindhárom_csatornán(self):
        """Világosabb szürke sosem adhat sötétebb kimenetet."""
        tabla = sepia_lut_array().astype(int)
        for csatorna in range(3):
            kulonbsegek = np.diff(tabla[:, csatorna])
            assert (kulonbsegek >= 0).all(), f"{csatorna}. csatorna nem monoton"

    def test_a_FEKETE_meg_van_emelve(self):
        """A 2. lépés lényege: `gray = 0` → `base = 38`, nem 0. Ez adja a
        szépia „poros" alját — egy sima színezés itt 0-t adna."""
        assert int(sepia_lut_array()[0].max()) == 46
        assert 255 - (((255 - 0) * 218) >> 8) == 38

    def test_a_TINTA_sorrendje_R_nagyobb_G_nagyobb_B(self):
        tabla = sepia_lut_array().astype(int)
        # a 255 a felső fixpont (mindhárom 255), ott nincs sorrend
        for gray in range(255):
            r, g, b = tabla[gray]
            assert r >= g >= b, f"gray={gray}: {r} {g} {b}"

    def test_az_EGESZ_aritmetika_nem_lebegopontos(self):
        """Ha a `>> 8` helyére kerekítő `/ 256` kerülne, a kimenet elcsúszna.

        MÉRVE: a 256 szürke-értékből **127-nél** tér el a csonkoló eltolás a
        kerekítő osztástól — nem peremeset, hanem a bemenetek fele. A
        legkisebb ilyen a `gray = 3` (egész 41, lebegőpontos 40), és a tábla
        ott az EGÉSZ ágat követi."""
        eltero = [
            gray
            for gray in range(256)
            if (255 - (((255 - gray) * 218) >> 8))
            != (255 - round((255 - gray) * 218 / 256))
        ]
        assert len(eltero) == 127
        assert eltero[0] == 3

        gray = 3
        base_egesz = 255 - (((255 - gray) * 218) >> 8)
        assert base_egesz == 41
        assert int(sepia_lut_array()[gray][0]) == (2 * base_egesz * 155) >> 8


class TestAzEffekt:
    def test_a_szurkearnyalat_EGESZ_sulyokkal(self):
        """`(77, 151, 28) >> 8` — az összeg pontosan 256, nincs erősítés."""
        assert 77 + 151 + 28 == 256
        be = _folt((10, 200, 90))
        gray = (77 * 10 + 151 * 200 + 28 * 90) >> 8
        assert np.array_equal(
            apply_sepia(be)[0, 0], sepia_lut_array()[gray]
        )

    @pytest.mark.parametrize("gray,vart", MINTAPONTOK)
    def test_a_szurke_bemenet_a_mintapontra_kepez(self, gray, vart):
        """Szürke bemeneten a luma maga a szürke (az összeg 256)."""
        assert tuple(int(v) for v in apply_sepia(_folt(gray))[0, 0]) == vart

    def test_a_kimenet_uint8(self):
        assert apply_sepia(_folt(100)).dtype == np.uint8

    def test_a_bemenetet_nem_irja_at(self):
        be = _folt((10, 200, 90))
        masolat = be.copy()
        apply_sepia(be)
        assert np.array_equal(be, masolat)

    def test_a_MONOKROM_tonus_sorrend(self):
        """Bármilyen színes bemenet R > G > B tónust ad (a tinta miatt)."""
        eredmeny = apply_sepia(_folt((30, 180, 60)))[0, 0].astype(int)
        assert eredmeny[0] > eredmeny[1] > eredmeny[2]
