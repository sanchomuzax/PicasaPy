"""Videó-lejátszás a nézőben (#14) — a QML-ellenőrzés alprocesszben fut.

A MediaPlayer + engine ismételt életciklusa egy processzen belül GIL↔Qt
deadlockra hajlamos (a #53-as hibaosztály), ezért a teljes videós
QML-viselkedést a qml_video_probe.py egyetlen alprocesszben ellenőrzi —
így a tesztkészlet többi (engine-t építő) tesztjét nem veszélyezteti.
A Qt Multimedia hiányában a teszt kimarad — DE a Python-kötés megléte NEM
elég hozzá: a próba QML-oldalról (`VideoPlayerView.qml`) importálja a
`QtMultimedia`-t, aminek SAJÁT QML-modulja van, külön csomagban. Ha csak a
kötés van meg, az `importorskip` átengedi a tesztet, a próba pedig
`module "QtMultimedia" is not installed`-del elhasal — és a bukás így
környezeti hiányról szól, nem a kódról. Ezért MINDKETTŐT ellenőrizzük.
"""

import os
import re
import socket
import subprocess
import sys
from pathlib import Path

import pytest


def _qml_modul_hianyzik(nev: str) -> bool:
    """Hiányzik-e a `nev` QML-modul a Qt import-útjáról?

    A QML-modul a Python-kötéstől FÜGGETLENÜL telepíthető (Debian alatt
    `python3-pyside6.qtmultimedia` vs. `qml6-module-qtmultimedia`), ezért a
    kötés importálhatósága önmagában nem bizonyíték.
    """
    from PySide6.QtCore import QLibraryInfo

    import_ut = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.QmlImportsPath))
    return not (import_ut / nev).is_dir()


def _linux_hangkimenet_elerheto() -> bool:
    """A Linux Qt Multimedia videólejátszója hangkimenetet is nyit."""
    if not sys.platform.startswith("linux") or os.environ.get("PULSE_SERVER"):
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


def test_video_viewer_probe(tmp_path):
    # exc_type=ImportError: a felhő-konténerben a modul megvan, de a
    # rendszerkönyvtára (libpulse) hiányzik — az is kihagyás, nem hiba
    pytest.importorskip("PySide6.QtMultimedia", exc_type=ImportError)
    if _qml_modul_hianyzik("QtMultimedia"):
        pytest.skip(
            "a QtMultimedia QML-modulja hiányzik ezen a gépen (a Python-kötés "
            "megvan, de a QML-oldali modul KÜLÖN csomag), ezért a videós néző "
            "nem tölthető be. Debian/Ubuntu alatt így pótolható: "
            "sudo apt install qml6-module-qtmultimedia"
        )
    if not _linux_hangkimenet_elerheto():
        pytest.skip(
            "a Qt Multimedia videópróba kihagyva: a MediaPlayer a "
            "videónéző betöltésekor Linuxon hangkimenetet nyit; hang nélküli "
            "gépen a videó-gesztust a VideoExitGestureArea külön próbája méri"
        )
    probe = Path(__file__).parent / "qml_video_probe.py"
    repo_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_QUICK_BACKEND"] = "software"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root / "src"), str(repo_root / "tests")]
    )
    try:
        result = subprocess.run(
            [sys.executable, str(probe), str(tmp_path)],
            capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            timeout=120,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        def szoveg(kimenet):
            if isinstance(kimenet, bytes):
                return kimenet.decode("utf-8", errors="replace")
            return kimenet or ""

        pytest.fail(
            "a videónéző-próba 120 másodperc alatt nem fejeződött be\n"
            f"stdout:\n{szoveg(exc.stdout)}\n"
            f"stderr:\n{szoveg(exc.stderr)}",
            pytrace=False,
        )
    assert result.returncode == 0, (
        f"probe exit={result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "OK" in result.stdout
    lepesek = (
        "video-single-click",
        "video-double-click",
        "video-single-click-exit-click",
        "photo-single-click-exit-click",
        "photo-double-click-exit-click",
    )
    for lepes in lepesek:
        assert f"PROBE-STEP START {lepes} " in result.stdout
        assert f"PROBE-STEP END {lepes} " in result.stdout
        assert re.search(
            rf"PROBE-MOUSE step={re.escape(lepes)} "
            r"event=press timestamp=\d+ monotonic=\d+\.\d+",
            result.stdout,
        ), f"{lepes}: nem került egéresemény-időbélyeg a próbanaplóba"
    assert re.search(
        r"PROBE-DOUBLECLICK step=photo-double-click-exit-click "
        r"handler=(?:entered|not-entered) entries=\d+ "
        r"singleClickExitEnabled=(?:True|False) layoutMode='[^']+' "
        r"tiltActive=(?:True|False)",
        result.stdout,
    ), "a próba nem naplózta a dupla kattintás kezelőjét és a három feltételt"
    assert re.search(
        r"PROBE-MOUSE step=photo-double-click-exit-click event=press "
        r"timestamp=\d+ monotonic=\d+\.\d+ "
        r"eventTarget=(?:None|'[^']*') "
        r"singleClickExitTimerRunning=(?:True|False|None) ",
        result.stdout,
    ), "a dupla próbánál nem naplózott eseménypontot és időzítő-állapotot"
    assert re.search(
        r"PROBE-DOUBLECLICK step=photo-double-click-exit-click "
        r"handler=(?:entered|not-entered) entries=\d+ "
        r"singleClickExitEnabled=(?:True|False) layoutMode='[^']+' "
        r"tiltActive=(?:True|False) pressEvents=\[.*\] "
        r"pressEventCountBefore=\d+ pressEventCountAfter=\d+ "
        r"lastPressBranch='[^']+' timerRunningOnLastPress=(?:True|False)",
        result.stdout,
    ), "a próba nem naplózta a QML-lenyomás ágát és időzítőjét"
