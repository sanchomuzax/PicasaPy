"""QML-funkcionális tesztek: a vágás-eszköz #448-as képarány-listája —
a beépített preset-lista a javított KULCSLISTÁT követi (ld. #448 jegy
2026-08-07-es kommentje), az egyéni arány felvétele/törlése a
`CustomAspectRatiosMixin`-en át a valódi AppControllerbe kötve (a mixin
`controller.py`-ba már be van drótozva, nincs szükség stub-controllerre,
a `test_folder_pane_collections_320.py` #320-as mintájával ellentétben,
ahol a bekötés még nem volt kész)."""

from __future__ import annotations

from PySide6.QtCore import QObject


def _open_viewer(window, qt_app, index=0):
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", index)
    qt_app.processEvents()
    return viewer


def _list_property(obj, name):
    """A QML `var`-tömb property Python-oldali olvasása — a
    `panel.property(...)` egy `QJSValue`-t ad vissza, amit explicit
    `.toVariant()` alakít Python listává (a `test_search.py` mintája)."""
    value = obj.property(name)
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return value


class TestAspectPresetKeys:
    """A #448 kulcskészlete. A `Picasa3i18n.dll` teljes listája (a jegy
    2026-08-10-i kommentje) feloldotta a korábban kihagyott kulcsokat is:
    `Widescreen` = 16:10, `WideFrame` = 5:3, `CurrentDisplay` = a KÉPERNYŐ
    aránya — így ezek már nem találgatások. A `8.5x11` (Letter méretű papír)
    ugyanabból a forrásból került be."""

    _EXPECTED_KEYS = [
        "Manual",
        "CurrentRatio",
        "CurrentDisplay",
        "4x4",
        "Desktop4x3",
        "4x6",
        "5x7",
        "8x10",
        "8.5x11",
        "5x3",
        "9x13",
        "10x15",
        "13x18",
        "20x25",
        "5x8",
        "16x10",
        "HDTV16x9",
        "Square",
        "FullPage",
    ]

    def test_builtin_preset_keys_match_the_corrected_list(self, qml_app, qt_app):
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None, "viewerEditorPanel nem található"
        presets = _list_property(panel, "aspectPresets")
        keys = [item["key"] for item in presets]
        assert keys == self._EXPECTED_KEYS

    def test_the_resolved_keys_carry_the_documented_ratio(self, qml_app, qt_app):
        """A `Picasa3i18n.dll` feloldotta a korábban kihagyott kulcsokat:
        a `Widescreen` a 16:10, a `WideFrame` az 5:3 felirata — ezért ezek
        NEM külön tételek, hanem a meglévő arányok magyarázó alcímei."""
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        presets = {
            item["key"]: item for item in _list_property(panel, "aspectPresets")
        }
        assert presets["16x10"]["note"] == "Widescreen monitor"
        assert presets["5x3"]["note"] == "Widescreen Photo Frame"
        assert presets["Square"]["note"] == "CD Cover"
        assert presets["8.5x11"]["note"] == "Letter paper"
        # az `Other` továbbra sem tétel: nálunk az egyéni arány felvétele
        # tölti be ezt a szerepet (AddCustomAspectRatio)
        assert "Other" not in presets

    def test_the_display_ratio_is_dynamic(self, qml_app, qt_app):
        """A „Jelenlegi megjelenítés" a képernyő arányát veszi át — a
        listában külön jelzés (-2) áll, nem bebetonozott szám."""
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        presets = {
            item["key"]: item for item in _list_property(panel, "aspectPresets")
        }
        assert presets["CurrentDisplay"]["ratio"] == -2

    def test_full_list_starts_with_the_builtin_presets(self, qml_app, qt_app):
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        full_list = _list_property(panel, "aspectFullList")
        assert [item["key"] for item in full_list] == self._EXPECTED_KEYS


