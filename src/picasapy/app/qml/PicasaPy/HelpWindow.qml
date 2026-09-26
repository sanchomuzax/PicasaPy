import QtQuick
import QtQuick.Window

// #3544: a súgó KÜLÖN ablakban — a külön ablakos, alkalmazás-modális
// párbeszédek (Nyomtatás, Mappakezelő, Beállítások, …) F1-e és Shift+F1-e
// ezt nyitja.
//
// **Miért nem a főablak `HelpDialog`-ja.** Az a főablak rétegében élő
// `Dialog`: egy modális külön ablakból nyitva a párbeszéd MÖGÉ kerülne, és a
// modalitás miatt kezelni sem lehetne. Ez az ablak a párbeszéd átmeneti
// gyermeke (`transientParent`, az ablakkezelő fölé rendeli), és maga is
// alkalmazás-modális: a legutóbb nyílt modális ablak kapja a bemenetet, így a
// súgó ELÖL áll és kezelhető — a Mappakezelő régi súgóablaka (#543) is így él.
//
// A tartalom UGYANAZ a `HelpDialog` (fejezetlista, keresés, előzmény), nem
// másolat: az ablakot kitöltve ül benne, és a bezárása az ablakot is elrejti.
Window {
    id: helpWindow
    objectName: "helpWindow"

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
        objectName: "helpWindowDialog"
        modal: false
        width: helpWindow.width
        height: helpWindow.height
        onClosed: helpWindow.visible = false
    }
}
