"""Alkalmazás-bootstrap: Qt, fordítások, adat-útvonalak, QML-betöltés.

Könyvtár-gyökerek: parancssori argumentumok, vagy a Picasa-paritású
~/.config/picasapy/WatchedFolders.txt (soronként egy abszolút útvonal).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import ctypes as ctypes
import importlib
import logging
import math as math
import os as os
import sqlite3 as sqlite3
import sys as sys
import threading
import time
from collections.abc import Callable as Callable, Mapping as Mapping
from pathlib import Path
from types import FunctionType as _FunctionType
from types import SimpleNamespace as _SimpleNamespace

import shutil
import subprocess

import PySide6 as PySide6
from PySide6.QtCore import (
    QCoreApplication,
    QEventLoop as QEventLoop,
    QLocale as QLocale,
    QLibraryInfo as QLibraryInfo,
    QLockFile as QLockFile,
    QObject,
    QSettings,
    Qt,
    QTimer,
    QTranslator as QTranslator,
    qVersion as qVersion,
)
from PySide6.QtGui import QFontDatabase as QFontDatabase, QGuiApplication as QGuiApplication, QIcon as QIcon
from PySide6.QtQml import QQmlApplicationEngine as QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle as QQuickStyle

from picasapy.index import open_index, prune_foreign_folders
from picasapy.index.sync import sync_folder as sync_folder
from picasapy.perf import default_log_dir as default_log_dir, start_startup_timeline as start_startup_timeline
from picasapy.perf.logwriter import session_header as session_header
from picasapy.perf.tesztuzem import (
    argv_kapcsolo_nelkul as argv_kapcsolo_nelkul,
    argv_tesztuzem as argv_tesztuzem,
    irj_indulasi_naplot as irj_indulasi_naplot,
    konyvtar_merete as konyvtar_merete,
    naplo_szovege as naplo_szovege,
    tarolo_tipusa as tarolo_tipusa,
    tesztuzem_bekapcsolva as tesztuzem_bekapcsolva,
)
from picasapy.render.text_fonts import clear_family_cache as clear_family_cache
from picasapy.scanner import (
    EXCLUDE_FOLDERS_NAME as EXCLUDE_FOLDERS_NAME,
    WATCHED_FOLDERS_NAME as WATCHED_FOLDERS_NAME,
    find_exclude_folders_file as find_exclude_folders_file,
    find_watched_folders_file as find_watched_folders_file,
    read_exclude_folders as read_exclude_folders,
    read_watched_folders as read_watched_folders,
)
from picasapy.thumbs import ThumbnailCache
from picasapy.version import version_string as version_string
from .color_palette import ColorPaletteProvider as ColorPaletteProvider
from .folder_cover_provider import FolderCoverProvider, borito_belyegkepe
from .data_location import read_data_root as read_data_root, read_pending_root as read_pending_root
from . import display_photo_provider as display_photo_provider
from .error_log import error_log_path as error_log_path, install_error_log as install_error_log, rotate_if_large as rotate_if_large
from .exported_folders import (
    EXPORTED_FOLDERS_SETTINGS_KEY as EXPORTED_FOLDERS_SETTINGS_KEY,
    existing_exported_folders as existing_exported_folders,
    registered_exported_folders as registered_exported_folders,
)
from .startup_relocate import (
    IndulasiKoltozo as IndulasiKoltozo,
    KoltozesEredmeny as KoltozesEredmeny,
    KoltozesHid as KoltozesHid,
)
from .filetype_preferences import enabled_filetypes as enabled_filetypes
from .option_settings import (
    initialize_option_settings as initialize_option_settings,
)
from .i18n_build import forditsd as forditsd
from .language_controller import (
    DEFAULT_LANGUAGE as DEFAULT_LANGUAGE,
    LANGUAGE_KEY as LANGUAGE_KEY,
    coerce_language as coerce_language,
    resolve_first_run_language as resolve_first_run_language,
    resolve_startup_language as resolve_startup_language,
)
from .startup_language_prompt import (
    ask_startup_language_prompt as ask_startup_language_prompt,
)
from .platform_check import hianyzo_wayland_bovitmeny as hianyzo_wayland_bovitmeny
from .platform_storage import (
    MigrationNotice as MigrationNotice,
    StorageAlreadyRunning as StorageAlreadyRunning,
    StorageBootstrap as StorageBootstrap,
    StorageMigrationError as StorageMigrationError,
    StoragePaths as StoragePaths,
    bootstrap_storage as bootstrap_storage,
    default_storage_paths as default_storage_paths,
)
from .startup_status import StartupStatus as StartupStatus
from .startup_maintenance import StartupMaintenance as StartupMaintenance, StartupMaintenanceStep
from .startup_diagnostics import (
    StartupProgressLog,
    runtime_version_messages as runtime_version_messages,
    write_console,
)
from .window_geometry import virtual_desktop_rect, wire_window_geometry
from ._application_constants import _SPLASH_MIN_VISIBLE_MS as _SPLASH_MIN_VISIBLE_MS

load_enabled_filetypes = enabled_filetypes
del enabled_filetypes
_ask_first_run_language = ask_startup_language_prompt
del ask_startup_language_prompt


_LAZY_APP_SYMBOLS = {
    "AppController": ".controller",
    "BackupController": ".backup_controller",
    "CameraCaptureController": ".camera_capture_controller",
    "CompactController": ".compact_controller",
    "ConfirmSettingsBridge": ".confirm_settings_bridge",
    "DedupController": ".dedup_controller",
    "DiscoveryController": ".discovery_controller",
    "DropImportController": ".drop_import_controller",
    "EditController": ".edit_controller",
    "EditPreviewProvider": ".edit_preview",
    "EffectThumbnailProvider": ".effect_thumbnails",
    "EmailController": ".email_controller",
    "FaceScanController": ".face_scan_controller",
    "FacesHelper": ".faces_helper",
    "FileOpsController": ".fileops_controller",
    "FolderHierarchyController": ".folder_hierarchy_controller",
    "FolderTreeController": ".folder_tree_controller",
    "GombsavBridge": ".gombsav_bridge",
    "ImportSourceController": ".import_source_controller",
    "PassportPhotoController": ".passport_controller",
    "PicasaImportController": ".picasa_import_controller",
    "PrintController": ".print_controller",
    "RelocateController": ".relocate_controller",
    "SecondPreview": ".second_preview",
    "ScreenCaptureController": ".screen_capture",
    "ThumbnailProvider": ".thumbnail_provider",
    "TimelineController": ".timeline_controller",
    "WebExportController": ".webexport_controller",
    "sorted_folder_rows": ".models",
    "wire_color_management": ".color_management_controller",
    "wire_display_mode": ".display_mode_controller",
}
_LAZY_APP_MODULES = {
    "collage_output": ".collage_output",
    "collage_prefs": ".collage_prefs",
}


def _lazy_app_symbol(name: str):
    """Az alkalmazásritkán használt hídjait csak kéréskor importálja (#4913).

    A globális névteret ellenőrizzük először, így a régi teszt-fogantyúk
    (`monkeypatch.setattr(application, ...)`) továbbra is működnek.
    """
    if name in globals():
        return globals()[name]
    if name in _LAZY_APP_MODULES:
        module = importlib.import_module(_LAZY_APP_MODULES[name], __package__)
        globals()[name] = module
        return module
    try:
        module = importlib.import_module(_LAZY_APP_SYMBOLS[name], __package__)
        value = getattr(module, name)
    except ImportError:
        if name != "PrintController":
            raise
        # A print_controller a QtPrintSupport-ot igényli, ami nem minden
        # rendszer-Qt csomag része (#1472). A hiányt a QML jelzi a használatkor.
        value = None
    globals()[name] = value
    return value


_APPLICATION_HELPER_MODULES = (
    "application_data",
    "application_platform",
    "application_services",
    "application_startup_prepare",
    "application_startup_controllers",
    "application_startup_qml",
)
_APPLICATION_HELPERS_LOADED = False


def _ensure_application_helpers() -> None:
    """A külön modulok függvényeit a régi modulnévtérbe exportálja.

    Az eredeti függvényobjektum marad a segédmodul globális szótárával;
    az `application`-beli alias őrzi a régi importútvonalat.
    """
    global _APPLICATION_HELPERS_LOADED
    if _APPLICATION_HELPERS_LOADED:
        return
    for helper_name in _APPLICATION_HELPER_MODULES:
        helper = importlib.import_module(f".{helper_name}", __package__)
        for name, value in vars(helper).items():
            if not isinstance(value, _FunctionType) or value.__module__ != helper.__name__:
                continue
            value.__module__ = __name__
            globals()[name] = value
    _APPLICATION_HELPERS_LOADED = True


def __getattr__(name: str):
    if name in _LAZY_APP_SYMBOLS or name in _LAZY_APP_MODULES:
        return _lazy_app_symbol(name)
    _ensure_application_helpers()
    try:
        return globals()[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None


def __dir__():
    _ensure_application_helpers()
    return sorted(globals())

#: A `shutil.which` és a `subprocess.run` MODULSZINTŰ fogantyúja (#1375) —
#: a teszt EZEKET cserélje.
#:
#: A `monkeypatch.setattr(application.shutil, "which", …)` alak a GLOBÁLIS
#: `shutil`-t írja át, tehát minden más modul `which`-hívására is hat, amíg
#: a teszt fut.
_which = shutil.which
_run = subprocess.run

_APP_DIR = Path(__file__).parent
_I18N_DIR = _APP_DIR / "i18n"

# A rács legnagyobb megjelenítési mérete logikai pixelben — a Main.qml
# sizeSlider.to értékével azonos (#83). Ha az ottani felső határ változik,
# ezt is frissíteni kell, különben a legnagyobb rács-fokozat újra
# nagyítással (homályosan) jelenhet meg.
_GRID_MAX_THUMB_PX = 256

# #144: a thumbnail-lemezcache méretkorlátja — induláskor háttérszálon
# lefutó LRU-takarító tartja be, hogy a ~/.cache alatti tár ne nőjön
# korlátlanul (minden fájlváltozás új hash-bejegyzést szül).
_THUMB_CACHE_LIMIT_BYTES = 512 * 1024 * 1024


class _StartupSmokeProbe(QObject):
    """A teljes indulási út után ellenőrzi a főablak és a splash állapotát."""

    def __init__(self, app, window, startup_status, controller, progress_log) -> None:
        super().__init__(app)
        self._app = app
        self._window = window
        self._startup_status = startup_status
        self._progress_log = progress_log
        self._sync_finished = threading.Event()
        self._deadline = time.monotonic() + 25.0
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._check)
        controller.syncFinished.connect(self._sync_finished.set)
        startup_status.readyChanged.connect(self._check)
        self._timer.start()

    def _check(self) -> None:
        splash = self._window.findChild(QObject, "splashScreen")
        if self._startup_status.ready and splash is not None:
            # A valódi indítás megerősítő üzenetet mutat. A füstpróba az OK
            # műveletet végzi el, majd megvárja a QML átmenet végét.
            if bool(splash.property("confirmationRequired")) and not bool(
                splash.property("confirmed")
            ):
                splash.setProperty("confirmed", True)
            if (
                self._sync_finished.is_set()
                and self._window.isVisible()
                and not splash.isVisible()
            ):
                self._timer.stop()
                self._progress_log.mark("A főablak a splash után megjelent")
                write_console("startup-smoke passed: main window shown after splash")
                self._app.exit(0)
                return
        if time.monotonic() >= self._deadline:
            self._timer.stop()
            message = (
                "startup-smoke failed: the main window did not appear after "
                "the splash within 25 seconds"
            )
            self._progress_log.mark(message)
            write_console(message, error=True)
            self._app.exit(1)



if TYPE_CHECKING:
    from .application_data import (
        _bootstrap_storage,
        _exportcelok_visszavetele,
        _resolve_roots,
        _screen_device_pixel_ratio,
        _takaritas_gyokerei,
        _thumbnail_cache_size,
    )
    from .application_platform import _remaining_splash_ms, _start_initial_scan
    from .application_services import (
        _indexelt_kepszamok,
        _indulasi_idovonal,
        _jelentsd_az_idovonalat,
        argv_indulasellenorzes,
        argv_onellenorzes,
    )
    from .application_startup_controllers import (
        _startup_step_create_edit_and_file_controllers,
        _startup_step_create_library_controllers,
    )
    from .application_startup_prepare import (
        _startup_step_log_and_qt_setup,
        _startup_step_prepare_index_and_main_controller,
        _startup_step_prepare_storage,
    )
    from .application_startup_qml import (
        _startup_step_create_qml_engine,
        _startup_step_load_qml,
        _startup_step_register_qml_context,
        _startup_step_screensaver,
    )

# a `screensaver_idle.SCREENSAVER_FLAG` másolata — az import nélkül olvasható
# (#1653); az egyezést a #4613 tesztje őrzi
KEPERNYOVEDO_KAPCSOLO = "--screensaver"

#: #526: a felület betűtípusa. Az eredeti Picasa a **Praxis** (Linotype)
#: családot használta — kereskedelmi, nem szállítható. A helyettesítőt a jegy
#: előírása szerint MÉRÉSSEL választottuk, nem ránézésre: a tulajdonos két
#: Picasa-képernyőképéről (a „Gyakori javítások" és a „Finomhangolás" fül)
#: leolvasott TÍZ magyar felirat képpont-szélességét vetettük össze az öt
#: jelölt ugyanazon szövegeivel, közös legkisebb-négyzetes skálázás mellett:
#:
#:     Open Sans ......... 0,92 %   (legrosszabb szó: 2,92 %)
#:     Source Sans 3 ..... 1,15 %   (4,33 %)
#:     Fira Sans ......... 1,29 %   (3,43 %)
#:     Roboto Condensed .. 2,05 %   (4,38 %)
#:     Archivo Narrow .... 2,52 %   (8,97 %)
#:
#: A mérés a betűtípus SAJÁT arányait fogja meg (szóhosszak egymáshoz mért
#: viszonyát), ezért a képernyőkép nagyítása/DPI-je nem befolyásolja. A
#: keskenyített jelöltek egyértelműen rosszabbak — a panel-feliratok tehát
#: NEM keskenyítettek, összhangban azzal, hogy a Praxis sem az.
#:
#: A betűtípus SIL Open Font License 1.1 alatt áll (`assets/fonts/OFL.txt`).
_UI_FONT_FILES = ("OpenSans-Regular.ttf", "OpenSans-Bold.ttf")
_UI_FONT_FAMILY = "Open Sans"

# #240: a splash minimális megjelenítési ideje — az első képkockától
# számítva legalább ennyi ideig látszik, gyors betöltésnél is.
_ONELLENORZES_KAPCSOLO = "--onellenorzes"
_INDULAS_ELLENORZES_KAPCSOLO = "--indulasellenorzes"

def _ottragadt_mappak_takaritasa(
    index_db: Path, roots: tuple[str, ...], settings: QSettings
) -> None:
    """A #58 takarítás SAJÁT kapcsolaton, az első képkocka UTÁN (#1716).

    Eddig ez a lépés a kritikus úton futott: a védett gyökerek (figyelt
    mappák + nyilvántartott exportcélok) száma × a hálózati `stat` ára —
    a tulajdonos gépén MÉRVE 2 293,9 ms (a #1706 modellje szerint 10
    gyökér × ~4 `lstat`, NAS-on ~47 ms/hívás). A feloldás ára ELKERÜL-
    HETETLEN (#1706/#1667 óta a nyilvántartott exportcélokat létezés-
    ellenőrzés nélkül kell védeni), tehát nem OLCSÓBB lett, hanem ODÉBB
    került — pontosan a `_exportcelok_visszavetele` (#1667) mintája.

    A törlés (`folders`/`photos`/`folder_scan_state`) nem sürgős: ottragadt
    (a figyelt gyökereken kívülre került) mappákat takarít, ami a felület
    megjelenése UTÁN ugyanúgy elvégezhető.

    ## Versenyhelyzet a háttér-szinkronnal (#1716/#4687)

    ⚠️ Ez a lépés a `_start_initial_scan` (tehát a `controller.start()` →
    `rescan()`) ELŐTT fut, a soros `StartupMaintenance` munkacsoportban.
    A `rescan()` saját SQLite-kapcsolattal futó HÁTTÉRSZÁLAT indít
    (`_sync_worker`, ld. `library_controller.py`), ami ugyanazokat a
    táblákat írja. A takarítás tranzakciója a munkafüggvény visszatérésekor
    már commitolt; a sor csak ezután lép tovább a mappafa- és exportcél-
    frissítésre, majd a `batchFinished` jelzés indítja a könyvtárszinkront.
    Így a két író nem fut egyszerre, a fő szál pedig közben eseményeket
    dolgoz fel. Az elhelyezés-őr (`tests/perf/test_takaritas_utrol_1716.py`)
    ezt a sorrendet fagyasztja be.

    A bal hasáb mappafája a takarítás után, ugyanebben a soros munkacsoportban
    töltődik fel, így nem mutat ottragadt mappát a következő szinkronig.

    A hiba nyelt (a takarítás soha nem hiúsulhat meg tőle), de naplózva."""
    _ensure_application_helpers()
    try:
        with open_index(index_db) as conn:
            prune_foreign_folders(conn, _takaritas_gyokerei(roots, settings))
    except Exception:  # noqa: BLE001 - a felület már áll, ez csak karbantartás
        logging.getLogger(__name__).warning(
            "az ottragadt mappák takarítása hibára futott", exc_info=True
        )


def _create_thumbnail_cache(app, cache_dir):
    _ensure_application_helpers()
    cache_size = _thumbnail_cache_size(_screen_device_pixel_ratio(app))
    thumb_cache = ThumbnailCache(
        cache_dir / "thumbs",
        size=cache_size,
        max_bytes=_THUMB_CACHE_LIMIT_BYTES,
    )
    return thumb_cache


def _create_print_controller(photo_source, tray_source):
    PrintController = _lazy_app_symbol("PrintController")
    return (
        PrintController(photo_source=photo_source, tray_source=tray_source)
        if PrintController is not None
        else None
    )


def _create_folder_cover_provider(data_dir, thumb_cache):
    return FolderCoverProvider(
        lambda mappa: borito_belyegkepe(data_dir / "index.db", mappa, thumb_cache)
    )


def _startup_step_smoke_test(state) -> None:
    print("onellenorzes: a felulet felepult", flush=True)
    state.screen_capture_controller.shutdown()
    state.controller.shutdown()
    state.edit_controller.cancelPendingPreview()
    state.edit_controller.waitForBackgroundWorkers(2.0)


def run(argv: list[str], *, entry_at: float | None = None) -> int:
    """Az alkalmazás indítása.

    #1601: az entry_at a belépési pont (__main__.py) legelső saját
    sorában olvasott time.monotonic() — ebből látszik, mennyit visz el
    maga a Python- és PySide6-import, mielőtt idáig eljutnánk. None
    esetén ez a szakasz kimarad a jelentésből; mérni nem kötelező.

    Az idővonal alapból KI van kapcsolva; a tartós tesztüzem beállítás
    (#1654), a --tesztuzem kapcsoló és a PICASAPY_STARTUP_TIMELINE=1
    környezeti változó (#1601) kapcsolja be — ld. _indulasi_idovonal.
    """
    _ensure_application_helpers()
    screensaver_exit = _startup_step_screensaver(argv)
    if screensaver_exit is not None:
        return screensaver_exit

    progress_log = StartupProgressLog()
    progress_log.mark("Python- és PySide6-modulok betöltése befejeződött")
    onellenorzes, argv = argv_onellenorzes(argv)
    startup_smoke, argv = argv_indulasellenorzes(argv)
    progress_log.mark("Indulási argumentumok beolvasva")
    timeline, argv = _indulasi_idovonal(argv, entry_at=entry_at)
    # #5762: a fájlok közvetlenül a viewer listájába kerülnek; a könyvtárak
    # maradnak a könyvtárnézet gyökerei. A fájlnevek Qt-argumentumként sem
    # szükségesek, az alkalmazás a saját listájából olvassa őket.
    from .quick_view import parse_launch_arguments

    launch_arguments = parse_launch_arguments(argv)
    library_argv = [argv[0] if argv else "picasapy", *launch_arguments.directory_roots]
    state = _SimpleNamespace(
        argv=argv,
        progress_log=progress_log,
        timeline=timeline,
        onellenorzes=onellenorzes,
        startup_smoke=startup_smoke,
        launch_arguments=launch_arguments,
        library_argv=library_argv,
    )

    _startup_step_log_and_qt_setup(state)
    # A hívást késleltetjük: a lépés előbb ellenőrzi a #3214 költözést,
    # aztán a #1076 tárhely-bootstrapot, mindkettőt a gyökerek feloldása előtt.
    storage_exit = _startup_step_prepare_storage(
        state, bootstrap_storage=lambda: _bootstrap_storage()
    )
    if storage_exit is not None:
        return storage_exit

    progress_log.mark("Figyelt könyvtárak beolvasása elkezdődött")
    with timeline.phase("figyelt gyökerek beolvasása (WatchedFolders.txt)"):
        roots = _resolve_roots(library_argv)
    progress_log.mark("Figyelt könyvtárak beolvasva")
    state.roots = roots

    _startup_step_prepare_index_and_main_controller(state)
    _startup_step_create_edit_and_file_controllers(state)
    _startup_step_create_library_controllers(state)
    _startup_step_create_qml_engine(state)
    _startup_step_register_qml_context(state)
    load_exit = _startup_step_load_qml(state)
    if load_exit is not None:
        return load_exit

    #: #3021: a csomagolás füstpróbája. Idáig eljutni azt jelenti, hogy a
    #: Qt-bővítmények, a QML-fa, a fordítás és az ikon MIND a csomagban van
    #: — a felület felépült. Az ablakot már nem mutatjuk meg, és az
    #: eseményciklus el sem indul.
    #:
    #: A LEZÁRÁS nem hagyható ki. A vezérlő ekkor már él, és háttérszálai
    #: vannak; nélkülük a processz nem lép ki, csak áll — a windowsos
    #: CI-futáson MÉRVE 38 percig, amíg a job időkorlátja levágta. A
    #: füstpróba pontosan azt nem mutatta volna meg, amiért van.
    if onellenorzes:
        _startup_step_smoke_test(state)
        return 0

    # #240: a betöltés csak az ablak ELSŐ kirajzolt képkockája UTÁN indul —
    # Windowson a korábbi singleShot(0) még az első frame előtt lefutott, a
    # finish() a splash-t láthatatlanul kifakította. A splash emellett
    # legalább _SPLASH_MIN_VISIBLE_MS-ig látszik (gyors betöltésnél is van
    # ideje megjelenni, a Picasa-élményhez hasonlóan).
    window = state.engine.rootObjects()[0]

    # #192: az utolsó ablakpozíció/-méret visszaállítása induláskor,
    # mentése az ablak zárásakor — a controllerrel közös QSettings-tárba
    wire_window_geometry(
        window, QSettings("PicasaPy", "PicasaPy"), virtual_desktop_rect(state.app)
    )
    smoke_probe = (
        _StartupSmokeProbe(
            state.app, window, state.startup_status, state.controller, progress_log
        )
        if startup_smoke
        else None
    )
    splash_state = {"started": False}
    startup_state = {"first_frame_at": None}

    def _start_and_finish() -> None:
        startup_state["first_frame_at"] = time.monotonic()
        if state.quick_view_started:
            # Ne kérdezzük le a mentett könyvtárat és ne indítsuk el a
            # könyvtárszkennelést: a gyorsnézegető induló képsora csak a
            # parancssorban kapott fájlokat tartalmazza.
            state.startup_status.finish()
            timeline.mark("közvetlen gyorsnézegető-indítás")
            progress_log.mark("A gyorsnézegető megnyílt a megadott képekkel")
            return
        # #4687: a három induláskori karbantartás külön háttérszálon, de
        # egymás után fut. Így a lassú hálózati stat nem fogja a Qt főszálat,
        # a takarítás mégis a könyvtárszinkron ELŐTT commitol.
        state.startup_maintenance.enqueue(
            "initial",
            (
                StartupMaintenanceStep(
                    key="orphan_cleanup",
                    name="Mappák ellenőrzése",
                    status_text=QCoreApplication.translate(
                        "startup", "Checking folders…"
                    ),
                    work=lambda: _ottragadt_mappak_takaritasa(
                        state.data_dir / "index.db", roots, QSettings()
                    ),
                ),
                StartupMaintenanceStep(
                    key="folder_hierarchy",
                    name="A mappafa frissítése",
                    status_text=QCoreApplication.translate(
                        "startup", "Refreshing folder list…"
                    ),
                    work=state._mappafa_sorai,
                ),
                StartupMaintenanceStep(
                    key="exported_folders",
                    name="Exportmappák ellenőrzése",
                    status_text=QCoreApplication.translate(
                        "startup", "Checking export folders…"
                    ),
                    work=lambda: _exportcelok_visszavetele(
                        state.data_dir / "index.db", QSettings()
                    ),
                ),
            ),
        )

    def _maintenance_batch_finished(batch_key: str) -> None:
        if batch_key != "initial":
            return
        progress_log.mark("Induláskori könyvtárszinkron indítása")
        with timeline.phase("könyvtár betöltése (a vezérlő indítása)"):
            _start_initial_scan(
                state.startup_status,
                state.controller,
                state.storage_bootstrap.migration_notice,
            )
        elapsed_ms = (
            time.monotonic() - startup_state["first_frame_at"]
        ) * 1000
        _jelentsd_az_idovonalat(
            timeline,
            lambda: _indexelt_kepszamok(state.data_dir),
            lambda: _takaritas_gyokerei(roots, QSettings()),
        )

        def _finish_splash() -> None:
            progress_log.mark("A splash lezárása elkezdődött")
            state.startup_status.finish()
            progress_log.mark("A splash állapota készre váltott")

        QTimer.singleShot(_remaining_splash_ms(elapsed_ms), _finish_splash)

    state.startup_maintenance.batchFinished.connect(
        _maintenance_batch_finished, Qt.ConnectionType.QueuedConnection
    )

    def _on_first_frame() -> None:
        # a frameSwapped minden képkockánál jön — csak az első számít
        if splash_state["started"]:
            return
        splash_state["started"] = True
        timeline.mark("az ablak első kirajzolt képkockája")
        progress_log.mark("Első főablak-képkocka; a rács megjelent")
        QTimer.singleShot(0, _start_and_finish)

    app = state.app
    controller = state.controller
    edit_controller = state.edit_controller
    screen_capture_controller = state.screen_capture_controller
    startup_maintenance = state.startup_maintenance
    window.frameSwapped.connect(_on_first_frame)
    # tartalék: ha a frameSwapped nem jönne (pl. offscreen platform), az
    # indulás legkésőbb 1 s után akkor is elkezdődik
    QTimer.singleShot(1000, _on_first_frame)
    exit_code = app.exec()
    if smoke_probe is not None:
        smoke_probe._timer.stop()
    startup_maintenance.cancel()
    startup_maintenance.waitForBackgroundWorkers(2.0)
    screen_capture_controller.shutdown()
    controller.shutdown()
    # #547: a szerkesztő háttér-renderét külön kell lezárni — az
    # edit_controller önálló objektum, nem része a controller.shutdown()
    # láncának. Előbb ÉRVÉNYTELENÍTÜNK (a worker így a végén sem emitál egy
    # közben megsemmisülő QObject-nek, ld. #430), utána rövid ideig várunk:
    # a perces rendert nem kell végigvárni, a daemon-szál emit nélkül fut ki.
    edit_controller.cancelPendingPreview()
    edit_controller.waitForBackgroundWorkers(2.0)
    return exit_code
