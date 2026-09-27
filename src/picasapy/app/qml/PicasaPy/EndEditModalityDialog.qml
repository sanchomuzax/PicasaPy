import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

//: #3651: a nyitott modális eszköz (Vágás/Retusálás/Szöveg/Vörösszem)
//: lezárás-kérdése a kettős nézet „aa"/„ab" módjába LÉPÉSKOR —
//: `CThumbUI::ConfirmAbandonModifiedEdit*` (`0x005f8d80`),
//: `docs/specs/ui-audit-editor.md` 4/b.1 2. lépés + 3/c szakasz (#3543/#3686).
//:
//: A `0x0056a260` (belépés „aa"/„ab" módba) a 2-up kilépési létra (4/b) UTÁN
//: hívja ezt a kaput, HA egy modális eszköz nyitva ÉS módosult. Alkalmaz/
//: Elvet lezárja az eszközt, és a módváltás folytatódik; Mégse a módváltást
//: állítja meg, az eszköz NYITVA marad.
//:
//: A jelölő (`Preferences/DoNotAskOnEndEditModality`) ELVETÉSNÉL is beíródik
//: — az eredeti mérve így viselkedik (`0x005f9018`, a 4/b.1 idézete): a
//: jelző nem a MOSTANI választ ismétli, hanem azt dönti el, hogy MOSTANTÓL
//: kérdés nélkül alkalmaz-e a kapu. Mégsére a jelölő állása figyelmen kívül
//: marad, akkor sem ír, ha be volt pipálva.
Dialog {
    id: root
    objectName: "endEditModalityDialog"
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    //: az Esc a Mégse útja; mellékattintás nem dönt semmiről
    closePolicy: Popup.CloseOnEscape
    onRejected: root._megsem()
    //: `IDS_ENDEDITMODALITY_TITLE`
    title: qsTr("Confirm Edit")

    //: a #367-es tár döntés-kulcsa — az eredeti beállítás neve
    readonly property string beallitasKulcs: "DoNotAskOnEndEditModality"

    //: `true` = Alkalmaz, `false` = Elvet; Mégsére nem bocsát ki jelzést
    signal eldontve(bool alkalmaz)
    signal megse()

    function kerdez() {
        neKerdezzen.checked = false
        root.open()
    }

    function _dont(alkalmaz) {
        if (neKerdezzen.checked && typeof confirmSettings !== "undefined"
                && confirmSettings)
            confirmSettings.setSuppressed(root.beallitasKulcs, true)
        root.close()
        root.eldontve(alkalmaz)
    }

    function _megsem() {
        root.close()
        root.megse()
    }

    ColumnLayout {
        spacing: 12

        Text {
            objectName: "endEditModalityUzenet"
            Layout.preferredWidth: 320
            //: `IDS_ENDEDITMODALITY_MESSAGE`
            text: qsTr("Apply changes to the current image?")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        CheckBox {
            id: neKerdezzen
            objectName: "endEditModalityNeKerdezzenCheck"
            //: `IDS_ENDEDITMODALITY_CHECKMESSAGE`
            text: qsTr("Don't ask me again, always apply changes.")
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 8

            //: 0. gomb — `CThumbUI::ConfirmAbandonModifiedEditYesButton`
            PicasaButton {
                objectName: "endEditModalityApplyButton"
                text: qsTr("Apply Changes")
                accent: Theme.picasaGreen
                onClicked: root._dont(true)
            }
            //: 1. gomb — `CThumbUI::ConfirmAbandonModifiedEditNoButton`
            PicasaButton {
                objectName: "endEditModalityDiscardButton"
                text: qsTr("Discard Changes")
                onClicked: root._dont(false)
            }
            //: 2. gomb — `il_Cancel`
            PicasaButton {
                objectName: "endEditModalityCancelButton"
                text: qsTr("Cancel")
                onClicked: root._megsem()
            }
        }
    }
}
