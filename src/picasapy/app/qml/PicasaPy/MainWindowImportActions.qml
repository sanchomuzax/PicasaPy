pragma ComponentBehavior: Bound
import QtQuick
import PicasaPy

// Az importpanel bezárásakor megjelenő döntés és a hozzá tartozó műveletek.
Item {
    id: importActions
    anchors.fill: parent

    required property var hostWindow
    required property var hostController
    required property var exitDialog
    required property var importSourceDialog
    required property string messageText
    required property string importText
    required property string quitText

    property alias confirmationDialog: importBeforeCloseDialog

    function hasPendingImport() {
        var panel = importActions.importSourceDialog
            ? importActions.importSourceDialog.item : null
        return importActions.hostWindow.importPanelOpen
            && panel && panel.visible && panel.canImportAll
    }

    function askBeforeClose() {
        importBeforeCloseDialog.ensure().ask("", importActions.messageText)
    }

    function kilepes(ablakZarasiKeres) {
        if (!importActions.hostWindow.aaKapu(
                importActions.hostWindow.kilepes)) return false
        if (!importActions.hostWindow.kilepesMegerositve
                && importActions.hasPendingImport()) {
            importActions.askBeforeClose()
            return false
        }
        if (!importActions.hostWindow.kilepesMegerositve
                && importActions.hostController
                && importActions.hostController.backgroundWorkRunning()) {
            importActions.exitDialog.askExit()
            return false
        }
        if (ablakZarasiKeres === true) return true
        Qt.quit()
        return true
    }

    DeferredDialog {
        id: importBeforeCloseDialog
        objectName: "importBeforeCloseDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "importBeforeCloseDialog"
                namePrefix: "importBeforeClose"
                cancelVisible: false
                rememberVisible: false
                yesText: importActions.importText
                noText: importActions.quitText
                onConfirmed: {
                    var panel = importActions.importSourceDialog
                        ? importActions.importSourceDialog.item : null
                    if (panel)
                        panel.importBeforeClosing()
                }
                onDenied: {
                    importActions.hostWindow.importPanelOpen = false
                    importActions.hostWindow.kilepes()
                }
            }
        }
    }
}
