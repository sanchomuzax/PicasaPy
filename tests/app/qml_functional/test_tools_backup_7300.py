"""#7300: a Képek biztonsági mentése nem nyitja újra a kiadás-panelt."""

from __future__ import annotations

import threading

import pytest
from PySide6.QtCore import QObject, QMetaObject, Qt

from tests.app.qml_functional._fomenu_4420_menu import _kattints, _megnyit
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _objektum
from tests.support.varakozas import var_feltetelre

_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)


def _elem(window, object_name: str):
    elem = _objektum(window, object_name)
    assert elem is not None, f"{object_name} nem található a főablakban"
    return elem


def _nyisd_meg_panelt(window, qt_app, menu_title: str, item_name: str):
    menu_bar = window.property("menuBar")
    _megnyit(menu_bar, qt_app, menu_title)
    item = _elem(window, item_name)
    assert item.property("visible") is True, f"{item_name} nem látható"
    _kattints(qt_app, item)
    return item


def _allitsd_be_az_ablakmagassagot(window, qt_app, eltolás: int) -> None:
    window.setHeight(window.height() + eltolás)
    qt_app.processEvents()


@pytest.mark.parametrize(
    ("menu_title", "panel_item", "host_name", "cancel_name"),
    (
        ("&Tools", "menuToolsBackup", "backupHost", "publishBackupCancel"),
        ("&Create", "menuCreateGiftCd", "giftCdHost", "publishPresentCdCancel"),
    ),
    ids=("mentes-panel", "ajandek-cd-panel"),
)
@pytest.mark.parametrize("magassag_eltolas", _ABLAKMAGASSAG_ELTOLASOK)
def test_mentes_menupont_letiltva_nyitott_kiadas_panelnel(
    qml_app, qt_app, menu_title, panel_item, host_name, cancel_name,
    magassag_eltolas,
):
    window, _controller, _engine = qml_app
    window.show()
    window.requestActivate()
    _allitsd_be_az_ablakmagassagot(window, qt_app, magassag_eltolas)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    _nyisd_meg_panelt(window, qt_app, menu_title, panel_item)
    host = window.findChild(QObject, host_name)
    assert host is not None, f"{host_name} nem található"
    assert var_feltetelre(
        qt_app, lambda: host.property("visible") is True, 3.0
    ), f"a {host_name} panel nem nyílt meg kattintásra"

    backup_item = _elem(window, "menuToolsBackup")
    assert backup_item.property("enabled") is False, (
        "nyitott mentés- vagy Ajándék-CD panel mellett a mentés menüpont "
        "aktív maradt"
    )

    _kattints(qt_app, _elem(window, cancel_name))
    assert var_feltetelre(
        qt_app, lambda: host.property("visible") is False, 3.0
    ), f"a {host_name} panel nem záródott be"
    backup_item = _elem(window, "menuToolsBackup")
    assert backup_item.property("enabled") is True, (
        "a bezárt kiadás-panel után a mentés menüpont nem állt vissza"
    )


@pytest.mark.parametrize("magassag_eltolas", _ABLAKMAGASSAG_ELTOLASOK)
def test_futo_masolas_kozben_a_mentes_panel_nem_nyithato_ujra(
    qml_app, qt_app, tmp_path, monkeypatch, magassag_eltolas
):
    window, _controller, engine = qml_app
    monkeypatch.setattr(
        "picasapy.app.backup_controller._kepek_mappaja",
        lambda: str(tmp_path / "Kepek"),
    )
    from picasapy.app.backup_controller import BackupController

    backup_controller = BackupController(
        tmp_path / "index.db", (str(tmp_path / "kepek"),)
    )
    engine.rootContext().setContextProperty("backupController", backup_controller)
    assert backup_controller.ujKeszlet(
        "Próba mentés", str(tmp_path / "biztonsagi-mentes"), "minden", "lemez"
    ), "a próba mentési készlet nem jött létre"
    keszlet_id = backup_controller.keszletek()[0]["id"]
    assert backup_controller.terv(keszlet_id)["darab"] > 0, (
        "a próbamappában nincs másolható kép"
    )

    window.show()
    window.requestActivate()
    _allitsd_be_az_ablakmagassagot(window, qt_app, magassag_eltolas)
    backup_item = _elem(window, "menuToolsBackup")
    assert QMetaObject.invokeMethod(
        backup_item, "triggered", Qt.ConnectionType.DirectConnection
    ), "a mentés menüpont nem indítható"
    qt_app.processEvents()
    host = window.findChild(QObject, "backupHost")
    assert host is not None
    assert host.property("nyitva") is True

    import picasapy.app.backup_controller as backup_module

    masolas_elindult = threading.Event()
    masolas_mehet = threading.Event()
    eredeti_futtasd = backup_module.futtasd

    def tartsd_fel_a_masolast(*args, **kwargs):
        masolas_elindult.set()
        masolas_mehet.wait(10.0)
        return eredeti_futtasd(*args, **kwargs)

    monkeypatch.setattr(backup_module, "futtasd", tartsd_fel_a_masolast)
    backup_controller.futtasdMost(keszlet_id, None)
    try:
        assert var_feltetelre(qt_app, masolas_elindult.is_set, 10.0), (
            "a háttérmásolás nem indult el"
        )
        # A qml_app a főablak betöltése után adja a próba-vezérlőt a
        # QML-környezethez, ezért a BackupHost Connections-je nem figyeli a
        # vezérlő futasIndult jelét. A blokkolt futtaspéldány mellett itt a
        # jelzés által beállított felületi állapotot állítjuk be.
        host.setProperty("fut", True)
        assert host.property("fut") is True
        _kattints(qt_app, _elem(window, "publishBackupCancel"))
        assert var_feltetelre(
            qt_app, lambda: host.property("visible") is False, 3.0
        ), "a mentés-panel nem záródott be a futó másolás mellett"
        assert host.property("fut") is True, "a bezárás megszakította a másolást"

        backup_item = _elem(window, "menuToolsBackup")
        assert backup_item.property("enabled") is False, (
            "futó másolás mellett újra nyitható maradt a mentés-panel"
        )
        assert host.property("nyitva") is False
    finally:
        masolas_mehet.set()

    assert backup_controller.waitForBackgroundWorkers(10.0), (
        "a próbamásolás nem fejeződött be"
    )
    host.setProperty("fut", False)
    qt_app.processEvents()


@pytest.mark.parametrize("magassag_eltolas", _ABLAKMAGASSAG_ELTOLASOK)
def test_a_mentes_menupont_nem_dob_hibat_ha_a_gazdak_meg_hianyoznak(
    qml_app, qt_app, magassag_eltolas
):
    """A főablak építésekor a menüsor hamarabb létezik, mint a két panel gazdája:
    a kötés `undefined` gazdánál sem szólhat QML-hibát (a `qml_warnings` őr
    a teszt végén jelzi), és gazda nélkül a panel nincs nyitva, a pont aktív."""
    window, _controller, _engine = qml_app
    window.show()
    window.requestActivate()
    _allitsd_be_az_ablakmagassagot(window, qt_app, magassag_eltolas)
    menu_bar = window.property("menuBar")
    backup_item = _elem(window, "menuToolsBackup")

    for nev in ("hostBackupHost", "hostGiftCdHost"):
        assert menu_bar.setProperty(nev, None), f"{nev} nem állítható"
        qt_app.processEvents()
        assert menu_bar.property(nev) is None, f"{nev} nem lett üres"

    assert backup_item.property("enabled") is True, (
        "gazdák nélkül a mentés menüpont nem lehet szürke: a panel nincs nyitva"
    )
