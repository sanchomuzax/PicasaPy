"""Qt tesztkörnyezet: offscreen platform, egyetlen alkalmazás-példány."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qt_app():
    from PySide6.QtGui import QGuiApplication

    app = QGuiApplication.instance() or QGuiApplication([])
    yield app


@pytest.fixture(autouse=True)
def qml_warnings():
    """#718: figyeli a Qt/QML üzenetkezelőt (qInstallMessageHandler), és a
    teszt VÉGÉN hibát dob, ha QML-SZKRIPTHIBA jelent meg (pl. „Cannot read
    property … of null"). Eredetileg csak a `tests/app/qml_functional/`
    alatt futott (#305/#309) — a #718 kiterjeszti a `tests/app/` alatt
    KÖZVETLENÜL élő `test_qml_*.py` fájlokra is, mert ott is QML-t töltő
    tesztek vannak, és őr nélkül a hibák némán a stderr-re mentek.

    A szűrésről (mire hasal el és mire nem, és miért) ld. a
    `support/qml_warning_filter.py` modul-docstringjét (#309).

    A `tests/app/qml_functional/conftest.py` UGYANEZEN A NÉVEN definiál
    saját `qml_warnings` fixture-t — pytest a közelebbi (alkönyvtárbeli)
    definíciót használja, ez a szülőbeli teljesen ÁRNYÉKOLVA van ott, tehát
    az őr nem fut le kétszer egyazon teszten.

    `autouse=True`, ezért minden e könyvtárbeli teszthez automatikusan
    társul, `qml_app`-ot használóhoz és nem-használóhoz egyaránt — nem kell
    minden tesztfüggvény szignatúráját módosítani.

    A fixture-sorrend a lényeg: mivel ez a fixture ELSŐKÉNT áll fel (a
    pytest a szignatúrában/autouse-ban elsőként szereplőt előbb állítja
    fel), a lebontása UTOLSÓKÉNT történik (LIFO) — vagyis a handler még
    aktív, amikor a `qml_app` fixture a tesztek végén elvégzi az
    `engine.deleteLater()` + `processEvents()` hívást, ami a null-őrök
    nélkül a fenti figyelmeztetéseket generálná."""
    from PySide6.QtCore import QtMsgType, qInstallMessageHandler

    from support.qml_warning_filter import is_qml_script_error

    messages: list[str] = []

    def _handler(msg_type, context, message):
        if msg_type in (
            QtMsgType.QtWarningMsg,
            QtMsgType.QtCriticalMsg,
            QtMsgType.QtFatalMsg,
        ) and is_qml_script_error(message):
            messages.append(message)

    previous = qInstallMessageHandler(_handler)
    yield messages
    qInstallMessageHandler(previous)
    assert not messages, (
        "QML-szkripthiba jelent meg a teszt során (#718/#305) — "
        "valószínűleg hiányzó null-őr egy `controller`-kötésben:\n"
        + "\n".join(messages)
    )


@pytest.fixture
def qml_app(qt_app, tmp_path):
    """Teljes app betöltve offscreen: (window, controller, lib, engine) —
    az application.py bekötésének tükre (controller + edit + fileops).

    A test_qml_functional.py saját, azonos nevű fixture-e ezt árnyékolja
    (ott a visszatérési alak is más); az új funkcionális teszt-fájlok ezt
    a közöset használják."""
    import picasapy.app.application as app_module
    from picasapy.app.controller import AppController
    from picasapy.app.dedup_controller import DedupController
    from picasapy.app.discovery_controller import DiscoveryController
    from picasapy.app.drop_import_controller import DropImportController
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from picasapy.app.effect_thumbnails import EffectThumbnailProvider
    from picasapy.app.face_scan_controller import FaceScanController
    from picasapy.app.faces_helper import FacesHelper
    from picasapy.app.fileops_controller import FileOpsController
    from picasapy.app.folder_tree_controller import FolderTreeController
    from picasapy.app.import_source_controller import ImportSourceController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.app.timeline_controller import TimelineController
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from picasapy.version import version_string
    from PySide6.QtCore import QSettings
    from picasapy.app.worker_thread import (
        running_background_workers,
        wait_for_all_background_workers,
    )
    from PySide6.QtQml import QQmlApplicationEngine

    from support.jpeg_factory import make_jpeg

    lib = tmp_path / "kepek"
    lib.mkdir()
    make_jpeg(lib / "a.jpg", size=(320, 160))
    make_jpeg(lib / "b.jpg", size=(100, 100))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, lib)

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    # #960: a kollázs kimeneti mappája — ide kerül az `autosave.cxf`
    # piszkozat is. Enélkül a kollázst indító tesztek a felhasználó VALÓDI
    # képmappájába (`~/Pictures/Kollázsok`) írnának.
    settings.setValue("collage/outputDir", str(tmp_path / "kollazsok"))
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    controller = AppController(db, (str(lib),), provider, settings=settings)
    # #367: az általános ConfirmDialog "Ne kérdezze újra" tára — ugyanaz az
    # elszigetelt settings, mint a controlleré
    from picasapy.app.confirm_settings_bridge import ConfirmSettingsBridge

    confirm_settings = ConfirmSettingsBridge(settings=settings)
    edit_preview = EditPreviewProvider()
    edit_controller = EditController(edit_preview)
    # effekt-gomb bélyegképek (#338) — az application.py bekötésének tükre
    effect_thumb_provider = EffectThumbnailProvider(provider.photo_record)
    fileops_controller = FileOpsController()
    app_module.wire_fileops(fileops_controller, controller)
    discovery_controller = DiscoveryController(add_folder=controller.addWatchedFolder)
    # kép/mappa ablakra ejtése (#237) — az application.py bekötésének tükre
    drop_import_controller = DropImportController(
        add_folder=controller.addWatchedFolder
    )
    folder_tree_controller = FolderTreeController()
    # Duplikátum-kezelő (#287) — az application.py bekötésének tükre
    dedup_controller = DedupController(db, provider)
    # Import forrásból (#23) — az application.py bekötésének tükre
    import_source_controller = ImportSourceController(
        provider,
        add_folder=controller.addWatchedFolder,
        index_path=db,
        settings=settings,
    )
    faces_helper = FacesHelper()
    # #26 (3. lépcső) — az application.py bekötésének tükre
    face_scan_controller = FaceScanController(db, faces_helper=faces_helper)
    # Időrend nézet (#24) — az application.py bekötésének tükre: a
    # thumbnail-provider a controllerrel KÖZÖS példány
    timeline_controller = TimelineController(db, provider)
    controller.syncFinished.connect(timeline_controller.reload)
    engine = QQmlApplicationEngine()
    engine.addImageProvider("thumbs", provider)
    engine.addImageProvider("editpreview", edit_preview)
    engine.addImageProvider("effectthumb", effect_thumb_provider)
    engine.addImageProvider("collagepreview", controller.collage_preview_provider)
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty("editController", edit_controller)
    engine.rootContext().setContextProperty(
        "fileOpsController", fileops_controller
    )
    engine.rootContext().setContextProperty(
        "discoveryController", discovery_controller
    )
    engine.rootContext().setContextProperty(
        "dropImportController", drop_import_controller
    )
    engine.rootContext().setContextProperty(
        "folderTreeController", folder_tree_controller
    )
    engine.rootContext().setContextProperty("dedupController", dedup_controller)
    engine.rootContext().setContextProperty(
        "importSourceController", import_source_controller
    )
    engine.rootContext().setContextProperty("facesHelper", faces_helper)
    engine.rootContext().setContextProperty(
        "faceScanController", face_scan_controller
    )
    engine.rootContext().setContextProperty(
        "timelineController", timeline_controller
    )
    engine.rootContext().setContextProperty("appVersion", version_string())
    engine.rootContext().setContextProperty("confirmSettings", confirm_settings)
    # #189: a splash-híd — a funkcionális tesztek kész (ready) állapotból
    # indulnak, hogy a splash-overlay ne takarjon semmit
    from picasapy.app.startup_status import StartupStatus

    startup_status = StartupStatus()
    startup_status.finish()
    engine.rootContext().setContextProperty("startupStatus", startup_status)
    engine.load(str(app_module._APP_DIR / "qml" / "Main.qml"))
    assert engine.rootObjects(), "Main.qml betöltése sikertelen"
    window = engine.rootObjects()[0]
    controller._reload()
    controller.selectFolder(str(lib))
    qt_app.processEvents()
    yield window, controller, lib, engine
    engine.deleteLater()
    qt_app.processEvents()
    # #438: minden nyilvántartott daemon-szál bevárása, AMÍG a controllerek
    # még élnek — a #430 SIGSEGV-osztály elkerülése (ld.
    # picasapy.app.worker_thread.BackgroundWorkerMixin).
    # #988/#999: EGY hívás vár be MINDEN nyilvántartott háttérmunkát — a
    # folyamat összes `_start_background`-szálát és a bejelentkezett
    # `QThreadPool`-okat. Korábban itt egy KÉZZEL FELSOROLT controller-lista
    # állt, és elcsúszott: a fixture által létrehozott `EditController`,
    # `FaceScanController` és a két bélyegkép-szolgáltató pool-ja kimaradt
    # belőle. Ebből lett két, véletlenszerűen pirosló SIGSEGV a CI-ben.
    assert wait_for_all_background_workers(30.0), (
        "háttérmunka nem állt le a teardownban (#430/#438/#988/#999): "
        + ", ".join(running_background_workers())
    )
