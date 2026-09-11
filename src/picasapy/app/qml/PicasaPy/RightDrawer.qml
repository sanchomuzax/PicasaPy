import QtQuick

//: #754: a jobb oldali fiók — EGY fiók, közös fejléccel, benne vált a négy
//: tartalom (Emberek · Helyek · Címkék · Tulajdonságok). A normatív
//: méretlap: `docs/specs/jobb-fiok-meretek.md`.
//:
//: Előtte négy KÜLÖN `SplitView`-cella volt, négy különböző szélességgel
//: (190 · 320 · 210 · 200) és négy saját fejléccel. Az eredetiben egyetlen
//: fiók van, `rightdrawerpanel/base_decrect`, és a négy panel ugyanarra a
//: helyre van ültetve.
//:
//: ⚠️ Fülsáv NINCS: a `respack.yt`-ban a `tab_container` és mind a négy fül
//: `#`-kal ki van kommentezva a KIADOTT csomagban (a #754 2026-08-16-i
//: helyesbítése). A lapváltás a Nézet menüből megy (#1773).
Rectangle {
    id: fiok
    objectName: "rightDrawer"

    //: a fiók tartalma — a hívó ide teszi a négy panelt
    default property alias tartalom: tartalomTer.data

    //: a fejléc CÍME a lap neve, és ugyanaz a szöveg, mint a Nézet menü
    //: tételéé (a #754 mérése: `PropertiesPanel::title` · `TagPanel::tags`
    //: · `PeoplePanel::title` · `GeoPanel::title`). A `rightdrawerpanel`
    //: „Metaadatok" felirata a fiók SAJÁT neve, de a kiadott program a
    //: panel nevét mutatja — ezért a hívó adja meg.
    property string cim: ""

    //: a `size_toggle` állapota: kicsi (alap) vagy nagy fiók
    property bool nagy: false
    //: az ablak szélessége — a nagy állás ennek a 30 %-a (#2529)
    property real ablakSzelesseg: 0

    //: `RIGHTDRAWEROFFSET -280` (`thumbui.tre:700`)
    readonly property int alapSzelesseg: 280
    //: a nagy állás plafonja: `0x00cf4e40` = 392,0
    readonly property int nagyPlafon: 392
    //: a nagy állás aránya: `0x00cf3ae0` = 0,3
    readonly property real nagyArany: 0.3
    //: `rightdrawerpanel/header`
    readonly property int fejlecMagassag: 30
    //: a tartalom vászna 276 széles (a 280-as fiókban)
    readonly property int tartalomSzelesseg: 276

    //: a MÉRT két szélesség. Keskeny ablakon a kettő egybeeshet — a bináris
    //: is a kisebbiket választja, nem véd ellene.
    readonly property real kivantSzelesseg: nagy
        ? Math.min(fiok.ablakSzelesseg * fiok.nagyArany, fiok.nagyPlafon)
        : fiok.alapSzelesseg

    signal closeRequested()

    color: Theme.panelBg
    border.color: Theme.chromeBorder

    Rectangle {
        id: fejlec
        objectName: "rightDrawerHeader"
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: fiok.fejlecMagassag
        color: Theme.panelBg
        border.color: Theme.chromeBorder

        //: `rightdrawerpanel/size_toggle` 14 × 14, BALRA. A súgója az
        //: eredeti szövege: „Váltás a kis és a nagy oldalpanel közt".
        DrawerHeaderButton {
            id: meretValto
            objectName: "rightDrawerSizeToggle"
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 6
            jel: fiok.nagy ? "‹" : "›"
            sugo: qsTr("Switch between the small and large side panel")
            onKattintva: fiok.nagy = !fiok.nagy
        }

        //: `rightdrawerpanel/title_text` 218 × 19, KÖZÉPRE (`m_centerXY`).
        //: A felirat a FIÓK neve, nem a panelé (`rightdrawerpanel_text.tre:1`).
        Text {
            objectName: "rightDrawerTitle"
            anchors.centerIn: parent
            width: 218
            height: 19
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            text: fiok.cim
            font.pixelSize: Theme.fontSize + 1
            font.bold: true
            color: Theme.ink
        }

        //: `rightdrawerpanel/close` 14 × 14, JOBBRA.
        DrawerHeaderButton {
            objectName: "rightDrawerClose"
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: 6
            jel: "✕"
            sugo: qsTr("Close side panel")
            onKattintva: fiok.closeRequested()
        }
    }

    //: a tartalom y 31-től indul, 276 széles vásznon
    Item {
        id: tartalomTer
        objectName: "rightDrawerContent"
        anchors {
            top: fejlec.bottom
            topMargin: 1
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
        }
        width: Math.min(fiok.width, fiok.tartalomSzelesseg)
    }
}
