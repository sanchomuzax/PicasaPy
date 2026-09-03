"""#2111: az őrnek FOGA van — a vetett hibát megtalálja, a helyeset átengedi.

A `scripts/subprocess_kodolas_or.py` a `subprocess.run(text=True)` alakot
tiltja megadott kódolás nélkül. Az őr önmagában semmit nem ér, ha nem fog: a
hamis biztonság rosszabb, mintha nem volna őr.

Az éles eset: a `main` CI-je minden kód-merge után pirosra ment a
windows-lábon, mert a `text=True` ott `cp1252`-vel dekódolta a saját
őr-szkriptjeink UTF-8-as magyar kimenetét.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OR = REPO / "scripts" / "subprocess_kodolas_or.py"


def _futtat(gyoker: Path | None = None) -> subprocess.CompletedProcess:
    """Az őr futtatása. `gyoker` megadásával EGY ideiglenes fát vizsgál — a
    vetett fájlok így nem kerülnek a repóba, tehát a párhuzamosan futó
    tesztek nem látják őket (különben a `docs/`-őrök a vetett fájlokra
    riasztanának)."""
    return subprocess.run(
        [sys.executable, str(OR)] + ([str(gyoker)] if gyoker else []),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )


class TestAMaiForras:
    def test_tiszta(self, tmp_path):
        eredmeny = _futtat()
        assert eredmeny.returncode == 0, (
            f"az őr leletet talált a mai forráson:\n{eredmeny.stdout}"
        )


class TestAFOGA:
    def test_a_VETETT_hibat_megtalalja(self, tmp_path):
        vetett = tmp_path / "_vetett_kodolas_2111.py"
        vetett.write_text(
            "import subprocess\n\n\n"
            "def fut():\n"
            "    return subprocess.run(['ls'], capture_output=True, text=True)\n",
            encoding="utf-8",
        )
        try:
            eredmeny = _futtat(tmp_path)
        finally:
            vetett.unlink()
        assert eredmeny.returncode == 1, "az őr ÁTENGEDTE a vetett hibát"
        assert "_vetett_kodolas_2111.py" in eredmeny.stdout

    def test_a_universal_newlines_alakot_is_megtalalja(self, tmp_path):
        """A `text=True` régi neve ugyanaz a hiba."""
        vetett = tmp_path / "_vetett_un_2111.py"
        vetett.write_text(
            "import subprocess\n\n\n"
            "def fut():\n"
            "    return subprocess.run(['ls'], universal_newlines=True)\n",
            encoding="utf-8",
        )
        try:
            eredmeny = _futtat(tmp_path)
        finally:
            vetett.unlink()
        assert eredmeny.returncode == 1, "a universal_newlines alak átment"

    def test_a_HELYES_alakot_ATENGEDI(self, tmp_path):
        """Ellenkező irányú őr: ha a helyes alakot is bukná, senki nem
        használná — és a #2077 tanulsága szerint a kapu nem büntetheti a
        gondos munkát."""
        jo = tmp_path / "_jo_kodolas_2111.py"
        jo.write_text(
            "import subprocess\n\n\n"
            "def fut():\n"
            "    return subprocess.run(\n"
            "        ['ls'], capture_output=True, text=True,\n"
            "        encoding='utf-8', errors='replace',\n"
            "    )\n",
            encoding="utf-8",
        )
        try:
            eredmeny = _futtat(tmp_path)
        finally:
            jo.unlink()
        assert eredmeny.returncode == 0, (
            f"az őr a HELYES alakot is leletnek vette:\n{eredmeny.stdout}"
        )

    def test_a_BAJTOS_hivast_nem_bantja(self, tmp_path):
        """`text=` nélkül nincs dekódolás, tehát nincs mit elrontani."""
        jo = tmp_path / "_bajtos_2111.py"
        jo.write_text(
            "import subprocess\n\n\n"
            "def fut():\n"
            "    return subprocess.run(['ls'], capture_output=True)\n",
            encoding="utf-8",
        )
        try:
            eredmeny = _futtat(tmp_path)
        finally:
            jo.unlink()
        assert eredmeny.returncode == 0, (
            f"az őr a bájtos hívásra riasztott:\n{eredmeny.stdout}"
        )
