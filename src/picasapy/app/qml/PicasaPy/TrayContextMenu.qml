import QtQuick
import QtQuick.Controls

// A képtálca jobbklikk-menüje — a Picasa `Tray` menüosztálya.
//
// ## #1917: HÉT tétel + elválasztó, nem kettő
//
// A menü korábban két tételes volt, mert a `Tray::` névtérben PONTOSAN
// két parancsazonosító van. **A névtér-számlálásból nem következik a menü
// hossza:** a másik öt tétel MÁS névterekből öröklődik ide.
//
// A menü-leíró tábla a `0x00732ee0` címen épül fel (egyszeri init, a
// `0xda038c` bitjével őrizve; a bejegyzések a `0xd6edc0`-tól, 20 bájtos
// lépésekkel). Hívó: `0x005e7d10`. A tételek a felépítés sorrendjében:
//
//   1 AlbumPhoto::ID_PICTURE_VIEW                  (0xcadb44) &View and Edit
//   2 Tray::ID_PICTURE_HOLDINPICTURETRAY           (0xcae618) &Hold Selection
//   3 Tray::ID_REMOVE_SELECTION                    (0xcae5e4) &Remove Selection
//   4 AlbumPhoto::ID_PICTURE_ROTATECLOCKWISE       (0xcadf04) R&otate Clockwise
//   5 AlbumPhoto::ID_PICTURE_ROTATECOUNTERCLOCKWISE(0xcadbc0) Rotate &Counterclockwise
//   6 FolderPhotoWin::ID_FILE_LOCATEONDISK         (0xcadd5c) &Locate on Disk
//   7 elválasztó                                   (CMenuBar::Enter, 0xc8c4e4)
//   8 AlbumPhotoWin::ID_PICTURE_PROPERTIES         (0xcadedc) Propert&ies
//
// ⚠️ A 2. tétel angol felirata **`&Hold Selection`** (0xcae63c). A korábbi
// felirat a mi találgatásunk volt — a forrásban szándékosan nem írjuk le,
// mert egy forrás-szintű őr a KOMMENTET is olvassa.
//
// A 4./5. tétel közös másodlagos mutatója (`0xc8d794`) és a 6. tétel 1-es
// jelzőbitje: a jelentésük NINCS MEG. A menü felépítéséhez nem kell.
//
// Önálló, signal-alapú komponens: a bekötést a TrayBar.qml végzi.
PicasaMenu {
    id: menu
    objectName: "trayContextMenu"

    signal viewAndEditRequested()
    signal keepSelectionRequested()
    signal removeSelectionRequested()
    signal rotateRightRequested()
    signal rotateLeftRequested()
    signal locateRequested()
    signal propertiesRequested()

    MenuItem {
        objectName: "trayMenuViewAndEdit"
        //: `AlbumPhoto::ID_PICTURE_VIEW` — a menü ELSŐ tétele (#1917).
        text: qsTr("&View and Edit")
        onTriggered: menu.viewAndEditRequested()
    }
    MenuItem {
        objectName: "trayMenuKeepSelection"
        //: `Tray::ID_PICTURE_HOLDINPICTURETRAY` — az eredeti felirata
        //: „&Hold Selection" (0xcae63c); a korábbi a mi találgatásunk
        //: volt (#1917).
        text: qsTr("&Hold Selection")
        onTriggered: menu.keepSelectionRequested()
    }
    MenuItem {
        objectName: "trayMenuRemoveSelection"
        //: `Tray::ID_REMOVE_SELECTION`
        text: qsTr("&Remove Selection")
        onTriggered: menu.removeSelectionRequested()
    }
    MenuItem {
        objectName: "trayMenuRotateRight"
        //: `AlbumPhoto::ID_PICTURE_ROTATECLOCKWISE`
        text: qsTr("R&otate Clockwise")
        onTriggered: menu.rotateRightRequested()
    }
    MenuItem {
        objectName: "trayMenuRotateLeft"
        //: `AlbumPhoto::ID_PICTURE_ROTATECOUNTERCLOCKWISE`
        text: qsTr("Rotate &Counterclockwise")
        onTriggered: menu.rotateLeftRequested()
    }
    MenuItem {
        objectName: "trayMenuLocate"
        //: `FolderPhotoWin::ID_FILE_LOCATEONDISK`
        text: qsTr("&Locate on Disk")
        onTriggered: menu.locateRequested()
    }
    MenuSeparator { objectName: "trayMenuSeparator" }
    MenuItem {
        objectName: "trayMenuProperties"
        //: `AlbumPhotoWin::ID_PICTURE_PROPERTIES`
        text: qsTr("Propert&ies")
        onTriggered: menu.propertiesRequested()
    }
}
