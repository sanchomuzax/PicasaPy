import QtQuick
import QtQuick.Controls

// „A kollázs kész (kattintson ide)" — a mentés utáni KATTINTHATÓ értesítés
// (#1028). Spec: `picasa-create-features.md` 1.10; a szöveg forrása a
// `collage::done` honosítási kulcs.
//
// ## Miért nem a folyamatjelzőbe megy
//
// A szöveg MÁR MEGVOLT a kódban — csak a folyamatjelző sávba írtuk
// (`collage_save.py`), amit a `CollagePanel` a rá következő pillanatban
// elrejt. A felhasználó tehát a helyes üzenetet egy haldokló
// folyamatjelzőben kapta, egy villanásra, kattinthatatlanul. Innen a
// panasza, hogy a létrehozás után „bezáródik és nem visz sehova".
//
// Az eredetiben ez külön, dedikált értesítés-készítő (`0x0088a020`), ami
// pontosan két erőforrást hivatkozik: a `collage::done` szöveget és a
// kulcsát. Vagyis a lapzárás UTÁN is megmarad — ezért él a gazdában
// (`Main.qml`), nem a panelben, ami közben bezárul.
//
// ## Miért nem visz oda magától
//
// A `locate` a könyvtárban KIJELÖLI a kész képet, de nem nyit nézőt. A
// nagyban megnyitás a felhasználó kattintása — az eredeti is így osztja
// szét a kettőt, és ez tartja meg neki a döntést.
Rectangle {
    id: notice
    objectName: "collageDoneNotice"

    /** A kész kollázs útvonala — a kattintás ezt nyitja meg. */
    property string path: ""

    signal clicked()

    /** Megjelenítés egy elkészült kollázsra. */
    function showFor(utvonal) {
        notice.path = String(utvonal || "")
        notice.visible = notice.path.length > 0
    }

    /** Elrejtés — kattintás után, vagy ha a felhasználó továbblép. */
    function dismiss() {
        notice.visible = false
        notice.path = ""
    }

    visible: false
    implicitWidth: felirat.implicitWidth + 32
    implicitHeight: Math.max(28, felirat.implicitHeight + 12)
    radius: 3
    color: Theme.picasaGreen
    border.width: 1
    border.color: Theme.chromeBorder

    Text {
        id: felirat
        objectName: "collageDoneNoticeText"
        anchors.centerIn: parent
        //: `collage::done` — a kész kollázs kattintható értesítése
        text: qsTr("The collage is ready (click here)")
        font.pixelSize: Theme.fontSize
        color: Theme.panelSelectionText
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: notice.clicked()
    }
}
