"""Alkalmazás-bootstrap: Qt, fordítások, adat-útvonalak, QML-betöltés.

Könyvtár-gyökerek: parancssori argumentumok, vagy a Picasa-paritású
~/.config/picasapy/WatchedFolders.txt (soronként egy abszolút útvonal).
"""

from __future__ import annotations

import ctypes
import logging
import math
import os
import sqlite3
import sys
import time
from collections.abc import Callable, Mapping
from pathlib import Path

import shutil
import subprocess

from PySide6.QtCore import (
    QCoreApplication,
    QLockFile,
    QSettings,
    Qt,
    QTimer,
    QTranslator,
)
from PySide6.QtGui import QFontDatabase, QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from picasapy.index import open_index, prune_foreign_folders
from picasapy.index.sync import sync_folder
from picasapy.perf import default_log_dir, start_startup_timeline
from picasapy.perf.logwriter import session_header
from picasapy.perf.tesztuzem import (
    argv_kapcsolo_nelkul,
    argv_tesztuzem,
    irj_indulasi_naplot,
    konyvtar_merete,
    naplo_szovege,
    tesztuzem_bekapcsolva,
)
from picasapy.scanner import (
    EXCLUDE_FOLDERS_NAME,
    WATCHED_FOLDERS_NAME,
    find_exclude_folders_file,
    find_watched_folders_file,
    read_exclude_folders,
    read_watched_folders,
)
from picasapy.thumbs import ThumbnailCache
from picasapy.version import version_string
from .confirm_settings_bridge import ConfirmSettingsBridge
from .controller import AppController
from .data_location import read_data_root
from .error_log import error_log_path, install_error_log
from .exported_folders import (
    EXPORTED_FOLDERS_SETTINGS_KEY,
    existing_exported_folders,
    registered_exported_folders,
)
from .compact_controller import CompactController
from .relocate_controller import RelocateController
from . import collage_output, collage_prefs
from .dedup_controller import DedupController
from .email_controller import EmailController
from .discovery_controller import DiscoveryController
from .drop_import_controller import DropImportController
from .edit_controller import EditController
from .edit_preview import EditPreviewProvider
from .effect_thumbnails import EffectThumbnailProvider
from .face_scan_controller import FaceScanController
from .faces_helper import FacesHelper
from .language_controller import (
    DEFAULT_LANGUAGE,
    LANGUAGE_KEY,
    coerce_language,
)
from .display_mode_controller import wire_display_mode
from .fileops_controller import FileOpsController
from .folder_hierarchy_controller import FolderHierarchyController
from .folder_tree_controller import FolderTreeController
from .import_source_controller import ImportSourceController
from .models import sorted_folder_rows
# #1472: a nyomtatás vezérlője. Az import VÉDETT, mert a
# `print_controller` a `PySide6.QtPrintSupport`-ra épül, azt pedig a
# Debian/Ubuntu-féle rendszercsomag KÜLÖN modulba teszi (a pip-es wheel —
# és így a CI — mindent hoz, ld. #664). Egy csupasz import ilyen gépen az
# egész alkalmazás indulását megölné egy nyomtatás miatt; a felület a
# hiányt nem hallgatja el, ld. `PrintDialog.qml` `openForRows`.
try:
    from .print_controller import PrintController
except ImportError:  # pragma: no cover — csak a hiányos Qt-telepítésen fut
    PrintController = None
from .platform_storage import (
    MigrationNotice,
    StorageAlreadyRunning,
    StorageBootstrap,
    StorageMigrationError,
    StoragePaths,
    bootstrap_storage,
    default_storage_paths,
)
from .startup_status import StartupStatus
from .thumbnail_provider import ThumbnailProvider
from .timeline_controller import TimelineController
from .webexport_controller import WebExportController
from .window_geometry import virtual_desktop_rect, wire_window_geometry

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


def _platform() -> str:
    """A futó platform — külön függvény, hogy a teszt helyettesíthesse (#1217).

    A modul többi platformfüggő ága nevesített `platform=` paramétert kap;
    ez az egyetlen, amit nem hívunk paraméterrel (a Qt indulása ELŐTT fut).
    """
    return sys.platform


def _thumbnail_cache_size(device_pixel_ratio: float) -> int:
    """A cache-elt thumbnail célmérete (leghosszabb oldal, px).

    A cél mindig legalább a rács legnagyobb megjelenítési mérete, a
    képernyő devicePixelRatio-jával szorozva — így a GridView-delegate
    Image-e (ThumbDelegate.qml) minden csúszka-fokon KICSINYÍTÉSSEL áll
    elő a cache-elt képből, sosem nagyítással (ami homályos lenne).
    Felfelé kerekítünk (math.ceil), hogy törtszámú DPR (pl. 1.5) se
    essen a küszöb alá. RPi5-ön jellemzően DPR=1 (natív HDMI kimenet),
    de HiDPI monitoron (DPR=2) is éles maradjon a legnagyobb fokozat —
    ezért nem rögzítünk fix 256-os cache-méretet, hanem a tényleges
    képernyőhöz igazítjuk.
    """
    ratio = max(device_pixel_ratio, 1.0)
    return math.ceil(_GRID_MAX_THUMB_PX * ratio)


def _screen_device_pixel_ratio(app: QGuiApplication) -> float:
    """A elsődleges képernyő devicePixelRatio-ja; hiányzó képernyőnél 1.0."""
    screen = app.primaryScreen()
    return screen.devicePixelRatio() if screen is not None else 1.0


def _onjavito_kollazsmappa(conn, settings: QSettings) -> None:
    """A Kollázsok mappa felvétele az indexbe INDULÁSKOR (#1075).

    A tulajdonos jelentése a v0.8.18-ról: *„nincsen Kollázsok mappa sehol,
    eltűnt. A Projektek mappa alatt sincsen semmi ismét."*

    A Projektek gyűjtemény két feltételt kér: a mappa legyen az indexben, és
    a `.picasa.ini`-je hordozza a `P2category`-t. Mindkettőt eddig KIZÁRÓLAG
    a mentés állította elő (#1046, #1048), tehát visszamenőleg semmi:

    * a 0.8.8 ELŐTT készült kollázsok mappájában nincs `.picasa.ini`, és a
      frissítés nem javította utólag;
    * ha az indexelés egyszer elbukott, a mentés-ág némán továbbment, és a
      mappa soha többé nem került be.

    Ezért fut ez minden induláskor. A megjelölés feltétele szigorú (ld.
    `ensure_project_album`): csak a MI kimenetünket jelöljük meg.

    A hiba nyelt — egy önjavítási kísérlet soha nem akadályozhatja meg az
    indulást —, de NAPLÓZVA: a #1075 másik fele éppen az volt, hogy a néma
    ág miatt vakon álltunk."""
    try:
        mappa = collage_output.output_dir(
            settings.value(collage_prefs.OUTPUT_DIR_KEY)
        )
        if not mappa.is_dir():
            return
        collage_output.ensure_project_album(mappa)
        sync_folder(conn, mappa, mappa)
    except Exception:  # noqa: BLE001 - az indulás soha nem hiúsulhat meg tőle
        logging.getLogger(__name__).warning(
            "a Kollázsok mappa indulási felvétele hibára futott", exc_info=True
        )


