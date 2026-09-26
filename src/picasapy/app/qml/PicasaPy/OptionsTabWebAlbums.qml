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
        PicasaComboBox {
            objectName: "optionsWebUploadSizeCombo"
            model: ["800px", "1024px", "1600px", qsTr("Original size")]
        }
    }
    CheckBox {
        objectName: "optionsWebStripedUploadCheck"
        text: qsTr("When syncing large files, upload previews first")
        // #3572: a hivatalos magyar felirat hosszabb az ablak legkisebb
        // szélességénél — tördelődik, nem tolja ki a fület
        Layout.fillWidth: true
        Layout.preferredWidth: 0
        contentItem: Text {
            leftPadding: parent.indicator.width + parent.spacing
            text: parent.text
            font: parent.font
            color: parent.palette.windowText
            wrapMode: Text.WordWrap
            verticalAlignment: Text.AlignVCenter
        }
    }
    CheckBox {
        objectName: "optionsWebKeepJpegQualityCheck"
        text: qsTr("Preserve original image quality (uses more storage)")
        // #3572: a hivatalos magyar felirat hosszabb az ablak legkisebb
        // szélességénél — tördelődik, nem tolja ki a fület
        Layout.fillWidth: true
        Layout.preferredWidth: 0
        contentItem: Text {
            leftPadding: parent.indicator.width + parent.spacing
            text: parent.text
            font: parent.font
            color: parent.palette.windowText
            wrapMode: Text.WordWrap
            verticalAlignment: Text.AlignVCenter
        }
    }
    CheckBox { objectName: "optionsWebStarredOnlyCheck"; text: qsTr("Sync starred photos only") }
    // ld. a fájl fejlécében: ez a "confirmsync" globális döntés-kulcsot
    // némítaná el, NEM egy saját webalbum-beállítás
    CheckBox {
        objectName: "optionsWebConfirmSyncDisableCheck"
        text: qsTr("Don't confirm every sync (use the above settings)")
        // #3572: a hivatalos magyar felirat szélesebb az ablaknál — a
        // fül szélességét nem tolhatja ki (az a többi fül gombjait is
        // kilógatná), ezért tördelődik
        Layout.fillWidth: true
        Layout.preferredWidth: 0
        contentItem: Text {
            leftPadding: parent.indicator.width + parent.spacing
            text: parent.text
            font: parent.font
            color: parent.palette.windowText
            wrapMode: Text.WordWrap
            verticalAlignment: Text.AlignVCenter
        }
    }
    // #3572: az eredetiben csoportcímke („Name Tags:") + jelölőnégyzet
    // (`options/enablefruploads`), nem egyetlen összevont jelölő
    RowLayout {
        spacing: 8
        Text { text: qsTr("Name Tags:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        CheckBox { objectName: "optionsWebUploadNameTagsCheck"; text: qsTr("Include with photo uploads") }
    }
    CheckBox { objectName: "optionsWebWatermarkCheck"; text: qsTr("Add a watermark for all photo uploads:") }
    TextField { objectName: "optionsWebWatermarkTextField"; Layout.fillWidth: true 
        // #422: jobbklikk-menü (Picasa `Address`)
        TextFieldContextArea {}
    }

    Item { Layout.fillHeight: true }
}
