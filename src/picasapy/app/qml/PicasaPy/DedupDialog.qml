import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Duplikátum-kezelő (#287): a `picasapy.dedup` mag (find_duplicates) fölötti
// UI — a Mappakezelő (FolderManagerDialog.qml) mintájára ÖNÁLLÓ, mozgatható/
// átméretezhető ablak (nem a főablakba ékelt Dialog). Csoportonként (pontos
// + hasonló duplikátumok) mutatja az érintett képeket előnézeti thumbnaillel
// (image://thumbs/<id>, ld. thumbnail_provider.py); a felhasználó
// kiválasztja a megtartandó képet (kattintás a kártyájára), a csoport
// többi tagja pedig egy gombbal áthelyezhető a forrásmappa
// "Duplikátumok" alkönyvtárába (NEM-DESZTRUKTÍV alapértelmezés, #287 DoD)
// vagy törölhető a Kukába.
Window {
    id: dedupWindow
    objectName: "dedupDialog"
    title: qsTr("Find Duplicates")
    modality: Qt.ApplicationModal
    width: 640
    height: 520
    minimumWidth: 420
    minimumHeight: 320
    color: Theme.canvasBg

    // a legutóbbi keresés eredménye — dict-ek listája: {kind, maxDistance,
    // items: [{path, thumbUrl}, ...]}; a DedupController.scanFinished
    // MINDIG listát ad (soha tuple-t), ez a property is azt tükrözi
    property var groups: []
    // csoportonként a megtartandó útvonal (groupIndex -> path); ha egy
    // csoportra nincs explicit bejegyzés, az első elem számít
    // megtartandónak (a "legrégebbi/első" a legkevésbé meglepő alapértelmezés)
    property var keepByGroup: ({})
    property bool scanning: false
    property string lastError: ""

    function open() {
        dedupWindow.visible = true
        if (dedupWindow.groups.length === 0 && !dedupWindow.scanning)
            dedupWindow.scan()
    }

    function scan() {
        dedupWindow.scanning = true
        dedupWindow.lastError = ""
        dedupController.scanForDuplicates()
    }

    // a csoport megtartandó útvonala — alapértelmezés az első (0.) elem
    function keepPathFor(groupIndex) {
        var explicit = dedupWindow.keepByGroup[groupIndex]
        if (explicit !== undefined) return explicit
        var group = dedupWindow.groups[groupIndex]
        return (group && group.items.length > 0) ? group.items[0].path : ""
    }

    function setKeep(groupIndex, path) {
        var next = {}
        for (var key in dedupWindow.keepByGroup) next[key] = dedupWindow.keepByGroup[key]
        next[groupIndex] = path
        dedupWindow.keepByGroup = next
    }

    function groupPaths(groupIndex) {
        var group = dedupWindow.groups[groupIndex]
        if (!group) return []
        var paths = []
        for (var i = 0; i < group.items.length; ++i) paths.push(group.items[i].path)
        return paths
    }

    // NEM-DESZTRUKTÍV alapértelmezés (#287 DoD): a csoport többi tagja a
    // forrásmappa "Duplikátumok" alkönyvtárába kerül
    function moveGroup(groupIndex) {
        dedupController.moveOthersToDuplicatesFolder(
            dedupWindow.groupPaths(groupIndex), dedupWindow.keepPathFor(groupIndex))
    }

    // Destruktívabb út — csak explicit felhasználói döntésre (gombnyomás)
    function deleteGroup(groupIndex) {
        dedupController.deleteOthers(
            dedupWindow.groupPaths(groupIndex), dedupWindow.keepPathFor(groupIndex))
    }

    // egy feloldott elem eltávolítása a helyi listából — a csoport
    // egészét is eldobjuk, ha kettő alá csökken a tagok száma (akkor már
    // nem "duplikátum-csoport")
    function removeResolvedItem(path) {
        var next = []
        for (var g = 0; g < dedupWindow.groups.length; ++g) {
            var group = dedupWindow.groups[g]
            var items = []
            for (var i = 0; i < group.items.length; ++i)
                if (group.items[i].path !== path) items.push(group.items[i])
            if (items.length >= 2)
                next.push({ kind: group.kind, maxDistance: group.maxDistance, items: items })
        }
        dedupWindow.groups = next
        dedupWindow.keepByGroup = ({})
    }

    Connections {
        target: typeof dedupController !== "undefined" ? dedupController : null
        function onScanFinished(newGroups) {
            dedupWindow.groups = newGroups
            dedupWindow.keepByGroup = ({})
            dedupWindow.scanning = false
        }
        function onScanFailed(message) {
            dedupWindow.lastError = message
            dedupWindow.scanning = false
        }
        function onItemResolved(path) {
            dedupWindow.removeResolvedItem(path)
        }
        function onOperationFailed(path, message) {
            dedupWindow.lastError = message
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: qsTr(
                    "Groups of duplicate and similar pictures found in your "
                    + "watched folders. Pick which one to keep in each group; "
                    + "the rest can be moved to a \"Duplikátumok\" folder or "
                    + "deleted.")
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            PicasaButton {
                objectName: "dedupScanButton"
                text: dedupWindow.scanning ? qsTr("Scanning...")
                                           : qsTr("Scan for Duplicates")
                enabled: !dedupWindow.scanning
                onClicked: dedupWindow.scan()
            }
        }

        Text {
            objectName: "dedupErrorText"
            visible: dedupWindow.lastError.length > 0
            text: dedupWindow.lastError
            color: Theme.brandRed
            font.pixelSize: Theme.fontSize
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Text {
            objectName: "dedupEmptyText"
            visible: !dedupWindow.scanning && dedupWindow.groups.length === 0
            text: qsTr("No duplicates found.")
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        Flickable {
            id: groupsFlick
            objectName: "dedupGroupsFlick"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: width
            contentHeight: groupsColumn.height
            ScrollBar.vertical: PicasaScrollBar {}

            Column {
                id: groupsColumn
                width: groupsFlick.width
                spacing: 10

                Repeater {
                    model: dedupWindow.groups
                    delegate: Rectangle {
                        id: groupCard
                        required property var modelData
                        required property int index
                        objectName: "dedupGroup:" + groupCard.index
                        width: groupsColumn.width
                        height: groupContent.height + 16
                        color: "#ffffff"
                        border.color: Theme.chromeBorder
                        radius: 3

                        ColumnLayout {
                            id: groupContent
                            x: 8
                            y: 8
                            width: parent.width - 16
                            spacing: 6

                            Text {
                                objectName: "dedupGroupLabel:" + groupCard.index
                                text: groupCard.modelData.kind === "exact"
                                      ? qsTr("Exact duplicates (%1 pictures)")
                                            .arg(groupCard.modelData.items.length)
                                      : qsTr("Similar pictures (%1, distance %2)")
                                            .arg(groupCard.modelData.items.length)
                                            .arg(groupCard.modelData.maxDistance)
                                font.pixelSize: Theme.fontSize
                                color: Theme.ink
                            }

                            Row {
                                spacing: 6
                                Repeater {
                                    model: groupCard.modelData.items
                                    delegate: Column {
                                        id: itemCell
                                        required property var modelData
                                        required property int index
                                        readonly property bool isKeep:
                                            dedupWindow.keepPathFor(groupCard.index)
                                            === itemCell.modelData.path
                                        spacing: 2

                                        Rectangle {
                                            objectName:
                                                "dedupThumbFrame:" + groupCard.index
                                                + ":" + itemCell.index
                                            width: 72
                                            height: 72
                                            border.width: itemCell.isKeep ? 3 : 1
                                            border.color: itemCell.isKeep
                                                          ? Theme.thumbSelection
                                                          : Theme.thumbBorder
                                            color: Theme.thumbCard

                                            Image {
                                                anchors.fill: parent
                                                anchors.margins: 3
                                                source: itemCell.modelData.thumbUrl
                                                fillMode: Image.PreserveAspectFit
                                                asynchronous:
                                                    Qt.platform.pluginName !== "offscreen"
                                            }

                                            MouseArea {
                                                objectName:
                                                    "dedupKeepArea:" + groupCard.index
                                                    + ":" + itemCell.index
                                                anchors.fill: parent
                                                onClicked: dedupWindow.setKeep(
                                                    groupCard.index,
                                                    itemCell.modelData.path)
                                            }
                                        }

                                        Text {
                                            width: 72
                                            elide: Text.ElideMiddle
                                            horizontalAlignment: Text.AlignHCenter
                                            text: itemCell.modelData.path.split("/").pop()
                                            font.pixelSize: 10
                                            color: Theme.textGray
                                        }
                                    }
                                }
                            }

                            RowLayout {
                                spacing: 8
                                PicasaButton {
                                    objectName: "dedupMoveButton:" + groupCard.index
                                    text: qsTr("Move others to \"Duplikátumok\"")
                                    onClicked: dedupWindow.moveGroup(groupCard.index)
                                }
                                PicasaButton {
                                    objectName: "dedupDeleteButton:" + groupCard.index
                                    text: qsTr("Delete others to Trash")
                                    onClicked: dedupWindow.deleteGroup(groupCard.index)
                                }
                            }
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            PicasaButton {
                objectName: "dedupCloseButton"
                text: qsTr("Close")
                onClicked: dedupWindow.visible = false
            }
        }
    }
}
