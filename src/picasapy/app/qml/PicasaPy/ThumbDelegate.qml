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
    // lasszó: a koordináták a cella saját rendszerében — a fogadó képezi le
    signal lassoDragged(real startX, real startY, real curX, real curY)
    signal lassoFinished(real startX, real startY, real curX, real curY,
                         int modifiers)
    // jobbklikk (#15): fájlműveletek kontextusmenüje — a pozíció a cella
    // saját koordináta-rendszerében, a hívó nyitja meg ott a menüt
    signal contextMenuRequested(int index, real x, real y)

    readonly property string captionText: {
        switch (cell.captionMode) {
        case "filename": return cell.name
        case "caption": return cell.caption
        case "tags": return cell.keywords
        case "resolution": return cell.resolution
        default: return ""
        }
    }
    // a felirat-sáv a cella aljából van fenntartva — a kép nem lóghat bele
    readonly property int captionStrip: captionMode !== "none" ? 16 : 0

    Rectangle {
        id: frame
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: -cell.captionStrip / 2
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
            height: cell.height - 18 - cell.captionStrip
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
    // továbbadjuk, és innen indul a lasszós kijelölés is (az egér-grab a
    // lenyomó cellánál marad, így cellahatárokon át is követjük a húzást).
    MouseArea {
        id: mouse
        objectName: "thumbMouseArea"
        anchors.fill: parent
        hoverEnabled: true
        preventStealing: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        property bool lassoing: false
        property bool didLasso: false
        property real pressX: 0
        property real pressY: 0
        onPressed: function(event) {
            if (event.button !== Qt.LeftButton) return
            pressX = event.x; pressY = event.y
            lassoing = false; didLasso = false
        }
        onPositionChanged: function(event) {
            if (!pressed) return
            if (!lassoing
                && Math.abs(event.x - pressX) + Math.abs(event.y - pressY) > 8)
                lassoing = true
            if (lassoing)
                cell.lassoDragged(pressX, pressY, event.x, event.y)
        }
        onReleased: function(event) {
            if (lassoing) {
                cell.lassoFinished(
                    pressX, pressY, event.x, event.y, event.modifiers)
                lassoing = false
                didLasso = true   // a rákövetkező clicked ne váltson kijelölést
            }
        }
        onClicked: function(event) {
            cell.handleClicked(event.button, event.modifiers, event.x, event.y)
        }
        onDoubleClicked: cell.opened(cell.index)
    }

    // a tényleges elágazás külön, hívható függvényben (nem az onClicked
    // kezelőben) — így teszt közvetlenül hívhatja, valódi egéresemény
    // szintetizálása nélkül (a TestLasso.applyLasso mintája, #15)
    function handleClicked(button, modifiers, x, y) {
        if (button === Qt.RightButton) {
            cell.contextMenuRequested(cell.index, x, y)
            return
        }
        if (!mouse.didLasso) cell.chosen(cell.index, modifiers)
    }
}
