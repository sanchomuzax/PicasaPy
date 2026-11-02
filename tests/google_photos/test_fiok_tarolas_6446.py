"""A belépett Google-fiók tárolása a tálca-vezérlőben (#6446).

A hálózatot és a rendszerkulcstartót a teszt helyettesíti: a kijelentkezés
revokálását egy rögzítő transport kapja meg, nem a valódi Google-végpont.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QSettings

import picasapy.google_photos as google_photos
from picasapy.app.tray_google_photos_controller import TrayGooglePhotosMixin
from support.google_fiok import PROBA_EMAIL, PROBA_REFRESH


class _HamisKulcstarto:
    def __init__(self):
        self.values = {}

    def get_password(self, service, username):
        return self.values.get((service, username))

    def set_password(self, service, username, password):
        self.values[(service, username)] = password

    def delete_password(self, service, username):
        self.values.pop((service, username), None)


class _RogzitoTransport:
    def __init__(self):
        self.kerek = []

    def request(self, method, url, headers=None, body=None, timeout=None):
        self.kerek.append((method, url, body))
        return google_photos.HttpResponse(200, b"")


class _Hoszt(TrayGooglePhotosMixin, QObject):
    """A tálca-vezérlő minimális gazdája: a beállítás egy eldobható ini-fájl."""

    def __init__(self, beallitas: QSettings):
        super().__init__()
        self._beallitas = beallitas

    def _get_settings(self) -> QSettings:
        return self._beallitas

    def _start_background(self, target, **_kwargs):
        target()


def _hoszt(tmp_path, monkeypatch):
    monkeypatch.setattr(google_photos, "keyring", _HamisKulcstarto())
    monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_SECRET", "test-client-secret")
    beallitas = QSettings(str(tmp_path / "beallitas.ini"), QSettings.Format.IniFormat)
    hoszt = _Hoszt(beallitas)
    hoszt._ensure_google_photos_wired()
    rogzito = _RogzitoTransport()
    hoszt._google_photos_oauth = google_photos.OAuthClient(transport=rogzito)
    return hoszt, rogzito


def test_a_bejelentkezes_menti_a_fiok_azonositojat(tmp_path, monkeypatch):
    hoszt, _rogzito = _hoszt(tmp_path, monkeypatch)

    hoszt._on_google_photos_auth_result(PROBA_REFRESH, "", PROBA_EMAIL)

    assert hoszt.property("googlePhotosAccount") == PROBA_EMAIL
    assert hoszt._google_photos_credentials.get_secret("refresh_token") == PROBA_REFRESH


def test_fiok_nelkul_bejelentkezes_ures_fiokot_ad(tmp_path, monkeypatch):
    hoszt, _rogzito = _hoszt(tmp_path, monkeypatch)

    hoszt._on_google_photos_auth_result(PROBA_REFRESH, "", "")

    assert hoszt.property("googlePhotosAccount") == ""


def test_hibas_bejelentkezes_nem_hagy_fiokot(tmp_path, monkeypatch):
    hoszt, _rogzito = _hoszt(tmp_path, monkeypatch)

    hoszt._on_google_photos_auth_result("", "auth_failed", "")

    assert hoszt.property("googlePhotosAccount") == ""
    assert hoszt._google_photos_credentials.get_secret("refresh_token") == ""


def test_a_kijelentkezes_torli_a_tokent_es_a_fiokot_es_revokal(tmp_path, monkeypatch):
    hoszt, rogzito = _hoszt(tmp_path, monkeypatch)
    hoszt._on_google_photos_auth_result(PROBA_REFRESH, "", PROBA_EMAIL)

    hoszt.signOutGooglePhotos()

    assert hoszt.property("googlePhotosAccount") == ""
    assert hoszt._google_photos_credentials.get_secret("refresh_token") == ""
    assert [(metodus, url) for metodus, url, _body in rogzito.kerek] == [
        ("POST", google_photos.GOOGLE_OAUTH_REVOKE_URL)
    ]


def test_a_lejart_token_utan_nem_marad_fiok(tmp_path, monkeypatch):
    hoszt, _rogzito = _hoszt(tmp_path, monkeypatch)
    hoszt._on_google_photos_auth_result(PROBA_REFRESH, "", PROBA_EMAIL)

    hoszt._on_photos_upload_result("token_expired", False, 1)

    assert hoszt.property("googlePhotosAccount") == ""
