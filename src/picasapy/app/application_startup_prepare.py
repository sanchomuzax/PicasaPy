"""application startup prepare az alkalmazásindítóhoz."""

from __future__ import annotations

import logging
import sqlite3
import sys

import PySide6
from PySide6.QtCore import QCoreApplication, QSettings, Qt, qVersion
from PySide6.QtGui import QGuiApplication, QIcon

from picasapy.index import open_index
from picasapy.scanner import read_exclude_folders
from . import application as _app
from .application_data import (
    _exclude_folders_path,
    _fuggo_koltozes_indulaskor,
    _offer_error_log,
    _onjavito_kollazsmappa,
    _watched_folders_path,
    allitsd_be_a_stilust,
)
from .application_platform import (
    _force_qml_dialogs,
    _install_desktop_entry,
    _install_ui_font,
    _set_windows_app_id,
    _window_icon_path,
)
from .application_services import _install_translator
from .error_log import error_log_path, install_error_log, rotate_if_large
from .platform_check import hianyzo_wayland_bovitmeny
from .platform_storage import StorageAlreadyRunning, StorageMigrationError
from .startup_diagnostics import runtime_version_messages, write_console
from .startup_status import StartupStatus

def _startup_step_log_and_qt_setup(state):
    argv = state.argv
    progress_log = state.progress_log
    timeline = state.timeline

    for message in runtime_version_messages(PySide6.__version__, qVersion() or "ismeretlen"):
        write_console(message, error=True)
        progress_log.mark(message)

    progress_log.mark("Korai indulási hibanapló útvonalának feloldása elkezdődött")
    early_error_log = error_log_path(_app._data_dir())
    rotate_if_large(early_error_log)
    progress_log.install(early_error_log)
    progress_log.mark("Korai indulási hibanapló elérhető")

    # A PicasaPy egyelőre MINDENHOL világos (a sötét téma V3-feature):
    # Fusion stílus + explicit világos paletta; Linuxon/macOS-en a saját,
    # világos QML-dialógusok a rendszer sötét mappaválasztója helyett.
    # Windowson natív dialógus kell — ld. _force_qml_dialogs (#58).
    if _force_qml_dialogs():
        QGuiApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs)
    progress_log.mark("Qt-stílus és platform-kapcsolók beállítása elkezdődött")
    allitsd_be_a_stilust()

    # Windows taskbar-ikon: explicit AppUserModelID-beállítás (#67)
    _set_windows_app_id()

    # #3028: a hiányzó platform-bővítményt a Qt angolul, megoldás nélkül
    # jelenti, és utána KILÉP — ezért itt szólunk, a QGuiApplication ELŐTT.
    # Csak jelzünk: néma átterelés más platformra elrejtené a valódi hiányt.
    figyelmeztetes = hianyzo_wayland_bovitmeny()
    if figyelmeztetes:
        print(figyelmeztetes, file=sys.stderr)

    timeline.mark("Qt-stílus és platform-kapcsolók")
    progress_log.mark("Qt-stílus és platform-kapcsolók beállítva")
    progress_log.mark("Qt-alkalmazás létrehozása elkezdődött")
    app = QGuiApplication(argv)
    app.setApplicationName("PicasaPy")
    app.setOrganizationName("PicasaPy")
    try:
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    except AttributeError:
        pass  # régebbi Qt: a paletta (Main.qml) így is világost kényszerít
    app.setDesktopFileName("picasapy")  # Wayland app_id → tálca-ikon
    app.setWindowIcon(QIcon(str(_window_icon_path())))
    timeline.mark("Qt-alkalmazás létrehozása")
    progress_log.mark("Qt-alkalmazás létrehozva")
    progress_log.mark("Felület-betűtípus betöltése elkezdődött")
    _install_ui_font(app)
    timeline.mark("felület-betűtípus betöltése")
    progress_log.mark("Felület-betűtípus betöltve")
    progress_log.mark("Fordítás betöltése elkezdődött")
    _install_translator(app)
    timeline.mark("fordítás betöltése")
    progress_log.mark("Fordítás betöltve")

    state.early_error_log = early_error_log
    state.app = app

def _startup_step_prepare_storage(state, bootstrap_storage):
    progress_log = state.progress_log
    timeline = state.timeline

    # #3214: az előjegyzett adatbázis-költözés MÉG a tárhely-előkészítés
    # előtt fut le — különben a program a régi helyet nyitná meg, és
    # újraindítást kellene kérni (a mért eredeti sem kér).
    koltozes = _fuggo_koltozes_indulaskor()
    if koltozes.hiba:
        print(koltozes.hiba, file=sys.stderr)
    timeline.mark("előjegyzett adatbázis-költözés")
    progress_log.mark("Előjegyzett adatbázis-költözés ellenőrizve")

    # #1076: Windowson a legacy konfigurációból feloldott EFFEKTÍV
    # adatgyökeret még a migráció előtt zárjuk. A bootstrap az útvonalakat
    # egyszer számolja ki, a régi és új zárat pedig futás végéig őrzi.
    progress_log.mark("Tárhely és példányzár előkészítése elkezdődött")
    try:
        storage_bootstrap = bootstrap_storage()
    except StorageAlreadyRunning:
        progress_log.mark("Tárhely előkészítése megszakadt: már fut egy példány")
        print(
            "A PicasaPy már fut — egyszerre csak egy példány engedélyezett.",
            file=sys.stderr,
        )
        return 0
    except StorageMigrationError as error:
        progress_log.mark("Tárhely előkészítése sikertelen: költözési hiba")
        print(str(error), file=sys.stderr)
        return 1
    timeline.mark("tárhely előkészítése (zár + migráció)")
    progress_log.mark("Tárhely előkészítve")

    # Indítóképernyő-híd (#189): korán jön létre, hogy az első állapot-
    # üzenetek is látsszanak; helyi változóban tartva (GC ellen).
    # #243: amíg az eredeti Picasa effekt-készlete nem teljes (#20, #190),
    # a splash a betöltés végén „félkész szoftver" figyelmeztetést és OK
    # gombot mutat — az effekt-paritás elérésekor ezt False-ra kell állítani.
    startup_status = StartupStatus(
        QCoreApplication.translate("startup", "Starting…"),
        requires_confirmation=True,
    )
    progress_log.mark("Splash állapotobjektum létrehozva")

    state.koltozes = koltozes
    state.storage_bootstrap = storage_bootstrap
    state.startup_status = startup_status

    return None

