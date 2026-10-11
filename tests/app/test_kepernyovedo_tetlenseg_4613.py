"""A képernyővédő indítása a gép tétlenségekor — a környezet-felismerés és a
saját automatikus indítási bejegyzés kezelése (#4613).

A modul tiszta Python: a környezetet, a fájlrendszer-gyökeret, a
folyamatlistát és az indítót mind paraméterként kapja, így a teszt a valódi
`~/.config`-hoz és a valódi `swayidle`-hoz nem nyúl.
"""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest

from picasapy.app import screensaver_idle as idle

_LABWC = {
    "XDG_CURRENT_DESKTOP": "labwc:wlroots",
    "WAYLAND_DISPLAY": "wayland-0",
    "XDG_SESSION_TYPE": "wayland",
}


def _which(found: dict[str, str]):
    return lambda name: found.get(name)


# --- környezet-felismerés -------------------------------------------------


def test_labwc_swayidle_mellett_tamogatott():
    support = idle.detect_support(_LABWC, "linux", _which({"swayidle": "/usr/bin/swayidle"}))
    assert support.supported is True
    assert support.reason == ""
    assert support.swayidle == "/usr/bin/swayidle"
    assert support.desktop == "labwc:wlroots"


@pytest.mark.parametrize("desktop", ["sway", "Wayfire", "river", "Hyprland", "niri"])
def test_mas_wlroots_alapu_asztal_is_tamogatott(desktop):
    env = {"XDG_CURRENT_DESKTOP": desktop, "WAYLAND_DISPLAY": "wayland-1"}
    support = idle.detect_support(env, "linux", _which({"swayidle": "/usr/bin/swayidle"}))
    assert support.supported is True


@pytest.mark.parametrize(
    "env",
    [
        {"XDG_CURRENT_DESKTOP": "GNOME", "WAYLAND_DISPLAY": "wayland-0"},
        {"XDG_CURRENT_DESKTOP": "KDE", "WAYLAND_DISPLAY": "wayland-0"},
        {"XDG_CURRENT_DESKTOP": "XFCE", "DISPLAY": ":0", "XDG_SESSION_TYPE": "x11"},
    ],
)
def test_gnome_kde_es_x11_nem_tamogatott_es_megnevezi_az_asztalt(env):
    support = idle.detect_support(env, "linux", _which({"swayidle": "/usr/bin/swayidle"}))
    assert support.supported is False
    assert support.reason == idle.REASON_DESKTOP
    assert support.desktop == env["XDG_CURRENT_DESKTOP"]


def test_wlroots_nev_x11_munkamenetben_nem_tamogatott():
    """A swayidle Wayland-protokollon figyel — X11 alatt a név önmagában kevés."""
    env = {"XDG_CURRENT_DESKTOP": "labwc", "DISPLAY": ":0", "XDG_SESSION_TYPE": "x11"}
    support = idle.detect_support(env, "linux", _which({"swayidle": "/usr/bin/swayidle"}))
    assert support.supported is False
    assert support.reason == idle.REASON_DESKTOP


def test_ismeretlen_asztal_x11_cimkét_kap():
    support = idle.detect_support({"DISPLAY": ":0"}, "linux", _which({}))
    assert support.supported is False
    assert support.desktop == "X11"


def test_hianyzo_swayidle_kulon_okot_ad():
    support = idle.detect_support(_LABWC, "linux", _which({}))
    assert support.supported is False
    assert support.reason == idle.REASON_NO_SWAYIDLE


@pytest.mark.parametrize("platform", ["win32", "darwin"])
def test_nem_linuxon_nem_tamogatott(platform):
    support = idle.detect_support(_LABWC, platform, _which({"swayidle": "/usr/bin/swayidle"}))
    assert support.supported is False
    assert support.reason == idle.REASON_NOT_LINUX


# --- az indítandó parancs -------------------------------------------------


def test_parancs_a_repo_inditojat_a_futo_ertelmezovel_hivja(tmp_path):
    launcher = tmp_path / "picasapy"
    launcher.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    command = idle.screensaver_command(
        launcher=launcher, which=_which({"picasapy": "/usr/bin/picasapy"}),
        executable="/venv/bin/python3",
    )
    assert command == ["/venv/bin/python3", str(launcher), "--screensaver"]


def test_parancs_telepitett_belepesi_pontra_esik_vissza(tmp_path):
    command = idle.screensaver_command(
        launcher=tmp_path / "nincs", which=_which({"picasapy": "/usr/bin/picasapy"}),
        executable="/venv/bin/python3",
    )
    assert command == ["/usr/bin/picasapy", "--screensaver"]


