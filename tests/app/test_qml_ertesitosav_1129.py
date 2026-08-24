r"""#1129: a lebegő értesítősáv (`CNotifierPopup` — „Picasa Értesítő").

Spec: `docs/specs/picasa-lebego-ertesito.md`.

## Mit mér ez a fájl

A sáv **kerete**: az önálló, keret nélküli, mindig felül lévő ablak, a
benne élő **cellák** (247 × 45), a záró vezérlő, az elvágódó felirat és a
kattintás. A rákötött ESEMÉNYEKBŐL kettő van bent (a kollázs „kész" és az
importálás két záró állapota) — a többi (képernyőfelvétel, „N kép
érkezett") külön jegyé, azokat itt nem mérjük.

A komponens **önállóan** töltődik be (a `Main.qml` gyökerére helyezés az
integrátoré — ld. `test_qml_import_drop_area.py` ugyanezt a mintát).

## Az időzítés mérése — miért nem `sleep`

A cella magától eltűnik, és az átmenetnek hossza van. Mindkettőt lehetne
valós időben mérni — a CI-n az ilyen mérés ingadozó. Ez a fájl ezért a
**beállított** értékeket olvassa ki (`cellLifetimeMs`, `fadeInMs`,
`fadeOutMs`), külön ellenőrzi, hogy a `Timer` és a `Behavior` tényleg
AZOKAT használja, az állapotgépet pedig a `Timer` **kiváltásával** lépteti
— nem a lejárat megvárásával. Nulla időfüggés van benne.

Az alak szándékosan azonos a #1000 (gyűrű-elhalványulás) alakjával:
olvasható `readonly property int` konstansok + `Timer` + `Behavior on
opacity`, iránytól függő animációhosszal. Két versengő időzítés-minta
helyett egy.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt, Signal, Slot
from PySide6.QtTest import QTest

#: A `respack.yt` `notifier` moduljának mért rétegei (a spec „Geometria"
#: szakasza) — a cella és a jobb oldali vezérlősáv.
CELLA_SZELES = 247
CELLA_MAGAS = 45
BAL_SAV = 13
VEZERLO_SAV_X = 226
VEZERLO_SAV_SZELES = 21
ZARO_X = 231
ZARO_Y = 4
ZARO_MERET = 11

#: `0x00657369`: a munkaterület ALSÓ széléhez képesti eltolás.
HORGONY_ELTOLAS = 144


class FakeController(QObject):
    """A `controller` gyökér-kontextus-tulajdonság szükséges szelete."""

    collageDesktopBackgroundReady = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.selected_folders: list[str] = []

    @Slot(str)
    def selectFolder(self, folder_path: str) -> None:
        self.selected_folders.append(str(folder_path))


class FakeImportController(QObject):
    """Az `importSourceController` záró jelzése (importált, sikertelen)."""

    importFinished = Signal(int, int)


def _qml_dir() -> Path:
    import picasapy.app.application as app_module

    return Path(app_module._APP_DIR) / "qml"


def _tolts(nev: str, qt_app):
    """Egy QML-fájl önálló betöltése fake vezérlőkkel.

    ⚠️ A `QQmlComponent`-et VISSZA kell adni: ha csak lokális változó
    marad, a Python felszabadítja, és vele a létrehozott objektum C++
    oldala is eltűnik („Internal C++ object already deleted")."""
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    controller = FakeController()
    import_controller = FakeImportController()
    engine = QQmlEngine()
    engine.addImportPath(str(_qml_dir()))
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty(
        "importSourceController", import_controller
    )
    factory = QQmlComponent(engine, str(_qml_dir() / "PicasaPy" / nev))
    objektum = factory.create()
    assert objektum is not None, factory.errorString()
    return objektum, controller, import_controller, engine, factory


@pytest.fixture
def sav(qt_app):
    """A `PicasaNotifier.qml` önállóan, fake vezérlőkkel."""
    objektum, controller, import_controller, engine, _factory = _tolts(
        "PicasaNotifier.qml", qt_app
    )
    yield objektum, controller, import_controller, qt_app
    objektum.deleteLater()
    engine.deleteLater()
    qt_app.processEvents()


def _walk(item):
    """A VIZUÁLIS fa bejárása — a `Repeater` elemeit a `findChild` NEM
    látja (a delegáltak QObject-szülője nem a `Repeater`)."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _keres(gyoker, nev: str):
    """Elem az `objectName`-je alapján, a vizuális fából."""
    for item in _walk(gyoker):
        if item.objectName() == nev:
            return item
    return None


def _cellak(sav_objektum) -> list:
    """A sávban élő cellák, felülről lefelé.

    ⚠️ A visszaadott listát a hívónak VÁLTOZÓBAN kell tartania, amíg a
    cellákkal dolgozik. A `Repeater` delegáltjának nincs QObject-szülője,
    ezért a PySide a Python-oldali burkoló felszabadításakor a C++
    objektumot is elviszi — a cella gyerekei (pl. az időzítő) ilyenkor
    némán elhalnak („Internal C++ object already deleted"), és egy
    „eltűnt a cella" állítás HAMISAN zöld lenne."""
    talalt = []
    index = 0
    while True:
        cella = _keres(sav_objektum.contentItem(), f"notifierCell{index}")
        if cella is None:
            return talalt
        talalt.append(cella)
        index += 1


def _kattints(ablak, elem) -> None:
    """IGAZI egérkattintás a vezérlő közepére.

    A kezelő közvetlen meghívása akkor is zöld, ha a vezérlő valójában
    elérhetetlen (MEMORY: „a vezérlőre KATTINTS, ne a metódust hívd"). A
    sáv ráadásul önálló ablak, tehát a kattintás pontosan oda küldhető,
    ahová a felhasználóé is érkezne — és így a takarás is mérhető."""
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont.toPoint(),
    )


# --------------------------------------------------------------------------
# 1. Az ABLAK
# --------------------------------------------------------------------------


class TestAzAblak:
    """`0x00657300`: keret nélküli, mindig felül lévő, tálcagomb nélküli."""

    def test_az_ablaknev_a_stringresbol_valo(self, sav):
        objektum, _c, _i, _q = sav
        assert objektum.property("title") == "Picasa Notifier"

    def test_keret_nelkuli_mindig_felul_eszkoz_ablak(self, sav):
        objektum, _c, _i, _q = sav
        flags = int(objektum.property("flags"))
        assert flags & int(Qt.WindowType.FramelessWindowHint)
        assert flags & int(Qt.WindowType.WindowStaysOnTopHint)
        # `WS_EX_TOOLWINDOW` (0x80): nincs tálcagombja
        assert flags & int(Qt.WindowType.Tool) == int(Qt.WindowType.Tool)

    def test_a_szelesseg_fix_247(self, sav):
        objektum, _c, _i, _q = sav
        assert objektum.property("width") == CELLA_SZELES

    def test_ures_allapotban_nem_latszik(self, sav):
        objektum, _c, _i, _q = sav
        assert objektum.property("visible") is False

    def test_a_munkaterulet_also_szelehez_horgonyzodik(self, sav):
        """`SPI_GETWORKAREA` + `local_4 + -0x90`: a MUNKATERÜLET alja
        mínusz 144 képpont a felső él — nem a teljes képernyőé."""
        objektum, _c, _i, _q = sav
        munkateruletMagassag = objektum.property("munkateruletMagassag")
        assert objektum.property("y") == munkateruletMagassag - HORGONY_ELTOLAS

    def test_a_jobb_szelre_all(self, sav):
        objektum, _c, _i, _q = sav
        munkateruletSzelesseg = objektum.property("munkateruletSzelesseg")
        assert objektum.property("x") == munkateruletSzelesseg - CELLA_SZELES


# --------------------------------------------------------------------------
# 2. A CELLA geometriája
# --------------------------------------------------------------------------


class TestACellaGeometriaja:
    """A `respack.yt` `notifier` moduljának mért rétegei."""

    @pytest.fixture
    def cella(self, sav):
        objektum, _c, import_controller, qt_app = sav
        import_controller.importFinished.emit(3, 0)
        qt_app.processEvents()
        cellak = _cellak(objektum)
        assert cellak, "az importálás vége után nincs cella"
        return cellak[0]

    def test_a_cella_247_x_45(self, cella):
        assert cella.property("width") == CELLA_SZELES
        assert cella.property("height") == CELLA_MAGAS

    def test_a_bal_sav_13_szeles(self, cella):
        alap = _keres(cella, "notifierCellBase0")
        assert alap is not None, "hiányzik a bal oldali sáv (`cellbase`)"
        assert alap.property("width") == BAL_SAV

    def test_a_jobb_vezerlosav_a_helyen_van(self, cella):
        sav_elem = _keres(cella, "notifierCellControls0")
        assert sav_elem is not None, "hiányzik a `basedecrect` vezérlősáv"
        assert sav_elem.property("x") == VEZERLO_SAV_X
        assert sav_elem.property("width") == VEZERLO_SAV_SZELES

    def test_a_zaro_vezerlo_a_jobb_FELSO_sarokban_all(self, cella):
        """`close`: 231..242 × 4..15 — a cella koordinátáiban."""
        zaro = _keres(cella, "notifierCellClose0")
        assert zaro is not None, "hiányzik a záró vezérlő"
        assert zaro.property("width") == ZARO_MERET
        assert zaro.property("height") == ZARO_MERET
        pont = zaro.mapToItem(cella, QPointF(0, 0))
        assert (round(pont.x()), round(pont.y())) == (ZARO_X, ZARO_Y)


# --------------------------------------------------------------------------
# 3. A felirat ELVÁGÓDIK, nem tördel
# --------------------------------------------------------------------------


class TestAFeliratElvagodik:
    """A tulajdonos képernyőképe: „A képernyőfelvétel mentése si…".

    Nem a `elide`/`wrapMode` property ÉRTÉKÉT mérjük (azt a PySide nem is
    tudja átkonvertálni), hanem a LÁTHATÓ következményt: a hosszú felirat
    egyetlen sorban marad és csonkolódik, a cella magassága pedig nem nő
    meg. Ez az, ami a felhasználónál számít."""

    #: A `CThumbUI::screensaved` magyar alakja — a képernyőképen ez vágódik
    #: el. Angol forrásszövegként nem szerepel a kódban, itt csak MÉRŐESZKÖZ.
    HOSSZU = "A képernyőfelvétel mentése sikerült, és minden rendben ment"

    @pytest.fixture
    def cella(self, sav):
        objektum, controller, _i, qt_app = sav
        controller.collageDesktopBackgroundReady.emit("/kepek/hosszu/nev.jpg")
        qt_app.processEvents()
        cellak = _cellak(objektum)
        assert cellak, "a kollázs-jelzés után nincs cella"
        return cellak[0]

    def test_a_hosszu_felirat_ELVAGODIK(self, cella, sav):
        _o, _c, _i, qt_app = sav
        felirat = _keres(cella, "notifierCellTitle0")
        assert felirat is not None

        cella.setProperty("title", self.HOSSZU)
        qt_app.processEvents()

        assert felirat.property("truncated") is True, (
            "a hosszú felirat nem csonkolódik — a fix szélességű ablakban "
            "az eredeti is elvágja"
        )

    def test_a_hosszu_felirat_NEM_tordel(self, cella, sav):
        _o, _c, _i, qt_app = sav
        felirat = _keres(cella, "notifierCellTitle0")

        cella.setProperty("title", self.HOSSZU)
        qt_app.processEvents()

        assert felirat.property("lineCount") == 1
        assert cella.property("height") == CELLA_MAGAS

    def test_a_felirat_belefer_a_ket_sav_kozotti_savba(self, cella):
        felirat = _keres(cella, "notifierCellTitle0")
        elerheto = VEZERLO_SAV_X - BAL_SAV
        assert felirat.property("width") <= elerheto


# --------------------------------------------------------------------------
# 4. Az ESEMÉNYEK
# --------------------------------------------------------------------------


class TestImportErtesites:
    """`CAcquireUI::donenotifer` / `errornotifer` — a két záró állapot."""

    def test_a_sikeres_import_utan_a_done_szoveg_all_ki(self, sav):
        objektum, _c, import_controller, qt_app = sav
        import_controller.importFinished.emit(4, 0)
        qt_app.processEvents()

        cella = _cellak(objektum)[0]
        felirat = _keres(cella, "notifierCellTitle0")
        assert felirat.property("text") == "Completed Importing"

    def test_a_sikeres_import_cselekvesi_tippet_is_ad(self, sav):
        objektum, _c, import_controller, qt_app = sav
        import_controller.importFinished.emit(4, 0)
        qt_app.processEvents()

        cella = _cellak(objektum)[0]
        tipp = _keres(cella, "notifierCellHint0")
        assert tipp is not None, "hiányzik a második, cselekvési sor"
        assert tipp.property("text") == "click to view"

    def test_a_hibas_import_utan_a_hibaszoveg_all_ki(self, sav):
        objektum, _c, import_controller, qt_app = sav
        import_controller.importFinished.emit(0, 2)
        qt_app.processEvents()

        cella = _cellak(objektum)[0]
        felirat = _keres(cella, "notifierCellTitle0")
        assert felirat.property("text") == "Error Importing"

    def test_a_sav_lathatova_valik(self, sav):
        objektum, _c, import_controller, qt_app = sav
        import_controller.importFinished.emit(1, 0)
        qt_app.processEvents()
        assert objektum.property("visible") is True


class TestKollazsErtesites:
    """#1168: a `collageDesktopBackgroundReady` gazdája a sáv."""

    def test_a_kesz_kollazs_cellat_kap(self, sav):
        objektum, controller, _i, qt_app = sav
        controller.collageDesktopBackgroundReady.emit("/kepek/kollazs.jpg")
        qt_app.processEvents()

        cella = _cellak(objektum)[0]
        felirat = _keres(cella, "notifierCellTitle0")
        assert felirat.property("text") == "The collage is ready (click here)"

    def test_ures_utvonalra_nem_villan_fel(self, sav):
        objektum, controller, _i, qt_app = sav
        controller.collageDesktopBackgroundReady.emit("")
        qt_app.processEvents()
        assert _cellak(objektum) == []


class TestTobbCella:
    """`cellbase` + `cell1`: az ablak TÖBB bejegyzést tud egymás alatt —
    ezért nem eseményenkénti ablak, hanem egy tartály cellákkal."""

    def test_ket_esemeny_ket_cellat_ad(self, sav):
        objektum, controller, import_controller, qt_app = sav
        import_controller.importFinished.emit(1, 0)
        controller.collageDesktopBackgroundReady.emit("/kepek/k.jpg")
        qt_app.processEvents()

        assert len(_cellak(objektum)) == 2

    def test_az_ablak_a_cellakkal_egyutt_magasodik(self, sav):
        objektum, controller, import_controller, qt_app = sav
        import_controller.importFinished.emit(1, 0)
        controller.collageDesktopBackgroundReady.emit("/kepek/k.jpg")
        qt_app.processEvents()

        assert objektum.property("height") == 2 * CELLA_MAGAS

    def test_egy_cella_zarasa_a_masikat_nem_viszi_el(self, sav):
        objektum, controller, import_controller, qt_app = sav
        import_controller.importFinished.emit(1, 0)
        controller.collageDesktopBackgroundReady.emit("/kepek/k.jpg")
        qt_app.processEvents()
        cellak = _cellak(objektum)

        _kattints(objektum, _keres(cellak[0], "notifierCellClose0"))
        qt_app.processEvents()

        maradt = _cellak(objektum)
        assert len(maradt) == 1
        assert _keres(maradt[0], "notifierCellTitle0").property("text") == (
            "The collage is ready (click here)"
        )


# --------------------------------------------------------------------------
# 5. A KATTINTÁS és a ZÁRÁS
# --------------------------------------------------------------------------


class TestKattintas:
    def test_a_kattintas_a_kep_MAPPAJARA_navigal(self, sav):
        objektum, controller, _i, qt_app = sav
        controller.collageDesktopBackgroundReady.emit("/kepek/kollazs.jpg")
        qt_app.processEvents()
        cellak = _cellak(objektum)

        _kattints(objektum, _keres(cellak[0], "notifierCellHit0"))
        qt_app.processEvents()

        assert controller.selected_folders == ["/kepek"]

    def test_a_kattintas_elviszi_a_cellat(self, sav):
        objektum, controller, _i, qt_app = sav
        controller.collageDesktopBackgroundReady.emit("/kepek/kollazs.jpg")
        qt_app.processEvents()
        cellak = _cellak(objektum)

        _kattints(objektum, _keres(cellak[0], "notifierCellHit0"))
        qt_app.processEvents()

        assert objektum.property("hasCells") is False

    def test_a_zaro_vezerlo_elviszi_a_cellat(self, sav):
        objektum, _c, import_controller, qt_app = sav
        import_controller.importFinished.emit(2, 0)
        qt_app.processEvents()
        cellak = _cellak(objektum)

        _kattints(objektum, _keres(cellak[0], "notifierCellClose0"))
        qt_app.processEvents()

        assert objektum.property("hasCells") is False

    def test_a_zaras_NEM_navigal(self, sav):
        """A záró vezérlő a cella FÖLÖTT ül — ha a kattintás átszivárogna
        a cellára, a bezárás navigálna is."""
        objektum, controller, _i, qt_app = sav
        controller.collageDesktopBackgroundReady.emit("/kepek/kollazs.jpg")
        qt_app.processEvents()
        cellak = _cellak(objektum)

        _kattints(objektum, _keres(cellak[0], "notifierCellClose0"))
        qt_app.processEvents()

        assert controller.selected_folders == []


# --------------------------------------------------------------------------
# 6. Az IDŐZÍTÉS — beállított értékek, nem valós idő
# --------------------------------------------------------------------------


class TestAzIdozites:
    """Amit mérünk: a BEÁLLÍTOTT értékek és az állapotgép — nem az eltelt
    idő. A lejáratot mi váltjuk ki, nem megvárjuk."""

    def test_a_harom_konstans_olvashato_property(self, sav):
        objektum, _c, _i, _q = sav
        assert objektum.property("cellLifetimeMs") > 0
        assert objektum.property("fadeInMs") > 0
        assert objektum.property("fadeOutMs") > 0

    def test_a_cella_idozitoje_a_konstanst_hasznalja(self, sav):
        objektum, _c, import_controller, qt_app = sav
        import_controller.importFinished.emit(1, 0)
        qt_app.processEvents()
        cellak = _cellak(objektum)

        ora = cellak[0].findChild(QObject, "notifierCellLife0")
        assert ora is not None, "a cellának nincs élettartam-időzítője"
        assert ora.property("interval") == objektum.property("cellLifetimeMs")
        assert ora.property("running") is True

    def test_a_lejarat_elviszi_a_cellat(self, sav):
        """A lejáratot KIVÁLTJUK, nem megvárjuk — így a mérés nem függ a
        gép terhelésétől."""
        objektum, _c, import_controller, qt_app = sav
        import_controller.importFinished.emit(1, 0)
        qt_app.processEvents()
        cellak = _cellak(objektum)

        ora = cellak[0].findChild(QObject, "notifierCellLife0")
        QMetaObject.invokeMethod(
            ora, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert objektum.property("hasCells") is False

    def test_az_atmenet_iranya_donti_el_a_hosszat(self, sav):
        """0,25 s be, 0,5 s ki — ugyanaz az alak, mint a #1000-nél."""
        objektum, _c, import_controller, qt_app = sav
        animacio = objektum.findChild(QObject, "notifierFadeAnim")
        assert animacio is not None

        import_controller.importFinished.emit(1, 0)
        qt_app.processEvents()
        assert animacio.property("duration") == objektum.property("fadeInMs")
        cellak = _cellak(objektum)

        _kattints(objektum, _keres(cellak[0], "notifierCellClose0"))
        qt_app.processEvents()
        assert animacio.property("duration") == objektum.property("fadeOutMs")


# --------------------------------------------------------------------------
# 7. A régi, ablakon belüli értesítés ÁTADJA a helyét
# --------------------------------------------------------------------------


class TestACollageDoneNoticeAtadja:
    """#1168 → #1129: a `collageDesktopBackgroundReady`-nek eddig a
    `CollageDoneNotice` volt a fogadója (a főablak alján, kattintásra
    tűnt csak el). Ha a sáv jelen van, a régi értesítés HALLGAT — különben
    a felhasználó ugyanazt kétszer kapná.

    ⚠️ A mérés a `path`-on és nem a `visible`-ön történik: a komponens itt
    ÖNÁLLÓAN, szülő nélkül él, és a QQuickItem `visible`-je ilyenkor a
    hiányzó szülő miatt akkor is hamis, ha a `showFor()` lefutott. A
    `path`-t viszont pontosan a `showFor()` állítja — az mutatja meg, hogy
    a régi értesítés megszólalt-e."""

    def test_sav_nelkul_a_regi_ertesites_MEGSZOLAL(self, qt_app):
        notice, controller, _i, engine, _factory = _tolts(
            "CollageDoneNotice.qml", qt_app
        )
        try:
            controller.collageDesktopBackgroundReady.emit("/kepek/a.jpg")
            qt_app.processEvents()
            assert notice.property("path") == "/kepek/a.jpg"
        finally:
            notice.deleteLater()
            engine.deleteLater()
            qt_app.processEvents()

    def test_savval_a_regi_ertesites_HALLGAT(self, qt_app):
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        controller = FakeController()
        import_controller = FakeImportController()
        engine = QQmlEngine()
        engine.addImportPath(str(_qml_dir()))
        engine.rootContext().setContextProperty("controller", controller)
        engine.rootContext().setContextProperty(
            "importSourceController", import_controller
        )
        objektumok = []
        gyarak = []  # a gyárat életben kell tartani (ld. `_tolts`)
        for nev in ("PicasaNotifier.qml", "CollageDoneNotice.qml"):
            factory = QQmlComponent(engine, str(_qml_dir() / "PicasaPy" / nev))
            gyarak.append(factory)
            objektum = factory.create()
            assert objektum is not None, factory.errorString()
            objektumok.append(objektum)
        savi, notice = objektumok
        try:
            qt_app.processEvents()
            controller.collageDesktopBackgroundReady.emit("/kepek/a.jpg")
            qt_app.processEvents()

            assert notice.property("path") == ""
            assert savi.property("hasCells") is True
        finally:
            for objektum in objektumok:
                objektum.deleteLater()
            engine.deleteLater()
            qt_app.processEvents()
