# A Hangolás lap folyamata: eredeti Picasa 3.9 és PicasaPy (#7345)

**Állapot: a J0-J7 Colab-felvételek kiértékelve (zárókör 2), a jegy lezárható hat megnevezett futásmérési hiánnyal.** A 23 tételből 17 lezárva (ebből hat igazolt eltérés: két korábbi, T1 és T2, és négy új tétel, amelyekhez három új jegytörzs, T3, T4, T5 tartozik a „J1-J7 eredménye" szakaszban), 6 blokkolt, mindegyikhez kész javított Colab-lépéssor vagy megnevezett végrehajtói hiány tartozik. A zárókör 1 állapota: a statikusan eldönthető pontok lezárultak (a Gyakori javítások Derítőfény-csúszkája `fill`, nem `finetune2` - #7369 óta kint; a pipetta fülbe lépéskor kikapcsol - #7370 óta kint). Az első kör állapota: az eredeti teljes futásút (egy/több kijelölt kép, húzás közbeni előnézet, `.picasa.ini` írásának időpontja, Undo/Redo és a kép mentése) nincs egyetlen lépéssorban lemérve; ezt a J0-J7 felvételek pótolták.

## Bizonyítékmérce és korábbi anyagok

Átnéztem a `grep -rn "job-[0-9]" docs/specs/` 830 találatát és a `grep -rln 'tuning\|Fill Light' docs/specs/` eredményeit. A kapcsolódó mérések a Tuning-fül képét, a menü- és billentyűleltárt, illetve a szűrőlánc formátumát fedik le; teljes, Tuning-lépéssorról készült eredeti futásmérést nem találtam. A #375 eredeti Picasa 3.9 felvétele **egy kijelölt képpel** a `Ctrl+3` utáni nyitást rögzíti; a 2026-07-17-i panelkép a 2. fület mutatja. A `paritas-folyamat-7327.md` az Alapvető javítások eszközeiről és azok nyitott futásméréseiről szól, nem fedi le ezt a teljes Hangolás-folyamatot.

Felhasznált korábbi spec-lapok: `picasa-effekt-nevek.md`, `picasa-effekt-feliratok.md`, `filterdesc-registry.md`, `filters-decoded.md`, `picasa-ini-format.md`, `picasa-gyorsbillentyuk.md`, `picasa-menu-parancsok-viselkedes.md`, `ui-audit-editor.md` és `ui-audit-context-menus.md`.

### A jegy bináris horgonya hibás

A jegyben megadott `0x00559150` nem a szerkesztőfülek táblája. A közvetlen disassembly részlete:

```text
0x0055918f  push 0xc8c7a4 ; "eMenuFile::ID_FILE_NEWLABEL"
0x00559194  mov eax, 0xc8c7c0 ; "&New Album..."
```

Az SQLite index `FUN_00559150`, `.text`, 15495 bájtos függvényt ad erre a címre; a már meglevő Ghidra-kimenet a `CreateMenu` és `SetMenu` hívásokat is ehhez a függvényhez kapcsolja. Ez menüsor-építő. A Tuning-fül rekordja az `editpanel.tre` `editpanel/tab2` része: a `showtarget` az `editcontrol_well` és `tabpanel2` elemekre mutat (`ui-audit-editor.md:3547-3553`); a panelváltó kódjának string-hivatkozása `0x0057bb50`. Ez azonosítja a fül erőforrását, nem indokolja a `0x00559150` átnevezését „fültáblára”.

## Eredeti / nálunk / teendő

| Eredeti (bináris cím vagy mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Belépés egy képpel.** `Ctrl+3` (`thumbui/fullview`, `0x005e624f`) és a menüparancsok `0x9c8f` / `0x9ca0` a nagy képes nézőt nyitják. A #375 eredeti mérésben egy kijelölt képpel a néző az **Alapvető javítások** füllel nyílik meg (`picasa-gyorsbillentyuk.md:475, 2340`). Ezután a Hangolás a második fül. | `MainKeyboardShortcuts.qml:116-125` a `Ctrl+3`-at a `nezdEsSzerkeszd()` hívására köti; `PicasaViewMenu.qml:62-73` és `PicasaPictureMenu.qml:9-14` ugyanerre vezet. `MainWindowLibraryActions.qml:95-100` csak nem üres kijelölésnél nyit nézőt; `EditorPanel.qml:60` kezdeti `activeTab: 0`, `EditorTabHost.qml:89-100` a Tuning-fület `activeTab === 1`-hez köti. | Az egyképes menü- és gyorsbillentyűút forrása egyezik a #375 nyitó állapotával. A közvetlen Hangolásra mutató külön menüparancsot nem azonosítottam. Külön gyorsbillentyű hiányát nem állítom mérés nélkül. |
| **Indexkép helyi menüje / Enter.** A félkövér `Megjelenítés és szerkesztés` tétel `Enter`-rel nyitja a nézőt (`ui-audit-context-menus.md:101-121`; `picasa-gyorsbillentyuk.md:475`). Ez a nézőbe lépés, nem közvetlen Hangolás-parancs. | `LightboxFeed.qml:401-410` Return/Enterre a kiválasztott indexet nyitja; `MainLibraryCanvas.qml:387-395` a dupla kattintás és a kép-helyi menü eseményeit kezeli; `MainPhotoContextMenu.qml:110-118` a beépített nézőt nyitja. A `picasa-gyorsbillentyuk.md:673-675` történeti Enter-jegyzete elavult, mert a jelenlegi QML már beköti az Entert (#1417). | Az Enter és a menü útja kódban megvan. PicasaPy-futtatási próba ebben a kutatási körben nem készült. Az eredeti dupla kattintás kimenetét külön futásmérés nem igazolta. |
| **„Fájl(ok) megnyitása szerkesztőben” / `Ctrl+Shift+O`.** A már feltárt parancs a rendszer fájltársításán keresztül külső alkalmazást nyit; nem a beépített Tuning-panel belépője (`picasa-menu-parancsok-viselkedes.md`, „Fájl(ok) megnyitása szerkesztőben”). | A beépített út a `Ctrl+3`, a Nézet/Kép menü, az indexkép Enterje és a dupla kattintás. A `MainPhotoContextMenu.qml:116-119` külső fájlmegnyitást külön kezel. | A külső szerkesztőparancsot ne számítsuk a Tuning fül belépési pontjának. |
| **Többes kijelölés.** A meglévő eredeti #375 felvétel csak egy képet vizsgált; a többes kijelölésnél a menük engedélyezése, a megnyitott kép és a Tuning-módosítás célja: **NINCS MEG**. | `MainWindowLibraryActions.qml:95-100` a menü/`Ctrl+3` útban a `selectedRows()[0]` elemet nyitja. Az Enter-út a `LightboxFeed.qml:407-409` `selectedIndex` értékét használja. A kép-helyi menü a `fileOpTargetRow` értékét adja át (`MainPhotoContextMenu.qml:110-113`). | E kódutakból a PicasaPy célképe leolvasható; az eredeti többes kijelölés kimenetét nem lehet statikus UI-leletből megállapítani. Colab-mérés szükséges, eltérést addig ne nyissunk. |
| **Vezérlők és alapállapot.** Az eredeti 2. fül 2026-07-17-i képe négy csúszkát (Derítőfény, Kiemelések, Árnyékok, Színhőmérséklet), semleges színmintát, pipettát, két pálcát, alul Visszavonás/Újra gombokat mutat; az üres állapotban a gombok inaktívak (`ui-audit-editor.md:33-38, 754-858`, mérés: `2026-07-17 20 56 42.png`). Az erőforrásfa ugyanebben a közös `editcontrol_well`-ben négy csúszkát, pipettát és közös `ok`, `cancel`, `eraserbutton` elemeket sorol fel (`ui-audit-editor.md:3547-3605`). A statikus erőforrás önmagában nem bizonyítja, hogy az utóbbi gombok mikor láthatók a Hangolás fülön. | `EditorFinetunePanel.qml:128-264` négy csúszkát, semleges színmintát/pipettát és két pálcát tartalmaz. `EditorPanel.qml:369-382` globális Undo/Redo sort ad. A Hangolás QML-ben nincs saját Cancel vagy Reset vezérlő. | Az alap képernyőleltár egyezik. Eredeti `ok`/`cancel`/radír láthatósága és művelete slider-módosítás után, valamint Reset jelentése: **NINCS MEG**. Ne tekintsük az erőforrásfában való jelenlétet látható gombnak. |
| **Csúszkák tartománya és nullás állapota.** A Picasa 3.9.141.259 `runtime/filterdesc.xml` `finetune2` rekordja (`:142-165`) `Fill Light 0..1`, `Highlights 0..0.48`, `Shadows 0..0.48`, `Color Temperature -1..1` tartományt és `zerostate="zero"` értéket ad. A legacy `finetune` hőmérsékleti tartománya `-0.5..0.5` (`:115-139`). A panelképen a három első csúszka bal szélen, a hőmérséklet középen áll. | `EditorFinetunePanel.qml:128-193, 207-222` szó szerint a `finetune2` tartományokat, mind a négy csúszkán `value: 0` értéket állítja be. A mentett értékeket a `PhotoViewerEditorPanel.qml:57-62` a kontrollerből tölti. | A `finetune2`-tartományok és a PicasaPy bekötése egyezik. A `filterdesc.xml` nem ad lépésközt; az eredeti pontos egér-lépésköz és a memorizált értékek futó váltáskor **NINCS MEG**. |
| **Billentyűs csúszkalépés.** `0x005f95d0` először a panel fülét vizsgálja: `cmp eax,3` / `jb` és `cmp eax,5` / `ja` alapján csak a 3-5. fülön enged tovább. `0x005d2290` `+`/`=` esetén a `0xcf50d8`, `-`/`_` esetén a `0xcf50d4` konstansból léptet; a meglévő specifikáció ezeket `+0.02` / `-0.02`-ként olvassa (`picasa-gyorsbillentyuk.md:1182-1183`, §10.13-10.14). Ez nem a 2. Hangolás fül lépése. | `EditorParamPanel.qml:342-347,462-467` csak `activeTab` 2-4 esetén engedi a billentyűs léptetést; `PicasaSlider.qml:92-110` csak engedélyezés után kezeli a `+`, `=`, `-`, `_` karaktereket. A `EditorFinetunePanel.qml` nem kapcsolja be ezt a módot. | A Hangolás billentyűs léptetése nincs engedélyezve egyik oldalon sem; a 0.02 nem állítható be a Tuning-csúszkákra. Más, egérrel végzett finom lépés nagysága **NINCS MEG**. |
| **Előnézet, lánc és mentés.** A regiszter és ini-formátum alapján a szerkesztési lánc `finetune2=1,fill,highlights,shadows,szín(8 hex),temperature`; valós ini-példa szerepel a `picasa-ini-format.md:143, 272-291` szakaszban. Ez az adatmodell, nem bizonyíték arra, hogy eredetiben a lánc pontosan húzáskor, elengedéskor vagy mentéskor íródik. Eredeti preview-időzítés, fájlmentés és műveleti határ: **NINCS MEG**. | `EditorFinetunePanel.qml:141-143,171-175,190-193,219-221` húzáskor előnézetet, felengedéskor véglegesítést indít. `PhotoViewerEditorPanel.qml:70-88` a preview-t `previewFinetune`/`previewFinetuneGpu` felé, a commitot `setFinetune` felé vezeti. `edit_controller_effects_finetune_mixin.py:114-128` preview-ja nem ír ini-t és nem tesz Undo-lépést; `:170-199` commitja Undo-t készít, `finetune2`-t ment vagy nullás csúszkáknál törli. `edit_controller_save_mixin.py:162-210` a `filters` sort a közös ini API-n írja ki. | A mai PicasaPy-kód útja bizonyított; az eredeti út nem. Mentéskor az eredeti kép módosítása, backupja, ini- és exportállapota csak párban futtatott mérésből dönthető el. |
| **Undo/Redo, Cancel és Reset.** A felvétel a tiszta állapotban letiltott Undo/Redo-t mutatja; a művelet utáni veremhatárt és a közös `ok`/`cancel`/`eraserbutton` viselkedését nem rögzíti. Reset/Mégse után lánc, előnézet, fájl, illetve következő képre váltás: **NINCS MEG**. | `edit_controller_history_mixin.py:59-84` Undo/Redo-ra az előző/új szerkesztési láncot állítja vissza és azonnal `_save()`-ot hív. `setFinetune` (`edit_controller_effects_finetune_mixin.py:170-192`) négy nulla csúszkánál törli a teljes `finetune2` réteget. A `picasa-ini-format.md:279-289` ugyanakkor érvényes p4 semleges színt is dokumentál nullás slider-értékek mellett, például `finetune2=1,0,0,0,006b8088,0`. | Ez konkrét mai kódbeli él: a négy csúszka nullára véglegesítése a tárolt semleges színrekeszt is eltávolíthatja. Az eredeti viselkedés slider-nullázáskor **NINCS MEG**, ezért ez egyelőre vizsgálandó jelölt, nem igazolt paritáshiba és nem fejlesztői jegy. |

## Bizonyítottsági fok és független utak

**A út: eredeti bináris és erőforrások.** A `0x00559150` célzott utasításszintű olvasása és a korábbi Ghidra-kimenet menüsor-építőt azonosít. Külön, a Tuning-fülre irányítva a `0x005f95d0` őr és a `0x005d2290` karakterkezelő a billentyűléptetés hatókörét határolja. A szállított `filterdesc.xml` és `editpanel.tre` adja a szűrőtartományokat és a panel erőforrás-kapcsolatait.

**B út: futó eredeti UI-mérések, korpusz és PicasaPy-forrás.** A #375 felvétel egyképes `Ctrl+3` állapotot mutat; a 2026-07-17-i kép a Tuning UI-ját mutatja. A korpusz/spec dokumentálja a `finetune2` ini-alakot; a PicasaPy QML/controller kódja önállóan megmutatja az aktuális tab- és mentési útvonalakat.

**Egyezés és fok.** A billentyűkapu / Tuning-lépés és a látható vezérlők leltára egyezik a két úton. Az eredeti preview-lánc-fájl-Undo teljes folyamatról viszont nincs B útból futásmérés, így a jegy egészének bizonyítottsága **nyitott**; részmegállapításként az egyképes belépés és a panel leltára **feltételes**, a binárisból közvetlenül kiolvasott függvény- és őrfeltételek **megerősítettek**. A három fogalmat nem terjesztem ki a teljes futásra.

## Cáfoló kísérlet

**Állítás, amit cáfolni próbáltam:** `0x00559150` a szerkesztőfülek táblája. A függvényt közvetlenül szétszedtem, majd a meglévő Ghidra-kimenetben cím szerint ellenőriztem. A `0x0055918f`/`0x00559194` `eMenuFile::ID_FILE_NEWLABEL` / `&New Album...` rekordot ír, a Ghidra-kimenet `CreateMenu`/`SetMenu` hívásokat társít hozzá. A cáfoló ellenőrzése az SQLite `functions` bejegyzés `.text` szakasza és az `editpanel.tre` `tab2` külön erőforrása: mind ugyanazt támasztja alá. **A jegy horgonycíme hibás.**

**Második cáfoló próba:** próbáltam cáfolni, hogy az eredeti `+`/`-` lépés a Hangolás fülön is működik. A `0x005f95d0` belépő-őre elutasítja a 2. fület és csak a 3-5. indexet engedi; a PicasaPy `EditorParamPanel.qml` ugyanígy tiltja az 1-es (Hangolás) tab-indexet. A billentyűs lépésből tehát nem következik Hangolás-eltérés.

## A jegy „Kész, ha” pontjai

1. ⛔ **Belépési pontok és kijelölési feltételek:** egyképes `Ctrl+3` eredeti mérése és a menü/Enter utak dokumentáltak; többes kijelölés és a közvetlen Hangolás-billentyű/menü futáspróbája `NINCS MEG`.
2. ⛔ **Vezérlők, alapérték, lépés és megjegyzett állapot:** négy csúszka, pipetta, pálcák és Undo/Redo sor; a `finetune2` nullás állapot és tartomány adott. Egér-lépésköz, csúszkahúzás utáni gombállapot és képváltáskor megjegyzett állapot `NINCS MEG`.
3. ⛔ **Előnézet, `.picasa.ini`, mentett fájl, Undo és Redo:** PicasaPy-kód útja forrásból feltárt; eredeti teljes futásmérés és a mentett képfájl/backup párja `NINCS MEG`.
4. ⛔ **Több kijelölés, Mégse/Alaphelyzet és mentés:** eredeti többes kijelölés, Tuning-panel Reset/Mégse állapota és ezek utáni fájl-/lánchatás `NINCS MEG`.

## Colab-lépéssor a nyitott pontokhoz

Eredeti Picasa 3.9-ben, friss tesztprofillal és másolati tesztképekkel, minden lépés előtt/után rögzíts képernyőképet, ablakállapotot, kijelölést, `.picasa.ini`-t, exportképet és fájl-hasítóértéket:

A felvétel a privát eszköztár `~/picasapy-agent/eszkozok/colab_felmero.py` segédjével készüljön; töltsd le a `kepernyokep`, `ablakmeret`, `allapot`, `picasa_ini` és `export` kimeneteket. A `db3` mentése csak akkor szükséges, ha a művelet az index állapotát is láthatóan megváltoztatja.

1. Könyvtárnézet kijelölés nélkül, egy képpel és két képpel: nyisd meg külön-külön a Nézet menü `Ctrl+3`, Kép menü `Ctrl+3`, indexkép-helyi menü Enter, dupla kattintás és `Ctrl+Shift+O` útját. Jegyezd fel, mi tiltott, hova nyílik és hány képet érint.
2. Egy képpel lépj a második, Tuning fülre. Rögzítsd a csúszkák és gombok állapotát, majd próbáld a `+`, `=`, `-`, `_` karaktereket fókuszált csúszkán. Mozgasd külön-külön mind a négy csúszkát bal szélre, középre, jobb szélre és vissza. Fényképezd le a panelt a húzás alatt és felengedés után.
3. Minden változás után olvasd vissza az érintett kép `filters=` sorát és az eredeti fájl hashét. Kattints Undo, Redo, képre váltás, majd vissza; írd fel, mi marad a panelen és az ini-ben.
4. Nézd meg, megjelenik-e a közös `ok`, `cancel`, radír/reset gomb slider-húzás után. Ha megjelenik, külön tiszta indulásból próbáld, és minden gomb után rögzíts panelt, ini-t, képet, hash-t és undo/redo állapotot. Ha nem jelenik meg, jegyezd fel, hogy nincs Tuning-módú Cancel/Reset.
5. Húzd a csúszkákat nullára egy külön olyan másolaton, ahol már van semleges-szín p4 érték. Ezután mentsd a képet a Picasa mentési parancsával; rögzítsd a `.picasa.ini`, eredeti fájl, backup és export változásait. A lépés eldönti a jelenlegi kódban észlelt p4/nullázási kérdést.

## Következtetés és jegyjavaslat

*(Az első kör következtetése; a zárókör és a zárókör 2 felülírja.)* Az első körben nem volt bizonyított, felhasználó számára látható Hangolás-eltérés, ezért fejlesztői jegytörzset nem javasoltam. A zárókör két eltérést igazolt (T1, T2; mindkettő kint van: #7369, #7370). A zárókör 2 (J0-J7 felvételek) három további eltérést igazolt, mindhárom látható: **T3** a Hangolás-csúszkák modellje (alaphelyzet, egy Undo-lépés látogatásonként, új réteg a betöltött mellé), **T4** a pipetta (forrásszín, képváltás), **T5** a `Ctrl+3` kijelölés nélkül és többes kijelölésnél; kész jegytörzsük a „J1-J7 eredménye" szakaszban van. A T1 3. kész-feltétele megdőlt (a csúszka nyitáskor alaphelyzetben áll). A #7345 kutatási jegy lezárható: a maradék hat tételhez kész javított lépéssor (B1, B2a-c, B4a-d, B4u, B5a-b, B6) vagy megnevezett végrehajtói hiány (B7) tartozik, ezekből új felvételi jegy nyitandó.

**Forrásfájlok:** `docs/specs/paritas-folyamat-7345.md` (ez a lap), valamint a hivatkozott meglévő PicasaPy-forráshelyek. Ebben a körben kód, teszt vagy más spec-lap nem változott.

## Zárókör

**Következtetés.** A Hangolás fül folyamatának statikusan eldönthető része lezárult. Két igazolt eltérés van, mindkettő a binárisból és a PicasaPy forrásából egymástól függetlenül adódik:

1. **A Gyakori javítások Derítőfény-csúszkája az eredetiben a `fill` szűrőt szerkeszti, a Hangolás fül csúszkái a `finetune2`-t.** Nálunk egyetlen `finetune2` réteg a közös állapot (T1 jegytörzs lent).
2. **Az eredeti a Hangolás fülre lépéskor kikapcsolja a pipettát.** Nálunk a pipetta fülváltás után is élesen marad, és más fülön is mintát vesz (T2 jegytörzs lent).

Az első kör több állítása megerősödött (billentyűs léptetés nincs a fülön, Alkalmaz/Mégse nincs a fülön, a csúszkák tartománya és kiosztása egyezik, szám nincs kiírva). Hét pont csak futásméréssel dönthető el: ezek BLOKKOLT besorolást és kész Colab-lépéssort kapnak (J1-J7). Az eredetileg hibás `0x00559150` horgonyt a lap korábbi szakasza már kijavította, ezt a kör nem érinti.

### A `[panel+0x3378]` mező jelentése (az első kör állításának megerősítése)

A mező a szerkesztő **aktuális fülének 1-alapú sorszáma**, nem nézetkód. Bizonyíték (mind közvetlen utasítás-olvasás):

```text
0x005d77b4  mov dword ptr [esi+0x3378], 1     ; 0x005d7780: az 1. fül belépője
0x005d78b7  mov dword ptr [eax+0x3378], 2     ; 0x005d77d0: a 2. (Hangolás) fül belépője
0x0057de60  mov eax,[eax+0x3378] ; test eax,eax ; jne ; mov eax,1 ; push eax
0x0057de73  push 0xc87014 ("editpanel/tab%d")  ; a mező 0-nál 1-re esik vissza
```

A `0x005f95d0` őr ezért a 3-5. fülön (effektfülek) enged tovább, a 2. fülön az első `cmp eax,3` / `jb 0x5f967c` (`0x005f95d9`, `0x005f95df`) nullával tér vissza: a `+`/`-` csúszkalépés a Hangolás fülön nincs. Ez egyezik a PicasaPy-val (`EditorParamPanel.qml:342-347,462-467`, `PicasaSlider.qml` `keyboardStepEnabled: false` alapérték).

### Új bináris tények

| # | Tény | Bizonyíték | Fok |
|---|---|---|---|
| F1 | A Hangolás fülön az **Alkalmaz/Mégse gomb rejtett**. A csúszkákat felépítő `0x00750ff0` a szűrő módját (`vtable+0x14`, a `filterdesc.xml` `mode` egésze) a `[ebx+0x54]`-be teszi. `cmp [ebx+0x54], 4` (`0x007513e7`): csak az `effect` módnál (4) hívja a `editpanel/cancel` és `editpanel/ok` elem `vtable+0x6c` (megjelenítő) metódusát és rejti a `fxthumbs` rácsot (`0x007513fa-0x0075143f`). Minden más módnál (a `finetune2` módja `soft` = 5, `filterdesc-registry.md` 1378-1388. sor) a `vtable+0x68` (elrejtő) metódust hívja mindkét gombra (`0x0075144a-0x0075147f`). Az `editpanel.tre` is `m_hidden`-nel adja a gombokat. | `0x00750ff0` utasításai; a `+0x6c` megjelenítő és `+0x68` elrejtő pár olvasata ugyanaz a többi helyen is: a `0x007522a0` megjeleníti (`0x007522f3`), a `0x005f8520` elrejti (`0x005f8634`) a `editpanel/puck` elemet, a `0x007518e0` elrejti a `eraserbutton` elemet (`0x00751b49`) | erős |
| F2 | A **radír** a Hangolás fülön rejtett. A `eraserbutton` az `.tre`-ben `m_hidden` (`editpanel.tre:501-503`); a `0x007518e0` minden vezérlőt elrejtő alaphelyzet-függvénye is elrejti (`0x00751b49-0x00751b5e`). A sztring bájtszintű, indextől független pásztázása (`.text` szakasz, `0xc86fbc` literál): 6 találat, `0x0050c817`, `0x0050e106`, `0x005d6ffb`, `0x005d700d`, `0x005d703e`, `0x00751b4a`, vagyis a Hangolás-belépő (`0x005d77d0`), a pipetta-kezelők (`0x005f8380`, `0x00752800`) és a `0x00750ff0` egyike sem hivatkozik rá. | bájtpásztázás + `.tre` | erős |
| F3 | A Hangolás fülre **lépéskor a pipetta kikapcsol**. A `0x005d77d0` megkeresi a `editpanel/droppertoggle` gombot, és ha be van kapcsolva (`cmp byte ptr [ebx+0x359], 0` `0x005d7810`), nullázza az állapotot jelző bájtot (`0x005d781f mov byte ptr [ebx+0x359], 0`), és kiadja a gomb `buttontoggle` eseményét (`0x005d7833`, `0x005d7866`). A `0x005f8380` a gomb állapotát a szűrőkezelő interakciós módjává alakítja: `0x005f84ee-0x005f8502` (`mov cl,[eax+0x359] ; neg cl ; sbb ecx,ecx ; and ecx,2 ; push ecx ; call 0x7522a0`), vagyis bekapcsolva 2, kikapcsolva 0. | `0x005d77d0`, `0x005f8380` | erős |
| F4 | A pipetta **egyszeri használatú**: a kép-egéresemény kezelője (`0x00752800`) akkor, ha az aktív szűrő neve `colorfix`, `finetune` vagy `finetune2` (`0x00752883-0x00752978`) és az esemény jelzője nem nulla (`0x0075297f`), a bekapcsolt pipettagombra rákattint (`0x007529c0 mov edx,0xc871ac ; call 0x9cd8a0`; a `0x009cd8a0` név szerint megkeresi a gombot és a `vtable+0x78` kattintás-metódusát hívja). | `0x00752800`, `0x009cd8a0` | erős |
| F5 | A **1. fül aktív szűrője a `fill`, a 2. fülé a `finetune2`.** `0x005d7780`: `0x005d77ad push 0xc87128` (a sztring bájtjai: `fill`), `0x005d77be call 0x5f8520`. `0x005d77d0`: `0x005d78b2 push 0xc962b8` (`finetune2`), `0x005d78c1 call 0x5f8520`. A `0x005f8520` az aktív szűrőt név szerint állítja be. | `0x005d7780`, `0x005d77d0`, `0x005f8520` | erős |
| F6 | A **csúszkaesemények a Derítőfény-csúszkát az aktív szűrő 0. paraméterére kötik**: a `0x005de8e0` diszpécser a `editslider1/editslider` (`0x005dfbbd`), a `toolslider/toolslider` (`0x005dfbf6`) és a `flightslider1/scaleslider` (`0x005dfc2f`) egyezésekor ugyanarra a `0x005e04b5` címre ugrik (`push 0 ; call 0x5d21a0`), a `editslider2..4` a 1..3 indexre (`0x005dfc96`, `0x005dfcd7`, `0x005dfd18`). A `0x005d21a0` az indexet a `0x00751d20`-nak adja, az pedig az aktív szűrő (`[[mgr+0x70]+0x164]`) `vtable+0x50` metódusával állítja a paramétert (`0x00751d4d`, `0x00751d99`). A Gyakori javítások Derítőfény-csúszkája ezért az 1. fül aktív szűrőjét, a `fill`-t szerkeszti. | `0x005de8e0`, `0x005d21a0`, `0x00751d20` | erős |
| F7 | A csúszka **kétféle eseményt** kezel. Értékváltáskor a `0x00751d20` először `vtable+0x4c(1)`-et hív (`0x00751d59`), majd beállítja a paramétert; a másik eseménytípusnál (`[esi+0x20] == 0x8000001`, `0x005d21f0`) `vtable+0x4c(0)`-t (`0x005d2210-0x005d2215`) és az Undo/Redo/WriteToDisk állapotot frissítő `0x00567680`-at hívja (`0x005d2217-0x005d221b`; a `0x00567680` a `filter_undo`, `filter_redo`, `writetodisk` elemeket kezeli, `0x0056770e-0x0056772c`). A `vtable+0x4c` a `CGenericFilter` `+0xc8` bájtját írja (`0x008f6d30`). Az értékváltás előtt a `0x005d2240-0x005d2252` a legutóbbi értéket a globális `0xd34678` tömbből veszi és csak változásnál lép tovább. | `0x005d21a0`, `0x00751d20`, `0x008f6d30` | erős (szerkezet) |
| F8 | A csúszkák függőleges osztása `0x35` = **53 képpont**: `0x007513d4 add dword ptr [esp+0x10], 0x35` a csúszkaciklus végén. Ez egyezik a `ui-audit-editor.md` 4.3 mérésével (53 px). | `0x00750ff0` | megerősített (két út) |
| F9 | **Nincs a Hangolásra közvetlenül mutató parancs vagy billentyű.** A `editpanel/tab2` sztring címére (`0xc901a8`) a teljes fájlban 2 hivatkozás van: a `0x0057bd28` (a `0x0057bb50` elrendezés-tömbje) és egy `.data` névlista (`0xd3465c`; a lista `0xd34630`-nál kezdődik, benne `tab1`..`tab5`, és egyetlen olvasója a `0x005e0610`: egy ciklus, amely egy sztringet keres a listában, kattintást nem végez). A `editpanel/tab%d` formátumsztringet (`0xc87014`) csak a `0x0050ccd0` (melyik fül van bekapcsolva) és a `0x0057de60` (az aktuális fül neve) használja, egyik sem kattint. Név szerinti programozott kattintás a 2. fülre ezért nincs. A `0x005cb990` menüparancs-kezelő a `editpanel/tab1` nevet (`0x005cc921`, `0x005cc953`, `0x005cc985`) és a `editpanel/tab3` nevet (`0x005cc9b7`, `0x005cca51`, `0x005cca7b`, `0x005ccaa8`, `0x005ccad5`) használja, a `tab2`-t nem. | bájtszintű pásztázás (a teljes fájl, indextől független: a literálcímek little-endian dword-keresése a nyers bájtokban, a találatok szakaszra leképezve) | erős; hatóköre: a három literál (`tab2`, `tab%d`, `tab1`/`tab3`) minden előfordulása; máshol összefűzött fülnevet nem keresett a pásztázás, de a `tab%d` formátumot csak a fenti két függvény használja |

### A nyitott pontok besorolása

| # | Pont | Állapot | Indok / bizonyíték |
|---|---|---|---|
| Z1 | Belépés egy képpel (`Ctrl+3`, Nézet/Kép menü) az Alapvető javítások füllel | **LEZÁRVA** | A #375 felvétel és a bináris (`thumbui/fullview`, `0x005e624f`); `MainKeyboardShortcuts.qml:116-125`. Egyezik. |
| Z2 | Külső szerkesztő (`Ctrl+Shift+O`) nem Hangolás-belépő | **LEZÁRVA** | `picasa-menu-parancsok-viselkedes.md`; a PicasaPy `MainPhotoContextMenu.qml:116-119` külön kezeli. |
| Z3 | Van-e közvetlen Hangolás-parancs vagy billentyű | **LEZÁRVA** (negatív) | F9: nincs; a PicasaPy-ban sincs. A hatókör ott van kimondva. |
| Z4 | Alkalmaz/Mégse/Alaphelyzet a fülön | **LEZÁRVA** | F1: az eredetiben rejtett; a PicasaPy Hangolás-panelén sincs (`EditorFinetunePanel.qml` teljes tartalma). Egyezik. |
| Z5 | Radír a fülön | **LEZÁRVA** | F2: rejtett az eredetiben, nálunk nincs. Egyezik. |
| Z6 | Csúszkák tartománya, nullás alapállapot, geometria | **LEZÁRVA** | `filterdesc.xml` `finetune2` (0..1, 0..0.48, 0..0.48, -1..1) = `EditorFinetunePanel.qml:139,170,189,218`; F8 az 53 px osztás. Egyezik. |
| Z7 | Billentyűs `+`/`-` léptetés a fülön | **LEZÁRVA** | A `0x005f95d0` nullát ad a 2. fülön, nálunk `keyboardStepEnabled` ki van kapcsolva. Egyezik. |
| Z8 | Számkijelzés a csúszkák mellett | **LEZÁRVA** | `ui-audit-editor.md` 4.5 (nincs szám); `EditorFinetunePanel.qml` és `EditorSlider.qml` nem rajzol számot. Egyezik. |
| Z9 | Húzás közbeni előnézet és lezáró esemény szerkezete | **LEZÁRVA** (szerkezet) | F7: az eredetiben kétféle esemény van (érték változik / lezárás), nálunk `onValueChanged` előnézet és `onVeglegesult` véglegesítés (`EditorFinetunePanel.qml:141-143`). Az, hogy a lezáráskor mi íródik ki és mikor, külön pont (B2). |
| Z10 | Pipetta egyszeri használata (kattintás után kikapcsol) | **LEZÁRVA** | F4 és `PhotoViewerNeutralPickArea.qml:29` (`neutralPickerActive = false`). Egyezik. |
| Z11 | Melyik szűrőt szerkeszti a két Derítőfény-csúszka | **LEZÁRVA, igazolt eltérés** (kint: #7369, J2a megerősíti) | F5, F6, lásd T1; J2a: `fill=1,0.523364` és `finetune2` külön sorban. |
| Z12 | A pipetta állapota a fül váltásakor | **LEZÁRVA, igazolt eltérés** (kint: #7370, J5b-J5c megerősíti) | F3, lásd T2; J5b: a Hangolásra visszatérve a gomb felengedett; J5c: más fülön kattintás nem mintáz. |
| B1 | Belépés Entertől, dupla kattintástól, helyi menüből, valamint **többes kijelölésnél**: melyik kép nyílik, melyik fül, mi a filmszalag | **LEZÁRVA, igazolt eltérés** (T5) | J1a, J1b (E1-E3): egy képpel minden út ugyanazt nyitja az 1. fülön; kijelölés nélkül a `Ctrl+3` az 1. képet nyitja; két kijelölt képnél a rács szerinti elsőt, mindkét kijelölési sorrendben. A PicasaPy kijelölés nélkül nem nyit, többesnél a kattintás-sorrend szerinti elsőt nyitja. |
| B2 | Az Undo-bejegyzések száma és a húzás/lezárás/fülváltás körüli viselkedés; rács/bélyegkép hatása | **LEZÁRVA, igazolt eltérés** (T3) | J3a, J3c, J3d, J4a (E6, E7, E15): egy Hangolás-látogatás összes húzása egyetlen Undo-lépés; húzás közben az előnézet él és az Undo tiltott; a rács bélyegképe kilépéskor a lánc szerinti. A PicasaPy elengedésenként külön Undo-lépést tol. |
| B3 | Undo/Redo után a csúszkák állása; képváltás és újranyitás után a megjegyzett állapot | **LEZÁRVA, igazolt eltérés** (T3) | J2a, J3b, J4a, J4b (E5, E6, E14): a csúszkák minden belépésnél alaphelyzetben állnak, nem a láncot mutatják; Undo után alaphelyzet, Redo után is az; a Hangolás fül nyílik újra elsőnek (utolsó fül megjegyezve). A PicasaPy a mentett értékre állítja a csúszkákat. |
| B4 | A pipetta mintavétele: melyik kép (forrás vagy előnézet) | **LEZÁRVA, igazolt eltérés** (T4) | J5a, J5d (E10, E11): a p4 a FORRÁS színe akkor is, ha az előnézet módosított; képváltáskor a pipetta kikapcsol. A PicasaPy a megjelenített előnézetből mintáz és képváltáskor élesen marad. |
| B5 | A négy csúszka pontos nullázása: törlődik-e a `finetune2` réteg; mentés utáni fájl, backup | **BLOKKOLT** (hiány: pontos nulla) | J6c, J6f (E8, E12): a mentés (Save ablak, backup, fájl- és ini-változás) lemérve; a nullázás kérdése nem dőlt el, mert az egérrel visszahúzott Színhőmérséklet maradéka `-0.005848` (nem nulla), így a réteg minden felvételen megmaradt. Javított lépéssor: B5a, B5b (a Színhőmérséklethez nem nyúlnak). |
| B6 | A T1 megerősítése: a Gyakori javítások csúszka `fill=` sort ír; a másik fül állása | **LEZÁRVA** (T1 megerősítve, a 3. kész-feltétel megdőlt) | J2a, J2b (E4, E5): `fill=1,0.523364` és `finetune2` külön sorban; a másik fül csúszkája 0-n. A betöltött `fill` réteg melletti húzás ága külön tétel (B11). |
| B7 | Írásvédett vagy hálózati mentési hibaág a Hangolás után | **BLOKKOLT** (végrehajtói hiány) | J7 (E13): az írásvédett (`chmod 0444`) fájlon a mentés hibaablak nélkül lefut. Hogy az írásvédelem a mentéskor tényleg érvényben volt-e, nem igazolt (rootként a Wine-os írást a mód nem tiltja, és a fájllista csak a feladat végén készül). Hiány: a végrehajtó nem tud megbízhatóan írási hibát előidézni. |
| B8 | Enter, dupla kattintás és helyi menü **többes kijelölésnél**: melyik kép nyílik | **BLOKKOLT** (javított lépéssor: B1) | A J1b csak a `Ctrl+3`-at mérte többes kijelölésnél (E3); a többi belépési út nincs. |
| B9 | A `.picasa.ini` kiírásának kiváltója és késleltetése | **BLOKKOLT** (javított lépéssor: B2a, B2b, B2c) | J3a, J3b, J3c, J3d, J4a, J6a (E9): az elengedés után ~2-3 másodperccel nincs ini; fülváltás/Undo/kilépés után van; a kiváltó (idő, fülváltás, Undo, kilépés) nincs szétválasztva. Felhasználónak látható hatása nincs, amíg a program fut. |
| B10 | A pipetta mintavételének mérete (pont vagy terület), az Undo-gomb és a színminta a pipetta után | **BLOKKOLT** (javított lépéssor: B4a-d, B4u) | J5a (E11): a határon egyik folt sem lett szürke (terület-átlag a valószínű, sugara ismeretlen); az Undo tiltott maradt a pipetta után; a színminta fekete maradt (Wine-korlát vagy eredeti viselkedés: nincs eldöntve). |
| B11 | Betöltött `fill` réteg melletti húzás: új `fill` réteg vagy a meglévő módosul; az Undo hatása | **BLOKKOLT** (javított lépéssor: B6) | A `finetune2`-re a J6c azt mutatta, hogy új réteg kerül a betöltött mellé (E8); a `fill`-re nincs mérés. |

### Igazolt eltérések: kész fejlesztői jegytörzsek

#### T1: A Gyakori javítások Derítőfény-csúszkája a `fill` szűrőt szerkessze, ne a Hangolás `finetune2` rétegét

**Eredeti.** A szerkesztő az 1. fülre lépéskor a `fill` szűrőt aktiválja, a 2. fülre lépéskor a `finetune2`-t (`0x005d7780`: `0x005d77ad push 0xc87128` = `fill`; `0x005d77d0`: `0x005d78b2 push 0xc962b8` = `finetune2`; mindkettő a `0x005f8520`-at hívja). A `flightslider1/scaleslider` esemény a `0x005de8e0` diszpécserben ugyanarra az ágra ugrik, mint a `editslider1/editslider` (`0x005dfc57` és `0x005dfbe5` mindkettő `jne 0x5e04b5`), és az aktív szűrő 0. paraméterét állítja (`0x005d21a0` → `0x00751d20`). A regiszterben a `fill` UI-neve `Fill Light`, `soft` módú, egyetlen rejtett paraméterrel (`filterdesc-registry.md` 171. sor); a `finetune2` UI-neve `Tuning` (139. sor), és az eredeti szövegtár szerint a Visszavonás-felirata is `Tuning` (`edit_action_names.py:88`). Mérés: a `job-812` `kepernyo__27` képén a Derítőfény-csúszka mozgatása után az Undo felirata `Undo Fill Light` (a #7327 lap 7327-7 sora szerint; a képet ebben a körben nem néztem újra). Korpusz: az eredeti Picasa által írt ini-fájlokban a `fill=1,<érték>` sor önálló szűrőként 1089-szer fordul elő (`picasa-ini-format.md:253`, `:1814`).

**Nálunk.** A csúszka nem a `fill` réteget, hanem a Hangolás `finetune2` rétegét írja, és a két fül csúszkája közös állapot:

```qml
// EditorTabCommonFixes.qml:322,326
onValueChanged: panel.fillLightMoved(value)
onVeglegesult: panel.fillLightCommitted()
```

```js
// editorpanel_logika.js:231 és :262
fixesTab.fillSlider.value = panel.fillLight   // #337: a másik fül párja
function fillLightCommitted() { panel.emitFinetuneCommit() }
```

```python
# edit_controller_effects_finetune_mixin.py:180
self._push_undo("finetune")
```

A `session_effects.py:118` és `:161` csak a `finetune`/`finetune2` nevű réteget olvassa (`_FINETUNE_NAMES`), a `fill` réteget soha. Következmény (a kódból, futtatás nélkül): egy eredeti Picasában szerkesztett, `fill=1,0.5` sort tartalmazó képen a csúszka 0-n áll, a mozgatása pedig a `fill` mellé egy `finetune2` réteget ad (kettős hatás), és a Visszavonás felirata `Finomhangolás` lesz `Derítőfény` helyett.

**Teendő.** A Gyakori javítások Derítőfény-csúszkája (`fixesFillSlider`) a lánc `fill=1,<érték>` rétegét szerkessze (egy ilyen réteg, a helyén cserélve), nyitáskor a meglévő `fill` réteg értékét mutassa, a Visszavonás-felirata legyen `Fill Light` (magyarul `Derítőfény`). A Hangolás fül Derítőfény-csúszkája a `finetune2` 1. paraméterét írja tovább. A két csúszka ne osztozzon állapoton (`fillLightMoved`, `syncFinetuneSliders` kapcsolata megszűnik). A másik fül csúszkájának állása, ha mindkét réteg létezik, a J2 felvétel szerint dől el: a jegy addig nem teszi szinkronba őket.

**A J2 felvétel eredménye (zárókör 2).** A teendő magja megerősödött és kint van (#7369): a J2a ini-je `fill=1,0.523364;finetune2=1,0.760234,...`, a két csúszka külön réteg és külön felirat (`Undo Fill Light`, `Undo Tuning`). A 3. kész-feltétel viszont **megdőlt**: az eredeti a meglévő `fill=1,0.5` réteget a képen alkalmazza, de a csúszka nyitáskor a bal szélen áll (J2b 14. kép), mert az eredetiben a csúszkák nem a láncot mutatják (lásd T3). A „nyitáskor a meglévő érték" tehát NEM követelmény, hanem eltérés.

**Kész, ha.**
1. A Gyakori javítások csúszka húzása után a láncban `fill=1,<érték>` van, `finetune2` nincs; a Hangolás fülön a csúszka 0-n áll.
2. A Hangolás csúszka húzása után `finetune2` van a láncban, a `fill` változatlan.
3. ~~Egy `fill=1,0.5` sort tartalmazó kép megnyitásakor a Gyakori javítások csúszka a 0.5-nek megfelelő állásban van.~~ MEGDŐLT (J2b): a csúszka alaphelyzetben (bal szél) áll, a kép viszont a `fill` réteg szerint korrigált; ezt a T3 kezeli.
4. A Visszavonás-felirat a Gyakori javítások csúszka után `Visszavonás: Derítőfény`, a Hangolás után `Visszavonás: Finomhangolás`.
5. A `job-812` és a J2 felvétel a PicasaPy kimenetével párban egyezik (felirat, kép, ini-sor).
6. Valódi egéresemény-teszt mindkét csúszkára (nem csak a kontroller-metódus hívása), és rontás-kontroll: az a teszt elbukik, ha a Gyakori javítások csúszka visszakerül a `finetune2`-re.

**Bizonyítottsági fok.** Megerősített (zárókör 2): a bináris utasítások (F5, F6), a `job-812` felirata és a J2a ini-visszaolvasása (`fill=` és `finetune2=` külön sorban, külön Undo-felirattal) egymástól független utak, és egyeznek.

#### T2: A pipetta kapcsoljon ki a Hangolás fülre lépéskor, és ne vegyen mintát más fülön

**Eredeti.** A `0x005d77d0` (a Hangolás fül belépője) a `editpanel/droppertoggle` gombot kikapcsolja, ha be volt kapcsolva: `0x005d7810 cmp byte ptr [ebx+0x359], 0`, `0x005d781f mov byte ptr [ebx+0x359], 0`, majd a `buttontoggle` esemény kiadása (`0x005d7833`, `0x005d7866`); a `0x005f8380` a gomb állapotát a szűrőkezelő módjává alakítja (`0x005f84ee-0x005f8502`: bekapcsolva 2, kikapcsolva 0). A kattintás utáni kikapcsolás is csak `colorfix`/`finetune`/`finetune2` aktív szűrőnél fut (`0x00752800`, `0x00752883-0x00752978`, `0x0075297f`, `0x007529c0`).

**Nálunk.** A pipetta állapota fülváltáskor érintetlen marad, és a mintavevő felület a fültől függetlenül aktív:

```qml
// PhotoViewerNeutralPickArea.qml:15-16
visible: photoArea.hostEditorPanel.neutralPickerActive
enabled: photoArea.hostEditorPanel.neutralPickerActive
```

```qml
// EditorPanel.qml:275-289 (onActiveTabChanged): syncFinetuneSliders(), Shift-figyelés,
// és csak ennyi: if (panel.paramPanelActive) panel.cancelParamPanel()
```

A `neutralPickerActive` kizárólag a pipettagomb váltásakor (`PhotoViewerEditorPanel.qml:278-279`) és a kép-kattintáskor (`PhotoViewerNeutralPickArea.qml:29`) változik; a `src` alatt (`.qml`, `.js`, `.py`) más írója nincs. Következmény (a kódból, futtatás nélkül): élesített pipettával az Alapvető javítások vagy egy effektfülre váltva a képre kattintás meghívja a `pickNeutralColor`-t (`edit_controller_effects_color_mixin.py:53`), ami `finetune2` réteget ír, és a Hangolás fülre visszatérve a pipettagomb még lenyomva látszik.

**Teendő.** A Hangolás fülre lépéskor (`activeTab` 1-re váltása) a pipetta kapcsoljon ki (`neutralPickerActive = false`). A mintavevő felület csak a Hangolás fülön legyen aktív (`neutralPickerActive && activeTab === 1`). A kattintás utáni kikapcsolás maradjon. A fül elhagyásának eredeti viselkedése a J5 felvételeken mérve (zárókör 2): élesített pipetta, Effektek fül, vissza a Hangolásra: a gomb nincs lenyomva (J5b 17. kép); élesített pipettával az 1. fülön a képre kattintás nem mintáz (J5c 17. kép: a kép és az Undo változatlan, nincs ini). A #7370 ezzel egyezik; a képváltás ága viszont eltér (J5d, lásd T4).

**Kész, ha.**
1. Élesített pipetta után fülváltás Alapvető javítások vagy Effektek fülre, majd vissza a Hangolásra: a pipettagomb nincs lenyomva, és az első képkattintás nem ír `finetune2` réteget.
2. Élesített pipettával a nem Hangolás fülön a képre kattintás nem hívja a `pickNeutralColor`-t és nem módosít láncot.
3. A meglévő egyszeri használat (kattintás után kikapcsol) változatlan.
4. Valódi egéresemény-teszt (tab-váltás, kattintás a képre), rontás-kontroll: a teszt elbukik, ha az `onActiveTabChanged` visszakerül a mai alakra.
5. A J5 felvétel 6-7. lépése egyezik a PicasaPy kimenetével.

**Bizonyítottsági fok.** Megerősített (zárókör 2): a belépési oldalt a `0x005d77d0` utasításai és a J5b felvétel, a más fülön kattintást a J5c felvétel támasztja alá (két független út); a PicasaPy kódja két helyen egyezik (`editorpanel_logika.js:67-70`, `EditorPanel.qml:140,280`).

### Colab-lépéssor (a blokkolt pontokhoz)

*(Lefuttatva: job-840 ... job-860; az eredmény a „J1-J7 eredménye" szakaszban, a maradék kérdések javított lépéssorai ott a táblázatban.)*

Mindegyik feladat friss tesztprofilban, a tesztmappa **másolatán** fut a Colab-os végrehajtón. Minden lépés előtt és után rögzíts: `kepernyokep`, `ablakmeret`, `allapot`, `picasa_ini`, `export` és az eredeti fájl hasítóértékét. A mintakép a tesztmappa `color_patches.jpg` másolata (ismert színfoltok), hacsak a lépés mást nem mond. Az 1280×1024-es kimeneten a Hangolás-fül gombja a fülsáv 2. ikonja (nap/csillag, `ui-audit-editor.md` 1. szakasz); a csúszkák és gombok koordinátáit az első, kalibráló képből olvasd ki (mint a `#7327` Crop-koordinátáit), a 2026-07-17-i 1920×1080 referencián a sávok x 44-230, y 162, 215, 268, 321.

**J1: belépés és többes kijelölés (B1).**
1. Könyvtárnézet, kijelölés nélkül: `Ctrl+3`. Rögzíts: nyílt-e nézet, melyik kép.
2. Egy kép kijelölve: `Ctrl+3`; majd vissza a könyvtárhoz; dupla kattintás a képen; vissza; `Enter`; vissza; jobb gomb a képen, `Megjelenítés és szerkesztés`. Mindegyik után: melyik fül aktív (az 1. fülnek kell lennie), melyik kép nyílt.
3. Két kép kijelölve (`Ctrl`+kattintás): `Ctrl+3`. Rögzíts: melyik kép nyílik meg, hány kép látszik a filmszalagon, melyik fül aktív.
4. Ugyanabban az állapotban kattints a Hangolás fülre, húzd a Színhőmérséklet csúszkát a jobb szélre és engedd el. Rögzíts mindkét kép `.picasa.ini`-jét: melyikbe került `finetune2`.

**J2: a két Derítőfény-csúszka és a `fill` (B6, T1).**
1. Tiszta másolat, Alapvető javítások fül: a Derítőfény-csúszka sávjának közepére húzás, elengedés. Rögzíts: kép, az Undo felirata, `.picasa.ini` (`fill=` vagy `finetune2=`).
2. Kattints a Hangolás fülre. Rögzíts: a Derítőfény-csúszka állása, a Visszavonás felirata.
3. A Hangolás Derítőfény-csúszkáját a sáv 3/4-ére húzd, elengedés. Rögzíts: ini (a `fill` érintetlen-e, van-e `finetune2`), a Visszavonás felirata, majd vissza az Alapvető javítások fülre: a csúszka állása.
4. Új másolat, ini-előkészítés: `filters=fill=1,0.500000;`. Nyisd meg a nézőt az Alapvető javítások fülön. Rögzíts: a csúszka állása a megnyitáskor (T1 kész-feltétele: 0.5-nek megfelelő hely), majd a Hangolás fülön a csúszka állása.

**J3: húzás, elengedés, ini, Undo, felület (B2).**
1. Hangolás fül, tiszta másolat. A Kiemelések csúszkát lassan húzd a sáv közepére, de ne engedd el: rögzíts képernyőképet a húzás alatt (előnézet látszik-e, Visszavonás-gomb állapota) és olvasd vissza az ini-t (van-e már `finetune2`).
2. Engedd el. Rögzíts: ini, Undo-gomb felirata, a rács/bélyegkép és az állapotsor változása.
3. Ugyanazt a csúszkát húzd tovább és engedd el még kétszer. Rögzíts: hány Undo-lépés van (nyomj Undo-t, amíg tilt; számold), ini minden lépés után.
4. Mozgasd a négy csúszkát egymás után, mindegyiket elengedve; rögzíts minden lépés után ini-t. Egy `finetune2` sor lesz-e, vagy több.
5. Fülváltás (Alapvető javítások) húzás nélkül, majd vissza: az ini és az Undo változatlan-e.

**J4: Undo/Redo és képváltás (B3).**
1. J3 4. lépés végállapotából: Undo, Undo, Redo. Mindegyik után: a négy csúszka állása a Hangolás fülön, az ini.
2. Lépj a következő képre (nyíl), majd vissza. Rögzíts: a csúszkák állása a visszatéréskor, az ini.
3. Lépj ki a könyvtárba, nyisd meg újra ugyanazt a képet, kattints a Hangolás fülre: a csúszkák állása (megjegyzett-e), melyik fül nyílik először.

**J5: pipetta (B4, T2).** Mintakép: `color_patches.jpg`, ahol a pipetta célpontjának környezete ismert, két kis színfoltra osztható.
1. Hangolás fül, kattints a pipettára: rögzíts képernyőképet (gomb állapota, kurzor).
2. Kattints egy egyszínű folt belsejébe: rögzíts ini-t (`finetune2` p4), a gomb állapotát (kikapcsolt-e), és a folt pontos színét a forrásképből.
3. Ismételd egy két folt határán álló képpontra: ha a p4 a két szín valamelyike, egy képpontot mintáz; ha a keverékük, területet. Ha a kép nagyítva van, ismételd 100%-os és illesztett nézetben is, hogy kiderüljön, a forrást vagy az előnézetet mintázza.
4. Ismételd egy olyan másolaton, ahol már van `finetune2` nem nulla Színhőmérséklettel: a p4 a forrás vagy az előnézet (már módosított) színét tárolja-e.
5. Élesítsd a pipettát, **ne** kattints a képre; váltsd az Effektek fülre, majd vissza a Hangolásra: a pipettagomb állapota (T2 1. kész-feltétele).
6. Élesítsd a pipettát, váltsd az Alapvető javítások fülre, és kattints a képre: történt-e mintavétel, változott-e az ini.
7. Élesítsd a pipettát, lépj a következő képre, majd vissza: a gomb állapota.

**J6: nullázás, semleges szín, mentés (B5).**
1. Ini-előkészítés: `filters=finetune2=1,0.000000,0.000000,0.000000,ffccc6b2,0.000000;`. Nyisd meg a Hangolás fület: a színminta a `ffccc6b2` színű-e.
2. Húzd a Színhőmérséklet csúszkát a jobb szélre és vissza pontosan a középre; engedd el mindkétszer. Rögzíts: ini (a `finetune2` sor megvan-e, a p4 megmaradt-e), a színminta, az Undo-lépések száma.
3. Ismételd a Kiemelések csúszkával (jobb szél, vissza a bal szélre).
4. Mentsd a képet a Picasa mentési parancsával (`Ctrl+S` vagy Fájl menü); rögzíts: `.picasa.ini`, az eredeti fájl hasítóértéke, a biztonsági másolat (`.picasaoriginals`), az export, a rács és az állapotsor.

**J7: hibaág (B7), közös a #7327 8. lépésével.** Eldobható, írásvédetté tett másolaton végezz Hangolás-módosítást és mentést; rögzítsd a teljes hibaüzenet szövegét, a fájl és az ini változatlanságát és a csúszkák állását a hiba után.

### J1-J7 eredménye (zárókör 2)

**Módszer és mérce.** A húsz felvétel (job-840 ... job-860: J1a, J1b, J2a, J2b, J3a-J3d, J4a, J4b, J5a-J5d, J6a-J6c, J6f, J7) az eredeti Picasa 3.9 Wine alatt, 1280x1024-en. Az `allapot.json` OCR-je üres volt (a Save ablakon kívül), ezért a döntés a képkockák megnézéséből és pixelmérésből jön; az ini-k és a fájllista csak a feladat VÉGÉN készülnek. A `kepernyo__NN` az NN. lépés ELŐTTI állapot. Minden döntő kockán ellenőriztem, hogy a kattintás a szándékolt elemre ment (J0 utáni koordináták: csúszkák y 160/213/266/320, Visszavonás (70,412), Újra (207,412), pipetta (148,374)): a Hangolás fül elrendezése az első kockákon: négy csúszka (Fill Light, Highlights, Shadows, Color Temperature), a Highlights/Shadows mellett varázspálca, "Neutral Color Picker" felirat alatt színminta-korong és pipetta, mellette varázspálca, alul "Undo"/"Redo" gomb. Az 1. fülön egy "Fill Light" csúszka (x 107-220, y 345).

#### Mért tények

| # | Tény | Döntő kockák | Fok |
|---|---|---|---|
| E1 | Kijelölés nélkül (a mappa kijelölve, a tálcán "Folder Selected - 24 photos") a `Ctrl+3` az **1. képet** (`gray_ramp.jpg`, "1 of 24") nyitja, az Alapvető javítások fülön. A bináris `0x005e624f` ága kijelölés-ellenőrzés nélkül kattintja a `thumbui/fullview` gombot (`0x005e624f mov edx,0xc8f0dc`, `0x005e6254 call 0x9cd8a0`, `0x005e6259 jmp 0x5e65f7`). | J1a 9. | erős (felvétel + bináris) |
| E2 | Egy kijelölt képnél a `Ctrl+3`, a dupla kattintás, az Enter és a helyi menü első, félkövér "View and Edit" (Enter) tétele ugyanazt nyitja: `color_patches.jpg`, "2 of 24", 1. fül. Az Escape a könyvtárba lép, a kijelölés megmarad. | J1a 15., 19., 25., 33.; 17., 27., 35. | erős |
| E3 | Két kijelölt képnél (állapotsor "2 pictures") a `Ctrl+3` **mindkét** kijelölési sorrendben a rács szerinti első képet (`color_patches`) nyitja, nem az elsőnek vagy utolsónak kattintottat. A felső filmszalag a szomszéd képeket mutatja, nem a kijelölést (egy képpel ugyanaz). A Hangolás-módosítás csak a megnyitott kép ini-jébe kerül (`rgb_gradient`-nek nincs szakasza). | J1b 10., 12., 19., 23. + ini | erős (két sorrend) |
| E4 | A két Derítőfény-csúszka két külön réteg: `filters=fill=1,0.523364;finetune2=1,0.760234,0.000000,0.000000,00000000,0.000000;`. Az Undo felirata az 1. fül húzása után "Undo Fill Light", a Hangolás húzása után "Undo Tuning". Az 1. fül húzása után a Hangolás Derítő-csúszkája 0-n áll, a Hangolás húzása után az 1. fül csúszkája is 0-n. | J2a 11., 13., 15., 17. + ini | erős |
| E5 | A csúszkák **soha nem a láncot mutatják**, mindig alaphelyzetben állnak (Színhőmérséklet a közepén): újraindítás után (J2a 28., 30.), előkészített `fill=1,0.5` mellett (J2b 14., 16.), betöltött `finetune2` mellett (J6a 16.), a könyvtárból újranyitva (J4b 33.), és a Hangolásról elmenve-visszatérve is (J3b 5.: Kiemelések 0-n, az ini-ben 0.238596). A kép viszont a lánc szerint korrigált (J2b 12., 14. világosabb; J6a 14.). | lásd mellette | erős (hét felvétel) |
| E6 | A Hangolás-látogatás összes húzása **egy Undo-lépés**: hat húzás négy csúszkán, majd egy Undo kattintás mindent visszaállít, a gomb tiltott, az Újra felirata "Redo Tuning"; további Undo kattintások nem tesznek semmit. Négy húzás, Undo, Undo, Redo után a kép újra szerkesztett, de a csúszkák alaphelyzetben maradnak. | J3d 23., 25., 27-39.; J4a 19., 21., 23., 25. | erős |
| E7 | Húzás közben az előnézet már változik (kép, hisztogram), az Undo gomb tiltott; elengedés után "Undo Tuning". | J3a 11_közben, 12. | erős |
| E8 | Betöltött `finetune2` réteg mellé az első húzás **új** `finetune2` réteget ad: `finetune2=1,0,0,0,ffccc6b2,0;finetune2=1,0,0,0,00000000,-0.005848` (a második p4-je `00000000`). Egy munkamenetben a pipetta és a csúszkák egy rétegbe kerülnek: `finetune2=1,0,0,0,ffc89779,-0.005848`; négy húzás négy csúszkán: egy réteg négy értékkel. | J6c, J6f (`.picasaoriginals` ini); J4a ini | erős |
| E9 | Az ini kiírása nem azonnali: nincs ini az elengedés után ~2 másodperccel (J3a), hat húzás után ~3 másodperccel (J3c), és az előkészített ini a J6a/J6b végén, a húzások után néhány másodperccel is érintetlen (86 bájt). Van ini fülváltások után (J3b), Undo/Redo után (J4a), Escape után (J3d, J4b, J5a). A J3d-ben a nyolc Undo után az ini csak `backuphash=`-t tartalmaz (a `filters` sor eltűnik, a szakasz marad). | lásd mellette | közepes (a kiváltó nincs szétválasztva) |
| E10 | A pipetta egyszeri (a mintavétel után a gomb felenged); más fülről a Hangolásra visszatérve felengedett (J5b 17.); élesített pipettával az 1. fülön a képre kattintás nem mintáz (J5c 17.: a kép és az Undo változatlan, nincs ini); képváltás és vissza után is felengedett (J5d 15., 17.). | J5a 15., 19., 25.; J5b; J5c; J5d | erős |
| E11 | A pipetta **a forrás színét** tárolja: a bézs folt forrása `c89779`, a 3. mintavételkor az előnézet `cf9c54` (Színhőmérséklet a jobb szélen), az ini végső p4-e `ffc89779`. A mintavétel után a folt szürke (`a1a1a1`). A két folt határán (x=782) egyik folt sem lesz szürke (bézs `c69c65`, kék `3e5b80`), tehát nem egy folt tiszta színe lett a semleges: terület-átlag a valószínű, a sugara ismeretlen. Az Undo gomb a pipetta után tiltott maradt (J5a 15., 19.), a csúszkahúzás után lett aktív (21.). A színminta-korong minden felvételen fekete maradt, még `ffccc6b2` p4-nél is (J6a 16.). | J5a 13-25. (pixelmérés) | erős (forrásszín); közepes (terület); nyitott (Undo, színminta) |
| E12 | Mentés (`Ctrl+S`): "Save" ablak, "Save changes to disk?", "A backup of this file will be made.", "Do not ask me again." jelölő, Save és Cancel gomb; a Return ment. Utána az Undo felirata "Undo Save", a csúszkák alaphelyzetben. A fájl új (20557 -> 12438 / 12419 bájt), az eredeti a `.picasaoriginals/color_patches.jpg`, az ottani ini őrzi a mentés előtti `filters` sort, plusz `moddate`, `width`, `height`, `textactive`; a fő ini mentés után csak `backuphash=`. | J6c 26., 28., 31.; J6f; J7 16., 18. | erős |
| E13 | Az írásvédett (`chmod 0444`) `color_patches.jpg` mentése **hibaablak nélkül** lefut (a fájl 95733 bájt, a `csak_olvashato` jelző a végén hamis, az eredeti a `.picasaoriginals`-ban). | J7 16-19. + fájllista | közepes (az írásvédelem érvényesülése a mentéskor nem igazolt) |
| E14 | Képváltásnál (J4b 27.) és a könyvtárból újranyitva (J4b 33.) a **Hangolás fül nyílik** (az utolsó fül megjegyezve); az újraindítás utáni első nyitás az 1. fül (J2a 28., J2b 14., J6a 14.); hogy az utolsó fül újraindítás után is megmarad-e, nem mért (a J2a-ban az utolsó fül az 1. volt). A 2. fül súgóbuborékja: "Finely-tuned lighting and color fixes" (J4b 35.). | lásd mellette | erős |
| E15 | A rács bélyegképe kilépéskor a lánc szerinti: szerkesztés után szerkesztett (J4b 31.: `fde990` az eredeti `c59773` helyett), az összes Undo után az eredeti (J3d 41.: `c59974`). | J3d 41.; J4b 31. | erős |

#### Összevetés a PicasaPy mai viselkedésével (1.0.172)

| Pont | Eredeti | Nálunk (fájl:sor) | Egyezik? |
|---|---|---|---|
| Két külön Derítőfény-réteg (#7369) | E4 | `edit_controller_effects_finetune_mixin.py:203-231` (`previewFixesFill`, `setFixesFill`), `editorpanel_logika.js:237-245` | **igen** (réteg és felirat) |
| A csúszkák helye belépéskor, képváltáskor, Undo/Redo után | E5, E6 | `PhotoViewerEditorPanel.qml:56-66` (a kontroller mentett értékei), `editorpanel_logika.js:237-245`, `EditorPanel.qml:276-280`, `PhotoViewerEditWorkflow.qml:609-616,711-712`, `edit_controller_effects_finetune_mixin.py:28-54,234-238` | **NEM** (T3) |
| Undo-lépések száma | E6 | `edit_controller_effects_finetune_mixin.py:187-188` + `edit_controller_history_mixin.py:100-102` (elengedésenként új bejegyzés, nincs összevonás) | **NEM** (T3) |
| Réteg-modell betöltött réteg mellett | E8 | `edit/session_effects.py:58-101` (`_with_single_layer`: a láncban egy `finetune2`, a húzás a helyén cserél) | **NEM** (T3) |
| Húzás közbeni előnézet | E7 | `edit_controller_effects_finetune_mixin.py:122-135` (nem ír ini-t, nem tol Undo-t) | **igen** |
| Pipetta fülváltáskor (#7370) | E10 | `editorpanel_logika.js:67-70`, `EditorPanel.qml:140,280`, `PhotoViewerNeutralPickArea.qml:15-17` | **igen** |
| Pipetta képváltáskor | E10 | `PhotoViewerEditWorkflow.qml:691-712` (a `neutralPickerActive`-hoz nem nyúl) | **NEM** (T4) |
| Pipetta mintavétel forrása | E11 | `edit_preview.py:491-508` (a megjelenített előnézet pixele), `edit_controller_effects_color_mixin.py:53-72` | **NEM** (T4) |
| `Ctrl+3` kijelölés nélkül | E1 | `MainWindowLibraryActions.qml:95-100` (üres kijelölésnél kilép) | **NEM** (T5) |
| `Ctrl+3` többes kijelölésnél | E3 | `selection.js:7-12,32-36`, `MainLibrarySelectionState.qml:274-280` (kattintás-sorrend), `MainWindowLibraryActions.qml:99` (`sorok[0]`) | **NEM** (T5) |
| Egy képpel Enter, dupla kattintás, helyi menü | E2 | `LightboxFeed.qml:401-410`, `MainLibraryCanvas.qml:387-395`, `MainPhotoContextMenu.qml:110-118` (kódolvasás, futtatás nincs) | igen (kódból) |
| Save ablak szövege és gombjai | E12 | `SaveDialogs.qml:110-160` | **igen** (szó szerint) |
| Utolsó fül megjegyzése | E14 | `EditorPanel.qml:60`; az `activeTab` csak az effekt-alpanel bezárásakor áll 0-ra (`editorpanel_logika.js:218`) | igen (kódból) |
| Színminta-korong | E11 | `EditorFinetunePanel.qml:240-243` (a kiválasztott színt mutatja) | nyitott (az eredeti felvételeken fekete) |
| Négy nulla csúszka | B5 | `edit_controller_effects_finetune_mixin.py:189-190` (a réteget törli) | nyitott (B5a, B5b) |

#### T3: A Hangolás fül csúszkái alaphelyzetben induljanak, a látogatás legyen egyetlen Undo-lépés, a betöltött réteg mellé új réteg kerüljön (jegy: #7383)

**Mi a hiba.** Három összefüggő, látható eltérés ugyanabból a modellből (ezért egy jegy; külön-külön megvalósítva egymást törnék):
1. A PicasaPy csúszkái a lánc mentett értékére állnak (fülbelépés, képváltás, újranyitás, Undo/Redo); az eredetiben mindig alaphelyzetben állnak, a kép viszont a láncot mutatja.
2. A PicasaPy minden elengedést külön Undo-lépésként tárol; az eredetiben egy látogatás összes húzása egy lépés.
3. A PicasaPy láncában egyetlen `finetune2` lehet, a húzás a helyén cserél; az eredetiben a betöltött réteg mellé új `finetune2` kerül (két réteg a láncban).

**Eredeti.** E5, E6, E8: a J2a 28. és 30. képe (újraindítás után az 1. és a Hangolás fül csúszkái a bal szélen, az ini-ben `fill=1,0.523364` és `finetune2=1,0.760234`), a J2b 14. és 16. képe (előkészített `fill=1,0.5`: a kép korrigált, a csúszka a bal szélen), a J3b 5. képe (fülváltás után a Kiemelések 0-n, az ini-ben 0.238596), a J3d 23. és 25. képe (hat húzás után egy Undo mindent visszaállít, "Redo Tuning"), a J4a 19., 21., 25. képe (négy húzás, Undo, Redo: a csúszkák alaphelyzetben), a J6c ini-je (két `finetune2` réteg). Bináris: a Hangolás-fül belépője `0x005d77d0` a pipetta kikapcsolása (`0x005d7810-0x005d787a`) és az aktív szűrő név szerinti beállítása (`0x005d78b2 push 0xc962b8` = `finetune2`, `0x005d78c1 call 0x5f8520`) között nem olvas rétegértéket; a `0x005f8520` a szűrőleírót a regiszterből név szerint kéri (`0x005f856d-0x005f8570`). A csúszkák kezdőértékét író utasítás nincs azonosítva: a bináris az összhangot támasztja, a viselkedést a felvételek bizonyítják. Az Undo-összevonás jelöltjei: F7 (`0x005d21f0-0x005d2217`, `0x00567680`).

**Nálunk.** `PhotoViewerEditorPanel.qml:56-66` (a csúszkák a kontroller mentett értékeire kötve), `editorpanel_logika.js:237-245` (`syncFinetuneSliders`), `EditorPanel.qml:276-280` (tábla-váltáskor szinkron), `PhotoViewerEditWorkflow.qml:609-616` (a kontroller változásakor) és `:711-712` (képváltáskor), `edit_controller_effects_finetune_mixin.py:28-54,234-238` (a csúszka-tulajdonságok a mentett `finetune2`-ből), `:187-188` (`_push_undo` minden elengedésre), `edit_controller_history_mixin.py:100-102` (nincs összevonás), `edit/session_effects.py:58-101` (egy `finetune2` réteg).

**Teendő.**
1. A Hangolás-látogatás fogalma: a Hangolás fülre lépéstől a fül elhagyásáig, a képváltásig, az Undo/Redo-ig és a mentésig. A látogatás első húzásakor új `finetune2` réteg kerül a lánc végére (a betöltött és ismeretlen rétegek érintetlenek); a látogatás további húzásai és a pipetta ugyanazt a réteget módosítják; az egész egy Undo-bejegyzés (felirat: Finomhangolás).
2. A csúszkák (a négy Hangolás-csúszka és az 1. fül Derítőfény-csúszkája) belépéskor, képváltáskor, megnyitáskor, Undo és Redo után alaphelyzetben állnak (0; a Színhőmérséklet a tartomány közepén); a kép a láncot mutatja. A `syncFinetuneSliders` a mentett értékek helyett az alaphelyzetet állítsa.
3. A látogatás előtt a láncban lévő `finetune2` (betöltött vagy egy korábbi látogatásból való) mellé új réteg kerül; az Undo csak az újat veszi le. A fül elhagyása utáni húzás új réteget ad: ez a J6c általánosítása, **közvetlenül nem mért** (a B9/B2b felvétel dönti el); ha az mást mutat, a jegyet igazítani kell.
4. Az 1. fül Derítőfénye (`fill` réteg) ugyanígy: alaphelyzeti csúszka; hogy a betöltött `fill` mellett a húzás új réteget ad-e, a B11/B6 felvétel dönti el, addig a `fill` réteg a mai módon cserélődik.

**Kész, ha** (látás alapú, a felvétel kockáival párban):
1. `fill=1,0.5` és `finetune2` sort tartalmazó kép megnyitásakor mindkét fülön minden csúszka alaphelyzetben áll, a renderelt kép a lánc szerint korrigált (J2b 14., 16.; J2a 28., 30.).
2. Hat húzás négy csúszkán, majd egy Undo kattintás: minden visszaáll, az Undo tiltott, az Újra a lépés nevét viseli (J3d 23., 25.).
3. Négy húzás, Undo, Undo, Redo: a kép szerkesztett, a csúszkák alaphelyzetben (J4a 25.).
4. A Hangolásról elmenve és visszatérve a csúszkák alaphelyzetben (J3b 5.).
5. Betöltött `finetune2=1,0,0,0,ffccc6b2,0` mellett egy húzás után a láncban két `finetune2` sor áll, a második p4-je `00000000` (J6c ini-párja).
6. Valódi egéresemény-teszt a csúszkákra és az Undo/Redo gombokra (nem a kontroller-metódus hívása), rontás-kontroll: a teszt elbukik, ha a csúszkák ismét a mentett értékre állnak.
7. Vizuális elfogadás: a renderelt kimenet és a J3d/J4a/J2b kockák összevetése mért eltéréssel; a szomszéd (Gyakori javítások fül, effektfülek, Undo/Redo gombsor) regresszió-ellenőrzése a kiadás előtt.

**Bizonyítottsági fok.** Erős a viselkedésre (nyolc felvétel, azonos eredmény); a bináris oldal összhangban van, de a kezdőértéket író utasítás nincs azonosítva.

#### T4: A pipetta a forrásképből mintázzon, és képváltáskor kapcsoljon ki (jegy: #7385)

**Mi a hiba.**
1. A PicasaPy a MEGJELENÍTETT (szerkesztett) előnézetből mintáz; az eredetiben a p4 a forrás színe. Nem nulla Színhőmérséklet vagy korábbi semleges szín mellett az újabb mintavétel így mást ír az ini-be (nálunk `ffcf9c54`, illetve a már semlegesített szürke; az eredetiben `ffc89779`).
2. A PicasaPy-ban képváltáskor a pipetta élesen marad, az eredetiben kikapcsol.

**Eredeti.** E10, E11: a J5a 23. és 25. képe (a bézs folt előnézete `cf9c54`), az ini p4-e `ffc89779` (a forrás `c89779`); a mintavétel után a folt szürke (`a1a1a1`, 15. kép); J5d 13. kép (lenyomott gomb), 15. és 17. kép (képváltás után felengedett). Bináris: a pipetta-gomb állapota a szűrőkezelő módjává alakul (`0x005f8380`, `0x005f84ee-0x005f8502`), a kép-egéresemény kezelője egyszer használatra kapcsolja ki (`0x00752800`, `0x00752883-0x007529c0`, F3, F4). A mintavétel forrására és a képváltási kikapcsolás kiváltójára bináris cím nincs azonosítva; a viselkedést a felvételek bizonyítják.

**Nálunk.** `edit_preview.py:491-508` (`sample_color` a megjelenített képből), `edit_controller_effects_color_mixin.py:53-72` (`pickNeutralColor`), `PhotoViewerEditWorkflow.qml:691-712` (`onCurrentIndexChanged` nem nyúl a `neutralPickerActive`-hoz), `PhotoViewerNeutralPickArea.qml:24-31`.

**Teendő.** (1) A mintavétel a `finetune2` réteg ELŐTTI lánc képéből történjen (a `gpuPrefixSource` párja), ne a megjelenített előnézetből; a J5a-ban nincs más réteg, ezért a "vágás előtti vagy utáni kép" kérdése NINCS MEG, a mai vágás-kezelést ne változtassa. (2) A képváltás (`onCurrentIndexChanged`) a pipettát kapcsolja ki. A mintavétel méretét (pont vagy terület) a B10 felvétel dönti el: a jegy addig az egy pixeles mintavételt hagyja.

**Kész, ha.**
1. Élesített pipetta, következő kép, vissza: a gomb felengedett, az első képkattintás nem mintáz (J5d 15., 17.).
2. Mintavétel a bézs folton, Színhőmérséklet a jobb szélre, újabb mintavétel ugyanott: az ini p4-e a forrás színe (`ffc89779`), nem az előnézeté (J5a ini-je).
3. A mintavétel utáni kép és a J5a 15. kép (a folt szürke) mért eltéréssel összevetve; az eltérés nagyságát a mérés jelenti, túllépés esetén külön jegy (a semlegesítő képlet nem e jegy tárgya).
4. Valódi egéresemény-teszt (gombnyomás, képkattintás, nyíl), rontás-kontroll: a teszt elbukik, ha a mintavétel visszakerül az előnézetre.

**Bizonyítottsági fok.** Erős a forrásszínre (két független adat: az ini p4-e és az előnézet pixele ugyanabban a lépésben) és a képváltásra (J5d); a bináris támasz csak a gomb/egyszeri használat oldalán van.

#### T5: A `Ctrl+3` kijelölés nélkül az 1. képet nyissa, többes kijelölésnél a rács szerinti elsőt (jegy: #7384)

**Mi a hiba.** (a) Kijelölt kép nélkül (a mappa kijelölve) az eredeti `Ctrl+3` megnyitja az 1. képet, a PicasaPy nem csinál semmit. (b) Két kijelölt képnél az eredeti a rács szerinti elsőt nyitja, a PicasaPy a kattintás-sorrend szerinti elsőt: "gradient, majd Ctrl+kattintás a `color_patches`-en" sorrendnél a gradientet.

**Eredeti.** E1, E3: J1a 9. kép (`gray_ramp.jpg`, "1 of 24", 1. fül, a tálcán "Folder Selected - 24 photos"); J1b 12. és 19. kép (mindkét kijelölési sorrendben `color_patches`, "2 of 24"). Bináris: a `Ctrl+3` ága `0x005e624f` kijelölés-ellenőrzés nélkül kattintja a `thumbui/fullview` gombot (`0x005e6254 call 0x9cd8a0`, `0x005e6259 jmp 0x5e65f7`), tehát a kijelölés kezelése a gomb mögötti nézetbe lépésben van (a `0x005cb990` menükezelő és a `0x005c90f0` ugyanezt a gombot kapcsolja).

**Nálunk.** `MainWindowLibraryActions.qml:95-100` (`nezdEsSzerkeszd`: `sorok.length === 0` esetén kilép, egyébként `sorok[0]`), `selection.js:7-12,32-36` (`toggled` a végére fűz, `effectiveRows` a kattintás-sorrendet adja), `MainLibrarySelectionState.qml:274-280`.

**Teendő.** `nezdEsSzerkeszd()`: kijelölés nélkül a megjelenített rács 1. képét nyissa; többes kijelölésnél a legkisebb sorindexűt (`Math.min`), nem a `sorok[0]`-t. A menü, az Enter és a dupla kattintás útjához ne nyúljon: egy képpel egyeznek, többesnél a B8 felvétel dönt.

**Kész, ha.**
1. Mappa kijelölve, nincs kép kijelölve, `Ctrl+3`: az 1. kép nyílik, 1. fül, "1 of 24" (J1a 9.).
2. Két kijelölt kép, mindkét kijelölési sorrend: a rács szerinti első nyílik (J1b 12., 19.).
3. Egy kijelölt képnél változatlan (J1a 15.), és az Escape után a kijelölés megmarad (J1a 17.).
4. Valódi billentyűesemény-teszt (nem a függvény közvetlen hívása), rontás-kontroll: a teszt elbukik, ha a `sorok[0]` visszakerül.

**Bizonyítottsági fok.** Erős: felvétel (két kijelölési sorrend) és bináris (`0x005e624f`).

#### Javított Colab-lépéssorok a blokkolt pontokhoz

| Pont | Fájl | Mit dönt el | Lényeg |
|---|---|---|---|
| B8 | B1 | Enter, dupla kattintás és `Ctrl+3` többes (két és három) kijelölésnél | két kijelölés (gradient, majd `color_patches`) Enter, majd dupla kattintás a gradienten; három kijelölés (4., 6., 2. kép kattintási sorrendben) `Ctrl+3`; mindegyik után Escape |
| B9 | B2a | kiíródik-e az ini 60 s idle után a szerkesztőben | egy húzás, 6x10 s várakozás, kimenet: ini és fájllista |
| B9, B3 | B2b | fülváltás után új réteg lesz-e; egy Undo mit vesz le | húzás, 1. fül, vissza, második húzás (másik csúszka), egy Undo, 30 s várakozás, ini |
| B9 | B2c | az Escape (kilépés) kiírja-e az ini-t | húzás, 3 s, Escape, 3 s, ini |
| B10 | B4a, B4b, B4c, B4d | a mintavétel mérete: a p4 tiszta folt vagy keverék, a határtól 0, 10, 20, 40 képpontra | pipetta, egy kattintás a bézs folt jobb szélén (x 782, 772, 762, 742), Escape, 10 s, ini p4 |
| B10 | B4u | az Undo gomb és a színminta a pipetta után | pipetta, mintavétel, 10 s, majd fülváltás és vissza (újrarajzolás) |
| B5 | B5a | pipetta + a Kiemelések ki-be húzása (a Színhőmérséklet érintetlen), mentés | a mentés előtti `filters` sor a `.picasaoriginals` ini-ben: marad-e a réteg nullás csúszkákkal és nem semleges p4-gyel |
| B5 | B5b | csak a Kiemelések ki-be húzása, mentés | marad-e a réteg négy nulla és semleges p4 mellett; a Save egyáltalán felkínálódik-e |
| B11 | B6 | betöltött `fill=1,0.5` + Derítő-húzás az 1. fülön + Undo | új `fill` réteg vagy a meglévő módosul; az Undo mit vesz le |
| B7 | (nincs) | valódi írási hiba | **hiány**: a végrehajtó `csak_olvashato` lépése `os.chmod 0444` (rootként Wine alatt nem biztos, hogy tilt), és a fájllista csak a feladat végén készül. Kell: megbízható írásvédelem (pl. nem-root futtatás vagy `chattr +i`) és egy közbenső `kepmappa` pillanatkép a mentés előtt. Ez végrehajtói (gépezet-repó) igény, nem terméktétel. |

A lépéssorok mind átmentek a figyelő saját validátorán (lépésszám, kulcsok, kimenetek, koordináták az 1280x1024-en belül). A koordináták a J0 utáni javított értékek (a csúszkák y 213/266, a Visszavonás (70,412), a pipetta (148,374), a bézs folt (682,588)).

### Független újralevezetés (#140)

Nem készült. A T1 foka a zárókör 2 óta "megerősített" (a bináris és a J2a ini-je két független út), ezért a külön újralevezetés nem feltétel; ha mégis készül, a független kérdés: melyik szűrőt aktiválja a szerkesztő 1. és 2. füle (`0x005d7780`, `0x005d77d0`), és melyik szűrő paraméterét állítja a `flightslider1/scaleslider` csúszka (`0x005de8e0`).

### Nyitott kérdések mérlege

Nyitott kérdések: 0 nyílt · 17 lezárva (ebből 6 igazolt eltérés) · 6 blokkolt · 0 hatókörön kívül · 0 „csak nyitva" (összesen 23 tétel).

- **Lezárva (17):** Z1-Z12 és B1, B2, B3, B4, B6. Az igazolt eltérések: Z11 (T1, kint: #7369), Z12 (T2, kint: #7370), B1 (T5), B2 és B3 (T3), B4 (T4).
- **Blokkolt (6):** B5 (pontos nulla; B5a, B5b), B7 (végrehajtói hiány: megbízható írásvédelem és közbenső fájllista), B8 (többes kijelölés Enter/dupla kattintás; B1), B9 (az ini kiírásának kiváltója; B2a, B2b, B2c), B10 (pipetta mintaméret, Undo-gomb, színminta; B4a-d, B4u), B11 (betöltött `fill` melletti húzás; B6). Egyik sem blokkolja a T3, T4, T5 fejlesztését: azok kész-feltételei a hiányzó felvételek nélkül teljesíthetők (a T3 3-4. pontja kimondja, mi nem mért).
- **Hatókörön kívül (0):** nincs olyan pont, amelyről tulajdonosi döntés született volna.
- **Címke-javaslat a jegyre:** a #7345 a J0-J7 kiértékelésével lezárható; a hat blokkolt tételből új, kisebb kutatási jegy (felvétel) nyitandó `bináris-kutatható` címkével, a B7 külön gépezet-jegy a privát repóban. A T3, T4, T5 külön fejlesztői jegy (`PicasaPy`, UI-sáv). A T3 és a T4 is az `editorpanel_logika.js`/`PhotoViewerEditWorkflow.qml`/`EditorPanel.qml` forró zónát érinti, ezért egymás után, ne párhuzamosan (előbb a T3); a T5 a `MainWindowLibraryActions.qml`/`selection.js` fájlokat érinti, vele párhuzamosan vihető.
- **Átvezetés a #7327-re:** a `paritas-folyamat-7327.md` Derítőfény-sorának „NINCS MEG: az eredeti tárolt érték" kérdését F5, F6 és a J2a ini-je megválaszolja (az 1. fül csúszkája `fill=1,<érték>`); a J2b/E5 szerint a csúszka nyitáskor alaphelyzetben áll, ezt a lap kész-feltételeinél is figyelembe kell venni. A lapot a #7327 gazdája vezesse át.

**Módosított fájlok:** `docs/specs/paritas-folyamat-7345.md` (ez a lap), `changelog.d/7345.md`.
