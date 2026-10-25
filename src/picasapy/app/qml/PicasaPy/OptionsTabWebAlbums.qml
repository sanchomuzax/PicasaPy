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
    objectName: "optionsWebAlbumsTab"
    spacing: 10
    enabled: false

    readonly property var prefs: (typeof controller !== "undefined" && controller)
        ? controller : null

    RowLayout {
        spacing: 8
        Text { text: qsTr("Default upload size:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        // #5482: az eredeti sablon öt tétele, a sablon sorrendjében (a
        // `CGeneralPrefsPage` sztringjei). A hosszú tételek csonkolódnak, de
        // nem szélesítik a fület; a kiválasztott méretet a controller tárolja,
        // a hiányzó kulcsnál az 1600 (2. index) van kiválasztva.
        PicasaComboBox {
            objectName: "optionsWebUploadSizeCombo"
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            model: [qsTr("Original size (slowest upload)"),
                    qsTr("Best for web sharing (2048px)"),
                    qsTr("Recommended: 1600 pixels (for prints, screensavers, and sharing)"),
                    qsTr("Medium: 1024 pixels (for sharing)"),
                    qsTr("Small: 800 pixels (for blogs and webpages)")]
            currentIndex: root.prefs && root.prefs.webUploadSizeIndex !== undefined
                ? root.prefs.webUploadSizeIndex : 2
            onActivated: if (root.prefs
                    && typeof root.prefs.setWebUploadSizeIndex === "function")
                root.prefs.setWebUploadSizeIndex(currentIndex)
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
    RowLayout {
        spacing: 8
        Text {
            objectName: "optionsWebJpegQualityLabel"
            text: qsTr("JPEG Quality:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        CheckBox {
            objectName: "optionsWebKeepJpegQualityCheck"
            text: qsTr("Preserve original image quality (uses more storage)")
            // #3572: a hivatalos magyar felirat hosszabb az ablak legkisebb
            // szélességénél - tördelődik, nem tolja ki a fület
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
    }
    RowLayout {
        spacing: 8
        Text {
            objectName: "optionsWebSyncingLabel"
            text: qsTr("Syncing:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            Layout.alignment: Qt.AlignTop
        }
        ColumnLayout {
            spacing: 3
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            CheckBox {
                objectName: "optionsWebStarredOnlyCheck"
                text: qsTr("Sync starred photos only")
            }
            // ld. a fájl fejlécében: ez a "confirmsync" globális döntés-kulcsot
            // némítaná el, NEM egy saját webalbum-beállítás.
            CheckBox {
                objectName: "optionsWebConfirmSyncDisableCheck"
                text: qsTr("Don't confirm every sync (use the above settings)")
                // #3572: a hivatalos magyar felirat szélesebb az ablaknál - a
                // fül szélességét nem tolhatja ki, ezért tördelődik.
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
        }
    }
    // #3572: az eredetiben csoportcímke („Name Tags:") + jelölőnégyzet
    // (`options/enablefruploads`), nem egyetlen összevont jelölő
    RowLayout {
        spacing: 8
        Text { text: qsTr("Name Tags:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        CheckBox { objectName: "optionsWebUploadNameTagsCheck"; text: qsTr("Include with photo uploads") }
    }
    RowLayout {
        spacing: 8
        Text {
            objectName: "optionsWebWatermarksLabel"
            text: qsTr("Watermarks:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            Layout.alignment: Qt.AlignTop
        }
        ColumnLayout {
            spacing: 3
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            CheckBox {
                objectName: "optionsWebWatermarkCheck"
                text: qsTr("Add a watermark for all photo uploads:")
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
            TextField {
                objectName: "optionsWebWatermarkTextField"
                Layout.fillWidth: true
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
            Text {
                objectName: "optionsWebWatermarkHelp"
                text: qsTr("Stamp photos with your name, a web domain, or a copyright notice.")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }
    }

    Item { Layout.fillHeight: true }
}
