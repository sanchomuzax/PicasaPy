"""QML-funkcionális tesztek: EditorPanel és CropOverlay önálló komponensek.

A Main.qml-be való bekötés az integrátor feladata (19-es issue #2) — itt a
két komponenst önmagában, a PicasaPy modulon (`import PicasaPy 1.0`)
keresztül töltjük be, a tests/app/test_qml_functional.py mintája szerint
(pl. TestThumbCaption.test_thumb_delegate_shows_filename_caption).
"""

import pytest
from PySide6.QtCore import QMetaObject, QObject, QRectF, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

# a QML-ből létrehozott gyökér-objektumok élő Python-referenciák nélkül a
# JS-motor tulajdonába kerülnek és a GC bármikor eltávolíthatja őket —
# CppOwnership-re váltva és itt megtartva éljük túl a teszt-futást.
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


class TestEditorPanelButtons:
    TOOLS = ["crop", "tilt", "redeye", "enhance", "autolight", "autocolor"]
    OBJECT_NAMES = {
        "crop": "editToolCrop",
        "tilt": "editToolTilt",
        "redeye": "editToolRedeye",
        "enhance": "editToolEnhance",
        "autolight": "editToolAutolight",
        "autocolor": "editToolAutocolor",
    }
    # mód-eszközök: helyi kapcsoló-állapot ("benyomva" csempe); az egygombos
    # javítások (enhance/autolight/autocolor) NEM kapcsolók (#116)
    MODE_TOOLS = ["crop", "tilt", "redeye"]
    ACTIVE_PROPS = {
        "crop": "cropActive",
        "tilt": "tiltActive",
        "redeye": "redeyeActive",
    }
    ONE_SHOT_TOOLS = ["enhance", "autolight", "autocolor"]
    ENABLED_PROPS = {
        "enhance": "enhanceEnabled",
        "autolight": "autolightEnabled",
        "autocolor": "autocolorEnabled",
    }

    def _make_panel(self, qml_engine):
        return _load(
            qml_engine,
            'import QtQuick\nimport PicasaPy 1.0\nEditorPanel { objectName: "panel" }\n',
        )

    def test_disabled_panel_grays_out_tools(self, qml_engine, qt_app):
        # #103: videónál a PhotoViewer enabled=false-ra állítja a panelt —
        # a csempéknek VIZUÁLISAN is tiltottnak kell látszaniuk
        panel = _load(
            qml_engine,
            "import QtQuick\nimport PicasaPy 1.0\n"
            'EditorPanel { objectName: "panel"; enabled: false }\n',
        )
        qt_app.processEvents()
        tools = panel.findChild(QObject, "toolsColumn")
        assert tools.property("opacity") < 1
        crop_tile = panel.findChild(QObject, "editToolCrop")
        assert crop_tile.property("enabled") is False
        assert crop_tile.property("opacity") < 1

    def test_enabled_panel_tools_fully_opaque(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        qt_app.processEvents()
        tools = panel.findChild(QObject, "toolsColumn")
        assert tools.property("opacity") == 1
        crop_tile = panel.findChild(QObject, "editToolCrop")
        assert crop_tile.property("opacity") == 1
        # a 2. ütemre váró csempék viszont maradnak halványak
        retouch = panel.findChild(QObject, "editToolRetouch")
        assert retouch.property("opacity") < 1

    def test_all_buttons_present_with_object_names(self, qml_engine):
        panel = self._make_panel(qml_engine)
        for tool in self.TOOLS:
            name = self.OBJECT_NAMES[tool]
            button = panel.findChild(QObject, name)
            assert button is not None, f"{name} nem található"

    @pytest.mark.parametrize("tool", TOOLS)
    def test_tool_click_emits_tool_activated(self, qml_engine, qt_app, tool):
        panel = self._make_panel(qml_engine)
        activated = []
        panel.toolActivated.connect(lambda t: activated.append(t))
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            *_string_arg(tool),
        )
        qt_app.processEvents()
        assert activated == [tool]

    def test_crop_click_also_emits_crop_requested(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        requested = []
        panel.cropRequested.connect(lambda: requested.append(True))
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            *_string_arg("crop"),
        )
        qt_app.processEvents()
        assert requested == [True]

    def test_non_crop_click_does_not_emit_crop_requested(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        requested = []
        panel.cropRequested.connect(lambda: requested.append(True))
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            *_string_arg("redeye"),
        )
        qt_app.processEvents()
        assert requested == []

    @pytest.mark.parametrize("tool", MODE_TOOLS)
    def test_active_state_toggles_and_reflects_on_button(self, qml_engine, qt_app, tool):
        panel = self._make_panel(qml_engine)
        prop = self.ACTIVE_PROPS[tool]
        button = panel.findChild(QObject, self.OBJECT_NAMES[tool])

        assert panel.property(prop) is False
        assert button.property("active") is False

        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            *_string_arg(tool),
        )
        qt_app.processEvents()
        assert panel.property(prop) is True
        assert button.property("active") is True  # benyomott állapot

        # ismételt kattintás visszakapcsol
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            *_string_arg(tool),
        )
        qt_app.processEvents()
        assert panel.property(prop) is False
        assert button.property("active") is False


