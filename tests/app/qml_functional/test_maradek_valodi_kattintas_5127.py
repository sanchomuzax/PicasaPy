"""Valódi kattintások és billentyűk a maradék elemekre (#5127, negyedik rész).

Gombok `QTest.mouseClick`-kel, a középpontjukra kattintva:
- `viewerEditMovieButton` a nézőben, mozgófilm-projektfájlos képen;
- `facesEditToggleButton` a nézőben (az arc-szerkesztő kapcsoló);
- `hiddenPasswordClear` a jelszó-párbeszédben, a Rejtett mappák
  helyi menüjén át érve el;
- `dedupCancelButton` a duplikátum-kezelőben, futó keresés közben.

Gyorsbillentyűk `QTest.keyClick`-kel, az ablakra küldve:
- `Ctrl+F7` hasonlóra keresés, `Ctrl+F8` a minta törlése;
- `Ctrl+Shift+B` fekete-fehér szűrő, `Ctrl+Shift+E` „Jó napom van” a
  kijelölésre.

A hatást a felhasználó felől nézzük: nyílik-e a film-párbeszéd, átáll-e az
arc-szerkesztés, törlődik-e a jelszó, zárul-e a keresés, áll-e a minta, és
íródik-e az `.picasa.ini` `filters=` lánca.

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated`
hívás és nincs `.emit()`. A párbeszédek takarításához a `close` hívás szabad.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from picasapy.movie.mxf import MxfAtmenet, MxfForras, MxfProjekt, write_mxf
from support.jpeg_factory import make_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.conftest import _build_qml_app as _build_teljes_app
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _objektum
from tests.app.qml_functional._fomenu_4420_menu import _gyoker_menu, _menu_fejlec

_MAPPA = "fotok"
_KEPEK = ("a_elso.jpg", "b_masodik.jpg")
_REJTETT_FEJLEC = "hiddenCollectionHeader"


def _keszits_konyvtarat(lib: Path) -> None:
    cel = lib / _MAPPA
    cel.mkdir()
    for nev in _KEPEK:
        make_jpeg(cel / nev, size=(320, 240))


@pytest.fixture
def valodi_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
    )


@pytest.fixture
def dedup_app(qt_app, tmp_path):
    """A teljes app: a duplikátum-kezelő vezérlője csak itt van a kontextusban."""
    yield from _build_teljes_app(qt_app, tmp_path)


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _elokeszit(window, qt_app, controller) -> None:
    """Megjeleníti az ablakot, betölti a mappát, és kijelöli az első képet."""
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    cel = str(Path(str(controller.watchedFolders[0])) / _MAPPA)
    controller.selectFolder(cel)
    assert _varj(
        qt_app, lambda: len(controller.photos.photos) == len(_KEPEK)
    ), "a teszt mappája nem töltődött be"
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()


def _gyerek(window, nev: str):
    elem = _objektum(window, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _latszik(window, nev: str) -> bool:
    elem = _objektum(window, nev)
    return elem is not None and elem.property("visible") is True


def _zar(qt_app, objektum) -> None:
    QMetaObject.invokeMethod(objektum, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _nezot_nyit(window, qt_app):
    window.setProperty("viewerOpen", True)
    nezo = _gyerek(window, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    nezo.setProperty("visible", True)
    qt_app.processEvents()
    return nezo


def _projektet_ir_a_kep_melle(nezo) -> Path:
    """Mozgófilm-projektfájl a megnyitott kép mellé (mint a #2114 őrében)."""
    kep = Path(str(nezo.property("currentFilePath")).replace("file://", ""))
    projekt = MxfProjekt(
        defaulttrans=MxfAtmenet(advanceinterval=3.0),
        atmenetek=(MxfAtmenet(forras=MxfForras(index=0, filename=str(kep))),),
    )
    return write_mxf(kep.with_suffix(".mxf"), projekt)


def _ini_szoveg(utvonal: Path) -> str:
    return utvonal.read_text(encoding="utf-8") if utvonal.exists() else ""


def _vizualis_elem(window, nev: str):
    """A lista sorainak nincs QObject-szülője, csak vizuális: a vizuális fán keresünk."""
    sor = [window.contentItem()]
    while sor:
        item = sor.pop()
        if item.objectName() == nev and item.isVisible():
            return item
        sor.extend(item.childItems())
    return None


def _kattints(qt_app, ablak, elem, gomb=Qt.MouseButton.LeftButton) -> None:
    """Valódi egérkattintás `elem` középpontjára, az `ablak`-ra küldve.

    ⚠️ Az ablakot a hívó adja át, és a teszt tartja életben. Az `elem.window()`
    minden híváskor új Python-burkolót hoz létre, és annak megsemmisítése
    a főablakot is a C++ oldalon törölte (a dedup-próbán ez volt a bukás oka)."""
    assert elem is not None, "a kattintandó felületi elem hiányzik"
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nincs kattintható mérete"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        gomb,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _megnyit(window, qt_app, cim: str):
    """A felső menü megnyitása a fejlécének valódi kattintásával."""
    menu_bar = window.property("menuBar")
    menu = _gyoker_menu(menu_bar, cim)
    if menu.property("opened") is not True:
        _kattints(qt_app, window, _menu_fejlec(menu_bar, cim))
    assert _varj(qt_app, lambda: menu.property("opened") is True), (
        f"a felső {cim} menü nem nyílt meg"
    )


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


def _menupont(qt_app, window, nev: str) -> None:
    elem = _gyerek(window, nev)
    assert _varj(qt_app, lambda: elem.property("visible") is True), (
        f"{nev} nem látszik a menüben"
    )
    _kattints(qt_app, window, elem)


class TestNezoFilmszerkesztoGomb:
    def test_valodi_kattintas_megnyitja_a_film_parbeszedet(
        self, valodi_app, qt_app
    ):
        window, controller, _engine = valodi_app
        _elokeszit(window, qt_app, controller)
        nezo = _nezot_nyit(window, qt_app)
        _projektet_ir_a_kep_melle(nezo)
        # a jelző a `currentFilePath`-ra köt: lapozással újraértékeltetjük
        nezo.setProperty("currentIndex", 1)
        nezo.setProperty("currentIndex", 0)
        qt_app.processEvents()

        gomb = _gyerek(window, "viewerEditMovieButton")
        assert _varj(qt_app, lambda: gomb.property("visible") is True), (
            "a Film szerkesztése gomb nem jelent meg a projektfájlos képen"
        )
        _kattints(qt_app, window, gomb)

        assert _varj(qt_app, lambda: _latszik(window, "movieDialog")), (
            "a Film szerkesztése kattintás nem nyitotta meg a film-párbeszédet"
        )
        assert window.property("viewerOpen") is False, (
            "a film megnyitásakor a néző nem záródott be"
        )
        _zar(qt_app, _gyerek(window, "movieDialog"))


class TestNezoArcSzerkesztoKapcsolo:
    def test_valodi_kattintasra_be_es_ki_kapcsol_az_arc_szerkesztes(
        self, valodi_app, qt_app
    ):
        window, controller, _engine = valodi_app
        _elokeszit(window, qt_app, controller)
        nezo = _nezot_nyit(window, qt_app)
        gomb = _gyerek(window, "facesEditToggleButton")
        assert _varj(qt_app, lambda: gomb.property("visible") is True), (
            "az arc-szerkesztő kapcsoló nem látszik a nézőben"
        )
        assert nezo.property("facesEditMode") is False

        _kattints(qt_app, window, gomb)
        assert _varj(qt_app, lambda: nezo.property("facesEditMode") is True), (
            "az első kattintás nem kapcsolta be az arc-szerkesztést"
        )
        assert nezo.property("facesVisible") is True, (
            "az arc-szerkesztés bekapcsolása nem tette láthatóvá a kereteket"
        )

        _kattints(qt_app, window, gomb)
        assert _varj(qt_app, lambda: nezo.property("facesEditMode") is False), (
            "a második kattintás nem kapcsolta ki az arc-szerkesztést"
        )


class TestJelszoTorlesGomb:
    def test_valodi_kattintas_torli_a_jelszot(self, valodi_app, qt_app):
        window, controller, _engine = valodi_app
        _elokeszit(window, qt_app, controller)
        lib = Path(controller.watchedFolders[0])
        for nev in ("latszo", "titkos"):
            (lib / nev).mkdir(parents=True, exist_ok=True)
            make_jpeg(lib / nev / "a.jpg", size=(80, 60))
        controller.rescan()
        assert _varj(qt_app, lambda: controller.waitForBackgroundWorkers(0.05))
        controller.toggleFolderHidden(str(lib / "titkos"))
        controller.setShowHidden(True)
        assert _varj(
            qt_app, lambda: _vizualis_elem(window, _REJTETT_FEJLEC) is not None
        ), "a Rejtett mappák fejléce nem jelent meg"
        controller.setHiddenPassword("titok", False)
        assert controller.hiddenPasswordSet is True, "a jelszó nem állt be"
        # a jelszó beállítása újraépíti a fejlécet: csak a stabil állapotot kattintjuk
        qt_app.processEvents()
        assert _varj(
            qt_app, lambda: _vizualis_elem(window, _REJTETT_FEJLEC) is not None
        ), "a jelszó beállítása után nem maradt fejléc"

        # a Rejtett mappák fejlécének helyi menüje → „Jelszó megadása/módosítása”
        _kattints(
            qt_app,
            window,
            _vizualis_elem(window, _REJTETT_FEJLEC),
            Qt.MouseButton.RightButton,
        )
        menu = _gyerek(window, "collectionContextMenu")
        assert _varj(qt_app, lambda: menu.property("opened") is True), (
            "jobb gombra nem nyílt meg a gyűjtemény-menü"
        )
        _menupont(qt_app, window, "collectionMenuPassword")

        assert _varj(qt_app, lambda: _latszik(window, "hiddenPasswordDialog")), (
            "a jelszó-párbeszéd nem nyílt meg"
        )
        parbeszed = _gyerek(window, "hiddenPasswordDialog")
        torlo = _gyerek(window, "hiddenPasswordClear")
        ablak = torlo.window()
        assert torlo.property("visible") is True, (
            "beállított jelszó mellett nem látszik a törlés gomb"
        )

        _kattints(qt_app, ablak, torlo)

        assert _varj(qt_app, lambda: controller.hiddenPasswordSet is False), (
            "a törlés gomb valódi kattintásra nem törölte a jelszót"
        )
        assert _varj(qt_app, lambda: not _latszik(window, "hiddenPasswordDialog")), (
            "a törlés után a jelszó-párbeszéd nyitva maradt"
        )
        _zar(qt_app, parbeszed)


class TestDuplikatumMegszakitasGomb:
    def test_valodi_kattintas_megszakitja_a_keresest(self, dedup_app, qt_app):
        window, controller, _lib, engine = dedup_app
        _elokeszit(window, qt_app, controller)
        _megnyit(window, qt_app, "&Tools")
        # a Manage Duplicates... az Experimental almenüben ül, azt előbb nyitjuk
        tools = _gyoker_menu(window.property("menuBar"), "&Tools")
        experimental = next(
            elem
            for elem in tools.findChildren(QObject)
            if shiboken6.isValid(elem) and elem.property("title") == "Experimental"
        )
        _kattints(qt_app, window, _almenu_sora(tools, experimental))
        assert _varj(qt_app, lambda: experimental.property("opened") is True), (
            "az Experimental almenü nem nyílt meg"
        )
        _menupont(qt_app, window, "menuToolsDedupManager")

        assert _varj(qt_app, lambda: _latszik(window, "dedupDialog")), (
            "a Duplikátumok kezelője nem nyílt meg"
        )
        parbeszed = _gyerek(window, "dedupDialog")
        assert _varj(qt_app, lambda: parbeszed.property("scanning") is False), (
            "az első keresés nem állt le"
        )

        # a Mégse csak futó keresés közben látszik: a jelzőt erre állítjuk
        parbeszed.setProperty("scanning", True)
        qt_app.processEvents()
        megszakitva = []
        dedup = engine.rootContext().contextProperty("dedupController")
        dedup.scanCancelled.connect(lambda: megszakitva.append(True))

        # a párbeszédet aktiváljuk, mint a felhasználó: enélkül a kattintás
        # a nem aktív ablakon nem ért el a gombig (a próbán ez volt a bukás)
        parbeszed.requestActivate()
        assert _varj(qt_app, lambda: parbeszed.isActive() is True), (
            "a duplikátum-kezelő nem kapta meg a fókuszt"
        )
        cancel = _gyerek(window, "dedupCancelButton")
        # a sáv elrendezése a következő körben áll be: csak a két egymás utáni,
        # azonos geometriát kattintjuk, különben a középpont a régi helyre esik
        geometriak = []

        def _allando_geometria() -> bool:
            geometriak.append((cancel.x(), cancel.y(), cancel.width(), cancel.height()))
            return (
                cancel.property("visible") is True
                and len(geometriak) >= 2
                and geometriak[-1] == geometriak[-2]
                and geometriak[-1][2] > 0
            )

        assert _varj(qt_app, _allando_geometria), (
            "a Mégse gomb elrendezése nem állt meg a kattintás előtt"
        )
        _kattints(qt_app, parbeszed, cancel)

        assert _varj(qt_app, lambda: parbeszed.property("scanning") is False), (
            "a Mégse gomb nem állította le a keresést"
        )
        assert megszakitva == [True], "a Mégse gomb nem jelzett a vezérlőnek"
        _zar(qt_app, parbeszed)


class TestGyorsbillentyuk:
    def test_ctrl_f7_hasonlora_keres_a_kijeloltre(self, valodi_app, qt_app):
        window, controller, _engine = valodi_app
        _elokeszit(window, qt_app, controller)

        QTest.keyClick(window, Qt.Key.Key_F7, Qt.KeyboardModifier.ControlModifier)

        assert _varj(
            qt_app,
            lambda: str(controller.similaritySample or "").endswith(_KEPEK[0]),
        ), "a Ctrl+F7 nem a kijelölt kép lett a hasonlóság mintája"

    def test_ctrl_f8_torli_a_hasonlosag_mintat(self, valodi_app, qt_app):
        window, controller, _engine = valodi_app
        _elokeszit(window, qt_app, controller)
        QTest.keyClick(window, Qt.Key.Key_F7, Qt.KeyboardModifier.ControlModifier)
        assert _varj(qt_app, lambda: str(controller.similaritySample or "") != ""), (
            "a Ctrl+F7 előtt nincs minta, így a törlés nem mérhető"
        )

        QTest.keyClick(window, Qt.Key.Key_F8, Qt.KeyboardModifier.ControlModifier)

        assert _varj(qt_app, lambda: str(controller.similaritySample or "") == ""), (
            "a Ctrl+F8 nem törölte a hasonlóság mintáját"
        )
        assert _varj(qt_app, lambda: controller.filterActive is False), (
            "a minta törlése után a szűrő aktív maradt"
        )

    def test_ctrl_shift_b_fekete_feher_a_kijelolesre(self, valodi_app, qt_app):
        window, controller, _engine = valodi_app
        _elokeszit(window, qt_app, controller)
        ini = Path(controller.watchedFolders[0]) / _MAPPA / ".picasa.ini"
        mod = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier

        QTest.keyClick(window, Qt.Key.Key_B, mod)

        assert _varj(qt_app, lambda: "bw=1;" in _ini_szoveg(ini)), (
            "a Ctrl+Shift+B nem írta a fekete-fehér szűrőt a kijelölt képhez"
        )
        assert _varj(qt_app, lambda: controller.canUndoBatchEdit is True), (
            "a köteg-szerkesztés nem vonható vissza"
        )

    def test_ctrl_shift_e_jo_napom_van_a_kijelolesre(self, valodi_app, qt_app):
        window, controller, _engine = valodi_app
        _elokeszit(window, qt_app, controller)
        ini = Path(controller.watchedFolders[0]) / _MAPPA / ".picasa.ini"
        mod = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier

        QTest.keyClick(window, Qt.Key.Key_E, mod)

        assert _varj(qt_app, lambda: "enhance=1;" in _ini_szoveg(ini)), (
            "a Ctrl+Shift+E nem írta a „Jó napom van” szűrőt a kijelölt képhez"
        )
