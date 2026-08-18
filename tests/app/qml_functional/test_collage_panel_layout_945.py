"""A Kollázs-panel MÉRETEZÉSI TÖRVÉNYE, kirajzolva — #945.

Spec: `docs/specs/kollazs-panel-ui-spec.md` **2.** és **4.1**.

> **A bal hasáb FIX MÉRETŰ, a vászon-oldal NYÚLIK.**

Miért kirajzolt teszt: a property-t olvasó, komponenst izoláltan betöltő
ellenőrzés nem látja a szülő geometriáját, és nem látja azt sem, amit a
felhasználó lát (`PROTOKOLL.md`: „a KIMENETET ellenőrizd, ne a szándékot").
A #411-ben pontosan ez a hiba csúszott át egyszer már: egy fix szélességű
oldalpanelt valaki ablakarányosan skálázott, és a felhasználó
screenshot-összevetése bizonyította a hibát, nem a tesztkészlet.

Ezért a lap valódi `QQuickView`-ba tölt, HÁROM ablakméretnél, és az ABLAK
koordinátarendszerében kérdez.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Property, QObject, QPoint, Qt, QUrl, Slot
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

_KEEPALIVE: list[object] = []

#: A három mérce: a tervezővászon, egy tipikus laptop és egy teljes HD.
ABLAKMERETEK = [(800, 534), (1280, 800), (1920, 1080)]

#: A bal hasáb szélessége — a törvény lényege. Ez a szám SOHA nem függhet az
#: ablakmérettől.
HASAB_SZELESSEG = 276

#: A négy alsó gomb neve és tervezői helye a panel bal-felső sarkához mérve
#: (spec 2.6). Ezek is fixek: a `.tre` a FIX `tabbase` aljához köti őket.
ALSO_GOMBOK = {
    "collageMakeDesktopButton": (10, 415, 127, 28),
    "collageShareButton": (147, 415, 133, 28),
    "collageResetButton": (10, 448, 127, 28),
    "collageCloseButton": (147, 448, 133, 28),
}


class _CollageControllerStub(QObject):
    """Annyi a vezérlőből, amennyitől a panel geometriája megszületik.

    A `collagePageRatio` MAGASSÁG / SZÉLESSÉG (spec 8.1) — ebből él a lap
    alakja."""

    def __init__(self, page_ratio: float = 0.75, clip_count: int = 0) -> None:
        super().__init__()
        self._page_ratio = page_ratio
        self._clip_count = clip_count
        self.close_calls = 0

    @Slot()
    def closeCollage(self) -> None:
        self.close_calls += 1

    @Property(float, constant=True)
    def collagePageRatio(self) -> float:
        return self._page_ratio

    @Property(int, constant=True)
    def collageClipCount(self) -> int:
        return self._clip_count


def _panel(qt_app, width: int, height: int, *, page_ratio=0.75, clips=0):
    """A panel valódi ablakban, adott mérettel — a kötések lefuttatva."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)

    stub = _CollageControllerStub(page_ratio, clips)
    qml = """
import QtQuick
import PicasaPy 1.0
CollagePanel {
    objectName: "collagePanel"
}
"""
    component = QQmlComponent(view.engine())
    component.setData(qml.encode("utf-8"), QUrl())
    assert [e.toString() for e in component.errors()] == []
    root = component.create()
    assert root is not None
    root.setProperty("controller", stub)
    root.setParentItem(view.contentItem())
    view.resize(width, height)
    root.setWidth(width)
    root.setHeight(height)
    view.show()
    _KEEPALIVE.extend((view, root, stub, component))
    root.setProperty("_stub", stub)
    root.setProperty("_view", view)
    return root


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása — a `findChild` nem lát mindent (#651)."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _child(root: QQuickItem, name: str) -> QQuickItem:
    for item in _walk(root):
        if item.objectName() == name:
            return item
    found = root.findChild(QObject, name)
    assert found is not None, f"{name} nem található a kirajzolt fában"
    return found


def _ablakban(item: QQuickItem) -> tuple[float, float, float, float]:
    """Az elem doboza az ABLAK koordinátarendszerében (x, y, szél., mag.)."""
    bal_felso = item.mapToScene(item.boundingRect().topLeft())
    return (bal_felso.x(), bal_felso.y(), item.width(), item.height())


# --- 1. A törvény: a hasáb fix, a vászon nyúlik -----------------------------


@pytest.mark.parametrize("meret", ABLAKMERETEK)
def test_a_bal_hasab_szelessege_mindig_276(qt_app, meret):
    """A bal hasáb szélessége nem függhet az ablakmérettől (#411 precedens)."""
    panel = _panel(qt_app, *meret)
    _, _, szeles, _ = _ablakban(_child(panel, "collageTabBase"))
    assert szeles == HASAB_SZELESSEG


@pytest.mark.parametrize("meret", ABLAKMERETEK)
@pytest.mark.parametrize("gomb", sorted(ALSO_GOMBOK))
def test_a_negy_also_gomb_mindig_ugyanott_van(qt_app, meret, gomb):
    """A négy alsó gomb a FIX hasábhoz tartozik — nem ül az ablak aljára.

    Ez az az állítás, amit a felhasználó képernyőképe számszerűen igazolt:
    egy ~1352 px széles ablakban ugyanott vannak, ahol 800 px-esben."""
    panel = _panel(qt_app, *meret)
    elvart_x, elvart_y, elvart_w, elvart_h = ALSO_GOMBOK[gomb]
    assert _ablakban(_child(panel, gomb)) == (elvart_x, elvart_y, elvart_w, elvart_h)


def test_a_vaszon_oldal_nyulik_az_ablakkal(qt_app):
    """A vászon-oldal MINDKÉT irányban nő, ahogy az ablak."""
    meretek = []
    for szeles, magas in ABLAKMERETEK:
        panel = _panel(qt_app, szeles, magas)
        _, _, vaszon_w, vaszon_h = _ablakban(_child(panel, "collageCanvas"))
        meretek.append((vaszon_w, vaszon_h))
    for elozo, kovetkezo in zip(meretek, meretek[1:], strict=False):
        assert kovetkezo[0] > elozo[0]
        assert kovetkezo[1] > elozo[1]


@pytest.mark.parametrize("meret", ABLAKMERETEK)
def test_a_vaszon_a_spec_behuzasait_kapja(qt_app, meret):
    """`rightcontainer = base − (289, 20, 10, 10)` — pontosan (spec 2.6)."""
    szeles, magas = meret
    panel = _panel(qt_app, szeles, magas)
    assert _ablakban(_child(panel, "collageCanvas")) == (
        289,
        20,
        szeles - 289 - 10,
        magas - 20 - 10,
    )


def test_a_tervezovaszon_merete_az_implicit_meret(qt_app):
    """`implicitWidth: 800`, `implicitHeight: 534` — a minimális panelméret."""
    panel = _panel(qt_app, 800, 534)
    assert panel.property("implicitWidth") == 800
    assert panel.property("implicitHeight") == 534


def test_a_hasab_szuk_ablakban_sem_zsugorodik(qt_app):
    """A tervezővászon ALATT a vászon-oldal fogy el, a hasáb soha (spec 2.6)."""
    panel = _panel(qt_app, 420, 300)
    _, _, hasab_w, _ = _ablakban(_child(panel, "collageTabBase"))
    assert hasab_w == HASAB_SZELESSEG
    _, _, vaszon_w, _ = _ablakban(_child(panel, "collageCanvas"))
    assert vaszon_w < 276


# --- 2. A lap: arány, behúzás, középre igazítás -----------------------------

#: Néhány oldalformátum MAGASSÁG / SZÉLESSÉG arányban: 4:3 fekvő, 3:2 fekvő,
#: négyzetes, és 4:3 álló.
OLDALARANYOK = [0.75, 2 / 3, 1.0, 4 / 3]


@pytest.mark.parametrize("arany", OLDALARANYOK)
@pytest.mark.parametrize("meret", ABLAKMERETEK)
def test_a_lap_oldalaranya_az_oldalformatume(qt_app, arany, meret):
    """A lap aránya az oldalformátumé, ±0,5 %-on belül.

    A tűrés a képpontra kerekítésé: a lap egész képpontokból áll."""
    panel = _panel(qt_app, *meret, page_ratio=arany)
    _, _, szeles, magas = _ablakban(_child(panel, "collageSheet"))
    assert szeles > 0 and magas > 0
    assert magas / szeles == pytest.approx(arany, rel=0.005)


@pytest.mark.parametrize("arany", OLDALARANYOK)
@pytest.mark.parametrize("meret", ABLAKMERETEK)
def test_a_lap_a_behuzason_belul_van_es_kozepen(qt_app, arany, meret):
    """A lap a `previewinset`-en belül ül, vízszintesen ÉS függőlegesen középen.

    A `previewinset` a vászonkeret mínusz (12, 35, 12, 35) — a 35 képpont a
    lap fölött és alatt lebegő gombsoré (28 px + 2 px rés + levegő)."""
    panel = _panel(qt_app, *meret, page_ratio=arany)
    vaszon_x, vaszon_y, vaszon_w, vaszon_h = _ablakban(_child(panel, "collageCanvas"))
    lap_x, lap_y, lap_w, lap_h = _ablakban(_child(panel, "collageSheet"))

    behuzas_x = vaszon_x + 12
    behuzas_y = vaszon_y + 35
    behuzas_w = vaszon_w - 24
    behuzas_h = vaszon_h - 70

    assert lap_x >= behuzas_x
    assert lap_y >= behuzas_y
    assert lap_x + lap_w <= behuzas_x + behuzas_w
    assert lap_y + lap_h <= behuzas_y + behuzas_h

    # középen: a két oldalon maradó rés legfeljebb egy képpontnyit tér el
    # (a kerekítés miatt)
    assert abs((lap_x - behuzas_x) - (behuzas_x + behuzas_w - lap_x - lap_w)) <= 1
    assert abs((lap_y - behuzas_y) - (behuzas_y + behuzas_h - lap_y - lap_h)) <= 1


def test_a_lap_kitolti_a_behuzas_rovidebb_iranyat(qt_app):
    """A lap a lehető LEGNAGYOBB — az egyik irányban felül a behúzáson.

    Enélkül a törvény teljesülne, de a felhasználó apró lapot látna nagy
    üres kereten."""
    panel = _panel(qt_app, 1280, 800, page_ratio=0.75)
    vaszon_x, vaszon_y, vaszon_w, vaszon_h = _ablakban(_child(panel, "collageCanvas"))
    lap_x, lap_y, lap_w, lap_h = _ablakban(_child(panel, "collageSheet"))
    behuzas_w = vaszon_w - 24
    behuzas_h = vaszon_h - 70
    assert lap_w == behuzas_w or lap_h == behuzas_h


# --- 3. A fülsáv ------------------------------------------------------------


def test_a_masodik_ful_a_tenyleges_darabszamot_mutatja(qt_app):
    """A második fül felirata futásidőben frissül a klip-darabszámmal."""
    panel = _panel(qt_app, 800, 534, clips=7)
    assert "7" in _child(panel, "collageClipsTabButton").property("text")


def test_a_beallitasok_lap_az_alapertelmezett(qt_app):
    """A `.tre`-ben a `tab1` az előre lenyomott (`setpressed 1`)."""
    panel = _panel(qt_app, 800, 534)
    assert _child(panel, "collageSettingsTab").isVisible()
    assert not _child(panel, "collageClipsTab").isVisible()


def test_mindig_pontosan_egy_laptartalom_latszik(qt_app):
    """A két laptartalom UGYANOTT ül — együtt látszaniuk kellene átfedést.

    A #650 pontosan ilyen hiba volt: két vezérlő egymás tetején, mindkettő
    látható."""
    panel = _panel(qt_app, 800, 534)
    tabbar = _child(panel, "collageTabBar")
    for index in (0, 1):
        tabbar.setProperty("currentIndex", index)
        lathato = [
            nev
            for nev in ("collageSettingsTab", "collageClipsTab")
            if _child(panel, nev).isVisible()
        ]
        assert len(lathato) == 1, f"{index}. fülnél láthatók: {lathato}"


def test_a_ket_laptartalom_ugyanott_kezdodik(qt_app):
    """Mindkét lap a (13, 55) abszolút sarokból indul (spec 4.1)."""
    panel = _panel(qt_app, 800, 534)
    tabbar = _child(panel, "collageTabBar")
    sarkok = []
    for index in (0, 1):
        tabbar.setProperty("currentIndex", index)
        nev = "collageSettingsTab" if index == 0 else "collageClipsTab"
        x, y, _, _ = _ablakban(_child(panel, nev))
        sarkok.append((x, y))
    assert sarkok == [(13, 55), (13, 55)]


# --- 4. Az Esc a Bezárás ----------------------------------------------------


def test_az_esc_bezar(qt_app):
    """A `.tre` a `cancelbutton`-ra `escapekey 1`-et tesz: az Esc a Bezárás.

    ⚠️ Az őr nem formalitás. Az első változat `focus: true` NÉLKÜL épült, és a
    `Keys` kezelő némán soha nem tüzelt — a kód azt állította, hogy az Esc
    bezár, a valóságban nulla hívás ment. Kirajzolt, billentyűt küldő teszt
    nélkül ez a hiba átcsúszott volna."""
    panel = _panel(qt_app, 800, 534)
    view = panel.property("_view")
    stub = panel.property("_stub")
    QTest.qWaitForWindowExposed(view)
    assert stub.close_calls == 0

    QTest.keyClick(view, Qt.Key_Escape)
    assert stub.close_calls == 1


def test_a_bezaras_gomb_ugyanazt_teszi_mint_az_esc(qt_app):
    """Egy kódút: a gomb és az Esc ugyanazt a `requestClose()`-t hívja.

    ⚠️ #949: a hívás VALÓDI kattintás lett. A `requestClose()` azóta egy
    paramétert kapott (`skipUnsavedPrompt`, a mentés utáni önzáródás ága —
    ezt a #945 kommentje elő is írta), és a paraméteres QML-függvényt az
    `invokeMethod` argumentum nélkül nem tudja meghívni. A gombot megnyomni
    amúgy is közelebb van ahhoz, amit a teszt neve állít."""
    panel = _panel(qt_app, 800, 534)
    view = panel.property("_view")
    stub = panel.property("_stub")
    QTest.qWaitForWindowExposed(view)
    gomb = _child(panel, "collageCloseButton")
    kozep = gomb.mapToScene(gomb.boundingRect().center())
    QTest.mouseClick(
        view,
        Qt.LeftButton,
        Qt.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    QTest.qWait(50)
    assert stub.close_calls == 1
