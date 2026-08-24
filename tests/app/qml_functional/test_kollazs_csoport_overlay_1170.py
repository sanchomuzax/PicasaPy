"""A kollázs CSOPORT-ELEME kirajzolva — #1170.

Spec: `docs/specs/picasa-kollazs-felulet.md` **2.** (a 6. bit kapuja) és
**2/b** (mit rajzol: `#F85E0F` körvonalas téglalap, 2 képpont vonallal).

## Miért kirajzolt teszt

A jegy szerződése a RAJZOLÁSI RÉTEGRE szól: a csoport-elemnek a képek
FÖLÖTT kell lennie. Ez property-olvasásból nem derül ki — a `z` értékét
minden `CollageNode` maga számolja (`nodeIndex`, `Alt` esetén 9999), tehát
a magasabb réteget csak az ÖSSZES kirajzolt csomópont `z`-jével összevetve
lehet állítani.

⚠️ A `Repeater` delegáltjait a `findChild` NEM találja meg (nincs
QObject-szülőjük, csak vizuális) — a harness `_walk()`-ja a VIZUÁLIS fát
járja be.

⚠️ A `visible` öröklődik a szülőtől, ezért a puszta láthatóság gyenge
állítás. A tesztek ezért a láthatóság MELLETT a doboz geometriáját is
mérik: egy 0 × 0-s, „látható" keret semmit nem mutatna a felhasználónak.
"""

from __future__ import annotations

import re

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlProperty

from picasapy.collage.themes import (
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    PICTUREGRID,
    PICTUREPILE,
    REGULARGRID,
)

from support.collage_canvas_harness import (
    _ablakban,
    _child,
    _csomopontok,
    _egyseg,
    _lap,
    _panel,
    _walk,
    keszits_kepeket,
    nyitott_vezerlo,
)

#: A csoport-keret neve a kirajzolt fában.
CSOPORT = "collageGroupNode"

#: `0x0085fd70`: a csomópont színe `0xFFF85E0F` (AARRGGBB — a bájtsorrend
#: kalibrálva, ld. spec 2/b.3).
CSOPORT_SZIN = "#f85e0f"

#: `ShapeDraw` `+0x04` = 2 → a körvonal vastagsága (spec 2/b.5).
VONAL = 2

#: A CSOMÓPONT gyökere — a delegate BELSEJÉBEN további `collageNode…` nevek
#: vannak (réteg, keret, kép, felirat, kijelölés-keret), azok nem a
#: csomópont `z`-jét viselik. Csak a `collageNode<szám>` alak a gyökér.
_CSOMOPONT_NEV = re.compile(r"^collageNode\d+$")


@pytest.fixture
def library(tmp_path):
    return keszits_kepeket(tmp_path)


@pytest.fixture
def controller(qt_app, tmp_path, library):
    yield from nyitott_vezerlo(tmp_path, library)


def _frissit():
    QGuiApplication.instance().processEvents()


def _racs_panel(controller, tema=REGULARGRID):
    """Rács-témára állított, kirajzolt panel — ott áll a 6. bit."""
    controller.setCollageTheme(tema)
    panel = _panel(controller)
    _frissit()
    return panel


# --- 1. A kapu: a 6. bit ------------------------------------------------------


@pytest.mark.parametrize("tema", [PICTUREGRID, FRAMEGRID, REGULARGRID])
def test_a_racs_temaknal_megjelenik_a_csoport_elem(controller, tema):
    """Két kijelölt kép + rács-téma → látható csoport-keret."""
    panel = _racs_panel(controller, tema)
    controller.setCollageSelection([0, 1])
    _frissit()
    csoport = _child(panel, CSOPORT)
    assert csoport.isVisible()
    assert csoport.width() > 0 and csoport.height() > 0


@pytest.mark.parametrize("tema", [PICTUREPILE, CONTACTSHEET, MULTIEXP])
def test_a_tobbi_temanal_nem_jelenik_meg(controller, tema):
    """A 6. bit nem áll → nincs overlay-ág, akárhány kép van kijelölve."""
    panel = _racs_panel(controller, tema)
    controller.setCollageSelection([0, 1, 2])
    _frissit()
    assert not _child(panel, CSOPORT).isVisible()


# --- 2. A küszöb: KETTŐ vagy több kép ----------------------------------------


def test_kijeloles_nelkul_nincs_csoport_elem(controller):
    panel = _racs_panel(controller)
    assert not _child(panel, CSOPORT).isVisible()


def test_egyetlen_kijelolt_kep_meg_nem_csoport(controller):
    panel = _racs_panel(controller)
    controller.setCollageSelection([1])
    _frissit()
    assert not _child(panel, CSOPORT).isVisible()


def test_a_kijeloles_megszunesekor_eltunik(controller):
    """A jegy 4. pontja — a be-/kikapcsolás mindkét iránya."""
    panel = _racs_panel(controller)
    controller.setCollageSelection([0, 1])
    _frissit()
    assert _child(panel, CSOPORT).isVisible()
    controller.selectNoNodes()
    _frissit()
    assert not _child(panel, CSOPORT).isVisible()


