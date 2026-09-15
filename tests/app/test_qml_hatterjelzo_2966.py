"""#2966 — a jobb-felső sarki, KÖZÖS háttérművelet-jelző felülete.

Amit a jegy „Kész, ha" listája kér, és amit ez a fájl mér:

* a jelző munka NÉLKÜL rejtve van;
* bármelyik, a közös nyilvántartásba bejelentkezett háttérmunka futásakor
  magától megjelenik;
* a megszakítás gombja CSAK akkor látszik, ha a futó munkának van
  leállítója (az eredeti szerkesztő-példánya, `editpanelactivity`, gomb
  nélküli — #3112);
* a megszakítás tényleg leállítja a műveletet (a bejelentkezett visszahívás
  meghívódik).

A geometriát (35 × 28, felülről 5, jobbról 5) a `respack.yt` mérése adja.
⚠️ A LÁTVÁNYT ez a teszt nem méri — arra referencia-képernyőkép kellene.
"""

import time

import pytest
from PySide6.QtCore import QObject

from picasapy.app import busy_registry as busy_registry_module
from picasapy.app.busy_registry import get_app_busy_registry, reset_app_busy_registry

_TEST_SHOW_DELAY_MS = 40
_TEST_MIN_VISIBLE_MS = 60


@pytest.fixture(autouse=True)
def _kis_busy_idozitesek(monkeypatch):
    monkeypatch.setattr(busy_registry_module, "SHOW_DELAY_MS", _TEST_SHOW_DELAY_MS)
    monkeypatch.setattr(busy_registry_module, "MIN_VISIBLE_MS", _TEST_MIN_VISIBLE_MS)
    reset_app_busy_registry()
    yield
    reset_app_busy_registry()


def _gyerek(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _varj(qt_app, feltetel, timeout_s=2.0):
    hatarido = time.monotonic() + timeout_s
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.005)
    return False


class TestHatterjelzo:
    def test_munka_nelkul_rejtve(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        jelzo = _gyerek(window, "activityBadge")
        assert _varj(qt_app, lambda: not controller.isWorking)
        assert jelzo.property("visible") is False

    def test_a_merete_a_mert_35x28(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        jelzo = _gyerek(window, "activityBadge")
        assert jelzo.property("width") == 35
        assert jelzo.property("height") == 28

    def test_a_jobb_felso_sarokban_all(self, qml_app, qt_app):
        """Felülről 5, jobbról 5 képpont (a `respack.yt` mérése, #3112)."""
        window, _controller, _lib, _engine = qml_app
        jelzo = _gyerek(window, "activityBadge")
        szulo = jelzo.parent()
        assert jelzo.property("y") == 5
        assert (
            szulo.property("width") - jelzo.property("x") - jelzo.property("width")
        ) == 5

    def test_hattermunkara_megjelenik(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        jelzo = _gyerek(window, "activityBadge")
        assert _varj(qt_app, lambda: not controller.isWorking)

        get_app_busy_registry().begin()
        assert _varj(qt_app, lambda: jelzo.property("visible") is True), (
            "a háttérmunka nem hozta elő a jelzőt"
        )
        get_app_busy_registry().end()
        assert _varj(qt_app, lambda: jelzo.property("visible") is False)

    def test_leallito_nelkuli_munkanal_nincs_gomb(self, qml_app, qt_app):
        """A bélyegkép-betöltés fut, de nincs mivel leállítani — a jelző
        pörögjön, a gomb maradjon rejtve."""
        window, controller, _lib, _engine = qml_app
        gomb = _gyerek(window, "activityBadgeCancel")
        get_app_busy_registry().begin()
        assert _varj(qt_app, lambda: controller.isWorking is True)
        assert gomb.property("visible") is False
        get_app_busy_registry().end()

    def test_leallithato_munkanal_megjelenik_a_gomb(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        gomb = _gyerek(window, "activityBadgeCancel")
        nyilvantarto = get_app_busy_registry()
        nyilvantarto.begin()
        jegy = nyilvantarto.register_cancel(lambda: None)
        assert _varj(qt_app, lambda: gomb.property("visible") is True), (
            "a leállítható munka nem hozta elő a megszakítás gombját"
        )
        nyilvantarto.unregister_cancel(jegy)
        assert _varj(qt_app, lambda: gomb.property("visible") is False)
        nyilvantarto.end()

    def test_a_megszakitas_tenyleg_leallit(self, qml_app, qt_app):
        """A vezérlő `cancelActivity()`-je a bejelentkezett leállítót hívja."""
        window, controller, _lib, _engine = qml_app
        nyilvantarto = get_app_busy_registry()
        hivasok = []
        nyilvantarto.begin()
        nyilvantarto.register_cancel(lambda: hivasok.append("leall"))
        assert _varj(qt_app, lambda: controller.activityCancellable is True)

        controller.cancelActivity()
        assert hivasok == ["leall"]
        nyilvantarto.end()

    def test_a_megerosito_parbeszed_letezik_es_nem_modalisan_all(self, qml_app, qt_app):
        """A gomb NEM állít le azonnal: az eredetiben megerősítő kérdés
        jött. A párbeszéd legyen ott, és alapból zárva."""
        window, _controller, _lib, _engine = qml_app
        parbeszed = _gyerek(window, "activityCancelConfirm")
        assert parbeszed.property("visible") is False
