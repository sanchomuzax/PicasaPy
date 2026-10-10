"""Egyéni méretarány: hivatalos feliratú párbeszéd, szakaszcím a legördülőben,
a törlés a kombó melletti kukával (#4550).

Az eredeti `customaspectratio.fen`-ben a „Példa:" sor STATIKUS `<label>`
(nincs `bind`, nincs `name`) — ezért nem élő; a sor szövege a hivatalos
katalógusból való (angolul „   4 x 6   Small print"; a QML-teszt fordító
nélkül fut, a magyart a `.ts`-teszt méri). A ui-audit „feltehetően
élő" mondata képernyőkép-alapú feltevés volt.

Amit ez a fájl NEM mér: a kuka ikonjának pixelpontos egyezését az eredetivel
(csak a méretét, 14 × 14, és hogy látszik/tiltott).
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest


def _megnyit(window, qt_app):
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    panel = window.findChild(QObject, "viewerEditorPanel")
    panel.setProperty("cropActive", True)
    qt_app.processEvents()
    return panel


def _kozep(elem):
    return elem.mapToScene(
        QPointF(elem.width() / 2, elem.height() / 2)).toPoint()


def _klikk(window, qt_app, elem):
    pont = _kozep(elem)
    QTest.mouseMove(window, pont, 10)
    qt_app.processEvents()
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        pont)
    qt_app.processEvents()


def _felvesz(panel, qt_app, w=4.0, h=6.0, nev="Small print"):
    dialog = panel.findChild(QObject, "addCustomAspectRatioDialog")
    dialog.created.emit(w, h, nev)
    qt_app.processEvents()


class TestParbeszed:
    def test_feliratok_hivatalosak_es_a_pelda_statikus(self, qml_app, qt_app):
        window, _, _ = qml_app
        panel = _megnyit(window, qt_app)
        dialog = panel.findChild(QObject, "addCustomAspectRatioDialog")
        dialog.open()
        qt_app.processEvents()

        def szoveg(nev):
            elem = dialog.findChild(QObject, nev)
            assert elem is not None, nev
            return elem.property("text")

        assert szoveg("customAspectDimensionsLabel") == "Dimensions:"
        assert szoveg("customAspectNameLabel") == "Name:"
        assert szoveg("customAspectExampleLabel") == "Example:"
        assert szoveg("customAspectExampleText") == "   4 x 6   Small print"
        assert dialog.findChild(QObject, "customAspectWidthLabel") is None
        assert dialog.property("title") == "Add Custom Aspect Ratio"

    def test_gepelesre_a_pelda_nem_valtozik(self, qml_app, qt_app):
        window, _, _ = qml_app
        panel = _megnyit(window, qt_app)
        dialog = panel.findChild(QObject, "addCustomAspectRatioDialog")
        dialog.open()
        qt_app.processEvents()
        szel = dialog.findChild(QObject, "customAspectWidthField")
        szel.forceActiveFocus()
        QTest.keyClick(window, Qt.Key.Key_9)
        qt_app.processEvents()
        assert szel.property("text") == "9"
        pelda = dialog.findChild(QObject, "customAspectExampleText")
        assert pelda.property("text") == "   4 x 6   Small print"


class TestKuka:
    def test_szakaszcim_a_listaban_pontosan_egyszer_latszik(
        self, qml_app, qt_app
    ):
        window, _, _ = qml_app
        panel = _megnyit(window, qt_app)
        window.findChild(QObject, "cropAspectList").setProperty("visible", True)
        qt_app.processEvents()

        def latszo():
            """(y, szöveg) a látható szakaszcímekről — a Repeater-delegátok
            nem QObject-gyerekek, ezért a vizuális gyerekeken át járjuk be."""
            oszlop = window.findChild(QObject, "cropAspectColumn")
            talalat = []

            def bejar(elem):
                for gyerek in elem.childItems():
                    if (gyerek.objectName() == "cropAspectCustomHeading"
                            and gyerek.isVisible()):
                        talalat.append((
                            gyerek.mapToScene(QPointF(0, 0)).y(),
                            gyerek.property("text")))
                    bejar(gyerek)

            bejar(oszlop)
            return talalat

        # nincs egyéni arány: az „Add" sor fölött áll
        assert [t for _, t in latszo()] == ["Custom Aspect Ratios"]
        # van egyéni arány: az első egyéni sor fölött, még mindig egyszer
        _felvesz(panel, qt_app)
        _felvesz(panel, qt_app, 5.0, 7.0, "Large print")
        window.findChild(QObject, "cropAspectList").setProperty("visible", True)
        qt_app.processEvents()
        talalat = latszo()
        assert [t for _, t in talalat] == ["Custom Aspect Ratios"]
        oszlop = window.findChild(QObject, "cropAspectColumn")
        sorok = oszlop.childItems()
        # 13 beépített + 2 egyéni delegátum, utána az „Add" sor
        elso_egyeni = sorok[13]
        assert talalat[0][0] < elso_egyeni.mapToScene(QPointF(0, 0)).y() + 20
        beepitett_utolso = sorok[12]
        assert talalat[0][0] >= beepitett_utolso.mapToScene(
            QPointF(0, 0)).y() + 19

    def test_a_regi_soronkenti_torlo_nincs(self, qml_app, qt_app):
        window, _, _ = qml_app
        panel = _megnyit(window, qt_app)
        _felvesz(panel, qt_app)
        assert panel.findChild(QObject, "cropAspectDelete13") is None

    def test_beepitett_aranynal_a_kuka_tiltott(self, qml_app, qt_app):
        window, controller, _ = qml_app
        panel = _megnyit(window, qt_app)
        _felvesz(panel, qt_app)
        panel.setProperty("aspectIndex", 2)
        qt_app.processEvents()
        kuka = window.findChild(QObject, "cropDeleteCustom")
        assert kuka is not None and kuka.isVisible()
        assert kuka.property("width") == 14 and kuka.property("height") == 14
        assert kuka.property("enabled") is False
        _klikk(window, qt_app, kuka)
        confirm = panel.findChild(QObject, "deleteCustomAspectConfirmDialog")
        assert confirm.property("visible") is False
        assert len(controller.customAspectRatios) == 1

    def test_egyeni_aranynal_kattintasra_torol(self, qml_app, qt_app):
        window, controller, _ = qml_app
        panel = _megnyit(window, qt_app)
        _felvesz(panel, qt_app)
        kuka = window.findChild(QObject, "cropDeleteCustom")
        assert kuka.property("enabled") is True
        _klikk(window, qt_app, kuka)
        confirm = panel.findChild(QObject, "deleteCustomAspectConfirmDialog")
        assert confirm.property("visible") is True
        confirm.accept()
        qt_app.processEvents()
        assert controller.customAspectRatios == []


class TestMagyarFordítas:
    """A .ts a hivatalos `customaspectratio.xml` és `tooltips` szövegeit adja."""

    def test_hivatalos_magyar_feliratok(self):
        from pathlib import Path

        import picasapy.app

        ts = (Path(picasapy.app.__file__).parent / "i18n"
              / "picasapy_hu.ts").read_text(encoding="utf-8")
        for forras, fordit in (
            ("Dimensions:", "Méretek:"),
            ("Example:", "Példa:"),
            ("   4 x 6   Small print", "   4x6   kisméretű nyomat"),
            ("Deletes the current aspect ratio",
             "Törli az aktuális méretarányt"),
        ):
            assert (f"<source>{forras}</source>" in ts), forras
            blokk = ts.split(f"<source>{forras}</source>")[1].split(
                "</message>")[0]
            assert f"<translation>{fordit}</translation>" in blokk, forras
