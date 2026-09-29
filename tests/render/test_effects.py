"""A `picasapy.render.effects` térbeli effektek tesztjei a golden-elemzés
mérési pontjai ellen (`docs/specs/filters-decoded.md`, 3–4. kör).

Ahol van mért adat (Vignette-maszk, glow középemelés), ott ±1/255 a tűrés;
a `radsat` a spec képpontonkénti alakjához bájtra egyezik (#3517), és a
684-es Picasa-exporthoz is mérve van (lent, golden).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.effects import (
    GLOW_V1_INTENSITY,
    GLOW_V1_RADIUS,
    apply_glow,
    apply_radblur,
    apply_radsat,
    apply_vignette,
    vignette_gain,
)


def _uniform_image(
    value: int | tuple[int, int, int], height: int = 6, width: int = 8
) -> np.ndarray:
    return np.full((height, width, 3), value, dtype=np.uint8)


def _radsat_referencia(
    image: np.ndarray, x: float, y: float, size: float, sharpness: float
) -> np.ndarray:
    """Független, képpontonkénti átirat a `filters-decoded.md` „radsat —
    TELJES" (#317) C-alakjából (`0x0090aeb0` tábla + `0x0090b660` mag)."""
    import math

    height, width = image.shape[:2]
    r = min(width / 2.0, height / 2.0) * (size + 1.0)
    r2 = r * r
    shift = 0
    while r2 > 1024.0:
        r2 *= 0.5
        shift += 1
    k = 1.0 / (1.0 - 0.99 * math.sqrt(sharpness))
    tabla = []
    for i in range(1024):
        t = math.sqrt(i / r2) if r2 > 0 else math.inf
        v = 1.0 - min(max(0.5 + k * (t - 0.5), 0.0), 1.0)
        # a tábla CSONKOL (`or eax, 0xc00` a `fistp` előtt, #3946)
        tabla.append(math.trunc((3.0 - 2.0 * v) * v * v * 255.0))
    cx, cy = round(width * x), round(height * y)
    out = np.empty_like(image)
    for py in range(height):
        for px in range(width):
            red, green, blue = (int(c) for c in image[py, px])
            luma = (77 * red + 151 * green + 28 * blue) >> 8
            idx = ((px - cx) ** 2 + (py - cy) ** 2) >> shift
            if idx < 1024:
                w = 256 - tabla[idx]
                out[py, px] = [c + (((luma - c) * w) >> 8) for c in (red, green, blue)]
            else:
                out[py, px] = [luma, luma, luma]
    return out


class TestVignetteGain:
    # Mért radiális profil (golden 4. kör, Vignette=1,35.0,1.4,0.0,00000000):
    # közép 1,000 · r≈0,25: 0,994 · r≈0,45: 0,729 · r≈0,65: 0,328 · sarok 0,250
    def test_mert_profil_pontjai(self) -> None:
        assert vignette_gain(0.0) == pytest.approx(1.0, abs=0.004)
        assert vignette_gain(0.25) == pytest.approx(0.994, abs=0.004)
        assert vignette_gain(0.45) == pytest.approx(0.729, abs=0.004)
        assert vignette_gain(0.65) == pytest.approx(0.328, abs=0.004)

    def test_sarkon_tuli_ertek_klippel(self) -> None:
        # a sarok (r≈0,7071) mért értéke 0,250; azon túl nem csökken tovább
        assert vignette_gain(0.7071) == pytest.approx(0.250, abs=0.004)
        assert vignette_gain(0.9) == pytest.approx(0.250, abs=0.004)

    def test_monoton_csokkeno(self) -> None:
        radii = np.linspace(0.0, 0.7071, 30)
        gains = [vignette_gain(float(r)) for r in radii]
        # szomszédos-pár (pairwise) összehasonlítás — szándékosan eggyel
        # rövidebb a második sorozat.
        assert all(a >= b for a, b in zip(gains, gains[1:], strict=False))

    def test_negativ_sugar_value_error(self) -> None:
        with pytest.raises(ValueError):
            vignette_gain(-0.1)


