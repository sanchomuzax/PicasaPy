"""A #864 hisztogram-algoritmus KIRAJZOLT, képpontos regressziótesztje.

Nem belső property-t vagy a rajzolás elindulását ellenőrizzük: valódi
``QQuickView`` képernyőképéből olvassuk vissza azt a négy képpontszínt,
amelyet a visszafejtett ``+85`` RGBA-keverés előír.
"""

from __future__ import annotations

import math

import pytest

from PySide6.QtCore import QObject, QPointF, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

_KEEPALIVE: list[object] = []


def _histogram_box(qt_app, histogram=None) -> tuple[QQuickView, QQuickItem]:
    """A valódi ``HistogramBox`` 238 × 144-es ablakban kirajzolva."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(
        view.engine(),
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "HistogramBox.qml")
        ),
    )
    assert [error.toString() for error in component.errors()] == []

    # Alulról 20 px-ig R+G+B, 40 px-ig R+G, 60 px-ig csak R.
    # Minden bin azonos, így a 256→213 kicsinyítés vízszintesen homogén.
    if histogram is None:
        histogram = {
            "r": [60 / 70] * 256,
            "g": [40 / 70] * 256,
            "b": [20 / 70] * 256,
        }
    root = component.createWithInitialProperties(
        {"histogramData": histogram, "cameraSummary": "Gép\t1/125 s"}
    )
    assert root is not None
    root.setWidth(238)
    root.setHeight(144)
    root.setParentItem(view.contentItem())
    view.resize(238, 144)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    for _ in range(5):
        qt_app.processEvents()
        QTest.qWait(20)

    _KEEPALIVE.extend((view, root, component))
    return view, root


def _histogram_bitmap(qt_app) -> tuple[QQuickView, QQuickItem]:
    """A 256 × 70-es belső kép önállóan, fehér háttér előtt."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.setColor(QColor("white"))
    component = QQmlComponent(
        view.engine(),
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "HistogramBitmap.qml")
        ),
    )
    assert [error.toString() for error in component.errors()] == []
    histogram = {
        "r": [60 / 70] * 256,
        "g": [40 / 70] * 256,
        "b": [20 / 70] * 256,
    }
    root = component.createWithInitialProperties({"histogramData": histogram})
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(256, 70)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    for _ in range(5):
        qt_app.processEvents()
        QTest.qWait(20)
    _KEEPALIVE.extend((view, root, component))
    return view, root


def _pixel_at_fraction_from_bottom(
    image, plot: QQuickItem, fraction: float
) -> QColor:
    """A rajzterület közepén, az aljától mért aránynál vett képpont."""
    point = plot.mapToScene(
        QPointF(plot.width() / 2, plot.height() * (1.0 - fraction))
    ).toPoint()
    return image.pixelColor(point.x(), point.y())


def _assert_rgb(actual: QColor, expected: str) -> None:
    """Legfeljebb egy szintnyi renderelői kerekítést enged."""
    target = QColor(expected)
    assert max(
        abs(actual.red() - target.red()),
        abs(actual.green() - target.green()),
        abs(actual.blue() - target.blue()),
    ) <= 1, f"várt {target.name()}, kapott {actual.name()}"


def _valtozo_binek() -> tuple[dict[str, list[float]], dict[str, list[int]]]:
    """Minden binben eltérő, egész belső magasságú tesztmintát ad."""
    heights = {
        "r": [(index * 13 + 3) % 71 for index in range(256)],
        "g": [(index * 29 + 11) % 71 for index in range(256)],
        "b": [(index * 47 + 23) % 71 for index in range(256)],
    }
    return (
        {
            channel: [height / 70 for height in channel_heights]
            for channel, channel_heights in heights.items()
        },
        heights,
    )


def _vart_kijelzo_szin(
    heights: dict[str, list[int]], x: int, y: int
) -> QColor:
    """Független orákulum a 256 × 70 → 213 × 59 legközelebbi mintához."""
    # A legközelebbi texel középpontos leképezése; pontos félúton a kisebb
    # index nyer, ezért ``ceil(...)-1`` és nem a Python bankárkerekítése.
    source_x = min(255, math.ceil((x + 0.5) * 256 / 213) - 1)
    source_y = min(69, math.ceil((y + 0.5) * 70 / 59) - 1)
    bottom_y = 69 - source_y
    active = tuple(heights[channel][source_x] > bottom_y for channel in "rgb")
    count = sum(active)
    # A bináris +85 premultiplied-alfa pufferét fehér háttérre kompozitáljuk.
    background = 255 - 85 * count
    return QColor(*(background + 85 * int(enabled) for enabled in active))


