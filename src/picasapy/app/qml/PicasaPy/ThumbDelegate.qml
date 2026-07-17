import QtQuick

// Egy indexkép a Lightboxban: fehér keret, hover- és kijelölés-szegély,
// csillag-jelvény, videó-overlay — Picasa-stílusban.
Item {
    id: cell
    required property string name
    required property string thumbUrl
    required property bool star
    required property string caption
    required property bool isVideo
    required property int index
    property bool selected: false
    signal chosen(int index)

    Rectangle {
        id: frame
        anchors.centerIn: parent
        width: image.paintedWidth + 8
        height: image.paintedHeight + 8
        color: "#ffffff"
        border.width: cell.selected ? 3 : (hover.hovered ? 2 : 1)
        border.color: cell.selected ? Theme.thumbSelection
                     : (hover.hovered ? Theme.thumbHover : Theme.thumbBorder)

        Image {
            id: image
            anchors.centerIn: parent
            width: cell.width - 16
            height: cell.height - 16
            source: cell.thumbUrl
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            cache: true
        }

        Text {
            visible: cell.star
            anchors.right: parent.right; anchors.bottom: parent.bottom
            anchors.margins: 3
            text: "★"
            color: Theme.starYellow
            font.pixelSize: 16
            style: Text.Outline; styleColor: "#00000060"
        }

        Rectangle {
            visible: cell.isVideo
            anchors.centerIn: parent
            width: 28; height: 28; radius: 14
            color: "#000000a0"
            Text {
                anchors.centerIn: parent
                text: "▶"; color: "white"; font.pixelSize: 13
            }
        }
    }

    HoverHandler { id: hover }
    TapHandler { onTapped: cell.chosen(cell.index) }
}
