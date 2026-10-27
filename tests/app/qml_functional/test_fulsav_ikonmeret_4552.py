"""#4552 — a szerkesztőfül-ikonok mért mérete és horgonygeometriája.

Spec: `docs/specs/ui-audit-editor.md`, „A fülsáv ikonjai — sorrend és méret":
tab1 15×16 · tab2 17×18 · tab3 20×19 · tab4 25×19 · tab5 25×19. A `.tre`
horgony alapján a felső él `round((25 - magasság) / 2 - 1)`; a 6.–7. fül a
3–5. fül 25×19-es ikonméretét kapja.

A teszt a QML-geometriából ellenőrzi a méretet, középre igazítást és horgonyt.
A renderelt tintadoboz nem használható méretként, mert a rajz saját üres széleit
is beleszámítja.
"""

import math

import pytest
from PySide6.QtCore import QPointF, QUrl
from PySide6.QtQuick import QQuickView

#: (fül objectName, szélesség, magasság) — a spec táblázata
MERT = (
    ("editTabFixes", 15, 16),
    ("editTabFinetune", 17, 18),
    ("editTabEffects", 20, 19),
    ("editTabEffects2", 25, 19),
    ("editTabEffects3", 25, 19),
    # a 6. és 7. fül a mi többletünk: a 3–5. fül ikonméretét kapja
    ("editTabEffects4", 25, 19),
    ("editTabLegacy", 25, 19),
)

TURES = 3

_QML = """
import QtQuick
import PicasaPy 1.0
Rectangle {
    width: 276; height: 40; color: "#ffffff"
    QtObject {
        id: stub
        property int activeTab: 99
        property bool legacyEffectsPresent: false
        function selectTab(i) { activeTab = i }
    }
    EditorTabBar { objectName: "bar"; panel: stub; width: 276; y: 5 }
}
"""


@pytest.fixture
def sav(qt_app, tmp_path, request):
    import picasapy.app.application as app_module

    ablakmagassag = request.param
    qml = tmp_path / "fulsav_4552.qml"
    qml.write_text(
        _QML.replace("height: 40;", f"height: {ablakmagassag};"), encoding="utf-8"
    )
    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    view.setSource(QUrl.fromLocalFile(str(qml)))
    assert view.status() == QQuickView.Status.Ready, view.errors()
    view.resize(276, ablakmagassag)
    view.show()
    for _ in range(30):
        qt_app.processEvents()
    yield view
    view.close()
    view.deleteLater()


def _elem(view, nev):
    from PySide6.QtCore import QObject

    obj = view.rootObject().findChild(QObject, nev)
    assert obj is not None, nev
    return obj


@pytest.mark.parametrize("sav", (35, 40, 45), indirect=True)
def test_az_ikon_merete_es_horgonya_a_qml_geometriaban(sav):
    for nev, szel, mag in MERT:
        ful = _elem(sav, nev)
        ikon = _elem(sav, nev + "Icon")
        assert ikon.width() == szel, (nev, ikon.width(), szel)
        assert ikon.height() == mag, (nev, ikon.height(), mag)

        vart_y = math.floor((ful.height() - ikon.height()) / 2 - 1 + 0.5)
        assert ikon.y() == vart_y, (nev, ikon.y(), vart_y)

        ikon_kozepe = ikon.mapToScene(QPointF(ikon.width() / 2, 0)).x()
        ful_kozepe = ful.mapToScene(QPointF(ful.width() / 2, 0)).x()
        assert abs(ikon_kozepe - ful_kozepe) <= TURES, (
            nev,
            ikon_kozepe - ful_kozepe,
        )
