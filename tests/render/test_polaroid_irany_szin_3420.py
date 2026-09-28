"""#3420: a Polaroid forgatási IRÁNYA és a képkeret SZÍNE az eredeti szerint.

A 684-es golden-készlet (`\\\\DS215j\\lemez\\My Pictures\\684-merokeszlet`)
három Polaroid-exportja mellett a renderünk ΔE-je 18,7–22,7 volt, pedig a
kimenet mérete képpontra egyezett (#1144). Az egymás melletti kép két
szerkezeti eltérést mutatott, és a szállított `filterdesc.xml` mindkettőt
kimondja:

1. `SimpleBorderImageOperation ... color="0xffffff"` — a képkeret FEHÉR; a
   paraméter színe (`_cpkrOuter`, alap `E2E2E2`) csak az árnyék hátterére és
   a forgatás kitöltésére megy.
2. `RotateImageOperation degAngle="{_sldrRotate.value}"` — a Picasa pozitív
   szöge az óramutató JÁRÁSA szerint dönt (az exporton `Rotate = 5`-nél a
   keret felső éle jobbra LEJT); az OpenCV pozitív szöge fordítva forgat.

⚠️ A golden-képek a NAS-on vannak, ezért ez a próba szintetikus képen méri
a két szerkezeti tulajdonságot.

## #3809 — a geometria: floor-os eltolás, uniós margó, képpontközepes forgatás

A tartalom 1–3 képponttal el volt tolva (golden ΔE 0,69 / 1,10 / 2,58).
Három ok (`docs/specs/filterdesc-registry.md`, „A Polaroid geometriája”):

1. az árnyék eltolása `floor` (`test_arnyek_eltolas_649.py`);
2. az árnyék vászna az eredeti és az eltolt-kiterjesztett doboz UNIÓJA:
   bal `11 − dx`, fent `11 − dy`, jobb `11 + dx`, lent `11 + dy`;
3. a forgatás (`0x00bc8060`) `T(sW/2, sH/2) · R · T(−dW/2, −dH/2)`, a
   képpont közepét (`+0,5`) vetíti vissza, és a mintavevő (`0x009e7060`)
   8 bites súlyú fixpontos bilineáris: `a + floor((b − a)·f/256)`, a perem
   egy képpontos sávjában a szélső képpont ismétlődik, azon kívül a vászon
   színe marad.

A golden-mérés a fájl végén (684-merokeszlet, a Picasa-exporthoz).
"""

# rontás-kontroll: az `apply_polaroid` a régi `pads=(11, 11, 11, 11)`-gyel →
# 8 failed (a `TestUniosMargo` öt próbája és a három Polaroid-golden); a
# mintavevő `- 32767` helyett `- 0`-val (sarok-konvenció) → 10 failed (a
# 180°/90°/0°-os pontos próbák, a négy fixpontos próba, a három golden); a
# perem egy képpontos sávja nélkül (`0 ≤ ix ≤ W − 2`) → 7 failed; a lerp
# `floor` helyett kerekítéssel (`+ 128`) → 4 failed (a fixpontos próbák —
# a golden ezt NEM látja). Ellenőrizve lefuttatva.

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

from picasapy.render import glimmer_frames
from picasapy.render.glimmer_frame_ops import drop_shadow_padding, rotate_with_pad
from picasapy.render.glimmer_frames import apply_polaroid

HATTER = (0xE2, 0xE2, 0xE2)


def _kep() -> np.ndarray:
    # sötét, egyszínű fénykép — a fehér keret így egyértelműen elválik tőle
    return np.full((400, 600, 3), 40, dtype=np.uint8)


def _felso_feher_sor(kep: np.ndarray, oszlop: int) -> int:
    """Az adott oszlop első TISZTA fehér képpontjának sora (a keret teteje)."""
    feher = np.all(kep[:, oszlop] >= 250, axis=-1)
    sorok = np.flatnonzero(feher)
    assert sorok.size, f"a(z) {oszlop}. oszlopban nincs fehér keret"
    return int(sorok[0])


