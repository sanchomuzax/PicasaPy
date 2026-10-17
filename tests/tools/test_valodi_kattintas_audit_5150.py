"""#5150: the audit distinguishes physical input from mentions and slot calls."""

# rontás-kontroll: ha az invokeMethod vagy a szöveges említés valódi inputnak
# számítana, az elvárt 2 maradékos vezérlőlista eltérne, és ez a próba elbukna.

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_audit(repo: Path, qml_source: str, tests_source: str) -> dict[str, object]:
    qml_root = repo / "src" / "picasapy" / "app" / "qml"
    tests_root = repo / "tests" / "app"
    qml_root.mkdir(parents=True, exist_ok=True)
    tests_root.mkdir(parents=True, exist_ok=True)
    (qml_root / "TrayBar.qml").write_text(qml_source, encoding="utf-8")
    (tests_root / "test_sample.py").write_text(tests_source, encoding="utf-8")

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
    return json.loads(result.stdout)


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


# Rontás-kontroll: az auditkód megváltoztatása előtt mind a négy új próba
# külön-külön piros volt a lenti lefedettségi állításnál.
def test_parametrize_resolves_module_level_control_names(tmp_path: Path):
    report = _run_audit(
        tmp_path,
        '''import QtQuick.Controls
Button { objectName: "displayModeAuto" }
Button { objectName: "displayModeNormal" }
''',
        '''from PySide6.QtTest import QTest
import pytest

_KIJELZESI_MODOK = (("displayModeAuto", "auto"), ("displayModeNormal", "normal"))

@pytest.mark.parametrize(("name", "value"), _KIJELZESI_MODOK)
def test_real_click(window, name, value):
    button = window.findChild(QObject, name)
    QTest.mouseClick(button, Qt.LeftButton)
''',
    )

    assert report["total"] == 2
    assert report["covered"] == 2
    assert report["remaining"] == 0


def test_parametrize_keeps_names_when_values_contain_qt_enums(tmp_path: Path):
    report = _run_audit(
        tmp_path,
        '''import QtQuick
Shortcut { objectName: "shortcutOne" }
Shortcut { objectName: "shortcutTwo" }
''',
        '''from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
import pytest

_SHORTCUTS = (("shortcutOne", Qt.Key.Key_1), ("shortcutTwo", Qt.Key.Key_2))

@pytest.mark.parametrize(("name", "key"), _SHORTCUTS)
def test_real_key_press(window, name, key):
    window.findChild(QObject, name)
    QTest.keyClick(window, key)
''',
    )

    assert report["total"] == 2
    assert report["covered"] == 2
    assert report["remaining"] == 0


def test_a_lambda_belsejeben_levo_qtest_kattintas_fed(tmp_path: Path):
    report = _run_audit(
        tmp_path,
        '''import QtQuick.Controls
Button { objectName: "lambdaButton" }
''',
        '''from PySide6.QtTest import QTest
from support.qt_wait import wait_for_signal

def test_real_click_after_signal(window, finished):
    button = window.findChild(QObject, "lambdaButton")
    wait_for_signal(finished, lambda: QTest.mouseClick(button, Qt.LeftButton))
''',
    )

    assert report["total"] == 1
    assert report["covered"] == 1
    assert report["remaining"] == 0


def test_dinamikus_objectname_prefixe_fed_a_tesztekben(tmp_path: Path):
    report = _run_audit(
        tmp_path,
        '''import QtQuick.Controls
MenuItem { objectName: "dynamicMenuItem_" + modelData }
''',
        '''from PySide6.QtTest import QTest

def vizualis(window, name):
    for item in window.findChildren(QObject):
        if item.objectName() == name:
            return item

def kattints(window, item):
    QTest.mouseClick(item, Qt.LeftButton)

def test_real_click_on_delegate(window):
    item = vizualis(window, "dynamicMenuItem_album42")
    kattints(window, item)
''',
    )

    assert report["total"] == 1
    assert report["covered"] == 1
    assert report["remaining"] == 0
