"""Az effekt-csempék előnézete minden láncmódosítás után frissül (#4561)."""

from __future__ import annotations

from urllib.parse import unquote

import pytest
from PySide6.QtCore import (
    QObject,
    QPoint,
    QPointF,
    Property,
    Qt,
    QUrl,
    QUrlQuery,
    Signal,
    Slot,
)
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre

_KEEPALIVE: list[object] = []
_EFFECT_GRIDS = (
    (2, "effectsGrid", 12),
    (3, "effectsGrid2", 12),
    (4, "effectsGrid3", 12),
    (5, "effectsGrid4", 5),
)


class _EditController(QObject):
    """A valódi QML-jelutat kiszolgáló, szálmentes szerkesztési csonk."""

    revisionChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._filters: list[str] = []
        self._revision = 0

    @Property(str, notify=revisionChanged)
    def previewSource(self) -> str:
        return f"image://editpreview/42?rev={self._revision}"

    @Property(str, notify=revisionChanged)
    def effectChain(self) -> str:
        return "".join(f"{name}=1;" for name in self._filters)

    @Property("QVariant", notify=revisionChanged)
    def effectChainCounts(self) -> dict[str, int]:
        return {name: self._filters.count(name) for name in set(self._filters)}

    @Property("QVariant", constant=True)
    def oneClickEffects(self) -> list[str]:
        return ["bw", "sepia", "warm", "invert"]

    @Property("QVariantList", constant=True)
    def legacyEffectsInChain(self) -> list[str]:
        return []

    @Property(bool, constant=True)
    def shiftAktiv(self) -> bool:
        return False

    @Slot(str, result=bool)
    def effectHasParams(self, name: str) -> bool:
        return False

    @Slot(str)
    def applyEffect(self, name: str) -> None:
        self._filters.append(name.casefold())
        self._revision += 1
        self.revisionChanged.emit()


def _source(item: QObject) -> str:
    value = item.property("source")
    return value.toString() if hasattr(value, "toString") else str(value)


def _grid_thumbnails(panel: QObject, grid_name: str) -> list[QObject]:
    grid = panel.findChild(QObject, grid_name)
    if grid is None:
        return []
    return [
        image
        for image in grid.findChildren(QObject)
        if image.objectName().startswith("effect")
        and image.objectName().endswith("Thumb")
    ]


def _chain_in_url(source: str) -> str:
    return unquote(QUrlQuery(QUrl(source)).queryItemValue("filters"))


def _grid_shows_chain(
    panel: QObject, grid_name: str, expected_count: int, chain: str
) -> bool:
    thumbnails = _grid_thumbnails(panel, grid_name)
    return len(thumbnails) == expected_count and all(
        _chain_in_url(_source(image)) == chain for image in thumbnails
    )


def _click(view: QQuickView, button: QObject, qt_app) -> None:
    """Kattintás a felépült csempe tényleges, jelenetbeli középpontjára."""
    center = button.mapToScene(
        QPointF(button.width() / 2, button.height() / 2)
    )
    QTest.mouseClick(
        view,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("height", [695, 700, 705])
def test_two_effect_clicks_refresh_every_tile_from_the_current_chain(
    qt_app, height
):
    """Két valódi csempekattintás után mind a négy effektfül az új láncot kéri.

    A `filters` URL-paraméter jelzi a termék képszolgáltatójának az aktuális
    szerkesztési láncot. A teszt szolgáltató szinkron, ezért a felületi kötést
    méri, a lassú képszámítást nem.
    """
    import picasapy.app.application as app_module

    view = QQuickView()
    engine = view.engine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    edit_controller = _EditController()
    engine.rootContext().setContextProperty("editController", edit_controller)
    engine.rootContext().setContextProperty("controller", None)

    from PySide6.QtQml import QQmlComponent

    component = QQmlComponent(engine)
    component.setData(
        b'import QtQuick\nimport PicasaPy 1.0\n'
        b'EditorPanel { objectName: "panel"; activeTab: 2 }\n',
        QUrl(),
    )
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors
    panel = component.create()
    assert panel is not None
    panel.setParentItem(view.contentItem())
    panel.setWidth(280)
    panel.setHeight(height)
    view.resize(280, height)
    view.show()
    _KEEPALIVE.extend((view, component, panel, edit_controller))

    try:
        qt_app.processEvents()
        panel.effectRequested.connect(edit_controller.applyEffect)

        # Az aktív fül valódi csempéi már kirajzolódtak és betöltöttek.
        thumbnails = _grid_thumbnails(panel, "effectsGrid")
        assert len(thumbnails) == 12, "az első effektfül 12 csempéje nem épült fel"
        before = {image.objectName(): _source(image) for image in thumbnails}

        # A fekete-fehér és a szépia paraméter nélküli, egy kattintásos effektek.
        bw = panel.findChild(QObject, "effectBw")
        sepia = panel.findChild(QObject, "effectSepia")
        assert bw is not None and sepia is not None
        _click(view, bw, qt_app)
        assert varj_feltetelre(
            qt_app,
            lambda: edit_controller.effectChainCounts == {"bw": 1},
            3.0,
        ), "a fekete-fehér csempére kattintás nem alkalmazta az effektet"

        for tab, grid_name, expected_count in _EFFECT_GRIDS:
            panel.setProperty("activeTab", tab)
            assert varj_feltetelre(
                qt_app,
                lambda grid_name=grid_name, expected_count=expected_count: _grid_shows_chain(
                    panel, grid_name, expected_count, "bw=1;"
                ),
                3.0,
            ), f"a(z) {grid_name} csempéi nem a friss fekete-fehér láncot mutatják"

        # Vissza az első fülre, majd a második valódi kattintás.
        panel.setProperty("activeTab", 2)
        assert varj_feltetelre(
            qt_app, lambda: panel.findChild(QObject, "effectSepia") is not None, 3.0
        )
        sepia = panel.findChild(QObject, "effectSepia")
        _click(view, sepia, qt_app)
        assert varj_feltetelre(
            qt_app,
            lambda: edit_controller.effectChainCounts == {"bw": 1, "sepia": 1},
            3.0,
        ), "a szépia csempére kattintás nem fűzte hozzá a második effektet"

        for tab, grid_name, expected_count in _EFFECT_GRIDS:
            panel.setProperty("activeTab", tab)
            assert varj_feltetelre(
                qt_app,
                lambda grid_name=grid_name, expected_count=expected_count: _grid_shows_chain(
                    panel, grid_name, expected_count, "bw=1;sepia=1;"
                ),
                3.0,
            ), f"a(z) {grid_name} csempéi nem a két effekt utáni láncot mutatják"

        assert all(
            _source(image) != before[image.objectName()]
            for image in _grid_thumbnails(panel, "effectsGrid")
        ), "az első effektfül csempe-URL-je nem változott az alkalmazás után"
    finally:
        qt_app.processEvents()
        view.close()
        view.deleteLater()
        qt_app.processEvents()
