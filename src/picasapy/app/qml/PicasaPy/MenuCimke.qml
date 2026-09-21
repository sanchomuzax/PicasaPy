import QtQuick
import QtQuick.Controls.impl

// #3455: a menütétel felirata és gyorsbillentyűje KÉT oszlopban.
//
// A feliratok `qsTr("…") + "\tCtrl+S"` alakban hordozzák a gyorsbillentyűt.
// Egy címke a tabulátort szövegként rajzolta: a gyorsbillentyű a felirat
// hosszától függő helyre került, a hosszú tételeknél ki is lógott a menüből.
// Az eredeti Picasa (Windows-menü) a gyorsbillentyűket közös, jobbra
// igazított oszlopba teszi — itt a tabulátor utáni rész a tétel jobb
// szélére igazodik, és a tétel szélessége a kettő együttes hosszát kéri,
// így a `PicasaMenu` mérése (#1740) a gyorsbillentyűt is beszámítja.
//
// A felirat-rész `IconLabel` (#757: a `&` mnemonik aláhúzás, nem betű).
Item {
    id: cimke

    property string text
    property font font
    property color color
    property real leftPadding: 0
    property real rightPadding: 0

    readonly property int _tab: cimke.text.indexOf("\t")
    readonly property string felirat: _tab < 0 ? cimke.text : cimke.text.substring(0, _tab)
    readonly property string gyorsbillentyu: _tab < 0 ? "" : cimke.text.substring(_tab + 1)
    //: a felirat és a gyorsbillentyű közti legkisebb köz
    readonly property real koz: gyorsbillentyu === "" ? 0 : 24

    implicitWidth: leftPadding + feliratResz.implicitWidth + koz
        + (gyorsbillentyu === "" ? 0 : gyorsResz.implicitWidth) + rightPadding
    implicitHeight: Math.max(feliratResz.implicitHeight, gyorsResz.implicitHeight)

    IconLabel {
        id: feliratResz
        objectName: "menuTetelFelirat"
        x: cimke.leftPadding
        width: Math.max(0, cimke.width - cimke.leftPadding - cimke.rightPadding
            - (cimke.gyorsbillentyu === "" ? 0 : gyorsResz.implicitWidth + cimke.koz))
        anchors.verticalCenter: parent.verticalCenter
        text: cimke.felirat
        font: cimke.font
        color: cimke.color
        alignment: Qt.AlignLeft | Qt.AlignVCenter
    }

    Text {
        id: gyorsResz
        objectName: "menuTetelGyorsbillentyu"
        visible: cimke.gyorsbillentyu !== ""
        anchors.right: parent.right
        anchors.rightMargin: cimke.rightPadding
        anchors.verticalCenter: parent.verticalCenter
        text: cimke.gyorsbillentyu
        font: cimke.font
        color: cimke.color
    }
}
