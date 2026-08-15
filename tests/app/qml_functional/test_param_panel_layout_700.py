"""#700: az effekt-paraméter alpanel elrendezése — KIRAJZOLT ellenőrzés.

A hiba, amit ez a fájl kizár: az alpanel öt ponton eltért az eredeti
Picasáétól, és mindet a felhasználó szemrevételezése találta meg, végig
zöld CI mellett. A legsúlyosabb a panel CÍME volt: a `filters=` lánc belső
kulcsa (`holga`) állt ott, nyersen, holott ugyanannak az effektnek a
csempéje már a helyes emberi nevét mutatta („Holga-szerű").

A mérce nem szemrevételezés: az eredeti panel elrendezését a
`docs/specs/ui-audit-editor.md` **7. szakasza** vezeti le a Picasa saját
erőforrásaiból (`respack.yt` rétegleltára és kicsomagolt bitképei,
`tre:editpanel`, `tre:fontmacros_win`, `filterdesc.xml`). Az itteni
állítások oda hivatkoznak vissza.

A mérés a #651 mintáját követi: valódi `QQuickView`, több ablakméret, az
ABLAK koordinátarendszerében mért geometria — a property-t olvasó, izolált
teszt épp azt nem látja, amit a felhasználó lát. A `Repeater` delegáltjait
a `findChild` NEM találja meg, ezért a VIZUÁLIS fát járjuk be.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtCore import Property, QMetaObject, QObject, Qt, QUrl, Slot
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickView

from picasapy.app.effect_params import has_params, resolve_effect_params

_KEEPALIVE: list[object] = []

_REPO_ROOT = Path(__file__).resolve().parents[3]
_QML_DIR = _REPO_ROOT / "src" / "picasapy" / "app" / "qml" / "PicasaPy"

#: A Holga csempéje a 4. effekt-fülön (`activeTab: 3`) — három csúszkás
#: paraméterrel; a #700 bejelentése is ezt a panelt mutatta.
_HOLGA_TAB = 3
_HOLGA_TILE = "effectHolga"
_HOLGA_KEY = "holga"


class _FakeEditController(QObject):
    """Annyi az EditControllerből, amennyitől az alpanel élesben viselkedik.

    A `previewSource` nem kényelmi részlet: enélkül a csempék bélyegkép
    nélkül, ~24 képpont magasan rajzolódnak, és a geometria mérése hamis
    biztonságot ad (a #651 tanulsága)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.preview_calls: list[tuple[str, list]] = []

    @Property(str, constant=True)
    def previewSource(self):
        return "image://editpreview/42?rev=1"

    @Property("QVariantList", constant=True)
    def legacyEffectsInChain(self):
        return []

    @Property("QVariant", constant=True)
    def legacyEffects(self):
        return []

    @Slot(str, result=bool)
    def effectHasParams(self, name):
        return has_params(name)

    @Slot(str, result="QVariant")
    def effectParams(self, name):
        return [
            {
                "key": p.key,
                "label": p.label,
                "kind": p.kind,
                "minimum": p.minimum,
                "maximum": p.maximum,
                "default": p.default,
                "step": p.step,
                "color": p.color,
            }
            for p in resolve_effect_params(name, width=1000, height=1000)
        ]

    @Slot(str, "QVariantList")
    def previewEffect(self, name, values):
        self.preview_calls.append((name, list(values)))

    @Slot()
    def discardEffectPreview(self):
        pass

    @Slot(str, "QVariantList")
    def applyEffectWithParams(self, name, values):
        pass


_PANEL_QML = """
import QtQuick
import PicasaPy 1.0
EditorPanel {{ objectName: "panel"; activeTab: {tab} }}
"""


def _view(qt_app, qml: str, width: int, height: int):
    """A QML valódi ablakban, adott mérettel — a layoutok tényleg lefutnak."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    controller = _FakeEditController()
    view.engine().rootContext().setContextProperty("editController", controller)
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)

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
    _KEEPALIVE.extend((view, root, component, controller))
    view.show()
    qt_app.processEvents()
    return root


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása — a `Repeater` delegáltjainak csak vizuális
    szülőjük van, `findChild` üres kézzel térne vissza (#650/#651)."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _maybe_child(root: QQuickItem, name: str) -> QQuickItem | None:
    for item in _walk(root):
        if item.objectName() == name:
            return item
    return None


def _child(root: QQuickItem, name: str) -> QQuickItem:
    found = _maybe_child(root, name)
    assert found is not None, f"{name} nem található a kirajzolt fában"
    return found


def _center_x(item: QQuickItem) -> float:
    """Az elem vízszintes középpontja az ABLAK koordinátarendszerében."""
    rect = item.boundingRect()
    return item.mapToScene(rect.center()).x()


def _top(item: QQuickItem) -> float:
    return item.mapToScene(item.boundingRect().topLeft()).y()


def _bottom(item: QQuickItem) -> float:
    return item.mapToScene(item.boundingRect().bottomLeft()).y()


def _open_holga(qt_app, width: int = 280, height: int = 760):
    """A Holga alpanelje a VALÓDI úton: a csempére kattintva."""
    root = _view(qt_app, _PANEL_QML.format(tab=_HOLGA_TAB), width, height)
    tile = _child(root, _HOLGA_TILE)
    QMetaObject.invokeMethod(
        tile, "buttonClicked", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    assert root.property("paramPanelActive") is True
    return root, tile


class TestTheTitleIsTheEffectName:
    """#700/1 — a cím az effekt EMBERI neve, nem a `filters=` kulcs."""

    def test_the_title_is_not_the_internal_chain_key(self, qt_app):
        root, _ = _open_holga(qt_app)

        title = _child(root, "effectParamTitle")

        assert title.property("text") != _HOLGA_KEY, (
            "a panel címe a `filters=` lánc belső kulcsa — ez nem "
            "felhasználói szöveg (#700/1)"
        )

    def test_the_title_is_exactly_what_the_tile_says(self, qt_app):
        """Nem „valamilyen szép név": UGYANAZ, ami a csempén áll.

        Ez az állítás köti össze a két forrást; ha valaki külön nevet vezet
        be az alpanelnek, itt elhasal."""
        root, tile = _open_holga(qt_app)

        title = _child(root, "effectParamTitle")

        assert title.property("text") == tile.property("label")

    def test_the_title_is_not_shouted_in_a_header_band(self, qt_app):
        """Az eredetiben (`editpanel/filter_name`) sima, nem félkövér
        szedés a panel hátterén — ld. az audit 7.1 pontját."""
        root, _ = _open_holga(qt_app)

        title = _child(root, "effectParamTitle")

        assert title.property("font").bold() is False


class TestTheParameterLabelSitsAboveTheSliderAndIsCentred:
    """#700/2 — a felirat a csúszka FÖLÖTT, KÖZÉPRE (audit 7.3)."""

    @pytest.mark.parametrize("index", [0, 1, 2])
    def test_the_label_is_above_its_slider(self, qt_app, index):
        root, _ = _open_holga(qt_app)

        label = _child(root, f"effectParamLabel{index}")
        slider = _child(root, f"effectParamSlider{index}")

        assert _bottom(label) <= _top(slider) + 0.5, (
            f"a(z) {index}. felirat nem a csúszka fölött áll"
        )

    @pytest.mark.parametrize("index", [0, 1, 2])
    @pytest.mark.parametrize("width", [280, 240, 320])
    def test_the_label_is_horizontally_centred(self, qt_app, index, width):
        """A viszonyítás a PANEL közepe, nem a tartalom-oszlopé: ha az
        oszlop maga csúszik balra, egy oszlopon belüli középre igazítás
        semmit nem ér — a felhasználó a panelt látja."""
        root, _ = _open_holga(qt_app, width=width)

        panel = _child(root, "editorEffectParamScroll")
        label = _child(root, f"effectParamLabel{index}")
        slider = _child(root, f"effectParamSlider{index}")

        assert abs(_center_x(label) - _center_x(panel)) <= 1.0, (
            f"a(z) {index}. felirat nincs a panel középvonalán "
            f"({width} px széles panelen)"
        )
        assert abs(_center_x(label) - _center_x(slider)) <= 1.0, (
            f"a(z) {index}. felirat nincs a csúszkával egy középvonalon "
            f"({width} px széles panelen)"
        )

    @pytest.mark.parametrize("index", [0, 1, 2])
    def test_the_label_box_hugs_its_text(self, qt_app, index):
        """Enélkül a középre igazítás nem lenne mérhető.

        Egy teljes szélességű doboz középpontja akkor is a panel közepén
        van, ha a SZÖVEG balra tapad benne — a fenti középvonal-állítás
        csak azért mond valamit, mert a doboz a szövegére zsugorodik."""
        root, _ = _open_holga(qt_app)

        panel = _child(root, "editorEffectParamScroll")
        label = _child(root, f"effectParamLabel{index}")

        assert 0 < label.width() < panel.width() - 40, (
            f"a(z) {index}. felirat doboza {label.width():.0f} px széles "
            f"egy {panel.width():.0f} px-es panelben — nem a szövegére "
            "méretezett, így a középre igazítás nem ellenőrizhető"
        )


class TestTheRawNumberIsGone:
    """#700/3 — az eredeti panel a csúszka értékét NEM írja ki (audit 7.2)."""

    @pytest.mark.parametrize("index", [0, 1, 2])
    def test_no_numeric_readout_is_rendered(self, qt_app, index):
        root, _ = _open_holga(qt_app)

        value = _maybe_child(root, f"effectParamValue{index}")

        assert value is None or not value.isVisible(), (
            "a nyers számérték ott áll a felirat mellett — az eredeti "
            "panel teljes rétegleltárában nincs érték-kijelző (#700/3)"
        )


class TestTheButtonRowIsCentred:
    """#700/4 — `XConstraint 0.5, 0.5, ±52`: a gombok a KÖZÉPHEZ kötve."""

    @pytest.mark.parametrize("width", [280, 240, 320])
    def test_the_two_buttons_are_symmetric_about_the_centre(self, qt_app, width):
        """A viszonyítás itt is a PANEL közepe — ld. a felirat-tesztnél."""
        root, _ = _open_holga(qt_app, width=width)

        panel = _child(root, "editorEffectParamScroll")
        apply_button = _child(root, "effectParamApplyButton")
        cancel_button = _child(root, "effectParamCancelButton")

        middle = (_center_x(apply_button) + _center_x(cancel_button)) / 2
        assert abs(middle - _center_x(panel)) <= 1.0, (
            f"a gombsor nem a panel közepén ül ({width} px széles panelen)"
        )

    def test_the_buttons_do_not_span_the_whole_panel(self, qt_app):
        """A középre igazítás csak akkor látszik, ha a gombok nem érnek
        szélről szélig — különben minden „középen" van."""
        root, _ = _open_holga(qt_app)

        panel = _child(root, "editorEffectParamScroll")
        apply_button = _child(root, "effectParamApplyButton")

        assert apply_button.width() < panel.width() * 0.45, (
            "a gomb a panel felénél szélesebb — a gombsor a teljes "
            "szélességre feszül, nem középre igazított"
        )


class TestTheButtonsCarryTheOriginalIcons:
    """#700/5 — 15×15 kör: zöld pipa / indigó X (audit 7.4)."""

    @pytest.mark.parametrize(
        "name,expected",
        [("effectParamApplyIcon", "#4e904a"), ("effectParamCancelIcon", "#524ba1")],
    )
    def test_the_icon_badge_is_visible_with_the_original_colour(
        self, qt_app, name, expected
    ):
        root, _ = _open_holga(qt_app)

        icon = _child(root, name)

        assert icon.isVisible(), f"{name} nem látszik"
        assert icon.width() > 0 and icon.height() > 0
        assert icon.property("color").name() == expected

    @pytest.mark.parametrize(
        "icon_name,button_name",
        [
            ("effectParamApplyIcon", "effectParamApplyButton"),
            ("effectParamCancelIcon", "effectParamCancelButton"),
        ],
    )
    def test_the_icon_stays_inside_its_button(self, qt_app, icon_name, button_name):
        root, _ = _open_holga(qt_app)

        icon = _child(root, icon_name)
        button = _child(root, button_name)

        icon_right = icon.mapToScene(icon.boundingRect().topRight()).x()
        button_right = button.mapToScene(button.boundingRect().topRight()).x()
        assert icon_right <= button_right + 0.5, f"{icon_name} kilóg a gombjából"


class TestTheSliderFollowsTheOriginalProportions:
    """#700/6 — 9 képpontos sín, 16×26 álló fogantyú (audit 7.5)."""

    @pytest.mark.parametrize("index", [0, 1, 2])
    def test_the_slider_reserves_room_for_the_tall_handle(self, qt_app, index):
        root, _ = _open_holga(qt_app)

        slider = _child(root, f"effectParamSlider{index}")

        assert slider.height() >= 26, (
            f"a(z) {index}. csúszka {slider.height():.0f} px magas — az "
            "eredeti fogantyúja 26 px, tehát vagy alacsonyabb a fogantyú, "
            "vagy nem foglal neki helyet a doboz (a #659 hibaosztálya)"
        )


class TestTheContentUsesTheWholePanelWidth:
    """A bejelentő megfogalmazása: „a bal szélére szorul a területnek"."""

    @pytest.mark.parametrize("width", [280, 240, 320])
    def test_the_column_is_as_wide_as_the_panel(self, qt_app, width):
        root, _ = _open_holga(qt_app, width=width)

        panel = _child(root, "editorEffectParamScroll")
        column = _child(root, "effectParamColumn")

        assert column.width() >= panel.width() - 24, (
            f"a tartalom {column.width():.0f} px széles egy "
            f"{panel.width():.0f} px-es panelben — a bal szélre szorul"
        )


class TestEveryTilePassesItsOwnLabel:
    """A cím helyessége FORRÁS-szinten is kikényszerítve.

    A futásidejű állítás csak a Holga-csempét járja be; ez a szöveges
    ellenőrzés MINDEN effekt-csempére kimondja ugyanazt, hogy egy jövőbeli
    új csempénél se lehessen elfelejteni a nevet átadni."""

    #: `panel.tryOpenParamPanel("<kulcs>"` + ami utána jön a zárójelig
    _CALL = re.compile(r'panel\.tryOpenParamPanel\((?P<args>[^)]*)\)')

    def _call_sites(self):
        for path in sorted(_QML_DIR.glob("Editor*Tab*.qml")):
            for match in self._CALL.finditer(path.read_text(encoding="utf-8")):
                yield path.name, match.group("args")

    def test_there_are_call_sites_to_check(self):
        """Néma őr ne legyen: ha a regex elavul, itt bukik el."""
        assert len(list(self._call_sites())) >= 40

    def test_every_call_site_passes_a_display_label(self):
        missing = [
            f"{name}: tryOpenParamPanel({args})"
            for name, args in self._call_sites()
            if "," not in args
        ]
        assert not missing, (
            "csempe, ami nem adja át a saját feliratát az alpanelnek — "
            "ott a panel címe a belső kulcsra esne vissza (#700/1): "
            f"{missing}"
        )
