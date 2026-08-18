"""A Kollázs-panel „Beállítások" lapja, KIRAJZOLVA — #946.

Spec: `docs/specs/kollazs-panel-ui-spec.md` **4.2** (elemenkénti tábla),
**5.** (a képesség-maszk mátrixa) és **12.** (teszt-szerződés).

Miért kirajzolt teszt: a property-t olvasó ellenőrzés nem látja, mit lát a
felhasználó. A lap két csoportja — a keretsor és a térköz-csúszka —
**ugyanazt a helyet foglalja**, tehát a „nem látszik egyszerre" állítás
csak a valódi vizuális fából dönthető el. A `Repeater` delegáltjait a
`findChild` NEM találja meg, ezért a `_walk()` a vizuális fán jár, és a
kapcsolókat VALÓDI egérkattintás éri — nem függvényhívás. Így derül ki, ha
egy felirat mellé nem került kattintható felület (`m_hit_childlabel`).

A geometria a **`collageSettingsTab` bal-felső sarkához** képest értendő
(a spec 1.10-es abszolút értékéből 13 / 55 levonva).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Property, QObject, QPointF, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

from picasapy.collage.page_formats import PAGE_FORMATS
from picasapy.collage.themes import COLLAGE_THEMES, capability_map

_KEEPALIVE: list[object] = []

#: A lap tervezői mérete (spec 4.1).
LAP_SZELESSEG = 266
LAP_MAGASSAG = 351

#: A spec 4.2-es táblája: `objectName` → (x, y, szélesség, magasság) a lap
#: bal-felső sarkához mérve. Ez a SZERZŐDÉS — a `.tre`-ből származó számok.
GEOMETRIA = {
    "collageThemePopup": (0, 8, 266, 56),
    "collageBordersLabel": (3, 67, 239, 15),
    "collageBordersGroup": (0, 67, 266, 89),
    "collageBorder0": (34, 88, 62, 62),
    "collageBorder1": (103, 88, 62, 62),
    "collageBorder2": (172, 88, 62, 62),
    "collageSpacingGroup": (6, 68, 250, 81),
    "collageSpacingLabel": (21, 76, 225, 21),
    "collageSpacingSlider": (35, 98, 191, 27),
    "collageSpacingMinLabel": (35, 125, 83, 14),
    "collageSpacingMaxLabel": (140, 125, 86, 14),
    "collageLeftDivider": (0, 154, 256, 3),
    "collageBkgTitle": (3, 159, 239, 15),
    "collageBackgroundTypes": (6, 178, 127, 55),
    "collageColorBgRadio": (6, 179, 24, 24),
    "collageBitmapBgRadio": (6, 206, 24, 24),
    "collageColorPickContainer": (134, 180, 49, 49),
    "collageColorCircle": (140, 186, 37, 37),
    "collageDropperIcon": (180, 198, 24, 14),
    "collageBackgroundContainer": (134, 180, 135, 49),
    "collageCurrentBackground": (140, 186, 37, 37),
    "collageBkgFromSelection": (185, 186, 71, 37),
    "collagePickerPanel": (48, 9, 218, 178),
    "collageFormatTitle": (3, 235, 239, 15),
    "collageFormatMenu": (3, 255, 243, 21),
    "collageOrientation": (88, 280, 74, 22),
    "collageLandscapeButton": (88, 280, 37, 22),
    "collagePortraitButton": (125, 280, 37, 22),
    "collageShadowCheckbox": (5, 303, 14, 14),
    "collageCaptionCheckbox": (4, 328, 14, 14),
    "collageSetFrameCenter": (137, 310, 124, 30),
}

#: A kuka a lap JOBB széléhez igazodik (−4), nem beégetett x-hez.
KUKA_JOBB_MARGO = 4

#: A három keretgomb sorrendje a panelen (spec 4.2 3a–c).
KERET_KULCSOK = ("noborder", "whiteborder", "polaroid")

#: Egy egyéni képarány a #448-as úton — a kulcs alakja az `EditorPanel.qml`
#: `aspectFullList`-jével azonos, hogy ne szülessen második írásmód.
EGYENI = {"name": "Panoráma", "width": 3.0, "height": 1.0}
EGYENI_KULCS = "custom:Panoráma:3x1"


class _CollageStub(QObject):
    """Annyi a vezérlőből, amennyit a „Beállítások" lap használ.

    A képességek a VALÓDI `themes.capability_map`-ből jönnek — így a teszt
    nem tud eltérni attól az egyetlen forrástól, ami a panelt vezérli."""

    collageThemeChanged = Signal()
    collageBorderChanged = Signal()
    collageSpacingChanged = Signal()
    collageShadowsChanged = Signal()
    collageCaptionsChanged = Signal()
    collageOrientationChanged = Signal()
    collageFormatKeyChanged = Signal()
    collageBackgroundModeChanged = Signal()
    collageBackgroundColorChanged = Signal()
    collageBackgroundImageChanged = Signal()
    collageCapabilitiesChanged = Signal()
    customAspectRatiosChanged = Signal()

    def __init__(
        self,
        theme="picturepile",
        *,
        border="noborder",
        spacing=0.5,
        shadows=None,
        captions=True,
        orientation="landscape",
        format_key="Desktop4x3",
        bg_mode="solid",
        bg_color="#000000",
        bg_image="",
        custom=(),
    ) -> None:
        super().__init__()
        self._theme = theme
        self._border = border
        self._spacing = spacing
        # az árnyék alapértékét a téma maszkja adja (14. bit)
        self._shadows = (
            capability_map(theme)["shadow"] if shadows is None else shadows
        )
        self._captions = captions
        self._orientation = orientation
        self._format = format_key
        self._bg_mode = bg_mode
        self._bg_color = QColor(bg_color)
        self._bg_image = bg_image
        self._custom = list(custom)
        self.frame_center_calls = 0
        self.background_from_selection_calls = 0
        self.deleted_ratios: list[tuple] = []
        self.added_ratios: list[tuple] = []

    # -- property-k ------------------------------------------------------

    @Property(str, notify=collageThemeChanged)
    def collageTheme(self) -> str:
        return self._theme

    @Property(str, notify=collageBorderChanged)
    def collageBorder(self) -> str:
        return self._border

    @Property(float, notify=collageSpacingChanged)
    def collageSpacing(self) -> float:
        return self._spacing

    @Property(bool, notify=collageShadowsChanged)
    def collageShadows(self) -> bool:
        return self._shadows

    @Property(bool, notify=collageCaptionsChanged)
    def collageCaptions(self) -> bool:
        return self._captions

    @Property(str, notify=collageOrientationChanged)
    def collageOrientation(self) -> str:
        return self._orientation

    @Property(str, notify=collageFormatKeyChanged)
    def collageFormatKey(self) -> str:
        return self._format

    @Property(str, notify=collageBackgroundModeChanged)
    def collageBackgroundMode(self) -> str:
        return self._bg_mode

    @Property(QColor, notify=collageBackgroundColorChanged)
    def collageBackgroundColor(self) -> QColor:
        return self._bg_color

    @Property(str, notify=collageBackgroundImageChanged)
    def collageBackgroundImage(self) -> str:
        return self._bg_image

    @Property("QVariantMap", notify=collageCapabilitiesChanged)
    def collageCapabilities(self) -> dict:
        return capability_map(self._theme)

    @Property("QVariant", notify=customAspectRatiosChanged)
    def customAspectRatios(self) -> list:
        return list(self._custom)

    # A panelbe ágyazott próbához (a váz, #945, ezt a kettőt olvassa).

    @Property(float, constant=True)
    def collagePageRatio(self) -> float:
        return 0.75

    @Property(int, constant=True)
    def collageClipCount(self) -> int:
        return 0

    # -- slotok ----------------------------------------------------------

    @Slot(str)
    def setCollageTheme(self, key: str) -> None:
        self._theme = key
        self.collageThemeChanged.emit()
        self.collageCapabilitiesChanged.emit()

    @Slot(str)
    def setCollageBorder(self, key: str) -> None:
        self._border = key
        self.collageBorderChanged.emit()

    @Slot(float)
    def setCollageSpacing(self, value: float) -> None:
        self._spacing = float(value)
        self.collageSpacingChanged.emit()

    @Slot(bool)
    def setCollageShadows(self, on: bool) -> None:
        self._shadows = bool(on)
        self.collageShadowsChanged.emit()

    @Slot(bool)
    def setCollageCaptions(self, on: bool) -> None:
        self._captions = bool(on)
        self.collageCaptionsChanged.emit()

    @Slot(str)
    def setCollageOrientation(self, kind: str) -> None:
        self._orientation = kind
        self.collageOrientationChanged.emit()

    @Slot(str)
    def setCollageFormat(self, key: str) -> None:
        # A teszt-kettős MINDEN kulcsot elfogad (az egyénieket is): itt az a
        # kérdés, hogy a lap a HELYES kulcsot küldi-e. Hogy a valódi vezérlő
        # mit fogad el, az a `test_collage_controller_943.py` dolga.
        self._format = key
        self.collageFormatKeyChanged.emit()

    @Slot(str)
    def setCollageBackgroundMode(self, mode: str) -> None:
        self._bg_mode = mode
        self.collageBackgroundModeChanged.emit()

    @Slot("QColor")
    def setCollageBackgroundColor(self, color) -> None:
        self._bg_color = QColor(color)
        self.collageBackgroundColorChanged.emit()

    @Slot()
    def setBackgroundFromSelection(self) -> None:
        self.background_from_selection_calls += 1

    @Slot()
    def setFrameCenterFromSelection(self) -> None:
        self.frame_center_calls += 1

    @Slot(float, float, str)
    def addCustomAspectRatio(self, width: float, height: float, name: str) -> None:
        self.added_ratios.append((width, height, name))
        self._custom = [*self._custom, {"name": name, "width": width, "height": height}]
        self.customAspectRatiosChanged.emit()

    @Slot(str, float, float)
    def deleteCustomAspectRatio(self, name: str, width: float, height: float) -> None:
        self.deleted_ratios.append((name, width, height))
        self._custom = [c for c in self._custom if c["name"] != name]
        self.customAspectRatiosChanged.emit()


def _betolt(qt_app, qml: bytes, szeles: int, magas: int, stub):
    """A megadott QML valódi ablakban, kirajzolva."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(view.engine())
    component.setData(qml, QUrl())
    assert [e.toString() for e in component.errors()] == []
    root = component.create()
    assert root is not None
    root.setProperty("controller", stub)
    root.setWidth(szeles)
    root.setHeight(magas)
    root.setParentItem(view.contentItem())
    view.resize(szeles, magas)
    view.show()
    QTest.qWaitForWindowExposed(view)
    qt_app.processEvents()
    _KEEPALIVE.extend((view, root, stub, component))
    root.setProperty("_stub", stub)
    root.setProperty("_view", view)
    return root


