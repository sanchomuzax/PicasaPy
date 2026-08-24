import QtQuick

// Egy indexkép a lightboxban — Picasa 3.9: fehér kártya vékony szürke
// szegéllyel a #eaeaea háttéren; kijelöléskor kétszínű keret (#384,
// constants.ui thumbsel_color1/2): kívül élénk azúr (#009eff), belül
// fehér rés.
Item {
    id: cell
    required property string name
    required property string thumbUrl
    required property bool star
    required property string caption
    required property bool isVideo
    // #463: arc-jelvények — nem `required`, hogy a régebbi (jelvény nélküli)
    // hívók (pl. a tálca-előnézet) változatlanul működjenek
    property bool hasFaces: false
    property bool hasFaceSuggestion: false
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
    // #463: van-e a képhez rendelve hely (ini `geotag=` vagy EXIF GPS) — a
    // jobb alsó sarokban piros pin jelvényt kap (design-guide.md: "Geo-
    // címkés képen piros pin jelvény a jobb alsó sarokban"). Nem required
    // (régi hívók enélkül is működjenek).
    property bool hasGeo: false
    // #455: a kép a képtálcán van-e ("megtartva", `TrayMixin.isHeldAt`) —
    // bal alsó sarokban zöld pin jelvényt kap (a jobb alsó sarok már a
    // csillagé/geo-piné). Nem required (régi hívók enélkül is működjenek).
    property bool held: false
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
    // lasszó: a koordináták a cella saját rendszerében — a fogadó képezi le.
    // #897: a MÓDOSÍTÓK is kellenek, mert a kijelölés már húzás közben
    // frissül, és a Shift/Ctrl a felvételkori állapothoz viszonyít.
    signal lassoDragged(real startX, real startY, real curX, real curY,
                        int modifiers)
    signal lassoFinished(real startX, real startY, real curX, real curY,
                         int modifiers)
    // jobbklikk (#15): fájlműveletek kontextusmenüje — a pozíció a cella
    // saját koordináta-rendszerében, a hívó nyitja meg ott a menüt
    signal contextMenuRequested(int index, real x, real y)
    // #455: fogd-és-vidd — a húzás MÁR KIJELÖLT képről indul (a ki nem
    // jelölt területről továbbra is lasszó lesz, különben elveszne a
    // rács legfontosabb kijelölő gesztusa)
    signal photoDragStarted(int index)

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

    // #384: constants.ui thumbsel_color1/2 — a kijelölt indexkép kerete
    // KÉTSZÍNŰ: kívül élénk azúr (thumbsel_color1 = Theme.thumbSelection),
    // belül egy vékony, a kártyával azonos színű sáv (thumbsel_color2 =
    // #FFFFFF a Picasában; nálunk Theme.thumbCard — sötét témán is a
    // kártya saját színe marad, nem kell külön token). A két réteg a
    // `frame` MÖGÉ, teli téglalapként rajzolódik (nem `border`-ként) —
    // QML Rectangle csak egyszínű keretet tud, két beágyazott, teli
    // téglalap viszont egyszerűen adja ki a "kívül kék, belül fehér rés"
    // hatást. Csak kijelöléskor látszik.
    Rectangle {
        id: selectionOuter
        objectName: "thumbSelectionOuter"
        visible: cell.selected
        anchors.centerIn: frame
        readonly property int outerWidth: 2
        readonly property int innerWidth: 1
        width: frame.width + 2 * (outerWidth + innerWidth)
        height: frame.height + 2 * (outerWidth + innerWidth)
        color: Theme.thumbSelection
    }
    Rectangle {
        id: selectionInner
        objectName: "thumbSelectionInner"
        visible: cell.selected
        anchors.centerIn: frame
        width: frame.width + 2 * selectionOuter.innerWidth
        height: frame.height + 2 * selectionOuter.innerWidth
        color: Theme.thumbCard
    }

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
        // #384: kijelöléskor a saját keret a kártyával egybeolvad — a
        // kék/fehér kettős keretet a selectionOuter/Inner adja alatta;
        // csak a hover/alap állapot rajzol látható 1px keretet.
        border.width: 1
        border.color: cell.selected ? Theme.thumbCard
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

        // #463: a jobb alsó sarok jelvény-sora — csillag és geo-pin egymás
        // mellett (a design-guide.md screenshot-mintája szerint mindkettő
        // ide kerül, ezért Row-ba fogva, hogy ne fedjék egymást).
        Row {
            objectName: "thumbCornerBadges"
            anchors.right: parent.right; anchors.bottom: parent.bottom
            anchors.margins: 3
            spacing: 2
            Image {
                objectName: "geoMark"
                visible: cell.hasGeo
                source: "icons/geo-pin.svg"
                // #463: a jegy réteg-adatokból kiolvasott mérete 8×14 —
                // nálunk a csillaggal vizuálisan arányos magasságra
                // (~14px) skálázva.
                width: 8; height: 14
                sourceSize.width: 8; sourceSize.height: 14
                anchors.bottom: parent.bottom
            }
            Text {
                visible: cell.star
                text: "★"
                color: Theme.starYellow
                font.pixelSize: 15
                style: Text.Outline; styleColor: "#00000060"
                anchors.bottom: parent.bottom
            }
        }

        // #463: arc-jelvények a BAL FELSŐ sarokban (a jobb alsó a
        // csillag/geo soré, a jobb felső a szerkesztés-visszahajtásé, a bal
        // alsó a tálca-jelvényé). Az eredeti méretarányok: „emberek" 14×20,
        // „arc-javaslat" 20×20 a rácsban.
        Row {
            objectName: "thumbFaceBadges"
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.margins: 3
            spacing: 2

            // „van rajta felismert arc"
            Image {
                objectName: "facesMark"
                visible: cell.hasFaces
                source: "icons/faces-badge.svg"
                width: 14; height: 20
                sourceSize.width: 14; sourceSize.height: 20
            }
            // „jóváhagyásra váró névjavaslat" — KÜLÖN jelvény: azt jelzi,
            // hogy elintézetlen dolgod van a képpel (#26 javaslat-folyamat)
            Image {
                objectName: "faceSuggestionMark"
                visible: cell.hasFaceSuggestion
                source: "icons/face-suggestion-badge.svg"
                width: 20; height: 20
                sourceSize.width: 20; sourceSize.height: 20
            }
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

        // #455: a tálcán tartott kép jelvénye — a jobb alsó sarok
        // (csillag/geo) mintája, de a BAL alsó sarokban, hogy ne
        // fedjék egymást.
        Image {
            objectName: "holdMark"
            visible: cell.held
            source: "icons/hold-pin.svg"
            width: 8; height: 14
            sourceSize.width: 8; sourceSize.height: 14
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            anchors.margins: 3
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
    // #455: a húzás „teste" — a DropArea ezt látja `drag.source`-ként, és
    // ebből olvassa ki, hogy fotók érkeznek. Külön, láthatatlan Item kell
    // hozzá: a Drag csatolt tulajdonságai csak Itemre élnek, és a
    // találat-vizsgálat ennek a JELENET-beli helyzetét nézi — ezért követi
    // az egeret húzás közben.
    Item {
        id: dragProxy
        objectName: "thumbDragProxy"
        width: 1; height: 1
        readonly property string payload: "photos"
        Drag.active: mouse.dragging
        Drag.hotSpot.x: 0
        Drag.hotSpot.y: 0
    }

    // A húzás indítása/vége külön, hívható függvényben (a `handleClicked`
    // mintája): így a teszt valódi egéresemény szintetizálása nélkül is
    // végigjátszhatja.
    function beginPhotoDrag() {
        if (!cell.selected) return false
        mouse.dragging = true
        cell.photoDragStarted(cell.index)
        return true
    }
    function endPhotoDrag() {
        if (!mouse.dragging) return
        dragProxy.Drag.drop()
        mouse.dragging = false
    }

    MouseArea {
        id: mouse
        objectName: "thumbMouseArea"
        anchors.fill: parent
        hoverEnabled: true
        preventStealing: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        property bool lassoing: false
        property bool didLasso: false
        property bool dragging: false
        property real pressX: 0
        property real pressY: 0
        onPressed: function(event) {
            if (event.button !== Qt.LeftButton) return
            pressX = event.x; pressY = event.y
            lassoing = false; didLasso = false; dragging = false
        }
        onPositionChanged: function(event) {
            if (!pressed) return
            var moved =
                Math.abs(event.x - pressX) + Math.abs(event.y - pressY) > 8
            // #455: kijelölt képről indulva a kijelölés UTAZIK (fogd-és-
            // vidd), egyébként marad a lasszó
            if (dragging || (moved && !lassoing && cell.selected)) {
                if (!dragging) cell.beginPhotoDrag()
                dragProxy.x = event.x
                dragProxy.y = event.y
                return
            }
            if (!lassoing && moved) lassoing = true
            if (lassoing)
                cell.lassoDragged(
                    pressX, pressY, event.x, event.y, event.modifiers)
        }
        onReleased: function(event) {
            if (dragging) {
                cell.endPhotoDrag()
                didLasso = true   // a rákövetkező clicked ne váltson kijelölést
                return
            }
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
