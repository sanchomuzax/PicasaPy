import QtQuick
import QtQuick.Controls

// #894: legördülő lista a MÉRT Picasa-rajzzal.
//
// A panel rajza a `respack.yt` `listdecrect/listdecrect` rétege (17 × 17,
// nyújtható), képpontból olvasva:
//
//   sor 2:    #D6D6D6   lágy árnyék (a keret KÍVÜL)
//   sor 3:    #BABABA   a keret, 1 px
//   sor 4–12  #E8E8E8   a kitöltés — **SÍK**, nincs színátmenet
//   sor 13:   #F8F8F8   belső fénykiemelés alul
//   sor 14:   #F0F0F0
//
// Vízszintesen ugyanez, de a bal él árnyéka kicsit sötétebb
// (#DDDDDD → #C7C7C7) — ugyanaz a bal-felüli fényforrás, mint a gomboknál.
//
// ⚠️ Amit EGYSZERŰSÍTETTÜNK: a mért réteg kilencszeletes, 2 képpontos lágy
// árnyékkal. Itt EGY képpont árnyék-keret áll a keret körül; a lágy átmenet
// két külön sorral (`#D6D6D6`) nem reprodukálható Rectangle-lel anélkül, hogy
// a panel geometriája elmozdulna. A SZÍNEK és a rétegsorrend mértek.
//
// A kiemelt sor geometriája a `.tre`-ből: 2 képpont lekerekítés, és a felirat
// dobozánál **4 képponttal szélesebb mindkét oldalon**.
ComboBox {
    id: control

    //: #741: a mért legördülő-magasság a paneleken 21 képpont; a hívó
    //: felülírhatja, de az alapérték a mérést követi.
    implicitHeight: 21
    topPadding: 0
    bottomPadding: 0
    font.pixelSize: Theme.fontSize - 1

    //: a kiemelt sor a felirat dobozánál ennyivel szélesebb OLDALANKÉNT
    readonly property int highlightOverhang: 4

    popup: Popup {
        objectName: "picasaComboPopup"
        y: control.height
        width: control.width
        implicitHeight: Math.min(
            contentItem.implicitHeight + 4, control.Window.height * 0.6)
        padding: 2

        contentItem: ListView {
            objectName: "picasaComboList"
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            ScrollBar.vertical: PicasaScrollBar {}
        }

        //: A MÉRT panel: SÍK kitöltés + 1 px keret + kívül árnyék-keret, és
        //: alul két sor belső fénykiemelés.
        background: Rectangle {
            objectName: "picasaComboPopupBackground"
            color: Theme.listPanelShadow
            Rectangle {
                objectName: "picasaComboPopupPanel"
                anchors.fill: parent
                anchors.margins: 1
                color: Theme.listPanelBg
                border.color: Theme.listPanelBorder
                border.width: 1
                //: sor 13–14: a belső fénykiemelés ALUL (két képpont)
                Rectangle {
                    anchors.left: parent.left; anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: 1
                    height: 1
                    color: Theme.listPanelInnerLight2
                }
                Rectangle {
                    anchors.left: parent.left; anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 2
                    anchors.leftMargin: 1; anchors.rightMargin: 1
                    height: 1
                    color: Theme.listPanelInnerLight
                }
            }
        }
    }

    delegate: ItemDelegate {
        id: sor
        required property var modelData
        required property int index
        width: control.popup.width - 4
        height: Math.round(Theme.fontSize * 1.7)
        padding: 0
        highlighted: control.highlightedIndex === index

        background: Rectangle {
            //: a kiemelés a FELIRAT dobozánál 4 képponttal szélesebb
            //: oldalanként (a `.tre` szó szerint), és 2 px lekerekítésű
            objectName: "picasaComboRowHighlight"
            anchors.fill: parent
            anchors.leftMargin: 1
            anchors.rightMargin: 1
            radius: 2
            visible: sor.highlighted
            color: Theme.selectionBlue
        }
        contentItem: Text {
            x: sor.control_overhang
            width: parent.width - 2 * sor.control_overhang
            //: A `textRole`-os hívókat is ki kell szolgálni (pl.
            //: `ExportDialogs`: `textRole: "text"`), különben az objektum-modell
            //: sorai „[object Object]"-ként jelennének meg. Ez a Qt saját
            //: ComboBox-delegáltjának mintája.
            text: control.textRole
                  ? (sor.modelData !== undefined && sor.modelData !== null
                     && sor.modelData[control.textRole] !== undefined
                     ? sor.modelData[control.textRole] : "")
                  : (sor.modelData !== undefined && sor.modelData !== null
                     ? String(sor.modelData) : "")
            font.pixelSize: Theme.fontSize - 1
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
            color: sor.highlighted ? Theme.panelSelectionText : Theme.ink
        }
        //: a felirat doboza a kiemelésnél ennyivel szűkebb oldalanként
        readonly property int control_overhang: control.highlightOverhang
    }
}
