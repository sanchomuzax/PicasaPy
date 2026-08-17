"""#431 — a Picasa-hű kollázs-rajzoló: mind a hat téma és a három keret.

A #431 magja (214 teszt) elkészült, **de senki nem hívta**: a felület a
#29-es, saját tervezésű négy elrendezésen maradt. Ezek az őrök azt
rögzítik, hogy a mag ténylegesen FUT, és hogy mind a hat téma más
eredményt ad — enélkül egy elgépelt téma-kulcs némán ugyanazt rajzolná.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from picasapy.collage.picasa_render import PicasaCollageSettings, make_picasa_collage
from picasapy.collage.themes import (
    FRAMEGRID,
    BORDER_THEMES,
    COLLAGE_THEMES,
    CONTACTSHEET,
    MULTIEXP,
    NOBORDER,
    PICTUREGRID,
    PICTUREPILE,
    POLAROID,
    WHITEBORDER,
)


@pytest.fixture
def kepek(tmp_path):
    """Négy jól megkülönböztethető, eltérő oldalarányú kép."""
    szinek = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255)]
    meretek = [(120, 160), (160, 120), (100, 100), (90, 200)]
    utak = []
    for index, (szin, (magassag, szelesseg)) in enumerate(zip(szinek, meretek, strict=True)):
        kep = np.empty((magassag, szelesseg, 3), dtype=np.uint8)
        kep[:, :] = szin
        # apró rajzolat, hogy a kép ne legyen teljesen homogén
        cv2.rectangle(kep, (5, 5), (szelesseg - 6, magassag - 6), (0, 0, 0), 2)
        ut = tmp_path / f"kep{index}.png"
        cv2.imwrite(str(ut), kep)
        utak.append(ut)
    return utak


def _beallitas(**kwargs) -> PicasaCollageSettings:
    alap = {"width": 320, "height": 240, "background": (255, 255, 255)}
    return PicasaCollageSettings(**{**alap, **kwargs})


class TestMindAHatTema:
    @pytest.mark.parametrize("tema", COLLAGE_THEMES)
    def test_lefut_es_rajzol_valamit(self, kepek, tema):
        jelentes = make_picasa_collage(kepek, _beallitas(theme=tema))
        assert jelentes.image.shape == (240, 320, 3)
        assert jelentes.image.dtype == np.uint8
        assert len(jelentes.used) == 4
        # nem maradhat üres, háttérszínű lap
        assert not np.all(jelentes.image == 255), f"a(z) {tema} nem rajzolt semmit"

    def test_az_ot_ONALLO_tema_ot_kulonbozo_kepet_ad(self, kepek):
        """Ez a döntő őr: ha a bekötés elgépel egy kulcsot, két téma
        ugyanazt adná — és ezt semmi más nem venné észre.

        A `framegrid` szándékosan kimarad: rögzített központi kép nélkül az
        EREDETI IS az alap pakolóra esik vissza (spec 1.9.14), tehát ott az
        azonosság a HELYES viselkedés — ld. a lenti két őrt.
        """
        onallo = tuple(tema for tema in COLLAGE_THEMES if tema != FRAMEGRID)
        kimenetek = {
            tema: make_picasa_collage(kepek, _beallitas(theme=tema, seed=7)).image.tobytes()
            for tema in onallo
        }
        assert len(set(kimenetek.values())) == len(onallo), (
            "két téma ugyanazt a képet adta: " + str(list(kimenetek))
        )

    def test_framegrid_rogzitett_kep_NELKUL_a_mozaikkal_azonos(self, kepek):
        """Spec 1.9.14: a `CLocationTree` nem helyettesíti, hanem kiegészíti
        az alap pakolót — rögzített kép híján visszaesik rá."""
        mozaik = make_picasa_collage(kepek, _beallitas(theme=PICTUREGRID, seed=7)).image
        kockak = make_picasa_collage(kepek, _beallitas(theme=FRAMEGRID, seed=7)).image
        np.testing.assert_array_equal(mozaik, kockak)

    def test_framegrid_rogzitett_keppel_MAR_elter(self, kepek):
        """A „Beállítás képkockaközéppontként" gomb hatása."""
        alap = make_picasa_collage(kepek, _beallitas(theme=FRAMEGRID, seed=7)).image
        rogzitve = make_picasa_collage(
            kepek, _beallitas(theme=FRAMEGRID, seed=7, frame_center=2)
        ).image
        assert not np.array_equal(alap, rogzitve)


