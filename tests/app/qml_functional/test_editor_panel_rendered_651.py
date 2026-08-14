"""A szerkesztő-panel KIRAJZOLVA, a valós néző-elrendezésben — #651/1.

Miért ez a fájl létezik: a meglévő QML-tesztek komponenseket töltenek be
izoláltan, és property-ket olvasnak. Egyik sem rajzol ki semmit, és egyik
sem látja a SZÜLŐ geometriáját. Emiatt csúszott át két olyan hiba, amit a
felhasználó ránézésre azonnal észrevett:

- #641: a Visszavonás/Újra sor a szülő layout túlnyúlása miatt lecsúszott
  a képernyőről. A panelen BELÜL minden rendben volt — a meglévő teszt
  ezért zöld maradt.
- #650: minden csúszkás paraméter alatt megjelent egy oda nem való
  jelölőnégyzet és színpaletta is. A fájl KOMMENTJE leírta, hogy csak az
  egyik látszik; a kód nem valósította meg, és semmi nem állította.

Ezek a tesztek ezért valódi `QQuickWindow`-ba töltenek (a layoutok tényleg
lefutnak), és az ABLAK koordinátarendszerében kérdeznek: ott van-e, amit a
felhasználó lát. Nem képpontokat hasonlítunk — az törékeny lenne —, hanem
a leképezett geometriát és a láthatóságot.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QUrl, Property
from PySide6.QtQuick import QQuickItem, QQuickView

_KEEPALIVE: list[object] = []


class _EditControllerStub(QObject):
    """Annyi az EditControllerből, amennyitől a csempék BÉLYEGKÉPESEK.

    Ez nem kényelmi részlet: bélyegkép nélkül a csempe 24 képpont magas,
    élesben viszont ~98. A #641 küszöbe (a panel teljes igénye) emiatt 404
    helyett 504 — a bélyegkép nélküli mérés hamis biztonságot adott.
    """

    @Property(str, constant=True)
    def previewSource(self):
        return "image://editpreview/42?rev=1"

    @Property("QVariantList", constant=True)
    def legacyEffectsInChain(self):
        return []


def _view(qt_app, qml: str, width: int, height: int) -> QQuickView:
    """A QML valódi ablakban, adott mérettel — a layoutok lefuttatva."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    stub = _EditControllerStub()
    view.engine().rootContext().setContextProperty("editController", stub)
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    view.setInitialProperties({})
    view.setSource(QUrl())
    view.engine().clearComponentCache()

    from PySide6.QtQml import QQmlComponent

    component = QQmlComponent(view.engine())
    component.setData(qml.encode("utf-8"), QUrl())
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(width, height)
    root.setWidth(width)
    root.setHeight(height)
    _KEEPALIVE.extend((view, root, stub, component))
    view.show()
    return view, root


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása.

    A `findChild` itt nem elég: a `Repeater` által létrehozott elemeknek
    nincs QObject-szülőjük, csak vizuális szülőjük — a #650 vezérlői
    pontosan ilyenek. Aki `findChild`-dal keresi őket, üres kézzel tér
    vissza, és könnyen arra jut, hogy „nincs is ott" — holott a
    felhasználó látja őket a képernyőn.
    """
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


def _bottom_in_window(item: QQuickItem) -> float:
    """Az elem aljának Y-koordinátája az ABLAK rendszerében."""
    scene_point = item.mapToScene(item.boundingRect().bottomLeft())
    return scene_point.y()


#: A néző elrendezésének HŰ mása: felső sáv + a bal panel dobozzal.
#: Szándékosan nem a PhotoViewer.qml egésze (az kontrollert és modellt
#: kérne) — a #641 szempontjából a lényeg a beágyazás ALAKJA.
_VIEWER_QML = """
import QtQuick
import QtQuick.Layouts
import PicasaPy 1.0
Item {{
    objectName: "viewerRoot"
    readonly property real minimumUsableHeight:
        topBar.height + editorPanel.implicitHeight
    ColumnLayout {{
        anchors.fill: parent
        spacing: 0
        Rectangle {{ id: topBar; Layout.fillWidth: true; height: 46 }}
        RowLayout {{
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0
            Rectangle {{
                objectName: "panelBox"
                Layout.preferredWidth: 280
                Layout.fillHeight: true
                {overflow}
                EditorPanel {{
                    id: editorPanel
                    objectName: "viewerEditorPanel"
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    activeTab: {tab}
                }}
            }}
            Item {{ Layout.fillWidth: true; Layout.fillHeight: true }}
        }}
    }}
}}
"""

#: A doboz TÚLNYÚLÁSÁT előidéző sor. Ez állt a `PhotoViewer.qml`-ben a
#: #641 előtt: jó szándékkal („kapja meg a panel, amennyit kér"), de a
#: layout nem zsugorít, hanem kilógat — és a panel aljához kötött gombsor
#: vele együtt csúszott le a képernyőről.
_OVERFLOWING_PARENT = "Layout.minimumHeight: editorPanel.implicitHeight"


def _viewer_qml(tab: int = 2, *, overflowing_parent: bool = False) -> str:
    return _VIEWER_QML.format(
        tab=tab,
        overflow=_OVERFLOWING_PARENT if overflowing_parent else "",
    )


class TestTheUndoRowIsAlwaysOnScreen:
    """#641 — a hiba, ami a panelen BELÜLRŐL nézve nem látszott."""

    @pytest.mark.parametrize("height", [900, 700, 560, 480, 400, 320])
    def test_the_undo_row_stays_within_the_window(self, qt_app, height):
        view, root = _view(qt_app, _viewer_qml(2), 1200, height)

        row = _child(root, "editorGlobalUndoRow")
        bottom = _bottom_in_window(row)

        assert bottom <= height + 0.5, (
            f"{height} px magas ablakban a Visszavonás/Újra sor alja "
            f"{bottom:.0f} px-nél van — lecsúszott a képernyőről (#641)"
        )

    @pytest.mark.parametrize("height", [900, 560, 400, 320])
    def test_the_undo_buttons_have_a_real_size(self, qt_app, height):
        """Nem elég a helyén lennie: látszania is kell."""
        view, root = _view(qt_app, _viewer_qml(2), 1200, height)

        for name in ("editUndoButton", "editRedoButton"):
            button = _child(root, name)
            assert button.width() > 0 and button.height() > 0, (
                f"{name} nulla méretű {height} px magas ablakban"
            )

    @pytest.mark.parametrize("height", [900, 700, 560, 480, 400, 320])
    def test_the_panel_box_never_overflows_the_window(self, qt_app, height):
        """A #641 PONTOS mechanizmusa, közvetlenül mérve.

        A gombsor a panel aljához van kötve, tehát ha a panel doboza
        túlnyúlik az ablakon, a gombok velük együtt csúsznak le. A
        `PhotoViewer`-ben ezt egy `Layout.minimumHeight` okozta: a layout
        nem zsugorít az alá, hanem KILÓGAT.

        Ez az őr azt méri, ami a hibát okozta — nem azt, hogy épp most
        hogyan van megoldva."""
        view, root = _view(qt_app, _viewer_qml(2), 1200, height)

        box = _child(root, "panelBox")
        bottom = _bottom_in_window(box)

        assert bottom <= height + 0.5, (
            f"a panel doboza {bottom:.0f} px-ig ér egy {height} px magas "
            "ablakban — túlnyúlik, és a gombsort magával viszi (#641)"
        )

    def test_an_overflowing_parent_is_what_the_bug_looked_like(self, qt_app):
        """A hibás alak MÉG MINDIG hibás — az őrnek van foga.

        Ha ez a teszt egyszer elbukik (azaz a túlnyúló szülő mellett is
        minden rendben lenne), akkor a fenti őr elvesztette az értelmét,
        és felül kell vizsgálni. Egy néma őr rosszabb a semminél."""
        view, root = _view(
            qt_app, _viewer_qml(2, overflowing_parent=True), 1200, 320
        )

        row = _child(root, "editorGlobalUndoRow")

        assert _bottom_in_window(row) > 320, (
            "a túlnyúló szülő már nem idézi elő a hibát — az őr "
            "feltételezései elavultak, vizsgáld felül"
        )

    def test_the_thumbnailed_tiles_drive_the_requirement(self, qt_app):
        """A bélyegképes csempe ~98 px — enélkül a mérés hamisan megnyugtat.

        Ez az állítás azt őrzi, hogy a STUB tényleg bekapcsolja a
        bélyegképeket; ha elromlik, a fenti tesztek észrevétlenül
        elveszítik az élüket."""
        view, root = _view(qt_app, _viewer_qml(2), 1200, 900)

        panel = _child(root, "viewerEditorPanel")

        assert panel.property("implicitHeight") > 450, (
            "a csempék bélyegkép nélkül alacsonyak — a stub nem ér el a "
            "panelig, és a küszöb-tesztek elvesztették az értelmüket"
        )


