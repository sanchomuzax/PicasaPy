import QtQuick

// #6446: a menüsor jobb szélének Google-fiók-sora. Belépve az eredetihez
// hasonlóan három elem: a fiók e-mail-címe (kattintás nélkül), a Google
// Fotók és a Kijelentkezés hivatkozás. Kilépve csak a bejelentkezési
// hivatkozás látszik. A feliratokat a PicasaMenuBar adja (a fordítás ott
// van kötve a környezethez), ez a fájl az elrendezést és a kattintásokat
// kezeli. A Row a láthatatlan elemeket kihagyja, így a szélessége mindig a
// látszó tartalomé.
Row {
    id: root

    // A menüsor (PicasaMenuBar): innen jön a vezérlő és a feliratok.
    required property var bar
    // Ha a belépés nem indítható (nincs kliens), a gazda dialógusa nyílik.
    signal signInUnavailable()

    readonly property bool signedIn: !!bar.ctl && bar.ctl.googlePhotosSignedIn === true
    readonly property bool authBusy: !!bar.ctl && bar.ctl.googlePhotosAuthBusy === true

    // Kilépve: a bejelentkezési hivatkozás.
    Text {
        id: signInLink
        objectName: "menuBarSignInLink"
        visible: !root.signedIn
        text: root.authBusy ? root.bar.authBusyText : root.bar.signInLinkText
        color: Theme.linkBlue
        font.pixelSize: Theme.fontSize
        font.underline: true

        MouseArea {
            objectName: "menuBarSignInArea"
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            enabled: !root.authBusy
            onClicked: {
                if (root.bar.ctl && root.bar.ctl.googlePhotosCanSignIn !== undefined
                        && root.bar.ctl.googlePhotosCanSignIn) {
                    root.bar.ctl.signInGooglePhotos()
                } else {
                    root.signInUnavailable()
                }
            }

            PressFeedbackOverlay { pressSource: parent }
        }
    }

    // Belépve: a fiók e-mail-címe, kattintás nélkül. Ha a belépés régi
    // (nincs eltárolt cím), az általános felirat marad.
    Text {
        objectName: "menuBarAccountText"
        visible: root.signedIn
        text: root.bar.googleAccountText
        color: Theme.ink
        font.pixelSize: Theme.fontSize
    }
    Text {
        visible: root.signedIn
        text: "  |  "
        color: Theme.ink
        font.pixelSize: Theme.fontSize
    }
    Text {
        objectName: "menuBarGooglePhotosLink"
        visible: root.signedIn
        text: root.bar.googlePhotosLinkText
        color: Theme.linkBlue
        font.pixelSize: Theme.fontSize
        font.underline: true

        MouseArea {
            objectName: "menuBarGooglePhotosArea"
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: Qt.openUrlExternally("https://photos.google.com")

            PressFeedbackOverlay { pressSource: parent }
        }
    }
    Text {
        visible: root.signedIn
        text: "  |  "
        color: Theme.ink
        font.pixelSize: Theme.fontSize
    }
    Text {
        objectName: "menuBarSignOutLink"
        visible: root.signedIn
        text: root.bar.signOutLinkText
        color: Theme.linkBlue
        font.pixelSize: Theme.fontSize
        font.underline: true

        MouseArea {
            objectName: "menuBarSignOutArea"
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: if (root.bar.ctl) root.bar.ctl.signOutGooglePhotos()

            PressFeedbackOverlay { pressSource: parent }
        }
    }
}
