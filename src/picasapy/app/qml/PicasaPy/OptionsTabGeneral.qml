import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
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
//   - "Másodpéldányok észlelése importáláskor" — a #2893 óta ÉLŐ: ugyanaz
//     az `import/autoexclude` kulcs, amit az importáló párbeszéd
//     "Exclude Duplicates" jelölője ír (importSourceController).
//
//   - "Gyorsítótár ürítése…" — a #598 óta ÉLŐ: az eredeti `disposepreviews`
//     kapcsolójának megfelelője, a bélyegkép-tár lemezes ürítése
//     (controller.clearThumbnailCache).
//
//   - Felületi átmenetek és buboréksúgók — a #4449 óta QSettings-ben
//     tárolt, futás közben is ható kapcsolók.
//
//   - Alapértelmezett importcélmappa — a #4450 óta mentett beállítás, az
//     importáló párbeszéd ezt ajánlja fel.
//
// Az egykattintásos kilépés a #4458-ban azonosított videó-előnézet
// kattintására hat; az állóképes dupla kattintás változatlan.
// A többi FEN-vezérlőnek sincs még PicasaPy-beli funkciója (statisztika-
// küldés/frissítés-ellenőrzés, kamera-esemény); ezek tiltottak maradnak.
ColumnLayout {
    id: root
    spacing: 2

    //: #598: a felszabadult hely emberi alakja. Kilobájt alatt bájtban —
    //: egy „0,0 MB" eredmény azt sugallná, hogy nem történt semmi.
    function emberiMeret(bajt) {
        if (bajt < 1024)
            return qsTr("%1 bytes").arg(bajt)
        if (bajt < 1024 * 1024)
            return qsTr("%1 kB").arg(Number(bajt / 1024).toLocaleString(
                Qt.locale(), "f", 1))
        return qsTr("%1 MB").arg(Number(bajt / (1024 * 1024)).toLocaleString(
            Qt.locale(), "f", 1))
    }

    // ---- Kezelőfelület (labelgroup4) ------------------------------------
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 2

        Text {
            text: qsTr("User interface:")
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.ink
        }

        CompactCheckBox {
            objectName: "optionsUiTransitionsCheck"
            text: qsTr("Use special effects")
            enabled: typeof controller !== "undefined" && controller !== null
                     && controller.uiTransitionsEnabled !== undefined
                     && controller.setUITransitionsEnabled !== undefined
            checked: typeof controller !== "undefined" && controller !== null
                     && controller.uiTransitionsEnabled !== undefined
                     ? controller.uiTransitionsEnabled : true
            onToggled: {
                if (typeof controller !== "undefined" && controller
                        && controller.setUITransitionsEnabled !== undefined)
                    controller.setUITransitionsEnabled(checked)
            }
        }
        CompactCheckBox {
            objectName: "optionsShowTooltipsCheck"
            text: qsTr("Show tooltips")
            enabled: typeof controller !== "undefined" && controller !== null
                     && controller.showTooltipsEnabled !== undefined
                     && controller.setShowTooltipsEnabled !== undefined
            checked: typeof controller !== "undefined" && controller !== null
                     && controller.showTooltipsEnabled !== undefined
                     ? controller.showTooltipsEnabled : true
            onToggled: {
                if (typeof controller !== "undefined" && controller
                        && controller.setShowTooltipsEnabled !== undefined)
                    controller.setShowTooltipsEnabled(checked)
            }
        }
        CompactCheckBox {
            objectName: "optionsSingleClickExitCheck"
            text: qsTr("Single click to exit the editing view")
            enabled: typeof controller !== "undefined" && controller !== null
                     && controller.singleClickExitEnabled !== undefined
                     && controller.setSingleClickExitEnabled !== undefined
            checked: typeof controller !== "undefined" && controller !== null
                     && controller.singleClickExitEnabled !== undefined
                     ? controller.singleClickExitEnabled : false
            onToggled: {
                if (typeof controller !== "undefined" && controller
                        && controller.setSingleClickExitEnabled !== undefined)
                    controller.setSingleClickExitEnabled(checked)
            }
        }
    }

    // ---- Fájlok (labelgroup10) ------------------------------------------
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 2

        Text {
            text: qsTr("Files:")
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.ink
        }

        // ÉLŐ (#2893): az importáláskori másodpéldány-észlelés. UGYANAZT az
        // `import/autoexclude` kulcsot írja, amit az importáló párbeszéd
        // „Exclude Duplicates" jelölője (`importSourceController`,
        // `AUTOEXCLUDE_SETTINGS_KEY`) — két külön állapot tilos: amit itt
        // beállítasz, azt ott is látod, és viszont.
        //
        // Eddig szürke helyfoglaló volt, azzal az indoklással, hogy „nincs
        // automatikus duplikátum-észlelés importáláskor". Ez a #1398 óta
        // nem igaz: a forrás-beolvasás megjelöli a másodpéldányokat, és
        // eszerint hagyja ki őket a válogatásból.
        //
        // ⚠️ A felirat: a `picasa-menu-parancsok-viselkedes.md` az
        // `options.fen`-ből „Detect duplicates **while importing**" alakot
        // idéz, nálunk „on import" áll. A kettő ugyanazt jelenti, és a fen
        // teljes szövegkiírása nincs a lapon — a feliratot ezért NEM
        // írjuk át egyetlen idézet alapján.
        CompactCheckBox {
            objectName: "optionsAutoExcludeCheck"
            text: qsTr("Detect duplicates on import")
            //: A jelölő CSAK akkor él, ha van kihez kötni: vezérlő nélkül
            //: (próbákban, leépítés közben) a pipa semmit nem tárolna el —
            //: a hazug „élő" állapot rosszabb, mint a szürke vezérlő.
            enabled: typeof importSourceController !== "undefined"
                     && importSourceController !== null
            checked: (typeof importSourceController !== "undefined"
                      && importSourceController
                      && importSourceController.autoExclude !== undefined)
                         ? importSourceController.autoExclude : false
            onToggled: {
                if (typeof importSourceController !== "undefined"
                    && importSourceController)
                    importSourceController.setAutoExclude(checked)
            }
        }
        //: #598: az eredeti `disposepreviews` kapcsolójának megfelelője. A
        //: #144-es LRU-takarító a MÉRETET tartja karban; ez a gomb a
        //: felhasználó döntése, ha most akar helyet visszanyerni.
        //: A hármas pont a feliratban azt ígéri, hogy kérdez — ezért
        //: megerősítést kér, és utána megmondja, mennyit szabadított fel.
        Button {
            objectName: "optionsClearCacheButton"
            text: qsTr("Clear Cache...")
            onClicked: clearCacheConfirm.ask(
                "", qsTr("Empty the thumbnail cache? The thumbnails are "
                         + "rebuilt when needed — no picture is lost."))
        }
        ConfirmDialog {
            id: clearCacheConfirm
            objectName: "optionsClearCacheConfirm"
            namePrefix: "optionsClearCache"
            yesText: qsTr("Empty")
            noText: qsTr("Keep")
            onConfirmed: {
                var bajt = (typeof controller !== "undefined" && controller)
                           ? controller.clearThumbnailCache() : 0
                clearCacheResult.text = qsTr("%1 freed.").arg(
                    root.emberiMeret(bajt))
            }
        }
        Text {
            id: clearCacheResult
            objectName: "optionsClearCacheResult"
            visible: text !== ""
            color: Theme.ink
            font.pixelSize: Theme.fontSize
        }

        // ÉLŐ: a törlés-megerősítés elnyomása — ugyanaz a confirmSettings
        // "delete" kulcs, amit a FileOpsDialogs ConfirmDialog-ja ír (#367)
        CompactCheckBox {
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
        // #3539: az albumból eltávolítás is megerősítést kér — ugyanaz a
        // confirmSettings "removeFromAlbum" kulcs, amit a Main.qml
        // removeFromAlbumDialog ConfirmDialog-ja ír (#367 mintája)
        CompactCheckBox {
            objectName: "optionsSkipRemoveConfirmCheck"
            text: qsTr("Remove from album without confirmation")
            checked: typeof confirmSettings !== "undefined" && confirmSettings
                     ? confirmSettings.isSuppressed("removeFromAlbum") : false
            onToggled: {
                if (typeof confirmSettings !== "undefined" && confirmSettings)
                    confirmSettings.setSuppressed("removeFromAlbum", checked)
            }
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
        CompactCheckBox {
            objectName: "optionsUsageStatsCheck"
            text: qsTr("Send anonymous usage statistics")
            enabled: false
            // #3661: a hivatalos magyar felirat („Névtelen használati
            // statisztikák küldése a Google részére") 455 px-es implicit
            // szélessége a legkisebb ablakon (456 px) 1 px-es tartalékkal
            // fért csak el — a #3572 mintája szerint tördelődik, hogy ne
            // legyen betűkészlet-függő élen egyensúlyozó méret.
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

    // ---- Automatikus frissítés (csak Win az eredetiben) -------------------
    // nincs beépített frissítés-ellenőrző a PicasaPy-ban (csomagkezelőn/
    // git-en át frissül) — a lista a FEN-struktúra kedvéért jelenik meg
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 2
        enabled: false

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text {
                text: qsTr("Automatic updates:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            PicasaComboBox {
                objectName: "optionsUpdateModeCombo"
                Layout.fillWidth: true
                model: [
                    qsTr("Update automatically"),
                    qsTr("Prompt before downloading updates"),
                    qsTr("Never check for updates")
                ]
                currentIndex: 0
            }
        }
    }

    // ÉLŐ: nyelvválasztás — a specben az automatikus frissítés után áll, és
    // ugyanazt a pendingLanguage értéket használja, mint az Eszközök → Nyelv
    // menü (#333). A választás megerősítése miatt csak az újraindításkor él.
    RowLayout {
        spacing: 8
        Text {
            text: qsTr("Language:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        PicasaComboBox {
            id: languageCombo
            objectName: "optionsLanguageCombo"
            readonly property var codes: [
                controller ? controller.systemLanguageCode : "system"
            ].concat(controller ? controller.availableLanguages : ["en"])
            model: languageCombo.codes.map(function (code) {
                if (controller && code === controller.systemLanguageCode)
                    return qsTr("System Default (%1)").arg(
                        controller.systemLanguageSuffix)
                return controller ? controller.ownLanguageName(code) : code
            })
            function syncToPending() {
                var idx = codes.indexOf(
                    controller ? controller.pendingLanguage : "en")
                currentIndex = idx >= 0 ? idx : 0
            }
            Component.onCompleted: syncToPending()
            Connections {
                target: controller
                function onPendingLanguageChanged() {
                    languageCombo.syncToPending()
                }
            }
            onActivated: function (index) {
                if (!controller) return
                var code = languageCombo.codes[index]
                if (code === controller.pendingLanguage) return
                languageConfirm.candidateCode = code
                languageConfirm.ask("", qsTr("Change the language Picasa uses?\n\nIt will change the next time Picasa is opened."))
            }
        }
    }
    ConfirmDialog {
        id: languageConfirm
        namePrefix: "optionsLanguageConfirm"
        property string candidateCode: ""
        onConfirmed: if (controller) controller.setLanguage(candidateCode)
        onDenied: languageCombo.syncToPending()
        onCanceled: languageCombo.syncToPending()
    }

    // ---- Importált képek célmappája ---------------------------------------
    // A QSettings-ben tárolt célmappa az import párbeszéd induló célja is.
    RowLayout {
        id: importDestRow
        Layout.fillWidth: true
        spacing: 8
        enabled: typeof importSourceController !== "undefined"
                 && importSourceController !== null
                 && importSourceController.defaultDestination !== undefined
                 && typeof importSourceController.setDefaultDestination === "function"

        Text {
            text: qsTr("Import destination folder:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        TextField {
            objectName: "optionsImportDestField"
            Layout.fillWidth: true
            readOnly: true
            text: importDestRow.enabled
                  ? importSourceController.defaultDestination : ""
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
        }
        Button {
            objectName: "optionsImportDestBrowseButton"
            text: qsTr("Browse...")
            onClicked: importDestFolderDialog.open()
        }
    }

    Item { Layout.fillHeight: true }

    FolderDialog {
        id: importDestFolderDialog
        objectName: "optionsImportDestFolderDialog"
        title: qsTr("Import destination folder:")
        currentFolder: importDestRow.enabled
            ? importSourceController.defaultDestinationUrl
            : Qt.resolvedUrl(".")
        onAccepted: if (importDestRow.enabled)
            importSourceController.setDefaultDestination(selectedFolder.toString())
    }

    component CompactCheckBox: CheckBox {
        Layout.minimumHeight: 24
        Layout.preferredHeight: 24
        topPadding: 0
        bottomPadding: 0
    }

}
