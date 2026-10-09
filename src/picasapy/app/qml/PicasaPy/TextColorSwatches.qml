import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Közös színválasztó a szöveg- és effekt-színekhez (#450/#4548): a fix
// paletta mellett szabad spektrumválasztás és előzmény-sor is elérhető; a
// kijelölt szín kék kerettel jelölt.
//
// #496: kiemelve az EditorPanel.qml-ből (ld. ott a `ToolTile` megjegyzését).
//
// #775: NÉGYOSZLOPOS rács (2 sor), nem egysoros. Egysorban a 8 mező
// (8 × 16 + 7 × 3 = 149 px) két, egymás mellett álló példánnyal (kitöltés-
// és körvonalszín) 308 px-et igényelt — ennyi a szerkesztő bal paneljének
// SEHOL nem áll rendelkezésre (a tartalom-oszlop 260, a belső margókkal
// 240). A 4×2-es elrendezés ugyanazt a 8 színt, ugyanakkora (16×16)
// mezőkkel mutatja, de a szélesség-igénye 73 px-re esik — bőven elfér két
// példánnyal is.
Item {
    id: swatches
    // #4283/#4548: az effekt- és a szöveg-színválasztóban is látható az MRU-sor.
    property bool showRecentColors: false
    property string currentColor: "#ffffff"
    property string displayedColor: currentColor
    readonly property bool spectrumPickerVisible:
        spectrumPickerLoader.item ? spectrumPickerLoader.item.visible : false
    readonly property real spectrumPickerWidth:
        spectrumPickerLoader.item ? spectrumPickerLoader.item.width : 225
    readonly property real spectrumPickerHeight:
        spectrumPickerLoader.item ? spectrumPickerLoader.item.height : 225
    readonly property real spectrumSceneX:
        spectrumPickerLoader.item
            ? spectrumPickerLoader.item.x
                + spectrumPickerLoader.item.spectrumFieldItem.x : 0
    readonly property real spectrumSceneY:
        spectrumPickerLoader.item
            ? spectrumPickerLoader.item.y
                + spectrumPickerLoader.item.spectrumFieldItem.y : 0
    readonly property real spectrumWidth:
        spectrumPickerLoader.item
            ? spectrumPickerLoader.item.spectrumFieldItem.width : 181
    readonly property real spectrumHeight:
        spectrumPickerLoader.item
            ? spectrumPickerLoader.item.spectrumFieldItem.height : 147
    readonly property real hueSceneX:
        spectrumPickerLoader.item
            ? spectrumPickerLoader.item.x
                + spectrumPickerLoader.item.hueSpectrumItem.x : 0
    readonly property real hueSceneY:
        spectrumPickerLoader.item
            ? spectrumPickerLoader.item.y
                + spectrumPickerLoader.item.hueSpectrumItem.y : 0
    readonly property real hueWidth:
        spectrumPickerLoader.item
            ? spectrumPickerLoader.item.hueSpectrumItem.width : 181
    signal colorPicked(string hex)
    // #506: a "palette" néven elnevezve elfedte az Item/Control
    // beépített `palette` tulajdonságát (Qt-figyelmeztetés induláskor)
    // — átnevezve `swatchColors`-ra.
    readonly property var swatchColors: [
        "#ffffff", "#000000", "#ff0000", "#ffff00",
        "#00a651", "#0072bc", "#ff7f27", "#a349a4"
    ]
    readonly property var recentColors:
        showRecentColors && typeof editController !== "undefined" && editController
                && editController.recentPickerColors !== undefined
            ? editController.recentPickerColors : ["", "", "", "", ""]
    implicitWidth: showRecentColors ? 225 : 103
    implicitHeight: showRecentColors ? 85 : 35

    onCurrentColorChanged: displayedColor = currentColor

    function rememberColor(hex) {
        if (typeof editController !== "undefined" && editController
                && typeof editController.rememberPickerColor === "function")
            editController.rememberPickerColor(String(hex))
    }

    function chooseColor(hex) {
        displayedColor = String(hex)
        colorPicked(displayedColor)
        if (showRecentColors)
            rememberColor(displayedColor)
    }

    function closeSpectrumPicker() {
        if (spectrumPickerLoader.item)
            spectrumPickerLoader.item.close()
    }

    function openSpectrumPicker() {
        if (spectrumPickerLoader.item)
            spectrumPickerLoader.item.open()
        else
            spectrumPickerLoader.active = true
    }

    GridLayout {
        id: palette
        x: swatches.showRecentColors ? 20 : 0
        y: swatches.showRecentColors ? 50 : 0
        columns: 4
        rowSpacing: 3
        columnSpacing: 3
        Repeater {
            model: swatches.swatchColors
            delegate: Rectangle {
                required property string modelData
                required property int index
                objectName: swatches.objectName + "Swatch" + index
                width: 16; height: 16; radius: 2
                color: modelData
                border.width: modelData.toLowerCase() === swatches.displayedColor.toLowerCase() ? 2 : 1
                border.color: modelData.toLowerCase() === swatches.displayedColor.toLowerCase()
                              ? Theme.selectionBlue : Theme.chromeBorder
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        swatches.chooseColor(modelData)
                    }
                }
            }
        }
    }

    Rectangle {
        id: spectrumButton
        objectName: swatches.objectName + "SpectrumButton"
        x: swatches.showRecentColors ? 20 : 77
        y: swatches.showRecentColors ? 15 : 4
        width: 26
        height: 26
        radius: 13
        color: Theme.buttonBg
        border.width: 1
        border.color: Theme.chromeBorder
        ToolTip.text: qsTr("Pick Color")
        ToolTip.visible: spectrumButtonMouse.containsMouse
        ToolTip.delay: Theme.tooltipDelay

        Rectangle {
            anchors.fill: parent
            anchors.margins: 4
            radius: width / 2
            clip: true
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.00; color: "#ff0000" }
                GradientStop { position: 0.17; color: "#ffff00" }
                GradientStop { position: 0.33; color: "#00ff00" }
                GradientStop { position: 0.50; color: "#00ffff" }
                GradientStop { position: 0.67; color: "#0000ff" }
                GradientStop { position: 0.83; color: "#ff00ff" }
                GradientStop { position: 1.00; color: "#ff0000" }
            }
        }

        MouseArea {
            id: spectrumButtonMouse
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: swatches.openSpectrumPicker()
        }
    }

    Loader {
        id: spectrumPickerLoader
        active: false
        sourceComponent: Component {
            ColorSpectrumPicker {
                objectName: swatches.objectName + "Picker"
                anchorItem: swatches
                currentColor: swatches.displayedColor
                recentColors: swatches.recentColors
                onColorPicked: (hex) => swatches.chooseColor(hex)
            }
        }
        onLoaded: item.open()
    }

    Repeater {
        model: swatches.showRecentColors ? swatches.recentColors : []
        delegate: Rectangle {
            required property string modelData
            required property int index
            objectName: swatches.objectName + "Recent" + index
            property string recentColor: modelData || ""
            // A `pickerpanel/mru_0` az első hely; az eredeti 31 px-es
            // osztás és a 26 × 26-os mező a szerkesztőpanel méretspecéből jön.
            x: 51 + index * 31
            y: 15
            width: 26
            height: 26
            color: recentColor === "" ? "transparent" : recentColor
            border.width: recentColor !== ""
                          && recentColor.toLowerCase() === swatches.displayedColor.toLowerCase()
                          ? 2 : 1
            border.color: recentColor !== ""
                          && recentColor.toLowerCase() === swatches.displayedColor.toLowerCase()
                          ? Theme.selectionBlue : Theme.chromeBorder
            MouseArea {
                anchors.fill: parent
                enabled: parent.recentColor !== ""
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    var color = parent.recentColor
                    swatches.chooseColor(color)
                }
            }
        }
    }
}
