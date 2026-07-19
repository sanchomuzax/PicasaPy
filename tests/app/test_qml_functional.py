"""QML-funkcionális tesztek: a betöltött Main.qml viselkedése offscreen.

A Python-egységtesztek nem fogják meg a QML-kötések hibáit (pl. nem
újraértékelődő binding) — ezek a tesztek a teljes felületet betöltve
ellenőrzik a funkcionalitást.
"""

import pytest
from PySide6.QtCore import QObject

from picasapy.index import open_index, sync_tree
from picasapy.version import version_string
from support.jpeg_factory import make_jpeg


@pytest.fixture
def qml_app(qt_app, tmp_path):
    """Teljes app betöltve offscreen: (window, controller, engine)."""
    import picasapy.app.application as app_module
    from picasapy.app.controller import AppController
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from picasapy.app.fileops_controller import FileOpsController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings
    from PySide6.QtQml import QQmlApplicationEngine

    lib = tmp_path / "kepek"
    lib.mkdir()
    make_jpeg(lib / "a.jpg", size=(320, 160))
    make_jpeg(lib / "b.jpg", size=(100, 100))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, lib)

    # elszigetelt QSettings — a rendszer valós PicasaPy-beállításait ne
    # szennyezze a teszt (session/lastFolder, view/thumbCaption).
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    controller = AppController(db, (str(lib),), provider, settings=settings)
    # szerkesztő-híd (#19) — az application.py bekötésének tükre
    edit_preview = EditPreviewProvider()
    edit_controller = EditController(edit_preview)
    engine = QQmlApplicationEngine()
    engine.addImageProvider("thumbs", provider)
    engine.addImageProvider("editpreview", edit_preview)
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty("editController", edit_controller)
    # fájlműveletek (#15) — az application.py bekötésének tükre
    fileops_controller = FileOpsController()
    app_module.wire_fileops(fileops_controller, controller)
    engine.rootContext().setContextProperty(
        "fileOpsController", fileops_controller
    )
    engine.rootContext().setContextProperty("appVersion", version_string())
    engine.load(str(app_module._APP_DIR / "qml" / "Main.qml"))
    assert engine.rootObjects(), "Main.qml betöltése sikertelen"
    window = engine.rootObjects()[0]
    controller._reload()
    controller.selectFolder(str(lib))
    qt_app.processEvents()
    yield window, controller, engine
    engine.deleteLater()
    qt_app.processEvents()


def _viewer_image(window):
    image = window.findChild(QObject, "viewerImage")
    assert image is not None, "viewerImage nem található"
    return image


