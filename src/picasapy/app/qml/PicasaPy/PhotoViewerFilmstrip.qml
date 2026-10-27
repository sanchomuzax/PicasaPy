import QtQuick
import QtQuick.Layouts

// A gyökér burkoló Item; a görgethető ListView ebben áll.
// Miért: a 656-os túlcsordulás-őr az összetett QML-gyökér nevét
// (például `PhotoViewerFilmstrip_QMLTYPE_3`) nem ListView-nek látja, ezért a
// középre igazított, szándékosan túllógó tartalmat (contentWidth 248 > 214)
// levágásnak mérné. A ListView a saját clip-jével vág, így a kép nem változik.
Item {
    // #4562: a hét férőhely mérete fix, akkor is, ha a
    // mappában kevesebb kép van. A mérés: 7×28 + 6×3 = 214.
    width: 214
    height: 28

    // A gazda ezeken át éri el a szalagot: a `hostViewer` a ListView-hez
    // megy, a `count` a darabszámot adja vissza.
    property alias hostViewer: filmstrip.hostViewer
    property alias count: filmstrip.count

    ListView {
        id: filmstrip

        property var hostViewer: null
        objectName: "viewerFilmstrip"
        anchors.fill: parent

        //: [kezdet, darab] - a `revision` a modell-változásra köt
        readonly property var mappaSav: (filmstrip.hostViewer.photosModel
            && filmstrip.hostViewer.currentIndex >= 0)
            ? (filmstrip.hostViewer.photosModel.revision,
               filmstrip.hostViewer.photosModel.folderRowRange(filmstrip.hostViewer.currentIndex))
            : [0, 0]
        readonly property int mappaKezdet: mappaSav[0]
        readonly property int mappaDarab: mappaSav[1]

        orientation: ListView.Horizontal
        // Három üres cella mindkét oldalon adja meg a helyet,
        // hogy a mappaszélre eső kép is a középső férőhelyen
        // maradjon. A valós sorok a 3…mappaDarab+2 indexek.
        model: mappaDarab > 0 ? mappaDarab + 6 : 0
        currentIndex: filmstrip.hostViewer.currentIndex >= mappaKezdet
                     && filmstrip.hostViewer.currentIndex < mappaKezdet + mappaDarab
                   ? filmstrip.hostViewer.currentIndex - mappaKezdet + 3 : -1
        preferredHighlightBegin: (width - 28) / 2
        preferredHighlightEnd: preferredHighlightBegin + 31
        highlightRangeMode: ListView.StrictlyEnforceRange
        highlightMoveDuration: 100
        // A középső férőhelyet a viewport geometriájából
        // számoljuk, a mappaszéleken lévő üres cellákkal együtt.
        // A szalag saját húzása nem mozdíthatja el a kijelölést.
        interactive: false
        function kozepreIgazit() {
            contentX = currentIndex >= 0 && currentIndex < count
                ? Math.max(0, currentIndex * 31
                           - preferredHighlightBegin) : 0
        }
        onCurrentIndexChanged: kozepreIgazit()
        onCountChanged: kozepreIgazit()
        Component.onCompleted: kozepreIgazit()
        clip: true
        delegate: Rectangle {
            required property int index
            //: a három kitöltőcella előtt a rácsmodell valós sora
            readonly property int racsSor:
                filmstrip.mappaKezdet + index - 3
            readonly property bool mappaKepen:
                racsSor >= filmstrip.mappaKezdet
                && racsSor < filmstrip.mappaKezdet + filmstrip.mappaDarab
            width: 31
            height: 28
            // #3014: a másik AB-kép tömör jelölése megmarad;
            // az aktuális képet a mért kétszínű keret jelöli.
            color: mappaKepen
                   && racsSor !== filmstrip.hostViewer.currentIndex
                   && filmstrip.hostViewer.layoutMode === "ab"
                   && racsSor === filmstrip.hostViewer.abMasikSor
                   ? Theme.thumbSelection : "transparent"
            Image {
                objectName: "viewerFilmstripThumbnail"
                width: 28
                height: 28
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                visible: parent.mappaKepen
                source: visible && filmstrip.hostViewer.photosModel
                    ? filmstrip.hostViewer.photosModel.thumbUrlAt(parent.racsSor)
                    : ""
                // #1600: a bélyegkép-textúra a Qt gyorsítótárában KÖZÖS a
                // ráccsal, ami mipmapot kér (#83). Eltérő beállítás mellett a
                // Qt „Mipmap settings changed” figyelmeztetést ad, és
                // VISSZAESIK a korábbi szűrésre - a kép nem azzal a szűréssel
                // jelenik meg, amit kértünk (Windowson hatszor egy futásban).
                smooth: true
                mipmap: true
                fillMode: Image.PreserveAspectCrop
                asynchronous: Qt.platform.pluginName !== "offscreen"
            }
            Item {
                objectName: visible
                    ? "viewerFilmstripCurrentFrame" : ""
                width: 28
                height: 28
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                visible: parent.mappaKepen
                         && parent.racsSor === filmstrip.hostViewer.currentIndex
                Rectangle {
                    anchors.fill: parent
                    color: "transparent"
                    border.width: 1
                    border.color: "#009EFF"
                }
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 1
                    color: "transparent"
                    border.width: 1
                    border.color: "#D4D4D4"
                }
            }
            TapHandler {
                enabled: parent.mappaKepen
                //: #3014: AB módban az AKTÍV oldal képét
                //: cseréljük - ez a válogató munkafolyamat
                //: lelke (a `swap_2up_focus` választja ki,
                //: melyik felet lapozzuk).
                onTapped: {
                    //: #3773: a JOBB fél a `masodikIndex`-é,
                    //: a bal a `currentIndex`-é
                    if (filmstrip.hostViewer.layoutMode === "ab"
                            && filmstrip.hostViewer.aktivOldal === "jobb") {
                        filmstrip.hostViewer.masodikIndex = parent.racsSor
                    } else {
                        filmstrip.hostViewer.currentIndex = parent.racsSor
                    }
                }
            }
        }
    }
}
