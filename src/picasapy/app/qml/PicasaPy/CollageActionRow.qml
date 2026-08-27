import QtQuick
import QtQuick.Controls

// A lap FÖLÖTT lebegő négy gomb — `action_group` (#948, a #920 7/8 lépcsője).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` **2.4** és **4.4**; a
// geometria a `picasa-create-features.md` **1.10.4** táblájából.
//
// ## Amit ez a fájl NEM csinál: nem tudja, HOL van
//
// A `.tre` szerint a csoport a `previewshadow` (= maga a lap) gyereke,
// `m_centerX` + `YConstraint 1, 0, -2` kényszerrel: az ALSÓ éle van a lap
// teteje fölött 2 képponttal. Ezt a `CollageCanvas` számolja ki a lap
// téglalapjából — így a csoport oldalformátum- és ablakméret-váltáskor is
// a lappal együtt mozog, és a helyszámítás EGY helyen él.
//
// ⚠️ A régi olvasat (`picasa-kollazs-felulet.md` 4.) a vászon abszolút
// koordinátáit adta meg (318, 36). Az a TERVEZŐI alapállás, nem a
// futásidejű hely: aki oda rajzolja, fekvő 4:3-nál még jónak látja, álló
// formátumban viszont a gombsor otthagyja a lapot.
//
// ## A gombok engedélyezése
//
// A négy szabály (spec 4.4) a felhasználó két képernyőképéből is látszik:
// kijelölés nélkül három gomb halvány, egy kijelölt képpel mind aktív.
// A maszkfüggő rész EGYETLEN forrásból jön (`collageCapabilities`) —
// témánkénti `if` itt nem születhet.
Item {
    id: row
    objectName: "collageActionRow"

    property var controller: null

    // A `.tre` csoportmérete: 445 × 28, 1 képpontos belső margóval és
    // 3 képpontos réssel a gombok között.
    implicitWidth: 445
    implicitHeight: 28
    width: implicitWidth
    height: implicitHeight

    readonly property var capabilities:
        row.controller && row.controller.collageCapabilities
            ? row.controller.collageCapabilities : ({})

    readonly property int selectionCount:
        row.controller && row.controller.collageSelection
            ? row.controller.collageSelection.length : 0

    // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
    // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
    readonly property int clipCount:
        (row.controller && row.controller.collageClipCount !== undefined)
            ? row.controller.collageClipCount : 0

    function can(name) {
        return row.capabilities[name] === true
    }

    PicasaButton {
        objectName: "collageSelectAllButton"
        x: 1; y: 1; width: 100; height: 26
        text: qsTr("Select All")
        // maszk 4. bitje ÉS legalább egy kép (spec 4.4)
        enabled: row.can("selection") && row.clipCount >= 1
        //: `select_all` buboréksúgó.
        ToolTip.text: qsTr("Select all the pictures (Ctrl+A)")
        ToolTip.visible: hovered
        ToolTip.delay: 500
        onClicked: if (row.controller) row.controller.selectAllNodes()
    }

    PicasaButton {
        objectName: "collageSelectNoneButton"
        x: 104; y: 1; width: 100; height: 26
        text: qsTr("Select None")
        enabled: row.selectionCount > 0
        //: `select_none` buboréksúgó.
        ToolTip.text: qsTr("Deselect all the pictures (Ctrl+D)")
        ToolTip.visible: hovered
        ToolTip.delay: 500
        onClicked: if (row.controller) row.controller.selectNoNodes()
    }

    PicasaButton {
        objectName: "collageRemoveButton"
        x: 207; y: 1; width: 100; height: 26
        text: qsTr("Remove")
        enabled: row.selectionCount > 0
        //: `remove_node` buboréksúgó.
        ToolTip.text: qsTr("Remove selected items from the collage (Del)")
        ToolTip.visible: hovered
        ToolTip.delay: 500
        onClicked: if (row.controller) row.controller.removeSelectedNodes()
    }

    PicasaButton {
        objectName: "collageSetBackgroundButton"
        x: 310; y: 1; width: 134; height: 26
        text: qsTr("Set as Background")
        // PONTOSAN egy kijelölt kép — a háttérnek egy képe van
        enabled: row.selectionCount === 1
        //: `set_background` buboréksúgó.
        ToolTip.text: qsTr("Use the selected picture as the background")
        ToolTip.visible: hovered
        ToolTip.delay: 500
        onClicked: if (row.controller) row.controller.setBackgroundFromSelection()
    }
}
