import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő 4. füle: a „Kreatív" (zöld ecset) effektek rácsa
// (#329/#516) — Infravörös filmtől a Duo-tone-ig.
//
// #496: kiemelve az EditorPanel.qml-ből — a gazda-panelre a `panel`
// tulajdonságon át hivatkozik (ld. `EditorCropPanel.qml`).
ColumnLayout {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    objectName: "effectsColumn2"
    visible: !panel.modeToolActive && panel.activeTab === 3 && !panel.paramPanelActive
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
            text: qsTr("Creative")
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.panelHeaderText
        }
    }

    GridLayout {
        objectName: "effectsGrid2"
        // #537: HÁROM oszlop, mint az eredeti Picasa effekt-fülein
        columns: 3
        columnSpacing: 6
        rowSpacing: 6
        Layout.fillWidth: true

        PanelButton {
            objectName: "effectIr"
            label: qsTr("Infrared Film")
            onButtonClicked: if (!panel.tryOpenParamPanel("ir")) panel.effectRequested("ir")
            thumbSource: panel.effectThumbSource("ir")
        }
        PanelButton {
            objectName: "effectLomo"
            label: qsTr("Lomo-ish")
            onButtonClicked: if (!panel.tryOpenParamPanel("lomo")) panel.effectRequested("lomo")
            thumbSource: panel.effectThumbSource("lomo")
        }
        PanelButton {
            objectName: "effectHolga"
            label: qsTr("Holga-ish")
            onButtonClicked: if (!panel.tryOpenParamPanel("holga")) panel.effectRequested("holga")
            thumbSource: panel.effectThumbSource("holga")
        }
        PanelButton {
            objectName: "effectHdr"
            label: qsTr("HDR-ish")
            onButtonClicked: if (!panel.tryOpenParamPanel("hdr")) panel.effectRequested("hdr")
            thumbSource: panel.effectThumbSource("hdr")
        }
        PanelButton {
            objectName: "effectCinemascope"
            label: qsTr("Cinemascope")
            onButtonClicked: if (!panel.tryOpenParamPanel("cinemascope")) panel.effectRequested("cinemascope")
            thumbSource: panel.effectThumbSource("cinemascope")
        }
        PanelButton {
            objectName: "effectOrton"
            label: qsTr("Orton-ish")
            onButtonClicked: if (!panel.tryOpenParamPanel("orton")) panel.effectRequested("orton")
            thumbSource: panel.effectThumbSource("orton")
        }
        PanelButton {
            objectName: "effectSixties"
            label: qsTr("1960s")
            onButtonClicked: if (!panel.tryOpenParamPanel("sixties")) panel.effectRequested("sixties")
            thumbSource: panel.effectThumbSource("sixties")
        }
        PanelButton {
            objectName: "effectInvert"
            label: qsTr("Invert Colors")
            onButtonClicked: if (!panel.tryOpenParamPanel("invert")) panel.effectRequested("invert")
            thumbSource: panel.effectThumbSource("invert")
        }
        PanelButton {
            objectName: "effectHeatMap"
            label: qsTr("Heat Map")
            onButtonClicked: if (!panel.tryOpenParamPanel("heatmap")) panel.effectRequested("heatmap")
            thumbSource: panel.effectThumbSource("heatmap")
        }
        PanelButton {
            objectName: "effectCrossProcess"
            label: qsTr("Cross Process")
            onButtonClicked: if (!panel.tryOpenParamPanel("crossprocess")) panel.effectRequested("crossprocess")
            thumbSource: panel.effectThumbSource("crossprocess")
        }
        PanelButton {
            objectName: "effectQuantizePalette"
            label: qsTr("Posterize")
            onButtonClicked: if (!panel.tryOpenParamPanel("quantizepalette")) panel.effectRequested("quantizepalette")
            thumbSource: panel.effectThumbSource("quantizepalette")
        }
        PanelButton {
            objectName: "effectTwoTone"
            label: qsTr("Duo-Tone")
            onButtonClicked: if (!panel.tryOpenParamPanel("twotone")) panel.effectRequested("twotone")
            thumbSource: panel.effectThumbSource("twotone")
        }
    }
}
