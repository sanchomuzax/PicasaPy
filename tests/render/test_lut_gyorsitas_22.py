"""#22 — a négy csatornánkénti LUT-os szűrő gyors, BITRE azonos útja.

## A lelet

A #22 mérése (`docs/benchmarks/2026-09-18-cpu-eloonezet-kesleltetes-22.md`)
szerint az `autocontrast`, `colortemp`, `enhance` és `warm` a célgépen
100 ms fölött fut az előnézeti felbontáson. Mind a négy **csatornánkénti
256-os táblázat**: a költség nem a számításé, hanem az alkalmazásé — a
numpy-indexelés 2560 × 1707 képponton ~100 ms, az OpenCV `LUT`-ja
ugyanerre néhány ms.

## Amit ez a fájl őriz

1. az új `apply_channel_luts` **bitre** ugyanazt adja, mint a régi
   numpy-út (a régi kód itt, szó szerint, mérceként él);
2. a `colortemp` táblázatos útja bitre ugyanazt adja, mint a képpontonkénti
   natív képlet (szintén szó szerint, mérceként);
3. az új út **mérhetően gyorsabb** — különben a jegy célja nem teljesül.
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from picasapy.render.curves import apply_channel_luts
from picasapy.render.native_colortemp import apply_native_colortemp


def _regi_apply_channel_luts(image, luts):
    """A #22 előtti megvalósítás, szó szerint — ez a mérce."""
    channels = []
    for index, lut in enumerate(luts):
        table = np.clip(np.rint(lut), 0, 255).astype(np.uint8)
        channels.append(table[image[..., index]])
    return np.stack(channels, axis=-1)


_LEVELS = np.arange(256, dtype=np.int64)
_PARABOLA = _LEVELS * (256 - _LEVELS)


