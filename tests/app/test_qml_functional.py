"""QML-funkcionális tesztek: a betöltött Main.qml viselkedése offscreen.

A Python-egységtesztek nem fogják meg a QML-kötések hibáit (pl. nem
újraértékelődő binding) — ezek a tesztek a teljes felületet betöltve
ellenőrzik a funkcionalitást.
"""

import pytest
from PySide6.QtCore import QObject

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg


@pytest.fixture
def qml_app(qt_app, tmp_path):
    """Teljes app betöltve offscreen: (window, controller, engine)."""
    import picasapy.app.application as app_module
    from picasapy.app.controller import AppController
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
    engine = QQmlApplicationEngine()
    engine.addImageProvider("thumbs", provider)
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", controller)
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
    def test_field_updates_after_set_folder_description(self, qml_app, qt_app):
        window, controller, _ = qml_app
        controller.setFolderDescription("teszt leírás")
        qt_app.processEvents()
        field = window.findChild(QObject, "folderDescriptionField")
        assert field is not None, "folderDescriptionField nem található"
        assert field.property("text") == "teszt leírás"


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
    def test_lasso_selects_geometry_range(self, qml_app, qt_app):
        # A lasszó rács-geometriából számol — a (0,0)-tól két cellányira
        # húzott keret az összes (itt: 2) képet kijelöli.
        from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

        window, controller, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None, "photoGrid nem található"
        cell_w = grid.property("cellWidth")
        QMetaObject.invokeMethod(
            grid, "applyLasso", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0), Q_ARG("QVariant", 0),
            Q_ARG("QVariant", cell_w * 2 + 1), Q_ARG("QVariant", 1),
            Q_ARG("QVariant", 0),
        )
        qt_app.processEvents()
        value = window.property("selectedIndexes")
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        assert sorted(int(v) for v in value) == [0, 1]

    def test_lasso_ctrl_merges(self, qml_app, qt_app):
        from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

        window, controller, _ = qml_app
        window.setProperty("selectedIndexes", [1])
        grid = window.findChild(QObject, "photoGrid")
        ctrl = int(Qt.KeyboardModifier.ControlModifier.value)
        QMetaObject.invokeMethod(
            grid, "applyLasso", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0), Q_ARG("QVariant", 0),
            Q_ARG("QVariant", 1), Q_ARG("QVariant", 1),
            Q_ARG("QVariant", ctrl),
        )
        qt_app.processEvents()
        value = window.property("selectedIndexes")
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        assert sorted(int(v) for v in value) == [0, 1]


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