class TestTheWindowMinimumCarriesTheGuarantee:
    """#641 — a garancia HELYE: az ablak minimális magassága."""

    def test_the_panel_fits_at_the_declared_minimum(self, qt_app):
        view, root = _view(qt_app, _viewer_qml(2), 1200, 900)
        minimum = root.property("minimumUsableHeight")

        view2, root2 = _view(qt_app, _viewer_qml(2), 1200, int(minimum))

        row = _child(root2, "editorGlobalUndoRow")
        assert _bottom_in_window(row) <= minimum + 0.5, (
            "a bejelentett minimális magasságon sem fér el a gombsor — "
            "akkor a minimum számítása hibás"
        )

    def test_no_tab_needs_scrolling_at_the_minimum(self, qt_app):
        """Az eredeti Picasa `editpanel/` névterében EGYETLEN görgető elem
        sincs — a minimális magasságon egyik fülnek sem szabad görgetnie."""
        for tab in range(7):
            view, root = _view(qt_app, _viewer_qml(tab), 1200, 900)
            minimum = root.property("minimumUsableHeight")
            view2, root2 = _view(qt_app, _viewer_qml(tab), 1200, int(minimum))

            panel = _child(root2, "viewerEditorPanel")
            tab_area = panel.findChild(QObject, "editorTabArea")
            if tab_area is None:
                continue  # a fülterület nem külön elem — nincs mit görgetni
            content = tab_area.property("contentHeight")
            if content is None:
                continue
            assert content <= tab_area.property("height") + 0.5, (
                f"a(z) {tab}. fül görgetne a minimális magasságon"
            )


