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
    for item in _latvanyelemek(window.contentItem()):
        if (
            item.property("kind") == "folder"
            and Path(item.property("path") or "") == path
        ):
            return item
    raise AssertionError(f"A mappasor nem található: {path}")


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
    qt_app.processEvents()
    library = Path(controller._roots[0])
    source = library / "forras"
    target = library / "cel"
    source_photo = source / "atvitt.jpg"
    assert source_photo.is_file()
    assert _mappasor_latszik(window, target)

    _fileops = engine.rootContext().contextProperty("fileOpsController")
    finished = QSignalSpy(_fileops.batchFinished)
    failed = QSignalSpy(_fileops.operationFailed)
    shutil.rmtree(target)
    assert not target.exists()

    _mappat_kivalaszt(window, controller, qt_app, source)
    window.setProperty("selectedIndexes", [0])
    qt_app.processEvents()
    # A sor szándékosan elavult marad: a ledobás a watcher frissítése előtt érkezik.
    _mappasor(window, target)
    mouse_area = next(
        item
        for item in _latvanyelemek(window.contentItem())
        if item.objectName() == "thumbMouseArea"
        and int(item.parentItem().property("index")) == 0
    )
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
    start = _ablakpont(window, mouse_area)
    end = _ablakpont(window, _mappasor(window, target))
    QTest.mouseMove(window, start)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
    qt_app.processEvents()
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
    assert _attached_drag(drag_proxy).property("active") is True
    assert drop_area.property("enabled") is True
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=end)
    qt_app.processEvents()

    assert finished.count() == 0, "a nem létező célra elindult a fájlművelet"
    assert failed.count() == 0, "a nem létező cél hibajelzést váltott ki"
    assert source_photo.is_file()
