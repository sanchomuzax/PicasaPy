"""#874: a `dir_tint` (Graduated Tint) visszafejtett natív modelljének őrei.

A modell a `0x008f9880` regisztráló callbackből és a `0x0090f470`
munkafüggvényből olvasva:

- az átmenet **elforgatható**: a szög a kiválasztott puck-koordinátából
  jön, `(puck − 0,5) × 30` **fokban** (tehát ±15°),
- a `[szűrő+0xc4]` **negyedválasztó egész** (0…3), nem fok,
- a `Feather` alsó korlátja **0,001**,
- a magba a `Shade` helyett **`1 − Shade`** megy,
- a tónusgörbe 256 elemű, `uint16` LUT, a képpont **értékére** indexelve,
- a színezés **szorzás** (`tone × szín / 256`), nem keverés a szín felé.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.dir_tint import (
    DIR_TINT_FEATHER_FLOOR,
    apply_dir_tint,
    dir_tint_ramp_table,
    dir_tint_tone_curve,
    dir_tint_tone_lut,
)


def _kep(value: int = 120, height: int = 40, width: int = 40) -> np.ndarray:
    """Egyenletes szürke próbakép."""
    return np.full((height, width, 3), value, dtype=np.uint8)


class TestTonusGorbe:
    def test_p_egynel_azonossag(self) -> None:
        x = np.linspace(0.0, 1.0, 17, dtype=np.float32)
        np.testing.assert_array_equal(dir_tint_tone_curve(x, 1.0), x)

    def test_vegpontok_rogzitettek(self) -> None:
        # A·B = 1 azonosan, ezért y(0) = 0 és y(1) = 1 minden p-re.
        for p in (0.01, 0.5, 2.0, 100.0):
            y = dir_tint_tone_curve(np.array([0.0, 1.0], dtype=np.float32), p)
            assert abs(float(y[0])) < 1e-5
            assert abs(float(y[1]) - 1.0) < 1e-5

    def test_p_egynel_a_lut_azonossag(self) -> None:
        # a képpont-ciklus a felső bájtot olvassa: LUT[i] >> 8 == i
        lut = dir_tint_tone_lut(1.0)
        assert lut.dtype == np.uint16
        assert lut.shape == (256,)
        np.testing.assert_array_equal(lut >> 8, np.arange(256, dtype=np.uint16))

    def test_nagy_p_sotetit(self) -> None:
        # Shade = 1 → q = 0,01 → p = 100: a görbe erősen lefelé hajlít
        lut = dir_tint_tone_lut(100.0)
        assert int(lut[128]) >> 8 < 10


class TestRampaTabla:
    def test_384_bejegyzes_0_tol_255_ig(self) -> None:
        table = dir_tint_ramp_table()
        assert table.shape == (384,)
        assert int(table[0]) == 0
        assert int(table[-1]) == 255

    def test_monoton_no(self) -> None:
        table = dir_tint_ramp_table().astype(int)
        assert all(a <= b for a, b in zip(table, table[1:], strict=False))


class TestFeatherPadlo:
    def test_a_padlo_0_001(self) -> None:
        assert DIR_TINT_FEATHER_FLOOR == pytest.approx(0.001)

    def test_nulla_feather_ugyanaz_mint_a_padlo(self) -> None:
        image = _kep()
        nulla = apply_dir_tint(
            image, x=0.5, y=0.5, gradient=0.0, shade=0.8, color=(255, 255, 255)
        )
        padlo = apply_dir_tint(
            image,
            x=0.5,
            y=0.5,
            gradient=DIR_TINT_FEATHER_FLOOR,
            shade=0.8,
            color=(255, 255, 255),
        )
        np.testing.assert_array_equal(nulla, padlo)

    def test_a_padlo_eles_hatart_ad(self) -> None:
        # 0,001-es átmenettel a lépésvektor akkora, hogy a rámpa a
        # középpont körül azonnal telítődik: felül teljes hatás, alul semmi
        image = _kep(200, height=40, width=8)
        result = apply_dir_tint(
            image, x=0.5, y=0.5, gradient=0.0, shade=1.0, color=(255, 255, 255)
        )
        assert int(result[0, 4, 0]) < 20
        np.testing.assert_array_equal(result[-1], image[-1])


class TestShadeMegforditva:
    def test_shade_nulla_semleges_szinnel_valtozatlan(self) -> None:
        # Shade = 0 → q = 1 → p = 1 → a tónusgörbe AZONOSSÁG; fehér
        # színnel a natív a szorzást is kihagyja, tehát a kép változatlan
        image = _kep(137)
        result = apply_dir_tint(
            image, x=0.5, y=0.5, gradient=0.25, shade=0.0, color=(255, 255, 255)
        )
        np.testing.assert_array_equal(result, image)

    def test_shade_nulla_szines_tinttel_MEG_szoroz(self) -> None:
        # A natív magban a szorzó színezés nem függ a Shade-től: az egyetlen
        # kapuja a `cmp dword ptr [esp+0x3e8], 0xffffff` (`0x0090f525`).
        # A referencia-mérőszett csak fehér színt tartalmaz, ezért ezt az
        # ágat MÉRÉS nem, csak a diszasszemblátum támasztja alá.
        image = _kep(137)
        result = apply_dir_tint(
            image, x=0.5, y=0.5, gradient=0.25, shade=0.0, color=(0x00, 0x80, 0xFF)
        )
        assert not np.array_equal(result, image)
        # alul a súly nulla → ott a szorzás sem látszik
        np.testing.assert_array_equal(result[-1], image[-1])

    def test_shade_egy_a_legerosebb(self) -> None:
        image = _kep(180)
        eltero = [
            float(
                np.abs(
                    apply_dir_tint(
                        image,
                        x=0.5,
                        y=0.5,
                        gradient=0.5,
                        shade=shade,
                        color=(255, 255, 255),
                    ).astype(float)
                    - image.astype(float)
                ).mean()
            )
            for shade in (0.0, 0.25, 0.5, 0.75, 1.0)
        ]
        assert all(a < b for a, b in zip(eltero, eltero[1:], strict=False))


class TestPuckX:
    def test_ketto_kulonbozo_x_kulonbozo_kepet_ad(self) -> None:
        # ez fogja meg az `x` elhagyását: a régi modell mindkettőre
        # BITRE azonos képet adott
        image = np.tile(
            np.arange(64, dtype=np.uint8).reshape(1, 64, 1) * 3, (64, 1, 3)
        )
        balra = apply_dir_tint(
            image, x=0.0, y=0.5, gradient=0.5, shade=0.9, color=(255, 255, 255)
        )
        jobbra = apply_dir_tint(
            image, x=1.0, y=0.5, gradient=0.5, shade=0.9, color=(255, 255, 255)
        )
        assert not np.array_equal(balra, jobbra)

    def test_a_szog_a_puck_x_bol_jon(self) -> None:
        # x = 0,5 → 0°: az átmenet vízszintes sávokból áll, tehát egy soron
        # belül a súly állandó; x ≠ 0,5 → a sor mentén változik
        image = _kep(150, height=64, width=64)
        egyenes = apply_dir_tint(
            image, x=0.5, y=0.5, gradient=0.5, shade=0.9, color=(255, 255, 255)
        )
        assert len(np.unique(egyenes[20, :, 0])) == 1
        ferde = apply_dir_tint(
            image, x=1.0, y=0.5, gradient=0.5, shade=0.9, color=(255, 255, 255)
        )
        assert len(np.unique(ferde[20, :, 0])) > 1


class TestIrany:
    def test_negyedek_kulonbozo_kepet_adnak(self) -> None:
        image = _kep(150, height=48, width=64)
        kepek = [
            apply_dir_tint(
                image,
                x=0.5,
                y=0.5,
                gradient=0.5,
                shade=0.9,
                color=(255, 255, 255),
                direction=direction,
            )
            for direction in range(4)
        ]
        for first in range(4):
            for second in range(first + 1, 4):
                assert not np.array_equal(kepek[first], kepek[second])

    def test_a_menetirany_negyedenkent(self) -> None:
        # 0 → felül hat, 2 → alul; 1 → balra, 3 → jobbra
        # (a páratlan negyed felcseréli a lépésvektort, a 3-as előjelet is vált)
        image = _kep(200, height=48, width=48)
        felso = lambda kep: float(kep[:8].mean())  # noqa: E731
        also = lambda kep: float(kep[-8:].mean())  # noqa: E731
        bal = lambda kep: float(kep[:, :8].mean())  # noqa: E731
        jobb = lambda kep: float(kep[:, -8:].mean())  # noqa: E731
        hat = dict(
            x=0.5, y=0.5, gradient=0.5, shade=0.9, color=(255, 255, 255)
        )
        assert felso(apply_dir_tint(image, direction=0, **hat)) < also(
            apply_dir_tint(image, direction=0, **hat)
        )
        assert also(apply_dir_tint(image, direction=2, **hat)) < felso(
            apply_dir_tint(image, direction=2, **hat)
        )
        assert bal(apply_dir_tint(image, direction=1, **hat)) < jobb(
            apply_dir_tint(image, direction=1, **hat)
        )
        assert jobb(apply_dir_tint(image, direction=3, **hat)) < bal(
            apply_dir_tint(image, direction=3, **hat)
        )

    def test_minusz_egy_nullat_jelent(self) -> None:
        image = _kep(150)
        hat = dict(
            x=0.5, y=0.5, gradient=0.5, shade=0.9, color=(255, 255, 255)
        )
        np.testing.assert_array_equal(
            apply_dir_tint(image, direction=-1, **hat),
            apply_dir_tint(image, direction=0, **hat),
        )


class TestSzorzoSzinezes:
    def test_a_szin_szoroz_nem_kever(self) -> None:
        # a szín felé keverés VILÁGOSÍTANA a piros csatornán;
        # a szorzás csak sötétíthet
        image = _kep(60, height=16, width=8)
        result = apply_dir_tint(
            image, x=0.5, y=0.5, gradient=1.0, shade=0.5, color=(0xFF, 0x00, 0x00)
        )
        assert int(result[0, 4, 0]) <= 60
        # a felső szélen a súly 250/256 (a rámpa ott még nem telített),
        # ezért a kioltott csatornákon 1 egységnyi maradék marad
        assert int(result[0, 4, 1]) <= 2
        assert int(result[0, 4, 2]) <= 2

    def test_a_feher_szin_nem_szoroz(self) -> None:
        # a natív `cmp [esp+0x3e8], 0xffffff` a tiszta fehérnél kihagyja a
        # szorzást — ez 1 egységnyi különbség a 254/255-ös osztásnál
        image = _kep(255, height=8, width=8)
        result = apply_dir_tint(
            image, x=0.5, y=0.5, gradient=1.0, shade=0.0, color=(255, 255, 255)
        )
        np.testing.assert_array_equal(result, image)


class TestAlapok:
    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _kep(60, height=16, width=8)
        original = image.copy()
        apply_dir_tint(
            image, x=0.5, y=0.5, gradient=0.3, shade=0.7, color=(255, 0, 0)
        )
        np.testing.assert_array_equal(image, original)

    def test_hibas_kepre_valueerror(self) -> None:
        with pytest.raises(ValueError):
            apply_dir_tint(
                np.zeros((4, 4), dtype=np.uint8),
                x=0.5,
                y=0.5,
                gradient=0.25,
                shade=0.5,
                color=(255, 255, 255),
            )
