import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350: "Name Tags" fül (options.fen) — V3/arcfelismerés hatókör.
//
// #1473 (helyesbítés): arcfelismerő motorunk MÁR VAN
// (`face_scan_controller.py` + YuNet/SFace), és `Eszközök ▸ Arcok
// keresése…` alól indítható is. A fül attól még tiltott marad: az ITT
// felsorolt BEÁLLÍTÁSOK egyike sincs bekötve — nincs háttérszál, amit
// ki-be lehetne kapcsolni (az eredeti `BgFaceDetectThread`-je), és a két
// küszöb (`FRSuggestionThreshold`/`FRSortThreshold`) sem jut el a
// csoportosításig. A fül élesítése ezek bekötését jelenti, nem a motor
// megírását.
ColumnLayout {
    id: root
    spacing: 10
    enabled: false

    CheckBox { objectName: "optionsFaceDetectionCheck"; text: qsTr("Enable face detection") }
    CheckBox {
        id: suggestionsCheck
        objectName: "optionsFaceSuggestionsCheck"
        text: qsTr("Enable suggestions:")
    }
    RowLayout {
        enabled: suggestionsCheck.checked
        spacing: 8
        Text { text: qsTr("Suggestion threshold:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        PicasaSlider { objectName: "optionsFaceSuggestionThresholdSlider"; from: 50; to: 95 }
    }
    RowLayout {
        spacing: 8
        Text { text: qsTr("Clustering threshold:"); font.pixelSize: Theme.fontSize; color: Theme.ink }
        PicasaSlider { objectName: "optionsFaceClusterThresholdSlider"; from: 50; to: 95 }
    }
    CheckBox { objectName: "optionsFacePersistToFileCheck"; text: qsTr("Store name tags in the file") }
    CheckBox { objectName: "optionsFaceUploadContactPhotosCheck"; text: qsTr("Upload contact thumbnails to Google Contacts") }

    Item { Layout.fillHeight: true }
}
