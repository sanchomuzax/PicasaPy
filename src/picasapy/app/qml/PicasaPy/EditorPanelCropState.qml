import QtQml
import QtQuick.Window

// A vágóeszköz képarányai, javaslatai és a kiválasztott arány számítása.
QtObject {
    required property var editorPanel
    required property var hostController
    required property var hostEditController

    property bool resetEnabled: false
    property var suggestions: []
    property int aspectIndex: 0
    property bool aspectRotated: false

    readonly property string suggestionThumbSource: {
        if (!editorPanel.hasEffectController())
            return ""
        var forras = hostEditController.previewSource
        return forras ? String(forras) : ""
    }

    function suggestionLabel(key) {
        switch (key) {
        case "faces_tight": return qsTr("Close crop to faces")
        case "faces_compose": return qsTr("Compose around faces")
        case "horizon": return qsTr("Crop by horizon")
        case "red_green": return qsTr("Crop by color")
        case "variance": return qsTr("Crop by detail")
        default: return key
        }
    }

    readonly property var aspectPresets: [
        { key: "Manual", label: qsTr("Manual"), note: "", ratio: 0 },
        { key: "CurrentRatio", label: qsTr("Current ratio"), note: "", ratio: -1 },
        { key: "5x8m", label: "5x8", note: "", ratio: 8 / 5 },
        { key: "9x13m", label: "9x13", note: qsTr("Small print"), ratio: 13 / 9 },
        { key: "10x15m", label: "10x15", note: qsTr("Large print"), ratio: 15 / 10 },
        { key: "Crop13x18m", label: "13x18", note: "", ratio: 18 / 13 },
        { key: "::Crop20x25m", label: "20x25", note: "", ratio: 25 / 20 },
        { key: "::A4", label: "A4", note: qsTr("Full page"), ratio: 297 / 210 },
        { key: "Square", label: qsTr("Square"), note: qsTr("CD Cover"), ratio: 1 },
        { key: "Desktop4x3", label: "4:3", note: qsTr("Standard screen"), ratio: 4 / 3 },
        { key: "Widescreen", label: "16:10", note: qsTr("Widescreen monitor"), ratio: 16 / 10 },
        { key: "HDTV16x9", label: "16:9", note: "HDTV", ratio: 16 / 9 },
        { key: "WideFrame", label: "5:3", note: qsTr("Widescreen Photo Frame"), ratio: 5 / 3 }
    ]

    readonly property var customAspectRatios:
        hostController ? hostController.customAspectRatios : []

    readonly property var aspectFullList: {
        var list = aspectPresets.slice()
        if (editorPanel.imagePixelWidth > 0 && editorPanel.imagePixelHeight > 0) {
            var manual = list[0]
            var manualLabel = manual.label
            if (editorPanel.cropHasSelection) {
                manualLabel = qsTr("Manual") + ": "
                    + formatCropPixelSize(
                        Math.round(editorPanel.cropRect.width * editorPanel.imagePixelWidth),
                        Math.round(editorPanel.cropRect.height * editorPanel.imagePixelHeight))
            }
            list[0] = {
                key: manual.key,
                label: manualLabel,
                note: manual.note,
                ratio: manual.ratio
            }

            var current = list[1]
            list[1] = {
                key: current.key,
                label: qsTr("Current ratio") + ": "
                    + formatCropPixelSize(
                        editorPanel.imagePixelWidth, editorPanel.imagePixelHeight),
                note: current.note,
                ratio: current.ratio
            }
        }
        for (var i = 0; i < customAspectRatios.length; i++) {
            var c = customAspectRatios[i]
            list.push({
                key: "custom:" + c.name + ":" + c.width + "x" + c.height,
                label: c.width + " x " + c.height + "   " + c.name,
                ratio: c.width / c.height,
                isCustom: true,
                customName: c.name,
                customWidth: c.width,
                customHeight: c.height
            })
        }
        return list
    }

    function formatCropPixelSize(width, height) {
        return qsTr("%1$d x %2$d")
            .replace("%1$d", width).replace("%2$d", height)
    }

    readonly property var selectedPreset:
        aspectFullList[Math.max(0, Math.min(aspectIndex, aspectFullList.length - 1))]

    readonly property real currentAspect: {
        var base = selectedPreset.ratio
        if (base === 0) return 0
        if (base === -1) base = editorPanel.imageAspect
        if (base === -2)
            base = (Screen.height > 0) ? Screen.width / Screen.height
                                       : editorPanel.imageAspect
        if (base < 1) base = 1 / base
        return aspectRotated ? 1 / base : base
    }
}
