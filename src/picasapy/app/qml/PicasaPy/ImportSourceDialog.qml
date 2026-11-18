import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Import forrásból (#23/#441): külső mappa (pl. fényképezőgép/kártya
// csatolt mappája, vagy bármely más mappa) képeinek/videóinak másolása a
// könyvtárba — a főablak központi munkaterületén, a könyvtár helyén.
//
// #441 — a mai szabad szöveges mappa-sablon mező helyett HÁROM célmappa-
// elnevezési mód (namingMode: "manual" | "date" | "today"), duplikátum-
// kizárás (autoExclude, a jelölt-előnézetben "duplicate"/"excluded"
// zászlókkal), egyenkénti válogatás, és háromállapotú, kétlépcsős
// megerősítésű forrás-törlés ("After Copying:").
Rectangle {
    id: importSourceWindow
    objectName: "importSourceDialog"
    required property var hostWindow
    anchors.fill: parent
    color: Theme.canvasBg
    implicitWidth: 900
    implicitHeight: importSourceContent.implicitHeight
                     + 2 * importSourceContent.anchors.margins

    //: A Shift+F1 fejezete a főablak saját súgóján keresztül nyílik.
    property string helpTopic: "features/importalas.md"
    property bool closeAfterNextImport: false
    property bool closeAfterImport: false

    onVisibleChanged: {
        if (hostWindow && hostWindow.importPanelOpen !== visible)
            hostWindow.importPanelOpen = visible
        if (visible)
            importSourceWindow.loadStoredImportChoices()
        if (visible
                && typeof importSourceController !== "undefined"
                && importSourceController
                && importSourceController.refreshMountedSources !== undefined)
            importSourceController.refreshMountedSources()
    }

    // a forrás/cél FolderDialog `selectedFolder.toString()`-ja (file:// URL
    // is lehet) — a Pythonnak MINDIG ezt a nyers alakot adjuk át, a
    // `to_local_path` ott alakítja lokális útvonallá (a Mappakezelő
    // `addWatchedFolder`-jének mintája); a felület a megjelenítéshez
    // egyszerűen lehántja a "file://" előtagot.
    property string sourceFolder: ""
    // #4596: a forrás kijelölt FÁJLOK listája is lehet (file:// URL-ek) —
    // ekkor a `sourceFolder` üres. Mappa-választás törli.
    property var sourceFiles: []
    readonly property bool hasSource:
        importSourceWindow.sourceFolder.length > 0
        || importSourceWindow.sourceFiles.length > 0
    property string destFolder: ""

    // A Qt által észlelt, csatolt kártyák és USB-meghajtók. A
    // forrásfajta feliratát itt fordítjuk; a vezérlő csak útvonalat és
    // kötetcímkét ad vissza.
    readonly property var mountedSourceOptions: {
        if (typeof importSourceController === "undefined"
                || !importSourceController
                || importSourceController.mountedSources === undefined)
            return []
        var sources = importSourceController.mountedSources
        var options = []
        for (var i = 0; i < sources.length; i++) {
            options.push({
                "path": sources[i].path,
                "label": qsTr("Removable Drive (%1)").arg(sources[i].name)
            })
        }
        return options
    }

    // #441: a HÁROM célmappa-elnevezési mód — a `picasapy.importsource.
    // NAMING_*` konstansaival egyező string. #7183: az eredeti alapértéke a
    // kézi cím (`acquireUseSubFolder` = 0, `0x00514180`); az ablak nyitáskor
    // a vezérlő tárolt értékét veszi fel (`loadStoredImportChoices`).
    property string namingMode: "manual"
    property string manualFolderName: ""
    // #4837: a kézi név egyetlen, biztonságos útvonal-elem-e (Python dönt)
    readonly property bool manualNameValid:
        manualFolderName.trim().length > 0
        && (!importSourceController
            || importSourceController.isValidFolderName === undefined
            || importSourceController.isValidFolderName(manualFolderName))

    // #441: "After Copying:" — a `picasapy.app.import_source_controller.
    // AFTER_COPY_*` konstansaival egyező string. #7183: a VÁLASZTOTT (tárolt)
    // érték; ténylegesen csak törölhető forrásnál érvényes, egyébként az
    // `effectiveAfterCopying` Leave.
    property string afterCopying: "leave"
    // #7183: a forrás a csatolt meghajtók listájából jött-e (a mappa-, fájl- és
    // előzményforrás sosem törölhető). A forrásválasztók állítják.
    property bool sourceFromDrive: false
    // #7183: törölhető forrás = csatolt meghajtó, gyökerében `DCIM` mappával
    // (`0x0050f590` → `0x0050f6a0`); a vizsgálat Python-oldali (kis-nagybetű
    // érzéketlen).
    readonly property bool sourceDeletable:
        importSourceWindow.sourceFromDrive
        && importSourceWindow.sourceFiles.length === 0
        && importSourceWindow.sourceFolder.length > 0
        && (typeof importSourceController !== "undefined"
            && importSourceController
            && importSourceController.isDeletableSource !== undefined)
        && importSourceController.isDeletableSource(
               importSourceWindow.sourceFolder) === true
    readonly property string effectiveAfterCopying:
        importSourceWindow.sourceDeletable
            ? importSourceWindow.afterCopying : "leave"

    property bool scanning: false
    // előnézeti elemek — dict-ek listája: {path, thumbUrl, duplicate,
    // excluded, rotation, starred}; a controller MINDIG listát ad (ld.
    // MEMORY.md-tanulság)
    property var previewItems: []
    property int previewCount: 0
    // Az eredeti previous/next gombok az előnézeti képet léptetik. A
    // bélyegkép-rács megmarad; a kijelölt kép kiemelése és görgetése követi.
    property int selectedPreviewIndex: 0
    // A rácsbeli importkijelölés külön él az előnézeti képtől.
    property var selectedPreviewPaths: []
    readonly property int duplicateCount: {
        var count = 0
        for (var i = 0; i < importSourceWindow.previewItems.length; i++) {
            if (importSourceWindow.previewItems[i].duplicate) count++
        }
        return count
    }
    readonly property int includedCount: {
        var count = 0
        for (var j = 0; j < importSourceWindow.previewItems.length; j++) {
            if (!importSourceWindow.previewItems[j].excluded) count++
        }
        return count
    }
    readonly property int selectedPreviewCount: {
        var count = 0
        for (var i = 0; i < importSourceWindow.previewItems.length; i++) {
            if (importSourceWindow.isPreviewSelected(
                    importSourceWindow.previewItems[i].path)) count++
        }
        return count
    }
    readonly property int selectedIncludedCount: {
        var count = 0
        for (var j = 0; j < importSourceWindow.previewItems.length; j++) {
            var item = importSourceWindow.previewItems[j]
            if (!item.excluded
                    && importSourceWindow.isPreviewSelected(item.path)) count++
        }
        return count
    }
    readonly property bool canStartImport:
        destFolder.length > 0
        && !importing
        && (namingMode !== "manual" || manualNameValid)
    readonly property bool canImportAll: includedCount > 0 && canStartImport
    readonly property bool canImportSelected:
        selectedIncludedCount > 0 && canStartImport

    property bool importing: false
    property bool pendingSelectedOnly: false
    property int importDone: 0
    property int importTotal: 0
    // #441: a másolás sebessége bájt/mp-ben (0 = még nem mérhető)
    property real importBytesPerSecond: 0
    // a sebesség emberi alakja — a méret-formázás mintáját követve
    // (bájt és KB egészre, MB-tól egy tizedesre)
    function formatSpeed(bytesPerSecond) {
        if (bytesPerSecond >= 1024 * 1024)
            return (bytesPerSecond / (1024 * 1024)).toFixed(1) + " MB"
        if (bytesPerSecond >= 1024)
            return Math.round(bytesPerSecond / 1024) + " KB"
        return Math.round(bytesPerSecond) + " " + qsTr("bytes")
    }
    // -1: még nem futott import ebben a munkamenetben (az eredmény-sor rejtve)
    property int lastCopiedCount: -1
    property int lastFailedCount: -1

    property string lastError: ""

    // #7183: az almappa-mód és a törlési mód az import INDÍTÁSAKOR mentődik;
    // újranyitáskor a tárolt érték látszik (a nyitás óta csak átállított,
    // el nem indított választás elvész, mint az eredetiben).
    function loadStoredImportChoices() {
        if (typeof importSourceController === "undefined"
                || !importSourceController)
            return
        if (importSourceController.namingMode !== undefined)
            importSourceWindow.namingMode = importSourceController.namingMode
        if (importSourceController.afterCopying !== undefined)
            importSourceWindow.afterCopying = importSourceController.afterCopying
    }

    Component.onCompleted: importSourceWindow.loadStoredImportChoices()

    //: #1629: a megjelenített útvonal OS-NATÍV alakban. A szöveges
    //: `file://`-levágás Windowson `/C:/Users/…`-t hagyott maga után; a
    //: helyes átalakítás csak Python-oldalon végezhető el (`to_local_path`,
    //: #1626). A null-őr a #305/#1572 mintája: a párbeszéd önálló
    //: próbákban is betöltődik, ahol a vezérlő nincs regisztrálva.
    readonly property string sourceFolderDisplay: {
        var toLocal = function (url) {
            return (typeof fileOpsController !== "undefined" && fileOpsController)
                ? fileOpsController.toLocalPath(url)
                : url.replace(/^file:\/\//, "")
        }
        var files = importSourceWindow.sourceFiles
        if (files.length > 0)
            return toLocal(files[0])
                + (files.length > 1 ? " (+" + (files.length - 1) + ")" : "")
        return toLocal(importSourceWindow.sourceFolder)
    }
    readonly property string destFolderDisplay:
        (typeof fileOpsController !== "undefined" && fileOpsController)
            ? fileOpsController.toLocalPath(importSourceWindow.destFolder)
            : importSourceWindow.destFolder.replace(/^file:\/\//, "")

    function open() {
        if (typeof importSourceController !== "undefined"
            && importSourceController
            && importSourceController.defaultDestination !== undefined)
            importSourceWindow.destFolder = importSourceController.defaultDestination
        if (importSourceWindow.hostWindow)
            importSourceWindow.hostWindow.importPanelOpen = true
        importSourceWindow.visible = true
        if (typeof importSourceController !== "undefined"
                && importSourceController
                && importSourceController.refreshMountedSources !== undefined)
            importSourceController.refreshMountedSources()
    }

    function closePanel() {
        if (importSourceWindow.hostWindow)
            importSourceWindow.hostWindow.importPanelOpen = false
        importSourceWindow.visible = false
    }

    function importBeforeClosing() {
        importSourceWindow.closeAfterNextImport = true
        importSourceWindow.requestImport()
    }

    function stepPreview(delta) {
        var nextIndex = importSourceWindow.selectedPreviewIndex + delta
        if (nextIndex < 0 || nextIndex >= importSourceWindow.previewItems.length)
            return
        importSourceWindow.selectedPreviewIndex = nextIndex
        previewPanel.positionAt(nextIndex)
    }

    function isPreviewSelected(path) {
        return importSourceWindow.selectedPreviewPaths.indexOf(path) >= 0
    }

    function togglePreviewSelection(path, index) {
        var selected = importSourceWindow.selectedPreviewPaths.slice()
        var current = selected.indexOf(path)
        if (current >= 0) selected.splice(current, 1)
        else selected.push(path)
        importSourceWindow.selectedPreviewPaths = selected
        importSourceWindow.selectedPreviewIndex = index
        previewPanel.positionAt(index)
    }

    function selectedImportPaths() {
        var selected = []
        for (var i = 0; i < importSourceWindow.previewItems.length; i++) {
            var item = importSourceWindow.previewItems[i]
            if (!item.excluded
                    && importSourceWindow.isPreviewSelected(item.path))
                selected.push(item.path)
        }
        return selected
    }

    // #7183: a mappa-forrás kiválasztása — a mappaválasztó, a korábbi források
    // és a csatolt meghajtók legördülője egyaránt ezen át állít forrást;
    // `fromDrive` csak a csatolt meghajtók listájából igaz.
    function useSourceFolder(folder, fromDrive) {
        importSourceWindow.sourceFiles = []
        importSourceWindow.sourceFolder = folder
        importSourceWindow.sourceFromDrive = fromDrive === true
        importSourceWindow.scanCurrentSource()
    }

    // a forrás (rekurzív) beolvasása háttérszálon — a FolderDialog
    // elfogadásakor és tesztből is hívható (a DedupDialog `scan()` mintája)
    function scanCurrentSource() {
        importSourceWindow.lastError = ""
        importSourceWindow.previewItems = []
        importSourceWindow.previewCount = 0
        importSourceWindow.selectedPreviewIndex = 0
        importSourceWindow.lastCopiedCount = -1
        importSourceWindow.lastFailedCount = -1
        if (!importSourceWindow.hasSource) return
        importSourceWindow.scanning = true
        if (importSourceWindow.sourceFiles.length > 0)
            importSourceController.scanFiles(importSourceWindow.sourceFiles)
        else
            importSourceController.scanSource(importSourceWindow.sourceFolder)
    }

    // #4596: a fájlválasztó kijelölése lesz a forrás. Külön függvény, hogy a
    // natív választó megkerülésével is tesztelhető legyen (AddFileDialog
    // `addSelectedFiles` mintája).
    function useSelectedFiles(fileUrls) {
        if (!fileUrls || fileUrls.length === 0) return
        importSourceWindow.sourceFolder = ""
        importSourceWindow.sourceFromDrive = false
        importSourceWindow.sourceFiles = fileUrls.map(function (url) {
            return url.toString()
        })
        importSourceWindow.scanCurrentSource()
    }

    // #441: a másolás tényleges indítása — a kétlépcsős megerősítés (ld.
    // lent, `requestImport`) UTÁN hívódik.
    function runImportNow() {
        importSourceWindow.lastError = ""
        importSourceWindow.closeAfterImport =
            importSourceWindow.closeAfterNextImport
        importSourceWindow.closeAfterNextImport = false
        if (importSourceWindow.pendingSelectedOnly) {
            importSourceController.runSelectedImport(
                importSourceWindow.destFolder,
                importSourceWindow.namingMode,
                importSourceWindow.manualFolderName,
                importSourceWindow.effectiveAfterCopying,
                importSourceWindow.selectedImportPaths())
        } else {
            importSourceController.runImport(
                importSourceWindow.destFolder,
                importSourceWindow.namingMode,
                importSourceWindow.manualFolderName,
                importSourceWindow.effectiveAfterCopying)
        }
    }

    // "After Copying:" - a törléssel járó két állapotnál EGYETLEN
    // megerősítés (az eredeti `0x00519720`, #7173); "Leave card alone"-nál
    // nincs kérdés.
    function requestImport() {
        importSourceWindow.requestImportMode(false)
    }

    function requestSelectedImport() {
        importSourceWindow.requestImportMode(true)
    }

    function requestImportMode(selectedOnly) {
        var onlySelected = selectedOnly === true
        if (onlySelected && !importSourceWindow.canImportSelected) return
        if (!onlySelected && !importSourceWindow.canImportAll) return
        importSourceWindow.pendingSelectedOnly = onlySelected
        if (importSourceWindow.effectiveAfterCopying === "leave") {
            importSourceWindow.runImportNow()
            return
        }
        // Delete Copied: a `confirmRemoveCopied::message` eredeti szövege
        // (kisbetűs második mondattal); Delete All: a vezérlő összeállított
        // figyelmeztetése.
        removeConfirm.ask("", importSourceWindow.effectiveAfterCopying === "delete_all"
            ? importSourceController.wipeCardWarning()
            : qsTr("Are you sure you want to remove the imported files from "
                   + "your card? This cannot be undone."))
    }

    function activateDefaultImport() {
        if (importSourceWindow.selectedPreviewCount <= 1)
            importSourceWindow.requestImport()
        else
            importSourceWindow.requestSelectedImport()
    }

    Connections {
        target: typeof importSourceController !== "undefined"
                ? importSourceController : null
        function onSourceScanFinished(items, count) {
            importSourceWindow.previewItems = items
            importSourceWindow.previewCount = count
            importSourceWindow.selectedPreviewIndex = 0
            importSourceWindow.selectedPreviewPaths = []
            importSourceWindow.scanning = false
        }
        function onSourceScanFailed(message) {
            importSourceWindow.lastError = message
            importSourceWindow.scanning = false
        }
        function onSelectionChanged(items) {
            importSourceWindow.previewItems = items
            if (importSourceWindow.selectedPreviewIndex >= items.length)
                importSourceWindow.selectedPreviewIndex = Math.max(0, items.length - 1)
        }
        function onImportStarted(total) {
            importSourceWindow.importing = true
            importSourceWindow.importDone = 0
            importSourceWindow.importTotal = total
            importSourceWindow.importBytesPerSecond = 0
        }
        function onImportProgress(done, total) {
            importSourceWindow.importDone = done
            importSourceWindow.importTotal = total
        }
        function onImportSpeed(bytesPerSecond) {
            importSourceWindow.importBytesPerSecond = bytesPerSecond
        }
        function onImportFailedDetails(details) {
            importSourceWindow.lastError = details.join("\n")
        }
        function onImportFinished(copied, failed) {
            importSourceWindow.importing = false
            importSourceWindow.pendingSelectedOnly = false
            importSourceWindow.lastCopiedCount = copied
            importSourceWindow.lastFailedCount = failed
            if (importSourceWindow.closeAfterImport) {
                importSourceWindow.closeAfterImport = false
                if (copied > 0 && failed === 0) {
                    importSourceWindow.closePanel()
                    importSourceWindow.hostWindow.kilepes()
                } else {
                    importSourceWindow.closeAfterNextImport = false
                }
            }
        }
    }

    Shortcut {
        objectName: "importSourceReturnShortcut"
        sequence: "Return"
        context: Qt.WindowShortcut
        enabled: importSourceWindow.visible
        onActivated: importSourceWindow.activateDefaultImport()
    }
    Shortcut {
        objectName: "importSourceEnterShortcut"
        sequence: "Enter"
        context: Qt.WindowShortcut
        enabled: importSourceWindow.visible
        onActivated: importSourceWindow.activateDefaultImport()
    }
    Shortcut {
        objectName: "importSourceEscapeShortcut"
        sequence: "Escape"
        context: Qt.WindowShortcut
        enabled: importSourceWindow.visible
        onActivated: importSourceWindow.closePanel()
    }

    ColumnLayout {
        id: importSourceContent
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        ImportSourcePickerPanel {
            id: sourcePanel
            hostWindow: importSourceWindow
            sourceFolderDialog: sourceFolderDialog
            sourceFilesDialog: sourceFilesDialog
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 8

            // A kijelölt kép a panel megmaradó, nyújtott részét kapja; a
            // bélyegképrács mellette önállóan görgethető marad.
            ImportSourcePreview {
                id: previewPanel
                hostWindow: importSourceWindow
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
            // A célbeállítás belső soraiban több rögzített szélességű
            // választó van. A sima Item ad neki külön sávot, így a belső
            // ColumnLayout nem nyújtózik rá a teljes sorra.
            Item {
                Layout.minimumWidth: 530
                Layout.preferredWidth: 530
                Layout.maximumWidth: 530
                Layout.fillHeight: true

                ImportSourceDestinationPanel {
                    anchors.fill: parent
                    hostWindow: importSourceWindow
                    folderDialog: destFolderDialog
                }
            }
        }
    }

    FolderDialog {
        id: sourceFolderDialog
        objectName: "importSourceFolderDialog"
        title: qsTr("Choose source folder...")
        onAccepted: importSourceWindow.useSourceFolder(
            selectedFolder.toString(), false)
    }

    // #4596: kijelölt fájlok a forrás. A szűrők az eredeti tallózóéi
    // („Picture and Movie Files” / „Picture Files” / „All Files”).
    FileDialog {
        id: sourceFilesDialog
        objectName: "importSourceFilesDialog"
        title: qsTr("Import Files/Folder")
        fileMode: FileDialog.OpenFiles
        // az eredeti három szűrője (picsmovfilter / picsfilter /
        // allfilesfilter); a kiterjesztések az AddFileDialog (#2929) és a
        // `scanner/filetypes.py` halmaza, a RAW is a „kép” része, mint a
        // beolvasás `_FILTER_KINDS`-ében
        readonly property string pictureGlobs:
            "*.bmp *.gif *.jpe *.jpeg *.jpg *.png *.psd *.tga *.tif "
            + "*.tiff *.webp "
            + "*.3fr *.arw *.cr2 *.crw *.dcr *.dng *.kdc *.mrw "
            + "*.nef *.nrw *.orf *.pef *.raf *.raw *.rw2 *.sr2 *.srf *.x3f"
        readonly property string movieGlobs:
            "*.3g2 *.3gp *.asf *.avi *.divx *.m2t *.m2ts *.m2v *.m4v "
            + "*.mkv *.mmv *.mod *.mov *.mp4 *.mpeg *.mpg *.mts *.ogg "
            + "*.ogv *.tod *.tp *.ts *.ty *.wmv"
        nameFilters: [
            qsTr("Picture and Movie Files")
                + " (" + pictureGlobs + " " + movieGlobs + ")",
            qsTr("Picture Files") + " (" + pictureGlobs + ")",
            qsTr("All Files") + " (*)"
        ]
        onAccepted: importSourceWindow.useSelectedFiles(
            selectedFiles.length > 0 ? selectedFiles
            : (selectedFile.toString().length > 0 ? [selectedFile] : []))
    }

    FolderDialog {
        id: destFolderDialog
        title: qsTr("Choose destination folder...")
        currentFolder: typeof importSourceController !== "undefined"
            && importSourceController
            && importSourceController.defaultDestinationUrl !== undefined
                ? importSourceController.defaultDestinationUrl
                : Qt.resolvedUrl(".")
        onAccepted: importSourceWindow.destFolder = selectedFolder.toString()
    }

    // Az egyetlen törlés-megerősítés (#7173). Az eredeti ablakban nincs
    // „Do not ask again” jelölő és nincs „No” gomb, csak az igen-gomb és a
    // Cancel; az üres kulcs miatt a kérdés soha nem nyomható el.
    ConfirmDialog {
        id: removeConfirm
        namePrefix: "importSourceConfirmRemove"
        title: qsTr("Import from Source")
        rememberVisible: false
        noVisible: false
        yesText: importSourceWindow.effectiveAfterCopying === "delete_all"
            ? qsTr("Remove All Files") : qsTr("Remove Imported Files")
        onCanceled: importSourceWindow.closeAfterNextImport = false
        onConfirmed: importSourceWindow.runImportNow()
    }
}
