"""#3878 — a Comicize négy lánclépése a natív viselkedés szerint.

A spec: `docs/specs/filters-decoded.md`, „⛳ A Comicize maradéka: négy
lánclépés natív viselkedése” (#3876). Mind a négy lépés a binárisból jön,
illesztés nélkül:

1. az elő-elmosás a natív `BlurImageOperation` (`nativ_blur`), nem Gauss;
2. a `Pixelate` az eltolást eldobja, `⌈W/pw⌉ × ⌈H/ph⌉` blokkra dobozzal
   kicsinyít, és a rácsot KÖZÉPRE igazítva nagyít vissza;
3. a `TiledImageMask` rácsának origója `int((W − ⌈W/t⌉·t)/2) + int(offset)`,
   és a távolság a képpont INDEXÉBŐL mér;
4. a záró `multiply` és `BlendAlpha` egész aritmetikájú.

A golden-mérés (ΔE a 684-es készleten) a helyi kör dolga; ez a fájl a
lépések képleteit őrzi.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.effects_artistic import (
    apply_comicize,
    pixelate_centered,
)
from picasapy.render.glimmer_ops import alpha_blend, resize_image
from picasapy.render.halftone import (
    DOT_SCALE,
    dot_size_for,
    native_dot_mask,
    tiled_mask_origin,
)
from picasapy.render.nativ_blur import blur_image_operation


def _veletlen(magas: int, szeles: int, mag: int = 3878) -> np.ndarray:
    return np.random.default_rng(mag).integers(0, 256, (magas, szeles, 3), dtype=np.uint8)


class TestAMaszkOrigoja:
    """3. lépés — középre igazított rács, csonkolt eltolás."""

    def test_960x640_t15_az_elso_maszk_origoja(self):
        assert dot_size_for(960) == 15
        assert tiled_mask_origin(960, 640, 15) == (0, -2)

    def test_960x640_t15_a_masodik_maszk_origoja(self):
        """`offset = 7,5` → 7-re csonkol: `(0 + 7, −2 + 7)`."""
        assert tiled_mask_origin(960, 640, 15, 7.5, 7.5) == (7, 5)

    def test_a_kilogas_felezese_nulla_fele_csonkol(self):
        """`W − rács = −5` → `−2` (nem `−3`, mint a lefelé kerekítésnél)."""
        assert tiled_mask_origin(640, 640, 15)[0] == -2
        assert tiled_mask_origin(655, 655, 15) == (-2, -2)  # ⌈655/15⌉·15 = 660

    def test_a_negativ_eltolas_is_nulla_fele_csonkol(self):
        assert tiled_mask_origin(960, 960, 15, -7.5, 0.9) == (-7, 0)

    def test_a_maszk_a_kepontindexbol_mer(self):
        """A csempe közepe `origó + t/2`, a távolság az indexből (nincs +0,5)."""
        magas, szeles, t = 640, 960, 15
        ox, oy = tiled_mask_origin(szeles, magas, t)
        maszk = native_dot_mask(magas, szeles, t, ox + 0.5, oy + 0.5)
        ys, xs = np.mgrid[0:magas, 0:szeles].astype(np.float64)
        lx = np.mod(xs - ox, t) - t / 2.0
        ly = np.mod(ys - oy, t) - t / 2.0
        rampa = np.hypot(lx, ly) / (t / 2.0) / DOT_SCALE
        # a pont közepe a 7,5-ös koordinátán: a 7. és a 8. index EGYFORMÁN messze
        assert maszk[0 + 5, 7] == maszk[0 + 5, 8]
        # a (−2)-es origó miatt az első TELJES csempe a 13. sorban kezdődik
        assert maszk[13 + 7, 7] == maszk[13 + 8, 8]
        kozel = rampa < 0.95
        assert np.all(maszk[kozel] > 0)
        assert np.all(maszk[rampa >= 1.0] == 0)


class TestAPixelateKozepreIgazitott:
    """2. lépés — `⌈W/pw⌉ × ⌈H/ph⌉` blokk, doboz, középre igazított rács."""

    def test_960x640_nH_43_kozepre_igazitva(self):
        kep = _veletlen(640, 960)
        ki = pixelate_centered(kep, 15, 15)
        # a sorblokkok határa: ahol a sor változik
        valtas = np.flatnonzero(np.any(ki[1:, :, :] != ki[:-1, :, :], axis=(1, 2))) + 1
        hatarok = np.concatenate([[0], valtas, [640]])
        hosszak = np.diff(hatarok)
        assert len(hosszak) == 43
        # 2,5 sor lóg ki fent és lent: a képpont KÖZEPE vetül vissza, ezért
        # fent 12, lent 13 sor marad, a belső blokkok 15 sorosak
        assert hosszak[0] == 12
        assert hosszak[-1] == 13
        assert np.all(hosszak[1:-1] == 15)

    def test_960x640_vizszintesen_64_blokk_kilogas_nelkul(self):
        ki = pixelate_centered(_veletlen(640, 960), 15, 15)
        valtas = np.flatnonzero(np.any(ki[:, 1:, :] != ki[:, :-1, :], axis=(0, 2))) + 1
        assert list(valtas) == list(range(15, 960, 15))

    def test_a_blokk_erteke_a_doboz_kicsinyites(self):
        kep = _veletlen(640, 960)
        kicsi = resize_image(kep, 64, 43, smoothing=True)
        ki = pixelate_centered(kep, 15, 15)
        np.testing.assert_array_equal(ki[0], kicsi[0].repeat(15, axis=0))
        np.testing.assert_array_equal(ki[12], kicsi[1].repeat(15, axis=0))
        np.testing.assert_array_equal(ki[639], kicsi[42].repeat(15, axis=0))

    def test_alakot_es_tipust_tart(self):
        kep = _veletlen(97, 213)
        ki = pixelate_centered(kep, 4, 4)
        assert ki.shape == kep.shape and ki.dtype == np.uint8


class TestAzEloElmosasNativ:
    """1. lépés — `min(kép, BlurImageOperation(xb, xb, 3))`, uint8."""

    @pytest.mark.parametrize("blur_xy", [0.0, 20.0, 100.0])
    def test_alfa_nullanal_a_darkened_a_kimenet(self, blur_xy):
        """`DotFade = 100` → `BlendAlpha = 0`: a kimenet maga a `darkened`."""
        kep = _veletlen(60, 100)
        xb = 1.0 + 20.0 * blur_xy / 100.0
        vart = np.minimum(kep, blur_image_operation(kep, xb, xb, 3))
        np.testing.assert_array_equal(apply_comicize(kep, blur_xy, 50.0, 100.0), vart)


class TestAZaroKeveresEgesz:
    """4. lépés — SIMD-párok, odd widthnél a spec sorvégi skalárágával."""

    def test_alfa_nulla_az_also_elem(self):
        b = _veletlen(4, 5)
        t = _veletlen(4, 5, 1)
        np.testing.assert_array_equal(alpha_blend(b, t, 0.0).astype(np.uint8), b)

    def test_alfa_egy_a_felso_elem(self):
        b = _veletlen(4, 5)
        t = _veletlen(4, 5, 1)
        np.testing.assert_array_equal(alpha_blend(b, t, 1.0).astype(np.uint8), t)

    @pytest.mark.parametrize("alfa,w", [(0.5, 127), (0.25, 63), (0.3, 75)])
    def test_a_suly_csonkolt_es_eggyel_kisebb(self, alfa, w):
        # Páros szélesség: mindkét pixelre a SIMD-pár képlete érvényes.
        b = np.tile(np.array([[[255, 200, 0]]], dtype=np.uint8), (1, 2, 1))
        t = np.tile(np.array([[[255, 100, 255]]], dtype=np.uint8), (1, 2, 1))
        vart = (b.astype(np.int64) * (255 - w) + t.astype(np.int64) * w) >> 8
        np.testing.assert_array_equal(alpha_blend(b, t, alfa).astype(np.uint8), vart.astype(np.uint8))

    def test_ket_255_os_bemenetbol_254(self):
        """A SIMD-pár súlyainak összege 255, osztója 256 — egy szinttel sötétebb."""
        f = np.full((1, 2, 3), 255, dtype=np.uint8)
        assert alpha_blend(f, f, 0.5)[0, 0, 0] == 254

    def test_feher_kepen_a_kimenet_egy_szinttel_sotetebb(self):
        """Sík fehér: a raszter fehér, `⌊255·255/255⌋ = 255`, a keverés 254-et ad
        (a kép közepén, ahol a belső ragyogás már nem sötétít)."""
        feher = np.full((200, 700, 3), 255, dtype=np.uint8)
        ki = apply_comicize(feher, 20.0, 50.0, 50.0)
        assert ki[100, 350, 0] == 254


class TestAMestergorbeKerekitese:
    """A mestergörbe bájtra `trunc(x + 0,5)` (nem `rint`: a ,5 mindig felfelé)."""

    @pytest.mark.parametrize("bemenet,vart", [(10, 11), (11, 12), (12, 13)])
    def test_a_pontosan_fel_ertek_felfele_kerekul(self, monkeypatch, bemenet, vart):
        import picasapy.render.effects_artistic as ea

        lut = np.arange(256, dtype=np.float64)
        lut[10:13] = (10.5, 11.5, 12.5)  # `rint` 10, 12, 12 lenne
        monkeypatch.setattr(ea, "comicize_master_curve", lambda _dc: lut)
        monkeypatch.setattr(ea, "inner_glow", lambda img, *a, **kw: img)
        latott = {}
        eredeti = ea.pixelate_centered

        def figyel(curved, *a, **kw):
            latott["curved"] = curved
            return eredeti(curved, *a, **kw)

        monkeypatch.setattr(ea, "pixelate_centered", figyel)
        ea.apply_comicize(np.full((8, 8, 3), bemenet, dtype=np.uint8))
        assert np.all(latott["curved"] == vart)
