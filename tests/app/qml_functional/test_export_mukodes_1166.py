"""Az exportálás működése a felületen (#1166).

Az eredeti levezetése: `docs/specs/export-parbeszed.md` 8., 12.1 és 13.
szakasz. A mappa-export, az e-mail és a képernyővédő közös magja a
`CImageOutput` (`0x0073f320`); a párbeszéd alapértékeit a
`CExportPrefsDialog` (`0x0073b500`, `0x00738d16`) adja.
"""

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt

from support.halasztott_parbeszed import epitsd_fel


def _elem(window, nev):
    # #1720: az itt keresett elemek a HALASZTOTT párbeszéd
    # belsejében ülnek — előbb fel kell épülnie, a valódi
    # menüponton át (ld. support/halasztott_parbeszed.py).
    epitsd_fel(window, "exportDialog")
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _megnyit(window, qt_app, sor=0):
    window.setProperty("selectedIndexes", [sor])
    window.setProperty("selectedIndex", sor)
    qt_app.processEvents()
    parbeszed = _elem(window, "exportDialog")
    QMetaObject.invokeMethod(
        parbeszed, "openForSelection", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    return parbeszed


class TestBelepesiPontok:
    """Az eredetiben HÁROM belépési pont van (Fájl menü `0x9c81`, a
    kimeneti sáv gombja `0x005dac55`, és egy harmadik út) — mindegyik
    UGYANAZT a párbeszédet nyitja (`0x005312b0`)."""

    def test_a_menu_es_a_talca_gombja_ugyanazt_nyitja(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        parbeszed = _elem(window, "exportDialog")

        # 1. út: a menü/gyorsbillentyű kezelője
        QMetaObject.invokeMethod(
            parbeszed, "openForSelection", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert parbeszed.property("visible") is True
        QMetaObject.invokeMethod(
            parbeszed, "close", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        # 2. út: a tálca „Exportálás" gombjának jelzése
        talca = _elem(window, "trayBar")
        QMetaObject.invokeMethod(
            talca, "exportRequested", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert parbeszed.property("visible") is True, (
            "a tálca gombja nem ugyanazt a párbeszédet nyitotta"
        )


class TestAlapertekek:
    def test_a_mappanev_alapertelmezese_a_forrasmappa_neve(self, qml_app, qt_app):
        """Spec 12.1: a név a kiválasztott album/mappa neve
        (`0x0073b500`); üres névnél a honosított „export"."""
        window, controller, _engine = qml_app
        _megnyit(window, qt_app)

        mezo = _elem(window, "exportFolderNameField")
        assert str(mezo.property("text")) == Path(controller.currentFolder).name

    def test_a_hely_alapertelmezese_kitoltodik(self, qml_app, qt_app):
        """Spec 12.1: a hely a korábban használt mappa, hiányában a képek
        mappájában lévő gyűjtő — a mező nem maradhat üresen."""
        window, _controller, _engine = qml_app
        parbeszed = _megnyit(window, qt_app)

        assert str(parbeszed.property("targetFolder")), "a hely üresen maradt"


class TestFilmRadio:
    def test_a_taroltbol_indul_es_visszairodik(self, qml_app, qt_app):
        """Spec: az alapérték a `FileExportMovie` megfelelője — nem
        nulla → „Teljes film", nulla/hiányzó → „Első képkocka"."""
        window, controller, _engine = qml_app
        controller.setExportMovieFull(True)

        parbeszed = _megnyit(window, qt_app)

        assert parbeszed.property("movieFull") is True
        assert _elem(window, "exportMovieFull").property("checked") is True

    def test_film_nelkuli_kijelolesnel_le_van_tiltva(self, qml_app, qt_app):
        """A `.fen` nem ad kötést erre — futásidejű döntés (spec 9.3/2):
        film nélkül mindkét rádió szürke."""
        window, _controller, _engine = qml_app
        _megnyit(window, qt_app)

        assert _elem(window, "exportMovieFirstFrame").property("enabled") is False
        assert _elem(window, "exportMovieFull").property("enabled") is False


class TestCelmappaUtkozes:
    def test_letezo_celmappanal_megkerdez(self, qml_app, qt_app, tmp_path):
        """`CExportPrefsPage::destexists` — „A cél már létezik. Felülírja
        az új albummal?" Az export csak a válasz után indul."""
        window, _controller, _engine = qml_app
        parbeszed = _megnyit(window, qt_app)
        cel = tmp_path / "mar-van"
        cel.mkdir()
        nev = str(_elem(window, "exportFolderNameField").property("text"))
        (cel / nev).mkdir()
        (cel / nev / "regi.jpg").write_bytes(b"regi")
        parbeszed.setProperty("targetFolder", cel.as_uri())
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            parbeszed, "accept", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert _elem(window, "exportOverwriteDialog").property("visible") is True

    def test_ures_celmappanal_nem_kerdez(self, qml_app, qt_app, tmp_path):
        """Megőrző: nincs mit felülírni, ne álljunk a felhasználó útjába."""
        window, _controller, _engine = qml_app
        parbeszed = _megnyit(window, qt_app)
        cel = tmp_path / "ures"
        cel.mkdir()
        parbeszed.setProperty("targetFolder", cel.as_uri())
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            parbeszed, "accept", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert _elem(window, "exportOverwriteDialog").property("visible") is False


class TestHibaszovegek:
    def test_a_hibas_futas_cime_Hiba(self, qml_app, qt_app):
        """`CExportPrefsPage::errortitle` — hibás futásnál a párbeszéd
        címe „Hiba", sikeresnél marad az „Export"."""
        window, controller, _engine = qml_app
        parbeszed = _elem(window, "exportResultDialog")

        controller.exportFailedDetails.emit(["valami baj"])
        qt_app.processEvents()

        assert str(parbeszed.property("title")) == "Error"

    def test_ures_koteg_eseten_az_eredeti_uzenete_megy_ki(self, qml_app, qt_app):
        """`IDS_NO_IMAGES_TO_SEND` — „Nem állt rendelkezésre kép a
        küldéshez." Az eredeti sem hallgat el egy üres köteget."""
        window, controller, _engine = qml_app
        uzenetek = []
        controller.exportFailedDetails.connect(uzenetek.append)

        controller.exportRows([], "/tmp/nem-hasznaljuk", 0, 85)
        qt_app.processEvents()

        assert uzenetek, "üres kötegre semmilyen jelzés nem ment ki"
        assert "No images were available to send." in uzenetek[0][0]