def _ujraindexelt_exportcelok(conn, settings: QSettings) -> None:
    """A nyilvántartott exportcélok visszavétele az indexbe INDULÁSKOR
    (#1565) — a `_onjavito_kollazsmappa` (#1075) párja.

    ⚠️ **Enélkül a javítás egyetlen munkamenetig élne.** A közvetlenül
    előtte futó `prune_foreign_folders` (#58) MINDEN olyan mappát töröl az
    indexből, amely egyik figyelt gyökér alatt sincs — az exportcél pedig
    épp ilyen (`<Képek>/Picasa/Exports`). A felhasználó tehát exportálás
    után látná a képeit, a következő indításnál viszont az „Exportált
    képek" ismét üres rácsot nyitna. Ugyanez a szerkezet tartja bent a
    Kollázsok mappát is.

    A forrás a korlátos, létezésre szűrt nyilvántartás (`exported_folders`,
    #457) — figyelt gyökeret NEM veszünk fel a felhasználó nevében, a
    `WatchedFolders.txt` érintetlen marad. A gyökér mindig MAGA a célmappa,
    tehát egyetlen mappa kerül be, nem részfa.

    A hiba nyelt (az indulás soha nem hiúsulhat meg tőle), de naplózva."""
    try:
        mappak = existing_exported_folders(
            settings.value(EXPORTED_FOLDERS_SETTINGS_KEY)
        )
    except Exception:  # noqa: BLE001 - olvashatatlan beállítás sem állíthat meg
        logging.getLogger(__name__).warning(
            "az exportcélok nyilvántartása nem olvasható", exc_info=True
        )
        return
    for mappa in mappak:
        try:
            sync_folder(conn, Path(mappa), Path(mappa))
        except Exception:  # noqa: BLE001 - egy rossz cél ne vigye el a többit
            logging.getLogger(__name__).warning(
                "az exportcél indulási felvétele hibára futott: %s",
                mappa,
                exc_info=True,
            )


def _takaritas_gyokerei(
    roots: tuple[str | Path, ...], settings: QSettings
) -> tuple[str, ...]:
    """A #58 induláskori takarítás VÉDETT gyökerei (#1667).

    A figyelt gyökerek mellé a **nyilvántartott exportcélok** is bekerülnek.
    Az exportcél a #1565 óta SAJÁT GYÖKÉRKÉNT van indexelve — a takarítás
    szempontjából tehát pontosan olyan jogos horgony, mint egy figyelt
    mappa, nem „ottragadt idegen mappa".

    ## Miért ez a #1667 javítása

    A takarítás eddig minden induláskor kidobta az exportcélok mappa- ÉS
    fotósorait (a `folder_scan_state`-tel együtt), a rá következő
    `_ujraindexelt_exportcelok` pedig NULLÁRÓL építette vissza őket. Az
    üres `photos` tábla miatt a `_sync_folder` inkrementális kihagyása nem
    tudott működni: minden exportált képre lefutott a (drága) EXIF/IPTC-
    olvasás. MÉRVE (RPi5, 4 exportcél / 180 kép): **180 fájlnyitás
    indulásonként**; a védelemmel **0**. A tulajdonos gépén ugyanez a
    szakasz **8 406 ms** volt — az indulás 77,8%-a (#1667).

    ## Amit a védelem nem tesz meg

    A már nem NYILVÁNTARTOTT exportcél (kiesett a 20 elemű listából)
    továbbra is kitakarítódik. A nyilvántartott, de a lemezen épp nem
    látható cél viszont bent marad: a hiány nem bizonyíték (#1560), és a
    listát szándékosan nem szűrjük létezésre — ld.
    `registered_exported_folders`."""
    return (
        *(str(root) for root in roots),
        *registered_exported_folders(
            settings.value(EXPORTED_FOLDERS_SETTINGS_KEY)
        ),
    )


