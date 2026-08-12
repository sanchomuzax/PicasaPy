import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350: "Slideshow" fül (options.fen) — a PicasaPy diavetítése
// (SlideshowView.qml) ma nem tárol perzisztens ismétlés-/zene-beállítást
// (a hurkolás/zene bekapcsolása jelenleg nincs QSettings-ben), ezért a
// fül tiltott, a FEN `bind enabled` mintáját (a zenei mappa csak akkor
// aktív, ha a lejátszás be van kapcsolva) megőrizve a struktúrában.
ColumnLayout {
    id: root
    spacing: 10
    enabled: false

    CheckBox {
        objectName: "optionsSlideshowLoopCheck"
        text: qsTr("Loop slideshow")
    }

    CheckBox {
        id: playMusicCheck
        objectName: "optionsSlideshowPlayMusicCheck"
        text: qsTr("Play MP3 music during slideshow")
    }
    RowLayout {
        // FEN: <bind attr="enabled" source="PlayMP3Tracks"> — a mappaválasztó
        // csak akkor aktív, ha a zenelejátszás be van kapcsolva
        enabled: playMusicCheck.checked
        spacing: 8
        Text { text: qsTr("Select a music folder:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        TextField { objectName: "optionsSlideshowMusicPathField"; Layout.fillWidth: true; readOnly: true 
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
        }
        Button { objectName: "optionsSlideshowMusicBrowseButton"; text: qsTr("Browse...") }
    }

    Item { Layout.fillHeight: true }
}
