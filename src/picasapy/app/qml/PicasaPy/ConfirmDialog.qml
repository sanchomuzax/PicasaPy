import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #367: általános, újrafelhasználható megerősítő dialógus — a `confirm.fen`
// szerkezetének megfelelően (üzenet + „Do not ask again" jelölő + Igen/Nem/
// Mégse gombsor, ebben a sorrendben). A FEN-ben a „No" gomb type="other",
// NEM "cancel" — ezért itt sem a Dialog beépített reject()-jét futtatja,
// hanem külön `denied` jelzést ad; a Cancel gomb a valódi mégse-út.
//
// Kulcs-alapú elnyomás (#367): ha a felhasználó egy adott `key`-re egyszer
// bepipálja a „Do not ask again"-t és Igent választ, a `confirmSettings`
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
    // #459: némelyik hívó az eredeti Picasa KÉRDÉS-szövegét jeleníti meg
    // úgy, hogy az "Igen" ág (pl. mappa-másolás) MÉG nincs megvalósítva —
    // ilyenkor a hívó `false`-ra állítja, hogy a gomb LÁTHATÓAN tiltott
    // legyen, ne egy néma no-op (CLAUDE.md #459 feladat, (j) szabály).
    property bool yesEnabled: true
    // #459: az eredeti Picasa némely dialógusán a gombfelirat NEM
    // "Yes"/"No" (pl. sérült kép: "Hide Files" / "Don't Hide") — a
    // gombok viselkedése (accept/deny) változatlan, csak a felirat hívó-
    // testreszabható.
    property string yesText: qsTr("Yes")
    property string noText: qsTr("No")
    // Egyes megerősítők biztonságos alapértelmezésként a Mégse gombra
    // teszik a kezdeti fókuszt; az alapbeállítás a többi hívót változatlanul
    // hagyja.
    property bool focusCancelOnOpen: false
    // #6283: az eredeti album-törlő ablakában (job-329) csak két gomb van,
    // jelölőnégyzet nincs, és a fókusz a „No” gombon áll: Enterre elutasít.
    property bool cancelVisible: true
    property bool rememberVisible: true
    property bool focusNoOnOpen: false
    // #6287: a Rejtett mappák jelszóajánlatában (job-331) az igen-gomb a
    // fókuszos, Enterre elfogad.
    property bool focusYesOnOpen: false
    // #5704: az opt-out a „No” ágon is menthető az eredeti rejtettjelszó-
    // ajánlatban. Más megerősítők változatlanul csak az „Yes” ágon mentenek.
    property bool rememberOnDenied: false
    property string rememberText: qsTr("Do not ask again")

    onOpened: {
        if (root.focusCancelOnOpen)
            cancelButton.forceActiveFocus()
        else if (root.focusNoOnOpen)
            noButton.forceActiveFocus()
        else if (root.focusYesOnOpen)
            yesButton.forceActiveFocus()
    }

    function _deny() {
        if (root.rememberOnDenied && rememberCheck.checked
                && root.decisionKey.length > 0
                && typeof confirmSettings !== "undefined"
                && confirmSettings) {
            confirmSettings.setSuppressed(root.decisionKey, true)
        }
        root.close()
        root.denied()
    }

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
            text: root.rememberText
            visible: root.rememberVisible
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 8

            PicasaButton {
                id: yesButton
                objectName: root.namePrefix + "YesButton"
                text: root.yesText
                accent: Theme.picasaGreen
                enabled: root.yesEnabled
                Keys.onReturnPressed: root.accept()
                Keys.onEnterPressed: root.accept()
                onClicked: root.accept()
            }
            PicasaButton {
                id: noButton
                objectName: root.namePrefix + "NoButton"
                text: root.noText
                Keys.onReturnPressed: root._deny()
                Keys.onEnterPressed: root._deny()
                onClicked: root._deny()
            }
            PicasaButton {
                id: cancelButton
                objectName: root.namePrefix + "CancelButton"
                text: qsTr("Cancel")
                visible: root.cancelVisible
                focus: root.focusCancelOnOpen
                Keys.priority: Keys.BeforeItem
                Keys.onReturnPressed: function(event) {
                    if (!root.focusCancelOnOpen) {
                        event.accepted = false
                        return
                    }
                    root.close()
                    root.canceled()
                    event.accepted = true
                }
                Keys.onEnterPressed: function(event) {
                    if (!root.focusCancelOnOpen) {
                        event.accepted = false
                        return
                    }
                    root.close()
                    root.canceled()
                    event.accepted = true
                }
                onClicked: {
                    root.close()
                    root.canceled()
                }
            }
        }
    }
}
