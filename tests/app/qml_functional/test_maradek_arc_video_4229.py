"""#4229: valós főablakban kattintható arc- és videómaradékok.

A gombok helyét mindig a QML-elem aktuális geometriájából számítjuk. A főablak
magassága mindhárom vezérlőpróbában -5, 0 és +5 képponttal változik; nincs
platformhoz kötött, beégetett képernyőkoordináta.
"""

from __future__ import annotations

import csv
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

GYOKER = Path(__file__).resolve().parents[3]
ELEMEK = GYOKER / "docs" / "specs" / "ui-lefedettseg-elemek.csv"


def _lefedettseg_sor(elem: str) -> dict[str, str]:
    with ELEMEK.open(encoding="utf-8", newline="") as fajl:
        sor = next((s for s in csv.DictReader(fajl) if s["elem"] == elem), None)
    assert sor is not None, f"a lefedettségi táblából hiányzik: {elem}"
    return sor


def _lefedett(elem: str, allapot: str) -> dict[str, str]:
    sor = _lefedettseg_sor(elem)
    assert sor["allapot"] == allapot, f"{elem}: {sor['allapot']} != {allapot}"
    return sor


def _elem(ablak, nev: str, kotelezo: bool = True):
    talalat = ablak.findChild(QObject, nev)
    if kotelezo:
        assert talalat is not None, f"a(z) {nev} elem nincs a főablakban"
    return talalat


def _vard_meg(feltetel, qt_app, leiras: str, hatarido: float = 3.0):
    vege = time.monotonic() + hatarido
    while time.monotonic() < vege:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.05)
    raise AssertionError(f"időkorláton belül nem teljesült: {leiras}")


