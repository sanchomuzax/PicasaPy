"""#6374: a Windows-csomag előre fordított QML-cache-t használ."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from picasapy.app.qml_disk_cache import (
    _qt_cache_file_name,
    _seed_packaged_qml_cache,
)

_REPO = Path(__file__).resolve().parents[1]
_BUILD_SCRIPT = _REPO / "packaging" / "windows" / "build_qml_cache.py"


def _csomag_cache(qml_root: Path, csomag: Path) -> dict:
    eredmeny = subprocess.run(
        [
            sys.executable,
            str(_BUILD_SCRIPT),
            "--qml-root",
            str(qml_root),
            "--output",
            str(csomag),
        ],
        cwd=_REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
    )
    assert eredmeny.returncode == 0, eredmeny.stdout + eredmeny.stderr
    return json.loads((csomag / "manifest.json").read_text(encoding="utf-8"))


def test_a_windowsi_helyi_utvonal_perjeleit_normalizalja_a_cache_hashhoz() -> None:
    helyi_utvonal = r"D:\Programok\PicasaPy\qml\Main.qml"
    vart = hashlib.sha1(
        b"D:/Programok/PicasaPy/qml/Main.qml"
    ).hexdigest() + ".qmlc"

    assert _qt_cache_file_name(helyi_utvonal, ".qmlc") == vart


def test_a_qt_a_csomagban_levo_qml_es_js_cachet_hasznalja(tmp_path: Path) -> None:
    build_qml_root = tmp_path / "build" / "qml"
    build_qml_root.mkdir(parents=True)
    (build_qml_root / "dimensions.js").write_text(
        ".pragma library\nfunction width() { return 21; }\n", encoding="utf-8"
    )
    (build_qml_root / "CacheProbe.qml").write_text(
        'import QtQuick\nimport "dimensions.js" as Dimensions\n'
        "Rectangle { width: Dimensions.width(); height: 13 }\n",
        encoding="utf-8",
    )
    qml_root = tmp_path / "installed" / "picasapy" / "app" / "qml"
    qml_root.parent.mkdir(parents=True)
    shutil.copytree(build_qml_root, qml_root)
    qml_file = qml_root / "CacheProbe.qml"
    csomag = tmp_path / "csomagolt-cache"
    manifest = _csomag_cache(build_qml_root, csomag)
    assert {Path(item["source"]).suffix for item in manifest["files"]} == {
        ".qml",
        ".js",
    }

    cache_dir = tmp_path / "qt-cache"
    kornyezet: dict[str, str] = {}
    masolt = _seed_packaged_qml_cache(
        qml_root, bundle_dir=csomag, cache_dir=cache_dir, environ=kornyezet
    )
    assert masolt == 2
    assert kornyezet["QML_DISK_CACHE_PATH"] == str(cache_dir)

    cache_fajlok = {
        _qt_cache_file_name(
            str((qml_root / item["source"]).resolve()),
            ".qmlc" if item["source"].endswith(".qml") else ".jsc",
        )
        for item in manifest["files"]
    }
    elotte = {
        nev: hashlib.sha256((cache_dir / nev).read_bytes()).hexdigest()
        for nev in cache_fajlok
    }
    futas_kornyezet = os.environ.copy()
    futas_kornyezet.pop("QML_DISABLE_DISK_CACHE", None)
    futas_kornyezet.update(
        {
            "QT_QPA_PLATFORM": "offscreen",
            "QT_QUICK_BACKEND": "software",
            "QML_DISK_CACHE_PATH": str(cache_dir),
        }
    )
    betoltes = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from PySide6.QtCore import QUrl; "
            "from PySide6.QtGui import QGuiApplication; "
            "from PySide6.QtQml import QQmlComponent, QQmlEngine; "
            "app=QGuiApplication([]); engine=QQmlEngine(); "
            "component=QQmlComponent(engine, QUrl.fromLocalFile(sys.argv[1]), "
            "QQmlComponent.CompilationMode.PreferSynchronous); "
            "obj=component.create(); "
            "print('CACHE_PROBE_READY' if obj else component.errors()); "
            "sys.exit(0 if obj else 1)",
            str(qml_file.resolve()),
        ],
        cwd=_REPO,
        env=futas_kornyezet,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    assert betoltes.returncode == 0, betoltes.stdout + betoltes.stderr
    assert "CACHE_PROBE_READY" in betoltes.stdout
    assert {
        nev: hashlib.sha256((cache_dir / nev).read_bytes()).hexdigest()
        for nev in cache_fajlok
    } == elotte, "a Qt újrafordította a csomagolt QML/JS cache-t"


def test_a_windows_csomagolas_a_foablak_elott_elokesziti_a_qml_cachet() -> None:
    workflow = (_REPO / ".github" / "workflows" / "package.yml").read_text(
        encoding="utf-8"
    )
    spec = (_REPO / "packaging" / "windows" / "picasapy.spec").read_text(
        encoding="utf-8"
    )
    indito = (
        _REPO / "src" / "picasapy" / "app" / "application_startup_qml.py"
    ).read_text(encoding="utf-8")

    assert "build_qml_cache.py" in workflow
    assert "PICASAPY_QML_CACHE_DIR" in workflow
    assert "PICASAPY_QML_CACHE_DIR" in spec
    assert "picasapy/app/qmlcache" in spec
    engine_setup = indito.split("def _startup_step_create_qml_engine", 1)[1].split(
        "def _startup_step_register_qml_context", 1
    )[0]
    assert "_seed_packaged_qml_cache" in engine_setup
    assert engine_setup.index("_seed_packaged_qml_cache") < engine_setup.index(
        "engine = QQmlApplicationEngine()"
    )

    mertesi_lepes = workflow.split(
        "- name: Mérés — valósághű könyvtár, elérhetetlen hálózati exportcél", 1
    )[1].split("- name: Inno Setup telepítő", 1)[0]
    assert "--inditasok 3" in mertesi_lepes
    assert "--hatar-mp 5" in mertesi_lepes
    assert "--elso-hatar-mp" not in mertesi_lepes
