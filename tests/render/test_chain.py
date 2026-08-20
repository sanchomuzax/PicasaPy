"""A `picasapy.render.chain` lánc-alkalmazó tesztjei."""

from __future__ import annotations

import math

import numpy as np
import pytest

from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import Rect64
from picasapy.ini.retouch import RetouchPatch, build_retouch_op, build_retouch_patches_op
from picasapy.render.chain import apply_filters, tilt_cover_scale
from picasapy.render.color import apply_bw
from picasapy.render.ops import apply_autocolor, apply_autolight, apply_crop
from picasapy.render.retouch import apply_retouch, apply_retouch_patches
from picasapy.render.tinting import apply_tint
from picasapy.render.tone import apply_fill, apply_finetune2


def _gradient_image(width: int = 20, height: int = 10) -> np.ndarray:
    row = np.linspace(80, 180, width, dtype=np.uint8)
    image = np.tile(row, (height, 1))
    return np.stack([image, image, image], axis=-1).astype(np.uint8)


class TestTiltCoverScale:
    def test_nulla_szognel_egy(self) -> None:
        assert tilt_cover_scale(100, 50, 0.0) == pytest.approx(1.0)

    def test_pozitiv_szognel_nagyobb_mint_egy(self) -> None:
        assert tilt_cover_scale(100, 50, math.radians(10)) > 1.0

    def test_negativ_szog_ugyanaz_mint_pozitiv(self) -> None:
        pos = tilt_cover_scale(100, 60, math.radians(15))
        neg = tilt_cover_scale(100, 60, math.radians(-15))
        assert pos == pytest.approx(neg)


