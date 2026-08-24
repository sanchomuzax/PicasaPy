"""A kollázs mozgató- és cseregesztusának szétválasztása, kirajzolva — #990.

Spec: `docs/specs/picasa-kollazs-felulet.md` **5.2–5.2/c**.

A gyűrű belseje küszöb nélkül mozgat. A kép teste lenyomáskor kijelöl,
majd a lenyomási ponttól 10 képpontnál hosszabb húzás után cseregesztust
indít. A két eseményút felengedéskor sem találkozhat.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QGuiApplication

from support.collage_canvas_harness import (
    _child,
    _csomopontok,
    _eger_fel,
    _eger_le,
    _eger_mozog,
    _egyseg,
    _kozeppont,
    _lap_pont,
    _panel,
    _tartalmazza,
    keszits_kepeket,
    nyitott_vezerlo,
)


@pytest.fixture
def library(tmp_path):
    return keszits_kepeket(tmp_path)


@pytest.fixture
def controller(qt_app, tmp_path, library):
    yield from nyitott_vezerlo(tmp_path, library)


def _utvonalak(controller) -> list[str]:
    return [node.path for node in _csomopontok(controller)]


def _fedje_egymast(controller, panel, also_index: int, felso_index: int) -> QPoint:
    """Két csomópontot azonos középre tesz, és visszaadja a felső közepét."""
    felso = _csomopontok(controller)[felso_index]
    controller.moveNode(also_index, felso.center_x, felso.center_y)
    QGuiApplication.instance().processEvents()
    pont_f = _kozeppont(_child(panel, f"collageNode{felso_index}"))
    pont = QPoint(round(pont_f[0]), round(pont_f[1]))
    assert _tartalmazza(_child(panel, f"collageNode{also_index}"), pont)
    assert _tartalmazza(_child(panel, f"collageNode{felso_index}"), pont)
    return pont


def test_a_gyuru_mozgatasa_atfedesnel_sem_cserel(controller):
    """A gyűrű felengedése nem válhat csereeseménnyé fedésnél sem."""
    panel = _panel(controller)
    view = panel.property("_view")
    _fedje_egymast(controller, panel, also_index=1, felso_index=2)
    controller.setCollageSelection([2])
    QGuiApplication.instance().processEvents()
    kezdo = QPoint(*map(round, _kozeppont(_child(panel, "collageRing2"))))
    cel = QPoint(kezdo.x() + 1, kezdo.y())
    elotte = _csomopontok(controller)[2]
    utak = _utvonalak(controller)

    _eger_le(view, kezdo)
    _eger_mozog(view, cel)
    _eger_fel(view, cel)

    utana = _csomopontok(controller)[2]
    assert utana.center_x == pytest.approx(
        elotte.center_x + 1 / _egyseg(panel), abs=1.5
    ), "a gyűrű első képpontja már mozgat"
    assert _utvonalak(controller) == utak, "a gyűrű felengedése soha nem cserél"


def test_a_kep_teste_nem_mozgat_es_lenyomaskor_kijelol(controller):
    """A kép teste csak kijelöl és cseregesztust élesít, nem mozgat."""
    panel = _panel(controller)
    view = panel.property("_view")
    elem = _child(panel, "collageNode2")
    kezdo = QPoint(*map(round, _kozeppont(elem)))
    cel = QPoint(kezdo.x() + 20, kezdo.y())
    elotte = _csomopontok(controller)[2]

    _eger_le(view, kezdo)
    assert list(controller.collageSelection) == [2], "a kijelölés lenyomáskor történik"
    _eger_mozog(view, cel)

    kozben = _csomopontok(controller)[2]
    assert kozben.center_x == elotte.center_x
    assert kozben.center_y == elotte.center_y
    _eger_fel(view, cel)


def test_tiz_pixelig_nincs_csere(controller):
    """A kép testének 10 px-es küszöbe alatt a fedés sem okoz cserét."""
    panel = _panel(controller)
    view = panel.property("_view")
    kezdo = _fedje_egymast(controller, panel, also_index=0, felso_index=1)
    utak = _utvonalak(controller)
    cel = QPoint(kezdo.x() + 10, kezdo.y())

    _eger_le(view, kezdo)
    _eger_mozog(view, cel)
    _eger_fel(view, cel)

    assert _utvonalak(controller) == utak


def test_a_kuszob_a_lenyomasi_ponthoz_merodik(controller):
    """Két kis részmozdulat összege indít cserét, ha a kezdettől már >10 px."""
    panel = _panel(controller)
    view = panel.property("_view")
    kezdo = _fedje_egymast(controller, panel, also_index=0, felso_index=1)
    utak = _utvonalak(controller)

    _eger_le(view, kezdo)
    _eger_mozog(view, QPoint(kezdo.x() + 6, kezdo.y()))
    _eger_mozog(view, QPoint(kezdo.x() + 11, kezdo.y()))
    _eger_fel(view, QPoint(kezdo.x() + 11, kezdo.y()))

    utana = _utvonalak(controller)
    assert (utana[0], utana[1]) == (utak[1], utak[0])


def test_ctrl_kattintas_utan_a_huzas_sem_cserel(controller):
    """A Ctrl billent, de kifejezetten nem élesíti a cseregesztust."""
    panel = _panel(controller)
    view = panel.property("_view")
    kezdo = _fedje_egymast(controller, panel, also_index=0, felso_index=1)
    utak = _utvonalak(controller)
    cel = QPoint(kezdo.x() + 20, kezdo.y())

    _eger_le(view, kezdo, Qt.KeyboardModifier.ControlModifier)
    assert list(controller.collageSelection) == [1]
    _eger_mozog(view, cel, Qt.KeyboardModifier.ControlModifier)
    _eger_fel(view, cel, Qt.KeyboardModifier.ControlModifier)

    assert _utvonalak(controller) == utak


def test_sajat_csomopontra_ejtes_nem_cserel(controller):
    """A saját kép testén levő ejtés nem számít cserecélpontnak."""
    panel = _panel(controller)
    view = panel.property("_view")
    elem = _child(panel, "collageNode2")
    kezdo = QPoint(*map(round, _kozeppont(elem)))
    utak = _utvonalak(controller)
    elotte = _csomopontok(controller)[2]
    cel = QPoint(kezdo.x() + 20, kezdo.y())
    assert _tartalmazza(elem, cel)
    assert not any(
        _tartalmazza(_child(panel, f"collageNode{index}"), cel)
        for index in (0, 1)
    ), "a célponton csak a húzott csomópont lehet"

    _eger_le(view, kezdo)
    _eger_mozog(view, cel)
    _eger_fel(view, cel)

    utana = _csomopontok(controller)[2]
    assert _utvonalak(controller) == utak
    assert utana.center_x == elotte.center_x
    assert utana.center_y == elotte.center_y


def test_cseregesztus_ures_celra_nem_cserel(controller):
    """10 px után is kell valódi találat: az üres vászon nem cserecél."""
    panel = _panel(controller)
    view = panel.property("_view")
    elem = _child(panel, "collageNode2")
    kezdo = QPoint(*map(round, _kozeppont(elem)))
    cel = _lap_pont(panel, 5.0, 5.0)
    utak = _utvonalak(controller)
    elotte = _csomopontok(controller)[2]
    assert not any(
        _tartalmazza(_child(panel, f"collageNode{index}"), cel)
        for index in range(3)
    ), "a választott célpont nem üres"

    _eger_le(view, kezdo)
    _eger_mozog(view, cel)
    _eger_fel(view, cel)

    utana = _csomopontok(controller)[2]
    assert _utvonalak(controller) == utak
    assert utana.center_x == elotte.center_x
    assert utana.center_y == elotte.center_y