class TestApplyVignette:
    def test_kozeppont_valtozatlan(self) -> None:
        image = _uniform_image(200, height=51, width=51)
        result = apply_vignette(image)
        assert int(result[25, 25, 0]) == 200

    def test_sarok_a_mert_maszkkal_sotetul(self) -> None:
        # nagy képen a sarokpixel r-je ≈0,706 → gain ≈0,250 → 200·0,25 = 50
        image = _uniform_image(200, height=201, width=201)
        result = apply_vignette(image)
        assert abs(int(result[0, 0, 0]) - 50) <= 2

    def test_mert_pont_r045(self) -> None:
        # r=0,45 → gain 0,729 → 200·0,729 = 145,8 ≈ 146 (±1)
        image = _uniform_image(200, height=201, width=201)
        result = apply_vignette(image)
        # a (100, 100) középponttól vízszintesen r=0,45-re eső pixel: x≈190,5
        column = 190
        radius = (column + 0.5) / 201 - 0.5
        expected = 200.0 * vignette_gain(abs(radius))
        assert abs(int(result[100, column, 0]) - round(expected)) <= 1

    def test_multiplikativ_fekete_fekete_marad(self) -> None:
        image = _uniform_image(0, height=21, width=21)
        result = apply_vignette(image)
        np.testing.assert_array_equal(result, image)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(180, height=11, width=11)
        original = image.copy()
        apply_vignette(image)
        np.testing.assert_array_equal(image, original)

    def test_hibas_bemenet_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_vignette(np.zeros((4, 4), dtype=np.uint8))

    def test_erosseg_nulla_identitas(self) -> None:
        image = _uniform_image(200, height=21, width=21)
        result = apply_vignette(image, strength=0.0)
        np.testing.assert_array_equal(result, image)


class TestApplyGlow:
    # Mért középemelés sík szürkén. A 3. kör 144/151-es értékeit a #668
    # ÚJRAMÉRTE a `golden-kit/09-effects` VALÓDI Picasa-exportjának sík
    # szürke foltjain: 128 → 141,92 (v1) és 128 → 148,86 (v2). A régi
    # számok a Gauss-modellhez tapadtak, nem a goldenhez.
    # A teljes tónusválasz-sor: `test_glow_radblur_668.py`.
    def test_glow_v1_mert_kozepemeles(self) -> None:
        image = _uniform_image(128, height=32, width=32)
        result = apply_glow(image, GLOW_V1_INTENSITY, GLOW_V1_RADIUS)
        assert abs(int(result[16, 16, 0]) - 142) <= 1

    def test_glow2_mert_kozepemeles(self) -> None:
        image = _uniform_image(128, height=32, width=32)
        result = apply_glow(image, 0.65, 3.0)
        assert abs(int(result[16, 16, 0]) - 149) <= 1

    def test_nulla_intenzitas_identitas(self) -> None:
        image = _uniform_image((30, 90, 200))
        result = apply_glow(image, 0.0, 3.0)
        np.testing.assert_array_equal(result, image)

    def test_feher_nem_lo_tul(self) -> None:
        image = _uniform_image(255)
        result = apply_glow(image, 1.0, 3.0)
        assert result.max() <= 255

    def test_vilagosit_sohasem_sotetit(self) -> None:
        # a screen-keverés monoton: ki >= be minden pixelen
        rng = np.random.default_rng(7)
        image = rng.integers(0, 256, size=(16, 16, 3), dtype=np.uint8)
        result = apply_glow(image, 0.65, 3.0)
        assert np.all(result.astype(int) >= image.astype(int))

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(128)
        original = image.copy()
        apply_glow(image, 0.65, 3.0)
        np.testing.assert_array_equal(image, original)


class TestApplyRadblur:
    def test_nulla_amount_sem_azonossag(self) -> None:
        # A korábbi modell az amount=0-t no-opnak vette; a #668 mérése ezt
        # MEGCÁFOLTA (`golden-kit/09-effects`, `radblur=1,…,0,0`: a peremen
        # a kép átlagosan 26 szintnyit változik). Részletek:
        # `test_glow_radblur_668.py`.
        rng = np.random.default_rng(3)
        image = rng.integers(0, 256, size=(120, 160, 3), dtype=np.uint8)
        result = apply_radblur(image, 0.5, 0.5, 0.0, 0.0)
        assert not np.array_equal(result, image)

    def test_kozeppont_eles_marad(self) -> None:
        rng = np.random.default_rng(5)
        image = rng.integers(0, 256, size=(40, 40, 3), dtype=np.uint8)
        result = apply_radblur(image, 0.5, 0.5, 0.3, 0.8)
        # A megadott középpont a védett zónán belül gyakorlatilag változatlan
        # — a natív súlytábla maximuma 255/256, ezért 1 szint eltérés belefér.
        assert np.all(np.abs(result[20, 20].astype(int) - image[20, 20]) <= 1)

    def test_szel_elmosodik(self) -> None:
        # kontrasztos sakktáblán a szélső sáv szórása csökken
        image = np.zeros((40, 40, 3), dtype=np.uint8)
        image[::2, ::2] = 255
        image[1::2, 1::2] = 255
        result = apply_radblur(image, 0.5, 0.5, 0.1, 1.0)
        edge_before = float(np.std(image[0, :, 0].astype(np.float64)))
        edge_after = float(np.std(result[0, :, 0].astype(np.float64)))
        assert edge_after < edge_before

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(90, height=16, width=16)
        original = image.copy()
        apply_radblur(image, 0.5, 0.5, 0.2, 0.7)
        np.testing.assert_array_equal(image, original)


