"""#3315: a `Pixelate` csempe Shift-párja (`PicnikFocalPixelate`) megépült.

A bináris (2026-09-22) két kérdést döntött el:

* a lánc-ÍRÓ a leíró nevét írja betűhíven (`0x0042abcc` `"%s=%s;"`, a név a
  leíró `+0x14` mezőjéből: `0x008f6bc0`), az értékrész sorrendje pedig
  `0x008fac40` szerint: engedélyezés → puck x,y → az első három csúszka →
  (szín) → a NEGYEDIK csúszka → a jelölőnégyzetek `,%d`-ként ⇒ a teljes alak
  **nyolcmezős**: `PicnikFocalPixelate=1,x,y,Impact,Radius,Hardness,Fade,Reverse;`
* a betöltő úton semmi nem zárja ki: a név a `filterdesc.xml`-regiszterben
  van (`0x008f9fe0` → `0x008f9a60`), tehát a #1142 „nem fut" mérése rossz
  aritású (hét-, illetve négymezős) sorra készült.

A felhasználó képernyőképe (`3315-pixelate-parja`) ugyanezt mutatja:
Shifttel a csempe neve „Képpontnövelés", panelje Hatás · Sugár ·
Élkeménység · Fokozat + Megfordítás.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini import parse_filters, serialize_filters
from picasapy.ini.filter_registry import canonicalize_filter_name
from picasapy.render import apply_filters
from picasapy.render.chain import _HANDLERS, can_render_filter

TELJES = "PicnikFocalPixelate=1,0.500000,0.500000,40.000000,60.000000,50.000000,0.000000,0;"


@pytest.fixture
def minta():
    y, x = np.mgrid[0:64, 0:96]
    return np.dstack([(x * 255 // 96), (y * 255 // 64), np.full((64, 96), 120)]).astype(np.uint8)


def test_a_nyolcmezos_alak_lefut(minta):
    jelentes = apply_filters(minta, parse_filters(TELJES))
    assert jelentes.skipped == ()
    assert not np.array_equal(jelentes.image, minta)


def test_van_kezeloje_es_renderelheto():
    assert "picnikfocalpixelate" in _HANDLERS
    assert can_render_filter("PicnikFocalPixelate")


def test_a_kanonikus_nev_a_leiro_neve():
    """A lánc-író a `filterdesc.xml` `id`-jét írja, betűhíven."""
    assert canonicalize_filter_name("picnikfocalpixelate") == "PicnikFocalPixelate"


def test_a_nyolcadik_mezo_a_megforditas(minta):
    """`_chkReverse` — a körmaszk két alfájának cseréje (#788): a kör
    közepe helyett a széle lesz pixeles, tehát MÁS a kimenet."""
    ki = apply_filters(minta, parse_filters(TELJES)).image
    forditva = apply_filters(
        minta, parse_filters(TELJES[:-2] + "1;")
    ).image
    assert not np.array_equal(ki, forditva)


def test_a_lanc_korbe_jar(minta):
    """Írás–olvasás: a nyolc mező megmarad, a név kanonikus."""
    ops = parse_filters(TELJES)
    assert len(ops[0].params) == 8
    assert serialize_filters(ops) == TELJES


def test_a_shift_ag_be_van_kotve():
    """A QML-csempe Shift-ága és a render-kezelő együtt mozog."""
    from pathlib import Path

    qml = (
        Path(__file__).resolve().parents[2]
        / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "EditorEffectsTab3.qml"
    ).read_text(encoding="utf-8")
    assert '? "picnikfocalpixelate"' in qml
    assert 'qsTr("Focal Pixelate")' in qml


def test_a_felulet_katalogusaban_is_ott_van():
    from picasapy.app.edit_controller import _EFFECT_INI_NAMES, _EFFECT_NAMES

    assert "picnikfocalpixelate" in _EFFECT_NAMES
    assert _EFFECT_INI_NAMES["picnikfocalpixelate"] == "PicnikFocalPixelate"
