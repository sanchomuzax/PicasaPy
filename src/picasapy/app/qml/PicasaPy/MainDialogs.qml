import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PicasaPy

Item {
    id: rootDialogs
    property alias clearGeotagDialog: _clearGeotagDialog
    property alias bulkTagConfirmLoader: _bulkTagConfirmLoader
    property alias setGeotagDialog: _setGeotagDialog
    property alias dropGeotagDialog: _dropGeotagDialog
    property alias panelClearGeotagDialog: _panelClearGeotagDialog
    property alias undoAllEditsDialog: _undoAllEditsDialog
    property alias languageConfirmDialog: _languageConfirmDialog
    property alias wallpaperConfirmDialog: _wallpaperConfirmDialog

    // #5836: a mért eredeti cím és a két gomb kell, ezért ez nem a közös
    // pipás/Mégse-vel működő ConfirmDialog-komponens.
    // #1404: a geocímke-törlés MEGERŐSÍTÉSE. Az eredeti `ClearGeoTag::warn`
    // szövegével, szó szerint - nem átfogalmazva.
    //
    // ⚠️ Ez nem stílusdöntés: a törlés VISSZAFORDÍTHATATLAN (a `geotag`
    // kulcs kikerül a `.picasa.ini`-ből), és eddig kérdés NÉLKÜL futott le
    // a Helyek panel gombjáról. Mindkét belépési pont - a menüpont és a
    // panel gombja - ezen az EGY párbeszéden megy át.
    //: #1612: halasztva - a geocímke-törlés megerősítése csak a menüpont/panel útján kell
    DeferredDialog {
        id: _clearGeotagDialog
        //: a BUROK neve - a #1612 őre ezen hívja az `ensure()`-t, és
        //: ezzel bizonyítja, hogy induláskor tényleg nincs példány
        objectName: "clearGeotagDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "clearGeotagConfirm"
                namePrefix: "clearGeotag"
                title: qsTr("Clear Geotags")
                property var rows: []
                function openFor(rowList) {
                    if (!rowList || rowList.length === 0) return
                    rows = rowList
                    //: `ClearGeoTag::warn` - az eredeti szövege
                    ask("clearGeotag", qsTr(
                        "You are about to erase all geographic location information"
                        + " (i.e., latitude and longitude) from the selected photos."
                        + "\n\nOK to proceed?"))
                }
                onConfirmed: controller.clearGeotagRows(rows)
            }
        }
    }

    // #4271: a CThumbUI::keyword_warning_fmt csak 30 kijelölt kép fölött
    // kérdez. Mégse esetén nincs címkézés; OK esetén a megnyitáskori
    // kijelölés pillanatfelvételére írunk.
    DeferredDialog {
        id: _bulkTagConfirmLoader
        objectName: "bulkTagConfirmDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            Dialog {
                id: bulkTagConfirmDialog
                objectName: "bulkTagConfirmDialog"
                modal: true
                focus: true
                anchors.centerIn: Overlay.overlay
                property var rows: []
                property string keyword: ""
                property string message: ""

                function askFor(rowList, tag) {
                    rows = rowList.slice()
                    keyword = tag
                    message = qsTr(
                        "You have a fairly large number of items selected.\n\n"
                        + "Are you sure you want to apply this tag to all %d items?"
                    ).replace("%d", String(rowList.length))
                    open()
                }

                onAccepted: {
                    if (controller) controller.addKeywordToRows(rows, keyword)
                }

                contentItem: ColumnLayout {
                    spacing: 12
                    Text {
                        objectName: "bulkTagConfirmMessage"
                        Layout.preferredWidth: 320
                        text: bulkTagConfirmDialog.message
                        wrapMode: Text.WordWrap
                        font.pixelSize: Theme.fontSize
                        color: Theme.ink
                    }
                    RowLayout {
                        Layout.alignment: Qt.AlignRight
                        spacing: 8
                        PicasaButton {
                            objectName: "bulkTagConfirmOkButton"
                            text: qsTr("OK")
                            accent: Theme.picasaGreen
                            onClicked: bulkTagConfirmDialog.accept()
                        }
                        PicasaButton {
                            objectName: "bulkTagConfirmCancelButton"
                            text: qsTr("Cancel")
                            onClicked: bulkTagConfirmDialog.reject()
                        }
                    }
                }
            }
        }
    }

    // #2013: a Helyek PANEL saját két megerősítése. Az eredetiben ez KÉT
    // KÜLÖN erőforrás a menüparancsétól (`ClearGeoTag::warn`) - más
    // küszöbbel és más számmal:
    //
    //   hely MEGVÁLTOZTATÁSA  > 20 KIJELÖLT elem   (0x00652585, cmp ebx,0x14)
    //   hely TÖRLÉSE          >  5 GEOCÍMKÉZETT    (0x006527ad, cmp esi,5)
    //
    // A küszöb alatt az eredeti NEM kérdez - ezért itt sem kérdezünk.
    //: #1612: halasztva - a helyváltoztatás megerősítése (küszöb fölött) csak a panel/menü útján kell
    DeferredDialog {
        id: _setGeotagDialog
        //: a BUROK neve - a #1612 őre ezen hívja az `ensure()`-t, és
        //: ezzel bizonyítja, hogy induláskor tényleg nincs példány
        objectName: "setGeotagDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "setGeotagConfirm"
                namePrefix: "setGeotag"
                title: qsTr("Change Location")
                property var rows: []
                property real lat: 0
                property real lon: 0
                function futtasd(rowList, latitude, longitude) {
                    if (!rowList || rowList.length === 0) return
                    if (rowList.length <= controller.geoChangeConfirmThreshold) {
                        controller.setGeotagRows(rowList, latitude, longitude)
                        return
                    }
                    rows = rowList; lat = latitude; lon = longitude
                    //: `GeoPanel::geotag_warning_change` - az eredeti szövege
                    ask("setGeotag", qsTr(
                        "You have more than a few items selected."
                        + "\n\nAre you sure you want to change the location of all"
                        + " %1 items?").arg(rowList.length))
                }
                onConfirmed: controller.setGeotagRows(rows, lat, lon)
            }
        }
    }

    // A térképre ejtés az eredeti Picasa szerint mindig külön megerősítést
    // kér; az elfogadás ugyanazt az INI-író utat hívja, mint a panel helye.
    DeferredDialog {
        id: _dropGeotagDialog
        objectName: "dropGeotagDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            Dialog {
                id: dialog
                objectName: "dropGeotagConfirm"
                modal: true
                focus: true
                anchors.centerIn: parent ? Overlay.overlay : undefined
                property var rows: []
                property real latitude: 0
                property real longitude: 0
                property string message: ""

                function futtasd(rowList, lat, lon) {
                    if (!rowList || rowList.length === 0) return
                    rows = rowList.slice()
                    latitude = lat
                    longitude = lon
                    var moving = controller.geotaggedCount(rows) > 0
                    if (rows.length === 1) {
                        message = moving ? qsTr("Move photo here?")
                                         : qsTr("Put photo here?")
                    } else {
                        var template = moving
                            ? qsTr("Move %d photos here?")
                            : qsTr("Put %d photos here?")
                        message = template.replace("%d", String(rows.length))
                    }
                    open()
                }

                onAccepted: controller.setGeotagRows(rows, latitude, longitude)

                ColumnLayout {
                    spacing: 12
                    Text {
                        objectName: "dropGeotagMessage"
                        Layout.preferredWidth: 320
                        text: dialog.message
                        wrapMode: Text.WordWrap
                        font.pixelSize: Theme.fontSize
                        color: Theme.ink
                    }
                    RowLayout {
                        Layout.alignment: Qt.AlignRight
                        spacing: 8
                        PicasaButton {
                            objectName: "dropGeotagYesButton"
                            text: qsTr("(OK)")
                            accent: Theme.picasaGreen
                            onClicked: dialog.accept()
                        }
                        PicasaButton {
                            objectName: "dropGeotagCancelButton"
                            text: qsTr("Cancel")
                            onClicked: dialog.reject()
                        }
                    }
                }
            }
        }
    }

    //: #1612: halasztva - a Helyek panel törlés-megerősítése csak onnan nyílik
    DeferredDialog {
        id: _panelClearGeotagDialog
        //: a BUROK neve - a #1612 őre ezen hívja az `ensure()`-t, és
        //: ezzel bizonyítja, hogy induláskor tényleg nincs példány
        objectName: "panelClearGeotagDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "panelClearGeotagConfirm"
                namePrefix: "panelClearGeotag"
                title: qsTr("Clear Geotags")
                property var rows: []
                function futtasd(rowList) {
                    if (!rowList || rowList.length === 0) return
                    //: ⚠️ a küszöb a GEOCÍMKÉZETT elemek száma, nem a kijelölésé:
                    //: 100 kijelöltből 3 geocímkézettnél az eredeti nem kérdez.
                    var geos = controller.geotaggedCount(rowList)
                    if (geos <= controller.geoClearConfirmThreshold) {
                        controller.clearGeotagRows(rowList)
                        return
                    }
                    rows = rowList
                    //: `GeoPanel::geotag_warning_clear` - az eredeti szövege
                    ask("panelClearGeotag", qsTr(
                        "You have more than a few items selected."
                        + "\n\nAre you sure you want to clear the locations for all"
                        + " %1 items?").arg(geos))
                }
                onConfirmed: controller.clearGeotagRows(rows)
            }
        }
    }

    //: #1612: halasztva - a „minden szerkesztés visszavonása" megerősítése csak a menüpontból nyílik
    DeferredDialog {
        id: _undoAllEditsDialog
        //: a BUROK neve - a #1612 őre ezen hívja az `ensure()`-t, és
        //: ezzel bizonyítja, hogy induláskor tényleg nincs példány
        objectName: "undoAllEditsDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            Dialog {
                id: undoAllEditsConfirmDialog
                objectName: "undoAllEditsDialog"
                //: Az eredeti cím: `ytApp::ConfirmTitle`.
                title: qsTr("Confirm")
                modal: true
                focus: true
                anchors.centerIn: parent ? Overlay.overlay : undefined
                property var rows: []
                property string message: ""
                // #465: az eredeti Picasa KÉT külön szöveget használ egy, illetve
                // több képre (IDS_CONFIRMREVERT / IDS_CONFIRMREVERT_MULTIPLE) - a
                // többesszámúban a „MINDEGYIK" nagybetűs. Ha a kijelölésben van
                // vörösszem-javítás, az eredeti KÜLÖN is figyelmeztet rá
                // (IDS_CONFIRM_REDEYE_REVERT): az régió-adat, és a törléssel
                // véglegesen elvész.
                // Az egyparaméteres openFor szerződését megtartjuk: a néző és
                // a #3573 régi őre is ezt hívja, a könyvtári menük külön kérik
                // a mért többes szöveget.
                function openFor(rowList) {
                    openWithText(rowList, false)
                }
                function openForLibrary(rowList) {
                    openWithText(rowList, true)
                }
                function openWithText(rowList, useMultipleText) {
                    if (rowList.length === 0) return
                    rows = rowList
                    //: `IDS_CONFIRMREVERT` / `IDS_CONFIRMREVERT_MULTIPLE` -
                    //: az eredeti szövege, a záró kérdéssel együtt (#3573)
                    var singlePicture = rowList.length === 1 && !useMultipleText
                    var text = singlePicture
                        ? qsTr("This will remove all edits you have made to the"
                               + " current picture.  Do you want to continue?")
                        : qsTr("This will remove all edits you have made to ALL of"
                               + " the selected pictures.  Do you want to continue?")
                    // #3573: az eredeti a képet NÉVVEL mondja; több
                    // vörösszemes kép esetén a nevek vesszővel sorakoznak
                    var redeyeNames = controller.redeyeNamesInSelection(rowList)
                    if (redeyeNames.length > 0)
                        //: `IDS_CONFIRM_REDEYE_REVERT` - az eredeti szövege a
                        //: sortörésekkel; %1 a kép neve (#3573)
                        text += "\n\n" + qsTr("Red eye fixes have been applied to %1.\n"
                                              + "If you remove all edits, your red eye"
                                              + " fixes cannot be recovered with redo. \n"
                                              + "Are you sure you want to remove the"
                                              + " fixes forever?")
                                              .arg(redeyeNames.join(", "))
                    // A job-254 útján a könyvtárnézet egyetlen kijelölése is
                    // ezt a többes szöveget és minden alkalommal megerősítést kér.
                    message = text
                    open()
                }
                onAccepted: controller.clearAllEffectsMany(rows)

                ColumnLayout {
                    spacing: 12

                    Text {
                        objectName: "undoAllEditsMessageLabel"
                        Layout.preferredWidth: 320
                        text: undoAllEditsConfirmDialog.message
                        wrapMode: Text.WordWrap
                        font.pixelSize: Theme.fontSize
                        color: Theme.ink
                    }

                    RowLayout {
                        Layout.alignment: Qt.AlignRight
                        spacing: 8

                        PicasaButton {
                            objectName: "undoAllEditsYesButton"
                            //: `IDS_CONFIRMREVERT_MULTIPLE_YES_BUTTON`.
                            text: qsTr("Remove Edits")
                            accent: Theme.picasaGreen
                            focus: true
                            onClicked: undoAllEditsConfirmDialog.accept()
                        }
                        PicasaButton {
                            objectName: "undoAllEditsNoButton"
                            //: Az eredeti `confirm:confirm/no.title` felirata.
                            text: qsTr("No")
                            onClicked: undoAllEditsConfirmDialog.reject()
                        }
                    }
                }
            }
        }
    }

    // #3555: a nyelvváltás megerősítése - az Eszközök → Nyelv menüből jön
    // (`bar.languageConfirmRequested`, ld. fent). A szöveg a hivatalos
    // `CGeneralPrefsPage::LangChange`. A `settingKey` üres: ez a
    // választás sosem nyomható el a „Ne kérdezze újra" jelölővel - minden
    // váltás legalább egy kattintást kér, ahogy az eredeti is teszi.
    DeferredDialog {
        id: _languageConfirmDialog
        objectName: "menuLanguageConfirmDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "menuLanguageConfirmDialog"
                namePrefix: "menuLanguageConfirm"
                property string candidateCode: ""
                function askFor(code) {
                    candidateCode = code
                    ask("", qsTr("Change the language PicasaPy uses?\n\nIt will change the next time PicasaPy is opened."))
                }
                onConfirmed: if (controller) controller.setLanguage(candidateCode)
            }
        }
    }

    // #6295: a Create > Set as Desktop parancs az asztal megváltoztatása
    // előtt kéri a felhasználó megerősítését.
    DeferredDialog {
        id: _wallpaperConfirmDialog
        objectName: "wallpaperConfirmDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "wallpaperConfirmDialog"
                namePrefix: "wallpaperConfirm"
                title: qsTr("Confirm")
                //: IDS_CONFIRM_SET_DESKTOP_YES_BUTTON — az eredeti gombfelirat.
                yesText: qsTr("Set Desktop")
                //: Az eredeti `confirm:confirm/no.title` felirata.
                noText: qsTr("No")
                cancelVisible: false
                rememberVisible: false
                focusYesOnOpen: true
                property int pendingRow: -1
                function openFor(row) {
                    if (row < 0) return
                    pendingRow = row
                    //: IDS_CONFIRM_SET_DESKTOP — az eredeti szöveg két
                    //: mondata között két szóközzel.
                    ask("", qsTr("This will replace your current desktop background with the current image.  Are you sure you want to proceed?"))
                }
                onConfirmed: {
                    var row = pendingRow
                    pendingRow = -1
                    if (controller && row >= 0)
                        controller.setPhotoAsDesktopBackground(row)
                }
                onDenied: pendingRow = -1
                onCanceled: pendingRow = -1
            }
        }
    }

}
