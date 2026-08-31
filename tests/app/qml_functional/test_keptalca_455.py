"""A Képtálca (#455) a VALÓDI alkalmazásban — kirajzolt felületen mérve.

## Mit őriz

A jegy öt teendőjéből azt a négyet, ami eddig hiányzott vagy hibás volt:

1. **a kijelölés automatikusan a tálcába kerül**, és a következő kijelölés
   elsöpri — kivéve, amit a „Kijelölés megtartása" rögzített;
2. a rögzített kép **mappaváltás után is bent marad** (ettől gyűjtő a
   tálca), és a jelvény (`holdadorner` → `holdMark`) a rácsban látszik;
3. az **ürítés rákérdez**, az eredeti `IDS_CLEARTRAY` szövegével — nem a
   MÁSIK párbeszédével (`il_ClearFromTray`), ami korábban itt állt;
4. a **kék infó-sáv és a műveletsor a TÁLCA tartalmán** dolgozik, tehát a
   más mappából tartott képet is beleszámítja.

Ehhez jön a Klipek fül (#1276) előkészítése: a „felhasználtság" az
adatmodellben van, nem a nézetben.

## Miért a valódi ablakban

A #1153 tanulsága: mesterséges burokban felépített panelen és közvetlen
slot-híváson a hibák átcsúsznak. A gombokra ezért **valódi egérrel**
kattintunk, és a jelvényt a kirajzolt cellán mérjük.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.halasztott_parbeszed import epitsd_fel
from support.jpeg_factory import make_jpeg

#: A két próbamappa és képszámuk — a mappákon átnyúló gyűjtéshez.
ALMA = "alma"
KORTE = "korte"


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása — a `Repeater` elemei csak itt látszanak."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _elem(window, nev: str) -> QQuickItem:
    # #1720: az itt keresett elemek a HALASZTOTT párbeszéd
    # belsejében ülnek — előbb fel kell épülnie, a valódi
    # menüponton át (ld. support/halasztott_parbeszed.py).
    epitsd_fel(window, "exportDialog")
    for item in _walk(window.contentItem()):
        if item.objectName() == nev:
            return item
    talalt = window.findChild(QObject, nev)
    assert talalt is not None, f"a(z) {nev} nincs a kirajzolt jelenetben"
    return talalt


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    """Esemény-pörgetés, amíg a feltétel teljesül (vagy lejár az idő)."""
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


def _kattints(window, item: QQuickItem, qt_app, amig=None) -> None:
    """VALÓDI egérkattintás az elem közepére.

    A projekt szabálya: a vezérlőre kattintani kell, nem a metódusát hívni
    — a közvetlen hívás zöld lehet úgy is, hogy a gomb kattinthatatlan
    (tiltott, letakart, nulla méretű). Ezért előbb kivárjuk, hogy az elem
    tényleg látható és engedélyezett legyen.
    """
    assert _var(qt_app, lambda: item.width() > 0 and item.height() > 0), (
        f"{item.objectName()} nem kapott méretet — kattinthatatlan"
    )
    assert item.isEnabled(), f"{item.objectName()} tiltott — nem kattintható"
    kozep = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()
    if amig is not None:
        assert _var(qt_app, amig), (
            f"{item.objectName()} kattintásának nem lett következménye"
        )


def _kijelol(window, qt_app, sorok) -> None:
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _ujraolvas(controller, qt_app) -> None:
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _ket_mappa(qml_app, qt_app):
    """Két almappa két-két képpel — enélkül a „mappákon átnyúló" állítás
    nem is mérhető."""
    window, controller, _engine = qml_app
    lib = Path(controller.watchedFolders[0])
    for mappa in (ALMA, KORTE):
        (lib / mappa).mkdir(exist_ok=True)
        for i in range(2):
            make_jpeg(lib / mappa / f"{mappa}{i}.jpg", size=(80, 60))
    _ujraolvas(controller, qt_app)
    return window, controller, lib / ALMA, lib / KORTE


def _sor(controller, nev: str) -> int:
    """A fájlnév sor-indexe a JELENLEGI rácsban; -1, ha nincs benne.

    ⚠️ A `selectFolder` nálunk NEM szűkíti a rácsot egy mappára — a rács
    feed, és a mappaválasztás csak odagörget (mérve). A „mappákon átnyúló"
    állítás ezért nem mappaváltással mérhető, hanem KERESÉSSEL: az szűkíti
    a modellt, és így a tartott kép tényleg kiesik a rácsból.
    """
    for index, photo in enumerate(controller.photos.photos):
        if photo.name == nev:
            return index
    return -1


def _szukit(controller, qt_app, window, kifejezes: str) -> None:
    """Keresés — a rács a találatokra szűkül, a többi kép kiesik belőle."""
    controller.search(kifejezes)
    qt_app.processEvents()
    _kijelol(window, qt_app, [])


def _kijelolt(window) -> list[int]:
    """A `selectedIndexes` PYTHON-listaként — QML felől `QJSValue` is
    jöhet, a Pythonból írt érték viszont sima lista marad."""
    ertek = window.property("selectedIndexes")
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return [int(sor) for sor in (ertek or [])]


def _talca_utvonalak(controller) -> list[str]:
    return [str(p) for p in (controller.heldPaths or [])]


class TestAKijelolesBekerulATalcaba:
    """„A kijelölés automatikusan a tálcába kerül" — a tálca a kijelölés
    meghosszabbítása volt, nem külön kosár."""

    def test_a_kijeloles_azonnal_a_talcara_kerul(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        assert controller.heldCount == 0
        _kijelol(window, qt_app, [0, 1])
        assert controller.heldCount == 2

    def test_a_kovetkezo_kijeloles_ELSOPRI_a_nem_rogzitettet(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        _kijelol(window, qt_app, [1])
        assert controller.heldCount == 1
        assert [Path(p).name for p in _talca_utvonalak(controller)] == ["b.jpg"]

    def test_a_kijeloles_megszunese_kiuriti_a_talcat(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        _kijelol(window, qt_app, [])
        assert controller.heldCount == 0


class TestMegtartas:
    """A „Kijelölés megtartása" gomb — VALÓDI kattintással."""

    def test_a_rogzitett_kepet_a_kovetkezo_kijeloles_nem_sopri_el(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        _kattints(
            window, _elem(window, "trayHoldButton"), qt_app,
            amig=lambda: controller.isHeldAt(0),
        )
        _kijelol(window, qt_app, [1])
        assert controller.heldCount == 2
        assert sorted(
            Path(p).name for p in _talca_utvonalak(controller)
        ) == ["a.jpg", "b.jpg"]

    def test_a_talca_MAPPAKON_ATNYULVA_gyujt(self, qml_app, qt_app):
        """A jegy lényege: az egyik mappában rögzítesz, a rács utána már nem
        is mutatja azt a képet — a tálcán mégis ott van, és a művelet
        forrása marad."""
        window, controller, _alma, _korte = _ket_mappa(qml_app, qt_app)
        alma_sor = _sor(controller, "alma0.jpg")
        _kijelol(window, qt_app, [alma_sor])
        _kattints(
            window, _elem(window, "trayHoldButton"), qt_app,
            amig=lambda: controller.isHeldAt(alma_sor),
        )
        alma_kep = _talca_utvonalak(controller)[0]

        # a rács a másik mappára szűkül: a rögzített kép SORINDEXE megszűnik
        _szukit(controller, qt_app, window, KORTE)
        assert _sor(controller, "alma0.jpg") == -1, (
            "a szűkítés nem vette ki a rácsból — a teszt nem azt méri, amit hisz"
        )
        _kijelol(window, qt_app, [_sor(controller, "korte0.jpg")])

        utvonalak = _talca_utvonalak(controller)
        assert alma_kep in utvonalak, "a másik mappából tartott kép elveszett"
        assert len(utvonalak) == 2
        assert {Path(p).parent.name for p in utvonalak} == {ALMA, KORTE}

    def test_a_gomb_tiltott_kijeloles_nelkul(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [])
        assert _elem(window, "trayHoldButton").isEnabled() is False


class TestJelvenyARacsban:
    """`thumbui/#holdadorner` — a rácsban látszik, mi van RÖGZÍTVE."""

    def _holdmark(self, window, sor: int):
        for item in _walk(window.contentItem()):
            if item.objectName() != "thumbMouseArea":
                continue
            cella = item.parentItem()
            if cella is None or cella.property("index") != sor:
                continue
            for jelolo in _walk(cella):
                if jelolo.objectName() == "holdMark":
                    return jelolo
        return None

    def test_a_rogzitett_kep_jelvenyt_kap(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        assert self._holdmark(window, 0) is not None
        assert self._holdmark(window, 0).isVisible() is False, (
            "a puszta kijelölés még nem jelvény — azt a kijelölés-keret mutatja"
        )
        _kattints(
            window, _elem(window, "trayHoldButton"), qt_app,
            amig=lambda: controller.isHeldAt(0),
        )
        assert _var(qt_app, lambda: self._holdmark(window, 0).isVisible())

    def test_a_nem_rogzitett_kep_nem_kap_jelvenyt(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        _kattints(
            window, _elem(window, "trayHoldButton"), qt_app,
            amig=lambda: controller.isHeldAt(0),
        )
        _kijelol(window, qt_app, [0, 1])
        assert _var(qt_app, lambda: self._holdmark(window, 0).isVisible())
        assert self._holdmark(window, 1).isVisible() is False


class TestUritesRakerdez:
    """A TELJES ürítés az `IDS_CLEARTRAY` kérdését teszi fel."""

    def test_az_urites_gomb_nem_urit_azonnal_hanem_kerdez(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        parbeszed = _elem(window, "trayClearConfirmDialog")
        assert parbeszed.property("visible") is False

        _kattints(
            window, _elem(window, "trayClearButton"), qt_app,
            amig=lambda: parbeszed.property("visible") is True,
        )
        assert controller.heldCount == 2, "a kattintás magától nem üríthet"

    def test_a_kerdes_szovege_a_TELJES_uritese(self, qml_app, qt_app):
        """⚠️ Itt korábban a MÁSIK párbeszéd szövege állt („old held
        items…"). A spec 4. szakasza szerint az egy külön, FELKÍNÁLT
        takarítás, nem a Törlés gomb megerősítése."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        _kattints(window, _elem(window, "trayClearButton"), qt_app)
        szoveg = _elem(window, "trayClearConfirmText").property("text")
        assert "entire tray" in szoveg
        assert "old held items" not in szoveg

    def test_a_megse_erintetlenul_hagyja_a_talcat(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        parbeszed = _elem(window, "trayClearConfirmDialog")
        _kattints(
            window, _elem(window, "trayClearButton"), qt_app,
            amig=lambda: parbeszed.property("visible") is True,
        )
        _kattints(window, _elem(window, "trayClearConfirmNoButton"), qt_app)
        assert controller.heldCount == 2

    def test_a_megerositesre_kiurul(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        parbeszed = _elem(window, "trayClearConfirmDialog")
        _kattints(
            window, _elem(window, "trayClearButton"), qt_app,
            amig=lambda: parbeszed.property("visible") is True,
        )
        _kattints(
            window, _elem(window, "trayClearConfirmYesButton"), qt_app,
            amig=lambda: controller.heldCount == 0,
        )
        assert controller.heldCount == 0


class TestAKekSavATalcarolIr:
    """`il_GetSelectionInfo` — a sáv a tálcát összesíti, tehát a más
    mappából tartott képet is."""

    def test_a_masik_mappabol_tartott_kep_is_beleszamit(
        self, qml_app, qt_app
    ):
        window, controller, _alma, _korte = _ket_mappa(qml_app, qt_app)
        alma_sor = _sor(controller, "alma0.jpg")
        _kijelol(window, qt_app, [alma_sor])
        _kattints(
            window, _elem(window, "trayHoldButton"), qt_app,
            amig=lambda: controller.isHeldAt(alma_sor),
        )
        _szukit(controller, qt_app, window, KORTE)
        korte_sor = _sor(controller, "korte0.jpg")
        _kijelol(window, qt_app, [korte_sor])

        sav = _elem(window, "trayInfoText")
        assert _var(qt_app, lambda: sav.property("text") == controller.trayInfo())
        # a lényeg: a sáv KETTŐT összesít, pedig a rácsban egy kép van
        # kijelölve — a kijelölés-alapú szöveg mást mondana
        assert sav.property("text") != controller.selectionInfo([korte_sor])
        assert "2" in sav.property("text"), sav.property("text")

    def test_ures_talcanal_marad_a_mai_osszesites(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [])
        sav = _elem(window, "trayInfoText")
        assert _var(qt_app, lambda: sav.property("text") == controller.statusText)


class TestAMuveletsorATalcanDolgozik:
    """A jegy 3. teendője: a művelet a TÁLCA tartalmán fut (`trayexec`)."""

    def test_az_export_a_masik_mappabol_tartott_kepet_viszi(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _alma, _korte = _ket_mappa(qml_app, qt_app)
        alma_sor = _sor(controller, "alma0.jpg")
        _kijelol(window, qt_app, [alma_sor])
        _kattints(
            window, _elem(window, "trayHoldButton"), qt_app,
            amig=lambda: controller.isHeldAt(alma_sor),
        )
        tartott = Path(_talca_utvonalak(controller)[0])

        # a rács a MÁSIK mappára szűkül, és ott semmi nincs kijelölve:
        # a kijelölés-alapú út ilyenkor semmit nem exportálna
        _szukit(controller, qt_app, window, KORTE)
        assert _kijelolt(window) == []
        assert _sor(controller, tartott.name) == -1

        cel = tmp_path / "export-cel"
        cel.mkdir()
        controller.exportHeld(str(cel), 0, 85, False, "")
        assert _var(
            qt_app, lambda: [p.name for p in cel.glob("*.jpg")] == [tartott.name]
        ), f"a tálca tartalma nem került ki: {list(cel.glob('*'))}"

    def test_az_export_parbeszed_a_talcat_valasztja_kijeloles_nelkul(
        self, qml_app, qt_app
    ):
        window, controller, _alma, _korte = _ket_mappa(qml_app, qt_app)
        alma_sor = _sor(controller, "alma0.jpg")
        _kijelol(window, qt_app, [alma_sor])
        _kattints(
            window, _elem(window, "trayHoldButton"), qt_app,
            amig=lambda: controller.isHeldAt(alma_sor),
        )
        _szukit(controller, qt_app, window, KORTE)
        parbeszed = _elem(window, "exportDialog")
        assert _var(qt_app, lambda: parbeszed.property("useTray") is True)


class TestKlipekFulElokeszites:
    """#1276: a Klipek fül a tálca FEL NEM HASZNÁLT képeit mutatja
    (`collagepanel/filmstrip_title` = `Unused Pictures`). Ez a kör a
    modellt adja hozzá — a fül átkötése a #1276 dolga."""

    def test_a_felhasznalt_kep_a_talcan_marad_de_kiesik_a_listabol(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        assert controller.trayUnusedCount == 2

        elso = controller.trayItems[0]["photoId"]
        controller.setTrayUsed([elso], True)
        qt_app.processEvents()

        assert controller.heldCount == 2, "a felhasznált kép a tálcán marad"
        assert controller.trayUnusedCount == 1
        allapotok = {t["photoId"]: t["used"] for t in controller.trayItems}
        assert allapotok[elso] is True

    def test_a_felhasznaltsag_visszavonhato(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        elso = controller.trayItems[0]["photoId"]
        controller.setTrayUsed([elso], True)
        controller.setTrayUsed([elso], False)
        qt_app.processEvents()
        assert controller.trayUnusedCount == 1

    def test_a_felhasznalt_kepet_a_kovetkezo_kijeloles_sem_sopri_el(
        self, qml_app, qt_app
    ):
        """A felhasználtság olyan állapot, amit a kijelölésből nem lehet
        visszaállítani — elsöpörni néma adatvesztés volna."""
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        elso = controller.trayItems[0]["photoId"]
        controller.setTrayUsed([elso], True)
        _kijelol(window, qt_app, [1])
        assert controller.heldCount == 2
        assert controller.trayUnusedCount == 1

    def test_a_lista_minden_eleme_kirajzolhato_adatot_ad(
        self, qml_app, qt_app
    ):
        """A Klipek lapnak útvonal ÉS bélyegkép-URL is kell — enélkül a
        modell megvan, a lista mégis üres marad (a #1153 hibaosztálya)."""
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        elem = controller.trayItems[0]
        assert Path(elem["path"]).exists()
        assert elem["thumbUrl"].startswith("image://thumbs/")
        assert elem["name"]