class TestApplyFilters:
    def test_tamogatott_crop64_alkalmazasa(self) -> None:
        image = _gradient_image()
        ops = (FilterOp("crop64", ("1", "20001000c000e000")),)
        result, skipped = apply_filters(image, ops)
        expected = apply_crop(
            image,
            __import__(
                "picasapy.ini.rect64", fromlist=["decode_rect64"]
            ).decode_rect64("20001000c000e000"),
        )
        assert result.shape == expected.shape
        assert skipped == ()

    def test_tobb_crop64_nem_kaszkadol(self) -> None:
        # #130: valódi Picasa-láncban több crop64 lehet (szerkesztési
        # történet), de a tényleges vágás EGY (a crop= kulcs = az effektív,
        # utolsó crop64), az EREDETI képméretre. A régi kód mindet sorban,
        # az aktuális köztes képre alkalmazta → kaszkád-vágás (rossz kivágás).
        from picasapy.ini.rect64 import decode_rect64

        image = _gradient_image(width=40, height=40)
        first = "2000200060006000"   # egy köztes vágás a történetben
        last = "10001000e000e000"    # az effektív (végső) vágás
        ops = (
            FilterOp("crop64", ("1", first)),
            FilterOp("crop64", ("1", last)),
        )
        result, skipped = apply_filters(image, ops)

        # helyes: az EREDETI képre alkalmazott EGYETLEN (utolsó) vágás
        expected = apply_crop(image, decode_rect64(last))
        np.testing.assert_array_equal(result, expected)

        # és NEM a kaszkád (az elsőre vágott képre alkalmazott második)
        cascade = apply_crop(apply_crop(image, decode_rect64(first)),
                             decode_rect64(last))
        assert result.shape != cascade.shape
        assert skipped == ()

    def test_crop_az_effektusok_utan_a_teljes_kepre(self) -> None:
        # #130: a crop= a filterek UTÁN, a teljes képre alkalmazódik (Picasa-
        # szemantika: a crop= külön kulcs). A fill a teljes képen fut, majd a
        # végén vágunk — nem a vágott kis képen futna a fill.
        from picasapy.ini.rect64 import decode_rect64

        image = _gradient_image(width=40, height=20)
        rect = "20002000c000c000"
        ops = (FilterOp("fill", ("1", "0.5")), FilterOp("crop64", ("1", rect)))
        result, skipped = apply_filters(image, ops)
        expected = apply_crop(apply_fill(image, 0.5), decode_rect64(rect))
        np.testing.assert_array_equal(result, expected)
        assert skipped == ()

    def test_nem_tamogatott_szurot_nemán_kihagyja(self) -> None:
        # lomoish: még nem dekódolt 3.9-es effekt (#190) → nincs handlere,
        # a lánc kihagyja (a grain2 a #20 óta rögzített maggal renderelt)
        image = _gradient_image()
        ops = (FilterOp("lomoish", ("1",)),)
        result, skipped = apply_filters(image, ops)
        np.testing.assert_array_equal(result, image)
        assert skipped == ("lomoish",)

    def test_vegyes_lanc_sorrend_es_kihagyottak(self) -> None:
        image = _gradient_image()
        ops = (
            FilterOp("autolight", ("1",)),
            FilterOp("lomoish", ("1",)),
            FilterOp("autocolor", ("1",)),
        )
        result, skipped = apply_filters(image, ops)
        expected = apply_autocolor(apply_autolight(image))
        np.testing.assert_array_equal(result, expected)
        assert skipped == ("lomoish",)

    def test_finetune2_alkalmazasa(self) -> None:
        image = _gradient_image()
        ops = (FilterOp("finetune2", ("1", "0.3", "0.1", "0.2", "00000000", "0.0")),)
        result, skipped = apply_filters(image, ops)
        expected = apply_finetune2(
            image, fill=0.3, highlights=0.1, shadows=0.2, neutral=None, temperature=0.0
        )
        np.testing.assert_array_equal(result, expected)
        assert skipped == ()

    def test_fill_alkalmazasa(self) -> None:
        image = _gradient_image()
        ops = (FilterOp("fill", ("1", "0.5")),)
        result, skipped = apply_filters(image, ops)
        np.testing.assert_array_equal(result, apply_fill(image, 0.5))
        assert skipped == ()

    def test_bw_alkalmazasa(self) -> None:
        image = np.full((4, 4, 3), (100, 150, 200), dtype=np.uint8)
        result, skipped = apply_filters(image, (FilterOp("bw", ("1",)),))
        assert skipped == ()
        np.testing.assert_array_equal(result[..., 0], result[..., 1])
        np.testing.assert_array_equal(result[..., 1], result[..., 2])

    def test_sat_alkalmazasa(self) -> None:
        image = np.full((4, 4, 3), (200, 100, 100), dtype=np.uint8)
        result, skipped = apply_filters(image, (FilterOp("sat", ("1", "-1.0")),))
        assert skipped == ()
        np.testing.assert_array_equal(result[..., 0], result[..., 1])

    def test_unsharp_v1_egyenerteku_unsharp2_0_6(self) -> None:
        # mérve: unsharp=1 kimenete bitre azonos az unsharp2=1,0.600000-val
        image = _gradient_image()
        v1, skipped_v1 = apply_filters(image, (FilterOp("unsharp", ("1",)),))
        v2, skipped_v2 = apply_filters(
            image, (FilterOp("unsharp2", ("1", "0.600000")),)
        )
        np.testing.assert_array_equal(v1, v2)
        assert skipped_v1 == skipped_v2 == ()

    def test_enhance_alkalmazasa(self) -> None:
        image = _gradient_image()
        ops = (FilterOp("enhance", ("1",)),)
        result, skipped = apply_filters(image, ops)
        assert result.shape == image.shape
        assert skipped == ()

    def test_ures_lanc_valtozatlan_kepet_ad(self) -> None:
        image = _gradient_image()
        result, skipped = apply_filters(image, ())
        np.testing.assert_array_equal(result, image)
        assert skipped == ()

    def test_tilt_azonossag_nulla_szognel(self) -> None:
        image = _gradient_image()
        ops = (FilterOp("tilt", ("1", "0.0")),)
        result, skipped = apply_filters(image, ops)
        assert result.shape == image.shape
        assert skipped == ()

    def test_tilt_picasa_nulla_skalaval(self) -> None:
        """#73: az éles Picasa `tilt=1,<szög>,0.000000` alakot ír — a 0 skála
        nem hiba, hanem „számold ki a kitöltő skálát" jelentésű."""
        image = _gradient_image()
        ops = (FilterOp("tilt", ("1", "-0.153061", "0.000000")),)
        result, skipped = apply_filters(image, ops)
        assert result.shape == image.shape
        assert skipped == ()
        # ténylegesen forgatott (nem a bemenet másolata)
        assert not np.array_equal(result, image)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _gradient_image()
        original = image.copy()
        ops = (FilterOp("autolight", ("1",)),)
        apply_filters(image, ops)
        np.testing.assert_array_equal(image, original)

    def test_grain2_alkalmazasa(self) -> None:
        image = _gradient_image()
        ops = (FilterOp("grain2", ("1",)),)
        result, skipped = apply_filters(image, ops)
        assert result.shape == image.shape
        assert skipped == ()


