"""Qt tesztkörnyezet: offscreen platform, egyetlen alkalmazás-példány."""

import os

import pytest

from support.fixture_guards import qml_warning_guard, user_folder_guard
from support.folder_hierarchy_wiring import wire_folder_hierarchy
from support.print_wiring import wire_print

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qt_app():
    """A folyamat egyetlen Qt-alkalmazása.

    #1526: a lebontáskor LE KELL VENNI a vágólapról a Pythonban létrehozott
    `QMimeData`-t, különben a tesztfolyamat **SIGSEGV**-vel áll le — a
    tesztek zölden lefutnak, és a hiba CSAK a kilépőkódban látszik
    (`pytest -q` „11 passed"-et ír, a kilépőkód 139). A `run_tests.py`
    ilyenkor hibás részfutást jelent, a CI pedig pirosat.

    Mérve (2026-08-27, PySide6, offscreen, Qt-n kívüli kód nélkül):

    | mi áll a vágólapon a folyamat leállásakor | kilépőkód |
    |---|---|
    | semmi, vagy `setText()` (a `QMimeData`-t a Qt hozza létre C++-ban) | 0 |
    | Pythonban létrehozott `QMimeData` | **139 (SIGSEGV)** |
    | ugyanaz, de előtte `clear()`/`setText()` | 0 |

    A Python-oldali hivatkozás megtartása vagy eldobása (`del` +
    `gc.collect()`), a `setParent()`, a `shiboken6.invalidate()` és a
    `setUrls()` egyike sem segít; tulajdonjog-átadó hívást ez a `shiboken6`
    nem kínál. Az egyetlen működő fogás: a leállás pillanatában ne a
    Pythonban gyártott `QMimeData` legyen a vágólapon.

    A TERMÉK ugyanezt a `QGuiApplication.aboutToQuit`-on végzi
    (`FileOpsController._release_clipboard`) — az viszont a tesztekben nem
    sül el, mert a tesztfolyamat sosem hívja az `app.quit()`-ot. Ezért kell
    itt is, a fixture lebontásában.

    SZÁNDÉKOSAN itt van, nem az egyes vágólapos tesztfájlokban: így minden
    jövőbeli teszt is védve van, amelyik `QMimeData`-t tesz a vágólapra —
    az a hibaosztály ugyanis némán, a kilépőkódban jelentkezik.
    """
    from PySide6.QtGui import QGuiApplication

    app = QGuiApplication.instance() or QGuiApplication([])
    yield app


@pytest.fixture(autouse=True)
def _vagolap_elengedese():
    """A Pythonban gyártott `QMimeData` levétele a vágólapról — TESZTENKÉNT.

    ⚠️ A lebontás HELYE mérés eredménye, nem ízlés. Először a session-szintű
    `qt_app` fixture végén állt; ott a `clear()` a QML-motorok GLOBÁLIS
    lebontásának pillanatában futott, és a #1260 őre elé sodorta az addig
    csak a stderr-re menő, lebontáskori QML-hibákat („Property 'endEdit' …
    is not a function", „Cannot read property 'length' of undefined").
    Mérve: a CI-n ettől HAT darab bukott el, három KÜLÖNBÖZŐ, a vágólappal
    nem is érintkező tesztfájlon (`test_qml_hidden.py`,
    `test_qml_fileops_export.py`, `test_vagolap_parancsok_1526.py`).

    Tesztenként futtatva a vágólap akkor ürül, amikor még minden él: a
    lebontási zaj a helyén marad, a SIGSEGV pedig ugyanúgy elmarad —
    mutációval igazolva (a törzs kivételével a vágólapos fájl újra 139).
    """
    yield
    from PySide6.QtGui import QGuiApplication

    if QGuiApplication.instance() is None:
        return
    board = QGuiApplication.clipboard()
    if board is not None:
        board.clear()


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
    yield from qml_warning_guard()


@pytest.fixture(scope="module")
def _module_qml_warnings():
    """A modul-fixture teljes setup/teardownja alatt aktív QML-hiba-őr."""
    yield from qml_warning_guard()


@pytest.fixture(scope="module")
def _module_user_folder_guard():
    """A modul-fixture teljes életciklusa alatt aktív mappaszennyezés-őr."""
    yield from user_folder_guard()


