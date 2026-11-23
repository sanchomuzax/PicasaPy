import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

PicasaMenu {
    id: menuPicture
    property var bar: null
    // #7389: nyitott paraméterpanelnél a Kép menü hét tétele és a
    // Csoportos szerkesztés almenü letiltott.
    readonly property bool pictureActionsEnabled: !!bar && bar.photoActionsEnabled && !bar.paramPanelActive
    title: qsTr("&Picture")
    MenuItem {
        objectName: "menuPictureViewAndEdit"
        text: qsTr("&View and Edit") + "\tCtrl+3"
        enabled: menuPicture.pictureActionsEnabled
        onTriggered: bar.viewAndEditRequested()
    }
    // #4701: az almenü sorrendje és 19 rekordja a menüleltárban szereplő
    // eredeti táblát követi. Az effektparancsok a kijelölt N kép
    // MINDEGYIKÉRE egyszerre alkalmazott egykattintásos effekt
    // (`controller.applyEffectMany`, `batch_effect_controller`).
    PicasaMenu {
        objectName: "menuPictureBatchEdit"
        title: qsTr("&Batch Edit")
        enabled: menuPicture.pictureActionsEnabled
        MenuItem {
            objectName: "menuBatchRename"
            text: qsTr("&Rename...") + "\tF2"
            enabled: menuPicture.pictureActionsEnabled
            onTriggered: bar.renameRequested()
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuBatchRotateRight"
            text: qsTr("R&otate Clockwise")
            enabled: menuPicture.pictureActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("rotate_cw")
        }
        MenuItem {
            objectName: "menuBatchRotateLeft"
            text: qsTr("Rotate &Counterclockwise")
            enabled: menuPicture.pictureActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("rotate_ccw")
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuBatchAutoContrast"
            text: qsTr("A&uto Contrast")
            enabled: menuPicture.pictureActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("autolight")
        }
        MenuItem {
            objectName: "menuBatchAutoColor"
            text: qsTr("&Auto Color")
            enabled: menuPicture.pictureActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("autocolor")
        }
        MenuItem {
            objectName: "menuBatchEnhance"
            text: qsTr("I'm Feeling Lucky")
            enabled: menuPicture.pictureActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("enhance")
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuBatchSepia"
            text: qsTr("&Sepia")
            enabled: menuPicture.pictureActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("sepia")
        }
        MenuItem {
            objectName: "menuBatchSharpen"
            text: qsTr("S&harpen")
            enabled: menuPicture.pictureActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("unsharp")
        }
        MenuItem {
            objectName: "menuBatchWarmify"
            text: qsTr("&Warmify")
            enabled: menuPicture.pictureActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("warm")
        }
        MenuItem {
            objectName: "menuBatchFilmGrain"
            text: qsTr("&Film Grain")
            enabled: menuPicture.pictureActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("grain2")
        }
        MenuItem {
            objectName: "menuBatchBlackWhite"
            text: qsTr("&Black and White")
            enabled: menuPicture.pictureActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("bw")
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuBatchAutoRedeye"
            text: qsTr("Auto Red Eye Correction")
            enabled: menuPicture.pictureActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("redeye")
        }
        MenuSeparator {}
        // #4335/#7122: az eredeti (`0x0056e1c0`) a két tételt csak a csoport
        // közös szürkítő ágában tiltja, ezért a kapujuk a csoporté. A menünyitás
        // nem olvas ini-t; a kattintás (`setTextOverlayVisibleMany`) dönti el,
        // melyik képen van átállítandó szövegfedvény.
        MenuItem {
            objectName: "menuPictureShowText"
            text: qsTr("Show Text")
            enabled: menuPicture.pictureActionsEnabled
            onTriggered: bar.textOverlayVisibilityRequested(true)
        }
        MenuItem {
            objectName: "menuPictureHideText"
            text: qsTr("Hide Text")
            enabled: menuPicture.pictureActionsEnabled
            onTriggered: bar.textOverlayVisibilityRequested(false)
        }
    }
    // #1774 (mérve): a mentések szerint itt csoporthatár van.
    MenuSeparator {}
    // #465 3. pont: korábban placeholder — a kijelölt kép(ek) teljes
    // szerkesztési láncát törli, megerősítéssel (Main.qml). #7017: az
    // eredeti szerkesztettségi állapot szerint szürke, ha nincs szerkesztett
    // kép a kijelölésben, vagy az első szerkesztett kép csak elforgatott.
    MenuItem {
        objectName: "menuPictureUndoAllEdits"
        text: qsTr("Undo &All Edits")
        enabled: menuPicture.pictureActionsEnabled && bar.undoAllEditsEnabled
        onTriggered: bar.undoAllEditsRequested()
    }
    MenuSeparator {}
    MenuItem {
        objectName: "menuPictureHide"
        text: qsTr("&Hide")
        enabled: menuPicture.pictureActionsEnabled
        onTriggered: bar.hideToggleRequested()
    }
    // #1774/#4409: az eredetiben az Elrejtés mellett önálló
    // Megjelenítés tétel áll. Mindkét parancs működik: a Hide a helyi
    // menü kapcsolóútját, az Unhide a rejtett kijelölések útját használja.
    MenuItem {
        objectName: "menuPictureUnhide"
        text: qsTr("&Unhide")
        enabled: menuPicture.pictureActionsEnabled && bar.hasHiddenPhotoSelection
        onTriggered: bar.unhideRequested()
    }
    // #1774 (mérve): a mentések szerint itt csoporthatár van.
    MenuSeparator {}
    // hiányzott (#324 audit): arc-négyzetek pozíciójának visszaállítása
    // (3. fázis, arcfelismerés-előkészítés)
    MenuItem {
        objectName: "menuPictureResetFaces"
        text: qsTr("Reset &Faces")
        enabled: menuPicture.pictureActionsEnabled
        onTriggered: bar.resetFacesRequested()
    }
    // #1774 (mérve): a mentések szerint itt csoporthatár van.
    MenuSeparator {}
    MenuItem {
        objectName: "menuPictureProperties"
        text: qsTr("Properties") + "\tAlt+Enter"
        enabled: !bar || !bar.paramPanelActive
        onTriggered: bar.propertiesPanelRequested()
    }
}
