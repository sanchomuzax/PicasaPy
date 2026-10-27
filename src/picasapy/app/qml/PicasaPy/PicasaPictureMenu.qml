import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

PicasaMenu {
    id: menuPicture
    property var bar: null
    title: qsTr("&Picture")
    onAboutToShow: bar.textOverlayStatesRefreshRequested()
    MenuItem {
        objectName: "menuPictureViewAndEdit"
        text: qsTr("&View and Edit") + "\tCtrl+3"
        enabled: bar.photoActionsEnabled
        onTriggered: bar.viewAndEditRequested()
    }
    // #4701: az almenü sorrendje és 19 rekordja a menüleltárban szereplő
    // eredeti táblát követi. Az effektparancsok a kijelölt N kép
    // MINDEGYIKÉRE egyszerre alkalmazott egykattintásos effekt
    // (`controller.applyEffectMany`, `batch_effect_controller`).
    PicasaMenu {
        objectName: "menuPictureBatchEdit"
        title: qsTr("&Batch Edit")
        enabled: bar.photoActionsEnabled
        MenuItem {
            objectName: "menuBatchRename"
            text: qsTr("&Rename...") + "\tF2"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.renameRequested()
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuBatchRotateRight"
            text: qsTr("R&otate Clockwise")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("rotate_cw")
        }
        MenuItem {
            objectName: "menuBatchRotateLeft"
            text: qsTr("Rotate &Counterclockwise")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("rotate_ccw")
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuBatchAutoContrast"
            text: qsTr("A&uto Contrast")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("autolight")
        }
        MenuItem {
            objectName: "menuBatchAutoColor"
            text: qsTr("&Auto Color")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("autocolor")
        }
        MenuItem {
            objectName: "menuBatchEnhance"
            text: qsTr("I'm Feeling Lucky")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("enhance")
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuBatchSepia"
            text: qsTr("&Sepia")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("sepia")
        }
        MenuItem {
            objectName: "menuBatchSharpen"
            text: qsTr("S&harpen")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("unsharp")
        }
        MenuItem {
            objectName: "menuBatchWarmify"
            text: qsTr("&Warmify")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("warm")
        }
        MenuItem {
            objectName: "menuBatchFilmGrain"
            text: qsTr("&Film Grain")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("grain2")
        }
        MenuItem {
            objectName: "menuBatchBlackWhite"
            text: qsTr("&Black and White")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("bw")
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuBatchAutoRedeye"
            text: qsTr("Auto Red Eye Correction")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.batchApplyEffectRequested("redeye")
        }
        MenuSeparator {}
        // #4335: külön parancsok, a kijelölésben levő szövegfedvények
        // aktuális `textactive=` állapota szerint engedélyezve.
        MenuItem {
            objectName: "menuPictureShowText"
            text: qsTr("Show Text")
            enabled: bar.photoActionsEnabled && bar.textOverlayShowEnabled
            onTriggered: bar.textOverlayVisibilityRequested(true)
        }
        MenuItem {
            objectName: "menuPictureHideText"
            text: qsTr("Hide Text")
            enabled: bar.photoActionsEnabled && bar.textOverlayHideEnabled
            onTriggered: bar.textOverlayVisibilityRequested(false)
        }
    }
    // #1774 (mérve): a mentések szerint itt csoporthatár van.
    MenuSeparator {}
    // #465 3. pont: korábban placeholder — a kijelölt kép(ek) teljes
    // szerkesztési láncát törli, megerősítéssel (Main.qml)
    MenuItem {
        objectName: "menuPictureUndoAllEdits"
        text: qsTr("Undo &All Edits")
        enabled: bar.photoActionsEnabled
        onTriggered: bar.undoAllEditsRequested()
    }
    MenuSeparator {}
    MenuItem {
        objectName: "menuPictureHide"
        text: qsTr("&Hide")
        enabled: bar.photoActionsEnabled
        onTriggered: bar.hideToggleRequested()
    }
    // #1774/#4409: az eredetiben az Elrejtés mellett önálló
    // Megjelenítés tétel áll. Mindkét parancs működik: a Hide a helyi
    // menü kapcsolóútját, az Unhide a rejtett kijelölések útját használja.
    MenuItem {
        objectName: "menuPictureUnhide"
        text: qsTr("&Unhide")
        enabled: bar.photoActionsEnabled && bar.hasHiddenPhotoSelection
        onTriggered: bar.unhideRequested()
    }
    // #1774 (mérve): a mentések szerint itt csoporthatár van.
    MenuSeparator {}
    // hiányzott (#324 audit): arc-négyzetek pozíciójának visszaállítása
    // (3. fázis, arcfelismerés-előkészítés)
    MenuItem {
        objectName: "menuPictureResetFaces"
        text: qsTr("Reset &Faces")
        enabled: bar.photoActionsEnabled
        onTriggered: bar.resetFacesRequested()
    }
    // #1774 (mérve): a mentések szerint itt csoporthatár van.
    MenuSeparator {}
    MenuItem {
        objectName: "menuPictureProperties"
        text: qsTr("Properties") + "\tAlt+Enter"
        onTriggered: bar.propertiesPanelRequested()
    }
}
