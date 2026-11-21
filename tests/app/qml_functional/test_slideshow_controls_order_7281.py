"""A diavetítés sávja a mért sorrendet és a lista végi tartóelemet őrzi (#7281)."""

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

from support.qt_wait import varj_feltetelre

_ROOT = Path(__file__).resolve().parents[3]
_QML = _ROOT / "src/picasapy/app/qml"
_IMAGE = _ROOT / "tests/fixtures/slideshow_6102/image-600.png"
_SORREND = (
    "slideshowExitButton",
    "slideshowImageSliderSlot",
    "slideshowRotateLeftButton",
    "slideshowRotateRightButton",
    "slideshowPrevButton",
    "slideshowPlayButton",
    "slideshowNextButton",
    "slideshowStarButton",
    "slideshowTransitionBox",
    "slideshowCaptionModeButton",
    "slideshowTimeBlock",
)
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

    @Property(int, notify=revisionChanged)
    def revision(self) -> int:
        return 0

    @Slot(result=int)
    def rowCount(self) -> int:
        return 2

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
        return 1024

    @Slot(int, result=int)
    def pixelHeightAt(self, _index: int) -> int:
        return 576

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


def _render(view: QQuickView):
    image = view.grabWindow()
    assert not image.isNull(), "a vetítő valódi képernyőképe üres"
    return image


def _regio_megvaltozott(before, after, item: QQuickItem) -> bool:
    point = item.mapToScene(item.boundingRect().topLeft())
    scale = after.devicePixelRatio()
    left = floor(point.x() * scale)
    top = floor(point.y() * scale)
    right = ceil((point.x() + item.width()) * scale)
    bottom = ceil((point.y() + item.height()) * scale)
    return any(
        before.pixelColor(x, y) != after.pixelColor(x, y)
        for y in range(top, bottom)
        for x in range(left, right)
    )


def _valodi_kattintas(view: QQuickView, qt_app, item: QQuickItem) -> None:
    pont = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        view,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("height", (595, 600, 605))
def test_a_vezerlosav_sorrendje_es_lista_vegi_tartoeleme_renderelt(
    qt_app, height
):
    """A sáv a mért sorrendben áll; a hely az első dián üres, a végén csúszka (#7281, #7322)."""
    view = QQuickView()
    view.engine().addImportPath(str(_QML))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    view.setSource(QUrl.fromLocalFile(str(_QML / "PicasaPy/SlideshowView.qml")))
    assert view.status() == QQuickView.Status.Ready, [
        error.toString() for error in view.errors()
    ]
    view.resize(1024, height)
    root = view.rootObject()
    model = _PhotosModel()
    root.setProperty("photosModel", model)
    root.setProperty("captionMode", "none")
    root.setProperty("transitionKind", "cut")
    root.setProperty("transitionMs", 120)
    root.setProperty("loop", False)
    view.show()
    assert varj_feltetelre(
        qt_app, lambda: round(root.height()) == height, masodperc=10.0
    ), "a vetítő nem követte az ablakmagasságát"

    QMetaObject.invokeMethod(
        root,
        "start",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 0),
        Q_ARG("QVariant", True),
    )
    controls = _item(root, "slideshowControls")
    hide_timer = _object(root, "slideshowHideTimer")
    QMetaObject.invokeMethod(hide_timer, "stop", Qt.ConnectionType.DirectConnection)
    controls.setProperty("shown", True)
    assert varj_feltetelre(
        qt_app,
        lambda: float(controls.property("opacity")) >= 0.999,
        masodperc=10.0,
    ), "a szüneteltetett sáv nem jelent meg"

    sorrend = [_item(root, name) for name in _SORREND]
    elso_xek = tuple(float(item.x()) for item in sorrend)
    assert all(a < b for a, b in zip(elso_xek, elso_xek[1:], strict=False)), (
        "a sáv elemei nem a mért balról jobbra sorrendben állnak: "
        f"{dict(zip(_SORREND, elso_xek, strict=True))}"
    )
    slot = sorrend[1]
    tartalom = _item(root, "slideshowImageSliderContent")
    assert slot.width() > 0 and not tartalom.isVisible(), (
        "az első szünetben a fenntartott hely nem üres"
    )
    elso_sor_szelesseg = sorrend[0].parentItem().width()
    elso_kep = _render(view)

    QMetaObject.invokeMethod(root, "advance", Qt.ConnectionType.DirectConnection)
    assert varj_feltetelre(
        qt_app,
        lambda: int(root.property("currentIndex")) == 1,
        masodperc=10.0,
    ), "a vetítő nem érte el a lista utolsó képét"
    QMetaObject.invokeMethod(root, "advance", Qt.ConnectionType.DirectConnection)
    assert root.property("playing") is False
    # #7322: a lista végén a fenntartott helyen képikon és csúszka áll; a hely
    # mérete, a sor szélessége és a gombok sorrendje változatlan marad.
    qt_app.processEvents()
    vegso_kep = _render(view)
    assert tartalom.isVisible(), "a lista végén nem jelent meg a csúszka"
    assert tuple(float(item.x()) for item in sorrend) == elso_xek
    assert sorrend[0].parentItem().width() == elso_sor_szelesseg
    assert elso_kep.size() == vegso_kep.size()

    QMetaObject.invokeMethod(root, "stop", Qt.ConnectionType.DirectConnection)
    view.close()
    view.deleteLater()
    qt_app.processEvents()


