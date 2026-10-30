import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A PhotoViewer változatlan vizuális fája, külön komponenshatáron.
ColumnLayout {
    id: viewerLayout
    property var hostViewer: null
    property var hostContextActions: null
    property alias topBar: viewerTopBarComponent
    property alias filmstrip: filmstrip
    property alias leftDrawer: leftDrawer
    property alias photoArea: photoArea
    property alias overlayControls: viewerOverlayControls
    property alias editorPanel: leftDrawer.hostEditorPanel
    property alias cropOverlay: photoArea.hostCropOverlay
    property alias editorToolBar: photoArea.hostEditorToolBar
    property alias effectColorPickArea: photoArea.hostEffectColorPickArea
    property alias facesOverlay: photoArea.hostFacesOverlay
    property alias gpuPrefixImage: photoArea.hostGpuPrefixImage
    property alias kepkockaJelzes: photoArea.hostKepkockaJelzes
    property alias neutralPickArea: photoArea.hostNeutralPickArea
    property alias paintMaskArea: photoArea.hostPaintMaskArea
    property alias photo: photoArea.hostPhoto
    property alias photoElotte: photoArea.hostPhotoElotte
    property alias photoElotteKeret: photoArea.hostPhotoElotteKeret
    property alias photoKeret: photoArea.hostPhotoKeret
    property alias redeyeDragArea: photoArea.hostRedeyeDragArea
    property alias retouchClickArea: photoArea.hostRetouchClickArea
    property alias textClickArea: photoArea.hostTextClickArea
    property alias videoLoader: photoArea.hostVideoLoader

    anchors.fill: parent
    // A gyorsnézet 67 px-es alsó sávját a 12.8.2 koordinátái adják:
    // a vezérlők a 800 px magas referencia-keret 733–769. sorában állnak.
    anchors.bottomMargin: viewerLayout.hostViewer.quickViewerMode ? 67 : 0
    spacing: 0

    // felső sáv: vissza gomb + filmszalag nyilakkal
    PhotoViewerTopBar {
        id: viewerTopBarComponent
        Layout.fillWidth: true
        hostViewer: viewerLayout.hostViewer
        hostLeftDrawer: leftDrawer
        hostPhotoArea: photoArea
        hostFilmstrip: filmstrip
        PhotoViewerFilmstrip {
            id: filmstrip
            hostViewer: viewerLayout.hostViewer
            width: 214
            height: 28
        }
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        spacing: 0

        // bal eszközpanel — Gyakori javítások élesben (#19); a
        // Retusálás/Szöveg és a finomhangolás a #20-ban élesedik
        PhotoViewerLeftDrawer {
            id: leftDrawer
            Layout.preferredWidth: 280 + viewerLayout.hostViewer.editorDrawerOffset
            Layout.minimumWidth: 1
            Layout.maximumWidth: 280
            Layout.fillHeight: true
            hostViewer: viewerLayout.hostViewer
            hostPhotoArea: photoArea
            hostCropOverlay: viewerLayout.hostViewer.cropOverlay
            hostCopyCaptionConfirmLoader:
                viewerLayout.hostContextActions.hostCopyCaptionConfirmLoader
            hostUndoDataLossDialogLoader:
                viewerLayout.hostContextActions.hostUndoDataLossDialogLoader
            hostMovieResetConfirmLoader:
                viewerLayout.hostContextActions.hostMovieResetConfirmLoader
            hostKepkockaJelzes: viewerLayout.hostViewer.kepkockaJelzes
            hostVideoLoader: viewerLayout.hostViewer.videoLoader
        }

        // fő képterület
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Theme.viewerBg

            WheelHandler {
                acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                // #6: Ctrl+görgő = zoom a kép fölött; sima görgő marad a
                // képek közti lapozás (#77) — a két igény így fér össze
                onWheel: function(event) {
                    if (event.modifiers & Qt.ControlModifier)
                        viewerLayout.hostViewer.wheelZoom(event.angleDelta.y)
                    else
                        viewerLayout.hostViewer.wheelStep(event.angleDelta.y)
                }
            }

            PhotoViewerPhotoArea {
                id: photoArea
                hostViewer: viewerLayout.hostViewer
                hostViewerPanArea: viewerOverlayControls.hostViewerPanArea
                hostEditorPanel: viewerLayout.hostViewer.editorPanel
            }

            PhotoViewerOverlayControls {
                id: viewerOverlayControls
                anchors.fill: parent
                hostViewer: viewerLayout.hostViewer
                hostPhotoArea: photoArea
            }
        }
        PhotoViewerRightPanels {
            hostViewer: viewerLayout.hostViewer
        }
    }
}
