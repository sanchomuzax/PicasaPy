import QtQuick
import QtQuick.Controls

// A kollázs HÁROM helyi menüje (#948, a #920 7/8 lépcsője).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` **7.6**; a tételsorok és a
// feliratok forrása a `picasa-kollazs-felulet.md` **6.** és a
// `picasa-create-features.md` **1.10.6**.
//
// A `CollageNodeHandler` a jobb gomb LE eseményére (5. esemény) a
// KIJELÖLÉS MÉRETE szerint választ menüt:
//
//   collagenode_context_single    — egy kijelölt kép   (8 tétel)
//   collagenode_context_group     — több kijelölt kép  (3 tétel)
//   collagenode_context_document  — a vászon           (4 tétel)
//
// ## ⚠️ Ugyanannak a parancsnak két felirata van
//
// A `rand_placement` GOMBON „Scramble Collage" / „Véletlenszerű kollázs",
// EBBEN A MENÜBEN „Scatter Pictures" / „Képek szétszórása". A két
// erőforrás külön szöveget tart; mindkettőt úgy kell átvenni, ahogy van.
//
// ## ⚠️ A „270 fok" a FELIRAT, nem a tárolt érték
//
// A négy igazítás a vezérlő `snapRotation` slotján megy át
// (`canvas.snap_theta`), ami a `snap_9`-re **−90,0 fokot** tárol. Aki a
// feliratot írná a `.cxf`-be, a windowsos Picasával elcsúszó fájlt ír.
//
// ## Amit ez a fájl NEM csinál
//
// Nem dönt a kijelölésről és nem számol: minden tétel a vezérlő egy
// slotját hívja. A menü megnyitását a `CollageCanvas` jobbgombos
// egérterülete kéri — ott dől el, melyik menü való a kattintás alá.
Item {
    id: menus
    objectName: "collageContextMenus"

    property var controller: null

    readonly property var capabilities:
        menus.controller && menus.controller.collageCapabilities
            ? menus.controller.collageCapabilities : ({})

    readonly property int selectionCount:
        menus.controller && menus.controller.collageSelection
            ? menus.controller.collageSelection.length : 0

    readonly property int clipCount:
        menus.controller ? menus.controller.collageClipCount : 0

    function can(name) {
        return menus.capabilities[name] === true
    }

    // --- A parancsok: EGY út a vezérlőhöz -----------------------------------

    function applyBorder(key) {
        if (menus.controller)
            menus.controller.setCollageBorder(key)
    }

    //: A menü FELIRATA fok, a tárolt érték a `snap_*` parancsé — ezért megy
    //: a hívás a `snapRotation`-ön át, és nem szöggel.
    function applyAlign(command) {
        if (menus.controller)
            menus.controller.snapRotation(command)
    }

    // --- A megnyitás --------------------------------------------------------

    //: Jobb gomb egy csomóponton. A hívó gondoskodik róla, hogy a megfogott
    //: kép a kijelölés része legyen.
    function openNodeMenu(x, y) {
        if (menus.selectionCount > 1)
            groupMenu.popup(x, y)
        else
            singleMenu.popup(x, y)
    }

    //: Jobb gomb a vászon üres területén.
    //:
    //: ⚠️ A `multiexp` témánál a menü EL VAN NYOMVA: az eredeti kezelő
    //: (`0x0082d3af`–`0x0082d3d0`) lekérdezi a téma kulcsát, és `multiexp`
    //: esetén más ágra ugrik. Nálunk ezt nem téma-hasonlítás, hanem a
    //: képesség-maszk 4. bitje adja — a spec szerint a két kódút
    //: ugyanazt mondja, és nekünk EGY forrásunk van.
    function openCanvasMenu(x, y) {
        if (!menus.can("selection"))
            return
        canvasMenu.popup(x, y)
    }

    // --- A két almenü, EGYSZER megírva --------------------------------------
    //
    // Mindkét csomópont-menü hordozza őket, de a tételsoruk ugyanaz. A
    // `prefix` csak az `objectName`-eket különbözteti meg, hogy a teszt
    // egyértelműen tudjon rájuk hivatkozni.

    component BorderSubmenu: Menu {
        property var host: null
        property string prefix: ""

        //: `CollageS::ChangeBorder`
        title: qsTr("Change Border")

        MenuItem {
            objectName: prefix + "BorderNone"
            text: qsTr("None")
            onTriggered: host.applyBorder("noborder")
        }
        MenuItem {
            objectName: prefix + "BorderWhite"
            text: qsTr("White Border")
            onTriggered: host.applyBorder("whiteborder")
        }
        MenuItem {
            objectName: prefix + "BorderPolaroid"
            text: qsTr("Polaroid Camera")
            onTriggered: host.applyBorder("polaroid")
        }
    }

    component RotationSubmenu: Menu {
        property var host: null
        property string prefix: ""

        //: `CollageS::AlignRotation`
        title: qsTr("Align Rotation")

        MenuItem {
            objectName: prefix + "Align0"
            text: qsTr("0 Degrees")
            onTriggered: host.applyAlign("snap_12")
        }
        MenuItem {
            objectName: prefix + "Align90"
            text: qsTr("90 Degrees")
            onTriggered: host.applyAlign("snap_3")
        }
        MenuItem {
            objectName: prefix + "Align180"
            text: qsTr("180 Degrees")
            onTriggered: host.applyAlign("snap_6")
        }
        MenuItem {
            objectName: prefix + "Align270"
            // ⚠️ a felirat 270, a tárolt érték −90,0 (ld. a fejlécet)
            text: qsTr("270 Degrees")
            onTriggered: host.applyAlign("snap_9")
        }
    }

    // --- 1. Egy kijelölt kép: NYOLC tétel -----------------------------------

    Menu {
        id: singleMenu
        objectName: "collageNodeMenuSingle"

        MenuItem {
            objectName: "collageMenuRemove"
            text: qsTr("Remove")
            onTriggered: if (menus.controller) menus.controller.removeSelectedNodes()
        }
        MenuItem {
            objectName: "collageMenuSetBackground"
            text: qsTr("Set as Background")
            onTriggered: if (menus.controller)
                             menus.controller.setBackgroundFromSelection()
        }
        MenuItem {
            objectName: "collageMenuSetFrameCenter"
            text: qsTr("Set as Frame Center")
            onTriggered: if (menus.controller)
                             menus.controller.setFrameCenterFromSelection()
        }
        BorderSubmenu {
            objectName: "collageMenuChangeBorder"
            host: menus
            prefix: "collageMenu"
        }
        RotationSubmenu {
            objectName: "collageMenuAlignRotation"
            host: menus
            prefix: "collageMenu"
        }
        MenuItem {
            objectName: "collageMenuMoveTop"
            text: qsTr("Bring to Top")
            onTriggered: if (menus.controller) menus.controller.moveSelectionTop()
        }
        MenuItem {
            objectName: "collageMenuMoveBottom"
            text: qsTr("Move to Bottom")
            onTriggered: if (menus.controller) menus.controller.moveSelectionBottom()
        }
        MenuItem {
            objectName: "collageMenuViewAndEdit"
            text: qsTr("View and Edit")
            onTriggered: if (menus.controller) menus.controller.viewAndEditSelection()
        }
    }

    // --- 2. Több kijelölt kép: HÁROM tétel ----------------------------------
    //
    // Ami kimarad, az mind EGY képet vár: háttér, képkockaközéppont,
    // rétegsorrend, megjelenítés és szerkesztés.

    Menu {
        id: groupMenu
        objectName: "collageNodeMenuGroup"

        MenuItem {
            objectName: "collageGroupMenuRemove"
            text: qsTr("Remove")
            onTriggered: if (menus.controller) menus.controller.removeSelectedNodes()
        }
        BorderSubmenu {
            objectName: "collageGroupMenuChangeBorder"
            host: menus
            prefix: "collageGroupMenu"
        }
        RotationSubmenu {
            objectName: "collageGroupMenuAlignRotation"
            host: menus
            prefix: "collageGroupMenu"
        }
    }

    // --- 3. A vászon: NÉGY tétel --------------------------------------------

    Menu {
        id: canvasMenu
        objectName: "collageCanvasMenu"

        MenuItem {
            objectName: "collageCanvasMenuSelectAll"
            text: qsTr("Select All")
            enabled: menus.can("selection") && menus.clipCount >= 1
            onTriggered: if (menus.controller) menus.controller.selectAllNodes()
        }
        MenuItem {
            objectName: "collageCanvasMenuSelectNone"
            text: qsTr("Select None")
            enabled: menus.selectionCount > 0
            onTriggered: if (menus.controller) menus.controller.selectNoNodes()
        }
        MenuItem {
            objectName: "collageCanvasMenuShuffle"
            text: qsTr("Shuffle Pictures")
            enabled: menus.can("shuffle") && menus.clipCount >= 2
            onTriggered: if (menus.controller) menus.controller.shufflePictures()
        }
        MenuItem {
            objectName: "collageCanvasMenuScatter"
            //: ⚠️ a GOMBON ugyanez a parancs „Scramble Collage"
            text: qsTr("Scatter Pictures")
            enabled: menus.can("scramble") && menus.clipCount >= 1
            onTriggered: if (menus.controller) menus.controller.scrambleCollage()
        }
    }
}
