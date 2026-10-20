"""Az Időrend visszakapcsolt belépési pontjai (#1903, #5377)."""

from pathlib import Path

from PySide6.QtCore import QObject

import picasapy.app
from tests.support.qml_blokk import blokk_horgonyra

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_TOOLBAR = (_QML / "MainToolbar.qml").read_text(encoding="utf-8")
_MENU = (_QML / "PicasaMenuBar.qml").read_text(encoding="utf-8")
_MAIN = (_QML.parent / "Main.qml").read_text(encoding="utf-8")


class TestAktivBelepesiPontok:
    def test_a_toolbar_gomb_es_az_aktiv_allapot_megvan(self):
        blokk = blokk_horgonyra(
            _TOOLBAR, 'objectName: "toolbarTimelineButton"'
        )
        assert 'text: qsTr("Timeline")' in blokk
        assert "checked: toolbar.timelineActive" in blokk
        assert "onClicked: toolbar.timelineRequested()" in blokk

    def test_a_menu_es_a_gazdaablak_ugyanazt_a_modot_nyitja(self):
        menu = blokk_horgonyra(_MENU, 'objectName: "menuViewTimeline"')
        assert "enabled: true" in menu
        assert '"\\tCtrl+5"' in menu
        assert "onTriggered: bar.timelineRequested()" in menu
        assert "onTimelineRequested: window.toggleTimeline()" in _MAIN

    def test_a_ctrl5_aktiv_es_nincs_kijelolesi_feltetele(self):
        shortcut = blokk_horgonyra(_MAIN, 'sequence: "Ctrl+5"')
        assert "enabled: false" not in shortcut
        assert "onActivated: window.toggleTimeline()" in shortcut
        assert "selectedIndex" not in shortcut

    def test_a_valodi_menu_es_toolbar_elemenek_aktivak(self, qml_app, qt_app):
        window = qml_app[0]
        menu_item = window.findChild(QObject, "menuViewTimeline")
        toolbar_button = window.findChild(QObject, "toolbarTimelineButton")
        assert menu_item is not None and menu_item.property("enabled") is True
        assert toolbar_button is not None
        assert toolbar_button.property("enabled") is True
        assert toolbar_button.property("visible") is True