class TestApplyFiltersHibatoleranciaja:
    """#301: az ismert nevű, de hibás/hiányos paraméterű bejegyzés a lánc
    TÖBBI TAGJÁT nem viszi magával — csak ő maga marad ki, kivétel nem
    szökik ki (a hívóknál korábban külön-külön kimásolt védelem helyett)."""

    def test_hianyos_tilt_mellett_a_tobbi_lefut(self) -> None:
        image = _gradient_image()
        ops = (FilterOp("tilt", ("1",)), FilterOp("autolight", ("1",)))
        result, skipped = apply_filters(image, ops)
        np.testing.assert_array_equal(result, apply_autolight(image))
        assert skipped == ("tilt",)

    def test_ervenytelen_crop64_mellett_a_tobbi_lefut(self) -> None:
        image = _gradient_image()
        ops = (FilterOp("fill", ("1", "0.5")), FilterOp("crop64", ("1", "zzz")))
        result, skipped = apply_filters(image, ops)
        # a crop64 érvénytelen hexje miatt a vágás elmarad, de a fill lefut
        np.testing.assert_array_equal(result, apply_fill(image, 0.5))
        assert skipped == ("crop64",)

    def test_nem_numerikus_sat_mellett_a_tobbi_lefut(self) -> None:
        image = np.full((4, 4, 3), (100, 150, 200), dtype=np.uint8)
        ops = (FilterOp("sat", ("1", "abc")), FilterOp("bw", ("1",)))
        result, skipped = apply_filters(image, ops)
        np.testing.assert_array_equal(result, apply_bw(image))
        assert skipped == ("sat",)

    def test_tobb_hibas_bejegyzes_mind_a_skipped_listaba_kerul(self) -> None:
        image = _gradient_image()
        ops = (
            FilterOp("tilt", ("1",)),
            FilterOp("lomoish", ("1",)),  # ismeretlen név
            FilterOp("sat", ("1", "abc")),
            FilterOp("autolight", ("1",)),
        )
        result, skipped = apply_filters(image, ops)
        np.testing.assert_array_equal(result, apply_autolight(image))
        assert skipped == ("tilt", "lomoish", "sat")