def test_parancs_vegso_tartaleka_a_modul(tmp_path):
    command = idle.screensaver_command(
        launcher=tmp_path / "nincs", which=_which({}), executable="/venv/bin/python3",
    )
    assert command == ["/venv/bin/python3", "-m", "picasapy.app", "--screensaver"]


def test_swayidle_parancssor_percet_masodpercre_valt_es_var():
    argv = idle.swayidle_argv("/usr/bin/swayidle", 10, ["/usr/bin/picasapy", "--screensaver"])
    assert argv == [
        "/usr/bin/swayidle", "-w", "timeout", "600", "/usr/bin/picasapy --screensaver",
    ]


def test_swayidle_parancs_szokozos_utat_shell_szerint_idez():
    argv = idle.swayidle_argv("/usr/bin/swayidle", 1, ["/a b/picasapy", "--screensaver"])
    assert shlex.split(argv[-1]) == ["/a b/picasapy", "--screensaver"]


@pytest.mark.parametrize("minutes", [0, -3, idle.MAX_MINUTES + 1])
def test_ervenytelen_perc_hibat_ad(minutes):
    with pytest.raises(ValueError):
        idle.swayidle_argv("/usr/bin/swayidle", minutes, ["x"])


# --- az XDG Exec-idézés ---------------------------------------------------


def _exec_unquote(value: str) -> list[str]:
    """Az XDG Desktop Entry Exec-kulcsának visszafejtése (a spec szerint):
    előbb a karakterlánc-szintű `\\\\` → `\\`, aztán az idézőjeles argumentumok
    `\\"`, `` \\` ``, `\\$`, `\\\\` feloldása, végül `%%` → `%`."""
    string_level = value.replace("\\\\", "\\")
    args, current, quoted, i, started = [], [], False, 0, False
    while i < len(string_level):
        ch = string_level[i]
        if quoted:
            if ch == "\\" and i + 1 < len(string_level) and string_level[i + 1] in '"`$\\':
                current.append(string_level[i + 1])
                i += 2
                continue
            if ch == '"':
                quoted = False
            else:
                current.append(ch)
        elif ch == '"':
            quoted, started = True, True
        elif ch == " ":
            if current or started:
                args.append("".join(current).replace("%%", "%"))
            current, started = [], False
        else:
            current.append(ch)
        i += 1
    if current or started:
        args.append("".join(current).replace("%%", "%"))
    return args


@pytest.mark.parametrize(
    "argv",
    [
        ["/usr/bin/swayidle", "-w", "timeout", "600", "/usr/bin/picasapy --screensaver"],
        ["/x/swayidle", "timeout", "60", "'/a b/pic$asa%py' --screensaver"],
        ["/x/swayidle", 'say "hi" `x` \\ back'],
    ],
)
def test_exec_idezes_visszafejtve_az_eredeti_argumentumokat_adja(argv):
    assert _exec_unquote(idle.xdg_exec_line(argv)) == argv


@pytest.mark.parametrize("ctrl", ["\n", "\r", "\t", "\x01", "\x1f", "\x7f"])
def test_exec_idezes_vezerlokaraktert_elutasit(ctrl):
    with pytest.raises(idle.IdleIntegrationError):
        idle.xdg_exec_line(["/usr/bin/swayidle", f"a{ctrl}Exec=rm -rf ~"])


# --- az automatikus indítási bejegyzés ------------------------------------


class _Procs:
    """Hamis folyamattábla és leállító — a valódi /proc helyett."""

    def __init__(self, rows):
        self.rows = list(rows)
        self.killed: list[int] = []
        self.spawned: list[list[str]] = []
        self.environs: dict[int, dict[str, str]] = {}
        self.spawn_error: OSError | None = None

    def environ(self, pid):
        return self.environs.get(pid, {"WAYLAND_DISPLAY": "wayland-0"})

    def list(self):
        return list(self.rows)

    def kill(self, pid):
        self.killed.append(pid)
        self.rows = [row for row in self.rows if row[0] != pid]

    def spawn(self, argv):
        if self.spawn_error is not None:
            raise self.spawn_error
        self.spawned.append(list(argv))
        self.rows.append((9999, list(argv)))


