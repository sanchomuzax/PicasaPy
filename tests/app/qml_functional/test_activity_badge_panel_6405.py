"""A háttérmunka-jelző a keresőmezőtől jobbra, vele egy sorban áll (#6405).

Mérce: az eredeti Picasa képernyőképe (`research/testdata/screenshot/
2026-07-17 20 54 38.png`): az 1920 széles ablakban a keresőmező vége
x≈1872, a pörgő jelző x≈1888-1908, a mezővel egy sorban (y≈62). A mappafejléc
„Szinkronizálás az internettel” kapcsolója NEM a jelző szomszédja.
"""

from __future__ import annotations

import math
import os

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
def test_a_jelzo_a_keresomezotol_jobbra_vele_egy_sorban_all(qml_app, qt_app, height_offset):
    window, _controller, _engine = qml_app
    base_height = window.height()
    target_height = base_height + height_offset
    window.resize(window.width(), target_height)
    _wait(qt_app, lambda: window.height() == target_height, "az ablakmagasság nem állt be")

    root = window.contentItem().parentItem() or window.contentItem()
    badge = _find_item(root, "activityBadge")
    toolbar = _find_item(root, "mainToolbar")
    search_box = _find_item(root, "toolbarSearchBox")
    version = _find_item(root, "versionLabel")
    assert badge is not None, "az ActivityBadge nem épült fel"
    assert toolbar is not None and search_box is not None and version is not None
    assert _contains(toolbar, badge), "a jelző nem az eszközsáv része"

    registry = get_app_busy_registry()
    registry.begin()
    try:
        _wait(qt_app, badge.isVisible, "a működő háttérmunka nem mutatta a jelzőt")
        badge_rect = _item_rect(badge, root)
        search_rect = _item_rect(search_box, root)
        toolbar_rect = _item_rect(toolbar, root)
        assert badge.width() == 35 and badge.height() == 28
        # egy sorban: a függőleges közép egyezik
        assert abs(badge_rect.center().y() - search_rect.center().y()) <= 2
        # a mezőtől jobbra, rés nélküli ráfedés nélkül, az eszközsáv jobb szélén
        assert badge_rect.left() >= search_rect.right() + 3
        assert abs(badge_rect.right() - (toolbar_rect.right() - 5)) <= 2
        # a verziófelirat átadja a helyét
        assert not version.isVisible(), "a verziófelirat a jelzővel együtt látszik"

        for name in ("searchField", "toolbarImportButton", "toolbarNewAlbumButton"):
            item = _find_item(root, name)
            assert item is not None, f"a szomszédos elem nem található: {name}"
            if item.isVisible() and item.width() > 0 and item.height() > 0:
                assert not badge_rect.adjusted(-2, -2, 2, 2).intersects(
                    _item_rect(item, root)
                ), f"a jelző ráfed a(z) {name} elemre"

        spinner = _find_item(root, "activityBadgeSpinner")
        assert spinner is not None and spinner.isVisible(), "a pörgő ábra nem látszik"
        from PySide6.QtTest import QTest

        QTest.qWait(400)  # a pörgő animáció néhány képkockája, hogy a képen is látsszon
        window.update()
        image = window.grabWindow()
        assert not image.isNull(), "a főablak renderelése üres"
        scale_x = image.width() / window.width()
        scale_y = image.height() / window.height()
        left = max(0, math.floor(badge_rect.left() * scale_x))
        top = max(0, math.floor(badge_rect.top() * scale_y))
        right = min(image.width(), math.ceil(badge_rect.right() * scale_x))
        bottom = min(image.height(), math.ceil(badge_rect.bottom() * scale_y))
        rendered_colors = {
            image.pixelColor(x, y).rgba()
            for y in range(top, bottom)
            for x in range(left, right)
        }
        assert len(rendered_colors) > 1, "a jelző nem látszik a kirajzolt főablakban"
        celfajl = os.environ.get("PICASAPY_BIZONYITEK_KEP")
        if celfajl and height_offset == 0:
            image.save(celfajl)
    finally:
        registry.end()
    _wait(qt_app, lambda: not badge.isVisible(), "a munka végén a jelző nem tűnt el")
    _wait(qt_app, version.isVisible, "a munka végén a verziófelirat nem jött vissza")
