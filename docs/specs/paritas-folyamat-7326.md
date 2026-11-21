# A nézet rendezésének és megjelenítésének teljes folyamata az eredeti Picasával összevetve (#7326, második kör)

Issue: #7326. Eredeti: Picasa 3.9.141.259, SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96` (a helyi `Picasa3.exe` bitre azonos a bináris-indexben szereplővel). Kép-alap: az `0x00400000`. A bináris statikusan volt vizsgálva (capstone, a `pe_dis.py` és az index), a két tulajdonosi felvétel pedig a mérce (lásd 1. szakasz).

A lap a Nézet és a Mappa menü rendezési és megjelenítési parancsait követi a belépési ponttól a hatásig: a bal hasáb ▾ ("View options") legördülőjét, a Nézet ▸ Mappanézet almenüt, a Mappa ▸ Rendezés almenüt, az Indexkép felirata almenüt és a hasáb jobbklikk-menüjét. A bélyegméret-csúszka (`Thumbscale`, `ThumbscalePeople`) tárgya a #7333, azt ez a kör szándékosan nem vizsgálja újra.

## Következtetés

**A rendezési szemantika egyezik, a menük szerkezete nem.** A rendezés kulcsai, iránya, alapértéke és a fordítás független tárolása a PicasaPy-ban az eredetit követik, és az Indexkép felirata almenü is egyezik (egy mnemonikus betű hiányát leszámítva). Az eltérés abban van, hogy az eredetinek **két külön menütáblája** van (a ▾ gomb 14 rekordos legördülője és a menüsáv 13 rekordos Mappanézet almenüje), a PicasaPy pedig **egyetlen** `PicasaFolderViewMenu`-t nyit mindkét belépési pontról, ráadásul a két meglévő menüben tételek hiányoznak, többletként vannak jelen, vagy fordított sorrendben állnak. Emellett a menüsáv Mappa ▸ Rendezés tételei nálunk **tartós rácssorrendet** állítanak, az eredetiben viszont **egyszeri átrendezést** végeznek az aktuális mappa képein.

Négy javasolt fejlesztői jegytörzs (J1-J4) és egy felirat-apróság (J5), a 7. szakaszban. A futásidejű kérdéseket (C1-C5, 8. szakasz) csak az eredeti Picasa futtatott felvétele dönti el, a pontos Colab-lépéssort ott adom meg.

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

A kezelő három további `EnableMenuItem`-et is hív a Shortcuts-gyerekekre (`0x005e2558` My Pictures `0x9e3a`, `0x005e256a` és `0x005e257c` mindkettő `0x9dba`): a jelzők a `0x004f7e40` három hívásának eredményei (az argumentumot a `0x009966a0`, `0x00996230` és `0x00996b90` adja; a hívások jelentését nem bontottam tovább, a rendszermappa-ellenőrzés csak feltevés). A `0x005e257c` a My Documents (`0x9db7`) helyett is a Desktop azonosítót küldi, tehát a My Documents ebben a kezelőben sosem kap tiltást: Windows-specifikus, a PicasaPy-ban nincs teendő.

### 3.3 Megjelenítés

`TrackPopupMenu` (`[0xc407c4]`, `0x005e264e`: `uFlags = 2`), a pozíciót a `ClientToScreen` (`[0xc40828]`, `0x005e208c`) adja. A hívás körül a kezelő a `[esi+0x34a4]` számlálót eggyel növeli (`0x005e2637`) és csökkenti (`0x005e2659`): lásd a 9. szakasz helyesbítését.

## 4. Hatás: mi változik a parancs kiadásakor

