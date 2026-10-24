"""#5762: a fájllistás néző a gyorsnézet vezérlőit mutatja."""

from PySide6.QtCore import QObject
from PySide6.QtGui import QColor, QImage

from support.varakozas import var_feltetelre


def _kep(path, color):
    image = QImage(12, 8, QImage.Format.Format_ARGB32)
    image.fill(QColor(color))
    assert image.save(str(path))


def test_quick_view_megjeleniti_a_kijelolt_fajlsort_es_vezerloit(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    first_folder = tmp_path / "quick-one"
    second_folder = tmp_path / "quick-two"
    first_folder.mkdir()
    second_folder.mkdir()
    first = first_folder / "first.png"
    second = second_folder / "second.png"
    _kep(first, "red")
    _kep(second, "blue")

    assert controller.begin_quick_view([str(first), str(second)])
    assert controller.photos.rowCount() == 2
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    window.setProperty("viewerOpen", True)
    viewer.setProperty("currentIndex", 0)
    assert var_feltetelre(
        qt_app,
        lambda: viewer.property("visible")
        and viewer.property("currentIndex") == 0,
        5.0,
    )

    controls = (
        "viewerQuickZoomInButton",
        "viewerQuickZoomOutButton",
        "viewerQuickZoomActualButton",
        "viewerPrevButton",
        "viewerQuickPlayButton",
        "viewerNextButton",
        "viewerQuickUploadButton",
        "viewerQuickRotateLeftButton",
        "viewerQuickRotateRightButton",
        "viewerQuickStarButton",
        "viewerQuickMoreOptionsButton",
    )
    for delta in (-5, 0, 5):
        height = int(window.height()) + delta
        window.setHeight(height)
        assert var_feltetelre(
            qt_app, lambda target=height: int(window.height()) == target, 5.0
        ), f"a főablak nem vette fel a {height} px-es magasságot"
        for name in controls:
            control = window.findChild(QObject, name)
            assert control is not None, f"hiányzik a gyorsnézet vezérlője: {name}"
            assert control.property("visible") is True, (
                f"a gyorsnézetben nem látszik: {name}"
            )

    upload = window.findChild(QObject, "viewerQuickUploadButton")
    assert upload.property("enabled") is False

    top_bar = window.findChild(QObject, "viewerTopBar")
    toolbar_order = (
        "viewerQuickZoomInButton",
        "viewerQuickZoomOutButton",
        "viewerQuickZoomActualButton",
        "viewerBackButton",
        "viewerPrevButton",
        "viewerQuickPlayButton",
        "viewerNextButton",
        "viewerQuickUploadButton",
        "viewerQuickRotateLeftButton",
        "viewerQuickRotateRightButton",
        "viewerQuickStarButton",
        "viewerQuickMoreOptionsButton",
    )
    toolbar_x = [
        window.findChild(QObject, name).mapToItem(top_bar, 0, 0).x()
        for name in toolbar_order
    ]
    assert all(
        left < right for left, right in zip(toolbar_x, toolbar_x[1:], strict=False)
    )

    assert controller.photos.folderNeighbor(0, 1) == 1
    assert controller.photos.folderNeighbor(1, -1) == 0
