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
    // #100: van-e a képen Picasa-szerkesztés (filters=) — a jobb felső
    // sarok kék „visszahajtás" jelölője erre köt. Nem required: a régi
    // hívóhelyek (próba-oldalak, tesztek) enélkül is működnek.
    property bool hasEdits: false
    // #17: rejtett kép — csak a Nézet → Rejtett képek kapcsolóval látszik,
    // ilyenkor félig áttetsző (Picasa-minta). Nem required (régi hívók).
    property bool isHidden: false
    // #85: kiegyenlített rács-sor esetén a cella (parent Item) nagyobb
    // lehet a névleges thumbSize-nál — a MEGJELENÍTETT kép mérete ekkor
    // is a névleges méretre plafonozott marad (0 = nincs plafon), hogy a
    // #83-mal beállított DPR-arányos thumbnail-cache-t ne nagyítsuk fel
    // (recés/homályos lenne). A többletet a cellán belüli térköz kapja —
    // a kép középen marad, csak a hézag nő.
    property int maxContentWidth: 0
    property int maxContentHeight: 0
    readonly property real contentWidth:
        maxContentWidth > 0 ? Math.min(cell.width, maxContentWidth) : cell.width
    readonly property real contentHeight:
        maxContentHeight > 0 ? Math.min(cell.height, maxContentHeight) : cell.height
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
        objectName: "thumbFrame"
        // #17: a rejtett (de előhívott) kép félig áttetsző
        opacity: cell.isHidden ? 0.45 : 1
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
            objectName: "thumbImage"
            anchors.centerIn: parent
            width: cell.contentWidth - 18
            height: cell.contentHeight - 18 - cell.captionStrip
            source: cell.thumbUrl
            fillMode: Image.PreserveAspectFit
            // #53: offscreen (teszt) platformon SZINKRON betöltés — az async
            // kép-betöltő szál (QQuickPixmapReader) a Python image-providert
            // a GIL-en át hívja, miközben a főszál egy natív Qt-hívásban
            // (pl. setProperty) tartja a GIL-t → kölcsönös várakozás
            // (GIL-deadlock). A főszálon (szinkron) betöltve nincs második
            // szál, így nincs holtpont. Produkcióban marad az async (a UI
            // ne akadjon meg a dekódolásra).
            asynchronous: Qt.platform.pluginName !== "offscreen"
            cache: true
            // #83: a cache-elt thumbnail (application.py: DPR-arányos
            // méret) mindig legalább a legnagyobb rács-fokozatnyi — ez az
            // Image ezért csak KICSINYÍT. A mipmap a köztes csúszka-
            // fokokon élesebb, moiré-mentes kicsinyítést ad; a smooth a
            // felnagyítás nélküli oldalak bilineáris simítását biztosítja.
            smooth: true
            mipmap: true
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

        // #100: mini kék „visszahajtás" a jobb felső sarokban, ha a képen
        // Picasa-szerkesztés van. Szín: Theme.infoBar — szándékosan NEM a
        // kijelölés azúrja (thumbSelection), hogy a két jelentés ne
        // mosódjon össze. Megvalósítás: 45°-ban forgatott négyzet, aminek
        // a középpontja a kártya sarkán ül — a clip levágja, a bent maradó
        // fele adja a behajtott lapsarok-háromszöget (statikus, olcsó).
        Item {
            objectName: "editsFoldMark"
            visible: cell.hasEdits
            width: 12; height: 12
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.margins: 1
            clip: true
            Rectangle {
                width: 17; height: 17
                rotation: 45
                x: parent.width - width / 2
                y: -height / 2
                color: Theme.infoBar
            }
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
        width: cell.contentWidth - 8
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
