"""Az élő kollázs-vászon és a gyűrű, KIRAJZOLVA — #947 (1/2).

Spec: `docs/specs/kollazs-panel-ui-spec.md` **6.** és **7.2**, **7.4**.

Ez a fájl a vászon FELÉPÍTÉSÉT méri: a koordinátarendszert, a gyűrű helyét
és méretét, a fogantyú matematikáját és a húzás közbeni feliratokat. A
mozgatás, a csere, az `Alt` és a kijelölés a testvérfájlban van
(`test_collage_drag_947.py`).

Miért kirajzolt teszt, és miért valódi egéresemény: a gyűrű viselkedése nem
property-olvasásból derül ki. A #945 tanulsága szó szerint ez volt — egy
`Keys` kezelő `focus: true` nélkül SOHA nem tüzel, és a property-t olvasó
teszt ezt nem vette észre.
"""

from __future__ import annotations

import math

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QGuiApplication

from picasapy.collage.canvas import angle_caption_degrees, scale_caption_percent
from picasapy.collage.themes import PICTUREPILE, REGULARGRID

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
    _lap,
    _panel,
    _van,
    keszits_kepeket,
    nyitott_vezerlo,
)


@pytest.fixture
def library(tmp_path):
    return keszits_kepeket(tmp_path)


@pytest.fixture
def controller(qt_app, tmp_path, library):
    yield from nyitott_vezerlo(tmp_path, library)

# --- 1. A vászon felépítése és a koordinátarendszer --------------------------


def test_minden_csomoponthoz_tartozik_egy_kirajzolt_elem(controller):
    """A `Repeater` a modellre jár: három kép → három csomópont-elem."""
    panel = _panel(controller)
    for index in range(3):
        assert _van(panel, f"collageNode{index}")
    assert not _van(panel, "collageNode3")


def test_a_csomopont_helye_a_lapegysegbol_szamolodik(controller):
    """`képernyő = lap.x + u * lap.szélesség / 1024`, UGYANAZZAL az osztóval.

    Ez a spec 6.1 törvénye: a lap méretez, de nem torzít. Ha a magasságot
    a lap MAGASSÁGÁVAL osztaná valaki, a kollázs álló formátumban némán
    összenyomódna — és a mentett JPEG mást mutatna, mint a vászon."""
    panel = _panel(controller)
    egyseg = _egyseg(panel)
    lap_x, lap_y, _, _ = _ablakban(_lap(panel))
    for index, node in enumerate(_csomopontok(controller)):
        elem = _child(panel, f"collageNode{index}")
        kozep_x, kozep_y = _kozeppont(elem)
        assert kozep_x == pytest.approx(lap_x + node.center_x * egyseg, abs=1.0)
        assert kozep_y == pytest.approx(lap_y + node.center_y * egyseg, abs=1.0)
        assert elem.width() == pytest.approx(node.width * egyseg, abs=1.0)
        assert elem.height() == pytest.approx(node.height * egyseg, abs=1.0)


def test_a_vaszon_ugyanoda_rajzol_mint_a_mentes(controller):
    """A vásznon látott elrendezés = a `render_nodes` elrendezése (jegy 1/8).

    Nem képpont-összevetés: a `nodes.sheet_to_pixels` UGYANAZT az osztót
    adja, amit a vászonnak használnia kell. Ha a kettő elválik, a WYSIWYG
    hazudik — pontosan az a hiba, ami miatt a `render_nodes` megszületett."""
    from picasapy.collage.nodes import sheet_to_pixels

    panel = _panel(controller)
    lap = _lap(panel)
    lap_szelesseg = round(lap.width())
    lap_x, lap_y, _, _ = _ablakban(lap)
    for index, node in enumerate(_csomopontok(controller)):
        elem = _child(panel, f"collageNode{index}")
        kozep_x, kozep_y = _kozeppont(elem)
        assert kozep_x == pytest.approx(
            lap_x + sheet_to_pixels(node.center_x, lap_szelesseg), abs=1.5
        )
        assert kozep_y == pytest.approx(
            lap_y + sheet_to_pixels(node.center_y, lap_szelesseg), abs=1.5
        )


def test_a_forgatas_a_csomopont_kozepe_korul_tortenik(controller):
    """A `theta` a doboz KÖZEPE körül forgat — a középpont nem vándorol."""
    panel = _panel(controller)
    elem = _child(panel, "collageNode0")
    elotte = _kozeppont(elem)
    controller.transformNode(0, 1.0, math.radians(30.0))
    qt_app = QGuiApplication.instance()
    qt_app.processEvents()
    assert elem.rotation() == pytest.approx(30.0, abs=0.01)
    utana = _kozeppont(elem)
    assert utana[0] == pytest.approx(elotte[0], abs=1.0)
    assert utana[1] == pytest.approx(elotte[1], abs=1.0)


