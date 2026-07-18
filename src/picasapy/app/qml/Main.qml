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
    property bool viewerOpen: false

    menuBar: PicasaMenuBar {
        onRescanRequested: controller.rescan()
        onAboutRequested: aboutDialog.open()
        onThumbSizePreset: function(size) { window.thumbSize = size }
        onSelectStarredRequested: controller.showStarred()
    }

    // Eszköztár: Importálás | (szűrők középen) | kereső jobbra
    header: Rectangle {
        height: 34
        color: Theme.chromeBg
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width; height: 1
            color: Theme.chromeBorder
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 8; anchors.rightMargin: 8
            spacing: 10
            PicasaButton {
                text: qsTr("Import")
                enabled: false
                Layout.preferredWidth: 100
                Layout.preferredHeight: 24
            }
            Item { Layout.fillWidth: true }
            Column {
                Layout.alignment: Qt.AlignVCenter
                spacing: 0
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: qsTr("Filters")
                    font.pixelSize: 9
                    color: Theme.textGray
                }
                Row {
                    spacing: 7
                    Text {
                        text: "★"
                        font.pixelSize: 13
                        color: starFilter.hovered ? Theme.starYellow : "#8f8f8f"
                        HoverHandler { id: starFilter }
                        TapHandler { onTapped: controller.showStarred() }
                    }
                    // fotó-szűrő (inaktív): kis keretezett kép sziluett
                    Rectangle {
                        width: 13; height: 11; radius: 1
                        color: "#ffffff"; border.color: "#9a9a9a"; opacity: 0.5
                        Rectangle {
                            x: 2; y: 6; width: 9; height: 3
                            color: "#8ab06a"
                        }
                    }
                    // személy-szűrő (inaktív)
                    Item {
                        width: 11; height: 11; opacity: 0.5
                        Rectangle {
                            x: 3; y: 0; width: 5; height: 5; radius: 2.5
                            color: "#8a8a8a"
                        }
                        Rectangle {
                            x: 1; y: 6; width: 9; height: 5
                            radius: 2; color: "#8a8a8a"
                        }
                    }
                    // videó-szűrő (inaktív)
                    Rectangle {
                        width: 13; height: 11; radius: 1
                        color: "#8a8a8a"; opacity: 0.5
                        Text {
                            anchors.centerIn: parent
                            text: "▶"; color: "white"; font.pixelSize: 7
                        }
                    }
                    // geo-szűrő (inaktív)
                    Item {
                        width: 9; height: 12; opacity: 0.6
                        Rectangle {
                            x: 0; y: 0; width: 9; height: 9; radius: 4.5
                            color: "#c94b3d"
                        }
                        Rectangle {
                            x: 3.5; y: 8; width: 2; height: 4
                            color: "#c94b3d"
                        }
                    }
                }
            }
            Item { width: 20 }
            TextField {
                id: searchField
                placeholderText: "🔍 " + qsTr("Search")
                Layout.preferredWidth: 300
                Layout.preferredHeight: 24
                font.pixelSize: Theme.fontSize
                onTextEdited: {
                    window.selectedIndex = -1
                    controller.search(text)
                }
            }
        }
    }

    PhotoViewer {
        id: photoViewer
        objectName: "photoViewer"
        anchors.fill: parent
        visible: window.viewerOpen
        photosModel: controller.photos
        onClosed: {
            window.viewerOpen = false
            window.selectedIndex = currentIndex   // a rács kövesse a nézőt
        }
        onCurrentIndexChanged: if (visible) window.selectedIndex = currentIndex
    }

    SplitView {
        anchors.fill: parent
        visible: !window.viewerOpen
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
                anchors.margins: 12
                spacing: 4

                LightboxHeader {
                    folderName: controller.currentFolder
                                ? controller.currentFolder.split("/").pop()
                                : qsTr("Library")
                    dateText: controller.folderDateText
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
                        onOpened: function(i) {
                            window.viewerOpen = true
                            photoViewer.show(i)
                        }
                    }
                    ScrollBar.vertical: ScrollBar {}
                }
            }
        }
    }

    footer: Column {
        width: parent.width

        // tömör acélkék infó-sáv; kijelöléskor a kép adatai
        Rectangle {
            width: parent.width; height: 20
            color: Theme.infoBar
            Text {
                anchors.centerIn: parent
                text: window.viewerOpen
                      ? controller.viewerInfo(photoViewer.currentIndex)
                      : (window.selectedIndex >= 0
                         ? controller.photoInfo(window.selectedIndex)
                         : controller.statusText)
                color: Theme.infoBarText
                font.pixelSize: Theme.fontSize
                font.bold: true
            }
        }

        Rectangle {
            width: parent.width; height: 52
            color: Theme.trayBg
            Rectangle {
                width: parent.width; height: 1
                color: Theme.trayBorder
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10; anchors.rightMargin: 10
                spacing: 8

                PicasaButton {
                    text: "★"
                    enabled: window.viewerOpen || window.selectedIndex >= 0
                    Layout.preferredWidth: 34
                    onClicked: controller.toggleStar(
                        window.viewerOpen ? photoViewer.currentIndex
                                          : window.selectedIndex)
                }
                PicasaButton { text: "↺"; enabled: false; Layout.preferredWidth: 34 }
                PicasaButton { text: "↻"; enabled: false; Layout.preferredWidth: 34 }
                Item { width: 8 }
                PicasaButton {
                    text: qsTr("Upload to Google Photos")
                    enabled: false
                    accent: Theme.picasaGreen
                }
                PicasaButton { text: qsTr("E-Mail"); enabled: false }
                PicasaButton { text: qsTr("Print"); enabled: false }
                PicasaButton { text: qsTr("Export"); enabled: false }
                Item { Layout.fillWidth: true }
                Rectangle {
                    width: 14; height: 11; radius: 1
                    color: "#ffffff"; border.color: "#9a9a9a"
                    Rectangle { x: 2; y: 6; width: 10; height: 3; color: "#8ab06a" }
                }
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
