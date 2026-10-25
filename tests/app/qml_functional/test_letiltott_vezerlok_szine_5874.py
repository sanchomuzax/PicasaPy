"""A letiltott Qt Controls-felirat a témához illő szürkével rajzolódik ki (#5874)."""

from __future__ import annotations

import math

from PySide6.QtCore import QObject, QPointF, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem

from tests.support.varakozas import var_feltetelre


_VEZERLOK = """
import QtQuick
import QtQuick.Controls
import PicasaPy
ApplicationWindow {
    objectName: "paletteProbeWindow"
    visible: true
    width: 820
    height: 160
    color: Theme.canvasBg
    palette {
        window: Theme.canvasBg
        active.windowText: Theme.ink
        inactive.windowText: Theme.ink
        base: Theme.controlBase
        alternateBase: Theme.panelBg
        active.text: Theme.ink
        inactive.text: Theme.ink
        button: Theme.buttonBg
        active.buttonText: Theme.ink
        inactive.buttonText: Theme.ink
        highlight: Theme.selectionBlue
        highlightedText: Theme.panelSelectionText
        placeholderText: Theme.placeholderText
        disabled.windowText: Theme.textGray
        disabled.text: Theme.textGray
        disabled.buttonText: Theme.textGray
        mid: Theme.chromeBorder
        light: Theme.shadeLight
        dark: Theme.shadeDark
    }
    readonly property color testRootDisabledButtonText:
        palette.disabled.buttonText
    Column {
        x: 20
        y: 20
        spacing: 8
        Row {
            spacing: 12
            Button {
                objectName: "enabledButton"
                width: 190
                height: 48
                text: "Enabled action"
                font.pixelSize: Theme.fontSize
                readonly property color testDisabledPaletteText: palette.disabled.buttonText
            }
            Button {
                objectName: "disabledButton"
                width: 190
                height: 48
                text: "Disabled action"
                font.pixelSize: Theme.fontSize
                enabled: false
                readonly property color testDisabledPaletteText: palette.disabled.buttonText
            }
        }
        Row {
            spacing: 12
            TextField {
                objectName: "enabledField"
                width: 190
                height: 48
                text: "Enabled value"
                font.pixelSize: Theme.fontSize
                readonly property color testLabelColor: palette.text
            }
            TextField {
                objectName: "disabledField"
                width: 190
                height: 48
                text: "Disabled value"
                font.pixelSize: Theme.fontSize
                enabled: false
                readonly property color testLabelColor: palette.disabled.text
            }
        }
    }
}
"""


def _gyerek(gyoker: QObject, nev: str) -> QQuickItem:
    item = gyoker.findChild(QQuickItem, nev)
    assert item is not None, f"{nev} nem található a kirajzolt vezérlők között"
    return item


def _theme(engine):
    komponens = QQmlComponent(engine)
    komponens.setData(
        b"import QtQuick\nimport PicasaPy\nQtObject { property var tema: Theme }",
        QUrl(),
    )
    holder = komponens.create()
    assert holder is not None, komponens.errorString()
    holder.setParent(engine)
    return holder.property("tema"), holder, komponens


def _legkozelebbi_feliratpixel(
    kep, vezerlo: QQuickItem, vart_szin: QColor
) -> tuple[QColor, int]:
    """A vezérlő képkivágásában megkeresi a tintához legközelebbi feliratpixelt."""
    jelenet = vezerlo.mapToScene(QPointF(0, 0))
    dpr = kep.devicePixelRatio()
    bal = max(0, math.floor(jelenet.x() * dpr))
    felso = max(0, math.floor(jelenet.y() * dpr))
    jobb = min(kep.width(), math.ceil((jelenet.x() + vezerlo.width()) * dpr))
    also = min(kep.height(), math.ceil((jelenet.y() + vezerlo.height()) * dpr))

    legjobb = QColor()
    tavolsag = 256 * 3
    for y in range(felso, also):
        for x in range(bal, jobb):
            pixel = kep.pixelColor(x, y)
            aktualis = (
                abs(pixel.red() - vart_szin.red())
                + abs(pixel.green() - vart_szin.green())
                + abs(pixel.blue() - vart_szin.blue())
            )
            if aktualis < tavolsag:
                tavolsag = aktualis
                legjobb = pixel
    return legjobb, tavolsag


