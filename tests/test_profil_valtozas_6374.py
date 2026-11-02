"""A csomagmérés megnevezi, mit írt a program a profilba (#6374)."""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packaging" / "windows"))

import profil_valtozas  # noqa: E402


def test_csak_az_indulas_ota_irt_fajlokat_osszesiti_mappankent(tmp_path):
    regi = tmp_path / "AppData" / "Local" / "regi.txt"
    regi.parent.mkdir(parents=True)
    regi.write_text("x")
    os.utime(regi, (time.time() - 3600, time.time() - 3600))
    ota = time.time() - 1
    cache = tmp_path / "AppData" / "Local" / "PicasaPy" / "cache" / "qtpipelinecache"
    cache.mkdir(parents=True)
    (cache / "a.bin").write_bytes(b"12345")
    (cache / "b.bin").write_bytes(b"123")
    sorok = profil_valtozas.uj_fajlok(tmp_path, ota)
    assert sorok == ["AppData/Local/PicasaPy/cache/qtpipelinecache: 2 fájl, 8 bájt"]


def test_hianyzo_profilnal_ures(tmp_path):
    assert profil_valtozas.uj_fajlok(tmp_path / "nincs", 0) == []
