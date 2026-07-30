"""QML-funkcionális tesztek: EditorPanel effekt-gombjai és a PanelButton
belső komponens (#314, #315, #318).

A `test_qml_editor_panel.py` (tests/app/) mintáját követve az EditorPanel-t
ÖNÁLLÓAN, a `PicasaPy 1.0` modulon át töltjük be — nem a teljes `qml_app`-on
keresztül. Ennek oka: a #315 két új gombja (`unsharp`/`vignette`) a
`panel.effectRequested` jelet a valós appban az `EditController.applyEffect`
fogadná, de annak Python-oldali `_EFFECT_NAMES` fehérlistája ezt a két
kulcsot MÉG NEM ismeri (ld. a jelentés "nyitva maradt" pontját) — a teljes
appon át kattintva a slot ValueError-t dobna. Az izolált betöltés a
`panel.effectRequested` jelet közvetlenül figyeli, az EditController-t
egyáltalán nem érinti.
"""

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

# a QML-ből létrehozott gyökér-objektumok élő Python-referencia nélkül a
# JS-motor tulajdonába kerülnek és a GC bármikor eltávolíthatja őket —
# CppOwnership-re váltva és itt megtartva éljük túl a teszt-futást
# (test_qml_editor_panel.py mintája).
_KEEPALIVE = []

# WCAG-nél lazább, de a régi hibát (kontraszt ~1.16, ld. jelentés) messze
# elválasztó küszöb — a jelenlegi token-párok mind 3.4 fölött teljesítenek.
_MIN_CONTRAST = 3.0


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


def _make_panel(engine):
    return _load(
        engine,
        "import QtQuick\nimport PicasaPy 1.0\n"
        'EditorPanel { objectName: "panel"; activeTab: 2 }\n',
    )


def _luminance(color):
    """Relatív fényesség (WCAG-képlet) egy QColor-ból."""

    def channel(value):
        c = value / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return (
        0.2126 * channel(color.red())
        + 0.7152 * channel(color.green())
        + 0.0722 * channel(color.blue())
    )


def _contrast_ratio(color_a, color_b):
    lum_a, lum_b = _luminance(color_a), _luminance(color_b)
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


