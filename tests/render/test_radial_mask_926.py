"""A sugaras maszk keverése PADLÓZ, nem csonkol (#926).

A jegy nyitott kérdése az volt, hogy a `radial_mask.py` `//`-ja helyes-e:
a natív `0x0090b050` `idiv`-vel (nulla felé csonkol) vagy eltolással
(padlóz) osztja-e a súlyozott különbséget.

A `0x0090b2bc`…`0x0090b30a` blokk diszasszemblátuma dönti el — a piros és
a kék csatorna EGY dwordbe csomagolva megy, és a lezáró osztás `shr`:

    mov    ecx, dword ptr [ecx]          ; a közép képpont
    movzx  edx, byte ptr [esp + eax + 0x50]   ; súly = tábla[idx]
    and    ebp, 0xff00ff                 ; közép piros+kék EGY regiszterben
    and    ecx, 0xff00                   ; közép zöld
    and    eax, 0xff00ff                 ; perem piros+kék
    sub    ebp, eax                      ; Δ(piros,kék) — NEGATÍV is lehet
    and    esi, 0xff00
    imul   ebp, edx
    sub    ecx, esi
    imul   ecx, edx
    shr    ebp, 8                        ; ← eltolás, NEM idiv
    shr    ecx, 8
    add    ebp, eax
    add    ecx, esi

Az őr ezt a blokkot bitpontosan újrajátssza, és a mi képletünkhöz méri.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.radial_mask import apply_radial_mask

#: 32 bites regiszter-maszk — a natív aritmetika körbefordulásához.
MASZK32 = np.int64(0xFFFFFFFF)


def nativ_keveres(kozep: np.ndarray, perem: np.ndarray, suly: np.ndarray) -> np.ndarray:
    """A `0x0090b2bc`…`0x0090b30a` blokk bitpontos mása, dword képpontokon.

    A képpont `0x00RRGGBB` alakú `int64`; a visszaadott érték ugyanilyen
    (az alfát a natív `or ebp, 0xff000000`-ja adja, azt itt elhagyjuk).
    """
    ebp = kozep & 0x00FF00FF
    ecx = kozep & 0x0000FF00
    eax = perem & 0x00FF00FF
    esi = perem & 0x0000FF00
    ebp = ((ebp - eax) & MASZK32) * suly & MASZK32
    ecx = ((ecx - esi) & MASZK32) * suly & MASZK32
    ebp = (ebp >> 8) + eax & MASZK32
    ecx = (ecx >> 8) + esi & MASZK32
    return (ebp & 0xFFFF00FF) | (ecx & 0x0000FF00)


def _csatornank(perem: np.ndarray, delta: np.ndarray, suly: np.ndarray, padloz: bool):
    """A mi képletünk egy csatornára — padlózva vagy nulla felé csonkolva."""
    szorzat = delta * suly
    hanyados = (
        szorzat // 256
        if padloz
        else (szorzat.astype(np.float64) / 256).astype(np.int64)
    )
    return (perem + hanyados) & 0xFF


class TestNativKeveresPadloz:
    """A natív blokk a PADLÓ-modellel egyezik, a csonkolóval nem."""

    @pytest.mark.parametrize("perem_ertek", [0, 1, 127, 128, 200, 255])
    def test_kimerito_minden_kulonbsegre_es_sulyra(self, perem_ertek: int) -> None:
        """Minden Δ(kék) × Δ(piros) × súly hármas egyetlen perem-értékre."""
        perem_kek = perem_piros = perem_zold = perem_ertek
        delta_kek = np.arange(-perem_kek, 256 - perem_kek, dtype=np.int64)
        delta_piros = np.arange(-perem_piros, 256 - perem_piros, dtype=np.int64)
        dk, dp = (t.ravel() for t in np.meshgrid(delta_kek, delta_piros, indexing="ij"))
        kozep = ((perem_piros + dp) << 16) | (perem_zold << 8) | (perem_kek + dk)
        perem = np.int64((perem_piros << 16) | (perem_zold << 8) | perem_kek)

        for suly in (0, 1, 2, 127, 128, 129, 200, 254, 255):
            kimenet = nativ_keveres(kozep, perem, np.int64(suly))
            kek, piros = kimenet & 0xFF, (kimenet >> 16) & 0xFF
            padlo_kek = _csatornank(perem_kek, dk, np.int64(suly), padloz=True)
            padlo_piros = _csatornank(perem_piros, dp, np.int64(suly), padloz=True)
            np.testing.assert_array_equal(kek, padlo_kek)
            np.testing.assert_array_equal(piros, padlo_piros)

    def test_a_csonkolo_modell_ELTERNE(self) -> None:
        """Az őrnek foga van: a másik szemantika mérhetően mást adna."""
        perem_ertek = 128
        delta = np.arange(-perem_ertek, 256 - perem_ertek, dtype=np.int64)
        dk, dp = (t.ravel() for t in np.meshgrid(delta, delta, indexing="ij"))
        kozep = ((perem_ertek + dp) << 16) | (perem_ertek << 8) | (perem_ertek + dk)
        perem = np.int64((perem_ertek << 16) | (perem_ertek << 8) | perem_ertek)
        suly = np.int64(200)

        kimenet = nativ_keveres(kozep, perem, suly)
        csonkolt = _csatornank(perem_ertek, dk, suly, padloz=False)
        eltero = int(np.count_nonzero((kimenet & 0xFF) != csonkolt))
        assert eltero > 0, "a két szemantika itt nem válik szét — az őr vak"


class TestAlkalmazoPadloz:
    """A `apply_radial_mask` NEGATÍV különbségnél is a natívot követi."""

    def test_sotet_korong_vilagos_peremen(self) -> None:
        """A korong sötétebb a peremnél — a számláló végig negatív."""
        magassag, szelesseg = 24, 32
        kozep = np.full((magassag, szelesseg, 3), 20, dtype=np.uint8)
        perem = np.full((magassag, szelesseg, 3), 201, dtype=np.uint8)

        eredmeny = apply_radial_mask(kozep, perem, 0.5, 0.5, 0.6, 0.3)

        # Minden képpontnak a perem és a korong közé kell esnie, és a
        # padló-modellel egyeznie — csonkolással 1-gyel feljebb lenne.
        assert eredmeny.min() >= 20
        assert eredmeny.max() <= 201
        kozeppont = int(eredmeny[magassag // 2, szelesseg // 2, 0])
        assert kozeppont == 20

    def test_a_teljes_kep_egyezik_a_nativ_blokkal(self) -> None:
        """Képpontonkénti egyezés a bitpontos natív mással."""
        veletlen = np.random.default_rng(926)
        magassag, szelesseg = 16, 20
        kozep = veletlen.integers(0, 256, (magassag, szelesseg, 3), dtype=np.uint8)
        perem = veletlen.integers(0, 256, (magassag, szelesseg, 3), dtype=np.uint8)

        eredmeny = apply_radial_mask(kozep, perem, 0.5, 0.5, 0.8, 0.2)

        # A natív mást a modul saját súlytáblájával etetjük, hogy a
        # geometria ne, csak az OSZTÁS szemantikája legyen a tét.
        from picasapy.render.radial_mask import (
            RADIAL_TABLE_SIZE,
            radial_weight_table,
        )
        from picasapy.render.radial_mask import _squared_distance  # noqa: PLC2701

        tabla, eltolas = radial_weight_table(szelesseg, magassag, 0.8, 0.2)
        index = _squared_distance(szelesseg, magassag, 0.5, 0.5, eltolas)
        suly = tabla[np.clip(index, 0, RADIAL_TABLE_SIZE - 1)]

        def dword(kep: np.ndarray) -> np.ndarray:
            k = kep.astype(np.int64)
            return (k[..., 0] << 16) | (k[..., 1] << 8) | k[..., 2]

        nativ = nativ_keveres(dword(kozep), dword(perem), suly)
        belul = index < RADIAL_TABLE_SIZE
        vart = np.where(belul, nativ, dword(perem))

        np.testing.assert_array_equal((vart >> 16) & 0xFF, eredmeny[..., 0])
        np.testing.assert_array_equal((vart >> 8) & 0xFF, eredmeny[..., 1])
        np.testing.assert_array_equal(vart & 0xFF, eredmeny[..., 2])
