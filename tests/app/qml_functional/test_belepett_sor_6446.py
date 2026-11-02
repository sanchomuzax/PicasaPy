"""A jobb felső sor belépett és kilépett állapota, valódi kattintással (#6446).

Az eredeti szerint belépve a sor három elemből áll: a fiók neve (kattintás
nélkül), a Google Fotók hivatkozás és a Kijelentkezés. Kilépve csak a
bejelentkezési hivatkozás látszik.

A külső címet a QDesktopServices url-kezelője fogja meg (#706 mintája): a
Google Fotók hivatkozás valódi útját méri, és közben nem indul böngésző.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app.tray_google_photos_controller as tray_google_photos_controller
import picasapy.google_photos as google_photos
from conftest import _build_qml_app
from support.google_fiok import PROBA_EMAIL, PROBA_REFRESH, id_token
from support.varakozas import hibaturo_feltetel, var_feltetelre

FOTOK_CIM = "https://photos.google.com"


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


class _HamisBelepes:
    """A bejelentkezési munkamenet helyettese: a Google-válasz id_token-nel."""

    def __init__(self, _oauth, *, client_id, client_secret):
        self.authorization_url = f"https://accounts.google.test/?client_id={client_id}"

    def wait_for_tokens(self):
        return {
            "refresh_token": PROBA_REFRESH,
            "id_token": id_token({"email": PROBA_EMAIL}),
        }

    def cancel(self):
        return None


class _UrlFogo(QObject):
    """A `https` séma kezelője a teszt idejére: a kért címeket rögzíti."""

    def __init__(self):
        super().__init__()
        self.cimek: list[str] = []

    @Slot("QUrl")
    def kezel(self, url):  # noqa: D102 - a Qt hívja
        self.cimek.append(url.toString())


@pytest.fixture
def google_photos_app(qt_app, tmp_path, monkeypatch, request):
    monkeypatch.setattr(google_photos, "keyring", _HamisKulcstarto())
    monkeypatch.delenv("PICASAPY_GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("PICASAPY_GOOGLE_CLIENT_SECRET", raising=False)
    yield from _build_qml_app(qt_app, tmp_path, keep_modul=request.module)


@pytest.fixture
def url_fogo(qt_app):
    fogo = _UrlFogo()
    QDesktopServices.setUrlHandler("https", fogo, "kezel")
    try:
        yield fogo
    finally:
        QDesktopServices.unsetUrlHandler("https")
        qt_app.processEvents()


def _gyerek(szulo, nev: str, tipus=QQuickItem):
    elem = szulo.findChild(tipus, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


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


def _klienssel(monkeypatch) -> None:
    monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("PICASAPY_GOOGLE_CLIENT_SECRET", "test-client-secret")


def _hamis_oauth(controller) -> None:
    controller._ensure_google_photos_wired()
    controller._google_photos_oauth = google_photos.OAuthClient(
        transport=_HamisOAuthTransport()
    )


def _bejelentkezve(controller) -> None:
    controller._on_google_photos_auth_result(PROBA_REFRESH, "", PROBA_EMAIL)


def test_kilepve_csak_a_bejelentkezesi_hivatkozas_latszik(google_photos_app, qt_app):
    window, controller, _engine = google_photos_app
    qt_app.processEvents()

    assert controller.googlePhotosSignedIn is False
    felirat = _gyerek(window, "menuBarSignInLink")
    assert _varj(qt_app, lambda: felirat.property("visible") is True)
    assert felirat.property("text") == "Sign in with Google Account"
    for nev in ("menuBarAccountText", "menuBarGooglePhotosLink", "menuBarSignOutLink"):
        assert _gyerek(window, nev).property("visible") is False, nev


def test_bejelentkezve_a_fiok_nem_kattinthato_es_ket_hivatkozas_van(
    google_photos_app, qt_app, monkeypatch
):
    window, controller, _engine = google_photos_app
    _klienssel(monkeypatch)
    _bejelentkezve(controller)
    qt_app.processEvents()

    fiok = _gyerek(window, "menuBarAccountText")
    assert _varj(qt_app, lambda: fiok.property("visible") is True)
    assert fiok.property("text") == PROBA_EMAIL
    assert not any(gyerek.inherits("QQuickMouseArea") for gyerek in fiok.childItems())
    assert _gyerek(window, "menuBarGooglePhotosLink").property("text") == "Google Photos"
    assert _gyerek(window, "menuBarSignOutLink").property("text") == "Sign Out"
    assert _gyerek(window, "menuBarSignInLink").property("visible") is False


def test_bejelentkezve_fiok_nelkul_az_altalanos_felirat_latszik(
    google_photos_app, qt_app, monkeypatch
):
    window, controller, _engine = google_photos_app
    _klienssel(monkeypatch)
    controller._on_google_photos_auth_result(PROBA_REFRESH, "", "")
    qt_app.processEvents()

    fiok = _gyerek(window, "menuBarAccountText")
    assert _varj(qt_app, lambda: fiok.property("visible") is True)
    assert fiok.property("text") == "Signed in to Google Photos"


def test_a_google_fotok_hivatkozas_a_fotok_cimet_nyitja(
    google_photos_app, qt_app, monkeypatch, url_fogo
):
    window, controller, _engine = google_photos_app
    _klienssel(monkeypatch)
    _bejelentkezve(controller)
    qt_app.processEvents()

    _kattints(qt_app, _gyerek(window, "menuBarGooglePhotosLink"))

    assert _varj(qt_app, lambda: url_fogo.cimek == [FOTOK_CIM])
    assert controller.googlePhotosSignedIn is True


def test_a_kijelentkezes_linkre_kattintva_a_sor_kilepett_allapotba_valt(
    google_photos_app, qt_app, monkeypatch
):
    window, controller, _engine = google_photos_app
    _klienssel(monkeypatch)
    _hamis_oauth(controller)
    _bejelentkezve(controller)
    qt_app.processEvents()

    _kattints(qt_app, _gyerek(window, "menuBarSignOutLink"))

    assert _varj(qt_app, lambda: controller.googlePhotosSignedIn is False)
    felirat = _gyerek(window, "menuBarSignInLink")
    assert _varj(qt_app, lambda: felirat.property("visible") is True)
    assert felirat.property("text") == "Sign in with Google Account"
    assert _gyerek(window, "menuBarAccountText").property("visible") is False
    assert controller.property("googlePhotosAccount") == ""


def test_a_valodi_belepes_utan_a_fiok_neve_latszik(google_photos_app, qt_app, monkeypatch):
    window, controller, _engine = google_photos_app
    _klienssel(monkeypatch)
    monkeypatch.setattr(google_photos, "LoopbackOAuthSession", _HamisBelepes)
    monkeypatch.setattr(
        tray_google_photos_controller,
        "QDesktopServices",
        SimpleNamespace(openUrl=lambda _url: True),
    )
    monkeypatch.setattr(
        controller,
        "_start_background",
        lambda target, **_kwargs: target(),
    )
    qt_app.processEvents()

    _kattints(qt_app, _gyerek(window, "menuBarSignInArea"))

    fiok = _gyerek(window, "menuBarAccountText")
    assert _varj(qt_app, lambda: fiok.property("visible") is True)
    assert fiok.property("text") == PROBA_EMAIL
    assert controller.property("googlePhotosAccount") == PROBA_EMAIL
