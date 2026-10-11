"""A képernyővédő indítása a gép tétlenségekor — asztali integráció (#4613).

Az eredeti Picasa képernyővédő-kiegészítőt telepített, amelyet a Windows
indított tétlenségkor (`picasa-create-features.md` 35.3: „külön integrációs
feladat”). Linuxon nincs ilyen közös felület, ezért itt a tétlenség-figyelő
(`swayidle`) kap egy sort, amely tétlenségkor a `picasapy --screensaver`
belépési pontot hívja.

**Mi támogatott.** A wlroots-alapú Wayland-asztalok (labwc — a Raspberry Pi
OS alapértelmezése —, sway, Wayfire, river, Hyprland, niri), ha a `swayidle`
telepítve van. A GNOME és a KDE saját, zárt képernyővédő-kezelést használ,
az X11-asztalok pedig mind mást; ezekre nincs megbízható út, ezért a
felület érthető okkal „nem támogatott”-at mond, és nem ír semmit.

**Mit ír, és mit nem.** Egyetlen fájlt, a felhasználó saját
`$XDG_CONFIG_HOME/autostart/picasapy-screensaver.desktop` bejegyzését, a
`MARKER_KEY` jelölővel. Kikapcsoláskor csak a jelölős fájlt törli, és csak
azt a `swayidle` folyamatot állítja le, amelynek parancssora a PicasaPy
képernyővédőjét indítja — a rendszer saját képernyő-kikapcsoló
`swayidle`-jához nem nyúl. Bekapcsoláskor a figyelő azonnal el is indul,
hogy ne kelljen újra bejelentkezni.
"""

from __future__ import annotations

import os
import shlex
import shutil
import signal
import subprocess
import sys
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

SCREENSAVER_FLAG = "--screensaver"
AUTOSTART_NAME = "picasapy-screensaver.desktop"
MARKER_KEY = "X-PicasaPy-Screensaver"
DEFAULT_MINUTES = 10
MIN_MINUTES = 1
MAX_MINUTES = 120

REASON_NOT_LINUX = "not-linux"
REASON_DESKTOP = "desktop"
REASON_NO_SWAYIDLE = "no-swayidle"

#: Az `ext-idle-notify` protokollt adó, `swayidle`-lal mérten működő
#: asztalok `XDG_CURRENT_DESKTOP`-nevei (kisbetűsen).
WLROOTS_DESKTOPS = frozenset(
    {"labwc", "sway", "wayfire", "river", "hyprland", "niri", "wlroots"}
)

#: Azok az asztalok, amelyek az `~/.config/autostart` bejegyzéseit magától
#: elindítják; a többi wlroots-asztal (sway, river, Hyprland, niri) alapból nem.
AUTOSTART_DESKTOPS = frozenset({"labwc", "wayfire"})

# Az XDG Desktop Entry spec szerint idézendő karakterek az Exec-kulcsban.
_EXEC_RESERVED = set(" \t\n\"'\\><~|&;$*?#()`")


class IdleIntegrationError(RuntimeError):
    """A tétlenségi indítás nem állítható be (nem támogatott, idegen fájl)."""


@dataclass(frozen=True)
class IdleSupport:
    """A jelen munkamenet támogatottsága, a felületnek kiírható okkal."""

    supported: bool
    reason: str
    desktop: str
    swayidle: str = ""
    #: Az asztal az autostart-bejegyzést újrabejelentkezéskor magától indítja?
    autostart: bool = True


def detect_support(
    env: Mapping[str, str], platform: str, which: Callable[[str], str | None]
) -> IdleSupport:
    """Eldönti, beállítható-e itt a tétlenségi indítás."""
    if not platform.startswith("linux"):
        return IdleSupport(False, REASON_NOT_LINUX, "")
    desktop = (
        env.get("XDG_CURRENT_DESKTOP")
        or env.get("XDG_SESSION_DESKTOP")
        or env.get("DESKTOP_SESSION")
        or ""
    )
    wayland = bool(env.get("WAYLAND_DISPLAY")) or (
        env.get("XDG_SESSION_TYPE", "").lower() == "wayland"
    )
    label = desktop or ("Wayland" if wayland else "X11" if env.get("DISPLAY") else "")
    names = {part.strip().lower() for part in desktop.split(":") if part.strip()}
    if not wayland or not names & WLROOTS_DESKTOPS:
        return IdleSupport(False, REASON_DESKTOP, label)
    swayidle = which("swayidle")
    if not swayidle:
        return IdleSupport(False, REASON_NO_SWAYIDLE, label)
    return IdleSupport(
        True, "", label, swayidle, autostart=bool(names & AUTOSTART_DESKTOPS)
    )


