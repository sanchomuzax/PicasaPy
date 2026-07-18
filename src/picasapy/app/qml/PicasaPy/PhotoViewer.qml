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
            editController.endEdit()
            editorPanel.cropActive = false
            editorPanel.tiltActive = false
        }
    }
    onCurrentIndexChanged: {
        if (visible) {
            beginEditCurrent()
            tiltSlider.value = 0
        }
    }
    Connections {
        target: editController
        function onToolsChanged() { viewer.syncPanelFromController() }
    }
    function next() {
        if (currentIndex < photoCount - 1) currentIndex += 1
    }
    function previous() {
        if (currentIndex > 0) currentIndex -= 1
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
                    text: "◀"; onClicked: viewer.previous()
                    enabled: viewer.currentIndex > 0
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
                    text: "▶"; onClicked: viewer.next()
                    enabled: viewer.currentIndex < viewer.photoCount - 1
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
                    height: 180
                    onToolActivated: function(tool) {
                        // crop/tilt helyi mód (overlay/csúszka); a többi
                        // azonnali ini-művelet az EditControlleren át
                        if (tool !== "crop" && tool !== "tilt")
                            editController.toggleTool(tool)
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
                    // döntés-csúszka: −1..1 Picasa-egység (±11,5°);
                    // elengedéskor ír — húzás közben nem spammeljük az init
                    Slider {
                        id: tiltSlider
                        objectName: "tiltSlider"
                        visible: editorPanel.tiltActive
                        from: -1; to: 1; value: 0
                        Layout.fillWidth: true
                        onPressedChanged: if (!pressed && editorPanel.tiltActive)
                                              editController.setTilt(value)
                    }
                    RowLayout {
                        PicasaButton { text: qsTr("Undo"); enabled: false; Layout.fillWidth: true }
                        PicasaButton { text: qsTr("Redo"); enabled: false; Layout.fillWidth: true }
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
                        x: (photo.width - photo.paintedWidth) / 2
                        y: (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight
                        onVisibleChanged: {
                            if (visible) forceActiveFocus()
                            else viewer.forceActiveFocus()
                        }
                        onAccepted: function(r) {
                            editController.applyCrop(r.x, r.y, r.width, r.height)
                            cropRect = Qt.rect(0.1, 0.1, 0.8, 0.8)
                            viewer.next()
                            if (visible) forceActiveFocus()
                        }
                        onCancelled: editorPanel.cropActive = false
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

                // elő-betöltés: a szomszédok már dekódolva, mire lépsz
                Image {
                    visible: false
                    source: viewer.urlAt(viewer.currentIndex + 1)
                    asynchronous: true; autoTransform: true
                    sourceSize.width: 2560
                }
                Image {
                    visible: false
                    source: viewer.urlAt(viewer.currentIndex - 1)
                    asynchronous: true; autoTransform: true
                    sourceSize.width: 2560
                }
            }
        }
    }
}
