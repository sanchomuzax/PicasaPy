"""A diavetítő lista végi képikonja és nagyítócsúszkája (#7322).

Az eredeti Picasa vezérlősávja a lista végén megállt vetítésnél a Kilépés után
képikont és csúszkát mutat (`editpanel/zoomup_icon`, `zoomslider/scaleslider`),
az első dián szüneteltetve nem. A csúszka húzása a kép skáláját állítja, a
diaindexet nem; a Következő nyíl ilyenkor tiltott (`picasa-colab-jobs` #762,
`kepernyo__13`-`15` és `kepernyo__32`-`37`; `docs/specs/picasa-diavetito-sav.md`).

# rontás-kontroll: a csúszka nélküli sávon (`visible: false` tartóelem) az
# összes itteni próba piros (FF); lásd a jegy jelentését a mutációs próbákról.
"""

from __future__ import annotations

from math import ceil, floor
from pathlib import Path

import pytest
from PySide6.QtCore import (
    Property,
    Q_ARG,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

from support.diavetites_sav_7363 import sor as _sor
from support.diavetites_sav_7363 import szabad_hellyel as _szabad_hellyel
from support.qt_wait import varj_feltetelre

_ROOT = Path(__file__).resolve().parents[3]
_QML = _ROOT / "src/picasapy/app/qml"
_IMAGE = _ROOT / "tests/fixtures/slideshow_6102/image-600.png"
#: a próbakép nyers mérete kétszerese az illesztettnek (1024 × 600 nézőben):
#: így a valódi méret és az illesztett különbözik, a leképezés mérhető
_FORRAS_SZELESSEG = 2048
_FORRAS_MAGASSAG = 1200
_KATTINTHATO_GOMBOK = (
    "slideshowExitButton",
    "slideshowRotateLeftButton",
    "slideshowRotateRightButton",
    "slideshowPrevButton",
    "slideshowPlayButton",
    "slideshowNextButton",
    "slideshowStarButton",
    "slideshowCaptionModeButton",
    "slideshowTimeMinus",
    "slideshowTimePlus",
)


class _PhotosModel(QObject):
    revisionChanged = Signal()
    rowsRemoved = Signal(object, int, int)
    modelReset = Signal()

    def __init__(self, sorok: int) -> None:
        super().__init__()
        self._sorok = sorok

    @Property(int, notify=revisionChanged)
    def revision(self) -> int:
        return 0

    @Slot(result=int)
    def rowCount(self) -> int:
        return self._sorok

    @Slot(int, result=bool)
    def isVideoAt(self, _index: int) -> bool:
        return False

    @Slot(int, str, result=str)
    def displayUrlAt(self, _index: int, _mode: str) -> str:
        return QUrl.fromLocalFile(str(_IMAGE)).toString()

    @Slot(int, result=str)
    def filePathAt(self, _index: int) -> str:
        return str(_IMAGE)

    @Slot(int, result=str)
    def captionAt(self, _index: int) -> str:
        return ""

    @Slot(int, result=int)
    def pixelWidthAt(self, _index: int) -> int:
        return _FORRAS_SZELESSEG

    @Slot(int, result=int)
    def pixelHeightAt(self, _index: int) -> int:
        return _FORRAS_MAGASSAG

    @Slot(int, result=int)
    def rotateAt(self, _index: int) -> int:
        return 0

    @Slot(int, result=bool)
    def starAt(self, _index: int) -> bool:
        return False


def _item(root: QObject, name: str) -> QQuickItem:
    item = root.findChild(QQuickItem, name)
    assert item is not None, f"a(z) {name} elem hiányzik"
    return item


def _object(root: QObject, name: str) -> QObject:
    obj = root.findChild(QObject, name)
    assert obj is not None, f"a(z) {name} objektum hiányzik"
    return obj


def _vetito(qt_app, width: int, height: int, *, sorok: int, loop: bool):
    """Megnyitja a vetítőt valódi ablakban; a sáv látható, az időzítő áll."""
    view = QQuickView()
    view.engine().addImportPath(str(_QML))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    view.setSource(QUrl.fromLocalFile(str(_QML / "PicasaPy/SlideshowView.qml")))
    assert view.status() == QQuickView.Status.Ready, [
        error.toString() for error in view.errors()
    ]
    view.resize(width, height)
    root = view.rootObject()
    model = _PhotosModel(sorok)
    root.setProperty("photosModel", model)
    root.setProperty("captionMode", "none")
    root.setProperty("transitionKind", "cut")
    root.setProperty("transitionMs", 120)
    root.setProperty("loop", loop)
    view.show()
    assert varj_feltetelre(
        qt_app,
        lambda: round(root.width()) == width and round(root.height()) == height,
        masodperc=10.0,
    ), "a vetítő nem vette fel a kért ablakméretet"
    return view, root, model


def _inditas_szunetben(qt_app, root, index: int) -> QQuickItem:
    QMetaObject.invokeMethod(
        root,
        "start",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", index),
        Q_ARG("QVariant", True),
    )
    assert root.property("currentIndex") == index
    assert root.property("playing") is False
    controls = _item(root, "slideshowControls")
    QMetaObject.invokeMethod(
        _object(root, "slideshowHideTimer"),
        "stop",
        Qt.ConnectionType.DirectConnection,
    )
    controls.setProperty("shown", True)
    assert varj_feltetelre(
        qt_app,
        lambda: float(controls.property("opacity")) >= 0.999,
        masodperc=10.0,
    ), "a szüneteltetett sáv nem jelent meg"
    qt_app.processEvents()
    return controls


def _lezar(qt_app, view: QQuickView, root: QObject) -> None:
    QMetaObject.invokeMethod(root, "stop", Qt.ConnectionType.DirectConnection)
    view.close()
    view.deleteLater()
    qt_app.processEvents()


def _scene_szelesseg(item: QQuickItem) -> float:
    bal = item.mapToScene(QPointF(0, 0))
    jobb = item.mapToScene(QPointF(item.width(), 0))
    return abs(jobb.x() - bal.x())


def _ablakpont(view: QQuickView, item: QQuickItem, x: float, y: float) -> QPoint:
    pont = item.mapToScene(QPointF(x, y))
    return QPoint(round(pont.x()), round(pont.y()))


def _regio_megvaltozott(elotte, utana, item: QQuickItem) -> bool:
    pont = item.mapToScene(item.boundingRect().topLeft())
    skala = utana.devicePixelRatio()
    bal = floor(pont.x() * skala)
    felso = floor(pont.y() * skala)
    jobb = ceil((pont.x() + item.width()) * skala)
    also = ceil((pont.y() + item.height()) * skala)
    return any(
        elotte.pixelColor(x, y) != utana.pixelColor(x, y)
        for y in range(felso, also)
        for x in range(bal, jobb)
    )


@pytest.mark.parametrize(
    ("index", "loop", "lista_vegen"),
    (
        (0, False, False),
        (1, False, False),
        (2, False, True),
        (2, True, False),
    ),
)
def test_a_csuszka_csak_a_lista_vegen_latszik_es_a_kovetkezo_nyil_tiltott(
    qt_app, index, loop, lista_vegen
):
    """Első és középső dián szünetelve nincs csúszka; a lista végén van (#7322)."""
    view, root, _model = _vetito(qt_app, 1024, 600, sorok=3, loop=loop)
    _inditas_szunetben(qt_app, root, index)

    tartalom = _item(root, "slideshowImageSliderContent")
    ikon = _item(root, "slideshowImageSliderIcon")
    csuszka = _item(root, "slideshowImageSlider")
    slot = _item(root, "slideshowImageSliderSlot")
    kovetkezo = _item(root, "slideshowNextButton")

    assert tartalom.isVisible() is lista_vegen
    assert ikon.isVisible() is lista_vegen
    assert csuszka.isVisible() is lista_vegen
    assert kovetkezo.isEnabled() is (not lista_vegen), (
        "a Következő nyíl a lista végén tiltott, máskor használható"
    )
    assert slot.width() > 0, "a csúszka helye a rejtett állapotban is megmarad"
    if lista_vegen:
        assert ikon.width() > 0 and csuszka.width() > 0
        assert csuszka.x() > ikon.x() + ikon.width() - 1, (
            "a csúszka a képikon után áll"
        )
    _lezar(qt_app, view, root)


def test_a_lista_vegen_a_savban_valoban_kirajzolodik_a_csuszka(qt_app):
    """A renderelt kép is mutatja: a fenntartott hely az első dián üres."""
    view, root, _model = _vetito(qt_app, 1024, 600, sorok=3, loop=False)
    _inditas_szunetben(qt_app, root, 0)
    slot = _item(root, "slideshowImageSliderSlot")
    elso = view.grabWindow()
    assert not elso.isNull()

    root.setProperty("currentIndex", 2)
    qt_app.processEvents()
    vegso = view.grabWindow()
    assert elso.size() == vegso.size()
    assert _regio_megvaltozott(elso, vegso, slot), (
        "a lista végén a fenntartott hely továbbra is üres, nem látszik csúszka"
    )
    _lezar(qt_app, view, root)


def test_a_csuszka_huzasa_a_kep_skalajat_allitja_a_diaindexet_nem(qt_app):
    """Valódi egérhúzás: a kép nagyobb lesz, majd illesztett; az index áll."""
    view, root, _model = _vetito(qt_app, 1024, 600, sorok=3, loop=False)
    _inditas_szunetben(qt_app, root, 2)
    csuszka = _item(root, "slideshowImageSlider")
    kep = _item(root, "slideshowImage")
    kiindulo_szelesseg = _scene_szelesseg(kep)
    assert root.property("imageZoomValue") == pytest.approx(0.0)

    y = csuszka.height() / 2
    bal = _ablakpont(view, csuszka, 6, y)
    jobb = _ablakpont(view, csuszka, csuszka.width() - 6, y)
    view.requestActivate()
    assert QTest.qWaitForWindowActive(view, 5000), "a vetítőablak nem lett aktív"

    QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, bal)
    QTest.mouseMove(view, jobb)
    qt_app.processEvents()
    assert csuszka.property("pressed") is True, "a húzás nem fogta meg a csúszkát"
    QTest.mouseRelease(
        view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, jobb
    )
    qt_app.processEvents()

    assert root.property("imageZoomValue") > 0.9, "a jobb végre húzott csúszka nem nagyít"
    assert _scene_szelesseg(kep) > kiindulo_szelesseg * 1.5, (
        "a csúszka húzása nem változtatta a kép skáláját"
    )
    assert root.property("currentIndex") == 2, "a csúszka húzása léptette a diát"

    QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, jobb)
    QTest.mouseMove(view, bal)
    QTest.mouseRelease(
        view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, bal
    )
    qt_app.processEvents()
    assert root.property("imageZoomValue") < 0.1
    assert _scene_szelesseg(kep) == pytest.approx(kiindulo_szelesseg, rel=0.05), (
        "a bal végállás nem hozta vissza az illesztett méretet"
    )
    assert root.property("currentIndex") == 2
    _lezar(qt_app, view, root)


