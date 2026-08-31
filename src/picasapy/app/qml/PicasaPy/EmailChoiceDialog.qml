import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #1798 — „Hogyan küldjem el?" A Beállítások E-mail fülén választható a
// „minden küldéskor kérdezz" mód; eddig ez a mód NÉMA volt: tárolódott,
// a felület visszajelezte, a küldés viszont átlépett rajta.
//
// Az eredetiben ehhez a `choose_mail` párbeszéd tartozik, két úttal
// (levelezőprogram / Google Mail) és egy „ne jelenítse meg újra"
// jelöléssel (`EmailPrepType`, `DoNotPromptForEmailPref`).
//
// ⚠️ A Google Mail-ág HALOTT — a Picasa saját Gmail-integrációja megszűnt,
// és Linuxon nincs miből felépíteni. A választó maga viszont NEM halott: a
// mi Beállításunk ígéri, és a „ne kérdezd többet" jelölés is valódi
// funkció. Ez a párbeszéd ezért az élő utat kínálja, a jelöléssel együtt.
Dialog {
    id: root

    //: A választó-párbeszéd címe küldés előtt
    title: qsTr("Send pictures by email")
    modal: true
    anchors.centerIn: Overlay.overlay
    standardButtons: Dialog.Ok | Dialog.Cancel

    //: A csatolmányok útvonalai — a hívó tölti ki megnyitás előtt
    property var attachmentPaths: []
    property string subject: ""
    property string body: ""

    //: Igaz, ha a felhasználó azt kérte, ne kérdezzünk többet
    readonly property bool rememberChoice: emlekezzKapcsolo.checked

    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        Label {
            objectName: "emailChoiceExplanation"
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            //: A választó-párbeszéd magyarázó sora
            text: qsTr("The pictures will be attached to a new message in "
                       + "your default email program.")
        }

        CheckBox {
            id: emlekezzKapcsolo
            objectName: "emailChoiceRemember"
            //: A mért „DoNotPromptForEmailPref" megfelelője
            text: qsTr("Remember this choice and do not ask again")
        }
    }

    // A jelölés ne ragadjon be két megnyitás közt: aki egyszer nem kérte a
    // megjegyzést, annak legközelebb se legyen bepipálva.
    onOpened: emlekezzKapcsolo.checked = false
}