def _regi_colortemp(image, cool_to_warm, white_shift):
    """A #22 előtti képpontonkénti natív képlet, szó szerint — a mérce."""
    warm = int(cool_to_warm * 256.0)
    shift = min(max(int(white_shift * 128.0), 0), 255)
    if warm == 0 and shift == 0:
        return image.copy()
    span = 256 - shift
    down = (_LEVELS * span) >> 8
    up = np.clip((_LEVELS * (65536 // span)) >> 8, 0, 255)
    warm_green = warm if warm >= 1 else 0
    values = image.astype(np.int64)
    red, green, blue = (down[values[..., c]] for c in range(3))
    shifted = (
        np.clip(red + ((_PARABOLA[red] * warm) >> 15), 0, 255),
        np.clip(green + ((_PARABOLA[green] * warm_green) >> 17), 0, 255),
        np.clip(blue - ((_PARABOLA[blue] * warm) >> 15), 0, 255),
    )
    return np.stack([up[c] for c in shifted], axis=-1).astype(np.uint8)


def _kep(magvet: int, magassag: int = 37, szelesseg: int = 53) -> np.ndarray:
    rng = np.random.default_rng(magvet)
    return rng.integers(0, 256, size=(magassag, szelesseg, 3), dtype=np.uint8)


def _lutok(magvet: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Tartományon kívüli és pontosan ,5-re eső értékek is — a kerekítés
    és a vágás is ugyanúgy kell menjen."""
    rng = np.random.default_rng(magvet)
    lutok = []
    for _ in range(3):
        lut = rng.uniform(-40.0, 300.0, 256)
        lut[::7] = np.floor(lut[::7]) + 0.5
        lutok.append(lut)
    return tuple(lutok)


class TestACsatornankentiLUTBitreAzonos:
    @pytest.mark.parametrize("magvet", range(6))
    def test_veletlen_kepen_es_LUT_okon(self, magvet):
        kep, lutok = _kep(magvet), _lutok(magvet + 100)
        assert np.array_equal(
            apply_channel_luts(kep, lutok), _regi_apply_channel_luts(kep, lutok)
        )

    def test_nem_folytonos_nezeten_is(self):
        """A lánc köztes képe lehet szeletelt nézet — a gyors út sem
        tételezheti fel a folytonos memóriát."""
        kep = _kep(9, 40, 80)[:, ::3]
        assert not kep.flags["C_CONTIGUOUS"]
        lutok = _lutok(11)
        assert np.array_equal(
            apply_channel_luts(kep, lutok), _regi_apply_channel_luts(kep, lutok)
        )

    def test_a_bemenetet_nem_irja_at(self):
        kep = _kep(3)
        eredeti = kep.copy()
        apply_channel_luts(kep, _lutok(4))
        assert np.array_equal(kep, eredeti)


class TestAColortempBitreAzonos:
    @pytest.mark.parametrize("hideg_meleg", [-0.5, -0.31, -0.004, 0.0, 0.003, 0.125, 0.5, 0.7])
    @pytest.mark.parametrize("feher", [0.0, 0.25, 0.5, 1.0, 1.9, -0.2])
    def test_a_parameter_racson(self, hideg_meleg, feher):
        kep = _kep(21)
        assert np.array_equal(
            apply_native_colortemp(kep, hideg_meleg, feher),
            _regi_colortemp(kep, hideg_meleg, feher),
        )


def _median_ido(fuggveny, ismetles: int = 3) -> float:
    idok = []
    for _ in range(ismetles):
        kezdet = time.perf_counter()
        fuggveny()
        idok.append(time.perf_counter() - kezdet)
    return sorted(idok)[len(idok) // 2]


class TestAGyorsUtTenylegGyorsabb:
    """Relatív mérés, nem abszolút: a CI-gépek sebessége ingadozik, a két
    út aránya viszont nem. A mért arány a célgépen ~20×; a próba csak 3×-t
    követel, hogy a zaj ne buktassa."""

    KEP = np.random.default_rng(5).integers(0, 256, size=(854, 1280, 3), dtype=np.uint8)

    def test_a_csatornankenti_LUT(self):
        lutok = _lutok(1)
        uj = _median_ido(lambda: apply_channel_luts(self.KEP, lutok))
        regi = _median_ido(lambda: _regi_apply_channel_luts(self.KEP, lutok))
        assert uj * 3 < regi, f"új {uj*1000:.1f} ms, régi {regi*1000:.1f} ms"

    def test_a_colortemp(self):
        uj = _median_ido(lambda: apply_native_colortemp(self.KEP, 0.125, 0.5))
        regi = _median_ido(lambda: _regi_colortemp(self.KEP, 0.125, 0.5))
        assert uj * 3 < regi, f"új {uj*1000:.1f} ms, régi {regi*1000:.1f} ms"


class TestAHisztogramBitreAzonos:
    """Az `enhance` és az `autocontrast` idejének nagyobbik része a három
    hisztogram. Az OpenCV `calcHist` float32-t ad, ami 2^24 fölött már nem
    pontos egész — ezért sávokban számol, és egészben összegez."""

    @pytest.mark.parametrize("magvet", range(4))
    def test_ugyanaz_mint_a_bincount(self, magvet):
        from picasapy.render import ops

        kep = _kep(magvet, 61, 47)[3:, 5:]
        for csatorna in range(3):
            assert np.array_equal(
                ops._channel_histograms(kep)[csatorna],
                np.bincount(kep[..., csatorna].reshape(-1), minlength=256),
            )

    def test_savokra_bontva_is_pontos(self, monkeypatch):
        """A sávhatárt kicsire állítva a több sávos út is lefut."""
        from picasapy.render import ops

        monkeypatch.setattr(ops, "_HISZTOGRAM_SAV_KEPPONT", 100)
        kep = _kep(8, 33, 29)
        for csatorna in range(3):
            assert np.array_equal(
                ops._channel_histograms(kep)[csatorna],
                np.bincount(kep[..., csatorna].reshape(-1), minlength=256),
            )

    def test_egyszinu_nagy_kep_nem_veszit_darabot(self):
        """Egyetlen rekeszbe 2^24-nél több képpont: float32-ben itt
        csúszna el a darabszám."""
        from picasapy.render import ops

        kep = np.full((4200, 4100, 3), 77, dtype=np.uint8)
        assert int(ops._channel_histograms(kep)[1][77]) == 4200 * 4100


class TestSzelsoMeretek:
    """Az átnézés lelete: a `cv2.LUT` nulla kiterjedésű képre `None`-t ad
    (a `display_modes._tablat_alkalmaz` ugyanezért véd); a régi numpy-út
    üres tömböt adott."""

    @pytest.mark.parametrize("alak", [(0, 5, 3), (4, 0, 3), (0, 0, 3)])
    def test_ures_kepre_ures_tomb(self, alak):
        kep = np.zeros(alak, dtype=np.uint8)
        eredmeny = apply_channel_luts(kep, _lutok(2))
        assert eredmeny.shape == alak
        assert apply_native_colortemp(kep, 0.125, 0.5).shape == alak

    def test_a_savnal_szelesebb_kep_is_pontos(self, monkeypatch):
        """Ha egyetlen sor is több képpont a sáv-korlátnál, a sort is
        darabolni kell — különben egy float32 rekesz túlcsordulhat."""
        from picasapy.render import ops

        import cv2 as valodi_cv2

        meretek: list[int] = []

        class Figyelo:
            @staticmethod
            def calcHist(kepek, *args):
                meretek.append(kepek[0].shape[0] * kepek[0].shape[1])
                return valodi_cv2.calcHist(kepek, *args)

        monkeypatch.setattr(ops, "_HISZTOGRAM_SAV_KEPPONT", 10)
        monkeypatch.setattr(ops, "cv2", Figyelo)
        kep = _kep(12, 3, 37)
        eredmeny = ops._channel_histograms(kep)
        assert meretek and max(meretek) <= 10, meretek
        for csatorna in range(3):
            assert np.array_equal(
                eredmeny[csatorna],
                np.bincount(kep[..., csatorna].reshape(-1), minlength=256),
            )