# --- 2. A gyűrű --------------------------------------------------------------


def test_a_gyuru_csak_kijeloleskor_latszik(controller):
    """Kijelölés nélkül nincs gyűrű; a kijelöltre kerül (spec 7.1)."""
    panel = _panel(controller)
    assert not _child(panel, "collageRing0").isVisible()
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()
    assert _child(panel, "collageRing0").isVisible()
    assert not _child(panel, "collageRing1").isVisible()


def test_a_gyuru_132x132_es_a_csomopont_kozepen_ul(controller):
    """`#ring` 132 × 132, a befoglaló téglalap közepén (spec 7.2)."""
    panel = _panel(controller)
    controller.setCollageSelection([1])
    QGuiApplication.instance().processEvents()
    gyuru = _child(panel, "collageRing1")
    assert (gyuru.width(), gyuru.height()) == (GYURU, GYURU)
    gyuru_kozep = _kozeppont(gyuru)
    node_kozep = _kozeppont(_child(panel, "collageNode1"))
    assert gyuru_kozep[0] == pytest.approx(node_kozep[0], abs=1.0)
    assert gyuru_kozep[1] == pytest.approx(node_kozep[1], abs=1.0)


def test_a_gyuru_merete_kepernyo_egysegben_allando(controller):
    """A gyűrű NEM méreteződik a képpel (spec 7.2) — 132 marad."""
    panel = _panel(controller)
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()
    controller.transformNode(0, 2.5, 0.0)
    QGuiApplication.instance().processEvents()
    gyuru = _child(panel, "collageRing0")
    assert (gyuru.width(), gyuru.height()) == (GYURU, GYURU)


def test_a_racs_temaban_nincs_gyuru(controller):
    """A képesség-maszk szerint a gyűrű CSAK a Képkupacé (spec 5.)."""
    panel = _panel(controller)
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()
    assert controller.collageTheme == PICTUREPILE
    assert _child(panel, "collageRing0").isVisible()

    controller.setCollageTheme(REGULARGRID)
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()
    assert not _child(panel, "collageRing0").isVisible()


def test_a_gyuru_belseje_mozgat_es_nem_forgat(controller):
    """A gyűrű BELSEJE mozgat (`RingMoveHandler`), a pereme forgat (spec 7.2).

    A gyűrű a kijelölt kép közepén ül, tehát a kép közepét ELTAKARJA: ha a
    belseje nem mozgatna, a felhasználó a saját képe közepénél fogva nem
    tudná odébb tenni. A forgatásnak viszont itt tilos elindulnia — az a
    perem dolga."""
    panel = _panel(controller)
    view = panel.property("_view")
    egyseg = _egyseg(panel)
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()

    elotte = _csomopontok(controller)[0]
    kozep_x, kozep_y = _kozeppont(_child(panel, "collageRing0"))
    kezdo = QPoint(round(kozep_x), round(kozep_y))
    cel = QPoint(kezdo.x() + 24, kezdo.y() + 18)
    _eger_le(view, kezdo)
    _eger_mozog(view, cel)
    _eger_fel(view, cel)

    utana = _csomopontok(controller)[0]
    assert utana.center_x == pytest.approx(elotte.center_x + 24 / egyseg, abs=1.5)
    assert utana.center_y == pytest.approx(elotte.center_y + 18 / egyseg, abs=1.5)
    assert utana.theta == elotte.theta, "a gyűrű belseje NEM forgat"


# --- 3. A gyűrű matematikája (spec 7.4) --------------------------------------


def _fogantyu_pont(panel, index: int, irany: str) -> QPoint:
    """A gyűrű PEREMÉN egy pont az adott irányban (12 / 3 / 6 / 9 óra)."""
    gyuru = _child(panel, f"collageRing{index}")
    kozep_x, kozep_y = _kozeppont(gyuru)
    sugar = 57  # a perem közepe: 48 (belső) és 66 (külső) között
    eltolas = {
        "12": (0, -sugar),
        "3": (sugar, 0),
        "6": (0, sugar),
        "9": (-sugar, 0),
    }[irany]
    return QPoint(round(kozep_x + eltolas[0]), round(kozep_y + eltolas[1]))


