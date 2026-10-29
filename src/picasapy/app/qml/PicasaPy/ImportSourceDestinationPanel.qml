import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    required property var hostWindow
    required property var folderDialog
    Layout.fillWidth: true
    spacing: 8
    // -- cél + célmappa-elnevezés (#441) -------------------------------
    RowLayout {
        objectName: "importSourceFolderMenu"
        Layout.fillWidth: true
        spacing: 8
        Text {
            text: qsTr("Destination:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        Text {
            objectName: "importSourceDestPathText"
            Layout.fillWidth: true
            elide: Text.ElideMiddle
            text: hostWindow.destFolderDisplay.length > 0
                  ? hostWindow.destFolderDisplay
                  : qsTr("(none selected)")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        // #1785: a korábbi CÉLMAPPÁK — az eredeti a célt is megjegyzi
        // (`Preferences\LastImport%x`), és háromszakaszos menüben
        // kínálja: korábbi importok · alapértelmezett hely · „Choose…".
        // Nálunk a FORRÁSÉVAL AZONOS legördülő adja az első kettőt (az
        // alapértelmezett hely az utolsó tétel), a „Tallózás…" pedig a
        // mellette álló gomb — így a szakaszhatár is látszik.
        PicasaComboBox {
            id: destRecentBox
            objectName: "importSourceRecentDestBox"
            Layout.preferredWidth: 180
            readonly property var korabbiak:
                (typeof importSourceController !== "undefined"
                 && importSourceController)
                ? importSourceController.recentDestinations : []
            readonly property string alapertelmezett:
                (typeof importSourceController !== "undefined"
                 && importSourceController)
                ? importSourceController.defaultDestination : ""
            //: A lista VÉGÉN az alapértelmezett hely áll, külön
            //: tételként — az eredeti menü is külön szakaszba tette
            //: (`-seperator-before-default_location-`). Ha már a
            //: korábbiak közt szerepel, nem ismételjük meg.
            model: destRecentBox.alapertelmezett.length > 0
                   && destRecentBox.korabbiak.indexOf(
                          destRecentBox.alapertelmezett) < 0
                   ? destRecentBox.korabbiak.concat(
                         [destRecentBox.alapertelmezett])
                   : destRecentBox.korabbiak
            visible: model.length > 0
            displayText: qsTr("Recent destinations")
            onActivated: hostWindow.destFolder = model[currentIndex]
        }
        // #1555: ÁTMÉRETEZÉS importáláskor — öt kizáró opció, a mért
        // képpontértékekkel (0 = eredeti méret). A tárolt érték
        // KÉPPONT, nem sorszám (ld. `RESIZE_SETTINGS_KEY`).
        PicasaComboBox {
            id: resizeBox
            objectName: "importSourceResizeBox"
            Layout.preferredWidth: 150
            readonly property var opciok:
                (typeof importSourceController !== "undefined"
                 && importSourceController
                 && importSourceController.resizeOptions !== undefined)
                ? importSourceController.resizeOptions : [0]
            model: resizeBox.opciok.map(function (px) {
                return px === 0
                    ? qsTr("Original size")
                    : qsTr("%1 pixels").arg(px)
            })
            currentIndex: {
                if (typeof importSourceController === "undefined"
                    || !importSourceController
                    || importSourceController.resizeLimit === undefined)
                    return 0
                var i = resizeBox.opciok.indexOf(
                    importSourceController.resizeLimit)
                return i >= 0 ? i : 0
            }
            onActivated: {
                if (typeof importSourceController === "undefined"
                    || !importSourceController)
                    return
                importSourceController.setResizeLimit(
                    resizeBox.opciok[currentIndex])
            }
        }
        PicasaButton {
            objectName: "importSourceChooseDestButton"
            text: qsTr("Browse...")
            onClicked: folderDialog.open()
        }
    }

    ButtonGroup { id: namingModeGroup }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 2
        RadioButton {
            objectName: "importSourceNamingManualRadio"
            //: #3575: `iCAcquireUI::SubFolder`
            text: qsTr("Enter Folder Title")
            ButtonGroup.group: namingModeGroup
            checked: hostWindow.namingMode === "manual"
            onToggled: if (checked) hostWindow.namingMode = "manual"
        }
        TextField {
            id: manualFolderField
            objectName: "importSourceManualNameField"
            Layout.fillWidth: true
            Layout.leftMargin: 24
            enabled: hostWindow.namingMode === "manual"
            text: hostWindow.manualFolderName
            onTextEdited: hostWindow.manualFolderName = text
            onEditingFinished: hostWindow.manualFolderName = text
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
        }
        // #4595: cím nélkül nincs import — a tipp ezt mondja ki
        Text {
            objectName: "importSourceManualTipText"
            Layout.fillWidth: true
            Layout.leftMargin: 24
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            visible: hostWindow.namingMode === "manual"
                     && hostWindow.manualFolderName.trim().length === 0
            //: #4595: `acquirepanel/importtiptext` (Text1)
            text: qsTr("Enter new folder title or choose existing folder to continue")
        }
        RadioButton {
            objectName: "importSourceNamingByDateRadio"
            //: #3575: `iCAcquireUI::AutoDate`
            text: qsTr("Date Taken (YYYY-MM-DD)")
            ButtonGroup.group: namingModeGroup
            checked: hostWindow.namingMode === "date"
            onToggled: if (checked) hostWindow.namingMode = "date"
        }
        RadioButton {
            objectName: "importSourceNamingTodayRadio"
            //: #3575: `iCAcquireUI::TodayDate` („%s (Today)”) — a %s a mai
            //: mappa neve, ugyanabban az alakban, ahogy létrejön (ÉÉÉÉ-HH-NN)
            text: qsTr("%1 (Today)").arg(Qt.formatDate(new Date(), "yyyy-MM-dd"))
            ButtonGroup.group: namingModeGroup
            checked: hostWindow.namingMode === "today"
            onToggled: if (checked) hostWindow.namingMode = "today"
        }
    }

    // -- "After Copying:" háromállapotú forrás-törlés (#441) -----------
    Text {
        text: qsTr("After Copying:")
        font.pixelSize: Theme.fontSize
        font.bold: true
        color: Theme.ink
    }
    ButtonGroup { id: afterCopyingGroup }
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 2
        RadioButton {
            objectName: "importSourceAfterLeaveRadio"
            text: qsTr("Leave card alone")
            ButtonGroup.group: afterCopyingGroup
            checked: hostWindow.afterCopying === "leave"
            onToggled: if (checked) hostWindow.afterCopying = "leave"
        }
        RadioButton {
            objectName: "importSourceAfterDeleteCopiedRadio"
            text: qsTr("Delete only copied photos")
            ButtonGroup.group: afterCopyingGroup
            checked: hostWindow.afterCopying === "delete_copied"
            onToggled: if (checked) hostWindow.afterCopying = "delete_copied"
        }
        RadioButton {
            objectName: "importSourceAfterDeleteAllRadio"
            text: qsTr("Delete everything on card")
            ButtonGroup.group: afterCopyingGroup
            checked: hostWindow.afterCopying === "delete_all"
            onToggled: if (checked) hostWindow.afterCopying = "delete_all"
        }
    }

    // -- haladás -------------------------------------------------------
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 8
        visible: hostWindow.importing
        radius: 4
        color: Theme.trackBg
        border.color: Theme.chromeBorder

        Rectangle {
            objectName: "importSourceProgressFill"
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            radius: parent.radius
            color: Theme.picasaGreen
            width: hostWindow.importTotal > 0
                   ? parent.width * hostWindow.importDone
                         / hostWindow.importTotal
                   : 0
        }
    }

    Text {
        objectName: "importSourceProgressText"
        visible: hostWindow.importing
        // #441: az eredeti haladásjelzője a SEBESSÉGET is kiírta
        // („Copying %d of %d files at %s/sec") — amíg nincs mérhető
        // adat, a sebesség-rész egyszerűen kimarad
        text: hostWindow.importBytesPerSecond > 0
              ? qsTr("%1 / %2 imported at %3/sec")
                    .arg(hostWindow.importDone)
                    .arg(hostWindow.importTotal)
                    .arg(hostWindow.formatSpeed(
                             hostWindow.importBytesPerSecond))
              : qsTr("%1 / %2 imported")
                    .arg(hostWindow.importDone)
                    .arg(hostWindow.importTotal)
        font.pixelSize: Theme.fontSize
        color: Theme.textGray
    }

    Text {
        objectName: "importSourceResultText"
        visible: !hostWindow.importing
                 && hostWindow.lastCopiedCount >= 0
        text: qsTr("Done: %1 imported, %2 failed")
              .arg(hostWindow.lastCopiedCount)
              .arg(hostWindow.lastFailedCount)
        font.pixelSize: Theme.fontSize
        color: Theme.textGray
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        Item { Layout.fillWidth: true }
        PicasaButton {
            objectName: "importSourceStartButton"
            text: qsTr("Import")
            accent: Theme.picasaGreen
            enabled: hostWindow.includedCount > 0
                     && hostWindow.destFolder.length > 0
                     && !hostWindow.importing
                     && (hostWindow.namingMode !== "manual"
                         || hostWindow.manualNameValid)
            onClicked: hostWindow.requestImport()
        }
        PicasaButton {
            objectName: "importSourceCloseButton"
            text: qsTr("Close")
            onClicked: hostWindow.visible = false
        }
    }
}
