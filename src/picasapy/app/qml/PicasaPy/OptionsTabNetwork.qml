import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350: "Network" fül (options.fen). A PicasaPy nem használ proxyt, ezért a
// proxy-csoport (a két mező és az automatikus felismerés) tiltott marad.
// #5145: a naplózási szint működik (a `LogLevel` kulcsba mentődik, alapérték 2).
// A naplófájl helye rögzített, az adatmappában van (`network.log`), a mező csak
// olvasható.
ColumnLayout {
    id: root
    spacing: 10

    readonly property var prefs: (typeof controller !== "undefined" && controller)
        ? controller : null

    ColumnLayout {
        enabled: false
        Layout.fillWidth: true
        spacing: 10

        Text {
            text: qsTr("Proxy username (Windows only):")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        TextField {
            objectName: "optionsNetworkProxyUserField"
            Layout.fillWidth: true
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
        }

        Text {
            text: qsTr("Proxy password:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        TextField {
            objectName: "optionsNetworkProxyPasswordField"
            Layout.fillWidth: true
            echoMode: TextInput.Password
        }

        CheckBox {
            objectName: "optionsNetworkAutoDetectCheck"
            text: qsTr("Automatically detect network settings")
            checked: true
        }
    }

    RowLayout {
        spacing: 8
        Text { text: qsTr("Network logging level:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        PicasaComboBox {
            id: logLevelCombo
            objectName: "optionsNetworkLogLevelCombo"
            // Az eredeti `<popup name="loglevel">` szélesség nélkül áll, tehát a
            // leghosszabb tételhez igazodik; a felirat nem vágódhat le.
            Layout.preferredWidth: Math.ceil(Math.max.apply(null,
                model.map(function(t) { return logLevelMetrics.advanceWidth(t) })))
                + leftPadding + rightPadding + (indicator ? indicator.width : 0) + 8
            FontMetrics { id: logLevelMetrics; font: logLevelCombo.font }
            model: [qsTr("Disable logging"), qsTr("Log errors only"),
                    qsTr("Minimal log information"), qsTr("Detailed log information"),
                    qsTr("Log all network information")]
            currentIndex: root.prefs && root.prefs.networkLogLevel !== undefined
                ? root.prefs.networkLogLevel : 2
            onActivated: if (root.prefs
                    && typeof root.prefs.setNetworkLogLevel === "function")
                root.prefs.setNetworkLogLevel(currentIndex)
        }
    }

    RowLayout {
        spacing: 8
        Text { text: qsTr("Log file:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        TextField {
            objectName: "optionsNetworkLogPathField"
            Layout.fillWidth: true
            readOnly: true
            text: root.prefs && root.prefs.networkLogFile !== undefined
                ? root.prefs.networkLogFile : ""
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
        }
    }

    Item { Layout.fillHeight: true }
}
