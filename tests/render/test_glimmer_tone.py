"""#381: `glimmer_tone` — Vignette/Matte/HDR/LocalContrast/CrossProcess/
Sixties/HeatMap/NightVision/TwoTone/QuantizePalette min/alap/max
határeset-tesztjei, a `filterdesc-registry.md` 4.2 tartományai szerint.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.render import glimmer_ops as ops
from picasapy.render import glimmer_tone as t
from tests.support.realistic_photo import make_realistic_photo


@pytest.fixture
def image() -> np.ndarray:
    rng = np.random.default_rng(9)
    img = rng.integers(20, 235, size=(48, 64, 3), dtype=np.uint8)
    img[:16, :, 0] = 220
    return img


def _real_photo_rgb(height: int, width: int, seed: int = 7) -> np.ndarray:
    """#504 (j1): ld. `test_glimmer_creative.py` ugyanilyen helperjét."""
    return cv2.cvtColor(make_realistic_photo(height=height, width=width, seed=seed), cv2.COLOR_BGR2RGB)


def _assert_valid(result, image):
    assert result.dtype == np.uint8
    assert result.shape[2] == 3


def _multiply_color_matrix_q11_reference(value: int, multiplier: float) -> int:
    """A filterdesc-registry.md-ben mért skalár Q11-képlet független oracle-ja."""
    m32 = np.float32(multiplier)
    scaled = np.float32(np.float32(2048.0) * m32)
    q = int(np.trunc(float(scaled) + (0.5 if scaled >= 0 else -0.5)))
    sar9 = (q * int(value)) >> 9
    return min(255, max(0, (sar9 + 2) >> 2))


def _multiply_color_matrix_q11_array_reference(values, multiplier: float) -> np.ndarray:
    array = np.asarray(values)
    return np.fromiter(
        (_multiply_color_matrix_q11_reference(v, multiplier) for v in array.flat),
        dtype=np.int64,
        count=array.size,
    ).reshape(array.shape)


class TestMultiplyColorMatrixQ11:
    @pytest.mark.parametrize("width", [2, 3], ids=["paros", "paratlan"])
    def test_multiply_color_matrix_q11_byte_exact(self, width):
        """#4172 / 626: a mért 1, 1,5, 2 és 3 szorzó Q11 bájtjai."""
        y, x = np.mgrid[0:2, 0:width]
        source = np.stack(
            (
                (17 + 31 * x + 7 * y) % 256,
                (29 + 23 * x + 11 * y) % 256,
                (43 + 19 * x + 13 * y) % 256,
            ),
            axis=-1,
        ).astype(np.uint8)

        hibak = []
        for multiplier in (1.0, 1.5, 2.0, 3.0):
            vart = np.fromiter(
                (_multiply_color_matrix_q11_reference(v, multiplier) for v in source.flat),
                dtype=np.uint8,
                count=source.size,
            ).reshape(source.shape)
            kapott = ops._szorzott_resz(source, multiplier)
            if not np.array_equal(kapott, vart):
                hibak.append(
                    f"szorzó={multiplier}: {np.count_nonzero(kapott != vart)} eltérő RGB-bájt"
                )

        assert not hibak, "; ".join(hibak)