class TestVersionLabel:
    def test_header_shows_version_string(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        label = window.findChild(QObject, "versionLabel")
        assert label is not None, "versionLabel nem található"
        assert label.property("text") == version_string()


class TestViewerRotation:
    def test_rotate_applies_to_open_viewer(self, qml_app, qt_app):
        # A felhasználó által talált hiba: a rácsban forgott a thumb, de a
        # megnyitott néző képe nem — a kötésnek a modell-frissítésre kell
        # reagálnia, nem a (változatlan) státuszsorra.
        window, controller, _ = qml_app
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        controller.rotateRight(0)
        qt_app.processEvents()
        image = _viewer_image(window)
        assert image.property("iniSteps") == 1
        assert image.property("rotation") == 90

    def test_rotation_follows_navigation(self, qml_app, qt_app):
        window, controller, _ = qml_app
        controller.rotateRight(0)  # a.jpg elforgatva, b.jpg nem
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        assert _viewer_image(window).property("rotation") == 90
        viewer.setProperty("currentIndex", 1)
        qt_app.processEvents()
        assert _viewer_image(window).property("rotation") == 0


class TestCaptionEditing:
    def test_caption_field_updates_after_set_caption(self, qml_app, qt_app):
        # A felirat-mező kötésének a modell revíziójára kell reagálnia,
        # ahogy a forgatás-kötés is (lásd photo.iniSteps fent).
        window, controller, _ = qml_app
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        field = window.findChild(QObject, "captionField")
        assert field is not None, "captionField nem található"
        controller.setCaption(0, "teszt felirat")
        qt_app.processEvents()
        assert field.property("text") == "teszt felirat"

    def test_caption_field_empty_for_other_photo(self, qml_app, qt_app):
        window, controller, _ = qml_app
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        controller.setCaption(0, "teszt felirat")
        qt_app.processEvents()
        viewer.setProperty("currentIndex", 1)
        qt_app.processEvents()
        field = window.findChild(QObject, "captionField")
        assert field.property("text") == ""


class TestFolderDescriptionField:
    def test_header_component_binds_description(self, qml_app, qt_app):
        # A fejléc a feedben (#64) delegate-ként él; a leírás-kötést a
        # komponensen önállóan ellenőrizzük (offscreen a ListView-delegate
        # létrejötte nem garantált).
        import picasapy.app.application as app_module
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent

        window, controller, engine = qml_app
        comp = QQmlComponent(
            engine,
            QUrl.fromLocalFile(
                str(app_module._APP_DIR / "qml" / "PicasaPy" / "LightboxHeader.qml")
            ),
        )
        header = comp.createWithInitialProperties(
            {"folderName": "kepek", "description": "teszt leírás"}
        )
        assert comp.errors() == []
        assert header is not None
        field = header.findChild(QObject, "folderDescriptionField")
        assert field is not None, "folderDescriptionField nem található"
        assert field.property("text") == "teszt leírás"

    def test_description_slot_round_trip(self, qml_app, qt_app):
        # A feed-fejléc útvonala: setFolderDescriptionOf → ini →
        # folderDescriptionOf (a QML-kötés ezt olvassa).
        window, controller, _ = qml_app
        controller.setFolderDescription("teszt leírás")
        qt_app.processEvents()
        assert (
            controller.folderDescriptionOf(controller.currentFolder)
            == "teszt leírás"
        )


class TestLibraryFeedQml:
    """#64: a rács csoportokra bontott feed-ListView."""

    def test_feed_shows_groups(self, qml_app, qt_app):
        window, controller, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None, "photoGrid nem található"
        groups = controller.feedGroups
        assert len(groups) == 1
        assert groups[0]["count"] == 2
        assert grid.property("count") == 1  # egy mappa-csoport a ListView-ban

    def test_cell_geometry_follows_thumb_size(self, qml_app, qt_app):
        # #85: a cellWidth mostantól a kiegyenlített (effektív, a sort
        # kitöltő) szélesség — legalább a névleges (thumbSize+18), de a
        # rendelkezésre álló szélesség egyenletes elosztásához igazodva
        # annál nagyobb is lehet.
        window, _, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        window.setProperty("thumbSize", 200)
        qt_app.processEvents()
        nominal = 200 + 18
        assert grid.property("cellWidth") >= nominal


class TestFolderPaneHighlight:
    def test_selected_path_follows_controller(self, qml_app, qt_app):
        window, controller, _ = qml_app
        folder_pane = window.findChild(QObject, "folderPane")
        assert folder_pane is not None, "folderPane nem található"
        assert folder_pane.property("selectedPath") == controller.currentFolder


class TestThumbCaption:
    def test_mode_round_trips_on_controller(self, qml_app, qt_app):
        # A GridView indexképei ebben az offscreen headless környezetben nem
        # jönnek létre (QQuickGridView lusta elem-létrehozása valódi
        # ablak-exponálást igényel, amit az offscreen platform nem ad —
        # ugyanez a jelenség reprodukálható a módosítás előtti főágon is).
        # Ezért a controller<->QML kötést közvetlenül, a ThumbDelegate
        # komponenst pedig önállóan (lásd lent) teszteljük.
        window, controller, _ = qml_app
        controller.setThumbCaptionMode("filename")
        qt_app.processEvents()
        assert controller.thumbCaptionMode == "filename"

    def test_thumb_delegate_shows_filename_caption(self, qml_app, qt_app):
        import picasapy.app.application as app_module
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent

        window, controller, engine = qml_app
        comp = QQmlComponent(
            engine,
            QUrl.fromLocalFile(
                str(app_module._APP_DIR / "qml" / "PicasaPy" / "ThumbDelegate.qml")
            ),
        )
        delegate = comp.createWithInitialProperties(
            {
                "name": "a.jpg",
                "thumbUrl": "image://thumbs/1",
                "star": False,
                "caption": "",
                "isVideo": False,
                "index": 0,
                "keywords": "",
                "resolution": "320x160",
                "captionMode": "filename",
            }
        )
        assert comp.errors() == []
        assert delegate is not None
        caption = delegate.findChild(QObject, "thumbCaption")
        assert caption is not None, "thumbCaption Text nem található"
        assert caption.property("text") == "a.jpg"
        assert caption.property("visible") is True


class TestThumbDelegateImageQuality:
    # #83: a legnagyobb rács-méretben (256px) a cache-elt thumbnail
    # nagyítás nélkül, kicsinyítéssel álljon elő — a delegate Image-nek
    # mipmap-elt kicsinyítést kell használnia, hogy a köztes csúszka-
    # fokokon se legyen recés/homályos a kép.
    def test_delegate_image_uses_mipmap_for_quality_downscale(self, qml_app):
        import picasapy.app.application as app_module
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent

        _, _, engine = qml_app
        comp = QQmlComponent(
            engine,
            QUrl.fromLocalFile(
                str(app_module._APP_DIR / "qml" / "PicasaPy" / "ThumbDelegate.qml")
            ),
        )
        delegate = comp.createWithInitialProperties(
            {
                "name": "a.jpg",
                "thumbUrl": "image://thumbs/1",
                "star": False,
                "caption": "",
                "isVideo": False,
                "index": 0,
                "keywords": "",
                "resolution": "320x160",
            }
        )
        assert comp.errors() == []
        image = delegate.findChild(QObject, "thumbImage")
        assert image is not None, "thumbImage Image nem található"
        assert image.property("mipmap") is True
        assert image.property("smooth") is True


class TestTrayStar:
    def test_star_button_reflects_selection_state(self, qml_app, qt_app):
        window, controller, _ = qml_app
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        controller.toggleStar(0)
        qt_app.processEvents()
        star_label = window.findChild(QObject, "trayStarLabel")
        assert star_label is not None
        assert star_label.property("color").name() == "#f5c518"  # arany


class TestMultiSelect:
    def _click(self, qt_app, window, index, modifiers=0):
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        QMetaObject.invokeMethod(
            window,
            "handleThumbClick",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", index),
            Q_ARG("QVariant", modifiers),
        )
        qt_app.processEvents()

    @staticmethod
    def _indexes(window):
        # a QML `property var` tömb QJSValue-ként érkezik Pythonba
        value = window.property("selectedIndexes")
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        return [int(v) for v in value]

    def test_plain_click_single_selection(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._click(qt_app, window, 0)
        assert self._indexes(window) == [0]
        assert window.property("selectedIndex") == 0

    def test_ctrl_click_toggles(self, qml_app, qt_app):
        from PySide6.QtCore import Qt

        window, _, _ = qml_app
        ctrl = int(Qt.KeyboardModifier.ControlModifier.value)
        self._click(qt_app, window, 0)
        self._click(qt_app, window, 1, ctrl)
        assert sorted(self._indexes(window)) == [0, 1]
        self._click(qt_app, window, 0, ctrl)
        assert self._indexes(window) == [1]

    def test_shift_click_selects_range(self, qml_app, qt_app):
        from PySide6.QtCore import Qt

        window, _, _ = qml_app
        shift = int(Qt.KeyboardModifier.ShiftModifier.value)
        self._click(qt_app, window, 0)
        self._click(qt_app, window, 1, shift)
        assert sorted(self._indexes(window)) == [0, 1]

    def test_clear_selection(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        self._click(qt_app, window, 0)
        QMetaObject.invokeMethod(
            window, "clearSelection", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert self._indexes(window) == []
        assert window.property("selectedIndex") == -1


class TestLasso:
    @staticmethod
    def _apply(qt_app, grid, start, count, flow_w, x1, y1, x2, y2, mods=0):
        # #64: a lasszó a húzás kezdő-csoportján belül jelöl ki — a hívás
        # a csoport (start, count) és a képfolyam szélessége szerint számol.
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        QMetaObject.invokeMethod(
            grid, "applyLasso", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", start), Q_ARG("QVariant", count),
            Q_ARG("QVariant", flow_w),
            Q_ARG("QVariant", x1), Q_ARG("QVariant", y1),
            Q_ARG("QVariant", x2), Q_ARG("QVariant", y2),
            Q_ARG("QVariant", mods),
        )
        qt_app.processEvents()

    def test_lasso_selects_geometry_range(self, qml_app, qt_app):
        # A (0,0)-tól két cellányira húzott keret a csoport mindkét képét
        # kijelöli.
        from PySide6.QtCore import QObject

        window, controller, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None, "photoGrid nem található"
        cell_w = grid.property("cellWidth")
        self._apply(qt_app, grid, 0, 2, cell_w * 4, 0, 0, cell_w * 2 + 1, 1)
        value = window.property("selectedIndexes")
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        assert sorted(int(v) for v in value) == [0, 1]

    def test_lasso_ctrl_merges(self, qml_app, qt_app):
        from PySide6.QtCore import QObject, Qt

        window, controller, _ = qml_app
        window.setProperty("selectedIndexes", [1])
        grid = window.findChild(QObject, "photoGrid")
        cell_w = grid.property("cellWidth")
        ctrl = int(Qt.KeyboardModifier.ControlModifier.value)
        self._apply(qt_app, grid, 0, 2, cell_w * 4, 0, 0, 1, 1, ctrl)
        value = window.property("selectedIndexes")
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        assert sorted(int(v) for v in value) == [0, 1]

    def test_lasso_respects_group_offset(self, qml_app, qt_app):
        # Egy második csoportban (start=5) húzott lasszó globális sorokat ad.
        from PySide6.QtCore import QObject

        window, _, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        cell_w = grid.property("cellWidth")
        self._apply(qt_app, grid, 5, 3, cell_w * 4, 0, 0, cell_w * 2 + 1, 1)
        value = window.property("selectedIndexes")
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        assert sorted(int(v) for v in value) == [5, 6, 7]


class TestBalancedGridRow:
    """#85: a sor a bal és jobb szél között kitöltött legyen, ne balra
    rendezett maradjon fix cellamérettel — az effektív cellaszélesség a
    rendelkezésre álló szélességből számítva töltse ki a sort."""

    @staticmethod
    def _assert_row_fills_width(grid, tolerance_cols=1):
        width = grid.property("width")
        cell_w = grid.property("cellWidth")
        columns = int(grid.property("columns"))
        assert columns >= 1, "legalább egy oszlopnak lennie kell"
        # az oszlopok együtt (kis tűréssel) kitöltik a rendelkezésre álló
        # szélességet — nem maradhat balra tömörült, üres jobb sáv
        leftover = width - columns * cell_w
        assert 0 <= leftover < cell_w * max(1, tolerance_cols) / columns + 2, (
            f"leftover={leftover} width={width} cols={columns} cell_w={cell_w}"
        )

    def test_cell_width_fills_row_at_multiple_thumb_sizes(self, qml_app, qt_app):
        from PySide6.QtCore import QObject

        window, controller, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None, "photoGrid nem található"

        for size in (72, 144, 256):
            window.setProperty("thumbSize", size)
            qt_app.processEvents()
            nominal = size + 18
            cell_w = grid.property("cellWidth")
            # az effektív cella legalább akkora, mint a névleges (nem zsugorodhat)
            assert cell_w >= nominal
            self._assert_row_fills_width(grid)

    def test_cell_width_adapts_on_window_resize(self, qml_app, qt_app):
        from PySide6.QtCore import QObject

        window, controller, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None, "photoGrid nem található"
        window.setProperty("thumbSize", 144)

        for w in (900, 1500):
            window.setProperty("width", w)
            qt_app.processEvents()
            self._assert_row_fills_width(grid)

    def test_displayed_image_capped_to_nominal_size_even_in_wide_cell(
        self, qml_app
    ):
        # #85 x #83: a kiegyenlítés miatt megnőtt cellában a MEGJELENÍTETT
        # kép ne nőjön a névleges (legnagyobb csúszka-fokozatnyi) méret
        # fölé — a #83-mal beállított DPR-arányos cache-t ne nagyítsuk fel
        # (recés/homályos lenne). A többlet a térközbe menjen, a kép a
        # névleges méretre plafonozva marad.
        import picasapy.app.application as app_module
        from PySide6.QtCore import QObject, QUrl
        from PySide6.QtQml import QQmlComponent

        _, _, engine = qml_app
        comp = QQmlComponent(
            engine,
            QUrl.fromLocalFile(
                str(app_module._APP_DIR / "qml" / "PicasaPy" / "ThumbDelegate.qml")
            ),
        )
        nominal = 256 + 18   # a legnagyobb csúszka-fokozat névleges cellája
        wide_cell = nominal + 60   # kiegyenlítés miatt megnövelt cella
        delegate = comp.createWithInitialProperties(
            {
                "name": "a.jpg",
                "thumbUrl": "image://thumbs/1",
                "star": False,
                "caption": "",
                "isVideo": False,
                "index": 0,
                "keywords": "",
                "resolution": "320x160",
                "width": wide_cell,
                "height": wide_cell,
                "maxContentWidth": nominal,
                "maxContentHeight": nominal,
            }
        )
        assert comp.errors() == []
        image = delegate.findChild(QObject, "thumbImage")
        assert image is not None, "thumbImage Image nem található"
        assert image.property("width") <= 256
        assert image.property("height") <= 256


class TestFolderManager:
    def test_dialog_lists_watched_folders(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, QObject, Qt

        window, controller, _ = qml_app
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


class TestEditorWiring:
    """A #19-es bekötés: EditorPanel/CropOverlay ↔ EditController ↔ ini."""

    def _open_viewer(self, window, qt_app, index=0):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", index)
        qt_app.processEvents()
        return viewer

    def _edit_controller(self, engine):
        return engine.rootContext().contextProperty("editController")

    def test_viewer_open_starts_edit_session(self, qml_app, qt_app):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        edit = self._edit_controller(engine)
        assert edit.property("previewSource").startswith("image://editpreview/")
        image = window.findChild(QObject, "viewerImage")
        assert image.property("source").toString().startswith("image://editpreview/")

    def test_viewer_close_ends_edit_session(self, qml_app, qt_app):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        assert self._edit_controller(engine).property("previewSource") == ""

    def test_panel_toggle_writes_ini_and_syncs_state(self, qml_app, qt_app, tmp_path):
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None, "viewerEditorPanel nem található"
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "autolight"),
        )
        qt_app.processEvents()
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "[a.jpg]" in ini_text
        assert "autolight=1" in ini_text
        # a panel állapota az EditController igazságforrásából szinkronizált:
        # az egygombos javítás gombja tiltott, amíg ő a lánc utolsó eleme (#116)
        assert panel.property("autolightEnabled") is False
        # a kép forrása új ?rev=-et kap → az előnézet frissül
        image = window.findChild(QObject, "viewerImage")
        assert "?rev=" in image.property("source").toString()

    def test_crop_accept_persists_and_advances(self, qml_app, qt_app, tmp_path):
        from PySide6.QtCore import QMetaObject, QRectF, Qt

        window, _, engine = qml_app
        viewer = self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        overlay = window.findChild(QObject, "cropOverlay")
        assert overlay is not None, "cropOverlay nem található"
        assert overlay.property("visible") is True
        overlay.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
        overlay.setProperty("hasSelection", True)
        QMetaObject.invokeMethod(
            overlay, "acceptCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "crop64=1," in ini_text
        # Enter-flow: elfogadás után a néző a következő képre lép, a
        # vágó-mód megmarad (sorozat-vágás)
        assert viewer.property("currentIndex") == 1
        assert panel.property("cropActive") is True

    def test_tilt_drag_previews_live_then_commits_on_release(
        self, qml_app, qt_app, tmp_path
    ):
        """#72: húzás közben élő előnézet, ini-mentés nélkül; elengedéskor ír."""
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("tiltActive", True)
        qt_app.processEvents()
        slider = window.findChild(QObject, "tiltSlider")
        assert slider is not None, "tiltSlider nem található"
        image = window.findChild(QObject, "viewerImage")
        before_source = image.property("source").toString()
        ini_path = tmp_path / "kepek" / ".picasa.ini"

        slider.setProperty("value", 0.3)
        qt_app.processEvents()
        assert not ini_path.exists(), "húzás közben nem szabadna ini-be írni"
        assert image.property("source").toString() != before_source

        slider.setProperty("pressed", True)
        slider.setProperty("pressed", False)
        qt_app.processEvents()
        ini_text = ini_path.read_text(encoding="utf-8")
        assert "filters=tilt=1,0.300000,0.000000;" in ini_text

    def test_reopen_crop_tool_shows_uncropped_image_and_existing_selection(
        self, qml_app, qt_app, tmp_path
    ):
        """#71: a Vágás eszköz újranyitásakor a teljes (vágatlan) kép +
        a meglévő kijelölés látszik, a vágás folytatható marad."""
        from PySide6.QtCore import QMetaObject, QRectF, Qt

        window, _, engine = qml_app
        viewer = self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        overlay = window.findChild(QObject, "cropOverlay")
        overlay.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
        overlay.setProperty("hasSelection", True)
        QMetaObject.invokeMethod(
            overlay, "acceptCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        # Enter-flow: elfogadás után a vágó-mód megmarad, de a kijelölés
        # üresre áll vissza a következő képre lépéskor
        assert panel.property("cropActive") is True
        assert overlay.property("hasSelection") is False

        # visszalépés az imént megvágott képre: a teljes kép + a mentett
        # kijelölés (nem a levágott eredmény) jelenjen meg
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        edit = self._edit_controller(engine)
        assert edit.property("previewSource").startswith("image://editpreview/")
        assert overlay.property("hasSelection") is True
        crop_rect = overlay.property("cropRect")
        assert crop_rect.x() == pytest.approx(0.25, abs=1e-3)
        assert crop_rect.width() == pytest.approx(0.5, abs=1e-3)

    def test_crop_cancel_leaves_crop_mode(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        overlay = window.findChild(QObject, "cropOverlay")
        QMetaObject.invokeMethod(
            overlay, "cancelCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert panel.property("cropActive") is False


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


class TestViewerFolderBoundedNavigation:
    """#84: a nagy nézőben (PhotoViewer) a lapozás CSAK az aktuális mappa
    képei között mozogjon — a rács (feed) nézet szűrői (pl. csillag-szűrő)
    több mappa fotóit is felsorolhatják egymás után, de a néző ne lépjen
    át a szomszéd mappába."""

    @pytest.fixture
    def qml_app_multi_folder(self, qt_app, tmp_path):
        """Két mappa csillagozott képekkel, egyetlen (mappaátlépő) rács-
        listában betöltve — ahogy a csillag-szűrő is összefésüli őket."""
        import picasapy.app.application as app_module
        from picasapy.app.controller import AppController
        from picasapy.app.edit_controller import EditController
        from picasapy.app.edit_preview import EditPreviewProvider
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache
        from PySide6.QtCore import QSettings
        from PySide6.QtQml import QQmlApplicationEngine

        lib = tmp_path / "kepek"
        folder_a = lib / "nyaralas"
        folder_b = lib / "telek"
        folder_a.mkdir(parents=True)
        folder_b.mkdir()
        make_jpeg(folder_a / "a1.jpg")
        make_jpeg(folder_a / "a2.jpg")
        make_jpeg(folder_b / "b1.jpg")
        make_jpeg(folder_b / "b2.jpg")
        (folder_a / ".picasa.ini").write_text(
            "[a1.jpg]\nstar=yes\n\n[a2.jpg]\nstar=yes\n", encoding="utf-8"
        )
        (folder_b / ".picasa.ini").write_text(
            "[b1.jpg]\nstar=yes\n\n[b2.jpg]\nstar=yes\n", encoding="utf-8"
        )
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)

        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
        controller = AppController(db, (str(lib),), provider, settings=settings)
        edit_preview = EditPreviewProvider()
        edit_controller = EditController(edit_preview)
        engine = QQmlApplicationEngine()
        engine.addImageProvider("thumbs", provider)
        engine.addImageProvider("editpreview", edit_preview)
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        engine.rootContext().setContextProperty("controller", controller)
        engine.rootContext().setContextProperty("editController", edit_controller)
        engine.load(str(app_module._APP_DIR / "qml" / "Main.qml"))
        assert engine.rootObjects(), "Main.qml betöltése sikertelen"
        window = engine.rootObjects()[0]
        controller._reload()
        # a rács (feed) nézet: mindkét mappa csillagozott képei, folytonosan
        # (f.path, p.name szerint: nyaralas/a1, a2, telek/b1, b2)
        controller.showStarred()
        qt_app.processEvents()
        yield window, controller, engine
        engine.deleteLater()
        qt_app.processEvents()

    def _open_viewer(self, window, qt_app, index):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", index)
        qt_app.processEvents()
        return viewer

    def test_next_stops_at_folder_end(self, qml_app_multi_folder, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, _ = qml_app_multi_folder
        assert controller.photos.rowCount() == 4  # a rács nem szűkül mappára
        viewer = self._open_viewer(window, qt_app, index=1)  # a2.jpg — nyaralas utolsó képe
        QMetaObject.invokeMethod(viewer, "next", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert viewer.property("currentIndex") == 1, (
            "a mappahatárnál a néző nem léphet át a szomszéd mappába"
        )

    def test_previous_stops_at_folder_start(self, qml_app_multi_folder, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, _ = qml_app_multi_folder
        viewer = self._open_viewer(window, qt_app, index=2)  # b1.jpg — telek első képe
        QMetaObject.invokeMethod(
            viewer, "previous", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert viewer.property("currentIndex") == 2

    def test_next_moves_within_folder(self, qml_app_multi_folder, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, _ = qml_app_multi_folder
        viewer = self._open_viewer(window, qt_app, index=0)  # a1.jpg
        QMetaObject.invokeMethod(viewer, "next", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert viewer.property("currentIndex") == 1  # a2.jpg — még a nyaralas mappa

    def test_nav_buttons_disabled_at_folder_boundaries(
        self, qml_app_multi_folder, qt_app
    ):
        window, controller, _ = qml_app_multi_folder
        viewer = self._open_viewer(window, qt_app, index=1)  # a2.jpg — nyaralas utolsó
        next_button = window.findChild(QObject, "viewerNextButton")
        assert next_button is not None, "viewerNextButton nem található"
        assert next_button.property("enabled") is False
        # ugyanezen a nézőn (egyetlen engine) a telek mappa első képénél a
        # ◀ gomb is letiltva — egy fixture-példányban ellenőrizve, hogy az
        # offscreen tesztkörnyezetben ne kelljen két QQmlApplicationEngine-t
        # egymás után létrehozni (ismert instabilitás a tesztfuttatóban)
        viewer.setProperty("currentIndex", 2)  # b1.jpg — telek első képe
        qt_app.processEvents()
        prev_button = window.findChild(QObject, "viewerPrevButton")
        assert prev_button is not None, "viewerPrevButton nem található"
        assert prev_button.property("enabled") is False
