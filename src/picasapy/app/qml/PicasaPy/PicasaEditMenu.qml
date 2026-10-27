import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

PicasaMenu {
    id: menuEdit
    property var bar: null
    title: qsTr("&Edit")
    // #2151: TUDATOS TÖBBLET — az eredeti Szerkesztés menüjében NINCS
    // visszavonás. A menü ott statikus: 11 tétel + 3 elválasztó, a
    // darabszám konstans, állapotfüggő elágazás nélkül (#1795, a tábla
    // a `docs/specs/picasa-menusor-csoportok.md`-ben). A korábbi
    // indoklás egy erőforrás-kulcsra hivatkozott, amely a binárisban
    // egyáltalán nem fordul elő — sem ASCII-ban, sem UTF-16LE-ben.
    // A menü TELJES kulcskészlete kiolvasható, és pontosan tizenegy:
    // ID_CUT · ID_COPY · ID_PASTE · ID_EDIT_COPYALLEFFECTS ·
    // ID_EDIT_PASTEALLEFFECTS · ID_EDIT_COPYTEXT · ID_EDIT_PASTETEXT ·
    // ID_ALBUM_SELECTALLPICTURES · ID_SELECTSTAR · ID_SELECT_INVERT ·
    // ID_CLEAR_SELECTION. Visszavonás NINCS köztük.
    //
    // Mégis marad, mert ez a két bulk-művelet EGYETLEN belépési pontja
    // (mérve: a jelzéseikre csak ez a fájl és a `Main.qml` köt).
    // Kivéve őket visszavonhatatlanná válnának; áthelyezni pedig nincs
    // hova, mert a szomszédos menük szerkezete is mért.
    // A felirat megnevezi a műveletet, hogy a felhasználó ne vaktában
    // nyomja meg.
    MenuItem {
        objectName: "menuEditUndoPasteAllEffects"
        text: qsTr("Undo Paste All Effects")
        enabled: bar.canUndoPasteAllEffects
        onTriggered: bar.undoPasteAllEffectsRequested()
    }
    MenuItem {
        objectName: "menuEditUndoBatchEdit"
        text: qsTr("Undo Batch Edit")
        enabled: bar.canUndoBatchEdit
        onTriggered: bar.undoBatchEditRequested()
    }
    MenuSeparator {}
    // hiányzott (#324 audit): a szabvány vágólap-műveletek
    // #1526: a Kivágás és a Másolás UGYANAZT az adatot teszi a
    // vágólapra — a binárisban a `Preferred DropEffect` formátum
    // különbözteti meg őket (mozgatás vs. másolás). Linuxon ennek a
    // párja az `x-special/gnome-copied-files` első sora.
    MenuItem {
        objectName: "menuEditCut"
        text: qsTr("Cu&t") + "\tCtrl+X"
        enabled: bar.photoActionsEnabled
        onTriggered: bar.cutFilesRequested()
    }
    MenuItem {
        objectName: "menuEditCopy"
        text: qsTr("&Copy") + "\tCtrl+C"
        enabled: bar.photoActionsEnabled
        onTriggered: bar.copyFilesRequested()
    }
    //: #1526: a Beillesztés a fájl-vágólap MÁSIK fele. A célmappa a
    //: KIVÁLASZTOTT mappa, az ütközéskezelést és a haladásjelzést a
    //: meglévő köteg-út adja (`copyPhotos`/`movePhotos`); a `cut`
    //: jelzésű vágólap-tartalom áthelyez, a `copy` másol.
    //:
    //: A tétel akkor él, ha VAN fájl a vágólapon — üres vágólapnál a
    //: szürke tétel megmagyarázza magát (nincs mit beilleszteni),
    //: szemben egy néma kattintással.
    MenuItem {
        objectName: "menuEditPaste"
        text: qsTr("&Paste") + "\tCtrl+V"
        enabled: bar.clipboardHasFiles
        onTriggered: bar.pasteFilesRequested()
    }
    MenuSeparator {}
    MenuItem {
        objectName: "menuEditCopyEffects"
        text: qsTr("C&opy All Effects")
        enabled: bar.photoActionsEnabled
        onTriggered: bar.copyAllEffectsRequested()
    }
    MenuItem {
        objectName: "menuEditPasteEffects"
        text: qsTr("Paste All E&ffects")
        enabled: bar.photoActionsEnabled && bar.hasAllEffectsClipboard
        onTriggered: bar.pasteAllEffectsRequested()
    }
    MenuSeparator {}
    // #5877: az eredeti Copy/Paste Text a Text eszköz szövegrétegét
    // kezeli (`text=`), nem a kép feliratát. A fájl-vágólap
    // (`Cut`/`Copy`/`Paste`) ettől is külön parancskészlet.
    MenuItem {
        objectName: "menuEditCopyText"
        text: qsTr("Copy Text")
        enabled: bar.photoActionsEnabled && bar.hasSelectedTextLayer
        onTriggered: bar.copyTextRequested()
    }
    MenuItem {
        objectName: "menuEditPasteText"
        text: qsTr("Paste Text")
        //: A Text eszköz a kijelölt réteget is a belső szövegpufferbe
        //: teszi; külön Copy Text után a puffer a másik kijelölt képre
        //: is beilleszthető.
        enabled: bar.photoActionsEnabled
                 && (bar.hasTextLayerClipboard || bar.hasSelectedTextLayer)
        onTriggered: bar.pasteTextRequested()
    }
    MenuSeparator {}
    MenuItem {
        text: qsTr("Select All") + "\tCtrl+A"
        onTriggered: bar.selectAllRequested()
    }
    MenuItem {
        text: qsTr("Select &Starred")
        onTriggered: bar.selectStarredRequested()
    }
    MenuItem {
        objectName: "menuEditInvertSelection"
        text: qsTr("&Invert Selection") + "\tCtrl+I"
        onTriggered: bar.invertSelectionRequested()
    }
    MenuItem {
        text: qsTr("C&lear Selection") + "\tCtrl+D"
        onTriggered: bar.clearSelectionRequested()
    }
}
