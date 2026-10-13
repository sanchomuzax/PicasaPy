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
            return root.canAccept()
        })
    }
    onAccepted: {
        var w = root.parseDimension(widthField.text)
        var h = root.parseDimension(heightField.text)
        if (w >= root.minDimension && h >= root.minDimension)
            root.created(w, h, nameField.text.trim())
    }

    // #4550: kétoszlopos űrlap a referencia szerint (jobbra igazított
    // feliratok, a mezők és a mintaszöveg azonos x-en)
    GridLayout {
        columns: 2
        columnSpacing: 8
        rowSpacing: 8

        Text {
            objectName: "customAspectDimensionsLabel"
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
            //: `customaspectratio.fen` „Dimensions:" csoportcím (#4550)
            text: qsTr("Dimensions:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        RowLayout {
            spacing: 0
            TextField {
                id: widthField
                objectName: "customAspectWidthField"
                Layout.preferredWidth: 46
                validator: root.dimensionValidator
                onAccepted: if (root.canAccept()) root.accept()
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
            Text {
                text: "  x  "
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            TextField {
                id: heightField
                objectName: "customAspectHeightField"
                Layout.preferredWidth: 46
                validator: root.dimensionValidator
                onAccepted: if (root.canAccept()) root.accept()
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
        }

        Text {
            objectName: "customAspectNameLabel"
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
            text: qsTr("Name:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        TextField {
            id: nameField
            objectName: "customAspectNameField"
            Layout.fillWidth: true
            Layout.preferredWidth: 195
            onAccepted: if (root.canAccept()) root.accept()
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
        }

        // #4550: a `customaspectratio.fen` „Example:" sora STATIKUS
        // `<label>` (nincs `bind`, nincs `name`) — az eredeti mintaszöveg,
        // nem a begépelt értékekből képzett előnézet.
        Text {
            objectName: "customAspectExampleLabel"
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
            text: qsTr("Example:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        Text {
            objectName: "customAspectExampleText"
            Layout.alignment: Qt.AlignLeft | Qt.AlignVCenter
            //: a hivatalos `customaspectratio/label11.title` minta (#4550)
            text: qsTr("   4 x 6   Small print")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    function canAccept() {
        return parseDimension(widthField.text) >= minDimension
            && parseDimension(heightField.text) >= minDimension
    }

    // #4891: a tizedes elválasztó vessző (magyar) és pont egyaránt jó,
    // a felület nyelvétől függetlenül — a `DoubleValidator` a nyelv
    // szerinti jelet fogadta el, a `Number()` viszont csak a pontot ismeri.
    // Egyetlen helyen alakítjuk át; érvénytelen szövegre NaN-t ad.
    function parseDimension(text) {
        return Number(String(text).replace(",", "."))
    }

    readonly property real minDimension: 0.01
    readonly property RegularExpressionValidator dimensionValidator: RegularExpressionValidator {
        regularExpression: /^[0-9]*[.,]?[0-9]*$/
    }
}
