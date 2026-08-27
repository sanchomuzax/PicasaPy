import QtQuick
import QtQuick.Dialogs

// #1654: a tesztüzem naplójának „Mentés másként…" TARTALÉKA.
//
// Az alapeset az egykattintásos átadás: a `Súgó ▸ Napló elküldése` a
// naplót a NAS közös mappájába (`/mnt/nas`, Windowson
// `//192.168.50.187/lemez`) másolja, a rögzített `picasapy-naplo/`
// almappába. Ha a megosztás nincs csatlakoztatva, a felhasználó nem
// maradhat üres kézzel: a vezérlő `tesztuzemMentesMaskentKert` jelzése
// nyitja ezt a párbeszédet, és a napló oda kerül, ahova a felhasználó
// mutat.
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
}