class TestEveryParameterShowsExactlyOneControl:
    """#650 — a komment leírta, a kód nem csinálta, semmi nem állította."""

    _PARAM_QML = """
import QtQuick
import PicasaPy 1.0
EditorPanel { objectName: "panel"; width: 280; height: 700 }
"""

    #: A Holga katalógus-bejegyzése (`effect_params.py`): három csúszka,
    #: egyetlen jelölőnégyzet és színválasztó nélkül.
    _HOLGA = [
        {
            "key": "blur", "label": "Blur", "kind": "slider",
            "minimum": 0, "maximum": 100, "step": 1, "default": 70,
        },
        {
            "key": "grain", "label": "Grain", "kind": "slider",
            "minimum": 0, "maximum": 100, "step": 1, "default": 30,
        },
        {
            "key": "fade", "label": "Fade", "kind": "slider",
            "minimum": 0, "maximum": 100, "step": 1, "default": 0,
        },
    ]

    def _panel(self, qt_app):
        # az alpanel állapota FUTÁSIDŐBEN kapcsolódik: a panel a
        # létrehozáskori értékeket felülírja (`onActiveTabChanged` →
        # `cancelParamPanel`), ezért utólag állítjuk — a #616-os teszt
        # ugyanezt a mintát követi
        view, root = _view(qt_app, self._PARAM_QML, 280, 700)
        root.setProperty("paramEffectName", "holga")
        root.setProperty("paramEffectParams", self._HOLGA)
        root.setProperty("paramPanelActive", True)
        return root

    @pytest.mark.parametrize("index", [0, 1, 2])
    def test_a_slider_parameter_shows_no_checkbox_or_colour_picker(
        self, qt_app, index
    ):
        panel = self._panel(qt_app)

        checkbox = _child(panel, f"effectParamCheckbox{index}")
        colours = _child(panel, f"effectParamColor{index}")

        assert not checkbox.isVisible(), (
            f"a(z) {index}. csúszkás paraméter alatt jelölőnégyzet látszik"
        )
        assert not colours.isVisible(), (
            f"a(z) {index}. csúszkás paraméter alatt SZÍNVÁLASZTÓ látszik — "
            "ez a #650, és nem csak csúnya: a palettára kattintva hex "
            "string kerül a numerikus paraméter helyére"
        )

    @pytest.mark.parametrize("index", [0, 1, 2])
    def test_the_slider_itself_is_visible(self, qt_app, index):
        panel = self._panel(qt_app)

        assert _child(panel, f"effectParamSlider{index}").isVisible()
