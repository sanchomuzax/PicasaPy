"""A ritkán használt főablak-nézetek csak első megnyitáskor épülnek fel."""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from tests.support.varakozas import var_feltetelre


def _child(parent, name):
    return parent.findChild(QObject, name)


def _wait(qt_app, condition, message):
    assert var_feltetelre(qt_app, condition, 5.0), message


def test_a_fooldali_nezetek_az_elso_megnyitasig_nem_epulnek_fel(
    qml_app, qt_app
):
    window, _controller, _engine = qml_app
    qt_app.processEvents()

    for object_name, loader_name in (
        ("photoViewer", "photoViewerLoader"),
        ("timelineView", "timelineViewLoader"),
        ("slideshowView", "slideshowLoader"),
    ):
        assert _child(window, object_name) is None, (
            f"{object_name} már induláskor felépült"
        )
        loader = _child(window, loader_name)
        assert loader is not None, f"hiányzik a(z) {loader_name} betöltő"
        assert loader.property("active") is False, (
            f"a(z) {loader_name} induláskor aktív"
        )

    assert QMetaObject.invokeMethod(
        window,
        "openPhotoViewer",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 0),
    )
    _wait(qt_app, lambda: _child(window, "photoViewer") is not None,
          "a néző első megnyitásakor nem épült fel")
    viewer = _child(window, "photoViewer")
    _wait(qt_app, viewer.isVisible, "a felépült néző nem látszik")
    window.setProperty("viewerOpen", False)
    _wait(qt_app, lambda: viewer.isVisible() is False,
          "a néző bezárása után továbbra is látszik")
    assert _child(window, "photoViewer") is viewer, (
        "a néző bezárásakor megsemmisült, ezért elveszhet az állapota"
    )

    assert QMetaObject.invokeMethod(
        window, "toggleTimeline", Qt.ConnectionType.DirectConnection
    )
    _wait(qt_app, lambda: _child(window, "timelineView") is not None,
          "az Időrend első megnyitásakor nem épült fel")
    timeline = _child(window, "timelineView")
    _wait(qt_app, timeline.isVisible, "a felépült Időrend nem látszik")
    assert QMetaObject.invokeMethod(
        window, "toggleTimeline", Qt.ConnectionType.DirectConnection
    )
    _wait(qt_app, lambda: timeline.isVisible() is False,
          "az Időrend bezárása után továbbra is látszik")
    assert _child(window, "timelineView") is timeline, (
        "az Időrend bezárásakor megsemmisült"
    )

    QMetaObject.invokeMethod(
        window,
        "startSlideshow",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 0),
    )
    _wait(qt_app, lambda: _child(window, "slideshowView") is not None,
          "a vetítés első indításakor nem épült fel")
    slideshow = _child(window, "slideshowView")
    _wait(qt_app, slideshow.isVisible, "a felépült vetítés nem látszik")
    QMetaObject.invokeMethod(
        window, "exitSlideshow", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    assert _child(window, "slideshowView") is slideshow, (
        "a vetítés bezárásakor megsemmisült"
    )


def test_a_foto_helyi_menuje_csak_elso_megnyitaskor_epul_fel(
    qml_app, qt_app
):
    window, _controller, _engine = qml_app
    qt_app.processEvents()

    assert _child(window, "photoContextMenu") is None, (
        "a rács helyi menüje már induláskor felépült"
    )
    loader = _child(window, "photoContextMenuLoader")
    assert loader is not None, "hiányzik a photoContextMenuLoader"
    assert loader.property("active") is False, (
        "a photoContextMenuLoader induláskor aktív"
    )

    grid = _child(window, "photoGrid")
    assert grid is not None, "a fotórács nem jött létre"
    QMetaObject.invokeMethod(
        window,
        "openPhotoContextMenu",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 0),
        Q_ARG("QVariant", grid),
        Q_ARG("QVariant", 5),
        Q_ARG("QVariant", 5),
    )
    _wait(qt_app, lambda: _child(window, "photoContextMenu") is not None,
          "a fotó helyi menüje első megnyitásakor nem épült fel")
    menu = _child(window, "photoContextMenu")
    _wait(qt_app, lambda: menu.property("visible") is True,
          "a felépült fotó helyi menü nem nyílt meg")
    QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    assert _child(window, "photoContextMenu") is menu, (
        "a helyi menü bezárásakor megsemmisült"
    )
