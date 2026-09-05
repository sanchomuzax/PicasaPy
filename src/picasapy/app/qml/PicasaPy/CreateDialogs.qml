import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

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
                ComboBox {
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
                ComboBox {
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
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property string targetFile: ""
        // a felbontás-lista indexei → videó-magasság
        //: #1977 (7. pont): az eredeti HÉT mérete
        //: (`docs/specs/picasa-create-features.md` 2.6/c). Öt közülük
        //: 4:3-as, ezért a SZÉLESSÉG is kell — a korábbi 16:9-es
        //: származtatás azokat torzította volna (1024-es magasságból
        //: 1820 jött volna ki 768 helyett).
        readonly property var sizeOptions: [
            [320, 240], [640, 480], [800, 600], [1024, 768],
            [1600, 1200], [1280, 720], [1920, 1080],
        ]
        //: az alapértelmezés a 720p — a lista hatodik eleme
        readonly property int defaultSizeIndex: 5
        function openForSelection() {
            // #455: tartott képekkel a tálca a forrás — ilyenkor a
            // rácsban nem is kell kijelölésnek lennie
            if (!dialogs.trayHasPictures
                    && dialogs.appWindow.selectedIndexes.length === 0) return
            open()
        }
        //: #1977: az OK MINDIG engedélyezett — az eredeti sem kér
        //: célfájlt. Cél nélkül a vezérlő a `Picasa`/honosított Filmek
        //: mappába ír, a forrásmappa nevével, ütközésnél sorszámozva.
        //: A fájlválasztó megmarad „Mentés másként"-ként.
        onOpened: standardButton(Dialog.Ok).enabled = true
        onAccepted: {
            movieProgressDialog.done = 0
            movieProgressDialog.total = dialogs.appWindow.selectedIndexes.length
            movieProgressDialog.open()
            var meret = movieDialog.sizeOptions[movieHeightBox.currentIndex]
            controller.exportMovie(
                dialogs.appWindow.selectedIndexes, movieDialog.targetFile,
                meret[1], movieSeconds.value / 10.0, meret[0])
        }
        ColumnLayout {
            spacing: 10
            Text {
                objectName: "movieCountLabel"
                text: qsTr("%1 pictures selected.").arg(
                    dialogs.appWindow.selectedIndexes.length)
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Video size:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                ComboBox {
                    id: movieHeightBox
                    objectName: "movieHeightBox"
                    Layout.preferredWidth: 160
                    model: [
                        "320 × 240", "640 × 480", "800 × 600", "1024 × 768",
                        "1600 × 1200", "1280 × 720 (720p)", "1920 × 1080 (1080p)",
                    ]
                    currentIndex: movieDialog.defaultSizeIndex
                }
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Seconds per picture:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                SpinBox {
                    id: movieSeconds
                    objectName: "movieSeconds"
                    // tizedmásodperc-felbontás: 1,0–10,0 mp
                    from: 10; to: 100; stepSize: 5; value: 30
                    textFromValue: function(value) {
                        return (value / 10.0).toFixed(1)
                    }
                    valueFromText: function(text) {
                        return Math.round(parseFloat(text) * 10)
                    }
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
                    objectName: "movieTargetLabel"
                    Layout.preferredWidth: 240
                    elide: Text.ElideMiddle
                    text: movieDialog.targetFile.length > 0
                          ? movieDialog.targetFile
                          : qsTr("(not selected)")
                    font.pixelSize: Theme.fontSize
                    color: Theme.textGray
                }
                PicasaButton {
                    text: qsTr("Browse...")
                    onClicked: movieTargetDialog.open()
                }
            }
        }
    }

    FileDialog {
        id: movieTargetDialog
        title: qsTr("Movie")
        fileMode: FileDialog.SaveFile
        defaultSuffix: "mp4"
        nameFilters: [qsTr("MP4 videos (*.mp4)")]
        onAccepted: movieDialog.targetFile = selectedFile.toString()
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
}
