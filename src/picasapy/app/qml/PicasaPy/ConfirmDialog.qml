import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #367: általános, újrafelhasználható megerősítő dialógus — a `confirm.fen`
// szerkezetének megfelelően (üzenet + „Don't ask again" jelölő + Igen/Nem/
// Mégse gombsor, ebben a sorrendben). A FEN-ben a „No" gomb type="other",
// NEM "cancel" — ezért itt sem a Dialog beépített reject()-jét futtatja,
// hanem külön `denied` jelzést ad; a Cancel gomb a valódi mégse-út.
//
// Kulcs-alapú elnyomás (#367): ha a felhasználó egy adott `key`-re egyszer
// bepipálja a „Don't ask again"-t és Igent választ, a `confirmSettings`
// (context property, ld. application.py/teszt-conftest-ek) megjegyzi —
// az `ask()` ettől kezdve NEM nyitja meg a dialógust, hanem azonnal úgy
// viselkedik, mintha a felhasználó Igent választott volna (`confirmed`
// jelzés szinkron kibocsátása).
Dialog {
    id: root
    objectName: namePrefix + "Dialog"
    // #422: több ConfirmDialog-példány is élhet egy ablakban (a törlés
    // megerősítése mellett pl. a mappa eltávolítása) — a belső elemek
    // neve ezért példányonként egyedi. Az alapérték a korábbi neveket
    // adja vissza, így a meglévő hívók változatlanok.
    property string namePrefix: "confirm"
    modal: true
    focus: true
    // window="fit" (confirm.fen) — a tartalomhoz igazodó méret
    anchors.centerIn: parent ? Overlay.overlay : undefined

    // a döntést azonosító kulcs (pl. "delete") — ez alatt tárolódik a
    // „ne kérdezze újra" jelölő a confirmSettings-ben
    property string decisionKey: ""
    // a ténylegesen megjelenő kérdés szövege — a hívó tölti fel (a FEN
    // `label name="message"` placeholderének felel meg)
    property string message: ""

    // Igen (accept) — akkor is kibocsátva, ha a dialógus meg sem nyílt,
    // mert a kulcs már el volt nyomva
    signal confirmed()
    // Nem (other) — explicit elutasítás, a hívó dolga eldönteni, mit jelent
    signal denied()
    // Mégse — a döntés elhalasztva, semmi nem történt
    signal canceled()

    // #367: a döntés megnyitása/automatikus elintézése kulcs szerint.
    // `settingKey` üres string esetén a dialógus mindig megnyílik (nincs
    // mit elnyomni) — ez a defenzív alapeset, ha a hívó elfelejtene kulcsot adni.
    function ask(settingKey, messageText) {
        decisionKey = settingKey
        message = messageText
        rememberCheck.checked = false
        if (settingKey.length > 0 && typeof confirmSettings !== "undefined"
                && confirmSettings && confirmSettings.isSuppressed(settingKey)) {
            confirmed()
            return
        }
        open()
    }

    onAccepted: {
        if (rememberCheck.checked && decisionKey.length > 0
                && typeof confirmSettings !== "undefined" && confirmSettings) {
            confirmSettings.setSuppressed(decisionKey, true)
        }
        confirmed()
    }

    ColumnLayout {
        spacing: 12

        Text {
            objectName: root.namePrefix + "MessageLabel"
            Layout.preferredWidth: 320
            text: root.message
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        CheckBox {
            id: rememberCheck
            objectName: root.namePrefix + "RememberCheck"
            text: qsTr("Don't ask again")
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 8

            PicasaButton {
                objectName: root.namePrefix + "YesButton"
                text: qsTr("Yes")
                accent: Theme.picasaGreen
                onClicked: root.accept()
            }
            PicasaButton {
                objectName: root.namePrefix + "NoButton"
                text: qsTr("No")
                onClicked: {
                    root.close()
                    root.denied()
                }
            }
            PicasaButton {
                objectName: root.namePrefix + "CancelButton"
                text: qsTr("Cancel")
                onClicked: {
                    root.close()
                    root.canceled()
                }
            }
        }
    }
}
