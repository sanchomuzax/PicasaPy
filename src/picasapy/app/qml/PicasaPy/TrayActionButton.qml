import QtQuick

// #1345: az alsó műveletsor EGY gombja — ikon fölül, felirat alatta.
//
// Miért nem maradhatott a korábbi „ikon és felirat egymás mellett" alak:
// a mért gomb (`docs/specs/picasa-keptalca.md` 11.) **55 × 36** képpont.
// Vízszintesen egymás mellé az ikon (16) + térköz + a MAGYAR felirat
// („Nyomtatás", „Exportálás") nem fér be — az eredeti éppen ezért rakja
// a feliratot az ikon ALÁ. Így a 36 képpontos magasságba kényelmesen
// belefér az ikon és egy sor szöveg.
//
// A gomb a `TrayActionCell` belső, 55 × 36-os dobozába kerül
// (`anchors.fill: parent`), tehát a méretet NEM itt kötjük meg: egy
// helyen, a cellában él.
PicasaButton {
    id: actionButton

    //: az ikon forrása (`icons/…svg`)
    property url iconSource
    //: a felirat/ikon objectName-je — a meglévő tesztek ezekre hivatkoznak
    property string iconObjectName: ""
    property string labelObjectName: ""
    //: van-e felirat (a felirat nélküli, ikon-only gomboknál nincs)
    readonly property bool labelShown: actionButton.text !== ""

    //: felirat mellett kisebb ikon, felirat nélkül nagyobb — a gomb
    //: doboza mindkét esetben ugyanaz az 55 × 36
    property int iconSize: actionButton.labelShown ? 16 : 24

    // Az 55 képpontból minél több jusson a feliratnak: az öröklött 5-ös
    // oldalmargó itt 10 képpontot venne el. (A függőleges kitöltés a
    // PicasaButton-ban már 0.)
    horizontalPadding: 1

    contentItem: Item {
        Column {
            anchors.centerIn: parent
            spacing: 1

            Image {
                objectName: actionButton.iconObjectName
                anchors.horizontalCenter: parent.horizontalCenter
                // #1188: a `Control` a contentItem geometriáját maga állítja
                // be, a `fillMode` alapja pedig `Image.Stretch` — a négyzetes
                // SVG enélkül a tartalom-dobozra feszülne.
                fillMode: Image.PreserveAspectFit
                width: actionButton.iconSize
                height: actionButton.iconSize
                sourceSize: Qt.size(actionButton.iconSize * 2,
                                    actionButton.iconSize * 2)
                source: actionButton.iconSource
            }

            Text {
                objectName: actionButton.labelObjectName
                visible: actionButton.labelShown
                anchors.horizontalCenter: parent.horizontalCenter
                width: actionButton.availableWidth
                horizontalAlignment: Text.AlignHCenter
                text: actionButton.text
                // #314/#893: rögzített tinta — a gomb-króm mindig világos,
                // a letiltás pedig a PicasaButton alfáján át hat, nem külön
                // szürkítéssel.
                color: Theme.iconInk
                font.pixelSize: 11
                // A magyar feliratok hosszabbak az angolnál: ha nem férnek
                // el, a betű zsugorodik a padlóig — csonkolni SOHA nem
                // szabad, azt semmi nem jelezné (PicasaButton indoklása).
                elide: Text.ElideNone
                maximumLineCount: 1
                fontSizeMode: Text.HorizontalFit
                minimumPixelSize: 7
                minimumPointSize: 7
                clip: true
            }
        }
    }
}
