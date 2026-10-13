"""Állapotmentes szerkesztőpanelek és eszköztipográfia próbái."""

import pytest
from PySide6.QtCore import QObject
from tests.app.qml_functional._editor_test_helpers import EditorTestHelpers


class _ModulAblakMixin:
    """#2851: a modul KÖZÖS ablakán futó osztályok jelölője.

    Csak olyan osztály veheti fel, amely **nem ír tartós állapotot** — se
    ini-t, se beállítást, se fájlt: felület-geometriát és kötést mér. A
    felület-állapotot (nyitott néző, aktív fül) minden teszt maga állítja be.

    Az állapotot író szerkesztési és navigációs tesztcsoportok
    SZÁNDÉKOSAN nem ilyenek: ini-t írnak, illetve saját könyvtárat építenek,
    tehát tesztenként friss ablakot kapnak."""

    @pytest.fixture
    def qml_app(self, qml_app_module):
        return qml_app_module


class _ViewerOpenMixin(EditorTestHelpers):
    """Az `_open_viewer` segédet a #464-es tesztek is használják."""


class TestFinetuneTabQuickFixesAndPicker(_ModulAblakMixin, _ViewerOpenMixin):
    """#464: a 2. fülön ott van a két egykattintásos javítás és a
    „semleges szín" pipetta.

    A tulajdonos képernyőképei (`referencia/finomhangolas/shot1..4.png`)
    pontosították a formát: a két egykattintásos javítás nem szöveges
    csempe, hanem KÉT VARÁZSPÁLCA-GOMB a csúszka-oszlop jobb szélén — az
    egyik a Kiemelések/Árnyékok párnál („…a megvilágításhoz"), a másik az
    Alapszínválasztás sorában („…a színhez")."""

    def test_wands_and_picker_present_on_the_finetune_tab(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("activeTab", 1)
        qt_app.processEvents()

        for name in (
            "finetuneLightingWand", "finetuneColorWand",
            "finetuneNeutralPicker", "finetuneNeutralSwatch",
        ):
            assert window.findChild(QObject, name) is not None, name

    def test_a_ket_palca_KULON_utat_indit(self, qml_app, qt_app):
        """A megvilágítás-pálca az Automatikus kontraszt műveletét indítja
        (a `referencia/varazspalcak/` mérése szerint), a SZÍN-pálca viszont
        NEM szűrőt fűz a láncra: a `finetune2` semleges szín (p4) mezőjét
        állítja be — a Picasa saját `.picasa.ini`-je bizonyítja (#551)."""
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("activeTab", 1)
        qt_app.processEvents()

        tools, wand = [], []
        panel.toolActivated.connect(tools.append)
        panel.colorWandRequested.connect(lambda: wand.append("color"))
        for name in ("finetuneLightingWand", "finetuneColorWand"):
            QMetaObject.invokeMethod(
                window.findChild(QObject, name),
                "clicked", Qt.ConnectionType.DirectConnection,
            )
        qt_app.processEvents()
        assert tools == ["autolight"]
        assert wand == ["color"]

    def test_picker_toggle_arms_the_sampling_area(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("activeTab", 1)
        qt_app.processEvents()

        area = window.findChild(QObject, "neutralPickArea")
        assert area is not None
        assert area.property("enabled") is False

        QMetaObject.invokeMethod(
            panel, "neutralPickerToggled", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert panel.property("neutralPickerActive") is True
        assert area.property("enabled") is True


class TestEffectTabsFitWithoutScrolling(_ModulAblakMixin, _ViewerOpenMixin):
    """#422 (felhasználói döntés): az effekt-füleknek KERET/GÖRGETÉS NÉLKÜL
    ki kell férniük.

    A rács azért lógott ki eredetileg, mert a három ismert fülre a spec
    listáján KÍVÜLI effektek is odakerültek; azok a 6., „További effektek"
    fülre kerültek. A görgethető keret (az én korábbi megoldásom) rossz
    válasz volt a tünetre — ez a teszt őrzi, hogy ne kerüljön vissza, és
    hogy a rács tényleg elférjen a gombsor fölött."""

    GRIDS = {2: "effectsGrid", 3: "effectsGrid2", 4: "effectsGrid3",
             5: "effectsGrid4"}

    def test_no_scroll_frame_on_the_effect_tabs(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        for name in (
            "editorEffectsTab1Scroll",
            "editorEffectsTab2Scroll",
            "editorEffectsTab3Scroll",
        ):
            assert window.findChild(QObject, name) is None, (
                f"visszakerült a görgethető keret: {name}"
            )

    def test_every_effect_tab_has_the_spec_button_count(self, qml_app, qt_app):
        """A fülek gombszáma az, ami az eredetin — ettől férnek ki.

        A tényleges GEOMETRIÁT szándékosan nem mérjük: a teszt-ablak
        panelje jóval alacsonyabb a valódinál, ott a legjobb elrendezés sem
        férne ki. A hiba forrása nem a magasság volt, hanem az, hogy a
        három ismert fülre a spec listáján kívüli effektek is odakerültek."""
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        # #704 HELYESBÍTÉS (▶KÉP, `ui-audit-editor.md` 2. szakasz):
        # mindhárom effekt-fül 12 csempés — a Vignetta az 5. fülre
        # tartozik, nem a #422-es „További effektek" gyűjtőre.
        expected = {2: 12, 3: 12, 4: 12, 5: 5}
        for tab, grid_name in self.GRIDS.items():
            panel.setProperty("activeTab", tab)
            qt_app.processEvents()
            grid = window.findChild(QObject, grid_name)
            assert grid is not None, grid_name
            buttons = [
                child for child in grid.children()
                if str(child.objectName()).startswith("effect")
            ]
            assert len(buttons) == expected[tab], (
                f"{tab}. fül: {len(buttons)} gomb, várt {expected[tab]}"
            )


class TestModeToolPanelsDoNotOverflow(_ModulAblakMixin, _ViewerOpenMixin):
    """#464: ugyanaz a hibaosztály, mint az effekt-füleknél — a mód-eszközök
    (vágás/retusálás/vörösszem/szöveg) panelje a tartalmától függően
    magasabb lehet a rendelkezésre álló helynél, és rálógna a panel alján
    ülő, globális Visszavonás/Újra sorra."""

    def test_effect_param_panel_is_clipped_above_the_undo_row(
        self, qml_app, qt_app
    ):
        """A sok paraméteres effektek alpanelje (pl. Vignetta) is
        magasabb lehet a helynél."""
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        row = window.findChild(QObject, "editorGlobalUndoRow")
        scroll = window.findChild(QObject, "editorEffectParamScroll")
        assert scroll is not None
        assert scroll.property("clip") is True

        panel.setProperty("paramPanelActive", True)
        qt_app.processEvents()
        assert scroll.property("visible") is True
        bottom = scroll.mapToItem(panel, 0, scroll.property("height"))
        assert bottom.y() <= row.mapToItem(panel, 0, 0).y() + 1

    def test_mode_panels_are_clipped_above_the_undo_row(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        row = window.findChild(QObject, "editorGlobalUndoRow")
        scroll = window.findChild(QObject, "editorModeToolScroll")
        assert scroll is not None
        assert scroll.property("clip") is True

        for prop in ("cropActive", "retouchActive", "redeyeActive", "textActive"):
            panel.setProperty(prop, True)
            qt_app.processEvents()
            assert scroll.property("visible") is True, prop
            bottom = scroll.mapToItem(panel, 0, scroll.property("height"))
            assert bottom.y() <= row.mapToItem(panel, 0, 0).y() + 1, (
                f"{prop}: a mód-panel területe a Visszavonás-sor alá nyúlik"
            )
            panel.setProperty(prop, False)
            qt_app.processEvents()


class TestGlobalUndoRedoRow(_ModulAblakMixin, _ViewerOpenMixin):
    """#464: a Visszavonás/Újra a panel alján, GLOBÁLISAN — nem fülönként
    ismételve (az eredetiben sem volt fülhöz kötve)."""

    def test_single_row_shared_by_every_tab(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")

        row = window.findChild(QObject, "editorGlobalUndoRow")
        assert row is not None
        for tab in range(5):
            panel.setProperty("activeTab", tab)
            qt_app.processEvents()
            assert row.property("visible") is True, f"{tab}. fülön eltűnt"

    def test_the_old_per_tab_buttons_are_gone(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        for name in (
            "finetuneUndoButton", "effectsUndoButton",
            "effects2UndoButton", "effects3UndoButton",
        ):
            assert window.findChild(QObject, name) is None, name


class TestTextToolTypography(_ModulAblakMixin):
    """#450 (2. lépcső): a szöveg-eszköz tipográfia-vezérlői a panelen —
    betűcsalád, méret, félkövér/dőlt/aláhúzott, igazítás."""

    def _open_text_tool(self, window, qt_app):
        # a néző megnyitása indítja a beginEdit-et — enélkül a stílus-slotok
        # jogosan tiltakoznak („Nincs aktív szerkesztés")
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("textActive", True)
        qt_app.processEvents()
        return panel

    def test_every_control_is_present(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        self._open_text_tool(window, qt_app)
        for name in (
            "textFontFamilyBox", "textFontSizeBox", "textBoldButton",
            "textItalicButton", "textUnderlineButton",
            "textAlign_left", "textAlign_center", "textAlign_right",
        ):
            assert window.findChild(QObject, name) is not None, name

    @pytest.mark.parametrize("height_delta", [-5, 0, 5])
    def test_the_family_list_comes_from_the_catalogue(
        self, qml_app, qt_app, height_delta
    ):
        from PySide6.QtGui import QFontDatabase

        window, _controller, _engine = qml_app
        window.setHeight(window.height() + height_delta)
        qt_app.processEvents()
        panel = self._open_text_tool(window, qt_app)
        keys = panel.property("fontFamilyKeys")
        keys = keys.toVariant() if hasattr(keys, "toVariant") else list(keys)
        expected = sorted(
            set(QFontDatabase.families()),
            key=lambda family: (family.casefold(), family),
        )
        assert keys == expected

    def test_the_style_buttons_reach_the_controller(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, _controller, _engine = qml_app
        panel = self._open_text_tool(window, qt_app)
        seen = []
        panel.textBoldEdited.connect(seen.append)
        panel.textAlignEdited.connect(seen.append)

        for name in ("textBoldButton", "textAlign_center"):
            QMetaObject.invokeMethod(
                window.findChild(QObject, name), "buttonClicked",
                Qt.ConnectionType.DirectConnection,
            )
        qt_app.processEvents()

        assert seen == [True, "center"]
