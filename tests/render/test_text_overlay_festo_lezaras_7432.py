"""#7432: a Qt-s szövegrajzoló kivétel esetén sem hagyhat aktív festőt a képen.

A CI-n a `test_szoveg_clear_all_cancel_7407.py` részfutása összeomlott:

    QPaintDevice: Cannot destroy paint device that is being painted
    Fatal Python error: Segmentation fault   (_pytest/logging.py, teardown)

Gyökérok: a `_draw_qt_font` a `QPainter`-t a `QImage`-en nyitja, és a
`painter.end()` nem `finally`-ben állt. Ha a festési ablakban kivétel
keletkezett, a háttérszál `_log.exception`-nel naplózta, a naplórekord pedig
megtartotta a tracebacketet, vagyis a keretet a `qimage` és a `painter`
helyi változóival. A keret felszabadításakor a `qimage` a `painter` ELŐTT
szabadult fel, a Qt pedig festés közben megsemmisülő eszközt látott.

A próba nem az összeomlást várja meg (az a teszt-folyamatot is megölné),
hanem a gyökérokot méri: a kivétel pillanatában már nem lehet aktív a festő.
"""

from __future__ import annotations

import numpy as np
import pytest

import picasapy.render.text_overlay as text_overlay

_ARGUMENTUMOK = {
    "origin": (2, 2),
    "color": (255, 255, 255),
    "outline_thickness": 2,
    "fill_enabled": True,
    "has_outline": True,
    "align": "left",
}


@pytest.fixture
def figyelt_festok(monkeypatch, qt_app):
    """Minden `_draw_qt_font`-hívásban létrejövő `QPainter` példányt feljegyez."""
    from PySide6 import QtGui

    peldanyok: list = []

    class FigyeltFesto(QtGui.QPainter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            peldanyok.append(self)

    monkeypatch.setattr(QtGui, "QPainter", FigyeltFesto)
    # ⚠️ lebontáskor a festőkhöz NEM nyúlunk: a hozzájuk tartozó kép addigra
    # felszabadult, egy aktív festő `isActive()`-ja pedig szabad memóriát olvas.
    # A teszt törzse zárja a festőt, amíg a kivétel kerete még él.
    yield peldanyok


def _font():
    from picasapy.render.text_fonts import qt_font_for

    font = qt_font_for("Arial", 12, bold=False, italic=False, underline=False)
    assert font is not None
    return font


def _hivas(outline_color):
    base = np.zeros((40, 80, 3), dtype=np.uint8)
    return text_overlay._draw_qt_font(
        base,
        "Proba",
        _ARGUMENTUMOK["origin"],
        _font(),
        _ARGUMENTUMOK["color"],
        outline_color,
        _ARGUMENTUMOK["outline_thickness"],
        _ARGUMENTUMOK["fill_enabled"],
        _ARGUMENTUMOK["has_outline"],
        _ARGUMENTUMOK["align"],
    )


class TestFestoLezarasKivetelEseten7432:
    def test_kivetel_a_festesi_ablakban_nem_hagy_aktiv_festot(self, figyelt_festok):
        """A hibás körvonalszín a QPainter létrehozása UTÁN dob ValueError-t."""
        try:
            _hivas(("x",))
        except ValueError as kivetel:
            # a naplórekord exc_info-ját utánozza: a traceback, vagyis a
            # `_draw_qt_font` kerete a teszt végéig él
            megtartott = kivetel
        else:
            pytest.fail("a hibás körvonalszínnek ValueError-t kellett dobnia")

        assert megtartott.__traceback__ is not None
        assert len(figyelt_festok) == 1, "pontosan egy festőnek kellett létrejönnie"
        festo = figyelt_festok[0]
        aktiv = festo.isActive()
        if aktiv:
            # a bukó (javítás előtti) állapotban a teszt maga zárja a festőt,
            # különben a keret felszabadulása leölné a teszt-folyamatot is
            festo.end()
        assert aktiv is False, (
            "A festő a kivétel után is aktív maradt: a kép felszabadulásakor "
            "a Qt festés közben megsemmisülő eszközt lát (szegmenshiba)."
        )

    def test_rendes_hivas_lezarja_a_festot_es_rajzol(self, figyelt_festok):
        """Kontroll: a rendes úton a festő zárt, és a rajz tényleg a képre került."""
        kep = _hivas((0, 0, 0))

        assert len(figyelt_festok) == 1
        assert figyelt_festok[0].isActive() is False
        assert kep.shape == (40, 80, 3)
        assert int(kep.sum()) > 0, "a szöveg nem került a képre"
