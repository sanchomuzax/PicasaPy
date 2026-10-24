"""#5704: a felhasználói gyűjtemények jelszava külön tárolódik és kapuz."""

from __future__ import annotations

import json

from PySide6.QtCore import QObject, QSettings

from picasapy.app.custom_collections import CUSTOM_COLLECTIONS_SETTING_KEY
from picasapy.app.custom_collections_controller import CustomCollectionsMixin


class _Host(CustomCollectionsMixin, QObject):
    def __init__(self, settings):
        super().__init__()
        self._settings = settings

    def _get_settings(self):
        return self._settings


def _host(path):
    settings = QSettings(str(path), QSettings.Format.IniFormat)
    return _Host(settings)


def test_a_jelszo_gyujtemenyenkent_tarolodik_es_nem_kerul_nyiltan_a_beallitasba(
    tmp_path,
):
    host = _host(tmp_path / "settings.ini")
    host.createCollection("Család")
    host.createCollection("Munka")

    assert host.setCollectionPassword("Család", "csalad-titok", "csalad-titok")

    assert host.collectionPasswordSet("Család") is True
    assert host.collectionPasswordSet("Munka") is False
    assert host.collectionPasswordLocked("Család") is True
    assert host.unlockCollection("Munka", "csalad-titok") is False
    assert host.unlockCollection("Család", "rossz") is False
    assert host.collectionPasswordLocked("Család") is True
    assert host.unlockCollection("Család", "csalad-titok") is True
    assert host.collectionPasswordLocked("Család") is False
    assert host.collectionPasswordLocked("Munka") is False

    raw = host._get_settings().value(CUSTOM_COLLECTIONS_SETTING_KEY)
    adat = json.loads(raw)
    csalad = next(item for item in adat if item["name"] == "Család")
    munka = next(item for item in adat if item["name"] == "Munka")
    assert csalad["password_hash"] != "csalad-titok"
    assert csalad["password_hash"]
    assert "password_hash" not in munka or not munka["password_hash"]


def test_jelszocsere_es_torles_rossz_regi_jelszoval_nem_megy(tmp_path):
    host = _host(tmp_path / "settings.ini")
    host.createCollection("Utazás")
    assert host.setCollectionPassword("Utazás", "régi", "régi")
    eredeti = json.loads(
        host._get_settings().value(CUSTOM_COLLECTIONS_SETTING_KEY)
    )[0]["password_hash"]

    assert host.changeCollectionPassword("Utazás", "hibás", "új", "új") is False
    assert host.clearCollectionPassword("Utazás", "hibás") is False
    assert json.loads(
        host._get_settings().value(CUSTOM_COLLECTIONS_SETTING_KEY)
    )[0]["password_hash"] == eredeti

    assert host.changeCollectionPassword("Utazás", "régi", "új", "új") is True
    assert host.verifyCollectionPassword("Utazás", "régi") is False
    assert host.verifyCollectionPassword("Utazás", "új") is True
    assert host.clearCollectionPassword("Utazás", "régi") is False
    assert host.clearCollectionPassword("Utazás", "új") is True
    assert host.collectionPasswordSet("Utazás") is False


def test_a_jelszo_atnevezeskor_a_gyujtemennyel_marad_es_torleskor_elveszik(
    tmp_path,
):
    host = _host(tmp_path / "settings.ini")
    host.createCollection("Régi név")
    assert host.setCollectionPassword("Régi név", "titok", "titok")

    host.renameCollection("Régi név", "Új név")
    assert host.verifyCollectionPassword("Új név", "titok") is True
    assert host.collectionPasswordSet("Régi név") is False

    host.deleteCollection("Új név")
    host.createCollection("Új név")
    assert host.collectionPasswordSet("Új név") is False
    assert host.unlockCollection("Új név", "titok") is False


def test_uj_peldanyban_a_jelszo_megmarad_de_a_feloldas_nem(tmp_path):
    path = tmp_path / "settings.ini"
    host = _host(path)
    host.createCollection("Privát")
    assert host.setCollectionPassword("Privát", "titok", "titok")
    assert host.unlockCollection("Privát", "titok") is True

    masik_peldany = _host(path)
    assert masik_peldany.collectionPasswordSet("Privát") is True
    assert masik_peldany.collectionPasswordLocked("Privát") is True
