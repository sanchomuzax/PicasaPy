"""#668: a `glow`/`glow2` és a `radblur` a KÖZÖS NATÍV elmosó magon.

A #623 bevitte a Picasa közös elmosóját (`render/iir_blur.py`), de a
`glow`-t és a `radblur`-t szándékosan a régi Gauss-közelítésen hagyta. Ez
a fájl a **mért** horgonyokat rögzíti, amik alapján az átállás megtörtént.

## Honnan valók a számok

- **Ragyogás tónusválasz** — a `golden-kit/09-effects` `chart_color__glow1`
  / `chart_color__glow2` VALÓDI Picasa-exportjának sík szürke foltjairól
  leolvasva (a folt akkora, hogy az elmosás rajta nem változtat, tehát a
  térbeli komponens kiesik és tisztán a keverés látszik). A mért pontok a
  modellt ±0,4 szinten belül adják vissza — ezért itt ±1 a tűrés.
- **Ragyogás él-profil** — a `referencia/blur-meres` szintetikus
  éllépcsőjének Picasa-exportja (Intenzitás maximumon, Sugár 50%,
  `R = 250^0,5 = 15,811`); ez a `docs/specs/picasa-native-filter-workers.md`
  4.2.5 mérésének forrása.
- **Lágy fókusz** — a `golden-kit3/16-effects-ramp` és a
  `golden-kit/09-effects` `radblur` exportjai (négy pár, három kép, két
  Amount-érték).

A goldenek a fejlesztői gépen élnek, a repóban nincsenek — ezért a tesztek
a mért SZÁMOKAT hordozzák, szintetikus képekre alkalmazva.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.effects import (
    apply_glow,
    apply_radblur,
    glow_premultiply,
    radblur_blur_radius,
)
from picasapy.render.iir_blur import apply_picasa_blur
from picasapy.render.radial_mask import radial_weight_table

#: A `glow` (v1) golden-kitbeli paraméterei (`glow=1,0.432749,2.469705`).
_GLOW1 = (0.432749, 2.469705)
#: A `glow2` golden-kitbeli paraméterei (`glow2=1,0.650000,3.000000`).
_GLOW2 = (0.650000, 3.000000)


def _uniform(value: int, size: int = 48) -> np.ndarray:
    return np.full((size, size, 3), value, dtype=np.uint8)


def _step_edge(width: int = 800, height: int = 64) -> np.ndarray:
    """A `blur-meres` éllépcsője: bal fél fekete, jobb fél fehér."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, width // 2 :] = 255
    return image


class TestGlowMertTonusvalasz:
    """A sík foltok mért kimenete a valódi Picasa-exportból.

    Ez a legerősebb őr: elbukik, ha a négyzetre emelő előgörbe kimarad,
    ha a keverés nem screen, vagy ha a súly nem az Intenzitás.
    """

    @pytest.mark.parametrize(
        "level,expected",
        [(64, 70), (96, 106), (128, 142), (160, 176), (192, 207)],
    )
    def test_glow_v1_sik_foltok(self, level: int, expected: int) -> None:
        result = apply_glow(_uniform(level), *_GLOW1)
        assert abs(int(result[24, 24, 0]) - expected) <= 1

    @pytest.mark.parametrize(
        "level,expected",
        [(64, 72), (96, 111), (128, 149), (160, 184), (192, 215)],
    )
    def test_glow2_sik_foltok(self, level: int, expected: int) -> None:
        result = apply_glow(_uniform(level), *_GLOW2)
        assert abs(int(result[24, 24, 0]) - expected) <= 1

    def test_a_negyzetre_emelt_elogorbe(self) -> None:
        # a natív mag az elmosás ELŐTT önmagával szorozza a képet
        # (multiply): 200 → 200²/255 = 156,86 → 157
        image = _uniform(200, size=8)
        assert int(glow_premultiply(image)[4, 4, 0]) == 157
        assert int(glow_premultiply(_uniform(255, size=8))[4, 4, 0]) == 255
        assert int(glow_premultiply(_uniform(0, size=8))[4, 4, 0]) == 0

    def test_fekete_marad_fekete(self) -> None:
        # a szorzó előgörbe miatt a teljesen fekete folt nem világosodik
        image = _uniform(0)
        np.testing.assert_array_equal(apply_glow(image, *_GLOW2), image)


