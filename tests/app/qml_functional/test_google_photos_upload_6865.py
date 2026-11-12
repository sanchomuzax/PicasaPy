"""A tálca és a mappa-fejléc kijelentkezve is indít feltöltést (#6865)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app.tray_google_photos_controller as tray_google_photos_controller
import picasapy.google_photos as google_photos
from conftest import _build_qml_app
from support.jpeg_factory import make_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre


class _FakeTransport:
    def __init__(self):
        self.requests = []
        self.upload_number = 0

    def request(self, method, url, *, headers, body, timeout, cancel_event=None):
        self.requests.append((method, url, dict(headers), body))
        if url.endswith("/token"):
            return google_photos.HttpResponse(
                200, b'{"access_token":"access-token","expires_in":3600}'
            )
        if url.endswith("/uploads"):
            self.upload_number += 1
            return google_photos.HttpResponse(
                200, f"upload-{self.upload_number}".encode()
            )
        if url.endswith("/mediaItems:batchCreate"):
            items = json.loads(body)["newMediaItems"]
            return google_photos.HttpResponse(
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
        raise AssertionError(f"Nem várt Google Photos kérés: {method} {url}")


class _FakeKeyring:
    def __init__(self):
        self.values = {}

    def get_password(self, service, username):
        return self.values.get((service, username))

    def set_password(self, service, username, password):
        self.values[(service, username)] = password

    def delete_password(self, service, username):
        self.values.pop((service, username), None)


class _FakeOAuth:
    authorization_url = "https://accounts.google.test/authorize"

    def refresh_access_token(self, *_args):
        return {"access_token": "access-token"}

    def revoke(self, *_args):
        return None


class _FakeLoopbackOAuthSession:
    def __init__(self, oauth, *, client_id, client_secret):
        self.authorization_url = oauth.authorization_url
        self.client_id = client_id
        self.client_secret = client_secret

    def wait_for_tokens(self):
        return {"refresh_token": "test-refresh-token"}

    def cancel(self):
        return None


@pytest.fixture
def google_photos_app(qt_app, tmp_path, monkeypatch, request):
    keyring = _FakeKeyring()
    monkeypatch.setattr(google_photos, "keyring", keyring)
    monkeypatch.setattr(
        tray_google_photos_controller,
        "account_email_from_tokens",
        lambda _tokens: "photos@example.test",
    )
    monkeypatch.setattr(
        tray_google_photos_controller,
        "QDesktopServices",
        SimpleNamespace(openUrl=lambda _url: True),
    )
    monkeypatch.setattr(
        google_photos, "LoopbackOAuthSession", _FakeLoopbackOAuthSession
    )
    monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_SECRET", "test-client-secret")

    def kepeket_keszit(mappa: Path) -> None:
        make_jpeg(mappa / "a.jpg", size=(96, 72))
        make_jpeg(mappa / "b.jpg", size=(96, 72))

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket_keszit,
        keep_modul=request.module,
    )


def _elem(window, object_name: str, tipo=QQuickItem):
    if tipo is not QQuickItem:
        return window.findChild(tipo, object_name)
    return next(
        (
            item
            for item in _walk(window.contentItem())
            if item.objectName() == object_name
        ),
        None,
    )


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _var(qt_app, condition, seconds: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(condition), seconds)


def _kattints(window, item, qt_app) -> None:
    assert item is not None and item.isVisible() and item.isEnabled()
    assert item.width() > 0 and item.height() > 0
    center = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _batch_filenames(transport):
    batches = [
        request
        for request in transport.requests
        if request[1].endswith("/mediaItems:batchCreate")
    ]
    assert len(batches) == 1
    return [
        item["simpleMediaItem"]["fileName"]
        for item in json.loads(batches[0][3])["newMediaItems"]
    ]


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_talca_upload_kattintasa_bejelentkezik_es_folytatja_a_feltoltest(
    google_photos_app, qt_app, height_delta
):
    window, controller, _engine = google_photos_app
    window.setProperty("height", window.property("height") + height_delta)
    qt_app.processEvents()
    gomb = _elem(window, "trayUploadButton")
    assert _var(qt_app, lambda: gomb is not None and gomb.isVisible())
    controller.holdRows([1, 0])
    assert controller.googlePhotosSignedIn is False
    assert gomb.isEnabled(), "kijelentkezve is kattintható kell legyen"

    transport = _FakeTransport()
    controller._google_photos_oauth = _FakeOAuth()
    controller._google_photos_transport = transport
    controller._start_background = lambda target, **_kwargs: target()
    _kattints(window, gomb, qt_app)

    assert _var(qt_app, lambda: controller.photosUploadFinished)
    assert controller.googlePhotosSignedIn is True
    assert _batch_filenames(transport) == ["b.jpg", "a.jpg"]
    dialog = _elem(window, "googlePhotosUploadDialog", QObject)
    assert _var(qt_app, lambda: dialog is not None and dialog.property("visible"))


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_mappa_fejlec_upload_kattintasa_bejelentkezik_es_a_mappat_tolti_fel(
    google_photos_app, qt_app, monkeypatch, height_delta
):
    window, controller, _engine = google_photos_app
    window.setProperty("height", window.property("height") + height_delta)
    qt_app.processEvents()
    gomb = _elem(window, "headerUploadButton")
    assert _var(qt_app, lambda: gomb is not None and gomb.isVisible())
    assert controller.googlePhotosSignedIn is False
    assert gomb.isEnabled(), "kijelentkezve is kattintható kell legyen"

    transport = _FakeTransport()
    controller._google_photos_oauth = _FakeOAuth()
    controller._google_photos_transport = transport
    controller._start_background = lambda target, **_kwargs: target()
    _kattints(window, gomb, qt_app)

    assert _var(qt_app, lambda: controller.photosUploadFinished)
    assert controller.googlePhotosSignedIn is True
    assert _batch_filenames(transport) == ["a.jpg", "b.jpg"]
    dialog = _elem(window, "googlePhotosUploadDialog", QObject)
    assert _var(qt_app, lambda: dialog is not None and dialog.property("visible"))

    if height_delta == 0:
        # A bejelentkezési hiba a meglévő feltöltési dialógusban látszik.
        dialog.close()
        controller._google_photos_credentials.delete_secret("refresh_token")
        controller._set_google_photos_account("")
        controller.googlePhotosChanged.emit()
        monkeypatch.delenv("PICASAPY_GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("PICASAPY_GOOGLE_CLIENT_SECRET", raising=False)
        _kattints(window, gomb, qt_app)
        assert controller.googlePhotosAuthError == "missing_credentials"
        assert _var(qt_app, lambda: dialog.property("visible"))
        status = _elem(window, "googlePhotosUploadStatus")
        assert status is not None and status.property("text")

        # A fiók beállítása után az engedélyezés közben a Mégse is működik.
        dialog.close()
        monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_SECRET", "test-client-secret")
        controller._start_background = lambda _target, **_kwargs: None
        _kattints(window, gomb, qt_app)
        assert controller.googlePhotosAuthBusy is True
        assert _var(qt_app, lambda: dialog.property("visible"))
        cancel = _elem(window, "googlePhotosUploadCancelButton")
        assert cancel is not None and cancel.isEnabled()
        _kattints(window, cancel, qt_app)
        assert controller.googlePhotosAuthBusy is False
        assert controller.photosUploadError == "cancelled"
        assert status.property("text") == "Upload cancelled"
