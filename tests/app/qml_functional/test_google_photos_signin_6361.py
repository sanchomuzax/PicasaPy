"""A Google Fotók-menüsor bejelentkezési útja valódi kattintással (#6361)."""

from __future__ import annotations

import pytest
from types import SimpleNamespace
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app.tray_google_photos_controller as tray_google_photos_controller
import picasapy.google_photos as google_photos
from conftest import _build_qml_app
from support.varakozas import hibaturo_feltetel, var_feltetelre


class _HamisKulcstarto:
    def __init__(self):
        self.values = {}

    def get_password(self, _service, _username):
        return self.values.get((_service, _username))

    def set_password(self, service, username, password):
        self.values[(service, username)] = password

    def delete_password(self, service, username):
        self.values.pop((service, username), None)


class _HamisOAuthTransport:
    def request(self, *_args, **_kwargs):
        return google_photos.HttpResponse(200, b"")


class _HamisLoopbackOAuthSession:
    def __init__(self, _oauth, *, client_id, client_secret):
        self.authorization_url = f"https://accounts.google.test/?client_id={client_id}"

    def wait_for_tokens(self):
        return {"refresh_token": "test-refresh-token"}

    def cancel(self):
        return None


@pytest.fixture
def google_photos_app(qt_app, tmp_path, monkeypatch, request):
    monkeypatch.setattr(google_photos, "keyring", _HamisKulcstarto())
    monkeypatch.delenv("PICASAPY_GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("PICASAPY_GOOGLE_CLIENT_SECRET", raising=False)
    yield from _build_qml_app(qt_app, tmp_path, keep_modul=request.module)


def _gyerek(szulo, nev: str, tipus=QQuickItem):
    elem = szulo.findChild(tipus, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _ablak(qt_app, nev: str):
    for ablak in qt_app.topLevelWindows():
        if ablak.objectName() == nev:
            return ablak
    raise AssertionError(f"{nev} ablak nem található")


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _kattints(qt_app, elem) -> None:
    assert elem.isVisible() and elem.width() > 0 and elem.height() > 0
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        elem.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_a_menusori_felirat_kattintasa_elinditja_a_bejelentkezest(
    google_photos_app, qt_app, monkeypatch, height_delta
):
    window, controller, _engine = google_photos_app
    window.setProperty("height", window.property("height") + height_delta)
    qt_app.processEvents()
    monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_SECRET", "test-client-secret")
    controller.googlePhotosChanged.emit()
    assert controller.googlePhotosCanSignIn is True
    megnyitott_url = []
    monkeypatch.setattr(
        google_photos, "LoopbackOAuthSession", _HamisLoopbackOAuthSession
    )
    monkeypatch.setattr(
        tray_google_photos_controller,
        "QDesktopServices",
        SimpleNamespace(
            openUrl=lambda url: megnyitott_url.append(url.toString()) or True
        ),
    )
    monkeypatch.setattr(
        controller,
        "_start_background",
        lambda target, **_kwargs: target(),
    )

    kattinthato = _gyerek(window, "menuBarSignInArea")
    _kattints(qt_app, kattinthato)

    assert _varj(qt_app, lambda: bool(megnyitott_url))
    assert megnyitott_url == [
        "https://accounts.google.test/?client_id=test-client-id"
    ]
    assert _varj(qt_app, lambda: controller.googlePhotosSignedIn is True)
    assert controller._google_photos_credentials.get_secret("refresh_token") == (
        "test-refresh-token"
    )


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_kliens_nelkul_a_menusori_kattintas_egyszeru_uzenetet_mutat(
    google_photos_app, qt_app, height_delta
):
    window, controller, _engine = google_photos_app
    window.setProperty("height", window.property("height") + height_delta)
    qt_app.processEvents()
    assert controller.googlePhotosCanSignIn is False

    kattinthato = _gyerek(window, "menuBarSignInArea")
    _kattints(qt_app, kattinthato)

    dialog = _gyerek(window, "googlePhotosUnavailableDialog", QObject)
    assert _varj(qt_app, lambda: dialog.property("visible") is True)
    message = _gyerek(dialog, "googlePhotosUnavailableMessage")
    assert message.property("text") == (
        "Google sign-in is not available in this version yet."
    )
    assert not any(
        ablak.objectName() == "optionsDialog"
        for ablak in qt_app.topLevelWindows()
    )


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_bejelentkezve_a_sor_kijelentkezes_linkjevel_lehet_kilepni(
    google_photos_app, qt_app, monkeypatch, height_delta
):
    # #6446: a fiókmenü megszűnt, a Kijelentkezés hivatkozás a sorban van.
    window, controller, _engine = google_photos_app
    window.setProperty("height", window.property("height") + height_delta)
    # A belépett sor (általános felirat + két hivatkozás) széles: keskeny
    # ablakban a menüsor tételei fölé csúszhat, és a kattintást azok kapnák.
    window.setProperty("width", max(int(window.property("width")), 1280))
    qt_app.processEvents()
    monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_SECRET", "test-client-secret")
    assert controller.googlePhotosCanSignIn is True
    controller._google_photos_credentials.set_secret("refresh_token", "test-refresh")
    controller._google_photos_oauth = google_photos.OAuthClient(
        transport=_HamisOAuthTransport()
    )
    controller.googlePhotosChanged.emit()

    kilepes = _gyerek(window, "menuBarSignOutLink")
    # A belépett sor a jel után épül újra: a kattintás csak akkor menjen,
    # amikor a hivatkozás látszik, és a helye két egymás utáni képkockán át
    # változatlan (a jobbra igazított sor szélessége közben még nőhet).
    assert _varj(qt_app, lambda: kilepes.isVisible() and kilepes.width() > 0)
    elozo = [None]

    def _all_a_helye():
        hely = kilepes.mapToScene(QPointF(0, 0))
        most = (round(hely.x()), round(hely.y()), round(kilepes.width()))
        stabil = most == elozo[0]
        elozo[0] = most
        return stabil

    assert _varj(qt_app, _all_a_helye)
    _kattints(qt_app, kilepes)

    assert _varj(qt_app, lambda: controller.googlePhotosSignedIn is False)
