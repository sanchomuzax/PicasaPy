import QtQuick
import QtQuick.Controls

// A Kollázs-panel VÁZA és a MÉRETEZÉSI TÖRVÉNYE (#945, a #920 4/8 lépcsője).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` 2. (a teljes levezetés) és 4.1.
//
// ## A törvény, egy mondatban
//
//     A bal hasáb FIX MÉRETŰ, a vászon-oldal NYÚLIK.
//
// A `respack.yt` `collagepanel.tre` kényszereiből, megerősítetten:
//
//   tabbase:        m_offsetLT + YConstraint 1, 0, 406   → FIX 276 × 386
//   makedesktop|share|reset|cancel: m_offsetLB           → a fix tabbase
//                                                          aljához kötve,
//                                                          tehát szintén fix
//   rightcontainer: m_offsetLTRB                         → mind a négy él nyúlik
//   previewinset  = previewclip − (12, 35, 12, 35)
//   lap (sheet)   = previewinset-be illesztve, az oldalformátum arányával,
//                   KÖZÉPEN
//
// A 35 képpontos függőleges behúzás nem véletlen: pontosan a lap fölött és
// alatt lebegő gombsor (28 px) + 2 px rés + 5 px levegő. A rendszer
// önmagával konzisztens — ez erős megerősítés arra, hogy az olvasat helyes.
//
// A felhasználó képernyőképe SZÁMSZERŰEN igazolja: egy ~1352 px széles
// ablakban a négy alsó gomb ugyanott van, ahol 800 px-esben, és alattuk nagy
// üres sáv marad a bal hasábban. Ha a hasáb nyúlna, a gombok az ablak aljára
// ülnének.
//
// ⚠️ Ez a #411 precedense: fix szélességű oldalpanelt TILOS ablakarányosan
// skálázni. A #405 ezt egyszer már elrontotta, és a felhasználó
// screenshot-összevetése bizonyította a hibát.
//
// ## Mit NEM csinál ez a fájl
//
// A váz a HELYEKET adja meg, nem a tartalmat. A `collageSettingsTab`, a
// `collageClipsTab` és a `collageCanvas` tartalma külön jegyeké (#946, #949,
// #947); itt üres, megjelölt tartók állnak a helyükön, a spec szerinti
// `objectName`-mel és geometriával. Aki oda beköltözik, a tartót cseréli —
// a méretezési törvényhez nem nyúl.
Item {
    id: panel
    objectName: "collagePanel"

    // A tervezővászon mérete. Ez alatt a vászon-oldal zsugorodik a
    // `previewinset` nulla méretéig — a bal hasáb SOHA (spec 2.6).
    implicitWidth: 800
    implicitHeight: 534

    //: A vezérlő (AppController + CollageMixin). Teszteléshez becserélhető.
    property var controller: null

    // --- A bal hasáb: FIX ---------------------------------------------------

    readonly property int columnX: 3
    readonly property int columnY: 20
    readonly property int columnWidth: 276
    readonly property int columnHeight: 386

    // --- A vászon-oldal: NYÚLIK --------------------------------------------

    readonly property int canvasLeft: 289
    readonly property int canvasTop: 20
    readonly property int canvasRight: 10
    readonly property int canvasBottom: 10

    // a `previewinset` behúzása a vászonkereten belül
    readonly property int insetX: 12
    readonly property int insetY: 35

    // A lap oldalaránya: MAGASSÁG / SZÉLESSÉG (spec 8.1 `collagePageRatio`).
    // Vezérlő nélkül a 4:3 fekvő alapállás — a `.tre`-ben a fekvő az előre
    // lenyomott (spec 9.3).
    readonly property real pageRatio:
        panel.controller ? panel.controller.collagePageRatio : 0.75

    readonly property int clipCount:
        panel.controller ? panel.controller.collageClipCount : 0

    // A lap téglalapja a VÁSZON koordinátarendszerében: a `previewinset`-be
    // arányosan illesztve, középen, egész képpontra kerekítve.
    //
    // Az illesztés a szélességgel indul, és csak akkor vált magasságra, ha
    // úgy nem férne be — így a lap mindig a behúzáson BELÜL marad.
    readonly property rect sheetRect: {
        const insetW = Math.max(0, canvasArea.width - 2 * panel.insetX)
        const insetH = Math.max(0, canvasArea.height - 2 * panel.insetY)
        if (insetW <= 0 || insetH <= 0 || panel.pageRatio <= 0)
            return Qt.rect(0, 0, 0, 0)
        let w = insetW
        let h = w * panel.pageRatio
        if (h > insetH) {
            h = insetH
            w = h / panel.pageRatio
        }
        w = Math.round(w)
        h = Math.round(h)
        return Qt.rect(panel.insetX + Math.round((insetW - w) / 2),
                       panel.insetY + Math.round((insetH - h) / 2),
                       w, h)
    }

    readonly property rect canvasArea: Qt.rect(
        panel.canvasLeft,
        panel.canvasTop,
        Math.max(0, panel.width - panel.canvasLeft - panel.canvasRight),
        Math.max(0, panel.height - panel.canvasTop - panel.canvasBottom))

    // --- Elemfa -------------------------------------------------------------

    Rectangle {
        anchors.fill: parent
        color: Theme.canvasBg
    }

    // A bal hasáb. A mérete BEÉGETETT, nem a szülőből számolt — ez maga a
    // törvény.
    Item {
        id: tabBase
        objectName: "collageTabBase"
        x: panel.columnX
        y: panel.columnY
        width: panel.columnWidth
        height: panel.columnHeight

        Rectangle {
            anchors.fill: parent
            color: Theme.chromeBg
            border.width: 1
            border.color: Theme.chromeBorder
        }

        CollagePanelTabBar {
            id: tabBar
            // (3, 25) abszolút = a tabbase tetejétől 5 px (`.tre`: tabs)
            x: 0
            y: 5
            width: parent.width
            clipCount: panel.clipCount
        }

        // A két laptartalom UGYANOTT ül; mindig pontosan az egyik látszik.
        // (13, 55) abszolút = a tabbase-hez képest (10, 35).
        Item {
            id: settingsTab
            objectName: "collageSettingsTab"
            x: 10
            y: 35
            width: 266
            height: 351
            visible: tabBar.currentIndex === 0
            // TARTALOM: #946 („Beállítások" lap). A tartó geometriája a
            // spec 4.1-é; aki ide költözik, a törvényhez nem nyúl.
        }

        Item {
            id: clipsTab
            objectName: "collageClipsTab"
            x: 10
            y: 35
            width: 256
            height: 352
            visible: tabBar.currentIndex === 1
            // TARTALOM: #949 („Képek" lap).
        }
    }

    // A négy alsó gomb. A `.tre` szerint a FIX tabbase aljához vannak kötve
    // (`m_offsetLB`), ami — mivel a tabbase fix — egyenértékű a panel
    // bal-felső sarkához mért rögzített helyzettel (spec 2.6).
    PicasaButton {
        objectName: "collageMakeDesktopButton"
        x: 10; y: 415; width: 127; height: 28
        text: qsTr("Desktop Background")
        //: Buboréksúgó az „Asztali háttérkép" gombon.
        ToolTip.text: qsTr("Save the picture as a JPG in the Collages album, then set "
                   + "it as your desktop background")
        ToolTip.visible: hovered
        ToolTip.delay: 500
        onClicked: if (panel.controller) panel.controller.createCollage(true)
    }
    PicasaButton {
        objectName: "collageShareButton"
        x: 147; y: 415; width: 133; height: 28
        text: qsTr("Create Collage")
        //: Buboréksúgó a „Kollázs létrehozása" gombon.
        ToolTip.text: qsTr("Save as a JPG in the Collages album (in the Projects "
                   + "collection).")
        ToolTip.visible: hovered
        ToolTip.delay: 500
        onClicked: if (panel.controller) panel.controller.createCollage(false)
    }
    PicasaButton {
        objectName: "collageResetButton"
        x: 10; y: 448; width: 127; height: 28
        text: qsTr("Reset")
        //: Buboréksúgó az „Alaphelyzet" gombon.
        ToolTip.text: qsTr("Undo all changes")
        ToolTip.visible: hovered
        ToolTip.delay: 500
        onClicked: if (panel.controller) panel.controller.resetCollage()
    }
    PicasaButton {
        id: closeButton
        objectName: "collageCloseButton"
        x: 147; y: 448; width: 133; height: 28
        text: qsTr("Close")
        //: Buboréksúgó a „Bezárás" gombon.
        ToolTip.text: qsTr("Close the Collage tab")
        ToolTip.visible: hovered
        ToolTip.delay: 500
        onClicked: panel.requestClose()
    }

    // A vászon-oldal: ez NYÚLIK az ablakkal.
    Item {
        id: canvas
        objectName: "collageCanvas"
        x: panel.canvasArea.x
        y: panel.canvasArea.y
        width: panel.canvasArea.width
        height: panel.canvasArea.height

        // A lap. A GEOMETRIÁJA ezé a jegyé (a méretezési törvény része); a
        // TARTALMA — csomópontok, gyűrű, árnyék — a #947-é.
        Rectangle {
            objectName: "collageSheet"
            x: panel.sheetRect.x
            y: panel.sheetRect.y
            width: panel.sheetRect.width
            height: panel.sheetRect.height
            visible: width > 0 && height > 0
            color: Theme.contentPanel
            border.width: 1
            border.color: "#9a9a9a"
        }
    }

    // Az Esc a Bezárás (`.tre`: cancelbutton `Property escapekey 1`).
    //
    // ⚠️ A `focus: true` NEM díszítés: nélküle a `Keys` csatolt kezelő
    // SOHA nem tüzel, mert billentyűesemény csak fókuszált elemhez jut el.
    // Mérve: fókusz nélkül az Esc nulla `closeCollage()` hívást adott.
    focus: true

    Keys.onEscapePressed: function (event) {
        panel.requestClose()
        event.accepted = true
    }

    // A mentetlen módosítás háromgombos megerősítése a #949-é; addig a
    // bezárás közvetlen.
    function requestClose() {
        if (panel.controller)
            panel.controller.closeCollage()
    }
}
