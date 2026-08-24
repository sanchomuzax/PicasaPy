# A könyvtár-eszköztár öt gombja — VISELKEDÉS (nem geometria)

**Ez a lap a MŰKÖDÉST írja le.** A gombok mérete és pozíciója a
[`konyvtar-ablak-meretek.md`](konyvtar-ablak-meretek.md) „A fő eszköztár —
mért geometria" szakaszában van (`respack.yt`, megerősített). A jegy, ami a
hiányukat felvetette: **#853**. Ez a lap az ott nyitva hagyott kérdést
("a `folderviewpopup` mit tartalmaz") és a másik négy gomb **teljes
viselkedését** (mit aktivál, mit ír, milyen feltétellel engedélyezett,
milyen hibaesetek vannak) zárja le.

Módszer: a megosztott név-diszpécser függvény (`0x005d9cc0`, 7153 bájt) a
felület minden `thumbui/<név>` kattintását ide vezeti; innen ágazik el az
öt gombra. Minden cím a `Picasa3.exe` (3.9.141.259) betöltési címe szerint
értendő (image base szerinti VA, nem RVA).

## 1. `importbutton` — Import

- **Kezelő:** `0x005d3010` (223 bájt), a `0x005d9cc0` diszpécserből a
  `"thumbui/importbutton"` sztringre hívva.
- **Mit csinál:**
  1. Növel egy számlálót a fő objektum `+0x24c` mezőjén, és nullázza a
     `+0x250` mezőt (munkamenet-jellegű "hányszor váltottunk importra"
     jelző — a pontos felhasználása nincs tovább követve).
  2. Ha az objektum `+0xed0` mezőjén át elérhető egy vtable, meghívja azt
     (`[[+0xed0]+0x258][0]+0xc]`) — egy generikus "előző mód lezárása"
     hívás, valószínűleg az aktuális szerkesztő/nézet állapot mentése
     váltás előtt.
  3. **Csak ha egy globális debug-kapcsoló (`[0x00d67914]`) be van
     kapcsolva** (kiadási build-ben feltehetően 0): frissíti az
     `editpanel/preview` vezérlő engedélyezett állapotát a jól ismert
     `[control+0x20e]` letiltás-bájt konvención át. **Ez NEM
     produkciós logika** — kihagyható.
  4. Létrehoz egy esemény-objektumot (`call 0xc07db2` fix
     típus-mutatópárral: `0xd3b8a0`/`0xd3b8d8`), majd egy belső
     eseménysoron (`+0x344c`) keresztül **eseményt küld**, ami a UI-t az
     Import/Acquire panelre kapcsolja.
- **`.tre` oldal:** az `importbutton` a `m_acquire_enable` makróval van
  megjelölve, ami a `panelroot/acquiretab` panelt teszi láthatóvá/célzottá
  — ez egyezik a fenti "esemény az Import panelra vált" olvasattal.
- **Menüegyenérték:** nincs bizonyíték rá ebben a diszpécserben; a
  `Fájl` menüben Picasa 3-ban nincs "Import" tétel (a valós programban a
  gomb az EGYETLEN belépési pont).
- **Engedélyezés/láthatóság:** a `.tre`-ben nincs feltételes
  `disable`/`setvisible` bejegyzés az `importbutton`-on — mindig aktív.
- **Hibaeset:** nincs kód-szintű hibaág (nem néz kamerát/scannert — az
  Acquire panel maga kezeli az eszközkeresést, az egy másik, itt nem
  vizsgált alrendszer).

## 2. `newalbum` — Új album