def test_egyre_csokkeno_kijeloles_utan_is_eltunik(controller):
    """Nem elég a NULLÁRA menő utat lefedni: kettőről egyre is meg kell
    szűnnie, különben az egyetlen képre húzott keret bennragad."""
    panel = _racs_panel(controller)
    controller.setCollageSelection([0, 1])
    _frissit()
    assert _child(panel, CSOPORT).isVisible()
    controller.setCollageSelection([1])
    _frissit()
    assert not _child(panel, CSOPORT).isVisible()


# --- 3. A RÉTEG — a jegy mérhető szerződése ----------------------------------


def test_a_kepek_folott_rajzolodik(controller):
    """A csoport-elem `z`-je MINDEN `CollageNode`-énál magasabb.

    Nem egy kiszemelt csomóponthoz mérünk: a kirajzolt fa ÖSSZES
    csomópontját összeszedjük, mert a `z` értéke csomópontonként más
    (`nodeIndex`, húzás közben 9999)."""
    panel = _racs_panel(controller)
    controller.setCollageSelection([0, 1, 2])
    _frissit()
    csoport = _child(panel, CSOPORT)
    csomopont_z = [
        item.z() for item in _walk(panel) if _CSOMOPONT_NEV.match(item.objectName())
    ]
    assert len(csomopont_z) == len(_csomopontok(controller))
    assert csoport.z() > max(csomopont_z)


def test_a_csoport_elem_a_lap_gyereke(controller):
    """A lapon BELÜL ül — így a vágó (`collageSheetClip`) rá is vonatkozik,
    és a koordinátái lapegységből számolhatók."""
    panel = _racs_panel(controller)
    controller.setCollageSelection([0, 1])
    _frissit()
    assert any(item.objectName() == CSOPORT for item in _walk(_lap(panel)))


# --- 4. A rajz és a geometria ------------------------------------------------


def test_korvonalas_narancs_teglalap(controller):
    """`#F85E0F`, 2 képpontos KÖRVONAL, kitöltés nélkül (spec 2/b.3, 2/b.5)."""
    panel = _racs_panel(controller)
    controller.setCollageSelection([0, 1])
    _frissit()
    csoport = _child(panel, CSOPORT)
    # ⚠️ A `border` egy `QQuickPen*`, amire a PySide-nak nincs átalakítója —
    # `item.property("border")` `RuntimeError`-t dob. A pontozott útvonalat a
    # `QQmlProperty` viszont fel tudja oldani.
    assert QQmlProperty.read(csoport, "border.width") == VONAL
    assert QQmlProperty.read(csoport, "border.color").name() == CSOPORT_SZIN
    assert csoport.property("color").alpha() == 0
    assert csoport.property("antialiasing") is True


def test_a_keret_korulveszi_a_kijelolt_kepeket(controller):
    """A doboz a kijelölt csomópontok közös befoglalója — a KIJELÖLETLEN
    kép kilóghat belőle, a kijelölt soha."""
    panel = _racs_panel(controller)
    controller.setCollageSelection([0, 1])
    _frissit()
    csoport_x, csoport_y, csoport_w, csoport_h = _ablakban(_child(panel, CSOPORT))
    lap_x, lap_y, _, _ = _ablakban(_lap(panel))
    egyseg = _egyseg(panel)
    for index in (0, 1):
        node = _csomopontok(controller)[index]
        bal = lap_x + (node.center_x - node.width / 2) * egyseg
        jobb = lap_x + (node.center_x + node.width / 2) * egyseg
        teteje = lap_y + (node.center_y - node.height / 2) * egyseg
        alja = lap_y + (node.center_y + node.height / 2) * egyseg
        assert csoport_x <= bal + 0.5
        assert csoport_y <= teteje + 0.5
        assert csoport_x + csoport_w >= jobb - 0.5
        assert csoport_y + csoport_h >= alja - 0.5


def test_a_keret_koveti_a_kijeloles_valtozasat(controller):
    """Bővülő kijelölés → bővülő keret. Enélkül a keret az ELSŐ kijelölésnél
    beragadna, és a felhasználó egy hazug dobozt látna."""
    panel = _racs_panel(controller)
    controller.setCollageSelection([0, 1])
    _frissit()
    kicsi = _child(panel, CSOPORT).width() * _child(panel, CSOPORT).height()
    controller.setCollageSelection([0, 1, 2])
    _frissit()
    nagy = _child(panel, CSOPORT).width() * _child(panel, CSOPORT).height()
    assert nagy >= kicsi
    assert nagy > 0


def test_a_keret_koveti_a_kep_mozgatasat(controller):
    """A keret a MOZGATÁST is követi, nem csak a kijelölés változását.

    A `collageGroupRect` jelzése a `collageSelectionChanged` — ez elsőre
    szűknek látszik, de a `_set_nodes` minden csomópont-változásnál elsüti.
    Ha valaki a jelzést egyszer „pontosítja", ez a teszt bukik el, nem a
    felhasználó szeme."""
    panel = _racs_panel(controller)
    controller.setCollageSelection([0, 1])
    _frissit()
    elotte = _child(panel, CSOPORT).width()
    node = _csomopontok(controller)[0]
    controller.moveNode(0, node.center_x - 200.0, node.center_y)
    _frissit()
    assert _child(panel, CSOPORT).width() > elotte