def screensaver_command(
    *, launcher: Path | None, which: Callable[[str], str | None], executable: str
) -> list[str]:
    """A tétlenségkor futtatandó `--screensaver` parancs.

    A repóból futtatott példány a saját indítóját a FUTÓ értelmezővel hívja
    (különben a `#!/usr/bin/env python3` egy PySide6 nélküli rendszer-
    Pythont találhatna); a telepített példány a `picasapy` parancsot.
    """
    if launcher is not None and launcher.is_file():
        return [executable, str(launcher), SCREENSAVER_FLAG]
    installed = which("picasapy")
    if installed:
        return [installed, SCREENSAVER_FLAG]
    return [executable, "-m", "picasapy.app", SCREENSAVER_FLAG]


def swayidle_argv(swayidle: str, minutes: int, command: list[str]) -> list[str]:
    """`swayidle -w timeout <mp> '<parancs>'` — a `-w` megvárja a vetítés végét."""
    if not MIN_MINUTES <= int(minutes) <= MAX_MINUTES:
        raise ValueError(f"érvénytelen perc: {minutes}")
    return [swayidle, "-w", "timeout", str(int(minutes) * 60), shlex.join(command)]


def _exec_quote(arg: str) -> str:
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in arg):
        raise IdleIntegrationError("control-character")
    if arg and not _EXEC_RESERVED.intersection(arg):
        return arg.replace("%", "%%")
    inner = "".join("\\" + ch if ch in '"`$\\' else ch for ch in arg)
    return '"' + inner.replace("%", "%%") + '"'


def xdg_exec_line(argv: Iterable[str]) -> str:
    """Az Exec-kulcs értéke: argumentum-idézés, majd karakterlánc-escape."""
    quoted = " ".join(_exec_quote(arg) for arg in argv)
    return quoted.replace("\\", "\\\\")


def autostart_text(argv: list[str], minutes: int) -> str:
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=PicasaPy Screensaver\n"
        "Comment=Starts the PicasaPy screensaver when the computer is idle\n"
        f"Exec={xdg_exec_line(argv)}\n"
        "Terminal=false\n"
        "NoDisplay=true\n"
        "X-GNOME-Autostart-enabled=true\n"
        f"X-PicasaPy-Idle-Minutes={int(minutes)}\n"
        f"{MARKER_KEY}=true\n"
    )


def is_own_idle_process(args: list[str]) -> bool:
    """Egy `swayidle`, amely a PicasaPy képernyővédőjét indítja?"""
    if not args or Path(args[0]).name != "swayidle":
        return False
    return any(
        SCREENSAVER_FLAG in arg and "picasapy" in arg.lower() for arg in args[1:]
    )


def list_processes(proc_root: Path = Path("/proc")) -> Iterator[tuple[int, list[str]]]:
    """(pid, argv) párok a /proc-ból; a közben kilépett folyamatot kihagyja."""
    try:
        entries = sorted(proc_root.iterdir(), key=lambda p: p.name)
    except OSError:
        return
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        args = [part.decode("utf-8", "replace") for part in raw.split(b"\0") if part]
        if args:
            yield int(entry.name), args


def process_environ(pid: int, proc_root: Path = Path("/proc")) -> dict[str, str] | None:
    """Egy folyamat környezete a /proc-ból; olvasási hibánál `None`."""
    try:
        raw = (proc_root / str(pid) / "environ").read_bytes()
    except OSError:
        return None
    result: dict[str, str] = {}
    for part in raw.split(b"\0"):
        key, sep, value = part.partition(b"=")
        if sep and key:
            result[key.decode("utf-8", "replace")] = value.decode("utf-8", "replace")
    return result


