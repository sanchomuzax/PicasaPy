"""A háttérmunka-jelző megszakító gombja a pörgő MELLÉ kerül (#6474).

A tulajdonos döntése (2026-11-03, #6474): a gomb ne a pörgőre lógjon, mert a
fedés rosszul néz ki. Megszakítható munkánál a jelző szélesebb: a pörgő balra,
a gomb jobbra áll, köztük rés van. Megszakíthatatlan munkánál marad a mért
35 × 28, a pörgő középen.

A keresőmezőt a jelző nem takarhatja: a mező jobb széle a MainToolbar-ban
(`searchBoxRight`) van rögzítve, ezért az a teszt a jelenlegi állapotban
bukhat - lásd a jelentést.
"""

from __future__ import annotations

import os

import pytest
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtTest import QTest

import picasapy.app.busy_registry as busy_registry_module
from picasapy.app.busy_registry import get_app_busy_registry, reset_app_busy_registry
from tests.support.varakozas import var_feltetelre

_KERET_MERET = (35, 28)
_RESS_RES_PX = 2
_KEREKTO_RES_PX = 3
_RENDER_FAJLNEV = "activity-badge-6474.png"


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
    left = max(0, int(rect.left() * scale_x))
    top = max(0, int(rect.top() * scale_y))
    right = min(image.width(), int(rect.right() * scale_x) + 1)
    bottom = min(image.height(), int(rect.bottom() * scale_y) + 1)
    return {
        image.pixelColor(x, y).rgba()
        for y in range(top, bottom)
        for x in range(left, right)
    }


def _keresd_az_elemeket(window):
    root = window.contentItem().parentItem() or window.contentItem()
    elemek = {
        nev: _find_item(root, nev)
        for nev in (
            "activityBadge",
            "activityBadgeFrame",
            "activityBadgeSpinner",
            "activityBadgeCancel",
            "mainToolbar",
            "toolbarSearchBox",
        )
    }
    for nev, elem in elemek.items():
        assert elem is not None, f"{nev} nem található"
    return root, elemek


def test_megszakithato_munkanal_a_gomb_a_porgo_mellett_all(qml_app, qt_app):
    window, _controller, _engine = qml_app
    root, e = _keresd_az_elemeket(window)
    registry = get_app_busy_registry()

    registry.begin()
    jegy = registry.register_cancel(lambda: None)
    try:
        _wait(
            qt_app,
            lambda: e["activityBadge"].isVisible() and e["activityBadgeCancel"].isVisible(),
            "a leállítható munka nem hozta elő a jelzőt és a gombot",
        )
        badge_rect = _item_rect(e["activityBadge"], root)
        frame_rect = _item_rect(e["activityBadgeFrame"], root)
        spinner_rect = _item_rect(e["activityBadgeSpinner"], root)
        cancel_rect = _item_rect(e["activityBadgeCancel"], root)

        assert e["activityBadge"].height() == 28
        assert frame_rect.contains(spinner_rect), "a pörgő kilóg a jelző keretéből"
        assert frame_rect.contains(cancel_rect), "a megszakító gomb kilóg a jelző keretéből"
        assert spinner_rect.right() + _RESS_RES_PX <= cancel_rect.left(), (
            "a pörgő és a megszakító gomb fedi egymást, vagy túl közel van"
        )
        assert abs(spinner_rect.center().y() - cancel_rect.center().y()) <= 1
        assert abs(badge_rect.center().y() - spinner_rect.center().y()) <= 1

        QTest.qWait(400)  # a pörgő néhány képkockája, hogy a képen is látsszon
        window.update()
        image = window.grabWindow()
        assert not image.isNull(), "a főablak renderelése üres"
        for nev, rect in (("pörgő", spinner_rect), ("gomb", cancel_rect)):
            assert len(_renderelt_szinek(image, window, rect)) > 1, (
                f"a(z) {nev} nem látszik a kirajzolt főablakban"
            )
        kimenet = os.environ.get("PICASAPY_RENDER_KIMENET")
        if kimenet:
            os.makedirs(kimenet, exist_ok=True)
            image.save(os.path.join(kimenet, _RENDER_FAJLNEV))
    finally:
        registry.unregister_cancel(jegy)
        registry.end()
    _wait(qt_app, lambda: not e["activityBadge"].isVisible(), "a munka végén a jelző nem tűnt el")


def test_megszakithatatlan_munkanal_35x28_es_kozepen_a_porgo(qml_app, qt_app):
    window, _controller, _engine = qml_app
    root, e = _keresd_az_elemeket(window)
    registry = get_app_busy_registry()

    registry.begin()
    try:
        _wait(qt_app, e["activityBadge"].isVisible, "a működő háttérmunka nem mutatta a jelzőt")
        assert (e["activityBadge"].width(), e["activityBadge"].height()) == _KERET_MERET
        assert not e["activityBadgeCancel"].isVisible(), (
            "megszakíthatatlan munkánál látszik a megszakító gomb"
        )
        badge_rect = _item_rect(e["activityBadge"], root)
        spinner_rect = _item_rect(e["activityBadgeSpinner"], root)
        assert abs(spinner_rect.center().x() - badge_rect.center().x()) <= 1
        assert abs(spinner_rect.center().y() - badge_rect.center().y()) <= 1
    finally:
        registry.end()
    _wait(qt_app, lambda: not e["activityBadge"].isVisible(), "a munka végén a jelző nem tűnt el")


def test_a_szelesebb_jelzo_nem_takarja_a_keresomezot(qml_app, qt_app):
    window, _controller, _engine = qml_app
    root, e = _keresd_az_elemeket(window)
    registry = get_app_busy_registry()

    registry.begin()
    jegy = registry.register_cancel(lambda: None)
    try:
        _wait(
            qt_app,
            lambda: e["activityBadge"].isVisible() and e["activityBadgeCancel"].isVisible(),
            "a leállítható munka nem hozta elő a jelzőt és a gombot",
        )
        badge_rect = _item_rect(e["activityBadge"], root)
        search_rect = _item_rect(e["toolbarSearchBox"], root)
        toolbar_rect = _item_rect(e["mainToolbar"], root)
        assert badge_rect.left() >= search_rect.right() + _KEREKTO_RES_PX, (
            "a megszakítható jelző ráfed a keresőmezőre"
        )
        assert abs(badge_rect.right() - (toolbar_rect.right() - 5)) <= 2
    finally:
        registry.unregister_cancel(jegy)
        registry.end()
    _wait(qt_app, lambda: not e["activityBadge"].isVisible(), "a munka végén a jelző nem tűnt el")
