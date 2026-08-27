"""Közös `qml_app` fixture a szétbontott QML-funkcionális tesztfájlokhoz (#155).

A `tests/app/test_qml_functional.py` (68 teszt, ~20 osztály EGY fájlban,
EGY processzben ~68 QML-engine/ablak-életciklus) volt a Windows-deadlock
(#53) egyik fő forrása. A #155 megoldása: a fájl felbontása több kisebb
fájlra a `tests/app/qml_functional/` alatt, amelyeket a
`scripts/run_tests.py` KÜLÖN-KÜLÖN processzben futtat — így processzenként
lényegesen kevesebb az engine-életciklus, és a Windowson jelentkező
GIL↔Qt-deadlock esélye csökken.

Ez a fixture SZÁNDÉKOSAN eltér a szülő `tests/app/conftest.py`
azonos nevű `qml_app` fixture-étől (más a visszatérési alakja: itt
`(window, controller, engine)`, ott `(window, controller, lib, engine)`).
Az alkönyvtár-conftest felülírja a szülőét — a szétvágott fájlok ezt a
(eredeti test_qml_functional.py-ból változatlanul áthozott) alakot kapják.
A `qt_app` (session-scope) a szülő conftestből öröklődik, azt itt nem kell
újradefiniálni.
"""

import pytest

from picasapy.index import open_index, sync_tree
from picasapy.version import version_string
from support.fixture_guards import qml_warning_guard, user_folder_guard
from support.folder_hierarchy_wiring import wire_folder_hierarchy
from support.print_wiring import wire_print
from support.jpeg_factory import make_jpeg


