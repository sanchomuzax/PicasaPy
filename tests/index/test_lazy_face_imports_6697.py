"""#6697: az indexcsomag importja nem tölti be előre az arcmodulokat."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


_SRC = str(Path(__file__).resolve().parents[2] / "src")


def _futtasd(kod: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = _SRC + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-c", kod],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )


def test_index_importja_nem_tolti_be_az_arcmodulokat():
    """Importlistával őrizzük, hogy az alap indeximport arcmentes maradjon."""
    result = _futtasd(
        """
import json
import sys
import picasapy.index
print(json.dumps(sorted(
    name for name in sys.modules
    if name == 'picasapy.faces'
    or name.startswith('picasapy.faces.')
    or name in {'picasapy.index.face_groups', 'picasapy.index.faces_detected'}
)))
"""
    )
    assert result.returncode == 0, result.stderr
    imported = json.loads(result.stdout)
    assert imported == [], f"Az index importja előre betöltötte: {imported}"


def test_a_lusta_arc_exportok_elso_kereskor_importalodnak():
    """A korábbi csomagszintű szimbólumok igény esetén továbbra is elérhetők."""
    result = _futtasd(
        """
import sys
import picasapy.index as index
assert 'picasapy.index.faces_detected' not in sys.modules
assert index.PendingEmbeddingFace is not None
assert 'picasapy.index.faces_detected' in sys.modules
assert 'picasapy.index.face_groups' not in sys.modules
assert index.face_groups is not None
assert 'picasapy.index.face_groups' in sys.modules
"""
    )
    assert result.returncode == 0, result.stderr

