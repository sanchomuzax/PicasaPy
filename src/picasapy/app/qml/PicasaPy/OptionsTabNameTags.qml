import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350: "Name Tags" fül (options.fen) — V3/arcfelismerés hatókör.
//
// A névcímke-beállítások a FaceScanController meglévő motorjához kötődnek.
ColumnLayout {
    id: root
    spacing: 10
    readonly property var faceCtl:
        typeof faceScanController !== "undefined" ? faceScanController : null

    CheckBox {
        objectName: "optionsFaceDetectionCheck"
        text: qsTr("Enable face detection")
        enabled: !!root.faceCtl
        checked: root.faceCtl ? root.faceCtl.automaticDetectionEnabled() : true
        onToggled: {
            if (root.faceCtl)
                root.faceCtl.setAutomaticDetectionEnabled(checked)
        }
    }
    CheckBox {
        id: suggestionsCheck
        objectName: "optionsFaceSuggestionsCheck"
        text: qsTr("Enable suggestions:")
        enabled: !!root.faceCtl
        checked: root.faceCtl ? root.faceCtl.suggestionsEnabled() : true
        onToggled: if (root.faceCtl)
            root.faceCtl.setSuggestionsEnabled(checked)
    }
    RowLayout {
        enabled: !!root.faceCtl && suggestionsCheck.checked
        spacing: 8
        Text { text: qsTr("Suggestion threshold:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        PicasaSlider {
            objectName: "optionsFaceSuggestionThresholdSlider"
            from: 50
            to: 95
            stepSize: 5
            snapMode: Slider.SnapAlways
            value: root.faceCtl ? root.faceCtl.suggestionThreshold() : 85
            onMoved: if (root.faceCtl)
                root.faceCtl.setSuggestionThreshold(value)
        }
    }
    RowLayout {
        enabled: !!root.faceCtl && suggestionsCheck.checked
        spacing: 8
        Text { text: qsTr("Clustering threshold:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        PicasaSlider {
            objectName: "optionsFaceClusterThresholdSlider"
            from: 50
            to: 95
            stepSize: 5
            snapMode: Slider.SnapAlways
            value: root.faceCtl ? root.faceCtl.clusterThreshold() : 70
            onMoved: if (root.faceCtl)
                root.faceCtl.setClusterThreshold(value)
        }
    }
    CheckBox {
        objectName: "optionsFacePersistToFileCheck"
        text: qsTr("Store name tags in the file")
        enabled: !!root.faceCtl
        checked: root.faceCtl ? root.faceCtl.persistFaceToFile() : true
        onToggled: if (root.faceCtl)
            root.faceCtl.setPersistFaceToFile(checked)
    }
    CheckBox {
        objectName: "optionsFaceUploadContactPhotosCheck"
        text: qsTr("Upload contact thumbnails to Google Contacts")
        // A PicasaPy-ban nincs Google Contacts feltöltő; a szöveg és a
        // `FREnableUploads` eredeti beállításkulcs önmagában nem hajt végre
        // feltöltést, ezért ez a vezérlő nem ígér működő funkciót.
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
