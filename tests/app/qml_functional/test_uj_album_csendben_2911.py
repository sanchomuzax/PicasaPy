"""A kijelöléses „Új album" utak csendben hoznak létre albumot (#2911).

## A mérés

Az eredeti `thumbui/newalbum` kezelője (`0x005eb810`, 245 bájt) **nem nyit
névbekérőt**: felépíti az album-leírót, a nevét az `IDS_DEFAULT_ALBUM_NAME`
erőforrásból tölti (`0x0055cfb2 push 0x8a`), létrehozza az albumot, és kész.
Nincs számozás és nincs dátum — minden alkalommal ugyanaz a név.

## Amit ez az őr állít

- a Fájl menü, a Ctrl+N, a kép-helyi menü és a bal hasábra ejtés
  névbekérés nélkül készít albumot; az eszköztár útja a #5812 szerint
  külön Album Properties párbeszédet használ;
- a név a felület saját, FORDÍTHATÓ felirata (a próba-motorban a forrásalak
  `Untitled`; hogy magyarul „Névtelen", azt a
  `tests/app/test_ujalbum_nev_forditas_2911.py` méri a `.qm`-ből);
- ⛔ üres kijelölésnél nem történik semmi — nálunk az album a
  `.picasa.ini`-ben él (`[.album:<token>]`), tehát TAG nélkül nincs hova
  kiírni. Az eredetinek adatbázisa volt, ott az üres album is létezhetett.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt


def _elem(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"a(z) {nev} nincs a jelenetben"
    return objektum


def _kijelol(window, qt_app, sor: int) -> None:
    window.setProperty("selectedIndex", sor)
    window.setProperty("selectedIndexes", [sor])
    qt_app.processEvents()


class TestEszkoztarParbeszed:
    def test_az_eszkoztar_gombja_album_properties_parbeszedet_nyit(
        self, qml_app, qt_app
    ):
        """A #5812 eszköztárútja nem a kijelöléses albumkészítő út."""
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, 0)
        assert _elem(window, "toolbarNewAlbumButton") is not None

        _elem(window, "mainToolbar").newAlbumRequested.emit()
        qt_app.processEvents()

        dialog = _elem(window, "toolbarNewAlbumPropertiesDialog")
        assert dialog.property("opened") is True
        assert dialog.property("title") == "Album Properties"
        name_field = _elem(dialog, "folderPropertiesNameField")
        assert name_field.property("text") == "Untitled"
        assert name_field.property("selectedText") == "Untitled"
        assert controller.albums == []


class TestKijelolesesBelepo:
    def test_a_menutetel(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, 0)

        QMetaObject.invokeMethod(
            _elem(window, "menuFileNewAlbum"),
            "triggered",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert [a["name"] for a in controller.albums] == ["Untitled"]

    def test_a_racs_helyi_menuje(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, 0)

        _elem(window, "photoContextMenu").newAlbumRequested.emit()
        qt_app.processEvents()

        assert [a["name"] for a in controller.albums] == ["Untitled"]

    # #5105: a bal hasábra ejtést valódi egérhúzás teszteli: test_huzas_hianyzoi_5008.py (új album terület).


class TestNincsParbeszed:
    def test_a_nevbekero_MEGSZUNT(self, qml_app, qt_app):
        """A `newAlbumDialog` már nem létezik — nem „csak nem nyílik meg"."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, 0)

        QMetaObject.invokeMethod(
            _elem(window, "menuFileNewAlbum"),
            "triggered",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert window.findChild(QObject, "newAlbumDialog") is None

    def test_a_kepek_bekerulnek_az_uj_albumba(self, qml_app, qt_app, tmp_path):
        """A kijelölés a tagság — enélkül üres album jönne létre, amit a
        tárolásunk nem is tud eltárolni."""
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, 0)

        _elem(window, "photoContextMenu").newAlbumRequested.emit()
        qt_app.processEvents()

        token = controller.albums[0]["token"]
        ini = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert f"albums={token}" in ini, ini


class TestUresKijeloles:
    def test_nem_jon_letre_album(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        window.setProperty("selectedIndex", -1)
        window.setProperty("selectedIndexes", [])
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            _elem(window, "menuFileNewAlbum"),
            "triggered",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert controller.albums == []
