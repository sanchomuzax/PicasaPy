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
- **Az engedélyezett/lenyomott állapot** (`0x00574b70`, a globális
  UI-frissítő, amit a `flatview`/`folderview` maguk is meghívnak
  kattintáskor): egy **közös mód-mező** (`[dokumentum+0x2c0+0xd8]`)
  alapján dönt —
  - `flatview` (parancs-azonosító `0x9c8b`) **akkor engedélyezett**, ha a
    mód-mező **0** (vagyis épp FA-nézetben vagyunk — a gomb felkínálja a
    váltást lapos nézetre),
  - `folderview` (`0x9cbd`) **akkor engedélyezett**, ha a mód-mező **1**
    (épp LAPOS nézetben vagyunk),

  vagyis a pár **kölcsönösen kizáró rádiógomb-szerűen** viselkedik: mindig
  csak az van engedélyezve, amelyik a MÁSIK állapotra váltana. (Ugyanez a
  mód-mező szolgálja ki más, itt nem vizsgált gombok — `0x9c8c` ha
  mód≠2, `0x9dc8` ha mód≠5 — engedélyezését is; ezek valószínűleg más
  fő nézetmódok, ld. „Ami nyitva marad".)
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
  - A menü tételeinek **engedélyezett/letiltott állapotát** kb. 9-10
    numerikus parancsazonosítóval (`0x9c8b`, `0x9cbd`, `0x9c8c`,
    `0x9dc8`, `0xa0cf`, `0x9db6`, `0x9db8`, `0x9db9`, `0x9e18`, `0x9e19`,
    `0x9e38`) frissíti, ugyanazzal a mechanizmussal, mint a `0x00574b70`
    globális UI-frissítő — ezek egy **közös "parancs engedélyezése"
    hívást** (`[0x00c40810]`) osztanak meg a teljes eszköztárral.
- **Menüegyenérték:** a `.tre` szerint a `folderviewpopup`-on
  `Property mousedown 1` áll (#885-be tartozik) — lenyomásra nyílik meg,
  nem kattintásra.
- **Amit NEM sikerült feloldani:** a fenti 9-10 numerikus azonosítóhoz
  **nincs egyező bejegyzés** a `stringres-en-hu.tsv`-ben — a pontos
  feliratszöveg (a menütételek angol/magyar szövege) ezen a forráson
  keresztül **nem dönthető el**. A tételek **létezését és a
  hatókör-kulcsok listáját** viszont a fenti bizonyíték megerősíti.

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

1. **A `folderviewpopup` menü öt tételének pontos felirata** (angol és
   magyar). A `stringres-en-hu.tsv` nem tartalmazza a `0x9c8b` stb.
   numerikus azonosítókat — vagy más táblában vannak, vagy futásidőben
   generált szöveg. **Folytatás:** a `thumbui_text.tre`-ben keresni
   `folderviewpopup` alatti almenü-feliratokat (ha van ilyen bejegyzés),
   vagy felhasználói képernyőkép a lenyíló menüről (mint a #901
   buboréksúgónál — ez itt is eldöntené a kérdést percek alatt).
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
