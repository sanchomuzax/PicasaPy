import QtQuick
import QtQuick.Controls

// A Picasa 3.9 teljes menüszerkezete (a magyar 3.9-ből dokumentálva).
// A még nem implementált pontok szürkék — a szerkezet a dizájn része.
MenuBar {
    id: bar
    // van-e kijelölt kép — a fájlművelet- és export-menüpontok feltétele (#15/#16)
    property bool photoActionsEnabled: false
    signal rescanRequested()
    signal aboutRequested()
    signal thumbSizePreset(int size)
    signal selectStarredRequested()
    signal selectAllRequested()
    signal clearSelectionRequested()
    signal folderManagerRequested()
    signal renameRequested()
    signal exportRequested()
    signal locateRequested()
    signal deleteRequested()
    signal slideshowRequested()
    // #12: a Címkék-panel állapota kívülről kötve, a menüpont csak kér
    property bool tagsPanelOpen: false
    signal tagsPanelRequested()
    // #17: Kép → Elrejtés a kijelölésre
    signal hideToggleRequested()
    // #13: Tulajdonságok-panel
    property bool propertiesPanelOpen: false
    signal propertiesPanelRequested()
    // #152: „Copy/Paste All Effects" — a Beillesztés csak akkor engedélyezett,
    // ha van másolt effektlánc (a controller.hasEffectsClipboard-hoz kötve)
    property bool hasEffectsClipboard: false
    signal copyEffectsRequested()
    signal pasteEffectsRequested()

    Menu {
        title: qsTr("&File")
        MenuItem { text: qsTr("New Album..."); enabled: false }
        MenuItem { text: qsTr("Add Folder to Picasa..."); enabled: false }
        MenuItem { text: qsTr("Add File to Picasa..."); enabled: false }
        MenuItem { text: qsTr("Import From..."); enabled: false }
        MenuSeparator {}
        MenuItem {
            objectName: "menuFileRename"
            text: qsTr("Rename...")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.renameRequested()
        }
        MenuItem { text: qsTr("Save"); enabled: false }
        MenuItem { text: qsTr("Revert"); enabled: false }
        MenuItem {
            objectName: "menuFileExport"
            text: qsTr("Export Picture to Folder...")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.exportRequested()
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuFileLocate"
            text: qsTr("Locate on Disk")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.locateRequested()
        }
        MenuItem {
            objectName: "menuFileDelete"
            text: qsTr("Delete from Disk")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.deleteRequested()
        }
        MenuSeparator {}
        MenuItem { text: qsTr("Print..."); enabled: false }
        MenuItem { text: qsTr("E-Mail..."); enabled: false }
        MenuSeparator {}
        MenuItem { text: qsTr("E&xit"); onTriggered: Qt.quit() }
    }
    Menu {
        title: qsTr("&Edit")
        MenuItem {
            objectName: "menuEditCopyEffects"
            text: qsTr("Copy All Effects")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.copyEffectsRequested()
        }
        MenuItem {
            objectName: "menuEditPasteEffects"
            text: qsTr("Paste All Effects")
            enabled: bar.photoActionsEnabled && bar.hasEffectsClipboard
            onTriggered: bar.pasteEffectsRequested()
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Select All")
            onTriggered: bar.selectAllRequested()
        }
        MenuItem {
            text: qsTr("Select Starred")
            onTriggered: bar.selectStarredRequested()
        }
        MenuItem { text: qsTr("Invert Selection"); enabled: false }
        MenuItem {
            text: qsTr("Clear Selection")
            onTriggered: bar.clearSelectionRequested()
        }
    }
    Menu {
        title: qsTr("&View")
        MenuItem { text: qsTr("Library View"); checkable: true; checked: true }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Small Thumbnails")
            onTriggered: bar.thumbSizePreset(96)
        }
        MenuItem {
            text: qsTr("Normal Thumbnails")
            onTriggered: bar.thumbSizePreset(144)
        }
        MenuItem { text: qsTr("Edit View"); enabled: false }
        MenuSeparator {}
        MenuItem {
            objectName: "menuViewProperties"
            text: qsTr("Properties")
            checkable: true
            checked: bar.propertiesPanelOpen
            onTriggered: bar.propertiesPanelRequested()
        }
        MenuItem {
            objectName: "menuViewTags"
            text: qsTr("Tags")
            checkable: true
            checked: bar.tagsPanelOpen
            onTriggered: bar.tagsPanelRequested()
        }
        MenuItem { text: qsTr("People"); enabled: false }
        MenuItem { text: qsTr("Places"); enabled: false }
        MenuSeparator {}
        MenuItem {
            objectName: "menuViewSlideshow"
            text: qsTr("Slideshow")
            onTriggered: bar.slideshowRequested()
        }
        MenuItem { text: qsTr("Timeline"); enabled: false }
        MenuItem {
            objectName: "menuViewHidden"
            text: qsTr("Hidden Pictures")
            checkable: true
            checked: controller.showHidden
            onTriggered: controller.toggleShowHidden()
        }
        Menu {
            title: qsTr("Folder View")
            MenuItem {
                text: qsTr("Sort by creation date")
                checkable: true
                checked: controller.folderSort === "date"
                onTriggered: controller.setFolderSort("date")
            }
            MenuItem {
                text: qsTr("Sort by recent changes")
                checkable: true
                checked: controller.folderSort === "changed"
                onTriggered: controller.setFolderSort("changed")
            }
            MenuItem {
                text: qsTr("Sort by size")
                checkable: true
                checked: controller.folderSort === "size"
                onTriggered: controller.setFolderSort("size")
            }
            MenuItem {
                text: qsTr("Sort by name")
                checkable: true
                checked: controller.folderSort === "name"
                onTriggered: controller.setFolderSort("name")
            }
            MenuSeparator {}
            MenuItem {
                text: qsTr("Reverse sort")
                checkable: true
                checked: controller.folderSortReverse
                onTriggered: controller.toggleFolderSortReverse()
            }
        }
        Menu {
            title: qsTr("Thumbnail Caption")
            MenuItem {
                text: qsTr("None")
                checkable: true
                checked: controller.thumbCaptionMode === "none"
                onTriggered: controller.setThumbCaptionMode("none")
            }
            MenuItem {
                text: qsTr("Filename")
                checkable: true
                checked: controller.thumbCaptionMode === "filename"
                onTriggered: controller.setThumbCaptionMode("filename")
            }
            MenuItem {
                text: qsTr("Caption")
                checkable: true
                checked: controller.thumbCaptionMode === "caption"
                onTriggered: controller.setThumbCaptionMode("caption")
            }
            MenuItem {
                text: qsTr("Tags")
                checkable: true
                checked: controller.thumbCaptionMode === "tags"
                onTriggered: controller.setThumbCaptionMode("tags")
            }
            MenuItem {
                text: qsTr("Resolution")
                checkable: true
                checked: controller.thumbCaptionMode === "resolution"
                onTriggered: controller.setThumbCaptionMode("resolution")
            }
        }
    }
    Menu {
        title: qsTr("F&older")
        MenuItem { text: qsTr("Edit Description..."); enabled: false }
        MenuItem {
            objectName: "menuFolderSlideshow"
            text: qsTr("View Slideshow")
            onTriggered: bar.slideshowRequested()
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Refresh Thumbnails")
            onTriggered: bar.rescanRequested()
        }
        MenuItem { text: qsTr("Sort By"); enabled: false }
        MenuSeparator {}
        MenuItem { text: qsTr("Locate on Disk"); enabled: false }
        MenuItem { text: qsTr("Remove from Picasa..."); enabled: false }
    }
    Menu {
        title: qsTr("&Picture")
        MenuItem { text: qsTr("View and Edit"); enabled: false }
        MenuItem { text: qsTr("Batch Edit"); enabled: false }
        MenuItem { text: qsTr("Undo All Edits"); enabled: false }
        MenuSeparator {}
        MenuItem {
            objectName: "menuPictureHide"
            text: qsTr("Hide")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.hideToggleRequested()
        }
        MenuItem {
            objectName: "menuPictureProperties"
            text: qsTr("Properties")
            onTriggered: bar.propertiesPanelRequested()
        }
    }
    Menu {
        title: qsTr("&Create")
        MenuItem { text: qsTr("Make a Poster..."); enabled: false }
        MenuItem { text: qsTr("Picture Collage..."); enabled: false }
        MenuItem { text: qsTr("Movie"); enabled: false }
    }
    Menu {
        title: qsTr("&Tools")
        MenuItem {
            text: qsTr("Folder Manager...")
            onTriggered: bar.folderManagerRequested()
        }
        MenuItem { text: qsTr("People Manager..."); enabled: false }
        MenuSeparator {}
        MenuItem { text: qsTr("Back Up Pictures..."); enabled: false }
        MenuItem { text: qsTr("Adjust Date and Time..."); enabled: false }
        MenuSeparator {}
        MenuItem { text: qsTr("Options..."); enabled: false }
    }
    Menu {
        title: qsTr("&Help")
        MenuItem { text: qsTr("Help Contents and Index"); enabled: false }
        MenuItem { text: qsTr("Keyboard Shortcuts"); enabled: false }
        MenuSeparator {}
        MenuItem { text: qsTr("Check for Updates"); enabled: false }
        MenuItem {
            text: qsTr("About PicasaPy")
            onTriggered: bar.aboutRequested()
        }
    }
}
