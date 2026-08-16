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
GridLayout {
    id: swatches
    property string currentColor: "#ffffff"
    signal colorPicked(string hex)
    // #506: a "palette" néven elnevezve elfedte az Item/Control
    // beépített `palette` tulajdonságát (Qt-figyelmeztetés induláskor)
    // — átnevezve `swatchColors`-ra.
    readonly property var swatchColors: [
        "#ffffff", "#000000", "#ff0000", "#ffff00",
        "#00a651", "#0072bc", "#ff7f27", "#a349a4"
    ]
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
                onClicked: swatches.colorPicked(modelData)
            }
        }
    }
}