def _tab(qt_app, **allapot):
    """A „Beállítások" lap önmagában, a tervezői méretével."""
    return _betolt(
        qt_app,
        b"""
import QtQuick
import PicasaPy 1.0
CollageSettingsTab { objectName: "collageSettingsTab" }
""",
        LAP_SZELESSEG,
        LAP_MAGASSAG,
        _CollageStub(**allapot),
    )


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása — a `findChild` nem lát mindent (#651)."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _keres(root: QQuickItem, name: str):
    for item in _walk(root):
        if item.objectName() == name:
            return item
    return root.findChild(QObject, name)


def _child(root: QQuickItem, name: str):
    item = _keres(root, name)
    assert item is not None, f"{name} nem található a kirajzolt fában"
    return item


def _doboz(tab: QQuickItem, item: QQuickItem) -> tuple[float, float, float, float]:
    """Az elem doboza a LAP koordinátarendszerében."""
    sarok = item.mapToItem(tab, QPointF(0, 0))
    return (sarok.x(), sarok.y(), item.width(), item.height())


def _latszik(tab: QQuickItem, name: str) -> bool:
    item = _keres(tab, name)
    return bool(item is not None and item.isVisible())


def _kattint(qt_app, item: QQuickItem, dx=None, dy=None) -> None:
    """VALÓDI egérkattintás az elemre, az ablak koordinátáiban."""
    pont = item.mapToScene(
        QPointF(
            item.width() / 2 if dx is None else dx,
            item.height() / 2 if dy is None else dy,
        )
    ).toPoint()
    QTest.mouseClick(item.window(), Qt.LeftButton, Qt.NoModifier, pont)
    qt_app.processEvents()


def _nyit(qt_app, tab: QQuickItem, nev: str) -> None:
    """Egy lenyíló (téma vagy oldalformátum) kinyitása kattintással."""
    _kattint(qt_app, _child(tab, nev))


# --- 1. Geometria — a spec 4.2-es táblája -----------------------------------


@pytest.mark.parametrize("nev", sorted(GEOMETRIA))
def test_az_elemek_a_spec_szerinti_helyen_vannak(qt_app, nev):
    """Minden elem pontosan ott és akkora, amit a `.tre` mond.

    Az elemek egy része csak bizonyos témánál látszik; a HELYE viszont
    akkor is a spec szerinti, ha épp rejtett — ezért a `framegrid` témát
    használjuk (ott a `collageSetFrameCenter` is él), és a rejtett
    csoportokat is megmérjük."""
    tab = _tab(qt_app, theme="framegrid")
    assert _doboz(tab, _child(tab, nev)) == GEOMETRIA[nev]


def test_a_kuka_a_lap_jobb_szelehez_igazodik(qt_app):
    """A `collageDeleteCustomAspect` jobbra igazítva (−4), 14 × 14."""
    tab = _tab(qt_app, custom=[EGYENI], format_key=EGYENI_KULCS)
    x, _, szeles, magas = _doboz(tab, _child(tab, "collageDeleteCustomAspect"))
    assert (szeles, magas) == (14, 14)
    assert x + szeles == LAP_SZELESSEG - KUKA_JOBB_MARGO


# --- 2. A képesség-maszk — spec 5. ------------------------------------------


@pytest.mark.parametrize("tema", COLLAGE_THEMES)
def test_a_keretsor_es_a_terkoz_soha_nem_latszik_egyutt(qt_app, tema):
    """A kettő UGYANAZT a helyet foglalja (spec 4.2) — együtt átfednének.

    ⚠️ Ezt a kérdést a `themes.capabilities_for` maszkja dönti el, nem
    témánkénti `if`: a Mozaiknál például NINCS keretválasztó, hiába
    gondolná az ember, hogy a három képkeret ott is választható."""
    tab = _tab(qt_app, theme=tema)
    keret = _latszik(tab, "collageBordersGroup")
    terkoz = _latszik(tab, "collageSpacingGroup")
    assert not (keret and terkoz), f"{tema}: mindkettő látszik"


@pytest.mark.parametrize("tema", COLLAGE_THEMES)
def test_a_keretsor_pontosan_a_maszk_szerint_latszik(qt_app, tema):
    tab = _tab(qt_app, theme=tema)
    vart = capability_map(tema)["borders"]
    assert _latszik(tab, "collageBordersGroup") is vart
    assert _latszik(tab, "collageBordersLabel") is vart


@pytest.mark.parametrize("tema", COLLAGE_THEMES)
def test_a_terkoz_csuszka_pontosan_a_maszk_szerint_latszik(qt_app, tema):
    tab = _tab(qt_app, theme=tema)
    vart = capability_map(tema)["spacing"]
    assert _latszik(tab, "collageSpacingGroup") is vart
    assert _latszik(tab, "collageSpacingSlider") is vart


@pytest.mark.parametrize("tema", COLLAGE_THEMES)
def test_az_arnyek_jelolo_pontosan_a_maszk_szerint_latszik(qt_app, tema):
    tab = _tab(qt_app, theme=tema)
    assert _latszik(tab, "collageShadowCheckbox") is capability_map(tema)["shadow"]


@pytest.mark.parametrize("tema", COLLAGE_THEMES)
def test_a_hatter_doboz_pontosan_a_maszk_szerint_latszik(qt_app, tema):
    tab = _tab(qt_app, theme=tema)
    vart = capability_map(tema)["background"]
    assert _latszik(tab, "collageBkgTitle") is vart
    assert _latszik(tab, "collageBackgroundTypes") is vart


def test_a_tobbszoros_exponalasnak_nincs_arnyeka_es_hattere(qt_app):
    """A spec 5. mátrixának legerősebb sora: a Többszörös exponálásnál
    egyszerre NÉGY beállítás tűnik el a lapról."""
    tab = _tab(qt_app, theme="multiexp")
    assert not _latszik(tab, "collageShadowCheckbox")
    assert not _latszik(tab, "collageBackgroundTypes")
    assert not _latszik(tab, "collageBordersGroup")
    assert not _latszik(tab, "collageSpacingGroup")


@pytest.mark.parametrize("tema", COLLAGE_THEMES)
def test_a_kepfelirat_jelolo_minden_temanal_latszik(qt_app, tema):
    """A 16. elem `mikor látszik` oszlopa: **mindig** (spec 4.2)."""
    tab = _tab(qt_app, theme=tema)
    assert _latszik(tab, "collageCaptionCheckbox")


@pytest.mark.parametrize("tema", COLLAGE_THEMES)
def test_az_oldalformatum_es_a_tajolas_mindig_latszik(qt_app, tema):
    """A 11., 12. és 14. elem: **mindig** — a Többszörös exponálásnál is."""
    tab = _tab(qt_app, theme=tema)
    assert _latszik(tab, "collageFormatTitle")
    assert _latszik(tab, "collageFormatMenu")
    assert _latszik(tab, "collageOrientation")


@pytest.mark.parametrize("tema", COLLAGE_THEMES)
def test_a_kepkockakozeppont_gomb_csak_framegridnel_latszik(qt_app, tema):
    """A 17. elem: **csak** `framegrid` (spec 4.2)."""
    tab = _tab(qt_app, theme=tema)
    assert _latszik(tab, "collageSetFrameCenter") is (tema == "framegrid")


# --- 3. A vezérlő hívása — a lap nem tart saját logikát ---------------------


def test_a_temavalaszto_hat_sort_kinal(qt_app):
    """A lenyíló hat sora a hat téma — se több, se kevesebb."""
    tab = _tab(qt_app)
    _nyit(qt_app, tab, "collageThemePopup")
    sorok = [
        item
        for item in _walk(tab)
        if item.objectName().startswith("collageThemeOption")
    ]
    assert len(sorok) == len(COLLAGE_THEMES)


@pytest.mark.parametrize("index,kulcs", list(enumerate(COLLAGE_THEMES)))
def test_a_temasor_a_sajat_temajat_allitja_be(qt_app, index, kulcs):
    tab = _tab(qt_app)
    stub = tab.property("_stub")
    _nyit(qt_app, tab, "collageThemePopup")
    _kattint(qt_app, _child(tab, f"collageThemeOption{index}"))
    assert stub.collageTheme == kulcs


def test_a_temavalaszto_becsukodik_a_valasztas_utan(qt_app):
    tab = _tab(qt_app)
    _nyit(qt_app, tab, "collageThemePopup")
    assert _latszik(tab, "collageThemeList")
    _kattint(qt_app, _child(tab, "collageThemeOption2"))
    assert not _latszik(tab, "collageThemeList")


@pytest.mark.parametrize("index,kulcs", list(enumerate(KERET_KULCSOK)))
def test_a_keretgomb_a_sajat_keretet_allitja_be(qt_app, index, kulcs):
    tab = _tab(qt_app)
    stub = tab.property("_stub")
    _kattint(qt_app, _child(tab, f"collageBorder{index}"))
    assert stub.collageBorder == kulcs


def test_a_terkoz_csuszka_a_vegein_nullat_es_egyet_ad(qt_app):
    """A csúszka 0…1-et ad a vezérlőnek — NEM képpontot (spec 8.1).

    Valódi kattintás a sín két végére: a felhasználó ezt teszi."""
    tab = _tab(qt_app, theme="picturegrid", spacing=0.5)
    stub = tab.property("_stub")
    csuszka = _child(tab, "collageSpacingSlider")
    assert csuszka.property("from") == 0.0
    assert csuszka.property("to") == 1.0

    _kattint(qt_app, csuszka, dx=csuszka.width() - 1)
    assert stub.collageSpacing == pytest.approx(1.0, abs=0.05)
    _kattint(qt_app, csuszka, dx=1)
    assert stub.collageSpacing == pytest.approx(0.0, abs=0.05)


def test_az_arnyek_jelolo_a_feliratra_kattintva_is_kapcsol(qt_app):
    """`m_hit_childlabel` — a felirat a jelölő része (spec 4.2).

    ⚠️ Ez az a fajta állítás, amit csak VALÓDI kattintás dönt el: a
    felirat mellé kattintható felület kell, különben a kód „működik", de a
    felhasználó hiába kattint a szövegre."""
    tab = _tab(qt_app, shadows=True)
    stub = tab.property("_stub")
    _kattint(qt_app, _child(tab, "collageShadowLabel"))
    assert stub.collageShadows is False


def test_a_felirat_jelolo_a_feliratra_kattintva_is_kapcsol(qt_app):
    tab = _tab(qt_app, captions=True)
    stub = tab.property("_stub")
    _kattint(qt_app, _child(tab, "collageCaptionLabel"))
    assert stub.collageCaptions is False


def test_a_jelolonegyzetek_magukra_kattintva_is_kapcsolnak(qt_app):
    tab = _tab(qt_app, shadows=True, captions=True)
    stub = tab.property("_stub")
    _kattint(qt_app, _child(tab, "collageShadowCheckbox"))
    _kattint(qt_app, _child(tab, "collageCaptionCheckbox"))
    assert stub.collageShadows is False
    assert stub.collageCaptions is False


def test_a_ket_jelolo_alapbol_bepipalt(qt_app):
    """`setpressed 1` — az árnyék és a képfelirat alapból BE (spec 4.2).

    Az árnyék alapértékét a téma maszkja adja (14. bit), ezért a
    Képkupacon nézzük."""
    tab = _tab(qt_app)
    assert _child(tab, "collageShadowCheckbox").property("checked") is True
    assert _child(tab, "collageCaptionCheckbox").property("checked") is True


@pytest.mark.parametrize(
    "gomb,kulcs",
    [("collageLandscapeButton", "landscape"), ("collagePortraitButton", "portrait")],
)
def test_a_tajolas_gombok_a_vezerlot_hivjak(qt_app, gomb, kulcs):
    masik = "portrait" if kulcs == "landscape" else "landscape"
    tab = _tab(qt_app, orientation=masik)
    stub = tab.property("_stub")
    _kattint(qt_app, _child(tab, gomb))
    assert stub.collageOrientation == kulcs


def test_a_tajolas_gombjai_kozul_a_jelenlegi_van_lenyomva(qt_app):
    tab = _tab(qt_app, orientation="portrait")
    assert _child(tab, "collagePortraitButton").property("checked") is True
    assert _child(tab, "collageLandscapeButton").property("checked") is False


def test_a_kepkockakozeppont_gomb_a_vezerlot_hivja(qt_app):
    tab = _tab(qt_app, theme="framegrid")
    stub = tab.property("_stub")
    _kattint(qt_app, _child(tab, "collageSetFrameCenter"))
    assert stub.frame_center_calls == 1


# --- 4. Háttér — a két rádió, a színkör és a paletta ------------------------


@pytest.mark.parametrize("mod", ["solid", "image"])
def test_a_ket_hatter_doboz_soha_nem_latszik_egyutt(qt_app, mod):
    """A színválasztó és a háttérkép-doboz UGYANOTT ül (134, 180)."""
    tab = _tab(qt_app, bg_mode=mod)
    szin = _latszik(tab, "collageColorPickContainer")
    kep = _latszik(tab, "collageBackgroundContainer")
    assert not (szin and kep)
    assert szin is (mod == "solid")
    assert kep is (mod == "image")


def test_az_egyszinu_az_alapertelmezes(qt_app):
    """`color_bg`: `Property setpressed 1` (spec 3.)."""
    tab = _tab(qt_app)
    assert _child(tab, "collageColorBgRadio").property("checked") is True
    assert _child(tab, "collageBitmapBgRadio").property("checked") is False


@pytest.mark.parametrize(
    "radio,mod", [("collageColorBgRadio", "solid"), ("collageBitmapBgRadio", "image")]
)
def test_a_radiogombok_a_hatter_modot_allitjak(qt_app, radio, mod):
    tab = _tab(qt_app, bg_mode="image" if mod == "solid" else "solid")
    stub = tab.property("_stub")
    _kattint(qt_app, _child(tab, radio))
    assert stub.collageBackgroundMode == mod


@pytest.mark.parametrize(
    "felirat,mod",
    [("collageColorBgLabel", "solid"), ("collageBitmapBgLabel", "image")],
)
def test_a_radiogombok_felirata_is_kapcsol(qt_app, felirat, mod):
    """`m_hit_childlabel` a rádiógomboknál is."""
    tab = _tab(qt_app, bg_mode="image" if mod == "solid" else "solid")
    stub = tab.property("_stub")
    _kattint(qt_app, _child(tab, felirat))
    assert stub.collageBackgroundMode == mod


def test_a_szinkor_a_jelenlegi_hatterszint_mutatja(qt_app):
    tab = _tab(qt_app, bg_color="#3366cc")
    kor = _child(tab, "collageColorCircle")
    assert QColor(kor.property("color")).name() == "#3366cc"
    # kör, nem négyzet: a sugár a fél oldalhossz (spec 4.2 8a)
    assert kor.property("radius") == pytest.approx(18.5)


def test_a_paletta_alapbol_rejtett_es_a_szinkorre_kattintva_nyilik(qt_app):
    """A `picker_panel` a `.tre`-ben `m_hidden` (spec 3.)."""
    tab = _tab(qt_app)
    assert not _latszik(tab, "collagePickerPanel")
    _kattint(qt_app, _child(tab, "collageColorCircle"))
    assert _latszik(tab, "collagePickerPanel")


def test_a_palettarol_valasztott_szin_a_vezerlobe_megy(qt_app):
    tab = _tab(qt_app, bg_color="#000000")
    stub = tab.property("_stub")
    _kattint(qt_app, _child(tab, "collageColorCircle"))
    minta = _child(tab, "collagePickerSwatch3")
    vart = QColor(minta.property("color")).name()
    _kattint(qt_app, minta)
    assert QColor(stub.collageBackgroundColor).name() == vart
    assert not _latszik(tab, "collagePickerPanel")


def test_a_kijelolt_elemek_hasznalata_a_vezerlot_hivja(qt_app):
    tab = _tab(qt_app, bg_mode="image")
    stub = tab.property("_stub")
    _kattint(qt_app, _child(tab, "collageBkgFromSelection"))
    assert stub.background_from_selection_calls == 1


# --- 5. Oldalformátum-menü --------------------------------------------------


def test_az_oldalformatum_lista_husz_teteles(qt_app):
    """18 beépített formátum + a csoportcím + a felvevő sor = 20 (spec 7.)."""
    tab = _tab(qt_app)
    _nyit(qt_app, tab, "collageFormatMenu")
    tetelek = [
        item
        for item in _walk(tab)
        if item.objectName().startswith("collageFormatOption")
    ]
    assert len(tetelek) == len(PAGE_FORMATS) == 18
    assert _latszik(tab, "collageFormatCustomHeader")
    assert _latszik(tab, "collageFormatAddCustom")


def test_a_formatum_valasztasa_a_vezerlot_hivja(qt_app):
    tab = _tab(qt_app)
    stub = tab.property("_stub")
    _nyit(qt_app, tab, "collageFormatMenu")
    _kattint(qt_app, _child(tab, "collageFormatOption6"))
    assert stub.collageFormatKey == PAGE_FORMATS[6].key


def test_a_menu_a_jelenlegi_formatumot_mutatja(qt_app):
    tab = _tab(qt_app, format_key="Square")
    assert "Square" in _child(tab, "collageFormatLabel").property("text")


def test_az_egyeni_aranyok_a_lista_vegen_allnak(qt_app):
    tab = _tab(qt_app, custom=[EGYENI])
    _nyit(qt_app, tab, "collageFormatMenu")
    assert "Panoráma" in _child(tab, "collageFormatCustom0").property("text")


def test_az_egyeni_arany_kivalasztasa_a_sajat_kulcsat_kuldi(qt_app):
    tab = _tab(qt_app, custom=[EGYENI])
    stub = tab.property("_stub")
    _nyit(qt_app, tab, "collageFormatMenu")
    _kattint(qt_app, _child(tab, "collageFormatCustom0"))
    assert stub.collageFormatKey == EGYENI_KULCS


def test_a_kuka_csak_egyeni_arany_eseten_latszik(qt_app):
    """A 13. elem: `ha egyéni arány az aktív` (spec 4.2)."""
    tab = _tab(qt_app, custom=[EGYENI], format_key="Desktop4x3")
    assert not _latszik(tab, "collageDeleteCustomAspect")
    tab = _tab(qt_app, custom=[EGYENI], format_key=EGYENI_KULCS)
    assert _latszik(tab, "collageDeleteCustomAspect")


def test_a_kuka_a_meglevo_448_as_uton_torol(qt_app):
    """Ne szülessen második megvalósítás: a #448 `deleteCustomAspectRatio`."""
    tab = _tab(qt_app, custom=[EGYENI], format_key=EGYENI_KULCS)
    stub = tab.property("_stub")
    _kattint(qt_app, _child(tab, "collageDeleteCustomAspect"))
    assert stub.deleted_ratios == [("Panoráma", 3.0, 1.0)]


def test_az_uj_egyeni_arany_a_meglevo_448_as_parbeszeddel_megy(qt_app):
    """Az `AddCustomAspectRatioDialog` (#448) — ne szülessen második.

    A felvevő sor megnyitja a MEGLÉVŐ párbeszédet, és annak `created` jele
    a #448-as `addCustomAspectRatio` slotba fut."""
    tab = _tab(qt_app)
    stub = tab.property("_stub")
    _nyit(qt_app, tab, "collageFormatMenu")
    _kattint(qt_app, _child(tab, "collageFormatAddCustom"))
    parbeszed = _child(tab, "addCustomAspectRatioDialog")
    assert parbeszed.property("visible") is True

    _child(tab, "customAspectWidthField").setProperty("text", "3")
    _child(tab, "customAspectHeightField").setProperty("text", "1")
    _child(tab, "customAspectNameField").setProperty("text", "Panoráma")
    parbeszed.metaObject().invokeMethod(parbeszed, "accept")
    qt_app.processEvents()
    assert stub.added_ratios == [(3.0, 1.0, "Panoráma")]


# --- 6. A panelbe ágyazva ---------------------------------------------------


def test_a_panel_beallitasok_lapja_a_valodi_tartalmat_mutatja(qt_app):
    """A `CollagePanel` üres tartója helyén MOST a tényleges lap áll.

    Enélkül a lap „kész" lenne, de a felhasználó továbbra is üres hasábot
    látna — a #945 tartója némán a helyén maradna."""
    panel = _betolt(
        qt_app,
        b"""
import QtQuick
import PicasaPy 1.0
CollagePanel { objectName: "collagePanel" }
""",
        800,
        534,
        _CollageStub(),
    )
    lap = _child(panel, "collageSettingsTab")
    # a tartó geometriája SZERZŐDÉS (#945): (13, 55) 266 × 351
    sarok = lap.mapToItem(panel, QPointF(0, 0))
    assert (sarok.x(), sarok.y(), lap.width(), lap.height()) == (13, 55, 266, 351)
    # …és MOST már tartalma is van
    assert _child(lap, "collageThemePopup").isVisible()
