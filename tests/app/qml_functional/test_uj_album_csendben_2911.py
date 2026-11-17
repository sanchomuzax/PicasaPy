"""A kijelöléses „Új album" utak az Album Properties ablakot nyitják (#2911).

## A mérés

Az eredeti `thumbui/newalbum` menüútja az Album Properties ablakot nyitja.
Az alapnév az `IDS_DEFAULT_ALBUM_NAME` erőforrásból jön; az album és a
kijelölt képek csak a jóváhagyás után kerülnek a gyűjteménybe.

## Amit ez az őr állít

- a Fájl menü és a kép-helyi menü az eszköztárral azonos Album Properties
  párbeszédet használja, és csak jóváhagyáskor készít albumot;
- a név a felület saját, FORDÍTHATÓ felirata (a próba-motorban a forrásalak
  `Untitled`; hogy magyarul „Névtelen", azt a
  `tests/app/test_ujalbum_nev_forditas_2911.py` méri a `.qm`-ből);
- ⛔ a kijelöléses utak (Add to ▸ New Album..., helyi menü) üres kijelölésnél
  nem csinálnak semmit, mert nálunk az album a `.picasa.ini`-ben él
  (`[.album:<token>]`), tehát TAG nélkül nincs hova kiírni. A Fájl ▸ New
  Album... és a Ctrl+N a #7164/#7180 óta kivétel: kijelöléstől függetlenül
  megnyitja az ablakot, és üres albumot készít
  (`test_uj_album_kijeloles_nelkul_7180.py`).
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _kattints
from tests.support.varakozas import var_feltetelre


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
    def test_a_menutetel_album_properties_abla_kot_nyit(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, 0)

        QMetaObject.invokeMethod(
            _elem(window, "menuFileNewAlbum"),
            "triggered",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        dialog = _elem(window, "toolbarNewAlbumPropertiesDialog")
        assert dialog.property("opened") is True
        assert dialog.property("title") == "Album Properties"
        assert controller.albums == []

    def test_a_racs_helyi_menuje_album_properties_abla_kot_nyit(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, 0)

        _elem(window, "photoContextMenu").newAlbumRequested.emit()
        qt_app.processEvents()

        dialog = _elem(window, "toolbarNewAlbumPropertiesDialog")
        assert dialog.property("opened") is True
        assert dialog.property("title") == "Album Properties"
        assert controller.albums == []

    # #5105: a bal hasábra ejtést valódi egérhúzás teszteli: test_huzas_hianyzoi_5008.py (új album terület).


class TestNincsParbeszed:
    def test_a_regi_nevbekero_helyett_album_properties_nyilik(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, 0)

        QMetaObject.invokeMethod(
            _elem(window, "menuFileNewAlbum"),
            "triggered",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert window.findChild(QObject, "newAlbumDialog") is None
        assert _elem(window, "toolbarNewAlbumPropertiesDialog").property("opened")

    def test_a_kepek_bekerulnek_az_uj_albumba(self, qml_app, qt_app, tmp_path):
        """A kijelölés a tagság — enélkül üres album jönne létre, amit a
        tárolásunk nem is tud eltárolni."""
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, 0)

        _elem(window, "photoContextMenu").newAlbumRequested.emit()
        qt_app.processEvents()

        dialog = _elem(window, "toolbarNewAlbumPropertiesDialog")
        assert dialog.property("opened") is True
        assert controller.albums == []
        _kattints(qt_app, _elem(dialog, "folderPropertiesOkButton"))
        assert var_feltetelre(
            qt_app, lambda: len(controller.albums) == 1, 5.0
        ), "az OK nem hozta létre az albumot"
        assert controller.albums[0]["name"] == "Untitled"

        token = controller.albums[0]["token"]
        ini = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert f"albums={token}" in ini, ini


class TestUresKijeloles:
    def test_a_racs_helyi_menuje_nem_hoz_letre_albumot(self, qml_app, qt_app):
        """A kijelöléses út (a kép helyi menüje) üres kijelölésnél hatástalan."""
        window, controller, _engine = qml_app
        window.setProperty("selectedIndex", -1)
        window.setProperty("selectedIndexes", [])
        qt_app.processEvents()

        _elem(window, "photoContextMenu").newAlbumRequested.emit()
        qt_app.processEvents()

        dialog = window.findChild(QObject, "toolbarNewAlbumPropertiesDialog")
        assert dialog is None or dialog.property("opened") is not True
        assert controller.albums == []

    def test_a_fajl_menu_nem_hoz_letre_albumot_az_ok_elott(self, qml_app, qt_app):
        """#7180: a Fájl ▸ New Album... kijelölés nélkül megnyitja az ablakot,
        de album csak az OK után jön létre."""
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

        assert _elem(window, "toolbarNewAlbumPropertiesDialog").property("opened")
        assert controller.albums == []