class TestMissingEffectButtons:
    """#315: a render/chain.py `_HANDLERS` ismeri az "unsharp" (Élesítés) és
    "vignette" render-opokat, de az Effektek fülön nem volt hozzájuk gomb."""

    def test_sharpen_and_vignette_buttons_exist(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        assert panel.findChild(QObject, "effectUnsharp") is not None, (
            "hiányzik az Élesítés (unsharp) gomb"
        )
        assert panel.findChild(QObject, "effectVignette") is not None, (
            "hiányzik a Vignette gomb"
        )

    def test_effects_grid_has_thirteen_buttons(self, qml_engine, qt_app):
        """A korábbi 11 + a két új (#315) = 13."""
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        grid = panel.findChild(QObject, "effectsGrid")
        assert grid is not None
        buttons = [c for c in grid.children() if c.objectName().startswith("effect")]
        assert len(buttons) == 13

    def test_sharpen_is_first_and_vignette_is_last(self, qml_engine, qt_app):
        """Az eredeti Picasa Effektek fülén az Élesítés az ELSŐ gomb; a
        Vignette a rács végére kerül, a Graduated Tint (dir_tint) után."""
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        grid = panel.findChild(QObject, "effectsGrid")
        buttons = [c for c in grid.children() if c.objectName().startswith("effect")]
        assert buttons[0].objectName() == "effectUnsharp"
        assert buttons[-1].objectName() == "effectVignette"
        assert buttons[-2].objectName() == "effectDirTint"

    @pytest.mark.parametrize(
        "object_name,key",
        [("effectUnsharp", "unsharp"), ("effectVignette", "vignette")],
    )
    def test_click_emits_effect_requested_with_lowercase_key(
        self, qml_engine, qt_app, object_name, key
    ):
        """A render/chain.py `_HANDLERS` kulcsai kisbetűsek (a "vignette" is,
        holott az ini-ben a szűrő neve nagybetűs "Vignette") — a QML-gomb
        ugyanígy kisbetűvel küldi az effectRequested jelet, a többi effekt
        mintáját követve (#20)."""
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        requested = []
        panel.effectRequested.connect(lambda name: requested.append(name))
        button = panel.findChild(QObject, object_name)
        QMetaObject.invokeMethod(
            button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert requested == [key]


class TestEffectLabelsInRealGrid:
    """#318 integrációs ellenőrzés: a valós 2 oszlopos effekt-rácsban egyik
    felirat sem vágódik "…"-ra — beleértve a hosszabb magyar fordításokat
    kapó gombokat is (pl. Focal Saturation -> "Fókuszos FF")."""

    def test_no_effect_button_label_is_truncated(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        grid = panel.findChild(QObject, "effectsGrid")
        buttons = [c for c in grid.children() if c.objectName().startswith("effect")]
        assert buttons, "nincsenek effekt-gombok a rácsban"
        for button in buttons:
            label = button.findChild(QObject, button.objectName() + "Label")
            assert label is not None, f"{button.objectName()}: hiányzik a felirat-Text"
            assert label.property("truncated") is False, (
                f"{button.objectName()}: a felirat levágódott"
            )


class TestPanelButtonDarkThemeContrast:
    """#314: a PanelButton korábban fix "#fdfdfd"/"#d8d8d8"/"#ececec" hátteret
    és "#9a968e" tiltott-szöveget használt. Sötét témában a háttér világos
    maradt, a felirat (Theme.textDark = világos "ink") pedig szintén világos
    lett — a kontrasztarányuk ~1.16 (gyakorlatilag olvashatatlan). A
    token-alapú háttér (Theme.buttonBg/Theme.chromeBg) mindkét témán jóval
    a küszöb fölötti kontrasztot ad."""

    def _make_button(self, engine, dark, enabled):
        return _load(
            engine,
            "import QtQuick\nimport QtQuick.Layouts\nimport PicasaPy 1.0\n"
            "ColumnLayout {\n"
            f"    Component.onCompleted: Theme.dark = {str(dark).lower()}\n"
            "    EditorPanel.PanelButton {\n"
            '        id: btn\n'
            '        objectName: "btn"\n'
            "        Layout.fillWidth: true\n"
            '        label: "Teszt felirat"\n'
            f"        buttonEnabled: {str(enabled).lower()}\n"
            "    }\n"
            "}\n",
        )

    @pytest.mark.parametrize("dark", [False, True])
    @pytest.mark.parametrize("enabled", [True, False])
    def test_label_readable_on_button_background(
        self, qml_engine, qt_app, dark, enabled
    ):
        root = self._make_button(qml_engine, dark, enabled)
        qt_app.processEvents()
        button = root.findChild(QObject, "btn")
        label = root.findChild(QObject, "btnLabel")
        contrast = _contrast_ratio(
            button.property("color"), label.property("color")
        )
        assert contrast >= _MIN_CONTRAST, (
            f"dark={dark}, enabled={enabled}: a gomb felirata nem elég "
            f"kontrasztos a háttérhez képest (arány={contrast:.2f})"
        )


class TestPanelButtonLabelWrapping:
    """#318: a felirat korábban `elide: Text.ElideRight`-tal "…"-ra vágódott
    keskeny gombnál (pl. "Filmszemcse", "Színátmenet", "Fókuszos FF" a
    magyar fordításban). Most `wrapMode: Text.WordWrap` + a feliratból
    számolt dinamikus magasság — a szöveg sortörést kap, nem vágást."""

    def _make_button(self, engine, width, label):
        return _load(
            engine,
            "import QtQuick\nimport QtQuick.Layouts\nimport PicasaPy 1.0\n"
            f"ColumnLayout {{\n    width: {width}\n"
            "    EditorPanel.PanelButton {\n"
            '        id: btn\n'
            '        objectName: "btn"\n'
            "        Layout.fillWidth: true\n"
            f'        label: "{label}"\n'
            "    }\n}\n",
        )

    def test_narrow_button_wraps_two_word_label_and_grows_taller(
        self, qml_engine, qt_app
    ):
        # 40px << a valós effekt-rács ~102px-es oszlopszélessége — a
        # kétszavas felirat itt biztosan nem fér ki egy sorba
        root = self._make_button(qml_engine, width=40, label="Graduated Tint")
        qt_app.processEvents()
        button = root.findChild(QObject, "btn")
        label = root.findChild(QObject, "btnLabel")
        assert label.property("lineCount") > 1
        assert label.property("truncated") is False
        # a fix 24px helyett a tördelt szöveghez igazodó, annál magasabb gomb
        assert button.property("height") > 24

    def test_button_label_never_truncates_regardless_of_width(
        self, qml_engine, qt_app
    ):
        root = self._make_button(qml_engine, width=30, label="Filmszemcse")
        qt_app.processEvents()
        label = root.findChild(QObject, "btnLabel")
        assert label.property("truncated") is False