def _build_qml_app(qt_app, tmp_path):
    """Teljes app betöltése és biztonságos lebontása egy gyökérmappában.

    A publikus fixture-wrapper dönti el, hogy a gyökér egy teszt vagy egy
    teljes modul élettartamáig él-e; maga az alkalmazásépítés közös, hogy a
    két életciklus ugyanazt a teardown-garanciát használja.
    """
    import picasapy.app.application as app_module
    from picasapy.app.controller import AppController
    from picasapy.app.dedup_controller import DedupController
    from picasapy.app.discovery_controller import DiscoveryController
    from picasapy.app.drop_import_controller import DropImportController
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
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
        elo_valaszok,
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
    # #1457: az effekt-bélyegkép szolgáltatót itt SZÁNDÉKOSAN nem hozzuk
    # létre. A motor szinkron szolgáltatót kap (ld. lentebb), tehát a
    # valódi, pool-szálas változatra ezekben a tesztekben nincs szükség —
    # és a puszta létrehozása is bejelentkezne a folyamat-szintű
    # pool-nyilvántartásba. Az `application.py` változatlanul a valódit
    # köti be; azt saját, motor nélküli tesztek mérik.
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
    # ⚠️ #1457: a QML-motor SZINKRON szolgáltatót kap. A termékkód
    # aszinkron marad; itt a pool-szálak és a válasz-objektumok csak a
    # #999-es összeomlás-osztályt hoznák be, haszon nélkül — ezek a
    # tesztek a felület bekötését mérik, nem a bélyegkép-készítést.
    # Az aszinkron utat saját, motor nélküli tesztek fedik.
    from support.szinkron_kepszolgaltato import SzinkronKepSzolgaltato

    engine.addImageProvider("thumbs", SzinkronKepSzolgaltato())
    engine.addImageProvider("editpreview", edit_preview)
    engine.addImageProvider("effectthumb", SzinkronKepSzolgaltato())
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
    # #1454: a bal hasáb fa-mappanézete (#702) — enélkül a menüsáv
    # `Nézet ▸ Mappanézet` tételei NÉMÁK ebben a fixture-ben, és egy rájuk
    # épülő teszt zölden mérne egy halott menüt
    # a névre kötés életben tartja a vezérlőt, amíg a motor él
    _folder_hierarchy_controller = wire_folder_hierarchy(
        engine, controller, db
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
    # #1472: a nyomtatás vezérlője — az application.py bekötésének tükre.
    # A `Main.qml` `PrintDialog`-ja `typeof`-őr mögül hivatkozik rá, tehát
    # enélkül a nyomtatás felületi útja NÉMÁN méretlen maradna.
    # a névre kötés életben tartja a vezérlőt, amíg a motor él
    _print_controller = wire_print(engine, lambda: controller.photos.photos)
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
    # #438: minden nyilvántartott daemon-szál bevárása, AMÍG a controllerek
    # és a QML-motor még él — a #430 SIGSEGV-osztály elkerülése (ld.
    # picasapy.app.worker_thread.BackgroundWorkerMixin).
    # #988/#999: EGY hívás vár be MINDEN nyilvántartott háttérmunkát — a
    # folyamat összes `_start_background`-szálát és a bejelentkezett
    # `QThreadPool`-okat. Korábban itt egy KÉZZEL FELSOROLT controller-lista
    # állt, és elcsúszott: a fixture által létrehozott `EditController`,
    # `FaceScanController` és a két bélyegkép-szolgáltató pool-ja kimaradt
    # belőle. Ebből lett két, véletlenszerűen pirosló SIGSEGV a CI-ben.
    # ⚠️ #1457: VALÓDI motor mellett a válasz-lánc is le kell hogy fusson.
    # A pool vége NEM a lánc vége: a Qt ezután dolgozza fel a `finished`-et
    # a saját image-reader szálán, hívja a `textureFactory()`-t, majd a
    # `deleteLater()`-t. Ha a lebontás ezt nem várja meg, a lánc félig
    # lebontott világban folytatódik — ez a #999 hibaosztálya.
    # ⚠️ Itt SZÁNDÉKOSAN nincs állítás, csak napló. Az első változat
    # `assert elo_valaszok() == ()`-t írt elő, és a CI megmutatta, miért
    # hibás: ezen a ponton a QML-fa MÉG ÉL (a motort csak lentebb engedjük
    # el), tehát a látszó képekhez tartozó válaszok jogosan léteznek.
    # Mérve: `EffectThumbnailProvider: 57`.
    #
    # A szám viszont ÖNMAGÁBAN lelet: a rács-bélyegképeknél nem marad
    # semmi, az effekt-bélyegképeknél viszont tucatnyi — ez a #1457-en
    # rögzített nyitott kérdés (szivárog-e, vagy csak a fa élettartama).
    maradek = elo_valaszok()
    if maradek:
        print(f"[#1457] élő aszinkron válasz a lebontás előtt: {maradek}")
    assert wait_for_all_background_workers(30.0), (
        "háttérmunka nem állt le a teardownban (#430/#438/#988/#999): "
        + ", ".join(running_background_workers())
    )
    # #1193: csak a háttérmunkák után szabad elengedni a motort. Az
    # EffectThumbnailProvider QRunnable-je a végén Qt `finished` jelzést küld;
    # Windows alatt hozzáférési hibát okoz, ha a válasz QML-tulajdonosa addigra
    # már megsemmisült.
    engine.deleteLater()
    qt_app.processEvents()


@pytest.fixture
def qml_app(qt_app, tmp_path):
    """Teljes app tesztenként, funkció-szintű állapot-izolációval."""
    yield from _build_qml_app(qt_app, tmp_path)


@pytest.fixture(scope="module")
def qml_app_module(
    qt_app,
    tmp_path_factory,
    _module_qml_warnings,
    _module_user_folder_guard,
):
    """Teljes app egyszer a modulhoz, csak állapotmentes QML-őrökhöz.

    A használó fájl nem írhat tartós állapotot: amelyik teszt ini-t,
    beállítást vagy más lemezállapotot módosít, annak a `qml_app` wrapper
    marad a funkció-scope-ban.
    """
    root = tmp_path_factory.mktemp("qml-app-module")
    yield from _build_qml_app(qt_app, root)
