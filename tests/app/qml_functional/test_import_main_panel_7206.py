"""#7206: a forrásimport a főablak panelje, nagy képelőnézettel."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, QUrl, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from support.jpeg_factory import make_minta_jpeg
from support.varakozas import var_feltetelre


def _bejara(item):
    yield item
    if hasattr(item, "childItems"):
        for child in item.childItems():
            yield from _bejara(child)


def _keres(root, name: str):
    found = root.findChild(QObject, name)
    if found is None:
        found = next((item for item in _bejara(root) if item.objectName() == name), None)
    return found


def _elem(root, name: str):
    found = _keres(root, name)
    assert found is not None, f"{name} nem található"
    return found


def _kattint(window: QQuickWindow, item, qt_app) -> None:
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _egyszinu_png(path: Path, color: QColor) -> None:
    image = QImage(320, 240, QImage.Format.Format_RGB32)
    image.fill(color)
    assert image.save(str(path), "PNG")


def _import_panel(window, qt_app, height_delta: int = 0):
    window.resize(1280, 800)
    window.show()
    qt_app.processEvents()
    _kattint(window, _elem(window, "toolbarImportButton"), qt_app)
    assert var_feltetelre(
        qt_app,
        lambda: window.findChild(QObject, "importSourceDialog") is not None,
        5,
    ), "az Import belépő nem nyitotta meg a panelt"
    window.setProperty("height", 800 + height_delta)
    qt_app.processEvents()
    return _elem(window, "importSourceDialog")


def test_import_panel_is_embedded_and_large_preview_tracks_the_clicked_photo(
    qml_app, qt_app, tmp_path
):
    window, _controller, _engine = qml_app
    panel = _import_panel(window, qt_app)

    assert isinstance(panel, QQuickItem), "az importfelület nem főablak-panel"
    assert panel.window() == window, "az importfelület külön ablakban nyílt meg"

    source = tmp_path / "forras"
    source.mkdir()
    first = source / "elso.png"
    second = source / "masodik.png"
    elso_szin = QColor(220, 35, 45)
    masodik_szin = QColor(25, 190, 75)
    _egyszinu_png(first, elso_szin)
    _egyszinu_png(second, masodik_szin)
    panel.setProperty("sourceFolder", str(source))
    panel.setProperty("destFolder", str(tmp_path / "cel"))
    assert QMetaObject.invokeMethod(
        panel, "scanCurrentSource", Qt.ConnectionType.DirectConnection
    )
    assert var_feltetelre(
        qt_app,
        lambda: not panel.property("scanning")
        and panel.property("previewCount") == 2,
        10,
    ), "a próbaképek beolvasása nem fejeződött be"

    grid = _elem(panel, "importSourcePreviewGrid")
    delegates_megvannak = var_feltetelre(
        qt_app, lambda: _keres(panel, "importSourceThumb:1") is not None, 5
    )
    assert delegates_megvannak, (
        "az előnézeti rács delegáltja nem épült fel: "
        f"count={grid.property('count')}, "
        f"méret={grid.width():.0f}x{grid.height():.0f}"
    )
    thumbnail = _elem(panel, "importSourceThumb:1")
    _kattint(window, thumbnail, qt_app)
    assert panel.property("selectedPreviewIndex") == 1
    preview = _elem(panel, "importSourceLargePreviewImage")
    assert preview.property("visible") is True
    assert Path(QUrl(preview.property("source")).toLocalFile()) == second
    assert Path(QUrl(preview.property("source")).toLocalFile()) != first

    def szin_egyezik(actual):
        return all(
            abs(got - expected) <= 3
            for got, expected in zip(
                (actual.red(), actual.green(), actual.blue()),
                (masodik_szin.red(), masodik_szin.green(), masodik_szin.blue()),
                strict=True,
            )
        )

    pane = _elem(panel, "importSourceLargePreviewPane")
    for height_delta in (-5, 0, 5):
        window.setProperty("height", 800 + height_delta)

        def elonezet_kozep_szin():
            pont = preview.mapToScene(
                QPointF(preview.width() / 2, preview.height() / 2)
            )
            return window.grabWindow().pixelColor(round(pont.x()), round(pont.y()))

        assert var_feltetelre(
            qt_app,
            lambda: pane.height() >= panel.height() * 0.5
            and szin_egyezik(elonezet_kozep_szin()),
            5,
        ), (
            f"{800 + height_delta} px-es ablaknál az előnézet nem tölti ki "
            "a panel legalább felét, vagy a kijelölt kép képpontja nem látszik"
        )
        if height_delta == 0:
            ablak_kep = window.grabWindow()
            kep_utvonal = (
                Path(__file__).resolve().parents[3] / ".codex-kepernyokep-7206.png"
            )
            assert ablak_kep.size().width() == 1280 and ablak_kep.size().height() == 800
            assert ablak_kep.save(str(kep_utvonal), "PNG"), (
                f"a képernyőkép nem menthető: {kep_utvonal}"
            )


def test_main_window_close_prompts_before_importing_scanned_photos(
    qml_app, qt_app, tmp_path
):
    window, _controller, _engine = qml_app
    panel = _import_panel(window, qt_app)
    source = tmp_path / "forras"
    source.mkdir()
    make_minta_jpeg(source / "kep.jpg")
    (tmp_path / "cel").mkdir()
    panel.setProperty("sourceFolder", str(source))
    panel.setProperty("destFolder", str(tmp_path / "cel"))
    panel.setProperty("namingMode", "date")
    assert QMetaObject.invokeMethod(
        panel, "scanCurrentSource", Qt.ConnectionType.DirectConnection
    )
    assert var_feltetelre(
        qt_app,
        lambda: not panel.property("scanning")
        and panel.property("previewCount") == 1
        and panel.property("canImportAll"),
        10,
    ), "a próbakép nem vált importálhatóvá"

    window.close()

    assert window.isVisible(), "a főablak kérdés nélkül bezárult"
    confirm = _elem(window, "importBeforeCloseDialog")
    assert confirm.property("visible") is True
    assert confirm.property("message") == "Import images before closing PicasaPy?"
    assert confirm.property("yesText") == "Import Images"
    assert confirm.property("noText") == "Quit"