def _kattint(ablak, elem, x_arany: float = 0.5) -> None:
    """Valódi egérkattintás az elem pillanatnyi helyére leképezve."""
    pont = elem.mapToScene(QPointF(elem.width() * x_arany, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )


def _linux_audio_backend_elerheto() -> bool:
    """Qt Multimedia Linuxon PipeWire/PulseAudio kapcsolatot igényel."""
    if not sys.platform.startswith("linux"):
        return True
    if os.environ.get("PULSE_SERVER"):
        return True
    futasido = Path(
        os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    )
    for nev in ("pipewire-0", "pulse/native"):
        ut = futasido / nev
        if not ut.exists():
            continue
        kliens = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        kliens.settimeout(0.25)
        try:
            if kliens.connect_ex(str(ut)) == 0:
                return True
        except OSError:
            continue
        finally:
            kliens.close()
    return False


def test_az_ismeretlen_arc_fejlec_ket_nezetvaltoja_a_valodi_fomablakban(
    qml_app, qt_app
):
    _lefedett("unknownfaceheaderpanel/showignored", "megvan")
    _lefedett("unknownfaceheaderpanel/showunknown", "megvan")

    ablak, _vezerlo, _engine = qml_app
    ablak.setProperty("unnamedFacesOpen", True)
    ablak.setProperty("facesAlbumMode", "unnamed")
    nezet = _elem(ablak, "unnamedFacesView")
    _vard_meg(lambda: nezet.isVisible(), qt_app, "a Névtelenek nézet megjelenése")

    alapmagassag = ablak.height()
    for elteres in (-5, 0, 5):
        celmagassag = alapmagassag + elteres
        ablak.setHeight(celmagassag)
        _vard_meg(
            lambda celmagassag=celmagassag: ablak.height() == celmagassag,
            qt_app,
            f"a főablak {elteres:+d} képpontos magasságváltozása",
        )

        show_ignored = _elem(ablak, "unknownfaceheaderpanel/showignored")
        assert show_ignored.isVisible()
        fejlec = _elem(ablak, "unknownFaceViewHeader")
        csoport_pane = _elem(ablak, "clusterToggleButton")
        assert csoport_pane.isVisible()
        ignoralt_pont = show_ignored.mapToItem(fejlec, QPointF(0, 0))
        csoport_pont = csoport_pane.mapToItem(fejlec, QPointF(0, 0))
        assert abs(show_ignored.width() - 120) <= 5
        assert abs(show_ignored.height() - 27) <= 5
        assert abs(csoport_pane.width() - 120) <= 5
        assert abs(ignoralt_pont.x() - csoport_pont.x() - csoport_pane.width() - 5) <= 5
        # A QML-tesztmotor nem telepíti a magyar fordítót; a hivatalos
        # fordítás meglétét az i18n-őrök ellenőrzik.
        assert str(show_ignored.property("text")) == "Show ignored faces"
        _kattint(ablak, show_ignored)
        _vard_meg(
            lambda: ablak.property("facesAlbumMode") == "ignored",
            qt_app,
            "a Mellőzött emberek album kiválasztása",
        )
        assert not csoport_pane.isVisible()

        back_to_unnamed = _elem(ablak, "unknownfaceheaderpanel/showunknown")
        assert back_to_unnamed.isVisible()
        nevnelkuli_pont = back_to_unnamed.mapToItem(fejlec, QPointF(0, 0))
        assert abs(back_to_unnamed.width() - 120) <= 5
        assert abs(back_to_unnamed.height() - 27) <= 5
        assert abs(nevnelkuli_pont.x() - ignoralt_pont.x()) <= 5
        assert abs(nevnelkuli_pont.y() - ignoralt_pont.y()) <= 5
        assert str(back_to_unnamed.property("text")) == "Back to Unnamed"
        _kattint(ablak, back_to_unnamed)
        _vard_meg(
            lambda: ablak.property("facesAlbumMode") == "unnamed",
            qt_app,
            "visszatérés a Névtelenek albumhoz",
        )


def test_a_ket_meglevo_video_csuszka_valodi_kattintassal_allitja_a_lejatszot(
    tmp_path,
):
    _lefedett("video_control_bar2/scaleslider", "megvan")
    _lefedett("video_control_bar2/volumeslider", "megvan")
    _lefedett("movieeditpanel/export_movie", "megvan")
    if os.environ.get("PICASAPY_VIDEO_PROBE") != "1":
        pytest.skip(
            "Valódi lejátszós Qt Multimedia-próba: csak PICASAPY_VIDEO_PROBE=1 "
            "mellett fut — a CI-n nincs hangkiszolgáló, az RPi-n a hardveres "
            "dekóder hiányzik (v4l2m2m), így alapból egyik környezetben sem állít"
        )
    if not _linux_audio_backend_elerheto():
        pytest.skip(
            "Qt Multimedia-kimeneti próba kihagyva: a Linux Qt-lejátszáshoz "
            "szükséges PipeWire/PulseAudio foglalat nem elérhető ebben a "
            "homokozóban"
        )

    probe = Path(__file__).parents[1] / "qml_video_controls_probe_4229.py"
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    # A próba ne kapcsolódjon a valódi kijelzőhöz (X-hitelesítés, Wayland).
    for kulcs in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY"):
        env.pop(kulcs, None)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(GYOKER / "src"), str(GYOKER / "tests")]
    )
    eredmeny = subprocess.run(
        [sys.executable, str(probe), str(tmp_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        env=env,
    )
    assert eredmeny.returncode == 0, (
        f"probe exit={eredmeny.returncode}\n"
        f"stdout:\n{eredmeny.stdout}\nstderr:\n{eredmeny.stderr}"
    )
    assert "OK #4229" in eredmeny.stdout


def test_youtube_feltoltes_nem_cel_es_indoka_a_lefedettsegben_szerepel():
    sor = _lefedett("movieeditpanel/export_youtube", "nem-cel")
    assert "megszűnt" in sor["megjegyzes"].casefold()
    assert "Picasa" in sor["megjegyzes"]
