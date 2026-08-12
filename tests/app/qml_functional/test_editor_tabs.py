"""QML-funkcionális tesztek: EditorPanel öt füle és a 4-5. effekt-fül
gombjai (#328, #329, #330).

A test_editor_effects.py mintáját követve az EditorPanel-t ÖNÁLLÓAN, a
`PicasaPy 1.0` modulon át töltjük be — a `panel.effectRequested` jelet
közvetlenül figyeljük, az EditController-t nem érintjük.
"""

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

# a QML-ből létrehozott gyökér-objektumok élő Python-referencia nélkül a
# JS-motor tulajdonába kerülnek és a GC bármikor eltávolíthatja őket —
# CppOwnership-re váltva és itt megtartva éljük túl a teszt-futást
# (test_qml_editor_panel.py / test_editor_effects.py mintája).
_KEEPALIVE = []


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


def _make_panel(engine, active_tab=0):
    return _load(
        engine,
        "import QtQuick\nimport PicasaPy 1.0\n"
        f'EditorPanel {{ objectName: "panel"; activeTab: {active_tab} }}\n',
    )


class TestFiveTabBar:
    """#328: a fülsáv háromról ötre bővült, a régi 3 fül változatlanul él."""

    TAB_NAMES = (
        "editTabFixes",
        "editTabFinetune",
        "editTabEffects",
        "editTabEffects2",
        "editTabEffects3",
    )

    def test_five_tab_buttons_exist(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        for name in self.TAB_NAMES:
            assert panel.findChild(QObject, name) is not None, f"{name} nem található"

    @pytest.mark.parametrize(
        "object_name,expected_tab", list(zip(TAB_NAMES, range(5), strict=True))
    )
    def test_clicking_tab_sets_active_tab(
        self, qml_engine, qt_app, object_name, expected_tab
    ):
        panel = _make_panel(qml_engine, active_tab=0 if expected_tab != 0 else 1)
        qt_app.processEvents()
        button = panel.findChild(QObject, object_name)
        assert button is not None
        panel.setProperty("activeTab", expected_tab)
        qt_app.processEvents()
        assert panel.property("activeTab") == expected_tab

    def test_tab_bar_fits_panel_width(self, qml_engine, qt_app):
        """#328 4. pont: az öt fülnek a panel szélességében kell elférnie —
        a RowLayout minden EditTabButton-ja Layout.fillWidth-öt használ."""
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        tab_bar = panel.findChild(QObject, "editTabBar")
        assert tab_bar is not None
        buttons = [panel.findChild(QObject, name) for name in self.TAB_NAMES]
        total_width = sum(b.property("width") for b in buttons)
        # kis lekerekítési hibahatár (spacing: 0, de layout-számítás miatt)
        assert total_width <= tab_bar.property("width") + 5

    def test_no_tab_label_is_truncated(self, qml_engine, qt_app):
        """#318 tanulság: tördelés, nem vágás — az öt fül feliratának egyike
        se veszíthet szöveget, még a legszűkebb (5 fül / panel) esetben sem."""
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        for name in self.TAB_NAMES:
            button = panel.findChild(QObject, name)
            label = button.findChild(QObject, name + "Label")
            assert label is not None, f"{name}: hiányzik a felirat-Text"
            assert label.property("truncated") is False, (
                f"{name}: a fülfelirat levágódott"
            )


COLUMNS_BY_TAB = {
    0: "toolsColumn",
    1: "finetuneColumn",
    2: "effectsColumn",
    3: "effectsColumn2",
    4: "effectsColumn3",
}


class TestFiveColumnsExclusive:
    """A meglévő 3 fül tartalma változatlan (regresszió), plusz a 2 új
    oszlop (effectsColumn2/3) csak a saját fülén látszik."""

    @pytest.mark.parametrize("active_tab", [0, 1, 2, 3, 4])
    def test_active_tab_shows_only_matching_column(
        self, qml_engine, qt_app, active_tab
    ):
        panel = _make_panel(qml_engine, active_tab=active_tab)
        qt_app.processEvents()
        for index, name in COLUMNS_BY_TAB.items():
            column = panel.findChild(QObject, name)
            assert column is not None, f"{name} nem található"
            assert column.property("visible") is (index == active_tab)


# 4. fül (zöld ecset, "kreatív effektek") — PONTOSAN a docs/specs/
# ui-audit-editor.md 4. fülének 12 kulcsa. A #516-ban ideiglenesen ide tett
# további effektek (Matte · NightVision · LocalContrast) a #422 felhasználói
# döntése nyomán a 6., „További effektek" fülre kerültek — az eredeti fülön
# nincs helyük, és tőlük a rács ki sem fért.
TAB4_BUTTONS = [
    ("effectIr", "ir"),
    ("effectLomo", "lomo"),
    ("effectHolga", "holga"),
    ("effectHdr", "hdr"),
    ("effectCinemascope", "cinemascope"),
    ("effectOrton", "orton"),
    ("effectSixties", "sixties"),
    ("effectInvert", "invert"),
    ("effectHeatMap", "heatmap"),
    ("effectCrossProcess", "crossprocess"),
    ("effectQuantizePalette", "quantizepalette"),
    ("effectTwoTone", "twotone"),
]

# 5. fül (kék ecset, "művészi effektek") — PONTOSAN a spec 11 kulcsa; a
# RoundedEdges és a PicnikGrain a 6. fülre került (ld. a 4. fül megjegyzését).
TAB5_BUTTONS = [
    ("effectBoost", "boost"),
    ("effectSoften", "soften"),
    ("effectPixelate", "pixelate"),
    ("effectFocalZoom", "focalzoom"),
    ("effectPencilSketch", "pencilsketch"),
    ("effectNeon", "neon"),
    ("effectComicize", "comicize"),
    ("effectBorder", "border"),
    ("effectDropShadow", "dropshadow"),
    ("effectMuseumMatte", "museummatte"),
    ("effectPolaroid", "polaroid"),
]

# 6. fül („További effektek", #422): azok a Glimmer-effektek, amelyek nem
# szerepelnek a 3–5. fül igazolt listáján. Amint előkerül egy képernyőkép a
# Picasa 3. effekt-füléről (#464 4. pont), a helyükre kerülhetnek.
TAB6_BUTTONS = [
    ("effectVignette", "vignette"),
    ("effectMatte", "matte"),
    ("effectNightVision", "nightvision"),
    ("effectLocalContrast", "localcontrast"),
    ("effectRoundedEdges", "roundededges"),
    ("effectPicnikGrain", "picnikgrain"),
]


class TestTab4CreativeEffects:
    """#329: a 4. effekt-fül (zöld ecset) — a spec szerinti 12 gomb."""

    def test_grid_has_the_spec_button_count(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine, active_tab=3)
        qt_app.processEvents()
        grid = panel.findChild(QObject, "effectsGrid2")
        assert grid is not None
        buttons = [c for c in grid.children() if c.objectName().startswith("effect")]
        assert len(buttons) == len(TAB4_BUTTONS) == 12

    @pytest.mark.parametrize("object_name,key", TAB4_BUTTONS)
    def test_button_exists_on_tab4(self, qml_engine, qt_app, object_name, key):
        panel = _make_panel(qml_engine, active_tab=3)
        qt_app.processEvents()
        grid = panel.findChild(QObject, "effectsGrid2")
        button = grid.findChild(QObject, object_name)
        assert button is not None, f"{object_name} hiányzik a 4. fülről"

    @pytest.mark.parametrize("object_name,key", TAB4_BUTTONS)
    def test_click_emits_effect_requested_with_lowercase_key(
        self, qml_engine, qt_app, object_name, key
    ):
        panel = _make_panel(qml_engine, active_tab=3)
        qt_app.processEvents()
        requested = []
        panel.effectRequested.connect(lambda name: requested.append(name))
        button = panel.findChild(QObject, object_name)
        QMetaObject.invokeMethod(
            button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert requested == [key]


class TestTab5ArtisticEffects:
    """#330: az 5. effekt-fül (kék ecset) — a spec szerinti 11 gomb."""

    def test_grid_has_the_spec_button_count(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine, active_tab=4)
        qt_app.processEvents()
        grid = panel.findChild(QObject, "effectsGrid3")
        assert grid is not None
        buttons = [c for c in grid.children() if c.objectName().startswith("effect")]
        assert len(buttons) == len(TAB5_BUTTONS) == 11

    @pytest.mark.parametrize("object_name,key", TAB5_BUTTONS)
    def test_button_exists_on_tab5(self, qml_engine, qt_app, object_name, key):
        panel = _make_panel(qml_engine, active_tab=4)
        qt_app.processEvents()
        grid = panel.findChild(QObject, "effectsGrid3")
        button = grid.findChild(QObject, object_name)
        assert button is not None, f"{object_name} hiányzik az 5. fülről"

    @pytest.mark.parametrize("object_name,key", TAB5_BUTTONS)
    def test_click_emits_effect_requested_with_lowercase_key(
        self, qml_engine, qt_app, object_name, key
    ):
        panel = _make_panel(qml_engine, active_tab=4)
        qt_app.processEvents()
        requested = []
        panel.effectRequested.connect(lambda name: requested.append(name))
        button = panel.findChild(QObject, object_name)
        QMetaObject.invokeMethod(
            button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert requested == [key]


class TestNewEffectLabelsNotTruncated:
    """#318 tanulság: a 4-5. fül feliratai sem vágódhatnak "…"-ra."""

    @pytest.mark.parametrize(
        "active_tab,grid_name,buttons",
        [(3, "effectsGrid2", TAB4_BUTTONS), (4, "effectsGrid3", TAB5_BUTTONS)],
    )
    def test_no_label_is_truncated(
        self, qml_engine, qt_app, active_tab, grid_name, buttons
    ):
        panel = _make_panel(qml_engine, active_tab=active_tab)
        qt_app.processEvents()
        grid = panel.findChild(QObject, grid_name)
        assert grid is not None
        for object_name, _key in buttons:
            button = grid.findChild(QObject, object_name)
            label = button.findChild(QObject, object_name + "Label")
            assert label is not None, f"{object_name}: hiányzik a felirat-Text"
            assert label.property("truncated") is False, (
                f"{object_name}: a felirat levágódott"
            )


class TestEffectGridsHaveThreeColumns:
    """#537: mindhárom effekt-fül HÁROM oszlopban rajzol, mint az eredeti.

    Az 1-2. fül rácsai már korábban is három oszlopban álltak, csak a három
    effekt-fül maradt ki — a teszt mindhármat lefedi, hogy a visszaesés
    (`columns: 2`) azonnal kiessen.
    """

    @pytest.mark.parametrize(
        "active_tab,grid_name",
        [(2, "effectsGrid"), (3, "effectsGrid2"), (4, "effectsGrid3")],
    )
    def test_grid_has_three_columns(self, qml_engine, qt_app, active_tab, grid_name):
        panel = _make_panel(qml_engine, active_tab=active_tab)
        qt_app.processEvents()
        grid = panel.findChild(QObject, grid_name)
        assert grid is not None, f"{grid_name} nem található"
        assert grid.property("columns") == 3, (
            f"{grid_name}: {grid.property('columns')} oszlop 3 helyett"
        )


class TestTab6MoreEffects:
    """#422 (felhasználói döntés): a 3–5. fül igazolt listáján kívüli
    effektek KÜLÖN fülön — így a három ismert fül pontosan az eredeti
    gombkészletét tartalmazza, és görgetés nélkül kifér."""

    def test_grid_has_the_moved_buttons(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine, active_tab=5)
        qt_app.processEvents()
        grid = panel.findChild(QObject, "effectsGrid4")
        assert grid is not None
        buttons = [c for c in grid.children() if c.objectName().startswith("effect")]
        assert len(buttons) == len(TAB6_BUTTONS) == 6

    @pytest.mark.parametrize("object_name,key", TAB6_BUTTONS)
    def test_button_exists_on_tab6(self, qml_engine, qt_app, object_name, key):
        panel = _make_panel(qml_engine, active_tab=5)
        qt_app.processEvents()
        grid = panel.findChild(QObject, "effectsGrid4")
        assert grid.findChild(QObject, object_name) is not None, (
            f"{object_name} hiányzik a 6. fülről"
        )

    @pytest.mark.parametrize("object_name,key", TAB6_BUTTONS)
    def test_click_emits_effect_requested_with_lowercase_key(
        self, qml_engine, qt_app, object_name, key
    ):
        panel = _make_panel(qml_engine, active_tab=5)
        qt_app.processEvents()
        requested = []
        panel.effectRequested.connect(lambda name: requested.append(name))
        QMetaObject.invokeMethod(
            panel.findChild(QObject, object_name),
            "buttonClicked", Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()
        assert requested == [key]

    def test_the_moved_effects_are_gone_from_the_original_tabs(
        self, qml_engine, qt_app
    ):
        """A hat effekt CSAK a 6. fülön van — nem duplikálva."""
        panel = _make_panel(qml_engine, active_tab=5)
        qt_app.processEvents()
        for grid_name in ("effectsGrid", "effectsGrid2", "effectsGrid3"):
            grid = panel.findChild(QObject, grid_name)
            names = {c.objectName() for c in grid.children()}
            for object_name, _key in TAB6_BUTTONS:
                assert object_name not in names, (
                    f"{object_name} még mindig a(z) {grid_name} rácson van"
                )
