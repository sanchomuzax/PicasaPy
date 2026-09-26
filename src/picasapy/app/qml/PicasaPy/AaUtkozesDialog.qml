import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

//: #3014: a kettős nézet szerkesztési ÜTKÖZÉS-párbeszéde — `CThumbUI::
//: Confirm2up*` (`0x0056aad0`), `docs/specs/ui-audit-editor.md` 4. szakasz.
//:
//: Akkor nyílik, amikor az „aa" mód két fele KÜLÖNBÖZŐEN módosult, és a
//: felhasználó kilép a módból. A gombok HELYZETEK, nem „A/B": vízszintes
//: elrendezésben `Bal`/`Jobb`, függőlegesben `Fent`/`Lent` (4/b 6. pont). Az
//: alapértelmezett gomb (Enter) az AKTÍV félé (4/b.1). A Mégse a kettős
//: nézetet hagyja meg, mindkét szerkesztéssel.
//:
//: A „Ne kérdezzen újra" a #367-es `confirmSettings` tárba írja a
//: `DoNotAskOnEnd2Up` kulcsot — de csak VÁLASZ esetén, Mégsére nem (az
//: eredeti a `0x0056af7d`-n, a gomb-ágak után írja).
Dialog {
    id: root
    objectName: "aaUtkozesDialog"
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    //: az Esc a Mégse útja; mellékattintás nem dönt semmiről
    closePolicy: Popup.CloseOnEscape
    onRejected: root.megse()
    //: `CThumbUI::Confirm2upEditTitle`
    title: qsTr("Choose Edits")

    //: a #367-es tár döntés-kulcsa — az eredeti beállítás neve
    readonly property string beallitasKulcs: "DoNotAskOnEnd2Up"

    //: `swap_2up_layout` állása: igaz ⇒ `Fent`/`Lent`
    property bool fuggoleges: false
    //: az aktív fél: `"elso"` (bal/fent) vagy `"masodik"` (jobb/lent)
    property string aktivFel: "masodik"

    //: a választott fél: `"elso"` vagy `"masodik"`
    signal valasztva(string fel)
    signal megse()

    function kerdez(fuggolegesen, aktiv) {
        root.fuggoleges = fuggolegesen
        root.aktivFel = aktiv
        neKerdezzen.checked = false
        root.open()
    }

    function _valaszt(fel) {
        if (neKerdezzen.checked && typeof confirmSettings !== "undefined"
                && confirmSettings)
            confirmSettings.setSuppressed(root.beallitasKulcs, true)
        root.close()
        root.valasztva(fel)
    }

    ColumnLayout {
        spacing: 12
        //: Enter = az alapértelmezett (az aktív félé) gomb. A jelölő a
        //: Return-t nem fogadja el, tehát onnan is ide jut.
        focus: true
        Keys.onReturnPressed: root._valaszt(root.aktivFel)
        Keys.onEnterPressed: root._valaszt(root.aktivFel)

        Text {
            objectName: "aaUtkozesUzenet"
            Layout.preferredWidth: 340
            //: `CThumbUI::Confirm2upEditMsg`
            text: qsTr("The same image has two different edits. Which one would you like to keep?")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        CheckBox {
            id: neKerdezzen
            objectName: "aaUtkozesNeKerdezzenCheck"
            //: `CThumbUI::Confirm2upEditDontAsk`
            text: qsTr("Don't ask again, always use the selected image")
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 8

            //: 0. gomb — az ELSŐ fél (`Confirm2upLeft` / `Confirm2upTop`)
            PicasaButton {
                objectName: "aaUtkozesElsoButton"
                readonly property bool alapertelmezett: root.aktivFel === "elso"
                text: root.fuggoleges ? qsTr("Top") : qsTr("Left")
                accent: alapertelmezett ? Theme.picasaGreen : "transparent"
                onClicked: root._valaszt("elso")
            }
            //: 1. gomb — a MÁSODIK fél (`Confirm2upRight` / `Confirm2upBottom`)
            PicasaButton {
                objectName: "aaUtkozesMasodikButton"
                readonly property bool alapertelmezett: root.aktivFel === "masodik"
                text: root.fuggoleges ? qsTr("Bottom") : qsTr("Right")
                accent: alapertelmezett ? Theme.picasaGreen : "transparent"
                onClicked: root._valaszt("masodik")
            }
            //: 2. gomb — `il_Cancel`
            PicasaButton {
                objectName: "aaUtkozesMegseButton"
                text: qsTr("Cancel")
                onClicked: {
                    root.close()
                    root.megse()
                }
            }
        }
    }
}
