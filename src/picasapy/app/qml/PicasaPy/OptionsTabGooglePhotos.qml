import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    objectName: "optionsGooglePhotosTab"
    spacing: 10
    property var openGooglePhotosHelp: null

    readonly property var prefs: (typeof controller !== "undefined" && controller)
        ? controller : null
    // #6402: az adatvédelmi tájékoztató és a feltételek címe (external_links.py)
    readonly property var links: typeof appLinks !== "undefined" ? appLinks : ({})

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
        text: qsTr("PicasaPy signs in with its built-in client. Use your own client only if needed.")
        color: Theme.ink
        font.pixelSize: Theme.fontSize
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        // ha egyik gomb sem látszik, a sor ne foglaljon helyet
        visible: signInButton.visible || signOutButton.visible

        PicasaButton {
            id: signInButton
            objectName: "googlePhotosSignInButton"
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:NCWebAlbums::Label3
            text: qsTr("Sign in with Google Account")
            visible: root.prefs && root.prefs.googlePhotosCanSignIn !== undefined
                ? root.prefs.googlePhotosCanSignIn : false
            enabled: visible && root.prefs.googlePhotosAuthBusy !== undefined
                && !root.prefs.googlePhotosAuthBusy
            onClicked: root.prefs.signInGooglePhotos()
        }

        PicasaButton {
            id: signOutButton
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

    // #6402: a bejelentkezésnél az adatvédelmi tájékoztató és a feltételek
    RowLayout {
        objectName: "googlePhotosLegalLinks"
        Layout.fillWidth: true
        spacing: 18

        ExternalLinkText {
            objectName: "googlePhotosPrivacyLink"
            text: qsTr("Privacy Policy")
            url: root.links.privacy || ""
        }

        ExternalLinkText {
            objectName: "googlePhotosTermsLink"
            text: qsTr("Terms of Service")
            url: root.links.terms || ""
        }
    }

    Text {
        text: qsTr("Uploaded photos are limited to 1600 pixels on the longer side.")
        color: Theme.ink
        font.pixelSize: Theme.fontSize
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
    }

    // a lenyitható rész a mappafa mintáját követi: háromszög + felirat
    Text {
        id: advancedToggle
        objectName: "googlePhotosAdvancedToggle"
        property bool checked: false
        Layout.fillWidth: true
        text: (checked ? "\u25BE " : "\u25B8 ")
            + qsTr("Advanced: use your own Google client (optional)")
        color: Theme.ink
        font.pixelSize: Theme.fontSize
        wrapMode: Text.WordWrap

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: advancedToggle.checked = !advancedToggle.checked
        }
    }

    ColumnLayout {
        id: advancedContents
        objectName: "googlePhotosAdvancedContents"
        visible: advancedToggle.checked
        enabled: visible
        Layout.fillWidth: true
        spacing: 8

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
            text: qsTr("Client secret")
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

        Text {
            objectName: "googlePhotosHelpLink"
            text: qsTr("Read the Google Photos sign-in guide")
            color: Theme.linkBlue
            font.pixelSize: Theme.fontSize
            font.underline: true

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: if (root.openGooglePhotosHelp)
                    root.openGooglePhotosHelp()
            }
        }

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