class TestGlowElProfil:
    """A térbeli komponens: a `blur-meres` exportjának mért él-profilja."""

    #: Sugár 50% (`R = 250^0,5`), a fekete oldal utolsó négy képpontja az
    #: exportált JPEG-en (x = 396…399, 512 sor átlagából).
    _MERT_PROFIL = (100, 108, 117, 122)

    def test_el_profil_a_nativ_maggal(self) -> None:
        image = _step_edge()
        radius = 250.0**0.5
        profile = apply_glow(image, 1.0, radius).mean(axis=0)[396:400, 0]
        # a JPEG-tömörítés miatt ±3 szint a tűrés
        assert np.allclose(profile, self._MERT_PROFIL, atol=3.0)

    def test_teljes_intenzitason_a_sotet_oldal_a_puszta_elmosas(self) -> None:
        # Intenzitás = 1 mellett a fekete oldalon a kimenet a KÖZÖS mag
        # elmosása (screen a 0-val = maga az elmosott érték)
        image = _step_edge()
        radius = 250.0**0.5
        blurred = apply_picasa_blur(image, radius, radius)
        result = apply_glow(image, 1.0, radius)
        np.testing.assert_array_equal(result[:, :400], blurred[:, :400])

    def test_a_feher_oldal_255_marad(self) -> None:
        result = apply_glow(_step_edge(), 1.0, 250.0**0.5)
        assert int(result[:, 799, 0].min()) == 255

    def test_a_sugar_keppontban_abszolut(self) -> None:
        # 4.2.5 ellenőrző mérés: a `glow` sugara NEM a képmérethez kötött —
        # kétszer szélesebb képen az él-profil ugyanaz marad
        radius = 250.0**0.5
        narrow = apply_glow(_step_edge(800), 1.0, radius).mean(axis=0)[396:400, 0]
        wide = apply_glow(_step_edge(1600), 1.0, radius).mean(axis=0)[796:800, 0]
        assert np.allclose(narrow, wide, atol=1.0)


class TestGlowAltalanos:
    def test_nulla_intenzitas_identitas(self) -> None:
        image = _uniform(180, size=16)
        np.testing.assert_array_equal(apply_glow(image, 0.0, 3.0), image)

    def test_sohasem_sotetit(self) -> None:
        rng = np.random.default_rng(11)
        image = rng.integers(0, 256, size=(24, 24, 3), dtype=np.uint8)
        result = apply_glow(image, 0.65, 3.0)
        assert np.all(result.astype(int) >= image.astype(int))

    def test_nem_lo_tul(self) -> None:
        assert int(apply_glow(_uniform(255), 1.0, 3.0).max()) == 255

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform(128, size=16)
        original = image.copy()
        apply_glow(image, 0.65, 3.0)
        np.testing.assert_array_equal(image, original)


class TestRadblurSugar:
    """A `radblur` elmosási sugara a KÉPSZÉLESSÉGHEZ kötött (4.2.4)."""

    @pytest.mark.parametrize(
        "width,amount,expected",
        [(1920, 0.0, 17.281), (1600, 0.5, 21.601), (1600, -1.0, 0.001)],
    )
    def test_mert_sugar(self, width: int, amount: float, expected: float) -> None:
        assert radblur_blur_radius(width, amount) == pytest.approx(
            expected, abs=0.01
        )

    def test_ketszeres_szelessegen_ketszeres_sugar(self) -> None:
        assert radblur_blur_radius(1600, 0.25) == pytest.approx(
            2.0 * radblur_blur_radius(800, 0.25), abs=0.002
        )


