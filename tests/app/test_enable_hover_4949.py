"""#4949: a Ctrl+Alt felugró előnézet a saját `EnableHover` kapcsolóját olvassa.

A kapcsoló QSettings-ben (`view/enableHover`) perzisztens, az alapállapot
BEKAPCSOLT (a mai viselkedés is alapból mutatja az előnézetet), és a
buboréksúgó (`view/showTooltips`) nem befolyásolja.
"""

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.app.appearance_controller import (
    ENABLE_HOVER_KEY,
    AppearanceMixin,
    coerce_ui_preference_flag,
)


class _Probe(AppearanceMixin, QObject):
    def __init__(self, settings):
        super().__init__()
        self._settings = settings
        self._init_appearance()

    def _get_settings(self):
        return self._settings


@pytest.fixture
def controller(qt_app, tmp_path):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return _Probe(settings)


def test_alapertelmezes_bekapcsolt(controller):
    assert controller.enableHover is True


def test_kikapcsolas_perzisztens(controller):
    controller.setEnableHover(False)
    assert controller.enableHover is False
    mentett = controller._get_settings().value(ENABLE_HOVER_KEY)
    assert coerce_ui_preference_flag(mentett, default=True) is False


def test_ujraindulas_utan_visszaall(qt_app, tmp_path):
    fajl = str(tmp_path / "settings.ini")
    elso = _Probe(QSettings(fajl, QSettings.Format.IniFormat))
    elso.setEnableHover(False)
    masodik = _Probe(QSettings(fajl, QSettings.Format.IniFormat))
    assert masodik.enableHover is False


def test_buboreksugo_nem_erinti(controller):
    controller.setShowTooltipsEnabled(False)
    assert controller.enableHover is True
    controller.setEnableHover(False)
    controller.setShowTooltipsEnabled(True)
    assert controller.enableHover is False


def test_azonos_ertek_nem_jelez(controller):
    jelzesek = []
    controller.enableHoverChanged.connect(lambda: jelzesek.append(1))
    controller.setEnableHover(True)
    assert jelzesek == []
    controller.setEnableHover(False)
    assert jelzesek == [1]


@pytest.mark.parametrize("ertek", ["hupak", "", None])
def test_hibas_mentett_ertek_az_alapra_esik(qt_app, tmp_path, ertek):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(ENABLE_HOVER_KEY, ertek)
    assert _Probe(settings).enableHover is True
