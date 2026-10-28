import QtQuick

Text {
    objectName: "gridEmptyText"
    required property var feed
    anchors.centerIn: feed
    //: #3751: mentés-üzemmódban, ha nincs mit mutatni, a `Text2`
    //: kontextus-szöveg jön a `Text1` („No photos found") helyett —
    //: ugyanaz, amit a `FolderPane.mentesAllapotSzoveg` is használ.
    //: `thumbui_text.tre` Text1 — az eredeti felirata
    text: feed.mentesSzuroAktiv
          ? qsTr("All Files are backed up in this set")
          : qsTr("No photos found")
    font.pointSize: 18
    color: Theme.textGray
    // Munka közben a rács is üres, de attól még nem igaz, hogy nincs
    // kép — a mondat ilyenkor hazudna (#1798 osztálya: hazudó állapot).
    // #3751: mentés-üzemmódban a mondat csak kiválasztott, kész
    // számítású készletre igaz — készlet nélkül és a `Számítás…` alatt
    // nem mondhatja, hogy mindenről van másolat.
    visible: feed.count === 0
             && !(feed.ctl && feed.ctl.isWorking !== undefined
                  ? feed.ctl.isWorking : false)
             && (!feed.mentesSzuroAktiv
                 || (feed.mentesVanKeszlet && !feed.mentesToltodnek))
}
