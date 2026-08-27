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
    //
    // #1589: `viewAfter === true` esetén a kiírás UTÁN megnyitjuk a fájlt
    // (`ID_VIEW_EARTH`), egyébként csak kiírjuk (`ID_EXPORT_EARTH`).
    function openGoogleEarth(viewAfter) {
        // ⚠️ #1589: kijelölés nélkül ez a függvény korábban NÉMÁN
        // visszatért — a felhasználó rákattintott a menüpontra, és nem
        // történt semmi. Az eredeti ilyenkor MEGSZÓLAL
        // (`PublishToEarth::NoTagged`), ezért mi is.
        if (dialogs.appWindow.selectedIndexes.length === 0) {
            earthResultDialog.message = qsTr("No geotagged images to export.")
            earthResultDialog.open()
            return
        }
        earthTargetDialog.viewAfter = viewAfter === true
        earthTargetDialog.open()
    }

    // #1138 (export.fen paritás): az „Exportálás mappába" párbeszéd
    // felülete a HITELES leíróból (`Picasa3/runtime/export.fen`) és a
    // tulajdonos képernyőképéről mérve — `docs/specs/export-parbeszed.md`
    // 1., 3., 7. és 9. szakasz. A MŰKÖDÉST (ini-átvitel, ütközéskezelés,
    // hibaágak, film-rádió, sorszámozás) a #1166 hozta be; itt a felület
    // épül újra: kétoszlopos űrlap, JOBBRA igazított feliratokkal (9.1).
    Dialog {
        id: exportDialog
        objectName: "exportDialog"
        // #1138: a `.fen` címe „Export to Folder", magyarul „Exportálás
        // mappába" — PONT NÉLKÜL (a honosítás `export/window1.title`-je).
        title: qsTr("Export to Folder")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel

        property string targetFolder: ""

        // #1138: a méret-csúszka hét fogása (`bind17.list`). A listát a
        // vezérlő adja (`export_prefs.SIZE_PRESETS`), hogy a felület és a
        // megőrzött index ne tudjon némán szétcsúszni.
        property var sizePresets: [320, 480, 640, 800, 1024, 1200, 1600]

        // #1138: az egyéni minőség (a 21 fogásos csúszka × 5). Külön
        // property, mert a legördülő ÖTÖDIK tételének felirata ebből épül
        // („Custom (%d)", `0x0073a0c0`), és a csúszka mozgatásakor
        // azonnal frissül.
        property int customQuality: 85

        // #1138 (spec 3.3, `<multi>`): a NÉGY magyarázó felirat, a
        // legördülő értéke szerint. Az ötödik tétel helyén nem szöveg,
        // hanem a csúszka áll.
        readonly property var qualityHints: [
            qsTr("Preserves original image quality"),
            qsTr("Good balance of quality and size"),
            qsTr("Very large file size, preserves fine detail"),
            qsTr("Smallest file size, some quality loss")
        ]

        // #369: a lenyíló megjelenített (fordítható) szövege és a
        // resolveExportQuality-nak átadott kulcs szándékosan külön —
        // a logika így nem törik el, ha a szöveg egyszer lefordítódik.
        readonly property var qualityPresetKeys:
            ["automatic", "normal", "maximum", "minimum", "custom"]

        // #455 (3. teendő): ha a KÉPTÁLCÁN van tartott kép, a művelet a
        // TÁLCA tartalmán fut, nem a pillanatnyi kijelölésen — az eredeti
        // Picasa buboréksúgói is végig „a képtálca képeire" hivatkoznak.
        // Üres tálcánál marad a kijelölés (a mai viselkedés).
        readonly property bool useTray:
            (typeof controller !== "undefined" && controller)
                ? controller.heldCount > 0 : false

        // #1166: a tárolt film-mód (`FileExportMovie` megfelelője) és a
        // kijelölés film-tartalma — megnyitáskor frissítjük.
        property bool movieFull: false
        property bool hasVideo: false

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

        // #1138: a legördülő ÖTÖDIK tételének felirata dinamikus —
        // „Custom (%d)" (`0x00cafa98`, formázó `0x0073a0c0`), és a szám a
        // csúszka mozgatásakor azonnal frissül. A modellt helyben írjuk
        // át (`setProperty`), mert egy ÚJ modell hozzárendelése
        // visszaállítaná a kiválasztott tételt.
        function refreshQualityLabels() {
            if (!exportQualityModel) return
            var labels = [qsTr("Automatic"), qsTr("Normal"), qsTr("Maximum"),
                          qsTr("Minimum"),
                          qsTr("Custom (%1)").arg(exportDialog.customQuality)]
            for (var i = 0; i < labels.length; ++i) {
                if (i < exportQualityModel.count)
                    exportQualityModel.setProperty(i, "text", labels[i])
                else
                    exportQualityModel.append({"text": labels[i]})
            }
        }
        onCustomQualityChanged: exportDialog.refreshQualityLabels()

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

        // #1138: a tényleges célméret. „Eredeti méret használata" mellett
        // 0 (nincs átméretezés); egyébként a MEZŐ száma — a csúszka csak
        // a hét előbeállítást tölti bele, a mező szabadon írható
        // (spec 9.3/4: a képernyőképen 1100 áll benne).
        function resolvedMaxDimension() {
            if (!exportSizeResizeRadio.checked) return 0
            var value = parseInt(exportSizeField.text, 10)
            return isNaN(value) || value < 1 ? 0 : value
        }

        onOpened: {
            // #1138 (spec 4. és 13.7): a párbeszéd a MEGŐRZÖTT
            // beállításokból indul — kilenc kulcs, egyetlen olvasással.
            var prefs = controller.exportSettings()
            exportDialog.sizePresets = controller.exportSizePresets()
            // #1166: a hely és a név alapértéke (spec 12.1) — a hely a
            // korábban használt mappa, a név a forrásalbumé. A névmező
            // fókuszban, tartalma kijelölve (`focus="name"`).
            if (exportDialog.targetFolder.length === 0)
                exportDialog.targetFolder = controller.defaultExportLocation()
            exportFolderNameField.text = controller.defaultExportName()
            exportFolderNameField.forceActiveFocus()
            exportFolderNameField.selectAll()

            // a méret-sor: ELŐBB a csúszka (az a mezőt is átírja), UTÁNA a
            // megőrzött egyéni méret — a képernyőképen a letiltott mezőben
            // is az előző egyéni érték áll (spec 9.3/3).
            exportSizeResizeRadio.checked = prefs.resize
            exportSizeOriginalRadio.checked = !prefs.resize
            exportSizeSlider.value = prefs.size
            exportSizeField.text = String(prefs.customSize)

            exportQualitySlider.value = Math.round(prefs.quality / 5)
            exportDialog.customQuality = prefs.quality
            exportDialog.refreshQualityLabels()
            exportQualityPreset.currentIndex = prefs.qualityType

            exportAddNumbersCheck.checked = prefs.addNumbers
            exportWatermarkCheck.checked = prefs.watermark
            exportWatermarkField.text = prefs.watermarkText

            exportDialog.movieFull = prefs.movieFull
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

        // #1166: az eredeti a MEGLÉVŐ célmappára rákérdez
        // (`CExportPrefsPage::destexists`), és igen esetén az ELŐZŐ albumot
        // törli. A kérdést az elfogadás UTÁN, de az indítás ELŐTT tesszük
        // fel — a válasz dönti el, ürítünk-e.
        function startExport(purgeExisting) {
            var presetKey = qualityPresetKeys[exportQualityPreset.currentIndex]
            controller.rememberExportLocation(exportDialog.targetFolder)
            var quality = controller.resolveExportQuality(
                presetKey, exportDialog.customQuality)
            // #1138 (spec 3.3): az „Automatikus" nem szám, hanem külön
            // jelző — a kimenet a FORRÁS kvantálási tábláit veszi át.
            var automatic = controller.exportQualityIsAutomatic(presetKey)
            var watermark =
                exportWatermarkCheck.checked ? exportWatermarkField.text : ""
            var maxDimension = exportDialog.resolvedMaxDimension()
            if (exportDialog.useTray)
                controller.exportHeld(
                    resolvedTargetFolder(), maxDimension, quality,
                    exportAddNumbersCheck.checked, watermark, purgeExisting,
                    automatic)
            else
                controller.exportRows(
                    dialogs.appWindow.selectedIndexes, resolvedTargetFolder(),
                    maxDimension, quality,
                    exportAddNumbersCheck.checked, watermark, purgeExisting,
                    automatic)
        }

        onAccepted: {
            // #1138 (spec 13.7, mért): a kilenc beállítás EGYETLEN
            // menetben, CSAK az elfogadáskor íródik ki — a közös
            // párbeszéd-lezáró (`0x008d2720`) a kiírót akkor hívja, ha a
            // lezárási kód 0. A Mégse ága az üres tő: sem nem ment, sem
            // nem állít vissza (ezért itt NINCS `onRejected`).
            controller.saveExportSettings({
                "size": Math.round(exportSizeSlider.value),
                "customSize": parseInt(exportSizeField.text, 10) || 800,
                "resize": exportSizeResizeRadio.checked,
                "qualityType": exportQualityPreset.currentIndex,
                "quality": exportDialog.customQuality,
                "movieFull": exportMovieFull.checked,
                "addNumbers": exportAddNumbersCheck.checked,
                "watermark": exportWatermarkCheck.checked,
                "watermarkText": exportWatermarkField.text
            })
            if (controller.exportTargetExists(resolvedTargetFolder()))
                exportOverwriteDialog.open()
            else
                exportDialog.startExport(false)
        }

        // #1138 (spec 9.1): KÉTOSZLOPOS űrlap — a `labelgroup` felirata
        // nem a vezérlő FÖLÖTT, hanem tőle BALRA, jobbra igazítva áll
        // (felirat-oszlop jobb széle x=151, vezérlő-oszlop bal széle
        // x=158, tehát 7 képpont rés).
        GridLayout {
            columns: 2
            columnSpacing: 7
            rowSpacing: 8

            // -- 1. sor: Exportálási hely (pathbox + Tallózás) -----------
            Text {
                objectName: "exportLocationLabel"
                text: qsTr("Export location:")
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            RowLayout {
                spacing: 6
                // #1138: a `.fen`-ben `pathbox`, ami az ÚTVONALAT mutatja
                // — nálunk eddig „(nincs kiválasztva)" szöveg állt. A
                // mező írásvédett: a helyet a Tallózás gomb adja
                // (`changeloc`, `0x00739850`).
                TextField {
                    id: exportLocationBox
                    objectName: "exportLocationBox"
                    Layout.preferredWidth: 357
                    readOnly: true
                    text: exportDialog.targetFolder.replace(/^file:\/\//, "")
                    font.pixelSize: Theme.fontSize
                    // #422: jobbklikk-menü (Picasa `Address`)
                    TextFieldContextArea {}
                }
                PicasaButton {
                    objectName: "exportBrowseButton"
                    text: qsTr("Browse...")
                    onClicked: exportTargetDialog.open()
                }
            }

            // -- 2. sor: Az exportált mappa neve -------------------------
            Text {
                objectName: "exportNameLabel"
                text: qsTr("Name of exported folder:")
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            TextField {
                id: exportFolderNameField
                objectName: "exportFolderNameField"
                Layout.preferredWidth: 448
                // #1166: az alapértéket a megnyitás tölti ki (a
                // forrásmappa neve — `0x0073b500`); a mező tartalma
                // induláskor KI VAN JELÖLVE (`focus="name"`).
                selectByMouse: true
                // #1138: `filter="filename"` — a Windows tiltott
                // karakterhalmaza (`0x009946f0`) nem gépelhető be.
                validator: RegularExpressionValidator {
                    regularExpression: /[^\\\/:*?"<>|]*/
                }
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }

            // -- 3. sor: sorszámozás (felirat nélkül, a 2. csoportban) ---
            Item { width: 1; height: 1 }
            CheckBox {
                id: exportAddNumbersCheck
                objectName: "exportAddNumbersCheck"
                text: qsTr("Add numbers to file names to preserve order")
            }

            // -- 4-5. sor: Képméret --------------------------------------
            Text {
                objectName: "exportSizeLabel"
                text: qsTr("Image size:")
                Layout.alignment: Qt.AlignRight | Qt.AlignTop
                topPadding: 4
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            ColumnLayout {
                spacing: 2
                Layout.fillWidth: true
                RadioButton {
                    id: exportSizeOriginalRadio
                    objectName: "exportSizeOriginalRadio"
                    text: qsTr("Use original size")
                    checked: true
                }
                RadioButton {
                    id: exportSizeResizeRadio
                    objectName: "exportSizeResizeRadio"
                    text: qsTr("Resize to:")
                }
                // #1138: `<bind attr="enabled" source="sizeradio"/>` — az
                // EGÉSZ sor tiltott, amíg az „Eredeti méret használata"
                // az aktív; az ÉRTÉKET viszont megőrzi (spec 9.3/3).
                RowLayout {
                    id: exportSizeRow
                    objectName: "exportSizeRow"
                    Layout.fillWidth: true
                    spacing: 8
                    enabled: exportSizeResizeRadio.checked
                    Item { Layout.preferredWidth: 12 }  // a FEN "indent" spacere
                    TextField {
                        id: exportSizeField
                        objectName: "exportSizeField"
                        Layout.preferredWidth: 72
                        font.pixelSize: Theme.fontSize
                        // #1138: `filter="digits"` — csak számjegy.
                        validator: RegularExpressionValidator {
                            regularExpression: /\d*/
                        }
                        TextFieldContextArea {}
                    }
                    Text {
                        objectName: "exportSizePixelsLabel"
                        text: qsTr("pixels")
                        font.pixelSize: Theme.fontSize
                        color: enabled ? Theme.ink : Theme.textGray
                    }
                    // #1138: HÉT fogás (`min="0" max="6" ticks="7"`), a
                    // 320/480/640/800/1024/1200/1600 előbeállításokkal. A
                    // csúszka a MEZŐBE ír (`bind source="size"
                    // attr="title" list="…"`); visszafelé nincs kötés, a
                    // mező szabadon írható.
                    PicasaSlider {
                        id: exportSizeSlider
                        objectName: "exportSizeSlider"
                        Layout.fillWidth: true
                        from: 0
                        to: 6
                        stepSize: 1
                        snapMode: Slider.SnapAlways
                        onValueChanged: {
                            var index = Math.round(value)
                            var presets = exportDialog.sizePresets
                            if (index >= 0 && index < presets.length)
                                exportSizeField.text = String(presets[index])
                        }
                    }
                }
            }

            // -- 6. sor: Képminőség --------------------------------------
            Text {
                objectName: "exportQualityLabel"
                text: qsTr("Image quality:")
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            RowLayout {
                spacing: 8
                Layout.fillWidth: true
                ComboBox {
                    id: exportQualityPreset
                    objectName: "exportQualityPreset"
                    Layout.preferredWidth: 153
                    textRole: "text"
                    model: ListModel {
                        id: exportQualityModel
                        Component.onCompleted: exportDialog.refreshQualityLabels()
                    }
                }
                // #1138 (spec 9.3/1): a `<multi>` a legördülő MELLETT
                // van, nem alatta, és a helye FIX — ezért a fokozat
                // váltása nem méretezi át az ablakot. Egyszerre pontosan
                // egy gyerek látszik.
                Item {
                    objectName: "exportQualityMulti"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 26
                    Text {
                        objectName: "exportQualityHint"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        visible: exportQualityPreset.currentIndex
                                 !== exportDialog.qualityHints.length
                        text: exportDialog.qualityHints[
                                  exportQualityPreset.currentIndex] || ""
                        elide: Text.ElideRight
                        font.pixelSize: Theme.fontSize
                        color: Theme.ink
                    }
                    // #1138: 21 fogás (`min="0" max="20" ticks="21"`), a
                    // minőség = állás × 5 (`0x00739fe6`). CSAK az
                    // „Egyéni" fokozat alatt látszik.
                    PicasaSlider {
                        id: exportQualitySlider
                        objectName: "exportQualitySlider"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        visible: exportQualityPreset.currentIndex
                                 === exportDialog.qualityHints.length
                        from: 0
                        to: 20
                        stepSize: 1
                        snapMode: Slider.SnapAlways
                        onValueChanged:
                            exportDialog.customQuality = Math.round(value) * 5
                    }
                }
            }

            // -- 7. sor: Filmek exportálása ------------------------------
            // #1166 (export.fen `radiogroup name="movies"`) + #1138 (spec
            // 13.10): a csoport akkor és csak akkor tiltott, ha a
            // kijelölésben egyetlen film sincs — és a CÍMKÉJÉVEL EGYÜTT
            // szürkül (a korábbi „a címke fekete marad" megfigyelés a
            // képernyőkép újranézésekor megdőlt).
            Text {
                objectName: "exportMovieLabel"
                text: qsTr("Export movies using:")
                Layout.alignment: Qt.AlignRight | Qt.AlignTop
                topPadding: 4
                enabled: exportDialog.hasVideo
                font.pixelSize: Theme.fontSize
                color: enabled ? Theme.ink : Theme.textGray
            }
            ColumnLayout {
                spacing: 2
                enabled: exportDialog.hasVideo
                RadioButton {
                    id: exportMovieFirstFrame
                    objectName: "exportMovieFirstFrame"
                    text: qsTr("First frame")
                    checked: !exportDialog.movieFull
                }
                RadioButton {
                    id: exportMovieFull
                    objectName: "exportMovieFull"
                    text: qsTr("Full movie (no resizing)")
                    checked: exportDialog.movieFull
                }
            }

            // -- 8. sor: Vízjel ------------------------------------------
            Text {
                objectName: "exportWatermarkLabel"
                text: qsTr("Watermark:")
                Layout.alignment: Qt.AlignRight | Qt.AlignTop
                topPadding: 4
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            ColumnLayout {
                spacing: 4
                Layout.fillWidth: true
                CheckBox {
                    id: exportWatermarkCheck
                    objectName: "exportWatermarkCheck"
                    text: qsTr("Add watermark")
                }
                TextField {
                    id: exportWatermarkField
                    objectName: "exportWatermarkField"
                    Layout.fillWidth: true
                    Layout.preferredWidth: 448
                    // #1138: `<bind attr="enabled" source="usewatermark"/>`
                    enabled: exportWatermarkCheck.checked
                    font.pixelSize: Theme.fontSize
                    // #422: jobbklikk-menü (Picasa `Address`)
                    TextFieldContextArea {}
                }
                // #1138: a mező alatt KIS BETŰS magyarázat
                // (`<label size="small">`, `export/label44.title`).
                Text {
                    objectName: "exportWatermarkHint"
                    Layout.preferredWidth: 448
                    wrapMode: Text.WordWrap
                    text: qsTr("Stamp photos with your name, a web domain, or a copyright notice.")
                    font.pixelSize: Theme.fontSizeLadder[0]
                    color: Theme.textGray
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
        // #1589: melyik menütétel nyitotta — a „Megtekintés…" ág a kiírás
        // után megnyittatja a fájlt, az „Exportálás…" nem
        property bool viewAfter: false
        title: earthTargetDialog.viewAfter
               ? qsTr("View in Google Earth...")
               : qsTr("Export to Google Earth File")
        onAccepted: {
            if (typeof controller === "undefined" || !controller) return
            // ⚠️ #1626: a `file://` előtag NYERS levágása Windowson
            // `/C:/Users/…`-t hagy maga után (a `file:///C:/…` alakból),
            // amiből a Python `Path` `\C:\Users\…` lesz — a `mkdir` ezen
            // `WinError 123`-mal elhasal, és a KML SOHA nem készül el (a
            // windows-CI-láb fogta meg, #1626). Az URL-t érintetlenül adjuk
            // át: a `to_local_path` (`formatting.py`) a `QUrl.toLocalFile()`-lel
            // oldja fel, ami a meghajtóbetűs alakot is helyesen kezeli. A
            // többi párbeszéd (import, webexport, adatbázis-áthelyezés,
            // mappa-mozgatás) is pontosan így, nyers URL-lel hív.
            var mappa = selectedFolder.toString()
            if (earthTargetDialog.viewAfter)
                controller.viewGoogleEarth(
                    dialogs.appWindow.selectedIndexes, mappa, "")
            else
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
        // #1589: a „Megtekintés a Google Earth programban…" ága. A
        // megnyitást SZÁNDÉKOSAN itt, a főszálon kérjük — a háttérszálból
        // indított `QDesktopServices.openUrl` nem biztonságos.
        function onEarthViewReady(kmlPath, placemarks, skipped) {
            if (kmlPath.length === 0) {
                earthResultDialog.message =
                    qsTr("No geotagged images to export.")
                earthResultDialog.open()
                return
            }
            if (typeof controller === "undefined" || !controller) return
            if (controller.openKml(kmlPath))
                return
            // néma hatástalanság helyett megmondjuk, mi történt: a fájl
            // KÉSZ, csak nincs mivel megnyitni (nincs telepítve Google
            // Earth vagy más KML-kezelő)
            earthResultDialog.message =
                qsTr("The Google Earth file was written to %1, but this "
                     + "computer has no program associated with it.")
                    .arg(kmlPath)
            earthResultDialog.open()
        }
    }
}