@pytest.fixture(autouse=True)
def qml_warnings():
    """#305: figyeli a Qt/QML üzenetkezelőt (qInstallMessageHandler), és a
    teszt VÉGÉN — a `qml_app` engine-lebontása UTÁN — hibát dob, ha
    QML-SZKRIPTHIBA jelent meg (pl. „Cannot read property … of null").

    A szűrésről (mire hasal el és mire nem, és miért) ld. a
    `support/qml_warning_filter.py` modul-docstringjét (#309).

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


def _build_qml_app(
    qt_app,
    tmp_path,
    *,
    kepeket_keszit=None,
    belyegkep_meret: int = 32,
    valodi_belyegkep: bool = False,
):
    """Teljes app betöltése és biztonságos lebontása egy gyökérmappában.

    A fixture-wrapper dönti el a teszt- vagy modulszintű életciklust; az
    alkalmazásépítés és a háttérmunkák teardownja közös marad.
    """
    import picasapy.app.application as app_module
    from picasapy.app.controller import AppController
    from picasapy.app.discovery_controller import DiscoveryController
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from picasapy.app.face_scan_controller import FaceScanController
    from picasapy.app.faces_helper import FacesHelper
    from picasapy.app.fileops_controller import FileOpsController
    from picasapy.app.folder_tree_controller import FolderTreeController
    from picasapy.app.import_source_controller import ImportSourceController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.app.timeline_controller import TimelineController
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings
    from picasapy.app.worker_thread import (
        running_background_workers,
        elo_valaszok,
        wait_for_all_background_workers,
    )
    from PySide6.QtQml import QQmlApplicationEngine

    lib = tmp_path / "kepek"
    lib.mkdir()
    # #1596: a hívó saját próbaképeket kérhet — a rács KIRAJZOLT
    # képpontjait mérő tesztnek ellenőrzött (egyenletes) képek kellenek,
    # a piros `make_jpeg`-minta arra alkalmatlan.
    if kepeket_keszit is not None:
        kepeket_keszit(lib)
    else:
        make_jpeg(lib / "a.jpg", size=(320, 160))
        make_jpeg(lib / "b.jpg", size=(100, 100))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, lib)

    # elszigetelt QSettings — a rendszer valós PicasaPy-beállításait ne
    # szennyezze a teszt (session/lastFolder, view/thumbCaption).
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    # #1054: a kollázs KIMENETI mappája is elszigetelt legyen. Enélkül a
    # piszkozat- és mentés-utak a VALÓDI `~/Pictures/Picasa/Kollázsok`-ba
    # írnak: a #985 fülsáv-tesztje például egy `autosave.cxf`-et hagyott ott
    # a fejlesztői gépen, amit később valódi felhasználói munkának néztünk.
    # Csak akkor állítjuk be, ha a teszt maga nem térítette már el (a #1051
    # tesztjei az ini-fájlon át adják meg a saját mappájukat).
    from picasapy.app import collage_prefs

    if not settings.value(collage_prefs.OUTPUT_DIR_KEY):
        settings.setValue(
            collage_prefs.OUTPUT_DIR_KEY, str(tmp_path / "kollazs-kimenet")
        )
    provider = ThumbnailProvider(
        ThumbnailCache(tmp_path / "thumbs", size=belyegkep_meret)
    )
    controller = AppController(db, (str(lib),), provider, settings=settings)
    # #367: az általános ConfirmDialog "Ne kérdezze újra" tára — ugyanaz az
    # elszigetelt settings, mint a controlleré
    from picasapy.app.confirm_settings_bridge import ConfirmSettingsBridge

    confirm_settings = ConfirmSettingsBridge(settings=settings)
    # szerkesztő-híd (#19) — az application.py bekötésének tükre
    edit_preview = EditPreviewProvider()
    edit_controller = EditController(edit_preview)
    # megjelenítési mód (#1575/#1576) — az application.py bekötésének tükre.
    # A név életben tartja az átvezetőt, amíg a motor él.
    _display_mode_bridge = app_module.wire_display_mode(
        controller, edit_controller, edit_preview
    )
    # #1457: az effekt-bélyegkép szolgáltatót itt SZÁNDÉKOSAN nem hozzuk
    # létre. A motor szinkron szolgáltatót kap (ld. lentebb), tehát a
    # valódi, pool-szálas változatra ezekben a tesztekben nincs szükség —
    # és a puszta létrehozása is bejelentkezne a folyamat-szintű
    # pool-nyilvántartásba. Az `application.py` változatlanul a valódit
    # köti be; azt saját, motor nélküli tesztek mérik.
    engine = QQmlApplicationEngine()
    # ⚠️ #1457: a QML-motor SZINKRON szolgáltatót kap. A termékkód
    # aszinkron marad; itt a pool-szálak és a válasz-objektumok csak a
    # #999-es összeomlás-osztályt hoznák be, haszon nélkül — ezek a
    # tesztek a felület bekötését mérik, nem a bélyegkép-készítést.
    # Az aszinkron utat saját, motor nélküli tesztek fedik.
    from support.szinkron_kepszolgaltato import (
        SzinkronKepSzolgaltato,
        SzinkronValodiBelyegkep,
    )

    # #1596: a `valodi_belyegkep` hívók a TERMÉK render-magját kapják (a
    # pool-ugrás nélkül) — enélkül a rács képpontjai a lapos helyettesítő
    # képet mutatnák, és a megjelenítési mód hatása méretlen maradna.
    engine.addImageProvider(
        "thumbs",
        SzinkronValodiBelyegkep(provider)
        if valodi_belyegkep
        else SzinkronKepSzolgaltato(),
    )
    engine.addImageProvider("editpreview", edit_preview)
    engine.addImageProvider("effectthumb", SzinkronKepSzolgaltato())
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty("editController", edit_controller)
    # fájlműveletek (#15) — az application.py bekötésének tükre
    fileops_controller = FileOpsController()
    app_module.wire_fileops(fileops_controller, controller)
    engine.rootContext().setContextProperty(
        "fileOpsController", fileops_controller
    )
    # meglévő Picasa-telepítés átvétele (#146) — az application.py
    # bekötésének tükre
    discovery_controller = DiscoveryController(add_folder=controller.addWatchedFolder)
    engine.rootContext().setContextProperty(
        "discoveryController", discovery_controller
    )
    # Mappakezelő fa-nézete (#231) — az application.py bekötésének tükre
    folder_tree_controller = FolderTreeController()
    engine.rootContext().setContextProperty(
        "folderTreeController", folder_tree_controller
    )
    # #1454: a bal hasáb fa-mappanézete (#702) — az application.py
    # bekötésének tükre. Korábban KIMARADT innen, ezért a `Main.qml`-ben
    # `typeof`-őr védte a hivatkozást, a nézetmód pedig `false`-ra volt
    # égetve — vagyis a fa-nézet egyetlen QML-funkcionális teszten sem
    # jelent meg. A nézetmód-váltó menü (#1454) csak így mérhető.
    # A bekötés a KÖZÖS helyen él, mert a szülő `tests/app/conftest.py`-nak
    # is kell — a féloldalas tükrözés ott már majdnem átcsúszott.
    # a névre kötés életben tartja a vezérlőt, amíg a motor él
    _folder_hierarchy_controller = wire_folder_hierarchy(
        engine, controller, db
    )
    # arc-keretek (#147) — az application.py bekötésének tükre
    faces_helper = FacesHelper()
    engine.rootContext().setContextProperty("facesHelper", faces_helper)
    # #26 (3. lépcső) — az application.py bekötésének tükre
    face_scan_controller = FaceScanController(db, faces_helper=faces_helper)
    engine.rootContext().setContextProperty(
        "faceScanController", face_scan_controller
    )
    # Időrend nézet (#24) — az application.py bekötésének tükre
    timeline_controller = TimelineController(db, provider)
    controller.syncFinished.connect(timeline_controller.reload)
    engine.rootContext().setContextProperty(
        "timelineController", timeline_controller
    )
    # Import forrásból (#23) — az application.py bekötésének tükre
    import_source_controller = ImportSourceController(
        provider, add_folder=controller.addWatchedFolder
    )
    engine.rootContext().setContextProperty(
        "importSourceController", import_source_controller
    )
    # adatbázis-tömörítés (#449) — az application.py bekötésének tükre
    from picasapy.app.compact_controller import CompactController

    compact_controller = CompactController(db)
    engine.rootContext().setContextProperty("compactController", compact_controller)
    # #1472: a nyomtatás vezérlője — az application.py bekötésének tükre.
    # A `Main.qml` `PrintDialog`-ja `typeof`-őr mögül hivatkozik rá, tehát
    # enélkül a nyomtatás felületi útja NÉMÁN méretlen maradna.
    # a névre kötés életben tartja a vezérlőt, amíg a motor él
    _print_controller = wire_print(engine, lambda: controller.photos.photos)
    engine.rootContext().setContextProperty("appVersion", version_string())
    engine.rootContext().setContextProperty("confirmSettings", confirm_settings)
    engine.load(str(app_module._APP_DIR / "qml" / "Main.qml"))
    assert engine.rootObjects(), "Main.qml betöltése sikertelen"
    window = engine.rootObjects()[0]
    controller._reload()
    controller.selectFolder(str(lib))
    qt_app.processEvents()
    yield window, controller, engine
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

    A használó fájl nem írhat tartós állapotot: az állapotot író tesztfájlok
    továbbra is a `qml_app` funkció-scope-ját használják.
    """
    root = tmp_path_factory.mktemp("qml-app-module")
    yield from _build_qml_app(qt_app, root)


