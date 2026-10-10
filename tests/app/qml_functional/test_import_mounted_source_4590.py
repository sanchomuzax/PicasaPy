"""A #4590 felkínált csatolt kártyát kattintással kiválaszt és importál."""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg


def _elem(root, name: str):
    result = root.findChild(QObject, name)
    assert result is not None, f"{name} nem található"
    return result


def _varj(qt_app, condition, message: str, seconds: float = 3.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return
        time.sleep(0.01)
    qt_app.processEvents()
    assert condition(), message


def _kattint(window, item, qt_app) -> None:
    assert item.isEnabled(), f"{item.objectName()} le van tiltva"
    assert item.width() > 0 and item.height() > 0, (
        f"{item.objectName()} nem kattintható"
    )
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _kattint_elso_legordulo_sorra(window, qt_app) -> None:
    deadline = time.monotonic() + 3.0
    row_list = None
    while time.monotonic() < deadline:
        qt_app.processEvents()
        row_list = next(
            (
                item
                for item in window.findChildren(QObject, "picasaComboList")
                if item.property("visible")
                and int(item.property("count")) > 0
                and float(item.property("contentHeight")) > 0
            ),
            None,
        )
        if row_list is not None:
            break
        time.sleep(0.01)
    assert row_list is not None, "a kártyaforrás legördülő sora nem épült fel"
    row_height = float(row_list.property("contentHeight")) / int(
        row_list.property("count")
    )
    center = row_list.mapToScene(QPointF(row_list.width() / 2, row_height / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def test_attached_card_can_be_selected_and_imported_at_nearby_window_heights(
    qml_app, qt_app, tmp_path, monkeypatch
):
    from picasapy.app import import_source_controller as module

    main_window, _app_controller, engine = qml_app
    controller = engine.rootContext().contextProperty("importSourceController")
    assert controller is not None

    source = tmp_path / "test-card"
    source.mkdir()
    make_jpeg(source / "photo.jpg", taken_at="2024:03:05 10:00:00")
    destination = tmp_path / "library"
    destination.mkdir()

    # A Qt storage volume is injected at the platform boundary; the selected
    # temporary card directory then exercises the real scan/copy pipeline.
    monkeypatch.setattr(
        module,
        "discover_mounted_sources",
        lambda: [{"path": str(source), "name": "Test Card"}],
        raising=False,
    )

    _kattint(main_window, _elem(main_window, "toolbarImportButton"), qt_app)
    _varj(
        qt_app,
        lambda: main_window.findChild(QObject, "importSourceDialog") is not None,
        "az Import gomb nem hozta létre a párbeszédet",
    )
    dialog = _elem(main_window, "importSourceDialog")
    _varj(qt_app, lambda: bool(dialog.property("visible")), "az importablak nem nyílt meg")
    original_height = float(dialog.property("height"))
    source_box = _elem(dialog, "importSourceMountedSourcesBox")
    scan_done = []
    controller.sourceScanFinished.connect(lambda *_args: scan_done.append(True))

    for height_delta in (-5, 0, 5):
        dialog.setProperty("height", original_height + height_delta)
        qt_app.processEvents()
        controller.refreshMountedSources()
        qt_app.processEvents()

        assert source_box.property("count") == 1
        model = source_box.property("model")
        if hasattr(model, "toVariant"):
            model = model.toVariant()
        assert "Test Card" in model[0]["label"]

        _kattint(dialog, source_box, qt_app)
        _kattint_elso_legordulo_sorra(dialog, qt_app)
        _varj(qt_app, lambda: bool(scan_done), "a kártya beolvasása nem fejeződött be")
        scan_done.clear()
        assert int(dialog.property("previewCount")) == 1

    dialog.setProperty("destFolder", str(destination))
    finished = []
    controller.importFinished.connect(lambda copied, failed: finished.append((copied, failed)))
    start_button = _elem(dialog, "importSourceStartButton")
    _kattint(dialog, start_button, qt_app)
    _varj(qt_app, lambda: bool(finished), "a kártyáról történő import nem fejeződött be")

    assert finished[-1] == (1, 0)
    assert (destination / "2024-03-05" / "photo.jpg").is_file()
    assert (source / "photo.jpg").is_file()
