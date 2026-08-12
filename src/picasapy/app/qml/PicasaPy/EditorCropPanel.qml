import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő „Fotó vágása" panelje (#71/#448) — a képarány-listával, a
// gyorsvágás-gombokkal és a saját Alkalmaz/Mégse párral.
//
// #496: korábban az EditorPanel.qml-en belül élt; a fájl így a 800 soros
// elv több mint kétszerese volt. A gazda-panelre a `panel` tulajdonságon át
// hivatkozik (a `FolderStatePanel.qml` `manager`-mintája) — a jelzések és az
// állapot továbbra is az EditorPanel-é, ez a fájl csak a megjelenítés.
ColumnLayout {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel
    objectName: "cropColumn"
    visible: panel.cropActive
    opacity: panel.enabled ? 1 : 0.45
    anchors.margins: 10
    spacing: 8

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        Image {
            Layout.preferredWidth: 40
            Layout.preferredHeight: 30
            source: "../../assets/tools/crop.png"
        }
        Text {
            Layout.fillWidth: true
            text: qsTr("Crop Photo")
            font.pixelSize: Theme.fontSize + 3
            color: Theme.ink
        }
    }

    Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: qsTr("Choose a size below, then drag on the picture to "
                   + "select the area you want to keep.")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    // #448: a Kiegyenesítés-figyelmeztetés — az eredeti Picasa szó
    // szerinti szövege (a jegy idézi), csak akkor jelenik meg, ha a
    // képen MÁR van aktív kiegyenesítés (`straightenActive`, a hívó
    // tölti az editController.tiltParam-ből).
    Text {
        objectName: "cropStraightenWarning"
        visible: panel.straightenActive
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: qsTr("This image's orientation has been modified by the "
                   + "Straighten tool and might not crop accurately… "
                   + "try undoing the Straighten fix, then recrop, and "
                   + "Straighten again if necessary.")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    // arány-választó legördülő (Picasa-lista)
    Rectangle {
        objectName: "cropAspectCombo"
        Layout.fillWidth: true
        Layout.preferredHeight: 22
        radius: 2
        color: Theme.contentPanel
        border.color: Theme.chromeBorder
        Text {
            anchors.left: parent.left; anchors.leftMargin: 6
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - 28
            elide: Text.ElideRight
            text: panel.selectedPreset.label
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        Text {
            anchors.right: parent.right; anchors.rightMargin: 6
            anchors.verticalCenter: parent.verticalCenter
            text: "▼"; font.pixelSize: 8; color: Theme.textDark
        }
        MouseArea {
            anchors.fill: parent
            onClicked: aspectList.visible = !aspectList.visible
        }
    }
    Rectangle {
        id: aspectList
        objectName: "cropAspectList"
        visible: false
        Layout.fillWidth: true
        Layout.preferredHeight: visible ? aspectColumn.height + 2 : 0
        color: Theme.contentPanel
        border.color: Theme.chromeBorder
        Column {
            id: aspectColumn
            x: 1; y: 1
            width: parent.width - 2
            Repeater {
                model: panel.aspectFullList
                Rectangle {
                    id: aspectRow
                    required property var modelData
                    required property int index
                    width: aspectColumn.width; height: 20
                    color: aspectRowHover.hovered ? Theme.panelSelection
                           : "transparent"
                    Text {
                        anchors.left: parent.left; anchors.leftMargin: 6
                        anchors.right: aspectDeleteBtn.visible
                            ? aspectDeleteBtn.left : parent.right
                        anchors.rightMargin: 4
                        anchors.verticalCenter: parent.verticalCenter
                        elide: Text.ElideRight
                        text: aspectRow.modelData.label
                        font.pixelSize: Theme.fontSize
                        // a kijelölő-kék (Theme.panelSelection) hátteren
                        // szándékosan téma-független fehér a token
                        // (Theme.panelSelectionText) — nem új hardkód
                        color: aspectRowHover.hovered ? Theme.panelSelectionText : Theme.ink
                    }
                    // #448: az EGYÉNI (felhasználó felvette) arányok
                    // törölhetők — a beépített preset-eknek nincs "×".
                    Text {
                        id: aspectDeleteBtn
                        objectName: "cropAspectDelete" + aspectRow.index
                        visible: aspectRow.modelData.isCustom === true
                        anchors.right: parent.right; anchors.rightMargin: 6
                        anchors.verticalCenter: parent.verticalCenter
                        text: "✕"
                        font.pixelSize: Theme.fontSize - 1
                        color: aspectDeleteMouse.containsMouse
                               ? Theme.selectionBlue : Theme.textGray
                        MouseArea {
                            id: aspectDeleteMouse
                            anchors.fill: parent
                            anchors.margins: -4
                            hoverEnabled: true
                            onClicked: {
                                deleteCustomAspectConfirm.pendingName =
                                    aspectRow.modelData.customName
                                deleteCustomAspectConfirm.pendingWidth =
                                    aspectRow.modelData.customWidth
                                deleteCustomAspectConfirm.pendingHeight =
                                    aspectRow.modelData.customHeight
                                deleteCustomAspectConfirm.ask(
                                    "deleteCustomAspectRatio",
                                    qsTr("Delete this custom aspect ratio?"))
                            }
                        }
                    }
                    HoverHandler { id: aspectRowHover }
                    TapHandler {
                        onTapped: {
                            panel.selectAspect(aspectRow.index)
                            aspectList.visible = false
                        }
                    }
                }
            }
            // #448: "AddCustomAspectRatio" — a beépítettek alatt, saját
            // sorban (a jegy szerint a dialógus szélesség × magasság +
            // nevet kér, a lista "<szél> x <mag>   <név>" alakban mutatja).
            Rectangle {
                objectName: "cropAspectAddRow"
                width: aspectColumn.width; height: 20
                color: addAspectRowHover.hovered ? Theme.panelSelection
                       : "transparent"
                Text {
                    anchors.left: parent.left; anchors.leftMargin: 6
                    anchors.verticalCenter: parent.verticalCenter
                    text: qsTr("Add Custom Aspect Ratio…")
                    font.pixelSize: Theme.fontSize
                    color: addAspectRowHover.hovered
                           ? Theme.panelSelectionText : Theme.ink
                }
                HoverHandler { id: addAspectRowHover }
                TapHandler {
                    onTapped: {
                        aspectList.visible = false
                        addCustomAspectRatioDialog.open()
                    }
                }
            }
        }
    }

    // #448: HÁROM automatikus vágás-JAVASLAT. Az eredeti panelen is három
    // javaslat-gomb ült; a mögöttük álló stratégiák a binárisban nevesítve
    // vannak (arcokra szorosan · kompozíció az arcok köré · horizont ·
    // szín-dominancia · variancia). Melyik három jelenik meg, azt a kép
    // dönti el: ha van rajta mentett arc, az arc-stratégiák előznek.
    //
    // A feliratok kulcsból oldódnak fel (`panel.cropSuggestionLabel`), mert
    // a stratégiát a kontroller választja, nem a felület.
    Text {
        Layout.fillWidth: true
        visible: panel.cropSuggestions.length > 0
        text: qsTr("Suggested crops")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }
    RowLayout {
        objectName: "cropSuggestionRow"
        Layout.fillWidth: true
        spacing: 6
        visible: panel.cropSuggestions.length > 0

        // A javaslatok száma FIX három (az eredeti panelen is annyi volt),
        // ezért a három gomb kiírva áll, nem Repeaterrel: így mindegyiknek
        // állandó `objectName`-je van (a Repeater-delegátumok a
        // findChild-nek nem látszanak), és a kód is olvashatóbb.
        component SuggestionButton: PanelButton {
            property int slot: 0
            readonly property var suggestion: panel.cropSuggestions.length > slot
                ? panel.cropSuggestions[slot] : null
            visible: suggestion !== null
            label: suggestion ? panel.cropSuggestionLabel(suggestion.key) : ""
            onButtonClicked: if (suggestion) panel.cropSuggestionChosen(
                suggestion.x, suggestion.y, suggestion.w, suggestion.h)
        }
        SuggestionButton { objectName: "cropSuggestion0"; slot: 0 }
        SuggestionButton { objectName: "cropSuggestion1"; slot: 1 }
        SuggestionButton { objectName: "cropSuggestion2"; slot: 2 }
    }

    // gyorsvágások: bal-felső / fekvő / álló (Picasa három bélyegképe)
    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        PanelButton {
            objectName: "quickCropTopleft"
            label: qsTr("Top left")
            onButtonClicked: panel.quickCropRequested("topleft")
        }
        PanelButton {
            objectName: "quickCropLandscape"
            label: qsTr("Landscape")
            onButtonClicked: panel.quickCropRequested("landscape")
        }
        PanelButton {
            objectName: "quickCropPortrait"
            label: qsTr("Portrait")
            onButtonClicked: panel.quickCropRequested("portrait")
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        PanelButton {
            objectName: "cropRotateButton"
            label: qsTr("Rotate")
            onButtonClicked: panel.cropRotateRequested()
        }
        PanelButton {
            objectName: "cropPreviewButton"
            label: qsTr("Preview")
            // amíg nyomva tartják, a hívó a vágott képet mutatja
            MouseArea {
                anchors.fill: parent
                onPressed: panel.cropPreviewHold(true)
                onReleased: panel.cropPreviewHold(false)
                onCanceled: panel.cropPreviewHold(false)
            }
        }
    }

    PanelButton {
        objectName: "cropResetButton"
        label: qsTr("Reset")
        Layout.fillWidth: false
        Layout.preferredWidth: 120
        Layout.alignment: Qt.AlignHCenter
        onButtonClicked: panel.cropResetRequested()
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        PanelButton {
            objectName: "cropApplyButton"
            label: qsTr("Apply") + " ✔"
            onButtonClicked: panel.cropApplyRequested()
        }
        PanelButton {
            objectName: "cropCancelButton"
            label: qsTr("Cancel") + " ✘"
            onButtonClicked: panel.cropCancelRequested()
        }
    }
}
