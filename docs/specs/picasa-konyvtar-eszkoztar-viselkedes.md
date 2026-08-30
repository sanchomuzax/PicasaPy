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
  (`Property prenotify 1` — **MEGFEJTVE (2026-08-30), ld. lent**, NEM
  azonos a `mousedown`-nal), a `flatview`-n **semmi**. A pár tehát **NEM**
  tagja a #885 49 elemes `mousedown`-listájának — ott ellenőrizhetően
  csak a `folderviewpopup` szerepel (ld. lent). Ez a lap egy korábbi
  fogalmazásban tévesen mindkettőre mousedown-t állított; itt javítva.

### ✅ A `prenotify` tulajdonság — MEGFEJTVE (2026-08-30)

A `.tre`-parszer (`0x009ca5e0`, 7899 b) a `prenotify` kulcsszót a
`0x009c7840` setterbe vezeti, amely az elem `+0x380` bájtjára **`1`-et
ír** (a többi interakciós property párhuzamos settereivel együtt:
`hiddentimer`→`0x009c7700`, `throb`→`0x009c7870`, `enableclip`→
`0x009c78a0`). A `picasa-eger-es-kijeloles.md` 1.3 szakaszának megfejtése
(„a váltás ELŐTT értesít") **megerősítve a binárisból**: a
`prenotify 1` egy **belső jelző-mezőt** állít (nem felirat, nem
mousedown-kezelő), a folderview elemen a kattintás-váltás előtti
értesítés engedélyezésére.

*Bizonyítottsági fok: **megerősített** — a parszer-kulcsszó-tábla
(`prenotify` string `0x0087cbd8`) és a `0x009c7840` setter diszasszemblálva.*

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



### 4/c ⭐ A `folderviewpopup` kezelő teljes parancstérképe (2026-08-30)

A kezelő (`0x005e2000`, 1689 b) a menü **megnyitásakor** fut, és minden
tétel pipa-állapotát a **dokumentum-mezőkből** építi. Ez lezárja a 4/b
„ami ebből NEM oldódott fel" megjegyzését és az alábbi NYITVA 2 és 3
pontokat is.

| parancs | menükulcs | mit pipáz a kezelő | a pipa forrása |
|---|---|---|---|
| `0x9c8b` | `eMenuView::ID_VIEWBYDATE` | Rendezés létrehozási dátum | `[+0x2c0+0xd8] == 0` |
| `0x9cbd` | `eMenuView::ID_VIEWBYRECENT` | Rendezés legutóbbi változtatások | `[+0x2c0+0xd8] == 1` |
| `0x9c8c` | `eMenuView::ID_VIEWBYNAME` | Rendezés név alapján | `[+0x2c0+0xd8] == 2` |
| `0x9dc8` | `eMenuView::ID_VIEWBYSIZE` | Rendezés méret alapján | `[+0x2c0+0xd8] == 5` |
| `0xa0cf` | `eMenuView::ID_VIEWREVERSE` | Rendezés megfordítása | `[+0x2c0+0x165]` (bájt) |
| `0x9e18` | (a menüsáv-építőben nincs) | a ▾ menü harmadik csoportjának 1. tétele | `[+0x2c0+0xdc] == 0` |
| `0x9e19` | (a menüsáv-építőben nincs) | … 2. tétele | `[+0x2c0+0xdc] == 1` |
| `0x9e38` | (a menüsáv-építőben nincs) | … 3. tétele | `[+0x2c0+0xdc] == 2` |
| `0x9db8` | `eMenuView::ID_VIEW_WATCHED` | &Egyszerűsített fanézet | `Preferences\SimplifiedHierarchy` |
| `0x9db6` | `eMenuView::ID_VIEW_FOLDERS` | &Egyszerű mappanézet | `[+0x2c0+0x9d] == 0` |
| `0x9db9` | `eMenuView::ID_VIEW_ALL` | &Fanézet | `[+0x2c0+0x9d] != 0` |
| `0x9dba` | `eMenuView::ID_VIEW_DESKTOP` | &Asztal | a gyökér-hatókör `"desktop"` |
| `0x9e3a` | `eMenuView::ID_VIEW_MYPICTURES` | &Képek | a gyökér-hatókör `"mypics"` |
| `0x9db7` | `eMenuView::ID_VIEW_MYDOCS` | Do&kumentumok | a gyökér-hatókör `"mydocs"` |
| `0x9cd7` | `eMenuView::ID_VIEW_THUMBNAILS` ("Show &Thumbnails in Library") | pipa | `Preferences\ShowAlbumThumbnails2` |

A diszasszemblálás bizonyítéka: `0x005e2000` minden tételnél a
`[0xc40810]` `CheckMenuItem`-importot hívja, `MF_CHECKED`-flaggel (a
`push … 8` az MF_CHECKED), a feltétel pedig a fenti mező-összehasonlítás
(a `neg`/`sbb`/`and eax, 8` idióma az „érték egyezik-e" kérdésre).

### ✅ A `ShowAlbumThumbnails2` preferencia pontos szerepe — LEZÁRVA

**Ez a fenti parancstábla egy pipa-tétele**: „Indexképek &megjelenítése a
könyvtárban" (`eMenuView::ID_VIEW_THUMBNAILS` = „Show &Thumbnails in
Library"). A kezelő a `Preferences\ShowAlbumThumbnails2` kulcsot
`GetPreference`-szel olvassa (`0x407a20`, alapérték: `0`), és az alapján
pipázza a `0x9cd7` parancsot (`0x005e25ef`–`0x005e2628`). **A tétel léte a
menüben és a preferencia-bekötése így MEGERŐSÍTVE** — nem kell többé
feltételezés.

A `0x9cd7` parancs tulajdonosai és a teljes életciklus:
- a menüsáv-építő `0x00559150` felveszi a rekordját (`[0xd6df54]` körüli
  tömb; kulcsa `eMenuView::ID_VIEW_THUMBNAILS`, felirata „Show &Thumbnails
  in Library", a string-címek `0xc8cd5c`/`0xc8cd7c`);
- a kezelő `0x005c93d0` (**nem** a fenti `0x005e2000`!) a parancs
  **bekapcsolását** végzi: ezt a `0x005cb990` menüsáv-diszpécser `0x9cd7`
  ága hívja (`0x005cbbc7`). A `0x005c93d0` a `GetPreference`-ből olvas, a
  `[+0xd4c]+0x20` bájtot állítja a beolvasott értékre, majd a nézetet
  frissíti (`0x00574b70`-en át) — a pipáló `0x005e2000` a menü NETTO
  pipa-állapotát ebből a preferenciából olvassa újra;
- a `0x00761870` konstruktor az induláskori állapot beolvasását végzi
  (`mov byte [obj+0x20], al` a `GetPreference` után — az album-nézet
  objektum +0x20 látszólagos „mutasd az indexképeket" flagje).

### ✅ A mód-mező (`+0x2c0+0xd8`) 0/1/2/5 értéke — LEZÁRVA

A fenti tábla rendezés-soraiból **kiolvasható a teljes kódolás**: a
`[+0x2c0+0xd8]` mező nem „külön nézetmód", hanem **a rendezés-mód kódja**:
`0` = Dátum, `1` = Legutóbbi változtatások, `2` = Név, `5` = Méret. A
`0x005e2000` és a `0x00574b70` ugyanezeket az értékeket pipázza a
rendezés-parancsokra.

*Bizonyítottsági fok: **megerősített** — minden állítás a `0x005e2000`
annotált diszasszemblálásából (a `[0xc40810]` CheckMenuItem-hívás, a
mező-összehasonlítások, a `neg`/`sbb` idiómák) és a `0x00559150`
menüsáv-építő rekordjaiból.*

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
| **Nézetváltó pár** (flatview/folderview) | kölcsönösen kizáró rádiógomb-pár, `SimplifiedHierarchy` preferenciát ír, menüegyenértéke is van (a `folderview` oldalán egy **MEGFEJTVE** `prenotify` jelzés, ld. 3. pont) | **az ADATRÉTEG megvan** (`FolderHierarchyController`, `treeViewMode` property, `FolderHierarchyView.qml` — #702-ből), de **nincs UI-vezérlő, ami átkapcsolná**: a `Main.qml:978` `treeViewMode: false`-ra van **beégetve**, sehol nem íródik felül | pótolni a két fejléc-gombot (#853 méret-táblája szerint), bekötni a meglévő `treeViewMode`-ra |
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
- **`folderviewpopup` menütartalma:** *megerősített* — a 4/b a
  parancsazonosítókat, a 4/c a **teljes pipa-térképet** (minden tétel
  pipa-forrása a dokumentum-mezőkből) a `0x005e2000` kezelő
  diszasszemblálásából.
- **A `ShowAlbumThumbnails2` és a mód-mező (`+0x2c0+0xd8`) értékei:**
  *megerősített* — ld. 4/c (a rendezés-parancsok pipa-kódjai; 0=Dátum,
  1=Legutóbbi változtatások, 2=Név, 5=Méret).

## Ami NYITVA marad

1. ~~**A `folderviewpopup` menü tételeinek pontos felirata**~~
2. ~~**A `ShowAlbumThumbnails2` preferencia pontos hatása**~~ —
   **LEZÁRVA (2026-08-30), ld. 4/c.** A „Indexképek megjelenítése a
   könyvtárban" (`0x9cd7`) pipa-tétele a ▾ menüben; a teljes életciklus a
   4/c-ben.
3. ~~**A mód-mező (`+0x2c0+0xd8`) 2-es és 5-ös értéke**~~ — **LEZÁRVA
   (2026-08-30), ld. 4/c**: 2 = név, 5 = méret rendezés; a rendezés-tételek
   pipa-kódjai, a `0x005e2000`/`0x00574b70` diszasszemblálásából.
4. **A `0x9e18`/`0x9e19`/`0x9e38` hármas konkrét felirata** — az
   `[+0x2c0+0xdc]` mező 0/1/2 értékeihez kötött rádió-hármas **pipa-sémája
   megvan**, de a felirat-szöveg a honosítási táblában nem azonosítható (a
   menüsáv-építőben nincs rekordjuk; a `0x005e2000` csak pipázza őket, a
   feliratot a helyi menü-erőforrás adja). A megvalósításhoz ez nem
   blokkol: a ▾ menünek ez a csoportja ma nálunk nem létezik, a feliratot
   a pótló kör veszi át (a tulajdonos képernyőképéről, ha elengedhetetlen).

## Amit KIZÁRTAM

- Hogy a `folderviewpopup` egy **önálló beállítás-dialógust** nyitna —
  **nem**, a közös scope-kulcsos függvényt hívja, tehát **menü**, nem
  panel.
- Hogy az `importbutton` a `.tre`-ben feltételesen tiltva lenne — nincs
  ilyen bejegyzés, mindig aktív.
- Hogy a webkamera-gomb kattintás-mechanikája bármiben eltérne a
  lebegő értesítősáv már ismert szingleton-mintájától — **nem tér el**,
  ugyanaz az `EnumWindows` + "wCPG" jelölő.
