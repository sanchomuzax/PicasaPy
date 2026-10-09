"""A Helyek térképjelölője és a buborék műveletei (#4582)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QSignalSpy, QTest

from tests.app.qml_functional.conftest import _build_qml_app
from support.jpeg_factory import make_jpeg

import picasapy.app


_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_PLACES_MAP = (_QML / "PlacesMap.qml").read_text(encoding="utf-8")

def _hat_kepet_keszit(konyvtar):
    for index in range(6):
        make_jpeg(
            konyvtar / f"hely-{index}.jpg",
            size=(120, 90),
        )


def _bejár(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _bejár(child)


def _keres_elem(window, object_name: str):
    item = next(
        (
            item
            for item in _bejár(window.contentItem())
            if item.objectName() == object_name
        ),
        None,
    )
    return item if item is not None else window.findChild(QObject, object_name)


def _elem(window, object_name: str) -> QQuickItem:
    item = _keres_elem(window, object_name)
    if item is None:
        raise AssertionError(f"A kirajzolt főablakból hiányzik: {object_name}")
    return item


def _var(qt_app, predicate, timeout: float = 3.0) -> bool:
    hatarido = time.monotonic() + timeout
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        try:
            if predicate():
                return True
        except (AttributeError, RuntimeError, TypeError):
            pass
        QTest.qWait(50)
    return bool(predicate())


def _kattint(window, item: QQuickItem, qt_app) -> None:
    assert _var(qt_app, lambda: item.width() > 0 and item.height() > 0)
    scene_point = item.mapToScene(item.boundingRect().center())
    pont = QPoint(round(scene_point.x()), round(scene_point.y()))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont,
    )
    qt_app.processEvents()


def _sorok(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def test_a_terkep_a_kozos_jelolokomponenst_hasznalja():
    assert "sourceItem: PlacesMarker" in _PLACES_MAP
    assert "markerData: markerItem.modelData" in _PLACES_MAP
    assert "root.markerSearchRequested(rows)" in _PLACES_MAP
    assert "root.markerEraseRequested(rows)" in _PLACES_MAP


@pytest.fixture
def qml_app_hat_keppel(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app, tmp_path, kepeket_keszit=_hat_kepet_keszit
    )


@pytest.mark.parametrize("magassag_delta", [-5, 0, 5])
def test_jelolo_buborek_keres_es_torol(
    qml_app_hat_keppel, qt_app, tmp_path, magassag_delta
):
    window, controller, engine = qml_app_hat_keppel
    konyvtar = tmp_path / "kepek"
    window.resize(window.width(), window.height() + magassag_delta)
    qt_app.processEvents()

    _kattint(window, _elem(window, "trayPanelToggle_places"), qt_app)
    panel = _elem(window, "placesPanel")
    assert _var(qt_app, panel.isVisible)

    sorok = list(range(6))
    controller.setGeotagRows(sorok, 47.5, 19.05)
    assert _var(qt_app, lambda: len(controller.geoMarkers) == 6)
    marker = controller.geoMarkers[0]
    assert marker["thumbUrl"].startswith("image://thumbs/")

    # A QtLocation ezen a gépen nincs telepítve. A PlacesMap ugyanazt a
    # modulfüggetlen PlacesMarker komponenst használja, ezért a komponenst
    # közvetlenül a valódi ablak közepére tesszük és azon kattintunk.
    komponens = QQmlComponent(
        engine, QUrl.fromLocalFile(str(_QML / "PlacesMarker.qml"))
    )
    assert komponens.status() == QQmlComponent.Status.Ready, komponens.errorString()
    jelolo = komponens.create()
    assert jelolo is not None, komponens.errorString()
    QQmlEngine.setObjectOwnership(jelolo, QQmlEngine.ObjectOwnership.CppOwnership)
    jelolo.setProperty(
        "markerData",
        {"rows": sorok, "thumbUrl": marker["thumbUrl"]},
    )
    jelolo.setParentItem(window.contentItem())
    jelolo.setX((window.contentItem().width() - jelolo.width()) / 2)
    jelolo.setY((window.contentItem().height() - jelolo.height()) / 2)
    jelolo.markerActivated.connect(panel.photoActivated)
    jelolo.markerSearchRequested.connect(panel.markerSearchRequested)
    jelolo.markerEraseRequested.connect(panel.clearGeotagRequested)

    assert _var(qt_app, lambda: jelolo.property("thumbnailReady") is True)
    kep = _elem(window, "placesMarkerImage")
    scene_pont = kep.mapToScene(kep.boundingRect().center())
    assert 0 <= scene_pont.x() < window.width()
    assert 0 <= scene_pont.y() < window.height()
    aktivalas = QSignalSpy(jelolo.markerActivated)
    _kattint(window, kep, qt_app)
    assert aktivalas.count() == 1, (
        "a jelölő kattintása nem érte el a QML-t: "
        f"scene={kep.mapToScene(kep.boundingRect().center())}, "
        f"enabled={kep.isEnabled()}, root={jelolo.x()},{jelolo.y()}, "
        f"window={jelolo.window()}"
    )

    buborek = _elem(window, "placesMarkerBubble")
    szamlalo = _elem(window, "placesMarkerPhotosHere")
    keres = _elem(window, "placesMarkerSearchButton")
    torles = _elem(window, "placesMarkerEraseButton")
    assert _var(qt_app, buborek.isVisible)
    assert szamlalo.property("text") == "6 photos here:"
    assert keres.property("text") == "Search for these photos in Picasa"
    assert torles.property("text") == "Erase location info"

    kepmentes = window.grabWindow()
    assert not kepmentes.isNull()
    assert kepmentes.save(str(tmp_path / "hely-jelolo-buborek-4582.png"))

    _kattint(window, keres, qt_app)
    assert _var(
        qt_app,
        lambda: _sorok(window.property("selectedIndexes")) == sorok,
    )

    _kattint(window, kep, qt_app)
    assert _var(qt_app, buborek.isVisible)
    _kattint(window, torles, qt_app)
    assert _var(
        qt_app,
        lambda: window.findChild(QObject, "panelClearGeotagConfirm") is not None,
    ), f"törlési párbeszéd nem épült fel; geotagged={controller.geotaggedCount(sorok)}"
    megerosites = _elem(window, "panelClearGeotagConfirm")
    assert bool(megerosites.property("visible"))
    igen = _elem(window, "panelClearGeotagYesButton")
    _kattint(window, igen, qt_app)

    assert _var(qt_app, lambda: len(controller.geoMarkers) == 0)
    ini = konyvtar / ".picasa.ini"
    assert "geotag=" not in ini.read_text(encoding="utf-8")

    controller.setGeotagRows([0], 47.5, 19.05)
    assert _var(qt_app, lambda: len(controller.geoMarkers) == 1)
    jelolo.setProperty(
        "markerData",
        {"rows": [0], "thumbUrl": controller.geoMarkers[0]["thumbUrl"]},
    )
    egy_kep = _elem(window, "placesMarkerImage")
    _kattint(window, egy_kep, qt_app)
    egy_foto_felirat = _elem(window, "placesMarkerPhotosHere")
    assert _var(qt_app, lambda: egy_foto_felirat.property("text") == "1 photo here:")
