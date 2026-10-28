import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: printSettingsPanel
    property var printWindow
    property var printOptionsPanel
    property alias sizeBox: printSizeBox
    property alias printAreaVisible: printSettingsChildren.visible
    default property alias content: printSettingsChildren.data
    spacing: 10

    // -- szegély és felirat (#1780) -----------------------------------
    PicasaButton {
        id: printOptionsButton
        objectName: "printOptionsButton"
        Layout.fillWidth: true
        text: qsTr("Border and Text Options")
        enabled: printSettingsPanel.printWindow.printCtl !== null
        hoverEnabled: true
        onClicked: printSettingsPanel.printOptionsPanel.showOptions()

        ToolTip {
            objectName: "printOptionsTooltip"
            parent: printOptionsButton
            text: qsTr("Configure borders and text for Photos to be printed")
            visible: printOptionsButton.hovered
            delay: Theme.tooltipDelay
        }
    }

    // -- nyomatméret + minőség-ellenőrzés (#1782) ---------------------
    // Az eredeti panel a választott mérethez kiszámolja minden kép
    // effektív felbontását, és nyomtatás ELŐTT szól, ha valamelyik túl
    // kicsi. Enélkül egy 640×480-as kép szó nélkül ment ki 8×10-re.
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 2
        Text {
            text: qsTr("Print size:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        //: Az eredeti azonosítók sorrendje; a Contact Sheet elrendezése
        //: és a Passport Photo forrása a saját külön útján marad.
        PicasaComboBox {
            id: printSizeBox
            objectName: "printSizeBox"
            Layout.fillWidth: true
            model: printSettingsPanel.printWindow.printSizeOptions
            textRole: "label"
            enabledRole: "enabled"
            currentIndex: printSettingsPanel.printWindow.printSizeIds.indexOf(
                printSettingsPanel.printWindow.contactSheet
                    ? "CONTACT" : printSettingsPanel.printWindow.printSize)
            //: #1401: az útlevélparancs külön forrásútja megőrzi az
            //: eredeti Passport azonosítót a teljes méretkatalógusban.
            displayText: currentIndex < 0
                ? (printSettingsPanel.printWindow.printSizeLabelById[
                    printSettingsPanel.printWindow.printSize] || "")
                : currentText
            onActivated: {
                var azonosito = printSettingsPanel.printWindow.printSizeIds[currentIndex]
                if (!azonosito) return
                if (azonosito === "CDSIZE") {
                    printSizeBox.currentIndex =
                        printSettingsPanel.printWindow.printSizeIds.indexOf(
                            printSettingsPanel.printWindow.printSize)
                    return
                }
                if (azonosito === "CONTACT") {
                    // #3712: az Indexképek nem CELLAMÉRET — a
                    // `setPrintSize` a #1961 készletén kívüli nevet
                    // úgyis elutasítaná, ezért nem is hívjuk.
                    printSettingsPanel.printWindow.contactSheet = true
                } else {
                    printSettingsPanel.printWindow.valasszNyomatmeretet(azonosito)
                }
                if (azonosito === "CONTACT")
                    printSettingsPanel.printWindow.frissitsdAMinoseget()
            }
        }

        // #4318 / options.fen: a beállítás öt nyomtatható méretgombhoz
        // rendel méretet; ezek a gombok közvetlenül a vezérlőn választják
        // ki és mentik az adott nyomatméretet.
        RowLayout {
            Layout.fillWidth: true
            spacing: 4
            Repeater {
                objectName: "printSizePresetRepeater"
                model: printSettingsPanel.printWindow.printSizePresetIds.length
                delegate: PicasaButton {
                    objectName: "printPresetSize" + index
                    Layout.fillWidth: true
                    text: printSettingsPanel.printWindow.printSizeLabelById[
                        printSettingsPanel.printWindow.printSizePresetIds[index]]
                    enabled: printSettingsPanel.printWindow.printCtl !== null
                        && typeof printController !== "undefined"
                        && printController !== null
                        && printController.canUsePrintSizePreset(
                            printSettingsPanel.printWindow.printSizePresetIds[index])
                    onClicked: printSettingsPanel.printWindow.valasszNyomatmeretet(
                        printSettingsPanel.printWindow.printSizePresetIds[index])
                }
            }
            PicasaButton {
                objectName: "printPresetFullPage"
                Layout.fillWidth: true
                text: printSettingsPanel.printWindow.printSizeLabelById["TELJES_OLDAL"]
                enabled: printSettingsPanel.printWindow.printCtl !== null
                onClicked: printSettingsPanel.printWindow.valasszNyomatmeretet(
                    "TELJES_OLDAL")
            }
        }

        // #1590/#3712: az indexkép rácsának oszlopszáma — csak akkor
        // látszik, ha a fenti listában az Indexképek van kijelölve.
        RowLayout {
            Layout.fillWidth: true
            visible: printSettingsPanel.printWindow.contactSheet
            spacing: 6
            Text {
                text: qsTr("Columns:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            SpinBox {
                objectName: "printContactColumnsBox"
                from: 1
                to: 10
                value: printSettingsPanel.printWindow.contactColumns
                onValueModified: {
                    printSettingsPanel.printWindow.contactColumns = value
                    printSettingsPanel.printWindow.frissitsdAzElonezetet()
                }
            }
            Item { Layout.fillWidth: true }
        }

        // A nyomatpéldányszám, az előnézet és a minőségi figyelmeztetés
        // ugyanennek az eredeti ColumnLayoutnak a gyermekei. Az alias
        // lehetővé teszi, hogy a PrintDialog.qml forráskontextusa megmaradjon.
        ColumnLayout {
            id: printSettingsChildren
            Layout.fillWidth: true
            spacing: 2
        }
    }
}
