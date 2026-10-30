pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PicasaPy

// A folegység mentési, fájlműveleti, export- és létrehozási párbeszédei.
Item {
    id: dialogStack
    objectName: "mainWindowDialogStack"
    required property var hostWindow
    required property var hostPhotoViewer
    required property var hostDocumentTabStrip
    required property var hostUnnamedFaceRefreshTimer

    property alias exportSaveDialogs: saveDialogs
    property alias exportCollageDraftDialog: collageDraftDialog
    property alias exportHiddenPasswordOfferDialog: hiddenPasswordOfferDialog
    property alias exportCollectionPasswordDialog: collectionPasswordDialog
    property alias exportInitialScanDialog: initialScanDialog
    property alias exportMoveToNewPersonDialog: moveToNewPersonDialog
    property alias exportRemovePeopleFacesDialog: removePeopleFacesDialog
    property alias exportRemoveFromAlbumDialog: removeFromAlbumDialog
    property alias exportBrokenPhotoBatchTimer: brokenPhotoBatchTimer
    property alias exportBrokenPhotoDialog: brokenPhotoDialog
    property alias exportXmpFacesWriteDialog: xmpFacesWriteDialog
    property alias exportActivityCancelConfirm: activityCancelConfirm
    property alias exportFileOpsDialogs: fileOpsDialogs
    property alias exportExportDialogs: exportDialogs
    property alias exportCreateDialogs: createDialogs
    property alias exportHelpDialog: helpDialog
    property alias exportConfigureButtonsDialog: configureButtonsDialog
    property alias exportAboutDialog: aboutDialog
    property alias exportOptionsDialog: optionsDialog
    property alias exportWebExportDialog: webExportDialog
    property alias exportPrintDialog: printDialog
    property alias exportMoveDatabaseDialog: moveDatabaseDialog
    property alias exportCompactDatabaseDialog: compactDatabaseDialog
    property alias exportPicasaDataImportDialog: picasaDataImportDialog

    // #444: Mentés / Visszaállítás / Utolsó mentés visszavonása
    // #1720: halasztott példányosítás — a párbeszéd csak az első
    // megnyitáskor épül fel (ld. `DeferredDialog.qml`).
    DeferredDialog {
        id: saveDialogs
        // ⚠️ Az `objectName` a BECSOMAGOLT párbeszédé marad, nem a
        // `Loader`-é: a `findChild(objectName)` így a megnyitás után a
        // VALÓDI komponenst adja vissza, nem a burkot.
        objectName: "saveDialogsLoader"
        anchors.fill: parent
        sourceComponent: Component {
            SaveDialogs { objectName: "saveDialogs"; appWindow: hostWindow }
        }
    }

    // átnevezés / áthelyezés / törlés / hiba (FileOpsDialogs.qml, #150)
    //: #1612: halasztva — a fájlművelet-párbeszédek 571 QObjectet építettek
    //: fel MINDEN induláskor, holott a legtöbb indulásnál egyet sem nyit meg
    //: a felhasználó. A vezérlő jelzéseit a lenti, MINDIG álló `Connections`
    //: fogadja, nem a komponens belseje (#1743, #2096).
    DeferredDialog {
        id: fileOpsDialogs
        objectName: "fileOpsDialogs"
        anchors.fill: parent
        sourceComponent: Component {
            //: a BELSŐ példány saját neve — a burok (`fileOpsDialogs`) a
            //: `Loader`, a párbeszédeket tartó `Item` ez. A tesztek az
            //: `ensure()` után ezen a néven érik el a nyilvános belépőket.
            FileOpsDialogs {
                objectName: "fileOpsDialogsItem"
                appWindow: hostWindow
            }
        }
    }

    //: #1612: a fájlművelet-vezérlő hallgatói. Azért ITT állnak és nem a
    //: komponensben, mert az halasztott: a `fileOpsController` jelzései nem
    //: csak a saját párbeszédeiből indulhatnak — a mappafa
    //: áthelyezés/törlés útja (`FolderPane.qml`) is ezen jelez. Az
    //: `ensure()` mindhárom ágon KÖTELEZŐ: mind a három a FELHASZNÁLÓNAK
    //: szól, tehát némán elmaradnia nem szabad.
    Connections {
        target: fileOpsController
        function onBatchProgress(operation, destination, done, total, speed) {
            fileOpsDialogs.ensure().reportBatch(
                operation, destination, done, total, speed)
        }
        function onBatchFinished(operation, done, skipped, failed, reason) {
            fileOpsDialogs.ensure().finishBatch(
                operation, done, skipped, failed, reason)
        }
        function onOperationFailed(operation, message) {
            fileOpsDialogs.ensure().showOperationError(operation, message)
        }
    }

    // exportálás mappába (#16, Ctrl+Shift+S; ExportDialogs.qml, #150)
    // #1720: halasztott példányosítás — a párbeszéd csak az első
    // megnyitáskor épül fel (ld. `DeferredDialog.qml`).
    DeferredDialog {
        id: exportDialogs
        anchors.fill: parent
        sourceComponent: Component {
            ExportDialogs { appWindow: hostWindow }
        }
    }

    // #1743: A HALLGATÓK MINDIG ÁLLNAK, a párbeszéd nem.
    //
    // A #1720 óta a mentés- és export-párbeszéd halasztott: csak az első
    // megnyitáskor épül fel. A vezérlő eredmény- és hibajelzéseit viszont
    // EDDIG a párbeszéden BELÜLI `Connections` fogadta — ami addig nem is
    // létezett. Amíg minden belépő az `ensure()`-ön át megy, ez nem okoz
    // bajt; egy ÚJ belépő (gyorsbillentyű, tálcagomb, kötegelt művelet)
    // viszont némán elnyelné a hibaüzenetet, és semmilyen teszt nem bukna
    // el rá.
    //
    // Ezért a hallgató ide került, a mindig felépülő ablakba: pár objektum,
    // a #1720 nyeresége érintetlen. Az `ensure()` a jelzés pillanatában
    // építi fel a párbeszédet — pontosan akkor, amikor tényleg kell.
    Connections {
        target: controller
        function onDiskOperationSucceededPaths(paths) {
            hostPhotoViewer.frissitsdALemezműveletUtániElőnézetet(paths)
        }
        function onSaveFailedDetails(details) {
            saveDialogs.ensure().jelezdAbukottMentest(details)
        }
        function onSaveErrorOccurred(kind, fileName, code) {
            saveDialogs.ensure().jelezdAmentesiHibat(kind, fileName, code)
        }
        function onRevertErrorOccurred() {
            saveDialogs.ensure().jelezdAVisszaallitasiHibat()
        }
        function onExportFailedDetails(details) {
            exportDialogs.ensure().jegyezdAbukottFajlokat(details)
        }
        function onExportFinished(done, failed) {
            exportDialogs.ensure().jelezdAzExportVeget(done, failed)
        }
        function onEarthExportFinished(kmlPath, placemarks, skipped) {
            exportDialogs.ensure().jelezdAzEarthExportVeget(
                kmlPath, placemarks, skipped)
        }
        function onEarthViewReady(kmlPath, placemarks, skipped) {
            exportDialogs.ensure().nyisdMegAzEarthFajlt(
                kmlPath, placemarks, skipped)
        }
    }

    // kollázs és mozgófilm a kijelölésből (#29; CreateDialogs.qml)
    //: #1612/#2096: halasztva — a Létrehozás-párbeszédek csak a menüből vagy
    //: a tálcáról nyílnak. A vezérlő jelzéseit a lenti, MINDIG álló
    //: `Connections` fogadja, nem a komponens belseje (#1743).
    DeferredDialog {
        id: createDialogs
        objectName: "createDialogs"
        // A belső Dialogok ehhez a felülethez igazodnak; méret nélkül a Loader 0×0 marad.
        anchors.fill: parent
        sourceComponent: Component {
            CreateDialogs { appWindow: hostWindow }
        }
    }

    // #2096: a Létrehozás-párbeszédek vezérlő-hallgatói. Azért ITT állnak és
    // nem a komponensben, mert az halasztott: amíg a felhasználó meg nem
    // nyitotta, egy belső `Connections` nem létezne, és a kollázs/film
    // visszajelzése NÉMÁN elmaradna. A kollázs a Kollázs panelről is
    // indítható, tehát ez nem elméleti eset.
    Connections {
        target: controller
        function onCollagePreviewReady(revision) {
            // ⚠️ Itt SZÁNDÉKOSAN nincs `ensure()`. Az élő előnézet csak a
            // NYITOTT kollázs-párbeszédnek szól: ha a párbeszéd nem áll, nincs
            // mit frissíteni, és felépíteni is fölösleges volna. A többi
            // jelzés (eredmény, hiba) viszont a felhasználónak szól, ott az
            // `ensure()` KÖTELEZŐ — különben némán elmaradna a visszajelzés.
            if (createDialogs.item)
                createDialogs.item.frissitsdAzElonezetet(revision)
        }
        function onMovieTransitionPreviewReady(source, generation) {
            // Mint a kollázs-előnézet: csak a NYITOTT párbeszédnek szól,
            // felépíteni fölösleges (nincs film-előnézet, ha nem áll).
            if (createDialogs.item)
                createDialogs.item.jelezdAFilmAtmenetElonezetet(source, generation)
        }
        function onCollageFinished(path, used, skipped, missing) {
            createDialogs.ensure().jelezdAKollazsSikert(path, used, skipped, missing)
        }
        function onCollagePreviewFailed(message) {
            // Az előnézet a háttérből a főablak lebontása közben is bukhat;
            // akkor már nincs párbeszéd, amelyben jelezni lehetne.
            const parbeszedek = createDialogs.ensure()
            if (parbeszedek)
                parbeszedek.jelezdAKollazsHibajat(message)
        }
        function onCollageFailed(message) {
            createDialogs.ensure().jelezdAKollazsHibajat(message)
        }
        function onMovieProgress(done, total) {
            createDialogs.ensure().frissitsdAFilmHaladast(done, total)
        }
        function onMovieFinished(path, used, skipped, missing) {
            createDialogs.ensure().jelezdAFilmSikert(path, used, skipped, missing)
        }
        function onMovieFailed(message) {
            createDialogs.ensure().jelezdAFilmHibajat(message)
        }
        function onPosterFinished(paths) {
            createDialogs.ensure().jelezdAPoszterSikert(paths)
        }
        function onPosterFailed(message) {
            createDialogs.ensure().jelezdAPoszterHibajat(message)
        }
    }

    // #2054: a felhasználói súgó — F1. Halasztott, mint a többi:
    // induláskor nem épül fel, csak az első megnyitáskor.
    DeferredDialog {
        id: helpDialog
        anchors.fill: parent
        sourceComponent: Component { HelpDialog { objectName: "helpDialog" } }
    }

    //: #1792: a fejlec gombsoranak testreszabasa — halasztott toltes, a
    //: tobbi parbeszed mintajara (a nev a BECSOMAGOLT parbeszede)
    DeferredDialog {
        id: configureButtonsDialog
        anchors.fill: parent
        sourceComponent: Component {
            ConfigureButtonsDialog { objectName: "configureButtonsDialog" }
        }
    }

    DeferredDialog {
        id: aboutDialog
        anchors.fill: parent
        // az `objectName` a BECSOMAGOLT párbeszédé — enélkül a #1720
        // őre üres halmazt vizsgálna, azaz némán mindig zöld lenne
        sourceComponent: Component { AboutDialog { objectName: "aboutDialog" } }
    }

    // #350: Beállítások-dialógus (options.fen)
    DeferredDialog {
        id: optionsDialog
        anchors.fill: parent
        sourceComponent: Component { OptionsDialog { } }
    }

    // #351: webexport-dialógus (.tpl sablonmotor)
    DeferredDialog {
        id: webExportDialog
        anchors.fill: parent
        sourceComponent: Component { WebExportDialog { } }
    }

    // #1472: nyomtatás-párbeszéd (nyomtató-választó + PDF-fájlba nyomtatás)
    DeferredDialog {
        id: printDialog
        anchors.fill: parent
        sourceComponent: Component { PrintDialog { } }
    }

    // #368: adatbázis-áthelyezés dialógus (relocateController hídon)
    DeferredDialog {
        id: moveDatabaseDialog
        anchors.fill: parent
        sourceComponent: Component { MoveDatabaseDialog { } }
    }
    // #644: figyelmeztetés, ha egy másik program felülírta a szerkesztéseinket
    DeferredDialog {
        id: editOverwriteDialog
        anchors.fill: parent
        sourceComponent: Component { EditOverwriteDialog { } }
    }
    Connections {
        target: controller
        function onEditsOverwritten(lost) { editOverwriteDialog.ensure().show(lost) }
    }
    DeferredDialog {
        id: compactDatabaseDialog
        anchors.fill: parent
        sourceComponent: Component { CompactDatabaseDialog { } }
    }
    // #1401: az Útlevélkép hibaablaka — a főablak tartalmában, tehát
    // fölötte látszik. Egy arcnál párbeszéd nélkül a MEGLÉVŐ nyomtatási
    // nézet nyílik (élő mérés, picasa-colab-jobs #54).
    DeferredDialog {
        id: passportErrorDialog
        anchors.fill: parent
        sourceComponent: Component { PassportErrorDialog { } }
    }
    Connections {
        target: typeof passportController !== "undefined" ? passportController : null
        function onPassportNoFace() {
            passportErrorDialog.ensure().showError("noFace")
        }
        function onPassportMultipleFaces() {
            passportErrorDialog.ensure().showError("multipleFaces")
        }
        function onPassportFailed(kind) {
            passportErrorDialog.ensure().showError(kind)
        }
        function onPassportReady(url) {
            printDialog.ensure().openForPassport(url)
        }
    }
    // #3132: a db3-import párbeszéde — ritkán nyitott, ezért halasztott
    DeferredDialog {
        id: picasaDataImportDialog
        anchors.fill: parent
        sourceComponent: Component { PicasaDataImportDialog { } }
    }


    //: #2966: a megszakítás megerősítése. Az eredeti címsora „Want to
    //: Cancel?" volt — azt NEM vesszük át, a miénk a műveletről szól.
    //: #1719/#1720: halasztott példányosítás — a párbeszéd csak az első
    //: megszakítás-kattintáskor épül fel.
    DeferredDialog {
        id: activityCancelConfirm
        objectName: "activityCancelConfirmLoader"
        anchors.fill: parent
        function ask() {
            //: a `decisionKey` SZÁNDÉKOSAN üres: a futó munka leállítását
            //: nem lehet „ne kérdezze újra"-val elnyomni
            //: `IBackgroundNotify::cancel` — az eredeti szövege (#3573)
            ensure().ask("", qsTr(
                "Do you want to cancel this operation?"))
        }
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "activityCancelConfirm"
                namePrefix: "activityCancel"
                //: `IBackgroundNotify::canceltitle` — az eredeti szövege (#3573)
                title: qsTr("Want to Cancel?")
                onConfirmed: controller.cancelActivity()
            }
        }
    }


    //: #4634: halasztott (#1720) — csak az Eszközök menüpontra épül fel.
    DeferredDialog {
        id: xmpFacesWriteDialog
        objectName: "xmpFacesWriteDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            XmpFacesWriteDialog {
                onWriteRequested: function (scope, rows) {
                    if (controller) controller.writeFacesToXmp(scope, rows)
                }
            }
        }
    }


    //: #1403: az arc elnevezése után AUTOMATIKUS XMP-írás hibája. A jelzés a
    //: `faceScanController`-é (nem a `facesHelper`-é), és az eredetiben is
    //: megnevezett hibaeset (csak olvasható fájl) — a névadás maga sikeres
    //: volt, csak az XMP nem, ezért nem nyeljük el.
    Connections {
        target: typeof faceScanController !== "undefined" ? faceScanController : null
        function onUnnamedCountChanged() { hostWindow.peopleFaceRevision++ }
        // #4586: a keresés közben is frissül a panel névtelen-arc listája —
        // összevonva, és csak nyitott panel mellett
        function onFacesStored() {
            if (hostWindow.peoplePanelOpen || hostPhotoViewer.peopleOpen)
                { if (!hostUnnamedFaceRefreshTimer.running) hostUnnamedFaceRefreshTimer.start() }
        }
        function onFaceSuggestionsChanged() { hostWindow._javaslatFrissult() }
        function onXmpAutoWriteFailed(reason) {
            hostWindow.errorBanner.notice = false
            hostWindow.errorBannerText.text = qsTr("Face data could not be written to XMP: %1").arg(reason)
        }
    }

    Connections {
        target: typeof facesHelper !== "undefined" ? facesHelper : null
        function onFaceWriteFailed(message) {
            hostWindow.errorBanner.notice = false
            hostWindow.errorBannerText.text = message
        }

    }


    // #459: sérült/betölthetetlen kép — ELREJTÉS felajánlása (nem törlés),
    // a felhasználó döntésével. A "Hide Files" a MEGLÉVŐ elrejtés-úton fut
    // (`controller.hidePhotosByIds` → `_apply_batch`, a `toggleHiddenRows`
    // mintája, `photo_ops_controller.py`) — itt NEM íródott újra.
    //: #1612: halasztva — a sérült kép elrejtés-felajánlása csak akkor kell, ha tényleg akad ilyen kép
    DeferredDialog {
        id: brokenPhotoDialog
        //: a BUROK neve — a #1612 őre ezen hívja az `ensure()`-t, és
        //: ezzel bizonyítja, hogy induláskor tényleg nincs példány
        objectName: "brokenPhotoDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                //: a BELSŐ példány saját neve: a `brokenPhotoDialog` a
                //: halasztó `Loader`, tehát a saját mezőire innen NEM azon
                //: a néven kell hivatkozni (az `ensure()` visszatérése ez az
                //: objektum)
                id: brokenPhotoBelso
                namePrefix: "brokenPhoto"
                yesText: qsTr("Hide Files")
                noText: qsTr("Don't Hide")
                property var pendingIds: []
                //: #3573: a nevek az üzenet fájllistájához (a `pendingIds`
                //: párja, ugyanabban a sorrendben)
                property var pendingNames: []
                onConfirmed: {
                    controller.hidePhotosByIds(brokenPhotoBelso.pendingIds)
                    brokenPhotoBelso.pendingIds = []
                    brokenPhotoBelso.pendingNames = []
                }
                onDenied: {
                    brokenPhotoBelso.pendingIds = []
                    brokenPhotoBelso.pendingNames = []
                }
            }
        }
    }


    Timer {
        id: brokenPhotoBatchTimer
        interval: 400
        onTriggered: {
            if (brokenPhotoDialog.ensure().pendingIds.length > 0) {
                // #3573: az eredeti KÉT erőforrásból rakja össze az
                // üzenetet, és a kettő közé soronként a hibás fájlok nevét
                // szúrja be (`GetBadImages` + lista + `GetBadImages2`)
                var dialog = brokenPhotoDialog.ensure()
                dialog.ask("",
                    //: `CThumbUI::GetBadImages` — utána a fájllista jön
                    qsTr("PicasaPy had a problem loading this file(s)\n")
                    + dialog.pendingNames.join("\n")
                    //: `CThumbUI::GetBadImages2`
                    + qsTr("\nWould you like to hide the files on disk?"))
            }
        }
    }


    // #3539: „Eltávolítás az albumból" — a kijelölt képek albumtagságát
    // veszi le, megerősítéssel (a "Remove from album without confirmation"
    // beállítással elnyomható, a #367 törlés-elnyomás mintája szerint).
    //: #1612: halasztva — a megerősítés csak a menüpontból/billentyűből nyílik
    DeferredDialog {
        id: removeFromAlbumDialog
        objectName: "removeFromAlbumDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "removeFromAlbumDialog"
                namePrefix: "removeFromAlbum"
                //: DeleteMessage::RemoveItemsTitle (spec picasa-fen-dialogs.md 3.3.1)
                title: qsTr("Remove Items")
                property var rows: []
                property string token: ""
                function openFor(rowList, albumToken) {
                    if (rowList.length === 0 || albumToken.length === 0) return
                    rows = rowList
                    token = albumToken
                    if (rowList.length <= 1) {
                        //: DeleteMessage::RemoveSingleYesButton
                        yesText = qsTr("Remove Image")
                        //: DeleteMessage::RemoveSingle
                        ask("removeFromAlbum", qsTr(
                            "Are you sure you want to remove the selected "
                            + "image from the current album?"))
                    } else {
                        //: DeleteMessage::RemoveMultipleYesButton
                        yesText = qsTr("Remove Images")
                        //: DeleteMessage::RemoveMultiple
                        ask("removeFromAlbum", qsTr(
                            "Are you sure you want to remove the %n selected "
                            + "images from the current album?", "",
                            rowList.length))
                    }
                }
                onConfirmed: controller.removeRowsFromAlbum(rows, token)
            }
        }
    }


    // #422: „Eltávolítás az Emberek albumból" — a kijelölt képekről leveszi
    // az ADOTT személy arc-címkéjét (a régió is eltűnik: a Picasa is az
    // arcot veszi le, nem csak a nevet). Megerősítéssel: a névcímke
    // visszaállítása csak újbóli felismeréssel/kézi felvétellel lehetséges.
    // #3539: a cím és a szöveg a `DeleteMessage::` család szerint (spec
    // 3.3.1) — a korábbi saját "arc-címke" szöveg helyett.
    //: #1612: halasztva — az arcok eltávolításának megerősítése csak a menüpontból nyílik
    DeferredDialog {
        id: removePeopleFacesDialog
        //: a BUROK neve — a #1612 őre ezen hívja az `ensure()`-t, és
        //: ezzel bizonyítja, hogy induláskor tényleg nincs példány
        objectName: "removePeopleFacesDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "removePeopleFacesDialog"
                namePrefix: "removePeopleFaces"
                //: DeleteMessage::UnknownPeopleTitle (a fajta=2 ágon, tárolón kívül)
                title: qsTr("Remove People")
                property var rows: []
                property string person: ""
                function openFor(rowList, name) {
                    if (rowList.length === 0 || name.length === 0) return
                    rows = rowList
                    person = name
                    if (rowList.length <= 1) {
                        //: DeleteMessage::RemoveSingleYesButtonPeople
                        yesText = qsTr("Remove Person")
                        //: DeleteMessage::RemoveSinglePeople
                        ask("removePeopleFaces", qsTr(
                            "Are you sure you want to remove the selected "
                            + "person from the current album?"))
                    } else {
                        //: DeleteMessage::RemoveMultipleYesButtonPeople
                        yesText = qsTr("Remove People")
                        //: DeleteMessage::RemoveMultiplePeople
                        ask("removePeopleFaces", qsTr(
                            "Are you sure you want to remove the %n selected "
                            + "people from the current album?", "",
                            rowList.length))
                    }
                }
                onConfirmed: controller.removePersonFromRows(rows, person)
            }
        }
    }


    // #422: „Áthelyezés új személyhez…" — az adott személy arc-címkéje a
    // kijelölt képeken ÁTKERÜL egy másik névre (a régió marad).
    //: #1612: halasztva — az „Áthelyezés új személyhez" csak az arcpanel
    //: helyi menüjéből nyílik. Az `objectName` a BELSŐ párbeszédre marad,
    //: hogy a felépülés után ugyanúgy megtalálható legyen.
    DeferredDialog {
        id: moveToNewPersonDialog
        sourceComponent: Component {
            NameInputDialog {
                objectName: "moveToNewPersonDialog"
                title: qsTr("Move to New Person")
                prompt: qsTr("New person's name:")
                property var rows: []
                property string person: ""
                function openFor(rowList, name) {
                    if (rowList.length === 0 || name.length === 0) return
                    rows = rowList
                    person = name
                    openEmpty()
                }
                onAccepted: controller.movePersonOnRows(rows, person, enteredName)
            }
        }
    }


    // #449: első indítás — a kérdés az ablak megjelenése UTÁN jön elő, hogy
    // a felhasználó lássa, mibe kerül bele
    InitialScanDialog {
        id: initialScanDialog
        objectName: "initialScanDialog"
        // #1167: a migrációs „frissítés" ág a meglévő Picasa-átvételt
        // nyitja (#146) — a felderítést a PicasaImportDialog végzi újra
        onImportRequested: {
            if (typeof discoveryController !== "undefined" && discoveryController)
                discoveryController.openImportDialog()
        }
    }


    // #5704: ugyanaz a jelszókezelő szolgálja ki a felhasználói és a
    // beépített Rejtett mappák gyűjteményt. Hibás jelszónál a párbeszéd
    // nyitva marad, így a felhasználó azonnal újrapróbálhatja.
    DeferredDialog {
        id: collectionPasswordDialog
        anchors.fill: parent
        sourceComponent: Component {
            CollectionPasswordDialog {
                controller: hostWindow.appController
            }
        }
    }


    // #5704 (spec #5700): ajánlat a Rejtett mappák védelmére elrejtés után.
    DeferredDialog {
        id: hiddenPasswordOfferDialog
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                namePrefix: "hiddenPasswordOffer"
                title: qsTr("Add Password")
                message: qsTr("The \"Hidden Folders\" collection is not currently password protected.\nWould you like to add a password now?")
                yesText: qsTr("Add Password")
                noText: qsTr("Don't Add Password")
                rememberText: qsTr("Do not ask me again.")
                rememberOnDenied: true
                cancelVisible: false
                focusYesOnOpen: true
                onConfirmed:
                    collectionPasswordDialog.ensure().openForHiddenCollection()
            }
        }
    }

    Connections {
        target: controller
        function onHiddenPasswordOfferRequested() {
            hiddenPasswordOfferDialog.ensure().ask(
                "DoNotConfirmHiddenPwd",
                qsTr("The \"Hidden Folders\" collection is not currently password protected.\nWould you like to add a password now?"))
        }
    }


    // #1051: a kollázs-piszkozat visszaállításának felajánlása. A LAPRA
    // váltás a gazdáé — a párbeszéd csak jelez, ahogy a `CollagePanel` is.

    CollageDraftDialog {
        id: collageDraftDialog
        onRestored: hostDocumentTabStrip.activateTab(hostWindow.collageTabId)
    }
}
