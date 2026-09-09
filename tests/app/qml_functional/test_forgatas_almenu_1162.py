r"""A Forgatás-almenü csak a forgatást TÁMOGATÓ témákon aktív (#1162).

## Miért nyílt ez a jegy, és mi lett a válasza

A #1151 (Keret-almenü) javításakor előkerült egy hasonló eset, amit
szándékosan nem javítottunk: a képesség-maszk `rotate` bitje **állítólag** a
szabad (tetszőleges szögű) forgatásra vonatkozik, a jobbklikk-menü viszont
FIX szögeket (0/90/180/270) kínál. Ha a kettő NEM ugyanaz, a menüt nem
szabad a bit szerint tiltani.

**A javítást most nem ez dönti el, hanem a BELSŐ ELLENTMONDÁS.** A mai
kódban ugyanaz a művelet két belépési ponton érhető el, és a kettő NEM
egyezik:

| belépési pont | gátolt-e |
|---|---|
| a bepattintó gombsor (`CollageSnapColumn.qml`) | **igen** (`capabilities.rotate`) |
| a jobbklikk Forgatás-almenüje | **nem** volt |

És a vezérlő maga is a bitet nézi: a `snapRotation` **némán visszatér**
(`collage_controller.py`), ha a téma nem forgat. A menütételek tehát azon az
öt témán, ahol a bit 0, egy néma no-opot ajánlottak — pontosan a #1151
osztálya („a felhasználó egy menütételt kapott, ami némán nem csinál
semmit").

⚠️ **Ez a javítás NEM változtat a program viselkedésén**, csak láthatóvá
teszi a meglévőt: a szürke tétel megmondja, hogy a funkció létezik, csak nem
ehhez a témához. Tiltás és nem elrejtés — a #1151 döntését követve; hogy az
eredeti rejt vagy tilt, **nincs kimérve**.

## A bináris kérdés MARAD, és a jegyben áll

A maszk 7. bitjéről a spec „erős" fokozatot ad. A #1162 körében mért új
adat: a bit által kapuzott blokk (`0x0083ad5f`) az elem **lebegőpontos**
mezőjét (`[esi+0x168]`) olvassa, és 0,1/0,15-es arányokkal számol —
folytonos szögre utal, nem negyedfordulatra. Ez azonban **nem bizonyíték**
(a mező írói nincsenek azonosítva), ezért a mai viselkedés marad.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject
from PySide6.QtGui import QGuiApplication

from support.collage_canvas_harness import (
    _panel,
    keszits_kepeket,
    nyitott_vezerlo,
)

#: A forgatást TÁMOGATÓ témák (a maszk 7. bitje 1) és a többi — a
#: `themes.capabilities_for` szerint, nem feltevésből.
FORGATOS = ("picturepile",)
FORGATAS_NELKULI = (
    "contactsheet",
    "framegrid",
    "multiexp",
    "picturegrid",
    "regulargrid",
)


@pytest.fixture
def library(tmp_path):
    return keszits_kepeket(tmp_path)


@pytest.fixture
def controller(qt_app, tmp_path, library):
    yield from nyitott_vezerlo(tmp_path, library)


def _forgatas_almenu(panel):
    menu = panel.findChild(QObject, "collageMenuAlignRotation")
    assert menu is not None, "nincs Forgatás-almenü"
    return menu


def _csoport_forgatas_almenu(panel):
    menu = panel.findChild(QObject, "collageGroupMenuAlignRotation")
    assert menu is not None, "nincs csoportos Forgatás-almenü"
    return menu


class TestATiltas:
    @pytest.mark.parametrize("tema", FORGATAS_NELKULI)
    def test_a_forgatast_nem_tamogato_teman_TILTOTT(self, controller, tema):
        controller.setCollageTheme(tema)
        panel = _panel(controller)
        QGuiApplication.instance().processEvents()

        assert _forgatas_almenu(panel).property("enabled") is False, (
            f"a Forgatás-almenü aktív a(z) {tema} témán, pedig a `snapRotation` "
            "ott némán visszatér — a tétel no-opot ajánl"
        )

    @pytest.mark.parametrize("tema", FORGATOS)
    def test_a_forgato_temakon_AKTIV(self, controller, tema):
        controller.setCollageTheme(tema)
        panel = _panel(controller)
        QGuiApplication.instance().processEvents()

        assert _forgatas_almenu(panel).property("enabled") is True


class TestACsoportosMenuIsGatolt:
    """A több kijelölt képre nyíló menüben ugyanez az almenü áll — a
    gátolásnak ott is látszania kell, különben a hiba egy másik belépési
    ponton visszatér (#1151 tanulsága: MINDEN belépési pontot végig kell nézni)."""

    def test_a_csoportos_almenu_is_tiltott(self, controller):
        controller.setCollageTheme("regulargrid")
        panel = _panel(controller)
        QGuiApplication.instance().processEvents()

        assert _csoport_forgatas_almenu(panel).property("enabled") is False

    def test_a_csoportos_almenu_forgato_teman_aktiv(self, controller):
        controller.setCollageTheme("picturepile")
        panel = _panel(controller)
        QGuiApplication.instance().processEvents()

        assert _csoport_forgatas_almenu(panel).property("enabled") is True


class TestABelsoEgyezes:
    """A menü gátolása a VEZÉRLŐ szabályát kövesse, ne egy másolt listát.

    A `snapRotation` egyetlen helyen dönt (`_capabilities().rotate`); ha a
    menü egy kézzel írt téma-listát nézne, a kettő idővel elcsúszna. Ez a
    próba minden témára összeveti a menü állapotát a vezérlő képességével —
    így egy ÚJ téma felvétele sem tudja némán megbontani az egyezést.
    """

    @pytest.mark.parametrize("tema", FORGATOS + FORGATAS_NELKULI)
    def test_a_menu_a_vezerlo_kepesseget_koveti(self, controller, tema):
        controller.setCollageTheme(tema)
        panel = _panel(controller)
        QGuiApplication.instance().processEvents()

        kepessegek = controller.property("collageCapabilities")
        assert kepessegek is not None, "nincs képesség-térkép a vezérlőn"
        elvart = bool(kepessegek["rotate"])
        assert _forgatas_almenu(panel).property("enabled") is elvart, (
            f"{tema}: a menü és a vezérlő `rotate` képessége eltér — a "
            "`snapRotation` némán visszatérne, a menü mégis kínálná"
        )
        assert _csoport_forgatas_almenu(panel).property("enabled") is elvart