class TestApplyFiltersEffects:
    """Az effekt-szűrők (#149) regisztrációja a láncban — élesben mért
    paraméter-alakokkal (golden-kit ini-sorok)."""

    def test_vignette_alkalmazasa(self) -> None:
        # Vignette: nagybetűs azonosító, éles alak — a filterdesc.xml EGZAKT
        # csővezetéke (#381): GlowImageOperation(innerglow), ld. glimmer_tone.
        from picasapy.render.glimmer_tone import apply_vignette

        image = _gradient_image()
        ops = (FilterOp("Vignette", ("1", "35.000000", "1.400000", "0.000000", "00000000")),)
        result, skipped = apply_filters(image, ops)
        np.testing.assert_array_equal(result, apply_vignette(image))
        assert skipped == ()

    def test_glow_v1_alkalmazasa(self) -> None:
        image = _gradient_image()
        ops = (FilterOp("glow", ("1", "0.432749", "2.469705")),)
        result, skipped = apply_filters(image, ops)
        assert skipped == ()
        assert not np.array_equal(result, image)

    def test_glow2_alkalmazasa(self) -> None:
        image = _gradient_image()
        ops = (FilterOp("glow2", ("1", "0.650000", "3.000000")),)
        result, skipped = apply_filters(image, ops)
        assert skipped == ()
        assert not np.array_equal(result, image)

    def test_tint_alkalmazasa(self) -> None:
        # Éles alak: tint=1,79.842102,ffff (rövid, vezető nullák nélküli
        # szín). Ez a lánc bekötését méri; a képletet a tinting céltesztjei.
        image = np.full((4, 4, 3), 128, dtype=np.uint8)
        ops = (FilterOp("tint", ("1", "79.842102", "ffff")),)
        result, skipped = apply_filters(image, ops)
        assert skipped == ()
        np.testing.assert_array_equal(
            result,
            apply_tint(image, preserve=79.842102, color=(0x00, 0xFF, 0xFF)),
        )

    def test_ansel_alkalmazasa(self) -> None:
        image = np.full((4, 4, 3), (100, 150, 200), dtype=np.uint8)
        ops = (FilterOp("ansel", ("1", "ffffffff")),)
        result, skipped = apply_filters(image, ops)
        assert skipped == ()
        assert result[0, 0, 0] == result[0, 0, 1] == result[0, 0, 2]

    def test_radblur_alkalmazasa(self) -> None:
        # Éles (golden-kit) alak. A size=0, amount=0 eset NEM no-op: a
        # `golden-kit/09-effects` valódi Picasa-exportja szerint a kép
        # pereme ilyenkor is elmosódik (#668) — a korong közepe marad éles.
        image = _gradient_image()
        ops = (FilterOp("radblur", ("1", "0.5", "0.5", "0.000000", "0.000000")),)
        result, skipped = apply_filters(image, ops)
        assert skipped == ()
        center = (image.shape[0] // 2, image.shape[1] // 2)
        assert np.all(np.abs(result[center].astype(int) - image[center]) <= 1)
        assert not np.array_equal(result, image)

    def test_radsat_alkalmazasa(self) -> None:
        image = np.full((21, 21, 3), (200, 80, 80), dtype=np.uint8)
        ops = (FilterOp("radsat", ("1", "0.5", "0.5", "0.2", "1.0")),)
        result, skipped = apply_filters(image, ops)
        assert skipped == ()
        corner = result[0, 0]
        assert int(corner[0]) == int(corner[1]) == int(corner[2])

    def test_dir_tint_alkalmazasa(self) -> None:
        image = _gradient_image()
        ops = (
            FilterOp(
                "dir_tint",
                ("1", "0.432422", "0.554167", "0.250000", "0.250000", "ffffffff"),
            ),
        )
        result, skipped = apply_filters(image, ops)
        assert skipped == ()
        assert result.shape == image.shape


class TestApplyFiltersRetouch:
    """`retouch` bejegyzés a láncban (#148) — PicasaPy-saját régió-
    kiterjesztés, ld. `picasapy.ini.retouch` docsztring."""

    def test_puszta_retouch_no_op(self) -> None:
        """Valódi Picasa-eredetű `retouch=1;` régió nélkül — nem változtat."""
        image = _gradient_image()
        ops = (FilterOp("retouch", ("1",)),)
        result, skipped = apply_filters(image, ops)
        np.testing.assert_array_equal(result, image)
        assert skipped == ()

    def test_regioval_ugyanaz_mint_kozvetlenul_hivva(self) -> None:
        image = _gradient_image()
        region = Rect64(0.2, 0.1, 0.6, 0.8)
        op = build_retouch_op((region,))
        result, skipped = apply_filters(image, (op,))
        np.testing.assert_array_equal(result, apply_retouch(image, (region,)))
        assert skipped == ()

    def test_ervenytelen_regio_kimarad_a_tobbi_lefut(self) -> None:
        image = _gradient_image()
        ops = (
            FilterOp("retouch", ("1", "nemhex")),
            FilterOp("autolight", ("1",)),
        )
        result, skipped = apply_filters(image, ops)
        np.testing.assert_array_equal(result, apply_autolight(image))
        assert skipped == ("retouch",)

    def test_folttal_ugyanaz_mint_kozvetlenul_hivva(self) -> None:
        """#445: `retouch=2,<patch>...;` — a v2 (folt-alapú, irányított
        klónozás) kiterjesztés a láncon keresztül is."""
        image = _gradient_image()
        # #445: a rádiuszt/koordinátákat úgy választjuk, hogy a fixpontos
        # (encode_patch/decode_patch) kerekítés kimenete biztosan
        # megegyezzen a lánc VISSZAOLVASOTT (kvantált) foltjával — egy
        # pixelhatáron (pl. radius*height == x.5) a kvantálási zaj
        # Python `round()`-jának bankár-kerekítése eltérő pixelt adhat.
        patch = RetouchPatch(target_x=0.65, target_y=0.5, source_x=0.15, source_y=0.5, radius=0.12)
        op = build_retouch_patches_op((patch,))
        result, skipped = apply_filters(image, (op,))
        np.testing.assert_array_equal(result, apply_retouch_patches(image, (patch,)))
        assert skipped == ()

    def test_ervenytelen_patch_kimarad_a_tobbi_lefut(self) -> None:
        image = _gradient_image()
        ops = (
            FilterOp("retouch", ("2", "nemhex")),
            FilterOp("autolight", ("1",)),
        )
        result, skipped = apply_filters(image, ops)
        np.testing.assert_array_equal(result, apply_autolight(image))
        assert skipped == ("retouch",)
