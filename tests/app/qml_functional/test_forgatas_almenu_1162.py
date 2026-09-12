r"""A Forgatás-almenü MINDEN kollázs-témán aktív (#1162).

## A jegy kérdése, és a mért válasz

A #1151 (Keret-almenü) javításakor előkerült egy hasonló eset: a
képesség-maszk `rotate` bitje **állítólag** a szabad (tetszőleges szögű)
forgatásra vonatkozik, a jobbklikk-menü viszont FIX szögeket (0/90/180/270)
kínál. A jegy azt kérte, hogy ezt a binárisból kell eldönteni.

**Kimérve (2026-09-12), az eredeti `Picasa3.exe` 3.9.141.259-en:**

| kérdés | válasz | bizonyíték |
|---|---|---|
| hova fut a négy `collagepanel/snap_*` parancs? | `FUN_0083b900` | `0x0082e0f3`, `0x0082e171`, `0x0082e1ef`, `0x0082e26d` |
| milyen szöggel? | 0 · 90 · 180 · **−90** fok | `0xcf4370` = 90, `0xcf409c` = 180, `0xcf50d0` = −90 |
| hogyan tárolja? | `* pi/180`, az elem `+0x15c` mezőjébe | `0xcf3fc8` = 0,017453292519938 |
| nézi-e a képesség-maszkot? | **NEM** — a 341 bájtos függvényben nincs ilyen vizsgálat | `FUN_0083b900` teljes diszasszemblátuma |
| hol nézi bárki a 7. bitet? | a teljes `.text`-en **egy** helyen: `0x0083ad5f` | pásztázás minden `call <reg>` utáni bitvizsgálatra |
| mit kapuz az az egy hely? | egy `AnimPlacementHandler` létrehozását elemenként | vtábla `0x00cbfebc`, RTTI-név |
| mit animál az? | hely + **szög** + méret (`+0x15c`, `+0x168`) | `FUN_007f8d10` → `FUN_009dec60`/`FUN_009deca0` |

**Következtetés:** a 7. bit a téma SZABAD, szórásos elrendezését engedi (a
Képkupacnál), nem a fix igazítást. A jobbklikk-almenüt tehát nem szabad a
bit szerint tiltani — és a vezérlőnek sem szabad némán visszatérnie.

## Amit ez visszavon

A #1162 korábbi köre (PR #2788) a menüt a bit szerint GÁTOLTA, a vezérlő
akkori `snapRotation`-jához igazodva. A belső egyezés érve helyes volt, csak
a rögzítési pontot választotta rosszul: a vezérlő volt az, ami tévedett.
Most mind a három belépési pont — vezérlő, bepattintó gombsor, helyi menü —
a mért eredetit követi.

## Amit ez NEM állít

Nem méri, hogy az eredeti a nem forgató témákon MIT MUTAT a vásznon a
elforgatott csempéből; csak azt, hogy a parancs lefut és tárol. A vizuális
egyezéshez referencia-képernyőkép kellene.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject
from PySide6.QtGui import QGuiApplication

from support.collage_canvas_harness import (
    _child,
    _panel,
    keszits_kepeket,
    nyitott_vezerlo,
)

#: Mind a hat kollázs-téma — a forgatást „támogató" (a maszk 7. bitje 1) és
#: a többi egyaránt. A megkülönböztetés ezen a felületen megszűnt.
TEMAK = (
    "picturepile",
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


class TestAzAlmenuMindenTemanAktiv:
    @pytest.mark.parametrize("tema", TEMAK)
    def test_az_egyes_menu(self, controller, tema):
        controller.setCollageTheme(tema)
        panel = _panel(controller)
        QGuiApplication.instance().processEvents()

        assert _forgatas_almenu(panel).property("enabled") is True, (
            f"a Forgatás-almenü gátolt a(z) {tema} témán, pedig az eredeti "
            "végrehajtója (`FUN_0083b900`) nem nézi a képesség-maszkot"
        )

    @pytest.mark.parametrize("tema", TEMAK)
    def test_a_csoportos_menu(self, controller, tema):
        """A több kijelölt képre nyíló menüben ugyanez az almenü áll — a
        #1151 tanulsága szerint MINDEN belépési pontot végig kell nézni."""
        controller.setCollageTheme(tema)
        panel = _panel(controller)
        QGuiApplication.instance().processEvents()

        assert _csoport_forgatas_almenu(panel).property("enabled") is True


class TestABepattintoGombsorIsAktiv:
    """A harmadik belépési pont: a vászon bal szélén álló négy kis gomb.

    Ha csak a menüt oldanánk fel, ugyanaz a funkció két helyen más választ
    adna — pontosan az az ellentmondás, amiért a #1162 első köre a menüt
    gátolta.

    A `multiexp` kimarad: ott a `selection` képesség hiányzik, tehát az
    egész oszlop rejtett (spec 2.4, #948) — az a gátolás más kérdés, és
    ehhez a jegyhez nincs köze.
    """

    @pytest.mark.parametrize(
        "tema", [t for t in TEMAK if t != "multiexp"]
    )
    @pytest.mark.parametrize("gomb", ["collageSnap12", "collageSnap3"])
    def test_a_gomb_nem_gatolt(self, controller, tema, gomb):
        controller.setCollageTheme(tema)
        panel = _panel(controller)
        controller.selectAllNodes()
        QGuiApplication.instance().processEvents()

        elem = _child(panel, gomb)
        assert elem.property("enabled") is True, (
            f"{tema}: a(z) {gomb} gomb gátolt, pedig az eredeti "
            "végrehajtója nem nézi a képesség-maszkot"
        )
