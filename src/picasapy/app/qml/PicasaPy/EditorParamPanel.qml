import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Az effekt-paraméter alpanel (#316): bármelyik effekt-fülön megnyílhat, és
// az adott fül rácsát fedi el ugyanazon a helyen — a visszatérés ugyanarra
// a fülre történik, mert az `activeTab` változatlan marad.
//
// #464 (ugyanaz a túlcsordulás-osztály, mint az effekt-füleknél): a sok
// paraméteres effektek (pl. Vignetta) alpanelje magasabb lehet a
// rendelkezésre álló helynél — ezért görgethető.
//
// #496: az `EditorPanel.qml`-ből kiemelve, viselkedés-semlegesen. A
// láthatóságot és a horgonyokat — a fülek mintája szerint — a gazda adja
// meg a használat helyén.
Flickable {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    // A csúszka-feliratok fordítása (#316): a `label` a Pythonból
    // (`app/effect_params.py`) angol kulcsszövegként érkezik — a lupdate ezt
    // nem látja, ezért itt statikus `qsTr(...)` hívásokkal soroljuk fel az
    // ÖSSZES lehetséges feliratot; az ismeretlent változatlanul adjuk vissza.
    //
    // #496: ez a segéd ide, az EGYETLEN hívója mellé került (korábban az
    // `EditorPanel.qml`-ben állt, ami a 800 soros korlát fölé nőtt). A gazda
    // vékony `paramLabel()`-je ezt hívja tovább, hogy a meglévő tesztek
    // változatlanul a panelen szólíthassák meg.
    function paramLabel(key) {
        switch (key) {
        case "Amount": return qsTr("Amount")
        case "Saturation": return qsTr("Saturation")
        case "Inner Radius": return qsTr("Inner Radius")
        case "Strength": return qsTr("Strength")
        case "Intensity": return qsTr("Intensity")
        case "Radius": return qsTr("Radius")
        case "Center X": return qsTr("Center X")
        case "Center Y": return qsTr("Center Y")
        case "Size": return qsTr("Size")
        case "Sharpness": return qsTr("Sharpness")
        case "Preserve Color": return qsTr("Preserve Color")
        case "Gradient": return qsTr("Gradient")
        case "Shade": return qsTr("Shade")
        case "Block Size": return qsTr("Block Size")
        case "Blur Radius": return qsTr("Blur Radius")
        case "Brightness": return qsTr("Brightness")
        case "Color Mix": return qsTr("Color Mix")
        case "Edge Strength": return qsTr("Edge Strength")
        case "Posterize": return qsTr("Posterize")
        case "Smoothness": return qsTr("Smoothness")
        case "Width": return qsTr("Width")
        case "Border Width": return qsTr("Border Width")
        case "Angle": return qsTr("Angle")
        case "Blur": return qsTr("Blur")
        case "Line Position": return qsTr("Line Position")
        // #516: a filterdesc-registry.md 4.2 táblázatából átvezetett
        // vezérlők feliratai
        case "Grain": return qsTr("Grain")
        case "Contrast": return qsTr("Contrast")
        case "Bloom": return qsTr("Bloom")
        case "Steps": return qsTr("Steps")
        case "Smoothing": return qsTr("Smoothing")
        case "Impact": return qsTr("Impact")
        case "Blend Mode": return qsTr("Blend Mode")
        case "Hue": return qsTr("Hue")
        case "Rotate": return qsTr("Rotate")
        case "Fade": return qsTr("Fade")
        case "Color": return qsTr("Color")
        case "Outer Color": return qsTr("Outer Color")
        case "Inner Color": return qsTr("Inner Color")
        case "Black Color": return qsTr("Black Color")
        case "White Color": return qsTr("White Color")
        case "Outer Thickness": return qsTr("Outer Thickness")
        case "Inner Thickness": return qsTr("Inner Thickness")
        case "Corner Radius": return qsTr("Corner Radius")
        case "Caption Height": return qsTr("Caption Height")
        case "Distance": return qsTr("Distance")
        case "Shadow Color": return qsTr("Shadow Color")
        case "Background Color": return qsTr("Background Color")
        case "Rounded": return qsTr("Rounded")
        case "Lighten": return qsTr("Lighten")
        default: return key
        }
    }
    objectName: "editorEffectParamScroll"
    anchors.bottomMargin: 6
    clip: true
    contentWidth: width
    contentHeight: effectParamColumn.implicitHeight + 20
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: PicasaScrollBar {}

    ColumnLayout {
        id: effectParamColumn
        objectName: "effectParamColumn"
        opacity: panel.enabled ? 1 : 0.45
        anchors.margins: 10
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            height: 22
            color: Theme.panelHeaderBg
            Text {
                objectName: "effectParamTitle"
                anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                text: panel.paramEffectName
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.panelHeaderText
            }
        }

        Repeater {
            objectName: "effectParamRepeater"
            model: panel.paramEffectParams

            // #516: a katalógus 3 vezérlő-fajtát ismer — "slider" (számtar-
            // tomány), "checkbox" (jelölőnégyzet) és "color" (színválasztó,
            // a #450 szöveg-eszköz `TextColorSwatches`-ának mintájára). Egy
            // delegate-en belül mindhárom ág megvan, csak a `kind` szerint
            // látszik az egyik — így a Repeater indexelése (és vele a
            // `panel.updateParamValue(index, …)` pozíció-egyeztetés)
            // változatlan marad, akármilyen a vezérlő-keverék.
            delegate: ColumnLayout {
                id: paramRow
                required property var modelData
                required property int index
                Layout.fillWidth: true
                spacing: 2

                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        objectName: "effectParamLabel" + paramRow.index
                        Layout.fillWidth: true
                        text: panel.paramLabel(paramRow.modelData.label)
                        font.pixelSize: Theme.fontSize - 1
                        color: Theme.textGray
                    }
                    Label {
                        objectName: "effectParamValue" + paramRow.index
                        text: paramSlider.value.toFixed(2)
                        font.pixelSize: Theme.fontSize - 1
                        color: Theme.textGray
                    }
                }
                PicasaSlider {
                    id: paramSlider
                    objectName: "effectParamSlider" + paramRow.index
                    Layout.fillWidth: true
                    from: paramRow.modelData.minimum
                    to: paramRow.modelData.maximum
                    stepSize: paramRow.modelData.step
                    value: paramRow.modelData.default
                    // húzás/kattintás közben élő előnézet (#316) — a
                    // programozott kezdőérték-beállítás NEM vált ki `moved`
                    // jelet, csak a valódi felhasználói interakció
                    onMoved: panel.updateParamValue(paramRow.index, paramSlider.value)
                }
                CheckBox {
                    id: paramCheckbox
                    objectName: "effectParamCheckbox" + paramRow.index
                    text: panel.paramLabel(paramRow.modelData.label)
                    checked: paramRow.modelData.default !== 0
                    onToggled: panel.updateParamValue(paramRow.index, paramCheckbox.checked ? 1 : 0)
                }
                TextColorSwatches {
                    id: paramColorSwatches
                    objectName: "effectParamColor" + paramRow.index
                    // #305 null-őr: régebbi/fake vezérlők (pl. teszt-dupla)
                    // "color" mező nélküli payloadot is küldhetnek
                    currentColor: paramRow.modelData.color ? paramRow.modelData.color : "#000000"
                    onColorPicked: (hex) => panel.updateParamValue(paramRow.index, hex)
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "effectParamApplyButton"
                label: qsTr("Apply")
                onButtonClicked: panel.applyParamPanel()
            }
            PanelButton {
                objectName: "effectParamCancelButton"
                label: qsTr("Cancel")
                onButtonClicked: panel.cancelParamPanel()
            }
        }
    }
}
