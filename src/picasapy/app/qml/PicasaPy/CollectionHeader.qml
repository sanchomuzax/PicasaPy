import QtQuick

// Egy gyűjtemény-fejléc a bal hasábon (#320): zöld ▼ (nyitva) / piros ▶
// (csukva) háromszög + felirat, a Picasa fejléc-gradiensével. A `headerText`
// felülírhatja a "label (itemCount)" alapértelmezést (pl. kereső-eredmény
// szövege).
//
// #730: a `FolderPane.qml` inline `component`-jéből emeltük ki önálló
// fájlba — a hasáb görgetése (Flickable) tovább növelte volna a már amúgy
// is túl nagy gazdafájlt.
Rectangle {
    id: header
    property string label: ""
    property int itemCount: 0
    property string headerText: ""
    property string labelObjectName: ""
    property bool collapsed: false
    signal toggled()
    // #461: BEZÁRHATÓ gyűjtemény (csak a felhasználói gyűjteményeknél).
    // Az eredeti figyelmeztetése mondja meg, hol a kapcsoló: „Egy
    // gyűjtemény megnyitásához kattintson duplán a nevére, vagy
    // kattintson a MELLETTE LÉVŐ IKONRA."
    // (IDS_CLOSING_LAST_COLLECTION_MSG) — ezért ül a jelző közvetlenül
    // a név mellett, és ezért nyit a néven a duplakattintás is.
    property bool closable: false
    property bool closed: false
    signal closeToggled()
    // #422: a felhasználói gyűjtemény-fejléc jobbklikk-menüjéhez — a
    // beépített öt gyűjtemény fejléce (Albumok/Emberek/…) nem köti be,
    // csak a FolderPane.qml customCollectionsRepeater-beli példánya.
    signal rightClicked()

    // a sor saját objectName-je a fejlécéből képezve (teszthez: a
    // "toggled" jel innen közvetlenül kiváltható, ahogy a projektben
    // szokásos egyedi gombok "clicked" jelének közvetlen hívása)
    objectName: header.labelObjectName !== "" ? header.labelObjectName + "Row" : ""
    height: 22
    gradient: Gradient {
        GradientStop { position: 0.0; color: Theme.panelHeaderTop }
        GradientStop { position: 1.0; color: Theme.panelHeaderBg }
    }
    border.color: Theme.chromeBorder
    Row {
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left; anchors.leftMargin: 4
        spacing: 4
        Text {
            text: header.collapsed ? "▶" : "▼"
            font.pixelSize: 8
            // Audit: az eredeti Picasában a nyitott gyűjtemény zöld, a
            // csukott piros — ez itt ÁLLAPOT-jelzés, nem márka-szerep;
            // külön "collapsed" jelzőszín híján a brandRed tokent
            // kölcsönözzük erre a célra.
            color: header.collapsed ? Theme.brandRed : Theme.picasaGreen
        }
        Text {
            objectName: header.labelObjectName
            text: header.headerText !== "" ? header.headerText
                  : header.label + " (" + header.itemCount + ")"
            font.pixelSize: Theme.fontSize; font.bold: true
            color: Theme.panelHeaderText
        }
        // #461: nyitott/zárt jelző — a NÉV MELLETT, ahogy az eredeti
        // üzenete leírja. Szándékosan más jelalak, mint a bal oldali
        // összecsukó háromszög: a kettő két külön művelet (az egyik a
        // fát hajtja össze, a másik a képeket veszi ki a rácsból).
        Text {
            objectName: header.labelObjectName !== ""
                        ? header.labelObjectName + "CloseToggle" : ""
            visible: header.closable
            text: header.closed ? "○" : "●"
            font.pixelSize: 9
            color: Theme.panelHeaderText
            TapHandler {
                gesturePolicy: TapHandler.ReleaseWithinBounds
                onTapped: header.closeToggled()
            }
        }
    }
    MouseArea {
        anchors.fill: parent
        onClicked: header.toggled()
        // #461: a BEZÁRT gyűjtemény a nevére duplán kattintva is nyílik
        onDoubleClicked: if (header.closed) header.closeToggled()
    }
    // #422: jobbklikk a gyűjtemény-menühöz — a mappasor/albumsor
    // mintáját követve TapHandler-rel (ReleaseWithinBounds), hogy a
    // sima MouseArea bal-kattintás-kezelését ne zavarja.
    TapHandler {
        acceptedButtons: Qt.RightButton
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onTapped: header.rightClicked()
    }
}
