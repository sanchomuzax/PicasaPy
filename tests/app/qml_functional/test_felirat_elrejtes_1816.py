"""#1816 — a felirat elrejthető és egy mozdulattal törölhető.

## A lelet

Az eredetiben a felirathoz **két külön vezérlő** tartozik:

| elem | buboréksúgó |
|---|---|
| `captionbutton` | „Show/Hide Caption” |
| `captiontrash` | „Delete this caption” |

Nálunk egyik sem volt meg: a mező mindig ott volt, és a szöveget kézzel
kellett kijelölni és kitörölni.

## ⭐ A láthatóság TARTÓS

Nem pillanatnyi kapcsoló: a `Preferences\\LastCaptionButton` őrzi, és a
főablak-építő (`0x0040bf70`) induláskor visszaállítja.

## A KÉT belépési pontról — mérve, nem feltételezve

A jegy előírja, hogy az elrejtés **mindkét** nézetben elérhető legyen
(`editpanel/` és `editoneup/captionbutton`). Nálunk a szerkesztő panel a
**nézőn belül** él (`EditorPanel` ugyanabban a fájlban, `PhotoViewer.qml`),
tehát egy sáv szolgálja mindkét állapotot. A teszt ezt **méri**: a sáv
láthatósága nem függ a szerkesztő nyitottságától.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt

_VIEWER_QML = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/PhotoViewer.qml"
)


def _gyerek(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _nyisd_a_nezot(window, qt_app):
    """⚠️ Egy elem `visible`-je HAMIS, amíg a szülője rejtett — zárt
    nézőben minden gyereke rejtettnek látszana, és a teszt hamisan
    bukna."""
    window.setProperty("viewerOpen", True)
    qt_app.processEvents()


class TestAVezerlokMegvannak:
    def test_van_elrejto_gomb(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        assert window.findChild(QObject, "captionToggleButton") is not None, (
            "nincs „Show/Hide Caption\" vezérlő (#1816)"
        )

    def test_van_torlo_gomb(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        assert window.findChild(QObject, "captionTrashButton") is not None, (
            "nincs „Delete this caption\" vezérlő (#1816)"
        )

    def test_a_torlo_gomb_ures_feliratnal_TILTOTT(self, qml_app, qt_app):
        """Nincs mit törölni — a gomb ne kínáljon hatástalan kattintást."""
        window, _controller, _engine = qml_app
        mezo = _gyerek(window, "captionField")
        if (mezo.property("text") or "") == "":
            assert _gyerek(window, "captionTrashButton").property(
                "enabled"
            ) is False


class TestALathatosagTartos:
    def test_az_allapot_a_vezerlon_el(self, qml_app, qt_app):
        """A `LastCaptionButton` megfelelője — nem QML-property."""
        _window, controller, _engine = qml_app
        assert controller.captionVisible is True, "alapból látszik"

    def test_a_kapcsolo_billent(self, qml_app, qt_app):
        _window, controller, _engine = qml_app
        eredeti = controller.captionVisible
        try:
            controller.toggleCaptionVisible()
            assert controller.captionVisible is not eredeti
        finally:
            controller.setCaptionVisible(eredeti)

    def test_a_sav_KOVETI_a_vezerlot(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _nyisd_a_nezot(window, qt_app)
        sav = _gyerek(window, "captionBar")
        try:
            controller.setCaptionVisible(False)
            qt_app.processEvents()
            assert sav.property("visible") is False, (
                "a felirat-sáv nem tűnt el, pedig a beállítás rejtve van"
            )
            controller.setCaptionVisible(True)
            qt_app.processEvents()
            assert sav.property("visible") is True
        finally:
            controller.setCaptionVisible(True)

    def test_rejtve_is_van_UT_a_visszahozashoz(self, qml_app, qt_app):
        """Az elrejtés ne legyen egyirányú: a felhasználó ne a
        beállítások közt keresse a visszakapcsolót."""
        window, controller, _engine = qml_app
        _nyisd_a_nezot(window, qt_app)
        vissza = _gyerek(window, "captionRevealButton")
        try:
            controller.setCaptionVisible(False)
            qt_app.processEvents()
            assert vissza.property("visible") is True
        finally:
            controller.setCaptionVisible(True)


class TestAKetBelepesiPont:
    def test_a_sav_a_SZERKESZTO_allapotatol_fuggetlen(self):
        """A jegy két belépési pontot ír elő. Nálunk a szerkesztő a nézőn
        BELÜL él, tehát egy sáv szolgálja mindkettőt — de ezt mérni kell,
        nem feltételezni: a sáv `visible`-je nem hivatkozhat a szerkesztő
        nyitottságára."""
        forras = _VIEWER_QML.read_text(encoding="utf-8")
        kezdet = forras.index('objectName: "captionBar"')
        blokk = forras[kezdet : kezdet + 400]
        assert "visible: viewer.captionVisible" in blokk, (
            "a felirat-sáv láthatósága nem csak a beállításon múlik"
        )
        assert "editorPanel" not in blokk, (
            "a sáv a szerkesztő állapotára hivatkozik — akkor az egyik "
            "nézetben hiányozna (#1816)"
        )

    def test_a_szerkeszto_panel_a_nezon_belul_van(self):
        """A fenti következtetés alapja — ha ez megváltozik, a fenti
        teszt önmagában már nem elég, és ezt itt kell megtudni."""
        forras = _VIEWER_QML.read_text(encoding="utf-8")
        assert "EditorPanel {" in forras, (
            "a szerkesztő panel kikerült a nézőből — a #1816 két belépési "
            "pontját újra kell mérni"
        )


class TestATorles:
    def test_a_torles_a_vezerlot_hivja(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        gomb = _gyerek(window, "captionTrashButton")
        hivasok = []
        eredeti = controller.setCaption
        controller.setCaption = lambda sor, szoveg: hivasok.append(
            (sor, szoveg)
        )
        try:
            gomb.setProperty("enabled", True)
            QMetaObject.invokeMethod(
                gomb, "clicked", Qt.ConnectionType.DirectConnection
            )
            qt_app.processEvents()
        finally:
            controller.setCaption = eredeti

        assert hivasok, "a törlő gomb nem hívta a vezérlőt"
        assert hivasok[0][1] == "", (
            "a törlés nem ÜRES szöveget küld — az ini-kulcs eltávolítása "
            "ehhez kötött (`with_removed`)"
        )
