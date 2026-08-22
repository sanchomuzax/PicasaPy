import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Exportálás mappába (#16, Ctrl+Shift+S; #150-ben kiemelve a Main.qml-ből):
// beállítás-dialógus (célmappa, méret, minőség), mappaválasztó és a
// háttérszálas export végeredmény-dialógusa (controller.exportFinished).
Item {
    id: dialogs
    anchors.fill: parent

    // a főablak (a kijelölt sorok forrása)
    required property var appWindow

    function openForSelection() {
        exportDialog.openForSelection()
    }

    // #530: Google Earth-export — a kijelölt képek közül a GEOCÍMKÉZETTEK
    // kerülnek térképre. A célmappa-választón kívül nincs beállítás: az
    // eredetiben sem volt, a bélyegkép-méretet a buborék szabja meg.
    function openGoogleEarth() {
        if (dialogs.appWindow.selectedIndexes.length === 0) return
        earthTargetDialog.open()
    }

    Dialog {
        id: exportDialog
        objectName: "exportDialog"
        // #350 (export.fen paritás): a FEN forrás címe "Export to Folder" —
        // az app eddigi elnevezési konvencióját (három pont a végén) megtartva
        title: qsTr("Export to Folder...")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property string targetFolder: ""
        // a méret-lista indexei → leghosszabb oldal px-ben (0 = eredeti)
        readonly property var sizeOptions: [0, 2048, 1600, 1024, 800]
        function openForSelection() {
            // #455: tartott képekkel a tálca a forrás — ilyenkor a rácsban
            // nem is kell kijelölésnek lennie
            if (!exportDialog.useTray
                    && dialogs.appWindow.selectedIndexes.length === 0) return
            open()
        }
        // tesztelhetőség: ld. renameDialog.acceptButtonText() megjegyzése
        function acceptButtonText() {
            return standardButton(Dialog.Ok) ? standardButton(Dialog.Ok).text : ""
        }
        // #369 (export.fen paritás): a "Name of exported folder:" mező
        // opcionális — üresen a célmappa változatlanul a browse-szal
        // választott hely (a régi viselkedés), kitöltve alá-mappaként jön
        // létre (az exporter mkdir(parents=True)-ja már ma is kezeli).
        function resolvedTargetFolder() {
            var name = exportFolderNameField.text
            if (name.length === 0) return targetFolder
            var sep = targetFolder.endsWith("/") ? "" : "/"
            return targetFolder + sep + name
        }
        onOpened: {
            // #1166: a hely és a név alapértéke (spec 12.1) — a hely a
            // korábban használt mappa, a név a forrásalbumé. A névmező
            // fókuszban, tartalma kijelölve (`focus="name"`).
            if (exportDialog.targetFolder.length === 0)
                exportDialog.targetFolder = controller.defaultExportLocation()
            exportFolderNameField.text = controller.defaultExportName()
            exportFolderNameField.forceActiveFocus()
            exportFolderNameField.selectAll()
            exportDialog.movieFull = controller.exportMovieFull()
            exportDialog.hasVideo = exportDialog.useTray
                ? true
                : controller.selectionHasVideo(
                      dialogs.appWindow.selectedIndexes)
            standardButton(Dialog.Ok).enabled = Qt.binding(
                function() { return exportDialog.targetFolder.length > 0 })
            // #350 (export.fen paritás): a FEN accept gombjának felirata
            // "Export", nem generikus "OK"
            standardButton(Dialog.Ok).text = qsTr("Export")
        }
        // #369: a lenyíló megjelenített (fordítható) szövege és a
        // resolveExportQuality-nak átadott kulcs szándékosan külön —
        // a logika így nem törik el, ha a szöveg egyszer lefordítódik.
        readonly property var qualityPresetKeys:
            ["automatic", "normal", "maximum", "minimum", "custom"]
        // #455 (3. teendő): ha a KÉPTÁLCÁN van tartott kép, a művelet a
        // TÁLCA tartalmán fut, nem a pillanatnyi kijelölésen — az eredeti
        // Picasa buboréksúgói is végig „a képtálca képeire" hivatkoznak.
        // Üres tálcánál marad a kijelölés (a mai viselkedés).
        // #1166: a tárolt film-mód (`FileExportMovie` megfelelője) és a
        // kijelölés film-tartalma — megnyitáskor frissítjük.
        property bool movieFull: false
        property bool hasVideo: false
        readonly property bool useTray:
            (typeof controller !== "undefined" && controller)
                ? controller.heldCount > 0 : false
        // #1166: az eredeti a MEGLÉVŐ célmappára rákérdez
        // (`CExportPrefsPage::destexists`), és igen esetén az ELŐZŐ albumot
        // törli. A kérdést az elfogadás UTÁN, de az indítás ELŐTT tesszük
        // fel — a válasz dönti el, ürítünk-e.
        function startExport(purgeExisting) {
            controller.setExportMovieFull(exportMovieFull.checked)
            controller.rememberExportLocation(exportDialog.targetFolder)
            var quality = controller.resolveExportQuality(
                qualityPresetKeys[exportQualityPreset.currentIndex],
                exportQuality.value)
            var watermark =
                exportWatermarkCheck.checked ? exportWatermarkField.text : ""
            if (exportDialog.useTray)
                controller.exportHeld(
                    resolvedTargetFolder(),
                    sizeOptions[exportSizeBox.currentIndex], quality,
                    exportAddNumbersCheck.checked, watermark, purgeExisting)
            else
                controller.exportRows(
                    dialogs.appWindow.selectedIndexes, resolvedTargetFolder(),
                    sizeOptions[exportSizeBox.currentIndex], quality,
                    exportAddNumbersCheck.checked, watermark, purgeExisting)
        }
        onAccepted: {
            if (controller.exportTargetExists(resolvedTargetFolder()))
                exportOverwriteDialog.open()
            else
                exportDialog.startExport(false)
        }
        ColumnLayout {
            spacing: 10
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Export location:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                Text {
                    objectName: "exportTargetLabel"
                    Layout.preferredWidth: 240
                    elide: Text.ElideMiddle
                    text: exportDialog.targetFolder.length > 0
                          ? exportDialog.targetFolder
                          : qsTr("(not selected)")
                    font.pixelSize: Theme.fontSize
                    color: Theme.textGray
                }
                PicasaButton {
                    text: qsTr("Browse...")
                    onClicked: exportTargetDialog.open()
                }
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Name of exported folder:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                TextField {
                    id: exportFolderNameField
                    objectName: "exportFolderNameField"
                    Layout.preferredWidth: 180
                    // #1166: az alapértéket a megnyitás tölti ki (a
                    // forrásmappa neve — `0x0073b500`); a mező tartalma
                    // induláskor KI VAN JELÖLVE (`focus="name"`).
                    selectByMouse: true
                    // #422: jobbklikk-menü (Picasa `Address`)
                    TextFieldContextArea {}
                }
            }
            // #1166 (export.fen `radiogroup name="movies"`): a filmek
            // exportálásának módja. A `.fen` nem ad kötést az
            // engedélyezésre — a rádiók akkor szürkék, ha a kijelölésben
            // nincs film (a spec 9.3/2. pontja, futásidejű döntés).
            ColumnLayout {
                spacing: 2
                Text {
                    text: qsTr("Export movies using:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                RadioButton {
                    id: exportMovieFirstFrame
                    objectName: "exportMovieFirstFrame"
                    text: qsTr("First frame")
                    enabled: exportDialog.hasVideo
                    checked: !exportDialog.movieFull
                }
                RadioButton {
                    id: exportMovieFull
                    objectName: "exportMovieFull"
                    text: qsTr("Full movie (no resizing)")
                    enabled: exportDialog.hasVideo
                    checked: exportDialog.movieFull
                }
            }
            CheckBox {
                id: exportAddNumbersCheck
                objectName: "exportAddNumbersCheck"
                text: qsTr("Add numbers to file names to preserve order")
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Image size:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                ComboBox {
                    id: exportSizeBox
                    objectName: "exportSizeBox"
                    Layout.preferredWidth: 160
                    model: [qsTr("Original size"), "2048 px", "1600 px",
                            "1024 px", "800 px"]
                }
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Image quality:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                ComboBox {
                    id: exportQualityPreset
                    objectName: "exportQualityPreset"
                    Layout.preferredWidth: 130
                    model: [qsTr("Automatic"), qsTr("Normal"),
                            qsTr("Maximum"), qsTr("Minimum"), qsTr("Custom")]
                    currentIndex: 1  // Normal — a korábbi, mindig-küldött 85 alapértelmezéssel egyező
                }
                SpinBox {
                    id: exportQuality
                    objectName: "exportQuality"
                    from: 1; to: 100; value: 85
                    // #369: csak "Custom" presetnél számít az érték, ekkor
                    // aktív — az exportRows-nak enélkül is mindig átadjuk
                    // (resolveExportQuality a nem-custom preseteknél eldobja).
                    enabled: exportQualityPreset.currentIndex === 4
                }
            }
            ColumnLayout {
                spacing: 4
                CheckBox {
                    id: exportWatermarkCheck
                    objectName: "exportWatermarkCheck"
                    text: qsTr("Add watermark")
                }
                RowLayout {
                    spacing: 8
                    Item { Layout.preferredWidth: 20 }  // behúzás (a FEN "indent" spacere)
                    TextField {
                        id: exportWatermarkField
                        objectName: "exportWatermarkField"
                        Layout.preferredWidth: 200
                        enabled: exportWatermarkCheck.checked
                        // #422: jobbklikk-menü (Picasa `Address`)
                        TextFieldContextArea {}
                    }
                }
            }
        }
    }

    FolderDialog {
        id: exportTargetDialog
        title: qsTr("Export Picture to Folder...")
        onAccepted: exportDialog.targetFolder = selectedFolder.toString()
    }

    // #1166: a célmappa-ütközés kérdése — az eredeti szövegeivel
    // (`CExportPrefsPage::destexists` / `::overwritetitle`). Igen esetén az
    // ELŐZŐ album tartalma törlődik, nem mellé exportálunk.
    Dialog {
        id: exportOverwriteDialog
        objectName: "exportOverwriteDialog"
        title: qsTr("Would you like to overwrite?")
        modal: true
        anchors.centerIn: parent
        // a tördelő szöveg és a Dialog implicit szélessége körbeérne (#1185)
        implicitWidth: 380 + leftPadding + rightPadding
        standardButtons: Dialog.Yes | Dialog.No
        onAccepted: exportDialog.startExport(true)
        onRejected: exportDialog.startExport(false)
        Text {
            objectName: "exportOverwriteText"
            width: 380
            wrapMode: Text.WordWrap
            text: qsTr("The destination already exists. Would you like to overwrite it with your new album?")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    Dialog {
        id: exportResultDialog
        objectName: "exportResultDialog"
        // #1166: hibás futásnál az eredeti címe „Hiba"
        // (`CExportPrefsPage::errortitle`), sikeresnél marad az „Export".
        title: exportResultDialog.failedDetails.length > 0
               ? qsTr("Error") : qsTr("Export")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        property string message: ""
        property var failedDetails: []
        Text {
            objectName: "exportResultText"
            text: exportResultDialog.message
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    // #530: a célmappa választása után azonnal indul az export (háttérszálon)
    FolderDialog {
        id: earthTargetDialog
        objectName: "earthTargetDialog"
        title: qsTr("Export to Google Earth File")
        onAccepted: {
            if (typeof controller === "undefined" || !controller) return
            var mappa = selectedFolder.toString().replace(/^file:\/\//, "")
            controller.exportGoogleEarth(
                dialogs.appWindow.selectedIndexes, mappa, "")
        }
    }

    Dialog {
        id: earthResultDialog
        objectName: "earthResultDialog"
        title: qsTr("Export to Google Earth File")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        property string message: ""
        Text {
            objectName: "earthResultText"
            text: earthResultDialog.message
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    Connections {
        target: controller
        // #136: a sikertelen fájlok neve/oka a számszerű összegzés ELŐTT
        // érkezik — a dialógus szövegébe fűzzük, hogy a felhasználó lássa,
        // melyik fájl és miért hiúsult meg, ne csak a darabszámot.
        function onExportFailedDetails(details) {
            exportResultDialog.failedDetails = details
        }
        function onExportFinished(done, failed) {
            var message = failed > 0
                ? qsTr("%1 pictures exported, %2 failed.").arg(done).arg(failed)
                : qsTr("%1 pictures exported.").arg(done)
            if (exportResultDialog.failedDetails.length > 0)
                message += "\n" + exportResultDialog.failedDetails.join("\n")
            exportResultDialog.message = message
            exportResultDialog.failedDetails = []
            exportResultDialog.open()
        }
        // #530: a Google Earth-export vége. A KIHAGYOTTAKAT is kiírjuk: a
        // felhasználónak tudnia kell, miért kevesebb a helyjelző, mint a
        // kijelölés (koordináta nélküli képet nincs hova tenni a térképen).
        function onEarthExportFinished(kmlPath, placemarks, skipped) {
            var message = kmlPath.length > 0
                ? qsTr("%1 pictures written to the Google Earth file.")
                    .arg(placemarks)
                : qsTr("None of the selected pictures has a location, so no Google Earth file was written.")
            if (skipped > 0 && kmlPath.length > 0)
                message += "\n" + qsTr("%1 pictures were left out: they have no location.")
                    .arg(skipped)
            earthResultDialog.message = message
            earthResultDialog.open()
        }
    }
}
