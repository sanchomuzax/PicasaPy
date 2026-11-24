"""#7431: A Vörösszem panel útmutatója és megjegyzése nem csordul túl Windowson sem.

Windowson a betűkészlet (Segoe UI) szélesebb és nagyobb sormagasságú, emiatt
260 és 280 képpontos panelszélességnél a `redeyeInstructionBlock` (129 px)
gyereke, a `redeyeFrameHintLabel` túlcsordult (`find_overflows`).
A javítás az eredetiben mért 14 képpontos sorköz rögzítése (`job-837 __10`:
a sorok kezdete 14 képpontonként), platformfüggetlenül.
"""

from __future__ import annotations

from pathlib import Path
import pytest
from PySide6.QtCore import QObject, Property, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView

import picasapy.app
from support.uiaudit_geometry import find_overflows, format_report

_QML_DIR = Path(picasapy.app.__file__).parent / "qml"
_KEEPALIVE = []


class _EditControllerStub(QObject):
    @Property(str, constant=True)
    def previewSource(self):
        return "image://editpreview/42?rev=1"

    @Property("QVariantList", constant=True)
    def legacyEffectsInChain(self):
        return []


def _render(qt_app, qml: str, width: int, height: int):
    view = QQuickView()
    view.engine().addImportPath(str(_QML_DIR))
    stub = _EditControllerStub()
    view.engine().rootContext().setContextProperty("editController", stub)
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)

    component = QQmlComponent(view.engine())
    component.setData(qml.encode("utf-8"), QUrl())
    assert not component.errors(), [e.toString() for e in component.errors()]

    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(width, height)
    root.setWidth(width)
    root.setHeight(height)
    _KEEPALIVE.extend((view, root, component, stub))
    view.show()
    qt_app.processEvents()
    return root


_PANEL_QML = """
    import QtQuick
    import QtQuick.Layouts
    import PicasaPy 1.0
    Item {
        objectName: "auditRoot"
        Rectangle {
            objectName: "baloszlop"
            anchors.fill: parent
            EditorPanel {
                objectName: "auditPanel"
                anchors.fill: parent
                redeyeActive: true
            }
        }
    }
    """


@pytest.mark.parametrize("nev", ["redeyeGuideText", "redeyeFrameHintLabel"])
def test_a_sorkoz_az_eredetiben_mert_14_kepont(qt_app, nev: str):
    """A renderelt szöveg sorköze 14 képpont, mint az eredetiben (`job-837 __10`),
    a betűtípus saját sormagasságától függetlenül (#7431)."""
    root = _render(qt_app, _PANEL_QML, 280, 900)
    szoveg = root.findChild(QObject, nev)
    assert szoveg is not None
    sorok = szoveg.property("lineCount")
    if sorok < 2:
        pytest.skip(f"{nev}: egy sor, a sorköz nem mérhető")
    # FixedHeight módban az utolsó sor a betű saját magasságával számít, a
    # többi sor pontosan a rögzített sorközzel: két szélesség különbsége
    # tehát a sorköz többszöröse
    szuk = _render(qt_app, _PANEL_QML, 260, 900).findChild(QObject, nev)
    kulonbseg_sor = szuk.property("lineCount") - sorok
    if kulonbseg_sor == 0:
        utolso = szoveg.height() - 14 * (sorok - 1)
        assert 10 <= utolso <= 18, (
            f"{nev}: {sorok} sor, {szoveg.height():.1f} képpont; a sorköz nem 14"
        )
    else:
        assert szuk.height() - szoveg.height() == pytest.approx(
            14 * kulonbseg_sor, abs=0.5
        ), f"{nev}: a sorköz nem 14 képpont"


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
@pytest.mark.parametrize("width", [260, 280, 340])
def test_redeye_panel_nem_csordul_tul_eszkoz_modban(qt_app, width: int, height_delta: int):
    """A panel tartalma nem lóg ki sem 260, sem 280, sem 340 px-nél (#7431)."""
    qml = """
    import QtQuick
    import QtQuick.Layouts
    import PicasaPy 1.0
    Item {
        objectName: "auditRoot"
        Rectangle {
            objectName: "baloszlop"
            anchors.fill: parent
            EditorPanel {
                objectName: "auditPanel"
                anchors.fill: parent
                redeyeActive: true
            }
        }
    }
    """
    root = _render(qt_app, qml, width, 900 + height_delta)
    guide = root.findChild(QObject, "redeyeGuideText")
    note = root.findChild(QObject, "redeyeFrameHintLabel")
    block = root.findChild(QObject, "redeyeInstructionBlock")
    assert guide is not None and note is not None and block is not None
    
    # A szövegek együttes magassága nem haladhatja meg a 129 px magas dobozt
    sum_height = guide.height() + note.height()
    assert sum_height <= block.height(), (
        f"A Vörösszem szövegek magassága ({sum_height:.1f} px) "
        f"meghaladja a konténert ({block.height():.1f} px)!"
    )
    
    sertesek = find_overflows(root)
    assert sertesek == [], format_report(sertesek)
