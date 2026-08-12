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

# #496: az 1. fül tartalma az `EditorPanel.qml`-ből az
# `EditorTabCommonFixes.qml`-be került (a fájl a 800 soros korlát fölé nőtt).
# A forrás-szöveges ellenőrzések ezért MINDKÉT fájlt nézik — a szerződés
# (sorrend, feliratok, hiányzó csempék) változatlan, csak a hely más.
_QML_DIR = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy"
)
_QML_SOURCE = "\n".join(
    (_QML_DIR / name).read_text(encoding="utf-8")
    for name in ("EditorPanel.qml", "EditorTabCommonFixes.qml")
)

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


# #464: az 1. fül sorrendje a tulajdonos KÉPERNYŐKÉPÉRŐL (Picasa 3.9,
# „Gyakori javítások"). Ez FELÜLÍRJA a jegy szövegében szereplő korábbi
# sorrendet, ami feljegyzésből készült — a képen három sorban:
#     Vágás · Kiegyenesítés · Vörösszem
#     Jó napom van · Automatikus kontraszt · Automatikus szín
#     Retusálás · Szöveg
# és MINDEGYIK ALATT a Derítőfény-csúszka.
_EXPECTED_ORDER = [
    'objectName: "editToolCrop"',
    'objectName: "editToolTilt"',
    'objectName: "editToolRedeye"',
    'objectName: "editToolEnhance"',
    'objectName: "editToolAutolight"',
    'objectName: "editToolAutocolor"',
    'objectName: "editToolRetouch"',
    'objectName: "editToolText"',
    "id: fixesFillSlider",
]


class TestTab1ButtonOrder:
    """#464 1. fül: a képernyőkép szerinti sorrend a forrásban."""

    def test_source_order_matches_the_screenshot(self):
        positions = [_QML_SOURCE.index(marker) for marker in _EXPECTED_ORDER]
        assert positions == sorted(positions), (
            "az 1. fül gombjainak/csúszkájának sorrendje nem egyezik a "
            "tulajdonos képernyőképén látható sorrenddel"
        )


class TestNoCreativeKitTile:
    """#464: a képernyőképen NINCS „Kreatív Kit" csempe — a jegy szövege
    tévesen sorolta fel (a Picnik külső szerkesztő gombja nem szerepel a
    „Gyakori javítások" fülön). A helyőrző csempét ezért levettük."""

    def test_tile_is_gone(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        assert panel.findChild(QObject, "editToolCreativeKit") is None

    def test_source_has_no_creative_kit_marker(self):
        assert 'objectName: "editToolCreativeKit"' not in _QML_SOURCE
