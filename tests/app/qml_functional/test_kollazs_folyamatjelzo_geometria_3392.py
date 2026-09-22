"""A kollázs folyamatjelzőjének BELSŐ geometriája és szülőlánca — #3392.

MÉRT (`docs/specs/picasa-create-features.md` 1.10.4, a `respack` abszolút
koordinátáiból az alapdobozhoz viszonyítva):

| elem | eredeti név | x, y | méret |
|---|---|---|---|
| alapdoboz | `collageprog_base` | — | 224 × 80 |
| cím | `collageprog_title` | 5, 6 | 213 × 14 |
| pörgő | `collageprog_spinner` | 100, 24 | 29 × 31 |
| állapotsor | `collageprog_status` | 5, 60 | 213 × 14 |

A szülőlánc az eredetiben `collageprog_base → collageprog_clip →
previewclip → …` (`collagepanel.tre`): a doboz egy SAJÁT vágókeretben ül,
az pedig a vászon területét vágó tárolóban. Nálunk ugyanez:
`collageProgressOverlay → collageProgressClip → collagePreviewClip`.

⚠️ Amit ez a fájl NEM mér: a kirajzolt KÉP egyezését egy eredeti
képernyőképpel — ehhez nincs referencia-kép. A számok a mért `respack`
koordináták; a látvány a kiadás képernyőképén ellenőrizhető.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPointF

from support.collage_canvas_harness import (
    _ablakban,
    _child,
    _panel,
    keszits_kepeket,
    nyitott_vezerlo,
)

#: (x, y, szélesség, magasság) az alapdobozhoz képest — a mért érték.
MERT = {
    "collageProgressTitle": (5, 6, 213, 14),
    "collageProgressSpinner": (100, 24, 29, 31),
    "collageProgressStatus": (5, 60, 213, 14),
}


@pytest.fixture
def library(tmp_path):
    return keszits_kepeket(tmp_path)


@pytest.fixture
def controller(qt_app, tmp_path, library):
    yield from nyitott_vezerlo(tmp_path, library)


@pytest.fixture
def panel(controller):
    return _panel(controller)


def _elem_doboza(item):
    """Az ELEM doboza az ablakban. A `_ablakban` a `boundingRect`-ből indul,
    ami egy `Text`-nél a kirajzolt szövegé, nem az elemé — itt az elem
    saját (0, 0) sarka kell."""
    sarok = item.mapToScene(QPointF(0, 0))
    return (sarok.x(), sarok.y(), item.width(), item.height())


class TestBelsoGeometria:
    @pytest.mark.parametrize("nev", sorted(MERT))
    def test_a_mert_doboz(self, panel, nev):
        ox, oy, _, _ = _elem_doboza(_child(panel, "collageProgressOverlay"))
        x, y, w, h = _elem_doboza(_child(panel, nev))
        assert (round(x - ox), round(y - oy), round(w), round(h)) == MERT[nev]

    def test_az_alapdoboz_224x80(self, panel):
        _, _, w, h = _ablakban(_child(panel, "collageProgressOverlay"))
        assert (round(w), round(h)) == (224, 80)


class TestSzuloLanc:
    def test_a_doboz_sajat_vagokeretben_ul(self, panel):
        overlay = _child(panel, "collageProgressOverlay")
        clip = overlay.parentItem()
        assert clip.objectName() == "collageProgressClip"
        assert clip.property("clip") is True

    def test_a_vagokeret_a_vaszon_teruletet_vago_taroloban(self, panel):
        clip = _child(panel, "collageProgressClip")
        elonezet = clip.parentItem()
        assert elonezet.objectName() == "collagePreviewClip"
        assert elonezet.property("clip") is True

    def test_a_tarolo_pontosan_a_vaszon_terulete(self, panel):
        elonezet = _ablakban(_child(panel, "collagePreviewClip"))
        vaszon = _ablakban(_child(panel, "collageCanvas"))
        assert [round(v) for v in elonezet] == [round(v) for v in vaszon]

    def test_a_doboz_a_vaszon_kozepen_marad(self, panel):
        x, y, w, h = _ablakban(_child(panel, "collageProgressOverlay"))
        cx, cy, cw, ch = _ablakban(_child(panel, "collageCanvas"))
        assert round(x + w / 2) == round(cx + cw / 2)
        assert round(y + h / 2) == round(cy + ch / 2)
