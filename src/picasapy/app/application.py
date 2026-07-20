"""Alkalmazás-bootstrap: Qt, fordítások, adat-útvonalak, QML-betöltés.

Könyvtár-gyökerek: parancssori argumentumok, vagy a Picasa-paritású
~/.config/picasapy/WatchedFolders.txt (soronként egy abszolút útvonal).
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import shutil
import subprocess
import sys

from PySide6.QtCore import QLocale, QLockFile, Qt, QTranslator
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from picasapy.index import open_index, prune_foreign_folders
from picasapy.scanner import (
    WATCHED_FOLDERS_NAME,
    find_watched_folders_file,
    read_watched_folders,
)
from picasapy.thumbs import ThumbnailCache
from picasapy.version import version_string
from .controller import AppController
from .edit_controller import EditController
from .edit_preview import EditPreviewProvider
from .faces_helper import FacesHelper
from .fileops_controller import FileOpsController
from .thumbnail_provider import ThumbnailProvider

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
    base = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(base) / "picasapy"


def _cache_dir() -> Path:
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


def _resolve_roots(argv: list[str]) -> tuple[str, ...]:
    if len(argv) > 1:
        return tuple(argv[1:])
    return read_watched_folders(_watched_folders_path())


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


def _install_translator(app: QGuiApplication) -> QTranslator | None:
    language = os.environ.get("PICASAPY_LANG") or QLocale.system().name()
    translator = QTranslator(app)
    if translator.load(f"picasapy_{language.split('_')[0]}", str(_I18N_DIR)):
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

    app = QGuiApplication(argv)
    app.setApplicationName("PicasaPy")
    app.setOrganizationName("PicasaPy")
    try:
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    except AttributeError:
        pass  # régebbi Qt: a paletta (Main.qml) így is világost kényszerít
    app.setDesktopFileName("picasapy")  # Wayland app_id → tálca-ikon
    app.setWindowIcon(QIcon(str(_APP_DIR / "assets" / "icon.png")))
    _install_translator(app)

    roots = _resolve_roots(argv)
    data_dir = _data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

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
    with open_index(data_dir / "index.db") as conn:
        prune_foreign_folders(conn, roots)

    # #83: a cache-méretet a képernyő DPR-jéhez igazítjuk, hogy a rács
    # legnagyobb fokozata (256px) se legyen homályos HiDPI kijelzőn.
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
    )

    # szerkesztő-előnézet (#19): a provider a filters= láncot alkalmazva
    # rendereli a képet; a hidat az EditController adja a QML-nek
    edit_preview = EditPreviewProvider()
    edit_controller = EditController(edit_preview)

    # fájlműveletek (#15): kontextusmenü/F2 híd + resync a műveletek után
    fileops_controller = FileOpsController()
    wire_fileops(fileops_controller, controller)

    engine = QQmlApplicationEngine()
    engine.addImageProvider("thumbs", provider)
    engine.addImageProvider("editpreview", edit_preview)
    engine.addImportPath(str(_APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty("editController", edit_controller)
    engine.rootContext().setContextProperty(
        "fileOpsController", fileops_controller
    )
    # #147: a néző arc-keret overlay-jének csak-olvasás szintű hídja —
    # a faces=/Contacts2 közvetlenül a fotó .picasa.ini-jéből olvasva.
    # A helyi változóban tartás megakadályozza, hogy a Python GC a
    # context property mögül idő előtt eltüntesse a QObject-et.
    faces_helper = FacesHelper()
    engine.rootContext().setContextProperty("facesHelper", faces_helper)
    # Verzió + build a fejlécben (jobb felső sarok): pontosan látsszon,
    # melyik commit fut — ld. version.version_string().
    engine.rootContext().setContextProperty("appVersion", version_string())
    engine.load(str(_APP_DIR / "qml" / "Main.qml"))
    if not engine.rootObjects():
        return 1
    controller.start()
    exit_code = app.exec()
    controller.shutdown()
    return exit_code