class TestCustomAspectRatioAdd:
    def test_add_dialog_is_present(self, qml_app, qt_app):
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        dialog = panel.findChild(QObject, "addCustomAspectRatioDialog")
        assert dialog is not None, "addCustomAspectRatioDialog nem található"

    def test_created_signal_adds_ratio_via_controller(
        self, qml_app, qt_app
    ):
        window, controller, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        dialog = panel.findChild(QObject, "addCustomAspectRatioDialog")
        assert dialog is not None

        dialog.created.emit(4.0, 6.0, "Small print")
        qt_app.processEvents()

        assert controller.customAspectRatios == [
            {"name": "Small print", "width": 4.0, "height": 6.0}
        ]
        # a panel is látja az újonnan felvett arányt a beépítettek UTÁN
        full_list = _list_property(panel, "aspectFullList")
        assert full_list[-1]["label"] == "4 x 6   Small print"
        assert full_list[-1]["isCustom"] is True

    def test_created_ratio_becomes_selected_and_persists_as_last_crop_ratio(
        self, qml_app, qt_app
    ):
        window, controller, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        dialog = panel.findChild(QObject, "addCustomAspectRatioDialog")

        dialog.created.emit(4.0, 6.0, "Small print")
        qt_app.processEvents()

        full_list = _list_property(panel, "aspectFullList")
        assert panel.property("aspectIndex") == len(full_list) - 1
        assert controller.lastCropRatio == full_list[-1]["key"]


class TestCustomAspectRatioDelete:
    def test_delete_confirm_dialog_is_present_with_unique_name_prefix(
        self, qml_app, qt_app
    ):
        """A #448/#422 szabálya: minden ConfirmDialog-példány EGYEDI
        namePrefix-et kap — itt "deleteCustomAspectConfirm"."""
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        confirm = panel.findChild(QObject, "deleteCustomAspectConfirmDialog")
        assert confirm is not None, "deleteCustomAspectConfirmDialog nem található"

    def test_confirmed_signal_deletes_the_pending_ratio(self, qml_app, qt_app):
        window, controller, _ = qml_app
        _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        dialog = panel.findChild(QObject, "addCustomAspectRatioDialog")
        dialog.created.emit(4.0, 6.0, "Small print")
        qt_app.processEvents()
        assert controller.customAspectRatios != []

        confirm = panel.findChild(QObject, "deleteCustomAspectConfirmDialog")
        assert confirm is not None
        confirm.setProperty("pendingName", "Small print")
        confirm.setProperty("pendingWidth", 4.0)
        confirm.setProperty("pendingHeight", 6.0)
        confirm.confirmed.emit()
        qt_app.processEvents()

        assert controller.customAspectRatios == []


class TestCropSuggestionButtons:
    """#448: a vágás-panel HÁROM automatikus javaslat-gombja."""

    def _open_crop(self, window, qt_app):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        return viewer, panel

    def test_three_buttons_appear_with_labels(self, qml_app, qt_app):
        window, _, _ = qml_app
        _viewer, panel = self._open_crop(window, qt_app)
        row = window.findChild(QObject, "cropSuggestionRow")
        assert row is not None
        assert row.property("visible") is True
        for index in range(3):
            button = window.findChild(QObject, f"cropSuggestion{index}")
            assert button is not None, index
            assert str(button.property("label")), f"{index}. javaslat felirat nélkül"

    def test_choosing_a_suggestion_fills_the_selection(self, qml_app, qt_app):
        """A javaslat a KIJELÖLÉSBE kerül — nem alkalmazódik azonnal, hogy a
        felhasználó még igazíthasson rajta (Alkalmaz/Mégse változatlan)."""
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        _viewer, panel = self._open_crop(window, qt_app)
        overlay = window.findChild(QObject, "cropOverlay")
        assert overlay.property("hasSelection") is False

        QMetaObject.invokeMethod(
            window.findChild(QObject, "cropSuggestion0"),
            "buttonClicked", Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()
        assert overlay.property("hasSelection") is True

    def test_unknown_key_falls_back_to_the_key_itself(self, qml_app, qt_app):
        """A felirat-feloldás sosem ad üres gombot."""
        window, _, _ = qml_app
        _viewer, panel = self._open_crop(window, qt_app)
        assert panel.property("cropSuggestions") is not None
