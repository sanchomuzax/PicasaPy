"""#878 — a `Neon` visszafejtett csővezetéke és a két új Glimmer-primitív.

A jegy leletje: a `Neon` a #685 mérőszettjének LEGROSSZABB effektje volt
(ΔE 113,89, SSIM −0,002), mert a modell szerkezetileg volt hibás. A javítás
után ugyanazon a golden páron ΔE 4,72 / SSIM 0,866.

A mérőszett képei nem kerülhetnek a publikus repóba, ezért az itteni őrök a
csővezeték **szerkezeti** állításait rögzítik — azokat, amelyek a régi
(Canny + szorzó-tint) modellel elbuknak —, valamint a `TintImageOperation`
golden párból MÉRT számhármasait.

#3812: az `EdgeDetectionB` elmosása a natív `BlurImageOperation(2, 2,
quality = 2)`, a Sobel egész aritmetikával számol
(`clamp(128 + floor(Σ/4))`). A `TestEdgeDetectionBNativ` független
referenciát épít a leírásból; a `TestNeonGolden` a 684-es mérőkészleten mér
(csak fejlesztői gépen, a NAS nélkül skip).
"""

# rontás-kontroll: ld. a `TestEdgeDetectionBNativ` előtti blokkot.

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from picasapy.render.glimmer_creative import apply_neon
from picasapy.render.glimmer_edges import _sobel_direction, edge_detection_b
from picasapy.render.glimmer_ops import (
    _haeberli_luma,
    adjust_curves,
    apply_blend_mode,
    simple_color_matrix,
    tint_luma_preserving,
)
from picasapy.render.nativ_blur import blur_image_operation

#: A `Tint` a HAEBERLI-lumát tartja meg, NEM a Rec.601-et (#3631) — a
#: `TestTintLumaPreserving` ezért ezekkel a súlyokkal mér.
HAEBERLI = (0.3086, 0.6094, 0.0820)


def _flat(value: int, height: int = 24, width: int = 32) -> np.ndarray:
    return np.full((height, width, 3), value, dtype=np.uint8)