- **Kezelő:** `0x005eb810` (245 bájt).
- **Mit csinál:**
  1. Lekér egy `"Labels"` (`0xc7ec5c`) kulcs alatti értéket 6-os indexszel
     (`call 0x00985ff0`) — feltehetően egy alapértelmezett albumnév-sablon
     vagy címke-lista.
  2. Egy objektum-metódussal (`0x00452a30`) és egy névgeneráló hívással
     (`0x0055cf70`) előállít egy jelölt nevet.
  3. **Próbál** azonnal létrehozni egy albumot (`call 0x006dc030(doc, name,
     1, 0)` → `bool`). Ha ez **sikeres** (`al != 0`): tovább egy második
     próbálkozásra (`0x0055d120`), és ha AZ is nullát ad vissza, a
     függvény egyszerűen visszatér — **csendes létrehozás, dialógus
     nélkül**.
  4. Ha a gyors létrehozás **sikertelen** (`al == 0`): beállítja a
     `+0x166` mezőn az 1-es "album létrehozás folyamatban" jelzőt, és
     meghívja a `0x0065b840(doc, 0, 0, 1)` függvényt — ez nyitja meg az
     **interaktív "Új album" tulajdonság-dialógust** (névbeírás).
- **Emberi nyelven:** a gomb **megpróbál egy alapértelmezett nevű albumot
  azonnal, dialógus nélkül létrehozni**; csak akkor jelenik meg a
  névbekérő ablak, ha ez a gyors út valamiért nem sikerül (pl. már van
  ilyen nevű album, vagy nincs kijelölt kép a gyors névhez).
- **Menüegyenérték:** **IGEN** — a `0x005cb990` menü-parancstáblában
  (a korábbi körben már feltárt View/Album parancs-diszpécser) van olyan
  ág, ami ugyanide, a `"thumbui/newalbum"` néven szimulált kattintáson
  (`call 0x009cd8a0(name)`) keresztül újra a fenti kezelőt hívja —
  vagyis a `Fájl → Új album` menüpont **ugyanazt** csinálja, mint a gomb.
- **Engedélyezés:** a `.tre`-ben nincs feltétel — a gomb mindig aktív.

## 3. `flatview` / `folderview` — a nézetváltó pár

- **Közös kezelő (kattintás + engedélyezés-frissítés):** `0x00575130`
  (1332 bájt). Ez **nem csak a két gombot** szolgálja ki, hanem a teljes
  `folderviewpopup` menüt is (ld. 4. pont) — egyetlen, szövegkulccsal
  paraméterezett függvény.
