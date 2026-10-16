"""A „Rács" táblázat vezérlői VALÓDI kattintással (#5135, 2. rész).

Lefedve:
- `contextMenuNewAlbum` - a fotó helyi menüje: Add to Album ▸ New Album...;
- `datePickerPreviousMonth`, `datePickerNextMonth` - a dátum-naptár nyilai;
- `duplicateCancelButton` - a duplikált-nevek párbeszéd Mégse gombja;
- `dedupScanButton`, `dedupKeepArea:`, `dedupMoveButton:`, `dedupDeleteButton:`
  - a duplikátum-kezelő gombjai (a törlés a Kukába a helyettesítővel fut).

A kezelők törzsét a rontás-kontroll idejére megjegyzésbe tesszük; a
futtatások után a QML-t `git checkout` állítja vissza.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import QMetaObject, QObject, Qt, Q_ARG

from conftest import _build_qml_app
from support.jpeg_factory import make_jpeg
from tests.app.qml_functional._fomenu_4420_menu import _gyoker_menu, _menu_fejlec
from test_racs_vezerlok_valodi_5135 import (
    _gyerek,
    _kattints_elemre,
    _kattints_mindenablakban,
    _latszik_mindenablakban,
    _varj,
    _vizualis,
    _vizualis_bejaras,
    _zar,
)

_MAPPA = "fotok"
_CELMAPPA = "celmappa"


def _keszits_fotokat(lib: Path) -> None:
    """Két BÁJTRA AZONOS kép: a duplikátum-kereső ezeket csoportosítja."""
    mappa = lib / _MAPPA
    mappa.mkdir()
    make_jpeg(mappa / "dup_a.jpg", size=(320, 240))
    (mappa / "dup_b.jpg").write_bytes((mappa / "dup_a.jpg").read_bytes())
    (lib / _CELMAPPA).mkdir()


@pytest.fixture
def foto_app(qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_fotokat,
        keep_modul=request.module,
    )


@pytest.fixture
def dedup_app(qt_app, tmp_path, request):
    """A foto-app a duplikátum-vezérlővel.

    A qml_functional felépítő nem köti be a `dedupController`-t (a teljes
    alkalmazás az `application.py`-ban köti); itt ugyanúgy, a `wire_dedup`-pal
    kötjük be, mielőtt a párbeszéd először felépül.
    """
    from picasapy.app.application import wire_dedup
    from picasapy.app.dedup_controller import DedupController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    epites = _build_qml_app(
        qt_app, tmp_path, kepeket_keszit=_keszits_fotokat, keep_modul=request.module,
    )
    window, controller, engine = next(epites)
    dedup = DedupController(
        tmp_path / "index.db",
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
    )
    wire_dedup(dedup, controller)
    engine.rootContext().setContextProperty("dedupController", dedup)
    yield window, controller, engine
    yield from epites


def _cel_utja(controller) -> str:
    return str(Path(str(controller.watchedFolders[0])) / _MAPPA)


def _mappa_kivalasztva(window, qt_app, controller) -> str:
    """Megjeleníti az ablakot, a fotós mappát betölti, és megvárja a két képet."""
    window.show()
    window.requestActivate()
    cel = _cel_utja(controller)
    controller.selectFolder(cel)
    qt_app.processEvents()
    assert _varj(qt_app, lambda: len(controller.photos.photos) == 2), (
        "a teszt mappája nem töltődött be"
    )
    return cel


# ---------------------------------------------------------------------------
# 1. A fotó helyi menüje: Add to Album ▸ New Album...
# ---------------------------------------------------------------------------


def _almenu_sora(menu, almenu):
    """A szülőmenü azon sora, amely az almenüt nyitja (a címe egyezik)."""
    cim = almenu.property("title")
    pending = [menu.property("contentItem")]
    while pending:
        item = pending.pop()
        if (
            "MenuItem" in item.metaObject().className()
            and item.property("text") == cim
            and not item.objectName()
        ):
            return item
        pending.extend(item.childItems())
    raise AssertionError(f"{cim!r} almenüsora nem található")


class TestFotoMenuUjAlbum:
    def test_uj_album_valodi_kattintassal_letrejon(self, foto_app, qt_app):
        window, controller, _engine = foto_app
        _mappa_kivalasztva(window, qt_app, controller)
        albumok_elotte = len(controller.albums)

        kep = _vizualis(window, "thumbMouseArea")
        _kattints_elemre(qt_app, window, kep, Qt.MouseButton.RightButton)
        menu = _gyerek(window, "photoContextMenu")
        assert _varj(qt_app, lambda: menu.property("visible") is True), (
            "a fotó jobbklikkje nem nyitotta meg a helyi menüt"
        )

        almenu = _gyerek(window, "contextMenuAddToAlbum")
        sor = _almenu_sora(menu, almenu)
        _kattints_elemre(qt_app, sor.window(), sor)
        assert _varj(qt_app, lambda: _latszik_mindenablakban("contextMenuNewAlbum")), (
            "az Add to Album kattintás nem nyitotta meg az almenüt"
        )

        _kattints_mindenablakban(qt_app, "contextMenuNewAlbum")

        assert _varj(qt_app, lambda: len(controller.albums) == albumok_elotte + 1), (
            "a New Album kattintás nem hozott létre új albumot"
        )


# ---------------------------------------------------------------------------
# 2. A dátum-naptár nyilai (a mappa tulajdonságai párbeszédből)
# ---------------------------------------------------------------------------


def _mappa_tulajdonsagai(window, qt_app, cel: str):
    sor = _mappa_sor(window, cel)
    _kattints_elemre(qt_app, window, sor, Qt.MouseButton.RightButton)
    menu = _gyerek(window, "folderContextMenu")
    assert _varj(qt_app, lambda: menu.property("visible") is True)
    _kattints_mindenablakban(qt_app, "folderMenuEditDescription")
    dialog = _gyerek(window, "folderPropertiesDialog")
    assert _varj(qt_app, lambda: dialog.property("opened") is True), (
        "a Leírás szerkesztése kattintás nem nyitotta meg a mappa-párbeszédet"
    )
    return dialog


def _mappa_sor(window, cel: str):
    for item in _vizualis_bejaras(window.contentItem()):
        if item.objectName() == "folderRowMouse" and item.property("folderPath") == cel:
            return item
    raise AssertionError(f"a bal oldali mappasor nem található: {cel}")


class TestDatumNaptarNyilak:
    def _naptar_nyitva(self, window, qt_app, cel: str):
        dialog = _mappa_tulajdonsagai(window, qt_app, cel)
        _kattints_mindenablakban(qt_app, "folderPropertiesDateCalendarButton")
        naptar = _gyerek(window, "folderPropertiesCalendar")
        assert _varj(qt_app, lambda: naptar.property("opened") is True), (
            "a naptár-gomb nem nyitotta meg a naptárat"
        )
        return dialog, naptar

    def _cim(self, window) -> str:
        return str(_gyerek(window, "datePickerMonthTitle").property("text"))

    def test_kovetkezo_honap_valodi_kattintassal_leptet(self, foto_app, qt_app):
        window, controller, _engine = foto_app
        cel = _mappa_kivalasztva(window, qt_app, controller)
        dialog, _naptar = self._naptar_nyitva(window, qt_app, cel)
        elotte = self._cim(window)

        _kattints_mindenablakban(qt_app, "datePickerNextMonth")

        assert _varj(qt_app, lambda: self._cim(window) != elotte), (
            "a következő-hónap kattintás nem léptette a naptárat"
        )
        _zar(qt_app, dialog)

    def test_elozo_honap_valodi_kattintassal_visszalep(self, foto_app, qt_app):
        window, controller, _engine = foto_app
        cel = _mappa_kivalasztva(window, qt_app, controller)
        dialog, _naptar = self._naptar_nyitva(window, qt_app, cel)
        elotte = self._cim(window)

        _kattints_mindenablakban(qt_app, "datePickerPreviousMonth")

        assert _varj(qt_app, lambda: self._cim(window) != elotte), (
            "az előző-hónap kattintás nem léptette a naptárat"
        )
        _zar(qt_app, dialog)


# ---------------------------------------------------------------------------
# 3. A duplikált-nevek párbeszéd Mégse gombja
# ---------------------------------------------------------------------------


class TestDuplikaltNevekMegse:
    def test_megse_bezarja_es_nem_mozgat_semmit(self, foto_app, qt_app):
        window, controller, _engine = foto_app
        cel = _mappa_kivalasztva(window, qt_app, controller)
        forras = Path(cel) / "dup_a.jpg"
        cel_mappa = Path(str(controller.watchedFolders[0])) / _CELMAPPA

        # a FileOpsDialogs halasztva épül: az ensure() építi fel (ahogy a
        # felhasználói út is), utána kereshetők a párbeszédei
        burok = _gyerek(window, "fileOpsDialogs")
        assert QMetaObject.invokeMethod(burok, "ensure")
        parbeszed = _gyerek(window, "duplicateNamesDialog")
        # állapot-előkészítés: a párbeszéd nyitása (a tesztelt a Mégse)
        QMetaObject.invokeMethod(
            parbeszed, "openFor", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "move"),
            Q_ARG("QVariant", [str(forras)]),
            Q_ARG("QVariant", str(cel_mappa)),
        )
        qt_app.processEvents()
        assert _varj(qt_app, lambda: parbeszed.property("opened") is True)

        _kattints_mindenablakban(qt_app, "duplicateCancelButton")

        assert _varj(qt_app, lambda: parbeszed.property("opened") is False), (
            "a Mégse kattintás nem zárta be a duplikált-nevek párbeszédet"
        )
        assert forras.exists(), "a Mégse után a fájl mégis elmozdult"
        assert not any(cel_mappa.iterdir()), "a Mégse után a célmappába került fájl"


# ---------------------------------------------------------------------------
# 4. A duplikátum-kezelő gombjai
# ---------------------------------------------------------------------------


def _dedup_megnyit(window, qt_app):
    """A Tools ▸ Experimental ▸ Manage Duplicates... út valódi kattintásokkal."""
    menu_bar = window.property("menuBar")
    tools = _gyoker_menu(menu_bar, "&Tools")
    if tools.property("opened") is not True:
        _kattints_elemre(qt_app, window, _menu_fejlec(menu_bar, "&Tools"))
    assert _varj(qt_app, lambda: tools.property("opened") is True)
    experimental = next(
        elem
        for elem in tools.findChildren(QObject)
        if shiboken6.isValid(elem) and elem.property("title") == "Experimental"
    )
    _kattints_elemre(qt_app, window, _almenu_sora(tools, experimental))
    assert _varj(qt_app, lambda: experimental.property("opened") is True)
    _kattints_elemre(qt_app, window, _gyerek(window, "menuToolsDedupManager"))

    dialog = _gyerek(window, "dedupDialog")
    assert _varj(qt_app, lambda: dialog.property("visible") is True), (
        "a Manage Duplicates... nem nyitotta meg a duplikátum-kezelőt"
    )
    dialog.requestActivate()
    assert _varj(qt_app, lambda: dialog.property("scanning") is False)
    return dialog


def _keresd_meg(qt_app, dialog) -> None:
    """A Scan gomb VALÓDI kattintása, és megvárjuk az első csoportot."""
    _kattints_mindenablakban(qt_app, "dedupScanButton")
    assert _varj(qt_app, lambda: _latszik_mindenablakban("dedupGroup:0")), (
        "a Scan for Duplicates nem talált csoportot"
    )


def _megtartott(dialog) -> str:
    """A csoport MEGTARTANDÓ képe: a kattintással beállított, különben az első.

    Olvasás a QML-állapotból (`keepByGroup` kulcs-érték térkép, `groups` lista),
    ugyanúgy, ahogy a `keepPathFor` számolja - a függvényt nem hívjuk.
    """
    kulcsok = dialog.property("keepByGroup").toVariant() or {}
    for kulcs in (0, "0"):
        if kulcsok.get(kulcs) is not None:
            return str(kulcsok[kulcs])
    return str(dialog.property("groups")[0]["items"][0]["path"])


def _kepek(cel: str) -> tuple[str, str]:
    return str(Path(cel) / "dup_a.jpg"), str(Path(cel) / "dup_b.jpg")


class TestDuplikatumKezelo:
    def test_scan_gomb_valodi_kattintassal_ujra_keres(self, dedup_app, qt_app):
        window, controller, engine = dedup_app
        _mappa_kivalasztva(window, qt_app, controller)
        dialog = _dedup_megnyit(window, qt_app)
        dedup = engine.rootContext().contextProperty("dedupController")
        inditasok: list[int] = []
        dedup.scanStarted.connect(lambda: inditasok.append(1))

        _kattints_mindenablakban(qt_app, "dedupScanButton")

        assert _varj(qt_app, lambda: len(inditasok) == 1), (
            "a Scan for Duplicates kattintás nem indított keresést"
        )
        assert _varj(qt_app, lambda: dialog.property("scanning") is False)

    def test_a_kattintas_atallitja_a_megtartando_kepet(self, dedup_app, qt_app):
        window, controller, _engine = dedup_app
        cel = _mappa_kivalasztva(window, qt_app, controller)
        dialog = _dedup_megnyit(window, qt_app)
        alapertelmezett = _megtartott(dialog)

        _kattints_mindenablakban(qt_app, "dedupKeepArea:0:1")

        assert _varj(qt_app, lambda: _megtartott(dialog) != alapertelmezett), (
            "a megtartás-kattintás nem változtatta a megtartandó képet"
        )
        assert {alapertelmezett, _megtartott(dialog)} == set(_kepek(cel))

    def test_athelyez_gomb_a_mas_kepet_a_duplikatumok_mappaba_viszi(
        self, dedup_app, qt_app
    ):
        from picasapy.app.dedup_controller import DUPLICATES_SUBFOLDER_NAME

        window, controller, _engine = dedup_app
        cel = _mappa_kivalasztva(window, qt_app, controller)
        dialog = _dedup_megnyit(window, qt_app)
        megtartott = Path(_megtartott(dialog))
        masik = next(Path(k) for k in _kepek(cel) if Path(k) != megtartott)

        _kattints_mindenablakban(qt_app, "dedupMoveButton:0")

        cel_utja = Path(cel) / DUPLICATES_SUBFOLDER_NAME / masik.name
        assert _varj(qt_app, lambda: cel_utja.exists()), (
            "az Move others kattintás nem vitte a másik képet a Duplikátumok mappába"
        )
        assert not masik.exists(), "a másik kép az eredeti helyén maradt"
        assert megtartott.exists(), "a megtartandó kép elmozdult"

    def test_torol_gomb_a_mas_kepet_a_kukaba_adja_a_helyettesitonek(
        self, dedup_app, qt_app, monkeypatch
    ):
        """Helyettesítő: a Kuka-művelet nem ír a valódi lomtárba."""
        import picasapy.app.dedup_controller as dedup_module

        window, controller, _engine = dedup_app
        cel = _mappa_kivalasztva(window, qt_app, controller)
        dialog = _dedup_megnyit(window, qt_app)
        megtartott = Path(_megtartott(dialog))
        masik = next(Path(k) for k in _kepek(cel) if Path(k) != megtartott)
        kukaba: list[Path] = []
        monkeypatch.setattr(
            dedup_module, "delete_photo_to_trash", lambda path: kukaba.append(path)
        )

        _kattints_mindenablakban(qt_app, "dedupDeleteButton:0")

        assert _varj(qt_app, lambda: kukaba == [masik]), (
            f"a Delete others to Trash nem a másik képet kérte a Kukába: {kukaba}"
        )
        assert megtartott.exists()
