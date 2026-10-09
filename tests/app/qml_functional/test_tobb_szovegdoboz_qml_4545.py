"""Több szövegdoboz létrehozása és kattintásos kijelölése (#4545)."""

import time

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.ini.text_overlay import parse_text


def _var(qt_app, condition, message: str, seconds: float = 3.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return
        time.sleep(0.01)
    raise AssertionError(message)


def _element(window, name: str):
    item = window.findChild(QObject, name)
    assert item is not None, f"Nem található a felületi elem: {name}"
    return item


def _click(window, item, x: float | None = None, y: float | None = None) -> None:
    point = item.mapToScene(
        QPointF(
            item.width() / 2 if x is None else x,
            item.height() / 2 if y is None else y,
        )
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )


def _saved_blocks(photo):
    ini = photo.parent / ".picasa.ini"
    value = next(
        line.removeprefix("text=")
        for line in ini.read_text(encoding="utf-8").splitlines()
        if line.startswith("text=")
    )
    return parse_text(value).blocks


@pytest.mark.parametrize("window_height", [900, 895, 905])
def test_tobb_doboz_kattintasra_szerkesztheto_es_ini_round_trip(
    qml_app, qt_app, tmp_path, window_height
):
    window, _, engine = qml_app
    window.resize(1280, window_height)
    assert window.height() == window_height
    window.setProperty("viewerOpen", True)
    viewer = _element(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    panel = _element(window, "viewerEditorPanel")
    edit = engine.rootContext().contextProperty("editController")
    photo = tmp_path / "kepek" / "a.jpg"

    _var(
        qt_app,
        lambda: _element(window, "viewerImage")
        .property("source")
        .toString()
        .startswith("image://editpreview/"),
        "A szerkesztő képe nem épült fel",
    )
    panel.setProperty("textActive", True)
    field = _element(window, "textContentField")
    click_area = _element(window, "textClickArea")
    _var(qt_app, lambda: click_area.width() > 0, "A szövegkattintás területe üres")
    apply_button = _element(window, "textApplyButton")

    field.setProperty("text", "Első doboz")
    qt_app.processEvents()
    _click(window, click_area, click_area.width() * 0.2, click_area.height() * 0.3)
    _var(qt_app, lambda: edit.property("textHasPlacement"), "Az első hely nem rögzült")
    _click(window, apply_button)
    _var(qt_app, lambda: panel.property("textActive") is False, "Az első Apply nem zárt")

    panel.setProperty("textActive", True)
    _var(qt_app, lambda: field.property("text") == "Első doboz", "Az első doboz nem töltődött be")
    field.setProperty("text", "Második doboz")
    qt_app.processEvents()
    _click(window, click_area, click_area.width() * 0.72, click_area.height() * 0.68)
    _var(qt_app, lambda: edit.property("textHasPlacement"), "A második hely nem rögzült")
    _click(window, apply_button)
    _var(qt_app, lambda: panel.property("textActive") is False, "A második Apply nem zárt")
    assert [block.content for block in _saved_blocks(photo)] == [
        "Első doboz",
        "Második doboz",
    ]

    # Új szerkesztési munkamenet: a két blokk újra beolvasódik az ini-ből.
    edit.endEdit()
    edit.beginEdit("1", str(photo))
    panel.setProperty("textActive", True)
    _var(
        qt_app,
        lambda: len(edit.property("textOverlayItems")) == 2,
        "A két doboz nem töltődött vissza az ini-ből",
    )
    second_item = edit.property("textOverlayItems")[1]
    text_height = second_item["size"] * click_area.height() / 360
    _click(
        window,
        click_area,
        click_area.width() * second_item["x"],
        click_area.height() * second_item["y"] - text_height / 2,
    )
    _var(
        qt_app,
        lambda: field.property("text") == "Második doboz"
        and edit.property("textSelectedIndex") == 1,
        "A második doboz kattintással nem jelölődött ki",
    )

    field.setProperty("text", "Második módosítva")
    qt_app.processEvents()
    _click(window, apply_button)
    _var(qt_app, lambda: panel.property("textActive") is False, "A módosítás nem zárt")
    assert [block.content for block in _saved_blocks(photo)] == [
        "Első doboz",
        "Második módosítva",
    ]
