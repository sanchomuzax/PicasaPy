"""#623: a `dir_*` irányított effektcsalád — a natív magokból.

A vázat (`s(x,y) = a·(2x/W − 1) + b·(2y/H − 1)`) a `dir_brite` natív magja
(`0x0090d8b0`) mutatja explicit módon; a két művelet pixelképlete a
`0x0090dbb0` és `0x0090d8b0` dekompilátumából származik. Ld.
`docs/specs/picasa-native-filter-workers.md` 2.7.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from picasapy.render.directional import (
    apply_dir_brite,
    apply_dir_sat,
    apply_dir_sharp,
    dir_sharp_amount,
    dir_sharp_blur_radius,
    directional_ramp,
    directional_weight,
)
from picasapy.render.iir_blur import apply_picasa_blur


def _egyszinu(color: tuple[int, int, int] = (150, 100, 80)) -> np.ndarray:
    return np.full((40, 60, 3), color, dtype=np.uint8)


class TestDirectionalRamp:
    def test_a_kep_kozepere_szimmetrikus(self) -> None:
        ramp = directional_ramp(40, 60, 1.0, 0.0)
        assert ramp[0, 0] == pytest.approx(-1.0)
        # a natív rámpa a `[0, W)` egészek felett fut: a nulla a
        # középső oszlopra esik, a jobb szél ezért egy lépéssel 1 alatt áll
        assert ramp[0, 29] < 0.0
        # a natív float32 akkumulátor kerekítési hibát halmoz (#3859): a
        # középső oszlop nem PONTOSAN nulla, csak float32-pontosságon belül
        assert ramp[0, 30] == pytest.approx(0.0, abs=1e-6)
        assert ramp[0, -1] == pytest.approx(1.0 - 2.0 / 60, abs=1e-6)

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
        # a bal szélen a súly −128 (#3859): a csatornák FÉLÚTON közelítenek
        # a lumához — összeszűkülnek, de nem esnek egybe
        eredeti_szoras = int(image[0, 0, 0]) - int(image[0, 0, 2])
        assert 0 < int(bal[0]) - int(bal[2]) < eredeti_szoras
        # a jobb szélen viszont szétnyílnak a csatornák
        assert int(jobb[0]) - int(jobb[2]) > int(image[0, 0, 0]) - int(image[0, 0, 2])

    def test_a_luma_sulyozas_nem_a_deritofenye(self) -> None:
        """`(2R + 5G + B) >> 3`, NEM `(B + 2G + R) >> 2`. Egy tiszta zöld
        képpont a két képlettel érdemben más szürkét adna."""
        image = np.full((20, 20, 3), (0, 200, 0), dtype=np.uint8)
        # a bal felső sarokban `a = b = 1` mellett a súly −256 (#3859): ott
        # esik a képpont a lumára
        szurke = apply_dir_sat(image, 1.0, 1.0)[0, 0]
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


def _zajos(height: int = 40, width: int = 60) -> np.ndarray:
    """Zajos kép: van rajta mit élesíteni MINDEN pozíción."""
    rng = np.random.default_rng(7)
    return rng.integers(40, 210, size=(height, width, 3), dtype=np.uint8)


class TestDirSharp:
    """#623: irányított unsharp mask — a natív `0x0090d600` mag.

    A burkoló (`0x008f9090`) egy `min(W, H) / 8` sugarú, KÜLÖN menetben
    készült elmosást ad a magnak; a mag maga csak összevon.
    """

    def test_a_burkolo_elmosasi_sugara(self) -> None:
        """`uVar1 = min(W, H) >> 3; if (uVar1 == 0) uVar1 = 1;`"""
        assert dir_sharp_blur_radius(400, 800) == 50
        assert dir_sharp_blur_radius(800, 400) == 50
        assert dir_sharp_blur_radius(4, 4) == 1  # a 0-t a natív kód 1-re emeli

    def test_nulla_parameter_azonossag(self) -> None:
        """`a = b = 0` → a horgony és a rámpa is 0, tehát `amount = 0`, és a
        natív `if (0 < amount)` ág be sem lép."""
        image = _zajos()
        assert np.array_equal(apply_dir_sharp(image, 0.0, 0.0), image)

    def test_egyszinu_kep_valtozatlan(self) -> None:
        """Unsharp mask: `c − elmosott(c) = 0` egyszínű képen, bármekkora is
        az erősség."""
        image = _egyszinu()
        assert np.array_equal(apply_dir_sharp(image, 1.0, 0.0), image)

    def test_a_hatas_a_rampa_POZITIV_vegen_a_legerosebb(self) -> None:
        """A natív `w = csonk(−128 · rámpa)`, `amount = (K − w) · 2` a rámpa
        legnagyobb (pozitív) sarkában maximális, a legkisebbnél nullára fut
        ki (#3858, #3859).
        """
        image = _zajos()
        result = apply_dir_sharp(image, 1.0, 0.0).astype(int)
        elteres = np.abs(result - image.astype(int)).mean(axis=(0, 2))
        assert elteres[-5:].mean() > 5.0 * elteres[:5].mean()

    def test_az_elojel_megforditja_az_iranyt(self) -> None:
        image = _zajos()
        balra = np.abs(
            apply_dir_sharp(image, -1.0, 0.0).astype(int) - image.astype(int)
        ).mean(axis=(0, 2))
        assert balra[:5].mean() > 5.0 * balra[-5:].mean()

    def test_a_fuggoleges_tengely_kulon_hat(self) -> None:
        image = _zajos()
        result = apply_dir_sharp(image, 0.0, 1.0).astype(int)
        elteres = np.abs(result - image.astype(int)).mean(axis=(1, 2))
        assert elteres[-5:].mean() > 5.0 * elteres[:5].mean()

    def test_a_bemenetet_nem_modositja(self) -> None:
        image = _zajos()
        eredeti = image.copy()
        apply_dir_sharp(image, 0.7, -0.3)
        assert np.array_equal(image, eredeti)

    def test_elesit_es_nem_lagyit(self) -> None:
        """Az unsharp mask NÖVELI a helyi kontrasztot: a kimenet szórása
        nagyobb, mint a bemeneté."""
        image = _zajos()
        result = apply_dir_sharp(image, 1.0, 0.0)
        assert float(result.std()) > float(image.std())


class TestBajtraEgyezikANativval:
    """#623: a numpy-implementáció a natív EGÉSZ aritmetika lassú, hurkos
    újraírásával vetve — képpontra azonos, nem „közel".

    Ez az a teszt, ami a float/egész kerekítés elcsúszását elkapja: a natív
    magok `>> 8`-cal (padló) dolgoznak, nem kerekítéssel.
    """

    @staticmethod
    def _akkumulatorok(h: int, w: int, a: float, b: float) -> tuple[list, list]:
        """A natív `x`/`y` akkumulátor, lépésenként float32-be visszaírva:
        `−a`-ról indul, `a / (W >> 1)` lépéssel (spec 2.7, #3858)."""
        a32 = np.float32(max(-1.0, min(1.0, a)))
        b32 = np.float32(max(-1.0, min(1.0, b)))
        lepes_x = np.float32(float(a32) / (w >> 1))
        lepes_y = np.float32(float(b32) / (h >> 1))
        xs, x = [], np.float32(-a32)
        for _ in range(w):
            xs.append(float(x))
            x = np.float32(x + lepes_x)
        ys, y = [], np.float32(-b32)
        for _ in range(h):
            ys.append(float(y))
            y = np.float32(y + lepes_y)
        return xs, ys

    @staticmethod
    def _csonk(value: float) -> int:
        return int(value)  # a Python `int()` nulla felé csonkol, mint a natív

    @classmethod
    def _ref_dir_sat(cls, img: np.ndarray, a: float, b: float) -> np.ndarray:
        h, w = img.shape[:2]
        xs, ys = cls._akkumulatorok(h, w, a, b)
        out = np.empty_like(img)
        for y in range(h):
            for x in range(w):
                weight = cls._csonk(128.0 * (xs[x] + ys[y]))
                r, g, bl = (int(v) for v in img[y, x])
                luma = (2 * r + 5 * g + bl) >> 3
                if weight < 0:
                    pixel = [luma + (((c - luma) * (weight + 256)) >> 8) for c in (r, g, bl)]
                else:
                    pixel = [
                        max(0, min(255, c + (((c - luma) * weight) >> 8)))
                        for c in (r, g, bl)
                    ]
                out[y, x] = pixel
        return out

    @classmethod
    def _ref_dir_brite(cls, img: np.ndarray, a: float, b: float) -> np.ndarray:
        h, w = img.shape[:2]
        xs, ys = cls._akkumulatorok(h, w, a, b)
        out = np.empty_like(img)
        for y in range(h):
            for x in range(w):
                weight = cls._csonk(128.0 * (xs[x] + ys[y]))
                lighten = weight > 0
                amount = abs(weight)
                rest = 256 - amount
                pixel = []
                for c in (int(img[y, x, 0]), int(img[y, x, 1]), int(img[y, x, 2])):
                    v = c ^ 0xFF if lighten else c
                    v = (((v * v * v) >> 16) * amount + rest * v) >> 8
                    if lighten:
                        v ^= 0xFF
                    pixel.append(v)
                out[y, x] = pixel
        return out

    @pytest.mark.parametrize(
        "horizontal,vertical",
        [
            (1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.6, -0.4), (0.0, 0.0), (1.0, 1.0),
            (0.5, 0.5), (-0.3, 0.7),
        ],
    )
    def test_dir_sat_bajtra(self, horizontal: float, vertical: float) -> None:
        image = np.random.default_rng(5).integers(0, 256, size=(12, 16, 3), dtype=np.uint8)
        np.testing.assert_array_equal(
            apply_dir_sat(image, horizontal, vertical),
            self._ref_dir_sat(image, horizontal, vertical),
        )

    @pytest.mark.parametrize(
        "horizontal,vertical",
        [
            (1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.6, -0.4), (0.0, 0.0), (1.0, 1.0),
            (0.5, 0.5), (-0.3, 0.7),
        ],
    )
    def test_dir_brite_bajtra(self, horizontal: float, vertical: float) -> None:
        image = np.random.default_rng(5).integers(0, 256, size=(12, 16, 3), dtype=np.uint8)
        np.testing.assert_array_equal(
            apply_dir_brite(image, horizontal, vertical),
            self._ref_dir_brite(image, horizontal, vertical),
        )

    @classmethod
    def _ref_dir_sharp(cls, img: np.ndarray, a: float, b: float) -> np.ndarray:
        """A `0x0090d600` képpont-ciklusa, egészben, hurokkal (#3858):
        `K = csonk(128·(|a| + |b|))`, `w = csonk(−128·(x + y))`,
        `amount = (K − w) · 2`."""
        h, w = img.shape[:2]
        radius = float(dir_sharp_blur_radius(h, w))
        blurred = apply_picasa_blur(img, radius, radius)
        xs, ys = cls._akkumulatorok(h, w, a, b)
        a32 = np.float32(max(-1.0, min(1.0, a)))
        b32 = np.float32(max(-1.0, min(1.0, b)))
        anchor = cls._csonk(128.0 * (abs(float(a32)) + abs(float(b32))))
        out = np.empty_like(img)
        for y in range(h):
            for x in range(w):
                weight = cls._csonk(-128.0 * (xs[x] + ys[y]))
                amount = (anchor - weight) * 2
                pixel = []
                for channel in range(3):
                    c = int(img[y, x, channel])
                    if amount > 0:
                        c += ((c - int(blurred[y, x, channel])) * amount) >> 8
                    pixel.append(max(0, min(255, c)))
                out[y, x] = pixel
        return out

    @pytest.mark.parametrize(
        "horizontal,vertical",
        [
            (1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.6, -0.4), (0.0, 0.0), (1.0, 1.0),
            (0.5, 0.5), (-0.3, 0.7),
        ],
    )
    def test_dir_sharp_bajtra(self, horizontal: float, vertical: float) -> None:
        image = np.random.default_rng(5).integers(0, 256, size=(12, 16, 3), dtype=np.uint8)
        np.testing.assert_array_equal(
            apply_dir_sharp(image, horizontal, vertical),
            self._ref_dir_sharp(image, horizontal, vertical),
        )


class TestNativSuly3859:
    """#3859: a súly `csonk(128 · (x + y))`, float32 akkumulátorokból — nem
    `round(s · 256)`. Spec: `picasa-native-filter-workers.md` 2.7, „A súly
    szorzója 128, csonkolva” (#3858)."""

    # rontás-kontroll: a szorzót 256-ra visszaírva ez az osztály, a bájtra
    # vetés és a golden BUKIK (29 bukás); a `dir_sharp` súlyát `+128`-ra
    # fordítva a két `dir_sharp`-erő-teszt, a három irány-teszt és a
    # `dir_sharp` golden (13 bukás); kerekítéssel csonkolás helyett a bal
    # felső súly és a bájtra vetés (12 bukás); float64 akkumulátorral a
    # bájtra vetés `0,6/−0,4`-es esete (2 bukás). Lefuttatva (#3859).
    def test_a_bal_felso_suly_minusz_128(self) -> None:
        weight = directional_weight(640, 960, 0.5, 0.5)
        assert weight.shape == (640, 960)
        assert int(weight[0, 0]) == -128
        # a jobb alsó sarok egy lépéssel a +128 alatt áll, csonkolva
        assert int(weight[-1, -1]) == 127

    def test_a_suly_legfeljebb_256_vagas_nelkul(self) -> None:
        weight = directional_weight(64, 96, 1.0, 1.0)
        assert int(weight[0, 0]) == -256
        assert int(np.abs(weight).max()) <= 256

    def test_a_dir_sharp_ereje_a_bal_felso_sarokban_nulla(self) -> None:
        amount = dir_sharp_amount(640, 960, 0.5, 0.5)
        assert int(amount[0, 0]) == 0

    def test_a_dir_sharp_ereje_a_jobb_also_sarokban_2x2K(self) -> None:
        amount = dir_sharp_amount(640, 960, 0.5, 0.5)
        horgony = 128  # K = csonk(128 · (0,5 + 0,5))
        assert 2 * 2 * horgony - 4 <= int(amount[-1, -1]) <= 2 * 2 * horgony
        assert int(amount.max()) == int(amount[-1, -1])
        assert int(amount.min()) >= 0


class TestDirGolden3859:
    """A 684-es mérőkészlet `dir_*__alap` párjai (FEJLESZTŐI GÉPEN; a NAS
    nélkül skip). A határ a #3858-ban a natív súllyal mért érték + 0,01."""

    _KIT = Path("/mnt/nas/My Pictures/684-merokeszlet")

    #: (név, lánc, a natív súllyal mért ΔE — #3858 táblája)
    _ESETEK = [
        ("dir_brite__alap", "dir_brite=1,0.500000,0.500000;", 0.187),
        ("dir_sat__alap", "dir_sat=1,0.500000,0.500000;", 0.184),
        ("dir_sharp__alap", "dir_sharp=1,0.500000,0.500000;", 0.384),
    ]

    @pytest.mark.parametrize(("nev", "lanc", "vart_de"), _ESETEK, ids=[e[0] for e in _ESETEK])
    def test_684_merokeszlet_dir(self, nev, lanc, vart_de):
        export_ut = self._KIT / "export" / f"{nev}.jpg"
        if not export_ut.is_file():
            pytest.skip(f"a mérőkészlet nem elérhető: {export_ut}")
        gyoker = Path(__file__).resolve().parents[2]
        if str(gyoker / "tools" / "golden") not in sys.path:
            sys.path.insert(0, str(gyoker / "tools" / "golden"))
        from analyze_validation_kit import load, mean_de

        from picasapy.ini.filters import parse_filters
        from picasapy.render.chain import apply_filters

        kimenet = apply_filters(load(self._KIT / f"{nev}.jpg"), parse_filters(lanc)).image
        de = mean_de(kimenet, load(export_ut))
        hatar = vart_de + 0.01
        assert de <= hatar, f"{nev}: ΔE {de:.3f} > {hatar:.3f}"
