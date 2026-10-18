import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    objectName: "firstRunLanguageDialogWindow"
    width: 480
    height: 200
    visible: true
    modality: Qt.ApplicationModal
    flags: Qt.Dialog
    title: qsTr("Confirm")

    signal chosen(bool accepted)
    property bool answered: false

    function finish(accepted) {
        if (answered)
            return
        answered = true
        chosen(accepted)
        close()
    }

    onClosing: function(closeEvent) {
        if (!answered) {
            answered = true
            chosen(false)
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 20

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 16

            Image {
                objectName: "firstRunLanguagePromptIcon"
                Layout.preferredWidth: 48
                Layout.preferredHeight: 48
                source: Qt.resolvedUrl("../../assets/icon.png")
                sourceSize: Qt.size(48, 48)
                fillMode: Image.PreserveAspectFit
            }

            Label {
                objectName: "firstRunLanguagePromptMessage"
                Layout.fillWidth: true
                Layout.fillHeight: true
                wrapMode: Text.WordWrap
                text: qsTr("PicasaPy is now available in your system's native language.\nWould you like to switch PicasaPy from English to this language?")
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 10

            Button {
                objectName: "firstRunLanguagePromptYesButton"
                text: qsTr("Yes")
                onClicked: root.finish(true)
            }

            Button {
                objectName: "firstRunLanguagePromptNoButton"
                text: qsTr("No")
                onClicked: root.finish(false)
            }
        }
    }
}
