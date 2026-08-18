import QtQuick
import QtQuick.Controls

// Az „Oldalformátum" legördülő a kollázs beállítás-lapján (#946).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` 4.2/12. és
// `picasa-kollazs-felulet.md` **7.** — a menü (3, 255) 243 × 21, a
// lenyílója **20 tételes**: 18 beépített formátum + a „Custom Aspect
// Ratios" csoportcím + a „Add Custom Aspect Ratio…" sor. A `.tre`
// `Property maxrows 0`: a lenyíló NEM korlátozza a sorok számát — csak a
// panel magassága, azon túl gördül.
//
// ⚠️ A tételek IGAZSÁGFORRÁSA a `src/picasapy/collage/page_formats.py`
// (`PAGE_FORMATS`): a kulcsok, a feliratok és a SORREND onnan valók, és a
// `test_collage_format_menu_source_946.py` sorról sorra összeveti a
// kettőt. Aki itt átír egy kulcsot, a `.cxf`-be írna rossz formátumot —
// a teszt ezért bukik meg, nem a szépség kedvéért.
//
// Az egyéni képarányok a MEGLÉVŐ #448-as úton élnek (`customAspectRatios`,
// `addCustomAspectRatio`, `deleteCustomAspectRatio`) — az `EditorPanel.qml`
// `aspectFullList`-jével azonos `custom:<név>:<szél>x<mag>` kulcsalakkal.
// Második megvalósítás ne szülessen.
Item {
    id: menu

    //: A vezérlő (AppController + CollageMixin + CustomAspectRatiosMixin).
    property var controller: null

    //: Nyitva van-e a lenyíló.
    property bool expanded: false

    //: A felvevő sorra kattintva — a lap nyitja a #448-as párbeszédet.
    signal addCustomRequested()

    implicitWidth: 243
    implicitHeight: 21

    //: Egy sor magassága. A húsz tétel így fér el a 351 képpontos lapon.
    readonly property int rowHeight: 16

    readonly property string currentKey:
        menu.controller ? menu.controller.collageFormatKey : "Desktop4x3"

    readonly property var customRatios:
        menu.controller ? menu.controller.customAspectRatios : []

    // A tizennyolc beépített formátum — a `page_formats.PAGE_FORMATS`
    // sorrendjében és kulcsaival.
    readonly property var formats: [
        { key: "Manual", label: qsTr("Manual"), note: "" },
        { key: "5x8m", label: "5 x 8", note: "" },
        { key: "9x13m", label: "9 x 13", note: qsTr("Small print") },
        { key: "10x15m", label: "10 x 15", note: qsTr("Large print") },
        { key: "Crop13x18m", label: "13 x 18", note: "" },
        { key: "Crop20x25m", label: "20 x 25", note: "" },
        { key: "A4", label: "A4", note: qsTr("Full page") },
        { key: "4x6", label: "4 x 6", note: qsTr("Small print") },
        { key: "5x7", label: "5 x 7", note: qsTr("Large print") },
        { key: "FullPage", label: "8.5 x 11", note: qsTr("Letter paper") },
        { key: "8x10", label: "8 x 10", note: "" },
        { key: "A4PageCollage", label: qsTr("A4 paper"), note: "" },
        { key: "Square", label: qsTr("Square"), note: qsTr("CD Cover") },
        { key: "Desktop4x3", label: "4:3", note: qsTr("Standard screen") },
        { key: "Widescreen", label: "16:10", note: qsTr("Widescreen monitor") },
        { key: "HDTV16x9", label: "16:9", note: "HDTV" },
        { key: "WideFrame", label: "5:3", note: qsTr("Widescreen Photo Frame") },
        { key: "CurrentDisplay", label: qsTr("Current display"), note: "" }
    ]

    //: Egy egyéni arány kulcsa — az `EditorPanel.qml` alakjával azonos.
    function customKey(ratio) {
        return "custom:" + ratio.name + ":" + ratio.width + "x" + ratio.height
    }

    function customLabel(ratio) {
        return ratio.width + " x " + ratio.height + "   " + ratio.name
    }

    //: A becsukott vezérlőn álló felirat — beépített vagy egyéni tételé.
    function labelFor(key) {
        for (var i = 0; i < menu.formats.length; i++)
            if (menu.formats[i].key === key)
                return menu.formats[i].label
        for (var j = 0; j < menu.customRatios.length; j++)
            if (menu.customKey(menu.customRatios[j]) === key)
                return menu.customLabel(menu.customRatios[j])
        return key
    }

    function choose(key) {
        menu.expanded = false
        if (menu.controller)
            menu.controller.setCollageFormat(key)
    }

    // --- a becsukott vezérlő ------------------------------------------------

    Rectangle {
        anchors.fill: parent
        radius: 2
        color: Theme.controlBase
        border.width: 1
        border.color: Theme.chromeBorder

        Text {
            objectName: "collageFormatLabel"
            anchors.left: parent.left
            anchors.leftMargin: 6
            anchors.right: parent.right
            anchors.rightMargin: 20
            anchors.verticalCenter: parent.verticalCenter
            text: menu.labelFor(menu.currentKey)
            elide: Text.ElideRight
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        Text {
            anchors.right: parent.right
            anchors.rightMargin: 6
            anchors.verticalCenter: parent.verticalCenter
            text: "▼"
            font.pixelSize: 8
            color: Theme.ink
        }
        MouseArea {
            anchors.fill: parent
            onClicked: menu.expanded = !menu.expanded
        }
        //: `format_menu` buboréksúgó (a hivatalos magyarral).
        ToolTip.text: qsTr("You can select the relative width and height of "
                           + "the collage")
        ToolTip.visible: menuHover.hovered
        ToolTip.delay: 500
        HoverHandler { id: menuHover }
    }

    // --- a lenyíló ----------------------------------------------------------

    // A tartalom teljes magassága: 18 formátum + csoportcím + az egyéniek +
    // a felvevő sor.
    readonly property real listContentHeight:
        (menu.formats.length + 2 + menu.customRatios.length) * menu.rowHeight + 2

    //: A lenyíló BELEFÉR a bal hasábba: ha alatta nincs hely, fölfelé nyílik,
    //: és ha úgy sem fér el, gördíthetővé válik (`maxrows 0` = nincs
    //: sorszám-korlát; a korlát a panel magassága).
    readonly property real listHeight:
        menu.parent ? Math.min(menu.listContentHeight, menu.parent.height - 2)
                    : menu.listContentHeight

    readonly property real listY:
        menu.parent
            ? Math.min(menu.height,
                       menu.parent.height - 1 - menu.y - menu.listHeight)
            : menu.height

    Rectangle {
        id: list
        objectName: "collageFormatList"
        visible: menu.expanded
        x: 0
        y: menu.listY
        width: menu.width
        height: menu.listHeight
        color: Theme.controlBase
        border.width: 1
        border.color: Theme.chromeBorder
        clip: true
        // a lap többi vezérlője fölé
        z: 150

        Flickable {
            anchors.fill: parent
            anchors.margins: 1
            contentHeight: rows.height
            interactive: contentHeight > height
            boundsBehavior: Flickable.StopAtBounds

            Column {
                id: rows
                width: list.width - 2

                // a 18 beépített formátum
                Repeater {
                    model: menu.formats
                    delegate: Rectangle {
                        id: sor
                        required property var modelData
                        required property int index
                        objectName: "collageFormatOption" + index
                        property string text: sor.modelData.label
                        width: rows.width
                        height: menu.rowHeight
                        color: sorHover.hovered
                               ? Theme.panelSelection
                               : (sor.modelData.key === menu.currentKey
                                  ? Theme.chromeBg : "transparent")
                        Text {
                            id: sorLabel
                            anchors.left: parent.left
                            anchors.leftMargin: 6
                            anchors.verticalCenter: parent.verticalCenter
                            text: sor.modelData.label
                            font.pixelSize: Theme.fontSize
                            color: sorHover.hovered ? Theme.panelSelectionText
                                                    : Theme.ink
                        }
                        Text {
                            anchors.left: sorLabel.right
                            anchors.leftMargin: 8
                            anchors.right: parent.right
                            anchors.rightMargin: 6
                            anchors.verticalCenter: parent.verticalCenter
                            horizontalAlignment: Text.AlignRight
                            elide: Text.ElideRight
                            visible: text.length > 0
                            text: sor.modelData.note
                            font.pixelSize: Theme.fontSize - 1
                            color: sorHover.hovered ? Theme.panelSelectionText
                                                    : Theme.textGray
                        }
                        HoverHandler { id: sorHover }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: menu.choose(sor.modelData.key)
                        }
                    }
                }

                // csoportcím: az egyéni arányok
                Rectangle {
                    objectName: "collageFormatCustomHeader"
                    width: rows.width
                    height: menu.rowHeight
                    color: "transparent"
                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: 6
                        anchors.verticalCenter: parent.verticalCenter
                        text: qsTr("Custom Aspect Ratios")
                        font.pixelSize: Theme.fontSize
                        font.bold: true
                        color: Theme.textGray
                    }
                }

                // a felhasználó egyéni arányai (#448)
                Repeater {
                    model: menu.customRatios
                    delegate: Rectangle {
                        id: egyeni
                        required property var modelData
                        required property int index
                        objectName: "collageFormatCustom" + index
                        property string text: menu.customLabel(egyeni.modelData)
                        width: rows.width
                        height: menu.rowHeight
                        color: egyeniHover.hovered
                               ? Theme.panelSelection
                               : (menu.customKey(egyeni.modelData) === menu.currentKey
                                  ? Theme.chromeBg : "transparent")
                        Text {
                            anchors.left: parent.left
                            anchors.leftMargin: 6
                            anchors.right: parent.right
                            anchors.rightMargin: 6
                            anchors.verticalCenter: parent.verticalCenter
                            elide: Text.ElideRight
                            text: egyeni.text
                            font.pixelSize: Theme.fontSize
                            color: egyeniHover.hovered ? Theme.panelSelectionText
                                                       : Theme.ink
                        }
                        HoverHandler { id: egyeniHover }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: menu.choose(menu.customKey(egyeni.modelData))
                        }
                    }
                }

                // „Add Custom Aspect Ratio…" — a MEGLÉVŐ #448-as párbeszéd
                Rectangle {
                    objectName: "collageFormatAddCustom"
                    width: rows.width
                    height: menu.rowHeight
                    color: addHover.hovered ? Theme.panelSelection : "transparent"
                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: 6
                        anchors.verticalCenter: parent.verticalCenter
                        text: qsTr("Add Custom Aspect Ratio…")
                        font.pixelSize: Theme.fontSize
                        color: addHover.hovered ? Theme.panelSelectionText : Theme.ink
                    }
                    HoverHandler { id: addHover }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            menu.expanded = false
                            menu.addCustomRequested()
                        }
                    }
                }
            }
        }
    }
}
