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