@pytest.mark.parametrize(
    ("irany", "vart_theta"),
    [("6", 0.0), ("3", -math.pi / 2), ("9", math.pi / 2), ("12", math.pi)],
)
def test_a_fogantyu_szoge_atan2_minusz_dx_dy(controller, irany, vart_theta):
    """`szög = atan2(−dx, dy)` — a 0° a 12 óra IRÁNYA (spec 7.4).

    A képlet a képernyő koordinátáiban él (az y lefelé nő), ezért a
    `theta = 0` állásban a fogantyú a gyűrű ALJÁN áll; oda húzva nincs
    forgatás. A 3 órára húzva `−π/2` a TÁROLT szög — a felhasználó
    ellenben `+90`-et lát, mert a kiírás negál (`angle_caption_degrees`)."""
    panel = _panel(controller)
    view = panel.property("_view")
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()

    kezdo = _fogantyu_pont(panel, 0, "6")
    cel = _fogantyu_pont(panel, 0, irany)
    _eger_le(view, kezdo)
    _eger_mozog(view, cel)
    _eger_fel(view, cel)

    kapott = _csomopontok(controller)[0].theta
    assert math.isclose(
        math.cos(kapott), math.cos(vart_theta), abs_tol=0.02
    ) and math.isclose(math.sin(kapott), math.sin(vart_theta), abs_tol=0.02)


def test_a_fogantyu_meretez_is(controller):
    """Egy fogantyú: alapesetben EGYSZERRE forgat és méretez (spec 7.4)."""
    panel = _panel(controller)
    view = panel.property("_view")
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()
    elotte = _csomopontok(controller)[0].width

    gyuru = _child(panel, "collageRing0")
    kozep_x, kozep_y = _kozeppont(gyuru)
    kezdo = QPoint(round(kozep_x), round(kozep_y + 57))
    cel = QPoint(round(kozep_x), round(kozep_y + 114))
    _eger_le(view, kezdo)
    _eger_mozog(view, cel)
    _eger_fel(view, cel)

    assert _csomopontok(controller)[0].width == pytest.approx(2.0 * elotte, rel=0.05)


def test_ctrl_kikapcsolja_a_forgatast(controller):
    """A `Ctrl` a FORGATÁST kapcsolja ki — a méretezés megy tovább."""
    panel = _panel(controller)
    view = panel.property("_view")
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()
    szeles_elotte = _csomopontok(controller)[0].width
    # #989: a Képkupac LEGYEZŐSEN dönti meg a képeket (`pile_rotation`),
    # tehát a kiinduló szög nem nulla — az állítás a VÁLTOZATLANSÁGRÓL szól
    szog_elotte = _csomopontok(controller)[0].theta

    gyuru = _child(panel, "collageRing0")
    kozep_x, kozep_y = _kozeppont(gyuru)
    kezdo = QPoint(round(kozep_x), round(kozep_y + 57))
    cel = QPoint(round(kozep_x + 114), round(kozep_y))
    _eger_le(view, kezdo)
    _eger_mozog(view, cel, Qt.KeyboardModifier.ControlModifier)
    _eger_fel(view, cel, Qt.KeyboardModifier.ControlModifier)

    node = _csomopontok(controller)[0]
    assert node.theta == pytest.approx(szog_elotte, abs=1e-6)
    assert node.width == pytest.approx(2.0 * szeles_elotte, rel=0.05)


def test_alt_kikapcsolja_a_meretezest(controller):
    """Az `Alt` a MÉRETEZÉST kapcsolja ki — a forgatás megy tovább."""
    panel = _panel(controller)
    view = panel.property("_view")
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()
    szeles_elotte = _csomopontok(controller)[0].width

    gyuru = _child(panel, "collageRing0")
    kozep_x, kozep_y = _kozeppont(gyuru)
    kezdo = QPoint(round(kozep_x), round(kozep_y + 57))
    cel = QPoint(round(kozep_x + 114), round(kozep_y))
    _eger_le(view, kezdo)
    _eger_mozog(view, cel, Qt.KeyboardModifier.AltModifier)
    _eger_fel(view, cel, Qt.KeyboardModifier.AltModifier)

    node = _csomopontok(controller)[0]
    assert node.width == pytest.approx(szeles_elotte, rel=1e-6)
    assert node.theta == pytest.approx(-math.pi / 2, abs=0.02)


def test_ctrl_es_alt_egyutt_semmit_nem_csinal(controller):
    """„Mindkettőt nyomva tartva a fogantyú nem csinál semmit" (spec 7.4)."""
    panel = _panel(controller)
    view = panel.property("_view")
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()
    elotte = _csomopontok(controller)[0]

    gyuru = _child(panel, "collageRing0")
    kozep_x, kozep_y = _kozeppont(gyuru)
    kezdo = QPoint(round(kozep_x), round(kozep_y + 57))
    cel = QPoint(round(kozep_x + 114), round(kozep_y))
    mindketto = (
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier
    )
    _eger_le(view, kezdo)
    _eger_mozog(view, cel, mindketto)
    _eger_fel(view, cel, mindketto)

    utana = _csomopontok(controller)[0]
    assert utana.theta == pytest.approx(elotte.theta, abs=1e-9)
    assert utana.width == pytest.approx(elotte.width, rel=1e-9)


