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
//
// #294 — HATÓKÖR, HALADÁS, MEGSZAKÍTÁS. A keresés korábban feltétel nélkül a
// teljes indexelt könyvtárra futott, jelzés és megszakítási lehetőség
// nélkül; 140 000 képnél az ablak némán állt. Most:
//   * hatókör-választó (kijelölés / aktuális mappa+almappák / teljes
//     könyvtár) — az alapértelmezés a szűk hatókör, a teljes könyvtár
//     tudatos választás, a várható hosszról szóló figyelmeztetéssel;
//   * folyamatjelző (a DedupController.scanProgress jelzéseiből) és
//     Mégse gomb, amely bármikor tisztán leállítja a keresést.
// A jelzések a worker-szálról jönnek — a Qt queued kézbesítéssel sorolja
// őket a GUI-szálra, ahogy a scanFinished-et is.
//
// #298 — az ablak bezárásakor a dedup-bélyegképek regisztrációja elengedésre
// kerül (releaseThumbnails), a fő rács regisztrációjának érintetlenül
// hagyásával.
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

    // OPCIONÁLIS: a főablak — a kijelölés (selectedIndexes) forrása. Amíg a
    // Main.qml nem köti be, a "kijelölt képek" hatókör egyszerűen nem
    // választható, minden más változatlanul működik.
    property var appWindow: null

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

    // hatókör: 0 = kijelölt képek, 1 = aktuális mappa + almappák,
    // 2 = teljes könyvtár. Alapértelmezés a szűk (mappa) hatókör.
    readonly property int scopeSelection: 0
    readonly property int scopeFolder: 1
    readonly property int scopeLibrary: 2
    property int scopeIndex: dedupWindow.scopeFolder

    // haladás-állapot a folyamatjelzőhöz (a scanProgress jelzésekből)
    property string progressPhase: ""
    property int progressDone: 0
    property int progressTotal: 0

    readonly property int selectionCount:
        (dedupWindow.appWindow && dedupWindow.appWindow.selectedIndexes)
        ? dedupWindow.appWindow.selectedIndexes.length : 0
    readonly property bool hasSelection: dedupWindow.selectionCount >= 2
    readonly property string currentFolder:
        (typeof controller !== "undefined" && controller)
        ? controller.currentFolder : ""

    function open() {
        // a legkevésbé meglepő alapértelmezés: ha van érdemi kijelölés, arra
        // keresünk, egyébként az aktuális mappára (+almappákra)
        dedupWindow.scopeIndex = dedupWindow.hasSelection
                                 ? dedupWindow.scopeSelection
                                 : dedupWindow.scopeFolder
        dedupWindow.visible = true
        if (dedupWindow.groups.length === 0 && !dedupWindow.scanning)
            dedupWindow.scan()
    }

    // a kijelölt sorok fájl-URL-jei (a controller `to_local_path`-on
    // átfuttatja őket, ezért a file:// alak is jó)
    function selectedPaths() {
        var rows = dedupWindow.appWindow ? dedupWindow.appWindow.selectedIndexes : []
        var paths = []
        for (var i = 0; i < rows.length; ++i)
            paths.push(controller.photos.fileUrlAt(rows[i]))
        return paths
    }

    function scan() {
        if (dedupWindow.scopeIndex === dedupWindow.scopeSelection
                && !dedupWindow.hasSelection) {
            dedupWindow.lastError = qsTr(
                "Select at least two pictures in the grid, or pick another scope.")
            return
        }
        dedupWindow.scanning = true
        dedupWindow.lastError = ""
        dedupWindow.progressPhase = ""
        dedupWindow.progressDone = 0
        dedupWindow.progressTotal = 0
        if (dedupWindow.scopeIndex === dedupWindow.scopeSelection)
            dedupController.scanSelection(dedupWindow.selectedPaths())
        else if (dedupWindow.scopeIndex === dedupWindow.scopeLibrary)
            dedupController.scanForDuplicates()
        else
            dedupController.scanFolder(dedupWindow.currentFolder)
    }

    function cancelScan() {
        dedupController.cancelScan()
    }

    // #298: bezáráskor a dedup-bélyegképek elengedése (a fő rács
    // regisztrációja érintetlen marad), és a találatok eldobása — a
    // következő megnyitás friss keresést indít, így soha nem maradnak
    // "halott" image://thumbs/<id> URL-ek a listában.
    function releaseAndReset() {
        dedupController.cancelScan()
        dedupController.releaseThumbnails()
        dedupWindow.scanning = false
        dedupWindow.groups = []
        dedupWindow.keepByGroup = ({})
    }

    onVisibleChanged: {
        if (!dedupWindow.visible)
            dedupWindow.releaseAndReset()
    }

    // a haladás emberi szövege — a controller csak technikai fázis-tokent ad
    function phaseLabel(phase) {
        if (phase === "exact") return qsTr("Comparing files...")
        if (phase === "phash") return qsTr("Analysing pictures...")
        return qsTr("Searching...")
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
        function onScanProgress(phase, done, total) {
            dedupWindow.progressPhase = phase
            dedupWindow.progressDone = done
            dedupWindow.progressTotal = total
        }
        function onScanCancelled() {
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

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr(
                "Groups of duplicate and similar pictures. Pick which one to "
                + "keep in each group; the rest can be moved to a "
                + "\"Duplikátumok\" folder or deleted.")
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        // hatókör-választó (#294): a szűk hatókör az alapértelmezés, a
        // teljes könyvtár tudatos választás
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text {
                text: qsTr("Search in:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            ComboBox {
                id: scopeBox
                objectName: "dedupScopeBox"
                Layout.preferredWidth: 260
                enabled: !dedupWindow.scanning
                currentIndex: dedupWindow.scopeIndex
                onCurrentIndexChanged: dedupWindow.scopeIndex = currentIndex
                model: [
                    dedupWindow.hasSelection
                        ? qsTr("Selected pictures (%1)").arg(
                              dedupWindow.selectionCount)
                        : qsTr("Selected pictures (none)"),
                    qsTr("This folder and its subfolders"),
                    qsTr("Whole library")
                ]
            }
            Item { Layout.fillWidth: true }
            PicasaButton {
                objectName: "dedupScanButton"
                text: dedupWindow.scanning ? qsTr("Scanning...")
                                           : qsTr("Scan for Duplicates")
                enabled: !dedupWindow.scanning
                onClicked: dedupWindow.scan()
            }
        }

        // figyelmeztetés a teljes könyvtár várható hosszáról (#294)
        Text {
            objectName: "dedupScopeWarning"
            visible: dedupWindow.scopeIndex === dedupWindow.scopeLibrary
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr(
                "Searching the whole library reads every picture — with tens "
                + "of thousands of photos this can take a long time. You can "
                + "cancel at any point, and the next search starts from the "
                + "already analysed pictures.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.folderDate
        }

        // folyamatjelző + Mégse (#294) — csak futó keresés közben látszik
        ColumnLayout {
            objectName: "dedupProgressPanel"
            visible: dedupWindow.scanning
            Layout.fillWidth: true
            spacing: 4

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                Text {
                    objectName: "dedupProgressLabel"
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                    text: dedupWindow.progressTotal > 0
                          ? qsTr("%1 %2 / %3")
                                .arg(dedupWindow.phaseLabel(
                                    dedupWindow.progressPhase))
                                .arg(dedupWindow.progressDone)
                                .arg(dedupWindow.progressTotal)
                          : dedupWindow.phaseLabel(dedupWindow.progressPhase)
                    font.pixelSize: Theme.fontSize
                    color: Theme.textGray
                }
                PicasaButton {
                    objectName: "dedupCancelButton"
                    text: qsTr("Cancel")
                    onClicked: dedupWindow.cancelScan()
                }
            }

            // deklaratív (mindig renderelő) sáv — az ImportProgressPanel
            // mintája; Canvas/requestPaint szándékosan NEM (MEMORY-tanulság)
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 8
                radius: 4
                color: Theme.trackBg
                border.color: Theme.chromeBorder

                Rectangle {
                    objectName: "dedupProgressBarFill"
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    radius: parent.radius
                    color: Theme.picasaGreen
                    width: dedupWindow.progressTotal > 0
                           ? parent.width * dedupWindow.progressDone
                             / dedupWindow.progressTotal
                           : 0
                }
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
                        color: Theme.contentPanel
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
