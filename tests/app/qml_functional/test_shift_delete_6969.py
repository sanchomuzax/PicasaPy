"""#6969 - a `Shift+Delete` a VÉGLEGES törlés ágát választja; a Lomtár `0x0f`
eredményénél külön kérdés nyílik.

## Az eredeti - bizonyíték

* `0x005cb990` -> `0x005c9b00`: a `Delete` a Lomtárba helyez, a
  `Shift+Delete` a végleges törlés ágát választja, saját egyes és többes
  megerősítő szöveggel (`NoUndoSingle` / `NoUndoMultiple`, `0x005fdc30`).
* Ha a Lomtárba helyezés a Shelltől PONTOSAN `0x0f`-et kap, külön
  `Delete` / `Cancel` kérdés nyílik (`0x005fdb80`), és jóváhagyásra
  végleges törlést próbál (`0x009929b0`). Más hibakód nem törölhet
  véglegesen.
* Album- és Emberek-album nézetben ugyanez a parancs tagságot távolít el,
  nem fájlt töröl.

## A teszt mércéje

⚠️ VALÓDI billentyűleütés (`QTest.keyClick`), nem a metódus hívása; a
megerősítő gombjaira VALÓDI kattintás megy, ahol a gomb új (a `0x0f`
kérdés). A "fájl a lemezen marad / eltűnik" állítás a LEMEZEN mérve.

⚠️ Kétirányú őr: a sima `Delete` és a `Ctrl+Delete` a Lomtár-kérdést kapja,
a `Shift+Delete` a végleges törlését - egyik sem öröklődhet a másiktól.

⚠️ A várt feliratok KIÍRT LITERÁLOK (#1576); a fixture nem telepít
fordítót, ezért az angol forrásszöveg látszik.

⚠️ A Shell-hívás a `picasapy.fileops.trash._shfileoperation` modulszintű
fogantyún át, a platform a `_platform`-on át van cserélve (#1217/#1375).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.fileops import trash
from picasapy.index import open_index, sync_tree
from support.qml_halasztott import epitsd_fel_ha_fileops

_TOKEN = "604c294a68b0de9cc9222c4714f289d5"
_ROY_ID = "b8e4117cf1d6615b"
_ROY = "Roy Avery"
_RECT = "3f840000c3509f84"

_EGY_SZOVEG = (
    "Are you sure you want to permanently delete the selected file? "
    "(This cannot be undone.)"
)
_TOBB_SZOVEG = (
    "Are you sure you want to delete 2 selected files? "
    "(This cannot be undone.)"
)
_LOMTAR_EGY = (
    "Are you sure you want to send the selected file to the Recycle Bin? "
    "(It will also be removed from any albums in which it appears)"
)
_AZONNALI_SZOVEG = (
    "This file cannot be moved to the Trash and will be deleted "
    "immediately. Are you sure you want to continue?"
)


def _gyerek(window, nev):
    epitsd_fel_ha_fileops(window, nev)  # #1612: halasztott párbeszédek
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"a(z) {nev} nem található"
    return elem


def _fokusz(elem, qt_app):
    elem.setProperty("focus", True)
    QMetaObject.invokeMethod(
        elem, "forceActiveFocus", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _varj(controller, qt_app, korok=100):
    for _ in range(korok):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _katt(window, elem) -> None:
    kp = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window, Qt.LeftButton, Qt.NoModifier, QPoint(int(kp.x()), int(kp.y()))
    )


def _billentyu(window, qt_app, key, mods=Qt.KeyboardModifier.NoModifier):
    """Valódi (spontán) billentyűleütés az ablakra."""
    QTest.keyClick(window, key, mods)
    qt_app.processEvents()


def _shift_delete(window, qt_app):
    _billentyu(
        window, qt_app, Qt.Key.Key_Delete, Qt.KeyboardModifier.ShiftModifier
    )


def _kijelol(window, qt_app, sorok=(0,)):
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0])
    qt_app.processEvents()
    _fokusz(_gyerek(window, "photoGrid"), qt_app)


def _lista(ertek):
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return list(ertek)


def _album_nezet(lib, tmp_path, controller, qt_app):
    (lib / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\nname=Nyaralás\ntoken={_TOKEN}\n"
        f"[a.jpg]\nalbums={_TOKEN}\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    controller.showAlbum(_TOKEN)
    qt_app.processEvents()


def _szemely_nezet(lib, tmp_path, controller, qt_app):
    (lib / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ROY_ID}={_ROY};;\n"
        f"[a.jpg]\nfaces=rect64({_RECT}),{_ROY_ID};\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    controller.showPerson(_ROY)
    qt_app.processEvents()


@pytest.fixture
def lomtar_figyelo(monkeypatch):
    """A Lomtár-ág hívásainak rögzítője: a végleges törlés NEM mehet rajta át.

    A valódi függvényt NEM hívja (a teszt-környezet lomtárát nem érintjük),
    és `OSError`-t dob - ha a `Shift+Delete` mégis a Lomtárat használná,
    a fájl a helyén marad, és a hívólista is elárulja."""
    hivasok: list[str] = []

    def hamis(path, *args, **kwargs):
        hivasok.append(str(path))
        raise OSError("a Lomtár-ág nem hívható a végleges törlésnél")

    monkeypatch.setattr(
        "picasapy.app.fileops_controller.delete_photo_to_trash", hamis
    )
    return hivasok


class TestRacsShiftDelete:
    def test_egy_kepnel_a_vegleges_torles_egyes_szoveget_kerdezi(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app)
        confirm = _gyerek(window, "deleteConfirmDialog")
        assert confirm.property("visible") is False

        _shift_delete(window, qt_app)

        assert confirm.property("visible") is True
        assert confirm.property("trashAvailable") is False
        assert confirm.property("decisionKey") == "deletePermanently"
        assert confirm.property("message") == _EGY_SZOVEG
        assert confirm.property("yesText") == "Delete File"
        assert [Path(p) for p in _lista(confirm.property("paths"))] == [
            Path(controller.watchedFolders[0]) / "a.jpg"
        ]

    def test_tobb_kepnel_a_tobbes_szoveget_kerdezi(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, sorok=(0, 1))
        confirm = _gyerek(window, "deleteConfirmDialog")

        _shift_delete(window, qt_app)

        assert confirm.property("visible") is True
        assert confirm.property("decisionKey") == "deletePermanently"
        assert confirm.property("message") == _TOBB_SZOVEG
        assert confirm.property("yesText") == "Delete Files"
        assert len(_lista(confirm.property("paths"))) == 2

    def test_jovahagyasra_veglegesen_torol_a_lomtar_erintese_nelkul(
        self, qml_app, qt_app, tmp_path, lomtar_figyelo
    ):
        window, controller, _engine = qml_app
        kep = tmp_path / "kepek" / "a.jpg"
        assert kep.exists()
        _kijelol(window, qt_app)

        _shift_delete(window, qt_app)
        _katt(window, _gyerek(window, "confirmYesButton"))
        _varj(controller, qt_app)

        assert not kep.exists(), "a Shift+Delete jóváhagyva nem törölt"
        assert lomtar_figyelo == [], (
            "a Shift+Delete a Lomtár-ágon ment át, nem végleges törlés"
        )

    def test_a_cancel_meghagyja_a_fajlt(
        self, qml_app, qt_app, tmp_path, lomtar_figyelo
    ):
        window, controller, _engine = qml_app
        kep = tmp_path / "kepek" / "a.jpg"
        _kijelol(window, qt_app)

        _shift_delete(window, qt_app)
        _katt(window, _gyerek(window, "confirmCancelButton"))
        _varj(controller, qt_app)

        assert kep.exists()
        assert _gyerek(window, "deleteConfirmDialog").property(
            "visible"
        ) is False

    def test_kijeloles_nelkul_nem_nyit_kerdest(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        window.setProperty("selectedIndexes", [])
        window.setProperty("selectedIndex", -1)
        qt_app.processEvents()
        _fokusz(_gyerek(window, "photoGrid"), qt_app)

        _shift_delete(window, qt_app)

        assert _gyerek(window, "deleteConfirmDialog").property(
            "visible"
        ) is False

    def test_a_sima_delete_a_lomtar_kerdest_kapja_a_shift_utan_is(
        self, qml_app, qt_app
    ):
        """Kétirányú őr: a `Shift+Delete` állapota nem ragadhat a sima
        `Delete`-re (a `trashAvailable` és a kulcs újra beáll)."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app)
        confirm = _gyerek(window, "deleteConfirmDialog")
        _shift_delete(window, qt_app)
        assert confirm.property("trashAvailable") is False
        _katt(window, _gyerek(window, "confirmCancelButton"))
        qt_app.processEvents()
        _fokusz(_gyerek(window, "photoGrid"), qt_app)

        _billentyu(window, qt_app, Qt.Key.Key_Delete)

        assert confirm.property("visible") is True
        assert confirm.property("trashAvailable") is True
        assert confirm.property("decisionKey") == "delete"
        assert confirm.property("message") == _LOMTAR_EGY

    def test_a_ctrl_delete_is_a_lomtar_kerdest_kapja(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app)

        _billentyu(
            window, qt_app, Qt.Key.Key_Delete,
            Qt.KeyboardModifier.ControlModifier,
        )

        confirm = _gyerek(window, "deleteConfirmDialog")
        assert confirm.property("visible") is True
        assert confirm.property("trashAvailable") is True


