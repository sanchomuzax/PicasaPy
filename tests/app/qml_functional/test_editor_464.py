"""QML-funkcionális tesztek: az 1. fül ("Gyakori javítások") pontos
gombkészlete és sorrendje, a #464-es jegy szerint.

A jegy (a tulajdonos issue-szövege, `docs/specs/ui-audit-editor.md`
kiegészítéseként) rögzíti a sorrendet:

    Kivágás -> Vörösszem -> Jó napom van -> Kreatív Kit ->
    Automatikus szín -> Automatikus kontraszt -> Derítőfény-csúszka ->
    Kiegyenesítés -> Szöveg -> Retusálás

Ebből két konkrét eltérés van a korábbi (#411-es) implementációhoz képest:
1. az "Automatikus szín" (autocolor) a "Automatikus kontraszt" (autolight)
   ELŐTT áll (korábban fordítva volt),
2. a "Kreatív Kit" (a Picnik külső szerkesztő) gomb teljesen HIÁNYZOTT.

A `test_editor_405.py` mintáját követve a forrás-string POZÍCIÓJÁT
vizsgáljuk (nem futásidejű geometriát) — ez stabil és nyelvfüggetlen.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []

_QML_SOURCE = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "EditorPanel.qml"
).read_text(encoding="utf-8")

_ICONS_DIR = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "icons"
)


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _load(engine, qml_source):
    component = QQmlComponent(engine)
    component.setData(qml_source.encode("utf-8"), QUrl())
    obj = component.create()
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None, "a komponens betöltése sikertelen"
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.append(component)
    _KEEPALIVE.append(obj)
    return obj


def _make_panel(engine, active_tab=0):
    return _load(
        engine,
        "import QtQuick\nimport PicasaPy 1.0\n"
        f'EditorPanel {{ objectName: "panel"; activeTab: {active_tab} }}\n',
    )


# a #464 jegy sorrendje, a forrásban szereplő azonosítókkal
_EXPECTED_ORDER = [
    'objectName: "editToolCrop"',
    'objectName: "editToolRedeye"',
    'objectName: "editToolEnhance"',
    'objectName: "editToolCreativeKit"',
    'objectName: "editToolAutocolor"',
    'objectName: "editToolAutolight"',
    "id: fixesFillSlider",
    'objectName: "editToolTilt"',
    'objectName: "editToolText"',
    'objectName: "editToolRetouch"',
]


class TestTab1ButtonOrder:
    """#464 1. fül: a fentiek szerinti sorrend a forrásban."""

    def test_source_order_matches_the_issue(self):
        positions = [_QML_SOURCE.index(marker) for marker in _EXPECTED_ORDER]
        assert positions == sorted(positions), (
            "az 1. fül gombjainak/csúszkájának sorrendje nem egyezik a "
            "#464 jegyben rögzített sorrenddel"
        )


class TestCreativeKitTile:
    """#464: a "Kreatív Kit" (Picnik külső szerkesztő) gomb — nincs valódi
    háttere (nincs külső-szerkesztő integráció a projektben), ezért
    helyőrzőként, letiltva jelenik meg (a helye megvan, a bekötés nyitott)."""

    def test_tile_exists(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        tile = panel.findChild(QObject, "editToolCreativeKit")
        assert tile is not None

    def test_tile_is_disabled_placeholder(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        tile = panel.findChild(QObject, "editToolCreativeKit")
        assert tile.property("tileEnabled") is False

    def test_tile_icon_points_to_its_own_svg(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        icon = panel.findChild(QObject, "editToolCreativeKitIcon")
        assert icon is not None
        source = str(icon.property("source").toString())
        assert source.endswith("icons/kreativ-kit.svg")
        assert (_ICONS_DIR / "kreativ-kit.svg").is_file()
