"""A mappa húzásos áthelyezése és indexképeinek frissítése (#6845)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, QObject, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index
from picasapy.ini import load_document, parse_document, save_document
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre
from tests.app.qml_functional._fomenu_4420_menu import _megnyit, _menupont
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    gyerek,
    jobbklikk_mappan,
    kattints,
)


_MAGASSAG_ELTERESEK = (-5, 0, 5)
_FELIRAT = "A mappával együtt költöző felirat"


def _keszits_mappahuzas_konyvtarat(library: Path) -> None:
    make_jpeg(library / "a.jpg", size=(160, 120))
    make_jpeg(library / "b.jpg", size=(120, 90))

    source = library / "atmozgatando"
    target = library / "cel"
    source.mkdir()
    target.mkdir()
    make_jpeg(source / "mappakep.jpg", size=(80, 60))
    make_jpeg(target / "celkep.jpg", size=(80, 60))
    save_document(
        parse_document("").with_value("mappakep.jpg", "caption", _FELIRAT),
        source / ".picasa.ini",
    )


def _keszits_frissites_konyvtarat(library: Path) -> None:
    folder = library / "fotok"
    folder.mkdir()
    make_jpeg(folder / "a.jpg", size=(160, 120))
    make_jpeg(folder / "b.jpg", size=(120, 90))
    make_jpeg(folder / "c.jpg", size=(100, 80))
    save_document(
        parse_document("").with_value("a.jpg", "caption", "Változatlan felirat"),
        folder / ".picasa.ini",
    )


@pytest.fixture
def mappahuzas_app(qt_app, tmp_path, request):
    from conftest import _build_qml_app

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_mappahuzas_konyvtarat,
        keep_modul=request.module,
    )


@pytest.fixture
def frissites_app(qt_app, tmp_path, request):
    from conftest import _build_qml_app

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_frissites_konyvtarat,
        valodi_belyegkep=True,
        keep_modul=request.module,
    )


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _visual(window, name: str, *, predicate=None):
    for item in _walk(window.contentItem()):
        if item.objectName() == name and (predicate is None or predicate(item)):
            return item
    return None


def _mappa_sor(window, path: Path):
    return _visual(
        window,
        "folderRowMouse",
        predicate=lambda item: Path(str(item.property("folderPath"))) == path,
    )


def _ablakpont(window, item) -> QPoint:
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    return QPoint(round(point.x()), round(point.y()))


def _drag_attached(item):
    return next(
        child
        for child in item.children()
        if child.metaObject().className() == "QQuickDragAttached"
    )


def _valodi_mappahuzas(window, qt_app, source_mouse, drop_target) -> None:
    """A bal hasábon valódi egérhúzást végez, metódushívás nélkül."""
    source_row = source_mouse.parentItem()
    drag_proxy = next(
        item for item in _walk(source_row) if item.objectName() == "folderDragProxy"
    )
    drag = _drag_attached(drag_proxy)
    start = _ablakpont(window, source_mouse)
    end = _ablakpont(window, drop_target)
    QTest.mouseMove(window, start)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
    qt_app.processEvents()

    delta = end - start
    distance = max(abs(delta.x()), abs(delta.y()))
    steps = max(1, (distance + 3) // 4)
    for step in range(1, steps + 1):
        point = start + QPoint(
            round(delta.x() * step / steps), round(delta.y() * step / steps)
        )
        QTest.mouseMove(window, point, 1)
        qt_app.processEvents()

    assert drag.property("active") is True, (
        "a valódi egérhúzás nem indította el a mappa Drag forrását"
    )
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=end)
    qt_app.processEvents()


def _photo_paths(controller) -> list[Path]:
    return [
        Path(controller.photos.filePathAt(row))
        for row in range(controller.photos.rowCount())
    ]


def _selected_rows(window) -> list[int]:
    value = window.property("selectedIndexes")
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return list(value or [])


def _photo_record(controller, path: Path):
    return next(
        photo
        for photo in controller.photos.photos
        if Path(photo.folder_path) / photo.name == path
    )


def _wait(qt_app, predicate, description: str, timeout: float = 10.0) -> None:
    assert varj_feltetelre(qt_app, predicate, timeout), description


@pytest.mark.parametrize("magassag_elteres", _MAGASSAG_ELTERESEK)
def test_mappa_huzas_lemezen_indexben_hasabban_es_racsban_is_atvezet(
    mappahuzas_app, qt_app, magassag_elteres
):
    window, controller, _engine = mappahuzas_app
    window.resize(window.width(), window.height() + magassag_elteres)
    window.show()
    qt_app.processEvents()

    library = Path(controller.currentFolder)
    source = library / "atmozgatando"
    target = library / "cel"
    moved = target / source.name
    original_ini = (source / ".picasa.ini").read_bytes()
    controller.selectFolder(str(library))
    vart_racs = {
        library / "a.jpg",
        library / "b.jpg",
        source / "mappakep.jpg",
        target / "celkep.jpg",
    }
    _wait(
        qt_app,
        lambda: vart_racs.issubset(set(_photo_paths(controller))),
        "a gyökérmappa és almappái nem töltődtek be a rács modelljébe",
    )
    racs_elotte = set(_photo_paths(controller))
    window.setProperty("selectedIndexes", [1])
    qt_app.processEvents()

    source_row = _mappa_sor(window, source)
    drop_target = _visual(window, "folderDropArea_" + str(target))
    assert source_row is not None, f"a forrásmappa sora hiányzik a bal hasábból: {source}"
    assert drop_target is not None and drop_target.property("enabled") is True
    source_mouse = _visual(
        window,
        "folderRowMouse",
        predicate=lambda item: Path(str(item.property("folderPath"))) == source,
    )
    _valodi_mappahuzas(window, qt_app, source_mouse, drop_target)

    _wait(
        qt_app,
        lambda: moved.is_dir() and not source.exists(),
        "a mappa bal hasábról a célmappára húzása nem mozgatta a lemezen lévő könyvtárat",
    )
    _wait(
        qt_app,
        lambda: _mappa_sor(window, moved) is not None
        and _mappa_sor(window, source) is None,
        "a bal hasáb nem követte a mappa új helyét",
    )

    assert (moved / ".picasa.ini").read_bytes() == original_ini
    assert load_document(moved / ".picasa.ini").section("mappakep.jpg").get("caption") == _FELIRAT
    assert (moved / "mappakep.jpg").is_file()

    with open_index(controller._db_path) as connection:
        indexed = connection.execute(
            "SELECT f.path, p.name FROM photos AS p "
            "JOIN folders AS f ON f.id = p.folder_id "
            "WHERE p.name = 'mappakep.jpg'"
        ).fetchall()
        old_folder = connection.execute(
            "SELECT 1 FROM folders WHERE path = ?", (str(source),)
        ).fetchone()
    assert [(Path(row["path"]), row["name"]) for row in indexed] == [
        (moved, "mappakep.jpg")
    ]
    assert old_folder is None

    assert Path(controller.currentFolder) == library
    assert set(_photo_paths(controller)) == {
        library / "a.jpg",
        library / "b.jpg",
        moved / "mappakep.jpg",
        target / "celkep.jpg",
    }
    assert len(racs_elotte) == len(_photo_paths(controller))
    assert _selected_rows(window) == []


@pytest.mark.parametrize("belepesi_pont", ["helyi", "folder_menu"])
@pytest.mark.parametrize("magassag_elteres", _MAGASSAG_ELTERESEK)
def test_indexkepek_frissitese_ujraszinkronizalja_a_lemezt_indexet_cachet_es_racsot(
    frissites_app, qt_app, tmp_path, belepesi_pont, magassag_elteres
):
    window, controller, _engine = frissites_app
    window.resize(window.width(), window.height() + magassag_elteres)
    window.show()
    qt_app.processEvents()
    folder = Path(controller.watchedFolders[0]) / "fotok"
    controller.selectFolder(str(folder))
    _wait(qt_app, lambda: controller.photos.rowCount() == 3, "a próbamappa rácsa nem töltődött be")
    window.setProperty("selectedIndexes", [0, 1])
    qt_app.processEvents()

    changed_path = folder / "a.jpg"
    before_record = _photo_record(controller, changed_path)
    cache = controller._provider._cache
    old_cache = cache.thumbnail_path(
        changed_path, before_record.mtime_ns, before_record.size
    )
    _wait(qt_app, old_cache.is_file, "a rácsban lévő kép bélyegképe nem került a lemez-cache-be")
    ini_path = folder / ".picasa.ini"
    ini_before = ini_path.read_bytes()
    stat_before = changed_path.stat()

    make_jpeg(changed_path, size=(240, 180))
    os.utime(
        changed_path,
        ns=(stat_before.st_atime_ns, stat_before.st_mtime_ns + 5_000_000_000),
    )
    new_path = folder / "d_uj.jpg"
    make_jpeg(new_path, size=(90, 70))

    if belepesi_pont == "helyi":
        context_menu = jobbklikk_mappan(window, qt_app, folder)
        kattints(window, qt_app, gyerek(window, "folderMenuRefreshThumbnails"))
    else:
        menu_bar = window.property("menuBar")
        menu = _megnyit(menu_bar, qt_app, "F&older")
        refresh_item = next(
            _menupont(menu, index)
            for index in range(int(menu.property("count") or 0))
            if _menupont(menu, index).property("text") == "Refresh &Thumbnails"
        )
        kattints(window, qt_app, refresh_item)

    def index_frissult() -> bool:
        try:
            record = _photo_record(controller, changed_path)
            return (
                controller.photos.rowCount() == 4
                and record.mtime_ns == changed_path.stat().st_mtime_ns
                and record.size == changed_path.stat().st_size
                and new_path in _photo_paths(controller)
            )
        except (StopIteration, OSError):
            return False

    _wait(qt_app, index_frissult, "a Refresh Thumbnails nem frissítette a lemezváltozást az indexben")
    changed_record = _photo_record(controller, changed_path)
    new_cache = cache.thumbnail_path(
        changed_path, changed_record.mtime_ns, changed_record.size
    )
    _wait(qt_app, new_cache.is_file, "a frissített kép új bélyegképe nem került a lemez-cache-be")

    assert old_cache.is_file(), "a korábbi, verziózott bélyegkép-cache fájl eltűnt"
    assert new_cache != old_cache
    assert changed_path.stat().st_size != stat_before.st_size
    assert new_path.is_file()
    assert ini_path.read_bytes() == ini_before
    assert _mappa_sor(window, folder) is not None

    with open_index(controller._db_path) as connection:
        indexed = connection.execute(
            "SELECT p.name, p.size, p.mtime_ns FROM photos AS p "
            "JOIN folders AS f ON f.id = p.folder_id WHERE f.path = ?",
            (str(folder),),
        ).fetchall()
    indexed_by_name = {row["name"]: row for row in indexed}
    assert set(indexed_by_name) == {"a.jpg", "b.jpg", "c.jpg", "d_uj.jpg"}
    assert indexed_by_name["a.jpg"]["size"] == changed_path.stat().st_size
    assert indexed_by_name["a.jpg"]["mtime_ns"] == changed_path.stat().st_mtime_ns
    assert new_path in _photo_paths(controller)
    assert _selected_rows(window) == [0, 1]
    grid = window.findChild(QObject, "photoGrid")
    assert grid is not None
    new_row = next(
        row for row, path in enumerate(_photo_paths(controller)) if path == new_path
    )
    assert _visual(
        window,
        "thumbMouseArea",
        predicate=lambda item: int(item.parentItem().property("index")) == new_row,
    ) is not None, "az új kép nem jelent meg a tényleges rácsdelegátumok között"

    if belepesi_pont == "helyi":
        assert context_menu.property("visible") is False
