import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő „Retusálás" panelje (#148/#445): az ecsetméret-csúszka, a
// kétkattintásos klónozás súgószövege és a saját Alkalmaz/Mégse pár.
//
// #496: kiemelve az EditorPanel.qml-ből (ld. az `EditorCropPanel.qml`
// megjegyzését a `panel` tulajdonságról).
ColumnLayout {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    objectName: "retouchColumn"
    visible: panel.retouchActive
    opacity: panel.enabled ? 1 : 0.45
    anchors.margins: 10
    spacing: 8

    // #741: a retusálás gombjai SZÉLESEBBEK a többi eszközénél — 118 × 28
    // (`docs/specs/szerkeszto-panel-meretek.md` 6.3/7.), 7 képpont
    // hézaggal (x 18 és 143). A `retouchreset` egyedül, középen áll (x 80).
    //
    // #779: a 118 FELSŐ KORLÁT, nem fix méret. A névleges 280 képpontos
    // panelen a pár 118 + 7 + 118 = 243 képpont, pontosan a mért geometria;
    // egy keskenyebb (260 képpontos) panelen viszont a 240-es tartalom-oszlop
    // ennél szűkebb, és a fix méret 3 képponttal kilógatta a sort. A
    // `fillWidth` + `maximumWidth` páros a mért méretet adja, valahányszor van
    // rá hely, és csak akkor zsugorít, amikor nincs.
    component ActionButton: PanelButton {
        Layout.fillWidth: true
        Layout.preferredWidth: 118
        Layout.maximumWidth: 118
        Layout.preferredHeight: 28
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        Image {
            Layout.preferredWidth: 40
            Layout.preferredHeight: 30
            source: "../../assets/tools/retouch.png"
        }
        Text {
            Layout.fillWidth: true
            text: qsTr("Retouch")
            font.pixelSize: Theme.fontSize + 3
            color: Theme.ink
        }
    }

    Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: qsTr("Click to select the area to fix. Then, move the"
                   + " mouse to see a preview of the replacement area."
                   + " Click on the image again to finalize. Lather,"
                   + " rinse, repeat.")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    // #779: kitöltő, hogy a felirat betűszélessége ne szabja meg a panel
    // minimumát (ld. az EditorTextPanel.qml azonos okú megjegyzését).
    Label {
        Layout.fillWidth: true
        text: qsTr("Brush Size")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }
    PicasaSlider {
        id: retouchBrushSizeSlider
        objectName: "retouchBrushSizeSlider"
        // #741: `brushslider_container` — a mért 127 × 27, középen (x 74)
        Layout.fillWidth: false
        Layout.preferredWidth: 127
        Layout.preferredHeight: 27
        Layout.alignment: Qt.AlignHCenter
        from: 1; to: 100
        stepSize: 1
        value: panel.brushSize
        onMoved: panel.brushSizeEdited(Math.round(value))
    }

    Text {
        objectName: "retouchRegionCountLabel"
        Layout.fillWidth: true
        text: qsTr("Regions selected: %1").arg(panel.retouchRegionCount)
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    // #445: a Picasa súgószövege szerinti, számítás-alatti előnézetet
    // jelző felirat — a folt véglegesítéséig (cél kijelölve, forrás
    // mozgatás alatt) látszik az előnézet fölött.
    Text {
        objectName: "retouchRefiningLabel"
        Layout.fillWidth: true
        visible: panel.retouchPatchPending
        text: qsTr("Refining…")
        font.pixelSize: Theme.fontSize - 1
        font.italic: true
        color: Theme.textGray
    }

    // #741: az eredetin a `retouchreset` EGYEDÜL, középen ül, a
    // `retouchundo`/`retouchredo` pedig alatta párban — korábban mindhárom
    // egy sorban szorongott, és egyik sem érte el a 118 képpontot.
    ActionButton {
        objectName: "retouchResetButton"
        label: qsTr("Reset")
        Layout.alignment: Qt.AlignHCenter
        buttonEnabled: panel.retouchRegionCount > 0 || panel.retouchPatchPending
        onButtonClicked: panel.retouchResetRequested()
    }

    // #779: a gombpár sora is felső korláttal áll (ld. az ActionButton
    // megjegyzését) — a 243 képpont a névleges panelen pontos, keskenyebben
    // a sor a tartalom-oszlophoz igazodik.
    RowLayout {
        Layout.fillWidth: true
        Layout.maximumWidth: 118 + 7 + 118
        Layout.alignment: Qt.AlignHCenter
        spacing: 7
        ActionButton {
            objectName: "retouchUndoPatchButton"
            label: qsTr("Undo Patch")
            buttonEnabled: panel.canUndoPatch
            onButtonClicked: panel.retouchUndoPatchRequested()
        }
        ActionButton {
            objectName: "retouchRedoPatchButton"
            label: qsTr("Redo Patch")
            buttonEnabled: panel.canRedoPatch
            onButtonClicked: panel.retouchRedoPatchRequested()
        }
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.maximumWidth: 118 + 7 + 118
        Layout.alignment: Qt.AlignHCenter
        spacing: 7
        ActionButton {
            objectName: "retouchApplyButton"
            label: qsTr("Apply") + " ✔"
            buttonEnabled: panel.retouchRegionCount > 0
            onButtonClicked: panel.retouchApplyRequested()
        }
        ActionButton {
            objectName: "retouchCancelButton"
            label: qsTr("Cancel") + " ✘"
            onButtonClicked: panel.retouchCancelRequested()
        }
    }
}
