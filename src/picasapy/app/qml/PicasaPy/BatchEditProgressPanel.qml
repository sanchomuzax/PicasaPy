import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Lebegő „Csoportos szerkesztés" folyamat-panel (#425) — az
// `ImportProgressPanel` mintájára, de MEGSZAKÍTHATÓ: sok kijelölt képnél
// (sok mappa, esetleg NAS) a kötegelt `filters=`-írás percekig tarthat, a
// "Mégse" gomb a `controller.cancelBatchEdit()`-et hívja (a MÁR megírt
// mappák változása marad, csak a még el nem kezdettek maradnak ki).
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
            text: qsTr("Batch Edit")
            color: Theme.ink
            font.pixelSize: Theme.fontSize
            font.bold: true
            Layout.fillWidth: true
        }

        Text {
            objectName: "batchEditPanelFolder"
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
                objectName: "batchEditPanelBarFill"
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
                objectName: "batchEditPanelCounts"
                Layout.fillWidth: true
                text: qsTr("%1 / %2 folders").arg(panel.doneCount).arg(panel.totalCount)
                color: Theme.textGray
                font.pixelSize: Theme.fontSize - 1
            }
            Button {
                objectName: "batchEditPanelCancel"
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
