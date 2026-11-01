import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// #350: a Beállítások-dialógus "General" ("Általános") füle — az
// `options.fen` widget-fája szerint (docs/specs/picasa-fen-dialogs.md
// 3.11. szak.). A működő beállítások az OK-ig piszkozatban maradnak:
//
//   - Nyelv (`language`) — a #333-as nyelvválasztás (controller.language/
//     setLanguage/availableLanguages), eddig csak az Eszközök menüből
//     érhető el; itt a FEN "nyelv popup"-jának felel meg.
//   - "Törlés a lemezről megerősítés nélkül" — a #367-es ConfirmDialog
//     "delete" döntés-kulcsának elnyomás-állapota (confirmSettings
//     context property), ugyanaz a tár, mint a FileOpsDialogs törlés-
//     megerősítésénél.
//
//   - "Másodpéldányok észlelése importáláskor", a #2893 óta működő
//     `import/autoexclude` kulcs, amit az importáló párbeszéd
//     "Exclude Duplicates" jelölője is használ (importSourceController).
//
//   - "Clear cache files" - a `disposepreviews` beállítás megfelelője;
//     bekapcsolva a bélyegkép-cache az alkalmazás kilépésekor ürül.
//
//   - Felületi átmenetek és buboréksúgók — a #4449 óta QSettings-ben
//     tárolt kapcsolók.
//
//   - Alapértelmezett importcélmappa — a #4450 óta mentett beállítás, az
//     importáló párbeszéd ezt ajánlja fel.
//
// Az egykattintásos kilépés a #4458-ban azonosított videó-előnézet
// kattintására hat; az állóképes dupla kattintás változatlan.
// A #6340 óta a frissítés-ellenőrzés külön, PicasaPy saját funkciója; az
// eredeti Google-statisztika és a kamera-esemény itt továbbra is tiltott.
ColumnLayout {
    id: root
    spacing: 0
    property var optionsDraft: null

    function setting(key, fallback) {
        return root.optionsDraft
            ? root.optionsDraft.value(key, fallback) : fallback
    }

    function stage(key, value, writer) {
        if (root.optionsDraft)
            root.optionsDraft.stage(key, value, writer)
        else
            writer(value)
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
            wrapMode: Text.WordWrap
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
                     ? root.setting("general.transitions", controller.uiTransitionsEnabled)
                     : true
            onToggled: {
                if (typeof controller !== "undefined" && controller
                        && controller.setUITransitionsEnabled !== undefined)
                    root.stage("general.transitions", checked,
                        function(value) { controller.setUITransitionsEnabled(value) })
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
                     ? root.setting("general.tooltips", controller.showTooltipsEnabled)
                     : true
            onToggled: {
                if (typeof controller !== "undefined" && controller
                        && controller.setShowTooltipsEnabled !== undefined)
                    root.stage("general.tooltips", checked,
                        function(value) { controller.setShowTooltipsEnabled(value) })
            }
        }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 0
        Item { Layout.minimumWidth: 176; Layout.preferredWidth: 176 }
        CompactCheckBox {
            objectName: "optionsSingleClickExitCheck"
            text: qsTr("Single-click to exit Edit View")
            Layout.fillWidth: true
            enabled: typeof controller !== "undefined" && controller !== null
                     && controller.singleClickExitEnabled !== undefined
                     && controller.setSingleClickExitEnabled !== undefined
            checked: typeof controller !== "undefined" && controller !== null
                     && controller.singleClickExitEnabled !== undefined
                     ? root.setting("general.singleClickExit", controller.singleClickExitEnabled)
                     : false
            onToggled: {
                if (typeof controller !== "undefined" && controller
                        && controller.setSingleClickExitEnabled !== undefined)
                    root.stage("general.singleClickExit", checked,
                        function(value) { controller.setSingleClickExitEnabled(value) })
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

        // Működő (#2893): az importáláskori másodpéldány-észlelés. UGYANAZT az
        // `import/autoexclude` kulcsot írja, amit az importáló párbeszéd
        // „Exclude Duplicates" jelölője (`importSourceController`,
        // `AUTOEXCLUDE_SETTINGS_KEY`) - két külön állapot tilos: amit itt
        // beállítasz, azt ott is látod, és viszont.
        //
        // Eddig szürke helyfoglaló volt, azzal az indoklással, hogy „nincs
        // automatikus duplikátum-észlelés importáláskor". Ez a #1398 óta
        // nem igaz: a forrás-beolvasás megjelöli a másodpéldányokat, és
        // eszerint hagyja ki őket a válogatásból.
        //
        // #5473: a felirat a binárisból igazolt angol forrás
        // (`options/autoexclude.title`), az alapértéke pedig bekapcsolt (1).
        CompactCheckBox {
            objectName: "optionsAutoExcludeCheck"
            text: qsTr("Detect duplicates while importing")
            Layout.fillWidth: true
            //: A jelölő CSAK akkor él, ha van kihez kötni: vezérlő nélkül
            //: (próbákban, leépítés közben) a pipa semmit nem tárolna el —
            //: a hazug „élő" állapot rosszabb, mint a szürke vezérlő.
            enabled: typeof importSourceController !== "undefined"
                     && importSourceController !== null
            checked: (typeof importSourceController !== "undefined"
                      && importSourceController
                      && importSourceController.autoExclude !== undefined)
                         ? root.setting("general.autoExclude", importSourceController.autoExclude)
                         : false
            onToggled: {
                if (typeof importSourceController !== "undefined"
                    && importSourceController)
                    root.stage("general.autoExclude", checked,
                        function(value) { importSourceController.setAutoExclude(value) })
            }
        }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 0
        Item { Layout.minimumWidth: 176; Layout.preferredWidth: 176 }
        CompactCheckBox {
            objectName: "optionsClearCacheFilesCheck"
            text: qsTr("Clear cache files")
            Layout.fillWidth: true
            enabled: typeof controller !== "undefined" && controller !== null
                     && controller.disposePreviewsOnExit !== undefined
                     && controller.setDisposePreviewsOnExit !== undefined
            checked: typeof controller !== "undefined" && controller !== null
                     && controller.disposePreviewsOnExit !== undefined
                         ? root.setting("general.disposePreviewsOnExit",
                             controller.disposePreviewsOnExit) : false
            onToggled: {
                if (typeof controller !== "undefined" && controller
                    && controller.setDisposePreviewsOnExit !== undefined)
                    root.stage("general.disposePreviewsOnExit", checked,
                        function(value) { controller.setDisposePreviewsOnExit(value) })
            }
        }
    }

    // A törlés-megerősítés elnyomása, ugyanaz a confirmSettings
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
                     ? root.setting("general.skipDeleteConfirm",
                         confirmSettings.isSuppressed("delete")) : false
            onToggled: {
                if (typeof confirmSettings !== "undefined" && confirmSettings)
                    root.stage("general.skipDeleteConfirm", checked,
                        function(value) { confirmSettings.setSuppressed("delete", value) })
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
                     ? root.setting("general.skipRemoveConfirm",
                         confirmSettings.isSuppressed("removeFromAlbum")) : false
            onToggled: {
                if (typeof confirmSettings !== "undefined" && confirmSettings)
                    root.stage("general.skipRemoveConfirm", checked,
                        function(value) { confirmSettings.setSuppressed("removeFromAlbum", value) })
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
        // #3572: a normál szélességen megmarad a 414 px-es igazítás, de
        // keskeny ablakban a 176 px-es bal margó mellett összehúzódhat.
        Layout.minimumWidth: 0
        Layout.maximumWidth: 414
        Layout.fillWidth: true
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

    // ---- Frissítés-ellenőrzés (#6340) -------------------------------------
    // Az előző helyfoglaló sor objektumneve megmarad, hogy a régi QML-határ
    // fogyasztói továbbra is megtalálják a sor dobozát.
    RowLayout {
        objectName: "optionsUpdateModeCombo"
        Layout.fillWidth: true
        Layout.topMargin: 6
        Layout.preferredHeight: 32
        spacing: 0
        Item { Layout.minimumWidth: 176; Layout.preferredWidth: 176 }
        CompactCheckBox {
            objectName: "optionsAutomaticUpdatesCheck"
            Layout.fillWidth: true
            text: qsTr("Check for updates automatically")
            enabled: typeof updateController !== "undefined" && updateController !== null
            checked: (typeof updateController !== "undefined" && updateController
                && updateController.autoCheckEnabled !== undefined)
                ? root.setting("updates/autoCheck", updateController.autoCheckEnabled) : true
            onToggled: {
                if (typeof updateController !== "undefined" && updateController)
                    root.stage("updates/autoCheck", checked,
                        function(value) { updateController.setAutoCheckEnabled(value) })
            }
        }
    }
    Text {
        objectName: "optionsAutomaticUpdatesDescription"
        text: qsTr("PicasaPy checks GitHub for new versions.")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
        wrapMode: Text.WordWrap
        Layout.leftMargin: 176
        Layout.fillWidth: true
        Layout.preferredHeight: 14
    }

    // Nyelvválasztás, a specben az automatikus frissítés után áll, és
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
            Layout.minimumWidth: 96
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
                var idx = codes.indexOf(root.setting("general.language",
                    controller ? controller.pendingLanguage : "en"))
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
                if (code === root.setting("general.language",
                        controller.pendingLanguage)) return
                languageConfirm.candidateCode = code
                languageConfirm.ask("", qsTr("Change the language PicasaPy uses?\n\nIt will change the next time PicasaPy is opened."))
            }
        }
    }
    ConfirmDialog {
        id: languageConfirm
        namePrefix: "optionsLanguageConfirm"
        property string candidateCode: ""
        onConfirmed: {
            if (controller) {
                root.stage("general.language", candidateCode,
                    function(value) { controller.setLanguage(value) })
                languageCombo.syncToPending()
            }
        }
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
            text: qsTr("Save imported pictures in:")
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
            Layout.minimumWidth: 80
            Layout.preferredHeight: 32
            Layout.rightMargin: 8
            readOnly: true
            text: importDestRow.enabled
                  ? root.setting("general.importDestination",
                      importSourceController.defaultDestination) : ""
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
            root.stage("general.importDestination",
                fileOpsController.toLocalPath(selectedFolder.toString()),
                function(value) {
                    importSourceController.setDefaultDestination(value)
                })
    }

    component CompactCheckBox: CheckBox {
        Layout.minimumHeight: 24
        Layout.preferredHeight: 24
        Layout.maximumHeight: 24
        topPadding: 0
        bottomPadding: 0
    }

}
