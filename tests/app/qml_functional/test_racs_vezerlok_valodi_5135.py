"""A „Rács" táblázat vezérlői VALÓDI kattintással (#5135, 1. rész).

A fanézet (`FolderHierarchyView`) a `folderHierarchyController.setTreeView`
kapcsolóval lép be a fanézetbe - ez állapot-előkészítés, a tesztelt műveletet
(a nyíl kattintását és a jobbklikk-menü tételeit) mind valódi egérkattintás
viszi. A fanézet alapból nem rajzolódik ki, ezért a teszt a `hierRow:` sorokat
a VIZUÁLIS fában, láthatóságuk szerint keresi.

Lefedve:
- `hierArrowMouse:` - a nyíl kattintása kinyitja az ágat, a második
  becsukja, és nem jelöli ki a mappát;
- `hierRowMouse:` - a sor szövegére kattintás kijelöli a mappát (#5137);
- `hierMenuExpandAll`, `hierMenuCollapseAll` - a közbenső csomópont menüje;
- `hierMenuLocateOnDisk` - a `fileOpsController.revealFolder` helyettesítője
  (a valódi fájlkezelő-indítás ki van váltva);
- `hierMenuRemoveFromPicasa` - a megerősítő párbeszéd nyílik meg;
- `hierMenuMoveFolder` - a mappaválasztó párbeszéd nyílik meg.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from picasapy.index import open_index, sync_tree
from support.halasztott_parbeszed import nyisd_meg
from test_people_manager_kattintas_4334 import (
    _FACE_RECT,
    _PERSON_ID,
    _click,
    _dialog_item,
    _open_manager,
    _replace_text,
    _select_contact,
)
from support.jpeg_factory import make_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre

#: a fa közbenső csomópontja: nincs saját fotója, csak gyerek-mappája
_KOZEP = "kozep"
_MELY = "kozep/mely"


def _keszits_fat(lib: Path) -> None:
    mely = lib / _KOZEP / "mely"
    mely.mkdir(parents=True)
    make_jpeg(mely / "kep.jpg", size=(64, 48))


@pytest.fixture
def fa_app(qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_fat,
        keep_modul=request.module,
    )


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _gyerek(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _vizualis_bejaras(item):
    """A VIZUÁLIS fa bejárása: a delegátumoknak nincs QObject-szülőjük."""
    for gyerek in item.childItems():
        yield gyerek
        yield from _vizualis_bejaras(gyerek)


def _utalak(ut) -> str:
    """Az útvonal a fa alakjában: `/`-elválasztóval.

    ⚠️ A fanézet két alakban adja a csomópont útvonalát: a közbenső
    (nem indexelt) mappák `/`-rel épülnek (`folder_hierarchy._join`), a
    valódi, indexelt mappák pedig a tárolt útjukon élnek, ami Windowson
    `\\`-es. A `str(Path)` Windowson mindig `\\`-es, ezért az összevetés
    előtt az elválasztót egységesítjük. Linuxon ez azonosság.
    """
    return str(ut).replace("\\", "/")


def _vizualis(window, nev: str):
    for item in _vizualis_bejaras(window.contentItem()):
        if _utalak(item.objectName()) == _utalak(nev):
            return item
    raise AssertionError(f"{nev} vizuális elem nem található")


def _latszik(window, nev: str) -> bool:
    """Ki van-e RAJZOLVA a vizuális fában az elem (látszik és van magassága)."""
    return any(
        _utalak(item.objectName()) == _utalak(nev)
        and item.isVisible() and item.height() > 0
        for item in _vizualis_bejaras(window.contentItem())
    )


def _vizualis_mindenablakban(nev: str):
    """A név szerinti vizuális elem és az ablak, ahol RAJZOLÓDIK.

    A helyi menük és a párbeszédek külön QQuickWindow-ban élnek, ezért nem
    elég a főablak fáját bejárni: az összes nyitott ablakot végigkeressük.
    Csak a látható példány számít (a menük zárva is léteznek).
    """
    for ablak in QGuiApplication.topLevelWindows():
        if not isinstance(ablak, QQuickWindow):
            continue
        for item in _vizualis_bejaras(ablak.contentItem()):
            if (
                item.objectName() == nev
                and item.isVisible()
                and item.width() > 0
                and item.height() > 0
            ):
                return ablak, item
    return None, None


def _latszik_mindenablakban(nev: str) -> bool:
    return _vizualis_mindenablakban(nev)[1] is not None


def _kattints_mindenablakban(qt_app, nev: str) -> None:
    ablak, elem = _vizualis_mindenablakban(nev)
    assert elem is not None, f"{nev} nem látszik egyik ablakban sem"
    _kattints_elemre(qt_app, ablak, elem)


def _kattints_elemre(qt_app, ablak, elem, gomb=Qt.MouseButton.LeftButton) -> None:
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nincs kattintható mérete"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        gomb,
        Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


def _kattints(window, qt_app, elem, gomb=Qt.MouseButton.LeftButton) -> None:
    assert elem.isVisible() and elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nem látszik / nulla méretű, nem kattintható"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        gomb,
        Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


def _zar(qt_app, objektum) -> None:
    QMetaObject.invokeMethod(objektum, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _fa(engine):
    fa = engine.rootContext().contextProperty("folderHierarchyController")
    assert fa is not None, "a folderHierarchyController nincs regisztrálva"
    return fa


def _fanezet_objektum(window, ut: str):
    """A `selectedPath`-ot hordozó fanézet: a sor ősei közül az első ilyen."""
    elem = _vizualis(window, f"hierRowMouse:{ut}")
    while elem is not None and elem.property("selectedPath") is None:
        elem = elem.parentItem()
    assert elem is not None, "a fanézet objektum nem található a sor felett"
    return elem


def _lib(fa_app) -> Path:
    """A figyelt gyökér (a teszt-könyvtár) a controllerből."""
    _window, controller, _engine = fa_app
    return Path(str(controller.watchedFolders[0]))


def _kozep_ut(lib: Path) -> str:
    return str(lib / _KOZEP)


def _mely_ut(lib: Path) -> str:
    return str(lib / _MELY)


def _fanezet(window, qt_app, engine, lib: Path) -> None:
    """Állapot-előkészítés: fanézet bekapcsolása a controlleren át.

    A nézetmód-váltás nem a tesztelt vezérlő; a kattintás-teszt maga a
    nyilat és a menütételeket kattintja. A közbenső mappa őseit a
    `revealPath` nyitja ki: ez a fa SAJÁT útvonal-alakját használja
    (Windowson a `toggle(str(lib))` nem találta el a `/`-es kulcsot, és a
    figyelt gyökér ága zárva maradt). A közbenső mappa ágát CSUKVA hagyjuk:
    a nyíl-teszt ezt kattintja, a `revealPath` a célt magát nem nyitja.
    """
    window.show()
    window.requestActivate()
    fa = _fa(engine)
    fa.setTreeView(True)
    fa.revealPath(_kozep_ut(lib))
    qt_app.processEvents()
    assert _varj(qt_app, lambda: _latszik(window, f"hierRow:{_kozep_ut(lib)}")), (
        "a fanézet nem rajzolta ki a közbenső mappát"
    )


def _jobbklikk_fa_sor(window, qt_app, ut: str):
    """Valódi jobbklikk a fasor egérterületén; a menü megnyílását is megvárjuk."""
    _kattints(window, qt_app, _vizualis(window, f"hierRowMouse:{ut}"),
              Qt.MouseButton.RightButton)
    menu = _gyerek(window, "hierFolderContextMenu")
    assert _varj(qt_app, lambda: menu.property("visible") is True), (
        "a közbenső mappa jobbklikkje nem nyitotta meg a fa menüjét"
    )
    return menu


class TestNyil:
    def test_a_nyil_kattintas_kinyitja_az_agat(self, fa_app, qt_app):
        window, _controller, engine = fa_app
        lib = _lib(fa_app)
        _fanezet(window, qt_app, engine, lib)
        assert not _latszik(window, f"hierRow:{_mely_ut(lib)}"), (
            "a próba feltétele: az ág kezdetben csukva van"
        )

        _kattints(window, qt_app, _vizualis(window, f"hierArrowMouse:{_kozep_ut(lib)}"))

        assert _varj(qt_app, lambda: _latszik(window, f"hierRow:{_mely_ut(lib)}")), (
            "a nyíl kattintás nem nyitotta ki a közbenső mappát"
        )

    def test_a_masodik_nyilkattintas_becsukja_az_agat(self, fa_app, qt_app):
        window, _controller, engine = fa_app
        lib = _lib(fa_app)
        _fanezet(window, qt_app, engine, lib)
        _kattints(window, qt_app, _vizualis(window, f"hierArrowMouse:{_kozep_ut(lib)}"))
        assert _varj(qt_app, lambda: _latszik(window, f"hierRow:{_mely_ut(lib)}"))

        # a kinyitás után a sor újrapéldányosodhat: a nyilat újra le kell kérni
        _kattints(window, qt_app, _vizualis(window, f"hierArrowMouse:{_kozep_ut(lib)}"))

        assert _varj(qt_app, lambda: not _latszik(window, f"hierRow:{_mely_ut(lib)}")), (
            "a második nyíl kattintás nem csukta be az ágat"
        )

    def test_a_nyil_kattintas_nem_valtoztatja_a_kijelolest(self, fa_app, qt_app):
        window, _controller, engine = fa_app
        lib = _lib(fa_app)
        _fanezet(window, qt_app, engine, lib)
        nezet = _fanezet_objektum(window, _kozep_ut(lib))
        kezdeti = nezet.property("selectedPath")
        assert _utalak(kezdeti) != _utalak(_kozep_ut(lib)), (
            "a próba feltétele: a közbenső mappa még nincs kijelölve"
        )

        _kattints(window, qt_app, _vizualis(window, f"hierArrowMouse:{_kozep_ut(lib)}"))
        assert _varj(qt_app, lambda: _latszik(window, f"hierRow:{_mely_ut(lib)}"))

        assert nezet.property("selectedPath") == kezdeti, (
            "a nyíl kattintás megváltoztatta a kijelölt mappát"
        )


class TestSorKijeloles:
    def test_a_sor_szovegere_kattintas_kijeloli_es_nem_nyitja_az_agat(self, fa_app, qt_app):
        window, _controller, engine = fa_app
        lib = _lib(fa_app)
        _fanezet(window, qt_app, engine, lib)
        nezet = _fanezet_objektum(window, _kozep_ut(lib))

        _kattints(window, qt_app, _vizualis(window, f"hierRowMouse:{_kozep_ut(lib)}"))

        assert _varj(
            qt_app,
            lambda: _utalak(nezet.property("selectedPath")) == _utalak(_kozep_ut(lib)),
        ), (
            "a sorra kattintás nem jelölte ki a mappát"
        )
        assert not _latszik(window, f"hierRow:{_mely_ut(lib)}"), (
            "a sorra kattintás kinyitotta az ágat"
        )


class TestHierMenu:
    def test_mind_kinyit_valodi_menupontra_kattintva(self, fa_app, qt_app):
        window, _controller, engine = fa_app
        lib = _lib(fa_app)
        _fanezet(window, qt_app, engine, lib)
        assert not _latszik(window, f"hierRow:{_mely_ut(lib)}")

        menu = _jobbklikk_fa_sor(window, qt_app, _kozep_ut(lib))
        _kattints(window, qt_app, _gyerek(menu, "hierMenuExpandAll"))

        assert _varj(qt_app, lambda: _latszik(window, f"hierRow:{_mely_ut(lib)}")), (
            "a Expand All kattintás nem nyitotta ki a fát"
        )

    def test_mind_becsuk_valodi_menupontra_kattintva(self, fa_app, qt_app):
        window, _controller, engine = fa_app
        lib = _lib(fa_app)
        _fanezet(window, qt_app, engine, lib)
        _fa(engine).expandAll()
        qt_app.processEvents()
        assert _varj(qt_app, lambda: _latszik(window, f"hierRow:{_mely_ut(lib)}"))

        menu = _jobbklikk_fa_sor(window, qt_app, _kozep_ut(lib))
        _kattints(window, qt_app, _gyerek(menu, "hierMenuCollapseAll"))

        assert _varj(qt_app, lambda: not _latszik(window, f"hierRow:{_mely_ut(lib)}")), (
            "a Collapse All kattintás nem csukta be a fát"
        )

    def test_lemezen_megmutatas_a_mappat_adja_at_a_helyettesitonek(
        self, fa_app, qt_app, monkeypatch
    ):
        """Helyettesítő: a valódi fájlkezelő-indítás ki van váltva."""
        import picasapy.app.fileops_controller as fileops_module

        window, _controller, engine = fa_app
        lib = _lib(fa_app)
        _fanezet(window, qt_app, engine, lib)
        megnyitva: list[Path] = []
        monkeypatch.setattr(
            fileops_module, "open_folder_in_file_manager",
            lambda path: megnyitva.append(Path(path)),
        )

        menu = _jobbklikk_fa_sor(window, qt_app, _kozep_ut(lib))
        _kattints(window, qt_app, _gyerek(menu, "hierMenuLocateOnDisk"))

        assert _varj(qt_app, lambda: megnyitva == [lib / _KOZEP]), (
            f"a Locate on Disk nem a mappát nyitotta meg: {megnyitva}"
        )

    def test_eltavolitas_megerositot_nyit_a_mappara(self, fa_app, qt_app):
        window, _controller, engine = fa_app
        lib = _lib(fa_app)
        _fanezet(window, qt_app, engine, lib)

        menu = _jobbklikk_fa_sor(window, qt_app, _kozep_ut(lib))
        _kattints(window, qt_app, _gyerek(menu, "hierMenuRemoveFromPicasa"))

        megerosites = _gyerek(window, "removeFolderConfirmDialog")
        assert _varj(qt_app, lambda: megerosites.property("visible") is True), (
            "a Remove from PicasaPy kattintás nem nyitotta meg a megerősítést"
        )
        assert _KOZEP in str(megerosites.property("message"))
        _zar(qt_app, megerosites)

    def test_athelyezes_a_mappavalasztot_nyitja_meg(self, fa_app, qt_app):
        window, _controller, engine = fa_app
        lib = _lib(fa_app)
        _fanezet(window, qt_app, engine, lib)
        pane = _gyerek(window, "folderPane")

        menu = _jobbklikk_fa_sor(window, qt_app, _kozep_ut(lib))
        _kattints(window, qt_app, _gyerek(menu, "hierMenuMoveFolder"))

        valaszto = _gyerek(window, "moveFolderDialog")
        assert _varj(qt_app, lambda: valaszto.property("visible") is True), (
            "a Move Folder kattintás nem nyitotta meg a mappaválasztót"
        )
        assert _utalak(pane.property("_movingFolder")) == _utalak(_kozep_ut(lib))
        _zar(qt_app, valaszto)


class TestArcfelismeresKapcsolo:
    def test_a_kapcsolo_kattintasa_keri_a_kikapcsolast_az_OK_utan(self, fa_app, qt_app):
        """A kikapcsolás csak az OK és a megerősítés után történik meg.

        A kattintás a kérést jegyzi fel: az OK ezért csak akkor hoz megerősítőt,
        ha a kapcsolót ténylegesen megnyomtuk.
        """
        window, controller, _engine = fa_app
        lib = _lib(fa_app)
        nyisd_meg(window, "folderManagerDialog")
        dialog = _gyerek(window, "folderManagerDialog")
        dialog.setProperty("selectedPath", str(lib))
        qt_app.processEvents()

        ablak, kapcsolo = _vizualis_mindenablakban("faceDetectionToggleArea")
        assert kapcsolo is not None, "az arcfelismerés-kapcsoló nem látszik"
        _kattints_elemre(qt_app, ablak, kapcsolo)
        _kattints_mindenablakban(qt_app, "folderManagerOkButton")

        megerosites = _gyerek(window, "faceDetectionConfirmDialog")
        assert _varj(qt_app, lambda: megerosites.property("visible") is True), (
            "a kapcsoló kattintása után az OK nem kért megerősítést"
        )
        assert controller.faceDetectionEnabledFor(str(lib)) is True, (
            "a kikapcsolás a megerősítés előtt megtörtént"
        )
        _zar(qt_app, megerosites)
        _zar(qt_app, dialog)


class TestSzemelyKezeloVisszavon:
    def test_visszavon_gomb_valodi_kattintassal_visszaallitja_a_nevet(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        library = Path(controller.photos.filePathAt(0)).parent
        (library / ".picasa.ini").write_text(
            "[Contacts2]\n"
            f"{_PERSON_ID}=Anna;anna@example.test;gaia-anna\n"
            "[a.jpg]\n"
            f"faces=rect64({_FACE_RECT}),{_PERSON_ID}\n",
            encoding="utf-8",
        )
        with open_index(controller._db_path) as conn:
            sync_tree(conn, library)
        controller._reload_after_sync()
        qt_app.processEvents()
        _open_manager(window, qt_app)
        # a kezelő-példányra tartott hivatkozás nélkül a QML-elemek a kiválasztás
        # közben megsemmisülnek (a 4334-es teszt ugyanígy tartja)
        kezelo_betoltes = _gyerek(window, "peopleManagerLoader")
        kezelo = kezelo_betoltes.property("item")
        assert kezelo is not None
        _select_contact(window, qt_app, "Anna")
        mezo = _dialog_item(window, "peopleManagerNameField")
        _replace_text(qt_app, mezo, "Anita")
        assert _varj(qt_app, lambda: mezo.property("text") == "Anita"), (
            "a név-szerkesztés nem írt be új nevet"
        )

        _click(qt_app, _dialog_item(window, "peopleManagerRevertButton"))

        assert _varj(qt_app, lambda: mezo.property("text") == "Anna"), (
            "a Revert kattintás nem állította vissza a nevet"
        )

