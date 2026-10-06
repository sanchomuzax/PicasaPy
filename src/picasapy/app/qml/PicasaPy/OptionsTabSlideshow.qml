import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// #4320: az options.fen ismétlés- és zenebeállításai a vezérlőben
// maradandóak; a mappaválasztó a FEN bind enabled kapcsolatát követi.
ColumnLayout {
    id: root
    spacing: 10

    readonly property var prefs: (typeof controller !== "undefined" && controller)
        ? controller : null

    CheckBox {
        objectName: "optionsSlideshowLoopCheck"
        text: qsTr("Loop slideshow")
        checked: root.prefs && root.prefs.slideshowLoop !== undefined
            ? root.prefs.slideshowLoop : true
        onToggled: if (root.prefs
                && typeof root.prefs.setSlideshowLoop === "function")
            root.prefs.setSlideshowLoop(checked)
    }

    CheckBox {
        id: playMusicCheck
        objectName: "optionsSlideshowPlayMusicCheck"
        text: qsTr("Play music tracks during slideshow")
        checked: root.prefs && root.prefs.slideshowMusicEnabled !== undefined
            ? root.prefs.slideshowMusicEnabled : false
        onToggled: if (root.prefs
                && typeof root.prefs.setSlideshowMusicEnabled === "function")
            root.prefs.setSlideshowMusicEnabled(checked)
    }
    RowLayout {
        // FEN: <bind attr="enabled" source="PlayMP3Tracks"> — a mappaválasztó
        // csak akkor aktív, ha a zenelejátszás be van kapcsolva
        enabled: playMusicCheck.checked
        spacing: 8
        Text { text: qsTr("Select a folder of music tracks:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        TextField {
            objectName: "optionsSlideshowMusicPathField"
            Layout.fillWidth: true
            readOnly: true
            text: root.prefs && root.prefs.slideshowMusicFolder !== undefined
                ? root.prefs.slideshowMusicFolder : ""
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
        }
        Button {
            objectName: "optionsSlideshowMusicBrowseButton"
            text: qsTr("Browse...")
            onClicked: musicFolderDialog.open()
        }
    }

    Item { Layout.fillHeight: true }

    FolderDialog {
        id: musicFolderDialog
        objectName: "optionsSlideshowMusicFolderDialog"
        title: qsTr("Select a folder of music tracks:")
        currentFolder: root.prefs
            && root.prefs.slideshowMusicFolderUrl !== undefined
                ? root.prefs.slideshowMusicFolderUrl : Qt.resolvedUrl(".")
        onAccepted: if (root.prefs)
            root.prefs.setSlideshowMusicFolder(selectedFolder.toLocalFile())
    }
}
