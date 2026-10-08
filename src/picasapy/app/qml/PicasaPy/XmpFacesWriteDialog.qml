import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Az eredeti `write_all_facetags.fen` hatókör-választója (#4634).
Dialog {
    id: dialog
    objectName: "xmpFacesWriteDialog"

    property var selectedRows: []
    signal writeRequested(string scope, var rows)

    title: qsTr("Write Face Tags")
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined

    function openFor(rows) {
        selectedRows = rows ? rows.slice(0) : []
        open()
    }

    function write(scope) {
        var rows = scope === "selected" ? selectedRows.slice(0) : []
        close()
        writeRequested(scope, rows)
    }

    ColumnLayout {
        spacing: 12

        Text {
            objectName: "xmpFacesWriteWarning"
            Layout.preferredWidth: 520
            text: qsTr("Write faces or write all may take a long time. If logging is set to detailed or higher, network.log will contain messages about read-only files which could not be updated. Signing out is recommended while using this feature.")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 8

            PicasaButton {
                objectName: "xmpFacesWriteSelected"
                text: qsTr("Write Selected")
                enabled: dialog.selectedRows.length > 0
                onClicked: dialog.write("selected")
            }
            PicasaButton {
                objectName: "xmpFacesWriteFaces"
                text: qsTr("Write Faces")
                onClicked: dialog.write("faces")
            }
            PicasaButton {
                objectName: "xmpFacesWriteAll"
                text: qsTr("Write All")
                onClicked: dialog.write("all")
            }
            PicasaButton {
                objectName: "xmpFacesWriteCancel"
                text: qsTr("Cancel")
                onClicked: dialog.reject()
            }
        }
    }
}
