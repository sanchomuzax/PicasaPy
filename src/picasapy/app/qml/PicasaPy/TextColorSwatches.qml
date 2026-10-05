import QtQuick
import QtQuick.Layouts

// Rögzített, PicasaPy-saját színpaletta a szöveg-eszközhöz (#450) — a
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
    // #4283: a közös effekt-színválasztóban jelenik meg az eredeti MRU-sor;
    // a szövegeszköz saját, kompakt palettája ezt nem bővíti ki.
    property bool showRecentColors: false
    property string currentColor: "#ffffff"
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
    implicitWidth: showRecentColors ? 225 : 73
    implicitHeight: showRecentColors ? 85 : 35

    function rememberColor(hex) {
        if (typeof editController !== "undefined" && editController
                && typeof editController.rememberPickerColor === "function")
            editController.rememberPickerColor(String(hex))
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
                border.width: modelData.toLowerCase() === swatches.currentColor.toLowerCase() ? 2 : 1
                border.color: modelData.toLowerCase() === swatches.currentColor.toLowerCase()
                              ? Theme.selectionBlue : Theme.chromeBorder
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (swatches.showRecentColors)
                            swatches.rememberColor(modelData)
                        swatches.colorPicked(modelData)
                    }
                }
            }
        }
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
                          && recentColor.toLowerCase() === swatches.currentColor.toLowerCase()
                          ? 2 : 1
            border.color: recentColor !== ""
                          && recentColor.toLowerCase() === swatches.currentColor.toLowerCase()
                          ? Theme.selectionBlue : Theme.chromeBorder
            MouseArea {
                anchors.fill: parent
                enabled: parent.recentColor !== ""
                onClicked: {
                    var color = parent.recentColor
                    swatches.colorPicked(color)
                    // A MRU-jel frissítése új Repeater-elemet építhet, ezért
                    // az objektumot törlő műveletnek kell az utolsónak lennie.
                    swatches.rememberColor(color)
                }
            }
        }
    }
}
