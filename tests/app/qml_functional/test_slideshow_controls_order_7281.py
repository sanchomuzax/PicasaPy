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
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtQuick import QQuickItem, QQuickView

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


@pytest.mark.parametrize("height", (595, 600, 605))
def test_a_vezerlosav_sorrendje_es_lista_vegi_tartoeleme_renderelt(
    qt_app, height
):
    """A sáv a mért sorrendben áll, a fenntartott hely üres (#7281, #7284)."""
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
    # #7284: a csúszka működése nem ismert, ezért a lista végi szünetben
    # sem rajzolunk működés nélküli vezérlőt; a hely és a sorrend marad.
    qt_app.processEvents()
    vegso_kep = _render(view)
    assert not tartalom.isVisible(), "működés nélküli csúszka jelent meg"
    assert tuple(float(item.x()) for item in sorrend) == elso_xek
    assert sorrend[0].parentItem().width() == elso_sor_szelesseg
    assert elso_kep.size() == vegso_kep.size()

    QMetaObject.invokeMethod(root, "stop", Qt.ConnectionType.DirectConnection)
    view.close()
    view.deleteLater()
    qt_app.processEvents()
