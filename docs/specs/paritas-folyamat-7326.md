# A nézet rendezésének és megjelenítésének teljes folyamata az eredeti Picasával összevetve (#7326, második kör)

Issue: #7326. Eredeti: Picasa 3.9.141.259, SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96` (a helyi `Picasa3.exe` bitre azonos a bináris-indexben szereplővel). Kép-alap: az `0x00400000`. A bináris statikusan volt vizsgálva (capstone, a `pe_dis.py` és az index), a két tulajdonosi felvétel pedig a mérce (lásd 1. szakasz).

A lap a Nézet és a Mappa menü rendezési és megjelenítési parancsait követi a belépési ponttól a hatásig: a bal hasáb ▾ ("View options") legördülőjét, a Nézet ▸ Mappanézet almenüt, a Mappa ▸ Rendezés almenüt, az Indexkép felirata almenüt és a hasáb jobbklikk-menüjét. A bélyegméret-csúszka (`Thumbscale`, `ThumbscalePeople`) tárgya a #7333, azt ez a kör szándékosan nem vizsgálja újra.

## Következtetés

**A rendezési szemantika egyezik, a menük szerkezete nem.** A rendezés kulcsai, iránya, alapértéke és a fordítás független tárolása a PicasaPy-ban az eredetit követik, és az Indexkép felirata almenü is egyezik (egy mnemonikus betű hiányát leszámítva). Az eltérés abban van, hogy az eredetinek **két külön menütáblája** van (a ▾ gomb 14 rekordos legördülője és a menüsáv 13 rekordos Mappanézet almenüje), a PicasaPy pedig **egyetlen** `PicasaFolderViewMenu`-t nyit mindkét belépési pontról, ráadásul a két meglévő menüben tételek hiányoznak, többletként vannak jelen, vagy fordított sorrendben állnak. Emellett a menüsáv Mappa ▸ Rendezés tételei nálunk **tartós rácssorrendet** állítanak, az eredetiben viszont **egyszeri átrendezést** végeznek az aktuális mappa képein.

