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
    spacing: 0

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
    RowLayout {
        Layout.fillWidth: true
        Layout.topMargin: 6
        spacing: 0

        Text {
            objectName: "optionsGeneralUiHeading"
            text: qsTr("User interface:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            Layout.minimumWidth: 176
            Layout.preferredWidth: 176
            Layout.maximumWidth: 176
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
        }

        CompactCheckBox {
            objectName: "optionsUiTransitionsCheck"
            text: qsTr("Use special effects")
            Layout.fillWidth: true
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
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 0
        Item { Layout.minimumWidth: 176; Layout.preferredWidth: 176 }
        CompactCheckBox {
            objectName: "optionsShowTooltipsCheck"
            text: qsTr("Show tooltips")
            Layout.fillWidth: true
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
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 0
        Item { Layout.minimumWidth: 176; Layout.preferredWidth: 176 }
        CompactCheckBox {
            objectName: "optionsSingleClickExitCheck"
            text: qsTr("Single click to exit the editing view")
            Layout.fillWidth: true
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
    RowLayout {
        Layout.fillWidth: true
        Layout.topMargin: 2
        spacing: 0

        Text {
            objectName: "optionsGeneralFilesHeading"
            text: qsTr("Files:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            Layout.minimumWidth: 176
            Layout.preferredWidth: 176
            Layout.maximumWidth: 176
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
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
            Layout.fillWidth: true
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
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        Item { Layout.minimumWidth: 176; Layout.preferredWidth: 176 }
        Button {
            objectName: "optionsClearCacheButton"
            text: qsTr("Clear Cache...")
            Layout.preferredHeight: 24
            Layout.minimumHeight: 24
            padding: 0
            onClicked: clearCacheConfirm.ask(
                "", qsTr("Empty the thumbnail cache? The thumbnails are "
                         + "rebuilt when needed — no picture is lost."))
        }
        Text {
            id: clearCacheResult
            objectName: "optionsClearCacheResult"
            visible: text !== ""
            Layout.fillWidth: true
            color: Theme.ink
            font.pixelSize: Theme.fontSize
            verticalAlignment: Text.AlignVCenter
        }
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

    // ÉLŐ: a törlés-megerősítés elnyomása — ugyanaz a confirmSettings
    // "delete" kulcs, amit a FileOpsDialogs ConfirmDialog-ja ír (#367)
    RowLayout {
        Layout.fillWidth: true
        spacing: 0
        Item { Layout.minimumWidth: 176; Layout.preferredWidth: 176 }
        CompactCheckBox {
            id: skipDeleteConfirmCheck
            objectName: "optionsSkipDeleteConfirmCheck"
            text: qsTr("Delete from disk without confirmation")
            Layout.fillWidth: true
            checked: typeof confirmSettings !== "undefined" && confirmSettings
                     ? confirmSettings.isSuppressed("delete") : false
            onToggled: {
                if (typeof confirmSettings !== "undefined" && confirmSettings)
                    confirmSettings.setSuppressed("delete", checked)
            }
        }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 0
        Item { Layout.minimumWidth: 176; Layout.preferredWidth: 176 }
        // #3539: az albumból eltávolítás is megerősítést kér — ugyanaz a
        // confirmSettings "removeFromAlbum" kulcs, amit a Main.qml
        // removeFromAlbumDialog ConfirmDialog-ja ír (#367 mintája)
        CompactCheckBox {
            objectName: "optionsSkipRemoveConfirmCheck"
            text: qsTr("Remove from album without confirmation")
            Layout.fillWidth: true
            checked: typeof confirmSettings !== "undefined" && confirmSettings
                     ? confirmSettings.isSuppressed("removeFromAlbum") : false
            onToggled: {
                if (typeof confirmSettings !== "undefined" && confirmSettings)
                    confirmSettings.setSuppressed("removeFromAlbum", checked)
            }
        }
    }

    Rectangle {
        objectName: "optionsGeneralFilesDivider"
        Layout.fillWidth: true
        Layout.topMargin: 1
        Layout.preferredHeight: 1
        color: Theme.chromeBorder
    }

    // ---- Részvétel a fejlesztésben (labelgroup16) ------------------------
    RowLayout {
        Layout.fillWidth: true
        Layout.topMargin: 7
        spacing: 0

        Text {
            objectName: "optionsGeneralParticipationHeading"
            text: qsTr("Help improve PicasaPy:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            // A lefordított cím a szokásos címkefülke szélességénél hosszabb
            // lehet. A szöveg saját szélességet kap, hogy ne vágódjon le.
            Layout.minimumWidth: Math.max(176, implicitWidth)
            Layout.preferredWidth: Math.max(176, implicitWidth)
            Layout.maximumWidth: Math.max(176, implicitWidth)
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
        }
        // nincs semmilyen használati-statisztika/telemetria a PicasaPy-ban
        CompactCheckBox {
            objectName: "optionsUsageStatsCheck"
            text: qsTr("Send anonymous usage statistics")
            enabled: false
            Layout.fillWidth: true
            // #3661: a hivatalos magyar felirat („Névtelen használati
            // statisztikák küldése a Google részére") 455 px-es implicit
            // szélessége a legkisebb ablakon (456 px) 1 px-es tartalékkal
            // fért csak el — a #3572 mintája szerint tördelődik, hogy ne
            // legyen betűkészlet-függő élen egyensúlyozó méret.
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
    Button {
        id: privacyLink
        objectName: "optionsPrivacyLink"
        text: qsTr("Privacy...")
        flat: true
        padding: 0
        Layout.leftMargin: 176
        Layout.topMargin: 3
        Layout.preferredWidth: 414
        Layout.minimumWidth: 414
        Layout.maximumWidth: 414
        Layout.preferredHeight: 24
        Layout.minimumHeight: 24
        Accessible.role: Accessible.Link
        contentItem: Text {
            text: privacyLink.text
            font.pixelSize: Theme.fontSize
            color: Theme.linkBlue
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            font.underline: true
        }
        onClicked: Qt.openUrlExternally("https://policies.google.com/privacy")
    }
    Rectangle {
        objectName: "optionsGeneralParticipationDivider"
        Layout.fillWidth: true
        Layout.topMargin: 1
        Layout.preferredHeight: 1
        color: Theme.chromeBorder
    }

    // ---- Automatikus frissítés (csak Win az eredetiben) -------------------
    // nincs beépített frissítés-ellenőrző a PicasaPy-ban (csomagkezelőn/
    // git-en át frissül) — a lista a FEN-struktúra kedvéért jelenik meg
    RowLayout {
        Layout.fillWidth: true
        Layout.topMargin: 6
        Layout.preferredHeight: 32
        spacing: 0
        enabled: false

        Text {
            text: qsTr("Automatic updates:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            Layout.minimumWidth: 176
            Layout.preferredWidth: 176
            Layout.maximumWidth: 176
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
        }
        PicasaComboBox {
            objectName: "optionsUpdateModeCombo"
            Layout.fillWidth: true
            Layout.preferredHeight: 32
            model: [
                qsTr("Update automatically"),
                qsTr("Prompt before downloading updates"),
                qsTr("Never check for updates")
            ]
            currentIndex: 0
        }
    }

    // ÉLŐ: nyelvválasztás — a specben az automatikus frissítés után áll, és
    // ugyanazt a pendingLanguage értéket használja, mint az Eszközök → Nyelv
    // menü (#333). A választás megerősítése miatt csak az újraindításkor él.
    RowLayout {
        Layout.fillWidth: true
        Layout.preferredHeight: 32
        spacing: 0
        Text {
            text: qsTr("Language:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            Layout.minimumWidth: 176
            Layout.preferredWidth: 176
            Layout.maximumWidth: 176
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
        }
        PicasaComboBox {
            id: languageCombo
            objectName: "optionsLanguageCombo"
            Layout.fillWidth: true
            Layout.preferredHeight: 32
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
        Layout.preferredHeight: 32
        spacing: 0
        enabled: typeof importSourceController !== "undefined"
                 && importSourceController !== null
                 && importSourceController.defaultDestination !== undefined
                 && typeof importSourceController.setDefaultDestination === "function"

        Text {
            objectName: "optionsImportDestinationLabel"
            text: qsTr("Import destination folder:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            Layout.minimumWidth: 176
            Layout.preferredWidth: 176
            Layout.maximumWidth: 176
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
        }
        TextField {
            objectName: "optionsImportDestField"
            Layout.fillWidth: true
            Layout.preferredHeight: 32
            Layout.rightMargin: 8
            readOnly: true
            text: importDestRow.enabled
                  ? importSourceController.defaultDestination : ""
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
        }
        Button {
            objectName: "optionsImportDestBrowseButton"
            text: qsTr("Browse...")
            Layout.preferredWidth: 92
            Layout.minimumWidth: 92
            Layout.preferredHeight: 32
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
        Layout.maximumHeight: 24
        topPadding: 0
        bottomPadding: 0
    }

}
