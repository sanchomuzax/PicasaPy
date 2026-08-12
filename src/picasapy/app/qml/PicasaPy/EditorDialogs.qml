import QtQuick
import QtQuick.Controls

// A szerkesztő PÁRBESZÉDEI (#448, #459): egyéni képarány törlésének
// megerősítése, csak-olvasható fájl kiútja és a lemez-hiba jelentése.
//
// #496: az `EditorPanel.qml`-ből kiemelve — a fájl a 800 soros korlát fölé
// nőtt. A viselkedés VÁLTOZATLAN; a `panel` a gazda EditorPanel.
Item {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel
    // #448: az egyéni arány törlésének megerősítése (a jegy szerint az
    // egyéni tételek törölhetők) — #422 mintája szerint EGYEDI namePrefix.
    ConfirmDialog {
        id: deleteCustomAspectConfirm
        namePrefix: "deleteCustomAspectConfirm"
        property string pendingName: ""
        property real pendingWidth: 0
        property real pendingHeight: 0
        onConfirmed: {
            if (typeof controller !== "undefined" && controller
                    && deleteCustomAspectConfirm.pendingName !== "") {
                controller.deleteCustomAspectRatio(
                    deleteCustomAspectConfirm.pendingName,
                    deleteCustomAspectConfirm.pendingWidth,
                    deleteCustomAspectConfirm.pendingHeight)
                // törlés után a kiválasztás védetten (selectedPreset)
                // tartományon belülre esik — nincs teendő itt
            }
        }
    }

    // #459: csak-olvasható mappa/fájl felismerése mentéskor — az eredeti
    // Picasa szövege szerinti kérdés, DE az "Igen" (mappa-másolás) ág nem
    // készült el, ezért a gomb láthatóan TILTOTT (yesEnabled: false),
    // hogy ne tegyünk úgy, mintha másolna. Egyedi namePrefix (#367/(c) szabály).
    ConfirmDialog {
        id: editReadOnlyDialog
        namePrefix: "editReadOnly"
        yesEnabled: false
    }

    // #459: minden egyéb mentési hiba (pl. lemez megtelt, tartós ütközés)
    // — az importálás/mentés eredeti szövege szerint ("...due to a disk
    // error. The disk may be full or read-only."). Egyedi namePrefix.
    ConfirmDialog {
        id: editSaveErrorDialog
        namePrefix: "editSaveError"
        yesEnabled: false
    }

    Connections {
        target: typeof editController !== "undefined" ? editController : null
        function onEditSaveReadOnly() {
            // #459: az ELSŐ bekezdés az eredeti Picasa szó szerinti
            // szövege. A második a MIÉNK, és azért kell, mert a
            // mappa-másolás még nincs megvalósítva: az "Igen" gomb
            // tiltott (`yesEnabled: false`), és megválaszolhatatlan
            // kérdést feltenni indoklás nélkül rosszabb, mint világosan
            // megmondani, hogy ez a kiút még nem elérhető.
            editReadOnlyDialog.ask("", qsTr(
                "This file is read only. In order to edit this file, "
                + "Picasa needs to copy the file's folder. Would you "
                + "like to make a copy now?")
                + "\n\n" + qsTr(
                "The automatic copy is not available yet. To edit this "
                + "picture, copy it to a writable folder yourself, or "
                + "remove the write protection."))
        }
        function onEditSaveFailed(message) {
            editSaveErrorDialog.ask("", qsTr(
                "Due to a disk error. The disk may be full or read-only.")
                + "\n" + message)
        }
    }
}
