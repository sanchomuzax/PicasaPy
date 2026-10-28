import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

Item {
    id: root
    anchors.fill: parent
    required property var movieDialog
    required property var tabs
    required property var previewPanel

    // Az állapotsor a filmcsík alatt, az előnézeti oszlop közepén áll.
    Text {
        objectName: "makemoviepanel/infotext"
        x: previewPanel.x
        y: parent.height - 20 * movieDialog.layoutScale
        width: previewPanel.width
        height: 16 * movieDialog.layoutScale
        horizontalAlignment: Text.AlignHCenter
        elide: Text.ElideMiddle
        color: Theme.textGray
        text: movieDialog.movieInfoText()
    }
    ColumnLayout {
        objectName: "movieFilmstripActions"
        x: 291 * movieDialog.layoutScale
        y: parent.height - 90 * movieDialog.layoutScale
        width: 32 * movieDialog.layoutScale
        height: 72 * movieDialog.layoutScale
        spacing: 4 * movieDialog.layoutScale
        PicasaButton {
            objectName: "movieFilmstripAddButton"
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "+"
            ToolTip.text: qsTr("Add selected clips")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: movieDialog.addSelectedClips()
        }
        PicasaButton {
            objectName: "movieFilmstripDeleteButton"
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "×"
            // A mérce X-e piros jelet mutat.
            labelColor: Theme.movieRemoveMark
            ToolTip.text: qsTr("Remove selected clip")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: movieDialog.deleteSelectedClip()
        }
    }
    ListView {
        id: movieFilmstrip
        objectName: "movieFilmstrip"
        x: 330 * movieDialog.layoutScale
        y: parent.height - 90 * movieDialog.layoutScale
        width: Math.max(0, parent.width - x)
        height: 72 * movieDialog.layoutScale
        orientation: ListView.Horizontal
        // A mérce bélyegei közt 3 képpont a rés (#5288).
        spacing: 3 * movieDialog.layoutScale
        clip: true
        // A mérce bélyegképe képpontról mérve 50 × 50; a sáv magassága ennél nagyobb.
        readonly property real thumbWidth: 50 * movieDialog.layoutScale
        readonly property real thumbHeight: 50 * movieDialog.layoutScale
        // A bélyegsor a sáv vízszintes közepén áll, ha kifér; ha nem fér ki,
        // a görgetés a bal szélről indul.
        readonly property real contentSpan: Math.max(
            0, count * (thumbWidth + spacing) - spacing)
        leftMargin: Math.max(0, (width - contentSpan) / 2)
        rightMargin: leftMargin
        model: movieDialog.movieFilmstripItems
        delegate: Item {
            required property int index
            required property var modelData
            width: movieFilmstrip.thumbWidth
            height: movieFilmstrip.height

            Rectangle {
                objectName: "movieFilmstripFrame"
                anchors.centerIn: parent
                width: movieFilmstrip.thumbWidth
                height: movieFilmstrip.thumbHeight
                color: Theme.panelBg
                border.width: index === tabs.movieClipList.currentIndex ? 2 : 1
                border.color: index === tabs.movieClipList.currentIndex
                    ? Theme.thumbSelection : Theme.chromeBorder
                Image {
                    anchors.fill: parent
                    anchors.margins: 2 * movieDialog.layoutScale
                    source: modelData.kind === "photo" ? modelData.source : ""
                    fillMode: Image.PreserveAspectCrop
                    visible: modelData.kind === "photo"
                    asynchronous: true
                }
            }
            Text {
                anchors.centerIn: parent
                visible: modelData.kind === "text"
                text: qsTr("Text Slide")
                color: Theme.ink
                font.pixelSize: Theme.fontSize - 1
            }
            MouseArea {
                anchors.fill: parent
                onClicked: movieDialog.selectMovieFilmstripItem(index)
            }
        }
    }
}
