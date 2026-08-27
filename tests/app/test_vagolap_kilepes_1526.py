"""#1526: a vágólapra másolás után a KILÉPÉS ne omoljon össze.

## A hibaosztály

A PySide6 `QClipboard.setMimeData()` átveszi a C++-oldali tulajdonjogot, de
a Python-oldali csomagoló nyilvántartásban marad. Ha a folyamat úgy áll le,
hogy a vágólapon egy **Pythonban létrehozott** `QMimeData` ül, a leállás
**SIGSEGV**-vel végződik.

Mérve (2026-08-27, PySide6, offscreen, Qt-n kívüli kód nélküli próba):

| mi áll a vágólapon a leálláskor | kilépőkód |
|---|---|
| semmi, vagy `setText()` (a `QMimeData`-t a Qt hozza létre C++-ban) | 0 |
| Pythonban létrehozott `QMimeData` | **139 (SIGSEGV)** |
| ugyanaz, de előtte `clear()`/`setText()` | 0 |

A Python-oldali hivatkozás megtartása vagy eldobása (`del` +
`gc.collect()`), a `setParent()`, a `shiboken6.invalidate()` és a
`setUrls()` egyike sem segít — mind 139; tulajdonjog-átadó hívást ez a
`shiboken6` nem kínál.

Ez NEM tesztkörnyezeti furcsaság: a felhasználó „másolok pár képet, majd
bezárom a programot" útján a folyamat a leállás közben omlik össze, és a
leállításkor futó munka (pl. a `QSettings` kiírása) elveszhet.

## Miért alprocesszben mérünk

A hiba a FOLYAMAT LEÁLLÁSAKOR jelentkezik, tehát a saját tesztfolyamatunkon
belülről nem figyelhető meg — csak egy külön folyamat kilépőkódján. Ezért
indít ez a fájl alprocesszt, és a `returncode`-ot állítja.

⚠️ A `-q` összefoglaló ilyenkor félrevezet: a tesztek „passed"-et írnak, a
bukás csak a kilépőkódban látszik. Ezt a jegy egy körrel korábban meg is
úszta volna, ha nem a kilépőkódot nézzük.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_SRC = _REPO / "src"

#: A termék útja: vezérlő -> vágólapra másolás -> RENDES kilépés
#: (`app.quit()` az eseményhurokból, tehát az `aboutToQuit` is elsül).
_SCRIPT = """
import os, sys
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
app = QGuiApplication([])
from picasapy.app.fileops_controller import FileOpsController

# A vágólapot tesztenként el kell engedni, különben a folyamat SIGSEGV-vel
# áll le (#1526) — az indoklás a fixture docstringjében.
pytestmark = pytest.mark.usefixtures("vagolap_elengedese")
vezerlo = FileOpsController()
getattr(vezerlo, sys.argv[1])([sys.argv[2]])
QTimer.singleShot(0, app.quit)
app.exec()
"""


def _futtat(muvelet: str, kep: Path) -> subprocess.CompletedProcess:
    kornyezet = dict(os.environ, PYTHONPATH=str(_SRC), QT_QPA_PLATFORM="offscreen")
    return subprocess.run(
        [sys.executable, "-c", _SCRIPT, muvelet, str(kep)],
        capture_output=True,
        timeout=120,
        env=kornyezet,
        check=False,
    )


@pytest.fixture
def kep(tmp_path) -> Path:
    ut = tmp_path / "a.jpg"
    ut.write_bytes(b"\xff\xd8\xff\xd9")
    return ut


@pytest.mark.parametrize("muvelet", ["copyToClipboard", "cutToClipboard"])
def test_a_vagolapra_masolas_utan_a_kilepes_TISZTA(muvelet, kep):
    eredmeny = _futtat(muvelet, kep)
    assert eredmeny.returncode == 0, (
        f"a(z) {muvelet} után a kilépés {eredmeny.returncode} kóddal állt le "
        f"(139 = SIGSEGV). stderr:\n{eredmeny.stderr.decode(errors='replace')[-2000:]}"
    )


def test_a_kontroll_ut_is_tiszta(kep):
    """Ellenpróba: vágólap-írás NÉLKÜL is nullával lép ki — különben nem a
    vágólapot mérnénk, hanem valami mást."""
    kornyezet = dict(os.environ, PYTHONPATH=str(_SRC), QT_QPA_PLATFORM="offscreen")
    eredmeny = subprocess.run(
        [
            sys.executable,
            "-c",
            "import os;os.environ['QT_QPA_PLATFORM']='offscreen'\n"
            "from PySide6.QtCore import QTimer\n"
            "from PySide6.QtGui import QGuiApplication\n"
            "app=QGuiApplication([])\n"
            "import picasapy.app.fileops_controller as m; m.FileOpsController()\n"
            "QTimer.singleShot(0, app.quit); app.exec()\n",
        ],
        capture_output=True,
        timeout=120,
        env=kornyezet,
        check=False,
    )
    assert eredmeny.returncode == 0
