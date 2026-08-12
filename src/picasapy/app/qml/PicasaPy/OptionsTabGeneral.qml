import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350: a Beállítások-dialógus "General" ("Általános") füle — az
// `options.fen` widget-fája szerint (docs/specs/picasa-fen-dialogs.md
// 3.11. szak.). Ez az egyetlen fül, amelyen TÉNYLEGESEN élő, a PicasaPy-ban
// már működő beállítás ül:
//
//   - Nyelv (`language`) — a #333-as nyelvválasztás (controller.language/
//     setLanguage/availableLanguages), eddig csak az Eszközök menüből
//     érhető el; itt a FEN "nyelv popup"-jának felel meg.
//   - "Törlés a lemezről megerősítés nélkül" — a #367-es ConfirmDialog
//     "delete" döntés-kulcsának elnyomás-állapota (confirmSettings
//     context property), ugyanaz a tár, mint a FileOpsDialogs törlés-
//     megerősítésénél.
//
// A többi FEN-vezérlőnek MA nincs PicasaPy-beli funkciója (nincs
// tooltip-kapcsoló, nincs "egy kattintásra kilépés szerkesztőből"-mód,
// nincs automatikus duplikátum-észlelés importáláskor, nincs
// gyorsítótár-törlés funkció, nincs statisztika-küldés/frissítés-
// ellenőrzés, nincs kamera-esemény, nincs perzisztens alapértelmezett
// importcélmappa) — ezek a struktúra kedvéért megjelennek, de
// `enabled: false`, a hiányzó funkció megnevezésével kommentben.
ColumnLayout {
    id: root
    spacing: 14

    // ---- Kezelőfelület (labelgroup4) ------------------------------------
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        Text {
            text: qsTr("User interface:")
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.ink
        }

        // nincs élő "speciális effektek" kapcsoló a PicasaPy UI-ban
        CheckBox {
            objectName: "optionsUiTransitionsCheck"
            text: qsTr("Use special effects")
            enabled: false
        }
        // nincs tooltip be/ki kapcsoló — a segédjelölések mindig megjelennek
        CheckBox {
            objectName: "optionsShowTooltipsCheck"
            text: qsTr("Show tooltips")
            enabled: false
        }
        // nincs "egy kattintásra kilépés szerkesztőből" mód
        CheckBox {
            objectName: "optionsSingleClickExitCheck"
            text: qsTr("Single click to exit the editing view")
            enabled: false
        }

        // ÉLŐ: nyelvválasztás — ugyanaz a controller.language, amit az
        // Eszközök → Nyelv menü is vezérel (#333)
        RowLayout {
            spacing: 8
            Text {
                text: qsTr("Language:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            ComboBox {
                id: languageCombo
                objectName: "optionsLanguageCombo"
                // a megjelenő lista a nyelvkódok emberi neve — a controller
                // csak kódokat ismer (en/hu), a leképezés itt él
                readonly property var codes:
                    controller ? controller.availableLanguages : ["en"]
                model: languageCombo.codes.map(function (code) {
                    return code === "hu" ? qsTr("Hungarian") : qsTr("English")
                })
                currentIndex: {
                    var idx = languageCombo.codes.indexOf(
                        controller ? controller.language : "en")
                    return idx >= 0 ? idx : 0
                }
                onActivated: function (index) {
                    if (controller) controller.setLanguage(languageCombo.codes[index])
                }
            }
        }
    }

    // ---- Fájlok (labelgroup10) ------------------------------------------
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        Text {
            text: qsTr("Files:")
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.ink
        }

        // nincs automatikus duplikátum-észlelés importáláskor — a
        // duplikátum-keresés a PicasaPy-ban egy külön, kézzel indított
        // eszköz (Eszközök → Duplikátumok keresése, DedupDialog.qml)
        CheckBox {
            objectName: "optionsAutoExcludeCheck"
            text: qsTr("Detect duplicates on import")
            enabled: false
        }
        // nincs "gyorsítótár törlése" művelet — a bélyegkép-gyorsítótár
        // mérete a #144-es LRU-takarítóval automatikusan karban tartott,
        // kézi ürítés ma nincs bekötve
        Button {
            objectName: "optionsClearCacheButton"
            text: qsTr("Clear Cache...")
            enabled: false
        }

        // ÉLŐ: a törlés-megerősítés elnyomása — ugyanaz a confirmSettings
        // "delete" kulcs, amit a FileOpsDialogs ConfirmDialog-ja ír (#367)
        CheckBox {
            id: skipDeleteConfirmCheck
            objectName: "optionsSkipDeleteConfirmCheck"
            text: qsTr("Delete from disk without confirmation")
            checked: typeof confirmSettings !== "undefined" && confirmSettings
                     ? confirmSettings.isSuppressed("delete") : false
            onToggled: {
                if (typeof confirmSettings !== "undefined" && confirmSettings)
                    confirmSettings.setSuppressed("delete", checked)
            }
        }
        // nincs megerősítő dialógus az albumból eltávolításnál (a
        // PhotoContextMenu "Remove from Album" azonnal végrehajt) — ha ez
        // változik, ide egy hasonló, "removeFromAlbum" kulcsú checkbox jön
        CheckBox {
            objectName: "optionsSkipRemoveConfirmCheck"
            text: qsTr("Remove from album without confirmation")
            enabled: false
        }
    }

    // ---- Részvétel a fejlesztésben (labelgroup16) ------------------------
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        Text {
            text: qsTr("Help improve PicasaPy:")
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.ink
        }
        // nincs semmilyen használati-statisztika/telemetria a PicasaPy-ban
        CheckBox {
            objectName: "optionsUsageStatsCheck"
            text: qsTr("Send anonymous usage statistics")
            enabled: false
        }
    }

    // ---- Automatikus frissítés (csak Win az eredetiben) -------------------
    // nincs beépített frissítés-ellenőrző a PicasaPy-ban (csomagkezelőn/
    // git-en át frissül) — a három rádiógomb csak a FEN-struktúra kedvéért
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4
        enabled: false

        Text {
            text: qsTr("Automatic updates:")
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.ink
        }
        ButtonGroup { id: updateGroup }
        RadioButton {
            objectName: "optionsUpdateAutoRadio"
            text: qsTr("Update automatically")
            ButtonGroup.group: updateGroup
        }
        RadioButton {
            objectName: "optionsUpdatePromptRadio"
            text: qsTr("Prompt before downloading updates")
            ButtonGroup.group: updateGroup
            checked: true
        }
        RadioButton {
            objectName: "optionsUpdateNeverRadio"
            text: qsTr("Never check for updates")
            ButtonGroup.group: updateGroup
        }
    }

    // ---- Importált képek célmappája ---------------------------------------
    // nincs perzisztens alapértelmezett importcélmappa — a PicasaPy-ban a
    // felhasználó importálásonként választ célmappát (ImportSourceDialog)
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        enabled: false

        Text {
            text: qsTr("Import destination folder:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        TextField {
            objectName: "optionsImportDestField"
            Layout.fillWidth: true
            readOnly: true
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
        }
        Button {
            objectName: "optionsImportDestBrowseButton"
            text: qsTr("Browse...")
        }
    }

    Item { Layout.fillHeight: true }
}
