"""#3462: a festett ecset-maszk a MENTETT képre is hat.

A maszkot eddig egyedül az előnézeti út adta át a láncnak
(`edit_preview.py`: `apply_filters(..., paint_mask=maszk)`); a mentés maszk
nélkül renderelt, így a Felpörgetés, a Képpontnagyítás, a Lágyítás és az
Árnyalás a mentett fájlban az EGÉSZ képre került rá.

A mérce képpont-összevetés: ugyanaz a vonás az előnézeten és a mentett képen
ugyanazt a területet érinti.

⚠️ Az előnézet a láncot a FORGATATLAN forráson futtatja (a néző a kirajzolt
elemet forgatja), a vonások tehát a forrás terében vannak. A mentés a
forgatás UTÁN renderel, ezért a maszkot a képpel azonos módon kell tükrözni
és forgatni — ezt a forgatott eset méri.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.app.paint_mask import Vonas, maszk_vonasokbol
from picasapy.app.save_controller import _render_for_save
from picasapy.edit.session import EditSession
from picasapy.render.chain import apply_filters

#: képpontonkénti (térbeli szomszédság nélküli) festhető effekt — így a
#: forgatott eset is bitre összevethető
LANC = "PicnikTint=1,0.000000,0080cfff;"
VONASOK = (Vonas(0.25, 0.3, 0.12, False), Vonas(0.3, 0.35, 0.12, False))


@pytest.fixture
def kep(tmp_path) -> Path:
    rng = np.random.default_rng(3462)
    bgr = rng.integers(0, 256, size=(60, 90, 3), dtype=np.uint8)
    utvonal = tmp_path / "kep.png"
    assert cv2.imwrite(str(utvonal), bgr)
    return utvonal


def _elonezet(utvonal: Path) -> np.ndarray:
    """Az előnézet útja: a forgatatlan forrás, a vonásokból épített maszk."""
    rgb = cv2.cvtColor(cv2.imread(str(utvonal)), cv2.COLOR_BGR2RGB)
    ops = EditSession.from_value(LANC).ops
    maszk = maszk_vonasokbol(VONASOK, rgb.shape[0], rgb.shape[1])
    kesz = apply_filters(rgb, ops, paint_mask=maszk).image
    return cv2.cvtColor(kesz, cv2.COLOR_RGB2BGR)


def test_a_mentett_kep_ugyanott_valtozik_mint_az_elonezet(kep):
    mentett = _render_for_save(kep, 0, LANC, 0, paint_strokes=VONASOK)
    np.testing.assert_array_equal(mentett, _elonezet(kep))


def test_a_festetlen_terulet_erintetlen_marad(kep):
    eredeti = cv2.imread(str(kep))
    mentett = _render_for_save(kep, 0, LANC, 0, paint_strokes=VONASOK)
    valtozott = (mentett != eredeti).any(axis=-1)
    assert valtozott[18, 22], "a befestett terület nem változott"
    assert not valtozott[:, 60:].any(), "a festetlen jobb oldal is megváltozott"


def test_forgatott_kepnel_a_maszk_a_keppel_egyutt_fordul(kep):
    mentett = _render_for_save(kep, 1, LANC, 0, paint_strokes=VONASOK)
    np.testing.assert_array_equal(
        mentett, cv2.rotate(_elonezet(kep), cv2.ROTATE_90_CLOCKWISE)
    )


def test_tukrozott_kepnel_a_maszk_a_keppel_egyutt_tukrozodik(kep):
    mentett = _render_for_save(kep, 0, LANC, 1, paint_strokes=VONASOK)
    np.testing.assert_array_equal(mentett, cv2.flip(_elonezet(kep), 1))


def test_vonas_nelkul_a_regi_viselkedes_marad(kep):
    np.testing.assert_array_equal(
        _render_for_save(kep, 0, LANC, 0, paint_strokes=()),
        _render_for_save(kep, 0, LANC, 0),
    )


class TestBekotes:
    """A szerkesztő → mentés híd: CSAK a szerkesztett kép kapja a festést."""

    def _szerkeszto(self, kep_utja: Path):
        from picasapy.app.paint_mask_controller import PaintMaskMixin

        class _Szerkeszto(PaintMaskMixin):
            paintMaskSupported = True  # noqa: N815 — a mixin QML-neve

        szerkeszto = _Szerkeszto()
        szerkeszto._init_paint_mask()
        szerkeszto._image_path = kep_utja
        szerkeszto._paint_mask.fess(0.25, 0.3, 0.12, False)
        return szerkeszto

    def test_a_szerkesztett_kep_megkapja_a_vonasokat(self, tmp_path):
        utvonal = tmp_path / "a.jpg"
        assert len(self._szerkeszto(utvonal).paint_strokes_for_path(utvonal)) == 1

    def test_masik_kep_mentese_nem_kap_festest(self, tmp_path):
        szerkeszto = self._szerkeszto(tmp_path / "a.jpg")
        assert szerkeszto.paint_strokes_for_path(tmp_path / "b.jpg") == ()

    def test_a_mentes_a_szolgaltatotol_keri_a_vonasokat(self, tmp_path):
        from picasapy.app.save_controller import SaveMixin

        mentes = SaveMixin.__new__(SaveMixin)
        assert mentes._festes_vonasai(tmp_path / "a.jpg") == ()
        mentes.set_paint_strokes_provider(lambda p: VONASOK if p.name == "a.jpg" else ())
        assert mentes._festes_vonasai(tmp_path / "a.jpg") == VONASOK
        assert mentes._festes_vonasai(tmp_path / "b.jpg") == ()
