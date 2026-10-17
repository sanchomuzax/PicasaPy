"""Az utolsó maradék vezérlők VALÓDI bemenettel (#5150, utolsó rész, S. fájl).

Lefedve (valódi egérrel, a hatást a jelzésen vagy az állapoton mérve):
- `VideoExitGestureArea.videoExitMouseArea`: a kilépési gesztus. Egykattintásos
  módban egy kattintás, másképp dupla kattintás lép ki. A komponenst önállóan
  futtatjuk; a videó-lejátszó háttere (Qt Multimedia) ezen a gépen nem fut,
  ezért a `VideoPlayerView` bekötését nem mérjük.
- `XmpFacesProgressPanel.xmpFacesPanelCancel`: a futó arcíráskor a Mégse gomb
  megszakítást kér. A futó feladatot a panel számlálója (kész/összes) jelzi; a
  megszakító kód ettől a jelzéstől külön van, ezért a `cancelRequested` jelzést
  mérjük (a hívás eljutását a megszakító kódig).
- `PerfMonitorPanel.perfPanelSavedPathTap`: a naplóútvonal koppintása a
  diagnosztikai mappát nyitja. A fájlkezelő külső program, ezért a `controller`
  hívását rögzítjük (mock).
- `ZoomNavigator.zoomNavigatorViewportDrag`: a nagyító keretének húzása pásztázza
  a nézetet. A kattintás a `MouseArea`-ra megy, ezt a fogó elem nevével ellenőrizzük.
- `AlbumUgroGomb.albumUgroTerulet`: nyomva tartva ismétel (300 ms, majd 100 ms),
  felengedésre leáll.
- `EffectFocalPuck.viewerEffectFocalPuckMouseArea`: a fókuszpont területének
  lenyomása a kattintás helyére állítja az effekt x és y értékét. A radblur
  paraméterpaneljét a 4553-as teszt fixture-jével nyitjuk meg.

Nincs itt: `ignoreFacesDontAskCheck` (a `test_unnamed_faces_view.py`
`TestDontAskAgain` osztálya már valódi kattintással fedi, csak szöveg szerint
keresve), és `hierMentesCheck` (a 5210-es teszt valódi kattintással fedi, de az
audit a beindexelt névről nem látja).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt, Slot
from PySide6.QtTest import QTest

from tests.app.qml_functional._racs_maradek_5150_helpers import az_ablakban, keres
from tests.app.qml_functional._utolso_maradek_5150_helpers import (
    erintes_kattintas,
    keszit_ablakot,
    keszit_motort,
    kattint,
    lista,
    utvonal,
    varj,
)
from tests.app.qml_functional.test_effect_focal_puck_4553 import focal_app  # noqa: F401

_KILEPES_QML = """
import QtQuick
import QtQuick.Controls
import PicasaPy 1.0

ApplicationWindow {
    width: 640
    height: 360
    visible: true
    property int kilepesek: 0
    VideoExitGestureArea {
        anchors.fill: parent
        singleClickExit: SINGLE
        onExitRequested: kilepesek += 1
    }
}
"""

_XMP_QML = """
import QtQuick
import QtQuick.Controls
import PicasaPy 1.0

ApplicationWindow {
    width: 400
    height: 200
    visible: true
    property int megszakitasok: 0
    XmpFacesProgressPanel {
        x: 20
        y: 20
        folderName: "Nyaralas"
        totalCount: 4
        doneCount: 1
        onCancelRequested: megszakitasok += 1
    }
}
"""

_NAPLO_QML = """
import QtQuick
import QtQuick.Controls
import PicasaPy 1.0

ApplicationWindow {
    width: 480
    height: 240
    visible: true
    property string utvonal: ""
    PerfMonitorPanel {
        x: 10
        y: 10
        width: 460
        height: 220
        lastSavedPath: utvonal
    }
}
"""

_ALBUM_QML = """
import QtQuick
import QtQuick.Controls
import PicasaPy 1.0

