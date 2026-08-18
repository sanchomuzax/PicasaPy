import QtQuick
import QtQuick.Controls

// A lap ALATT lebegő három gomb — `rand_group` (#948, a #920 7/8 lépcsője).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` **2.4** és **4.4**; a
// geometria a `picasa-create-features.md` **1.10.4** táblájából
// (354 × 28; 115 · 116 · 115 széles gombok, 3 képpontos réssel).
//
// A csoport a lap gyereke (`m_centerX` + `YConstraint 0, 1, 2`): a FELSŐ
// éle van a lap alja alatt 2 képponttal. A helyét a `CollageCanvas`
// számolja a lap téglalapjából — ld. `CollageActionRow.qml`.
//
// ## ⚠️ „Véletlenszerű kollázs" — ugyanaz a parancs, két felirat
//
// A `rand_placement` GOMB felirata „Scramble Collage" / „Véletlenszerű
// kollázs", a helyi menüben ugyanez a parancs „Scatter Pictures" /
// „Képek szétszórása". Nem elírás: a két erőforrás külön szöveget tart,
// és mindkettőt úgy kell átvenni, ahogy van. Aki „egységesíti", az
// eredetitől tér el.
Item {
    id: row
    objectName: "collageRandomRow"

    property var controller: null

    implicitWidth: 354
    implicitHeight: 28
    width: implicitWidth
    height: implicitHeight

    readonly property var capabilities:
        row.controller && row.controller.collageCapabilities
            ? row.controller.collageCapabilities : ({})

    readonly property int selectionCount:
        row.controller && row.controller.collageSelection
            ? row.controller.collageSelection.length : 0

    readonly property int clipCount:
        row.controller ? row.controller.collageClipCount : 0

    function can(name) {
        return row.capabilities[name] === true
    }

    PicasaButton {
        objectName: "collageScrambleButton"
        x: 1; y: 1; width: 115; height: 26
        //: `rand_placement-label` — a GOMB felirata (a menüé más!).
        text: qsTr("Scramble Collage")
        // maszk 3. bitje ÉS legalább egy kép (spec 4.4)
        enabled: row.can("scramble") && row.clipCount >= 1
        //: `rand_placement` buboréksúgó.
        ToolTip.text: qsTr("Mix up the collage layout")
        ToolTip.visible: hovered
        ToolTip.delay: 500
        onClicked: if (row.controller) row.controller.scrambleCollage()
    }

    PicasaButton {
        objectName: "collageShuffleButton"
        x: 119; y: 1; width: 116; height: 26
        text: qsTr("Shuffle Pictures")
        // maszk 2. bitje ÉS legalább KETTŐ kép: egyetlen képet nincs mivel
        // összekeverni (spec 4.4)
        enabled: row.can("shuffle") && row.clipCount >= 2
        //: `rand_order` buboréksúgó.
        ToolTip.text: qsTr("Randomize the order of the pictures")
        ToolTip.visible: hovered
        ToolTip.delay: 500
        onClicked: if (row.controller) row.controller.shufflePictures()
    }

    PicasaButton {
        objectName: "collageViewAndEditButton"
        x: 238; y: 1; width: 115; height: 26
        text: qsTr("View and Edit")
        // PONTOSAN egy kijelölt kép — a szerkesztő egy képet nyit meg.
        //
        // Buboréksúgója SZÁNDÉKOSAN nincs: a `view_and_edit` a
        // `respack`-leltárban buboréksúgó nélkül szerepel
        // (`ui-lefedettseg.md`), és kitalálni nem szabad.
        enabled: row.selectionCount === 1
        onClicked: if (row.controller) row.controller.viewAndEditSelection()
    }
}