def test_additive_rgba_mix_is_visible_in_rendered_pixels(qt_app):
    """A +85-ös szorzott-alfa keverés négy tartománya képpontos."""
    view, root = _histogram_box(qt_app)
    plot = root.findChild(QObject, "histogramPlot")
    assert isinstance(plot, QQuickItem)
    image = view.grabWindow()

    # A színek a nulláról induló premultiplied ARGB-puffer fehér háttérre
    # kompozitált értékei: 3 csatorna #555, 2 csatorna #aaaa55,
    # 1 csatorna #ffaaaa, majd az érintetlen fehér háttér.
    for fraction, expected in (
        (10 / 70, "#555555"),
        (30 / 70, "#aaaa55"),
        (50 / 70, "#ffaaaa"),
        (65 / 70, "#ffffff"),
    ):
        _assert_rgb(_pixel_at_fraction_from_bottom(image, plot, fraction), expected)


def test_internal_bitmap_matches_binary_spec_pixel_for_pixel(qt_app):
    """A teljes belső kép egyezik a binárisból levezetett referenciával."""
    view, _ = _histogram_bitmap(qt_app)
    image = view.grabWindow()

    # A várt kép nem a termékkód képletét hívja: közvetlenül a visszafejtett
    # +85 RGBA-konstansok fehér háttérre kompozitált eredményét rögzíti.
    expected_rows = (
        (range(0, 10), "#ffffff"),
        (range(10, 30), "#ffaaaa"),
        (range(30, 50), "#aaaa55"),
        (range(50, 70), "#555555"),
    )
    for rows, expected in expected_rows:
        for y in rows:
            for x in range(256):
                _assert_rgb(image.pixelColor(x, y), expected)


def test_internal_and_display_geometry_is_exact(qt_app):
    """A 256 × 70-es kép a 213 × 59-es rajzterületre kerül."""
    _, root = _histogram_box(qt_app)
    plot = root.findChild(QObject, "histogramPlot")
    bitmap = root.findChild(QObject, "histogramBitmap")
    assert isinstance(plot, QQuickItem)
    assert isinstance(bitmap, QQuickItem)
    assert (plot.width(), plot.height()) == (213, 59)
    assert (bitmap.width(), bitmap.height()) == (256, 70)


def test_final_213x59_output_scales_every_varying_bin(qt_app):
    """A végső plot minden képpontja független skálázási orákulumot követ."""
    histogram, heights = _valtozo_binek()
    view, root = _histogram_box(qt_app, histogram)
    plot = root.findChild(QObject, "histogramPlot")
    assert isinstance(plot, QQuickItem)
    image = view.grabWindow()
    origin = plot.mapToScene(QPointF(0, 0))

    mismatches: list[str] = []
    for y in range(59):
        for x in range(213):
            actual = image.pixelColor(round(origin.x() + x), round(origin.y() + y))
            expected = _vart_kijelzo_szin(heights, x, y)
            if max(
                abs(actual.red() - expected.red()),
                abs(actual.green() - expected.green()),
                abs(actual.blue() - expected.blue()),
            ) > 1:
                mismatches.append(
                    f"({x}, {y}): várt {expected.name()}, kapott {actual.name()}"
                )
    assert not mismatches, (
        f"A 213 × 59-es kirajzolás eltér (origó: {origin.x()}, {origin.y()}):\n"
        + "\n".join(mismatches[:20])
    )


def test_real_photo_viewer_histogram_panel_geometry(qml_app, qt_app):
    """A Mainből nyitott PhotoViewer lebegő paneljének éles geometriája pontos."""
    window, _, _ = qml_app
    window.setProperty("viewerOpen", True)
    for _ in range(5):
        qt_app.processEvents()
        QTest.qWait(20)

    viewer = window.findChild(QObject, "photoViewer")
    drawer = window.findChild(QObject, "viewerLeftDrawer")
    box = window.findChild(QObject, "viewerHistogramBox")
    title = window.findChild(QObject, "histogramTitle")
    assert all(isinstance(item, QQuickItem) for item in (viewer, drawer, box, title))

    assert (box.width(), box.height()) == (238, 144)
    drawer_right = drawer.mapToScene(drawer.boundingRect().topRight()).x()
    box_left = box.mapToScene(box.boundingRect().topLeft()).x()
    viewer_bottom = viewer.mapToScene(viewer.boundingRect().bottomLeft()).y()
    box_bottom = box.mapToScene(box.boundingRect().bottomLeft()).y()
    assert box_left == pytest.approx(drawer_right + 20, abs=0.5)
    assert box_bottom == pytest.approx(viewer_bottom - 95, abs=0.5)
    assert title.property("font").pointSizeF() == pytest.approx(14)