class TestAlbumbanEsEmberekAlbumbanNemTorolFajlt:
    def test_albumban_a_shift_delete_nem_torol_fajlt(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _album_nezet(lib, tmp_path, controller, qt_app)
        assert controller.currentAlbumToken == _TOKEN
        _kijelol(window, qt_app)

        _shift_delete(window, qt_app)

        assert _gyerek(window, "deleteConfirmDialog").property(
            "visible"
        ) is False, "album-nézetben a Shift+Delete lemezről törlést kérdezett"
        assert _gyerek(window, "removeFromAlbumDialog").property(
            "visible"
        ) is True, "album-nézetben a Shift+Delete a tagságot veszi le"
        assert (lib / "a.jpg").exists()

    def test_albumban_megerositve_sem_torli_a_fajlt(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _album_nezet(lib, tmp_path, controller, qt_app)
        _kijelol(window, qt_app)

        _shift_delete(window, qt_app)
        _katt(window, _gyerek(window, "removeFromAlbumYesButton"))
        _varj(controller, qt_app)

        assert (lib / "a.jpg").exists(), (
            "ADATVESZTÉS: album-nézetben a Shift+Delete letörölte a fájlt"
        )
        ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert f"albums={_TOKEN}" not in ini

    def test_emberek_albumban_a_shift_delete_nem_torol_fajlt(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _szemely_nezet(lib, tmp_path, controller, qt_app)
        assert controller.currentPersonName == _ROY
        _kijelol(window, qt_app)

        _shift_delete(window, qt_app)

        assert _gyerek(window, "deleteConfirmDialog").property(
            "visible"
        ) is False
        assert _gyerek(window, "removePeopleFacesDialog").property(
            "visible"
        ) is True
        assert (lib / "a.jpg").exists()


class TestNezoShiftDelete:
    def _nezo(self, window, qt_app):
        window.setProperty("viewerOpen", True)
        viewer = _gyerek(window, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        _fokusz(viewer, qt_app)
        return viewer

    def test_a_nezoben_a_shift_delete_vegleges_torlest_kerdez(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        self._nezo(window, qt_app)
        confirm = _gyerek(window, "deleteConfirmDialog")
        assert confirm.property("visible") is False

        _shift_delete(window, qt_app)

        assert confirm.property("visible") is True
        assert confirm.property("trashAvailable") is False
        assert confirm.property("message") == _EGY_SZOVEG
        assert [Path(p) for p in _lista(confirm.property("paths"))] == [
            Path(controller.watchedFolders[0]) / "a.jpg"
        ]

    def test_a_nezo_sajat_billentyukezeloje_is_ugyanezt_teszi(
        self, qml_app, qt_app
    ):
        """Az ablak-szintű kötés nélkül is él a `PhotoViewer` saját
        kezelője (a `Ctrl+Delete` két belépőjének mintája, #4621)."""
        window, _controller, _engine = qml_app
        self._nezo(window, qt_app)
        sc = _gyerek(window, "shortcutPermanentDeleteViewer")
        sc.setProperty("enabled", False)
        qt_app.processEvents()
        confirm = _gyerek(window, "deleteConfirmDialog")

        _shift_delete(window, qt_app)

        assert confirm.property("visible") is True
        assert confirm.property("trashAvailable") is False
        assert confirm.property("message") == _EGY_SZOVEG

    def test_a_nezoben_a_jovahagyott_shift_delete_torol(
        self, qml_app, qt_app, tmp_path, lomtar_figyelo
    ):
        window, controller, _engine = qml_app
        kep = tmp_path / "kepek" / "a.jpg"
        self._nezo(window, qt_app)

        _shift_delete(window, qt_app)
        _katt(window, _gyerek(window, "confirmYesButton"))
        _varj(controller, qt_app)

        assert not kep.exists()
        assert lomtar_figyelo == []

    def test_a_nezoben_a_sima_delete_tovabbra_sem_torol(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        self._nezo(window, qt_app)
        confirm = _gyerek(window, "deleteConfirmDialog")

        _billentyu(window, qt_app, Qt.Key.Key_Delete)

        assert confirm.property("visible") is False

    def test_albumbol_megnyitott_kepen_a_shift_delete_nem_torol_fajlt(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _album_nezet(lib, tmp_path, controller, qt_app)
        self._nezo(window, qt_app)

        _shift_delete(window, qt_app)

        assert _gyerek(window, "deleteConfirmDialog").property(
            "visible"
        ) is False
        assert (lib / "a.jpg").exists()


@pytest.fixture
def shell_0f(monkeypatch):
    """Windowsos platform; a Shell-hívás kódja a teszt kezében."""
    monkeypatch.setattr(trash, "_platform", lambda: "win32")
    allapot = {"kod": 0x0F, "hivasok": 0}

    def hamis(muvelet) -> int:
        allapot["hivasok"] += 1
        return allapot["kod"]

    monkeypatch.setattr(trash, "_shfileoperation", hamis)
    return allapot


class TestALomtar0fKulonKerdese:
    def _torol_es_megerosit(self, window, controller, qt_app, sorok=(0,)):
        _kijelol(window, qt_app, sorok=sorok)
        _billentyu(window, qt_app, Qt.Key.Key_Delete)
        confirm = _gyerek(window, "deleteConfirmDialog")
        assert confirm.property("visible") is True
        assert confirm.property("trashAvailable") is True
        _katt(window, _gyerek(window, "confirmYesButton"))
        _varj(controller, qt_app)

    def test_0f_eredmenynel_kulon_delete_cancel_kerdes_nyilik(
        self, qml_app, qt_app, tmp_path, shell_0f
    ):
        window, controller, _engine = qml_app
        kep = tmp_path / "kepek" / "a.jpg"

        self._torol_es_megerosit(window, controller, qt_app)

        kerdes = _gyerek(window, "immediateDeleteDialog")
        assert kerdes.property("visible") is True
        assert kerdes.property("message") == _AZONNALI_SZOVEG
        assert _gyerek(window, "immediateDeleteYesButton").property(
            "text"
        ) == "Delete"
        assert _gyerek(window, "immediateDeleteCancelButton").property(
            "text"
        ) == "Cancel"
        assert kep.exists(), "jóváhagyás előtt nincs végleges törlés"
        assert _gyerek(window, "fileOpsErrorDialog").property(
            "visible"
        ) is False, "a 0x0f nem hibaablak"

    def test_a_delete_gomb_veglegesen_torol(
        self, qml_app, qt_app, tmp_path, shell_0f
    ):
        window, controller, _engine = qml_app
        kep = tmp_path / "kepek" / "a.jpg"
        self._torol_es_megerosit(window, controller, qt_app)

        _katt(window, _gyerek(window, "immediateDeleteYesButton"))
        _varj(controller, qt_app)

        assert not kep.exists()
        assert _gyerek(window, "immediateDeleteDialog").property(
            "visible"
        ) is False

    def test_a_cancel_gomb_meghagyja_a_fajlt(
        self, qml_app, qt_app, tmp_path, shell_0f
    ):
        window, controller, _engine = qml_app
        kep = tmp_path / "kepek" / "a.jpg"
        self._torol_es_megerosit(window, controller, qt_app)

        _katt(window, _gyerek(window, "immediateDeleteCancelButton"))
        _varj(controller, qt_app)

        assert kep.exists()
        assert _gyerek(window, "immediateDeleteDialog").property(
            "visible"
        ) is False

    def test_az_escape_is_meghagyja_a_fajlt(
        self, qml_app, qt_app, tmp_path, shell_0f
    ):
        window, controller, _engine = qml_app
        kep = tmp_path / "kepek" / "a.jpg"
        self._torol_es_megerosit(window, controller, qt_app)

        _billentyu(window, qt_app, Qt.Key.Key_Escape)

        assert kep.exists()
        assert _gyerek(window, "immediateDeleteDialog").property(
            "visible"
        ) is False

    def test_az_alapertelmezett_fokusz_a_cancelen_van(
        self, qml_app, qt_app, shell_0f
    ):
        """Az Enter ne töröljön véglegesen: a biztonságos gomb az alap."""
        window, controller, _engine = qml_app
        self._torol_es_megerosit(window, controller, qt_app)

        gomb = _gyerek(window, "immediateDeleteCancelButton")

        assert gomb.property("activeFocus") is True

    @pytest.mark.parametrize("kod", [0x02, 0x05, 0x0E, 0x10, 0x7C, 0x402])
    def test_mas_hibakod_nem_kerdez_es_nem_torol(
        self, qml_app, qt_app, tmp_path, shell_0f, kod
    ):
        window, controller, _engine = qml_app
        shell_0f["kod"] = kod
        kep = tmp_path / "kepek" / "a.jpg"

        self._torol_es_megerosit(window, controller, qt_app)

        assert _gyerek(window, "immediateDeleteDialog").property(
            "visible"
        ) is False, f"a {kod:#x} hibakód nem kérdezhet végleges törlést"
        assert _gyerek(window, "fileOpsErrorDialog").property(
            "visible"
        ) is True
        assert kep.exists()

    def test_tobb_kepnel_kepenkent_kerdez_es_a_cancel_csak_az_egyet_hagyja(
        self, qml_app, qt_app, tmp_path, shell_0f
    ):
        window, controller, _engine = qml_app
        a = tmp_path / "kepek" / "a.jpg"
        b = tmp_path / "kepek" / "b.jpg"
        self._torol_es_megerosit(window, controller, qt_app, sorok=(0, 1))
        kerdes = _gyerek(window, "immediateDeleteDialog")
        assert kerdes.property("visible") is True
        assert a.exists() and b.exists()

        _katt(window, _gyerek(window, "immediateDeleteYesButton"))
        _varj(controller, qt_app)

        assert not a.exists(), "az első kép jóváhagyva törlődik"
        assert kerdes.property("visible") is True, (
            "a második képről külön kérdés jön"
        )
        assert b.exists()

        _katt(window, _gyerek(window, "immediateDeleteCancelButton"))
        _varj(controller, qt_app)

        assert b.exists(), "a Cancel a második képet meghagyja"
        assert kerdes.property("visible") is False