def _hard_edge(height: int = 48, width: int = 64) -> np.ndarray:
    """Bal fele fekete, jobb fele fehér — egyetlen, maximálisan erős él."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, width // 2 :] = 255
    return image


def _luma_of(pixel) -> float:
    return float(sum(w * float(c) for w, c in zip(HAEBERLI, pixel, strict=True)))


class TestEdgeDetectionB:
    """`EdgeDetectionB` = FEHÉR alap, sötét élek (a háromszög-görbe miatt)."""

    def test_sik_felulet_feher_lesz(self):
        # A Sobel válasza sík felületen 0 → a 128-as eltolás után a
        # {(0,0),(128,255),(255,0)} görbe csúcsa: 255.
        result = edge_detection_b(_flat(120))
        assert result.min() >= 250, f"a sík felületnek fehérnek kell lennie, min={result.min()}"

    def test_eles_el_sotet_vonalat_ad(self):
        result = edge_detection_b(_hard_edge())
        middle = result[:, 30:34]
        assert middle.min() <= 5, f"az élnek sötétnek kell lennie, min={middle.min()}"

    def test_a_hatter_az_eltol_tavol_feher_marad(self):
        result = edge_detection_b(_hard_edge())
        assert result[:, :20].min() >= 250
        assert result[:, 44:].min() >= 250

    @pytest.mark.parametrize("detail", [-0.1, 100.1])
    def test_tartomanyon_kivuli_detail_hibat_dob(self, detail):
        with pytest.raises(ValueError, match="detail"):
            edge_detection_b(_flat(128), detail=detail)


# ---------------------------------------------------------------------------
# #3812 — a natív elmosás és az egész Sobel.
#
# rontás-kontroll: az elmosást visszaírva a régi `cv2.sepFilter2D`-s
# `[1,2,1]/4` magra → 5 failed (a négy referencia-próba és a golden
# `neon__alap`, ΔE 1,967 > 0,543); a Sobelt lebegőpontosra írva
# (`rint(total / 4)`) → 5 failed (a négy referencia-próba és a páratlan
# összegű próba; a golden ezt NEM fogja meg, mert ΔE-ben 0,493 marad); a 10.
# lépést Darkenre (1) írva → 4 failed (a négy referencia-próba). Ellenőrizve
# lefuttatva.
# ---------------------------------------------------------------------------

_SOBEL_V = ((-2, 0, 2), (-4, 0, 4), (-2, 0, 2))
_SOBEL_H = ((2, 4, 2), (0, 0, 0), (-2, -4, -2))
_EDGE_CURVE = ((0.0, 0.0), (128.0, 255.0), (255.0, 0.0))
_NATIVE_TOP_RIGHT_POSITIONS = {
    "TL": (0, -2),
    "C": (0, -1),
    "BL": (1, -2),
    "B": (1, -1),
}
_NATIVE_TOP_RIGHT_BGRA = {
    (0, "TL"): (120, 116, 108, 255),
    (0, "C"): (104, 84, 60, 255),
    (0, "BL"): (152, 180, 204, 255),
    (0, "B"): (104, 84, 60, 255),
    (1, "TL"): (176, 216, 255, 255),
    (1, "C"): (160, 184, 216, 255),
    (1, "BL"): (144, 152, 168, 255),
    (1, "B"): (96, 56, 24, 255),
}


def _egesz_sobel(kep: np.ndarray, mag) -> np.ndarray:
    """A leírás képlete: `clamp((512 + Σ kᵢ·pᵢ) idiv 4, 0, 255)`, a peremen
    ismétlődő képponttal, kivéve a specifikáció szerinti jobb felső sarkot.
    Az `idiv` nulla felé csonkol; negatív osztandónál az eredmény úgyis 0-ra
    vágódik."""
    h, w = kep.shape[:2]
    pixels = kep.astype(np.int64)
    pad = np.pad(pixels, ((1, 1), (1, 1), (0, 0)), mode="edge")
    osszeg = np.full(kep.shape, 512, dtype=np.int64)
    for dy in range(3):
        for dx in range(3):
            osszeg += mag[dy][dx] * pad[dy : dy + h, dx : dx + w]
    if np.array_equal(mag, _SOBEL_V):
        osszeg[0, -1] = 512 + 4 * pixels[1, -2] - 2 * pixels[1, -1] - 2 * pixels[0, -1]
    elif np.array_equal(mag, _SOBEL_H):
        osszeg[0, -1] = 512 + 4 * pixels[0, -2] + 2 * pixels[0, -1] - 6 * pixels[1, -1]
    hanyados = np.trunc(osszeg / 4).astype(np.int64)
    return np.clip(hanyados, 0, 255).astype(np.uint8)


def _referencia(kep: np.ndarray, detail: float) -> np.ndarray:
    """Független referencia a natív lépéssorból (`0x00bbca60`)."""
    elokeszitett = simple_color_matrix(
        blur_image_operation(kep, 2.0, 2.0, quality=2), contrast=100.0 - detail
    )
    fuggoleges = adjust_curves(_egesz_sobel(elokeszitett, _SOBEL_V), master=_EDGE_CURVE)
    vizszintes = adjust_curves(_egesz_sobel(elokeszitett, _SOBEL_H), master=_EDGE_CURVE)
    kevert = apply_blend_mode(
        vizszintes.astype(np.float32), fuggoleges.astype(np.float32), 5, 1.0
    )
    return np.clip(np.rint(kevert), 0, 255).astype(np.uint8)


class TestEdgeDetectionBNativ:
    @pytest.mark.parametrize("detail", [50.0, 0.0, 87.0])
    def test_bitre_a_referencia_szerint(self, detail):
        rng = np.random.default_rng(3812)
        kep = rng.integers(0, 256, size=(37, 45, 3), dtype=np.uint8)
        np.testing.assert_array_equal(edge_detection_b(kep, detail), _referencia(kep, detail))

    def test_sima_atmenet_bitre_a_referencia_szerint(self):
        """Lágy színátmenet: itt a Sobel-összeg kicsi, a kerekítés számít."""
        y, x = np.mgrid[0:40, 0:52]
        kep = np.stack([x * 3, y * 5, (x + y) * 2], axis=-1).clip(0, 255).astype(np.uint8)
        np.testing.assert_array_equal(edge_detection_b(kep), _referencia(kep, 50.0))

    def test_paratlan_osszeg_lefele_kerekit(self):
        """Egy 1 szintes lépcső, amely a felső sorban hiányzik: ott a
        (kétszeres súlyú) Sobel-összeg ±2, a második sorban ±6. A döntő a
        lefelé lépő él: `floor(−2/4) = −1` → 127, míg lebegőpontosan és
        kerekítve 127,5 → 128 jönne ki; `floor(6/4) = 1` → 129 a 129,5 → 130
        helyett."""
        kep = np.zeros((5, 6, 3), dtype=np.uint8)
        kep[:, 3:] = 1  # függőleges él, a `_SOBEL_V` érzékeli
        kep[0, 3:] = 0  # a felső sorban a lépcső hiányzik → ±2-es összegek
        ki = _sobel_direction(kep, np.array(_SOBEL_V, dtype=np.int32))
        np.testing.assert_array_equal(ki, _egesz_sobel(kep, _SOBEL_V))
        ki_le = _sobel_direction(1 - kep, np.array(_SOBEL_V, dtype=np.int32))
        np.testing.assert_array_equal(ki_le, _egesz_sobel(1 - kep, _SOBEL_V))
        assert (ki_le == 127).any(), ki_le[..., 0]

    @pytest.mark.parametrize(("height", "width"), [(5, 8), (5, 9)])
    @pytest.mark.parametrize(
        ("direction", "source"),
        [(0, source) for source in ("TL", "C", "BL", "B")]
        + [(1, source) for source in ("TL", "C", "BL", "B")],
    )
    def test_natív_jobb_felső_sarok_impulzusértékei(self, height, width, direction, source):
        """A QEMU-peremtérkép négy szomszédját impulzusokkal ellenőrzi.

        A specifikáció a QEMU-próba 8×5 és 9×5 bemeneti képpontjait nem írja
        le, ezért a rögzített, irányonkénti natív együtthatókat használó
        impulzuspróba ellenőrzi a jobb felső BGRA-értéket. Az alfa a natív
        mérésben változatlanul 255.
        """
        kep = np.zeros((height, width, 3), dtype=np.uint8)
        impulse = np.array((32, 64, 96), dtype=np.uint8)
        mag = _SOBEL_V if direction == 0 else _SOBEL_H
        impulses = {source: impulse}
        # A második impulzus a natív nulla együtthatót is láthatóvá teszi.
        anchor = "C" if direction == 0 else "TL"
        anchor_impulse = np.array((16, 24, 40), dtype=np.uint8)
        if anchor in impulses:
            impulses[anchor] = impulses[anchor] + anchor_impulse
        else:
            impulses[anchor] = anchor_impulse
        for position, value in impulses.items():
            y, x = _NATIVE_TOP_RIGHT_POSITIONS[position]
            kep[y, x] = value

        vart = _egesz_sobel(kep, mag)
        vart_bgra = _NATIVE_TOP_RIGHT_BGRA[(direction, source)]
        vart_bgr = np.array(vart_bgra[:3], dtype=np.uint8)
        vart[0, -1] = vart_bgr

        kapott = _sobel_direction(kep, np.array(mag, dtype=np.int32))
        np.testing.assert_array_equal(kapott, vart)
        kapott_bgra = tuple(int(channel) for channel in kapott[0, -1]) + (255,)
        assert kapott_bgra == vart_bgra

    @pytest.mark.parametrize(("height", "width"), [(2, 4), (4, 2), (2, 2)])
    @pytest.mark.parametrize("mag", [_SOBEL_V, _SOBEL_H])
    def test_harom_alatti_meretnel_nincs_sobel_feldolgozas(self, height, width, mag):
        kep = np.arange(height * width * 3, dtype=np.uint8).reshape(height, width, 3)
        np.testing.assert_array_equal(
            _sobel_direction(kep, np.array(mag, dtype=np.int32)),
            kep,
        )

    def test_a_bemenet_nem_mutalodik(self):
        kep = np.random.default_rng(1).integers(0, 256, size=(9, 11, 3), dtype=np.uint8)
        masolat = kep.copy()
        edge_detection_b(kep)
        np.testing.assert_array_equal(kep, masolat)


class TestNeonGolden:
    """A 684-es mérőkészlet `neon__*` párjai (FEJLESZTŐI GÉPEN; a NAS nélkül
    skip). A határ a #3812 után mért érték + 0,05, de legfeljebb 0,55."""

    _KIT = Path("/mnt/nas/My Pictures/684-merokeszlet")

    #: (név, lánc, a #3812 után mért ΔE)
    _ESETEK = [
        ("neon__alap", "Neon=1,0.000000,00ff0000;", 0.493),
        ("neon__max", "Neon=1,100.000000,00ff0000;", 0.121),
    ]

    @pytest.mark.parametrize(("nev", "lanc", "vart_de"), _ESETEK, ids=[e[0] for e in _ESETEK])
    def test_684_merokeszlet_neon(self, nev, lanc, vart_de):
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
        hatar = min(vart_de + 0.05, 0.55)
        assert de <= hatar, f"{nev}: ΔE {de:.3f} > {hatar:.3f}"


