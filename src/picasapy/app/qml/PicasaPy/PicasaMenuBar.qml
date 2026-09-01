import QtQuick
import QtQuick.Controls

// A Picasa 3.9 teljes menüszerkezete (a magyar 3.9-ből dokumentálva,
// ld. docs/specs/ui-audit-menus.md, #324/#327). A még nem implementált
// pontok szürkék — a szerkezet a dizájn része. A gyorsbillentyűk a
// feliratban `\t`-tal elválasztva jelennek meg (pl. "Rename...\tF2");
// a ténylegesen ható (élő) billentyűket vagy a lenti `Shortcut` elemek,
// vagy a Main.qml globális `Shortcut`-jai kötik be — az inaktív
// pontoknál a felirat csak vizuális, nincs mögötte élő billentyű.
MenuBar {
    id: bar
    // #305: null-őr a `controller` kötésekhez — a QML-engine leépítésekor
    // a context property átmenetileg null lehet, miközben a QML-kötések
    // utoljára kiértékelődnek.
    readonly property var ctl: controller
    // #1454: a bal hasáb NÉZETMÓDJA (Egyszerű / Fa / Egyszerűsített fa) a
    // `FolderHierarchyController`-ben él, ami ÖNÁLLÓ context property — nem
    // az `AppController` része. A `typeof`-őr azért kell, mert a menüsávot
    // önmagában betöltő próbák nem regisztrálják.
    readonly property var folderViewCtl:
        (typeof folderHierarchyController !== "undefined")
        ? folderHierarchyController : null

    // #423: a kék „Bejelentkezés Google Fiókkal" hivatkozás a menüsáv jobb
    // szélén — az eredeti Picasa ugyanabban a sorban tartja, mint a
    // Fájl/Szerkesztés/… menüket. A `background` felülírása szükséges,
    // mert a MenuBar tartalma (a menük listája) csak a saját szélességét
    // foglalja el balra — a jobb oldali üres sáv a háttérrétegen keresztül
    // látszik, oda kerül a felirat. A `Theme.canvasBg` a Main.qml
    // `palette.window`-jával megegyező szín (ld. Main.qml `palette {}`
    // blokkja), így a csere vizuálisan nem tér el az alap Fusion-nézettől.
    // Funkció még nincs mögötte (a Google-fiókos bejelentkezés nem cél) —
    // ez csak az elrendezés része, ezért nem interaktív.
    background: Rectangle {
        color: Theme.canvasBg
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width; height: 1
            color: Theme.chromeBorder
        }
        Text {
            id: signInLink
            objectName: "menuBarSignInLink"
            anchors.right: parent.right
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            text: qsTr("Sign in with your Google Account")
            color: Theme.linkBlue
            font.pixelSize: Theme.fontSize
            font.underline: true
        }
        // #1654: a tesztüzem LÁTHATÓ állapot. A menüben ülő pipa ehhez
        // kevés — ahhoz ki kell nyitni a menüt. A felhasználó ne felejtse
        // bekapcsolva észrevétlenül: amíg a mód él, a menüsáv jobb szélén
        // állandó, figyelmeztető feliratot lát.
        Text {
            id: tesztuzemBadge
            objectName: "menuBarTesztuzemBadge"
            // #1676: a jelvény a menütételek FÖLÉ kerül. A `background` a
            // `Control`-ban mindig a `contentItem` ALATT van, a menütételek
            // pedig a `contentItem`-ben ülnek. Windowson a felirat majdnem
            // kétszer olyan széles (324 px a linuxos 174 helyett), ezért
            // benyúlik a menütételek alá, és a legjobboldalibb `MenuBarItem`
            // ELVESZI a kattintást — a felirat kikapcsoló gombja némán
            // hatástalan lett. MÉRVE a windowsos CI-n: a pontot fedő elemek
            // közt ott a `MenuBarItem_QMLTYPE_185`, miközben az ablak aktív,
            // a jelvény látható és engedélyezett.
            //
            // A `parent` futásidejű átállítása megkerüli a `Container`
            // alapértelmezett tulajdonságát (különben menütétel lenne
            // belőle), és plain vizuális gyerekként a `z` már a tételek
            // fölé emeli. Emiatt viszont a `signInLink` MÁR NEM testvér,
            // tehát a jobb margót számolni kell.
            // ⚠️ #1697: az `anchors` a `bar`-ra hivatkozva figyelmeztetést
            // dobott MINDEN induláskor („Cannot anchor to an item that isn't
            // a parent or sibling"), mert a kötések a KOMPONENS
            // létrehozásakor kiértékelődnek — akkor viszont a szülő még a
            // háttér-téglalap, a `bar` pedig annak sem szülője, sem
            // testvére. A `parent`-re hivatkozva a kötés MINDKÉT állapotban
            // érvényes: előbb a háttérre (az kitölti a sávot), a
            // reparentálás után a menüsávra — és újra is értékelődik, mert
            // a `parent` maga is tulajdonság.
            Component.onCompleted: parent = bar
            z: 3
            anchors.right: parent.right
            anchors.rightMargin: signInLink.width + 26  // 10 (signIn) + 16 (rés)
            anchors.verticalCenter: parent.verticalCenter
            visible: (bar.ctl && bar.ctl.tesztuzemEnabled !== undefined)
                ? bar.ctl.tesztuzemEnabled : false
            text: qsTr("TEST MODE — logging startup")
            color: "#c0392b"
            font.pixelSize: Theme.fontSize
            font.bold: true
            // A jelzés egyben KIKAPCSOLÓ is: a felhasználónak ne kelljen
            // visszakeresnie a Súgó menüt ahhoz, hogy megszabaduljon a
            // módtól, amiről épp most jutott eszébe, hogy bekapcsolva van.
            MouseArea {
                objectName: "menuBarTesztuzemBadgeArea"
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: bar.ctl.setTesztuzemEnabled(false)
            }
        }
    }
    // van-e kijelölt kép — a fájlművelet- és export-menüpontok feltétele (#15/#16)
    property bool photoActionsEnabled: false
    // #922: a Létrehozás-tételek forrása a KÉPTÁLCA is lehet (#455), ezért
    // NEM a `photoActionsEnabled`-ből élnek — az a rácsbeli kijelöléshez
    // kötött 27 fotó-műveletet vezérli, és azoknak tényleg kijelölés kell.
    property bool createActionsEnabled: false
    // #444: van-e a kijelölésben MÁR mentett kép — enélkül a
    // „Visszaállítás" és az „Utolsó mentés visszavonása" értelmetlen
    property bool hasSavedBackup: false
    signal rescanRequested()
    signal aboutRequested()
    signal thumbSizePreset(int size)
    signal selectStarredRequested()
    signal selectAllRequested()
    signal clearSelectionRequested()
    // #1686: a `Ctrl+I` MÁR MŰKÖDÖTT (Main.qml globális `Shortcut`-ja), csak
    // a menütétel volt helyfoglaló — a funkciót tehát csak az érte el, aki
    // ismerte a billentyűt. A #1616 söprő őre ezt nem foghatta meg: az a
    // helyfoglaló tételeket szándékosan kizárja (ott a felirat nem ígéret).
    signal invertSelectionRequested()
    signal folderManagerRequested()
    // #350: Eszközök → Beállítások... (options.fen) — az OptionsDialog
    // megnyitását a Main.qml köti be (forró fájl, az integrátor dolga)
    signal optionsRequested()
    // #287: Duplikátum-kereső ablak megnyitása
    signal dedupRequested()
    // #1473: Arckeresés — az `Eszközök` menü tétele. Az eredetiben ez nem
    // menüpont volt, hanem alapból bekapcsolt háttérszál
    // (`BgFaceDetectThread`, ld. docs/specs/picasa-arcfelismeres.md 1.1);
    // nálunk háttérmotor híján ez a belépési pont (FaceScanDialog.qml).
    signal faceScanRequested()
    // #368: Eszközök → Kísérleti → Adatbázis áthelyezése
    signal moveDatabaseRequested()
    signal compactDatabaseRequested()
    signal renameRequested()
    signal exportRequested()
    // #1616: Fájl ▸ Új album… (Ctrl+N) — a dialógus (`newAlbumDialog`,
    // FileOpsDialogs.qml) a Main.qml-ben él, és ugyanazt a
    // `fileOpsDialogs.openNewAlbum(...)` belépőt hívja, amit a rács helyi
    // menüjének „Új album…" tétele is (PhotoContextMenu.newAlbumRequested).
    signal newAlbumRequested()
    // #1615: Fájl ▸ Importálás forrása… (Ctrl+M) —
    // `eMenuFile::ID_FILE_IMPORTPICTURE`, `cmd 0x9c91`. A párbeszéd
    // (`ImportSourceDialog`) a Main.qml-ben él, és ugyanaz a példány, amit
    // az eszköztár „Import" gombja nyit — a menü NEM külön utat jár.
    signal importSourceRequested()
    // #1633: Fájl ▸ Fájl felvétele a Picasába… (Ctrl+O) —
    // `ID_FILE_OPEN`, `cmd 0xe101` (ld. `AddFileDialog.qml` fejléce a
    // teljes indoklásért — ugyanaz a hibaosztály, mint a Ctrl+M volt a
    // #1615 előtt). A párbeszéd a Main.qml-ben él.
    signal addFileRequested()
    // #1614: Fájl ▸ Áthelyezés új mappába… — `eMenuFile::ID_FILE_NEWFOLDER`.
    // A parancs NEVE félrevezet: nem mappát hoz létre, hanem a kijelölt
    // képeket helyezi át egy újba (a hivatalos magyar felirat ezt mondja
    // ki: `stringres-en-hu.tsv` — „Áthel&yezés új mappába…"). A dialógus
    // (`moveToNewFolderDialog`, FileOpsDialogs.qml) a Main.qml-ben él, és
    // csak a NEVET kéri — a helyet (a kijelölés mappáját) a
    // `FileOpsController.moveSelectionToNewFolder` választja, ugyanúgy,
    // mint az „Új album…" (#1616) a saját dialógusánál.
    signal moveToNewFolderRequested()
    // #1472: Fájl ▸ Nyomtatás… (Ctrl+P) — a párbeszéd a Main.qml-ben él,
    // ugyanúgy, mint az exportnál; a képtálca „Nyomtatás" gombja
    // (TrayBar.printRequested) ugyanoda vezet
    signal printRequested()
    // #1590: Mappa ▸ Bélyegképek nyomtatása… (Ctrl+Shift+P) —
    // `eMenuLabelFolder::ID_FILE_PRINTCONTACTSHEET`. Ugyanaz a
    // nyomtatás-párbeszéd nyílik, indexkép-elrendezésre állítva.
    signal printContactSheetRequested()
    // #351: Mappa → Exportálás weboldalként… (webexport.fen)
    signal webExportRequested()
    // #530: Google Earth-export a kijelölt (geocímkézett) képekből
    signal earthExportRequested()
    // #1589: `ID_VIEW_EARTH` — ugyanaz a KML, de utána MEG IS NYITJA a
    // rendszer társított programjával. Az eredetiben KÉT külön menütétel
    // van; a párbeszédet itt is a hívó (Main.qml) nyitja.
    signal earthViewRequested()
    // #29: Létrehozás → Képkollázs / Mozgófilm a kijelölésből
    signal collageRequested()
    signal movieRequested()
    signal locateRequested()
    signal deleteRequested()
    // #1608: a `0x9c9a` parancs jelentése NÉZETFÜGGŐ (spec 5., két
    // független forrás: a `stringres` gyorsbillentyű-mezői és a #1154
    // rekord-mérése). Mappában „Törlés a lemezről" (Lomtár), albumban
    // „Eltávolítás az albumból", Emberek-albumban „Eltávolítás az
    // Emberek albumból" — az utóbbi kettőnél a fájl A LEMEZEN MARAD.
    // A `Delete` eddig feltétel nélkül törölt: ez ADATVESZTÉS volt.
    signal removeFromAlbumRequested()
    signal removeFromPeopleAlbumRequested()
    // A NÉZET azonosítói — a hívó (Main.qml) tölti a vezérlőből. Üres
    // mindkettő = mappa-nézet; a kettő kizárja egymást (a vezérlő
    // `_view_mode`-ja egyetlen érték, ld. controller.py `currentAlbumToken`
    // és people_controller.py `currentPersonName`).
    property string currentAlbumToken: ""
    property string currentPersonName: ""
    // A felirat és a művelet EGYETLEN helyen dől el, hogy a kettő ne
    // csúszhasson el egymástól (a menütétel azt csinálja, amit ígér).
    readonly property string deleteCommandText:
        bar.currentPersonName !== ""
            ? qsTr("Remove from People Album")
            : (bar.currentAlbumToken !== ""
                ? qsTr("Remove from Album")
                : qsTr("Delete from Disk"))
    // A `Delete` billentyű és a Fájl ▸ tétel KÖZÖS belépője (#1608) — így
    // a kettő nem tud különböző dolgot csinálni.
    function activateDeleteCommand() {
        if (bar.currentPersonName !== "")
            bar.removeFromPeopleAlbumRequested()
        else if (bar.currentAlbumToken !== "")
            bar.removeFromAlbumRequested()
        else
            bar.deleteRequested()
    }
    // #444: a NÉGY mentés-művelet közül három (a negyedik, az „Összes
    // szerkesztés visszavonása" a Kép menüben él, #465)
    signal saveRequested()
    signal revertRequested()
    // #1527: a mentés-család két hiányzó tagja. Mérve (ld.
    // `picasapy.edit.save_copy`): az eredetiben MINDKETTŐ ugyanaz a
    // függvény, egyetlen kapcsolóval — a „Mentés másként…" fájlválasztót
    // nyit (ezért végződik a felirata pontokra), a „Másolat mentése"
    // nem kérdez, a nevet a `%s-%03lu` minta adja.
    signal saveAsRequested()
    signal saveCopyRequested()
    signal slideshowRequested()
    // #24: Időrend nézet (Ctrl+5)
    signal timelineRequested()
    // #12: a Címkék-panel állapota kívülről kötve, a menüpont csak kér
    property bool tagsPanelOpen: false
    signal tagsPanelRequested()
    // #30: Helyek-panel (térkép)
    property bool placesPanelOpen: false
    signal placesPanelRequested()
    // #26: Emberek-panel (a jobb fiók negyedik panelje)
    property bool peoplePanelOpen: false
    signal peoplePanelRequested()
    // #17: Kép → Elrejtés a kijelölésre
    signal hideToggleRequested()
    // #13: Tulajdonságok-panel
    property bool propertiesPanelOpen: false
    signal propertiesPanelRequested()
    // #426: „Az összes effektus másolása/beillesztése" — a Beillesztés
    // csak akkor engedélyezett, ha van másolt effektlánc (a
    // controller.hasAllEffectsClipboard-hoz kötve). A `photo_ops_
    // controller.PhotoOpsMixin` motorját hívja — SZÁNDÉKOSAN nem a
    // #152-es `effects_controller`-t, mert az a kép-specifikus
    // `crop64`-et is átvinné (ld. `docs/specs/filterdesc-registry.md`).
    property bool hasAllEffectsClipboard: false
    signal copyAllEffectsRequested()
    signal pasteAllEffectsRequested()
    // #1475: a KÉT kötegelt visszavonás vezérlője. Az eredetiben a
    // Szerkesztés menü ÉLÉN áll a visszavonás (`eMenuEdit::ID_UNDO`, ld.
    // `docs/specs/picasa-hu-terminology.md`), és a felirat megnevezi a
    // visszavonandó műveletet (a `CFilterStackUI` `undoname` kulcsa záró
    // szóközzel áll, ld. `app/edit_action_names.py`). Nálunk a #465 óta
    // HÁROM külön verem van, ezért nem EGY általános „Visszavonás" áll itt,
    // hanem művelet szerint nevesített tétel, mindegyik a SAJÁT
    // `canUndo…`-jától függően szürkülve. Kijelöléstől SZÁNDÉKOSAN nem
    // függenek: a visszavonandó köteg a művelet óta megjegyzett képekre
    // hat, nem a mostani kijelölésre.
    property bool canUndoPasteAllEffects: false
    property bool canUndoBatchEdit: false
    signal undoPasteAllEffectsRequested()
    signal undoBatchEditRequested()
    // #425: Kép ▸ Csoportos szerkesztés — a kijelölt N kép mindegyikére
    // egyszerre alkalmazott egykattintásos effekt (`controller.
    // applyEffectMany`); a `name` a `batch_effect_controller._KNOWN_EFFECTS`
    // egyike ("autolight"/"autocolor"/"redeye"/"enhance"/"unsharp"/
    // "grain2"/"warm"). A forgatás NEM ide tartozik — az a meglévő
    // `rotateRightMany`/`rotateLeftMany` úton fut, közvetlenül a Main.qml-ből.
    signal batchApplyEffectRequested(string name)
    // #465 3. pont: „Undo All Edits" — a kijelölt kép(ek) TELJES
    // szerkesztési láncát törli (a Csoportos szerkesztés almenün KÍVÜL, a
    // Kép menü saját tétele) — megerősítéssel, ld. Main.qml ConfirmDialog.
    signal undoAllEditsRequested()
    //: #1526: a kijelölt képek FÁJLJAI a vágólapra
    signal copyFilesRequested()
    signal cutFilesRequested()
    // #1595: a Mappa menü négy néma tétele — mind a MEGNYITOTT mappára
    // vonatkozik (az eredetiben a „Mappa" menü ezt jelenti). A vezérlők
    // már megvannak: a mappa-áthelyezés a #457, a lomtárba tétel a #1638,
    // az eltávolítás a #1249, a fájlkezelőben megnyitás a #422 óta.
    signal folderMoveRequested()
    signal folderDeleteRequested()
    signal folderRemoveFromPicasaRequested()
    signal folderLocateRequested()

    // #327: gyorsbillentyűk azoknak az AKTÍV menüpontoknak, amelyeknek
    // még nincs élő bekötésük máshol (a többi már a Main.qml globális
    // Shortcut-jain vagy a menüpont onTriggered-jén keresztül működik —
    // azokhoz itt csak a MENÜBEN LÁTSZÓ felirat tartozik, ld. lent).
    Shortcut {
        objectName: "shortcutSmallThumbnails"
        sequence: "Ctrl+1"
        onActivated: bar.thumbSizePreset(96)
    }
    Shortcut {
        objectName: "shortcutNormalThumbnails"
        sequence: "Ctrl+2"
        onActivated: bar.thumbSizePreset(144)
    }
    Shortcut {
        objectName: "shortcutLocateOnDisk"
        sequence: "Ctrl+Return"
        enabled: bar.photoActionsEnabled
        onActivated: bar.locateRequested()
    }
    Shortcut {
        objectName: "shortcutDeleteFromDisk"
        sequence: "Delete"
        enabled: bar.photoActionsEnabled
        // #1608: nézetfüggő — albumban NEM töröl lemezről
        onActivated: bar.activateDeleteCommand()
    }
    // #1472: a Ctrl+P eddig SEHOL nem létezett — a menüfelirat hirdette,
    // de billentyű nem tartozott hozzá. A feliratot itt szó szerint
    // követjük (nem `StandardKey.Print`), hogy a kettő ne csúszhasson el.
    Shortcut {
        objectName: "shortcutPrint"
        sequence: "Ctrl+P"
        enabled: bar.photoActionsEnabled
        onActivated: bar.printRequested()
    }
    // #1590: a Mappa-menü felirata Ctrl+Shift+P-t hirdet
    // (`docs/specs/picasa-gyorsbillentyuk.md` 25. sora is ezt mondja) —
    // ne maradjon puszta felirat, ahogy a Ctrl+P is az volt a #1472-ig.
    // ⚠️ A menütételtől ELTÉRŐEN itt VAN feltétel: a gyorsbillentyűnek
    // nincs hova visszajeleznie, ha nincs mit nyomtatni.
    Shortcut {
        objectName: "shortcutPrintContactSheet"
        sequence: "Ctrl+Shift+P"
        enabled: bar.photoActionsEnabled
        onActivated: bar.printContactSheetRequested()
    }
    // #1615: a Fájl-menü felirata Ctrl+M-et hirdet (a #1154 MÉRTE a
    // menüsáv gyorsbillentyű-táblájából: `0xd6d9b0`, `cmd 0x9c91`) — ne
    // maradjon puszta felirat. Feltétel nélkül él, mint maga a menüpont.
    //
    // Szövegmező-ütközés (#1526/#1571): a Qt a leütést előbb
    // `ShortcutOverride`-ként ajánlja fel a fókuszált elemnek, és a
    // `QQuickTextInput` csak az általa KEZELT billentyűket fogadja el. A
    // `Ctrl+M` nem ilyen, tehát a keresőmezőben állva is ez nyer — MÉRVE:
    // `tests/app/qml_functional/test_import_menupont_1615.py`.
    Shortcut {
        objectName: "shortcutImportFrom"
        sequence: "Ctrl+M"
        onActivated: bar.importSourceRequested()
    }
    // #1633: a Fájl-menü felirata Ctrl+O-t hirdet — ugyanaz a
    // hibaosztály, mint a Ctrl+M volt a #1615 előtt. Feltétel nélkül él,
    // mint maga a menüpont (a fájlválasztó nem függ kijelöléstől).
    Shortcut {
        objectName: "shortcutAddFile"
        sequence: "Ctrl+O"
        onActivated: bar.addFileRequested()
    }
    // #1616: a Fájl-menü felirata Ctrl+N-et hirdet — ugyanaz a hibaosztály,
    // mint a Ctrl+M/Ctrl+O volt. A kijelölés-függés (`photoActionsEnabled`)
    // itt SZÁNDÉKOS, eltérően a Ctrl+M/Ctrl+O-tól: a `createAlbum` üres
    // kijelölésnél nem hoz létre semmit (üres tokent ad vissza), tehát a
    // billentyűnek sincs mit csinálnia — ugyanaz a feltétel, mint a
    // menütételen.
    Shortcut {
        objectName: "shortcutNewAlbum"
        sequence: "Ctrl+N"
        enabled: bar.photoActionsEnabled
        onActivated: bar.newAlbumRequested()
    }

    PicasaMenu {
        title: qsTr("&File")
        // #1616: a tétel `PicasaMenuItem { placeholder: true }` volt —
        // MÉRVE (`git log -S'menuFileNewAlbum'`): MINDIG az volt, az #416
        // óta, tehát a #1616 jegy „a tétel él, csak a billentyű néma"
        // állítása a mai kódon TÉVES. A funkció maga viszont NEM hiányzik:
        // a `newAlbumDialog` (FileOpsDialogs.qml) és a `controller.
        // createAlbum(name, rows)` már kész és élesen működik a rács
        // helyi menüjéből (`PhotoContextMenu.newAlbumRequested` →
        // `fileOpsDialogs.openNewAlbum(window.selectedRows())`, Main.qml).
        // Ugyanaz a hibaosztály, mint a #1615/#1633: hiányzó BEKÖTÉS, nem
        // hiányzó funkció — ezért itt a Ctrl+M/Ctrl+O mintáját követjük:
        // a Fájl-menü tétele és a Ctrl+N UGYANAZT a dialógust nyitja.
        // Kijelölés nélkül a `createAlbum` üres tokent ad vissza (nincs
        // mit albumba tenni), ezért a `photoActionsEnabled`-hez kötve él,
        // mint a többi kijelölés-függő tétel.
        MenuItem {
            objectName: "menuFileNewAlbum"
            text: qsTr("New Album...") + "\tCtrl+N"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.newAlbumRequested()
        }
        // #1774 (mérve): a mentések szerint itt csoporthatár van.
        MenuSeparator {}
        // ⚠️ #1200: ez NEM külön funkció és NEM mappaválasztó — az
        // eredetiben EZ A MENÜPONT nyitja meg a Mappakezelőt:
        // `eMenuFile::ID_TOOLS_INCLUDEEXCLUDEFOLDERS` (`stringres` 2648.)
        // → parancs `0x9caa` → `0x005cb990` szétosztó → `0x005ce590`.
        //
        // Korábban fordítva volt: a menüpont inaktív (placeholder), a
        // funkciót pedig egy gomb végezte magában a párbeszédben.
        MenuItem {
            objectName: "menuFileAddFolder"
            text: qsTr("Add Folder to Picasa...")
            onTriggered: bar.folderManagerRequested()
        }
        // #1633: ÉLŐ tétel. A fájlválasztó nem függ kijelöléstől, ezért
        // nincs `enabled` feltétele — ugyanúgy, mint az Importálás forrása…
        MenuItem {
            objectName: "menuFileAddFile"
            text: qsTr("Add File to Picasa...") + "\tCtrl+O"
            onTriggered: bar.addFileRequested()
        }
        // #1615: ÉLŐ tétel. Az importálás nem függ kijelöléstől (a forrást
        // maga a párbeszéd kérdezi meg), ezért — a Nyomtatás…-tól eltérően
        // — nincs `enabled` feltétele.
        MenuItem {
            objectName: "menuFileImportFrom"
            text: qsTr("Import From...") + "\tCtrl+M"
            onTriggered: bar.importSourceRequested()
        }
        // hiányzott (#324 audit): a Google Fotókból importálás menüpontja
        PicasaMenuItem { text: qsTr("Import From Google Photos..."); placeholder: false; retired: true }  // #638
        MenuSeparator {}
        // hiányzott (#324 audit): fájl(ok) megnyitása a szerkesztőben
        // #1616: a felirat Ctrl+Shift+O-t hirdetett, de a funkció teljesen
        // hiányzik (a tétel helyfoglaló) — a billentyű lekerült a feliratról.
        PicasaMenuItem { text: qsTr("Open File(s) in Editor"); placeholder: true }
        MenuSeparator {}
        // #1614: ÉLŐ tétel — MÉRVE (`git log -S'ID_FILE_NEWFOLDER'`) a
        // tétel a #324 audit óta helyfoglaló volt, holott a parancs neve
        // ELLENÉRE nem mappa-létrehozás, hanem a kijelölt képek áthelyezése
        // (ld. a `moveToNewFolderRequested` jelzés fenti megjegyzését). A
        // kijelölés-függés (`photoActionsEnabled`) ugyanaz a minta, mint az
        // „Új album…"-nál (#1616): kijelölés nélkül nincs mit áthelyezni.
        MenuItem {
            objectName: "menuFileMoveToNewFolder"
            text: qsTr("Move to New Folder...")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.moveToNewFolderRequested()
        }
        MenuItem {
            objectName: "menuFileRename"
            text: qsTr("Rename...") + "\tF2"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.renameRequested()
        }
        // #1774 (mérve): a mentések szerint itt csoporthatár van.
        MenuSeparator {}
        // #444/#1791: a nem-destruktív mentés HÁROM fokozata, de a
        // menüben csak KETTŐ látszik. A „Mentés" beégeti a
        // szerkesztéseket a fájlba (előtte biztonsági másolattal), a
        // „Visszaállítás" az eredetit hozza vissza (a szerkesztések
        // elvesznek). A harmadik fokozat — a fájl visszaáll, de a
        // szerkesztések MEGMARADNAK — az eredetiben NEM menütétel, hanem
        // a Visszaállítás párbeszéd „Undo Save" gombja
        // (`CThumbUI::FileRevert::undosave`); ld. SaveDialogs.qml.
        MenuItem {
            objectName: "menuFileSave"
            text: qsTr("Save") + "\tCtrl+S"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.saveRequested()
        }
        MenuItem {
            objectName: "menuFileRevert"
            text: qsTr("Revert")
            // csak akkor van mit visszaállítani, ha a kép már volt mentve
            enabled: bar.photoActionsEnabled && bar.hasSavedBackup
            onTriggered: bar.revertRequested()
        }
        MenuSeparator {}
        // #1527: a mentés-család két további tagja — ÉLŐ tételek. A
        // különbségük MÉRT (`picasapy.edit.save_copy` modul-docstring):
        // a „Mentés másként…" fájlválasztót nyit (ellipszis a
        // feliratban), és az AKTUÁLIS képre hat, mert egy választó egy
        // célt tud megnevezni; a „Másolat mentése" nem kérdez, a nevet
        // a mért `-001` minta adja, és a teljes kijelölésre hat.
        MenuItem {
            objectName: "menuFileSaveAs"
            text: qsTr("Save As...")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.saveAsRequested()
        }
        MenuItem {
            objectName: "menuFileSaveCopy"
            text: qsTr("Save a Copy")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.saveCopyRequested()
        }
        // #1774 (mérve): az exportálás UGYANEBBEN a csoportban van, mint a
        // „Mentés másként…” és a „Másolat mentése” — nincs közte elválasztó.
        MenuItem {
            objectName: "menuFileExport"
            text: qsTr("Export Picture to Folder...") + "\tCtrl+Shift+S"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.exportRequested()
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuFileLocate"
            text: qsTr("Locate on Disk") + "\tCtrl+Enter"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.locateRequested()
        }
        MenuItem {
            objectName: "menuFileDelete"
            // #1608: a felirat a nézettel EGYÜTT vált
            text: bar.deleteCommandText + "\tDelete"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.activateDeleteCommand()
        }
        MenuSeparator {}
        // #1472: ÉLŐ tétel — a `print_controller.py` 213 sora addig
        // elérhetetlen volt, mert ez a pont helyfoglaló maradt
        MenuItem {
            objectName: "menuFilePrint"
            text: qsTr("Print...") + "\tCtrl+P"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.printRequested()
        }
        // #1616: a felirat Ctrl+E-t hirdetett, de a `TrayBar.emailRequested()`
        // jelzés MÉRVE nincs sehova bekötve (ld. `email_controller.py`
        // fejléce — a bekötés az integrátor teendője, még nem történt meg),
        // tehát ez a menütétel is helyfoglaló — a billentyű lekerült.
        PicasaMenuItem { text: qsTr("E-Mail..."); placeholder: true }
        // hiányzott (#324 audit): nyomtatott képek online rendelése
        PicasaMenuItem { text: qsTr("Order Prints..."); placeholder: false; retired: true }  // #638
        MenuSeparator {}
        // #1527: a Fájl menü zárótétele. A jegy „nincs a menüben"-ként
        // írta le — MÉRVE megvolt (2026-08-24), csak `objectName` nélkül,
        // ezért egyetlen teszt sem érte el. A név most már fogja.
        MenuItem {
            objectName: "menuFileExit"
            text: qsTr("E&xit")
            onTriggered: Qt.quit()
        }
    }
    PicasaMenu {
        title: qsTr("&Edit")
        // #1475: a visszavonás a menü ÉLÉN — ide teszi az eredeti is
        // (`eMenuEdit::ID_UNDO`). A felirat megnevezi a műveletet, hogy a
        // felhasználó ne vaktában nyomja meg.
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
            text: qsTr("Cut") + "\tCtrl+X"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.cutFilesRequested()
        }
        MenuItem {
            objectName: "menuEditCopy"
            text: qsTr("Copy") + "\tCtrl+C"
            enabled: bar.photoActionsEnabled
            onTriggered: bar.copyFilesRequested()
        }
        // #1526: a Beillesztés a fájl-vágólap MÁSIK fele — külön munka
        // (ütközéskezelés, célmappa), ezért egyelőre helyfoglaló marad.
        PicasaMenuItem { text: qsTr("Paste") + "\tCtrl+V"; placeholder: true }
        MenuSeparator {}
        MenuItem {
            objectName: "menuEditCopyEffects"
            text: qsTr("Copy All Effects")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.copyAllEffectsRequested()
        }
        MenuItem {
            objectName: "menuEditPasteEffects"
            text: qsTr("Paste All Effects")
            enabled: bar.photoActionsEnabled && bar.hasAllEffectsClipboard
            onTriggered: bar.pasteAllEffectsRequested()
        }
        MenuSeparator {}
        // hiányzott (#324 audit): feliratszöveg vágólap-műveletei
        PicasaMenuItem { text: qsTr("Copy Text"); placeholder: true }
        PicasaMenuItem { text: qsTr("Paste Text"); placeholder: true }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Select All") + "\tCtrl+A"
            onTriggered: bar.selectAllRequested()
        }
        MenuItem {
            text: qsTr("Select Starred")
            onTriggered: bar.selectStarredRequested()
        }
        MenuItem {
            objectName: "menuEditInvertSelection"
            text: qsTr("Invert Selection") + "\tCtrl+I"
            onTriggered: bar.invertSelectionRequested()
        }
        MenuItem {
            text: qsTr("Clear Selection") + "\tCtrl+D"
            onTriggered: bar.clearSelectionRequested()
        }
    }
    PicasaMenu {
        title: qsTr("&View")
        MenuItem {
            objectName: "menuViewLibraryView"
            text: qsTr("Library View")
            checkable: true
            // A pipa ÁLLANDÓ (a könyvtárnézet mindig aktív, amíg az „Edit
            // View" helykitöltő). Kötés híján itt nincs mit újraértékelni,
            // ezért a kattintás imperatív `checked`-írását kézzel kell
            // visszavenni — különben egyetlen kattintás VÉGLEG leszedi.
            checked: true
            onTriggered: checked = true
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Small Thumbnails") + "\tCtrl+1"
            onTriggered: bar.thumbSizePreset(96)
        }
        MenuItem {
            text: qsTr("Normal Thumbnails") + "\tCtrl+2"
            onTriggered: bar.thumbSizePreset(144)
        }
        PicasaMenuItem { text: qsTr("Edit View") + "\tCtrl+3"; placeholder: true }
        MenuSeparator {}
        MenuItem {
            objectName: "menuViewProperties"
            text: qsTr("Properties")
            checkable: true
            checked: bar.propertiesPanelOpen
            onTriggered: bar.propertiesPanelRequested()
        }
        MenuItem {
            objectName: "menuViewTags"
            text: qsTr("Tags") + "\tCtrl+T"
            checkable: true
            checked: bar.tagsPanelOpen
            onTriggered: bar.tagsPanelRequested()
        }
        // #26: az Emberek-panel — a jobb fiók negyedik panelje
        MenuItem {
            objectName: "menuViewPeople"
            text: qsTr("People")
            checkable: true
            checked: bar.peoplePanelOpen
            onTriggered: bar.peoplePanelRequested()
        }
        MenuItem {
            objectName: "menuViewPlaces"
            text: qsTr("Places")
            checkable: true
            checked: bar.placesPanelOpen
            onTriggered: bar.placesPanelRequested()
        }
        MenuSeparator {}
        // hiányzott (#324 audit): a szerkesztő panel láthatóság-kapcsolója
        PicasaMenuItem { text: qsTr("Show Editing Controls"); checkable: true; placeholder: true }
        // #1774 (mérve): a mentések szerint itt csoporthatár van.
        MenuSeparator {}
        MenuItem {
            objectName: "menuViewSlideshow"
            text: qsTr("Slideshow") + "\tCtrl+4"
            onTriggered: bar.slideshowRequested()
        }
        MenuItem {
            objectName: "menuViewTimeline"
            text: qsTr("Timeline") + "\tCtrl+5"
            onTriggered: bar.timelineRequested()
        }
        MenuSeparator {}
        // hiányzott (#324 audit): keresési opciók
        PicasaMenuItem { text: qsTr("Search Options"); placeholder: true }
        // hiányzott (#324 audit): a jelentése a screenshotokból nem
        // egyértelmű — feltehetően mappacím nélküli indexkép-rács
        PicasaMenuItem {
            objectName: "menuViewThumbnailsOnly"
            text: qsTr("Thumbnails Only")
            checkable: true
            placeholder: true
        }
        MenuItem {
            objectName: "menuViewHidden"
            text: qsTr("Hidden Pictures")
            checkable: true
            // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
            // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
            checked: (bar.ctl && bar.ctl.showHidden !== undefined) ? bar.ctl.showHidden : false
            onTriggered: controller.toggleShowHidden()
        }
        // #1774 (mérve): a mentések szerint itt csoporthatár van.
        MenuSeparator {}
        // hiányzott (#324 audit): színprofil-kezelés kapcsoló
        PicasaMenuItem { text: qsTr("Use Color Management"); checkable: true; placeholder: true }
        MenuItem {
            // #28: opcionális sötét téma — az alapértelmezés a világos
            objectName: "menuViewDarkTheme"
            text: qsTr("Dark Theme")
            checkable: true
            checked: (bar.ctl && bar.ctl.darkTheme !== undefined) ? bar.ctl.darkTheme : false
            onTriggered: controller.toggleDarkTheme()
        }
        // #1774 (mérve): a Megjelenítési mód UGYANEBBEN a csoportban van,
        // mint a Színkezelés használata — nincs közte elválasztó.
        // #1575: a Megjelenítési mód almenü — 11 tétel + 4 elválasztó
        // (15 rekord), a `docs/specs/picasa-megjelenitesi-modok.md` 1.
        // szakaszának SORRENDJÉBEN. A tartalom a binárisból mérve
        // (`0x0055ab62`–`0x0055abd4`); a korábbi „a screenshotokból nem
        // derül ki" komment 2026-08-27 óta elavult.
        //
        // Mind a tizenegy EGYETLEN kizáró csoport tagja (mérve,
        // `0x00575670`) — kapcsoló egy sincs köztük, tehát a
        // „Túlcsordult képpontok" és a „Projektor mód" sem kombinálható a
        // gammákkal. A pipa ezért végig a `bar.ctl.displayMode`-ra köt.
        //
        // ⚠️ RÁDIÓ-CSAPDA (ld. a `Thumbnail Caption` alatti magyarázatot és
        // a #1464/#1468-at): a valódi kattintás előbb IMPERATÍVAN átbillenti
        // a `checked`-et, és a `setDisplayMode` azonos értéknél
        // SZÁNDÉKOSAN nem jelez — a kötés tehát magától soha nem értékelődne
        // újra. Ezért minden tétel a jelzés után VISSZAKÖTI a `checked`-et.
        //
        // A VÁZ szintjén mind a tizenegy MŰKÖDIK: pipázódik, és a módot
        // beállítja a vezérlőn. A képpont-hatásuk külön jegyeké
        // (#1576/#1577/#1578); a `24 bites` és — 24 bites képernyőn — az
        // `Automatikus` az eredetiben is no-op.
        //
        // A `&`-gyorsítóbetűket a spec 1. szakasza tartalmazza; ide
        // SZÁNDÉKOSAN nem kerültek be: ebben a fájlban ma csak a hét
        // FŐMENÜ-cím visel mnemonikot, a 130+ tétel egyike sem, és egyetlen
        // almenüt kiemelni következetlenséget szülne. Ez külön jegy dolga.
        PicasaMenu {
            objectName: "menuViewDisplayMode"
            title: qsTr("Display Mode")
            MenuItem {
                objectName: "menuViewDisplayModeAuto"
                text: qsTr("Automatic")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "auto"
                onTriggered: {
                    controller.setDisplayMode("auto")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "auto"
                    })
                }
            }
            MenuSeparator {}
            MenuItem {
                objectName: "menuViewDisplayModeNormal"
                text: qsTr("24-bit")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "normal"
                onTriggered: {
                    controller.setDisplayMode("normal")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "normal"
                    })
                }
            }
            PicasaMenuItem {
                objectName: "menuViewDisplayMode16Bit"
                text: qsTr("16-bit (dithered)")
                // #1658: megvalósítható (a szabály MÉRVE van: MT-zaj +0…7/0…3/0…7,
                // telítő), de 16 bites képernyő ma nincs — ezért helyfoglaló,
                // nem nyugdíjazott: ha egyszer értelmet nyer, bekötjük.
                placeholder: true
            }
            MenuSeparator {}
            PicasaMenuItem {
                objectName: "menuViewDisplayModeRemoteDesktop"
                text: qsTr("Remote Desktop")
                // #1658: a spec 7. táblázata szerint HATÓKÖRÖN KÍVÜL (RDP-specifikus,
                // 3-3-3 bites levágás) — sosem kötjük be, tehát nyugdíjazott.
                placeholder: false
                retired: true
            }
            MenuItem {
                objectName: "menuViewDisplayModeLcd"
                text: qsTr("LCD Whitepoint")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "lcd"
                onTriggered: {
                    controller.setDisplayMode("lcd")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "lcd"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewDisplayModeProjector"
                text: qsTr("Projector Mode")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "projector"
                onTriggered: {
                    controller.setDisplayMode("projector")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "projector"
                    })
                }
            }
            MenuSeparator {}
            MenuItem {
                objectName: "menuViewDisplayModeOverflow"
                text: qsTr("Show overflow pixels")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "overflow"
                onTriggered: {
                    controller.setDisplayMode("overflow")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "overflow"
                    })
                }
            }
            // #1730: ÉLŐ tétel. A #1658 „hatókörön kívül, amíg nincs
            // referencia-mérés" indoka MEGSZŰNT: a #1580 képpont-mérése
            // megvan (a tulajdonos felvételeiről), és a mag a mért
            // világosítást reprodukálja (`render/display_modes.py`,
            // `apply_mac_gamma`).
            MenuItem {
                objectName: "menuViewDisplayModeMacGamma"
                text: qsTr("Mac Gamma (1.6)")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "mac"
                onTriggered: {
                    controller.setDisplayMode("mac")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "mac"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewDisplayModeLinearGamma"
                text: qsTr("Linear Gamma (2.2)")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "linear"
                onTriggered: {
                    controller.setDisplayMode("linear")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "linear"
                    })
                }
            }
            MenuSeparator {}
            MenuItem {
                objectName: "menuViewDisplayModeSepia"
                text: qsTr("Sepia")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "sepia"
                onTriggered: {
                    controller.setDisplayMode("sepia")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "sepia"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewDisplayModeBlackWhite"
                text: qsTr("Black and White")
                checkable: true
                checked: bar.ctl && bar.ctl.displayMode === "bw"
                onTriggered: {
                    controller.setDisplayMode("bw")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.displayMode === "bw"
                    })
                }
            }
        }
        // #1774 (mérve): a mentések szerint itt csoporthatár van.
        MenuSeparator {}
        // #1468: a valódi kattintás előbb IMPERATÍVAN átbillenti a `checked`-et,
        // és csak utána dördül el a `triggered`. Kizáró csoportban a MÁR AKTÍV
        // tételre kattintva a vezérlő állapota nem változik, tehát a kötés magától
        // soha nem értékelődik újra — a menü újranyitásakor egyik tételen sem
        // állna pipa. Ezért a jelzés után azonnal VISSZAKÖTJÜK a `checked`-et
        // (a #1464-ben bevezetett minta).
        //
        // Az öt felirat-mód kizáró csoport. FIGYELEM: a `setThumbCaptionMode`
        // ma FELTÉTEL NÉLKÜL jelez (`statusChanged.emit()`), ezért a hiba itt
        // épp nem látszik — ez azonban a setter véletlen mellékhatása, nem
        // szerződés. A visszakötés ettől függetlenné teszi a menüt.
        PicasaMenu {
            objectName: "menuViewThumbnailCaption"
            title: qsTr("Thumbnail Caption")
            MenuItem {
                objectName: "menuViewThumbCaptionNone"
                text: qsTr("None")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "none"
                onTriggered: {
                    controller.setThumbCaptionMode("none")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.thumbCaptionMode === "none"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewThumbCaptionFilename"
                text: qsTr("Filename")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "filename"
                onTriggered: {
                    controller.setThumbCaptionMode("filename")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.thumbCaptionMode === "filename"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewThumbCaptionCaption"
                text: qsTr("Caption")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "caption"
                onTriggered: {
                    controller.setThumbCaptionMode("caption")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.thumbCaptionMode === "caption"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewThumbCaptionTags"
                text: qsTr("Tags")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "tags"
                onTriggered: {
                    controller.setThumbCaptionMode("tags")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.thumbCaptionMode === "tags"
                    })
                }
            }
            MenuItem {
                objectName: "menuViewThumbCaptionResolution"
                text: qsTr("Resolution")
                checkable: true
                checked: bar.ctl && bar.ctl.thumbCaptionMode === "resolution"
                onTriggered: {
                    controller.setThumbCaptionMode("resolution")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.thumbCaptionMode === "resolution"
                    })
                }
            }
        }
        // #1454: a `Nézet ▸ Mappanézet` az eredetiben NEM rendez — a bal
        // hasáb GYÖKERÉT és HIERARCHIÁJÁT állítja. Korábban itt a
        // `Mappa ▸ Sort By` szó szerinti másolata állt, ugyanazzal a
        // `folderSort` bekötéssel; a rendezés oda (és az indexkép-helyi
        // menübe) tartozik, ide a szerkezet.
        //
        // A pipa-logika mérve (`0x00574b70`, `docs/specs/picasa-mappanezet.md`
        // 3.): az első kettő EGYETLEN bájt két állapota, tehát kizáró pár;
        // az „Egyszerűsített fanézet" ettől FÜGGETLEN, tartós kapcsoló.
        // A négy gyökér (Sajátgép / Képek / Dokumentumok / Asztal) külön
        // jegy (#1407), ezért itt még nem szerepel.
        PicasaMenu {
            id: folderViewMenu
            objectName: "menuViewFolderView"
            title: qsTr("Folder View")
            // A vezérlő állapota EGY helyen — a tételek pipái ezt olvassák,
            // és a kattintás utáni visszakötés is erre hivatkozik.
            readonly property bool treeMode:
                (bar.folderViewCtl && bar.folderViewCtl.treeView !== undefined)
                    ? bar.folderViewCtl.treeView : false
            readonly property bool simplifiedMode:
                (bar.folderViewCtl && bar.folderViewCtl.simplified !== undefined)
                    ? bar.folderViewCtl.simplified : false

            // MÉRT buktató (#1454): a valódi kattintás IMPERATÍVAN
            // átbillenti a `checked`-et, MIELŐTT a `triggered` eldördülne.
            // Ha a felhasználó a MÁR aktív tételre kattint, a vezérlő
            // állapota nem változik, a kötés tehát nem értékelődik újra —
            // és a menü újranyitásakor EGYIK tételen sem lenne pipa. Ezért
            // a jelzés után azonnal visszakötjük a `checked`-et.
            MenuItem {
                objectName: "menuViewFlatFolderView"
                text: qsTr("Flat Folder View")
                checkable: true
                checked: !folderViewMenu.treeMode
                onTriggered: {
                    if (bar.folderViewCtl) bar.folderViewCtl.setTreeView(false)
                    checked = Qt.binding(function () {
                        return !folderViewMenu.treeMode
                    })
                }
            }
            MenuItem {
                objectName: "menuViewTreeView"
                text: qsTr("Tree View")
                checkable: true
                checked: folderViewMenu.treeMode
                onTriggered: {
                    if (bar.folderViewCtl) bar.folderViewCtl.setTreeView(true)
                    checked = Qt.binding(function () {
                        return folderViewMenu.treeMode
                    })
                }
            }
            MenuSeparator {}
            MenuItem {
                objectName: "menuViewSimplifiedTreeView"
                text: qsTr("Simplified Tree View")
                checkable: true
                checked: folderViewMenu.simplifiedMode
                onTriggered: {
                    if (bar.folderViewCtl) bar.folderViewCtl.toggleSimplified()
                    checked = Qt.binding(function () {
                        return folderViewMenu.simplifiedMode
                    })
                }
            }
        }
    }
    PicasaMenu {
        title: qsTr("F&older")
        PicasaMenuItem { text: qsTr("Edit Description..."); placeholder: true }
        MenuItem {
            objectName: "menuFolderSlideshow"
            text: qsTr("View Slideshow") + "\tCtrl+4"
            onTriggered: bar.slideshowRequested()
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Refresh Thumbnails")
            onTriggered: bar.rescanRequested()
        }
        // #324 audit („eltérő"): eredetiben aktív almenü — nálunk is az.
        // #1454: a mappák sorrendje EGYEDÜL itt (és az indexkép-helyi
        // menüben) állítható; a Nézet ▸ Mappanézetből kikerült, mert ott az
        // eredetiben szerkezeti tételek állnak, nem rendezés.
        // #1468: a valódi kattintás előbb IMPERATÍVAN átbillenti a `checked`-et,
        // és csak utána dördül el a `triggered`. Kizáró csoportban a MÁR AKTÍV
        // tételre kattintva a vezérlő állapota nem változik, tehát a kötés magától
        // soha nem értékelődik újra — a menü újranyitásakor egyik tételen sem
        // állna pipa. Ezért a jelzés után azonnal VISSZAKÖTJÜK a `checked`-et
        // (a #1464-ben bevezetett minta).
        //
        // A négy rendezési szempont kizáró csoport; a „Fordított sorrend"
        // ÖNÁLLÓ kapcsoló (az állapota minden kattintásra változik, a kötés
        // tehát magától helyreáll) — ott nem kell visszakötés.
        PicasaMenu {
            objectName: "menuFolderSortBy"
            title: qsTr("Sort By")
            MenuItem {
                objectName: "menuFolderSortByDate"
                text: qsTr("Sort by creation date")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "date"
                onTriggered: {
                    controller.setFolderSort("date")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.folderSort === "date"
                    })
                }
            }
            MenuItem {
                objectName: "menuFolderSortByChanged"
                text: qsTr("Sort by recent changes")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "changed"
                onTriggered: {
                    controller.setFolderSort("changed")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.folderSort === "changed"
                    })
                }
            }
            MenuItem {
                objectName: "menuFolderSortBySize"
                text: qsTr("Sort by size")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "size"
                onTriggered: {
                    controller.setFolderSort("size")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.folderSort === "size"
                    })
                }
            }
            MenuItem {
                objectName: "menuFolderSortByName"
                text: qsTr("Sort by name")
                checkable: true
                checked: bar.ctl && bar.ctl.folderSort === "name"
                onTriggered: {
                    controller.setFolderSort("name")
                    checked = Qt.binding(function () {
                        return bar.ctl && bar.ctl.folderSort === "name"
                    })
                }
            }
            MenuSeparator {}
            MenuItem {
                objectName: "menuFolderSortReverse"
                text: qsTr("Reverse sort")
                checkable: true
                checked: (bar.ctl && bar.ctl.folderSortReverse !== undefined)
                    ? bar.ctl.folderSortReverse : false
                onTriggered: controller.toggleFolderSortReverse()
            }
        }
        MenuSeparator {}
        // hiányzott (#324 audit): mappa szintű elrejtés/megjelenítés — más,
        // mint a Nézet ▸ Rejtett képek (kép-szintű) kapcsoló
        PicasaMenuItem { text: qsTr("Hide"); placeholder: true }
        PicasaMenuItem { text: qsTr("Show"); placeholder: true }
        MenuSeparator {}
        // hiányzott (#324 audit)
        // #1590: ÉLŐ tétel. A #1472 még szándékosan hagyta helyfoglalónak,
        // mert a `print_controller.py` egy képet tett egy oldalra; a
        // #1590-ben megépült az indexkép-rajzoló (`printing/contact_sheet.py`
        // + `PrintController.printContactSheet`), tehát a tétel mögött MOST
        // MÁR van motor. A rácsot a kollázs indexkép-elrendezése adja, a
        // fejlécet viszont az eredeti NYOMTATÓJA („Album:" / „Dátum:") —
        // a kettő az eredetiben sem azonos.
        MenuItem {
            objectName: "menuFolderPrintContactSheet"
            text: qsTr("Print Thumbnails...") + "\tCtrl+Shift+P"
            onTriggered: bar.printContactSheetRequested()
        }
        MenuItem {
            objectName: "menuFolderWebExport"
            text: qsTr("Export as HTML Page...")
            onTriggered: bar.webExportRequested()
        }
        MenuSeparator {}
        // #1595: a négy tétel a MEGNYITOTT mappára hat. Eddig mind néma
        // helyfoglaló volt, pedig a motorjuk régóta megvan — csak a helyi
        // menüből lehetett elérni őket, a Mappa menüből nem.
        MenuItem {
            objectName: "menuFolderLocate"
            text: qsTr("Locate on Disk") + "\tCtrl+Enter"
            onTriggered: bar.folderLocateRequested()
        }
        MenuItem {
            objectName: "menuFolderRemoveFromPicasa"
            text: qsTr("Remove from Picasa...")
            onTriggered: bar.folderRemoveFromPicasaRequested()
        }
        MenuSeparator {}
        // hiányzott (#324 audit): mappa áthelyezése/törlése a lemezen
        MenuItem {
            objectName: "menuFolderMove"
            text: qsTr("Move...")
            onTriggered: bar.folderMoveRequested()
        }
        MenuItem {
            objectName: "menuFolderDelete"
            text: qsTr("Delete...")
            onTriggered: bar.folderDeleteRequested()
        }
    }
    PicasaMenu {
        title: qsTr("&Picture")
        PicasaMenuItem { text: qsTr("View and Edit") + "\tCtrl+3"; placeholder: true }
        // #425 (K.1 szakasz, ui-audit-menus.md): az almenü teljes tartalma
        // az `eMenuPicture` osztályból ismert — a kijelölt N kép
        // MINDEGYIKÉRE egyszerre alkalmazott egykattintásos effekt
        // (`controller.applyEffectMany`, `batch_effect_controller`).
        PicasaMenu {
            objectName: "menuPictureBatchEdit"
            title: qsTr("Batch Edit")
            enabled: bar.photoActionsEnabled
            MenuItem {
                objectName: "menuBatchAutoContrast"
                text: qsTr("Auto Contrast")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("autolight")
            }
            MenuItem {
                objectName: "menuBatchAutoColor"
                text: qsTr("Auto Color")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("autocolor")
            }
            MenuItem {
                objectName: "menuBatchAutoRedeye"
                text: qsTr("Auto Redeye Fix")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("redeye")
            }
            MenuItem {
                objectName: "menuBatchEnhance"
                text: qsTr("I'm Feeling Lucky")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("enhance")
            }
            MenuItem {
                objectName: "menuBatchSharpen"
                text: qsTr("Sharpen")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("unsharp")
            }
            MenuItem {
                objectName: "menuBatchFilmGrain"
                text: qsTr("Film Grain")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("grain2")
            }
            MenuItem {
                objectName: "menuBatchWarmify"
                text: qsTr("Warmify")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("warm")
            }
            MenuSeparator {}
            MenuItem {
                objectName: "menuBatchRotateRight"
                text: qsTr("Rotate Right")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("rotate_cw")
            }
            MenuItem {
                objectName: "menuBatchRotateLeft"
                text: qsTr("Rotate Left")
                enabled: bar.photoActionsEnabled
                onTriggered: bar.batchApplyEffectRequested("rotate_ccw")
            }
            MenuSeparator {}
            // #425 5. pont: a `docs/specs/` a szöveg-overlay index-
            // lefedettségét nem dokumentálja (van-e a kijelölésben szöveg-
            // réteges kép) — a feltételes engedélyezéshez szükséges adat
            // jelenleg nincs meg olcsón, ezért egyelőre placeholder
            // (ld. `batch_effect_controller` modul-docstring).
            PicasaMenuItem { text: qsTr("Show Text"); placeholder: true }
            PicasaMenuItem { text: qsTr("Hide Text"); placeholder: true }
        }
        // #1774 (mérve): a mentések szerint itt csoporthatár van.
        MenuSeparator {}
        // #465 3. pont: korábban placeholder — a kijelölt kép(ek) teljes
        // szerkesztési láncát törli, megerősítéssel (Main.qml)
        MenuItem {
            objectName: "menuPictureUndoAllEdits"
            text: qsTr("Undo All Edits")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.undoAllEditsRequested()
        }
        MenuSeparator {}
        MenuItem {
            objectName: "menuPictureHide"
            text: qsTr("Hide")
            enabled: bar.photoActionsEnabled
            onTriggered: bar.hideToggleRequested()
        }
        // #1774 (mérve): az eredetiben az Elrejtés MELLETT önálló
        // „Megjelenítés” tétel áll (a mentésen mindkettő inaktív). Nálunk
        // az Elrejtés ma kapcsoló — a szétválasztás külön jegy, addig ez a
        // tétel helyfoglaló, hogy a csoport szerkezete stimmeljen.
        PicasaMenuItem { text: qsTr("Show"); placeholder: true }
        // #1774 (mérve): a mentések szerint itt csoporthatár van.
        MenuSeparator {}
        // hiányzott (#324 audit): arc-négyzetek pozíciójának visszaállítása
        // (3. fázis, arcfelismerés-előkészítés)
        PicasaMenuItem { text: qsTr("Reset Face Positions"); placeholder: true }
        // #1774 (mérve): a mentések szerint itt csoporthatár van.
        MenuSeparator {}
        MenuItem {
            objectName: "menuPictureProperties"
            text: qsTr("Properties") + "\tAlt+Enter"
            onTriggered: bar.propertiesPanelRequested()
        }
    }
    PicasaMenu {
        title: qsTr("&Create")
        // hiányzott (#324 audit)
        PicasaMenuItem { text: qsTr("Set as Desktop Background..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Make a Poster..."); placeholder: true }
        // #1774 (mérve): a mentések szerint itt csoporthatár van.
        MenuSeparator {}
        MenuItem {
            objectName: "menuCreateCollage"
            text: qsTr("Picture Collage...")
            enabled: bar.createActionsEnabled
            onTriggered: bar.collageRequested()
        }
        // hiányzott (#324 audit): OS-integrációs funkciók
        PicasaMenuItem { text: qsTr("Add to Screensaver..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Make a Gift CD..."); placeholder: true }
        // #324 audit („eltérő"): eredetiben almenü — a valódi (működő)
        // filmkészítés a submenu egyetlen tételeként maradt életben
        PicasaMenu {
            title: qsTr("Movie")
            // #922: az ALMENÜ is kapuz — a benne lévő tétel hiába él, ha a
            // szülő szürke. A film ugyanúgy a tálcáról is dolgozik (#455).
            enabled: bar.createActionsEnabled
            MenuItem {
                objectName: "menuCreateMovie"
                text: qsTr("New Movie...")
                enabled: bar.createActionsEnabled
                onTriggered: bar.movieRequested()
            }
        }
        // #1774 (mérve): a mentések szerint itt csoporthatár van.
        MenuSeparator {}
        // hiányzott (#324 audit)
        PicasaMenuItem { text: qsTr("Publish to Blogger..."); placeholder: false; retired: true }  // #638
    }
    PicasaMenu {
        title: qsTr("&Tools")
        MenuItem {
            text: qsTr("Folder Manager...")
            onTriggered: bar.folderManagerRequested()
        }
        // hiányzott (#324 audit) — az auditban jelzett screenshot-időpontban
        // az eredetiben is inaktív volt
        PicasaMenuItem { text: qsTr("Upload Manager..."); placeholder: false; retired: true }  // #638
        PicasaMenuItem { text: qsTr("People Manager..."); placeholder: true }
        MenuSeparator {}
        MenuItem {
            objectName: "menuToolsDedup"
            text: qsTr("Find Duplicates...")
            onTriggered: bar.dedupRequested()
        }
        // #1473: az arckeresés a duplikátum-kereső mellé kerül, mert
        // ugyanaz a fajta munka: az egész könyvtárat végigolvasó, hosszú,
        // megszakítható keresés saját ablakkal. A tétel MINDIG él — ha a
        // modell hiányzik, azt a megnyíló ablak MONDJA MEG; egy szürke
        // menüpont nem tudja megmagyarázni magát (néma tiltás, #1473).
        MenuItem {
            objectName: "menuToolsFaceScan"
            text: qsTr("Find Faces...")
            onTriggered: bar.faceScanRequested()
        }
        MenuSeparator {}
        // hiányzott (#324 audit)
        PicasaMenuItem { text: qsTr("Configure Photo Viewer..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Configure Screensaver..."); placeholder: true }
        // #1774 (mérve): a mentések szerint itt csoporthatár van.
        MenuSeparator {}
        PicasaMenuItem { text: qsTr("Back Up Pictures..."); placeholder: true }
        PicasaMenuItem { text: qsTr("Batch Upload..."); placeholder: false; retired: true }  // #638
        PicasaMenuItem { text: qsTr("Adjust Date and Time..."); placeholder: true }
        MenuSeparator {}
        // hiányzott (#324 audit): a tartalma a screenshotokból nem derül ki
        PicasaMenu { title: qsTr("Upload"); enabled: false }
        // #530: a Geocímke almenü élesedett — az export motorja kész
        // (export/kml.py + earth.py). A feliratok a bináris index szerint:
        // eMenuTools::Geotag = "&Geotag", ID_EXPORT_EARTH =
        // "Export to Google Earth File".
        PicasaMenu {
            title: qsTr("Geotag")
            MenuItem {
                objectName: "menuToolsExportEarth"
                text: qsTr("Export to Google Earth File")
                onTriggered: bar.earthExportRequested()
            }
            // #1589: `eMenuTools::ID_VIEW_EARTH` = „View in Google Earth..."
            // / „Megtekintés a Google Earth programban...". Az export
            // MELLETT áll, mert az eredetiben is két külön tétel ez a
            // kettő: az egyik csak kiírja a fájlt, ez kiírja ÉS megnyitja.
            //
            // ⚠️ MÉRVE, hogy a tétel NEM szürkül el geocímke híján. Az
            // eredeti ilyenkor BESZÉL, nem tilt: `PublishToEarth::NoTagged`
            // („Nincsenek exportálható geocímkézett képek") és
            // `PublishToEarth::Tag` („Nem minden kijelölt elem tartalmaz
            // geocímke jellegű információt… Megcímkézi most a képeket?").
            // Ez egybevág a #1473 döntésével: egy szürke menüpont nem tudja
            // megmagyarázni magát.
            MenuItem {
                objectName: "menuToolsViewEarth"
                text: qsTr("View in Google Earth...")
                onTriggered: bar.earthViewRequested()
            }
        }
        PicasaMenu {
            title: qsTr("Experimental")
            // #368: az eredeti Picasa is a Kísérleti almenüből nyitotta
            MenuItem {
                objectName: "menuToolsMoveDatabase"
                text: qsTr("Move Database...")
                onTriggered: bar.moveDatabaseRequested()
            }
            // #449: adatbázis-tömörítés (`compacting.fen`) — az eredetiben
            // is a Kísérleti almenüben lakott, az áthelyezés mellett
            MenuItem {
                objectName: "menuToolsCompactDatabase"
                text: qsTr("Compact Database...")
                onTriggered: bar.compactDatabaseRequested()
            }
        }
        MenuSeparator {}
        PicasaMenuItem { text: qsTr("Configure Buttons..."); placeholder: true }
        // #1774 (mérve): az eredetiben itt NINCS csoporthatár.
        // #333: nyelvválasztás — alapértelmezés az angol, a magyar
        // választható; a döntés a QSettings-ben marad. A #305-ös null-őr
        // kötelező: a controller a QML-engine leépítésekor null lehet.
        // #1468: a valódi kattintás előbb IMPERATÍVAN átbillenti a `checked`-et,
        // és csak utána dördül el a `triggered`. Kizáró csoportban a MÁR AKTÍV
        // tételre kattintva a vezérlő állapota nem változik, tehát a kötés magától
        // soha nem értékelődik újra — a menü újranyitásakor egyik tételen sem
        // állna pipa. Ezért a jelzés után azonnal VISSZAKÖTJÜK a `checked`-et
        // (a #1464-ben bevezetett minta).
        //
        // Itt a hiba MÉRHETŐ volt: a `LanguageController.setLanguage` azonos
        // értéknél szándékosan NEM jelez, tehát a már aktív nyelvre kattintva
        // mindkét pipa eltűnt.
        PicasaMenu {
            objectName: "menuToolsLanguage"
            title: qsTr("Language")
            MenuItem {
                objectName: "menuLanguageEnglish"
                text: qsTr("English")
                checkable: true
                checked: controller ? controller.language === "en" : true
                onTriggered: {
                    if (controller) controller.setLanguage("en")
                    checked = Qt.binding(function () {
                        return controller ? controller.language === "en" : true
                    })
                }
            }
            MenuItem {
                objectName: "menuLanguageHungarian"
                text: qsTr("Hungarian")
                checkable: true
                checked: controller ? controller.language === "hu" : false
                onTriggered: {
                    if (controller) controller.setLanguage("hu")
                    checked = Qt.binding(function () {
                        return controller ? controller.language === "hu" : false
                    })
                }
            }
        }
        // #1774 (mérve): az eredetiben itt NINCS csoporthatár.
        // #350: az OptionsDialog.qml megépült (9/8 fülős options.fen
        // paritás) — a jelzés itt fut ki, a dialógus példányosítása és a
        // signal bekötése a Main.qml-ben (forró fájl) az integrátoré
        MenuItem {
            objectName: "menuToolsOptions"
            text: qsTr("Options...")
            onTriggered: bar.optionsRequested()
        }
    }
    PicasaMenu {
        title: qsTr("&Help")
        PicasaMenuItem { text: qsTr("Help Contents and Index") + "\tF1"; placeholder: true }
        PicasaMenuItem { text: qsTr("Keyboard Shortcuts"); placeholder: true }
        MenuSeparator {}
        // hiányzott (#324 audit): web-linkek
        PicasaMenuItem { text: qsTr("Picasa Forums"); placeholder: false; retired: true }  // #638
        PicasaMenuItem { text: qsTr("Online Information"); placeholder: false; retired: true }  // #638
        PicasaMenuItem { text: qsTr("Product Release Notes"); placeholder: false; retired: true }  // #638
        // #1774 (mérve): az eredetiben itt NINCS csoporthatár.
        PicasaMenuItem { text: qsTr("Privacy Policy"); placeholder: false; retired: true }  // #638
        PicasaMenuItem { text: qsTr("Terms of Service"); placeholder: false; retired: true }  // #638
        MenuSeparator {}
        PicasaMenuItem { text: qsTr("Check for Updates"); placeholder: true }
        MenuSeparator {}
        MenuItem {
            objectName: "menuHelpPerfMonitor"
            text: qsTr("Performance Monitor")
            checkable: true
            checked: (bar.ctl && bar.ctl.perfMonitorEnabled !== undefined)
                ? bar.ctl.perfMonitorEnabled : false
            onTriggered: controller.togglePerfMonitor()
        }
        // #1654: TARTÓS tesztüzem. A Teljesítmény-monitorral szemben ez
        // TÚLÉLI a kilépést, és a KÖVETKEZŐ indulást naplózza az első
        // ezredmásodperctől — az indulás az egyetlen szakasz, amit
        // menetközbeni kapcsolóval elvből nem lehet megmérni (#1653).
        PicasaMenuItem {
            objectName: "menuHelpTesztuzem"
            // #1701: a tesztüzem a PicasaPy saját eszköze — az eredeti
            // Picasában nincs megfelelője
            placeholder: false
            sajat: true
            text: qsTr("Test Mode (logs the next startup)")
            checkable: true
            checked: (bar.ctl && bar.ctl.tesztuzemEnabled !== undefined)
                ? bar.ctl.tesztuzemEnabled : false
            onTriggered: bar.ctl.toggleTesztuzem()
        }
        // Egykattintásos átadás — CSAK tesztüzemben látszik. A `height`
        // nullázása azért kell, mert a rejtett MenuItem különben üres
        // sávot hagyna a Súgó menüben.
        PicasaMenuItem {
            objectName: "menuHelpSendLog"
            // #1701: a naplóátadás is a miénk — a tesztüzem párja
            placeholder: false
            sajat: true
            // ⚠️ A láthatóság feltétele SAJÁT tulajdonságban él, nem
            // közvetlenül a `visible`-ben: a QQuickItem `visible`-je az
            // EFFEKTÍV láthatóságot adja vissza, ami csukott menünél
            // mindig hamis — a kötés helyessége azon nem mérhető.
            readonly property bool tesztuzemAktiv:
                (bar.ctl && bar.ctl.tesztuzemEnabled !== undefined)
                ? bar.ctl.tesztuzemEnabled : false
            text: qsTr("Send Log...")
            visible: tesztuzemAktiv
            height: tesztuzemAktiv ? implicitHeight : 0
            onTriggered: bar.ctl.tesztuzemNaploAtadasa()
        }
        MenuItem {
            text: qsTr("About PicasaPy")
            onTriggered: bar.aboutRequested()
        }
    }
}
