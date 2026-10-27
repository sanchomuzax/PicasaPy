import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

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
    readonly property var faceScanCtl:
        (typeof faceScanController !== "undefined") ? faceScanController : null
    // #1454: a bal hasáb NÉZETMÓDJA (Egyszerű / Fa / Egyszerűsített fa) a
    // `FolderHierarchyController`-ben él, ami ÖNÁLLÓ context property — nem
    // az `AppController` része. A `typeof`-őr azért kell, mert a menüsávot
    // önmagában betöltő próbák nem regisztrálják.
    readonly property var folderViewCtl:
        (typeof folderHierarchyController !== "undefined")
        ? folderHierarchyController : null

    property bool searchOptionsOpen: false
    signal searchOptionsToggleRequested()

    // #3555: a nyelvváltás megerősítő kérdése a Main.qml-ben él (a
    // ConfirmDialog nem fér el egy MenuBar gyermekeként — annak a default
    // property-je `list<Menu>`). A menütétel csak jelez, ha a választás
    // ELTÉR a mai függő nyelvtől; az azonos tételre kattintás így sem kérdést,
    // sem `setLanguage`-hívást nem indít (a #1468-as rebind ettől függetlenül
    // mindig lefut, ld. fent).
    signal languageConfirmRequested(string code)
    signal writeXmpFacesDialogRequested()
    function requestLanguageChange(code) {
        if (!controller || code === controller.pendingLanguage) return
        bar.languageConfirmRequested(code)
    }

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
        Connections {
            target: bar.ctl
            function onCaptionPasteConfirmationRequested() {
                pasteCaptionReplaceDialog.open()
            }
        }
        Dialog {
            id: pasteCaptionReplaceDialog
            objectName: "pasteCaptionReplaceDialog"
            modal: true
            focus: true
            anchors.centerIn: parent ? Overlay.overlay : undefined
            onAccepted: if (bar.ctl) bar.ctl.confirmCaptionPaste()
            onRejected: if (bar.ctl) bar.ctl.cancelCaptionPaste()

            ColumnLayout {
                spacing: 12

                Text {
                    objectName: "pasteCaptionReplaceMessage"
                    Layout.preferredWidth: 420
                    text: qsTr("Are you sure you want to replace the existing caption with the contents of the clipboard?\n(This operation is not undoable)")
                    wrapMode: Text.WordWrap
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }

                RowLayout {
                    Layout.alignment: Qt.AlignRight
                    spacing: 8

                    PicasaButton {
                        objectName: "pasteCaptionReplaceButton"
                        text: qsTr("Replace")
                        accent: Theme.picasaGreen
                        onClicked: pasteCaptionReplaceDialog.accept()
                    }
                    PicasaButton {
                        objectName: "pasteCaptionCancelButton"
                        text: qsTr("Cancel")
                        onClicked: pasteCaptionReplaceDialog.reject()
                    }
                }
            }
        }
        Connections {
            target: bar.faceScanCtl
            function onFaceResetConfirmationRequested(mode) {
                resetFacesConfirmDialog.openFor(mode)
            }
        }
        Dialog {
            id: resetFacesConfirmDialog
            objectName: "resetFacesConfirmDialog"
            property string resetMode: ""
            property string message: ""
            title: qsTr("Reset Faces")
            modal: true
            focus: true
            anchors.centerIn: parent ? Overlay.overlay : undefined

            function openFor(mode) {
                resetMode = mode
                message = mode === "removeAllFaceData"
                    ? qsTr("WARNING! This will DELETE all face data, people albums, and rescan all photos for faces again. This can REMOVE name tags on synced web albums. Do you want to do this?")
                    : qsTr("WARNING! This will DELETE all people albums, and move all the faces to the unnamed album. This can REMOVE name tags on synced web albums also. Do you want to do this?")
                open()
            }

            onAccepted: {
                if (!bar.faceScanCtl) return
                if (resetMode === "removeAllFaceData")
                    bar.faceScanCtl.removeAllFaceData()
                else if (resetMode === "resetAllFaces")
                    bar.faceScanCtl.resetAllFaces()
                if (bar.ctl) bar.ctl.refreshCollections()
                resetMode = ""
            }
            onRejected: resetMode = ""

            ColumnLayout {
                spacing: 12

                Text {
                    objectName: "resetFacesConfirmMessage"
                    Layout.preferredWidth: 420
                    text: resetFacesConfirmDialog.message
                    wrapMode: Text.WordWrap
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }

                RowLayout {
                    Layout.alignment: Qt.AlignRight
                    spacing: 8

                    PicasaButton {
                        objectName: "resetFacesConfirmButton"
                        text: qsTr("Yes")
                        accent: Theme.picasaGreen
                        onClicked: resetFacesConfirmDialog.accept()
                    }
                    PicasaButton {
                        objectName: "resetFacesCancelButton"
                        text: qsTr("Cancel")
                        onClicked: resetFacesConfirmDialog.reject()
                    }
                }
            }
        }
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
            text: qsTr("Sign in with Google Account")
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
    // van-e fotó-művelet célpontja: a rács kijelölése vagy a néző aktív képe
    property bool photoActionsEnabled: false
    // #5883: a mentés csak a fotóművelet célpontjának mentetlen
    // szerkesztési láncával érhető el.
    property bool photoHasPendingEdits: false
    // #5882: a Kép ▸ Unhide csak rejtett képet tartalmazó célkijelölésnél él.
    property bool hasHiddenPhotoSelection: false
    // A könyvtárhoz kötött műveletek ne váljanak aktívvá a szerkesztőnézetben.
    property bool libraryPhotoActionsEnabled: false
    //: A TextInput/TextEdit aktív fókusza esetén a billentyű a mezőé.
    property bool textEntryHasFocus: false
    // #4335: a kijelölt fedvények állapota a controller INI-lekérdezéséből.
    property bool textOverlayShowEnabled: false
    property bool textOverlayHideEnabled: false
    signal textOverlayStatesRefreshRequested()
    signal textOverlayVisibilityRequested(bool visible)
    //: #1768: a szerkesztő-előnézet aktív-e. Az eredeti a `0x9caa`
    //: parancsot (a Mappakezelő MINDKÉT belépési pontját) a menü
    //: megnyitásakor SZÜRKÍTI, amíg a szerkesztő-előnézet él
    //: (`editpanel/preview`, `FUN_0056e1c0`). Nálunk a szerkesztőpanel a
    //: nézőben lakik, tehát a nyitott néző a megfelelője.
    property bool editorActive: false
    // #922: a Létrehozás-tételek forrása a KÉPTÁLCA is lehet (#455), ezért
    // NEM a `photoActionsEnabled`-ből élnek — az a rácsbeli kijelöléshez
    // kötött 27 fotó-műveletet vezérli, és azoknak tényleg kijelölés kell.
    property bool createActionsEnabled: false
    // #4633: az Emberek-album filmhez nem kell kijelölt kép; a People-modell
    // csak olyan személyalbumokat tartalmaz, amelyeknek van alsó képlistája.
    readonly property bool hasPeopleAlbumMovieSources: {
        var people = bar.ctl ? bar.ctl.people : []
        return people !== null && people !== undefined && people.length > 0
    }
    // #444: van-e a kijelölésben MÁR mentett kép — enélkül a
    // „Visszaállítás" és az „Utolsó mentés visszavonása" értelmetlen
    property bool hasSavedBackup: false
    //: #1637: a rejtettek feloldása jelszóval / a jelszó beállítása
    //: #1421: az eszköztár `folderviewpopup` (▾) gombja UGYANEZT az
    //: almenüt nyitja meg — a bináris `0x005e2000` kezelője a pár
    //: scope-kulcsos függvényét hívja, a tételek a Mappanézet tételei
    //: (`picasa-konyvtar-eszkoztar-viselkedes.md` 4/b). Egy definíció, két
    //: belépési pont: a menü NEM készül újra az eszköztáron.
    function openFolderViewMenu(anchorItem) {
        if (!anchorItem) return
        menuView.openFolderViewMenu(anchorItem)
    }

    signal hiddenUnlockRequested()
    signal hiddenPasswordRequested()
    signal rescanRequested()
    signal aboutRequested()
    //: #1792: a fejlec gombsoranak testreszabasa
    signal configureButtonsRequested()
    //: #671: a Fájl ▸ Kilépés — a gazda dönti el, kérdez-e
    signal exitRequested()
    // #4329: a felső Fájl/Kép/Nézet belépők ugyanazt az útvonalat kérik,
    // amelyet a tálca vagy a kép helyi menüje már használ.
    signal emailRequested()
    signal openInEditorRequested()
    signal viewAndEditRequested()
    // #4622: a Nézet menü visszajelez a gazdának, hogy a nézőből a
    // PhotoViewer szokásos kilépési útján térjen vissza a könyvtárba.
    signal returnToLibraryRequested()
    signal unhideRequested()
    signal resetFacesRequested()
    signal thumbSizePreset(int size)
    // #4623: az aktuális indexképméret a gazdától jön (Main.qml `thumbSize`)
    property int thumbSize: 144
    signal selectStarredRequested()
    signal selectAllRequested()
    signal clearSelectionRequested()
    // #1686: a `Ctrl+I` MÁR MŰKÖDÖTT (Main.qml globális `Shortcut`-ja), csak
    // a menütétel volt helyfoglaló — a funkciót tehát csak az érte el, aki
    // ismerte a billentyűt. A #1616 söprő őre ezt nem foghatta meg: az a
    // helyfoglaló tételeket szándékosan kizárja (ott a felirat nem ígéret).
    signal invertSelectionRequested()
    signal folderManagerRequested()
    // #4334: a név- és Emberek-albumkezelő saját párbeszédablaka.
    signal peopleManagerRequested()
    // #4332: a kijelölt képek felvételi dátumának módosítása.
    signal adjustTimestampRequested()
    // #350: Eszközök → Beállítások... (options.fen) — az OptionsDialog
    // megnyitását a Main.qml köti be (forró fájl, az integrátor dolga)
    signal optionsRequested()
    //: #2054: a súgó megnyitása; a paraméter a fejezet ( = főoldal)
    signal helpRequested(string topic)
    // #4639: a kódban bekötött gyorsbillentyűk helyi listájának megnyitása.
    signal keyboardShortcutsRequested()
    // SAJÁT FUNKCIÓ (#287, jegyzékbe véve: #1364): a Duplikátum-kereső az
    // eredeti Picasa 3.9 Eszközök menüjében NEM létezik
    // (`docs/specs/ui-audit-menus.md`). A másodpéldány-kereséshez az eredeti
    // az importáláskori ellenőrzést és a keresési módot adta (#1398) — ez a
    // párbeszéd a mi hozzáadásunk.
    // #287: Duplikátum-kereső ablak megnyitása (a SAJÁT kezelő-párbeszéd;
    // #1398 óta nem a menüből, hanem a másodpéldány-mód eredménysávjáról)
    signal dedupRequested()
    //: #1398: a MÉRT parancs (`eMenuTools::ID_DUPES`) — keresési MÓDBA vált
    //: (`dupesearch`), párbeszédet NEM nyit. A kezelő-párbeszédhez a módból
    //: vezet tovább út.
    signal duplicateSearchRequested()
    // #1473: Arckeresés — az `Eszközök` menü tétele. Az eredetiben ez nem
    // menüpont volt, hanem alapból bekapcsolt háttérszál
    // (`BgFaceDetectThread`, ld. docs/specs/picasa-arcfelismeres.md 1.1);
    // nálunk háttérmotor híján ez a belépési pont (FaceScanDialog.qml).
    //: #1399/#4689: a hét szín-keresés menüpontja — a szín-token megy át,
    //: a `color:` előtagot a gazda teszi rá (a keresőmező szövege lesz belőle).
    signal colorSearchRequested(string szin)
    //: #1405: a keresés mentése albumként — a gazda dönt a megerősítésről.
    property bool canSaveSearch: false
    signal saveSearchRequested()
    //: #1775: a kijelölt kép asztali háttérképnek — a gazda adja a sort.
    signal wallpaperRequested()
    // #4268: egyetlen kijelölt kép poszterlapokra bontása.
    signal posterRequested()
    //: #1406: a címke albumként — a gazda nyitja a bekérő párbeszédet.
    signal showTagAsAlbumRequested()
    //: #1401: az Útlevélkép — a gazda adja a kijelölt sort, és nyitja a
    //: nyomtatási nézetet (arcfelismerés + kivágás után).
    signal passportPhotoRequested()
    signal faceScanRequested()
    // #368: Eszközök → Kísérleti → Adatbázis áthelyezése
    signal moveDatabaseRequested()
    //: #440: Eszközök ▸ Képek biztonsági mentése… (`ID_TOOLS_BACKUP`)
    signal backupRequested()
    signal compactDatabaseRequested()
    //: #3132: SAJÁT FUNKCIÓ — a régi Picasa adatbázisából (`db3`) vesszük át
    //: a neveket, kulcsszavakat és helyeket a `.picasa.ini`-be. Az eredetinek
    //: nincs ilyen parancsa: ő MAGA a db3 gazdája. A helyét a tulajdonos
    //: választotta (2026-09-18): menüpont, tehát kérésre fut.
    signal picasaDataImportRequested()
    signal renameRequested()
    signal exportRequested()
    // #1616: Fájl ▸ Új album… (Ctrl+N) — a belépő (`openNewAlbum`,
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
    // #5713: Eszközök → Kísérleti → közzététel FTP-fiókra.
    signal ftpPublishRequested()
    // #530: Google Earth-export a kijelölt (geocímkézett) képekből
    signal earthExportRequested()
    // #1589: `ID_VIEW_EARTH` — ugyanaz a KML, de utána MEG IS NYITJA a
    // rendszer társított programjával. Az eredetiben KÉT külön menütétel
    // van; a párbeszédet itt is a hívó (Main.qml) nyitja.
    signal earthViewRequested()
    //: #1404: `eMenuTools::ID_PICTURE_GEOUNTAG` — a geocímkék törlése
    signal clearGeotagRequested()
    // #29: Létrehozás → Képkollázs / Mozgófilm a kijelölésből
    signal collageRequested()
    signal movieRequested()
    //: `eMenuCreateMovie::ID_FACES` — a kijelölt képeket adja át az arcfilm módnak.
    signal faceMovieRequested()
    //: `eMenuCreateMovie::ID_FACESRANDOM` — a nem üres Emberek-albumokat adja át.
    signal peopleAlbumsMovieRequested()
    //: #3503: Létrehozás ▸ Ajándék CD készítése… — a kiadás-panel
    signal giftCdRequested()
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
    //: #3460: a megnyitott mappa — üres, ha nincs (a „Leírás szerkesztése…"
    //: csak mappára vonatkozik)
    property string currentFolder: ""
    // #5882: a mappa Unhide-állapotát a menü megnyitásakor frissítjük,
    // mert az adatbázis-lekérdezésnek nincs QML-értesítő jele.
    property bool folderUnhideEnabled: false
    // #4631: a mappaparancs csak mappanézetben aktív. A controller
    // album- és személynézetben is megőrzi az előző mappát, ezért ezek
    // kizárása a Mappa menütétel és a Ctrl+Enter közös kapuja.
    readonly property bool folderLocateEnabled:
        currentFolder !== "" && currentAlbumToken === ""
        && currentPersonName === ""
    // #4416: a felső Mappa menü Hide/Show tételei ugyanazt a vezérlői
    // műveletet használják, mint a mappa helyi menüje. A két felső tétel
    // külön parancs, ezért csak akkor billentünk, ha az állapot eltér a
    // kért iránytól.
    function setCurrentFolderHidden(hidden) {
        var path = bar.currentFolder
        if (!controller || path.length === 0
                || controller.isFolderHidden === undefined
                || controller.toggleFolderHidden === undefined)
            return
        if (controller.isFolderHidden(path) !== hidden)
            controller.toggleFolderHidden(path)
    }
    // A felirat és a művelet EGYETLEN helyen dől el, hogy a kettő ne
    // csúszhasson el egymástól (a menütétel azt csinálja, amit ígér).
    readonly property string deleteCommandText:
        bar.currentPersonName !== ""
            ? qsTr("Remove from People Album")
            : (bar.currentAlbumToken !== ""
                ? qsTr("Remove from Album")
                : qsTr("Delete from Disk"))
    // #4621: a parancs „album-ági” (a fájl marad) — a néző helyi menüjének
    // felirata ugyanebből a feltételből jön, mint az alábbi elágazás.
    readonly property bool deleteRemovesFromAlbum:
        bar.currentPersonName !== "" || bar.currentAlbumToken !== ""
    // A `Delete` billentyű és a Fájl ▸ tétel KÖZÖS belépője (#1608) — így
    // a kettő nem tud különböző dolgot csinálni. #4621: a néző három
    // belépője (ablak-szintű és saját `Ctrl+Delete`, helyi menü) is ide fut.
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
    signal addToScreensaverRequested()
    signal configureScreensaverRequested()
    signal configurePhotoViewerRequested()
    //: #3460/#4630: Mappa ▸ Leírás szerkesztése… és Album ▸ Albumleírás…
    //: ugyanazt az `album.fen` párbeszédet nyitja a megfelelő nézettel
    signal editFolderDescriptionRequested()
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
    // egyike ("autolight"/"autocolor"/"redeye"/"enhance"/"sepia"/
    // "unsharp"/"bw"/"grain2"/"warm"). A forgatást a meglévő
    // `rotateRightMany`/`rotateLeftMany` út kezeli, közvetlenül a Main.qml-ből.
    signal batchApplyEffectRequested(string name)
    // #465 3. pont: „Undo All Edits" — a kijelölt kép(ek) TELJES
    // szerkesztési láncát törli (a Csoportos szerkesztés almenün KÍVÜL, a
    // Kép menü saját tétele) — megerősítéssel, ld. Main.qml ConfirmDialog.
    signal undoAllEditsRequested()
    //: #1526: a kijelölt képek FÁJLJAI a vágólapra
    signal copyFilesRequested()
    //: #1526: a Beillesztés — a gazda tudja, melyik mappa a cél.
    property bool clipboardHasFiles: false
    //: #5877: a kijelölés első képén van-e Text eszközös szövegréteg.
    property bool hasSelectedTextLayer: false
    //: #5877: van-e beilleszthető Text eszközös réteg a belső pufferben.
    property bool hasTextLayerClipboard: false
    //: #5877: a Text eszköz rétegét kezelő parancsok (a gazda a kijelölésre hívja).
    signal copyTextRequested()
    signal pasteTextRequested()
    signal pasteFilesRequested()
    signal cutFilesRequested()
    // #1595: a Mappa menü négy néma tétele — mind a MEGNYITOTT mappára
    // vonatkozik (az eredetiben a „Mappa" menü ezt jelenti). A vezérlők
    // már megvannak: a mappa-áthelyezés a #457, a lomtárba tétel a #1638,
    // az eltávolítás a #1249, a fájlkezelőben megnyitás a #422 óta.
    signal folderMoveRequested()
    signal folderDeleteRequested()
    signal folderRemoveFromPicasaRequested()
    signal folderLocateRequested()

    // #4639: a súgó csoportcímei a menücímek fordításából jönnek, a
    // billentyűk pedig a tényleges Shortcut.sequence értékekből.
    readonly property string keyboardShortcutsTitle:
        qsTr("&Keyboard Shortcuts").replace("&", "")
    readonly property var keyboardShortcutGroupTitles: ({
        file: menuFile.title.replace("&", ""),
        edit: menuEdit.title.replace("&", ""),
        view: menuView.title.replace("&", ""),
        folder: menuFolder.title.replace("&", ""),
        picture: menuPicture.title.replace("&", ""),
        help: menuHelp.title.replace("&", "")
    })
    readonly property var keyboardShortcutSequences: ({
        file: [shortcutNewAlbum.sequence, shortcutAddFile.sequence,
               shortcutImportFrom.sequence, shortcutDeleteFromDisk.sequence,
               shortcutLocateOnDisk.sequence, shortcutPrint.sequence],
        view: [shortcutSmallThumbnails.sequence,
               shortcutNormalThumbnails.sequence],
        folder: [shortcutPrintContactSheet.sequence]
    })

    // #327: gyorsbillentyűk azoknak az AKTÍV menüpontoknak, amelyeknek
    // még nincs élő bekötésük máshol (a többi már a Main.qml globális
    // Shortcut-jain vagy a menüpont onTriggered-jén keresztül működik —
    // azokhoz itt csak a MENÜBEN LÁTSZÓ felirat tartozik, ld. lent).
    Shortcut {
        id: shortcutSmallThumbnails
        objectName: "shortcutSmallThumbnails"
        sequence: "Ctrl+1"
        enabled: !bar.editorActive && !bar.textEntryHasFocus
        onActivated: bar.thumbSizePreset(96)
    }
    Shortcut {
        id: shortcutNormalThumbnails
        objectName: "shortcutNormalThumbnails"
        sequence: "Ctrl+2"
        enabled: !bar.editorActive && !bar.textEntryHasFocus
        onActivated: bar.thumbSizePreset(144)
    }
    Shortcut {
        id: shortcutLocateOnDisk
        objectName: "shortcutLocateOnDisk"
        sequence: "Ctrl+Return"
        // #4631: a kijelölt kép elsőbbséget élvez; üres kijelölésnél a
        // megnyitott mappát mutatja. Mindkét ág a megfelelő menütétel
        // engedélyezési feltételét használja.
        enabled: (bar.photoActionsEnabled || bar.folderLocateEnabled)
                 && !bar.textEntryHasFocus
        onActivated: {
            if (bar.photoActionsEnabled)
                bar.locateRequested()
            else if (bar.folderLocateEnabled)
                bar.folderLocateRequested()
        }
    }
    Shortcut {
        id: shortcutDeleteFromDisk
        objectName: "shortcutDeleteFromDisk"
        sequence: "Delete"
        // A menüpont a nézőben is aktív, de a néző saját gyorsbillentyűje
        // Ctrl+Delete (#1418). A sima Delete csak a könyvtári belépő.
        enabled: bar.photoActionsEnabled && !bar.editorActive
                 && !bar.textEntryHasFocus
        // #1608: nézetfüggő — albumban NEM töröl lemezről
        onActivated: bar.activateDeleteCommand()
    }
    // #1472: a Ctrl+P eddig SEHOL nem létezett — a menüfelirat hirdette,
    // de billentyű nem tartozott hozzá. A feliratot itt szó szerint
    // követjük (nem `StandardKey.Print`), hogy a kettő ne csúszhasson el.
    Shortcut {
        id: shortcutPrint
        objectName: "shortcutPrint"
        sequence: "Ctrl+P"
        enabled: bar.photoActionsEnabled && !bar.textEntryHasFocus
        onActivated: bar.printRequested()
    }
    // #1590: a Mappa-menü felirata Ctrl+Shift+P-t hirdet
    // (`docs/specs/picasa-gyorsbillentyuk.md` 25. sora is ezt mondja) —
    // ne maradjon puszta felirat, ahogy a Ctrl+P is az volt a #1472-ig.
    // A Mappa-parancs az aktuális mappára hat, ezért kijelölés nélkül is
    // ugyanúgy él, mint a menütétel.
    Shortcut {
        id: shortcutPrintContactSheet
        objectName: "shortcutPrintContactSheet"
        sequence: "Ctrl+Shift+P"
        enabled: !bar.textEntryHasFocus
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
        id: shortcutImportFrom
        objectName: "shortcutImportFrom"
        sequence: "Ctrl+M"
        enabled: !bar.editorActive && !bar.textEntryHasFocus
        onActivated: bar.importSourceRequested()
    }
    // #1633: a Fájl-menü felirata Ctrl+O-t hirdet — ugyanaz a
    // hibaosztály, mint a Ctrl+M volt a #1615 előtt. Feltétel nélkül él,
    // mint maga a menüpont (a fájlválasztó nem függ kijelöléstől).
    Shortcut {
        id: shortcutAddFile
        objectName: "shortcutAddFile"
        sequence: "Ctrl+O"
        enabled: !bar.editorActive && !bar.textEntryHasFocus
        onActivated: bar.addFileRequested()
    }
    // #1616: a Fájl-menü felirata Ctrl+N-et hirdet — ugyanaz a hibaosztály,
    // mint a Ctrl+M/Ctrl+O volt. A kijelölés-függés (`photoActionsEnabled`)
    // itt SZÁNDÉKOS, eltérően a Ctrl+M/Ctrl+O-tól: a `createAlbum` üres
    // kijelölésnél nem hoz létre semmit (üres tokent ad vissza), tehát a
    // billentyűnek sincs mit csinálnia — ugyanaz a feltétel, mint a
    // menütételen.
    Shortcut {
        id: shortcutNewAlbum
        objectName: "shortcutNewAlbum"
        sequence: "Ctrl+N"
        enabled: bar.photoActionsEnabled && !bar.textEntryHasFocus
        onActivated: bar.newAlbumRequested()
    }

    PicasaFileMenu {
        id: menuFile
        bar: bar
    }
    PicasaEditMenu {
        id: menuEdit
        bar: bar
    }
    PicasaViewMenu {
        id: menuView
        bar: bar
        controllerRef: ctl
    }
    PicasaFolderMenu {
        id: menuFolder
        bar: bar
        controllerRef: ctl
    }
    PicasaPictureMenu {
        id: menuPicture
        bar: bar
    }
    PicasaCreateMenu { bar: bar }
    PicasaToolsMenu { bar: bar }
    PicasaHelpMenu {
        id: menuHelp
        bar: bar
        controllerRef: ctl
    }
}
