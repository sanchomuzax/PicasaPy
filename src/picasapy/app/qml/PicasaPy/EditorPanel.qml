import QtQuick
import QtQuick.Layouts

// Szerkesztő eszközpanel — a néző bal oldali "Gyakori javítások" füle,
// Picasa-hű ikonos csempékkel (#51). Két mód:
//  - "tools": ikonrács + Derítőfény + Visszavonás/Újra
//  - "crop":  "Fotó vágása" — arány-lista, gyorsvágások, gombok
// Csak UI + állapot: a kép-feldolgozás a render/edit rétegben él.
Rectangle {
    id: panel
    objectName: "editorPanel"
    color: Theme.chromeBg
    implicitWidth: 230

    // kapcsoló-állapotok — az aktív eszköz csempéje "benyomva" jelenik meg
    property bool cropActive: false
    property bool tiltActive: false
    property bool redeyeActive: false
    property bool enhanceActive: false
    property bool autolightActive: false
    property bool autocolorActive: false

    // Visszavonás/Újra (jelenleg a vágásra): a hívó (PhotoViewer) tölti
    property bool undoAvailable: false
    property bool redoAvailable: false
    property string undoLabel: qsTr("Undo")
    property string redoLabel: qsTr("Redo")

    // a kép aktuális szélesség/magasság aránya ("Jelenlegi méretarány"-hoz)
    property real imageAspect: 4 / 3

    // vágás-mód állapota
    property int aspectIndex: 0        // az aspectPresets lista indexe
    property bool aspectRotated: false // Forgatás: fekvő <-> álló

    // tool: "crop"|"tilt"|"redeye"|"enhance"|"autolight"|"autocolor"
    signal toolActivated(string tool)
    // a vágás külön jelet is kap — a hívó ez alapján nyitja a CropOverlay-t
    signal cropRequested()
    signal undoRequested()
    signal redoRequested()
    // vágás-mód jelei a hívónak
    signal quickCropRequested(string kind)   // "topleft"|"landscape"|"portrait"
    signal cropRotateRequested()
    signal cropPreviewHold(bool held)
    signal cropResetRequested()
    signal cropApplyRequested()
    signal cropCancelRequested()

    // Arány-lista (Picasa-minta). ratio = szélesség/magasság fekvő
    // tájolásban; 0 = kézi (szabad), -1 = a kép jelenlegi aránya.
    readonly property var aspectPresets: [
        { label: qsTr("Manual"), ratio: 0 },
        { label: qsTr("Current aspect"), ratio: -1 },
        { label: "5x8", ratio: 8 / 5 },
        { label: "9x13", ratio: 13 / 9 },
        { label: "10x15", ratio: 15 / 10 },
        { label: "13x18", ratio: 18 / 13 },
        { label: "20x25", ratio: 25 / 20 },
        { label: qsTr("A4: Full page"), ratio: 297 / 210 },
        { label: qsTr("Square: CD cover"), ratio: 1 },
        { label: qsTr("4:3: Standard screen"), ratio: 4 / 3 },
        { label: qsTr("16:10: Widescreen"), ratio: 16 / 10 },
        { label: qsTr("16:9: HDTV"), ratio: 16 / 9 },
        { label: qsTr("5:3: Wide frame"), ratio: 5 / 3 }
    ]

    // a kiválasztott arány a Forgatással együtt — a CropOverlay-nek
    readonly property real currentAspect: {
        var base = aspectPresets[aspectIndex].ratio
        if (base === 0) return 0
        if (base === -1) base = panel.imageAspect
        if (base < 1) base = 1 / base   // fekvő alapállás
        return panel.aspectRotated ? 1 / base : base
    }

    // egy csempe-kattintás kezelése: kapcsoló-állapot váltása + jelzés
    function handleToolClick(tool) {
        switch (tool) {
        case "crop": panel.cropActive = !panel.cropActive; break
        case "tilt": panel.tiltActive = !panel.tiltActive; break
        case "redeye": panel.redeyeActive = !panel.redeyeActive; break
        case "enhance": panel.enhanceActive = !panel.enhanceActive; break
        case "autolight": panel.autolightActive = !panel.autolightActive; break
        case "autocolor": panel.autocolorActive = !panel.autocolorActive; break
        }
        panel.toolActivated(tool)
        if (tool === "crop") panel.cropRequested()
    }

    // ikonos eszköz-csempe: kis kép-ikon + felirat alatta (Picasa-minta)
    component ToolTile: Item {
        id: tile
        required property string toolName
        required property string label
        required property string icon
        property bool active: false
        property bool tileEnabled: true
        signal activated(string tool)

        Layout.fillWidth: true
        Layout.preferredHeight: 66
        opacity: tile.tileEnabled ? 1 : 0.4

        Rectangle {
            anchors.fill: parent
            radius: 3
            color: tile.active ? "#cfe4f7"
                 : (tileMouse.containsMouse && tile.tileEnabled ? "#e8eef4"
                                                                : "transparent")
            border.width: tile.active ? 1 : 0
            border.color: Theme.selectionBlue
        }
        Image {
            anchors.top: parent.top
            anchors.topMargin: 4
            anchors.horizontalCenter: parent.horizontalCenter
            width: 40; height: 30
            source: "../../assets/tools/" + tile.icon + ".png"
            smooth: true
        }
        Text {
            anchors.top: parent.top
            anchors.topMargin: 37   // az ikon alatt, nem érhet össze vele
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width - 2
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            lineHeight: 0.9
            text: tile.label
            font.pixelSize: Theme.fontSize - 2
            color: Theme.textDark
        }
        MouseArea {
            id: tileMouse
            anchors.fill: parent
            hoverEnabled: true
            enabled: tile.tileEnabled
            onClicked: tile.activated(tile.toolName)
        }
    }

    // egyszerű panel-gomb (PicasaButton-színvilág)
    component PanelButton: Rectangle {
        id: pbtn
        property string label: ""
        property bool buttonEnabled: true
        signal buttonClicked()
        Layout.fillWidth: true
        Layout.preferredHeight: 24
        radius: 3
        border.width: 1
        border.color: Theme.chromeBorder
        color: !pbtn.buttonEnabled ? "#ececec"
               : (pbtnMouse.pressed ? "#d8d8d8" : "#fdfdfd")
        Text {
            anchors.centerIn: parent
            text: pbtn.label
            font.pixelSize: Theme.fontSize
            color: pbtn.buttonEnabled ? Theme.textDark : "#9a968e"
            elide: Text.ElideRight
            width: parent.width - 8
            horizontalAlignment: Text.AlignHCenter
        }
        MouseArea {
            id: pbtnMouse
            anchors.fill: parent
            enabled: pbtn.buttonEnabled
            onClicked: pbtn.buttonClicked()
        }
    }

    // ---------------- "tools" mód: ikonrács ----------------
    ColumnLayout {
        objectName: "toolsColumn"
        visible: !panel.cropActive
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        Rectangle {
            Layout.fillWidth: true
            height: 22
            color: Theme.panelHeaderBg
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Common Fixes")
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.panelHeaderText
            }
        }

        GridLayout {
            columns: 3
            columnSpacing: 4
            rowSpacing: 10
            Layout.fillWidth: true

            ToolTile {
                objectName: "editToolCrop"
                toolName: "crop"; label: qsTr("Crop"); icon: "crop"
                active: panel.cropActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolTilt"
                toolName: "tilt"; label: qsTr("Straighten"); icon: "tilt"
                active: panel.tiltActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolRedeye"
                toolName: "redeye"; label: qsTr("Redeye"); icon: "redeye"
                active: panel.redeyeActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolEnhance"
                toolName: "enhance"; label: qsTr("I'm Feeling Lucky"); icon: "lucky"
                active: panel.enhanceActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolAutolight"
                toolName: "autolight"; label: qsTr("Auto Contrast"); icon: "contrast"
                active: panel.autolightActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolAutocolor"
                toolName: "autocolor"; label: qsTr("Auto Color"); icon: "color"
                active: panel.autocolorActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolTile {
                objectName: "editToolRetouch"
                toolName: "retouch"; label: qsTr("Retouch"); icon: "retouch"
                tileEnabled: false   // 2. ütem
            }
            ToolTile {
                objectName: "editToolText"
                toolName: "text"; label: qsTr("Text"); icon: "text"
                tileEnabled: false   // 2. ütem
            }
        }

        // Derítőfény — a render-op a 2. ütemben élesedik (inaktív csúszka)
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Image {
                Layout.preferredWidth: 40
                Layout.preferredHeight: 30
                source: "../../assets/tools/filllight.png"
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                Text {
                    text: qsTr("Fill Light")
                    font.pixelSize: Theme.fontSize - 1
                    color: Theme.textGray
                }
                Rectangle {
                    Layout.fillWidth: true
                    height: 4; radius: 2
                    color: "#d0cdc4"
                    Rectangle {
                        x: 0; y: -4
                        width: 12; height: 12; radius: 6
                        color: "#efefef"
                        border.color: Theme.chromeBorder
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            PanelButton {
                objectName: "editUndoButton"
                label: panel.undoLabel
                buttonEnabled: panel.undoAvailable
                onButtonClicked: panel.undoRequested()
            }
            PanelButton {
                objectName: "editRedoButton"
                label: panel.redoLabel
                buttonEnabled: panel.redoAvailable
                Layout.fillWidth: false
                Layout.preferredWidth: 64
                onButtonClicked: panel.redoRequested()
            }
        }
    }

    // ---------------- "crop" mód: Fotó vágása ----------------
    ColumnLayout {
        objectName: "cropColumn"
        visible: panel.cropActive
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
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

        // arány-választó legördülő (Picasa-lista)
        Rectangle {
            objectName: "cropAspectCombo"
            Layout.fillWidth: true
            Layout.preferredHeight: 22
            radius: 2
            color: "#ffffff"
            border.color: Theme.chromeBorder
            Text {
                anchors.left: parent.left; anchors.leftMargin: 6
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width - 28
                elide: Text.ElideRight
                text: panel.aspectPresets[panel.aspectIndex].label
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
            color: "#ffffff"
            border.color: Theme.chromeBorder
            Column {
                id: aspectColumn
                x: 1; y: 1
                width: parent.width - 2
                Repeater {
                    model: panel.aspectPresets
                    Rectangle {
                        required property var modelData
                        required property int index
                        width: aspectColumn.width; height: 20
                        color: aspectRowHover.hovered ? Theme.panelSelection
                               : "transparent"
                        Text {
                            anchors.left: parent.left; anchors.leftMargin: 6
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.label
                            font.pixelSize: Theme.fontSize
                            color: aspectRowHover.hovered ? "#ffffff" : Theme.ink
                        }
                        HoverHandler { id: aspectRowHover }
                        TapHandler {
                            onTapped: {
                                panel.aspectIndex = index
                                panel.aspectRotated = false
                                aspectList.visible = false
                            }
                        }
                    }
                }
            }
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
}
