"""application startup qml az alkalmazásindítóhoz."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtQml import QQmlApplicationEngine

from picasapy.version import version_string
from . import application as _app
from . import display_photo_provider
from .color_palette import ColorPaletteProvider
from .option_settings import initialize_option_settings

def _startup_step_create_qml_engine(state):
    controller = state.controller
    data_dir = state.data_dir
    edit_preview = state.edit_preview
    effect_thumb_provider = state.effect_thumb_provider
    provider = state.provider
    thumb_cache = state.thumb_cache
    timeline = state.timeline

    # #1653: a QML-MOTOR létrehozása külön szakasz. Az eddigi közös
    # mérőpont („a többi vezérlő létrehozása és regisztrálása") egyben
    # mérte a vezérlők konstruktorait, a `QQmlApplicationEngine()`-t és a
    # kontextus-tulajdonságok bekötését. A jegyben felsorolt windowsos
    # gyanúk közül a **Qt plugin-keresés** kizárólag a motor
    # létrehozásakor jelentkezne — összevont szakaszban láthatatlan.
    timeline.mark("a többi vezérlő létrehozása")
    engine = QQmlApplicationEngine()

    color_palette_provider = ColorPaletteProvider()
    engine.addImageProvider("colorpalette", color_palette_provider)
    engine.rootContext().setContextProperty("colorPalette", color_palette_provider)
    engine.addImageProvider("thumbs", provider)
    engine.addImageProvider("editpreview", edit_preview)
    # #1640: a diavetítés teljes felbontású képe — a megjelenítési móddal
    engine.addImageProvider(
        display_photo_provider.PROVIDER_NAME,
        display_photo_provider.DisplayPhotoProvider(),
    )
    engine.addImageProvider("effectthumb", effect_thumb_provider)
    # #920: élő kollázs-előnézet. A szolgáltatót a vezérlő birtokolja
    # (lusta init), mert a kollázs állapota is ott él.
    engine.addImageProvider("collagepreview", controller.collage_preview_provider)
    # #4820: az élő filmátmenet ugyanazt a képkocka-geometriát kéri, mint az export.
    engine.addImageProvider(
        "moviepreview", controller.movie_transition_preview_provider
    )

    # #2049: a bal hasáb fasorainak fotó-kupac borítója. A lekérdező az
    # INDEXBŐL veszi a mappa fotóit, névsorban — a kupacba a lista első
    # legfeljebb négy eleme kerül (`0x004237ab`), tehát a sorrend
    # látszik is a képen.
    # #2984: a lekérdezés MODUL-SZINTŰ (`folder_cover_provider.borito_belyegkepe`),
    # hogy őr tudjon rá futni — lezárásként évekig hibásan állt, és a
    # `lambda`-val hívott őrök nem látták.
    # #4876: a borító a rács bélyegkép-tárából jön — meleg tárral az eredeti
    # fotót nem dekódoljuk újra minden indításkor.
    folder_cover_provider = _app._create_folder_cover_provider(data_dir, thumb_cache)
    engine.addImageProvider("foldercover", folder_cover_provider)
    engine.addImportPath(str(_app._APP_DIR / "qml"))
    # #1653: idáig tart a motor felállítása (konstruktor + kép-szolgáltatók
    # + import-útvonal); innentől már csak kontextus-bekötés következik.
    timeline.mark("QML-motor létrehozása és import-útvonalak")

    state.engine = engine
    state.color_palette_provider = color_palette_provider
    state.folder_cover_provider = folder_cover_provider

def _startup_step_register_qml_context(state):
    app = state.app
    backup_controller = state.backup_controller
    cache_dir = state.cache_dir
    config_dir = state.config_dir
    camera_capture_controller = state.camera_capture_controller
    confirm_settings = state.confirm_settings
    controller = state.controller
    data_dir = state.data_dir
    dedup_controller = state.dedup_controller
    discovery_controller = state.discovery_controller
    drop_import_controller = state.drop_import_controller
    edit_controller = state.edit_controller
    email_controller = state.email_controller
    engine = state.engine
    fileops_controller = state.fileops_controller
    folder_hierarchy_controller = state.folder_hierarchy_controller
    folder_tree_controller = state.folder_tree_controller
    gombsav = state.gombsav
    import_source_controller = state.import_source_controller
    progress_log = state.progress_log
    print_controller = state.print_controller
    second_preview = state.second_preview
    startup_status = state.startup_status
    timeline = state.timeline
    timeline_controller = state.timeline_controller
    _lathato_fotok = state._lathato_fotok
    web_export_controller = state.web_export_controller

    ScreenCaptureController = _app._lazy_app_symbol("ScreenCaptureController")
    screen_capture_controller = ScreenCaptureController(
        settings=QSettings("PicasaPy", "PicasaPy"), parent=app
    )
    app.aboutToQuit.connect(screen_capture_controller.shutdown)
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty("screenCaptureController", screen_capture_controller)
    engine.rootContext().setContextProperty("cameraCaptureController", camera_capture_controller)
    engine.rootContext().setContextProperty("editController", edit_controller)
    engine.rootContext().setContextProperty("secondPreview", second_preview)
    engine.rootContext().setContextProperty("fileOpsController", fileops_controller)
    engine.rootContext().setContextProperty("confirmSettings", confirm_settings)
    engine.rootContext().setContextProperty("gombsav", gombsav)
    engine.rootContext().setContextProperty("discoveryController", discovery_controller)
    engine.rootContext().setContextProperty("dropImportController", drop_import_controller)
    engine.rootContext().setContextProperty("folderTreeController", folder_tree_controller)
    engine.rootContext().setContextProperty("folderHierarchyController", folder_hierarchy_controller)
    engine.rootContext().setContextProperty("timelineController", timeline_controller)
    engine.rootContext().setContextProperty("backupController", backup_controller)
    engine.rootContext().setContextProperty("dedupController", dedup_controller)
    # #1066 — az „E-Mail" beállításfül és a webexportálás párbeszéde
    engine.rootContext().setContextProperty("emailController", email_controller)
    engine.rootContext().setContextProperty("webExportController", web_export_controller)
    # #1472: a nyomtatás-párbeszéd hídja (`PrintDialog.qml`)
    engine.rootContext().setContextProperty("printController", print_controller)
    # #1401: az Útlevélkép — arcfelismerés + kivágás háttérszálon; a kivágott
    # képet a `Main.qml` a MEGLÉVŐ nyomtatási nézetnek adja
    # (`PrintDialog.openForPassport` → `printController.setPassportSource`).
    PassportPhotoController = _app._lazy_app_symbol("PassportPhotoController")
    passport_controller = PassportPhotoController(photo_source=_lathato_fotok)
    engine.rootContext().setContextProperty("passportController", passport_controller)
    # #368: adatbázis-áthelyezés — a MoveDatabaseDialog.qml hídja
    RelocateController = _app._lazy_app_symbol("RelocateController")
    relocate_controller = RelocateController(data_dir / "index.db", cache_dir / "thumbs", config_dir)
    engine.rootContext().setContextProperty("relocateController", relocate_controller)
    # #449: adatbázis-tömörítés — a CompactDatabaseDialog.qml hídja
    CompactController = _app._lazy_app_symbol("CompactController")
    compact_controller = CompactController(
        data_dir / "index.db", writer_queue=controller._index_iro_sor
    )
    engine.rootContext().setContextProperty("compactController", compact_controller)
    # #3132: a db3-import belépési pontja (`Eszközök ▸ Import a Picasából…`).
    # A mag a #3002/#3184 óta kész; eddig semmi nem hívta a `src/` alól.
    PicasaImportController = _app._lazy_app_symbol("PicasaImportController")
    picasa_import_controller = PicasaImportController(
        index_path=data_dir / "index.db",
        writer_queue=controller._index_iro_sor,
    )
    picasa_import_controller.importFinished.connect(controller._reload_after_sync)
    # #4591: az átvett videódátumok után a rács/mappalista újratöltése
    picasa_import_controller.datesApplied.connect(controller._reload_after_sync)
    engine.rootContext().setContextProperty("picasaImportController", picasa_import_controller)
    # #4597: a Picasában beállított rejtett-jelszó átvétele (csak ha nálunk
    # még nincs) — sorba állított hívás, hogy a fő szálon fusson.
    picasa_import_controller.hiddenPasswordFound.connect(
        controller.adoptHiddenPasswordHash, Qt.ConnectionType.QueuedConnection
    )
    engine.rootContext().setContextProperty("importSourceController", import_source_controller)
    # #147/#4572: a néző arc-keret overlay-jének hídja — a
    # faces=/Contacts2 az ini-ből, a névtelen felismerések az indexből jönnek.
    # A helyi változóban tartás megakadályozza, hogy a Python GC a
    # context property mögül idő előtt eltüntesse a QObject-et.
    FacesHelper = _app._lazy_app_symbol("FacesHelper")
    faces_helper = FacesHelper(data_dir / "index.db")
    engine.rootContext().setContextProperty("facesHelper", faces_helper)
    # #26 (3. lépcső): a SAJÁT arcfelismerés bekötése — a `FaceScanController`
    # (1–2. lépcső) eddig sehol nem volt elérve a QML-ből. A `faces_helper`
    # átadása a tömeges névadáshoz kell (`assignNameToFaces` a MEGLÉVŐ
    # `FacesHelper.addFace()` úton ír, ld. `face_scan_controller.py`).
    FaceScanController = _app._lazy_app_symbol("FaceScanController")
    face_scan_controller = FaceScanController(
        data_dir / "index.db",
        faces_helper=faces_helper,
        # #1403: a KÖZÖS beállítás-tároló — innen jön az „arc elnevezésekor
        # írjuk-e ki az XMP-t" kapcsoló (alapérték BE, ahogy az eredetiben).
        settings=QSettings(),
        face_detection_enabled=controller.faceDetectionEnabledFor,
    )
    # #6067: a regisztrált értékeket induláskor rögzítjük, hogy egy későbbi
    # alapérték-változás ne módosítsa a felhasználó által látott állapotot.
    initialize_option_settings(
        controller._get_settings(),
        import_source_controller=import_source_controller,
        library_controller=controller,
        print_controller=print_controller,
        face_scan_controller=face_scan_controller,
    )
    engine.rootContext().setContextProperty("faceScanController", face_scan_controller)
    face_scan_controller.unnamedCountChanged.connect(
        controller._invalidate_people_manager_contacts_cache
    )
    controller.syncFinished.connect(face_scan_controller.scanNewFaces)
    # Verzió + build a fejlécben (jobb felső sarok): pontosan látsszon,
    # melyik commit fut — ld. version.version_string().
    engine.rootContext().setContextProperty("appVersion", version_string())
    # #6340: kiadásellenőrzés a főablak betöltése után induló 30 mp-es
    # várással; a hálózati hívás a vezérlő saját háttérmunkásán fut.
    from picasapy import __version__
    from .update_manager import UpdateController

    update_controller = UpdateController(
        __version__, settings=controller._get_settings(), schedule=False
    )
    engine.rootContext().setContextProperty("updateController", update_controller)
    # Indítóképernyő (#189): a Main.qml legfelső rétegén ülő SplashScreen
    # ebből a hídból kapja az állapotot, és a finish()-re magától eltűnik.
    engine.rootContext().setContextProperty("startupStatus", startup_status)
    timeline.mark("vezérlők regisztrálása a QML-kontextusban")
    progress_log.mark("QML-kontextus és vezérlők regisztrálva")

    state.screen_capture_controller = screen_capture_controller
    state.passport_controller = passport_controller
    state.compact_controller = compact_controller
    state.picasa_import_controller = picasa_import_controller
    state.faces_helper = faces_helper
    state.face_scan_controller = face_scan_controller
    state.update_controller = update_controller

def _startup_step_load_qml(state):
    engine = state.engine
    progress_log = state.progress_log
    screen_capture_controller = state.screen_capture_controller
    timeline = state.timeline

    progress_log.mark("Main.qml betöltése elkezdődött")
    with timeline.phase("QML betöltése (Main.qml)"):
        engine.load(str(_app._APP_DIR / "qml" / "Main.qml"))
    if not engine.rootObjects():
        progress_log.mark("Main.qml betöltése sikertelen: nem jött létre főablak")
        screen_capture_controller.shutdown()
        return 1
    update_controller = getattr(state, "update_controller", None)
    if update_controller is not None:
        update_controller.start_automatic_check()
    health_file = os.environ.get("PICASAPY_UPDATE_HEALTH_FILE")
    if health_file:
        try:
            Path(health_file).write_text("ready\n", encoding="utf-8")
        except OSError:
            pass
    progress_log.mark("Main.qml betöltve; főablak létrejött")

    return None

def _startup_step_screensaver(argv: list[str]) -> int | None:
    """A képernyővédő belépője a normál bootstrap előtt (#4613)."""
    if _app.KEPERNYOVEDO_KAPCSOLO not in argv:
        return None
    # lustán töltve: a normál indulás importlánca ne hízzon (#1653)
    from . import screensaver_mode

    _kepernyovedo, argv = screensaver_mode.argv_kepernyovedo(argv)
    return screensaver_mode.run_screensaver(argv)
