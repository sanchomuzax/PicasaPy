"""A mappa és az album helyi menüjének Google Fotók-feltöltése (#6849)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from PySide6.QtCore import Qt

import picasapy.app.tray_google_photos_controller as tray_google_photos_controller
import picasapy.google_photos as google_photos
from picasapy.google_photos import HttpResponse, OAuthClient
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import app_epitese, elokeszit
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    gyerek,
    jobbklikk_mappan,
    kattints,
    keres_vizualis,
    kijelol,
    varj,
    zar,
)


class FakePhotosServer:
    def __init__(self):
        self.requests = []
        self.upload_number = 0

    def request(self, method, url, *, headers, body, timeout, cancel_event=None):
        self.requests.append((method, url, dict(headers), body))
        if url.endswith("/token"):
            return HttpResponse(200, b'{"access_token":"access-token","expires_in":3600}')
        if url.endswith("/uploads"):
            self.upload_number += 1
            return HttpResponse(200, f"upload-{self.upload_number}".encode())
        if url.endswith("/mediaItems:batchCreate"):
            items = json.loads(body)["newMediaItems"]
            return HttpResponse(
                200,
                json.dumps(
                    {
                        "newMediaItemResults": [
                            {
                                "status": {"code": 0},
                                "uploadToken": item["simpleMediaItem"]["uploadToken"],
                            }
                            for item in items
                        ]
                    }
                ).encode(),
            )
        raise AssertionError(f"Ismeretlen kérés: {method} {url}")


class FakeKeyring:
    def __init__(self):
        self.values = {}

    def get_password(self, service, username):
        return self.values.get((service, username))

    def set_password(self, service, username, password):
        self.values[(service, username)] = password

    def delete_password(self, service, username):
        self.values.pop((service, username), None)


class FakeLoopbackOAuthSession:
    def __init__(self, _oauth, *, client_id, client_secret):
        self.authorization_url = f"https://accounts.google.test/?client_id={client_id}"

    def wait_for_tokens(self):
        return {"refresh_token": "test-refresh-token"}

    def cancel(self):
        return None


@pytest.fixture
def google_photos_app(qt_app, tmp_path, monkeypatch):
    keyring = FakeKeyring()
    monkeypatch.setattr(google_photos, "keyring", keyring)
    monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_SECRET", "test-client-secret")
    yield from app_epitese(qt_app, tmp_path)


def _nyisd_album_menut(window, qt_app, token: str):
    nev = f"albumItem_{token}"
    assert varj(
        qt_app,
        lambda: (s := keres_vizualis(window, nev)) is not None
        and s.width() > 0
        and s.height() > 0,
    ), f"{nev}: az album sora nem kapott méretet"
    sor = keres_vizualis(window, nev)
    kattints(window, qt_app, sor, Qt.MouseButton.RightButton)
    menu = gyerek(window, "albumContextMenu")
    assert varj(qt_app, lambda: menu.property("visible") is True), (
        "az album jobbklikkje nem nyitotta meg a helyi menüt"
    )
    return menu


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_mappamenu_google_photos_feltoltes_bejelentkezve_feltolti_a_kepeket(
    google_photos_app, qt_app, height_delta
):
    window, controller, _engine = google_photos_app
    alap_magassag = window.property("height")
    window.setProperty("height", alap_magassag + height_delta)
    window.show()
    window.requestActivate()
    qt_app.processEvents()

    cel = elokeszit(window, qt_app, controller)
    controller._google_photos_credentials.set_secret("refresh_token", "test-refresh")
    controller.googlePhotosChanged.emit()
    assert controller.googlePhotosSignedIn is True

    server = FakePhotosServer()
    controller._google_photos_transport = server
    controller._google_photos_oauth = OAuthClient(
        transport=server,
        token_endpoint="https://photos.test/token",
    )

    jobbklikk_mappan(window, qt_app, cel)
    tetel = gyerek(window, "folderMenuUploadToGooglePhotos")
    assert tetel.property("enabled") is True, "a mappa feltöltési tétele legyen aktív"
    assert tetel.property("retired") is not True, "a mappa feltöltési tétele nem lehet retired"

    kattints(window, qt_app, tetel)

    assert varj(qt_app, lambda: not controller.photosUploadRunning), (
        "a mappa feltöltése nem fejeződött be időben"
    )
    assert controller.photosUploadFinished is True
    batch = [
        request
        for request in server.requests
        if request[1].endswith("/mediaItems:batchCreate")
    ]
    assert len(batch) == 1
    names = [
        item["simpleMediaItem"]["fileName"]
        for item in json.loads(batch[0][3])["newMediaItems"]
    ]
    assert names == ["a_nagy.jpg", "b_kicsi.jpg", "c_kozepes.jpg"]

    dialog = gyerek(window, "googlePhotosUploadDialog")
    assert varj(qt_app, lambda: dialog.property("visible")), (
        "a feltöltési párbeszédablaknak látszania kell"
    )
    zar(qt_app, dialog)


def test_mappamenu_google_photos_feltoltes_bejelentkezes_nelkul_bejelentkezest_indit(
    google_photos_app, qt_app, monkeypatch
):
    window, controller, _engine = google_photos_app
    window.show()
    window.requestActivate()
    qt_app.processEvents()

    cel = elokeszit(window, qt_app, controller)
    controller.googlePhotosChanged.emit()
    assert controller.googlePhotosSignedIn is False

    megnyitott_url = []
    monkeypatch.setattr(
        google_photos, "LoopbackOAuthSession", FakeLoopbackOAuthSession
    )
    monkeypatch.setattr(
        tray_google_photos_controller,
        "QDesktopServices",
        SimpleNamespace(
            openUrl=lambda url: megnyitott_url.append(url.toString()) or True
        ),
    )

    jobbklikk_mappan(window, qt_app, cel)
    tetel = gyerek(window, "folderMenuUploadToGooglePhotos")
    assert tetel.property("enabled") is True
    assert tetel.property("retired") is not True

    kattints(window, qt_app, tetel)

    assert varj(qt_app, lambda: len(megnyitott_url) == 1), (
        "bejelentkezés hiányában az OAuth bejelentkezési útnak kell elindulnia"
    )
    assert "https://accounts.google.test/" in megnyitott_url[0]


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_albummenu_google_photos_feltoltes_bejelentkezve_feltolti_az_albumot(
    google_photos_app, qt_app, height_delta
):
    window, controller, _engine = google_photos_app
    alap_magassag = window.property("height")
    window.setProperty("height", alap_magassag + height_delta)
    window.show()
    window.requestActivate()
    qt_app.processEvents()

    elokeszit(window, qt_app, controller)
    kijelol(window, qt_app, [0, 2])
    token = controller.createAlbum("TestAlbum", [0, 2])
    assert token, "az album nem jött létre"

    controller._google_photos_credentials.set_secret("refresh_token", "test-refresh")
    controller.googlePhotosChanged.emit()
    assert controller.googlePhotosSignedIn is True

    server = FakePhotosServer()
    controller._google_photos_transport = server
    controller._google_photos_oauth = OAuthClient(
        transport=server,
        token_endpoint="https://photos.test/token",
    )

    _nyisd_album_menut(window, qt_app, token)
    tetel = gyerek(window, "albumMenuUploadToGooglePhotos")
    assert tetel.property("enabled") is True, "az album feltöltési tétele legyen aktív"
    assert tetel.property("retired") is not True, "az album feltöltési tétele nem lehet retired"

    kattints(window, qt_app, tetel)

    assert varj(qt_app, lambda: not controller.photosUploadRunning), (
        "az album feltöltése nem fejeződött be időben"
    )
    assert controller.photosUploadFinished is True
    batch = [
        request
        for request in server.requests
        if request[1].endswith("/mediaItems:batchCreate")
    ]
    assert len(batch) == 1
    names = [
        item["simpleMediaItem"]["fileName"]
        for item in json.loads(batch[0][3])["newMediaItems"]
    ]
    assert names == ["a_nagy.jpg", "c_kozepes.jpg"]

    dialog = gyerek(window, "googlePhotosUploadDialog")
    assert varj(qt_app, lambda: dialog.property("visible")), (
        "a feltöltési párbeszédablaknak látszania kell"
    )
    zar(qt_app, dialog)


def test_albummenu_google_photos_feltoltes_bejelentkezes_nelkul_bejelentkezest_indit(
    google_photos_app, qt_app, monkeypatch
):
    window, controller, _engine = google_photos_app
    window.show()
    window.requestActivate()
    qt_app.processEvents()

    elokeszit(window, qt_app, controller)
    kijelol(window, qt_app, [1])
    token = controller.createAlbum("TestAlbum2", [1])
    assert token, "az album nem jött létre"

    controller.googlePhotosChanged.emit()
    assert controller.googlePhotosSignedIn is False

    megnyitott_url = []
    monkeypatch.setattr(
        google_photos, "LoopbackOAuthSession", FakeLoopbackOAuthSession
    )
    monkeypatch.setattr(
        tray_google_photos_controller,
        "QDesktopServices",
        SimpleNamespace(
            openUrl=lambda url: megnyitott_url.append(url.toString()) or True
        ),
    )

    _nyisd_album_menut(window, qt_app, token)
    tetel = gyerek(window, "albumMenuUploadToGooglePhotos")
    assert tetel.property("enabled") is True
    assert tetel.property("retired") is not True

    kattints(window, qt_app, tetel)

    assert varj(qt_app, lambda: len(megnyitott_url) == 1), (
        "bejelentkezés hiányában az OAuth bejelentkezési útnak kell elindulnia"
    )
    assert "https://accounts.google.test/" in megnyitott_url[0]
