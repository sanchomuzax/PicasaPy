"""Valódi egérhúzás a tálcára, albumon belülre, mappára és személyre (#5008)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, QMetaObject, QObject, Qt
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import open_index, replace_faces, sync_tree
from picasapy.ini import load_or_empty, parse_document, save_document
from picasapy.ini.rect64 import Rect64, encode_rect64
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre


_HEIGHT_DELTAS = (-5, 0, 5)
_CONTACT_ID = "b8e4117cf1d6615b"
_PERSON_NAME = "anna kis"


def _keszits_konyvtarat(library: Path) -> None:
    for name in ("a.jpg", "b.jpg", "c.jpg", "cut-me.jpg"):
        make_jpeg(library / name, size=(160, 120))

    source = library / "atmozgatando"
    target = library / "cel"
    source.mkdir()
    target.mkdir()
    make_jpeg(source / "mappakep.jpg", size=(80, 60))
    make_jpeg(target / "celkep.jpg", size=(80, 60))
    document = parse_document("").with_value(
        "mappakep.jpg", "caption", "A mappával együtt költöző felirat"
    ).with_value("mappakep.jpg", "hidden", "yes")
    save_document(document, source / ".picasa.ini")
    target_document = parse_document("").with_value("celkep.jpg", "hidden", "yes")
    save_document(target_document, target / ".picasa.ini")

    tree_source = library / "fanegyed"
    tree_target = library / "facel"
    tree_source.mkdir()
    tree_target.mkdir()
    make_jpeg(tree_source / "fakep.jpg", size=(80, 60))
    make_jpeg(tree_target / "facelkep.jpg", size=(80, 60))
    save_document(
        parse_document("").with_value("fakep.jpg", "hidden", "yes"),
        tree_source / ".picasa.ini",
    )
    save_document(
        parse_document("").with_value("facelkep.jpg", "hidden", "yes"),
        tree_target / ".picasa.ini",
    )


@pytest.fixture
def dnd_qml_app(qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
        keep_modul=request.module,
    )


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _find_visual(root, name: str, *, predicate=None):
    for item in _walk(root.contentItem()):
        if item.objectName() == name and (predicate is None or predicate(item)):
            return item
    raise AssertionError(f"A(z) {name!r} vizuális elem nem található")


def _folder_row(window, path: Path):
    for item in _walk(window.contentItem()):
        if item.property("kind") == "folder" and Path(item.property("path") or "") == path:
            return item
    raise AssertionError(f"A mappasor nem található: {path}")


def _child(root, name: str):
    item = root.findChild(QObject, name)
    assert item is not None, f"A(z) {name!r} elem nem található"
    return item


def _point_in_window(window, item) -> QPoint:
    pos = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    return QPoint(round(pos.x()), round(pos.y()))


def _wait(qt_app, predicate, description: str, timeout: float = 10.0) -> None:
    assert varj_feltetelre(qt_app, predicate, timeout), description


def _attached_drag(item):
    return next(
        child
        for child in item.children()
        if child.metaObject().className() == "QQuickDragAttached"
    )


def _real_drag(window, qt_app, engine, source, start_item, end_item) -> None:
    drag = _attached_drag(source)
    start = _point_in_window(window, start_item)
    end = _point_in_window(window, end_item)
    if not (0 <= start.x() < window.width() and 0 <= start.y() < window.height()):
        chain = []
        item = start_item
        while item is not None:
            point = item.mapToItem(window.contentItem(), QPointF(0, 0))
            chain.append(
                (item.objectName(), item.x(), item.y(), item.width(), item.height(),
                 item.isVisible(), round(point.x()), round(point.y()))
            )
            item = item.parentItem()
        pytest.fail(f"a forrás nem látható: {start}; {chain}")
    QTest.mouseMove(window, start)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
    qt_app.processEvents()
    if start_item.property("pressed") is not None:
        assert start_item.property("pressed") is True, f"a húzás lenyomása nem a forráson indult: {start}"

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
        "a QTest-egérhúzás nem indította el a Drag forrást: "
        f"pressed={start_item.property('pressed')}, "
        f"dragging={start_item.property('dragging')}, "
        f"selected={start_item.parentItem().property('selected')}, "
        f"start={start}, end={end}"
    )
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=end)
    qt_app.processEvents()


def _value_list(value) -> list:
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return list(value or [])


def _invoke(obj, name: str, *arguments) -> None:
    assert QMetaObject.invokeMethod(
        obj, name, Qt.ConnectionType.DirectConnection, *arguments
    ), f"A(z) {name} QML-jel nem hívható"


def _path_row(controller, path: Path) -> int:
    row = int(controller.photos.rowOfPath(str(path)))
    assert row >= 0, f"A kép nincs a rácsban: {path}"
    return row


def _reorder_drop_arguments(window, controller, target_row: int):
    target = _find_visual(
        window,
        "thumbMouseArea",
        predicate=lambda item: int(item.parentItem().property("index")) == target_row,
    )
    area = _find_visual(window, "feedReorderDropArea")
    point = target.mapToItem(
        area, QPointF(target.width() / 2, target.height() / 2)
    )
    return (
        0,
        int(controller.photos.rowCount()),
        float(area.width()),
        float(point.x()),
        float(point.y()),
    )


@pytest.mark.parametrize("height_delta", _HEIGHT_DELTAS)
def test_grid_to_tray_and_tray_to_grid_use_the_dragged_rows_and_clipboard_keys(
    dnd_qml_app, qt_app, height_delta
):
    """A tálcára dobás rögzít; visszadobáskor a forrás képe rendeződik."""
    window, controller, engine = dnd_qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()

    library = Path(controller.currentFolder)
    photo_a = library / "a.jpg"
    photo_b = library / "b.jpg"
    photo_c = library / "c.jpg"
    row_a, row_b, row_c = (
        _path_row(controller, path) for path in (photo_a, photo_b, photo_c)
    )
    window.setProperty("selectedIndexes", [row_a])
    photo_grid = _child(window, "photoGrid")
    photo_grid.setProperty("contentY", 0)
    qt_app.processEvents()

    source_proxy = _find_visual(
        window,
        "thumbDragProxy",
        predicate=lambda item: int(item.property("photoIndex")) == row_a,
    )
    source_mouse = _find_visual(
        window,
        "thumbMouseArea",
        predicate=lambda item: int(item.parentItem().property("index")) == row_a,
    )
    source_center = QPointF(source_mouse.width() / 2, source_mouse.height() / 2)
    source_in_grid = source_mouse.mapToItem(photo_grid, source_center)
    photo_grid.setProperty(
        "contentY",
        max(
            0.0,
            photo_grid.property("contentY")
            + source_in_grid.y()
            - photo_grid.height() / 2,
        ),
    )
    qt_app.processEvents()
    source_proxy = _find_visual(
        window,
        "thumbDragProxy",
        predicate=lambda item: int(item.property("photoIndex")) == row_a,
    )
    source_mouse = _find_visual(
        window,
        "thumbMouseArea",
        predicate=lambda item: int(item.parentItem().property("index")) == row_a,
    )
    source_in_grid = source_mouse.mapToItem(
        photo_grid,
        QPointF(source_mouse.width() / 2, source_mouse.height() / 2),
    )
    assert 0 <= source_in_grid.y() <= photo_grid.height(), (
        "a rácsbeli forrás nem került a nézőtérre görgetés után: "
        f"y={source_in_grid.y()}, height={photo_grid.height()}"
    )

    tray_area = _find_visual(window, "trayDropArea")
    tray_strip = _child(window, "trayScratchStrip")
    assert tray_area.property("enabled") is True

    _real_drag(window, qt_app, engine, source_proxy, source_mouse, tray_strip)
    _wait(
        qt_app,
        lambda: bool(controller.isHeldAt(row_a)),
        "a rácsból a tálcára húzott kép nem került a megtartott elemek közé",
    )
    assert str(photo_a) in list(controller.heldPaths)

    # A régi kijelölés C; a tálcáról húzott A-nak kell a C elé kerülnie.
    # Ha a rács a saját kijelölését használná, C-t próbálná önmaga elé tenni.
    window.setProperty("selectedIndexes", [row_c])
    controller.selectTrayIndex(0, False, False)
    qt_app.processEvents()
    tray_thumb = _find_visual(
        window,
        "trayPreviewThumb",
        predicate=lambda item: int(item.property("index")) == 0,
    )
    tray_drag_rows = _value_list(tray_thumb.property("photoRows"))
    assert tray_drag_rows == [row_a]
    grid_mouse_c = _find_visual(
        window,
        "thumbMouseArea",
        predicate=lambda item: int(item.parentItem().property("index")) == row_c,
    )
    tray_proxy = next(
        item for item in _walk(tray_thumb) if item.objectName() == "trayDragProxy"
    )
    _real_drag(window, qt_app, engine, tray_proxy, tray_thumb, grid_mouse_c)
    reorder_area = _find_visual(window, "feedReorderDropArea")
    assert reorder_area.property("enabled") is True
    reordered = varj_feltetelre(
        qt_app,
        lambda: Path(controller.photos.filePathAt(row_b)) == photo_a,
        10.0,
    )
    assert reordered, (
        "a tálcáról a rácsra dobott kép nem a cél elé került: "
        f"rows={(row_a, row_b, row_c)}, "
        f"order={[Path(controller.photos.filePathAt(row)).name for row in range(3)]}, "
        f"grid={(photo_grid.width(), photo_grid.height(), photo_grid.property('contentY'))}"
    )
    assert [Path(controller.photos.filePathAt(row)).name for row in range(3)] == [
        "b.jpg",
        "a.jpg",
        "c.jpg",
    ]

    # A rács Ctrl+C és Ctrl+V útja is valódi billentyűeseménnyel működik.
    photo_to_copy = library / "c.jpg"
    copy_row = _path_row(controller, photo_to_copy)
    window.requestActivate()
    window.setProperty("selectedIndexes", [copy_row])
    window.setProperty("selectedIndex", copy_row)
    qt_app.processEvents()
    copy_shortcut = _child(window, "shortcutCopyFiles")
    assert copy_shortcut.property("enabled") is True
    QTest.keyClick(window, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()
    file_ops = engine.rootContext().contextProperty("fileOpsController")
    copy_mime = file_ops._vagolap_adat
    assert [Path(url.toLocalFile()) for url in copy_mime.urls()] == [photo_to_copy]
    assert any(
        bytes(copy_mime.data(fmt)).startswith(b"copy\n")
        for fmt in copy_mime.formats()
        if "copied-files" in fmt
    ), "a Ctrl+C nem másolásként jelölte a vágólap fájljait"

    paste_shortcut = _child(window, "shortcutPasteFiles")
    assert paste_shortcut.property("enabled") is True
    QTest.keyClick(window, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    _wait(
        qt_app,
        lambda: any(library.glob("c-*.jpg")),
        "a Ctrl+V nem másolta vissza a fájlt a rács mappájába",
    )
    assert photo_to_copy.is_file(), "Ctrl+V másoláskor meg kell maradnia a forrásnak"
    from picasapy.app.worker_thread import wait_for_all_background_workers

    assert wait_for_all_background_workers(30.0)

    # A rácson a Ctrl+X billentyűesemény ténylegesen kivágja a kijelölt fájlt.
    photo_to_cut = library / "cut-me.jpg"
    cut_row = _path_row(controller, photo_to_cut)
    window.requestActivate()
    window.setProperty("selectedIndexes", [cut_row])
    window.setProperty("selectedIndex", cut_row)
    qt_app.processEvents()
    cut_shortcut = _child(window, "shortcutCutFiles")
    assert cut_shortcut.property("enabled") is True
    QTest.keyClick(window, Qt.Key.Key_X, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()
    cut_mime = file_ops._vagolap_adat
    assert cut_mime.hasUrls()
    assert [Path(url.toLocalFile()) for url in cut_mime.urls()] == [photo_to_cut]
    assert any(
        bytes(cut_mime.data(fmt)).startswith(b"cut\n")
        for fmt in cut_mime.formats()
        if "copied-files" in fmt
    ), "a Ctrl+X nem jelölte kivágottnak a vágólap fájljait"


@pytest.mark.parametrize("height_delta", _HEIGHT_DELTAS)
def test_album_drag_rewrites_albumorder_through_the_ini_api(
    dnd_qml_app, qt_app, height_delta
):
    window, controller, engine = dnd_qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()
    library = Path(controller.currentFolder)
    paths = [library / name for name in ("a.jpg", "b.jpg", "c.jpg")]
    rows = [_path_row(controller, path) for path in paths]
    token = controller.createAlbum("Húzással rendezett album", rows)
    assert token
    controller.showAlbum(token)
    _wait(
        qt_app,
        lambda: controller.photos.rowCount() == 3
        and controller.currentAlbumToken == token,
        "a tesztalbum nem nyílt meg",
    )

    row_a = _path_row(controller, paths[0])
    row_c = _path_row(controller, paths[2])
    window.setProperty("selectedIndexes", [row_a])
    qt_app.processEvents()
    source = _find_visual(
        window,
        "thumbDragProxy",
        predicate=lambda item: int(item.property("photoIndex")) == row_a,
    )
    source_mouse = _find_visual(
        window,
        "thumbMouseArea",
        predicate=lambda item: int(item.parentItem().property("index")) == row_a,
    )
    target_mouse = _find_visual(
        window,
        "thumbMouseArea",
        predicate=lambda item: int(item.parentItem().property("index")) == row_c,
    )
    _real_drag(window, qt_app, engine, source, source_mouse, target_mouse)

    _wait(
        qt_app,
        lambda: Path(controller.photos.filePathAt(1)) == paths[0],
        "az album kézi húzása nem rendezte át a rácsot",
    )
    assert [Path(controller.photos.filePathAt(row)).name for row in range(3)] == [
        "b.jpg",
        "a.jpg",
        "c.jpg",
    ]

    document = load_or_empty(library / ".picasa.ini")
    members = [
        (document.section(path.name).get("albums") or "").split(",")
        for path in paths
    ]
    assert all(token in album_tokens for album_tokens in members)
    positions = {
        path.name: float(
            next(
                part.split(":", 1)[1]
                for part in (document.section(path.name).get("albumorder") or "").split(",")
                if part.startswith(token + ":")
            )
        )
        for path in paths
    }
    assert sorted(positions, key=positions.get) == ["b.jpg", "a.jpg", "c.jpg"]


@pytest.mark.parametrize("height_delta", _HEIGHT_DELTAS)
def test_folder_drag_moves_directory_in_flat_and_tree_views(
    dnd_qml_app, qt_app, height_delta
):
    window, controller, engine = dnd_qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()
    library = Path(controller.currentFolder)
    source_path = library / "atmozgatando"
    target_path = library / "cel"
    source_row = _folder_row(window, source_path)
    target_drop = _find_visual(
        window,
        "folderDropArea_" + str(target_path),
    )

    source_mouse = next(
        item for item in _walk(source_row) if item.objectName() == "folderRowMouse"
    )
    assert target_drop.property("enabled") is True
    folder_proxy = next(
        item for item in _walk(source_row) if item.objectName() == "folderDragProxy"
    )
    _real_drag(window, qt_app, engine, folder_proxy, source_mouse, target_drop)
    folder_pane = _child(window, "folderPane")
    moved = target_path / source_path.name
    _wait(
        qt_app,
        lambda: moved.is_dir() and not source_path.exists(),
        "a mappasor húzása nem helyezte át a forrásmappát",
    )
    moved_ini = load_or_empty(moved / ".picasa.ini")
    assert moved_ini.section("mappakep.jpg").get("caption") == (
        "A mappával együtt költöző felirat"
    )
    from picasapy.app.worker_thread import wait_for_all_background_workers

    assert wait_for_all_background_workers(30.0)

    # A mappafa alternatív nézetében is ugyanaz a húzásos áthelyezés él.
    tree_source_path = library / "fanegyed"
    tree_target_path = library / "facel"
    folder_pane = _child(window, "folderPane")
    hierarchy = engine.rootContext().contextProperty("folderHierarchyController")
    hierarchy.setSimplified(True)
    hierarchy.setTreeView(True)
    hierarchy.expandAll()
    _wait(
        qt_app,
        lambda: bool(folder_pane.property("treeViewMode")),
        "a hierarchikus mappanézet nem nyílt meg",
    )
    qt_app.processEvents()
    def tree_rows_ready():
        object_names = {
            item.objectName() for item in _walk(window.contentItem())
        }
        return (
            "hierRow:" + str(tree_source_path) in object_names
            and "hierRow:" + str(tree_target_path) in object_names
        )

    assert varj_feltetelre(qt_app, tree_rows_ready, 10.0), (
        "a húzandó mappasorok nem jelentek meg a fában: "
        f"hierarchy.rows={hierarchy.rows!r}"
    )
    tree_target_row = _find_visual(window, "hierRow:" + str(tree_target_path))
    tree_target_drop = _find_visual(
        window, "hierFolderDropArea:" + str(tree_target_path)
    )
    assert tree_target_drop.property("enabled") is True
    tree_source_mouse = _find_visual(
        window, "hierRowMouse:" + str(tree_source_path)
    )
    tree_drag_proxy = _find_visual(window, "folderTreeDragProxy")
    _real_drag(
        window, qt_app, engine, tree_drag_proxy, tree_source_mouse, tree_target_row
    )

    _wait(
        qt_app,
        lambda: (tree_target_path / tree_source_path.name).is_dir()
        and not tree_source_path.exists(),
        "a fanézetbeli húzás nem helyezte át a forrásmappát",
    )
def _prepare_face_drag(qml_app, qt_app, tmp_path):
    from picasapy.app.worker_thread import wait_for_all_background_workers

    window, controller, engine = qml_app
    assert wait_for_all_background_workers(30.0)
    library = tmp_path / "kepek"
    photo_path = library / "a.jpg"
    make_jpeg(photo_path, size=(320, 160))
    named_rect = Rect64(0.08, 0.12, 0.34, 0.68)
    ini_text = (
        "[Contacts2]\n"
        f"{_CONTACT_ID}={_PERSON_NAME};;\n"
        "[a.jpg]\n"
        f"faces=rect64({encode_rect64(named_rect)}),{_CONTACT_ID};\n"
    )
    (library / ".picasa.ini").write_text(ini_text, encoding="utf-8")
    detection = FaceDetection(
        left=155.0,
        top=15.0,
        right=260.0,
        bottom=130.0,
        score=0.99,
        landmarks=FaceLandmarks(
            right_eye=(185.0, 50.0),
            left_eye=(230.0, 50.0),
            nose=(207.0, 75.0),
            mouth_right=(190.0, 105.0),
            mouth_left=(225.0, 105.0),
        ),
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
        photo_id = conn.execute(
            "SELECT id FROM photos WHERE name = 'a.jpg'"
        ).fetchone()["id"]
        replace_faces(conn, photo_id, [detection])
        conn.commit()
    controller._reload_after_sync()
    assert wait_for_all_background_workers(30.0)
    photo_row = _path_row(controller, photo_path)

    _invoke(
        _child(window, "menuViewPeople"),
        "triggered",
    )
    window.setProperty("selectedIndexes", [photo_row])
    qt_app.processEvents()
    panel = _child(window, "peoplePanel")
    _wait(qt_app, lambda: panel.width() >= 275, "az Emberek panel nem nyílt ki")
    return window, controller, engine, library, photo_path, photo_row


@pytest.mark.parametrize("height_delta", _HEIGHT_DELTAS)
def test_unnamed_face_dragged_onto_person_is_assigned_in_the_ini(
    qml_app_valodi_belyegkep, qt_app, tmp_path, height_delta
):
    window, controller, engine, library, photo_path, photo_row = _prepare_face_drag(
        qml_app_valodi_belyegkep, qt_app, tmp_path
    )
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()
    faces = controller.unnamedFacesOfRows([photo_row])
    assert faces, "a próbaképen nincs húzható névtelen arc"
    face_id = int(faces[0]["faceId"])
    source = _find_visual(window, f"peopleFaceDragProxy_{face_id}")
    source_area = _find_visual(window, f"peopleFaceDragArea_{face_id}")
    target = _find_visual(window, f"peoplePanelRow_{_PERSON_NAME}")
    target_drop = _find_visual(
        window, f"peoplePanelPersonDropArea_{_PERSON_NAME}"
    )
    assert target_drop.property("enabled") is True
    _real_drag(window, qt_app, engine, source, source_area, target)

    _wait(
        qt_app,
        lambda: not any(
            int(face["faceId"]) == face_id
            for face in controller.unnamedFacesOfRows([photo_row])
        ),
        "a cél személyre dobott arc névtelen maradt",
    )
    people = {str(person["name"]).casefold() for person in controller.peopleOfRows([photo_row])}
    assert _PERSON_NAME in people
    document = load_or_empty(library / ".picasa.ini")
    contacts = document.section("Contacts2")
    assert contacts is not None
    assert (contacts.get(_CONTACT_ID) or "").casefold().startswith(_PERSON_NAME)
    assert document.section(photo_path.name).get("faces")


@pytest.mark.parametrize("height_delta", _HEIGHT_DELTAS)
def test_photo_dragged_onto_album_row_joins_the_album(
    dnd_qml_app, qt_app, height_delta
):
    """#5105: a rácsból a bal sáv album-sorára húzott kép az albumba kerül —
    valódi egérhúzással, a ledobási jel közvetlen hívása nélkül."""
    window, controller, engine = dnd_qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()

    library = Path(controller.currentFolder)
    photo_a = library / "a.jpg"
    photo_b = library / "b.jpg"
    controller.createAlbum("Húzás-album", [_path_row(controller, photo_a)])
    qt_app.processEvents()
    row_b = _path_row(controller, photo_b)
    window.setProperty("selectedIndexes", [row_b])
    _child(window, "photoGrid").setProperty("contentY", 0)
    qt_app.processEvents()

    album_drop = next(
        item
        for item in _walk(window.contentItem())
        if item.objectName().startswith("albumDropArea_")
    )
    source_proxy = _find_visual(
        window,
        "thumbDragProxy",
        predicate=lambda item: int(item.property("photoIndex")) == row_b,
    )
    source_mouse = _find_visual(
        window,
        "thumbMouseArea",
        predicate=lambda item: int(item.parentItem().property("index")) == row_b,
    )
    _real_drag(window, qt_app, engine, source_proxy, source_mouse, album_drop)

    def _albumai(name):
        section = load_or_empty(library / ".picasa.ini").section(name)
        return set(filter(None, (section.get("albums") if section else "").split(",")))

    album_tokens = _albumai("a.jpg")
    assert len(album_tokens) == 1, f"az előkészített album hiányzik: {album_tokens}"
    _wait(
        qt_app,
        lambda: _albumai("b.jpg") == album_tokens,
        "a rácsból az album sorára húzott kép nem került az albumba",
    )


@pytest.mark.parametrize("height_delta", _HEIGHT_DELTAS)
def test_photos_dragged_onto_new_album_area_create_an_album_with_them(
    dnd_qml_app, qt_app, height_delta
):
    """#5008: a rácsból az albumlista „új album" területére húzott kép új
    albumba kerül. A névbekérő párbeszéd a #2911 óta nincs meg, az album
    csendben „Untitled" nevet kap — valódi egérhúzással, a ledobási jel
    közvetlen hívása nélkül."""
    window, controller, engine = dnd_qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()

    library = Path(controller.currentFolder)
    photo_b = library / "b.jpg"
    assert len(controller.albums) == 0, "a teszt induló állapotában nincs album"
    row_b = _path_row(controller, photo_b)
    window.setProperty("selectedIndexes", [row_b])
    _child(window, "photoGrid").setProperty("contentY", 0)
    qt_app.processEvents()

    album_area = _find_visual(window, "albumDropArea")
    source_proxy = _find_visual(
        window,
        "thumbDragProxy",
        predicate=lambda item: int(item.property("photoIndex")) == row_b,
    )
    source_mouse = _find_visual(
        window,
        "thumbMouseArea",
        predicate=lambda item: int(item.parentItem().property("index")) == row_b,
    )
    _real_drag(window, qt_app, engine, source_proxy, source_mouse, album_area)

    _wait(
        qt_app,
        lambda: len(controller.albums) == 1,
        "a rácsról az új album területre húzott kép nem hozott létre albumot",
    )
    token = controller.albums[0]["token"]
    section = load_or_empty(library / ".picasa.ini").section("b.jpg")
    album_tokens = set(
        filter(None, (section.get("albums") if section else "").split(","))
    )
    assert token in album_tokens, (
        f"a húzott kép nem az új albumba került: {album_tokens}"
    )


@pytest.mark.parametrize("height_delta", _HEIGHT_DELTAS)
def test_tray_photo_dragged_onto_folder_row_moves_the_file(
    dnd_qml_app, qt_app, height_delta
):
    """#5105: a tálcán kijelölt kép a bal sáv mappasorára húzva átkerül a
    célmappába. Valódi egérhúzás, a ledobási jel közvetlen hívása nélkül."""
    window, controller, engine = dnd_qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()

    library = Path(controller.currentFolder)
    photo_a = library / "a.jpg"
    target_path = library / "cel"
    row_a = _path_row(controller, photo_a)
    window.setProperty("selectedIndexes", [row_a])
    _child(window, "photoGrid").setProperty("contentY", 0)
    qt_app.processEvents()

    # A tálca csak megtartott képeket mutat, ezért előbb a rácsról húzzuk be.
    source_proxy = _find_visual(
        window,
        "thumbDragProxy",
        predicate=lambda item: int(item.property("photoIndex")) == row_a,
    )
    source_mouse = _find_visual(
        window,
        "thumbMouseArea",
        predicate=lambda item: int(item.parentItem().property("index")) == row_a,
    )
    tray_strip = _child(window, "trayScratchStrip")
    _real_drag(window, qt_app, engine, source_proxy, source_mouse, tray_strip)
    _wait(
        qt_app,
        lambda: bool(controller.isHeldAt(row_a)),
        "a rácsból a tálcára húzott kép nem került a megtartott elemek közé",
    )

    controller.selectTrayIndex(0, False, False)
    qt_app.processEvents()
    tray_thumb = _find_visual(
        window,
        "trayPreviewThumb",
        predicate=lambda item: int(item.property("index")) == 0,
    )
    tray_proxy = next(
        item for item in _walk(tray_thumb) if item.objectName() == "trayDragProxy"
    )
    target_drop = _find_visual(window, "folderDropArea_" + str(target_path))
    assert target_drop.property("enabled") is True

    _real_drag(window, qt_app, engine, tray_proxy, tray_thumb, target_drop)

    moved = target_path / photo_a.name
    _wait(
        qt_app,
        lambda: moved.is_file() and not photo_a.exists(),
        "a tálcáról a mappasorra húzott kép nem került át a célmappába",
    )
    from picasapy.app.worker_thread import wait_for_all_background_workers

    assert wait_for_all_background_workers(30.0)
