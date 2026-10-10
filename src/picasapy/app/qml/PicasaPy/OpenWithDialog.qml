import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #4533: a „Társítás…" (Open With) választó Linuxon. A listát a
// `fileops/open_with.py` adja: a fájltípushoz társított asztali alkalmazások.
// A kiválasztottal a `fileOpsController.openWithApp` nyitja meg a képet.
Dialog {
    id: root

    title: qsTr("Open With...")
    modal: true
    focus: true
    anchors.centerIn: Overlay.overlay
    padding: 18
    standardButtons: Dialog.NoButton
    width: Math.min(480, parent ? parent.width - 48 : 480)
    height: Math.min(420, parent ? parent.height - 48 : 420)

    property string photoPath: ""
    property var apps: []
    property int selectedIndex: -1
    readonly property string selectedAppId: selectedIndex >= 0 && selectedIndex < apps.length
        ? apps[selectedIndex].id : ""

    // A lista a megnyitáskor készül: a választó nem tart állapotot a
    // korábbi képről.
    function openFor(path) {
        photoPath = path
        apps = (typeof fileOpsController !== "undefined" && fileOpsController)
            ? fileOpsController.openWithChoices(path) : []
        selectedIndex = apps.length > 0 ? 0 : -1
        open()
    }

    background: Rectangle {
        color: Theme.panelBg
        border.color: Theme.chromeBorder
        radius: 6
    }

    contentItem: ColumnLayout {
        spacing: 12

        ListView {
            id: appList
            objectName: "openWithAppList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.apps.length > 0
            clip: true
            model: root.apps
            currentIndex: root.selectedIndex

            delegate: ItemDelegate {
                objectName: "openWithAppItem"
                width: appList.width
                text: modelData.name
                highlighted: index === root.selectedIndex
                onClicked: root.selectedIndex = index
            }
        }

        Label {
            objectName: "openWithEmptyLabel"
            visible: root.apps.length === 0
            Layout.fillWidth: true
            Layout.fillHeight: true
            wrapMode: Text.WordWrap
            text: qsTr("No application is associated with this file type.")
            color: Theme.ink
            font.pixelSize: Theme.fontSize
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Item { Layout.fillWidth: true }

            PicasaButton {
                objectName: "openWithCancelButton"
                text: qsTr("Cancel")
                onClicked: root.reject()
                contentItem: Label {
                    objectName: "openWithCancelLabel"
                    text: qsTr("Cancel")
                    color: Theme.ink
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            PicasaButton {
                objectName: "openWithOpenButton"
                text: qsTr("Open")
                enabled: root.selectedIndex >= 0
                accent: Theme.picasaGreen
                onClicked: root.accept()
                contentItem: Label {
                    objectName: "openWithOpenLabel"
                    text: qsTr("Open")
                    color: "white"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }
}
