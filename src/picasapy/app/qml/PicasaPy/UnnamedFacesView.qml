import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #26 (3. lépcső): a „Névtelenek" album felülete — SAJÁT (YuNet/SFace)
// arcfelismerés, a Picasa munkamenete szerint: „Group by face" / „Expand
// groups" kapcsolók, arconkénti kijelölés, „Add a name" tömeges névadás.
//
// Szándékosan ÖNÁLLÓ komponens (nem a fő rács/`controller._show()` útján),
// mert a `FaceScanController` is önálló QObject, NEM az `AppController`
// mixinje (ld. face_scan_controller.py modul-docstring) — a Main.qml csak
// egy Loader-szerű látszás/rejtés kapcsolót kap.
//
// Egyszerűsítés (jelentve az issue-ban): a bélyegkép a TELJES fotó, nem az
// arc-téglalapra vágott index-kép — a Picasa-hű arc-vágás egy későbbi
// kör finomítása.
ColumnLayout {
    id: root
    property var faceScanController: null
    // #26: „unnamed" = a Névtelenek album, „ignored" = a Mellőzött emberek
    // album (`CAlbumLabel::Ignored`). Az eredetiben ez két ALBUM volt
    // ugyanabban a listában, ezért ugyanaz a nézet szolgálja ki — csak a
    // tartalom és a művelet-gombok mások.
    property string mode: "unnamed"
    readonly property bool ignoredMode: root.mode === "ignored"
    property bool groupByFace: true
    property bool expandGroups: false
    property var groupsModel: []
    property var selectedFaceIds: ({})
    property int selectedCount: 0
    spacing: 8

    function reload() {
        if (!faceScanController) {
            root.groupsModel = []
            return
        }
        root.groupsModel = (root.mode === "ignored")
            ? faceScanController.ignoredGroups()
            : faceScanController.unnamedGroups(
                root.groupByFace, root.expandGroups)
    }

    function toggleFace(faceId) {
        var current = root.selectedFaceIds
        if (current[faceId]) {
            delete current[faceId]
        } else {
            current[faceId] = true
        }
        root.selectedFaceIds = current
        root.selectedCount = Object.keys(current).length
    }

    function clearSelection() {
        root.selectedFaceIds = ({})
        root.selectedCount = 0
    }

    Component.onCompleted: reload()
    onModeChanged: root.reload()
    onGroupByFaceChanged: { clearSelection(); reload() }
    onExpandGroupsChanged: { clearSelection(); reload() }
    onVisibleChanged: if (visible) reload()

    RowLayout {
        Layout.fillWidth: true
        spacing: 14

        CheckBox {
            id: groupByFaceCheck
            objectName: "groupByFaceCheck"
            visible: !root.ignoredMode
            text: qsTr("Group by face")
            checked: root.groupByFace
            onToggled: root.groupByFace = checked
        }
        CheckBox {
            id: expandGroupsCheck
            objectName: "expandGroupsCheck"
            visible: !root.ignoredMode
            text: qsTr("Expand groups")
            checked: root.expandGroups
            onToggled: root.expandGroups = checked
        }
        Item { Layout.fillWidth: true }
        Text {
            text: root.selectedCount > 0
                  ? qsTr("%1 selected").arg(root.selectedCount)
                  : ""
            color: Theme.textDark
        }
        TextField {
            id: nameField
            objectName: "unnamedNameField"
            visible: !root.ignoredMode
            Layout.preferredWidth: 180
            placeholderText: qsTr("Name")
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
        }
        // #26: „Ignore" — az eredetiben a mellőzés NEM törlés volt: a
        // személy a „Mellőzött emberek" albumba került
        // (`DeleteMessage::RemoveSingleUnknown`), külön megerősítéssel.
        // #26: a Mellőzött emberek albumban a mellőzés VISSZAVONÁSA a
        // művelet — az eredetiben is album volt, tehát vissza lehetett
        // nyúlni belőle, nem egyirányú szemetes
        Button {
            objectName: "unignoreFacesButton"
            visible: root.ignoredMode
            text: qsTr("Stop ignoring")
            enabled: root.selectedCount > 0 && !!root.faceScanController
            onClicked: root.unignoreSelected()
        }
        Button {
            id: ignoreButton
            objectName: "ignoreFacesButton"
            visible: !root.ignoredMode
            text: qsTr("Ignore")
            enabled: root.selectedCount > 0 && !!root.faceScanController
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Move the selected people to the ignored "
                               + "people album")
            onClicked: ignoreConfirm.open()
        }
        Button {
            id: addNameButton
            objectName: "addNameButton"
            visible: !root.ignoredMode
            text: qsTr("Add a name")
            enabled: root.selectedCount > 0
                     && nameField.text.trim().length > 0
                     && !!root.faceScanController
            ToolTip.visible: hovered
            ToolTip.text: qsTr(
                "Assign a name to all of the selected faces")
            onClicked: {
                var ids = []
                var key
                for (key in root.selectedFaceIds) {
                    ids.push(parseInt(key))
                }
                var ok = root.faceScanController.assignNameToFaces(
                    ids, nameField.text.trim())
                if (ok) {
                    nameField.text = ""
                    root.clearSelection()
                    root.reload()
                    if (typeof controller !== "undefined" && controller) {
                        controller.refreshCollections()
                    }
                }
            }
        }
    }

    ListView {
        id: groupsList
        objectName: "unnamedGroupsList"
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 12
        model: root.groupsModel
        ScrollBar.vertical: PicasaScrollBar {}

        delegate: ColumnLayout {
            id: groupDelegate
            required property var modelData
            width: groupsList.width
            spacing: 4

            Text {
                text: groupDelegate.modelData.label
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.textDark
            }

            GridView {
                id: faceGrid
                objectName: "unnamedFaceGrid"
                Layout.fillWidth: true
                interactive: false
                cellWidth: 96
                cellHeight: 96
                readonly property int columns:
                    Math.max(1, Math.floor(width / cellWidth))
                height: Math.ceil(
                    groupDelegate.modelData.faces.length
                    / Math.max(1, columns)) * cellHeight
                model: groupDelegate.modelData.faces

                delegate: Rectangle {
                    id: faceTile
                    required property var modelData
                    objectName: "faceTile_" + faceTile.modelData.faceId
                    width: faceGrid.cellWidth - 6
                    height: faceGrid.cellHeight - 6
                    color: "transparent"
                    border.width: 2
                    border.color: root.selectedFaceIds[faceTile.modelData.faceId]
                                  ? Theme.panelSelectionActive : "transparent"

                    Image {
                        anchors.fill: parent
                        anchors.margins: 3
                        source: faceTile.modelData.thumbUrl
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.toggleFace(faceTile.modelData.faceId)
                    }

                    // #26: név-javaslat — az eredeti KÉRDÉSKÉNT vetette
                    // fel („Anna?", `PeoplePanel::SuggestionFmt` = „%s?"),
                    // és a felhasználó pipával erősítette meg, x-szel
                    // vetette el (`PeopleAlbum::ConfirmText`). Sosem
                    // döntött helyette.
                    Rectangle {
                        objectName: "suggestionBar_" + faceTile.modelData.faceId
                        visible: (faceTile.modelData.suggestedName || "") !== ""
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.margins: 3
                        height: 20
                        color: Theme.infoBar

                        Row {
                            anchors.fill: parent
                            anchors.leftMargin: 4
                            spacing: 4
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                width: parent.width - 44
                                elide: Text.ElideRight
                                //: a javasolt név kérdésként — az eredeti
                                //: formátuma egyszerűen „%s?"
                                text: qsTr("%1?").arg(
                                    faceTile.modelData.suggestedName || "")
                                font.pixelSize: Theme.fontSize - 1
                                color: Theme.infoBarText
                            }
                            Text {
                                objectName: "suggestionYes_"
                                            + faceTile.modelData.faceId
                                anchors.verticalCenter: parent.verticalCenter
                                text: "✓"
                                color: Theme.infoBarText
                                MouseArea {
                                    anchors.fill: parent
                                    anchors.margins: -4
                                    onClicked: root.acceptSuggestion(
                                        faceTile.modelData.faceId)
                                }
                            }
                            Text {
                                objectName: "suggestionNo_"
                                            + faceTile.modelData.faceId
                                anchors.verticalCenter: parent.verticalCenter
                                text: "✕"
                                color: Theme.infoBarText
                                MouseArea {
                                    anchors.fill: parent
                                    anchors.margins: -4
                                    onClicked: root.rejectSuggestion(
                                        faceTile.modelData.faceId)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Az eredeti megerősítés — szó szerinti szövegekkel
    // (`DeleteMessage::IgnorePeopleTitle` / `RemoveSingleUnknown` /
    // `RemoveMultipleUnknown` / `RemoveSingleYesButtonUnknown`).
    Dialog {
        id: ignoreConfirm
        objectName: "ignoreFacesDialog"
        title: qsTr("Ignore People")
        modal: true
        anchors.centerIn: Overlay.overlay
        standardButtons: Dialog.Yes | Dialog.Cancel
        onOpened: standardButton(Dialog.Yes).text =
            root.selectedCount > 1 ? qsTr("Ignore People")
                                   : qsTr("Ignore Person")
        onAccepted: root.ignoreSelected()

        Text {
            objectName: "ignoreFacesMessage"
            width: 380
            wrapMode: Text.WordWrap
            text: root.selectedCount > 1
                  ? qsTr("Are you sure you want to move the %1 selected "
                         + "people to the ignored people album?")
                    .arg(root.selectedCount)
                  : qsTr("Are you sure you want to move this person to the "
                         + "ignored people album?")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    // #26: a javaslat elfogadása/elvetése — külön, hívható függvényben
    // (tesztelhetőség: a GridView delegate-jei nem érhetők el findChild-dal)
    function acceptSuggestion(faceId) {
        if (!root.faceScanController) return false
        var ok = root.faceScanController.acceptSuggestion(faceId)
        if (ok) {
            root.reload()
            if (typeof controller !== "undefined" && controller)
                controller.refreshCollections()
        }
        return ok
    }
    function rejectSuggestion(faceId) {
        if (!root.faceScanController) return
        root.faceScanController.rejectSuggestion(faceId)
        root.reload()
    }

    // a mellőzés visszavonása — külön, hívható függvényben
    function unignoreSelected() {
        if (!root.faceScanController) return 0
        var ids = []
        for (var key in root.selectedFaceIds) ids.push(parseInt(key))
        if (ids.length === 0) return 0
        var count = root.faceScanController.unignoreFaces(ids)
        root.clearSelection()
        root.reload()
        return count
    }

    // a tényleges mellőzés — külön, hívható függvényben (tesztelhetőség)
    function ignoreSelected() {
        if (!root.faceScanController) return 0
        var ids = []
        for (var key in root.selectedFaceIds) ids.push(parseInt(key))
        if (ids.length === 0) return 0
        var count = root.faceScanController.ignoreFaces(ids)
        root.clearSelection()
        root.reload()
        return count
    }
}
