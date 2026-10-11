"""A képernyővédő-beállítás „Indítás, ha a gép ennyi ideig tétlen” sora (#4613).

A valódi főablakon, valódi kattintással. A tétlenségi integráció hamis
folyamattáblát és ideiglenes `XDG_CONFIG_HOME`-ot kap, így a teszt a valódi
`~/.config/autostart`-hoz és a valódi `swayidle`-hoz nem nyúl.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtTest import QTest
from support.qt_wait import varj_feltetelre

from picasapy.app import screensaver_idle as idle

_LABWC = {"XDG_CURRENT_DESKTOP": "labwc:wlroots", "WAYLAND_DISPLAY": "wayland-0"}


class _Procs:
    def __init__(self):
        self.rows: list[tuple[int, list[str]]] = []
        self.spawned: list[list[str]] = []
        self.killed: list[int] = []
        self.spawn_error: OSError | None = None

    def list(self):
        return list(self.rows)

    def kill(self, pid):
        self.killed.append(pid)
        self.rows = [row for row in self.rows if row[0] != pid]

    def spawn(self, argv):
        if self.spawn_error is not None:
            raise self.spawn_error
        self.spawned.append(list(argv))
        self.rows.append((500 + len(self.spawned), list(argv)))


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _click(window, item, qt_app):
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        center.toPoint(),
    )
    qt_app.processEvents()


def _install(controller, tmp_path, env):
    procs = _Procs()
    controller._screensaver_idle = idle.IdleIntegration(
        env=env,
        platform="linux",
        config_home=tmp_path / "cfg",
        command=["/usr/bin/picasapy", "--screensaver"],
        which=lambda name: "/usr/bin/swayidle" if name == "swayidle" else None,
        processes=procs.list,
        kill=procs.kill,
        spawn=procs.spawn,
        environ=lambda _pid: {"WAYLAND_DISPLAY": "wayland-0"},
    )
    controller.screensaverIdleChanged.emit()
    return procs


def _open_dialog(window, qt_app):
    QMetaObject.invokeMethod(
        _child(window, "menuToolsScreensaver"), "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    assert varj_feltetelre(
        qt_app,
        lambda: _child(window, "screensaverDialog").property("visible") is True,
        3.0,
    )
    return _child(window, "screensaverDialog")


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_kattintasra_bekapcsol_percet_allit_es_kikapcsol(
    qml_app, qt_app, tmp_path, height_delta
):
    window, controller, _engine = qml_app
    window.resize(window.width(), window.height() + height_delta)
    procs = _install(controller, tmp_path, _LABWC)
    dialog = _open_dialog(window, qt_app)
    check = _child(dialog, "screensaverIdleCheck")
    spin = _child(dialog, "screensaverIdleMinutes")
    message = _child(dialog, "screensaverIdleMessage")
    autostart = tmp_path / "cfg" / "autostart" / idle.AUTOSTART_NAME

    assert check.property("enabled") is True
    assert check.property("checked") is False
    assert message.property("visible") is False
    assert spin.property("value") == idle.DEFAULT_MINUTES

    _click(window, check, qt_app)
    assert check.property("checked") is True
    assert autostart.is_file()
    assert procs.spawned[-1][:4] == ["/usr/bin/swayidle", "-w", "timeout", "600"]

    # a növelő nyílra kattintva 11 perc lesz, és a figyelő újraindul
    up = _child(spin, "screensaverIdleMinutesUp")
    _click(window, up, qt_app)
    assert spin.property("value") == 11
    assert controller.screensaverIdleMinutes == 11
    assert procs.spawned[-1][3] == "660"
    assert len(procs.killed) == 1

    _click(window, check, qt_app)
    assert check.property("checked") is False
    assert not autostart.exists()
    assert procs.rows == []


def test_nem_tamogatott_asztalon_tiltott_es_megmondja_miert(qml_app, qt_app, tmp_path):
    window, controller, _engine = qml_app
    procs = _install(controller, tmp_path, {"XDG_CURRENT_DESKTOP": "GNOME",
                                            "WAYLAND_DISPLAY": "wayland-0"})
    dialog = _open_dialog(window, qt_app)
    check = _child(dialog, "screensaverIdleCheck")
    message = _child(dialog, "screensaverIdleMessage")

    assert check.property("enabled") is False
    assert _child(dialog, "screensaverIdleMinutes").property("enabled") is False
    assert message.property("visible") is True
    assert "GNOME" in message.property("text")
    assert "swayidle" in message.property("text")

    _click(window, check, qt_app)
    assert check.property("checked") is False
    assert not (tmp_path / "cfg").exists()
    assert procs.spawned == []


def test_hianyzo_swayidle_eseten_a_telepitest_javasolja(qml_app, qt_app, tmp_path):
    window, controller, _engine = qml_app
    procs = _install(controller, tmp_path, _LABWC)
    controller._screensaver_idle._which = lambda _name: None
    controller.screensaverIdleChanged.emit()
    dialog = _open_dialog(window, qt_app)

    message = _child(dialog, "screensaverIdleMessage")
    assert _child(dialog, "screensaverIdleCheck").property("enabled") is False
    assert message.property("visible") is True
    assert "swayidle" in message.property("text")
    assert procs.spawned == []


def test_indito_hiba_eseten_a_pipa_nem_marad_es_hibauzenet_jelenik_meg(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    procs = _install(controller, tmp_path, _LABWC)
    procs.spawn_error = OSError("nem indítható")
    dialog = _open_dialog(window, qt_app)
    check = _child(dialog, "screensaverIdleCheck")
    message = _child(dialog, "screensaverIdleMessage")

    _click(window, check, qt_app)

    assert check.property("checked") is False
    assert not (tmp_path / "cfg" / "autostart" / idle.AUTOSTART_NAME).exists()
    assert controller.screensaverIdleEnabled is False
    assert message.property("visible") is True
    assert "could not be saved" in message.property("text")


def test_autostartot_nem_futtato_asztalon_figyelmeztet_de_engedi(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    procs = _install(
        controller, tmp_path,
        {"XDG_CURRENT_DESKTOP": "sway", "WAYLAND_DISPLAY": "wayland-0"},
    )
    dialog = _open_dialog(window, qt_app)
    check = _child(dialog, "screensaverIdleCheck")
    message = _child(dialog, "screensaverIdleMessage")

    assert check.property("enabled") is True
    assert message.property("visible") is True
    assert "log in again" in message.property("text")

    _click(window, check, qt_app)
    assert check.property("checked") is True
    assert procs.spawned


def test_labwc_en_nincs_autostart_figyelmeztetes(qml_app, qt_app, tmp_path):
    window, controller, _engine = qml_app
    _install(controller, tmp_path, _LABWC)
    dialog = _open_dialog(window, qt_app)
    assert _child(dialog, "screensaverIdleMessage").property("visible") is False


def test_kivulrol_torolt_bejegyzes_megnyitaskor_kikapcsoltnak_latszik(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    _install(controller, tmp_path, _LABWC)
    dialog = _open_dialog(window, qt_app)
    check = _child(dialog, "screensaverIdleCheck")
    _click(window, check, qt_app)
    assert check.property("checked") is True

    QMetaObject.invokeMethod(dialog, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    (tmp_path / "cfg" / "autostart" / idle.AUTOSTART_NAME).unlink()

    dialog = _open_dialog(window, qt_app)
    assert _child(dialog, "screensaverIdleCheck").property("checked") is False


def test_bekapcsolt_allapotban_a_percet_a_bejegyzesbol_olvassa(
    qml_app, qt_app, tmp_path
):
    _window, controller, _engine = qml_app
    _install(controller, tmp_path, _LABWC)
    controller._screensaver_idle.enable(17)
    assert controller.screensaverIdleMinutes == 17
    controller._screensaver_idle.disable()
    assert controller.screensaverIdleMinutes == idle.DEFAULT_MINUTES
