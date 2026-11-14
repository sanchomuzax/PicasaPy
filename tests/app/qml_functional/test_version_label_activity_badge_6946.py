"""A jobb felső verziócímke háttérmunka közben is látszódjon a háttérjelző mellett (#6946).

Kész, ha:
- [ ] A verziócímke háttérmunka közben is látszik; a háttérjelző mellette kap helyet, nem helyette, és nem lóg a keresőmezőre.
- [ ] Renderelt teszt: futó háttérmunka mellett a versionLabel látható, és nem fedi a háttérjelzőt.
"""

from __future__ import annotations

import math
import pytest
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtTest import QTest

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


def _wait(qt_app, predicate, message: str) -> None:
    assert var_feltetelre(qt_app, predicate, 3.0), message


def _item_rect(item, scene_root) -> QRectF:
    point = item.mapToItem(scene_root, QPointF(0, 0))
    return QRectF(point.x(), point.y(), item.width(), item.height())


def _renderelt_szinek(image, window, rect: QRectF) -> set[int]:
    scale_x = image.width() / window.width()
    scale_y = image.height() / window.height()
    left = max(0, math.floor(rect.left() * scale_x))
    top = max(0, math.floor(rect.top() * scale_y))
    right = min(image.width(), math.ceil(rect.right() * scale_x))
    bottom = min(image.height(), math.ceil(rect.bottom() * scale_y))
    return {
        image.pixelColor(x, y).rgba()
        for y in range(top, bottom)
        for x in range(left, right)
    }


@pytest.mark.parametrize("height_offset", _HEIGHT_OFFSETS)
def test_a_verziocimke_hattermunka_mellett_is_latszik_nem_fedi_a_jelzot_es_nem_log_a_keresore(
    qml_app, qt_app, height_offset
):
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
    assert toolbar is not None, "a mainToolbar nem épült fel"
    assert search_box is not None, "a toolbarSearchBox nem épült fel"
    assert version is not None, "a versionLabel nem épült fel"

    # Alapállapotban (munka nélkül) a verziófelirat látszik, a badge rejtve
    assert version.isVisible(), "a verziófelirat alapállapotban nem látszik"
    assert not badge.isVisible(), "a háttérjelző munka nélkül látszik"

    registry = get_app_busy_registry()
    registry.begin()
    try:
        _wait(qt_app, badge.isVisible, "a működő háttérmunka nem mutatta a jelzőt")
        # #6946: A verziócímke háttérmunka közben is látszik
        assert version.isVisible(), "a verziócímke háttérmunka közben eltűnt (#6946)"

        badge_rect = _item_rect(badge, root)
        search_rect = _item_rect(search_box, root)
        version_rect = _item_rect(version, root)
        toolbar_rect = _item_rect(toolbar, root)

        # A háttérjelző helye (#6405 / #3112): jobb felül, felülről és jobbról 5 px
        assert abs(badge_rect.right() - (toolbar_rect.right() - 5)) <= 2

        # A verziócímke a háttérjelző mellett, attól balra kap helyet, nem fedi
        assert version_rect.right() <= badge_rect.left() - 2, (
            f"a verziócímke fedi a háttérjelzőt vagy nem tőle balra áll: "
            f"version right={version_rect.right()}, badge left={badge_rect.left()}"
        )
        assert not version_rect.intersects(badge_rect), "a verziócímke és a háttérjelző metszi egymást"

        # A keresőmező a verziócímkétől balra ér véget, nem lóg a verziócímkére
        assert search_rect.right() <= version_rect.left() - 2, (
            f"a keresőmező a verziócímkére lóg: "
            f"search right={search_rect.right()}, version left={version_rect.left()}"
        )
        assert not search_rect.intersects(version_rect), "a keresőmező és a verziócímke metszi egymást"

        # Renderelt (képernyőképes) ellenőrzés
        QTest.qWait(400)
        window.update()
        image = window.grabWindow()
        assert not image.isNull(), "a főablak renderelése üres"

        version_colors = _renderelt_szinek(image, window, version_rect)
        assert len(version_colors) > 1, "a verziócímke nem látszik a kirajzolt főablakban"

        badge_colors = _renderelt_szinek(image, window, badge_rect)
        assert len(badge_colors) > 1, "a háttérjelző nem látszik a kirajzolt főablakban"
    finally:
        registry.end()

    _wait(qt_app, lambda: not badge.isVisible(), "a munka végén a jelző nem tűnt el")
    _wait(qt_app, version.isVisible, "a munka végén a verziófelirat nem maradt látható")


def test_megszakithato_munkanal_is_latszik_a_verzio_a_szelesebb_jelzo_mellett(qml_app, qt_app):
    window, _controller, _engine = qml_app
    root = window.contentItem().parentItem() or window.contentItem()
    badge = _find_item(root, "activityBadge")
    search_box = _find_item(root, "toolbarSearchBox")
    version = _find_item(root, "versionLabel")

    assert badge is not None and search_box is not None and version is not None

    registry = get_app_busy_registry()
    registry.begin()
    jegy = registry.register_cancel(lambda: None)
    try:
        _wait(qt_app, badge.isVisible, "a megszakítható háttérmunka nem mutatta a jelzőt")
        assert version.isVisible(), "a verziócímke megszakítható munka közben eltűnt (#6946)"

        badge_rect = _item_rect(badge, root)
        search_rect = _item_rect(search_box, root)
        version_rect = _item_rect(version, root)

        # Megszakítható munkánál a jelző szélesebb (54 px)
        assert badge.width() > 35

        # Verziócímke és badge nem fedik egymást
        assert version_rect.right() <= badge_rect.left() - 2
        assert not version_rect.intersects(badge_rect)

        # Keresőmező és verziócímke nem fedik egymást
        assert search_rect.right() <= version_rect.left() - 2
        assert not search_rect.intersects(version_rect)
    finally:
        registry.unregister_cancel(jegy)
        registry.end()

    _wait(qt_app, lambda: not badge.isVisible(), "a munka végén a jelző nem tűnt el")
