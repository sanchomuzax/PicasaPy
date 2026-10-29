"""application platform az alkalmazásindítóhoz."""

from __future__ import annotations

# ruff: noqa: F821
# These function bodies are rebound into application.py's shared namespace.

import sys

from .application import _SPLASH_MIN_VISIBLE_MS

def _force_qml_dialogs(platform: str = sys.platform) -> bool:
    """Kényszerítsük-e a saját (nem natív) QML-dialógusokat.

    Linuxon/macOS-en igen: az app mindig világos, a rendszer sötét témájú
    választója kilógna (rögzített dizájn-döntés). Windowson viszont a natív
    mappaválasztó kell (#58): meghajtók, hálózati helyek és ékezetes mappák
    csak abból érhetők el rendesen — a QML-es tartalék a meghajtó szintje
    fölé nem tud lépni."""
    return platform != "win32"

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
    # #4964: a betű-regisztráció megváltoztatta a családlistát, a korábbi
    # lenyíló-gyorsítótár már nem stimmel
    clear_family_cache()
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
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PicasaPy.PicasaPy")
    except (AttributeError, OSError):
        # AttributeError: régi Windows-verzió vagy hiányzó API
        # OSError: nem admin-felhasználó vagy rendszer-hiba — csendben kimarad
        pass

def _remaining_splash_ms(elapsed_ms: float, minimum_ms: int = _SPLASH_MIN_VISIBLE_MS) -> int:
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
        text = template.format(source=migration_notice.source, target=migration_notice.target)
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
    from .quick_view import SUPPORTED_IMAGE_MIME_TYPES

    base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
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
        f"MimeType={';'.join(SUPPORTED_IMAGE_MIME_TYPES)};\n"
        "StartupWMClass=picasapy\n"
    )
    desktop_target = base / "applications" / "picasapy.desktop"
    try:
        if not icon_target.exists() or icon_target.read_bytes() != icon_source.read_bytes():
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
