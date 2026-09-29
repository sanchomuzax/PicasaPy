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
    glow_gamma_lut,
    glow_premultiply,
    glow_weight,
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

    def test_teljes_intenzitason_a_sotet_oldal_az_elmosas_screenje(self) -> None:
        # Intenzitás = 1 mellett (k = 256) a fekete oldalon a kimenet a KÖZÖS
        # mag elmosásának Screenje a 0-val: `255 − (((255 − t) · 255) >> 8)`
        # — a natív `>> 8` miatt legfeljebb 1 szinttel az elmosott fölött
        image = _step_edge()
        radius = 250.0**0.5
        blurred = apply_picasa_blur(image, radius, radius)[:, :400].astype(int)
        result = apply_glow(image, 1.0, radius)[:, :400].astype(int)
        np.testing.assert_array_equal(result, 255 - (((255 - blurred) * 255) >> 8))
        assert int((result - blurred).max()) <= 1

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
    """A `radblur` elmosási sugara a KÉPSZÉLESSÉGHEZ kötött (4.2.4).

    A hányad a binárisban álló `0,01` (`[0xcf40b8]`, #3916/#3917): a korábbi
    `0,009` a közös elmosó mag régi együtthatóját kompenzálta. A 684-es
    készleten a `0,01` az `alap` és a `max` esetet 0,640 → 0,330 és
    0,530 → 0,335 ΔE-re viszi (zajszint ~0,30).
    """

    @pytest.mark.parametrize(
        "width,amount,expected",
        [(1920, 0.0, 19.201), (1600, 0.5, 24.001), (1600, -1.0, 0.001)],
    )
    def test_binaris_sugar(self, width: int, amount: float, expected: float) -> None:
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
        # (`(3−2u)·u²·255`, CSONKOLVA — #3946) rendre 215 / 127 / 39 — a
        # LINEÁRIS átmenet ugyanitt 191 / 127 / 63 volna.
        table, shift = radial_weight_table(400, 400, 0.0, 0.0)
        assert shift == 6
        assert [int(table[i]) for i in (39, 156, 352)] == [215, 127, 39]

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


def _nativ_keveres(original: np.ndarray, blurred: np.ndarray, k: int) -> np.ndarray:
    """A spec egész keverése képpontonként, SKALÁR Python-egészekkel (#3913).

    Szándékosan nem vektoros: a független újraszámolás a vektoros
    megvalósítás őre. A negatív szorzat `>>` -je Pythonban is lefelé kerekít,
    ahogy a csomagolt 16 bites út modulo-256-os összeadása.
    """
    out = np.empty_like(original)
    for index, (o_val, t_val) in enumerate(
        zip(original.reshape(-1).tolist(), blurred.reshape(-1).tolist(), strict=True)
    ):
        s_val = 255 - (((255 - t_val) * (255 - o_val)) >> 8)
        out.reshape(-1)[index] = s_val + (((o_val - s_val) * (256 - k)) >> 8)
    return out


class TestGlowEgeszAritmetika3913:
    """A binárisból kiolvasott egész aritmetika (spec: „⛳ A `glow` egész
    aritmetikája a binárisból”, #3912): gamma-tábla, Screen `>> 8`,
    visszakeverés `256 − k` súllyal."""

    @pytest.mark.parametrize(
        ("intenzitas", "vart_k"),
        [(0.432749, 110), (0.65, 166), (-0.65, 166), (0.00390625, 1), (1.5, 256), (-2.0, 256)],
    )
    def test_a_suly_csonkolt_es_vagott(self, intenzitas: float, vart_k: int) -> None:
        """`k = min(|trunc(256·i)|, 256)`, az `i` előtte `[−1, 1]`-re vágva —
        CSONKOL, nem kerekít (a v1 alapérték 110,78 → 110, kerekítve 111
        lenne)."""
        assert glow_weight(intenzitas) == vart_k

    def test_a_gamma_tabla_ertekei(self) -> None:
        lut = glow_gamma_lut()
        assert lut.dtype == np.uint8
        assert lut.shape == (256,)
        assert int(lut[0]) == 0
        assert int(lut[128]) == 64
        assert int(lut[200]) == 157
        assert int(lut[255]) == 255

    def test_az_elogorbe_a_gamma_tabla(self) -> None:
        image = np.arange(256, dtype=np.uint8).reshape(16, 16, 1).repeat(3, axis=2)
        np.testing.assert_array_equal(glow_premultiply(image), glow_gamma_lut()[image])

    def test_k_nulla_a_kimenet_a_bemenet(self) -> None:
        # 256 · 0,0039 = 0,998 → csonkolva k = 0 → ki = o, bitre
        rng = np.random.default_rng(3913)
        image = rng.integers(0, 256, size=(32, 32, 3), dtype=np.uint8)
        np.testing.assert_array_equal(apply_glow(image, 0.0039, 3.0), image)
        np.testing.assert_array_equal(apply_glow(image, 0.0, 3.0), image)
        # fehér mezőben egy fekete képpont: a lebegőpontos súly (0,0039) már
        # 1 szintet emelne rajta, a csonkolt k = 0 nem
        dot = _uniform(255, size=16)
        dot[8, 8] = 0
        np.testing.assert_array_equal(apply_glow(dot, 0.0039, 3.0), dot)

    @pytest.mark.parametrize("intensity,k", [(0.65, 166), (1.0, 256), (0.5, 128)])
    def test_nulla_sugarnal_nincs_elmosas_es_a_keveres_bitre(
        self, intensity: float, k: int
    ) -> None:
        # 0-s sugárnál a natív mag azonnal visszatér: t = LUT[o]
        rng = np.random.default_rng(k)
        image = rng.integers(0, 256, size=(12, 12, 3), dtype=np.uint8)
        expected = _nativ_keveres(image, glow_gamma_lut()[image], k)
        np.testing.assert_array_equal(apply_glow(image, intensity, 0.0), expected)

    def test_a_keveres_bitre_elmosassal(self) -> None:
        rng = np.random.default_rng(7)
        image = rng.integers(0, 256, size=(20, 20, 3), dtype=np.uint8)
        blurred = apply_picasa_blur(glow_premultiply(image), 3.0, 3.0)
        expected = _nativ_keveres(image, blurred, 166)
        np.testing.assert_array_equal(apply_glow(image, 0.65, 3.0), expected)

    def test_negativ_intenzitas_az_abszolut_erteke(self) -> None:
        # a callback `fabs`-szal adja tovább az Intenzitást (0x0049f5c0)
        rng = np.random.default_rng(5)
        image = rng.integers(0, 256, size=(16, 16, 3), dtype=np.uint8)
        np.testing.assert_array_equal(
            apply_glow(image, -0.65, 3.0), apply_glow(image, 0.65, 3.0)
        )

    def test_a_sugar_250_re_vagva(self) -> None:
        image = _step_edge(width=1200, height=8)
        np.testing.assert_array_equal(
            apply_glow(image, 1.0, 400.0), apply_glow(image, 1.0, 250.0)
        )

    def test_teljes_intenzitason_a_fekete_egy_szintet_emelkedik(self) -> None:
        # k = 256 → ki = s; o = t = 0 → s = 255 − (65025 >> 8) = 1
        np.testing.assert_array_equal(apply_glow(_uniform(0, size=8), 1.0, 3.0), 1)
