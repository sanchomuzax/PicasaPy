"""Az őrnek FOGA van: vetett hibát talál, a tisztát átengedi (#1991).

A `scripts/cv2_utvonal_or.py` a `cv2.imread` / `cv2.imwrite`
fájlútvonalas alakját tiltja a forrásban. Ez a fájl azt méri, hogy az őr
tényleg fog — enélkül a hamis biztonság rosszabb, mint ha nem volna őr.

⚠️ Az őrnek a **kommentet és a docstringet ki kell hagynia**: a projekt
négy modulja (és maga az őr) NÉV SZERINT említi a tiltott hívásokat a
magyarázatában. Naiv szövegkeresés azonnal hamis pozitívot adna.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OR = REPO / "scripts" / "cv2_utvonal_or.py"


def _futtat() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(OR)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120
    )


class TestAMaiForras:
    def test_tiszta(self):
        eredmeny = _futtat()
        assert eredmeny.returncode == 0, (
            f"az őr leletet talált a mai forráson:\n{eredmeny.stderr}"
        )


class TestAFOGA:
    def test_a_VETETT_hibat_megtalalja(self, tmp_path, monkeypatch):
        """Ideiglenes modul a forrásfába, tiltott hívással."""
        vetett = REPO / "src" / "picasapy" / "_vetett_hiba_1991.py"
        vetett.write_text(
            "from picasapy.lazy_cv2 import cv2\n\n\n"
            "def olvas(ut):\n    return cv2.imread(str(ut))\n",
            encoding="utf-8",
        )
        try:
            eredmeny = _futtat()
        finally:
            vetett.unlink()
        assert eredmeny.returncode == 1, "az őr ÁTENGEDTE a vetett hibát"
        assert "_vetett_hiba_1991.py" in eredmeny.stderr

    def test_a_KOMMENTET_nem_veszi_leletnek(self):
        """A hamis pozitív ugyanolyan rossz: ha az őr a magyarázatokra is
        riaszt, senki nem fogja használni."""
        vetett = REPO / "src" / "picasapy" / "_vetett_komment_1991.py"
        vetett.write_text(
            '"""Ez a modul a cv2.imread(...) tiltásáról szól."""\n\n'
            "# NE hívj cv2.imwrite(...)-ot fájlútvonallal!\n"
            "SZOVEG = \"cv2.imread(str(path))\"\n",
            encoding="utf-8",
        )
        try:
            eredmeny = _futtat()
        finally:
            vetett.unlink()
        assert eredmeny.returncode == 0, (
            f"az őr a kommentre/docstringre riasztott:\n{eredmeny.stderr}"
        )
