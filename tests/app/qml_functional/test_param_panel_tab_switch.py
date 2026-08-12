"""Az effekt-paraméter alpanel ne ragadjon be fülváltáskor — #583.

Felhasználói hibajelentés: a nyitott paraméter-panel (a képen a vignette)
másik fülre lépve is nyitva maradt, és RÁRAJZOLÓDOTT a másik fül tartalmára
(a „Gyakori javítások" csúszkái közé keveredve). Két oka volt:

1. a panel láthatósága csak a `paramPanelActive`-tól függött, a fültől nem,
   és fülváltáskor senki nem zárta be;
2. a „További effektek" (5.) és a „Régi effektek" (6.) fül — a testvér
   effekt-fülekkel ellentétben — nem rejtőzött el a nyitott alpanel alatt,
   így a saját tartalmával is egymásra rajzolódott.
"""

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine

from picasapy.app.effect_params import has_params, resolve_effect_params

_KEEPALIVE = []


class _FakeEditController(QObject):
    """Csak amit az alpanel-út hív (a test_effect_sliders.py mintája)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.discard_calls = 0

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
        pass

    @Slot()
    def discardEffectPreview(self):
        self.discard_calls += 1

    @Slot(str, "QVariantList")
    def applyEffectWithParams(self, name, values):
        pass


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _panel(engine, fake, active_tab=2):
    engine.rootContext().setContextProperty("editController", fake)
    component = QQmlComponent(engine)
    component.setData(
        (
            "import QtQuick\nimport PicasaPy 1.0\n"
            f'EditorPanel {{ objectName: "panel"; activeTab: {active_tab} }}\n'
        ).encode("utf-8"),
        QUrl(),
    )
    obj = component.create()
    assert [e.toString() for e in component.errors()] == []
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((component, obj, fake))
    return obj


def _open_param_panel(panel, qt_app, button="effectVignette"):
    QMetaObject.invokeMethod(
        panel.findChild(QObject, button), "buttonClicked",
        Qt.ConnectionType.DirectConnection,
    )
    qt_app.processEvents()
    assert panel.property("paramPanelActive") is True


class TestSwitchingTabsClosesTheParamPanel:
    def test_the_panel_closes_and_the_preview_is_discarded(
        self, qml_engine, qt_app
    ):
        fake = _FakeEditController()
        panel = _panel(qml_engine, fake)
        _open_param_panel(panel, qt_app)

        panel.setProperty("activeTab", 0)
        qt_app.processEvents()

        assert panel.property("paramPanelActive") is False
        assert panel.property("paramEffectName") == ""
        # a Mégse ága: az élő előnézet elvész, a mentett lánc érintetlen
        assert fake.discard_calls == 1

    def test_the_other_tab_is_not_covered_by_the_param_panel(
        self, qml_engine, qt_app
    ):
        fake = _FakeEditController()
        panel = _panel(qml_engine, fake)
        _open_param_panel(panel, qt_app)

        panel.setProperty("activeTab", 0)
        qt_app.processEvents()

        param_panel = panel.findChild(QObject, "editorEffectParamScroll")
        assert param_panel.property("visible") is False
        # és a „Gyakori javítások" fül LÁTSZIK, nem takarja semmi
        fixes = panel.findChild(QObject, "toolsColumn")
        assert fixes is not None
        assert fixes.property("visible") is True


class TestEveryTabHidesUnderTheParamPanel:
    """A nyitott alpanel alatt EGYETLEN fül tartalma sem látszhat."""

    @pytest.mark.parametrize(
        "tab,column,button",
        [
            (2, "effectsColumn", "effectVignette"),
            (5, "effectsColumn4", None),
            (6, "legacyEffectsColumn", None),
        ],
    )
    def test_the_tab_content_hides(self, qml_engine, qt_app, tab, column, button):
        fake = _FakeEditController()
        panel = _panel(qml_engine, fake, active_tab=tab)
        qt_app.processEvents()
        if button is not None:
            _open_param_panel(panel, qt_app, button)
        else:
            # ezeken a füleken nincs paraméteres gomb — az állapotot
            # közvetlenül állítjuk, az állítás a LÁTHATÓSÁGRÓL szól
            panel.setProperty("paramPanelActive", True)
        qt_app.processEvents()

        content = panel.findChild(QObject, column)
        assert content is not None, f"{column} nem található"
        assert content.property("visible") is False
