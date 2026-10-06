import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

// Létrehozás menü (#29): képkollázs és mozgófilm a kijelölt képekből.
// Az ExportDialogs.qml mintája szerint: beállítás-dialógus → fájlválasztó
// → háttérszálas munka → eredmény-dialógus (controller-jelzésekre).
Item {
    id: dialogs
    anchors.fill: parent

    // a főablak (a kijelölt sorok forrása)
    required property var appWindow

    // #455: van-e a KÉPTÁLCÁN tartott kép — ilyenkor a műveletek a tálca
    // tartalmán futnak (a vezérlő dönt, ld. `_sources_for`), és a
    // párbeszédek kijelölés nélkül is megnyílnak
    readonly property bool trayHasPictures:
        (typeof controller !== "undefined" && controller)
            ? controller.heldCount > 0 : false

    // #431: a HAT Picasa-elrendezés, a FELÜLETI sorrendben (a kulcsok a
    // `.cxf` téma-azonosítói — egy betű eltérés olvashatatlan projektfájlt
    // adna). ⚠️ A „Mozaik" kulcsa `picturegrid`, a „Rács"-é `regulargrid`.
    readonly property var collageKinds: ["picturepile", "picturegrid", "framegrid",
                                         "regulargrid", "contactsheet", "multiexp"]
    // a három képkeret ugyanígy, a ComboBox sorrendjében
    readonly property var collageBorders: ["noborder", "whiteborder", "polaroid"]
    // #923: a keretválasztó CSAK a Képkupacnál és az Indexképnél létezik az
    // eredetiben (a téma képesség-maszkjának 9. bitje) — a többi témánál a
    // renderelő úgyis figyelmen kívül hagyja, ezért ne is kínáljuk fel.
    // A panelen ugyanezt a helyet a térköz-csúszka foglalja el.
    readonly property var collageBorderCapable: [true, false, false, false, true, false]

    function openCollage() { collageDialog.openForSelection() }
    function openMovie() { movieDialog.openForSelection() }
    function openPoster(sourcePath) { posterDialog.openForSource(sourcePath) }
    //: #4212: a személy-album fejléce minden ottani képet átad a meglévő
    //: Filmkészítőnek; a felbontást a szokásos `movieHeightBox` kezeli.
    function openMovieForRows(rows) {
        // A személyalbum teljes sora a forrás, akkor is, ha a képtálcán
        // másik kép van. A megszokott megnyitás továbbra is a tálcát részesíti előnyben.
        movieDialog.openForRows(rows, false, false)
    }
    //: #2114: a film ÚJRANYITÁSA a projektfájljából — a diaidő onnan
    //: jön, a kijelölés a hívó oldalán már a projekt képeire áll.
    //: ⛔ A FELBONTÁS nincs a projektfájlban (`curresolution` nálunk
    //: kitöltetlen), ezért az marad az alapértelmezésen — a párbeszéd
    //: felirata ezt ki is mondja.
    function openMovieProject(masodperc, burstmodethresh) {
        movieDialog.projektbolNyilt = true
        if (masodperc > 0)
            movieSeconds.value = Math.round(masodperc * 10)
        if (burstmodethresh !== undefined && burstmodethresh >= 0)
            movieBurstSlider.value = Math.sqrt(
                Math.min(86400, burstmodethresh) / 86400)
        movieDialog.open()
    }

    Dialog {
        id: posterDialog
        objectName: "posterDialog"
        title: qsTr("Poster Settings")
        modal: true
        focus: true
        anchors.centerIn: parent
        width: Math.min(440, dialogs.appWindow.width - 32)
        standardButtons: Dialog.NoButton
        property string sourcePath: ""
        readonly property var paperOptions: {
            var sizes = controller
                    && typeof controller.posterPaperSizes === "function"
                    ? controller.posterPaperSizes() : ["4x6", "8.5x11"]
            var options = []
            for (var i = 0; i < sizes.length; ++i)
                options.push({key: sizes[i], label: posterPaperLabel(sizes[i])})
            return options
        }

        function posterPaperLabel(key) {
            if (key === "4x6") return qsTr("4x6")
            if (key === "8.5x11") return qsTr("8.5x11")
            if (key === "10x15") return qsTr("10x15")
            if (key === "20x25") return qsTr("20x25")
            return key
        }

        function openForSource(path) {
            sourcePath = String(path || "")
            posterSizeBox.currentIndex = 0
            posterPaperBox.currentIndex = 0
            if (controller && typeof controller.posterPaperSize === "function") {
                var preferredPaper = controller.posterPaperSize()
                for (var i = 0; i < paperOptions.length; ++i) {
                    if (paperOptions[i].key === preferredPaper) {
                        posterPaperBox.currentIndex = i
                        break
                    }
                }
            }
            posterOverlapCheck.checked = false
            open()
        }

        onAccepted: {
            if (!controller || sourcePath.length === 0) return
            var paper = paperOptions[posterPaperBox.currentIndex].key
            if (typeof controller.setPosterPaperSize === "function")
                controller.setPosterPaperSize(paper)
            controller.createPoster(
                sourcePath, 200 + posterSizeBox.currentIndex * 100,
                paper, posterOverlapCheck.checked)
        }

        ColumnLayout {
            spacing: 12

            Text {
                objectName: "posterTip"
                Layout.fillWidth: true
                text: qsTr("Tip: if you don't want to trim, crop your picture to the same size as the paper.")
                wrapMode: Text.WordWrap
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }

            RowLayout {
                Layout.fillWidth: true
                Text {
                    objectName: "posterSizeLabel"
                    text: qsTr("Poster size:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                PicasaComboBox {
                    id: posterSizeBox
                    objectName: "posterSizeBox"
                    Layout.fillWidth: true
                    model: [qsTr("200%"), qsTr("300%"), qsTr("400%"),
                            qsTr("500%"), qsTr("600%"), qsTr("700%"),
                            qsTr("800%"), qsTr("900%"), qsTr("1000%")]
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Text {
                    objectName: "posterPaperLabel"
                    text: qsTr("Paper size:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                PicasaComboBox {
                    id: posterPaperBox
                    objectName: "posterPaperBox"
                    Layout.fillWidth: true
                    textRole: "label"
                    model: posterDialog.paperOptions
                }
            }

            CheckBox {
                id: posterOverlapCheck
                objectName: "posterOverlapCheck"
                text: qsTr("Overlap tiles")
                font.pixelSize: Theme.fontSize
            }

            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: 8
                PicasaButton {
                    objectName: "posterAcceptButton"
                    text: qsTr("OK")
                    accent: Theme.picasaGreen
                    onClicked: posterDialog.accept()
                }
                PicasaButton {
                    objectName: "posterCancelButton"
                    text: qsTr("Cancel")
                    onClicked: posterDialog.reject()
                }
            }
        }
    }

    Dialog {
        id: collageDialog
        objectName: "collageDialog"
        title: qsTr("Picture Collage...")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property string targetFile: ""
        // #922: hány kép lesz ténylegesen a kollázsban — a tálca ELŐBBRE
        // való a kijelölésnél, ugyanúgy, ahogy a vezérlő `_sources_for`-ja
        // dönt (#455). Ebből él a tipp és az OK is.
        readonly property int sourceCount:
            dialogs.trayHasPictures
                ? controller.heldCount
                : dialogs.appWindow.selectedIndexes.length
        // #920: élő előnézet — a Kollázs eddig VAKON dolgozott: a
        // felhasználó választott, a program fájlba renderelt, és csak utána
        // derült ki, mit kapott.
        property int previewRevision: 0
        function refreshPreview() {
            controller.requestCollagePreview(
                dialogs.appWindow.selectedIndexes,
                dialogs.collageKinds[collageKindBox.currentIndex],
                dialogs.collageBorders[collageBorderBox.currentIndex])
        }
        function openForSelection() {
            // #922: MINDIG megnyílik. Korábban forrás nélkül némán
            // visszatért, és a kattintás nyomtalanul elnyelődött — az
            // eredeti Picasában ilyen nincs, az megnyitja a lapot és
            // megmondja, mi hiányzik.
            open()
            refreshPreview()
        }
        onOpened: standardButton(Dialog.Ok).enabled = Qt.binding(
            function() {
                return collageDialog.targetFile.length > 0
                       && collageDialog.sourceCount > 0
            })
        onAccepted: controller.makeCollage(
            dialogs.appWindow.selectedIndexes,
            dialogs.collageKinds[collageKindBox.currentIndex],
            collageDialog.targetFile,
            dialogs.collageBorders[collageBorderBox.currentIndex])
        ColumnLayout {
            spacing: 10
            Text {
                objectName: "collageNoSourceHint"
                visible: collageDialog.sourceCount === 0
                text: qsTr("Select pictures in the library first, or put them in the Picture Tray.")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                wrapMode: Text.WordWrap
                Layout.preferredWidth: 320
            }
            Text {
                objectName: "collageCountLabel"
                text: qsTr("%1 pictures selected.").arg(
                    dialogs.appWindow.selectedIndexes.length)
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            // #920: az élő előnézet — ez az, ami eddig hiányzott
            Image {
                objectName: "collagePreviewImage"
                Layout.preferredWidth: 320
                Layout.preferredHeight: 240
                fillMode: Image.PreserveAspectFit
                cache: false
                visible: collageDialog.sourceCount > 0
                source: collageDialog.previewRevision > 0
                        ? "image://collagepreview/kollazs?rev=" + collageDialog.previewRevision
                        : ""
            }
            Button {
                objectName: "collageShuffleButton"
                text: qsTr("Scramble Collage")
                visible: collageDialog.sourceCount > 0
                onClicked: {
                    controller.shuffleCollage()
                    collageDialog.refreshPreview()
                }
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Collage type:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                PicasaComboBox {
                    id: collageKindBox
                    objectName: "collageKindBox"
                    Layout.preferredWidth: 180
                    // az eredeti Picasa nevei és sorrendje
                    model: [qsTr("Picture Pile"), qsTr("Mosaic"),
                            qsTr("Frame Mosaic"), qsTr("Grid"),
                            qsTr("Contact Sheet"), qsTr("Multiple Exposure")]
                    onCurrentIndexChanged: collageDialog.refreshPreview()
                }
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Picture borders:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                PicasaComboBox {
                    id: collageBorderBox
                    objectName: "collageBorderBox"
                    Layout.preferredWidth: 180
                    model: [qsTr("None"), qsTr("White Border"), qsTr("Polaroid")]
                    enabled: dialogs.collageBorderCapable[collageKindBox.currentIndex]
                    onCurrentIndexChanged: collageDialog.refreshPreview()
                }
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Target file:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                Text {
                    objectName: "collageTargetLabel"
                    Layout.preferredWidth: 240
                    elide: Text.ElideMiddle
                    text: collageDialog.targetFile.length > 0
                          ? collageDialog.targetFile
                          : qsTr("(not selected)")
                    font.pixelSize: Theme.fontSize
                    color: Theme.textGray
                }
                PicasaButton {
                    text: qsTr("Browse...")
                    onClicked: collageTargetDialog.open()
                }
            }
        }
    }

    FileDialog {
        id: collageTargetDialog
        title: qsTr("Picture Collage...")
        fileMode: FileDialog.SaveFile
        defaultSuffix: "jpg"
        nameFilters: [qsTr("JPEG images (*.jpg)")]
        onAccepted: collageDialog.targetFile = selectedFile.toString()
    }

    Dialog {
        id: movieDialog
        objectName: "movieDialog"
        title: qsTr("Movie")
        modal: false
        anchors.centerIn: parent
        width: 700
        // A magyar feliratokkal is a teljes Mozgófilm fül férjen el az
        // előnézet és a vezérlősáv fölött; kisebb főablaknál a ScrollView
        // maradjon látható, saját görgetősávval.
        height: Math.min(720, Math.max(0, dialogs.appWindow.height - 24))
        standardButtons: Dialog.NoButton
        property string targetFile: ""
        property string audioFile: ""
        property int audioOption: 0
        property int transitionIndex: 1
        property var movieClipIndexes: []
        property var movieClipSources: []
        property int movieInitialPhotoCount: 0
        property int previewIndex: 0
        property string previewSource: ""
        property bool previewActualSizeEnabled: false
        property int previewWindowVisibilityBeforeFullscreen: Window.Windowed
        property bool previewOwnsFullscreen: false
        property var movieSlides: []
        property var movieSlideSelection: []
        property int movieSlideEditingIndex: -1
        property string textColor: "#ffffff"
        property string backgroundColor: "#000000"
        property bool loadingTextSlide: false
        onTextColorChanged: updateSelectedTextSlide()
        onBackgroundColorChanged: updateSelectedTextSlide()
        //: #2114: projektfájlból nyitottuk-e — ilyenkor a párbeszéd
        //: kimondja, hogy a felbontás NEM a projektből jön.
        property bool projektbolNyilt: false
        // A `makemoviepanel` 2.1 listája, a binárisban használt kulcsokkal.
        readonly property var transitionKeys: [
            "cut", "dissolve", "dissolveblack", "dissolvewhite",
            "wipeleft", "wiperight", "wipeup", "wipedown",
            "diagwipeul", "diagwipeur", "diagwipedl", "diagwipedr",
            "pushleft", "pushright", "pushtop", "pushdown",
            "circlein", "circleout", "kenburns", "kenburnsaoi",
            "timelapse", "rect",
        ]
        readonly property var sizeOptions: [
            [320, 240], [640, 480], [800, 600], [1024, 768],
            [1600, 1200], [1280, 720], [1920, 1080],
        ]
        readonly property var textSizes: [
            8, 10, 12, 14, 16, 18, 20, 22, 26, 30, 36, 48, 60, 72, 84, 96,
        ]
        readonly property var textStyleIds: [
            "textstyle0", "textstyle1", "textstyle2", "textstyle3",
            "textstyle4", "textstyle5", "textstyle6", "textstyle7",
            "textstyle8", "textstyle9", "textstyle10", "textstyle11",
        ]
        readonly property int defaultSizeIndex: controller
                && controller.movieResolutionIndex !== undefined
                ? controller.movieResolutionIndex : 1
        readonly property int movieUsedPhotoCount: Math.floor(
            movieLengthSlider.value * movieLengthSlider.value
            * movieInitialPhotoCount)
        readonly property int movieBurstThresholdSeconds: Math.floor(
            movieBurstSlider.value * movieBurstSlider.value * 86400)
        readonly property real previewSlideDurationSeconds:
            Math.max(0.5, movieSeconds.value / 10)
        readonly property real previewDurationSeconds:
            previewSlideDurationSeconds * movieClipSources.length
        function formatPreviewTime(seconds) {
            var total = Math.max(0, Math.floor(seconds))
            var hours = Math.floor(total / 3600)
            var minutes = Math.floor(total / 60) % 60
            var remainingSeconds = total % 60
            function ketjegyu(value) {
                return value < 10 ? "0" + value : String(value)
            }
            return ketjegyu(hours) + ":" + ketjegyu(minutes)
                    + ":" + ketjegyu(remainingSeconds)
        }
        function togglePreviewPlayback() {
            if (!movieClipSources.length) {
                moviePreviewTimer.stop()
            } else if (moviePreviewTimer.running) {
                moviePreviewTimer.stop()
            } else {
                previewIndex = 0
                previewSource = movieClipSources[0]
                moviePreviewTimer.start()
            }
        }
        function seekPreview(seconds) {
            if (!movieClipSources.length) return
            previewIndex = Math.min(
                movieClipSources.length - 1,
                Math.max(0, Math.floor(seconds / previewSlideDurationSeconds)))
            previewSource = movieClipSources[previewIndex]
        }
        function togglePreviewFullscreen() {
            var hostWindow = moviePreviewPanel.Window.window
            if (!hostWindow) return
            if (previewOwnsFullscreen
                    && hostWindow.visibility === Window.FullScreen) {
                hostWindow.visibility = previewWindowVisibilityBeforeFullscreen
                previewOwnsFullscreen = false
            } else if (hostWindow.visibility !== Window.FullScreen) {
                previewWindowVisibilityBeforeFullscreen = hostWindow.visibility
                hostWindow.visibility = Window.FullScreen
                previewOwnsFullscreen = true
            }
        }
        function restorePreviewFullscreen() {
            var hostWindow = moviePreviewPanel.Window.window
            if (previewOwnsFullscreen && hostWindow
                    && hostWindow.visibility === Window.FullScreen) {
                hostWindow.visibility = previewWindowVisibilityBeforeFullscreen
                previewOwnsFullscreen = false
            }
        }
        function openForSelection() {
            // #455: tartott képekkel a tálca a forrás — ilyenkor a
            // rácsban nem is kell kijelölésnek lennie
            openForRows(
                dialogs.appWindow.selectedIndexes,
                dialogs.trayHasPictures,
                true)
        }
        function openForRows(rows, allowTray, preferTray) {
            if ((!rows || rows.length === 0) && !allowTray) return
            movieClipIndexes = rows ? rows.slice(0) : []
            movieClipSources = preferTray
                ? controller.movieSourceUrls(movieClipIndexes)
                : controller.selectedMovieSourceUrls(movieClipIndexes)
            movieInitialPhotoCount = movieClipSources.length
            movieSlides = []
            movieSlideSelection = []
            movieSlideEditingIndex = -1
            movieSlideList.currentIndex = -1
            loadTextSlide()
            previewIndex = 0
            previewSource = movieClipSources.length ? movieClipSources[0] : ""
            targetFile = ""
            open()
        }
        function selectedPictureCaption() {
            if (!controller || !controller.photos
                    || typeof controller.photos.captionAt !== "function")
                return ""
            var row = dialogs.appWindow.selectedIndex
            if (row < 0 && dialogs.appWindow.selectedIndexes.length)
                row = dialogs.appWindow.selectedIndexes[0]
            return row >= 0 ? controller.photos.captionAt(row) : ""
        }
        function openTitleDialog() {
            movieTitleDialog.openForCaption(selectedPictureCaption(), {
                text: movieSlideText.text,
                font: movieFontBox.currentText,
                size: textSizes[movieTextSizeBox.currentIndex],
                style: movieTextStyleBox.currentIndex,
                bold: movieBoldBox.checked,
                italic: movieItalicBox.checked,
                outline: movieOutlineBox.checked,
            })
        }
        function addTextSlide(slide) {
            var slides = movieSlides.slice(0)
            var selected = movieSlideSelection.length
                    ? movieSlideSelection : (movieSlideList.currentIndex >= 0
                        ? [movieSlideList.currentIndex] : [])
            var insertionIndex = selected.length
                    ? Math.max.apply(null, selected) + 1 : slides.length
            slides.splice(insertionIndex, 0, slide || {
                text: movieSlideText.text || qsTr("Text"),
                font: movieFontBox.currentText,
                size: textSizes[movieTextSizeBox.currentIndex],
                style: movieTextStyleBox.currentIndex,
                bold: movieBoldBox.checked,
                italic: movieItalicBox.checked,
                outline: movieOutlineBox.checked,
                textColor: textColor,
                backgroundColor: backgroundColor,
            })
            movieSlides = slides
            movieSlideSelection = [insertionIndex]
            movieSlideEditingIndex = insertionIndex
            movieSlideList.currentIndex = insertionIndex
            loadTextSlide()
        }
        function loadTextSlide() {
            loadingTextSlide = true
            var index = movieSlideList.currentIndex
            var slide = index >= 0 && index < movieSlides.length
                    ? movieSlides[index] : null
            if (slide) {
                movieSlideText.text = slide.text || qsTr("Text")
                var fontIndex = movieFontBox.model.indexOf(slide.font)
                if (fontIndex >= 0) movieFontBox.currentIndex = fontIndex
                var sizeIndex = textSizes.indexOf(slide.size)
                if (sizeIndex >= 0) movieTextSizeBox.currentIndex = sizeIndex
                movieTextStyleBox.currentIndex = Math.max(
                    0, Math.min(11, slide.style || 0))
                movieBoldBox.checked = !!slide.bold
                movieItalicBox.checked = !!slide.italic
                movieOutlineBox.checked = !!slide.outline
                textColor = slide.textColor || "#ffffff"
                backgroundColor = slide.backgroundColor || "#000000"
            } else {
                movieSlideText.text = qsTr("Text")
                movieFontBox.currentIndex = movieFontBox.model.length > 0 ? 0 : -1
                movieTextSizeBox.currentIndex = 4
                movieTextStyleBox.currentIndex = 0
                movieBoldBox.checked = false
                movieItalicBox.checked = false
                movieOutlineBox.checked = false
                textColor = "#ffffff"
                backgroundColor = "#000000"
            }
            loadingTextSlide = false
        }
        function updateSelectedTextSlide() {
            var index = movieSlideList.currentIndex
            if (loadingTextSlide || index < 0 || index >= movieSlides.length)
                return
            var slides = movieSlides.slice(0)
            slides[index] = {
                text: movieSlideText.text || qsTr("Text"),
                font: movieFontBox.currentText || movieSlides[index].font
                    || "DejaVuSans",
                size: movieTextSizeBox.currentIndex >= 0
                    ? textSizes[movieTextSizeBox.currentIndex]
                    : movieSlides[index].size || 16,
                style: movieTextStyleBox.currentIndex >= 0
                    ? movieTextStyleBox.currentIndex
                    : movieSlides[index].style || 0,
                bold: movieBoldBox.checked,
                italic: movieItalicBox.checked,
                outline: movieOutlineBox.checked,
                textColor: textColor.toString(),
                backgroundColor: backgroundColor.toString(),
            }
            movieSlides = slides
            movieSlideList.currentIndex = index
        }
        function removeTextSlide() {
            var selected = movieSlideSelection.length
                    ? movieSlideSelection.slice(0)
                    : (movieSlideList.currentIndex >= 0
                        ? [movieSlideList.currentIndex] : [])
            if (!selected.length) return
            var slides = movieSlides.slice(0)
            selected.sort(function(a, b) { return b - a })
            selected.forEach(function(index) { slides.splice(index, 1) })
            movieSlides = slides
            var nextIndex = Math.min(selected[selected.length - 1], slides.length - 1)
            movieSlideSelection = nextIndex >= 0 ? [nextIndex] : []
            movieSlideEditingIndex = -1
            movieSlideList.currentIndex = nextIndex
            loadTextSlide()
        }
        function selectTextSlide(index, modifiers) {
            var selected = movieSlideSelection.slice(0)
            if (modifiers & Qt.ControlModifier) {
                var at = selected.indexOf(index)
                if (at >= 0) selected.splice(at, 1)
                else selected.push(index)
            } else if (selected.indexOf(index) < 0) {
                selected = [index]
            }
            movieSlideSelection = selected
            movieSlideList.currentIndex = index
        }
        function moveTextSlides(targetIndex) {
            var selected = movieSlideSelection.length
                    ? movieSlideSelection.slice(0) : [movieSlideList.currentIndex]
            selected = selected.filter(function(index) {
                return index >= 0 && index < movieSlides.length
            }).sort(function(a, b) { return a - b })
            if (!selected.length) return
            if (selected.indexOf(targetIndex) >= 0) return
            var slides = movieSlides.slice(0)
            var moving = selected.map(function(index) { return slides[index] })
            var removedBeforeTarget = selected.filter(function(index) {
                return index < targetIndex
            }).length
            var movingBeforeTarget = selected[selected.length - 1] < targetIndex
            for (var i = selected.length - 1; i >= 0; --i)
                slides.splice(selected[i], 1)
            var insertionIndex = Math.max(0, Math.min(
                slides.length,
                targetIndex - removedBeforeTarget + (movingBeforeTarget ? 1 : 0)))
            slides.splice.apply(slides, [insertionIndex, 0].concat(moving))
            movieSlides = slides
            movieSlideSelection = moving.map(function(_slide, index) {
                return insertionIndex + index
            })
            movieSlideEditingIndex = -1
            movieSlideList.currentIndex = insertionIndex
        }
        function editTextSlide(index) {
            if (index < 0 || index >= movieSlides.length) return
            movieSlideSelection = [index]
            movieSlideEditingIndex = index
            movieSlideList.currentIndex = index
            loadTextSlide()
        }
        function updateSelectedText(text) {
            var index = movieSlideEditingIndex
            if (index < 0 || index >= movieSlides.length) return
            var slides = movieSlides.slice(0)
            var slide = Object.assign({}, slides[index])
            slide.text = text
            slides[index] = slide
            movieSlides = slides
        }
        function recomputeMovie() {
            if (movieSlides.length > 0) {
                movieRecomputeConfirm.ask(
                    "askapplyconfirm",
                    qsTr("This will generate a new movie removing all the text slides you added. Are you sure?")
                )
                return
            }
            applyMovieRecompute()
        }
        function applyMovieRecompute() {
            movieSlides = []
            movieSlideSelection = []
            movieSlideEditingIndex = -1
            movieSlideList.currentIndex = -1
            loadTextSlide()
            if (controller)
                movieClipSources = controller.movieSourceUrls(movieClipSources)
            previewIndex = 0
            previewSource = movieClipSources.length ? movieClipSources[0] : ""
            moviePreviewTimer.stop()
            movieTabs.currentIndex = 0
        }
        function exportMovie() {
            var meret = sizeOptions[movieHeightBox.currentIndex]
            var sources = movieClipSources.slice(0)
            if (movieSoloClip.checked && sources.length) {
                var selected = movieClipList.currentIndex < 0 ? 0 : movieClipList.currentIndex
                sources = [sources[selected]]
            }
            sources = sources.slice(0, movieUsedPhotoCount)
            movieProgressDialog.done = 0
            movieProgressDialog.total = sources.length
                    + movieSlides.length
            movieProgressDialog.open()
            controller.exportMovie(
                sources, targetFile, meret[1], movieSeconds.value / 10.0,
                meret[0], transitionKeys[transitionIndex], movieOverlapSlider.value,
                audioFile, audioOption, movieSlides, {
                    ordering: movieSmartOrder.checked ? 0
                        : movieChronologicalOrder.checked ? 2 : 1,
                    showcaptions: movieShowCaptions.checked,
                    showdates: movieShowDates.checked,
                    cropfit: movieCropToFit.checked,
                    removelowresfaces: movieRemoveLowResFaces.checked,
                    burstmodethresh: movieBurstThresholdSeconds,
                })
            close()
        }
        onClosed: {
            movieDialog.projektbolNyilt = false
            moviePreviewTimer.stop()
            movieDialog.restorePreviewFullscreen()
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 14
            spacing: 8
            TabBar {
                id: movieTabs
                objectName: "movieTabs"
                Layout.fillWidth: true
                TabButton { objectName: "movieTabMotion"; text: qsTr("Movie") }
                TabButton { objectName: "movieTabSlide"; text: qsTr("Slide") }
                TabButton { objectName: "movieTabClips"; text: qsTr("Clips") }
            }
            StackLayout {
                id: moviePages
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: movieTabs.currentIndex
                ScrollView {
                    objectName: "movieTabPanelMotion"
                    clip: true
                    ScrollBar.vertical: ScrollBar {
                        objectName: "movieMotionScrollBar"
                    }
                    ColumnLayout {
                        width: moviePages.width
                        spacing: 8
                        Text {
                            objectName: "movieProjectNote"
                            visible: movieDialog.projektbolNyilt
                            text: qsTr("The movie's pictures and timing come from the project file; the size starts from the default.")
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                            font.pixelSize: Theme.fontSize - 1
                            color: Theme.textGray
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.maximumWidth: moviePages.width
                            Text {
                                objectName: "movieCountLabel"
                                text: qsTr("%1 pictures selected.").arg(movieDialog.movieClipSources.length)
                                font.pixelSize: Theme.fontSize
                                color: Theme.textGray
                            }
                            Item { Layout.fillWidth: true }
                            Button {
                                objectName: "rewind"
                                text: qsTr("Back to selected slide")
                                ToolTip.text: qsTr("Back to selected slide")
                                ToolTip.visible: hovered
                                ToolTip.delay: Theme.tooltipDelay
                                onClicked: {
                                    moviePreviewTimer.stop()
                                    var selected = movieClipList.currentIndex
                                    if (selected < 0) selected = 0
                                    movieDialog.previewIndex = selected
                                    movieDialog.previewSource =
                                        movieDialog.movieClipSources.length
                                        ? movieDialog.movieClipSources[selected] : ""
                                }
                            }
                        }
                        RowLayout {
                            Layout.maximumWidth: moviePages.width
                            Text {
                                objectName: "moviesize_label"
                                text: qsTr("Dimensions")
                                color: Theme.ink
                            }
                            PicasaComboBox {
                                id: movieHeightBox
                                objectName: "movieHeightBox"
                                Layout.preferredWidth: 190
                                model: ["320x240", "640x480", "800x600",
                                    "1024x768", "1600x1200", "1280x720 (720p)",
                                    "1920x1080 (1080p)"]
                                currentIndex: movieDialog.defaultSizeIndex
                                onActivated: controller.setMovieResolutionIndex(currentIndex)
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.maximumWidth: moviePages.width
                            Text { text: qsTr("Transition style:"); color: Theme.ink }
                            PicasaComboBox {
                                id: movieTransitionBox
                                objectName: "movieTransitionBox"
                                Layout.fillWidth: true
                                model: [qsTr("Cut"), qsTr("Dissolve"),
                                    qsTr("Dissolve through black"), qsTr("Dissolve through white"),
                                    qsTr("Wipe - left"), qsTr("Wipe"), qsTr("Wipe - top"),
                                    qsTr("Wipe - bottom"), qsTr("Wipe - up left"),
                                    qsTr("Wipe - up right"), qsTr("Wipe - down left"),
                                    qsTr("Wipe - down right"), qsTr("Push - left"), qsTr("Push"),
                                    qsTr("Push - top"), qsTr("Push - bottom"),
                                    qsTr("Circle - inwards"), qsTr("Circle"),
                                    qsTr("Pan and Zoom"), qsTr("Pan and Zoom - face"),
                                    qsTr("Time Lapse"), qsTr("Rectangle")]
                                currentIndex: movieDialog.transitionIndex
                                onCurrentIndexChanged: movieDialog.transitionIndex = currentIndex
                                onActivated: movieDialog.transitionIndex = currentIndex
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.maximumWidth: moviePages.width
                            Text { text: qsTr("Overlap"); color: Theme.ink }
                            PicasaSlider {
                                id: movieOverlapSlider
                                objectName: "movieOverlapSlider"
                                Layout.fillWidth: true
                                from: 0; to: Math.max(0.1, movieSeconds.value / 10 * 0.9)
                                value: Math.min(0.5, to); stepSize: 0.1
                                grooveThickness: 9
                                grooveInset: 3
                                handleWidth: 16
                                handleHeight: 22
                                handleRadius: 3
                                handleOffsetY: 2
                                showTicks: false
                            }
                            Text {
                                objectName: "movieOverlapValueLabel"
                                text: qsTr("%1 Sec").arg(
                                    movieOverlapSlider.value.toFixed(1))
                            }
                        }
                        RowLayout {
                            Layout.maximumWidth: moviePages.width
                            Text { text: qsTr("Slide Duration:"); color: Theme.ink }
                            PicasaSlider {
                                id: movieSeconds
                                objectName: "movieSeconds"
                                Layout.fillWidth: true
                                from: 10; to: 100; stepSize: 5; value: 30
                                grooveThickness: 9
                                grooveInset: 3
                                handleWidth: 16
                                handleHeight: 22
                                handleRadius: 3
                                handleOffsetY: 2
                                showTicks: false
                            }
                            Text {
                                objectName: "movieSecondsValueLabel"
                                text: qsTr("%1 Sec").arg(
                                    (movieSeconds.value / 10).toFixed(1))
                                color: Theme.ink
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.maximumWidth: moviePages.width
                            Text { text: qsTr("Target file:"); color: Theme.ink }
                            Text {
                                objectName: "movieTargetLabel"
                                Layout.fillWidth: true
                                elide: Text.ElideMiddle
                                text: movieDialog.targetFile.length
                                    ? movieDialog.targetFile : qsTr("(not selected)")
                                color: Theme.textGray
                            }
                            Button { objectName: "movieBrowseButton"; text: qsTr("Browse..."); onClicked: movieTargetDialog.open() }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.maximumWidth: moviePages.width
                            Text {
                                objectName: "audio_label"
                                text: qsTr("Audio Track:")
                                color: Theme.ink
                            }
                            Text {
                                objectName: "movieAudioPathLabel"
                                Layout.fillWidth: true
                                text: movieDialog.audioFile.length
                                    ? decodeURIComponent(movieDialog.audioFile.split("/").pop())
                                    : qsTr("No audio selected")
                                elide: Text.ElideMiddle
                            }
                            Button { objectName: "movieAddAudioButton"; text: qsTr("Load…"); onClicked: movieAudioDialog.open() }
                            Button { objectName: "movieRemoveAudioButton"; text: qsTr("Clear"); onClicked: movieDialog.audioFile = "" }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.maximumWidth: moviePages.width
                            Text { text: qsTr("Options"); color: Theme.ink }
                            PicasaComboBox {
                                id: movieAudioOptionBox
                                objectName: "movieAudioOptionBox"
                                Layout.fillWidth: true
                                model: [qsTr("Truncate audio"), qsTr("Fit photos into audio"),
                                    qsTr("Loop photos to match audio")]
                                currentIndex: movieDialog.audioOption
                                onActivated: movieDialog.audioOption = currentIndex
                            }
                        }
                        Flow {
                            Layout.fillWidth: true
                            Layout.maximumWidth: moviePages.width
                            spacing: 8
                            CheckBox {
                                id: movieShowCaptions
                                objectName: "movieShowCaptions"
                                text: qsTr("Show Captions")
                                checked: controller && typeof controller.moviePreference === "function"
                                        ? controller.moviePreference("captions") : false
                                onToggled: if (controller && typeof controller.setMoviePreference === "function")
                                               controller.setMoviePreference("captions", checked)
                            }
                            CheckBox { id: movieShowDates; objectName: "movieShowDates"; text: qsTr("Show Dates") }
                            CheckBox {
                                id: movieCropToFit
                                objectName: "movieCropToFit"
                                text: qsTr("Full frame photo crop")
                                checked: controller && typeof controller.moviePreference === "function"
                                        ? controller.moviePreference("cropfit") : false
                                onToggled: if (controller && typeof controller.setMoviePreference === "function")
                                               controller.setMoviePreference("cropfit", checked)
                            }
                            CheckBox {
                                id: movieRemoveLowResFaces
                                objectName: "movieRemoveLowResFaces"
                                text: qsTr("Remove Low Resolution Faces")
                                checked: controller && typeof controller.moviePreference === "function"
                                        ? controller.moviePreference("removeLowResFaces") : false
                                onToggled: if (controller && typeof controller.setMoviePreference === "function")
                                               controller.setMoviePreference("removeLowResFaces", checked)
                            }
                        }
                        Flow {
                            Layout.fillWidth: true
                            Layout.maximumWidth: moviePages.width
                            spacing: 8
                            Text {
                                objectName: "ordering_header_label"
                                text: qsTr("Ordering of Slides:")
                                color: Theme.ink
                            }
                            RadioButton { id: movieSmartOrder; objectName: "movieSmartOrder"; text: qsTr("Best Transitions") }
                            RadioButton { objectName: "movieAlbumOrder"; text: qsTr("Album Order"); checked: true }
                            RadioButton { id: movieChronologicalOrder; objectName: "movieChronologicalOrder"; text: qsTr("Chronological") }
                        }
                    }
                }
                ScrollView {
                    objectName: "tabpanel2"
                    clip: true
                    ColumnLayout {
                        width: moviePages.width
                        spacing: 8
                        Text { text: qsTr("Text slide:"); color: Theme.ink }
                        TextField {
                            id: movieSlideText
                            objectName: "movieSlideText"
                            Layout.fillWidth: true
                            text: qsTr("Text")
                            onTextChanged: movieDialog.updateSelectedTextSlide()
                            TextFieldContextArea {}
                            onTextEdited: movieDialog.updateSelectedText(text)
                        }
                        RowLayout {
                            Text { text: qsTr("Font:"); color: Theme.ink }
                            PicasaComboBox {
                                id: movieFontBox
                                objectName: "movieFontBox"
                                Layout.fillWidth: true
                                model: Qt.fontFamilies()
                                onCurrentIndexChanged: movieDialog.updateSelectedTextSlide()
                            }
                        }
                        RowLayout {
                            Text { text: qsTr("Size:"); color: Theme.ink }
                            PicasaComboBox {
                                id: movieTextSizeBox
                                objectName: "movieTextSizeBox"
                                model: movieDialog.textSizes.map(function(size) {
                                    return String(size)
                                })
                                currentIndex: 4
                                onCurrentIndexChanged: movieDialog.updateSelectedTextSlide()
                            }
                            Text { text: qsTr("Style:"); color: Theme.ink }
                            PicasaComboBox {
                                id: movieTextStyleBox
                                objectName: "movieTextStyleBox"
                                Layout.fillWidth: true
                                model: [qsTr("Centered"), qsTr("I'm Feeling Lucky"), qsTr("Caption"),
                                    qsTr("Caption - Classic"), qsTr("Gradient - Black"),
                                    qsTr("Gradient - White"), qsTr("Transparent - Black"),
                                    qsTr("Transparent - White"), qsTr("Scrolling Credits"),
                                    qsTr("Music Video - Left"), qsTr("Music Video - Right"),
                                    qsTr("Caption - Typewriter")]
                                onCurrentIndexChanged: movieDialog.updateSelectedTextSlide()
                            }
                        }
                        RowLayout {
                            CheckBox {
                                id: movieBoldBox
                                objectName: "movieBoldBox"
                                text: qsTr("Bold")
                                onToggled: movieDialog.updateSelectedTextSlide()
                            }
                            CheckBox {
                                id: movieItalicBox
                                objectName: "movieItalicBox"
                                text: qsTr("Italic")
                                onToggled: movieDialog.updateSelectedTextSlide()
                            }
                            CheckBox {
                                id: movieOutlineBox
                                objectName: "movieOutlineBox"
                                text: qsTr("Automatic Outline")
                                onToggled: movieDialog.updateSelectedTextSlide()
                                ToolTip.text: qsTr("Automatic Outline (like movie subtitles)")
                                ToolTip.visible: hovered
                                ToolTip.delay: Theme.tooltipDelay
                            }
                        }
                        RowLayout {
                            Button {
                                objectName: "movieTextColorButton"
                                text: qsTr("Text color")
                                onClicked: movieTextColorDialog.open()
                            }
                            Rectangle {
                                objectName: "txcolorpicker_bevel"
                                Layout.preferredWidth: 20
                                Layout.preferredHeight: 20
                                color: movieDialog.textColor
                                border.color: Theme.chromeBorder
                                border.width: 1
                                radius: 2
                            }
                            Button {
                                objectName: "movieBackgroundColorButton"
                                text: qsTr("Background color")
                                onClicked: movieBackgroundColorDialog.open()
                            }
                            Button { objectName: "movieInsertSlideButton"; text: qsTr("Insert Text Slide"); onClicked: movieDialog.openTitleDialog() }
                            Button {
                                objectName: "movieRemoveSlideButton"
                                text: qsTr("Remove Selected Slide")
                                ToolTip.text: qsTr("Remove the selected slide")
                                ToolTip.visible: hovered
                                ToolTip.delay: Theme.tooltipDelay
                                onClicked: movieDialog.removeTextSlide()
                            }
                        }
                        Item {
                            objectName: "viewedit"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 150
                            property alias count: movieSlideList.count
                            property alias contentHeight: movieSlideList.contentHeight
                            property alias currentIndex: movieSlideList.currentIndex
                            property alias contentY: movieSlideList.contentY
                            ListView {
                                id: movieSlideList
                                objectName: "movieSlideList"
                                anchors.fill: parent
                                model: movieDialog.movieSlides
                                onCurrentIndexChanged: movieDialog.loadTextSlide()
                                delegate: ItemDelegate {
                                    id: movieSlideDelegate
                                    objectName: "movieSlideDelegate" + index
                                    width: movieSlideList.width
                                    text: modelData.text
                                    highlighted: movieDialog.movieSlideSelection.indexOf(index) >= 0
                                    MouseArea {
                                        id: movieSlidePointer
                                        anchors.fill: parent
                                        acceptedButtons: Qt.LeftButton
                                        property real pressX: 0
                                        property real pressY: 0
                                        property bool dragged: false
                                        onPressed: function(mouse) {
                                            var selected = movieDialog.movieSlideSelection
                                            if (mouse.modifiers & Qt.ControlModifier)
                                                movieDialog.selectTextSlide(index, mouse.modifiers)
                                            else if (selected.indexOf(index) < 0)
                                                movieDialog.selectTextSlide(index, mouse.modifiers)
                                            else
                                                movieSlideList.currentIndex = index
                                            pressX = mouse.x
                                            pressY = mouse.y
                                            dragged = false
                                        }
                                        onPositionChanged: function(mouse) {
                                            if (!pressed) return
                                            if (!dragged && Math.abs(mouse.x - pressX)
                                                    + Math.abs(mouse.y - pressY)
                                                    < Qt.styleHints.startDragDistance)
                                                return
                                            dragged = true
                                            var point = mapToItem(
                                                movieSlideList.contentItem, mouse.x, mouse.y)
                                            if (point.y < movieSlideList.contentY
                                                    || point.y >= movieSlideList.contentY
                                                        + movieSlideList.height) {
                                                movieDialog.removeTextSlide()
                                                return
                                            }
                                            var rowHeight = movieSlideList.count > 0
                                                    ? movieSlideList.contentHeight
                                                        / movieSlideList.count : height
                                            var targetIndex = Math.floor(point.y / rowHeight)
                                            targetIndex = Math.max(0, Math.min(
                                                movieSlideList.count - 1, targetIndex))
                                            if (targetIndex !== movieSlideList.currentIndex)
                                                movieDialog.moveTextSlides(targetIndex)
                                        }
                                        onClicked: function(mouse) {
                                            mouse.accepted = false
                                        }
                                        onDoubleClicked: movieDialog.editTextSlide(index)
                                    }
                                }
                            }
                        }
                    }
                }
                ColumnLayout {
                    objectName: "movieTabPanelClips"
                    spacing: 8
                    RowLayout {
                        Text {
                            objectName: "lengthslider_label"
                            text: qsTr("Total Photos")
                            color: Theme.ink
                        }
                        Slider {
                            id: movieLengthSlider
                            objectName: "lengthslider/scaleslider"
                            Layout.fillWidth: true
                            from: 0; to: 1; value: 1
                        }
                        Text {
                            objectName: "movieLengthCount"
                            text: String(movieDialog.movieUsedPhotoCount)
                            color: Theme.textGray
                        }
                    }
                    RowLayout {
                        Text {
                            objectName: "burstslider_label"
                            text: movieBurstSlider.value === 0
                                  ? qsTr("Don't filter by time taken")
                                  : qsTr("Remove Photos Taken Within %1")
                                      .arg(movieDialog.movieBurstThresholdSeconds)
                            color: Theme.ink
                        }
                        Slider {
                            id: movieBurstSlider
                            objectName: "burstslider/scaleslider"
                            Layout.fillWidth: true
                            from: 0; to: 1; value: 0
                        }
                    }
                    RowLayout {
                        Button {
                            objectName: "movieRecomputeButton"
                            text: qsTr("Recompute")
                            onClicked: movieDialog.recomputeMovie()
                        }
                        Button {
                            objectName: "movieAddClipsButton"
                            text: qsTr("Add selected clips")
                            ToolTip.text: qsTr("Add the selected clip(s) to the end of the movie")
                            ToolTip.visible: hovered
                            ToolTip.delay: Theme.tooltipDelay
                            onClicked: {
                                var sources = movieDialog.movieClipSources.slice(0)
                                controller.selectedMovieSourceUrls(
                                    dialogs.appWindow.selectedIndexes).forEach(function(url) {
                                    if (sources.indexOf(url) < 0) sources.push(url)
                                })
                                movieDialog.movieClipSources = sources
                            }
                        }
                        Button {
                            objectName: "movieDeleteClipButton"
                            text: qsTr("Remove selected clip")
                            ToolTip.text: qsTr("Remove the selected clip(s) from the tray")
                            ToolTip.visible: hovered
                            ToolTip.delay: Theme.tooltipDelay
                            onClicked: {
                                if (movieClipList.currentIndex < 0) return
                                var sources = movieDialog.movieClipSources.slice(0)
                                sources.splice(movieClipList.currentIndex, 1)
                                movieDialog.movieClipSources = sources
                            }
                        }
                        CheckBox { id: movieSoloClip; objectName: "movieSoloClip"; text: qsTr("Play selected clip only") }
                    }
                    ListView {
                        id: movieClipList
                        objectName: "movieClipList"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: controller && typeof controller.movieClipNames === "function"
                                ? controller.movieClipNames(movieDialog.movieClipSources) : []
                        delegate: ItemDelegate {
                            width: movieClipList.width
                            text: modelData
                            onClicked: movieClipList.currentIndex = index
                        }
                    }
                }
            }
            ColumnLayout {
                id: moviePreviewPanel
                objectName: "moviePreviewPanel"
                Layout.fillWidth: true
                spacing: 4
                RowLayout {
                    Layout.fillWidth: true
                    Item {
                        objectName: "moviePreviewViewport"
                        Layout.preferredWidth: 240
                        Layout.preferredHeight: 140
                        clip: true
                        Image {
                            id: moviePreviewImage
                            objectName: "moviePreviewImage"
                            anchors.centerIn: parent
                            width: movieDialog.previewActualSizeEnabled
                                    && sourceSize.width > 0
                                ? sourceSize.width : parent.width
                            height: movieDialog.previewActualSizeEnabled
                                    && sourceSize.height > 0
                                ? sourceSize.height : parent.height
                            fillMode: Image.PreserveAspectFit
                            cache: false
                            source: movieDialog.previewSource
                        }
                    }
                    Button {
                        objectName: "moviePreviewButton"
                        text: qsTr("Preview")
                        checkable: true
                        checked: moviePreviewTimer.running
                        onClicked: movieDialog.togglePreviewPlayback()
                    }
                }
                RowLayout {
                    objectName: "video_control_bar2/controlbar"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 32
                    spacing: 6
                    Item {
                        objectName: "video_control_bar2/moviecontrolsclip"
                        Layout.preferredWidth: 34
                        Layout.preferredHeight: 30
                        PicasaButton {
                            objectName: "video_control_bar2/moviecontrols"
                            anchors.fill: parent
                            text: moviePreviewTimer.running ? "❚❚" : "▶"
                            ToolTip.text: moviePreviewTimer.running
                                    ? qsTr("Pause") : qsTr("Preview")
                            ToolTip.delay: Theme.tooltipDelay
                            ToolTip.visible: hovered
                            onClicked: movieDialog.togglePreviewPlayback()
                        }
                    }
                    RowLayout {
                        objectName: "video_control_bar2/moviescrubslider_container"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 30
                        PicasaSlider {
                            id: moviePreviewScrubSlider
                            objectName: "video_control_bar2/scaleslider"
                            Layout.fillWidth: true
                            from: 0
                            to: Math.max(1, movieDialog.previewDurationSeconds)
                            stepSize: movieDialog.previewSlideDurationSeconds
                            enabled: movieDialog.movieClipSources.length > 1
                            Binding on value {
                                when: !moviePreviewScrubSlider.pressed
                                value: movieDialog.previewIndex
                                        * movieDialog.previewSlideDurationSeconds
                            }
                            onMoved: movieDialog.seekPreview(value)
                        }
                    }
                    Text {
                        objectName: "video_control_bar2/time"
                        Layout.preferredWidth: 136
                        horizontalAlignment: Text.AlignHCenter
                        color: Theme.ink
                        text: movieDialog.formatPreviewTime(
                                  movieDialog.previewIndex
                                  * movieDialog.previewSlideDurationSeconds)
                              + " / " + movieDialog.formatPreviewTime(
                                  movieDialog.previewDurationSeconds)
                    }
                    Text {
                        text: "🔊"
                        color: Theme.ink
                    }
                    PicasaSlider {
                        objectName: "video_control_bar2/volumeslider"
                        Layout.preferredWidth: 70
                        from: 0
                        to: 1000
                        stepSize: 10
                        value: controller && controller.movieVolume !== undefined
                            ? controller.movieVolume : 500
                        onMoved: if (controller && controller.setMovieVolume)
                                     controller.setMovieVolume(Math.round(value))
                    }
                    PicasaButton {
                        objectName: "video_control_bar2/1to1"
                        Layout.preferredWidth: 38
                        text: "1:1"
                        checkable: true
                        checked: movieDialog.previewActualSizeEnabled
                        ToolTip.text: qsTr("Show actual movie size (don't stretch)")
                        ToolTip.delay: Theme.tooltipDelay
                        ToolTip.visible: hovered
                        onClicked: movieDialog.previewActualSizeEnabled = checked
                    }
                    PicasaButton {
                        objectName: "video_control_bar2/fullscreen"
                        Layout.preferredWidth: 32
                        text: "⛶"
                        ToolTip.text: qsTr("Play full screen")
                        ToolTip.delay: Theme.tooltipDelay
                        ToolTip.visible: hovered
                        onClicked: movieDialog.togglePreviewFullscreen()
                    }
                }
            }
            RowLayout {
                objectName: "movieFooter"
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button { objectName: "movieCancelButton"; text: qsTr("Close"); onClicked: movieDialog.close() }
                Button { objectName: "movieCreateButton"; text: qsTr("Create Movie"); onClicked: movieDialog.exportMovie() }
            }
        }
    }

    Timer {
        id: moviePreviewTimer
        objectName: "moviePreviewTimer"
        interval: Math.max(500, movieSeconds.value * 100)
        repeat: true
        onTriggered: {
            if (!movieDialog.movieClipSources.length) {
                stop()
                return
            }
            movieDialog.previewIndex = (movieDialog.previewIndex + 1)
                    % movieDialog.movieClipSources.length
            movieDialog.previewSource = movieDialog.movieClipSources[movieDialog.previewIndex]
        }
    }

    ConfirmDialog {
        id: movieRecomputeConfirm
        namePrefix: "movieRecomputeConfirm"
        title: qsTr("Please Confirm...")
        onConfirmed: movieDialog.applyMovieRecompute()
    }

    MovieTitleDialog {
        id: movieTitleDialog
        textColor: movieDialog.textColor
        backgroundColor: movieDialog.backgroundColor
        previewAspectRatio: {
            var selectedSize = movieDialog.sizeOptions[movieHeightBox.currentIndex]
            return selectedSize[0] / selectedSize[1]
        }
        onSlideAdded: function(slide) { movieDialog.addTextSlide(slide) }
        onTextColorRequested: movieTextColorDialog.open()
        onBackgroundColorRequested: movieBackgroundColorDialog.open()
    }

    FileDialog {
        id: movieTargetDialog
        title: qsTr("Movie")
        fileMode: FileDialog.SaveFile
        defaultSuffix: "mp4"
        nameFilters: [qsTr("MP4 videos (*.mp4)")]
        onAccepted: movieDialog.targetFile = selectedFile.toString()
    }

    FileDialog {
        id: movieAudioDialog
        objectName: "movieAudioDialog"
        title: qsTr("Audio files")
        fileMode: FileDialog.OpenFile
        nameFilters: [
            Qt.platform.os === "windows"
                ? qsTr("Music files (*.mp3, *.wma)")
                : qsTr("Music files (*.mp3, *.m4a)"),
        ]
        onAccepted: movieDialog.audioFile = selectedFile.toString()
    }

    ColorDialog {
        id: movieTextColorDialog
        objectName: "text_picker_panel"
        title: qsTr("Text color")
        selectedColor: movieDialog.textColor
        onAccepted: movieDialog.textColor = selectedColor
    }
    ColorDialog {
        id: movieBackgroundColorDialog
        objectName: "bkg_picker_panel"
        title: qsTr("Background color")
        selectedColor: movieDialog.backgroundColor
        onAccepted: movieDialog.backgroundColor = selectedColor
    }

    // A film írása képenként halad — a Picasa is mutatja a haladást;
    // a dialógus a movieFinished/movieFailed jelzésre záródik.
    Dialog {
        id: movieProgressDialog
        objectName: "movieProgressDialog"
        title: qsTr("Movie")
        modal: true
        closePolicy: Popup.NoAutoClose
        anchors.centerIn: parent
        property int done: 0
        property int total: 0
        ColumnLayout {
            spacing: 8
            Text {
                objectName: "movieProgressText"
                text: qsTr("Creating movie: %1 / %2").arg(
                    movieProgressDialog.done).arg(movieProgressDialog.total)
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredWidth: 240
                Layout.preferredHeight: 8
                radius: 4
                color: Theme.trackBg
                border.color: Theme.chromeBorder
                Rectangle {
                    height: parent.height
                    radius: parent.radius
                    color: Theme.picasaGreen
                    width: movieProgressDialog.total > 0
                           ? parent.width * movieProgressDialog.done
                             / movieProgressDialog.total
                           : 0
                }
            }
        }
    }

    Dialog {
        id: createResultDialog
        objectName: "createResultDialog"
        title: qsTr("Create")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        property string message: ""
        // #918: a csupasz, tördelő `Text` `width: 360`-cal kötési hurkot
        // okozott (a `Dialog` az `implicitWidth`-jét a contentItem
        // `implicitWidth`-jéből számolja, a tördelő `Text` `implicitWidth`-
        // je viszont a saját szélességétől függ). A fájl többi dialógusa
        // (`collageDialog`, `movieDialog`) ugyanígy egy szimpla
        // `ColumnLayout`-gyerekbe csomagolja a tartalmát (a `Dialog` ezt
        // teszi meg `contentItem`-nek egyetlen gyerekként) — ehhez a
        // mintához igazodunk, NEM `contentItem:`-ként explicit kötve; a
        // szélesség a `Layout`-on rögzítve, nem a `Text`-en.
        ColumnLayout {
            Text {
                objectName: "createResultText"
                text: createResultDialog.message
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                wrapMode: Text.WordWrap
                Layout.preferredWidth: 360
                Layout.fillWidth: true
            }
        }
    }

    // #459/3: a hiányzó fájl KÜLÖN mondatot kap az eredeti Picasa
    // szövegével — az megmondja, mi történhetett, és a munka a maradékkal
    // elkészül. Az olvashatatlan (de meglévő) fájlok a régi, semleges
    // „kihagyva" mondatban maradnak.
    function _skippedSuffix(skipped, missing) {
        var text = ""
        if (missing > 0)
            text += "\n" + qsTr("%1 picture(s) could not be found and will not be shown. (The missing files must have been moved, renamed or deleted)").arg(missing)
        var unreadable = skipped - missing
        if (unreadable > 0)
            text += "\n" + qsTr("%1 pictures were skipped.").arg(unreadable)
        return text
    }

    // #2096: a vezérlő jelzéseit NEM itt fogadjuk. Ez a komponens a #1612 óta
    // HALASZTOTT (`DeferredDialog`), tehát amíg a felhasználó meg nem
    // nyitotta, egy itteni `Connections` NEM LÉTEZNE — a jelzés senkihez nem
    // érne el, és a visszajelzés némán elmaradna. A kollázs a Kollázs
    // PANELRŐL is indítható, tehát ez nem elméleti eset (#1743 őre fogta meg).
    //
    // A `Main.qml` mindig álló `Connections`-e hívja az alábbi függvényeket,
    // az `ensure()` után. A logika változatlan; csak a HALLGATÓ került ki.
    // Ugyanez a minta, mint a `SaveDialogs.qml`-nél.

    //: A kollázs élő előnézetének új változata (a panel jelzi).
    function frissitsdAzElonezetet(revision) {
        collageDialog.previewRevision = revision
    }

    //: A kollázs elkészült — az összegző párbeszéd megnyitása.
    function jelezdAKollazsSikert(path, used, skipped, missing) {
        createResultDialog.message =
            qsTr("Collage saved: %1").arg(path)
            + "\n" + qsTr("%1 pictures used.").arg(used)
            + dialogs._skippedSuffix(skipped, missing)
        createResultDialog.open()
    }

    //: A kollázs nem készült el.
    function jelezdAKollazsHibajat(message) {
        createResultDialog.message =
            qsTr("The collage could not be created.") + "\n" + message
        createResultDialog.open()
    }

    //: A film haladása.
    function frissitsdAFilmHaladast(done, total) {
        movieProgressDialog.done = done
        movieProgressDialog.total = total
    }

    //: A film elkészült.
    function jelezdAFilmSikert(path, used, skipped, missing) {
        movieProgressDialog.close()
        createResultDialog.message =
            qsTr("Movie saved: %1").arg(path)
            + "\n" + qsTr("%1 pictures used.").arg(used)
            + dialogs._skippedSuffix(skipped, missing)
        createResultDialog.open()
    }

    //: A film nem készült el.
    function jelezdAFilmHibajat(message) {
        movieProgressDialog.close()
        createResultDialog.message =
            qsTr("The movie could not be created.") + "\n" + message
        createResultDialog.open()
    }

    //: #4268: a poszterlapok a forráskép mellett készültek el.
    function jelezdAPoszterSikert(paths) {
        createResultDialog.message = qsTr("Poster tiles saved.")
            + "\n" + paths.join("\n")
        createResultDialog.open()
    }

    //: #4268: a poszterlapok írási hibája a párbeszédben jelenik meg.
    function jelezdAPoszterHibajat(message) {
        createResultDialog.message =
            qsTr("The poster tiles could not be created.") + "\n" + message
        createResultDialog.open()
    }
}
