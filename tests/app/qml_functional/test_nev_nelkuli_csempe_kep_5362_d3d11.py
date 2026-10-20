"""#5362: a csempe-teszt a valódi Windows-ablakon, Direct3D 11 megjelenítővel.

A sima QML-tesztek `offscreen` platformon, szoftveres megjelenítéssel futnak; a
tulajdonos gépe viszont Direct3D-vel rajzol, és ott voltak üresek a csempék. Ez a
teszt Windows alatt külön folyamatban, `QT_QPA_PLATFORM=windows` és
`QSG_RHI_BACKEND=d3d11` mellett futtatja ugyanazt a csempe-ellenőrzést (a
futón a WARP adja a Direct3D-t). Más platformon kimarad.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="csak Windows alatt értelmes")

_CEL = Path(__file__).with_name("test_nev_nelkuli_csempe_kep_5362.py")


def test_a_csempek_arckepe_direct3d_megjelenitovel_is_latszik(tmp_path):
    env = {**os.environ, "QT_QPA_PLATFORM": "windows", "QSG_RHI_BACKEND": "d3d11",
           "QSG_INFO": "1"}
    ki = subprocess.run(
        [sys.executable, "-m", "pytest", str(_CEL), "-q", "-p", "no:cacheprovider",
         f"--basetemp={tmp_path / 'bt'}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300, env=env,
        cwd=Path(__file__).resolve().parents[3],
    )
    naplo = (ki.stdout + ki.stderr)[-6000:]
    assert ki.returncode == 0, f"a csempe-teszt Direct3D-vel bukott:\n{naplo}"
