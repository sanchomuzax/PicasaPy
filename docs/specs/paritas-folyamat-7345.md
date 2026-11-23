# A Hangolás lap folyamata: eredeti Picasa 3.9 és PicasaPy (#7345)

**Állapot: zárókör után nyitott, két igazolt eltéréssel.** A statikusan eldönthető pontok lezárultak (12 lezárva, ebből két igazolt eltérés: a Gyakori javítások Derítőfény-csúszkája `fill`, nem `finetune2`; a pipetta fülbe lépéskor kikapcsol), hét pont futásmérésre vár (lásd a „Zárókör" szakaszt a lap végén). Az első kör állapota: az eredeti teljes futásút (egy/több kijelölt kép, húzás közbeni előnézet, `.picasa.ini` írásának időpontja, Undo/Redo és a kép mentése) nincs egyetlen lépéssorban lemérve.

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

*(Az első kör következtetése; a zárókör felülírja.)* Az első körben nem volt bizonyított, felhasználó számára látható Hangolás-eltérés, ezért fejlesztői jegytörzset nem javasoltam. A zárókör két eltérést igazolt (T1, T2), mindkettőhöz kész jegytörzs van a „Zárókör" szakaszban. A #7345 kutatási jegy a J1-J7 Colab-felvételekre nyitva marad.

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
| Z11 | Melyik szűrőt szerkeszti a két Derítőfény-csúszka | **LEZÁRVA, igazolt eltérés** | F5, F6, lásd T1. |
| Z12 | A pipetta állapota a fül váltásakor | **LEZÁRVA, igazolt eltérés** | F3, lásd T2. |
| B1 | Belépés Entertől, dupla kattintástól, helyi menüből, valamint **többes kijelölésnél**: melyik kép nyílik, melyik fül, mi a filmszalag | **BLOKKOLT** | A bináris a nézőbe lépés feltételét (`0x005c90f0` csak a fullview-gombot kapcsolja, a kijelölés-választás a nézet kezdőkép-kiválasztásában van) nem adja meg futásmérés nélkül; kell: J1. |
| B2 | A `.picasa.ini` írásának időpontja és az Undo-bejegyzések száma a húzás, a lezárás és a fülváltás körül; rács/bélyegkép/állapotsor hatása | **BLOKKOLT** | F7 megmutatja a két eseményt, de azt nem, hogy a `+0xc8` jelző mit vált ki. Kell: J3. |
| B3 | Undo/Redo után a csúszkák állása; képváltás és újranyitás után a megjegyzett állapot | **BLOKKOLT** | Nincs bináris ág, ami a csúszkák visszatöltését adná; a `0xd34678` tömb csak az ismételt érték kiszűrője. Kell: J4. |
| B4 | A pipetta mintavétele: egy képpont vagy terület, melyik kép (forrás vagy előnézet) | **BLOKKOLT** | Az egér-kezelő (`0x008fbf10`) a szűrő `[+0x10]` visszahívásának adja a törtkoordinátákat; a visszahívás törzse a Hangolás szűrőre nincs azonosítva. Kell: J5 (kontrollált színfoltos kép). |
| B5 | A négy csúszka nullázása semleges szín mellett: törlődik-e a `finetune2` réteg; mentés utáni fájl, backup | **BLOKKOLT** | A `zerostate="zero"` fogyasztója nincs azonosítva; a Picasa saját `finetune2=1,0,0,0,006b8088,0` sora azt mutatja, hogy semleges színnel nullás csúszkákkal létezik réteg, de azt, hogy a csúszkák nullára húzása megtartja-e, csak a mérés dönti el. Jelölt: `edit_controller_effects_finetune_mixin.py:181-182`. Kell: J6. |
| B6 | A T1 megerősítése: a Gyakori javítások csúszka valóban `fill=` sort ír, és egy meglévő `fill=` réteg értékét mutatja nyitáskor; a másik fül csúszkájának állása | **BLOKKOLT** | A bináris és a felirat egyezik, az ini-visszaolvasás hiányzik (a `job-812` `allapot.json`-ja nem adta). Kell: J2. |
| B7 | Írásvédett vagy hálózati mentési hibaág a Hangolás után | **BLOKKOLT** | Közös a #7327 8. Colab-lépésével; kell: J7. |

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

**Kész, ha.**
1. A Gyakori javítások csúszka húzása után a láncban `fill=1,<érték>` van, `finetune2` nincs; a Hangolás fülön a csúszka 0-n áll.
2. A Hangolás csúszka húzása után `finetune2` van a láncban, a `fill` változatlan.
3. Egy `fill=1,0.5` sort tartalmazó kép megnyitásakor a Gyakori javítások csúszka a 0.5-nek megfelelő állásban van.
4. A Visszavonás-felirat a Gyakori javítások csúszka után `Visszavonás: Derítőfény`, a Hangolás után `Visszavonás: Finomhangolás`.
5. A `job-812` és a J2 felvétel a PicasaPy kimenetével párban egyezik (felirat, kép, ini-sor).
6. Valódi egéresemény-teszt mindkét csúszkára (nem csak a kontroller-metódus hívása), és rontás-kontroll: az a teszt elbukik, ha a Gyakori javítások csúszka visszakerül a `finetune2`-re.

**Bizonyítottsági fok.** Erős: két független út (bináris utasítások F5, F6; mérésfelirat és korpusz). Nem megerősített, mert az ini-visszaolvasás hiányzik (B6, J2).

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

**Teendő.** A Hangolás fülre lépéskor (`activeTab` 1-re váltása) a pipetta kapcsoljon ki (`neutralPickerActive = false`). A mintavevő felület csak a Hangolás fülön legyen aktív (`neutralPickerActive && activeTab === 1`). A kattintás utáni kikapcsolás maradjon. A fül elhagyásakor az eredeti viselkedése nincs mérve (J5), a fenti korlát védelem, nem mért eltérés.

**Kész, ha.**
1. Élesített pipetta után fülváltás Alapvető javítások vagy Effektek fülre, majd vissza a Hangolásra: a pipettagomb nincs lenyomva, és az első képkattintás nem ír `finetune2` réteget.
2. Élesített pipettával a nem Hangolás fülön a képre kattintás nem hívja a `pickNeutralColor`-t és nem módosít láncot.
3. A meglévő egyszeri használat (kattintás után kikapcsol) változatlan.
4. Valódi egéresemény-teszt (tab-váltás, kattintás a képre), rontás-kontroll: a teszt elbukik, ha az `onActiveTabChanged` visszakerül a mai alakra.
5. A J5 felvétel 6-7. lépése egyezik a PicasaPy kimenetével.

**Bizonyítottsági fok.** Erős a belépési oldalra (`0x005d77d0` utasításai, a PicasaPy kódja két helyen). A fül elhagyása utáni eredeti viselkedés nincs mérve.

### Colab-lépéssor (a blokkolt pontokhoz)

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

### Független újralevezetés (#140)

Nem készült. Amíg nincs meg, a T1 foka "erős", nem "megerősített"; a független kérdés: melyik szűrőt aktiválja a szerkesztő 1. és 2. füle (`0x005d7780`, `0x005d77d0`), és melyik szűrő paraméterét állítja a `flightslider1/scaleslider` csúszka (`0x005de8e0`).

### Nyitott kérdések mérlege

Nyitott kérdések: 0 nyílt · 12 lezárva (ebből 2 igazolt eltérés) · 7 blokkolt · 0 hatókörön kívül · 0 „csak nyitva".

- **Lezárva (12):** Z1-Z12 (a fenti táblázat). Az igazolt eltérések: Z11 (T1) és Z12 (T2).
- **Blokkolt (7):** B1-B7; mindegyikhez a J1-J7 Colab-feladat adja a hiányzó bizonyítékot (a tulajdonos gépe vagy szeme nem kell, a Colab-gép elvégzi). Egyik pont sem blokkolja a T1 és T2 fejlesztését: azok kész-feltételei a Colab-felvételek nélkül is teljesíthetők, a J2 és J5 csak megerősít.
- **Hatókörön kívül (0):** nincs olyan pont, amelyről tulajdonosi döntés született volna.
- **Címke-javaslat a jegyre:** a #7345 maradjon `bináris-kutatható` és kapjon `in-progress` nélküli `ready` állapotot a J1-J7 felvételéhez; T1 és T2 külön fejlesztői jegy (`PicasaPy`, UI-sáv, mindkettő a `EditorPanel.qml`/`EditorTabCommonFixes.qml`/`editorpanel_logika.js` forró zónát érinti, ezért egymás után, ne párhuzamosan).
- **Átvezetés a #7327-re:** a `paritas-folyamat-7327.md` Derítőfény-sorának „NINCS MEG: az eredeti tárolt érték" kérdését F5 és F6 megválaszolja (az 1. fül csúszkája `fill`); a lapot a #7327 gazdája vezesse át.

**Módosított fájlok:** `docs/specs/paritas-folyamat-7345.md` (ez a lap), `changelog.d/7345.md`.