class TestVignetteMatte:
    @pytest.mark.parametrize("blur,strength,fade", [(0.0, 1.0, 0.0), (35.0, 1.4, 0.0), (50.0, 2.0, 100.0)])
    def test_vignette_hatarok(self, image, blur, strength, fade):
        _assert_valid(t.apply_vignette(image, blur=blur, strength=strength, fade=fade), image)

    @pytest.mark.parametrize("blur,strength,fade", [(0.0, 1.0, 0.0), (40.0, 1.2, 0.0), (50.0, 2.0, 100.0)])
    def test_matte_hatarok(self, image, blur, strength, fade):
        _assert_valid(t.apply_matte(image, blur=blur, strength=strength, fade=fade), image)

    def test_vignette_fade_100_valtozatlan(self, image):
        result = t.apply_vignette(image, fade=100.0)
        np.testing.assert_array_equal(result, image)

    def test_vignette_szel_sotetebb_kozepnel(self):
        white = np.full((60, 80, 3), 255, dtype=np.uint8)
        result = t.apply_vignette(white)
        assert int(result[30, 40, 0]) >= int(result[0, 40, 0])

    # a VALÓDI Picasa-kimenetből (`referencia/vignette/Vignette default`,
    # 2560×1702) mért maszk: a középtől mért, a fél-hosszabbik-oldallal
    # normált sugár → a sötétítés szorzója (a képpontok medián-aránya az
    # effekt nélküli exporthoz). A 0,45 alatti sávban a maszk 1,000.
    _PICASA_VIGNETTE_PROFILE = ((0.45, 0.973), (0.65, 0.895), (0.85, 0.746), (1.05, 0.336))

    def test_vignette_maszkja_a_picasa_mert_profiljat_adja(self):
        """#317: a `Blur=35` (alapértelmezett) maszk a VALÓDI Picasa-kimenetből
        mért profilt követi.

        Ez a mérés adta a `sugár = Blur·0,02·max(W,H)/8` képletet is: a
        `filterdesc.xml` `/4`-es képlete (és a rá tett 255-ös Flash-korlát)
        ennél a profilnál mérhetően beljebb kezdi a sötétítést.
        """
        height, width = 851, 1280  # a referencia-fotó fele, arányhelyesen
        white = np.full((height, width, 3), 255, dtype=np.uint8)
        mask = t.apply_vignette(white, blur=35.0)[..., 0].astype(float) / 255.0
        rows, cols = np.mgrid[0:height, 0:width]
        radius = np.hypot(
            (rows - height / 2) / (max(height, width) / 2),
            (cols - width / 2) / (max(height, width) / 2),
        )
        for centre, expected in self._PICASA_VIGNETTE_PROFILE:
            band = (radius >= centre - 0.05) & (radius < centre + 0.05)
            measured = float(np.median(mask[band]))
            assert measured == pytest.approx(expected, abs=0.06), (
                f"r={centre}: {measured:.3f} a Picasa mért {expected:.3f} helyett"
            )

    def test_vignette_nagy_kepen_sem_vagodik_le_a_sugar(self):
        """A 255-ös Flash-korlát (#518, Lomo/Holga) itt NEM érvényes: a
        `referencia/vignette/` Blur=50-es exportja 310–320-as szigmát kíván,
        a 255-re vágott sugár mérhetően rosszabb. Ha valaki visszatenné a
        korlátot, a Blur=35 és a Blur=50 kimenete AZONOSSÁ válna egy nagy
        képen (mindkettő 255-re vágódna) — ez a teszt épp ezt buktatja.
        """
        photo = _real_photo_rgb(1200, 1800, seed=5)
        mid = t.apply_vignette(photo, blur=35.0)
        wide = t.apply_vignette(photo, blur=50.0)
        difference = float(np.abs(mid.astype(float) - wide.astype(float)).mean())
        assert difference > 1.0, "a Blur csúszka nem hat — visszakerült a 255-ös korlát?"


class TestHdrLocalContrast:
    @pytest.mark.parametrize("radius,strength", [(1.3, 1.0), (20.0, 3.0), (80.0, 7.0)])
    def test_hdr_hatarok(self, image, radius, strength):
        _assert_valid(t.apply_hdr(image, radius=radius, strength=strength), image)

    def test_hdr_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_hdr(image, fade=100.0), image)

    @pytest.mark.parametrize("radius,strength", [(1.3, 1.0), (15.0, 1.5), (40.0, 3.0)])
    def test_local_contrast_hatarok(self, image, radius, strength):
        _assert_valid(t.apply_local_contrast(image, radius=radius, strength=strength), image)


