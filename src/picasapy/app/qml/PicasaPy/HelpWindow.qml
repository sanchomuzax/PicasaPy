import QtQuick
import QtQuick.Window

// #3544: a súgó KÜLÖN ablakban: a külön ablakos, alkalmazás-modális
// párbeszédek (Nyomtatás, Mappakezelő, Beállítások, …) F1-e és Shift+F1-e
// ezt nyitja.
//
// Miért nem a főablak `HelpDialog`-ja: az a főablak rétegében élő
// `Dialog`. Egy modális külön ablakból nyitva a párbeszéd MÖGÉ kerülne, és a
// modalitás miatt kezelni sem lehetne. Ez az ablak a párbeszéd átmeneti
// gyermeke (`transientParent`, az ablakkezelő fölé rendeli), és alapesetben
// maga is alkalmazás-modális: a legutóbb nyílt modális ablak kapja a
// bemenetet, így a súgó ELÖL áll és kezelhető. A Mappakezelő régi súgóablaka
// (#543) is így él.
//
// #6387: a főablakból nyitott súgó ugyanez az ablak, de a főablak írja felül
// `modality: Qt.NonModal`-ra és a `dialogObjectName`-re. Így a főablak
// kezelhető marad a súgó nyitva tartása mellett.
//
// A tartalom UGYANAZ a `HelpDialog` (fejezetlista, keresés, előzmény), nem
// másolat: az ablakot kitöltve ül benne, és a bezárása az ablakot is elrejti.
Window {
    id: helpWindow
    objectName: "helpWindow"

    //: A belső `HelpDialog` objectName-je. A főablak példánya a `helpDialog`
    //: nevet kapja, hogy a főablak súgóját a meglévő fa-keresések is megtalálják.
    property string dialogObjectName: "helpWindowDialog"
    //: A főablak billentyűlistája a belső párbeszédhez megy (#4639).
    property alias keyboardShortcutTitle: sugo.keyboardShortcutTitle
    property alias keyboardShortcutGroups: sugo.keyboardShortcutGroups

    title: sugo.title
    modality: Qt.ApplicationModal
    width: 900
    height: 620
    color: Theme.canvasBg

    function nyisdMeg(fejezet) {
        helpWindow.visible = true
        sugo.nyisdMeg(fejezet)
        helpWindow.raise()
        helpWindow.requestActivate()
    }

    // az ablak kereszttel bezárva a párbeszéd se maradjon nyitva
    onVisibleChanged: if (!visible && sugo.visible) sugo.close()

    HelpDialog {
        id: sugo
        objectName: helpWindow.dialogObjectName
        modal: false
        width: helpWindow.width
        height: helpWindow.height
        onClosed: helpWindow.visible = false
    }
}