| Kérdés | Eredeti | Bizonyíték | Fok |
|---|---|---|---|
| Mikor hat? | **Azonnal**, a menüpont kiválasztásakor. Az `0x004b07c0` (75 bájt) a mezőt és a megfordítást egyszerre állítja (`0x004b07dc`, `0x004b07e2`), azonos érték mellett nem csinál semmit (`0x000f4242`), különben a `0x006dc4c0(…, 1)` újraépíti a listát (`0x004b0803`). | `picasa-idorend-bemutato-kutatas.md` §2, `picasa-menu-parancsok-viselkedes.md` 67.3 | megerősített |
| Mit ír? | Csak a `Preferences` kulcsait: **`datesort`** (mód 0/1/2/5, `0xc83078`), **`peoplesort`** (0/1/2, `0xc83084`), **`albumlistflip`** (megfordítás, `0xc83090`). Olvasó `0x004a1560` (`0x004a195f`-`0x004a1a05`), író `0x004a3790`. **Fájlt, `.picasa.ini`-t, indexet nem ír.** | `picasa-menu-parancsok-viselkedes.md` 36.3 | megerősített |
| Alapérték | `datesort` 0 (dátum), `peoplesort` 0 (név), `albumlistflip` 0: a `GetPreference` hívás előtt `xor eax, eax` (`0x004a196e`), és a #26 felvétel dátumrendezést mutat. A `0x00407a20` alapérték-paraméterének jelentését nem bontottam ki, tiszta profilú mérés NINCS MEG (C5). | `0x004a1930`-`0x004a1a05`, `picasa-menu-parancsok-viselkedes.md` 36.3 | feltételes |
| Szempontváltáskor a fordítás | **Megmarad** (a két mező egy hívásban, a gombok a jelenlegi megfordítást adják tovább). | `0x004b07cc`, `0x005db200`, `0x005db266` | megerősített |
| Irány | Dátum, legutóbbi, méret **csökkenő** (az újabb, a nagyobb előbb), név **növekvő**. | `0x004a7890`, `picasa-idorend-bemutato-kutatas.md` §2 | megerősített (név: erős) |
| Mi fut le utána? | A hasáb újraépül; a Mappa ▸ Rendezéssel ellentétben **a képek sorrendjét nem írja át**. Háttérmunka, állapotsor-üzenet, folyamatjelző a ▾ parancsokhoz nincs a kezelőben. | `0x005e2000` teljes olvasata | erős |
| Hiba, megszakítás, írásvédett vagy hálózati hely | A ▾ parancsok fájlt nem módosítanak, ezért írásvédett vagy hálózati helyre vonatkozó ág nincs; a `Preferences` registry-írás eredményének vizsgálatát a `0x004a3790`-ben nem olvastam ki: NINCS MEG. | `0x004a3790` | feltételes |
| Visszavonás | A `0x004b07c0` (75 bájt) csak a két mezőt írja és újraépít, előző állapotot nem ment, és a két menütábla egyik rekordja sem hív visszavonást. A mód közvetlenül újra állítható. | `0x004b07c0`, 2.1 és 2.2 tábla | feltételes |
| Mikor kerül a registrybe? | NINCS MEG: a `0x004a3790` hívási pontja nincs kielemezve (kilépéskor vagy a váltás pillanatában). Lásd C5. | | nyitott |

## 5. Belépési pontok és feltételek