def _terminate(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass


def _spawn(argv: list[str]) -> None:
    """A figyelő indítása kettős elágazással: a rövid életű `sh` háttérbe
    teszi a parancsot és azonnal kilép, így a figyelőt az init örökli —
    a PicasaPy-nak nem kell rá várnia, és zombi sem marad utána."""
    shell = subprocess.Popen(  # noqa: S603 — a parancs a saját, ellenőrzött listánk
        ["/bin/sh", "-c", 'exec "$@" >/dev/null 2>&1 </dev/null &', "sh", *argv],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    try:
        shell.wait(timeout=5)
    except subprocess.TimeoutExpired as exc:
        shell.kill()
        raise OSError("a képernyővédő-figyelő indítása nem fejeződött be") from exc


def _repo_launcher() -> Path:
    return Path(__file__).resolve().parents[3] / "picasapy"


class IdleIntegration:
    """A saját automatikus indítási bejegyzés és figyelő kezelése."""

    def __init__(
        self,
        *,
        env: Mapping[str, str],
        platform: str,
        config_home: Path,
        command: list[str],
        which: Callable[[str], str | None] = shutil.which,
        processes: Callable[[], Iterable[tuple[int, list[str]]]] = list_processes,
        kill: Callable[[int], None] = _terminate,
        spawn: Callable[[list[str]], None] = _spawn,
        environ: Callable[[int], Mapping[str, str] | None] = process_environ,
    ) -> None:
        self._env = dict(env)
        self._platform = platform
        self._config_home = Path(config_home)
        self._command = list(command)
        self._which = which
        self._processes = processes
        self._kill = kill
        self._spawn = spawn
        self._environ = environ

    @classmethod
    def for_session(cls) -> IdleIntegration:
        env = dict(os.environ)
        config_home = Path(env.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        command = screensaver_command(
            launcher=_repo_launcher(), which=shutil.which, executable=sys.executable
        )
        return cls(env=env, platform=sys.platform, config_home=config_home, command=command)

    @property
    def command(self) -> list[str]:
        return list(self._command)

    @property
    def autostart_path(self) -> Path:
        return self._config_home / "autostart" / AUTOSTART_NAME

    def support(self) -> IdleSupport:
        return detect_support(self._env, self._platform, self._which)

    def _own_entry_text(self) -> str | None:
        try:
            text = self.autostart_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
        return text if f"\n{MARKER_KEY}=true" in f"\n{text}" else None

    def is_enabled(self) -> bool:
        return self._own_entry_text() is not None

    def configured_minutes(self) -> int | None:
        text = self._own_entry_text()
        if text is None:
            return None
        for line in text.splitlines():
            if line.startswith("X-PicasaPy-Idle-Minutes="):
                try:
                    return int(line.split("=", 1)[1])
                except ValueError:
                    return None
        return None

    def _same_session(self, pid: int) -> bool:
        """A folyamat ugyanabban a Wayland-munkamenetben fut, mint mi?

        Más munkamenet (másik bejelentkezett felhasználói session, headless
        compositor) figyelőjét nem szabad leállítani; olvasási hibánál sem.
        """
        own = self._env.get("WAYLAND_DISPLAY", "")
        if not own:
            return False
        environ = self._environ(pid)
        return environ is not None and environ.get("WAYLAND_DISPLAY") == own

    def _stop_own_watchers(self) -> None:
        for pid, args in list(self._processes()):
            if is_own_idle_process(args) and self._same_session(pid):
                self._kill(pid)

    def enable(self, minutes: int) -> None:
        support = self.support()
        if not support.supported:
            raise IdleIntegrationError(support.reason)
        argv = swayidle_argv(support.swayidle, minutes, self._command)
        path = self.autostart_path
        if path.exists() and not self.is_enabled():
            raise IdleIntegrationError("foreign-entry")
        text = autostart_text(argv, minutes)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        try:
            tmp.write_text(text, encoding="utf-8")
            os.replace(tmp, path)
        finally:
            tmp.unlink(missing_ok=True)
        try:
            self._stop_own_watchers()
            self._spawn(argv)
        except OSError:
            # félsiker nincs: figyelő nélkül ne maradjon bejegyzés, amely
            # a felület szerint „be van kapcsolva”
            path.unlink(missing_ok=True)
            raise

    def disable(self) -> None:
        if self.is_enabled():
            self.autostart_path.unlink(missing_ok=True)
        self._stop_own_watchers()
