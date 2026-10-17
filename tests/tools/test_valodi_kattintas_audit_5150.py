"""#5150: the audit distinguishes physical input from mentions and slot calls."""

# rontás-kontroll: ha az invokeMethod vagy a szöveges említés valódi inputnak
# számítana, az elvárt 2 maradékos vezérlőlista eltérne, és ez a próba elbukna.

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_audit_only_counts_a_qtest_input_on_the_named_control(tmp_path: Path):
    repo = tmp_path
    qml_root = repo / "src" / "picasapy" / "app" / "qml"
    tests_root = repo / "tests" / "app"
    qml_root.mkdir(parents=True)
    tests_root.mkdir(parents=True)
    (qml_root / "TrayBar.qml").write_text(
        """import QtQuick.Controls
Button { objectName: "realButton" }
Button { objectName: "invokedButton" }
Button { objectName: "mentionedButton" }
""",
        encoding="utf-8",
    )
    (tests_root / "test_sample.py").write_text(
        """from PySide6.QtTest import QTest

def _click(button):
    QTest.mouseClick(button, Qt.LeftButton)

def test_real(window):
    button = window.findChild(QObject, "realButton")
    _click(button)

def test_invoked(window):
    button = window.findChild(QObject, "invokedButton")
    QMetaObject.invokeMethod(button, "click")

def test_mentioned():
    assert "mentionedButton" in QML_SOURCE
""",
        encoding="utf-8",
    )

    script = Path(__file__).resolve().parents[2] / "scripts" / "valodi_kattintas_audit.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--qml-root",
            str(qml_root),
            "--tests-root",
            str(tests_root),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["total"] == 3
    assert report["covered"] == 1
    assert report["remaining"] == 2
    remaining = {
        entry["object_name"]
        for entries in report["groups"].values()
        for entry in entries
    }
    assert remaining == {"invokedButton", "mentionedButton"}
