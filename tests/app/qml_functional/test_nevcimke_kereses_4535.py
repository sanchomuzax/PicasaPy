"""Kattintásos arckeresés a mappa- és album-helyi menüből (#4535)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPointF, QSettings, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_jpeg


_TOKEN = "45354535453545354535453545354535"
_HEIGHT_OFFSETS = (-5, 0, 5)


class _ArcMintaDetektor:
    """Determinista arcot ad a helyi JPEG-mintához, YuNet-modell nélkül."""

    available = True

    def detect(self, _image):
        from picasapy.faces.detector import FaceDetection, FaceLandmarks

        landmarks = FaceLandmarks(
            right_eye=(10.0, 20.0),
            left_eye=(30.0, 20.0),
            nose=(20.0, 30.0),
            mouth_right=(15.0, 40.0),
            mouth_left=(25.0, 40.0),
        )
        return (
            FaceDetection(
                left=5, top=10, right=40, bottom=50, score=0.9,
                landmarks=landmarks,
            ),
        )


def _folder_sample(lib: Path) -> None:
    (lib / "celmappa").mkdir()
    (lib / "masikmappa").mkdir()
    make_jpeg(lib / "celmappa" / "cel.jpg", size=(320, 200))
    make_jpeg(lib / "masikmappa" / "masik.jpg", size=(320, 200))


def _album_sample(lib: Path) -> None:
    make_jpeg(lib / "cel.jpg", size=(320, 200))
    make_jpeg(lib / "masik.jpg", size=(320, 200))
    (lib / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\nname=Célalbum\ntoken={_TOKEN}\n"
        f"[cel.jpg]\nalbums={_TOKEN}\n",
        encoding="utf-8",
    )


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(feltetel())


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _click_menu_item(item, qt_app) -> None:
    assert item.property("visible") is True, f"{item.objectName()} nem látható"
    assert item.property("enabled") is True, f"{item.objectName()} le van tiltva"
    assert item.property("placeholder") is False, (
        f"{item.objectName()} továbbra is helyfoglaló"
    )
    ablak = item.window()
    kozep = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
    QTest.mouseMove(ablak, kozep, 10)
    qt_app.processEvents()
    QTest.mouseClick(
        ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kozep
    )
    qt_app.processEvents()


def _configure_scanner(engine, tmp_path):
    scanner = engine.rootContext().contextProperty("faceScanController")
    assert scanner is not None, "faceScanController nincs a QML-környezetben"
    scanner._detector = _ArcMintaDetektor()
    scanner._settings = QSettings(
        str(tmp_path / "face-settings.ini"), QSettings.Format.IniFormat
    )
    scanner.setSuggestionsEnabled(False)
    return scanner


def _click_and_wait(item, scanner, qt_app):
    finished = []

    def callback(found, scanned):
        finished.append((found, scanned))

    scanner.scanFinished.connect(callback)
    try:
        _click_menu_item(item, qt_app)
        assert _varj(qt_app, lambda: bool(finished)), "az arckeresés nem fejeződött be"
    finally:
        scanner.scanFinished.disconnect(callback)
    return finished[-1]


@pytest.mark.parametrize("height_offset", _HEIGHT_OFFSETS)
def test_mappa_menuje_csak_a_cel_mappaban_keres(qt_app, tmp_path, height_offset):
    gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_folder_sample)
    window, _controller, engine = next(gen)
    try:
        scanner = _configure_scanner(engine, tmp_path)
        pane = _child(window, "folderPane")
        base_height = window.height()
        window.setHeight(base_height + height_offset)
        assert _varj(qt_app, lambda: window.height() == base_height + height_offset), (
            f"a főablak magassága nem állt be ({height_offset:+} px)"
        )
        QMetaObject.invokeMethod(
            pane,
            "openFolderContextMenu",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", str(tmp_path / "kepek" / "celmappa")),
        )
        item = _child(window, "folderMenuAddNameTags")
        assert _varj(qt_app, lambda: item.property("visible") is True), (
            "a mappa helyi menüje nem nyílt meg"
        )

        result = _click_and_wait(item, scanner, qt_app)
        assert result == (1, 1), "a mappa keresése nem pontosan egy képet vizsgált"
        assert [Path(photo["path"]).name for photo in scanner.unnamedAlbum()] == [
            "cel.jpg"
        ], "a mappa keresése a másik mappa képét is feldolgozta"
    finally:
        gen.close()


@pytest.mark.parametrize("height_offset", _HEIGHT_OFFSETS)
def test_album_menuje_csak_az_album_tagkepein_keres(qt_app, tmp_path, height_offset):
    gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_album_sample)
    window, _controller, engine = next(gen)
    try:
        scanner = _configure_scanner(engine, tmp_path)
        pane = _child(window, "folderPane")
        base_height = window.height()
        window.setHeight(base_height + height_offset)
        assert _varj(qt_app, lambda: window.height() == base_height + height_offset), (
            f"a főablak magassága nem állt be ({height_offset:+} px)"
        )
        QMetaObject.invokeMethod(
            pane,
            "openAlbumContextMenu",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", _TOKEN),
            Q_ARG("QVariant", "Célalbum"),
        )
        item = _child(window, "albumMenuAddNameTags")
        assert _varj(qt_app, lambda: item.property("visible") is True), (
            "az album helyi menüje nem nyílt meg"
        )

        result = _click_and_wait(item, scanner, qt_app)
        assert result == (1, 1), "az album keresése nem pontosan egy képet vizsgált"
        assert [Path(photo["path"]).name for photo in scanner.unnamedAlbum()] == [
            "cel.jpg"
        ], "az album keresése a nem tag képet is feldolgozta"
    finally:
        gen.close()
