import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: traySingleActionBar
    objectName: "traySingleActionBar"
    property var trayRoot
    property var trayBar
    //: a `basecontrolset` tetejétől +45; a 14-es infó-csík már
    //: nem része ennek a sávnak, ezért 45 − 14
    y: 45 - 14
    x: trayBar.splitX + 2
    width: Math.max(
        0, trayBar.width - trayBar.rightMargin * 2 - x)
    //: alul −2 a készlet aljától
    height: Math.max(0, trayBar.height - 2 - y)
    //: `decrect(softbevel/flatbevel)` — átlátszatlan, ezért TAKAR
    color: Theme.trayPanelBg
    border.width: 1
    border.color: Theme.trayBorder
    radius: 2
    //: a kimeneti gombsor FÖLÉ kerül (spec 2.4)
    z: 50

    //: #718-minta: az appWindow átmenetileg null lehet.
    //:
    //: A ✕ CSAK ELREJT (spec 2.3: `Property hidetarget`, más
    //: hívás nélkül) — a mód jelzőjéhez NEM nyúl, a projekt lapja
    //: nyitva marad, és a lapsávból tovább lehet visszatérni.
    property bool elrejtve: false
    visible: trayRoot.appWindow
             ? ((trayRoot.appWindow.backToCollagePrompted === true
                || trayRoot.appWindow.backToMovieMakerPrompted === true)
                && !traySingleActionBar.elrejtve)
             : false
    //: újbóli belépéskor megint látszódjon
    Connections {
        //: ⚠️ TERNÁRIUS, nem csupasz hivatkozás (#1260): a
        //: `trayRoot.appWindow` az engine felépítése/leépítése közben
        //: `undefined` lehet, és a Qt ilyenkor „Unable to assign
        //: [undefined] to QObject*" hibát ír — a fixture-életciklus
        //: őre ezt BUKÁSNAK veszi. A `null` érvényes cél (a
        //: kapcsolat egyszerűen nem él), az `undefined` nem.
        target: trayRoot.appWindow ? trayRoot.appWindow : null
        ignoreUnknownSignals: true
        function onBackToCollagePromptedChanged() {
            traySingleActionBar.elrejtve = false
        }
        function onBackToMovieMakerPromptedChanged() {
            traySingleActionBar.elrejtve = false
        }
    }

    // #3605: a három elem egy FIX, 481 × 30-as csoportban ül
    // (`thumbui/single_action_group`, `m_centerXY`), és a csoport a
    // sáv KÖZEPÉN marad — nem a jobb széléhez tapad. A csoport
    // belseje: | 2 | üzenet 335 | 9 | Vissza 109 | 3 | × 18 | 5 |.
    // A két szélső eltolás a jegy 1920 px-es számából: a sáv
    // 702,8 … 1900, a csoport jobb széle 1541,9, a × jobb széle 1537
    // ⇒ 5, a bal a maradék (481 − 474 − 5 = 2).
    Item {
        id: traySingleActionGroup
        objectName: "traySingleActionGroup"
        width: 481
        height: 30
        anchors.centerIn: parent

        Text {
            objectName: "traySingleActionMessage"
            //: MÉRT: 335 × 26, JOBBRA igazítva (`textalign right`)
            width: 335
            height: 26
            anchors.verticalCenter: parent.verticalCenter
            //: `m_offsetL` a csoportban
            anchors.left: parent.left
            anchors.leftMargin: 2
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            wrapMode: Text.WordWrap
            elide: Text.ElideRight
            color: Theme.ink
            font.pixelSize: Theme.fontSize
            //: a `thumbui/single_action_message` HIVATALOS magyar
            //: fordítása (`referencia/panel-feliratok-hu.tsv:5187`)
            text: qsTr("Select items to add to your project's clips tray, then press the \"Back\" button to return to your project")
        }

        PicasaButton {
            id: traySingleActionReturn
            objectName: "traySingleActionReturn"
            //: MÉRT: 109 × 43
            width: 109
            height: 43
            anchors.verticalCenter: parent.verticalCenter
            //: `m_offsetR`; MÉRT rés a × előtt: 3 (az üzenet után 9 —
            //: 2 + 335 + 9 + 109 + 3 + 18 + 5 = 481)
            anchors.right: traySingleActionClose.left
            anchors.rightMargin: 3
            accent: Theme.picasaGreen
            // #2438: az eredetiben ez a `thumbui/single_action_return`, a
            // 13 pulzáló elem egyike — a klip-gyűjtő módban EZ a fő
            // cselekvés, tehát ez mutatja meg, hol lehet visszalépni.
            throbbing: true
            text: trayRoot.appWindow
                  && trayRoot.appWindow.backToMovieMakerPrompted === true
                ? qsTr("Back to Movie Maker")
                : qsTr("Back to Collage")
            ToolTip.text: qsTr("Go back to what you were editing")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: {
                if (trayRoot.appWindow
                        && trayRoot.appWindow.backToMovieMakerPrompted === true)
                    trayRoot.backToMovieMakerRequested()
                else
                    trayRoot.backToCollageRequested()
            }
        }

        PicasaButton {
            id: traySingleActionClose
            objectName: "traySingleActionClose"
            //: MÉRT: 18 × 18
            width: 18
            height: 18
            anchors.verticalCenter: parent.verticalCenter
            //: `m_offsetR` a csoportban
            anchors.right: parent.right
            anchors.rightMargin: 5
            text: "\u2715"
            ToolTip.text: qsTr("Cancel \"Get more\"")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            //: CSAK elrejt — a módból NEM lép ki (spec 2.3)
            onClicked: traySingleActionBar.elrejtve = true
        }
    }
}
