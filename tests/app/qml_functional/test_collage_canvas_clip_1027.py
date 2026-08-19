"""A vászon VÁGÁSA — `previewclip` (#1027).

Spec: `docs/specs/kollazs-panel-ui-spec.md` **2.3**; a forrás a
`referencia/tre-eroforrasok/collagepanel.tre` 160–170. és 238–250. sora.

## Miért a vászonkeretnél vág, és nem a lapnál

A `.tre` láncolata:

```
collagepanel/previewclip:     collagepanel/previewcontainer   ; 0,0,0,0 — a
                                                                TELJES keret
collagepanel/previewinset:    collagepanel/previewclip        ; −(12,35,12,35)
collagepanel/previewshadow:   collagepanel/previewinset       ; A LAP
collagepanel/previewroot:     collagepanel/previewinset       ; a CSOMÓPONTOK
```

Két dolog olvasható ki belőle, és mindkettő a vágás HELYÉRŐL szól:

1. a `previewroot` — amiben a képek ülnek — **a lap TESTVÉRE**, nem a
   gyereke; a lap tehát nem is tudná elvágni őket;
2. a `previewclip` geometriailag **azonos** a `previewcontainer`-rel
   (mind a négy élen 0). Egy azonos méretű, külön elem egyetlen dolog
   miatt létezik: **ez a vágás határa** — és ez a vászonkeret, nem a lap.

Aki a LAPNÁL vágna, a `previewinset` 12/35 képpontos sávját is levágná,
és mást mutatna, mint az eredeti.

## A négy lebegő gombcsoport

Nálunk a négy csoport nem a lap gyereke, hanem a vászon gyereke, a lap
téglalapjából számolva (ld. `CollageCanvas.qml`). A vágó konténer ezért
**csak a lapot** veszi körül: a gombcsoportok kívül maradnak, tehát a
vágás elvi lehetőséggel sem tudja megcsonkítani őket.

Ez tudatos, a felhasználó JAVÁRA szóló eltérés az eredetitől: ott a négy
csoport a `previewshadow` gyereke, tehát a `previewclip`-en belül van, és
800 × 534-es panelen a bal oldali oszlop 7 képponttal valóban ki is lóg
belőle. A 3. és az 5. teszt pontosan ezt a regressziót őrzi.
"""

from __future__ import annotations

import time

import numpy as np
import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem

