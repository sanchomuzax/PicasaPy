"""A face_groups almodul importja nem írja felül a face_groups() függvényt (#6697)."""

import subprocess
import sys
from pathlib import Path

_SRC = str(Path(__file__).resolve().parents[2] / "src")


def test_almodul_import_utan_is_fuggveny():
    kod = (
        "import sys; sys.path.insert(0, %r)\n"
        "import picasapy.index.face_groups\n"
        "import picasapy.index as ix\n"
        "assert callable(ix.face_groups), type(ix.face_groups)\n"
        "from picasapy.index import face_groups\n"
        "assert callable(face_groups)\n"
    ) % _SRC
    r = subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True, check=False)
    assert r.returncode == 0, r.stderr
