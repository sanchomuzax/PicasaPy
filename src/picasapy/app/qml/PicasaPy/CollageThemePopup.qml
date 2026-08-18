import QtQuick
import QtQuick.Controls

// A kollázs-típus választója a „Beállítások" lap tetején (#946).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` 4.2/1. — a becsukott vezérlő
// (0, 8) 266 × 56, a lenyílója **hat sor**, mind ikon + egysoros szöveg
// („Képkupac: szétszórt képek hatását kelti"). A tételek belső margója a
// `.tre`-ben `itempadding 2 2 20 4` — a jobb oldali 20 képpont a
// lenyíló-nyílé, ezért a szöveg addig, és csak addig ér.
//
// A hat kulcs és a hozzájuk tartozó felirat a
// `docs/specs/picasa-create-features.md` 1.1 tábláját követi; a magyar
// szöveg a 4.2-es tábláé, SZÓ SZERINT (a leírásokat nem szépítjük).
//
// ⚠️ A sorrend nem a bináris tömbjének sorrendje, hanem a FELÜLETI sorrend
// — ezt a `collage.themes.COLLAGE_THEMES` rögzíti, és a teszt onnan
// olvassa. Aki itt átrendezi, a mag egyetlen forrásától tér el.
Item {
    id: control

    //: A vezérlő (AppController + CollageMixin).
    property var controller: null

    //: Nyitva van-e a lenyíló. A lap más vezérlői is becsukhatják.
    property bool expanded: false

    // A vezérlő az igazságforrás — de a kötés kibírja a HIÁNYOS vezérlőt is
    // (a panel váza `undefined`-ot adó próba-vezérlővel is felépül, és a #305
    // őre a néma QML-szkripthibát is hibának veszi).
    readonly property string currentTheme:
        control.controller && control.controller.collageTheme !== undefined
            ? control.controller.collageTheme : "picturepile"

    implicitWidth: 266
    implicitHeight: 56

    //: A `.tre` `itempadding 2 2 20 4` jobb oldali 20 képpontja: a nyíl helye.
    readonly property int arrowRoom: 20

    //: Egy lenyíló sor magassága — a becsukott vezérlő fele, hogy a hat sor
    //: a lap alsó feléig se érjen le.
    readonly property int rowHeight: 28

    // A hat téma: kulcs, ikon, név és leírás. A név és a leírás KÜLÖN
    // fordítható, mert a magyar szöveg a kettőt más ragozással köti össze.
    readonly property var themes: [
        {
            key: "picturepile",
            icon: "icons/collage-theme-picturepile.svg",
            name: qsTr("Picture Pile"),
            desc: qsTr("Looks like a pile of scattered pictures")
        },
        {
            key: "picturegrid",
            icon: "icons/collage-theme-picturegrid.svg",
            name: qsTr("Mosaic"),
            desc: qsTr("Automatically fit pictures into the page")
        },
        {
            key: "framegrid",
            icon: "icons/collage-theme-framegrid.svg",
            name: qsTr("Frame Mosaic"),
            desc: qsTr("A mosaic with a prominent center picture")
        },
        {
            key: "regulargrid",
            icon: "icons/collage-theme-regulargrid.svg",
            name: qsTr("Grid"),
            desc: qsTr("Arrange pictures into regular rows and columns")
        },
        {
            key: "contactsheet",
            icon: "icons/collage-theme-contactsheet.svg",
            name: qsTr("Contact Sheet"),
            desc: qsTr("Thumbnails with an informative header")
        },
        {
            key: "multiexp",
            icon: "icons/collage-theme-multiexp.svg",
            name: qsTr("Multiple Exposure"),
            desc: qsTr("Superimpose pictures over one another")
        }
    ]

    function themeAt(key) {
        for (var i = 0; i < control.themes.length; i++)
            if (control.themes[i].key === key)
                return control.themes[i]
        return control.themes[0]
    }

    function chooseTheme(key) {
        control.expanded = false
        if (control.controller)
            control.controller.setCollageTheme(key)
    }

    // --- a becsukott vezérlő ------------------------------------------------

    Rectangle {
        id: closedBox
        objectName: "collageThemeClosed"
        anchors.fill: parent
        color: Theme.controlBase
        border.width: 1
        border.color: Theme.chromeBorder
        radius: 2

        Image {
            id: closedIcon
            objectName: "collageThemeCurrentIcon"
            source: control.themeAt(control.currentTheme).icon
            width: 24
            height: 24
            sourceSize.width: 24
            sourceSize.height: 24
            x: 8
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            objectName: "collageThemeCurrentLabel"
            anchors.left: closedIcon.right
            anchors.leftMargin: 8
            anchors.right: parent.right
            anchors.rightMargin: control.arrowRoom
            anchors.verticalCenter: parent.verticalCenter
            // a kiválasztott sor a becsukott vezérlőn UGYANÚGY jelenik meg
            text: control.themeAt(control.currentTheme).name + ": "
                  + control.themeAt(control.currentTheme).desc
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            elide: Text.ElideRight
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        // A lenyíló-nyíl a jobb oldali 20 képpontos sávban.
        //
        // ⚠️ SVG, nem `Canvas` — ugyanaz a megfontolás, mint a
        // `CollageSettingsTab` pipájánál: a `Canvas` rajza külön festési
        // körben készül el, az `Image` viszont a mérés pillanatától
        // függetlenül ott van. Hogy a nyíl LÁTSZIK is, azt a
        // `test_a_temavalaszton_latszik_a_lenyilo_nyil` képpont-szintű őre
        // méri.
        Image {
            objectName: "collageThemeArrow"
            width: 9
            height: 5
            anchors.right: parent.right
            anchors.rightMargin: 6
            anchors.verticalCenter: parent.verticalCenter
            source: "icons/collage-dropdown-arrow.svg"
            sourceSize.width: 9
            sourceSize.height: 5
            fillMode: Image.PreserveAspectFit
        }

        MouseArea {
            anchors.fill: parent
            onClicked: control.expanded = !control.expanded
        }
    }

    // --- a lenyíló ----------------------------------------------------------

    Rectangle {
        id: list
        objectName: "collageThemeList"
        visible: control.expanded
        y: control.height
        width: control.width
        height: control.themes.length * control.rowHeight + 2
        color: Theme.controlBase
        border.width: 1
        border.color: Theme.chromeBorder
        // a lap többi vezérlője fölé
        z: 100

        Column {
            x: 1
            y: 1
            width: parent.width - 2

            Repeater {
                model: control.themes
                delegate: Rectangle {
                    id: row
                    required property var modelData
                    required property int index
                    objectName: "collageThemeOption" + index
                    width: list.width - 2
                    height: control.rowHeight
                    color: rowHover.hovered ? Theme.panelSelection
                           : (row.modelData.key === control.currentTheme
                              ? Theme.chromeBg : "transparent")

                    Image {
                        id: rowIcon
                        source: row.modelData.icon
                        width: 24
                        height: 24
                        sourceSize.width: 24
                        sourceSize.height: 24
                        // `itempadding 2 2 20 4`: bal 2, felső 2
                        x: 2
                        y: 2
                    }
                    Text {
                        anchors.left: rowIcon.right
                        anchors.leftMargin: 6
                        anchors.right: parent.right
                        anchors.rightMargin: control.arrowRoom
                        anchors.verticalCenter: parent.verticalCenter
                        text: row.modelData.name + ": " + row.modelData.desc
                        elide: Text.ElideRight
                        font.pixelSize: Theme.fontSize
                        color: rowHover.hovered ? Theme.panelSelectionText : Theme.ink
                    }
                    HoverHandler { id: rowHover }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: control.chooseTheme(row.modelData.key)
                    }
                }
            }
        }
    }
}
