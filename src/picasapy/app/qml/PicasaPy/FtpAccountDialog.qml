import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: ftpAccountDialog
    objectName: "ftpAccountDialog"
    property var ownerWindow
    title: qsTr("Manage FTP Accounts")
    modal: true
    x: Math.max(0, (ownerWindow.width - width) / 2)
    y: Math.max(0, (ownerWindow.height - height) / 2)
    width: 390
    standardButtons: Dialog.NoButton
    property string editingId: ""
    property string accountError: ""

    function openFor(accountId) {
        ftpAccountDialog.editingId = accountId || ""
        ftpAccountDialog.accountError = ""
        if (ftpAccountDialog.editingId.length > 0
                && typeof webExportController !== "undefined"
                && webExportController) {
            var account = webExportController.ftpAccount(
                ftpAccountDialog.editingId)
            accountNameField.text = account.name || ""
            accountHostField.text = account.domain || ""
            accountUserField.text = account.user || ""
            accountRootField.text = account.root || "/"
        } else {
            ftpAccountDialog.beginNew()
        }
        accountPasswordField.text = ""
        ftpAccountDialog.open()
    }

    function beginNew() {
        ftpAccountDialog.editingId = ""
        accountNameField.text = ""
        accountHostField.text = ""
        accountUserField.text = ""
        accountRootField.text = "/"
        accountPasswordField.text = ""
        ftpAccountDialog.accountError = ""
    }

    function saveAccount() {
        var result = webExportController.saveFtpAccount(
            ftpAccountDialog.editingId,
            accountNameField.text,
            accountHostField.text,
            accountUserField.text,
            accountRootField.text,
            accountPasswordField.text)
        if (!result.ok) {
            ftpAccountDialog.accountError = result.error
            return
        }
        webExportController.selectFtpAccount(result.id)
        ownerWindow.refreshFtpAccounts(result.id)
        ftpAccountDialog.close()
    }

    function deleteAccount() {
        if (ftpAccountDialog.editingId.length === 0) return
        if (!webExportController.deleteFtpAccount(
                ftpAccountDialog.editingId)) {
            ftpAccountDialog.accountError = qsTr("The account could not be deleted.")
            return
        }
        ftpAccountDialog.beginNew()
        ownerWindow.refreshFtpAccounts("")
    }

    contentItem: ColumnLayout {
        spacing: 8
        Label { text: qsTr("Account name:") }
        TextField {
            id: accountNameField
            objectName: "ftpAccountNameField"
            Layout.fillWidth: true
            TextFieldContextArea {}
        }
        Label { text: qsTr("FTP server:") }
        TextField {
            id: accountHostField
            objectName: "ftpAccountHostField"
            Layout.fillWidth: true
            TextFieldContextArea {}
        }
        Label { text: qsTr("Username:") }
        TextField {
            id: accountUserField
            objectName: "ftpAccountUserField"
            Layout.fillWidth: true
            TextFieldContextArea {}
        }
        Label { text: qsTr("Password:") }
        TextField {
            id: accountPasswordField
            objectName: "ftpAccountPasswordField"
            Layout.fillWidth: true
            echoMode: TextInput.Password
            TextFieldContextArea {}
        }
        Label { text: qsTr("Remote folder:") }
        TextField {
            id: accountRootField
            objectName: "ftpAccountRootField"
            Layout.fillWidth: true
            TextFieldContextArea {}
        }
        Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Theme.textGray
            text: ftpAccountDialog.editingId.length > 0
                  ? qsTr("Leave blank to keep the saved password.") : ""
        }
        Text {
            objectName: "ftpAccountErrorText"
            visible: ftpAccountDialog.accountError.length > 0
            text: ftpAccountDialog.accountError
            color: Theme.brandRed
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        RowLayout {
            Layout.fillWidth: true
            PicasaButton {
                objectName: "ftpAccountNewButton"
                text: qsTr("New")
                onClicked: ftpAccountDialog.beginNew()
            }
            PicasaButton {
                objectName: "ftpAccountDeleteButton"
                text: qsTr("Delete")
                enabled: ftpAccountDialog.editingId.length > 0
                onClicked: ftpAccountDialog.deleteAccount()
            }
            Item { Layout.fillWidth: true }
            PicasaButton {
                objectName: "ftpAccountCancelButton"
                text: qsTr("Cancel")
                onClicked: ftpAccountDialog.close()
            }
            PicasaButton {
                objectName: "ftpAccountSaveButton"
                text: qsTr("Save")
                accent: Theme.picasaGreen
                onClicked: ftpAccountDialog.saveAccount()
            }
        }
    }
}