class TestKeretSzin:
    def test_a_kepkeret_feher_a_hatter_a_megadott_szin(self):
        ki = apply_polaroid(_kep(), 0.0, HATTER)
        h, w = ki.shape[:2]
        # a felirat-sáv közepe: a keret alsó, széles része
        assert tuple(int(c) for c in ki[int(h * 0.85), w // 2]) == (255, 255, 255)
        # a vászon sarka: a háttér (árnyék-margó)
        assert tuple(int(c) for c in ki[0, 0]) == HATTER

    def test_a_szin_parameter_nem_festi_at_a_keretet(self):
        ki = apply_polaroid(_kep(), 0.0, (0x20, 0x40, 0x80))
        h, w = ki.shape[:2]
        assert tuple(int(c) for c in ki[int(h * 0.85), w // 2]) == (255, 255, 255)


class TestForgatasIranya:
    @pytest.mark.parametrize("szog", [5.0, 10.0])
    def test_pozitiv_szognel_a_felso_el_jobbra_lejt(self, szog):
        ki = apply_polaroid(_kep(), szog, HATTER)
        w = ki.shape[1]
        bal, jobb = _felso_feher_sor(ki, w // 3), _felso_feher_sor(ki, 2 * w // 3)
        assert jobb > bal, (bal, jobb)

    def test_negativ_szognel_jobbra_emelkedik(self):
        ki = apply_polaroid(_kep(), -10.0, HATTER)
        w = ki.shape[1]
        bal, jobb = _felso_feher_sor(ki, w // 3), _felso_feher_sor(ki, 2 * w // 3)
        assert jobb < bal, (bal, jobb)


# ---------------------------------------------------------------------------
# #3809 — az árnyék vásznának uniós margója
# ---------------------------------------------------------------------------


class TestUniosMargo:
    @pytest.mark.parametrize("szog", [5.0, 10.0, -10.0, 0.0])
    def test_a_pads_a_drop_shadow_kiterjesztoje(self, szog, monkeypatch):
        """Az `apply_polaroid` ugyanazt az uniós margót adja át, mint az
        önálló `DropShadow` (`drop_shadow_padding(3, 90 − forgatás, 8)`)."""
        atadott = {}
        eredeti = glimmer_frames.compose_drop_shadow

        def figyelo(*args, **kwargs):
            atadott["pads"] = kwargs.get("pads")
            return eredeti(*args, **kwargs)

        monkeypatch.setattr(glimmer_frames, "compose_drop_shadow", figyelo)
        apply_polaroid(_kep(), szog, HATTER)
        _, _, vart = drop_shadow_padding(3, 90.0 - szog, 8)
        assert atadott["pads"] == vart

    def test_forgatas_nelkul_a_keret_teteje_a_8_sorban(self):
        """0°-nál `(dx, dy) = (0, 3)`, tehát fent `11 − 3 = 8` képpont a
        margó (nem 11), bal oldalt 11."""
        ki = apply_polaroid(_kep(), 0.0, HATTER)
        w = ki.shape[1]
        assert _felso_feher_sor(ki, w // 2) == 8
        bal = np.flatnonzero(np.all(ki[ki.shape[0] // 2] >= 250, axis=-1))
        assert int(bal[0]) == 11


# ---------------------------------------------------------------------------
# #3809 — a képpontközepes forgatás és a fixpontos mintavevő
# ---------------------------------------------------------------------------


def _veletlen(magas: int, szeles: int, seed: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, size=(magas, szeles, 3), dtype=np.uint8)


def _referencia_forgatas(kep: np.ndarray, szog: float, szin) -> np.ndarray:
    """A spec pontjai képpontonként, ciklussal (a kód vektoros — ez a
    független párja). `fistp` = páros felé kerekítés (Python `round`)."""
    sh, sw = kep.shape[:2]
    rad = math.radians(szog)
    c, s = math.cos(rad), math.sin(rad)
    dw = int(math.floor(sw * abs(c) + sh * abs(s)))
    dh = int(math.floor(sw * abs(s) + sh * abs(c)))
    # cél → forrás: T(sW/2, sH/2) · R⁻¹ · T(−dW/2, −dH/2), óramutató szerint
    m0, m1, m2 = c, s, sw / 2 - c * dw / 2 - s * dh / 2
    m3, m4, m5 = -s, c, sh / 2 + s * dw / 2 - c * dh / 2
    ki = np.empty((dh, dw, 3), dtype=np.int64)
    ki[:] = szin
    lepes_u, lepes_v = round(m0 * 65536), round(m3 * 65536)
    src = kep.astype(np.int64)
    for y in range(dh):
        u0 = round((m0 * 0.5 + m1 * (y + 0.5) + m2) * 65536) - 32767
        v0 = round((m3 * 0.5 + m4 * (y + 0.5) + m5) * 65536) - 32767
        for x in range(dw):
            uu, vv = u0 + x * lepes_u, v0 + x * lepes_v
            ix, iy = uu >> 16, vv >> 16
            if not (-1 <= ix <= sw - 1 and -1 <= iy <= sh - 1):
                continue
            fx, fy = (uu >> 8) & 0xFF, (vv >> 8) & 0xFF
            x0, x1 = max(ix, 0), min(ix + 1, sw - 1)
            y0, y1 = max(iy, 0), min(iy + 1, sh - 1)
            fent = src[y0, x0] + (((src[y0, x1] - src[y0, x0]) * fx) >> 8)
            lent = src[y1, x0] + (((src[y1, x1] - src[y1, x0]) * fx) >> 8)
            ki[y, x] = fent + (((lent - fent) * fy) >> 8)
    return ki.astype(np.uint8)


class TestKeppontkozepesForgatas:
    def test_180_fok_pontos_tukrozes(self):
        """A forrás közepe a cél közepére esik: 180°-nál minden képpont
        pontosan a tükörpárjára kerül — fél képpontos csúszás nélkül."""
        kep = _veletlen(7, 10)
        ki = rotate_with_pad(kep, 180.0, (1, 2, 3))
        np.testing.assert_array_equal(ki, kep[::-1, ::-1])

    def test_90_fok_paratlan_kulonbseggel_is_pontos(self):
        """`W − H` páratlan: az egész osztásos (`//2`) vászonra rakás itt
        fél képpontot tolt, a képpontközepes mátrix nem."""
        kep = _veletlen(5, 8)
        ki = rotate_with_pad(kep, 90.0, (1, 2, 3))
        np.testing.assert_array_equal(ki, np.rot90(kep, k=-1))

    def test_nulla_fok_azonossag(self):
        kep = _veletlen(6, 9)
        np.testing.assert_array_equal(rotate_with_pad(kep, 0.0, (1, 2, 3)), kep)

    def test_a_perem_nem_keveredik_a_vaszon_szinevel(self):
        """Egyszínű képnél a kimenetben CSAK a kép és a vászon színe
        fordul elő: a perem sávja a szélső képpontot ismétli, nem a
        kitöltő színnel mos össze."""
        kep = np.full((40, 60, 3), 90, dtype=np.uint8)
        ki = rotate_with_pad(kep, 5.0, (200, 200, 200))
        szinek = {tuple(int(v) for v in p) for p in ki.reshape(-1, 3)}
        assert szinek == {(90, 90, 90), (200, 200, 200)}

    @pytest.mark.parametrize("szog", [5.0, -10.0, 10.0, 33.0])
    def test_a_fixpontos_mintavevo_kepontra(self, szog):
        kep = _veletlen(13, 17, seed=11)
        vart = _referencia_forgatas(kep, szog, (7, 8, 9))
        np.testing.assert_array_equal(rotate_with_pad(kep, szog, (7, 8, 9)), vart)


def _regi_numpy_mintavevo(image, matrix, cel_w, cel_h, border_color):
    """A #3809-es, numpy-s `_fixpontos_bilinearis` VÁLTOZATLANUL — a #3846
    gyorsított (`cv2.remap` + `cv2.multiply`) alakjának referenciája."""
    m0, m1, m2, m3, m4, m5 = matrix
    src_h, src_w = image.shape[:2]
    sor = np.arange(cel_h, dtype=np.float64) + 0.5
    oszlop = np.arange(cel_w, dtype=np.int64)
    u0 = np.rint((m0 * 0.5 + m1 * sor + m2) * 65536).astype(np.int64) - 32767
    v0 = np.rint((m3 * 0.5 + m4 * sor + m5) * 65536).astype(np.int64) - 32767
    u = u0[:, None] + oszlop[None, :] * int(np.rint(m0 * 65536))
    v = v0[:, None] + oszlop[None, :] * int(np.rint(m3 * 65536))
    ix, iy = u >> 16, v >> 16
    ervenyes = (ix >= -1) & (ix <= src_w - 1) & (iy >= -1) & (iy <= src_h - 1)
    ix, iy = ix[ervenyes], iy[ervenyes]
    fx = ((u[ervenyes] >> 8) & 0xFF)[:, None]
    fy = ((v[ervenyes] >> 8) & 0xFF)[:, None]
    x0, x1 = np.clip(ix, 0, src_w - 1), np.clip(ix + 1, 0, src_w - 1)
    y0, y1 = np.clip(iy, 0, src_h - 1), np.clip(iy + 1, 0, src_h - 1)
    forras = image.astype(np.int32)
    fent = forras[y0, x0] + (((forras[y0, x1] - forras[y0, x0]) * fx) >> 8)
    lent = forras[y1, x0] + (((forras[y1, x1] - forras[y1, x0]) * fx) >> 8)
    cel = np.empty((cel_h, cel_w, image.shape[2]), dtype=image.dtype)
    cel[:] = np.array(border_color, dtype=image.dtype)
    cel[ervenyes] = (fent + (((lent - fent) * fy) >> 8)).astype(image.dtype)
    return cel


# rontás-kontroll (#3846, a gyors mintavevő): a `_lerp8` floor helyett
# kerekítéssel (`+ 128`) → 26 failed; a remap-ág x/y eltolása felcserélve →
# 29 failed; a numpy-s (32 767 fölötti) gyűjtő ág `x1`-e `ix + 1` helyett
# `ix` → 1 failed (a kényszerített ág próbája). Ellenőrizve lefuttatva.


class TestGyorsMintavevoBitreAzonos:
    """#3846: a közös mintavevő gyorsított alakja bitre ugyanazt adja, mint a
    #3809-es numpy-s — véletlen képen, kilógó vásznon, sok szögnél."""

    @pytest.mark.parametrize("szog", [0.0, 3.0, -7.5, 11.459, 33.0, 90.0, 180.0, -135.0])
    @pytest.mark.parametrize(("magas", "szeles"), [(37, 53), (120, 91)])
    def test_kiloge_vaszonnal(self, szog, magas, szeles):
        """A `rotate_with_pad` mátrixa: a vászon nagyobb, a sarkok kilógnak
        (a kitöltő szín és a perem egy képpontos sávja is szerepel)."""
        from picasapy.render.glimmer_frame_ops import _fixpontos_bilinearis

        kep = _veletlen(magas, szeles, seed=int(abs(szog) * 10) + magas)
        rad = math.radians(szog)
        c, s = math.cos(rad), math.sin(rad)
        cw = int(math.floor(szeles * abs(c) + magas * abs(s))) + 9
        ch = int(math.floor(szeles * abs(s) + magas * abs(c))) + 5
        m = (c, s, szeles / 2 - c * cw / 2 - s * ch / 2,
             -s, c, magas / 2 + s * cw / 2 - c * ch / 2)
        np.testing.assert_array_equal(
            _fixpontos_bilinearis(kep, m, cw, ch, (226, 1, 77)),
            _regi_numpy_mintavevo(kep, m, cw, ch, (226, 1, 77)),
        )

    @pytest.mark.parametrize("p", [1.0, -1.0, 0.37, -0.05])
    def test_a_kiegyenesites_matrixaval(self, p):
        from picasapy.render.glimmer_frame_ops import _fixpontos_bilinearis
        from picasapy.render.ops import tilt_matrix

        kep = _veletlen(64, 96, seed=5)
        m = tilt_matrix(96, 64, 0.2 * p)
        np.testing.assert_array_equal(
            _fixpontos_bilinearis(kep, m, 96, 64, (0, 0, 0)),
            _regi_numpy_mintavevo(kep, m, 96, 64, (0, 0, 0)),
        )

    def test_nagyitas_es_kicsinyites_skalaval(self):
        """Nem csak forgatás: skálázó és nyíró mátrix is bitre azonos."""
        from picasapy.render.glimmer_frame_ops import _fixpontos_bilinearis

        kep = _veletlen(50, 70, seed=9)
        for m in ((0.37, 0.11, 3.3, -0.08, 0.52, 7.9), (1.9, -0.4, -12.0, 0.3, 2.2, -20.5)):
            np.testing.assert_array_equal(
                _fixpontos_bilinearis(kep, m, 88, 61, (5, 6, 7)),
                _regi_numpy_mintavevo(kep, m, 88, 61, (5, 6, 7)),
            )

    def test_a_remap_korlatja_folott_a_numpy_gyujtes_ugyanaz(self, monkeypatch):
        """A `cv2.remap` csak 32 767 képpont alatt fut; a fölötti ág (numpy-s
        gyűjtés) is bitre azonos — itt a határt lecsökkentve kényszerítjük."""
        from picasapy.render import glimmer_frame_ops

        kep = _veletlen(40, 60, seed=21)
        m = (0.9, 0.2, 1.5, -0.2, 0.9, 9.0)
        gyors = glimmer_frame_ops._fixpontos_bilinearis(kep, m, 66, 47, (1, 2, 3))
        monkeypatch.setattr(glimmer_frame_ops, "_REMAP_HATAR", 0)
        numpys = glimmer_frame_ops._fixpontos_bilinearis(kep, m, 66, 47, (1, 2, 3))
        np.testing.assert_array_equal(numpys, gyors)
        np.testing.assert_array_equal(gyors, _regi_numpy_mintavevo(kep, m, 66, 47, (1, 2, 3)))


# ---------------------------------------------------------------------------
# FEJLESZTŐI GÉPEN futó golden-mérés a valódi Picasa-exporttal (684-
# merokeszlet), a `test_glimmer_autofix_2229.py` mintájára.
# ---------------------------------------------------------------------------

_KIT = Path("/mnt/nas/My Pictures/684-merokeszlet")

#: (címke, fájlnév, lánc, határ). A Polaroid határa a mért érték + 0,05,
#: legfeljebb 0,2 (#3809); a DropShadow-é a javítás előtti érték + 0,01 —
#: az nem romolhat.
#:
#: Mérve (`analyze_validation_kit.mean_de`, CIE76 átlag-ΔE):
#:
#: | eset | a #3809 előtt | a #3809 után |
#: |---|---:|---:|
#: | Polaroid alap (5°) | 0,694 | **0,118** |
#: | Polaroid max (10°) | 1,095 | **0,131** |
#: | Polaroid min (−10°) | 2,584 | **0,131** |
#: | DropShadow alap / max / min | 0,084 / 0,054 / 0,084 | változatlan |
#:
#: A jegy `cv2.INTER_LINEAR`-es mérése 0,149 / 0,155 / 0,154 volt; a natív
#: fixpontos mintavevő ennél is közelebb visz.
_TURES = 0.05
_PLAFON = 0.2
_GOLDEN_ESETEK = [
    ("Polaroid alap", "polaroid__alap.jpg", "Polaroid=1,5.000000,00e2e2e2;",
     min(0.118 + _TURES, _PLAFON)),
    ("Polaroid max", "polaroid__max.jpg", "Polaroid=1,10.000000,00e2e2e2;",
     min(0.131 + _TURES, _PLAFON)),
    ("Polaroid min", "polaroid__min.jpg", "Polaroid=1,-10.000000,00e2e2e2;",
     min(0.131 + _TURES, _PLAFON)),
    (
        "DropShadow alap",
        "dropshadow__alap.jpg",
        "DropShadow=1,4.000000,90.000000,10.000000,00000000,00ffffff,30.000000;",
        0.084 + 0.01,
    ),
    (
        "DropShadow max",
        "dropshadow__max.jpg",
        "DropShadow=1,30.000000,360.000000,100.000000,00000000,00ffffff,100.000000;",
        0.054 + 0.01,
    ),
    (
        "DropShadow min",
        "dropshadow__min.jpg",
        "DropShadow=1,0.000000,0.000000,0.000000,00000000,00ffffff,0.000000;",
        0.084 + 0.01,
    ),
]


def _golden_eszkozok():
    gyoker = Path(__file__).resolve().parents[2]
    utvonal = str(gyoker / "tools" / "golden")
    if utvonal not in sys.path:
        sys.path.insert(0, utvonal)
    from analyze_validation_kit import load, mean_de

    return load, mean_de


@pytest.mark.skipif(not _KIT.is_dir(), reason="a 684-merokeszlet NAS-os mérőkészlet nem elérhető")
@pytest.mark.parametrize(
    ("cimke", "nev", "lanc", "hatar"), _GOLDEN_ESETEK, ids=[e[0] for e in _GOLDEN_ESETEK]
)
def test_golden_a_684_merokeszlettel_a_hatarertek_alatt(cimke, nev, lanc, hatar):
    load, mean_de = _golden_eszkozok()
    from picasapy.ini.filters import parse_filters
    from picasapy.render.chain import apply_filters

    forras = load(_KIT / nev)
    export = load(_KIT / "export" / nev)
    kep = apply_filters(forras, parse_filters(lanc)).image
    assert kep.shape == export.shape
    de = mean_de(kep, export)
    assert de <= hatar, f"{cimke}: ΔE {de:.3f} > {hatar:.3f}"
