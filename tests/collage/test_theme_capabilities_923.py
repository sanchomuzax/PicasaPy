"""#923 — a téma képesség-maszkja dönti el, mely beállítások értelmesek.

A Picasában nem minden beállítás értelmes minden kollázs-típusnál, és ezt
nem témánkénti felületi kód dönti el, hanem **egy konstans bitmaszk**
(a téma-osztály 7. vtable-slotja). A panel (`0x00831750`) ebből mutatja,
rejti és tiltja a vezérlőit.

A mi `PicasaCollageSettings`-ünk korábban **bármit bármivel** engedett:
`theme="picturegrid", border="polaroid"` érvényes volt nálunk, holott az
eredeti felületen elő sem állítható — a Mozaiknál nincs keretválasztó.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.collage.picasa_render import PicasaCollageSettings
from picasapy.collage.themes import (
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    NOBORDER,
    PICTUREGRID,
    PICTUREPILE,
    POLAROID,
    REGULARGRID,
    THEME_CAPABILITIES,
    THEME_MASKS,
    capabilities_for,
)

#: A jegy táblája — a maszkoktól FÜGGETLENÜL leírva, hogy a származtatás
#: hibája kiderüljön. (keret, térköz, árnyék, kijelölés)
VART = {
    PICTUREPILE: (True, False, True, True),
    PICTUREGRID: (False, True, True, True),
    FRAMEGRID: (False, True, True, True),
    REGULARGRID: (False, True, True, True),
    CONTACTSHEET: (True, False, True, True),
    MULTIEXP: (False, False, False, False),
}


class TestKepessegTabla:
    @pytest.mark.parametrize("tema", sorted(VART))
    def test_a_negy_kepesseg_a_jegy_tablaja_szerint(self, tema):
        c = capabilities_for(tema)
        assert (c.borders, c.spacing, c.shadow, c.selection) == VART[tema]

    def test_mind_a_hat_temara_van_bejegyzes(self):
        assert set(THEME_CAPABILITIES) == set(VART)
        assert set(THEME_MASKS) == set(VART)

    def test_ismeretlen_tema_HIBAT_dob_nem_alapertelmezest(self):
        with pytest.raises(ValueError, match="Ismeretlen kollázs-téma"):
            capabilities_for("nincs_ilyen")

    def test_a_keret_es_a_terkoz_SOSEM_latszik_egyutt(self):
        """A panelen a keretsor (13, 122) és a térköz-csoport (19, 123)
        UGYANAZT a helyet foglalja — ez önmagában bizonyítja."""
        for tema, c in THEME_CAPABILITIES.items():
            assert not (c.borders and c.spacing), tema

    def test_az_arnyek_alapertelmezese_a_14_bit(self):
        """A kutatás 2026-08-18-i köre: árnyék alapból BE a Képkupacnál és
        az Indexképnél, KI a másik négynél."""
        bekapcsolva = {t for t, c in THEME_CAPABILITIES.items() if c.shadow_default}
        assert bekapcsolva == {PICTUREPILE, CONTACTSHEET}


class TestBeallitasSzures:
    def test_nem_tamogatott_keret_FIGYELMEN_KIVUL_marad(self):
        b = PicasaCollageSettings(theme=PICTUREGRID, border=POLAROID)
        assert b.effective_border == NOBORDER

    def test_tamogatott_keret_ervenyesul(self):
        b = PicasaCollageSettings(theme=PICTUREPILE, border=POLAROID)
        assert b.effective_border == POLAROID

    def test_nem_tamogatott_terkoz_nullara_esik(self):
        assert PicasaCollageSettings(theme=PICTUREPILE, spacing=0.7).effective_spacing == 0.0

    def test_tamogatott_terkoz_ervenyesul(self):
        assert PicasaCollageSettings(theme=PICTUREGRID, spacing=0.7).effective_spacing == 0.7

    def test_a_TAROLT_ertek_megmarad_round_trip_miatt(self):
        """A `.cxf` tartalmazhat sávon kívüli értéket; azt megőrizzük, csak
        nem rajzoljuk ki. A néma ÁTÍRÁS adatvesztés lenne."""
        b = PicasaCollageSettings(theme=PICTUREGRID, border=POLAROID, spacing=0.7)
        assert b.border == POLAROID and b.spacing == 0.7

    def test_a_multiexp_arnyeka_TILTOTT(self):
        assert PicasaCollageSettings(theme=MULTIEXP, shadow=True).effective_shadow is False

    def test_az_arnyek_alapbol_a_tema_szerint_all(self):
        assert PicasaCollageSettings(theme=PICTUREPILE).effective_shadow is True
        assert PicasaCollageSettings(theme=PICTUREGRID).effective_shadow is False

    def test_az_arnyek_kifejezetten_felulirhato_ahol_engedett(self):
        assert PicasaCollageSettings(theme=PICTUREGRID, shadow=True).effective_shadow is True
        assert PicasaCollageSettings(theme=PICTUREPILE, shadow=False).effective_shadow is False


class TestRendereles:
    """A renderelő az EFFEKTÍV értékeket használja, nem a tároltat."""

    @pytest.fixture
    def kepek(self, tmp_path):
        import cv2

        utak = []
        for index in range(3):
            kep = np.full((80, 100, 3), 40 + index * 60, dtype=np.uint8)
            ut = tmp_path / f"k{index}.png"
            cv2.imwrite(str(ut), kep)
            utak.append(ut)
        return utak

    def test_a_mozaik_kimenete_FUGGETLEN_a_kerettol(self, kepek):
        from picasapy.collage.picasa_render import make_picasa_collage

        alap = {"theme": PICTUREGRID, "width": 200, "height": 160, "seed": 3}
        nelkule = make_picasa_collage(kepek, PicasaCollageSettings(**alap)).image
        polaroiddal = make_picasa_collage(
            kepek, PicasaCollageSettings(**alap, border=POLAROID)
        ).image
        np.testing.assert_array_equal(nelkule, polaroiddal)

    def test_a_kepkupac_kimenete_FUGG_a_kerettol(self, kepek):
        from picasapy.collage.picasa_render import make_picasa_collage

        alap = {"theme": PICTUREPILE, "width": 200, "height": 160, "seed": 3}
        nelkule = make_picasa_collage(kepek, PicasaCollageSettings(**alap)).image
        polaroiddal = make_picasa_collage(
            kepek, PicasaCollageSettings(**alap, border=POLAROID)
        ).image
        assert not np.array_equal(nelkule, polaroiddal)
