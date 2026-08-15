"""A Visszavonás/Újra sor SOSEM csúszhat ki a látható területről — #641.

**Miért kellett ez a teszt.** A #628 javítása a panel `implicitHeight`-jére
és egy `Layout.minimumHeight`-re bízta a „mindig elfér" garanciát — csakhogy
azt semmi nem érvényesítette az ablak szintjén. Rövid ablakban a panel nem
zsugorodott, hanem TÚLNYÚLT a celláján, és a panel aljához igazodó gombsor
vele együtt csúszott ki a képernyőről. A felhasználó a Visszavonás/Újra
gombokat egyáltalán nem látta.

**Amit a régi teszt nem látott.** A `test_editor_tab_overlap_616.py`
kizárólag a panelen BELÜLI viszonyokat vizsgálta (a sor a fül alatt van-e).
Ez a készlet a SZÜLŐ geometriáját is felépíti — a néző elrendezését
lemásolva —, és több ablakmagasságon nézi, hogy a sor a látható területen
belül maradt-e.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []

#: A hibajelentésben szereplő magasságok, a bőségestől a szűkösig. A 360 az,
#: ahol a régi kód a sort az ablak alá tette.
ABLAKMAGASSAGOK = (900, 620, 520, 480, 420, 360)

#: A néző elrendezésének mása: felső sáv (46) + kitöltő sor, benne a 280 px
#: széles panel-doboz — pontosan úgy, ahogy a PhotoViewer.qml csinálja
#: (a #641 óta `Layout.minimumHeight` NÉLKÜL: az okozta a túlnyúlást).
_QML = """
import QtQuick
import QtQuick.Layouts
import PicasaPy 1.0

Item {
    id: root
    objectName: "root"
    width: 900
    property alias panel: editorPanel
    property alias box: panelBox
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Rectangle { Layout.fillWidth: true; height: 46 }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0
            Rectangle {
                id: panelBox
                Layout.preferredWidth: 280
                Layout.fillHeight: true
                EditorPanel {
                    id: editorPanel
                    objectName: "editorPanel"
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    activeTab: 2
                }
            }
            Item { Layout.fillWidth: true; Layout.fillHeight: true }
        }
    }
}
"""


@pytest.fixture
def engine(qt_app):
    import picasapy.app.application as app_module

    eng = QQmlEngine()
    eng.addImportPath(str(app_module._APP_DIR / "qml"))
    eng.rootContext().setContextProperty("controller", None)
    eng.rootContext().setContextProperty("editController", None)
    yield eng
    eng.deleteLater()


def _nezo(engine, magassag: int):
    component = QQmlComponent(engine)
    component.setData(_QML.encode("utf-8"), QUrl())
    obj = component.create()
    assert [e.toString() for e in component.errors()] == []
    assert obj is not None
    obj.setProperty("height", magassag)
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((component, obj))
    return obj


def _sor_alja_az_ablakban(gyoker) -> float:
    """A gombsor aljának abszolút helye a néző koordinátáiban."""
    panel = gyoker.findChild(QObject, "editorPanel")
    doboz = panel.parent()
    return (
        doboz.property("y")
        + panel.property("y")
        + panel.property("undoRowBottom")
    )


class TestAGombsorLathatoMarad:
    @pytest.mark.parametrize("magassag", ABLAKMAGASSAGOK)
    def test_a_sor_alja_az_ablakon_belul_van(self, engine, magassag: int) -> None:
        """A hiba lényege: 360 px-es nézőnél a sor az ablak ALATT volt."""
        gyoker = _nezo(engine, magassag)

        assert _sor_alja_az_ablakban(gyoker) <= magassag + 1, (
            f"{magassag} px magas nézőben a Visszavonás/Újra sor kicsúszik"
        )

    @pytest.mark.parametrize("magassag", ABLAKMAGASSAGOK)
    def test_a_sor_nem_csuszik_a_lathato_terulet_folé(
        self, engine, magassag: int
    ) -> None:
        """Ellenpróba: ne is ugorjon fel a panel tetejére."""
        gyoker = _nezo(engine, magassag)

        assert _sor_alja_az_ablakban(gyoker) > 46


class TestANezoKozliAzIgenyet:
    def test_a_szukseges_magassag_a_panel_igenyebol_szamol(self, engine) -> None:
        """A #641 elsődleges javítása: a néző MEGMONDJA, mennyi hely kell,
        és az ablak minimuma ebből számol — nem beégetett számból."""
        gyoker = _nezo(engine, 900)
        panel = gyoker.findChild(QObject, "editorPanel")

        assert panel.property("implicitHeight") > 0

    def test_bo_helyen_a_tartalom_alatt_ul(self, engine) -> None:
        """#616: bő helyen a sor a TARTALOM alatt ül, nem a panel alján.

        A korábbi állítás (a sor alja a panel látható aljához közel) nagy
        képernyőn a hibát rögzítette: a gombsor több száz képponttal a fül
        tartalma alá került. Az eredeti fix méretű panelén a sor mindig
        közvetlenül a tartalom alatt van — ez az irányadó. A „sosem lóg ki
        a látható területből" garancia változatlanul él, azt a szűk ablakos
        testvér-tesztek őrzik."""
        gyoker = _nezo(engine, 900)
        panel = gyoker.findChild(QObject, "editorPanel")

        # a látható területen belül marad
        assert panel.property("undoRowBottom") <= panel.property("visibleHeight")
        # és NEM a panel aljára van szegezve: bő helyen jóval fölötte ül
        assert panel.property("undoRowBottom") < panel.property("visibleHeight") - 100
