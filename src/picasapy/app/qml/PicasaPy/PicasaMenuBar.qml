import QtQuick
import QtQuick.Controls

// A Picasa 3.9 teljes menüszerkezete (a magyar 3.9-ből dokumentálva).
// A még nem implementált pontok szürkék — a szerkezet a dizájn része.
MenuBar {
    id: bar
    signal rescanRequested()
    signal aboutRequested()
    signal thumbSizePreset(int size)
    signal selectStarredRequested()
    signal selectAllRequested()
    signal clearSelectionRequested()

    Menu {
        title: qsTr("&File")
        MenuItem { text: qsTr("New Album..."); enabled: false }
        MenuItem { text: qsTr("Add Folder to Picasa..."); enabled: false }
        MenuItem { text: qsTr("Add File to Picasa..."); enabled: false }
        MenuItem { text: qsTr("Import From..."); enabled: false }
        MenuSeparator {}
        MenuItem { text: qsTr("Rename..."); enabled: false }
        MenuItem { text: qsTr("Save"); enabled: false }
        MenuItem { text: qsTr("Revert"); enabled: false }
        MenuItem { text: qsTr("Export Picture to Folder..."); enabled: false }
        MenuSeparator {}
        MenuItem { text: qsTr("Locate on Disk"); enabled: false }
        MenuItem { text: qsTr("Delete from Disk"); enabled: false }
        MenuSeparator {}
        MenuItem { text: qsTr("Print..."); enabled: false }
        MenuItem { text: qsTr("E-Mail..."); enabled: false }
        MenuSeparator {}
        MenuItem { text: qsTr("E&xit"); onTriggered: Qt.quit() }
    }
    Menu {
        title: qsTr("&Edit")
        MenuItem { text: qsTr("Copy All Effects"); enabled: false }
        MenuItem { text: qsTr("Paste All Effects"); enabled: false }
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
        MenuItem { text: qsTr("Properties"); enabled: false }
        MenuItem { text: qsTr("Tags"); enabled: false }
        MenuItem { text: qsTr("People"); enabled: false }
        MenuItem { text: qsTr("Places"); enabled: false }
        MenuSeparator {}
        MenuItem { text: qsTr("Slideshow"); enabled: false }
        MenuItem { text: qsTr("Timeline"); enabled: false }
        MenuItem { text: qsTr("Hidden Pictures"); enabled: false }
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
        MenuItem { text: qsTr("View Slideshow"); enabled: false }
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
        MenuItem { text: qsTr("Hide"); enabled: false }
        MenuItem { text: qsTr("Properties"); enabled: false }
    }
    Menu {
        title: qsTr("&Create")
        MenuItem { text: qsTr("Make a Poster..."); enabled: false }
        MenuItem { text: qsTr("Picture Collage..."); enabled: false }
        MenuItem { text: qsTr("Movie"); enabled: false }
    }
    Menu {
        title: qsTr("&Tools")
        MenuItem { text: qsTr("Folder Manager..."); enabled: false }
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