ApplicationWindow {
    width: 200
    height: 200
    visible: true
    property int aktivalasok: 0
    AlbumUgroGomb {
        objectName: "albumUgroGomb"
        x: 20
        y: 20
        width: 24
        height: 60
        felfele: true
        magyarazat: "Previous album"
        onAktivalva: aktivalasok += 1
    }
}
"""


@pytest.fixture
def motor(qt_app):
    return keszit_motort(qt_app)


class _DiagnosztikaVezerlo(QObject):
    """A `controller` context property a naplóútvonal-kattintáshoz.

    Nem nyit fájlkezelőt: a hívást rögzíti, hogy a teszt a paramétert mérje."""

    def __init__(self):
        super().__init__()
        self.megnyitott: list[str] = []

    @Slot(str)
    def openDiagnosticsFolder(self, ut):
        self.megnyitott.append(ut)


def _kilepes_ablak(motor, qt_app, egykattintasos: bool):
    qml = _KILEPES_QML.replace("SINGLE", "true" if egykattintasos else "false")
    return keszit_ablakot(qt_app, motor, qml)


def _nagyitott_nezo(qml_app_email, qt_app):
    """A nagyított nézet megnyitva, 400%-os nagyítással (ld. a 4568-as tesztet)."""
    ablak, _vezerlo, _engine = qml_app_email
    ablak.setHeight(1024)
    assert varj(qt_app, lambda: int(ablak.height()) == 1024)
    ablak.setProperty("viewerOpen", True)
    nezo = keres(ablak, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    kep = keres(ablak, "viewerImage")
    assert varj(
        qt_app,
        lambda: kep.property("visible")
        and kep.property("paintedWidth") > 0
        and kep.property("paintedHeight") > 0,
    )
    nezo.setProperty("zoomValue", 1.0)
    return ablak, nezo


def test_egykattintasos_gesztus_egy_kattintasra_kilep(motor, qt_app):
    ablak = _kilepes_ablak(motor, qt_app, egykattintasos=True)
    kattint(ablak, qt_app, "videoExitMouseArea")
    assert varj(qt_app, lambda: ablak.property("kilepesek") == 1)


def test_dupla_kattintasos_gesztus_egy_kattintasra_nem_lep_ki(motor, qt_app):
    ablak = _kilepes_ablak(motor, qt_app, egykattintasos=False)
    kattint(ablak, qt_app, "videoExitMouseArea")
    qt_app.processEvents()
    assert ablak.property("kilepesek") == 0, "egy kattintás is kilépett"


def test_dupla_kattintasos_gesztus_dupla_kattintasra_kilep(motor, qt_app):
    ablak = _kilepes_ablak(motor, qt_app, egykattintasos=False)
    gate = keres(ablak, "videoExitMouseArea")
    pont = gate.mapToScene(QPointF(gate.width() / 2, gate.height() / 2)).toPoint()
    QTest.mouseDClick(ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    assert varj(qt_app, lambda: ablak.property("kilepesek") == 1)


def test_a_megszakitas_gomb_valodi_kattintassal_megszakitast_ker(motor, qt_app):
    ablak = keszit_ablakot(qt_app, motor, _XMP_QML)
    kattint(ablak, qt_app, "xmpFacesPanelCancel")
    assert varj(qt_app, lambda: ablak.property("megszakitasok") == 1)


def test_a_naplo_utvonalra_koppintva_a_diagnosztikai_mappat_nyitja(motor, qt_app, tmp_path):
    vezerlo = _DiagnosztikaVezerlo()
    motor.rootContext().setContextProperty("controller", vezerlo)
    ablak = keszit_ablakot(qt_app, motor, _NAPLO_QML)
    ut = tmp_path / "naplo"
    ablak.setProperty("utvonal", str(ut))
    assert varj(qt_app, lambda: keres(ablak, "perfPanelSavedPath").isVisible())
    erintes_kattintas(ablak, qt_app, "perfPanelSavedPathTap")
    assert varj(qt_app, lambda: len(vezerlo.megnyitott) == 1)
    assert utvonal(vezerlo.megnyitott[0]) == utvonal(ut)


def test_a_nagyito_keretenek_huzasa_a_fogo_elemmel_pasztazza_a_nezetet(
    qml_app_email, qt_app
):
    ablak, nezo = _nagyitott_nezo(qml_app_email, qt_app)
    nagyito = keres(ablak, "zoomNavigator")
    assert varj(qt_app, lambda: nagyito.property("visible"))
    elem = keres(ablak, "zoomNavigatorViewportDrag")
    assert varj(qt_app, lambda: elem.isVisible() and az_ablakban(ablak, elem))
    kezdo_pan = float(nezo.property("panX"))
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseMove(ablak, pont)
    qt_app.processEvents()
    QTest.mousePress(ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()
    fogo = ablak.mouseGrabberItem()
    assert fogo is not None and fogo.objectName() == "zoomNavigatorViewportDrag", (
        "a lenyomás nem a nagyító húzható területére ment"
    )
    cel = pont + QPoint(8, 0)
    QTest.mouseMove(ablak, cel, delay=10)
    QTest.mouseRelease(ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, cel)
    assert varj(qt_app, lambda: abs(float(nezo.property("panX")) - kezdo_pan) > 1)


def test_a_nyomva_tartott_album_ugro_ismetel_es_felengedesre_all_le(motor, qt_app):
    ablak = keszit_ablakot(qt_app, motor, _ALBUM_QML)
    terulet = keres(ablak, "albumUgroTerulet")
    assert az_ablakban(ablak, terulet)
    pont = terulet.mapToScene(QPointF(terulet.width() / 2, terulet.height() / 2)).toPoint()
    QTest.mouseMove(ablak, pont)
    QTest.mousePress(ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()
    assert varj(qt_app, lambda: ablak.property("aktivalasok") >= 3), (
        "nyomva tartva nem ismétel"
    )
    QTest.mouseRelease(ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()
    kesz = ablak.property("aktivalasok")
    QTest.qWait(400)
    assert ablak.property("aktivalasok") == kesz, "felengedés után is ismételt"


def test_a_fokuszpont_teruletenek_lenyomasa_beallitja_a_pontot(focal_app, qt_app):  # noqa: F811
    """A radblur effekt paraméterpaneljén a `viewerEffectFocalPuckMouseArea` lenyomása
    a kattintás helyét állítja be (x és y, 0-1 közötti arány)."""
    ablak, _vezerlo, _engine = focal_app
    ablak.setProperty("viewerOpen", True)
    nezo = keres(ablak, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    panel = keres(ablak, "viewerEditorPanel")
    panel.setProperty("activeTab", 2)
    assert varj(qt_app, lambda: panel.property("activeTab") == 2)
    kattint(ablak, qt_app, "effectRadblur")
    assert varj(qt_app, lambda: panel.property("paramPanelActive") is True)
    terulet = keres(ablak, "viewerEffectFocalPuckMouseArea")
    cel = terulet.mapToScene(
        QPointF(terulet.width() * 0.68, terulet.height() * 0.34)
    ).toPoint()
    QTest.mousePress(ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, cel)
    QTest.mouseRelease(ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, cel)
    assert varj(
        qt_app,
        lambda: abs(float(lista(panel.property("paramEffectValues"))[0]) - 0.68) < 0.01,
    ), "a lenyomás nem állította be a fókuszpont x-ét"
    ertekek = lista(panel.property("paramEffectValues"))
    assert abs(float(ertekek[1]) - 0.34) < 0.01, "a fókuszpont y-ja nem követte a lenyomást"
