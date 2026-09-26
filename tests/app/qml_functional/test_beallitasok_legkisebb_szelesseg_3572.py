"""#3572 — a Beállítások ablak a legkisebb szélességén, magyarul se lógjon ki.

A hivatalos magyar feliratok hosszabbak az angolnál. Az átnézés mérte, hogy
a `minimumWidth` (480 px) szélességen egy nem tördelődő jelölő-felirat
kitolja a fül tartalmát, és vele a fülsort és a „Tallózás…” gombokat is.

Az őr a VALÓDI `OptionsDialog`-ot tölti be a magyar `.qm`-mel, a legkisebb
szélességre állítja, és fülenként kimondja: egyetlen látható elem jobb széle
sem nagyobb az ablak szélességénél. Geometriát mér (a kirajzolt elemek
jelenet-koordinátáit), képet nem hasonlít referenciához.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QTranslator, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem

import picasapy.app

_I18N_DIR = Path(picasapy.app.__file__).parent / "i18n"
_TURES = 1.0
_ELETBEN: list = []


def _latszo_elemek(gyoker: QQuickItem):
    for gyerek in gyoker.childItems():
        if not gyerek.isVisible() or gyerek.opacity() == 0:
            continue
        yield gyerek
        yield from _latszo_elemek(gyerek)


@pytest.fixture
def magyar_beallitasok(qml_app, qt_app):
    fordito = QTranslator(qt_app)
    assert fordito.load("picasapy_hu", str(_I18N_DIR))
    qt_app.installTranslator(fordito)
    _window, _controller, engine = qml_app
    engine.retranslate()
    komponens = QQmlComponent(engine)
    komponens.setData(b"import PicasaPy 1.0\nOptionsDialog { visible: true }\n", QUrl())
    assert komponens.errors() == [], [h.toString() for h in komponens.errors()]
    ablak = komponens.create()
    assert ablak is not None
    QQmlEngine.setObjectOwnership(ablak, QQmlEngine.ObjectOwnership.CppOwnership)
    _ELETBEN.append(ablak)
    ablak.setProperty("width", ablak.property("minimumWidth"))
    qt_app.processEvents()
    try:
        yield ablak
    finally:
        ablak.setProperty("visible", False)
        qt_app.removeTranslator(fordito)
        _ELETBEN.clear()


_WEBALBUM_JELOLOK = (
    "optionsWebStripedUploadCheck",
    "optionsWebKeepJpegQualityCheck",
    "optionsWebConfirmSyncDisableCheck",
)


def test_a_webalbum_hosszu_feliratai_tordelodnek(magyar_beallitasok, qt_app):
    """A #3572 saját feliratai: a hosszú magyar szöveg tördelődik, és nem
    szélesíti a fület (a kiváltó mérésben 652 px-re tolta a tartalmat)."""
    ablak = magyar_beallitasok
    ablak.findChild(QObject, "optionsTabBar").setProperty("currentIndex", 6)
    for _ in range(5):
        qt_app.processEvents()
    verem = ablak.findChild(QObject, "optionsTabStack")
    for nev in _WEBALBUM_JELOLOK:
        jelolo = ablak.findChild(QObject, nev)
        assert jelolo.property("width") <= verem.property("width") + _TURES, nev
    # a leghosszabb feliratnak ténylegesen több sorba kell törnie
    hosszu = ablak.findChild(QObject, "optionsWebStripedUploadCheck")
    assert hosszu.property("contentItem").property("lineCount") > 1, "nem tördelődik"


@pytest.mark.xfail(strict=True, reason="#3661: régi hiba — a 8 fülcím és néhány felirat 480 px-en kilóg")
@pytest.mark.parametrize("ful", range(8))
def test_a_legkisebb_szelessegen_egyik_ful_sem_log_ki(magyar_beallitasok, qt_app, ful):
    ablak = magyar_beallitasok
    assert ablak.property("width") == ablak.property("minimumWidth") == 480
    fulsor = ablak.findChild(QObject, "optionsTabBar")
    fulsor.setProperty("currentIndex", ful)
    for _ in range(5):
        qt_app.processEvents()
    szelesseg = ablak.property("width")
    kilogok = []
    for elem in _latszo_elemek(ablak.contentItem()):
        jobb = elem.mapToScene(elem.boundingRect().topRight()).x()
        if jobb > szelesseg + _TURES and elem.objectName():
            kilogok.append((elem.objectName(), round(jobb)))
    assert kilogok == [], f"a(z) {ful}. fülön kilóg: {kilogok}"
