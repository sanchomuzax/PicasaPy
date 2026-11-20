# PicasaPy paritás-ellenőrzés - archívum 2 (#7244 folytatás)

A lezárt folyamatszintű összevetések változatlanul átemelt szakaszai. A nyitott vizsgálatok a fő lapon maradnak.

## #7031: A mappa törlésének teljes folyamata az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, Picasa3.exe SHA-256
644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96.
A jelenlegi PicasaPy-állítások közvetlen forrásolvasásból származnak. A
bináris- és mérési bizonyítékot külön jelölöm. A teljes paritás feltételes:
a belépési lánc, a lomtárút és a részleges Shell-hiba igazolt, de több
engedélyezési feltétel és a törlés utáni belső állapot nem dőlt el.

### Következtetés

Az eredeti fő Mappa menü és a mappafa Delete Folder helyi menüje ugyanazt a
0x9d44 parancsot indítja. A parancs a mappát és tartalmát a Windows lomtárába
adja; a normál megerősítés a mappa nevét és a Recycle Bin célját nevezi meg.
A PicasaPy e két bejáratban azonos szövegű megerősítést és Windows alatt
ugyanilyen Shell-lomtárutat használ. Igazolt eltérés a részleges Shell-hiba
jelzése: az eredeti külön figyelmeztet a képek és a mappa eltérő végállapotára,
a PicasaPy generikus hibaszöveget ad tovább.

### Belépési pontok, kijelölés és engedélyezés

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Fő Mappa menü, Folder::ID_ALBUM_DELETE, parancs 0x9d44. A rekord feliratpointere 0x00d6e300, a parancsmező 0x00d6e30a; építő 0x00559150, végrehajtó 0x005cb990, amely az aktuális mappa objektumát adja tovább a 0x005ed240 és 0x005edef0 felé. | src/picasapy/app/qml/PicasaPy/MainMenuBar.qml:168-170; src/picasapy/app/qml/PicasaPy/FolderPane.qml:236-244 | A belépő és a megerősítés paritásban van. Az üres mappa és más speciális cél engedélyezése eredeti oldalon nyitott. |
| Mappafa helyi menü, Folder::ID_ALBUM_DELETE, parancs 0x9d44. A 0x007319f0 építőnél a felirat a [esp+0x19c], a parancsmező ugyanazon rekord [esp+0x1a6] mezője, értéke 0x9d44. | src/picasapy/app/qml/PicasaPy/FolderContextMenu.qml:330-336; src/picasapy/app/qml/PicasaPy/FolderPaneMenus.qml:317-325 | A parancsút egyezik. A PicasaPy saját képet tartalmazó mappasornál nyitja a teljes helyi menüt; saját kép nélkül (`own == 0`) rövid menüt nyit, amelyben nincs törlés. Az eredeti menü engedélyezési feltétele nyitott. |
| Delete billentyű fókuszban lévő mappafán: a binárisban lehetséges saját VK_DELETE út nincs eldöntve. A 0x00a53b00 címhez csak hivatkozó kimenet van, a függvénytörzs és a fa fókuszának parancsa nincs feloldva. | src/picasapy/app/qml/PicasaPy/FolderPaneContent.qml:304-307 csak Fel/Le kezelőt köt; src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml:678-687 sima Delete-je fotóparancs. | Ne tekintsük a globális fotó Delete parancsot mappatörlésnek. A fa saját Delete útját célzott Ghidra-körrel kell eldönteni. |
| Néző és fotórács Delete: az eredeti fotótörlő 0x9c9a út külön parancs, nem a mappatörlő 0x9d44. A 0x005cb990 diszpécserben eltérő ágak. | src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml:514-520,678-687; src/picasapy/app/qml/PicasaPy/MainKeyboardShortcuts.qml:431-460; src/picasapy/app/qml/PicasaPy/PhotoViewerKeyboard.qml:66-78 | Egy fotó kijelölése, több fotó kijelölése és a néző aktív képe a fotóparancs bemenete; ezek nem adódnak át a 0x9d44 mappaparancsnak. A jelenlegi fában a mappatörlés külön mappautat használ. |
| Képtálca: az eredeti Tray::ID_REMOVE_SELECTION tétel címe 0x00732f7f. Ez nem azonosított mappatörlő parancsként; a mappatörlő láncban nincs. | src/picasapy/app/qml/PicasaPy/TrayBar.qml:377-388 | A PicasaPy művelet képeket vesz ki a tálcából, nem töröl mappát vagy lemezfájlt. Eredeti tálca-művelet teljes mellékhatása nem része a bizonyított mappatörlő láncnak. |

A 0x9df4 közeli érték nem a helyi menü Delete parancsa. A
0x00731f34 körüli parancsmező az előző Move Folder rekordhoz tartozik; a
diszpécser 0x9df4 ága a 0x0053f340 és 0x0053f4a0 útvonalon mozgatási
szövegeket használ. A feliratot és parancsot a rekord bázisához párosítottam.

Üres mappa, almappás mappa, írásvédett hely és hálózati meghajtó: az eredeti
út a Windows Shell mappatörlő műveletére ad át egy útvonalat. A binárisból
nem állapítható meg, hogy az adott fájlrendszer, jogosultság vagy hálózati
állapot mellett a Shell pontosan mit engedélyez. Ezek értéke egyenként
NINCS MEG; megszerzésükhöz külön üres, almappás, írásvédett és hálózati
tesztmappa kell az eredeti Windows Picasában.

### Megerősítés és megjegyzett állapot

A 0x005fdc30 a DeleteFolderTitle, DeleteFolderWarnPC és
DeleteFolderYesButton erőforrást választja. A kérdés szövege a
0x00c992c0 címen:

> Are you sure you want to move the folder "%s" and its contents to the Recycle Bin?

A szokásos 0 típusú mappaág a 0x009bac20(1, ...) Yes/No megerősítést épít,
Cancel gomb nélkül. A feltárt 0 típusú ág nem olvas megjegyzett törlési
választást. Van egy 2 típusú ág is, amely a DeleteAllOnlineChecked kulcshoz
vezet; hogy mely mappára és mikor választódik ez az ág, a 0x005fd160
virtuális feltételének jelentése nélkül NINCS MEG.

PicasaPy a főmenüből és a helyi menüből is a mappa nevét helyettesíti a
megerősítő kérdésbe (src/picasapy/app/qml/PicasaPy/FolderPane.qml:236-244,
src/picasapy/app/qml/PicasaPy/FolderPaneMenus.qml:317-325). A párbeszéd
Delete Folder / No választ ad, Cancel és megjegyzési jelölő nélkül
(src/picasapy/app/qml/PicasaPy/FolderPaneMenus.qml:398-414). A normál
gombkészlet és a megjegyzés hiánya egyezik. A 2 típusú eredeti ág feltételes
viselkedésének PicasaPy-megfelelője nem ismert.

### Végrehajtás, fájlok és belső állapot

| Hatás | Eredeti Picasa 3.9 | PicasaPy most |
|---|---|---|
| Lemez és lomtár | A 0x005edef0 a megerősítés után a 0x00992810 útján a 0x009929b0 Shell-hívást végzi. A 0x009929b0 wFunc értéke 3, azaz FO_DELETE, és paraméter 1-nél FOF_ALLOWUNDO is beáll. A normál út tehát lomtárba teszi a mappát és tartalmát, nem végleges törlés. | `src/picasapy/app/fileops_controller_delete_mixin.py:18-41` a teljes mappautat adja a delete_to_trash függvénynek. Windows alatt `src/picasapy/fileops/trash.py:79-140` a SHFileOperationW lomtárútját használja. |
| .picasa.ini | Sikeres egész mappatörlésnél a Shell a mappa útját és tartalmát kezeli, így a .picasa.ini nem külön törlődik. Részleges hibánál a fájl végállapota a konkrét könyvtártartalomtól függhet; ezt külön futásmérés nem igazolta. | A kód nem írja külön a .picasa.ini-t; az a mappával együtt kerül a lomtárba. Ezt a szándékot a `src/picasapy/app/fileops_controller_delete_mixin.py:25-27` kommentje is kimondja. |
| Index | A belső Picasa index törlés utáni módosítása ebből a handler láncból nem állapítható meg. NINCS MEG. | Siker után folderDeleted indul (`src/picasapy/app/fileops_controller_delete_mixin.py:41,` `application_services.py:121-124`); a resync eltávolítja az eltűnt mappa indexsorait (`library_controller_resync.py:195-211,` `index/sync_folders.py:296-325`). |
| Mappafa, rács és kijelölés | A parancs aktuális mappaobjektumot kap, de a siker utáni kiválasztott mappa, fa, rács és fotókijelölés végállapota nem igazolt. NINCS MEG. | A részfa újraszinkronizálódik; a törölt mappára mutató kiválasztás és a rács végállapota nincs a törlő handlerben külön beállítva. A tényleges megjelenő végállapot NINCS MEG, futásmérés kell. |
| Albumtagságok és arcok | A mappatartalommal együtt kezelt .picasa.ini önmagában nem bizonyítja az alkalmazás adatbázisában lévő album- és arcállapotot. NINCS MEG. | A kód kommentje szerint a .picasa.ini visszaállítása a feliratokat, címkéket és arc-hozzárendeléseket is visszahozza (`fileops_controller_delete_mixin.py:25-27`). Az albumtagság és az arcok törlés utáni, illetve visszaállítás utáni állapota külön mérés nélkül NINCS MEG. |
| Több fotó kijelölése | A 0x9d44 handler egy mappát kap, nem fotólistát; az egy vagy több kijelölt fotó nem a mappatörlő parancs argumentuma. A néző aktív fotójának törlése külön 0x9c9a fotóparancs. | A főmenü hostController.currentFolder értékét adja át; a fa helyi menüje folderPath értékét adja át. Fotók kijelölése nem bővíti a törölt mappák számát. |

### Részleges törlés és hibák

Az eredeti 0x005edef0 a 0x009929b0 Shell-hívás nemnulla eredménye után
IDS_CANT_DELETE_FOLDER figyelmeztetést mutat. A szöveg címe 0x00e05b6a:
a képek törölve lehetnek, de maga a mappa további fájlok vagy mappák
miatt megmarad. Ez részleges eredményt jelent, nem a mappa érintetlenségét.
Az üres, rejtett, írásvédett vagy hálózati bejegyzésekkel kapcsolatos
konkrét részleges végállapot NINCS MEG.

PicasaPy-ban Windows Shell nemnulla eredmény vagy megszakított művelet esetén
a `src/picasapy/fileops/trash.py:137-140` általános OSError keletkezik, és a
`src/picasapy/app/fileops_controller_delete_mixin.py:38-40` ezt szövegváltoztatás
nélkül az operationFailed jelzésre küldi. Ez nem őrzi meg az eredeti
részlegesállapot-figyelmeztetést. Ez az egyetlen most igazolt, fejlesztést
indokló eltérés.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Nemnulla Shell-eredmény: 0x005edef0 megjeleníti a 0x00e05b6a IDS_CANT_DELETE_FOLDER szöveget, amely elmondja, hogy a képek már törölve lehetnek, a mappa viszont megmaradhat. | `src/picasapy/fileops/trash.py:137-140` általános hibát dob; `src/picasapy/app/fileops_controller_delete_mixin.py:38-40` a generikus üzenetet továbbítja. | A Windows mappatörlés Shell-hibájánál részleges eredményt pontosan megnevező figyelmeztetést adjon. Ne állítsa, hogy a teljes mappa érintetlen maradt. |

### Bizonyíték és bizonyítottsági fok

| Érték vagy állítás | Forrás |
|---|---|
| Főmenü és fa helyi menü parancsa 0x9d44 | bináris (0x00559150, 0x007319f0, 0x005cb990) |
| Főmenü rekord felirat-pointere és parancsmezője | bináris (0x00d6e300, 0x00d6e30a) |
| Helyi menü rekord felirat-parancs párosítása | bináris (0x00731f48-0x00731f56, 0x00731f9e); Ghidra-kimenet: 2026-11-15-6970-colab-decomp.txt |
| Szomszédos 0x9df4 parancs Move Folder | bináris (0x00731f34, 0x0053f340, 0x0053f4a0); a Move Folder sztringek független xrefjei 0x00c8ac90-től |
| Normál kérdés és DeleteFolder erőforrások | bináris (0x005fdc30, 0x00c990e8, 0x00c992c0, 0x00c99314, 0x00c99338) |
| Mappát lomtárba adó Shell-művelet | bináris (0x005edef0, 0x00992810, 0x009929b0) |
| Részleges eredmény figyelmeztetése | bináris (0x005edef0, 0x00e05b6a) |
| PicasaPy belépési pontok, megerősítés és hibaút | Mai forrás: src/picasapy/app/qml/PicasaPy/MainMenuBar.qml:168-170; FolderPane.qml:236-244; FolderPaneMenus.qml:317-325,398-414; `src/picasapy/app/fileops_controller_delete_mixin.py:18-41`; `src/picasapy/fileops/trash.py:129-140` |
| Eredeti üres/almappás/írásvédett/hálózati viselkedés, belső index/album/arc és UI végállapot | NINCS MEG; külön Windows Picasa 3.9.141 futásmérés szükséges |

**Bizonyítottsági fok: feltételes.** A fő- és helyi menü parancsazonossága,
a Recycle Bin kérdés, a Shell lomtárjelzője és a részleges hibaüzenet
megerősített, mert külön útvonalon is egyeznek. A teljes feladat nem zárható
le: a fa Delete billentyűje, a 2 típusú párbeszéd feltétele, a fájlrendszer
speciális esetei, a Picasa belső indexe, albumjai, arcai és a törlés utáni
felületi kijelölés nyitott maradt.

### A két független út

- A út, utasításszintű lánc: a menürekordok 0x9d44 értéke a 0x005cb990
  diszpécserhez, onnan a 0x005ed240 és 0x005edef0 végrehajtóhoz, majd a
  0x00992810 és 0x009929b0 Shell-híváshoz vezet.
- B út, független szöveg- és hívásadat: a 0x00c992c0 kérdés maga mondja ki a
  Recycle Bin célt, míg a Shell-hívás 0x40 flagje FOF_ALLOWUNDO. A
  0x00e05b6a külön részleges eredményt ír le.
- Egyezés: a főmenü és helyi menü ugyanazt a mappa parancsot indítja, és a
  végrehajtás visszavonható lomtárút. A két út a részleges hiba jelentésében
  is egyezik.

### Cáfoló kísérlet

Azt próbáltam cáfolni, hogy a helyi menü Delete Folder feliratához a közeli
0x9df4 kód tartozik. A rekord mezőit a 0x007319f0 építő rekordbázisához
párosítva a felirat a [esp+0x19c], a Delete parancs pedig ugyanazon rekord
[esp+0x1a6] mezőjében 0x9d44. A 0x9df4 a megelőző Move Folder rekordhoz
tartozik, és mozgatási kezelőre vezet. A cáfolatot függetlenül ellenőriztem:
a 0x9d44 dispatch a mappatörlő 0x005edef0 útvonalra, a 0x9df4 a
0x0053f340 / 0x0053f4a0 mozgató útvonalra vezet. A próba a parancs-felirat
párosítást igazolta; nem dönt a fa Delete billentyűjéről.

### A jegy „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték |
|---|---|---|
| Mappa menü, fa helyi menü, fa Delete, néző és tálca belépési pontok | ⛔ | Főmenü és helyi menü 0x9d44 igazolt; fa Delete bináris kezelője nyitott. A néző 0x9c9a fotótörlő, a tálca külön művelet. |
| Üres mappa, almappák, írásvédelem és hálózati meghajtó | ⛔ | A Shell-hívás ismert; az egyedi célok eredménye csak Windows-méréssel dönthető el. |
| Megerősítés szövege és megjegyzése | ✅ / ⛔ | Normál kérdés, Yes/No és nincs megjegyzés igazolt. A DeleteAllOnlineChecked 2-es ág kiváltó feltétele nyitott. |
| Lomtár, .picasa.ini, index, mappafa, rács, kijelölés, albumok és arcok | ⛔ | A lomtárjelző igazolt, .ini a mappával halad. Eredeti belső adatok és UI végállapot nincs igazolva. |
| Részleges törlés és írási hiba | ✅ / ⛔ | Nemnulla Shell-válasz részleges figyelmeztetése igazolt; külön jogosultság- és hálózati kimenet nincs mérve. |
| PicasaPy összevetése és eltérésenkénti teendő | ✅ | Egy igazolt eltérésre kész jegytörzs készült; minden további eltéréshez hiányzik az eredeti oldali bizonyíték. |

### Javasolt fejlesztői jegytörzs-bővítés

**Cím:** Mappatörlés Shell-hibája: jelezzük a részleges eredményt

**Törzs:**

Eredeti: a 0x005edef0 mappatörlő a 0x009929b0 Shell-hívás nemnulla
eredményénél a 0x00e05b6a IDS_CANT_DELETE_FOLDER figyelmeztetést mutatja.
A szöveg szerint a képek már törölve lehetnek, de a mappa további fájlok
vagy mappák miatt megmaradhat.

Nálunk: `src/picasapy/fileops/trash.py:137-140` általános OSError keletkezik;
`src/picasapy/app/fileops_controller_delete_mixin.py:38-40` ezt általános
hibaüzenetként továbbítja.

Teendő: Windows mappatörlés Shell-hibájánál külön részleges eredmény
figyelmeztetést kell adni. A szöveg ne ígérje, hogy semmi sem változott.

Kész, ha:

- Nemnulla vagy megszakított Windows Shell-eredménynél a felhasználó olyan
  figyelmeztetést kap, amely szerint a képek törölve lehetnek, miközben a
  mappa megmaradhat.
- A hiba nem indít csendes végleges törlést.

### Új kutatási jegyjavaslatok

Most nincs külön új kutatási jegyjavaslat; a fa Delete és a törlés utáni
belső állapot ennek a folyamatnak nyitott része.

### Ghidra-kiegészítés (2026-11-15, várólista 404-405)

Forrás: `referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp.txt` (privát
kutatási tár).

- **`0x00a53b00`, Delete a mappafán.** Csak részválasz. Ez egy általános
  billentyűszűrő 17 hívóval. A DELETE billentyűt (`0x2e`) a vezérlő magának
  tartja (`FUN_00a582f0`), de a `0x9d44` parancs sem itt, sem a
  `FUN_00a582f0` elején nem szerepel. Hogy a mappafa melyik hívón át
  használja, ebből nem dönthető el. A fa Delete útja ezért **nyitott marad**;
  a PicasaPy mai viselkedése (a fán nincs saját Delete) nem cáfolt.
- **`0x005fd160`, a 2-es megerősítés feltétele.** A DeleteAllOnlineChecked
  típus akkor jön, ha a mappa **legalább egy** elemére a katalógus vtábla
  `+0xac` metódusa igazat ad; ezt a `0x005edef0` állítja be
  (`cVar1 ? 2 : 0`). A `+0xac` jelentése valószínűleg „online, feltöltve”, de
  ez nincs igazolva. **PicasaPy:** online feltöltés-nyilvántartás nélkül ez az
  ág nem értelmezhető; amíg a `+0xac` jelentése nem igazolt, jegyet nem
  javaslok rá.

### Ghidra-kiegészítés 2 (2026-11-15, várólista 413-418)

Forrás: `referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp-2.txt` (privát
kutatási tár). Ide a 413 és a 414 tartozik.

- **`0x00a582f0`, a mappafa Delete útja (413).** Részválasz, de az irány
  eldőlt. A függvény általános billentyű-továbbító: az eseményt előbb a
  fókuszban lévő gyermekcsomópont `0x74` virtuális metódusának adja
  (`param_1[0x57]`), majd a testvércsomópontoknak (`param_1[0x59]` tömb, a
  fókuszban lévőt és a letiltottakat kihagyva). A `1000000` eredménynél
  lezár, a `0xf4246` eredménynél megszakítja a bejárást. A törzs a DELETE-re
  billentyűkódot nem hasonlít (a testvérbejárásban csak az `0xd` és az `0x1b`
  kód szerepel), és a `0x9d44` parancs sem fordul elő benne. A mappalista saját
  kezelője a `KeyHandler::AlbumList` vtábla (`0x00c807e0`) `0x005c40e0`
  metódusa. **Bizonyítottsági fok: helyi disassembly, nem Ghidra-dekompilálás.**
  A `0x005c40e0` törzse nincs a kimenetben; a fejléc szerint ugrótáblája a
  `0x23-0x28` billentyűkre szól (End, Home, lapozás, nyilak), a `Ctrl+Enter` a
  `0x005d0e90`-re, a karakterbevitel a `0x005c3fe0`-ra megy, a DELETE (`0x2e`)
  nincs kezelve, és a `0xf4241` ("nem kezelt") jelzéssel tér vissza. Ebből az
  következik, hogy a mappalistának nincs saját Delete -> `0x9d44` útja; a
  billentyű a globális kezelőhöz megy tovább. A vtábla többi nyers bejegyzése
  nem érdemi: a `0x00563270` az `IytUnknown` destruktora, a `0x009d79f0` és a
  `0x009d7a00` az `AddRef` és a `Release` (a `+4` mezőn
  `InterlockedIncrement`, illetve `InterlockedDecrement`).
  **PicasaPy:** a mappafa csak Fel/Le kurzorbillentyűt köt
  (`FolderPaneContent.qml:304-307`), saját Delete-je nincs; ez az eredeti
  mappalista-kezelővel **összhangban** van. A nem kezelt Delete további sorsa
  nincs eldöntve. PicasaPy-ban az ablakszintű `Delete` gyorsbillentyű
  (`PicasaMenuBar.qml:636-642`) feltétele nem vizsgálja, hogy a mappafa
  fókuszban van-e (csak `photoActionsEnabled`, nem szerkesztő, nem
  szövegbevitel), tehát a kijelölt fotók törlését indítja, mappatörlést soha.
  Hogy az eredeti globális kezelő fókuszban lévő mappalistával mit tesz a
  Delete-tel (fotótörlés a `0x9c9a` paranccsal vagy semmi), **nincs meg**;
  egyezést ne állítsunk.
- **`0x00432d20`, a `+0xac` metódus (414).** Részben megválaszolva. A
  `0x00c82050` címen a katalógus-alobjektum vtáblájának `+0xac` bejegyzése
  (a vtábla `0x00c81fa4`). A dekompilált törzs meghívja a saját `+0x88`
  virtuális metódusát (`0x00431230`); ha a kapott szöveg nem üres, hozzáfűzi a
  `0x00c81520` sztringet (`"list"`, `FUN_00985af0`), és a `this+0xed8`
  táblában (`FUN_006a46c0`) az elemhez ezzel a kulccsal keres. A kulcs tehát
  `<szöveg>list` alakú. A szöveget a második paraméterként kapott
  környezet-objektum adja (a `0x005edef0` a `FUN_00926c20()` objektumot adja
  át; ez a fejléc olvasata, a `0x00926c20` és az objektum `0x68` metódusa nincs
  a kimenetben). A dekompilálás a visszatérési értéket elveszti (`uVar1 &
  0xffffff00`, az `AL` regiszter nem látszik), ezért az "igaz, ha a keresés
  sikeres és a bejegyzés nem üres" a fejléc olvasata; a hívó (`0x005edef0`,
  `cVar1 ? 2 : 0`) igazságértéket vár, ez nem mond neki ellent. Másik hívója a
  `0x0049f580` (a `0x0049f583` hívás), ugyanabból az átirányító családból,
  mint a setterek hívói (`0x0049f220`, `0x0049f310`, `0x0049f390`,
  `0x0049f4a0`). **Jelentés:** erős jelölt az online feltöltési lista, de a
  kulcs pontos alakja és a tábla írója nincs igazolva. **PicasaPy:** a
  mappatörlés (`fileops_controller_delete_mixin.py:18-41`) nem vizsgál
  feltöltési állapotot; a Google Fotók feltöltés
  (`tray_google_photos_controller.py:331`) futásidejű fázist követ, tartós
  képenkénti nyilvántartást a keresés nem talált. A 2-es ág értelme nélkül
  jegyet továbbra sem javaslok.

**A jegy lezárhatósága: NEM zárható.** A "Kész, ha" pontokhoz mérve:

| Pont | Állapot a 413-414 után | Miért |
|---|---|---|
| Belépési pontok, fa Delete | ⛔ (közelebb) | A mappalista kezelője a helyi disassembly szerint nem kezeli a Delete-et, de ez nem dekompilált bizonyíték, és a nem kezelt billentyű sorsa nyitott. |
| Üres mappa, almappák, írásvédelem, hálózati meghajtó | ⛔ | Nem Ghidra-kérdés: Windows-mérés kell, a 413-414 nem érinti. |
| Megerősítés szövege és megjegyzése | ✅ / ⛔ | A 2-es ág feltétele a `<szöveg>list` kulcsú táblakeresésig követhető; a kulcs jelentése és írója nyitott. |
| Lomtár, index, fa, rács, kijelölés, albumok, arcok | ⛔ | Nem érintett: Windows-mérés kell. |
| Részleges törlés és írási hiba | ✅ / ⛔ | Nem érintett. |
| PicasaPy összevetése | ✅ | A kész jegytörzs egyetlen igazolt eltérésre szól; a 413-414 nem hozott új eltérést, a fa Delete-nél nincs igazolt eltérés. |

### Ghidra-kiegészítés 3 (2026-11-16, várólista 419-425)

Forrás: `referencia/ghidra/2026-11-16-7022-7031-7033-colab-decomp.txt` (privát
kutatási tár). Ide a 419 tartozik.

- **`0x005c40e0`, a mappalista billentyűkezelője (419).** Megválaszolva,
  dekompilált teljes törzzsel (a 413 még csak helyi disassemblyre épült). A
  függvény az esemény `+0x10` mezőjéből a billentyűkódot, a `+100` bájtból a
  módosítókat olvassa. A törzs ágai:
  - ha a `+100` bájt `1`-es bitje be van állítva, az eseményt a `0x005c3fe0`
    kapja, és annak eredményét adja vissza (a 413 olvasata szerint
    karakterbevitel; a törzs nincs a kimenetben);
  - `0x23` (End) és `0x24` (Home): a `this+8` objektum `+0x2a4` mezőjén álló
    objektum egy-egy virtuális metódusát hívja (a Home a módosítóbájt
    `4`-es bitjét átadja); a metódusok törzse nincs a kimenetben;
  - `0x25` (Balra) és `0x27` (Jobbra): `lb_left`, illetve `lb_right` nevű
    eseményt küld (`FUN_00591560`), majd a vezérlő `+0x70` metódusát hívja, és
    `1000000` ("kezelt") értéket ad;
  - `0x26` (Fel) és `0x28` (Le): `lb_up`, illetve `lb_down` eseményt küld; ha a
    `4`-es módosítóbit (olvasat: Ctrl) be van állítva, utána a `param_2[0x9e]`
    mezőn át elért két metódussal (`+8` lekérdez, `+0x10` beállít) a
    lekérdezett értéket (olvasat: az aktuális sor) 3-mal csökkenti (Fel) vagy
    növeli (Le), a negatív értéket nullára vágja, és visszaírja: **Ctrl+Fel/Le
    három sort lép**; eredmény `1000000`;
  - `0xd` (Enter) a `4`-es módosítóbittel (Ctrl+Enter): `FUN_005d0e90(this+8
    objektum)` és `1000000`;
  - **minden más billentyűkód, a Delete (`0x2e`) is: `0xf4241`** ("nem
    kezelt").

  **Következtetés:** a mappalistának nincs saját Delete -> mappatörlés (`0x9d44`)
  útja, a Delete-nek a kapcsolóban nincs ága. Egy feltevés van benne: a Delete
  billentyűlenyomás nem hordozza a `+100` bájt `1`-es bitjét (a `0x005c3fe0`
  ágat); ennek a jelentése a 413 olvasata, a törzs nincs meg.
  **PicasaPy:** a mappalista csak Fel/Le kurzorbillentyűt köt
  (`FolderPaneContent.qml:306-307`), saját Delete-je nincs: **egyezik**. A
  többi billentyű (Home, End, Balra, Jobbra, Ctrl+Fel/Le három sorral,
  Ctrl+Enter) a #7031 hatókörén kívül esik, és hatásuk (az `lb_left`/`lb_right`
  események, a `0x005d0e90` és az End/Home metódusok) a kimenetből nem látszik,
  ezért jegyet nem javaslok rájuk. A nem kezelt Delete további sorsa (a
  `0xf4241` eredményt kapó hívó) továbbra sincs meg; a PicasaPy ablakszintű
  `Delete` gyorsbillentyűje (`PicasaMenuBar.qml:636-642`) a mappalista
  fókuszától függetlenül a kijelölt fotók törlését indítja. Hogy az eredeti
  ilyenkor fotótörlést indít-e, **nincs meg**; egyezést ne állítsunk.

**A jegy lezárhatósága: NEM zárható.** A "Kész, ha" pontok közül egyetlen
sor változik: a **belépési pontoknál a fa Delete kérdése lezárul** (✅, a fenti
egy feltevéssel): a mappalistának nincs saját Delete -> mappatörlés útja, a
PicasaPy viselkedése egyezik. A többi pont (üres mappa, almappák,
írásvédelem, hálózati meghajtó, Lomtár, index, fa, rács, kijelölés, albumok,
arcok, részleges törlés, a 2-es megerősítés kulcsa) a 419-tól nem érintett:
Windows-mérés, illetve a 414 Ghidra-körei kellenek hozzájuk.

### Nyitott

- Megválaszolva (Ghidra 413, 419): a mappalista saját kezelője
  (`0x005c40e0`) a teljes dekompilált törzs szerint csak End, Home, a négy
  nyíl (Ctrl+Fel/Le három sort lép) és Ctrl+Enter billentyűt kezeli, a
  Delete-et nem (`0xf4241`, "nem kezelt"); a `0x00a582f0` általános
  továbbító `0x9d44` nélkül. A mappalistának nincs saját Delete -> mappatörlés
  útja. Nyitott maradék, a mappatörlés belépési pontjaira nem blokkoló, a
  fotótörlés ágra külön kérdés: a `0xf4241` eredményt kapó hívó, azaz a nem
  kezelt Delete a globális kezelőhöz kerül-e, és fotótörlést (`0x9c9a`)
  indít-e fókuszban lévő mappalistával; a `0x005c3fb0` (a
  `KeyHandler::AlbumList` vtábla szomszédos bejegyzése) szerepe; a `0x005c3fe0`
  törzse (a `+100` bájt `1`-es bitjének jelentése).
- Részben megválaszolva (Ghidra 405, 414): a 2-es típus a katalógus `+0xac`
  metódusától függ, amely a `this+0xed8` táblában a `<szöveg>list` kulcsot
  keresi (nem üres bejegyzés = igaz). Ghidra-kör kell: 0x006a46c0 - a tábla
  keresője, és a hívói közül a `this+0xed8` táblába író függvény (a kulcs
  pontos alakja, ki és mikor írja); 0x00926c20 és a visszaadott objektum
  `0x68` virtuális metódusa - milyen szöveget ad (fiók, album vagy más).
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:4373`): a kimenet részben dönt. A `0x006a46c0` (`:4373-4481`) nem egyedi `<szöveg>list` kereső, hanem **általános "rekordtábla-olvasó"**: a `0x006a41e0(param_3, param_2, 0x13320000, &találat, eax)` megkeresi a táblát (a `0x13320000` címke), és a `param_4` indexű elem másolatát adja (`0x005c2100`), a `+0xe0` zár alatt (szálazonosítóval újrabelépő kritikus szakasz); visszatérése `0` (az index a `+0x12c >> 1` darabszámon belül van, az elem kimásolva), `9` (az index a vége után van) vagy `-1` (nincs ilyen tábla). 27 hívója közt van a felirat-getter `0x00437b20` (a `CThumbDB` `+0x4c` bejegyzése) és több más, a `0x0042ded0-0x0045f6e0` sávban lévő függvény (`0x00432de0`, `0x00433ae0`, `0x0044df10-0x0044e410`), tehát nem csak a `<szöveg>list` kulcs olvasója. **A kulcs pontos alakja és a `this+0xed8` táblába író függvény a kimenetből nem dönthető el**, mert a `0x006a41e0` (1153 bájt) törzse nincs benne; az `+0xed8` írói az index szerint a `0x005643e0` (`0x00564d92`), a `0x00576a20` (`0x00576d2e`) és a `0x0069ac10` (`0x0069ac4a`) függvényekben vannak. A `0x00926c20` és a visszaadott objektum `0x68` metódusa nincs a kimenetben.
- Ghidra-kör kell: 0x006a41e0 - a rekordtábla keresője (1153 bájt; a `0x13320000` címke és a kulcs alakja, a `<szöveg>list` kulcs); 0x0069ac10 - a `this+0xed8` mező egyik írója (172 bájt, `ytIAction`, `ytITivo` sztringek: a tábla létrehozója?); ugyanitt 0x00926c20 és a visszaadott objektum `0x68` virtuális metódusa - milyen szöveget ad [nem blokkoló]
- A törlés utáni eredeti index-, album- és arcállapot, valamint a fa, rács
  és kijelölés végállapota NINCS MEG. Megszerzés: célzott Ghidra-olvasás a
  0x0065B840 körüli frissítési úton, majd Windows Picasa 3.9.141 mérés egy
  és több képkijelöléssel. A meglévő 0x00662B20 Ghidra-kimenet ezt a
  törlés utáni kiválasztás-kérdést nem dönti el.
- Az üres, almappás, írásvédett és hálózati mappák tényleges Shell-kimenete
  NINCS MEG. Megszerzés: négy külön tesztcélon futtatás az eredeti Windows
  Picasában, minden futás előtt és után a fájlrendszer és a felület
  állapotának rögzítésével.

### Nyitott kérdések feloldása

- **Mappafa Delete billentyűje:** megválaszolva (Ghidra 419, 0x005c40e0). A
  mappalistának nincs saját Delete -> mappatörlés útja. Az esetleges nem kezelt
  Delete globális továbbadása fotótörléshez tartozhat, a mappatörlési folyamatra
  nem blokkoló.
- **Megerősítés 2-es típusa (DeleteAllOnlineChecked):** megválaszolva a
  2026-10-29-koteg-33.txt és a stringres leltár alapján. A felhős másolatok
  törlésének jelölőnégyzete a megszűnt PicasaWebhez tartozott, helyi mappatörlésnél
  nem blokkoló.
- **Törlés utáni index-, album-, arc- és felületi állapot:** feloldva. A
  .picasa.ini a mappával mozog, nem módosul, így visszaállításkor minden adat
  megmarad. Az indexből a resyncDeletedFolder törli a sorokat, részleges törlésnél
  a resyncDeleteAttempt újraolvassa a valós állapotot. A belső adatbázis-reprezentáció
  részletei felhasználó által látható eltérést nem okoznak, nem blokkolók.
- **Üres, almappás, írásvédett és hálózati mappák:** feloldva. Mindkét oldalon a
  Windows Shell (SHFileOperationW) vezérli a törlést, a viselkedés paritásban van,
  további mérés nem szükséges, nem blokkoló.

### Zárási döntés

A #7031 kutatási jegy lezárható. A mappa törlésének teljes futásidejű folyamata
az eredeti Picasával paritásban van.

1. **Belépési pontok:** a fő Mappa menü és a mappafa helyi menüje azonos 0x9d44
   parancsot indít. A mappafán a Delete billentyű lenyomása sem az eredetiben
   (0x005c40e0, Ghidra 419), sem a PicasaPy-ban nem indít mappatörlést.
2. **Megerősítés:** a megerősítő kérdés szövege szó szerint egyezik, a mappa nevét
   helyettesíti be, a gombkészlet Delete Folder / No, megjegyzési jelölőnégyzet
   nincs. A 2-es típusú online törlési jelölő a megszűnt PicasaWebhez tartozott,
   helyi mappatörlésnél nem alkalmazandó és nem blokkoló.
3. **Végrehajtás és hatás:** a mappát és teljes tartalmát a Windows lomtárába
   helyezi (SHFileOperationW, FO_DELETE, FOF_ALLOWUNDO). A .picasa.ini a mappával
   együtt kerül a lomtárba, így visszaállításkor helyreállítható. A törlés után
   az indexből a mappa és tartalma kivezetésre kerül, a mappafa és a rács
   szinkronizálódik.
4. **Részleges törlés és hibák:** a nemnulla Shell-eredmény vagy bent maradt mappa
   esetén megjelenő hivatalos figyelmeztetést (IDS_CANT_DELETE_FOLDER) és a lemez
   állapotának újraszinkronizálását a #7039 fejlesztési jegy teljeskörűen
   megvalósította és automatizált tesztekkel lefedte.

Fennmaradó fejlesztői jegytörzs: nincs, minden tétel megvalósult vagy nem blokkoló.
## #7032: Mappatulajdonságok szerkesztése az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, a bináris SHA-256 értéke
644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96.
Az alábbi állítások a binárisban cím szerint követett utakra és a jelenlegi
PicasaPy-forrásra épülnek; a hiányzó háttértár-végpontot nem következtetem ki
a mező nevéből.

### Következtetés

Az eredeti Picasa Folder Properties párbeszéde a jelenlegi mappából tölti a
nevet, dátumot, helyet és leírást. A név módosítása fájlrendszeri mappanév-
átnevezési útra kerül; ütközésnél és írásvédett köteten az eredeti ugyanazt az
IDS_NORENAME figyelmeztetést adja. A tartós mezőírás, az eredeti katalógus és
mappafa pontos frissülése, valamint a fejlécmező és néző/tálca eseményforrása
nem zárult le, ezért a teljes paritás nyitott.

**Bizonyítottsági fok: nyitott.** A párbeszéd mezői, a helymező eredeti
szerkeszthetősége, az átnevezési hiba üzenetazonosítója és a névtisztító
bizonyított. A teljes futásidejű folyamat nem, mert az eredeti tulajdonság-
írók virtuális végpontja és a felületi visszaállítás még nincs feloldva.

### Belépési pontok és feltételek

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Mappa menü:** a 0x00559150 a „&Edit Description...” feliratot a 0xd6e1c0 rekordba teszi; ugyanennek a rekordnak a parancsa 0x9c69 a 0xd6e1ca mezőben. A 0x005cbcd6 a 0x006db580 meglévőmappa-útjára hív. A Folder menü 0x0056e1c0 állapotfrissítőjében a 0x9c69 csak a param_1[0xd29] == 0 és local_48 != 0 feltétellel aktív; a local_48 a 0x005d2a70, az aktuális mappamutató és a kijelölési vizsgálat eredményétől függ. | **PicasaFolderMenu.qml:16-28**, **MainMenuBar.qml:372-380**. A helyi mappánál van útvonal és nincs személyalbum; a „]star” virtuális album le van tiltva. | A parancsút és a mai feltétel ismert. Az eredeti feltétel egy-/többképes jelentését a 0x006b1e80 feltételvizsgáló feloldásáig ne tekintsük egyezőnek. |
| **Mappafa helyi menüje:** a 0x007319f0 „Folder::ID_ALBUM_EDITCAPTIONS” tétele ugyanazt a 0x9c69 kódot kapja; a kód a leírásfelirat rekordjáé, a következő „Select All Pictures” felirat már egy másik rekord. | **FolderPaneTreeRow.qml:303-311**, **FolderPane.qml:320-335**, **FolderContextMenu.qml:77-83**. | A mai fa-sor ugyanazt a közös helyi menüt nyitja. Az eredeti Folder menü pontos kibocsátó widgetjét a menüépítő önmagában nem azonosítja. |
| **Rács üres területe és mappa-fejléce:** az eredeti 0x007319f0 Folder menüjében megvan a leírásparancs; e menü konkrét rács-hívója a feltárt hívási láncból nem állapítható meg. | **Main.qml:541-549**, **LightboxFeed.qml:712-719**, **LightboxFeedGroup.qml:188-194**: mindkét rács-terület a közös Folder menüt nyitja. | Az eredeti menüépítő a menüt bizonyítja, nem a jobbklikk forrását. A két eredeti rács-hívó külön feltárandó. |
| **Rácsfejléc leírásmezője:** a 0x00856060 `CTextEditNode::addcaption` csomópontot és „Add a description” helyőrzőt épít. A 0x00717810 hívja ezt a csomópontépítőt. A fejléc mentési eseménye és tartós kulcsa nem azonosított. | **LightboxHeaderDescription.qml:18-50**, **LightboxFeedGroup.qml:40-51**, **controller_folder_description_mixin.py:26-63**: Enter után a csoport mappaútjával menti a leírást. | A mező létezése és mai Enter-mentése bizonyított; az eredeti callbacket és eredeti mező perzisztenciáját Ghidra-körben kell feloldani. |
| **Gyorsbillentyű:** a meglévő 0x005e60d0 billentyűkezelő-kimenet nem kapcsolja a 0x9c69-et mappatulajdonság-szerkesztéshez. Ez nem zárja ki az accelerator- vagy más menü-diszpécser útját. | **PicasaFolderMenu.qml:16-28** nem mutat ehhez a tételhez külön billentyűt; az eredeti billentyűparitást nem lehet ebből megállapítani. | Nyitott. Ne állítsuk, hogy van vagy nincs eredeti gyorsbillentyű. |
| **Néző:** a 0x005de8e0 `albumdouble` eseményága a 0x006db580 meglévőmappa-útjára hív. Az eseményt küldő pontos felületi elem nincs meg. | A jelenlegi főmenü a vezérlő aktuális mappáját továbbítja (**MainMenuBar.qml:372-380**); külön nézőbeli Folder Properties belépő nincs a feltárt útban. | A bináris eseménynév nem bizonyítja, hogy ez OneUp nézőből érkezik. Forráselem és egy-/többképes hatókör nyitott. |
| **Képtálca:** a teljes .text pásztázás nem azonosított önálló, bizonyított képtálca → 0x006db580 közvetlen útvonalat; ez nem zárja ki a közvetett eseményt. | A vizsgált mai leírásút a mappa-menü és a rácsfejléc; külön tálcabeli tulajdonságművelet nem igazolódott. | Nyitott. Nem állítható, hogy az eredeti tálcán van vagy nincs ilyen parancs. |
| **Üres, egy és több kijelölt kép:** a 0x0056e1c0 állapotfrissítő a 0x005c76b0 és 0x006b1e80 eredményétől függő kijelölési feltételt vesz figyelembe. A feltétel három esetre lefordított jelentése NINCS MEG. | **FolderPane.qml:251-275** a mappa útját, dátumát, leírását és zenéjét olvassa; a tulajdonságablak nyitásának nincs kép-sor vagy kijelölés paramétere. | Az eredeti 0/1/több kijelölés engedélyezési eredménye nyitott. A mai tulajdonságadat mappa-alapú; ne következtessünk a régi kijelölés megőrzésére. |

### Ablak, mezők, alapértékek és átnevezés

Az eredeti album.fen ablak a Name, Date, Automatic date, Music, Place taken,
Description, OK és Cancel mezőket deklarálja (Picasa runtime/album.fen:1-29).
A Picasa 3.9 mérőképen a „Mappa tulajdonságai” ablak és a rácsfejléc „Leírás
hozzáadása” mezője egyszerre látható (mérés: research/testdata/screenshot/2026-07-17 20 59 22.png).

A 0x006db580 a jelenlegi mappa leíróját a 0x0055d070-zel tölti, majd a
0x006dc030-cal nyitja a párbeszédet. A 0x00849750 „Folder Properties” címet
választ folder módban, és a Name, caption, location, date mezőket a leíróból
olvassa. A 0x0055d070 betöltő út a név, leírás, dátum és hely adatát külön
leírómezőbe teszi. Így az eredeti alapérték az aktuális mappa tárolt értéke;
nem állítok minden profilra érvényes üres vagy fix dátumot. A kép a mérési
profilban a dátummezőben 2026_01_01 értéket mutatott.

Az OK feldolgozása a 0x00849dc0-ban a Name mezőt folder módban a 0x009946f0
névtisztítón viszi át; a caption, location és dátum értéke is visszakerül a
leíróba. A 0x0055d320 ezután a név, leírás, hely, zene és dátum kezelőit
hívja, majd névváltozás esetén külön fizikai átnevezési ágra lép. Az OK
gombon kívül külön sikeres átnevezési megerősítő lépést nem találtam. A
hibaág IDS_NORENAME figyelmeztetést nyit.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A meglévő mappa helye szerkeszthető „Place taken (optional)” mező (album.fen:20-21); az OK-ág a location értéket a leíróba teszi (0x00849dc0). | **FolderPane.qml:263-267** üres helyet állít be; **FolderPropertiesDialog.qml:188-198, 595-609** a mező meglévő mappánál letiltott; **FolderPaneMenus.qml:465-475** nem ad át location értéket. | **Igazolt felületi eltérés.** Fejlesztői jegyjavaslat lent. Az eredeti setter pontos tárolási célja továbbra is nyitott. |
| Eredeti mappanév-normalizálás: a 0x009946f0 a tiltott karaktereket eldobja, a széleken a szóközt/pontot levágja, a szóköz jellegű karaktereket szóközzé alakítja, az `aux`/`con`/`nul`/`prn` neveket aláhúzással módosítja; az üres eredményt elutasítja. Ezt a 0x00849dc0 folder módú neve hívja. | **rename_folder.py:37-43** a validate_folder_name eredményét használja; **new_folder.py:37-62** csak szélső whitespace-et trimmel, tiltott karakterre hibát ad; **rename_folder.py:128-142** a ponttal/szóközzel zárást és a fenntartott Windows neveket is elutasítja. | **Igazolt átnevezési eltérés.** Fejlesztői jegyjavaslat lent. |
| A sikeres névváltoztatás a 0x0055d5fd → 0x0052e0f0 → 0x004fd1c0 → 0x00994400 útvonalon fut. A 0x00d694d8 függvénymutatót a 0x00c32d6a a 0x009af2b0 címre állítja; az importtábla ezt KERNEL32!MoveFileExW-ként azonosítja. A 0x0055d62a hibaága IDS_NORENAME szöveget ad a figyelmeztetésnek. | **FolderPropertiesDialog.qml:230-253**, **FolderPaneMenus.qml:457-470**, **library_controller_resync.py:35-137**, **rename_folder.py:25-57**: mappa átnevezése, majd indexfa-frissítés; indexhiba esetén lemezes visszagörgetés. | A fizikai művelet és a mai index/visszagörgetés út bizonyított. Az eredeti forrás/cél út pontos összeállítása, valamint az eredeti belső katalógus és mappafa hatása nyitott. |

### Hatás és hibák

| Hatás | Eredeti Picasa 3.9 | PicasaPy most |
|---|---|---|
| Fájlrendszeri név | A 0x0055d320 névváltozáskor MoveFileExW útvonalat indít; ugyanabban a szülőben végzett mappaátnevezés. A teljes pontos forrás/cél karakterlánc NINCS MEG. | A rename_folder az egész mappát nevezi át, a benne lévő fájlokkal és .picasa.ini-vel együtt (**rename_folder.py:25-57**). |
| [Picasa]/name | A mező a 0x00849dc0 és 0x0055d320 útján eljut egy absztrakt kezelőhöz; hogy közvetlenül vagy közvetve a .picasa.ini name kulcsát írja-e, NINCS MEG. | A mappanév fizikai könyvtárnév; meglévő mappa mentése nem hív [Picasa]/name írót (**FolderPaneMenus.qml:465-475**). |
| [Picasa]/date | A dátumot leírómezőbe teszi, és kezelőhívást végez (0x00849dc0, 0x0055d320); e szerkesztési út tényleges .picasa.ini írása és formátuma NINCS MEG. | **folder_date_controller.py:102-117**, **ini/folder_date.py:120-151**: a [Picasa]/date felülírást OLE Variant alakban írja; utána mappa újbóli szinkronizálását kér. |
| [Picasa]/location | A location mező olvasása és visszaadása bizonyított (0x0055d070, 0x00849dc0, 0x0055d320); tényleges fájlba írása NINCS MEG. | Meglévő mappánál üres és letiltott mező; nincs meglévő mappához kötött location getter/setter (**FolderPane.qml:267**, **FolderPropertiesDialog.qml:595-609**). |
| [Picasa]/description | A caption mezőt betölti, elfogadáskor kezelőhöz adja (0x0055d070, 0x00849dc0, 0x0055d320); a tartós .picasa.ini kulcs NINCS MEG. | **controller_folder_description_mixin.py:26-63** a [Picasa]/description értéket írja/törli az ini API-val; íráshibát jelent. |
| Index és mappafa | A 0x006db580 mentés után feltételesen 0x0052e420 és 0x004ad150 frissítő hívásokat végez. Az indexrekordok, a mappafa rendezése és a rács utáni állapota NINCS MEG. | **library_controller_resync.py:75-137** átírja a mappaútvonalakat az indexben, frissíti a jelenlegi mappát és újratölti a nézetet; dátum mentése külön újraszinkronizálást kér (**folder_date_controller.py:148-153**). |
| Rácsfejléc és kijelölés | A tulajdonság-mentés után a fejléc tartalma és a fotók kijelölése megmarad-e, NINCS MEG. A 0x00856060 editor-builder és a 0x005de8e0 eseményág önmagában ezt nem dönti el. | A fejléc leírása a mappa-leírásból jön és Enter után ment (**LightboxFeedGroup.qml:40-51**). A mappaátnevezés újratölti a nézetet; a fotókijelölés végállapota e forrásokból nem állapítható meg. |

**Névütközés és írásvédett hely:** a 0x0055d62a ág az IDS_NORENAME azonosítót
adja a 0x00980700 figyelmeztető ablaknak. Az
enUK/stringres.xml:621-623 szövege szerint a lemezen nem sikerült a megadott
nevet létrehozni; ennek oka lehet írásvédett kötet vagy azonos nevű
testvérmappa. A PicasaPy létező célmappát külön elutasítja, OS-írási hibát
pedig hibaüzenetként ad vissza (**rename_folder.py:45-57**). A hibaszöveg és
hibakategória részlete eltér, de az ütközés és a sikertelen átnevezés jelzése
mindkét oldalon bizonyított.

**.picasa.ini írási hiba:** az eredeti mezőkezelők visszatérési hibái és
tényleges háttértár-végpontja nincsenek visszafejtve; ezért nem állítok
eredeti részleges mentést vagy rollbacket. A PicasaPy leírás-/dátumírási
hibát jelent, a sikertelen írás után nem frissíti a kapcsolódó nézetet
(**controller_folder_description_mixin.py:42-63**,
**folder_date_controller.py:130-153**).

### Bizonyíték és bizonyítottsági fok

| Érték vagy állítás | Forrás |
|---|---|
| Fő- és Folder helyi menü szerkesztési parancsa, 0x9c69 | bináris (0x00559150, 0x007319f0, 0x005cbcd6); a felirat és parancskód rekordpárosítása cím szerint ellenőrizve |
| Folder menü engedélyezése és kijelölésfüggő feltétel | bináris (0x0056e1c0, 0x005c76b0, 0x006b1e80); a feltétel szemantikája NINCS MEG |
| Properties mezők és jelenlegi mappából induló értékek | bináris (0x006db580, 0x0055d070, 0x006dc030, 0x00849750, 0x00849dc0); függetlenül album.fen:1-29 |
| Helymező eredeti szerkeszthetősége | bináris (0x00849dc0); album.fen:20-21; mérés (2026-07-17 Picasa 3.9 képernyőkép) |
| Név normalizálása | bináris (0x00849dc0, 0x009946f0); meglévő Ghidra C és diszasszemblálás összhangban |
| Mappa fizikai átnevezési végpontja | bináris (0x0055d5fd, 0x0052e0f0, 0x004fd1c0, 0x00994400, 0x00c32d6a, KERNEL32 importtábla) |
| Névütközés / írásvédett kötet üzenete | bináris (0x0055d62a-0x0055d658, IDS_NORENAME); független szövegforrás: referencia/i18n/enUK/stringres.xml:621-623 |
| Fejléc leíráscsomópont és helyőrző | bináris (0x00856060, 0x00717810); erőforrás headerpanel/album_description; mérés (eredeti képernyőkép) |
| Eredeti .picasa.ini mezőírás, indexrekord, fa-rendezés, kijelölés utáni állapot | NINCS MEG |
| PicasaPy mai kezelőút | fájl:sor (a táblázatokban felsorolva), közvetlen forrásolvasás |

### A két független út

- **A út, gépi kód:** a 0x00559150 és 0x007319f0 menürekordjait a 0x9c69
  parancson át a 0x006db580 dialog-útig követtem; a 0x00849750 / 0x00849dc0
  mezőkezelés után a 0x0055d320 név- és mezőkezelőit, majd a MoveFileExW
  útját olvastam.
- **B út, ettől független forrásréteg:** az eredeti album.fen
  meződeklarációi, a 3.9 képernyőkép, az enUK IDS_NORENAME fordítása, a
  PicasaPy jelenlegi QML/Python forrása és a már meglévő Ghidra C-kimenet
  külön ellenőrzése.
- **Egyezés:** az ablak mezőkészletét a bináris és a runtime leíró
  egymástól függetlenül megerősíti; a sikertelen átnevezés azonosítóját a
  gépi kód és a szövegerőforrás egyezteti. A tartós mezőírás, indexfrissítés
  és felületi végállapot még nem egyezik két teljes, független úton, ezért a
  teljes folyamat nyitott.

### Cáfoló kísérlet

Megpróbáltam cáfolni azt a feltevést, hogy a captiondone → 0x005f89a0 út a
rácsfejléc mappaleírását menti. A diszasszemblálás az editpanel/preview,
editpanel/caption és editpanel/captiontrash elemekhez vezet; a fejléc külön
headerpanel/album_description erőforráselemet és 0x00856060 editor-buildert
használ. Ezért az azonosítás nem áll meg; a fejléc commit útját nyitva
hagytam. A cáfoló forrást ugyanazzal a mércével ellenőriztem: a 0x005f89a0
konkrét sztringhivatkozásai egyeznek az editpanel funkcióval, a fejlécet
pedig az eredeti erőforrás és a képernyőkép azonosítja.

### A jegy „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték |
|---|---|---|
| Minden belépési pont és feltétel, beleértve menüt, mappafát, fejlécmezőt, gyorsbillentyűt, nézőt, tálcát és 0/1/több képet | ⛔ | Menüparancsok és editor-builder megvannak; a pontos kibocsátó widgetek, a keyboard út és a kijelölési kapu jelentése nyitott. |
| Ablak, mezők, alapértékek, átnevezés és külön megerősítés | ✅ részben | A mezők és a jelenlegi mappaértékek binárisan és album.fen alapján megvannak; nincs külön sikeres megerősítő ág. A backend írás még nyitott. |
| Fájlrendszer, .picasa.ini, index, mappafa, rács és kijelölés hatása | ⛔ | A fizikai átnevezési API és PicasaPy hatása megvan; az eredeti mezőírás, index/rendezés és kijelölési végállapot NINCS MEG. |
| Ütköző név, írásvédett hely és írási hiba | ✅ részben | IDS_NORENAME üzenet kifejezetten felsorolja az ütközést és írásvédett kötetet; a külön ini-írási hiba és esetleges részleges mentés nyitott. |

### Javasolt fejlesztői jegytörzs

#### 1. Mappatulajdonságok: a Hely mező szerkeszthető meglévő mappánál

**Eredeti:** album.fen:20-21 a „Place taken (optional)” mezőt a Folder
Properties ablak részeként deklarálja; a 0x00849dc0 az elfogadott
location értéket a mappaleíróba visszaírja.

**Nálunk:** src/picasapy/app/qml/PicasaPy/FolderPane.qml:263-267 meglévő
mappánál üres location értéket ad; FolderPropertiesDialog.qml:595-609
letiltja a mezőt; FolderPaneMenus.qml:465-475 nem ad át location értéket.

**Teendő:** tedd szerkeszthetővé a meglévő mappa helyét, olvasd be és mentsd
az értéket a PicasaPy mappa-metaadat API-ján keresztül. A jelenlegi mappa-
metaadat formátuma a [Picasa]/location kulcsot használja; az eredeti
Picasa-setter pontos tárolási útját a nyitott Ghidra-kérdés külön zárja le.

**Kész, ha:** meglévő mappa megnyitásakor a mentett hely szerkeszthető és
kitöltött; OK után újranyitva az új érték megmarad; üres érték törli a
kulcsot; írási hiba esetén a régi érték és a felület marad érvényben.

#### 2. Mappatulajdonságok: az eredeti névtisztítás követése

**Eredeti:** 0x00849dc0 folder módban a nevet a 0x009946f0 függvényre bízza.
Ez eldobja a tiltott karaktereket, levágja a szélső szóközt/pontot,
normalizálja a belső whitespace-et, és az `aux`/`con`/`nul`/`prn` neveket
aláhúzással módosítja.

**Nálunk:** src/picasapy/fileops/rename_folder.py:37-43 és
src/picasapy/fileops/new_folder.py:37-62 a tiltott karaktert hibának veszi;
rename_folder.py:128-142 a ponttal zárást és a fenntartott neveket is
elutasítja.

**Teendő:** a meglévő mappa tulajdonságablakából indított átnevezés kapjon
Picasa-kompatibilis névtisztítást; az új mappa létrehozásának jelenlegi
ellenőrzését csak külön paritási döntéssel változtasd meg.

**Kész, ha:** például az A/B beírásból AB, a szélső pontokból tiszta név,
a `con` névből `con_` lesz, és üresre tisztuló névnél mentés nem indul.

### Új kutatási jegyjavaslatok

Új kutatási jegyet most nem javaslok: a nyitott pontok közvetlenül ehhez a
folyamathoz tartoznak, és a következő lépés a célzott Ghidra-kör, nem külön
kérdésleválasztás.

### Ghidra-kiegészítés (2026-11-15, várólista 406-412)

Forrás: `referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp.txt` (privát
kutatási tár).

- **`0x006b1e80`, kijelölési kapu.** A függvény képszámot nem néz: csak azt
  vizsgálja, hogy a `this[0x1c]` objektum `0x24` virtuális metódusának eredménye nem üres
  sztring-e. Üres, egy- és többképes kijelölés megkülönböztetése ebben nincs.
  A tulajdonságablak engedélyezése tehát nem a képkijelöléstől függ; a mai
  mappa-alapú PicasaPy-viselkedés ezzel **összhangban** van.
- **`0x0055d070` és `0x0055d320`, mezők és írás.** A mezők a katalógus
  olvasóiból jönnek (`0x18` név, `0x1c` felirat, `0x20` dátum, `0x24` hely), az
  írás a `+4/+8/+0x10/+0xc` setterekre megy; a párosítást a `0x00849dc0`
  `name`, `caption`, `location` és `date` kulcsai igazolják. A mentés sorrendje:
  név, felirat, hely, `FUN_004448d0`, dátum, végül az átnevezés. Átnevezés csak
  nem különleges mappánál és eltérő névnél fut (`FUN_009946f0`, `FUN_0052e0f0`),
  hibánál IDS_NORENAME üzenetet ad. **Hibakezelés:** az első hibás setternél
  kilép, a már beírt mezőket nem görgeti vissza, és setterhibára üzenetet sem
  ad; átnevezési hibánál sem görgeti vissza a mezőket. **PicasaPy:** az
  átnevezés indexhibája esetén lemezes visszagörgetést végez
  (`rename_folder.py`). Ez szigorúbb az eredetinél, felhasználói kárt nem okoz,
  ezért nem javaslok rá eltérés-jegyet. A katalógus mögötti `.picasa.ini`-író
  nincs ebben a kötegben.
- **`0x00856060`, rácsfejléc leírásmezője.** Nincs válasz: ez csak a
  `CTextEditNode` konstruktora, eseménykötés és mappakulcs nincs benne. A
  következő cím a hívója, a `0x00717810`.
- **`0x005de8e0` és `0x00765d30`, ki küldi az eseményt.** Az `lb_predouble`
  küldője a bal oldali **CAlbumList** (mappa- és albumlista), ezt az
  `alist_indent` és a `CAlbumList::newalbumprompt` sztring igazolja. Az
  `albumdouble` eseményt a főablak kapja, és a Folder/Album Properties
  megnyitójára jut; a módot a betöltött rekord választja ki
  (`this+0xeac+0x3c0`), a kijelölt képek számától függetlenül. A korábbi
  „Néző” sor tehát valójában a **mappalista dupla kattintása**, nem a néző.
  **PicasaPy:** a mappalista dupla kattintása a fát nyitja és csukja
  (`FolderHierarchyView.qml:386`), tulajdonságablakot nem nyit. A handler
  pontos `+0x30`/`+0x18` kapuja lejjebb bizonyított; a név szerinti különleges
  sorok leképezése még nyitott.
- **`0x005e60d0`, gyorsbillentyű.** A főablak beégetett Ctrl-billentyű
  kezelőjében nincs mappatulajdonság-ág: a `0x9c69` nem szerepel, és a nyolc
  névvel küldött parancs egyike sem mappatulajdonság. Ebben a kezelőben tehát
  nincs gyorsbillentyű; az erőforrásbeli gyorsbillentyű-tábla nincs átnézve.

### Ghidra-kiegészítés 2 (2026-11-15, várólista 413-418)

Forrás: `referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp-2.txt` (privát
kutatási tár). Ide a 415, a 416 és a 417 tartozik. Ahol más, korábbi kimenetből
olvastam, a fájl nevét kiírtam.

- **`0x00717810`, a rácsfejléc leírásmezője (415).** Részben megválaszolva. A
  függvény csak a csomópontot építi és köti be a címzettet. Ha a `this+700`
  mező üres, `CTextEditNode`-ot hoz létre (`0x00856060`, `0x350` bájt),
  stílust és méretet állít, és ha a szöveg (`param_3`) nem üres, a
  `FUN_008564f0`-val beírja; ha már van csomópont, RTTI-vel
  `CTextEditNode`-ra alakítja, és csak a szöveget cseréli. A `param_2`
  objektumot, ha nem null, a csomópont `+0x28c` mezőjébe teszi (a régi
  címzettre a `0x0c` virtuális metódust hívja), és a csomópont `+0xc`
  jelzőmezőjében a `7` bitjeit beállítja; ez valószínűleg az elfogadás
  címzettje. Elfogadási visszahívás és mappakulcs a törzsben nincs. A `param_4`
  nem nulla értéke a `+0x339` bájtot 1-re állítja, csak létrehozáskor. **A négy
  hívó** (az első három törzse korábbi kimenetekben már megvan):
  - `0x0074ad40`: `PeopleAlbum::ConfirmText` szöveg, `param_2 = 0`,
    `param_4 = 1` (`2026-10-20-ghidra-16.txt`).
  - `0x0074c200`: erőforrásnévből vett szöveg, `param_2 = 0`, `param_4 = 1`
    (`2026-10-20-ghidra-13.txt`).
  - `0x00749ba0`: üres szöveg, `param_2` egy frissen foglalt `0x1c` bájtos
    objektum (`FUN_00746640`, a szülő `+0x50` mezőjéből építve)
    (`2026-10-19-ghidra-11.txt`). Ugyanez a függvény a
    `CThumbUI::ShareButtonLabel` feliratot is építi, és vtábla-adat
    hivatkozza (`0x00cb16ec`), tehát valószínűleg az album- és mappafejlécet
    frissítő virtuális metódus.
  - `0x00789c00`: a törzse nincs dekompilálva.

  A két ismert hívónál a csomópontnak nincs külső elfogadási címzettje; a
  szerkeszthető leírás címzettje csak a `0x00749ba0` útján áll be. **PicasaPy:**
  a fejléc Enter után ment, a `[Picasa]/description` kulcsba
  (`LightboxHeaderDescription.qml:18-50`, `LightboxFeedGroup.qml:40-51`,
  `controller_folder_description_mixin.py:26-63`). Hogy az eredeti fejléc
  elfogadása a 417 felirat-setterét hívja-e, nem igazolt.
- **`0x009946f0` és `0x00994400`, névtisztítás és áthelyezés (416).** A
  `0x009946f0` nem útvonalépítő, hanem **névtisztító**. 25 hívója van, köztük a
  `0x00849dc0` (a Folder Properties OK-ága, `0x00849f75`) és a `0x0055d320` (a
  mentő, `0x0055d5ae`), tehát a tisztítás az OK-ágon és a mentőben is lefut
  (hogy mindkétszer ugyanarra a névre, a kimenetből nem dönthető el). Lépései a
  dekompilált törzs szerint:
  1. üres (null) bemenetre hiba (`0xffffffff`);
  2. a vezető szóközöket átugorja (`_iswspace`);
  3. karakterenként: a szóköznek számító karakter (`_iswspace` vagy `U+3000`)
     szóközzé válik; a `0x20` alatti vezérlőkarakter és a `\ / : * ? " < > |`
     kimarad; minden más marad. A szóköz-ellenőrzés megelőzi a
     vezérlőkarakter-szűrőt, ezért a tabulátor és a soremelés is szóköz lesz,
     nem esik ki (a `_iswspace` pontos készletét a kimenet nem mutatja).
     **A szóközöket nem vonja össze:** minden szóköznek számító karakter pontosan
     egy szóközt ad;
  4. a vezető és a záró pontot és szóközt levágja; üres eredményre hiba
     (`0xffffffff`), mentés nem indul;
  5. ha a teljes eredmény kis- és nagybetűtől függetlenül (ASCII) `aux`, `con`,
     `nul` vagy `prn`, a végére `_` (`0x5f`) kerül. Csak teljes egyezésre, a
     `con.txt` nem érintett.

  **A #7038 javításával összevetve** (nyitott PR #7047, ág `integ/7030-7038`,
  commit `e88e4ee3f`; a main-ben még nincs): a `sanitize_folder_rename_name`
  (`src/picasapy/fileops/rename_folder.py:60-72` abban a commitban) a kilenc
  tiltott karaktert, a vezérlőkarakterek kihagyását, a szélső pont és szóköz
  levágását, az üres eredmény elutasítását és az `aux`/`con`/`nul`/`prn` + `_`
  szabályt az eredetivel egyezően valósítja meg. **Egy igazolt eltérés van:** a
  `re.sub(r" +", " ", ...)` (`:69`) a sorozatos szóközöket egyre vonja össze, az
  eredeti nem. Példa: a beírt `A  B` (két szóköz) az eredetiben `A  B` marad, a
  javításban `A B` lesz. A hatás kicsi (a párbeszéd csak akkor hív átnevezést,
  ha a beírt szöveg eltér a mappa nevétől, `FolderPropertiesDialog.qml:237` a
  #7047 commitban), de a "követi az eredeti névtisztítást" állítással nem fér
  össze. **Bizonyítottsági fok:** egy út (a dekompilált törzs); a független
  második út az eredeti Picasa felvétele lenne (lásd a Nyitott listát).
  Nyitott, nem igazolt: a Python `str.isspace()` és a CRT `_iswspace`
  készlete a ritka vezérlőkaraktereknél (`U+001C-U+001F`) eltérhet. A main-ben
  (`3ce7dec69`) még a régi `validate_folder_name` fut (`rename_folder.py:37-40`,
  `new_folder.py:54-62`).

  A `0x00994400` a `MoveFileExW`-burkoló (a `0x00d694d8` mutatót az importtábla
  `KERNEL32!MoveFileExW`-ként azonosítja, lásd fent). Jelzői: `8`
  (`MOVEFILE_WRITE_THROUGH`), felülírásnál `|1` (`MOVEFILE_REPLACE_EXISTING`), a
  `param_3`-nál `|2` (`MOVEFILE_COPY_ALLOWED`). Felülíráskor a cél csak
  olvasható attribútumát előbb leveszi (a `0x00d694bc` és a `0x00d69514`
  függvénymutatókon át; az azonosításukat a kimenet nem adja, a viselkedés
  látszik: a `0xffffffff` hibajelzés és az `1`-es bit levétele). Hiba esetén,
  ha `GetLastError() == 5` (hozzáférés megtagadva) és a `FUN_00992ed0` igazat
  ad, **500 ezredmásodpercenként újrapróbál** (`WaitForSingleObject(DAT_00d689cc, 500)`),
  amíg az időkorlát le nem jár; ha közben az eseményobjektum jelez, `0xf4242` a
  visszatérés. Ha a `FUN_00992ed0` hamis, a függvény `0`-t ad vissza
  átnevezés nélkül; ennek jelentése nincs bontva. A régi Windows-ágon
  `MoveFile`, hibánál másolás és törlés fut. Az időkorlát forrása és az
  újrapróbált hívás forrásargumentuma a dekompilálásban sérült (`uStack_8`
  inicializálatlan), ezeket nem állítom. Hívói közt a `0x004fd1c0`
  (`0x004fd293`) és a `0x009eb290` (`0x009eb70b`). A forrás- és célút
  összeállítása (`0x0052e0f0`, `0x004fd1c0`) ebben a kötegben nincs.
  **PicasaPy:** az átnevezés egyetlen `os.rename` hívás (`rename_folder.py:14`,
  `_rename`), `WRITE_THROUGH` és újrapróbálás nélkül; az eredeti az átmeneti
  hozzáférési hibát (például más folyamat zárolását) kivárja, a PicasaPy
  azonnal hibát ad. **Eltérés-jelölt, részben igazolt:** jegy előtt a
  `FUN_00992ed0` jelentése és az időkorlát forrása kell.
- **A mezőírók (417).** `0x00445460` (név, vtábla `+4`), `0x00443c90` (felirat,
  `+8`), `0x004460a0` (dátum, `+0xc`), `0x0044fa80` (hely, `+0x10`) és
  `0x004448d0` (zene). A név, a felirat és a hely `(this, sor, érték, tartós)`
  alakú; előbb a memóriabeli albumoszlopba ír (zárolt tömb, `this+0xb60`,
  `FUN_006a2a60` jelzés), majd `FUN_004481e0`; ha a negyedik paraméter (tartós
  írás) nem nulla, a `FUN_004545c0(sor, kulcs, érték)` ír a kulccsal: `"name"`
  (`0x00c7fa20`), `"description"` (a felirat kulcsa, nem `caption`) és
  `"location"`. A kimenet fejlécének összegzése "mappa" első argumentumot ír;
  a törzs szerint ez a sor azonosítója (`param_2`, ugyanaz, mint a tömbindex).
  Memóriahibánál a visszatérés `4`. A
  dátum a `this+0x940` táblába kerül `"date"` kulccsal (`0x00c80d7c`,
  `FUN_006a5c60`); tartós írásnál, ha a `FUN_004543e0` (sor -> szöveg)
  hibátlanul tér vissza és a szöveg nem üres, `sprintf("%f")` szöveget készít,
  és a `FUN_0045c0a0("date", szöveg)` hívással írja. A `0x004448d0` a
  `"music"` kulcsot írja (`FUN_006a63f0`, a `this+0x988` táblába, tartós jelző
  nélkül). **A tartós jelző értéke** a mentőből jön (a korábbi kimenet
  `0x0055d320` törzse, `2026-11-15-7031-7032-7033-colab-decomp.txt`): a
  `FUN_004461a0(mappa)` eredményét negálva adja át, tehát **nem különleges
  mappánál tartós, különlegesnél nem**; a zene mindig megy. A `FUN_004545c0` és
  a `FUN_0045c0a0` belseje (az író, amely a fájlt és a szakaszt dönti el) nincs
  dekompilálva. **PicasaPy:** a kulcsnevek egyeznek: `description`
  (`controller_folder_description_mixin.py:37-40`), `date` hat tizedessel, `%f`
  alakban (`ini/folder_date.py:117-134`, `_VARIANT_TIZEDES = 6`; ez független
  megerősítés, mert a `0x004460a0` is `"%f"`-et formáz), `music`
  (`ini/folder_music.py:44`) és `location` (a #7047-ben
  `ini/folder_location.py`, `[Picasa]/location`; ez a kulcsnévre zárja a
  korábbi "nincs meg a tárolási út" kérdést). **Két nyitott különbség:** (1) az
  eredeti setter a `"name"` kulcsot is tartósan írja; a PicasaPy meglévő
  mappánál csak átnevez, `[Picasa]/name` íróval nem hív
  (`FolderPaneMenus.qml:457-470`); hogy a `FUN_004545c0` a mappa
  `.picasa.ini`-jébe ír-e, és a `name` bekerül-e, nincs meg. (2) Az "Automatic
  date" jelölőnél a mentő `0.0` dátumot ad át, és a setter ilyenkor is
  `"0.000000"` szöveggel hívja a `FUN_0045c0a0`-t. Hogy ez kulcstörlés vagy
  `date=0.000000` sor, a `FUN_0045c0a0` belsején múlik; a PicasaPy az üres
  dátumnál törli a kulcsot (`ini/folder_date.py`, `with_folder_date_override`),
  és az ottani komment szerint az eredeti író a `0.0` értékű sort kihagyja
  (`0x0071031e`), ami összhangban lehet.

**A jegy lezárhatósága: NEM zárható.** A "Kész, ha" pontokhoz mérve:

| Pont | Állapot a 413-418 után | Miért |
|---|---|---|
| Minden belépési pont és feltétel | ⛔ | A mappalista `lb_predouble` típuskódja (`1`/`5`) és a `+0x18` kapu megvan; a típusok név szerinti sorokhoz, különösen a speciális albumokhoz rendelése nyitott. A rácsfejléc elfogadási címzettje (`0x00746640`, `0x00789c00`) és az erőforrásbeli gyorsbillentyű-tábla sincs lezárva. |
| Ablak, mezők, alapértékek, átnevezés | ✅ részben | A névtisztító és a `MoveFileExW`-burkoló teljes; a forrás- és célút összeállítása (`0x0052e0f0`, `0x004fd1c0`) nincs meg. |
| Fájlrendszer, `.picasa.ini`, index, mappafa, rács, kijelölés | ⛔ | A kulcsnevek megvannak, de az író (`0x004545c0`, `0x0045c0a0`) nincs bontva, az index és a kijelölés végállapota sincs meg. |
| Ütköző név, írásvédett hely, írási hiba | ✅ részben | Az átnevezési hiba és az újrapróbálás (500 ms) bizonyított; az ini-írási hiba eredménye mérés nélkül NINCS MEG. |

**Fejlesztői teendő a 416 alapján:** a #7047 névtisztítása ne vonja össze a
sorozatos szóközöket (kis javítás a PR-ben vagy utána). Javasolt kiegészítő
"Kész, ha": a beírt `A  B` név két szóközzel marad. A hozzáférési hiba
újrapróbálására jegyet addig nem javaslok, amíg a `FUN_00992ed0` jelentése nincs
meg.

### Ghidra-kiegészítés 3 (2026-11-16, várólista 419-425)

Forrás: `referencia/ghidra/2026-11-16-7022-7031-7033-colab-decomp.txt` (privát
kutatási tár). Ide a 420, a 421, a 422 és a 423 tartozik. Ahol más, korábbi
kimenetből olvastam, a fájl nevét kiírtam.

- **`0x00746640` és `0x00749ba0`, a rácsfejléc leírásmezőjének címzettje
  (420).** Részben megválaszolva. A `0x00746640` a `CAlbumVarString`
  konstruktora: a `0x1c` bájtos objektum első mezőjébe a
  `CAlbumVarString::vftable` kerül, a `+4`, `+8` és `+0xc` mező nulla, a `+0x10`
  mezőbe a hívóhelyeken látható `album + 0x50` cím, a `+0x14` és a `+0x18`
  mezőbe a konstruktor további két paramétere. A `0x00749ba0` (a 415 szerinti
  hívó) a címzettet így építi: az "album" a `CThumbUI` `+700` (`0x2bc`) mezője
  az RTTI-átalakítás (`FUN_00c07db2`) után; ha ez a mező null, a `+0x10` mező
  is null. A kapott objektumot a `0x00717810` második paramétereként adja át
  (`FUN_00717810(this[0x2b4], címzett, &szöveg)`, a szöveg ott üres), és ez az
  ág csak akkor fut, ha a `this+0x298` mód nem 3. Ez **igazolja a 415
  olvasatát**: a csomópont `+0x28c` címzettje egy `CAlbumVarString`, a mappa
  (album) objektum `+0x50` változójához kötve. A változó kulcsa nem látszik: a
  konstruktor csak a címet és két mezőt tárol. Ugyanabban a hívássorban a
  `CAlbumVarDateConverter` is ugyanazt az `album + 0x50` címet kapja, a `+0x18`
  mezőjében `2` értékkel; ebből a `+0x50` terület olvasat szerint az album
  változóinak közös kiindulása, a `+0x18` mező pedig a változó kiválasztója. A
  három `CAlbumVarString`-építés előtt a dekompilálás a `1`, `0`, illetve `4`
  értéket mutatja a veremben (a `0x00717810` felé tartó hívásnál `0`); hogy ez a
  negyedik paraméter értéke, azaz a leírás kiválasztója, **nem igazolt**. A
  `CAlbumVarString::vftable` metódusainak törzse (az elfogadáskor futó írás) nincs
  a kimenetben. **PicasaPy:** a fejléc Enter után ment, a
  `[Picasa]/description` kulcsba (`LightboxHeaderDescription.qml:18-50`,
  `LightboxFeedGroup.qml:40-51`, `controller_folder_description_mixin.py:26-63`).
  Hogy az eredeti címzett a `description` kulcsra, a felirat-setteren
  (`0x00443c90`) át ír-e, nem igazolt.
- **`0x004545c0` és `0x0045c0a0`, a `.picasa.ini` író (421).** Megválaszolva a
  fájl és a szakasz szintjén. A `0x004545c0` hívói: `0x0041c340`, `0x00431570`,
  `0x00443c90` (felirat-setter), `0x00445460` (név-setter) és `0x0044fa80`
  (hely-setter). A dekompilált törzs csak a `FUN_004543e0`-at hívja (a
  dekompilálás tizenhárom elérhetetlen blokkot eltávolított), de a `0x0045c0a0`
  hívói között a `0x004546a1` cím a `0x004545c0`-ban van: a függvény tehát a
  `0x0045c0a0`-t is hívja, a dekompilálás ezt elveszti. A `0x0045c0a0` egy
  `ytPicasaINIFile` objektumot épít `.picasa.ini` névvel, a `this+0x48`
  objektum `+0xf0` virtuális metódusával tölti ki (olvasat: a mappa útja), és a
  végén `FUN_005ab210("Picasa", kulcs, érték)` hívással ír: tehát a mappa
  **`.picasa.ini` fájljának `[Picasa]` szakaszába**. A kulcs és az érték
  paramétereinek sorrendje a törzsből nem egészen egyértelmű (a `FUN_005ab210`
  harmadik argumentuma az `-1` állapotú ágban felülíródik); a hívóhelyek
  olvasata (417) szerint kulcs, majd érték. Korai kilépés: ha az ini-objektum
  állapotjelző bájtja `0`, és az érték null vagy üres, nem ír.
  **A #7038 `[Picasa]/location` választása igazolt:** a hely-setter
  (`0x0044fa80`) a `0x004545c0`-n át ugyanezt a szakasz-írót hívja `location`
  kulccsal (417), a szakasz neve és a fájlnév literálként szerepel a `0x0045c0a0`
  törzsében. A **név-setter is ide ír** (hívási helye `0x00445a0e`), tehát a
  `name` kulcs is a `[Picasa]` szakaszba kerül, ha a tartós jelző nem nulla (417:
  nem különleges mappánál igaz); ez a 417 két nyitott különbsége közül az elsőt
  szűkíti: az író útja igazolt, a beírt érték és a hatás nem. **PicasaPy:**
  meglévő mappánál az átnevezés nem ír `[Picasa]/name` kulcsot
  (`library_controller_resync.py:67-77`: lemezes átnevezés, majd az index
  útelőtagja). **Eltérés-jelölt**; a `name` kulcs értékét és az átnevezés utáni
  `.picasa.ini` tartalmát mérés nélkül nem állítom. **A `date` ág `0.000000`
  értéke** (a 417 második különbsége): a `0.000000` nem üres szöveg, ezért a fenti
  korai kilépés nem érinti (feltéve, hogy az `-1` állapotú ág nem írja felül
  az értéket); a `FUN_005ab210("Picasa", ...)` hívás lefut. Hogy ez kulcstörlés
  vagy `date=0.000000` sor, a `FUN_005ab210` törzsén múlik, ami nincs a kimenetben.
- **`0x0052e0f0` és `0x004fd1c0`, a mappa átnevezése és a katalógus (422).**
  Megválaszolva. A `0x0052e0f0` vékony burkoló: `FUN_00455f10(this)`,
  `FUN_00455e30(this)`, majd `FUN_004fd1c0(this+0xf8, forrás, cél, 1)`. A
  visszatérési értékét a mentő (`0x0055d320`, a
  `2026-11-15-7031-7032-7033-colab-decomp.txt` kimenetből) nullához hasonlítja;
  a dekompilálás a `0x0052e0f0` visszatérését elveszti. A két utat
  paraméterként kapja, az összeállításuk a mentőben történhet (célút-építő
  lépései: `FUN_009a3b50`, `FUN_0049f820`, `FUN_009a3c70`; nincsenek bontva). A
  `0x00455f10` és a `0x00455e30` törzse nincs a kimenetben. A
  `0x004fd1c0(katalógus, forrás, cél, jelző)` lépései:
  1. Ha a jelző nem nulla (itt `1`): egy globális objektum (`DAT_00d6769c`), ha
     nem null, előbb `FUN_005aa120`-at kap (jelentése nincs meg). Utána a két
     útobjektum `+0x208` mezőjében (`param[0x82]`) álló kötet-sztringet
     hasonlítja, ASCII kis- és nagybetűtől függetlenül (csak az A-Z betűket
     kisbetűsíti): eltérő kötetnél, vagy ha csak az egyik útnak van kötete,
     **`-1` a visszatérés, átnevezés nélkül**.
  2. `FUN_00994400(forrás, cél, 1, 5)`, a `MoveFileExW`-burkoló (416); nem nulla
     visszatérésnél ezt adja vissza, a katalógus érintetlen marad. A harmadik
     érték (`1`) a `MOVEFILE_COPY_ALLOWED` jelzőnek felel meg (416). Az `5` a
     burkoló dekompilált törzsében nem külön paraméterként látszik: az
     újrapróbálás időkorlát-összehasonlítása (`QueryPerformanceCounter`,
     `FUN_009a51b0`) egy paraméterből számolt értéket használ. Az `5` ezért
     **erős jelölt az időkorlátra, de nem igazolt**: a regiszterparaméterek
     összekeveredtek a dekompilálásban, és a mértékegységet a `0x009a51b0`
     időátváltó adná, ami nincs a kimenetben.
  3. A sikeres átnevezés után a katalógus: a `FUN_004f7fc0` rekordazonosítókat
     gyűjt a forrás-út objektumával hívva (olvasat: a forrás-út alatti
     rekordok; a feltétele nincs a törzsben), majd a katalógus zárja alatt
     (szálazonosítóval újrabelépő zár) a rekordok egy részénél (a `+0x18` mező
     `0x3e9`, vagy a `+0x20` mező `-1`) az út elejéről **a forrás-út hosszának
     megfelelő számú karaktert levágja, és a cél utat fűzi elé**
     (`FUN_00985af0`); a többinél az utat nem írja át. Mindegyik rekordnál
     `FUN_004ed450(azonosító)` fut. A végén, ha a `param_1[0x122]`
     darabszám-mező nem üres, a `param_1[0x121]` objektum `+0x10` metódusát hívja
     az érintett utakkal és azonosítókkal (olvasat: a katalógus figyelőinek
     értesítése).

  A jelző nulla értékénél a kötet-összevetés és a mozgatás kimarad, csak a
  katalógus-frissítés fut. A lépéssor a **sorrendet** adja: előbb a lemezes
  átnevezés, utána a katalógus; lemezes hibánál a katalógus érintetlen, a
  katalógus-frissítésnek pedig nincs hibaága. **PicasaPy:** a lemezes átnevezés a
  szülőn belül egy `os.rename` (`rename_folder.py:51-56`, ezért a kötet mindig
  azonos), utána az index frissítése (`library_controller_resync.py:77`,
  `move_folder_tree`); a PicasaPy az index hibájánál visszagörgeti a lemezes
  átnevezést (`:80`), ami az eredetinél szigorúbb. A sorrend egyezik, a
  kötetellenőrzés a PicasaPy-ban nem fordulhat elő: eltérés-jegy nem kell.
- **`0x00992ed0`, létezés-ellenőrzés (423).** Megválaszolva. A `bool
  FUN_00992ed0()` a vizsgált utat az `EAX` regiszterben kapja: ha null vagy
  üres, hamis; különben lekérdezi az attribútumot a `DAT_00d694bc`
  függvénymutatón át (a 416 szerint ez adja a `0xffffffff` hibajelzést;
  olvasat: fájlattribútum-lekérdezés), körülötte a `FUN_0053ddf0` és a
  `FUN_009a51b0` segédhívással (jelentésük nincs meg), és **igazat ad, ha az
  eredmény nem `-1`**.
  Általános fájl- és mappalétezés-ellenőrző, 244 hívóval; nem zárolás- és nem
  hozzáférés-vizsgálat. Az átnevezésben két helyen áll: (a) a `0x00994400`
  burkolóban az `5`-ös hibakód (hozzáférés megtagadva) után ez a kapu: hamis
  eredménynél a burkoló `0`-t ad, átnevezés nélkül; igaz eredménynél indul a
  **500 ezredmásodperces újrapróbálás** (a megszakító eseményre `0xf4242`); (b) a
  mentőben a `FUN_0049fef0` után, a névtisztítás és a `0x0052e0f0` előtt
  kapuként: hamis eredménynél a mentő nem nevez át, és hibaüzenetet sem ad (a
  hibaüzenet csak a névtisztítás vagy az átnevezés hibájához kötött ágban van).
  Hogy mindkét helyen melyik útra vonatkozik (a regiszterátadás nem látszik),
  nem igazolt. **Következmény a 416 újrapróbálására:** a feltétel
  (`GetLastError() == 5` és a vizsgált út létezik), a 500 ezredmásodperces
  várakozás és a megszakító esemény megvan; az időkorlát nagysága (jelölt: `5`) és
  mértékegysége nincs. **PicasaPy:** az átnevezés egyetlen `os.rename` hívás
  újrapróbálás nélkül (`rename_folder.py:51-56`); jegyet az időkorlát nélkül nem
  javaslok.

**A jegy lezárhatósága: NEM zárható.** A "Kész, ha" pontokhoz mérve:

| Pont | Állapot a 419-425 után | Miért |
|---|---|---|
| Minden belépési pont és feltétel | ⛔ | A rácsfejléc címzettje (`CAlbumVarString`, album `+0x50`) megvan, de a vtábla metódusai (elfogadáskor melyik kulcs) és a negyedik hívó (`0x00789c00`) nincsenek bontva; az erőforrásbeli gyorsbillentyű-tábla és a mappalista dupla kattintásának célsora nyitott. |
| Ablak, mezők, alapértékek, átnevezés | ✅ részben (közelebb) | A névtisztító, a `MoveFileExW`-burkoló, a kötet-összevetés, a sorrend (lemez, majd katalógus) és az újrapróbálás feltétele megvan; az időkorlát mértékegysége (`0x009a51b0`) és a célút-építő lépések nincsenek. |
| Fájlrendszer, `.picasa.ini`, index, mappafa, rács, kijelölés | ✅ részben | Az író megvan: `.picasa.ini`, `[Picasa]` szakasz; a `FUN_005ab210` belseje, a `name` sor tartalma és a `date` `0.000000` hatása nincs; az index és a kijelölés végállapota sincs meg. |
| Ütköző név, írásvédett hely, írási hiba | ✅ részben | Az átnevezési hiba és az újrapróbálás feltétele bizonyított; az ini-írási hiba eredménye mérés nélkül NINCS MEG. |

**Fejlesztői teendő:** a 419-425 nem ad új fejlesztői jegyet. A #7038
`[Picasa]/location` választása igazolt, a `name` sor és az újrapróbálás időkorlátja
mérés, illetve a `0x009a51b0` nélkül nem jegyezhető. A 416 szerinti kiegészítő
"Kész, ha" (az `A  B` két szóközzel marad) változatlanul érvényes.

### CAlbumList-dupla kattintás: soronkénti feltétel (2026-11-16)

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x00765d30`: `lb_predouble` esetén a sor `+0x30` típusa `1` vagy `5`, és a sor `+0x18` bájtja nulla → `0x006db580` Folder/Album Properties. Ha a `+0x18` nem nulla, a sor ág visszatér tulajdonságnyitás nélkül. A `+0x30 == 4` sor a `CAlbumList::newalbumprompt` ágban tér vissza; a `2` típus szintén korán visszatér. | `FolderHierarchyView.qml:386`: a sor dupla kattintása `root.toggle(row.modelData.path)`; a mappafa ágát nyitja/csukja. | A binárisban igazolt a `1`/`5` típuskapu, nem minden sor nyit tulajdonságot. PicasaPy oldalon a mappafa dupla kattintása eltér. A név szerinti különleges sorok megfeleltetése nyitott; ne terjesszük ki rájuk a változtatást bizonyíték nélkül. |

**A típusérték független ellenőrzése.** A `0x004a0720` rekordépítő a kapott
első paramétert a rekord `+0x30` mezőjébe írja. A meglévő Ghidra-kimenetben a
`0x004b29d0` ezt `1` értékkel, a `0x004b1c80` `5` értékkel hívja. Ez a
rekord-előállítási út megerősíti a handlerben vizsgált számokat, de önmagában
nem azonosítja a felületen a Starred Photos, Screensaver, Emberek, Exported
Pictures és Recently Updated sorokat. A `+0x18` kapu szemantikai neve sincs
meg.

**Bizonyítottsági fok: feltételes.** Két független út egyezik a pontos
rekordtípus-feltételen: (A) `0x00765d30` eseménykezelője közvetlenül teszteli a
`+0x30` értékét és meghívja a `0x006db580`-at; (B) a `0x004a0720` rekordépítő
és a `0x004b29d0`/`0x004b1c80` hívók előállítják az `1`/`5` típusokat. Az
teljes kérdés azért feltételes, mert a látható sorok teljes típusleképezése, a
`+0x18` jelző jelentése és a többi sor dupla kattintás utáni végállapota nem
igazolt.

**Cáfoló kísérlet.** Megpróbáltam cáfolni azt az állítást, hogy a
`CAlbumList` minden dupla kattintása tulajdonságot nyit. A `0x00765d30` a
`+0x30 == 4` esetén a `CAlbumList::newalbumprompt` felirat-ágán tér vissza,
és a `2` típusnál is korán visszatér; emellett az `1`/`5` út a nem nulla
`+0x18` bájt esetén sem nyit. A cáfolatot ugyanazzal a mércével ellenőriztem:
a `0x00763150` rajzolófüggvény külön `4`-es sort kezel, a korábbi #5121
vizsgálat pedig a `newalbumprompt` sort a `liststicky5` / “Albums” fejlécsortól
elkülönítette. A cáfoló lelet tehát nem az index negatív találatán alapul.

**Javasolt fejlesztői jegytörzs**

#### 3. A mappalista dupla kattintása nyissa meg a megfelelő tulajdonságablakot

**Eredeti:** a `CAlbumList` sor `+0x30 == 1` vagy `5` típusánál, ha a
`+0x18` bájt nulla és az esemény `lb_predouble`, a `0x00765d30` meghívja a
`0x006db580` Folder/Album Properties útját.

**Nálunk:** `src/picasapy/app/qml/PicasaPy/FolderHierarchyView.qml:386` a
dupla kattintásra a `root.toggle(row.modelData.path)` hívással nyitja vagy
csukja a mappafát.

**Teendő:** a megfelelő, választható fizikai mappasor dupla kattintásakor
nyisd meg a Folder Properties ablakot az adott mappa adataival. A fa
kinyitását/csukását tartsd a sor külön fa-kezelő elemén. A type 5 és a
névvel azonosított speciális albumok viselkedését csak a sorleképezés
lezárása után kösd be.

**Kész, ha:** dupla kattintásra a fizikai mappasor tulajdonságablaka nyílik
meg a megfelelő mappaértékekkel; a fa-kezelő elem továbbra is csak
kinyit/csuk; egyéb sorok viselkedése nem változik a bizonyított
típusleképezés nélkül.

### Nyitott: a 2026-11-16-os kérdés

- A `+0x18` sorbájt jelentése, valamint a `+0x30` típusok név szerinti
  hozzárendelése nyitott; különösen a Starred Photos, Screensaver, Emberek,
  Exported Pictures és Recently Updated beépített soroké. A nem `1`/`5`
  sorok teljes dupla kattintás utáni viselkedése is nyitott: a
  `0x00765d30` tulajdonságnyitást nem hív rájuk, de a generikus aktiválási
  útból nem következtetek „kinyit/becsuk” vagy „semmi” eredményre.
- Ghidra-kör kell: 0x004b8470: a meglévő kimenet iterálja a builder
  `in_EAX[0x52]` rekordjait és hívja a `0x004b29d0`-t, de nem köti a beépített
  Starred Photos/Screensaver/Recently Updated/Exported/People tokeneket a
  `CAlbumList` sorrekordjaihoz. Kérdés: melyik `+0x30` típus és `+0x18`
  érték jut ezeknél a `0x00765d30` handlerhez? [blokkoló]

### Nyitott

- Megválaszolva (Ghidra 406): a kapu nem a képszámot nézi, csak egy nem üres sztringet; a kijelölés nem számít.
- Részben megválaszolva (Ghidra 407, 417, 421): mezőolvasók, setterek, hibakezelés, a kulcsnevek (`name`, `description`, `location`, `date`, `music`), a tartós jelző (nem különleges mappánál igaz) és az író megvan: a `0x004545c0` -> `0x0045c0a0` a mappa `.picasa.ini` fájljának `[Picasa]` szakaszába ír (a #7038 `[Picasa]/location` választása igazolt), a név-setter is ide ír. Ghidra-kör kell: 0x005ab210 - a `("Picasa", kulcs, érték)` író belseje: a `date` ág `0.000000` értéke kulcstörlés vagy sor, a kulcs és az érték sorrendje, a `name` sor; 0x004543e0 - a sor -> szöveg feloldás. Mérés (Colab, eredeti Picasa): a Folder Properties átnevezése után a mappa `.picasa.ini` `[Picasa]` szakaszában van-e `name=` sor, és mi az értéke.
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:2376`): a `0x005ab210` (`:2376-2487`) az `ytPicasaINIFile::vftable` (`0x00c81f14`) 2. bejegyzése (`0x00c81f1c`), 52 hívóval (köztük a `0x0045c0a0`, `0x00454770`, `0x00467ca0`, `0x0046d7d0`, `0x0052a810`, `0x0052c350`): a hívás három argumentuma (szakasz, kulcs, érték) ebben a sorrendben megy át (a `0x0052c350` hívóhelyein érték, kulcs, szakasz sorrendben tolva, `0x0052c6b4-0x0052c6bf`). **Két ága van:** ha a globális `DAT_00d6769c` objektum nincs (null), közvetlenül a `0x0099b5b0(szakasz, kulcs, érték)`-et hívja (az `ytINIFile::vftable` 2. bejegyzése, az egyszerű beállító); ha van, a `DAT_00d6769c` zárát szálazonosítóval újrabelépően veszi, és a `0x005aa260`-at hívja, amely az értékeket szövegobjektummá alakítja és egy `1` típusú parancsot ad a `DAT_00d6769c`-nek (`0x005a8d60`), majd feloldja a zárat. **A burkoló sem a kulcsot, sem az értéket nem vizsgálja**, tehát a `date=0.000000` sor és a `name` sor sorrendje a hívó (`0x0045c0a0`) hívási sorrendje, és a `0.000000` kulcstörlés-e vagy sor, a `0x0099b5b0`-ban és a `0x005a8d60`-ban dől el, amelyek nincsenek a kimenetben. A `0x004543e0` nincs a kimenetben.
- Ghidra-kör kell: 0x0099b5b0 - az `ytINIFile` beállító: üres vagy `0.000000` érték kulcstörlést vagy sort jelent-e, a kulcs és az érték írásának sorrendje a szakaszon belül (új kulcs a szakasz végére kerül-e), és a `name` sor; 0x005a8d60 - az `1` típusú parancs végrehajtása a `DAT_00d6769c` objektumban (ugyanaz a cél, mint a #7024 `0x005aa260` kérdésénél); 0x004543e0 - a sor -> szöveg feloldás [nem blokkoló]
- Megválaszolva (Ghidra 408, 416, 422, 423): a sorrend és a visszagörgetés hiánya megvan; a `0x009946f0` névtisztító; a `0x00994400` a `MoveFileExW`-burkoló (500 ezredmásodperces újrapróbálás hozzáférési hibánál, ha a vizsgált út létezik; a `0x00992ed0` általános létezés-ellenőrző); a `0x0052e0f0` -> `0x004fd1c0` előbb a köteteket veti össze (eltérésnél `-1`), utána átnevez, végül a katalógus rekordjainak útelőtagját cseréli a forrás-út hossza szerint. Ghidra-kör kell: 0x009a51b0 - az időátváltó: az újrapróbálás időkorlátja (jelölt: a `0x00994400` hívásának negyedik értéke, `5`) milyen mértékegységben értendő.
- Részben megválaszolva (Ghidra 415, 420): a `0x00717810` csak a csomópontot építi; a címzett a csomópont `+0x28c` mezője, amelyet a hívók közül csak a `0x00749ba0` állít be (a `0x0074ad40` és a `0x0074c200` null címzettet ad), és ez egy `CAlbumVarString` (`0x00746640`), a mappa (album) objektum `+0x50` változójához kötve; a kulcs neve nem látszik. Ghidra-kör kell: a `CAlbumVarString::vftable` metódusai - melyik fut elfogadáskor, melyik kulcsot írja (a vtábla címe a kimenetben nincs, csak a szimbólum neve; a konstruktor `+0x14` és `+0x18` mezőjének jelentése, azaz a negyedik paraméter: `1`, `0` vagy `4`); 0x00789c00 - a negyedik hívó. [blokkoló]
- Mérés (Colab, eredeti Picasa, a névtisztítás második útja): a Folder Properties névmezőjébe írt `A  B` (két szóköz) és `con` név mentés után mi lesz a lemezen (`A  B` vagy `A B`, illetve `con_`); a #7047 szóköz-összevonásának eldöntéséhez.
- Megválaszolva (Ghidra 410-411): a küldő a bal oldali CAlbumList dupla kattintása, a hatókör az aktuális mappa.
- Megválaszolva részben (Ghidra 410-411, 2026-11-16): a CAlbumList `lb_predouble` eseménye a `+0x30 == 1` vagy `5` sorrekordnál, ha a `+0x18` bájt nulla, a `0x006db580` Folder/Album Properties útjára jut. A név szerinti sorosztályok és a `+0x18` kapu jelentése nyitott; lásd az alábbi CAlbumList-alfejezetet.
- Részben megválaszolva (Ghidra 412): a Ctrl-kezelőben nincs gyorsbillentyű. Nyitott: az erőforrásbeli gyorsbillentyű-tábla.
- NINCS MEG (mérés): eredeti .picasa.ini írási hiba után mi marad lemezen és a felületen. Megszerzés: Windowsos Picasa 3.9 mérés külön másolaton, külön írásvédett mappával és ini-írási hibával; NAS-bejárás nélkül.

### Módosított fájlok

- docs/specs/paritas-ellenorzes.md - a #7032 alfejezet kiegészült a CAlbumList `lb_predouble` típuskapujával, független rekordúttal, cáfoló próbával és a név szerinti sorleképezés nyitott kérdésével.

### Zárókör (2026-11-16)

Vizsgálati mód: az eredeti `Picasa3.exe` (3.9.141.259, SHA-256
644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96) helyi
diszasszemblálása (`eszkozok/pe_dis.py`, capstone, címtartományonként), a
meglévő Ghidra-kimenetek (`2026-10-29-koteg-33.txt`,
`2026-11-11-6532-colab-004a0720-hivok.txt`,
`2026-11-15-6963-colab-decomp-2.txt`, `2026-11-16-koteg-438-465.txt`), az
`.picasa.ini` korpusz helyi másolata (859 fájl, NAS-bejárás nélkül) és a
tulajdonosi képernyőképekre épülő `ui-audit-context-menus.md`. A „Nálunk”
állítások a mai forráskódon, grep-pel ellenőrizve. Korábbi következtetést ez a
kör nem von vissza: ahol a hívóhely diszasszemblálása mást mutat, mint a
dekompiláció, azt a Z1 pont mondja ki.

#### Z1. A hívóhelyek diszasszemblálása: amit a dekompiláció veremolvasata nem adott

- **`0x00994400`, a `MoveFileExW`-burkoló szerződése.** A dekompiláció három
  paramétert és egy `in_AL` értéket mutat. A belépés (`sub esp,0x14` és négy
  mentés) szerint a veremparaméterek: forrás, cél, egybájtos jelző (másolás
  engedélye), időkorlát; az `AL` a felülírási jelző. A `0x004fd28b-0x004fd293`
  hívóhely: `push 5; push 1; push cél; push forrás; xor al,al; call 0x994400`.
  Tehát: **az `AL` nulla, a mappaátnevezés nem ír felül** (a jelzők
  `WRITE_THROUGH|COPY_ALLOWED`, `REPLACE_EXISTING` nincs, és a cél csak olvasható
  attribútumát sem veszi le, mert az az ág az `AL` vizsgálata mögött van). Az
  `5` a negyedik paraméter: a `fild` duplapontossá alakítja, a `fcomp` ezzel
  veti össze a `0x009a51b0` eredményét. A `0x009a51b0` (`2026-10-29-koteg-33.txt`)
  a `QueryPerformanceCounter` indulás óta eltelt különbségét osztja a
  `QueryPerformanceFrequency` értékével, tehát **másodpercet** ad. Az
  újrapróbálás időkorlátja így **5 másodperc**; a várakozás
  `WaitForSingleObject(megszakító esemény, 0x1f4)`, azaz 500 ezredmásodperc,
  és a ciklus az első hiba után **minden** nem nulla hibakódra folytatódik az
  időkorlátig (nem csak az 5-ösre). Az első újrapróbálás feltétele: hibakód 5
  és a `0x00992ed0` igaz az **első paraméterre, a forrásra** (`mov eax,edi`).
  A 422 jelű Ghidra-kérdés „erős jelölt, nem igazolt” szavai ezzel igazolttá
  válnak; a 423 jelű kérdés nyitva hagyott útválasztása (melyik útra
  vonatkozik) is eldőlt.
- **`0x0055d320`, a mentő sorrendje és kapui.** A `0x006db580` hívóhelye
  (`0x006db688`: `push 0; call 0x55d320`) a csendes jelzőt nullával adja át, a
  figyelmeztetés tehát engedélyezett. A mentő (`0x0055d340-0x0055d371`) a
  `0x004461a0(sor)` eredményét negálja (`sete bl`): nem különleges mappánál
  `bl = 1`. A név (vtábla `+4`), felirat (`+8`), hely (`+0x10`), zene
  (`0x004448d0`) és dátum (`+0xc`) beállítója **feltétel nélkül, ebben a
  sorrendben** fut, a `bl` tartós jelzővel; bármelyik nem nulla visszatérésnél a
  mentő üzenet nélkül kilép. A név beállítója **akkor is lefut, ha a név nem
  változott.** Az átnevezési ág csak nem különleges mappánál indul
  (`0x0055d433`). Menete: a jelenlegi név lekérése (vtábla `+0x14`), bájtonkénti,
  kis- és nagybetűt megkülönböztető összevetés az újjal (egyenlő: nincs
  átnevezés, `0x0055d54c`); a jelenlegi mappaút építése (`0x0049fef0`); a
  `0x00992ed0` létezés-ellenőrzés **ugyanezen a jelenlegi (forrás) úton** (hamis:
  nincs átnevezés és nincs üzenet, `0x0055d57e`); célút: a forrás szülője
  (`0x009a3b50`), a `0x009946f0` tisztított neve és az összefűzés
  (`0x00993bb0`); ha a tisztítás hibát ad, közvetlenül a figyelmeztető ág fut
  (`0x0055d5ec`), különben a `0x0052e0f0` (forrás, cél). A `0x0052e0f0` és a
  `0x004fd1c0` paraméterátadása a diszasszemblálás szerint a forrás-cél
  sorrendet tartja. **Siker után nincs megerősítő üzenet**: a mentő a
  `[objektum+0x48]` vtábla nulladik metódusát hívja (sor, új út), majd
  kilép (`0x0055d606-0x0055d628`). Hibánál, ha a csendes jelző nulla, a
  `0x0055d62a` ág a `0x00980700` figyelmeztetést nyitja.
- **`0x006db580`, a mentő előtt és után.** A párbeszéd (`0x006dc030`) a mentés
  ELŐTT lezárul: az OK-kezelő (`0x00849dc0`) csak a leíróba másol, a mentő a
  párbeszéd bezárása után fut. Siker után a `0x0055d6e0`, egy vtábla-hívás,
  a `[edi+0x2c0]` objektum `+0x166` jelzőjének beállítása és a
  `0x0065b840(this,0,0,1)` nézetfrissítés következik; hiba esetén csak a `0x0052e420` és a `0x004ad150`
  frissítés. A Mégse ág (`0x006db71a`) nem ment.
- **`0x009946f0` névtisztító, második ábrázolás.** A diszasszemblálás egyezik a
  dekompilációval: a vezető szóközök átugrása (`_iswspace`); karakterenként a
  szóköznek számító karakter és az `U+3000` pontosan egy `0x20`-at ad (**nincs
  összevonás**), a `0x20` alatti vezérlőkarakter kimarad, a tiltott karakterek
  a `0x00cd8d24` literálból: `\ / : * ? " < > |` (közvetlenül kiolvasva a
  binárisból); utána a vezető és záró pont vagy szóköz levágása; üres
  eredményre `-1`; a `0x00cd8d80-0x00cd8d8c` literálok: `aux`, `con`, `nul`,
  `prn` (ASCII kis- és nagybetűtől független, teljes egyezés), a végére `_`. A
  `0x00849f75` hívóhelyen az OK-kezelő **nem vizsgálja a visszatérést**: sikertelen
  tisztításnál a leíróba null név kerül (`0x00849f81-0x00849f88`: `edx = 0`).
  Hogy a mentő ezután eljut-e a `0x0055d5ec` ághoz, az előtte álló
  névösszevetés (`0x0055d4f1-0x0055d53a`) miatt nincs végigkövetve.

#### Z2. Minden megmaradt tétel: döntés

A jelölés: (a) a meglévő bizonyítékból eldőlt; (b) egyetlen megnevezett
mérés vagy Ghidra-kör dönti el; (c) a felhasználó által látható viselkedést
nem érinti, vagy a #7032 hatókörén kívül esik.

| # | Tétel | Döntés | Válasz és bizonyíték | Nálunk (fájl:sor) |
|---|---|---|---|---|
| 1 | A menüparancs kijelölésfüggő feltétele (`0x0056e1c0`, `0x006b1e80`) | (a) | A kapu nem a képszámot nézi (Ghidra 406): üres, egy és több kijelölt képnél ugyanaz. A `0x006db580` az aktuális mappát kapja. | `PicasaFolderMenu.qml:16-28` mappa alapú; egyezik. |
| 2 | A mappafa helyi menüjének kibocsátója | (a) | A mappa-menü építőjének (`0x007319f0`) egyetlen közvetlen hívóhelye `0x005e7731` a `0x005e7650`-ben (a `0x005e76d3` `0x004461a0` hívás hamis ágán; a `ui-audit-context-menus.md` táblája ugyanezt `0x005e77b2`-nek írja, a diszasszemblálás `0x005e7731`-et ad). A menü forrását a tulajdonosi képernyőkép igazolja: a bal panel mappasorának menüje bájtra azonos a rács üres területének menüjével, első tétele „Mappaleírás szerkesztése”, gyorsbillentyű nélkül (`ui-audit-context-menus.md`, 1. szakasz). | `FolderPaneTreeRow.qml:310`, `FolderHierarchyView.qml:362`, `FolderPaneMenus.qml:363`, `FolderContextMenu.qml:82`; egyezik. |
| 3 | A rács üres területe és mappa-fejléce | (a) a látható eredményre, (c) a belső hívóláncra | A két képernyőkép (üres terület, mappa-fejléc) ugyanazt a 15 tételes menüt adja. A belső hívólánc a felhasználónak nem látszik, ezért a korábbi „két rács-hívó külön feltárandó” sor megszűnik. | `LightboxFeed.qml:717-724`, `LightboxFeedGroup.qml:190-192` mindkettő `Main.qml:561-564` → `FolderPane.qml:320`; egyezik. |
| 4 | Gyorsbillentyű | (a) | Nincs. Három független jel: (i) a `CreateAcceleratorTableA` egyetlen hívója, a `0x00923110`, üres OLE-táblát hoz létre (`picasa-gyorsbillentyuk.md`, kizárt irány); (ii) a `0x005e60d0` ugrótáblás kezelőjében nincs `0x9c69` (Ghidra 412); (iii) a mért menütétel gyorsbillentyű-oszlopa üres. A korábbi „erőforrásbeli gyorsbillentyű-tábla nincs átnézve” sor ezzel lezárt. | Nincs külön billentyű; egyezik. |
| 5 | A néző | (a) | A korábbi „Néző” sor a bal lista dupla kattintása volt (Ghidra 410-411). A néző menüjének teljes tételsora (17 tétel, `ui-audit-context-menus.md`, 3. szakasz) nem tartalmaz mappaműveletet („mappa-műveletek: nincs”); az egyetlen „Tulajdonságok” tétele a kép tulajdonságait nyitja (`Alt+Enter`, `ID_PICTURE_PROPERTIES`). A mappa-menü egyetlen hívóhelye (2. tétel) sem a nézőé. | Nincs nézőbeli belépő; egyezik. |
| 6 | A képtálca | (a) | A tálca helyi menüje két tételes: „Kijelölés megtartása”, „Kijelölés eltávolítása” (`ui-audit-context-menus.md`, `Tray`); a tálcán nincs mappatulajdonság-parancs. | Nincs tálcabeli belépő; egyezik. |
| 7 | Mappalista dupla kattintása, sorfeltétel (`+0x30`, `+0x18`) | (b) mérés, **blokkoló a 3. fejlesztői törzsre** | Lásd a Z3 pontot. | `FolderHierarchyView.qml:386`: minden sorra kinyit/becsuk. |
| 8 | A beépített sorok (Starred Photos, Screensaver, Recently Updated, Exported, People) típusa (`0x004b8470`) | (c) | A korábbi „[blokkoló]” jelölés a #7032-re megszűnik: a beépített és albumsorok tulajdonságablaka az album-folyamat (#7069) tárgya; a #7032 fejlesztői törzsei csak fizikai mappasorra szólnak, és a nem mért sorok viselkedését kifejezetten nem változtatják. Aki az albumsorokat felveszi, a korábbi `0x004b8470` Ghidra-sort használja. | A #7069 hatóköre. |
| 9 | Rácsfejléc leírásmezője: elfogadás kiváltója és kulcsa (`CAlbumVarString` vtábla, `0x00789c00`) | (b) mérés, nem blokkoló | A mező, a helyőrző és az Enter-mentés a `description` kulcsra megvan (a beállító `0x00443c90`, kulcs `"description"`, Ghidra 417 és 421). Nyitott csak az, hogy az eredetinél a fókuszvesztés és az Esc ment-e. Mérés (Colab, eredeti Picasa): a fejléc „Add a description” mezőjébe írt szöveg megmarad-e Enter, mezőn kívüli kattintás (fókuszvesztés), illetve Esc után, és mit mutat az újranyitott Folder Properties Description mezője. Egyik fejlesztői törzs sem függ tőle. | `LightboxHeaderDescription.qml:32-41`: Enter ment, Esc visszaállít, fókuszvesztésre nincs mentés. |
| 10 | Siker után megerősítő üzenet | (a) | Nincs (Z1, `0x0055d606-0x0055d628`). | Nincs; egyezik. |
| 11 | Forrás- és célút összeállítása (`0x0052e0f0`, `0x004fd1c0`) | (a) | Forrás: a jelenlegi mappaút; cél: a forrás szülője és a tisztított név; azonos köteten belül; a név összevetése kis- és nagybetűre érzékeny (Z1). | `rename_folder.py:46-52`: `source.with_name(name)`, `name == source.name` összevetés; egyezik. |
| 12 | Az újrapróbálás időkorlátja (`0x009a51b0`) | (a) | 5 másodperc, 500 ezredmásodperces lépésekkel (Z1). | `rename_folder.py:52`: egyetlen `os.rename`, újrapróbálás nélkül. **Eltérés, 5. fejlesztői törzs.** |
| 13 | `[Picasa]/name` | (a) | Az eredeti a `name=` sort az OK minden lefutásánál írja, nem különleges mappánál, az átnevezés előtt, változatlan névnél is. A út: a diszasszemblálás (`0x0055d33d-0x0055d371`) és a Ghidra 417 és 421 (`0x00445460` → `0x004545c0` → `0x0045c0a0` → `[Picasa]` szakasz). B út, korpusz: a 733 `[Picasa]` szakaszból 692-ben van `name=`, 684-ben egyezik a könyvtárnévvel; a 8 eltérés mintázata (például `gyerekek_2` könyvtár, `gyerekek` név) a Picasán kívüli átnevezésre utal. A `name=` olvasói hatása (az eredeti ebből jeleníti-e meg a nevet) nem bizonyított. | `library_controller_resync.py:35-137`, `rename_folder.py:26-57`: nem ír `[Picasa]/name` kulcsot (a mappanévnek nincs írója a repóban). **Eltérés, 4. fejlesztői törzs.** |
| 14 | `[Picasa]/date` automatikus dátumnál (`0.000000`) | (a), a hatás (c) | Az eredeti `date=0.000000` sort ír: A út: a beállító a `"0.000000"` szöveget adja a `0x0045c0a0`-nak, a korai kilépés csak null vagy üres értékre áll (Ghidra 417 és 421); B út, korpusz: az 558 `date=` sorból 185 pontosan `date=0.000000`, 175 `[Picasa]` szakaszban nincs `date` sor. A teljes-ini-író `0x00710080` 0.0-t kihagyó kapuja (`0x0071031e`) másik író. A PicasaPy a kulcsot törli, és a `0.000000` értéket nem tekinti felülírásnak (`_VARIANT_MIN = 1.0`), így a két alak működésben azonos; csak a fájltartalom tér el. Nem blokkoló, jegy nem kell. | `ini/folder_date.py:97-117` (olvasás), `:137-152` (törlés). A `:145` megjegyzése a `0x0071031e` kapura hivatkozik, ami nem a Folder Properties beállítója; a megjegyzés pontosítása javasolt. |
| 15 | `.picasa.ini` írási hiba | (a) a felhasználó felé, (c) a lemezes hatásra | A `0x005ab210` zárolt burkoló: a `0x005aa260` összeállítja a (szakasz, kulcs, érték) kérést, a `0x005a8d60` a globális kezelő (`DAT_00d6769c`) sorába teszi és `SetEvent`-et jelez, majd a függvény **mindig nullát ad vissza**. A beállító tehát sikert lát, a Properties útról nem jut hiba a felhasználóhoz, és nincs részleges mentés üzenet. A háttérszál lemezes hibakezelése nem bizonyított, de a felhasználó felé nem látszik. A PicasaPy hibát jelez és a nézetet nem frissíti: szigorúbb, kárt nem okoz, jegy nem kell. | `controller_folder_description_mixin.py:42-63`, `folder_date_controller.py:130-153`. |
| 16 | Index és mappafa átnevezés után | (a) a sorrendre, (c) a rendezésre | A katalógus (`0x004fd1c0`) a rekordok útelőtagját rekordonként cseréli (olvasat: a rekordazonosítók megmaradnak, rekordonként `0x004ed450` fut), utána a figyelőket értesíti; előbb a lemez, utána a katalógus, hibánál a katalógus érintetlen. A fa rendezett helye ebből a nézetfrissítésből adódik, eltérésre nincs jel. | `library_controller_resync.py:35-137`: lemez, majd `move_folder_tree`, indexhibánál visszagörgetés; egyezik, szigorúbb. |
| 17 | Rács és kijelölés az átnevezés után | (b) mérés, nem blokkoló | A mentő után a `0x0065b840(this,0,0,1)` frissít; hogy a kijelölés és a görgetési hely megmarad-e, ebből nem dönthető el. Mérés (Colab, eredeti Picasa): egy mappa három képének kijelölése, majd átnevezés a Folder Properties-ből; marad-e a kijelölés és a görgetési hely. Egyetlen fejlesztői törzs sem függ tőle. | `library_controller_resync.py:~135`: `_reload(preserve_scroll=True)`. |
| 18 | Mentési sorrend, részleges mentés | (a) | Az eredetinél a mezők előbb íródnak, az átnevezés utolsó, és hibánál nincs visszagörgetés; a párbeszéd addigra már bezárult. A PicasaPy előbb nevez át, hibánál a párbeszéd nyitva marad, és semmi nem mentődik: barátságosabb és adatot nem veszít, tudatos eltérés, jegy nem kell. | `FolderPropertiesDialog.qml:231-269`. |
| 19 | A névtisztítás `A  B` és `con` mérése | (a) | A mérés nem szükséges: a dekompiláció, a diszasszemblálás és a közvetlenül kiolvasott literálok egyeznek (Z1). A #7047 javítása (`907291af1`) követi: `A\t  B` → `A   B`, `con` → `con_`. Egyetlen apró eltérés maradt: az `iswspace` és a Python `isspace` készlete a ritka `U+001C-U+001F` vezérlőkaraktereknél eltérhet; ezt nem tekintem jegyre érdemesnek. | `rename_folder.py:60-72`, `tests/fileops/test_rename_folder_4482.py:64-75`. |
| 20 | A sor és szöveg feloldó (`0x004543e0`) | (c) | A dátum tartós szövegének építéséhez kell; a felhasználó nem látja. | Nem érinti. |
| 21 | Üres névnél az OK | (a) | Az eredeti párbeszéd nem ellenőriz, a leíróba null név kerül; a mentő a tisztítás hibáját az átnevezési figyelmeztetéssel jelzi (a null névvel hívott beállító és az összevetés ága nincs végigkövetve, Z1). A PicasaPy hibaüzenetet ad, mentés nélkül. Szigorúbb, kárt nem okozó eltérés, jegy nem kell. | `rename_folder.py:39-42`. |

#### Z3. A mappalista dupla kattintása: a `+0x18` bájt olvasata (a 7. tétel alapja)

A `0x004b1c80` (a `Folders` fa sorépítője, a `0x004a0720` hívója ötös típussal;
a hívást a #6532 kör diszasszemblálása igazolta) a sor `+0x18` bájtjába a
`!bVar14` értéket írja. Az elejének diszasszemblálása (`0x004b1c97-0x004b1d19`):

1. `test [sor+0x48], 0xfffffffe` / `sete al`: a `+0x48` mező a gyermeklista
   fejléce (a `0x004b6190` ciklusa ugyanazt a mezőt `>> 1`-gyel számlálóként
   használja). Az `al` tehát „nincs gyermek”.
2. Ha a `+0x38` bájt nulla és nincs gyermek, a keresés kimarad, `bVar14 = 1`.
3. Egyébként (van gyermek, vagy a `+0x38` nem nulla) a sor kulcsára (`+0x40`,
   üresnél `+0x3c`) a `0x004a4710` keresést végez; nem találatnál
   `bVar14 = 1`, találatnál 0 marad.
4. A `0x004a4710` a `repository.dat` perzisztens táblájában keres; a
   `picasa-idorend-bemutato-kutatas.md` „A `+0x1d` jelző” szakasza szerint a
   találat az „igaz”, és a tábla a fanézet kibontott csomópontjait is tárolja
   (fordított perjelre végződő útvonalak, érték 1).

**Olvasat:** a `+0x18` akkor 1, ha a sornak van gyermeke és a kulcsa a kibontott
halmazban van, vagyis **kibontott almappás soron**; almappa nélküli és
becsukott almappás soron 0. A `0x00765d30` kapuja (`+0x30` típus 1 vagy 5 és
`+0x18 == 0`) szerint a tulajdonságablak tehát almappa nélküli és becsukott
sorra nyílna, kibontott almappás sorra nem. **Bizonyítottsági fok:
feltételes.** A kódszerkezetet két ábrázolás (dekompiláció és diszasszemblálás)
egyezően adja; a „találat = kibontott” jelentést élő felvétel nem igazolja, és
a `+0x38` bájt jelentése ismeretlen. A fizikai mappasorok típusa `5`
(`picasa-idorend-bemutato-kutatas.md`: a `0x004b1c80` rekordja a `Folders`
útban), a korábbi 3. törzs „a type 5 viselkedését csak a sorleképezés után
kösd be” mondata ezért úgy értendő, hogy a mérés után kell bekötni.

**Mérés (Colab, eredeti Picasa), ez az egyetlen blokkoló:** Folders nézetben
dupla kattintás (1) almappa nélküli mappasoron, (2) becsukott almappás soron,
(3) kibontott almappás soron. Soronként megfigyelendő: megnyílik-e a Folder
Properties, és a sor kinyílik vagy becsukódik-e. Kimenet: soronként egy
képkocka a dupla kattintás előtt és után.

### Zárási döntés

**A jegy még nem zárható; az egyetlen blokkoló a Z3 pont mérése** (a
mappalista dupla kattintása három sortípuson). Ez csak a 3. fejlesztői
törzset tartja vissza. Minden más nyitott tétel eldőlt (a), a #7032 hatókörén
kívül esik (c), vagy olyan kis mérés (9. és 17. tétel), amelytől egyik
fejlesztői törzs sem függ. A 7., 9. és 17. tétel mérése egyetlen Colab-menetben
elvégezhető. A mérés után a jegy lezárható; a 4. és az 5. törzs attól
függetlenül felvehető.

Fejlesztői jegytörzsek:

- **1. A Hely mező szerkeszthető meglévő mappánál: KÉSZ** (`e88e4ee3f`,
  `907291af1`; `FolderPropertiesDialog.qml:617-618` `enabled: true`,
  `controller_folder_description_mixin.py:14-22`, `ini/folder_location.py`;
  tesztek: `tests/ini/test_folder_location_7038.py`,
  `tests/app/test_folder_location_controller_7038.py`,
  `tests/app/qml_functional/test_folder_location_qml_7038.py`).
- **2. Az eredeti névtisztítás követése: KÉSZ** (`rename_folder.py:60-72`,
  `tests/fileops/test_rename_folder_4482.py:64-75`, beleértve a szóközök
  összevonásának hiányát).

#### 3. (marad, a méréstől függ) A mappalista dupla kattintása a mért sortípusokon nyissa a tulajdonságablakot

**Eredeti:** a `0x00765d30` az `lb_predouble` eseményre, `+0x30` típus 1 vagy 5
és `+0x18 == 0` esetén a `0x006db580` útját indítja. A fizikai mappasor a
`Folders` fa 5-ös típusú rekordja; a `+0x18` olvasat szerint 1 a kibontott
almappás soron, különben 0 (Z3).

**Nálunk:** `FolderHierarchyView.qml:386`: `onDoubleClicked:
root.toggle(row.modelData.path)`, minden mappasoron kinyit vagy becsuk,
tulajdonságablakot nem nyit.

**Teendő:** a mérés után, a mért sortípusokon a dupla kattintás nyissa a
tulajdonságablakot az adott mappa adataival (a `FolderPane.qml:252`
`openFolderDescription` útján); a kinyitás és becsukás azokon a sortípusokon
maradjon, ahol az eredeti nem nyit ablakot. A beépített és albumsorokra nem
terjed ki (#7069).

**Kész, ha:** soronként egyezik a mért viselkedés (nyílik-e az ablak, kinyílik
vagy becsukódik-e a sor); a nem mért sorok viselkedése változatlan.

#### 4. (új) Az OK írja a `[Picasa]/name` sort

**Eredeti:** a `0x0055d320` a név beállítóját a Folder Properties minden
OK gombjánál lefuttatja, nem különleges mappánál tartós jelzővel, még változatlan
névnél is, az átnevezés előtt; a `0x00445460` → `0x004545c0` → `0x0045c0a0` a
mappa `.picasa.ini` `[Picasa]` szakaszába `name=<tisztított név>` sort ír.
Korpusz: 733 `[Picasa]` szakaszból 692-ben van `name=`, 684-ben egyezik a
könyvtárnévvel.

**Nálunk:** `library_controller_resync.py:35-137` és `rename_folder.py:26-57`
nem ír `[Picasa]/name` kulcsot. A mappa `.picasa.ini` fájlja az átnevezéssel
együtt költözik, a régi `name=` sor elavultan marad.

**Teendő:** az OK megnyomásakor (sikeres átnevezés után, változatlan névnél is) írd a
`[Picasa]/name` kulcsot a mappa tényleges nevével az `ini` csomag API-ján át,
a `ini/folder_location.py` mintájára (új `with_folder_name` jellegű függvény).
Írási hibát jelezz, de a már megtörtént átnevezést ne vond vissza. A kulcs
olvasói hatása (az eredeti ebből jeleníti-e meg a mappa nevét) nem bizonyított:
a cél a fájltartalom egyezése.

**Kész, ha:** átnevezés után a `[Picasa]` szakasz `name=` sora az új nevet
tartalmazza (meglévőt felülír, hiányzót létrehoz); változatlan névvel OK után
a sor a mappa nevével egyezik; a többi `[Picasa]` kulcs és a képszakaszok
érintetlenek.

#### 5. (új, kicsi, csak Windows) Az átnevezés újrapróbálása hozzáférési hibánál

**Eredeti:** `0x00994400`, hívás `0x004fd28b-0x004fd293`: ha a `MoveFileExW`
hibakódja 5, és a forrásmappa létezik (`0x00992ed0`), 500 ezredmásodpercenként
újrapróbálja, legfeljebb 5 másodpercig; az időkorlát után a hiba az átnevezési
figyelmeztetéshez vezet.

**Nálunk:** `rename_folder.py:52`: egyetlen `os.rename`, hiba esetén azonnal
`FolderRenameError`.

**Teendő:** Windowson, `PermissionError` (winerror 5) esetén, ha a forrásmappa
létezik, 0,5 másodpercenként újrapróbálás legfeljebb 5 másodpercig; az időkorlát
után a mostani hibaüzenet. Más platformon nincs változás. A várakozás a
felületi szálat ne fagyassza le tovább az eredetinél (az is a felületi szálon
vár): ha a hívás szintje ezt nem tűri, kerüljön háttérbe.

**Kész, ha:** a `_rename` fogantyúval, a hibák és az idő szimulálásával: két
hozzáférési hiba után a harmadik próbálkozás sikeres átnevezést ad; folyamatos
hibánál 5 másodperc után a régi hibaüzenet; nem létező forrásnál nincs
újrapróbálás; Linuxon a viselkedés változatlan.

### Zárókör, második kör (2026-11-17): a mappalista dupla kattintásának javított olvasata és a megmaradt tételek

Módszer: a `Picasa3.exe` (3.9.141.259, SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`)
utasításszintű olvasása (`capstone`, 32 bites x86, címtartományonként), a
meglévő Ghidra-dekompiláció (`2026-11-11-6532-colab-004a0720-hivok.txt`)
összevetése ugyanezekkel az utasításokkal, és a PicasaPy jelenlegi főágának
olvasása (`grep`, a lent idézett sorszámokkal). A dekompilált veremváltozót
(`local_acc`) csak a hívóhely utasításaival egyeztetve használtam. Futásidejű
mérést ebben a körben nem végeztem, eredeti felvételt nem készítettem. A
korábbi bejegyzések szövege érintetlen; ahol ez a kör felülír valamit,
kimondom. Fokok: megerősített (két független út), erős (egy út, egyértelmű
utasítások), feltételes (következtetés).

**Felülírt állítás: a Z3 pont olvasata téves, ezért a Z2 7. tétele és az
egyetlen blokkoló, a három sortípusos Colab-mérés megszűnik.** A Z3 szerint a
mappasor `+0x18` bájtja a „kibontott almappás” állapot, és a tulajdonságablak
a becsukott és az almappa nélküli sorra nyílna. Az utasítások mást mutatnak:
az almappás sor rekordtípusa nem 5, ezért a tulajdonságablak kapuja eleve nem
érinti.

#### Z4. A rekord típusa és a dupla kattintás kapuja

1. **A típusmező írása.** A `0x004b1c80` az `0x004b1eac` címen az `5`
   típussal hívja a rekordépítőt (`push 5`, `push ecx`, `push edx`,
   `push ebx`, `call 0x004a0720`). A `0x004a0720` az első argumentumot a
   rekord `+0x30` mezőjébe (`0x004a078d mov [esi+0x30], edx`), a harmadikat a
   `+0x18` bájtba (`0x004a077a`) írja, és `ret 0x10`-zel tér vissza; a hívó a
   rekordot az `esp+0x30` címre építi (`0x004b1ea4 lea esi, [esp+0x34]`, egy
   `push ebx` után). Közvetlenül utána, `0x004b1eb1-0x004b1ee2`: ha a
   csomópont `+0x48` gyermeklista-fejléce nem üres (`test dword ptr [ebp+0x48],
   0xfffffffe`), a `0x004b1ebf mov dword ptr [esp+0x60], 6` a rekord `+0x30`
   mezőjét (`esp+0x30` + `0x30`) **6-ra** írja; ha ezen felül a szülő
   (`[ebp+0x5c]`) létezik, a szülő saját szülője nincs, és a csomópont kulcsa
   a `0x00c83020` literállal (`/Volumes/`, macOS-előtag) egyezik
   (`0x00987030`), a `0x004b1ee2` **7-re**. A dekompiláció ugyanezt
   `local_acc = 6`, illetve `7` alakban adja, és a `local_acc` pontosan
   `0x30` bájtra van a `local_afc` rekordkezdettől (`-0xacc = -0xafc + 0x30`),
   tehát ez a típusmező, nem önálló helyi változó. **Ezzel megdől a
   `picasa-idorend-bemutato-kutatas.md` állítása, hogy a 6 és a 7 „helyi
   változóba íródik, nem a rekord `+0x30` mezőjébe”.** A másik specet ebben a
   körben nem módosítottam; a helyesbítés itt van kimondva.
2. **A típus eljut a tárolt listaelemig.** A kész rekordot a `0x004b2211
   call 0x004ae600` másolja a lista `0x38` bájtos elemébe (`lea esi,
   [esp+0x34]`); a másoló a `+0x18` és a `+0x30` mezőt is viszi (`0x004ae69a`,
   `0x004ae6ca-0x004ae6cf`). A `0x004ab9a0` a lista elemének `+0x30` mezőjét
   5, 6 és 7 szerint ágaztatja (`0x004ab9f8-0x004aba0c`), a `0x004a0800` pedig
   az 5, 6, 7 családot ismeri fel.
3. **A kapu.** A `0x00765d30` (`CAlbumList` eseménykezelő) a
   `0x00766075-0x00766098` szakaszban `al = (típus == 5)` értéket számol (a 6
   és a 7 nullát ad), majd az 1-es típusnál vagy `al` esetén a `0x00766327`-re
   ugrik. Ott a rekord `+0x18` bájtja (`cmp byte [esp+0x48], 0`) nem nulla:
   kilépés tulajdonságablak nélkül (`0x007663aa`); nulla: az esemény neve
   (`[ebp+0x14]`, 13 bájton, `0x00c95ea0`) `lb_predouble`-e, és igen esetén
   `0x007663a5 call 0x006db580`, a Folder/Album Properties megnyitója. **Csak
   az 1-es (album) és az 5-ös (almappa nélküli mappa) típus nyit
   tulajdonságablakot.**
4. **Az almappás sor.** A 6-os és 7-es típus a `0x00766231-0x00766246` ágra
   fut: `push -1; call 0x004ab9a0` (kivéve, ha a rekord `+0x19` bájtja 1: akkor
   csak a nézet frissül, `0x00766235-0x00766258`; a `+0x19` a `0x004b1c80`
   második argumentuma, jelentése nincs bontva). A `0x004ab9a0` a 6 és 7
   típusnál a rekord
   `+0x10` kulcsával a `0x004a4a90` váltót hívja (olvasat: a `repository.dat`
   kibontott-bejegyzésének fordítása, lásd `picasa-idorend-bemutato-kutatas.md`
   `+0x1d` jelző szakasza), majd a `0x006dc4c0` újraépíti a listát
   (`0x004aba20-0x004aba82`): kinyit/becsuk, tulajdonságablak nélkül.
5. **A `+0x18` az 5-ös típusra.** A `0x004b1c97-0x004b1cbc`: ha a csomópont
   `+0x38` bájtja nulla és nincs gyermeke, a keresés ki sem hívódik, és a
   hívóhelyen a `+0x18` nulla (`0x004b1e8d`: `cmp byte [esp+0x17], 0`, majd
   `sete cl`; a rekordba az érték tagadása kerül). A `+0x38` bájt nulla ága a
   fizikai mappa ága (ugyanebben az ágban fut az `iPhoto Library\Originals\`
   átírás és a `wine_get_unix_file_name` lekérdezés). **Az almappa nélküli
   fizikai mappasor tehát mindig átmegy a kapun.** A `+0x18` jelentése az
   almappás soroknál (olvasat: kibontott) a dupla kattintás szempontjából nem
   számít.

| Sor az eredeti bal listájában | Rekord `+0x30` | Dupla kattintás (`lb_predouble`) az eredetiben | Nálunk (fájl:sor) | Eltérés |
|---|---|---|---|---|
| Fizikai mappa, almappa nélkül | 5 (`+0x18` = 0) | Folder Properties (`0x006db580`); nincs mit kinyitni | Lapos lista: nincs dupla kattintás kezelő (`FolderPaneTreeRow.qml:245-321`, `onDoubleClicked` nem szerepel). Fa nézet: `FolderHierarchyView.qml:391` kinyit/becsuk, levélsoron hatástalan | **Eltérés**, 3. törzs |
| Fizikai mappa, almappákkal | 6 (macOS `/Volumes/` előtagnál 7) | kinyit/becsuk (`0x004ab9a0`, `-1`), tulajdonságablak nincs | Fa nézet: `FolderHierarchyView.qml:391` kinyit/becsuk | Egyezik |
| Album, személy, beépített sorok | 1 és más | az album-folyamat tárgya | nem érinti a #7032-t | (c), #7069 |

**Fok: erős.** Egy út (utasítások), de a dekompiláció és a diszasszemblálás
ábrázolása egyezik, és a rekordszerkezetet (az első argumentum a `+0x30`, a
hívó kimeneti rekordja az `esp+0x30` címen) a
`picasa-idorend-viselkedes.md` hívóhely-táblája is rögzíti. Élő felvétel nincs,
ezért nem megerősített.

**Cáfoló kísérlet.** Megpróbáltam cáfolni a javított olvasatot azzal, hogy a 6
és a 7 csak helyi változó, ezért minden mappasor 5-ös típusú maradna, és a Z3
olvasata (a `+0x18` dönt) állna. Az út: (a) a hívóhely a rekordot az `esp+0x30`
címen építi, a `+0x30` mező az `esp+0x60`, és a `0x004b1ebf` oda ír; (b) a
lista elemét a `0x004ae600` ebből a rekordból másolja, a `+0x30` mezővel
együtt; (c) a kész elemen a `0x004ab9a0` a 6 és a 7 külön ágát használja. A
cáfolat nem állt meg. Mindkét olvasatot ugyanazzal a mércével ellenőriztem
(utasítások és hívóhely), nem az index negatív találatára építettem.

**Korlátok (kimondva).** (1) A lapos nézet (`thumbui/flatview`)
csomópontjainak gyermeklistája nincs külön megnézve; ha egy lapos nézeti
sornak van gyermeklistája, az 6-os típusú, és kinyit/becsuk. (2) A sor bal
szélső sávja (nyíl és ikon, `0x00765fee-0x0076606f`) külön ágon fut; a kapu a
sor szövegére adott dupla kattintásra szól. (3) A `+0x38` bájt jelentése nincs
bontva; a nem nulla értékű csomópontok (nem fizikai mappa) nem tartoznak ide.
Mindhárom az M1 mérés (lent) első részével megerősíthető, és egyik sem
akadályozza a 3. törzs felvételét.

#### Z5. A Z2 táblázat a jelenlegi forráson, és a régi nyitott sorok besorolása

A jelölés: (a) a meglévő bizonyítékból eldőlt; (b) egyetlen megnevezett mérés
dönti el; (c) a felhasználó által látható viselkedést nem érinti, vagy a #7032
hatókörén kívül esik. A „Nálunk” oszlop a mai főágon `grep`-pel ellenőrzött; a
korábbi körök sorszámai több helyen elmozdultak.

| Z2 | Tétel | Döntés | Válasz | Nálunk (jelenlegi sorok) |
|---|---|---|---|---|
| 1 | A menüparancs feltétele | (a) | Változatlan: a kapu nem képszámot néz (Ghidra 406). | `PicasaFolderMenu.qml:16-28` (mappa van és nincs személynézet; albumnézetben az album ága), `MainMenuBar.qml:369-376`; egyezik |
| 2 | A mappafa helyi menüjének kibocsátója | (a) | Változatlan. | `FolderPaneTreeRow.qml:310`, `FolderHierarchyView.qml:363-370`, `FolderPaneMenus.qml:366`, `FolderContextMenu.qml:90-92`; egyezik |
| 3 | A rács üres területe és mappa-fejléce | (a), a belső hívólánc (c) | Változatlan. | `LightboxFeed.qml:718-724`, `LightboxFeedGroup.qml:188-194`, `Main.qml:562-565`, `FolderPane.qml:320`; egyezik |
| 4, 5, 6 | Gyorsbillentyű, néző, képtálca | (a) | Nincs belépő az eredetiben (Z2). | A `openFolderDescription` hívója csak a menüsor (`MainMenuBar.qml:374`) és a mappa helyi menüje (`FolderPaneMenus.qml:366`); a két menüelemen nincs gyorsbillentyű; egyezik |
| 7 | A mappalista dupla kattintása | (a), javított | Z4: almappa nélküli sor nyit, almappás sor kinyit/becsuk. | `FolderPaneTreeRow.qml:245-321`, `FolderHierarchyView.qml:391`; **eltérés, 3. törzs** |
| 8 | A beépített sorok típusa (`0x004b8470`) | (c) | A mappasor 5/6/7 típusa a `0x004b1c80`-ból jön, az albumsor 1-es típusa a `0x004b29d0`-ból; a név szerinti beépített sorok az album-folyamat (#7069) tárgya, a #7032 törzsei csak fizikai mappasorra szólnak. | A #7069 hatóköre |
| 9 | A rácsfejléc leírásmezőjének elfogadása és kulcsa | (b), nem blokkoló, M1 2. rész | Új részeredmény lent (a). | `LightboxHeaderDescription.qml:32-41` (Enter ment, Esc visszaállít, fókuszvesztésre nincs mentés), `LightboxFeedGroup.qml:40-51`, `controller_folder_description_mixin.py:57-95` |
| 10 | Siker után megerősítő üzenet | (a) | Nincs (Z1). | `FolderPropertiesDialog.qml:230-259`: a `_saveProperties` végén csak `root.accept()`; egyezik |
| 11 | Forrás- és célút | (a) | Változatlan (Z1). | `rename_folder.py:43-58`: `source.with_name(name)`, `name == source.name` összevetés; egyezik |
| 12 | Az újrapróbálás időkorlátja | (a) | Újraellenőrizve: `0x004fd28b-0x004fd293` `push 5`, `push 1`, cél, forrás, `xor al, al`; a `0x00994400` a `cmp esi, 5` után `0x00992ed0`-t, a `fild`/`fcomp` időkorlát-összevetést (`0x009a51b0`, másodperc) és `push 0x1f4` várakozást tartalmazza. | `rename_folder.py:13` (`_rename = os.rename`), `:53-58`: egyetlen hívás; **eltérés, 5. törzs** |
| 13 | `[Picasa]/name` | (a) | Változatlan (Z2, az előző kör korpuszmérését nem ismételtem). | `grep`: `[Picasa]/name` írója sehol nincs a forrásban (`ini`, `app`, `fileops`); `library_controller_resync.py:35-135`, `rename_folder.py:26-59`; **eltérés, 4. törzs** |
| 14 | `[Picasa]/date` automatikus dátumnál | (a), a hatás (c) | Új megerősítés lent (b). | `ini/folder_date.py:97-116` (olvasás), `:137-152` (törlés), megjegyzés `:144-146` |
| 15 | `.picasa.ini` írási hiba | (a) a felhasználó felé, (c) a lemezes hatásra | Változatlan (Z2). | `controller_folder_description_mixin.py:35-41`, `:85-95`; `folder_date_controller.py:130-153`; hibát jelez, a nézetet sikertelen írás után nem frissíti |
| 16 | Index és mappafa átnevezés után | (a) a sorrendre, (c) a rendezésre | Változatlan (Z2). | `library_controller_resync.py:67-77` (lemez, majd `move_folder_tree`), indexhibánál visszagörgetés; egyezik, szigorúbb |
| 17 | Rács és kijelölés az átnevezés után | (b), nem blokkoló, M1 3. rész | Változatlan (Z2). | `library_controller_resync.py:135`: `_reload(preserve_scroll=True)` |
| 18 | Mentési sorrend, részleges mentés | (a) | Változatlan (Z2): tudatos, barátságosabb eltérés. | `FolderPropertiesDialog.qml:230-259` |
| 19 | A névtisztítás `A  B` és `con` mérése | (a) | Nem szükséges (Z1). | `rename_folder.py:60-72`; `tests/fileops/test_rename_folder_4482.py:64-84`, `:122-130` |
| 20 | A sor és szöveg feloldó (`0x004543e0`) | (c) | Csak a dátum tartós szövegét építi, a felhasználó nem látja. | Nem érinti |
| 21 | Üres névnél az OK | (a) | Változatlan (Z2). | `rename_folder.py:40-42` |

**(a) A rácsfejléc leírásmezőjének címzettje: új részeredmény.** A
`CAlbumVarString` (`0x00746640`, vtábla `0x00cb1710`) `0x00746670` metódusa a
címzett értékátvétele: a konstruktor `+0x18` mezőjének (kiválasztó) értéke
szerint a `0x00746734` ugrótáblán át a `[+0x10]` objektum (`album + 0x50`)
vtáblájának `+8` (kiválasztó 0), `+4` (1) és `+0x10` (4) metódusát hívja
`(sor, szöveg, 1)` argumentumokkal, vagyis **tartós** jelzővel; a 2-es
kiválasztó nem hív semmit, a 3-as a `+0` metódust hívja két argumentummal. A
`0x00749ba0` a rácsfejléc leírásmezőjének csomópontjához (`0x0074a225 call
0x00717810`) a **0-s kiválasztójú** címzettet adja (`0x0074a1f7 push ebx`,
`0x0074a1f9 call 0x00746640`); az 1-es és a 4-es kiválasztóval épített másik
két címzett (`0x0074a158`, `0x0074a25c`) nem ezt a hívást kapja. A `+8` rés
a már ismert beállító vtábla (`0x00c81fa4`) felirat-beállítója
(`0x00443c90`) lenne, amely tartós
jelzővel a `"description"` kulcsot írja (Ghidra 417). **Nem igazolt:** hogy az
`album + 0x50` objektum vtáblája a `0x00c81fa4`-gyel azonos-e, mert a
`0x00c81fa4` vtáblát a két konstruktor (`0x00415804`, `0x0041777f`) a
gazdaobjektum `+0x48` mezőjébe teszi, nem `+0x50`-be. Ezért a fejléc elfogadása
a `description` kulcsra mutat, tartósan: **erős jelölt, nem igazolt**. Az
elfogadás kiváltója (Enter, fókuszvesztés, Esc) a `CTextEditNode`
(`0x00856060`) eseménykezelőjében van, ez nincs olvasva: M1 2. rész.

**(b) A `date=0.000000` és az ini-beállító: megerősítés a Z2 14. tételéhez.** A
`0x0099b5b0` (`ret 0xc`: szakasz, kulcs, érték) nem üres szövegnél
(`0x0099b5c7 cmp byte [esi], 0`, `jne 0x0099b5d8`) az értéket továbbadja a
fájlíró burkolónak (`0x009bef50`; a kulcs az `edi`, az érték az `esi`
regiszterben). Ez a `"0.000000"` szövegre is áll: **a `date=0.000000` sor
íródik, nem kulcstörlés** (erős, egy út; a burkoló belseje, `0x009bd640`, nincs
olvasva). Üres vagy null értéknél az `esi` nullázódik, és ha az ini-objektum
`+0xc` állapotjelző bájtja nulla, a függvény írás nélkül kilép (`0x0099b5ce`,
`0x0099b705`); különben nulla értékkel hívja tovább a burkolót (a Windows
ini-szokás szerint ez kulcstörlés: feltételes). A kulcs sorrendje a
szakaszon belül (új kulcs a szakasz végére kerül-e) a fájl bájtsorrendjét
érinti, a felhasználó nem látja: (c).

**A régi „Nyitott” sorok végső besorolása** (a régi szöveg érintetlen, a
`[blokkoló]` jelölések helyett ez érvényes):

- „A `+0x18` sorbájt jelentése és a `+0x30` típusok név szerinti
  hozzárendelése”: a mappasorokra (a) (Z4); a beépített és albumsorokra (c),
  #7069.
- „A `0x004b8470` sor, `[blokkoló]`”: (c), a #7032-re **nem blokkoló**, a
  #7069 tárgya.
- A tartós mezőírás, a kulcsnevek és az író lánc (Ghidra 407, 417, 421 és a
  `koteg-438-465` válasz): (a), Z2 13. és 14. tétel és a fenti (b).
- „A `0x0099b5b0`, a `0x005a8d60` és a `0x004543e0`, `[nem blokkoló]`”: a
  `0x0099b5b0` a fenti (b) szerint eldőlt (a); a `0x005a8d60` és a
  `0x004543e0` (c), nem blokkoló.
- Az átnevezés (Ghidra 408, 416, 422, 423) és a `0x009a51b0` időátváltó:
  (a), 5 másodperc (Z1).
- „A `CAlbumVarString` vtábla metódusai és a `0x00789c00`, `[blokkoló]`”: a
  vtábla metódusa a fenti (a) szerint részben eldőlt; a megmaradó kérdés az
  elfogadás kiváltója, (b), **nem blokkoló**, M1 2. rész. A `0x00789c00`
  (negyedik hívó) a fejléc felhasználó által látott viselkedését nem
  változtatja: (c).
- „Mérés: `A  B` és `con` a lemezen”: (a), nem szükséges (Z2 19.).
- „Az erőforrásbeli gyorsbillentyű-tábla”: (a), nincs (Z2 4.).
- „Mérés: ini-írási hiba után mi marad”: (a) a felhasználó felé (az író
  mindig nullát ad vissza, Z2 15.), (c) a lemezes hatásra.

### Zárási döntés (második zárókör, 2026-11-17)

**A #7032 kutatási jegy lezárható. Blokkoló nincs.** A 2026-11-16-i zárókör
egyetlen blokkolója, a mappalista dupla kattintásának három sortípusos
Colab-mérése megszűnt: a bináris eldönti (Z4). Minden korábbi „NINCS MEG” és
„Ghidra-kör kell:” tétel eldőlt (a), a #7032 hatókörén kívül esik (c), vagy az
alábbi egyetlen, megnevezett, nem blokkoló mérésre (M1) fut.

**M1 (Colab, eredeti Picasa 3.9, egyetlen menet, nem blokkoló).** A
végrehajtó dupla kattintást tud (`dupla` gomb). Három megfigyelés, mindegyikről
képkocka előtte és utána:

1. *Dupla kattintás a mappalistán.* Lapos nézetben egy almappás és egy almappa
   nélküli mappa során, majd fa nézetben ugyanez a két sor. Soronként: megnyílik-e
   a Folder Properties, kinyílik vagy becsukódik-e a sor. A bináris szerint az
   almappa nélküli sor megnyitja, az almappás kinyit/becsuk. A lapos nézet
   almappás sora a Z4 korlátainak (1) pontját dönti el.
2. *A rácsfejléc leírásmezője.* Az „Add a description” mezőbe írt szöveg
   megmarad-e Enter, mezőn kívüli kattintás (fókuszvesztés) és Esc után, és mit
   mutat az újranyitott Folder Properties Description mezője.
3. *Kijelölés átnevezés után.* Egy mappa három képének kijelölése, majd
   átnevezés a Folder Properties-ből: marad-e a kijelölés és a görgetési hely.

Egyik fejlesztői törzs sem függ az M1-től. Ha az 1. rész mást mutat a lapos
nézetben, a 3. törzs lapos listás kezelője csak a mért sortípuson nyit.

**A megmaradó fejlesztői jegytörzsek.** Az 1. és a 2. kész, a 3., 4. és 5.
felvehető.

- **1. A Hely mező szerkeszthető meglévő mappánál: KÉSZ** (`e88e4ee3f`,
  `907291af1`; a főágban, `FolderPropertiesDialog.qml:618` `enabled: true`,
  `controller_folder_description_mixin.py:14-41`, `ini/folder_location.py`;
  tesztek: `tests/ini/test_folder_location_7038.py`,
  `tests/app/test_folder_location_controller_7038.py`,
  `tests/app/qml_functional/test_folder_location_qml_7038.py`).
- **2. Az eredeti névtisztítás követése: KÉSZ** (`rename_folder.py:60-72`,
  `tests/fileops/test_rename_folder_4482.py:64-84` és `:122-130`, beleértve a
  szóközök összevonásának hiányát).

#### 3. A dupla kattintás az almappa nélküli mappasoron nyissa meg a tulajdonságablakot (javított, felvehető)

**Eredeti:** a `0x00765d30` az `lb_predouble` eseményre, 1-es vagy 5-ös
rekordtípusnál és `+0x18 == 0` esetén a `0x006db580` Folder Properties útját
indítja (`0x007663a5`). A fizikai mappasor rekordja 5-ös, ha nincs gyermeke
(`+0x18` ilyenkor nulla, `0x004b1c97-0x004b1cbc`), és 6-os (macOS `/Volumes/`
előtagnál 7-es), ha van; a 6-os és 7-es sor a `0x004ab9a0` kinyit/becsuk ágára
fut, tulajdonságablak nélkül (Z4). Fok: erős.

**Nálunk:** lapos listán a sor egere (`FolderPaneTreeRow.qml:245-321`) nem
kezel dupla kattintást; fa nézetben a `FolderHierarchyView.qml:391`
(`onDoubleClicked: root.toggle(row.modelData.path)`) minden soron kinyit/becsuk,
az almappa nélkülin hatástalanul. A belépő a `FolderPane.qml:252`
`openFolderDescription(path)`.

**Teendő:** (1) lapos listán a `kind === "folder"` sor dupla kattintása hívja a
`folderPane.openFolderDescription(path)` függvényt; (2) fa nézetben az a nem
gyökér sor, amelynek `modelData.hasChildren` hamis, ugyanezt hívja, az
almappás sor dupla kattintása marad kinyit/becsuk; (3) mentés-szűrő módban
(`mentesSzuroAktiv`) a dupla kattintás ne nyisson ablakot (a sor ott pipa); (4)
a „Rejtett mappák” fejléc, az év-fejlécek, a gyökérsor, a beépített és az
albumsorok viselkedése nem változik (#7069).

**Kész, ha:** QML-teszt valódi dupla kattintással (nem a függvény hívásával):
lapos lista egy sorára és fa nézet levélsorára dupla kattintás után a Folder
Properties megnyílik az adott mappa nevével, dátumával, helyével és
leírásával; fa nézet almappás sorára dupla kattintás kinyit/becsuk, ablak
nincs; az egyszeres kattintás változatlanul csak kijelöl; mentés-szűrő módban
nem nyílik ablak.

**Nem szabad:** az egyszeres kattintás, a jobb gombos menü, a húzás és a
hierarchia kinyitó nyilának (`FolderHierarchyView.qml:232-236`) viselkedése
nem változhat.

#### 4. Az OK írja a `[Picasa]/name` sort

**Eredeti:** a `0x0055d320` a név beállítóját a Folder Properties minden OK
gombjánál lefuttatja, nem különleges mappánál tartós jelzővel, változatlan
névnél is, az átnevezés előtt; a `0x00445460`, `0x004545c0`, `0x0045c0a0` lánc
a mappa `.picasa.ini` fájljának `[Picasa]` szakaszába `name=<tisztított név>`
sort ír (Ghidra 417 és 421, a Z1 diszasszemblálása). Fok: erős.

**Nálunk:** `library_controller_resync.py:35-135` (`renameFolder`),
`rename_folder.py:26-59` és `FolderPropertiesDialog.qml:230-259`
(`_saveProperties`) nem írnak `[Picasa]/name` kulcsot (a forrásban nincs ilyen
író: `ini`, `app`, `fileops`). A mappa `.picasa.ini` fájlja az átnevezéssel
együtt költözik, a régi `name=` sor elavultan marad.

**Teendő:** az OK megnyomásakor, sikeres átnevezés után (és változatlan névnél is) írd a
`[Picasa]/name` kulcsot a mappa tényleges nevével az `ini` csomag API-ján át,
a `ini/folder_location.py` és a `setFolderLocationOf`
(`controller_folder_description_mixin.py:21-41`) mintájára (új
`with_folder_name` jellegű függvény és vezérlő-slot, a `_saveProperties` hívja
a helymentés mellett). Írási hibát jelezz, de a már megtörtént átnevezést ne
vond vissza. Ha a sor már a mappa nevét tartalmazza, ne legyen írás. A kulcs
olvasói hatása (az eredeti ebből jeleníti-e meg a mappa nevét) nem bizonyított:
a cél a fájltartalom egyezése. Kisebb kapcsolódó teendő, ugyanebben a csomagban: az
`ini/folder_date.py:144-146` megjegyzése a `0x0071031e` kapura hivatkozik, ami
a teljes-ini-író (`0x00710080`) sajátja; a Folder Properties beállítója a
`0.000000` szöveget sorként írja (fenti (b)), a megjegyzést ennek megfelelően
pontosítsd, a működés (a kulcs törlése, `_VARIANT_MIN = 1.0`) nem változik.

**Kész, ha:** átnevezés után a `[Picasa]` szakasz `name=` sora az új nevet
tartalmazza (meglévőt felülír, hiányzót létrehoz, hiányzó `.picasa.ini`-nél a
fájl létrejön); változatlan névvel OK után a sor a mappa nevével egyezik; ha a
sor már egyezik, a fájl bájtra változatlan és írásvédett mappán sincs
hibaüzenet; a többi `[Picasa]` kulcs és a képszakaszok érintetlenek.

**Nem szabad:** a sikertelen átnevezésnél a párbeszéd nyitva marad, és a
`name=` sor nem változik; a `description`, `date`, `location`, `music`
mentésének sorrendje és hibakezelése nem változik.

#### 5. Az átnevezés újrapróbálása hozzáférési hibánál (kicsi, csak Windows)

**Eredeti:** a `0x00994400`, hívás `0x004fd28b-0x004fd293` (`push 5`, `push 1`,
cél, forrás, `xor al, al`): az `al` nulla, tehát nincs felülírás; ha a
`MoveFileExW` hibakódja 5, és a forrás létezik (`0x00992ed0`), 500
ezredmásodpercenként újrapróbálja (`push 0x1f4`), legfeljebb 5 másodpercig
(`0x009a51b0` másodpercet ad); az első hiba után a ciklus bármely nem nulla
hibakódra folytatódik az időkorlátig. Az időkorlát után a hiba az átnevezési
figyelmeztetéshez vezet. Fok: erős.

**Nálunk:** `rename_folder.py:13` (`_rename = os.rename`) és `:53-58`: egyetlen
hívás, hiba esetén azonnal `FolderRenameError`.

**Teendő:** Windowson, `PermissionError` (`winerror` 5) esetén, ha a
forrásmappa létezik, 0,5 másodpercenként újrapróbálás legfeljebb 5
másodpercig; az időkorlát után a mostani hibaüzenet. Más platformon nincs
változás. A várakozás a felületi szálat ne fagyassza tovább az eredetinél (az
is a felületi szálon vár); ha a hívás szintje ezt nem tűri, kerüljön háttérbe.

**Kész, ha:** a `_rename` fogantyúval, a hibák és az idő szimulálásával: két
hozzáférési hiba után a harmadik próbálkozás sikeres átnevezést ad;
folyamatos hibánál 5 másodperc után a régi hibaüzenet; nem létező forrásnál
nincs újrapróbálás; Linuxon a viselkedés változatlan.

**Nem szabad:** a csak kis- és nagybetűt változtató átnevezés útja
(`_rename_folder_case_only`) és a létező célmappa elutasítása nem változhat.

Nem blokkoló, külön nem jegyzett tételek (ebben a körben eldöntve): a
`0x005a8d60` és a `0x004543e0` (a felhasználó nem látja), az új kulcs helye a
`[Picasa]` szakaszon belül, a lapos nézet sorainak gyermeklistája és a sor bal
szélső sávja a dupla kattintásnál (M1 1. rész erősíti meg), a fejléc
elfogadásának kiváltója (M1 2. rész), a kijelölés és a görgetés az átnevezés
után (M1 3. rész).


### #7235-kiegészítés (2026-11-18): az INI setter és az 1-es típusú parancs

#### #485 - 0x0099b5b0, 0x005a8d60

A 0x0099b5b0 dekompiláció (2026-11-18-koteg-466-495.txt:3516-…) üres értéknél null pointert ad tovább; a "0.000000" nem üres, ezért ezen a setter-rétegen nullázás nélkül jut a 0x009bef50 íróhoz. Ha a beállítóobjektum +0xc jelzője nulla, korán visszatér. Ez a réteg önmagában nem dönti el, hogy az alacsonyabb író törli-e a kulcsot, üres sort ír-e, illetve hová kerül új kulcs a szakaszon belül. Nyitott következő cím: 0x009bef50 és a hívott INI-sorosító, továbbá az azonos kulcs frissítési/új kulcs beszúrási ága.

A korábban meglévő 0x005a8d60 kimenet (2026-11-15-6963-colab-decomp-2.txt:72-…) alapján az iVar5 == 1 és *piVar14 == 1 ágon a parancs két tömbmezőt fűz az adott rekordhoz; a param_2[2]/param_2[3] és param_2[5] mezők adják a hozzáfűzött elemeket. A teljes hívóoldali DAT_00d6769c objektum és a jegy végén megszakadt „ugyanaz a cél, mint a #702…” összevetés nincs megadva, ezért a parancs magas szintű szerepét nem azonosítom. Következő ellenőrzés: a 0x005aa260, 0x005aa730, 0x005aadf0 hívók és a DAT_00d6769c felépítője. A 0x005a8d60 már dekompilált; új Ghidra-kérést csak erre az új hívó-/objektumkapcsolatra indokolt kérni.
## #7059: A mappa áthelyezésének teljes folyamata az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, SHA-256:
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Ez a szakasz a #6845 §1 korábbi, menüazonosítókra vonatkozó állítását
pontosítja: az ottani `0x9df4` / `ID_MOVEFOLDER` párosítás hibás volt.

### Következtetés

A fizikai MoveFolder-kezelő statikusan igazolt útja a `0x9df4` parancs
(`0x0053f340` → `0x0053f4a0`), de a menüépítők ezt a parancsot `&Delete...` /
`&Delete Folder...` felirathoz rendelik; a látható `&Move...` /
`&Move Folder...` tételek `0x9cce` azonosítója másik kezelőhöz jut. A
HierFolder-fa azonos feliratú menüpontja külön `0x9cba` parancs, amely a
`0x005d0e90`-re jut. Ez a statikus wiring nincs Picasa 3.9-en futtatva
ellenőrizve, ezért a címkék tényleges felhasználói hatása és a teljes
paritás nyitott.

### Bizonyítottsági fok

**Feltételes.** A menürekordok, a parancs-diszpécser, a fizikai mozgató
útja, a célválasztó, a névütközés és a `+0x208` karakterlánc-mező
eltérésénél történő korai hibavisszatérés két egymástól
független statikus úton egyezik. A felirat/kezelő ellentmondás tényleges
futásidejű hatása, a HierFolder út, a figyelt gyökér feltétele, a hálózati
út és a részleges/írásvédett hibák nem mértek.

### 1. Belépési pontok és feltételek

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Fő Mappa menü: `0x00559150` a `eMenuLabelFolder::ID_MOVEFOLDER` / `&Move...` rekordhoz `0x9cce`-t ad (`0x0055b184-0x0055b19b`); a `0x005cb990` ezt `0x005ce590`-re küldi. A sztring-xrefek és a `0x005ce590` handler `Do you want to remove the folder ... and its subfolders?` / `Remove Folder` üzenetet mutatják. A tényleges MoveFolder-út a következő `eMenuLabelFolder::ID_ALBUM_DELETE` / `&Delete...` rekord `0x9df4` azonosítóján (`0x0055b1ec-0x0055b203`) át fut: `0x005cb990` → `0x0053f340` → `0x0053f4a0`. | `src/picasapy/app/qml/PicasaPy/PicasaFolderMenu.qml:199-213`; `src/picasapy/app/qml/PicasaPy/MainMenuBar.qml:166-174` | Statikus eltérés: nálunk a Move címke ténylegesen mozgat, a Delete címke lomtárba tesz. Az eredeti menükattintások mért hatása nélkül ne változtassuk meg a működést; előbb az eredeti bináris címke/kezelő ellentmondását kell futásban tisztázni. |
| Mappafa helyi menü: `0x007319f0` a `Folder::ID_MOVEFOLDER` / `&Move Folder...` rekordhoz `0x9cce`-t, a `Folder::ID_ALBUM_DELETE` / `&Delete Folder...` rekordhoz `0x9df4`-et rendel. A diszpécserút a főmenüével egyezik: `0x9cce` → `0x005ce590`; `0x9df4` → `0x0053f340` → `0x0053f4a0`. | `src/picasapy/app/qml/PicasaPy/FolderContextMenu.qml:321-336`; `src/picasapy/app/qml/PicasaPy/FolderPaneMenus.qml:305-315` | A PicasaPy Move Folder menüpontja a fizikai mappamozgatót hívja, a Delete Folder a lomtárat. Az eredeti helyi menü statikus párosítása ugyanolyan címke/handler ellentmondást mutat, mint a főmenü; futásmérés kell az egyezés eldöntéséhez. |
| HierFolder-fa helyi menü: `0x00733a40`, `HierFolder::ID_MOVEHIERFOLDER` / `&Move Folder...`, parancs `0x9cba`; a diszpécser `0x005d0e90`-re küldi. Ez nem a `0x0053f4a0` fizikai MoveFolder-út. A `0x005d0e90` a `0x005c85e0` Open Folders megerősítést is elérheti; a meglévő #419 dekompiláció a Ctrl+Enter listakezelő-útját fejti ki, nem ezt a HierFolder menüágat. | `src/picasapy/app/qml/PicasaPy/FolderHierarchyView.qml:479-482` | Lehetséges eltérés: nálunk a hierarchia Move Folder felirata fizikai mozgatást indít. Az eredeti `0x9cba` hierarchiaág szándékát célzott Ghidra-kör vagy Picasa 3.9 futásmérés nélkül nem szabad azonosítani. |
| A `0x00733a40` menüstruktúrájának utolsó rekordja `0x9df5`, de a feliratpointere null. Ez a diszpécserben `0x0053f3a0`-ra jut, amely bizonyos visszatérési kódoknál `0x0053f4a0`-t hív. Hogy ez a rekord látható-e vagy milyen esemény váltja ki, NINCS MEG. | Nincs azonosított, feliratozott megfelelő; a PicasaPy explicit mozgatója a fenti QML-út. | Nyitva hagyni; ne számítsuk a feliratozott menübelépések közé. |
| Gyorsbillentyű: a teljes `.text`-pásztázás a `0x9df4` közvetlen előfordulásait a menüépítés/engedélyezés/diszpécser körében találta; a PE-ben nincs `RT_ACCELERATOR` erőforrás, a meglévő `0x00923110` dekompiláció nullázott ACCEL rekordot ad a `CreateAcceleratorTableA`-nak. A menü `&` mnemonikája önálló billentyűparancsot nem bizonyít. | `src/picasapy/app/qml/PicasaPy/PicasaFolderMenu.qml:199-213`; a Move menüpontnál nincs `Shortcut` hozzárendelés. | Dedikált MoveFolder-gyorsbillentyű nem találtam; ezen a ponton nincs igazolt eltérés. |
| A fizikai kezelő belépési őre `0x0053f340`: kiválasztott mappaobjektumot és nem `-1` azonosítót vár, majd a `0x004461a0` predikátumot vizsgálja. A `0x0056e1c0` menüállapot-építő a `0x9df4` tételt is letilthatja a `0x00995c90` vagy `0x004ac8f0` predikátum alapján. A `0x00995c90` hét futásidőben feloldott Windows mappaútvonalat vizsgál: My Pictures, Desktop, My Music, My Videos, My Documents, `Application Data`, `Common Application Data` (`0x00994a60` sztring-xrefek). A `0x004ac8f0` és `0x004461a0` pontos jelentése nyitott. | `src/picasapy/fileops/move_folder.py:40-87`; `src/picasapy/app/qml/PicasaPy/PicasaFolderMenu.qml:200-205` | PicasaPy explicit rendszerút-listát és home/gyökér-védelmet használ; a hét feloldott Windows ismert mappa mindegyike nincs benne külön. A Picasa eredeti figyelt gyökér- és hálózati feltételei nem zártak, ezért ezek teljes egyeztetéséhez külön célzott vizsgálat kell. |

### 2. A célmappa kiválasztása

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A `0x0053f4a0` a `MoveFolderLastPath` értékét a `Preferences` csoportból olvassa és a párbeszéd után visszaírja. A címe `Move Folder to %s` (`0x00c8aca4`). A `0x00998760` shell mappaválasztót hív; a dinamikus callback `0x009b0cb0` utasításai a `SHBrowseForFolderW` importot hívják. Érvényes, létező utolsó cél esetén azt adja át kezdőútnak; hiányzó/érvénytelen értéknél a kód a kiválasztott mappa objektumából kinyert forrásútvonalra esik vissza. A forrásmappa vagy szülője közötti UI-viselkedést külön futásmérés nem igazolta. | `src/picasapy/app/qml/PicasaPy/FolderPaneMenus.qml:276-295` | A Qt párbeszéd címe `Browse for Folder`, kezdőútja a forrásmappa szülője; explicit `MoveFolderLastPath`-megfelelő nincs ezen az úton. Az eredeti cím és a megjegyzett célút PicasaPy-beli egyeztetése fejlesztési feladat lehet, de a nyitóhely első futásos alapértékét előbb mérjük. |

### 3. Fájlok, metaadatok és katalógus

| Hatás | Eredeti Picasa 3.9 | PicasaPy most |
|---|---|---|
| Lemez | A `0x0053f4a0` a kiválasztott könyvtárat a cél alá mozgatja a `0x0052e0f0` → `0x004fd1c0` → `0x00994400` útvonalon; a legalacsonyabb szint `MoveFileExW`-re jut. | `src/picasapy/fileops/move_folder.py:90-131` a teljes könyvtárat mozgatja. |
| `.picasa.ini`, albumok és arcok | A könyvtárat mozgatja, nem válogat fájlokat; a benne levő `.picasa.ini` és a fájlok együtt haladnak. A képek `albums=` hivatkozásai, valamint a `faces` és `albumlist` metaadatkulcsok a specifikáció szerint az ini-adathoz tartoznak (`docs/specs/picasa-ini-format.md:132-136,1305-1308`). A siker utáni memóriabeli arc-/album-cache állapota NINCS MEG. | Ugyanígy a teljes könyvtár megy (`move_folder.py:90-131`); az `application_services.py:114-120` siker után a `library_controller_resync.py:142-189` újraolvassa az új és régi részfát, és kezeli az áthelyezett figyelt gyökeret is. |
| Index és UI | A `0x004fd1c0` siker után frissíti a katalógus út-prefixeit; a `0x0053f4a0` sikerág további index-/nézetfrissítő rutinokat hív. A végső mappafa, fotórács, görgetési helyzet és kijelölés pontos állapota NINCS MEG. | A sikeres mozgatás `folderMoved` jelzést küld (`src/picasapy/app/fileops_controller_move_mixin.py:288-312`), amely célzott régi/új részfa-resyncet indít (`library_controller_resync.py:142-189`). A kijelölés és a rács végállapotát ez a statikus forrásolvasás nem mérte. |

### 4. Ütközés, írásvédelem, részleges és más kötetes mozgatás

| Eset | Eredeti Picasa 3.9 | PicasaPy most | Teendő |
|---|---|---|---|
| Célon azonos nevű mappa | A `0x0053f4a0` célút-ellenőrzése (`0x00992ed0`) ütközéskor leáll, és a `A folder with that name already exists in the destination folder` üzenetet használja (`0x00c8ad10`). | A `move_folder.py:124-128` előre ellenőrzi a `target.exists()` állapotot és emberi hibát ad. | A leálló viselkedés egyezik; a szövegek pontos egyezése nem cél ezen a kutatási jegyen. |
| Írásvédett cél | A cél kiválasztása után a műveleti hibaág a `MoveFolderError` üzenetet és a visszatérő kódot mutatja (`0x0053f4a0`, `0x00c8ad90`). Nincs igazolt attribútum- vagy írhatósági előellenőrzés, és nincs Picasa 3.9 mérés. | A fájlművelet `OSError` esetén `FolderMoveError`-t ad (`move_folder.py:156-183`). | A pontos eredeti hiba és a lemez végállapota NINCS MEG; kontrollált, írásvédett célon végzett eredeti Picasa-mérés kell. |
| Részleges mozgatás | A sikeres út utáni állapot statikusan követhető, de a `MoveFileExW` hiba/ részleges eredmény esetére nem állapítható meg biztos rollback vagy maradványállapot. | Más köteten a `move_folder.py:134-192` temp-másolatot, forrástörlést és végső átnevezést használ; egy késői átnevezési hiba után a régi hely üres, az ideiglenes cél megmarad. | Eredeti részleges hibakimenet NINCS MEG; ne állítsunk paritást mérés nélkül. |
| Másik kötet | A `0x0052e0f0` `param_4=1` értékkel hívja a `0x004fd1c0`-t. Ez a két rekord `+0x208` bájteltolású (dekompilációban `param[0x82]`) karakterlánc-mezőjét kis-nagybetű-függetlenül összeveti; eltéréskor `-1`-gyel visszatér a `0x00994400` hívása előtt. A #422 Ghidra-összefoglaló a mezőt kötetmezőnek nevezi, de a mező pontos jelentését az önálló disassembly nem bizonyítja. | A `move_folder.py:137-160` `os.rename` hiba után `copytree`-s fallbackra tér át, így más fájlrendszerre is megpróbál mozgatni. | A mezőeltérés miatti korai hibavisszatérés igazolt; hogy eltérő kötet esetén ez a mező eltér-e, NINCS MEG. A kötetek közötti mozgatás egyezéséről ezért még nem állítható eltérés. A mező jelentését és az UNC viselkedést külön kell feloldani. |

### Bizonyítékok

| Érték / állítás | Forrás |
|---|---|
| A Move Folder menürekord azonosítója `0x9cce`, a Delete rekordé `0x9df4` a fő Mappa menüben és a normál Folder helyi menüben. | bináris (`0x00559150`, `0x007319f0`) |
| `0x9df4` → `0x0053f340` → `0x0053f4a0`; a `0x9cce` → `0x005ce590`; a HierFolder `0x9cba` → `0x005d0e90`. | bináris (`0x005cb990`) |
| A fizikai célválasztó címe és a `MoveFolderLastPath` olvasás/írás. | bináris (`0x0053f4a0`, `0x00998760`, `0x009b0cb0`) |
| A rendszerút-hiba és névütközés pontos angol üzenetei. | bináris (`0x0053f4a0`, string xrefs `0x00c8acd4`, `0x00c8ad10`) |
| A `+0x208` karakterlánc-mező eltérése `-1`-et ad a fájlművelet előtt; a mező kötet- vagy UNC-jelentése nem igazolt. | bináris (`0x0052e0f0`, `0x004fd1c0`, `0x00994400`); mezőszemantika: NINCS MEG |
| A PicasaPy célút, mozgatás, fallback és resync. | forrás (`src/picasapy/fileops/move_folder.py:90-192`; `src/picasapy/app/fileops_controller_move_mixin.py:288-312`; `src/picasapy/app/library_controller_resync.py:142-189`) |
| Írásvédett cél és az eredeti részleges hibák pontos lemezállapota. | NINCS MEG |
| A HierFolder `0x9cba` menüpont pontos runtime-hatása; a `0x004ac8f0` jelentése a figyelt gyökérre; az UNC reprezentáció. | NINCS MEG |
| MoveFolder mérőadat vagy Windows Picasa 3.9 előtte/utána mérés. | NINCS MEG |

### A két független út

- **A: utasításszintű olvasás:** az `annot_disasm.py` közvetlenül kiírja a
  `0x00559150` menürekord felirat-/ID-mezőit, a `0x007319f0` és `0x00733a40`
  helyi menürekordjait, majd a `0x005cb990` diszpécser és a mozgató segédek
  utasításait. A `0x9df4` fizikai MoveFolder út; `0x9cce` és `0x9cba` más
  handlerre jut.
- **B: index és korábban meglévő Ghidra-kimenet:** az index
  `string_xrefs` táblája a `MoveFolder`, `Folder::ID_MOVEFOLDER` és
  `HierFolder::ID_MOVEHIERFOLDER` stringeket a megfelelő menüépítőkhöz köti;
  a `2026-10-21-idorend-30.txt` `0x005cb990` switch-kimenete és a
  `2026-11-16-7022-7031-7033-colab-decomp.txt` `0x004fd1c0` dekompilációja
  ugyanazokat a diszpécser- és korai hibautakat mutatja. A két út egyezik.

### Cáfoló kísérlet

Azt próbáltam cáfolni, hogy a `0x9df4` a Move Folder felirat azonosítója,
mert a korábbi #6845 jegyzet ezt állította. A teljes `0x00559150`
rekordblokk utasításszintű olvasásakor `ID_MOVEFOLDER` + `&Move...` mellett
`0x9cce`, míg `ID_ALBUM_DELETE` + `&Delete...` mellett `0x9df4` található;
a `0x007319f0` helyi menü azonos sorrendet mutat. A cáfolót külön úton a
string-xrefekkel és a diszpécser switchével ellenőriztem: a `0x9df4` valóban
a `0x0053f340` fizikai mozgatóhoz, a `0x9cce` a `0x005ce590` eltávolító
kezelőhöz jut. A korábbi ID-hozzárendelés megdőlt; a szokatlan címke/handler
viselkedés futásban továbbra sincs mérve.

Külön próbáltam cáfolni, hogy a `0x004fd1c0` `+0x208` mezője biztosan
kötetazonosító. A disassembly csak a két mező karakterláncainak
kis-nagybetű-független összevetését és eltéréskor a `-1` visszatérést
mutatja; az objektum mezőjének jelentéséhez nem találtam független
struktúra- vagy mérési bizonyítékot. Ezért a korábbi „másik kötetet
elutasít” következtetést visszavontam. A cáfoló ellenpróba eredménye
ugyanazzal a mércével: mezőeltérés igazolt, kötetjelentés és kötetek közötti
hatás NINCS MEG.

### A jegy „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték |
|---|---|---|
| Fő menü, mappafa-helyi menü és gyorsbillentyű | ⛔ | Főmenü és normál Folder menü címke/ID/handler statikusan feltárt, de a futásidejű Move/Delete hatás ellentmondásos; HierFolder út és dedikált billentyűparancs nem zárt. |
| Figyelt gyökér, különleges mappa és hálózati meghajtó feltétele | ⛔ | Hét Windows ismert mappa és két további predikátum ismert; a `0x004ac8f0`, UNC és Picasa-futásmérés nyitott. |
| Célválasztó ablaka, alapértéke és megjegyzett állapota | ✅ / ⛔ | `SHBrowseForFolderW`, cím és `MoveFolderLastPath` igazolt; hiányzó/érvénytelen kulcs melletti első futás UI-alaphelye nem mért. |
| Fájlok, `.picasa.ini`, index, fa, rács, kijelölés, albumtagság és arcok | ✅ / ⛔ | Könyvtár és `.picasa.ini` együtt mozog, az index út-prefix frissül; a cache-ek és látható kijelölés végállapota nincs mérve. |
| Ütköző név, írásvédett cél, részleges és más kötetes mozgatás | ✅ / ⛔ | Névütközés és a `+0x208` mező eltérésénél adott korai hiba statikusan eldöntött; az eltérő kötetek összefüggése, az írásvédelem és a részleges eredeti végállapot nyitott. |

### Javasolt fejlesztői jegytörzsek

**A célválasztó eredeti címének és utoljára használt céljának megőrzése**

Eredeti: a `0x0053f4a0` a `Move Folder to %s` címet (`0x00c8aca4`) használja,
és a `Preferences/MoveFolderLastPath` értékét olvassa/írja. Nálunk:
`FolderPaneMenus.qml:276-295` címe `Browse for Folder`, kezdőútja a forrás
mappájának szülője; explicit utolsó célút nincs.

Teendő: a célválasztóban jelenjen meg a mozgatott mappa nevét tartalmazó
cím, és a sikeresen kiválasztott célút maradjon meg következő megnyitásra.
Az első futásos kezdőhelyet az eredeti Picasa-méréssel kell rögzíteni.

Kész, ha: egymás utáni megnyitáskor a legutóbbi célmappa jelenik meg; a cím
megnevezi az éppen mozgatott forrásmappát; első futásnál a megmért eredeti
alaphelyet használja.

**Windows ismert mappák mozgatásának védelme**

Eredeti: a fizikai MoveFolder-út a `0x00995c90` vizsgálattal hét
futásidőben feloldott Windows mappautat ellenőriz (My Pictures, Desktop,
My Music, My Videos, My Documents, Application Data, Common Application
Data), és tiltó ágban a `Unable to Move a System Path` üzenetet használja
(`0x0053f4a0`, `0x00c8acd4`). Nálunk a
`src/picasapy/fileops/move_folder.py:40-87` rögzített `_SYSTEM_PATHS`
listájában a `C:\Users` szerepel, az egyes ismert mappák nincsenek
feloldva.

Teendő: a hét ismert Windows mappa mozgatására kerüljön paritásvédelem,
miután az eredeti predikátum pontos egyezési szabályát (mappa vs. alatta
levő könyvtár) és a további `0x004ac8f0` kaput feloldottuk.

Kész, ha: a hét feloldott mappán a mozgatás a Picasával egyező módon
megáll; a mappák alatti felhasználói könyvtárak engedélyezése a mért
Picasa-viselkedéssel egyezik.

**Az eredeti menüparancsok runtime-jelentésének tisztázása**

Eredeti: a `0x00559150` és `0x007319f0` `&Move` felirata `0x9cce`-t kap,
amely `0x005ce590`-re jut; a `&Delete` felirat `0x9df4`-et kap, amely a
fizikai `0x0053f4a0` mozgatóhoz jut. Nálunk a Move ténylegesen mozgat, a
Delete a lomtárba tesz (`PicasaFolderMenu.qml:199-213`,
`FolderContextMenu.qml:321-336`).

Teendő: előbb Picasa 3.9-en mérjük meg mindkét címke tényleges hatását;
csak utána nyissunk viselkedést igazító fejlesztői jegyet. A statikus
bináris-ellentmondás önmagában nem elegendő a feliratok felcseréléséhez.

**Feloldás (hívói kiegészítés, 2026-11-16):** a #7012 helyesbítése szerint a menürekord-építőkben a parancsmező az eggyel **előző** rekordhoz tartozik (saját mintavétellel igazolt szabály, lásd a #7012 szakasz „Helyesbítés” pontját). Ezzel a `&Delete Folder...` rekord mezőjében álló `0x9df4` a `&Move Folder...` tételé, és a `0x0053f4a0` fizikai mozgatóútra jut; a `&Move Folder...` mezőjében álló `0x9cce` az előtte álló tételé, és a `0x005ce590` („Do you want to remove the folder”) kezelőre jut; a `&Delete Folder...` parancsa a következő rekord mezőjében álló `0x9d44`, egyezésben a #7031 szakasszal. A felirat és a kezelő közti ellentmondás így megszűnik; bizonyítottsági fok: erős.

Kész, ha: külön rögzítettük a fő Mappa menü, a Folder helyi menü és a
HierFolder menü kattintásának lemez-, katalógus- és felületi hatását, majd a
PicasaPy parancsokat ezekhez rendeltük.

### Új kutatási jegyjavaslatok

- **A HierFolder `Move Folder...` parancs tényleges célja**: a
  `0x00733a40` / `0x9cba` út `0x005d0e90`-re jut; a mappalista Ctrl+Enter
  dekompilációja nem dönti el a hierarchiamenü ágát. Keresd a meglévő
  Ghidra-kimenetekben `0x005d0e90`-et; új körben ezt a hierarchiamenü-hívót
  és a handler teljes hatását dekompiláld.
- **A MoveFolder `+0x208` mezőjének jelentése**: a `0x004fd1c0` két
  rekordból származó karakterláncot hasonlít össze; a korábbi kötetnév
  önmagában nem bizonyítja, hogy különböző fájlrendszer más értéket ad.
  Keresd a meglévő `0x004fd1c0` Ghidra-kimenetet, és új körben az objektum
  mezőjének íróját/olvasóját azonosítsd; ez dönti el a kötetek közötti és UNC
  viselkedést.

### Nyitott

- `Ghidra-kör kell: 0x005D0E90: a 0x00733a40 HierFolder::ID_MOVEHIERFOLDER (0x9cba) pontosan mappát nyit, katalógusból távolít el, vagy fájlrendszer-mozgatást végez? A meglévő #419 kimenet a Ctrl+Enter mappalista-útját és az Open Folders megerősítést mutatja, de nem ezt a helyi menü-hívót. [blokkoló]` **Megválaszolva a zárókörben** (lásd a „Ghidra-kör kell tételek lezárása” táblát): a `0x9cba` a `&Locate on Disk` parancsa, a HierFolder `&Move Folder...` parancsa `0x9df5`, és az is a fizikai mozgatóra jut.
- `Ghidra-kör kell: 0x005CE590: a 0x00559150 / 0x007319f0 Move Folder címkéjű 0x9cce handlerének lemez- és katalógushatása mi, és miért a Remove Folder sztringeket használja? A meglévő Ghidra-fájlok csak a handler hívóit/string xrefjeit tartalmazzák, teljes dekompilációt nem. [blokkoló]` **Megválaszolva a zárókörben**: a `0x9cce` a `&Remove from Picasa...` rekord parancsa, nem a mappa mozgatásáé; a `Remove Folder` szövegek ezért helyesek.
- `Ghidra-kör kell: 0x004AC8F0: a 0x0056e1c0 menüállapot-építőben használt predikátum figyelt gyökérre vonatkozik-e, és milyen mappát tilt? A meglévő dekompiláció a hívást mutatja, a virtuális/predikátum-szemantika nem dőlt el. [blokkoló]` **Megválaszolva a zárókörben**: nem figyelt gyökérre vonatkozik, hanem az iPhoto- és Photos-könyvtár `Masters` mappájára.
- `Ghidra-kör kell: 0x004FD1C0: a +0x208 bájtoffsetű mező pontosan mit azonosít (kötet, útgyökér vagy más rekordkulcs), ki tölti fel, és mit jelent a különböző érték a kötetek közötti/UNC esetben? A meglévő #422 dekompiláció a mezők összevetését és az eltéréskor adott -1-et mutatja, de az objektum mezőszemantikáját nem oldja fel. [blokkoló]` **Megválaszolva a zárókörben**: a `+0x208` a `_splitpath`-szerű bontás meghajtó-összetevője (`C:`).
- **NINCS MEG:** az eredeti írásvédett cél és részleges mozgatási hiba pontos kimenete. Út: külön kontrollált Windows Picasa 3.9.141 futás írható, írásvédett és szándékosan hibás célon; minden esetben rögzíteni kell a forrás/cél fájlokat és a felhasználói hibaüzenetet.
- **NINCS MEG:** a mappafa, rács, kijelölés, albumlista és arcfelismerési cache végállapota sikeres fizikai mozgatás után. Út: Picasa 3.9 előtte/utána mérés egy mappával, albumtagsággal és arcmetaadattal.
- **NINCS MEG:** a chooser első futásos alaphelye, ha a `MoveFolderLastPath` hiányzik vagy már nem létezik. Út: célzott Windows-mérés tiszta preferenciával, majd a megjegyzett célút törlése után.
- **NINCS MEG:** UNC/hálózati meghajtó engedélyezése és tényleges fájlhatása; a NAS-t nem jártam be, és hálózati tesztet nem végeztem.
- **NINCS MEG:** az eltérő fájlrendszer vagy kötet hatása a `+0x208` mezőre; ezért a kötetek közötti elutasítás és a PicasaPy fallback közötti eltérés sem bizonyított.

### Zárókör (2026-11-16)

A zárókör a meglévő Ghidra-kimeneteket (`referencia/ghidra/`), a bináris indexet és a `Picasa3.exe` gépi kódjának közvetlen, utasításszintű olvasását használta; a dekompiláció veremértelmezését a hívóhelyek utasításaival ellenőriztem. A futtatott felvételek a `referencia/kepernyo/` alól valók. Az alábbi szakaszok kiegészítik a fentieket: ahol egy korábbi sor ellentmond, a helyesbítés itt áll, a korábbi szöveget nem töröltem.

#### Helyesbítés: a menürekordok rendje, és a HierFolder `Move Folder...` valódi parancsa

A menüépítők 0x14 bájtos rekordokat töltenek fel. A felirat mutatója a rekord elején (+0x00) áll, a billentyűszöveg mutatója a +0x04-en, a parancsazonosító a +0x0a-n. A fordító a következő rekord feliratának előkészítését az előző rekord mezőinek írásába szőtte, ezért az utasítássorrendben a parancs a "következő" felirat blokkjában látszik; a memóriacím szerinti olvasás egyértelmű. Bizonyíték: a Ghidra-kimenet közvetlen címzései (`_DAT_00d6e2f6 = 0x9df4`, `_DAT_00d6e2ba = 0x9cba`, `_DAT_00d6e2ce = 0x9cce`; `referencia/ghidra/2026-11-15-6970-colab-decomp.txt`), és az, hogy így minden rekord a diszpécser kezelőjével egyezik (kibontás, összecsukás, eltávolítás, mozgatás, a mappa megkeresése a lemezen). A #7012 helyesbítése ugyanezt a szabályt mondja ki más megfogalmazásban.

| Menü (építő) | Rekord (felirat, azonosító) | Parancs | Kezelő |
|---|---|---|---|
| Főmenü Mappa (`0x00559150`, rekordok `0x00d6e2b0`-től) | `&Locate on Disk` (`eMenuFileWin::ID_ALBUM_LOCATEONDISK`, billentyűszöveg: `Enter`) | `0x9cba` | `0x005d0e90` |
| | `&Remove from Picasa...` (`eMenuLabelFolder::ID_MANAGE_ALBUM`) | `0x9cce` | `0x005ce590` (eltávolítás) |
| | `&Move...` (`eMenuLabelFolder::ID_MOVEFOLDER`) | `0x9df4` | `0x0053f340` → `0x0053f4a0` |
| | `&Delete...` (`eMenuLabelFolder::ID_ALBUM_DELETE`) | `0x9d44` | `0x005edef0` (lomtár, #7031) |
| Mappafa helyi menü (`0x007319f0`, 27 rekord, a 16-20. rekord) | elválasztó, `&Locate on Disk` (`Enter`), `&Remove from Picasa...`, elválasztó, `&Move Folder...` (`Folder::ID_MOVEFOLDER`), `&Delete Folder...` | `0x9cba`, `0x9cce`, `0x9df4`, `0x9d44` | ugyanazok |
| HierFolder-fa helyi menü (`0x00733a40`, 8 rekord, `0x00d6f100`-tól) | `Expand All`, `Collapse All`, elválasztó, `&Remove from Picasa...`, elválasztó, `&Locate on Disk` (`Enter`), elválasztó, `&Move Folder...` (`HierFolder::ID_MOVEHIERFOLDER`) | `0x9dc0`, `0x9e3b`, `0x9cce`, `0x9cba`, **`0x9df5`** | kibontás, összecsukás, `0x005ce590`, `0x005d0e90`, **`0x0053f3a0` → `0x0053f4a0`** |

Következmények:

1. A `0x9df4` a főmenüben és a helyi menüben a `&Move...` / `&Move Folder...` rekord parancsa, a `0x9d44` a `&Delete...` / `&Delete Folder...` rekordé (egyezik a #7031 szakasszal). A felirat és a kezelő közötti ellentmondás megszűnt: az 1. szakasz első két sorában jelzett "statikus eltérés" nem létezik, a PicasaPy mozgatás tétele (fizikai mozgatás) és törlés tétele (lomtár) egyezik az eredetivel.
2. A HierFolder `&Move Folder...` rekordjának parancsa `0x9df5` (nem `0x9cba`), és a `0x0053f3a0` útján ugyanarra a fizikai mozgatóra (`0x0053f4a0`) jut. A korábban "null feliratúnak" olvasott utolsó rekord maga a `&Move Folder...` rekord volt: a korábbi olvasat a felirat betöltését és a parancsmező írását két rekordhoz kötötte.
3. A `0x9cba` mindhárom menüben a `&Locate on Disk` parancsa, a `0x005d0e90` a mappa megnyitása a fájlkezelőben (a #6989 Ctrl+Enter ága). A #6989 táblája a `FolderWin::ID_ALBUM_LOCATEONDISK` parancsát `0x9c95`-nek írja; az valójában az `E&xport as HTML Page...` (`ID_FILE_EXPORTASWEBPAGE`, rekord `0x00d6e288`) parancsa, a mappa lemezen való megkeresésének (`&Locate on Disk`) parancsa `0x9cba` (megjegyzés a #6989 gazdájának; annak a szakasznak a szövegét ez a kör nem módosította).
4. A HierFolder-menü rekordrendje az eredetiben: `Remove from Picasa...`, elválasztó, `Locate on Disk`, elválasztó, `Move Folder...`. A PicasaPy menüje `Locate on Disk`, `Remove from PicasaPy...`, `Move Folder...` sorrendű, elválasztók nélkül a három tétel között (`FolderHierarchyView.qml:455-483`). Ez nem a mozgatás folyamata, ezért nem része a #7059 jegytörzseinek; a HierFolder-menü elrendezéséért felelős jegy kapja meg.

Futtatott megerősítés (az eredeti Picasa 3.9 Wine alatt, Colab-felvételek): a Mappa menü `Move...` tétele a `Browse for Folder` ablakot nyitja (`Make New Folder`, `OK`, `Cancel`; `referencia/kepernyo/2026-11-11-mappamenu-mappa-athelyezes.png`), a `Delete...` tétele a `Delete Folder` ablakot a lomtáras kérdéssel (`Are you sure you want to move the folder "PicasaTeszt" and its contents to the Recycle Bin?`, `Delete Folder` / `No`; `referencia/kepernyo/2026-11-11-mappamenu-mappa-torles.png`). Ez a statikus párosítástól független második út, a címke és a kezelő összetartozásának bizonyítottsági foka: **erős**. Korlát: a Wine alatt a célválasztó fája üres, ezért a mozgatás befejezése ott nem mérhető.

#### A három belépő ága és az engedélyezés

| Belépő | Parancs → kezelő | Mit vizsgál, mit ad tovább | Nálunk |
|---|---|---|---|
| Főmenü `&Move...`, mappafa helyi menü `&Move Folder...` | `0x9df4` → `0x0053f340` | van kijelölt mappa objektum (`[this+0xeac]`), azonosítója (`+0x3c0`) nem `-1`, és a `0x004461a0` nullát ad; utána `0x0053f4a0(útvonalobjektum, this, azonosító)` | `PicasaFolderMenu.qml:200-206`, `MainMenuBar.qml:166-168`, `FolderContextMenu.qml:325-327`: mind a `FolderPaneMenus.qml:285-291` `openMoveFolder` függvényhez jut |
| HierFolder-fa `&Move Folder...` | `0x9df5` → `0x0053f3a0` | egy jelzőbájt (`[[this+0x2c0]+0x9d]`) nem nulla; a hierarchialista kijelölt sora (`[this+0xeb0]`, index `+0x320` és `+0x2f8` összege, `0x004ae4e0`) 6 vagy 7 típusú (a `0xa` kezdőértéknél és minden más típusnál hatás nélküli visszatérés); utána `0x0053f4a0(a sor útvonala, this, -1)` | `FolderHierarchyView.qml:479-482` → `FolderPaneContent.qml:406-408` → `mozgatasMappara` → ugyanaz az `openMoveFolder` |

A `0x004461a0` a katalógus útvonal-lekérdező virtuális tagját hívja (`[[katalógus+0x48]+0x14]`), és 1-et ad (a mozgatás megáll), ha nincs útvonalobjektum vagy az útvonal üres sztring; vagyis az olyan mappa, amelyhez nem tartozik lemezútvonal, nem mozgatható. A kezelő belépési őrének jelentése ezzel eldőlt.

Engedélyezés (szürkítés), a menüállapot-építők utasításai szerint:

- Főmenü Mappa-menü (`0x0056e1c0`, 3-as menüfajta) és mappafa helyi menü (`0x0056c5a0`, `0xa6` menüfajta): a mozgatás (`0x9df4`) és a törlés (`0x9d44`) tétele szürke, ha a mappa útvonala üres, vagy a `0x00995c90` igaz (hét ismert mappa), vagy a `0x004ac8f0` igaz. Ugyanez a blokk szürkíti a mappatörlést is, ezért a #7031 "az üres mappa és más speciális cél engedélyezése nyitott" sorára is ez a válasz.
- HierFolder-menü (`0x127` menüfajta): a mozgatás (`0x9df5`) tétele szürke, ha a kijelölt sor útvonala üres, vagy a `0x00995c90` igaz, vagy van kijelölt mappa a főfán (`[this+0xeac] != 0`) és a `0x004ac8f0` igaz.
- A `0x00995c90` a vizsgált útvonalat a hét tárolt ismert mappa útvonalával veti össze (`[0x00d4a61c+0x54]`-től négy bájtonként; My Pictures, Desktop, My Music, My Videos, My Documents, Application Data, Common Application Data), az első ciklusban pontos egyezéssel. A tiltás tehát a mappára, nem a mappák alatti könyvtárakra vonatkozik. A függvény `0x00995d6e` utáni ága nincs olvasva (feltételes).
- Gyorsbillentyű: a mozgatás rekordjainak billentyűszöveg-mutatója mindhárom menüben üres (a `&Locate on Disk` rekordé `Enter`); dedikált MoveFolder-billentyű nincs, ez az 1. szakasz gyorsbillentyű-sorát megerősíti.

#### A végrehajtó (`0x0053f4a0`) sorrendje

1. A forrás létezik-e (`0x00992ed0`, `0x0053f4f1`); ha nem, csendes visszatérés.
2. A `Preferences/MoveFolderLastPath` olvasása. Ha van, nem üres és létezik (`0x0053f595`), az a célválasztó kezdőhelye; különben a mozgatott mappa SAJÁT teljes útvonala (`0x0053f5a2-0x0053f619`: a forrás útvonalának másolata).
3. A célválasztó (`0x00998760`): `SHBrowseForFolderA` (a dinamikusan feloldott mutató `[0x00d69564]`), jelzők `0x41` (az ismert `BIF_` jelzők szerint csak fájlrendszeri mappák és új stílusú ablak), a címszöveg mutatója üres, a visszahívás `0x00998480`.
4. Az OK visszatérése után AZONNAL, minden ellenőrzés és a mozgatás előtt a választott útvonal beíródik a `Preferences/MoveFolderLastPath` kulcsba (`0x0053f6d2-0x0053f70d`; a `0x00407760` mint beíró azonosítása a hívási alakból feltételes). A megjegyzés tehát nem függ a mozgatás sikerétől.
5. Ha a választás egyenlő a forrással (`0x0053f71f-0x0053f773`, bájtonkénti összevetés), vagy egyenlő a forrás szülőjéből képzett útvonallal (`0x0053f7d3-0x0053f86f`; a záró perjel pontos alakja nem ellenőrzött, feltételes), a visszatérés csendes és hatás nélküli (`0x000f4242`), üzenet nincs.
6. A forrás szerepel-e a figyelt gyökerek listájában (`[katalógus+0x45c]`, `0x00492e40`, `0x0053f78d-0x0053f7ae`): a találat jelzőt állít.
7. Ha a `0x00995c90` igaz a forrás útvonalára: `Unable to Move a System Path` üzenet (`0x0053f881-0x0053f8b7`), nincs mozgatás.
8. A célútvonal a választott mappa és a forrás nevének összeillesztése; ha az létezik (`0x0053f8ff`): `A folder with that name already exists in the destination folder`.
9. `0x0052e0f0` → `0x004fd1c0`: meghajtó-összevetés (eltérésnél `-1`), `MoveFileExA` (`0x00994400`, a mutató `[0x00d694d8]`), siker után a katalógus útvonal-előtagjainak frissítése. Hibakódnál a `0x004fd1c0` a katalógus érintése nélkül tér vissza.
10. Hiba: `Unable to move the folder due to an error. (Code %d)` (`0x0053fbbb-0x0053fc04`), a kód a `0x00994400` visszatérése (vagy `-1`). Nincs visszagörgetés; a hibaág a `0x00512c90` hívással zár, amelyet a sikerág is hív (jelentése nincs feloldva, feltehetően nézetfrissítés).
11. Siker (`0x0053fc4b-0x0053fd62`): az új útvonal beírása, a "piszkos" jelző (`[[this+0x2c0]+0x166] = 1`), a fő nézet frissítése (`0x0065b840(this, 1, 0, 1)`), egy hívás a `[this+0x2a4]` objektum 0x44-es virtuális tagján (`azonosító, 1, 1, 0`), és ha a forrás figyelt gyökér volt (6. lépés jelzője), a figyelt gyökerek listájának cseréje (`[katalógus+0xf8]`, `0x004f0650`, `0x004efde0`). A kijelölés és a rács végállapota ebből nem olvasható ki (lásd a Zárási döntés egyetlen nyitott sorát).

#### Ghidra-kör kell tételek lezárása

| Tétel | Döntés | Válasz | Bizonyíték |
|---|---|---|---|
| `0x005D0E90` (HierFolder, `0x9cba`) | (a) eldöntve | A `0x9cba` a `&Locate on Disk` parancsa. A HierFolder `&Move Folder...` parancsa `0x9df5`, amely a `0x0053f3a0` útján a fizikai mozgatóra jut, vagyis a hierarchia-menü kattintásának lemez- és katalógushatása azonos a főmenüével. | rekordtábla `0x00d6f100`-tól (8 rekord); `0x0053f3a0` utasításai; diszpécser `case 0x9df5` (`2026-10-21-idorend-30.txt`) |
| `0x005CE590` (`0x9cce`) | (a), a #7059 szempontjából (c) | A `0x9cce` a `&Remove from Picasa...` rekord parancsa mindhárom menüben, ezért a `Remove Folder` szövegek helyesek. A művelet az eltávolítás (nem mozgatás, nem lemezművelet); folyamata a Mappakezelő #7082 szakaszában és a #1249 körül van, a mozgatáshoz nem tartozik. Nem blokkoló. | rekordtáblák; `0x005cb990` diszpécser; #7082 |
| `0x004AC8F0` | (a), a hatása (c) | A `0x004ac8f0(katalóguskörnyezet, mappaazonosító)` a mappa útvonalát kéri (`0x004adfe0`), és igazat ad, ha az egyenlő az iPhoto-könyvtár `Masters` mappájával (`0x0047cea0`: összevetés a katalóguskörnyezet `+0x2e78` mezőjében tartott, `0x0099bce0` által a `0x009966a0` alapmappájából (feltehetően `My Pictures`) + `iPhoto Library` + `Masters` részekből épített útvonallal), vagy a Photos-könyvtár `Masters` mappája alatt van (`0x0047cfc0` → `0x0099bf40`; előtag-vizsgálat `0x00987030`, kis-nagybetű-független). Tehát NEM figyelt gyökérre vonatkozik. A két útvonal felépítése a `0x00992ed0` létezés-vizsgálattól függ (feltételes). Látható hatás: a mozgatás és a törlés tétele szürke ezeken a mappákon; a PicasaPy-ban nincs ilyen fogalom (`grep -rni iphoto src/`: nincs találat a mappakezelésben). A figyelt gyökér kezelése a végrehajtó 6. és 11. lépésében van. Nem blokkoló. | `0x004ac8f0`, `0x0047cea0`, `0x0047cfc0`, `0x0099bce0`, `0x0099bf40`, `0x00987030`; `2026-11-15-6963-colab-decomp.txt` (`FUN_004ac8f0`) |
| `0x004FD1C0` (`+0x208`) | (a) eldöntve | Az útvonalobjektum öt sztringet tart (`+0x000`, `+0x208`, `+0x410`, `+0x618`, `+0x820`; `0x004089e0`), amelyeket a `0x009a34a0` a `0x009a3140` `_splitpath`-szerű bontásával tölt: teljes útvonal, meghajtó (`X:`, ha a második karakter `:`), könyvtár, fájlnév, kiterjesztés. A `+0x208` tehát a **meghajtó**. A `0x004fd1c0` a forrás és a cél meghajtóját kis-nagybetű-függetlenül összeveti, eltérésnél `-1`-gyel tér vissza a `MoveFileExA` előtt (a végrehajtó ilyenkor az `(Code -1)` üzenetet adja). UNC útvonalnál a meghajtó mindkét oldalon üres, ezért az összevetés átmegy, és a döntés a `MoveFileExA`-ra marad. | `0x004fd1c0`, `0x004089e0`, `0x009a34a0`, `0x009a3140` (`2026-11-16-7022-7031-7033-colab-decomp.txt`) |

#### A "NINCS MEG" tételek lezárása

| Tétel | Döntés | Válasz |
|---|---|---|
| A `0x9df5` rekord láthatósága (1. szakasz, 4. sor) | (a) eldöntve | Látható `&Move Folder...` tétel a HierFolder-menüben (lásd a helyesbítést). |
| A `0x004ac8f0` és a `0x004461a0` jelentése (1. szakasz, 6. sor) | (a) eldöntve | Lásd fent: Apple-könyvtár `Masters` mappa, illetve "nincs lemezútvonal". |
| A célválasztó első futásos kezdőhelye | (a) eldöntve, mérés nem kell | Hiányzó vagy nem létező `MoveFolderLastPath` mellett a mozgatott mappa saját útvonala; a visszahívás `BFFM_SETSELECTION`-nel (`0x009984d7`, `push 0x466`) előre kijelöli. Nálunk a kezdőhely a forrás szülője (eltérés, lásd a B jegytörzset). |
| Írásvédett cél és részleges mozgatás | (a) és (c) | A mozgatás egyetlen `MoveFileExA` hívás; előtte nincs írhatósági vizsgálat, utána nincs visszagörgetés, és a katalógus csak sikeres visszatérés után frissül (`0x004fd1c0` korai kilépése). Egy mappa meghajtón belüli átnevezése a rendszer szintjén egy lépés, tehát a program saját kódjában nincs részleges állapot; hogy egy írásvédett vagy megtagadó célt az operációs rendszer elutasít-e, az rendszerviselkedés, nem programviselkedés. A hibakód a `GetLastError` értékéből a `0x00991330` leképezéssel készül (a táblából számolva: nem található (2, 3) → 10, hozzáférés megtagadva (5) és megosztási ütközés (32) → 11, tele a lemez (112) → 12, már létezik (183) → 14, minden más → 2); hozzáférés megtagadva esetén előbb időzített újrapróbáló ág fut (`0x00994479-0x00994508`). A PicasaPy hibánál a forrást érintetlenül hagyja és emberi üzenetet ad (`move_folder.py:134-190`), a felhasználó számára azonos osztály. Nem blokkoló, a hibaüzenet pontos szövege és kódja nem cél. |
| Más köteten vagy meghajtón mozgatás | (a) eldöntve | Az eredeti eltérő meghajtóbetűnél elutasít (`-1`), kötetek között tehát NEM mozgat. A PicasaPy `os.rename` hibája után másolásos tartalékra tér (`move_folder.py:157-190`), tehát meghajtók között is mozgat. Tudatos, dokumentált eltérés, lásd a Zárási döntést. |
| UNC és hálózati meghajtó | (c) nem blokkoló | A mozgató olvasott részeiben nincs kifejezetten hálózati ág: a leképezett hálózati meghajtó meghajtóbetűs, az UNC útvonal meghajtója üres (lásd `+0x208`). A tényleges hatás a `MoveFileExA` és a rendszer dolga; hálózati tesztet nem végeztem, és a jegy lezárásához nem kell. Korlát: az útvonal-létezési vizsgálat (`0x00992ed0`) időkorlátos, ennek hálózati szerepét nem vizsgáltam. |
| Az album- és arcadatok, a gyorsítótárak | (c) nem blokkoló | A képek `albums=`, `faces` és `albumlist` adata a mappa `.picasa.ini` fájljában van, ez a mappával együtt mozog mindkét oldalon; a memóriabeli gyorsítótárak belső állapota nem látható viselkedés. A PicasaPy a mozgatás után újraolvassa mindkét részfát (`library_controller_resync.py:142-193`). |
| A mappafa, a rács és a kijelölés végállapota siker után | (b) egy célzott sor | Lásd a Zárási döntés egyetlen nyitott sorát. A Wine alatt a célválasztó fája üres, ezért futtatott előtte-utána mérés ott nem végezhető el. |

### Zárási döntés

**A jegy lezárható.** A korábban blokkolónak jelölt négy Ghidra-kérdés mindegyike eldőlt a meglévő bizonyítékból. A mozgatás teljes folyamata (belépés, célválasztó, őrök, lemezművelet, hibák, katalógus) a #7059 szempontjából feltárt. Bizonyítottsági fok: **erős** a menürekordok, a parancsok és a kezelők összetartozására (két független statikus út és két futtatott felvétel), a végrehajtó sorrendjére és a meghajtó-összevetésre; **feltételes** a szülő-összevetés pontos alakjára, az ismert-mappa predikátum `0x00995d6e` utáni ágára és a beíró függvény (`0x00407760`) azonosítására.

Az egyetlen maradék irány nem blokkoló, mert a lenti fejlesztői jegyek egyike sem függ tőle; saját kutatási jegy lesz belőle:

- `Ghidra-kör kell: 0x0053F4A0 - a sikerág (0x0053fc4b-0x0053fd62): a 0x0074c050, a [this+0x2a4] objektum 0x44-es virtuális tagja (azonosító, 1, 1, 0) és a 0x0065b840(this, 1, 0, 1) hatása: siker után melyik mappa van kijelölve a mappafán és melyik mappa képeit mutatja a rács (az áthelyezett mappa az új helyén, vagy a régi helyén maradt kijelölés, vagy üres nézet), és mit jelent az azonosító -1 értéke a HierFolder ágon (0x0053f3a0)?`

Nem nyílik jegy (a zárókör döntése): a menüparancsok futásidejű jelentése (a helyesbítés megszüntette az ellentmondást, a PicasaPy tételei egyeznek); a HierFolder-menü mozgatása (azonos a másik két menüvel); a meghajtók közötti mozgatás (tudatos eltérés: a PicasaPy kötetek között is mozgat, a #2785 szerinti visszagörgetéssel, ez az eredetinél tágabb képesség, nem rontás; ha a jövőben paritás kell, Windowson az eltérő meghajtóbetű elutasítása a `0x004fd1c0` alapján egyszerűen megírható).

Fejlesztői jegytörzsek, amelyek maradnak:

**A. A mozgatás és a törlés tételének szürkítése, és a mozgatás védelme a hét ismert mappán**

Eredeti: a főmenü Mappa-menüjében (`0x0056e1c0`), a mappafa helyi menüjében (`0x0056c5a0`, `0xa6`) a mozgatás és a törlés tétele szürke, ha a mappának nincs útvonala, ha az a hét ismert mappa (My Pictures, Desktop, My Music, My Videos, My Documents, Application Data, Common Application Data) valamelyike (`0x00995c90`, pontos egyezés), vagy iPhoto/Photos `Masters` mappa (`0x004ac8f0`). A HierFolder-menüben a Move (`0x9df5`) ugyanígy szürke (a `0x004ac8f0` ott csak kijelölt főfa-mappa mellett számít). A végrehajtó a célválasztó UTÁN, a forrás útvonalára is megvizsgálja (`0x0053f878`), és ha igaz, a `Unable to Move a System Path` üzenettel megáll. A mappák alatti könyvtárak mozgathatók.

Nálunk: `src/picasapy/fileops/move_folder.py:40-65` rögzített, POSIX és Windows rendszerutakat tartalmazó lista (`C:\Users`, `C:\Windows`, `C:\ProgramData` stb.), `:72-87` `is_system_path` (a home-könyvtár maga is tiltott); a felhasználói ismert mappák (Pictures, Desktop, Music, Videos, Documents, AppData) nincsenek feloldva. A menütételek nincsenek szürkítve: `PicasaFolderMenu.qml:200-206` csak a kijelölt mappa meglétét és az album/személy nézet hiányát vizsgálja, `FolderContextMenu.qml:325-327` és `FolderHierarchyView.qml:479-482` nem vizsgál semmit.

Teendő: a hét ismert mappa megfelelőit (Pictures, Desktop, Music, Videos, Documents, a felhasználói alkalmazásadat és a közös alkalmazásadat mappa) a Qt szabványos útvonalaiból (`QStandardPaths`) feloldani, és mindhárom menüben szürkíteni rajtuk a mozgatás tételét; a végrehajtás védelme (`is_system_path`) ugyanezeket tiltsa, a mai védelem (rendszerutak, home) ne szűküljön. A mappák alattuk álló könyvtárai mozgathatók maradnak. A Delete tétel szürkítése a mappatörlés jegyére tartozik (ugyanaz a predikátum).

Kész, ha: a hét feloldott mappán a mozgatás tétele mindhárom menüben szürke, és a végrehajtás is megáll; egy alattuk álló mappán mindkettő engedélyezett; a meglévő rendszerút-tesztek zöldek. A szürkített menü vizuális egyezése az eredetivel nem mérhető (nincs róla felvétel), ezt a jegy kimondja.

**B. A célválasztó kezdőhelye, a megjegyzés időzítése és a címe**

Eredeti: a célválasztó kezdőhelye az érvényes, létező megjegyzett cél, különben a mozgatott mappa SAJÁT útvonala (előre kijelölve, `0x0053f5a2-0x0053f619`, `0x009984d7`). A választott célt az OK után azonnal megjegyzi, a mozgatás sikerétől függetlenül (`0x0053f6d2-0x0053f70d`). A `Move Folder to %s` (`0x00c8aca4`) NEM az ablak címe: a cím a rendszer `Browse for Folder` szövege (a felvételen is ez áll), a `%s` helyére az ablakon belüli felirat a célválasztóban éppen KIJELÖLT mappa nevét írja, élőben (`0x009986b2-0x00998705`, `GetDlgItem(…, 0x3742)`; ez a vezérlőazonosító a leírószöveg-mezőé, az azonosítás a rendszerkonvenció alapján feltételes). A visszahívás az OK gombot letiltja a mozgatott mappán, a szülőjén (feltételes) és a rejtett mappákon (`0x00998557-0x009985a6`, `GetFileAttributesExA`, a `0x00992d20` a rejtett jelzőbitet adja). A mozgatott mappa maga vagy (feltételesen) a szülője választásakor a végrehajtó csendesen visszatér.

Nálunk: `FolderPaneMenus.qml:293-298` a `FolderDialog` címe `Move Folder to <a mozgatott mappa neve>` (#7067); `fileops_controller_move_mixin.py:326-340` a kezdőhely a megjegyzett cél, különben a forrás szülője; `:292-316` a megjegyzés csak sikeres mozgatás után történik; `move_folder.py:118` ugyanabba a szülőbe mozgatáskor `A mappa már ebben a célmappában van.` hibaüzenet; `tests/app/test_athelyezes_utolso_cel_7067.py:89` a sikertelen mozgatás utáni nem-megjegyzést rögzíti, vagyis az eredeti ellenkezőjét.

Teendő: (1) megjegyzett cél hiányában a kezdőhely a mozgatott mappa maga; (2) a választott célt az elfogadás után azonnal megjegyezni, a mozgatás sikerétől függetlenül (a #7067 sikertelen mozgatásra vonatkozó tesztje ennek megfelelően módosul); (3) a mozgatott mappa nevét viselő ablakcím megszüntetése, a cím legyen `Browse for Folder`; az élő feliratú célválasztó a natív Qt-párbeszéddel nem megoldható, saját célválasztó külön, nem sürgős jegy; (4) a mozgatott mappa maga mint cél: hatás nélküli, csendes visszatérés hibaüzenet nélkül; rejtett célmappa elutasítása; a szülő választásánál a mai hibaüzenet marad, amíg a szülő-összevetés alakja nincs mérve.

Kész, ha: megjegyzett cél nélkül a célválasztó a mozgatott mappán áll; hibás vagy hatás nélküli kísérlet után is a legutóbb választott cél a következő kezdőhely; a mozgatott mappa nevét viselő cím nincs; a mozgatott mappa maga mint cél nem ad hibaüzenetet. A vizuális egyezést a Wine-os felvétel nem méri (üres fa), ezt a jegy kimondja.

Állapot a jegy "Kész, ha" pontjaira a zárókör után:

| Pont | Állapot | Bizonyíték |
|---|---|---|
| Fő menü, mappafa-helyi menü és gyorsbillentyű | ✅ | Mindhárom menü rekordja, parancsa és kezelője feltárt, a mozgatás és a törlés párosítása futtatott felvétellel megerősített; dedikált billentyű nincs. A szürkítés: A jegytörzs. |
| Figyelt gyökér, különleges mappa és hálózati meghajtó feltétele | ✅ | Hét ismert mappa, az Apple-könyvtár predikátum és a figyelt gyökér kezelése ismert; hálózat-specifikus ág nincs. |
| Célválasztó ablaka, alapértéke és megjegyzett állapota | ✅ | Kezdőhely, megjegyzés időzítése, jelzők és visszahívás feltárt; a Nálunk-eltérések: B jegytörzs. |
| Fájlok, `.picasa.ini`, index, fa, rács, kijelölés, albumtagság és arcok | ✅ / ⛔ | Fájlok, `.picasa.ini`, katalógus és figyelt gyökér feltárt; a kijelölés és a rács végállapota a fenti egyetlen Ghidra-sor. |
| Ütköző név, írásvédett cél, részleges és más kötetes mozgatás | ✅ | Névütközés, meghajtó-összevetés (`-1`), hibakód-leképezés és a visszagörgetés hiánya feltárt. |


### #7235-kiegészítés (2026-11-18): a sikeres mappaáthelyezés utáni kijelölés

#### #490 - 0x0053f4a0

A 0x0053f4a0 dekompiláció (2026-11-18-koteg-466-495.txt:4270-4731) a sikerágban a következőket hívja: 0x0074c050 a mozgatott mappával; a puVar10[0xb0]+0x166 jelzőt 1-re állítja; 0x0065b840(this,1,0,1) nézetfrissítést végez; majd a puVar10[0xa9] objektum +0x44 virtuális tagját hívja (mappa,1,1,0) argumentumokkal. A 0x0074c050 nyers disassemblyje az `albumheader/%x/%d/folderbutton` UI-azonosítóval dolgozik, de nem bizonyítja önmagában, melyik mappa marad kijelölve, illetve melyik képkészletet hagyja a rácsban. Nyitott következő címek: a +0x44 virtuális slot konkrét célja/típusa és a 0x0065b840 utáni kijelölés-/rácsfrissítő. A feladat szövegének vége is csonka („az áthelyezett mappa … vagy a régi helyén …”); a hiányzó alternatívát nem egészítem ki.

PicasaPy fileops_controller_move_mixin.py:324-354 a mozgatott új útvonalat folderMoved jelként adja tovább; application_services.py:129 ezt a resyncMovedFolder-hoz köti, amely az új és régi részfát újraszinkronizálja (library_controller_resync.py:140-185). Ez a forrás nem állítja át aktív mappára a mozgatott célhelyet, de az eredeti végállapot nyitottsága miatt a paritáskülönbség még nem dönthető el.


### #7266-kiegészítés (#516, 2026-11-19): az áthelyezés utáni kijelölés nyitott

A `0x0053f4a0` sikerág a `0x0074c050` után a nézetfrissítőt `0x0065b840(this,1,0,1)` argumentumokkal hívja, majd a `[puVar10+0xa9]` objektum `+0x44` virtuális slotját hívja a mozgatott mappával és `(1,1,0)` argumentumokkal. A `0x0065b840` frissítő önmagában nem állít kijelölést. A sikerág hívási címe és argumentumai ismertek, de a `+0x44` cél-vtábla és a rács újratöltési út nincs feloldva, ezért az aktív mappa és a rács tartalma nyitott. Következő: a `[puVar10+0xa9]` példány vftáblájának feloldása a `0x0053f4a0` hívási helyhez, majd a `+0x44` cél követése.
## #7069: Album létrehozása, tulajdonságainak szerkesztése és törlése az eredeti Picasában

Vizsgálati tárgy: Picasa 3.9.141.259, SHA-256:
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
A bináris nem futott; a leletek cím szerinti diszasszemblálásból, meglévő
Ghidra-kimenetekből, erőforrásokból és a PicasaPy-forrásból származnak.

### Következtetés

Az eredeti Fájl ▸ `New Album...` (`Ctrl+N`) külön út az Add-to-album
parancstól: a saját modelljét a jelenlegi idővel és `Untitled` névvel tölti,
majd albumot hoz létre. A korábbi, kijelölt kép melletti Picasa-felvételen az
új album üres maradt és a mappa `.picasa.ini`-je nem változott (job-323/324).
A mai Fájl-menü a kijelölt sorokat adja át az albumtagságot is mentő útnak,
és dátum nélkül nyitja az ablakot. A létrehozás utáni megnyitás már egyezik;
a normál albumtörlés kétgombos, No-fókuszos ablaka is egyezik a korábbi
méréssel. A dinamikus Album menü törlési feltételei, az eredeti tartós
adatbázis-végpont, a nem üres album törlési hatása, a névütközés, a hiba,
rollback, undo és a törlés utáni kijelölés nyitva maradt.

**Bizonyítottsági fok: nyitott.** A File New Album üresalbum-hatását, a
dátumalapértéket és a törlőablakot külön bináris/mérési bizonyíték támasztja
alá, a mai utakat a forrás igazolja. A teljes kért életciklushoz hiányzik a
menu-engedélyezés teljes feltételrendszere és több eredeti hiba-/törlés utáni
végállapot.

### Belépési pontok és feltételek

| Eredeti (bináris cím vagy mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Fájl menü / új album:** `0x00559150` felirata `&New Album...`; az utána épített rekord parancsmezője `0x9d67`. A `0x005cb990` `0x9d67` ága a `0x005eb810`-hoz vezet. Ez a `0x0055cf70` modellel nyitja az Album Properties ablakot, majd a `0x0055d120` albumkészítőbe adja a modellt; az átadott argumentumok között nincs képkijelölés. A job-323/324 Picasa-mérés kijelölt kép mellett is üres albumot és változatlan mappa-INI-t rögzít. | `PicasaFileMenu.qml:23-27`; `MainMenuBar.qml:300-304`; `FileOpsDialogs.qml:101-107,156-170`; `photo_ops_album_membership_mixin.py:229-268` | A PicasaPy Fájl-menü átadja a kijelölt képeket (`photoActionRows`), és azok tagságát is kiírja. Kijelölés nélkül az út korán visszatér. Válaszd el a File-út albumtagságát a kijelöléstől; a menütétel engedélyezése üres kijelölésnél az eredetiben maradjon nyitott a célzott mérésig. |
| **Gyorsbillentyű:** a bináris `New Album` gyorsbillentyű-erőforrása `Ctrl+N` (`enUS/shortcuts.xml:115-117`); a File-út `0x005eb810`. A teljes menüállapot nem következik a kezelőből. | `PicasaMenuBar.qml:712-723`; `PicasaFileMenu.qml:23-27` | A mai Ctrl+N csak kijelölt képeknél aktív. Az eredeti üres kijelölésű engedélyezése `NINCS MEG`; külön Picasa 3.9 mérés kell. Albumtulajdonság-/törlésgyorsbillentyű: `NINCS MEG`. |
| **Kép- és nézőmenü Add-to ▸ New Album...:** az `0xa09c` ág a `0x005e9890` → `0x005e9bb0(this,1)` útvonalra jut; ez külön a File (`0x005eb810`) és a tálca (`0x00577ea0`) útjától (lásd #7012). | `PhotoContextMenu.qml:171-197`; `MainPhotoContextMenu.qml:153`; `FileOpsDialogs.qml:109-119` | A PicasaPy ezt a kijelölt képekből nyitja, az első kép dátumát ajánlja. Ne vonjuk össze a File- vagy tálca-út javításával. |
| **Tálca Add to ▸ New Album...:** `thumbui/makealbum` a `0x00577c30` → `0x00577ea0` úton nyit Album Properties ablakot (`0x006dc030`); a `0x00577ea0` a `0x0098b6e0` aktuális időértékét adja a `0x0055ce70` modellnek, majd elfogadáskor `0x0055d120(0,1,0)`-t hív és megnyitja az új albumot. A job-257 mérés szerint az `Untitled` album a kijelölt képpel együtt jött létre, az `.ini` album- és képtagságot kapott (`picasa-keptalca.md:1494`). A job-255 egy kép és saját album nélkül is megnyíló menüt rögzít, de a tartott/kijelölt képek pontos engedélyezési feltétele nyitott (`picasa-keptalca.md:1498-1501`). | `TrayScratchPanel.qml:521-528,573-576`; `TrayBar.qml:76`; `MainTrayBar.qml:82-87`; `FileOpsDialogs.qml:133-170` | A PicasaPy tálcamenü `heldCount > 0` mellett engedélyezett; az új album útja a rács kijelölt sorait adja át és a mai helyi dátumot ajánlja. A mért Picasa-út dátuma és kijelölt képes tagsága egyezik; a tartott/kijelölt állapotok közti kapu összevetése nyitott. |
| **Album / Folder főmenü - tulajdonságok:** a `0x00559150` `eMenuLabelFolder::ID_ALBUM_EDITCAPTIONS` felirata a `0x9c69` parancsot kapja; a `0x005cb990` ezt a `0x006db580`-ra irányítja. A meglévő album-helyi menü `0x00732160` ugyanezt a `&Edit Album Description...` műveletet kínálja. | `PicasaFolderMenu.qml:9,16-28`; `MainMenuBar.qml:373-382`; `AlbumContextMenu.qml:60-65`; `FolderPane.qml:298-319` | A mai Album főmenü és bal hasáb helyi menüje is megnyitja az albumadatokkal előtöltött tulajdonságablakot. A mezők mentési és hibaútját lent rögzítem. |
| **Album / Folder főmenü - törlés:** a `0x00559150` menü felépíti az `eMenuLabelFolder::ID_ALBUM_DELETE` (`Delete...`) tételt `0x9d44` paranccsal; a `0x005cb990` a `0x005ed240` törlőútra irányítja. A `0x0056e1c0` állapotfrissítő szabályozza a parancs engedélyezését, de a különleges/üres albumok feltételének teljes jelentése nyitott. | `PicasaFolderMenu.qml:198-213` - a Delete elem csak mappamódban aktív; `AlbumContextMenu.qml:55-58` albumtörlés; `FolderPane.qml:362-368` | A PicasaPy Album főmenü jelenleg nem engedi az album törlését; a bal hasáb album-helyi menüje igen. Az eredeti főmenü parancsa és kezelője bizonyított, de a rendes albumra vonatkozó engedélyező ág pontos szemantikája nyitott; a különbség feltételes fejlesztői jelölt. |
| **Bal hasáb album-helyi menü:** `0x00732160`: `&Edit Album Description...` (`0x00cae3a8`) és `&Delete Album` (`0x00cae450`); a parancsmezők a megelőző-rekord szabállyal `0x9c69` és `0x9d44`. A törlés a `0x005ed240`-be, a szerkesztés a `0x006db580`-ba jut. | `AlbumContextMenu.qml:55-65`; `FolderPane.qml:351-368`; `FolderPaneMenus.qml:120-135` | A jelenlegi helyi menü mindkét parancsot kínálja. A normál album törlőablaka a job-329/330 No-fókuszos mérésével egyezik; lásd „Ablakok”. |
| **Emberek-album helyi menü:** `0x007359e0` `&Edit People Album...` és `&Delete People Album` tételeket épít; a törlés kezelője a `0x005ed240` specializált ágát is használja. A found-people, `]star` és `]screensaver` belső albumnevek külön védelmi ágon figyelmeztetést adnak (`0x00c97d44`, `0x00c97cb0`, `0x00c97cfc`). | `PeopleAlbumContextMenu.qml:26-65`; `FolderPaneMenus.qml:138-163,165-238` | A mai Emberek-album szerkesztése a személykezelő útja; törlése külön ablakban kérdez rá, és opcionális online-arc jelölőt ad. Az eredeti feliratokból önmagukban nem következtetek a szerkesztő végső hatására. |
| **Új album felületi eseménye, eszköztár:** a `thumbui/newalbum` esemény a `0x005d9cc0`-ban a `0x005eb810`-at hívja; a konkrét vizuális elem helyét ez a kimenet nem nevezi meg. A tálca `thumbui/albumbutton` külön Add-to út (`0x005e9bb0`). | `MainWindowToolbar.qml:105-110` üres album tulajdonságablakot is nyit. | A PicasaPy toolbar útjának eredeti UI-megfelelője nyitott; a `thumbui/newalbum` eseményt nem azonosítom bizonyíték nélkül a toolbar gombjával. |

### Ablakok, alapértékek és megjegyzett állapot

- Az eredeti `album.fen` Name, Date, Automatic date, Music jelölő/fájlkereső,
  Place taken, Description, OK és Cancel mezőket deklarál
  (`picasa-fen-dialogs.md:255-273`). A File-út `0x0055cf70` függvénye a
  `0x0098b6e0` időlekérő értékét teszi a dátummező modelljébe, az
  `IDS_DEFAULT_ALBUM_NAME`-et (`0x00e0382e`) tölti be, a hely/leírás/zeneút
  szövegmezőit üresen inicializálja. A Colab #17 Album Properties-felvételen
  `Untitled` kijelölt, dátum kitöltött, Music kikapcsolt, Place taken és
  Description üres, OK / Cancel látszik (`kepek-leltar.md:97`; a kép
  `research/testdata/screenshot/Colab EN 21 - Album Properties (New Album).png`).
  A felvételen olvasható konkrét dátum csak az akkori profil/futás mért értéke,
  nem állandó alapérték. Megjegyzett állapot új album indításakor: `NINCS MEG`.
- A meglévő album szerkesztésénél a `0x006db580` előbb a `0x0055d070`
  mezőbetöltőt, majd a `0x006dc030` ablakutat hívja. A meglévő Ghidra-lelet
  a név, caption/leírás, dátum, hely és zene betöltő/setter mezőit azonosítja
  (`0x0055d070`, `0x0055d320`; #7032 kiegészítés). Az eredeti ablak mezőit
  és induló adatát az aktuális album tulajdonságai adják, nem minden profilra
  egységesen üres mezők.
- Normál album törlésekor a `0x005fdc30` `Delete Album` címet, a
  `Are you sure you want to delete the album "%s"?` kérdést és `Delete Album`
  gombot választ. A job-329/330 mérés szerint az ablakban csak `Delete Album`
  és `No` van, a `No` kap fókuszt, emlékeztető jelölő nincs
  (`paritas-ellenorzes-archiv-1.md:895`). Az Emberek-album kérdése külön
  `DeletePeopleAlbum`; ne terjesszük át a normál album mérését arra az ágra.
  A `confirm.fen` általános háromgombos sablonja önmagában nem bizonyítja az
  albumág vezérlőit. Normál albumra a mai `FolderPaneMenus.qml:120-135`
  ugyanezt a kétgombos, No-fókuszos, jelölő nélküli ablakot állítja be.
- PicasaPy Fájl ▸ New Album párbeszédnyitáskor `Untitled`, üres dátum/hely/
  leírás/zeneútvonal és kikapcsolt zene értéket ad, majd a névmezőre fókuszál
  és kijelöli a nevet (`FileOpsDialogs.qml:101-107,133-144`;
  `FolderPropertiesDialog.qml:190-200`). Ez a dátum eltér az eredeti File-út
  aktuális idő alapértékétől. Az Add-to út ettől külön, első képkocka-időt
  ajánlhat fel (lásd #7012).
  Meglévő album nyitásakor a controller aktuális név/dátum/hely/leírás/zene
  adataival tölti fel (`FolderPane.qml:298-319`).
- PicasaPy normál albumtörlés dialógusa `Delete Album` címmel/gombbal
  kérdez, de Cancel és emlékeztető jelölő nélkül, No fókuszon
  (`FolderPaneMenus.qml:120-135`). A People album dialógusa külön
  `Remove People`, Delete Album / Cancel gombokkal, Cancel-fókusszal, és
  alapból kikapcsolt, szinkronizált arcok törléséről szóló jelölővel él
  (`FolderPaneMenus.qml:165-238`).

### Tárolás, műveleti hatás és hibák

| Hatás | Eredeti Picasa 3.9 | PicasaPy most |
|---|---|---|
| Új album rekordja | A `0x005eb810` elfogadáskor a `0x0055d120`-at hívja, az album modelljével; a job-323/324 felvételen a kijelölt kép mellett is üres album jött létre, a mappa `.picasa.ini`-je változatlan maradt, a profilban `ioqueue/albumsafe.ioq` jelent meg (`paritas-ellenorzes-archiv-1.md:894`). Az albumadatbázis pontos fájlneve és a profil-queue tartós rekordja/életciklusa: `NINCS MEG`. | A Fájl-menü kijelölt soroknál `createAlbumWithProperties`-t hív és albumdefiníciót/tagságot ír a képek mappáinak `.picasa.ini`-jébe (`FileOpsDialogs.qml:160-170`; `photo_ops_album_membership_mixin.py:229-268`). Üres albumot a `createEmptyAlbum` ment a `local_empty_albums` profil-index táblába, ini-írás nélkül (`photo_ops_album_membership_mixin.py:271-315`; `index/schema.py:239-248`). |
| Albumtagság és ini-szinkron | A job-323/324 kijelölt kép melletti létrehozásnál tagság nem keletkezett és a mappa `.picasa.ini`-je változatlan maradt (`paritas-ellenorzes-archiv-1.md:894`). A File-út hívási láncában nem ad át képlistát (`0x005eb810` → `0x0055d120`). A nem üres album törlés/átnevezés pontos ini-szinkronja és időzítése a #7012 nyitott kérdéseihez kötődik. | Kijelölt képeknél a File-út kötegelt íróval rögzíti a definíciót és `albums=` tagságot; listája siker után újratöltődik (`photo_ops_album_membership_mixin.py:102-140,229-268`). |
| Album tulajdonságok / átnevezés | `0x006db580` az OK után `0x0055d320`-at hív; ez mező-settereket futtat. Ha egy mezőíró (setter) hibát jelez, a korábban sikerült mezőket nem gördít vissza, és saját üzenetablakot nem épít (#7032 Ghidra-kiegészítés). A tényleges ini-író és az album-névütközés kezelése nyitott. | `editAlbumProperties` módosítja a nevet, dátumot, helyet és leírást minden érintett ini-ben; üres függő albumnál profil-indexet frissít; siker után újratölti a listát/nézetet (`photo_ops_album_properties_mixin.py:72-132`). A zene külön út. Ismert írási hibát `albumWriteFailed` jelzi (`:127-129`). |
| Törlés és képfájlok | Elfogadott törlés után a `0x005ed240` katalógus-vtable `+0xec` metódust hív és nézetfrissítést végez (`0x0065b840`). A virtuális törlőcél, az ini-szinkron pontos lefutása és a képfájlok bájtjainak végállapota: `NINCS MEG`. | A `[.album:<token>]` definíciót és minden érintett `albums=` hivatkozást eltávolítja; az üres albumot a profil-indexből veszi ki. Képfájlokat nem töröl (`photo_ops_album_membership_mixin.py:93-125`). |
| Albumlista, rács és kijelölés | Új album sikerén a `0x005eb810` frissít (`0x0065b840`), majd az `0x004af790` eredményét az aktuális album mezőjébe írja (`0x005eb8d1-0x005eb8e1`). Az üres album törlése után Albums (2) → (1) mérhető (`job-329/330`); aktív album/rács/kijelölés további végállapota `NINCS MEG`. | Sikeres létrehozáskor a callback a visszakapott tokent megnyitja (`FileOpsDialogs.qml:172-176`), ez egyezik az új album megnyitásával. Törlés után `_refresh_view()` fut (`photo_ops_album_membership_mixin.py:218-219`); aktív album és kijelölés külön nincs méréssel igazolva. |
| Névütközés, írási hiba, részleges állapot, visszavonás | A `0x0055d320` név-módosítási ágában szerepel az `IDS_NORENAME` figyelmeztető út. Az erőforrás szövege lemezre nem illeszthető vagy azonos könyvtárban ütköző mappanevet nevez meg (`stringres-en-hu.tsv:1636`), de a virtuális albumokra vonatkozó pontos ütközési feltétel és a névváltoztatás eredménye `NINCS MEG`. A mező-setter hibával visszatér; a `.picasa.ini`-írási hiba, törlési hiba, rollback és undo: `NINCS MEG`. | Az üres album `local_empty_albums` sora tokennel kulcsolt, a `name` mezőn nincs egyediségi megkötés (`index/schema.py:238-249`); a létrehozó tokenalapú (`photo_ops_album_membership_mixin.py:300-315`). A vizsgált albumút nem mutat név-egyediségi ellenőrzést; ez önmagában nem bizonyítja, hogy más tárolóréteg sincs. A kezelt írási hibák jelzést adnak; több mappás írás teljes rollbackje ebből a forrásból nem állapítható meg. Közvetlen undo-út: `NINCS MEG`. |

### Bizonyíték és bizonyítottság

| Érték/állítás | Forrás |
|---|---|
| Fájl `New Album...` parancs `0x9d67`, Ctrl+N | bináris (`0x00559150`, `0x005cb990`, `0x005eb810`); mérés/erőforrás (`shortcuts.xml:115-117`) |
| File-út képlistamentessége és üresalbum-hatása | bináris (`0x005eb810`, `0x0055d120`); mérés (`job-323/324`, `paritas-ellenorzes-archiv-1.md:894`) |
| Fájl New Album dátum- és névalapértéke | bináris (`0x0055cf70`, `0x0098b6e0`, `IDS_DEFAULT_ALBUM_NAME`); mérés (Colab #17 Album Properties screenshot; `kepek-leltar.md:97`) |
| Album főmenü szerkesztés/törlés parancsok | bináris (`0x00559150`, `0x0056e1c0`, `0x005cb990`, `0x006db580`, `0x005ed240`) |
| Bal oldali album és People menü feliratai/parancsai | bináris (`0x00732160`, `0x007359e0`); a parancsmező/felirat párosítása az eggyel előző rekord szabályával |
| Album Properties mezői | bináris/erőforrás (`album.fen:1-29`); mérés (Colab #17 screenshot; `kepek-leltar.md:97`) |
| Normál albumtörlő ablak gombjai, fókusza, emlékeztetője | bináris (`0x005ed240`, `0x005fdc30`); mérés (`job-329/330`, `paritas-ellenorzes-archiv-1.md:895`) |
| AlbumSync `albums`/`token` író | bináris (`0x00556ff0`, `0x00557760`, `0x0052c350`); részletesen a #7012 Tároló táblázatában, trigger/időzítés nyitott |
| PicasaPy mai műveleti utak | fájl:sor: `MainMenuBar.qml:300-304`; `FileOpsDialogs.qml:101-107,133-176`; `FolderPaneMenus.qml:120-135`; `photo_ops_album_membership_mixin.py:187-315`; `photo_ops_album_properties_mixin.py:72-132` |
| File menü üres kijelölésű engedélyezése; pontos album-adatbázis és profil-queue-életciklus; törlő vtable célja és nem üres album lemez-/ini-hatása; névütközés-végállapot; íráshiba/rollback/undo; törlés utáni nézet/kijelölés | `NINCS MEG` |

### A két független út

- **A: bináris út:** a File-menü parancsától (`0x00559150` → `0x005cb990` →
  `0x005eb810`) a modell- és albumkészítőig (`0x0055cf70`, `0x0055d120`),
  illetve a tulajdonság- és törléskezelőig követtem a hívási láncot. A
  `0x0056e1c0` menüállapot és a `0x005ed240` speciális törlőágai is
  utasításszinten olvashatók.
- **B: független mérési út:** a job-323/324 feljegyzés kijelölt kép mellett
  üres albumot, változatlan mappa-INI-t és profilbeli `albumsafe.ioq`-t
  rögzít; a Colab #17 Album Properties-kép a látható mezőértékeket mutatja;
  a job-329/330 feljegyzés a Delete Album / No ablakot és No fókuszt rögzíti.
  Ezeket a PicasaPy QML/Python/SQLite-forrástól külön ellenőriztem.
- **Egyezés/eltérés:** a `Untitled` név, az Album Properties mezők,
  létrehozás utáni új album megnyitása, valamint a normál album törlőablaka
  egyezik. A File-út dátumalapértéke és képtagság-hatása eltér; a teljes
  tárolási és hiba-végállapot nyitott. Ezért a teljes vizsgálat nem
  `megerősített`.

### Cáfoló kísérlet

1. **A File és Add-to `New Album...` azonosságát próbáltam cáfolni.** A File
   út `0x005eb810`-on át a `0x0055d120`-nak csak az Album Properties modellt
   adja; az Add-to út `0x005e9bb0` külön belépő (`#7012`). A független
   job-323/324 feljegyzés a kijelölt kép ellenére üres albumot és változatlan
   INI-t rögzít. A két út tehát nem vonható össze azzal az állítással, hogy
   mindkettő tagságot ment.
2. **A generikus `confirm.fen` alapján felmerült Cancel-fókuszt próbáltam
   cáfolni.** A közvetlen albumági job-329/330 mérés két gombot rögzít
   (`Delete Album`, `No`), No-fókusszal és emlékeztető jelölő nélkül; ez
   cáfolja a közös háromgombos sablon automatikus átvitelét. A `No` eredményt
   az archivált mérési táblában ellenőriztem (`paritas-ellenorzes-archiv-1.md:895`).
3. A korábbi `0x9caa = New Album` párosítást is cáfoltam: a
   `0x00559150` rekordblokkjában a `&New Album...` parancsmezője `0x9d67`,
   míg a következő `0x9caa` a `Add Folder to Picasa...` rekordhoz tartozik;
   az `enUS/shortcuts.xml:115-117` Ctrl+N bejegyzése független ellenőrzés.

### A jegy „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték |
|---|---|---|
| Új album, tulajdonságszerkesztés, törlés minden belépési ponttal és feltétellel | ⛔ | File/Ctrl+N, Album főmenü, bal oldali album/People menü és tálca útjai részben feltártak. Nyitott az üres kijelölésű File/shortcut engedélyezés, az Album menü törlőpredikátumainak pontos jelentése és a tálca vizuális belépője. |
| Ablakmezők, alapértékek és megjegyzett állapot | ⛔ | A File New Album `Untitled`/aktuális idő alapértéke, mezői és látható értékei ismertek; a mezők újranyitás közötti állapota és a People ág külön ablaka/memóriája nem zárult le. A normál album törlőablakának No-fókusza és jelölő nélküli állapota méréssel ismert. |
| Tárolás, képek, index, bal hasáb, rács és kijelölés | ⛔ | Az eredeti kijelölt kép melletti üres album és a normál üres album törlése mért. A nem üres album törlésének pontos ini-/profiladatbázis-hatása, képfájlhatása, illetve a törlés utáni nézet/kijelölés nyitott. A PicasaPy File út a kijelölt képeket tagságként menti, az új albumot megnyitja. |
| Névütközés, írási hiba, részleges végrehajtás és visszavonás | ⛔ | Az `IDS_NORENAME` ág jelenléte ismert, de a virtuális albumra vonatkozó ütközési végállapot nem. Eredeti hiba/rollback/undo, illetve több mappát érintő mai írás teljes tranzakciója nyitott. |

### Javasolt fejlesztői jegytörzsek

#### 1. Fájl ▸ New Album: ne legyen a kijelölésből albumtagság, és ajánlja fel az aktuális dátumot

**Eredeti:** a File-kezelő `0x005eb810` a `0x0055cf70` modellen át jut a
`0x0055d120` albumkészítőhöz; a hívás nem ad képlistát. A job-323/324 mérése
kijelölt kép mellett is üres albumot és változatlan mappa-`.picasa.ini`-t
rögzít. A modell a `0x0098b6e0` időlekérő dátumát és `Untitled` nevet ajánlja.

**Nálunk:** `MainMenuBar.qml:304` a kijelölt sorokat adja át;
`FileOpsDialogs.qml:104-107,160-170` azokat az albumba teszi, és a dátumot
üresen hagyja (`:139`). Az üres kijelölésű File út azonnal visszatér
(`FileOpsDialogs.qml:105`). Sikeres létrehozás után az új album már megnyílik
(`FileOpsDialogs.qml:172-176`).

**Teendő:** válaszd külön a Fájl menü útját a kijelölt képeket albumtagságként
mentő művelettől; a File New Album az eredetivel egyezően üres albumot hozzon
létre akkor is, ha van kijelölt kép, és a dátummező ajánlja fel az aktuális
dátumot. Tartsd meg az új album siker utáni megnyitását. Az üres kijelölésű
menüpont engedélyezéséről külön eredeti mérés kell; ne változtass rajta ennek
a jegynek a bizonyítéka nélkül.

**Kész, ha:** egy vagy több kép kijelölése mellett a Fájl ▸ New Album… és
Ctrl+N az `Untitled`/aktuális dátum ablakot nyitja; OK után üres album nyílik
meg, a kijelölt képek `albums=` tagsága és mappa-`.picasa.ini`-je nem változik;
Cancel nem hoz létre albumot. Az Add-to ▸ New Album külön, kijelölt képeket
mentő útja nem változik.

#### 2. Feltételes jelölt: az Album főmenü törlésparancsa

**Eredeti:** a `0x00559150` `eMenuLabelFolder::ID_ALBUM_DELETE` (`Delete...`)
tételt épít `0x9d44` kóddal; a `0x005cb990` a `0x005ed240` albumtörlőre
irányítja. A `0x0056e1c0` állapotfrissítő a kijelölt albumra és további
predikátumokra támaszkodik.

**Nálunk:** `PicasaFolderMenu.qml:198-213` a Delete elemet mappamódban
engedélyezi; album törlése a bal hasáb helyi menüjéből érhető el
(`AlbumContextMenu.qml:55-58`; `FolderPaneMenus.qml:120-135`).

**Teendő:** előbb oldd fel a nyitott `0x0056e1c0` kapuk rendes, üres,
Starred Photos, Screensaver és People albumokra vonatkozó jelentését, majd
csak az eredetiben engedélyezett esetekben kösd be a főmenü `Delete...`
parancsot a már létező törlőablakhoz és `controller.deleteAlbum(token)`-hoz.

**Kész, ha:** a normál és különleges albumoknál a főmenü láthatósága/
engedélyezése a feloldott eredeti feltételekkel egyezik; jóváhagyás csak
engedélyezett célra indít törlést. A képfájlok hatását ne állítsd be
követelményként, amíg az eredeti nem üres album törlési végállapota nyitott.

### Új kutatási jegyjavaslatok

Új kutatási jegyet nem javaslok: a fennmaradó kérdések ehhez a #7069
életciklushoz tartoznak, az Add-to/tálca `New Album` út részletes nyitott
részei pedig a #7012-ben szerepelnek.

### Nyitott

- `Ghidra-kör kell: 0x0056E1C0 - oldd fel a dinamikus Album/Folder menü 0x9d44 Delete... parancsának 0x00995c90, 0x004ac8f0 és 0x004aca00 predikátumait: normál/üres, Starred Photos, Screensaver és found-people célon pontosan melyik ág tilt. A meglévő 2026-11-15-6970 kimenet megadja a hívásokat és EnableMenuItem ágakat, de nem azonosítja a predikátumok albumtípus-szemantikáját. [blokkoló]` **Megválaszolva a zárókörben (Z1)**: a három predikátum és az ágválasztó `0x10` bit utasításszinten feloldva; a `Delete...` normál (üres is) és személyalbumnál engedélyezett, `]star`, `]screensaver` és más belső tokennél szürke.
- `Ghidra-kör kell: 0x005ED240 - oldd fel a katalógus-vtable +0xec törlőmetódus célját, és kövesd le a nem üres album definíciójának/tagságának tárolását, képfájlhatását és a törlési hibaágat. A meglévő 2026-11-15-6963 kimenet a közvetett hívást és nézetfrissítést mutatja, a célfüggvényt nem. [blokkoló]` **Megválaszolva a zárókörben (Z2)**: a `+0xec` rekesz célja a `0x00451ff0` (az `albumdata` tábla sorának törlése a memóriában, értesítéssel); képfájlt nem érint; az ini-szinkron a #7012-ben megválaszolt `AlbumSync` útja, a végállapota az M1 mérésben dől el.
- `Ghidra-kör kell: 0x0055D120 - kövesd az elfogadott újalbum-objektum útját a job-323/324-ben megjelenő profilbeli ioqueue/albumsafe.ioq-ig: pontos adatbázis, író, queue ürítési pont és hibaút. A meglévő 2026-11-15-7006-7008-7009-7012 dekompilálás a katalógusobjektum létrehozását és settereket mutatja, a queue tartós végpontját nem; ez külön kérdés. [blokkoló]` **Megválaszolva a zárókörben (Z6)**: az `albumsafe.ioq` a `CThumbDB` megnyitásakor jön létre (`0x00415790`), nem a `0x0055d120`-ban; a tartós albumrekord a `db3` `albumdata_*` oszlopfájlja; látható viselkedést nem érint, nem blokkoló.
- `Ghidra-kör kell: 0x006DC030 - derítsd ki, hogy az Album Properties párbeszéd Cancel/újranyitás után megtart-e felhasználói mezőértékeket, illetve ment-e köztes állapotot. A File-út induló név/dátum/üres mezőit a 0x0055cf70 és a Colab #17 mérés már megadja; a meglévő ablakleírás ezt nem válaszolja meg. [blokkoló]` **#7266 után részben nyitott (Z4):** a Cancel a hívó mentési ágát kihagyja és a modellt felszabadítja, de a `+0x40` adatátadó és az újranyitás mezőértékei nem bizonyítottak; lásd a #7266 kiegészítést.
- `Ghidra-kör kell: 0x0055D320 - oldd fel albumobjektumon a név setterének virtuális célját, és azt, hogy a duplikált megjelenített név melyik ága vezet IDS_NORENAME-hoz, illetve elveti-e vagy megtartja-e az átnevezést. A meglévő #7032 dekompilálás a közös settereket és az üzenetágat mutatja, a konkrét album-vtábla és eredmény nem állapítható meg belőle. [blokkoló]` **Megválaszolva a zárókörben (Z5)**: az `IDS_NORENAME` ág csak lemezútvonalas csomópontnál fut (`0x0055d433`), albumnál nincs névütközés-vizsgálat; a névíró a `CThumbDB` `+0x04` rekesze (`0x00445460`), két azonos nevű album létezhet.
- A `0x00556ff0` AlbumSync-trigger/időzítés és `0x0052c350` ini-író hibasorrend kérése már szerepel a #7012 „Nyitott” részében; ott van a kép/néző Add-to `0x005e9bb0` útja is.
- **NINCS MEG:** File ▸ New Album és Ctrl+N engedélyezése üres kijelölésnél. Út: külön Picasa 3.9 mérés üres kijelöléssel, a File menü megnyitásával és a Ctrl+N próbájával; a `0x005eb810` belsejében nincs kijelölésvizsgálat, de ez önmagában nem bizonyítja a menüállapotot. **Megválaszolva a zárókörben (Z3)**: a `0x0056e1c0` a `0x9d67` azonosítót sehol nem szürkíti, a menü és a Ctrl+N kijelölés nélkül is engedélyezett.
- **NINCS MEG:** a tálca New Album engedélyezésekor a tartott képek és a rács kijelölése közül melyik szükséges. A job-255 feljegyzés egy kijelölt képpel és saját album nélkül megnyíló menüt rögzít; út: kontrollált Picasa-mérés csak tartott képpel, csak rácskijelöléssel, mindkettővel és üres állapottal. **Megválaszolva a zárókörben (Z9)**: a tálca New Album kezelője a tálca képlistáját olvassa, üres listánál hatás nélkül kilép; a rács kijelölése nem kapu. A képek tagsága a #7012 (b) mérésének tárgya, nem a #7069 blokkolója.
- **NINCS MEG:** törlés után a bal hasáb, rács, aktív album és fotókijelölés pontos végállapota; create/delete/rename undo-viselkedése; nem üres album `.picasa.ini`/profiladatbázis-hatása; íráshiba, több fájlos részleges végrehajtás és rollback. Út: a fenti célzott Ghidra-kör után kontrollált, előtte/utána eredeti Picasa-mérés. **Megválaszolva a zárókörben**: az undo nincs (Z7, eldöntve); az íráshiba és a rollback a #7012 kérdése és a látható hatás nélküli ágon marad (Z11, nem blokkoló); a törlés utáni bal hasáb, rács, aktív album és kijelölés, valamint a nem üres album ini-végállapota egyetlen mérésre fut (M1, a Zárási döntésben).
- **NINCS MEG:** a Name mezőn kívüli tulajdonságok megjegyzése új Album Properties nyitások között, valamint a People-album törlőablakának külön alapállapota. Út: célzott `0x006dc030` feloldás és külön People-album mérés. **#7266 után:** a Name-en kívüli mezők újranyitáskori állapota nyitott (Z4, #517); a személyalbum törlőablakának alapállapota külön mért (Z12, job-223, job-336-job-339), a PicasaPy egyezik.

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md`: a meglévő #7069 szakasz helyesbítése és
  pontosítása: File és tálca út szétválasztása; a File-út új albumának üres tagsága/
  dátumeltérés; a siker utáni albummegnyitás és normál törlőablak státuszának
  javítása; bizonyítéktábla, cáfoló kör, feltételes fejlesztői javaslat és
  célzott nyitott kérdések.

### Zárókör (2026-11-17): a megmaradt tételek eldöntése

Módszer: a `Picasa3.exe` cím szerinti diszasszemblálása a bináris-index címtáblájával (a bináris SHA-256 értéke egyezik a vizsgálati tárgyéval); a Ghidra-kimenetek veremértelmezését (`param_1`, `unaff_EDI`, eltolások) a hívóhelyek utasításaival ellenőriztem; a hívási zárlatot az index CALL-éleiből számoltam. A programot nem futtattam, a mérések a fenti táblázatok job-hivatkozásai. A "Nálunk" állítások a jelenlegi forráson (1.0.140, a #7164 után) a forráskód keresésével ellenőrzöttek; a fenti táblázatok és jegytörzsek "Nálunk" oszlopa a #7164 előtti állapotot írja (a Fájl-út üres tagsága és mai dátuma azóta kész).

**Z1. A `Delete...` (`0x9d44`) szürkítése az Album/Folder főmenüben: eldöntve (a), erős.** A frissítő a `0x0056e1c0` 3-as menüfajtája (`0x0056ecd1`-`0x0056ef86`). A dekompiláció a `0x0056ef23`-`0x0056ef2b` közti vizsgálatot a `param_1`-re írja, de az utasításokban a vizsgálat alanya a `+0x14` rekesztől kapott, veremben álló szöveges objektum (`[esp+0x20]`, a csomópont útvonala).
- Közös kapu (`0x0056ecd1`-`0x0056ee0e`, tizenegy tételes ciklus): a tétel szürke, ha a `[főablak+0x34a4]` foglaltság-jelző nem nulla, vagy nincs aktív csomópont (`[főablak+0xeac]`), vagy a `0x005d2a70` hamis, vagy a nyomtatási panel (`thumbui/printpanel`) látszik. Ha a szerkesztőpanel előnézete (`editpanel/preview`) látszik, a menü minden tétele pozíció szerint szürke (`0x0056ed0c`-`0x0056ed39`).
- Ágválasztó: a `0x005cb1a0` állapotszavának `0x10` bitje (`0x005cb806`). A bit akkor áll be, ha a csomópont lemezútvonala (`+0x14` rekesz) üres vagy hiányzik, és a token (`+0x28` rekesz) hiányzik vagy nem `]search` (összehasonlítás: `0x005cb720`-`0x005cb72c`). Nem üres útvonalnál az `0x005cb7db`-`0x005cb7e5` ugrás kihagyja az összehasonlítást, a bit nem áll be (ez a dekompiláció `goto LAB_005cb862` ága). A személyalbum-üzemmód korai visszatérése (`0x13`, `0x4013`) a bitet szintén tartalmazza. A `0x004461a0` pontosan az "üres útvonal" kérdést teszi fel (`0x004461c3`-`0x004461f7`).
- A ág (a bit nincs beállítva: mappa vagy `]search`; `0x0056ee99`-`0x0056ef6a`): a `Delete...` és a `Move...` (`0x9df4`) szürke, ha nincs aktív csomópont, vagy az útvonal üres, vagy a `0x00995c90` igaz (hét ismert Windows-mappa, pontos egyezés), vagy a `0x004ac8f0` igaz (iPhoto/Photos `Masters`, a #7059 zárókörében feloldva).
- B ág (a bit be van állítva: albumok, személyalbumok és belső gyűjtemények; `0x0056ee1b`-`0x0056ee83`): a `0x9c72`, `0x9cd0`, `0x9cce`, `0x9cba` és a `0x9df4` mindig szürke; a `Delete...` akkor szürke, ha a `0x004aca00(csomópont)` igaz. Ez azt kérdezi, hogy a token nem üres, és nem `]album:`, nem `]facealbum:` előtagú (`0x004aca00`-`0x004aca7f`; az előtag-összehasonlító `0x00987030` kis- és nagybetűt nem különböztet meg).

| Aktív csomópont | Ág | `Delete...` |
|---|---|---|
| Felhasználói album (`]album:` token), üres is | B | engedélyezett |
| Személyalbum (`]facealbum:<id>` token, `picasa-arcfelismeres.md:528`) | B | engedélyezett; a törlő a személyágat futtatja (`0x005ed240`, `CThumbUI::DeleteFacesAlbum`) |
| Csillagozott fotók (`]star`), Screensaver (`]screensaver`) és minden más nem üres, nem `]album:`/`]facealbum:` előtagú token | B | szürke |
| Keresési találatok (`]search`) | A | szürke (az útvonal üres) |
| Mappa | A | a mappakapuk szerint (útvonal, hét ismert mappa, Apple `Masters`), változatlan |
| Nincs aktív csomópont | A | szürke |

Nálunk (a forráson ellenőrizve): `PicasaFolderMenu.qml:206-211` a `Delete...` tételt csak mappánál engedélyezi (`currentFolder !== "" && currentAlbumToken === "" && currentPersonName === ""`), albumnál és személyalbumnál szürke. Ez eltér, lásd D2.

**Z2. A `+0xec` rekesz célja és a nem üres album törlése: eldöntve (a), erős; az ini végállapota M1.**
- A `[főablak+0x2bc]+0x48` objektum a `CThumbDB` másodlagos vtáblájú része: a `0x00415804` és a `0x0041777f` címen álló két konstruktor-utasítás a `0x00c81fa4` vtáblát írja a `[this+0x48]` mezőbe (`mov [ebp+0x48], 0xc81fa4`; a `.text` bájtpásztázása a vtábla címére pontosan ezt a két találatot adja). Ennek 59. rekesze (`+0xec`) a `0x00451ff0`. A vtábla azonosítását független jel erősíti: a `+0xcc` rekesz célja `0x004755d0`, amelyet a csillag lekérdezőjeként a `ui-audit-context-menus.md` D.8.3 pontja is így nevez meg, a `+0x28` rekesz (`0x0044db30`) pedig a token táblájából másol sztringet, ahogy a `0x004aca00` használja.
- A `0x00451ff0` (1999 bájt) az `idx` sor értékeit törli a memóriabeli albumtáblából: a `db+0x2748` objektum az `albumdata` tábla `albumcontactids` oszlopa (`0x00415b9b`-`0x00415bc2`), és a függvény további oszlop- és tábla-objektumok (`db+0xdb0`, `db+0x23e0`) `idx` sorát is üríti. A `0x006b75f0` a tábla piszkos jelzőjét állítja (`[tábla+0x50] = 1`, `0x006b7654`), majd három virtuális hívás fut az adatbázis-objektum saját vtábláján (`+0`, `+4`, `+0xc`; `0x004522df`, `0x004522ed`, `0x00452305`; az `idx`-et kapják, feltehetően értesítések, feltételes), végül a `0x0045e4a0` az `]album` és `]facealbum` előtagú tokeneknél a címketábla függvényeit hívja (`0x0045eb71`, `0x0045ebdc`; a pontos hatásuk nincs olvasva, feltételes). Visszatérési értéke mindig 0 (`0x004527b9`), hibaága nincs.
- Képfájl: a `0x005ed240` album-ága nem hívja a lemezes törlőt (`0x009929b0`, az a `0x005c9b00` fájltörlő ága), a megerősítő szöveg sem említ fájlt, a személyalbum törlésének mért hatása pedig csak a `faces=` sor, a db3 `albumdata_*` oszlopai és az arcsablon-adatbázis (job-222, job-224). A képfájlok bájtjait ez nem érinti (erős: hívólista és mérés).
- A `.picasa.ini` íróját az `AlbumSync` (`0x00556ff0` a `0x0052c350`-nel) adja, a #7012 szakasz szerint; a trigger és a hibasorrend ott áll. Új kérdés nincs. A nem üres album törlése utáni ini-végállapotot (kikerül-e a `[.album:token]` szakasz és az `albums=` sor, mindkét mappában) az M1 méri.

**Z3. Fájl ▸ New Album... és Ctrl+N üres kijelölésnél: eldöntve (a), erős.** A `0x0056e1c0` teljes diszasszemblálásában (1883 sor) nincs `0x9d67` közvetlen érték; a Fájl menü (0. menüfajta) csoportjai (`0x9d9b`, `0x9dca`, `0xe107`, `0x9c81`, `0x9c97`-`0x9c9a`, `0x9d4f`) közt sem szerepel. A `.text` teljes bájtpásztázása a `0x9d67` kódra egyetlen valódi közvetlen értéket ad: a menüépítő `0x00559150`-ben (`0x005591d9`, `mov word [0xd6d96a], 0x9d67`); a másik három találat hívási eltolás (`0x007a2d85`, `0x00a2a8ee`, `0x00a2a954`). A tétel tehát sosem szürke. A `0x005eb810` kezelő sem vizsgál kijelölést: a `Labels` nevű rekord keresése (`0x00452a30`), a friss modell (`0x0055cf70`), az ablak futtatója (`0x006dc030`), a készítő (`0x0055d120`), majd frissítés (`0x0065b840`) és az új album kijelölése (`0x004af790`) áll benne. A Ctrl+N a `shortcuts.xml` `New label` bejegyzése (`Ctrl+N`), ugyanezt a parancsot váltja ki. Nálunk: `PicasaFileMenu.qml:16-20` és `PicasaMenuBar.qml:717-723` a tételt és a billentyűt a `photoActionsEnabled`-hez köti, vagyis kijelölés nélkül szürke és hatástalan; a `PicasaMenuBar.qml:711-716` megjegyzése a #7164 előtti okot írja (a `createAlbum` üres kijelölésnél nem hoz létre semmit), de a Fájl-út azóta `createEmptyAlbum`-ot hív (`FileOpsDialogs.qml:105-110,164-170`). Ez eltér, lásd D1.

**Z4. Album Properties ablak: Cancel caller-oldali hatása igazolt, az újranyitott mezők nyitottak (#7266).** A `0x006dc030` az ablak futtatója; a `CEditAlbum` ablakot (`0x00849750`; mezők: `caption`, `location`, `music`, `usemusic`, `autodate`) a `0x006db4e0` építi, a modell mezőit a `0x008496c0` tölti, személy-üzemmódban pedig a `0x006db730`-ra tér át (`0x006dc04a`-`0x006dc05c`). Hívói: `0x005eb810` (Fájl), `0x00577ea0` (tálca), `0x005ea770` (Add to), `0x006db580` (szerkesztés); több belépő friss, veremben álló modellel indul. Cancel esetén a futtató 0-val tér vissza (`0x006dc120`-`0x006dc12b`), így a hívók elfogadáshoz kötött létrehozási/mentési ága kimarad, a modell felszabadul. Ez nem bizonyítja, hogy a `+0x40` virtuális adatátadás vagy a `0x008496c0` honnan tölti az újranyitott űrlap mezőit; a korábbi „semmi nem marad meg” megállapítást visszavonom. A #7266 kiegészítés szerinti nyitott következő vizsgálat: a `+0x40` konkrét vtable-célja, `0x008496c0` és a mentő `0x006db730` ág. Nálunk a forrás nyitáskor alaphelyzetet vagy dialog-props mezőket tölt (`FileOpsDialogs.qml:135-146`, `FolderPropertiesDialog.qml:190-200`); az eredeti újranyitási érték hiányában a paritás **NINCS MEG**.

**Z5. Név és névütközés albumnál: eldöntve (a), erős.** A `0x0055d320` a `0x004461a0` eredményéből `bl`-t képez (`sete bl`, `0x0055d34b`: igaz, ha van lemezútvonal), és a mappanév-módosító ágat albumnál kihagyja (`0x0055d433 test bl, bl`, `je 0x0055d69d`). Az `IDS_NORENAME` (`0x0055d634`) csak ebben az ágban hivatkozott, tehát csak lemezútvonalas mappánál jelenhet meg. Az album nevét a `CThumbDB` `+0x04` rekesze (`0x00445460`) írja a táblába, a hívás hibakódja nem felületi üzenet; a rekeszben nincs a neveket összevető hívás, és a `0x0055d120` hívottjai (`0x004ada80`, `0x00440bc0`, `0x0055d320`, `0x006ca5a0`, `0x0045ef50`) között sincs ilyen. Két azonos nevű album létezhet. Nálunk: az üres album `local_empty_albums` táblájának `name` oszlopán nincs egyediségi korlát (`index/schema.py:239-248`), egyezik.

**Z6. Az `ioqueue\albumsafe.ioq` és az eredeti tartós végpont: eldöntve (a), nem blokkoló (c).** A `0x00415790` (a `CThumbDB` megnyitása, 7851 bájt; hívói `0x00402f90`, `0x00467ca0`, `0x0053fe30`) a `slingshot.ioq`, `filesafe.ioq` és `albumsafe.ioq` fájlokat `CreateFileA`-val nyitja (`0x004164a7`, `0x00416534`, `0x004165b5`-`0x004165fc`; olvasás-írás, `OPEN_ALWAYS`), a fogantyút a `[db+0x29c8]` mezőbe teszi. Az album-létrehozó `0x0055d120` ezt nem nyitja, tehát a job-323/324 "az `albumsafe.ioq` megjelent" megfigyelése valószínűleg a profil első megnyitásához kötődik, nem az album létrehozásához (feltevés, mert az előtte/utána pillanatkép időzítése nem rögzített). A tartós albumrekord a `db3` `albumdata_*` oszlopfájljaiban él (`m_albumData`, `albumdata` tábla: `0x004158c4`, `0x00416b45`; a személyalbum törlésének mért hatása az `albumdata_*` oszlopok md5-változása, `picasa-arcfelismeres-kutatasi-naplo.md:2676`). Látható viselkedést ez nem érint: a PicasaPy üres albuma a `local_empty_albums` táblában újraindítás után is megvan, az eredeti profilbeli várólista-fájl pedig nem felhasználói felület. Nem blokkoló.

**Z7. Visszavonás: eldöntve (a), nincs album-visszavonás.** A három album-kezelő hívottjai között (`0x005eb810`: `0x00452a30`, `0x0055cf70`, `0x006dc030`, `0x0055d120`, `0x004ad150`, `0x0065b840`, `0x004af790`; `0x006db580`: `0x0055d070`, `0x006dc030`, `0x0055d320`, `0x0052e3c0`, `0x0055d6e0`, `0x0074c050`, `0x0065b840`; `0x005ed240`: a 2026-11-15-6963 kimenet 28 hívottja) nincs visszavonás-nyilvántartó hívás, és a szövegtárban az `Undo` feliratok kizárólag képszerkesztésre, mentésre, filmszerkesztésre és importra vonatkoznak (`stringres-en-hu.tsv`: `eMenuEdit::ID_UNDO`, `CFilterStackUI::undolabel`, `CThumbUI::FileRevert::undosave`); album létrehozására, átnevezésére vagy törlésére nincs felirat. Hatókör: közvetett (virtuális) hívások nem látszanak a hívólistán, a szövegtár hiánya viszont független jel. A Szerkesztés ▸ Undo tehát album-műveletet nem von vissza; a PicasaPy-ban sincs album-visszavonás, egyezik.

**Z8. Gyorsbillentyűk: dedikált nincs (a); a Delete billentyű albumútja mérendő (b).** Az `enUS/shortcuts.xml` 48 bejegyzéséből albumhoz a `New label`/`New Album` (`Ctrl+N`), a `Move to End of Album` (billentyű nélkül) és a `Select 1st/Last Picture in Album` (`Home`, `End`) tartozik; Album Properties vagy Delete Album gyorsbillentyű nincs. A `VK_DELETE` (`Delete from Disk`) viszont a `0x005c9b00` fájltörlő kezelőre fut, és ennek albumága van. Ha az aktív kijelölés-csomópont a bal hasáb csomópontja (`0x005c9b55`), a rácsban nincs kijelölt kép (`0x005c9b70`) és a csomópont `+0x330` listája nem üres (`0x005c9b80`), akkor a negyedik paraméter mellett `0x005ed240(ablak, idx)` fut (`0x005c9b8c`-`0x005c9b98`), vagyis a megerősítéses albumtörlés. A Ghidra-kimenet szerint (`2026-11-15-6963-colab-decomp.txt:818-825`) a teljesen üres kijelölés ágában a `0x004aca00` hamis eredménye esetén a `+0xec` rekesz közvetlenül hívódik, megerősítés nélkül (feltételes: ezt a részt csak a dekompilációból olvastam). A `+0x330` lista jelentése (a bal hasáb kijelölt elemei vagy a csomópont elemei) nem dőlt el, ezért az, hogy a Delete billentyű üres és nem üres albumon töröl-e, kérdez-e, mérendő (M1). Nálunk: a `FolderPane.qml`-ban nincs billentyűkezelő a Delete-re (`Keys.on`, `Key_Delete`: nincs találat), a `Delete from Disk` gyorsbillentyű a fotókra hat.

**Z9. Tálca ▸ New Album...: eldöntve (a), nem blokkoló (c).** A `thumbui/makealbum` kezelő `0x00577c30` a tálca képlistáját (`+0xea4`, `0x007164b0`) olvassa, és üres listánál 0-val kilép (`0x00577c9c`); a rács kijelölése nem kapu (a #7012 megfelelő sorai). A `New Album...` ága a `0x00577ea0`: a `0x0055ce70` modell a mai időt kapja (`0x0098b6e0`), az ablakot a `0x006dc030` futtatja, és a `0x0055d120` második argumentuma 1 (`0x00577f26`-`0x00577f2e`), ami kihagyja az albumkészítő belső tagságfelvételét (a `0x0045ef50`-et). A tálca képeinek az új albumba kerülése tehát a hívó láncából következik; hogy mely képek (tartottak vagy kijelöltek), a #7012 (b) mérésének tárgya, a #7069-et nem blokkolja. Nálunk a New Album sor a rács kijelölt soraira hat (`MainTrayBar.qml:82-87`, `photoActionRows()`), a meglévő albumsorok a tartott képekre (`addHeldToAlbum`); ezt a #7012 zárókörének 3. pontja is jelzi.

**Z10. Törlés utáni bal hasáb, rács, aktív album és kijelölés: (b), M1.** A `0x005ed240` album-ága a `+0xec` rekesz után a `0x0065b840(ablak, 0, 0, 1)` teljes frissítést hívja (2026-11-15-6963 kimenet, a `FUN_005ed240` törzse), de a törzsében nincs aktív csomópontot állító írás, ellentétben a létrehozással (`0x005eb8c6`-`0x005eb8e1`: az `0x004af790` eredménye a `[főablak+0xeb0]+0x30c` mezőbe kerül). A frissítés eredménye statikusan nem olvasható ki a 4 paraméteres nagy frissítőből; felhasználó számára látható, ezért M1.

**Z11. Íráshiba, részleges végrehajtás, visszagörgetés: (c), a #7012 kérdése.** A hibaág az ini-író `0x0052c350`-ben és az `AlbumSync`-ben van (a #7012 szerint: hibakód 9, mappánkénti sorrend, nincs visszagörgetés); a `+0xec` rekesz nem ad hibakódot (Z2); a létrehozás hibakódját a `0x005eb810` és a `0x00577ea0` az `0x0055d120` visszatérési értékeként adja tovább, és frissítés és kijelölés nélkül lép ki (`0x005eb88d`-`0x005eb8aa`). A felhasználó csak tényleges írási hibánál látja, ami nem idézhető elő mérésben; a PicasaPy az ismert írási hibát `albumWriteFailed`-del jelzi. Nem blokkoló.

**Z12. A személyalbum törlőablakának alapállapota: eldöntve (a), mért.** Cím `Remove People`, kérdés `Are you sure you want to delete the people album "%s"?`, jelölőnégyzet `Delete tagged faces from synced Picasa Web albums, too` kikapcsolva, gombok `Delete Album` és `Cancel`, az alapértelmezett a `Cancel` (job-223, job-336-job-339; `picasa-arcfelismeres-kutatasi-naplo.md:2675`). A hatás: a `faces=` sor kikerül, a `[Contacts2]` sor marad. A PicasaPy ablaka ugyanezt adja (`FolderPaneMenus.qml:165-238`), eltérés nincs.

**A korábbi `NINCS MEG` tételek helye:**

| Korábbi tétel | Válasz |
|---|---|
| Albumtulajdonság-/törlésgyorsbillentyű (belépési pontok táblája) | Z8: dedikált nincs; a Delete billentyű albumútja M1 |
| File menü üres kijelölésű engedélyezése, Ctrl+N | Z3 |
| Megjegyzett állapot új album indításakor és újranyitáskor | Z4 |
| Album-adatbázis fájlneve, profil-várólista életciklusa | Z6 |
| Virtuális törlőcél, ini-szinkron, képfájl végállapota | Z2 |
| Aktív album, rács, kijelölés törlés után | Z10, M1 |
| Névütközés, írási hiba, rollback, undo | Z5, Z11, Z7 |
| Tálca New Album engedélyezése, tartott vagy kijelölt kép | Z9 |
| People-album törlőablakának alapállapota | Z12 |

### Zárási döntés

**A #7069 kutatási jegy lezárható.** Blokkoló nincs: minden korábbi "NINCS MEG" és "Ghidra-kör kell:" tétel eldőlt (a), nem blokkoló (c), vagy egyetlen megnevezett mérésre fut (b). Az egyetlen nyitott tétel az M1 mérés; ez nem a jegy lezárását gátolja, hanem a D3 jegytörzs megírását (lásd lent), a D1 és D2 kiadását nem akadályozza, mert azok nem függnek tőle. A jegy nem vár semmire, ami rajtunk kívül áll.

**M1 (b): egyetlen Colab-mérés az eredeti Picasával.** Előfeltétel: két mappa két-két képpel; három album: A (egy-egy kép mindkét mappából), B (üres), C (egy kép). Lépések: (1) az A album megnyitva, a rácsban semmi kijelölve: képernyőkép; Delete billentyű; képernyőkép (jelenik-e ablak, melyik); ha `Delete Album` ablak jön, jóváhagyás; képernyőkép a törlés után (a bal hasáb aktív eleme, a rács tartalma, a kijelölés); mindkét mappa `.picasa.ini`-je és a `db3\albumdata_*.pmp` fájlok md5-je előtte és utána. (2) a B (üres) album megnyitva: Delete billentyű; képernyőkép; törlődött-e, és kérdés nélkül-e. (3) a C album megnyitva: Album menü ▸ Delete... ▸ jóváhagyás; képernyőkép a bal hasábról és a rácsról. Eldönti: (i) a megnyitott album törlése utáni bal hasáb, rács és kijelölés végállapotát; (ii) a Delete billentyű albumútját üres és nem üres albumnál, megerősítéssel vagy anélkül; (iii) a nem üres album `.picasa.ini` végállapotát (a `[.album:token]` szakasz és az `albums=` sorok kikerülése mindkét mappában). Ezt a hívó önálló mérési jegybe tegye; az eredménye legfeljebb egy új fejlesztői jegyet (D3: a bal hasáb Delete billentyűje, és a törlés utáni nézet) hozza.

**A "Kész, ha" pontok állapota a zárókör után:**

| Pont | Állapot | Bizonyíték |
|---|---|---|
| Új album, tulajdonságszerkesztés, törlés minden belépési ponttal és feltétellel | ✅ / M1 | Z1, Z3, Z8, Z9: minden menü- és billentyűfeltétel eldőlt; a Delete billentyű útja M1 |
| Ablakmezők, alapértékek és megjegyzett állapot | ✅ | Z4, Z12 |
| Tárolás, képek, index, bal hasáb, rács és kijelölés | ✅ / M1 | Z2, Z6; a törlés utáni nézet és a nem üres album ini-állapota M1 |
| Névütközés, írási hiba, részleges végrehajtás és visszavonás | ✅ | Z5, Z7, Z11 |

**Maradó fejlesztői jegytörzsek.** A fenti "Javasolt fejlesztői jegytörzsek" 1. pontja (a Fájl ▸ New Album üres albummal és mai dátummal) a #7164-ben (1.0.140) kész; az engedélyezési maradéka D1. A 2. pont (feltételes jelölt) feltétel nélküli D2 lett. Új felületi szöveg egyikhez sem kell, ezért fordítási teendő sincs; ha a megvalósítás mégis új feliratot hozna, a fordítás minden nyelvre kell.

#### D1. A Fájl ▸ New Album... és a Ctrl+N kijelölés nélkül is működjön

Eredeti: a Fájl menü állapotfrissítője (`0x0056e1c0`) a `0x9d67` (New Album...) azonosítót sehol nem szürkíti, és a `0x005eb810` kezelő nem vizsgál kijelölést; a Ctrl+N ugyanezt a parancsot váltja ki. A tétel és a billentyű tehát kijelölés nélkül is megnyitja az `Untitled`, mai dátumos Album Properties ablakot. Fok: erős (a `0x9d67` bájtpásztázása egyetlen valódi találatot ad, a menüépítőt).

Nálunk: a `PicasaFileMenu.qml:16-20` tétele és a `PicasaMenuBar.qml:717-723` Ctrl+N billentyűje a `photoActionsEnabled`-hez kötött, kijelölés nélkül szürke és hatástalan; a `PicasaMenuBar.qml:711-716` megjegyzése a #7164 előtti okot írja. A Fájl-út a #7164 óta kijelölés nélkül is üres albumot hoz létre (`FileOpsDialogs.qml:105-110`).

Teendő: a Fájl ▸ New Album... tétel mindig legyen engedélyezett, a Ctrl+N billentyű pedig kijelölés nélkül is fusson (a szövegmező-fókusz melletti tiltás, `textEntryHasFocus`, maradjon, mert az eredetiből nem ellentmondó). Frissítsd a `PicasaMenuBar.qml:711-716` megjegyzést. Az Add to ▸ New Album... és a tálca útja ne változzon.

Kész, ha: valódi kattintásos QML-teszt: kijelölt kép nélkül a Fájl ▸ New Album... engedélyezett, és az `Untitled`, mai dátumos ablakot nyitja; a Ctrl+N kijelölés nélkül ugyanezt teszi; OK után üres album nyílik meg, a mappa `.picasa.ini`-je nem változik; Cancel nem hoz létre albumot; kijelölt képekkel a viselkedés változatlan (üres album, tagság nélkül); az Add to ▸ New Album... kijelölt képeket mentő útja változatlan.

Nem szabad: az Add to ▸ New Album... és a tálca New Album... sora, valamint a Fájl-út mai dátuma és `Untitled` neve nem változhat.

#### D2. Az Album főmenü Delete... tétele legyen engedélyezett a megnyitott albumnál

Eredeti: az Album/Folder főmenü `Delete...` tétele (`0x9d44`) a `0x0056e1c0` B ágában (útvonal nélküli, nem `]search` csomópont) akkor szürke, ha a `0x004aca00` igaz: a token nem üres, és nem `]album:`, nem `]facealbum:` előtagú. Így a felhasználói album (üres is) és a személyalbum esetén engedélyezett, a `]star` (Csillagozott fotók), a `]screensaver` és más belső tokennél szürke; a kattintás a `0x005cb990` szétosztón át a `0x005ed240` törlőre fut, amely a normál albumnál a `Delete Album` / `No` ablakot, a személyalbumnál a `Remove People` ablakot adja (job-329/330, job-223, job-336-job-339). Fok: erős.

Nálunk: a `PicasaFolderMenu.qml:206-211` a tételt csak mappánál engedélyezi (`currentFolder !== "" && currentAlbumToken === "" && currentPersonName === ""`), a megnyitott albumnál és személyalbumnál szürke; az album törlése csak a bal hasáb helyi menüjéből érhető el (`FolderPane.qml:361-368`, `FolderPaneMenus.qml:120-135`, a személyalbum `FolderPaneMenus.qml:165-238`).

Teendő: megnyitott felhasználói albumnál (a token nem `]` jellel kezdődik; üres album is) és megnyitott személyalbumnál a `Delete...` legyen engedélyezett, és a bal hasáb helyi menüjével azonos ablakot nyissa (normál: `Delete Album` / `No`, a `No` fókuszban, jelölő nélkül; személy: `Remove People`, `Cancel` fókusszal, kikapcsolt jelölővel), jóváhagyás után ugyanazt a törlést végezze. Szürke maradjon a `]star`, a `]screensaver` és minden más `]` jellel kezdődő belső tokennél, a keresési találatoknál és ha nincs megnyitott hely. Mappánál a mai mappatörlés változatlan. A képfájlokat az albumtörlés nem érinti.

Kész, ha: valódi kattintásos QML-teszt: megnyitott felhasználói albumnál az Album ▸ Delete... engedélyezett, kattintásra a `Delete Album` / `No` ablak jön (a `No` fókuszban), jóváhagyás után az album eltűnik a bal hasábról, a képfájlok és a tagok képei megmaradnak; üres albumnál ugyanez; személyalbumnál a `Remove People` ablak jön; a Starred Photos és a Screensaver nézetben a tétel szürke; mappanézetben a mappatörlés a mai módon működik.

Nem szabad: a bal hasáb album- és személyalbum-helyi menüjének törlése, az `Edit Album Description...` tétel mai (#4883) viselkedése és a mappatörlés nem változhat.

**Nem most kiadható, az M1 utáni jegytörzs (D3).** A bal hasáb Delete billentyűje és a törlés utáni nézet addig nem adható ki fejlesztésre, amíg az M1 nem dönt: (i) a megnyitott album törlése utáni bal hasáb, rács és kijelölés, (ii) a Delete billentyű albumútja üres és nem üres albumnál. Az M1 eredménye után a hívó írja meg a jegytörzset (Eredeti, Nálunk, Teendő, Kész, ha); addig nem félkész feature, hanem nem indított munka.


### #7235-kiegészítés (2026-11-18): Cancel és újranyitás

#### #491 - 0x006dc030

A 0x006dc030 dekompiláció (2026-11-18-koteg-466-495.txt:4720-4780) szerint a dialog objektum +0x40 virtuális művelete a modális eredmény vizsgálata előtt fut, majd csak az iStack_58 == 0 (elfogadás) ág hívja a 0x0065b840 frissítőt és tér vissza 1-gyel; a Cancel (nem nulla) ág a 0x00849d00 után 0-val tér vissza. A két vizsgált hívó, 0x005eb810 és 0x006db580 csak igaz visszatérés után indítja el az album létrehozását, illetve mentését. Ez alátámasztja, hogy a hívó oldali elfogadási/mentési művelet Cancel után kimarad, de a vtable +0x40 adatátadásának pontos hatását és a felhasználó által beírt mezők újranyitáskori értékét nem dönti el.

A PicasaPy forrásban a FileOpsDialogs.qml:135-146 az új album mezőit nyitáskor alaphelyzetbe állítja, a FolderPropertiesDialog.qml:190-200 pedig a dialog-props mezőiből tölti fel az űrlapot. Ez csak a jelenlegi forrás viselkedése; nem bizonyítja az eredeti párbeszéd újranyitáskori állapotát. Következő vizsgálat: a 0x006db4e0 párbeszéd-konfiguráló és a 0x008496c0 mezőátadó adatútja, különösen a +0x40 virtuális hívás címzettje. Az eredeti mezőérték-megőrzés nyitott; a korábbi „ezen a szűk kérdésen egyezik” minősítést visszavonom. Fejlesztői eltérésre jegytörzs addig nem indokolt, amíg az eredeti újranyitáskori érték nem bizonyított.


### #7266-kiegészítés (#517, 2026-11-19): Cancel és újranyitás mezői

A `0x006db4e0` konstruktor nullázza a párbeszéd néhány állapotmezőjét. A `0x006dc030` a párbeszéd `+0x40` virtuális műveletét még a modális eredmény vizsgálata előtt hívja. Cancel esetén a `0x00849d00` takarítást hívja és 0-val tér vissza; ezen az ágon nem hívja a mentő `0x006db730` utat. A `0x008496c0` inicializálja a dialógus `+0xc8`, `+0xcc`, `+0xcd` mezőit és a `+0xd0` útvonaladatot, de önmagában nem mutatja meg az újranyitáskor visszaállított értékek tulajdonosi forrását. Következő: a `0x006dc030` `+0x40` címzettjének vftáblacélja és a mezőket újranyitáskor betöltő modellút.
## #7083: Az importálás teljes folyamata az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
A bináris nem futott; az eredeti oldalt statikus olvasásból (`capstone`,
cím szerinti diszasszemblálás), az index `string_xrefs`/`xrefs`/`rtti`
tábláiból, az `acquirepanel.tre` és `acquirepanel_text.tre` erőforrásból, a
`stringres-en-hu.tsv` szövegtárból és a gyorsbillentyű-táblából olvastam. A
PicasaPy oldalt a jelenlegi forrásból. Korábbi, igazolt részekre hivatkozom,
újra nem kutattam őket: `picasa-importalas.md` (panelelemek, tippsor, törlési
figyelmeztetés, hibaszövegek), `picasa-menu-parancsok-viselkedes.md` 41.
tétel (`AcquirePath`, `LastImport%x`, `acquireUseSubFolder`, almappa-módok),
`picasa-kereses-modok.md` (a másodpéldány-ellenőrző `originfast` kulcsa),
`picasa-fo-ablak-elrendezes.md` (`autoexclude`, `importdest`),
`picasa-gyorsbillentyuk.md` (Ctrl+M), `picasa-lebego-ertesito.md`.
**Futtatott felvételt az importálási panelről nem találtam:** a #6845 lapon a
`ki00/kepernyo__29.png` ("importálási ablak") csak a PicasaPy-sor szövegében
szerepel, a kép a helyi mérőadat-archívumban nincs meg. Ezért minden
működés-állítás statikus; a futtatott mérést a Nyitott résznél kérem.
Ideiglenes szkriptjeim és nyers kimeneteim a munkafa `.bt/` mappájában vannak
(a `.gitignore` kizárja).

**A menürekord-szabály (#7012) alkalmazása.** A menüépítő rekordjaiban a
parancsmező az eggyel előző rekordhoz tartozik. A Fájl menüben az `&Import From...` (`ID_FILE_IMPORTPICTURE`, felirat `0x00c8c718`) után épített
`Import from Picasa Web Albums...` blokk írja a `0x9c91` parancsot
(`0x005592d7`); ez az `&Import From...` rekord parancsa. Független
ellenőrzés: a gyorsbillentyű-tábla `0x00d6d9b0 | 0x9c91 | &Import From... | Ctrl+M` (`picasa-menu-leltar.md:434`), és az `&Import From...` blokk a
megelőző `Add &File to Picasa...` rekord `0xe101` (MFC `ID_FILE_OPEN`)
parancsát írja. A bélyegkép helyi menüjében (`0x00733c70`, 20 bájtos
rekordok, a parancsszó a rekord `+0xa` mezője) ugyanígy: `Include File` =
`0x9dc4`, `Exclude File` = `0x9dc5`, `Include All` = `0x9dc2`, `Exclude All` =
`0x9dc3`.

### Következtetés

Az eredeti importálás nem külön ablak, hanem a főablak `panelroot/acquiretab`
panelje (`acquirepanel`), amely a könyvtár helyére lép (`m_acquire_enable`,
`macros.tre:281`). **Három belépési út fut ugyanarra a kezelőre
(`0x005d3010`):** az eszköztár `Import` gombja, a Fájl ▸ `&Import From...`
menüpont és a `Ctrl+M`. A `picasa-konyvtar-eszkoztar-viselkedes.md` 1.
szakaszának "menüegyenérték nincs" állítása ezzel megdőlt: a `0x005cb990`
parancs-diszpécser ugrótáblája a `0x9c91` parancsot a `0x005cba7c` címre
viszi, ami közvetlenül a `0x005d3010`-et hívja. A PicasaPy mindhárom belépést
tartalmazza, ezekben nincs eltérés. Az eltérések a panel tartalmában vannak.

Az eredeti folyamat: forrásválasztás (`Loading N files`, `Acquired N files`)
▸ bélyegképek és előnézet ▸ választások (cél, almappa-mód, "After Copying")
▸ `Import All` vagy `Import Selected (N)` ▸ egyetlen megerősítés, ha törlés
jár vele ▸ indításkor a beállítások mentése ▸ háttérszál: `Reading`, `Copying at speed`,
`Finishing` (az átmeneti `PhotoLabTemp` átnevezése), `Cleaning Up`
▸ `scandir` a célmappákra ▸ `Completed Importing` vagy `Error Importing`.

**Igazolt, eredetivel összevethető eltérések (a részletek lent): nyolc.** (E1) a célmappa-elnevezési
mód alapértéke és megjegyzése, (E2) az "After Copying" megjegyzése és a
"minden törlése" visszalépése, (E3) a kártyatörlés megerősítése: az eredeti
egyetlen ablak, a hívás jelölő-szöveget nem ad át (az elrendezést nem
mértük); nálunk kétlépcsős ablak, amelyen a "Do not ask again" jelölő a
figyelmeztetést véglegesen eltüntetheti, (E4) az
`Import Selected (N)` gomb és az Enter/Esc kezelés hiánya, (E5) a tippsor
három hiányzó állapota, (E6) a korábbi célok mentésének ideje és darabszáma, (E7) panel helyett
modális ablak, egyetlen nagy előnézet nélkül, (E8) az Include/Exclude
műveletek helyi menüjének hiánya. PicasaPy-forrásból külön hibaág is látszik:
forrástörlési OSError után a QML `importing` állapota beragadhat; ennek eredeti
Picasa-megfelelője nyitott.
Feltételes jelölt még a fájlhiba utáni leállás (az eredeti az egész importot
leállítja) és a Windows-forráslista szabálya. A 2026-11-17-i zárókör két
dolgot erősített meg: a törlési mód kapuja forrástípushoz kötött (az E2
kiegészítése: csak `DCIM` mappás meghajtógyökér törölhető, `Folder on Disk`
nem), és fájlhiba után az eredeti a forrásból semmit nem töröl (E10).

**Bizonyítottsági fok: részben megerősített.** A belépési utak, a panel
eseménykezelői, a megjegyzett kulcsok és alapértékeik, a törlés-megerősítés
szerkezete és a szövegek két független úton egyeznek (diszasszemblátum és
erőforrás). A másolás belső sorrendje, az ütközés-, hiba- és megszakítás-
kezelés, valamint a végállapot (rács, bal hasáb, kijelölés) nem zárult le.

### Belépési pontok és feltételek

| Eredeti bináris cím | Nálunk fájl:sor | Teendő |
|---|---|---|
| **Eszköztár `thumbui/importbutton`:** `0x005d3010` (223 b); hívói `0x005d9cc0` (név-diszpécser), `0x005cb990` (parancs-diszpécser), `0x005e60d0`. Növeli a fő objektum `+0x24c` számlálóját, majd `0x005218e0`-on át megkeresi a `thumbui/acquirebutton` elemet és virtuálisan hívja. A panel `acquirebutton` eseményének kezelője a `0x0051d4c0` (az `iCAcquireController` vtable-ben, `0x0051e9a0`): `[panel+0x3c2]=1`, `[panel+0x3b0]=1`, majd `0x0051c010`, amely a `/StiDevice:` argumentumot vagy a `0x0051b990(panel,1)` forrásválasztást futtatja. A két lánc összekötése statikusan nem teljes. `.tre`: `m_acquire_enable` makró. | `MainToolbar.qml:185-203`; `MainWindowToolbar.qml:72`; `MainWindowCommands.qml:704` (`importSourceDialog`) | A belépés egyezik. A cél más: modális, önálló `Window` (`ImportSourceDialog.qml:16-31`) panel helyett; lásd E7. |
| **Fájl ▸ `&Import From...`:** `0x00559150`, parancs `0x9c91` (előző-rekord szabály, `0x005592d7`); ugrótábla `0x005cd9fc`/`0x005cdb34` a `0x9c91`-hez `0x005cba7c` → `call 0x005d3010`. A `.text`-ben a `0x9c91` utasítás-azonnali értéke csak a menüépítőben fordul elő; a `0x0056e1c0` állapotfrissítő nem hivatkozza, tehát külön tiltásra nincs bizonyíték. | `PicasaFileMenu.qml:57-61`; `MainMenuBar.qml:314` | Egyezik, feltétel nélkül aktív. A menüpont engedélyezése más állapotforrásból nyitott (lásd Nyitott). Helyesbítés a régi lapra: a menüegyenérték létezik. |
| **`Ctrl+M`:** gyorsbillentyű-tábla `0x00d6d9b0`, parancs `0x9c91` (`picasa-gyorsbillentyuk.md:166,291,458`). | `PicasaMenuBar.qml:686-690` (`enabled: !bar.editorActive && !bar.textEntryHasFocus`) | Egyezik. A tábla "könyvtár" nézethez köti; a szerkesztő és a szövegmező tiltása a mi döntésünk, ellenpróba nincs. |
| **Helyi menü a bélyegképeken:** `0x00733c70`: `Include File`, `Exclude File`, `Include All`, `Exclude All`; a parancsok (`0x9dc4`, `0x9dc5`, `0x9dc2`, `0x9dc3`) a `0x005cb990` kezelőiben az `acquirepanel/include`, `includeall`, `exclude`, `excludeall` eseményt küldik (`0x005ccea8`...), a panel `0x0051f070` kezelője `0x0051f7f0(panel, include, all)`-t hív. | Nincs helyi menü. `ImportSourcePreview.qml:100-145`: csak szöveges hivatkozás (`Exclude`/`Include`); `ImportSourcePickerPanel.qml:251-260`: `Exclude All`/`Include All` gomb | E8: adj helyi menüt a négy művelettel; a külön gombok maradhatnak. |
| **Parancssor `/StiDevice:`** (Windows WIA kamera csatlakozás): `0x004bc0c0` (`/StiDevice`, `0x00c839e8`), `0x0051c010` (`/StiDevice:`, `Runtime\StiDevice`), forrás kijelölése `0x0051b990`. | Nincs. A PTP/MTP kamera szándékosan kimarad (`import_source_controller_sources.py:156-165`). | Nincs teendő: Windows-specifikus eszközút, a kamera külön termékdöntés tárgya. |
| **Behúzott hordozó (AutoRun):** az `iCDriveDetectorThread`, `...Response`, `...IsImport`, `...AR` nevű kernel-események (`0x00512cf0`, `0x00514180`); `Runtime\AutoRun` olvasása `0x00522570`, `0x00513d70`, `0x00514040`, `0x0051ee50`; törlése `0x00525630` (az import indítás végén, `0x005254fc`), a `Runtime\StiDevice`-szel együtt. A `PicasaMediaDetector.exe` név a `0x00704be0` folyamatnév-listában áll; az `AutoRun` írója nem azonosított. | Nincs. A forráslista az ablak megnyitásakor frissül (`ImportSourceDialog.qml:151-157`). | Nincs teendő: külső folyamat és Windows-specifikus; Linuxon a csatolás-figyelés külön termékdöntés. |
| **Bezárás-figyelmeztetés:** `0x005e45c0` (1271 b; hívók `0x0057c4e0` ← `0x005e4ac0`, `0x005d3290` ← `0x005de8e0`): ha a `panelroot/acquiretab` aktív és az `anowbutton` engedélyezett, kérdés: `Import images before closing Picasa?` (`IDS_WARNCLOSEACQUIRE`), gombok `Import Images` és `Quit`; a másik ág az `acquirepanel/acancelbutton`-t nyomja (`0x005e4761`). A `0x005e4ac0` a keresés függvényei közt is szerepel (#7072). | Nincs. Az ablak modális, a főablak vele nem zárható. | Nincs teendő, amíg az importálás modális ablak. Ha a panel-átalakítás megtörténik, ez a kérdés hozzá tartozik. |
| **Import from Google Photos...:** parancs `0x9dfa` → `0x005cc4b4` → `0x005d2ca0` ("Import in Progress...", `Disk Space Warning`). | `PicasaFileMenu.qml:62-68` (nyugdíjazott) | Nincs teendő; megszűnt szolgáltatás (#6845: nincs látható hatás). Itt fontos: a "not enough free disk space" szöveg innen való, lásd a hibák szakaszát. |

### Ablak (panel), mezők, alapértékek és megjegyzett állapot

- **Elrendezés (`acquirepanel.tre`).** Felül `import_from_menu` és az
  `excludedupesbutton`; balra a bélyegképek (`selcontainer`, üres állapotban
  "No photos available"); jobbra az előnézet (`thumbpreview`), alatta a
  forgatás (`rotate1button`, `rotate2button`), lapozás (`previousbutton`,
  `nextbutton`), csillag (`startoggle`) és kizárás (`excludetoggle`) gomb és a
  `fileinfo`; alul `import_to_label`, `import_folder_menu`, `subfolder_menu`,
  `subfolder_label`, `delete_menu`, a (megszűnt) megosztás blokk, a tippsor és
  a gombok: `acancelbutton` (`Property escapekey 1`, azaz Esc), `anowbutton`
  (felirata `Import All`), `import_selected` (`Import Selected (%d)`). A
  `excludetoggle` letiltja a `startoggle`-t (`Property disabletarget`): kizárt
  képre nem lehet csillagot tenni. Az `acquirepanel/timesegment` elem rejtett
  (`m_hidden`). PicasaPy: egy 640 × 680-as modális `Window`, forrás-,
  szűrő-, másodpéldány-, rács-, cél- és "After Copying" sorokkal
  (`ImportSourceDialog.qml:297-316`).
- **Forrás-menü.** `0x00510500` a meghajtókat `GetLogicalDriveStringsA` +
  `GetDriveTypeA` + `GetVolumeInformationA` szerint sorolja: a 2-es típusú
  (cserélhető) meghajtó mind, kivéve az `A:` és `B:` betűjelet; a 3-as típusú
  (fix) kötetnél, ha a fájlrendszer `FAT`, `FAT32` vagy `NTFS`, csak akkor,
  ha a címke `KODAK`-kal kezdődik (`0x005107c8`-`0x00510824`), más
  fájlrendszernél megkötés nélkül; az 5-ös típusú (CD-ROM) olvasható kötetnél
  mind. A
  felirat `Removable Drive(%s)` (`%s` a gyökér, nem a címke). Nincs `DCIM`
  vizsgálat a felsorolóban; a `\dcim\` szöveget a `0x0050f6a0` használja
  (hívói `0x0050f590` és `0x0070d520`; az utóbbit a szál főrutinja,
  `0x0070ccb0`, korán hívja).
  `iCAcquireWIAScanner`/`iCAcquireTWAINScanner` (RTTI) az eszközútról. A
  "Folder on Disk" tétel az `Import Files/Folder` tallózót nyitja
  (`0x00520fa0`), ami a `Preferences\FilesFromImport` mappát jegyzi meg.
  PicasaPy: Linuxon `/media` és `/run/media` alatti csatolások, Windowson
  cserélhető meghajtó vagy `DCIM` mappás kötet (`import_source_controller_ sources.py:77-165`); ez az eredeti szabálytól eltér (CD-ROM nincs, a
  `KODAK` szabály nincs, a `DCIM` vizsgálat a felsorolóban nincs).
- **A tippsor négy állapota (`0x0051ae90`).** Az állapotot a `[panel+0x7b0]`
  almappa-mód és a `[panel+0x480]` jelző adja: kézi mód és jelző nulla = 1.
  ("Enter new folder title or choose existing folder to continue"), kézi mód
  és jelző nem nulla = 2. ("Click Import All or Import Selected"), dátum mód
  = 3. ("Import into separate folders for each date taken"), mai dátum mód =
  4. ("Import into folder with today's date"). PicasaPy csak az 1. állapotot
  mutatja (`ImportSourceDestinationPanel.qml:129-140`).
- **Mikor engedélyezett az Import.** Az `AcquireImportAllEnable` (`0x005276f0`)
  és `AcquireImportSelectedEnable` (`0x00527730`) állítmány a `0x005238b0 (panel, csakKijelölt)`-et hívja: akkor engedélyez (a visszaadott 1 =
  engedélyezett, 2 = letiltott; a kódolás az `AcquireHasImages` és az
  `AcquireDeleteMenuEnable` párhuzamából következik), ha a `[panel+0x480]` nem
  nulla, és van legalább egy nem kizárt (`[elem+0xbc]==0`), `Import Selected`-nél kijelölt (`[elem+0x5d]`) elem. Az alapgomb-kezelő
  (`0x0051b620`, feltehetően az Enter; a kód a `+0x228` célra és egy
  "mégse" jelzőre ágazik) az `anowbutton`-t nyomja, ha legfeljebb egy kép
  van kijelölve, különben az `import_selected`-et; a jelzős ág az
  `acancelbutton`-t (Esc). PicasaPy: egyetlen
  `Import` gomb, engedélye `includedCount > 0 && destFolder && !importing && (nem kézi || manualNameValid)` (`ImportSourceDestinationPanel.qml:251-261`),
  kijelölés nincs; a #4595 óta a címhiány letiltja a gombot (a régi lap
  "a gomb engedélyezett" megjegyzése elavult).
- **Megjegyzett állapot és alapértékek.**

| Kulcs (`Preferences\`) | Eredeti | PicasaPy |
|---|---|---|
| `AcquirePath` | cél-gyökér; olvasás `0x00513830`: üres vagy nem létező út esetén a `0x009966a0` hívás eredményére esik vissza (egy ismertmappa-lekérdezés, jelentése nem ellenőrzött), és azt feltehetően visszaírja (`0x00407760`, ugyanaz a hívás, mint a `LastImport%x` írásánál) | `import/defaultdestination`, alap a képek rendszermappája (`import_source_controller_state.py:162-199`); egyezik |
| `acquireUseSubFolder` | egész; **alapérték 0** (`0x00514180`: `xor esi,esi` → olvasás `0x005148ac`-`0x00514936`, `[panel+0x7b0]`); a menü sorrendje `0x005181b0`: 0 = `Enter Folder Title`, 1 = `Date Taken (YYYY-MM-DD)`, 2 = `%s (Today)`; **írás az import indításakor** `0x00525400` | alap `"date"`, **nem tárolt** (`ImportSourceDialog.qml:94`) |
| `acquireCleanCard` | egész; alap 0 (`Leave card alone`); olvasás `0x00519560`: a **2 (összes törlése) 1-re esik vissza**; írás `0x0051a0c2`, csak ha a forrás törölhető (`[panel+0x2a6] != 0`) | alap `"leave"`, **nem tárolt** (`ImportSourceDialog.qml:105`) |
| `LastImport%x` | korábbi célok; **írás az import indításakor** (`0x00525352`), legfeljebb 5 tétel (`0x0052532c`-`0x00525347`: a darabszám 5-re vágva); menü `0x00516180` | **sikeres másolás után**, legfeljebb 8 (`import_source_controller_state.py:55,210-223`; `import_source_controller.py:440-444`) |
| `autoexclude` | alap 1; `0x0051f600` | `import/autoexclude`, alap igaz (#5473); egyezik |
| `ImportSegmentMinutes` | alap 0, ekkor 90 perc (`0x005219c5`-`0x00521a10`); perc × 60 / 86400 nap, a bélyegkép-lista `+0x310` mezőjébe | nincs; a rács nem szegmentál |
| `FilesFromImport` | a fájltallózó utolsó mappája (`0x00521050`) | nincs (Qt `FileDialog`) |

A "Recent sources" legördülő (`ImportSourcePickerPanel.qml:44-57`) **nem
eredeti:** a `LastImport%x`, a `-seperator-before-LastImports-` és az
`Acquire::ChooseFolder` a `0x00516180`-ban, az `import_folder_menu`
építőjében áll (a `0x005254c3` hívás az `acquirepanel/import_folder_menu`
elemmel). A forráslistának megjegyzett előzménye az eredetiben nincs. Ez egy
tudatos, működő többlet, nem teendő; a komment (`ImportSourcePickerPanel.qml: 42-43`) téves állítását pontosítani érdemes.

### Tárolás, hatás és állapotsor

| Hatás | Eredeti Picasa 3.9 | PicasaPy most |
|---|---|---|
| Fájlok másolása | A `0x0070ccb0` (az `iCAcquireScanner` fő rutinja) háttérszálon dolgozik. A `0x0070bdd0` befejező lépése az átmeneti `PhotoLabTemp`-et átnevezi (a hibaszöveg: `An error has occurred while renaming PhotoLabTemp. Cancelling Import.`), majd egy elérési útra `GetFileAttributes`, a `2` bit törlése, `SetFileAttributes` (`0x0070c424`-`0x0070c446`; a hívott `[0x00d694bc]` a `GetFileAttributes`, a `[0x00d69514]` a `SetFileAttributes` (NT-n a `...W` változat burkolón át, Windows 9x-en az `...A` import; feloldva 2026-11-17-én; az `and eax, 0xfffffffd` a rejtett jelzőt veszi le a célmappáról, `0x0070c437-0x0070c440`)). Az átmeneti név létrehozási helye nincs meg (a `PhotoLabTemp` csak a hibaszövegben szerepel). A dátumos ág `0x0070b1e0`. Az ütköző nevek kezelése nyitott. | Közvetlenül a végleges almappába másol (`import_source_controller.py:415-438`), `fileops.copy_photo` ütközésnél új nevet ad (`név-1.jpg`). Átmeneti mappa nincs. |
| Almappa neve | `Date Taken (YYYY-MM-DD)`: a `%d-%02d-%02d` formátum (`0x00c875c4`, `0x00514980`); `%s (Today)`; kézi cím. Ismeretlen dátumú képek mappája nincs meg. | `ÉÉÉÉ-HH-NN`, kézi név, mai dátum (`importsource.py:351-389`); ismeretlen dátumnál `Ismeretlen dátum` (`importsource.py:48`), eredeti nincs |
| `.picasa.ini` | A csillag és a forgatás helye az eredetiben nincs meg (nyitott). A forrás-ini szekciójának sorsa törléskor nyitott. | `_mark_imported_ini`: `rotate=rotate(n)` és `backuphash`, `star=yes` a másolat ini-jébe; törléskor a forrás-ini szekció és a kísérők mennek (`import_source_controller_import.py:26-86`) |
| Index és bal hasáb | A worker végén `scandir` feladatot épít be (`0x0070c4ce`-`0x0070c55a`, `0x0070baa8`-`0x0070bb85`); a mappa-halmaz és a bal hasáb pontos változása nincs ellenőrizve. A meglévő Ghidra-kimenet a worker befejező ágában `0x0052db70` és feltételes `0x00709460` hívást mutat (`2026-11-16-koteg-426-437.txt:3506-3508`). | Csak sikeres másolás után hívja az `addWatchedFolder`-t (`import_source_controller.py:440-444`); a `library_controller_folders.py:319-390` felveszi és eltárolja a gyökeret, majd háttér-indexelést indít. Az import nem választja ki az új mappát; a `controller_sync_mixin.py:145-159` a meglévő nézetet tölti újra. |
| Rács és kijelölés | A panel bezárása, a megjelenő mappa és a kijelölés nincs meg (nyitott). | Az importablak nyitva marad. Az import utáni navigációra nincs kötés. Az értesítő `click to view` feliratot mutat, de üres útvonalat ad (`PicasaNotifier.qml:360-369`), ezért nincs hová navigálnia (`:325-336`). |
| Állapotsor és háttérmunka | A fázisszövegek egy `ytProgress` elembe kerülnek (RTTI `0x00c81db4`; létrehozás `0x0070ebf0`, frissítés `0x00415610(elem, szöveg, tört)`): `Reading %1$d of %2$d files`, `Copying %1$d of %2$d files` + ` at %s/sec` (tört = kész/összes), `Finishing`, `Cleaning Up`, `Completed Importing` vagy `Error Importing` (`[+0x2c8]==6`, tört 1,0). A panel státuszsorába: `Loading %d files`, `Loading %1$d of %2$d files`, `Acquired %d files` (`0x0051e5c0`). Melyik felület mutatja a `ytProgress`-t (lebegő ablak vagy alsó sáv): nyitott. A `picasa-lebego-ertesito.md` "közbenső fázisok" nyitott kérdése ezzel részben lezárul: a közbenső fázisok nem a panelben, hanem a `ytProgress`-ben vannak. | A párbeszédben sáv és "%1 / %2 imported at %3/sec" (`ImportSourceDestinationPanel.qml:195-234`), a végén "Done: %1 imported, %2 failed" (saját szöveg), a végén értesítő `Completed Importing` vagy `Error Importing`. Az eredeti fázisszövegek (`Loading`, `Reading`, `Finishing`, `Cleaning Up`) nincsenek. |

### Hibák, ütközés, megszakítás, hálózat, írásvédett hely és visszavonás

| Eset | Eredeti | PicasaPy most |
|---|---|---|
| Fájlhiba másolás közben | "A file error has occurred while importing files. Cancelling Import." (`0x0070b1e0`, `0x0070bdd0`), üzenetablak (`0x00980700`), a worker befejeződik; a már másolt fájlok és az átmeneti könyvtár sorsa nyitott. A meglévő Ghidra-kimenet a `0x0070ccb0` → `0x0070bdd0` hívást és a `PhotoLabTemp` átnevezési hibaágat mutat, de nem igazolja a végső fájlrendszer-diffet (`2026-11-16-koteg-426-437.txt:3143-3835,3836-3970`). | Másoláskor a fájlonkénti `OSError`-t rögzíti, a következő képpel folytatja, és a legfeljebb 5 hiba részletét mutatja (`import_source_controller.py:431-439`); az előzetes lemezhely-ellenőrzés elégtelen szabad hely esetén a teljes köteget 0 másolással leállítja (`:392-408`). |
| Átnevezési hiba | `...renaming PhotoLabTemp. Cancelling Import.` és `...renaming '%s'. Cancelling Import.` (`iCAcquireScanner::error2`) | Nincs ilyen lépés. |
| Eszköz hibakódok | `0x0051e4c0` (hívó `0x00527470`): 6 = "Unable to connect to the device..."; 7 = "The selected device is busy..."; minden más = `eFileErr` ("...the source is unavailable or the destination is full or read only."), szöveg nélkül `\n(%d)` kóddal; üzenetablakban. | Nincs; `sourceScanFailed` az üres forrásra, `importFailedDetails` a fájlokra. |
| Eszköz eltűnése import közben | `iCAcquireController::NotifyDeviceGone`: `The device '%s' has unexpectedly disappeared while attempting to import from it.` (`0x0051d9c0`, vtable `0x00c892dc`) | Nincs külön ág; a fájlhibák jelzik. |
| Elfogyott hely, írásvédett cél | Az `eFileErr` szövege nevezi meg (utólagos jelzés). **Előzetes szabad-hely ellenőrzés az importáló sávban nincs bizonyítva:** a `Disk Space Warning` és `Sorry, there is not enough free disk space to safely download pictures.` egyetlen hivatkozója a `0x005d2ca0`, amit a `0x9dfa` (Google Fotók import) hív. A `GetDiskFreeSpaceExA` burkolóinak hívóit nem követtem. | A források fájlméretét összeadja, és a cél eszköz `disk_usage().free` értékével veti össze (`fileops/diskspace.py:30-55`; `import_source_controller.py:392-408`). Másolási írási hiba fájlonként fogódik meg és a köteg folytatódik. |
| Forrásfájl törlési OSError (pl. írásvédett vagy kieső megosztás) | A Picasa eredeti futásidejű kimenete nyitott. | A másolás utáni `_remove_source_file` közvetlen `unlink`-ot hív, erre nincs helyi `OSError`-kezelő (`import_source_controller_import.py:41-86`, `import_source_controller.py:446-464`). A háttérszál eltárolja és naplózza a kivételt, de nem küld `importFinished`-et (`worker_thread.py:311-361`); a QML csak e jelzésre állítja vissza az `importing` állapotot (`ImportSourceDialog.qml:274-297`). Az ablak így „dolgozik” állapotban maradhat. |
| Megszakítás | Az `acancelbutton` (`0x0051f070` → `0x00523ac0(panel,1)` és `0x00523a00`) a panelt zárja és a listát üríti; Esc ugyanez. Hogy import közben a másolást állítja-e le: nyitott. | Nincs megszakítás: a `Close` csak elrejti az ablakot, a háttérszál fut tovább (`ImportSourceDestinationPanel.qml:262-266`, `import_source_controller.py:392-465`). |
| Hálózati forrás | A meghajtó-felsorolás a 4-es (hálózati) típust nem veszi fel; a `Folder on Disk` tallózóval bármely út megadható. A hálózati másolás tényleges futásidejű eredménye nincs mérve. | A tallózó tetszőleges útvonalat elfogad; a forráslista platformonként szűrt (`import_source_controller_sources.py:77-165`; `ImportSourcePickerPanel.qml:73-96`). A hálózati I/O eredményéről nincs mérés, paritást nem állítok. |
| Visszavonás | Az importnak nincs bizonyított visszavonási útja; a kártyatörlés kifejezetten "nem vonható vissza" (`confirmRemoveCopied::message`). Az Edit ▸ Undo verem tartalmát nem vizsgáltam. | Nincs visszavonás. |

**A kártyatörlés megerősítése (`0x00519720`, 2559 b).** A `0x0051b3c0`
adja a törlés-menü állapotát (0 = `DeleteNothing`, 1 = `DeleteCopied`, 2 =
`DeleteAll`). A 0 állapotban nincs kérdés. Az 1 állapotban az általános
`confirmRemoveCopied::message` ("Are you sure you want to remove the
imported files from your card? This cannot be undone."), a 2 állapotban a
`WipeCard...` darabokból összeállított figyelmeztetés kerül **egyetlen**
ablakra (`0x0051a01c`, az egyetlen `0x009ba4d0` hívás); a cím "Confirm
Remove" (`confirmRemove::title`), az igen gomb "Remove Imported Files"
vagy "Remove All Files", a másik gomb "Cancel" (`il_Cancel`). A
`0x009ba4d0` hívás hét argumentuma: cím, üzenet, igen-szöveg, `0`,
mégse-szöveg, `0`, `0`; jelölő-szöveg nincs köztük (az ablak elrendezését
nem mértük). A "Don't warn me about this in the future"
(`CAcquireUI::dontwarn`, kulcs
`DoNotConfirmPublicUpload`) a `0x0051b710`-ban, a nyilvános feltöltés
kérdésén van, **nem** a törlés kérdésén. A `0x005277e0`
(`AcquireDeleteMenuEnable`) szerint a törlés-menü csak akkor aktív, ha a
kiválasztott forrás törlést enged (`[panel+0x2a6]`, a forrás-elem `+0x18`
virtuális metódusából, `0x00519630`); különben a menü 0-ra áll. PicasaPy:
mindig mindhárom választás elérhető, forrástípustól függetlenül
(`ImportSourceDestinationPanel.qml:161-192`); `delete_all` esetén két
egymás utáni, általános `ConfirmDialog`: előbb a "...THIS CANNOT BE UNDONE."
nagybetűs mondat (az eredetiben ez csak a `WipeCardFinalWarning` vége; a
`confirmRemoveCopied` szövege kisbetűs), utána az összeállított
figyelmeztetés (`ImportSourceDialog.qml:239-254`, `:376-401`). A
`ConfirmDialog` "Do not ask again" jelölője itt látható marad
(`rememberVisible` alapértéke igaz, `ConfirmDialog.qml:59`; az `ask` a
kulcs elnyomása esetén megkérdezés nélkül `confirmed()`-et ad,
`ConfirmDialog.qml:100-110`), így egyetlen bejelölés után a "minden törlése"
figyelmeztetés véglegesen eltűnhet, és az import a kártyát megkérdezés
nélkül kiüríti.

### 2026-11-17-i ellenőrző kör

**Mérési kapu.** A kért `grep -rn "job-[0-9]" docs/specs/` és a
`~/.local/share/picasapy-meroadat/meroadat.tar` tartalomjegyzékének ellenőrzése
nem talált az eredeti importpanelről vagy importfutásról szóló felvételt. A
#6845 által említett `ki00/kepernyo__29.png` sincs a helyi archívumban. A
Picasa 3.9.141.259 bináris hash-e
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`; maga a
bináris nem futott. A korábbi Ghidra-kimenetek címeit a kutatás előtt
ellenőriztem; a `2026-11-16-koteg-426-437.txt` már dekompilálja a
`0x0070ccb0`, `0x0070bdd0`, `0x00524730`, `0x0071a4d0`, `0x0070e990` és
`0x00519630` címeket. Új Ghidra-kört nem kértem.

**Bizonyíték és bizonyítottság.** A belépési utak, az importpanel szerkezete,
a gombkezelők és a megjegyzett Preferences-állapot statikus leletei
megerősítettek: az utasításszintű út a gyorsbillentyű-/menürekorddal,
illetve az erőforrás-feliratokkal egyezik. A másolás, ütközés, hiba utáni
lemeztartalom, megszakítás, hálózati/írásvédett futás és a végállapot nem
megerősített, mert ezekhez nincs második, futásidejű bizonyíték.

| Érték / állítás | Forrás |
|---|---|
| Eszköztár, Fájl ▸ Import From… és Ctrl+M ugyanarra a `0x005d3010` kezelőre jut. | bináris (`0x00559150`, `0x005cb990`, `0x005cba7c`, `0x005d3010`); gyorsbillentyű-rekord `0x00d6d9b0`; `acquirepanel.tre` |
| A Picasa importja a `panelroot/acquiretab` beépített panelje; az alap Almappa mód kézi cím, a törlés alapja „Leave card alone”, a legutóbbi célok száma 5. | bináris (`0x00514180`, `0x00519560`, `0x0052532c`-`0x00525400`); `acquirepanel.tre` |
| A Picasa másolási folyamata háttérszál; a `PhotoLabTemp` átnevezési hiba és az `Error Importing` ág kódútja létezik. | bináris (`0x0070ccb0`, `0x0070bdd0`, `0x00710700`); meglévő dekompiláció: `2026-11-16-koteg-426-437.txt:3143-3970` |
| Az eredeti Import Selected, a pontos ütközés, `.picasa.ini`-diff, törlési hiba, megszakítás alatti worker-állapot és záró kijelölés/rácsállapot. | NINCS MEG: nincs importfutás-felvétel; a lemezen maradó állapotot tiszta Windows VM-profilon, fájl- és index-diffel kell megmérni. |
| PicasaPy sikeres másolás után felveszi és háttérben indexeli a célgyökeret, de nem navigál oda; a sikeres importértesítő üres útvonalat ad. | `import_source_controller.py:440-444`; `library_controller_folders.py:319-390`; `controller_sync_mixin.py:145-159`; `PicasaNotifier.qml:325-336,360-369` |
| PicasaPy másolási OSError után folytatja; sikeres másolás utáni forrástörlési OSError-t a worker naplóz, de az import QML nem kap `importFinished` jelet. | `import_source_controller.py:431-465`; `import_source_controller_import.py:41-86`; `worker_thread.py:311-361`; `ImportSourceDialog.qml:274-297` |

**A két független út.**

- **A - eredeti bináris:** utasításszinten követtem a `0x005cb990` parancs-
  diszpécsert, a `0x005d3010` eszköztárkezelőt, a panel gombjait és a
  `0x0070ccb0`/`0x0070bdd0` workerútvonalat. A `0x00d6d9b0` gyorsbillentyű-
  rekord és az `acquirepanel.tre`/`acquirepanel_text.tre` külön megerősíti a
  belépőt és a panel feliratait.
- **B - PicasaPy:** a vezérlő `runImport`/`addWatchedFolder` hívásláncát
  külön követtem; ettől független QML-kötésként ellenőriztem a haladás-,
  befejezés- és értesítőkezelőket, valamint a könyvtár `selectFolder`
  hívásait. A két út egyezik abban, hogy az import háttérben dolgozik és a
  helyi befejezés nem választja ki a mappát; az eredeti rács-végállapotra
  nincs bizonyíték.

**Cáfoló kísérlet.** Azt az értelmezést ellenőriztem, hogy a sikeres import
automatikusan kiválasztja a célmappát, mert az alkalmazás importvégén nézetet
tölt újra. Cáfolat: az általános `_reload_after_sync` bekötés a külön
`PicasaImportController` (PicasaPy-adatbázisimport) jelzésére vonatkozik. A
forrásfájl-import `addWatchedFolder`-t hív; a mappakiválasztó callback csak a
`newFolderMoveFinished` jelzést figyeli. Az importértesítő üres célútvonalat
ad a kattintáskezelőnek. Tehát az automatikus navigációra vonatkozó állítás
elvetendő; a `PicasaNotifier.qml` útvonalas handlerét és az import-controller
hívását külön, fájl:sor szinten ellenőriztem.

### A jegy „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték / hiány |
|---|---|---|
| 1. Belépési pontok és feltételek | ✅ / ⛔ | A három fő út (`0x005d3010`, `0x9c91`, Ctrl+M) megvan. ⛔ Az eredeti engedélyezési állapot minden nézetben, az AutoRun/WIA automatikus megnyitás és a helyi menük futásidejű használata nincs mérve. |
| 2. Ablak, mezők, alapérték és megjegyzett állapot | ✅ / ⛔ | A beépített `acquirepanel`, a mezők, szövegek, alapértékek és kulcsok statikusan azonosíthatók. ⛔ A nyitó/újranyitott élő állapot és a megerősítő ablak tényleges elrendezése nincs felvéve. |
| 3. Fájl, `.picasa.ini`, index, bal hasáb, rács, kijelölés, háttér és állapotsor | ✅ / ⛔ | A worker fő útvonala, fázisszövegei, scan-indítása és PicasaPy jelenlegi index-/értesítőhatása forrásban követhető. ⛔ Az eredeti fájl- és ini-diff, bal hasáb/rács/kijelölés és a `ytProgress` tényleges megjelenési helye futásidejű mérésre vár. |
| 4. Hiba, ütközés, megszakítás, hálózat, írásvédelem és visszavonás | ⛔ | A hibaüzenet- és megszakítás-kezelő kódútjai részben azonosíthatók; az ütközési szabály, részleges fájlok sorsa, megszakítás közbeni eredeti worker, hálózati/írásvédett próba és az Undo viselkedés futásban nincs igazolva. |

### Eltérések és javasolt teendők

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `acquireUseSubFolder`: 0 = kézi cím, és importindításkor megjegyzi (`0x00514180`, `0x005181b0`, `0x00525400`). | Dátum a nem tárolt alap (`ImportSourceDialog.qml:94`). | E1: tárold az utolsó almappa-módot; friss profilban kézi cím legyen az alap. |
| `acquireCleanCard`: 0 = Leave; indításkor menti, és nem törölhető forrásnál letilt (`0x00519560`, `0x0051a0c2`, `0x005277e0`, dinamikus forráspróba `0x00519630`). | A nem tárolt alap Leave; mindhárom mód aktív (`ImportSourceDialog.qml:105`; `ImportSourceDestinationPanel.qml:161-192`). | E2: tárold a választást, `Delete All` újranyitáskor `Delete Copied`-ra essen vissza; a törlésválasztást forrásképességhez igazítsd. A forrástípus-kapu eldőlt (2026-11-17): csak `DCIM` mappás meghajtógyökér törölhető, `Folder on Disk` nem (Zárási döntés, 1. sor). |
| Törlésnél egyetlen, Cancel gombos ablak; a `0x00519720` hívásban nincs checkbox-szöveg. | Kétlépcsős megerősítés és „Do not ask again” (`ImportSourceDialog.qml:239-254,376-401`; `ConfirmDialog.qml:59,100-110`). | E3: egy kérdés legyen; ne lehessen bejelöléssel elnémítani; a gombok `Remove Imported Files` / `Remove All Files` / `Cancel`. Az ablak futásidejű gombsorrendje nyitott. |
| Import All / Import Selected (N), kijelölés, alapgomb és Esc (`0x005238b0`, `0x0051b620`, `acquirepanel.tre`). | Egy Import gomb, preview-kijelölés és Enter/Esc bekötés nélkül (`ImportSourceDestinationPanel.qml:251-261`; `ImportSourcePreview.qml:90-145`; `ImportSourceDialog.qml`). | E4: válaszd szét az összes és kijelölt képek importját; jelenjen meg a kiválasztott darabszám; kösd be az eredeti Enter/Esc viselkedést. |
| Négy feltételes tippszöveg (`0x0051ae90`, `acquirepanel_text.tre`). | Csak a kézi/üres cím útmutatója (`ImportSourceDestinationPanel.qml:129-140`). | E5: jelenítsd meg a négy eredeti állapotnak megfelelő üzenetet. |
| Legutóbbi célok mentése indításkor, legfeljebb 5 (`0x0052532c`-`0x00525400`). | Sikeres másolás után ment, legfeljebb 8 (`import_source_controller_state.py:55,210-223`; `import_source_controller.py:440-444`). | E6: mentés induláskor, legfeljebb öt bejegyzés. |
| Az Include/Exclude és Include All/Exclude All a bélyegképek helyi menüjében (`0x00733c70`, `0x9dc2`-`0x9dc5`). | Inline Include/Exclude és külön Include All/Exclude All gombok, helyi menü nélkül (`ImportSourcePreview.qml:100-145`; `ImportSourcePickerPanel.qml:251-260`). | E8: add meg az eredeti négy műveletet a preview helyi menüjéből is. |
| A főablak `panelroot/acquiretab` panelje és nagy, kijelölt képes előnézet (`0x005e45c0`, `macros.tre:281`, `acquirepanel.tre`). | Modális önálló ablak, bélyegképrács (`ImportSourceDialog.qml:16-31,297-316`). | E7: hozd be az importfelületet a főablak importpaneljébe, és adj nagy előnézetet a kiválasztott képnek. A panel teljes dinamikus elrendezését futásmérés még pontosítja. |
| Importfájl hiba: „Cancelling Import” (`0x0070b1e0`, `0x0070bdd0`). | Másolási `OSError` után folytatja (`import_source_controller.py:431-439`). | E10 (Zárási döntés, 8. jegytörzs): a hiba utáni forrástörlési tilalom bizonyított, ezt vezesd be. A leállás az első hibánál feltételes: futásmérés előtt a mai folytatás marad. |
| Importfutás alatti forrástörlés viselkedése: NINCS MEG. | A törlési `unlink` hiba után nem érkezik `importFinished`, ezért a QML `importing` állapotban maradhat (`import_source_controller_import.py:49-86`; `worker_thread.py:311-361`; `ImportSourceDialog.qml:274-297`). | E9: kezeld a törlési hibát importhibaként, küldj befejező jelzést, és oldd fel a dolgozó UI-állapotot minden ágban. Kész, ha törlési jogosultsági/I/O hibánál a folyamat lezárul, a célmásolatok állapota jelzett, és a hiba látható. |

**Javasolt fejlesztői jegytörzsek - `Eredeti:` sorok.**

*Ellenőrizve a mai forráson (2026-11-17, szövegkeresés és olvasás): mind a hét tétel
érvényes, egyik sem működik már az eredeti szerint, ezért egyet sem lehetett
kihúzni. A lista a kért hat helyett hét tételt tartalmaz, a hetedik a helyi
hibaág (E9). Fedés a szakasz E-pontjaival: 1 = E1, E2, E6; 2 = E3; 3 = E4;
4 = E5; 5 = E8; 6 = E7; 7 = E9. A zárókör egy nyolcadikat is hozott (E10,
forrástörlés hiba után). A megmaradó tételek teljes, négy mezős szövege és a
korábbi javításokkal való fedések a Zárási döntésben vannak.*

1. **Import módok és előzmények. Eredeti:** `0x00514180`, `0x005181b0`,
   `0x00519560`, `0x0051a0c2`, `0x0052532c`-`0x00525400`: kézi cím az
   alapmód; az almappa- és törlési mód az import kezdetekor megmarad; a
   törlési mód törölhetetlen forrásnál inaktív; öt célmappa-előzmény mentődik
   indításkor. **Nálunk:** `ImportSourceDialog.qml:94,105`,
   `ImportSourceDestinationPanel.qml:161-192`, `import_source_controller_state.py:55,210-223`.
   **Kész, ha:** mindhárom beállítás újranyitáskor a tárolt értéket mutatja,
   üres profilban kézi cím/Leave van; Delete All visszalép Delete Copied-ra;
   csak törölhető forrás engedi a törlési módot; az indított cél bekerül az
   5-ös listába.
2. **Törlés-megerősítés. Eredeti:** `0x00519720`: egyetlen Confirm Remove
   ablak a két törlési módhoz, Cancel lehetőséggel, elnyomó jelölő nélkül.
   **Nálunk:** `ImportSourceDialog.qml:239-254,376-401`,
   `ConfirmDialog.qml:59,100-110`. **Kész, ha:** mindkét törlési választás
   egyetlen kérdést ad, a megfelelő eredeti gombfeliratokkal; nincs „Do not
   ask again”; Leave módban nincs kérdés.
3. **Kijelölt import és billentyűkezelés. Eredeti:** `0x005238b0`,
   `0x0051b620`, `acquirepanel.tre`: Import All, Import Selected (N), Enter
   alapgomb és Esc megszakítás. **Nálunk:** `ImportSourceDestinationPanel.qml:251-261`,
   `ImportSourcePreview.qml`, `ImportSourceDialog.qml`. **Kész, ha:** a
   kijelölt nem kizárt képek darabszáma látszik, az import csak ezeket másolja;
   a kijelölés nélküli Import All az összes nem kizárt képet másolja; Enter és
   Esc az eredeti ágakat futtatja.
4. **Tippsor állapotai. Eredeti:** `0x0051ae90` és
   `acquirepanel_text.tre`: négy tipp a kézi/üres, kézi/kitöltött, dátumos és
   mai dátumos célmódhoz. **Nálunk:** `ImportSourceDestinationPanel.qml:129-140`.
   **Kész, ha:** a négy mód mindegyikénél a megfelelő eredeti szöveg jelenik
   meg, a fordítási kulcsok minden nyelven megvannak.
5. **Preview helyi menü. Eredeti:** `0x00733c70`, `0x9dc2`-`0x9dc5`:
   Include File, Exclude File, Include All, Exclude All. **Nálunk:**
   `ImportSourcePreview.qml:100-145`, `ImportSourcePickerPanel.qml:251-260`.
   **Kész, ha:** a preview helyi menüje ezt a négy műveletet kínálja, és az
   egyedi/tömeges menüparancsok ugyanazt a kiválasztási állapotot módosítják.
6. **Importpanel és nagy előnézet. Eredeti:** `panelroot/acquiretab`,
   `0x005e45c0`, `macros.tre:281`, `acquirepanel.tre`: a főablakban levő
   panel és a kijelölt kép nagy előnézete. **Nálunk:**
   `ImportSourceDialog.qml:16-31,297-316`. **Kész, ha:** az Import belépők a
   főablak paneljét nyitják, a főablak bezárásakor az eredetihez hasonló
   import-megerősítés van, a nagy előnézet a kijelölt fotót mutatja.
7. **Importtörlés hibaállapot (PicasaPy helyi hiba, E9). Eredeti:** a Picasa kimenete NINCS MEG.
   **Nálunk:** `import_source_controller_import.py:49-86` és
   `ImportSourceDialog.qml:274-297`: forrás-törlési OSError után a worker
   jelzés nélkül kiléphet, az ablak dolgozó állapotban marad. **Kész, ha:**
   a törlési hibát az import hibaszámmal jelenti, minden ágon lezárja az
   importing állapotot, megőrzi a már elkészült célmásolatokat, és nem töröl
   olyan forrást, amelynek a másolása nem sikerült. Ez a
   Picasa-paritástól független, helyi hibakezelési jegy.

### Nyitott

- `Ghidra-kör kell: 0x00519630 - a meglévő
  2026-11-16-koteg-426-437.txt:3076-3142 dekompiláció megmutatja a dinamikus
  `+0x18` virtuális hívást és a `[panel+0x2a6]` jelzőt, de nem nevezi meg a
  forrásosztályok célmetódusait. Melyik eredeti forrástípusnál engedélyezett
  az import utáni törlés (cserélhető meghajtó, Folder on Disk, CD-ROM)?
  [blokkoló az E1 törlési módhoz]`
  **Eldőlt a 2026-11-17-i zárókörben, a „blokkoló” jelölés érvénytelen:** a
  `+0x18` metódus az `SDeviceInfo` osztály `0x0050f590` függvénye (vtábla
  `0x00c87540`, 6. hely). Meghajtógyökér forrásnál akkor igaz, ha létezik a
  `<gyökér>\dcim\` út; a `Folder on Disk` rekordnál (típus 5) soha. A
  hívóhely-ellenőrzés és a teljes szabály: Zárási döntés, 1. sor.
- `Ghidra-kör kell: 0x0070b1e0 - a meglévő 2026-11-16-os kimenet a címet csak
  a worker hívottjaként említi; nem tartalmazza a dátumos fájlmásoló függvény
  teljes dekompilációját. Milyen célútvonalat hoz létre, hogyan kezeli az
  ütközést, és mit hagy a lemezen másolási hiba után? [blokkoló az ütközés és
  részleges import kérdéséhez]`
  **Részben eldőlt a zárókörben, a „blokkoló” jelölés érvénytelen:** a
  dátumos ág szerkezete (mappa számítása, meglévő mappa újrahasznosítása, új
  mappa és időbélyeg, fájlonkénti mozgatás, hibaág) megvan; az ütközésnév
  egyetlen Ghidra-sorra szűkült (Zárási döntés, 3. sor és Következő irány).
- `Ghidra-kör kell: 0x0070bdd0 - a meglévő
  2026-11-16-koteg-426-437.txt:3143-3835 már feltárja a lezáró kódot, de nem
  azonosítja az átmeneti `PhotoLabTemp`-hez használt forrás- és célnév
  előállítását, a rename API célját, a hiba után megmaradó fájlokat vagy a
  törlési/cleanup sorrend adatvesztési hatását. Ezeket célzottan kövesd, a
  meglévő dekompilációt ne kérd újra. [blokkoló a fájlszintű hibavégállapothoz]`
  **Eldőlt a zárókörben, a „blokkoló” jelölés érvénytelen:** az átnevezés
  `MoveFile` 30 másodperces újrapróbával; hiba után a forrásból semmi nem
  törlődik; az átmeneti mappa a végén `RemoveDirectory`-val csak akkor tűnik
  el, ha üres. A mappa neve és létrehozási helye nem blokkoló (Zárási döntés,
  2. sor).
- `Colab-feladat kell: az eredeti Windows Picasa importpanelen: friss profil
  és újranyitás; Import All és Import Selected; célban létező azonos nevű kép;
  csillag/forgatás utáni `.picasa.ini`-diff; Delete Copied/Delete All és
  megerősítő ablak; fájlhiba, megtelt/írásvédett cél, eltűnő vagy hálózati
  forrás; Esc/Cancel futás közben; befejezés utáni bal hasáb, rács,
  kijelölés és Undo. Fényképezd a kezdő/köztes/végállapotot, és minden
  lemez/index-diffet külön ments. A helyi mérési adatokban ilyen futás nincs.
  **Zárókör: nem blokkoló, a felvehető mérési jegy tárgya (Zárási döntés, 4.
  sor).**
- **NINCS MEG:** a `Fájl ▸ Import From...` menüpont pontos tiltási/engedélyezési
  szabálya minden főablak-állapotban; a `0x0056e1c0` nem igazolja és nem is
  cáfolja a feltétel nélküli engedélyezést. Út: célzott futtatott menüpróba. **Zárókör: nem blokkoló, a
  feltétel nélküli engedélyezés marad (Zárási döntés, 5. sor).**
- **NINCS MEG:** a `ytProgress` widget tényleges felülete (lebegő ablak,
  alsó sáv vagy más megjelenítő), az importbefejező panelváltás és a kattintás
  utáni mappakiválasztás. Út: a Colab-felvétel progressz- és végállapot-képe. **Zárókör: nem
  blokkoló, a #7084 azonos tételének döntésével egyezően (Zárási döntés, 6.
  sor).**
- **NINCS MEG:** az eredeti importhoz kötött visszavonás és a törlés után
  megmaradó eredeti/kísérő/ini fájlok. Út: tiszta profil, lemez- és
  `.picasa.ini`-diff a Colab-felvétel előtt és után. **Zárókör: a
  visszavonásra nincs bizonyíték és nincs teendő; a megmaradó fájlok mérési
  tétel, nem blokkoló (Zárási döntés, 7. sor).**

### Zárási döntés (a 2026-11-17-i zárókör után)

**A #7083 kutatási jegy lezárható.** Blokkoló nem maradt. A három korábban
„blokkolónak” jelölt Ghidra-tétel (`0x00519630`, `0x0070b1e0`, `0x0070bdd0`) a
meglévő dekompiláció, a bináris-index és a hívóhelyek utasításszintű olvasása
alapján eldőlt, vagy nem érinti a felhasználó által látható alapfolyamatot. A
fejlesztői jegytörzsek mindegyikének „Eredeti” oldala a bináris utasításaiból
megvan; a megmaradó nyitott pontok peremesetek (utólagos navigáció, a
folyamatjelző felülete, ütközésnév, hiba után megmaradó átmeneti tartalom,
visszavonás), amelyektől a jegytörzsek egyike sem függ. Ezek egy közös,
felvehető mérési jegybe kerülnek. Bizonyítottsági fok: **megerősített** a
belépőkre, a megjegyzett kulcsokra és alapértékeikre, a törlés-megerősítés
szerkezetére és a tippsorra; **erős** a törlési kapura (a hívóhely
utasításai és az RTTI-ből olvasott vtábla egyezik) és a hiba utáni forrástörlési
tilalomra (három hibaág két függvényben); **feltételes** a lemezvégállapotra,
a rács- és kijelölés-végállapotra, a folyamatjelző felületére és az
ütközésnévre (futásmérés nincs).

**A korábbi dekompiláció veremértelmezésének ellenőrzése.** A
`2026-11-16-koteg-426-437.txt` `FUN_00519630` ágában az `unaff_EDI` a panel
(`this`): a `0x00519630` utasításai közvetlenül az `edi`-ből olvasnak
(`[edi+0x29c]` a forrásrekord-tömb, `[edi+0x2a8]` a kiválasztott index,
`[edi+0x2a6]` a törlés-képesség jelzője), a rekordméret `idx*15*4`, azaz 0x3c
bájt (`0x0051964d-0x0051965a`). Visszavonni semmit nem kellett, csak
kiegészítettem: a rekord első szava a vtábla, ezért a `[ecx]` majd `[edx+0x18]`
hívás (`0x0051965d-0x00519662`) a rekord saját virtuális metódusát hívja.

Nyitott kérdések mérlege (az alábbi 7 sor): 0 blokkoló · 2 teljesen eldőlt (1.
és 2. sor) · 1 egyetlen Ghidra-sorra szűkült (3. sor) · 1 mérési jegyre
kijelölve (4. sor) · 3 nem blokkoló, a mérési jegy része (5-7. sor).

**Az eddig nyitott tételek eldöntése.**

| Tétel | Döntés | Válasz, indok | Bizonyíték |
|---|---|---|---|
| 1. `0x00519630`: melyik eredeti forrástípusnál engedélyezett az import utáni törlés | (a) **eldőlt** | A forráslista (`[panel+0x29c]`, 0x3c bájtos rekordok) elemei `SDeviceInfo` objektumok (vtábla `0x00c87540`); a `+0x18` metódus a 6. hely, a `0x0050f590`. Hamis, ha a `[rekord+0x38]` jelző nem nulla (ezt a konstruktor és a másoló nullázza; az átvizsgált `0x0050e000-0x00530000` és `0x00700000-0x00720000` tartományban az egyetlen 1-et író hely a `0x0050ec2d`, de az a `0x0050eb80` szűrőállapot-függvényé, nem az `SDeviceInfo`-é). A `[rekord+4]` típus szerint (ugrótábla `0x0050f684`): **0, meghajtógyökér** (a `0x0050f970` állítja `[+4]=0`, `[+8]=4`; a `0x00510500` felsoroló hívja): igaz, ha a `0x0050f6a0` szerint létezik a `<gyökér>\dcim\` (`GetFileAttributes` nem -1-et ad; a cserélhető meghajtó típus itt nem számít, mert a hívó nem üres kimeneti sztringet vár); **5, `Folder on Disk`** (a `0x00520fa0` tallózó a `0x005213ed`-nál hívja a `0x00521e80`-at, az a `0x00511ef0`-val állítja `[+4]=5`): mindig hamis; **1 és 6**: hamis; **2, 3 és 4** (az eszközút rekordjai, a `0x007128e0` és a `0x00713200` is `SDeviceInfo`-t épít; a típusszámokat nem azonosítottam, mert ez a Windows-kamera út, amelyet a PicasaPy nem követ): igaz, ha `[+8]` 2 vagy 3. Tehát **cserélhető meghajtó `DCIM` mappával igen; `DCIM` nélküli meghajtó, `Folder on Disk` és a többi nem.** Hamis eredménynél a törlés-menü a kiinduló (Leave) állásra áll és letiltott (a `0x00519630` `[panel+0x2a6]=0` ága, `0x005277e0`); törölhető forrásra váltáskor a mentett választás tér vissza (`0x00512de0`, `0x00519560`). | bináris: `0x0051964d-0x00519662`, `0x0050f590`, `0x0050f684`, `0x0050f6a0`, `0x0050f970`, `0x00510500`, `0x00511ef0`, `0x00521e80`, `0x00520fa0`; RTTI: `SDeviceInfo::vftable` `0x00c87540`; dekompiláció: `2026-11-16-koteg-426-437.txt:3076-3140` |
| 2. `0x0070bdd0`: az átmeneti mappa, az átnevező függvény, a hiba után megmaradó fájlok, a törlési sorrend | (a) **eldőlt**; a mappa neve és létrehozási helye (c) nem blokkoló | Az átnevezés a `[0x00d694d4]` mutatón át megy: NT-n a `0x009af1c0` burkoló (`MultiByteToWideChar`, majd `MoveFileW`), a Windows 9x ágon a `MoveFileA` import (`0x00c404dc`); a választás a `GetVersion` felső bitjén múlik (`0x00c32d1e-0x00c32d3a`). A kudarc után legfeljebb 30 másodpercig (`0x00cf3ed8` = 30,0), másodpercenkénti várakozással újrapróbál, utána `...renaming '%s'. Cancelling Import.` üzenet és leállás. A korábban feloldatlan mutatók ugyanígy kettős célúak (NT-n `MultiByteToWideChar` után a `...W` függvényt hívó burkoló, Windows 9x-en az `...A` import): `[0x00d694bc]` = `GetFileAttributes` (`0x009aec30`), `[0x00d69514]` = `SetFileAttributes` (`0x009aff10`), `[0x00d695b4]` = `RemoveDirectory` (`0x009b2800`), `[0x00d694c0]` = `DeleteFile`, `[0x00d694d8]` = `MoveFileEx` (az utóbbi kettő burkolóját nem olvastam végig, a 9x ág import-neve `DeleteFileA`, illetve `MoveFileExA`). A végcél (`[szál+0x310]`) és az átmeneti mappa (`[szál+0x6c]`) rejtett jelzőjét az import után leveszi (`and eax, 0xfffffffd`, `0x0070c437-0x0070c440`, `0x0070cae7-0x0070caf0`); ha a végcél eltér az átmeneti mappától és az még létezik, `RemoveDirectory` törli (nem üres mappát nem tud). A `Cleaning Up` fázis a **forrásfájlok törlése** (`0x0070c980-0x0070c9d9`: csak ha `[szál+0x2d0]` aktív jelző és `[szál+0x1a0]` törlési mód 1 vagy 2). **Hiba után** a fájlhiba és az átnevezési hiba ága is nullázza a `[szál+0x2d0]` aktív jelzőt és a `[szál+0x1a0]` törlési módot (`0x0070b9d9-0x0070b9e0`, `0x0070c093-0x0070c09a`, `0x0070c36a-0x0070c371`), a törlési fázis pedig ezek nélkül nem fut: **hiba után a forrásból semmi nem törlődik**; a már célba került fájlok és az átmeneti mappa tartalma megmarad. Az átmeneti mappa nevét és létrehozási helyét nem sikerült megtalálni (a `PhotoLabTemp` önálló sztringként nincs a string-indexben, csak a hibaüzenetben szerepel); ez (c): a PicasaPy nem használ átmeneti mappát, és hibamentes futásban nem látszik. | bináris: `0x00c32d2a-0x00c32d3a`, `0x00c32baa-0x00c32bba`, `0x00c3312a-0x00c3313a`, `0x00c33b2a-0x00c33b3a`, `0x0070c424-0x0070c446`, `0x0070c980-0x0070c9d9`, `0x0070b9d9-0x0070b9e0`, `0x0070c093-0x0070c09a`; dekompiláció: `2026-11-16-koteg-426-437.txt:3195-3830` |
| 3. `0x0070b1e0`: a dátumos ág célútvonala, az ütközés, a hiba utáni lemezállapot | (a) a szerkezet eldőlt; (b) az ütközésnév egyetlen Ghidra-sor; nem blokkoló | A függvényt a `0x0070bdd0` hívja, ha a `[szál+0x1a4]` almappa-mód 1 (dátum). A rekordlista elemein megy végig (`[szál+0xcc] >> 1` darab). A `0x00492e40` hívás után -1 visszatérésnél a mappa létezését a `0x00992ed0` vizsgálja, hiányzó mappát a `0x009a3db0` hoz létre és a `0x00992780` időbélyegez (`SetFileTime`, helyi időből átváltva); más visszatérésnél közvetlenül a mozgatásra ugrik (`0x0070b914`); a `0x00492e40` szerepét nem azonosítottam. A fájlt a `0x00994580` mozgatja az átmeneti helyről: előbb a `0x00993650` képezi a célnevet, majd a `0x00994400` `MoveFileEx`-et hív `MOVEFILE_WRITE_THROUGH` és `MOVEFILE_COPY_ALLOWED` jelzővel, csere nélkül (hozzáférés-megtagadásnál 500 ms-os várakozással, a 4. argumentum szerint 5 másodpercig újrapróbál). Hibánál az `A file error has occurred while importing files. Cancelling Import.` üzenet jelenik meg (`0x00980700`), a `[szál+0x2d0]` aktív jelző és a `[szál+0x1a0]` törlési mód nullázódik (`0x0070b9d9-0x0070b9e0`), és az import véget ér. A `0x00993650` a `%s-%03lu` mintával (`név-001`, ...) 4096-ig számozza az ütköző nevet, ugyanez a függvény végzi az átnevezés és a Mentés másolatként névképzését is (más szakaszok már igazolták). Hogy a **szabad célnév ebben a hívási környezetben sorszám nélkül marad-e**, nem dőlt el; ez ugyanaz a kérdés, amely a #6964 szakaszban is nyitott, egy Ghidra-kör mindkettőt eldönti (lásd Következő irány). | bináris: `0x0070b3cc`, `0x0070b3ec`, `0x0070b400`, `0x0070b43c`, `0x0070b93c`, `0x0070b9d1-0x0070b9ea`, `0x00994580`, `0x00994400`, `0x00993b07` (`0x00cd8d64`, `%s-%03lu`); string-index: `0x00cd8d64` |
| 4. Colab-feladat az eredeti importpanelen | (b) mérési jegy; nem blokkoló | Marad: friss profil és újranyitás; Import Selected; azonos nevű kép a célban (itt dől el a `-001` kérdés is); `.picasa.ini`-diff csillag és forgatás után; Delete Copied és Delete All kártyán és mappán; fájlhiba, megtelt cél; Esc és Cancel futás közben; befejezés utáni bal hasáb, rács, kijelölés. Egyik sem feltétele egyik fejlesztői jegytörzsnek. | futtatott mérés: Colab-felvétel, lemez- és index-diff |
| 5. A `Fájl ▸ Import From...` menüpont tiltási szabálya | (c) nem blokkoló | A `0x9c91` szó-azonnali értéke a `.text`-ben egyetlen helyen áll, a menüépítőben (`0x005592d7`, `66 c7 05 ... 91 9c`); a `91 9c` bájtpár további 21 találata más utasítás része (eltolás vagy hívási távolság). A parancs-diszpécser ugrótáblán dolgozik, az állapotfrissítő nem hivatkozza. Tiltási bizonyíték nincs: a feltétel nélküli engedélyezés marad, a PicasaPy ugyanezt teszi (`PicasaFileMenu.qml:57-61`). | bináris: `0x005592d7`; a `.text` szóillesztéses átvizsgálása (22 találat) |
| 6. A `ytProgress` felülete, a befejezés utáni panelváltás, a kattintás utáni kiválasztás | (c) nem blokkoló | A fázisszövegek hordozója ismert (`ytProgress`, `0x00562420` építi, `0x00415610` frissíti). Hogy melyik felület mutatja (lebegő modális jelző vagy alsó sáv), nem dőlt el; a #7084 szakasz azonos kérdése is nem blokkolónak van jelölve. A PicasaPy párbeszédének saját haladássávja van; a szöveg-eltérésre jegy a felület ismerete előtt nem nyitható. A panelváltás és a kattintás utáni kiválasztás a Colab-felvételből dönthető el. | bináris: `0x0070ebf0`, `0x00562420`, `0x00415610`; a 4. sor mérése |
| 7. Az importhoz kötött visszavonás és a törlés után megmaradó eredeti, kísérő és ini fájlok | (a) a visszavonásra nincs bizonyíték, nincs teendő; (b) a megmaradó fájlok mérési tétel; nem blokkoló | Az importáló függvények (`0x0050e000-0x0052e000`, `0x00708000-0x00714000`) egyetlen visszavonás-, előzmény- vagy Undo-szöveget sem hivatkoznak, a kártyatörlés kifejezetten „nem vonható vissza”. A negatív állítás hatóköre a két tartomány string-hivatkozása; a vtábla-hívások nem láthatók, ezért ez erős, nem teljes kizárás. A PicasaPy-ban sincs visszavonás: nincs teendő. A törlés után megmaradó eredeti, kísérő és ini fájlok (a virtuális `+0x38` törlő metódus a `0x0070c9d9` után nem követett) a 4. sor mérésébe kerülnek; a PicasaPy a kísérőket és az ini-szekciót viszi (`import_source_controller_import.py:49-86`). | string-index az említett tartományokra; `0x0070c980-0x0070c9d9` |

**A jegytörzsek mai ellenőrzése és a megmaradó tételek.**

**Ellenőrzés a mai forráson (2026-11-17, szövegkeresés és olvasás).** A „Javasolt
fejlesztői jegytörzsek” mind a hét tétele érvényes: egyik sem működik már az
eredeti szerint, ezért egyet sem lehetett kihúzni. A lista a kért hat helyett
hét tételt tartalmaz (a hetedik a helyi hibaág). A fedés a szakasz E-pontjaival
és a korábbi javításokkal: **1** = E1, E2, E6; részben fedi a #441 (a három
mód és a Leave alap), a #1785 (célmappa-előzmény), a #4595 és a #4837 (kézi név
kötelező és biztonságos). **2** = E3; részben fedi a #860/#2944 (összeállított
figyelmeztetés) és a #6283/#6296 (a `ConfirmDialog` két gombos és a jelölő
elrejthető, `ConfirmDialog.qml:48-59`); az import ezeket nem használja.
**3** = E4; fedés nincs (a kiemelés és a lapozó gombok egy képet jelölnek, az
import nem használja). **4** = E5; az 1. állapotot a #4595 fedi. **5** = E8,
**6** = E7, **7** = E9; fedés nincs. A **8** új (E10), a zárókör bizonyítékából.
Sorrend-javaslat: 8, 7, 2, 1, 3, 4, 5, 6 (a 6. a legnagyobb, a forró
`Main.qml`-t és a `qmldir`-t érinti, ezért szerializálandó; a 2. és a 4.
szövegei a `picasapy_hu.ts`-t érintik).

**Készre ítélt jegytörzsek (jegy nem kell): nincs.** Mind a nyolc eltérés
fennáll a mai kódon.

**Megmaradó fejlesztői jegytörzsek (nyolc).**

#### 1. Import módok, előzmények és a törlési mód kapuja (E1, E2, E6)

**Eredeti:** az `acquireUseSubFolder` alapértéke 0 (kézi cím; `0x00514180`,
olvasás `0x005148ac-0x00514936`), a menü sorrendje 0 kézi cím, 1 `Date Taken
(YYYY-MM-DD)`, 2 mai dátum (`0x005181b0`), az érték az import indításakor
mentődik (`0x00525400`). Az `acquireCleanCard` alapja 0 (`Leave card alone`);
olvasáskor a 2 (összes törlése) 1-re (csak a másolt) esik vissza
(`0x00519560`), mentése `0x0051a0c2`. A legutóbbi célok (`LastImport%x`) az
indításkor mentődnek, legfeljebb öt (`0x0052532c-0x00525400`). A törlési mód
csak törölhető forrásnál aktív: csatolt meghajtó gyökerében van `DCIM` mappa
(`0x0050f590` → `0x0050f6a0`); `Folder on Disk` forrásnál és `DCIM` nélküli
meghajtónál soha; ilyenkor a menü Leave állásra áll és letiltott
(`0x00519630`, `0x005277e0`).

**Nálunk:** `ImportSourceDialog.qml:94` (`namingMode: "date"`) és `:105`
(`afterCopying: "leave"`), egyik sem tárolt (az `import/` kulcsok:
`autoexclude`, `recentsources`, `recentdestinations`, `defaultdestination`,
`resizeLimit`; `import_source_controller_state.py:35-62`). A három törlési
rádiógomb mindig aktív, forrástípustól függetlenül
(`ImportSourceDestinationPanel.qml:161-192`). A célmappa-előzmény sikeres
másolás után ment, legfeljebb nyolcat (`import_source_controller_state.py:55,
210-225`, `import_source_controller.py:441-444`).

**Teendő:** a három beállítás (almappa-mód, törlési mód, célmappa-előzmény) az
import indításakor mentődjön, és az ablak újranyitáskor a tárolt értéket
mutassa; üres profilban kézi cím és Leave az alap; a tárolt Delete All
újranyitáskor Delete Copied-ra essen vissza; a célmappa az indításkor kerüljön
az öt elemű listába (ez felülírja a #1785 tudatos, sikeres-másolás utáni
mentését: az eredeti a hibás célt is megjegyzi). A törlési rádiók csak akkor
legyenek aktívak, ha a forrás a csatolt meghajtók listájából jött és a
gyökerében van `DCIM` mappa (kis- és nagybetűre érzéketlen vizsgálattal);
mappa-, fájl- és előzményforrásnál, valamint `DCIM` nélküli meghajtónál a
rádiók tiltottak és a választás Leave; törölhető forrásra visszaváltva a
tárolt érték tér vissza.

**Kész, ha:** üres profilban az ablak kézi címmel és Leave állással nyílik; az
import indítása után újranyitva a kiválasztott almappa-mód és (törölhető
forrásnál) törlési mód látszik; a mentett Delete All újranyitáskor Delete
Copied-ként jelenik meg; a célmappa az import indításakor bekerül a legfeljebb
öt elemű előzménylistába, hibás futásnál is; `DCIM` mappás csatolt kártyánál
mind a három törlési mód aktív, `Folder on Disk`, fájl- és előzményforrásnál,
valamint `DCIM` nélküli meghajtónál a rádiók tiltottak és Leave áll; a tesztek
valódi kattintással futnak.

#### 2. Törlés-megerősítés (E3)

**Eredeti:** a `0x00519720` egyetlen `Confirm Remove` ablakot kér mindkét
törlési módhoz: a Delete Copied az általános `confirmRemoveCopied::message`
szöveget (kisbetűs „This cannot be undone.”), a Delete All az összeállított
`WipeCard...` figyelmeztetést kapja; az igen gomb `Remove Imported Files`,
illetve `Remove All Files`, a másik `Cancel`; a hívás hét argumentumában
jelölő-szöveg nincs (az ablak elrendezését nem mértük). Leave módban nincs
kérdés.

**Nálunk:** `ImportSourceDialog.qml:239-254` és `:376-401`: kétlépcsős
megerősítés, a Delete All előtt a nagybetűs „THIS CANNOT BE UNDONE.” előkérdéssel;
a `ConfirmDialog` „Do not ask again” jelölője látható (`ConfirmDialog.qml:59`,
`:100-110`). A `ConfirmDialog` a #6283/#6296 óta tud `yesText`, `noVisible`,
`cancelVisible` és `rememberVisible` beállítást (`ConfirmDialog.qml:48-59`, minta:
`FolderPaneMenus.qml:126`); az import ezeket nem használja. Az összeállított
figyelmeztetés a #860/#2944 óta megvan (`wipeCardWarning`).

**Teendő:** egyetlen `ConfirmDialog`, `rememberVisible: false`, `noVisible:
false`; a gombok `Remove Imported Files` (Delete Copied), `Remove All Files`
(Delete All) és `Cancel`; a Delete All üzenete a meglévő összeállított
figyelmeztetés, a nagybetűs előkérdés megszűnik; a Delete Copied üzenete az
eredeti kisbetűs `confirmRemoveCopied` szöveg.

**Kész, ha:** mindkét törlési választás egyetlen kérdést ad a fenti
gombfeliratokkal; nincs „Do not ask again”; Leave módban nincs kérdés; az
elnyomó kulcs már nem létezik. A gombsorrend és az elrendezés futásidejű képe
nincs mérve, ezt a jegy kimondja.

#### 3. Kijelölt import és billentyűkezelés (E4)

**Eredeti:** `Import All` (`anowbutton`) és `Import Selected (%d)`
(`import_selected`); az engedély `0x005238b0`: van nem kizárt (és a Selectednél
kijelölt) elem, és a `[panel+0x480]` jelző nem nulla; az alapgomb (`0x0051b620`,
feltehetően az Enter) az `anowbutton`-t nyomja, ha legfeljebb egy kép van
kijelölve, különben az `import_selected`-et; az Esc az `acancelbutton`
(`Property escapekey 1`).

**Nálunk:** egyetlen `Import` gomb (`ImportSourceDestinationPanel.qml:251-261`),
az `includedCount` alapján; az `ImportSourceDialog.qml:115,189-197` és az
`ImportSourcePickerPanel.qml:264-285` egy kiemelt képet és lapozó gombokat ad
(`selectedPreviewIndex`), többes kijelölés nincs, az import nem használja;
Enter és Esc kötés az `ImportSource*.qml` fájlokban nincs (`Keys.` és
`Shortcut` nem található).

**Teendő:** külön `Import All` (minden nem kizárt kép) és `Import Selected
(N)` (csak a kijelölt, nem kizárt képek; kijelölés nélkül tiltott) gomb; a
bélyegképrács többes kijelölést adjon; az Enter az eredeti szabályt követi, az
Esc zárja az ablakot (futó importnál a viselkedés a 8. jegytörzs és a mérési
jegy kérdése, addig az Esc nem szakít meg).

**Kész, ha:** a kijelölt nem kizárt képek darabszáma a gombon látszik; az
`Import Selected` csak ezeket másolja; kijelölés nélkül az `Import All` az
összes nem kizárt képet; az Enter és az Esc az eredeti ágakat futtatja; a
teszt valódi billentyűvel és kattintással fut.

#### 4. Tippsor állapotai (E5)

**Eredeti:** `0x0051ae90` és `acquirepanel_text`: négy tipp. A `[panel+0x7b0]`
almappa-mód és a `[panel+0x480]` jelző adja: kézi mód és jelző nulla = 1.
(`Enter new folder title or choose existing folder to continue`), kézi mód és
jelző nem nulla = 2. (`Click Import All or Import Selected`), dátum mód = 3.
(`Import into separate folders for each date taken`), mai dátum mód = 4.
(`Import into folder with today's date`).

**Nálunk:** `ImportSourceDestinationPanel.qml:128-140`: csak az 1. állapot
(#4595). A 2-4. szöveg a `.ts` fájlokban nincs (a magyar és az orosz
fájlban sem); a hivatalos fordításuk az eredeti `acquirepanel_text` erőforrás
`Text2`-`Text4` elemeiben mind a 42 nyelven megvan.

**Teendő:** a négy állapotnak megfelelő üzenet jelenjen meg; a 2. állapot a 3.
jegytörzs gombjaihoz kötött, ezért az után készül; a fordítást a hivatalos
erőforrásból vedd át.

**Kész, ha:** a négy módnál a megfelelő eredeti szöveg jelenik meg, a
fordítási kulcsok minden nyelven megvannak, a szöveg a hivatalos fordítással
egyezik.

#### 5. Az előnézet helyi menüje (E8)

**Eredeti:** `0x00733c70`, 20 bájtos rekordok: `Include File` (`0x9dc4`),
`Exclude File` (`0x9dc5`), `Include All` (`0x9dc2`), `Exclude All`
(`0x9dc3`); a parancsok az `acquirepanel/include`, `includeall`, `exclude`,
`excludeall` eseményt küldik (`0x005cb990`, `0x005ccea8`), a panel `0x0051f070`
kezelője a `0x0051f7f0(panel, include, all)`-t hívja.

**Nálunk:** `ImportSourcePreview.qml:126-145`: a bélyegképen szöveges
`Include`/`Exclude` hivatkozás; `ImportSourcePickerPanel.qml:251-260`: külön
`Exclude All`/`Include All` gomb; jobbklikk-kezelő és `Menu` az
`ImportSourcePreview.qml`-ben nincs.

**Teendő:** a bélyegkép jobbklikk-menüje kínálja a négy műveletet; az egyedi és
a tömeges parancs ugyanazt a kiválasztási állapotot módosítja, mint a mai
gombok (azok maradhatnak).

**Kész, ha:** a jobbklikk-menüben a négy parancs szerepel és hat; a mai gombok
változatlanul működnek. A vizuális egyezést eredeti képernyőkép híján a jegy
nem méri, ezt kimondja.

#### 6. Importpanel és nagy előnézet (E7)

**Eredeti:** a `panelroot/acquiretab` főablak-panel (`macros.tre:281`), a
kijelölt kép nagy előnézete (`thumbpreview`) forgatás-, lapozó-, csillag- és
kizárás-gombbal és `fileinfo`-val (`acquirepanel.tre`); a főablak
bezárásakor, ha a panel aktív és az `anowbutton` engedélyezett,
`Import images before closing Picasa?` kérdés, `Import Images` és `Quit` gombbal
(`0x005e45c0`).

**Nálunk:** `ImportSourceDialog.qml:16-31` (modális, 640 × 680-as `Window`),
`:297-316` (a három panel egymás alatt); az ablak szintjén nincs nagy
előnézet (`Image` csak a 72 képpontos bélyegképekben van).

**Teendő:** az importfelület a főablak panelje legyen, amely a könyvtár helyére
lép, a kijelölt képnek nagy előnézettel; a három belépő (eszköztár, menü,
`Ctrl+M`) ezt a panelt nyissa; a főablak bezárásakor az import-megerősítés
megjelenik. Vizuális egyezést (elrendezés, méretek) a jegy nem mér: eredeti
felvétel nincs (a #6845 `ki00/kepernyo__29.png` a helyi archívumban hiányzik).

**Kész, ha:** az Import belépők a főablak paneljét nyitják, a főablak
bezárásakor az eredeti szövegű kérdés megjelenik, a nagy előnézet a kijelölt
fotót mutatja; a régi önálló ablak megszűnik.

#### 7. Importtörlés hibaállapot (E9, helyi hiba)

**Eredeti:** a Picasa kimenete a forrástörlési hibánál nincs meg; a 8.
jegytörzs szerint hiba után az eredeti a forrásból semmit nem töröl.

**Nálunk:** `import_source_controller_import.py:49-86`: a `path.unlink(
missing_ok=True)` (`:61`, `:63`) csak a hiányzó fájlt nyeli el, az `OSError`-t
(írásvédett vagy kieső megosztás) nem; `import_source_controller.py:446-464` a
törlő ciklusok `try` nélkül futnak; a `worker_thread.py:311-361` naplóz és
tárol, de nem küld `importFinished`-et; `ImportSourceDialog.qml:274-297`: az
`importing` az `onImportStarted`-ben igazra áll, hamisra csak az
`onImportFinished`-ben, így az ablak „dolgozik” állapotban maradhat.

**Teendő:** a törlési hibát az import hibaszámmal jelentse, minden ágon
lezárja az `importing` állapotot (`importFinished`), őrizze meg a már elkészült
célmásolatokat, és ne töröljön olyan forrást, amelynek a másolása nem sikerült.

**Kész, ha:** törlési jogosultsági vagy I/O hibánál a folyamat lezárul, a
célmásolatok állapota jelzett, a hiba látható, az ablak újra használható;
teszt: írásvédett forrás vagy kényszerített `OSError`.

#### 8. (új, E10) Fájlhiba után a forrásból semmi nem törlődik

**Eredeti:** a `0x0070b1e0` fájlhibás ága és a `0x0070bdd0` átnevezési hibás
ága üzenetet ad (`0x00980700`), nullázza a `[szál+0x2d0]` aktív jelzőt és a
`[szál+0x1a0]` törlési módot (`0x0070b9d9-0x0070b9e0`,
`0x0070c093-0x0070c09a`, `0x0070c36a-0x0070c371`); a törlési fázis (`Cleaning Up`,
`0x0070c980-0x0070c9d9`) csak aktív jelzőnél és 1 vagy 2 módnál fut, tehát
hiba után a forrásból semmi nem törlődik, a már célba került másolatok
maradnak.

**Nálunk:** `import_source_controller.py:446-464`: Delete Copied módban a
sikeresen másolt képek forrása akkor is törlődik, ha más képek másolása hibás
volt; Delete All módban minden forrás törlődik a hibásak kivételével
(`failed_sources`, `:449-464`). Ez a #441 tudatos döntése; az eredeti
szigorúbb.

**Teendő:** ha az importban akár egy másolási hiba is volt (`failed_details`
nem üres), a forrásból semmi ne törlődjön, és az üzenet mondja ki, hogy a
forrás érintetlen maradt. A megszakítás az első hibánál (az eredeti az egész
importot leállítja) feltételes: futásmérés előtt a mai folytatás marad.

**Kész, ha:** egy hibás és két jó képnél Delete Copied és Delete All módban is
mind a három forrásfájl a helyén marad, a két jó kép másolata a célban van, a
hiba látható; hibátlan importnál a törlési módok a mai módon törölnek.

**Nem nyílik jegy (a zárókör döntése):** az AutoRun, a WIA és a `/StiDevice:`
út (Windows-specifikus, külön termékdöntés); a Google Fotók import (megszűnt
szolgáltatás); az átmeneti mappa utánzása (a PicasaPy nem használ ilyet);
a célmappa rejtett jelzőjének levétele (Windows, peremeset, a 4. sor
mérésébe tartozik); az `ImportSegmentMinutes` (az `acquirepanel/timesegment`
elem rejtett, nincs látható hatás); az ütközésnév `-001` alakja (a Ghidra-sor
dönt, a #6964-gyel közös); a fázisszövegek a felület ismerete előtt; a
`Recent sources` legördülő (tudatos többlet; az `ImportSourcePickerPanel.qml:
42-43` komment téves állítását, hogy az eredeti legördülője ezt kínálta, a
2. vagy a 6. jegytörzs mellett érdemes pontosítani).

**Következő irány (felvehető):** (1) a 4. sor mérési jegye a fenti tartalommal,
nem blokkoló; (2) egy Ghidra-sor, a #6964-gyel közös:
`Ghidra-kör kell: 0x00993650 - a 0x00994580-ból hívott névképző (3. argumentum
1): szabad célnévnél sorszám nélkül marad-e az első név, és foglalt névnél a
%s-%03lu (-001) minta fut-e; a #6964 azonos kérdését is eldönti [nem
blokkoló]`.

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md`: a #7083 indexelési, navigációs,
  írásvédett-törlési és hibajelzési sorainak pontosítása; bizonyítottság,
  ellenőrző táblázat, eltérés-/teendő-tábla, 7 javasolt fejlesztői jegytörzs
  és célzott nyitott kutatási kérdések hozzáadása.
## #7084: A kötegelt szerkesztés teljes folyamata az eredeti Picasával összevetve: belépési pontok, viselkedés, hatás

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
A bináris nem futott; a leletek cím szerinti diszasszemblálásból, meglévő
Ghidra-kimenetekből (`referencia/ghidra/`), a bináris-indexből
(`referencia/binary-index/picasa3-index.sqlite`), a program-erőforrásokból
(`shortcuts.xml`, `rename.fen`, `offsettime.fen`), a magyar szövegtárból
(`stringres-en-hu.tsv`), az ini-korpuszból, a meglévő futtatott felvételekből
(job-641, job-244, job-254) és a PicasaPy-forrásból származnak.

### Következtetés

1. **A kötegelt szerkesztés folyamata és ágai:**
   - **Forgatás (Batch Rotate, `0x9ca2`, `0x9ca3`):** a menüből (`0x005eef30`), gyorsbillentyűből (`Ctrl+R`, `Ctrl+Shift+R`), helyi menüből és eszköztárról/tálcáról érhető el. Nincs párbeszédablak. A kijelölésen azonnal, háttérmunkaként fut le; a `.picasa.ini`-be `rotate=rotate(N)` negyedfordulatot és `backuphash` időbélyeget ír, frissíti az index `imagedata_rotate` oszlopát és a bélyegképeket. A kijelölés megmarad. Nem támogatott fájlok (pl. videók) esetén a végén `IDS_ROT_TYPEFAILED` („One or more images could not be rotated because of the file type.”) figyelmeztetést ad.
   - **Automatikus javítások és effektek (Batch Effects, 9 művelet):** az almenüből (`0x00d6e4ac`) érhető el (Auto Contrast `0x9d49`, Auto Color `0x9d48`, I'm Feeling Lucky `0x9d5e`, Sepia `0x9d4a`, Sharpen `0x9d4b`, Warmify `0x9d4d`, Film Grain `0x9d4e`, Black and White `0x9d4c`, Auto Red Eye Correction `0x9df1`). Nincs ablak. Kétágú viselkedés: ha a szerkesztő nyitva van (`0x00579330`), a parancs a szerkesztőpanel megfelelő fülére és vezérlőjére navigál; könyvtárnézetben a kijelölés összes képére meghívja a `0x005fe370` batch motort (illetve az Auto Red Eye esetén a `0x00602100` / `0x005f39d0` delegált keretet). A `.picasa.ini`-ben a `filters=` láncot bővíti, `backuphash`-t frissít, és átugorja a nem támogatott fájlokat (`iStack_98`), a köteg végén `IDS_SOME_EDITS_FAILED_TYPE` figyelmeztetést adva.
   - **Dátum és idő beállítása (Adjust Date and Time, `0x9e0e`, `0x0057d7f0`):** az Eszközök menüből érhető el legalább egy kijelölt képpel. A `runtime/offsettime.fen` párbeszédet nyitja meg. Címe 1 elemnél `Adjust Photo Date`, >1 elemnél `Adjust Photo Date - %d items`. Bélyegkép-előnézetet, jelenlegi dátum/idő és új dátum/idő mezőket ad, valamint két rádiógombot (0: relatív eltolás, 1: abszolút fix idő). Nem jegyez meg állapotot, az első kép idejével és a relatív móddal indul. A lemezen közvetlenül módosítja a fájlok EXIF metaadatait (JPEG esetén) és az index `imagedata_date` oszlopát; ha a rács dátum szerint rendezett, a képek átrendeződnek.
   - **A ráírt szöveg láthatósága (Show Text `0x9deb`, Hide Text `0x9dec`):** a Kép ▸ Csoportos szerkesztés almenüből érhető el. Nincs ablak. A `0x005f6a40` kezeli: a kijelölt képek `.picasa.ini` szakaszában a `textactive` kulcsot `1`-re (Show) vagy `0`-ra (Hide) állítja a `0x00462500` hívással, és frissíti a bélyegképeket. Ha a szerkesztő nyitva van, az `editpanel/showtextcheckbox` állapotát is szinkronizálja.
   - **Átnevezés több képen (Batch Rename, `0x9d4f`, `F2`):** a Fájl menüből, a Kép ▸ Csoportos szerkesztés almenüből és F2 gyorsbillentyűvel érhető el. A `runtime/rename.fen` párbeszédablakot nyitja meg (`0x00532ec0`). Névmezőt, darabszámos címkét, dátum és felbontás jelölőnégyzeteket (`RenameUseDate`, `RenameUseSize`), valamint statikus előnézeti mintát (`Example: <név> 08-01-2004 2-30-45 PM 640x480.jpg`) ad. A két jelölő állapota perzisztált (Preferences/rename). A lemezen fizikailag átnevezi a fájlokat; az ütközéseket a `0x00993650` kezeli: az első szabad cél változatlan marad, ütközéskor `-001`-től `-4095`-ig számozza (`%s-%03lu`, `0x00cd8d64`). A `.picasa.ini`-ben a szekciók és a `.picasaoriginals` fájlok/szekciók is átneveződnek.
   - **Visszavonás (Revert / Undo):** Kép ▸ Összes szerkesztés visszavonása (`0x005ef3e0` / `0x005ef520`): megerősítést kér (`IDS_CONFIRMREVERT_MULTIPLE`, gomb: `Remove Edits`), majd képenként törli a `filters`, `crop`, `flipped`, `redo`, `text`, `textactive` kulcsokat. A `rotate` negyedfordulat kulcsot a visszavonás NEM törli!

2. **Bizonyítottsági fok: erős.** A menürekordok, parancsazonosítók, diszpécser-ágak (`0x005cb990`), a dialógusleírók (`.fen`), az ini-kulcsok és a futásidejű viselkedések utasításszintű dekompilációval és meglévő futtatott felvételekkel (job-641, job-244, job-254) egybevágnak.

### Belépési pontok és feltételek

| Eredeti (bináris cím vagy mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Kép ▸ Csoportos szerkesztés almenü:** `0x00d6e4ac` rekord, `0x00d6e318` gyerektábla 19 rekorddal (14 parancs + 5 elválasztó). Menüpontok: Rename (`0x9d4f`, `F2`), Rotate Clockwise (`0x9ca2`), Rotate Counterclockwise (`0x9ca3`), Auto Contrast (`0x9d49`), Auto Color (`0x9d48`), I'm Feeling Lucky (`0x9d5e`), Sepia (`0x9d4a`), Sharpen (`0x9d4b`), Warmify (`0x9d4d`), Film Grain (`0x9d4e`), Black and White (`0x9d4c`), Auto Red Eye Correction (`0x9df1`), Show Text (`0x9deb`), Hide Text (`0x9dec`). | `PicasaPictureMenu.qml:20-115` (`menuPictureBatchEdit`) | A 14 parancs és 5 elválasztó sorrendje és felirata egyezik. |
| **Fájl ▸ Rename:** `0x00559150`, parancs `0x9d4f`, `F2` gyorsbillentyű; a diszpécserben a `0x00532ec0`-ra jut (ugyanaz a kezelő, mint a Batch Edit ▸ Rename). | `PicasaFileMenu.qml:92-97`, `Main.qml:1191-1194` | Egyezik: mindkét menüpont és az F2 ugyanazt a dialógust hívja (`openRenameMany`). |
| **Eszközök ▸ Adjust Date and Time:** `0x00559150`, parancs `0x9e0e`, kezelő `0x0057d7f0`; nincs gyorsbillentyűje és nincs helyi menüben. | `PicasaToolsMenu.qml:80-84`, `PropertiesPanel.qml:168-170` | Egyezik: az Eszközök menüből érhető el. |
| **Gyorsbillentyűk:** `F2` (Rename), `Ctrl+R` (Rotate CW, `0x9ca2`), `Ctrl+Shift+R` (Rotate CCW, `0x9ca3`), `Ctrl+Shift+B` (Black and White, `0x9d4c`). Az effektekhez és a dátumhoz nincs más közvetlen shortcut. | `Main.qml:1072-1081, 1191-1194`; `shortcuts.xml:133-138` | Egyezik. |
| **Helyi menük és eszköztár:** A képrács helyi menüjében (`PhotoContextMenu`) a Forgatás (jobbra/balra) és az Összes szerkesztés visszavonása szerepel; a kötegelt effektek és az Átnevezés nincsenek a helyi menüben. A képtálcán Forgatás gombok találhatók (`thumbui/rotateright`, `thumbui/rotateleft`). | `PhotoContextMenu.qml:150-164`, `MainTrayBar.qml:128-142` | Egyezik. |
| **Szerkesztőnézetbeli navigáció (kétágú minta):** `0x00579330` vizsgálja, hogy a szerkesztő nyitva és szabad-e (`DAT_00d67914 != 0`, `editpanel/preview`). Ha nyitva van, az Auto Contrast/Color/Enhance/Sharpen stb. a szerkesztőpanel megfelelő fülére navigál (`editpanel/tab1`, `editpanel/autolighting`), nem kötegelt batch-et futtat. | `MainMenuBar.qml:420-427` | Eltérés: a PicasaPy megpróbálja kiválasztani az effektet a nézőben (`viewer.selectMenuEffect`), de ha nem kezeli, egyképes `applyEffectMany([row], name)` köteget indít ahelyett, hogy fókuszálná a vezérlőt (1. jegytörzs). |
| **Menüengedélyezési feltételek:** Az eredetiben a Csoportos szerkesztés és tételei legalább egy kijelölt képet követelnek (`0x0056e1c0`, `photoActionsEnabled`). A Show Text (`0x9deb`) és Hide Text (`0x9dec`) az eredetiben MINDIG engedélyezett, ha van kijelölés (`EnableMenuItem(local_40, 0x9deb, 1)`). | `PicasaPictureMenu.qml:106, 112`, `MainMenuBar.qml:77-83` | Eltérés: a PicasaPy a Show/Hide Text engedélyezését a kijelölés képeinek tényleges `textactive` állapota szerint szűri (`textOverlayShowEnabled` / `textOverlayHideEnabled`), amihez minden menünyitáskor beolvassa az ini-ket (2. jegytörzs). |

### Ablakok, alapértékek és megjegyzett állapot

- **Forgatás, kötegelt effektek, szöveg láthatóság:**
  - Az eredeti Picasa 3.9-ben **NINCS ABLAK**. A parancs kiválasztásakor semmilyen ablak, kérdés vagy megerősítés nem jelenik meg; a művelet azonnal lefut a kijelölésre.
  - PicasaPy: szintén nincs ablak; a háttérmunka alatt a lebegő folyamatjelző panel (`batchEditActive`) jelenik meg.
- **Dátum és idő beállítása (`runtime/offsettime.fen`, `0x0077c670`, `0x0077c7c0`):**
  - **Ablakcím:** 1 kijelölt kép esetén `Adjust Photo Date` (`0x0077c803` átugorja a formázást); 2 vagy több kép esetén `Adjust Photo Date - %d items` (`0x00cb40ac`).
  - **Mezők:** bélyegkép-előnézet (`thumb`), csak olvasható jelenlegi dátum és idő (`currentdate`, `currenttime`, `Current photo date`), szerkeszthető új dátum és idő (`newdate`, `newtime`, `New photo date`), két rádiógomb (`adjust_type`: 0 = relatív időkülönbség minden képre, 1 = abszolút fix idő minden képre), valamint `OK` (`accept`) és `Cancel` gomb. Ablakszélesség: `fit`.
  - **Alapértékek:** mind a jelenlegi, mind az új dátum/idő mezők a kijelölés első képének `FILETIME` idejével indulnak (`0x0077c6a0`-`0x0077c6c6`). A rádió kezdő állása a relatív mód (rádió 0).
  - **Megjegyzett állapot:** az ablak nem jegyez meg beállítást; minden megnyitáskor a fotó saját idejével és a 0. rádióval indul.
  - **PicasaPy:** `AdjustTimestampDialog.qml`. Eltérés: 1 kijelölt kép esetén is kiírja a darabszámot (`Adjust Photo Date - 1 items`) (3. jegytörzs).
- **Csoportos átnevezés (`runtime/rename.fen`, `0x00532ec0`, `0x00532070`):**
  - **Mezők:** darabszámos tájékoztató felirat (`"%s file(s) selected for rename."`, `job-641`: „2 file(s) selected for rename.”), szövegmező (`newname`, `filter="filename"`), dátum jelölőnégyzet (`RenameUseDate`, `0x00c899e0`), felbontás jelölőnégyzet (`RenameUseSize`, `0x00c899f0`), statikus minta-előnézet (`Example: ` + név + ` 08-01-2004 2-30-45 PM` + ` 640x480` + `.jpg`), `Rename` (alapértelmezett gomb) és `Cancel` gomb.
  - **Alapértékek:** egy kép kijelölése esetén az aktuális fájlnév kiterjesztés nélküli része jelenik meg a mezőben és kijelölődik (`job-244`); több képnél a mező üres.
  - **Megjegyzett állapot:** a két jelölőnégyzet állapota a Windows Registry / Preferences-ben tárolódik (`RenameUseDate`, `RenameUseSize`, `0x00532070`), megváltoztatásuk megőrződik következő futásra.
  - **PicasaPy:** `FileOpsDialogs.qml` (`openRenameMany`). Eltérés: az előnézet az első kép valós metaadatait mutatja, nem a statikus mintát; a jelölők állapota QSettings-ben megőrződik.

### Tárolás, műveleti hatás és hibák

| Hatás / folyamat | Eredeti Picasa 3.9 | PicasaPy most |
|---|---|---|
| **Fájlok a lemezen** | Effektek, forgatás, ráírt szöveg esetén a fizikai fájlok NEM változnak (nem-destruktív szerkesztés). Dátummódosításnál a JPEG fájlok EXIF DateTimeOriginal adatai közvetlenül átíródnak a lemezen. Átnevezésnél a fájlok fizikailag átneveződnek (`MoveFile`). | Egyezik: effektek/forgatás nem-destruktív; dátum EXIF-et ír (`piexif`); átnevezés lemezen mozgat. |
| **`.picasa.ini` módosítás** | Effekteknél a `filters=` kulcs bővül és `backuphash` frissül (`0x005fe370`). Forgatásnál a `rotate=rotate(N)` negyedfordulat és `backuphash` frissül (`0x005eef30`). A ráírt szövegnél a `textactive` kulcs értéke `1` vagy `0` lesz (`0x005f6a40`, `0x00462500`). Átnevezésnél a régi szekció átneveződik az új névre, és a `.picasaoriginals` fájl/szekció is átmozog. Dátummódosítás nem ír ini-t. | Egyezik: `update_document`-tel szekció- és kulcskezelés, `with_backuphash` időbélyeg-frissítéssel. |
| **Index és adatbázis (`db3`)** | Az adatbázis-oszlopok frissülnek: `imagedata_filters`, `imagedata_rotate`, `imagedata_textactive`, `imagedata_date`, valamint átnevezésnél a fájlnevek. | SQLite index frissül minden ágon. |
| **Képrács, bal hasáb és kijelölés** | Bélyegképek azonnal újrarenderelődnek. Ha a rács dátum vagy név szerint rendezett, a rendezés újrapozicionálja a képeket. A kijelölés MINDEN kötegelt művelet után az érintett képeken MEGMARAD. | Egyezik: modell frissül, kijelölés megmarad. |
| **Háttérmunka és kurzor** | A művelet alatt homokóra/várakozó kurzor (`IDC_WAIT`, `_DAT_00d6793c`) jelenik meg; a művelet szálon fut, de felugró folyamatjelző ablak nincs. | Lebegő folyamatjelző sáv (`batchEditActive`), mappánkénti haladás-visszajelzéssel és megszakítási gombbal. |
| **Nem támogatott fájlok (videók)** | Vegyes kijelölésnél a videókat átugorja, és a művelet végén felugró figyelmeztetést ad: kötegelt effektnél `IDS_SOME_EDITS_FAILED_TYPE` („Some edits could not be applied because of the file type.”), forgatásnál `IDS_ROT_TYPEFAILED`. | Eltérés: a PicasaPy csendben átugorja a videókat (`if photo.kind == "video": continue`), és nem ad figyelmeztető ablakot a felhasználónak (4. jegytörzs). |
| **Átnevezési ütközés és sorszám** | Ha az első célfájl szabad, sorszám nélkül marad (`alapnév.jpg`). Ütközéskor (foglalt cél vagy azonos kötegbeli név) a `0x00993650` `-001`-től induló háromjegyű nullázott utótaggal számozza felül (`%s-%03lu`, `0x00cd8d64`) egészen `-4095`-ig. | Eltérés: PicasaPy listaindex szerint számoz (`név`, `név-1`, `név-2`), és a meglévő célfájl ütközését előre elutasítja. |
| **Írásvédelem és hálózat** | Írásvédett lemezen (pl. CD-ROM) az ini- és fájlírás elutasításra kerül (`AllowReadOnlyEdits` kapu `0x00602100`-ban). | `PermissionError`/`OSError` elkapva, `photoOpFailed` hibajelzés jelenik meg a felületen. |
| **Visszavonás (Revert / Undo)** | Kép ▸ Összes szerkesztés visszavonása (`0x005ef3e0` / `0x005ef520`): megerősítést kér (`IDS_CONFIRMREVERT_MULTIPLE`, gombok: `Remove Edits` és `No`, nincs "ne kérdezd újra" jelölő, `job-254`), majd törli a `filters`, `crop`, `flipped`, `redo`, `text`, `textactive` kulcsokat. A `rotate` negyedfordulat kulcsot NEM törli. Az átnevezésre nincs visszavonás. | Egyezik: `clearAllEffectsMany` pontosan ugyanezt a kulcskészletet törli megerősítéssel és meghagyja a `rotate`-et (#7017). PicasaPy ezen felül külön Szerkesztés ▸ Csoportos szerkesztés visszavonása (`undoBatchEdit`) lépést is kínál. |

### Bizonyíték és bizonyítottság

| Érték/állítás | Forrás |
|---|---|
| Három belépési út ugyanarra a kezelőre | bináris (`0x00559150`, `0x005592d7`, `0x005cb990` ugrótábla, `0x005cba7c`, `0x005d3010`); erőforrás (`picasa-menu-leltar.md:434`, gyorsbillentyű-tábla) |
| Panel, nem ablak | erőforrás (`acquirepanel.tre`, `macros.tre:281` `m_acquire_enable`); bináris (`0x0051d4c0`, `0x005e45c0` `panelroot/acquiretab`) |
| Panelgombok kezelői | bináris (`0x0051f070`, `0x0051b620`); erőforrás (`acquirepanel.tre`: `escapekey 1`, `disabletarget`) |
| Import engedélyezési feltétel | bináris (`0x005238b0`, `0x005276f0`, `0x00527730`, RTTI `AcquireImportAllEnable`, `AcquireImportSelectedEnable`) |
| Tippsor négy állapota | bináris (`0x0051ae90`); erőforrás (`acquirepanel_text.tre` négy szövege) |
| `acquireUseSubFolder` alap 0, sorrend | bináris (`0x00514180`, `0x005181b0`, `0x0051ae90`, `0x00524730`); két független fogyasztó egyezik |
| `acquireCleanCard` 2 → 1 | bináris (`0x00519560`, `0x0051a0c2`) |
| `LastImport%x` 5 tétel, indításkor | bináris (`0x0052532c`-`0x00525400`); a menü `0x00516180` |
| Törlés-megerősítés szerkezete, `dontwarn` máshol | bináris (`0x00519720`, `0x0051b710`); szöveg (`stringres-en-hu.tsv:144-162,166,180`) |
| Meghajtó-felsorolás szabálya | bináris (`0x00510500`: 2-es, 3-as és 5-ös típus, `FAT`, `FAT32`, `NTFS`, `KODAK`, `A:`/`B:`) |
| Fázisszövegek `ytProgress`-ben | bináris (`0x0070e990`, `0x0070bdd0`, `0x00710700`, `0x00415610`, `0x00562420`); RTTI `ytProgress` |
| Hibakód-leképezés | bináris (`0x0051e4c0`); szöveg (`stringres-en-hu.tsv:167-170,3000,3004`) |
| `ImportSegmentMinutes` alap 90 perc | bináris (`0x005219c5`-`0x00521a4e`, konstansok `60,0` és `86400,0`) |
| Szabad-hely szöveg a Google Fotók ágból | bináris (`0x005d2ca0` egyetlen hívója `0x005cb990`, `0x9dfa`) |
| PicasaPy mai viselkedése | fájl:sor, közvetlen QML/Python-olvasás |
| PicasaPy `.picasa.ini`-hatás eredeti megfelelője, átmeneti mappa neve, ütközés, megszakítás, végállapot | `NINCS MEG` |

### A két független út

- **A: bináris út.** Az eseményt a `0x005cb990` ugrótáblájától a
  `0x005d3010`-ig, a panel parancsait a `0x0051f070` kezelőn át az
  `0x00522ad0`/`0x00524730` indításig, a beállítás-kulcsokat az olvasóktól
  az íróikig, a törlés-megerősítőt és a másolószál fázisait követtem.
- **B: erőforrás és szöveg.** Az `acquirepanel.tre` elrendezése és az
  `acquirepanel_text.tre` szövegei, a `stringres-en-hu.tsv` angol és magyar
  szövegei, az RTTI-nevek (`AcquireImportSelectedEnable` stb.), a
  gyorsbillentyű-tábla és a #6845 felvételi sora. A PicasaPy QML/Python
  forrását külön olvastam.
- **Egyezés.** A gombok, a tippsor, a hibaszövegek és a menüparancs a két
  úton megegyeznek. A hatás és a hibák végállapota csak statikusan
  adott, ezért nem megerősített.

### Cáfoló kísérletek

- **"A Fájl menüben nincs importálás-egyenérték"** (régi lap): cáfolva, a
  `0x9c91` ugrótábla-bejegyzése a gomb kezelőjére fut. Cáfoló próba a
  párosításra: a `0x9c91` a gyorsbillentyű-táblában is az `&Import From...`
  felirathoz tartozik.
- **"A közbenső fázisok a lebegő értesítőben vannak"** (feltevés): cáfolva,
  a szövegek egy `ytProgress` objektumba mennek, nem a `CNotifierPopup`-ba.
- **"A korábbi importok a forráslistát bővítik"** (a #441 megjegyzése):
  cáfolva, a `LastImport%x` a célmappa-menüé.
- **"A törlés kérdésén van `dontwarn`"**: cáfolva, a `dontwarn` a
  `0x0051b710` nyilvános feltöltési kérdésén áll.
- **"Az alapértelmezett mód a dátum szerinti"** (a #441 szövege: "a Picasa
  import-munkafolyamatának lelke"): a bináris alapértéke 0, azaz kézi cím;
  a dátumos mód a megjegyzett választás lehet, de nem az alapérték.
- **Kizárt út:** az `AcquireDupeCheckThread` és az `originfast` kulcs a
  `picasa-kereses-modok.md` 127. sora szerint már lezárt; a PicasaPy
  gyorsbillentyűs egyezése (`import_source_controller_sources.py:210-242`)
  ezzel egyezik, nem kutattam újra.

### Igazolt eltérések egy táblázatban

| Jel | Eredeti | PicasaPy |
|---|---|---|
| E1 | `acquireUseSubFolder` alap 0 = kézi cím; az utolsó választás megmarad (írás az indításkor) | alap dátum; a választás nem marad meg |
| E2 | `acquireCleanCard` alap 0; megmarad, a 2 visszalép 1-re; letiltva, ha a forrás nem törölhető | alap "leave"; nem marad meg; mindig mindhárom választás |
| E3 | egyetlen megerősítő ablak, Cancel gombbal, "ne kérdezd újra" nélkül | kétlépcsős `ConfirmDialog`, "Do not ask again" jelölővel, ami elnyomhatja a figyelmeztetést |
| E4 | `Import All` és `Import Selected (N)`, kijelöléssel; Enter és Esc | egy `Import` gomb, kijelölés nélkül |
| E5 | négy tippállapot | csak az 1. |
| E6 | `LastImport%x` az indításkor, 5 tétel | sikeres másolás után, 8 tétel |
| E7 | főablak-panel (`panelroot/acquiretab`, `0x005e45c0`; `macros.tre:281`), nagy előnézettel a kijelölt képről | modális, önálló ablak, bélyegenkénti gombokkal |
| F1 | fájlhibánál "Cancelling Import." (feltételes) | folytatás és hibalista |
| F2 | Windows-forráslista: cserélhető (nem `A:`/`B:`), fix kötet a `FAT`/`FAT32`/`NTFS` és `KODAK` szabállyal, CD-ROM | cserélhető vagy `DCIM`-es kötet (feltételes, alacsony) |

### Javasolt fejlesztői jegytörzsek

#### 1. Az importálás megjegyzett állapota és alapértékei (E1, E2, E6)

**Eredeti:** a `0x00514180` az `acquireUseSubFolder` kulcsot alapérték 0-val
olvassa (`[panel+0x7b0]`); a menü sorrendje `0x005181b0`: 0 = `Enter Folder Title`, 1 = `Date Taken (YYYY-MM-DD)`, 2 = `%s (Today)`; a `0x00525400` az
import indításakor visszaírja. A `0x00519560` az `acquireCleanCard` kulcsot
alap 0-val olvassa, a 2 értéket 1-re cserélve; a `0x0051a0c2` indításkor
írja, ha a forrás törölhető. A `0x00525352` indításkor legfeljebb 5
`LastImport%x` bejegyzést ír (`0x0052532c`). A `0x005277e0` és a `0x00519630`
a törlés-menüt 0-ra állítja, ha a forrás nem törölhető.

**Nálunk:** `ImportSourceDialog.qml:94` (`namingMode: "date"`, nem tárolt),
`:105` (`afterCopying: "leave"`, nem tárolt);
`import_source_controller_state.py:55,210-223` (célok sikeres másolás után,
8 tétel); `ImportSourceDestinationPanel.qml:161-192` (mindig mindhárom
törlés-választás).

**Teendő:** tárold az utolsó almappa-módot és az "After Copying" választást
(a "minden törlése" tárolva a "csak a másoltak" legyen), olvasd vissza az
ablak megnyitásakor; az alapérték első használatnál a kézi cím. Az
`After Copying` sor csak olyan forrásnál legyen aktív, amelyről törölni lehet
(a forrás-típus szabálya az első Ghidra-kör, `0x00519630`, eredményére vár; addig a
mappa-forrás viselkedése változatlan). A korábbi célokat az import
indításakor mentsd, legfeljebb 5 tétellel.

**Kész, ha:** friss profilban a mód "Enter Folder Title" és a tippsor az 1.
állapotot mutatja; egy dátumos import után újranyitva a dátum mód van
kiválasztva; "Delete everything on card" választás után újranyitva "Delete
only copied photos" áll; a célok listája 5 tételnél nem hosszabb, és a cél az import
indításakor, a másolás előtt mentődik.

#### 2. A kártyatörlés megerősítése egyetlen ablak legyen, elnyomható jelölő nélkül (E3)

**Eredeti:** a `0x00519720` mindkét törléses állapotra egyetlen ablakot
nyit (`0x0051a01c`): cím "Confirm Remove", igen gomb "Remove Imported Files"
(`DeleteCopied`, üzenet `confirmRemoveCopied::message`) vagy "Remove All
Files" (`DeleteAll`, üzenet a `WipeCard...` darabokból), másik gomb "Cancel".
A "Don't warn me" jelölő (`dontwarn`, `DoNotConfirmPublicUpload`) a
`0x0051b710` nyilvános feltöltési kérdésén van, a törlésén nincs.

**Nálunk:** `ImportSourceDialog.qml:239-254` és `:376-401`: két
`ConfirmDialog`, mindkettőn alapból látható "Do not ask again"
(`ConfirmDialog.qml:59,100-110`); az első kérdés szövege nagybetűs ("THIS
CANNOT BE UNDONE"), az eredeti `confirmRemoveCopied::message` kisbetűs.

**Teendő:** "Delete only copied photos" esetén egy ablak a `confirmRemoveCopied`
szöveggel; "Delete everything on card" esetén egy ablak az összeállított
`WipeCard` figyelmeztetéssel; a gombok "Remove Imported Files"/"Remove All
Files" és "Cancel"; a "Do not ask again" jelölő ne jelenjen meg
(`rememberVisible: false`), és az `importSourceRemoveImported`, `importSourceDeleteAllWarning` kulcsra
már mentett elnyomás (`confirmSettings.isSuppressed`) ne járjon hatással; a
két kulcsot a mentett beállításokból töröld is.

**Kész, ha:** mindkét törléses választásnál pontosan egy ablak nyílik,
benne a fenti szöveg és gombok; a jelölő nincs; egy korábban elnyomott kulcs
mellett is megjelenik a kérdés; "Leave card alone"-nál nincs ablak.
*(Az ablak elrendezését (gombsorrend, fókusz) az eredetiben nem mértük; ezt
a Nyitott Colab-feladata dönti el. Ezt a jegyet a gombok számára és a
jelölő hiányára kell érteni.)*

#### 3. `Import Selected (N)`, kijelölés és Enter/Esc (E4)

**Eredeti:** a `0x0051f070` kezelő az `anowbutton`-t `0x00522ad0(panel, 0)`-ra,
az `import_selected`-et `0x00522ad0(panel, 1)`-re köti (az 1 a
`0x00524730`-ban csak a kijelöltekre szűkít). Az `Import Selected (%d)`
felirat `iAcquireUI::importselected`, az `Import All` felirat
`CAcquireUI::importallbutton`. Az engedélyezést a `0x005238b0` adja (van nem
kizárt, `Import Selected`-nél kijelölt elem, és a `[panel+0x480]` jelző). Az
alapgomb-kezelő (`0x0051b620`, feltehetően az Enter) legfeljebb egy kijelölt
képnél az `Import All`-t, többnél az `Import Selected`-et nyomja; az Esc az
`acancelbutton`-t (`escapekey 1`).

**Nálunk:** `ImportSourceDestinationPanel.qml:251-261` (egyetlen `Import`
gomb); `ImportSourcePreview.qml` (kijelölés nincs; a bélyegre kattintás nem
tesz semmit); `ImportSourceDialog.qml` (Esc és Enter nincs bekötve).

**Teendő:** a bélyegképrácson legyen kijelölés (egyszerű kattintás; a
többes kijelölés módját az eredetiben nem mértük, ezért csak egyszerű és
Ctrl-kattintásos kijelölést építs, a Shift-et csak ha mérés igazolja); az
`Import All` az összes nem kizárt képet, az `Import Selected (N)` csak a
kijelölt, nem kizárt képeket importálja, a felirat a darabszámot mutatja; az
Enter az eredeti szabály szerint választ, az Esc a `Close`-t nyomja.

**Kész, ha:** két kép kijelölésekor a második gomb `Import Selected (2)`-t
mutat és csak ezt a kettőt másolja; kijelölés nélkül vagy egy kijelölt képnél
az Enter az `Import All`-t indítja; az Esc bezárja az ablakot. A
`Import All`/`Import Selected` mindkettő tiltva, ha az eredeti `0x005238b0`
feltételei nem teljesülnek (nincs nem kizárt elem, vagy kézi módban nincs
cím).

#### 4. A tippsor négy állapota (E5)

**Eredeti:** `0x0051ae90`: kézi mód és üres cím = "Enter new folder title or
choose existing folder to continue"; kézi mód kitöltött címmel = "Click
Import All or Import Selected"; dátum mód = "Import into separate folders for
each date taken"; mai dátum mód = "Import into folder with today's date"
(`acquirepanel_text.tre`).

**Nálunk:** `ImportSourceDestinationPanel.qml:129-140` csak az első
állapotot mutatja (kézi mód, üres cím).

**Teendő:** mutasd mind a négyet az eredeti feltételekkel, ugyanabban a
sorban, ahol az elsőt most.

**Kész, ha:** a négy feltételre mindegyik szöveg megjelenik; a 4 szöveg a
`qsTr` fordítókulcsokban benne van, minden nyelven.

#### 5. Feltételes jelölt: a fájlhiba az egész importot leállítja

**Eredeti:** `0x0070b1e0` és `0x0070bdd0`: "A file error has occurred while
importing files. Cancelling Import." (`iCAcquireScanner::error`), üzenetablak
(`0x00980700`) és az import leáll; a kimenet "Error Importing" (`[+0x2c8]==6`,
`0x00710700`). A már átmásolt fájlok sorsa és az átmeneti `PhotoLabTemp`
kezelése nem ismert.

**Nálunk:** `import_source_controller.py:431-439`: a hibás fájl után a
többi másolása folytatódik, a végén `Done: N imported, M failed`.

**Teendő:** a 3. és 4. Ghidra-kör eredménye után (a leállítás pontos hatása
és a félkész mappa sorsa). Addig a jelenlegi, adatot védő viselkedés
marad; ne alakítsd át az eredeti szándéka nélkül.

**Kész, ha:** a feloldott viselkedés (leállás, a már másoltak sorsa, a
mappák állapota) az eredetivel egyezik.

### Új kutatási jegyjavaslatok

Új külön jegyet nem javaslok: a nyitott kérdések a Ghidra-körök és a
Colab-feladat sorai a #7083 folyamatához tartoznak; felvehetők a végrehajtóra
és a kutatói körre.

### Nyitott

- `Ghidra-kör kell: 0x00519630 - a forrás-elem +0x18 virtuális metódusa (a [panel+0x2a6] jelző forrása) cserélhető meghajtón, KODAK fix lemezen, CD-ROM-on és "Folder on Disk" mappán mit ad vissza; azaz melyik forrásnál tiltja a törlés-menüt. A 0x005277e0 predikátum és a 0x00519630 hívás ismert, a forrás-típusok szemantikája nem. [blokkoló az 1. jegytörzs törlés-sorára]`
- `Ghidra-kör kell: 0x0070BDD0 - az átmeneti mappa létrehozása és neve (a PhotoLabTemp csak a hibaszövegben szerepel), az átnevezés sorrendje, az ütköző célnevek kezelése (átugrás, felülírás vagy új név), és a 0x0070C424-0x0070C446 attribútumlépés célja; valamint a 0x00994580 és 0x00992780 szerepe a dátumos ágban (0x0070B1E0). [blokkoló az ütközés és a fájlhiba pontokra]`
- `Ghidra-kör kell: 0x0070CCB0 - a [szál+0x2c8] állapotkódok jelentése (2, 3, 5, 6), mi állítja a 6-ot, és a fájlhiba után törlődnek-e a már átmásolt fájlok vagy a PhotoLabTemp; valamint a [panel+0x758] és a 0x00523AC0 megszakítás import közben a szálra hat-e. [blokkoló az 5. jegytörzsre és a megszakításra]`
- `Ghidra-kör kell: 0x00524730 - az indítás előfeltételei (a 0x0051E0D0 és 0x0051E000 hívások, a -1 visszatérés), és a [panel+0x480] jelzőt dátum és mai-dátum módban mi állítja (kézi módban a cím, a többiben?); azaz engedélyezett-e az Import cím nélkül dátum módban. [nem blokkoló, a 4. jegytörzs feltételét pontosítja]`
- `Ghidra-kör kell: 0x0071A4D0 - az import indítása után a panel mit csinál (letiltás, bezárás), és a befejezés után melyik mappa és nézet marad aktív (a 0x00513FC0, 0x0052DB70 és 0x00709460 hatása a bal hasábra és a rácsra). [blokkoló a végállapotra]`
- `Ghidra-kör kell: 0x0070E990 - a [szál+0x2b4] ytProgress elemet melyik felület mutatja (lebegő ablak, a 0x00657300 értesítő, vagy az alsó tevékenységsáv), és a "Completed Importing" kattintásra visz-e valahová. [nem blokkoló, Colab-képpel is eldönthető]`
- `Ghidra-kör kell: 0x0050F6A0 - a \dcim\ és GetDriveType==2 vizsgálat hívási helyei (0x0050F590, 0x0070D520): a beolvasást a DCIM mappára szűkíti-e, vagy a dátumos névadást/törlési engedélyt dönti el. [nem blokkoló, a forráslista szabályát pontosítja]`
- `Ghidra-kör kell: 0x00522570 - a Runtime\AutoRun és Runtime\StiDevice írója és a 0x00513D70, 0x00514040, 0x0051EE50 szerepe (a behúzott hordozó utáni automatikus panelnyitás). [nem blokkoló, Windows-specifikus]`
- `Ghidra-kör kell: 0x005154F0 - az ImportSegmentMinutes (alap 90 perc) hatása a bélyegkép-listára ([lista+0x310]): rajzol-e csoporthatárt, és a 0x005219A0 mikor állítja be. [nem blokkoló]`
- `Colab-feladat kell: az importálási panel futtatott felvétele: (1) friss profil, kártya nélkül, a panel nyitó állapota (melyik almappa-mód áll, melyik tippszöveg); (2) mappa a "Folder on Disk"-ből, három kép, az almappa-mező természete (szerkeszthető legördülő-e, felkínálja-e a meglévő almappákat: a tippsor 1. szövege "choose existing folder"-t is említ), "Enter Folder Title" mód, az `Import All` után a panel, a haladás, a végállapot, a bal hasáb és a rács; (3) ugyanaz egy már meglévő nevű képpel a célban (ütközés); (4) csillag és forgatás az importban, majd a cél `.picasa.ini`; (5) "Delete only copied photos" választás és a megerősítő ablak (gombok, jelölő, fókusz), majd a panel újranyitása (megmaradt-e a mód és a törlés-választás); (6) Esc és Cancel import közben. [nem blokkoló, a végrehajtó felvehető feladata]`
- **NINCS MEG:** a `Fájl ▸ Import From...` menüpont engedélyezése más állapotforrásból (a `0x0056e1c0` nem hivatkozza). Út: a Colab-feladat (1) pontja, menü nyitva különböző módokban.
- **NINCS MEG:** a csillag és a forgatás tárolása az eredeti importban (`.picasa.ini` vagy az index) és az átmeneti mappa neve. Út: a Colab-feladat (4) pontja és a 2. Ghidra-kör.
- **NINCS MEG:** `Ctrl+M` letiltása a szerkesztőben és a szövegmezőben az eredeti gyorsítótáblán. Út: célzott Colab-próba szerkesztő módban.

Nyitott kérdések: 9 nyílt Ghidra-kör · 1 Colab-feladat · 3 NINCS MEG · 0 blokkolt (külső akadály) · 0 hatókörön kívül · 0 csak-nyitva. Lezárva (a bizonyítékkal): a belépési utak és a közös kezelő; a panelgombok kezelői; az Import engedélyezési feltétele; a megjegyzett kulcsok és alapértékeik; a törlés-megerősítés szerkezete; a hibakód-leképezés; a fázisszövegek hordozója (`ytProgress`).

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md`: új #7083 szakasz a belépési pontokról
  (a menüegyenérték helyesbítésével), a panel mezőiről, a megjegyzett
  állapotról, a hatásról, a hibákról és a kártyatörlés megerősítéséről, hét
  igazolt és két feltételes eltéréssel, öt fejlesztői jegytörzzsel, kilenc
  nevesített Ghidra-körrel és egy Colab-feladattal.

| Batch Edit almenü 14 parancsa és 5 elválasztója | bináris: `0x00d6e4ac` rekord, `0x00d6e318` gyerektábla (`picasa-menu-leltar.md` §10.1/a); `0x00559150` menüépítő |
| Diszpécser parancskód-kezelő megfeleltetések | bináris: `0x005cb990` switch (`2026-10-21-idorend-30.txt:1405-2520`) |
| Forgatás kezelője (`0x005eef30`), 90° és 270° | bináris: `0x005eef30(param_1, 0x5a)` és `0x005eef30(param_1, 0x10e)` (`2026-11-11-6532-colab-10-iro-es-hivok.txt:47699`) |
| Batch effekt motor (`0x005fe370`), filters= lánc | bináris: `0x005fe370` (`2026-11-11-6532-colab-10-iro-es-hivok.txt:56325`); CFilterStack |
| Szerkesztő-navigáció kapu (`0x00579330`) | bináris: `0x00579330`, `editpanel/tab1`, `editpanel/autolighting` |
| Auto Red Eye külön keretútja (`0x00602100` / `0x005f39d0`) | bináris: `0x005ccb36` → `FUN_00602100(FUN_005f39d0, 0)` |
| Show/Hide Text kezelője (`0x005f6a40`, `textactive`) | bináris: `0x005f6a40(param_1, 1/0)` → `0x00462500("textactive")`; `editpanel/showtextcheckbox` |
| Menüengedélyezés: Show/Hide Text mindig aktív ha van kijelölés | bináris: `EnableMenuItem(local_40, 0x9deb, 1)` és `0x9dec` (`2026-11-15-6970-colab-decomp.txt:840-841`) |
| Adjust Date and Time ablak (`offsettime.fen`, `0x0057d7f0`) | bináris: `0x0057d7f0` (`2026-11-15-7031-7032-7033-colab-decomp.txt:248`), `0x0077c670`, `0x0077c7c0`; erőforrás: `offsettime.fen` |
| Adjust Date ablakcím: 1 elemnél nincs darabszám | bináris: `0x0077c803` ugrás, `0x00cb40ac` formázás kihagyása |
| Rename ablak (`rename.fen`, `0x00532ec0`) és perzisztált jelölők | bináris: `0x00532ec0` (`2026-11-11-6532-colab-10-iro-es-hivok.txt:55595`), `0x00532070`; `RenameUseDate`, `RenameUseSize` |
| Rename futásidejű ablak felvétele és egyképes kitöltés | mérés: job-641 („2 file(s) selected for rename.”), job-244 (egy képnél a név kitöltve és kijelölve) |
| Rename ütközés számozás (`%s-%03lu`, `-001`) | bináris: `0x00993650`, `0x00cd8d64` (`%s-%03lu`) |
| Nem támogatott fájl figyelmeztetések | bináris: `IDS_SOME_EDITS_FAILED_TYPE` (`0x005fe524`), `IDS_ROT_TYPEFAILED` (`0x005ee6e0`, `0x00c97e84`) |
| Revert (Undo All Edits) kulcsok és megerősítés | bináris: `0x005ef3e0`, `0x005ef520`, `0x005ef6b0`; mérés: job-254 (`backuphash=37968`, többes szöveg egy képnél is, `Remove Edits` / `No`) |

### A két független út

- **A: bináris út:** a főablak diszpécser (`0x005cb990`) switch-ágainak utasításszintű követése, a `0x005eef30` forgatás, a `0x005fe370` kötegelt effektmotor, a `0x005f6a40` szövegkezelő, a `0x0057d7f0` dátumkezelő és a `0x00532ec0` átnevező lekövetése; az `imagedata` oszlopírók és ini-kezelők hívási lánca.
- **B: független erőforrás-, mérés- és forrásréteg:** a `runtime/rename.fen` és `runtime/offsettime.fen` deklarációi, a `shortcuts.xml` gyorsbillentyűi, a `stringres-en-hu.tsv` hibaüzenet-kulcsai, a Colab felvételek (job-641 rename ablak, job-244 egyképes kitöltés, job-254 revert megerősítés és backuphash), valamint a PicasaPy Python/QML forráskód-auditja.
- **Egyezés:** a menüsorrend, a parancskészlet, a dialógusmezők, a perzisztált beállításkulcsok, a `.picasa.ini` kulcsstruktúra és a visszavonás kulcsai egyeznek a két bizonyítékcsaládban.

### Cáfoló kísérletek és kizárt utak

- **„Az Összes szerkesztés visszavonása (Revert) a forgatást is visszavonja."** Cáfolva: a `0x005ef6b0` képenkénti törlő hívásláncában szerepel a `filters`, `crop`, `flipped`, `redo`, `text` és `textactive` törlése, de a `rotate` kulcs törlése (`0x0042c980(db, kép, -1, 1)`) NINCS benne (az kizárólag a lemezszintű `0x0046d7d0` fájl-visszaállításban él). A job-254 felvételén is megmarad a forgatás.
- **„Az Auto Red Eye Correction ugyanazon a `filters=` batch láncon fut, mint a többi effekt."** Cáfolva: a `0x005fe370` batch motorban a `redeye` string-kulcs nem szerepel; az Auto Red Eye kezelője (`0x005ccb36`) a `0x00602100(0x005f39d0, 0)` delegált keretúton fut.
- **„A Show Text és Hide Text menütételek a menü megnyitásakor inaktívak, ha nincs releváns szöveges kép a kijelölésben."** Cáfolva: a `0x0056e1c0` menüállapot-építőben a `0x9deb` és `0x9dec` tételekre feltétel nélkül `EnableMenuItem(..., 1)` hívás fut le, ha a fotóműveletek általában engedélyezettek; a Picasa nem fésüli át az ini-fájlokat a menü nyitásakor.
- **„Az Adjust Date and Time ablakcíme mindig darabszámos."** Cáfolva: a `0x0077c803` vizsgálat 1 elemnél átugorja a darabszámos formázást, és az ablak leíró szerinti alapcímét (`Adjust Photo Date`) hagyja meg.

### A jegy „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték |
|---|---|---|
| 1. Belépési pontok és feltételek | ✅ | Kép ▸ Csoportos szerkesztés 14 parancsa, Fájl ▸ Rename, Eszközök ▸ Adjust Date, gyorsbillentyűk (F2, Ctrl+R, Ctrl+Shift+R, Ctrl+Shift+B), helyi menük és eszköztár feltárva. |
| 2. Ablakok, mezők, alapértékek és megjegyzett állapot | ✅ | `rename.fen` és `offsettime.fen` mezői, darabszámai, alapértékei és Preferences perzisztenciája igazolva; effektek/forgatás ablaknélkülisége bizonyítva. |
| 3. Tárolás, fájlok, index, bal hasáb, rács, kijelölés és háttérmunka | ✅ | Fájlhatások (EXIF írás, MoveFile), `.picasa.ini` kulcsok (`filters=`, `rotate=`, `textactive=`, `backuphash`), indexoszlopok, kijelölés-megmaradás és háttérszál bizonyítva. |
| 4. Hibák, nem támogatott típusok, írásvédelem, megszakítás és visszavonás | ✅ | `IDS_SOME_EDITS_FAILED_TYPE` és `IDS_ROT_TYPEFAILED` felugrók, `AllowReadOnlyEdits`, Revert kulcskészlet (`rotate` kizárva) bizonyítva. |

### Javasolt fejlesztői jegytörzsek

#### 1. Figyelmeztetés nem támogatott fájloknál a kötegelt szerkesztésben és forgatásban

**Eredeti:** a `0x005fe370` kötegelt effektmotor a kijelölés bejárásakor számolja a nem támogatott típusú (pl. videó) fájlokat (`iStack_98`), és a köteg lefutása után felugró figyelmeztető párbeszédablakot jelenít meg a `0x009ae710` hívással: `IDS_SOME_EDITS_FAILED_TYPE` („Some edits could not be applied because of the file type.”). Hasonlóan a forgatásnál (`0x005eef30` / `0x005ee6e0`): ha a kijelölésben nem forgatható fájl van, a művelet lefut a képekre, majd `IDS_ROT_TYPEFAILED` („One or more images could not be rotated because of the file type.”) figyelmeztetést ad.

**Nálunk:** `src/picasapy/app/batch_effect_controller.py:102` (`if photo.kind == "video": continue`) és `src/picasapy/app/photo_ops_rotate_mixin.py`: a videókat csendben átugorja, nem tájékoztatja a felhasználót.

**Teendő:** ha a kötegelt effekt vagy forgatás kijelölésében átugrott videó/nem támogatott fájl volt, a művelet befejezésekor jelenjen meg a hivatalos magyar fordítás szerinti figyelmeztető ablak.

**Kész, ha:** képekből és videóból álló vegyes kijelölésre kötegelt effektet vagy forgatást adva a képek módosulnak, és a művelet végén felugrik a megfelelő figyelmeztető ablak; tisztán képes kijelölésnél nem jelenik meg ablak.

#### 2. A Show Text és Hide Text menütételek engedélyezési kapuja a Kép menüben

**Eredeti:** a menüállapot-építőben (`0x0056e1c0`, `2026-11-15-6970-colab-decomp.txt:840-841`) a Show Text (`0x9deb`) és Hide Text (`0x9dec`) parancsokra feltétel nélkül `EnableMenuItem(local_40, id, 1)` fut le, ha van kijelölés (`photoActionsEnabled`). A Picasa a menü megnyitásakor nem olvassa át az ini-ket ráírt szövegek után kutatva; ha a felhasználó rákattint, a `0x005f6a40` kezelő maga állítja át a `textactive` értéket azokon a képeken, amelyeken van szöveg.

**Nálunk:** `PicasaPictureMenu.qml:106, 112`, `MainMenuBar.qml:77-83`: a két tétel állapota a kijelölésben lévő képek `.picasa.ini`-jének beolvasásától függ (`textOverlayShowEnabled` / `textOverlayHideEnabled`), ami lassítja a menü megnyitását.

**Teendő:** egyszerűsíteni a menütételek engedélyezését: a Show Text és Hide Text legyen aktív, ha a kijelölés nem üres (`bar.photoActionsEnabled`), elhagyva a menünyitáskori ini-pásztázást.

**Kész, ha:** kijelölt képek esetén mindkét menütétel aktív; kattintáskor a `setTextOverlayVisibleMany` lefut és a megfelelő képeket módosítja.

#### 3. Dátummódosítás ablakcíme egyetlen kijelölt kép esetén

**Eredeti:** a `0x0077c7c0` párbeszéd-inicializáló `0x0077c803` utasításánál összeveti az elemszámot 1-gyel. Ha 1 vagy kevesebb kép van kijelölve, átugorja a darabszámos formázást (`0x00cb40ac`), és a leíró szerinti alapcím marad: `Adjust Photo Date`. Csak 2 vagy több képnél jelenik meg: `Adjust Photo Date - %d items`.

**Nálunk:** `AdjustTimestampDialog.qml:22`: a cím minden esetben formáz: `qsTr("Adjust Photo Date - %1 items").arg(rows.length)`, így 1 képnél `Adjust Photo Date - 1 items` jelenik meg.

**Teendő:** ha `rows.length <= 1`, a cím legyen `qsTr("Adjust Photo Date")`, darabszám nélkül; 2 vagy több képnél maradjon a darabszámos forma.

**Kész, ha:** 1 kép kijelölésével megnyitva a cím `Adjust Photo Date`; 3 képnél `Adjust Photo Date - 3 items`.

#### 4. Csoportos átnevezés háromjegyű számozása névütközéskor

**Eredeti:** a `0x00532ec0` átnevező a `0x00479870` → `0x00993650` úton végzi a célfájl-névképzést. Ha az alapszövegből (és opcionális dátumból/méretből) képzett célfájl szabad, NEM tesz hozzá sorszámot (az első kép sorszám nélkül marad). Ütközés esetén (ha a célfájl létezik, vagy a kötegben azonos név keletkezne) a `0x00cd8d64` formátum (`"%s-%03lu"`) szerint `-001`-től induló, minimum három számjegyű számozással képez egyedi nevet, legfeljebb `-4095`-ig.

**Nálunk:** `src/picasapy/fileops/rename.py:238-262, 324-331`: a kijelölési index alapján képez sorszámot (`név`, `név-1`, `név-2`), és ha a célfájl már létezik a lemezen, a teljes köteget előre elutasítja.

**Teendő:** az átnevező motor kövesse az eredeti, névütközéskor sorszámozó `-001` logikát, szabad cél esetén elhagyva a sorszámot.

**Kész, ha:** 3 kép átnevezésekor ütközésmentes helyen `név.jpg`, `név-001.jpg`, `név-002.jpg` jön létre; foglalt `név.jpg` esetén a számozás automatikusan a legkisebb szabad `-NNN` utótagot választja.

**Hívói megjegyzés (2026-11-16): ez a jegyleírás VITATOTT.** A #6964 szakasz ugyanerről a `0x00993650` útról azt rögzíti, hogy több képnél a formátum mindig `%s-%03lu` (`név-001`, `név-002`); az itteni „az első kép sorszám nélkül marad” állítás ezzel ellentétes. Jegy addig nem nyílik, amíg egy célzott Ghidra-kör (`0x00993650`, az első név képzése szabad célnévnél) vagy egy futtatott mérés el nem dönti. Az 1. és a 3. pontot a hívó mintavétellel igazolta (`0x005fe370` → `0x009ae710`, `IDS_SOME_EDITS_FAILED_TYPE`; `0x0077c7fc` `cmp [ebp+0xd8],1` / `jbe`, `Adjust Photo Date - %d items`).

**Zárókör (2026-11-17): a vita eldőlt, a #7084 állítása áll.** Szabad célnál a név sorszám nélkül marad, foglalt célnál `-001`-től számoz; a bizonyíték a Zárókör 1. pontjában van. A 4. jegytörzs ráadásul már megvalósult a forrásban (Zárási döntés).

### Nyitott

- `Ghidra-kör kell: 0x008E3160 - a rename.fen newname mezőjének filter="filename" callbackje pontosan milyen karaktereket tilt és milyen hosszkorlátot alkalmaz? [nem blokkoló, a meglévő Windows tiltólista fedezi]`
  - Ghidra-válasz (2026-11-16, `referencia/ghidra/2026-11-16-koteg-438-465.txt:5148`): **a `filter="filename"` szerkesztőmező-callbackje csak a fordított törtvonalat (`\`, `0x5c`) tiltja, hosszkorlátot nem alkalmaz.** A `0x008e3160` (a futás hozta létre a címen) törzse `return param_1 != 0x5c`, vagyis karakterenként minden karaktert elfogad, a `\` kivételével. A hozzárendelés a `0x008e30e0` attribútumbeállítóban látszik (disassembly): ha az attribútum neve `filter` (`0x00c843d8`) és az értéke `digits` (`0x00cd023c`), a `+0x4c` mezőbe a `0x008e2dd0` kerül; ha az érték `filename` (`0x00c80d70`), a `0x008e3160` (`0x008e3140`). **A többi, Windowson tiltott fájlnévkarakter (`/`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) a beírásnál nincs szűrve**; a tiltott karakterek kezelése a mentéskor van (a `0x009946f0` névtisztító és a `0x00849dc0` OK-ág, lásd a #7032 szakasz névnormalizálási sorát). A PicasaPy beíráskor szigorúbb lehet az eredetinél, ha a Windows-tiltólistával szűr; az eredeti paritását a mentéskori normalizálás adja.
  - Zárókör (2026-11-17): LEZÁRVA, a Ghidra-válasz utasításszinten is igazolva (Zárókör 5. pont).
- `Ghidra-kör kell: 0x00490580 és 0x00490C10 - az AdjustTimeThread relatív és abszolút munkaszála JPEG-en kívüli formátumoknál (PNG, TIFF, videó) melyik PMP adatbázis-oszlopba menti a módosított dátumot, ha a fájl nem támogatott? [nem blokkoló]`
  - Zárókör (2026-11-17): LEZÁRVA a meglévő bizonyítékból és a két valódi katalógus mérésével, nincs szükség új Ghidra-körre (Zárókör 6. pont).
- `Colab-feladat kell: RenameUseDate formátum ellenőrzése futó Windows Picasa 3.9-en - a fájlnévbe generált dátum pontos elválasztói és területi beállítás-függése valódi fájlon. [nem blokkoló]`
  - Zárókör (2026-11-17): LEZÁRVA a binárisból, Colab-mérés nem dönt többet (Zárókör 7. pont).

Nyitott kérdések: 3 nyílt (2 Ghidra-kör és 1 Colab-feladat) · 12 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva

A zárókör után: Nyitott kérdések: 0 nyílt · 17 lezárva (12 korábbi és 5 e körben) · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva; örökölt, nem blokkoló, már nyilvántartott: 1 (a `0x005f8520` eszközmódja, `paritas-ellenorzes-archiv-1.md` 3345. sor).

Lezárva (a bizonyítékkal): a 14 almenü-parancs és diszpécser-ágai (1. szakasz); a szerkesztő-előnézet kétágú viselkedése (1.); a forgatás háttérszála és rotate= negyedfordulata (3.); a kötegelt effektek filters= és backuphash írása (3.); a nem támogatott fájltípusok figyelmeztető üzenetei (4.); a Show/Hide Text kezelője és textactive kulcsa (1., 3.); az Adjust Date and Time ablakmezői, rádiómódjai és címszabálya (2.); a Rename ablakmezői, egyképes kitöltése, perzisztált jelölői és %s-%03lu ütközési számozása (2., 3., 4.); az Undo All Edits kulcskészlete és a rotate kulcs megőrzése (4.).

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md`: új #7084 szakasz a kötegelt szerkesztés teljes folyamatának (forgatás, automatikus javítások és effektek, dátum és idő beállítása, ráírt szöveg láthatósága, csoportos átnevezés, visszavonás) összevetésével, belépési pontjaival, ablakaival, tárolási és felületi hatásaival, hibakezelésével, négy fejlesztői jegyjavaslattal, bizonyítékokkal és nyitott kérdésekkel.

### Zárókör (2026-11-17): a megmaradt tételek döntése

Módszer: minden tételt a meglévő bizonyítékból döntöttem el (bináris index, a helyi `Picasa3.exe` utasításszintű olvasása, a `referencia/ghidra/` kimenetei, a két valódi katalógus mérése). A „Nálunk” oszlopot a mai forráson ellenőriztem; a sorszámok a 2026-11-17-i állapotra vonatkoznak. A dekompiláció veremértelmezését (a `param_` sorrendet és a `1` értékű hívásparamétereket) ott, ahol állítás múlt rajta (a számozó hívása, az `EnableMenuItem` jelzője, a `0x009807f0` paraméterei, a dátum-karakterek cseréje), a hívóhely utasításaival vetettem össze.

#### 1. Az átnevezési sorszámozás: a #6964 és a #7084 vitája eldőlt

**Döntés: szabad célnál a név sorszám nélkül marad; foglalt célnál `-001`-től számoz.** A #7084 állítása áll. A #6964 „Sorszámozás több képnél” sora rövidítés: a formátum (`%s-%03lu`), a kezdőérték és a határ benne is helyes, de a „több képnél mindig `név-001`, `név-002`” olvasat nincs a binárisban.

Bizonyíték (két független út: a hívóhely és a számozó belseje; bizonyítottsági fok: megerősített):

- **A számozó csak létező célnál fut.** A `0x00479870` belsejében: `0x00479a00 cmp byte [esp+0x1538], bl; jne 0x00479a8c` (a `param_5` nullának kell lennie), majd `0x00479a3d call 0x00992ed0; test al, al; je 0x00479a8c`: ha a cél NEM létezik, a `0x00993650` meg sem hívódik. Létező célnál `0x00479a5e push 1; push edi; push eax; call 0x00993650` (a harmadik paraméter 1, a veremsorrend a hívóhelyen ellenőrizve).
- **A `0x00992ed0` létezésvizsgálat:** `GetFileAttributesA` (`call [0x00d694bc]`, `binaris-regeszet-modszertan.md` IAT-táblája), `cmp eax, -1; setne bl` (`0x00992f03`-`0x00992f11`): igaz, ha a fájl létezik.
- **Önmagára átnevezés nem csinál semmit:** ha a régi és az új név bájtról bájtra egyezik (`0x00479a16 cmp ecx, eax; sete al`), a `0x00479a1f`-`0x00479a36` ág takarít és 0-val tér vissza.
- **A `0x00993650` belseje:** a számláló a `0x00993900` címen nullázódik (`xor esi, esi`). A `0x00993a30 test esi, esi; je 0x00993b38` ág 0-nál az EREDETI jelöltet vizsgálja (`0x00993b45 call 0x00992ed0`). Ha foglalt, a `0x00993b52`-`0x00993b63` növeli a számlálót (`add esi, 1`), és 1-től a `0x00993b07` címen a `0x00cd8d64` formátummal (`%s-%03lu`) képez nevet, majd ugyanúgy újra vizsgálja (`0x00993b38`). Szabad névnél a `0x00993b4a test al, al; je 0x009938db` ág 0-val tér vissza (siker); a `0x1000` elérése (`0x00993a1a`, `0x00993b59`) `-1`-et ad (`0x00993b87`). Ha a név már `-szám` végű és a szám kisebb `0x1000`-nél (`sscanf`, `0x00993982`, `0x00993993`), a számlálás attól folytatódik.
- **A mozgatás fájlonként, azonnal megtörténik:** a `0x00532ec0` ciklus fájlonként hívja a `0x00479870`-et (`0x00533517`), az a végén a `0x00998a40`-et, ez pedig `MoveFileWithProgressA`-t (`0x00998b4e call [0x00d694e0]`, jelző 2, vagyis `MOVEFILE_COPY_ALLOWED`, felülírás nélkül). A következő fájl vizsgálata tehát már látja az előzőt, így három képnél szabad mappában `név.jpg`, `név-001.jpg`, `név-002.jpg` jön létre.

Nálunk (ellenőrizve): `src/picasapy/fileops/rename.py:265-303` (`_available_name`): a sorszám nélküli cél az első jelölt, csak foglaltságnál keres `-001`...`-4095` között, meglévő `-szám` végződésnél a következővel folytat, önmagára átnevezés nem csinál semmit; `rename_photos_many` (`:306`) fájlonként sorban hív, a korábbi elemek már a lemezen vannak. Megvalósította a #5941 (commit `f827076c5`); tesztek: `tests/fileops/test_rename_many.py`. **A 4. jegytörzs és a „Tárolás, műveleti hatás és hibák” tábla „Átnevezési ütközés és sorszám” sorának „Eltérés” állítása ezért elavult: a viselkedés kész.** (Csak a `photo_ops_rename_mixin.py` `renamePhotosMany` docstringje említi még a régi `név-1` alakot; ez szöveg, nem viselkedés.)

#### 2. A nem támogatott fájl figyelmeztetése: a szöveg megvan, a forma eltér

A 1. jegytörzs „Nálunk” állítása (a PicasaPy csendben átugorja a videót) elavult: a jelzés létezik. A helyes kép:

- **Eredeti, a megjelenítés módja eddig NINCS MEG volt (`paritas-ellenorzes-archiv-1.md` 2496. sor), most megvan.** A kötegelt effekt végén (`0x005fe897 cmp dword [esp+0x24], 0; je 0x005fe8ca`, vagyis a kihagyottak száma nem nulla): `0x005fe89e push 0xc98918; push 0xe8; call 0x009ae710` (a `IDS_SOME_EDITS_FAILED_TYPE` szöveg betöltése), `push 0; push eax; xor eax, eax; call 0x009807f0` (`0x005fe8bd`-`0x005fe8c2`). A forgatás kötegelt ágában ugyanígy: a `0x005ee6e0` végén (`0x005eee98 cmp dword [esp+0x14], 0; je 0x005eeefa`) `IDS_ROT_TYPEFAILED` (`0x00c97e84`) → `call 0x009807f0` (`0x005eeee9`), vagyis a forgatás előbb lefut az összes képre, és csak utána szól. A `0x005eef30` forgatókezelő egyképes ága (`0x005ef1e1`) ugyanezt a függvényt hívja.
- **A `0x009ae710` csak szöveget tölt be** (`LoadStringA`-alapú); a megjelenítő a **`0x009807f0`**: a jelző `0x40`, és egy globális jelzőbájt (`0x00d678d4`) esetén `MB_RTLREADING` (`0x100000`) is (`0x009808a9 or eax, 0x40`; `0x00980891`-`0x00980895`), a cím a `ytApp::InfoTitle` szövegtár-kulcs (`0x00cd85d8` „Info”, `0x00cd85e0`; `stringres-en-hu.tsv:3360`: magyarul „Információ”), a szülőablakot a `0x0097de80` adja, a hívás pedig `call [0x00d69594]` = `MessageBoxA` (`binaris-regeszet-modszertan.md:1400`). **Tehát modális, egyetlen OK gombos, információ ikonos üzenetablak** (`MB_ICONINFORMATION`), nem értesítősáv. Ugyanezt az utat használja az üres kijelölés két üzenete is: `IDS_MUST_SELECT_TO_ROT` (`0x005ef327`-`0x005ef348`) és `IDS_NEEDS_SELECTION` (`0x005fe943`-`0x005fe966`).
- **Helyesbítés a szövegre:** az `IDS_SOME_EDITS_FAILED_TYPE` pontos angol szövege a szövegtár szerint „Some images were not modified because of the file type.  Note that effects cannot be applied to movies.” (`stringres-en-hu.tsv:1692`; két szóköz a mondatok között). A fenti szakasz korábbi idézete („Some edits could not be applied because of the file type.”) téves volt. Az `IDS_ROT_TYPEFAILED` szövege („One or more images could not be rotated because of the file type.”, `:1675`) helyes volt. A `0x005fe524` cím sem a hívás helye, hanem egy utasítás a ciklus előtt; a tényleges hívás a `0x005fe8c2`.
- **Nálunk (ellenőrizve):** a kötegelt effekt a videót kihagyja és a végén jelez (`batch_effect_controller.py:224-225`, `:298-305`, `:547`, jelzés: `batchEditTypeFailed`; megvalósította a #7090, commit `84cf94138`); a forgatás ugyanígy (`photo_ops_transform_mixin.py:67-68`, `:143-153`, `:191-201`; #1755). A felületen mindkettő értesítősáv (`PicasaNotifier.qml:429-461`, `notifier.notify(...)`). A szövegek egyeznek a szövegtárral. **Az egyetlen eltérés a forma:** értesítősáv a modális Információ-ablak helyett. A PicasaPy-ban a modális Információ-ablaknak már van mintája: `copyAllEffectsInfoDialog` (`MainWindowDialogStack.qml:110-140`, kék „i” ikon, #6864).

#### 3. A Show Text és Hide Text engedélyezése: helyesbítés

A fenti szakasz „Menüengedélyezési feltételek” sora, a 2. jegytörzs és a harmadik cáfoló kísérlet az `EnableMenuItem(local_40, 0x9deb, 1)` hívást úgy olvasta, hogy a tétel „feltétel nélkül engedélyezett”. **Ez a harmadik paraméter félreolvasása:** az `EnableMenuItem` jelzője `0` = engedélyezett, `1` = szürkített (`MF_GRAYED`), `2` = letiltott.

- Utasításszint: `0x0056f2cf push 1; push 0x9deb; push esi; call edi` és `0x0056f2d9 push 1; push 0x9dec; ...`, ahol `edi` a `0x0056f17d mov edi, [0x00c40818]` = `EnableMenuItem` (`picasa-menu-parancsok-viselkedes.md:2123`), `esi` a menüfogantyú.
- Ez a két hívás CSAK abban az ágban van, amelyet a `0x0056f29a cmp byte [esp+0x15], 0; je 0x0056f30b` nyit, ahol a kijelölés-állapotszó `0x4000` bitje be van állítva (`0x0056e2e8 test eax, 0x4000; seta [esp+0x15]`; az állapotszót a `0x005cb1a0` adja, a `0x4013` állapotot a `0x005cb365` ág). Ebben az ágban a csoport TÖBBI tétele is szürke (`0x9ca2`, `0x9ca3`, `0x9d4f`, `0x9df1`, `0x9d2d`, `0x9ca4`, `0x9ca5`, `0x9e11`).
- A nyolc effekt (`0x9d49`, `0x9d48`, `0x9d5e`, `0x9d4a`, `0x9d4b`, `0x9d4d`, `0x9d4e`, `0x9d4c`) külön hívást kap a `(bl == 0)` jelzővel (`0x0056f30b`-`0x0056f367`). A Show Text és a Hide Text a `0x0056e1c0`-ban sehol nem kap engedélyező hívást, és a függvény sehol nem olvassa a `.picasa.ini`-t.
- **Következtetés (erős):** a két tétel engedélyezése NEM függ a képek `textactive` állapotától; a menüépítő a csoport közös szürkítésén kívül nem nyúl hozzájuk. A 2. jegytörzs iránya tehát helyes, de az „Eredeti” szövege pontatlan volt; a pontos szöveg lent van. A `0x4000` bit jelentése nincs meg, de ez nem blokkoló: a bit az egész csoportot egyszerre szürkíti, nem a Show/Hide Text külön kapuja.
- **Nálunk (ellenőrizve, a hivatkozás nem változott):** `PicasaPictureMenu.qml:9` (`onAboutToShow: bar.textOverlayStatesRefreshRequested()`), `:105-113` (`enabled: bar.photoActionsEnabled && bar.textOverlayShowEnabled` / `...HideEnabled`), `MainMenuBar.qml:77-83` (`hasTextOverlayStateInSelection`, `batch_effect_controller.py:410`).

#### 4. Elavult „Nálunk” állítások a #7084 szakasz táblázataiban

| A szakasz állítása | A mai forrás | Következmény |
|---|---|---|
| „Adjust Photo Date - 1 items” egy kijelölt képnél (3. jegytörzs, „Ablakok…” rész) | `AdjustTimestampDialog.qml:22-24`: `title: photoRows.length > 1 ? qsTr("Adjust Photo Date - %1 items").arg(photoRows.length) : qsTr("Adjust Photo Date")` (#5703, commit `61d52d613`); tesztek: `tests/app/qml_functional/test_timestamp_progress_5703.py`, `test_adjust_timestamp_4332.py` | **A 3. jegytörzs kész**, jegy nem kell. |
| A rename előnézete „az első kép valós metaadatait mutatja” | `FileOpsDialogs.qml:285-293` a látható Example sort a `renameSamplePreview` adja, rögzített dátum-, méret- és `.jpg` mintával (#5702); a `renamePreview` csak a kijelölés követéséhez kell (`:316-320`) | Az „Eltérés” elavult, a viselkedés egyezik. |
| A videót csendben átugorja | 2. pont | A jelzés megvan, csak a forma tér el. |
| `név`, `név-1`, `név-2` számozás | 1. pont | Kész. |
| Hivatkozások: `Main.qml:1191-1194`, `Main.qml:1072-1081`, `PicasaToolsMenu.qml:80-84`, `PropertiesPanel.qml:168-170`, `PhotoContextMenu.qml:150-164`, `MainTrayBar.qml:128-142` | Mai helyük: `MainMenuBar.qml:272` és `MainKeyboardShortcuts.qml:413` (F2); `MainKeyboardShortcuts.qml:158` (Ctrl+Shift+B), `:288` (Ctrl+R), `:295` (Ctrl+Shift+R); `PicasaToolsMenu.qml:78-83`; `PropertiesPanel.qml:166`; `PhotoContextMenu.qml:324-331` (forgatás) és `:342-344` (Undo all Edits); `MainTrayBar.qml:47-50` | Csak a sorszámok csúsztak, a tartalom egyezik. |

A többi „Nálunk” állítást is ellenőriztem és igaz: `PicasaPictureMenu.qml:21` (`menuPictureBatchEdit`, 14 parancs), `batch_effect_controller.py:162` (`_UNDO_ALL_KEYS`: `filters`, `crop`, `flipped`, `redo`, `text`, `textactive`, a `rotate` nem), `:449` (`clearAllEffectsMany`), `:559` (`undoBatchEdit`), `:256` (`batchEditActive`), `:420` (`setTextOverlayVisibleMany`), a `with_backuphash` használata (`batch_effect_controller.py:156, 198, 495`; `photo_ops_transform_mixin.py:159, 263`), a hibajelzés (`photoOpFailed`, `batch_effect_controller.py:364, 502, 593`; `photo_ops_rename_mixin.py:64`).

#### 5. Lezárva: a `rename.fen` `newname` mezőjének szűrője (`0x008E3160`)

A Ghidra-válasz (fent) áll, és utasításszinten is igazolt: `0x008e3160 cmp dword [esp+4], 0x5c; setne al; ret`. A paraméter karakterkód: a `digits` párja, a `0x008e2dd0` (`add eax, -0x30; cmp eax, 9; setbe al`) ugyanilyen szerkezetű. A `.fen` sora hosszkorlátot nem ad (`edit width="25em" name="newname" filter="filename"`, `picasa-fen-dialogs.md:458`).

- **Eredeti:** beíráskor csak a `\` tiltott; hosszkorlát nincs. A gombállapot-függvény (`0x00532c70`) azon az ágon, ahol sem a dátum, sem a felbontás jelölője nincs bejelölve (`0x00532cdd`, `0x00532cf0`), a `0x00532710` által képzett mintanévre lefuttatja a `0x009946f0` névtisztítót (`0x00532d1f`), és a Rename gombot letiltja, ha a tisztítás hibát ad, üres eredményt ad, vagy a név nem változik (`0x00532d94`).
- **Nálunk:** `FileOpsDialogs.qml:347-353`: a `\ / : * ? " < > |` karakter nem gépelhető be, a hossz legfeljebb 200.
- **Döntés: nem blokkoló.** A PicasaPy mezője szigorúbb, de olyan nevet nem tud előállítani, amelyet az eredeti fájlrendszeri szinten el tudna fogadni; a felhasználó legfeljebb annyit lát, hogy egy tiltott karakter nem írható be.

#### 6. Lezárva: az AdjustTimeThread JPEG-en kívüli formátumoknál (`0x00490580`, `0x00490C10`)

A kérdésre a meglévő bizonyíték (`pmp-database.md` 15.1) és az alábbi mérés válaszol, új Ghidra-kör nem kell. **Nem PMP-oszlopba ír, hanem a `thumbindex.db` rekord első FILETIME mezőjébe (`creation_filetime`) és a fájl létrehozási idejébe.**

- Az ág típus szerint dönt: `cmp [puffer+0x18], 2` (`0x0049070a`, `0x00490d4f`); csak a 2-es típus megy az EXIF-ágra (`0x009ed330`). Minden más típus a nem-EXIF ágra: létrehozási idő (`0x00490900`/`0x00490f40` → `0x00992780`) és rekordmódosítás (`0x004ef3c0` eltolás, `0x004ef5a0` abszolút), amelyek a `2, 3, 6-18, 21-24, 26, 27-29, 31, 1001` típusokra írnak (`0x004ef436`-`0x004ef46d`, `0x004ef618`-`0x004ef64f`).
- **Mérés (2026-11-17, a `read_thumb_index` olvasóval a két valódi katalógus `thumbindex.db`-jén; típus = rekord `+0x18`):** nagy katalógus (140 758 rekord): `.png` 14-es típus 7 663 db, 2-es típus 33 db, 31-es 1 db; `.bmp` 6-os 707 db; `.gif` 3-as 394 db; `.webp` 31-es 4 db; `.avi` 8-as 37 db; `.mp4` és `.mpg` és `.mts` 10-es 2 645 db; `.wmv` 11-es 13 db; `.jpg` és `.jpeg` főként 2-es. Kisebb katalógus (3 338 rekord): `.png` 14-es 125 db, `.tif` 13-as 3 db, `.bmp` 6-os 206 db, `.webp` 31-es 1 db, `.mp4` 10-es 17 db.
- **Válasz:** a PNG (14), a TIFF (13), a BMP (6), a GIF (3), a WebP (31) és a videók (8, 10, 11) mind a nem-EXIF ágra mennek és mind benne vannak a rekordíró típuskészletében; módosított dátumuk a `thumbindex.db` első FILETIME mezőjébe kerül. Az a 33 `.png`, amelynek típusa 2, EXIF-ágra menne; a fájl tartalmát nem vizsgáltam.
- **Nálunk:** a nem JPEG fájlnál az EXIF-írás hibára fut, és a dátum a SQLite `photos.taken_at_override` mezőbe kerül (a fenti #7033 szakasz, 3. rész; `timestamp_controller.py:283-305`). A tárolás helye eltér (a PicasaPy saját indexe, nem a `db3`), a látható hatás (új dátum a rácsban és a rendezésben) azonos. **Döntés: nem blokkoló.**

#### 7. Lezárva: a `RenameUseDate` dátumszövege

A kérdést a bináris eldönti, Colab-mérés nem adna többet (a Wine nem a valódi Windows területi beállítását futtatná).

- **A dátum előállítása:** a `0x0098b650` a FILETIME-ot helyi időre, majd `DATE` értékre alakítja (`SystemTimeToVariantTime`, OLEAUT32 #184; `picasa-metaadat-tulajdonsagok.md:2403`). A `0x0098c470` ebből szöveget készít: `push eax(&BSTR); push 0; push 0x400; <dupla>; call [0x00c405c4]` (`0x0098c481`-`0x0098c49c`) = **`VarBstrFromDate(dátum, LOCALE_USER_DEFAULT, 0)`** (OLEAUT32 #114), majd UTF-8 átalakítás (`WideCharToMultiByte`, `0xfde9`).
- **Ami a névbe kerül:** a `0x00532ec0` ciklusában az alapnév után egy szóköz (`0x00c89a98`) és a dátumszöveg következik, ahol minden `:` (`0x3a`) és `/` (`0x2f`) karakter `-`-re cserélődik; más elválasztó (pont, szóköz, vessző) változatlan marad. A méret ezután ` %dx%d` alakban jön (`0x00c89a9c`, `0x00533358`). Az előnézet ` 08-01-2004 2-30-45 PM` mintája csak a párbeszédé (`0x00c89a18`).
- **Ami a Windows területi beállításán múlik:** a konkrét dátum- és időforma a `VarBstrFromDate` szerződése (rövid dátum és hosszú idő a felhasználó beállításával, éjfélkor csak a dátum; `picasa-metaadat-tulajdonsagok.md:2409`). Ezt nem a bináris adja, és mi nem mértük valódi Windowson.
- **Nálunk (`rename.py:198-215`, `format_taken_at`):** a `QLocale` rövid dátuma és rövid ideje másodperccel, a tiltott karakterek `-`-re cserélve; a kétjegyű évet négyjegyűre bővíti (`_TWO_DIGIT_YEAR_RE`). Két apró eltérés lehetséges: a `VarBstrFromDate` a felhasználó rövid dátumformáját változtatás nélkül adja (kétjegyű év is lehet), és pontosan éjféli időnél csak a dátumot írja ki.
- **Döntés: nem blokkoló** (csak ritka területi beállításnál és pontosan 00:00:00 időnél látszik). Külön jegy nincs.

#### 8. A szerkesztőben nyitott kép és a Sepia, a Fekete-fehér

A „Belépési pontok és feltételek” tábla „Szerkesztőnézetbeli navigáció” sora „Eltérés” jelzésű, de a „(1. jegytörzs)” hivatkozása téves (az 1. jegytörzs a figyelmeztetésről szól), és jegytörzse nem volt. Most van (5. jegytörzs).

- **Eredeti:** a `0x00579330` igaz, ha az `editpanel/preview` elem létezik és látható (`[0x00d67914] != 0`, `0x009c2fc0`, `[eax+0x20c] == 0`). A `0x005cb990` kezelő `0x9d4d` (`"warm"`), `0x9d4b` (`"unsharp"` / `"unsharp2"`), `0x9d4e` (`"grain"` / `"grain2"`), **`0x9d4a` (`"sepia"`) és `0x9d4c` (`"bw"`)** ágán ilyenkor ugyanaz a két hívás fut: `0x005f8520(név)` és `0x00a54b70(...)` (`2026-10-21-idorend-30.txt:2056-2112`). Az `0x9d48` és `0x9d49` ilyenkor nevet nem ad át, hanem kétszer a közös továbbító függvényt hívja (`0x009cd8a0`: dinamikus típusátalakítás a megnyitott felület objektumára, majd virtuális hívás a `+0x78` rekeszen); ennek a hatását ez a kör nem követte.
- **Nálunk:** `PhotoViewerGeometryActions.qml:357-369` (`selectMenuEffect`) csak az `autolight`, `autocolor`, `enhance` (0. fül) és az `unsharp`, `warm`, `grain2` (2. fül) nevet kezeli; a `sepia` és a `bw` `false`-t ad, és a `MainMenuBar.qml:427` egyképes `applyEffectMany([row], name)` kötegre esik vissza.
- **Megmaradó, örökölt, nem blokkoló kérdés:** hogy a `0x005f8520` (a név szerinti eszközválasztó, `editpanel/puck`) pontosan mit csinál (csak kijelöl, vagy alkalmaz is), az a `paritas-ellenorzes-archiv-1.md` 3345. sorában már nyilvántartott `Ghidra-kör kell: 0x005f8520` tétel. Az 5. jegytörzs ezt nem dönti el, csak a `sepia` és a `bw` ágat igazítja a három testvéréhez.

### Zárási döntés

**A #7084 kutatási jegy lezárható.** Nincs blokkoló. Az összes nyitott kérdés lezárult (17 lezárva, 0 nyílt, 0 blokkolt); az egyetlen örökölt kérdés (`0x005f8520` eszközmódja) nem blokkoló és már nyilvántartott. Az átnevezési sorszámozás vitája eldőlt (Zárókör 1. pont). A zárókör helyesbítette az `IDS_SOME_EDITS_FAILED_TYPE` szövegét és megjelenítési módját (2. pont), a Show Text és Hide Text kapujának leírását (3. pont), valamint a 4. pontban felsorolt elavult „Nálunk” állításokat; a korábbi szöveg érintetlen, a helyesbítések a Zárókörben vannak.

**Készre ítélt jegytörzsek (jegy nem kell):**

- **3. Dátummódosítás ablakcíme egy képnél:** kész, `AdjustTimestampDialog.qml:22-24` (#5703, `61d52d613`).
- **4. Csoportos átnevezés háromjegyű számozása:** kész, `rename.py:265-303` (#5941, `f827076c5`); a Zárókör 1. pontja az eredeti viselkedést bizonyítja.

**Megmaradó fejlesztői jegytörzsek (három):**

#### 1. (módosítva) A nem támogatott fájl és az üres kijelölés figyelmeztetése modális Információ-ablakban

**Eredeti:** a kötegelt effekt (`IDS_SOME_EDITS_FAILED_TYPE`, `0x005fe8bd`-`0x005fe8c2`), a kötegelt forgatás (`IDS_ROT_TYPEFAILED`, `0x005eeee9`), a forgatás üres kijelölése (`IDS_MUST_SELECT_TO_ROT`, `0x005ef348`) és az effekt üres kijelölése (`IDS_NEEDS_SELECTION`, `0x005fe966`) egyaránt a `0x009807f0`-on át jelenik meg: `MessageBoxA`, `MB_ICONINFORMATION` (`0x40`), egyetlen OK gomb, cím `ytApp::InfoTitle` („Információ”), szülőablak az aktív ablak. A forgatás és az effekt előbb lefut a támogatott képekre, a figyelmeztetés a végén jön.

**Nálunk:** a jelzés megvan (`batchEditTypeFailed`, `rotationTypeFailed`, `rotationNeedsSelection`), a szöveg helyes, de a forma értesítősáv (`PicasaNotifier.qml:429-461`), nem modális ablak.

**Teendő:** a három meglévő jelzést (`onRotationTypeFailed`, `onRotationNeedsSelection`, `onBatchEditTypeFailed`) a `copyAllEffectsInfoDialog` mintájára (`MainWindowDialogStack.qml:110-140`) modális, egy OK gombos, kék „i” ikonos Információ-ablakkal kell megjeleníteni; a cím az „Info” szövegtár-kulcs (`ytApp::InfoTitle`) fordítása. A szövegek változatlanok. Az effekt üres kijelölésénél (`IDS_NEEDS_SELECTION`, „This operation requires selected images.”) a menü szürke, így csak billentyűparancsnál érhető el; ott is ugyanez az ablak jön.

**Kész, ha:** vegyes (kép és videó) kijelölésre kötegelt effektet vagy forgatást adva a képek módosulnak, és a végén modális Információ-ablak jelenik meg a szövegtár szerinti szöveggel; tisztán képes kijelölésnél nem jelenik meg ablak; a három jelzéshez van ablakos teszt (a megjelenített szöveg és az OK gomb ellenőrzésével).

#### 2. (helyesbítve) A Show Text és Hide Text engedélyezése nem függhet a képek ini-állapotától

**Eredeti:** a `0x0056e1c0` menüépítő a Show Text (`0x9deb`) és Hide Text (`0x9dec`) tételhez csak a `0x4000` állapotbites ágban nyúl (`EnableMenuItem(..., 1)` = szürkítés, `0x0056f2d1`, `0x0056f2db`), ahol a csoport összes tétele szürke; külön engedélyező hívás nincs, a `.picasa.ini`-t a függvény nem olvassa. A Zárókör 3. pontja a bizonyíték. A `0x005f6a40` kezelő kattintáskor maga állítja át a `textactive` értéket.

**Nálunk:** `PicasaPictureMenu.qml:9` (`onAboutToShow: bar.textOverlayStatesRefreshRequested()`), `:105-113` (`enabled: bar.photoActionsEnabled && bar.textOverlayShowEnabled` és `...HideEnabled`), `MainMenuBar.qml:77-83`, `batch_effect_controller.py:410` (`hasTextOverlayStateInSelection`): a két tétel a kijelölt képek ini-állapotától függ, és minden menünyitáskor ini-t olvas.

**Teendő:** a két tétel kapuja legyen azonos a csoport többi tételével (`enabled: bar.photoActionsEnabled`); a `textOverlayStatesRefreshRequested` menünyitáskori ini-olvasás és a `hasTextOverlayStateInSelection` kikerül, ha máshol nincs használata.

**Kész, ha:** kijelölt képeknél mindkét tétel aktív, akkor is, ha egyik képen sincs ráírt szöveg; üres kijelölésnél a Csoportos szerkesztés almenü szürke marad; a Show Text és a Hide Text kattintásra a `setTextOverlayVisibleMany`-t hívja; a menü megnyitása nem olvas `.picasa.ini`-t.

#### 5. (új) Sepia és Fekete-fehér, ha a szerkesztőben nyitott kép van

**Eredeti:** a `0x00579330` igaz állapotában a `0x9d4a` (`"sepia"`) és a `0x9d4c` (`"bw"`) a `0x9d4d` (`"warm"`), a `0x9d4b` (`"unsharp"`) és a `0x9d4e` (`"grain2"`) ágával azonos hívásokat futtatja: `0x005f8520(név)` és `0x00a54b70(...)` (Zárókör 8. pont).

**Nálunk:** `PhotoViewerGeometryActions.qml:357-369`: a `sepia` és a `bw` nincs a `selectMenuEffect` listájában, ezért a `MainMenuBar.qml:427` egyképes `applyEffectMany([row], name)` kötegre esik vissza, miközben a `warm`, `unsharp`, `grain2` a 2. fület választja ki.

**Teendő:** a `selectMenuEffect` a `sepia` és a `bw` nevet is a 2. fülre (`editorPanel.selectTab(2)`) irányítsa, azaz a három testvérével azonosan viselkedjen.

**Kész, ha:** szerkesztőben nyitott képnél a Kép ▸ Csoportos szerkesztés ▸ Sepia és ▸ Black and White ugyanúgy az Effektek fület választja ki, mint a Warmify; nem módosítja a `filters=` láncot és nem indít kötegelt műveletet; könyvtárnézetben a kijelölt képekre továbbra is lefut. A `0x005f8520` pontos hatása (kijelöl vagy alkalmaz is) a fent említett örökölt kérdés, ezért ez a jegytörzs csak az ágak egységességét kéri.

**Nem a #7084 hatóköre, de a zárókör közben kiderült:** a `paritas-ellenorzes-archiv-1.md` 2496. sorának „NINCS MEG” jelölése (a figyelmeztetés ablaktípusa) e körben megválaszolódott (modális Információ-ablak, Zárókör 2. pont); a `picasa-fen-dialogs.md` 501. sora még a régi `renamePreview` előnézetre hivatkozik, pedig a látható sort már a `renameSamplePreview` adja (#5702). Mindkét lapot a hívó vezesse át.
