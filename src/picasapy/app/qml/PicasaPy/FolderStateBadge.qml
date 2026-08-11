import QtQuick

// Mappa-állapot jelvény a Mappakezelő fájában (#543).
//
// Az eredeti `foldermgr.tre` három KÉP-erőforrást használ (`icon_once`,
// `icon_exclude`, `icon_always`), nálunk eddig egyetlen szöveges karakter
// állt a helyén. A rajzokat itt primitívekből rakjuk ki (nincs új
// kép-fájl, nincs betűtípus-függő karakter): körkörös nyíl-utalás az
// egyszeri kereséshez, teli pipa a figyelthez, áthúzás a kihagyotthoz.
//
// A `faceExcluded` az arcfelismerés-jelvény (`nofr_on`/`nofr_off`): az
// eredetiben ez KÜLÖN, átfedő ikon — a két állapot független egymástól
// (egy mappa lehet figyelt ÉS arcfelismerésből kizárt).
Item {
    id: badge

    // "always" | "once" | "none".  A név SZÁNDÉKOSAN nem `state`: az az
    // Item beépített (állapotgép-) tulajdonsága, a felülírása hibát adna.
    property string folderState: "none"
    property bool faceExcluded: false
    property color tint: Theme.selectionBlue
    property int size: 11

    implicitWidth: badge.size + (badge.faceExcluded ? badge.size + 3 : 0)
    implicitHeight: badge.size

    // --- állapot-jelvény ---------------------------------------------
    Item {
        id: stateIcon
        width: badge.size
        height: badge.size
        anchors.verticalCenter: parent.verticalCenter
        visible: badge.folderState === "always" || badge.folderState === "once"

        // "Scan Always": teli kör, benne pipa (két elforgatott vonal)
        Rectangle {
            anchors.fill: parent
            radius: width / 2
            color: badge.folderState === "always" ? badge.tint : "transparent"
            border.width: 1
            border.color: badge.tint
        }
        Rectangle {  // a pipa rövid szára
            visible: badge.folderState === "always"
            width: Math.max(2, badge.size * 0.18)
            height: Math.max(2, badge.size * 0.30)
            radius: width / 2
            color: "#ffffff"
            x: badge.size * 0.26
            y: badge.size * 0.45
            rotation: -45
        }
        Rectangle {  // a pipa hosszú szára
            visible: badge.folderState === "always"
            width: Math.max(2, badge.size * 0.18)
            height: Math.max(3, badge.size * 0.55)
            radius: width / 2
            color: "#ffffff"
            x: badge.size * 0.52
            y: badge.size * 0.20
            rotation: 45
        }
        // "Scan Once": félig töltött kör — az egyszeri, nem folytatódó
        // beolvasás jelzése (az eredetiben is halványabb, mint az „always")
        Rectangle {
            visible: badge.folderState === "once"
            width: parent.width / 2
            height: parent.height
            anchors.left: parent.left
            color: badge.tint
            // a bal félkör: a kerek befoglalón belül vágva
            clip: true
            Rectangle {
                width: badge.size
                height: badge.size
                radius: width / 2
                color: badge.tint
            }
        }
    }

    // --- arcfelismerés-jelvény (áthúzott arc) -------------------------
    Item {
        id: faceIcon
        objectName: "folderFaceExcludedBadge"
        width: badge.size
        height: badge.size
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        visible: badge.faceExcluded

        Rectangle {
            anchors.fill: parent
            radius: width / 2
            color: "transparent"
            border.width: 1
            border.color: badge.tint
        }
        Rectangle {  // az áthúzás
            width: Math.max(2, badge.size * 0.16)
            height: badge.size * 1.15
            radius: width / 2
            color: badge.tint
            anchors.centerIn: parent
            rotation: 45
        }
    }
}