from support.collage_canvas_harness import (
    _ablakban,
    _child,
    _lap,
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


#: A vágó konténer neve — a `.tre` `previewclip`-jének megfelelője.
VAGO = "collageSheetClip"

#: A négy lebegő gombcsoport (#948).
CSOPORTOK = (
    "collageActionRow",
    "collageRandomRow",
    "collageSnapColumn",
    "collageZOrderColumn",
)


# --------------------------------------------------------------------------
# Kiszolgáló
# --------------------------------------------------------------------------


def _var(korok=4):
    """Eseménypörgetés — az elrendezés és a miniatűrök sem állnak elő
    azonnal (#985/#987)."""
    for _ in range(korok):
        QGuiApplication.processEvents()
        szunet = QEventLoop()
        QTimer.singleShot(20, szunet.quit)
        szunet.exec()


def _keppontok(view) -> np.ndarray:
    """Az ablak VÖRÖS csatornája `float32` tömbként (a #1021 mintájára).

    Egy csatorna elég: a kérdés nem az, milyen SZÍNŰ egy képpont, hanem
    hogy MEGVÁLTOZOTT-e — és így a mérés színtértől független marad."""
    kep = view.grabWindow()
    assert not kep.isNull(), "az ablakot nem lehetett kirajzolni"
    magas, szeles = kep.height(), kep.width()
    return np.array(
        [[kep.pixelColor(x, y).red() for x in range(szeles)] for y in range(magas)],
        dtype=np.float32,
    )


def _stabil_kep(view, hatarido=8.0) -> np.ndarray:
    """Kirajzolt kép, ami két egymás utáni méréskor MÁR NEM változik.

    Fejnélküli módban az elrendezés és a miniatűrök késve érkeznek
    (#985/#987): beégetett várakozás helyett HATÁRIDŐS figyelés kell,
    különben a mérés a még be nem állt képet hasonlítaná össze."""
    kezdet = time.monotonic()
    elozo = None
    while time.monotonic() - kezdet < hatarido:
        _var()
        mostani = _keppontok(view)
        if elozo is not None and np.array_equal(elozo, mostani):
            return mostani
        elozo = mostani
    raise AssertionError("a kirajzolt kép nem állt be a határidőn belül")


def _oseik(item: QQuickItem, gyoker: QQuickItem):
    """Az elem ősei a gyökérig, magát a gyökeret is beleértve."""
    szulo = item.parentItem()
    while szulo is not None:
        yield szulo
        if szulo is gyoker:
            return
        szulo = szulo.parentItem()


def _vag(item: QQuickItem) -> bool:
    return bool(item.property("clip"))


def _egesz_doboz(item: QQuickItem) -> tuple[int, int, int, int]:
    """Az elem doboza az ablakban, egészre kerekítve: (x0, y0, x1, y1)."""
    x, y, w, h = _ablakban(item)
    return (round(x), round(y), round(x + w), round(y + h))


def _lapegysegben(panel: QQuickItem, x: float, y: float) -> tuple[float, float]:
    """Ablak-koordináta → LAPEGYSÉG (spec 6.1: mindkét tengelyen ugyanaz
    az osztó). Így a teszt célpontja a mért geometriából jön, nem
    beégetett számokból."""
    lap = _lap(panel)
    egyseg = lap.width() / 1024.0
    sarok = lap.mapToScene(lap.boundingRect().topLeft())
    return ((x - sarok.x()) / egyseg, (y - sarok.y()) / egyseg)


def _kivul_valtozott(alap: np.ndarray, uj: np.ndarray, doboz) -> int:
    """Hány képpont változott a megadott dobozon KÍVÜL."""
    x0, y0, x1, y1 = doboz
    kulonbseg = np.abs(alap - uj) > 0.5
    kulonbseg[max(0, y0) : max(0, y1), max(0, x0) : max(0, x1)] = False
    return int(kulonbseg.sum())


def _belul_valtozott(alap: np.ndarray, uj: np.ndarray, doboz) -> int:
    x0, y0, x1, y1 = doboz
    kulonbseg = np.abs(alap - uj) > 0.5
    return int(kulonbseg[max(0, y0) : max(0, y1), max(0, x0) : max(0, x1)].sum())


# --------------------------------------------------------------------------
# 1. A vágó konténer LÉTEZIK, és a vászonkeret téglalapját kapja
# --------------------------------------------------------------------------


@pytest.mark.parametrize("meret", [(800, 534), (1280, 800)])
def test_a_vago_a_LAP_teglalapjat_kapja(controller, meret):
    """A vágó a LAP téglalapja — nem a vászonkereté.

    ⚠️ EZ AZ ÁLLÍTÁS MEGFORDULT, és a megfordítás a lényeg. Az első
    változat azt követelte, hogy a vágó a VÁSZONKERETTEL legyen azonos
    (`previewclip = previewcontainer`), és zölden őrizte ezt — miközben a
    felhasználó azt látta, hogy **a képek továbbra is kilógnak**.

    Mindkettő igaz volt egyszerre: a csempe a vászonkereten belül maradt
    (tehát a teszt átment), de a LAPON kívülre csúszott — és a felhasználó
    a lap színes szélét nézi, nem a vászonkeretet. A teszt a kód
    értelmezését rögzítette, nem azt, amit a képernyőn látni.

    A négy lebegő gombcsoport ettől nem sérül: azok a vágó TESTVÉREI, nem
    a gyerekei."""
    panel = _panel(controller, *meret)
    _var()
    lap = _child(panel, "collageSheet")
    vago = _child(panel, VAGO)

    assert _vag(vago), f"a(z) {VAGO} nem vág — a képek kilógnak a lapból"
    assert _ablakban(vago) == _ablakban(lap), (
        "a vágó téglalapja nem a LAPÉ — a lapon kívülre csúszott csempe "
        "nem vágódik el, és a felhasználó ezt látja kilógó képként"
    )


def test_a_lap_es_a_csomopontok_a_vago_konteneren_belul_ulnek(controller):
    """A lapnak (és vele a csomópontoknak) a vágón BELÜL kell lennie —
    különben a `clip: true` semmit nem vág el."""
    panel = _panel(controller)
    _var()
    vago = _child(panel, VAGO)
    assert vago in list(_oseik(_lap(panel), panel)), (
        "a lap nincs a vágó konténerben — a vágás nem hat a csomópontokra"
    )


# --------------------------------------------------------------------------
# 2. A négy gombcsoport SÉRTETLEN — a legvalószínűbb regresszió
# --------------------------------------------------------------------------


@pytest.mark.parametrize("csoport", CSOPORTOK)
def test_a_gombcsoportoknak_nincs_egyetlen_vago_osuk_sem(controller, csoport):
    """A vágást a lap köré kell tenni, NEM a vászon gyökerére.

    Ha valaki a `CollageCanvas` gyökerére írja a `clip: true`-t, a négy
    csoport is a vágón belülre kerül — és 800 × 534-es panelen a bal
    oldali oszlop 7 képponttal ki is lóg a keretből, tehát tényleg
    megcsonkulna. Ez a teszt azt zárja ki, hogy a vágás egyáltalán
    ELÉRHESSE őket."""
    panel = _panel(controller)
    controller.selectAllNodes()
    _var()
    osok = _oseik(_child(panel, csoport), panel)
    vagok = [o.objectName() or "<névtelen>" for o in osok if _vag(o)]
    assert vagok == [], f"a(z) {csoport} vágó ős(ök) alatt ül: {vagok}"


def test_a_bal_oldali_oszlop_a_kereten_kivuli_savja_is_kirajzolodik(controller):
    """A KIRAJZOLT bizonyíték a gombcsoportok sértetlenségére.

    800 × 534-es panelen a lap a `previewinset` teljes SZÉLESSÉGÉT
    kitölti, tehát a bal széle a keret bal szélétől 12 képpontra van — a
    17 képpont széles oszlop pedig 2 képpont réssel elé kerül, azaz
    7 képponttal a vászonkereten KÍVÜLRE. Ha a vágás rossz szinten
    kerülne be, pont ez a sáv tűnne el."""
    panel = _panel(controller, 800, 534)
    view = panel.property("_view")
    controller.selectNoNodes()
    _var()
    kijeloles_nelkul = _stabil_kep(view)

    vaszon_x0 = _egesz_doboz(_child(panel, "collageCanvas"))[0]
    o_x0, o_y0, _, o_y1 = _egesz_doboz(_child(panel, "collageSnapColumn"))
    # Az őr csak akkor ér valamit, ha a helyzet tényleg elő is áll.
    assert o_x0 < vaszon_x0, (
        "a bal oldali oszlop nem lóg ki a vászonkeretből — a teszt nem mér semmit"
    )

    controller.setCollageSelection([0])
    _var()
    kijelolessel = _stabil_kep(view)

    sav = (o_x0, o_y0, vaszon_x0, o_y1)
    assert _belul_valtozott(kijeloles_nelkul, kijelolessel, sav) > 0, (
        "a bal oldali oszlopnak a vászonkereten kívülre eső sávja nem "
        "rajzolódott ki — a vágás elvágta a gombcsoportot"
    )


# --------------------------------------------------------------------------
# 3. A KIRAJZOLT bizonyíték: a lapról kilógó kép nem megy a kereten túlra
# --------------------------------------------------------------------------


def test_a_lapon_kivulre_tolt_csomopont_nem_rajzol_a_vaszonkereten_kivul(controller):
    """A felhasználó panasza, mérve: a képek nem csúszhatnak a panelre.

    A mérés KÜLÖNBSÉG-alapú, tehát nincs benne beégetett képpontérték és
    beégetett szín sem: kirajzoljuk a panelt az alap-elrendezéssel, majd
    a csomópontokat messze a lapon KÍVÜLRE toljuk. Ami ettől a
    vászonkereten kívül megváltozik, az a hiba maga."""
    panel = _panel(controller, 1280, 800)
    view = panel.property("_view")
    _var()
    alap = _stabil_kep(view)

    vaszon = _egesz_doboz(_child(panel, "collageCanvas"))
    # A célpont a BAL HASÁB közepe: az ablakon belül van (különben a mérés
    # semmit nem mutatna), a vászonkereten viszont kívül — pontosan oda,
    # ahova a felhasználó szerint a képek ma becsúsznak.
    hasab = _egesz_doboz(_child(panel, "collageTabBase"))
    cel_x = (hasab[0] + hasab[2]) / 2
    cel_y = (hasab[1] + hasab[3]) / 2
    for i in range(controller.collageClipCount):
        controller.moveNode(i, *_lapegysegben(panel, cel_x, cel_y))
    _var()
    kitolva = _stabil_kep(view)

    # Az őrnek FOGA van: ha a tolás semmit nem mozdítana, a teszt akkor is
    # zöld lenne — ezért előbb kimondjuk, hogy a kép TÉNYLEG megváltozott.
    assert _belul_valtozott(alap, kitolva, vaszon) > 0, (
        "a csomópontok tolása semmit nem változtatott — a teszt nem mér semmit"
    )
    assert _kivul_valtozott(alap, kitolva, vaszon) == 0, (
        "a lapról kitolt csomópontok a vászonkereten KÍVÜL is rajzolnak — "
        "a kollázs képei a panelre csúsznak (#1027)"
    )
