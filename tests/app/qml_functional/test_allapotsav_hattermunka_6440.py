"""#6440: az alsó állapotsáv kiírja, min dolgozik a program (élő QML-fa).

Háttérmunka közben a sáv a munka nevét mutatja, a munka végén visszaáll az
alap felirat. A Súgó menü pipás tétele kapcsolja, és a beállítás túléli a
kilépést. A menütételt a projekt szabálya szerint VALÓDI kattintással
működtetjük (`toggle()` és `triggered`), nem a metódust hívjuk.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QMetaObject, QObject, QSettings, Qt

import picasapy.app.busy_registry as busy_registry_module
from picasapy.app.activity_status_mixin import (
    ACTIVITY_STATUS_KEY,
    activity_status_enabled_from,
)
from picasapy.app.busy_registry import get_app_busy_registry, reset_app_busy_registry
from tests.support.varakozas import var_feltetelre

TETEL = "menuHelpActivityStatus"
SAV = "trayInfoText"


@pytest.fixture(autouse=True)
def _kis_busy_idozitesek(monkeypatch):
    monkeypatch.setattr(busy_registry_module, "SHOW_DELAY_MS", 40)
    monkeypatch.setattr(busy_registry_module, "MIN_VISIBLE_MS", 60)
    reset_app_busy_registry()
    yield
    reset_app_busy_registry()


def _nev(window, nev: str):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található a QML-fában"
    return obj


def _kattints(tetel):
    """A valódi kattintás mindkét lépése, a QML sorrendjében."""
    QMetaObject.invokeMethod(tetel, "toggle", Qt.ConnectionType.DirectConnection)
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)


def _sav_szovege(window) -> str:
    return _nev(window, SAV).property("text")


class TestMenupont:
    def test_a_pipas_tetel_letezik_es_alapbol_be_van(self, qml_app):
        window, controller, _engine = qml_app
        tetel = _nev(window, TETEL)
        assert tetel.property("checkable") is True
        assert tetel.property("sajat") is True
        assert controller.statusActivityEnabled is True
        assert tetel.property("checked") is True

    def test_a_kattintas_kikapcsolja_es_a_pipa_kovet(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        tetel = _nev(window, TETEL)
        try:
            _kattints(tetel)
            qt_app.processEvents()
            assert controller.statusActivityEnabled is False
            assert tetel.property("checked") is False
            _kattints(tetel)
            qt_app.processEvents()
            assert controller.statusActivityEnabled is True
            assert tetel.property("checked") is True
        finally:
            controller.setStatusActivityEnabled(True)

    def test_a_beallitas_tartosan_mentodik(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        tetel = _nev(window, TETEL)
        try:
            _kattints(tetel)
            qt_app.processEvents()
            settings = controller._get_settings()
            settings.sync()
            ujra = QSettings(settings.fileName(), QSettings.Format.IniFormat)
            assert ujra.value(ACTIVITY_STATUS_KEY) in ("false", False)
            assert activity_status_enabled_from(ujra) is False
        finally:
            controller.setStatusActivityEnabled(True)


class TestAllapotsav:
    def test_bekapcsolva_a_munka_neve_latszik_es_utana_visszaall(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setStatusActivityEnabled(True)
        assert var_feltetelre(qt_app, lambda: not controller.isWorking, 3.0)
        alap = _sav_szovege(window)
        reg = get_app_busy_registry()
        jegy = reg.begin("Exporting photos")
        try:
            assert var_feltetelre(
                qt_app, lambda: _sav_szovege(window) == "Exporting photos", 3.0
            ), "munka közben a sáv nem a munka nevét mutatta"
            assert _nev(window, SAV).property("visible") is True
        finally:
            reg.end(jegy)
        assert var_feltetelre(
            qt_app, lambda: _sav_szovege(window) == alap, 3.0
        ), "a munka végén nem állt vissza az alap felirat"

    def test_kikapcsolva_munka_kozben_is_az_alap_felirat_marad(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setStatusActivityEnabled(False)
        try:
            assert var_feltetelre(qt_app, lambda: not controller.isWorking, 3.0)
            alap = _sav_szovege(window)
            reg = get_app_busy_registry()
            jegy = reg.begin("Exporting photos")
            try:
                assert var_feltetelre(qt_app, lambda: controller.isWorking is True, 3.0)
                vege = time.monotonic() + 0.3
                while time.monotonic() < vege:
                    qt_app.processEvents()
                    assert _sav_szovege(window) == alap, (
                        "kikapcsolt állapotban a munka neve felülírta a sávot"
                    )
                    time.sleep(0.01)
            finally:
                reg.end(jegy)
            assert var_feltetelre(qt_app, lambda: not controller.isWorking, 3.0)
            assert _sav_szovege(window) == alap
        finally:
            controller.setStatusActivityEnabled(True)

    def test_tobb_munkanal_a_legfrissebb_es_a_darabszam_latszik(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setStatusActivityEnabled(True)
        assert var_feltetelre(qt_app, lambda: not controller.isWorking, 3.0)
        reg = get_app_busy_registry()
        elso = reg.begin("Exporting photos")
        masodik = reg.begin("Creating backup image")
        try:
            assert var_feltetelre(
                qt_app,
                lambda: _sav_szovege(window) == "Creating backup image (+1 more)",
                3.0,
            ), "két munkánál a legfrissebb neve és a darabszám nem látszik"
            reg.end(masodik)
            assert var_feltetelre(
                qt_app, lambda: _sav_szovege(window) == "Exporting photos", 3.0
            ), "a befejezett munka után nem a maradék munka neve látszik"
        finally:
            reg.end(elso)
