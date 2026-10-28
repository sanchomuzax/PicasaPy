"""A diavetítés fő képernyőállapotai őrzik a refaktor előtti képet (#6102)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import (
    Property,
    QPointF,
    Q_ARG,
    QMetaObject,
    QObject,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtQuick import QQuickItem, QQuickView

from support.qt_wait import varj_feltetelre

_ROOT = Path(__file__).resolve().parents[3]
_QML = _ROOT / "src/picasapy/app/qml"
_REFERENCIA = _ROOT / "tests/fixtures/slideshow_6102"
_ALLAPOTOK = ("image", "controls", "paused", "transition-end")


class _SlideshowModel(QObject):
    """A két szintetikus képhez szükséges, fájlalapú vetítőmodell."""

    revisionChanged = Signal()
    rowsRemoved = Signal(object, int, int)
    modelReset = Signal()

    def __init__(self, images: list[Path]) -> None:
        super().__init__()
        self._images = images

    @Property(int, notify=revisionChanged)
    def revision(self) -> int:
        return 0

    @Slot(result=int)
    def rowCount(self) -> int:
        return len(self._images)

    @Slot(int, result=bool)
    def isVideoAt(self, _index: int) -> bool:
        return False

    @Slot(int, str, result=str)
    def displayUrlAt(self, index: int, _mode: str) -> str:
        return QUrl.fromLocalFile(str(self._images[index])).toString()

    @Slot(int, result=str)
    def filePathAt(self, index: int) -> str:
        return str(self._images[index])

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


def _photo(path: Path, colors: tuple[str, str, str, str]) -> None:
    image = QImage(1024, 576, QImage.Format.Format_RGB32)
    painter = QPainter(image)
    painter.fillRect(0, 0, 512, 288, QColor(colors[0]))
    painter.fillRect(512, 0, 512, 288, QColor(colors[1]))
    painter.fillRect(0, 288, 512, 288, QColor(colors[2]))
    painter.fillRect(512, 288, 512, 288, QColor(colors[3]))
    painter.fillRect(504, 0, 16, 576, QColor("#ffffff"))
    painter.fillRect(0, 280, 1024, 16, QColor("#111111"))
    painter.end()
    assert image.save(str(path), "PNG")


def _pixels(image: QImage) -> np.ndarray:
    converted = image.convertToFormat(QImage.Format.Format_RGBA8888)
    sor = np.frombuffer(converted.constBits(), dtype=np.uint8).reshape(
        converted.height(), converted.bytesPerLine()
    )
    return sor[:, : converted.width() * 4].reshape(
        converted.height(), converted.width(), 4
    ).copy()


def _egyezo_eltolassal(
    referencia: QImage,
    tenyleges: QImage,
    *,
    also_sav_kihagyasa: int = 0,
) -> tuple[int, int]:
    """Szöveg nélkül hasonlít, legfeljebb 3 px eltolást engedve."""
    assert (referencia.width(), referencia.height()) == (
        tenyleges.width(), tenyleges.height()
    ), "a renderelt vetítőablak mérete eltér a referenciától"
    ref, aktualis = _pixels(referencia), _pixels(tenyleges)
    magassag, szelesseg = ref.shape[:2]
    also = magassag - also_sav_kihagyasa if also_sav_kihagyasa else magassag - 3
    felso = 3
    bal = jobb = 3

    for dy in range(-3, 4):
        for dx in range(-3, 4):
            y0, y1 = max(felso, -dy), min(also, magassag - dy)
            x0, x1 = max(bal, -dx), min(szelesseg - jobb, szelesseg - dx)
            if y0 >= y1 or x0 >= x1:
                continue
            if np.array_equal(
                ref[y0:y1, x0:x1],
                aktualis[y0 + dy : y1 + dy, x0 + dx : x1 + dx],
            ):
                return dx, dy
    raise AssertionError("a renderelt kép nem egyezik a refaktor előtti referenciával")


def _vezerlosav_felso_pixelei(
    referencia: QImage,
    tenyleges: QImage,
    controls: QObject,
    eltolás: tuple[int, int],
) -> None:
    """A sáv feliratmentes felső kitöltését ellenőrzi a saját geometriájából."""
    scene_pont = controls.mapToScene(QPointF(0, 0))
    x0 = referencia.width() // 2 - 12
    y0 = round(scene_pont.y()) + 1
    dx, dy = eltolás
    ref, aktualis = _pixels(referencia), _pixels(tenyleges)
    assert np.array_equal(
        ref[y0 : y0 + 4, x0 : x0 + 24],
        aktualis[y0 + dy : y0 + dy + 4, x0 + dx : x0 + dx + 24],
    ), "a vezérlősáv képpontjai megváltoztak"


def _capture(view: QQuickView) -> QImage:
    image = view.grabWindow()
    assert not image.isNull(), "az offscreen vetítő képernyőképe üres"
    return image


@pytest.mark.parametrize("height", (595, 600, 605))
def test_a_diavetites_negy_fobb_allapota_keppontra_megegyezik(
    qt_app, tmp_path, height
):
    """A szövegterület kimarad; a kép és a sáv szöveg nélküli kitöltése mérődik."""
    first, second = tmp_path / "first.png", tmp_path / "second.png"
    _photo(first, ("#d93a37", "#f5c949", "#426fbd", "#f1f1ed"))
    _photo(second, ("#245f54", "#ce4779", "#ee9940", "#383e84"))

    view = QQuickView()
    view.engine().addImportPath(str(_QML))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    view.setSource(
        QUrl.fromLocalFile(str(_QML / "PicasaPy/SlideshowView.qml"))
    )
    assert view.status() == QQuickView.Status.Ready, [
        error.toString() for error in view.errors()
    ]
    model = _SlideshowModel([first, second])
    root = view.rootObject()
    root.setProperty("photosModel", model)
    root.setProperty("captionMode", "none")
    root.setProperty("transitionKind", "dissolve")
    root.setProperty("transitionMs", 120)
    view.resize(1024, height)
    view.show()
    assert varj_feltetelre(
        qt_app, lambda: round(root.height()) == height, masodperc=10.0
    ), "a vetítő nem követte az ablakmagasságát"

    QMetaObject.invokeMethod(
        root, "start", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    image = root.findChild(QObject, "slideshowImage")
    controls = root.findChild(QQuickItem, "slideshowControls")
    transition = root.findChild(QObject, "slideshowTransition")
    timer = root.findChild(QObject, "slideshowTimer")
    assert image is not None and controls is not None
    assert transition is not None and timer is not None
    assert varj_feltetelre(
        qt_app, lambda: float(image.property("paintedWidth")) > 0, masodperc=10.0
    ), "az első dia nem rajzolódott ki"

    captures: dict[str, QImage] = {}
    controls.setProperty("shown", False)
    assert varj_feltetelre(
        qt_app, lambda: float(controls.property("opacity")) <= 0.001
    )
    captures["image"] = _capture(view)

    controls.setProperty("shown", True)
    assert varj_feltetelre(
        qt_app, lambda: float(controls.property("opacity")) >= 0.999, masodperc=10.0
    ), "a vezérlősáv nem jelent meg"
    captures["controls"] = _capture(view)

    QMetaObject.invokeMethod(root, "togglePause", Qt.ConnectionType.DirectConnection)
    assert root.property("playing") is False
    assert timer.property("running") is False
    captures["paused"] = _capture(view)

    controls.setProperty("shown", False)
    assert varj_feltetelre(
        qt_app, lambda: float(controls.property("opacity")) <= 0.001
    )
    QMetaObject.invokeMethod(root, "togglePause", Qt.ConnectionType.DirectConnection)
    QMetaObject.invokeMethod(root, "advance", Qt.ConnectionType.DirectConnection)
    assert varj_feltetelre(
        qt_app, lambda: bool(transition.property("running")), masodperc=10.0
    ), "a következő diára lépés nem indította el az átmenetet"
    assert varj_feltetelre(
        qt_app,
        lambda: int(root.property("currentIndex")) == 1
        and image.property("source").toString().endswith("second.png")
        and float(image.property("paintedWidth")) > 0
        and not bool(transition.property("running")),
        masodperc=10.0,
    ), "az áttűnés nem ért véget"
    captures["transition-end"] = _capture(view)

    for state in _ALLAPOTOK:
        reference = QImage(str(_REFERENCIA / f"{state}-{height}.png"))
        assert not reference.isNull(), f"hiányzó képernyőkép-referencia: {state}/{height}"
        ignored_height = 100 if state in ("controls", "paused") else 0
        shift = _egyezo_eltolassal(
            reference, captures[state], also_sav_kihagyasa=ignored_height
        )
        if state in ("controls", "paused"):
            _vezerlosav_felso_pixelei(reference, captures[state], controls, shift)

    QMetaObject.invokeMethod(root, "stop", Qt.ConnectionType.DirectConnection)
    view.close()
    view.deleteLater()
    qt_app.processEvents()
