"""#7491: vörösszem-útmutató hosszabb fordításokkal is a helyén marad."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Property, QPointF, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView

import picasapy.app

_QML_DIR = Path(picasapy.app.__file__).parent / "qml"
_KEEPALIVE = []


class _EditControllerStub(QObject):
    @Property(str, constant=True)
    def previewSource(self):
        return "image://editpreview/42?rev=1"

    @Property("QVariantList", constant=True)
    def legacyEffectsInChain(self):
        return []


def _render(qt_app, width: int, height: int):
    view = QQuickView()
    view.engine().addImportPath(str(_QML_DIR))
    stub = _EditControllerStub()
    view.engine().rootContext().setContextProperty("editController", stub)
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)

    component = QQmlComponent(view.engine())
    component.setData(
        b"""
        import QtQuick
        import QtQuick.Layouts
        import PicasaPy 1.0
        Item {
            objectName: "redeyeFitRoot"
            EditorPanel {
                objectName: "redeyeFitPanel"
                anchors.fill: parent
                redeyeActive: true
            }
        }
        """,
        QUrl(),
    )
    assert not component.errors(), [error.toString() for error in component.errors()]
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


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
@pytest.mark.parametrize("width", [260, 280])
def test_redeye_utmutato_hosszabb_forditasokkal_is_befer(qt_app, width, height_delta):
    root = _render(qt_app, width, 900 + height_delta)
    block = root.findChild(QObject, "redeyeInstructionBlock")
    guide = root.findChild(QObject, "redeyeGuideText")
    note = root.findChild(QObject, "redeyeFrameHintLabel")
    assert block is not None and guide is not None and note is not None
    buttons = [
        root.findChild(QObject, name)
        for name in ("redeyeAutoButton", "redeyeResetButton", "redeyeApplyButton")
    ]
    assert all(button is not None for button in buttons)
    button_y = [button.mapToScene(QPointF(0, 0)).y() for button in buttons]

    translations = (
        (
            "Halten Sie die Maustaste gedrückt und ziehen Sie um jedes Auge, "
            "das Sie einzeln auswählen möchten. Ein Auswahlrahmen erscheint "
            "über dem Bereich. Lassen Sie die Maustaste los, um die Auswahl "
            "abzuschließen. Das Foto wird mit entfernten roten Augen angezeigt.",
            "Hinweis: Klicken Sie auf einen Rahmen, um die Änderung zu löschen.",
        ),
        (
            "Tartsa lenyomva az egérgombot, és külön-külön húzza körbe az "
            "egyes szemeket a kijelölésükhöz. A terület fölött kijelölőkeret "
            "jelenik meg. A kijelölés befejezéséhez engedje fel az egérgombot. "
            "A fényképen a vörösszem-javítás eredménye látható.",
            "Megjegyzés: a módosítás törléséhez kattintson a keretre.",
        ),
    )
    for instruction, hint in translations:
        # A fordítások hossza nyelvenként jelentősen eltérhet. A duplázás
        # szándékos terhelés: a teszt azt védi, hogy a 129 px-es keretben a
        # hosszú fordítás se fedje el a saját végét.
        guide.setProperty("text", f"{instruction} {instruction}")
        note.setProperty("text", f"{hint} {hint}")
        qt_app.processEvents()

        assert guide.property("contentHeight") <= guide.height() + 0.5, (
            f"Az útmutató szövege levágódik: {guide.property('contentHeight'):.1f} "
            f"> {guide.height():.1f} px"
        )
        assert note.property("contentHeight") <= note.height() + 0.5, (
            f"A megjegyzés szövege levágódik: {note.property('contentHeight'):.1f} "
            f"> {note.height():.1f} px"
        )
        assert guide.height() + note.height() <= block.height() + 0.5, (
            "A fordított szövegek túlnyúlnak a 129 px-es útmutatóblokkon: "
            f"{guide.height() + note.height():.1f} > {block.height():.1f} px"
        )
        assert note.y() == pytest.approx(guide.height(), abs=0.5), (
            "A megjegyzés nem közvetlenül az útmutató után következik"
        )
        assert [button.mapToScene(QPointF(0, 0)).y() for button in buttons] == pytest.approx(
            button_y, abs=0.5
        ), "A szöveg illesztése elmozdította a gombokat"