class TestTintLumaPreserving:
    """`TintImageOperation`: a bemenet HAEBERLI-luminanciáját a
    csatornánkénti csonkolásig (~1 szint) megőrzi (NEM Rec.601-ét, #3631)."""

    @pytest.mark.parametrize("value", [0, 16, 64, 128, 200, 255])
    @pytest.mark.parametrize("color", [(128, 207, 255), (255, 0, 0), (0, 255, 0)])
    def test_a_luminancia_megmarad(self, value, color):
        # A natív tábla csatornánként CSONKOL, ezért a lumát csak ~1 szintre
        # tartja: az emulált táblán (54 szín, `tint_resaturate_3631.json`) a
        # legnagyobb eltérés 1,415 (0x80cfff-nél L=16-on 1,002) — ez a mérce.
        result = tint_luma_preserving(_flat(value), color)
        assert abs(float(_haeberli_luma(result.astype(np.float32)).mean()) - value) <= 1.5

    def test_fekete_fekete_marad_es_feher_feher(self):
        # Ez a döntő különbség a szorzó-tinthez képest: a szorzó-tint a
        # feketéből is, a fehérből is TISZTA SZÍNT csinálna.
        assert tint_luma_preserving(_flat(0), (255, 0, 0)).max() == 0
        assert tint_luma_preserving(_flat(255), (255, 0, 0)).min() == 255

    @pytest.mark.parametrize(
        ("value", "expected"),
        [(16, (0, 16, 65)), (128, (69, 147, 195)), (248, (231, 255, 255))],
    )
    def test_mert_golden_harmasok(self, value, expected):
        """A #685 `picniktint__alap.jpg` golden párjából mért mediánok
        (`PicnikTint=1,0.000000,0080cfff;`, szín RGB `(128, 207, 255)`).
        A 248-as sor a döntő: két csatorna 255-ön áll, a harmadik pontosan
        arra az értékre, amellyel a luminancia visszajön.
        """
        result = tint_luma_preserving(_flat(value), (128, 207, 255))[0, 0]
        assert np.allclose(result, expected, atol=3), f"{tuple(int(c) for c in result)} != {expected}"
        assert abs(_luma_of(result) - value) <= 1.5


