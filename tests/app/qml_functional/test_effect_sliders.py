"""QML-funkcionális tesztek: effekt-paraméter csúszkák alpanelje (#316).

Két réteg:
- `TestParamSubpanelIsolated*`: az EditorPanel-t ÖNÁLLÓAN, a `PicasaPy 1.0`
  modulon át töltjük be (a test_editor_effects.py / test_editor_tabs.py
  mintája), egy Python-oldali FAKE `editController`-rel — ez pontosan
  ellenőrzi a csúszkák számát/alapértékét, és hogy a Fake milyen
  argumentumokkal kapja a preview/apply/discard hívásokat.
- `TestParamSubpanelIntegration`: a TELJES app (`qml_app` fixture, valós
  EditController + valós `.picasa.ini`) — az Apply/Cancel után a lánc
  (ini `filters=`) tényleges tartalmát ellenőrzi.
"""

import time

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, Qt, QUrl, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine

from picasapy.app.effect_params import effect_params, has_params

# a QML-ből létrehozott gyökér-objektumok élő Python-referencia nélkül a
# JS-motor tulajdonába kerülnek és a GC bármikor eltávolíthatja őket —
# CppOwnership-re váltva és itt megtartva éljük túl a teszt-futást
# (test_editor_effects.py mintája).
_KEEPALIVE = []


def _params_payload(name):
    """A valós katalógus (`effect_params.py`) alakja, ahogy a QML-nek az
    EditController.effectParams(...) is adná (lista dict-ekből)."""
    return [
        {
            "key": p.key,
            "label": p.label,
            "minimum": p.minimum,
            "maximum": p.maximum,
            "default": p.default,
            "step": p.step,
        }
        for p in effect_params(name)
    ]


