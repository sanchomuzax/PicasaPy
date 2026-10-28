import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A fénytábla fejlécének címsora (#6104): mappa-ikon és cím, a személy-album
// avatarja és neve, a nagyítás-váltó, az „Eltávolítás” gomb és a szinkron-sor.
// Az állapot és a jelzések a `header` (LightboxHeader) tulajdonságai és
// jelzései, ahogy a LightboxFeedGroup-nál a `feed`.
// -- címsor: mappa-ikon + cím (50px behúzás) + jobb-felső szinkron-kapcsoló --
Item {
    id: titleRow
    required property var header

    Layout.fillWidth: true
    implicitHeight: header.personAlbumHeaderMode
        ? 86 : (header.personAlbumFolderMode
            ? 22 : Math.max(titleClip.height, syncRow.implicitHeight) + 4)

    FolderIcon {
        id: folderIcon
        visible: !header.personAlbumHeaderMode
        size: header.personAlbumFolderMode ? 30 : 20
        anchors.left: parent.left
        anchors.leftMargin: header.personAlbumFolderMode ? 12 : 8
        anchors.verticalCenter: titleClip.verticalCenter
    }

    // a cím levágó/halványító konténere: bal szél 50px, jobb szél a
    // fejléc szélétől 20px-re (a szinkron-sor előtt) - a `#423`
    // respack-kényszer (`album_title`, `album_title_clip`) tükre
    Item {
        id: titleClip
        objectName: "folderTitleClip"
        visible: !header.personAlbumHeaderMode
        x: 50
        y: 2
        width: Math.max(
            0, titleRow.width - 50 - 20 - syncRow.implicitWidth - 8
               - (nagyitasSor.visible ? nagyitasSor.width + 8 : 0))
        height: titleText.implicitHeight
        clip: true

        Text {
            id: titleText
            objectName: "folderTitleText"
            text: header.folderName
            color: Theme.folderTitle
            font.family: "Georgia"
            font.pointSize: header.personAlbumFolderMode ? 14 : 20
            font.weight: Font.DemiBold
        }

        // halványuló kifutás hosszú mappanévnél - NEM "…" (a Picasa
        // eredeti `title_fade0/1` rétegeinek tükre)
        Rectangle {
            objectName: "folderTitleFade"
            visible: titleText.implicitWidth > titleClip.width
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 24
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop {
                    position: 0.0
                    color: Qt.rgba(
                        Theme.lightboxBg.r, Theme.lightboxBg.g,
                        Theme.lightboxBg.b, 0.0)
                }
                GradientStop { position: 1.0; color: Theme.lightboxBg }
            }
        }
    }

    Image {
        objectName: "personAlbumAvatar"
        readonly property bool imageReady: status === Image.Ready
        visible: header.personAlbumHeaderMode
        source: header.personAvatarUrl
        x: 12; y: 8
        width: 59; height: 71
        sourceSize.width: 59; sourceSize.height: 71
        fillMode: Image.PreserveAspectFit
        asynchronous: Qt.platform.pluginName !== "offscreen"
    }

    Text {
        objectName: "personAlbumName"
        visible: header.personAlbumHeaderMode
        x: 80; y: 8
        text: header.personName
        color: Theme.folderTitle
        font.pixelSize: 18
        elide: Text.ElideRight
        width: Math.max(0, titleRow.width - x - 110)
    }

    //: #2187: az arc ↔ teljes kép nagyításváltó - MÉRT `zoom_container`
    //: (457,4)-(527,25): két 35 × 21-es gomb hézag nélkül, a fejléc
    //: JOBB FELSŐ sarkában. Nálunk ott a szinkron-sor ül, ezért elé
    //: kerül. Váltópár, nem kapcsoló: a már érvényes állapot gombja
    //: nem kér semmit.
    Row {
        id: nagyitasSor
        objectName: "headerZoomContainer"
        visible: header.personName !== ""
        anchors.right: header.personAlbumHeaderMode
            ? parent.right : syncRow.left
        anchors.rightMargin: header.personAlbumHeaderMode ? 13 : 8
        y: header.personAlbumHeaderMode
            ? 6 : Math.max(0, (syncRow.height - height) / 2)
        spacing: 0

        PicasaButton {
            id: arcNagyitasGomb
            objectName: "headerFaceZoomButton"
            visible: nagyitasSor.visible
            width: 35; height: 21
            checkable: true
            checked: header.faceZoom
            //: MÉRT súgó (`faceheaderpaneltext.tre:68`): „View zoomed in
            //: to the face" - magyarul „Megjelenítés az arcra közelítve"
            ToolTip.text: qsTr("View zoomed in to the face")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            //: a kötést a kattintás UTÁN vissza kell állítani (#1468)
            onClicked: {
                if (!header.faceZoom)
                    header.faceZoomToggled(true)
                checked = Qt.binding(function () { return header.faceZoom })
            }
            contentItem: Item {
                Image {
                    source: "icons/faces-badge.svg"
                    width: 14; height: 14
                    sourceSize.width: 14; sourceSize.height: 14
                    fillMode: Image.PreserveAspectFit
                    anchors.centerIn: parent
                }
            }
        }
        PicasaButton {
            id: kepNagyitasGomb
            objectName: "headerPictureZoomButton"
            visible: nagyitasSor.visible
            width: 35; height: 21
            checkable: true
            checked: !header.faceZoom
            //: MÉRT súgó: „View zoomed out to the full picture" -
            //: magyarul „Megjelenítés a teljes képre távolítva"
            ToolTip.text: qsTr("View zoomed out to the full picture")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: {
                if (header.faceZoom)
                    header.faceZoomToggled(false)
                checked = Qt.binding(function () { return !header.faceZoom })
            }
            contentItem: Item {
                Image {
                    source: "icons/zoom-fit.svg"
                    width: 14; height: 14
                    sourceSize.width: 14; sourceSize.height: 14
                    fillMode: Image.PreserveAspectFit
                    anchors.centerIn: parent
                }
            }
        }
    }

    PicasaButton {
        objectName: "headerRemovePersonButton"
        visible: header.personAlbumHeaderMode
        enabled: header.personAlbumRemoveEnabled
        text: qsTr("Remove")
        width: 88; height: 27
        x: titleRow.width - width - 15
        y: 58
        onClicked: header.removePersonAlbumRequested()
    }

    // jobb-felső: „Szinkronizálás az internettel" + kapcsoló - csak
    // elrendezés, letiltott (#423: funkció nélkül, funkció majd később)
    Row {
        id: syncRow
        objectName: "folderSyncRow"
        visible: !header.personAlbumHeaderMode
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: 4
        Text {
            objectName: "folderSyncLabel"
            anchors.verticalCenter: parent.verticalCenter
            text: qsTr("Sync to Web")
            font.pixelSize: 10
            color: Theme.textGray
        }
        Switch {
            objectName: "folderSyncSwitch"
            anchors.verticalCenter: parent.verticalCenter
            enabled: false
            checked: false
        }
    }
}
