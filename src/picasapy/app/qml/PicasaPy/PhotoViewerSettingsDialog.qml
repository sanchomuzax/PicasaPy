import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A specifikációban teljesen leírt Fotónéző-beállítás (#2816, 12.6):
// a színkezelés ugyanazt a tartós kapcsolót használja, mint a Nézet menü.
Dialog {
    id: dialog
    objectName: "photoViewerSettingsDialog"
    title: qsTr("Configure Photo Viewer...")
    modal: true
    focus: true
    width: 520
    parent: Overlay.overlay
    anchors.centerIn: parent

    property var viewerController: null

    ColumnLayout {
        width: parent ? parent.width : 380

        CheckBox {
            id: fullscreenStartupCheck
            objectName: "photoViewerFullscreenStartupCheck"
            Layout.fillWidth: true
            text: qsTr("Fullscreen startup (requires restart of Photo Viewer to take effect)")
            checked: dialog.viewerController
                     && dialog.viewerController.viewerFullscreenStartup !== undefined
                     ? dialog.viewerController.viewerFullscreenStartup : true
            onClicked: {
                if (dialog.viewerController
                        && dialog.viewerController.toggleViewerFullscreenStartup !== undefined)
                    dialog.viewerController.toggleViewerFullscreenStartup()
            }
        }

        CheckBox {
            id: colorManagementCheck
            objectName: "photoViewerColorManagementCheck"
            Layout.fillWidth: true
            text: qsTr("Use Color Management")
            checked: dialog.viewerController
                     && dialog.viewerController.colorManagement !== undefined
                     ? dialog.viewerController.colorManagement : false
            onClicked: {
                if (dialog.viewerController
                        && dialog.viewerController.toggleColorManagement !== undefined)
                    dialog.viewerController.toggleColorManagement()
            }
        }
    }
}