def test_a_letiltott_gomb_es_mezo_felirata_szurke_a_kirajzolt_ablakban(
    qml_app, qt_app
):
    _main_window, controller, engine = qml_app
    import picasapy.app.application as app_module

    for qml_name in ("Main.qml", "PicasaPy/ImportSourceDialog.qml"):
        source = (app_module._APP_DIR / "qml" / qml_name).read_text(
            encoding="utf-8"
        )
        for role in ("windowText", "text", "buttonText"):
            assert f"disabled.{role}: Theme.textGray" in source, (
                f"{qml_name}: hiányzik a disabled.{role} Theme-kötése"
            )
            for group in ("active", "inactive"):
                assert f"{group}.{role}: Theme.ink" in source, (
                    f"{qml_name}: hiányzik a {group}.{role} Theme-kötése"
                )

    komponens = QQmlComponent(engine)
    komponens.setData(_VEZERLOK.encode("utf-8"), QUrl())
    hibak = [hiba.toString() for hiba in komponens.errors()]
    assert hibak == [], hibak
    probe = komponens.create()
    assert probe is not None, komponens.errorString()

    tema, tema_holder, tema_komponens = _theme(engine)
    assert tema is not None, "a Theme szingleton nem érhető el a főablakból"
    alapmagassag = probe.height()

    for sotet in (False, True):
        controller.setDarkTheme(sotet)
        assert var_feltetelre(
            qt_app,
            lambda sotet=sotet: bool(tema.property("dark")) is sotet,
            3.0,
        ), f"a Theme nem váltott {'sötét' if sotet else 'világos'} módra"
        vart_szurke = QColor(tema.property("textGray"))

        for eltolás in (-5, 0, 5):
            probe.setHeight(alapmagassag + eltolás)
            assert abs(probe.height() - (alapmagassag + eltolás)) <= 3, (
                "a próbaablak nem vette fel a kért, ±5 px-es próbaméretet"
            )
            qt_app.processEvents()
            kep = probe.grabWindow()
            assert not kep.isNull(), "a próbaablak renderelt képe üres"

            gyoker_csoportszin = QColor(
                probe.property("testRootDisabledButtonText")
            )
            assert gyoker_csoportszin == vart_szurke, (
                "a Main.qml ablakpalettájának disabled.buttonText színe "
                f"nem Theme.textGray: {gyoker_csoportszin.name()} "
                f"!= {vart_szurke.name()}"
            )

            disabled_button = _gyerek(probe, "disabledButton")
            csoportszin = QColor(
                disabled_button.property("testDisabledPaletteText")
            )
            assert csoportszin == vart_szurke, (
                "a főablak disabled.buttonText csoportja nem örökli "
                f"a Theme.textGray értékét: {csoportszin.name()} "
                f"!= {vart_szurke.name()}"
            )

            pixel_szin = {}
            for nev in (
                "enabledButton",
                "disabledButton",
                "enabledField",
                "disabledField",
            ):
                vezerlo = _gyerek(probe, nev)
                if "Button" in nev:
                    felirat = vezerlo.property("contentItem")
                    assert isinstance(felirat, QQuickItem), f"{nev}: nincs kirajzolt felirat"
                    szin = QColor(felirat.property("color"))
                else:
                    szin = QColor(vezerlo.property("testLabelColor"))
                pixel, tavolsag = _legkozelebbi_feliratpixel(kep, vezerlo, szin)
                assert tavolsag <= 24, (
                    f"{nev}: a renderelt feliratpixel nem követi a színét; "
                    f"távolság={tavolsag}, elvárt={szin.name()}, "
                    f"mért={pixel.name()}"
                )
                pixel_szin[nev] = pixel

            for aktiv, letiltott in (
                ("enabledButton", "disabledButton"),
                ("enabledField", "disabledField"),
            ):
                assert pixel_szin[aktiv] != pixel_szin[letiltott], (
                    f"{letiltott}: a renderelt feliratpixel megegyezik az "
                    f"engedélyezett {aktiv} feliratával ({pixel_szin[aktiv].name()})"
                )

            assert QColor(
                _gyerek(probe, "disabledField").property("testLabelColor")
            ) == vart_szurke, (
                f"a letiltott mező palettafelirata nem Theme.textGray: "
                f"{QColor(_gyerek(probe, 'disabledField').property('testLabelColor')).name()} "
                f"!= {vart_szurke.name()}"
            )

    controller.setDarkTheme(False)
    probe.close()
    probe.deleteLater()
    komponens.deleteLater()
    tema_holder.deleteLater()
    tema_komponens.deleteLater()
