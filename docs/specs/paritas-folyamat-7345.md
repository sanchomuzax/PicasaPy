# A Hangolás lap folyamata: eredeti Picasa 3.9 és PicasaPy (#7345)

**Állapot: a J0-J7, job-895..906, job-932..935 felvételek és a B15 bináris részvizsgálata kiértékelve.** A 27 pontból 24 lezárva, ebből tíz igazolt, látható eltérés; egy pont fejlesztői jegytörzzsel átadva (B8, #7412); kettő blokkolt (B7, B15). A B15 bináris részvizsgálatát és a hiányzó összekötő bizonyítékot lásd a „B15 bináris vizsgálata” szakaszban. A korábbi fejlesztői jegytörzsek T1-T6 változatlanok; a job-932..935 eredményeit és a T7 jegytörzset lásd a „Job-932..935 eredménye” szakaszban. A kutatási jegyet nem módosítottam GitHubon.

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
| **Színminta a pipetta után (B15).** A `finetune2` `<colorcircle id="0"/>` leírója p4-hez kötött (`0x0090eda0`); a `0x00752020` az aktív objektum virtuális `+0x54` slotját hívja. A leíró/RTTI és argumentumszám alapján a `CGenericFilter` `0x008fbee0` slotja statikus célként illeszkedik; az alapága paraméterbe ír és nullát ad vissza, ezért nem igazolt p4-getter. A `ytColorCircleNode` (`0x00a66ea0`) a saját színállapotából rajzol a `0x00aa1840` szoftveres képpuffer-raszterezővel; a p4 és a node mezői közti kapcsolat hiányzik. | A QML szó szerinti sora: `color: panel.neutralColor === "" ? "#000000" : panel.neutralColor` (`src/picasapy/app/qml/PicasaPy/EditorFinetunePanel.qml:241`). A getter a látogatás p4-ét olvassa (`src/picasapy/app/edit_controller_effects_finetune_mixin.py:70-76`). | **BLOKKOLT / NINCS MEG (B15), eltérés nincs igazolva.** A `0x009c50d7` node-színforrás p4-kapcsolata és a `0x00c90874` CFilterStackUI +0x08 hívó/fogyasztó nincs meg; lásd a „B15 bináris vizsgálata” részt. |

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

A felvétel a privát eszköztár `eszkozok/colab_felmero.py` segédjével készüljön; töltsd le a `kepernyokep`, `ablakmeret`, `allapot`, `picasa_ini` és `export` kimeneteket. A `db3` mentése csak akkor szükséges, ha a művelet az index állapotát is láthatóan megváltoztatja.

1. Könyvtárnézet kijelölés nélkül, egy képpel és két képpel: nyisd meg külön-külön a Nézet menü `Ctrl+3`, Kép menü `Ctrl+3`, indexkép-helyi menü Enter, dupla kattintás és `Ctrl+Shift+O` útját. Jegyezd fel, mi tiltott, hova nyílik és hány képet érint.
2. Egy képpel lépj a második, Tuning fülre. Rögzítsd a csúszkák és gombok állapotát, majd próbáld a `+`, `=`, `-`, `_` karaktereket fókuszált csúszkán. Mozgasd külön-külön mind a négy csúszkát bal szélre, középre, jobb szélre és vissza. Fényképezd le a panelt a húzás alatt és felengedés után.
3. Minden változás után olvasd vissza az érintett kép `filters=` sorát és az eredeti fájl hashét. Kattints Undo, Redo, képre váltás, majd vissza; írd fel, mi marad a panelen és az ini-ben.
4. Nézd meg, megjelenik-e a közös `ok`, `cancel`, radír/reset gomb slider-húzás után. Ha megjelenik, külön tiszta indulásból próbáld, és minden gomb után rögzíts panelt, ini-t, képet, hash-t és undo/redo állapotot. Ha nem jelenik meg, jegyezd fel, hogy nincs Tuning-módú Cancel/Reset.
5. Húzd a csúszkákat nullára egy külön olyan másolaton, ahol már van semleges-szín p4 érték. Ezután mentsd a képet a Picasa mentési parancsával; rögzítsd a `.picasa.ini`, eredeti fájl, backup és export változásait. A lépés eldönti a jelenlegi kódban észlelt p4/nullázási kérdést.

## Következtetés és jegyjavaslat

*(Az első kör következtetése; a zárókör és a zárókör 2 felülírja.)* Az első körben nem volt bizonyított, felhasználó számára látható Hangolás-eltérés, ezért fejlesztői jegytörzset nem javasoltam. A zárókör két eltérést igazolt (T1, T2; mindkettő kint van: #7369, #7370). A zárókör 2 (J0-J7 felvételek) három további eltérést igazolt, mindhárom látható: **T3** a Hangolás-csúszkák modellje (alaphelyzet, egy Undo-lépés látogatásonként, új réteg a betöltött mellé), **T4** a pipetta (forrásszín, képváltás), **T5** a `Ctrl+3` kijelölés nélkül és többes kijelölésnél; kész jegytörzsük a „J1-J7 eredménye" szakaszban van. A T1 3. kész-feltétele megdőlt (a csúszka nyitáskor alaphelyzetben áll). A #7345 kutatási jegy lezárható: a maradék hat tételhez kész javított lépéssor (B1, B2a-c, B4a-d, B4u, B5a-b, B6) vagy megnevezett végrehajtói hiány (B7) tartozik, ezekből új felvételi jegy nyitandó. A zárókör 3 (job-895..906) a T6 jegytörzset és a T4 kiegészítését adta; a maradék hat tétel állapota a „Nyitott kérdések mérlege" szakaszban.

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
| B5 | A négy csúszka pontos nullázása: törlődik-e a `finetune2` réteg; mentés utáni fájl, backup | **LEZÁRVA, igazolt eltérés** (T6) | J6c, J6f (E8, E12) és job-904, job-905 (E25, E26): pipetta-szín nélkül a csupa nulla réteg eltűnik, a visszavonási lépése is (Undo és Újra tiltott, nincs ini, nincs mit menteni); pipetta-színnel a réteg négy nullával megmarad, a kép a pipettás állapot, a Save felkínálódik és a mentett kép szerkesztett. A #7383 ága a pipettás esetet jól kezeli, a pipetta nélküli esetben az Undo-lépés megmarad (T6). |
| B6 | A T1 megerősítése: a Gyakori javítások csúszka `fill=` sort ír; a másik fül állása | **LEZÁRVA** (T1 megerősítve, a 3. kész-feltétel megdőlt) | J2a, J2b (E4, E5): `fill=1,0.523364` és `finetune2` külön sorban; a másik fül csúszkája 0-n. A betöltött `fill` réteg melletti húzás ága külön tétel (B11). |
| B7 | Írásvédett vagy hálózati mentési hibaág a Hangolás után | **BLOKKOLT** (végrehajtói hiány) | J7 (E13): az írásvédett (`chmod 0444`) fájlon a mentés hibaablak nélkül lefut. Hogy az írásvédelem a mentéskor tényleg érvényben volt-e, nem igazolt (rootként a Wine-os írást a mód nem tiltja, és a fájllista csak a feladat végén készül). Hiány: a végrehajtó nem tud megbízhatóan írási hibát előidézni. |
| B8 | Enter, dupla kattintás és helyi menü **többes kijelölésnél**: melyik kép nyílik | **BLOKKOLT** (javított lépéssor: B8) | job-895 (E16-E19): az Enter két kijelölésnél (gradient, majd color_patches) a color_patches-t nyitja, a kattintás-sorrend szerinti első kizárva; ebben a sorrendben a rács szerinti első és az utoljára kattintott ugyanaz a kép, ezért a kettő nem választható szét, és nálunk az Enter az utoljára kattintottat nyitja. A lépéssor Enterje egy képre szűkítette a kijelölést, így a dupla kattintás próbája nem többes kijelölésnél készült; a helyi menü nem szerepelt benne. |
| B9 | A `.picasa.ini` kiírásának kiváltója és késleltetése | **LEZÁRVA** (nincs látható eltérés) | job-896, job-897, job-898 (E20-E22): 62 másodperc tétlenség után sincs ini (nem időzítő ír); van ini fülváltás után (J3b), Undo után (E22, J4a) és a nézőből kilépéskor (E21, J3d, J4b). Nálunk minden véglegesítés azonnal ír (`edit_controller_save_mixin.py:145-169`); ez a futó programban nem látszik, és összeomláskor megőrzi a munkát, ezért NEM másoljuk (alapértelmezett döntés, a tulajdonos felülbírálhatja). Nem szétválasztott: a képváltás (nyíl) és a Save mint kiváltó. A `redo=` kulcs tartós Újra-listát jelenthet: B12. |
| B10 | A pipetta mintavételének mérete (pont vagy terület), az Undo-gomb és a színminta a pipetta után | **LEZÁRVA, igazolt eltérés** (T4 kiegészítése) | job-899..903 (E23, E24): a mintavétel TERÜLETÁTLAG (a határon keverék, 10 képpontra tiszta folt); nálunk egyetlen képpont (`edit_preview.py:491-508`). Az Undo-gomb az eredetiben a pipetta után késve frissül (fülváltásig tiltott), nálunk azonnal: nem másoljuk (alapértelmezett döntés: a gomb a belső állapotot késve mutatja, az oka Wine-újrarajzolás is lehet). A terület pontos mérete (B14) külön tétel; a színminta p4-rajzolása külön nyitott pont (B15). |
| B11 | Betöltött `fill` réteg melletti húzás: új `fill` réteg vagy a meglévő módosul; az Undo hatása | **LEZÁRVA, igazolt eltérés** (T6) | job-906 (E27): a betöltött `fill=1,0.5` mellé új `fill` réteg kerül (`fill=1,0.500000;fill=1,0.523364;`), a két réteg halmozódik (szürke folt 169 -> 200); nálunk a betöltött réteg helyben cserélődik (`session_effects.py:136-151`). Az Undo hatása és az ismételt húzás nem mért (a lépéssor Undo-kattintása az 1. fülön célt tévesztett): B13. |
| B12 | Tartós Újra-lista: a `redo=` kulcs Undo után, kilépés és újranyitás után is újrajátszható-e | **BLOKKOLT** (javított lépéssor: B12) | job-897 (E22): az Undo után az ini `redo=` sora a levett réteget őrzi. Hogy újranyitás után az Újra gomb él-e és visszahozza-e a réteget, nem mért. Nálunk a redo-verem csak memóriában él (`edit_controller_save_mixin.py:162-169` csak `filters=`-t ír). |
| B13 | Gyakori javítások Derítőfény-csúszka betöltött `fill` mellett: ismételt húzás egy látogatáson belül, két Undo, Redo | **LEZÁRVA, egyezik** | job-948: két húzás után a végső ini `filters=fill=1,0.500000;fill=1,0.859813;`, tehát egy látogatás egyetlen új réteget ír a betöltött mellé, a második húzás ezt frissíti. Nálunk ugyanígy (`edit_controller_fill_visit_mixin.py`, #7397). |
| B14 | A pipetta mintaterületének pontos mérete és alakja | **BLOKKOLT** (javított lépéssor: B14) | job-899..902 (E23): a határon (x=782) a bézs súlya 0,400 (2/5), 10 képpontra tiszta. A középre igazított páratlan négyzetek közül csak az 5x5 adja a 2/5-öt; más ablak (pl. 10 széles) egyetlen pontból nem zárható ki. A határtól 1-4 képpontra vett minták döntenek. |
| B15 | A színminta-korong színe a pipetta után | **BLOKKOLT / NINCS MEG** (a p4→node kapcsolat nem bizonyított) | E24: Wine alatt a korong fekete; ez önmagában nem dönt Windowsos Picasa-viselkedésről. A `0x00752020` hívási adatútja és az RTTI/ABI alapján a `CGenericFilter::vftable` `+0x54` slotja (`0x008fbee0`) a statikus cél; alapága paraméterbe ír és nullát ad vissza, a callbackág tényleges mezőértéke nincs meg. A node mezőinek igazolt írói: `0x0052d9b0` báziskonstruktor (`+0x268` átadott szín, `+0x26c=0`) és `0x009c4da0` leszármazott konstruktor (`+0x26c` újraszámítása); a `0x0050cf90` külön Desaturate-panel útja ír `+0x268`-at. A vtable-metódusok nem írják a mezőket. A p4 és az építőszín kapcsolata, valamint a `0x00752020` visszatérő EAX hívóoldali fogyasztása nincs meg. Következő irány: az építő szín `[esp+0x20]` forrása (`0x009c50d7`) és a CFilterStackUI +0x08 slot hívója/fogyasztója (`0x00c90874`), vagy Windowsos mintavétel utáni felvétel. GDI/GDI+ hívás nincs a renderelő útvonalon. |

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
3. A látogatás előtt a láncban lévő `finetune2` (betöltött vagy egy korábbi látogatásból való) mellé új réteg kerül; az Undo csak az újat veszi le. A fül elhagyása utáni húzás új réteget ad. **Mérve (zárókör 3, job-897, E22):** Kiemelések húzása, 1. fül, vissza, Árnyékok húzása két külön réteget és két külön Undo-lépést ad; egy Undo csak a másodikat veszi le (a kép a Kiemelések-réteg állapotára áll vissza), az ini `filters=` sora az első réteg, a `redo=` sora a levett. A #7383 ága ezzel egyezik (`EditorPanel.qml:272-274`, `PhotoViewerEditorPanel.qml:60`, `edit_controller_finetune_visit_mixin.py:114-164`).
4. Az 1. fül Derítőfénye (`fill` réteg) ugyanígy: alaphelyzeti csúszka. **Eldőlt (zárókör 3, job-906, E27):** a betöltött `fill` mellett a húzás új réteget ad, NEM cserél: ez a T6 tárgya.

**Kész, ha** (látás alapú, a felvétel kockáival párban):
1. `fill=1,0.5` és `finetune2` sort tartalmazó kép megnyitásakor mindkét fülön minden csúszka alaphelyzetben áll, a renderelt kép a lánc szerint korrigált (J2b 14., 16.; J2a 28., 30.).
2. Hat húzás négy csúszkán, majd egy Undo kattintás: minden visszaáll, az Undo tiltott, az Újra a lépés nevét viseli (J3d 23., 25.).
3. Négy húzás, Undo, Undo, Redo: a kép szerkesztett, a csúszkák alaphelyzetben (J4a 25.).
4. A Hangolásról elmenve és visszatérve a csúszkák alaphelyzetben (J3b 5.).
5. Betöltött `finetune2=1,0,0,0,ffccc6b2,0` mellett egy húzás után a láncban két `finetune2` sor áll, a második p4-je `00000000` (J6c ini-párja).
6. Valódi egéresemény-teszt a csúszkákra és az Undo/Redo gombokra (nem a kontroller-metódus hívása), rontás-kontroll: a teszt elbukik, ha a csúszkák ismét a mentett értékre állnak.
7. Vizuális elfogadás: a renderelt kimenet és a J3d/J4a/J2b kockák összevetése mért eltéréssel; a szomszéd (Gyakori javítások fül, effektfülek, Undo/Redo gombsor) regresszió-ellenőrzése a kiadás előtt.

**Bizonyítottsági fok.** Erős a viselkedésre (nyolc felvétel, azonos eredmény); a bináris oldal összhangban van, de a kezdőértéket író utasítás nincs azonosítva. A zárókör 3 a 3. pontot is megmérte (job-897), és a 4. pontot cáfolta (a `fill` is új réteget kap, T6).

#### T4: A pipetta a forrásképből mintázzon, és képváltáskor kapcsoljon ki (jegy: #7385)

**Mi a hiba.**
1. A PicasaPy a MEGJELENÍTETT (szerkesztett) előnézetből mintáz; az eredetiben a p4 a forrás színe. Nem nulla Színhőmérséklet vagy korábbi semleges szín mellett az újabb mintavétel így mást ír az ini-be (nálunk `ffcf9c54`, illetve a már semlegesített szürke; az eredetiben `ffc89779`).
2. A PicasaPy-ban képváltáskor a pipetta élesen marad, az eredetiben kikapcsol.

**Eredeti.** E10, E11: a J5a 23. és 25. képe (a bézs folt előnézete `cf9c54`), az ini p4-e `ffc89779` (a forrás `c89779`); a mintavétel után a folt szürke (`a1a1a1`, 15. kép); J5d 13. kép (lenyomott gomb), 15. és 17. kép (képváltás után felengedett). Bináris: a pipetta-gomb állapota a szűrőkezelő módjává alakul (`0x005f8380`, `0x005f84ee-0x005f8502`), a kép-egéresemény kezelője egyszer használatra kapcsolja ki (`0x00752800`, `0x00752883-0x007529c0`, F3, F4). A mintavétel forrására és a képváltási kikapcsolás kiváltójára bináris cím nincs azonosítva; a viselkedést a felvételek bizonyítják.

**Nálunk.** `edit_preview.py:491-508` (`sample_color` a megjelenített képből), `edit_controller_effects_color_mixin.py:53-72` (`pickNeutralColor`), `PhotoViewerEditWorkflow.qml:691-712` (`onCurrentIndexChanged` nem nyúl a `neutralPickerActive`-hoz), `PhotoViewerNeutralPickArea.qml:24-31`.

**Teendő.** (1) A mintavétel a `finetune2` réteg ELŐTTI lánc képéből történjen (a `gpuPrefixSource` párja), ne a megjelenített előnézetből; a J5a-ban nincs más réteg, ezért a "vágás előtti vagy utáni kép" kérdése NINCS MEG, a mai vágás-kezelést ne változtassa. (2) A képváltás (`onCurrentIndexChanged`) a pipettát kapcsolja ki. A mintavétel méretét a B10 felvétel eldöntötte: terület, lásd a „T4 kiegészítése (zárókör 3)" részt.

**Kész, ha.**
1. Élesített pipetta, következő kép, vissza: a gomb felengedett, az első képkattintás nem mintáz (J5d 15., 17.).
2. Mintavétel a bézs folton, Színhőmérséklet a jobb szélre, újabb mintavétel ugyanott: az ini p4-e a forrás színe (`ffc89779`), nem az előnézeté (J5a ini-je).
3. A mintavétel utáni kép és a J5a 15. kép (a folt szürke) mért eltéréssel összevetve; az eltérés nagyságát a mérés jelenti, túllépés esetén külön jegy (a semlegesítő képlet nem e jegy tárgya).
4. Valódi egéresemény-teszt (gombnyomás, képkattintás, nyíl), rontás-kontroll: a teszt elbukik, ha a mintavétel visszakerül az előnézetre.
5. (Zárókör 3) A határmintavétel: a `color_patches.jpg` bézs foltján x=772, 762, 742 képpontnál a p4 `ffc89779`, a folt jobb szélét követő első kék oszlopon (x=782, y=588 a nézőben 1:1 nagyításnál) `ff74728a` (csatornánként legfeljebb +-1 eltéréssel; job-899..902 ini-je).

**Bizonyítottsági fok.** Erős a forrásszínre (két független adat: az ini p4-e és az előnézet pixele ugyanabban a lépésben) és a képváltásra (J5d); a bináris támasz csak a gomb/egyszeri használat oldalán van.

**T4 kiegészítése (zárókör 3, B10).** A job-899..903 három új, látható tényt ad a #7385 tárgyához (a #7385 ága a pipettához még nem tartalmaz commitot, ezért kiegészítés, nem cáfolat):

1. **Területátlag, nem képpont (E23).** A határon (x=782, az első kék oszlop) a p4 `ff74728a` = (116,114,138): a bézs (200,151,121) és a kék (60,90,150) 8 bites csatornánkénti átlaga, a bézs súlya 0,400 / 0,393 / 0,414 (a kerekítési metszet 0,397-0,402), azaz 2/5. Fényességben (lineárisan) átlagolva a súlyok 0,24 / 0,32 / 0,45 volnának, az nem egyezik. A határtól 10, 20, 40 képpontra a p4 a tiszta folt. Nálunk a `sample_color` (`edit_preview.py:491-508`) egyetlen képpontot ad vissza, a határon tehát a kattintott oldal tiszta színét.
2. **Teendő.** A mintavétel a kattintott képpont körüli négyzet 8 bites csatornánkénti egyszerű átlaga legyen (nem fényesség-lineáris), a `finetune2` ELŐTTI lánc képéből (az (1) pont szerint). A négyzet mérete NYITOTT (B14): a mért négy pontot (x=782, 772, 762, 742) a kattintott képpontra középre igazított páratlan négyzetek közül csak az 5x5 elégíti ki (3x3: 1/3, 7x7: 3/7), ezért az implementáció a legkisebb kielégítő ablakot, az 5x5-öt használja, a tesztben csak a négy mért pontot rögzíti, és a B14 eredménye szerint igazítandó. Más ablak (pl. 10 széles) egyetlen pontból nem zárható ki.
3. **Nem másoljuk (alapértelmezett döntés).** A pipetta utáni Undo-gomb az eredetiben késve frissül: a Hangolás fülön 10 másodperc múlva is tiltott, fülváltás után (1. fül, majd vissza) "Undo Tuning" és aktív (E24, job-903 15., 17., 19.). A lépés létrejön, csak a gomb nem rajzolódik újra; a bináris közvetlen hívási gráfja (`0x00752800` mélység 4-ig) nem éri el az Undo-feliratot állító `0x007533b0`-t és az állapotfrissítő `0x00567680`-at (a vtábla-hívásokat az index nem látja), ezért az ok (az eredeti hibája vagy Wine-újrarajzolás) nincs eldöntve. Nálunk az Undo azonnal frissül (`edit_controller_effects_color_mixin.py:53-72`); a késést, ami hibának látszik, nem utánozzuk.
4. **Színminta (B15).** Az eredeti Wine-felvételeken a korong fekete (E24). A bináris vizsgálat megtalálta a `ytColorCircleNode` mezőinek konstruktorbeli íróit és egy külön Desaturate-panelből érkező `+0x268` írót, de egyik sem köti bizonyítékkal a Hangolás p4-et a megjelenített állapothoz. A `0x00752020` `+0x54` hívásának általános célja is azonosítható, de futásidejű callbackje és a visszatérés hívóoldali fogyasztója nincs meg. Ezért az eredeti mintavétel utáni színe, és így a PicasaPy-val való egyezés/eltérés sem dönthető el. Részletek alább.

**B14 frissítése (job-934).** A hat széli mintapont és a semlegesítés utáni pixelek 5x5-ös, középre igazított négyzetet igazolnak. A `picasa.ini` `ff976084` értéke a forráskép (682,688) körüli 5x5 terület csatornánkénti átlagának kerekítése: RGB (151,96,132). A mintavétel előtti szerkesztett előnézet ugyanott mért színe (191.8,93.4,76.2), ezért ez a mérés a forrásból mintavételt is alátámasztja. A jelenlegi PicasaPy 5 forrásképpontot és egyszerű 8 bites csatornaátlagot használ (`edit_preview_sample.py:39-44,61-64,98-104`), tehát a mintaméret és az átlagolás egyezik. Az `edit_preview_sample.py:39-43` megjegyzése a mért eredmény után is feltevésnek nevezi az 5x5-öt; termékkódhoz ebben a kutatási körben nem nyúltam.

### B15 bináris vizsgálata (E24)

**Kérdés.** A mintavétel után a Hangolás-korong az eredeti `finetune2` p4 színét rajzolja-e; a Wine alatti fekete korong magyarázható-e egy hiányzó vagy nem támogatott GDI/GDI+ hívással?

**Eredeti filter és `+0x54` slot.** A meglévő `filterdesc-registry.md:139` a `finetune2` vezérlőjét `<colorcircle id="0"/>`-ként azonosítja, és a p4 pipetta-színhez köti (`0x0090eda0`, #7400). A `0x00752020` a `CFilterStackUI` mezőláncából kapott aktív objektum virtuális `+0x54` slotját hívja; a `0x0075203b-56` menti, a `0x00752128` tölti vissza a receivert. `CFineTune2Filter`/`FineTune2` nevű RTTI-osztály nincs az indexben; a bináris-alapú `filterdesc-registry.md:7631-7638` szerint a `desat` kivételével az XML-leírók a `CGenericFilter` gyárhoz futnak. Ennek RTTI-vtáblája `0x00cd184c`, `+0x4c` slotja `0x008f6d30`, `+0x54` slotja `0x008fbee0`. A hívó az előző slotnak egy, a `+0x54` slotnak két veremargumentumot ad; a megfelelő metódusok `ret 4`/`ret 8` konvenciója egyezik, ezért a `CGenericFilter` statikus feloldása erősen alátámasztott. A példány tényleges vptr-jét futás közben nem mértük, ezért ez nem közvetlen futásidejű megfigyelés.

```text
0x00752130  mov eax, dword ptr [ecx]
0x00752132  mov eax, dword ptr [eax + 0x54]
0x00752135  push edx
0x00752136  push esi
0x00752137  call eax
0x0075213d  mov ebp, eax

0x008fbee0  mov eax, dword ptr [ecx + 0x18]
0x008fbee3  test eax, eax
0x008fbee5  je 0x8fbefa
0x008fbefa  mov eax, dword ptr [esp + 8]
0x008fbefe  mov edx, dword ptr [eax]
0x008fbf00  mov eax, dword ptr [esp + 4]
0x008fbf04  mov dword ptr [ecx + eax*4 + 0x50], edx
0x008fbf08  xor eax, eax
0x008fbf0a  ret 8
```

A `CGenericFilter` konstruktor (`0x008f6ad0`) `0x008f6b02` címén nullázza a `[this+0x18]` mezőt. Ha ez az aktív példányban így marad, a `+0x54` alapága az `arg2` mutatóról olvas, az `arg1` indexű filtermezőbe ír, majd nullával tér vissza; az EBP-be mentett EAX ezért nem a színérték. Nem nulla `[this+0x18]` esetén a slot ezt callbackként hívja, de az aktív példány futásidejű mezőértéke és a callback célfüggvénye **NINCS MEG**. A node-vtáblákban szintén előforduló `0x009e5730` +0x54 metódus eltérő (egy veremargumentumot vesz át, `ret 4`, geometriai/hit-test állapotot vizsgál), ezért nem illeszkedik a hívás két argumentumához és a `CGenericFilter` statikus feloldásához.

**A node mezői és a teljes mezőírási keresés.** Az RTTI a `ytColorCircleNode::vftable` 17. slotját a `0x00a66ea0` rendererhez köti; ez `[esi+0x268]` és `[esi+0x26c]` értékeket olvas, a `0x00aa1840` képpuffer-raszterezőt hívja, amely a szín-dwordot a célpufferbe írja (`0x00aa1b1f`). A vtable 6. slotja (`0x00a66570`) szintén olvassa/hasonlítja e mezőket; az RTTI-alapú `offset_map.py` a node vtable metódusai közt egyikre sem talált írást. A teljes `.text`-et a kötelező `paszta.py` darabolt bejárásával és `memoria_kapu()` mellett pásztázva 212 `mov` disp32 `+0x268/+0x26c` tárolási jelölt adódott. A `ytColorCircleNode` építésekor először a `ytColorRectNode` báziskonstruktora (`0x0052d9b0`) fut: `0x009c50df`-nél a hívó `EAX=ESI` értékkel adja át a node példányt; a segéd `0x0052d9b2`-nél `ESI=EAX`, `0x0052d9cd`-nél `[esi+0x26c]=0`, majd `0x0052d9df`-nél a hívó által átadott színt `[esi+0x268]`-ba írja. A helper átmenetileg beállítja a `ytColorRectNode` vtable-t (`0x00c8b66c`), amelyet a `0x009c4da0` `0x009c50e6`-nél `ytColorCircleNode`-ra (`0x00cda3ec`) cserél; a származtatott konstruktor ezután `0x009c51ec`-nél számított értéket ír ugyanennek a példánynak a `+0x26c` mezőjébe. A helpernek átadott `[esp+0x20]` szín eredete és p4-hez való kapcsolata **NINCS MEG**.

Van valódi, későbbi külső író is: a `0x0050cf90` RTTI-caston `ytColorCircleNode` példányt vesz elő, majd `0x0050d184`-nél a paraméter RGB-csatornáiból csomagolt értéket ír `[esi+0x268]`-ba. Ez a `CDesaturateFilter::vftable` 20. (0-alapú 19.) slotja, és ugyanabban a függvényben `CDesaturateFilter::strength`/`pickcolor` sztringek vannak; a külön „Pick Color” panel útját írja, nem bizonyítja a `finetune2` út frissítését. A cáfoló jelöltek között a `0x009c5580` ugyanabban a konstruktorban, de már `0x00cda2ec` vtable-jű másik objektumot ír; a `0x00a65890` a `+0x268` értéket számlálóként kezeli (`shr`, 16-bájtos kapacitásméret, majd növelés), a `0x00a68900` pedig `0x00ce4904` (`ytWinTrackNode`) vtable-t telepít. |

```text
0x00a66efc  mov eax, dword ptr [esi + 0x268]
0x00a66f7e  mov eax, dword ptr [esi + 0x26c]
0x00a67016  call 0xaa1840
0x00aa1b1f  mov dword ptr [edi], eax
0x0052d9b2  mov esi, eax
0x0052d9c5  xor eax, eax
0x0052d9cd  mov dword ptr [esi + 0x26c], eax
0x0052d9d9  mov dword ptr [esi], 0xc8b66c
0x0052d9df  mov dword ptr [esi + 0x268], ecx
0x009c50df  mov eax, esi
0x009c50e1  call 0x52d9b0
0x009c50e6  mov dword ptr [esi], 0xcda3ec
0x009c51ec  mov dword ptr [esi + 0x26c], eax
0x0050d184  mov dword ptr [esi + 0x268], ecx
0x009c5574  mov dword ptr [esi], 0xcda2ec
0x009c5580  mov dword ptr [esi + 0x268], ebx
```

**A `0x00752020` visszatérésének útja.** A hívás eredménye `0x0075213d`-nél EAX→EBP; a függvény a befejező ágakon `0x00752222` vagy `0x00752283` címén EBP→EAX értéket állít vissza, majd `ret 0x10`-zel tér vissza. A független újraolvasás a hívási környezetet is ellenőrizte: a belépő negyedik stack argumentum a korábbi `+0x4c` virtuális hívást befolyásolja (`0x00752060`-`0x00752072`); ez nem köti közvetlenül a `+0x54` visszatérő EAX-át a p4-hez. A `0x00752020` a `CFilterStackUI::vftable` `0x00c9086c` táblájának +0x08 slotja; az indexben nincs közvetlen kódcímű hívó, és a függvény törzsében nincs `ytColorCircleNode` setterhívás vagy a két renderermezőbe írás. Az EAX visszatérési érték hívóoldali felhasználása és a p4-hez kötő lánc **NINCS MEG**; következő bináris címek: CFilterStackUI +0x08 virtuális hívó/fogyasztó (`0x00c90874` slotcím), valamint a node-építő színforrás (`0x009c50d7`, `[esp+0x20]`). GDI/GDI+ hívás nincs a renderer útvonalán.

**Nálunk.** A Hangolás-korong QML-sora szó szerint:

```qml
color: panel.neutralColor === "" ? "#000000" : panel.neutralColor
```

(`src/picasapy/app/qml/PicasaPy/EditorFinetunePanel.qml:241`). A `neutralColor` a látogatásból kéri le a p4-et; érvénytelen/üres értéknél üres stringet ad, különben `#rrggbb` színt készít (`src/picasapy/app/edit_controller_effects_finetune_mixin.py:70-76`). A PicasaPy tehát p4-et mutat, üres értéknél feketét. Az eredeti E24 Wine-felvételen a korong szintén fekete, de ebből Windowsos Picasa 3.9-viselkedés nem dönthető el; a bináris sem köti még a mintavett p4-et a renderer mezőihez. Eltérést nem állítok.

**A két független út és cáfolat.** A út: teljes `.text` mezőtárolás-pásztázás `paszta.py`-val, majd a nyers címek RTTI-/utasításszintű szűrése; ez megtalálja a `0x0052d9b0` báziskonstruktort és a `0x0050cf90` Desaturate-panelíróját. B út: RTTI-alapú `offset_map.py` a node-vtable-re, majd a `0x009c4da0` → `0x0052d9b0` közvetlen hívás és regiszter-/stack-adatfolyam külön olvasása; egy friss kontextusú újralevezetés ettől függetlenül visszakövette a `0x00752020` receivert a `CFilterStackUI` `[this+0x24]` → `+0x164` mezőláncán (`0x0075203b-56`, `0x00752128`), és ellenőrizte a +0x4c/+0x54 argumentum- és `ret 4`/`ret 8` konvenciót. Egyezés: a node saját vtable-metódusai nem írják a két színmezőt; a konstruktor-bázis `+0x268`-at állít és `+0x26c`-et nulláz, a leszármazott konstruktor később `+0x26c`-et újraírja; a `0x00752020` EAX-ot EBP-ben őrzi, majd EAX-ban adja vissza, setterig vezető kapcsolat nélkül. A cáfoló próba ellenpéldaként kezelte a `0x0050cf90` írást is: ez valóban azonos node-típust ír, de a RTTI-tulajdonosa és a `CDesaturateFilter::pickcolor`/`strength` sztringek miatt nem a Hangolás p4-frissítése. A másik lehetséges `+0x54` cél, `0x009e5730`, a node-vtáblákban szerepel, de egy argumentumot vesz át és `ret 4`-gyel tér vissza; ez nem illik a hívó két argumentumához. A `0x009c5580`, `0x00a65890` és `0x00a68900` másik objektumot/számlálót/`ytWinTrackNode`-ot érint, így ezek sem adják a hiányzó p4-láncot.

**Következtetés és következő irány.** B15 eredménye: **NINCS MEG**, pontosabban nem dőlt el, hogy a Hangolás pipettájának p4 értéke jut-e a `ytColorCircleNode` megjelenített állapotába; igazolt fejlesztési eltérés nincs, ezért fejlesztői jegytörzs nem készül. A `CGenericFilter +0x54` statikus feloldását a RTTI és az argumentum/ret-konvenció alátámasztja; az alapág nem szín-getter, hanem paraméteríró és nullát ad vissza. Ha a callback mező nem nulla, a callback célfüggvénye **NINCS MEG**. A visszatérési láncban EAX→EBP→EAX igazolt, de a CFilterStackUI +0x08 virtuális hívó és a visszaadott érték fogyasztója **NINCS MEG** (`0x00c90874` slot; hívóoldali xref/dinamikus trace kell); a node-konstruktor színargumentumának p4-forrása is **NINCS MEG** (`0x009c50d7`, `[esp+0x20]`). Ezért a táblázatban az eredeti és a PicasaPy közötti paritás nyitva marad. Ha a statikus bináris vizsgálat nem oldja fel, friss tesztprofillal és tesztképpel Windowsos Picasa 3.9-ben pipettázás előtt/után rögzíts képernyőképet, ablakállapotot, `filters=` sort és exportképet; az E24 Wine-feketeséget ne tekintsd Windows-viselkedés bizonyítékának. A `0x00aa1840` szoftveres képpufferút miatt a hiányzó GDI-hívás nem magyarázza a binárisban azonosított renderelést.

### B15 folytatás (#7422)

**Konstruktorargumentum.** A `0x009c4da0` `0x67` node-ága a parser `vtable+0x20` metódusát hívja (`0x009c50af`), a kimeneti dwordot a `0x009c4330` szín-előkészítőn engedi át (`0x009c50b5`), majd ezt adja a `ytColorCircleNode` konstruktorának: `mov eax,[esp+0x20]; push eax` (`0x009c50d7-0x009c50e1`). A konstruktor az argumentumot a `[this+0x268]` mezőbe írja (`0x0052d9df`). A `0x009c4330` a parserből kapott ARGB értéket csak a `[0xd9fe04]` preferencia bekapcsolt ágában szürkíti; a futó argumentum pontos dwordja **NINCS MEG**. A `finetune2` leírója csak `<colorcircle id="0"/>`-t tartalmaz, színkonstanst nem (`runtime/filterdesc.xml:142-145`; `filterdesc-registry.md:139`). A feldolgozótól (parser) kapott argumentum és a p4 közötti közvetlen kapcsolatot nem találtam.

`0x009c51ec` ugyanebben a parserben külön írja a node `[this+0x26c]` mezőjét: a `%x`-szel beolvasott értéket a parserben kiszámított átlátszósággal módosítja, majd eltárolja. Ez a mező sem a `0x00752020` EAX-ából származik.

**A `+0x54` slot jelentése.** A korábbi B15-ben a `0x00752020` „getterként” szerepelt; ez az elnevezés a most azonosított generikus szűrőútra nem helyes. A `CGenericFilter::vftable +0x54` (`0x00cd18a0`) implementációja `0x008fbee0`. Null `[this+0x18]` callbacknél ez a második argumentum által mutatott dwordot a `[this+0x50+index*4]` paraméterhelyre írja, majd EAX=`0`-val tér vissza (`0x008fbee0-0x008fbf0a`); nemnulla callbacknél a callbacket hívja. A `0x00752020` ezt a slotot hívja (`0x00752130-0x0075213d`), az EAX-ot megőrzi, majd visszaadja (`0x00752222`, `0x00752283`).

A `CFilterStackUI +0x08` slot hívója `0x00808740`: a `call eax` utáni közvetlen fogyasztás a `cmp eax,0xf4241` (`0x0080878f`). Ha az EAX eltér a jelzőértéktől (sentinel), a függvény változatlanul visszaadja; az egyezés egy másik `+0x08` slotra esik vissza. A sentinel értéke bináris `0x000f4241`; itt nem p4 színérték.

**A Hangolás callbackje.** A `finetune2` natív-regiszter rekordja (`0x00cd06a8`) a generikus gyár útjára jut (`0x0050e460` → `0x008f9fe0` → `0x008f6ad0`). A `CGenericFilter` konstruktor nullázza a `[this+0x18]` mezőt (`0x008f6b02`); a gyár a létrehozott objektumot ezután visszaadja (`0x008fa21a-0x008fa222`). A 43 vtable-metódus célzott eltolástérképében a `+0x18` egyetlen írásjelöltje (`0x008fa8d0`) egy belső segédobjektumé, a többi talált metódus olvassa a mezőt (`offset_map.py 0x00cd184c --max-offset 0x30 --reszletes`). Ez alapján a példány létrehozáskori callbackértéke bináris `0`; nemnulla célcím nincs. Későbbi, külső runtime felülírást nem mértem. A constructor és objektumtérkép leírása a `picasa-native-filter-registry.md` „A 204 bájtos szűrő-objektum térképe” részével egyezik.

**Két bizonyítási út és cáfoló próba.** A) Az utasításszintű út a parser dwordját a node konstruktorába, a `CGenericFilter +0x54`-et pedig paraméteríróba követi; EAX státusz/sentinel, nem p4. B) A runtime `filterdesc.xml` `id=0`-t, de színkonstans nélküli korongot ad meg; a registry/RTTI és az objektumtérkép a `finetune2`-t a null callbackes generikus konstruktorhoz köti. A két út egyezik abban, hogy közvetlen p4→node-mező adatátadás nincs igazolva. Cáfolatként megvizsgáltam a teljes `0x00752020` út, a `0x00808740` EAX-fogyasztó és a B15-ben azonosított `[this+0x268]/[this+0x26c]` írók kapcsolatát: a lekérdező (getter) eredményéből node-mezőbe írást nem találtam. Ez a közvetlen út ellen szól, de nem zárja ki a közvetett frissítést.

**Következtetés.** **Nyitott:** nem állapítható meg, hogy a mintavétel után az eredeti Picasa korongja a p4-et vagy más színt mutatja. A `0x00752020` nem p4-getterként bizonyítja a kapcsolatot, a konstruktorérték parserből jön, a rajzoló pedig a node színmezőit olvassa; a köztük lévő futásidejű mezőfrissítő nincs meg. A PicasaPy p4-et rajzol (`EditorFinetunePanel.qml:241`, `edit_controller_effects_finetune_mixin.py:70-76`), de ez alapján eltérés sem állítható. Fejlesztői jegytörzs ezért még nem indokolt. Döntő következő mérés: eredeti Windowsos Picasa 3.9-ben p4 mintavétele előtt/után a korong képernyőképe és a node `[this+0x268]/[this+0x26c]`, valamint a `finetune2` paraméter értékének egyidejű kiolvasása.

**Kész, ha (#7422).**

- ⛔ A konstruktor színargumentumának parser-eredetű bemenete ismert (`0x009c50d7`), de a futó ARGB érték és p4-kapcsolata **NINCS MEG**.
- ✅ A `CFilterStackUI +0x08` hívója `0x00808740`, közvetlen EAX-fogyasztója `0x0080878f`.
- ✅ A `finetune2` generikus példányának létrehozáskori `[this+0x18]` callbackje `0`; nemnulla callbackcél nem merül fel ezen az úton.
- ⛔ A p4 és a kirajzolt node-mezők közti futásidejű kapcsolat, így a korong tényleges színe **nyitott**.

**Lezárás (#7422).** Két független statikus kör (#7345 B15, #7422) után a binárisban nincs olyan út, amely a pipetta p4 értékét a korong `+0x268/+0x26c` mezőibe vinné, és eltérés sincs igazolva. A statikus út ezzel kimerült: a korong színe a feldolgozó futás közbeni állapotából jön, ezt csak futásidejű kiolvasás döntené el, a Wine alatti felvétel (E24) pedig erre nem megbízható. Döntés: a PicasaPy viselkedése marad (a korong a p4-et mutatja, üres értéknél feketét), fejlesztői jegy nem nyílik. Újranyitás csak Windowsos futásidejű mérés alapján.

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

#### Javított Colab-lépéssorok a blokkolt pontokhoz (zárókör 2; lefuttatva: job-895..906, eredményük a „Job-895..906 eredménye" szakaszban)

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

### Job-895..906 eredménye (zárókör 3)

**Módszer és mérce.** A tizenkét felvétel az eredeti Picasa 3.9 Wine alatt, 1280x1024-en: job-895 (B1), job-896 (B2a), job-897 (B2b), job-898 (B2c), job-899, job-900, job-901, job-902 (B4, x=782, 772, 762, 742), job-903 (B4u), job-904 (B5a), job-905 (B5b), job-906 (B6). A mintakép a `color_patches.jpg` (800x800, a nézőben 1:1: a kép bal széle x=382, felső széle y=88, a foltok 200 képpontosak). A `kepernyo__NN` az NN. lépés ELŐTTI állapot; minden döntő kockát megnéztem, a színeket pixelmérés adja (forrásfoltok: bézs `c89779` = (200,151,121), kék `3c5a96` = (60,90,150), szürke 128). Az ini-k és a fájllista a feladat végén készülnek; a job-896 és a job-905 azért nem adott ini-t, mert a mappában nincs: ez maga az eredmény. Az `allapot.json` OCR-je üres, a döntés a kockákból jön. A lépéssorok koordináta-hibája: a job-906 Undo-kattintása (70,412) a Hangolás-fül elrendezése, az 1. fülön a gomb y=380 (lásd E27).

#### Mért tények (E16-E27)

| # | Tény | Döntő kockák | Fok |
|---|---|---|---|
| E16 | Két kijelölt képnél (kattintás-sorrend: gradient, majd color_patches) az **Enter a color_patches-t** nyitja ("2 of 24"), 1. fül; a kattintás-sorrend szerinti első (gradient) kizárva. Ebben a sorrendben a rács szerinti első és az utoljára kattintott kép ugyanaz, a kettő nem választható szét. | job-895 9., 11. | erős (kizárás); a szétválasztás nyitott |
| E17 | A nézőből Escape-pel visszalépve a többes kijelölés **a megnyitott képre szűkül**: a tálca egy képet ír ("color_patches.jpg"), csak az kap keretet. Ugyanígy három kijelölés és `Ctrl+3` után. | job-895 13., 25. | erős |
| E18 | Három kijelölt képnél (kattintás-sorrend: 4., 6., 2. kép) a `Ctrl+3` a 2. képet (color_patches, "2 of 24") nyitja, nem a kattintás-sorrend szerinti elsőt: az E3 harmadik sorrendje. | job-895 21., 23. | erős |
| E19 | A dupla kattintás a gradienten a gradientet nyitja ("3 of 24"), 1. fül; visszalépve csak az marad kijelölve. Mivel az előző Enter már egy képre szűkítette a kijelölést (E17), ez **nem többes kijelölés próbája**. | job-895 15., 17. | erős egy képre; többesre nem mér |
| E20 | A Hangolás-húzás után 62 másodperccel (hat darab 10 másodperces várakozás és egy 2 másodperces) a mappában **nincs `.picasa.ini`** (91 fájl), miközben az Undo gomb "Undo Tuning" és a kép módosított: az ini kiírását nem időzítő váltja ki. | job-896 13., 19., fájllista | erős (62 s-ig) |
| E21 | A húzás után 3 másodperccel a nézőből kilépve (Escape) **az ini megvan**: `filters=finetune2=1,0.000000,0.238596,0.000000,00000000,0.000000;` és `backuphash=`; a könyvtárban a mentés-ikon aktív, a bélyegkép szerkesztett. | job-898 13., 15., ini | erős |
| E22 | Két Hangolás-látogatás (Kiemelések húzása, 1. fül, vissza, Árnyékok húzása): **két külön réteg és két külön visszavonási lépés**. Egy Undo csak a másodikat veszi le (a kép a Kiemelések-réteg állapotára áll vissza: a szürke folt 168 -> 141 -> 167), mindkét csúszka alaphelyzetben áll, az Undo "Undo Tuning" és az Újra "Redo Tuning" is aktív. Az ini az Undo után: `filters=finetune2=1,0.000000,0.238596,0.000000,00000000,0.000000;`, `redo=finetune2=1,0.000000,0.000000,0.238596,00000000,0.000000;`, `backuphash=`. | job-897 16., 19., 21., ini | erős |
| E23 | A pipetta mintavétele **területátlag**: a bézs folt jobb szélén 10, 20 és 40 képponttal a határ előtt (x=772, 762, 742) a p4 a tiszta folt (`ffc89779`); az első kék oszlopon (x=782, a bézs oszlopai 781-ig tartanak) keverék: `ff74728a` = (116,114,138). A bézs súlya 0,400 / 0,393 / 0,414 csatornánként (a kerekítési metszet 0,397-0,402), azaz 2/5, 8 bites csatornánkénti átlaggal; fényességben átlagolva 0,24 / 0,32 / 0,45 volna, az nem egyezik. A 772-es tiszta minta felső korlát: a minta jobb oldali fél szélessége legfeljebb 9 képpont. | job-899..902 13-15., ini, pixelmérés | erős (terület, átlag); a méret nyitott |
| E24 | A pipetta után az **Undo gomb a Hangolás fülön tiltott marad** (10 s múlva is), de az 1. fülre váltva "Undo Tuning" és aktív, és a Hangolásra visszatérve is az: a lépés létrejön, csak a gomb nem frissül. A színminta-korong minden kockán fekete, a visszarajzolás után is, `ffc89779` p4 mellett. | job-903 15., 17., 19. | erős (gomb); a korong oka nyitott |
| E25 | Pipetta (`ffc89779`) után a Kiemelések a jobb szélre húzva, majd a bal szélen túlra húzva pontosan nullára: **a réteg megmarad**, a kép azonos a csak-pipettás állapottal (bézs (161,161,161)), az Undo "Undo Tuning", a Ctrl+S Save ablakot kínál, a mentett kép szerkesztett marad (20557 -> 12502 bájt, "Undo Save"); a `.picasaoriginals` ini `filters=finetune2=1,0.000000,0.000000,0.000000,ffc89779,0.000000;`, a fő ini a mentés után csak `backuphash=`. | job-904 15., 18., 20., 22., ini | erős |
| E26 | Pipetta nélkül ugyanaz a kihúzás és visszahúzás nullára: a kép **az eredetire áll vissza** (bézs (200,151,121)), az Undo ÉS az Újra tiltott, a Ctrl+S nem kínál Save ablakot, nincs ini, nincs `.picasaoriginals`, egyetlen fájl sem változott, a mentés-ikon szürke. A csupa nulla, semleges színű réteg nem marad meg, és a visszavonási lépése sem. | job-905 12., 14., 17., 22., fájllista | erős |
| E27 | Betöltött `fill=1,0.5` mellett az 1. fül Derítőfény-csúszkájának húzása **új `fill` réteget** ad: `filters=fill=1,0.500000;fill=1,0.523364;`. A két réteg halmozódik: a szürke folt 128 -> 169 (csak a betöltött) -> 200 (mindkettő); a `fill=1,0.523364` egyedül 171 (job-844 10. kocka). Az Undo gomb már megnyitáskor "Undo Fill Light" és aktív (a betöltött réteg visszavonható). A lépéssor Undo-kattintása (70,412) célt tévesztett, ezért az Undo hatása nem mért. | job-906 14., 15., 17., ini; job-844 10. | erős (új réteg, halmozódás); az Undo nem mért |

#### Összevetés a PicasaPy mai viselkedésével (1.0.173, `main`)

| Pont | Eredeti | Nálunk (fájl:sor) | Egyezik? |
|---|---|---|---|
| Enter két kijelölésnél | E16 | `LightboxFeed.qml:401-410` a `selectedIndex`-et nyitja, az az utoljára kattintott kép (`MainLibrarySelectionState.qml:274-280`): a job-895 sorrendjében color_patches | igen ebben a sorrendben; a másik sorrend nem mért (B8) |
| Kijelölés a nézőből visszalépve | E17 | `MainWindowWorkspace.qml:213-219` (`selectedIndexes = [currentIndex]`) | **igen** |
| `Ctrl+3` három kijelölésnél | E18 | `main`: `MainWindowLibraryActions.qml:95-100` (`sorok[0]`, kattintás-sorrend: a 4. kép); `fix/7384-claude`: `MainWindowLibraryActions.qml:96-110` (`Selection.firstInGridOrder`) | `main` **NEM**, a #7384 igen |
| Dupla kattintás | E19 | `MainLibraryCanvas.qml:387-395` (a kattintott képet nyitja) | igen (egy képre) |
| Az ini kiírásának kiváltója | E20-E22 | `edit_controller_save_mixin.py:145-169`: minden véglegesítés azonnal ír | NEM, de nem látható (B9) |
| Új réteg és új Undo-lépés minden látogatáson | E22 | `main`: `edit_controller_effects_finetune_mixin.py:179-202` (egy réteg, minden elengedés új lépés); `fix/7383-claude`: `EditorPanel.qml:272-274`, `PhotoViewerEditorPanel.qml:60`, `edit_controller_finetune_visit_mixin.py:114-164` | `main` NEM, a #7383 **igen** |
| `redo=` az ini-ben Undo után | E22 | `edit_controller_save_mixin.py:162-169` csak `filters=`-t ír; a redo-verem csak memóriában él (`edit_controller_history_mixin.py:59-84`) | nyitott (B12) |
| Betöltött lánc visszavonható megnyitáskor | E27 | `edit_controller_history_mixin.py:87-98`, `edit_controller_session_mixin.py:116-121` (`_seed_undo_from_chain`) | **igen** |
| A pipetta mintavétele területátlag | E23 | `edit_preview.py:491-508` (egyetlen képpont, a megjelenített előnézetből) | **NEM** (T4 kiegészítése) |
| Undo gomb a pipetta után | E24 | `edit_controller_effects_color_mixin.py:53-72` (azonnal frissít) | NEM, nem másoljuk (T4 kiegészítése) |
| Színminta a pipetta után | E24 + részleges B15 bináris | `EditorFinetunePanel.qml:241`: `color: panel.neutralColor === "" ? "#000000" : panel.neutralColor`; `edit_controller_effects_finetune_mixin.py:70-76` a látogatás p4-ét olvassa | **nem eldöntött (B15)** |
| Csupa nulla réteg pipetta nélkül | E26 | `main`: `edit_controller_effects_finetune_mixin.py:179-202` (az Undo-lépés megmarad, `clear_finetune` az összes finetune-réteget törli); `fix/7383-claude`: `edit_controller_finetune_visit_mixin.py:137-143, 153-155` (a réteg törlődik, a látogatás Undo-lépése marad) | **NEM** (T6) |
| Csupa nulla réteg pipetta-színnel | E25 | `fix/7383-claude`: `edit_controller_finetune_visit_mixin.py:137-143` (a semleges szín nem alapérték, a réteg marad); `main`: ugyanaz a `clear_finetune`, ami a p4-et is eldobja | #7383 **igen**, `main` NEM |
| Betöltött `fill` melletti húzás | E27 | `session_effects.py:136-151` (`set_fill` a betöltött réteget helyben cseréli), `edit_controller_effects_finetune_mixin.py:215-232` (`setFixesFill`) | **NEM** (T6) |

**Mit mondanak a három közben készült fejlesztésről.**
- **#7383 (Hangolás-látogatás):** a job-897 és a job-904 **megerősíti** (két látogatás két réteg és két Undo-lépés; pipetta-színes réteg négy nullával is megmarad). **Kiegészíti** két ponton, mindkettő a T6: a nulla nettó hatású, semleges színű látogatás visszavonási lépése az eredetiben is eltűnik (`edit_controller_finetune_visit_mixin.py:153-155` megtartja), és a T3 4. pontjának feltevését (a `fill` helyben cserélődik) **cáfolja** (E27).
- **#7384 (`Ctrl+3`):** a job-895 harmadik kijelölési sorrendje (E18) **megerősíti** a rács szerinti első nyitását; a kijelölés a nézőből visszalépve nálunk is egy képre szűkül (E17), ez nem igényel módosítást.
- **#7385 (pipetta):** a mintavétel nem képpont, hanem területátlag (E23), ezt a „T4 kiegészítése (zárókör 3)" rész rögzíti; a #7385 ága a pipettához még nem tartalmaz commitot.

#### A nyitott pontok besorolása (zárókör 3)

| # | Pont | Állapot | Indok / bizonyíték |
|---|---|---|---|
| B1 | Belépés többes kijelölésnél (`Ctrl+3`) | **LEZÁRVA, igazolt eltérés** (T5 megerősítve) | E18: harmadik kijelölési sorrend is a rács szerinti elsőt nyitja; a #7384 ága helyes. |
| B2, B3 | Undo-lépések, csúszkák állása | **LEZÁRVA, igazolt eltérés** (T3 megerősítve) | E22: két látogatás két réteg és két lépés, az Undo után alaphelyzet; a T3 3. pontja mérve. |
| B5 | Pontos nullázás, mentés | **LEZÁRVA, igazolt eltérés** (T6) | E25, E26. |
| B8 | Enter, dupla kattintás, helyi menü többes kijelölésnél | **BLOKKOLT** (javított lépéssor: B8) | E16-E19: egy sorrendben mérve egyezik; a szétválasztó sorrend, a helyi menü és a többesen belüli dupla kattintás nem mért. |
| B9 | Az ini kiírásának kiváltója | **LEZÁRVA** (nincs látható eltérés) | E20-E22; alapértelmezett döntés: nem másoljuk. |
| B10 | Pipetta: terület, Undo-gomb, színminta | **LEZÁRVA, igazolt eltérés** (T4 kiegészítése) | E23, E24; a mintaterület mérete B14-ben, a korong p4-színének útja B15-ben külön nyitott pont. |
| B11 | Betöltött `fill` melletti húzás | **LEZÁRVA, igazolt eltérés** (T6) | E27. |
| B12 | Tartós Újra-lista (`redo=`) | **BLOKKOLT** (javított lépéssor: B12) | E22: a `redo=` sor létezik; az újranyitás utáni Újra nem mért. |
| B13 | `fill`: ismételt húzás, Undo, Redo | **LEZÁRVA, egyezik** | job-948: két `fill` tag (`0.500000`, `0.859813`), a #7397 viselkedésével azonos. |
| B14 | A pipetta mintaterületének mérete | **BLOKKOLT** (javított lépéssor: B14) | E23: 2/5 a határon, 5x5 az egyetlen egyszerű jelölt, más ablak nem zárható ki. |
| B15 | A színminta színe mintavétel után | **BLOKKOLT / NINCS MEG** | A binárisban igazoltak a node konstruktorbeli mezőírói és a külön Desaturate-panel `+0x268` írója; a `CGenericFilter +0x54` slot statikusan paraméteríró jellegű, nem igazolt p4-getter. A Hangolás p4-ének útja a node mezőiig nincs meg; a Wine alatti fekete korong Windowsos felvétel nélkül nem dönt. Következő címek: a node-szín forrása `0x009c4330` → `0x009c50d7`, és a CFilterStackUI +0x08 hívó/fogyasztója (`0x00c90874` slot). |

#### T6: A #7383 kiegészítése: a csupa nulla, semleges színű látogatás ne hagyjon visszavonási lépést, és a Gyakori javítások Derítőfénye új réteget fűzzön a betöltött `fill` mellé

**Mi a hiba.** Két, a #7383 modelljéhez tartozó, látható eltérés (egy jegy, mert ugyanabból a réteg-modellből erednek):
1. **Csupa nulla látogatás** (E26). Hangolás fülön a Kiemelések kihúzva és pontosan nullára visszahúzva, pipetta nélkül: az eredetiben nyom nélkül eltűnik (kép az eredeti, az Undo és az Újra tiltott, nincs ini, nincs mit menteni). A #7383 ágán a réteg kikerül a láncból, de a látogatás Undo-lépése megmarad, tehát az Undo gomb aktív és üres lépést vesz le; a `main`-en `clear_finetune` ráadásul az összes finetune-réteget (a betöltöttet is) törli. Pipetta-színnel a réteg az eredetiben is megmarad (E25): ezt a #7383 jól kezeli.
2. **Betöltött `fill` melletti húzás** (E27). Az 1. fül Derítőfény-csúszkája az eredetiben új `fill` réteget fűz a lánc végére (a két réteg halmozódik, a kép erősebben világosodik: a szürke folt 169 -> 200); nálunk a betöltött réteg helyben cserélődik, a kép csak a 171 körüli értékig világosodik.

**Eredeti.** E25, E26, E27: job-905 12., 14., 17., 22. kocka és a fájllista (E26); job-904 15., 18., 20., 22. kocka és a `.picasaoriginals` ini (E25); job-906 14., 15., 17. kocka és az ini, valamint a job-844 10. kocka a `fill=1,0.523364` egyedüli hatásához (E27). Bináris: az Undo-feliratot és -állapotot a lánc maga adja: az `editpanel/filter_undo` (`0x00c8e9ec`) és `editpanel/filter_redo` (`0x00c8ea04`) sztringek hivatkozója a `0x00567680` és a `0x007533b0` (a `0x007533b0` a "Undo " feliratot a lánc utolsó eleméből állítja, `0x00753c46`; `session_core.py:90-110` a `CFilterStackUI` `0x006ad530` frissítőjére hivatkozva a `filters=`-t a visszavonás-veremként írja le). Az aktív szűrőt a `0x005f8520` név szerint állítja be (`fill`: `0x005d77ad`, `finetune2`: `0x005d78b2`, F5). Az az utasítás, amely a szűrő-példányt létrehozza, illetve a csupa nulla példányt eldobja, nincs azonosítva: a viselkedést a felvételek bizonyítják.

**Nálunk.** `fix/7383-claude`: `edit_controller_finetune_visit_mixin.py:137-143` (a csupa nulla és semleges szín jelölt), `:153-155` (a látogatás nyitva marad, a lánc a látogatás előtti, az Undo-bejegyzés a veremben), `:114-164` (`_commit_finetune_layer`). `main`: `edit_controller_effects_finetune_mixin.py:179-202` (`setFinetune`: `_push_undo` és `clear_finetune`), `edit/session_effects.py:136-151` (`set_fill` a `_with_single_layer`-rel, `:290`), `edit_controller_effects_finetune_mixin.py:215-232` (`setFixesFill`: `_push_undo("fill")`, `_session_with_fill`).

```python
# edit_controller_finetune_visit_mixin.py:153-155 (fix/7383-claude)
if is_noop:
    self._session = EditSession(ops=self._session.ops[: visit.base_length])
    return True          # az Undo-bejegyzés a veremben marad (E26: az eredetiben nincs)
```

```python
# session_effects.py:150-151
new_op = _new_op("fill", ("1", f"{value:.6f}"))
return self._with_single_layer(lambda op: op.matches("fill"), new_op)   # a betöltött fill helyben cserélődik (E27)
```

**Teendő.**
1. Csupa nulla látogatás: ha a látogatás rétege az elengedéskor csupa nulla és a p4 semleges (`00000000`), a réteg és a látogatás visszavonási bejegyzése is törlődik (az Undo és az Újra állapota a látogatás előttire áll vissza, az Újra-verem érintetlen; az ini a látogatás előtti láncot kapja, üres láncnál a `filters=` kulcs sem marad). A következő húzás új réteget és új lépést kezd. Pipetta-színnel a réteg megmarad.
2. Gyakori javítások Derítőfény: az 1. fülön a csúszka első húzása új `fill=1,<érték>` réteget fűz a lánc végére (`append_fill`, az `append_finetune` mintájára), egy Undo-lépéssel (felirat: Derítőfény); a betöltött `fill` réteg érintetlen, a kép a rétegek halmozott hatását mutatja. A látogatás további húzásai a mai módon az új réteget írják felül; ennek helyességét a B13 dönti el.
3. A `set_fill` és a `_with_single_layer` a többi hívónak marad.

**Nem része.** A látogatás-modell többi pontja (#7383); a pipetta (T4); a `fill` nullára húzásának viselkedése (nem mért); a színminta (B15); az ini kiírásának időzítése (B9, nem másoljuk).

**Kész, ha** (látás alapú, a felvétel kockáival párban):
1. Hangolás fül, pipetta nélkül a Kiemelések kihúzva a jobb szélre, majd a bal szélen túlra húzva: a kép egyezik az eredetivel (bézs (200,151,121)), az Undo és az Újra tiltott, a `Ctrl+S` nem kínál Save ablakot, nincs ini-változás (job-905 14., 17.).
2. Ugyanez előzetes pipettával (`ffc89779`): a kép a csak-pipettás állapot (bézs (161,161,161)), az Undo aktív, mentéskor a Save ablak felkínálódik, az ini-ben `finetune2=1,0.000000,0.000000,0.000000,ffc89779,0.000000` áll (job-904 18., 20.).
3. `fill=1,0.5` betöltve, az 1. fül csúszkája húzva: a láncban `fill=1,0.500000;fill=1,<érték>` áll, a szürke folt a csak-betöltött 169-ről 200 körülire világosodik (a `fill=1,0.523364` egyedül 171), az Undo "Visszavonás: Derítőfény" (job-906 14., 15.).
4. Betöltött `fill` mellett megnyitáskor az Undo már aktív (job-906 14.; ez ma is így van, regresszió-őr).
5. Valódi egéresemény-teszt (csúszkák, `Ctrl+S`, Undo gomb), rontás-kontroll: a teszt elbukik, ha a csupa nulla látogatás Undo-lépése visszakerül, illetve ha a `fill` helyben cserélődik.
6. Szomszéd regresszió-ellenőrzés a kiadás előtt: Gyakori javítások fül egyéb vezérlői, a Hangolás látogatás-modellje (két látogatás két réteg, E22), az Undo/Redo gombsor.

**Bizonyítottsági fok.** Erős a viselkedésre (E25-E27: mindegyiknél két független adat, a kép pixelei és az ini); a bináris oldal közvetett, a réteg-létrehozás utasítása nincs azonosítva.

#### Javított Colab-lépéssorok (zárókör 3)

A lépéssorok a `.tmp/javitott-lepesek3/7345-<pont>.json` fájlokban vannak (`indulas: alapallapot`, legfeljebb 40 lépés); a koordináták a J0 utáni értékek (csúszkák y 160/213/266/320, Visszavonás (70,412), Újra (207,412) a Hangolás fülön; az 1. fülön a Derítőfény-csúszka y=345, Visszavonás (70,380), Újra (207,380); pipetta (148,374); fülek: 1. (28,94), Hangolás (83,94); a bézs folt (682,588), a kék folt (882,588)).

| Pont | Fájl | Mit dönt el | Lényeg (lépésszám) | Döntő kockák és értelmezés |
|---|---|---|---|---|
| B8 | 7345-B8 | melyik kép nyílik két kijelölésnél Enterrel, helyi menüvel és dupla kattintással | Lefutott: job-935 | 11. (Enter), 17. és 21. (jobb gomb a gradienten, majd View and Edit), 27. és 31. (jobb gomb a color_patches-en), 37. (dupla kattintás a gradienten). Enter és helyi menü: rács szerinti első; dupla kattintás: kattintott tag. Lásd T7. |
| B12 | 7345-B12 | megmarad-e az Újra kilépés és újranyitás után | Lefutott: job-932 | 20. (Undo után az Újra aktív), 25. (újranyitás után tiltott), 26. (kattintás után változatlan), ini. Újra csak a nyitott munkamenetben él, a PicasaPy memória-alapú veremével egyezik. |
| B13 | 7345-B13 | a második Gyakori javítások húzás külön `fill` réteget ír-e a betöltött `fill=1,0.5` mellé | job-933 után célzott ismétlés szükséges | job-933: 16. kocka első húzás után, 18. kocka második húzás után, 20., 22., 24. Undo/Undo/Redo után; a képpontértékek 169, 200, 222, 169, 128, 169. A két húzás egy Undo-lépés, de köztes ini nincs, ezért a 2. húzás rétegszáma nem bizonyított. Az új lépéssor a második húzás után azonnal kilép, hogy az ini ezt eldöntse. |
| B14 | 7345-B14 | a pipetta mintaterületének mérete | Lefutott: job-934 | A széli minták és az ini utolsó p4 értéke 5x5-ös, középre igazított négyzetet igazol; részletek a B14 frissítésében és a job-934 eredményében. |

**B15 blokkolt, javított lépéssor nélkül:** a `0x00752020` a `CFilterStackUI` mezőláncából kapott aktív objektum `+0x54` virtuális slotját hívja; a filterleíró/RTTI és a hívási konvenció alapján a `CGenericFilter` `0x008fbee0` statikus célja illeszkedik, az alapág paramétert ír és nullát ad vissza, tehát nem igazolt p4-getter. A `0x00a66ea0` a `ytColorCircleNode` színállapotát rajzolja; a konstruktor és a Desaturate-panel mezőírói megvannak, de a Hangolás p4 értékének ezekhez jutása nincs meg. Következő irány: a színargumentum `0x009c4330`→`0x009c50d7` forrásának és a `CFilterStackUI +0x08` hívó/fogyasztójának (`0x00c90874` slot) követése; ha binárisból nem oldható fel, Windowsos mintavétel utáni felvétel kell. A renderelő út nem használ GDI/GDI+-t, így a fekete Wine-kép erre nem ad magyarázatot.
**B7 változatlan:** a végrehajtói hiány (megbízható írásvédelem, közbenső fájllista) nem kapott új adatot.

### Job-932..935 eredménye

**Módszer.** A `kepernyo__NN.png` az NN. lépés előtti állapot. A következtetések a döntő képkockákból, a futás végén mentett `picasa.ini`-ből és a képpontmérésekből származnak. Köztes INI-t nem feltételezek ott, ahol a felvétel nem mentett ilyet.

| Felvétel | Döntés és bizalom | Döntő bizonyíték |
|---|---|---|
| job-932, B12: két Hangolás-látogatás, Undo, kilépés és újranyitás | **LEZÁRVA, erős.** Az Újra a munkamenet bezárásáig él, újranyitás után nem. | A 20. kockán az Undo utáni Újra aktív; a 25. kockán újranyitás után tiltott; a 26. kockán a kattintás nem változtat az állapoton. A futás végi INI egyetlen `finetune2` réteget tartalmaz, `highlights=0.238596` értékkel. Ez megegyezik a PicasaPy memóriabeli redo-vermével (`edit_controller_history_mixin.py:77-105`, `edit_controller_save_mixin.py:162-168`). |
| job-933, B13: két Gyakori javítások Derítőfény-húzás, Undo, Undo, Redo | **Részben lezárva, közepes.** A két húzás egyetlen látogatásként egy Undo-lépésbe kerül; az új rétegek pontos száma a második húzás után nyitott. | A szürke folt mért csatornaértéke a 14., 16., 18., 20., 22. és 24. kockán rendre 169, 200, 222, 169, 128, 169. Az első Undo a betöltött `fill=1,0.5` állapotára állít vissza; a második eltávolítja azt; a Redo visszaállítja az első állapotot. A futás végi INI az Undo/Redo után készült, így csak a kiinduló `fill=1,0.500000;` látszik benne. Köztes INI híján a második húzás rétegszáma nem dönthető el.
| job-934, B14: pipetta mintaméret; #7385 forrásmintája | **LEZÁRVA, erős.** Az eredeti 5x5 forrásképpontot átlagol; ez egyezik a mai PicasaPy megvalósítással. | A hat minta a (781,588), (780,588), (779,588), (783,588), (784,588) széli pontokon és a (682,688) bézs/lila határon történt. A határ mintavétele utáni kimeneti foltok pixelszórása 5x5-tel egyezik, a 3x3 és 7x7 modellel nem. A végső ini p4-e `ff976084`, vagyis RGB (151,96,132), pontosan a forráskép (682,688) körüli 5x5 egyszerű csatornaátlagának kerekítése. A már módosított előnézet ugyanott (191.8,93.4,76.2), ezért a p4 a forrásból jött. A mai PicasaPy `MINTA_FORRAS_KEPPONT = 5` és `teruletatlag()` implementációja (`edit_preview_sample.py:39-44,61-64,98-104`) egyezik.
| job-935, B8: két kijelölt kép, Enter, helyi menü, dupla kattintás | **JEGYTÖRZZEL ÁTADVA, erős.** Enter és a helyi View and Edit a rács első képét nyitja; a dupla kattintás a megkattintott tagot. | A 9. kockán két kép kijelölt. A 11. kockán Enter után a rács szerinti első `color_patches.jpg` nyílik, noha a `gradient` volt az utoljára kijelölt. A 17. és 21. kockán a `gradient` helyi menüjének View and Edit parancsa szintén `color_patches.jpg`-t nyit. A 27. és 31. kocka a másik kijelölt tag helyi menüjét mutatja. A 37. kockán a `gradient` dupla kattintása a `rgb_gradient.jpg`-t nyitja. |

#### A kiadott jegyek összevetése

| Jegy | Eredmény a felvételekhez képest |
|---|---|
| #7383 | Nem cáfolja. A job-932 két látogatása és egy Undo-ja, valamint a korábban mért job-904 pipettaszíne egyezik a látogatási réteg viselkedésével. A nulla nettó hatású látogatás Undo-állapotát ez a felvétel nem vizsgálta. |
| #7384 | Nem cáfolja. A job-935 nem tesztelte a Ctrl+3-at; a job-895 E18 továbbra is megerősíti a rács szerinti első kép nyitását. A job-935 új eltérése az Enter és a helyi menü útja. |
| #7385 | Nem cáfolja. A job-934 forrásból származó mintaszíne és a 5x5 méret egyezik a jelenlegi mintavételi kóddal. |
| #7397 | A betöltött `fill` melletti első húzás új, halmozódó hatását támogatja. A második húzás ugyanazon látogatáson belüli rétegszáma köztes INI nélkül nem dönthető el, ezért sem nem cáfolja, sem teljesen nem igazolja ezt a részét. |
| #7400 | Nem cáfolja. A job-934 az eredeti semlegesített előnézetet rögzíti, de nem tartalmaz azonos képről származó PicasaPy-render összevetést; a semlegesítés képletének paritását ez a felvétel nem dönti el. |

#### T7: Többes kijelölésnél az Enter és a helyi View and Edit a rács első képét nyissa

**Mi az eltérés.** Két kijelölt képnél az eredeti Picasa az Enter és a helyi menü View and Edit parancsára a rács szerinti első képet nyitja meg. A job-935-ben a `color_patches` volt a rács első eleme, a `gradient` az utoljára kijelölt: mindkét eredeti parancs a `color_patches` képet nyitotta meg. A dupla kattintás célzott marad, és a `gradient` képet nyitotta.

**Eredeti:** `0x007344b0` (a `0x00caed5c` című `View and Edit` sztring `string_xrefs` hivatkozója); job-935, 11., 17., 21. és 37. kocka.

**Nálunk.** Az Enter az utoljára kattintott horgonyt használja (`LightboxFeed.qml:407-409`):

```qml
if (appWindow.selectedIndex >= 0) {
    openRequested(appWindow.selectedIndex)
    ev.accepted = true
}
```

A Ctrl-kattintás ezt a horgonyt az utoljára kattintott sorra állítja (`MainLibrarySelectionState.qml:277-280`):

```qml
hostWindow.selectedIndexes =
    Selection.toggled(hostWindow.selectedIndexes, i)
hostWindow.selectedIndex = i
```

A helyi menü célja közvetlenül a jobb kattintott sor (`MainLibrarySelectionState.qml:228-229`, `MainPhotoContextMenu.qml:111-113`):

```qml
hostWindow.fileOpTargetRow = index
hostPhotoContextMenu.popup(item, x, y)
```

```qml
onOpenRequested: {
    hostWindow.openPhotoViewer(hostWindow.fileOpTargetRow)
}
```

Ezért a mostani Enter a `gradient` utoljára kijelölt elemre nyit, a `gradient` helyi menüje pedig a jobb kattintott `gradient` képre. A dupla kattintás már a kattintott indexet adja át (`MainLibraryCanvas.qml:390-392`):

```qml
onOpened: function(i) {
    hostWindow.openPhotoViewer(i)
}
```

**Teendő.** Többes kijelölésnél az Enter és a helyi menü alapértelmezett View and Edit parancsa a rács szerinti első kijelölt képet nyissa meg. A dupla kattintás maradjon a megkattintott képhez kötve. A #7384 Ctrl+3 viselkedése külön út, ezt a jegy ne változtassa.

**Kész, ha.** A `color_patches` majd a `gradient` kijelölése után az Enter a `color_patches` képet nyitja; a `gradient` helyi menüjének View and Edit parancsa ugyanezt nyitja; a `gradient` dupla kattintása továbbra is a `gradient` képet nyitja.

**Bizonyítottsági fok.** Erős, mert a 935-ös felvétel külön rögzíti a kijelölést, mindkét parancs megnyitott képét és a dupla kattintás ellenpróbáját. A PicasaPy kódrészletei közvetlenül idézettek.

### Független újralevezetés (#140)

Nem készült. A T1 foka a zárókör 2 óta "megerősített" (a bináris és a J2a ini-je két független út), ezért a külön újralevezetés nem feltétel; ha mégis készül, a független kérdés: melyik szűrőt aktiválja a szerkesztő 1. és 2. füle (`0x005d7780`, `0x005d77d0`), és melyik szűrő paraméterét állítja a `flightslider1/scaleslider` csúszka (`0x005de8e0`).

### Nyitott kérdések mérlege

Nyitott kérdések: 0 nyílt · 24 lezárva (ebből 10 igazolt, látható eltérés) · 1 jegytörzzsel átadva (#7412) · 2 blokkolt · 0 hatókörön kívül (összesen 27 tétel).

- **Lezárva (24):** Z1-Z12 és B1, B2, B3, B4, B5, B6, B9, B10, B11, B12, B13, B14 (B13: job-948, egyezik a #7397-tel). Kilenc igazolt eltérés zárult le: Z11 (T1, kint: #7369), Z12 (T2, kint: #7370), B1 (T5), B2 és B3 (T3), B4 (T4), B5 (T6), B10 (T4 kiegészítése), B11 (T6). A tizedik igazolt eltérés T7, B8 alatt jegytörzzsel átadva.
- **Jegytörzzsel átadva (1):** B8, T7 több kijelölt képnél Enter és helyi View and Edit eltérése: #7412.
- **Blokkolt (2):** B7 (végrehajtói hiány: megbízható írásvédelem és közbenső fájllista), B15 (a p4 és a színkör node mezői közti értékátadás bizonyítatlan; a `+0x54` filter-slot nem igazolt getter; lásd a következő címeket). B12 és B14 feloldódott a job-932 és job-934 méréssel.
- **Hatókörön kívül (0):** nincs olyan pont, amelyről tulajdonosi döntés született volna. Alapértelmezett döntések, amelyeket a tulajdonos felülbírálhat: az ini azonnali kiírása marad (B9), a pipetta utáni késő Undo-gomb nem utánzott (B10).
- **Címke-javaslat a jegyre:** a #7345 kutatási mérlege elkészült a job-932..935 eredményeivel és a B15 részleges bináris vizsgálatával. Két pont maradt blokkolt (B7: végrehajtói hiány; B15: a p4 és a színkör node mezői közti értékátadás bizonyítéka hiányzik); B8 T7 fejlesztői jegytörzzsel átadva (#7412). B13-at a job-948 lezárta. A meglévő T1-T6 jegytörzsek, a #7383, #7384, #7385, #7397 és #7400 összevetése, valamint a mérleg alapján a kutatási jegy lezárható; a GitHubon nem végeztem műveletet.
- **Átvezetés a #7327-re:** változatlan (lásd a zárókör 2 mérlegét): az 1. fül Derítőfénye `fill=1,<érték>`, a csúszka nyitáskor alaphelyzetben áll, és új (nem helyben cserélt) réteget ír a betöltött mellé (E27).

**Módosított fájlok:** `docs/specs/paritas-folyamat-7345.md` (ez a lap), `changelog.d/7345.md`.
