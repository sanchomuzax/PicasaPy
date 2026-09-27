import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

//: #3651: a nyitott modális eszköz (Vágás/Retusálás/Szöveg/Vörösszem)
//: lezárás-kérdése a kettős nézet „aa"/„ab" módjába LÉPÉSKOR, ÉS #3693: a
//: fókuszváltáskor is — `CThumbUI::ConfirmAbandonModifiedEdit*`
//: (`0x005f8d80`), `docs/specs/ui-audit-editor.md` 4/b.1 2. lépés + 3/c
//: szakasz (#3543/#3686).
//:
//: A `0x0056a260` (belépés „aa"/„ab" módba) a 2-up kilépési létra (4/b) UTÁN
//: hívja ezt a kaput, HA egy modális eszköz nyitva ÉS módosult. Alkalmaz/
//: Elvet lezárja az eszközt, és a módváltás folytatódik.
//:
//: A 2. gomb (`il_Cancel`) csak nem nulla 4. argumentumnál kerül a
//: párbeszédbe (`0x005f8e36`, 3/c 2. pont): a mód-belépés `0x005f8d80(this,
//: 1, 0, 0)`-t hív (NINCS Mégse — az Esc és a mellékattintás sem zár), a
//: fókuszváltó (`0x0056a160`) viszont `0x005f8d80(this, 1, 0, 1)`-et (VAN
//: Mégse: `megseLathato`, Mégsére a fókusz nem vált, 3/c 2. pont). Csak a
//: gombokkal dönthető — Esc és mellékattintás Mégse esetén sem zár, ez nincs
//: mérve.
Dialog {
    id: root
    objectName: "endEditModalityDialog"
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    //: sem Esc, sem mellékattintás nem zár — ld. fent
    closePolicy: Popup.NoAutoClose
    //: `IDS_ENDEDITMODALITY_TITLE`
    title: qsTr("Confirm Edit")

    //: a #367-es tár döntés-kulcsa — az eredeti beállítás neve
    readonly property string beallitasKulcs: "DoNotAskOnEndEditModality"

    //: #3693: a hívó dönt a Mégse gomb láthatóságáról (`kerdez` argumentuma)
    property bool megseLathato: false

    //: `true` = Alkalmaz, `false` = Elvet
    signal eldontve(bool alkalmaz)
    //: #3693: Mégse — az eszköz nyitva marad, semmi nem zárul
    signal megse()

    function kerdez(megseEngedve) {
        neKerdezzen.checked = false
        root.megseLathato = megseEngedve === true
        root.open()
        //: a Mégse láthatóságának változása (és a megnyitás) a sorokat csak
        //: a KÖVETKEZŐ képkocka polírozásakor rendezné újra — addig a Mégse
        //: az Alkalmaz helyén állna, és a párbeszéd a régi szélességű
        //: volna. Az újrarendezés itt, azonnal lefut.
        tartalom.ensurePolished()
        gombsor.ensurePolished()
    }

    function _dont(alkalmaz) {
        if (neKerdezzen.checked && typeof confirmSettings !== "undefined"
                && confirmSettings)
            confirmSettings.setSuppressed(root.beallitasKulcs, true)
        root.close()
        root.eldontve(alkalmaz)
    }

    function _megseDont() {
        root.close()
        root.megse()
    }

    ColumnLayout {
        id: tartalom
        objectName: "endEditModalityTartalom"
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

        //: a rejtett Mégse gombot a `RowLayout` kihagyja a sorból és a
        //: szélesség-számításból is — a mód-belépés párbeszéde így
        //: képpontra a Mégse nélküli kétgombos sor marad (#3651).
        RowLayout {
            id: gombsor
            objectName: "endEditModalityGombsor"
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
            //: 2. gomb — `il_Cancel`, csak `megseLathato` esetén látszik
            //: (3/c 2. pont). A #3651 tesztje a `visible` property-t nézi,
            //: nem a gomb létét.
            PicasaButton {
                objectName: "endEditModalityCancelButton"
                text: qsTr("Cancel")
                visible: root.megseLathato
                onClicked: root._megseDont()
            }
        }
    }
}
