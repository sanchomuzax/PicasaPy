"""A frissítési jelvény a márkakézikönyv színét és térközeit követi (#6473)."""

from __future__ import annotations

import os

import pytest
from PySide6.QtCore import QPointF, Property, QObject, Signal
from PySide6.QtGui import QColor
from PySide6.QtQuick import QQuickItem

from tests.support.varakozas import var_feltetelre


class _FakeUpdateController(QObject):
    updateAvailableChanged = Signal()

    @Property(bool, notify=updateAvailableChanged)
    def updateAvailable(self):  # noqa: N802
        return True

    @Property(str, notify=updateAvailableChanged)
    def availableVersion(self):  # noqa: N802
        return "1.0.29"

    @Property(str, notify=updateAvailableChanged)
    def releaseNotes(self):  # noqa: N802
        return "A rövid kiadási leírás."

    @Property(str, notify=updateAvailableChanged)
    def releaseUrl(self):  # noqa: N802
        return "https://example.test/release"

    @Property(bool, notify=updateAvailableChanged)
    def oneClickUpdateSupported(self):  # noqa: N802
        return False

    @Property(str, notify=updateAvailableChanged)
    def updateCommand(self):  # noqa: N802
        return ""

    @Property(bool, notify=updateAvailableChanged)
    def checking(self):
        return False

    @Property(int, notify=updateAvailableChanged)
    def downloadProgress(self):  # noqa: N802
        return 0

    @Property(str, notify=updateAvailableChanged)
    def downloadState(self):  # noqa: N802
        return "idle"

    @Property(bool, notify=updateAvailableChanged)
    def applicationBusy(self):  # noqa: N802
        return False


def _frissitesi_jelveny(qml_app, qt_app):
    window, _controller, engine = qml_app
    fake = _FakeUpdateController()
    engine.rootContext().setContextProperty("updateController", fake)
    assert var_feltetelre(
        qt_app,
        lambda: bool(window.findChild(QObject, "versionUpdateHighlight"))
        and window.findChild(QObject, "versionUpdateHighlight").property("visible"),
        3.0,
    ), "a frissítési jelvény nem jelent meg"
    badge = window.findChild(QObject, "versionUpdateHighlight")
    assert isinstance(badge, QQuickItem)
    return window, fake, badge


@pytest.mark.parametrize("height_offset", (-5, 0, 5))
def test_a_jelveny_jobb_margoja_egyezik_a_kereso_elotti_ressel(
    qml_app, qt_app, height_offset
):
    window, _fake, badge = _frissitesi_jelveny(qml_app, qt_app)
    window.resize(window.width(), 800 + height_offset)
    assert var_feltetelre(
        qt_app,
        lambda: window.height() == 800 + height_offset,
        3.0,
    ), "az ablakmagasság nem állt be"

    toolbar = window.findChild(QObject, "mainToolbar")
    search = window.findChild(QObject, "toolbarSearchBox")
    assert isinstance(toolbar, QQuickItem)
    assert isinstance(search, QQuickItem)

    toolbar_rect = badge.mapToItem(toolbar, QPointF(0, 0))
    search_rect = search.mapToItem(toolbar, QPointF(0, 0))
    jobb_margo = toolbar.width() - (toolbar_rect.x() + badge.width())
    keresotol_mert_res = toolbar_rect.x() - (search_rect.x() + search.width())
    assert jobb_margo == pytest.approx(4, abs=3)
    assert keresotol_mert_res == pytest.approx(jobb_margo, abs=3)


def _jelveny_keppontok(window, badge):
    image = window.grabWindow()
    assert not image.isNull(), "a főablak képe üres"
    scale_x = image.width() / window.width()
    scale_y = image.height() / window.height()
    badge_origin = badge.mapToScene(QPointF(0, 0))
    fill = QColor("#3478DB")
    fill_x = round((badge_origin.x() + badge.width() / 2) * scale_x)
    fill_y = round((badge_origin.y() + 1) * scale_y)
    corner_x = round((badge_origin.x() + 0.5) * scale_x)
    corner_y = round((badge_origin.y() + 0.5) * scale_y)
    return image, fill, (fill_x, fill_y), (corner_x, corner_y)


def test_a_jelveny_kitoltese_a_brandbook_markakeke(qml_app, qt_app):
    window, _fake, badge = _frissitesi_jelveny(qml_app, qt_app)
    image, fill, fill_point, _corner_point = _jelveny_keppontok(window, badge)
    assert image.pixelColor(*fill_point) == fill, (
        "a jelvény kitöltése nem a márkakézikönyv #3478DB márkakéke"
    )
    assert image.pixelColor(*_corner_point) != fill, (
        "a jelvény sarka nem követi a márkakézikönyv lekerekített címkeformáját"
    )

    bizonyitek = os.environ.get("PICASAPY_BIZONYITEK_KEP")
    if bizonyitek:
        image.save(bizonyitek)
