"""Valódi mappasorra ejtés és fájl-vágólap a QML-felületen (#5007)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import (
    QPoint,
    QPointF,
    QMetaObject,
    QObject,
    Qt,
)
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from picasapy.ini import load_or_empty, parse_document, save_document
from support.jpeg_factory import make_jpeg


def _keszits_atviteli_mappakat(root: Path) -> None:
    source = root / "forras"
    target = root / "cel"
    source.mkdir()
    target.mkdir()
    make_jpeg(source / "atvitt-a.jpg", size=(64, 64))
    make_jpeg(source / "atvitt-b.jpg", size=(64, 64))
    make_jpeg(target / "marad.jpg", size=(64, 64))

    document = parse_document("")
    document = document.with_value("atvitt-a.jpg", "caption", "Megőrzendő felirat A")
    document = document.with_value("atvitt-a.jpg", "star", "1")
    document = document.with_value("atvitt-b.jpg", "caption", "Megőrzendő felirat B")
    document = document.with_value("atvitt-b.jpg", "star", "1")
    save_document(document, source / ".picasa.ini")


@pytest.fixture
def ketmappas_qml_app(qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_atviteli_mappakat,
        keep_modul=request.module,
    )


def _varj(qt_app, feltetel, leiras: str, timeout: float = 10.0) -> None:
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
        if item.property("kind") == "folder" and Path(item.property("path") or "") == path:
            return item
    raise AssertionError(f"A mappasor nem található: {path}")


def _ablakpont(window, item) -> QPoint:
    scene_point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    return QPoint(round(scene_point.x()), round(scene_point.y()))


def _mappat_kivalaszt(window, controller, qt_app, path: Path) -> None:
    row = _mappasor(window, path)
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _ablakpont(window, row),
    )
    _varj(
        qt_app,
        lambda: Path(controller.currentFolder or "") == path,
        f"a kiválasztott mappa {path} legyen",
    )


def _kep_sora(controller, kep: Path) -> int:
    # #5556: a rács a könyvtár összes képét mutatja, a sorrendjük gépfüggő,
    # ezért a sort az útvonal alapján keressük.
    utvonalak = _racs_utvonalai(controller)
    assert kep in utvonalak, f"a kép nincs a rácsban: {kep}"
    return utvonalak.index(kep)


def _kepek_kijelolese(
    window, controller, qt_app, source: Path, nevek: tuple[str, ...]
) -> list[int]:
    _mappat_kivalaszt(window, controller, qt_app, source)
    kijelolt_sorok = sorted(_kep_sora(controller, source / nev) for nev in nevek)
    window.setProperty("selectedIndexes", kijelolt_sorok)
    qt_app.processEvents()
    assert list(window.property("selectedIndexes")) == kijelolt_sorok
    return kijelolt_sorok


def _elso_kep_kijelolese(window, controller, qt_app, source: Path) -> Path:
    _kepek_kijelolese(window, controller, qt_app, source, ("atvitt-a.jpg",))
    return source / "atvitt-a.jpg"


def _racs_utvonalai(controller) -> list[Path]:
    photos = controller.photos
    return [Path(photos.filePathAt(row)) for row in range(photos.rowCount())]


def _fileops(engine):
    return engine.rootContext().contextProperty("fileOpsController")


def _attached_drag(item):
    return next(
        child
        for child in item.children()
        if child.metaObject().className() == "QQuickDragAttached"
    )


def _menu_tetel(window, name):
    item = window.findChild(QObject, name)
    assert item is not None, f"A menütétel nem található: {name}"
    return item


def _menu_elsutese(item) -> None:
    QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)


class TestMappasorraHuzas:
    @pytest.mark.parametrize("height_delta", (-5, 0, 5))
    def test_valodi_egerhuzas_atmozgatja_a_fajlt_es_az_ini_bejegyzest(
        self, ketmappas_qml_app, qt_app, height_delta
    ):
        window, controller, engine = ketmappas_qml_app
        window.resize(window.width(), window.height() + height_delta)
        qt_app.processEvents()
        source = Path(controller.currentFolder) / "forras"
        target = source.parent / "cel"
        kijelolt_sorok = _kepek_kijelolese(
            window, controller, qt_app, source, ("atvitt-a.jpg", "atvitt-b.jpg")
        )
        huzott_sor = kijelolt_sorok[0]
        source_photos = [source / "atvitt-a.jpg", source / "atvitt-b.jpg"]
        target_photos = [target / path.name for path in source_photos]
        revision = controller.photos.revision

        mouse_area = next(
            item
            for item in _latvanyelemek(window.contentItem())
            if item.objectName() == "thumbMouseArea"
            and int(item.parentItem().property("index")) == huzott_sor
        )
        drag_proxy = next(
            item
            for item in _latvanyelemek(window.contentItem())
            if item.objectName() == "thumbDragProxy"
            and int(item.property("photoIndex")) == huzott_sor
        )
        drop_area = next(
            item
            for item in _latvanyelemek(window.contentItem())
            if item.objectName() == f"folderDropArea_{target}"
        )
        # #5105: a termék húzási módját a teszt NEM írja át — pontosan azt
        # húzzuk, amit a felhasználó.
        start = _ablakpont(window, mouse_area)
        end = _ablakpont(window, _mappasor(window, target))

        QTest.mouseMove(window, start)
        QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
        qt_app.processEvents()
        assert mouse_area.property("pressed") is True, (
            f"a lenyomás nem a rács képére érkezett: {start}"
        )
        delta = end - start
        distance = max(abs(delta.x()), abs(delta.y()))
        steps = max(1, (distance + 3) // 4)
        for step in range(1, steps + 1):
            point = start + QPoint(
                round(delta.x() * step / steps),
                round(delta.y() * step / steps),
            )
            QTest.mouseMove(window, point)
            qt_app.processEvents()
        assert mouse_area.property("dragging") is True, (
            "a valódi egérmozgás nem indította el a kijelölt kép húzását: "
            f"pressed={mouse_area.property('pressed')}, "
            f"selected={mouse_area.parentItem().property('selected')}"
        )
        assert _attached_drag(drag_proxy).property("active") is True, (
            "a húzóforrás nem lett aktív"
        )
        row_payload = drag_proxy.property("photoRows")
        if hasattr(row_payload, "toVariant"):
            row_payload = row_payload.toVariant()
        photo_rows = [int(row) for row in row_payload]
        assert sorted(photo_rows) == kijelolt_sorok
        assert drop_area.property("enabled") is True
        QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=end)

        # #5105: a ledobást a DropArea-nak kell elkapnia — a jelet a teszt
        # nem hívja közvetlenül.
        _varj(
            qt_app,
            lambda: all(path.exists() for path in target_photos)
            and all(not path.exists() for path in source_photos),
            "a kijelölt képek a célmappába kerüljenek át",
        )
        target_document = load_or_empty(target / ".picasa.ini")
        source_document = load_or_empty(source / ".picasa.ini")
        for photo, caption in zip(
            source_photos,
            ("Megőrzendő felirat A", "Megőrzendő felirat B"),
            strict=True,
        ):
            assert target_document.section(photo.name).get("caption") == caption
            assert target_document.section(photo.name).get("star") == "1"
            assert source_document.section(photo.name) is None

        _varj(
            qt_app,
            lambda: controller.photos.revision > revision
            and all(
                path not in _racs_utvonalai(controller)
                for path in source_photos
            ),
            "a fájlművelet után a rács frissüljön",
        )
        assert _fileops(engine) is not None


class TestFajlVagolap:
    def test_ctrl_c_mappavalasztas_ctrl_v_atmasolja_a_fajlt(
        self, ketmappas_qml_app, qt_app
    ):
        window, controller, engine = ketmappas_qml_app
        source = Path(controller.currentFolder) / "forras"
        target = source.parent / "cel"
        source_photo = _elso_kep_kijelolese(window, controller, qt_app, source)
        target_photo = target / source_photo.name

        QTest.keyClick(window, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        qt_app.processEvents()
        _mappat_kivalaszt(window, controller, qt_app, target)
        QTest.keyClick(window, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)

        _varj(
            qt_app,
            lambda: target_photo.exists()
            and target_photo in _racs_utvonalai(controller),
            "a Ctrl+V másolja a képet és a rács frissül",
        )
        assert source_photo.exists(), "a Ctrl+C/Ctrl+V nem mozgathatja el a forrást"
        assert target_photo in _racs_utvonalai(controller)
        assert controller.currentFolder == str(target)

    def test_masolas_es_beillesztes_menuponttal_is_fajlt_masol(
        self, ketmappas_qml_app, qt_app
    ):
        window, controller, _engine = ketmappas_qml_app
        source = Path(controller.currentFolder) / "forras"
        target = source.parent / "cel"
        source_photo = _elso_kep_kijelolese(window, controller, qt_app, source)
        target_photo = target / source_photo.name

        _menu_elsutese(_menu_tetel(window, "menuEditCopy"))
        qt_app.processEvents()
        _mappat_kivalaszt(window, controller, qt_app, target)
        paste_item = _menu_tetel(window, "menuEditPaste")
        assert paste_item.property("enabled") is True
        _menu_elsutese(paste_item)

        _varj(
            qt_app,
            lambda: target_photo.exists()
            and target_photo in _racs_utvonalai(controller),
            "a Szerkesztés ▸ Beillesztés másol és a rács frissül",
        )
        assert source_photo.exists(), "a menüs másolásnak meg kell őriznie a forrást"
        assert target_photo in _racs_utvonalai(controller)
        assert controller.currentFolder == str(target)