def test_a_nagyitas_a_mert_lekepezest_koveti_illesztestol_negyszeres_meretig(qt_app):
    """0 = illesztés, 0,5 = valódi méret, 1 = 400 % (a néző mért képlete)."""
    view, root, _model = _vetito(qt_app, 1024, 600, sorok=3, loop=False)
    _inditas_szunetben(qt_app, root, 2)
    kep = _item(root, "slideshowImage")
    alap = _scene_szelesseg(kep)
    valodi_arany = float(kep.property("zoomActualRatio"))
    assert valodi_arany > 1.0, "a próbakép valódi mérete nagyobb az illesztettnél"

    elozo = alap
    for ertek, vart in ((0.0, 1.0), (0.5, valodi_arany), (1.0, 4 * valodi_arany)):
        root.setProperty("imageZoomValue", ertek)
        qt_app.processEvents()
        assert _scene_szelesseg(kep) / alap == pytest.approx(vart, rel=0.01), (
            f"a(z) {ertek} csúszkaérték skálája eltér a mért leképezéstől"
        )
        assert _scene_szelesseg(kep) >= elozo - 1e-6, "a leképezés nem monoton"
        elozo = _scene_szelesseg(kep)
    _lezar(qt_app, view, root)


def test_a_nagyitas_visszaall_ha_a_vetites_elhagyja_a_lista_veget(qt_app):
    """A nagyítás az aktuális képé: a lépés után a másik kép illesztve áll."""
    view, root, _model = _vetito(qt_app, 1024, 600, sorok=3, loop=False)
    _inditas_szunetben(qt_app, root, 2)
    kep = _item(root, "slideshowImage")
    alap = _scene_szelesseg(kep)
    root.setProperty("imageZoomValue", 1.0)
    qt_app.processEvents()
    assert _scene_szelesseg(kep) > alap * 1.5

    QMetaObject.invokeMethod(root, "goBack", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    assert root.property("currentIndex") == 1
    assert root.property("imageZoomValue") == pytest.approx(0.0)
    assert _scene_szelesseg(kep) == pytest.approx(alap, rel=0.01), (
        "a nagyítás átragadt a lista végéről a következő képre"
    )
    _lezar(qt_app, view, root)


def test_a_kovetkezo_nyil_valodi_kattintasra_a_lista_vegen_nem_lep(qt_app):
    """A tiltott nyíl nem fordít vissza az első képre; máshol lép."""
    view, root, _model = _vetito(qt_app, 1024, 600, sorok=3, loop=False)
    _inditas_szunetben(qt_app, root, 1)
    kovetkezo = _item(root, "slideshowNextButton")
    view.requestActivate()
    assert QTest.qWaitForWindowActive(view, 5000), "a vetítőablak nem lett aktív"

    pont = _ablakpont(view, kovetkezo, kovetkezo.width() / 2, kovetkezo.height() / 2)
    QTest.mouseClick(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()
    assert root.property("currentIndex") == 2, "a Következő nem léptetett a lista végéig"

    QTest.mouseClick(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()
    assert root.property("currentIndex") == 2, (
        "a lista végén a tiltott Következő nyíl visszafordított az első képre"
    )
    _lezar(qt_app, view, root)


#: a használható csúszka legkisebb helye: ikon (24) + rés (6) + legalább 40 px-es
#: csúszka (az alatt a csúszka használhatatlanul keskeny)
_HASZNALHATO_HELY = 24 + 6 + 40


def _kilog_a_helyerol(
    kep, ures_kep, sav: QQuickItem, slot: QQuickItem, tolerancia: int = 1
) -> bool:
    """Igaz, ha a két kép a sávban a slot téglalapján KÍVÜL is eltér.

    `kep`: a sáv a csúszka tartalmával; `ures_kep`: ugyanaz a tartalom nélkül
    (átlátszóra állítva). Ha a tartalom a helyén belül marad, a különbség csak a
    slot téglalapjában van; ha rálóg a szomszéd gombra, azon kívül is.
    """
    skala = kep.devicePixelRatio()
    sav_bal = sav.mapToScene(QPointF(0, 0))
    slot_bal = slot.mapToScene(QPointF(0, 0))
    x0, x1 = floor(sav_bal.x() * skala), ceil((sav_bal.x() + sav.width()) * skala)
    y0, y1 = floor(sav_bal.y() * skala), ceil((sav_bal.y() + sav.height()) * skala)
    hely_bal = floor(slot_bal.x() * skala) - tolerancia
    hely_jobb = ceil((slot_bal.x() + slot.width()) * skala) + tolerancia
    return any(
        kep.pixelColor(x, y) != ures_kep.pixelColor(x, y)
        for y in range(max(0, y0), min(kep.height(), y1))
        for x in range(max(0, x0), min(kep.width(), x1))
        if not hely_bal <= x < hely_jobb
    )


@pytest.mark.parametrize("szabad", (70, 120, 160, 226))
def test_szuk_savban_a_csuszka_vagy_hasznalhato_vagy_nem_latszik(qt_app, szabad):
    """Szűk helyen a csúszka nem lóghat rá a szomszéd gombra (#7363).

    A lista végén az átmenetválasztó enged előbb (90 px-ig), a csúszkahely a
    maradékot kapja. Ha az 0 vagy néhány képpont, a hely tartalmát (24 px-es
    ikon, csúszka) nem szabad kirajzolni: a nulla szélességű hely x-e nem
    frissül, és az ikon egy szomszéd gombra (Kilépés vagy forgatás) festett
    volna. A próba renderelt képet néz, nem csak geometriát: a tartalmat
    átlátszóra állítva a sáv képe a slot téglalapján kívül nem változhat.
    """
    view, root, _model = _vetito(qt_app, 1024, 600, sorok=3, loop=False)
    sav = _inditas_szunetben(qt_app, root, 2)
    assert root.property("listaVegen") is True
    _szabad_hellyel(qt_app, view, root, szabad)

    slot = _item(root, "slideshowImageSliderSlot")
    tartalom = _item(root, "slideshowImageSliderContent")
    ikon = _item(root, "slideshowImageSliderIcon")
    csuszka = _item(root, "slideshowImageSlider")
    assert slot.width() == pytest.approx(max(0.0, min(157.0, szabad - 90.0)), abs=1.0), (
        "a lista végén a csúszkahely a rugalmas helyből az átmenetválasztó "
        "90 px-es legkisebb szélessége után maradót kapja"
    )
    if slot.width() >= _HASZNALHATO_HELY:
        assert tartalom.isVisible() and ikon.isVisible() and csuszka.isVisible(), (
            f"a {slot.width():.1f} px-es helyen elfér a csúszka, mégsem látszik"
        )
        assert ikon.x() >= 0 and csuszka.x() + csuszka.width() <= slot.width() + 0.5, (
            f"a csúszka kilóg a fenntartott helyéből: x={csuszka.x():.1f}, "
            f"szélesség={csuszka.width():.1f}, hely={slot.width():.1f}"
        )
        assert csuszka.width() >= 40, "a csúszka használhatatlanul keskeny"
    else:
        assert not tartalom.isVisible(), (
            f"a {slot.width():.1f} px-es helyen nem fér el a csúszka, mégis kirajzolódik"
        )

    kep = view.grabWindow()
    assert not kep.isNull()
    tartalom.setOpacity(0.0)
    qt_app.processEvents()
    ures_kep = view.grabWindow()
    assert kep.size() == ures_kep.size()
    assert not _kilog_a_helyerol(kep, ures_kep, sav, slot), (
        "a csúszkahely tartalma a saját helyén kívülre, szomszéd gombra festett"
    )
    _lezar(qt_app, view, root)


@pytest.mark.parametrize(("szelesseg", "magassag"), ((800, 600), (1280, 600)))
def test_a_lista_vegi_csuszka_a_sav_hataran_belul_marad(
    qt_app, szelesseg, magassag
):
    """800 px-en a #7314 elrendezés nem romlik: a csúszka a helyén belül áll.

    #7363: a csúszka legkisebb használható helye a platformfüggő betűtől függ
    (a windowsos CI-n a rögzített elemek szélesebbek, a hely 800 px-en 0-ra
    szorul). Ezért a "van csúszka és legalább 40 px" állítás csak ott él, ahol a
    hely elég; máshol a tartalomnak nem szabad látszania. Az `availableWidth`-et
    a sor adja, nem a próba tippeli.
    """
    view, root, _model = _vetito(
        qt_app, szelesseg, magassag, sorok=3, loop=False
    )
    sav = _inditas_szunetben(qt_app, root, 2)
    slot = _item(root, "slideshowImageSliderSlot")
    csuszka = _item(root, "slideshowImageSlider")
    ikon = _item(root, "slideshowImageSliderIcon")
    sor = _sor(root)

    sav_pont = sav.mapToItem(root, QPointF(0, 0))
    assert sav_pont.x() >= 0 and sav_pont.x() + sav.width() <= root.width(), (
        f"a sáv kilóg a {szelesseg} px-es nézőből"
    )
    meretek = (
        f"rögzített={float(sor.property('fixedWidth')):.1f}, "
        f"rugalmas={float(sor.property('availableWidth')):.1f}, "
        f"hely={slot.width():.1f}, "
        f"kilépés={_item(root, 'slideshowExitButton').width():.1f}, "
        f"időblokk={_item(root, 'slideshowTimeBlock').width():.1f}"
    )
    if slot.width() >= _HASZNALHATO_HELY:
        assert csuszka.isVisible() and ikon.isVisible(), (
            f"a {slot.width():.1f} px-es helyen nem látszik a csúszka ({meretek})"
        )
        assert ikon.x() >= 0 and csuszka.x() + csuszka.width() <= slot.width() + 0.5, (
            f"a csúszka kilóg a fenntartott helyéből: x={csuszka.x():.1f}, "
            f"szélesség={csuszka.width():.1f}, hely={slot.width():.1f} ({meretek})"
        )
        assert csuszka.width() >= 40, f"a csúszka használhatatlanul keskeny ({meretek})"
    else:
        assert not _item(root, "slideshowImageSliderContent").isVisible(), (
            f"a csúszka kirajzolódik a {slot.width():.1f} px-es helyen ({meretek})"
        )
    for nev in _KATTINTHATO_GOMBOK:
        gomb = _item(root, nev)
        pont = gomb.mapToItem(root, QPointF(0, 0))
        assert (
            pont.x() >= 0
            and pont.x() + gomb.width() <= root.width()
            and pont.y() >= 0
            and pont.y() + gomb.height() <= root.height()
        ), f"{nev} kilóg a {szelesseg}×{magassag} px-es nézőből"
    if szelesseg == 1280:
        assert slot.width() == pytest.approx(157)
    else:
        assert slot.width() < 157
    _lezar(qt_app, view, root)