def _integration(tmp_path, procs, env=None, which=None):
    return idle.IdleIntegration(
        env=_LABWC if env is None else env,
        platform="linux",
        config_home=tmp_path / "config",
        command=["/usr/bin/picasapy", "--screensaver"],
        which=which or _which({"swayidle": "/usr/bin/swayidle"}),
        processes=procs.list,
        kill=procs.kill,
        spawn=procs.spawn,
        environ=procs.environ,
    )


def test_bekapcsolas_megirja_a_sajat_bejegyzest_es_azonnal_elinditja(tmp_path):
    procs = _Procs([])
    integration = _integration(tmp_path, procs)
    assert integration.is_enabled() is False

    integration.enable(5)

    path = tmp_path / "config" / "autostart" / idle.AUTOSTART_NAME
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert f"{idle.MARKER_KEY}=true" in text
    exec_line = next(line for line in text.splitlines() if line.startswith("Exec="))
    assert _exec_unquote(exec_line.removeprefix("Exec=")) == [
        "/usr/bin/swayidle", "-w", "timeout", "300", "/usr/bin/picasapy --screensaver",
    ]
    assert procs.spawned == [[
        "/usr/bin/swayidle", "-w", "timeout", "300", "/usr/bin/picasapy --screensaver",
    ]]
    assert integration.is_enabled() is True
    assert integration.configured_minutes() == 5


def test_ujra_bekapcsolas_a_regi_sajat_figyelot_leallitja(tmp_path):
    regi = ["/usr/bin/swayidle", "-w", "timeout", "600", "/usr/bin/picasapy --screensaver"]
    procs = _Procs([(41, regi)])
    integration = _integration(tmp_path, procs)

    integration.enable(2)

    assert procs.killed == [41]
    assert len(procs.spawned) == 1


def test_kikapcsolas_torli_a_sajat_bejegyzest_es_leallitja_a_sajat_figyelot(tmp_path):
    procs = _Procs([])
    integration = _integration(tmp_path, procs)
    integration.enable(3)
    idegen = (77, ["/usr/bin/swayidle", "-w", "timeout", "300", "wlopm --off '*'"])
    procs.rows.append(idegen)

    integration.disable()

    assert not (tmp_path / "config" / "autostart" / idle.AUTOSTART_NAME).exists()
    assert procs.killed == [9999], "csak a saját figyelőt szabad leállítani"
    assert idegen in procs.rows
    assert integration.is_enabled() is False


def test_idegen_azonos_nevu_bejegyzest_nem_tekint_sajatnak_es_nem_torol(tmp_path):
    path = tmp_path / "config" / "autostart" / idle.AUTOSTART_NAME
    path.parent.mkdir(parents=True)
    path.write_text("[Desktop Entry]\nType=Application\nExec=valami\n", encoding="utf-8")
    integration = _integration(tmp_path, _Procs([]))

    assert integration.is_enabled() is False
    integration.disable()
    assert path.read_text(encoding="utf-8").endswith("Exec=valami\n")
    with pytest.raises(idle.IdleIntegrationError):
        integration.enable(5)
    assert path.read_text(encoding="utf-8").endswith("Exec=valami\n")


def test_nem_tamogatott_kornyezetben_a_bekapcsolas_nem_ir_semmit(tmp_path):
    procs = _Procs([])
    integration = _integration(
        tmp_path, procs, env={"XDG_CURRENT_DESKTOP": "GNOME", "WAYLAND_DISPLAY": "w"}
    )
    with pytest.raises(idle.IdleIntegrationError):
        integration.enable(5)
    assert not (tmp_path / "config").exists()
    assert procs.spawned == []


def test_sajat_folyamat_felismerese():
    assert idle.is_own_idle_process(
        ["/usr/bin/swayidle", "-w", "timeout", "60", "/h/PicasaPy/picasapy --screensaver"]
    )
    assert idle.is_own_idle_process(
        ["swayidle", "timeout", "60", "/v/python3 -m picasapy.app --screensaver"]
    )
    assert not idle.is_own_idle_process(["/usr/bin/swayidle", "timeout", "60", "wlopm --off"])
    assert not idle.is_own_idle_process(["/usr/bin/picasapy", "--screensaver"])
    assert not idle.is_own_idle_process([])


def test_valodi_proc_olvaso_hamis_gyokerrel(tmp_path):
    (tmp_path / "12").mkdir()
    (tmp_path / "12" / "cmdline").write_bytes(b"/usr/bin/swayidle\0-w\0timeout\0")
    (tmp_path / "self").mkdir()
    (tmp_path / "13").mkdir()  # cmdline nélkül (közben kilépett) — kihagyja
    assert list(idle.list_processes(tmp_path)) == [
        (12, ["/usr/bin/swayidle", "-w", "timeout"])
    ]