class TestRadialMaskTabla:
    """A natív, négyzetes távolsággal indexelt smoothstep-súlytábla."""

    def test_kozepen_teli_sulyt_ad(self) -> None:
        table, _ = radial_weight_table(1600, 1200, 0.3, 0.0)
        assert table.shape == (1024,)
        assert int(table[0]) == 255

    def test_monoton_csokken_es_kinullazodik(self) -> None:
        table, _ = radial_weight_table(1600, 1200, 0.3, 0.0)
        assert all(a >= b for a, b in zip(table, table[1:], strict=False))
        assert int(table[-1]) == 0

    def test_smoothstep_alaku_es_nem_linearis(self) -> None:
        # 400×400, Size = 0 → a korong sugara 200 px, a lépték 2^6.
        # A normált 0,25 / 0,5 / 0,75 sugárnál a natív smoothstep
        # (`(3−2u)·u²·255`) rendre 215 / 128 / 40 — a LINEÁRIS átmenet
        # ugyanitt 191 / 128 / 64 volna.
        table, shift = radial_weight_table(400, 400, 0.0, 0.0)
        assert shift == 6
        assert [int(table[i]) for i in (39, 156, 352)] == [215, 128, 40]

    def test_az_elesseg_meredekebb_atmenetet_ad(self) -> None:
        lagy, _ = radial_weight_table(1600, 1200, 0.3, 0.0)
        eles, _ = radial_weight_table(1600, 1200, 0.3, 0.9)
        # ugyanaz a geometria, de az éles változat hamarabb nullázódik ki
        assert int(np.count_nonzero(eles)) < int(np.count_nonzero(lagy))

    def test_a_lepteko_a_negyzetes_tavolsagot_1024_ala_hozza(self) -> None:
        _, shift = radial_weight_table(1600, 1200, 0.3, 0.0)
        radius = min(1600, 1200) / 2.0 * 1.3
        assert (radius * radius) / (2**shift) <= 1024.0
        assert (radius * radius) / (2 ** max(shift - 1, 0)) > 1024.0


class TestRadblurNativ:
    def test_amount_nulla_NEM_azonossag(self) -> None:
        # A régi modell azonosságnak vette; a golden-kit exportja
        # (`radblur=1,0.411585,0.611111,0,0`) ezt MEGCÁFOLJA: a kép
        # pereme ott is érezhetően elmosódik.
        rng = np.random.default_rng(5)
        image = rng.integers(0, 256, size=(300, 400, 3), dtype=np.uint8)
        result = apply_radblur(image, 0.5, 0.5, 0.0, 0.0)
        corner = np.abs(
            result[:20, :20].astype(float) - image[:20, :20].astype(float)
        )
        assert corner.mean() > 5.0

    def test_a_kozeppont_eles_marad(self) -> None:
        rng = np.random.default_rng(7)
        image = rng.integers(0, 256, size=(200, 200, 3), dtype=np.uint8)
        result = apply_radblur(image, 0.5, 0.5, 0.3, 0.5)
        # a natív tábla maximuma 255/256, ezért 1 szint eltérés belefér
        assert np.all(np.abs(result[100, 100].astype(int) - image[100, 100]) <= 1)

    def test_a_tavoli_sarok_a_puszta_elmosas(self) -> None:
        rng = np.random.default_rng(9)
        image = rng.integers(0, 256, size=(200, 300, 3), dtype=np.uint8)
        radius = radblur_blur_radius(300, 0.0)
        blurred = apply_picasa_blur(image, radius, radius)
        result = apply_radblur(image, 0.5, 0.5, -0.5, 0.0)
        np.testing.assert_array_equal(result[0, 0], blurred[0, 0])

    def test_a_maszkot_nulla_Sharpness_szel_futtatja(self) -> None:
        # A `radblur`-nak nincs „Élesség" csúszkája, és a négy golden-pár
        # illesztési minimuma is a 0-nál van. Ellenőrzés: egy ismert, normált
        # 0,25 sugarú ponton a keverési súlynak a natív tábla 215-ös értékét
        # kell adnia (Sharpness = 0,5 mellett ott már 255 állna).
        rng = np.random.default_rng(13)
        image = rng.integers(0, 256, size=(400, 400, 3), dtype=np.uint8)
        radius = radblur_blur_radius(400, 0.5)
        blurred = apply_picasa_blur(image, radius, radius).astype(np.int64)
        result = apply_radblur(image, 0.5, 0.5, 0.0, 0.5)
        point = (200, 250)  # dx = 50 = a 200 px-es korong negyede
        base = blurred[point]
        expected = base + (image[point].astype(np.int64) - base) * 215 // 256
        np.testing.assert_array_equal(result[point].astype(np.int64), expected)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform(90, size=64)
        original = image.copy()
        apply_radblur(image, 0.5, 0.5, 0.2, 0.7)
        np.testing.assert_array_equal(image, original)
