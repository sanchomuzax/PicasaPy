"""#2077: a POSIX-őr foga és a kapu-ellenőrzése.

A `skipif` kifejezése az **importáláskor** fut le. Egy Windowson nem
létező `os`-függvény ott nem egy tesztet buktat, hanem a **gyűjtést** —
és vele a részfutás egészét. Éles eset (`ci.yml` 33690975023, windows
1/4): a `tests/scanner/test_hibas_bejegyzesek_1998.py` modulszintű
`os.getuid()`-ja `exit 2`-t adott a `tests --ignore=tests/app` részre.

⚠️ Ez a fájl a KÉT irányt együtt méri: az őr fogja a védtelen alakot, és
NEM bünteti a rövidzárral védettet. Egy kapu, ami a helyes munkát is
elbuktatja, rosszabb a semminél.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

GYOKER = Path(__file__).resolve().parents[1]
OR = GYOKER / "scripts" / "posix_or.py"

VEDTELEN = {
    "csupasz_skipif": (
        "import os\nimport pytest\n\n"
        '@pytest.mark.skipif(os.getuid() == 0, reason="x")\n'
        "def test_a(): pass\n"
    ),
    "csupasz_pytestmark": (
        "import os\nimport pytest\n\n"
        'pytestmark = pytest.mark.skipif(os.geteuid() == 0, reason="x")\n'
    ),
    "osztaly_dekoratorban": (
        "import os\nimport pytest\n\n"
        '@pytest.mark.skipif(os.uname().sysname == "Linux", reason="x")\n'
        "class TestX:\n    def test_a(self): pass\n"
    ),
}

VEDETT = {
    "hasattr_rovidzar": (
        "import os\nimport pytest\n\n"
        "@pytest.mark.skipif(\n"
        '    not hasattr(os, "getuid") or os.getuid() == 0, reason="x")\n'
        "def test_a(): pass\n"
    ),
    "sys_platform_rovidzar": (
        "import os, sys\nimport pytest\n\n"
        "pytestmark = pytest.mark.skipif(\n"
        '    sys.platform.startswith("win")\n'
        '    or (hasattr(os, "geteuid") and os.geteuid() == 0), reason="x")\n'
    ),
    "fuggvenyen_belul": ("import os\n\n\ndef test_a():\n    assert os.getuid() >= 0\n"),
}


def _futtat() -> int:
    return subprocess.run(
        [sys.executable, str(OR)], cwd=GYOKER, capture_output=True, text=True
    ).returncode


@pytest.fixture
def proba_fajl():
    """Ideiglenes tesztfájl a `tests/` alatt — az őr azt járja be."""
    ut = GYOKER / "tests" / "_proba_posix_or_2077.py"
    yield ut
    ut.unlink(missing_ok=True)


def test_a_mai_keszlet_TISZTA():
    """Az őr a jelenlegi fán zölden fut — enélkül minden más eset hamis."""
    assert _futtat() == 0


@pytest.mark.parametrize("nev", sorted(VEDTELEN))
def test_a_vedtelen_alakot_MEGFOGJA(proba_fajl, nev):
    proba_fajl.write_text(VEDTELEN[nev], encoding="utf-8")
    assert _futtat() != 0, f"az őr átengedte a védtelen alakot: {nev}"


@pytest.mark.parametrize("nev", sorted(VEDETT))
def test_a_HELYES_alakot_ATENGEDI(proba_fajl, nev):
    """Kapu-ellenőrzés: a rövidzáras és a futásidejű alak a projekt
    bevált mintája — ezeket az őr nem büntetheti."""
    proba_fajl.write_text(VEDETT[nev], encoding="utf-8")
    assert _futtat() == 0, f"az őr hamisan riasztott a helyes alakra: {nev}"