def _exportcelok_visszavetele(index_db: Path, settings: QSettings) -> None:
    """A #1565 visszavétele SAJÁT kapcsolaton, az első képkocka UTÁN (#1667).

    Az indexkarbantartásnak semmi köze ahhoz, hogy az ablak megjelenjen —
    a #1601 ugyanezért tolta a könyvtár betöltését a `frameSwapped` mögé.
    A `_takaritas_gyokerei` védelme óta ez a lépés önjavítás: azt hozza
    rendbe, ami a program KIKAPCSOLT állapotában változott (új fájl az
    exportmappában), illetve azt, amit egy korábbi verzió takarítása még
    kidobott.

    A hiba nyelt — egy önjavítás soha nem viheti el a felületet —, de
    naplózva."""
    try:
        with open_index(index_db) as conn:
            _ujraindexelt_exportcelok(conn, settings)
    except Exception:  # noqa: BLE001 - a felület már áll, ez csak karbantartás
        logging.getLogger(__name__).warning(
            "az exportcélok visszavétele hibára futott", exc_info=True
        )


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

    ## Versenyhelyzet a háttér-szinkronnal (#1716)

    ⚠️ A `_start_and_finish` ezt a lépést a `_start_initial_scan` (tehát a
    `controller.start()` → `rescan()`) ELŐTT hívja, és ez a sorrend a
    SZINKRONPONT — nem zár. A `rescan()` saját SQLite-kapcsolattal futó
    HÁTTÉRSZÁLAT indít (`_sync_worker`, ld. `library_controller.py`), ami
    ugyanazokat a táblákat írja. Ha a takarítás ezután (vagy azzal egy
    időben) futna, a törlés versenyhelyzetbe kerülne a szál írásával: egy
    épp szinkronizált mappa sora eltűnhetne a lába alól. Mivel a takarítás
    a FŐSZÁLON, egyetlen tranzakcióban fut és `commit()`-tal lezárul,
    MIELŐTT a `controller.start()` egyáltalán meghívná a `rescan()`-t, a
    háttérszál a takarítás befejezése előtt még nem is létezik — a
    sorrend tehát garantálja a kizárást, zár nélkül. Az elhelyezés-őr
    (`tests/perf/test_takaritas_utrol_1716.py`) ezt a sorrendet fagyasztja
    be: ha a hívás a `_start_initial_scan` MÖGÉ kerülne, az őr bukik.

    A bal hasáb mappafája (`_reload_folder_hierarchy`) a takarítás ELŐTT,
    az első képkocka előtt egyszer már feltöltődött — a takarítás után
    ezért a hívó azonnal újratölti, hogy a nézet ne mutasson egy már
    törölt, ottragadt mappát a következő szinkron végéig.

    A hiba nyelt (a takarítás soha nem hiúsulhat meg tőle), de naplózva."""
    try:
        with open_index(index_db) as conn:
            prune_foreign_folders(conn, _takaritas_gyokerei(roots, settings))
    except Exception:  # noqa: BLE001 - a felület már áll, ez csak karbantartás
        logging.getLogger(__name__).warning(
            "az ottragadt mappák takarítása hibára futott", exc_info=True
        )


def _data_dir(platform: str | None = None) -> Path:
    """Az index-SQLite (+ zárolófájl) mappája — ha a "Move Database"
    dialóguson (#368) keresztül egyszer már áthelyezésre került, az
    útvonal-felülbírálás (`data_location.py`) felülírja a platform-
    alapértelmezést; ilyenkor a cache-cel EGYESÍTVE ugyanazt a mappát
    adja vissza, mint `_cache_dir()` (ld. ott)."""
    active_platform = sys.platform if platform is None else platform
    override = read_data_root(_config_dir(platform=active_platform))
    if override is not None:
        return override
    return default_storage_paths(active_platform).data


def _cache_dir(platform: str | None = None) -> Path:
    """A thumbnail-lemezcache mappája — áthelyezés után (#368) a
    `_data_dir()`-rel EGYESÍTVE, hogy a Picasa-paritású "egy adatbázis-
    mappa" elv teljesüljön (a hívó ide illeszti a "thumbs" alkönyvtárat,
    ld. `run()`)."""
    active_platform = sys.platform if platform is None else platform
    override = read_data_root(_config_dir(platform=active_platform))
    if override is not None:
        return override
    return default_storage_paths(active_platform).cache


def _config_dir(platform: str | None = None) -> Path:
    active_platform = sys.platform if platform is None else platform
    return default_storage_paths(active_platform).config


def _bootstrap_storage(
    platform: str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
    acquire_lock: Callable[[Path], object | None] | None = None,
    migrate: Callable[[StoragePaths, StoragePaths], object] | None = None,
) -> StorageBootstrap:
    """A Qt-zárolót a platformfüggetlen, tesztelhető bootstraphoz köti."""
    active_platform = sys.platform if platform is None else platform
    return bootstrap_storage(
        active_platform,
        acquire_lock=(
            _acquire_instance_lock if acquire_lock is None else acquire_lock
        ),
        environ=environ,
        home=home,
        migrate=migrate,
    )


def _force_qml_dialogs(platform: str = sys.platform) -> bool:
    """Kényszerítsük-e a saját (nem natív) QML-dialógusokat.

    Linuxon/macOS-en igen: az app mindig világos, a rendszer sötét témájú
    választója kilógna (rögzített dizájn-döntés). Windowson viszont a natív
    mappaválasztó kell (#58): meghajtók, hálózati helyek és ékezetes mappák
    csak abból érhetők el rendesen — a QML-es tartalék a meghajtó szintje
    fölé nem tud lépni."""
    return platform != "win32"


def _watched_folders_path() -> Path:
    """A `WatchedFolders.txt` útvonala — kis-nagybetű-független kereséssel
    (#145): élesben (pl. importált/áthozott konfig-könyvtárban) kisbetűs
    néven is előfordulhat. Ha nincs ilyen fájl, a kanonikus nevet adja
    vissza (ide fog írni a `write_watched_folders`)."""
    config_dir = _config_dir()
    return find_watched_folders_file(config_dir) or (
        config_dir / WATCHED_FOLDERS_NAME
    )


def _exclude_folders_path() -> Path:
    """A `FRExcludeFolders.txt` útvonala — kis-nagybetű-független kereséssel
    (#145/#449, a `_watched_folders_path` mintáját követve). NEGYEDIK,
    a figyelt-mappa hármastól (Scan Always/Once/Remove) FÜGGETLEN
    kapcsoló: az arcfelismerésből kizárt mappák (ma még csak SZÁNDÉK-
    rögzítés, arcfelismerés-motor nélkül, ld. library_controller.py)."""
    config_dir = _config_dir()
    return find_exclude_folders_file(config_dir) or (
        config_dir / EXCLUDE_FOLDERS_NAME
    )


def _resolve_roots(argv: list[str]) -> tuple[str, ...]:
    if len(argv) > 1:
        return tuple(argv[1:])
    return read_watched_folders(_watched_folders_path())


def _offer_error_log(path: Path) -> None:
    """Adatbázis-hiba után felajánlja a napló megtekintését (#449).

    Az eredeti szövege: „There were errors loading the Picasa database.
    Would you like to view the error log?" — a megnyitás a rendszer
    társított alkalmazásával megy. A program a válasz után elindul: az
    index a következő beolvasáskor újraépül.
    """
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import QMessageBox

    text = QCoreApplication.translate(
        "startup",
        "There were errors loading the PicasaPy database. "
        "Would you like to view the error log?",
    )
    answer = QMessageBox.question(
        None, QCoreApplication.translate("startup", "Database error"), text
    )
    if answer == QMessageBox.StandardButton.Yes and path.exists():
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


def _acquire_instance_lock(data_dir: Path) -> QLockFile | None:
    """Egy-példányos futás: zárolófájl; ha már fut a PicasaPy, None.

    A QLockFile a PID-et is tárolja, így az összeomlott példány elavult
    zárját magától felismeri és átveszi.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(data_dir / "picasapy.lock"))
    if lock.tryLock(100):
        return lock
    return None



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


def _install_ui_font(app: QGuiApplication) -> None:
    """A csomagolt felület-betűtípus betöltése és beállítása (#526).

    Ha a betöltés bármiért nem sikerül (hiányzó fájl egy csonka
    telepítésben, vagy a platform elutasítja), NÉMÁN a rendszer alapértelmezett
    betűtípusánál maradunk — a felület ettől még használható, csak nem
    Picasa-arányos.
    """
    families: list[str] = []
    for name in _UI_FONT_FILES:
        path = _APP_DIR / "assets" / "fonts" / name
        if not path.is_file():
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id >= 0:
            families.extend(QFontDatabase.applicationFontFamilies(font_id))
    if _UI_FONT_FAMILY not in families:
        return
    font = app.font()
    font.setFamily(_UI_FONT_FAMILY)
    app.setFont(font)


def _set_windows_app_id() -> None:
    """Windows taskbar-ikon: explicit AppUserModelID-beállítás (#67).

    Windows alatt, ha az alkalmazás python.exe/pythonw.exe-ből fut (saját .exe
    nélkül), a taskbar az értelmezőhöz köti a csoportosítást és az ikont,
    hacsak nincs explicit AppUserModelID beállítva. Ez az API csak Windowson
    érhető el; Linuxon/macOS-en nincs hatása.

    A hívás a QGuiApplication indítása ELŐTT kell történjen, hogy a taskbar-
    ikon azonnal helyesen jelenjen meg.
    """
    if _platform() != "win32":
        return  # Csak Windowson van értelme

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "PicasaPy.PicasaPy"
        )
    except (AttributeError, OSError):
        # AttributeError: régi Windows-verzió vagy hiányzó API
        # OSError: nem admin-felhasználó vagy rendszer-hiba — csendben kimarad
        pass


# #240: a splash minimális megjelenítési ideje — az első képkockától
# számítva legalább ennyi ideig látszik, gyors betöltésnél is.
_SPLASH_MIN_VISIBLE_MS = 1500


def _remaining_splash_ms(
    elapsed_ms: float, minimum_ms: int = _SPLASH_MIN_VISIBLE_MS
) -> int:
    """Hátralévő splash-idő: a minimum-megjelenítésből még ki nem töltött
    rész (0, ha a betöltés maga is elég sokáig tartott)."""
    return max(0, round(minimum_ms - elapsed_ms))


def _start_initial_scan(
    startup_status: StartupStatus,
    controller: object,
    migration_notice: MigrationNotice | None,
) -> None:
    """Elindítja a kezdeti szkennelést, előtte felhasználói státuszt ad.

    A migrációs üzenet ugyanazon, már kirajzolt splash-csatornán marad
    látható a minimum splash-idő végéig; nem sikert álcázunk hibának.
    """
    if migration_notice is None:
        text = QCoreApplication.translate("startup", "Scanning folders…")
    else:
        template = QCoreApplication.translate(
            "startup", "Existing data migrated from {source} to {target}."
        )
        text = template.format(
            source=migration_notice.source, target=migration_notice.target
        )
    startup_status.report(text)
    controller.start()


def _window_icon_path(platform: str = sys.platform) -> Path:
    """Az ablak-/taskbar-ikon fájlja (#67): Windowson a több méretű `.ico`
    (a taskbar 16–32 px-es változatai előre renderelve, nem futásidejű
    PNG-skálázással — az hol késleltetve, hol egyáltalán nem jelent meg),
    máshol a 256 px-es PNG."""
    if platform == "win32":
        return _APP_DIR / "assets" / "icon.ico"
    return _APP_DIR / "assets" / "icon.png"


def _install_desktop_entry() -> None:
    """Asztali bejegyzés + ikon telepítése (~/.local/share) — Waylanden a
    tálca az app_id ↔ .desktop párosításból kapja az ikont. Idempotens."""
    base = Path(
        os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    )
    icon_target = base / "icons" / "hicolor" / "256x256" / "apps" / "picasapy.png"
    icon_source = _APP_DIR / "assets" / "icon.png"
    launcher = Path(__file__).resolve().parents[3] / "picasapy"
    exec_line = str(launcher) if launcher.exists() else "picasapy"
    desktop_text = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=PicasaPy\n"
        "Comment=Picasa-kompatibilis fotókezelő\n"
        f"Exec={exec_line} %U\n"
        "Icon=picasapy\n"
        "Terminal=false\n"
        "Categories=Graphics;Photography;Viewer;\n"
        "StartupWMClass=picasapy\n"
    )
    desktop_target = base / "applications" / "picasapy.desktop"
    try:
        if (
            not icon_target.exists()
            or icon_target.read_bytes() != icon_source.read_bytes()
        ):
            icon_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(icon_source, icon_target)
            _refresh_icon_cache(base / "icons" / "hicolor")
        if (
            not desktop_target.exists()
            or desktop_target.read_text(encoding="utf-8") != desktop_text
        ):
            desktop_target.parent.mkdir(parents=True, exist_ok=True)
            desktop_target.write_text(desktop_text, encoding="utf-8")
    except OSError:
        pass  # csak kényelmi funkció — hibája nem akadályozhat indulást


def _refresh_icon_cache(icons_dir: Path) -> None:
    """A hicolor icon-theme.cache frissítése ikoncsere után — enélkül a
    tálca a cache-elt régi ikont mutatja, amíg kézzel nem frissítik (#35).
    Best-effort: ahol nincs gtk-update-icon-cache (pl. Windows), kimarad."""
    tool = _which("gtk-update-icon-cache")
    if tool is None:
        return
    try:
        _run(
            [tool, "-f", "--ignore-theme-index", str(icons_dir)],
            check=False,
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        pass  # kényelmi funkció — hibája nem akadályozhat indulást


def _watched_folder_of(path: str, roots) -> str | None:
    """A fájl szülőmappája, ha valamelyik figyelt gyökér alatt van; None,
    ha nem — figyelt körön kívüli mappát nem szinkronizálunk az indexbe."""
    folder = Path(path).parent
    for root in roots:
        try:
            if folder == Path(root) or folder.is_relative_to(root):
                return str(folder)
        except (OSError, ValueError):
            continue
    return None


def wire_fileops(fileops: FileOpsController, controller: AppController) -> None:
    """Fájlműveletek utáni index-frissítés (#15): a sikeres átnevezés/
    áthelyezés/másolás/törlés után az érintett mappák célzott resyncje, hogy
    a rács (és a .picasa.ini-t követő szekció) azonnal a valós állapotot
    mutassa."""

    def refresh(*paths: str) -> None:
        seen: set[str] = set()
        for path in paths:
            folder = _watched_folder_of(path, controller.watchedFolders)
            if folder is not None and folder not in seen:
                seen.add(folder)
                controller.resyncFolder(folder)

    fileops.photoRenamed.connect(lambda old, new: refresh(old, new))
    fileops.photoMoved.connect(lambda old, new: refresh(old, new))
    fileops.photoDeleted.connect(refresh)
    # #1522: másolásnál CSAK a célmappa változott — a forrás érintetlen
    # marad, annak újraolvasása fölösleges lemez- és indexmunka volna.
    fileops.photoCopied.connect(lambda _source, new: refresh(new))
    # #1538: a MAPPA áthelyezése SZÁNDÉKOSAN nem a `refresh()`-en megy. Az
    # fájlutakra van szabva (`_watched_folder_of` a `.parent`-et veszi),
    # tehát egy mappára a SZÜLŐT olvasná újra — ráadásul nem-rekurzívan,
    # így sem az áthelyezett mappa sora, sem az almappáié nem kerülne a
    # helyére. A részfa-logika a vezérlőben él (`resyncMovedFolder`), mert
    # a RÉGI oldalhoz az INDEXET kell megkérdezni: a lemezen az már nincs.
    fileops.folderMoved.connect(
        lambda old, new: controller.resyncMovedFolder(old, new)
    )
    # #1638: a lomtárba tett mappa kivezetése az indexből — ugyanaz a
    # részfa-logika, mint az áthelyezés RÉGI oldalán (a lemezen már nincs
    # meg, tehát az indexet kell megkérdezni).
    fileops.folderDeleted.connect(
        lambda path: controller.resyncDeletedFolder(path)
    )


def wire_dedup(dedup: DedupController, controller: AppController) -> None:
    """A duplikátum-kezelő utáni index-frissítés (#1539).

    A dedup mindkét feloldó művelete a LEMEZT változtatja meg, az indexnek
    viszont eddig egyikről sem szólt: az `itemResolved`-nek egyetlen
    fogyasztója volt, a dialógus sorát levevő QML-kezelő.

    Mérve (valódi vezérlő, produkciós `FOLDER_POLL_MS`, figyelő nélkül): a
    „Duplikátumok" almappába mozgatott kép **25 s alatt sem jelent meg**, a
    forrásmappából pedig 10,3 s-ig (a #1275 lekérdezéssel), illetve
    egyáltalán nem (anélkül) tűnt el a sora.

    Két jelzés kell, mert két mappa változik:

    * `itemResolved` — a FORRÁSMAPPA, mindkét ágon (kukázás és áthelyezés
      is onnan viszi el a képet);
    * `photoRelocated` — a CÉLMAPPA, ami frissen létrehozott, sosem
      indexelt könyvtár (a #1522 alakja).

    A `deleteOthers` ágán SZÁNDÉKOSAN nincs második kötés: a Kuka nem a
    figyelt körben van, oda nincs mit újraolvasni."""
    dedup.itemResolved.connect(controller.resyncOutputFolder)
    dedup.photoRelocated.connect(
        lambda _source, new: controller.resyncOutputFolder(new)
    )


def _configured_language() -> str:
    """A betöltendő nyelv: a környezeti változó nyer, utána a mentett
    beállítás, végül az alapértelmezés (#333).

    A rendszer nyelvét SZÁNDÉKOSAN nem nézzük: a felhasználó kérése szerint
    az alapértelmezés az angol, és a váltás a beállításokban történik.
    """
    forced = os.environ.get("PICASAPY_LANG")
    if forced:
        return coerce_language(forced)
    settings = QSettings("PicasaPy", "PicasaPy")
    return coerce_language(settings.value(LANGUAGE_KEY, DEFAULT_LANGUAGE))


def _install_translator(
    app: QGuiApplication, language: str | None = None
) -> QTranslator | None:
    """A `language` (vagy a beállított) nyelv fordítójának telepítése.

    Az angolhoz nincs `.qm` — a forrásszövegek maguk angolok —, ezért ott
    nincs mit betölteni, és ez nem hiba.
    """
    code = coerce_language(language) if language else _configured_language()
    if code == DEFAULT_LANGUAGE:
        return None
    translator = QTranslator(app)
    if translator.load(f"picasapy_{code}", str(_I18N_DIR)):
        app.installTranslator(translator)
        return translator
    return None


def _indexelt_kepszamok(data_dir: Path) -> tuple[int, ...]:
    """A mappánkénti képdarabszámok az indexből — CSAK SZÁMOK.

    ⚠️ Adatvédelem (#211/#1654): a mappanevek és útvonalak itt SZÁNDÉKOSAN
    eldobódnak, még mielőtt a naplóösszeállítóhoz érnének. A #1653 fő
    gyanúja a méretfüggés, ahhoz pedig a darabszám elég.

    Hibánál üres sorozat: egy diagnosztika nem dönthet el egy indulást."""
    try:
        with open_index(data_dir / "index.db") as conn:
            return tuple(
                int(count) for _name, _path, count, *_rest in sorted_folder_rows(conn)
            )
    except sqlite3.DatabaseError:
        logging.getLogger(__name__).warning(
            "a könyvtárméret leolvasása hibára futott", exc_info=True
        )
        return ()


def _jelentsd_az_idovonalat(timeline, kepszamok=None, vedett_gyokerek=None) -> None:
    """#1601/#1654: az indulási napló kiírása — kikapcsolva NEM CSINÁL SEMMIT.

    Két helyre megy, mert két különböző igényt szolgál ki: a `stderr`-re a
    fejlesztő/terminálból indító lát azonnal, a fájlt pedig a felhasználó
    tudja **átküldeni** (`Súgó ▸ Napló elküldése`, #1654) — az útvonalát
    ezért kiírjuk.

    A napló három rétegből áll (#1654/3): a `perf/logwriter.py`
    session-fejléce, a #1601 szakaszos bontása, és a könyvtár mérete
    darabszámban. A `kepszamok` egy KÉSLELTETETT hívható (a mappánkénti
    képdarabszámokat adja) — kikapcsolt mérésnél meg sem hívjuk, tehát az
    indexlekérdezés költsége sem merül fel.

    A jelentés nem tartalmaz fájlnevet, teljes útvonalat és
    felhasználónevet, ld. `perf/tesztuzem.py` (`utvonalmentes`).

    Hibája soha nem akadályozhatja az indulást — egy diagnosztika nem
    fontosabb a programnál."""
    if not timeline.enabled:
        return
    try:
        from PySide6.QtCore import qVersion

        szoveg = naplo_szovege(
            idovonal_jelentes=timeline.render(
                app_version=version_string(), qt_version=qVersion()
            ),
            fejlec=session_header(version_string(), qVersion() or ""),
            meret=konyvtar_merete(kepszamok() if kepszamok is not None else ()),
            # #1712: a #1706 szerint EZ a szám a domináns tényező, nem a
            # mappáké — késleltetve hívjuk, hogy kikapcsolt tesztüzemben
            # ne kerüljön semmibe.
            vedett_gyokerek=(
                len(vedett_gyokerek()) if vedett_gyokerek is not None else None
            ),
        )
        print(szoveg, file=sys.stderr)
        target = irj_indulasi_naplot(szoveg, default_log_dir())
        if target is not None:
            print(f"Az indulási napló ide került: {target}", file=sys.stderr)
    except Exception:  # noqa: BLE001 - a diagnosztika sosem viheti el az appot
        logging.getLogger(__name__).warning(
            "az indulási idővonal kiírása hibára futott", exc_info=True
        )


def _indulasi_idovonal(
    argv: list[str],
    *,
    settings=None,
    environ: Mapping[str, str] | None = None,
    entry_at: float | None = None,
    clock=time.perf_counter,
) -> tuple[object, list[str]]:
    """A `run()` LEGELSŐ érdemi lépése: mérünk-e, és mivel indulunk (#1654).

    Három, egyenrangú bekapcsolási út van — bármelyik elég:

    * a **tartós tesztüzem** (`QSettings`), amit a `Súgó ▸ Tesztüzem`
      menüpont állít, és ami TÚLÉLI a kilépést. Ez az a bejárat, amit a
      tulajdonos használ: bekapcsolja, kilép, és a KÖVETKEZŐ indulás
      magától méri magát;
    * a `--tesztuzem` **parancssori kapcsoló** — csak erre a futásra, a
      beállítást nem írja át (fejlesztői és CI-oldal);
    * a `PICASAPY_STARTUP_TIMELINE=1` **környezeti változó** (#1601), amire
      a #1653 windowsos CI-mérése épül.

    A visszaadott argumentumlistából a `--tesztuzem` kikerül: az
    `_resolve_roots` MINDEN `argv[1:]` elemet figyelt gyökérnek vesz, tehát
    bennhagyva egy `--tesztuzem` nevű mappát próbálnánk indexelni.

    ⚠️ Az `entry_at` szakaszát ITT zárjuk le, közvetlenül a példány
    létrehozása után: a naplózás így az ELSŐ ezredmásodperctől — a Python-
    és PySide6-importoktól — fut, nem csak innentől."""
    if settings is None:
        settings = QSettings("PicasaPy", "PicasaPy")
    tesztuzem = argv_tesztuzem(argv) or tesztuzem_bekapcsolva(settings)
    timeline = start_startup_timeline(environ, forced=tesztuzem, clock=clock)
    if entry_at is not None:
        timeline.mark_from(entry_at, "Python- és PySide6-modulok betöltése")
    return timeline, argv_kapcsolo_nelkul(argv)


def run(argv: list[str], *, entry_at: float | None = None) -> int:
    """Az alkalmazás indítása.

    #1601: az `entry_at` a belépési pont (`__main__.py`) legelső saját
    sorában olvasott `time.monotonic()` — ebből látszik, mennyit visz el
    maga a Python- és PySide6-import, mielőtt idáig eljutnánk. `None`
    esetén ez a szakasz kimarad a jelentésből; mérni nem kötelező.

    Az idővonal alapból KI van kapcsolva; a tartós „tesztüzem" beállítás
    (#1654), a `--tesztuzem` kapcsoló és a `PICASAPY_STARTUP_TIMELINE=1`
    környezeti változó (#1601) kapcsolja be — ld. `_indulasi_idovonal`."""
    timeline, argv = _indulasi_idovonal(argv, entry_at=entry_at)

    # A PicasaPy egyelőre MINDENHOL világos (a sötét téma V3-feature):
    # Fusion stílus + explicit világos paletta; Linuxon/macOS-en a saját,
    # világos QML-dialógusok a rendszer sötét mappaválasztója helyett.
    # Windowson natív dialógus kell — ld. _force_qml_dialogs (#58).
    if _force_qml_dialogs():
        QGuiApplication.setAttribute(
            Qt.ApplicationAttribute.AA_DontUseNativeDialogs
        )
    QQuickStyle.setStyle("Fusion")

    # Windows taskbar-ikon: explicit AppUserModelID-beállítás (#67)
    _set_windows_app_id()

    timeline.mark("Qt-stílus és platform-kapcsolók")
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
    _install_ui_font(app)
    timeline.mark("felület-betűtípus betöltése")
    _install_translator(app)
    timeline.mark("fordítás betöltése")

    # #1076: Windowson a legacy konfigurációból feloldott EFFEKTÍV
    # adatgyökeret még a migráció előtt zárjuk. A bootstrap az útvonalakat
    # egyszer számolja ki, a régi és új zárat pedig futás végéig őrzi.
    try:
        storage_bootstrap = _bootstrap_storage()
    except StorageAlreadyRunning:
        print(
            "A PicasaPy már fut — egyszerre csak egy példány engedélyezett.",
            file=sys.stderr,
        )
        return 0
    except StorageMigrationError as error:
        print(str(error), file=sys.stderr)
        return 1
    timeline.mark("tárhely előkészítése (zár + migráció)")

    # Indítóképernyő-híd (#189): korán jön létre, hogy az első állapot-
    # üzenetek is látsszanak; helyi változóban tartva (GC ellen).
    # #243: amíg az eredeti Picasa effekt-készlete nem teljes (#20, #190),
    # a splash a betöltés végén „félkész szoftver" figyelmeztetést és OK
    # gombot mutat — az effekt-paritás elérésekor ezt False-ra kell állítani.
    startup_status = StartupStatus(
        QCoreApplication.translate("startup", "Starting…"),
        requires_confirmation=True,
    )

    with timeline.phase("figyelt gyökerek beolvasása (WatchedFolders.txt)"):
        roots = _resolve_roots(argv)
    data_dir = storage_bootstrap.data_dir
    cache_dir = storage_bootstrap.cache_dir
    config_dir = storage_bootstrap.config_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    # #449: hibanapló — a WARNING és súlyosabb üzenetek fájlba is mennek,
    # hogy adatbázis-hiba esetén legyen mit felajánlani megtekintésre
    error_log = install_error_log(data_dir) or error_log_path(data_dir)
    timeline.mark("hibanapló előkészítése")

    _install_desktop_entry()
    timeline.mark("asztali bejegyzés telepítése")

    # Ottragadt gyökerek takarítása (#58): az indexben csak a most figyelt
    # mappák maradhatnak — a korábbi futások (pl. régi parancssori argumentum)
    # mappái különben örökre a bal hasábban ragadnának.
    startup_status.report(
        QCoreApplication.translate("startup", "Preparing index…")
    )
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
    except sqlite3.DatabaseError:
        # #449: az eredeti sem omlott össze némán és nem javított titokban —
        # FELAJÁNLOTTA a hibanaplót („There were errors loading the Picasa
        # database. Would you like to view the error log?"). A program ezután
        # elindul: az index önmagát újraépíti a következő beolvasáskor.
        logging.getLogger(__name__).exception("az index megnyitása hibára futott")
        _offer_error_log(error_log)

    # #83: a cache-méretet a képernyő DPR-jéhez igazítjuk, hogy a rács
    # legnagyobb fokozata (256px) se legyen homályos HiDPI kijelzőn.
    startup_status.report(
        QCoreApplication.translate("startup", "Loading photo library…")
    )
    timeline.mark("index előkészítése — utómunka")
    cache_size = _thumbnail_cache_size(_screen_device_pixel_ratio(app))
    provider = ThumbnailProvider(
        ThumbnailCache(
            cache_dir / "thumbs",
            size=cache_size,
            max_bytes=_THUMB_CACHE_LIMIT_BYTES,
        )
    )
    controller = AppController(
        data_dir / "index.db",
        roots,
        provider,
        watched_file=_watched_folders_path(),
        exclude_file=_exclude_folders_path(),
        face_excluded=read_exclude_folders(_exclude_folders_path()),
    )
    timeline.mark("bélyegkép-gyorstár és fővezérlő létrehozása")

    # szerkesztő-előnézet (#19): a provider a filters= láncot alkalmazva
    # rendereli a képet; a hidat az EditController adja a QML-nek
    edit_preview = EditPreviewProvider()
    edit_controller = EditController(edit_preview)
    # #644: minden mentett szerkesztési lánc a TARTÓS naplóba is bekerül — ez
    # az egyetlen nyomunk, ha a párhuzamosan futó Picasa később felülírja a
    # `.picasa.ini`-t a saját adatbázis-rekordjával.
    #
    # #750: ez a JELZÉS-kötés csak a szerkesztőé, mert az `EditController`
    # önálló QObject. A többi lánc-író (csoportos effekt, a két effekt-
    # beillesztés, a lemezre mentés) maga is az `AppController` szelete,
    # ezért közvetlenül a `recordSavedChains()`-t hívja — nincs második
    # jelzés-út, amit itt el lehetne felejteni bekötni.
    edit_controller.chainSaved.connect(controller.recordSavedChain)

    # effekt-gomb bélyegképek (#338): a meglévő thumbnail-provider
    # regisztrációját (a teljes könyvtár fotóit) használja fel útvonal-
    # feloldásra, saját aszinkron poollal renderel
    effect_thumb_provider = EffectThumbnailProvider(provider.photo_record)

    # fájlműveletek (#15): kontextusmenü/F2 híd + resync a műveletek után
    fileops_controller = FileOpsController()
    wire_fileops(fileops_controller, controller)

    # megjelenítési mód (#1575/#1576): a `Nézet ▸ Megjelenítési mód` almenü
    # állapota a KÉPERNYŐRE ható átalakítóig. A visszaadott átvezetőt névre
    # kötjük, hogy a kapcsolat a motor életében biztosan éljen.
    _display_mode_bridge = wire_display_mode(
        controller, edit_controller, edit_preview
    )

    # #367: az általános ConfirmDialog "Ne kérdezze újra" tára — a
    # controllerrel közös QSettings("PicasaPy", "PicasaPy")-ba ír
    confirm_settings = ConfirmSettingsBridge()

    # meglévő Picasa-telepítés átvétele (#146): felderítés + a kijelölt
    # mappák hozzáadása a meglévő addWatchedFolder úton
    discovery_controller = DiscoveryController(add_folder=controller.addWatchedFolder)

    # kép/mappa ablakra ejtése (#237): a kép mappája (vagy maga a mappa)
    # figyelt gyökér lesz — az ImportDropArea.qml hídja
    drop_import_controller = DropImportController(
        add_folder=controller.addWatchedFolder
    )

    # Mappakezelő fa-nézete (#231): a helyi fájlrendszer LUSTA, háttérszálas
    # listázása — a FolderManagerDialog.qml hídja
    folder_tree_controller = FolderTreeController()

    # A bal hasáb fa-mappanézete (#702): az INDEXELT mappák hierarchiája,
    # részfa-összegzett darabszámmal — a FolderHierarchyView.qml hídja.
    # Nem téveszthető össze a fenti `folder_tree_controller`-rel: az a
    # Mappakezelő dialógus fájlrendszer-böngészője, ez az indexé.
    folder_hierarchy_controller = FolderHierarchyController()

    def _reload_folder_hierarchy() -> None:
        """A fa-nézet mappalistájának újratöltése az indexből.

        Ugyanaz az esemény frissíti, mint az időrendet (`syncFinished`): a
        fa és a lapos lista UGYANABBÓL a `folders` táblából él, csak más
        alakban. A vezérlő a kinyitott ágakat megőrzi, tehát a szinkron nem
        csukja össze a felhasználó alatt a fát.
        """
        try:
            with open_index(data_dir / "index.db") as conn:
                folder_hierarchy_controller.setFolders(
                    [
                        {"path": path, "count": count}
                        for _name, path, count, *_rest in sorted_folder_rows(conn)
                    ]
                )
        except sqlite3.DatabaseError:
            # a hasáb lapos listája külön úton frissül — egy sérült index
            # miatt a fa maradjon a korábbi tartalmán, ne dőljön el a
            # `syncFinished` jelzés kiszolgálása
            logging.getLogger(__name__).exception(
                "a fa-mappanézet frissítése hibára futott"
            )

    controller.syncFinished.connect(_reload_folder_hierarchy)
    with timeline.phase("a bal hasáb mappafájának betöltése"):
        _reload_folder_hierarchy()

    # Időrend nézet (#24, Ctrl+5): a teljes könyvtár év/hónap szerinti
    # csoportosítása — a MEGLÉVŐ (AppControllerrel közös) thumbnail-
    # providert kapja, hogy a bélyegkép-URL-ek nála is regisztrálva
    # legyenek. Háttér-szinkron után a nézet friss adatot mutasson, ha
    # épp nyitva van — a TimelineView.qml a megnyitáskor is újratölt.
    timeline_controller = TimelineController(data_dir / "index.db", provider)
    controller.syncFinished.connect(timeline_controller.reload)
    # Duplikátum-kezelő (#287): a picasapy.dedup mag fölötti UI-híd —
    # a DedupDialog.qml-nek adja a csoportokat, a thumbnail-providernél
    # regisztrálja az érintett fotókat
    dedup_controller = DedupController(data_dir / "index.db", provider)
    # #1539: a feloldás után a forrás- ÉS a célmappa is célzott
    # újraolvasást kap — enélkül a „Duplikátumok" mappa képei eltűnnek
    wire_dedup(dedup_controller, controller)

    # #1066: a levelezés és a webexportálás vezérlője. Mindkettő a JELENLEG
    # látható fotókat kéri (`photo_source`), ahogy a saját docstringjük
    # előírja.
    #
    # ⚠️ Miért került ez külön jegybe: egyik sem jött létre SOHA, és egyik
    # sem volt regisztrálva — miközben az `OptionsTabEmail.qml` és a
    # `WebExportDialog.qml` hivatkozott rájuk, `typeof`-őr mögül. Az őr nem
    # engedte elszállni a felületet, viszont el is REJTETTE a hiányt: az
    # e-mail beállításfül elfogadta a módosítást, és némán nem mentette.
    def _lathato_fotok():
        return controller.photos.photos

    # #1671: a nyomtatás és az e-mail a KÉPTÁLCA tartalmán dolgozik, ha az
    # nem üres — a mappába exportálás (#455) mintájára. Enélkül kijelölés
    # nélkül némák maradtak, és a MÁS mappából tartott képet sosem látták.
    def _talca_fotok():
        return controller._tray_records()

    email_controller = EmailController(photo_source=_lathato_fotok, tray_source=_talca_fotok)
    web_export_controller = WebExportController(photo_source=_lathato_fotok)
    # #1472: a nyomtatás vezérlője — UGYANARRA a `photo_source`-ra épül
    # (a `printRows`/`renderPrintPreviewPdf` sorindexei a látható fotók
    # listájába mutatnak). Ez a vezérlő 213 sor kész kóddal és két
    # tesztfájllal SOHA nem jött létre a futó alkalmazásban, ezért a
    # Ctrl+P és a képtálca „Nyomtatás" gombja halott volt.
    print_controller = (
        PrintController(photo_source=_lathato_fotok, tray_source=_talca_fotok)
        if PrintController is not None
        else None
    )

    # Import forrásból (#23): külső mappa (kártya/fényképezőgép) képeinek
    # másolása/áthelyezése a könyvtárba — a thumbnail-providerrel adja az
    # előnézetet, sikeres import után az addWatchedFolder úton a cél-mappa
    # a könyvtár része lesz
    import_source_controller = ImportSourceController(
        provider,
        add_folder=controller.addWatchedFolder,
        index_path=data_dir / "index.db",
    )

    # #1653: a QML-MOTOR létrehozása külön szakasz. Az eddigi közös
    # mérőpont („a többi vezérlő létrehozása és regisztrálása") egyben
    # mérte a vezérlők konstruktorait, a `QQmlApplicationEngine()`-t és a
    # kontextus-tulajdonságok bekötését. A jegyben felsorolt windowsos
    # gyanúk közül a **Qt plugin-keresés** kizárólag a motor
    # létrehozásakor jelentkezne — összevont szakaszban láthatatlan.
    timeline.mark("a többi vezérlő létrehozása")
    engine = QQmlApplicationEngine()

    # Nyelvváltás futásidőben (#333): a régi fordító le, az új fel, majd a
    # QML-kötések újraszámolása. A `retranslate` a qsTr-es kötéseket frissíti;
    # a már megjelenített, C++/Python oldalon összeállított szövegek
    # (pl. státuszsor) a következő frissítésükkor követik.
    installed: list[QTranslator] = []

    def _apply_language() -> None:
        for old in installed:
            app.removeTranslator(old)
        installed.clear()
        new = _install_translator(app, controller.language)
        if new is not None:
            installed.append(new)
        engine.retranslate()

    controller.languageChanged.connect(_apply_language)

    engine.addImageProvider("thumbs", provider)
    engine.addImageProvider("editpreview", edit_preview)
    engine.addImageProvider("effectthumb", effect_thumb_provider)
    # #920: élő kollázs-előnézet. A szolgáltatót a vezérlő birtokolja
    # (lusta init), mert a kollázs állapota is ott él.
    engine.addImageProvider("collagepreview", controller.collage_preview_provider)
    engine.addImportPath(str(_APP_DIR / "qml"))
    # #1653: idáig tart a motor felállítása (konstruktor + kép-szolgáltatók
    # + import-útvonal); innentől már csak kontextus-bekötés következik.
    timeline.mark("QML-motor létrehozása és import-útvonalak")
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty("editController", edit_controller)
    engine.rootContext().setContextProperty(
        "fileOpsController", fileops_controller
    )
    engine.rootContext().setContextProperty("confirmSettings", confirm_settings)
    engine.rootContext().setContextProperty(
        "discoveryController", discovery_controller
    )
    engine.rootContext().setContextProperty(
        "dropImportController", drop_import_controller
    )
    engine.rootContext().setContextProperty(
        "folderTreeController", folder_tree_controller
    )
    engine.rootContext().setContextProperty(
        "folderHierarchyController", folder_hierarchy_controller
    )
    engine.rootContext().setContextProperty(
        "timelineController", timeline_controller
    )
    engine.rootContext().setContextProperty("dedupController", dedup_controller)
    # #1066 — az „E-Mail" beállításfül és a webexportálás párbeszéde
    engine.rootContext().setContextProperty("emailController", email_controller)
    engine.rootContext().setContextProperty(
        "webExportController", web_export_controller
    )
    # #1472: a nyomtatás-párbeszéd hídja (`PrintDialog.qml`)
    engine.rootContext().setContextProperty("printController", print_controller)
    # #368: adatbázis-áthelyezés — a MoveDatabaseDialog.qml hídja
    relocate_controller = RelocateController(
        data_dir / "index.db", cache_dir / "thumbs", config_dir
    )
    engine.rootContext().setContextProperty(
        "relocateController", relocate_controller
    )
    # #449: adatbázis-tömörítés — a CompactDatabaseDialog.qml hídja
    compact_controller = CompactController(data_dir / "index.db")
    engine.rootContext().setContextProperty("compactController", compact_controller)
    engine.rootContext().setContextProperty(
        "importSourceController", import_source_controller
    )
    # #147: a néző arc-keret overlay-jének csak-olvasás szintű hídja —
    # a faces=/Contacts2 közvetlenül a fotó .picasa.ini-jéből olvasva.
    # A helyi változóban tartás megakadályozza, hogy a Python GC a
    # context property mögül idő előtt eltüntesse a QObject-et.
    faces_helper = FacesHelper()
    engine.rootContext().setContextProperty("facesHelper", faces_helper)
    # #26 (3. lépcső): a SAJÁT arcfelismerés bekötése — a `FaceScanController`
    # (1–2. lépcső) eddig sehol nem volt elérve a QML-ből. A `faces_helper`
    # átadása a tömeges névadáshoz kell (`assignNameToFaces` a MEGLÉVŐ
    # `FacesHelper.addFace()` úton ír, ld. `face_scan_controller.py`).
    face_scan_controller = FaceScanController(
        data_dir / "index.db", faces_helper=faces_helper
    )
    engine.rootContext().setContextProperty(
        "faceScanController", face_scan_controller
    )
    # Verzió + build a fejlécben (jobb felső sarok): pontosan látsszon,
    # melyik commit fut — ld. version.version_string().
    engine.rootContext().setContextProperty("appVersion", version_string())
    # Indítóképernyő (#189): a Main.qml legfelső rétegén ülő SplashScreen
    # ebből a hídból kapja az állapotot, és a finish()-re magától eltűnik.
    engine.rootContext().setContextProperty("startupStatus", startup_status)
    timeline.mark("vezérlők regisztrálása a QML-kontextusban")
    with timeline.phase("QML betöltése (Main.qml)"):
        engine.load(str(_APP_DIR / "qml" / "Main.qml"))
    if not engine.rootObjects():
        return 1

    # #240: a betöltés csak az ablak ELSŐ kirajzolt képkockája UTÁN indul —
    # Windowson a korábbi singleShot(0) még az első frame előtt lefutott, a
    # finish() a splash-t láthatatlanul kifakította. A splash emellett
    # legalább _SPLASH_MIN_VISIBLE_MS-ig látszik (gyors betöltésnél is van
    # ideje megjelenni, a Picasa-élményhez hasonlóan).
    window = engine.rootObjects()[0]

    # #192: az utolsó ablakpozíció/-méret visszaállítása induláskor,
    # mentése az ablak zárásakor — a controllerrel közös QSettings-tárba
    wire_window_geometry(
        window, QSettings("PicasaPy", "PicasaPy"), virtual_desktop_rect(app)
    )
    splash_state = {"started": False}

    def _start_and_finish() -> None:
        first_frame_at = time.monotonic()
        # #1667/#1716: az induláskori indexkarbantartás NEM a kritikus
        # úton — az ablak már látszik, mire ez elindul. A takarítás (#58)
        # ELŐBB fut, mint a `_start_initial_scan` (`controller.start()` →
        # `rescan()`): az utóbbi indítja a háttér-szinkron szálat, ami
        # SAJÁT kapcsolattal írja ugyanazt az indexet. Amíg ez a sorrend
        # áll, a háttérszál a takarítás `commit()`-ja UTÁN keletkezik —
        # tehát a kettő SOHA nem ír egyszerre (ld. `_ottragadt_mappak_
        # takaritasa` docstringje a versenyhelyzet indoklásáért).
        with timeline.phase("ottragadt mappák takarítása (#58)"):
            _ottragadt_mappak_takaritasa(data_dir / "index.db", roots, QSettings())
        # a bal hasáb mappafája az első képkocka ELŐTT, még a takarítatlan
        # indexből töltődött fel (ld. lent) — a takarítás után azonnal
        # újratöltjük, hogy ne mutasson ottragadt mappát a következő
        # szinkron végéig.
        _reload_folder_hierarchy()
        with timeline.phase("exportcélok visszavétele (#1565)"):
            _exportcelok_visszavetele(data_dir / "index.db", QSettings())
        with timeline.phase("könyvtár betöltése (a vezérlő indítása)"):
            _start_initial_scan(
                startup_status, controller, storage_bootstrap.migration_notice
            )
        elapsed_ms = (time.monotonic() - first_frame_at) * 1000
        _jelentsd_az_idovonalat(
            timeline,
            lambda: _indexelt_kepszamok(data_dir),
            lambda: _takaritas_gyokerei(roots, QSettings()),
        )
        QTimer.singleShot(
            _remaining_splash_ms(elapsed_ms), startup_status.finish
        )

    def _on_first_frame() -> None:
        # a frameSwapped minden képkockánál jön — csak az első számít
        if splash_state["started"]:
            return
        splash_state["started"] = True
        timeline.mark("az ablak első kirajzolt képkockája")
        QTimer.singleShot(0, _start_and_finish)

    window.frameSwapped.connect(_on_first_frame)
    # tartalék: ha a frameSwapped nem jönne (pl. offscreen platform), az
    # indulás legkésőbb 1 s után akkor is elkezdődik
    QTimer.singleShot(1000, _on_first_frame)
    exit_code = app.exec()
    controller.shutdown()
    # #547: a szerkesztő háttér-renderét külön kell lezárni — az
    # `edit_controller` önálló objektum, nem része a `controller.shutdown()`
    # láncának. Előbb ÉRVÉNYTELENÍTÜNK (a worker így a végén sem emitál egy
    # közben megsemmisülő QObject-nek, ld. #430), utána rövid ideig várunk:
    # a perces rendert nem kell végigvárni, a daemon-szál emit nélkül fut ki.
    edit_controller.cancelPendingPreview()
    edit_controller.waitForBackgroundWorkers(2.0)
    return exit_code
