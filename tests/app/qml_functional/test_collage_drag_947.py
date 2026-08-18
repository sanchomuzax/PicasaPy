"""A kollázs-vászon MANIPULÁCIÓI, KIRAJZOLVA — #947 (2/2).

Spec: `docs/specs/kollazs-panel-ui-spec.md` **7.1**, **7.3** és **7.7**.

Mozgatás elhúzási küszöb nélkül, a csere, az `Alt`-tal a legfelső rétegbe,
a kijelölés és a kézi szerkesztés megmaradása. A vászon felépítése és a
gyűrű matematikája a testvérfájlban van (`test_collage_canvas_947.py`).

Mindegyik viselkedés csak VALÓDI eseménysorral mérhető: a húzási küszöb, a
rétegváltás és a csere property-olvasásból nem látszik.
"""

from __future__ import annotations

import math

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest

from support.collage_canvas_harness import (
    GYURU,
    _ablakban,
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

# --- 5. Mozgatás (spec 7.3) --------------------------------------------------


def test_nincs_elhuzasi_kuszob(controller):
    """Az ELSŐ egérmozdulatra indul a mozgatás — nincs 10 képpontos küszöb.

    A 10 képpontos küszöb a fájlrendszer felé menő OLE-vonszoláshoz
    tartozik, nem ide (spec 7.3)."""
    panel = _panel(controller)
    view = panel.property("_view")
    elotte = _csomopontok(controller)[0].center_x

    elem = _child(panel, "collageNode0")
    kozep_x, kozep_y = _kozeppont(elem)
    kezdo = QPoint(round(kozep_x), round(kozep_y))
    _eger_le(view, kezdo)
    _eger_mozog(view, QPoint(kezdo.x() + 1, kezdo.y()))

    utana = _csomopontok(controller)[0].center_x
    assert utana != elotte, "egyetlen képpontnyi mozdulat is mozgat"
    _eger_fel(view, QPoint(kezdo.x() + 1, kezdo.y()))


def test_huzas_kozben_az_atlatszatlansag_09(controller):
    """`opacity = 0.9` húzás közben, felengedve 1,0 (spec 7.3)."""
    panel = _panel(controller)
    view = panel.property("_view")
    elem = _child(panel, "collageNode0")
    assert elem.opacity() == pytest.approx(1.0)

    kozep_x, kozep_y = _kozeppont(elem)
    kezdo = QPoint(round(kozep_x), round(kozep_y))
    _eger_le(view, kezdo)
    assert elem.opacity() == pytest.approx(0.9)
    _eger_mozog(view, QPoint(kezdo.x() + 20, kezdo.y() + 20))
    assert elem.opacity() == pytest.approx(0.9)
    _eger_fel(view, QPoint(kezdo.x() + 20, kezdo.y() + 20))
    assert elem.opacity() == pytest.approx(1.0)


def test_a_mozgatas_a_fogasi_eltolast_tartja(controller):
    """`csomópont = egér − fogási_eltolás` — a kép nem ugrik a kurzorhoz."""
    panel = _panel(controller)
    view = panel.property("_view")
    egyseg = _egyseg(panel)
    elotte = _csomopontok(controller)[0]

    elem = _child(panel, "collageNode0")
    kozep_x, kozep_y = _kozeppont(elem)
    # SZÁNDÉKOSAN nem a közepén fogjuk meg
    kezdo = QPoint(round(kozep_x + 12), round(kozep_y + 7))
    cel = QPoint(kezdo.x() + 40, kezdo.y() - 25)
    _eger_le(view, kezdo)
    _eger_mozog(view, cel)
    _eger_fel(view, cel)

    utana = _csomopontok(controller)[0]
    assert utana.center_x == pytest.approx(elotte.center_x + 40 / egyseg, abs=1.5)
    assert utana.center_y == pytest.approx(elotte.center_y - 25 / egyseg, abs=1.5)


# --- 6. Csere (spec 7.3) -----------------------------------------------------


def test_egy_kepet_a_masikra_ejtve_cserelnek(controller):
    """A KÉPEK cserélnek helyet; a fogadó mérete, kerete és szöge MARAD."""
    panel = _panel(controller)
    view = panel.property("_view")
    controller.transformNode(1, 1.7, math.radians(20.0))
    QGuiApplication.instance().processEvents()

    elotte = _csomopontok(controller)
    ut0, ut1 = elotte[0].path, elotte[1].path
    fogado_meret = (elotte[1].width, elotte[1].height)
    fogado_szog = elotte[1].theta
    fogado_keret = elotte[1].border

    honnan = _kozeppont(_child(panel, "collageNode0"))
    hova = _kozeppont(_child(panel, "collageNode1"))
    _eger_le(view, QPoint(round(honnan[0]), round(honnan[1])))
    _eger_mozog(view, QPoint(round(hova[0]), round(hova[1])))
    _eger_fel(view, QPoint(round(hova[0]), round(hova[1])))

    utana = _csomopontok(controller)
    assert (utana[0].path, utana[1].path) == (ut1, ut0), "a képek cserélnek"
    assert (utana[1].width, utana[1].height) == fogado_meret
    assert utana[1].theta == fogado_szog
    assert utana[1].border == fogado_keret


def test_a_csere_nem_athelyezes(controller):
    """„Nem áthelyezés, hanem csere" — a húzott RÉS a helyén marad."""
    panel = _panel(controller)
    view = panel.property("_view")
    elotte = _csomopontok(controller)[0]

    honnan = _kozeppont(_child(panel, "collageNode0"))
    hova = _kozeppont(_child(panel, "collageNode1"))
    _eger_le(view, QPoint(round(honnan[0]), round(honnan[1])))
    _eger_mozog(view, QPoint(round(hova[0]), round(hova[1])))
    _eger_fel(view, QPoint(round(hova[0]), round(hova[1])))

    utana = _csomopontok(controller)[0]
    assert utana.center_x == pytest.approx(elotte.center_x, abs=0.5)
    assert utana.center_y == pytest.approx(elotte.center_y, abs=0.5)


def test_a_puszta_kattintas_NEM_cserel(controller):
    """A csere gesztusa az EJTÉS, nem a kattintás (spec 7.3).

    A képkupac képei fedik egymást. Ha a felengedés magától cserélne, akkor
    minden olyan kattintás, amivel a felhasználó csak KI AKAR JELÖLNI egy
    képet, némán helyet cserélne két fájllal — és a felhasználó azt látná,
    hogy a képei maguktól ugrálnak. Egérmozdulat nélkül tehát tilos csere."""
    panel = _panel(controller)
    view = panel.property("_view")
    elotte = [node.path for node in _csomopontok(controller)]

    # Az őrnek csak akkor van foga, ha a pont TÉNYLEG két képen van rajta.
    pont = _lap_pont(panel, 300.0, 320.0)
    fedok = [
        index
        for index in range(3)
        if _tartalmazza(_child(panel, f"collageNode{index}"), pont)
    ]
    assert len(fedok) >= 2, f"a pont csak a(z) {fedok} képen van — nincs mit cserélni"

    _eger_le(view, pont)
    _eger_fel(view, pont)

    assert [node.path for node in _csomopontok(controller)] == elotte


# --- 7. Alt = a legfelső rétegbe (spec 7.3) ----------------------------------


def test_alt_lenyomas_a_legfelso_retegbe_visz(controller):
    """`Alt` + lenyomás: a kép a lista VÉGÉRE (legfelülre) kerül."""
    panel = _panel(controller)
    view = panel.property("_view")
    elotte = [node.path for node in _csomopontok(controller)]

    kozep = _kozeppont(_child(panel, "collageNode0"))
    pont = QPoint(round(kozep[0]), round(kozep[1]))
    _eger_le(view, pont, Qt.KeyboardModifier.AltModifier)
    _eger_fel(view, pont, Qt.KeyboardModifier.AltModifier)

    utana = [node.path for node in _csomopontok(controller)]
    assert utana == [elotte[1], elotte[2], elotte[0]]


def _reteg_allapot(controller):
    """A rétegsorrend és a geometria — a KIJELÖLÉS nélkül.

    A kijelölés szándékosan marad ki: minden kattintás kijelöl (spec 7.1,
    `CollageNodeHandler`), tehát azt összehasonlítani annyi volna, mint a
    kijelölést hibának nevezni."""
    return [
        (node.path, node.center_x, node.center_y, node.width, node.height, node.theta)
        for node in _csomopontok(controller)
    ]


def test_alt_a_legfelsonel_nem_valtoztat_semmit(controller):
    """„Ha már ott van, nem történik semmi" — nincs villanás (spec 7.3)."""
    panel = _panel(controller)
    view = panel.property("_view")
    elotte = _reteg_allapot(controller)

    kozep = _kozeppont(_child(panel, "collageNode2"))
    pont = QPoint(round(kozep[0]), round(kozep[1]))
    _eger_le(view, pont, Qt.KeyboardModifier.AltModifier)
    _eger_fel(view, pont, Qt.KeyboardModifier.AltModifier)

    assert _reteg_allapot(controller) == elotte


def test_alt_utan_a_felemelt_kep_mozog_tovabb(controller):
    """„…és onnan mozog tovább" — a húzás a FELEMELT képre vonatkozik."""
    panel = _panel(controller)
    view = panel.property("_view")
    egyseg = _egyseg(panel)
    ut0 = _csomopontok(controller)[0].path
    kezdo_kozep = _csomopontok(controller)[0].center_x

    kozep = _kozeppont(_child(panel, "collageNode0"))
    pont = QPoint(round(kozep[0]), round(kozep[1]))
    cel = QPoint(pont.x() + 30, pont.y())
    _eger_le(view, pont, Qt.KeyboardModifier.AltModifier)
    _eger_mozog(view, cel, Qt.KeyboardModifier.AltModifier)
    _eger_fel(view, cel, Qt.KeyboardModifier.AltModifier)

    utana = _csomopontok(controller)
    assert utana[-1].path == ut0, "a felemelt kép a legfelső rétegben van"
    assert utana[-1].center_x == pytest.approx(kezdo_kozep + 30 / egyseg, abs=1.5)


def test_alt_nem_masol_es_nem_klonoz(controller):
    """Az `Alt` NEM másol — a darabszám nem változhat (spec 14.)."""
    panel = _panel(controller)
    view = panel.property("_view")
    kozep = _kozeppont(_child(panel, "collageNode0"))
    pont = QPoint(round(kozep[0]), round(kozep[1]))
    _eger_le(view, pont, Qt.KeyboardModifier.AltModifier)
    _eger_fel(view, pont, Qt.KeyboardModifier.AltModifier)
    assert len(_csomopontok(controller)) == 3


# --- 8. Kijelölés (spec 7.1) -------------------------------------------------


def test_kattintas_kijelol_es_a_tobbirol_leveszi(controller):
    panel = _panel(controller)
    view = panel.property("_view")
    controller.setCollageSelection([1, 2])
    QGuiApplication.instance().processEvents()

    kozep = _kozeppont(_child(panel, "collageNode0"))
    pont = QPoint(round(kozep[0]), round(kozep[1]))
    _eger_le(view, pont)
    _eger_fel(view, pont)
    assert list(controller.collageSelection) == [0]


def test_ctrl_kattintas_hozzaad_es_elvesz(controller):
    panel = _panel(controller)
    view = panel.property("_view")
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()

    # ⚠️ NEM a kép közepére kattintunk: az első Ctrl+kattintás után a képre
    # rákerül a gyűrű, ami a közepét eltakarja, és a belseje MOZGAT, nem
    # kijelöl (spec 7.2). A kijelölés elvétele tehát a gyűrűn kívül, de a
    # képen belül történik — pontosan úgy, ahogy a felhasználó is teszi.
    elem = _child(panel, "collageNode2")
    kozep = _kozeppont(elem)
    tavolsag = (GYURU / 2 + elem.width() / 2) / 2
    assert tavolsag > GYURU / 2, "a képen nincs a gyűrűn kívüli pont"
    pont = QPoint(round(kozep[0] + tavolsag), round(kozep[1]))
    assert _tartalmazza(elem, pont), "a kattintás lecsúszott a képről"

    _eger_le(view, pont, Qt.KeyboardModifier.ControlModifier)
    _eger_fel(view, pont, Qt.KeyboardModifier.ControlModifier)
    assert sorted(controller.collageSelection) == [0, 2]

    _eger_le(view, pont, Qt.KeyboardModifier.ControlModifier)
    _eger_fel(view, pont, Qt.KeyboardModifier.ControlModifier)
    assert list(controller.collageSelection) == [0]


def test_ures_teruletre_kattintva_megszunik_a_kijeloles(controller):
    """`CollageDeselectHandler` — az üres vászon kattintása töröl (spec 7.1)."""
    panel = _panel(controller)
    view = panel.property("_view")
    controller.setCollageSelection([0, 1])
    QGuiApplication.instance().processEvents()

    vaszon = _child(panel, "collageCanvas")
    x, y, _, _ = _ablakban(vaszon)
    _eger_le(view, QPoint(round(x + 4), round(y + 4)))
    _eger_fel(view, QPoint(round(x + 4), round(y + 4)))
    assert list(controller.collageSelection) == []


def test_ctrl_a_es_ctrl_d(controller):
    """A buboréksúgók kimondják: Ctrl+A = mind, Ctrl+D = semmi (spec 7.1).

    ⚠️ A #945 tanulsága: `Keys` kezelő fókusz nélkül SOHA nem tüzel, ezért
    ez a teszt VALÓDI billentyűt küld a kirajzolt ablaknak."""
    panel = _panel(controller)
    view = panel.property("_view")
    QTest.keyClick(view, Qt.Key_A, Qt.KeyboardModifier.ControlModifier)
    assert sorted(controller.collageSelection) == [0, 1, 2]
    QTest.keyClick(view, Qt.Key_D, Qt.KeyboardModifier.ControlModifier)
    assert list(controller.collageSelection) == []


def test_a_del_eltavolitja_a_kijeloltet(controller):
    panel = _panel(controller)
    view = panel.property("_view")
    controller.setCollageSelection([1])
    QGuiApplication.instance().processEvents()
    QTest.keyClick(view, Qt.Key_Delete)
    assert len(_csomopontok(controller)) == 2


def test_az_esc_tovabbra_is_bezar(controller):
    """Regresszió-őr a #945-re: a vászon billentyűkezelője nem nyelheti el
    az Esc-et — a lap bezárása az `escapekey 1` szerint az Esc-en van."""
    panel = _panel(controller)
    view = panel.property("_view")
    assert controller.collageOpen is True
    QTest.keyClick(view, Qt.Key_Escape)
    assert controller.collageOpen is False


# --- 9. A kézi szerkesztés megmarad (a `collage_adapt` célja, spec 7.7) ------


def test_a_kezi_szerkesztes_a_felengedes_utan_a_modellben_van(controller):
    """A manipuláció VÉGÉN az állapot a modellben ül — nem a felületen.

    A `collage_adapt` célja (spec 7.7) éppen ez: a kézi szerkesztés ne
    vesszen el egy későbbi újrarajzoláskor. Nálunk a modell az igazságforrás,
    tehát az őr az, hogy a felengedés után a modell a VÉGSŐ állapotot
    tartalmazza, és a lap „piszkos"-ra vált."""
    panel = _panel(controller)
    view = panel.property("_view")
    egyseg = _egyseg(panel)
    elotte = _csomopontok(controller)[0]
    assert controller.collageDirty is False

    kozep = _kozeppont(_child(panel, "collageNode0"))
    pont = QPoint(round(kozep[0]), round(kozep[1]))
    cel = QPoint(pont.x() + 33, pont.y() + 21)
    _eger_le(view, pont)
    _eger_mozog(view, cel)
    _eger_fel(view, cel)

    utana = _csomopontok(controller)[0]
    assert utana.center_x == pytest.approx(elotte.center_x + 33 / egyseg, abs=1.5)
    assert utana.center_y == pytest.approx(elotte.center_y + 21 / egyseg, abs=1.5)
    assert controller.collageDirty is True
