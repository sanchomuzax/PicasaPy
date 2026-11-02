"""#2966 - a könyvtárnézet-panel jobb felső sarkában álló közös jelző.

Amit a jegy „Kész, ha" listája kér, és amit ez a fájl mér:

* a jelző munka NÉLKÜL rejtve van;
* bármelyik, a közös nyilvántartásba bejelentkezett háttérmunka futásakor
  magától megjelenik;
* a megszakítás gombja CSAK akkor látszik, ha a futó munkának van
  leállítója (az eredeti szerkesztő-példánya, `editpanelactivity`, gomb
  nélküli — #3112);
* a megszakítás tényleg leállítja a műveletet (a bejelentkezett visszahívás
  meghívódik).

Geometria: 35 × 28 px, a könyvtárnézet-panel tetejétől és jobb szélétől 5 px.
A panelhez viszonyított renderelt elhelyezést a #6405 tesztje is ellenőrzi.
"""


import pytest
from PySide6.QtCore import QObject

from picasapy.app import busy_registry as busy_registry_module
from picasapy.app.busy_registry import get_app_busy_registry, reset_app_busy_registry
from tests.support.varakozas import var_feltetelre

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


def _qml_item_benne(root, name):
    if root.objectName() == name:
        return True
    return any(_qml_item_benne(child, name) for child in root.childItems())


def _varj(qt_app, feltetel, timeout_s=10.0):
    return var_feltetelre(qt_app, feltetel, timeout_s)


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
        """A jelző a könyvtárnézet paneljéhez tartozik (#3112, #6405)."""
        window, _controller, _lib, _engine = qml_app
        jelzo = _gyerek(window, "activityBadge")
        szulo = jelzo.parentItem()
        tartalom = _gyerek(window, "unnamedFacesView")
        assert szulo is not None
        assert szulo != window.contentItem(), "a jelző még mindig a teljes ablakhoz tartozik"
        assert _qml_item_benne(szulo, tartalom.objectName()), (
            "a jelző szülője nem a könyvtárnézet-panel"
        )
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

    def test_a_megerosito_parbeszed_HALASZTVA_epul(self, qml_app, qt_app):
        """A gomb NEM állít le azonnal: az eredetiben megerősítő kérdés
        jött. A párbeszéd a #1719/#1720 szerint HALASZTOTT — induláskor
        csak a betöltője áll ott, maga a dialógus még nincs felépítve."""
        window, _controller, _lib, _engine = qml_app
        _gyerek(window, "activityCancelConfirmLoader")  # a betöltő ott van
        assert window.findChild(QObject, "activityCancelConfirm") is None, (
            "a párbeszéd MINDEN induláskor felépül — halasztani kell (#1719)"
        )
