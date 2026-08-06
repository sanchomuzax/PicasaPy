import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350: "File Types" fül (options.fen) — a Picasa eredetiben Windows- és
// Mac-ágban KÜLÖN, majdnem duplikált checkbox-listával jelenik meg
// (docs/specs/picasa-fen-dialogs.md 3.11. szak.). A PicasaPy Linux-first,
// nincs platform-elágazás — ezért itt EGYETLEN, egyesített listával épül
// fel. A támogatott kiterjesztések a `scanner/filetypes.py`-ban rögzített,
// FIX halmazok (nem felhasználói beállítás) — a lista ezért csak
// tájékoztató, minden vezérlő tiltott.
ColumnLayout {
    id: root
    spacing: 8
    enabled: false

    Text {
        text: qsTr("In addition to JPEG, also show these file types:")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }

    // a scanner/filetypes.py PHOTO_EXTENSIONS/RAW_EXTENSIONS/
    // VIDEO_EXTENSIONS halmazainak megfelelő kapcsolók — mind mindig
    // "bekapcsolva", mert a PicasaPy-ban ezek a formátumok fixen
    // felismertek, nem felhasználó által ki/bekapcsolhatók
    CheckBox { objectName: "optionsFileTypeBmpCheck"; text: "BMP"; checked: true }
    CheckBox { objectName: "optionsFileTypeGifCheck"; text: "GIF"; checked: true }
    CheckBox { objectName: "optionsFileTypePngCheck"; text: "PNG"; checked: true }
    CheckBox { objectName: "optionsFileTypeTgaCheck"; text: "TGA"; checked: true }
    CheckBox { objectName: "optionsFileTypeTiffCheck"; text: "TIFF"; checked: true }
    CheckBox { objectName: "optionsFileTypeWebpCheck"; text: "WEBP"; checked: false }
    CheckBox { objectName: "optionsFileTypePsdCheck"; text: "PSD"; checked: true }
    RowLayout {
        spacing: 8
        CheckBox { objectName: "optionsFileTypeRawCheck"; text: qsTr("RAW"); checked: true }
        Text {
            text: qsTr("Supported Formats")
            color: Theme.linkBlue
            font.pixelSize: Theme.fontSize
            font.underline: true
        }
    }
    CheckBox { objectName: "optionsFileTypeMoviesCheck"; text: qsTr("Movies"); checked: true }

    Item { Layout.fillHeight: true }
}