def test_ures_bejegyzes_perc_nelkul_none(tmp_path):
    assert _integration(tmp_path, _Procs([])).configured_minutes() is None


def test_for_session_a_valodi_kornyezetbol_epul(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    integration = idle.IdleIntegration.for_session()
    assert integration.autostart_path == (
        tmp_path / "cfg" / "autostart" / idle.AUTOSTART_NAME
    )
    assert integration.command[-1] == "--screensaver"
    assert Path(integration.command[0]).name


def test_valodi_indito_levalasztva_futtat_es_nem_hagy_zombit(tmp_path):
    """A figyelő a mi folyamatunktól leválasztva fut (nem a mi gyermekünk,
    tehát zombiként sem maradhat ránk), és szál sem indul hozzá (#988)."""
    import os
    import sys
    import threading
    import time

    jel = tmp_path / "szulo.txt"
    szalak_elotte = threading.active_count()
    idle._spawn([
        sys.executable, "-c",
        f"import os, pathlib; pathlib.Path({str(jel)!r}).write_text(str(os.getppid()))",
    ])
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and not (jel.exists() and jel.read_text()):
        time.sleep(0.05)

    assert jel.read_text(), "a figyelő nem indult el"
    assert int(jel.read_text()) != os.getpid()
    assert threading.active_count() == szalak_elotte


def test_vezerlokaraktert_tartalmazo_parancs_nem_ir_fajlt(tmp_path):
    procs = _Procs([])
    integration = idle.IdleIntegration(
        env=_LABWC, platform="linux", config_home=tmp_path / "config",
        command=["/usr/bin/picasapy\nExec=evil", "--screensaver"],
        which=_which({"swayidle": "/usr/bin/swayidle"}),
        processes=procs.list, kill=procs.kill, spawn=procs.spawn,
        environ=procs.environ,
    )
    with pytest.raises(idle.IdleIntegrationError):
        integration.enable(5)
    assert not (tmp_path / "config").exists()
    assert procs.spawned == []


def test_indito_hiba_eseten_a_bejegyzes_es_a_tmp_sincs_meg(tmp_path):
    procs = _Procs([])
    procs.spawn_error = OSError("nincs végrehajtható")
    integration = _integration(tmp_path, procs)

    with pytest.raises(OSError):
        integration.enable(5)

    autostart = tmp_path / "config" / "autostart"
    assert not (autostart / idle.AUTOSTART_NAME).exists()
    assert not list(autostart.glob("*.tmp"))
    assert integration.is_enabled() is False


def test_irasi_hiba_eseten_a_tmp_takaritva(tmp_path, monkeypatch):
    integration = _integration(tmp_path, _Procs([]))

    def _hiba(*_args, **_kwargs):
        raise OSError("tele a lemez")

    monkeypatch.setattr(idle.os, "replace", _hiba)
    with pytest.raises(OSError):
        integration.enable(5)
    assert not list((tmp_path / "config" / "autostart").glob("*"))


def test_csak_a_sajat_wayland_munkamenet_figyeloje_all_le(tmp_path):
    figyelo = ["/usr/bin/swayidle", "-w", "timeout", "600", "/usr/bin/picasapy --screensaver"]
    procs = _Procs([(41, figyelo), (42, figyelo), (43, figyelo)])
    procs.environs = {
        41: {"WAYLAND_DISPLAY": "wayland-0"},
        42: {"WAYLAND_DISPLAY": "wayland-headless"},
        # 43: olvasási hiba (nincs bejegyzés → alapértelmezés felülírva None-nal)
    }
    base = procs.environ
    procs.environ = lambda pid: None if pid == 43 else base(pid)
    integration = _integration(tmp_path, procs)

    integration.enable(2)

    assert procs.killed == [41]


def test_autostartot_futtato_asztalok_jelolese():
    which = _which({"swayidle": "/usr/bin/swayidle"})
    for desktop, expected in [("labwc:wlroots", True), ("Wayfire", True),
                              ("sway", False), ("river", False),
                              ("Hyprland", False), ("niri", False)]:
        env = {"XDG_CURRENT_DESKTOP": desktop, "WAYLAND_DISPLAY": "wayland-0"}
        support = idle.detect_support(env, "linux", which)
        assert support.supported is True
        assert support.autostart is expected, desktop
