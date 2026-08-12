import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő 2., „Finomhangolás" füle (#20/#464/#551).
//
// #464: az elrendezés a tulajdonos NÉGY KÉPERNYŐKÉPÉRŐL származik
// (`sanchomuzax/picasapy-agent`: `referencia/finomhangolas/shot1..4.png`),
// nem feltevésből. Amit azok kimondtak, és ami eddig nálunk másképp volt:
//
//  * Nincs szöveges panel-fejléc — a csúszkák rögtön a fülsáv alatt
//    kezdődnek (ugyanaz az elv, mint az 1. fülnél, #405).
//  * A csúszka-feliratok KÖZÉPRE igazítottak, a csúszka fölött.
//  * Az „egy gombnyomásos javítás" NEM két nagy szöveges csempe a csúszkák
//    fölött, hanem KÉT KIS VARÁZSPÁLCA-GOMB a csúszka-oszlop JOBB szélén:
//      – az egyik a Kiemelések/Árnyékok párra fog rá (buboréksúgó:
//        „Egy gombnyomásos javítás a megvilágításhoz"),
//      – a másik az Alapszínválasztás sorára („…a színhez").
//  * A pipetta MELLETT egy korong mutatja a kijelölt semleges színt, és a
//    sor felirata „Alapszínválasztás"; a pipetta is kis ikonos gomb.
//
// A két pálca a mérés szerint az Automatikus kontraszt, illetve az
// Automatikus szín művelete: a `referencia/varazspalcak/` fotóján a
// fény-pálca kimenete a mi `autolight`-unkhoz 2,08-ra, a szín-pálcáé az
// `autocolor`-hoz 3,00-ra esik (az érintetlen kép 17,52 illetve 5,78).
//
// #496: önálló fájl (ld. az `EditorCropPanel.qml` megjegyzését a `panel`
// tulajdonságról). A csúszkákat a gazda `EditorPanel` az alias-okon át éri
// el — a QML-ben az `id` nem látszik át fájlhatáron.
ColumnLayout {
    id: finetunePanel

    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    property alias fillSlider: finetuneFillSlider
    property alias highlightsSlider: finetuneHighlightsSlider
    property alias shadowsSlider: finetuneShadowsSlider
    property alias tempSlider: finetuneTempSlider

    objectName: "finetuneColumn"
    opacity: panel.enabled ? 1 : 0.45
    anchors.margins: 10
    spacing: 6

    // középre igazított csúszka-felirat (az eredetin is középen áll)
    component SliderCaption: Label {
        Layout.fillWidth: true
        horizontalAlignment: Text.AlignHCenter
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    // kis, négyzetes ikonos gomb (varázspálca / pipetta) — az eredetin
    // ezek NEM a nagy, feliratos eszköz-csempék, hanem apró gombok
    component IconButton: Rectangle {
        id: iconButton
        property string iconFile: ""
        property string tooltip: ""
        property bool active: false
        signal clicked()

        implicitWidth: 24
        implicitHeight: 24
        radius: 3
        border.width: 1
        border.color: Theme.chromeBorder
        color: iconButton.active
               ? Qt.rgba(Theme.selectionBlue.r, Theme.selectionBlue.g,
                         Theme.selectionBlue.b, 0.45)
               : (iconMouse.pressed ? Qt.darker(Theme.buttonBg, 1.15)
                                    : Theme.buttonBg)

        Image {
            anchors.centerIn: parent
            width: 18
            height: 12
            fillMode: Image.PreserveAspectFit
            smooth: true
            source: "icons/" + iconButton.iconFile + ".svg"
        }
        MouseArea {
            id: iconMouse
            anchors.fill: parent
            hoverEnabled: true
            onClicked: iconButton.clicked()
        }
        ToolTip.visible: iconMouse.containsMouse && iconButton.tooltip !== ""
        ToolTip.text: iconButton.tooltip
        ToolTip.delay: 400
    }

    // --- Derítőfény -------------------------------------------------------
    SliderCaption { text: qsTr("Fill Light") }
    PicasaSlider {
        id: finetuneFillSlider
        objectName: "finetuneFillSlider"
        Layout.fillWidth: true
        from: 0; to: 1; value: 0
        // #337: a Gyakori javítások fülön lévő párjával közös állapot
        onValueChanged: panel.fillLightMoved(value)
        onPressedChanged: if (!pressed) panel.fillLightCommitted()
    }

    // --- Kiemelések + Árnyékok, jobbra a megvilágítás-pálcával ------------
    RowLayout {
        Layout.fillWidth: true
        spacing: 6

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            SliderCaption { text: qsTr("Highlights") }
            PicasaSlider {
                id: finetuneHighlightsSlider
                objectName: "finetuneHighlightsSlider"
                Layout.fillWidth: true
                // #551: a `filterdesc.xml` szerinti nyers paraméter-
                // tartomány [0..0.48] — a mérés is pontosan ezt igazolta (a
                // felső állásban a FEHÉRPONT 0,48-cal mozdul). A csúszka
                // számot nem mutat, tehát ez csak a mentett ini-értéket
                // teszi Picasa-azonossá.
                from: 0; to: 0.48; value: 0
                onValueChanged: if (!panel.suppressFinetune)
                    panel.emitFinetunePreview()
                onPressedChanged: if (!pressed) panel.emitFinetuneCommit()
            }

            SliderCaption { text: qsTr("Shadows") }
            PicasaSlider {
                id: finetuneShadowsSlider
                objectName: "finetuneShadowsSlider"
                Layout.fillWidth: true
                // #551: ld. a Kiemelések megjegyzését — itt a FEKETEPONT
                // mozdul ugyanennyivel.
                from: 0; to: 0.48; value: 0
                onValueChanged: if (!panel.suppressFinetune)
                    panel.emitFinetunePreview()
                onPressedChanged: if (!pressed) panel.emitFinetuneCommit()
            }
        }

        IconButton {
            objectName: "finetuneLightingWand"
            iconFile: "varazspalca"
            //: az eredeti buboréksúgója a képernyőképről
            tooltip: qsTr("One-click lighting fix")
            Layout.alignment: Qt.AlignVCenter
            onClicked: panel.handleToolClick("autolight")
        }
    }

    // --- Színhőmérséklet --------------------------------------------------
    SliderCaption { text: qsTr("Color Temperature") }
    PicasaSlider {
        id: finetuneTempSlider
        objectName: "finetuneTempSlider"
        Layout.fillWidth: true
        from: -1; to: 1; value: 0
        onValueChanged: if (!panel.suppressFinetune) panel.emitFinetunePreview()
        onPressedChanged: if (!pressed) panel.emitFinetuneCommit()
    }

    // --- Alapszínválasztás: színminta + pipetta, jobbra a szín-pálcával ---
    SliderCaption { text: qsTr("Neutral Color Picker") }
    RowLayout {
        Layout.fillWidth: true
        spacing: 6

        Item { Layout.fillWidth: true }   // a pipetta-csoport középre húzása

        // a kijelölt semleges szín korongja — kijelölés nélkül fekete,
        // ahogy az eredetin is (shot1.png)
        Rectangle {
            objectName: "finetuneNeutralSwatch"
            implicitWidth: 22
            implicitHeight: 22
            radius: width / 2
            color: panel.neutralColor === "" ? "#000000" : panel.neutralColor
            border.width: 1
            border.color: Theme.textGray
        }
        IconButton {
            objectName: "finetuneNeutralPicker"
            iconFile: "pipetta"
            //: az eredeti buboréksúgója a képernyőképről (shot4.png)
            tooltip: qsTr("Pick a neutral gray or white area of the photo to"
                          + " remove an unwanted color cast.")
            active: panel.neutralPickerActive
            onClicked: panel.neutralPickerToggled()
        }

        Item { Layout.fillWidth: true }

        IconButton {
            objectName: "finetuneColorWand"
            iconFile: "varazspalca"
            //: az eredeti buboréksúgója a képernyőképről
            tooltip: qsTr("One-click color fix")
            Layout.alignment: Qt.AlignVCenter
            // #551: a semleges színt (finetune2 p4) állítja, nem az
            // autocolor szűrőt fűzi a láncra — ld. a panel jelzésénél
            onClicked: panel.colorWandRequested()
        }
    }

    Item { Layout.fillHeight: true }   // a csúszkák felülre tapadnak
}
