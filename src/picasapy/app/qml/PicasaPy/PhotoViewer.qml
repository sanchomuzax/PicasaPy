import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Egyképes néző — a Picasa 3.9 "Megjelenítés és szerkesztés" képernyője
// alapján (#808080 háttér, felső filmszalag nyilakkal, bal eszközpanel;
// a szerkesztő-gombok a 2. fázisig szürkék). Enter/Jobbra: következő,
// Balra: előző, Esc: vissza a könyvtárba.
Rectangle {
    id: viewer
    color: "#808080"

    property var photosModel: null
    property int currentIndex: -1
    // a ListView.count reaktív — a rowCount() hívást a QML nem követné
    property int photoCount: filmstrip.count
    signal closed()

    function show(index) { currentIndex = index; forceActiveFocus() }

    // Vágás alkalmazása a kijelölésből. advance=true: Enter-flow —
    // következő kép, vágó-mód megtartva; false: Alkalmaz gomb — a panel
    // visszaáll az eszközrácsra (Picasa-viselkedés).
    function applyCrop(advance) {
        if (!cropOverlay.hasSelection) {
            if (!advance) editorPanel.cropActive = false
            return
        }
        var r = cropOverlay.cropRect
        editController.applyCrop(r.x, r.y, r.width, r.height)
        cropOverlay.resetSelection()
        if (advance) viewer.next()
        else editorPanel.cropActive = false
    }

    // a művelet-kulcs magyar gombfelirata (Visszavonás: <művelet>, #59)
    function toolLabel(action) {
        switch (action) {
        case "crop": return qsTr("Crop")
        case "tilt": return qsTr("Straighten")
        case "redeye": return qsTr("Redeye")
        case "enhance": return qsTr("I'm Feeling Lucky")
        case "autolight": return qsTr("Auto Contrast")
        case "autocolor": return qsTr("Auto Color")
        default: return ""
        }
    }

    // -- szerkesztés (#19): EditController-életciklus --------------------
    // A nézőbe lépés = szerkesztési munkamenet az aktuális képre; kilépéskor
    // a munkamenet zárul. A panel kapcsoló-állapotait az EditController
    // igazságforrásából szinkronizáljuk (a kötést a panel belső átírása
    // megtörné, ezért imperatív sync a toolsChanged-re).
    function beginEditCurrent() {
        if (visible && currentIndex >= 0 && photosModel)
            editController.beginEdit(photosModel.idAt(currentIndex),
                                     photosModel.filePathAt(currentIndex))
    }
    function syncPanelFromController() {
        editorPanel.redeyeActive = editController.redeyeActive
        editorPanel.enhanceActive = editController.enhanceActive
        editorPanel.autolightActive = editController.autolightActive
        editorPanel.autocolorActive = editController.autocolorActive
    }
    onVisibleChanged: {
        if (visible) {
            beginEditCurrent()
        } else {
            // a cropActive lenullázása ELŐBB (még aktív szerkesztés alatt)
            // fut, hogy az onCropActiveChanged->exitCropTool() még érvényes
            // munkameneten hívódjon; utána zárja az endEdit()
            editorPanel.cropActive = false
            editorPanel.tiltActive = false
            editController.endEdit()
        }
    }
    onCurrentIndexChanged: {
        if (visible) {
            beginEditCurrent()
            tiltSlider.value = 0
            if (editorPanel.cropActive) {
                editController.enterCropTool()
                cropOverlay.loadSelection(editController.cropSelection)
            } else {
                cropOverlay.resetSelection()
            }
        }
    }
    Connections {
        target: editController
        function onToolsChanged() { viewer.syncPanelFromController() }
    }
    // Vágás eszköz nyitása/zárása (#71): nyitáskor a lánc crop64 nélküli
    // (teljes, vágatlan) előnézete + a meglévő kijelölés betöltése; záráskor
    // (Mégse) a rendes, crop64-et is tartalmazó előnézet visszaáll
    Connections {
        target: editorPanel
        function onCropActiveChanged() {
            if (editorPanel.cropActive) {
                editController.enterCropTool()
                cropOverlay.loadSelection(editController.cropSelection)
            } else {
                editController.exitCropTool()
            }
        }
    }
    // A lapozás a #84 óta a modell mappán-belüli lépését használja: a
    // rács (feed) nézet mappaátlépő listáin (csillag-szűrő, keresés) sem
    // ugorhatunk át a szomszéd mappába — a folderNeighbor a saját mappa
    // határán a jelenlegi indexet adja vissza, tehát nem lép tovább.
    function next() {
        if (!photosModel) return
        currentIndex = photosModel.folderNeighbor(currentIndex, 1)
    }
    function previous() {
        if (!photosModel) return
        currentIndex = photosModel.folderNeighbor(currentIndex, -1)
    }
    // a ◀/▶ gombok (és Keys.onLeft/Right) enabled-je is a mappahatárt
    // tükrözi: nincs hova lépni, ha a folderNeighbor helyben marad
    function hasNext() {
        return photosModel
            ? photosModel.folderNeighbor(currentIndex, 1) !== currentIndex
            : false
    }
    function hasPrevious() {
        return photosModel
            ? photosModel.folderNeighbor(currentIndex, -1) !== currentIndex
            : false
    }
    // Egérgörgős lapozás (#77): a nagy nézőben a görgő a képek között
    // lép (Picasa-viselkedés). A touchpad kis deltáit egy teljes
    // görgő-fokozatig (120) gyűjtjük, hogy ne ugráljon több képet.
    property real wheelAccum: 0
    function wheelStep(delta) {
        wheelAccum += delta
        while (wheelAccum <= -120) { wheelAccum += 120; next() }
        while (wheelAccum >= 120) { wheelAccum -= 120; previous() }
    }
    function urlAt(index) {
        return photosModel ? photosModel.fileUrlAt(index) : ""
    }

    focus: visible
    Keys.onEscapePressed: viewer.closed()
    Keys.onRightPressed: next()
    Keys.onReturnPressed: next()
    Keys.onLeftPressed: previous()

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // felső sáv: vissza gomb + filmszalag nyilakkal
        Rectangle {
            Layout.fillWidth: true
            height: 46
            color: Theme.chromeBg
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8; anchors.rightMargin: 8
                spacing: 8
                PicasaButton {
                    text: "◀  " + qsTr("Back to Library")
                    font.pixelSize: Theme.fontSize
                    onClicked: viewer.closed()
                }
                Item { Layout.fillWidth: true }
                PicasaButton {
                    text: "▶ " + qsTr("Play")
                    enabled: false
                    font.pixelSize: Theme.fontSize
                }
                PicasaButton {
                    objectName: "viewerPrevButton"
                    text: "◀"; onClicked: viewer.previous()
                    enabled: viewer.hasPrevious()
                    Layout.preferredWidth: 30
                }
                ListView {
                    id: filmstrip
                    Layout.preferredWidth: Math.min(7, viewer.photoCount) * 44
                    Layout.preferredHeight: 38
                    orientation: ListView.Horizontal
                    model: viewer.photosModel
                    currentIndex: viewer.currentIndex
                    highlightMoveDuration: 100
                    clip: true
                    delegate: Rectangle {
                        required property string thumbUrl
                        required property int index
                        width: 42; height: 38
                        color: index === viewer.currentIndex
                               ? Theme.thumbSelection : "transparent"
                        Image {
                            anchors.fill: parent
                            anchors.margins: 2
                            source: thumbUrl
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                        }
                        TapHandler {
                            onTapped: viewer.currentIndex = index
                        }
                    }
                }
                PicasaButton {
                    objectName: "viewerNextButton"
                    text: "▶"; onClicked: viewer.next()
                    enabled: viewer.hasNext()
                    Layout.preferredWidth: 30
                }
                Item { Layout.fillWidth: true }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // bal eszközpanel — Gyakori javítások élesben (#19); a
            // Retusálás/Szöveg és a finomhangolás a #20-ban élesedik
            Rectangle {
                Layout.preferredWidth: 230
                Layout.fillHeight: true
                color: Theme.chromeBg

                EditorPanel {
                    id: editorPanel
                    objectName: "viewerEditorPanel"
                    anchors.top: parent.top
                    anchors.left: parent.left; anchors.right: parent.right
                    height: 420
                    imageAspect: photo.paintedHeight > 0
                                 ? photo.paintedWidth / photo.paintedHeight
                                 : 4 / 3
                    // Visszavonás/Újra — a controller undo-verméből (#59)
                    undoAvailable: editController.canUndo
                    undoLabel: editController.canUndo
                               ? qsTr("Undo") + ": "
                                 + viewer.toolLabel(editController.undoAction)
                               : qsTr("Undo")
                    redoAvailable: editController.canRedo
                    redoLabel: editController.canRedo
                               ? qsTr("Redo") + ": "
                                 + viewer.toolLabel(editController.redoAction)
                               : qsTr("Redo")
                    onToolActivated: function(tool) {
                        // crop/tilt helyi mód (overlay/csúszka); a többi
                        // azonnali ini-művelet az EditControlleren át
                        if (tool !== "crop" && tool !== "tilt")
                            editController.toggleTool(tool)
                    }
                    onUndoRequested: editController.undo()
                    onRedoRequested: editController.redo()
                    onCropRotateRequested: {
                        // rögzített aránynál a fekvő↔álló kapcsoló forgat
                        // (a kijelölés az arány-követéssel formálódik át);
                        // kézi aránynál közvetlenül a kijelölést forgatjuk
                        if (editorPanel.currentAspect > 0)
                            editorPanel.aspectRotated =
                                !editorPanel.aspectRotated
                        else
                            cropOverlay.swapSelectionOrientation()
                    }
                    // arány-választás/Forgatás: a meglévő kijelölés kövesse
                    onCurrentAspectChanged: {
                        if (cropOverlay.hasSelection
                            && editorPanel.currentAspect > 0)
                            cropOverlay.applyAspect(editorPanel.currentAspect)
                    }
                    onQuickCropRequested: (kind) => cropOverlay.selectPreset(kind)
                    onCropPreviewHold: (held) => cropOverlay.previewHold = held
                    onCropResetRequested: cropOverlay.resetSelection()
                    onCropApplyRequested: viewer.applyCrop(false)
                    onCropCancelRequested: {
                        cropOverlay.resetSelection()
                        editorPanel.cropActive = false
                    }
                }

                ColumnLayout {
                    anchors.top: editorPanel.bottom
                    anchors.left: parent.left; anchors.right: parent.right
                    anchors.margins: 10
                    spacing: 6
                    Label {
                        visible: editorPanel.tiltActive
                        text: qsTr("Straighten")
                        font.pixelSize: Theme.fontSize
                        color: Theme.textGray
                    }
                    // döntés-csúszka: −1..1 Picasa-egység (±11,5°); húzás
                    // közben élő előnézet (previewTilt, nincs ini-mentés,
                    // #72), elengedéskor ír + tol undo-lépést (setTilt)
                    Slider {
                        id: tiltSlider
                        objectName: "tiltSlider"
                        visible: editorPanel.tiltActive
                        from: -1; to: 1; value: 0
                        Layout.fillWidth: true
                        onValueChanged: if (editorPanel.tiltActive)
                                            editController.previewTilt(value)
                        onPressedChanged: if (!pressed && editorPanel.tiltActive)
                                              editController.setTilt(value)
                    }
                }
                Rectangle {
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left; anchors.right: parent.right
                    anchors.margins: 10
                    height: 90
                    color: "#f2f2f0"
                    border.color: Theme.chromeBorder
                    Text {
                        anchors.centerIn: parent
                        width: parent.width - 12
                        text: qsTr("Histogram and camera information")
                        font.pixelSize: Theme.fontSize - 1
                        color: Theme.textGray
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }

            // fő képterület
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#808080"

                WheelHandler {
                    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                    onWheel: function(event) { viewer.wheelStep(event.angleDelta.y) }
                }

                Item {
                    id: photoArea
                    anchors.fill: parent
                    anchors.margins: 14
                    anchors.bottomMargin: 30

                    Image {
                        id: photo
                        objectName: "viewerImage"
                        // a model.revision referencia miatt a kötés minden
                        // modell-frissítésnél újraértékelődik
                        readonly property int iniSteps: viewer.photosModel
                            ? (viewer.photosModel.revision,
                               viewer.photosModel.rotateAt(viewer.currentIndex))
                            : 0
                        anchors.centerIn: parent
                        // 90°/270°-nál a befoglaló doboz oldalai cserélődnek
                        width: iniSteps % 2 ? photoArea.height : photoArea.width
                        height: iniSteps % 2 ? photoArea.width : photoArea.height
                        rotation: iniSteps * 90
                        // nyitott szerkesztésnél a filters= láncot alkalmazó
                        // editpreview provider rendereli a képet (?rev=
                        // cache-buster minden módosításnál)
                        source: editController.previewSource !== ""
                                ? editController.previewSource
                                : viewer.urlAt(viewer.currentIndex)
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        autoTransform: true   // EXIF-orientáció
                        sourceSize.width: 2560
                    }

                    // vágó-overlay a kép TÉNYLEGESEN kirajzolt (letterbox
                    // nélküli) területén. Enter: elfogad + következő kép a
                    // vágó-mód megtartásával (sorozat-vágás, UX-alapelv 1);
                    // Esc: kilép a vágásból. MVP-korlát: ini-forgatott
                    // (rotate=) képnél a koordináták a megjelenített térben
                    // értendők — a forgatás+vágás kombináció a #21-ben pontosodik.
                    CropOverlay {
                        id: cropOverlay
                        parent: photo
                        visible: editorPanel.cropActive
                        aspectRatio: editorPanel.currentAspect
                        x: (photo.width - photo.paintedWidth) / 2
                        y: (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight
                        onVisibleChanged: {
                            if (visible) forceActiveFocus()
                            else viewer.forceActiveFocus()
                        }
                        // Enter-flow: elfogad ÉS következő kép, a vágó-mód
                        // megtartásával (sorozat-vágás, UX-alapelv 1)
                        onAccepted: function(r) {
                            viewer.applyCrop(true)
                            if (visible) forceActiveFocus()
                        }
                        onCancelled: {
                            cropOverlay.resetSelection()
                            editorPanel.cropActive = false
                        }
                    }
                }
                BusyIndicator {
                    anchors.centerIn: parent
                    running: photo.status === Image.Loading
                }
                // szerkeszthető felirat-sor — a model.revision referencia
                // miatt a kötés modell-frissítésnél (pl. mentés után)
                // újraértékelődik, ahogy a forgatás-kötés is (lásd fent).
                // Gépeléskor a Qt eltávolítja a deklaratív kötést a text
                // property-ről (közvetlen C++ írás), ezért elfogadás és
                // Esc után Qt.binding()-gel újra be kell kötni, különben a
                // mező a következő navigáláskor nem frissülne.
                TextInput {
                    id: captionField
                    objectName: "captionField"
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 8
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: Math.min(400, photoArea.width)
                    horizontalAlignment: TextInput.AlignHCenter
                    color: "#ffffff"
                    font.pixelSize: Theme.fontSize
                    selectByMouse: true
                    text: viewer.photosModel
                        ? (viewer.photosModel.revision,
                           viewer.photosModel.captionAt(viewer.currentIndex))
                        : ""

                    function rebind() {
                        text = Qt.binding(function () {
                            return viewer.photosModel
                                ? (viewer.photosModel.revision,
                                   viewer.photosModel.captionAt(viewer.currentIndex))
                                : ""
                        })
                    }

                    onAccepted: {
                        controller.setCaption(viewer.currentIndex, text)
                        rebind()
                        viewer.forceActiveFocus()
                    }
                    Keys.onEscapePressed: (event) => {
                        rebind()
                        viewer.forceActiveFocus()
                        event.accepted = true
                    }
                }
                Text {
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 8
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: qsTr("Make a caption!")
                    color: "#e8e8e8"
                    font.pixelSize: Theme.fontSize
                    visible: captionField.text.length === 0 && !captionField.activeFocus
                }

                // elő-betöltés: a szomszédok már dekódolva, mire lépsz —
                // a #84 óta a mappán belüli szomszéd (folderNeighbor), nem
                // a nyers currentIndex±1, hogy ne a szomszéd mappa képét
                // töltsük elő feleslegesen a mappahatárnál
                Image {
                    visible: false
                    source: viewer.photosModel
                        ? viewer.urlAt(viewer.photosModel.folderNeighbor(viewer.currentIndex, 1))
                        : ""
                    asynchronous: true; autoTransform: true
                    sourceSize.width: 2560
                }
                Image {
                    visible: false
                    source: viewer.photosModel
                        ? viewer.urlAt(viewer.photosModel.folderNeighbor(viewer.currentIndex, -1))
                        : ""
                    asynchronous: true; autoTransform: true
                    sourceSize.width: 2560
                }
            }
        }
    }
}
