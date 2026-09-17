"""Az „Új album" CSENDBEN hoz létre „Névtelen" albumot — mind a négy belépő (#2911).

## A mérés

Az eredeti `thumbui/newalbum` kezelője (`0x005eb810`, 245 bájt) **nem nyit
névbekérőt**: felépíti az album-leírót, a nevét az `IDS_DEFAULT_ALBUM_NAME`
erőforrásból tölti (`0x0055cfb2 push 0x8a`), létrehozza az albumot, és kész.
Nincs számozás és nincs dátum — minden alkalommal ugyanaz a név.

## Amit ez az őr állít

- mind a **négy belépő** (eszköztár, `Fájl ▸ Új album`, `Ctrl+N`,
  fogd-és-vidd a bal hasábra) ugyanazt az utat járja: album jön létre,
  párbeszéd nélkül;
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


class TestANegyBelepo:
    def test_az_eszkoztar_gombja(self, qml_app, qt_app):
        """A gomb egy `TapHandler`-es `Item` (nincs `clicked` jelzése), a
        hatását a tálca `newAlbumRequested` jelzése viszi tovább — a próba
        ezt süti el, ahogy a koppintás tenné."""
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, 0)
        assert _elem(window, "toolbarNewAlbumButton") is not None

        _elem(window, "mainToolbar").newAlbumRequested.emit()
        qt_app.processEvents()

        assert [a["name"] for a in controller.albums] == ["Untitled"]

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

    def test_a_bal_hasabra_ejtes(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, 0)

        QMetaObject.invokeMethod(
            _elem(window, "folderPane"),
            "newAlbumDropped",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert [a["name"] for a in controller.albums] == ["Untitled"]


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