def test_a_modositot_a_huzas_KOZBEN_kerdezzuk(controller):
    """⚠️ A spec 7.4 legkönnyebben elrontható sora.

    Aki a `Ctrl`-t a LENYOMÁSKOR menti el, más programot ír: a Picasa
    `GetAsyncKeyState`-tel a pillanatnyi állást kérdezi. A teszt módosító
    NÉLKÜL nyom le, `Ctrl`-lel mozdít (nem forgathat), majd `Ctrl` nélkül
    mozdít újra (innentől forgat)."""
    panel = _panel(controller)
    view = panel.property("_view")
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()

    gyuru = _child(panel, "collageRing0")
    kozep_x, kozep_y = _kozeppont(gyuru)
    kezdo = QPoint(round(kozep_x), round(kozep_y + 57))
    jobbra = QPoint(round(kozep_x + 57), round(kozep_y))
    # #989: a kupac kiinduló szöge nem nulla (`pile_rotation`)
    szog_elotte = _csomopontok(controller)[0].theta

    _eger_le(view, kezdo)
    _eger_mozog(view, jobbra, Qt.KeyboardModifier.ControlModifier)
    assert _csomopontok(controller)[0].theta == pytest.approx(
        szog_elotte, abs=1e-6
    ), "a Ctrl-lel megtett mozdulat NEM forgathat"

    _eger_mozog(view, jobbra)
    assert _csomopontok(controller)[0].theta == pytest.approx(
        -math.pi / 2, abs=0.02
    ), "a Ctrl elengedése után a forgatás azonnal él"
    _eger_fel(view, jobbra)


# --- 4. A visszajelző feliratok (spec 7.4) -----------------------------------


def test_a_visszajelzes_lenyomaskor_jelenik_meg_es_100_szazalek(controller):
    """„Méretarány: %1%" a lenyomás pillanatában **100** (spec 7.4)."""
    panel = _panel(controller)
    view = panel.property("_view")
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()

    szog = _child(panel, "collageAngleText")
    meret = _child(panel, "collageScaleText")
    assert not szog.isVisible() and not meret.isVisible()

    kezdo = _fogantyu_pont(panel, 0, "6")
    _eger_le(view, kezdo)
    assert szog.isVisible() and meret.isVisible()
    assert "100" in meret.property("text")
    _eger_fel(view, kezdo)
    assert not szog.isVisible() and not meret.isVisible()


def test_a_szogfelirat_a_kesz_fuggvenyt_hasznalja_elojelvaltassal(controller):
    """A kiírt szög a `canvas.angle_caption_degrees` értéke — NEGÁLVA.

    ⚠️ #921: a Picasa a kiírás előtt előjelet vált. A 3 órára húzott
    fogantyú `−90` radiánt tárol, de a felhasználó `90`-et lát."""
    panel = _panel(controller)
    view = panel.property("_view")
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()

    kezdo = _fogantyu_pont(panel, 0, "6")
    cel = _fogantyu_pont(panel, 0, "3")
    _eger_le(view, kezdo)
    _eger_mozog(view, cel)

    varhato = angle_caption_degrees(_csomopontok(controller)[0].theta)
    assert varhato == 90
    assert str(varhato) in _child(panel, "collageAngleText").property("text")
    _eger_fel(view, cel)


def test_a_meretarany_felirat_a_kesz_fuggvenyt_hasznalja(controller):
    """A kiírt méretarány a `canvas.scale_caption_percent` értéke."""
    panel = _panel(controller)
    view = panel.property("_view")
    controller.setCollageSelection([0])
    QGuiApplication.instance().processEvents()

    gyuru = _child(panel, "collageRing0")
    kozep_x, kozep_y = _kozeppont(gyuru)
    kezdo = QPoint(round(kozep_x), round(kozep_y + 57))
    cel = QPoint(round(kozep_x), round(kozep_y + 114))
    _eger_le(view, kezdo)
    _eger_mozog(view, cel)

    # ⚠️ Az egéresemény EGÉSZ képpontra kerekít, a gyűrű közepe viszont
    # törtszám — a két táv aránya ezért nem pontosan 2,0, és egy beégetett
    # „200" a kerekítésen múlna, nem a megvalósításon. Az arányt tehát a
    # ténylegesen elküldött pontokból mérjük, a százalékot pedig a KÉSZ
    # formázó adja: az őr így is elbukik, ha a felület maga számolna.
    elso = math.hypot(kezdo.x() - kozep_x, kezdo.y() - kozep_y)
    masodik = math.hypot(cel.x() - kozep_x, cel.y() - kozep_y)
    assert str(scale_caption_percent(masodik / elso, 1.0)) in _child(
        panel, "collageScaleText"
    ).property("text")
    _eger_fel(view, cel)


