import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő „Vörösszem" panelje (#445).
//
// A jegy két tényt rögzít az eredeti eszközről, és mindkettő ITT látszik:
//  * AUTOMATIKUS: a panel megnyitásakor a felismerés azonnal lefut, az
//    „Auto" gombbal újrafuttatható, és sikerüzenet kíséri („Picasa has
//    found and corrected red eye(s)").
//  * KÉZI kiegészítés: „You can also draw a square around any red eye that
//    Picasa may have missed." — a téglalap-húzást a hívó (PhotoViewer)
//    végzi a képen, ez a fájl nem ismeri a kép geometriáját (a Retusálás/
//    Vágás panel mintája).
//
// A „Preview changes without square outlines" jelölőnégyzet csak a
// kijelölő-négyzetek RAJZÁT kapcsolja ki az előnézeten — a javításon nem
// változtat, ezért tisztán nézet-állapot (nem megy a kontrollerhez).
ColumnLayout {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    objectName: "redeyeColumn"
    visible: panel.redeyeActive
    opacity: panel.enabled ? 1 : 0.45
    anchors.margins: 10
    spacing: 8

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        Image {
            Layout.preferredWidth: 40
            Layout.preferredHeight: 30
            source: "../../assets/tools/redeye.png"
        }
        Text {
            Layout.fillWidth: true
            text: qsTr("Redeye")
            font.pixelSize: Theme.fontSize + 3
            color: Theme.ink
        }
    }

    Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: qsTr("You can also draw a square around any red eye that"
                   + " Picasa may have missed. Click, hold, and drag the"
                   + " mouse around each eye separately to select it. A"
                   + " selection box appears over the area.")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    // az automatika visszajelzése — a jegy szó szerinti sikerüzenete
    Text {
        objectName: "redeyeAutoResultLabel"
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        visible: panel.redeyeFoundCount >= 0
        text: panel.redeyeFoundCount > 0
              ? qsTr("Picasa has found and corrected red eye(s).")
              : qsTr("No red eye was found automatically.")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    Text {
        objectName: "redeyeRegionCountLabel"
        Layout.fillWidth: true
        text: qsTr("Regions selected: %1").arg(panel.redeyeRegionCount)
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    CheckBox {
        objectName: "redeyeHideOutlinesCheck"
        text: qsTr("Preview changes without square outlines")
        font.pixelSize: Theme.fontSize - 1
        checked: panel.redeyeHideOutlines
        onToggled: panel.redeyeHideOutlines = checked
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        PanelButton {
            objectName: "redeyeAutoButton"
            label: qsTr("Auto")
            onButtonClicked: panel.redeyeAutoRequested()
        }
        PanelButton {
            objectName: "redeyeUndoRegionButton"
            label: qsTr("Undo")
            buttonEnabled: panel.canUndoRedeyeRegion
            onButtonClicked: panel.redeyeUndoRegionRequested()
        }
        PanelButton {
            objectName: "redeyeResetButton"
            label: qsTr("Reset")
            buttonEnabled: panel.redeyeRegionCount > 0
            onButtonClicked: panel.redeyeResetRequested()
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        PanelButton {
            objectName: "redeyeApplyButton"
            label: qsTr("Apply") + " ✔"
            onButtonClicked: panel.redeyeApplyRequested()
        }
        PanelButton {
            objectName: "redeyeCancelButton"
            label: qsTr("Cancel") + " ✘"
            onButtonClicked: panel.redeyeCancelRequested()
        }
    }
}