class TestKeretek:
    """#923: a keretválasztó CSAK a Képkupacnál és az Indexképnél él (a
    képesség-maszk 9. bitje) — a Mozaiknál az eredetiben elő sem
    állítható. Ezek a tesztek ezért KÉPKUPACON futnak; korábban Mozaikon
    futottak, ami a maszk ismerete előtti (téves) feltevés volt."""

    @pytest.mark.parametrize("keret", BORDER_THEMES)
    def test_mindharom_keret_lefut(self, kepek, keret):
        jelentes = make_picasa_collage(kepek, _beallitas(theme=PICTUREPILE, border=keret))
        assert jelentes.image.shape == (240, 320, 3)

    def test_a_harom_keret_KULONBOZO_kepet_ad(self, kepek):
        kimenetek = {
            keret: make_picasa_collage(
                kepek, _beallitas(theme=PICTUREPILE, border=keret, seed=3)
            ).image.tobytes()
            for keret in (NOBORDER, WHITEBORDER, POLAROID)
        }
        assert len(set(kimenetek.values())) == 3


class TestIsmetelhetoseg:
    def test_azonos_mag_azonos_kollazs(self, kepek):
        """A Képkupac szórása véletlen — de rögzített maggal ismételhető."""
        elso = make_picasa_collage(kepek, _beallitas(theme=PICTUREPILE, seed=42)).image
        masodik = make_picasa_collage(kepek, _beallitas(theme=PICTUREPILE, seed=42)).image
        np.testing.assert_array_equal(elso, masodik)

    def test_mas_mag_mas_kollazs(self, kepek):
        elso = make_picasa_collage(kepek, _beallitas(theme=PICTUREPILE, seed=1)).image
        masodik = make_picasa_collage(kepek, _beallitas(theme=PICTUREPILE, seed=2)).image
        assert not np.array_equal(elso, masodik)


class TestHibasBemenet:
    def test_hianyzo_fajl_kimarad_de_nem_all_le(self, kepek, tmp_path):
        jelentes = make_picasa_collage(
            [*kepek, tmp_path / "nincs.png"], _beallitas(theme=PICTUREGRID)
        )
        assert len(jelentes.used) == 4
        assert len(jelentes.missing) == 1
        assert jelentes.reasons == ("a fájl nem található",)

    def test_csupa_hianyzo_forras_ures_lapot_ad(self, tmp_path):
        jelentes = make_picasa_collage([tmp_path / "a.png"], _beallitas())
        assert jelentes.used == ()
        assert np.all(jelentes.image == 255)

    def test_ures_forraslista_hibat_dob(self):
        with pytest.raises(ValueError, match="legalább egy kép"):
            make_picasa_collage([], _beallitas())

    @pytest.mark.parametrize(
        ("mezo", "ertek"),
        [("theme", "nincs_ilyen"), ("border", "nincs_ilyen"), ("spacing", 1.5)],
    )
    def test_ervenytelen_beallitas_hibat_dob(self, mezo, ertek):
        with pytest.raises(ValueError):
            _beallitas(**{mezo: ertek})


class TestIndexkep:
    def test_a_fejlec_savja_a_lap_tetejen_van(self, kepek):
        """Az Indexkép fejléce megkülönbözteti a Rácstól."""
        indexkep = make_picasa_collage(
            kepek, _beallitas(theme=CONTACTSHEET, caption="2026. augusztus")
        ).image
        sav = indexkep[: round(240 * 0.08)]
        assert not np.all(sav == 255), "a feliratnak látszania kell a fejlécben"

    def test_felirat_nelkul_is_lefut(self, kepek):
        jelentes = make_picasa_collage(kepek, _beallitas(theme=CONTACTSHEET))
        assert jelentes.image.shape == (240, 320, 3)


class TestTobbszorosExponalas:
    def test_a_keveres_kozteserteket_ad(self, kepek):
        """Négy telített kép átlaga nem lehet egyik eredeti szín sem."""
        kep = make_picasa_collage(kepek, _beallitas(theme=MULTIEXP)).image
        kozep = kep[120, 160]
        assert 0 < int(kozep.max()) < 255 or int(kozep.min()) > 0
