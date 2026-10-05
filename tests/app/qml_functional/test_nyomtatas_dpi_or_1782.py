"""#1782 — a nyomtatási párbeszéd minőség-ellenőrzése a felületen.

A `printing/dpi.py` a számolást méri; ez a fájl azt, hogy a felhasználó
**látja** is. A jegy nyitómondata:

> A felhasználó ma úgy nyomtathat ki egy 640×480-as képet 8×10-re, hogy a
> program egy szót sem szól.

Két külön dolog kell hozzá, és a teszt mindkettőt méri: legyen
**nyomatméret-választó** (enélkül a DPI-nek nincs mihez képest értelme),
és a mondat **kövesse** a választást.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtQml import QQmlExpression, qmlContext

from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre

_QML = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/PrintDialog.qml"
)


def _forras() -> str:
    return _QML.read_text(encoding="utf-8")


class TestAFeluletenMegvan:
    def test_van_nyomatmeret_valaszto(self):
        assert 'objectName: "printSizeBox"' in _forras(), (
            "nincs nyomatméret-választó — a DPI-nek nincs mihez képest "
            "értelme (#1782)"
        )

    def test_van_minoseg_sor(self):
        assert 'objectName: "printQualityText"' in _forras()

    def test_a_valasztas_ELTEVODIK(self):
        """`PrintLastSize` — a méret túléli az újraindítást."""
        assert "setPrintSize(" in _forras(), (
            "a nyomatméret nem tevődik el — minden indításnál alapértékre "
            "esne vissza"
        )

    def test_a_valasztas_UJRAMER(self):
        """Méretváltáskor a mondatnak követnie kell."""
        forras = _forras()
        assert forras.count("frissitsdAMinoseget()") >= 2, (
            "a méretváltás nem méri újra a minőséget — a mondat a régi "
            "mérethez tartozó számot mutatná"
        )

    def test_mind_a_harom_mondat_szerepel(self):
        forras = _forras()
        for mondat in (
            "Smallest picture: %1 pixels/inch.",
            "Please review before printing.\\n%1 small %2 found.",
            "You are ready to print.",
        ):
            assert mondat in forras, f"hiányzik: {mondat!r}"

    def test_az_egyes_es_a_tobbes_szam_KULON_van(self):
        """Az eredetiben is két külön erőforrás (`::picture`/`::pictures`),
        amelyet a `ReviewPrompt` `%2`-ként kap meg (#3573)."""
        forras = _forras()
        assert 'qsTr("picture")' in forras
        assert 'qsTr("pictures")' in forras


class TestAzEloFaban:
    def test_a_parbeszed_felepul_a_valasztoval(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        from support.halasztott_parbeszed import nyisd_meg

        nyisd_meg(window, "printDialog")
        qt_app.processEvents()
        assert window.findChild(QObject, "printSizeBox") is not None
        assert window.findChild(QObject, "printQualityText") is not None


class TestMinosegiSavok:
    def test_az_ellenorzo_lista_minden_savot_megjelenit(self, qml_app, qt_app, tmp_path):
        """A teljes listán a három sáv ténylegesen megjelenik, nem csak számolódik."""
        from support.halasztott_parbeszed import nyisd_meg

        class Photo:
            def __init__(self, folder, name, width, height):
                self.folder_path = str(folder)
                self.name = name
                self.width = width
                self.height = height

        window, _controller, engine = qml_app
        window.setProperty("selectedIndexes", [0, 1])
        nyisd_meg(window, "printDialog")
        dialog = window.findChild(QObject, "printDialog")
        assert dialog is not None

        foto_mappa = tmp_path / "savok"
        foto_mappa.mkdir()
        meretek = {
            "best.jpg": (900, 600),
            "good.jpg": (600, 400),
            "bad.jpg": (594, 396),
        }
        for nev, meret in meretek.items():
            make_jpeg(foto_mappa / nev, size=meret)
        print_controller = engine.rootContext().contextProperty("printController")
        assert print_controller is not None
        print_controller._photo_source = lambda: [
            Photo(foto_mappa, nev, *meret)
            for nev, meret in meretek.items()
        ]
        dialog.setProperty("rows", [0, 1, 2])
        dialog.setProperty("printSize", "M4X6")
        assert QMetaObject.invokeMethod(
            dialog, "frissitsdAMinoseget", Qt.ConnectionType.DirectConnection
        )

        review_button = dialog.findChild(QObject, "printReviewButton")
        assert review_button is not None
        assert review_button.property("visible") is True
        assert QMetaObject.invokeMethod(
            review_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        assert varj_feltetelre(
            qt_app, lambda: dialog.property("reviewOpen") is True, 3
        ), "az Ellenőrzés gomb nem nyitotta meg a minőséglistát"

        lista = dialog.findChild(QObject, "printReviewList")
        assert lista is not None

        def sav_feliratok():
            feliratok = []
            for index in range(3):
                expression = QQmlExpression(
                    qmlContext(lista), lista, f"itemAtIndex({index})"
                )
                value, error = expression.evaluate()
                assert not error, expression.error()
                if value is None:
                    return []
                feliratok.append(value)
            return feliratok

        assert varj_feltetelre(qt_app, lambda: len(sav_feliratok()) == 3, 3), (
            "a teljes képlista nem épült fel a három minőségi felirattal"
        )
        feliratok = [
            elem.findChild(QObject, "printReviewListRowText").property("text")
            for elem in sav_feliratok()
        ]
        assert [
            next(nev for nev in ("bad.jpg", "good.jpg", "best.jpg") if nev in szoveg)
            for szoveg in feliratok
        ] == ["bad.jpg", "good.jpg", "best.jpg"]
        assert "Bad quality (99 pixels/inch)" in feliratok[0]
        assert "Good quality (100 pixels/inch)" in feliratok[1]
        assert "Best quality (150 pixels/inch)" in feliratok[2]

        # A sorok és a feliratok az ablakmagasság ±5 px eltérésénél is
        # ugyanazok maradnak; itt nem rögzítünk betűméretet vagy pixelhelyet.
        alapmagassag = int(dialog.property("height"))
        for magassag in (alapmagassag - 5, alapmagassag, alapmagassag + 5):
            dialog.setProperty("height", magassag)
            assert varj_feltetelre(
                qt_app,
                lambda vart=magassag: int(dialog.property("height")) == vart
                and len(sav_feliratok()) == 3,
                3,
            ), f"az ellenőrzőlista nem állt helyre {magassag} px magasságnál"
