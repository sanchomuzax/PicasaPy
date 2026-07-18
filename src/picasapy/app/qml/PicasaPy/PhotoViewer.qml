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

            // bal eszközpanel — 2. fázisig placeholder, de dizájn-hű
            Rectangle {
                Layout.preferredWidth: 230
                Layout.fillHeight: true
                color: Theme.chromeBg
                ColumnLayout {
                    anchors.top: parent.top
                    anchors.left: parent.left; anchors.right: parent.right
                    anchors.margins: 10
                    spacing: 6
                    GridLayout {
                        columns: 2
                        columnSpacing: 6; rowSpacing: 6
                        Layout.fillWidth: true
                        PicasaButton { text: qsTr("Crop"); enabled: false; Layout.fillWidth: true }
                        PicasaButton { text: qsTr("Straighten"); enabled: false; Layout.fillWidth: true }
                        PicasaButton { text: qsTr("Redeye"); enabled: false; Layout.fillWidth: true }
                        PicasaButton { text: qsTr("I'm Feeling Lucky"); enabled: false; Layout.fillWidth: true }
                        PicasaButton { text: qsTr("Auto Contrast"); enabled: false; Layout.fillWidth: true }
                        PicasaButton { text: qsTr("Auto Color"); enabled: false; Layout.fillWidth: true }
                        PicasaButton { text: qsTr("Retouch"); enabled: false; Layout.fillWidth: true }
                        PicasaButton { text: qsTr("Text"); enabled: false; Layout.fillWidth: true }
                    }
                    Label {
                        text: qsTr("Fill Light")
                        font.pixelSize: Theme.fontSize
                        color: Theme.textGray
                    }
                    Slider { enabled: false; Layout.fillWidth: true }
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
                        source: viewer.urlAt(viewer.currentIndex)
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        autoTransform: true   // EXIF-orientáció
                        sourceSize.width: 2560
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
