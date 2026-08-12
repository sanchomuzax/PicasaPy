import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// "Add Custom Aspect Ratio…" — szélesség × magasság + név bekérő (#448):
// az eredeti Picasa vágás-panelének egyéni-arány dialógusa (a jegy leírása
// szerint: szélesség × magasság + név, a listában "4 x 6   Small print"
// alakban jelenik meg — ld. EditorPanel.qml `aspectFullList`). A hívó
// (EditorPanel.qml) végzi a controller-hívást a `created` jelre — a
// NewCollectionDialog.qml mintáját követve.
Dialog {
    id: root
    objectName: "addCustomAspectRatioDialog"
    title: qsTr("Add Custom Aspect Ratio")
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    standardButtons: Dialog.Ok | Dialog.Cancel

    // szélesség, magasság, név — bármilyen mértékegységben, csak az
    // ARÁNYuk számít (EditorPanel.qml ratio = width / height)
    signal created(real width, real height, string name)

    onOpened: {
        widthField.text = ""
        heightField.text = ""
        nameField.text = ""
        widthField.forceActiveFocus()
        standardButton(Dialog.Ok).enabled = Qt.binding(function() {
            return Number(widthField.text) > 0 && Number(heightField.text) > 0
        })
    }
    onAccepted: {
        var w = Number(widthField.text)
        var h = Number(heightField.text)
        if (w > 0 && h > 0) root.created(w, h, nameField.text.trim())
    }

    ColumnLayout {
        spacing: 8
        RowLayout {
            spacing: 8
            Text {
                text: qsTr("Width:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            TextField {
                id: widthField
                objectName: "customAspectWidthField"
                Layout.preferredWidth: 70
                validator: DoubleValidator {
                    bottom: 0.01
                    notation: DoubleValidator.StandardNotation
                }
                onAccepted: if (root.canAccept()) root.accept()
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
            Text {
                text: "x"
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            TextField {
                id: heightField
                objectName: "customAspectHeightField"
                Layout.preferredWidth: 70
                validator: DoubleValidator {
                    bottom: 0.01
                    notation: DoubleValidator.StandardNotation
                }
                onAccepted: if (root.canAccept()) root.accept()
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
        }
        RowLayout {
            spacing: 8
            Text {
                text: qsTr("Name:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            TextField {
                id: nameField
                objectName: "customAspectNameField"
                Layout.preferredWidth: 160
                onAccepted: if (root.canAccept()) root.accept()
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
        }
    }

    function canAccept() {
        return Number(widthField.text) > 0 && Number(heightField.text) > 0
    }
}