class TestNeon:
    def test_fade_100_bajtra_valtozatlan(self):
        image = _hard_edge()
        np.testing.assert_array_equal(apply_neon(image, fade=100.0), image)

    def test_sik_felulet_feketere_valt(self):
        """A régi Canny-modell itt FEHÉR (invertált, tint nélkül üres)
        képet adott; a valódi Neon sík felületen FEKETE."""
        result = apply_neon(_flat(120), fade=0.0)
        assert result.max() <= 5, f"a sík felületnek feketének kell lennie, max={result.max()}"

    def test_az_el_vilagos_vonalkent_marad_meg(self):
        result = apply_neon(_hard_edge(), fade=0.0)
        assert result[:, 30:34].max() >= 200
        assert result[:, :20].max() <= 5

    def test_a_fade_monoton_halvanyit(self):
        """0 → 100 között a kimenet MONOTON közelít az eredetihez."""
        image = _hard_edge()
        source = image.astype(np.int32)
        distances = [
            float(np.abs(apply_neon(image, fade=fade).astype(np.int32) - source).mean())
            for fade in (0.0, 25.0, 50.0, 75.0, 100.0)
        ]
        assert distances == sorted(distances, reverse=True), distances
        assert distances[-1] == 0.0

    def test_a_szin_a_kozepes_eleket_festi(self):
        """A neonszín a NEM telített éleken látszik: zöld színnel a zöld
        csatorna vezet. (Szorzó-tinttel a fehér élmag is színes lenne.)"""
        gradient = np.tile(
            np.linspace(0, 255, 64, dtype=np.uint8)[np.newaxis, :, np.newaxis], (48, 1, 3)
        )
        result = apply_neon(gradient, color=(0, 255, 0), fade=0.0).astype(np.int32)
        colored = result[..., 1] > result[..., 0]
        assert colored.any(), "a neonszínnek meg kell jelennie a képen"
