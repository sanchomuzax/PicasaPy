"""A Picasa 16 bites megjelenítési mód determinisztikus zajgenerátora."""

from __future__ import annotations

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.render.display_modes import (
    DITHER16_SEED,
    _MT_M,
    _MT_MATRIX_A,
    _MT_N,
    _MT_ONE,
    _MT_U32_MASK,
    _MT_UPPER_MASK,
    _MT_LOWER_MASK,
)
from picasapy.render.display_mode_pixels import _rgb_kep_e

class PicasaDitherGenerator:
    """A spec 5.3 szerinti MT19937-alakú, Picasa-maszkos generátor.

    Az inicializáló szorzó (`0x19660D`) és a két temperálómaszk eltér a
    klasszikus MT19937-től. A twist annak lépéseit követi. A `random_uint32`
    blokkonként temperálja az állapotot, hogy nagy képeknél se pixelenkénti
    Python-hívás legyen a renderelési út.
    """

    def __init__(self, seed: int = DITHER16_SEED) -> None:
        self._state = np.empty(_MT_N, dtype=np.uint32)
        self._state[0] = np.uint32(int(seed) & 0xFFFFFFFF)
        for index in range(1, _MT_N):
            elozo = int(self._state[index - 1])
            self._state[index] = np.uint32(
                (0x0019660D * (elozo ^ (elozo >> 30)) + index) & 0xFFFFFFFF
            )
        self._index = _MT_N

    def _twist(self) -> None:
        """624 állapotérték újratöltése a szabványos MT19937-twisttel."""
        regi = self._state
        uj = regi.copy()

        elso = np.arange(0, _MT_N - _MT_M)
        osszefuzes = (regi[elso] & _MT_UPPER_MASK) | (
            regi[elso + 1] & _MT_LOWER_MASK
        )
        uj[elso] = (
            regi[elso + _MT_M]
            ^ (osszefuzes >> _MT_ONE)
            ^ ((osszefuzes & _MT_ONE) * _MT_MATRIX_A)
        )

        masodik_elso = np.arange(_MT_N - _MT_M, 2 * (_MT_N - _MT_M))
        osszefuzes = (regi[masodik_elso] & _MT_UPPER_MASK) | (
            regi[masodik_elso + 1] & _MT_LOWER_MASK
        )
        uj[masodik_elso] = (
            uj[masodik_elso + _MT_M - _MT_N]
            ^ (osszefuzes >> _MT_ONE)
            ^ ((osszefuzes & _MT_ONE) * _MT_MATRIX_A)
        )

        # Az in-place MT-twist második fele már egymásra épül: i=454-től a
        # `i-227` forrás maga is a fenti szakaszban frissített elem. Két
        # adagban dolgozunk, így a numpy-vektoros lépés a ciklussorrendet is
        # bitre megtartja.
        masodik_masodik = np.arange(2 * (_MT_N - _MT_M), _MT_N - 1)
        osszefuzes = (regi[masodik_masodik] & _MT_UPPER_MASK) | (
            regi[masodik_masodik + 1] & _MT_LOWER_MASK
        )
        uj[masodik_masodik] = (
            uj[masodik_masodik + _MT_M - _MT_N]
            ^ (osszefuzes >> _MT_ONE)
            ^ ((osszefuzes & _MT_ONE) * _MT_MATRIX_A)
        )

        utolso_osszefuzes = (regi[_MT_N - 1] & _MT_UPPER_MASK) | (
            uj[0] & _MT_LOWER_MASK
        )
        uj[_MT_N - 1] = (
            uj[_MT_M - 1]
            ^ (utolso_osszefuzes >> _MT_ONE)
            ^ ((utolso_osszefuzes & _MT_ONE) * _MT_MATRIX_A)
        )

        self._state = uj
        self._index = 0

    @staticmethod
    def _temper(values: np.ndarray) -> np.ndarray:
        tempered = values.copy()
        tempered ^= tempered >> np.uint32(11)
        tempered ^= (tempered & np.uint32(0xFF3A58AD)) << np.uint32(7)
        tempered &= _MT_U32_MASK
        tempered ^= (tempered & np.uint32(0xFFFFDF8C)) << np.uint32(15)
        tempered &= _MT_U32_MASK
        tempered ^= tempered >> np.uint32(18)
        return tempered

    def random_uint32(self, count: int) -> np.ndarray:
        """`count` egymást követő, 32 bites temperált érték tömbje."""
        mennyiseg = max(0, int(count))
        eredmeny = np.empty(mennyiseg, dtype=np.uint32)
        kitoltott = 0
        while kitoltott < mennyiseg:
            if self._index == _MT_N:
                self._twist()
            adag = min(_MT_N - self._index, mennyiseg - kitoltott)
            nyers = self._state[self._index : self._index + adag]
            eredmeny[kitoltott : kitoltott + adag] = self._temper(nyers)
            self._index += adag
            kitoltott += adag
        return eredmeny


def apply_dither16(rgb: np.ndarray) -> np.ndarray:
    """A Picasa 16 bites, szemcsézett képernyőmódja (spec 5.3, 5.3/b).

    Minden forráspixelhez egy temperált 32 bites értéket kér a bizonyított
    `0x80AE2D6C` magú generátortól. A `0x00070307` maszk RGB-ben
    `(R:0…7, G:0…3, B:0…7)` zajt ad; a csatornánkénti összeadás telít.
    Minden kép saját, újraindított generátort kap, így a QML/thumbnail
    újrakérése ugyanazokat a pixeleket adja, és párhuzamos kérések sorrendje
    nem változtatja meg a képet.

    A bemenet `(H, W, 3)` uint8 RGB. Érvénytelen bemenet változatlanul
    visszatér; érvényes bemenetet sosem írunk át.
    """
    if not _rgb_kep_e(rgb):
        return rgb
    if rgb.size == 0:
        return rgb.copy()

    magassag, szelesseg = rgb.shape[:2]
    szavak = PicasaDitherGenerator().random_uint32(magassag * szelesseg)
    szavak = szavak.reshape((magassag, szelesseg))
    zaj = np.empty_like(rgb)
    zaj[:, :, 0] = ((szavak >> np.uint32(16)) & np.uint32(0x07)).astype(
        np.uint8
    )
    zaj[:, :, 1] = ((szavak >> np.uint32(8)) & np.uint32(0x03)).astype(
        np.uint8
    )
    zaj[:, :, 2] = (szavak & np.uint32(0x07)).astype(np.uint8)
    return cv2.add(rgb, zaj)
