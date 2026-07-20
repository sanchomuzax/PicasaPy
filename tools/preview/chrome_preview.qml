import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../src/picasapy/app/qml/PicasaPy"

// Próba-oldal a Picasa widget-króm komponensekhez (#3): PicasaScrollBar és
// PicasaSlider különböző állapotokban. Önálló, semmilyen alkalmazás-
// kontrollerhez nem kötött — csak vizuális ellenőrzésre.
//
// Futtatás: pyside6-qml tools/preview/chrome_preview.qml
// (a fenti relatív import miatt a jelenlegi könyvtárból indítandó).
ApplicationWindow {
    id: root
    width: 720
    height: 520
    visible: true
    color: Theme.canvasBg
    title: "PicasaPy widget-króm próba"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 24

        Text {
            text: "Görgetősáv (PicasaScrollBar)"
            font.pixelSize: Theme.folderTitleSize
            font.bold: true
            color: Theme.ink
        }

        RowLayout {
            spacing: 24
            Layout.fillWidth: true

            // álló görgetősáv — mindig látszó (AlwaysOn), hosszú listán
            ListView {
                id: verticalList
                Layout.preferredWidth: 220
                Layout.preferredHeight: 160
                clip: true
                model: 40
                delegate: Text {
                    width: verticalList.width
                    padding: 4
                    text: "Elem " + (index + 1)
                    color: Theme.ink
                }
                ScrollBar.vertical: PicasaScrollBar {
                    policy: ScrollBar.AlwaysOn
                }
            }

            // fekvő görgetősáv — csak igény szerint (AsNeeded)
            ListView {
                id: horizontalList
                Layout.preferredWidth: 300
                Layout.preferredHeight: 60
                clip: true
                orientation: ListView.Horizontal
                model: 20
                delegate: Rectangle {
                    width: 60; height: 40
                    color: Theme.contentPanel
                    border.color: Theme.thumbBorder
                    Text {
                        anchors.centerIn: parent
                        text: index + 1
                        color: Theme.ink
                    }
                }
                ScrollBar.horizontal: PicasaScrollBar {
                    policy: ScrollBar.AsNeeded
                }
            }
        }

        Text {
            text: "Csúszka (PicasaSlider)"
            font.pixelSize: Theme.folderTitleSize
            font.bold: true
            color: Theme.ink
        }

        // nagyítás-csúszka − / + jelekkel, a kézikönyv 06. fejezete szerint
        RowLayout {
            spacing: 8
            Text { text: "−"; color: Theme.textGray; font.pixelSize: 13 }
            PicasaSlider {
                id: zoomPreview
                from: 72; to: 256; value: 140
            }
            Text { text: "+"; color: Theme.textGray; font.pixelSize: 13 }
            Text {
                text: Math.round(zoomPreview.value) + " px"
                color: Theme.textGray
            }
        }

        RowLayout {
            spacing: 24
            Text { text: "Letiltva:"; color: Theme.ink }
            PicasaSlider {
                enabled: false
                from: 0; to: 1; value: 0.3
            }
        }

        RowLayout {
            spacing: 24
            Text { text: "Álló csúszka:"; color: Theme.ink }
            PicasaSlider {
                orientation: Qt.Vertical
                Layout.preferredHeight: 100
                from: 0; to: 1; value: 0.6
            }
        }

        Item { Layout.fillHeight: true }
    }
}
