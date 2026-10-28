import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    required property var hostWindow
    required property var sourceFolderDialog
    required property var sourceFilesDialog
    Layout.fillWidth: true
    spacing: 8

    Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: qsTr(
            "Import pictures and videos from another folder (e.g. a "
            + "mounted camera or memory card) into your library.")
        font.pixelSize: Theme.fontSize
        color: Theme.textGray
    }

    // -- forrás ------------------------------------------------------
    RowLayout {
        objectName: "importSourceFromMenu"
        Layout.fillWidth: true
        spacing: 8
        Text {
            text: qsTr("Source:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        Text {
            objectName: "importSourcePathText"
            Layout.fillWidth: true
            elide: Text.ElideMiddle
            text: hostWindow.sourceFolderDisplay.length > 0
                  ? hostWindow.sourceFolderDisplay
                  : qsTr("(none selected)")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        // #441: a korábbi importok listája — az eredeti legördülője is
        // ezt kínálta a „Choose…" mellett (`LastImport…`)
        PicasaComboBox {
            objectName: "importSourceRecentBox"
            Layout.preferredWidth: 180
            visible: model.length > 0
            model: (typeof importSourceController !== "undefined"
                    && importSourceController)
                   ? importSourceController.recentSources : []
            displayText: qsTr("Recent sources")
            onActivated: {
                hostWindow.sourceFiles = []
                hostWindow.sourceFolder = model[currentIndex]
                hostWindow.scanCurrentSource()
            }
        }
        PicasaComboBox {
            objectName: "importSourceMountedSourcesBox"
            Layout.preferredWidth: 170
            visible: count > 0
            textRole: "label"
            displayText: qsTr("Removable drives")
            model: hostWindow.mountedSourceOptions
            onActivated: {
                var source = model[currentIndex]
                if (!source) return
                hostWindow.sourceFiles = []
                hostWindow.sourceFolder = source.path
                hostWindow.scanCurrentSource()
            }
        }
        // #4596: a „Tallózás…” kételemű menüt nyit: mappa vagy fájlok
        // (az eredeti tallózó „Fájlok/mappa importálása” ablaka mindkettőt
        // kínálta)
        PicasaButton {
            id: chooseSourceButton
            objectName: "importSourceChooseSourceButton"
            text: qsTr("Browse...")
            onClicked: chooseSourceMenu.popup(chooseSourceButton, 0,
                                              chooseSourceButton.height)
        }
        PicasaMenu {
            id: chooseSourceMenu
            objectName: "importSourceChooseMenu"
            MenuItem {
                objectName: "importSourceChooseFolderItem"
                text: qsTr("Folder...")
                onTriggered: sourceFolderDialog.open()
            }
            MenuItem {
                objectName: "importSourceChooseFilesItem"
                text: qsTr("Files...")
                onTriggered: sourceFilesDialog.open()
            }
        }
    }

    // #441: fájltípus-szűrő — az eredeti tallózó három szűrőt kínált
    // („Picture and Movie Files" / „Picture Files" / „All Files").
    // Ugyanez a három fokozat a BEOLVASÁSRA is vonatkozik (mappánál és
    // fájllistánál egyaránt): mi számítson importálandó jelöltnek.
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        Text {
            text: qsTr("File types:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        PicasaComboBox {
            objectName: "importSourceMediaFilterBox"
            Layout.preferredWidth: 220
            readonly property var filterKeys:
                ["pictures_and_movies", "pictures", "all"]
            model: [qsTr("Picture and Movie Files"),
                    qsTr("Picture Files"),
                    qsTr("All Files")]
            currentIndex: {
                if (typeof importSourceController === "undefined"
                        || !importSourceController) return 0
                var i = filterKeys.indexOf(importSourceController.mediaFilter)
                return i < 0 ? 0 : i
            }
            onActivated: {
                importSourceController.setMediaFilter(filterKeys[currentIndex])
                // a szűrő a KÖVETKEZŐ beolvasásra érvényes — ha már van
                // kiválasztott forrás, azonnal újraolvassuk
                if (hostWindow.hasSource)
                    hostWindow.scanCurrentSource()
            }
        }
    }

    // #441: "Exclude Duplicates" — "Exclude photos that are already
    // imported into Picasa" (autoexclude QSettings-kulcs, a
    // controller property-je).
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        CheckBox {
            objectName: "importSourceAutoExcludeCheckBox"
            text: qsTr("Exclude Duplicates")
            // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
            // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
            checked:
                (typeof importSourceController !== "undefined" && importSourceController
                    && importSourceController.autoExclude !== undefined)
                        ? importSourceController.autoExclude : false
            onToggled: importSourceController.setAutoExclude(checked)
        }
        Item { Layout.fillWidth: true }
        // A Picasa Web Albums szolgáltatás megszűnt, ezért a jelölő
        // látható marad, de online műveletet nem indíthat.
        CheckBox {
            objectName: "importSourceUploadCheckBox"
            text: qsTr("Upload")
            enabled: false
            property string helpText: qsTr("Upload to Picasa Web Albums...")
            ToolTip.visible: hovered
            ToolTip.text: helpText
            ToolTip.delay: Theme.tooltipDelay
        }
        PicasaButton {
            objectName: "importSourceOptionsButton"
            text: qsTr("Options")
            property string helpText: qsTr("Online options")
            ToolTip.visible: hovered
            ToolTip.text: helpText
            ToolTip.delay: Theme.tooltipDelay
            onClicked: onlineOptionsPopup.open()
        }
        Popup {
            id: onlineOptionsPopup
            objectName: "importSourceOnlineOptionsMenu"
            width: 250
            padding: 10
            contentItem: ColumnLayout {
                Text {
                    Layout.fillWidth: true
                    text: qsTr("Online options")
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                }
                CheckBox {
                    objectName: "importSourceSyncStarredOnlyCheckBox"
                    text: qsTr("Sync starred photos only")
                    enabled: false
                }
            }
        }
    }
    Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: qsTr("Exclude photos that are already imported into PicasaPy")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }
    Text {
        objectName: "importSourceDuplicateCountText"
        visible: hostWindow.duplicateCount > 0
        text: qsTr("%n of those are duplicates already in PicasaPy", "",
                   hostWindow.duplicateCount)
        font.pixelSize: Theme.fontSize
        color: Theme.textGray
    }

    Text {
        objectName: "importSourceErrorText"
        visible: hostWindow.lastError.length > 0
        text: hostWindow.lastError
        color: Theme.brandRed
        font.pixelSize: Theme.fontSize
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }

    BusyIndicator {
        objectName: "importSourceBusyIndicator"
        Layout.alignment: Qt.AlignHCenter
        running: hostWindow.scanning
        visible: hostWindow.scanning
    }

    Text {
        objectName: "importSourceCountText"
        visible: !hostWindow.scanning && hostWindow.previewCount > 0
        text: qsTr("%1 pictures/videos found").arg(hostWindow.previewCount)
        font.pixelSize: Theme.fontSize
        color: Theme.textGray
    }

    Text {
        objectName: "importSourceEmptyText"
        visible: !hostWindow.scanning
                 && hostWindow.hasSource
                 && hostWindow.previewCount === 0
                 && hostWindow.lastError.length === 0
        text: qsTr("No pictures or videos found in this folder.")
        font.pixelSize: Theme.fontSize
        color: Theme.textGray
    }

    // -- egyenkénti válogatás parancsai (#441) -------------------------
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        visible: hostWindow.previewCount > 0
        PicasaButton {
            objectName: "importSourceExcludeAllButton"
            text: qsTr("Exclude All")
            onClicked: importSourceController.excludeAll()
        }
        PicasaButton {
            objectName: "importSourceIncludeAllButton"
            text: qsTr("Include All")
            onClicked: importSourceController.includeAll()
        }
        Item { Layout.fillWidth: true }
        PicasaButton {
            objectName: "importSourcePreviousButton"
            text: "‹"
            enabled: hostWindow.previewItems.length > 0
                     && hostWindow.selectedPreviewIndex > 0
            property string helpText: qsTr("View the previous Photo")
            ToolTip.visible: hovered
            ToolTip.text: helpText
            ToolTip.delay: Theme.tooltipDelay
            onClicked: hostWindow.stepPreview(-1)
        }
        PicasaButton {
            objectName: "importSourceNextButton"
            text: "›"
            enabled: hostWindow.previewItems.length > 0
                     && hostWindow.selectedPreviewIndex
                            < hostWindow.previewItems.length - 1
            property string helpText: qsTr("View the next Photo")
            ToolTip.visible: hovered
            ToolTip.text: helpText
            ToolTip.delay: Theme.tooltipDelay
            onClicked: hostWindow.stepPreview(1)
        }
    }


}
