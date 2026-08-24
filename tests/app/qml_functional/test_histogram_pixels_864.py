"""A #864 hisztogram-algoritmus KIRAJZOLT, képpontos regressziótesztje.

Nem belső property-t vagy a rajzolás elindulását ellenőrizzük: valódi
``QQuickView`` képernyőképéből olvassuk vissza azt a négy képpontszínt,
amelyet a visszafejtett ``+85`` RGBA-keverés előír.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QPointF, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

_KEEPALIVE: list[object] = []


def _histogram_box(qt_app) -> tuple[QQuickView, QQuickItem]:
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