def _startup_step_prepare_index_and_main_controller(state):
    app = state.app
    launch_arguments = state.launch_arguments
    progress_log = state.progress_log
    roots = state.roots
    startup_status = state.startup_status
    storage_bootstrap = state.storage_bootstrap
    timeline = state.timeline

    data_dir = storage_bootstrap.data_dir
    cache_dir = storage_bootstrap.cache_dir
    config_dir = storage_bootstrap.config_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    # #449: hibanapló — a WARNING és súlyosabb üzenetek fájlba is mennek,
    # hogy adatbázis-hiba esetén legyen mit felajánlani megtekintésre
    error_log = install_error_log(data_dir) or error_log_path(data_dir)
    progress_log.install(error_log)
    timeline.mark("hibanapló előkészítése")
    progress_log.mark("Hibanapló elérhető")

    _install_desktop_entry()
    timeline.mark("asztali bejegyzés telepítése")
    progress_log.mark("Asztali bejegyzés ellenőrizve")

    # Ottragadt gyökerek takarítása (#58): az indexben csak a most figyelt
    # mappák maradhatnak — a korábbi futások (pl. régi parancssori argumentum)
    # mappái különben örökre a bal hasábban ragadnának.
    startup_status.report(QCoreApplication.translate("startup", "Preparing index…"))
    progress_log.mark("Index megnyitása elkezdődött")
    try:
        with open_index(data_dir / "index.db") as conn:
            # #1601: a `mark` az ELŐZŐ bejelentés óta eltelt időt zárja le —
            # itt tehát pontosan a fenti `open_index` (séma + migráció)
            # költségét, anélkül hogy a `with`-et szét kellene szedni.
            timeline.mark("index megnyitása (séma + migráció)")
            # #1716: az ottragadt mappák takarítása (#58) NEM itt fut többé —
            # a védett gyökerek (figyelt mappák + nyilvántartott exportcélok)
            # száma × a hálózati `stat` ára miatt ez volt a legnagyobb tétel,
            # ami még a kritikus úton maradt (mérve 2 293,9 ms). A takarítás
            # az első képkocka UTÁN fut (`_start_and_finish` →
            # `_ottragadt_mappak_takaritasa`), a `_exportcelok_visszavetele`
            # (#1667) mintájára — ld. ott a versenyhelyzet indoklását.
            with timeline.phase("Kollázsok mappa önjavítása (#1075)"):
                _onjavito_kollazsmappa(conn, QSettings())
        progress_log.mark("Index megnyitása és előkészítése befejeződött")
    except sqlite3.DatabaseError:
        progress_log.mark("Index megnyitása adatbázishibával tért vissza")
        # #449: az eredeti sem omlott össze némán és nem javított titokban —
        # FELAJÁNLOTTA a hibanaplót („There were errors loading the Picasa
        # database. Would you like to view the error log?"). A program ezután
        # elindul: az index önmagát újraépíti a következő beolvasáskor.
        logging.getLogger(__name__).exception("az index megnyitása hibára futott")
        _offer_error_log(error_log)

    # #83: a cache-méretet a képernyő DPR-jéhez igazítjuk, hogy a rács
    # legnagyobb fokozata (256px) se legyen homályos HiDPI kijelzőn.
    startup_status.report(QCoreApplication.translate("startup", "Loading photo library…"))
    timeline.mark("index előkészítése — utómunka")
    progress_log.mark("Index utómunkája elkezdődött")
    thumb_cache = _app._create_thumbnail_cache(app, cache_dir)
    provider = _app._lazy_app_symbol("ThumbnailProvider")(
        thumb_cache, index_path=data_dir / "index.db"
    )
    AppController = _app._lazy_app_symbol("AppController")
    controller = AppController(
        data_dir / "index.db",
        roots,
        provider,
        watched_file=_watched_folders_path(),
        exclude_file=_exclude_folders_path(),
        face_excluded=read_exclude_folders(_exclude_folders_path()),
    )
    quick_view_started = bool(launch_arguments.photo_paths) and controller.begin_quick_view(
        list(launch_arguments.photo_paths)
    )
    controller.syncFinished.connect(
        lambda: progress_log.mark("Az induláskori könyvtárszinkron befejeződött")
    )
    timeline.mark("bélyegkép-gyorstár és fővezérlő létrehozása")

    state.data_dir = data_dir
    state.cache_dir = cache_dir
    state.config_dir = config_dir
    state.error_log = error_log
    state.thumb_cache = thumb_cache
    state.provider = provider
    state.controller = controller
    state.quick_view_started = quick_view_started