Négy javasolt fejlesztői jegytörzs (J1-J4) és egy felirat-apróság (J5), a 7. szakaszban; a J1-J4 azóta a fő ágba került (#7340, #7341). A futásidejű kérdéseket (C1-C5) a Colab-mérés döntötte el (8. szakasz, "Mérési eredmény (Colab)"): a mérés négy újabb eltérést hozott (J6-J9), és egyetlen új mérést nevesít (C5c).

### Az első kör két állításának helyesbítése

| Az első kör állítása | Mi igaz | Bizonyíték |
|---|---|---|
| A "Show Thumbnails in Library" engedélyezett (egy disassembly-ugrásból levezetve). | **Fanézetben (`[+0x9d] != 0`) szürke**, lapos nézetben engedélyezett. A tulajdonos 3. felvétele (#2989) és a bináris egyaránt ezt mutatja. | `0x005e2596`: `EnableMenuItem(menü, 0x9cd7, [+0x9d] != 0)`, lásd 3.2. |
| A `0x9c5e` parancs a Mappa ▸ Rendezéshez tartozik. | A `0x9c5e` az **Indexképek frissítése** (`eMenuLabelFolder::ID_REFRESH_THUMB`). A Mappa ▸ Rendezés négy parancsa `0x9cd3`, `0x9cd4`, `0x9cd5`, `0xa0d0`. | `0x0055af0d`: `mov word ptr [0xd6e206], 0x9c5e` a `ID_REFRESH_THUMB` rekordban (`0xd6e1fc`); a rendezés rekordjai `0xd6e170`-`0xd6e1ac`. |

## 1. Mérce: két tulajdonosi felvétel és a bináris menütáblák

A két felvételen minden tétel a bináris rekordjaival tételenként egyezik. A mérce erősebb a statikus következtetésnél, ezért a lap minden eltérése ezekhez köti a PicasaPy kódját.

- **A ▾ legördülő** (`2026-07-17 20 58 37.png`, leltár 26. sor): Rendezés dátum alapján (pipa) · legutóbbi változtatások · méret · név · megfordítása | Személyek rendezése név alapján (pipa) · mennyiség alapján · **toplista alapján (szürke)** | Gyorsbillentyűk ▸ | Indexképek megjelenítése a könyvtárban · Egyszerűsített fanézet. A bal hasáb ekkor **lapos** nézetben áll (az első nézetváltó gomb aktív, évszám-fejlécek a mappalistában).
- **A Nézet ▸ Mappanézet almenü** (`Képernyőkép 2026-07-18 151412.png`, leltár 41. sor): Egyszerű mappanézet (pipa) · Fanézet | Rendezés létrehozási dátum alapján (pipa) · legutóbbi változtatások · méret · név · megfordítása | Gyorsbillentyűk ▸ | Indexképek megjelenítése a könyvtárban · Egyszerűsített fanézet. **Emberek-rendezési tétel és gyökértétel az almenü felső szintjén nincs.**

## 2. Az eredeti két menütáblája (kimérve)

### 2.1 A ▾ gomb legördülője: `0x00733480` (14 rekord)

A `0x00733480` (1311 bájt) nem menüt rajzol, hanem **egyszer feltölti a rekordtáblát** (az újrafuttatást a `test byte ptr [0xda0384], 1` védi a `0x00733483`-on, a 2-es bitet a `0x007335de`), majd `CreatePopupMenu`-t hív (`0x00733978`, `[0xc408f0]`), és a 14 rekordot a `0x00a6aee0`-val tölti be (`push 0xe`, `push 0xd6efd0`: `0x0073397f`-`0x00733981`). Egyetlen hívója a `0x005e2000` (`call 0x733480` a `0x005e2096`-on; a teljes `.text` rel32 és abszolút hivatkozás-pásztázása semmi mást nem ad). A `0x005e2000` hívója a `0x005d9cc0` eseménykezelő (`0x005db5b9`), a `thumbui/folderviewpopup` névre.

Rekordméret 20 bájt, a parancsszó a rekord `+0x0a` helyén. A menüpont sorrendje a rekordtábla sorrendje:

| # | Rekord | Kulcs | Felirat (angol) | Parancs | Ír a rekordba |
|---:|---|---|---|---|---|
| 0 | `0xd6efd0` | `AlbumList::ID_VIEWBYDATE` | Sort by &Date | `0x9c8b` | `0x0073363b` |
| 1 | `0xd6efe4` | `AlbumList::ID_VIEWBYRECENT` | Sort by &Recent Changes | `0x9cbd` | `0x00733685` |
| 2 | `0xd6eff8` | `AlbumList::ID_VIEWBYSIZE` | Sort by &Size | `0x9dc8` | `0x007336cf` |
| 3 | `0xd6f00c` | `AlbumList::ID_VIEWBYNAME` | Sort by &Name | `0x9c8c` | `0x00733719` |
| 4 | `0xd6f020` | `AlbumList::ID_VIEWREVERSE` | Re&verse sort | `0xa0cf` | `0x00733777` |
| 5 | `0xd6f034` | (elválasztó) | | | |
| 6 | `0xd6f048` | `AlbumList::ID_PEOPLEBYNAME` | Sort &People by Name | `0x9e18` | `0x007337c7` |
| 7 | `0xd6f05c` | `AlbumList::ID_PEOPLEBYAMOUNT` | Sort People by &Amount | `0x9e19` | `0x00733811` |
| 8 | `0xd6f070` | `AlbumList::ID_PEOPLEBYAMOUNTTOP10` | Sort People by Top &10 | `0x9e38` | `0x0073386f` |
| 9 | `0xd6f084` | (elválasztó) | | | |
| 10 | `0xd6f098` | `AlbumList::Shortcuts` | &Shortcuts (almenü) | nincs | gyerekek: `0xd6ef68`, darab 5 (`0x007338d0`, `0x007338da`) |
| 11 | `0xd6f0ac` | (elválasztó) | | | |
| 12 | `0xd6f0c0` | `AlbumList::ID_VIEW_THUMBNAILS` | Show &Thumbnails in Library | `0x9cd7` | `0x0073392b` |
| 13 | `0xd6f0d4` | `AlbumList::ID_VIEW_WATCHED` | &Simplified Tree View | `0x9db8` | `0x00733961` |

A Shortcuts almenü öt gyereke (`0xd6ef68`-tól): **Desktop** `0x9dba` · **My Documents** `0x9db7` · **My Pictures** `0x9e3a` · (elválasztó) · **My Computer** `0x9db9`. Sem Egyszerű/Fa nézetváltó, sem gyökértétel nincs a legördülő felső szintjén.

### 2.2 A menüsáv Nézet ▸ Mappanézet almenüje: `0x00559150` (13 rekord)

A fejlécrekord `eMenuView::FolderView` (`0xd6e158`): a gyerekek mutatója `0xd6de98` (`0x0055ac7a`), a darabszám `0xd` = 13 (`0x0055ac84`). A rekordok:

| # | Rekord | Kulcs | Felirat | Parancs |
|---:|---|---|---|---|
| 0 | `0xd6de98` | `eMenuView::ID_VIEW_FOLDERS` | &Flat Folder View | `0x9db6` |
| 1 | `0xd6deac` | `eMenuView::ID_VIEW_ALL` | &Tree View | `0x9db9` |
| 2 | `0xd6dec0` | (elválasztó) | | |
| 3 | `0xd6ded4` | `eMenuView::ID_VIEWBYDATE` | Sort by &Creation Date | `0x9c8b` |
| 4 | `0xd6dee8` | `eMenuView::ID_VIEWBYRECENT` | Sort by &Recent Changes | `0x9cbd` |
| 5 | `0xd6defc` | `eMenuView::ID_VIEWBYSIZE` | Sort by &Size | `0x9dc8` |
| 6 | `0xd6df10` | `eMenuView::ID_VIEWBYNAME` | Sort by &Name | `0x9c8c` |
| 7 | `0xd6df24` | `eMenuView::ID_VIEWREVERSE` | Re&verse sort | `0xa0cf` (`0x0055a55f`) |
| 8 | `0xd6df38` | (elválasztó) | | |
| 9 | `0xd6df4c` | `eMenuView::Shortcuts` | &Shortcuts (almenü) | gyerekek: `0xd6de30` (`0x0055a5ce`), darab 5 (`mov edi, 5` `0x0055a335`, `0x0055a5d8`) |
| 10 | `0xd6df60` | (elválasztó) | | |
| 11 | `0xd6df74` | `eMenuView::ID_VIEW_THUMBNAILS` | Show &Thumbnails in Library | `0x9cd7` |
| 12 | `0xd6df88` | `eMenuView::ID_VIEW_WATCHED` | &Simplified Tree View | `0x9db8` |

A parancsszavakat közvetlenül a `mov word ptr [rekord+0x0a]` írásokból olvastam (`0x0055a385`, `0x0055a3cf`, `0x0055a437`, `0x0055a481`, `0x0055a4cb`, `0x0055a515`, `0x0055a55f`, `0x0055a631`, `0x0055a671`).

Az öt Shortcuts-gyerek (`0xd6de30`-tól): Desktop · My Documents · My Pictures · (elválasztó) · My Computer, azonos sorrendben, mint a ▾ legördülőben. **A két tábla különbsége:** a menüsáv Mappanézet almenüjében van Flat/Tree és a rendezés felirata "Creation Date", az Emberek-rendezés nincs; a ▾ legördülőben nincs Flat/Tree, a dátumrendezés felirata "Date", és az Emberek-rendezés megvan.

### 2.3 A Mappa ▸ Rendezés és az Indexkép felirata almenü

- **Mappa ▸ Rendezés** (`eMenuLabelFolder::SortBy`, `0xd6e210`): gyerekek `0xd6e170` (`0x0055af63`), darab 4 (`mov edi, 4` `0x0055af40`): **&Name** `0x9cd3` · **&Date** `0x9cd4` · **&Size** `0x9cd5` · **&Reverse order** `0xa0d0`. "Legutóbbi változtatások" nincs benne. A tételek az `album-sorrend.md` 2.4 szerint **egyszeri átrendezést** végeznek (`0x005e5ce0(ui, mód, Shift)`, mód 6/3/5/12), nincs tárolt mód és nincs pipa.
- **Indexkép felirata** (`eMenuView::ThumbnailCaption`, `0xd6e144`): gyerekek `0xd6ddc8` (`0x0055ac38`), darab 5 (`mov edi, 5`, `0x0055ac42`): **&None** · &Filename · &Caption · &Tags · &Resolution. A szövegtár: `eMenuView::ID_CAPNONE	&None	&Nincs`.

## 3. Mit csinál a ▾ legördülő: a `0x005e2000` kezelő

### 3.1 Állapotok és azok forrása

A kezelő a menü **megnyitásakor** fut, és minden pipát a `[esi+0x2c0]` listaobjektum mezőiből épít (`CheckMenuItem`, `[0xc40810]`, jelző 0 vagy 8):

| Pipa | Feltétel | Cím |
|---|---|---|
| `0x9c8b` Dátum | `[+0xd8] == 0` | `0x005e20b5`-`0x005e20c6` |
| `0x9cbd` Legutóbbi | `[+0xd8] == 1` | `0x005e20c8`-`0x005e20e0` |
| `0x9c8c` Név | `[+0xd8] == 2` | `0x005e20e4`-`0x005e20f9` |
| `0x9dc8` Méret | `[+0xd8] == 5` | `0x005e20fd`-`0x005e2112` |
| `0xa0cf` Megfordítás | `[+0x165] != 0` | `0x005e211a`-`0x005e212e` |
| `0x9e18` / `0x9e19` / `0x9e38` | `[+0xdc] == 0` / `1` / `2` | `0x005e2136`-`0x005e2190` |
| `0x9cd7` Indexképek | `Preferences\ShowAlbumThumbnails2 != 0` | `0x005e25ef`-`0x005e2628` |
| `0x9db8` Egyszerűsített | `Preferences\SimplifiedHierarchy` | `0x005e227d` |

### 3.2 Tiltások (új lelet ebben a körben)

A kezelő a pipákon kívül **két** `EnableMenuItem`-et (`[0xc40818]`, USER32 import) hív a `[esi+0x2c0]+0x9d` bájt alapján (a `0x9d` a mappa-hasáb "hierarchikus" jelzője: nem nulla = fanézet, lásd `picasa-mappanezet.md` 3.):

- `0x005e2596`: `EnableMenuItem(menü, 0x9cd7, [+0x9d] != 0)`: az **Indexképek megjelenítése** fanézetben **szürke**.
- `0x005e25a4`-`0x005e25b9`: `EnableMenuItem(menü, 8, (([+0x9d] == 0) | 0x400))`: a `0x400` a `MF_BYPOSITION`, tehát a **8. pozíció** (a 2.1 tábla 8. rekordja, a **Sort People by Top 10**) lapos nézetben **szürke** (a jelző 1 = `MF_GRAYED`).

A #26 felvétel egyezik ezzel: a lapos nézetben a toplista szürke, az Indexképek és az Egyszerűsített tétel engedélyezett.

A kezelő három további `EnableMenuItem`-et is hív a Shortcuts-gyerekekre (`0x005e2558` My Pictures `0x9e3a`, `0x005e256a` és `0x005e257c` mindkettő `0x9dba`): a jelzők a `0x004f7e40` három hívásának eredményei (az argumentumot a `0x009966a0` (`CSIDL_MYPICTURES`), `0x00996230` (`CSIDL_PERSONAL`) és `0x00996b90` (`CSIDL_DESKTOP`) adja; a hívások jelentését a mérés utáni kör bontotta ki, lásd a 8. szakasz C4 eredményét). A `0x005e257c` a My Documents (`0x9db7`) helyett is a Desktop azonosítót küldi, tehát a My Documents ebben a kezelőben sosem kap tiltást. A korábbi "Windows-specifikus, a PicasaPy-ban nincs teendő" állítás **megdőlt** (9. szakasz, J7).

### 3.3 Megjelenítés

`TrackPopupMenu` (`[0xc407c4]`, `0x005e264e`: `uFlags = 2`), a pozíciót a `ClientToScreen` (`[0xc40828]`, `0x005e208c`) adja. A hívás körül a kezelő a `[esi+0x34a4]` számlálót eggyel növeli (`0x005e2637`) és csökkenti (`0x005e2659`): lásd a 9. szakasz helyesbítését.

## 4. Hatás: mi változik a parancs kiadásakor

| Kérdés | Eredeti | Bizonyíték | Fok |
|---|---|---|---|
| Mikor hat? | **Azonnal**, a menüpont kiválasztásakor. Az `0x004b07c0` (75 bájt) a mezőt és a megfordítást egyszerre állítja (`0x004b07dc`, `0x004b07e2`), azonos érték mellett nem csinál semmit (`0x000f4242`), különben a `0x006dc4c0(…, 1)` újraépíti a listát (`0x004b0803`). | `picasa-idorend-bemutato-kutatas.md` §2, `picasa-menu-parancsok-viselkedes.md` 67.3 | megerősített |
| Mit ír? | Csak a `Preferences` kulcsait: **`datesort`** (mód 0/1/2/5, `0xc83078`), **`peoplesort`** (0/1/2, `0xc83084`), **`albumlistflip`** (megfordítás, `0xc83090`). Olvasó `0x004a1560` (`0x004a195f`-`0x004a1a05`), író `0x004a3790`. **Fájlt, `.picasa.ini`-t, indexet nem ír.** | `picasa-menu-parancsok-viselkedes.md` 36.3 | megerősített |
| Alapérték | `datesort` 0 (dátum), `peoplesort` 0 (név), `albumlistflip` 0: a `GetPreference` hívás előtt `xor eax, eax` (`0x004a196e`), és a #26 felvétel dátumrendezést mutat. **Tiszta profilon mérve** (Colab): az első indításkor a hasáb dátum szerint csökkenő, évszám-fejlécekkel, megfordítás nélkül (job-802 4. kép; job-806 18. kép az újraindítás után). | `0x004a1930`-`0x004a1a05`, `picasa-menu-parancsok-viselkedes.md` 36.3, Colab job-802, job-806 | megerősített |
| Szempontváltáskor a fordítás | **Megmarad** (a két mező egy hívásban, a gombok a jelenlegi megfordítást adják tovább). Mérve: a Reverse után a Recent Changes, majd a Date választása is növekvő sorrendet ad (Colab job-802 19., 25., 29. kép). | `0x004b07cc`, `0x005db200`, `0x005db266`, Colab job-802 | megerősített (mért) |
| Irány | Dátum, legutóbbi, méret **csökkenő** (az újabb, a nagyobb előbb), név **növekvő**. | `0x004a7890`, `picasa-idorend-bemutato-kutatas.md` §2 | megerősített (név: erős) |
| Mi fut le utána? | A hasáb újraépül; a Mappa ▸ Rendezéssel ellentétben **a képek sorrendjét nem írja át**. Háttérmunka, állapotsor-üzenet, folyamatjelző a ▾ parancsokhoz nincs a kezelőben. | `0x005e2000` teljes olvasata | erős |
| Hiba, megszakítás, írásvédett vagy hálózati hely | A ▾ parancsok fájlt nem módosítanak, ezért írásvédett vagy hálózati helyre vonatkozó ág nincs; a `Preferences` registry-írás eredményének vizsgálatát a `0x004a3790`-ben nem olvastam ki: NINCS MEG. | `0x004a3790` | feltételes |
| Visszavonás | A `0x004b07c0` (75 bájt) csak a két mezőt írja és újraépít, előző állapotot nem ment, és a két menütábla egyik rekordja sem hív visszavonást. A mód közvetlenül újra állítható. | `0x004b07c0`, 2.1 és 2.2 tábla | feltételes |
| Mikor kerül a registrybe? | **Nem a váltás pillanatában**: 40 mp múlva sincs a `datesort`, `peoplesort`, `albumlistflip` a `Preferences` kulcsban (job-805), és a Picasa kényszerített leállítása és újraindítása után a hasáb az alapállapotba áll vissza (job-806). A `0x004a3790` író egyetlen hívója a lista-objektum destruktor-burkolója (`0x004a35d0`), tehát a mentés az objektum megsemmisülésekor (leálláskor) várható. A szabályos kilépés utáni mérés (C5c) még hiányzik. | job-805, job-806, `0x004a35d3`, `0x00c8368c` | mért (nem azonnal) · erős, statikus (leálláskor) · a szabályos kilépés mérése nyitott |

## 5. Belépési pontok és feltételek

| Belépési pont | Eredeti | Nálunk (fájl:sor) | Eredmény |
|---|---|---|---|
| Eszköztár ▾ ("View options", `thumbui/folderviewpopup`) | A 14 rekordos legördülő (2.1), lenyomásra nyílik. | `MainToolbar.qml:365`: `onPressedChanged: if (pressed) toolbar.folderViewMenuRequested(parent)`; `PicasaViewMenu.qml:14-15`: `function openFolderViewMenu(anchorItem) {` `folderViewMenu.popup(anchorItem, 0, anchorItem.height)` | **Eltér** (J1): a menüsáv almenüjét nyitja. |
| Menüsor Nézet ▸ Mappanézet | A 13 rekordos almenü (2.2). | `PicasaViewMenu.qml:548`: `PicasaFolderViewMenu {`; tartalma `PicasaFolderViewMenu.qml` | **Eltér** (J2). |
| Bal hasáb üres részén jobbklikk | **Nincs menü** (mért, Colab job-801: két ponton, 05-06. és 09-10. kép). Az `AlbumList` tábla (`0xd6efd0`) egyetlen felhasználója a ▾ kezelő; a `ui-audit-context-menus.md` A.2 szerint ez a menü "a képernyőképeken nem szerepelt". | `FolderPane.qml:604-607`: `objectName: "folderPaneContextMenuHandler"` ... `onSingleTapped: pane.openFolderListContextMenu()` | **Eltér** (J6, #7349). |
| Menüsor Mappa ▸ Rendezés | Négy tétel, egyszeri átrendezés az aktuális mappa/album képein (2.3). | `PicasaFolderMenu.qml:62`: `title: qsTr("&Sort By")`; `:69`: `controller.setFolderSort("date")` | **Eltér** (J4). |
| Mappasor jobbklikk ▸ Mappa rendezésének alapja | Ugyanaz a négy parancs, egyszeri átrendezés. | `FolderPaneMenus.qml:382`: `controller.sortFolderBy(folderContextMenu.folderPath, mode)` | Egyezik (az `album-sorrend.md` 2.4 és a #4890 szerint). |
| Menüsor Nézet ▸ Indexkép felirata | Öt tétel (2.3). | `PicasaViewMenu.qml:477-478`: `objectName: "menuViewThumbCaptionNone"` / `text: qsTr("None")` | Egyezik, a `&` hiányzik (J5). |
| Gyorsbillentyű | **Nincs.** A rekordok `+0x04` gyorsbillentyű-szövege nulla (a ▾ táblában `0x0073362e`, a menüsávban `0x0055a552`), és a 24 gyorsbillentyűs menürekord listájában (`picasa-menu-leltar.md` 8.3) a rendezés- és nézetparancsok közül (`0x9c8b`, `0x9cbd`, `0x9c8c`, `0x9dc8`, `0xa0cf`, `0x9cd3`-`0x9cd5`, `0xa0d0`, `0x9cd7`, `0x9db6`, `0x9db8`, `0x9db9`) egyik sem szerepel. | a PicasaPy rendezés-menüiben sincs gyorsbillentyű-szöveg | Egyezik (negatív, erős). |
| `thumbui/datesort`, `thumbui/namesort` | A `0x005d9cc0` kezeli (`0x005db26d` mód 0, `0x005db207` mód 2, `picasa-menu-parancsok-viselkedes.md` 67.1). A `tre-eroforrasok/` alatt `datesort` vagy `namesort` csomópont nincs (grep: 0 találat), gombként való megjelenése nem igazolt. | A PicasaPy-ban a két névre hivatkozás nincs (`grep -rn "datesort\|namesort" src/picasapy/app`: 0). | Egyezik: a futó eredeti eszköztárán nincs ilyen gomb (Colab job-802, mind a 29 kép), lásd C2. |
| Bal hasáb Lapos/Fa gombpár | `thumbui/flatview`, `thumbui/folderview` (`0x005d9cc0`). | `MainToolbar.qml` `toolbarFlatViewButton`, `toolbarFolderViewToggle` | Egyezik (#1421). |

## 6. Eredeti | Nálunk | Teendő

| # | Eredeti (bináris cím) | Nálunk (fájl:sor, szó szerint) | Teendő |
|---:|---|---|---|
| 1 | A ▾ gomb a **14 rekordos** `0x00733480` legördülőt nyitja, Flat/Tree és gyökértétel nélkül (`0x005e2096`; `0xd6efd0`, darab 14: `0x0073397f`). | `PicasaViewMenu.qml:15`: `folderViewMenu.popup(anchorItem, 0, anchorItem.height)`; ez a menüsáv almenüje, benne `PicasaFolderViewMenu.qml:54-55`: `objectName: "menuViewFlatFolderView"` / `text: qsTr("&Flat Folder View")`. | **J1**: a ▾ gomb külön legördülőt nyisson, a 2.1 tábla szerinti szerkezettel. |
| 2 | A menüsávi Mappanézet almenü **13 rekord**: nincs felső szintű gyökértétel és nincs Emberek-rendezés (`0xd6e168 = 0xd`, `0x0055ac84`; felvétel #41). | `PicasaFolderViewMenu.qml:98`: `objectName: "menuViewRootMyComputer"` (a négy gyökértétel a 98-152. sorban, elválasztó: 153); `:242`: `objectName: "menuViewSortPeopleByName"` (három Emberek-tétel a 242-276. sorban, elválasztó: 277). | **J2**: töröld a felső szintű négy gyökértételt és a három Emberek-tételt a menüsávi almenüből. |
| 3 | A Shortcuts-gyerekek sorrendje: **Desktop · My Documents · My Pictures · elválasztó · My Computer** (`0xd6de30`, `0x0055a5ce`; `0xd6ef68`, `0x007338d0`). | `PicasaFolderViewMenu.qml:285`: `objectName: "menuViewShortcutMyComputer"` az első, majd `:298` MyPictures, `:311` MyDocuments, `:324` Desktop; elválasztó nincs. | **J2**: igazítsd az eredeti sorrendhez és elválasztóhoz. |
| 4 | A ▾ legördülő sorrendje: Date, **Recent, Size, Name**, Reverse (`0xd6efd0`-`0xd6f020`). | `FolderListContextMenu.qml:67`, `:79`, `:91`, `:103`: `Sort by &Date`, `Sort by &Name`, `Sort by &Size`, `Sort by &Recent Changes`. | **J3**: Date, Recent, Size, Name, Reverse. |
| 5 | A blokkok sorrendje: rendezés, Emberek, **Shortcuts ▸**, majd **Show Thumbnails**, **Simplified** (rekord 10, 12, 13). | `FolderListContextMenu.qml:185`: `objectName: "folderListMenuSimplifiedTree"` (előbb), `:198`: `objectName: "folderListMenuShowThumbnails"`, a Shortcuts almenü az utolsó (`:224`: `title: qsTr("&Shortcuts")`). | **J3**: Shortcuts ▸ előre, Show Thumbnails az Egyszerűsített elé. |
| 6 | **Top 10 lapos nézetben szürke**, az **Indexképek fanézetben szürke** (`0x005e25a4`-`0x005e25b9`, `0x005e2596`; felvétel #26). | `FolderListContextMenu.qml:165-166`: `objectName: "folderListMenuSortPeopleByTopList"` / `text: qsTr("Sort People by Top &10")` és `:198`: `objectName: "folderListMenuShowThumbnails"`: egyiknek sincs `enabled` tulajdonsága. `PicasaFolderViewMenu.qml:353`: `enabled: !folderViewMenu.treeMode` az Indexképeknél viszont megvan, a Top 10-nél (`:266`) nincs. | **J3**: `enabled` mindkét tételre, mindkét menüben (a Top 10 a menüsáv almenüjében a J2 után kikerül). |
| 7 | **Mappa ▸ Rendezés**: négy tétel, egyszeri átrendezés, nincs pipa és nincs tárolt mód (`0xd6e170`, `0x0055af63`; `0x005e5ce0`). | `PicasaFolderMenu.qml:69`: `controller.setFolderSort("date")`; `:127`: `controller.toggleFolderSortReverse()`; a tételek `checkable`-ek, a `folderSort` tartós (`controller_folder_view_mixin.py`: `setValue("view/folderSort", mode)`). | **J4**: a négy eredeti tétel hívja a `sortFolderBy`-t az aktuális mappára. |
| 8 | A hasáb rendezésének **alapértéke** dátum, a fordítás külön tárolódik, szempontváltáskor megmarad (`0x004a196e`, `0x004b07cc`). | `controller_folder_view_mixin.py:44`: `return self._get_settings().value("view/paneSort", "date")`; `setPaneSort` a megfordításhoz nem nyúl. | Egyezik. |
| 9 | Irány: dátum, legutóbbi, méret csökkenő, név növekvő (`0x004a7890`). | `model_helpers.py:119`: `return sort_mode != "name"` | Egyezik. |
| 10 | Indexkép felirata: öt tétel, **&None** `&Nincs`. | `PicasaViewMenu.qml:478`: `text: qsTr("None")` | **J5**: `qsTr("&None")`. |

## 7. Javasolt fejlesztői jegytörzsek

A J1-J3 és a J5 ugyanazt a három QML-fájlt és a `picasapy_hu.ts`-t érinti (forró fájl: a `.ts`), ezért **egy session vigye mindet egyben**. A J4 a `PicasaFolderMenu.qml`-t és a controllert érinti, külön vihető.

### J1. A ▾ ("View options") gomb a saját legördülőjét nyissa

- **Eredeti:** `0x00733480` (14 rekord, `0xd6efd0`, `push 0xe` `0x0073397f`), `0x005e2000` (kezelő, `call 0x733480` `0x005e2096`), felvétel #26.
- **Mit ad ma:** a ▾ gomb a menüsáv `PicasaFolderViewMenu`-jét nyitja (`PicasaViewMenu.qml:14-15`), ezért a legördülőben Egyszerű/Fa nézetváltó és négy felső szintű gyökértétel is van, amit az eredeti ▾ legördülő nem tartalmaz.
- **Teendő:** a ▾ gomb a 2.1 táblának megfelelő legördülőt nyissa: Date · Recent · Size · Name · Reverse | Emberek ×3 | Shortcuts ▸ | Show Thumbnails · Simplified, az elválasztókkal. A tételek feliratai és a pipák a meglévő `FolderListContextMenu.qml` tételeinek felelnek meg ("Sort by &Date"). A menüsávi almenü marad a menüsávban.
- **Kész, ha:** a ▾ gomb legördülője nem tartalmaz Flat/Tree tételt és felső szintű gyökértételt; a tételek sorrendje és elválasztói a 2.1 táblával azonosak; a #26 felvételhez hasonló képkockán (lapos nézet, dátumrendezés) a Top 10 szürke.

### J2. A menüsávi Nézet ▸ Mappanézet almenü a 13 rekordos szerkezet szerint

- **Eredeti:** `0xd6e158` fejléc, darab `0xd` (`0x0055ac84`), Shortcuts gyerekek `0xd6de30` × 5 (`0x0055a5ce`, `0x0055a335`), felvétel #41.
- **Mit ad ma:** a menüsávi almenüben a Flat/Tree után négy felső szintű gyökértétel áll (`PicasaFolderViewMenu.qml:98-152`) és a rendezések után három Emberek-tétel (`:242-276`); a Shortcuts almenü fordított sorrendű és elválasztó nélküli (`:285`, `:298`, `:311`, `:324`).
- **Teendő:** töröld a felső szintű négy gyökértételt és az utánuk álló elválasztót (98-153. sor), töröld a három Emberek-tételt és elválasztóját (241-277. sor), a Shortcuts almenüt rendezd Desktop · My Documents · My Pictures · elválasztó · My Computer sorrendbe. A Windows-specifikus három tétel a PicasaPy-ban megmaradhat a Linux megfelelőikkel (`setViewRoot` tokenek változatlanok), a döntés a Shortcuts almenü két menüben azonos tartalma.
- **Kész, ha:** a menüsávi almenü 13 elemű (2 nézet, elválasztó, 5 rendezés, elválasztó, Shortcuts, elválasztó, Show Thumbnails, Simplified), a #41 felvétel minden tételével azonos sorrendben.

### J3. A ▾ legördülő (FolderListContextMenu) sorrendje és tiltásai

- **Eredeti:** `0xd6efd0`-`0xd6f0d4` rekordsorrend, `0x005e2596`, `0x005e25a4`-`0x005e25b9`, felvétel #26.
- **Mit ad ma:** a sorrend Date · Name · Size · Recent (`FolderListContextMenu.qml:67-103`), az Egyszerűsített az Indexképek előtt áll (`:185`, `:198`), a Shortcuts az utolsó blokk (`:224`), a Shortcuts-ban csak a Desktop (`:226`); sem a Top 10, sem az Indexképek nem tiltható (`:165`, `:198`).
- **Teendő:** Date · Recent · Size · Name · Reverse sorrend; a blokksorrend Shortcuts ▸, majd Show Thumbnails, Simplified; a Top 10 `enabled: treeMode` (lapos nézetben szürke), az Indexképek `enabled: !treeMode` (fanézetben szürke); a `treeMode` a `PicasaFolderViewMenu.qml:15-17` mintájára a `folderViewCtl.treeView`-ból jön.
- **Kész, ha:** egy lapos nézetű és egy fanézetű renderelt próba a tiltásokat és a sorrendet méri (nem csak a tulajdonságokat olvassa), a #26 felvétel tételsorrendjével egyező képkockával.

### J4. A Mappa ▸ Rendezés négy tétele egyszeri átrendezés legyen

- **Eredeti:** `0xd6e170` (4 gyerek, `0x0055af63`, `0x0055af40`), `0x005e5ce0`, `album-sorrend.md` 2.4.
- **Mit ad ma:** `PicasaFolderMenu.qml:62-127` pipás (`checkable`), tartós `folderSort` beállítást állít a rács mappa-blokkjainak sorrendjére (`controller.setFolderSort("date")`, `controller.toggleFolderSortReverse()`), miközben ugyanennek a négy parancsnak a mappasor-jobbklikkes párja a mappa képeit rendezi át egyszer (`FolderPaneMenus.qml:382`: `controller.sortFolderBy(folderContextMenu.folderPath, mode)`). Egy parancskészlet két belépési pontja két különböző hatású.
- **Teendő:** a Name, Date, Size és Reverse order tétel hívja a `sortFolderBy(bar.currentFolder, mód)`-ot (albumnézetben az album sorrendjét, `album-sorrend.md` 4.1), `checkable` nélkül. A **"Recent &changes" saját tétel marad** (`docs/decisions/vedett-sajat-funkciok.md`: védett), a viselkedése és a `sajat: true` jelölése nem változik. Az eredeti tételek kikötése után a `folderSort` csak ehhez a tételhez tartozik, ezért a rács mappa-blokkjainak sorrendje a bal hasáb rendezését (`paneSort`) kövesse az eredeti szerint (C2 méri, addig a `folderSort` a saját tétel mögött maradjon).
- **Kész, ha:** a Mappa ▸ Rendezés négy tétele után a kijelölt mappa képsorrendje megváltozik (a `.picasa.ini` kézi sorrendje frissül), a menü újranyitásakor egyik tételen nincs pipa, és egy Shift nélküli és egy fordított hívás a mappasor-jobbklikkes úttal azonos eredményt ad.

### J5. Az Indexkép felirata ▸ None tétel mnemonikja

- **Eredeti:** `eMenuView::ID_CAPNONE`, szövegtár: `&None`, `&Nincs`.
- **Mit ad ma:** `PicasaViewMenu.qml:478`: `text: qsTr("None")`, a mnemonik hiányzik (a másik négy tételnek megvan).
- **Teendő:** `qsTr("&None")` és a magyar `&Nincs` a `picasapy_hu.ts`-ben (a "None" forrásszöveg másik előfordulásait ne érintse).
- **Kész, ha:** a menü Alt+N mnemonikot ad a tételnek, és a magyar felirat `&Nincs`.

## 8. Nyitott kérdések mérlege, a Colab-lépéssorok és a mérés eredménye

```
Nyitott kérdések: 1 nyílt (C5c) · 10 lezárva (C1-C5 mérve) · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

A C1-C4 teljesen lezárult. A C5 két fele (nem a váltás pillanatában ír; kényszerített leállás után az alapérték áll) mért, a harmadik fele (szabályos kilépéskor ír-e) statikusan erős, de nem mért: ez a **C5c**, felvehető Colab-feladat, a lépéssora a "Következő mérés" alszakaszban van. Az alábbi C1-C5 leírások a lefuttatott feladatok tervei; az eredmény a "Mérési eredmény (Colab)" alszakaszban áll.

A hat feladat (job-801 ... job-806) az eredeti Picasa Colab-végrehajtójával futott, `idorend` mintakészlettel (több mappa, különböző dátumok), tiszta profilon.

- **C1. Van-e jobbklikk-menü a hasáb üres részén az eredetiben?** Lépések: tiszta profil, mintakészlet betöltve; jobb gomb a bal hasáb üres részén (a mappalista alatt), képernyőkép; ha nyílik menü, a tételek listája. Eredmény: ha nincs, a `FolderPane.qml:604-607` kezelő hamis belépési pont, a J1 ▾ legördülője az egyetlen belépés. Fok jelenleg: feltételes.
- **C2. A rács mappa-blokkjainak sorrendje követi-e a hasábét?** Lépések: ▾ ▸ Sort by Name, majd Sort by Size, majd Reverse sort; minden lépés után egy képernyőkép a bal hasábról és a Könyvtárnézet blokk-fejlécekről (mappanevek sorrendben). Ebből dől el a `folderSort` sorsa (J4) és a `thumbui/datesort`/`namesort` gombok léte.
- **C3. A ▾ tiltások fanézetben:** lépések: fanézet (Nézet ▸ Mappanézet ▸ Fanézet), ▾ megnyitása, képernyőkép. Várt: Top 10 engedélyezett, Indexképek szürke (statikusan igazolt, `0x005e2596`, `0x005e25a4`-`0x005e25b9`).
- **C4. A Shortcuts almenü tartalma és szürke tételei:** lépések: ▾ ▸ Gyorsbillentyűk, képernyőkép; várt: Desktop, My Documents, My Pictures, elválasztó, My Computer (2.1), a hiányzó mappák szürkén.
- **C5. Mikor kerül a registrybe a `datesort`, `peoplesort`, `albumlistflip`?** Lépések: ▾ ▸ Sort by Name, majd Reverse sort; azonnal `wine reg query "HKCU\Software\Google\Picasa\Picasa2\Preferences" /v datesort` és `/v albumlistflip` (az útvonal a `0x006e3990` regisztráló-lap szerinti, Wine-profilonként ellenőrizendő), majd a Picasa szabályos bezárása és megismételt lekérdezés, végül újraindítás és a hasáb sorrendje. Eldönti az 4. szakasz utolsó sorát és a PicasaPy `QSettings` mentési időpontját.

A lezárt kérdések: a ▾ tábla (2.1), a menüsávi tábla (2.2), a tiltások (3.2), a rendezés iránya és a megjegyzett állapot kulcsai (4.), a gyorsbillentyű hiánya (5.), és a Colab-mérés öt kérdése (lent).

### Mérési eredmény (Colab)

A feladatok 2026-11-21-én futottak az eredeti Picasa 3.9.141.259-cel (Wine alatt, 1280x1024-es képernyő), tiszta profilon, `idorend` mintakészlettel. A könyvtárban öt mappa van, öt különböző évből: `PicasaTeszt` (24 kép, 2026), `2021_eltero_fajlido` (2), `2019_marcius` (7), `2014_november` (3), `2009_majus` (1). Kezdőállapot (job-802 4. kép): lapos nézet, dátumrendezés, évszám-fejlécekkel.

Olvasási kulcs: a felmérő minden lépés ELŐTT képet ad, ezért egy lépés utáni állapot a következő sorszámú kép. A képek a teljes képernyőt mutatják, a legördülők és az almenük is látszanak rajtuk (a nyitott legördülő az állapotkivonatot is megváltoztatja: job-802 5-6. lépés), tehát egy menü hiánya a képen valódi hiány. Az "Eredeti | Nálunk" idézetek a **mai main** állapotát mutatják (a #7340 és #7341 után), nem a 6. szakasz régi sorait.

| Kérdés | Döntés | Fok | Fejlesztői teendő |
|---|---|---|---|
| C1 | A hasáb üres részén **nincs** jobbklikk-menü. | mért | J6: a PicasaPy kezelője hamis belépési pont. |
| C2 | A rács mappa-blokkjainak sorrendje **követi** a hasábét; független rács-rendezés és dátum/név gomb nincs; a megfordítás szempontváltáskor megmarad. Új eltérések: a Recent Changes fejlécei "Updated <Hónap> <Év>" alakúak, és a lista első sora fölött sosincs fejléc. | mért | A #7341 egyezik; J8, J9. |
| C3 | Lapos nézetben a Top 10 szürke, fanézetben a Show Thumbnails szürke. | mért | Egyezik (#7340). |
| C4 | A Shortcuts sorrendje és elválasztója egyezik; a **Desktop és a My Pictures szürke** lehet, a My Documents és a My Computer sosem. | mért + erős (statikus) | J7. |
| C5 | A rendezés **nem a váltás pillanatában** kerül a registrybe; kényszerített leállítás után az alapérték áll vissza; a szabályos kilépéskor írás statikusan várható, nem mért. | mért (két fele) · erős (a harmadik) | Nincs fejlesztői jegy; C5c mérés. |

#### C1. Van-e jobbklikk-menü a hasáb üres részén? Nincs (job-801, 12 kép)

| Kép | Mit mutat |
|---|---|
| 04 | Alapállapot: az utolsó mappasor (`2009_majus`, y=391) alatt a hasáb szürke, üres része (y=405-910). |
| 05, 06 | Jobb gomb a (120,700) ponton: közvetlenül és 2 mp múlva sem nyílik menü, a hasáb és a rács változatlan. |
| 09, 10 | Jobb gomb a (120,850) ponton: menü nincs; csak a fókusz kerül a keresőmezőbe (a hasáb kijelölése szürkére vált). |
| 12 | Escape után ugyanaz az állapot. |

A 2-10. lépés állapotkivonata azonos, tehát semmi sem nyílt meg. **Következtetés:** az eredeti nem nyit menüt a hasáb üres részén, a PicasaPy `FolderPane.qml:604-607` kezelője hamis belépési pont. Korlát: lapos nézetben, dátumrendezéssel mértem; fanézetben nem, de a bináris szerint az `AlbumList` tábla egyetlen felhasználója a ▾ kezelő (2.1), tehát ott sincs más belépés.

#### C2. A rács mappa-blokkjainak sorrendje követi-e a hasábét? Igen (job-802, 29 kép)

| Kép | Állapot | A hasáb sorrendje (fentről lefelé) | Fejlécek a hasábban |
|---|---|---|---|
| 04 | Alap: Date, csökkenő | PicasaTeszt, 2021_eltero_fajlido, 2019_marcius, 2014_november, 2009_majus | évszám: 2021, 2019, 2014, 2009; a `PicasaTeszt` fölött nincs |
| 06 | ▾ nyitva | Date és People by Name pipával, Top 10 szürke, 14 rekord a 2.1 szerint | |
| 08 | Sort by Name | 2009_majus, 2014_november, 2019_marcius, 2021_eltero_fajlido, PicasaTeszt | nincs |
| 15 | Sort by Size | PicasaTeszt (24), 2019_marcius (7), 2014_november (3), 2021_eltero_fajlido (2), 2009_majus (1) | nincs |
| 19 | Reverse sort (a Size után) | 2009_majus (1), 2021_eltero_fajlido (2), 2014_november (3), 2019_marcius (7), PicasaTeszt (24) | nincs |
| 25 | Recent Changes (a megfordítás megmaradt) | 2009_majus, 2014_november, 2019_marcius, 2021_eltero_fajlido, PicasaTeszt | "Updated November 2014", "Updated March 2019", "Updated August 2021", "Updated November 2026"; a `2009_majus` fölött nincs |
| 29 | Date (a megfordítás megmaradt) | ugyanaz a növekvő sorrend | évszám: 2014, 2019, 2021, 2026; a `2009_majus` fölött nincs |

**Következtetések:**

1. **A rács követi a hasábot.** A 15. képen a `PicasaTeszt` blokk alatt a rácson a `2019_marcius` blokk következik (a dátumrendezésnél, a 04. képen a `2021_eltero_fajlido`), vagyis a blokksorrend a Size sorrendet követi. A 08., 19., 25., 29. képen a rács görgetősávjának csúszkája az alsó végen áll, a `PicasaTeszt` blokk a rács végén, ahogy a hasábban is utolsó. Független rács-rendezés tehát nincs: a `folderSort` mint eredeti funkció nem létezik (a védett saját "Recent &changes" tétel a Mappa menüben marad, de nem az eredeti része). A PicasaPy ezt a #7341 óta így csinálja: `controller_folder_view_mixin.py:194-195`: `# #7341: a bal hasáb és a rács mappa-blokkjai a `paneSort`-ot` / `# követik.`, és `:200-201`: `self.paneSort,` / `self.paneSortReverse,`.
2. **A megfordítás megmarad a szempont váltásakor** (19 → 25 → 29: mind növekvő). Egyezik a 4. szakasz sorával.
3. **Fejlécek:** Date: évszám; Recent Changes: "Updated <Hónap> <Év>"; Name és Size: nincs fejléc. A PicasaPy a Recent Changes-nél is évszámot ír (J8).
4. **Az első csoport fölött sosincs fejléc** (04., 25., 29. kép és job-806 18. kép). A tulajdonosi felvétel (`Képernyőkép 2026-07-18 150933`) ezzel egyezik: a dátum nélküli `HS logo` az első sor, fejléc nélkül, a `2024` fejléc csak utána jön. A korábbi megfigyelés ("ha minden mappa azonos évű, nincs fejléc", `ui-audit-mainwindow.md` 1.1) ennek a szabálynak a speciális esete (J9).
5. **A `thumbui/datesort` és `thumbui/namesort` gomb nincs** a futó eredeti könyvtár-eszköztárán (Import, a lapos/fa gombpár és a ▾ áll a bal oldalon; mind a 29 képen). A PicasaPy-ban sincs rájuk hivatkozás: egyezik, nincs teendő.

#### C3. A ▾ tiltásai lapos és fanézetben (job-803, 16 kép)

| Kép | Mit mutat |
|---|---|
| 08 | Lapos nézet, ▾ nyitva: **Sort People by Top 10 szürke**; Show Thumbnails in Library és Simplified Tree View engedélyezett; Date és People by Name pipával. |
| 12 | A fa gomb után: fanézet (`Folders (6)`, gyökér `My Computer (37)`, alatta a fa). |
| 14 | Fanézet, ▾ nyitva: **Show Thumbnails in Library szürke**; Top 10 és Simplified Tree View engedélyezett. |

**Következtetés:** a statikus lelet (`0x005e2596`, `0x005e25a4`-`0x005e25b9`) pontosan igaz: a Top 10 lapos nézetben szürke, az Indexképek megjelenítése fanézetben szürke. A PicasaPy egyezik: `FolderListContextMenu.qml:179`: `enabled: menu.treeMode`; `:262`: `enabled: !menu.treeMode`; a `treeMode` mindkét példányban kötött (`PicasaViewMenu.qml:35`, `FolderPaneMenus.qml`). A renderelt egyezést ez a kör nem mérte; a tulajdonság-egyezés a kódból áll.

#### C4. A Shortcuts almenü tartalma és szürke tételei (job-804, 20 kép)

| Kép | Mit mutat |
|---|---|
| 15 | A ▾ nyitva, a 9. kijelölhető tétel (Shortcuts) kijelölve. |
| 16, 17 | Jobbra nyíl után az almenü: **Desktop (szürke) · My Documents (engedélyezett) · My Pictures (szürke) · elválasztó · My Computer (engedélyezett)**; a mnemonikok: D, My Do**c**uments, P, C. |
| 20 | Escape után bezárva. |

A ▾ legördülő (job-802 06. kép, job-804 15. kép) a 2.1 tábla mind a 14 rekordját mutatja, a mért sorrendben és elválasztókkal.

**A szürkítés szabálya (új, statikus, erős).** A `0x004f7e40` igazat ad, ha a rendszermappa útvonala kis/nagybetűre érzéketlen **előtagja** a mappalista valamely elemének: a lista a `this+0x3f0` tömb, az elemek közül a `[+0x18]` 1-es és 5-ös típusúak kimaradnak, a `[+0x1d]` jelzőnek nem nullának kell lennie, az összevetés a `0x00987030`. Az `EnableMenuItem` jelzője az eredmény tagadása: `0x005e2554` `sete cl` (My Pictures, `0x9e3a`, a `0x009966a0` = `CSIDL_MYPICTURES` eredményéből), `0x005e2562` `sete dl` (a `0x00996230` = `CSIDL_PERSONAL` eredménye, de a `0x9dba` Desktop-azonosítóra megy), `0x005e2574` `sete al` (a `0x00996b90` = `CSIDL_DESKTOP` eredménye, szintén `0x9dba`, ezért ez írja felül az előzőt). Tehát: **Desktop és My Pictures akkor engedélyezett, ha a könyvtár valamelyik mappája a megfelelő rendszermappa alatt van; a My Documents és a My Computer sosem tiltott.** A mintakészletben egyetlen mappa van (a teszt gyökere), ami sem a Desktop, sem a My Pictures alatt nincs: a mért kép (Desktop és My Pictures szürke, My Documents engedélyezett) pontosan ezt adja. Nincs mérve a pozitív eset (egy mappa a Pictures alatt), és a `this+0x3f0` lista azonosítása (figyelt mappák vagy a betöltött mappafa) nyitott; a két lista a mintában megegyezik.

**Következtetés:** a sorrend és az elválasztó egyezik a PicasaPy-val; a tiltás hiányzik (J7, #7350). A korábbi "Windows-specifikus, nincs teendő" (3.2) megdőlt.

#### C5. Mikor kerül a registrybe a `datesort`, `peoplesort`, `albumlistflip`? (job-805, job-806)

**C5a (job-805, 16 kép és `registry__picasa.reg`).** A 08. kép: a Sort by Name után a hasáb név szerint növekvő (2009_majus ... PicasaTeszt); a 12. kép: a Reverse sort után név szerint csökkenő, fejlécek nélkül; a 16. kép: +40 mp után a hasáb változatlan. A registry-kivonat (user.reg formátumú, kulcsonként időbélyeges kimenet) `Picasa2\Preferences` kulcsa 26 értéket tartalmaz (többek közt `CleanExit`, `LastABPromo`, `lastdesktop`, `Picasa Notifier`), **a `datesort`, `peoplesort` és `albumlistflip` nincs közöttük**, pedig a kulcs időbélyege (06:26:01 UTC) a Picasa első indítása (06:24:50 UTC) után 71 mp-cel van, vagyis a kulcs a futás közben is kapott írást. **Következtetés: a rendezés a váltás után 40 mp-cel sem szerepel a registryben** (a feladat tervezésekor feltételezett ~30 mp-es Wine-mentési periódus kisebb a 40 mp-nél; a kivonat a fájlba már kiírt állapotot mutatja).

**C5b (job-806, 18 kép és `registry__picasa.reg`).** A 12. kép: Name + Reverse után a hasáb név szerint csökkenő (PicasaTeszt, 2021_eltero_fajlido, 2019_marcius, 2014_november, 2009_majus, fejlécek nélkül). A 13. kép: fekete képernyő (a Picasa leállítva). A 15. kép: a Picasa indulóképe. A 18. kép: az újraindított Picasa hasábja **dátum szerint csökkenő, évszám-fejlécekkel**, vagyis az alapállapot; a rendezés és a megfordítás elveszett. A registry-kivonat itt sem tartalmazza a három kulcsot. **Korlát:** a Colab `picasa leallit` lépése a gépen `wineserver -k`, tehát **kényszerített leállítás**, nem a Fájl ▸ Kilépés kapuja (`WM_SYSCOMMAND` `SC_CLOSE`, `0x005e4d87`); ezért a C5b a szabályos kilépés mentéséről nem dönt.

**Statikus lelet (erős).** A `0x004a3790` ír: a `datesort` a `[esi+0xd8]`-ből (`0x004a379e`, `push 0xc83078` `0x004a37a5`), a `peoplesort` a `[esi+0xdc]`-ből (`0x004a37e8`, `push 0xc83084` `0x004a37ee`), az `albumlistflip` a `[esi+0x165]`-ből (`0x004a3835`, `push 0xc83090` `0x004a383c`). Egyetlen közvetlen hívója a `0x004a35d3`, a `0x004a35d0` burkolóban (`push esi` / `mov esi, ecx` / `call 0x4a3790` / `test byte ptr [esp+8], 1` / `call 0x97caf0`: a törlő destruktor alakja), amelyre egyetlen hivatkozás van a teljes képen: a `.rdata` `0x00c8368c` címe (vtábla-slot). Az olvasó (`0x004a1560`) indításkor fut (`0x0040300d`). Tehát a rendezési állapot **az objektum megsemmisülésekor** íródik, indításkor olvasódik. A vtábla-slot azonosítása a burkoló alakjából következik; hogy a destruktor a szabályos kilépéskor tényleg lefut, nincs végigkövetve.

**Következtetés (C5):** a rendezés és a megfordítás **nem a váltás pillanatában** kerül a registrybe (mért), kényszerített leállítás után az alapérték áll (mért), a szabályos kilépéskor írás **várható** (statikus), de nem mért: ez a C5c. **PicasaPy:** `controller_folder_view_mixin.py:58`: `self._get_settings().setValue("view/paneSort", mode)` a váltáskor ír. Szabályos kilépés után a két viselkedés a várakozás szerint egyezik; összeomlás vagy kényszerített leállás után az eredeti elveszti a választást, a PicasaPy megtartja: ezt **nem másoljuk** (az elvesztés hiba, nem funkció). Fejlesztői jegy a C5-ből nincs.

### Javasolt fejlesztői jegytörzsek a mérésből (J6-J9)

A J8 és a J9 ugyanazt a két fájlt érinti (`folder_list_model.py`, `model_helpers.py`) és a hozzájuk tartozó teszteket, ezért **egy session vigye mindkettőt**. A J6 és a J7 a QML-t érinti; a J7 a `picasapy_hu.ts`-t nem, mert nem ad új szöveget.

#### J6. A hasáb üres részének jobbklikkje ne nyisson menüt

- **Eredeti:** nincs menü a hasáb üres részén (Colab job-801, 05-06. és 09-10. kép); az `AlbumList` menü egyetlen belépése a ▾ gomb (`0x005e2000`, hívója `0x005d9cc0`).
- **Mit ad ma:** `FolderPane.qml:603-607`: `TapHandler {` / `objectName: "folderPaneContextMenuHandler"` / `acceptedButtons: Qt.RightButton` / `gesturePolicy: TapHandler.ReleaseWithinBounds` / `onSingleTapped: pane.openFolderListContextMenu()`; a függvény `FolderPane.qml:373`: `function openFolderListContextMenu() {`.
- **Teendő:** töröld a kezelőt (a fölötte álló #422-megjegyzéssel együtt) és az `openFolderListContextMenu` függvényt; mivel más hívója nincs, a `FolderPaneMenus.qml` `folderListContextMenu` példányát és álnevét (`:20`, `:241`) is. A ▾ gomb legördülője (`PicasaViewMenu.toolbarFolderOptionsMenu`) marad. Az átírandó tesztek a törölt belépésre épülnek: `test_stage3_menu_wiring_422.py`, `test_racs_maradek_valodi_5150_p.py:203`, `test_menu_radio_pipa_1468.py:469-484`, `test_mappanezet_menu_1454.py:383` (a ▾ példányt vizsgálják, a jobbklikk-próba azt, hogy nem nyílik menü).
- **Kész, ha:** renderelt próbában a jobb kattintás a hasáb üres részén (lapos és fanézetben) nem nyit menüt, és a hasáb képkockája változatlan; a mappasor, az Albums és a People sor jobbklikk-menüje (a szomszéd) és a ▾ legördülője változatlan. A próba a nyitást méri, az eredeti képével való vizuális egyezést nem.

#### J7. A Shortcuts almenü Desktop és My Pictures tétele legyen tiltható

- **Eredeti:** `0x005e2558`, `0x005e256a`, `0x005e257c` `EnableMenuItem(..., (eredmény == 0))`; a `0x004f7e40` igaz, ha a rendszermappa útvonala előtagja a mappalista valamely elemének (C4 statikus lelet). Mért: Colab job-804 17. kép: Desktop és My Pictures szürke, My Documents és My Computer engedélyezett.
- **Mit ad ma:** `FolderListContextMenu.qml:203-204`: `text: qsTr("&Desktop")` / `checkable: true`; `:229-230`: `text: qsTr("My &Pictures")` / `checkable: true`; `PicasaFolderViewMenu.qml:193-195`: `objectName: "menuViewShortcutMyPictures"` / `text: qsTr("My &Pictures")` / `checkable: true`. Egyiknek sincs `enabled` tulajdonsága, mind engedélyezett.
- **Teendő:** a Desktop és a My Pictures tétel `enabled`-je mindkét menüben (`FolderListContextMenu.qml`, `PicasaFolderViewMenu.qml`) legyen igaz, ha a könyvtár legalább egy mappájának útvonala a megfelelő helyi gyökér alatt van (a gyökerek: `folder_hierarchy_controller.py`, `_RENDSZERMAPPAK`: `DesktopLocation`, `PicturesLocation`). A My Documents és a My Computer mindig engedélyezett (az eredetiben a My Documents hibából, a Desktop-azonosító kétszeri küldése miatt sosem tiltott; a mért kép ezt mutatja, a viselkedést megtartjuk). Az eredeti nyers előtag-összevetést végez; a PicasaPy útvonal-határon (komponens szerint) vessen össze, és ezt az egyetlen szándékos eltérést a jegy mondja ki.
- **Kész, ha:** renderelt próbában két könyvtárral: az egyikben van mappa a Pictures alatt (My Pictures engedélyezett), a másikban nincs (szürke, mint a job-804 17. képen); a Documents és a My Computer mindkettőben engedélyezett. **Fok:** a szabály statikus és egy negatív mintán igazolt; a pozitív eset (mappa a Pictures alatt) és a lista azonosítása nincs mérve, ezt a jegy kimondja.

#### J8. Recent Changes rendezésnél "Updated <Hónap> <Év>" fejlécek

- **Eredeti:** a hasáb Recent Changes rendezésekor a csoportfejlécek a változtatás hónapját írják: "Updated November 2014", "Updated March 2019", "Updated August 2021", "Updated November 2026" (Colab job-802 25. kép); dátumrendezésnél évszám, névnél és méretnél nincs fejléc.
- **Mit ad ma:** `folder_list_model.py:200-201`: `if sort_mode in ("date", "changed"):` / `lathato = _with_year_separators(rows)`, vagyis a `changed` mód is a mappa dátumának **évszámát** írja; a teszt ezt rögzíti: `tests/app/test_folder_sort_split.py:197-200`: `def test_changed_view_keeps_them(self, controller):` / `# a „legutóbbi változtatás" is dátum-alapú nézet` / `controller.setPaneSort("changed")` / `assert "year" in self._kinds(controller)`.
- **Teendő:** `changed` módban a fejléc a mappa változtatási idejének hónapját mutassa "Updated <Hónap> <Év>" alakban (a sor `_change` mezője az `rows` felépítésekor már rendelkezésre áll). Két részlet a jegy első lépése: (1) a magyar sablon a szövegtárból (az angol sablon kulcsa nincs azonosítva), (2) az azonos hónapra eső két mappa egy csoportot kap-e: a mintában négy különböző hónap volt, a hónap szemcséje feltevés; ha a szövegtár nem dönti el, kétmappás, azonos hónapú Colab-mintával kell mérni (C6, a jegy része).
- **Kész, ha:** egy renderelt próba a Recent Changes rendezésnél a job-802 25. képpel egyező fejléc-sorrendet és -feliratot ad (angol nyelven), a `test_changed_view_keeps_them` a fejléc új alakját rögzíti.

#### J9. A lista első sora fölött ne legyen évszám-fejléc

- **Eredeti:** évszám-fejléc csak akkor áll, ha az előző sor más évű vagy dátum nélküli; a lista első sora fölött soha nincs (Colab job-802 04. és 29. kép, job-806 18. kép). A tulajdonosi felvétel (150933): a dátum nélküli `HS logo` az első sor fejléc nélkül, utána jön a `2024`.
- **Mit ad ma:** `model_helpers.py:168-169`: `if year and year != last_year:` / `rows.append(("year", year, "", 0, False, False))`, a `last_year` kezdőértéke `None`, ezért az első dátumos sor fölé is fejléc kerül; a teszt ezt rögzíti: `tests/app/test_models.py:55`: `assert model.data(model.index(0, 0), FolderListModel.KindRole) == "year"`.
- **Teendő:** az első sor fölé ne kerüljön fejléc (a `last_year` kezdőértéke az első sor éve); dátum nélküli első sor után az első dátumos csoport kap fejlécet (150933). A homogén-év külön ág (`len(distinct_years) <= 1 and all(years)`) az új szabály következménye, kivehető. Átírandó: `tests/app/test_models.py:55` és a `:85-133` közötti sorrend-assertek.
- **Kész, ha:** a Colab 04. kép mintáján (öt mappa, öt év, dátumrendezés) a hasáb első sora a `PicasaTeszt`, fejléc nélkül, utána a `2021` fejléc; a 150933 mintán a `HS logo` után a `2024`; a három eset renderelt próbával (nem csak sorlistával) ellenőrzött.

### Következő mérés: C5c (szabályos kilépés után mentődik-e)

Felvehető Colab-feladat, a C5b mása, a `picasa leallit` helyett a Fájl ▸ Kilépés menüvel (a menüsor és a Exit tétel koordinátája a felület-térképből: File `[14,29]`, Exit `[40,409]`, azonosító `0x9c41`, nem törlő). Kimenet: `kepernyokep,registry`, `--perc 12`, `--extra '{"mintakeszlet": "idorend"}'`.

```json
[
 {"var": 10}, {"var": 10}, {"var": 10},
 {"kattint": [237, 58]}, {"var": 1}, {"billentyu": "n"}, {"var": 2},
 {"kattint": [237, 58]}, {"var": 1}, {"billentyu": "v"}, {"var": 2},
 {"kattint": [14, 29]}, {"var": 1}, {"kattint": [40, 409]}, {"var": 10},
 {"picasa": "indit"}, {"var": 10}, {"var": 10}, {"var": 10}
]
```

A Fájl menüt megnyitó kattintás utáni kép (13.) mutatja, hogy az Exit a `[40,409]` pontnál áll-e. **Várt eredmény, ha a statikus olvasat igaz:** az újraindítás utáni registry-kivonatban a `datesort` 2 és az `albumlistflip` 1, és a hasáb név szerint csökkenő sorrendben áll. **Ha nincs bennük:** az eredetiben a rendezés egyáltalán nem tartós, és a PicasaPy `view/paneSort` tartós mentésének nincs eredeti megfelelője (új döntés kell: megtartjuk-e). Mindkét kimenetel következtetés, a kör nem parkol.

## 9. Helyesbítés a korábbi lapokhoz

A `picasa-menu-parancsok-viselkedes.md` 36.2 pontja szerint a `[edi+0x34a4]` "ebben a buildben mindig 0: a teljes fájlban egyetlen írása van, a konstruktorban". Ez **megdőlt**: a `0x005e2637` `add dword ptr [esi+0x34a4], 1` és a `0x005e2659` `add dword ptr [esi+0x34a4], -1` a ▾ legördülő `TrackPopupMenu` hívását keretezi. A korábbi pásztázás csak a `mov imm` és `mov reg` írásalakokat kereste, az `add` formát nem. A mező tehát egy **"legördülő nyitva" számláló**, és a rá épülő `jne` ágak a legördülő nyitva tartása alatt futnak. Felhasználói hatás nincs (a legördülő modális), a PicasaPy-ban nincs teendő; a Mappakezelő szürkítésére vonatkozó állítás (a szerkesztő-előnézet) ettől külön, a `0x0056c5a0` olvasóján marad. Az azonos objektumra vonatkozás az `esi`/`edi` regiszterekből feltételes (a mezőeltolás és a `this`-szerepű argumentum azonos).

A Colab-mérés (8. szakasz) két további állítást helyesbít:

- **3.2, a Shortcuts-tiltások:** "a rendszermappa-ellenőrzés csak feltevés, Windows-specifikus, a PicasaPy-ban nincs teendő." **Megdőlt:** a Desktop és a My Pictures tétel a mért képen szürke (job-804 17. kép), és a `0x004f7e40` olvasata szerint a szürkítés a könyvtár mappáitól függ, nem Windows-specifikus; a teendő a J7. A My Documents sosem tiltott, ez a korábbi állítás része volt, és a mérés megerősíti.
- **4., "Mikor kerül a registrybe? nyitott":** a váltás pillanatában nem (job-805), kényszerített leállás után az alapérték áll (job-806), a szabályos kilépés a C5c mérésére vár.

A 6. szakasz 1-7. sora és a 7. szakasz J1-J4 "Mit ad ma" mezői a #7340 és #7341 beolvasztása előtti állapotot írják; a J1-J4 azóta a fő ágban van, a mai kód idézetei a 8. szakasz jegyeiben állnak.

## 10. Amit kizártam

- **A `0x9c5e` a Mappa ▸ Rendezéshez tartozik** (első kör): megdőlt, `ID_REFRESH_THUMB`.
- **A Show Thumbnails fanézetben engedélyezett** (első kör): megdőlt, szürke (`0x005e2596`).
- **A `0x00733480` a menüsáv-építő**: nem, ez a ▾ legördülő rekordtábla-feltöltője (`CreatePopupMenu` `0x00733978`).
- **A `Thumbscale` és `ThumbscalePeople`**: a #7333 tárgya, nem vizsgáltam.
- **A hasáb jobbklikk-menüjének léte az eredetiben**: kizárva, a futó eredetiben nincs (C1, job-801).
- **A rács mappa-blokkjainak független rendezése (`folderSort`) mint eredeti funkció**: a binárisban egyetlen rendezési mezőpár (`+0xd8`, `+0x165`) áll a listaobjektumon; a C2 mérése igazolta, hogy a rács a hasáb sorrendjét követi (job-802 15. kép), független rendezés nincs.
- **A szabályos kilépéskori mentés mint mért tény**: nem állítom, a C5c mérésére vár; a kényszerített leállításból (`wineserver -k`) nem következik.