class _FakeEditController(QObject):
    """A valós `EditController` #316-os felületének minimál-hű mása —
    csak a csúszkás alpanelhez szükséges 5 slot, a valós katalógusból
    (`effect_params.py`) táplálva, hogy a QML-oldali logikát a Python-implementáció
    érintése nélkül lehessen tesztelni."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.preview_calls = []
        self.apply_calls = []
        self.discard_calls = 0

    @Slot(str, result=bool)
    def effectHasParams(self, name):
        return has_params(name)

    @Slot(str, result="QVariant")
    def effectParams(self, name):
        return _params_payload(name)

    @Slot(str, "QVariantList")
    def previewEffect(self, name, values):
        self.preview_calls.append((name, list(values)))

    @Slot()
    def discardEffectPreview(self):
        self.discard_calls += 1

    @Slot(str, "QVariantList")
    def applyEffectWithParams(self, name, values):
        self.apply_calls.append((name, list(values)))


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _load(engine, qml_source):
    """QML-forrás betöltése inline szövegként (nincs saját fájl-URL-je)."""
    component = QQmlComponent(engine)
    component.setData(qml_source.encode("utf-8"), QUrl())
    obj = component.create()
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None, "a komponens betöltése sikertelen"
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.append(component)
    _KEEPALIVE.append(obj)
    return obj


def _make_panel(engine, fake_controller, active_tab=2):
    engine.rootContext().setContextProperty("editController", fake_controller)
    panel = _load(
        engine,
        "import QtQuick\nimport PicasaPy 1.0\n"
        f'EditorPanel {{ objectName: "panel"; activeTab: {active_tab} }}\n',
    )
    _KEEPALIVE.append(fake_controller)
    return panel


def _click(obj):
    QMetaObject.invokeMethod(obj, "buttonClicked", Qt.ConnectionType.DirectConnection)


def _grid_name_for_tab(active_tab):
    return {2: "effectsGrid", 3: "effectsGrid2", 4: "effectsGrid3"}[active_tab]


def _as_list(value):
    """A `paramEffectValues`/`paramEffectParams` property() Python felé
    hol sima listaként, hol QJSValue-ként jön (attól függően, hogy a QML
    JS futásidőben mikor materializálódott) — mindkettőt listává alakítja."""
    if hasattr(value, "toVariant"):
        return value.toVariant()
    return value


class TestParamSubpanelIsolatedOpening:
    """#316: a paraméteres effekt-gomb alpanelt nyit, a paraméter nélküli
    NEM — a fake editController a valós katalógust szolgálja ki."""

    @pytest.mark.parametrize(
        "active_tab,object_name,key,expected_count",
        [
            (2, "effectSat", "sat", 1),
            (2, "effectVignette", "vignette", 2),
            (2, "effectUnsharp", "unsharp", 1),
            (2, "effectRadblur", "radblur", 4),
            (2, "effectDirTint", "dir_tint", 4),
            (3, "effectBoost", "boost", 1),
            (4, "effectPixelate", "pixelate", 1),
            (4, "effectComicize", "comicize", 3),
        ],
    )
    def test_param_effect_click_opens_subpanel_with_right_slider_count(
        self, qml_engine, qt_app, active_tab, object_name, key, expected_count
    ):
        panel = _make_panel(qml_engine, _FakeEditController(), active_tab=active_tab)
        qt_app.processEvents()
        button = panel.findChild(QObject, object_name)
        assert button is not None, f"{object_name} hiányzik"
        _click(button)
        qt_app.processEvents()

        assert panel.property("paramPanelActive") is True
        assert panel.property("paramEffectName") == key
        sub = panel.findChild(QObject, "effectParamColumn")
        assert sub is not None
        assert sub.property("visible") is True
        # a fül eredeti rácsa eltűnik, amíg az alpanel nyitva van
        grid = panel.findChild(QObject, _grid_name_for_tab(active_tab))
        assert grid.property("visible") is False

        # a Repeater ténylegesen ennyi csúszkát hozott létre (a dinamikusan
        # létrehozott delegate-eket a Qt Quick NEM QObject-gyermekként
        # parentel, ezért itt a Repeater `count`-ját és a ténylegesen
        # betöltött érték-listát ellenőrizzük findChild helyett)
        repeater = panel.findChild(QObject, "effectParamRepeater")
        assert repeater is not None
        assert repeater.property("count") == expected_count

        expected_defaults = [p.default for p in effect_params(key)]
        actual_defaults = _as_list(panel.property("paramEffectValues"))
        assert actual_defaults == pytest.approx(expected_defaults)
        actual_params = _as_list(panel.property("paramEffectParams"))
        assert len(actual_params) == expected_count

    @pytest.mark.parametrize(
        "object_name,key",
        [
            ("effectSepia", "sepia"),
            ("effectBw", "bw"),
            ("effectWarm", "warm"),
            ("effectGrain2", "grain2"),
        ],
    )
    def test_parameterless_effect_click_does_not_open_subpanel(
        self, qml_engine, qt_app, object_name, key
    ):
        fake = _FakeEditController()
        panel = _make_panel(qml_engine, fake, active_tab=2)
        qt_app.processEvents()
        requested = []
        panel.effectRequested.connect(lambda name: requested.append(name))
        button = panel.findChild(QObject, object_name)
        assert button is not None
        _click(button)
        qt_app.processEvents()

        assert panel.property("paramPanelActive") is False
        assert requested == [key]
        assert fake.preview_calls == []

    def test_invert_on_tab4_stays_parameterless(self, qml_engine, qt_app):
        """Invert Colors a 4. fülön van — a katalógus szándékosan kihagyja
        (docs/effect_params.py fejrésze), egygombosnak kell maradnia."""
        fake = _FakeEditController()
        panel = _make_panel(qml_engine, fake, active_tab=3)
        qt_app.processEvents()
        requested = []
        panel.effectRequested.connect(lambda name: requested.append(name))
        button = panel.findChild(QObject, "effectInvert")
        _click(button)
        qt_app.processEvents()
        assert panel.property("paramPanelActive") is False
        assert requested == ["invert"]


class TestParamSubpanelIsolatedApplyCancel:
    """Apply/Cancel a fake controlleren át — a QML-oldali adatfolyam."""

    def _open(self, qml_engine, qt_app, object_name="effectSat", active_tab=2):
        fake = _FakeEditController()
        panel = _make_panel(qml_engine, fake, active_tab=active_tab)
        qt_app.processEvents()
        _click(panel.findChild(QObject, object_name))
        qt_app.processEvents()
        return panel, fake

    def test_apply_sends_current_values_and_returns_to_grid(self, qml_engine, qt_app):
        panel, fake = self._open(qml_engine, qt_app, "effectSat", active_tab=2)
        # a csúszka húzásának szimulációja: updateParamValue (ugyanaz, amit
        # a PicasaSlider onMoved hív) — 0-dik index, új érték
        QMetaObject.invokeMethod(
            panel,
            "updateParamValue",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0),
            Q_ARG("QVariant", 0.85),
        )
        apply_button = panel.findChild(QObject, "effectParamApplyButton")
        assert apply_button is not None
        _click(apply_button)
        qt_app.processEvents()

        assert fake.apply_calls == [("sat", [0.85])]
        assert panel.property("paramPanelActive") is False
        assert panel.property("paramEffectName") == ""
        grid = panel.findChild(QObject, "effectsGrid")
        assert grid.property("visible") is True

    def test_cancel_discards_preview_and_returns_to_grid(self, qml_engine, qt_app):
        panel, fake = self._open(qml_engine, qt_app, "effectVignette", active_tab=2)
        QMetaObject.invokeMethod(
            panel,
            "updateParamValue",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 1),
            Q_ARG("QVariant", 2.0),
        )
        cancel_button = panel.findChild(QObject, "effectParamCancelButton")
        assert cancel_button is not None
        _click(cancel_button)
        qt_app.processEvents()

        assert fake.discard_calls == 1
        assert fake.apply_calls == []
        assert panel.property("paramPanelActive") is False
        grid = panel.findChild(QObject, "effectsGrid")
        assert grid.property("visible") is True

    def test_opening_panel_previews_defaults_immediately(self, qml_engine, qt_app):
        """Az alpanel nyitásakor az élő előnézet AZONNAL az alapértékekkel
        induljon — ne kelljen előbb húzni egy csúszkát."""
        panel, fake = self._open(qml_engine, qt_app, "effectSat", active_tab=2)
        assert fake.preview_calls
        name, values = fake.preview_calls[-1]
        assert name == "sat"
        assert values == pytest.approx([0.5])

    def test_debounced_preview_fires_after_drag(self, qml_engine, qt_app):
        panel, fake = self._open(qml_engine, qt_app, "effectSat", active_tab=2)
        fake.preview_calls.clear()
        QMetaObject.invokeMethod(
            panel,
            "updateParamValue",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0),
            Q_ARG("QVariant", 0.9),
        )
        # a Timer (interval: 60ms) lefutásához valós idő kell — a
        # processEvents()-et ismételten hívjuk, amíg a Qt-eseményhurok a
        # QTimer lejáratát fel nem dolgozza
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline and not fake.preview_calls:
            qt_app.processEvents()
        assert fake.preview_calls == [("sat", [0.9])]


class TestParamLabelTranslationHelper:
    """#316: a csúszkák felirat-Text-jei a `paramLabel(...)` fordító-segéden
    át jelennek meg — angol forrásnyelven (nincs betöltött .qm fájl a
    tesztben) a switch minden ismert kulcsnál a bemenetet adja vissza."""

    def test_vignette_labels_pass_through_the_switch_unmodified(
        self, qml_engine, qt_app
    ):
        """Vignette: "Inner Radius" és "Strength" — a `paramLabel(...)`
        (amit a csúszka-sor felirat-Text-je hív) a valós katalógus-feliratra
        pontosan a forrásszöveget adja vissza (angol, .qm nélkül a tesztben)."""
        panel = _make_panel(qml_engine, _FakeEditController(), active_tab=2)
        qt_app.processEvents()
        for param in effect_params("vignette"):
            result = QMetaObject.invokeMethod(
                panel,
                "paramLabel",
                Qt.ConnectionType.DirectConnection,
                Q_RETURN_ARG("QVariant"),
                Q_ARG("QVariant", param.label),
            )
            assert result == param.label

    def test_all_catalogue_labels_are_covered_by_the_switch(self):
        """A #316 feladatleírás 5. pontjának teljes kulcslistája — ha az
        `effect_params.py` katalógusa bővül egy itt nem szereplő felirattal,
        ez a teszt figyelmeztet, hogy a QML `paramLabel` switch-e is bővüljön."""
        known = {
            "Amount",
            "Saturation",
            "Inner Radius",
            "Strength",
            "Intensity",
            "Radius",
            "Center X",
            "Center Y",
            "Size",
            "Sharpness",
            "Preserve Color",
            "Gradient",
            "Shade",
            "Block Size",
            "Blur Radius",
            "Brightness",
            "Color Mix",
            "Edge Strength",
            "Posterize",
            "Smoothness",
            "Width",
            "Border Width",
            "Angle",
            "Blur",
            "Line Position",
        }
        from picasapy.app.effect_params import _CATALOGUE

        used = {p.label for params in _CATALOGUE.values() for p in params}
        assert used <= known, f"ismeretlen felirat(ok): {used - known}"


class TestParamSubpanelIntegration:
    """Teljes app, valós EditController — a `.picasa.ini` tényleges
    tartalmát ellenőrzi Apply/Cancel után."""

    def _open_viewer(self, window, qt_app, index=0):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", index)
        qt_app.processEvents()
        return viewer

    def _open_effects_tab(self, window, qt_app):
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None
        panel.setProperty("activeTab", 2)
        qt_app.processEvents()
        return panel

    def test_apply_writes_the_configured_value_to_the_chain(
        self, qml_app, qt_app, tmp_path
    ):
        window, _controller, _engine = qml_app
        panel = self._open_effects_tab(window, qt_app)

        _click(panel.findChild(QObject, "effectSat"))
        qt_app.processEvents()
        assert panel.property("paramPanelActive") is True

        QMetaObject.invokeMethod(
            panel,
            "updateParamValue",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0),
            Q_ARG("QVariant", 0.75),
        )
        _click(panel.findChild(QObject, "effectParamApplyButton"))
        qt_app.processEvents()

        assert panel.property("paramPanelActive") is False
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=sat=1,0.750000;" in ini_text

    def test_cancel_leaves_the_chain_empty(self, qml_app, qt_app, tmp_path):
        window, _controller, _engine = qml_app
        panel = self._open_effects_tab(window, qt_app)

        _click(panel.findChild(QObject, "effectVignette"))
        qt_app.processEvents()
        assert panel.property("paramPanelActive") is True

        QMetaObject.invokeMethod(
            panel,
            "updateParamValue",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 1),
            Q_ARG("QVariant", 2.5),
        )
        _click(panel.findChild(QObject, "effectParamCancelButton"))
        qt_app.processEvents()

        assert panel.property("paramPanelActive") is False
        ini_path = tmp_path / "kepek" / ".picasa.ini"
        ini_text = ini_path.read_text(encoding="utf-8") if ini_path.exists() else ""
        assert "Vignette" not in ini_text
        assert "filters=" not in ini_text
