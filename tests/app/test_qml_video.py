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
    probe = Path(__file__).parent / "qml_video_probe.py"
    repo_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root / "src"), str(repo_root / "tests")]
    )
    result = subprocess.run(
        [sys.executable, str(probe), str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    assert result.returncode == 0, (
        f"probe exit={result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "OK" in result.stdout
