"""A kézi arc-hozzáadás megszakítható, és az Emberek-panel üres állapota
az eredeti, hivatalos szöveget mutatja (#4156).
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, QRectF, Qt
from PySide6.QtTest import QTest

_QML = Path(__file__).resolve().parents[3] / "src/picasapy/app/qml/PicasaPy"
_PEOPLE = (_QML / "PeoplePanel.qml").read_text(encoding="utf-8")


def test_a_kezi_arcbevitel_megse_gombja_a_panelen_van():
    # A Picasa spec a kézi hozzáadás teljes vezérlését a PeoplePanelbe teszi;
    # a korábbi, képen lebegő Mégse gomb ezt a paritást nem fedte le.
    assert 'objectName: "peoplePanelManualCancelButton"' in _PEOPLE
    assert 'text: qsTr("Cancel")' in _PEOPLE


def test_ures_emberek_panelen_megjelenik_a_mappa_utmutatoja():
    assert 'objectName: "peoplePanelStatusLabel"' in _PEOPLE
    assert 'qsTr("Select a folder to display faces")' in _PEOPLE


def test_a_statuszszoveg_a_foablakban_is_latszik(qml_app, qt_app):
    window, _controller, _engine = qml_app
    window.setProperty("activeDrawerTab", "people")
    label = window.findChild(QObject, "peoplePanelStatusLabel")
    assert label is not None
    panel = window.findChild(QObject, "peoplePanel")
    assert panel is not None
    panel.setProperty("folderSelected", False)

    height = window.height()
    try:
        for delta in (-5, 0, 5):
            window.resize(window.width(), height + delta)
            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline:
                qt_app.processEvents()
                if label.property("visible"):
                    break
                time.sleep(0.01)
            assert label.property("visible")
            assert label.property("text") == "Select a folder to display faces"
    finally:
        window.resize(window.width(), height)


def test_a_kezi_arcbevitel_megse_gombja_a_foablakban_mukodik(qml_app, qt_app):
    window, _controller, _engine = qml_app
    window.setProperty("viewerOpen", True)
    window.setProperty("activeDrawerTab", "people")
    qt_app.processEvents()
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    viewer.setProperty("facesVisible", True)
    viewer.setProperty("facesEditMode", True)
    overlay = window.findChild(QObject, "facesOverlay")
    assert overlay is not None
    overlay.setProperty("draftRect", QRectF(20, 20, 40, 40))
    button = window.findChild(QObject, "peoplePanelManualCancelButton")
    assert button is not None
    assert button.property("text") == "Cancel"
    panel_button = window.findChild(QObject, "peoplePanelManualAddButton")
    assert panel_button is not None
    height = window.height()
    try:
        for delta in (-5, 0, 5):
            window.resize(window.width(), height + delta)
            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline:
                qt_app.processEvents()
                if button.property("visible") and button.width() > 0:
                    break
                time.sleep(0.01)
            assert button.property("visible")
            center = button.mapToScene(
                QPointF(button.width() / 2, button.height() / 2)
            )
            QTest.mouseClick(
                window,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                QPoint(round(center.x()), round(center.y())),
            )
            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline:
                qt_app.processEvents()
                if viewer.property("facesEditMode") is False:
                    break
                time.sleep(0.01)
            assert viewer.property("facesEditMode") is False
            assert overlay.property("draftRect").width() == 0
            assert panel_button.property("visible")
            viewer.setProperty("facesEditMode", True)
            overlay.setProperty("draftRect", QRectF(20, 20, 40, 40))
    finally:
        window.resize(window.width(), height)
