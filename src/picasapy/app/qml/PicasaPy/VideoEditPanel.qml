import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Videó-panel (#4566): videónál a bal oldali szerkesztőpanel fülsávja helyén
// áll. Az eredeti `editpanel/movietab` ezt a panelt mutatja a fülsáv
// elrejtése mellett (`docs/specs/ui-audit-editor.md`, a `movietab` szakasza).
//
// Csak a gombok és az állapot élnek itt: a parancsot a gazda (PhotoViewer)
// hajtja végre, így a panel a lejátszó betöltése nélkül is kattintható.
Rectangle {
    id: panel
    //: a vágás (kezdő- vagy befejező pont) megvan — csak akkor értelmes a
    //: visszaállítás és a klip-export
    property bool trimmed: false
    //: a képkocka-mentéshez élő lejátszó kell
    property bool captureAvailable: false

    signal resetTrimRequested()
    signal captureFrameRequested()
    signal exportClipRequested()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        PicasaButton {
            objectName: "movieeditpanel/reset_trim"
            Layout.fillWidth: true
            text: qsTr("Reset Start and End")
            enabled: panel.trimmed
            ToolTip.text: qsTr("Restore movie to its original length (remove start and end points)")
            ToolTip.delay: Theme.tooltipDelay
            ToolTip.visible: hovered
            onClicked: panel.resetTrimRequested()
        }
        PicasaButton {
            objectName: "movieeditpanel/capture_frame"
            Layout.fillWidth: true
            text: qsTr("Take Snapshot")
            enabled: panel.captureAvailable
            ToolTip.text: qsTr("Capture current frame")
            ToolTip.delay: Theme.tooltipDelay
            ToolTip.visible: hovered
            onClicked: panel.captureFrameRequested()
        }
        PicasaButton {
            objectName: "movieeditpanel/export_movie"
            Layout.fillWidth: true
            text: qsTr("Export Clip")
            enabled: panel.trimmed
            ToolTip.text: qsTr("Save a clip of the movie between the start and end points")
            ToolTip.delay: Theme.tooltipDelay
            ToolTip.visible: hovered
            onClicked: panel.exportClipRequested()
        }
        Item {
            Layout.fillHeight: true
        }
    }
}
