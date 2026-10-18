"""A Név nélküliek fejlécének betűmérete és tiltott felirata (#5328)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QPointF, Property, QUrl, Slot
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from tests.support.varakozas import var_feltetelre

_KEEPALIVE: list = []


class _FaceScanStub(QObject):
    unnamedCount = Property(int, lambda _self: 6, constant=True)  # noqa: N815

    @Slot(result=bool)
    def unnamedWelcomeHasBeenShown(self):  # noqa: N802
        return True

    @Slot(bool, bool, result="QVariantList")
    def unnamedGroups(self, group_by_face, expand_groups):  # noqa: N802
        return []

    @Slot(result="QVariantList")
    def ignoredGroups(self):  # noqa: N802
        return []


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _item(window: QQuickWindow, object_name: str) -> QQuickItem:
    matches = [
        child for child in _walk(window.contentItem())
        if child.objectName() == object_name
    ]
    assert len(matches) == 1, f"{object_name}: {len(matches)} elem"
    return matches[0]


def _capture(window: QQuickWindow):
    image = window.grabWindow()
    assert not image.isNull()
    return image


def _inner_min_luminance(image, item: QQuickItem) -> int:
    """A gomb belső területének legsötétebb pixele, keret nélkül."""
    top_left = item.mapToScene(QPointF(0, 0))
    scale = image.devicePixelRatio()
    left = round((top_left.x() + 8) * scale)
    top = round((top_left.y() + 4) * scale)
    right = round((top_left.x() + item.width() - 8) * scale)
    bottom = round((top_left.y() + item.height() - 4) * scale)
    return min(
        image.pixelColor(x, y).lightness()
        for y in range(top, bottom)
        for x in range(left, right)
    )


def _effective_label_alpha(button: QQuickItem) -> float:
    """A PicasaButton opacityja a feliratot is azonos arányban halványítja."""
    ink = button.property("inkColor")
    assert ink.isValid(), f"{button.objectName()}: nincs PicasaButton feliratszín"
    return ink.alphaF() * button.opacity()


def test_fejlec_betumeret_es_letiltott_felirat_renderelve(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    face_scan = _FaceScanStub()
    component = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "UnnamedFacesView.qml")
        ),
    )
    view = component.createWithInitialProperties(
        {"faceScanController": face_scan}
    )
    assert [error.toString() for error in component.errors()] == []
    assert view is not None
    QQmlEngine.setObjectOwnership(view, QQmlEngine.ObjectOwnership.CppOwnership)

    window = QQuickWindow()
    window.resize(1280, 1024)
    window.setColor(QColor("#eaeaea"))
    view.setParentItem(window.contentItem())
    view.setProperty("width", 1280)
    view.setProperty("height", 1024)
    view.setProperty("grouped", False)
    window.show()
    _KEEPALIVE.extend([engine, component, view, window, face_scan])

    assert var_feltetelre(
        qt_app,
        lambda: window.isExposed()
        and _item(window, "ignoreFacesButton").width() > 0
        and _item(window, "unnamedAlbumFaceCount").isVisible(),
        3.0,
    )

    ignore = _item(window, "ignoreFacesButton")
    show_ignored = _item(window, "unknownfaceheaderpanel/showignored")
    assert ignore.property("enabled") is False
    assert show_ignored.property("enabled") is False
    disabled_label_alpha = {
        "Ignore Selected": _effective_label_alpha(ignore),
        "Show ignored faces": _effective_label_alpha(show_ignored),
    }

    disabled_image = _capture(window)
    output = Path(__file__).resolve().parents[3] / ".bt" / "kep_5328.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    assert disabled_image.save(str(output))

    view.setProperty("selectedCount", 1)
    view.setProperty("hasIgnoredFaces", True)
    assert var_feltetelre(
        qt_app,
        lambda: ignore.property("enabled") is True
        and show_ignored.property("enabled") is True,
        3.0,
    )
    enabled_image = _capture(window)

    # Csak a vizuális kontrasztot mérjük; a betűk befoglaló mérete
    # platformfüggő, ezért azt a QML font.pixelSize tulajdonsága őrzi.
    for button, name in ((ignore, "Ignore Selected"),
                         (show_ignored, "Show ignored faces")):
        assert button.property("text") == name
        assert disabled_label_alpha[name] < _effective_label_alpha(button)
        disabled_luma = _inner_min_luminance(disabled_image, button)
        enabled_luma = _inner_min_luminance(enabled_image, button)
        assert disabled_luma > enabled_luma + 10, (
            f"{name}: tiltott={disabled_luma}, engedélyezett={enabled_luma}"
        )

    # A mért értéket a tényleges QFont pixelSize propertykkel vetjük össze;
    # a renderelt betűk befoglaló mérete gépenként eltérhet.
    for name in (
        "clusterToggleButton",
        "unknownfaceheaderpanel/showignored",
        "unknownfaceheaderpanel/showunknown",
        "ignoreFacesButton",
    ):
        item = _item(window, name)
        font = item.property("font")
        assert font.pixelSize() == 12, f"{name}: {font.pixelSize()} px"

    count_font = _item(window, "unnamedAlbumFaceCount").property("font")
    assert count_font.pixelSize() == 12, f"N Face(s): {count_font.pixelSize()} px"

    window.close()
