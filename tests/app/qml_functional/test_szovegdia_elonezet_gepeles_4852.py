"""A szöveges dia szerkesztése után az előnézet gyorsan frissül (#4852)."""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest


def _elem(window, name):
    element = window.findChild(QObject, name)
    assert element is not None, f"{name} nem található"
    return element


def _wait(qt_app, condition, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(condition())


def _click(window, qt_app, item, x_ratio=0.5):
    assert item.property("visible"), f"{item.objectName()} nem látható"
    point = item.mapToScene(
        QPointF(item.property("width") * x_ratio, item.property("height") / 2)
    ).toPoint()
    QTest.mouseClick(item.window() or window, Qt.MouseButton.LeftButton, pos=point)
    qt_app.processEvents()


def _open_movie_dialog(window, qt_app, height):
    window.resize(1280, height)
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    _click(window, qt_app, _elem(window, "trayMovieButton"))
    dialog = _elem(window, "movieDialog")
    assert _wait(qt_app, lambda: dialog.property("visible"))
    return dialog



def test_a_gepeles_billentyuleutesenkent_egy_kerest_indit_es_gyorsan_frissul(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    dialog = _open_movie_dialog(window, qt_app, 800)
    provider = controller.movie_transition_preview_provider
    kerelmek: list[str] = []
    eredeti = provider.request_transition

    def szamlalo(*args, **kwargs):
        kerelmek.append(args[10])  # incoming_slide_json
        return eredeti(*args, **kwargs)

    provider.request_transition = szamlalo
    try:
        dialog.setProperty("movieClipSources", [])
        _click(window, qt_app, _elem(window, "movieTabSlide"))
        _click(window, qt_app, _elem(window, "movieInsertSlideButton"))
        title_dialog = _elem(window, "movieTitleDialog")
        assert _wait(qt_app, lambda: title_dialog.property("visible"))
        _elem(window, "titledialog/captiontext").setProperty("text", "4852 dia")
        qt_app.processEvents()
        _click(window, qt_app, _elem(window, "titledialog/add"))
        assert _wait(qt_app, lambda: not title_dialog.property("visible"))
        slide_list = _elem(window, "movieSlideList")
        assert _wait(qt_app, lambda: int(slide_list.property("count")) == 1)
        click_y = float(slide_list.property("contentHeight")) / 2
        point = slide_list.mapToScene(
            QPointF(float(slide_list.property("width")) / 2, click_y)
        ).toPoint()
        QTest.mouseClick(slide_list.window(), Qt.MouseButton.LeftButton, pos=point)
        assert _wait(
            qt_app,
            lambda: int(dialog.property("previewDisplayedGeneration"))
            >= int(dialog.property("previewLatestRequestGeneration")),
            timeout=10.0,
        )

        field = _elem(window, "movieSlideText")
        point = field.mapToScene(
            QPointF(field.property("width") / 2, field.property("height") / 2)
        ).toPoint()
        QTest.mouseClick(field.window(), Qt.MouseButton.LeftButton, pos=point)
        assert _wait(qt_app, lambda: field.property("activeFocus"))
        QTest.keyClick(field.window(), Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        QTest.qWait(300)
        qt_app.processEvents()
        kerelmek.clear()

        # Egyetlen billentyűleütés: legfeljebb egy előnézet-kérés.
        QTest.keyClick(field.window(), Qt.Key.Key_X)
        assert _wait(qt_app, lambda: len(kerelmek) >= 1, timeout=2.0)
        QTest.qWait(400)
        qt_app.processEvents()
        assert len(kerelmek) == 1, f"egy leütés {len(kerelmek)} kérést indított"
        assert field.property("text") == "x"

        # Gépelés után a megjelenített generáció <= 1 s-on belül friss.
        kezdet = time.monotonic()
        QTest.keyClick(field.window(), Qt.Key.Key_Y)
        assert _wait(
            qt_app,
            lambda: len(kerelmek) >= 2
            and int(dialog.property("previewDisplayedGeneration"))
            >= int(dialog.property("previewLatestRequestGeneration")),
            timeout=5.0,
        )
        eltelt = time.monotonic() - kezdet
        assert eltelt <= 1.0, f"a frissítés {eltelt:.2f} s volt"
        assert field.property("text") == "xy"
    finally:
        provider.request_transition = eredeti
        dialog.close()
        qt_app.processEvents()
