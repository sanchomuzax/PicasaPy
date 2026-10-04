"""#4126 — a feltöltési csoport `+0xd4` módválasztása kattintással.

Az online művelet nem része ennek a próbának. A `biztonsagi-mentes.md`
15.1 szerint a három rádióelem a panel módját 1/2/3-ra állítja; itt a
felhasználó tényleges egérkattintása és a három kizáró pipa ellenőrzi ezt.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, QTranslator, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest

import picasapy.app.application as app_module

_KEEP_ALIVE: list = []


@pytest.fixture(scope="module")
def engine(qt_app):
    motor = QQmlEngine()
    motor.addImportPath(str(app_module._APP_DIR / "qml"))
    yield motor
    motor.deleteLater()


@pytest.fixture
def panelablak(engine, qt_app):
    panel_url = QUrl.fromLocalFile(
        str(app_module._APP_DIR / "qml" / "PicasaPy" / "PublishPanel.qml")
    ).toString()
    qml = f"""import QtQuick
import QtQuick.Window
Window {{
    width: 1024
    height: 212
    visible: true
    Loader {{
        id: betolto
        anchors.fill: parent
        source: "{panel_url}"
    }}
    property alias panel: betolto.item
}}"""
    comp = QQmlComponent(engine)
    comp.setData(qml.encode(), QUrl())
    ablak = comp.create()
    assert comp.errors() == [], comp.errors()
    assert ablak is not None
    panel = ablak.property("panel")
    assert panel is not None
    panel.setProperty("uzemmod", "upload")
    _KEEP_ALIVE.extend((comp, ablak))
    qt_app.processEvents()
    yield ablak, panel
    ablak.close()
    qt_app.processEvents()


def _elem(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nincs megépítve"
    return elem


def _kattints(window, qt_app, elem) -> None:
    assert elem.property("visible") is True, f"{elem.objectName()} nem látható"
    pont = elem.mapToScene(
        QPointF(elem.property("width") / 2, elem.property("height") / 2)
    ).toPoint()
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(pont.x(), pont.y()),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("ablakmagassag_eltolas", (-5, 0, 5))
def test_a_valodi_kattintas_a_spec_szerinti_modot_valasztja(
    panelablak, qt_app, ablakmagassag_eltolas
):
    """A tesztelt kattintási pont mindig az aktuális vezérlő geometriájából jön."""
    window, panel = panelablak
    window.setHeight(window.height() + ablakmagassag_eltolas)
    qt_app.processEvents()

    valasztok = (
        (1, "publishUploadMode1"),
        (2, "publishUploadMode2"),
        (3, "publishUploadMode3"),
    )
    assert panel.property("feltoltesMod") == 1
    for mod, nev in valasztok:
        _kattints(window, qt_app, _elem(window, nev))
        assert panel.property("feltoltesMod") == mod
        assert [
            _elem(window, gomb).property("checked") for _, gomb in valasztok
        ] == [ertek == mod for ertek, _ in valasztok]


def test_a_feliratok_a_spec_hivatalos_angol_szovegei(panelablak):
    window, _panel = panelablak
    vart = {
        "publishUploadMode1": "Upload",
        "publishUploadMode2": "Change options",
        "publishUploadMode3": "Remove online",
    }
    for nev, felirat in vart.items():
        assert _elem(window, nev).property("text") == felirat


@pytest.mark.parametrize(
    "ablakmagassag_eltolas", (-5, 0, 5)
)
@pytest.mark.parametrize(
    ("kezdo_mod", "felirat_nev", "vart_mod"),
    (
        (1, "publishLabelUploadMode2", 2),
        (1, "publishLabelUploadMode3", 3),
        (2, "publishLabelUploadMode1", 1),
    ),
)
def test_a_feliratra_kattintas_modot_valaszt(
    panelablak, qt_app, ablakmagassag_eltolas, kezdo_mod, felirat_nev, vart_mod
):
    window, panel = panelablak
    window.setHeight(window.height() + ablakmagassag_eltolas)
    qt_app.processEvents()
    panel.setProperty("feltoltesMod", kezdo_mod)
    qt_app.processEvents()

    _kattints(window, qt_app, _elem(window, felirat_nev))

    assert panel.property("feltoltesMod") == vart_mod


@pytest.mark.parametrize("ablakmagassag_eltolas", (-5, 0, 5))
def test_a_magyar_felirat_teljes_es_a_kesz_forditast_hasznalja(
    panelablak, engine, qt_app, ablakmagassag_eltolas
):
    window, _panel = panelablak
    window.setHeight(window.height() + ablakmagassag_eltolas)
    qt_app.processEvents()
    fordito = QTranslator(qt_app)
    i18n_dir = app_module._APP_DIR / "i18n"
    assert fordito.load("picasapy_hu", str(i18n_dir)), "a magyar fordító nem tölthető be"
    qt_app.installTranslator(fordito)
    engine.retranslate()
    qt_app.processEvents()

    try:
        vart = {
            "publishLabelUploadMode1": ("Upload", "Feltöltés"),
            "publishLabelUploadMode2": (
                "Change options", "Opciók módosítása"
            ),
            "publishLabelUploadMode3": (
                "Remove online", "Eltávolítás: online elemek"
            ),
        }
        for nev, (forras, magyar) in vart.items():
            felirat = _elem(window, nev)
            assert felirat.property("text") == magyar
            assert fordito.translate("PublishPanel", forras) == magyar
            keret = _elem(window, "publishRpOptions")
            vart_szelesseg = (
                keret.property("x") + keret.property("width")
                - felirat.property("x")
            )
            assert felirat.property("width") == pytest.approx(vart_szelesseg)

        qml = (app_module._APP_DIR / "qml" / "PicasaPy" / "PublishPanel.qml")
        forras_qml = qml.read_text(encoding="utf-8")
        for nev in vart:
            kezdet = forras_qml.index(f'objectName: "{nev}"')
            vege = forras_qml.index("\n        }", kezdet)
            blokk = forras_qml[kezdet:vege]
            assert "elide: Text.ElideNone" in blokk
            assert "wrapMode: Text.WordWrap" in blokk
    finally:
        qt_app.removeTranslator(fordito)
        engine.retranslate()
