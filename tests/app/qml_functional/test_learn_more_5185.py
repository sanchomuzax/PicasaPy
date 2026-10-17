"""A Név nélküliek üdvözlőablakának „Learn more...” gombja VALÓDI kattintással (#5185).

Az eredetiben a gomb (`instructionpanel/learn_more`, a 19.2 kutatási szakasz)
a Picasa súgócímét nyitja az alapértelmezett böngészőben, és közben az
üdvözlőablak nyitva marad:
`http://picasa.google.com/support/bin/answer.py?hl=<nyelv>&answer=156272`.
A `hl` a FELÜLET nyelvéből jön, a Picasa 45 bejegyzéses nyelvtáblája szerint.

Lefedve:
- a gomb valódi kattintása a fenti címet nyitja, a `hl` a beállított nyelv
  Picasa-kódja (`hu`, `en`, `pt-BR`; az `enUK` a táblában `en-GB`);
- a kattintás után az üdvözlőablak nyitva marad;
- minden támogatott nyelvnek van `hl`-kódja a táblában.

A megnyitást a `QDesktopServices` url-kezelője fogja meg (ld. #706): a
`Qt.openUrlExternally` valódi útját méri, és közben egyetlen böngésző sem indul.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, QSettings, QUrl, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from tests.app.qml_functional._utolso_maradek_5150_helpers import kattint_elemre, varj

CIM_SABLON = "http://picasa.google.com/support/bin/answer.py?hl={hl}&answer=156272"

_KEEPALIVE: list = []


class _UrlFogo(QObject):
    """A `http` séma kezelője a teszt idejére: a kért címeket rögzíti."""

    def __init__(self):
        super().__init__()
        self.cimek: list[str] = []

    @Slot("QUrl")
    def kezel(self, url):  # noqa: D102 - a Qt hívja
        self.cimek.append(url.toString())


class _FaceScanSztub(QObject):
    """A `FaceScanController` helyett: csak a nézet betöltéséhez kellő hívások."""

    @Slot(result=bool)
    def unnamedWelcomeHasBeenShown(self):  # noqa: N802
        return False

    @Slot()
    def markUnnamedWelcomeShown(self):  # noqa: N802
        pass

    @Slot(bool, bool, result="QVariantList")
    def unnamedGroups(self, group_by_face, expand_groups):  # noqa: N802
        return []

    @Slot(result="QVariantList")
    def ignoredGroups(self):  # noqa: N802
        return []


def _vezerlo(qt_app, tmp_path, nyelv):
    """A valódi `AppController`, a beállításban mentett felületi nyelvvel."""
    from picasapy.app.controller import AppController
    from picasapy.app.language_controller import LANGUAGE_KEY
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index
    from picasapy.thumbs import ThumbnailCache

    konyvtar = tmp_path / "kepek"
    konyvtar.mkdir()
    with open_index(tmp_path / "index.db"):
        pass
    beallitas = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    beallitas.setValue(LANGUAGE_KEY, nyelv)
    beallitas.sync()
    return AppController(
        tmp_path / "index.db",
        (str(konyvtar),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=beallitas,
        watched_file=tmp_path / "WatchedFolders.txt",
    )


def _montaz(qt_app, tmp_path, nyelv):
    """A Név nélküliek nézete valódi (offscreen) ablakban, a valódi vezérlővel.

    A nézet láthatatlanul épül, és az ablak megjelenése után lesz látható:
    az `onVisibleChanged` nyitja meg az üdvözlőablakot."""
    import picasapy.app.application as app_module

    vezerlo = _vezerlo(qt_app, tmp_path, nyelv)
    fogo_sztub = _FaceScanSztub()
    motor = QQmlEngine()
    motor.addImportPath(str(app_module._APP_DIR / "qml"))
    motor.rootContext().setContextProperty("controller", vezerlo)
    komponens = QQmlComponent(
        motor,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "UnnamedFacesView.qml")
        ),
    )
    nezet = komponens.createWithInitialProperties(
        {"faceScanController": fogo_sztub, "visible": False}
    )
    assert [e.toString() for e in komponens.errors()] == []
    assert nezet is not None
    QQmlEngine.setObjectOwnership(nezet, QQmlEngine.ObjectOwnership.CppOwnership)

    ablak = QQuickWindow()
    ablak.resize(1000, 600)
    nezet.setParentItem(ablak.contentItem())
    nezet.setProperty("width", 1000)
    nezet.setProperty("height", 600)
    ablak.show()
    QTest.qWaitForWindowExposed(ablak)
    ablak.requestActivate()
    QTest.qWaitForWindowActive(ablak)
    nezet.setProperty("visible", True)
    qt_app.processEvents()
    _KEEPALIVE.extend([motor, komponens, nezet, ablak, vezerlo, fogo_sztub])
    return ablak, nezet


def _bejar(elem):
    for gyermek in elem.childItems():
        yield gyermek
        yield from _bejar(gyermek)


def _latszo_elem(qt_app, ablak, nev):
    """A látszó elem a nevével. A felugró ablak az overlay-ében él, a nézet
    elemfáján kívül, ezért az ablak teljes elemfáját járjuk be."""
    talalt = []

    def latszik():
        talalt[:] = [
            e
            for e in _bejar(ablak.contentItem())
            if e.objectName() == nev and e.isVisible() and e.width() > 0
        ]
        return bool(talalt)

    assert varj(qt_app, latszik), f"{nev} nem látszik"
    return talalt[0]


@pytest.mark.parametrize(
    ("nyelv", "hl"),
    [("hu", "hu"), ("en", "en"), ("pt-BR", "pt-BR"), ("enUK", "en-GB")],
)
def test_learn_more_click_opens_the_picasa_help_in_the_ui_language(
    qt_app, tmp_path, nyelv, hl
):
    ablak, nezet = _montaz(qt_app, tmp_path, nyelv)
    udvozlo = nezet.findChild(QObject, "unnamedWelcomeDialog")
    assert varj(
        qt_app, lambda: udvozlo is not None and udvozlo.property("visible") is True
    ), "az üdvözlőablak nem nyílt meg"
    gomb = _latszo_elem(qt_app, ablak, "unnamedWelcomeLearnMoreButton")

    fogo = _UrlFogo()
    QDesktopServices.setUrlHandler("http", fogo, "kezel")
    try:
        kattint_elemre(ablak, qt_app, gomb)
        assert varj(qt_app, lambda: bool(fogo.cimek)), (
            "a „Learn more...” gomb nem nyitott címet"
        )
        assert fogo.cimek == [CIM_SABLON.format(hl=hl)]
        assert udvozlo.property("visible") is True, (
            "a „Learn more...” kattintás bezárta az üdvözlőablakot"
        )
    finally:
        QDesktopServices.unsetUrlHandler("http")
        # a bezárás még a sztub élettartama alatt fut le: a `closed` kezelő
        # hívja a `markUnnamedWelcomeShown`-t, és leálláskor már nem élne
        QMetaObject.invokeMethod(udvozlo, "close")
        varj(qt_app, lambda: udvozlo.property("visible") is False)
        ablak.close()


def test_every_supported_language_has_a_picasa_help_code():
    from picasapy.app.language_controller import (
        PICASA_HELP_LANGUAGE,
        SUPPORTED_LANGUAGES,
    )

    assert set(PICASA_HELP_LANGUAGE) == set(SUPPORTED_LANGUAGES)