| Belépési pont | Eredeti | Nálunk (fájl:sor) | Eredmény |
|---|---|---|---|
| Eszköztár ▾ ("View options", `thumbui/folderviewpopup`) | A 14 rekordos legördülő (2.1), lenyomásra nyílik. | `MainToolbar.qml:365`: `onPressedChanged: if (pressed) toolbar.folderViewMenuRequested(parent)`; `PicasaViewMenu.qml:14-15`: `function openFolderViewMenu(anchorItem) {` `folderViewMenu.popup(anchorItem, 0, anchorItem.height)` | **Eltér** (J1): a menüsáv almenüjét nyitja. |
| Menüsor Nézet ▸ Mappanézet | A 13 rekordos almenü (2.2). | `PicasaViewMenu.qml:548`: `PicasaFolderViewMenu {`; tartalma `PicasaFolderViewMenu.qml` | **Eltér** (J2). |
| Bal hasáb üres részén jobbklikk | NINCS MEG: az `AlbumList` tábla (`0xd6efd0`) egyetlen felhasználója a ▾ kezelő; a hasáb-háttér jobbklikkjének belépését a bináris nem mutatja. A `ui-audit-context-menus.md` A.2 szerint ez a menü "a képernyőképeken nem szerepelt". | `FolderPane.qml:604-607`: `objectName: "folderPaneContextMenuHandler"` ... `onSingleTapped: pane.openFolderListContextMenu()` | Feltételes, lásd C1. |
| Menüsor Mappa ▸ Rendezés | Négy tétel, egyszeri átrendezés az aktuális mappa/album képein (2.3). | `PicasaFolderMenu.qml:62`: `title: qsTr("&Sort By")`; `:69`: `controller.setFolderSort("date")` | **Eltér** (J4). |
| Mappasor jobbklikk ▸ Mappa rendezésének alapja | Ugyanaz a négy parancs, egyszeri átrendezés. | `FolderPaneMenus.qml:382`: `controller.sortFolderBy(folderContextMenu.folderPath, mode)` | Egyezik (az `album-sorrend.md` 2.4 és a #4890 szerint). |
| Menüsor Nézet ▸ Indexkép felirata | Öt tétel (2.3). | `PicasaViewMenu.qml:477-478`: `objectName: "menuViewThumbCaptionNone"` / `text: qsTr("None")` | Egyezik, a `&` hiányzik (J5). |
| Gyorsbillentyű | **Nincs.** A rekordok `+0x04` gyorsbillentyű-szövege nulla (a ▾ táblában `0x0073362e`, a menüsávban `0x0055a552`), és a 24 gyorsbillentyűs menürekord listájában (`picasa-menu-leltar.md` 8.3) a rendezés- és nézetparancsok közül (`0x9c8b`, `0x9cbd`, `0x9c8c`, `0x9dc8`, `0xa0cf`, `0x9cd3`-`0x9cd5`, `0xa0d0`, `0x9cd7`, `0x9db6`, `0x9db8`, `0x9db9`) egyik sem szerepel. | a PicasaPy rendezés-menüiben sincs gyorsbillentyű-szöveg | Egyezik (negatív, erős). |
| `thumbui/datesort`, `thumbui/namesort` | A `0x005d9cc0` kezeli (`0x005db26d` mód 0, `0x005db207` mód 2, `picasa-menu-parancsok-viselkedes.md` 67.1). A `tre-eroforrasok/` alatt `datesort` vagy `namesort` csomópont nincs (grep: 0 találat), gombként való megjelenése nem igazolt. | A PicasaPy-ban a két névre hivatkozás nincs (`grep -rn "datesort\|namesort" src/picasapy/app`: 0). | NYITOTT, lásd C2. |
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

## 8. Nyitott kérdések mérlege és a Colab-lépéssorok

```
Nyitott kérdések: 5 nyílt (C1-C5) · 5 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

Mindegyik **felvehető**, mert az eredeti Picasa Colab-végrehajtójával (`eszkozok/colab_felmero.py`) megmérhető; a következő kör ezeket egy `futtat --lepesek …` feladatban viszi, `--extra '{"mintakeszlet":"idorend"}'` mintakészlettel (több mappa, különböző dátumok), tiszta profilon.

- **C1. Van-e jobbklikk-menü a hasáb üres részén az eredetiben?** Lépések: tiszta profil, mintakészlet betöltve; jobb gomb a bal hasáb üres részén (a mappalista alatt), képernyőkép; ha nyílik menü, a tételek listája. Eredmény: ha nincs, a `FolderPane.qml:604-607` kezelő hamis belépési pont, a J1 ▾ legördülője az egyetlen belépés. Fok jelenleg: feltételes.
- **C2. A rács mappa-blokkjainak sorrendje követi-e a hasábét?** Lépések: ▾ ▸ Sort by Name, majd Sort by Size, majd Reverse sort; minden lépés után egy képernyőkép a bal hasábról és a Könyvtárnézet blokk-fejlécekről (mappanevek sorrendben). Ebből dől el a `folderSort` sorsa (J4) és a `thumbui/datesort`/`namesort` gombok léte.
- **C3. A ▾ tiltások fanézetben:** lépések: fanézet (Nézet ▸ Mappanézet ▸ Fanézet), ▾ megnyitása, képernyőkép. Várt: Top 10 engedélyezett, Indexképek szürke (statikusan igazolt, `0x005e2596`, `0x005e25a4`-`0x005e25b9`).
- **C4. A Shortcuts almenü tartalma és szürke tételei:** lépések: ▾ ▸ Gyorsbillentyűk, képernyőkép; várt: Desktop, My Documents, My Pictures, elválasztó, My Computer (2.1), a hiányzó mappák szürkén.
- **C5. Mikor kerül a registrybe a `datesort`, `peoplesort`, `albumlistflip`?** Lépések: ▾ ▸ Sort by Name, majd Reverse sort; azonnal `wine reg query "HKCU\Software\Google\Picasa\Picasa2\Preferences" /v datesort` és `/v albumlistflip` (az útvonal a `0x006e3990` regisztráló-lap szerinti, Wine-profilonként ellenőrizendő), majd a Picasa szabályos bezárása és megismételt lekérdezés, végül újraindítás és a hasáb sorrendje. Eldönti az 4. szakasz utolsó sorát és a PicasaPy `QSettings` mentési időpontját.

A lezárt kérdések: a ▾ tábla (2.1), a menüsávi tábla (2.2), a tiltások (3.2), a rendezés iránya és a megjegyzett állapot kulcsai (4.), a gyorsbillentyű hiánya (5.).

## 9. Helyesbítés a korábbi lapokhoz

A `picasa-menu-parancsok-viselkedes.md` 36.2 pontja szerint a `[edi+0x34a4]` "ebben a buildben mindig 0: a teljes fájlban egyetlen írása van, a konstruktorban". Ez **megdőlt**: a `0x005e2637` `add dword ptr [esi+0x34a4], 1` és a `0x005e2659` `add dword ptr [esi+0x34a4], -1` a ▾ legördülő `TrackPopupMenu` hívását keretezi. A korábbi pásztázás csak a `mov imm` és `mov reg` írásalakokat kereste, az `add` formát nem. A mező tehát egy **"legördülő nyitva" számláló**, és a rá épülő `jne` ágak a legördülő nyitva tartása alatt futnak. Felhasználói hatás nincs (a legördülő modális), a PicasaPy-ban nincs teendő; a Mappakezelő szürkítésére vonatkozó állítás (a szerkesztő-előnézet) ettől külön, a `0x0056c5a0` olvasóján marad. Az azonos objektumra vonatkozás az `esi`/`edi` regiszterekből feltételes (a mezőeltolás és a `this`-szerepű argumentum azonos).

## 10. Amit kizártam

- **A `0x9c5e` a Mappa ▸ Rendezéshez tartozik** (első kör): megdőlt, `ID_REFRESH_THUMB`.
- **A Show Thumbnails fanézetben engedélyezett** (első kör): megdőlt, szürke (`0x005e2596`).
- **A `0x00733480` a menüsáv-építő**: nem, ez a ▾ legördülő rekordtábla-feltöltője (`CreatePopupMenu` `0x00733978`).
- **A `Thumbscale` és `ThumbscalePeople`**: a #7333 tárgya, nem vizsgáltam.
- **A hasáb jobbklikk-menüjének léte az eredetiben**: nem zártam ki és nem is igazoltam (C1).
- **A rács mappa-blokkjainak független rendezése (`folderSort`) mint eredeti funkció**: a binárisban egyetlen rendezési mezőpár (`+0xd8`, `+0x165`) áll a listaobjektumon; független blokk-rendezést nem találtam, a döntést C2 hozza meg.
