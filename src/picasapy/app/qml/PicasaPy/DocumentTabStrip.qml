import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Dokumentum-fülsáv (#944, a Kollázs-panel 3/8. szelete).
//
// A lelet (`docs/specs/kollazs-panel-ui-spec.md` 3.1–3.3): az eredeti
// Picasában a kollázs NEM párbeszédablak, hanem SAJÁT LAP a fülsávban
// (`panelroot/collagetab` 125 × 21, jobb szélén ✕), a „Könyvtár” lapja
// pedig mellette marad, a tartalmával együtt.
//
// Három szerződés, amit ez a komponens tart:
//
//  1. **Regresszió-mentesség.** Nyitott projekt-lap nélkül a sáv nem csak
//     „nem látszik”, hanem NEM IS FOGLAL HELYET (`implicitHeight: 0`), így a
//     mai felület egyetlen képponttal sem csúszik el.
//  2. **Állapotmegőrzés.** A sáv csak az `activeTabId`-t billenti át és
//     `tabActivated`-et jelez — nem semmisít meg semmit. A gazda ebből
//     `visible`-t köt (nem `Loader.active`-ot), így a könyvtár-rács
//     kijelölése és görgetési helye megmarad.
//  3. **Egy bezárási út.** Az ✕ és az `Esc` egyaránt a `requestClose()`-ba
//     fut be; a mentetlen módosítás háromgombos kérdése is ott dől el, tehát
//     a két kapu nem tud szétcsúszni.
//
// A gazda (Main.qml) bekötése az INTEGRÁTOR dolga — ez a fájl szándékosan
// nem ismer sem controllert, sem konkrét lap-típust.
Item {
    id: root
    objectName: "documentTabStrip"

    // A MÉRT sávmagasság: `design-guide.md` „felső fül-sáv 29 px”.
    readonly property int savMagassag: 29

    //: a rögzített, nem zárható könyvtár-fül azonosítója
    readonly property string libraryTabId: "library"
    //: a rögzített fül felirata
    property string libraryTitle: qsTr("Library")

    //: a nyitott projekt-lapok: `[{ id, title, modified }]`
    property var projectTabs: []
    //: melyik lap aktív — a gazda ebből köti a tartalom láthatóságát
    property string activeTabId: root.libraryTabId

    //: a mentetlen módosításról szóló kérdés szövege (hivatalos fordítással)
    property string unsavedMessage: qsTr(
        "The current collage contains unsaved changes.\n\n" +
        "Would you like to save or discard them before closing the tab? " +
        "(Note: drafts are saved to the Collages album.)\n\n" +
        "Click Cancel to leave the tab open.")

    readonly property bool hasProjectTabs: root.projectTabs.length > 0
    readonly property bool libraryActive: root.activeTabId === root.libraryTabId

    // A sáv üresen SEM látszik, SEM helyet nem foglal. A magasságot azért is
    // kimondjuk (nem csak a `visible`-t), mert a `visible` öröklődik a
    // szülőtől: viselkedést kell tesztelni, nem láthatóságot.
    visible: root.hasProjectTabs
    implicitHeight: root.hasProjectTabs ? root.savMagassag : 0
    height: root.implicitHeight

    //: a felhasználó másik lapra váltott
    signal tabActivated(string tabId)
    //: a lap bezárása eldőlt — `saveDraft` esetén piszkozatként mentendő
    signal closeAccepted(string tabId, bool saveDraft)

    /** A megadott azonosítójú projekt-lap leírója, vagy `null`. */
    function tabAt(tabId) {
        var tabs = root.projectTabs
        for (var i = 0; i < tabs.length; ++i) {
            if (tabs[i] && tabs[i].id === tabId)
                return tabs[i]
        }
        return null
    }

    /** Fülváltás. Ugyanarra a fülre kattintva NEM ad jelzést — a gazdának
        nincs miért újraépítenie semmit. */
    function activateTab(tabId) {
        if (root.activeTabId === tabId)
            return
        root.activeTabId = tabId
        root.tabActivated(tabId)
    }

    /** AZ EGYETLEN bezárási út — ide fut be az ✕ és az `Esc` is. */
    function requestClose(tabId) {
        var tab = root.tabAt(tabId)
        if (tab === null)
            return
        if (tab.modified === true) {
            closeConfirm.pendingTabId = tabId
            closeConfirm.open()
            return
        }
        root.closeAccepted(tabId, false)
    }

    /** Az aktív lap bezárása (`Esc`). A könyvtár füle nem zárható. */
    function requestCloseActive() {
        if (!root.libraryActive)
            root.requestClose(root.activeTabId)
    }

    // Ha a gazda kivette a listából az épp aktív lapot, ne maradjon
    // „sehol” az alkalmazás: essünk vissza a könyvtárra.
    onProjectTabsChanged: {
        if (!root.libraryActive && root.tabAt(root.activeTabId) === null)
            root.activateTab(root.libraryTabId)
    }

    /** Lapváltás a soron KÖRBE (#2170).

        Az eredeti kezelője (`0x005b2390`) a `0x005b22b0(panel, ±1)`
        léptetőt hívja mind a négy billentyűre. A „sor" nálunk a KÖNYVTÁR
        fülét is tartalmazza — a felhasználó számára az is egy fül —, ezért
        a léptetés azon is átmegy.

        `irany`: +1 a következő, −1 az előző lap felé.
    */
    function lepjAKovetkezoLapra(irany) {
        var sor = [root.libraryTabId]
        var tabs = root.projectTabs
        for (var i = 0; i < tabs.length; ++i) {
            if (tabs[i] && tabs[i].id !== undefined)
                sor.push(tabs[i].id)
        }
        if (sor.length < 2)
            return
        var most = sor.indexOf(root.activeTabId)
        if (most < 0)
            most = 0
        //: a `% sor.length` a KÖRBEJÁRÁS: az utolsó után a könyvtár jön
        var cel = (most + irany + sor.length) % sor.length
        root.activateTab(sor[cel])
    }

    // `Property escapekey 1` (3.3): az Esc a LAPOT zárja. Csak akkor él, ha
    // tényleg van zárható, aktív lap — és nem akkor, amikor már a kérdés áll
    // a képernyőn (ott az Esc a Mégse útja).
    Shortcut {
        sequence: "Esc"
        enabled: root.hasProjectTabs && !root.libraryActive
                 && !closeConfirm.visible
        onActivated: root.requestCloseActive()
    }

    // #2170: a négy MÉRT projektlap-billentyű. Az eredeti kezelője
    // (`0x005b2390`) `Ctrl`-t követel; a `Ctrl+W` a bezárás
    // (`0x005b31a0`), a másik három a ±1-es léptető (`0x005b22b0`).
    //
    // ⚠️ A `Ctrl+W` a MEGLÉVŐ bezárás-úton megy (`requestCloseActive`),
    // nem külön ágon: a piszkos lap kérdését így nem kerüli meg — ugyanaz
    // a megfontolás, mint az `Esc`-nél (a fájl 3. invariánsa).
    Shortcut {
        sequence: "Ctrl+W"
        enabled: root.hasProjectTabs && !root.libraryActive
                 && !closeConfirm.visible
        onActivated: root.requestCloseActive()
    }
    Shortcut {
        sequence: "Ctrl+Tab"
        enabled: root.hasProjectTabs && !closeConfirm.visible
        onActivated: root.lepjAKovetkezoLapra(1)
    }
    Shortcut {
        sequence: "Ctrl+Shift+Tab"
        enabled: root.hasProjectTabs && !closeConfirm.visible
        onActivated: root.lepjAKovetkezoLapra(-1)
    }
    Shortcut {
        sequence: "Ctrl+Right"
        enabled: root.hasProjectTabs && !closeConfirm.visible
        onActivated: root.lepjAKovetkezoLapra(1)
    }
    Shortcut {
        sequence: "Ctrl+Left"
        enabled: root.hasProjectTabs && !closeConfirm.visible
        onActivated: root.lepjAKovetkezoLapra(-1)
    }

    Rectangle {
        anchors.fill: parent
        color: Theme.chromeBg
        clip: true

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            color: Theme.chromeBorder
        }
    }

    // A fülek ALULRA igazodnak a sávban (az eredeti 8 képpontos felső hézag).
    Row {
        objectName: "documentTabRow"
        anchors.left: parent.left
        anchors.leftMargin: 6
        anchors.bottom: parent.bottom
        spacing: 2

        DocumentTab {
            namePrefix: "documentTabLibrary"
            title: root.libraryTitle
            active: root.libraryActive
            closable: false
            onActivateRequested: root.activateTab(root.libraryTabId)
        }

        Repeater {
            model: root.projectTabs

            DocumentTab {
                required property int index
                required property var modelData

                namePrefix: "documentTab" + index
                title: modelData && modelData.title !== undefined
                       ? modelData.title : ""
                modified: modelData ? modelData.modified === true : false
                active: modelData ? root.activeTabId === modelData.id : false
                closable: true
                onActivateRequested: root.activateTab(modelData.id)
                onCloseRequested: root.requestClose(modelData.id)
            }
        }
    }

    // Háromgombos kérdés (`CCollageUI::ConfirmCloseTitle`, 3.3). SZÁNDÉKOSAN
    // nem a `ConfirmDialog`: annak van „Ne kérdezze újra” jelölője, mentetlen
    // módosítást pedig soha nem szabad némán eldobni. A harmadik gomb sem
    // dísz — az eredeti szöveg maga mondja ki, hogy a Mégse nyitva hagyja a
    // lapot (`docs/specs/picasa-bezaras-es-kilepes.md` 2. szint).
    Dialog {
        id: closeConfirm
        objectName: "documentTabCloseConfirm"

        //: melyik lap bezárása vár válaszra
        property string pendingTabId: ""

        modal: true
        title: qsTr("Confirm…")
        closePolicy: Popup.CloseOnEscape
        anchors.centerIn: parent ? Overlay.overlay : undefined

        /** A kérdés megválaszolása — a lap bezárul, mentéssel vagy anélkül. */
        function dontes(saveDraft) {
            var tabId = closeConfirm.pendingTabId
            closeConfirm.pendingTabId = ""
            closeConfirm.close()
            if (tabId.length > 0)
                root.closeAccepted(tabId, saveDraft)
        }

        ColumnLayout {
            spacing: 12

            // #918: a tördelő `Text` FIX szélességgel, layout-gyerekként —
            // egyetlen, csupasz gyerekként kötési hurkot okozna.
            Text {
                objectName: "documentTabCloseConfirmMessage"
                Layout.preferredWidth: 360
                text: root.unsavedMessage
                wrapMode: Text.WordWrap
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }

            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: 8

                PicasaButton {
                    objectName: "documentTabSaveDraftButton"
                    text: qsTr("Save Draft")
                    accent: Theme.picasaGreen
                    onClicked: closeConfirm.dontes(true)
                }
                PicasaButton {
                    objectName: "documentTabDiscardButton"
                    text: qsTr("Discard Changes")
                    onClicked: closeConfirm.dontes(false)
                }
                PicasaButton {
                    objectName: "documentTabCancelButton"
                    text: qsTr("Cancel")
                    onClicked: closeConfirm.close()
                }
            }
        }
    }
}
