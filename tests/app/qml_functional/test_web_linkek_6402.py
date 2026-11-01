"""A külső hivatkozások VALÓDI kattintással (#6402).

A Névjegyben a honlap, az adatvédelmi tájékoztató és a felhasználási feltételek;
a Google Fotók beállításainál (ahol a bejelentkezés indul) az adatvédelmi
tájékoztató és a feltételek. A megnyitást a `QDesktopServices` url-kezelője
fogja meg (ld. #706), így a teszt a felület VALÓDI kimenetét méri, és közben
egyetlen böngésző sem indul.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtQuick import QQuickItem

import picasapy.google_photos as google_photos
from conftest import _build_qml_app
from picasapy.app.external_links import PRIVACY_POLICY_URL, TERMS_URL, WEBSITE_URL
from tests.app.qml_functional._utolso_maradek_5150_helpers import kattint_elemre, varj


class _UrlFogo(QObject):
    """A `https` séma kezelője a teszt idejére: a kért címeket rögzíti."""

    def __init__(self):
        super().__init__()
        self.cimek: list[str] = []

    @Slot("QUrl")
    def kezel(self, url):  # noqa: D102 - a Qt hívja
        self.cimek.append(url.toString())


class _HamisKulcstarto:
    """A rendszer kulcstartója helyett: a valódi jelszótár nem érintődik."""

    def __init__(self):
        self.values = {}

    def get_password(self, service, username):
        return self.values.get((service, username))

    def set_password(self, service, username, password):
        self.values[(service, username)] = password

    def delete_password(self, service, username):
        self.values.pop((service, username), None)


@pytest.fixture
def google_photos_app(qt_app, tmp_path, monkeypatch, request):
    monkeypatch.setattr(google_photos, "keyring", _HamisKulcstarto())
    monkeypatch.delenv("PICASAPY_GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("PICASAPY_GOOGLE_CLIENT_SECRET", raising=False)
    yield from _build_qml_app(qt_app, tmp_path, keep_modul=request.module)


def _kattint_es_fogja_a_cimet(qt_app, ablak, elem) -> list[str]:
    """Valódi kattintás az `elem`-en, és a `https`-kezelő által kapott címek."""
    fogo = _UrlFogo()
    QDesktopServices.setUrlHandler("https", fogo, "kezel")
    try:
        kattint_elemre(ablak, qt_app, elem)
        varj(qt_app, lambda: bool(fogo.cimek))
        return list(fogo.cimek)
    finally:
        QDesktopServices.unsetUrlHandler("https")
        qt_app.processEvents()


def _latszo_hivatkozas(qt_app, szulo, nev: str) -> QQuickItem:
    elem = szulo.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} hivatkozás hiányzik"
    assert varj(
        qt_app, lambda: elem.isVisible() and elem.property("width") > 0
    ), f"{nev} nem látszik"
    return elem


def _ablak(qt_app, nev: str):
    for ablak in qt_app.topLevelWindows():
        if ablak.objectName() == nev:
            return ablak
    raise AssertionError(f"{nev} ablak nem található")


@pytest.mark.parametrize(
    ("nev", "cim"),
    [
        ("aboutWebsiteLink", WEBSITE_URL),
        ("aboutPrivacyLink", PRIVACY_POLICY_URL),
        ("aboutTermsLink", TERMS_URL),
    ],
)
def test_a_nevjegyben_a_linkre_kattintva_a_helyes_cim_nyilik(
    qml_app, qt_app, nev, cim
):
    window, _controller, _engine = qml_app
    menu_bars = [
        item
        for item in window.findChildren(QObject)
        if item.metaObject().indexOfSignal("aboutRequested()") >= 0
    ]
    assert len(menu_bars) == 1, "a Névjegy megnyitó jele hiányzik vagy többszörös"
    assert QMetaObject.invokeMethod(
        menu_bars[0], "aboutRequested", Qt.ConnectionType.DirectConnection
    )
    assert varj(
        qt_app, lambda: window.findChild(QObject, "aboutDialog") is not None
    ), "a Névjegy párbeszéd nem épült fel"
    dialog = window.findChild(QObject, "aboutDialog")
    assert varj(qt_app, lambda: dialog.property("visible") is True)

    link = _latszo_hivatkozas(qt_app, dialog, nev)

    assert _kattint_es_fogja_a_cimet(qt_app, window, link) == [cim]


def test_a_nevjegy_tartalmazza_a_harom_linket(qml_app, qt_app):
    window, _controller, _engine = qml_app
    menu_bars = [
        item
        for item in window.findChildren(QObject)
        if item.metaObject().indexOfSignal("aboutRequested()") >= 0
    ]
    QMetaObject.invokeMethod(
        menu_bars[0], "aboutRequested", Qt.ConnectionType.DirectConnection
    )
    assert varj(
        qt_app, lambda: window.findChild(QObject, "aboutDialog") is not None
    )
    dialog = window.findChild(QObject, "aboutDialog")
    for nev in ("aboutWebsiteLink", "aboutPrivacyLink", "aboutTermsLink"):
        assert dialog.findChild(QQuickItem, nev) is not None, f"{nev} hiányzik"


def _nyisd_meg_a_beallitasokat(qt_app, window):
    """A bejelentkezés-sáv kattintása kliens nélkül a Google Fotók beállításait nyitja."""
    kattinthato = window.findChild(QObject, "menuBarSignInArea")
    assert kattinthato is not None, "a menüsori bejelentkezés-sáv hiányzik"
    kattint_elemre(window, qt_app, kattinthato)
    assert varj(
        qt_app,
        lambda: any(
            ablak.objectName() == "optionsDialog" for ablak in qt_app.topLevelWindows()
        ),
    ), "a Google Fotók beállításai nem nyíltak meg"
    return _ablak(qt_app, "optionsDialog")


@pytest.mark.parametrize(
    ("nev", "cim"),
    [
        ("googlePhotosPrivacyLink", PRIVACY_POLICY_URL),
        ("googlePhotosTermsLink", TERMS_URL),
    ],
)
def test_a_google_bejelentkezesnel_a_linkre_kattintva_a_helyes_cim_nyilik(
    google_photos_app, qt_app, nev, cim
):
    window, controller, _engine = google_photos_app
    assert controller.googlePhotosCanSignIn is False, "a teszt kliens nélküli állapotot kér"
    options = _nyisd_meg_a_beallitasokat(qt_app, window)
    assert varj(qt_app, lambda: options.property("visible") is True)

    link = _latszo_hivatkozas(qt_app, options, nev)

    assert _kattint_es_fogja_a_cimet(qt_app, options, link) == [cim]
