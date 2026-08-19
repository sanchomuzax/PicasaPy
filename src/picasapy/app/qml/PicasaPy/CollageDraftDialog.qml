import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A kollázs-piszkozat HELYREÁLLÍTÁSÁNAK felajánlása (#1051).
//
// Spec: `docs/specs/picasa-create-features.md` 1.5 és
// `docs/specs/picasa-kollazs-felulet.md` 9.2/b.
//
// ## Miért létezik ez a fájl
//
// A visszatöltés MÁR KÉSZ volt a vezérlőben — `restoreCollageDraft`,
// `collageDraftAvailable`, `refreshCollageDraft`, `discardCollageDraft` —,
// csak éppen a felületről SOHA nem hívta meg senki. A tulajdonos gépén egy
// valódi, éjjel elmentett `autosave.cxf` állt elérhetetlenül a lemezen: a
// program elmentette a munkáját, és soha nem kínálta vissza.
//
// ## Miért párbeszéd, és miért nem album-csempe
//
// Az EREDETI Picasa nem kérdez: induláskor átnevezi az `autosave.cxf`-et
// „Helyreállított automatikus másolat"-ra, ír mellé egy 640 × 480-as
// helykitöltő JPEG-et, és beindexeli — a piszkozat így egyszerűen ott van a
// Kollázsok albumban. Ez a GAZDAGABB működés a #979, és blokkolt.
//
// Ez a felajánlás a köztes állapot: a már megírt visszatöltéshez ad utat,
// a #979 nélkül is. Ha a #979 elkészül, a felajánlás átalakulhat
// album-csempévé — a most bekötött slotok akkor is használatban maradnak.
//
// ## Az `Esc` nem „nem"
//
// Két GOMB van, de három kimenet. Az „Elvetés" TÖRLI a piszkozatot, tehát
// visszavonhatatlan; az `Esc` ezért csak elhalasztja a döntést, és a
// felajánlás a következő indításkor visszatér. Aki bizonytalan, ne
// veszítse el a munkáját azért, mert be akarta csukni az ablakot.
Dialog {
    id: draftDialog
    objectName: "collageDraftDialog"
    title: qsTr("Recovered Auto Backup")
    modal: true
    anchors.centerIn: parent
    closePolicy: Popup.CloseOnEscape

    /** A felajánlás CSAK ép piszkozatra jön elő.
        A `collageDraftAvailable` tényleges beolvasással válaszol, tehát a
        sérült vagy csonk piszkozatot magától kiszűri. */
    function openIfNeeded() {
        if (!controller)
            return
        controller.refreshCollageDraft()
        if (controller.collageDraftAvailable)
            open()
    }

    ColumnLayout {
        spacing: 12

        Text {
            objectName: "collageDraftMessage"
            Layout.preferredWidth: 420
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            text: qsTr("PicasaPy found an automatically saved collage draft "
                       + "from an earlier session.\n\n"
                       + "Restore it to continue where you left off. If you "
                       + "discard it, the draft is deleted and will not be "
                       + "offered again.")
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 8

            PicasaButton {
                objectName: "collageDraftRestoreButton"
                text: qsTr("Restore Draft")
                accent: Theme.picasaGreen
                onClicked: {
                    draftDialog.close()
                    controller.restoreCollageDraft()
                    draftDialog.restored()
                }
            }
            PicasaButton {
                objectName: "collageDraftDiscardButton"
                text: qsTr("Discard Draft")
                onClicked: {
                    draftDialog.close()
                    controller.discardCollageDraft()
                }
            }
        }
    }

    //: A piszkozat visszatöltése megtörtént — a gazda válthat a lapra.
    signal restored()
}
