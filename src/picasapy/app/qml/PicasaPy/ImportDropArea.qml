import QtQuick

// #237: fájl-drop fogadó a főablak gyökerére — Picasa-viselkedés: képet
// ejtve a kép MAPPÁJA, mappát ejtve maga a mappa lesz figyelt gyökér
// (dropImportController híd); az elutasított elemekről buborék ad rövid,
// emberi nyelvű visszajelzést. Bekötés (integrátor, Main.qml):
//   ImportDropArea { anchors.fill: parent; z: 95 }
// — a DropArea nem fog el egér-eseményeket, így a teljes ablakra téve sem
// zavarja a meglévő kezelőket.
DropArea {
    id: root

    // a híd kívülről cserélhető (tesztben fake kontextus-property); önálló
    // példányosításnál (híd nélkül) a drop csendben kimarad
    readonly property var dropController:
        (typeof dropImportController !== "undefined" && dropImportController)
            ? dropImportController : null

    // az onDropped-ból kiemelt átadás — offscreen tesztből közvetlenül
    // hívható (valódi asztali drag-eseményt ott nem lehet kelteni)
    function submitUrls(urls) {
        if (!dropController) return
        var list = []
        for (var i = 0; i < urls.length; ++i)
            list.push(String(urls[i]))
        dropController.importDroppedUrls(list)
    }

    onDropped: function(drop) {
        if (drop.hasUrls) {
            root.submitUrls(drop.urls)
            drop.acceptProposedAction()
        }
    }

    // húzás közben keret-kiemelés — látszik, hogy az ablak fogadja az elemet
    Rectangle {
        visible: root.containsDrag
        anchors.fill: parent
        color: "transparent"
        border.color: Theme.selectionBlue
        border.width: 3
    }

    // visszajelzés-buborék (nem támogatott elem / üres drop) — magától eltűnik
    Rectangle {
        id: dropFeedback
        objectName: "dropFeedback"
        property string message: ""
        visible: false
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 40
        width: Math.min(parent.width - 40, feedbackText.implicitWidth + 24)
        height: feedbackText.implicitHeight + 14
        radius: 4
        color: "#000000b3"
        Text {
            id: feedbackText
            anchors.centerIn: parent
            width: Math.min(dropFeedback.width - 20,
                            feedbackText.implicitWidth)
            text: dropFeedback.message
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            color: "#ffffff"
            font.pixelSize: Theme.fontSize
        }
        Timer {
            id: feedbackTimer
            interval: 4000
            onTriggered: dropFeedback.visible = false
        }
    }

    Connections {
        target: root.dropController
        enabled: root.dropController !== null
        function onDropRejected(message) {
            dropFeedback.message = message
            dropFeedback.visible = true
            feedbackTimer.restart()
        }
    }
}
