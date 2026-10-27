"""Google Photos tálcafeltöltés valódi QML-kattintással (#5976)."""

from __future__ import annotations

import json

import pytest
from PySide6.QtQuick import QQuickItem

import picasapy.google_photos as google_photos
from picasapy.google_photos import HttpResponse, OAuthClient
from conftest import _build_qml_app
from tests.app.qml_functional.test_talca_eszkoztar_valodi_5150 import (
    _gyerek,
    _kattints,
    _sor,
    _varj,
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
                            {"status": {"code": 0},
                             "uploadToken": item["simpleMediaItem"]["uploadToken"]}
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


@pytest.fixture
def google_photos_fakes(monkeypatch):
    keyring = FakeKeyring()
    monkeypatch.setattr(google_photos, "keyring", keyring)
    yield keyring


@pytest.fixture
def google_photos_app(qt_app, tmp_path, google_photos_fakes, request):
    yield from _build_qml_app(qt_app, tmp_path, keep_modul=request.module)


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_zold_gomb_valodi_kattintasa_a_talcat_sorrendben_tolti_fel(
    google_photos_app, google_photos_fakes, qt_app, height_delta
):
    window, controller, _engine = google_photos_app
    alap_magassag = window.property("height")
    window.setProperty("height", alap_magassag + height_delta)
    qt_app.processEvents()
    gomb = _gyerek(window, "trayUploadButton", QQuickItem)

    assert gomb.property("enabled") is False
    controller.configureGooglePhotos(
        "test-client.apps.googleusercontent.com", "test-client-secret"
    )
    assert google_photos.keyring.values[
        ("PicasaPy Google Photos", "client_secret")
    ] == "test-client-secret"
    assert controller._get_settings().value(
        "googlePhotos/secrets/client_secret", ""
    ) == ""
    controller._google_photos_credentials.set_secret("refresh_token", "test-refresh")
    controller.googlePhotosChanged.emit()
    assert gomb.property("enabled") is False, "üres tálcával tiltva kell maradnia"

    sorok = [_sor(controller, "b.jpg"), _sor(controller, "a.jpg")]
    controller.holdRows(sorok)
    assert _varj(qt_app, lambda: gomb.property("enabled") is True), (
        "bejelentkezéssel és tálcaképpel engedélyezni kell a feltöltést"
    )

    server = FakePhotosServer()
    controller._google_photos_transport = server
    controller._google_photos_oauth = OAuthClient(
        transport=server,
        token_endpoint="https://photos.test/token",
    )
    _kattints(qt_app, gomb)

    assert _varj(qt_app, lambda: not controller.photosUploadRunning), (
        "a kattintás után a feltöltés nem fejeződött be időben"
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
    assert names == ["b.jpg", "a.jpg"]
    assert controller.photosUploadError == ""
