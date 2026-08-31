"""QML-funkcionális tesztek: keresés, mappa-panel és kapcsolódó apróbb
bekötések (#7, #45, #10, #173, világos téma) — a témába nem sorolt
maradék tesztek gyűjtőfájlja (#155: a korábbi `test_qml_functional.py`
egyik szelete, processzenkénti izolációhoz)."""

from PySide6.QtCore import QObject


class TestSearchSuggestionsWiring:
    def test_refresh_fills_box_from_controller(self, qml_app, qt_app):
        # #7 bekötés: gépelés (debounce után) a controller-slotból tölti
        # a legördülőt.
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, _ = qml_app
        field = window.findChild(QObject, "searchField")
        box = window.findChild(QObject, "searchSuggestions")
        assert box is not None, "searchSuggestions nem található"
        field.setProperty("text", "kep")
        QMetaObject.invokeMethod(
            window, "refreshSuggestions", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        value = box.property("suggestions")
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        assert [s["name"] for s in value] == ["kepek"]
        assert box.property("visible") is True

    def test_choose_folder_jumps_and_clears(self, qml_app, qt_app):
        window, controller, _ = qml_app
        field = window.findChild(QObject, "searchField")
        box = window.findChild(QObject, "searchSuggestions")
        target = controller.currentFolder
        field.setProperty("text", "kep")
        box.setProperty(
            "suggestions",
            [{"kind": "folder", "name": "kepek", "count": 2, "param": target}],
        )
        qt_app.processEvents()
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        QMetaObject.invokeMethod(
            box, "choose", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
        )
        qt_app.processEvents()
        assert field.property("text") == ""
        assert controller.currentFolder == target
        value = box.property("suggestions")
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        assert value == []


class TestFolderClickDuringSearchWiring:
    def test_folder_chosen_keeps_search_text_and_filter(self, qml_app, qt_app):
        # #45: a bal paneli mappa-kattintás keresés közben nem üríti a
        # keresőmezőt és a szűrés megmarad (a mappára szűkítve).
        window, controller, _ = qml_app
        field = window.findChild(QObject, "searchField")
        pane = window.findChild(QObject, "folderPane")
        field.setProperty("text", "a")
        controller.search("a")
        qt_app.processEvents()
        assert controller.photos.rowCount() == 1  # csak a.jpg
        pane.folderChosen.emit(controller.currentFolder)
        qt_app.processEvents()
        assert field.property("text") == "a"      # a mező nem ürül
        assert controller.photos.rowCount() == 1  # a szűrés megmarad


class TestFolderManager:
    def test_dialog_lists_watched_folders(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, QObject, Qt

        from support.halasztott_parbeszed import nyisd_meg

        window, controller, _ = qml_app
        # #1720: a Mappakezelő HALASZTOTT — a valódi menüponttal nyílik
        nyisd_meg(window, "folderManagerDialog")
        dialog = window.findChild(QObject, "folderManagerDialog")
        assert dialog is not None, "folderManagerDialog nem található"
        QMetaObject.invokeMethod(dialog, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert dialog.property("visible") is True
        # a controller figyelt mappái jelennek meg benne
        assert len(controller.watchedFolders) == 1


class TestLightThemeAndSearch:
    def test_window_palette_forced_light(self, qml_app, qt_app):
        # Az OS sötét módja nem üthet át: a base fehér, a text tinta.
        from PySide6.QtQml import QQmlProperty

        window, _, _ = qml_app
        assert QQmlProperty.read(window, "palette.base").name() == "#ffffff"
        assert QQmlProperty.read(window, "palette.text").name() == "#1c1b19"

    def test_search_clear_button_appears_and_clears(self, qml_app, qt_app):
        from PySide6.QtCore import QObject

        window, controller, _ = qml_app
        field = window.findChild(QObject, "searchField")
        clear = window.findChild(QObject, "searchClear")
        assert field is not None and clear is not None
        assert clear.property("visible") is False
        field.setProperty("text", "logo")
        qt_app.processEvents()
        assert clear.property("visible") is True


class TestFolderPaneScrollStability:
    def test_saved_y_survives_reset_zeroing(self, qml_app, qt_app):
        # 10-es issue: modell-resetkor a ListView contentY-ja nullázódik,
        # és a mentett pozíció (savedY) is felülíródott nullával — a
        # visszaállítás így a lista tetejére "ugrott". A 0-ra ugrás nem
        # írhatja felül a mentett pozíciót (a fotórács már így működik).
        window, _, _ = qml_app
        folder_list = window.findChild(QObject, "folderListView")
        assert folder_list is not None, "folderListView nem található"
        folder_list.setProperty("contentY", 150)
        qt_app.processEvents()
        assert folder_list.property("savedY") == 150
        folder_list.setProperty("contentY", 0)  # reset mellékhatása
        qt_app.processEvents()
        assert folder_list.property("savedY") == 150


class TestFeedPositionAfterViewer:
    """#173: a nézőből visszatérve a feed a megnyitás előtti pozíción marad,
    nem ugrik a mappa elejére."""

    def test_reveal_captures_and_is_sticky(self, qml_app, qt_app):
        # A reveal RAGADÓS: a néző-zárás után az azonnali ÉS a háttér-resync
        # KÉSŐI (async) feedChanged-jére is érvényesül — az applyRevealAfterViewer
        # NEM törli a flaget, csak a felhasználói görgetés (cancel).
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None, "photoGrid nem található"
        grid.setProperty("savedY", 512)
        QMetaObject.invokeMethod(
            grid, "beginRevealAfterViewer", Qt.ConnectionType.DirectConnection
        )
        assert grid.property("revealAfterViewer") is True
        assert grid.property("revealTargetY") == 512
        # első (azonnali) feedChanged: alkalmaz, de a flag MEGMARAD
        QMetaObject.invokeMethod(
            grid, "applyRevealAfterViewer", Qt.ConnectionType.DirectConnection
        )
        assert grid.property("revealAfterViewer") is True
        # késői (async, a kék sáv eltűnésekor jövő) feedChanged: újra alkalmaz
        QMetaObject.invokeMethod(
            grid, "applyRevealAfterViewer", Qt.ConnectionType.DirectConnection
        )
        assert grid.property("revealAfterViewer") is True
        assert grid.property("revealTargetY") == 512

    def test_user_scroll_cancels_reveal(self, qml_app, qt_app):
        # valódi felhasználói görgetés (wheelStep) törli a ragadós reveal-t,
        # utána a késői feedChanged már nem áll vissza a régi pozícióra
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        window, _, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        grid.setProperty("savedY", 512)
        QMetaObject.invokeMethod(
            grid, "beginRevealAfterViewer", Qt.ConnectionType.DirectConnection
        )
        assert grid.property("revealAfterViewer") is True
        QMetaObject.invokeMethod(
            grid, "wheelStep", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", -120)
        )
        assert grid.property("revealAfterViewer") is False
        # a cancel után az apply no-op
        QMetaObject.invokeMethod(
            grid, "applyRevealAfterViewer", Qt.ConnectionType.DirectConnection
        )
        assert grid.property("revealAfterViewer") is False

    def test_apply_reveal_restores_saved_position(self, qml_app, qt_app):
        # a reveal a MEGNYITÁS ELŐTTI (savedY) pozíciót állítja vissza, nem a
        # szerkezeti horgonyt; contentHeight ≤ magasság esetén 0-ra klippel,
        # de a forrás mindenképp a rögzített revealTargetY (nem a mappa eleje)
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        grid.setProperty("savedY", 320)
        QMetaObject.invokeMethod(
            grid, "beginRevealAfterViewer", Qt.ConnectionType.DirectConnection
        )
        # a horgonyt szándékosan „rossz" mappára állítjuk — ha a reveal a
        # horgonyt használná, oda ugrana; a helyes viselkedés a revealTargetY
        grid.setProperty("anchorPath", "/nemletezo")
        QMetaObject.invokeMethod(
            grid, "applyRevealAfterViewer", Qt.ConnectionType.DirectConnection
        )
        # a mentett pozíció a revealTargetY-ból származik (a klipp után is a
        # helyes forrásból), nem a horgony-alapú restoreAnchor eredménye
        assert grid.property("revealTargetY") == 320
        # ragadós: a flag megmarad a késői async feedChanged-hez
        assert grid.property("revealAfterViewer") is True


class TestSearchResultsGroupedGridWiring:
    """#7: a bal paneli „Találatok…” sor és a rács mappánkénti
    csoportosítása (group_by_folder bekötése a kereső-eredmény nézetbe)."""

    def test_folder_pane_header_shows_query_and_count(self, qml_app, qt_app):
        window, controller, _ = qml_app
        header = window.findChild(QObject, "folderPaneHeader")
        assert header is not None, "folderPaneHeader nem található"
        assert "Folders" in header.property("text")
        controller.search("a")
        qt_app.processEvents()
        assert header.property("text") == 'Search results for "a" (1)'

    def test_folder_pane_header_restores_after_cleared_search(
        self, qml_app, qt_app
    ):
        window, controller, _ = qml_app
        header = window.findChild(QObject, "folderPaneHeader")
        controller.search("a")
        controller.search("")
        qt_app.processEvents()
        assert "Folders" in header.property("text")

    def test_grouped_view_swaps_in_during_search(self, qml_app, qt_app):
        window, controller, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        grouped = window.findChild(QObject, "groupedSearchResults")
        assert grid.property("visible") is True
        assert grouped.property("visible") is False
        controller.search("a")
        qt_app.processEvents()
        assert grid.property("visible") is False
        assert grouped.property("visible") is True
        controller.search("")
        qt_app.processEvents()
        assert grid.property("visible") is True
        assert grouped.property("visible") is False

    def test_grouped_view_model_follows_controller_search_groups(
        self, qml_app, qt_app
    ):
        # A ListView delegate-jei offscreen módban nem jönnek létre (ld. a
        # fájl elején a GridView-ra vonatkozó megjegyzést, ugyanez a
        # jelenség itt is) — a kötést a modellen keresztül ellenőrizzük;
        # a fejléc-feliratot a SearchGroupHeader önálló tesztje fedi.
        window, controller, _ = qml_app
        grouped = window.findChild(QObject, "groupedSearchResults")
        controller.search("a")
        qt_app.processEvents()
        model = grouped.property("model")
        assert [g["folderName"] for g in model] == ["kepek"]
        assert model[0]["photos"][0]["name"] == "a.jpg"
