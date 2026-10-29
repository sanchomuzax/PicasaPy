import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Weboldal exportálása (#351, `webexport.fen`, docs/specs/
// picasa-fen-dialogs.md 3.12.): a kijelölt mappa/album exportja statikus
// HTML-galériává a Picasa `.tpl` sablonnyelvével (`picasapy.webexport`).
//
// A párbeszéd a `webexport.fen` sablonlistáját, leírását és előnézeti
// képét adja. Önálló, mozgatható/átméretezhető Window (a
// MoveDatabaseDialog/#368 mintája), a `Main.qml`-be illesztés
// (menübekötés, `webExportController` context property) az integrátoré,
// ld. a `webexport_controller.py` docstringjét.
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
    width: 760
    //: #4611: a tartalomhoz igazodik. A rögzített 360/420 px-es magasságnál a
    //: „Létrehozás" gomb a 435. képpontnál kezdődött, azaz az ablakon kívül
    //: esett, és sablontól függetlenül nem volt kattintható.
    readonly property real fitHeight: mainColumn.implicitHeight + 2 * mainColumn.anchors.margins
    height: Math.max(webExportWindow.minimumHeight, webExportWindow.fitHeight)
    minimumWidth: 700
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
    readonly property var htmlTemplateEntries: orderedHtmlTemplateEntries()
    readonly property var templateDisplayNames:
        webExportWindow.htmlTemplateEntries.map(
            function (template) { return webExportWindow.templateDisplayName(template) })
    readonly property int htmlTemplateIndex:
        webExportWindow.htmlTemplateEntries.findIndex(
            function (template) { return template.id === webExportWindow.templateId })
    //: #534: a kiválasztott sablon előnézeti rajzának URL-je (üres, ha
    //: nincs) — az eredeti választójában is előnézeti kép van
    //: (`preview.jpg`), nálunk saját, sematikus SVG.
    readonly property url templatePreview:
        webExportWindow.templateIndex >= 0
        && webExportWindow.templateIndex < webExportWindow.templates.length
            ? webExportWindow.templates[webExportWindow.templateIndex].preview : ""

    function orderedHtmlTemplateEntries() {
        var picasaOrder = [
            "szurke", "fekete", "feher",
            "szurke-keret", "fekete-keret", "feher-keret", "xml"
        ]
        var ordered = []
        for (var i = 0; i < picasaOrder.length; ++i) {
            for (var j = 0; j < webExportWindow.templates.length; ++j) {
                if (webExportWindow.templates[j].id === picasaOrder[i])
                    ordered.push(webExportWindow.templates[j])
            }
        }
        for (var k = 0; k < webExportWindow.templates.length; ++k) {
            if (picasaOrder.indexOf(webExportWindow.templates[k].id) < 0)
                ordered.push(webExportWindow.templates[k])
        }
        return ordered
    }

    function templateDisplayName(template) {
        if (!template) return ""
        switch (template.id) {
        case "szurke":
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:webtpl_greybg_name
            return qsTr("Template 1, 2-page grey background")
        case "fekete":
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:webtpl_blackbg_name
            return qsTr("Template 2, 2-page black background")
        case "feher":
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:webtpl_whitebg_name
            return qsTr("Template 3, 2-page white background")
        case "szurke-keret":
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:webtpl_greyfrm_name
            return qsTr("Template 4, 1-page grey background")
        case "fekete-keret":
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:webtpl_blackfrm_name
            return qsTr("Template 5, 1-page black background")
        case "feher-keret":
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:webtpl_whitefrm_name
            return qsTr("Template 6, 1-page white background")
        case "xml":
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:webtpl_xml_name
            return qsTr("XML Code")
        default:
            return template.name
        }
    }

    function templateDescription(template) {
        if (!template) return ""
        switch (template.id) {
        case "szurke":
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:webtpl_greybg_descr
            return qsTr("Thumbnail index page linked to a full view picture page.")
        case "fekete":
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:webtpl_blackbg_descr
            return qsTr("Thumbnail index page linked to a full view picture page.")
        case "feher":
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:webtpl_whitebg_descr
            return qsTr("Thumbnail index page linked to a full view picture page.")
        case "szurke-keret":
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:webtpl_greyfrm_descr
            return qsTr("Scrollable thumbnail index on left with full view picture on right.")
        case "fekete-keret":
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:webtpl_blackfrm_descr
            return qsTr("Scrollable thumbnail index on left with full view picture on right.")
        case "feher-keret":
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:webtpl_whitefrm_descr
            return qsTr("Scrollable thumbnail index on left with full view picture on right.")
        case "xml":
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:webtpl_xml_descr
            return qsTr("Raw XML-formatted text for further translation.")
        default:
            return template.description
        }
    }

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

    function currentFolderTitle() {
        if (typeof controller === "undefined" || !controller) return ""
        var path = String(controller.currentFolder || "").replace(/[\\/]+$/, "")
        var parts = path.split(/[\\/]/)
        return parts.length > 0 ? parts[parts.length - 1] : ""
    }

    function openWithMode(publishViaFtp) {
        webExportWindow.ftpMode = publishViaFtp === true
        if (!webExportWindow.ftpMode)
            webExportWindow.albumTitle = webExportWindow.currentFolderTitle()
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
            // A mentett sablont azonosító alapján keressük. HTML-módban az
            // eredeti lista első eleme (Template 1, szürke háttér) az alap;
            // FTP-módban a korábbi kiválasztás marad.
            var defaultTemplateId = webExportWindow.ftpMode ? "" : "szurke"
            var preferredTemplateId = prefs.templateId || defaultTemplateId
            var savedTemplateIndex = 0
            for (var i = 0; i < webExportWindow.templates.length; ++i) {
                if (webExportWindow.templates[i].id === preferredTemplateId) {
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

    function generateButtonText() {
        if (webExportWindow.ftpMode) return qsTr("Publish")
        //: picasapy-origin: picasa
        //: picasapy-origin-key: webexport:webexport/button29.title
        return qsTr("Export")
    }

    function closeButtonText() {
        if (webExportWindow.ftpMode) return qsTr("Close")
        //: picasapy-origin: picasa
        //: picasapy-origin-key: webexport:webexport/button30.title
        return qsTr("Cancel")
    }

    function titleLabelText() {
        if (webExportWindow.ftpMode) return qsTr("Page title:")
        //: picasapy-origin: picasa
        //: picasapy-origin-key: webexport:webexport/labelgroup13.title
        return qsTr("Web page title:")
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

        // -- méret és mozgókép-mód -----------------------------------------------
        // #4610 (spec `picasa-menu-parancsok-viselkedes.md` 6.1): az eredeti
        // `webexport.fen` EGY méretválasztót ad (`sizeradio`, a nagy kép
        // mérete): a bélyegkép méretét a sablon szabja meg (hiányában 144
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
                // `Preferences\\WebExportSize` alapértéke → 640 képpont
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
                // `Preferences\\WebExportMovie` alapértéke → Első képkocka
                currentIndex: 0
            }
        }

        // -- cím (albumName override) --------------------------------------
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            enabled: !webExportWindow.exporting
            Text {
                objectName: "webExportTitleLabel"
                text: webExportWindow.titleLabelText()
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
                objectName: "webExportTargetLabel"
                //: picasapy-origin: picasa
                //: picasapy-origin-key: webexport:webexport/labelgroup15.title
                text: qsTr("Folder:")
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

        WebExportTemplatePane {
            id: webExportTemplatePane
            Layout.fillWidth: true
            ftpMode: webExportWindow.ftpMode
            exporting: webExportWindow.exporting
            templates: webExportWindow.templates
            htmlTemplateEntries: webExportWindow.htmlTemplateEntries
            htmlTemplateIndex: webExportWindow.htmlTemplateIndex
            templateIndex: webExportWindow.templateIndex
            templatePreview: webExportWindow.templatePreview
            templateDisplayName: function (template) {
                return webExportWindow.templateDisplayName(template)
            }
            templateDescription: function (template) {
                return webExportWindow.templateDescription(template)
            }
            onHtmlTemplateSelected: function (selectedId) {
                for (var i = 0; i < webExportWindow.templates.length; ++i) {
                    if (webExportWindow.templates[i].id === selectedId) {
                        webExportWindow.templateIndex = i
                        break
                    }
                }
            }
            onFtpTemplateSelected: function (index) {
                webExportWindow.templateIndex = index
            }
        }

        WebExportStatusPane {
            ftpMode: webExportWindow.ftpMode
            exporting: webExportWindow.exporting
            lastError: webExportWindow.lastError
            lastOutputFolder: webExportWindow.lastOutputFolder
            lastFtpAccount: webExportWindow.lastFtpAccount
            progressDone: webExportWindow.progressDone
            progressTotal: webExportWindow.progressTotal
            lastPageCount: webExportWindow.lastPageCount
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Item { Layout.fillWidth: true }
            PicasaButton {
                objectName: "webExportGenerateButton"
                text: webExportWindow.generateButtonText()
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
                text: webExportWindow.closeButtonText()
                enabled: !webExportWindow.exporting
                onClicked: webExportWindow.visible = false
            }
        }
    }

    FtpAccountDialog {
        id: ftpAccountDialog
        ownerWindow: webExportWindow
    }

    FolderDialog {
        id: targetFolderDialog
        title: qsTr("Choose target folder...")
        onAccepted: webExportWindow.targetFolder = selectedFolder.toString()
    }
}