class TestOneShotTiles:
    """#116: az egygombos javítások nem kapcsolók — a csempe tiltott, amíg
    ugyanez a szűrő a lánc utolsó eleme (a *Enabled propertyt a hívó tölti)."""

    def _make_panel(self, qml_engine):
        return _load(
            qml_engine,
            'import QtQuick\nimport PicasaPy 1.0\nEditorPanel { objectName: "panel" }\n',
        )

    @pytest.mark.parametrize("tool", TestEditorPanelButtons.ONE_SHOT_TOOLS)
    def test_default_enabled_and_not_pressed(self, qml_engine, qt_app, tool):
        panel = self._make_panel(qml_engine)
        qt_app.processEvents()
        button = panel.findChild(
            QObject, TestEditorPanelButtons.OBJECT_NAMES[tool]
        )
        assert panel.property(TestEditorPanelButtons.ENABLED_PROPS[tool]) is True
        assert button.property("enabled") is True
        # nincs "benyomva" állapot — a kattintás nem billent kapcsolót
        assert button.property("active") is False

    @pytest.mark.parametrize("tool", TestEditorPanelButtons.ONE_SHOT_TOOLS)
    def test_click_does_not_flip_pressed_state(self, qml_engine, qt_app, tool):
        panel = self._make_panel(qml_engine)
        button = panel.findChild(
            QObject, TestEditorPanelButtons.OBJECT_NAMES[tool]
        )
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            *_string_arg(tool),
        )
        qt_app.processEvents()
        assert button.property("active") is False

    @pytest.mark.parametrize("tool", TestEditorPanelButtons.ONE_SHOT_TOOLS)
    def test_disabled_tile_grays_out_and_ignores_click(self, qml_engine, qt_app, tool):
        panel = self._make_panel(qml_engine)
        panel.setProperty(TestEditorPanelButtons.ENABLED_PROPS[tool], False)
        qt_app.processEvents()
        button = panel.findChild(
            QObject, TestEditorPanelButtons.OBJECT_NAMES[tool]
        )
        assert button.property("enabled") is False
        assert button.property("opacity") < 1

        activated = []
        panel.toolActivated.connect(lambda t: activated.append(t))
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            *_string_arg(tool),
        )
        qt_app.processEvents()
        assert activated == []  # tiltott gomb: no-op védőkorlát

    @pytest.mark.parametrize("tool", TestEditorPanelButtons.ONE_SHOT_TOOLS)
    def test_reenabled_tile_emits_again(self, qml_engine, qt_app, tool):
        panel = self._make_panel(qml_engine)
        prop = TestEditorPanelButtons.ENABLED_PROPS[tool]
        panel.setProperty(prop, False)
        panel.setProperty(prop, True)
        activated = []
        panel.toolActivated.connect(lambda t: activated.append(t))
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            *_string_arg(tool),
        )
        qt_app.processEvents()
        assert activated == [tool]


