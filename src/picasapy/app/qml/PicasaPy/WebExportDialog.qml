import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Weboldal exportálása (#351, `webexport.fen`, docs/specs/
// picasa-fen-dialogs.md 3.12.): a kijelölt mappa/album exportja statikus
// HTML-galériává a Picasa `.tpl` sablonnyelvével (`picasapy.webexport`).
//
// A FEN-eredetiben van egy élő `printpreview` sablon-előnézet — ez itt
// KIMARADT (a motor a lényeg, nem a sablonválasztó UI-csiszolása); helyette
// a sablon neve/leírása szöveges. Önálló, mozgatható/átméretezhető Window
// (a MoveDatabaseDialog/#368 mintája) — a `Main.qml`-be illesztés (menü-
// bekötés, `webExportController` context property) az integrátoré, ld. a
// `webexport_controller.py` docstringjét.
Window {
    id: webExportWindow
    objectName: "webExportDialog"
    title: ftpMode ? qsTr("Publish via FTP...") : qsTr("Export as HTML Page...")
    modality: Qt.ApplicationModal

    //: #3544: a Shift+F1 fejezete. Külön ablakos, modális párbeszéd: a
    //: főablak súgója mögé kerülne, ezért a `WindowHelp` a párbeszéd FÖLÖTT,
    //: külön ablakban nyitja.
    property string helpTopic: "features/exportalas.md"
    WindowHelp { tema: webExportWindow.helpTopic }
    width: 520
    //: #4611: a tartalomhoz igazodik. A rögzített 360/420 px-es magasságnál a
    //: „Létrehozás" gomb a 435. képpontnál kezdődött, azaz az ablakon kívül
    //: esett, és sablontól függetlenül nem volt kattintható.
    readonly property real fitHeight: mainColumn.implicitHeight + 2 * mainColumn.anchors.margins
    height: Math.max(webExportWindow.minimumHeight, webExportWindow.fitHeight)
    minimumWidth: 460
    minimumHeight: 320
    color: Theme.canvasBg

    // a `webexport.fen` cím-mezője ("edit") — a generált oldalak
    // <%albumName%>-je ez lesz
    property string albumTitle: ""
    property string targetFolder: ""
    property var templates: []          // [{id, name, description}, ...]
    property int templateIndex: 0
    readonly property string templateId:
        webExportWindow.templateIndex >= 0
        && webExportWindow.templateIndex < webExportWindow.templates.length
            ? webExportWindow.templates[webExportWindow.templateIndex].id : ""
    //: #534: a kiválasztott sablon előnézeti rajzának URL-je (üres, ha
    //: nincs) — az eredeti választójában is előnézeti kép van
    //: (`preview.jpg`), nálunk saját, sematikus SVG.
    readonly property url templatePreview:
        webExportWindow.templateIndex >= 0
        && webExportWindow.templateIndex < webExportWindow.templates.length
            ? webExportWindow.templates[webExportWindow.templateIndex].preview : ""

    property bool exporting: false
    property bool ftpMode: false
    property var ftpAccounts: []
    property string selectedFtpAccountId: ""
    property int progressDone: 0
    property int progressTotal: 0

    property string lastError: ""
    property string lastOutputFolder: ""
    property string lastFtpAccount: ""
    property int lastPageCount: 0

    function open() {
        webExportWindow.openWithMode(false)
    }

    function openFtp() {
        webExportWindow.openWithMode(true)
    }

    function openWithMode(publishViaFtp) {
        webExportWindow.ftpMode = publishViaFtp === true
        webExportWindow.lastError = ""
        webExportWindow.lastOutputFolder = ""
        webExportWindow.lastFtpAccount = ""
        var promptForAccount = false
        //: #1956: `typeof` a NÉVRE, `&&` az ÉRTÉKRE
        if (typeof webExportController !== "undefined"
                && webExportController) {
            webExportWindow.templates = webExportController.listWebExportTemplates()
            //: #5714: a mentett útvonalat tölti vissza; az első megnyitáskor
            //: a vezérlő adja a platform szerinti alapmappát.
            var prefs = {
                "targetDir": "",
                "templateId": "",
                "sizeIndex": 3,
                "movieFull": false
            }
            if (typeof webExportController.webExportPrefs === "function")
                prefs = webExportController.webExportPrefs()
            if (webExportWindow.targetFolder.length === 0) {
                webExportWindow.targetFolder = prefs.targetDir
                    || webExportController.defaultWebExportTarget()
            }
            // A korábban mentett sablont azonosító alapján keressük; üres vagy
            // már nem telepített azonosítónál az eredeti 0. index az alap.
            var savedTemplateIndex = 0
            for (var i = 0; i < webExportWindow.templates.length; ++i) {
                if (webExportWindow.templates[i].id === prefs.templateId) {
                    savedTemplateIndex = i
                    break
                }
            }
            webExportWindow.templateIndex = savedTemplateIndex
            // #4610: a méret és a film módja is a mentett beállításból indul.
            sizeBox.currentIndex = prefs.sizeIndex
            movieBox.currentIndex = prefs.movieFull ? 1 : 0
            if (webExportWindow.ftpMode
                    && typeof webExportController.ftpAccounts === "function") {
                webExportWindow.ftpAccounts = webExportController.ftpAccounts()
                webExportWindow.selectedFtpAccountId =
                    webExportController.selectedFtpAccountId()
                ftpAccountBox.currentIndex = webExportWindow.ftpAccounts.findIndex(
                    function (account) {
                        return account.id === webExportWindow.selectedFtpAccountId
                    })
                if (webExportWindow.ftpAccounts.length === 0)
                    promptForAccount = true
            }
        }
        webExportWindow.visible = true
        if (promptForAccount) {
            Qt.callLater(function () { ftpAccountDialog.openFor("") })
        }
    }

    function refreshFtpAccounts(selectedId) {
        if (typeof webExportController === "undefined"
                || !webExportController
                || typeof webExportController.ftpAccounts !== "function") return
        webExportWindow.ftpAccounts = webExportController.ftpAccounts()
        webExportWindow.selectedFtpAccountId = selectedId
                || webExportController.selectedFtpAccountId()
        ftpAccountBox.currentIndex = webExportWindow.ftpAccounts.findIndex(
            function (account) {
                return account.id === webExportWindow.selectedFtpAccountId
            })
    }

    function startExport() {
        if ((!webExportWindow.ftpMode && webExportWindow.targetFolder.length === 0)
            || webExportWindow.templateId.length === 0) return
        webExportWindow.lastError = ""
        if (webExportWindow.ftpMode) {
            if (webExportWindow.selectedFtpAccountId.length === 0) return
            webExportController.publishWebExport(
                webExportWindow.selectedFtpAccountId,
                webExportWindow.templateId,
                webExportWindow.albumTitle,
                sizeBox.currentIndex,
                movieBox.currentIndex === 1)
        } else {
            webExportController.generateWebExport(
                webExportWindow.targetFolder,
                webExportWindow.templateId,
                webExportWindow.albumTitle,
                sizeBox.currentIndex,
                movieBox.currentIndex === 1)
        }
    }

    Connections {
        target: typeof webExportController !== "undefined" ? webExportController : null
        function onWebExportStarted() {
            webExportWindow.exporting = true
            webExportWindow.progressDone = 0
            webExportWindow.progressTotal = 0
        }
        function onWebExportProgress(done, total) {
            webExportWindow.progressDone = done
            webExportWindow.progressTotal = total
        }
        function onWebExportFinished(outputFolder, pageCount) {
            webExportWindow.exporting = false
            webExportWindow.lastOutputFolder = outputFolder
            webExportWindow.lastPageCount = pageCount
        }
        function onFtpPublishFinished(accountName, fileCount) {
            webExportWindow.exporting = false
            webExportWindow.lastFtpAccount = accountName
            webExportWindow.lastPageCount = fileCount
        }
        function onWebExportFailed(message) {
            webExportWindow.exporting = false
            webExportWindow.lastError = message
        }
    }

    ColumnLayout {
        id: mainColumn
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        // -- cím (albumName override) --------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            enabled: !webExportWindow.exporting
            Text {
                text: qsTr("Page title:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            TextField {
                id: titleField
                objectName: "webExportTitleField"
                Layout.fillWidth: true
                text: webExportWindow.albumTitle
                onTextEdited: webExportWindow.albumTitle = text
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
        }

        // -- FTP-fiók ---------------------------------------------------------
        RowLayout {
            objectName: "webExportFtpAccountRow"
            Layout.fillWidth: true
            spacing: 8
            visible: webExportWindow.ftpMode
            enabled: !webExportWindow.exporting
            Text {
                text: qsTr("FTP account:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            PicasaComboBox {
                id: ftpAccountBox
                objectName: "webExportFtpAccountBox"
                Layout.fillWidth: true
                model: webExportWindow.ftpAccounts.map(function (account) {
                    return account.name
                })
                onActivated: {
                    if (currentIndex >= 0) {
                        webExportWindow.selectedFtpAccountId =
                            webExportWindow.ftpAccounts[currentIndex].id
                        if (typeof webExportController !== "undefined"
                                && webExportController)
                            webExportController.selectFtpAccount(
                                webExportWindow.selectedFtpAccountId)
                    }
                }
            }
            PicasaButton {
                objectName: "webExportFtpAccountsButton"
                text: qsTr("Manage...")
                onClicked: ftpAccountDialog.openFor(
                    webExportWindow.selectedFtpAccountId)
            }
        }

        // -- célmappa ---------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            enabled: !webExportWindow.exporting
            visible: !webExportWindow.ftpMode
            Text {
                text: qsTr("Save to:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Text {
                    objectName: "webExportTargetText"
                    Layout.fillWidth: true
                    elide: Text.ElideMiddle
                    text: webExportWindow.targetFolder.length > 0
                          ? webExportWindow.targetFolder
                          : qsTr("(not selected)")
                    font.pixelSize: Theme.fontSize
                    color: Theme.textGray
                }
                PicasaButton {
                    objectName: "webExportBrowseButton"
                    text: qsTr("Browse...")
                    onClicked: targetFolderDialog.open()
                }
            }
        }

        // -- sablon -------------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            enabled: !webExportWindow.exporting
            Text {
                text: qsTr("Template:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            PicasaComboBox {
                id: templateBox
                objectName: "webExportTemplateBox"
                Layout.fillWidth: true
                model: webExportWindow.templates.map(function(t) { return t.name })
                currentIndex: webExportWindow.templateIndex
                onActivated: webExportWindow.templateIndex = currentIndex
            }
            Image {
                objectName: "webExportTemplatePreview"
                source: webExportWindow.templatePreview
                visible: webExportWindow.templatePreview.toString().length > 0
                //: a rajz 160 x 100; kétszeres méretben kérjük be, hogy
                //: nagy felbontású kijelzőn se legyen puha
                sourceSize.width: 320
                sourceSize.height: 200
                fillMode: Image.PreserveAspectFit
                Layout.preferredWidth: 160
                Layout.preferredHeight: 100
                Layout.topMargin: 4
            }
            Text {
                objectName: "webExportTemplateDescription"
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: webExportWindow.templateIndex >= 0
                      && webExportWindow.templateIndex < webExportWindow.templates.length
                      ? webExportWindow.templates[webExportWindow.templateIndex].description : ""
                font.pixelSize: Theme.fontSize - 1
                color: Theme.textGray
            }
        }

        // -- méret és mozgókép-mód -----------------------------------------------
        // #4610 (spec `picasa-menu-parancsok-viselkedes.md` 6.1): az eredeti
        // `webexport.fen` EGY méretválasztót ad (`sizeradio`, a nagy kép
        // mérete) — a bélyegkép méretét a sablon szabja meg (hiányában 144
        // képpont). Mellette a mozgókép-mód (`moviesradio`). Az elemek
        // sorrendje és angol forrásszövege a FEN-é, a magyar felirat a
        // hivatalos katalógusé (`webexport/itemN`); a címke+legördülő
        // rács elrendezése a miénk. A képpont-táblát a vezérlő tartja
        // (`SIZE_CHOICES`), a QML csak az indexet adja át.
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 8
            rowSpacing: 6
            enabled: !webExportWindow.exporting
            Text {
                text: qsTr("Export pictures at:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            PicasaComboBox {
                id: sizeBox
                objectName: "webExportSizeBox"
                Layout.fillWidth: true
                model: [qsTr("Original Size"),
                        qsTr("1024 pixels (for large monitors)"),
                        qsTr("800 pixels (for large Web pages)"),
                        qsTr("640 pixels (for Web pages)"),
                        qsTr("320 pixels (for email)")]
                // `Preferences\WebExportSize` alapértéke → 640 képpont
                currentIndex: 3
            }
            Text {
                text: qsTr("Export movies using:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            PicasaComboBox {
                id: movieBox
                objectName: "webExportMovieBox"
                Layout.fillWidth: true
                model: [qsTr("First frame"), qsTr("Full movie")]
                // `Preferences\WebExportMovie` alapértéke → Első képkocka
                currentIndex: 0
            }
        }

        Text {
            objectName: "webExportErrorText"
            visible: webExportWindow.lastError.length > 0
            text: webExportWindow.lastError
            color: Theme.brandRed
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        // -- haladás-nézet --------------------------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            visible: webExportWindow.exporting
            spacing: 6
            Text {
                text: qsTr("PicasaPy is generating the web page.")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 8
                radius: 4
                color: Theme.trackBg
                border.color: Theme.chromeBorder
                Rectangle {
                    objectName: "webExportProgressFill"
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    radius: parent.radius
                    color: Theme.picasaGreen
                    width: webExportWindow.progressTotal > 0
                           ? parent.width * webExportWindow.progressDone
                                 / webExportWindow.progressTotal
                           : 0
                }
            }
        }

        Text {
            objectName: "webExportResultText"
            visible: webExportWindow.ftpMode
                     ? webExportWindow.lastFtpAccount.length > 0
                     : webExportWindow.lastOutputFolder.length > 0
            text: webExportWindow.ftpMode
                  ? qsTr("Published %1 file(s) to %2.")
                    .arg(webExportWindow.lastPageCount).arg(webExportWindow.lastFtpAccount)
                  : qsTr("Web page generated: %1 file(s) in %2")
                    .arg(webExportWindow.lastPageCount).arg(webExportWindow.lastOutputFolder)
            color: Theme.picasaGreen
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Item { Layout.fillWidth: true }
            PicasaButton {
                objectName: "webExportGenerateButton"
                text: webExportWindow.ftpMode ? qsTr("Publish") : qsTr("Create")
                accent: Theme.picasaGreen
                enabled: (webExportWindow.ftpMode
                          || webExportWindow.targetFolder.length > 0)
                         && webExportWindow.templateId.length > 0
                         && (!webExportWindow.ftpMode
                             || webExportWindow.selectedFtpAccountId.length > 0)
                         && !webExportWindow.exporting
                onClicked: webExportWindow.startExport()
            }
            PicasaButton {
                objectName: "webExportCloseButton"
                text: qsTr("Close")
                enabled: !webExportWindow.exporting
                onClicked: webExportWindow.visible = false
            }
        }
    }

    Dialog {
        id: ftpAccountDialog
        objectName: "ftpAccountDialog"
        title: qsTr("Manage FTP Accounts")
        modal: true
        x: Math.max(0, (webExportWindow.width - width) / 2)
        y: Math.max(0, (webExportWindow.height - height) / 2)
        width: 390
        standardButtons: Dialog.NoButton
        property string editingId: ""
        property string accountError: ""

        function openFor(accountId) {
            ftpAccountDialog.editingId = accountId || ""
            ftpAccountDialog.accountError = ""
            if (ftpAccountDialog.editingId.length > 0
                    && typeof webExportController !== "undefined"
                    && webExportController) {
                var account = webExportController.ftpAccount(
                    ftpAccountDialog.editingId)
                accountNameField.text = account.name || ""
                accountHostField.text = account.domain || ""
                accountUserField.text = account.user || ""
                accountRootField.text = account.root || "/"
            } else {
                ftpAccountDialog.beginNew()
            }
            accountPasswordField.text = ""
            ftpAccountDialog.open()
        }

        function beginNew() {
            ftpAccountDialog.editingId = ""
            accountNameField.text = ""
            accountHostField.text = ""
            accountUserField.text = ""
            accountRootField.text = "/"
            accountPasswordField.text = ""
            ftpAccountDialog.accountError = ""
        }

        function saveAccount() {
            var result = webExportController.saveFtpAccount(
                ftpAccountDialog.editingId,
                accountNameField.text,
                accountHostField.text,
                accountUserField.text,
                accountRootField.text,
                accountPasswordField.text)
            if (!result.ok) {
                ftpAccountDialog.accountError = result.error
                return
            }
            webExportController.selectFtpAccount(result.id)
            webExportWindow.refreshFtpAccounts(result.id)
            ftpAccountDialog.close()
        }

        function deleteAccount() {
            if (ftpAccountDialog.editingId.length === 0) return
            if (!webExportController.deleteFtpAccount(
                    ftpAccountDialog.editingId)) {
                ftpAccountDialog.accountError = qsTr("The account could not be deleted.")
                return
            }
            ftpAccountDialog.beginNew()
            webExportWindow.refreshFtpAccounts("")
        }

        contentItem: ColumnLayout {
            spacing: 8
            Label { text: qsTr("Account name:") }
            TextField {
                id: accountNameField
                objectName: "ftpAccountNameField"
                Layout.fillWidth: true
                TextFieldContextArea {}
            }
            Label { text: qsTr("FTP server:") }
            TextField {
                id: accountHostField
                objectName: "ftpAccountHostField"
                Layout.fillWidth: true
                TextFieldContextArea {}
            }
            Label { text: qsTr("Username:") }
            TextField {
                id: accountUserField
                objectName: "ftpAccountUserField"
                Layout.fillWidth: true
                TextFieldContextArea {}
            }
            Label { text: qsTr("Password:") }
            TextField {
                id: accountPasswordField
                objectName: "ftpAccountPasswordField"
                Layout.fillWidth: true
                echoMode: TextInput.Password
                TextFieldContextArea {}
            }
            Label { text: qsTr("Remote folder:") }
            TextField {
                id: accountRootField
                objectName: "ftpAccountRootField"
                Layout.fillWidth: true
                TextFieldContextArea {}
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: Theme.textGray
                text: ftpAccountDialog.editingId.length > 0
                      ? qsTr("Leave blank to keep the saved password.") : ""
            }
            Text {
                objectName: "ftpAccountErrorText"
                visible: ftpAccountDialog.accountError.length > 0
                text: ftpAccountDialog.accountError
                color: Theme.brandRed
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            RowLayout {
                Layout.fillWidth: true
                PicasaButton {
                    objectName: "ftpAccountNewButton"
                    text: qsTr("New")
                    onClicked: ftpAccountDialog.beginNew()
                }
                PicasaButton {
                    objectName: "ftpAccountDeleteButton"
                    text: qsTr("Delete")
                    enabled: ftpAccountDialog.editingId.length > 0
                    onClicked: ftpAccountDialog.deleteAccount()
                }
                Item { Layout.fillWidth: true }
                PicasaButton {
                    objectName: "ftpAccountCancelButton"
                    text: qsTr("Cancel")
                    onClicked: ftpAccountDialog.close()
                }
                PicasaButton {
                    objectName: "ftpAccountSaveButton"
                    text: qsTr("Save")
                    accent: Theme.picasaGreen
                    onClicked: ftpAccountDialog.saveAccount()
                }
            }
        }
    }

    FolderDialog {
        id: targetFolderDialog
        title: qsTr("Choose target folder...")
        onAccepted: webExportWindow.targetFolder = selectedFolder.toString()
    }
}
