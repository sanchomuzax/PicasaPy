import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő „Szöveg" panelje (#148/#450): a szövegmező, a betűméret és
// az átlátszóság csúszkája, a kitöltés-/körvonalszín választója, valamint a
// saját Alkalmaz/Mégse pár.
//
// #496: kiemelve az EditorPanel.qml-ből — a gazda-panelre a `panel`
// tulajdonságon át hivatkozik (a `FolderStatePanel.qml` `manager`-mintája).
ColumnLayout {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    objectName: "textColumn"
    visible: panel.textActive
    opacity: panel.enabled ? 1 : 0.45
    anchors.margins: 10
    spacing: 8

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        Image {
            Layout.preferredWidth: 40
            Layout.preferredHeight: 30
            source: "../../assets/tools/text.png"
        }
        Text {
            Layout.fillWidth: true
            text: qsTr("Text")
            font.pixelSize: Theme.fontSize + 3
            color: Theme.ink
        }
    }

    Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: qsTr("Type your text, then click on the photo to place it.")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    TextField {
        id: textContentField
        objectName: "textContentField"
        Layout.fillWidth: true
        text: panel.textDraftContent
        onTextChanged: panel.textDraftEdited(text)
        // #422: jobbklikk-menü (Picasa `Address`)
        TextFieldContextArea {}
    }

    // #450: a kép meglévő feliratát tölti a szövegmezőbe — feliratozatlan
    // képnél a gomb tiltott (a jegy szó szerinti szövege szerint)
    PanelButton {
        objectName: "textCopyCaptionButton"
        Layout.fillWidth: true
        label: qsTr("Copy Caption")
        tooltip: qsTr("Add text based on the picture's caption")
        buttonEnabled: panel.captionText.length > 0
        onButtonClicked: panel.textCopyCaptionRequested()
    }

    // #450: kitöltés-szín ÉS körvonal-szín, egymástól függetlenül — a
    // betűtípus-lista/méret/félkövér-dőlt-aláhúzott/igazítás ehhez a
    // lépcsőhöz NEM tartozik (valódi TrueType-rajzolót igényelne, ma
    // Hershey-fonttal rajzolunk — ld. #450 jegy).
    RowLayout {
        Layout.fillWidth: true
        spacing: 10
        ColumnLayout {
            spacing: 4
            Text {
                text: qsTr("Text color")
                font.pixelSize: Theme.fontSize - 1
                color: Theme.textGray
            }
            TextColorSwatches {
                objectName: "textFillColorSwatches"
                currentColor: panel.textFillColor
                onColorPicked: (hex) => panel.textFillColorEdited(hex)
            }
        }
        ColumnLayout {
            spacing: 4
            Text {
                text: qsTr("Outline color")
                font.pixelSize: Theme.fontSize - 1
                color: Theme.textGray
            }
            TextColorSwatches {
                objectName: "textOutlineColorSwatches"
                currentColor: panel.textOutlineColor
                onColorPicked: (hex) => panel.textOutlineColorEdited(hex)
            }
        }
    }

    CheckBox {
        id: textFillDisabledCheck
        objectName: "textFillDisabledCheck"
        Layout.fillWidth: true
        text: qsTr("Don't show the solid fill color (show outline only)")
        checked: !panel.textFillEnabled
        onToggled: panel.textFillEnabledEdited(!checked)
    }

    Label {
        text: qsTr("Outline thickness")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }
    PicasaSlider {
        id: textOutlineThicknessSlider
        objectName: "textOutlineThicknessSlider"
        Layout.fillWidth: true
        from: 0; to: 8
        stepSize: 1
        value: panel.textOutlineThickness
        onMoved: panel.textOutlineThicknessEdited(value)
    }

    Label {
        text: qsTr("Opacity")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }
    PicasaSlider {
        id: textOpacitySlider
        objectName: "textOpacitySlider"
        Layout.fillWidth: true
        from: 0; to: 1
        value: panel.textOpacity
        onMoved: panel.textOpacityEdited(value)
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        PanelButton {
            objectName: "textApplyButton"
            label: qsTr("Apply") + " ✔"
            buttonEnabled: panel.textPlacementPending
                          && textContentField.text.length > 0
            onButtonClicked: panel.textApplyRequested()
        }
        PanelButton {
            objectName: "textCancelButton"
            label: qsTr("Cancel") + " ✘"
            onButtonClicked: panel.textCancelRequested()
        }
    }

    // #450: az összes szövegelem törlése — ma egyetlen szövegelem van,
    // a meglévő clearText (Visszavonás-verem NÉLKÜLI, azonnali) útvonalon
    PanelButton {
        objectName: "textRemoveAllButton"
        Layout.fillWidth: true
        label: qsTr("Remove all existing text")
        buttonEnabled: panel.hasTextOverlay
        onButtonClicked: panel.textRemoveAllRequested()
    }
}
