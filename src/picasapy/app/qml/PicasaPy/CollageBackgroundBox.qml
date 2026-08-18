import QtQuick
import QtQuick.Controls

// A „Háttér beállításai" csoport a kollázs beállítás-lapján (#946).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` 4.2/6–10. és
// `picasa-kollazs-felulet.md` **3.** („a háttér — három mód, nem kettő").
//
// A rádiócsoport KÉT gombot mutat (`Egyszínű`, `Kép használata`), de a
// modell HÁROM hátteret ismer: a harmadik a képek átlagszíne
// (`collage::avgcolor`), amit a vezérlő `solid`-ként ír a `.cxf`-be. A
// felületen ezért nincs harmadik rádiógomb — aki ide újat tesz, olyan
// vezérlőt épít, ami az eredetiben nincs.
//
// A `color_bg` az alapértelmezés (`.tre`: `Property setpressed 1`), és
// mindkét gomb `showtarget`-tel kapcsolja a saját dobozát: a színválasztó
// és a háttérkép-doboz UGYANAZT a helyet foglalja (134, 180).
//
// A komponens a LAP teljes területét kitölti, és a gyerekeit a spec
// lap-relatív koordinátáival helyezi el — a fájlban álló számok így egy az
// egyben a `.tre` számai.
Item {
    id: box

    //: A vezérlő (AppController + CollageMixin).
    property var controller: null

    readonly property string mode:
        box.controller ? box.controller.collageBackgroundMode : "solid"

    readonly property color currentColor:
        box.controller ? box.controller.collageBackgroundColor : "#000000"

    readonly property string currentImage:
        box.controller ? box.controller.collageBackgroundImage : ""

    //: Nyitva van-e a felugró paletta (`picker_panel`, a `.tre`-ben `m_hidden`).
    property bool paletteOpen: false

    function pickMode(kind) {
        if (box.controller)
            box.controller.setCollageBackgroundMode(kind)
    }

    function pickColor(hex) {
        box.paletteOpen = false
        if (box.controller)
            box.controller.setCollageBackgroundColor(hex)
    }

    //: A felugró paletta színei — öt sor: szürkék, meleg, zöld, kék, lila/barna.
    readonly property var swatchColors: [
        "#000000", "#333333", "#555555", "#777777",
        "#999999", "#bbbbbb", "#dddddd", "#ffffff",
        "#8b1a1a", "#c0392b", "#e74c3c", "#e67e22",
        "#f39c12", "#f1c40f", "#f7dc6f", "#fdebd0",
        "#145a32", "#1e8449", "#27ae60", "#2ecc71",
        "#7dcea0", "#a9dfbf", "#d5f5e3", "#eafaf1",
        "#154360", "#1f618d", "#2980b9", "#3498db",
        "#7fb3d5", "#aed6f1", "#d6eaf8", "#ebf5fb",
        "#4a235a", "#6c3483", "#8e44ad", "#a569bd",
        "#7b4f2b", "#a9744f", "#c8a27a", "#e6d3b3"
    ]

    // --- 6. cím -------------------------------------------------------------

    Text {
        objectName: "collageBkgTitle"
        x: 3
        y: 159
        width: 239
        height: 15
        text: qsTr("Background Options")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
        verticalAlignment: Text.AlignVCenter
    }

    // --- 7. a két rádiógomb -------------------------------------------------

    Item {
        objectName: "collageBackgroundTypes"
        x: 6
        y: 178
        width: 127
        height: 55

        // A rádiógomb maga 24 × 24; a felirat KÜLÖN elem (a `.tre` így méri),
        // de a `m_hit_childlabel` miatt a feliratra kattintva is kapcsol.
        //
        // ⚠️ Miért nem `QtQuick.Controls.RadioButton`: az saját `checked`
        // állapotot tart, és kattintáskor MAGA írja felül — ezzel elszakítja
        // a `collageBackgroundMode`-hoz kötött binding-et, tehát a vezérlő
        // állapota és a felület első kattintás után szétcsúszhat. Itt a
        // vezérlő az EGYETLEN igazságforrás: a `checked` mindig belőle
        // számolódik, a kattintás pedig csak kér.
        component ModeRadio: Item {
            id: radio
            property string modeKey: ""
            readonly property bool checked: box.mode === radio.modeKey
            width: 24
            height: 24
            Rectangle {
                x: 5
                y: 5
                width: 14
                height: 14
                radius: 7
                color: Theme.controlBase
                border.width: 1
                border.color: Theme.chromeBorder
                Rectangle {
                    anchors.centerIn: parent
                    visible: radio.checked
                    width: 8
                    height: 8
                    radius: 4
                    color: Theme.ink
                }
            }
            MouseArea {
                anchors.fill: parent
                onClicked: box.pickMode(radio.modeKey)
            }
        }

        ModeRadio {
            objectName: "collageColorBgRadio"
            modeKey: "solid"
            x: 0
            y: 1
        }
        Text {
            objectName: "collageColorBgLabel"
            x: 25
            y: 4
            width: 101
            height: 24
            text: qsTr("Solid Color")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            verticalAlignment: Text.AlignVCenter
            MouseArea {
                anchors.fill: parent
                onClicked: box.pickMode("solid")
            }
        }

        ModeRadio {
            objectName: "collageBitmapBgRadio"
            modeKey: "image"
            x: 0
            y: 28
        }
        Text {
            objectName: "collageBitmapBgLabel"
            x: 25
            y: 31
            width: 101
            height: 24
            text: qsTr("Use Image")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            verticalAlignment: Text.AlignVCenter
            MouseArea {
                anchors.fill: parent
                onClicked: box.pickMode("image")
            }
        }
    }

    // --- 8. a színválasztó doboz (csak `Egyszínű`) --------------------------

    Item {
        objectName: "collageColorPickContainer"
        visible: box.mode === "solid"
        x: 134
        y: 180
        width: 49
        height: 49
    }

    Rectangle {
        objectName: "collageColorCircle"
        visible: box.mode === "solid"
        x: 140
        y: 186
        width: 37
        height: 37
        // a `.tre` `Property round 3`: kör, nem lekerekített négyzet
        radius: 18.5
        color: box.currentColor
        border.width: 1
        border.color: Theme.chromeBorder
        MouseArea {
            anchors.fill: parent
            onClicked: box.paletteOpen = !box.paletteOpen
        }
    }

    Image {
        objectName: "collageDropperIcon"
        visible: box.mode === "solid"
        // a pipetta a színválasztó dobozon KÍVÜLRE lóg (180, 198) — a
        // `.tre` így méri; nem a doboz gyereke
        x: 180
        y: 198
        width: 24
        height: 14
        source: "icons/pipetta.svg"
        sourceSize.width: 24
        sourceSize.height: 14
        fillMode: Image.PreserveAspectFit
        MouseArea {
            anchors.fill: parent
            onClicked: box.paletteOpen = !box.paletteOpen
        }
    }

    // --- 9. a háttérkép-doboz (csak `Kép használata`) -----------------------

    Item {
        objectName: "collageBackgroundContainer"
        visible: box.mode === "image"
        x: 134
        y: 180
        width: 135
        height: 49
    }

    Rectangle {
        objectName: "collageCurrentBackground"
        visible: box.mode === "image"
        x: 140
        y: 186
        width: 37
        height: 37
        color: Theme.controlBase
        border.width: 1
        border.color: Theme.chromeBorder
        Image {
            anchors.fill: parent
            anchors.margins: 1
            source: box.currentImage ? "file://" + box.currentImage : ""
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            clip: true
        }
    }

    PicasaButton {
        objectName: "collageBkgFromSelection"
        visible: box.mode === "image"
        x: 185
        y: 186
        width: 71
        height: 37
        padding: 2
        horizontalPadding: 2
        text: qsTr("Use selected")
        onClicked: if (box.controller) box.controller.setBackgroundFromSelection()
    }

    // --- 10. a felugró paletta ---------------------------------------------

    Rectangle {
        objectName: "collagePickerPanel"
        visible: box.paletteOpen && box.mode === "solid"
        x: 48
        y: 9
        width: 218
        height: 178
        color: Theme.contentPanel
        border.width: 1
        border.color: Theme.chromeBorder
        // a lap többi vezérlője fölé
        z: 200

        Grid {
            id: swatchGrid
            x: 5
            y: 5
            columns: 8
            spacing: 2

            Repeater {
                model: box.swatchColors
                delegate: Rectangle {
                    id: swatch
                    required property string modelData
                    required property int index
                    objectName: "collagePickerSwatch" + index
                    width: 24
                    height: 24
                    color: swatch.modelData
                    border.width:
                        swatch.modelData.toLowerCase()
                        === box.currentColor.toString().toLowerCase() ? 2 : 1
                    border.color:
                        swatch.modelData.toLowerCase()
                        === box.currentColor.toString().toLowerCase()
                            ? Theme.thumbSelection : Theme.chromeBorder
                    MouseArea {
                        anchors.fill: parent
                        onClicked: box.pickColor(swatch.modelData)
                    }
                }
            }
        }
    }
}
