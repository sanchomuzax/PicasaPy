"""#5762: a fájllistás néző a gyorsnézet vezérlőit mutatja."""

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest

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
        "viewerQuickLaunchPicasaButton",
        "viewerQuickPrevButton",
        "viewerQuickPlayButton",
        "viewerQuickNextButton",
        "viewerQuickUploadButton",
        "viewerQuickRotateLeftButton",
        "viewerQuickRotateRightButton",
        "viewerQuickStarButton",
        "viewerQuickMoreOptionsButton",
    )
    base_height = int(window.height())
    for delta in (-5, 0, 5):
        height = base_height + delta
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

    quick_toolbar = window.findChild(QObject, "viewerQuickToolbar")
    toolbar_order = (
        "viewerQuickZoomInButton",
        "viewerQuickZoomOutButton",
        "viewerQuickZoomActualButton",
        "viewerQuickLaunchPicasaButton",
        "viewerQuickPrevButton",
        "viewerQuickPlayButton",
        "viewerQuickNextButton",
        "viewerQuickUploadButton",
        "viewerQuickRotateLeftButton",
        "viewerQuickRotateRightButton",
        "viewerQuickStarButton",
        "viewerQuickMoreOptionsButton",
    )
    toolbar_x = [
        window.findChild(QObject, name).mapToItem(quick_toolbar, 0, 0).x()
        for name in toolbar_order
    ]
    assert all(
        left < right for left, right in zip(toolbar_x, toolbar_x[1:], strict=False)
    )

    assert controller.photos.folderNeighbor(0, 1) == 1
    assert controller.photos.folderNeighbor(1, -1) == 0


def test_quick_view_elrejti_a_konyvtari_feluletet_es_launch_picasa_visszater(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    image_path = tmp_path / "quick.png"
    _kep(image_path, "green")
    assert controller.begin_quick_view([str(image_path)])
    assert controller.viewerFullscreenStartup is True

    window.startQuickViewer()
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    assert var_feltetelre(
        qt_app,
        lambda: viewer.property("visible") is True
        and viewer.property("currentIndex") == 0,
        5.0,
    )
    assert var_feltetelre(
        qt_app,
        lambda: window.visibility() == window.Visibility.FullScreen,
        5.0,
    )
    window.showNormal()
    assert var_feltetelre(
        qt_app,
        lambda: window.visibility() == window.Visibility.Windowed,
        5.0,
    )

    hidden_controls = (
        "viewerTopBar",
        "viewerLeftDrawer",
        "viewerEditorPanel",
        "viewerHistogramBox",
        "viewerPropertiesPanel",
        "viewerTagsPanelLoader",
        "viewerPlacesPanelLoader",
        "viewerPeoplePanelLoader",
        "viewerFacesBar",
        "captionBar",
        "captionToggleButton",
        "toggle_left_drawer",
        "mainToolbar",
        "mainSplit",
        "folderPane",
        "trayBar",
    )
    menu_bar = window.property("menuBar")
    assert menu_bar is not None
    assert menu_bar.isVisible() is False

    base_height = int(window.height())
    for height_delta in (-5, 0, 5):
        target_height = base_height + height_delta
        window.resize(window.width(), target_height)
        assert var_feltetelre(
            qt_app,
            lambda target=target_height: int(window.height()) == target,
            5.0,
        )
        for name in hidden_controls:
            control = window.findChild(QObject, name)
            assert control is not None, f"hiányzik a vizsgált elem: {name}"
            assert control.isVisible() is False, f"gyorsnézetben látszik: {name}"

        toolbar = window.findChild(QObject, "viewerQuickToolbar")
        assert toolbar is not None and toolbar.isVisible()
        frame = {
            "viewerQuickZoomInButton": (253, 744),
            "viewerQuickZoomOutButton": (283, 744),
            "viewerQuickZoomActualButton": (312, 744),
            "viewerQuickLaunchPicasaButton": (351, 744),
            "viewerQuickPrevButton": (473, 739),
            "viewerQuickPlayButton": (494, 733),
            "viewerQuickNextButton": (523, 738),
            "viewerQuickUploadButton": (555, 744),
            "viewerQuickRotateLeftButton": (639, 744),
            "viewerQuickRotateRightButton": (668, 744),
            "viewerQuickStarButton": (702, 744),
            "viewerQuickMoreOptionsButton": (737, 743),
        }
        for name, (frame_x, frame_y) in frame.items():
            control = window.findChild(QObject, name)
            assert control is not None, f"hiányzik a képkocka-vezérlő: {name}"
            assert control.isVisible(), f"gyorsnézetben rejtett vezérlő: {name}"
            actual = control.mapToItem(toolbar, 0, 0)
            expected_x = (toolbar.width() - 1024) / 2 + frame_x
            expected_y = toolbar.height() - 800 + frame_y
            assert abs(actual.x() - expected_x) <= 3, name
            assert abs(actual.y() - expected_y) <= 3, name

    launch = window.findChild(QObject, "viewerQuickLaunchPicasaButton")
    pont = launch.mapToScene(QPointF(launch.width() / 2, launch.height() / 2)).toPoint()
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont
    )
    assert var_feltetelre(
        qt_app,
        lambda: not window.property("viewerOpen")
        and not controller.quickViewActive,
        5.0,
    )
    assert menu_bar.isVisible() is True
    assert window.findChild(QObject, "mainToolbar").isVisible() is True
    assert window.findChild(QObject, "mainSplit").isVisible() is True
    assert window.findChild(QObject, "folderPane").isVisible() is True
    assert window.findChild(QObject, "trayBar").isVisible() is True


def test_kiadaskep_a_gyorsnezetrol(qml_app, qt_app, tmp_path):
    """Kiadáskép mintázatos képpel; csak `PICASAPY_KIADASKEP_MAPPA` mellett fut."""
    import os
    from pathlib import Path

    import pytest

    from support.jpeg_factory import make_minta_jpeg

    mappa = os.environ.get("PICASAPY_KIADASKEP_MAPPA")
    if not mappa:
        pytest.skip("kiadáskép csak kérésre készül")
    window, controller, _engine = qml_app
    kepek = tmp_path / "gyors"
    kepek.mkdir()
    utak = []
    for i in range(3):
        ut = kepek / f"minta_{i}.jpg"
        make_minta_jpeg(ut, size=(960, 640), seed=i + 3)
        utak.append(str(ut))
    assert controller.begin_quick_view(utak)
    viewer = window.findChild(QObject, "photoViewer")
    window.startQuickViewer()
    image = window.findChild(QObject, "viewerImage")
    assert var_feltetelre(
        qt_app,
        lambda: viewer.property("visible") is True
        and image.property("implicitWidth") > 0,
        5.0,
    )
    cel = Path(mappa) / "kiadaskep_5762.png"
    cel.parent.mkdir(parents=True, exist_ok=True)
    assert window.grabWindow().save(str(cel), "PNG")
