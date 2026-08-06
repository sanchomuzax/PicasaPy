import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350: "Network" fül (options.fen) — a PicasaPy nem használ proxyt/saját
// hálózati naplózást (nincs felhő-funkció, a lemezes I/O helyi vagy
// NAS-mountos), ezért a teljes fül tiltott.
ColumnLayout {
    id: root
    spacing: 10
    enabled: false

    Text {
        text: qsTr("Proxy username (Windows only):")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }
    TextField { objectName: "optionsNetworkProxyUserField"; Layout.fillWidth: true }

    Text {
        text: qsTr("Proxy password:")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }
    TextField { objectName: "optionsNetworkProxyPasswordField"; Layout.fillWidth: true; echoMode: TextInput.Password }

    CheckBox {
        objectName: "optionsNetworkAutoDetectCheck"
        text: qsTr("Automatically detect network settings")
        checked: true
    }

    RowLayout {
        spacing: 8
        Text { text: qsTr("Network logging level:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        ComboBox {
            objectName: "optionsNetworkLogLevelCombo"
            model: [qsTr("Disable logging"), qsTr("Log errors only"),
                    qsTr("Minimal log information"), qsTr("Detailed log information"),
                    qsTr("Log all network information")]
        }
    }

    RowLayout {
        spacing: 8
        Text { text: qsTr("Log file:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        TextField { objectName: "optionsNetworkLogPathField"; Layout.fillWidth: true; readOnly: true }
        Button { objectName: "optionsNetworkLogBrowseButton"; text: qsTr("Browse...") }
    }

    Item { Layout.fillHeight: true }
}
