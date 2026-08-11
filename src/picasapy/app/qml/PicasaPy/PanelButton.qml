import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Picasa-stílusú panel-gomb a szerkesztőben (#318/#338/#450): opcionális
// effekt-bélyegképpel, tördelt (sosem vágott) felirattal, opcionális
// buboréksúgóval.
//
// #496: kiemelve az EditorPanel.qml-ből (ld. ott a `ToolTile` megjegyzését).
Rectangle {
    id: pbtn
    property string label: ""
    property bool buttonEnabled: true
    // "" = sima gomb (korábbi kinézet); egyébként image://effectthumb/…
    property string thumbSource: ""
    // #450: opcionális hover-buboréksúgó (pl. "Copy Caption" gomb) —
    // üres stringnél nincs tooltip (a legtöbb PanelButton-hívó)
    property string tooltip: ""
    signal buttonClicked()
    Layout.fillWidth: true
    // #318: a felirat teljesen olvasható kell legyen. Bélyegképes
    // gombnál a kép + felirat együttes magassága számít, sima gombnál
    // (a régi mintát megtartva) csak a feliraté, 24px alsó korláttal.
    Layout.preferredHeight: pbtn.thumbSource !== ""
        ? pbtnThumbBox.height + pbtnLabel.implicitHeight + 12
        : Math.max(24, pbtnLabel.implicitHeight + 10)
    radius: 3
    border.width: 1
    border.color: Theme.chromeBorder
    // pbtn.enabled = buttonEnabled ÉS az öröklött (panel-)enabled (#103)
    enabled: pbtn.buttonEnabled
    // #314: fix világos hexák ("#fdfdfd"/"#d8d8d8"/"#ececec") helyett
    // téma-tokenekből — sötét témában a gomb is sötétedik, így a
    // (szintén témafüggő) Theme.textDark felirat olvasható marad rajta.
    color: !pbtn.enabled ? Theme.chromeBg
           : (pbtnMouse.pressed ? Qt.darker(Theme.buttonBg, 1.15) : Theme.buttonBg)

    // #338: a bélyegkép-terület — csak akkor foglal helyet, ha van
    // thumbSource. A KÉSZ bélyegképig (Image.status !== Ready) a
    // helyőrző-keret mutatja, hogy a gomb SOHA ne legyen üres/villogó.
    Item {
        id: pbtnThumbBox
        visible: pbtn.thumbSource !== ""
        anchors.top: parent.top
        anchors.topMargin: 5
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width - 10
        height: pbtn.thumbSource !== "" ? 56 : 0

        Rectangle {
            // helyőrző, amíg a bélyegkép még nem érkezett meg
            anchors.fill: parent
            radius: 2
            color: Theme.chromeBg
            border.width: 1
            border.color: Theme.chromeBorder
            visible: pbtnThumbImg.status !== Image.Ready
        }
        Image {
            id: pbtnThumbImg
            objectName: pbtn.objectName ? pbtn.objectName + "Thumb" : ""
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            source: pbtn.thumbSource
            smooth: true
            // amíg nem kész (Loading/Null/Error), nem rajzol semmit —
            // a fenti helyőrző-Rectangle látszik helyette, nem üres folt
            visible: status === Image.Ready
        }
    }
    Text {
        id: pbtnLabel
        // a hívó objectName-jéből képzett saját objectName (pl.
        // "effectGrain2Label") — a tesztek ezen ellenőrzik a
        // tördelést/nem-vágást (#318), a histogramTitle mintája (#235).
        objectName: pbtn.objectName ? pbtn.objectName + "Label" : ""
        // #305/#338 mintája: SOHA ne kössünk anchort feltételesen
        // `undefined`-ra (a QML-figyelmeztetés-őr ezt buktatná) — a
        // pbtnThumbBox magassága 0, ha nincs thumbSource, így ez az
        // egyetlen, mindig érvényes anchor-készlet mindkét esetben jó
        // (sima gombnál csak néhány px-szel tér el a régi centerIn-től,
        // ami a szűk, tömören méretezett gombokon nem látszik).
        anchors.top: pbtnThumbBox.bottom
        anchors.topMargin: pbtn.thumbSource !== "" ? 4 : 3
        anchors.horizontalCenter: parent.horizontalCenter
        text: pbtn.label
        font.pixelSize: Theme.fontSize
        color: pbtn.enabled ? Theme.textDark : Theme.textGray
        // #318: elide helyett tördelés — a panel szélessége nem nőhet,
        // de a szöveg soha nem vágódik "…"-ra; a Qt WordWrap szó-
        // határon tör, hosszú, tördelhetetlen szónál karakterhatáron.
        wrapMode: Text.WordWrap
        width: parent.width - 8
        horizontalAlignment: Text.AlignHCenter
    }
    MouseArea {
        id: pbtnMouse
        anchors.fill: parent
        hoverEnabled: pbtn.tooltip.length > 0
        onClicked: pbtn.buttonClicked()
    }
    ToolTip.text: pbtn.tooltip
    ToolTip.visible: pbtn.tooltip.length > 0 && pbtnMouse.containsMouse
    ToolTip.delay: 400
}
