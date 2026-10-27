import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    objectName: "optionsGooglePhotosTab"
    spacing: 10

    readonly property var prefs: (typeof controller !== "undefined" && controller)
        ? controller : null

    function authStatusText() {
        if (!prefs)
            return ""
        if (prefs.googlePhotosAuthBusy)
            return qsTr("Waiting for Google authorization…")
        if (prefs.googlePhotosAuthError === "missing_credentials")
            return qsTr("Enter a valid OAuth client ID and client secret.")
        if (prefs.googlePhotosAuthError === "browser_unavailable")
            return qsTr("Could not open the system browser.")
        if (prefs.googlePhotosAuthError === "cancelled")
            return qsTr("Sign-in was cancelled.")
        if (prefs.googlePhotosAuthError === "auth_timeout")
            return qsTr("Sign-in timed out. Try again.")
        if (prefs.googlePhotosAuthError === "network")
            return qsTr("Network error. Check your connection and try again.")
        if (prefs.googlePhotosAuthError === "token_expired")
            return qsTr("Your Google Photos sign-in has expired. Sign in again.")
        if (prefs.googlePhotosAuthError)
            return qsTr("Google sign-in failed. Check the OAuth client settings.")
        if (prefs.googlePhotosSignedIn)
            return qsTr("Signed in to Google Photos")
        return qsTr("Not signed in to Google Photos")
    }

    Text {
        text: qsTr("Use your own Google OAuth client (Desktop app).")
        color: Theme.ink
        font.pixelSize: Theme.fontSize
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }

    Text {
        text: qsTr("OAuth client ID")
        color: Theme.ink
        font.pixelSize: Theme.fontSize
    }

    TextField {
        id: clientIdField
        objectName: "googlePhotosClientIdField"
        Layout.fillWidth: true
        text: root.prefs && root.prefs.googlePhotosClientId !== undefined
            ? root.prefs.googlePhotosClientId : ""
        selectByMouse: true
        TextFieldContextArea {}
    }

    Text {
        text: qsTr("OAuth client secret")
        color: Theme.ink
        font.pixelSize: Theme.fontSize
    }

    TextField {
        id: clientSecretField
        objectName: "googlePhotosClientSecretField"
        Layout.fillWidth: true
        echoMode: TextInput.Password
        selectByMouse: true
        placeholderText: root.prefs && root.prefs.googlePhotosClientSecretConfigured
            ? qsTr("Leave blank to keep the saved client secret") : ""
        TextFieldContextArea {}
    }

    Text {
        text: qsTr("The client secret and refresh token are stored in the system keyring or user settings.")
        color: Theme.ink
        font.pixelSize: Theme.fontSize
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 8

        PicasaButton {
            objectName: "googlePhotosSaveCredentialsButton"
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:CThumbUI::FileSave::saveButton
            text: qsTr("Save")
        enabled: root.prefs
            && root.prefs.googlePhotosClientSecretConfigured !== undefined
            && clientIdField.text.trim().length > 0
            && (clientSecretField.text.length > 0
                || root.prefs.googlePhotosClientSecretConfigured)
            onClicked: root.prefs.configureGooglePhotos(
                clientIdField.text, clientSecretField.text)
        }

        PicasaButton {
            objectName: "googlePhotosSignInButton"
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:NCWebAlbums::Label3
            text: qsTr("Sign in with Google Account")
            enabled: root.prefs
                && root.prefs.googlePhotosCanSignIn !== undefined
                && root.prefs.googlePhotosSignedIn !== undefined
                && root.prefs.googlePhotosAuthBusy !== undefined
                && root.prefs.googlePhotosCanSignIn
                && !root.prefs.googlePhotosSignedIn && !root.prefs.googlePhotosAuthBusy
            onClicked: {
                if (root.prefs.configureGooglePhotos(clientIdField.text, clientSecretField.text))
                    root.prefs.signInGooglePhotos()
            }
        }

        PicasaButton {
            objectName: "googlePhotosSignOutButton"
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:NCWebAlbums::Label2
            text: qsTr("Sign Out")
            visible: root.prefs && root.prefs.googlePhotosSignedIn !== undefined
                ? root.prefs.googlePhotosSignedIn : false
            enabled: visible && root.prefs.googlePhotosAuthBusy !== undefined
                && !root.prefs.googlePhotosAuthBusy
            onClicked: root.prefs.signOutGooglePhotos()
        }
    }

    Text {
        objectName: "googlePhotosAuthStatus"
        text: root.authStatusText()
        color: Theme.ink
        font.pixelSize: Theme.fontSize
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }

    Text {
        text: qsTr("Uploaded photos are limited to 1600 pixels on the longer side.")
        color: Theme.ink
        font.pixelSize: Theme.fontSize
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }

    Item { Layout.fillHeight: true }

    Connections {
        target: root.prefs
        function onGooglePhotosChanged() {
            if (!clientIdField.activeFocus
                    && root.prefs.googlePhotosClientId !== undefined)
                clientIdField.text = root.prefs.googlePhotosClientId
            if (!clientSecretField.activeFocus)
                clientSecretField.clear()
        }
    }
}
