import QtQuick

// #7380: a Szöveg eszköz szövege KÖZVETLENÜL a képre gépelhető, mint az
// eredeti Picasában (job-839): a panelben nincs szövegmező.
//
// - kattintásig a kép KÖZEPÉN a „Type anywhere to add text" hint áll
//   (`EditText::GhostText`, `__10`);
// - a kattintás után a hely jelölt: a szövegkurzor a ponton áll (`__12`);
// - a gépelt szöveg a képen jelenik meg, lekerekített, vastag világos keretű
//   dobozban, amelynek a belseje átlátszó (`__14`: a belső képpontok a
//   kép azonos képpontjaival egyeznek, arány 1,00);
// - a szöveg bal felső sarka a kattintott ponton áll, ahogy az Alkalmaz
//   utáni kész szöveg is (`__26`; a rajzoló pontja a doboz teteje).
//
// A szerkesztett szöveget ez a komponens rajzolja, ezért ilyenkor az
// előnézeti raszter azt a blokkot kihagyja (`setTextInlineEditing`).
//
// A komponenst a `PhotoViewerPhotoArea` a `fokuszKep`-re ülteti, a rajzolt
// kép területére (ugyanaz a mérce, mint a `textClickArea`).
Item {
    id: gyoker

    //: a fotóterület: a kép, a szerkesztő panel és a controller gazdája
    required property var photoArea

    readonly property var panel: photoArea.hostEditorPanel
    readonly property var kep: photoArea.fokuszKep
    readonly property var ctl: photoArea.hostEditCtl
    //: a szerkesztett doboz helye a képre normalizálva (üres: nincs)
    readonly property var hely: helyErtek()
    readonly property bool eszkozNyitva: !!panel && panel.textActive
    readonly property bool szerkeszt: eszkozNyitva && hely.x !== undefined

    //: #7380: MÉRT, `__14` (12 pt): a külső keret a szövegsor dobozától
    //: 32 képpontra áll minden irányban; 3 + 8 + 3 képpont a keret
    //: (sötét · világos · sötét), a többi átlátszó belső tér.
    readonly property int keretKivul: 32
    readonly property color sotetSav: "#2d2d2d"
    readonly property color vilagosSav: "#acacac"

    objectName: "textPhotoOverlay"
    z: 3
    x: (kep.width - kep.paintedWidth) / 2
    y: (kep.height - kep.paintedHeight) / 2
    width: kep.paintedWidth
    height: kep.paintedHeight

    // Ezt az inline szerkesztő rajzolja, miközben a preview kihagyja a
    // kiválasztott szöveget. A tárolt x/y a forgatott befoglaló bal felső
    // sarka, ezért a szövegmezőt a befoglaló közepéhez igazítjuk.
    QtObject {
        id: forgatas
        readonly property real radians: {
            if (!gyoker.ctl || !gyoker.szerkeszt) return 0
            var selectedIndex = gyoker.ctl.textSelectedIndex
            var items = gyoker.ctl.textOverlayItems
            for (var i = 0; i < items.length; ++i) {
                if (items[i].index === selectedIndex)
                    return items[i].rotation
            }
            return 0
        }
        readonly property real degrees: radians * 180 / Math.PI
        readonly property real width: bevitel.width * Math.abs(Math.cos(radians))
                                     + bevitel.height * Math.abs(Math.sin(radians))
        readonly property real height: bevitel.width * Math.abs(Math.sin(radians))
                                      + bevitel.height * Math.abs(Math.cos(radians))
    }

    function helyErtek() {
        return (typeof editController !== "undefined" && editController)
            ? editController.textEditPlacement : ({})
    }

    onSzerkesztChanged: {
        if (typeof editController !== "undefined" && editController)
            editController.setTextInlineEditing(szerkeszt)
    }

    Text {
        objectName: "textHint"
        visible: gyoker.eszkozNyitva && !gyoker.szerkeszt
        anchors.centerIn: parent
        //: `EditText::GhostText` - hivatalos felirat az eredeti
        //: nyelvi erőforrásból
        text: qsTr("Type anywhere to add text")
        color: "#ffffff"
        font.pixelSize: Theme.fontSize - 3
    }

    // a vastag, lekerekített keret: három egymásba rakott, átlátszó belsejű
    // sáv (külső sötét · világos · belső sötét)
    Item {
        id: keret
        objectName: "textBoxFrame"
        visible: gyoker.szerkeszt && bevitel.text.length > 0
        x: bevitel.x - gyoker.keretKivul
        y: bevitel.y - gyoker.keretKivul
        width: bevitel.width + 2 * gyoker.keretKivul
        height: bevitel.height + 2 * gyoker.keretKivul
        rotation: forgatas.degrees
        transformOrigin: Item.Center

        Rectangle {
            anchors.fill: parent
            color: "transparent"
            radius: 22
            antialiasing: true
            border.width: 3
            border.color: gyoker.sotetSav
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: 3
            color: "transparent"
            radius: 19
            antialiasing: true
            border.width: 8
            border.color: gyoker.vilagosSav
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: 11
            color: "transparent"
            radius: 11
            antialiasing: true
            border.width: 3
            border.color: gyoker.sotetSav
        }
    }

    TextInput {
        id: bevitel
        // a régi panelmező neve: a próbák és a kötések ezen keresik
        objectName: "textContentField"
        visible: gyoker.szerkeszt
        // a pont a szövegsor doboza BAL FELSŐ sarka; a középre/jobbra igazított
        // szövegnél a pont a sor közepe/jobb széle (mint a rajzolónál)
        x: (gyoker.hely.x === undefined ? 0 : gyoker.hely.x * gyoker.width)
           - (gyoker.panel && gyoker.panel.textAlign === "center" ? width / 2
              : gyoker.panel && gyoker.panel.textAlign === "right" ? width : 0)
           + (forgatas.width - width) / 2
        y: (gyoker.hely.y === undefined ? 0 : gyoker.hely.y * gyoker.height)
           + (forgatas.height - height) / 2
        width: Math.max(2, contentWidth + 2)
        height: contentHeight
        rotation: forgatas.degrees
        transformOrigin: Item.Center
        topPadding: 0
        bottomPadding: 0
        leftPadding: 0
        rightPadding: 0
        selectByMouse: true
        activeFocusOnPress: true
        font.family: gyoker.panel ? gyoker.panel.textFontFamily : ""
        // a raszter betűmérete `méret × kép magassága ÷ 360` képpont
        font.pixelSize: Math.max(1, Math.round(
            (gyoker.panel ? gyoker.panel.textFontSize : 12)
            * gyoker.height / 360))
        font.bold: !!gyoker.panel && gyoker.panel.textBold
        font.italic: !!gyoker.panel && gyoker.panel.textItalic
        font.underline: !!gyoker.panel && gyoker.panel.textUnderline
        color: {
            if (!gyoker.panel) return "#ffffff"
            var c = Qt.color(gyoker.panel.textFillEnabled
                             ? gyoker.panel.textFillColor
                             : gyoker.panel.textOutlineColor)
            return Qt.rgba(c.r, c.g, c.b, gyoker.panel.textOpacity)
        }
        text: gyoker.panel ? gyoker.panel.textDraftContent : ""

        onTextChanged: {
            if (!gyoker.panel || text === gyoker.panel.textDraftContent) return
            gyoker.panel.textDraftContent = text
            gyoker.panel.textDraftEdited(text)
        }
        onVisibleChanged: {
            if (visible) forceActiveFocus()
        }
    }
}