- **A mechanizmus:** a hívás egy string-kulccsal érkezik
  (`"all"` / `"flat"` / `"watched"` / `"mypics"` / `"mydocs"` /
  `"desktop"`), és:
  - beolvassa/frissíti a **`Preferences\SimplifiedHierarchy`** kulcsot
    (`0x00407a20` generikus olvasó, ugyanaz, mint a projekt összes
    `Preferences\*` olvasása — 348 hívóhely a bináris egészében),
  - a `"flat"` kulcsra a `SimplifiedHierarchy` értéket **1**-re állítja
    (lapos nézet), másra (fanézet) töröl,
  - a mappalista **gyökér-hatókörét** is beállítja: `"all"` →
    `"ViewRoot::All"` / `"My Computer"` gyökér, `"watched"` →
    `"ViewRoot::AllFolders"` / `"Default View"` gyökér — a `"mypics"` /
    `"mydocs"` / `"desktop"` kulcsok egy közös ágon át szintén a
    gyökér-hatókört állítják be (a pontos cél-elérési út string.
    összefésülése ezen a mélységen nem lett tovább bontva — ld. „Ami
    nyitva marad").
- **Az engedélyezett állapot** (`0x00574b70`, a globális UI-frissítő,
  amit a `flatview`/`folderview` maguk is meghívnak kattintáskor).

  > ⛔ **HELYESBÍTÉS (2026-08-24).** Ez a szakasz korábban azt állította,
  > hogy a `flatview` parancsazonosítója `0x9c8b`, a `folderview`-é
  > `0x9cbd`, és hogy a kettő mód-mező szerint kölcsönösen kizáró.
  > **Mindkét azonosító TÉVES volt** — a menüépítő (`0x00559150`)
  > rekordtömbjének végigjárásával a valódi feloldás:
  >
  > | cmd | menükulcs | felirat (HU) |
  > |---|---|---|
  > | `0x9c8b` | `eMenuView::ID_VIEWBYDATE` | Rendezés létrehozási dátum alapján |
  > | `0x9cbd` | `eMenuView::ID_VIEWBYRECENT` | Rendezés a legutóbbi változtatások alapján |
  > | `0x9c8c` | `eMenuView::ID_VIEWBYNAME` | Rendezés név alapján |
  > | `0x9dc8` | `eMenuView::ID_VIEWBYSIZE` | Rendezés méret alapján |
  > | **`0x9db6`** | **`eMenuView::ID_VIEW_FOLDERS`** | **&Egyszerű mappanézet** |
  > | **`0x9db9`** | **`eMenuView::ID_VIEW_ALL`** | **&Fanézet** |
  >
  > Vagyis a `0x00574b70` a **RENDEZÉS** menütételeit tiltja/engedi a
  > mód-mező (`[dokumentum+0x2c0+0xd8]`, értékei 0/1/2/5) szerint, a két
  > **mappanézet-módot** pedig egyetlen közös jelzőn (`[+0x9d]`) — nem
  > kölcsönösen kizáróan, ahogy korábban írtuk.
  >
  > **Miből derült ki:** a menürekord 20 bájtos, a `+0x0a` a
  > parancsazonosító, és a `0x00559150`-ben a rekord **címkéjét** a
  > kulcs-push UTÁN írják. A rekordbázisok végigjárásával 160
  > parancsazonosító oldódott fel egyértelműen — köztük mind a hat fenti.
- **Menüegyenérték:** **IGEN** — a `0x005cb990` menü-diszpécserben a
  View menü megfelelő tételei ugyanezt a `0x00575130`-at hívják a
  `"all"`/`"flat"` kulccsal.
- **A `.tre` oldala — HELYESBÍTVE:** ellenőrizve közvetlenül a
  `thumbui.tre`-ben: **csak a `folderview`-n** van külön jelölés
  (`Property prenotify 1` — **dekódolatlan** tulajdonság, NEM azonos a
  `mousedown`-nal), a `flatview`-n **semmi**. A pár tehát **NEM** tagja a
  #885 49 elemes `mousedown`-listájának — ott ellenőrizhetően csak a
  `folderviewpopup` szerepel (ld. lent). Ez a lap egy korábbi
  fogalmazásban tévesen mindkettőre mousedown-t állított; itt javítva.

## 4. `folderviewpopup` — Nézet-beállítások (▾)

- **Kezelő:** `0x005e2000` (1689 bájt), ugyanabból a `0x005d9cc0`
  diszpécserből, a `"thumbui/folderviewpopup"` névre.
- **Ez ÉRDEMBEN megválaszolja a #853 nyitva hagyott kérdését** ("a
  nézet-beállítások gomb megnyit valamit, de a menü tartalma nem derült
  ki ebből a forrásból"):
  - A kezelő a **közös `0x00575130`** scope-kulcsos mechanizmust
    (ld. 3. pont) hívja meg — vagyis a `▾` gomb **NEM egy önálló
    beállítás-panelt**, hanem egy **lenyíló menüt** nyit, aminek a
    tételei **ugyanazok a gyökér-hatókör-kulcsok**, amiket a
    scope-függvény ismer: **Mind / My Computer** (`"all"`), **Figyelt
    mappák** (`"watched"`), **Saját képek** (`"mypics"`), **Saját
    dokumentumok** (`"mydocs"`), **Asztal** (`"desktop"`).
  - Emellett ugyanez a kezelő olvassa a **`Preferences\
    ShowAlbumThumbnails2`** kulcsot is — ez valószínűleg egy külön
    jelölőnégyzet-tétel a menüben ("Show album thumbnails" jellegű), de
    ennek a konkrét feliratát/hatását ez a kör nem azonosította.
  - A menü tételeinek engedélyezett állapotát numerikus
    parancsazonosítókkal frissíti, közös „parancs engedélyezése" híváson
    (`[0x00c40810]`) át — ugyanúgy, mint a `0x00574b70`.

### 4/b ⭐ A MENÜ TÉTELEI — feloldva (2026-08-24)

A korábbi „a pontos feliratszöveg nem dönthető el" megállapítás
**MEGDŐLT**. A menüépítő (`0x00559150`) rekordtömbjének végigjárásával
mind a tizenegy azonosító feloldódott, és a feliratok a honosítási
táblából jönnek. **Ez a `Nézet ▸ Mappanézet` almenü**
(`eMenuView::FolderView` = „&Mappanézet").

**Mappanézet-módok — HÁROM, nem kettő:**

| cmd | kulcs | angol | **magyar** |
|---|---|---|---|
| `0x9db6` | `ID_VIEW_FOLDERS` | &Flat Folder View | **&Egyszerű mappanézet** |
| `0x9db8` | `ID_VIEW_WATCHED` | &Simplified Tree View | **&Egyszerűsített fanézet** |
| `0x9db9` | `ID_VIEW_ALL` | &Tree View | **&Fanézet** |

> ⚠️ **A HARMADIK mód eddig sehol nem szerepelt nálunk.** A lap 3. pontja
> (és a `FolderHierarchyView.qml` fejléce) **két** egymást kizáró módról
> ír. Valójában **három** van — ez magyarázza a mód-mező 0/1/2/5
> értékkészletét is.

**Gyökér-hatókörök — a scope-kulcsok felirata:**

| scope-kulcs (`0x00575130`) | cmd | kulcs | **magyar felirat** |
|---|---|---|---|
| `"all"` | `0x9dcb` | `ID_VIEW_MYCOMPUTER` | **&Sajátgép** |
| `"mydocs"` | `0x9db7` | `ID_VIEW_MYDOCS` | **Do&kumentumok** |
| `"mypics"` | `0x9e3a` | `ID_VIEW_MYPICTURES` | **&Képek** |
| `"desktop"` | `0x9dba` | `ID_VIEW_DESKTOP` | **&Asztal** |
| `"watched"` | — | `ViewRoot::AllFolders` | **Alapértelmezett nézet** |

*(A kezelő az `"all"` ághoz szó szerint a `ViewRoot::All` = „My Computer"
/ **„Sajátgép"** feliratot használja, a `"watched"`-hez a
`ViewRoot::AllFolders` = „Default View" / **„Alapértelmezett nézet"**-et —
ez zárja a kört a `0x00575130`-ban látott sztringekkel.)*

**Rendezés-tételek** (ugyanennek a menünek a része, a mód-mező szerint
tiltva/engedve):

| cmd | kulcs | **magyar** |
|---|---|---|
| `0x9c8b` | `ID_VIEWBYDATE` | Rendezés létre&hozási dátum alapján |
| `0x9cbd` | `ID_VIEWBYRECENT` | Rendezés a leg&utóbbi változtatások alapján |
| `0x9c8c` | `ID_VIEWBYNAME` | Rendezés &név alapján |
| `0x9dc8` | `ID_VIEWBYSIZE` | Rendezés &méret alapján |
| `0xa0cf` | `ID_VIEWREVERSE` | Rendezés megfordítása |

**Ami ebből NEM oldódott fel:** `0x9e18`, `0x9e19`, `0x9e38` — ezek a
menüsáv-építőben nem szerepelnek, tehát egy **helyi menü** építőjében
élnek. Ez nem blokkol semmit: a ▾ menü nyolc tétele + öt rendezés
megvan.

*Bizonyítottsági fok: **megerősített** — a menürekord-tömb gépi
végigjárása (160 azonosító egyértelműen feloldva), a feliratok a
honosítási táblából. A `0x9db8` ↔ „Egyszerűsített fanézet" ugyanebből a
körből, ugyanazzal a módszerrel.*

## 5. `webcambutton` — Webkamera-felvétel

- **Kezelő:** `0x0062c340` (183 bájt).
- **Mit csinál:**
  1. **Szingleton-ellenőrzés**: `EnumWindows`-szerű bejárás
     (`call [0x00c40878]`) egy 4 bájtos "wCPG" (`0x47504377`) jelölővel
     — ugyanaz a minta, amit korábban a lebegő értesítősáv
     szingletonjánál is azonosítottunk. Ha **már fut** egy webkamera-
     ablak, egyszerűen előtérbe hozza (`call [0x00c408c8]`,
     valószínűleg `BringWindowToTop`/`SetForegroundWindow`), és
     **visszatér — nem hoz létre másodikat**.
  2. Ha nincs élő ablak: lefoglal egy 0x5c8 (1480) bájtos objektumot
     (`0x0097c5d0`), nullázza (`0x00bf37c0`, memset), majd megkonstruálja
     (`0x0062b0c0`) — ez a webkamera-előnézet panel objektuma.
  3. Létrehozza magát az ablakot a projekt jól ismert modál/felugró
     gyár-hívásán át: `call 0x009d4a80(panel, "capturemoviepanelpopup",
     0, 1)` — a panel **neve/azonosítója tehát `capturemoviepanelpopup`**
     (ugyanaz a gyár, mint a `U3`/`initialscan` felugró ablaknál).
- **Kapcsolódó függvény — hardver-érzékelés:** `0x0067d720` (218 bájt)
  dinamikusan engedélyezi/tiltja magát a `webcambutton` vezérlőt a jól
  ismert `[control+0x20e]` letiltás-bájt konvención át, attól függően,
  hogy talál-e webkamera-eszközt — vagyis **csak akkor kattintható**, ha
  van csatlakoztatott eszköz.
- **A funkció tartalma** (élő előnézet, Live Video/Snapshot mód,
  eszközválasztó, felbontás-beállítás): teljeskörűen dokumentálva a
  #466-ban — ott 2026-ban **P4, "javaslat: kihagyni"** döntés született
  (Windows-specifikus eszközkezelés, a projekt hatókörén kívül). Ez a kör
  nem változtat ezen a döntésen, csak a **kattintás-mechanikát** teszi
  hozzá (szingleton-ablak, panel-azonosító, hardver-kapu).

## Eredeti / nálunk / teendő

| gomb | eredeti viselkedés | nálunk (`app/qml/PicasaPy/`) | teendő |
|---|---|---|---|
| **Import** | esemény → Acquire panelre vált, számlálót növel | `toolbarImportButton` LÉTEZIK (`MainToolbar.qml:49`) | ellenőrizni, hogy a kattintás valóban az import/acquire folyamatot indítja-e — funkcionális teszttel |
| **Új album** | gyors, dialógus nélküli létrehozás → csak sikertelenség esetén névbekérő; **menüegyenérték is van** | **nincs önálló fejléc-gomb** — csak `Fájl → Új album` menü (`PicasaMenuBar.qml:154`, `objectName: "menuFileNewAlbum"`) és a bal hasáb „Új album" drag&drop súgója (`AlbumsSection.qml`) | pótolni a fejléc-gombot (#853-ban már felvéve méretre); a mögötte lévő **gyors-létrehozás ág** ma nincs meg — nálunk minden „Új album" út egyenesen a névbekérő dialógust nyitja |
| **Nézetváltó pár** (flatview/folderview) | kölcsönösen kizáró rádiógomb-pár, `SimplifiedHierarchy` preferenciát ír, menüegyenértéke is van (a `folderview` oldalán egy dekódolatlan `prenotify` jelzés) | **az ADATRÉTEG megvan** (`FolderHierarchyController`, `treeViewMode` property, `FolderHierarchyView.qml` — #702-ből), de **nincs UI-vezérlő, ami átkapcsolná**: a `Main.qml:978` `treeViewMode: false`-ra van **beégetve**, sehol nem íródik felül | pótolni a két fejléc-gombot (#853 méret-táblája szerint), bekötni a meglévő `treeViewMode`-ra |
| **Nézet-beállítások (▾)** | lenyíló menü: Mind/My Computer, Figyelt mappák, Saját képek, Saját dokumentumok, Asztal — gyökér-hatókör váltás | **nincs** semmilyen formában | pótolni: gomb + lenyíló menü öt tétellel; a pontos feliratok forrása még hiányzik (ld. „Ami nyitva marad") |
| **Webkamera** | szingleton előnézet-ablak, hardver-kapuzott, `capturemoviepanelpopup` panel | **nincs**, és a #466/#853 szerint **szándékosan kihagyva** | nincs teendő — a döntés érvényben marad |

## Kész, ha

- [ ] a fejlécben megjelenik az **Új album** gomb (29 × 22, x 124 —
      ld. #853), és ugyanazt a `createAlbum`-utat hívja, mint a meglévő
      menüpont
- [ ] megjelenik a **flatview/folderview** gombpár (2 × 30 × 22, x 160 és
      190), és a meglévő `pane.treeViewMode` property-t kapcsolja —
      NEM új állapotot vezet be
- [ ] a `folderviewpopup` (Nézet-beállítások ▾) gomb **mousedown**-ra
      (nem kattintásra) reagál (#885 általános feltétele — a nézetváltó
      pár NEM tartozik ide, ld. helyesbítés fent)
- [ ] a két gomb **kölcsönösen kizáró**: csak az az egyik van
      engedélyezve/kiemelve, amelyik a MÁSIK állapotra váltana
- [ ] a webkamera-gomb **hiánya** dokumentált, tudatos döntésként marad
      (#466/#853 — ehhez a körhöz nincs új teendő)
- [ ] a **Nézet-beállítások (▾)** gomb és az öt tételes lenyíló menü
      pótlása **külön jegyben** történik (ld. lent), mert a pontos
      feliratszöveg még nyitott kérdés

## Bizonyítottsági fok

- **Import, Új album, nézetváltó pár mechanizmusa, webkamera
  kattintás-mechanika:** *megerősített* — teljes függvénytest olvasva,
  konkrét sztring- és mező-hivatkozásokkal.
- **`folderviewpopup` menütartalma (öt hatókör-tétel léte és
  kulcsai):** *erős* — a hívott függvény és a benne szereplő
  sztringkulcsok egyértelműek, de a menü **feliratszövege** és a
  **`ShowAlbumThumbnails2` tétel pontos szerepe** nincs igazolva.
- **A mód-mező (`+0x2c0+0xd8`) pontos érték-enumerációja** (mi van a
  0/1-en kívül a 2-es és 5-ös értéken): *feltételes* — csak annyi
  bizonyított, hogy EZEK a gombok is ugyanazt a mezőt nézik, a
  konkrét jelentésük nincs feltárva (nem tartozik a mostani öt
  gombhoz).

## Ami NYITVA marad

1. ~~**A `folderviewpopup` menü tételeinek pontos felirata**~~ —
   **LEZÁRVA (2026-08-24), ld. 4/b.** Mind a tizenegy parancsazonosító
   feloldva a menüépítő rekordtömbjének gépi végigjárásával; a feliratok
   a honosítási táblából. **Képernyőkép NEM kellett hozzá** — a korábbi
   „ezt csak a tulajdonos képernyőképe döntheti el" megállapítás
   elhamarkodott volt, az olcsó bizonyítéklánc nem volt kimerítve.
   ⭐ Melléktermékként kiderült, hogy **három** mappanézet-mód van, nem
   kettő, és hogy két korábbi parancsazonosító-hozzárendelésünk téves
   volt (ld. a 3. pont helyesbítését).
2. **A `ShowAlbumThumbnails2` preferencia pontos hatása** — csak azt
   tudjuk, hogy a `folderviewpopup` kezelő olvassa; hogy ez egy
   jelölőnégyzet-e a menüben, vagy valami más UI-elemhez tartozik, nincs
   eldöntve.
3. **A mód-mező (`+0x2c0+0xd8`) 2-es és 5-ös értéke** — nem ehhez az öt
   gombhoz tartozik, de ugyanaz a frissítő függvény (`0x00574b70`) állítja
   be őket is; ha valaha más gombok (`timelinebutton`, `cdmode`?)
   viselkedését kutatjuk, innen érdemes folytatni.

## Amit KIZÁRTAM

- Hogy a `folderviewpopup` egy **önálló beállítás-dialógust** nyitna —
  **nem**, a közös scope-kulcsos függvényt hívja, tehát **menü**, nem
  panel.
- Hogy az `importbutton` a `.tre`-ben feltételesen tiltva lenne — nincs
  ilyen bejegyzés, mindig aktív.
- Hogy a webkamera-gomb kattintás-mechanikája bármiben eltérne a
  lebegő értesítősáv már ismert szingleton-mintájától — **nem tér el**,
  ugyanaz az `EnumWindows` + "wCPG" jelölő.
