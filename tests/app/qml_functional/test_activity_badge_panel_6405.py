"""A háttérmunka-jelző a könyvtárnézet paneljéhez igazodik (#6405)."""

from __future__ import annotations

import math

import pytest
from PySide6.QtCore import QPointF, QRectF

import picasapy.app.busy_registry as busy_registry_module
from picasapy.app.busy_registry import get_app_busy_registry, reset_app_busy_registry
from tests.support.varakozas import var_feltetelre

_HEIGHT_OFFSETS = (-5, 0, 5)


@pytest.fixture(autouse=True)
def _kis_busy_idozitesek(monkeypatch):
    monkeypatch.setattr(busy_registry_module, "SHOW_DELAY_MS", 40)
    monkeypatch.setattr(busy_registry_module, "MIN_VISIBLE_MS", 60)
    reset_app_busy_registry()
    yield
    reset_app_busy_registry()


def _find_item(root, object_name: str):
    if root.objectName() == object_name:
        return root
    for child in root.childItems():
        found = _find_item(child, object_name)
        if found is not None:
            return found
    return None


def _contains(root, candidate) -> bool:
    for child in root.childItems():
        if child == candidate or _contains(child, candidate):
            return True
    return False


def _wait(qt_app, predicate, message: str) -> None:
    assert var_feltetelre(qt_app, predicate, 3.0), message


def _item_rect(item, scene_root) -> QRectF:
    point = item.mapToItem(scene_root, QPointF(0, 0))
    return QRectF(point.x(), point.y(), item.width(), item.height())


@pytest.mark.parametrize("height_offset", _HEIGHT_OFFSETS)
def test_a_jelzo_a_konyvtari_panelhez_igazodik_es_nem_takar_vezerlot(
    qml_app, qt_app, height_offset
):
    window, _controller, _engine = qml_app
    base_height = window.height()
    target_height = base_height + height_offset
    window.resize(window.width(), target_height)
    _wait(qt_app, lambda: window.height() == target_height, "az ablakmagasság nem állt be")

    window.setProperty("unnamedFacesOpen", True)
    badge = _find_item(window.contentItem(), "activityBadge")
    face_view = _find_item(window.contentItem(), "unnamedFacesView")
    face_header = _find_item(window.contentItem(), "unknownFaceViewHeader")
    assert badge is not None, "az ActivityBadge nem épült fel"
    assert face_view is not None, "a könyvtárnézet tartalma nem épült fel"
    assert face_header is not None, "az Emberek-nézet fejléce nem épült fel"
    panel = badge.parentItem()

    _wait(qt_app, face_view.isVisible, "az Emberek-nézet nem vált láthatóvá")
    _wait(qt_app, face_header.isVisible, "az Emberek-nézet fejléce nem látható")
    assert panel != window.contentItem(), "a jelző a teljes ablakrétegben maradt"
    assert _contains(panel, face_view), "a jelző szülője nem a könyvtárnézet panelje"

    registry = get_app_busy_registry()
    registry.begin()
    try:
        _wait(qt_app, badge.isVisible, "a működő háttérmunka nem mutatta a jelzőt")
        _wait(
            qt_app,
            lambda: face_header.width() <= face_view.width() - 40,
            "az Emberek-fejléc nem hagyott helyet a jelzőnek",
        )

        local = badge.mapToItem(panel, QPointF(0, 0))
        assert abs(local.x() - (panel.width() - 40)) <= 3
        assert abs(local.y() - 5) <= 3
        assert badge.width() == 35
        assert badge.height() == 28

        badge_rect = _item_rect(badge, window.contentItem()).adjusted(-3, -3, 3, 3)
        neighbors = (
            "searchField",
            "toolbarImportButton",
            "toolbarNewAlbumButton",
            "toolbarFolderViewToggle",
            "toolbarFolderViewPopupButton",
            "toolbarWebcamCaptureButton",
            "unknownFaceViewHeader",
        )
        for name in neighbors:
            item = _find_item(window.contentItem(), name)
            assert item is not None, f"a szomszédos elem nem található: {name}"
            if item.isVisible() and item.width() > 0 and item.height() > 0:
                assert not badge_rect.intersects(_item_rect(item, window.contentItem())), (
                    f"a jelző ráfed a(z) {name} elemre"
                )

        people_panel_header = _find_item(window.contentItem(), "peoplePanelHeader")
        if people_panel_header is not None and people_panel_header.isVisible():
            assert not badge_rect.intersects(
                _item_rect(people_panel_header, window.contentItem())
            ), "a jelző ráfed az Emberek panel fejlécére"

        window.update()
        image = window.grabWindow()
        assert not image.isNull(), "a főablak renderelése üres"
        badge_scene = badge.mapToScene(QPointF(0, 0))
        scale_x = image.width() / window.width()
        scale_y = image.height() / window.height()
        left = max(0, math.floor(badge_scene.x() * scale_x))
        top = max(0, math.floor(badge_scene.y() * scale_y))
        right = min(image.width(), math.ceil((badge_scene.x() + badge.width()) * scale_x))
        bottom = min(image.height(), math.ceil((badge_scene.y() + badge.height()) * scale_y))
        rendered_colors = {
            image.pixelColor(x, y).rgba()
            for y in range(top, bottom)
            for x in range(left, right)
        }
        assert len(rendered_colors) > 1, "a jelző nem látszik a kirajzolt főablakban"
    finally:
        registry.end()
