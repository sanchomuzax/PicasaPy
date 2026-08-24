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
//
// ## MELYIK ágon jelenik meg (#1119 → #1168)
//
// A #1119 helyesbítése óta tudjuk: a `collage::done` értesítő
// (`0x0088a020`) a `0x0057aa10`-et hívja, amiben a `Control Panel\Desktop\`
// registrykulcs és a `picasabackground.bmp` szerepel — vagyis az értesítés
// az **„Asztali háttérkép"** ágé, NEM a rendes kollázs-készítésé. A
// tulajdonos háromszor jelezte, hogy a rendes létrehozás után ilyen gomb a
// Picasa 3-ban nincs.
//
// A #1119 óta ez a komponens ezért állt bekötetlenül: „a
// `collageDesktopBackgroundReady` jelzésnek nincs fogadója". A #1168
// (spec 16.1) ezt a hiányt zárja — a fogadó ITT él, nem a gazdában:
//
//   * a `Main.qml` FORRÓ FÁJL, és a kötés egyetlen jelzésről szól;
//   * a `controller` gyökér-kontextus-tulajdonság, tehát a komponens a
//     gazda közreműködése nélkül is eléri;
//   * így a „melyik ágon szólal meg" döntés EGY helyen, a komponens
//     mellett olvasható — a gazda csak a kattintás következményét viszi.
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

    // #1168 (spec 16.1): a jelzés fogadója. CSAK az „Asztali háttérkép"
    // ága — a `collageDesktopBackgroundReady`-t a vezérlő kizárólag akkor
    // adja ki, ha a mentés a háttérkép-gombbal indult (`collage_save.py`,
    // `payload["hatterkep"]`). A rendes `collageDone`-ra SZÁNDÉKOSAN nem
    // kötünk — az volna a #1119-ben javított hiba.
    // #1129: a valódi gazda a LEBEGŐ ÉRTESÍTŐSÁV (`CNotifierPopup`) — az
    // eredetiben ez az esemény ott jelenik meg, és ott tűnik el magától
    // is. Amíg a sáv nincs a felületen példányosítva, ez az értesítés
    // marad az egyetlen jelzés; amint ott van, ELHALLGAT — különben a
    // felhasználó ugyanazt kapná kétszer, két helyen. A kapu:
    // `NotifierBus.attached`.
    Connections {
        target: typeof controller !== "undefined" ? controller : null
        function onCollageDesktopBackgroundReady(path) {
            if (!NotifierBus.attached)
                notice.showFor(path)
        }
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
