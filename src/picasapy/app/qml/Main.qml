import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PicasaPy

ApplicationWindow {
    id: window
    width: 1280
    height: 800
    visible: true
    title: "PicasaPy"
    color: Theme.lightboxBg

    property int thumbSize: 144
    property int selectedIndex: -1        // horgony (utoljára kattintott)
    property var selectedIndexes: []      // a teljes kijelölés
    property bool viewerOpen: false

    // Kijelölés-logika (Picasa): sima katt = egy kép; Ctrl = hozzávesz/
    // elvesz; Shift = tartomány a horgonytól.
    function handleThumbClick(index, modifiers) {
        var i = Number(index)
        var mods = Number(modifiers)
        if (mods & Qt.ControlModifier) {
            var s = window.selectedIndexes.slice()
            var pos = s.indexOf(i)
            if (pos >= 0) s.splice(pos, 1); else s.push(i)
            window.selectedIndexes = s
            window.selectedIndex = i
        } else if ((mods & Qt.ShiftModifier) && window.selectedIndex >= 0) {
            var lo = Math.min(window.selectedIndex, i)
            var hi = Math.max(window.selectedIndex, i)
            var range = []
            for (var k = lo; k <= hi; ++k) range.push(k)
            window.selectedIndexes = range
        } else {
            window.selectedIndexes = [i]
            window.selectedIndex = i
        }
    }
    function clearSelection() {
        window.selectedIndexes = []
        window.selectedIndex = -1
    }
    function selectAll() {
        var range = []
        for (var k = 0; k < controller.photos.rowCount(); ++k) range.push(k)
        window.selectedIndexes = range
        if (range.length > 0) window.selectedIndex = 0
    }

    Shortcut { sequence: "Ctrl+A"; onActivated: window.selectAll() }
    Shortcut { sequence: "Ctrl+D"; onActivated: window.clearSelection() }

    // Picasa gyorsbillentyűk: Ctrl+R jobbra, Ctrl+Shift+R balra forgat
    Shortcut {
        sequence: "Ctrl+R"
        onActivated: if (trayStar.targetRow >= 0)
                         controller.rotateRight(trayStar.targetRow)
    }
    Shortcut {
        sequence: "Ctrl+Shift+R"
        onActivated: if (trayStar.targetRow >= 0)
                         controller.rotateLeft(trayStar.targetRow)
    }

    menuBar: PicasaMenuBar {
        onRescanRequested: controller.rescan()
        onAboutRequested: aboutDialog.open()
        onThumbSizePreset: function(size) { window.thumbSize = size }
        onSelectStarredRequested: controller.showStarred()
        onSelectAllRequested: window.selectAll()
        onClearSelectionRequested: window.clearSelection()
    }

    // Eszköztár: Importálás | (szűrők középen) | kereső jobbra
    header: Rectangle {
        height: 34
        color: Theme.chromeBg
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width; height: 1
            color: Theme.chromeBorder
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 8; anchors.rightMargin: 8
            spacing: 10
            PicasaButton {
                text: qsTr("Import")
                enabled: false
                Layout.preferredWidth: 100
                Layout.preferredHeight: 24
            }
            Item { Layout.fillWidth: true }
            Column {
                Layout.alignment: Qt.AlignVCenter
                spacing: 0
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: qsTr("Filters")
                    font.pixelSize: 9
                    color: Theme.textGray
                }
                Row {
                    spacing: 3

                    // szűrő-kapcsolók (kézikönyv 09): ★ ☺ ⚲ ▤ + csúszka;
                    // a bekapcsolt szűrő tónusa jelölő kék
                    Rectangle {
                        width: 22; height: 20; radius: 2
                        color: controller.filterActive ? "#ffffff" : "transparent"
                        border.width: controller.filterActive ? 1 : 0
                        border.color: Theme.selectionBlue
                        Text {
                            anchors.centerIn: parent
                            text: "★"
                            font.pixelSize: 13
                            color: controller.filterActive
                                   ? Theme.selectionBlue
                                   : (starFilter.hovered ? Theme.starYellow : "#8f8b83")
                        }
                        HoverHandler { id: starFilter }
                        TapHandler {
                            onTapped: controller.filterActive
                                      ? controller.clearFilter()
                                      : controller.showStarred()
                        }
                    }
                    Text {   // arc-szűrő (3. fázis)
                        width: 22; height: 20
                        text: "☺"; font.pixelSize: 13; color: "#8f8b83"
                        opacity: 0.45
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    Text {   // geo-szűrő
                        width: 22; height: 20
                        text: "⚲"; font.pixelSize: 13; color: "#8f8b83"
                        opacity: 0.45
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    Text {   // mozgókép / méret
                        width: 22; height: 20
                        text: "▤"; font.pixelSize: 12; color: "#8f8b83"
                        opacity: 0.45
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    Item { width: 6; height: 1 }
                    Slider {
                        width: 90; height: 20
                        enabled: false
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
            Item { width: 20 }
            TextField {
                id: searchField
                placeholderText: "🔍 " + qsTr("Search")
                Layout.preferredWidth: 300
                Layout.preferredHeight: 24
                font.pixelSize: Theme.fontSize
                onTextEdited: {
                    window.clearSelection()
                    controller.search(text)
                }
            }
        }
    }

    PhotoViewer {
        id: photoViewer
        objectName: "photoViewer"
        anchors.fill: parent
        visible: window.viewerOpen
        photosModel: controller.photos
        onClosed: {
            window.viewerOpen = false
            window.selectedIndex = currentIndex   // a rács kövesse a nézőt
            window.selectedIndexes = [currentIndex]
        }
        onCurrentIndexChanged: if (visible) window.selectedIndex = currentIndex
    }

    SplitView {
        anchors.fill: parent
        visible: !window.viewerOpen
        orientation: Qt.Horizontal

        FolderPane {
            objectName: "folderPane"
            SplitView.preferredWidth: 230
            SplitView.minimumWidth: 160
            foldersModel: controller.folders
            selectedPath: controller.currentFolder
            starredActive: controller.filterActive
            onFolderChosen: function(path) {
                searchField.clear()
                window.clearSelection()
                controller.selectFolder(path)
            }
            onStarredChosen: {
                searchField.clear()
                window.clearSelection()
                controller.showStarred()
            }
        }

        Rectangle {
            color: Theme.lightboxBg
            SplitView.fillWidth: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // zöld eredménysáv aktív szűrőnél (Picasa-minta)
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 26
                    visible: controller.filterActive
                    color: "#5aa865"
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        spacing: 10
                        Rectangle {
                            Layout.preferredHeight: 18
                            Layout.preferredWidth: viewAllText.width + 20
                            radius: 9
                            color: "#ffffff"
                            Text {
                                id: viewAllText
                                anchors.centerIn: parent
                                text: qsTr("View All")
                                font.pixelSize: Theme.fontSize - 1
                                font.bold: true
                                color: "#3b8f00"
                            }
                            TapHandler { onTapped: controller.clearFilter() }
                        }
                        Text {
                            text: controller.filterStatusText
                            color: "white"
                            font.pixelSize: Theme.fontSize
                            font.bold: true
                        }
                        Item { Layout.fillWidth: true }
                    }
                }

                // indexkép-csoport: fehér kártya a vásznon (kézikönyv 08)
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.margins: 12
                    color: Theme.contentPanel
                    border.color: Theme.chromeBorder

                    ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 4

                    LightboxHeader {
                    Layout.fillWidth: true
                    folderName: controller.currentFolder
                                ? controller.currentFolder.split("/").pop()
                                : qsTr("Library")
                    dateText: controller.folderDateText
                }

                GridView {
                    id: grid
                    objectName: "photoGrid"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: controller.photos
                    cellWidth: window.thumbSize + 18
                    cellHeight: window.thumbSize + 18
                        + (controller.thumbCaptionMode !== "none" ? 16 : 0)

                    // -- görgetési pozíció megőrzése frissítéskor --------
                    // A modell-reset (csillag/forgatás/felirat után) nullázná
                    // a contentY-t; a felhasználó maradjon, ahol volt.
                    property real savedY: 0
                    property bool restoring: false
                    property string folderKey: ""
                    onContentYChanged: {
                        if (!restoring && (contentY > 0 || moving))
                            savedY = contentY
                    }
                    onMovementEnded: savedY = contentY
                    Connections {
                        target: controller.photos
                        function onRevisionChanged() {
                            if (grid.folderKey === controller.currentFolder) {
                                grid.restoring = true
                                grid.contentY = Math.min(
                                    grid.savedY,
                                    Math.max(0, grid.contentHeight - grid.height))
                                grid.restoring = false
                            } else {
                                grid.folderKey = controller.currentFolder
                                grid.savedY = 0
                            }
                        }
                    }

                    // -- lasszós (gumikeretes) kijelölés ------------------
                    // Az indexeket rácsgeometriából számoljuk (a delegate-ek
                    // egyenletes cellákban ülnek).
                    function lassoIndexes(x1, y1, x2, y2) {
                        var cols = Math.max(1, Math.floor(width / cellWidth))
                        var left = Math.min(x1, x2), right = Math.max(x1, x2)
                        var top = Math.min(y1, y2), bottom = Math.max(y1, y2)
                        var c0 = Math.max(0, Math.floor(left / cellWidth))
                        var c1 = Math.min(cols - 1, Math.floor(right / cellWidth))
                        var r0 = Math.max(0, Math.floor(top / cellHeight))
                        var r1 = Math.floor(bottom / cellHeight)
                        var result = []
                        var total = controller.photos.rowCount()
                        for (var r = r0; r <= r1; ++r)
                            for (var c = c0; c <= c1; ++c) {
                                var idx = r * cols + c
                                if (idx >= 0 && idx < total) result.push(idx)
                            }
                        return result
                    }
                    function applyLasso(x1, y1, x2, y2, modifiers) {
                        var picked = lassoIndexes(x1, y1, x2, y2)
                        if (Number(modifiers) & Qt.ControlModifier) {
                            var merged = window.selectedIndexes.slice()
                            for (var i = 0; i < picked.length; ++i)
                                if (merged.indexOf(picked[i]) < 0)
                                    merged.push(picked[i])
                            window.selectedIndexes = merged
                        } else {
                            window.selectedIndexes = picked
                        }
                        if (picked.length > 0)
                            window.selectedIndex = picked[picked.length - 1]
                    }

                    delegate: ThumbDelegate {
                        width: grid.cellWidth
                        height: grid.cellHeight
                        captionMode: controller.thumbCaptionMode
                        selected: window.selectedIndexes.indexOf(index) !== -1
                        onChosen: function(i, mods) {
                            window.handleThumbClick(i, mods)
                        }
                        onOpened: function(i) {
                            window.viewerOpen = true
                            photoViewer.show(i)
                        }
                        onLassoDragged: function(sx, sy, cx, cy) {
                            lassoBand.update(
                                mapToItem(grid, sx, sy), mapToItem(grid, cx, cy))
                        }
                        onLassoFinished: function(sx, sy, cx, cy, mods) {
                            var a = mapToItem(grid, sx, sy)
                            var b = mapToItem(grid, cx, cy)
                            grid.applyLasso(
                                a.x, a.y + grid.contentY,
                                b.x, b.y + grid.contentY, mods)
                            lassoBand.visible = false
                        }
                    }
                    ScrollBar.vertical: ScrollBar {}

                    // gumikeret-vizualizáció
                    Rectangle {
                        id: lassoBand
                        visible: false
                        z: 10
                        color: "#33009eff"
                        border.color: Theme.thumbSelection
                        border.width: 1
                        function update(a, b) {
                            x = Math.min(a.x, b.x); y = Math.min(a.y, b.y)
                            width = Math.abs(a.x - b.x)
                            height = Math.abs(a.y - b.y)
                            visible = true
                        }
                    }
                }
                }
                }
            }
        }
    }

    footer: Column {
        width: parent.width

        // tömör acélkék infó-sáv; kijelöléskor a kép adatai
        Rectangle {
            width: parent.width; height: 20
            color: Theme.infoBar
            Text {
                anchors.centerIn: parent
                text: window.viewerOpen
                      ? controller.viewerInfo(photoViewer.currentIndex)
                      : (window.selectedIndexes.length === 1
                         ? controller.photoInfo(window.selectedIndex)
                         : controller.statusText)
                color: Theme.infoBarText
                font.pixelSize: Theme.fontSize
                font.bold: true
            }
        }

        Rectangle {
            width: parent.width; height: 52
            color: Theme.trayBg
            Rectangle {
                width: parent.width; height: 1
                color: Theme.trayBorder
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10; anchors.rightMargin: 10
                spacing: 8

                // kijelölés-tálca: a kijelölt képek miniatűrjei (Picasa)
                Item {
                    Layout.preferredWidth: 200
                    Layout.preferredHeight: 46
                    Flow {
                        anchors.fill: parent
                        spacing: 2
                        clip: true
                        Repeater {
                            model: window.selectedIndexes
                            delegate: Image {
                                required property var modelData
                                width: 20; height: 20
                                source: controller.photos.thumbUrlAt(
                                    Number(modelData))
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true
                            }
                        }
                    }
                    Text {
                        visible: window.selectedIndexes.length === 0
                        anchors.centerIn: parent
                        text: qsTr("Selection")
                        color: "#b8b8b8"
                        font.pixelSize: Theme.fontSize
                    }
                }

                PicasaButton {
                    id: trayStar
                    readonly property int targetRow: window.viewerOpen
                        ? photoViewer.currentIndex : window.selectedIndex
                    readonly property bool multi:
                        !window.viewerOpen && window.selectedIndexes.length > 1
                    enabled: window.viewerOpen || window.selectedIndex >= 0
                    Layout.preferredWidth: 34
                    onClicked: multi
                               ? controller.toggleStarMany(window.selectedIndexes)
                               : controller.toggleStar(targetRow)
                    contentItem: Text {
                        objectName: "trayStarLabel"
                        text: "★"
                        font.pixelSize: 15
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        // arany, ha a kiválasztott kép csillagos; egyébként
                        // világos kontúr-csillag (Picasa-minta, nem fekete!)
                        color: (controller.photos.revision,
                                controller.photos.starAt(trayStar.targetRow))
                               ? Theme.starYellow : "#ffffff"
                        style: Text.Outline
                        styleColor: "#9a9a9a"
                    }
                }
                PicasaButton {
                    text: "↺"
                    enabled: window.viewerOpen || window.selectedIndex >= 0
                    Layout.preferredWidth: 34
                    onClicked: trayStar.multi
                               ? controller.rotateLeftMany(window.selectedIndexes)
                               : controller.rotateLeft(trayStar.targetRow)
                }
                PicasaButton {
                    text: "↻"
                    enabled: window.viewerOpen || window.selectedIndex >= 0
                    Layout.preferredWidth: 34
                    onClicked: trayStar.multi
                               ? controller.rotateRightMany(window.selectedIndexes)
                               : controller.rotateRight(trayStar.targetRow)
                }
                Item { Layout.fillWidth: true }
                // nagyítás-csúszka − / + jelekkel (kézikönyv 06)
                Text { text: "−"; color: Theme.textGray; font.pixelSize: 13 }
                Slider {
                    id: sizeSlider
                    from: 72; to: 256; value: window.thumbSize
                    Layout.preferredWidth: 140
                    onMoved: window.thumbSize = value
                }
                Text { text: "+"; color: Theme.textGray; font.pixelSize: 13 }
                Item { width: 10 }
                PicasaButton { text: qsTr("E-Mail"); enabled: false }
                PicasaButton { text: qsTr("Print"); enabled: false }
                PicasaButton { text: qsTr("Export"); enabled: false }
                Item { width: 6 }
                // az egyetlen zöld elsődleges tett — jobbra igazítva,
                // a képernyő vizuális súlypontja (kézikönyv 01/08)
                PicasaButton {
                    text: qsTr("Upload to Google Photos")
                    enabled: false
                    accent: Theme.picasaGreen
                }
            }
        }
    }

    Dialog {
        id: aboutDialog
        title: qsTr("About PicasaPy")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        Column {
            spacing: 10
            Image {
                anchors.horizontalCenter: parent.horizontalCenter
                source: Qt.resolvedUrl("../assets/logo.svg")
                sourceSize.width: 320
                fillMode: Image.PreserveAspectFit
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "PicasaPy 0.1.0 — "
                      + qsTr("A modern, open Picasa successor.")
                      + "\nGPL-3.0 · github.com/sanchomuzax/PicasaPy"
                font.pixelSize: Theme.fontSize
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
}
