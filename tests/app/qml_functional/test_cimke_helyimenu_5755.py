"""A Címkék panel helyi menüje (#5755), valódi egérkattintásokkal."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtQml import QQmlExpression, qmlContext

from conftest import _build_qml_app
from picasapy.index import open_index
from picasapy.metadata.iptc_writer import write_iptc_keywords
from support.jpeg_factory import make_minta_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import MAPPA, elokeszit
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    gyerek,
    kattints,
    keres_vizualis,
    varj,
    vizualis_bejaras,
)

_TAG = "kirandulas"
_WINDOW_HEIGHT_OFFSETS = (-5, 0, 5)


def _keszits_konyvtarat(lib: Path) -> None:
    mappa = lib / MAPPA
    mappa.mkdir()
    for name, size, seed in (
        ("a_nagy.jpg", (640, 480), 1),
        ("b_kicsi.jpg", (40, 30), 2),
        ("c_kozepes.jpg", (200, 150), 3),
    ):
        make_minta_jpeg(mappa / name, size=size, seed=seed)
    write_iptc_keywords(mappa / "a_nagy.jpg", (_TAG,))


@pytest.fixture
def cimke_app(qt_app, tmp_path):
    app = _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )
    window, controller, engine = next(app)
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a menüsor nem épült fel"
    try:
        yield window, controller, engine
    finally:
        del menu_bar
        next(app, None)


def _wait_for_real_thumbnail(window, qt_app) -> None:
    def is_ready(image) -> bool:
        expression = QQmlExpression(qmlContext(image), image, "status === Image.Ready")
        value, error = expression.evaluate()
        assert not error, expression.error()
        return bool(value)

    def thumbnail_ready() -> bool:
        return any(
            item.objectName() == "thumbImage"
            and is_ready(item)
            and item.property("source")
            for item in vizualis_bejaras(window.contentItem())
        )

    assert var_feltetelre(
        qt_app, hibaturo_feltetel(thumbnail_ready), 10.0
    ), "a teszt valódi képe nem töltődött be a rácsba"


def _row_for(controller, name: str) -> int:
    return next(
        index
        for index, photo in enumerate(controller.photos.photos)
        if photo.name == name
    )


def _index_keywords(controller, name: str) -> tuple[str, ...]:
    with open_index(controller._db_path) as conn:
        row = conn.execute(
            "SELECT COALESCE(keywords_file, keywords_ini) "
            "FROM photos WHERE name = ?",
            (name,),
        ).fetchone()
    assert row is not None, f"{name} nincs az SQLite-indexben"
    return tuple(part.strip() for part in (row[0] or "").split(",") if part.strip())


def _tag_text_item(window):
    remove_button = keres_vizualis(window, f"tagRemove-{_TAG}")
    if remove_button is None:
        return None
    row = remove_button
    while row is not None and row.property("modelData") is None:
        row = row.parentItem()
    if row is None:
        return None
    return next(
        (
            item
            for item in vizualis_bejaras(row)
            if item.property("text") == _TAG
        ),
        None,
    )


def _open_tag_menu(window, qt_app):
    assert varj(qt_app, lambda: _tag_text_item(window) is not None), (
        "a címkesor nem jelent meg a Címkék panelen"
    )
    kattints(window, qt_app, _tag_text_item(window), gomb=Qt.MouseButton.RightButton)
    menu = gyerek(window, "tagContextMenu")
    assert varj(qt_app, lambda: menu.property("visible") is True), (
        "a címkesor jobbklikkje nem nyitotta meg a helyi menüt"
    )
    return menu


def _click_tag_command(window, qt_app, object_name: str) -> None:
    item = gyerek(window, object_name)
    assert varj(qt_app, lambda: item.isVisible()), f"{object_name} nem látszik"
    kattints(window, qt_app, item)


def _menu_texts(menu) -> list[str]:
    texts = []
    for index in range(int(menu.property("count") or 0)):
        expression = QQmlExpression(qmlContext(menu), menu, f"itemAt({index}).text")
        value, error = expression.evaluate()
        assert not error, expression.error()
        texts.append(str(value))
    return texts


def _show_tags_for_rows(window, qt_app, rows: list[int]) -> None:
    window.setProperty("activeDrawerTab", "tags")
    window.setProperty("selectedIndexes", rows)
    window.setProperty("selectedIndex", rows[0] if rows else -1)
    qt_app.processEvents()
    assert varj(qt_app, lambda: _tag_text_item(window) is not None), (
        "a címke nem jelent meg a kijelölt elemek Címkék paneljén"
    )


def _resize_for_layout(window, qt_app, delta: int) -> None:
    target_height = window.height() + delta
    window.resize(window.width(), target_height)
    qt_app.processEvents()
    assert varj(qt_app, lambda: window.height() == target_height), (
        f"az ablak magassága nem állt be: várt {target_height}, "
        f"kapott {window.height()}"
    )


@pytest.mark.parametrize("height_delta", _WINDOW_HEIGHT_OFFSETS)
def test_three_menu_commands_click_through_with_official_order_and_effects(
    cimke_app, qt_app, height_delta
):
    window, controller, _engine = cimke_app
    elokeszit(window, qt_app, controller)
    _wait_for_real_thumbnail(window, qt_app)
    _resize_for_layout(window, qt_app, height_delta)
    row0 = _row_for(controller, "a_nagy.jpg")
    row1 = _row_for(controller, "b_kicsi.jpg")
    _show_tags_for_rows(window, qt_app, [row0, row1])
    menu = _open_tag_menu(window, qt_app)

    assert _menu_texts(menu) == [
        "Remove this tag",
        "Search for items with this tag",
        "Add this tag to entire selection",
    ]

    screenshot = os.environ.get("PICASAPY_5755_SCREENSHOT")
    if screenshot and height_delta == 0:
        output = Path(screenshot)
        output.parent.mkdir(parents=True, exist_ok=True)
        image = window.grabWindow()
        assert not image.isNull(), "a Címkék menü kiadásképe üres"
        assert image.save(str(output), "PNG"), f"nem menthető a kiadáskép: {output}"

    _click_tag_command(window, qt_app, "tagMenuRemove")
    assert varj(
        qt_app,
        lambda: _TAG not in _index_keywords(controller, "a_nagy.jpg")
        and _TAG not in _index_keywords(controller, "b_kicsi.jpg"),
    ), "az eltávolítás nem törölte a címkét a kijelölt elemek indexéből"

    controller.addKeywordToRows([row0], _TAG)
    _show_tags_for_rows(window, qt_app, [row0])
    _open_tag_menu(window, qt_app)

    _click_tag_command(window, qt_app, "tagMenuFindTagged")
    search_field = gyerek(window, "searchField")
    assert varj(
        qt_app,
        lambda: search_field.property("text") == _TAG
        and controller.searchQuery == _TAG,
    ), "a címkekeresés nem állította be a keresőmezőt és a keresőkifejezést"

    search_field.setProperty("text", "")
    controller.search("")
    _show_tags_for_rows(window, qt_app, [row0, row1])
    _open_tag_menu(window, qt_app)

    _click_tag_command(window, qt_app, "tagMenuAddToSelection")
    assert varj(
        qt_app, lambda: _TAG in _index_keywords(controller, "b_kicsi.jpg")
    ), "a teljes kijelölésre címkéző menüelem nem írta az indexbe a címkét"
