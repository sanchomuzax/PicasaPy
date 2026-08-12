import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350: "Web Albums" fül (options.fen) — V3/felhő hatókör (PicasaWeb-
// szinkron), a PicasaPy-ban ma nincs webalbum-feltöltés, ezért a teljes
// fül tiltott.
//
// Figyelemre méltó FEN-részlet (ld. docs/specs/picasa-fen-dialogs.md
// 3.11. szak.): a "Ne kérdezzen rá minden szinkronizálásnál" checkbox
// `name` attribútuma `confirmsync::disable` — ez NEM ennek a fülnek a
// saját kulcsa, hanem a `confirmsync.fen` (Album szinkronizálás
// megerősítése) dialógusát néma állapotba kapcsoló globális kulcs. Ha a
// PicasaPy egyszer megépíti a webalbum-szinkront és a hozzá tartozó
// megerősítő dialógust, ÉRDEMES ezt a mintát követni: a #367-es
// `confirmSettings`/"decision key" tár pont erre a célra való (a kulcs
// itt "confirmsync" lenne).
ColumnLayout {
    id: root
    spacing: 10
    enabled: false

    RowLayout {
        spacing: 8
        Text { text: qsTr("Default upload size:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        ComboBox {
            objectName: "optionsWebUploadSizeCombo"
            model: ["800px", "1024px", "1600px", qsTr("Original size")]
        }
    }
    CheckBox { objectName: "optionsWebStripedUploadCheck"; text: qsTr("Upload previews first for large files") }
    CheckBox { objectName: "optionsWebKeepJpegQualityCheck"; text: qsTr("Keep original picture quality (uses more storage)") }
    CheckBox { objectName: "optionsWebStarredOnlyCheck"; text: qsTr("Sync starred photos only") }
    // ld. a fájl fejlécében: ez a "confirmsync" globális döntés-kulcsot
    // némítaná el, NEM egy saját webalbum-beállítás
    CheckBox {
        objectName: "optionsWebConfirmSyncDisableCheck"
        text: qsTr("Don't confirm each sync (use previous settings)")
    }
    CheckBox { objectName: "optionsWebUploadNameTagsCheck"; text: qsTr("Upload name tags") }
    CheckBox { objectName: "optionsWebWatermarkCheck"; text: qsTr("Add a watermark to all photo uploads:") }
    TextField { objectName: "optionsWebWatermarkTextField"; Layout.fillWidth: true 
        // #422: jobbklikk-menü (Picasa `Address`)
        TextFieldContextArea {}
    }

    Item { Layout.fillHeight: true }
}
