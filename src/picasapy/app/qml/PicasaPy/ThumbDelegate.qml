import QtQuick

// Egy indexkép a lightboxban — Picasa 3.9: fehér kártya vékony szürke
// szegéllyel a #eaeaea háttéren; kijelöléskor élénk azúr (#009eff) keret.
Item {
    id: cell
    required property string name
    required property string thumbUrl
    required property bool star
    required property string caption
    required property bool isVideo
    required property int index
    required property string keywords
    required property string resolution
    property bool selected: false
    property string captionMode: "none"
    signal chosen(int index, int modifiers)
    signal opened(int index)

    readonly property string captionText: {
        switch (cell.captionMode) {
        case "filename": return cell.name
        case "caption": return cell.caption
        case "tags": return cell.keywords
        case "resolution": return cell.resolution
        default: return ""
        }
    }

    Rectangle {
        id: frame
        anchors.centerIn: parent
        width: image.paintedWidth + 10
        height: image.paintedHeight + 10
        color: Theme.thumbCard
        border.width: cell.selected ? 3 : 1
        border.color: cell.selected ? Theme.thumbSelection
                     : (mouse.containsMouse ? Theme.thumbHover : Theme.thumbBorder)

        Image {
            id: image
            anchors.centerIn: parent
            width: cell.width - 18
            height: cell.height - 18
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
            font.pixelSize: 15
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

    Text {
        objectName: "thumbCaption"
        visible: cell.captionMode !== "none"
        anchors.top: frame.bottom
        anchors.topMargin: 2
        anchors.horizontalCenter: frame.horizontalCenter
        width: cell.width - 8
        horizontalAlignment: Text.AlignHCenter
        elide: Text.ElideMiddle
        text: cell.captionText
        font.pixelSize: 10
        color: Theme.textGray
    }

    // MouseArea kell (nem TapHandler): a Ctrl/Shift módosítókat is
    // továbbadjuk a többes kijelöléshez
    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        onClicked: function(event) { cell.chosen(cell.index, event.modifiers) }
        onDoubleClicked: cell.opened(cell.index)
    }
}
