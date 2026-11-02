"""#6383: a frissítési tesztdiagnosztika megtalálja az ablakba írt QML-elemet.

A QML-ben közvetlenül az ablakba írt elem Qt-szülője az ablak, nem a
tartalomelem. A diagnosztika korábban csak a tartalomelem gyerekeit járta
be, ezért a `versionLabel` sosem került a kimenetbe, és a windowsos
önfrissítési próba minden futáskor 60 másodperc után elbukott."""

from __future__ import annotations

import json

from PySide6.QtCore import QByteArray, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from picasapy.app.update_manager import UpdateController

_QML = b"""
import QtQuick
import QtQuick.Window
Window {
    width: 200; height: 100; visible: true
    Text { objectName: "versionLabel"; text: "v1.0.0" }
}
"""


class _Kliens:
    def latest_release(self):
        return None


def test_az_ablakba_irt_versionlabel_bekerul_a_diagnosztikaba(
    qt_app, tmp_path, monkeypatch
):
    monkeypatch.setenv("PICASAPY_UPDATE_TEST_DIAGNOSTICS", "1")
    monkeypatch.setenv("PICASAPY_UPDATE_TEST_DIAGNOSTICS_DIR", str(tmp_path))
    engine = QQmlEngine()
    component = QQmlComponent(engine)
    component.setData(QByteArray(_QML), QUrl())
    ablak = component.create()
    assert ablak is not None, component.errorString()
    try:
        from PySide6.QtCore import QSettings

        settings = QSettings(str(tmp_path / "beallitas.ini"), QSettings.Format.IniFormat)
        controller = UpdateController(
            "1.0.0", settings=settings, client=_Kliens(), schedule=False
        )
        controller._write_test_diagnostics()
        sorok = [
            json.loads(sor)
            for fajl in tmp_path.glob("*.jsonl")
            for sor in fajl.read_text(encoding="utf-8").splitlines()
        ]
        assert sorok, "a diagnosztika nem írt pillanatot"
        nevek = [obj["name"] for obj in sorok[-1]["objects"]]
        assert "versionLabel" in nevek
    finally:
        ablak.deleteLater()