@pytest.mark.parametrize(
    ("width", "height"),
    (
        (800, 595),
        (800, 600),
        (800, 605),
        (1280, 600),
    ),
)
def test_a_vezerlosav_gombjai_800_px_en_belul_es_kattinthatoak(
    qt_app, width, height
):
    """A keskeny vetítőn minden gomb elfér és valódi kattintást kap (#7314)."""
    view = QQuickView()
    view.engine().addImportPath(str(_QML))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    view.setSource(QUrl.fromLocalFile(str(_QML / "PicasaPy/SlideshowView.qml")))
    assert view.status() == QQuickView.Status.Ready, [
        error.toString() for error in view.errors()
    ]
    view.resize(width, height)
    root = view.rootObject()
    model = _PhotosModel()
    root.setProperty("photosModel", model)
    root.setProperty("captionMode", "none")
    root.setProperty("transitionKind", "cut")
    root.setProperty("loop", False)
    view.show()
    assert varj_feltetelre(
        qt_app,
        lambda: round(root.width()) == width and round(root.height()) == height,
        masodperc=10.0,
    ), "a vetítő nem vette fel a kért ablakméretet"
    QMetaObject.invokeMethod(
        root,
        "start",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 0),
        Q_ARG("QVariant", True),
    )
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
    ), "a diavetítő vezérlősávja nem jelent meg"

    ablakpont = controls.mapToItem(root, QPointF(0, 0))
    assert ablakpont.x() >= 0 and ablakpont.x() + controls.width() <= root.width(), (
        f"a sáv kilóg a {width} px-es nézőből: "
        f"x={ablakpont.x():.1f}, szélesség={controls.width():.1f}"
    )
    gombok = {nev: _item(root, nev) for nev in _KATTINTHATO_GOMBOK}
    for nev, gomb in gombok.items():
        pont = gomb.mapToItem(root, QPointF(0, 0))
        assert gomb.isVisible() and gomb.isEnabled(), f"{nev} nem használható"
        assert gomb.width() > 0 and gomb.height() > 0, f"{nev} mérete nulla"
        assert (
            pont.x() >= 0
            and pont.y() >= 0
            and pont.x() + gomb.width() <= root.width()
            and pont.y() + gomb.height() <= root.height()
        ), f"{nev} kilóg a {width}×{height} px-es nézőből"

    slot = _item(root, "slideshowImageSliderSlot")
    if width == 1280:
        assert slot.width() == pytest.approx(157), (
            "a 1280 px-es elrendezésben megváltozott a mért csúszkahely"
        )
    else:
        assert slot.width() < 157, "800 px-en az üres csúszkahely nem húzódott össze"

    view.requestActivate()
    assert QTest.qWaitForWindowActive(view, 5000), "a vetítőablak nem lett aktív"
    kattintasok = {nev: 0 for nev in _KATTINTHATO_GOMBOK}
    for nev, gomb in gombok.items():
        gomb.clicked.connect(
            lambda *_, gomb_nev=nev: kattintasok.__setitem__(
                gomb_nev, kattintasok[gomb_nev] + 1
            )
        )
    root.secondsChosen.connect(lambda value: root.setProperty("seconds", value))
    root.captionModePicked.connect(
        lambda value: root.setProperty("captionMode", value)
    )

    _valodi_kattintas(view, qt_app, gombok["slideshowRotateLeftButton"])
    _valodi_kattintas(view, qt_app, gombok["slideshowRotateRightButton"])
    _valodi_kattintas(view, qt_app, gombok["slideshowNextButton"])
    assert root.property("currentIndex") == 1, "a Következő kattintása nem léptetett"
    _valodi_kattintas(view, qt_app, gombok["slideshowPrevButton"])
    assert root.property("currentIndex") == 0, "az Előző kattintása nem léptetett vissza"
    _valodi_kattintas(view, qt_app, gombok["slideshowPlayButton"])
    assert root.property("playing") is True, "a Lejátszás kattintása nem indított"
    _valodi_kattintas(view, qt_app, gombok["slideshowPlayButton"])
    assert root.property("playing") is False, "a Szünet kattintása nem állított meg"
    _valodi_kattintas(view, qt_app, gombok["slideshowStarButton"])
    _valodi_kattintas(view, qt_app, gombok["slideshowCaptionModeButton"])
    assert root.property("captionMode") == "caption"
    _valodi_kattintas(view, qt_app, gombok["slideshowTimeMinus"])
    assert root.property("seconds") == 2, "a diaidő mínusz gombja nem kattintható"
    _valodi_kattintas(view, qt_app, gombok["slideshowTimePlus"])
    assert root.property("seconds") == 3, "a diaidő plusz gombja nem kattintható"
    _valodi_kattintas(view, qt_app, gombok["slideshowExitButton"])
    assert root.isVisible() is False, "a Kilépés gomb kattintása nem zárta be a vetítőt"
    assert kattintasok == {
        nev: (2 if nev == "slideshowPlayButton" else 1)
        for nev in _KATTINTHATO_GOMBOK
    }, f"nem minden gomb kapott valódi kattintást: {kattintasok}"

    view.close()
    view.deleteLater()
    qt_app.processEvents()
