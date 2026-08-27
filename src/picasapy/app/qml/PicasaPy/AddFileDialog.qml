import QtQuick
import QtQuick.Dialogs

// #1633: Fájl ▸ Fájl felvétele a Picasába… (Ctrl+O) — `ID_FILE_OPEN`,
// `cmd 0xe101` (`docs/specs/picasa-menu-parancsok.csv` 39. sor). A parancs
// az eredetiben a SZABVÁNYOS MFC „Megnyitás" azonosítót (`ID_FILE_OPEN`,
// `<afxres.h>` 0xE101) viseli — a Picasa ezt a szerepet a könyvtárhoz
// adásra használta fel: natív fájlválasztóval kép-/videófájlokat lehet
// kijelölni.
//
// A PicasaPy adatmodellje (`library_controller.py`) mappaszinten tart
// nyilván — nincs önálló, mappától független fájl —, ezért a kijelölt
// fájl(ok) SZÜLŐMAPPÁJA kerül a könyvtárba, ugyanazon a meglévő, azonnal
// ható belépési ponton (`controller.addWatchedFolder`), amit végső soron
// a „Mappa hozzáadása a Picasához…" (`ID_TOOLS_INCLUDEEXCLUDEFOLDERS`,
// `folderManagerRequested` → `FolderManagerDialog`) is elsüt — NEM másolt
// logika. ⚠️ A két menüpont EBBEN különbözik: ez a tétel egyetlen natív
// fájlválasztó, tranzakciós OK/Mégse nélkül, azonnali hatással.
//
// ⚠️ NYITOTT KÉRDÉS (nincs helyi bizonyíték rá): az eredeti Picasa az
// így felvett mappát TARTÓSAN figyeli-e, vagy csak egyszer szkenneli be
// (`controller.scanFolderOnce` lenne az analógja, ld.
// `FolderManagerDialog.qml` „Egyszeri keresés" rádiója). A tartós
// figyelés mellett döntöttünk, mert ez szimmetrikus a „Mappa hozzáadása a
// Picasához…" viselkedésével, és ez a kevésbé meglepő alapértelmezés —
// ld. #1633 jelentés.
FileDialog {
    id: addFileDialog
    objectName: "addFileDialog"
    title: qsTr("Add File to Picasa...")
    fileMode: FileDialog.OpenFiles
    // a felirat a meglévő ImportSourceDialog szűrő-szókészletét használja
    // (`ImportSourceDialog.qml` — „Picture and Movie Files" / „All Files"),
    // hogy ne kelljen új fordítást felvenni
    nameFilters: [
        qsTr("Picture and Movie Files") + " ("
            + "*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.gif *.psd *.tga "
            + "*.3g2 *.3gp *.asf *.avi *.divx *.m2t *.m2ts *.m4v *.mkv "
            + "*.mmv *.mod *.mov *.mp4 *.mpg *.mts *.tod *.wmv)",
        qsTr("All Files") + " (*)"
    ]
    onAccepted: addFileDialog.addSelectedFiles(addFileDialog.selectedFiles)

    // #1633: minden kijelölt fájl szülőmappája kerül a könyvtárba — a
    // duplikáció-védelem VÉGSŐ soron az `addWatchedFolder`-ben van
    // (`path_key`-alapú), a halmaz itt csak a fölösleges, ismételt
    // hívásokat spórolja meg egy többfájlos, azonos mappás kijelölésnél.
    // Külön függvényként (nem az `onAccepted`-ben) azért, hogy a natív
    // fájlválasztó megkerülésével, közvetlenül is tesztelhető legyen
    // (ld. `tests/app/qml_functional/test_addfile_menupont_1633.py`).
    function addSelectedFiles(fileUrls) {
        var mappak = {}
        for (var i = 0; i < fileUrls.length; i++) {
            var fajlUrl = fileUrls[i].toString()
            var perjel = fajlUrl.lastIndexOf("/")
            if (perjel < 0) continue
            var mappaUrl = fajlUrl.substring(0, perjel)
            if (mappak[mappaUrl]) continue
            mappak[mappaUrl] = true
            controller.addWatchedFolder(mappaUrl)
        }
    }
}
