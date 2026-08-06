"""QML-funkcionális tesztek — #411: a felhasználói screenshot-összevetés
két pontja, amit a #405-ös kör elrontott:

1. a szerkesztő-eszközpanel FIX 280px széles (nem ablakarányos, ld.
   EditorPanel.qml/PhotoViewer.qml kommentje),
2. a "Gyakori javítások" fül (0. fül) csempéi SAJÁT SVG-ikonokra mutatnak,
   NEM a felhasználó fotójának bélyegképére/effekt-előnézetére — a 3–5.
   effekt-fül (PanelButton) VÁLTOZATLANUL az effektthumb-providert
   használja (regresszió-őr).

Az `EditorPanel`-t önállóan, a `PicasaPy 1.0` modulon át töltjük be — a
`test_editor_405.py` / `test_editor_look.py` mintáját követve.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import Property, QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []

_ICONS_DIR = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "icons"
)
_QML_SOURCE = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "EditorPanel.qml"
).read_text(encoding="utf-8")
_VIEWER_QML_SOURCE = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "PhotoViewer.qml"
).read_text(encoding="utf-8")


class _FakeEditController(QObject):
    """Csak a bélyegkép-URL-hez szükséges felület: `previewSource`."""

    def __init__(self, preview_source="", parent=None):
        super().__init__(parent)
        self._preview_source = preview_source

    @Property(str)
    def previewSource(self):
        return self._preview_source


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _load(engine, qml_source):
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


def _make_panel(engine, fake_controller=None, active_tab=0):
    if fake_controller is not None:
        engine.rootContext().setContextProperty("editController", fake_controller)
        _KEEPALIVE.append(fake_controller)
    return _load(
        engine,
        "import QtQuick\nimport PicasaPy 1.0\n"
        f'EditorPanel {{ objectName: "panel"; activeTab: {active_tab} }}\n',
    )


class TestPanelFixedWidth:
    """#411 1. pont: a panel FIX 280px, nem ablakarányos."""

    def test_editor_panel_implicit_width_is_fixed_280(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        assert panel.property("implicitWidth") == 280

    def test_photo_viewer_source_reserves_280_for_the_panel(self):
        """A PhotoViewer.qml a bal panel-Rectangle-t 280px-re állítja —
        forrás-szintű ellenőrzés (a teljes PhotoViewer betöltése a
        `qml_app` fixtúrát igényelné, ld. test_viewer.py mintája)."""
        assert "Layout.preferredWidth: 280" in _VIEWER_QML_SOURCE

    def test_no_leftover_scaled_190_width_in_source(self):
        """Regresszió-őr: a #405-ös hibás, ablakarányosan leskálázott
        190px-es érték egyik fájlban se maradjon."""
        assert "implicitWidth: 190" not in _QML_SOURCE
        assert "Layout.preferredWidth: 190" not in _VIEWER_QML_SOURCE


class TestCommonFixesTabUsesOwnIcons:
    """#411 2. pont: a "Gyakori javítások" (0.) fül csempéi SAJÁT SVG-
    ikonokra mutatnak, NEM a felhasználó fotójának bélyegképére/effekt-
    előnézetére."""

    # csempe objectName -> várt ikonfájl-név (kiterjesztés nélkül)
    TILE_ICONS = {
        "editToolCrop": "vagas",
        "editToolTilt": "kiegyenesites",
        "editToolRedeye": "vorosszem",
        "editToolEnhance": "jo-napom-van",
        "editToolAutolight": "auto-kontraszt",
        "editToolAutocolor": "auto-szin",
        "editToolRetouch": "retusalas",
        "editToolText": "szoveg",
    }

    @pytest.mark.parametrize("object_name,icon_file", list(TILE_ICONS.items()))
    def test_tile_icon_image_points_to_the_expected_svg(
        self, qml_engine, qt_app, object_name, icon_file
    ):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        icon = panel.findChild(QObject, object_name + "Icon")
        assert icon is not None, f"{object_name}: hiányzik az ikon-gyermek"
        source = str(icon.property("source").toString())
        assert source.endswith(f"icons/{icon_file}.svg"), (object_name, source)

    @pytest.mark.parametrize("icon_file", list(TILE_ICONS.values()) + ["deritofeny"])
    def test_referenced_icon_file_actually_exists(self, icon_file):
        path = _ICONS_DIR / f"{icon_file}.svg"
        assert path.is_file(), f"hiányzik az ikonfájl: {path}"

    def test_tiles_are_pairwise_distinct_icon_files(self, qml_engine, qt_app):
        """Minden csempe MÁS ikont kap — sötét képnél is megkülönböztethetők
        (az elfogadási feltétel szó szerinti követelménye)."""
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        sources = []
        for object_name in self.TILE_ICONS:
            icon = panel.findChild(QObject, object_name + "Icon")
            sources.append(str(icon.property("source").toString()))
        assert len(sources) == len(set(sources))

    def test_tile_icons_do_not_change_with_or_without_edit_controller(
        self, qml_engine, qt_app
    ):
        """A saját ikon FÜGGETLEN attól, hogy van-e aktív szerkesztési
        munkamenet (a korábbi fotó-bélyegkép ezzel szemben üres maradt
        editController nélkül) — az ikonos csempe SOHA nem üres/villogó."""
        panel_no_ctl = _make_panel(qml_engine)
        qt_app.processEvents()
        no_ctl_source = str(
            panel_no_ctl.findChild(QObject, "editToolRedeyeIcon")
            .property("source")
            .toString()
        )

        fake = _FakeEditController(preview_source="image://editpreview/7?rev=3")
        panel_with_ctl = _make_panel(qml_engine, fake_controller=fake, active_tab=0)
        qt_app.processEvents()
        with_ctl_source = str(
            panel_with_ctl.findChild(QObject, "editToolRedeyeIcon")
            .property("source")
            .toString()
        )

        assert no_ctl_source == with_ctl_source
        assert no_ctl_source.endswith("icons/vorosszem.svg")

    def test_tool_tile_no_longer_exposes_a_thumb_source_property(
        self, qml_engine, qt_app
    ):
        """A csempéken NINCS többé fotó-bélyegkép-alapú `thumbSource`
        property — a #405-ös mechanizmus ezen a fülön teljesen megszűnt."""
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        tile = panel.findChild(QObject, "editToolCrop")
        assert tile.property("thumbSource") is None


class TestEffectTabsStillUseEffectThumbnails:
    """Regresszió-őr: a 3–5. effekt-fül (Effektek/Creative/Artistic) a
    PanelButton-on át VÁLTOZATLANUL a felhasználó fotójának effekt-
    előnézetét (`image://effectthumb/…`) mutatja — ezt a felhasználó
    kifejezetten jónak mondta, az #411 ide NEM nyúl."""

    def test_effects_tab_button_still_gets_effectthumb_url(self, qml_engine, qt_app):
        fake = _FakeEditController(preview_source="image://editpreview/42?rev=7")
        panel = _make_panel(qml_engine, fake_controller=fake, active_tab=2)
        qt_app.processEvents()
        button = panel.findChild(QObject, "effectSepia")
        assert button.property("thumbSource") == "image://effectthumb/42/sepia"

    def test_creative_tab_button_still_gets_effectthumb_url(self, qml_engine, qt_app):
        fake = _FakeEditController(preview_source="image://editpreview/42?rev=7")
        panel = _make_panel(qml_engine, fake_controller=fake, active_tab=3)
        qt_app.processEvents()
        button = panel.findChild(QObject, "effectIr")
        assert button.property("thumbSource") == "image://effectthumb/42/ir"

    def test_artistic_tab_button_still_gets_effectthumb_url(self, qml_engine, qt_app):
        fake = _FakeEditController(preview_source="image://editpreview/42?rev=7")
        panel = _make_panel(qml_engine, fake_controller=fake, active_tab=4)
        qt_app.processEvents()
        button = panel.findChild(QObject, "effectBoost")
        assert button.property("thumbSource") == "image://effectthumb/42/boost"

    def test_effect_tab_buttons_have_no_icon_child(self, qml_engine, qt_app):
        """A PanelButton-oknak (2–4. fül) NINCS `...Icon` gyermekük — az
        ikonos csempe-mechanizmus kizárólag a ToolTile-on (0. fül) él."""
        fake = _FakeEditController(preview_source="image://editpreview/1?rev=1")
        panel = _make_panel(qml_engine, fake_controller=fake, active_tab=2)
        qt_app.processEvents()
        assert panel.findChild(QObject, "effectSepiaIcon") is None