class TestCrossProcess:
    @pytest.mark.parametrize("fade", [0.0, 50.0, 100.0])
    def test_hatarok(self, image, fade):
        _assert_valid(t.apply_crossprocess(image, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_crossprocess(image, fade=100.0), image)

    def test_fade_0_valtoztat(self, image):
        assert not np.array_equal(t.apply_crossprocess(image, fade=0.0), image)


class TestSixties:
    @pytest.mark.parametrize("fade,rounded", [(0.0, False), (20.0, True), (100.0, True)])
    def test_hatarok(self, image, fade, rounded):
        _assert_valid(t.apply_sixties(image, fade=fade, rounded=rounded), image)

    def test_rounded_sarok_szinu(self, image):
        result = t.apply_sixties(image, fade=0.0, rounded=True, color=(1, 2, 3))
        assert tuple(result[0, 0]) == (1, 2, 3)


class TestHeatMap:
    @pytest.mark.parametrize("hue,fade", [(-180.0, 0.0), (0.0, 0.0), (180.0, 100.0)])
    def test_hatarok(self, image, hue, fade):
        _assert_valid(t.apply_heatmap(image, hue=hue, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_heatmap(image, fade=100.0), image)


class TestNightVision:
    @pytest.mark.parametrize(
        "brightness,contrast,fade", [(-50.0, -50.0, 0.0), (0.0, 0.0, 0.0), (50.0, 50.0, 100.0)]
    )
    def test_hatarok(self, image, brightness, contrast, fade):
        _assert_valid(t.apply_nightvision(image, brightness=brightness, contrast=contrast, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_nightvision(image, fade=100.0), image)


class TestVignetteMatteNightVisionRealPhoto504510:
    """#504/#510 — valódi (folytonos hisztogramú) fotóval mért kiegészítés
    a `TestHolgaRealPhoto504510`-hez (`test_glimmer_creative.py`): a #509/
    #504 mind az ÖT méretfüggő ragyogás-effektet érintette (j3), nemcsak a
    Lomo/Holga párt."""

    def test_nightvision_r_nagyobb_mint_b(self):
        """#510: a NightVision `#57cc29` (R=0x57=87 > B=0x29=41) tintje a
        valódi BGR-kimeneten is R>B legyen — ellenőrzi, hogy a
        `_NIGHTVISION_COLORS` RGB-ként helyesen íródott."""
        photo_rgb = _real_photo_rgb(200, 300)
        result_rgb = t.apply_nightvision(photo_rgb)
        result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
        assert float(result_bgr[..., 2].mean()) > float(result_bgr[..., 0].mean())

    @pytest.mark.parametrize(
        "effect_name,apply_fn",
        [
            ("Vignette", t.apply_vignette),
            ("Matte", t.apply_matte),
            ("NightVision", t.apply_nightvision),
        ],
    )
    def test_meretfuggetlen_fekete_arany(self, effect_name, apply_fn):
        """j2: a méretfüggő ragyogás-sugár ellenére a tiszta fekete arány
        96 px-en és 1600 px-en néhány százalékon belül egyezzen."""

        def black_pct(img: np.ndarray) -> float:
            return float(np.all(img == 0, axis=-1).mean() * 100.0)

        small = apply_fn(_real_photo_rgb(96, 72))
        large = apply_fn(_real_photo_rgb(1600, 1200))
        diff = abs(black_pct(small) - black_pct(large))
        assert diff <= 15.0, (
            f"{effect_name}: fekete-arány 96px={black_pct(small):.1f}% "
            f"vs 1600px={black_pct(large):.1f}% — {diff:.1f}pp eltérés"
        )

    @pytest.mark.parametrize(
        "effect_name,apply_fn",
        [
            ("Vignette", t.apply_vignette),
            ("Matte", t.apply_matte),
            ("NightVision", t.apply_nightvision),
        ],
    )
    def test_perf_nagy_kepen(self, effect_name, apply_fn):
        """j5: a közös `_border_glow` nagy képen is gyors maradjon
        (nagyvonalú korlát, hogy lassú CI-n se legyen ingatag — a
        javítás előtt a Vignette 124 s, a Matte 89 s volt egy
        4000×3000-es fotón, ld. a #504 utolsó kommentje)."""
        from support.perf_baseline import merd_es_ellenorizd

        photo_rgb = _real_photo_rgb(1500, 2000)
        merd_es_ellenorizd(f"{effect_name}(2000x1500)", photo_rgb, apply_fn)


class TestTwoTone:
    @pytest.mark.parametrize(
        "brightness,contrast,fade", [(-95.0, 0.0, 0.0), (0.0, 20.0, 0.0), (95.0, 100.0, 100.0)]
    )
    def test_hatarok(self, image, brightness, contrast, fade):
        _assert_valid(t.apply_twotone(image, brightness=brightness, contrast=contrast, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_twotone(image, fade=100.0), image)


class TestQuantizePalette:
    @pytest.mark.parametrize("steps,smoothing,fade", [(2.0, 0.0, 0.0), (8.0, 80.0, 0.0), (30.0, 100.0, 100.0)])
    def test_hatarok(self, image, steps, smoothing, fade):
        _assert_valid(t.apply_quantizepalette(image, steps=steps, smoothing=smoothing, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_quantizepalette(image, fade=100.0), image)


class TestHdrMeasuredModel:
    """#545 → #1607 → #3520: a HDR/LocalContrast modellje.

    A #1607 a `quality="3"` háromszoros dobozelmosásban találta meg a #545
    illesztett konstansainak (Radius/2, `+2,9·Strength`) okát. A #3520 a
    bináris láncából (`0x00bc41e0`) két további tényt hozott:

    * az elmosás a natív `BlurImageOperation` (`render/nativ_blur`), amely
      az 1,3-as sugárral is mos — a saját dobozunk 1-re kerekítette, és a
      `HDR` `min` állása hatástalan lett;
    * a `HDR` natív lánca az EREDETIBŐL indul (`be + C·(be − elm)`), a
      `LocalContrast` XML-lánca az elmosottból (`elm + C·(be − elm)`).
    """

    def test_sik_kepen_AZONOSSAG(self):
        """A régi modell síkon is világosított (`Strength=3` → +8,7 szint),
        pedig ott nincs mit kiemelni. A csonkítás sík felületen nulla
        torzítást ad, tehát az égbolt és a sima fal érintetlen marad."""
        flat = np.full((60, 80, 3), 137, dtype=np.uint8)
        for strength in (1.0, 3.0, 7.0):
            np.testing.assert_array_equal(
                t.apply_hdr(flat, radius=20.0, strength=strength, fade=0.0), flat
            )

    @staticmethod
    def _fuggetlen_lanc(photo, radius, c, eredetibol):
        """Független átirat a `filters-decoded.md` „`HDR` — a natív
        `LocalContrastImageOperation`…" táblájából, lépésenként 8 bitre vágva."""
        from picasapy.render.nativ_blur import blur_image_operation

        be = photo.astype(np.int64)
        elm = blur_image_operation(photo, radius, radius, 3).astype(np.int64)
        fel = _multiply_color_matrix_q11_array_reference(np.clip(be - elm, 0, 255), c)
        le = _multiply_color_matrix_q11_array_reference(np.clip(elm - be, 0, 255), c)
        if eredetibol:
            return np.clip(np.clip(be + fel, 0, 255) - le, 0, 255).astype(np.uint8)
        return np.clip(np.clip(elm - le, 0, 255) + fel, 0, 255).astype(np.uint8)

    @pytest.mark.parametrize("radius,c", [(1.3, 1.0), (20.0, 3.0), (80.0, 7.0)])
    def test_a_hdr_a_nativ_lanc_szerint_szamol(self, radius, c):
        photo = _real_photo_rgb(120, 160, seed=3)
        np.testing.assert_array_equal(
            t.apply_hdr(photo, radius=radius, strength=c, fade=0.0),
            self._fuggetlen_lanc(photo, radius, c, eredetibol=True),
        )

    @pytest.mark.parametrize("radius,c", [(1.3, 1.0), (15.0, 1.5), (40.0, 3.0)])
    def test_a_localcontrast_az_xml_lanc_szerint_szamol(self, radius, c):
        photo = _real_photo_rgb(120, 160, seed=4)
        np.testing.assert_array_equal(
            t.apply_local_contrast(photo, radius=radius, strength=c),
            self._fuggetlen_lanc(photo, radius, c, eredetibol=False),
        )

    def test_hdr_min_allasa_hat(self):
        """#3520: `R 1,3 / C 1` a Picasában ΔE 1,1-et mozdít — nálunk is hasson."""
        photo = _real_photo_rgb(120, 160, seed=5)
        eredmeny = t.apply_hdr(photo, radius=1.3, strength=1.0, fade=0.0)
        assert np.mean(np.abs(eredmeny.astype(np.int16) - photo)) > 0.5

    def test_localcontrast_c1_azonossag(self):
        """#688: a `LocalContrast` alsó vége bitre azonosság — az XML-láncból."""
        photo = _real_photo_rgb(120, 160, seed=6)
        for radius in (1.3, 15.0, 40.0):
            np.testing.assert_array_equal(
                t.apply_local_contrast(photo, radius=radius, strength=1.0), photo
            )

    def test_fade_100_valtozatlan_marad(self):
        photo = _real_photo_rgb(60, 80, seed=9)
        np.testing.assert_array_equal(
            t.apply_hdr(photo, radius=20.0, strength=3.0, fade=100.0), photo
        )




# ---------------------------------------------------------------------------
# #3520 — FEJLESZTŐI GÉPEN futó golden-mérés a 684-es készlet Picasa-
# exportjával; ha a készlet nincs a gépen, skip. A `HDR` natív lánca
# (`LocalContrastImageOperation`, `0x00bc41e0`) `be + C·(be − elm)`, a
# `LocalContrast` XML-lánca `elm + C·(be − elm)`; mindkettő a natív
# `BlurImageOperation`-nel (`quality = 3`) mos, ami az 1,3-as sugárral is hat.
# Mérve (CIE76 átlag-ΔE a Picasa-exporthoz, `analyze_validation_kit.mean_de`):
#
# | eset                         | előtte | utána |
# |------------------------------|-------:|------:|
# | HDR min (R 1,3 / C 1)        | 1,120  | 0,188 |
# | HDR alap (R 20 / C 3)        | 0,489  | 0,265 |
# | HDR max (R 80 / C 7 / F 100) | 0,121  | 0,121 |
# | LocalContrast min (R 1,3/C 1)| 0,121  | 0,121 |
# | LocalContrast alap (R 15/1,5)| 0,225  | 0,159 |
# | LocalContrast max (R 40/C 3) | 0,520  | 0,258 |
# ---------------------------------------------------------------------------

# rontás-kontroll: a `hdr_local_contrast` az elmosottból indítva → 6 failed
# (a három natív-lánc-egyezés, a `min` hatása, a golden HDR `min` és `alap`);
# az elmosás `quality=1`-re → 9 failed (öt lánc-egyezés, négy golden); a
# szorzó `rint` helyett `floor` → 2 failed (LocalContrast-lánc 1,5-tel és a
# golden `localcontrast__alap`); a `LocalContrast` az eredetiből indítva →
# 7 failed (három lánc-egyezés, a `C = 1` azonosság és a három golden).

_KIT_684 = Path("/mnt/nas/My Pictures/684-merokeszlet")

#: A mért érték + 0,05-ös tűrés.
_HDR_TURES = 0.05

_HDR_GOLDEN = [
    ("hdr__min", "HDR=1,1.300000,1.000000,0.000000;", 0.188),
    ("hdr__alap", "HDR=1,20.000000,3.000000,0.000000;", 0.265),
    ("hdr__max", "HDR=1,80.000000,7.000000,100.000000;", 0.121),
    ("localcontrast__min", "LocalContrast=1,1.300000,1.000000;", 0.121),
    ("localcontrast__alap", "LocalContrast=1,15.000000,1.500000;", 0.159),
    ("localcontrast__max", "LocalContrast=1,40.000000,3.000000;", 0.258),
]


@pytest.mark.parametrize(
    ("eset", "lanc", "vart_de"), _HDR_GOLDEN, ids=[e[0] for e in _HDR_GOLDEN]
)
def test_hdr_golden_a_picasa_exporthoz(eset: str, lanc: str, vart_de: float) -> None:
    forras_ut = _KIT_684 / f"{eset}.jpg"
    export_ut = _KIT_684 / "export" / f"{eset}.jpg"
    if not export_ut.is_file():
        pytest.skip(f"a mérőkészlet nem elérhető: {export_ut}")
    utvonal = str(Path(__file__).resolve().parents[2] / "tools" / "golden")
    if utvonal not in sys.path:
        sys.path.insert(0, utvonal)
    from analyze_validation_kit import load, mean_de

    from picasapy.ini.filters import parse_filters
    from picasapy.render.chain import apply_filters

    kep = apply_filters(load(forras_ut), parse_filters(lanc)).image
    de = mean_de(kep, load(export_ut))
    assert de <= vart_de + _HDR_TURES, f"{eset}: ΔE {de:.3f} > {vart_de + _HDR_TURES:.3f}"


# ---------------------------------------------------------------------------
# #3827 — a belső ragyogás natív lánca, golden a 684-es készleten (fejlesztői
# gépen; ha a készlet nincs meg, skip). Mérve (CIE76 átlag-ΔE a Picasa-
# exporthoz, `analyze_validation_kit.mean_de`):
#
# | eset               | előtte (erf-modell) | utána (natív lánc) |
# |--------------------|--------------------:|-------------------:|
# | Vignette alap      | 0,585 | 0,169 |
# | Matte alap         | 0,910 | 0,176 |
# | MuseumMatte min    | 0,842 | 0,128 |
# | MuseumMatte alap   | 0,773 | 0,230 |
# | MuseumMatte max    | 0,645 | 0,287 |
# | Lomo alap / min    | 0,453 / 0,442 | 0,289 / 0,280 |
# | Holga alap / min   | 0,750 / 0,500 | 0,604 / 0,253 |
# | NightVision alap / min | 4,595 / 3,663 | 4,528 / 3,624 |
# | Comicize alap / max / min | 2,689 / 2,328 / 2,299 | 2,687 / 2,328 / 2,294 |
#
# A `Blur = 0` és a `Fade = 100` esetek (0,121) az újrakódolás zajszintje.
# A küszöb a mért érték + 0,05, de legfeljebb a jegy felső korlátja
# (Vignette, Matte, MuseumMatte), illetve a javítás előtti érték.
# ---------------------------------------------------------------------------

# rontás-kontroll: a súly 255-ös vágása elhagyva → 1 failed a
# `test_glimmer_ops.py`-ban (8.8-as súly) és 2 golden;
# a maszk 255-ös pereme elhagyva (a puffer = a kép) → 7 + 13 failed; a
# Mitchell-nagyítás helyett doboz → 4 + 7 failed; a MuseumMatte második
# blurja a gyűrűs kép méretéből → 2 golden (MuseumMatte alap, max).
# ⚠️ A perem-pótlás 255 → a szélső érték ismétlése NEM mutáció: a puffer
# szélén a maszk mindig 255, a kettő ott azonos (lefuttatva: 0 failed).

_GLOW_TURES = 0.05

#: (eset, lánc, mért ΔE a javítás után, a küszöb felső korlátja)
_GLOW_GOLDEN = [
    ("vignette__alap", "Vignette=1,35,1.400000,0,00000000;", 0.169, 0.3),
    ("vignette__min", "Vignette=1,0,1.000000,0,00000000;", 0.121, 0.122),
    ("matte__alap", "Matte=1,40.000000,1.200000,0.000000,00ffffff;", 0.176, 0.3),
    ("matte__min", "Matte=1,0.000000,1.000000,0.000000,00ffffff;", 0.121, 0.122),
    ("museummatte__min", "MuseumMatte=1,0.000000,0.000000,001a0e03,00f0eae4;", 0.128, 0.15),
    ("museummatte__alap", "MuseumMatte=1,25.000000,40.000000,001a0e03,00f0eae4;", 0.230, 0.25),
    ("museummatte__max", "MuseumMatte=1,100.000000,100.000000,001a0e03,00f0eae4;", 0.287, 0.3),
    ("lomo__alap", "Lomo=1,50.000000,0.000000;", 0.289, 0.453),
    ("lomo__min", "Lomo=1,0.000000,0.000000;", 0.280, 0.442),
    ("holga__alap", "Holga=1,70.000000,30.000000,0.000000;", 0.604, 0.750),
    ("holga__min", "Holga=1,0.000000,0.000000,0.000000;", 0.253, 0.500),
    ("nightvision__alap", "NightVision=1,0.000000,0.000000,0.000000;", 4.528, 4.595),
    ("nightvision__min", "NightVision=1,-50.000000,-50.000000,0.000000;", 3.624, 3.663),
    ("comicize__alap", "Comicize=1,20.000000,50.000000,50.000000;", 2.687, 2.690),
    ("comicize__max", "Comicize=1,100.000000,100.000000,100.000000;", 2.328, 2.329),
    ("comicize__min", "Comicize=1,0.000000,0.000000,0.000000;", 2.294, 2.300),
]


@pytest.mark.parametrize(
    ("eset", "lanc", "mert_de", "korlat"), _GLOW_GOLDEN, ids=[e[0] for e in _GLOW_GOLDEN]
)
def test_belso_ragyogas_golden_a_picasa_exporthoz(
    eset: str, lanc: str, mert_de: float, korlat: float
) -> None:
    forras_ut = _KIT_684 / f"{eset}.jpg"
    export_ut = _KIT_684 / "export" / f"{eset}.jpg"
    if not export_ut.is_file():
        pytest.skip(f"a mérőkészlet nem elérhető: {export_ut}")
    utvonal = str(Path(__file__).resolve().parents[2] / "tools" / "golden")
    if utvonal not in sys.path:
        sys.path.insert(0, utvonal)
    from analyze_validation_kit import load, mean_de

    from picasapy.ini.filters import parse_filters
    from picasapy.render.chain import apply_filters

    kep = apply_filters(load(forras_ut), parse_filters(lanc)).image
    kuszob = min(mert_de + _GLOW_TURES, korlat)
    de = mean_de(kep, load(export_ut))
    assert de <= kuszob, f"{eset}: ΔE {de:.3f} > {kuszob:.3f}"