class TestApplyRadsat:
    """#3517: a `radsat` („Fókuszos FF") a `filters-decoded.md` „radsat —
    TELJES" algoritmusa szerint számol (smoothstep-tábla, 77/151/28 luma,
    fordulópont a sugár FELÉNÉL, a táblán túl teljes szürke)."""

    def test_kozeppont_telitettsege_megmarad(self) -> None:
        # A középen a tábla 255, a súly tehát 1/256: legfeljebb egy szint.
        image = _uniform_image((200, 80, 80), height=41, width=41)
        result = apply_radsat(image, 0.5, 0.5, 0.4, 1.0)
        diff = np.abs(result[20, 20].astype(int) - image[20, 20].astype(int))
        assert int(diff.max()) <= 1

    def test_sarok_szurkul(self) -> None:
        image = _uniform_image((200, 80, 80), height=41, width=41)
        result = apply_radsat(image, 0.5, 0.5, 0.2, 1.0)
        corner = result[0, 0]
        assert int(corner[0]) == int(corner[1]) == int(corner[2])

    def test_sarok_lumaja_a_77_151_28_sulyokkal(self) -> None:
        image = _uniform_image((200, 80, 80), height=41, width=41)
        result = apply_radsat(image, 0.5, 0.5, 0.2, 1.0)
        luma = (77 * 200 + 151 * 80 + 28 * 80) >> 8
        assert int(result[0, 0, 0]) == luma

    def test_maximum_allas_is_hat(self) -> None:
        """A régi modell `méret = 1`-nél a teljes képet érintetlenül hagyta
        (#3517 „max: nem hat"); az eredetiben a fordulópont a sugár felénél
        van, tehát a sarok ott is szürke."""
        image = _uniform_image((200, 80, 80), height=21, width=21)
        result = apply_radsat(image, 0.5, 0.5, 1.0, 1.0)
        corner = result[0, 0]
        assert int(corner[0]) == int(corner[1]) == int(corner[2])

    @pytest.mark.parametrize(
        ("height", "width", "x", "y", "size", "sharpness"),
        [
            (23, 31, 0.5, 0.5, 0.0, 0.5),
            (40, 70, 0.3, 0.6, 1.0, 1.0),
            (37, 29, 0.5, 0.5, -1.0, 0.0),
            (64, 48, 0.8, 0.2, 0.4, 0.25),
        ],
    )
    def test_egyezik_a_spec_kepontonkenti_alakjaval(
        self, height: int, width: int, x: float, y: float, size: float, sharpness: float
    ) -> None:
        rng = np.random.default_rng(3517)
        image = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
        np.testing.assert_array_equal(
            apply_radsat(image, x, y, size, sharpness),
            _radsat_referencia(image, x, y, size, sharpness),
        )

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image((150, 60, 40), height=15, width=15)
        original = image.copy()
        apply_radsat(image, 0.5, 0.5, 0.3, 0.5)
        np.testing.assert_array_equal(image, original)

    def test_zonaja_kor_4_3_aranyu_kepen(self) -> None:
        """4:3 arányú képen a zóna KÖR — a középponttól AZONOS KÉPPONT-
        távolságra eső pontok (egyszer vízszintesen, egyszer függőlegesen)
        AZONOS mértékben telítetlenednek (#859: a natív képlet izotróp, a
        kép RÖVIDEBB oldalához méretezve, nem tengelyenként).

        KÉPPONTBAN mérve: a hiba előtti (tengelyenkénti) rácsnál ugyanez a
        mérés `[171, 92, 92]` (vízszintes) vs `[150, 101, 101]`
        (függőleges) — egyértelműen ELTÉRŐ értéket adott (lemérve, 2026).
        """
        height, width = 300, 400  # 4:3, tehát min(w,h) = 300
        image = _uniform_image((200, 80, 80), height=height, width=width)
        result = apply_radsat(image, 0.5, 0.5, 0.2, 0.5)
        center_y, center_x = height // 2, width // 2
        distance = 149  # < min(w,h)/2, tehát mindkét irányban a képen belül

        horizontal = result[center_y, center_x + distance]
        vertical = result[center_y + distance, center_x]
        np.testing.assert_array_equal(horizontal, vertical)

    def test_aranyosan_ugyanakkora_4_3_es_1_1_kepen(self) -> None:
        """Azonos `min(szélesség, magasság)` mellett a zóna KÉPPONTBAN mért
        mérete ne függjön a képarányától (#859 „Kész, ha" 5. pontja).

        KÉPPONTBAN mérve: a hiba előtti rácsnál a 4:3-as kép vízszintes
        metszete `[171, 92, 92]`, az 1:1-esé `[150, 101, 101]` volt —
        ELTÉRT, holott mindkét kép rövidebb oldala 300 (lemérve, 2026).
        """
        distance = 149  # < 300 / 2, mindkét képen belül van
        image_4_3 = _uniform_image((200, 80, 80), height=300, width=400)
        result_4_3 = apply_radsat(image_4_3, 0.5, 0.5, 0.2, 0.5)
        horizontal_4_3 = result_4_3[150, 200 + distance]

        image_1_1 = _uniform_image((200, 80, 80), height=300, width=300)
        result_1_1 = apply_radsat(image_1_1, 0.5, 0.5, 0.2, 0.5)
        horizontal_1_1 = result_1_1[150, 150 + distance]

        np.testing.assert_array_equal(horizontal_4_3, horizontal_1_1)


