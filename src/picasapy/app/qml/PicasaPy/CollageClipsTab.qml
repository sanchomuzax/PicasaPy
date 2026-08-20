import QtQuick
import QtQuick.Controls

// A Kollázs-panel „Klipek" lapja (#949, a #920 8/8, ZÁRÓ lépcsője).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` **4.3**; a feliratok és a
// buboréksúgók hivatalos magyarja a `picasa-create-features.md` **1.10.6**
// (a `qsTr` forrásszövege angol, a magyar a `picasapy_hu.ts`-ben áll).
//
// ## Egy kijelölés van, nem kettő
//
// A klip-lista NEM tart saját kijelölést: a csempére kattintva a vezérlő
// `setCollageSelection`-jét hívjuk, és a jelölést a `collageSelection`-ből
// olvassuk vissza. Ez azért fontos, mert ugyanaz a kijelölés vezérli a
// vásznat, a vászon körüli gombsorokat és a „–" gombot. Két, egymással
// szinkronban tartott kijelölés-lista pár művelet után elválna, és a
// felhasználó azt látná, hogy a „–" mást töröl, mint amit a listán
// bejelölt.
//
// ## A „+" és a „–" NEM ugyanabból a listából dolgozik
//
// A hivatalos buboréksúgók ezt ki is mondják: a „+" a **kijelölt
// klipeket** veszi fel (azaz a KÖNYVTÁR kijelölését — ezért van
// `librarySelection` property), a „–" pedig a kollázs kijelölt képeit
// távolítja el. A kettő két különböző kijelölés, és ezt a felület
// szerkezetének is tükröznie kell.
//
// ## Egy geometriai feszültség, tudatosan vállalva
//
// A spec 4.1 szerint a lap tartója 256 képpont széles, a 4.3 viszont a
// „–" gombot 234-re teszi 28 szélességgel, azaz 262-ig ér. A két szám a
// `.tre` két különböző helyéről jön. A tartó mérete a #945 SZERZŐDÉSE (52
// teszt őrzi), a gombok helye a 4.3-é — ezért a gomb néhány képponttal
// túlnyúlik a tartón, de a bal hasábon (276) belül marad, tehát a
// felhasználó ebből semmit nem lát. A listát viszont a tartó jobb széléig
// nyújtjuk: a `.tre` `m_offsetLTR`-je pont ezt mondja.
Item {
    id: tab

    // A lap tervezői mérete (spec 4.1).
    implicitWidth: 256
    implicitHeight: 352

    //: A vezérlő (AppController + CollageMixin).
    property var controller: null

    //: A KÖNYVTÁR pillanatnyi kijelölése (rács-sorok) — ebből vesz fel a „+".
    property var librarySelection: []

    //: „Továbbiak..." — a gazda a Könyvtár fülre vált, és ott megjelenít egy
    //: „Vissza a kollázshoz" gombot; a kollázs lapja NYITVA marad. A
    //: fülváltás a gazdáé (spec 13.: a `Main.qml` az integrátoré).
    signal getMoreClipsRequested()

    readonly property var selection:
        tab.controller && tab.controller.collageSelection !== undefined
            ? tab.controller.collageSelection : []

    readonly property int librarySelectionCount:
        tab.librarySelection ? tab.librarySelection.length : 0

    //: A lista alsó behúzása (spec 4.3: „alul −10").
    readonly property int listBottomGap: 10

    // --- A három gomb ------------------------------------------------------

    PicasaButton {
        objectName: "collageGetMoreClips"
        x: 6; y: 5; width: 166; height: 28
        text: qsTr("Get more...")
        //: Buboréksúgó a „Továbbiak..." gombon (1.10.6 `getmoreclips`).
        ToolTip.text: qsTr("Load more pictures from the library")
        ToolTip.visible: hovered
        ToolTip.delay: 500
        // A gomb BAL oldalán ikon áll (spec 4.3) — ezért cseréljük a
        // `PicasaButton` egyszerű szöveges tartalmát egy sorra.
        contentItem: Row {
            spacing: 6
            leftPadding: 4
            Image {
                objectName: "collageGetMoreClipsIcon"
                anchors.verticalCenter: parent.verticalCenter
                source: "icons/collage-back.svg"
                sourceSize.width: 17
                sourceSize.height: 15
                width: 17
                height: 15
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Get more...")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
        }
        onClicked: tab.getMoreClipsRequested()
    }

    PicasaButton {
        objectName: "collageAddClips"
        x: 201; y: 5; width: 28; height: 28
        text: qsTr("+")
        enabled: tab.librarySelectionCount > 0
        //: Buboréksúgó a „+" gombon (1.10.6 `addclips`).
        ToolTip.text: qsTr("Add selected clips to the collage")
        ToolTip.visible: hovered
        ToolTip.delay: 500
        onClicked: if (tab.controller) tab.controller.addClips(tab.librarySelection)
    }

    PicasaButton {
        objectName: "collageDeleteClips"
        x: 234; y: 5; width: 28; height: 28
        //: A „–" gomb felirata GONDOLATJEL (U+2013), nem kötőjel — az
        //: eredeti erőforrás is ezt használja, és a kettő eltérő szélességű.
        text: qsTr("–")
        enabled: tab.selection.length > 0
        //: Buboréksúgó a „–" gombon (1.10.6 `deleteclips`).
        ToolTip.text: qsTr("Remove the selected pictures from the tray")
        ToolTip.visible: hovered
        ToolTip.delay: 500
        onClicked: if (tab.controller) tab.controller.deleteClips(tab.selection)
    }

    // --- A klip-lista ------------------------------------------------------

    GridView {
        id: clipList
        objectName: "collageClipList"
        x: 4
        y: 36
        width: tab.width - x
        height: Math.max(0, tab.height - y - tab.listBottomGap)
        clip: true
        cellWidth: 62
        cellHeight: 62

        model: tab.controller ? tab.controller.collageNodes : null

        ScrollBar.vertical: PicasaScrollBar {}

        delegate: Item {
            id: clip
            required property int index
            required property string path
            required property bool selected
            required property bool missing
            required property string caption

            objectName: "collageClip" + clip.index
            width: clipList.cellWidth
            height: clipList.cellHeight

            Rectangle {
                anchors.fill: parent
                anchors.margins: 2
                color: clip.selected ? Theme.thumbSelection : Theme.thumbCard
                border.width: 1
                border.color: clip.selected
                              ? Theme.thumbSelection : Theme.thumbBorder

                Image {
                    objectName: "collageClipImage" + clip.index
                    anchors.fill: parent
                    anchors.margins: 3
                    visible: !clip.missing && clip.path !== ""
                    //: ⚠️ NEM `"file:" + útvonal`: Windowson a meghajtóbetű
                    //: PORTNAK látszik (érvénytelen URL, üres kép), `#`-es
                    //: fájlnévnél pedig Linuxon is elvágja a nevet (#1019).
                    //: Az URL a MODELLBŐL jön, a Qt `fromLocalFile`-ján át.
                    //: A null-őr a #305 szabálya: teszt-kettősöknél és a
                    //: modell lebontásakor a szerep `undefined`-ot ad, amit a
                    //: `url` nem fogad el — QML-szkripthiba lenne belőle.
                    source: clip.missing || clip.path === ""
                            || clip.fileUrl === undefined
                            ? "" : clip.fileUrl
                    // A miniatűr KICSI: egy 350 képes kollázs listája
                    // teljes felbontású dekódolással megfojtaná a felületet.
                    sourceSize.width: 128
                    sourceSize.height: 128
                    asynchronous: true
                    cache: true
                    fillMode: Image.PreserveAspectCrop
                    clip: true
                }

                // Nem található kép: ugyanaz a helykitöltő csempe, amit a
                // vászon rajzol (spec 9.4) — a lyuk LÁTSZÓDJON, különben a
                // felhasználó azt hiszi, ő törölte.
                Rectangle {
                    objectName: "collageClipMissing" + clip.index
                    anchors.fill: parent
                    anchors.margins: 3
                    visible: clip.missing
                    color: "#c8c8c8"
                    border.width: 1
                    border.color: "#787878"

                    Text {
                        anchors.centerIn: parent
                        text: "?"
                        color: "#787878"
                        font.pixelSize: Theme.fontSize
                    }
                }
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton
                onClicked: function (mouse) {
                    if (!tab.controller)
                        return
                    // Ctrl: hozzáadás/elvétel; enélkül a kattintás EGYETLEN
                    // képre szűkíti a kijelölést — a vászon (7.1) ugyanígy
                    // viselkedik, és a két felület ugyanazt a kijelölést írja.
                    var wanted = []
                    if (mouse.modifiers & Qt.ControlModifier) {
                        var current = tab.selection
                        var found = false
                        for (var i = 0; i < current.length; ++i) {
                            if (current[i] === clip.index)
                                found = true
                            else
                                wanted.push(current[i])
                        }
                        if (!found)
                            wanted.push(clip.index)
                    } else {
                        wanted = [clip.index]
                    }
                    tab.controller.setCollageSelection(wanted)
                }
            }
        }
    }
}
