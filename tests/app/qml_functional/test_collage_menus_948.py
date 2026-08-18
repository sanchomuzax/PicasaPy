"""A kollázs HÁROM helyi menüje, KIRAJZOLVA — #948 (2/2).

Spec: `docs/specs/kollazs-panel-ui-spec.md` **7.6**, a feliratok forrása a
`picasa-create-features.md` **1.10.6** és a `picasa-kollazs-felulet.md`
**6.** szakasza.

Három menü, a KIJELÖLÉS MÉRETE szerint: egy kijelölt kép (8 tétel), több
kijelölt kép (3 tétel), a vászon üres területe (4 tétel). Két almenü:
*Szegély módosítása* és *Forgatás igazítása*.

⚠️ Két csapda, amit ez a fájl őriz:

1. **Ugyanannak a parancsnak két felirata van** — a gombon „Véletlenszerű
   kollázs" (`Scramble Collage`), a menüben „Képek szétszórása"
   (`Scatter Pictures`). Nem elírás; aki „egységesíti", az eredetitől tér
   el.
2. **A „270 fok" a menü FELIRATA; a tárolt érték −90,0.** Aki a feliratot
   írja a `.cxf`-be, a windowsos Picasával elcsúszó fájlt ír.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest

from support.collage_canvas_harness import (
    _ablakban,
    _child,
    _kozeppont,
    _panel,
    keszits_kepeket,
    nyitott_vezerlo,
)


@pytest.fixture
def library(tmp_path):
    return keszits_kepeket(tmp_path)


@pytest.fixture
def controller(qt_app, tmp_path, library):
    yield from nyitott_vezerlo(tmp_path, library)


def _var():
    QGuiApplication.instance().processEvents()


def _menu(panel, nev):
    menu = panel.findChild(QObject, nev)
    assert menu is not None, f"{nev} nem található"
    return menu


def _tetelek(menu, vartak):
    """A menü tételei DEKLARÁCIÓS sorrendben (a `findChildren` bejárása)."""
    return [
        gyerek.objectName()
        for gyerek in menu.findChildren(QObject)
        if gyerek.objectName() in vartak
    ]


def _zar(panel, nev):
    QMetaObject.invokeMethod(
        _menu(panel, nev), "close", Qt.ConnectionType.DirectConnection
    )
    _var()


def _kivalt(panel, nev):
    """A MenuItem-nek nincs hívható `trigger()`-e — a `triggered` SIGNAL
    kiváltása futtatja az `onTriggered` kezelőt."""
    QMetaObject.invokeMethod(
        _menu(panel, nev), "triggered", Qt.ConnectionType.DirectConnection
    )
    _var()


def _jobb_klikk(panel, pont: QPoint):
    view = panel.property("_view")
    QTest.mousePress(
        view, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier, pont
    )
    QTest.mouseRelease(
        view, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier, pont
    )
    _var()


def _ures_pont(panel) -> QPoint:
    """A vászon bal-felső sarka — se lap, se gombsor nincs alatta."""
    x, y, _, _ = _ablakban(_child(panel, "collageCanvas"))
    return QPoint(round(x) + 3, round(y) + 3)


# a spec 7.6 tételsorai, SORRENDBEN
EGY_KEP = [
    "collageMenuRemove",
    "collageMenuSetBackground",
    "collageMenuSetFrameCenter",
    "collageMenuChangeBorder",
    "collageMenuAlignRotation",
    "collageMenuMoveTop",
    "collageMenuMoveBottom",
    "collageMenuViewAndEdit",
]
TOBB_KEP = [
    "collageGroupMenuRemove",
    "collageGroupMenuChangeBorder",
    "collageGroupMenuAlignRotation",
]
VASZON = [
    "collageCanvasMenuSelectAll",
    "collageCanvasMenuSelectNone",
    "collageCanvasMenuShuffle",
    "collageCanvasMenuScatter",
]


# --- 1. Melyik menü nyílik ki ------------------------------------------------


def test_egy_kijelolt_kepen_a_nyolc_teteles_menu_nyilik(controller):
    """Jobb gomb LE a kijelölt képen → `collagenode_context_single`."""
    panel = _panel(controller)
    controller.setCollageSelection([0])
    _var()
    _jobb_klikk(panel, QPoint(*(round(k) for k in _kozeppont(_child(panel, "collageNode0")))))

    assert _menu(panel, "collageNodeMenuSingle").property("visible") is True
    assert _menu(panel, "collageNodeMenuGroup").property("visible") is False
    assert _menu(panel, "collageCanvasMenu").property("visible") is False
    _zar(panel, "collageNodeMenuSingle")


def test_a_jobb_klikk_a_ki_nem_jelolt_kepet_kijeloli(controller):
    """A kijelöletlen képre jobb gombbal kattintva a kép KIJELÖLŐDIK — a
    menü parancsai különben egy másik képre hatnának, mint amelyikre a
    felhasználó kattintott."""
    panel = _panel(controller)
    controller.setCollageSelection([2])
    _var()
    _jobb_klikk(panel, QPoint(*(round(k) for k in _kozeppont(_child(panel, "collageNode0")))))

    assert list(controller.collageSelection) == [0]
    assert _menu(panel, "collageNodeMenuSingle").property("visible") is True
    _zar(panel, "collageNodeMenuSingle")


def test_tobb_kijelolt_kepnel_a_harom_teteles_menu_nyilik(controller):
    """A csoport-menü akkor jön, ha a MEGFOGOTT kép a kijelölés RÉSZE — a
    többes kijelölést a jobb gomb nem bontja szét."""
    panel = _panel(controller)
    controller.setCollageSelection([0, 1])
    _var()
    _jobb_klikk(panel, QPoint(*(round(k) for k in _kozeppont(_child(panel, "collageNode1")))))

    assert list(controller.collageSelection) == [0, 1]
    assert _menu(panel, "collageNodeMenuGroup").property("visible") is True
    assert _menu(panel, "collageNodeMenuSingle").property("visible") is False
    _zar(panel, "collageNodeMenuGroup")


def test_az_ures_teruleten_a_vaszon_menuje_nyilik(controller):
    """A vászon üres területén `collagenode_context_document`."""
    panel = _panel(controller)
    _var()
    _jobb_klikk(panel, _ures_pont(panel))

    assert _menu(panel, "collageCanvasMenu").property("visible") is True
    assert _menu(panel, "collageNodeMenuSingle").property("visible") is False
    _zar(panel, "collageCanvasMenu")


def test_a_vaszon_menuje_a_tobbszoros_exponalasnal_el_van_nyomva(controller):
    """A kezelő `multiexp`-nél MÁS ÁGRA ugrik: nem nyitja meg a menüt
    (`picasa-kollazs-felulet.md` 6.). A maszk 4. bitje ugyanezt mondja —
    két külön kódút, egyetlen szabály; nálunk a maszk a forrás."""
    panel = _panel(controller)
    controller.setCollageTheme("multiexp")
    _var()
    _jobb_klikk(panel, _ures_pont(panel))

    assert _menu(panel, "collageCanvasMenu").property("visible") is False


# --- 2. A tételsorok ---------------------------------------------------------


def test_az_egykepes_menu_nyolc_tetele_sorrendben(controller):
    panel = _panel(controller)
    controller.setCollageSelection([0])
    _var()
    assert _tetelek(_menu(panel, "collageNodeMenuSingle"), EGY_KEP) == EGY_KEP


def test_a_tobbkepes_menu_harom_tetele_sorrendben(controller):
    panel = _panel(controller)
    controller.setCollageSelection([0, 1])
    _var()
    assert _tetelek(_menu(panel, "collageNodeMenuGroup"), TOBB_KEP) == TOBB_KEP


def test_a_vaszon_menuje_negy_teteles(controller):
    panel = _panel(controller)
    _var()
    assert _tetelek(_menu(panel, "collageCanvasMenu"), VASZON) == VASZON


@pytest.mark.parametrize(
    "menu,tetelek",
    [
        ("collageNodeMenuSingle", EGY_KEP),
        ("collageNodeMenuGroup", TOBB_KEP),
        ("collageCanvasMenu", VASZON),
    ],
)
def test_egyik_menuben_sincs_tobb_tetel_a_specnel(controller, menu, tetelek):
    """A tételszám SZERZŐDÉS: aki „hasznos" parancsot vesz fel, más
    programot ír. A `count` a menü saját tételszáma (az almenük egy-egy
    tételnek számítanak)."""
    panel = _panel(controller)
    _var()
    assert _menu(panel, menu).property("count") == len(tetelek)


# --- 3. A két almenü ---------------------------------------------------------


def test_a_szegely_almenu_harom_tetele(controller):
    """Egyik sem · Fehér szegély · Polaroid fényképezőgép (`Border::
    ID_COLLAGE_BORDER_0/1/2`)."""
    panel = _panel(controller)
    _var()
    vart = [
        "collageMenuBorderNone",
        "collageMenuBorderWhite",
        "collageMenuBorderPolaroid",
    ]
    assert _tetelek(_menu(panel, "collageMenuChangeBorder"), vart) == vart
    assert _menu(panel, "collageMenuChangeBorder").property("count") == 3


def test_a_forgatas_almenu_negy_tetele(controller):
    """0 fok · 90 fok · 180 fok · 270 fok (`Rotate::ID_COLLAGE_ALIGN_*`)."""
    panel = _panel(controller)
    _var()
    vart = [
        "collageMenuAlign0",
        "collageMenuAlign90",
        "collageMenuAlign180",
        "collageMenuAlign270",
    ]
    assert _tetelek(_menu(panel, "collageMenuAlignRotation"), vart) == vart
    assert _menu(panel, "collageMenuAlignRotation").property("count") == 4


def test_a_270_fok_felirat_mogott_minusz_90_all(controller):
    """⚠️ A „270 fok" a menü FELIRATA; a tárolt érték **−90,0** — a `.cxf`-be
    −1,570796 kerül. Aki a feliratot tárolja, a windowsos Picasával
    elcsúszó fájlt ír."""
    panel = _panel(controller)
    controller.setCollageSelection([1])
    _var()
    _kivalt(panel, "collageMenuAlign270")

    assert controller.collageNodes.nodes[1].theta == pytest.approx(-math.pi / 2)


@pytest.mark.parametrize(
    "tetel,fok",
    [
        ("collageMenuAlign0", 0.0),
        ("collageMenuAlign90", 90.0),
        ("collageMenuAlign180", 180.0),
    ],
)
def test_a_tobbi_harom_igazitas_a_felirat_szerinti_szoget_tarolja(
    controller, tetel, fok
):
    panel = _panel(controller)
    controller.setCollageSelection([1])
    _var()
    _kivalt(panel, tetel)

    assert controller.collageNodes.nodes[1].theta == pytest.approx(math.radians(fok))


def test_a_szegely_almenu_a_kijeloltek_keretet_allitja(controller):
    panel = _panel(controller)
    controller.setCollageSelection([0])
    _var()
    _kivalt(panel, "collageMenuBorderPolaroid")

    assert controller.collageNodes.nodes[0].border == "polaroid"


# --- 4. A tételek a VEZÉRLŐT hívják ------------------------------------------


def test_az_egykepes_menu_parancsai_a_vezerlore_mennek(controller):
    panel = _panel(controller)
    controller.setCollageSelection([1])
    _var()

    _kivalt(panel, "collageMenuSetFrameCenter")
    assert controller.collageFrameCenter == 1

    _kivalt(panel, "collageMenuMoveTop")
    assert controller.collageNodes.nodes[-1].selected

    _kivalt(panel, "collageMenuMoveBottom")
    assert controller.collageNodes.nodes[0].selected

    _kivalt(panel, "collageMenuRemove")
    assert controller.collageClipCount == 2


def test_a_megjelenites_es_szerkesztes_a_szerkesztot_keri(controller):
    panel = _panel(controller)
    controller.setCollageSelection([2])
    _var()
    kertek = []
    controller.collageEditRequested.connect(kertek.append)

    _kivalt(panel, "collageMenuViewAndEdit")

    assert len(kertek) == 1
    assert kertek[0].endswith("c.jpg")


def test_a_vaszon_menuje_a_negy_parancsot_futtatja(controller):
    panel = _panel(controller)
    _var()

    _kivalt(panel, "collageCanvasMenuSelectAll")
    assert list(controller.collageSelection) == [0, 1, 2]

    _kivalt(panel, "collageCanvasMenuSelectNone")
    assert list(controller.collageSelection) == []

    elotte = [n.path for n in controller.collageNodes.nodes]
    kozepek = [(n.center_x, n.center_y) for n in controller.collageNodes.nodes]
    _kivalt(panel, "collageCanvasMenuShuffle")
    assert [n.path for n in controller.collageNodes.nodes] != elotte
    # a „Képek összekeverése" a KÉPEKET cseréli, a réseket nem
    assert [(n.center_x, n.center_y) for n in controller.collageNodes.nodes] == kozepek

    _kivalt(panel, "collageCanvasMenuScatter")
    assert [
        (n.center_x, n.center_y) for n in controller.collageNodes.nodes
    ] != kozepek


def test_a_csoport_menu_parancsai_minden_kijeloltre_hatnak(controller):
    panel = _panel(controller)
    controller.setCollageSelection([0, 1])
    _var()

    _kivalt(panel, "collageGroupMenuBorderWhite")
    keretek = [n.border for n in controller.collageNodes.nodes]
    assert keretek[0] == "whiteborder"
    assert keretek[1] == "whiteborder"

    _kivalt(panel, "collageGroupMenuAlign90")
    assert controller.collageNodes.nodes[0].theta == pytest.approx(math.pi / 2)
    assert controller.collageNodes.nodes[1].theta == pytest.approx(math.pi / 2)

    _kivalt(panel, "collageGroupMenuRemove")
    assert controller.collageClipCount == 1


# --- 5. A képesség-maszk a menüben is --------------------------------------


def test_a_vaszon_menujeben_a_ket_veletlen_parancs_a_maszkot_koveti(controller):
    """Az „Indexkép" témában sem összekeverés, sem szétszórás nincs — a
    tétel LÁTSZIK, de szürke (az eredeti szabálya: az inaktív tétel is
    tétel)."""
    panel = _panel(controller)
    _var()
    assert _menu(panel, "collageCanvasMenuShuffle").property("enabled") is True
    assert _menu(panel, "collageCanvasMenuScatter").property("enabled") is True

    controller.setCollageTheme("contactsheet")
    _var()
    assert _menu(panel, "collageCanvasMenuShuffle").property("enabled") is False
    assert _menu(panel, "collageCanvasMenuScatter").property("enabled") is False


# --- 6. A hivatalos magyar feliratok ----------------------------------------
#
# Az erőforrásbeli felirat nem bizonyíték arra, mit lát a felhasználó — de a
# fordítatlan felirat az: a `.ts`-ben rossz magyar szöveg NÉMÁN megy ki.
# A `test_i18n_completeness.py` csak azt őrzi, hogy VAN fordítás; azt, hogy
# a HIVATALOS magyar van benne, ez.

_TS = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "i18n" / "picasapy_hu.ts"
)

#: `picasa-create-features.md` 1.10.6 + `picasa-kollazs-felulet.md` 6.
_HIVATALOS_MAGYAR = {
    "Remove": "Eltávolítás",
    "Set as Background": "Beállítás háttérként",
    "Set as Frame Center": "Beállítás képkockaközéppontként",
    "Change Border": "Szegély módosítása",
    "Align Rotation": "Forgatás igazítása",
    "Bring to Top": "Legfelülre helyezés",
    "Move to Bottom": "Legalulra helyezés",
    "View and Edit": "Megjelenítés és szerkesztés",
    "Select All": "Az összes kijelölése",
    "Select None": "Az összes kijelölés megszüntetése",
    "Shuffle Pictures": "Képek összekeverése",
    # ⚠️ ugyanaz a parancs, mint a gombon — de a MENÜ felirata más
    "Scatter Pictures": "Képek szétszórása",
    "None": "Egyik sem",
    "White Border": "Fehér szegély",
    "Polaroid Camera": "Polaroid fényképezőgép",
    "0 Degrees": "0 fok",
    "90 Degrees": "90 fok",
    "180 Degrees": "180 fok",
    "270 Degrees": "270 fok",
}


def _forditasok(kontextus: str) -> dict[str, str]:
    gyoker = ET.parse(_TS).getroot()
    talalt: dict[str, str] = {}
    for ctx in gyoker.findall("context"):
        if (ctx.find("name").text or "") != kontextus:
            continue
        for msg in ctx.findall("message"):
            forras = msg.find("source").text
            forditas = msg.find("translation")
            if forditas is None or forditas.get("type") in ("unfinished", "vanished"):
                continue
            talalt[forras] = forditas.text
    return talalt


@pytest.mark.parametrize("angol,magyar", sorted(_HIVATALOS_MAGYAR.items()))
def test_a_menufeliratok_hivatalos_magyarral_szerepelnek_a_ts_ben(angol, magyar):
    forditasok = _forditasok("CollageContextMenus")
    assert forditasok.get(angol) == magyar


def test_a_ket_veletlen_parancs_felirata_szandekosan_kulonbozik():
    """A gombon „Véletlenszerű kollázs", a menüben „Képek szétszórása" —
    ugyanaz a `scrambleCollage()` slot, két erőforrás-szöveg. Aki
    egységesíti, az eredetitől tér el."""
    menu = _forditasok("CollageContextMenus")
    sor = _forditasok("CollageRandomRow")
    assert menu["Scatter Pictures"] == "Képek szétszórása"
    assert sor["Scramble Collage"] == "Véletlenszerű kollázs"
