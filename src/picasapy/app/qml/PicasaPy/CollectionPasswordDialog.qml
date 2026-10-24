import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #5704: egyéni gyűjtemény és a beépített Rejtett mappák jelszava.
Dialog {
    id: root
    objectName: "collectionPasswordDialog"
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    standardButtons: Dialog.Cancel
    implicitWidth: 420 + leftPadding + rightPadding

    property var controller: null
    property string collectionName: ""
    property bool hiddenCollection: false
    property bool jelszoLetezik: false
    property string mode: "set" // set · manage · change
    property string errorMessage: ""
    readonly property string currentPassword: currentField.text
    readonly property string enteredPassword: passwordField.text
    readonly property string verificationPassword: verifyField.text
    readonly property bool modernRequested: modernBox.checked

    title: qsTr("Password Entry")

    function openForCollection(name) {
        root.hiddenCollection = false
        root.collectionName = name
        root.jelszoLetezik = root.controller
                ? root.controller.collectionPasswordSet(name) : false
        root._open(root.jelszoLetezik ? "manage" : "set")
    }

    function openForHiddenCollection() {
        root.hiddenCollection = true
        root.collectionName = "Hidden Folders"
        root.jelszoLetezik = root.controller
                ? root.controller.hiddenPasswordSet : false
        root._open(root.jelszoLetezik ? "manage" : "set")
    }

    function _open(which) {
        root.mode = which
        root.errorMessage = ""
        currentField.text = ""
        passwordField.text = ""
        verifyField.text = ""
        modernBox.checked = false
        root.open()
        if (which === "set") passwordField.forceActiveFocus()
        else currentField.forceActiveFocus()
    }

    function _verify(password) {
        if (!root.controller) return false
        return root.hiddenCollection
                ? root.controller.verifyHiddenPassword(password)
                : root.controller.verifyCollectionPassword(
                      root.collectionName, password)
    }

    function _unlock(password) {
        if (!root.controller) return false
        if (root.hiddenCollection) {
            if (!root.controller.unlockHidden(password)) return false
            root.controller.setShowHidden(true)
            return true
        }
        return root.controller.unlockCollection(root.collectionName, password)
    }

    function _setPassword(password, verification) {
        if (!root.controller) return false
        if (root.hiddenCollection)
            return password === verification
                    && root.controller.setHiddenPassword(
                        password, root.modernRequested)
        return root.controller.setCollectionPassword(
            root.collectionName, password, verification)
    }

    function _changePassword(current, password, verification) {
        if (!root.controller) return false
        if (root.hiddenCollection)
            return password === verification
                    && root.controller.changeHiddenPassword(
                        current, password, root.modernRequested)
        return root.controller.changeCollectionPassword(
            root.collectionName, current, password, verification)
    }

    function _removePassword(current) {
        if (!root.controller) return false
        return root.hiddenCollection
                ? root.controller.clearHiddenPassword(current)
                : root.controller.clearCollectionPassword(
                      root.collectionName, current)
    }

    function _beginChange() {
        if (!currentField.text) return
        if (!root._verify(currentField.text)) {
            root.errorMessage = qsTr("Please provide a valid password")
            return
        }
        root.errorMessage = ""
        root.mode = "change"
        passwordField.text = ""
        verifyField.text = ""
        passwordField.forceActiveFocus()
    }

    function _submit() {
        root.errorMessage = ""
        var ok = false
        if (root.mode === "set") {
            ok = root._setPassword(passwordField.text, verifyField.text)
        } else if (root.mode === "manage") {
            ok = root._unlock(currentField.text)
        } else {
            ok = root._changePassword(
                currentField.text, passwordField.text, verifyField.text)
        }
        if (!ok) {
            root.errorMessage = qsTr("Please provide a valid password")
            return false
        }
        return true
    }

    function _remove() {
        root.errorMessage = ""
        if (root._removePassword(currentField.text)) {
            root.close()
            return
        }
        root.errorMessage = qsTr("Please provide a valid password")
    }

    function _canSubmit() {
        if (root.mode === "manage") return currentField.text.length > 0
        return passwordField.text.length > 0
                && passwordField.text === verifyField.text
    }

    onOpened: {
        if (root.mode === "set") passwordField.forceActiveFocus()
        else currentField.forceActiveFocus()
    }

    ColumnLayout {
        spacing: 9

        Text {
            objectName: "collectionPasswordPrompt"
            Layout.preferredWidth: 390
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            text: root.mode === "set" || root.mode === "change"
                  ? qsTr("Please enter a password to use for this collection")
                  : qsTr("Please enter a password to open this collection")
        }

        TextField {
            id: currentField
            objectName: "collectionPasswordCurrent"
            visible: root.mode === "manage" || root.mode === "change"
            Layout.fillWidth: true
            Layout.minimumWidth: 300
            echoMode: TextInput.Password
            font.pixelSize: Theme.fontSize
            onAccepted: if (root._canSubmit() && root.mode === "manage") {
                            if (root._submit()) root.close()
                        }
            TextFieldContextArea {}
        }

        TextField {
            id: passwordField
            objectName: "collectionPasswordField"
            visible: root.mode === "set" || root.mode === "change"
            Layout.fillWidth: true
            Layout.minimumWidth: 300
            echoMode: TextInput.Password
            font.pixelSize: Theme.fontSize
            onAccepted: if (root._canSubmit() && root.mode !== "manage") {
                            if (root._submit()) root.close()
                        }
            TextFieldContextArea {}
        }

        TextField {
            id: verifyField
            objectName: "collectionPasswordVerify"
            visible: root.mode === "set" || root.mode === "change"
            Layout.fillWidth: true
            Layout.minimumWidth: 300
            echoMode: TextInput.Password
            font.pixelSize: Theme.fontSize
            placeholderText: qsTr("Please verify your password")
            onAccepted: if (root._canSubmit() && root.mode !== "manage") {
                            if (root._submit()) root.close()
                        }
            TextFieldContextArea {}
        }

        Text {
            objectName: "collectionPasswordMismatch"
            visible: (root.mode === "set" || root.mode === "change")
                     && passwordField.text.length > 0
                     && verifyField.text.length > 0
                     && passwordField.text !== verifyField.text
            Layout.preferredWidth: 390
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.brandRed
            text: qsTr("The passwords did not match.")
        }

        Text {
            objectName: "collectionPasswordError"
            visible: root.errorMessage.length > 0
            Layout.preferredWidth: 390
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.brandRed
            text: root.errorMessage
        }

        CheckBox {
            id: modernBox
            objectName: "collectionPasswordModern"
            visible: root.hiddenCollection
                     && (root.mode === "set" || root.mode === "change")
            font.pixelSize: Theme.fontSize
            text: qsTr("Stronger protection (Picasa cannot open it)")
        }

        RowLayout {
            visible: root.mode === "manage"
            Layout.fillWidth: true
            spacing: 8

            PicasaButton {
                objectName: "collectionPasswordChangeButton"
                // a gombon nincs gyorsbillentyű-aláhúzás: az & jelet levesszük
                text: qsTr("&Add/Change a password...").replace("&", "")
                onClicked: root._beginChange()
            }
            PicasaButton {
                objectName: "collectionPasswordRemoveButton"
                text: qsTr("Remove the password")
                onClicked: root._remove()
            }
        }

        RowLayout {
            Layout.fillWidth: true
            PicasaButton {
                objectName: "collectionPasswordSubmit"
                text: root.mode === "manage"
                      ? qsTr("Open")
                      : qsTr("&Add/Change a password...").replace("&", "")
                enabled: root._canSubmit()
                accent: Theme.picasaGreen
                onClicked: {
                    if (root._submit()) root.close()
                }
            }
        }
    }
}
