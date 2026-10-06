import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350: "Name Tags" fül (options.fen) — V3/arcfelismerés hatókör.
//
// A háttérdetektálás kapcsolója él: az eredeti `BgFaceDetectThread`
// alapértéke BE volt. A többi, még nem bekötött névcímke-beállítás tiltva
// marad.
ColumnLayout {
    id: root
    spacing: 10

    CheckBox {
        objectName: "optionsFaceDetectionCheck"
        text: qsTr("Enable face detection")
        checked: typeof faceScanController !== "undefined"
                 && faceScanController
                 ? faceScanController.automaticDetectionEnabled() : true
        onToggled: {
            if (typeof faceScanController !== "undefined" && faceScanController)
                faceScanController.setAutomaticDetectionEnabled(checked)
        }
    }
    CheckBox {
        id: suggestionsCheck
        objectName: "optionsFaceSuggestionsCheck"
        text: qsTr("Enable suggestions:")
        enabled: false
    }
    RowLayout {
        enabled: false
        spacing: 8
        Text { text: qsTr("Suggestion threshold:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        PicasaSlider { objectName: "optionsFaceSuggestionThresholdSlider"; from: 50; to: 95 }
    }
    RowLayout {
        enabled: false
        spacing: 8
        Text { text: qsTr("Clustering threshold:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        PicasaSlider { objectName: "optionsFaceClusterThresholdSlider"; from: 50; to: 95 }
    }
    CheckBox {
        objectName: "optionsFacePersistToFileCheck"
        text: qsTr("Store name tags in the file")
        enabled: false
    }
    CheckBox {
        objectName: "optionsFaceUploadContactPhotosCheck"
        text: qsTr("Upload contact thumbnails to Google Contacts")
        enabled: false
        // #3661: a hivatalos magyar felirat hosszabb az ablak legkisebb
        // szélességénél — tördelődik, nem tolja ki a fület (a #3572 mintája)
        Layout.fillWidth: true
        Layout.preferredWidth: 0
        contentItem: Text {
            leftPadding: parent.indicator.width + parent.spacing
            text: parent.text
            font: parent.font
            color: parent.palette.windowText
            wrapMode: Text.WordWrap
            verticalAlignment: Text.AlignVCenter
        }
    }

    Item { Layout.fillHeight: true }
}
