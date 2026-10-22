"""Külső mappaváltozás és elavult célra dobás a QML-felületen (#5177)."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QSignalSpy, QTest

from conftest import _build_qml_app
from picasapy.index import open_index
from picasapy.scanner.watcher import LibraryWatcher
from support.jpeg_factory import make_jpeg


def _keszits_mappakat(root: Path) -> None:
    source = root / "forras"
    target = root / "cel"
    vanished = root / "Eltunt"
    source.mkdir()
    target.mkdir()
    vanished.mkdir()
    make_jpeg(source / "atvitt.jpg", size=(64, 64))
    make_jpeg(target / "marad.jpg", size=(64, 64))
    make_jpeg(vanished / "kep.jpg", size=(64, 64))


@pytest.fixture
def qml_app_5177(qt_app, tmp_path, monkeypatch, request):
    """Asztal alakú, elkülönített felhasználói profilból induló QML-app."""
    username = Path.home().name or "test-user"
    home = tmp_path / "Users" / username
    desktop = home / "Desktop"
    desktop.mkdir(parents=True)
    for name, value in (
        ("HOME", home),
        ("USERPROFILE", home),
        ("XDG_CONFIG_HOME", home / ".config"),
        ("XDG_DATA_HOME", home / ".local" / "share"),
        ("XDG_CACHE_HOME", home / ".cache"),
        ("XDG_STATE_HOME", home / ".local" / "state"),
    ):
        monkeypatch.setenv(name, str(value))
    yield from _build_qml_app(
        qt_app,
        desktop,
        kepeket_keszit=_keszits_mappakat,
        keep_modul=request.module,
    )


def _varj(qt_app, feltetel, leiras: str, timeout: float = 15.0) -> None:
    hatarido = time.monotonic() + timeout
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.05)
    pytest.fail(f"Határidőn belül nem teljesült: {leiras}")


def _latvanyelemek(root):
    for child in root.childItems():
        yield child
        yield from _latvanyelemek(child)


def _mappasor(window, path: Path):
    row = _mappasor_if_present(window, path)
    if row is not None:
        return row
    raise AssertionError(f"A mappasor nem található: {path}")


def _mappasor_if_present(window, path: Path):
    for item in _latvanyelemek(window.contentItem()):
        if (
            item.property("kind") == "folder"
            and Path(item.property("path") or "") == path
        ):
            return item
    return None


def _mappasor_latszik(window, path: Path) -> bool:
    return any(
        item.property("kind") == "folder"
        and Path(item.property("path") or "") == path
        for item in _latvanyelemek(window.contentItem())
    )


def _ablakpont(window, item) -> QPoint:
    scene_point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    return QPoint(round(scene_point.x()), round(scene_point.y()))


def _thumb_mouse_area(window, index: int):
    for item in _latvanyelemek(window.contentItem()):
        if (
            item.objectName() == "thumbMouseArea"
            and item.parentItem() is not None
            and int(item.parentItem().property("index")) == index
        ):
            return item
    return None


def _varj_stabil_ablakpontokra(qt_app, window, *keresok):
    """Megvárja, hogy a keresett elemek és ablakbeli helyük stabil legyen."""
    elozo_items = ()
    elozo_geometry = None
    stabil_korok = 0
    stabil_items = ()
    stabil_points = ()

    def stabil():
        nonlocal elozo_items, elozo_geometry, stabil_korok
        nonlocal stabil_items, stabil_points
        items = tuple(kereso() for kereso in keresok)
        if any(item is None for item in items):
            elozo_items = ()
            elozo_geometry = None
            stabil_korok = 0
            return False

        scene_items = tuple(_latvanyelemek(window.contentItem()))
        if any(
            not any(candidate == item for candidate in scene_items) for item in items
        ):
            elozo_items = ()
            elozo_geometry = None
            stabil_korok = 0
            return False

        geometry = []
        for item in items:
            if not item.isVisible() or item.width() <= 0 or item.height() <= 0:
                elozo_items = ()
                elozo_geometry = None
                stabil_korok = 0
                return False
            point = _ablakpont(window, item)
            if not (
                0 <= point.x() < window.width()
                and 0 <= point.y() < window.height()
            ):
                elozo_items = ()
                elozo_geometry = None
                stabil_korok = 0
                return False
            geometry.append(
                (
                    point.x(),
                    point.y(),
                    round(item.width(), 3),
                    round(item.height(), 3),
                )
            )

        aktualis = tuple(geometry)
        try:
            same_items = len(items) == len(elozo_items) and all(
                current == previous
                for current, previous in zip(items, elozo_items, strict=True)
            )
        except RuntimeError:
            same_items = False
        if same_items and aktualis == elozo_geometry:
            stabil_korok += 1
        else:
            stabil_korok = 0
        elozo_items = items
        elozo_geometry = aktualis
        stabil_items = items
        stabil_points = tuple(_ablakpont(window, item) for item in items)
        return stabil_korok >= 2

    _varj(qt_app, stabil, "a QML-elemek ablakbeli helye stabil legyen")
    return stabil_items, stabil_points


def _mappat_kivalaszt(window, controller, qt_app, path: Path) -> None:
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _ablakpont(window, _mappasor(window, path)),
    )
    _varj(
        qt_app,
        lambda: Path(controller.currentFolder or "") == path,
        f"a kiválasztott mappa {path} legyen",
    )


def _attached_drag(item):
    return next(
        child
        for child in item.children()
        if child.metaObject().className() == "QQuickDragAttached"
    )


def test_kivul_atnevezett_mappa_sora_es_kepei_eltunnek(
    qml_app_5177, qt_app
):
    window, controller, _engine = qml_app_5177
    library = Path(controller._roots[0])
    vanished = library / "Eltunt"
    assert _mappasor_latszik(window, vanished)

    # A képet az observer indulása előtt távolítjuk el, így az indexben még
    # megvan, de a figyelőnek csak a könyvtár törlési eseményét kell kezelnie.
    (vanished / "kep.jpg").unlink()
    watcher = LibraryWatcher(
        tuple(controller._roots),
        lambda folders: controller.watcherDirty.emit(list(folders)),
    )
    watcher.start()
    try:
        vanished.rmdir()
        _varj(
            qt_app,
            lambda: not _mappasor_latszik(window, vanished),
            "a törölt mappa sora tűnjön el a bal sávból",
        )
    finally:
        watcher.stop()

    with open_index(controller._db_path) as conn:
        assert conn.execute(
            "SELECT 1 FROM folders WHERE path = ?", (str(vanished),)
        ).fetchone() is None
        assert conn.execute(
            "SELECT 1 FROM photos p JOIN folders f ON f.id = p.folder_id "
            "WHERE f.path = ? LIMIT 1",
            (str(vanished),),
        ).fetchone() is None


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_eltunt_celre_dobas_nem_indit_fajlmuveletet(
    qml_app_5177, qt_app, height_delta
):
    window, controller, engine = qml_app_5177
    window.resize(window.width(), window.height() + height_delta)
    library = Path(controller._roots[0])
    source = library / "forras"
    target = library / "cel"
    source_photo = source / "atvitt.jpg"
    assert source_photo.is_file()
    assert _mappasor_latszik(window, target)

    _fileops = engine.rootContext().contextProperty("fileOpsController")
    finished = QSignalSpy(_fileops.batchFinished)
    failed = QSignalSpy(_fileops.operationFailed)

    _varj(
        qt_app,
        lambda: not controller._sync_running and not controller._dirty_running,
        "az induláskori indexfrissítés fejeződjön be",
    )
    # A watcher leállítása a törlés ELŐTT a stale-row állapotot tartja fenn
    # a dobásig, ha ebben a fixture-ben elindult figyelő.
    watcher = controller._watcher
    if watcher is not None:
        watcher.stop()
    _varj_stabil_ablakpontokra(
        qt_app,
        window,
        lambda: _mappasor_if_present(window, target),
    )
    shutil.rmtree(target)
    assert not target.exists()

    _mappat_kivalaszt(window, controller, qt_app, source)
    window.setProperty("selectedIndexes", [0])
    qt_app.processEvents()
    # A sor szándékosan elavult marad; a teszt a frissítés előtti állapotot tartja fenn.
    (mouse_area, _target_row), (start, end) = _varj_stabil_ablakpontokra(
        qt_app,
        window,
        lambda: _thumb_mouse_area(window, 0),
        lambda: _mappasor_if_present(window, target),
    )
    assert mouse_area.contains(
        mouse_area.mapFromItem(window.contentItem(), QPointF(start))
    )
    QTest.mouseMove(window, start)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
    _varj(
        qt_app,
        lambda: mouse_area.property("pressed") is True
        and any(
            item == mouse_area for item in _latvanyelemek(window.contentItem())
        ),
        "a lenyomott bélyegkép-delegátum maradjon a jelenetben",
    )
    assert mouse_area.property("pressed") is True
    delta = end - start
    distance = max(abs(delta.x()), abs(delta.y()))
    steps = max(1, (distance + 3) // 4)
    for step in range(1, steps + 1):
        point = start + QPoint(
            round(delta.x() * step / steps), round(delta.y() * step / steps)
        )
        QTest.mouseMove(window, point)
        qt_app.processEvents()
    assert mouse_area.property("dragging") is True
    drag_proxy = next(
        item
        for item in _latvanyelemek(window.contentItem())
        if item.objectName() == "thumbDragProxy"
        and int(item.property("photoIndex")) == 0
    )
    drop_area = next(
        item
        for item in _latvanyelemek(window.contentItem())
        if item.objectName() == f"folderDropArea_{target}"
    )
    assert _attached_drag(drag_proxy).property("active") is True
    assert drop_area.property("enabled") is True
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=end)
    qt_app.processEvents()

    assert finished.count() == 0, "a nem létező célra elindult a fájlművelet"
    assert failed.count() == 0, "a nem létező cél hibajelzést váltott ki"
    assert source_photo.is_file()
