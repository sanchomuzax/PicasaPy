import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #4135: a választó és a levélszerkesztő ugyanazon küldési folyamat két
// oldala. A Gmail-fiókos út a projekt specifikációja szerint megszűnt; a
// választóban látható, de nem választható. A levelet a rendszer
// alapértelmezett levelezőjének adjuk át, címzettel és csatolmányokkal.
Dialog {
    id: root

    title: qsTr("Send pictures by email")
    modal: true
    focus: true
    anchors.centerIn: Overlay.overlay
    padding: 18
    standardButtons: Dialog.NoButton
    width: Math.min(620, parent ? parent.width - 48 : 620)
    height: Math.min(
        root.stage === "choose" ? 470 : 620,
        parent ? parent.height - 48 : 760
    )

    property string stage: "choose"
    property var attachmentPaths: []
    property alias subject: subjectField.text
    property alias body: bodyField.text
    property alias recipient: recipientField.text
    property int selectedAttachmentIndex: -1
    property bool showHelp: false

    readonly property bool rememberChoice: rememberCheck.checked

    onOpened: {
        rememberCheck.checked = false
        showHelp = false
        selectedAttachmentIndex = attachmentPaths.length > 0 ? 0 : -1
        if (typeof emailController !== "undefined" && emailController) {
            stage = emailController.useDefaultClient ? "compose" : "choose"
            emailController.setComposeRecipient("")
        } else {
            stage = "choose"
        }
    }

    onClosed: {
        stage = "choose"
        showHelp = false
    }

    background: Rectangle {
        objectName: "emailDialogSurface"
        color: Theme.panelBg
        border.color: Theme.chromeBorder
        radius: 6
    }

    contentItem: Item {
        implicitWidth: 560
        implicitHeight: root.stage === "choose" ? 434 : 584

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            Item {
                id: emailChoicePicker
                objectName: "emailChoicePicker"
                visible: root.stage === "choose"
                enabled: visible
                Layout.fillWidth: true
                Layout.fillHeight: true

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 14

                    Label {
                        objectName: "emailChoiceTitleLabel"
                        Layout.fillWidth: true
                        text: qsTr("Select Email")
                        color: Theme.ink
                        font.pixelSize: Theme.fontSize + 2
                        font.bold: true
                    }

                    Label {
                        objectName: "emailChoiceSelectText"
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: qsTr("Select how you want to e-mail your photos.")
                        color: Theme.ink
                        font.pixelSize: Theme.fontSize
                    }

                    ColumnLayout {
                        id: emailChoicePrefContainer
                        objectName: "emailChoicePrefContainer"
                        Layout.fillWidth: true
                        spacing: 8

                        RadioButton {
                            id: emailChoiceDefaultRadio
                            objectName: "emailChoiceDefaultButton"
                            Layout.fillWidth: true
                            checked: true
                            onClicked: root.stage = "compose"

                            contentItem: RowLayout {
                                spacing: 10

                                Label {
                                    objectName: "emailChoiceMailClientLabel"
                                    text: qsTr("MAIL CLIENT")
                                    color: Theme.ink
                                    font.bold: true
                                    font.pixelSize: Theme.fontSize
                                }

                                Label {
                                    objectName: "emailChoiceMailClientDescription"
                                    Layout.fillWidth: true
                                    text: qsTr("Use my default email program.")
                                    color: Theme.ink
                                    wrapMode: Text.WordWrap
                                    font.pixelSize: Theme.fontSize
                                }
                            }
                        }

                        RadioButton {
                            id: emailChoiceGoogleRadio
                            objectName: "emailChoiceGsender"
                            Layout.fillWidth: true
                            enabled: false

                            contentItem: RowLayout {
                                spacing: 10

                                Text {
                                    objectName: "emailChoiceGoogleIcon"
                                    text: "G"
                                    color: "#4285f4"
                                    font.bold: true
                                    font.pixelSize: Theme.fontSize + 2
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2

                                    Label {
                                        objectName: "emailChoiceGoogleLabel"
                                        text: qsTr("Google Mail")
                                        color: Theme.ink
                                        font.bold: true
                                        font.pixelSize: Theme.fontSize
                                    }

                                    Label {
                                        objectName: "emailChoiceGoogleDescription"
                                        Layout.fillWidth: true
                                        text: qsTr("Use my Gmail or Google account.")
                                        color: Theme.ink
                                        wrapMode: Text.WordWrap
                                        font.pixelSize: Theme.fontSize
                                    }
                                }
                            }
                        }
                    }

                    Button {
                        id: gmailSignup
                        objectName: "emailChoiceSignupLink"
                        flat: true
                        Layout.alignment: Qt.AlignLeft
                        onClicked: Qt.openUrlExternally("http://mail.google.com")
                        contentItem: Label {
                            objectName: "emailChoiceSignupLabel"
                            text: qsTr("Don't have Gmail? Get a free account.")
                            color: Theme.ink
                            font.pixelSize: Theme.fontSize
                            font.underline: true
                            horizontalAlignment: Text.AlignLeft
                        }
                    }

                    CheckBox {
                        id: rememberCheck
                        objectName: "emailChoiceRemember"
                        Layout.fillWidth: true
                        text: qsTr("Remember this setting, don't display this dialog again.")
                    }

                    Label {
                        id: emailHelpText
                        objectName: "emailChoiceHelpText"
                        Layout.fillWidth: true
                        visible: root.showHelp
                        wrapMode: Text.WordWrap
                        text: qsTr("The pictures will be attached to a new message in your default email program.")
                        color: Theme.ink
                        font.pixelSize: Theme.fontSize
                    }

                    Item { Layout.fillHeight: true }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        PicasaButton {
                            objectName: "emailChoiceHelpButton"
                            text: qsTr("Help")
                            onClicked: root.showHelp = !root.showHelp
                            contentItem: Label {
                                objectName: "emailChoiceHelpLabel"
                                text: qsTr("Help")
                                color: Theme.ink
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }

                        Item { Layout.fillWidth: true }

                        PicasaButton {
                            objectName: "emailChoiceCancelButton"
                            text: qsTr("Cancel")
                            onClicked: root.reject()
                            contentItem: Label {
                                objectName: "emailChoiceCancelLabel"
                                text: qsTr("Cancel")
                                color: Theme.ink
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }
                }
            }

            Item {
                id: emailComposePanel
                objectName: "emailComposePanel"
                visible: root.stage === "compose"
                enabled: visible
                Layout.fillWidth: true
                Layout.fillHeight: true

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 10

                    RowLayout {
                        Layout.fillWidth: true

                        Label {
                            Layout.fillWidth: true
                            text: qsTr("New message")
                            color: Theme.ink
                            font.pixelSize: Theme.fontSize + 2
                            font.bold: true
                        }

                        Button {
                            objectName: "emailComposeChangeUserButton"
                            enabled: false
                            text: qsTr("Change User")
                            ToolTip.visible: hovered
                            ToolTip.text: qsTr("Google account sending is not available in this version.")
                            ToolTip.delay: Theme.tooltipDelay
                            contentItem: Label {
                                objectName: "emailComposeChangeUser"
                                text: qsTr("Change User")
                                color: Theme.ink
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }

                    RowLayout {
                        id: emailComposeTopEntry
                        objectName: "emailComposeTopEntry"
                        Layout.fillWidth: true
                        spacing: 8

                        Label {
                            objectName: "emailComposeToLabel"
                            text: qsTr("To:")
                            color: Theme.ink
                            font.pixelSize: Theme.fontSize
                        }

                        TextField {
                            id: recipientField
                            objectName: "emailComposeRecipientField"
                            Layout.fillWidth: true
                            color: Theme.ink
                            placeholderText: ""
                            selectByMouse: true
                            TextFieldContextArea {}
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Label {
                            objectName: "emailComposeSubjectLabel"
                            text: qsTr("Subject:")
                            color: Theme.ink
                            font.pixelSize: Theme.fontSize
                        }

                        TextField {
                            id: subjectField
                            objectName: "emailComposeSubjectField"
                            Layout.fillWidth: true
                            color: Theme.ink
                            placeholderText: ""
                            selectByMouse: true
                            TextFieldContextArea {}
                        }
                    }

                    TextArea {
                        id: bodyField
                        objectName: "emailComposeBodyField"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: Theme.ink
                        wrapMode: TextEdit.Wrap
                        selectByMouse: true
                        TextFieldContextArea {}
                        background: Rectangle {
                            color: Theme.contentPanel
                            border.color: Theme.chromeBorder
                            radius: 3
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        ListView {
                            id: attachmentPreview
                            objectName: "emailComposePreview"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 82
                            orientation: ListView.Horizontal
                            spacing: 8
                            clip: true
                            model: root.attachmentPaths
                            currentIndex: root.selectedAttachmentIndex

                            delegate: Rectangle {
                                objectName: "emailComposePreviewItem"
                                width: 118
                                height: attachmentPreview.height
                                radius: 3
                                color: root.selectedAttachmentIndex === index
                                    ? Theme.selectionBlue : Theme.contentPanel
                                border.color: Theme.chromeBorder

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 5
                                    spacing: 3

                                    Image {
                                        objectName: "emailComposePreviewImage"
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        source: (typeof emailController !== "undefined" && emailController)
                                            ? emailController.attachmentUrl(modelData) : ""
                                        fillMode: Image.PreserveAspectFit
                                        asynchronous: true
                                    }

                                    Label {
                                        Layout.fillWidth: true
                                        text: String(modelData).replace(/\\/g, "/").split("/").pop()
                                        color: Theme.ink
                                        elide: Text.ElideMiddle
                                        horizontalAlignment: Text.AlignHCenter
                                        font.pixelSize: Theme.fontSize - 2
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: root.selectedAttachmentIndex = index
                                }
                            }
                        }

                        PicasaButton {
                            objectName: "emailComposeDiscardImageButton"
                            text: "×"
                            enabled: root.selectedAttachmentIndex >= 0
                                && root.selectedAttachmentIndex < root.attachmentPaths.length
                            ToolTip.visible: hovered
                            ToolTip.text: qsTr("Remove selected image from attachment")
                            ToolTip.delay: Theme.tooltipDelay
                            onClicked: {
                                var marad = []
                                for (var i = 0; i < root.attachmentPaths.length; ++i) {
                                    if (i !== root.selectedAttachmentIndex)
                                        marad.push(root.attachmentPaths[i])
                                }
                                root.attachmentPaths = marad
                                root.selectedAttachmentIndex = marad.length > 0
                                    ? Math.min(root.selectedAttachmentIndex, marad.length - 1)
                                    : -1
                            }
                            contentItem: Label {
                                objectName: "emailComposeDiscardImage"
                                text: "×"
                                color: Theme.ink
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true

                        PicasaButton {
                            objectName: "emailComposeDiscardButton"
                            text: qsTr("Discard")
                            onClicked: root.reject()
                            contentItem: Label {
                                objectName: "emailComposeDiscard"
                                text: qsTr("Discard")
                                color: Theme.ink
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }

                        Item { Layout.fillWidth: true }

                        PicasaButton {
                            objectName: "emailComposeSendButton"
                            text: qsTr("Send")
                            accent: Theme.picasaGreen
                            onClicked: {
                                if (typeof emailController !== "undefined"
                                        && emailController) {
                                    emailController.setComposeRecipient(recipientField.text)
                                }
                                root.accept()
                            }
                            contentItem: Label {
                                objectName: "emailComposeSend"
                                text: qsTr("Send")
                                color: "white"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }
                }
            }
        }
    }
}
