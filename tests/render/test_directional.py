"""#623: a `dir_*` irányított effektcsalád — a natív magokból.

A vázat (`s(x,y) = a·(2x/W − 1) + b·(2y/H − 1)`) a `dir_brite` natív magja
(`0x0090d8b0`) mutatja explicit módon; a két művelet pixelképlete a
`0x0090dbb0` és `0x0090d8b0` dekompilátumából származik. Ld.
`docs/specs/picasa-native-filter-workers.md` 2.7.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.directional import (
    apply_dir_brite,
    apply_dir_sat,
    directional_ramp,
)


def _egyszinu(color: tuple[int, int, int] = (150, 100, 80)) -> np.ndarray:
    return np.full((40, 60, 3), color, dtype=np.uint8)


class TestDirectionalRamp:
    def test_a_kep_kozepere_szimmetrikus(self) -> None:
        ramp = directional_ramp(40, 60, 1.0, 0.0)
        assert ramp[0, 0] == pytest.approx(-1.0)
        # a natív rámpa a `[0, W)` egészek felett fut: a nulla pontosan a
        # középső oszlopra esik, a jobb szél ezért egy lépéssel 1 alatt áll
        assert ramp[0, 29] < 0.0
        assert ramp[0, 30] == pytest.approx(0.0)
        assert ramp[0, -1] == pytest.approx(1.0 - 2.0 / 60)

    def test_a_ket_tengely_fuggetlen(self) -> None:
        """`a=1, b=0` → csak vízszintesen változik; `a=0, b=1` → csak
        függőlegesen. Ez a feliratok („Balról jobbra", „Felülről lefelé")
        közvetlen következménye."""
        vizszintes = directional_ramp(40, 60, 1.0, 0.0)
        fuggoleges = directional_ramp(40, 60, 0.0, 1.0)
        assert np.ptp(vizszintes[:, 0]) == 0.0
        assert np.ptp(fuggoleges[0, :]) == 0.0
        assert np.ptp(vizszintes[0, :]) > 1.9
        assert np.ptp(fuggoleges[:, 0]) > 1.9

    def test_a_parametereket_a_natv_kod_bevagja(self) -> None:
        """A mag maga vágja `[-1, 1]`-re — a túlcsordult érték nem erősít."""
        assert np.array_equal(
            directional_ramp(8, 8, 5.0, 0.0), directional_ramp(8, 8, 1.0, 0.0)
        )

    def test_ervenytelen_meret(self) -> None:
        with pytest.raises(ValueError):
            directional_ramp(0, 10, 0.0, 0.0)


class TestDirSat:
    def test_nulla_parameter_azonossag(self) -> None:
        image = _egyszinu()
        assert np.array_equal(apply_dir_sat(image, 0.0, 0.0), image)

    def test_egyik_oldal_telitetlenit_a_masik_telit(self) -> None:
        image = _egyszinu()
        result = apply_dir_sat(image, 1.0, 0.0)
        bal, jobb = result[0, 0], result[0, -1]
        # a bal szélen a súly −256: a képpont a lumára esik (szürke)
        assert bal[0] == bal[1] == bal[2]
        # a jobb szélen viszont szétnyílnak a csatornák
        assert int(jobb[0]) - int(jobb[2]) > int(image[0, 0, 0]) - int(image[0, 0, 2])

    def test_a_luma_sulyozas_nem_a_deritofenye(self) -> None:
        """`(2R + 5G + B) >> 3`, NEM `(B + 2G + R) >> 2`. Egy tiszta zöld
        képpont a két képlettel érdemben más szürkét adna."""
        image = np.full((20, 20, 3), (0, 200, 0), dtype=np.uint8)
        # a bal szélen a rámpa −1: ott esik a képpont a lumára
        szurke = apply_dir_sat(image, 1.0, 0.0)[0, 0]
        assert szurke[0] == szurke[1] == szurke[2]
        assert int(szurke[0]) == (5 * 200) // 8  # 125, nem (2*200)//4 = 100

    def test_fuggolegesen_allando_vizszintes_ramponal(self) -> None:
        result = apply_dir_sat(_egyszinu(), 1.0, 0.0)
        assert np.array_equal(result[0], result[-1])


class TestDirBrite:
    def test_nulla_parameter_azonossag(self) -> None:
        image = _egyszinu()
        assert np.array_equal(apply_dir_brite(image, 0.0, 0.0), image)

    def test_egyik_oldal_sotetit_a_masik_vilagosit(self) -> None:
        image = _egyszinu()
        result = apply_dir_brite(image, 1.0, 0.0)
        assert int(result[0, 0].max()) < int(image[0, 0].max())
        assert int(result[0, -1].min()) > int(image[0, 0].min())

    def test_a_szelso_ertekek_gyakorlatilag_helyben_maradnak(self) -> None:
        """A köbös görbe a 0-t és a 255-öt (majdnem) fixen tartja.

        A natív `(v*v*v) >> 16` egész aritmetikája 255-re 252-t ad, nem
        255-öt — ezért a szélsőértékek **három szinten belül** mozdulnak
        csak. Ez a natív kód sajátja, nem a mi kerekítésünk: szándékosan
        NEM javítjuk ki.
        """
        fekete = np.zeros((16, 16, 3), dtype=np.uint8)
        feher = np.full((16, 16, 3), 255, dtype=np.uint8)
        assert int(apply_dir_brite(fekete, 1.0, 0.0).max()) <= 3
        assert int(apply_dir_brite(feher, 1.0, 0.0).min()) >= 252

    def test_monoton_a_rampa_menten(self) -> None:
        result = apply_dir_brite(_egyszinu(), 1.0, 0.0)[0, :, 0].astype(int)
        assert np.all(np.diff(result) >= 0)


class TestBajtraEgyezikANativval:
    """#623: a numpy-implementáció a natív EGÉSZ aritmetika lassú, hurkos
    újraírásával vetve — képpontra azonos, nem „közel".

    Ez az a teszt, ami a float/egész kerekítés elcsúszását elkapja: a natív
    magok `>> 8`-cal (padló) dolgoznak, nem kerekítéssel.
    """

    @staticmethod
    def _ramp(h: int, w: int, a: float, b: float, x: int, y: int, clamp: bool) -> float:
        a = max(-1.0, min(1.0, a))
        b = max(-1.0, min(1.0, b))
        s = a * (2.0 * x / w - 1.0) + b * (2.0 * y / h - 1.0)
        return max(-1.0, min(1.0, s)) if clamp else s

    @classmethod
    def _ref_dir_sat(cls, img: np.ndarray, a: float, b: float) -> np.ndarray:
        h, w = img.shape[:2]
        out = np.empty_like(img)
        for y in range(h):
            for x in range(w):
                weight = int(np.round(cls._ramp(h, w, a, b, x, y, False) * 256))
                r, g, bl = (int(v) for v in img[y, x])
                luma = (2 * r + 5 * g + bl) >> 3
                out[y, x] = [
                    max(0, min(255, c + ((c - luma) * weight) // 256))
                    for c in (r, g, bl)
                ]
        return out

    @classmethod
    def _ref_dir_brite(cls, img: np.ndarray, a: float, b: float) -> np.ndarray:
        h, w = img.shape[:2]
        out = np.empty_like(img)
        for y in range(h):
            for x in range(w):
                s = cls._ramp(h, w, a, b, x, y, True)
                amount = abs(int(np.round(s * 256)))
                rest = 256 - amount
                pixel = []
                for c in (int(img[y, x, 0]), int(img[y, x, 1]), int(img[y, x, 2])):
                    v = c ^ 0xFF if s >= 0 else c
                    v = (((v * v * v) >> 16) * amount + rest * v) >> 8
                    if s >= 0:
                        v ^= 0xFF
                    pixel.append(max(0, min(255, v)))
                out[y, x] = pixel
        return out

    @pytest.mark.parametrize(
        "horizontal,vertical",
        [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.6, -0.4), (0.0, 0.0), (1.0, 1.0)],
    )
    def test_dir_sat_bajtra(self, horizontal: float, vertical: float) -> None:
        image = np.random.default_rng(5).integers(0, 256, size=(12, 16, 3), dtype=np.uint8)
        np.testing.assert_array_equal(
            apply_dir_sat(image, horizontal, vertical),
            self._ref_dir_sat(image, horizontal, vertical),
        )

    @pytest.mark.parametrize(
        "horizontal,vertical",
        [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.6, -0.4), (0.0, 0.0), (1.0, 1.0)],
    )
    def test_dir_brite_bajtra(self, horizontal: float, vertical: float) -> None:
        image = np.random.default_rng(5).integers(0, 256, size=(12, 16, 3), dtype=np.uint8)
        np.testing.assert_array_equal(
            apply_dir_brite(image, horizontal, vertical),
            self._ref_dir_brite(image, horizontal, vertical),
        )
