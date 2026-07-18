import QtQuick
import QtQuick.Layouts

// Szerkesztő eszközpanel — a néző bal oldali "Gyakori javítások" füle.
// Csak UI + kapcsoló-állapot: a tényleges kép-feldolgozás a render/edit
// rétegben él (más agent munkája), ide csak jelek jutnak ki.
// Az integrátor a Main.qml-be köti be (19-es issue).
Rectangle {
    id: panel
    objectName: "editorPanel"
    color: Theme.chromeBg
    implicitWidth: 230

    // kapcsoló-állapotok — az aktív eszköz vizuálisan benyomva jelenik meg
    property bool cropActive: false
    property bool tiltActive: false
    property bool redeyeActive: false
    property bool enhanceActive: false
    property bool autolightActive: false
    property bool autocolorActive: false

    // tool: "crop"|"tilt"|"redeye"|"enhance"|"autolight"|"autocolor"
    signal toolActivated(string tool)
    // a vágás külön jelet is kap — az integrátor ez alapján nyitja meg a
    // CropOverlay-t a néző fölött
    signal cropRequested()

    // egy gombkattintás kezelése: kapcsoló-állapot váltása + jelzés kifelé
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

    // eszközgomb — aktív állapotban kék kitöltés ("benyomott" hatás),
    // egyébként a PicasaButton.qml szín-mintáját követő világos gomb
    component ToolButton: Rectangle {
        id: btn
        required property string toolName
        required property string label
        property bool active: false
        signal activated(string tool)

        Layout.fillWidth: true
        Layout.preferredHeight: 32
        radius: 3
        border.width: 1
        border.color: btn.active ? Qt.darker(Theme.selectionBlue, 1.3)
                                  : Theme.chromeBorder
        color: btn.active ? Theme.selectionBlue
               : (mouseArea.pressed ? "#d8d8d8" : "#fdfdfd")

        Text {
            anchors.centerIn: parent
            text: btn.label
            font.pixelSize: Theme.fontSize
            color: btn.active ? "white" : Theme.textDark
        }

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            onClicked: btn.activated(btn.toolName)
        }
    }

    ColumnLayout {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 8

        // fül-sáv — 1. fázisban csak "Gyakori javítások"
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
            columns: 2
            columnSpacing: 6
            rowSpacing: 6
            Layout.fillWidth: true

            ToolButton {
                objectName: "editToolCrop"
                toolName: "crop"; label: qsTr("Crop")
                active: panel.cropActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolButton {
                objectName: "editToolTilt"
                toolName: "tilt"; label: qsTr("Straighten")
                active: panel.tiltActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolButton {
                objectName: "editToolRedeye"
                toolName: "redeye"; label: qsTr("Redeye")
                active: panel.redeyeActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolButton {
                objectName: "editToolEnhance"
                toolName: "enhance"; label: qsTr("I'm Feeling Lucky")
                active: panel.enhanceActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolButton {
                objectName: "editToolAutolight"
                toolName: "autolight"; label: qsTr("Auto Contrast")
                active: panel.autolightActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
            ToolButton {
                objectName: "editToolAutocolor"
                toolName: "autocolor"; label: qsTr("Auto Color")
                active: panel.autocolorActive
                onActivated: (tool) => panel.handleToolClick(tool)
            }
        }
    }
}
