import QtQuick
import QtQuick.Controls

// A Kollázs-panel „Klipek" lapja (#949, a #920 8/8, ZÁRÓ lépcsője).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` **4.3**; a feliratok és a
// buboréksúgók hivatalos magyarja a `picasa-create-features.md` **1.10.6**
// (a `qsTr` forrásszövege angol, a magyar a `picasapy_hu.ts`-ben áll).
//
// ## #1276 — a lap a VÁLASZTHATÓKAT mutatja, nem a kollázst
//
// A tulajdonos jelentése: a lap „kurvára semmit sem mutat". Az ok nem
// rajzolási hiba volt, hanem rossz forrás: a lista a kollázs SAJÁT
// csomópontjait listázta, vagyis a már feltett képeket — üres vagy frissen
// nyitott kollázsnál ez üres lap.
//
// Az eredetiben ez a lap a KÉSZLET, amiből válogatni lehet („Unused
// Pictures"): a képtálca fel nem használt része. Ezért van rajta „+",
// „–" és „Továbbiak…", és ezért ír a tulajdonos képernyőképe „Klipek
// (80)"-at egy néhány elemű kollázs mellett. A felhasználtságot az
// adatmodell tartja (`TrayItem.used`, #455/#1670), nem a nézet.
//
// ## Három különböző kijelölés, szándékosan
//
// A hivatalos buboréksúgók maguk választják szét:
//
// * a „+" a **könyvtár** kijelöltjeit veszi fel a kollázsra (ezért van
//   `librarySelection` property), és a felvett képeket felhasználtnak
//   jelöli — a tálcán MARADNAK, csak kiesnek e lap listájából;
// * a „–" *„Remove the selected pictures from the tray"* — vagyis EZEN a
//   listán bejelölteket veszi ki a tálcából. Ez a lap saját kijelölése
//   (`trayValasztas`, fotó-azonosítók), mert a tálca-elem nem
//   kollázs-csomópont: nincs is köze a vászon kijelöléséhez.
//
// Korábban a „–" a `deleteClips`-et hívta, azaz a KOLLÁZSRÓL törölt —
// miközben a saját buboréksúgója a tálcát ígérte. A kettő szétvált; most
// a súgó és a hatás ugyanazt mondja.
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

    //: #1276: a lap SAJÁT kijelölése — tálca-elemek FOTÓ-AZONOSÍTÓI.
    //: Nem rács-sor és nem kollázs-index: a tartott kép másik mappából is
    //: jöhet, ott sorszáma sincs.
    property var trayValasztas: []

    readonly property int librarySelectionCount:
        tab.librarySelection ? tab.librarySelection.length : 0

    //: A lista alsó behúzása (spec 4.3: „alul −10").
    readonly property int listBottomGap: 10

    //: #1276: a tálca FEL NEM HASZNÁLT elemei — ez a lap bemenete.
    //: A `!== undefined` őr a #1572 szabálya: a próbák stub-vezérlőjén a
    //: tulajdonság nincs rajta, és a `filter` `undefined`-on eldobna.
    readonly property var unusedClips: {
        if (!tab.controller || tab.controller.trayItems === undefined)
            return []
        var ki = []
        var elemek = tab.controller.trayItems
        for (var i = 0; i < elemek.length; ++i) {
            if (!elemek[i].used)
                ki.push(elemek[i])
        }
        return ki
    }

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
        // #1276: a kép a TÁLCÁN MARAD, csak kiesik a fel nem használtak
        // közül — ezért felhasználtnak jelöljük, nem eltávolítjuk. A
        // kollázsra helyezést továbbra is az `addClips` végzi.
        //
        // ⚠️ `setTrayUsedRows`, nem `setTrayUsed`: a `librarySelection`
        // RÁCS-SOROKAT tart, az azonosító-alapú változat pedig a 0. sort
        // némán eldobná — az első kép felvétele nyom nélkül maradna.
        onClicked: {
            if (!tab.controller) return
            tab.controller.addClips(tab.librarySelection)
            if (tab.controller.setTrayUsedRows !== undefined)
                tab.controller.setTrayUsedRows(tab.librarySelection, true)
        }
    }

    PicasaButton {
        objectName: "collageDeleteClips"
        x: 234; y: 5; width: 28; height: 28
        //: A „–" gomb felirata GONDOLATJEL (U+2013), nem kötőjel — az
        //: eredeti erőforrás is ezt használja, és a kettő eltérő szélességű.
        text: qsTr("–")
        enabled: tab.trayValasztas.length > 0
        //: Buboréksúgó a „–" gombon (1.10.6 `deleteclips`).
        ToolTip.text: qsTr("Remove the selected pictures from the tray")
        ToolTip.visible: hovered
        ToolTip.delay: 500
        // #1276: a súgó a TÁLCÁT ígéri, tehát a tálcából veszünk ki —
        // korábban a kollázsról törölt (`deleteClips`), ami más lista.
        onClicked: {
            if (!tab.controller || tab.controller.removeTrayItems === undefined)
                return
            tab.controller.removeTrayItems(tab.trayValasztas)
            tab.trayValasztas = []
        }
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

        // #1276: a lista forrása a KÉPTÁLCA fel nem használt része, nem a
        // kollázs saját csomópontjai. A tulajdonos jelentése szerint a lap
        // „kurvára semmit sem mutat" — mert a kollázsra MÁR feltett képeket
        // listázta a VÁLASZTHATÓK helyett, és üres kollázsnál ez üres lap.
        //
        // Az eredetiben a lap a készlet, amiből válogatni lehet („Unused
        // Pictures"); ezért van rajta „+", „–" és „Továbbiak…". A modell a
        // #455/#1670 tálca-csomagjából jön, ahol a FELHASZNÁLTSÁG az
        // adatmodellben él (`TrayItem.used`), nem a nézetben.
        model: tab.unusedClips

        ScrollBar.vertical: PicasaScrollBar {}

        // #1276: a modell mostantól sima JS-tömb (a `trayItems` szűrt
        // másolata), nem szerep-alapú Qt-modell — ezért `modelData`, nem
        // szerepenkénti `required property`. A szerepnevek amúgy sem
        // egyeznének: a tálca-elem `photoId`/`thumbUrl`/`name`-et ad, a
        // kollázs-csomópont `path`/`fileUrl`/`caption`-t adott.
        delegate: Item {
            id: clip
            required property int index
            required property var modelData

            readonly property int photoId: clip.modelData.photoId
            readonly property string path: clip.modelData.path
            readonly property string caption: clip.modelData.name
            //: A tálca-elemnek nincs „hiányzik" jelzője: az index csak
            //: létező fájlt tart nyilván. Ha az útvonal mégis üres, a
            //: helykitöltő csempét mutatjuk — ugyanaz a lyuk, amit a
            //: vászon rajzol (spec 9.4).
            readonly property bool missing: clip.path === ""
            readonly property bool selected:
                tab.trayValasztas.indexOf(clip.photoId) >= 0

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
                    source: clip.missing
                            || clip.modelData.thumbUrl === undefined
                            ? "" : clip.modelData.thumbUrl
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
                    // Ctrl: hozzáadás/elvétel; enélkül a kattintás EGYETLEN
                    // képre szűkíti a kijelölést — a vászon (7.1) ugyanígy
                    // viselkedik. #1276: a kijelölés a LAPÉ, és fotó-
                    // azonosítókból áll (ld. a fájl fejlécét).
                    var wanted = []
                    if (mouse.modifiers & Qt.ControlModifier) {
                        var current = tab.trayValasztas
                        var found = false
                        for (var i = 0; i < current.length; ++i) {
                            if (current[i] === clip.photoId)
                                found = true
                            else
                                wanted.push(current[i])
                        }
                        if (!found)
                            wanted.push(clip.photoId)
                    } else {
                        wanted = [clip.photoId]
                    }
                    tab.trayValasztas = wanted
                }
            }
        }
    }
}