#: A #1596 próbaképeinek egyenletes tónusa — a rácson EZT mérjük.
PROBA_HATTER = 200
#: A második próbakép tisztán fehér: a túlcsordulás-jelölésnek kell hova
#: látszania (a `200`-as képen az eredeti szerint NEM jelöl semmit).
PROBA_FEHER = 255


def _proba_kepek(lib) -> None:
    """Két EGYENLETES próbakép a rács képpont-méréséhez (#1596).

    Miért egyenletes, és miért két külön fájl? Mert a bélyegkép útja
    kétszer is átméretez (a gyorstár 256 px-re kicsinyít, majd a QML
    `Image` a cellába), és a JPEG is veszteséges. Egy éles él (pl. fehér
    sáv szürke háttéren) mindkét helyen elmosódna, és a mérés csak tűréssel
    volna kimondható. Két egyenletes képen viszont a teljes lánc BITRE
    pontos — mérve (#1596): mindkét bélyegkép egyetlen színt tartalmaz.
    """
    import cv2
    import numpy as np

    minta = [("a.jpg", PROBA_HATTER), ("b.jpg", PROBA_FEHER)]
    for nev, tonus in minta:
        kep = np.full((160, 320, 3), tonus, dtype=np.uint8)
        assert cv2.imwrite(
            str(lib / nev), kep, [int(cv2.IMWRITE_JPEG_QUALITY), 100]
        ), nev


@pytest.fixture
def qml_app_valodi_belyegkep(qt_app, tmp_path):
    """Teljes app a VALÓDI bélyegkép-szolgáltatóval és próbaképekkel (#1596).

    A `qml_app` helyettesítő szolgáltatót regisztrál (`thumbs` → egyszínű
    kép), ezért azzal a rácsra kirajzolt képpontokról semmit nem lehet
    állítani. Ez a fixture a termék render-magját köti be, és két
    egyenletes tónusú próbaképet tesz a könyvtárba (ld. `_proba_kepek`).
    """
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_proba_kepek,
        # a termék alapértelmezése (`ThumbnailCache` size=256): a rács
        # cellájánál nagyobb, tehát a QML `Image` csak KICSINYÍT — ez a
        # #83 óta a valódi működés
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )
