"""#5363: a Név nélküliek nézete első megnyitáskor sem csúszik a bal panel alá."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, QtMsgType, qInstallMessageHandler

from support.fixture_guards import qml_warning_guard
from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_unnamed_faces_view_5183 import (
    _click,
    _find_item,
    _make_portrait_photos,
    _seed_six_faces,
)
from tests.support.varakozas import var_feltetelre

_PERSON = "Teszt Elek"
_WINDOW_HEIGHT_OFFSETS = (-5, 0, 5)


@pytest.fixture
def qml_app_5363(qt_app, tmp_path, monkeypatch, request):
    """Valódi QML-ablak, helyi portréfotókkal és elkülönített felhasználói profillal."""
    isolated_home = tmp_path / "home"
    for variable, folder in (
        ("HOME", isolated_home),
        ("XDG_CONFIG_HOME", isolated_home / ".config"),
        ("XDG_DATA_HOME", isolated_home / ".local" / "share"),
        ("XDG_CACHE_HOME", isolated_home / ".cache"),
        ("XDG_STATE_HOME", isolated_home / ".local" / "state"),
    ):
        folder.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(variable, str(folder))

    warning_guard = qml_warning_guard()
    next(warning_guard)
    try:
        yield from _build_qml_app(
            qt_app,
            tmp_path,
            kepeket_keszit=_make_portrait_photos,
            belyegkep_meret=220,
            valodi_belyegkep=True,
            keep_modul=request.module,
        )
    finally:
        try:
            next(warning_guard)
        except StopIteration:
            pass


@pytest.mark.parametrize("source", ("folder", "person_album"))
@pytest.mark.parametrize("height_offset", _WINDOW_HEIGHT_OFFSETS)
def test_first_unnamed_open_stays_right_of_sidebar_and_has_no_header_loop(
    qml_app_5363, qt_app, source, height_offset
):
    window, controller, engine = qml_app_5363
    window.setWidth(1280)
    window.setHeight(1005 + height_offset)
    assert var_feltetelre(
        qt_app, lambda: window.height() == 1005 + height_offset, 3.0
    )

    face_scan = engine.rootContext().contextProperty("faceScanController")
    _seed_six_faces(controller._db_path)
    assert face_scan.unnamedCount == 6
    assert face_scan.assignNameToFaces([1], _PERSON)
    controller.refreshCollections()
    face_scan.unnamedCountChanged.emit()

    folder_pane = _find_item(window, "folderPane")
    assert folder_pane is not None
    folder_pane.setProperty("peopleCollapsed", False)

    messages: list[str] = []

    def capture_qml_warnings(message_type, _context, message):
        if message_type == QtMsgType.QtWarningMsg and "Binding loop detected" in message:
            messages.append(message)
        if previous_handler is not None:
            previous_handler(message_type, _context, message)

    previous_handler = qInstallMessageHandler(capture_qml_warnings)
    try:
        if source == "person_album":
            person_row = _find_item(window, f"personItem_{_PERSON}")
            assert var_feltetelre(
                qt_app,
                lambda: person_row is not None
                and person_row.width() > 0
                and person_row.height() > 0,
                3.0,
            )
            _click(qt_app, person_row)
            assert var_feltetelre(
                qt_app,
                lambda: controller.currentPersonName == _PERSON
                and (header := _find_item(window, "personAlbumFeedHeader"))
                is not None
                and header.height() > 0,
                3.0,
            )

        unnamed_row = _find_item(window, "unnamedFacesItem")
        assert var_feltetelre(
            qt_app,
            lambda: unnamed_row is not None
            and unnamed_row.width() > 0
            and unnamed_row.height() > 0,
            3.0,
        )
        _click(qt_app, unnamed_row)

        view = _find_item(window, "unnamedFacesView")
        assert var_feltetelre(
            qt_app,
            lambda: view is not None
            and view.isVisible()
            and view.width() > 0
            and _find_item(window, "unnamedAlbumFaceCount") is not None,
            3.0,
        )
        if source == "person_album":
            assert controller.currentPersonName == _PERSON
            assert window.property("unnamedFacesOpen") is True

        sidebar_right = folder_pane.mapToScene(
            QPointF(folder_pane.width(), 0)
        ).x()
        header_band = _find_item(window, "unnamedHeaderBandFill")
        count = _find_item(window, "unnamedAlbumFaceCount")
        instruction = _find_item(window, "unnamedInstructions")
        assert header_band is not None and count is not None and instruction is not None
        header_band_left = header_band.mapToScene(QPointF(0, 0)).x()
        count_left = count.mapToScene(QPointF(0, count.height() / 2)).x()
        instruction_left = instruction.mapToScene(QPointF(0, instruction.height() / 2)).x()

        image = window.grabWindow()
        assert not image.isNull(), "Az első megnyitás renderelt ablakképe üres."
        if height_offset == 0:
            output = Path.cwd() / ".bt" / f"kep_5363_{source}.png"
            output.parent.mkdir(parents=True, exist_ok=True)
            assert image.save(str(output))
    finally:
        qInstallMessageHandler(previous_handler)

    height_loops = [
        message
        for message in messages
        if "LightboxFeed.qml" in message and 'property "height"' in message
    ]
    failures = []
    # A sáv kitöltését és a feliratok elem-geometriáját hasonlítjuk a futó
    # ablak tényleges bal paneljéhez; betűpixelt nem mérünk.
    for name, left in (
        ("fejléc kitöltése", header_band_left),
        ("darabszám sora", count_left),
        ("útmutató", instruction_left),
    ):
        if left < sidebar_right - 3:
            failures.append(
                f"{name} a bal panel alá nyúlik: forrás={source}, "
                f"elem={left:.1f}, panel={sidebar_right:.1f}"
            )
    if height_loops:
        failures.append(
            "A személyalbum-fejléc kötési hurka megjelent:\n"
            + "\n".join(height_loops)
        )
    assert not failures, "\n".join(failures)
