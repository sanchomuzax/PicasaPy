import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Import forrásból (#23/#441): külső mappa (pl. fényképezőgép/kártya
// csatolt mappája, vagy bármely más mappa) képeinek/videóinak másolása a
// könyvtárba — a Mappakezelő/DedupDialog mintájára ÖNÁLLÓ, mozgatható/
// átméretezhető ablak (nem a főablakba ékelt Dialog).
//
// #441 — a mai szabad szöveges mappa-sablon mező helyett HÁROM célmappa-
// elnevezési mód (namingMode: "manual" | "date" | "today"), duplikátum-
// kizárás (autoExclude, a jelölt-előnézetben "duplicate"/"excluded"
// zászlókkal), egyenkénti válogatás, és háromállapotú, kétlépcsős
// megerősítésű forrás-törlés ("After Copying:").
Window {
    id: importSourceWindow
    objectName: "importSourceDialog"
    title: qsTr("Import from Source")
    modality: Qt.ApplicationModal

    //: #3544: a Shift+F1 fejezete. Külön ablakos, modális párbeszéd: a
    //: főablak súgója mögé kerülne, ezért a `WindowHelp` a párbeszéd FÖLÖTT,
    //: külön ablakban nyitja.
    property string helpTopic: "features/importalas.md"
    WindowHelp { tema: importSourceWindow.helpTopic }
    width: 640
    height: 680
    minimumWidth: 480
    minimumHeight: 480
    color: Theme.canvasBg
    //: #3575: a külön `Window` NEM örökli a főablak `palette`-jét — enélkül
    //: a célmappa-módok rádiófeliratai olvashatatlanok (mint a #3593-ban).
    palette {
        window: Theme.canvasBg
        active.windowText: Theme.ink
        inactive.windowText: Theme.ink
        base: Theme.controlBase
        alternateBase: Theme.panelBg
        active.text: Theme.ink
        inactive.text: Theme.ink
        button: Theme.buttonBg
        active.buttonText: Theme.ink
        inactive.buttonText: Theme.ink
        highlight: Theme.selectionBlue
        highlightedText: Theme.panelSelectionText
        placeholderText: Theme.placeholderText
        mid: Theme.chromeBorder
        light: Theme.shadeLight
        dark: Theme.shadeDark
        // #5874: ez az önálló ablak saját palettát használ; az aktív/inaktív
        // tinták nem írják felül a disabled csoportot.
        disabled.windowText: Theme.textGray
        disabled.text: Theme.textGray
        disabled.buttonText: Theme.textGray
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
    // NAMING_*` konstansaival egyező string. A dátum szerinti bontás a
    // Picasa import-munkafolyamatának lelke, ezért ez az alapértelmezés.
    property string namingMode: "date"
    property string manualFolderName: ""
    // #4837: a kézi név egyetlen, biztonságos útvonal-elem-e (Python dönt)
    readonly property bool manualNameValid:
        manualFolderName.trim().length > 0
        && (!importSourceController
            || importSourceController.isValidFolderName === undefined
            || importSourceController.isValidFolderName(manualFolderName))

    // #441: "After Copying:" — a `picasapy.app.import_source_controller.
    // AFTER_COPY_*` konstansaival egyező string.
    property string afterCopying: "leave"

    property bool scanning: false
    // előnézeti elemek — dict-ek listája: {path, thumbUrl, duplicate,
    // excluded, rotation, starred}; a controller MINDIG listát ad (ld.
    // MEMORY.md-tanulság)
    property var previewItems: []
    property int previewCount: 0
    // Az eredeti previous/next gombok az előnézeti képet léptetik. A
    // bélyegkép-rács megmarad; a kijelölt kép kiemelése és görgetése követi.
    property int selectedPreviewIndex: 0
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

    property bool importing: false
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

    onVisibleChanged: {
        if (visible
                && typeof importSourceController !== "undefined"
                && importSourceController
                && importSourceController.refreshMountedSources !== undefined)
            importSourceController.refreshMountedSources()
    }

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
        importSourceWindow.visible = true
    }

    function stepPreview(delta) {
        var nextIndex = importSourceWindow.selectedPreviewIndex + delta
        if (nextIndex < 0 || nextIndex >= importSourceWindow.previewItems.length)
            return
        importSourceWindow.selectedPreviewIndex = nextIndex
        previewPanel.positionAt(nextIndex)
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
        importSourceWindow.sourceFiles = fileUrls.map(function (url) {
            return url.toString()
        })
        importSourceWindow.scanCurrentSource()
    }

    // #441: a másolás tényleges indítása — a kétlépcsős megerősítés (ld.
    // lent, `requestImport`) UTÁN hívódik.
    function runImportNow() {
        importSourceWindow.lastError = ""
        importSourceController.runImport(
            importSourceWindow.destFolder,
            importSourceWindow.namingMode,
            importSourceWindow.manualFolderName,
            importSourceWindow.afterCopying)
    }

    // #441: "After Copying:" — kétlépcsős, egyre erősebb megerősítés a
    // törléssel járó két állapotnál; "Leave card alone"-nál nincs kérdés.
    function requestImport() {
        if (importSourceWindow.destFolder.length === 0) return
        if (importSourceWindow.includedCount === 0) return
        // #4595: kézi módban cím nélkül nincs import (és nincs megerősítés sem)
        if (importSourceWindow.namingMode === "manual"
                && !importSourceWindow.manualNameValid) return
        if (importSourceWindow.afterCopying === "leave") {
            importSourceWindow.runImportNow()
            return
        }
        removeImportedConfirm.ask("importSourceRemoveImported", qsTr(
            // #465 4. pont: az eredeti Picasa NAGYBETŰVEL írja — ez a
            // legsúlyosabb adatvesztési pont az egész programban
            "Are you sure you want to remove the imported files from your "
            + "card? THIS CANNOT BE UNDONE."))
    }

    Connections {
        target: typeof importSourceController !== "undefined"
                ? importSourceController : null
        function onSourceScanFinished(items, count) {
            importSourceWindow.previewItems = items
            importSourceWindow.previewCount = count
            importSourceWindow.selectedPreviewIndex = 0
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
            importSourceWindow.lastCopiedCount = copied
            importSourceWindow.lastFailedCount = failed
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        ImportSourceDialogSourcePanel {
            id: sourcePanel
            hostWindow: importSourceWindow
            sourceFolderDialog: sourceFolderDialog
            sourceFilesDialog: sourceFilesDialog
        }
        ImportSourceDialogPreview {
            id: previewPanel
            hostWindow: importSourceWindow
        }
        ImportSourceDialogDestinationPanel {
            hostWindow: importSourceWindow
            folderDialog: destFolderDialog
        }
    }

    FolderDialog {
        id: sourceFolderDialog
        objectName: "importSourceFolderDialog"
        title: qsTr("Choose source folder...")
        onAccepted: {
            importSourceWindow.sourceFiles = []
            importSourceWindow.sourceFolder = selectedFolder.toString()
            importSourceWindow.scanCurrentSource()
        }
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

    // #441 — kétlépcsős, egyre erősebb megerősítés a forrás-törléshez.
    // 1. lépés: mindkét törléssel járó "After Copying:" állapotra közös,
    // generikus kérdés. "delete_all"-nál ezt követi a 2. lépés (erősebb
    // figyelmeztetés + "ne figyelmeztess többé"), "delete_copied"-nél a
    // 2. lépés kimarad — a #422 mintája szerint EGYEDI namePrefix.
    ConfirmDialog {
        id: removeImportedConfirm
        namePrefix: "importSourceRemoveImportedConfirm"
        title: qsTr("Import from Source")
        onConfirmed: {
            if (importSourceWindow.afterCopying === "delete_all") {
                //: #860: az ÖSSZEÁLLÍTOTT figyelmeztetés a vezérlőtől jön
                //: (`wipe_card_warning`) — darabszámokkal, a nem felismert
                //: fájlokkal és a záró „A MŰVELET NEM VONHATÓ VISSZA."
                //: mondattal. Korábban egy három pontra rövidített mondat
                //: állt itt, ami épp a lényeget hallgatta el.
                deleteAllWarningConfirm.ask(
                    "importSourceDeleteAllWarning",
                    importSourceController.wipeCardWarning())
            } else {
                importSourceWindow.runImportNow()
            }
        }
    }

    ConfirmDialog {
        id: deleteAllWarningConfirm
        namePrefix: "importSourceDeleteAllWarningConfirm"
        title: qsTr("Import from Source")
        onConfirmed: importSourceWindow.runImportNow()
    }
}
