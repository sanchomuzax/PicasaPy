import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő „Retusálás" panelje (#148/#445): az ecsetméret-csúszka, a
// kétkattintásos klónozás súgószövege és a saját Alkalmaz/Mégse pár.
//
// #496: kiemelve az EditorPanel.qml-ből (ld. az `EditorCropPanel.qml`
// megjegyzését a `panel` tulajdonságról).
ColumnLayout {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    objectName: "retouchColumn"
    visible: panel.retouchActive
    opacity: panel.enabled ? 1 : 0.45
    anchors.margins: 10
    spacing: 8

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        Image {
            Layout.preferredWidth: 40
            Layout.preferredHeight: 30
            source: "../../assets/tools/retouch.png"
        }
        Text {
            Layout.fillWidth: true
            text: qsTr("Retouch")
            font.pixelSize: Theme.fontSize + 3
            color: Theme.ink
        }
    }

    Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: qsTr("Click to select the area to fix. Then, move the"
                   + " mouse to see a preview of the replacement area."
                   + " Click on the image again to finalize. Lather,"
                   + " rinse, repeat.")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    Label {
        text: qsTr("Brush Size")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }
    PicasaSlider {
        id: retouchBrushSizeSlider
        objectName: "retouchBrushSizeSlider"
        Layout.fillWidth: true
        from: 1; to: 100
        stepSize: 1
        value: panel.brushSize
        onMoved: panel.brushSizeEdited(Math.round(value))
    }

    Text {
        objectName: "retouchRegionCountLabel"
        Layout.fillWidth: true
        text: qsTr("Regions selected: %1").arg(panel.retouchRegionCount)
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    // #445: a Picasa súgószövege szerinti, számítás-alatti előnézetet
    // jelző felirat — a folt véglegesítéséig (cél kijelölve, forrás
    // mozgatás alatt) látszik az előnézet fölött.
    Text {
        objectName: "retouchRefiningLabel"
        Layout.fillWidth: true
        visible: panel.retouchPatchPending
        text: qsTr("Refining…")
        font.pixelSize: Theme.fontSize - 1
        font.italic: true
        color: Theme.textGray
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        PanelButton {
            objectName: "retouchUndoPatchButton"
            label: qsTr("Undo Patch")
            buttonEnabled: panel.canUndoPatch
            onButtonClicked: panel.retouchUndoPatchRequested()
        }
        PanelButton {
            objectName: "retouchRedoPatchButton"
            label: qsTr("Redo Patch")
            buttonEnabled: panel.canRedoPatch
            onButtonClicked: panel.retouchRedoPatchRequested()
        }
        PanelButton {
            objectName: "retouchResetButton"
            label: qsTr("Reset")
            buttonEnabled: panel.retouchRegionCount > 0 || panel.retouchPatchPending
            onButtonClicked: panel.retouchResetRequested()
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        PanelButton {
            objectName: "retouchApplyButton"
            label: qsTr("Apply") + " ✔"
            buttonEnabled: panel.retouchRegionCount > 0
            onButtonClicked: panel.retouchApplyRequested()
        }
        PanelButton {
            objectName: "retouchCancelButton"
            label: qsTr("Cancel") + " ✘"
            onButtonClicked: panel.retouchCancelRequested()
        }
    }
}
