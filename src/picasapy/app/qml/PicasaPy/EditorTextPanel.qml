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

    // #450 (2. lépcső): tipográfia — betűcsalád, méret, félkövér/dőlt/
    // aláhúzott és igazítás. A rajzoló ehhez már TrueType-ot használ
    // (`render.text_fonts`); ha a gépen nincs ilyen betű, a vezérlők
    // hatástalanok maradnak, de a szöveg akkor is megjelenik.
    // #779 (Windows CI): a `Layout.fillWidth` NÉLKÜLI felirat a saját — a
    // betűkészlettől függő — szélességét KÖTELEZŐ minimumként adja az
    // oszlopnak, és ezzel az EGÉSZ panelt szélesebbre feszítheti a
    // tartalom-oszlopnál. A linuxos futáson ez befért, a szélesebb windowsos
    // rendszerbetűvel (Segoe UI) nem. Kitöltővé téve a felirat a
    // rendelkezésre álló helyhez igazodik, a panel minimumát nem húzza föl.
    // Ugyanez az oka az alábbi `Label`-eknek és a szín-oszlopok feliratainak.
    Text {
        Layout.fillWidth: true
        text: qsTr("Font")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        // #741: a legördülők MÉRT magassága 21 képpont (`fontfamily`
        // 202 × 21, `sizelist` 48 × 21 —
        // `docs/specs/szerkeszto-panel-meretek.md` 6.4/7.). A belső
        // térközöket is nullázni kell, különben a vezérlő tartalma
        // kilógna a 21 képpontos dobozból.
        ComboBox {
            id: textFontBox
            objectName: "textFontFamilyBox"
            Layout.fillWidth: true
            Layout.preferredHeight: 21
            topPadding: 0
            bottomPadding: 0
            font.pixelSize: Theme.fontSize - 1
            model: panel.fontFamilyLabels
            currentIndex: Math.max(0, panel.fontFamilyKeys.indexOf(panel.textFontFamily))
            onActivated: panel.textFontFamilyEdited(panel.fontFamilyKeys[currentIndex])
        }
        SpinBox {
            objectName: "textFontSizeBox"
            //: a betűméret a rajzoló méret-szorzójának SZÁZALÉKA
            from: 20; to: 400; stepSize: 10
            // A `sizelist` az eredetiben 48 × 21-es LEGÖRDÜLŐ; nálunk
            // léptethető mező, aminek a két nyílgombbal együtt ennél több
            // kell. A 90 az implicit 120 helyett — a panel ettől még nem
            // lesz keskenyebb (a szöveg-panel túlcsordulása régebbi és más
            // okú, ld. a jelentést), de ez a rész már a mérethez igazodik.
            Layout.fillWidth: false
            Layout.preferredWidth: 90
            Layout.preferredHeight: 21
            topPadding: 0
            bottomPadding: 0
            font.pixelSize: Theme.fontSize - 1
            value: Math.round(panel.textFontScale * 100)
            onValueModified: panel.textFontScaleEdited(value / 100)
        }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        PanelButton {
            objectName: "textBoldButton"
            label: qsTr("B")
            tooltip: qsTr("Bold")
            active: panel.textBold
            onButtonClicked: panel.textBoldEdited(!panel.textBold)
        }
        PanelButton {
            objectName: "textItalicButton"
            label: qsTr("I")
            tooltip: qsTr("Italic")
            active: panel.textItalic
            onButtonClicked: panel.textItalicEdited(!panel.textItalic)
        }
        PanelButton {
            objectName: "textUnderlineButton"
            label: qsTr("U")
            tooltip: qsTr("Underline")
            active: panel.textUnderline
            onButtonClicked: panel.textUnderlineEdited(!panel.textUnderline)
        }
        Item { Layout.fillWidth: true }
        // a három igazítás-gomb: fix készlet, ezért kiírva (a Repeater
        // delegáltjai a funkcionális tesztekből nem érhetők el)
        PanelButton {
            objectName: "textAlign_left"
            label: "\u2261"
            tooltip: qsTr("Align left")
            active: panel.textAlign === "left"
            onButtonClicked: panel.textAlignEdited("left")
        }
        PanelButton {
            objectName: "textAlign_center"
            label: "\u2261"
            tooltip: qsTr("Align center")
            active: panel.textAlign === "center"
            onButtonClicked: panel.textAlignEdited("center")
        }
        PanelButton {
            objectName: "textAlign_right"
            label: "\u2261"
            tooltip: qsTr("Align right")
            active: panel.textAlign === "right"
            onButtonClicked: panel.textAlignEdited("right")
        }
    }

    // #450: kitöltés-szín ÉS körvonal-szín, egymástól függetlenül
    RowLayout {
        Layout.fillWidth: true
        spacing: 10
        ColumnLayout {
            spacing: 4
            Text {
                Layout.fillWidth: true
                elide: Text.ElideRight
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
                Layout.fillWidth: true
                elide: Text.ElideRight
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
        Layout.fillWidth: true
        text: qsTr("Outline thickness")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }
    PicasaSlider {
        id: textOutlineThicknessSlider
        objectName: "textOutlineThicknessSlider"
        Layout.fillWidth: true
        // #2271: az EREDETI mértékegysége `[0, 1]` folytonos — a csúszka
        // ugyanaz a `ytSliderHandler`, mint az átlátszatlanságé, és maga
        // normalizál a sáv hosszához (a korpuszban látott 0,25 és 0,5 a
        // negyed-, illetve félállás). Korábban 0–8 „képpont" volt, ezért
        // az érték nem is volt közvetlenül a fájlba írható.
        from: 0; to: 1
        value: panel.textOutlineThickness
        onMoved: panel.textOutlineThicknessEdited(value)
    }

    Label {
        Layout.fillWidth: true
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

    // #741: `edittextapply`/`edittextcancel` — párban álló, 98 × 28-as
    // gombok (x 38 és 141), nem a teljes oszlopot kitöltve
    //
    // #779: a 98 FELSŐ KORLÁT, nem fix méret. Fixen a pár 98 + 6 + 98 = 202
    // képpontot követelt az oszloptól, és ez volt a szöveg-panel mért
    // MINIMUMA (ablációval igazolva: elrejtve a minimum 202-ről 156-ra esik).
    // A `fillWidth` + `maximumWidth` a mért méretet adja, valahányszor van rá
    // hely, és csak akkor zsugorít, amikor nincs.
    RowLayout {
        Layout.fillWidth: true
        Layout.maximumWidth: 98 + 6 + 98
        Layout.alignment: Qt.AlignHCenter
        spacing: 6
        PanelButton {
            objectName: "textApplyButton"
            label: qsTr("Apply") + " ✔"
            Layout.fillWidth: true
            Layout.preferredWidth: 98
            Layout.maximumWidth: 98
            Layout.preferredHeight: 28
            buttonEnabled: panel.textPlacementPending
                          && textContentField.text.length > 0
            onButtonClicked: panel.textApplyRequested()
        }
        PanelButton {
            objectName: "textCancelButton"
            label: qsTr("Cancel") + " ✘"
            Layout.fillWidth: true
            Layout.preferredWidth: 98
            Layout.maximumWidth: 98
            Layout.preferredHeight: 28
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
