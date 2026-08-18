import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A Kollázs-panel párbeszédei (#949) — spec 9.1, 9.2, 9.4 és 3.3.
//
// Hét kérdés/üzenet, egy fájlban, mert egy dolgot csinálnak: a mentés és a
// bezárás körüli DÖNTÉSEKET viszik el a felhasználóhoz. Egyik sem tart
// állapotot: mindegyik jelzést ad, a következményt a `CollagePanel` intézi
// — így a „egy bezárási út" és az „egy mentési kódút" szabály nem tud
// ebben a fájlban megtörni.
//
// ## Miért nem `ConfirmDialog`
//
// A `ConfirmDialog`-nak van „Ne kérdezze újra" jelölője. Mentetlen
// módosítást vagy egy meglévő fájl felülírását SOHA nem szabad némán
// eldönteni — ezeknek a kérdéseknek nincs elnyomható változata. A
// `DocumentTabStrip` (#944) ugyanezért épített saját, háromgombos
// párbeszédet, és a bezárás-kérdés szövegét szó szerint ONNAN vesszük át.
//
// ## A szövegek
//
// Mind a `picasa-kollazs-felulet.md` 9.1–9.3 és a
// `picasa-create-features.md` 1.10.6 hivatalos magyarja. Egyetlen kivétel
// jelölve: a formátum-eltérés MAGYARÁZÓ szövege az eredeti angolból
// fordítva (a `collage::formatwarning` magyar erőforrása nincs a
// leltárunkban) — a CÍME és a két GOMBJA viszont hivatalos.
Item {
    id: dialogs

    // A párbeszédek `Popup`-ok: nem foglalnak helyet a szülő elrendezésében.
    width: 0
    height: 0

    //: „Beállítás ennek ellenére" — a formátum-figyelmeztetés átlépése.
    signal formatIgnored()
    //: „Beállítás mellőzése" — a mentés elmarad.
    signal formatRejected()
    //: „Meglévő cseréje".
    signal replaceExisting()
    //: „Új létrehozása".
    signal createNew()
    //: „Piszkozat mentése" / „Módosítások elvetése" a bezárás előtt.
    signal closeWithDraft()
    signal closeDiscardingChanges()
    //: „Kollázs megszakítása".
    signal cancelConfirmed()

    /** „Mentés mellőzve" (9.1) — nem maradt menthető kép. */
    function showSaveSkipped() { saveSkipped.open() }

    /** „Figyelmeztetés: eltérő formátumok" (9.1). */
    function askFormatMismatch() { formatMismatch.open() }

    /** „Lecseréli a meglévőt, vagy újat hoz létre?" (9.2). */
    function askReplace() { replaceDialog.open() }

    /** A mentetlen módosítás háromgombos kérdése (3.3). */
    function askClose() { closeConfirm.open() }

    /** „Megszakítja a kollázs létrehozását?" (9.1). */
    function askCancel() { cancelConfirm.open() }

    /** „%1 kép nem található…" (9.4). */
    function showMissing(count) {
        missingDialog.count = count
        missingDialog.open()
    }

    /** „Kötelező a kijelölés" (10/b.1). */
    function showSelectionRequired() { selectionRequired.open() }

    readonly property bool anyVisible:
        saveSkipped.visible || formatMismatch.visible || replaceDialog.visible
        || closeConfirm.visible || cancelConfirm.visible
        || missingDialog.visible || selectionRequired.visible

    // --- 9.1 „Mentés mellőzve" ---------------------------------------------

    Dialog {
        id: saveSkipped
        objectName: "collageSaveSkippedDialog"
        modal: true
        title: qsTr("Save Skipped")
        closePolicy: Popup.CloseOnEscape
        anchors.centerIn: parent ? Overlay.overlay : undefined
        standardButtons: Dialog.Ok

        Text {
            objectName: "collageSaveSkippedMessage"
            width: 340
            text: qsTr("The collage cannot be saved because all of the pictures "
                       + "have been removed. Add at least one picture and try "
                       + "again.")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    // --- 9.1 „Figyelmeztetés: eltérő formátumok" ---------------------------

    Dialog {
        id: formatMismatch
        objectName: "collageFormatMismatchDialog"
        modal: true
        title: qsTr("Format Mismatch Warning")
        closePolicy: Popup.CloseOnEscape
        anchors.centerIn: parent ? Overlay.overlay : undefined

        ColumnLayout {
            spacing: 12

            // ⚠️ A hosszú magyar szöveg TÖRDEL, nem elidál: a doboz-méretek
            // az angolra készültek, elidálva a felhasználó néma csonkot
            // látna — és pont a megoldást tartalmazó zárójeles tippet
            // veszítené el.
            Text {
                objectName: "collageFormatMismatchMessage"
                Layout.preferredWidth: 380
                text: qsTr("The page format of the collage does not match the "
                           + "format of your display. This may result in a "
                           + "desktop background that does not look as "
                           + "expected. (TIP: Choose „Current display” "
                           + "in the Page Format dropdown menu.)")
                wrapMode: Text.WordWrap
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }

            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: 8

                PicasaButton {
                    objectName: "collageFormatSetAnywayButton"
                    text: qsTr("Set Anyway")
                    accent: Theme.picasaGreen
                    onClicked: {
                        formatMismatch.close()
                        dialogs.formatIgnored()
                    }
                }
                PicasaButton {
                    objectName: "collageFormatDontSetButton"
                    text: qsTr("Don't Set")
                    onClicked: {
                        formatMismatch.close()
                        dialogs.formatRejected()
                    }
                }
            }
        }
    }

    // --- 9.2 „Lecseréli a meglévőt, vagy újat hoz létre?" ------------------

    Dialog {
        id: replaceDialog
        objectName: "collageReplaceDialog"
        modal: true
        title: qsTr("Confirm…")
        closePolicy: Popup.CloseOnEscape
        anchors.centerIn: parent ? Overlay.overlay : undefined

        ColumnLayout {
            spacing: 12

            Text {
                objectName: "collageReplaceMessage"
                Layout.preferredWidth: 360
                text: qsTr("Would you like to replace the existing one, or "
                           + "create a new one?")
                wrapMode: Text.WordWrap
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }

            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: 8

                PicasaButton {
                    objectName: "collageReplaceExistingButton"
                    text: qsTr("Replace Existing")
                    accent: Theme.picasaGreen
                    onClicked: {
                        replaceDialog.close()
                        dialogs.replaceExisting()
                    }
                }
                PicasaButton {
                    objectName: "collageCreateNewButton"
                    text: qsTr("Create New")
                    onClicked: {
                        replaceDialog.close()
                        dialogs.createNew()
                    }
                }
                PicasaButton {
                    objectName: "collageReplaceCancelButton"
                    text: qsTr("Cancel")
                    onClicked: replaceDialog.close()
                }
            }
        }
    }

    // --- 3.3 A mentetlen módosítás háromgombos kérdése ---------------------

    Dialog {
        id: closeConfirm
        objectName: "collageCloseConfirmDialog"
        modal: true
        title: qsTr("Confirm…")
        closePolicy: Popup.CloseOnEscape
        anchors.centerIn: parent ? Overlay.overlay : undefined

        ColumnLayout {
            spacing: 12

            Text {
                objectName: "collageCloseConfirmMessage"
                Layout.preferredWidth: 380
                text: qsTr("The current collage contains unsaved changes.\n\n"
                           + "Would you like to save or discard them before "
                           + "closing the tab? (Note: drafts are saved to the "
                           + "Collages album.)\n\n"
                           + "Click Cancel to leave the tab open.")
                wrapMode: Text.WordWrap
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }

            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: 8

                PicasaButton {
                    objectName: "collageSaveDraftButton"
                    text: qsTr("Save Draft")
                    accent: Theme.picasaGreen
                    onClicked: {
                        closeConfirm.close()
                        dialogs.closeWithDraft()
                    }
                }
                PicasaButton {
                    objectName: "collageDiscardChangesButton"
                    text: qsTr("Discard Changes")
                    onClicked: {
                        closeConfirm.close()
                        dialogs.closeDiscardingChanges()
                    }
                }
                PicasaButton {
                    objectName: "collageCloseCancelButton"
                    text: qsTr("Cancel")
                    onClicked: closeConfirm.close()
                }
            }
        }
    }

    // --- 9.1 „Megszakítja a kollázs létrehozását?" -------------------------

    Dialog {
        id: cancelConfirm
        objectName: "collageCancelConfirmDialog"
        modal: true
        title: qsTr("Confirm…")
        closePolicy: Popup.CloseOnEscape
        anchors.centerIn: parent ? Overlay.overlay : undefined

        ColumnLayout {
            spacing: 12

            Text {
                objectName: "collageCancelConfirmMessage"
                Layout.preferredWidth: 340
                text: qsTr("Cancel creating the collage?")
                wrapMode: Text.WordWrap
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }

            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: 8

                PicasaButton {
                    objectName: "collageCancelCollageButton"
                    text: qsTr("Cancel Collage")
                    onClicked: {
                        cancelConfirm.close()
                        dialogs.cancelConfirmed()
                    }
                }
                PicasaButton {
                    objectName: "collageDontCancelButton"
                    text: qsTr("Don't Cancel")
                    accent: Theme.picasaGreen
                    onClicked: cancelConfirm.close()
                }
            }
        }
    }

    // --- 9.4 Hiányzó képek -------------------------------------------------

    Dialog {
        id: missingDialog
        objectName: "collageMissingImagesDialog"
        modal: true
        title: qsTr("Confirm…")
        closePolicy: Popup.CloseOnEscape
        anchors.centerIn: parent ? Overlay.overlay : undefined
        standardButtons: Dialog.Ok

        property int count: 0

        Text {
            objectName: "collageMissingImagesMessage"
            width: 340
            text: qsTr("%1 pictures could not be found, so they cannot be "
                       + "displayed…").arg(missingDialog.count)
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    // --- 10/b.1 „Kötelező a kijelölés" -------------------------------------

    Dialog {
        id: selectionRequired
        objectName: "collageSelectionRequiredDialog"
        modal: true
        title: qsTr("Selection Required")
        closePolicy: Popup.CloseOnEscape
        anchors.centerIn: parent ? Overlay.overlay : undefined
        standardButtons: Dialog.Ok

        Text {
            objectName: "collageSelectionRequiredMessage"
            width: 340
            text: qsTr("Please select the single image you want to place in "
                       + "the center of the collage BEFORE pressing this "
                       + "button.")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }
}
