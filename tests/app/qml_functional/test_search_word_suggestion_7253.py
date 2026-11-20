"""#7253: javaslatlista szósorára kattintva a mezőbe a szó és egy szóköz kerül, és a keresés lefut."""

from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from tests.support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre
from tests.support.javaslatsor_kattintas import kattints_a_javaslatsorra


def _wait(qt_app, predicate, timeout: float = 10.0) -> bool:
    return var_feltetelre(qt_app, predicate, timeout)


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _value(obj, name):
    value = obj.property(name)
    return value.toVariant() if hasattr(value, "toVariant") else value


def _type_text(window, text: str) -> None:
    for character in text:
        modifier = (
            Qt.KeyboardModifier.ShiftModifier
            if character.isupper()
            else Qt.KeyboardModifier.NoModifier
        )
        QTest.keyClick(window, Qt.Key(ord(character.upper())), modifier)


def _click(window, item, qt_app) -> None:
    assert item is not None and item.isVisible()
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _javaslatsor(popup, nev):
    for row in _walk(popup):
        if row.objectName() != "suggestionRow" or not row.isVisible():
            continue
        if (_value(row, "modelData") or {}).get("name") == nev:
            return row
    return None


def _seed_zqai_sample(controller, tmp_path) -> None:
    root = tmp_path / "kepek"
    folder = root / "photos"
    folder.mkdir()

    # 3 kép zqai
    for i in (1, 2, 3):
        make_jpeg(folder / f"img_a_{i}.jpg", size=(64, 48))
    # 2 kép zqai1
    for i in (1, 2):
        make_jpeg(folder / f"img_b_{i}.jpg", size=(64, 48))
    # 1 kép zqai2
    make_jpeg(folder / "img_c_1.jpg", size=(64, 48))
    # 1 kép ZqKase
    make_jpeg(folder / "img_d_1.jpg", size=(64, 48))

    ini_lines = [
        "[img_a_1.jpg]\nkeywords=zqai\n",
        "[img_a_2.jpg]\nkeywords=zqai\n",
        "[img_a_3.jpg]\nkeywords=zqai\n",
        "[img_b_1.jpg]\nkeywords=zqai1\n",
        "[img_b_2.jpg]\nkeywords=zqai1\n",
        "[img_c_1.jpg]\nkeywords=zqai2\n",
        "[img_d_1.jpg]\nkeywords=ZqKase\n",
    ]
    (folder / ".picasa.ini").write_text("".join(ini_lines), encoding="utf-8")

    with open_index(controller._db_path) as conn:
        sync_tree(conn, root)
    controller._reload()


def test_search_word_suggestion_click_sets_field_with_space_and_runs_search(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    _seed_zqai_sample(controller, tmp_path)

    window.show()
    window.requestActivate()
    qt_app.processEvents()

    field = window.findChild(QObject, "searchField")
    popup = window.findChild(QObject, "searchSuggestions")
    assert field is not None and popup is not None

    # Fókusz a keresőmezőre és "zq" gépelése
    _click(window, field, qt_app)
    assert _wait(qt_app, lambda: field.property("activeFocus") is True)
    _type_text(window, "zq")

    def _zq_rows_ready():
        rows = _value(popup, "suggestions") or []
        return (
            popup.property("visible") is True
            and popup.property("query") == "zq"
            and len(rows) == 4
        )

    assert _wait(qt_app, _zq_rows_ready)
    suggestions = _value(popup, "suggestions")
    assert len(suggestions) == 4

    # Sorok ellenőrzése: zqai (3), zqai1 (2), zqkase (1), zqai2 (1)
    # A darabszámok csökkenő sorrendben állnak
    assert [s["name"] for s in suggestions[:2]] == ["zqai", "zqai1"]
    assert [s["count"] for s in suggestions[:2]] == [3, 2]
    assert {s["name"] for s in suggestions[2:]} == {"zqkase", "zqai2"}
    assert [s["count"] for s in suggestions[2:]] == [1, 1]

    # ZQK gépelése
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    _type_text(window, "ZQK")

    def _zqk_rows_ready():
        rows = _value(popup, "suggestions") or []
        return (
            popup.property("visible") is True
            and popup.property("query").casefold() == "zqk"
            and len(rows) == 1
        )

    assert _wait(qt_app, _zqk_rows_ready)
    suggestions_zqk = _value(popup, "suggestions")
    assert len(suggestions_zqk) == 1
    assert suggestions_zqk[0]["name"] == "zqkase"
    assert suggestions_zqk[0]["count"] == 1

    # zqkase sorra kattintás
    # #7324: a sort minden mintavételnél újra keressük, és csak akkor
    # kattintunk, ha a helye már nem mozog (a lista újraépülhet).
    kattints_a_javaslatsorra(
        window, popup,
        lambda: _javaslatsor(popup, "zqkase"), qt_app,
    )

    # A `searchActive` az első keresés óta igaz; a mező és a lekérdezés
    # új értéke jelzi, hogy a második kattintás feldolgozása is befejeződött.
    assert _wait(
        qt_app,
        lambda: field.property("text") == "zqkase "
        and controller.searchQuery == "zqkase",
    )
    assert field.property("text") == "zqkase "
    assert controller.searchQuery == "zqkase"
    assert controller.searchResultCount == 1
    assert not popup.property("visible") or len(_value(popup, "suggestions") or []) == 0

    # zqai sor ellenőrzése: újra "zq" gépelése
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    _type_text(window, "zq")
    assert _wait(qt_app, _zq_rows_ready)

    # #7324: a sort minden mintavételnél újra keressük, és csak akkor
    # kattintunk, ha a helye már nem mozog (a lista újraépülhet).
    kattints_a_javaslatsorra(
        window, popup,
        lambda: _javaslatsor(popup, "zqai"), qt_app,
    )

    # A korábbi searchActive állapot nem elég: az új mező- és lekérdezésértéket
    # várjuk meg, mielőtt a találatokat ellenőrizzük.
    assert _wait(
        qt_app,
        lambda: field.property("text") == "zqai "
        and controller.searchQuery == "zqai",
    )
    assert field.property("text") == "zqai "
    assert controller.searchQuery == "zqai"
    assert not popup.property("visible") or len(_value(popup, "suggestions") or []) == 0
