import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő 5. füle: a „Művészi" (kék ecset) effektek rácsa
// (#330/#516) — Boosttól a Polaroidig.
//
// #496: kiemelve az EditorPanel.qml-ből — a gazda-panelre a `panel`
// tulajdonságon át hivatkozik (ld. `EditorCropPanel.qml`).
ColumnLayout {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    objectName: "effectsColumn3"
    visible: !panel.modeToolActive && panel.activeTab === 4 && !panel.paramPanelActive
    opacity: panel.enabled ? 1 : 0.45
    anchors.margins: 10
    spacing: 8

    Rectangle {
        Layout.fillWidth: true
        height: 22
        color: Theme.panelHeaderBg
        Text {
            anchors.left: parent.left
            anchors.leftMargin: 6
            anchors.verticalCenter: parent.verticalCenter
            text: qsTr("Artistic")
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.panelHeaderText
        }
    }

    GridLayout {
        objectName: "effectsGrid3"
        // #537: HÁROM oszlop, mint az eredeti Picasa effekt-fülein
        columns: 3
        columnSpacing: 6
        rowSpacing: 6
        Layout.fillWidth: true

        PanelButton {
            objectName: "effectBoost"
            label: qsTr("Boost")
            onButtonClicked: if (!panel.tryOpenParamPanel("boost")) panel.effectRequested("boost")
            thumbSource: panel.effectThumbSource("boost")
        }
        PanelButton {
            objectName: "effectSoften"
            label: qsTr("Soft Focus")
            onButtonClicked: if (!panel.tryOpenParamPanel("soften")) panel.effectRequested("soften")
            thumbSource: panel.effectThumbSource("soften")
        }
        PanelButton {
            objectName: "effectPixelate"
            label: qsTr("Pixelate")
            onButtonClicked: if (!panel.tryOpenParamPanel("pixelate")) panel.effectRequested("pixelate")
            thumbSource: panel.effectThumbSource("pixelate")
        }
        PanelButton {
            objectName: "effectFocalZoom"
            label: qsTr("Focal Zoom")
            onButtonClicked: if (!panel.tryOpenParamPanel("focalzoom")) panel.effectRequested("focalzoom")
            thumbSource: panel.effectThumbSource("focalzoom")
        }
        PanelButton {
            objectName: "effectPencilSketch"
            label: qsTr("Pencil Sketch")
            onButtonClicked: if (!panel.tryOpenParamPanel("pencilsketch")) panel.effectRequested("pencilsketch")
            thumbSource: panel.effectThumbSource("pencilsketch")
        }
        PanelButton {
            objectName: "effectNeon"
            label: qsTr("Neon")
            onButtonClicked: if (!panel.tryOpenParamPanel("neon")) panel.effectRequested("neon")
            thumbSource: panel.effectThumbSource("neon")
        }
        PanelButton {
            objectName: "effectComicize"
            label: qsTr("Comicize")
            onButtonClicked: if (!panel.tryOpenParamPanel("comicize")) panel.effectRequested("comicize")
            thumbSource: panel.effectThumbSource("comicize")
        }
        PanelButton {
            objectName: "effectBorder"
            label: qsTr("Border")
            onButtonClicked: if (!panel.tryOpenParamPanel("border")) panel.effectRequested("border")
            thumbSource: panel.effectThumbSource("border")
        }
        PanelButton {
            objectName: "effectDropShadow"
            label: qsTr("Drop Shadow")
            onButtonClicked: if (!panel.tryOpenParamPanel("dropshadow")) panel.effectRequested("dropshadow")
            thumbSource: panel.effectThumbSource("dropshadow")
        }
        PanelButton {
            objectName: "effectMuseumMatte"
            label: qsTr("Museum Matte")
            onButtonClicked: if (!panel.tryOpenParamPanel("museummatte")) panel.effectRequested("museummatte")
            thumbSource: panel.effectThumbSource("museummatte")
        }
        PanelButton {
            objectName: "effectPolaroid"
            label: qsTr("Polaroid")
            onButtonClicked: if (!panel.tryOpenParamPanel("polaroid")) panel.effectRequested("polaroid")
            thumbSource: panel.effectThumbSource("polaroid")
        }
    }
}
