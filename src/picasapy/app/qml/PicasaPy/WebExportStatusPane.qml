import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: root

    property bool ftpMode: false
    property bool exporting: false
    property string lastError: ""
    property string lastOutputFolder: ""
    property string lastFtpAccount: ""
    property int progressDone: 0
    property int progressTotal: 0
    property int lastPageCount: 0

    Layout.fillWidth: true
    spacing: 10
    visible: root.lastError.length > 0
             || root.exporting
             || (root.ftpMode
                 ? root.lastFtpAccount.length > 0
                 : root.lastOutputFolder.length > 0)

    Text {
        objectName: "webExportErrorText"
        visible: root.lastError.length > 0
        text: root.lastError
        color: Theme.brandRed
        font.pixelSize: Theme.fontSize
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }

    ColumnLayout {
        Layout.fillWidth: true
        visible: root.exporting
        spacing: 6
        Text {
            text: qsTr("PicasaPy is generating the web page.")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            radius: 4
            color: Theme.trackBg
            border.color: Theme.chromeBorder
            Rectangle {
                objectName: "webExportProgressFill"
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                radius: parent.radius
                color: Theme.picasaGreen
                width: root.progressTotal > 0
                       ? parent.width * root.progressDone / root.progressTotal
                       : 0
            }
        }
    }

    Text {
        objectName: "webExportResultText"
        visible: root.ftpMode
                 ? root.lastFtpAccount.length > 0
                 : root.lastOutputFolder.length > 0
        text: root.ftpMode
              ? qsTr("Published %1 file(s) to %2.")
                .arg(root.lastPageCount).arg(root.lastFtpAccount)
              : qsTr("Web page generated: %1 file(s) in %2")
                .arg(root.lastPageCount).arg(root.lastOutputFolder)
        color: Theme.picasaGreen
        font.pixelSize: Theme.fontSize
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }
}
