import QtQuick
import QtQuick.Dialogs

// #1654/#2553: a tesztüzem naplójának mentés-párbeszéde.
//
// ⚠️ #2553: ez már NEM tartalék, hanem AZ út. A #1654 egy beégetett
// mappába másolt (`/mnt/nas`, Windowson `//DS215j/lemez`), és a párbeszéd
// csak akkor jött elő, ha az nem volt elérhető. Az a hely egyetlen gépre
// volt szabva, és mérve (2026-09-06) a fejlesztői gépről nem is látszott:
// a napló kiment, de senki nem érte el. Mostantól a `Súgó ▸ Napló
// elküldése` MINDIG ezt nyitja, a felhasználó választ, és a választása
// megmarad a következő alkalomra.
//
// ⚠️ Semmilyen hálózati feltöltés, külső szolgáltatás és hitelesítés nincs
// az úton — a napló mindkét ágon egyszerű fájlírás.
FileDialog {
    id: tesztuzemNaploDialog
    objectName: "tesztuzemNaploDialog"
    title: qsTr("Save Log As...")
    fileMode: FileDialog.SaveFile
    defaultSuffix: "txt"
    nameFilters: [qsTr("Text Files") + " (*.txt)", qsTr("All Files") + " (*)"]
    onAccepted: tesztuzemNaploDialog.mentsdIde(
        tesztuzemNaploDialog.selectedFile.toString())

    // Külön függvényként (nem az `onAccepted`-ben), hogy a natív
    // fájlválasztó megkerülésével, közvetlenül is tesztelhető legyen —
    // ugyanaz a minta, mint az `AddFileDialog.qml` `addSelectedFiles()`-e
    // (#1633): offscreen platformon a rendszerválasztó nem szimulálható.
    function mentsdIde(fajlUrl) {
        return controller.tesztuzemNaploMentese(fajlUrl)
    }

    // #2553: a vezérlő adja meg, hol nyíljon és mi legyen a javasolt név.
    // Külön függvény, ugyanazon az okon, mint a `mentsdIde`: a natív
    // párbeszéd offscreen platformon nem szimulálható, a bekötést viszont
    // így az őr-teszt közvetlenül hívhatja.
    function nyisdMeg(mappaUrl, javasoltNev) {
        if (mappaUrl)
            tesztuzemNaploDialog.currentFolder = mappaUrl
        if (javasoltNev)
            tesztuzemNaploDialog.selectedFile = mappaUrl + "/" + javasoltNev
        tesztuzemNaploDialog.open()
    }
}
