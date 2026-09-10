import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Lebegő „Arccímkék írása" folyamat-panel (#1403) — a
// `BatchEditProgressPanel` mintájára, MEGSZAKÍTHATÓ.
//
// Miért külön komponens, és nem a csoportos szerkesztés paneljének
// újrahasznosítása: ott a cím és a számláló szövege FIX („Batch Edit",
// „%1 / %2 folders"), és az `objectName`-jeire meglévő próbák állnak. A
// paraméterezés azokat törte volna el; a másolat ára egyetlen fájl, a
// haszna, hogy a MÉRT szöveg a helyén van.
//
// A három állapotszöveg az eredetiből (`0x006b9dd0`):
//   `FaceTagJob::progress`  → Writing face tags        (ez a panel)
//   `FaceTagJob::done`      → Done writing face tags   (sáv-üzenet)
//   `FaceTagJob::cancelled` → Cancelled writing face tags (sáv-üzenet)
Rectangle {
    id: panel

    property string folderName: ""
    property int doneCount: 0
    property int totalCount: 0
    signal cancelRequested()

    width: 250
    height: content.implicitHeight + 20
    radius: 4
    color: Theme.trayBg
    border.color: Theme.chromeBorder
    border.width: 1

    Rectangle {
        anchors.fill: parent
        anchors.margins: -1
        z: -1
        radius: panel.radius + 1
        color: "transparent"
        border.color: "#33000000"
    }

    ColumnLayout {
        id: content
        anchors.fill: parent
        anchors.margins: 10
        spacing: 6

        Text {
            text: qsTr("Writing face tags")
            color: Theme.ink
            font.pixelSize: Theme.fontSize
            font.bold: true
            Layout.fillWidth: true
        }

        Text {
            objectName: "xmpFacesPanelFolder"
            Layout.fillWidth: true
            text: panel.folderName
            color: Theme.folderDate
            font.pixelSize: Theme.fontSize
            elide: Text.ElideMiddle
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            radius: 4
            color: Theme.trackBg
            border.color: Theme.chromeBorder

            Rectangle {
                objectName: "xmpFacesPanelBarFill"
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                radius: parent.radius
                color: Theme.picasaGreen
                width: panel.totalCount > 0
                       ? parent.width * panel.doneCount / panel.totalCount
                       : 0
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Text {
                objectName: "xmpFacesPanelCounts"
                Layout.fillWidth: true
                text: qsTr("%1 / %2 pictures").arg(panel.doneCount).arg(panel.totalCount)
                color: Theme.textGray
                font.pixelSize: Theme.fontSize - 1
            }
            Button {
                objectName: "xmpFacesPanelCancel"
                text: qsTr("Cancel")
                onClicked: panel.cancelRequested()
            }
        }
    }

    DragHandler {
        target: panel
        xAxis.minimum: 0
        xAxis.maximum: panel.parent ? panel.parent.width - panel.width : 0
        yAxis.minimum: 0
        yAxis.maximum: panel.parent ? panel.parent.height - panel.height : 0
    }
}
