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
from .compact_controller import CompactController
from .relocate_controller import RelocateController
from .dedup_controller import DedupController
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
from .fileops_controller import FileOpsController
from .folder_hierarchy_controller import FolderHierarchyController
from .folder_tree_controller import FolderTreeController
from .import_source_controller import ImportSourceController
from .models import sorted_folder_rows
from .startup_status import StartupStatus
from .thumbnail_provider import ThumbnailProvider
from .timeline_controller import TimelineController
from .window_geometry import virtual_desktop_rect, wire_window_geometry

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


def _data_dir() -> Path:
    """Az index-SQLite (+ zárolófájl) mappája — ha a "Move Database"
    dialóguson (#368) keresztül egyszer már áthelyezésre került, az
    útvonal-felülbírálás (`data_location.py`) felülírja az XDG-
    alapértelmezést; ilyenkor a cache-cel EGYESÍTVE ugyanazt a mappát
    adja vissza, mint `_cache_dir()` (ld. ott)."""
    override = read_data_root(_config_dir())
    if override is not None:
        return override
    base = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(base) / "picasapy"


def _cache_dir() -> Path:
    """A thumbnail-lemezcache mappája — áthelyezés után (#368) a
    `_data_dir()`-rel EGYESÍTVE, hogy a Picasa-paritású "egy adatbázis-
    mappa" elv teljesüljön (a hívó ide illeszti a "thumbs" alkönyvtárat,
    ld. `run()`)."""
    override = read_data_root(_config_dir())
    if override is not None:
        return override
    base = os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
    return Path(base) / "picasapy"


def _config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(base) / "picasapy"


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
    if sys.platform != "win32":
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
    tool = shutil.which("gtk-update-icon-cache")
    if tool is None:
        return
    try:
        subprocess.run(
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
    áthelyezés/törlés után az érintett mappák célzott resyncje, hogy a rács
    (és a .picasa.ini-t követő szekció) azonnal a valós állapotot mutassa."""

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


def run(argv: list[str]) -> int:
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

    app = QGuiApplication(argv)
    app.setApplicationName("PicasaPy")
    app.setOrganizationName("PicasaPy")
    try:
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    except AttributeError:
        pass  # régebbi Qt: a paletta (Main.qml) így is világost kényszerít
    app.setDesktopFileName("picasapy")  # Wayland app_id → tálca-ikon
    app.setWindowIcon(QIcon(str(_window_icon_path())))
    _install_ui_font(app)
    _install_translator(app)

    # Indítóképernyő-híd (#189): korán jön létre, hogy az első állapot-
    # üzenetek is látsszanak; helyi változóban tartva (GC ellen).
    # #243: amíg az eredeti Picasa effekt-készlete nem teljes (#20, #190),
    # a splash a betöltés végén „félkész szoftver" figyelmeztetést és OK
    # gombot mutat — az effekt-paritás elérésekor ezt False-ra kell állítani.
    startup_status = StartupStatus(
        QCoreApplication.translate("startup", "Starting…"),
        requires_confirmation=True,
    )

    roots = _resolve_roots(argv)
    data_dir = _data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    # #449: hibanapló — a WARNING és súlyosabb üzenetek fájlba is mennek,
    # hogy adatbázis-hiba esetén legyen mit felajánlani megtekintésre
    error_log = install_error_log(data_dir) or error_log_path(data_dir)

    instance_lock = _acquire_instance_lock(data_dir)
    if instance_lock is None:
        print(
            "A PicasaPy már fut — egyszerre csak egy példány engedélyezett.",
            file=sys.stderr,
        )
        return 0
    _install_desktop_entry()

    # Ottragadt gyökerek takarítása (#58): az indexben csak a most figyelt
    # mappák maradhatnak — a korábbi futások (pl. régi parancssori argumentum)
    # mappái különben örökre a bal hasábban ragadnának.
    startup_status.report(
        QCoreApplication.translate("startup", "Preparing index…")
    )
    try:
        with open_index(data_dir / "index.db") as conn:
            prune_foreign_folders(conn, roots)
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
    cache_size = _thumbnail_cache_size(_screen_device_pixel_ratio(app))
    provider = ThumbnailProvider(
        ThumbnailCache(
            _cache_dir() / "thumbs",
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

    # Import forrásból (#23): külső mappa (kártya/fényképezőgép) képeinek
    # másolása/áthelyezése a könyvtárba — a thumbnail-providerrel adja az
    # előnézetet, sikeres import után az addWatchedFolder úton a cél-mappa
    # a könyvtár része lesz
    import_source_controller = ImportSourceController(
        provider,
        add_folder=controller.addWatchedFolder,
        index_path=data_dir / "index.db",
    )

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
    engine.addImportPath(str(_APP_DIR / "qml"))
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
    # #368: adatbázis-áthelyezés — a MoveDatabaseDialog.qml hídja
    relocate_controller = RelocateController(
        data_dir / "index.db", _cache_dir() / "thumbs", _config_dir()
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
        startup_status.report(
            QCoreApplication.translate("startup", "Scanning folders…")
        )
        controller.start()
        elapsed_ms = (time.monotonic() - first_frame_at) * 1000
        QTimer.singleShot(
            _remaining_splash_ms(elapsed_ms), startup_status.finish
        )

    def _on_first_frame() -> None:
        # a frameSwapped minden képkockánál jön — csak az első számít
        if splash_state["started"]:
            return
        splash_state["started"] = True
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
