"""#4552 — a szerkesztő fülsávjának ikonjai az eredeti (mért) méretűek.

Spec: `docs/specs/ui-audit-editor.md`, „A fülsáv ikonjai — sorrend és méret":
tab1 15×16 · tab2 17×18 · tab3 20×19 · tab4 25×19 · tab5 25×19; minden ikon a
fül tetejétől 4 képpontra, a fülön belül vízszintesen középen.

A próba a RENDERELT ablakképen (`grabWindow`) méri az ikon nem háttérszínű
képpontjainak dobozát — nem property-t olvas. A 6.–7. fülnek (a mi
többletünk) nincs mért párja; ott csak azt őrizzük, hogy az ikon befér.
"""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, QUrl
from PySide6.QtQuick import QQuickView

_QML_DIR = (
    Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "qml"
)

#: (fül objectName, szélesség, magasság) — a spec táblázata
MERT = (
    ("editTabFixes", 15, 16),
    ("editTabFinetune", 17, 18),
    ("editTabEffects", 20, 19),
    ("editTabEffects2", 25, 19),
    ("editTabEffects3", 25, 19),
)

TURES = 2
KUSZOB = 40  # a három csatorna összegében

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
def sav(qt_app, tmp_path):
    import picasapy.app.application as app_module

    qml = tmp_path / "fulsav_4552.qml"
    qml.write_text(_QML, encoding="utf-8")
    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    view.setSource(QUrl.fromLocalFile(str(qml)))
    assert view.status() == QQuickView.Status.Ready, view.errors()
    view.resize(276, 40)
    view.show()
    for _ in range(30):
        qt_app.processEvents()
    yield view
    view.close()
    view.deleteLater()


def _kep(view, qt_app):
    for _ in range(30):
        qt_app.processEvents()
    return view.grabWindow()


def _elem(view, nev):
    from PySide6.QtCore import QObject

    obj = view.rootObject().findChild(QObject, nev)
    assert obj is not None, nev
    return obj


def _doboz(kep, x0, y0, x1, y1):
    """A [x0,x1)×[y0,y1) sávban a háttértől eltérő képpontok doboza."""
    hatter = kep.pixelColor(x0, y0)

    def kulonbseg(x, y):
        c = kep.pixelColor(x, y)
        return (abs(c.red() - hatter.red()) + abs(c.green() - hatter.green())
                + abs(c.blue() - hatter.blue()))

    pontok = [(x, y) for y in range(y0, y1) for x in range(x0, x1)
              if kulonbseg(x, y) > KUSZOB]
    assert pontok, "az ikon nem rajzolódott ki"
    xs = [p[0] for p in pontok]
    ys = [p[1] for p in pontok]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


@pytest.mark.parametrize("nev,szel,mag", MERT)
def test_az_ikon_merete_es_helye_a_renderelt_kepen(sav, qt_app, nev, szel, mag):
    kep = _kep(sav, qt_app)
    ful = _elem(sav, nev)
    fx = round(ful.mapToScene(QPointF(0, 0)).x())
    fy = round(ful.mapToScene(QPointF(0, 0)).y())
    fw = round(ful.width())
    # a fül 1 képpontos kerete belül marad ki a mérésből
    x0, y0, x1, y1 = _doboz(kep, fx + 2, fy + 2, fx + fw - 2, fy + 25 - 2)
    assert abs((x1 - x0) - szel) <= TURES, (nev, x1 - x0, szel)
    assert abs((y1 - y0) - mag) <= TURES, (nev, y1 - y0, mag)
    # vízszintesen a fül közepén
    kozep = (x0 + x1) / 2 - (fx + fw / 2)
    assert abs(kozep) <= TURES, (nev, kozep)
    # a fül tetejétől 4 képpontra
    assert abs((y0 - fy) - 4) <= TURES, (nev, y0 - fy)


def test_a_het_ikon_befer_a_fulbe(sav, qt_app):
    kep = _kep(sav, qt_app)
    for nev in ("editTabEffects4", "editTabLegacy"):
        ful = _elem(sav, nev)
        fx, fy = round(ful.x()), round(_elem(sav, "bar").y())
        x0, y0, x1, y1 = _doboz(kep, fx + 2, fy + 2,
                                fx + round(ful.width()) - 2, fy + 25 - 2)
        assert x1 - x0 <= ful.width() - 2
        assert y1 <= fy + 25


def test_a_kep_a_scratchpadbe(sav, qt_app):
    cel = os.environ.get("FULSAV_4552_KEP")
    if not cel:
        pytest.skip("nincs FULSAV_4552_KEP")
    kep = _kep(sav, qt_app).scaled(276 * 4, 40 * 4)
    assert kep.save(cel)
