import QtQuick
import QtQuick.Window

// #3544: az F1 és a Shift+F1 egy KÜLÖN ablakban nyíló párbeszédben.
//
// A főablak súgó-gyorsbillentyűi (`Main.qml`) egy alkalmazás-modális külön
// ablakban nem élnek, a főablak súgója pedig a párbeszéd mögé kerülne. Ez az
// elem a párbeszéd ablakába ül (bárhová a fájában), és ABLAKSZINTŰ
// gyorsbillentyűvel a párbeszéd fölött nyitja a súgót (`HelpWindow.qml`):
//
//     WindowHelp { tema: printWindow.helpTopic }
//
// A súgóablak halasztva épül (#1720 mintája): csak az első megnyomásra.
Item {
    id: root

    //: A Shift+F1 fejezete — a párbeszéd `helpTopic`-ja.
    property string tema: ""

    //: A párbeszéd ablaka: ENNEK a gyermeke lesz a súgóablak.
    readonly property var _ablak: root.Window.window

    //: CSAK látható párbeszédben él: a Qt az ablakszintű gyorsbillentyűt a
    //: rokon (tranziens) ablakokban is illeszti, és egy rejtett párbeszéd
    //: F1-e a főablakéval kétértelmű lenne — MEGMÉRVE egyik sem sülne el.
    readonly property bool _el: root._ablak !== null && root._ablak !== undefined
                                && root._ablak.visible

    function nyisdASugot(fejezet) {
        sugoAblak.active = true
        sugoAblak.item.nyisdMeg(fejezet)
    }

    //: Az F1 az eredeti gyorsbillentyűje (tartalomjegyzék), a Shift+F1 a
    //: MIÉNK (a párbeszéd fejezete) — ugyanaz a kiosztás, mint a főablakban.
    Shortcut {
        sequence: "F1"
        context: Qt.WindowShortcut
        enabled: root._el
        onActivated: root.nyisdASugot("")
    }
    Shortcut {
        sequence: "Shift+F1"
        context: Qt.WindowShortcut
        enabled: root._el
        onActivated: root.nyisdASugot(root.tema)
    }

    Loader {
        id: sugoAblak
        active: false
        asynchronous: false
        sourceComponent: Component {
            HelpWindow { transientParent: root._ablak }
        }
    }
}