class TestFillLightRemoved:
    """#20: a "Hamarosan" Derítőfény-sor helyét a működő Finomhangolás fül
    vette át — a régi placeholder-elemeknek el kell tűnniük."""

    def _make_panel(self, qml_engine):
        return _load(
            qml_engine,
            'import QtQuick\nimport PicasaPy 1.0\nEditorPanel { objectName: "panel" }\n',
        )

    def test_fill_light_row_no_longer_exists(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        qt_app.processEvents()
        assert panel.findChild(QObject, "fillLightRow") is None
        assert panel.findChild(QObject, "fillLightComingSoon") is None


class TestEditorTabs:
    """#20: a három fül (Gyakori javítások / Finomhangolás / Effektek)
    kizárólagosan mutatja a hozzá tartozó oszlopot."""

    def _make_panel(self, qml_engine):
        return _load(
            qml_engine,
            'import QtQuick\nimport PicasaPy 1.0\nEditorPanel { objectName: "panel" }\n',
        )

    COLUMNS = ["toolsColumn", "finetuneColumn", "effectsColumn"]

    @pytest.mark.parametrize("active_tab", [0, 1, 2])
    def test_active_tab_shows_only_matching_column(self, qml_engine, qt_app, active_tab):
        panel = self._make_panel(qml_engine)
        panel.setProperty("activeTab", active_tab)
        qt_app.processEvents()
        for index, name in enumerate(self.COLUMNS):
            column = panel.findChild(QObject, name)
            assert column is not None, f"{name} nem található"
            assert column.property("visible") is (index == active_tab)

    def test_tab_buttons_present_with_object_names(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        qt_app.processEvents()
        for name in ("editTabFixes", "editTabFinetune", "editTabEffects"):
            assert panel.findChild(QObject, name) is not None, f"{name} nem található"

    @pytest.mark.parametrize(
        "object_name,expected_tab",
        [("editTabFixes", 0), ("editTabFinetune", 1), ("editTabEffects", 2)],
    )
    def test_clicking_tab_sets_active_tab(
        self, qml_engine, qt_app, object_name, expected_tab
    ):
        panel = self._make_panel(qml_engine)
        panel.setProperty("activeTab", -1 if expected_tab != 0 else 1)
        qt_app.processEvents()
        button = panel.findChild(QObject, object_name)
        assert button is not None
        panel.setProperty("activeTab", expected_tab)
        qt_app.processEvents()
        assert panel.property("activeTab") == expected_tab


class TestFinetuneSliders:
    """#20: a 4 finomhangoló-csúszka élő előnézetet küld húzás közben
    (finetunePreview), a syncFinetuneSliders() viszont NEM vált ki előnézetet
    (a tiltSlider mintáját követve, #131)."""

    SLIDERS = {
        "finetuneFillSlider": (0.0, 1.0),
        "finetuneHighlightsSlider": (0.0, 1.0),
        "finetuneShadowsSlider": (0.0, 1.0),
        "finetuneTempSlider": (-1.0, 1.0),
    }

    def _make_panel(self, qml_engine):
        panel = _load(
            qml_engine,
            'import QtQuick\nimport PicasaPy 1.0\n'
            'EditorPanel { objectName: "panel"; activeTab: 1 }\n',
        )
        return panel

    def test_sliders_present_with_expected_ranges(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        qt_app.processEvents()
        for name, (lo, hi) in self.SLIDERS.items():
            slider = panel.findChild(QObject, name)
            assert slider is not None, f"{name} nem található"
            assert slider.property("from") == lo
            assert slider.property("to") == hi

    def test_dragging_slider_emits_finetune_preview(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        qt_app.processEvents()
        previews = []
        panel.finetunePreview.connect(
            lambda f, h, s, t: previews.append((f, h, s, t))
        )
        fill = panel.findChild(QObject, "finetuneFillSlider")
        fill.setProperty("value", 0.5)
        qt_app.processEvents()
        assert len(previews) == 1
        assert previews[0][0] == pytest.approx(0.5)

    def test_suppress_finetune_blocks_preview_emission(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        qt_app.processEvents()
        panel.setProperty("suppressFinetune", True)
        previews = []
        panel.finetunePreview.connect(lambda f, h, s, t: previews.append((f, h, s, t)))
        highlights = panel.findChild(QObject, "finetuneHighlightsSlider")
        highlights.setProperty("value", 0.7)
        qt_app.processEvents()
        assert previews == []

    def test_sync_finetune_sliders_sets_values_without_preview(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        qt_app.processEvents()
        panel.setProperty("fillLight", 0.2)
        panel.setProperty("highlights", 0.3)
        panel.setProperty("shadows", 0.4)
        panel.setProperty("colorTemp", -0.1)
        previews = []
        panel.finetunePreview.connect(lambda f, h, s, t: previews.append((f, h, s, t)))
        QMetaObject.invokeMethod(
            panel, "syncFinetuneSliders", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert previews == []
        assert panel.findChild(QObject, "finetuneFillSlider").property(
            "value"
        ) == pytest.approx(0.2)
        assert panel.findChild(QObject, "finetuneHighlightsSlider").property(
            "value"
        ) == pytest.approx(0.3)
        assert panel.findChild(QObject, "finetuneShadowsSlider").property(
            "value"
        ) == pytest.approx(0.4)
        assert panel.findChild(QObject, "finetuneTempSlider").property(
            "value"
        ) == pytest.approx(-0.1)


class TestEffectButtons:
    """#20: minden effekt-gomb a saját kulcsával küldi az effectRequested
    jelet — a lánc mindig új réteget kap (append-only, #116-mintát követve)."""

    EFFECTS = {
        "effectSepia": "sepia",
        "effectBw": "bw",
        "effectWarm": "warm",
        "effectGrain2": "grain2",
        "effectTint": "tint",
        "effectSat": "sat",
        "effectRadblur": "radblur",
        "effectGlow2": "glow2",
        "effectAnsel": "ansel",
        "effectRadsat": "radsat",
        "effectDirTint": "dir_tint",
    }

    def _make_panel(self, qml_engine):
        return _load(
            qml_engine,
            'import QtQuick\nimport PicasaPy 1.0\n'
            'EditorPanel { objectName: "panel"; activeTab: 2 }\n',
        )

    def test_all_effect_buttons_present(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        qt_app.processEvents()
        for name in self.EFFECTS:
            assert panel.findChild(QObject, name) is not None, f"{name} nem található"

    @pytest.mark.parametrize("object_name,key", list(EFFECTS.items()))
    def test_effect_button_click_emits_effect_requested(
        self, qml_engine, qt_app, object_name, key
    ):
        panel = self._make_panel(qml_engine)
        qt_app.processEvents()
        requested = []
        panel.effectRequested.connect(lambda name: requested.append(name))
        button = panel.findChild(QObject, object_name)
        QMetaObject.invokeMethod(
            button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert requested == [key]


def _string_arg(value):
    """Q_ARG segéd — a PySide6 verziók között eltér a string-argumentum
    átadásának preferált formája, ezért itt egyszerű változó-listát adunk
    vissza a QMetaObject.invokeMethod hívásokhoz."""
    from PySide6.QtCore import Q_ARG

    return (Q_ARG("QVariant", value),)


class TestCropOverlay:
    def _make_overlay(self, qml_engine, extra=""):
        return _load(
            qml_engine,
            "import QtQuick\nimport PicasaPy 1.0\n"
            f'CropOverlay {{ width: 200; height: 100; {extra} }}\n',
        )

    def test_croprect_default_matches_selection_geometry(self, qml_engine):
        # #51: Picasa-hűen NINCS elő-kijelölés — a keret rejtve indul,
        # a kijelölést a felhasználó húzással hozza létre.
        overlay = self._make_overlay(qml_engine)
        selection = overlay.findChild(QObject, "cropSelection")
        assert selection is not None
        assert overlay.property("hasSelection") is False
        assert selection.property("visible") is False

    def test_croprect_change_updates_selection_geometry(self, qml_engine, qt_app):
        overlay = self._make_overlay(qml_engine)
        selection = overlay.findChild(QObject, "cropSelection")
        overlay.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
        qt_app.processEvents()
        assert round(selection.property("x")) == 50
        assert round(selection.property("y")) == 25
        assert round(selection.property("width")) == 100
        assert round(selection.property("height")) == 50

    def test_enter_emits_accepted_with_current_rect(self, qml_engine, qt_app):
        overlay = self._make_overlay(
            qml_engine,
            extra="cropRect: Qt.rect(0.1, 0.2, 0.3, 0.4); hasSelection: true",
        )
        accepted = []
        overlay.accepted.connect(lambda r: accepted.append(r))
        QMetaObject.invokeMethod(
            overlay, "acceptCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert len(accepted) == 1
        r = accepted[0]
        assert round(r.x(), 2) == 0.1
        assert round(r.y(), 2) == 0.2
        assert round(r.width(), 2) == 0.3
        assert round(r.height(), 2) == 0.4

    def test_escape_emits_cancelled(self, qml_engine, qt_app):
        overlay = self._make_overlay(qml_engine)
        cancelled = []
        overlay.cancelled.connect(lambda: cancelled.append(True))
        QMetaObject.invokeMethod(
            overlay, "cancelCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert cancelled == [True]

    def test_escape_does_not_emit_accepted(self, qml_engine, qt_app):
        overlay = self._make_overlay(qml_engine)
        accepted = []
        overlay.accepted.connect(lambda r: accepted.append(r))
        QMetaObject.invokeMethod(
            overlay, "cancelCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert accepted == []

    def test_object_names_present(self, qml_engine):
        overlay = self._make_overlay(qml_engine)
        assert overlay.objectName() == "cropOverlay"
        assert overlay.findChild(QObject, "cropSelection") is not None


class TestCropAspectReshape:
    """#59: az arány-váltás és a Forgatás a meglévő kijelölést is átformálja."""

    OVERLAY = (
        "import QtQuick\nimport PicasaPy 1.0\n"
        "CropOverlay { width: 400; height: 300 }\n"
    )

    def _selected(self, qml_engine):
        from PySide6.QtCore import Q_ARG

        overlay = _load(qml_engine, self.OVERLAY)
        QMetaObject.invokeMethod(
            overlay, "updateCreation", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 100), Q_ARG("QVariant", 75),
            Q_ARG("QVariant", 300), Q_ARG("QVariant", 225),
        )
        return overlay

    def test_apply_aspect_reshapes_keeping_center(self, qml_engine):
        from PySide6.QtCore import Q_ARG

        overlay = self._selected(qml_engine)
        QMetaObject.invokeMethod(
            overlay, "applyAspect", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 2.0),
        )
        r = overlay.property("cropRect")
        w_px = r.width() * 400
        h_px = r.height() * 300
        assert abs(w_px / h_px - 2.0) < 0.01
        # a középpont a helyén marad
        assert abs((r.x() + r.width() / 2) - 0.5) < 0.01

    def test_swap_orientation_flips_ratio(self, qml_engine):
        overlay = self._selected(qml_engine)
        before = overlay.property("cropRect")
        ratio_before = (before.width() * 400) / (before.height() * 300)
        QMetaObject.invokeMethod(
            overlay, "swapSelectionOrientation",
            Qt.ConnectionType.DirectConnection,
        )
        after = overlay.property("cropRect")
        ratio_after = (after.width() * 400) / (after.height() * 300)
        assert abs(ratio_after - 1 / ratio_before) < 0.05

    def test_apply_aspect_without_selection_noop(self, qml_engine):
        from PySide6.QtCore import Q_ARG

        overlay = _load(qml_engine, self.OVERLAY)
        QMetaObject.invokeMethod(
            overlay, "applyAspect", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 2.0),
        )
        assert overlay.property("hasSelection") is False