# ---------------------------------------------------------------------------
# #3517 — FEJLESZTŐI GÉPEN futó golden-mérés a 684-es készlet Picasa-
# exportjával (`radsat__alap/max/min`); ha a készlet nincs a gépen, skip.
# Mérve (CIE76 átlag-ΔE a Picasa-exporthoz, `analyze_validation_kit.mean_de`):
#
# | eset                 | előtte (régi közelítés) | utána (spec) |
# |----------------------|------------------------:|-------------:|
# | alap (méret 0; 0,5)  | 6,468                   | 0,082        |
# | max  (méret 1; 1)    | 3,657 — nem hatott      | 0,128        |
# | min  (méret −1; 0)   | 2,730                   | 0,034        |
# ---------------------------------------------------------------------------

# rontás-kontroll: az `apply_radsat` lumája 76/150/30-ra átírva → 6 failed
# (a sarok-luma, mind a négy spec-egyezés és a golden `min`); az élesség
# gyöke elhagyva → 3 failed (két spec-egyezés és a golden `alap`); a táblán
# túl a kép érintetlenül hagyva → 4 failed (két spec-egyezés, a golden
# `alap` és `min`).

_KIT_684 = Path("/mnt/nas/My Pictures/684-merokeszlet")

#: A mért érték + 0,05-ös tűrés.
_RADSAT_TURES = 0.05

_RADSAT_GOLDEN = [
    ("alap", "radsat=1,0.500000,0.500000,0.000000,0.500000;", 0.082),
    ("max", "radsat=1,0.500000,0.500000,1.000000,1.000000;", 0.128),
    ("min", "radsat=1,0.500000,0.500000,-1.000000,0.000000;", 0.034),
]


@pytest.mark.parametrize(
    ("eset", "lanc", "vart_de"), _RADSAT_GOLDEN, ids=[e[0] for e in _RADSAT_GOLDEN]
)
def test_radsat_golden_a_picasa_exporthoz(eset: str, lanc: str, vart_de: float) -> None:
    forras_ut = _KIT_684 / f"radsat__{eset}.jpg"
    export_ut = _KIT_684 / "export" / f"radsat__{eset}.jpg"
    if not export_ut.is_file():
        pytest.skip(f"a mérőkészlet nem elérhető: {export_ut}")
    utvonal = str(Path(__file__).resolve().parents[2] / "tools" / "golden")
    if utvonal not in sys.path:
        sys.path.insert(0, utvonal)
    from analyze_validation_kit import load, mean_de

    kep = apply_filters(load(forras_ut), parse_filters(lanc)).image
    de = mean_de(kep, load(export_ut))
    assert de <= vart_de + _RADSAT_TURES, f"{eset}: ΔE {de:.3f} > {vart_de + _RADSAT_TURES:.3f}"
