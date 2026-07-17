import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PicasaPy

ApplicationWindow {
    id: window
    width: 1280
    height: 800
    visible: true
    title: "PicasaPy"
    color: Theme.lightboxBg

    property int thumbSize: 144
    property int selectedIndex: -1

    menuBar: MenuBar {
        Menu {
            title: qsTr("&File")
            MenuItem { text: qsTr("Import..."); enabled: false }
            MenuSeparator {}
            MenuItem { text: qsTr("E&xit"); onTriggered: Qt.quit() }
        }
        Menu {
            title: qsTr("&Edit")
            MenuItem { text: qsTr("Select All"); enabled: false }
        }
        Menu {
            title: qsTr("&View")
            MenuItem {
                text: qsTr("Refresh")
                onTriggered: controller.rescan()
            }
        }
        Menu {
            title: qsTr("F&older")
            MenuItem {
                text: qsTr("Rescan folders")
                onTriggered: controller.rescan()
            }
        }
        Menu { title: qsTr("&Picture") }
        Menu { title: qsTr("&Create") }
        Menu {
            title: qsTr("&Tools")
            MenuItem { text: qsTr("Folder Manager..."); enabled: false }
        }
        Menu {
            title: qsTr("&Help")
            MenuItem {
                text: qsTr("About PicasaPy")
                onTriggered: aboutDialog.open()
            }
        }
    }

    header: Rectangle {
        height: 40
        color: Theme.chromeBg
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width; height: 1
            color: Theme.chromeBorder
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 8; anchors.rightMargin: 8
            spacing: 8
            Button {
                text: qsTr("Import")
                enabled: false
                Layout.preferredWidth: 110
            }
            Item { Layout.fillWidth: true }
            TextField {
                id: searchField
                placeholderText: "🔍 " + qsTr("Search")
                Layout.preferredWidth: 240
                onTextEdited: controller.search(text)
            }
        }
    }

    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal

        FolderPane {
            SplitView.preferredWidth: 230
            SplitView.minimumWidth: 160
            foldersModel: controller.folders
            onFolderChosen: function(path) {
                searchField.clear()
                window.selectedIndex = -1
                controller.selectFolder(path)
            }
            onStarredChosen: {
                searchField.clear()
                window.selectedIndex = -1
                controller.showStarred()
            }
        }

        Rectangle {
            color: Theme.lightboxBg
            SplitView.fillWidth: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 4

                Text {
                    text: controller.currentFolder
                          ? controller.currentFolder.split("/").pop()
                          : qsTr("Library")
                    color: Theme.folderTitle
                    font.pixelSize: Theme.folderTitleSize
                    font.bold: true
                }
                Rectangle {
                    Layout.fillWidth: true; height: 1
                    color: Theme.chromeBorder
                }

                GridView {
                    id: grid
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: controller.photos
                    cellWidth: window.thumbSize + 18
                    cellHeight: window.thumbSize + 18
                    delegate: ThumbDelegate {
                        width: grid.cellWidth
                        height: grid.cellHeight
                        selected: window.selectedIndex === index
                        onChosen: function(i) { window.selectedIndex = i }
                    }
                    ScrollBar.vertical: ScrollBar {}
                }
            }
        }
    }

    footer: Column {
        width: parent.width

        Rectangle {
            width: parent.width; height: 22
            gradient: Gradient {
                GradientStop { position: 0.0; color: Theme.infoBarTop }
                GradientStop { position: 1.0; color: Theme.infoBarBottom }
            }
            Text {
                anchors.centerIn: parent
                text: controller.statusText
                color: Theme.infoBarText
                font.pixelSize: Theme.fontSize
                font.bold: true
            }
        }

        Rectangle {
            width: parent.width; height: 48
            color: Theme.trayBg
            Rectangle {
                width: parent.width; height: 1
                color: Theme.trayBorder
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10; anchors.rightMargin: 10
                spacing: 8
                Button { text: qsTr("Hold"); enabled: false }
                Button { text: qsTr("Clear"); enabled: false }
                Button { text: qsTr("Add to"); enabled: false }
                Item { width: 12 }
                Button {
                    text: qsTr("Share")
                    enabled: false
                    palette.button: Theme.picasaGreen
                    palette.buttonText: "white"
                }
                Item { Layout.fillWidth: true }
                Text { text: "🖼"; font.pixelSize: 14 }
                Slider {
                    id: sizeSlider
                    from: 72; to: 256; value: window.thumbSize
                    Layout.preferredWidth: 140
                    onMoved: window.thumbSize = value
                }
            }
        }
    }

    Dialog {
        id: aboutDialog
        title: qsTr("About PicasaPy")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        Text {
            text: "PicasaPy 0.1.0\n" + qsTr("A modern, open Picasa successor.")
            font.pixelSize: Theme.fontSize
        }
    }
}
