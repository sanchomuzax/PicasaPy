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
//: Elvet lezárja az eszközt, és a módváltás folytatódik.
//:
//: NINCS Mégse gomb: a belépés a kaput `0x005f8d80(this, 1, 0, 0)` alakban
//: hívja, és a 2. gomb (`il_Cancel`) csak nem nulla 4. argumentumnál kerül a
//: párbeszédbe (`0x005f8e36`, 3/c 2. pont). Ezért az Esc és a mellékattintás
//: sem zárja be — a két gomb egyikével kell dönteni.
//:
//: A jelölő (`Preferences/DoNotAskOnEndEditModality`) ELVETÉSNÉL is beíródik
//: — az eredeti mérve így viselkedik (`0x005f9018`, a 4/b.1 idézete): a
//: jelző nem a MOSTANI választ ismétli, hanem azt dönti el, hogy MOSTANTÓL
//: kérdés nélkül alkalmaz-e a kapu.
Dialog {
    id: root
    objectName: "endEditModalityDialog"
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    //: Mégse nincs (ld. fent) — sem Esc, sem mellékattintás nem zár
    closePolicy: Popup.NoAutoClose
    //: `IDS_ENDEDITMODALITY_TITLE`
    title: qsTr("Confirm Edit")

    //: a #367-es tár döntés-kulcsa — az eredeti beállítás neve
    readonly property string beallitasKulcs: "DoNotAskOnEndEditModality"

    //: `true` = Alkalmaz, `false` = Elvet
    signal eldontve(bool alkalmaz)

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
            font.pixelSize: Theme.fontSize
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
        }
    }
}
