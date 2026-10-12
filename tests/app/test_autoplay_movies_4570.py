"""#4570: az `AutoPlayMovies` beállítás — a videó megnyitáskor elindul-e.

A kapcsoló QSettings-ben (`view/autoPlayMovies`) perzisztens, az alapállapot
a Picasa-paritás szerint BEKAPCSOLT (az eredeti azonnal lejátszotta a videót),
és hibás/kézzel átírt értékből sem lesz más az alapnál.
"""

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.app.appearance_controller import (
    AUTO_PLAY_MOVIES_KEY,
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
    assert controller.autoPlayMovies is True


def test_kikapcsolas_perzisztens(controller):
    controller.setAutoPlayMovies(False)
    assert controller.autoPlayMovies is False
    mentett = controller._get_settings().value(AUTO_PLAY_MOVIES_KEY)
    assert coerce_ui_preference_flag(mentett, default=True) is False


def test_ujraindulas_utan_visszaall(qt_app, tmp_path):
    fajl = str(tmp_path / "settings.ini")
    elso = _Probe(QSettings(fajl, QSettings.Format.IniFormat))
    elso.setAutoPlayMovies(False)
    masodik = _Probe(QSettings(fajl, QSettings.Format.IniFormat))
    assert masodik.autoPlayMovies is False


def test_azonos_ertek_nem_jelez(controller):
    jelzesek = []
    controller.autoPlayMoviesChanged.connect(lambda: jelzesek.append(1))
    controller.setAutoPlayMovies(True)
    assert jelzesek == []
    controller.setAutoPlayMovies(False)
    assert jelzesek == [1]


@pytest.mark.parametrize("ertek", ["hupak", "", None])
def test_hibas_mentett_ertek_az_alapra_esik(qt_app, tmp_path, ertek):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(AUTO_PLAY_MOVIES_KEY, ertek)
    assert _Probe(settings).autoPlayMovies is True
