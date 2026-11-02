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


def test_a_futas_kozben_irt_qmlc_forrasneve_visszakeresheto(tmp_path):
    """#6426: a 7 futás közben írt .qmlc forrásnevét a hash-ből keresi vissza."""
    from hashlib import sha1

    qml = tmp_path / "app" / "_internal" / "PySide6" / "qml" / "QtQuick" / "Dialogs" / "Dlg.qml"
    qml.parent.mkdir(parents=True)
    qml.write_text("import QtQuick\nItem {}\n")
    cache = tmp_path / "profile" / "AppData" / "Local" / "PicasaPy" / "cache" / "qmlcache"
    cache.mkdir(parents=True)
    ota = time.time() - 1
    nev = sha1(qml.resolve().as_posix().encode("utf-8")).hexdigest()
    (cache / f"{nev}.qmlc").write_bytes(b"x")
    (cache / f"{'0' * 40}.qmlc").write_bytes(b"x")
    sorok = profil_valtozas.qmlc_nevek(tmp_path / "profile", ota, tmp_path / "app")
    assert sorok == ["0" * 40, "_internal/PySide6/qml/QtQuick/Dialogs/Dlg.qml"]
