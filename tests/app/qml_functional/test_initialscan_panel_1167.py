"""Az első indítás panelje — az eredeti `initialscan` viselkedése (#1167).

Az eredeti bizonyítéka: `docs/specs/picasa-elso-inditas.md` (a
`tre:initialscan` szó szerinti szövegei; a kezelő `0x005b7e80`; a
kétlépcsős migráció `0x005b7eeb`; a bezárás-megszakítás `0x005b7e69`).
"""

from PySide6.QtCore import QMetaObject, QObject, Qt


def _elem(window, nev):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _nyisd(window, controller, qt_app, monkeypatch, migracio):
    monkeypatch.setattr(
        type(controller), "initialScanMigration", lambda self: migracio,
        raising=False,
    )
    parbeszed = _elem(window, "initialScanDialog")
    # a fixture könyvtárában VAN figyelt mappa — a panel feltételét
    # közvetlenül nem tudjuk előállítani, ezért a megnyitó belsejét hívjuk
    parbeszed.setProperty("migrationStep", bool(migracio))
    parbeszed.setProperty("updateChosen", False)
    parbeszed.setProperty("choice", "narrow")
    QMetaObject.invokeMethod(parbeszed, "open", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    return parbeszed


def _folytatas(parbeszed, qt_app):
    QMetaObject.invokeMethod(
        parbeszed, "acceptChoice", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


class TestTisztaTelepites:
    def test_a_szovegek_az_eredetiek(self, qml_app, qt_app, monkeypatch):
        window, controller, _ = qml_app
        _nyisd(window, controller, qt_app, monkeypatch, migracio=False)

        assert str(_elem(window, "initialScanQuestionText").property("text")) == (
            "Picasa is ready to search for pictures on your computer"
        )
        assert "whole computer" in str(
            _elem(window, "initialScanWide").property("text")
        )
        assert "never moves or copies files" in str(
            _elem(window, "initialScanReassuranceText").property("text")
        )

    def test_continue_a_valasztast_alkalmazza_es_zar(
        self, qml_app, qt_app, monkeypatch
    ):
        window, controller, _ = qml_app
        hivasok = []
        monkeypatch.setattr(
            type(controller), "applyInitialScan",
            lambda self, choice: hivasok.append(choice), raising=False,
        )
        parbeszed = _nyisd(window, controller, qt_app, monkeypatch, migracio=False)
        parbeszed.setProperty("choice", "wide")

        _folytatas(parbeszed, qt_app)

        assert hivasok == ["wide"]
        assert parbeszed.property("visible") is False


class TestMigracio:
    def test_a_migracios_szovegek_az_eredetiek(self, qml_app, qt_app, monkeypatch):
        window, controller, _ = qml_app
        _nyisd(window, controller, qt_app, monkeypatch, migracio=True)

        assert "older version of Picasa" in str(
            _elem(window, "initialScanQuestionText").property("text")
        )
        assert str(_elem(window, "initialScanNarrow").property("text")) == (
            "Update my existing picture library"
        )
        assert str(_elem(window, "initialScanWide").property("text")) == (
            "Search my computer for pictures again"
        )

    def test_a_frissites_valasztas_KETLEPCSOS(self, qml_app, qt_app, monkeypatch):
        """`0x005b7eeb`: a „frissítés" után ugyanaz az ablak átvált a
        keresési kérdésre, és NYITVA marad."""
        window, controller, _ = qml_app
        hivasok = []
        monkeypatch.setattr(
            type(controller), "applyInitialScan",
            lambda self, choice: hivasok.append(choice), raising=False,
        )
        parbeszed = _nyisd(window, controller, qt_app, monkeypatch, migracio=True)
        parbeszed.setProperty("choice", "narrow")  # „frissítés"

        _folytatas(parbeszed, qt_app)

        assert parbeszed.property("visible") is True, "az ablaknak nyitva kell maradnia"
        assert parbeszed.property("migrationStep") is False, (
            "át kellett váltania a keresési kérdésre"
        )
        assert hivasok == [], "az első lépcső még nem alkalmazhat semmit"
        assert "ready to search" in str(
            _elem(window, "initialScanQuestionText").property("text")
        )

    def test_a_frissites_utan_a_masodik_Continue_importot_nyit(
        self, qml_app, qt_app, monkeypatch
    ):
        """A jegy kérése: a migrációs ág a meglévő Picasa-átvételt
        (#146, PicasaImportDialog) használja."""
        window, controller, _ = qml_app
        monkeypatch.setattr(
            type(controller), "applyInitialScan",
            lambda self, choice: None, raising=False,
        )
        parbeszed = _nyisd(window, controller, qt_app, monkeypatch, migracio=True)
        kertek = []
        parbeszed.importRequested.connect(lambda: kertek.append(True))

        parbeszed.setProperty("choice", "narrow")
        _folytatas(parbeszed, qt_app)   # 1. lépcső: átváltás
        _folytatas(parbeszed, qt_app)   # 2. lépcső: keresés + import

        assert kertek, "a frissítés-ág nem kérte a Picasa-átvételt"
        assert parbeszed.property("visible") is False

    def test_az_ujrakereses_azonnal_zar_teljes_geppel(
        self, qml_app, qt_app, monkeypatch
    ):
        """`0x005b7ee9`: a „Search my computer for pictures again" a
        teljes-gép kóddal zár, import nélkül."""
        window, controller, _ = qml_app
        hivasok = []
        monkeypatch.setattr(
            type(controller), "applyInitialScan",
            lambda self, choice: hivasok.append(choice), raising=False,
        )
        parbeszed = _nyisd(window, controller, qt_app, monkeypatch, migracio=True)
        kertek = []
        parbeszed.importRequested.connect(lambda: kertek.append(True))
        parbeszed.setProperty("choice", "wide")

        _folytatas(parbeszed, qt_app)

        assert hivasok == ["wide"]
        assert parbeszed.property("visible") is False
        assert kertek == []
