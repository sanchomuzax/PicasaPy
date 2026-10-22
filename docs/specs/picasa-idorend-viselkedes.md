# A Picasa Időrend-bemutatójának viselkedése (#4443, #5401)

### 38.2 Idővonal - egy közös „bemutató-mód" kezelő

A `0x9ccc` a binárisban nem jelenik meg közvetlen összehasonlításban
(ugrótáblás ág), a viselkedés viszont a `0x005e8a70`-ből olvasható. Ez a
függvény **három bemutató-módot** kezel egy helyen:

| mód | sztringek |
|---|---|
| **Idővonal** | `CThumbUI::MakeTimeline` · **„Preparing timeline…"** |
| Flipbook | `CThumbUI::MakeFlip` · „Preparing flipbook…" |
| Nagy diavetítés | `BigSlideshow2` |

Közös őre az `IDS_MUST_SELECT`, és a függvény a `thumbui/fullview`,
`editpanel/preview`, `editpanel/only_1up_toggle`, `oneup/back`
csomópontokat is kezeli - vagyis a **teljes képernyős** útra vált át. A
`thumbui/timelinebutton` név szerinti parancsága is megvan a közös
`0x005d9cc0` diszpécserben (`0x005da7ab-0x005da7ae`), de a
`thumbui.tre:472-478` ugyanennek a főablaki elemnek `m_hidden`-t és az
eltávolítási blokkot adja. ⇒ Ez **akció-belépési pont**, nem bizonyíték arra,
hogy a kiadott főablakban látható Idővonal-gombnak kell lennie.

⇒ **Az Idővonal parancs egy előkészítő szöveget használó, `oneup` bemutató-útvonalat indít; nem a mai PicasaPy év/hónap-rács útvonala.** A teljes képernyős jelleg az útvonalból és a hozzá tartozó `oneup`/overlay erőforrásokból következik, a futó ablak tényleges megjelenése itt nincs megmérve.

#### 38.2.1 Az Időrend bemutató-útja és bizonyított határai (#4443 kutatás)

**A út - utasításszintű olvasat.** A billentyűkezelő `0x005e6279` ága
ellenőrzi a `0x005696c0` őrt, majd `1` argumentummal hívja a
`0x005e8a70`-et; a `Ctrl+5` menürekordja a `0x9ccc` parancsra mutat
(`picasa-gyorsbillentyuk.md` 10.6). A `thumbui/timelinebutton` diszpécserága
(`0x005da767-0x005da7ae`) ugyanezt a kezelőt hívja. A függvényben megtalálható
a Picture Tray hibaüzenete („You must have images in the Picture Tray to do
this.”), de a szöveg jelenléte önmagában nem azonosítja a Timeline bemenetét:
a függvény több bemutatóágat kezel.

Az Időrend ág `0x005e942e`-nél a `CThumbUI+0x2c0` mező által mutatott
gyűjteménytől kér elemszámot
(`0x004a0980`), majd `0`-tól a kapott elemszámig indexelve meghívja a
`CThumbUI` vtable `+0x90` metódusát (`0x005e9490-0x005e94f1`). Ez a metódus
`0x00562cc0`-n keresztül a `CThumbUI+0x2bc` szolgáltató `+0x20` virtuális
metódusának adja át az indexet. Ez bizonyítja az indexelt bemeneti sorozat
bejárását; a szolgáltató konkrét típusa, hogy az aktuális mappa/album, teljes
könyvtár vagy Picture Tray adatait adja-e, továbbá a bejárás előtti dátum-
rendezés és a képernyőn mutatott kártyák **NINCS MEG**.

`0x005e943d-0x005e944d` a `CThumbUI::MakeTimeline` és a „Preparing
timeline…” szöveget adja át a `0x009ae560` helpernek. A helper diszasszemblálása
nem azonosít megjelenítő- vagy folyamatjelző-vezérlőt: **a szöveg bizonyított,
a tényleges folyamatjelző NINCS MEG**. A bemutató-út később meghívja a
`0x008037e0`-et, amely a `oneup/timeline` és `oneup/transtype` csomópontokat
kéri le, majd a `0x007fb210` overlay-felépítőt. Utóbbi a
`overlays/left`, `right`, `mouse`, `rollovermouse`, `exit`, `timeline`,
`timelinedot`, `sliderthumb`, `startbutton` és `overlay` nevű rétegeket tölti
be. A `oneup/timeline` gomb `0x008032e0` kattintási ága meghívja a
`0x007fda00`-et; az állapotváltás időforrást kér, a `0x00802230` átmeneti
frissítőt indítja, és állapotjelzőket állít. Az átmenet pontos képi tartalma,
végpontjai és időtartama **NINCS MEG**.

Az `oneup/prev` és `oneup/next` kattintási ág a `0x00802980`/`0x008029f0`
képlista-indexet lépteti. A OneUpUI eseménykezelő `0x00803180` kezeli a
`0x20a` egérgörgő-eseményt előző/következő ismételt hívásokkal, illetve a
`0x319` esemény 1-es alparancsát ugyanarra a kilépési visszahívási útra küldi,
mint az `oneup/exit` gombot. A `WM_KEYDOWN` (`0x100`) és `WM_KEYUP` (`0x101`)
eseményhez ez a virtuális metódus nem rendel külön műveletet; az örökölt
`0x00a52890` kezelő tartományellenőrzése is a közös kilépő ágra küldi őket. Ez
csak a OneUpUI és örökölt eseményút olvasata: a főablak globális gyorsbillentyűi
és a tényleges, futó módbeli billentyűviselkedés külön futtatási próbát igényel.

Az `oneup/exit` kattintás a `0x008032e0`-ben a OneUpUI vtable `+0x24`
metódusával elkéri a `this+0x50` objektumot, majd annak vtable `+0x14`
metódusát hívja két nulla argumentummal. A visszahívás konkrét célobjektuma
és az utána látható nézet **NINCS MEG**; a statikus híváslánc nem bizonyítja,
hogy a kilépés pontosan melyik képernyőre tér vissza.

**B út - független `respack.yt`-erőforrás-leltár.** A helyi Picasa 3.7
telepítés `runtime/respack.yt` csomagjából kinyert teljes `oneup.tre` minden
elrendezési csomópontja csoportonként: kép/alap (`oneup`, `bicubiccontainer`,
`back`, `stripback`, `centergroup`, `caption`, `dtclip`); kilépés
(`exit_icon`, `bcklabel`, `bcklabel_base`, `exit`); Időrend (`timeline_icon`,
`tllabel`, `tllabel_base`, `timeline`); lapozás/lejátszás (`prev`, `next`,
`auto`, `auto_icon`, `auto2`); forgatás/csillag (`rotateleft`, `rotateright`,
`star`); átmenet/felirat (`transtype`, `caption_icon`, `caption_yesicon`,
`captionbutton`); kijelzési idő (`plusone_icon`, `plusone`, `minusone_icon`,
`minusone`, `tps`, `tpslabel`). A `prev`/`next` `mousedown` eseményre, a
kijelzési idő `plusone`/`minusone` gombjai automatikus ismétlésre vannak
állítva. A `oneuptext.tre` mindössze három feliratot ad meg: `Timeline`,
`Exit`, `Display Time`. Ebben a két elrendezésforrásban nincs mappanév-,
albumnév-, dátumkártya- vagy dátumfelirat-definíció; ez nem zárja ki a kódban
dinamikusan felépített tartalmat.

A csomag `overlays` rétegei között van egy vékony, vízszintes
`overlays/timeline` vonal (`0x00248b99`, forrás-rect
`(197,461,442,468)`, `245×7`), egy világos
`overlays/#timelinedot` pontgrafika (`0x0024898b`, `(215,459,222,470)`,
`7×11`), egy kék `overlays/timelinedot` pontgrafika (`0x00248a97`,
`(215,462,222,470)`, `7×8`), valamint egy kerek `sliderthumb`-grafika
(`0x00248be7`, `(260,457,285,480)`, `25×23`).
A háttérréteg forrás-rectje `0x002152fb`-nél `(0,0,640,480)`. Itt két
külön erőforrásról van szó: a `oneup/timeline` a `Timeline` gomb, az
`overlays/timeline` az alsó vízszintes vonal grafikája. Ezek a
640×480-as erőforrásvászon koordinátái; a `0x007fb210` kód az overlayek
x-koordinátáját futáskor skálázza. A képek igazolják a sávot és a két pont-
grafikát, de az erőforrásnevek és a rajzolat nem bizonyítják, hogy a sáv mit
időzít, vagy hogy a fogantyú húzással mit állít.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A `0x005e8a70` indexelt szolgáltatói sorozatot jár be, majd a `0x008037e0` → `0x007fb210` oneup/overlay bemutatóútba lép. A teljes tartalom, forráshalmaz, dátumsorrend és kártyák **NINCS MEG**. | A `TimelineView.qml` év-/hónap-rács. A Nézet ▸ Időrend menüpont és `Ctrl+5` tiltott; a `timelineRequested` jelzésnek nincs bekötése, aktív eszköztárgomb nincs. | A rácsot ne tekintsük az eredeti bemutató megfelelőjének. A képek és sorrend implementációja előtt a szolgáltató típusát, a bemeneti halmazt és a dátum-/kártyamodellt kell azonosítani. |
| Az `oneup.tre` képnéző-, Exit/Timeline-, prev/next, automatikus lejátszás-, forgatás-, csillag-, átmenet-, felirat- és kijelzési idő vezérlőket sorol fel. Az overlay-rétegek között sáv, két pontgrafika és fogantyú van; a fogantyú szemantikus művelete **NINCS MEG**. | A jelenlegi rácsban nincs oneup bemutató-vezérlősáv vagy ilyen overlay. | A bizonyított vezérlők megjelenítése specifikálható; a timeline sáv tartalmát, a `sliderthumb` műveletét és a dátumkártyákat csak célzott kódkövetés vagy eredeti futtatási próba után szabad bekötni. |
| A `0x008032e0` a `timeline`, `exit`, `prev`, `next` gombokat kezeli. `0x00803180` a görgőt navigációra, az `0x319/1` eseményt az Exit útjára küldi; a sima `WM_KEYDOWN/UP`-hoz a OneUpUI út nem rendel műveletet. Az Exit konkrét visszatérési célja **NINCS MEG**. | A menü és a `Ctrl+5` tiltott; futó bemutató és teszt nincs. | A billentyűmátrixot eredeti futtatásban kell próbálni; az Exit célját a `this+0x50` objektum dinamikus típusának és callbackjének követésével kell igazolni. |
| A `thumbui/timelinebutton` akciónév létezik, de a csomagolt `thumbui.tre` rejtettnek jelöli (`m_hidden`); a súgó „Timeline view of all your photos”. | Nincs aktív főablaki Időrend-eszköztárgomb. | Az eredeti főablaki gomb láthatóságát ne következtessük ki a parancs létezéséből; ehhez futó Picasa-képernyőkép kell. |

**Cáfoló kísérlet.** Megpróbáltam cáfolni azt az értelmezést, hogy a `timeline`
sáv és a `sliderthumb` együtt fotó-/dátum-kereső csúszkát alkot. A teljes
`oneup.tre`/`oneuptext.tre` leltárban nincs hozzájuk esemény- vagy értékkötés;
a `0x007fb210` a rétegeket tölti be és az x-koordinátákat skálázza, míg
a vizsgált `0x00803180`/`0x008032e0` eseményutak azonosíthatóan a görgőt és a
megnevezett oneup-gombokat kezelik. Ez nem cáfolja, hogy közös alaposztályban
vagy másik függvényben van húzáskezelés, ezért a fogantyú funkciója nyitva
maradt. A korábbi „csak év/hónap-rács” magyarázatot a két független út
(`0x005e8a70`→oneup/overlay és az önálló erőforrás-leltár) cáfolja; ez viszont
nem dönti el a bemutató képkockáinak tartalmát.

**Bizonyítottsági fok: feltételes.** Az utasításolvasat és a `respack.yt`
leltár egyezik abban, hogy az Időrend egyedi oneup bemutatóút saját gombokkal
és alsó overlay-grafikákkal. A képi tartalom/rendezés, a sáv és fogantyú
viselkedése, a módbeli billentyűk és az Exit célja nem zárható le e két úttal.
Minden fent megadott cím, fájloffset, rect és méret bináris rekordból vagy
utasításból származik; becsült érték nincs. A `CTransTimeline` név a
film-/People Albums másik hívási láncában szerepel
(`picasa-create-features.md` 2038-2138); itt nem használtam Időrend-bizonyítékként.

**Nyitott - következő pontos lépés:**

- `Ghidra-kör kell: 0x005e8a70 - az indexelt szolgáltató konkrét típusa és forráshalmaza (mappa/album, teljes könyvtár vagy Picture Tray), a dátum szerinti rendezés, valamint a megjelenő dátum-/mappakártyák építése. [blokkoló]`
- `Ghidra-kör kell: 0x00a52890 - az örökölt UI-eseménykezelő hogyan irányítja a OneUpUI egérle/fel/mozgatás eseményeit; a sliderthumb réteghez vezet-e húzásos hit-test vagy értékkötés. [blokkoló]`
- `Ghidra-kör kell: 0x005e60d0 - a globális billentyűkezelő mely gyorsbillentyűi maradnak aktívak a OneUpUI megjelenésekor, és van-e külön billentyűút az Exithez vagy a lapozáshoz. [blokkoló]`
- `Ghidra-kör kell: 0x008032e0 - az oneup/exit által elért this+0x50 objektum konkrét típusa, a vtable +0x14 callback célja és a visszatérési nézet. [blokkoló]`
- `Ghidra-kör kell: 0x007fda00 - a Timeline gomb átmenetének tényleges vizuális tartalma, kezdő/végállapota és időzítése. [blokkoló]`
- A tényleges kártyakép, Timeline sáv állapota, a billentyűk és Exit célja: **NINCS MEG**. A statikus kör után az eredeti Picasa futó módjában célzott billentyű-/húzáspróba és képernyőkép kell; QEMU-harness csak akkor használható, ha a Picasa felületet ezen a képen megjeleníti és az inputot továbbítja.

#### 38.2.2 Futás közbeni megfigyelés, job-102 (#4443)

**Forrás:** a `job-102` 14 képernyőképe és `allapot.json`-ja (a mérőmappa nincs a repóban). Eredeti Picasa 3.9, 1280×1024, mappa: „PicasaTeszt" (24 kép, mappadátum 2026. október 6.). A felvétel lépéssora: az 1. kép után Ctrl+5, 8 mp várakozás, Right, Right, Left (3-3 mp), Space (6 mp), Escape (4 mp); minden lépés után egy kép.

**Módszer:** PIL-lel dolgoztam. A 01-02 kockát `ImageOps.autocontrast`-tal világosítottam. A 03-14 kockák legvilágosabb képpontja 8-9 a 255-ből, ezért a 03. és a 14. kockát fix, 32-szeres szorzóval is megnéztem (a `.meres-102/vilagos/` alá mentve). A kockák közötti eltérést pixelenként számoltam.

**Kockák:**

| kocka | mit mutat | eltérés az előzőhöz |
|---|---|---|
| 01 | főrács, 24 bélyeg; a bal panelen „Scanning, 71% complete" | - |
| 02 | a főrács ugyanaz; a bal panelen „Unnamed (6)" | 32 116 képpont. A bal panel változott; a rácsban is van eltérés (26 125 képpont), ennek okát nem azonosítottam. |
| 03 | fekete, teljes képernyős ablak (`qshow`): az Időrend-bemutató | a teljes kocka |
| 04-14 | a 03-mal pixelre azonos (fájlméretük is azonos: 10 017 bájt) | 0 képpont |

**A bemutató elrendezése (03. kocka, képpontban, a teljes kockán):**

- Cím: „PicasaTeszt", jobbra igazítva, `x 743-850`, `y 384-403`.
- Dátum: „October 2026", jobbra igazítva, nap nélkül, `x 762-849`, `y 417-431`.
- Bal oldali elforgatott bélyeg-halom, a cím alatt, balra; pontozott ív köti a címhez. A határait külön nem mértem le.
- Jobb oldali bélyeg: `x 797-870`, `y 583-666`. A szerepe nem ismert.
- Vezérlősáv: 4 gomb és egy csúszka.
  - Bal szélső: rács-vissza ikon, `x 348-391`, `y 676-704`.
  - Előző (bal nyíl): `x 569-596`, `y 677-705`.
  - Indító (kép és nyíl ikon): `x 619-662`, `y 676-704`.
  - Következő (jobb nyíl): a mért határoló téglalap `x 684-730`, `y 660-705`; a gomb valódi jobb szélét a szomszédos elemtől nem választottam el.
  - Csúszka: sáv `x 525-770`, `y 729-746`. A fogantyút a képről látom, `x` kb. 591-606, `y` kb. 729-745 körül; külön nem mértem.

**Sötétség:** a 03-14 kockák legvilágosabb képpontja (8, 8, 9) a 255-ből. Minden elem (cím, bélyegek, gombok, csúszka) csak a szorzott változatban látszik, az átlagfényesség 0,04 a 255-ből. A kockák között nincs változás, ezért az animáció időbeli lefutása ebből nem látszik.

**Billentyűk:**

- Egy billentyű hatása nem olvasható ki. A 03. kocka után 11 egyforma kocka van, a lépések (7 művelet) és a kockák (14) száma nem egyezik, az `allapot.json` pedig nem tartalmaz lépésfeliratot, így a kockák nem köthetők billentyűhöz.
- Escape: az utolsó (14.) kockán a `windows` listában még ott van a `qshow`. Ha az utolsó kocka az Escape után készült, az Escape nem zárta be az ablakot. A kockákból nem derül ki, hogy így volt-e, ezért ezt nem állítom.
- Aktív ablak: a 01-14 kockák mindegyikén `active.title` = „Picasa 3", a `qshow` megjelenése után is. A fókusz a főablakon maradt. Ez összhangban van azzal, hogy a billentyűk nem a bemutatóhoz érkeztek, de a kockák ezt nem bizonyítják.

**Nyitott, a következő mérés dönti el:**

1. A sötétség oka: beúszó vagy ragadt animáció (ekkor időben változna), Wine-renderelés, vagy rögzítési hiba.
2. Melyik billentyű mit csinál. Ehhez a `qshow` ablak fókuszát kell igazolni.
3. Bezárja-e az Escape a bemutatót.
4. Több mappánál mi történik (sorrend, cím, dátum). A felvétel egyetlen mappát mutat.
5. A jobb bélyeg és a fogantyú szerepe, a bal halom pontos határai.

### Eredeti | Nálunk | Teendő

| Eredeti (mért) | Nálunk (forrásból) | Teendő |
|---|---|---|
| Ctrl+5 külön, fekete `qshow` ablakot nyit; a 03. kockán az Időrend-bemutató látszik. | `Main.qml:1723-1727`: a `Ctrl+5` gyorsbillentyű `enabled: false` (1725. sor); a `toggleTimeline()` (`Main.qml:1687`) csak ebből hívódik. A menütétel (`PicasaMenuBar.qml:1160-1163`) szintén tiltott, a `timelineRequested` jelzésnek a QML-ben nincs fogadója. | A billentyű és a menü jelenleg semmit nem nyit. A bemutató megépítése után a bekötést újra kell tervezni. |
| Cím „PicasaTeszt" és „October 2026" (hónap és év, nap nélkül), jobbra igazítva. | `TimelineView.qml`: a fejléc „Timeline" felirat; a korszak-fejléc `címke (darab)` alakú. | Eltérő megjelenés és tartalom. A bemutató címe a mappanév és a dátum; nálunk nincs ilyen. |
| Bal bélyeg-halom (elforgatott), jobb bélyeg, pontozott ív. | Nincs: a `TimelineView` lapos GridView-rács. | A halmok szerepe, darabszáma és forgatása nem mért. |
| Vezérlősáv: rács-vissza, előző, indító, következő gomb; csúszka. | Nincs vezérlősáv. A `TimelineView` egy bezáró gombot (`timelineCloseButton`) és az Escape-et ismeri (`TimelineView.qml:32`). Az `onClosed` jelzés (`Main.qml:3082`) a rácsra visszaviszi a nézetet. | A gombok műveletei nem mértek; az Exit célja sem ismert. |
| Billentyűk: Right, Right, Left, Space, Escape. Egy billentyű hatása nem olvasható ki. | A `TimelineView` csak az Escape-et kezeli (`Keys.onEscapePressed`), nyíl- és szóköz-kezelés nincs. | A mérés előtt nem állítható, hogy a nyilak lapoznának. Ld. a következő mérést. |
| 03-14 kockák: sötét (átlag 0,04), változatlan. | Nincs bemutató-animáció. | Nyitott (ld. fent, 1. pont). |

**Következő mérés** (a fenti 1-5. pontot dönti el). Az A és a B a `PicasaTeszt` mintakészletet használja; a C-hez egy második mappa kell.

**A - időbeli sorozat és billentyűk.** Ctrl+5 után 1 mp-es sorozat (minden `var:1` után egy kép), majd kattintás a fekete háttér alsó részére a fókuszhoz, utána a billentyűk az eredeti sorrendben, végül Escape.

```json
[
  {"picasa": "indit"},
  {"var_ablak": "Picasa", "mp": 60},
  {"kattint": [340, 437]},
  {"var": 2},
  {"billentyu": "ctrl+5"},
  {"var_ablak": "qshow", "mp": 10},
  {"var": 1}, {"var": 1}, {"var": 1}, {"var": 1}, {"var": 1},
  {"var": 1}, {"var": 1}, {"var": 1}, {"var": 1}, {"var": 1},
  {"kattint": [640, 950]},
  {"var": 1},
  {"billentyu": "Right"}, {"var": 3},
  {"billentyu": "Right"}, {"var": 3},
  {"billentyu": "Left"}, {"var": 3},
  {"billentyu": "space"}, {"var": 6},
  {"billentyu": "Escape"}, {"var": 4}
]
```

**B - kontroll a sötétségre.** Ugyanaz az A-lépéssor, de `ctrl+4` (Slideshow) a `ctrl+5` helyett, és a sorozat után Escape. Ha a Slideshow kockái világosak, a sötétség a Timeline-hoz köthető. Ha ők is sötétek, a rögzítés vagy a Wine-renderelés a gyanús.

**C - több mappa.** Mintakészlet: a `PicasaTeszt` mellé egy második mappa más hónapból (javaslat: 2025. június, 5 kép). Lépéssor: `picasa indít`, `var_ablak Picasa 60`, `billentyu ctrl+5`, `var_ablak qshow 10`, `var 8`, `billentyu Escape`, `var 4`. Ebből látszik, melyik mappák jelennek meg, milyen sorrendben, és van-e dátumkártya.

Megjegyzés a végrehajtóhoz: a fenti `var` egysége (mp) és a `kattint` koordinátái (1280×1024) a végrehajtó kódjából ellenőrizendők a futtatás előtt; a kockák egyeztetéséhez a lépés sorszámát a végrehajtó naplójában rögzíteni kell. A `var_ablak` a `qshow` címét várja, a pontos ablakcímet az első kísérlet `allapot.json`-ja adja meg.

#### 38.2.3 Futó felmérés az eredeti Picasán (Colab #102) - mit mutat a bemutató (#4443)

**Horgony:** a mai megfelelő nézet `src/picasapy/app/qml/PicasaPy/TimelineView.qml:1`; a menüparancs `ID_VIEW_TIMELINE` (`0x9ccc`, 38.2).

**Forrás:** eredeti angol Picasa 3.9.141, Wine, 1280×1024; futás 2026-10-06 22:33 UTC. A `job-102` 14 képernyőképe és `allapot.json`-ja egy „PicasaTeszt” mappát (24 kép, október 6-i mappadátum) és egy `Recently Updated (24)` albumot tartalmaz. A koordináták a `kepernyo__03.png` képpontjaiból származnak; ez a fájl és az `allapot.json` nem található meg a helyi mérőadat-archívumban, az eredmények a korábbi kutatási ágból vannak átvéve.

| Eredeti (mért) | Nálunk (forrásból ellenőrizve) | Teendő |
|---|---|---|
| A `Ctrl+5` külön, teljes képernyős, fekete `qshow` ablakot nyit. A tartalom középre tett 640×480-as mezőben jelenik meg. | A `TimelineView.qml` az alkalmazásablakon belüli év/hónap-rács; a Nézet ▸ Időrend és a `Ctrl+5` inaktív. | A rács nem felel meg ennek a bemutató-módnak. |
| A mappanév („PicasaTeszt”, `x 743-849, y 384-405`) és a hónap/év („October 2026”, `x 759-849, y 414-430`) jobbra igazított, nap nélkül. | A rács csoportfejléce `2026. szeptember (1)` alakú. | A bemutató elemének címe a mappanév, alatta a mappadátum hónapja és éve. |
| A felirat alatti bal képhalom (`x 694-776, y 585-679`) enyhén elforgatott képekből áll; 10 pontból álló ív köti össze a felirattal (`x 740-843, y 452-564`). A jobb oldali halom (`x 796-869, y 583-665`) szerepe **NINCS MEG**. | Lapos bélyegképrács van, halom és pontozott ív nincs. | A halmok darabszámát, forgatását, ívét és a jobb halom szerepét nem szabad megbecsülni. |
| Az alsó vezérlők sorrendje: kilépés (`x 348-390, y 676-703`), előző (`x 569-595, y 677-704`), indítás (`x 619-661, y 676-703`), következő (`x 684-719, y 668-704`). | A bemutató vezérlősávja nincs meg. | A gombok megjelenése bizonyított; műveletük és visszatérési céljuk nem. |
| Az időskála vonala 245×7 px (`x 525-769, y 733-739`), a forrásgrafika 25×23 px; a látható fogantyú képpontjai `x 591-606, y 729-745`. A sáv 1:1-ben rajzolódik, a vászon `y=272` eltolásával. | Nincs időskála. | A vonal és fogantyú megjelenése bizonyított; húzásuk, a pontok jelentése és a skálavég-feliratok nem. |
| A 3-14. képkocka bájtra azonos és nagyon sötét (legvilágosabb RGB=9). | Nincs bemutató-animáció. | E felvétel nem bizonyít beúszást vagy más animációt; az animációt és időzítését külön kell mérni. |
| A `Right`, `Left`, `Space` és `Escape` próbák nem változtatták meg a képet, de az aktív ablak végig a `Picasa 3` maradt. | A bemutató billentyűviselkedése nincs tesztelve. | Ez a billentyűpróba fókuszhiba miatt érvénytelen; a módbeli billentyűk nyitottak. |
| A `thumbui/timelinebutton` parancság létezik, de a csomagolt `thumbui.tre` elrejti (`m_hidden`). | Nincs látható főablaki Időrend-eszköztárgomb. | A jegy eszköztárgombot kér, de az eredeti kiadott felületen való láthatóságára nincs bizonyíték; az eredeti erőforrás alapján ne adjunk hozzá látható gombot. |

**Bizonyítottság:** a `qshow` bemutatóablak, a felirat, a két halom és a pontozott ív, a négy gomb, valamint a sáv képi elrendezése méréssel igazolt. A `Right`/`Left`/`Space`/`Escape` eredménye érvénytelen fókusz miatt. A képkockák változatlansága nem zárja ki, hogy a felvétel az animáció előtt vagy egy Wine-korlát miatt készült.

**Nyitott, implementációt blokkoló kérdések:** a bemeneti mappák/albumok halmaza és időrendje; a kártyák teljes tartalma, a jobb halom és az időskála jelentése; a gombok műveletei és az Exit célja; a billentyűk; az animáció és a „Preparing timeline…” tényleges folyamatjelzője. A folytatáshoz a `qshow` ablakra fókuszált eredeti futtatási próba kell; eltérő dátumú második mappával a lapozás és a jobb halom is vizsgálható.

#### 38.2.4 Helyi statikus újraolvasás: qshow, vezérlők és nyitott szemantika (#4443, 2026-10-16)

Ez a kör az eredeti bináris utasításait és a helyi Picasa 3.7 telepítés
`runtime/respack.yt` erőforrásait olvassa össze. A Colab/Wine futás az első
qshow képkockán megállt, ezért abból billentyű-, kattintás-, csúszka- vagy
animációs viselkedést nem veszek át. A qemu-harness izolált függvények kézzel épített állapotú
futtatására való, nem Win32 ablak és billentyűfókusz tesztelésére; a qshow
interakciós útvonalhoz nem alkalmas.

**A qshow ablak útja.** A `CThumbUI::MakeTimeline` (`0x005e8a70`) a
`0x008037e0` bemutató-felépítőt hívja; ez létrehozza a `qshow` nevű ablakobjektumot
(`0x008038e7`, `0x00982bf0`) és meghívja az overlay-felépítőt
(`0x008039cc`, `0x007fb210`). A qshow megjelenítésekor a `0x0080398f` a
`0x00983fc0`-nak látható állapotot és `7` jelzőt ad. A helper a GWL_STYLE
mezőbe `0x96080000` értéket ír (`0x0098407e-0x0098408b`), majd a
`SetWindowPos` hívásban `HWND_TOPMOST` beszúrási pozíciót használ
(`0x009841d4-0x009841d7`). Ez keret nélküli, legfelül tartott bemutatóablak
útját bizonyítja. A `0x007fa730` a képernyő méreteit a `GetSystemMetrics`
segítségével kéri le, és a `0x280 × 0x1e0` logikai vászonméretet is beállítja
(`0x007fa73c-0x007fa767`). A képernyőn ténylegesen elfoglalt terület a
futásidejű geometria és módjelző függvénye; a helyi futás ezt nem mérte meg.

**Két, egymástól külön kezelt Időrend-elem.** A `oneup/timeline` a
`oneup.tre` gombja, felirata „Timeline”, és a `0x008032e0` kattintási ága a
`0x007fda00` állapotváltót hívja. Az `overlays/timeline` ezzel szemben az
alsó skála vonalának képe; mellette külön `timelinedot` és `sliderthumb`
rétegek vannak. A `0x007fb210` ezeket a grafikai rétegeket tölti be és
skálázza. A rétegnevek és a rajzolat nem adják meg, hogy a skála mappát,
albumot, hónapot vagy képet választ-e.

**A négy overlay-grafika.** A csomag rekordjai a következő forrás-recteket
adják meg:

| réteg | forrás-rect | mit mutat a grafika | bináris rekord |
|---|---:|---|---:|
| `overlays/exit` | `(8,404,51,432)` | bélyegkép/rács jellegű ikon és balra mutató nyíl | `0x0027ca41` |
| `overlays/left` | `(243,405,274,436)` | balra mutató nyíl | `0x0027da50` |
| `overlays/startbutton` | `(298,404,341,432)` | kép ikon és lejátszásjel | `0x0027f126` |
| `overlays/right` | `(366,405,397,436)` | jobbra mutató nyíl | `0x0027e5d4` |
| `overlays/timeline` | `(197,461,442,468)` | vízszintes skálavonal | `0x00248b99` |
| `overlays/sliderthumb` | `(260,457,285,480)` | kerek fogantyú | `0x00248be7` |

Ezek a csomag képpont-koordinátái, nem futásidejű ablakkoordináták. A
`overlays/exit`, `left`, `startbutton`, `right` sorrend a grafikák sorrendje;
a kattintási célokhoz való kötésük **NINCS MEG**. A `oneup/prev`, `next`,
`auto` és `exit` külön parancsnevek, ezért nem állítható, hogy a négy overlay
automatikusan ezeket a gombokat hívja.

**A bizonyított `oneup` parancsok.** A `oneup.tre` a `prev` és `next`
gombra `mousedown` tulajdonságot ad; a `oneup/auto` grafikai rekordja „Auto
Play” feliratú. A `0x008032e0` a `prev`/`next` nevet a
`0x00802980`/`0x008029f0` függvényre irányítja. Ezek a OneUpUI `+0x3f4`
indexét csökkentik/növelik; a következő elem elérésekor a `+0x3ec` listát és
a `+0x3f0` elemszámot használják. Tehát ez a két parancs az aktuális oneup
listában léptet. Hogy a lista eleme egy fotó, egy mappakártya vagy más csoport,
az indexelt szolgáltató típusának hiányában **NINCS MEG**.

A `oneup/auto` és `oneup/auto2` a `0x00803110` kapcsolót hívja. Ez megfordítja
a `+0x3bb` állapotjelzőt a `0x00801130` segéden keresztül, majd az
állapotfüggő frissítési útjára lép.
Ez alátámasztja, hogy a oneup sáv „Auto Play” gombja lejátszást kapcsol; nem
bizonyítja, hogy a külön `overlays/startbutton` ugyanide köt, és azt sem, hogy
a lejátszás egy kiválasztott mappát jár-e be. A `oneup/exit` a OneUpUI
visszahívási láncán lép ki (`0x008032e0`, `0x00803180`), de a visszahívás
célobjektuma és a visszaállított főablaki nézet **NINCS MEG**.

**Görgő és billentyűk.** A OneUpUI eseménykezelő `0x00803180` kezeli a
`0x20a` egérgörgő-eseményt: az iránytól függően a `0x00801210` vagy
`0x008011b0` útjára lép. Az alút a OneUpUI állapotjelzői alapján a
`0x007fd0c0` értékfrissítőt, a `prev`/`next` lapozást vagy az átmeneti
frissítést hívja. Ezért a görgő hatása módfüggő; a Timeline módban végzett
értékfrissítés jelentése **NINCS MEG**. A `0x00803180` nem rendel külön
műveletet az `Up`, `Down`, `Left`, `Right`, `Space`, `Home`, `End` vagy
`Escape` billentyűkódhoz. Az egyéb eseményeket az örökölt `0x00a52890` útjára
adja, így a származtatott kezelő olvasata önmagában nem zárja ki, hogy a
globális vagy az alap UI-út billentyűt kezeljen. A felsorolt billentyűk
qshow-beli hatása **NINCS MEG**.

**Tartalom és animáció.** A `0x005e8a70` a `CThumbUI+0x2c0` kollekciót
bejárja, a `CThumbUI` vtable `+0x90` metódusát hívva. A thunk `0x00562cc0`
a `CThumbUI+0x2bc` szolgáltató vtable `+0x20` metódusának adja át az indexet.
A konstruktor `0x005643e0` e mezőket paraméterből tölti, de a konkrét
szolgáltatótípus és a kollekció eredete nem azonosítható az itt olvasott
hívásláncból. A mappák/albumok halmaza, rendezése, a kártyanév és a dátum
forrása **NINCS MEG**. A „Preparing timeline…” karakterlánc a
`0x00c978f0` címen van; tényleges folyamatjelző-vezérlő nem azonosítható.
Az Időrend-váltás `0x007fda00` állapotváltót és `0x00802230` frissítőt hív,
de az animáció tartalma, iránya és időzítése **NINCS MEG**.

### Eredeti | Nálunk | Teendő

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A `CThumbUI::MakeTimeline` qshow bemutatóablakot és overlay-rétegeket állít fel; a logikai vászon `640 × 480` (`0x007fa730`), a qshow ablak popup/topmost stílusú (`0x00983fc0`). | A `src/picasapy/app/qml/PicasaPy/TimelineView.qml` a főablakon belüli év/hónap bélyegképrács. | Az év/hónap rács nem az eredeti bemutató. A qshow jellegű, képernyőre illesztett felületet a nyitott méret- és tartalommodell után kell megépíteni. |
| A csomag külön Exit, bal, indító, jobb, timeline-sáv és fogantyú grafikát ad; a oneup `prev`/`next` az indexelt oneup listán léptet, az `auto` automatikus lejátszást kapcsol. | A `TimelineView.qml`-ben nincs ilyen vezérlősáv; bezárás és Escape van. | A gombok képi megjelenése ismert, a négy overlay kattintási célja, a fogantyú értéke és az Exit visszatérési nézete nyitott. Ne kösd az overlay `startbutton`-t a `oneup/auto` gombhoz bizonyíték nélkül. |
| A görgő OneUpUI eseményútja ismert, a felsorolt billentyűk qshow-beli hatása és a gyűjtemények/dátumkártyák forrása nem. | A `Main.qml` `Ctrl+5` parancsának `enabled` értéke hamis; a Nézet-menü Időrend eleme szintén letiltott, `timelineRequested` jelzésének nincs QML-fogyasztója. A `MainToolbar.qml` korábbi Időrend-gombját a #1903 eltávolította. Az eredeti `thumbui.tre` a `thumbui/timelinebutton` elemen `m_hidden`-t ad (`472-478`). | A menü és Ctrl+5 bekötés csak a teljes viselkedési modell után aktiválható. Az eredeti eszköztárgomb rejtett, ezért látható gomb hozzáadása eltér az eredeti felülettől. A valódi fókuszú eredeti qshow futás és képernyőkép továbbra is szükséges. |

**Bizonyítottsági fok: feltételes.** A kódút és a független erőforrás-leltár egyezik a külön oneup bemutató, a vezérlőgrafikák, a oneup listaindexelése és az Auto Play állításain. A tartalomforrás, a dátumozás/rendezés, az overlay callbackek, a billentyűk, a kilépési cél és az animáció nem dőlt el.

**Cáfoló kör.** Azt az értelmezést próbáltam cáfolni, hogy a `prev`/`next` közvetlenül hónapot vagy mappát léptet. A `0x00802980`/`0x008029f0` az indexelt oneup lista `+0x3f4` indexét módosítja, a `oneup.tre` pedig ugyanezekre a gombokra mousedown tulajdonságot ad. Ez cáfolja, hogy a gombkezelő közvetlenül naptári hónapindexet kezel; azt nem cáfolja, hogy a listaelemek mappakártyák lennének, mert a szolgáltató típusa továbbra is ismeretlen. A cáfoló eredmény ezért a teljes „mappa vagy hónap” kérdést nem zárja le.

**Nyitott, célzott következő lépések:**

- `Ghidra-kör kell: 0x004039f0 - a CThumbUI-konstruktor +0x2bc szolgáltató-argumentumának konkrét típusa, a +0x2c0 kollekció forráshalmaza és az upstream sorrend. [blokkoló]`
- `Ghidra-kör kell: 0x00a52890 - az örökölt billentyű/egér események, a négy overlay vezérlő hit-test/callback útja, és különösen a sliderthumb húzása. [blokkoló]`
- `Ghidra-kör kell: 0x005e60d0 - a globális billentyűút működése qshow fókuszában, beleértve a nyíl, szóköz, Home/End és Escape parancsokat. [blokkoló]`
- `Ghidra-kör kell: 0x008032e0 - a oneup/exit visszahívásának konkrét célja és visszatérési nézete, valamint hogy az overlay Exit ugyanide köt-e. [blokkoló]`
- `Ghidra-kör kell: 0x00802230 - a 0x007fda00 által indított Időrend-átmenet tényleges vizuális állapota, kezdő/végállapota és időzítése. [blokkoló]`

#### 38.2.5 Ghidra-köteg: a lista és a OneUp-parancsok határa (#4443, 2026-10-17)

**Elsődleges út - Ghidra C-kód.** A 2026-10-17-i köteg `FUN_005e8a70`
teljes dekompilálását adja (`referencia/ghidra/2026-10-17-qshow-diavetites.txt`,
`CÍM 0x005e942e`). Az Időrend bemutatóág lekéri az indexelt kollekció
elemszámát (`0x004a0980`), `0`-tól végigmegy rajta, és minden indexre a
`CThumbUI` vtable `+0x90` metódusát hívja. Ugyanebben az ágban a qshow
felépítőjét (`0x008037e0`) a `0x400` × `0x300` logikai vászonértékekkel hívja.
A hurok kimenete és a qshow descriptor-bemenete közötti kapcsolat nincs
igazolva. A `0x005e8a70` ezen ágában nem látszik dátummezőt olvasó komparátor
vagy rendezőhívás; ez önmagában nem bizonyítja a descriptor upstream
sorrendjét. A qshow közvetlen bemeneti mezőjének adatútját és nyitott
kollekciójelentését a 38.2.63 §1 rögzíti.

**Második út - helyi diszasszembly és RTTI.** A `0x005e942e-0x005e94f1`
utasításai ugyanezt az elemszám → indexhurok → vtable `+0x90` láncot mutatják.
A `0x00562cc0` thunk a `CThumbUI+0x2bc` objektum vtable `+0x20` helyére
továbbít. Az RTTI szerint a `CThumbDB` vtable `+0x20` bejegyzése
`0x00423300`, és a Ghidra-köteg ezt a függvényt is indexparaméterrel működő
adatlekérdezőként dekompilálja. A 38.2.63 §1 külön megerősíti, hogy a
`CThumbUI+0x2bc` mezőbe tett objektum `CThumbDB`; ez nem azonosítja a qshow
`CThumbUI+0x2c0` bemeneti mezője mögötti kollekciót, és nem bizonyítja, hogy
az indexhurok kimenete a qshow descriptor-listája.

**A léptető és az Auto Play.** A `0x008032e0` `oneup/prev` és `oneup/next`
ágai rendre a `0x00802980` és `0x008029f0` függvényeket hívják. Ezek az
OneUpUI `+0x3f4` indexét csökkentik/növelik, és a következő elemhez a
`+0x3ec` listát, illetve a `+0x3f0` elemszámot használják. A külön
`oneup.tre` erőforrás a két gombnak `mousedown` eseményt ad. Az `oneup/auto`
és `oneup/auto2` a `0x00803110` → `0x00801130` útvonalon a `+0x3bb` bájtot
0/1 között váltja, majd állapotfüggő frissítést indít; az erőforrás felirata
„Auto Play”. Az utóbbi két állítás kód- és erőforrás-útja egymástól külön
származik.

Az `oneup/exit` ág egy OneUpUI vtable `+0x24` hívásból kapott objektum
vtable `+0x14` metódusát hívja két nulla argumentummal. A callback célobjektuma
nem azonosítható az ág utasításaiból. A `overlays/exit` és a bal oldali
rács-vissza ikon hit-test/callback kötése sincs meg, ezért nem állítható, hogy
ez a `oneup/exit`-et hívja. A `oneup/oneup` elem neve szintén nem bizonyít
rács-vissza műveletet.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a qshow saját dátumsorrendet
épít. A teljes `FUN_005e8a70` dekompilált ágát és a megfelelő gépi kód
indexhurok-részét átnéztem dátummező-, komparátor- vagy rendezőhívásért; ilyen
lépés nincs a bemutatóágban. Ez csak a rendezés qshow-beli létrehozását
cáfolja, nem az upstream kollekció korábbi rendezését.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Egy bináris adatút szerint a qshow közvetlen bemenete a `CThumbUI+0x2c0` mezőből származik (**feltételes**); a `0x008018a0` a kapott descriptor elemeit sorrendben fűzi a oneup listába. A kollekció jelentése, elemlistája és upstream sorrendje nyitott. A `prev`/`next` a oneup listán léptet, az Auto Play állapotot vált. | `TimelineView.qml` év/hónap rács, nem qshow; a menü és Ctrl+5 letiltott, a QML-ben nincs qshow-vezérlősáv. | A bemutatót külön, teljes képernyős módként kell specifikálni. A `+0x2c0` mögötti kollekciót és a sorrendet további feltárásig ne nevezd meg. A rács-vissza és Exit bekötését csak a callback céljának feltárása után add meg. |
| A parancsnév `thumbui/timelinebutton` megvan, de a `thumbui.tre` elem `m_hidden`; a 2026-10-17-i út nem igazolt látható fejlécgombot. | Nincs aktív Időrend-eszköztárgomb. | A menü és Ctrl+5 újraaktiválása megfelel a jegynek; látható eszköztárgomb az eredetivel való paritásban nem bizonyított, ezt termékdöntésként külön kell kezelni. |

**Bizonyítottsági fok: feltételes.** A `CThumbUI+0x2bc` Flipbook-szolgáltató útját a kód és RTTI egymástól függetlenül alátámasztja; a qshow `CThumbUI+0x2c0` bemeneti lánca egy statikus bináris adatútból ismert, szemantikája nyitott. A parancsok egy része célzott diszasszemblyből és erőforrás-nevekből követhető, de a qshow billentyűi, az overlayek kattintási céljai, a rács-vissza, az Exit visszatérési nézete, a kártyák tartalma/sorrendje és a tényleges animáció továbbra sincs eldöntve.

**Nyitott:**

- `Ghidra-kör kell: 0x004039f0 - a CThumbUI-konstruktor +0x2bc szolgáltató-argumentumának konkrét típusa, a +0x2c0 kollekció forráshalmaza és upstream sorrendje. [blokkoló]`
- `Ghidra-kör kell: 0x00a52890 - az örökölt egér/billentyű eseményút, az overlay exit/left/startbutton/right hit-testje és a sliderthumb húzási értékkötése. [blokkoló]`
- `Ghidra-kör kell: 0x005e60d0 - a qshow láthatósága alatt elérhető globális gyorsbillentyűk és a Ctrl+5/nyilak/szóköz/Escape útja. [blokkoló]`
- `Ghidra-kör kell: 0x008032e0 - az oneup/exit callback konkrét célobjektuma és visszatérési nézete; az oneup/oneup rács-vissza szerepe. [blokkoló]`
- `Ghidra-kör kell: 0x00802230 - az Időrend-átmenet tényleges képi tartalma és időzítése. [blokkoló]`
- A mappák/albumok forráshalmaza és upstream sorrendje, a cím-/dátumkártyák, a futó billentyűviselkedés és az Exit utáni nézet: **NINCS MEG**.

#### 38.2.6 Második Ghidra-köteg: a 38.2.5 nyitott pontjainak mérése (#4443, 2026-10-17)

**Forrás és módszer.** A `referencia/ghidra/2026-10-17-qshow-2.txt` öt címe (`0x004039f0`, `0x00a52890`, `0x005e60d0`, `0x008032e0`, `0x00802230`) és az első köteg `FUN_005e8a70` dekompilátuma (`2026-10-17-qshow-diavetites.txt`). Két független úton ellenőriztem: (A) a `0x005e8a70` helyi diszasszemblálása (`annot_disasm.py`, a munkafa `.bt/` mappájában, a repón kívül), (B) a bináris-index (függvénytábla, RTTI, hívóélek), (C) a `Picasa3.exe` közvetlen olvasása (vtable-slotok, konstansok). A címek a `Picasa3.exe` virtuális címei.

##### 1. Lista forrása és sorrendje

- **Bizonyított: üres listánál nem indul a bemutató.** A `0x005e8a70` mód-1 ágában a `FUN_005d2a70()` és a `[this+0x2c0]+0x154` (0 vagy 1) ellenőrzése után, valamint a függvény végén, ha az összegyűjtött tömb (`uStack_d0`) üres, az `IDS_MUST_SELECT` üzenettel tér vissza. A `0x008037e0` (a qshow-építő) csak ezután hívódik, és egyetlen hívója van: a `0x005e8a70`. (dekompilátum + diszasszembly)
- **Bizonyított: a tömb CSAK a Flipbook + Ctrl + Shift ágban töltődik.** A feltételek: `Preferences\Flipbook` kulcs, `GetAsyncKeyState(0x11)` és `(0x10)`, valamint az aktív ablak (`DAT_00d67849`). A forrás `[this+0x2bc]` (a szolgáltató), az elemszám `[+0x4ec] >> 1`, a rekord elérése `+0xf8` (`0x004edf60`). A rekord típuskódja szerint szűr: 2, 3, 6, 7, 13, 14, 18, 22, 24, 26, 27, 28, 31 (a kódok jelentése **NINCS MEG**). A sorrend **fordított**: az elemszám-1 indextől 1-ig, a 0. elem kimarad. (dekompilátum + diszasszembly)
- **Ellentmondás (mérve):** Shift nélkül, a Flipbook beállítástól függetlenül, a tömb üres marad, tehát a mód-1 ág `IDS_MUST_SELECT`-re fut, nem qshow-ra. ⚠️ **HELYESBÍTVE (38.2.8):** ez téves: a `0x007164b0` Shift nélkül is tölt, a `[this+0xeac]` elemeiből. Az eredeti (téves) indoklás: a tömb-slotok (`[esp+0x2c]`, `[esp+0x30]`, `[esp+0x40]`, `[esp+0x44]`) íróhelyei ezt mutatják: a nullázás (`0x005e8dc1`-`0x005e8dcd`) után csak olyan írások vannak, amelyek a már üres `local_c0`-ból másolnak (`0x005e9178`-`0x005e929a`). **Ez nincs összhangban a 38.2.2 megfigyelésével** (job-102: Ctrl+5 után qshow látszott). Lehetséges magyarázat: a felvételen Shift volt lenyomva, ez nincs rögzítve.
- **Pontosítva (38.2.63):** a `0x004039f0` a főablakot (`ytFrameWindow`, vtable `0x00cd95c0`) és egy 0x3710 bájtos objektumot hoz létre; a `0x005643e0` konstruktora `CThumbUI::vftable`-t ír, így az objektum `CThumbUI`. A `FUN_0040bf70` tölti, de a rácslista forrása nincs igazolva. Egy statikus bináris adatút szerint a qshow bemenete a `CThumbUI+0x2c0` mezőből származik (**feltételes**); a mező mögötti kollekció jelentése nyitott.
- **Nyitott: a „Preparing timeline…” ciklus kimenete.** A ciklus (`0x005e8a70`, dekompilátum 1215-1259. sor) `FUN_004a0980()` elemszámon megy 0-tól felfelé, és minden indexre a `this->vt+0x90` hívást végzi, elemenként a `piStack_6c` folyamatjelző-objektumnak adva. Hogy ez-e a qshow listája, nincs igazolva.

##### 2. Vezérlők és billentyűk

- **`0x008032e0` (oneup esemény, kattintás = `0x8000004`): megerősített, tizenkét név.** A kód név-összehasonlítással választ: `captionbutton` (felirat-váltás, `0x009cd730` / `0x009cd760`), `plusone` / `minusone` (`0x00802ff0`, `+1,0` / `-1,0`; a `-1,0` a `0x00cf3ed0`-ban), `auto` / `auto2` (`0x00803110`, automatikus lejátszás), `timeline` (`0x00802be0`, majd `0x007fda00`), `exit` (lásd 3.), `prev` / `next` (`0x00802980` / `0x008029f0`, az indexet lépteti), `rotateright` / `rotateleft` (`0x00a60920` 1, illetve 0, vt+8 hívás, `0x00802e20`), `star` (vt+4 hívás a `[esi+0x359]` jelzővel).
- **Billentyűk: erős.** A `0x005e60d0` (a főablak billentyű-kapcsolója, a `0x005e6710` hívja) switch-listája: `0x0D` (Enter), `0x30`-`0x33`, **`0x34` és `0x35` (`4`, `5`) → `0x005e8a70(this, 0)`, illetve `(this, 1)`**, továbbá `0x36`, `0x38`, `0x39`, `0x41`-`0x59` (betűk), `0x75`-`0x78` (F6-F9). **Nincs eset** Esc (`0x1B`), Space (`0x20`), End/Home (`0x23`/`0x24`) és a nyilak (`0x25`-`0x28`) számára: a főablak kapcsolója ezekre nem ad műveletet. Ez egyezik a 38.2.2-es fókuszhibával.
- **Egér és görgő: megerősített.** A `0x00a52890` switchében nincs billentyű-eset (`0x100`/`0x101` nincs). Bal gomb (`0x201`): találat-kereső (`0x009e4630`) és `SetCapture`. Görgő (`0x20a`): a `0x00a516c0` a delta / 120 értéket kapja (`0x00cf4640` = 120, a WHEEL_DELTA). A OneUp saját kezelője (`0x00803180`, 38.2.4) léptet.
- **A `sliderthumb` húzása: NINCS MEG.** A találati elem kezelője a `0x0052d3c0` és a `0x009e4630` körül van, és nincs a kötegben.

##### 3. Exit és rács-vissza célja

- **Mechanizmus: megerősített (diszasszembly + vtable-olvasás).** `oneup/exit` → `this->vt+0x24()` → `0x00a6ccf0`: `mov eax,[ecx+0x50]; ret`, vagyis az objektum `[this+0x50]` mezőjét adja vissza → annak `vt+0x14(0, 0)` hívása. A `+0x50` mezőt a `vt+0x28` (`0x00a6cd00`: `mov [ecx+0x50], arg`) állítja. A CThumbUI vtable (`0x00c9052c`) +0x24 slotja ugyanez a getter.
- **Ha a tulajdonos CThumbUI, az Exit üres.** Ekkor a `vt+0x14` = `0x00b0d990`, amely csak `ret`. Vagyis az Exit ilyen tulajdonosnál nem végez műveletet. A tényleges tulajdonos osztálya **NINCS MEG**: a `vt+0x28` hívásai indirektek, az index nem látja őket. A `OneUpUI` vtable-jét (`0x00cbd5c4`) író konstruktort kell megkeresni.
- **Rács-vissza = `oneup/exit`: feltételes.** A bal alsó ikon (képernyő-x 348-391) az `overlays/exit` réteghez hasonlít (forrás-rect `(8,404,51,432)`, rács és nyíl), a `oneup.tre` kilépés-csoportja (`exit_icon`, `bcklabel`, `exit`) pedig ugyanerre a gombra utal. A kötés (hit-test) az `exit` elemhez a respack-geometria mérése nélkül nincs igazolva. A `oneup/oneup` nevet a `0x008032e0` nem kezeli: az a képalap elem.

##### 4. Átmenet

- **Időrend-váltás (`0x007fda00`): megerősített lépéssor (diszasszembly).** Kapuk: `[this+0x2d8]` (bájt) és `[this+0x538]` (mutató). Az aktuális index (`[this+0x3f4]`) negatív esetén 0. A QPC-érték a `[this+0x430]`-ba (double) kerül, majd **`0x00802230(this, 1)`** hívódik: a `param_2 = 1` nem animált ágat jelez. Végül `[+0x3b8]=1`, `[+0x3b9]=1`, `[+0x3ba]=0`, `[+0x3bb]=0`. A flagek jelentése **NINCS MEG**.
- **A `0x00802230` a következő elem ugrása véletlen eltolással: megerősített képlet.** Az elem `[this+0xfb][[this+0xfd]]`. Ha `([this+0xfc] >> 1) <= [this+0xfd]`, a visszatérés 4 (vége). Két `rand()` hívás (CRT, `0x00c08221`) ad egy-egy 15 bites `t = r / 32768` értéket. Az új eltolás: x = W · 0,15 · t_x, y = H · 0,5 · 0,15 · t_y, ahol W = `[this+0x11d]`, H = `[this+0x11e]` (a középre igazítás is ezekből számol). A konstansok a binárisban: `0,15` (`0x00cf4320`, double), `0,5` (`0x00c72150`, double). Az előző eltolás `[+0x102]`/`[+0x103]`-ban marad.
- **Nem animált ág (`param_2 ≠ 0`): a kódalak megvan, a viselkedés NINCS MEG.** Ekkor `local_58 = 0` és a `0x00802180` hívódik. Az animátor (`[+0xb8]+4`) viselkedése nincs megmérve. **Helyesbítve (38.2.7):** a `0x00802180` nem animációs ág, hanem a `Preferences\CarefulEnhance` beállítás frissítése.
- **Időtartam: NINCS MEG.** A `ROUND(_DAT_00d35808)` a `[+0xb9]` ágon van. A `0x00d35808` a `.data` szakaszban van (írható), a fájlban lévő bájtok nem fordítási idejű konstansok (f64-ként 7,18·10^-305). Az íróhely nincs az indexben: az `xrefs` táblában a hívások szerepelnek, adat-hivatkozás nem.
- **A véletlen seed-je: NINCS MEG** (a `srand` hívását nem vizsgáltam), így az eltolás nem reprodukálható.

##### Bizonyítottsági fok

| állítás | fok | alap |
|---|---|---|
| üres tömb → `IDS_MUST_SELECT`, nem qshow (mód-1, Shift nélkül) | megerősített | dekompilátum + diszasszembly (tömb-slotok) |
| a lista csak Flipbook + Ctrl + Shift ágban töltődik, fordított sorrend | megerősített | dekompilátum + diszasszembly |
| Ctrl+5 → qshow | **feltételes** (38.2.8) | a korábbi „Shift nélkül nem ad qshow-t” téves; a kód Shift nélkül is adhat qshow-t, ha K1/K2/K4 teljesül; a 38.2.2 megfigyelés összefér vele |
| billentyűtérkép (`0x005e60d0`) | erős | teljes switch-lista, nincs nyíl/Esc/Space eset |
| az Exit mechanizmusa (`this+0x50` → `vt+0x14`) | megerősített | diszasszembly + vtable-olvasás |
| az Exit célja (a tulajdonos osztálya) | NINCS MEG | indirekt `vt+0x28` hívások |
| rács-vissza = `oneup/exit` | feltételes | képi és névbeli egyezés, geometria nincs mérve |
| eltolás-képlet (0,15 · W; 0,5 · 0,15 · H; rand / 32768) | megerősített | dekompilátum + `pefile`-olvasott konstansok |
| időtartam, seed, animátor | NINCS MEG | futásidejű `.data` változó, nincs író az indexben |

**Két független út:** a lista-kapunál a dekompilátum és a helyi diszasszembly egyezik; az Exit-mechanizmusnál a diszasszembly és a vtable-olvasás; a konstansoknál a dekompilátum és a `pefile`-olvasás.

##### Cáfoló kísérletek

1. „A Ctrl+5 normál ága qshow-t nyit.” **Cáfolva a kódból** (a tömb üres, `IDS_MUST_SELECT`). Ez ellentmond a 38.2.2 megfigyelésének; a két állítás egyike téves, vagy Shift volt lenyomva. Ez nincs eldöntve.
2. „Az Exit a rácsnézetbe visz.” **Nem igazolt, részben cáfolt:** CThumbUI-tulajdonosnál a hívott `0x00b0d990` üres, így a visszatérés nem ebből az ágból jön.
3. „Az Időrend-váltás animált.” **Nem igazolt:** a `0x007fda00` `param_2 = 1`-gyel hívja a `0x00802230`-at, ami nem animált ágat jelez; az animátor viselkedése nincs megmérve.

##### Mérleg a 38.2.5 nyitott pontjairól

| 38.2.5 pont | állapot |
|---|---|
| lista forrása és sorrendje | **részben zárva**: a flipbook-ág forrása és sorrendje megvan; a normál ág ellentmond a 38.2.2-nek |
| vezérlők és billentyűk | **részben zárva**: név → művelet és billentyűtérkép megvan; a `sliderthumb` húzása nyitott |
| Exit és rács-vissza célja | **részben zárva**: a mechanizmus megvan; a célobjektum osztálya nyitott |
| átmenet | **részben zárva**: az eltolás-képlet és az Időrend-váltás lépései megvannak; az időtartam nyitott |

**Nyitott kérdések: 0 nyílt · 0 lezárva · 9 blokkolt · 0 hatókörön kívül · 0 csak-nyitva.** A 38.2.5 öt Ghidra-kérdéséből négy részben zárult; a maradék a lenti tételekben van.

##### Nyitott (a hívó futtatja, fontosság szerinti sorrendben)

- `Ghidra-kör kell: 0x00a52890 - a találati elem (sliderthumb) húzási kezelője: a 0x0052d3c0 eseményhívás és a 0x009e4630 találat-kereső célja, az értékkötés. [blokkoló]` **Részben (38.2.7):** a bal gombos ág és a `SetCapture` megvan; az értékkötés a `0x0052d430` alatt nyitott.
- `Ghidra-kör kell: 0x008037e0 - a qshow ablak létrehozása: WndProc, és melyik ablak kapja a billentyűket (nyíl, Esc). [blokkoló]` **Részben (38.2.7):** a fókusz a `obj+0x6c` HWND-re kerül; a WndProc a `0x00983670` alatt nyitott.
- ~~`Ghidra-kör kell: 0x00802180 - a 0x00802230 param_2 ≠ 0 (nem animált) ágának célja. [blokkoló]`~~ **LEZÁRVA (38.2.7):** nem animációs ág, a `Preferences\CarefulEnhance` beállítást olvassa.
- `Ghidra-kör kell: 0x004edf60 - a rekord típuskód-mezője (a 4. mező): a 13 kód (2, 3, 6, 7, 13, 14, 18, 22, 24, 26, 27, 28, 31) jelentése. [blokkoló]` **A mező olvasása kész (38.2.7); a kódok jelentése örökölt (paszta-kör).**
- ~~`Ghidra-kör kell: 0x00415500 - a Preparing ciklus folyamatjelző-objektuma (piStack_6c) és a vt+4 hívás célja: a ciklus kimenete. [blokkoló]`~~ **LEZÁRVA (38.2.7):** `ytProgress`-konstruktor; a ciklus a `0x005e8a70`-ben van.
- **Eredeti futtatás (Colab-gép, nem Ghidra):** Ctrl+5 Shift nélkül, a Preferences\Flipbook be- és kikapcsolva, a billentyű-állapot naplózva; rögzítendő a qshow vagy az `IDS_MUST_SELECT` üzenet. Ez dönti el a 38.2.2 ellentmondást. [blokkoló]
- **Paszta-kör (gépi, a teljes .text-keresés csak a `paszta.py`-n át):** (a) a `0x00cbd5c4` (OneUpUI vtable) írója, a konstruktor, amely megmondja a `+0x50` tulajdonos osztályát; (b) a `0x00d35808` íróhelye (az időtartam). [blokkoló]
- **Respack-kör (gépi):** az `overlays/exit` és az `oneup/exit` elemek geometriájának összevetése a képernyő-x 348-391 gombbal (rács-vissza kötés). [blokkoló]

#### 38.2.7 Harmadik Ghidra-köteg és a Ctrl+5 ellentmondása (#4443, 2026-10-17)

**Forrás és módszer.** A `referencia/ghidra/2026-10-17-qshow-3.txt` hat címe (`0x00a52890`, `0x008037e0`, `0x00802180`, `0x004edf60`, `0x00415500`, `0x0052d3c0`) és a `2026-10-17-qshow-diavetites.txt` (`FUN_005e8a70`) dekompilátuma. Két független úton ellenőriztem: (A) a dekompilátum, (B) a helyi diszasszembly (`annot_disasm.py`; a kimenet a munkafa `.bt/` mappájában volt, a repón kívül, a kör végén törölve). Kiegészítésként a billentyű-ugrótábla bájtjait (`pefile`) és a bináris-index hívóéleit néztem meg. A `Picasa3.exe` PE-verziója `3.9.141.259`, a fő verzió egyezik a Colab-gépen futó angol Picasáéval (3.9.141).

**Bizonyítottsági fok**

| állítás | fok | alap |
|---|---|---|
| a menü és a Ctrl+5 ugyanazt a `0x005e8a70(this, 1)` hívást indítja | megerősített | A + B + ugrótábla-bájtok |
| Shift nélkül nincs qshow (mód 1) | megerősített | A + B, írás-elemzés |
| a felvétel (Ctrl+5 kijelölés nélkül qshow) egyezik-e a kóddal | feltételes: összeférhető (38.2.8) | a 188-as kép nincs a munkafában |
| qshow-építő: mód-ág, fókusz-HWND | megerősített | A + B |
| `0x00802180` = `CarefulEnhance`-frissítés | megerősített | A |
| `0x00415500` = `ytProgress`, `0x0052d3c0` = `ytUIEvent` | megerősített | A |
| WndProc, csúszka értékkötés, rekord-típuskódok | nyitott | a kötegen kívül |

**1. Az útvonal.**
- A menü (`thumbui/timelinebutton`) és a billentyű ugyanazt a hívást indítja. A nevet a `0x005d9cc0` elosztó kezeli: a `thumbui/timelinebutton` ága `push 1` (`0x005da7ae`), a `thumbui/sbutton` ága `push 0`.
- A billentyűkapcsoló (`0x005e60d0`) ugrótábla-bejegyzése szerint a `4` a `0x005e625e` (mód 0), az `5` a `0x005e6279` (mód 1) ágra megy. A Ctrl+5 tehát mód 1.

**2. A mód-1 ág kapuja.**
1. `0x005d2a70()` nem nulla, és a `[this+0x2c0]+0x154` mező nem 0 és nem 1 (`0x005e8dd6`-`0x005e8dee`). Ha nem, IDS_MUST_SELECT (`0x005e983e`).
2. A tömb feltöltésének egyetlen útja: a Preferences\Flipbook igaz, az aktív ablak (`DAT_00d67849`) igaz, a Ctrl (`GetAsyncKeyState(0x11)`) és a Shift (`GetAsyncKeyState(0x10)`) egyszerre lenyomva (`0x005e8e28`-`0x005e8e6f`). Ekkor a rekordtár fordított sorrendű bejárása tölti a tömböt (`0x005e8e75` kezdettől).
3. A tömb elemszáma `[esp+0x30]` (`uStack_d0`). A qshow-építő (`0x005e9787`) csak akkor hívódik, ha ez legalább 1 (HELYESBÍTVE, 38.2.8: a kódolt érték 2·n + jelző, tehát n ≥ 1 elég): `0x005e95e6` `test [esp+0x30], 0xfffffffe`; különben IDS_MUST_SELECT (`0x005e97ce`).

**3. A nem-Flipbook ág nem tölt (megerősített, írás-elemzés).** A másolás forrása a `[esp+0x40]` lista-mutató, amelyet a mód-1 ág NULL-ra nulláz (`0x005e8dc1`). A másolási számlálót (`[esp+0x44]`) csak nullázás írja (`0x005e8dc5`, `0x005e8e09`). A Preferences-kulcsot felépítő `0x00407a20` a `[esp+0x50]` objektumba ír, a `0x009c84a0` pedig a `[esi+4]` és `[esi+8]` mezőket nullázza. A `[esp+0x30]` írói (`0x005e8f97`, `0x005e91a3`, `0x005e9274`) a Shift-ágban vagy számláló-függő ciklusokban vannak. Ellenpélda nincs: a Shift nélküli ág üres tömbbel IDS_MUST_SELECT-re fut.

**4. A mért ellentmondás.** A kód szerint Shift nélkül nincs qshow. A 38.2.2 (job-102) és a jegy 188-as Colab-felvétele szerint Ctrl+5 kijelölés nélkül qshow nyílik: mappanév és dátum jobbra fent, mappakártyák, alul rács-vissza, előző / lejátszás / következő, csúszka, és az Escape nem zárja be. A 188-as kép nincs a munkafában (a legfrissebb képtári fájl 2026. október 1-jei), ezért a leírást a kör feladatából vettem, a képet nem láttam.

**Ítélet.** ⚠️ **VISSZAVONVA (38.2.8):** a „Shift nélkül nincs qshow” állítás téves. A kód-olvasat többi része megerősített. A felvétel és a kód viszonyát a 38.2.8 rendezi: összeférhetők, a K1, K2 és K4 kapu futásidejű értékétől függően.

**5. A többi cím (Ghidra-köteg, 2026-10-17-qshow-3).**
- **`0x008037e0` (qshow-építő): megerősített.** A `Preferences\BigSlideshow2` kulcsot olvassa. A paraméter-struktúra 1. bájtja (a hívó módja, a `0x005e8a70` `[ebp+0xc]`-je) dönti el az ágat: mód 0 → `0x00801cf0`; mód 1 → `0x007fda00` (Időrend-váltás), majd `0x00802060`, ha `[obj+0x3bf] == 0` (`0x008039de`-`0x008039fb`). A billentyűfókuszt `SetFocus(obj+0x6c)` adja. A `+0x6c` mező HWND, ugyanez a mező az egérfogásban is (`SetCapture(param_1[0x14]+0x6c)`, `0x00a52890`). Az ablak osztálya és WndProc-ja nincs a kötegben: a `0x00982bf0` a `0x00983670`-et hívja, az a létrehozó hely.
- **`0x00802180`: LEZÁRVA. A 38.2.6 „nem animált ág" címke téves.** A `Preferences\CarefulEnhance` beállítást olvassa, beállítja az `obj+0x46c` mezőt (`0x009db610`), majd `0x00aa40a0` és `0x009ab410` hívásokat végez. Nem animációs ág. Az átmenet animátora (`0x00802230`) nyitott.
- **`0x004edf60` (rekordolvasó): a szerep LEZÁRVA, a típuskódok jelentése nyitott.** A `param_1[0xfc]` mutatótömbből olvas, és a 4. mezőt (`+0x18`) adja vissza. A `0x3e9` (1001) indirekció: a `+0x20` indexű rekordra ugrik, a `0xffffffff` azt jelenti, hogy nincs tovább. A 2, 3, 6, 7, 13, 14, 18, 22, 24, 26, 27, 28, 31 jelentését a rekordot író kód adja, az nincs a kötegben.
- **`0x00415500`: LEZÁRVA.** `ytProgress` (folyamatjelző) objektum konstruktora: vtable, számláló nullázása, a szöveg másolása (`0x00985ff0`), majd `0x00415380` hívása. A ciklus a `0x005e8a70`-ben van: az elemszám a `0x004a0980`-tól jön (`0x005e9434`), a szöveg `Preparing timeline...` (ASCII, három ponttal; bináris cím `0x00c978f0`, a hívó `0x005e9442`).
- **`0x0052d3c0`: LEZÁRVA.** `ytUIEvent` konstruktora; a paraméter az eseménytípus (a bal gombos lenyomás ága az `1`-et adja, `0x00a52890` `0x201`-ág). A találat-kereső (`0x009e4630`) visszatérése 1000000 (`0x000f4242`); a hívó ezt találatként kezeli.
- **`0x00a52890` (egér-kapcsoló): részben.** A `0x200`, `0x201`, `0x202`, `0x20a` ágak megvannak; találatkor a kattintott elem HWND-jére `SetCapture` kerül. A csúszka értékkötését az eseményt továbbító `0x0052d430` végzi, az nincs a kötegben.

**6. Cáfoló kísérletek.**
1. „Van más író, ami Shift nélkül tölti a tömböt." Megdőlt: a `[esp+0x30]` összes írója a Shift-ágban vagy számláló-függő ciklusban van; a Shift nélküli ágon a `[esp+0x40]` NULL, a `[esp+0x44]` nulla.
2. „A `copy_Picasa_3_7` mappanév miatt a bináris más verzió, mint a felvételen." Megdőlt: a PE-verzió 3.9.141.259, a fő verzió egyezik.
3. „A `0x00802180` az átmenet nem animált ága." Megdőlt: `CarefulEnhance`-frissítés.
4. „A `0x00415500` a Preparing-ciklus." Megdőlt: folyamatjelző-konstruktor, a ciklus a `0x005e8a70`-ben van.

**7. Kész, ha (a jegy pontjai).**
- ⛔ a spec leírja a bemutató működését, bizonyítékkal: **részben.** Megvan az indítási útvonal, a kapuk, a fókusz-HWND és az átmenet lépéssora. Nincs meg az ablak WndProc-ja, a billentyűk, a csúszka, az Exit célja, az időtartam és a kártyák tartalma.
- ⛔ Nézet ▸ Időrend és Ctrl+5 kattintásos teszttel: **nincs.** Ebben a körben kódot nem írtam (`src/`, `tests/` érintetlen).
- ⛔ képernyőkép az eredetivel összevetve: **nincs.** Nincs implementáció, és a 188-as kép nincs a munkafában.

**8. Codex-kész lista: nem adható.** A viselkedés nem dőlt el: a Ctrl+5 kiváltó feltétele ellentmondásos, a billentyűk, a csúszka és az Exit nincs megmérve. Egy fejlesztői lista most feltevésekre épülne. Előfeltételei: (a) a Ctrl+5 kettős olvasatának feloldása (188-as billentyű-napló), (b) a qshow WndProc-ja (`0x00983670`), (c) a csúszka kezelője (`0x0052d430`), (d) az Exit tulajdonos-osztálya (paszta).

**9. Nyitott (a hívó futtatja).**
- **Blokkolt:**
  - **Eredeti futtatás (Colab-gép, nem Ghidra):** a 188-as futás billentyű-naplójának ellenőrzése (volt-e Shift a Ctrl+5 pillanatában), vagy új Ctrl+5 futás Shift-naplóval, a Preferences\Flipbook be- és kikapcsolva. [blokkoló]
  - `Ghidra-kör kell: 0x00983670 - a qshow ablak létrehozása (CreateWindowEx) és az ablakosztály WndProc-ja: melyik HWND kapja a nyíl-, szóköz-, Home/End- és Escape-billentyűket. [blokkoló]`
  - `Ghidra-kör kell: 0x0052d430 - HELYESBÍTVE (38.2.8): nem továbbító, hanem `ytUIEvent`-vtábla-beállító; a csúszka-kezelést a `0x00a52890` vezérlőkezelő viszi tovább. [blokkoló]`
- **Örökölt (gépi, nem ebben a körben kérdezve; a munkasorba):** (a) a rekordtípus-kódok írója (`0x004edf60` rekordtára, paszta); (b) az Exit tulajdonos-osztályának írója, `0x00cbd5c4` (paszta); (c) az átmenet időtartamának íróhelye, `0x00d35808` (paszta); (d) az `overlays/exit` és `oneup/exit` geometriája (respack); (e) az átmenet animátora, `0x00802230` (Ghidra vagy diszasszembly); (f) a gyűjtemény forrása, `0x004039f0` (`+0x2bc` szolgáltató, Ghidra).

**Nyitott kérdések mérlege:** 6 nyílt (örökölt, a munkasorba) · 5 lezárva · 3 blokkolt · 0 hatókörön kívül · 0 csak nyitva.

Lezárva ebben a körben: a `0x00802180` szerepe; a `0x00415500` szerepe; a `0x0052d3c0` szerepe; a `0x008037e0` mód-ága és fókusz-HWND-je; a másolási számláló értéke a Shift nélküli ágon.

#### 38.2.8 Negyedik kör: a Ctrl+5 normál útja, a Shift-állítás visszavonva (#4443, 2026-10-17)

**Kérdés.** Melyik út vezet a `0x005e8a70` mód-1 ágához, és mely kapuk döntik el, hogy a Ctrl+5 megnyitja-e a qshow-t? A 38.2.6-38.2.7 szerint a Shift nélküli ág üres listával `IDS_MUST_SELECT`-re fut; a 188-as felvétel szerint kijelölés nélkül qshow nyílik.

**Forrás és módszer.** (A) A `0x005cb990` ID-switch táblái a `Picasa3.exe` PE-jéből olvasva (`pe_dis.read`, csak olvasás); a `0x005e60d0` billentyű-switch és a `0x005e8a70` teljes diszasszemblyje (`annot_disasm.py`; a munkafa `.bt/` mappájában, a kör végén törölve). (B) A bináris-index (`functions`, `xrefs`, `string_xrefs`) és a `paszta.py`-val végzett teljes `.text` pásztázás: `0x9ccc` és `0x9c..` immediate-ok, valamint a `+0xeac` mező írói. Nincs Ghidra-kör és nincs hálózat.

**1. A három belépés, egy cél (megerősített).**

| belépés | kód | hívás |
|---|---|---|
| menüparancs, ID `0x9ccc` (`Nézet ▸ Időrend`) | `0x005cb990`: `cmp esi,0x9c41` · `lea eax,[esi-0x9c42]` · `cmp eax,0xfa` · `movzx edx,byte ptr [eax+0x5cdb34]` · `jmp dword ptr [edx*4+0x5cd9fc]`. Az ID 0x9ccc → index 0x8a → bájt 47 → `0x005cbbdd`: `push 1` · `push ebx` · `call 0x005e8a70` | `(this, 1)` |
| billentyű `Ctrl+5` | `0x005e60d0` → `0x005e6279`: `push ebp` · `call 0x005696c0` · `jne 0x005e65f7` · `push 1` · `push ebp` · `call 0x005e8a70` | `(panel, 1)` |
| eszköztár-név `thumbui/timelinebutton` (a 38.2.7 kódolvasata, most nem mértem újra) | `0x005d9cc0` → `0x005da7ae` (`push 1`) | `(this, 1)` |

A menü és a billentyű ugyanabba a mód-1 ágba fut. A `this` a két ágban más objektum lehet (a billentyűnél a switch `ebp` argumentuma, a menünél az `ebx`); az azonosságuk nincs megmérve, de a K-kapuk mindkét esetben ugyanazt a kódot futtatják.

A „vizsgált ág nem a Ctrl+5 normál útja” hipotézis **cáfolva**: a `0x005e8a70` mód-1 ága a Ctrl+5 normál útja.

Módszertani megjegyzés: a `0x9ccc` literál egyetlen operandusként szerepel (`0x0055aa15`, a menütábla-építő tárolása). Az elosztó a `0x9c42` bázist vonja le (`lea eax,[esi-0x9c42]`), ezért a literálra keresés nem találja az esetet. A bázis-levonás a keresés kulcsa.

**2. A mód-1 ág kapui (megerősített, `0x005e8a70` diszasszembly).**

| kapu | cím | feltétel | ha nem |
|---|---|---|---|
| K1 | `0x005e8dd1` | `call 0x005d2a70` ≠ 0. A függvény a `[this+0x2bc]+0x760` (catdata, db3) soraiban keres olyat, ahol a `state` oszlop (`0x006a5e60`) ≠ 0 | `IDS_MUST_SELECT` (`0x005e983e`) |
| K2 | `0x005e8dde` | `test dword ptr [ecx+0x154], 0xfffffffe` ≠ 0, ahol `ecx = [this+0x2c0]`: a mező nem 0 és nem 1 | `IDS_MUST_SELECT` (`0x005e983e`) |
| K3 | `0x005e8df4`-`0x005e8e6f` | Flipbook-beállítás ∧ aktív ablak ∧ Ctrl ∧ Shift: Flipbook-lista a `[this+0x2bc]` rekordtárából, fordított sorrendben. Shift nélkül ugrás `0x005e907b`-re | nincs külön ág |
| K4 | `0x005e907d` | `call 0x005675d0` = 0. A függvény a `[this+0xeac]` láncot vizsgálja; ha nincs megfelelő csomópont, felszabadítja és újraépíti (`0x00717bb0`), és -1-et ad, ha az újraépítés nem sikerül | nem 0: a builder ezt az értéket adja vissza, qshow nem nyílik |
| L2 | `0x005e90a5` | `[this+0xeac]` ≠ 0: `call 0x007164b0`. Minden i-re: `item = vt+0xb8(i)`; ha `item[+0x5a] == 0`, az `item[+0xb4]` bekerül a listába | üres lista → K5 |
| L3 | `0x005e90b9` | `[this+0xe64] == -1`: a `0x005e92a0` ág, listaépítés a `0x00891110` függvénnyel | nem a fő út |
| K5 | `0x005e95e6` | `test dword ptr [esp+0x30], 0xfffffffe`: a kódolt számláló (2·n + jelző) ≠ 0, azaz n ≥ 1 | `IDS_MUST_SELECT` (`0x005e97ce`) |
| vége | `0x005e9787` | `call 0x008037e0` (a mód-1 qshow-építő) | nincs |

**3. Miért nem a kijelölés a lista forrása.** Az L2 lista a `[this+0xeac]` gyűjteményből épül, nem a kijelölésből. Ennek írója a `0x00662b20`, amelynek sztringjei (`faces`, `albums`, `Search results`, `pictures`) a nézetek neveire utalnak. Ebből az következik (feltételezés a sztringekből, nem mérve), hogy a `[this+0xeac]` a megjelenített nézet aktuális gyűjteménye. A `+0x5a` jelző jelentése nincs megmérve (rejtett-kép szűrő a gyanú).

**4. Cáfoló kísérletek.**

1. „A Shift nélküli ágban a tömb üres” (38.2.6, 38.2.7). **Cáfolva.** A `0x007164b0` a `lea esi,[esp+0x44]` mutatóján át tölti a hívó tömbjét. A `lea` a `push eax` után fut, így az `esp` 4-gyel le van húzva, és a `[esp+0x44]` a hívó `[esp+0x40]`-`[esp+0x44]` párját jelenti. A 38.2.7 „nem-Flipbook ág nem tölt” állítása csak a közvetlen írásokat nézte, a mutatón átadott írást nem.
2. „A qshow-kapu legalább 2 elemet kér”. **Helyesbítve.** A `[esp+0x30]` számláló 2·n + jelző kódolású (a `0x005e8f97` és a `0x005e9192`-`0x005e91a3` elemenként +2-t ad), a `0xfffffffe` maszk tehát n ≥ 1-et enged át.
3. „A Ctrl+5 nem a mód-1 ág”. **Cáfolva** (1. pont).
4. Megmaradó kérdés: K1, K2 és K4 futásidejű értéke. A statikus kód ezeket nem dönti el.

**5. Bizonyítottsági fok.**

| állítás | fok | alap |
|---|---|---|
| a Ctrl+5 billentyű és a menüparancs → `0x005e8a70(this, 1)` | megerősített | A: diszasszembly és PE-tábla; B: billentyű-switch |
| a Shift-ág (K3) Flipbook-listát ad, nem a normál listát | megerősített | A: diszasszembly |
| qshow-kapu: n ≥ 1 | megerősített | A: kódolás és maszk |
| a Shift nem feltétele a qshow-nak (L2 út) | feltételes | A; a K4 és K1/K2 futásidejű értékétől függ |
| felvétel ↔ kód | feltételes: összeférhető | A; K1/K2/K4 értéke nincs meg |
| `[this+0xeac]` = a nézet gyűjteménye | feltételezés | B: író sztringjei; nincs mérve |

**6. Helyesbítések a 38.2.6-38.2.7 állításaiban.**

- ⛔ „Shift nélkül nincs qshow”: **visszavonva** (L2 út).
- ⛔ „legalább 2 elem”: **helyesbítve**, n ≥ 1 (K5).
- ⛔ „a `0x0052d430` a bal gombos esemény továbbítója”: **helyesbítve**. A függvény `ytUIEvent`-vtábla-beállító (`mov dword ptr [ecx], 0xc8b4b0`, `[ecx+0x68] = 0`), nem továbbító.
- ✅ A `0x00983670` (qshow-ablak) dekompilátuma: `CreateWindowExA`-szerű hívás 12 argumentummal, osztálynév `"ytWindow"`. A HWND a `[obj+0x6c]`-be kerül, a szülő a `[obj+0x78]`. Stílus: az alapágban `0x00cb0000` (param_2 = 0) vagy `0x00cf0000` (param_2 ≠ 0); az 1. ágban ex-stílus `0x80`, stílus `0x84000000`; a 2. ágban stílus `0x84080000`; a 3. ágban `0x40000000`. A WndProc nincs ebben a függvényben.
- ✅ A `0x0052d3c0` `ytUIEvent`-konstruktor (az előző körből, újra megerősítve).

**7. Codex-kész lista: nem adható.** A viselkedés attól függ, hogy K1, K2 és K4 futásidejű értéke mi. Erre épülő fejlesztői lista feltevés volna. Már most eldönthető a fejlesztői következmény: a Ctrl+5-ös időrend nem Shift-függő (L2), és a listát a nézet gyűjteményéből (`[this+0xeac]`) kell építeni, nem a Flipbook-rekordtárból (K3).

**8. Nyitott kérdések (ennek a körnek).**

- Q-A: melyik a Ctrl+5 normál útja. **LEZÁRVA** (1. pont).
- Q-B: kell-e Shift. **LEZÁRVA, feltételesen** (4. pont; a K4 értéke a feltétel).
- Q-C: felvétel ↔ kód. **LEZÁRVA:** összeférhető, feltételes (5. pont).
- Q-D: a K1 catdata `state`-sorainak futásidejű értéke és a `state` jelentése. **BLOKKOLT**: paszta-kör kell (a `0x006a5e60` hívóinak és a helyi db3-mintának az olvasása, a hívó futtatja). [blokkoló]
- Q-E: a K2 `[this+0x2c0]+0x154` mezőjének jelentése és írói. **BLOKKOLT**: paszta-kör kell a `+0x154` írói az `[this+0x2c0]` típusában. [blokkoló]
- Q-F: a K4 (`0x005675d0`) -1-ága. `Ghidra-kör kell: 0x004ae180 - a 0x005675d0 -1-ágának feltétele: mit ad a 0x004ae180, és mikor ad -1-et. [blokkoló]` **Új állapot (38.2.9):** részben lezárva: a `0x004ae180` -1-et ad, ha az index ≥ darabszám (feltételes); a `0x005675d0` -1-ága nyitott.
- Q-G: az L3 ág (`0x00891110`). `Ghidra-kör kell: 0x00891110 - a listaépítő tartalma, ha a [this+0xe64] == -1. [nem blokkolja a fő utat]` **Új állapot (38.2.9):** részben lezárva: a `0x00891110` tömb-másoló, nem listaépítő (feltételes); az L3 forrása és célja nyitott.
- Q-H: a qshow-ablak WndProc-ja. `Ghidra-kör kell: 0x00983330 - a ytWindow-sztringet használó függvény: osztályregisztráció vagy WndProc (hívója a 0x00982d60); a billentyű-fókusz kezelése. [blokkoló]` **Új állapot (38.2.9):** részben lezárva: a `0x00983330` nem WndProc (elvetett); az ytWindow WndProc és a regisztráció nyitott.

**Nyitott kérdések mérlege (38.2.8): 0 nyílt · 3 lezárva · 5 blokkolt · 0 hatókörön kívül · 0 csak nyitva.** Az örökölt tételek (38.2.7 nyitott listája) változatlanul a munkasorban maradnak.

**9. A jegy „Kész, ha” pontjai (#4443).**

- ⛔ A spec leírja a bemutató működését bizonyítékkal: **részben.** Megvan az indítási út, a kapuk, a qshow-ablak létrehozása és az átmenet lépéssora. Nincs meg a WndProc, a csúszka, az Exit célja, az időtartam, a kártyák tartalma és a futásidejű K-értékek.
- ⛔ Nézet ▸ Időrend és Ctrl+5 kattintásos teszttel: **nincs.** Ebben a körben kódot nem írtam.
- ⛔ Képernyőkép az eredetivel összevetve: **nincs.** A 188-as kép nincs a munkafában, és nincs implementáció.

**10. Javasolt fejlesztői irány (feltételes, még nem Codex-kész).** A Ctrl+5 és a menüpont ugyanabba a mód-1 ágba fut. A lista forrása a nézet gyűjteménye (L2), nem a kijelölés. Mielőtt a fejlesztés ezt építi, a K1, K2 és K4 futásidejű értékét kell megmérni egy valódi Picasa-futtatásban (Ctrl+5, kijelölés nélkül, a catdata és a `[this+0x2c0]` állapotának naplózásával).

#### 38.2.9 Ötödik kör: a K4 kapu, a qshow-ablak és az Időrend-váltás C-kódja (#4443, 2026-10-17)

**Kérdés.** Három Q-pont és az Időrend-váltás (`0x007fda00`) C-kódja. Q-F: a `0x005675d0` (K4) -1-ága. Q-G: az L3 ág `0x00891110` függvénye. Q-H: a qshow-ablak WndProc-ja vagy osztályregisztrációja (`0x00983330`).

**Forrás és módszer.** Két fájl, csak olvasás. Nincs új Ghidra-futás és nincs hálózat.
- `2026-10-17-blokkolok-4443-4400.txt` (a `~/picasapy-agent/referencia/ghidra/` alatt): `0x004ae180`, `0x00983330`, `0x00891110`. A `0x00430610`, a `0x009e0660` (#4400) és a `0x00812470` (másik jegy) nincs vizsgálva.
- `2026-10-17-idorend-film-sav.txt` (ugyanott): `0x007fda00`.

(A) a dekompilált C-kód olvasata. (B) a korábbi diszasszembly-olvasat: a 38.2.6 Időrend-váltás lépéssora és a 38.2.7 mód-1 ága. A hívóéleket a HÍVÓK és HÍVOTTAK lista adja. A `0x00983670` és a `0x005e8a70` dekompilátuma más köteg fájlban van (`2026-10-17-qshow-ctrl5.txt`, `2026-10-17-qshow-diavetites.txt`). Ezt a kör nem olvasta be, csak a jelenlétüket nézte meg.

**Eredmények.**

*`0x004ae180` (Q-F).* Zárolt, indexelt olvasás. A `this` objektum `+0x150` mezőjének tömbjéből adja vissza az i-edik elemet (4 bájt). A darabszám a `+0x154` mező értékének a fele; az alsó bit jelző. Ha i ≥ darabszám, a visszatérési érték 0xFFFFFFFF. Más ág nem ad -1-et. Egy tömbelem is lehet 0xFFFFFFFF, és akkor a két eset nem különíthető el. A zár: ha a `+0x0C` bájt nulla, virtuális zárat hív (vtábla +0x18 és +0x1C), különben kritikus szakaszt (+0x28). A függvény újrabelépő: a tulajdonos szál a `+0x20`, a mélység a `+0x24` mezőben van.

A hívóhelyek száma 16. A `0x005675d0` (K4) a `0x0056763a` címen hívja.

*A K4 -1-ága (Q-F).* A `0x004ae180` nem a K4 -1-ága. Ez a `0x005675d0` egyik hívott függvénye. Hogy a `0x005675d0` mikor ad -1-et, az a saját kódjában dől el. Ez a kód nincs a kötegben, és a hívott index sem látszik.

*`0x00891110` (Q-G).* Nem listaépítő, hanem tömb-másoló. A forrás tömbjét változatlanul bemásolja a céltömbbe (EAX). Lépései:
1. Ha a cél és a forrás azonos, nem csinál semmit.
2. A forrás jelzőbitjétől függően hív egy függvényt (`0x0074cf40` vagy `0x009829f0`). Ezek nevét nem ismerjük.
3. Ha a forrás darabszáma 0, vagy 0x1FFFFFFF fölötti, a cél kiürül.
4. Különben igazítja a kapacitást (újrafoglal vagy felszabadít), beállítja a darabszámot, és darabszám × 4 bájtot másol.

A tartalom tehát a forrásé. Hogy mi a forrás és a cél az L3 ágban, azt a hívóhely dönti el (`0x005e92a9`, FUN_005e8a70). Ennek kódja a `2026-10-17-qshow-diavetites.txt`-ben van, ezt a kör nem olvasta be.

*`0x00983330` (Q-H).* Nem WndProc. Nincs benne billentyűkezelés, és osztályregisztráció sem látszik. Mit csinál:
1. Két osztálynevet ("ytWindow", "ytDialog") ad át egy függvénymutatón (`DAT_00d69538`) hívott műveletnek.
2. Egy másik függvénymutatóval (`DAT_00d69528`) lekérdez egy értéket az `uStack_14` ablakhoz (feltételezés: HWND), `-4` paraméterrel. A -4 (0xFFFFFFFC) a Win32 GWL_WNDPROC értéke, tehát a lekérdezés feltehetően a window procedure.
3. Az értéket három másik értékkel veti össze, köztük egy globálissal és egy fix címmel. Ha egyezik valamelyikkel, 1-et ad, különben 0-t.

A hívott függvények nevét a dekompilátum nem adja. Az `uStack_14` és a `puStack_3c` értékét a függvény nem állítja be, ezért az összevetés bemenete nincs igazolva. Hívói: `0x00982dc2` (FUN_00982d60) és `0x00a57325` (FUN_00a572f0).

*Az Időrend-váltás (`0x007fda00`).* A C-kód megerősíti a 38.2.6 lépéssorát. Két lépés hiányzott belőle:
1. Kapu: a `[this+0x2d8]` bájt és a `[this+0x538]` mutató nem nulla. Ha nem, a függvény nem csinál semmit.
2. A `[this+0x3f4]`, ha negatív, 0 lesz.
3. **Új:** hívja a `0x0097e510(0)` függvényt (nincs a kötegben).
4. **Új:** `[this+0x3be] = 1` (bájt, a jelentése nincs megnevezve).
5. A QueryPerformanceCounter értéke double-ként a `[this+0x430]` mezőbe kerül.
6. Hívja a `0x00802230(this, 1)` függvényt. Ez az animátor, nincs a kötegben.
7. `[this+0x3ba]` és `[this+0x3bb]` 0, `[this+0x3b8]` és `[this+0x3b9]` 1.

Billentyű-lekérdezés (GetAsyncKeyState) és Ctrl/Shift-ellenőrzés nincs benne. A függvény csak az átmenetet indítja. Vége, kártyái és kilépése nincs benne. Hívói: `0x007fde80`, `0x00802630`, `0x008032e0` és `0x008037e0`. A mód-1 hívás a `0x008037e0`-ban van (`0x008039e7`). Az első három szerepe nincs vizsgálva.

**Cáfoló kísérletek.**
1. „A `0x004ae180` a K4 -1-ága.” **Cáfolva:** a `0x005675d0` hívott függvénye.
2. „A `0x00983330` a ytWindow WndProc-ja.” **Cáfolva:** nincs benne üzenetkezelés, csak 1 vagy 0 értéket ad.
3. „A `0x00891110` listát épít.” **Cáfolva:** másol.
4. „Az Időrend-váltást Shift vagy Ctrl szűri.” **Cáfolva** ebben a függvényben. A Shift-kapu a `0x005e8a70`-ben van (38.2.8).
5. „A `param_2 = 1` nem animált ágat jelez” (38.2.6). **Visszavonva**, lásd a Helyesbítéseket.

**Bizonyítottsági fok.**

| állítás | fok | alap |
|---|---|---|
| `0x004ae180`: zárolt, indexelt olvasás; -1 pontosan akkor, ha index ≥ darabszám | feltételes | A (egy út) |
| `0x004ae180` a K4 -1-ága | elvetett | A: a `0x005675d0` hívottja |
| `0x00891110`: tömb-másolás | feltételes | A (egy út) |
| a 38.2.8 „listaépítés” neve a `0x00891110`-re | elvetett | A |
| `0x00983330` nem WndProc | elvetett | A |
| `0x00983330`: két osztálynév, `-4` lekérdezés, 1/0 visszatérés | feltételes | A; a hívott függvények nevei hiányoznak |
| `0x00983330` nem kezel billentyűfókuszt | elvetett | A |
| `0x00983330` hívói: `0x00982dc2`, `0x00a57325` | feltételes | A (HÍVÓK); a 38.2.8 Q-H sora a `0x00982d60` hívót említi, de az nem független út |
| `0x007fda00` lépéssora (1., 2., 5., 6., 7. pont) | megerősített | A (C) + B (38.2.6 lépéssor) |
| `0x007fda00` 3. és 4. lépése (`0x0097e510(0)`, `+0x3be = 1`) | feltételes | A; a B-listában nincs |
| `0x007fda00` nem néz billentyűt | megerősített | A + B (a 38.2.6 listában sincs) |
| `0x007fda00` mód-1 hívója a `0x008037e0` | megerősített | A (HÍVÓK) + B (38.2.7 mód-1 ága) |
| az átmenet időzített (a kezdőidő QPC-ből) | feltételes | A; az animátor (`0x00802230`) nincs a kötegben |

**Összefüggés (feltételezés, nem mérve).** A `0x004ae180` darabszám-mezője a `+0x154` eltolásban van. A 38.2.8 K2 ugyanezen az eltoláson (`[this+0x2c0]+0x154`) vizsgálja a „nem 0 és nem 1” feltételt. Ha a `[this+0x2c0]` objektum ugyanilyen tömb, a K2 feltétele azt jelenti, hogy a darabszám nem nulla. A `[this+0x2c0]` típusát nem láttuk. Ellenőrzés: a `+0x154` írói (Q-E, paszta).

**Helyesbítések.**
- A 38.2.8 K-tábla L3 sorában a „listaépítés a `0x00891110` függvénnyel” helyesbítve: a `0x00891110` másol, nem épít listát.
- A 38.2.8 Q-F előfeltétele („a `0x004ae180` a K4 -1-ága”) nem igaz: a `0x004ae180` a `0x005675d0` hívott függvénye.
- A 38.2.6 Időrend-váltás lépéssora kihagyta a `0x0097e510(0)` hívást és a `[this+0x3be] = 1` beállítást.
- A 38.2.6 cáfoló 3. pontja („`param_2 = 1` nem animált ágat jelez”) visszavonva. Alapja a „nem animált ág” címke volt, amelyet a 38.2.7 már visszavont. Az animátor viselkedése nyitott.
- A 38.2.2 kérése a `0x007fda00`-ra (az átmenet vizuális tartalma): részben válaszolva. A lépéssor kész, a vizuális tartalom a `0x00802230`-ban van.

**Nyitott kérdések (a hívó futtatja).**
- `Ghidra-kör kell: 0x005675d0 - a K4 -1-ága: melyik feltételnél ad -1-et, és mit kezd a 0x004ae180 visszatérésével (hívóhely: 0x0056763a). [blokkoló]` **Új állapot (38.2.10):** a -1 négy feltétele ismert; a futásidejű értékük nincs meg (Q-J).
- `Ghidra-kör kell: 0x00982d60 - a 0x00983330 hívója (0x00982dc2): mit tesz a 0/1 eredménnyel, és regisztrálja-e az ytWindow osztályt (lpfnWndProc). [blokkoló]` **Új állapot (38.2.10):** a 0x00982d60 nem regisztrál; a WndProc-ot az EDI adja. A regisztráció jelöltje a 0x00980670 (Q-K).
- `Ghidra-kör kell: 0x00802230 - az Időrend-átmenet animátora: a param_2 = 1 jelentése és az időzítés. [blokkoló]` A 38.2.5 és 38.2.6 kérése változatlan.
- `Ghidra-kör kell: 0x0097e510 - a 0x007fda00 első hívása, argumentum 0: mit csinál. [nem blokkolja a fő utat]` **Új állapot (38.2.10):** lezárva: ShowCursor-számláló (0 látható, -1 rejtett).
- Olvasás, nem Ghidra: a `FUN_005e8a70` 0x005e92a9 körüli L3 ága a `2026-10-17-qshow-diavetites.txt`-ben. Ebből derül ki a `0x00891110` forrása és célja. [nem blokkolja a fő utat] **Új állapot (38.2.10):** a 0x00891110 másol. A forrás és a cél a hívóhelyen van, az nincs a kötegben (Q-N). A kijelölés nélküli Ctrl+5 esetén ez blokkoló.
- A `0x00983670` (qshow-ablak létrehozása) a `2026-10-17-qshow-ctrl5.txt`-ben van. A WndProc-kérdést ott lehet olvasni; ezt a kör nem olvasta be. **Új állapot (38.2.10):** beolvasva; egyezik a K4 fájl változatával. A WndProc nincs benne.

**Nyitott kérdések mérlege (38.2.9):** 0 nyílt · 5 lezárva · 5 blokkolt · 0 hatókörön kívül · 0 csak nyitva.

**A Q-pontok új állapota.**
- **Q-F:** részben lezárva. A `0x004ae180` -1-et ad, ha az index ≥ darabszám (feltételes). A `0x005675d0` -1-ága nyitott.
- **Q-G:** részben lezárva. A `0x00891110` tömb-másoló (feltételes). Az L3 forrása és célja nyitott.
- **Q-H:** részben lezárva. A `0x00983330` nem WndProc. Az ytWindow WndProc és a regisztráció nyitott.

**Codex-kész lista: nem adható.** A K1, K2 és K4 futásidejű értéke nincs megmérve, a Q-F és a Q-H nyitott.

#### 38.2.10 Hatodik kör: a K4 -1-ága, az ytWindow regisztrációja és az L3 ág (#4443, 2026-10-17)

**Kérdés.** A 38.2.9 nyitott listájából négy pont: (a) a K4 (`0x005675d0`) mikor ad -1-et, és mit jelent ez kijelölés nélkül; (b) melyik függvény regisztrálja az ytWindow osztályt, mi a WndProc címe, és ki kezeli a billentyű-fókuszt; (c) mi a `0x0097e510` szerepe; (d) mi az L3 ág (`0x005e92a9`, a `0x00891110` hívása) forrása és célja. Végül: a K1, K2 és K4 alapján eldönthető-e, hogy a Ctrl+5 kijelölés nélkül qshow-t nyit-e.

**Forrás és módszer.** Csak olvasás. Nincs új Ghidra-futás és nincs hálózat. A fájlok a `~/picasapy-agent/referencia/ghidra/` mappában vannak:
- `2026-10-17-hog-qshow-k4.txt`: `0x005675d0`, `0x00982d60`, `0x0097e510`, `0x00983670`. A `0x0088c1a0` nincs vizsgálva (ez a #4194-hez tartozik).
- `2026-10-17-blokkolok-4443-4400.txt`: `0x004ae180`, `0x00983330`, `0x00891110`. A 38.2.9 forrása; az (a), (b) és (d) ponthoz kellett a törzsük.
- `2026-10-17-qshow-diavetites.txt`: `FUN_005e8a70`, két dekompilátum, ugyanaz a függvény. Az L3 ág és a farok. A sorszámok az első dekompilátumra vonatkoznak.
- `2026-10-17-qshow-ctrl5.txt`: `0x00983670` (2441-2541. sor), összevetve a K4 fájl változatával.
- `2026-10-17-idorend-film-sav.txt`: `0x007fda00`, a `0x0097e510(0)` hívás helye.

Nincs megnézve: `0x00980670`, `0x00717bb0`, `0x007164b0`, a `[this+0x2a4]` objektum +0x44 függvénye, és a `0x00982d60` hívóinak EDI-je. A `0x00802230` (animátor) a `2026-10-17-qshow-2.txt` fájlban van; ebben a körben nem olvastam.

**Eredmények.**

*(a) A K4 (`0x005675d0`).* A függvény a `[this+0xeac]` lánc csomópontjain megy végig. Ha az első olyan csomópont, amelynek `+0x213` bájtja nem nulla, a `+0x244` mezője is nem nulla, a K4 0-t ad, és nem épít újra. Minden más esetben a lánc felszabadul (vtábla `+8` hívás), és a függvény négy ponton ad -1-et:
1. `X = [P+0x2fc]`, ahol `P = [this+0xea0]`. Ha `X = 0`, -1.
2. Ha `[X+0x2c0] = 0`, -1.
3. Ha `FUN_004ae180([P+0x2f0]) = -1`, -1. Ez az index túllépése. Egy tárolt 0xFFFFFFFF elem is ide fut, a két eset nem különíthető el.
4. A `[this+0x2a4]` +0x44 függvényének hívása után `[this+0xeac] = 0`, -1. Ez a 38.2.8 „újraépítés nem sikerül" esete.

Ha az újraépítés (`0x00717bb0`) lefut, a K4 0-t ad. Ezért a -1-et adó K4 is törli a régi láncot.

Ctrl+5 esetén a -1 azt jelenti, hogy a `0x005e8a70` kilép: nincs qshow és nincs hibaüzenet. Hogy kijelölés nélkül a K4 -1-et ad-e, a kötegből nem dől el. A K4 törzse nem olvassa a `[this+0xe64]` mezőt (azt használja a szűrő és az L3 ág), de a négy feltétel mindegyike futásidejű értéktől függ.

Ha a K4 nem 0, a `0x005e8a70` azonnal visszaadja ugyanazt az értéket (332-336. sor). Nincs IDS_MUST_SELECT üzenet, és qshow sem nyílik.

*(b) Az ytWindow és a WndProc.* Az ytWindow-hoz tartozó három olvasott függvényben nincs olyan hívás, amely egy argumentumot kap, mint a RegisterClass. Ezek:
- `0x00983670` (qshow-ablak): a CreateWindowExA alakú függvényt hívja 12 argumentummal, a sorrend a CreateWindowExA-val egyezik. Osztálynév: `"ytWindow"`. Regisztrációt nem végez. Ha a hívás 0-t ad, meghívja a `0x00980670`-et, és utána a `[this+0x6c]` nem nulla értékét várja. Ez arra utal, hogy a `0x00980670` hwnd-t állíthat be, de ez feltételezés.
- `0x00983330`: a `DAT_00d69538`-at kétszer hívja, `"ytWindow"` és `"ytDialog"` névvel, három argumentummal. Ez GetClassInfo-alakú hívás. Utána a `DAT_00d69528`-cal (`-4`) lekérdez egy értéket. 1-et ad, ha ez egyezik a három összehasonlított érték egyikével, különben 0-t. Regisztrációt nem végez.
- `0x00982d60` (a `0x00983330` hívója): a `"ytWindow"` nevű `DAT_00d69538`-hívás lekérdezés. Utána a `DAT_00d69524` `(hwnd, -4, EDI)` hívásával a `[this+0x6c]` ablakon beállítja az EDI-t új WndProc-nak. A régi WndProc-ot a `[this+0x34]` őrzi. A `DAT_00d69524`-et 2 és 3 argumentummal is hívja, ezért az API neve (feltételezés: SetWindowLongA) nincs megerősítve.

Eredmény:
- **Regisztráció:** az olvasott kódban nincs. A következő jelölt a `0x00980670`. A teljes bináris-ban nem kerestem.
- **WndProc címe:** nincs meg. A `0x00982d60` az EDI-ből veszi. A hívói (`FUN_00982d00`, `FUN_007360b0`, `FUN_00736a50`, `FUN_00aa5100`) nincsenek a kötegben, így az EDI értéke sem ismert.
- **Billentyű-fókusz** (nyíl, szóköz, Home/End, Escape): nincs meg. Az olvasott függvények egyike sem kezel billentyű-üzenetet, a WndProc nincs a kötegben.

*(c) A `0x0097e510`.* ShowCursor-számlálót állít. Win32 szerint a 0 vagy annál nagyobb érték látható, a -1 rejtett. Ha az argumentum nagyobb, mint 0, a számlálót 0-ra viszi. Ha 0 vagy kisebb, -1-re. A `0x007fda00` az átmenet elején 0-val hívja (a `0x007fda2a` címen), tehát az átmenet alatt a kurzor rejtett. A 11 hívóból csak a `0x007fda00` van vizsgálva. A kurzor visszaállítása (1 argumentummal) nincs a kötegben.

*(d) Az L3 ág (`0x005e92a9`).* A C-ben a hívás argumentum nélkül látszik: `FUN_00891110();`. A `0x00891110` a célját az EAX-ben (`in_EAX`), a forrását az első verem-argumentumban (`param_1`) kapja. Másol: a forrás darabszám × 4 bájtját a célba (`_memcpy`), a cél méretét előbb igazítva. Listát nem épít. A cél alakja {mutató, darabszám << 1 | jelző}.

A forrás és a cél a hívóhelyen dől el. Az EAX és a verem értéke nincs a kötegben, ezért ez nincs igazolva. Erős feltételezés:
- **Cél:** a kimeneti pár, `iStack_d4` és `uStack_d0`. Ugyanez az alak (az első dekompilátum 444-447. sora), és a farok K5 ellenőrzése (532. sor) ezt olvassa. Ha a cél más lenne, az L3 ágban a K5 a 212. sorban nullázott értéket látná, és az L3 ág sosem nyitna qshow-t.
- **Forrás:** az L2-lista pár, `local_c0` és `local_bc`. A 38.2.8 szerint a `0x007164b0` ezt tölti, és a szűrő is ebből olvas (358. sor).

Így az L3 ág a teljes L2-listát másolja, szűrés nélkül. Ez azon a feltevésen áll, hogy a `[this+0xe64] == -1` azt jelenti: nincs kijelölt elem. A szűrő a `[this+0xe64]` értékű elemet keresi, ezért ez indokolt, de nincs igazolva.

Az L3 nem zsákutca. A `goto` után a közös farok fut: a K5, és ha a lista nem üres, a `0x008037e0` (qshow).

**Helyesbítés.** A 38.2.8 K4 sora szerint a -1 az újraépítés hibájából jön. Ez hiányos: a négy feltételből három a vtábla-hívás előtt van (1-3. pont).

**Megerősítés.** A 38.2.8 K3 és K5 sora helyes. A Shift-ág a 330. sorban a farokra ugrik, a K4 csak a Shift nélküli ágban fut. A `0x008037e0` hívása a K5 után áll (604. sor), nem Ctrl-feltételhez kötött. A `cStack_d9` blokk (455-483. sor) a flipbook-listát rajzolja. Ezt nem vizsgáltam tovább.

**Cáfoló kísérletek.**
1. „A K4 -1-e csak az újraépítés hibájától függ." **Cáfolva:** az 1-3. feltétel a vtábla-hívás előtt is -1-et ad.
2. „A K4 -1 után IDS_MUST_SELECT üzenet jelenik meg." **Cáfolva:** a 332-336. sor visszatér, nincs üzenet ebben a függvényben.
3. „A `0x00983330` vagy a `0x00982d60` regisztrálja az ytWindow-t." **Cáfolva** az olvasott kódban: csak lekérdezés és WndProc-csere van.
4. „A `0x008037e0` hívása Ctrl-feltételes." **Cáfolva:** a hívás a K5 else-ágában van (604. sor), nem a `cStack_d9` blokkban.
5. „Az L3 ág zsákutca." **Cáfolva:** a közös farok a K5 után a `0x008037e0`-t hívhatja.

**Bizonyítottsági fok.**

| állítás | fok | alap |
|---|---|---|
| K4: az 1-3. -1 feltétel (`X = 0`, `[X+0x2c0] = 0`, `0x004ae180 = -1`) | feltételes | A (C) |
| K4: a 4. -1 feltétel (a vtábla-hívás után `[this+0xeac] = 0`) | megerősített | A (C) + B (38.2.8 K4 sora) |
| K4 nem 0: a `0x005e8a70` azonnal visszatér, nincs IDS_MUST_SELECT | megerősített | A (332-336. sor) + B (38.2.8 K4 sora) |
| K4 futásidejű értéke kijelölés nélkül | nincs meg | - |
| a K4 törzse nem olvassa a `[this+0xe64]` mezőt | feltételes | A (a K4 teljes törzse; a hívott függvények nincsenek benne) |
| `0x0097e510`: argumentum > 0 → 0 (látható), egyébként -1 (rejtett) | feltételes | A (C) + ShowCursor importnév |
| `0x007fda00` az átmenet elején hívja a `0x0097e510(0)`-t | feltételes | A (C) |
| `0x00891110`: másolás, cél EAX, forrás verem-argumentum | feltételes | A (egy út) |
| L3 cél: a kimeneti pár (`iStack_d4`, `uStack_d0`) | feltételezés | C-ből következtetve; az EAX nincs meg |
| L3 forrás: az L2-lista pár (`local_c0`, `local_bc`) | feltételezés | C-ből következtetve; a verem-argumentum nincs meg |
| `0x00983670`: CreateWindowExA alak, `"ytWindow"` | feltételes | A (két dekompilátum, egy forrás) |
| `0x00983330`, `0x00982d60`: nincs ytWindow-regisztráció | feltételes | A (három argumentumos lekérdezés; az API neve nincs) |
| `0x00982d60`: a WndProc az EDI | feltételes | A |
| a WndProc címe, a billentyű-fókusz | nincs meg | - |
| `0x008037e0` a K5 után van, nem Ctrl-feltételes | megerősített | A (C) + B (38.2.8 K5 és „vége" sora) |

**Következtetés: Ctrl+5 kijelölés nélkül qshow-t nyit-e?** A kötegből nem dönthető el. A kód feltételes választ ad (a sorszámok az első dekompilátumra vonatkoznak):
- Ha K1 hamis, vagy a K2 feltétel nem teljesül: IDS_MUST_SELECT, nincs qshow (213-230. sor).
- Ha K4 = -1: a függvény csendben kilép. Nincs qshow és nincs üzenet.
- Ha K4 = 0: a lánc biztosan létezik, és az L2-lista épül. Ha a lista üres: IDS_MUST_SELECT (K5).
- Ha K1 ≠ 0, a K2 feltétel teljesül, K4 = 0, és a lista nem üres: qshow nyílik.

Ha a `[this+0xe64] == -1` valóban azt jelenti, hogy nincs kijelölt elem, a kijelölés nélküli eset az L3 ágra megy, és a teljes L2-lista kerül a qshow-ba. Ekkor nincs külön „nincs kijelölés" hibaág. Ez feltételezés, nem bizonyíték.

Hiányzik: K1 futásidejű értéke (Q-D), K2 `[this+0x2c0]+0x154` értéke (Q-E), a K4 négy feltételének értéke (Q-J), az L2-lista darabszáma (a `+0x5a` jelző jelentése nincs megmérve, 38.2.8), és az L3 forrása és célja (Q-N).

**Nyitott kérdések (38.2.10).**
- Q-I: a K4 -1 négy feltétele. **LEZÁRVA** (1-4. pont). A futásidejű értékük nincs meg (Q-J).
- Q-J: a K4 futásidejű értéke kijelölés nélkül. **BLOKKOLT:** `Ghidra-kör kell: 0x0056763a - a 0x004ae180 hívás előtti EAX (this): melyik objektum tömbjét olvassa a K4. [blokkoló]` Emellett paszta-kör kell a `[this+0x2a4]` +0x44 függvényére (a címe nincs a kötegben). [blokkoló]
- Q-K: az ytWindow regisztrációja. **BLOKKOLT:** `Ghidra-kör kell: 0x00980670 - a CreateWindowExA hibaágában hívott függvény: regisztrálja-e az ytWindow osztályt, és állít-e be hwnd-t a [this+0x6c]-be. [blokkoló]` **Új állapot (38.2.11):** részben lezárva: a `0x00980670` nem regisztrálja az ytWindow-t (feltételesen), a regisztráció helye nincs meg.
- Q-L: a WndProc címe és a billentyű-fókusz. **BLOKKOLT:** `Ghidra-kör kell: 0x00982d00 - a 0x00982d60 hívója (0x00982d48): mi van az EDI-ben a hívás előtt. [blokkoló]` **Új állapot (38.2.11):** a WndProc címe még nincs meg; az EDI forrása a `0x00982d00` két hívójánál van (`0x00735d96`, `0x00a70cb4`), és azok nincsenek a kötegben.
- Q-M: a `0x0097e510` szerepe. **LEZÁRVA** (c. pont). A visszaállító hívás helye nincs a kötegben, ez nem blokkol.
- Q-N: az L3 forrása és célja. **BLOKKOLT:** `Ghidra-kör kell: 0x005e92a9 - az L3 hívás előtti EAX (cél) és a verembe tett forrás-argumentum: melyik lista másolódik. [blokkoló]` A dekompilátum nem mutatja ezeket, ezért a 0x005e92a0-0x005e92a9 tartomány diszasszembly-olvasata kell.
- Q-O: Ctrl+5 kijelölés nélkül qshow-t nyit-e. **BLOKKOLT** (Q-D, Q-E, Q-J, Q-N).
- Q-P: a `0x00802230` (animátor). **HATÓKÖRÖN KÍVÜL** ebben a körben.

**Nyitott kérdések mérlege (38.2.10):** 0 nyílt · 2 lezárva · 5 blokkolt · 1 hatókörön kívül · 0 csak nyitva.

#### 38.2.11 Hetedik kör: az ytWindow regisztrációja és a WndProc (#4443, 2026-10-17)

**Kérdés.** Két pont a 38.2.10 nyitott listájából. (a) Regisztrálja-e a `0x00980670` az ytWindow osztályt, és állít-e hwnd-t a `[this+0x6c]`-be (ez a 38.2.10 feltételezése volt). (b) Milyen EDI-t ad a `0x00982d00` a `0x00982d60`-nak, vagyis mi a WndProc címe.

**Forrás és módszer.** Csak olvasás. Nincs új Ghidra-futás és nincs hálózat. A fájlok a `~/picasapy-agent/referencia/ghidra/` mappában vannak:
- `2026-10-17-hog-racs-ytwindow.txt` (1): a `0x00980670` és a `0x00982d00` szakasza (HÍVÓK, HÍVOTTAK, C-kód).
- `2026-10-17-hog-qshow-k4.txt` (2): a `0x00982d60` HÍVÓK-listája és C-kódja (306-376. sor).
- `2026-10-17-qshow-ctrl5.txt` (3): a `0x00983670` CreateWindowEx-alakú hívása és a hibaág (2524-2532. sor, keresési kivonat).

Nincs megnézve: a `0x00980670` által hívott `FUN_00512030`, `FUN_0097de80` és `FUN_009ae560` belseje; a `0x00982d00` két hívóhelye (`0x00735d96`, `0x00a70cb4`).

**Eredmények.**

*A `0x00980670` (Q-K).* Hibajelentő. Ha a `GetLastError` nem nulla, a `FormatMessageA` szöveget készít. Egy MessageBox-alakú hívás (`FUN_0097de80`) hibaablakot jelenít meg, a cím az `ytApp::ErrorTitle` kulcsú szöveg. Végül a `LocalFree` felszabadít. Ezután mindig meghívja a `FUN_00512030`-at. Nincs argumentuma, nem kap `this`-t, és nem ír a `[this+0x6c]` mezőbe. Nincs benne `RegisterClass`-alakú hívás. Kilenc hívója van; az egyik a `0x00983670` (`0x009837d2`).

*A `0x00983670` hibaága.* A CreateWindowEx-alakú hívás (indirekt, `DAT_00d695c8`, osztálynév `"ytWindow"`) 0-t ad, ekkor hívódik a `0x00980670`. A feltételes ág csak akkor fut, ha a `[this+0x6c]` a `0x00980670` hívása után sem nulla. A `0x00980670` nem írja a mezőt, ezért a feltétel a hibaágban hamis marad.

*A `0x00982d00` (Q-L).* Konstruktor-jellegű. Beállítja a `ytWindow::vftable`-t, és nullázza az EAX-ben kapott `this` mezőit. Ezután meghívja a `0x00982d60`-at (`0x00982d48`). A C-kódban nem állít be EDI-t. Hívói a `FUN_00735d90` (`0x00735d96`) és a `FUN_00a70cb0` (`0x00a70cb4`); ezek nincsenek a kötegben.

*A `0x00982d60` (WndProc-csere).* A C-kód szerint:
1. A hwnd-t (EAX) a `[this+0x6c]`-be írja. Ha ez nulla, visszatér.
2. Ha a `0x00983330` nem nulla értéket ad, és a `GetWindowLongA(hwnd, -21)` nem nulla, meghívja a `0x00982e60`-at, majd visszatér.
3. Ha a `[this+0x34]` nulla, a régi WndProc-ot (`DAT_00d69528(hwnd, -4)`) oda menti. Az osztályinfó-lekérdezés után, ha a régi eljárás megegyezik az EDI-vel vagy a `DAT_00983940` fix címmel, a mezőt nullázza.
4. A `DAT_00d69524(hwnd, -4, EDI)` hívás az EDI-t állítja be WndProc-ként. Az alakja SetWindowLongA-é, de a név nincs megerősítve.

*A regiszterek.* A `0x00982d00` a `this`-t EAX-ben kezeli, a `0x00982d60` a `this`-t ESI-ben és a hwnd-t EAX-ben. A két C-kód nem illeszkedik egymáshoz. A `0x00982d48`-as hívás előtti EAX, ESI és EDI értéke nincs megállapítva.

*A regisztráció helye.* Az olvasott részekben nincs. A `0x00982d60` GetClassInfo-alakú hívással csak lekérdezi az osztályt (`DAT_00d69538`, `"ytWindow"`). A teljes binárisban nem kerestük.

**Helyesbítés.** A 38.2.10 szerint a `0x00980670` hwnd-t állíthat be a `[this+0x6c]`-be. A C-kód szerint nem ír oda. A 38.2.10 többi állítása a `0x00982d60`-ról (EDI-ből veszi a WndProc-ot, a régi eljárás a `[this+0x34]`-ben) egyezik a C-kóddal, de feltételes marad.

**Cáfoló kísérletek.**
1. „A `0x00980670` regisztrálja az ytWindow osztályt.” **Cáfolva** a közvetlen C-kódban: nincs `RegisterClass`-alakú hívás, a közvetlen külső hívottak (`FormatMessageA`, `GetLastError`, `LocalFree`) nem regisztrálnak. Feltétel: a `FUN_00512030` belsejét nem néztük.
2. „A `0x00980670` hwnd-t állít be a `[this+0x6c]`-be.” **Cáfolva** a C-kódban: a függvény nem ír a mezőbe.
3. „A `0x00982d00` állítja be az EDI-t a `0x00982d60`-nak.” **Nem igazolódott:** a C-kód nem mutat EDI-írást. Ez a dekompilátum hiánya is lehet, ezért ez sem cáfolat, sem igazolás.
4. „A `0x00982d00` az ytWindow regisztrációja.” **Cáfolva:** vtable-írás és mezőnullázás van benne, osztályregisztráció nincs.

**Bizonyítottsági fok.**

A zárójeles számok a forrásfájlokat jelölik (lásd: Forrás és módszer).

| állítás | fok | alap |
|---|---|---|
| `0x00980670`: hibajelentő (`GetLastError`, `FormatMessageA`, hibaablak, `LocalFree`), utána `FUN_00512030` | feltételes | (1) C-kód; a HÍVOTTAK-lista ugyanebből a fájlból jön |
| `0x00980670` nem regisztrálja az ytWindow-t | feltételes | (1) C-kód; a `FUN_00512030` belseje nincs megnézve |
| `0x00980670` nem ír a `[this+0x6c]` mezőbe | feltételes | (1) C-kód |
| `0x00983670` a hibaágban hívja a `0x00980670`-et | megerősített | (3) C-kód, 2528. sor + (1) HÍVÓK: `0x009837d2` |
| `0x00983670`: CreateWindowEx-alakú hívás, osztálynév `"ytWindow"` | feltételes | (3) C-kód |
| `0x00982d00` hívja a `0x00982d60`-at (`0x00982d48`) | megerősített | (1) C-kód + (2) HÍVÓK: `0x00982d48` |
| `0x00982d00`: vtable-írás és mezőnullázás, osztályregisztráció nincs | feltételes | (1) C-kód |
| `0x00982d00` nem állít be EDI-t | feltételes | (1) C-kód (nincs regiszter-írás a C-ben) |
| `0x00982d60`: hwnd nulla esetén visszatér; a WndProc-csere az EDI-vel, `DAT_00d69524` (-4) | feltételes | (2) C-kód, 332-373. sor; a függvénynév nincs megerősítve |
| `0x00982d60`: a régi WndProc a `[this+0x34]` mezőben | feltételes | (2) C-kód, 364-366. sor |
| a `0x00982d00` és a `0x00982d60` regiszter-használata nem illeszkedik | feltételes | (1) és (2) C-kódja |
| a WndProc címe, a billentyű-fókusz | nincs meg | - |
| az ytWindow regisztrációjának helye | nincs meg | - |

**Következtetés.**
- A `0x00980670` nem regisztrálja az ytWindow osztályt (feltételesen). Hibajelentő.
- A WndProc címe nincs meg. A `0x00982d60` az EDI-t állítja be új WndProc-ként, ha a hwnd nem nulla, és a régi eljárást elmenti. Ez alosztályozásra utal, de nem dönti el, hogy az EDI az eredeti WndProc vagy egy alosztályozó eljárás.
- Az EDI értéke a `0x00982d48` előtt nincs megállapítva.
- A billentyű-fókusz nincs meg.

**Hiányzik.**
- A `0x00982d48` előtti EAX, ESI és EDI értéke.
- A `0x00735d96` és a `0x00a70cb4` körüli diszasszembly az EAX, az ESI és az EDI állapotához.
- Az `"ytWindow"` sztring xref-je, hogy a regisztráció helye megtalálható legyen.

Ghidra-kör a WndProc-ra most nem kérhető, mert a címe nincs meg. Ha a hívó kéri, a következő lépés a két hívóhely és az `"ytWindow"` xref-je.

**Nyitott kérdések (38.2.11).**
- Q-K1: regisztrálja-e a `0x00980670` az ytWindow-t. **LEZÁRVA**, feltételesen (1. cáfolat).
- Q-K2: állít-e a `0x00980670` hwnd-t. **LEZÁRVA** (2. cáfolat).
- Q-K3: hol van az ytWindow regisztrációja. **CSAK NYITVA.** Feltételesen nem blokkolja a billentyű-kérdést, mert a `0x00982d60` a saját WndProc-ot állítja be.
- Q-L: mi a WndProc címe, és ki kezeli a billentyű-fókuszt. **BLOKKOLT:** az EDI forrása hiányzik.

**Nyitott kérdések mérlege (38.2.11):** 0 nyílt · 2 lezárva · 1 blokkolt · 0 hatókörön kívül · 1 csak nyitva.

#### 38.2.12 Nyolcadik kör: a WndProc helye, és a qshow a Colab-környezetben (#4443, 2026-10-17)

**Kérdés.** A 38.2.11 után nyitott maradt, hol regisztrálják az ytWindow osztályt, mi a WndProc, és mit csinálnak a billentyűk a Ctrl+5-tel nyitott qshow ablakban.

**Forrás.**
- `referencia/ghidra/2026-10-17-ytwindow-hivatkozasok.txt`: az `"ytWindow"` sztring (`0x00c7f35c`) minden utasításbeli hivatkozása (Ghidra, konstans-keresés) és a tartalmazó függvények C-kódja.
- `referencia/ghidra/2026-10-17-ytwindow-wndproc.txt` és `referencia/ghidra/2026-10-17-ytwindow-uzenetek.txt`: a WndProc és a `OneUpUI` vtábla `+0x1c` bejegyzésének C-kódja.
- Colab-felvétel, picasa-colab-jobs job-189: alapállapot, Ctrl+5 kijelölés nélkül, majd Right, Right, Left, space, space, Home, End, Escape, lépésenként képernyőképpel és ablaklistával.
- Colab-felvétel, job-191: ugyanígy, majd kattintás a képernyő vezérlőire: következő (kétszer), előző, lejátszás (indítás, 10 mp, leállítás), egy kártya, rács-vissza.

**Eredmények.**
1. **Regisztráció (megerősített).** A `FUN_009838b0` kitölti a WNDCLASS-t: `style = 0x400b`, `lpfnWndProc = 0x00983940`, `cbWndExtra = 4`, ikon `IDI_APPLICATION` (`LoadIconA(0, 0x7f00)`), háttér `GetStockObject(0)`, osztálynév `"ytWindow"`, majd a `DAT_00d69530` mutatón át regisztrál. A konstans-keresés három hivatkozást talált: kettő a `0x00983670` (ablaklétrehozás), egy ez a függvény. Két független út: a sztring hivatkozásai és a WNDCLASS-mezők sorrendje.
2. **A WndProc (`0x00983940`) csak továbbít (megerősített a C-kódból).** A `GetWindowLongA(hwnd, -21)` (felhasználói adat) objektum vtáblájának `+0x1c` metódusát hívja az üzenettel. Ha az `0xf4241`-et ad vagy nincs objektum, a `DAT_00d69554` alapeljárás fut; az `1000000` visszatérés 1-re fordul. A billentyűkezelés tehát az ablakhoz kötött objektum osztályában van.
3. **A `OneUpUI` vtábla nem az ablakobjektumé (feltételes).** A `0x00cbd5c4 + 0x1c` bejegyzés a `0x0097b5f0`, amely csak egy kritikus szakaszt enged el. Az ablakhoz kötött objektum osztálya és vtáblája NINCS MEG; a `-21` mezőt író hívás a `0x00983670` körül keresendő.
4. **A bemenet mért hatása a Colab-környezetben (megerősített a felvételen, de a környezetre szól).** A Ctrl+5 után megjelenik a `qshow` ablak (az ablaklistában `['Picasa 3', 'qshow']`), de az aktív ablak végig a `Picasa 3` marad. A Right, Right, Left, space, space, Home, End és Escape után az egymást követő képek között **egyetlen képpont sem változik** (képpontonkénti összevetés, 8-as küszöb, 4.-22. kép), és a qshow nyitva marad. A job-191-ben a képernyő gombjaira kattintva (következő, előző, lejátszás, kártya, rács-vissza) **szintén egyetlen képpont sem változik** (5.-20. kép). Mivel a kattintás sem hat, a qshow ablak ebben a Wine-környezetben semmilyen bemenetre nem reagál (vagy nem rajzol újra). A mérés ezért **nem bizonyítja**, hogy az eredetiben a billentyűk hatástalanok.

**Bizonyítottsági fok.**

| állítás | fok | alap |
|---|---|---|
| ytWindow-regisztráció a `0x009838b0`-ban, WndProc `0x00983940` | megerősített | sztring-hivatkozások + WNDCLASS-mezők |
| a WndProc a `-21` objektum vtábla `+0x1c` metódusára továbbít | megerősített | C-kód + a `0x00982d60` alosztályozó mintája (38.2.11) |
| a Colab/Wine-környezetben a qshow sem billentyűre, sem kattintásra nem változik | megerősített | job-189 (18 kép) és job-191 (16 kép), nulla eltérés |
| az eredetiben (Windows) a billentyűk hatástalanok | NINCS MEG | a környezet a kattintást sem viszi át, ezért a felvétel nem dönt |
| a qshow nem kap billentyűfókuszt | feltételes | az ablaklista aktív ablaka; Wine alatt a fókusz kezelése eltérhet a Windowsétól (a 38.2.7 szerint a kód `SetFocus`-t hív) |

**Cáfoló kísérlet.** „A billentyűk hatnak, csak a kép lassan frissül.” Cáfolva: a lépések között 3-5 másodperc várakozás volt, és a 22. kép (az Escape után 3 másodperccel) is bitre egyezik a 4.-kel. „A környezet viszi a bemenetet a qshow-hoz.” Cáfolva: a job-191 kattintásai sem változtatnak a képen.

**Következtetés.** A Colab-végrehajtó a qshow ablakot csak megjeleníteni tudja, vezérelni nem: sem a billentyű, sem a kattintás nem jut el hozzá (vagy az ablak nem rajzol újra). A billentyűk és a gombok viselkedése ezért ebből a környezetből nem mérhető. Következő irány: a WndProc mögötti ablakobjektum osztályának megkeresése (a `-21` mezőt író hívás a `0x00983670` körül), és annak üzenetkezelője a binárisból.

**Nyitott kérdések mérlege (38.2.12):** 0 nyílt · 2 lezárva (regisztráció, WndProc-továbbítás) · 2 blokkolt (az ablakobjektum osztálya és üzenetkezelője; a billentyűk és gombok viselkedése, mert a Colab-környezet a bemenetet nem viszi át) · 0 hatókörön kívül.

#### 38.2.13 Kilencedik kör: a qshow ablakobjektuma (#4443, 2026-10-17)

**Kérdés.** A 38.2.12 szerint a WndProc (`0x00983940`) a `GetWindowLongA(hwnd, -21)` objektum vtábla `+0x1c` metódusára továbbít. Három kérdés: (a) melyik függvény írja a -21 mezőt, és mi kerül oda; (b) mi a qshow ablakobjektum vtábla-címe; (c) melyik `+0x1c` metódus kezeli a billentyűket és a gombokat.

**Forrás és módszer.** Csak olvasás. Nincs új Ghidra-futás, nincs bináris, nincs hálózat. A C-kódok a `~/picasapy-agent/referencia/ghidra/` mappában vannak:
- `2026-10-17-hog-qshow-k4.txt`: a `0x00983670` (147-253. sor) és a `0x00982d60` (306-377. sor).
- `2026-10-17-qshow-ctrl5.txt`: a `0x00983670` második példánya (2441-2541. sor).
- `2026-10-17-ytwindow-hivatkozasok.txt`: a `0x00982d60`, a `0x00983670` és a `0x009838b0` C-kódja, a `"ytWindow"` sztring hivatkozásai.
- `2026-10-17-ytwindow-wndproc.txt`: a WndProc (`0x00983940`).
- `2026-10-17-hog-racs-ytwindow.txt`: a `0x00982d00` (1286-1310. sor).
- `2026-10-17-qshow-2.txt`: a `0x004039f0`, a "Picasa 3" főablak építője (104-107. sor).
- `2026-10-17-qshow-3.txt`: a `0x008037e0`, a qshow építője (786-813. sor, és a függvény vége).

A mappa összes fájljában megkerestem a `-0x15` és a `0xffffffeb` előfordulásait, és a `0x00982bf0` hivatkozásait. A `0x00982bf0` C-kódja nincs a mappában.

**Eredmények.**

1. **A -21 mezőt két függvény írja (megerősített).** Mindkettő a `DAT_00d69524` függvénymutatón át hívja a `(hwnd, 0xffffffeb)` párost:
   - `0x00983670` (ablaklétrehozás): a `CreateWindowEx`-alakú hívás után, ha van hwnd. Hívója a `0x00982bf0` (`0x00982cf2`).
   - `0x00982d60` (WndProc-csere): a `-4` hívás után. Hívói a `0x00982d00` (`0x00982d48`), a `0x007360b0` (`0x00736497`), a `0x00736a50` (`0x00736abc`) és a `0x00aa5100` (`0x00aa5161`).
   Az alak SetWindowLongA-é, de a név nincs megerősítve.

2. **A CreateWindowEx nem adja a -21 értékét (megerősített).** A létrehozó hívás utolsó argumentuma (`lpParam`) a C-kódban `0`.

3. **Az érték nincs meg (NINCS MEG).** Mindkét `DAT_00d69524(hwnd, 0xffffffeb)` hívásnak csak két argumentuma látszik. A -4 hívásnak (`0x00982d60`, 373. sor) a harmadik argumentuma (`EDI`) látszik, a -21 hívásnak nem. Ez a dekompilátor hiánya is lehet, vagy egy regiszterből jövő érték. A C-ből nem dönthető el.

4. **A this és a jelölt objektum (feltételes).** A `0x00983670` és a `0x00982d60` `this`-e (`unaff_ESI`) a hwnd-t a `+0x6c`-ben tárolja, így a hwnd-ből vissza lehet rá találni. A `this` típusának neve nincs a C-kódban. Ismert mezői: `+0x00` vtábla-mutató, `+0x34` a régi WndProc, `+0x64` a `0x008037e0` által beállított másik objektum (`piVar5`, lásd 5.), `+0x6c` a hwnd, `+0x78` a szülő hwnd. Ha a -21 érték a `this`, akkor ez az objektum a jelölt. Ez nincs igazolva.

5. **A qshow ablakának objektuma: a `0x008037e0` piVar4-je (feltételes).** A `0x008037e0` két objektumot épít:
   - `piVar4` (0x88 bájt): a `0x00982bf0` visszatérési értéke. A `SetFocus((HWND)piVar4[0x1b])` (813. sor) a `+0x6c` hwnd-t használja, ezért ez feltételesen a qshow ablakának objektuma.
   - `piVar5` (0x890 bájt), a `0x007fa7f0` építi (C-kód nincs). A `piVar4[0x19] = piVar5` (808. sor) a `+0x64`-be írja, és a `(*piVar5 + 0x28)(piVar4)` hívás kapcsolja össze a kettőt.
   A -21 objektuma a `piVar4` és a `piVar5` közül bármelyik lehet. A C nem dönti el.

6. **A vtábla címe nincs meg (NINCS MEG).**
   - A `piVar4` vtábláját a `0x00982bf0` állíthatja be. Ennek C-kódja nincs a mappában. A `0x008037e0` nem ír vtáblát a `piVar4`-re.
   - A `0x004039f0` a `0x00982bf0` után írja be a `ytFrameWindow::vftable`-t (`qshow-2.txt` 107. sor). Ez a főablak, nem a qshow.
   - A `ytWindow::vftable` a `0x00982d00`-ban áll be (`*in_EAX = ytWindow::vftable`). A `0x00982d00` hívói között nincs a `0x00982bf0`, ezért nem bizonyított, hogy a qshow vtáblája ez. A szimbólum számértéke sincs a mappában.
   - A `piVar5` vtáblája a `0x007fa7f0`-ban áll be. Annak C-kódja sincs a mappában.

7. **A +0x1c üzenetkezelő címe nincs meg (NINCS MEG).** A cím a vtábla címéből számolható. A `vtábla + 0x1c` címen lévő 4 bájt (kis-endian, 32 bites binárisban) a metódus abszolút címe. A vtábla az objektum első 4 bájtja. Mivel a vtábla címe nincs meg, a bejegyzés címe sincs meg.

8. **A WndProc és a -21 olvasói (megerősített, a 38.2.12 kiegészítése).** A `0x00983940` a `GetWindowLongA(hwnd, -0x15)` eredményét használja. Ha van objektum, és a `+0x1c` hívás nem `0xf4241`-et ad, a függvény visszatér az eredménnyel (`1000000` esetén 1-gyel). Egyébként a `DAT_00d69554` alapeljárás fut. A `+0x1c` hívás három argumentumot kap: `msg`, `wParam`, `lParam`. A `this` a C-kódban nem látszik. A `0x00982d60` 357. sora is olvassa a -21 mezőt: ha van objektum, meghívja a `FUN_00982e60`-at, majd az objektum vtábla első slotját `1` argumentummal.

**Bizonyítottsági fok.**

| állítás | fok | alap |
|---|---|---|
| a -21 mezőt a `0x00983670` írja (létrehozás) | megerősített | (hog-qshow-k4) 244. sor; (qshow-ctrl5) 2532. sor |
| a -21 mezőt a `0x00982d60` írja (WndProc-csere) | megerősített | (hog-qshow-k4) 374. sor |
| az írás `DAT_00d69524`-en át, SetWindowLongA-alakú | feltételes | a C alakja; a név nincs megerősítve |
| a CreateWindowEx `lpParam`-ja `0`, a -21 értéke nem onnan jön | megerősített | (hog-qshow-k4) 236-237. sor |
| a -21-be kerülő érték (a harmadik argumentum) | NINCS MEG | a C-ben két argumentum látszik |
| a -21 objektuma a `this` (`unaff_ESI`) | feltételes (jelölt) | a hwnd a `+0x6c`-ben; az érték nincs |
| a qshow ablakának objektuma a `0x008037e0` `piVar4`-je | feltételes | (qshow-3) 813. sor: `SetFocus` a `+0x6c` hwnd-del |
| a qshow objektum vtáblája `ytWindow::vftable` | NINCS MEG | a `0x00982d00` nem hívója a `0x00982bf0`-nak |
| a `+0x1c` üzenetkezelő címe | NINCS MEG | a vtábla címe hiányzik |
| a WndProc a -21 objektum `+0x1c` metódusára továbbít | megerősített | (ytwindow-wndproc) C-kód |

**Cáfoló kísérletek.**
1. „A -21-et a CreateWindowEx `lpParam`-ja állítja be.” **Cáfolva:** a létrehozó hívás `lpParam` argumentuma `0`.
2. „A -21-et csak a `0x00983670` írja.” **Cáfolva:** a `0x00982d60` is ír rá (374. sor).
3. „A -21 objektuma `ytWindow::vftable`-t visel.” **Nem igazolódott:** a `0x00982d00` nem hívója a `0x00982bf0`-nak. Ez nem cáfolat, mert a `0x00982bf0` C-kódja hiányzik.
4. „A -21 objektuma a `this`.” **Nem cáfolható és nem igazolható:** a -21 értéke nincs a C-ben. A `piVar5` is jelölt marad.

**Következtetés.**
- A -21 mezőt a `0x00983670` (létrehozás) és a `0x00982d60` (WndProc-csere) írja. Ez megerősített.
- Hogy melyik objektum kerül oda, nincs megmérve. A jelöltek: a qshow ablakának `piVar4`-je vagy a `piVar5`.
- A vtábla címe nincs meg, ezért a `+0x1c` üzenetkezelő sincs meg. A billentyűk és gombok kérdése blokkolt.

**Hiányzik.**
- A `0x00982bf0` C-kódja: a vtábla-beállítás (`*this = ...`) és a `this` átadása a `0x00983670`-nek.
- A `0x00983670` `DAT_00d69524(hwnd, 0xffffffeb)` hívásának szerelése: a hívás előtti push-sor, vagyis a harmadik argumentum. A C-sorrend szerint a hívás a `0x009837d2`-es (`FUN_00980670`) hívás után van.
- A `0x007fa7f0` C-kódja, ha a `piVar5` lesz a jelölt.

**Ghidra-kör kell.** A kért sor (a vtábla +0x1c üzenetkezelője) most nem írható fel, mert a vtábla címe nincs meg. Helyette:

Ghidra-kör kell: 0x00982bf0 - a qshow ablakobjektum konstruktora (vtábla-beállítás, a `this` átadása a 0x00983670-nek) [blokkoló]

Szerelés kell: 0x00983670 - a `DAT_00d69524(hwnd, 0xffffffeb)` hívás előtti push-sor (a harmadik argumentum) [blokkoló]

Ha a vtábla címe megvan, a következő kör a `+0x1c` üzenetkezelőre szól: WM_KEYDOWN, WM_LBUTTONDOWN ága.

**Amit ez NEM jelent.** A qshow billentyű- és egérviselkedése Windowsban továbbra sincs megmérve. A 38.2.12 nyitott pontja nem zárult le, csak szűkült: az írók megvannak, az objektum nincs.

**Nyitott kérdések mérlege (38.2.13):** 0 nyílt · 2 lezárva (a -21 írói; a CreateWindowEx `lpParam`-ja kizárva) · 3 blokkolt (az érték; a vtábla címe; az üzenetkezelő) · 0 hatókörön kívül.

#### 38.2.14 Tizedik kör: a Ctrl+5 két belépési útja, a mód-bájt és a qshow-vezérlés (#4443, 2026-10-18)

**Kérdés.** (1) Melyik switch-ág hívja a `0x005e8a70`-et a `0x9ccc`-hez? (2) Milyen feltétellel nyit qshow-t a Ctrl+5 (job-188: kijelölés nélkül is nyit), milyen paraméterrel, és mi a különbség a Lejátszás (diavetítés) hívásához képest? (3) Mit olvasható ki a qshow-ablak létrehozásából (`0x00983670`) és a `0x0052d430`-ból a bemutató vezérléséről?

**Forrás és módszer.**
- (A) Helyi diszasszembly, csak olvasás: a `Picasa3.exe` PE-jéből, a munkafa ideiglenes `.bt/bt_kiolv.py` szkriptjével (a kör végén törölve). Vizsgált függvények: `0x005cb990` (WM_COMMAND-elosztó), `0x005e60d0` (billentyű-kezelő), `0x005e8a70`, `0x008037e0`, `0x005696c0` (kapu), `0x00559150` (menütábla-építő). Az ugrótábla-bejegyzést a PE-ből olvastam, nem a Ghidra-szövegből.
- (B) Azonosító-hozzárendelés: a menütábla-építő rekordjai és a `.rdata` feliratkulcsok (`eMenuView::ID_VIEW_TIMELINE` stb.) összevetése. A rekord `+0` mezője a `FUN_009ae560(kulcs)` eredményéből íródik (`mov [rekord], eax`), a `+0xa` a parancsazonosító.
- (C) A jelenlegi kód: `src/picasapy/app/qml/PicasaMenuBar.qml`, `src/picasapy/app/qml/Main.qml`, `MainToolbar.qml`, és a `01bb55264` commit (#1903).
- A függvényméreteket a bináris-index `functions` táblájából vettem. A vtábla-hívások nem látszanak az index `xrefs` táblájában, ezért a hívólista nem negatív állítás.

**Eredmények.**

1. **A `0x9ccc` hívási útja (megerősített; A + B).**
   - `0x005cb990`: `lea eax,[esi-0x9c42]` · `cmp eax,0xfa` · `ja 0x5cd979` · `movzx edx,byte ptr [eax+0x5cdb34]` · `jmp dword ptr [edx*4+0x5cd9fc]`.
   - `0x9ccc - 0x9c42` = index `0x8a`; a bájt (`0x5cdbbe`) értéke 47; az ugrótábla 47. bejegyzése (`0x5cdab8`) a `0x005cbbdd`-et adja.
   - `0x005cbbdd`: `push 1` · `push ebx` · `call 0x005e8a70` · `jmp 0x5cd9e6`. Vagyis `(this = ebx, mód = 1)`.
   - A `0x005cbbd1` ág (`push edi`, ahol `edi = 0`) a `0x9c6d` és a `0x9c9f` azonosítókat kapja: `(this, 0)`.
   - Az azonosítók (B): `0x9ccc` = `eMenuView::ID_VIEW_TIMELINE` (`Ti&meline`, rekord `0xd6e090`, a kulcs-mutató a `0x0055a9ed`-nél íródik). `0x9c9f` = `eMenuView::ID_VIEW_SLIDESHOW` („&Slideshow", rekord `0xd6e07c`, `0x0055a9a3`). `0x9c6d` = `eMenuLabelFolder::ID_ALBUM_SLIDESHOW` („&View Slideshow", rekord `0xd6e1d4`, `0x0055ae81`).
   - A `0x005e8a70` hívói (index, HÍVÓK): `005cbbd3`, `005cbbe0` (`FUN_005cb990`); `005da743`, `005da7ae` (`FUN_005d9cc0`, az eszköztár); `005e146f` (`FUN_005e0f70`, nem vizsgáltam); `005e626f`, `005e628a` (`FUN_005e60d0`, a billentyű).

2. **A Ctrl+5 két belépési útja.**
   - **E1, a menü.** A WM_COMMAND `0x9ccc` közvetlenül a `0x5cbbdd` ágra fut (1. pont). Az ágban nincs feltétel: a `0x005e8a70` `(this, 1)` paraméterrel hívódik. A gyorsbillentyű-hozzárendelés (accelerator-tábla) forrása NINCS MEG.
   - **E2, a billentyű.** A `0x005e60d0` a WM_KEYDOWN-t (`0x100`) kezeli. A `cmp word ptr [esi+8],0x11` · `je 0x5e6603` a Ctrl-billentyű SAJÁT lenyomását zárja ki; nem követeli meg a Ctrl meglétét. A `0x005e6279` ág (a „5"-ös): `push ebp` · `call 0x005696c0` · `test al,al` · `jne 0x5e65f7` (kilépés) · `push 1` · `push ebp` · `call 0x005e8a70`. A `0x005e625e` ág (a „4"-es) ugyanez `push 0`-val, vagyis mód 0.
   - **A kapu (`0x005696c0`, 91 bájt, `ret 4`).** `al = 1` pontosan akkor, ha: `[0x00d67914] != 0` ∧ a `0x009c2fc0(0x00c8ec30)` singleton nem 0 ∧ `[singleton+0x20c] == 0` ∧ `InterlockedCompareExchange([this+0x668], 0, 0) == InterlockedCompareExchange([this+0x99c], 0, 0)`. A `0x00c40328` IAT-slot a PE import-táblájából `KERNEL32!InterlockedCompareExchange`. A 0-ra való összehasonlítás nem ír (0 → 0), tehát a kapu tisztán olvas.
   - A billentyű-út a kapu HAMIS eredményénél nyit. A Ctrl+5 csak akkor éri el a `0x005e8a70`-et, ha a kapu 0 (például nincs singleton, vagy a két mező nem egyezik).
   - **A billentyű-út Ctrl-feltétele: NINCS MEG.** A látott kódban nincs `GetKeyState(VK_CONTROL)`-hívás. Lehet, hogy a Ctrl feltétele a `0x005e6710` hívóláncban van (lásd a nyitott pontokat).

3. **A `0x005e8a70` elágazása a móddal (megerősített a sorrend).**
   - Belépéskor: `call 0x005696c0` (`0x005e8acb`, `push ebx`). Ha ez 1, a `0x009cd8a0` hívás után `cmp eax,0xf4242` · `je 0x5e8b3d` (kilépés-jelölt ág).
   - `cmp byte ptr [0x00d67849],0` · `je 0x5e8b06`. Ha a globális nem 0: `push 0x10` · `call dword ptr [GetAsyncKeyState]` (Shift) · `jne 0x5e8d5d` (Shift lenyomva: a `0x5e8d5d` ág).
   - `0x005e8b06`: `cmp byte ptr [ebp+0xc],0` · `jne 0x5e8d5d`. **Mód 1 (Időrend)** a `0x5e8d5d` ágra megy; ebben vannak a K1-K4 kapuk (38.2.8). **Mód 0 (Lejátszás)** a `0x5e8b10` ágra megy. Ez a tartomány (`0x5e8b10`-`0x5e8d5c`) nem hívja a K1-et (`0x005d2a70`) és a K4-et (`0x005675d0`). Hívásai közül (részlet): `0x0052e8a0`, `0x0040fb50`, `0x004edf60`, `0x005c6710`, `0x00717bb0`, `0x00579330`, `0x009cd730`, `0x0052e2f0`, `0x005d1520`.
   - A mód-bájt a `0x005e9706`-ban íródik a qshow-struktúra 1. bájtjába (`mov cl,[ebp+0xc]` · `mov [esp+0x65],cl`). A `0x005e9787` (`call 0x008037e0`) az egyetlen hívóhely.

4. **A qshow-építő (`0x008037e0`) mód-ága (megerősített).**
   - `0x008039de`: `mov edx,[esp+0x6c]` · `cmp byte ptr [edx+1],0` · `je 0x8039fd`. Mód 0: `push esi` · `call 0x00801cf0` (sima diavetítés).
   - Mód nem 0: `call 0x007fda00` (Időrend-váltás) · `cmp byte ptr [esi+0x3bf],0` · ha 0, `call 0x00802060`.
   - A `0x008037e0` a `Preferences\BigSlideshow2` kulcsot olvassa (38.2.9).

5. **A qshow-ablak és a vezérlés (megerősített a létrehozás és a továbbítás; az objektum NINCS MEG).**
   - A `0x00983670` `CreateWindowExA`-alakú hívása az `"ytWindow"` osztályt használja (`.ghidra4443/2026-10-17-qshow-ctrl5.txt`, 2524. sor). Utána `(*DAT_00d69524)(hwnd, 0xffffffeb)` (2532. sor): a -21 (GWLP_USERDATA) mező írása. Az írt érték (a harmadik argumentum) NINCS MEG (38.2.13).
   - A WndProc (`0x00983940`) a -21 objektum `vt+0x1c` metódusára továbbít (38.2.12). Az objektum és a vtábla NINCS MEG (38.2.13).
   - **`0x0052d430` (23 bájt): NEM továbbító.** `push edi` · `lea edi,[ecx+0x68]` · `mov dword ptr [ecx],0x00c8b4b0` · `call 0x00401000` · `mov dword ptr [edi],0` · `pop edi` · `ret`. Vtábla-beállító (a 38.2.8 helyesbítését igazolja).
   - A főablak billentyű-kapcsolója (`0x005e60d0`) a 38.2.8 szerint nem kezel Escape-et, Space-t, nyilakat és Home/End-et. Ebben a körben ezt nem mértem újra. Ezek hatása a qshow-ablakban, a WndProc-objektumban van: NINCS MEG.
   - **Kilépés (Exit):** NINCS MEG ebben a körben (a 38.2.8 szerinti `this+0x50` / `vt+0x14` hívás nincs újramérve).

**Bizonyítottsági fok.**

| állítás | fok | alap |
|---|---|---|
| `0x9ccc` → `0x005cbbdd` → `0x005e8a70(this, 1)` | megerősített | A: PE-tábla és diszasszembly; B: rekord-kulcs |
| `0x9c9f` (Lejátszás) és `0x9c6d` (mappa-diavetítés) → `(this, 0)` | megerősített | A + B |
| menü (E1) és billentyű (E2) egyaránt mód 1 | megerősített | A |
| billentyű-kapu: IAT `InterlockedCompareExchange`, a feltételek szerkezete | megerősített | A + PE-import |
| a kapu futásidejű értékei (singleton, flag, a két mező) | NINCS MEG | statikusan nem mérhető |
| a Ctrl-feltétel a billentyű-útban | NINCS MEG | a látott kódban nincs Ctrl-ellenőrzés |
| mód 1 → `0x5e8d5d`, mód 0 → `0x5e8b10` | megerősített (elágazás) | A |
| a mód-0 ág listaépítése | NINCS MEG | nem követtem végig |
| qshow-építő: mód 0 → `0x801cf0`; mód ≠ 0 → `0x7fda00` + `0x802060` | megerősített | A |
| qshow-ablak: `CreateWindowExA`-alak, `"ytWindow"`, -21 írás | megerősített | Ghidra C (2524., 2532. sor) |
| `0x0052d430` = vtábla-beállító | megerősített | A |
| qshow billentyűi, Exit, vtábla | NINCS MEG | a WndProc-objektum hiányzik |

**Cáfoló kísérletek.**
1. „A Ctrl+5 nem jut a `0x005e8a70`-hez a `0x9ccc` switch-ágon át." **Cáfolva:** a `0x9ccc` egyedi indexe (`0x8a`) a `0x5cbbdd` ágra mutat, és ez az egyetlen ág, amely a `0x9ccc`-hez tartozik.
2. „A Lejátszás és az Időrend ugyanazt az ágat használja." **Cáfolva a szerkezetben:** mód 1 a `0x5e8d5d`-re, mód 0 a `0x5e8b10`-re ugrik, és csak mód 1 hívja a K1-et és a K4-et. A mód-0 ág listatartalmát viszont nem bizonyítottam.
3. „A `0x0052d430` a bal gombos esemény továbbítója." **Cáfolva** (23 bájt, vtábla-beállító).
4. „A kapu minden Ctrl+5-öt blokkol." **Cáfolva:** a kapu hamis eredménynél enged tovább, a futásidejű értékek viszont nem ismertek.

**Eredeti | Nálunk | Teendő**

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Nézet ▸ Időrend (`0x9ccc`) → `0x005e8a70(this, 1)`, kijelölés nélkül is (job-188) | menüpont `enabled: false` (`PicasaMenuBar.qml:1160-1164`), Ctrl+5 `Shortcut` `enabled: false` (`Main.qml:1765-1773`), #1903 | Engedélyezés csak a valódi bemutató megépítése UTÁN, a menüpont és a billentyű együtt. |
| Ctrl+5 billentyű-út: `0x005e60d0` „5"-ös ága, a `0x005696c0` kapuval, `(this, 1)` | nincs | A kapu futásidejű értékei és a Ctrl-feltétel kell a fejlesztés előtt (lásd a nyitott pontokat). |
| Lejátszás (`0x9c9f`) és mappa-diavetítés (`0x9c6d`): `(this, 0)`, a qshow mód-0 ága (`0x801cf0`) | Ctrl+4 és a mappa-diavetítés megvan (a 29. tétel szerint) | Nincs teendő; a bemutató útja más, mint az Időrend-é. |
| Időrend-váltás (`0x007fda00`, `0x802060`) mód 1-ben | nincs | A lépéssort (38.2.9) a bemutató-váltásnál kell követni. |
| qshow-ablak: `ytWindow`, `CreateWindowExA`, `[this+0x6c]` HWND, -21 objektum | `TimelineView.qml`: év/hónap rács, az alkalmazásablakon belül | A rács nem az eredeti bemutató. A qshow-t külön, teljes képernyős módként kell megépíteni. |
| Eszköztár-gomb `thumbui/timelinebutton` (`m_hidden`, 38.2.4) | `MainToolbar.qml` gombja #1903-mal eltávolítva | Az eredeti gomb rejtett, nem kell visszaállítani. |
| Lista-forrás: a nézet gyűjteménye (`[this+0xeac]`, feltételezés) | nincs | Ha a bemutató a nézet képeit járja, a listát az aktuális gyűjteményből kell építeni, nem a Flipbook-rekordtárból (38.2.8). |
| qshow billentyűi (nyíl, Space, Esc, Home/End) és egérkezelése | nincs | NINCS MEG: a `-21` objektum vtáblájának `+0x1c` metódusa kell (38.2.13). |
| Kilépés (Exit) célja | nincs | NINCS MEG (a 38.2.8 `this+0x50` hívása nincs újramérve). |

**Nyitott kérdések mérlege (38.2.14).** 4 nyílt · 3 lezárva (a `0x9ccc` hívási útja; a `0x0052d430` helyesbítése; a mód-elágazás és a qshow-építő mód-ága) · 3 blokkolt · 0 hatókörön kívül.

Ghidra-kör kell: 0x005e6710 - a „5"-ös billentyű-ág (`0x005e6279`) hívóláncában van-e Ctrl- vagy Shift-ellenőrzés, és a Ctrl+5 billentyű-kötésének forrása (accelerator-tábla vagy a hívó). [blokkoló]

Eredeti futtatás kell (Colab, nem Ghidra): Ctrl+5 kijelölés nélkül, a kapu-értékek naplózásával (`[this+0x668]` és `[this+0x99c]` egyezése, a singleton `+0x20c` flagje, a `[0x00d67849]` értéke). Ez dönti el a job-188 és a kód viszonyát. [blokkoló]

Pásztázás kell (`paszta.py`, memóriakapuval): a `[0x00d67849]` globális neve (Flipbook-beállítás?) és írói. [blokkoló a Shift-ág értelmezéséhez]

Válasz [részben, 2026-10-18]: a `0x005e8b10` a `FUN_005e8a70(this, mode)` mód-0 ágának belépési pontja. A `cmp byte ptr [ebp+0xc], 0` (`0x005e8b06`) után, a `jne` nem ugrik, és a `test ebx, ebx` (`0x005e8b10`) a C 127-130. sorának `param_1[0x93]++` (`+0x24c`) ágát nyitja. **Gyűjtemény:** `FUN_004edf60(this[0xaf] + 0xf8, &lista)` tölti a listát a `this[0xaf]+0xf8` objektumból; ennek az objektumnak az azonossága NINCS MEG (a `FUN_004edf60` törzse nincs a dumpban). **K-kapu van, három:** (1) a belépő kapu (C 117-122: a `0x009c2fc0` oneup-keresés és a `this+0x332e` jelző, valamint a `0x005696c0` és a `0x009cd8a0 == 0xf4242` ellenőrzés) `-1`-gyel tér vissza; (2) a `this[0x3aa]` objektum `+0xb4` vtábla-hívása nullát ad, és a függvény `-1`-gyel tér vissza; (3) a `this+0x336c` jelzőt (C-ben `param_1 + 0xcdb`, mutató-indexelés) a `this+0x332f` és a típuskód-szűrő (8, 9, 10, 11, 12, 23, 29) adja. Lásd még a Shift-ág (`DAT_00d67849`) mellékágát. [nem blokkoló]

#### 38.2.15 A Ctrl+5 feltétele, a qshow vezérlője és kilépése (#4443, 2026-10-18)

**Kérdés és módszer.** Ez a kör a Ctrl+5 módosító-feltételét, az `ytWindow`-hez tartozó bemutatóvezérlőt, valamint az Escape kilépési útját követte. A függvények mérete a bináris-indexből származik; a helyi diszasszemblálás a `picasapy-agent` venv `annot_disasm.py` eszközével készült. A PE-erőforrásokat, importokat és vtáblákat `pefile`-lal olvastam. Futó Picasa-mérést ez a kör nem végzett; a korábbi Colab-próbán a qshow megfagyott.

**1. A Ctrl+5 feltétele.** A `0x005e6710` eseménykezelő `0x005e680f`-nél az esemény `+0x10` módosító-bájtját olvassa, majd `0x005e6812`-nél a `0x04` bitet teszteli. Ha be van állítva, a `0x005e69cc` ágon meghívja a `0x005e60d0` billentyűkezelőt. Annak „5” ága (`0x005e6279`) a `0x005696c0` kapu hamis eredménye esetén hívja a `0x005e8a70(this, 1)` bemutatóutat. A Ctrl-feltétel tehát az esemény módosító-bájtjának `0x04` bitjénél dől el, nem a `0x005e60d0`-ben végzett `GetKeyState`-lekérdezéssel. A `0x005e6710` saját `GetAsyncKeyState(0x10)` hívása a Shiftet vizsgálja. A külön `ytWindow`-út `0x00984970` kezelője a `0x00984f8f`-nél közvetlenül lekérdezi a `VK_CONTROL` (`0x11`) állapotát, és azt a módosító-bájt `0x04` bitjébe teszi (`0x00984fba`-`0x00984fcc`); ez függetlenül megerősíti a bit Ctrl-jelentését. A főablaki esemény `+0x10` mezőjének írója ebben a körben **NINCS MEG**.

`pefile`-lal a PE erőforrásjegyzékében (`.rsrc`, `0x00da2000`) nincs `RT_ACCELERATOR` (`9`) típus. A bináris importálja a `USER32!CreateAcceleratorTableA` (`0x00c406e4`) és `USER32!TranslateAcceleratorA` (`0x00c4071c`) függvényt is, ezért ebből önmagában csak a beágyazott erőforrás-tábla hiánya következik, minden futásidejű gyorsítótábla kizárása nem. A vizsgált Ctrl+5 út közvetlen, kézi `WM_KEYDOWN`-kezelőág.

**2. A qshow vezérlőobjektuma és billentyűi.** A `0x00982bf0` konstruktor a `ytWindow` vtábláját (`0x00cd87fc`) állítja be. A `0x00983670` létrehozza az ablakot, majd a `GWLP_USERDATA` (`-21`) helyre ugyanennek az objektumnak a mutatóját írja. A `ytWindow` vtábla PE-ből olvasott elemei: `+0x1c = 0x00984970` és `+0x20 = 0x00985550`. A WndProc a `+0x1c` üzenetkezelőt hívja; a `0x00984970` a billentyűüzenetből módosító-bájtot épít, majd a `+0x20` metóduson át továbbít. A `0x00985550` a `ytWindow+0x64` gyermekre küldi az eseményt annak `+0x30` virtuális metódusán.

A gyermek a `QDrawable`: a `0x007fa7f0` konstruktor a `0x00cbd66c` vtáblát állítja be. A `0x008037e0` ezt rendeli a `ytWindow+0x64` mezőhöz, majd meghívja a QDrawable `+0x28` metódusát. Ennek célja a `0x007fa480`, amely a szülő `ytWindow` mutatóját a QDrawable `+0x50` mezőjébe írja. A PE-ből olvasott QDrawable vtábla `+0x30` eleme `0x00801270`, ez kezeli a qshow `WM_KEYDOWN` eseményeit:

| Billentyű | Bináris ág | Megállapított művelet |
|---|---|---|
| Escape (`0x1b`) | `0x008012a7` → `0x007fb820` | A qshow-ablak bezárási útját indítja. |
| Balra (`0x25`), Fel (`0x26`) | `0x008012bf`-`0x008012c9` → `0x008011b0` | Előző elem. |
| Jobbra (`0x27`), Le (`0x28`) | `0x008012cf`-`0x008012d9` → `0x00801210` | Következő elem. |
| Szóköz (`0x20`) | `0x008012df`-`0x00801344` | A `QDrawable+0x3bb` automatikus lejátszás-jelzőjét váltja; az aktív állapot külön leállítási/frissítési ágon megy. |
| Ctrl+Szóköz | `0x008012e3`-`0x0080130d` | A `QDrawable+0x3ba` mezőt `1`-re állítja. A mező hatása **NINCS MEG**. |
| Home (`0x24`), End (`0x23`) | teljes `0x00801270` függvény | Nincs hozzájuk külön ág; a vezérlő nem kezeli őket saját navigációs billentyűként. Az ismeretlen billentyű visszatérési értéke az ablak alapértelmezett üzenetkezelőjéhez engedi tovább az eseményt. |

**3. Az Escape kilépési célja.** A `0x007fb820` az Escape-ág végén a QDrawable `+0x24` getterével (`0x00a6ccf0`, a `+0x50` mező visszaadása) elkéri a szülő `ytWindow`-t, majd annak vtable `+0x14` metódusát hívja két nulla argumentummal. A `ytWindow` vtábla `+0x14` eleme `0x00983270`. Nulla első argumentummal, ha a `[0x00d67858]` jelző nulla, a függvény a saját HWND-jére `PostMessageA(hwnd, WM_CLOSE, 0, 0)` üzenetet tesz (`WM_CLOSE = 0x10`, importcím `0x00c4080c`). Ha a jelző nem nulla, a kód a jelenlegi szál ablakait sorolja fel az `EnumThreadWindows` importtal (`0x00c40710`) és a `0x00982fa0` callbackkel; a callback bizonyos ablakoknak `SendMessageA(hwnd, WM_CLOSE, 0, 0)` üzenetet küld (`0x00c40884`). Az Escape tehát a qshow bezárását kezdeményezi; hogy a bezárás után pontosan melyik főnézet és fókuszállapot látszik, futó mérés nélkül **NINCS MEG**.

**A két független út.**

- **A út, utasításszintű lánc:** `0x00983670` → `0x00984970` → `0x00985550` → QDrawable `0x00801270`; innen az Escape `0x007fb820`-ba és a szülő `ytWindow+0x14` kilépő metódusába jut. A főablaki `0x005e6710` külön útja a `0x04` bitet vizsgálja, majd a `0x005e60d0` „5” ágához enged.
- **B út, PE-adatok és RTTI:** a vtáblák nyers PE-olvasása a `ytWindow+0x14/+0x1c/+0x20` célokat (`0x00983270/0x00984970/0x00985550`) és a QDrawable `+0x30` célját (`0x00801270`) adja; a bináris-index RTTI-je a `ytWindow` és a QDrawable vtable-címeit azonosítja. A PE-importtábla a `0x00c4080c` címet `USER32!PostMessageA` néven azonosítja. A qshow eseménykezelő `GetAsyncKeyState(VK_CONTROL)` lekérdezése és `0x04` bitbe írása külön igazolja a Ctrl-bit jelentését.

A két út a vezérlőobjektum, a billentyűkezelő és az Escape bezárási kérésének céljában egyezik. A kódból statikusan igazolt események futásidejű látható hatását ez nem méri meg.

**Cáfoló kísérlet.** Megpróbáltam cáfolni azt, hogy a Ctrl+5 az erőforrásban tárolt accelerator-táblából jön: a teljes PE-erőforrástípus-jegyzékben nincs `RT_ACCELERATOR`; a megvizsgált billentyűút ehelyett a `0x005e6812` módosítóbit-próbán halad át. A PE más helyen dinamikus accelerator API-kat importál, ezért a negatív eredmény nem általánosítható minden gyorsítótáblára. Azt is próbáltam cáfolni, hogy a Home/End saját előző/következő műveletet kap: a teljes, index szerint 604 bájtos `0x00801270` függvényben nincs ilyen VK-ág, és a nem kezelt esemény a WndProc alapértelmezett útjára kerül. Mindkét cáfoló eredményt ugyanazzal a mércével ellenőriztem: függvénytörzs, PE-erőforrásjegyzék és nyers vtable/importadatok.

**Bizonyítottsági fok: feltételes.** A Ctrl+5 bitkapuja, a qshow objektumlánca és az Escape által küldött bezárási kérés statikus bináris- és PE-adatokkal megerősített. Az eredeti ablakon a billentyűk látható hatása, a bezárás utáni fókusz és a `QDrawable+0x3ba` Ctrl+Szóköz-jelző szemantikája nem lett futásban megmérve.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A Ctrl+5 a CThumbUI esemény `+0x10` mezőjének `0x04` bitjén át jut a `0x005e60d0` „5” ágához, amely mód 1-ben indítja a `0x005e8a70`-et. A statikus PE-erőforrásban nincs `RT_ACCELERATOR`. | A Nézet ▸ Időrend és a Ctrl+5 a #1903 óta inaktív. | A Ctrl-feltételt a főablaki vezérlő visszaállításakor tartsuk meg; az eseménybit íróját ne találgassuk. |
| A qshow a külön `ytWindow` és QDrawable objektumpárt használja. Balra/Fel előző, Jobbra/Le következő, Szóköz automatikus lejátszás-váltó, Escape bezárási kérés. Home/End nem kap egyedi navigációt. | A `TimelineView.qml` az alkalmazásablakon belüli év-/hónap-rács; qshow vezérlő nincs. | A bemutató saját teljes képernyős ablakában a fenti billentyűút és objektumhatár szükséges. |
| Escape a `ytWindow+0x14` (`0x00983270`) útján `WM_CLOSE`-t tesz az ablakra; a visszatérő főnézet futásban nem lett megfigyelve. | Nincs qshow ablak és kilépési út. | A qshow bezárása után az eredeti könyvtárnézethez térjen vissza; a fókusz részletét eredeti futásban kell ellenőrizni. |
| A bemutató tényleges kártyatartalma, dátumsorrendje és átmenetének képi/időbeli paraméterei korábbi körök alapján továbbra is **NINCS MEG**. | A mostani rács nem az eredeti bemutató. | A teljes reprodukció fejlesztése előtt a 38.2.1 és 38.2.9 nyitott tartalmi és animációs pontjait kell lezárni; addig csak a vezérlőhéj specifikált. |

**Nyitott pontok.** A főablaki esemény `+0x10` módosító-bájtjának írója; a `QDrawable+0x3ba` Ctrl+Szóköz-jelző jelentése; a `[0x00d67858]` ág futásidejű értéke és az általa érintett ablak; a bezárás utáni tényleges nézet és fókusz; továbbá a korábban rögzített kártya-, dátumsorrend- és átmeneti adatok. Ezekhez a főablaki WM_KEYDOWN esemény létrehozójának célzott követése, a jelző mezőíróinak `paszta.py`-s pásztázása, illetve eredeti Picasa futás kell. Ghidra-kör ehhez a körben nem szükséges.

**Nyitott kérdések mérlege (38.2.15).** 5 nyílt (módosítóbit-író, Ctrl+Szóköz-jelző, `[0x00d67858]` ág, bezárás utáni fókusz, korábbi tartalom/átmenet) · 3 lezárt (Ctrl+5 bitkapu, qshow vtable és kért billentyűk, Escape bezárási hívás) · 0 blokkolt · 0 hatókörön kívül.

#### 38.2.16 A `0x9ccc` parancs közvetlen ága és módparamétere (#4443, 2026-10-19)

**Kérdés és módszer.** A korábbi Ghidra-kör a `0x005e8a70` hívói közül nem azonosította, melyik tartozik a Nézet ▸ Időrend parancshoz. A helyi index xrefjeit, az érintett függvények utasításait (`annot_disasm.py`) és az eredeti PE ugrótábla-adatait (`pefile`) vetettem össze. Futó Picasa-mérés és Ghidra-dekompilálás ebben a körben nem történt.

**Parancs → ág → bemutató.** A `0x005cb990` parancs-elosztó a `0x005cba5d` címen levonja a `0x9c42` alapazonosítót. A `0x9ccc` ezért a `0x8a` indexet adja; a PE `0x005cdbbe` bájtja `0x2f`, és a `0x005cd9fc + 4×0x2f` ugrótábla-bejegyzése (`0x005cdab8`) a `0x005cbbdd` ágra mutat. Itt `push 1` (`0x005cbbdd`), majd `push ebx` és `call 0x005e8a70` (`0x005cbbe0`) következik: a menüparancs a bemutatót **1-es módban** nyitja.

Az ellenőrizhető, indexben szereplő közvetlen hívási helyek:

| Hívó ág | Hívás | Mód | Azonosító / jelölő |
|---|---:|---:|---|
| `0x005cb990` | `0x005cbbd3` | 0 | `0x9c6d`, `0x9c9f` menüparancsok |
| `0x005cb990` | `0x005cbbe0` | 1 | `0x9ccc` Nézet ▸ Időrend |
| `0x005d9cc0` | `0x005da743` | 0 | `thumbui/sbutton` |
| `0x005d9cc0` | `0x005da7ae` | 1 | `thumbui/timelinebutton` |
| `0x005e0f70` | `0x005e146f` | 0 | `"play"` parancság |
| `0x005e60d0` | `0x005e626f` | 0 | „4” billentyűág |
| `0x005e60d0` | `0x005e628a` | 1 | „5” billentyűág, a `0x005696c0` kapu után |

Ez az indexben látott négy közvetlen hívófüggvény hét hívási helye; nem állítás a közvetett, például vtable-hívások teljességéről.

**Két független ellenőrzés.** **A út:** az utasításokból követhető az azonosító csökkentése, az ugrótábla elérése, a `0x9ccc`-hez tartozó ág és a `push 1` / célhívás. **B út:** a nyers PE-táblaolvasás a `0x2f → 0x005cbbdd` célpárt adja; az index a `0x005cb990` függvényt a `0x005e8a70` közvetlen hívójaként tartja nyilván (két hívással). A pontos `0x005cbbe0` call-site címet az utasítások azonosítják. Ettől külön, a `0x00559150` menüépítőben a `0x0055a9b0`-`0x0055aa15` utasítások az `eMenuView::ID_VIEW_TIMELINE` címkét, a `Ti&meline` feliratot, az „5” gyorsbillentyű-jelölőt és a `0x9ccc` azonosítót írják a menürekordba. Az utak a parancs azonosításában és a mód-1-es bemutatóhívásban egyeznek.

**Cáfoló kísérlet.** A lehetséges szomszédos mód-0 ágat ellenőriztem: a PE ugrótáblában `0x9c6d` és `0x9c9f` a `0x005cbbd1` címre vezet, ahol a `0x005cbbd3` hívás előtt `push 0` áll. Ezzel szemben a `0x9ccc` saját táblabejegyzése `0x005cbbdd`-re vezet, ahol `push 1` áll. A nyers táblabejegyzések és a tényleges hívóutasítások ugyanazt az eredményt adják; a szomszédos ág nem cáfolja, hanem kizárja az off-by-one téves azonosítást.

**Bizonyítottsági fok: megerősített** a szűk állításra, hogy a `0x9ccc` közvetlen menüútja `0x005e8a70(this, 1)`-et hív: az utasításszintű út és a nyers PE-adatok/xref egyeznek, a menüépítő pedig külön azonosítja a parancsrekordot. Ez nem dönti el a bemutató tartalmának, animációjának vagy futásidejű kapuinak viselkedését. A helyi mérési archívumban ehhez a körhöz nem volt qshow/job-188 felvétel; a kijelölés nélküli megnyitásról szóló korábbi közlés ezért ebben a munkamenetben **NINCS MEG** közvetlen mérési bizonyítékként.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `0x9ccc` → `0x005cbbe0` → `0x005e8a70(this, 1)`; a Ctrl+5 „5” ága is mód 1-es hívást tartalmaz (`0x005e628a`), külön kapuval. | A `TimelineView.qml` régi év-/hónap-rács; a Nézet ▸ Időrend és a Ctrl+5 inaktív, az eredeti qshow-bemutató nincs megépítve. | A visszaállítás a külön bemutató-módot és a mód-1-es eredeti utat kövesse. A kijelölés nélküli megnyitás feltételét, a tartalmat és az animációt eredeti futásban kell lezárni; ezt a statikus ág feltárása nem helyettesíti. |

**Nyitott kérdés mérlege (38.2.16).** A `0x9ccc` → mód 1 közvetlen hívási útja lezárt. A qshow futásidejű K-kapui, a kijelölés nélküli viselkedés, a teljes tartalom/sorrend és az animáció továbbra is nyitott; ezeket a 38.2.14-38.2.15 nyitott pontjai részletezik.

#### 38.2.17 Az Időrend bemutató futás közben, Wine virtuális asztalon (#4443, job-217, 2026-10-20)

**Forrás:** picasa-colab-jobs job-217, 12 képernyőkép és `xinfo.txt`. Eredeti Picasa 3.9, alapállapot (C:\PicasaTeszt, 24 kép), a Picasa a Wine virtuális asztalán (1280×1024, `wine_desktop`, #215). Lépések: Ctrl+5, majd Right, Right, Escape.

**A 38.2.2 fekete kockájának oka.** A job-102-ben a qshow ablak a sima X-kijelzőn fekete maradt, és bemenetet sem kapott. A virtuális asztalon ugyanez a parancs kirajzolódik, és a billentyűket is fogadja: a fekete kép a Wine ablakkezelésének következménye volt, nem a bemutató viselkedése.

**Amit a felvétel mutat (megerősített, képkockák):**

| kocka | mit mutat |
|---|---|
| 04 (Ctrl+5 után) | teljes képernyős fekete háttér, középen kb. 600×480-as bemutatópanel: szürke háttérgörbe, jobbra fent a mappa neve („PicasaTeszt”) és dátuma („October 2026”), alatta pontozott ív, az ív végén a mappa képeinek egymásra döntött bélyegei; alul vezérlősáv (bal szélen lista-ikon, mellette balra mutató nyíl, középen balra nyíl, lejátszás, jobbra nyíl), legalul dátumcsúszka a két szélén „October 2026” felirattal |
| 07-08 (Right után) | a panel a következő gyűjteményre vált: „Recently Updated”, „October 2026”, más háttérkép a görbe mögött; a csúszka gombja jobbra lép |
| 11 (Escape után) | teljesen fekete kocka (a kilépés átmenete) |
| 12 | visszatér a főablak |

**Következtetés.** A Ctrl+5 kijelölés nélkül is az Időrend bemutatót nyitja; a bemutató gyűjteményenként egy kártyát mutat (név, dátum, bélyegköteg), a Right a következő gyűjteményre lép, az Escape kilép. A panel a teljes képernyőn középre igazított, fix méretű terület, körülötte fekete.

**Billentyűk és kattintás (job-219, job-220, 2026-10-20, megerősített, képkockák).** A vezérlősávra adott egérkattintás (lejátszás 640,690; lista-ikon 366,690) a job-219-ben semmit nem változtatott, a billentyűk igen. A job-220-ban a **szóköz** az aktuális kártya gyűjteményét teljes képernyős diavetítésként indítja: az első kép (a szürke átmenet) fekete háttéren, nagyítva jelenik meg, majd kisebbre vált (6. és 12. kocka, a halvány „PicasaTeszt” felirattal); az End, Left és Home billentyűkre képről képre lép (13. kocka: a színtábla, 17. kocka: egy űrkép); az Escape kilép a főablakba (20-21. kocka).

**Nem dőlt el ebből a felvételből:** az átmenet animációja (a kockák 3 másodpercenként készültek), a lejátszás gomb automatikus léptetésének üteme, a lista-ikon funkciója és a csúszka húzásának hatása. Ezekhez a következő felvétel lépései: a lejátszás gomb és a lista-ikon megnyomása, 1 másodperces kockákkal.

#### 38.2.18 Az Időrend bináris újraellenőrzése (#5401, 2026-10-20)

**Kérdés.** A #5401 négy nyitott pontja: a bemutató képláncának forrása és sorrendje; a kártyák mozgásának képlete és időzítése; az alsó vezérlők és a dátumcsúszka működése; végül a diavetítésbe lépés és a visszatérés helye. Ez a kör csak helyi bináris- és indexadatot olvasott. A futásfelvételek korábbi, 38.2.17-ben dokumentált eredményeit nem tekintem újramért adatnak: a szükséges nyers képek nincsenek a helyi mérőadat-archívumban.

**1. Képlánc és forráshalmaz.** A `CThumbUI::MakeTimeline` (`0x005e8a70`) az Időrend ágban a `CThumbUI+0x2c0` kollekció darabszámát kéri le (`0x005e9434`, `0x004a0980`), majd 0-tól a darabszámig járja az indexet (`0x005e9490`). Minden elemnél a CThumbUI vtable `+0x90` metódusát hívja; a thunk (`0x00562cc0`) a `CThumbUI+0x2bc` szolgáltató vtable `+0x20` metódusának adja át az indexet. Ez egy indexelt külső sorozat bejárását bizonyítja, nem a sorozat eredetét. A szolgáltató típusa, a könyvtár/mappa/album/Picture Tray tagsága, a dátumrendezés mezője és iránya, valamint a gyűjteményenként megjelenített képek száma és azonossága **NINCS MEG**. A 38.2.17 job-217 leírása egy mappakártyát mutatott, a Right pedig a következő kártyára váltott; a nyers képek hiánya miatt ez itt csak korábbi, nem újraellenőrzött mérési feljegyzés.

**2. Átmenet, háttér és kártyarajz.** A Timeline-gomb útja (`0x007fda00`) ellenőrzi a `[this+0x2d8]` jelzőt és a `[this+0x538]` mutatót, QPC-értéket rögzít a `[this+0x430]` mezőbe, majd `0x00802230(this, 1)` hívással indít frissítést. A frissítő a `[this+0x3f0]` elemszámot, `[this+0x3f4]` indexet, `[this+0x3ec]` listát, valamint a `+0x400/+0x404` és `+0x474/+0x478` geometriai mezőket használja; a bináris konstansokat is beolvassa, de ezek jelentése és a mezők kapcsolata nincs biztonságosan feloldva. A pálya, a mozgás iránya, a pozíció/méret/forgatás/átlátszóság függvénye, a görbe és az átmenet hossza **NINCS MEG**. QEMU-s képletigazolás nem történt: a helyi `qemu-i386` nem ad qshow/Win32 felületet futtató próbapadot, a `qemu_harness` csak különálló függvényeket futtat kézzel felépített állapottal; Wine és `qemu-system-i386` nincs telepítve.

Az ismert `CTransTimeline` cím (`0x00816b00`) nem a qshow képkocka-frissítőjeként azonosítható: közvetlen utasításolvasata `<CTransTimeline>`, `<defaulttrans>` és ismételt `<trans>` XML-elemeket ír, benne filmátmenet-paraméterekkel. Hívásai a `0x006175c0`, `0x00618050`, `0x0061d020` és `0x00814250` körüli filmkészítő útban vannak; a `CTransTimeline` vtable írói `0x0080f395` és `0x0080f620`, UI-vtable írója `0x0080f3fa`. A qshow animációjának jelöltje a külön `0x00802230`, de annak képlete nyitott. A `0x007fb210` csak a `timeline`, `timelinedot`, `sliderthumb`, `startbutton`, `exit` és további overlay-erőforrásokat tölti be és skálázza; ez nem bizonyítja sem azok rajzolási képletét, sem kattintási műveletét. A fekete háttér és a kártya elemei kizárólag a korábbi job-217 feljegyzésből ismertek; a binárisból e körben nem sikerült a teljes rajzútjukat azonosítani.

**3. Vezérlők és időzítés.** A `0x008032e0` OneUpfelületi ág kezeli a `oneup/timeline` kattintását, a `oneup/exit` visszahívását, valamint a külön `prev`/`next` parancsokat; ez önmagában nem köti az alsó overlay `startbutton`, `exit` vagy listaikon grafikáit ezekhez a parancsokhoz. A qshow billentyűkezelője (`0x00801270`) `WM_KEYDOWN`-on a Bal/Fel kódot előző elemre (`0x008011b0`), a Jobb/Le kódot következő elemre (`0x00801210`) irányítja. Escape a `0x007fb820` kilépési ágat hívja. A szóköz a `[this+0x3bb]` automatikus lejátszási jelző ágát váltja; ez statikusan egyezik az `Auto Play` vezérlő útjával, de nem azonosít önmagában teljes képernyős diavetítés-ablak létrehozását.

Az automatikus továbblépés küszöbe kiolvasható. A `0x00802060` a `0x009a51b0` helperrel számít eltelt időt: `QPC_now - QPC_start`, szorozva a `QueryPerformanceFrequency` reciprokával; a QPC-kezdőérték a `[this+0x520]` mezőben van. Ezután a `0x4019b0` getterrel beolvassa a `[this+0x760]` (`Preferences\SlideshowEffectTime`) értéket, egész másodpercként lebegőpontos értékké alakítja, és az eltelt QPC-másodperccel hasonlítja össze. Ha a beállított érték kisebb az eltelt időnél, a `0x00802630` léptető út fut. A `[this+0x760]` értékét a `0x00802ff0` `second`/`seconds` felirattal jeleníti meg, így a beállítás mértékegysége két külön kódútból is másodperc. A `0x007fa7f0` felépítő a `Preferences\SlideshowEffectTime` olvasóhívásnak 3-as kezdeti értéket ad át (`0x007facd3`-`0x007fad05`); az aktív felhasználói értéket ez nem rögzíti. A frissítő callback üteme, vagyis az ellenőrzés milyen időközönként fut le, **NINCS MEG**; így a beállítási küszöb ismert, a tényleges képkocka-/léptetési időpont nem. A callback címe a `ytCallback<QDrawable>::vftable` (`0x00cbd6c8`) `+0x04` elemében `0x00803ab0`; a vtable-t a `0x00803b00` állítja be. A QDrawable felépítő ezt a callback-objektumot a `0x007fae76` helyen átadja a `0x0097d150`-nek. Maga a callback (`0x00803ab0`) QPC-értéket ír, majd a `[QDrawable+0x3bf]` jelző nullás ágában meghívja a `0x00802060` frissítőt. A callback regisztrációs út egy része tehát megvan, de az eseménylista ütemezője és periódusa nincs feloldva.

A `timelinedot`, `sliderthumb`, `startbutton`, `exit` és listaikon pontos kattintási/húzási célja, a dátumcsúszka dátum- vagy képindexre vetítése, valamint az, hogy a listaikon melyik nézetet nyitja, **NINCS MEG**. A korábbi job-219 feljegyzés szerint a kattintási próba nem változtatott a képen; ez nem bizonyítja, hogy az eredeti Windows-felületen a gombok hatástalanok.

**4. Diavetítésbe lépés és visszatérés.** A korábbi job-220 feljegyzés szerint szóközre az aktuális kártya gyűjteménye teljes képernyős diavetítésként jelent meg, majd Escape a főablakba tért vissza. A nyers mérőadat hiányában ez most nem ellenőrizhető. A statikus `0x00801270` szóközága a qshow automatikus lejátszási jelzőjéhez vezet, nem látszik benne közvetlen új ablak létrehozása. Az Escape (`0x007fb820`) a szülő `ytWindow` bezárási visszahívását indítja. A teljes képernyős diavetítésre váltás pontos hívási lánca, a visszaállított gyűjtemény/képkocka és a fókusz ezért **NINCS MEG**.

**Két független út.** **A út:** a `0x00816b00` utasításszintű olvasata XML-szerializálót mutat; a `0x007fda00` → `0x00802230` híváslánc külön választja a qshow animációfrissítőjét. **B út:** a `0x00cbdcc4`/`0x00cbdcec` `CTransTimeline` vtable- és RTTI-adatai, az író konstruktorának/hívóinak filmkészítő xref-lánca, valamint a `picasa-create-features.md` 2.4. szakaszának független leírása ugyanazt a film-XML-szerializáló szerepet adja. A két út a szűk állításban egyezik: a `0x00816b00` a filmkészítés XML-szerializálója, nem a qshow frissítőfüggvénye. Ez nem zárja ki, hogy a film-átmenet típusa máshol közös adatot használjon.

Az automatikus időlépésre szintén két út áll rendelkezésre. **A út:** `0x00802060` és `0x009a51b0` QPC-időből másodpercet képez, majd a `+0x760` értékkel hasonlítja össze. **B út:** a külön `0x00802ff0` kód ugyanazt a `+0x760` mezőt olvassa és `second`/`seconds` szöveggel formázza. A mértékegység és a beállított küszöb szerepe egyezik; a callback ütemét és a konkrét futó értéket egyik út sem adja meg.

**Cáfoló kísérlet.** Megpróbáltam cáfolni, hogy a `CTransTimeline` (`0x00816b00`) számolja a qshow mozgását: a függvényt közvetlenül végigolvastam; XML-író hívásokat, csomópontneveket és filmátmenet-paramétereket ír. Ezután ettől függetlenül a `.text` utasításait a kötelező `paszta.memoria_kapu()` után streaming módban kerestem közvetlen hívásokra és vtable-címírásokra; a writer közvetlen hívói és a vtable-írók a filmkészítő útban vannak, míg a qshow felépítője a `0x007fda00`/`0x00802230` frissítőt hívja. Ez cáfolja, hogy a `0x00816b00` volna a qshow közvetlen animátorfüggvénye. A közvetett hívás vagy közös típus használatának teljes kizárására a pásztázás nem alkalmas, ezért ilyen negatív állítást nem teszek.

**Bizonyítottsági fok: nyitott.** A `CTransTimeline` szerializáló szerepe és a `SlideshowEffectTime`-küszöb szűk állításai két egymástól külön út egyezésével megerősítettek. A négy elfogadási pont közül egyik sem áll rendelkezésre teljesen: a forrás/rendezés, mozgásképlet, overlay-működés és a Space utáni visszatérési állapot nyitott. A korábbi Wine-képkockák csak megerősítő, itt nyers fájllal nem újraellenőrzött feljegyzések.

| állítás/érték | bizonyíték | fok |
|---|---|---|
| indexelt bemeneti sorozat és elemszám-bejárás | bináris `0x005e9434`, `0x005e9490`, thunk `0x00562cc0` | feltételes |
| gyűjtemények forráshalmaza, rendezési mező/sorrend, gyűjteményenkénti képlista | NINCS MEG | nyitott |
| átmenet-indítás és QPC-kezdőérték | bináris `0x007fda00`, `0x00802230` | feltételes |
| mozgás képlete, görbéje, iránya és időtartama | NINCS MEG | nyitott |
| `SlideshowEffectTime` beállított értéke a QPC-eltelt másodperchez hasonlítva | bináris `0x00802060`, `0x009a51b0`; második út: `0x00802ff0`, `0x007facd3` | megerősített (küszöb, nem frissítési ütem) |
| overlay kattintás/húzás, csúszka dátumleképezése, listaikon funkciója | NINCS MEG | nyitott |
| szóköz állapotfüggő ága, a qshow `[+0x3b8]` mező írása és a pontos visszatérés | bináris `0x00801270`, `0x00803110`; Ghidra/objektumkapcsolat: 38.2.21 §4; mérés: job-220 nyers adat NINCS MEG | a feltételes 0-s módág megerősített; a futásidejű látvány és visszatérés nyitott |
| `CTransTimeline` (`0x00816b00`) film-XML-szerializáló | bináris `0x00816b00`; független RTTI/vtable/xref és `picasa-create-features.md` 2.4. | megerősített |

**Nyitott - következő pontos lépések.**

- `Ghidra-kör kell: 0x005e8a70 - a CThumbUI+0x2bc szolgáltató konkrét típusa, a +0x2c0 forráskollekciója, upstream rendezési mezője és sorrendje [blokkoló]`
- `Ghidra-kör kell: 0x00802230 - a qshow-átmenet képenkénti pozíció/méret/forgatás/átlátszóság függvénye, easingje, végpontjai és időtartam-mechanizmusa [blokkoló]`
- `Ghidra-kör kell: 0x00a52890 - a sliderthumb, timelinedot, startbutton, exit és listaikon hit-test/callback útja, valamint a csúszka dátum-/képlista-leképezése [blokkoló]`
- `Ghidra-kör kell: 0x0097d150 - a 0x007fae76 callback-objektum átadásának eseménylista-útja, a QPC-frissítés forrása és a pontos ütemezési periódus [blokkoló]`
- ~~`Ghidra-kör kell: 0x00801130 - a szóköz/Auto Play ág teljes diavetítés-váltási útja, valamint a visszatéréskor megőrzött gyűjtemény és képpozíció [blokkoló]`~~ A statikus, állapotfüggő átmenetet a 38.2.65 rögzíti; nyitott marad a futásidejű előfeltétel és a visszatéréskor megőrzött gyűjtemény/képpozíció.

**A #5401 „Kész, ha” pontjai.** (1) Képlánc és forráshalmaz: ⛔ csak az indexelt lista bejárása ismert; a forrás, sorrend és elemlista nyitott. (2) Átmenet: ⛔ az indítóút és a QPC-kezdés ismert, a mozgásfüggvény nincs meg; QEMU-futtatás nem történt, mert nincs qshow-UI-harness. (3) Vezérlők: ⛔ a billentyűk statikus ága részben ismert, de az overlayek műveletei, csúszkaleképezés és frissítési periódus nyitott; a régi felvétel csak megerősítés. (4) Diavetítés és visszatérés: ⛔ a Space jelzőág és az Escape bezárási út ismert, a látható átmenet és a visszatérési pozíció nincs binárisan/futásban lezárva.

**Fejlesztési következmény.** A #5377 teljes animált bemutatójának folytatása továbbra is blokkolt. A fenti nyitott pontok lezárása előtt a képlista-, mozgásképlet-, vezérlőleképezés- vagy folytatási pozíció-értéket implementációban megadni becslés lenne.

#### 38.2.19 Az Időrend bináris feltárása, 2. kör: képlet, időzítés, Space, eseményút, vezérlők (#5401, 2026-10-20)

**Kérdés és hatókör.** A 38.2.18 öt nyitott tételét dolgoztuk fel: a mozgásképletet (1), az időzítést (2), a Space-ágat (3), az eseménylistát (4) és a vezérlőket (5). Bemenet: a két scratchpad-dekompilálás, a helyi bináris-index és a `pe_dis` diszasszemblálása. Futásfelvétel és QEMU-futtatás nem volt, mert a helyi környezetben nincs qshow-felületet futtató próbapad. Minden állításhoz bináris címet adunk. Ahol a dekompilált törzset nem diszasszemblálással ellenőriztük, ezt kimondjuk.

**Konstansok.** A típust a betöltő utasítás dönti el (`fld dword` float, `fld qword` double). Az értékek a `pe_dis` f32/f64 olvasásából származnak.

| bináris cím | betöltés | érték | szerep |
|---|---|---|---|
| `0x00cf4320` | `fld qword` (double) | 0,1499999761581421 | a `c` szorzó (a 0,15 float-pontossága) |
| `0x00c72150` | `fmul qword` (double) | 0,5 | a y-ág fele |
| `0x00cf39e4` | `fadd dword` (float) | 4294967296 (2^32) | negatív W előjel-korrekciója |
| `0x00cf3ac0` | `fadd qword` (double) | 4294967296 (2^32) | negatív H előjel-korrekciója |
| `0x00d35808` | `fld dword` (float) | 2276,5556640625; betöltés csonkolva: 2276 | csak a `p[0xb9]` ágban (0x008023bb); a csonkolást az RC=11 adja (0x008023c6-0x008023de) |

**1. Mozgásképlet (0x00802230).**

- Visszatérés `4`-gyel: ha `[this+0x3f0] >> 1 <= [this+0x3f4]`, vagyis a darabszám fele nem nagyobb az indexnél (0x00802299-0x008022b7).
- Az elem: `[this+0x3ec][index]` (0x008022ba-0x008022c0).
- Az előző eltolás mentése: `[this+0x400]` → `[this+0x408]`, `[this+0x404]` → `[this+0x40c]` (0x008022c3-0x008022d5). Vagyis `param_1[0x102]` és `param_1[0x103]`.
- Két egymás utáni véletlen szám: az első `rand()` (r1, 0x008022db) az y-ágat adja, a második (r2, 0x008022f2) az x-ágat.
- A `_rand` (0x00c08221) MSVC-féle lineáris kongruens generátor: állapot = állapot × 0x343fd + 0x269ec3, kimenet = (állapot >> 16) & 0x7fff. Tartomány: 0 és 32767 közötti egész.

**A float-trükk.** Az `(r + 0x3f8000) << 8` egészet a verembe írja (0x008022e6-0x008022ff), majd `fld dword`-del tölti vissza (r2: 0x00802306, r1: 0x00802353). Ez bitminta-újraértelmezés, nem számértékű átalakítás. A bitminta 0x3f800000 + r × 256, ami f = 1 + r / 32768 értéket ad, mert r × 256 kisebb 2^23-nál. Így f - 1 = r / 32768 pontosan, a tartománya [0; 0,99996948]. A Ghidra-dekompiláció `(float)` öntést mutat, ez félrevezető.

**x-eltolás (`param_1[0x100]`).**

x = fl32( c × W' × r2 / 32768 ), ahol c = 0,1499999761581421, W = `[this+0x474]` (`param_1[0x11d]`), és W' = W, ha W ≥ 0, különben W + 4294967296.

- W betöltése és előjel-korrekciója: 0x0080230d-0x0080233b.
- A c szorzó: 0x00802345-0x0080234b.
- Tárolás a verembe, majd `[this+0x400]`-ba: 0x0080234f, 0x0080238d-0x00802391.
- Tartomány: 0 ≤ x < 0,15 × W' (r2 legfeljebb 32767).

**y-eltolás (`param_1[0x101]`).**

y = fl32( c × 0,5 × H' × r1 / 32768 ), ahol H = `[this+0x478]` (`param_1[0x11e]`), H' ugyanúgy, mint W'.

- A H-ág: 0x00802353-0x0080237f (a 0,5 a 0x00802370 fmul-ban, az előjel-korrekció a 0x0080237f fadd-ban).
- A c szorzás: 0x00802397. Tárolás `[this+0x404]`-be: 0x0080239d-0x008023a1.
- Tartomány: 0 ≤ y < 0,075 × H'.

**W és H jelentése.** A két értéket (w, h) párként a `p[0xb8]` objektum +4-es metódusa kapja (dekompiláció 126. sor, `&local_60`), a középre igazítás pedig a méretkülönbség felét használja (dekompiláció 162-163. sor). Hogy ez a kép vagy a kártya mérete, **NINCS MEG**. A képlet a számokat ettől függetlenül adja.

**Visszatérési értékek.**

- `0` (0x0080260e): a képkocka elkészült.
- `4` (0x008022b7): az index kiesett a darabszámból, nem rajzol.
- `-1` (0xffffffff): a `p[0xb8]+4` callback nem nulla értéket adott (dekompiláció 126-130. sor).
- A hívó 0x00802630 nem nulla értéknél, ha a darabszám nem nulla, újrapróbálja (0x008026ee-0x008026fc, diszasszemblálva). Tehát a 4 és a -1 is újrapróbálást vált ki. A ciklus lezárását a 0x0080275b és a 0x00802765 ág adja; ezt nem vizsgáltuk: **NINCS MEG**.

**Az előző érték ([0x102], [0x103]).** A 0x00802230 törzsében csak írás van (dekompiláció 91-92. sor). Olvasót nem találtunk. Hogy a kártyák átmenete ezt használja-e: **NINCS MEG**. Olvasó kereséséhez teljes `.text` pásztázás kell (`paszta.py`), amit ebben a körben nem futtattunk.

**Mi nincs még.** A képlet nincs megfeleltetve a rajz geometriájának (a kártya helye a képkockán). Azt, hogy a rajzoló a `[this+0x400]` és `[this+0x404]` mezőkből milyen egységben olvas: **NINCS MEG**.

**2. Időzítés (0x00802060, 0x007fda00, 0x00803ab0, 0x009a51b0, 0x004019b0).**

- Eltelt idő: a `0x009a51b0` számítja: (QPC most - `[this+0x520]`) × (1/QPF), másodpercben. A reciprokot első híváskor tölti be, és `0x00d678e8`-ban tárolja (0x009a51c4-0x009a51ec).
- Küszöb: a `0x004019b0` a `[this+0x760]` objektumot olvassa. Ez registry-olvasó: a 0x004019ec és a 0x00401a1f címen a 0x009a4890 hívás KEY_ALL_ACCESS (0x000F003F), illetve KEY_READ (0x00020019) maszkot kap. A kulcs `Preferences\SlideshowEffectTime`: a sztring (0x00c8e5f4) a 0x007fa7f0 és a 0x005643e0 függvényből hivatkozott. Az objektumot a 0x007fa7f0 építi (0x007facdb-0x007facf2, a `Preferences` és a `SlideshowEffectTime` sztringekkel).
- A küszöb előjel nélküli 32 bites érték: negatív értéknél +2^32 (0x008020b9-0x008020c5).
- Alapérték: 3 (0x007facd3, `mov [esp+0x3c], 3`, az objektum építése előtt). **Feltételes**: a 0x00407a20 belső alapérték-kezelését nem vizsgáltuk. A felhasználó tényleges értéke a registryből jön, a binárisból nem olvasható ki: **NINCS MEG**.
- Összehasonlítás lebegőpontosan, nem egész másodpercre levágva. A 0x008020cb-0x008020d4 `fcomp qword` alapján a léptetés akkor fut, ha a küszöb kisebb az eltelt időnél. Ha nem, csak a `[this+0x3c1]` nem nulla esetén léptet (0x008020d6-0x008020dd). A dekompilált `(LONGLONG)` öntés a diszasszemblálásban nem jelenik meg.
- A léptetés-döntés sorrendje (0x00802060, diszasszemblálva):
  1. `[this+0x3bb] != 0`: visszatér `1`-gyel, nincs léptetés (0x00802066-0x00802078).
  2. `[this+0x3b8]` és a 0x00801cb0 hívás (0x0080207e-0x00802093).
  3. `[this+0x518] != 0`: azonnal léptet (0x00802095-0x0080209e).
  4. Egyébként: léptet, ha a küszöb kisebb az eltelt időnél, vagy ha `[this+0x3c1] != 0`.
  5. Sikeres léptetés után `[this+0x518] = 0` és `[this+0x520]` = most (0x008020f2-0x00802108).
- **A képkocka-frissítés is újraindítja az időt.** A 0x00802230 sikeres frissítésnél `[this+0x520]` = most (0x008025b9-0x008025cf). Egy köztes újrarajzolás ezért eltolja a következő léptetést. Hogy milyen gyakran fut a frissítés: **RÉSZBEN JAVÍTVA (38.2.20, 2. szakasz):** a `0x007fb540` 50 ms-os ciklus, és csak a `[this+0x51a]` jelzőre hív (legfeljebb 20 Hz). A jelző-beállítás gyakorisága **NINCS MEG**.
- **Periódus.** Ha nincs köztes újrarajzolás, a léptetési küszöb **S másodperc**, ahol S a `SlideshowEffectTime` értéke. **PONTOSÍTVA (38.2.20, 1. és 7. szakasz):** ez küszöb, nem periódus; a léptetés az első, küszöb feletti callback-hívásnál történik. A pontos ütem a callback hívási ritmusától függ: **NINCS MEG**.
- **A callback (0x00803ab0).** Ha `[callback+8]` (QDrawable) nulla, `-1`-et ad (0x00803abc-0x00803ac0). Egyébként a QPC-t `[callback+0x18]`-ba írja (double), és ha `[QDrawable+0x3bf] == 0`, meghívja a 0x00802060-at (0x00803ac2-0x00803ae0).
- **Az átmenet indítója (0x007fda00).** Ha `[this+0x2d8] != 0` és `[this+0x538] != 0`, a 0x00802230-at `1`-es jelzéssel hívja, az időt `[this+0x430]`-ban rögzíti, majd beállítja a `[this+0x3ba] = 0`, `[this+0x3bb] = 0`, `[this+0x3b8] = 1`, `[this+0x3b9] = 1` jelzőket (dekompiláció 384-396. sor).

**3. Space (0x00801270, 0x00801130, 0x00803110).**

- A billentyű-kezelő (0x00801270) csak WM_KEYDOWN-ra (0x100) reagál. A 0x102 (WM_CHAR) más ágra megy (0x0080128e-0x0080129e). A szóköz a VK 0x20 (0x008012df-0x008012e1).
- Ha a globális `[0xd67849]` nem nulla, és a Ctrl (VK 0x11) le van nyomva (a `[0xc406f8]` importtal kérdezve), `[this+0x3ba] = 1`, a visszatérés 0x000F4240 (0x008012e3-0x008012fb).
- Egyébként, ha `[this+0x3bb] == 0`: `0x00801130(this)` (0x00801317-0x00801334), a visszatérés 0x000F4241.
- Ha `[this+0x3bb] != 0`: `0x00803110([this+0x2dc])` (0x00801319-0x0080131f), a visszatérés 0x000F4241.
- **0x00801130 (váltás).** `[this+0x3bb] = ([this+0x3bb] == 0)` (`sete`, 0x00801134-0x0080113f). A 0x0097e510 az új értékkel hívódik (0x00801146). Célja: **NINCS MEG**.
  - Új érték `1`: `0x00802c20(this)` (0x00801159). Ha `[this+0x3ba] == 0`: `0x00aa6f40(this+0x58)` (0x00801167-0x0080116a). Mindkét függvény belseje: **NINCS MEG**. Ettől a léptetés (0x00802060) nem fut.
  - Új érték `0`: `0x00802230(this, 0)` (0x00801178), majd `0x009aabf0([this+0x444])` (dekompiláció 352. sor).
- **0x00803110 (második ág).** `esi = [edi+0x25c]`, ahol `edi = [this+0x2dc]`. Ha `[esi+0x3be] != 0`: `0x00801cf0(esi)` (0x0080311d-0x00803127). `[esi+0x518] = 1` (0x00803131), vagyis a következő tick azonnal léptet. A QPC → `[esi+0x520]` (0x00803138-0x00803150). `[esi+0x3b8] = 0` és `[esi+0x428] = 0` (0x00803142-0x00803149). Végül `0x00801130(esi)` (0x0080315c): az `esi` jelzőjét 1-ről 0-ra váltja, vagyis folytat. Hogy `esi` azonos-e a `this`-szel: **NINCS MEG** (a `[this+0x2dc]` objektum felépítése nincs feltárva).

**Összegzés (Space).** A szóköz a léptetést szünetelteti és folytatja a `[this+0x3bb]` jelzőn keresztül. A nem nulla jelző tiltja a léptetést. A 38.2.18 „automatikus lejátszási” jelzője ezért félrevezető lehet: a név a menüből jön, a viselkedés más. Teljes képernyős ablak létrehozását a közvetlen ágban nem találtunk; a két hívott függvény (0x00802c20, 0x00aa6f40) belseje **NINCS MEG**.

**Billentyű-ágak, amelyeket nem ellenőriztünk.** A 38.2.18 szerint a Bal/Fel a 0x008011b0-ra, a Jobb/Le a 0x00801210-re megy. A diszasszemblálás szerint a Bal és Fel a 0x008014bc, a Jobb és Le a 0x008014ac ágra ugrik (0x008012bf-0x008012d9). A 0x008011b0 és a 0x00801210 hozzárendelését ebben a körben nem ellenőriztük.

**4. Eseménylista (0x0097d150).**

- A függvény a tulajdonos-szálat (`DAT_00d3a568`) és a rekurziószámlálót (`DAT_00d3a56c`) kezeli. Zárolás: a `DAT_00d3a570` kritikus szakasz, vagy a `DAT_00d3a554` jelzőtől függően egy vtable-zár (dekompiláció 242-255. sor).
- `arg2 = 0`: hozzáfűzés a globális mutatótömbhöz (`DAT_00d69418`, darabszám: `DAT_00d6941c >> 1`, bit0 jelző). A növekedés 2-hatványonként történik 1 MiB-ig, utána 1024 elemenként (dekompiláció 256-290. sor).
- `arg2 != 0`: a `0x00982400(&arg1)` keresés. Találat esetén nincs új tétel, visszatér 4-gyel. Ha nincs találat, `0x0097d640`.
- Sikeres hozzáfűzés után is `0x0097d640` hívódik (dekompiláció 283-287. sor). A 0x0097d640 tehát a közös vég.
- Hívóhelyek száma: 26 (a dekompilált fájl fejléce). A qshow-építő 0x007fa7f0 a 0x007fae76 címen hívja `arg2 = 1`-gyel (0x007fae73-0x007fae76: `push 1`, `push eax`), miután a callback-objektumot a 0x00803b00 vtable-beállítással felépítette (0x007fae6a).
- **NINCS MEG**: a lista futtatója, vagyis a periodikus hívó. A 0x0097d640 két hívója a 0x0097d150 és a 0x0097d370. A 0x0097d370-nek 23 hívója van az indexben, köztük a 0x007fb5a0, aminek egyetlen hívója a 0x007fae90. **JAVÍTVA (38.2.20, 1. szakasz):** a `0x0097d370` nem a periodikus hívó, a futtató a `0x0097fc30` üzenethurok.

**5. Vezérlők és forráskollekció.**

- **0x005e8a70 (CThumbUI::MakeTimeline).** A név sztringből is igazolt: a `CThumbUI::MakeTimeline` és a `Preparing timeline...` sztring ide mutat (string_xrefs).
  - **Kapcsoló.** A `Preferences\BigSlideshow2` objektumot a 0x005e9409-0x005e9415 építi, alapértéke `1` (`mov [esp+0x44], 1`, feltételes: a belső alapérték-kezelés nincs feltárva). A 0x005e941e-nál a 0x004019b0 olvassa, és a 0x005e9425 `jne` nem nulla értéknél a 0x005e95cc-re ugrik. Mi van ott: **NINCS MEG**.
  - **Számlálás (nulla érték esetén).** A `[ebx+0x2c0]` objektumon (`this+0x2c0`, 0x005e942e) a `0x004a0980` a darabszámot adja (0x005e9434). Ezután ciklus: `(*this)[0x90](i)` minden `i`-re (dekompiláció 491-519. sor, nem diszasszemblálva). A kollekció típusa és a rendezés: **NINCS MEG**.
  - **Szolgáltató.** `[this+0x2bc]` (dekompiláció 136, 175, 246, 291, 461. sor). A Shift-ágban (`GetAsyncKeyState(0x10)`, dekompiláció 244-245. sor) a szolgáltató `[+0x4ec]` darabszámú listáját járja be, és 13 típuskód alapján szűr (dekompiláció 250-256. sor). A típuskódok jelentése: **NINCS MEG**.
- **0x007fb210 (overlay-betöltés).** A string_xrefs szerint itt töltődnek: `overlays/left`, `overlays/right`, `overlays/mouse`, `overlays/rollovermouse`, `overlays/exit`, `overlays/timeline`, `overlays/timelinedot`, `overlays/sliderthumb`, `overlays/startbutton`, `overlays/overlay`. A rajzolás és a kattintás: **NINCS MEG**.
- **0x00a52890 (üzenetkezelő, `__thiscall`).** A dekompilált `switch` egér-üzeneteket kezel: 0x201-0x208 és 0x20a (dekompiláció 1401-1653. sor). Használja a SetCapture/ReleaseCapture párost, a ScreenToClient-et és a SetCursor-t (`LoadCursorA(0, 0x7f00)`, dekompiláció 1885-1886. sor). A 0x121 ágban (dekompiláció 1383-1396. sor) a `FindWindowExA(..., "#32768")` után két `PostMessageA` megy: WM_KEYDOWN és WM_KEYUP, VK 0x0D-vel. A függvény hívottjai között van 0x00a516c0, 0x00a51740 és 0x00a517c0, de hogy melyik végez hit-testet: **NINCS MEG**. A kattintási cél és a dátumcsúszka leképezése is nyitott.

**Bizonyítottsági fok (38.2.19).**

| állítás | bizonyíték | fok |
|---|---|---|
| x és y képlete, a float-trükk | 0x008022db-0x008023a1, a konstansok diszasszemblálva | megerősített |
| W és H jelentése (kép vagy kártya) | dekompiláció 126-130, 162-163. sor | feltételes |
| visszatérés 4 és 0 | 0x008022b7, 0x0080260e | megerősített |
| visszatérés -1 | dekompiláció 126-130. sor | feltételes |
| előző érték írása | 0x008022c3-0x008022d5 | megerősített |
| előző érték olvasása | NINCS MEG | nyitott |
| eltelt idő, küszöb, léptetési feltétel | 0x009a51b0, 0x004019b0, 0x008020ae-0x008020dd | megerősített |
| alapérték 3 (SlideshowEffectTime) | 0x007facd3 | feltételes |
| felhasználói registry-érték | NINCS MEG | nyitott |
| léptetési periódus S másodperc | a képlet szerint; köztes frissítés és callback-ütem nélkül | feltételes |
| Space = szünet és folytatás | 0x00801130, 0x00803110, 0x008012e3-0x00801334 | megerősített |
| a 0x00801130 mellékhatásai | NINCS MEG | nyitott |
| eseménylista (0x0097d150) | dekompiláció 242-323. sor; hívó 0x007fae76 | megerősített (hozzáfűzés, keresés) |
| periodikus futtató | NINCS MEG | nyitott |
| BigSlideshow2 kapcsoló és számláló | 0x005e9409-0x005e9434 | megerősített (az ágválasztás); a nulla ág tartalma: nyitott |
| overlay-nevek | string_xrefs, 0x007fb210 | megerősített (betöltés); rajzolás: NINCS MEG |
| üzenetkezelő (0x00a52890) | dekompiláció 1401-1653. sor | megerősített (üzenetkódok); hit-test: NINCS MEG |

**Nyitott - következő Ghidra-körök.**

- ~~`Ghidra-kör kell: 0x00802180 - a 0x00802230 param_2 != 0 ágában hívódik, és a 0x0080275b, 0x00802765 ágak tartalma [blokkoló]`~~ **JAVÍTVA (38.2.20, 3. szakasz):** a `0x00802180` a `CarefulEnhance` beállítást alkalmazza, nem átmenet; a hívóhely `0x008025af` igazolt. A `0x0080275b` és `0x00802765` ágak tartalma: `Ghidra-kör kell: 0x00802630 - a 0x0080275b és 0x00802765 ágak tartalma [blokkoló]`.
- ~~`Ghidra-kör kell: 0x0097d370 és 0x007fae90 - a 0x0097d640 futtatójának és a periodikus hívónak az azonosítása [blokkoló]`~~ **JAVÍTVA (38.2.20, 1. szakasz):** a `0x0097d370` nem periodikus hívó, a tulajdonos szerinti törlő; a `0x0097d640` zárkezelő-vég; a léptetést a `0x0097fc30` üzenethurok hajtja.
- `Ghidra-kör kell: 0x007fb540 - a 0x00802230 hívóinak gyakorisága, mert ez tolja a léptetési időzítést [blokkoló]`
- ~~`Ghidra-kör kell: 0x005e95cc - a BigSlideshow2 nem nulla ága, amely az alapértelmezett 1 mellett fut [blokkoló]`~~ **JAVÍTVA (38.2.20, 4. szakasz):** a `0x005e95cc` közös pont a zéró-ág után, nem külön ág; a nem nulla ág a `uStack_d0` listát ellenőrzi, a `[this+0x3084]` objektumot építi és a `MP3SlideshowPath` értéket olvassa.
- `Ghidra-kör kell: 0x00a516c0, 0x00a51740, 0x00a517c0 - a 0x00a52890 hit-test függvényei és a kattintási cél [blokkoló]`
- ~~`Ghidra-kör kell: 0x00803110 - a [this+0x2dc] objektum felépítése, és hogy azonos-e a this-szel (a Space-visszatéréshez) [blokkoló]`~~ **JAVÍTVA (38.2.21, 4. szakasz):** `[this+0x2dc]` OneUpUI, és az `esi` azonos a `this`-szel.
- `Ghidra-kör kell: 0x00802c20, 0x00aa6f40 - a szüneteltetés mellékhatása [nem blokkoló] (a `0x0097e510` azonosítva: `ShowCursor`-váltás, 38.2.20, 7. szakasz)`
- `Ghidra-kör kell: 0x009a4890, 0x00407a20 - a registry-olvasó és az objektum-építő alapérték-kezelése (az alapértékek megerősítése) [nem blokkoló]`
- `Ghidra-kör kell: a [this+0x408] és [this+0x40c] olvasóinak pásztázása (paszta.py, teljes .text) [nem blokkoló]`

**Dekompiláló-hibák, amelyeket a diszasszemblálás felülírt.** A Ghidra-kimenet három helyen téved, és ezt a jövőbeli köröknek is tudniuk kell.

- 0x00802230, sor 102: `(float)((r + 0x3f8000) * 0x100)` bitminta-újraértelmezés (`fld dword`), nem számértékű öntés.
- 0x00802060, sor 434: `(LONGLONG)` öntés nincs a diszasszemblálásban; a bináris lebegőpontos összehasonlítást végez.
- 0x00802230, sor 135: `ROUND(_DAT_00d35808)` valójában csonkolás (RC=11), a betöltött érték 2276.

**A #5401 „Kész, ha” pontjai (2. kör).** (1) Képlánc és forráshalmaz: a kollekció számlálója és a bejárás ismert; a forrás típusa és rendezése nyitott, az alapértelmezett BigSlideshow2 mellett pedig a 0x005e95cc ág fut, nem a számláló ág. (2) Átmenet: a mozgásképlet és a léptetési feltétel bináris; a rajz-geometria megfeleltetése, a periódus pontos üteme és a felhasználói registry-érték nyitott. (3) Vezérlők: a Space-kapcsolás megerősített; a hit-test és a dátumcsúszka nyitott. (4) Diavetítés és visszatérés: a szüneteltetés és a folytatás megerősített; a teljes képernyős ablak és a visszatérési állapot nyitott.

**Fejlesztési következmény.** Ebben a körben terméki kódot nem írtunk. A mozgásképlet most bináris, de a fejlesztéshez még hiányzik a rajzoló geometriája, a periodikus hívó (0x0097d370) és a BigSlideshow2 nem nulla ága (0x005e95cc). A felhasználó registry-értékeit (SlideshowEffectTime, BigSlideshow2) nem ismerjük, és nem is becsültük.

#### 38.2.20 Az Időrend bináris feltárása, 3. kör: pumpa, lekérdező jelző, CarefulEnhance, BigSlideshow2, vezérlők, visszatérés (#5401, 2026-10-20)

**Kérdés és hatókör.** A 38.2.19 hat nyitott tétele: (1) ki hajtja a léptetést (0x0097d370, 0x007fae90); (2) a 0x007fb540 hívási gyakorisága a 0x00802230-ra; (3) a 0x00802180 param_2 != 0 ága; (4) a 0x005e95cc, vagyis a BigSlideshow2 nem nulla ág; (5) a 0x00a516c0, 0x00a51740, 0x00a517c0 találati vizsgálata és a dátumcsúszka; (6) a 0x00803110 és a diavetítésből való visszatérés pozíciója.

**Bemenet és eszközök.** A három Ghidra-kimenet (scratchpad: `idorend-1`, `idorend-2`, `idorend-3`), a helyi bináris-index olvasásban, és a `pe_dis` diszasszemblálása (capstone). Futásfelvétel és QEMU-futtatás nem volt. Terméki kódot nem írtunk.

**Módszer.** Ahol a cím után `diszasszembly` áll, a bájtokat a `pe_dis` adta. Ahol `dekompiláció` áll, csak a Ghidra-kimenetből származik. Ha a kettő eltért, a diszasszembly érvényes, és ezt kimondjuk. Az IAT-slotokat a PE import-táblából számoltuk, és ellenőriztük: Sleep = `0x00c402d0`, ShowCursor = `0x00c40700`, QueryPerformanceCounter = `0x00c40298`, PeekMessageA = `0x00c40844`; mind a négy megegyezik a kódban látott `mov reg,[slot]` hivatkozással. A vtable-ok típusát az RTTI-tábla adja: `0x00cbd66c` = `QDrawable::vftable`, `0x00cbd6c8` = `ytCallback<QDrawable>::vftable`. Független újralevezetés (#140) nem készült, ezért a bizonyítottsági fok a saját méréseinkből áll.

**Javítások a 38.2.19-ben.** Négy állítás a 38.2.19-ben tévesnek vagy elavultnak bizonyult; a 38.2.19 érintett sorai át vannak húzva és jelölve.

- `0x0097d370` **nem** periodikus hívó. A dekompiláció szerint a tulajdonos (`[elem+8]`) szerint töröl, és a törlő ág `vtable[0](1)` hívással szabadít. A 38.2.19 hipotézise (periodikus hívó) elvetve.
- `0x0097d640` **nem** futtató. Importjai (`EnterCriticalSection`, `LeaveCriticalSection`, `GetCurrentThreadId`) zárkezelő-vég. A futtató a `0x0097fc30` üzenethurok (1. szakasz).
- `0x00802180` **nem** átmenet vagy animáció. A törzsében nincs időbélyeg és nincs pozícióírás; a `CarefulEnhance` beállítást alkalmazza (3. szakasz).
- `0x005e95cc` **nem** önálló ág. A zéró-ág utáni egyesítési pont, és a nem nulla BigSlideshow2 ág ettől indul (4. szakasz).

**1. Ki hajtja a léptetést, és milyen periódussal?**

Bináris (diszasszembly), a `0x0097d370` és a `0x007fae90` **nem** hajtja a léptetést:

- `0x007fae90`: skaláris törlő dtor. Hívja a `0x007fb5a0`-t (`call 0x007fb5a0`, 0x007fae94), majd ha az argumentum bit 0 értéke 1, a `0x0097caf0`-t. Ez a `QDrawable::vftable` 0. slotja (`0x00cbd66c`).
- `0x0097d370`: a tulajdonos szerinti eltávolító (dekompiláció). Hívója a `0x007fb5a0` (`QDrawable` dtor), amelyet a `0x007fae90` hív.

A léptetés hajtója a **`0x0097fc30` üzenethurok** (diszasszembly, megerősített):

- `PeekMessageA` (IAT `0x00c40844`, betöltés `0x0097fc84`), a hurok többi ága a `DispatchMessageA`, `TranslateMessage`, `TranslateAcceleratorA`, `IsDialogMessageA` importokat is használja (index).
- `MsgWaitForMultipleObjects` (IAT `0x00c40720`), hívás `0x0098032a`: `nCount = [0xd69424] >> 1`; `pHandles = [0xd69420]`, ha `nCount != 0`; `fWaitAll = 0`; `dwMilliseconds` = a függvény első paramétere (`[ebp+8]`, `0x0098030f`); `dwWakeMask = 0x4FF` (QS_ALLINPUT).
- Csak akkor vár, ha az eltelt idő 0,005 s-nál kisebb (`0x009802f9-0x00980308`: `fcomp dword [0x00cf4b50]`, az érték f32 = 0,005; ha nem kisebb, a `jp 0x00980373` átugorja a várakozást). Az eltelt idő `((a - b) / QPF)`, ahol `a = [esp+0x38]`, `b = [esp+0x70]` (két QPC-érték). Az időbélyegek forrása **NINCS MEG**.
- Az időtúllépés a hívótól jön. Tíz hívóhely van (az utolsó `push` a `call` előtt, diszasszembly): **JAVÍTVA (38.2.21, 1. szakasz):** tizenegy van, a kimaradt `0x006fb417` 1 ms-os.
  - 1 ms: `0x0040e4b1` (`0x0040e410`), `0x005fff71` (`0x005ffc30`), `0x006fe680` (`0x006fe630`), `0x009d4dc6` (`0x009d4d10`);
  - 5 ms: `0x00405a55` (`0x004051b0`), `0x0059ec5e` (`0x0059e920`), `0x0074227c` (`0x007420f0`), `0x0074239c` (`0x007422d0`);
  - 10 ms: `0x0094ab72` (`0x0094aa00`), `0x0094ad8c` (`0x0094ace0`).
- A hurok a `0x00982270` bejárót hívja (`0x0097feac`, dekompiláció és diszasszembly), a zárolt szakaszon belül. A `0x00982270`-ben nincs közvetlen `call [reg+4]` (a callback slot+4 hívása), ezért a bejárás és a `0x00803ab0` callback közti lánc **NINCS MEG**. **JAVÍTVA (38.2.21, 1. szakasz):** a visszahívást a pumpa maga hívja, a `0x0097fff5`-nél (`call [vtable+4]`), a bejárón kívül.

**Válasz (1):** a léptetést a `0x0097fc30` üzenethurok hajtja (megerősített). Az Időrend alatt futó pumpa azonosítása (a tíz hívó közül melyik, a `0x0094aa00` vagy `0x0094ace0` a 10 ms-os jelölt) **NINCS MEG**, ezért a periódus is **NINCS MEG**. A 38.2.19 `S másodperc` értéke küszöb, nem periódus (lásd 7. szakasz).

**2. A 0x007fb540 hívási gyakorisága a 0x00802230-ra.**

Diszasszembly (`0x007fb540-0x007fb58f`, megerősített):

- Ciklus: a `vtable[1]` predikátum (`0x00408b30`: `InterlockedCompareExchange`-olvasás, a `[this+8] != 0` esetén igaz) ellenőrzése után, ha `[this+0x51a] != 0`, hívja a `0x00802230(this, 1)`-et, majd nullázza a jelzőt (`0x007fb571`). Ezután `Sleep(0x32)` (50 ms, `0x007fb57a`), és újra a predikátum.
- Egy iterációban legfeljebb egy hívás, és egy iteráció legalább 50 ms. Felső korlát: 20 hívás másodpercenként.
- A ciklus hívója a `QDrawable::vftable` 2. slotja (`0x00cbd674` = `0x007fb540`). A tényleges indirekt hívó **NINCS MEG**.
- A jelzőt a `0x00801c19` állítja (`mov byte [edi+0x51a], 1`, a `0x008018a0` függvényben). Ennek hívói: a `0x00801cb0` (ezt a `0x00802060` hívja `0x00802087`-nél, ha `[this+0x3b8] != 0`), valamint a `0x008037e0` és a `0x007fde80`. A beállítás gyakorisága **RÉSZBEN JAVÍTVA (38.2.21, 2. szakasz):** a hívók és a feltételeik megvannak.
- Sorrend-megfigyelés (diszasszembly): a jelzőt a hívás **után** törli, zár nélkül. A hívás alatti írást a törlés elveszti. Ez a bináris sorrend; a következménye csak párhuzamos íráskor számít (feltételes).

**Válasz (2):** a `0x00802230` hívása legfeljebb 20 Hz, és csak akkor, ha a `[this+0x51a]` jelző 1. A jelző beállításának gyakorisága **NINCS MEG**.

**3. A 0x00802180 param_2 != 0 ága.**

- Hívóhely: `0x008025af`. Előtte `0x008025a4`: `cmp byte [esp+0x8c], bl`, `je 0x008025b4`. A `bl` nulla, mert a `0x00802234` `xor ebx,ebx`. Tehát a hívás csak nem nulla `param_2`-nél történik (diszasszembly).
- `param_2 = 1` hívók: `0x007fb56c` (a 2. szakasz lekérdező ciklusa, diszasszembly `push 1`, `0x007fb569`) és `0x007fda4f` (`0x007fda00`, dekompiláció). `param_2 = 0` hívók: `0x00801d05` (`0x00801cf0`, diszasszembly `push 0`) és `0x00801178` (`0x00801130`, dekompiláció). A `0x008026e9` (a `0x00802630`-ból) `ebx`-et ad át; `ebx = 0` a `0x00802638`-nál, a köztes út nincs teljesen ellenőrizve.
- A törzs (dekompiláció, string-xref): a `Preferences` / `CarefulEnhance` kulcsot olvassa (`0x00802180` a sztring-hivatkozás). A getter (`0x004019b0`) alapértéke `_DAT_00cf3ed0` = `0xBF800000` (4 bájt; lebegőpontosként -1,0, a típust a `0x009db610` dönti el). Az eredményt a `this+0x46c` alobjektumra állítja (`0x009db610`), majd `0x00aa40a0`-t hív `_DAT_00c49618`-cel (`0x40400000`, lebegőpontosként 3,0), végül `0x009ab410`-et (`this+0x46c`, `this+0x648`, -1 négyszer).

**Válasz (3):** a `0x00802180` a `CarefulEnhance` beállítást alkalmazza. **Nem** átmenet vagy animáció: nincs QPC, nincs pozícióírás. Hogy a beállítás mit csinál a képpel, **NINCS MEG** (`0x009db610`, `0x009ab410`, `0x00aa40a0` nincs feltárva).

**4. A 0x005e95cc (BigSlideshow2 nem nulla ág).**

- `0x005e9409-0x005e9425` (diszasszembly): a `Preferences\BigSlideshow2` olvasása (alapérték 1), majd `test eax,eax; jne 0x005e95cc`.
- A `0x005e95cc` **közös pont**: a zéró-ág (`BigSlideshow2 == 0`, a kollekció-bejárás a `0x004a0980` darabszámmal és a `this+0x90` callbackkel) utáni `FUN_00401000(); piStack_b0 = 0; FUN_00401000();` sorok kezdete (dekompiláció, a törzs 533. sora). **JAVÍTVA (38.2.21, 5. szakasz):** a közös pont a 529-531. sor, az 533. sor az `IDS_MUST_SELECT` ágé. Nem nulla értéknél a zéró-ág kimarad.
- Utána (`0x005e95e6`): `test [esp+0x30], 0xfffffffe; je 0x005e97ce`. A `0x005e97ce` az `IDS_MUST_SELECT` ág (dekompiláció): üres kiválasztás hibát ad.
- Képforrás: a `uStack_d0` lista (dekompiláció, 212-285. sor). A Shift-ágban (`GetAsyncKeyState(0x10)`, dekompiláció 245. sor) a `[this+0xaf]+0x4ec` provider-listát járja be, és 13 típuskódra szűr: 2, 3, 6, 7, 13, 31, 14, 18, 24, 22, 27, 28, 26. A Ctrl (0x11) állapotát a `cStack_d9` jelző adja. A Ctrl és Shift nélküli alapút feltöltése (dekompiláció 350-447. sor) **NINCS MEG**.
- Rendezés: **NINCS MEG** (a rendezési mező és sorrend nincs feltárva).
- Utána (`0x005e95f4-0x005e961d`, diszasszembly): ha `[this+0x3084] == 0`, 8 bájtos objektum (`push 8`, `0x0097c5d0` foglalás), építés `0x0052e3c0`-lal, tárolás `[this+0x3084]`-be.
- Utána (`0x005e9628-0x005e964d`, diszasszembly): a `Preferences` / `MP3SlideshowPath` (sztring `0x00c97920`) kulcs olvasása (`0x00407630`, `0x004078e0`). A kulcs neve alapján a diavetítés zenéjének útvonala; a felhasználói érték **NINCS MEG**.

**Válasz (4):** a nem nulla ág a `uStack_d0` kiválasztott listát használja képforrásként (nem a kollekció teljes bejárását), üres listánál hibát ad. A Ctrl nélküli alapút feltöltése és a rendezés **NINCS MEG**. Az ág a `[this+0x3084]` objektumot hozza létre, és a `Preferences\MP3SlideshowPath` értéket olvassa.

**5. A három függvény és a vezérlők.**

- `0x00a516c0`, `0x00a51740` és `0x00a517c0` **nem** találati vizsgálat. Mindhárom az `ytUIEvent::vftable`-t írja a `[this]`-be, és az argumentumokból tölti a mezőket (dekompiláció). Eseménykonstruktorok:
  - `0x00a516c0` (float, pozíció, float, jelző): típus `0x0E + (jelző != 0)`, vagyis 14 vagy 15; pozíció a `+0x5C` / `+0x60` mezőkben. Hívó: `0x00a53707` (az üzenetkezelő `0x20a` / `0x5850534d` ága).
  - `0x00a51740` (pozíció): típus `0x10`. Hívó: `0x00a535f0` (a `0x8000009` ág).
  - `0x00a517c0` (téglalap, típus): típus az átadott érték (`0x11` vagy `0x12`). Hívók: `0x00a534e7` (`0x8000008`) és `0x00a53754` (`0x800000a`).
- A találatot az elosztás adja: `FUN_009e4630(esemény, &kimenet)`. Az üzenetkezelő az `1000000` (0xF4240) visszatérési értéket vizsgálja; ezt a konstanst a Space-ág is visszaadja. A `0x009e4630` belseje **NINCS MEG**.
- Vezérlők (`sliderthumb`, `timelinedot`, `startbutton`, `exit`, listaikon) kattintási célja és a dátumcsúszka leképezése **NINCS MEG**. A `0x007fb210` csak betölti az overlay-neveket (38.2.18), a rajz- és találati téglalapok nincsenek feltárva.

**Válasz (5):** a három függvény eseménykonstruktor, nem találati vizsgálat. Melyik vezérlő mire reagál, és a dátumcsúszka leképezése **NINCS MEG**.

**6. A 0x00803110 és a diavetítésből való visszatérés pozíciója.**

- Hívóhely (diszasszembly, `0x00801319-0x0080131f`): a `0x00801270` (a `QDrawable` Space-kezelője, a `QDrawable::vftable` tagja) `mov eax,[ebx+0x2dc]` után hívja a `0x00803110`-et. További hívók: `0x008032e0` (`OneUpUI`) a `0x00803486` és `0x008034c5` címen (dekompiláció, a 38.2.18 szerint).
- Törzs (a teljes `0x00803110-0x00803161`, diszasszembly): `X = eax` (`[this+0x2dc]`); `esi = [X+0x25c]`; ha `[esi+0x3be] != 0`, hívja a `0x00801cf0`-t; `[esi+0x518] = 1` (a következő léptetés azonnal fut); QPC a `[esi+0x520]`-ba; `[esi+0x3b8] = 0`; `[esi+0x428] = 0`; majd `0x00801130(esi)`, ami a `[esi+0x3bb]` jelzőt 1-ről 0-ra állítja (folytatás); végül `[X+0x50] != 0` esetén a `0x00802be0`.
- Pozíció: a `0x00803110` nem írja a `[esi+0x3f4]` indexet (a teljes törzs diszasszemblálva). A folytatásnál a `0x00802230(esi, 0)` a `[esi+0x3f8]`-ba írja az utolsó megjelenített indexet (dekompiláció). Tehát a visszatérés pozíciója a szüneteltetéskori index.
- `X` típusa és az `esi == this` azonosság **NINCS MEG**. `X`-et a `0x007fa7f0` építő írja (`0x007fae55`, `mov [ecx+0x2dc], eax`, bájt-keresés). Ha `esi != this`, a Space-ág a `this+0x3bb` jelzőt nem tudja visszaállítani, mert a folytatás az `esi` jelzőjét írja. Ez logikai következtetés, nem mért állítás.

**Válasz (6):** a visszatérés pozíciója a szüneteltetéskor érvényes `[esi+0x3f4]` index (a `0x00803110` nem írja). `X` típusa és az `esi == this` azonosság **NINCS MEG**.

**7. Új megfigyelések (38.2.20).**

- `0x0097e510` (diszasszembly, a `ShowCursor` IAT-ja `0x00c40700`): a paraméter 1 (szünet) esetén `ShowCursor(TRUE)` hívások a számláló 0-ig; 0 (folytatás) esetén `ShowCursor(FALSE)` a -1-ig. Szünetben a kurzor látszik, folytatáskor rejtett. A `0x007fda00` a diavetítés indításakor `0`-val hívja.
- A `QDrawable::vftable` (`0x00cbd66c`) 0. slotja a `0x007fae90`, 1. slotja a `0x00408b30`, 2. slotja a `0x007fb540`. A `ytCallback<QDrawable>::vftable` (`0x00cbd6c8`) 1. slotja a `0x00803ab0`.
- `0x00803ab0` (diszasszembly): a `[cb+0x18]`-ba írja a QPC-t (`fild qword`, `fstp qword`); ha `[QDrawable+0x3bf] == 0`, hívja a `0x00802060`-at a `[cb+8]` QDrawable-ra.
- `0x00802060` küszöb-összehasonlítása lebegőpontos (diszasszembly, `0x008020aa-0x008020d4`): az eltelt idő `fstp qword [esp+8]`-ba kerül (`0x009a51b0`), a küszöb `fild dword` (`0x004019b0`). A léptetés akkor fut, ha az eltelt idő nagyobb a küszöbnél. A Ghidra `LONGLONG` öntése a kimenet hibája, a bináris nem egész másodpercre vág.
- Léptetési lánc: `0x00802060` → `0x00801cb0` (ha `[this+0x3b8] != 0`) → `0x008018a0` (a jelző beállítása, 2. szakasz).

**8. Konstansok** (`pe_dis`, `f32` / `f64` / `int32`):

| bináris cím | típus | érték | szerep |
|---|---|---|---|
| `0x00cf4b50` | f32 | 0,005 | a pumpa 5 ms-os küszöbe (1. szakasz) |
| `0x00cf3ed0` | int32 | `0xBF800000` (-1082130432) | a `CarefulEnhance` getter alapértéke (3. szakasz) |
| `0x00c49618` | f32 bitminta | `0x40400000` = 3,0 | a `0x00aa40a0` argumentuma (3. szakasz) |
| `0x00cf4320` | f64 | 0,1499999761581421 | a `c` szorzó (38.2.19) |
| `0x00c72150` | f64 | 0,5 | a y-ág fele (38.2.19) |
| `0x00cf39e4` | f32 | 4294967296 (2^32) | negatív W előjel-korrekciója (38.2.19) |
| `0x00cf3ac0` | f64 | 4294967296 (2^32) | negatív H előjel-korrekciója; a `0x00802060` küszöbén is (38.2.19) |
| `0x00d35808` | f32 | 2276,5556640625 | a `p[0xb9]` ágban (38.2.19) |

**9. KIZÁRTAM (ne járják újra).**

- `0x0097d370` mint periodikus hajtó: a törlő ág nem léptet (1. szakasz).
- `0x0097d640` mint futtató: zárkezelő-vég (1. szakasz).
- `0x00802180` mint átmenet vagy animáció: a törzsében nincs időbélyeg, nincs pozícióírás (3. szakasz).
- `0x00a516c0`, `0x00a51740`, `0x00a517c0` mint találati vizsgálat: eseménykonstruktorok (5. szakasz).
- A `LONGLONG`-küszöbös léptetés (Ghidra): a diszasszembly lebegőpontos (2. és 7. szakasz).
- A `0x005e95cc` mint önálló nem nulla BigSlideshow2 ág: közös pont (4. szakasz).

**Bizonyítottsági fok (38.2.20).**

| állítás | bizonyíték | fok |
|---|---|---|
| `0x0097d370` nem periodikus, a tulajdonos szerinti törlő | dekompiláció `0x0097d370`; `0x007fae90` diszasszembly; RTTI | megerősített (szerep); a belső ciklus dekompiláció |
| `0x007fae90` skaláris törlő dtor, `QDrawable::vftable` 0. slot | diszasszembly `0x007fae90`, RTTI `0x00cbd66c` | megerősített |
| pumpa `0x0097fc30`: PeekMessageA, MsgWait, időtúllépés = paraméter | diszasszembly `0x0098030f-0x0098032a`; IAT-leképezés (4 slot ellenőrizve) | megerősített |
| 5 ms-os ág (`0x00cf4b50`) | diszasszembly `0x009802f9-0x00980308`, konstans | megerősített (feltétel); az időbélyegek forrása NINCS MEG |
| tíz hívóhely 1, 5 vagy 10 ms | diszasszembly (utolsó `push` a `call` előtt) | megerősített |
| pumpa hívja a bejárót (`0x00982270`) | diszasszembly `0x0097feac` | megerősített |
| bejáró hívja a 0x00803ab0 callbacket | nincs `call [reg+4]` a bejáróban | NINCS MEG |
| `0x007fb540`: 50 ms-os ciklus, `0x00802230(this,1)` a jelzőre | diszasszembly `0x007fb540-0x007fb58f` | megerősített |
| jelző-író `0x00801c19` (`0x008018a0`) | bájt-keresés, diszasszembly | megerősített (író); hívási gyakoriság NINCS MEG |
| `QDrawable` slot+8 hívója | indirekt hívás | NINCS MEG |
| `0x00802180`: CarefulEnhance, nem átmenet | `cmp bl` diszasszembly `0x008025a4`; string-xref; dekompiláció törzs | megerősített (hol és mit); vizuális hatás NINCS MEG |
| `0x005e95cc` közös pont, `uStack_d0` ellenőrzés | diszasszembly `0x005e9425`, `0x005e95e6`; dekompiláció 533. sor | megerősített |
| `MP3SlideshowPath` olvasása a nem nulla ágban | diszasszembly `0x005e9628-0x005e964d`; sztring `0x00c97920` | megerősített (a kulcs); felhasználói érték NINCS MEG |
| 13 típuskódos szűrő a Shift-ágban | dekompiláció 245-256. sor | feltételes (dekompiláció) |
| Ctrl nélküli képforrás, rendezés | **RÉSZBEN (38.2.21, 5. szakasz):** rendezés nincs, körforgatás van; a forrás NINCS MEG | nyitott |
| `0x0097e510` = ShowCursor-váltás | diszasszembly, IAT `0x00c40700` | megerősített |
| `0x00803110`: esi = `[X+0x25c]`, nincs írás `[+0x3f4]` | diszasszembly, teljes törzs | megerősített |
| `X` típusa, `esi == this` | **JAVÍTVA (38.2.21, 4. szakasz):** OneUpUI, és `[X+0x25c]` = this | megerősített |
| `0x00a516c0/0x00a51740/0x00a517c0` = eseménykonstruktor | dekompiláció (vftable-írás, mezők), hívóhelyek | feltételes (dekompiláció, nincs diszasszembly) |
| találati vizsgálat és vezérlő-leképezés, dátumcsúszka | NINCS MEG (`0x009e4630` belseje) | nyitott |

**Nyitott - következő Ghidra-körök.**

- `Ghidra-kör kell: 0x0097fc30 - a [esp+0x38] és [esp+0x70] időbélyegek forrása, a 0x00980373 utáni feldolgozó ág, és a 0x00982270 callback-hívása [blokkoló]` **RÉSZBEN JAVÍTVA (38.2.21, 1. szakasz):** a visszahívás nem a 0x00982270-ből hívódik, hanem a pumpából (`0x0097fff5`).
- ~~`Ghidra-kör kell: 0x0094aa00 és 0x0094ace0 - melyik a 10 ms-os pumpa, és fut-e az Időrend alatt [blokkoló]`~~ **SZŰKÍTVE (38.2.21, 1. szakasz):** mindkettő webböngésző-pumpa. Az Időrend-pumpa a `0x0097fc30` hívói közül **NINCS MEG** (`Ghidra-kör kell: 0x00983430, 0x00983fc0, 0x00982bf0 [blokkoló]`).
- `Ghidra-kör kell: 0x007fb540 slot+8 hívója (CreateThread / _beginthreadex hívóhelyek vagy QDrawable-futtató), és a 0x008018a0 hívóinak gyakorisága (0x007fde80) [blokkoló]` **RÉSZBEN JAVÍTVA (38.2.21, 2. szakasz):** a 0x008018a0 hívói: 0x007fde80 (0x007fe33e), 0x00801cb0 (0x00801ce5), 0x008037e0 (0x00803953). A 0x007fb540 közvetett hívója még NINCS MEG.
- `Ghidra-kör kell: 0x005e8a70 - a uStack_d0 lista feltöltése a Ctrl és Shift nélküli ágban (dekompiláció 350-447. sor), a rendezési mező [blokkoló]` **RÉSZBEN JAVÍTVA (38.2.21, 5. szakasz):** a 350-453. sor körforgatás, rendezés nincs; az Időrend-ág forrása NINCS MEG.
- `Ghidra-kör kell: 0x009e4630, 0x0052d3c0, 0x0052d430 - az ytUIEvent találati és elosztási útja, a csúszka és a gombok leképezése [blokkoló]` **RÉSZBEN JAVÍTVA (38.2.21, 3. szakasz):** az elosztó és a típusok megvannak; a csúszka és a gombok leképezése NINCS MEG.
- `Ghidra-kör kell: 0x007fa7f0 a 0x007fae55 körül - az [this+0x2dc] objektum típusa, és hogy [X+0x25c] == this [blokkoló]` **JAVÍTVA (38.2.21, 4. szakasz):** OneUpUI, és `[X+0x25c]` = this.
- `Ghidra-kör kell: 0x009db610, 0x009ab410, 0x00aa40a0 - a CarefulEnhance beállítás vizuális hatása [nem blokkoló]`
- `Ghidra-kör kell: 0x0097da20 - a 0xd69420 / 0xd69424 várakozási tömb tartalma; ha nCount = 0, a MsgWait csak időtúllépés és bemenet [nem blokkoló]`

**Fejlesztési következmény.** Terméki kódot nem írtunk. A léptetés periódusa (melyik pumpa, milyen időtúllépéssel) még nincs megállapítva, ezért nem implementálható. A CarefulEnhance vizuális hatása, a képforrás Ctrl nélküli ága és a dátumcsúszka leképezése is nyitott. Az 1, 5 és 10 ms pumpaidők nem tekinthetők az Időrend periódusának.

#### 38.2.21 Az Időrend bináris feltárása, 4. kör: üzenethurok és léptetési ütem, a jelző írói, találat és elosztás, OneUpUI, alapút (#5401, 2026-10-20)

**Kérdés és hatókör.** A 38.2.20 nyitott tételei öt kérdésben: (1) melyik üzenethurok fut az Időrend alatt, és mi a léptetési ütem; (2) ki és milyen gyakran állítja a `[this+0x51a]` jelzőt; (3) a `0x009e4630`, `0x0052d3c0` és `0x0052d430` találati és elosztási útja, a vezérlők és a dátumcsúszka; (4) a `0x007fa7f0` `[this+0x2dc]` objektuma, és teljesül-e `[X+0x25c] == this`; (5) a `0x005e8a70` alapútjának feltöltése és rendezése.

**Bemenet és eszközök.** A `2026-10-20-idorend-4.txt` kilenc függvénye, az `idorend-1` `0x005e8a70` és `0x008037e0` dekompilációja, a `pe_dis` diszasszemblálása (capstone), és a helyi index (`functions`, `rtti`). Futásfelvétel és QEMU-futtatás nem volt.

**Módszer.** Ahol egy állítás után `diszasszembly` áll, a bájtokat a `pe_dis` adta. Ahol `dekompiláció` áll, csak a Ghidra-kimenetből származik. A sorszámok a kimenetek fájlsorai (a dekompiláció törzse a fájl 69. sorától indul, így a 350-453. sor a `0x005e8a70` fájl 350-453. sora). A konstansok típusát a betöltő utasítás dönti el (`fcomp qword`, `fcomp dword`).

**Javítások a korábbi szakaszokban.** Az érintett sorok át vannak húzva és jelölve.
- 38.2.20 §1: a pumpának **tizenegy** közvetlen hívója van, nem tíz. A kimaradt `0x006fb417` `push 1`-gyel 1 ms-os.
- 38.2.20 §1: a visszahívást **nem** a `0x00982270` bejáró hívja. A pumpa hívja közvetlenül, a `0x0097fff5`-nél.
- 38.2.20 §1: a `0x0094aa00` és a `0x0094ace0` webböngésző-pumpa (`about:blank`, `ytCallback<WebBrowser>`), a tartalmuk szerint nem Időrend-specifikus.
- 38.2.20 §4: a közös pont a fájl 529-531. sora. Az 533. sor az `IDS_MUST_SELECT` ágé.
- 38.2.20 §6 és 38.2.19 §3: `X` **OneUpUI**, és `esi` azonos a `this`-szel (4. szakasz).
- Dekompiláció-hiba: a `0x007fe33e` hívása a dekompilációban argumentum nélkülinek látszik. A diszasszembly szerint EAX a `0x007fd800` kimeneti mezőjéből jön (2. szakasz).

**1. Üzenethurok és léptetési ütem.**

- **Hurok:** a `0x0097fc30` (megerősített: `PeekMessageA`, `MsgWaitForMultipleObjects`). Az Időrend alatti közvetlen hívója **NINCS MEG**. A tizenegy közvetlen hívó időtúllépése (diszasszembly, az utolsó `push` a `call` előtt):
  - 1 ms: `0x0040e4b1`, `0x005fff71`, `0x006fb417`, `0x006fe680`, `0x009d4dc6`;
  - 5 ms: `0x00405a55`, `0x0059ec5e`, `0x0074227c`, `0x0074239c`;
  - 10 ms: `0x0094ab72`, `0x0094ad8c`.
- **A 10 ms-os jelöltek:** a `0x0094aa00` `about:blank` lapot nyit (kimenet 404. sor), a `0x0094ace0` `ytCallback<WebBrowser>` objektumot hoz létre (501. sor). Az Időrend alatti futásukat nem zártuk ki, a tartalmuk alapján viszont nem Időrend-specifikusak. A hívóik: a `0x0094aa00`-nak három (`0x00593450`, `0x006fc7d0`, `0x006fcb60`), a `0x0094ace0`-nak tíz (441-451. sor). **NINCS MEG**, melyik fut az Időrend alatt.
- **Egy pumpa-kör (megerősített, kimenet és diszasszembly):**
  1. Üzenetkeret: legfeljebb 10 ms üzenetfeldolgozás. A `0x0097fe11` `fcomp qword` ellenőrzi a `0x00cf40b8` = 0,01 s értéket (kimenet 137-138. sor).
  2. A `0x00982270` összeállítja a bejegyzések listáját (`0x0097feac`, kimenet 168. sor).
  3. Minden bejegyzésre lejárat-ellenőrzés: `(most - [+0x18]) × (1/QPF) × 1000 >= [+0x20]` (kimenet 195-197. sor; `0x0097ff79` `fmul qword` a `0x00cf3e10` = 1000,0).
  4. Hívás: `mov edx,[esi]`, `mov eax,[edx+4]`, `call eax` (`0x0097ffe3-0x0097fff5`, diszasszembly). Ez a bejegyzés vtable-jének 1. slotja, `ecx = esi`, és argumentum a `(most - [+0x10]) / QPF` dupla szám. A `ytCallback<QDrawable>` vtable (`0x00cbd6c8`) 1. slotja a `0x00803ab0` (index-RTTI és a slot-érték egyezik).
  5. `0x00803ab0` (diszasszembly `0x00803ab0-0x00803aec`): ha `[+8]` (a QDrawable) nulla, `-1`. Egyébként `[+0x18] = QPC` (`0x00803ad4`), és ha `[QDrawable+0x3bf] == 0`, `0x00802060`. Egyébként `-1`.
  6. A visszatérés kezelése (kimenet 207-210. sor): `>= 0` → `[+0x20]` lesz az érték; `-2` → a kör többi lejárt bejegyzése kimarad; `-1` → a bejegyzés eltávolítása (kimenet 211-317. sor). A `0x00802060` soha nem ad `0`-t.
- **A léptetés döntése (`0x00802060`, diszasszembly `0x00802060-0x00802125`):**
  1. `[this+0x3bb] != 0` (szünet): visszatérés `1`.
  2. `[this+0x3b8] != 0`: `0x00801cb0` (`0x00802087`). Ha a jelző még nem nulla, az 5. pont.
  3. `[this+0x518] != 0`: léptetés.
  4. Egyébként léptetés, ha `S < (most - [this+0x520]) / QPF` másodpercben. Az `S` a `Preferences\SlideshowEffectTime` egész értéke (`0x004019b0`, `0x008020ae-0x008020b4`), negatív értéknél `+2^32` (`0x008020c5`). Az összehasonlítás `fcomp qword` (`0x008020cb`).
  5. Egyébként, ha `[this+0x3c1] != 0`: léptetés (`0x008020d6-0x008020dd`).
  6. Léptetés: `0x00802630` (`0x008020e1`). Nulla visszatérésnél `[this+0x518] = 0` és `[this+0x520] = most` (`0x00802101-0x00802108`). Nem nulla visszatérésnél `-1`.
  7. Nincs léptetés, vagy sikeres léptetés után: `0x00801f50` hívása, `[this+0x3fc] = 0`, és `-2` (`0x0080210e-0x0080211c`).
- **Ütem (következtetés):**
  - A léptetés legkorábbi időpontja `S` másodperc a `[this+0x520]` óta. Ez küszöb, nem periódus (a 38.2.20 7. szakasza megerősítve).
  - A tényleges időpont a pumpa-kör ritmusától függ. Üzenetmentes körben a pumpa az `MsgWaitForMultipleObjects`-nél vár `param_1` ezredmásodpercig, ha a kör 5 ezredmásodpercnél rövidebb volt (`0x009802fd`, `fcomp dword` a `0x00cf4b50` = 0,005). Üzenet azonnal felébreszti. A `param_1` a hívó időtúllépése (1, 5 vagy 10 ms). Hogy melyik hívó, **NINCS MEG**, ezért a pontos ütem sincs meg.
  - Szünet után a bejegyzés `[+0x20]` értéke 1 ms: a `0x00802060` `1`-et ad, a pumpa tárolja. Más írót a feltárt kódban nem találtunk. A teljes `.text` pásztázása nem futott.

**2. A `[this+0x51a]` jelző.**

- **Író: `0x008018a0` (diszasszembly).** A jelzőt csak akkor írja (`0x00801c19`, `mov byte [edi+0x51a], 1`), ha a bemeneti érték (EAX) eltér a `[this+0x50c]` mezőtől: `0x008018ac` `cmp [edi+0x50c], eax`, `0x008018b2` `je 0x801ca3`, ami átugorja a törzset. Az új értéket a `0x008018b8` tárolja.
- **Hívók, három (diszasszembly):**
  - a) `0x007fe33e`, a `0x007fde80` egéreseményében, a `0x201` (bal gomb) ágban, ha `[this+0x3b8] != 0` és a `0x007fd800` nullát ad (`0x007fe336`). EAX a `0x007fd800` kimeneti mezője (`mov eax,[esp+0x18]`, `0x007fe338`).
  - b) `0x00801ce5`, a `0x00801cb0`-ban. EAX = `[this+0x510]` (`0x00801ce1`), amelyet a `0x007fd8c0` írt (az `[this+0x510]` címét `0x00801cd5`-nél adja át). A `0x00801cb0` csak akkor fut, ha `[this+0x429] == 0` és a `0x007fd8c0` nem nullát ad (`0x00801cc6-0x00801cdf`). A `0x00801cb0`-t a `0x00802060` hívja, ha `[this+0x3b8] != 0` és nincs szünet (`0x00802087`).
  - c) `0x00803953`, a `0x008037e0` (`qshow`-építő) törzsében. EAX = `0` (`0x0080394f`), és a hívás csak akkor történik, ha `[ecx+4] & 0xfffffffe` nulla (`0x00803946-0x0080394d`).
- **Gyakoriság.** A jelző akkor lesz `1`, ha a bemeneti érték változik. Az a) eset egéresemény-szinten fut, az Időrend módban. A b) eset minden pumpa-körben fut, az Időrend módban és szünet nélkül, ha a találat változik. A c) eset egyszer, az építésnél, feltétellel. A `0x007fd800` és a `0x007fd8c0` kimenete a kurzor alatti elem indexe: **feltételes**, a jelentését Ghidra-kör igazolja.
- **Olvasó: `0x007fb540` (diszasszembly `0x007fb540-0x007fb58f`).** Ciklus: ha `[this+0x51a] != 0`, meghívja a `0x00802230(this, 1)`-et, majd törli a jelzőt (`0x007fb571`). Utána `Sleep(0x32)` (50 ms, `0x007fb57a`). Legfeljebb 20 újrarajzolás másodpercenként. A ciklust a `QDrawable::vftable` 2. slotja hívja (`0x00cbd674`); az indirekt hívó **NINCS MEG**.
- A `0x00802230` többi hívója a 38.2.19 szerint: `0x007fda00` (`1` jelzővel) és `0x00801130` (`0`-val, folytatáskor).

**Válasz (2):** a jelzőt a `0x008018a0` írja, és csak változáskor. Három hívója van. A `0x007fb540` 50 ezredmásodpercenként olvassa, ezért az újrarajzolás legfeljebb 20 Hz.

**3. Találat, elosztás, vezérlők.**

- **Win32 üzenet → típus.** A `0x00a52890` üzenetkezelő (dekompiláció). `0x200` → `2` és `3` (kimenet 1430, 1460. sor). `0x201` → `1` (1491. sor). `0x203` → `0xd` (1543. sor). `0x207` → `7` és `4` (1584, 1599. sor). `0x208` → `8` (1633. sor). A `0x202` és a `0x204` a `0x1c` ágba ugrik, ahol a `4` és az `5` van (1786, 1812. sor). `0x20a` → `0x00a516c0` (1686. sor). Az egyedi `0x8000008`, `0x8000009` és `0x800000a` üzenetek a 38.2.20 szerint a `0x00a517c0` (`0x11`, `0x12`) és a `0x00a51740` (`0x10`) függvényekhez tartoznak.
- **Konstruktor `0x0052d3c0` (dekompiláció, kimenet 1497-1523. sor):** a vtable `ytUIEvent::vftable`, a típus a `+8`-ban, a pozíciópár a `+0x5c` és `+0x60` mezőben, a negyedik paraméter a `+0x24`-ben. **Destruktor `0x0052d430` (1552-1554. sor):** a vtable visszaállítása, a `0x00401000` hívása (szerepe **NINCS MEG**), és `+0x68 = 0`.
- **Elosztó `0x009e4630` (dekompiláció, kimenet 1037-1467. sor):**
  - Típusvizsgálat (1376-1424. sor): `1` és `0xd` → a `0x4c` slot. Ha az elem `[+0x205]` nem nulla, és a hívás `1000000`-t ad, az elem a `*param_3` kimeneti mezőbe kerül. `2` és `3` → a `0x54` slot (kapu: `[+0x206]`). `4` → a `0x50` slot (`[+0x205]`). `0x13` → a `0x58` slot (`[+0x82]`).
  - Találat: a gyermekeken megy végig (1094-1095. sor, a `[+0x91]` láncon). A határoló téglalapot a `0x20` slot adja (1269. sor), és az esemény pozíciójával hasonlítja össze (1270. sor, `(iStack_c0 < iStack_b8) && (iStack_bc < iStack_b4)`).
  - Visszatérési kódok: `1000000` (kezelve), `0xf4242`, `0xf4243`. A rekurzió az 1295. és 1438. sorban van.
- **Slot-térkép** (index-RTTI, `OneUpUI::vftable`): `0x20` → `0x00a6cd10`; `0x4c` → `0x00a52820` (ez hívja a `0x009e4630`-t, kimenet 998. sor); `0x50` → `0x00401570`; `0x54` → `0x00803180`; `0x58` → `0x008032e0`; `0x74` → `0x00a54050`. A `QDrawable::vftable` 11. slotja (`0x00cbd698` = `0x00cbd66c + 0x2c`) a `0x007fde80` (diszasszembly).
- **A QDrawable egérkezelője (`0x007fde80`, 11. slot):**
  - `0x201` (bal gomb): ha `[this+0x3b8] == 0`, a `0x00801130` (szünet-váltás; diszasszembly `0x007fe1e6-0x007fe1f6`). Ha `[this+0x3b8] != 0`: a `0x007fda80` hívása, és ha az `1000000`, kilépés (`0x007fe202-0x007fe207`). Majd a `[+0x6c8]`-`[+0x72c]` mezőkből számolt tartománnyal való összevetés (kimenet 892-930. sor). Ha a pont a tartományban van, húzás indul (`[+0x429] = 1`, `0x007fdd00`), egyébként `[+0x428] = 1` (`0x007fe2b9-0x007fe31b`). Végül a `0x007fd800` és a `0x008018a0` (2. szakasz).
  - `0x202` (felengedés, kimenet 876-882. sor): ha `[+0x429]`, a `0x007fd770(this+0x514)`; majd `[+0x428] = [+0x429] = 0`.
  - `0x203` és `0x204` (dupla és jobb gomb, dekompiláció 855-875. sor): ha `[+0x3b8] == 0`, a `0x007fda00` (Időrend-váltás). Egyébként a `0x007fda80`, majd a `[+0x2e8]` objektum `vtable+0x18` hívása a `[+0x3ec][+0x3f8]` elemmel. Ezt az ágat a diszasszembly nem ellenőrizte.
  - A `0x201` blokkban van egy `0x203`-as ellenőrzés (`0x007fe346`, `cmp [edx+4], 0x203`, utána `[+0x3b8] = 0` és `[+0x428] = 0`). A blokkba csak `0x201` esemény léphet be (`0x007fe1d9-0x007fe1e0`), ezért ez az ág **nem fut** (kizárva).
  - Görgő (`0x20a`, kimenet 939-971. sor, dekompiláció): ha a `GetAsyncKeyState` szerint a `DAT_00d4a490` gomb lenyomva van, nem fut. Egyébként lépésenként a `0x008011b0` (pozitív) vagy a `0x00801210` (negatív) hívás.
- **Vezérlők.** A `sliderthumb`, `timelinedot`, `startbutton`, `exit` és a listaikon kattintása: **NINCS MEG**. A `0x007fb210` csak betölti az overlay-neveket (38.2.18), az elemekhez tartozó osztály és kattintás-kezelő nincs összekötve.
- **Dátumcsúszka: NINCS MEG.** A kódban csak egy lineáris skálázás van: az egérmozgás koordinátája (`0x007fde80`, kimenet 802-808. sor, dekompiláció): `x_logikai = x_kliens × ([+0x2d0] - [+0x2c8]) / kliens-szélesség`, az `y` hasonlóan `[+0x2d4] - [+0x2cc]` és a magasság szerint. Eltolás nincs. Ez a kurzor-koordináták skálája, nem a dátumcsúszka leképezése. A `[+0x2c8]`-`[+0x2d4]` mezőket a konstruktor (`0x007fa7f0`, kimenet 1582-1917. sor) nem írja.

**Válasz (3):** az elosztás megvan (`0x00a52890` → `0x0052d3c0` → `0x009e4630` → típus szerinti slot). A konstruktor és a destruktor megvan. A vezérlők kattintási célja és a dátumcsúszka leképezése **NINCS MEG**.

**4. A `[this+0x2dc]` objektum és `[X+0x25c] == this`.**

- `0x007fa7f0` (QDrawable konstruktor, kimenet 1899-1907. sor): a `0x0097c5d0(0x268)` foglalás és `memset` (diszasszembly `0x007fae32-0x007fae39`), majd `0x00802c60(X, this, [this+0x2e8])` (`0x007fae4a`: `push ecx`, `push ebp`, `push esi`). A visszatérés a `[this+0x2dc]`-be kerül (1907. sor).
- `0x00802c60` (diszasszembly `0x00802c60-0x00802d86`): az első argumentum `X` (az `ebx`-be kerül). `[ebx+0x25c] = eax` (`0x00802c79`), ahol az `eax` a második argumentum, vagyis `this`: a `0x00a518b0` hívás `ret 4`-gyel (`0x00a51bb2`) takarítja a saját argumentumát, így a `[esp+0x18]` a második argumentumra mutat. `[ebx+0x260] = ecx` (`0x00802c9d`) a harmadik argumentum, a `[this+0x2e8]`. Visszatérés: `X` (`0x00802d82`, `mov eax, ebx`, `ret 0xc`).
- Vtable: `[X] = 0xcbd5c4` (`0x00802c7f`), `[X+0x48] = 0xcbd650` (`0x00802c85`), `[X+0x58] = 0xcbd660` (`0x00802c8c`). Az index RTTI-ja mindhárom címre `OneUpUI::vftable`.
- **Válasz (4):** `[this+0x2dc]` egy **`OneUpUI`** objektum, mérete `0x268` bájt (megerősített: RTTI és foglalási méret). **`[X+0x25c] == this`: igen** (megerősített). `X` és `this` különböző objektum. Ezért a `0x00803110` `esi = [X+0x25c]` sora a QDrawable-re mutat, és a szünetből való visszatérés a `this` jelzőit állítja (38.2.19 §3).

**5. A `0x005e8a70` alapútja (kimenet 350-453. sor).**

- **A forrás.** A `local_c0` (forráslista) és a `local_bc` (darabszám) az Időrend-ágban (`param_2 = 1`) nullázódik (kimenet 209-210. sor). A `local_c0 = param_1` (127. sor) csak a `param_2 == 0` ágban van, és az a 192. vagy 195. sorban visszatér. A dekompiláció szerint tehát az Időrend-ágban a forrás üres. Ez ellentmond a 38.2.17 futásfelvételének (kártyák), ezért a dekompiláció vagy a változó-azonosítás hibás lehet. A forrás eredete **NINCS MEG**.
- **A feltöltés (ha a forrás nem üres).** Körforgatás: a `param_1[0x399]` (bájt-eltolás `0xe64`) értékével egyező első elemtől a forrás végéig (350-385. sor), majd a 0. elemtől a találatig (410-453. sor). Ha nincs találat, az eredeti sorrend. Ha `param_1[0x399] == -1`, a `0x00891110` hívás és üres lista (341. sor).
- **Rendezés: nincs.** A 350-453. sorban nincs rendező hívás. A hívások: `0x0097c810` (növelés) és `0x0097caf0` (felszabadítás).
- **Üres lista:** a 532. sor (`(uStack_d0 & 0xfffffffe) == 0`) az `IDS_MUST_SELECT` ágra visz.
- **A Ctrl- és Shift-ágak** (kimenet 231-330. sor) más úton töltik a listát (`0x0049e1e0`, a `piStack_b0` mutatóval, 313. sor); ez nem az alapút.
- **Válasz (5):** a rendezés nincs. A kiválasztott elem köré forgatás van. Az Időrend-ág forrása **NINCS MEG**, és a dekompiláció szerint üres.

**Nyitott kérdések mérlege.** A nyitva maradt tételek mind a 38.2.20-ból örököltek, ezért a munkasorba (`picasapy-agent`, `memory/nyitott-kerdesek-sor.md`) kerülnek; ezt a hívónak kell frissítenie. Saját, ebben a körben feltett kérdés nincs nyitva.

- Lezárva ebben a körben (7): (a) a visszahívás útja a pumpából (`0x0097fff5`); (b) a léptetési döntés (`0x00802060`); (c) a `[this+0x51a]` írói és hívói; (d) `X` típusa és `[X+0x25c] == this`; (e) a `0x203`-ág kizárása a `0x201` blokkban; (f) a `0x007fb540` ciklus és a 20 Hz felső korlát; (g) a MsgWait küszöb (5 ms) és az üzenetkeret (10 ms).
- Örökölt, nyitva (9): (1) az Időrend-pumpa azonosítása és a hívó időtúllépése; (2) a `0x00802630` léptetés-törzse és a nem nulla visszatérés; (3) a `0x007fd800` és a `0x007fd8c0` kimenetének jelentése; (4) a vezérlők kattintás-leképezése; (5) a dátumcsúszka leképezése; (6) az Időrend-ág alapút-forrása; (7) a `Preferences\SlideshowEffectTime` felhasználói értéke (mérés); (8) a `0x0094aa00` és a `0x0094ace0` hívói; (9) a `0x007fb540` közvetett hívója.

Nyitott kérdések: 9 nyílt (örökölt) · 7 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak nyitva (saját).

**Bizonyítottsági fok (38.2.21).**

| állítás | bizonyíték | fok |
|---|---|---|
| üzenethurok `0x0097fc30` | diszasszembly `0x0098030f-0x0098032a` (38.2.20) | megerősített |
| tizenegy közvetlen hívó, 1/5/10 ms | diszasszembly, az utolsó `push` | megerősített |
| az Időrend-pumpa azonosítása | NINCS MEG | nyitott |
| a 10 ms-os jelöltek webböngésző-jellegűek | dekompiláció 404, 501. sor | feltételes |
| visszahívás a pumpából, `call [vtable+4]` | diszasszembly `0x0097ffe3-0x0097fff5` | megerősített |
| a visszahívás a `0x00803ab0` | index-RTTI és `0xcbd6c8+4` | megerősített |
| a `0x00803ab0` visszatérései | diszasszembly `0x00803abc-0x00803aec` | megerősített |
| a `0x00802060` döntési sora | diszasszembly `0x00802066-0x00802125` | megerősített |
| léptetési küszöb: `S` másodperc | diszasszembly `0x008020b9-0x008020d4` | megerősített (küszöb) |
| az `S` felhasználói értéke | NINCS MEG | nyitott |
| szünet után az intervallum 1 ms | diszasszembly (`1` visszatérés), dekompiláció 207-209. sor | megerősített (író); más író NINCS MEG |
| a pumpa várakozása 5 ezredmásodpercnél rövidebb körben | diszasszembly `0x009802f9-0x00980308` | megerősített |
| a `[+0x51a]` írója és feltétele | diszasszembly `0x008018ac-0x008018b2`, `0x00801c19` | megerősített |
| a `[+0x51a]` három hívója | diszasszembly | megerősített |
| a hívók gyakorisága | a feltételek összevetése | feltételes |
| az olvasó 50 ms, legfeljebb 20 Hz | diszasszembly `0x007fb540-0x007fb58f` | megerősített |
| a `0x007fd800` kimenete EAX-ban | diszasszembly `0x007fe32f-0x007fe33e` | megerősített |
| `0x007fde80` a QDrawable 11. slotja | index-RTTI és `0xcbd698` olvasása | megerősített |
| a `0x203` ág a `0x201` blokkban nem fut | diszasszembly `0x007fe1d9-0x007fe346` | megerősített (kizárás) |
| ytUIEvent-konstruktor, destruktor, típustábla | dekompiláció 1376-1424, 1497-1554. sor | feltételes |
| slot-térkép (`0x4c`-`0x58`) | index-RTTI, `OneUpUI::vftable` | megerősített (a slot-szám); feltételes (az objektum) |
| vezérlők kattintása | NINCS MEG | nyitott |
| dátumcsúszka leképezése | NINCS MEG | nyitott |
| `[+0x2dc]` = `OneUpUI` | index-RTTI `0xcbd5c4`, foglalás 0x268 | megerősített |
| `[X+0x25c] == this` | diszasszembly `0x00802c79`, `0x00a51bb2`, `0x007fae4a` | megerősített |
| az alapút forrása az Időrend-ágban | dekompiláció 209-210. sor | feltételes (ellentmondás a 38.2.17-tel) |
| az alapút nem rendez | dekompiláció 350-453. sor, hívások | feltételes |

**Amit KIZÁRTAM (38.2.21).**
- A `0x0097fc30` időtúllépése nem az eltelt idő; a hívó adja.
- A `0x00982270` nem hívja a visszahívást.
- A `0x0094aa00` és a `0x0094ace0` a tartalmuk szerint nem Időrend-specifikus pumpa (a hívási kapcsolatot nem zártuk ki).
- `X` nem a QDrawable: külön, `0x268` bájtos OneUpUI objektum.
- A `0x007fe33e` hívásakor EAX nem a dekompiláció szerinti `0`, hanem a `0x007fd800` kimeneti mezője.
- A `0x203` ág a `0x201` blokkban nem fut.
- A `0x00802060` nem ad `0`-t.

**Fejlesztési következmény.** Terméki kódot nem írtunk. A léptetési ütem nem implementálható: hiányzik az Időrend-pumpa és a registry-érték. A `OneUpUI` és a `[this+0x2dc]` kapcsolat most már bináris. A kattintási cél és a dátumcsúszka leképezése nyitott, ezért a menüpont és a `Ctrl+5` bekötését a mostani ismeretek alapján nem lehet megírni.

**Következő Ghidra-körök.**

- ~~`Ghidra-kör kell: 0x00983430, 0x00983fc0, 0x00982bf0 - a qshow-ablak futtató hurka, és hogy a 0x0097fc30 11 hívója közül melyik fut az Időrend alatt, milyen időtúllépéssel [blokkoló]`~~ **RÉSZBEN JAVÍTVA (38.2.22, 1. szakasz):** a három függvény nem hurok (méret-értesítés, teljes képernyős váltás, `ytWindow` konstruktor). A futtató hívó és az időtúllépés **NINCS MEG**, lásd `Ghidra-kör kell: 0x005e6710` a 38.2.22 szakaszban.
- ~~`Ghidra-kör kell: 0x00802630 - a léptetés törzse, és a nem nulla visszatérés (-1, a bejegyzés eltávolítása) [blokkoló]`~~ **JAVÍTVA (38.2.22, 2. szakasz):** a léptetés törzse igazolt; a callee nem nulla visszatérése `3`, a hívó `0x00802060` ezt `-1`-re képezi.
- ~~`Ghidra-kör kell: 0x00982270 - a bejegyzés-lista felépítése és sorrendje [nem blokkoló]`~~ **JAVÍTVA (38.2.22, 1. szakasz):** a `0x00982270` a globális tömb rendezetlen másolata; a sorrend a hozzáfűzési sorrend.
- ~~`Ghidra-kör kell: 0x007fd800, 0x007fd8c0 - a találati index kimenete és a visszatérési érték jelentése [blokkoló]`~~ **RÉSZBEN JAVÍTVA (38.2.22, 3. szakasz):** a `0x007fd800` a kurzor alatti elem rekordjának `+0` mezőjét adja, vagy `-1`-et; a `0x007fd8c0` a 0,666 konstanshoz legközelebbi kártyát keresi. A `+0` mező jelentése **NINCS MEG**. A `0x007fd770` visszatérése **LEZÁRVA** (38.2.23 §6, 38.2.38 §1: 0).
- ~~`Ghidra-kör kell: 0x007fda80 - a 0x201 Időrend-ág hívott függvénye és az 1000000 visszatérés [blokkoló]`~~ **JAVÍTVA (38.2.22, 4. szakasz):** a `0x007fda80` négy overlay-téglalap találati függvénye; az `1000000` a kezelt kattintás jele.
- ~~`Ghidra-kör kell: 0x007fb210 - az overlay-elemek rajz- és találati téglalapjai, és a sliderthumb, timelinedot, startbutton, exit, listaikon kattintás-kezelői [blokkoló]`~~ **RÉSZBEN JAVÍTVA (38.2.22, 5. szakasz):** az overlay-nevek és az objektumok összerendelése megvan; a négy találati téglalap a `startbutton`, `exit`, `right`, `left` overlay-eké. A rajz, a `sliderthumb` húzásának hatása és a többi overlay kattintása **NINCS MEG**.
- `Ghidra-kör kell: 0x00a6cd10, 0x00a52820, 0x00401570, 0x00803180, 0x008032e0 - az OneUpUI kattintás-kezelői és a határoló téglalap, és hogy a 0x009e4630 melyik objektumon fut [blokkoló]`
- `Ghidra-kör kell: 0x005e8a70 - a local_c0 és a local_bc írói az Időrend-ágban (kimenet 209-210. sor), és a forrás-lista eredete; diszasszembly-ellenőrzés [blokkoló]`
- `Ghidra-kör kell: 0x0094aa00 és 0x0094ace0 hívói (0x00593450, 0x006fc7d0, 0x006fcb60, és a 0x0094ace0 tíz hívója) - Időrend-e [nem blokkoló]`
- ~~`Ghidra-kör kell: 0x006f9cc0 - az 1 ms-os 0x0097fc30 hívó (0x006fb417) kontextusa, qshow-e [nem blokkoló]`~~ **RÉSZBEN (38.2.22, 1. szakasz):** statikus hívási úton a `0x008037e0`-tól 9 szinten nem érhető el; a kontextus **NINCS MEG**.
- `Ghidra-kör kell: 0x00a52890 - a típuskódok diszasszemblált ellenőrzése (1, 2, 3, 4, 5, 0xd, 7, 8) [nem blokkoló]`
- Mérés kell (nem Ghidra): a `Preferences\SlideshowEffectTime` felhasználói értéke a tulajdonos gépén (futó Picasa vagy a registry-kulcs) [blokkoló a léptetési ütem pontos értékéhez]

#### 38.2.22 Az Időrend bináris feltárása, 5. kör: hurok, léptetés, találat, négy téglalap, csúszka-sáv (#5401, 2026-10-20)

**Kérdés és hatókör.** A 38.2.21 „Következő Ghidra-címek” nyolc címét dolgoztuk fel: `0x00983430`, `0x00983fc0`, `0x00982bf0`, `0x00802630`, `0x007fd800`, `0x007fd8c0`, `0x007fda80`, `0x00982270`. Öt kérdés volt: (1) melyik futtató hurok és időtúllépés fut az Időrend alatt, és milyen a bejegyzés-lista sorrendje; (2) mit csinál egy léptetés, és mit jelent a nem nulla visszatérés; (3) mi a találati kimenet; (4) mi a `0x007fda80`, és mit jelent az `1000000`; (5) hogyan kattintanak a vezérlők, és hogyan képződik le a dátumcsúszka.

**Bemenet és módszer.** Az `idorend-5` nyolc Ghidra-blokkja, és az `idorend-1` a `0x007fb210` miatt. A bináris index (`functions`, `xrefs`) csak függvényszintű `call` éleket tartalmaz: 78 901 sor, vtable- és függvénymutató-hivatkozás nincs benne. A sorok `from_address` mezője a hívó függvény kezdőcíme (például `0x004051b0`), nem a hívóhely; a hívóhelyet a diszasszemblálás adja (például `0x0040e4b1`). A diszasszemblálás a `pe_dis` modulból jött (capstone). Futásfelvétel és QEMU-futtatás nem volt. Terméki kódot nem írtunk.

**1. Futtató hurok, időtúllépés, bejegyzés-sorrend.**

Három cím nem hurok. Mindhárom a qshow-építőből (`0x008037e0`) hívódik:

- `0x00982bf0` (hívóhely `0x008038ec`): a `ytWindow` konstruktora (a vtable `ytWindow::vftable`). Tárolja a cím szövegét (`0x00985ff0`), és meghívja a `0x00983670` függvényt (ablak létrehozása, belseje **NINCS MEG**).
- `0x00983430` (hívóhely `0x00803983`): `GetClientRect` a `[this+0x6c]` ablakra, majd `0x00983a60(szél, magasság)`. Ha a kliensterület nem üres és `[this+0x64]` nem nulla, a `[this+0x64]` objektum vtable `+0x20` slotját hívja `(-1, -1, -1, -1)` argumentumokkal. Méret-értesítés.
- `0x00983fc0` (hívóhelyek `0x0080398f` és `0x005e68c5`, utóbbi a `0x005e6710`-ben): teljes képernyős váltás. Nem nulla paraméternél: a menü eltávolítása (`SetMenu` NULL), a `[this+0x70]` ablak megszüntetése (`DestroyWindow`), a stílus beállítása `0x96000000` vagy `0x96080000` értékre a `(*DAT_00d69524)` függvénypointeren a `-16` (`GWL_STYLE`) indexszel, és a képernyő méretére állítás (`GetSystemMetrics` 0 és 1; ha `0x00983b50` nem nulla, a `DAT_00d678b0` pointeren át). Nulla paraméternél visszaállítás: `SetMenu`, `0x00982ee0`, vtable `+0x10`, és ha a 2-es bit be van állítva, `SetWindowPos`. A `DAT_00d69524` célját nem ellenőriztem.

Tehát a qshow-építő létrehozza az ablakot (`0x00982bf0`), értesíti a méretéről (`0x00983430`), és teljes képernyőre kapcsolja (`0x00983fc0`).

A futtató hurok a `0x0097fc30` (38.2.20 §1: `PeekMessageA`, `MsgWaitForMultipleObjects`). Közvetlen hívói (függvényszint) tizenegyen vannak:

- 1 ms: `0x0040e410`, `0x005ffc30`, `0x006f9cc0` (hívóhely `0x006fb417`), `0x006fe630`, `0x009d4d10`;
- 5 ms: `0x004051b0`, `0x0059e920`, `0x007420f0`, `0x007422d0`;
- 10 ms: `0x0094aa00`, `0x0094ace0` (webböngésző-pumpa, 38.2.21 §1).

**Melyik hívó fut az Időrend alatt: NINCS MEG.** A bináris index nem köti össze a hívókat a qshow-val:

- `0x008037e0` egyetlen közvetlen hívója `0x005e8a70` (`CThumbUI::MakeTimeline`). Ennek hívói: `0x005cb990`, `0x005d9cc0`, `0x005e0f70`, `0x005e60d0`. A `0x005d9cc0` és a `0x005e0f70` hívója `0x005de8e0`; a `0x005e60d0` hívója `0x005e6710`.
- A `0x005cb990`, `0x005de8e0` és `0x005e6710` láncának tetején nincs közvetlen hívó az indexben. Valószínűleg függvénymutatón vagy vtable-on keresztül indul; ezt nem igazoltam.
- Egyik pumpa-hívóból sincs közvetlen hívási út `0x005e8a70`-hez vagy `0x008037e0`-hoz 9 szinten. Fordítva: a `0x008037e0`-ból 9 szinten elért 971 függvény között nincs pumpa-hívó.
- A `0x005e6710` hívja a `0x005e60d0`-t és a `0x00983fc0`-t is. Ez jelölt az Időrend-parancs kezelőjének, nem igazolt.

Ezért az időtúllépés is **NINCS MEG**: a 38.2.21 szerinti 1, 5 és 10 ms közül nem tudjuk, melyik érvényes.

**Bejegyzés-lista sorrendje (megerősített).** A `0x00982270` (hívója a pumpa, `0x0097feac`) a globális `DAT_00d69418` tömböt (darabszám: `DAT_00d6941c >> 1`) másolja a helyi pillanatképbe `_memcpy`-vel. Rendezés nincs. A másoláson kívül csak a kapacitás-növelés (`0x0097c810`), a felszabadítás (`0x0097caf0`) és egy zárolás (`0x0074cf40` vagy `0x009829f0`, belseje **NINCS MEG**) van. A pumpa ebben a sorrendben hívja a bejegyzéseket. A globális tömb sorrendje a hozzáfűzés sorrendje (38.2.19 §4: `0x0097d150`, arg2 = 0). Egy elem törlése után a tömörítés módja **NINCS MEG**.

**Léptetési ütem: NINCS MEG.** A legkorábbi léptetés S másodperc az utolsó léptetés után (38.2.21 §1, `Preferences\SlideshowEffectTime`). A tényleges időpont a pumpa-hívó időtúllépésétől függ, ezért **NINCS MEG**.

**2. A léptetés törzse (`0x00802630`).** Megerősített (dekompiláció és diszasszemblálás: `0x00802696`, `0x00802765`, `0x008026e9`).

- Zárolás: `[this+0x0c]` nulla esetén a vtable `+0x18` hívása, egyébként `EnterCriticalSection([this+0x28])`. A tulajdonos szál a `[this+0x20]`, a rekurzió a `[this+0x24]` mezőben van.
- Darabszám `[this+0x3f0] >> 1`. Ha nulla (`0x0080263a`): `0x009a8a30`, `0x009a8ca0([this+0x160])`, `0x009a8bc0`, és visszatér `0`-val.
- Ha az index `[this+0x3f4]` nem kisebb a darabszámnál (lista vége):
  - `[this+0x3fd] != 0` (`0x00802696`): az index `-1`, majd +1 után `0`. Csendes körbefordulás, nincs hívás.
  - `[this+0x3fd] == 0`: ha `[this+0x3b9] == 0`, meghívja a `0x007fb820` függvényt (38.2.18 szerint ez az `Escape` kilépési ága), feloldja a zárolást, és visszatér `3`-mal. Ha `[this+0x3b9] != 0` (`0x00802765`): az index `0`, a `0x007fda00` átmenet-indítás, feloldás, visszatérés `0`-val.
- Egyébként az index +1 (`0x008026ac`), feloldás, majd `0x00802230(this, 0)` (`0x008026e9`). Ha ez `0`-t ad, a léptetés `0`-val tér vissza. Ha `4` vagy `-1`, a ciklus újra fut.

Jelentés: egy lépés a következő index kiválasztása, majd az új képkocka a `0x00802230` nulla paraméteres változatával (38.2.19 §1: új véletlen eltolás). A lépés nem hív átmenet-indítót. Az átmenet-indító (`0x007fda00`) csak a lista végi újraindításkor fut.

**Nem nulla visszatérés.** A dekompiláció szerint csak `3` jöhet létre. A hívó `0x00802060` (`0x008020e1`, diszasszemblálás): `test eax,eax`; nulla esetén a normál út (`0x008020f2`), nem nulla esetén `or eax,-1`, azaz `-1`. A pumpában a `-1` a bejegyzés eltávolítása (38.2.21 §1). A `mov eax,3` sort nem ellenőriztem diszasszemblálással.

**Következmény (megerősített).** A `0x007fda00` állítja `[this+0x3b9] = 1`-re (38.2.19 §2). Ezért Időrend módban a lista vége nem lépteti ki a futtatót: a `[this+0x3fd]` értékétől függően csendesen körbefordul, vagy újraindítja az Időrendet. A `[this+0x3fd]` írója **NINCS MEG**.

**3. Találati kimenet (`0x007fd800`, `0x007fd8c0`).**

- `0x007fd800` (hívó `0x007fde80`, `0x007fe32f`): a kurzor alatti elem keresése. Bemenet: a `[this+0x2f8]` alobjektum (`lea ecx,[edi+0x2f8]`), a pont két float értéke (`ebx`), és a kimeneti mutató (`[esp+0x18]`). Az indexlistán (`[+0x80]`, darabszám `[+0x84] >> 1`) megy végig. Az elem rekordja `[+0xb0] + i*0xf8`; a téglalap bal széle `+0xdc`, felső széle `+0xe0`, jobb széle `+0xe4`, alsó széle `+0xe8` (egész számok). Találat: bal <= x < jobb és felső <= y < alsó. Az első találatnál a kimenetre a rekord `+0` mezőjét írja, és visszatér a `0x007fd770(i)` értékével. Nincs találat: `0xffffffff`.
- A hívó csak nulla visszatérésnél folytat (`0x007fe334-0x007fe336`), és ekkor az `[esp+0x18]` értéket adja a `0x008018a0`-nak (`0x007fe338-0x007fe33e`).
- Jelentés: a kimenet a rekord `+0` mezője, nem a listaindex. Hogy ez azonosító vagy index, **NINCS MEG**. A `0x007fd770` visszatérése **LEZÁRVA (38.2.23 §6): 0**.
- `0x007fd8c0` (hívó `0x00801cb0`, `0x00801cd8`): nem egérkeresés. A `[this+0xb4] >> 1` darabszámon megy végig. Minden `i`-re x_i = `i` * `[this+0x30]` + `[this+0x20]` (mindkettő f64), meghívja a `0x007fbab0` függvényt (`ecx = this`, x_i argumentum), majd a `0x0049f5c0`-val (`fabs`, cdecl, `ret`) a |x_i - 0,666| értéket számolja. A 0,666 a `0xcf4860` f64 konstans, pontosan 0,6660000085830688. A legkisebb távolságú `i` marad: `[this+0]` = `i`, `*param_1` = a rekord `+0` mezője.
- Eltérés: a diszasszemblálásban a legkisebb-kereső összehasonlítása más verem-helyről olvas, mint ahová a kezdeti küszöb íródik (`0xcf4900` = 1000000,0). **LEZÁRVA (38.2.23 §6):** a min-tároló a verem E0+0xc helyén van, a dekompiláció helyes (legkisebb távolság, kezdeti küszöb 1000000).
- Visszatérés: **JAVÍTVA (38.2.23 §4):** a `0x009a5210` nem időablak-ellenőrzés, hanem eltelt idő (QPC). Az időablak-vizsgálat a `0x007fd8c0` belsejében van, a `[this+0x48]` rekordjain; a visszatérés jelentése **NINCS MEG**.
- A 0,666 szerepe (lejátszási pont vagy más) **NINCS MEG**. A kártya-sor rajzolása nincs igazolva.
- Lánc Időrend módban: a `0x00802060` hívja a `0x00801cb0`-t, ha `[this+0x3b8] != 0`; a `0x00801cb0` csak akkor fut tovább, ha `[this+0x429] == 0` és a `0x007fd8c0` nem nullát ad. Az eredmény `[this+0x510]`-be kerül, és a `0x008018a0` állítja a `[this+0x51a]` jelzőt (38.2.21 §2).

**4. A `0x007fda80` és az `1000000`.**

- Hívók a `0x007fde80`-ban: `0x007fe1fd` (a 0x201-ágban, ha `[this+0x3b8] != 0`; diszasszemblálva) és `0x007fe15f` (nem ellenőriztem).
- Bemenet: `x = [this+0x420]`, `y = [this+0x424]` (float). A függvény a `this`-t az ESI-ből olvassa (`unaff_ESI` a dekompilációban; `mov esi,edi` a `0x007fe1fb` címen).
- Négy téglalap. Az `X` az overlay-objektum alap-offsetje (5. szakasz):

| sorrend | X | overlay | bal, felső, szél, magasság | művelet | visszatérés |
|---|---|---|---|---|---|
| A | `0x738` | `startbutton` | `+0x750`, `+0x754`, `+0x740`, `+0x744` | `0x007fb820`, majd `[this+0x2e8]` vtable `+0x18` hívása `(-1, azonosító)` | `1000000` |
| B | `0x580` | `exit` | `+0x598`, `+0x59c`, `+0x588`, `+0x58c` | `0x007fb820` | `1000000` |
| C | `0x558` | `right` | `+0x570`, `+0x574`, `+0x560`, `+0x564` | `0x007fd150` | `1000000` |
| D | `0x530` | `left` | `+0x548`, `+0x54c`, `+0x538`, `+0x53c` | `0x007fd120` | `1000000` |
| - | - | - | - | nincs találat | `0xf4241` (1000001) |

- Azonosító: `[ [this+0x3ec] + [this+0x3f8]*4 ]`, ha `[this+0x3f8] >= 0`, egyébként `0`. Ez az utoljára megjelenített elem (`[this+0x3f8]` az utolsó megjelenített index, 38.2.19 és 38.2.21).
- Az `[this+0x2e8]` objektum osztálya **NINCS MEG**. A `0x007fa7f0` építő a harmadik paraméterként adja (38.2.20 §6).
- Az `1000000` jelentése: a kattintás egy négy overlay egyikébe esett, és a kezelő kész. A `0x007fde80`-ban `cmp eax,0xf4240` és `je 0x007fe441` (`0x007fe202-0x007fe207`); a `0x007fe441` ága `mov eax,0xf4240` és a függvény kilépése. Húzás nem indul. A `0xf4241` esetén a `0x007fde80` a húzás-ággal folytatja (`0x007fe20d`).

**5. Vezérlők és dátumcsúszka.**

- Overlay → X leképezés (megerősített, a `0x007fb210` diszasszemblálásából): a `0x00410fa0(X)` hívás előtt `lea edi,[esi+X]`, `push edi`, `mov edx, <sztring>` áll. A sztringek a `0x00cbd334`-től indulnak: `left` = `0x530`; `right` = `0x558`; `mouse` = `0x5a8`; `rollovermouse` = `0x5d0`; `exit` = `0x580`; `timeline` = `0x6c0`; `timelinedot` = `0x6e8`; `sliderthumb` = `0x710`; `startbutton` = `0x738`. A tizedik, `overlay`, helyi objektumon töltődik.
- Mezők (dekompiláció): `X+0x08` szél, `X+0x0c` magasság, `X+0x18` bal, `X+0x1c` felső. A bal mezőt a dekompiláció `_DAT_00d34040`-nel szorozza és kerekíti (`ROUND`), a felső mezőt nem. Hogy a felső mezőnek van-e más skálázása, **NINCS MEG**.
- Húzás-sáv (`0x007fde80` 0x201-ága, a 4. kimenet dekompiláció 892-915. sora): a sáv a `timeline` (X `0x6c0`): bal `[+0x6d8]`, szél `[+0x6c8]`. A csúszka-gomb a `sliderthumb` (X `0x710`): bal `[+0x728]`, felső `[+0x72c]`, szél `[+0x718]`, magasság `[+0x71c]`. A dekompiláció a csúszka helyét a sáv bal és jobb széle közé korlátozza; a pontos képlet **LEZÁRVA (38.2.23 §3)**: `[this+0x728]` = trunc(x_c - (floor(SW/2) + 3)); korábban csak dekompiláció volt, most diszasszembly is megerősíti.
- A `sliderthumb` kattintása nem tartozik a `0x007fda80` találati vizsgálatába; a húzás-ágon megy. A húzás indítását a 38.2.21 §3 írja (`0x007fdd00`), ezt nem ellenőriztem.
- **A dátumcsúszka leképezése (csúszka-hely -> dátum vagy képindex): RÉSZBEN (38.2.23 §3).** A csúszka-hely rekordsorszámot ad (i*); a dátum vagy képindex jelentése **NINCS MEG**.
- `timelinedot`, `mouse`, `rollovermouse` és `overlay`: a `0x007fda80` nem vizsgálja őket. Kattintási céljuk **NINCS MEG**.
- Listaikon: nem azonosítottam, melyik overlay. **NINCS MEG**.

**6. Javítások a korábbi szakaszokban.**

- 38.2.21 „Következő Ghidra-címek” első tétele: a `0x00983430`, `0x00983fc0`, `0x00982bf0` nem a futtató hurok (1. szakasz). A futtató a `0x0097fc30`.
- 38.2.21 §1: a `0x00802630` nem nulla visszatérése `3`; a `-1` a hívó (`0x00802060`) leképezése (2. szakasz).
- 38.2.21 §1: a `0x00982270` sorrendje igazolt: rendezetlen másolat (1. szakasz).
- 38.2.21 §3: a `0x007fe33e` hívó EAX-értéke a `0x007fd800` kimeneti mezője: megerősítve (`mov eax,[esp+0x18]`, `0x007fe338`).
- 38.2.21 §3: a `0x007fda80` a 0x201 Időrend-ág négy téglalapos találati függvénye (4. szakasz).

**Bizonyítottsági fok (38.2.22).**

| állítás | bizonyíték | fok |
|---|---|---|
| `0x00982bf0`, `0x00983430`, `0x00983fc0` nem hurok | dekompiláció; hívóhelyek `0x008038ec`, `0x00803983`, `0x0080398f`, `0x005e68c5` | megerősített |
| futtató hurok: `0x0097fc30` | 38.2.20 §1, diszasszemblálás | megerősített |
| az Időrend alatti pumpa-hívó | index: nincs közvetlen hívási út 9 szinten | NINCS MEG |
| az időtúllépés | a hívótól függ | NINCS MEG |
| bejegyzés-lista sorrendje | `0x00982270` `_memcpy`, rendezés nélkül; `0x0097d150` hozzáfűzés | megerősített |
| léptetés törzse | dekompiláció `0x00802630`; diszasszemblálás `0x00802696`, `0x00802765`, `0x008026e9` | megerősített |
| nem nulla visszatérés: `3`, a hívó `-1` | dekompiláció; `0x008020e1` diszasszemblálás | megerősített (`mov eax,3` nem ellenőrzött) |
| lista vége Időrend módban nem lépteti ki | `0x00802765` `cmp`; dekompiláció; `0x007fda00` állítja `[this+0x3b9]`-et | megerősített |
| `[this+0x3fd]` írója | NINCS MEG | nyitott |
| `0x007fd800` téglalap-találat, kimenet a `+0` mező | dekompiláció; `0x007fe32f-0x007fe338` diszasszemblálás; `0x007fd8c0` vége `mov [edx], ecx` | megerősített (a mező jelentése NINCS MEG) |
| `0x007fd8c0` legkisebb távolság | dekompiláció; diszasszembly (38.2.23 §4: a min-tároló E0+0xc) | megerősített |
| `0x0049f5c0` = `fabs` | diszasszemblálás (`fabs`, `ret`) | megerősített |
| `0x007fda80`: négy téglalap és az `1000000` | dekompiláció; `0x007fe202-0x007fe207`, `0x007fe441` | megerősített |
| overlay-nevek és az `X` objektumok | `0x007fb210` diszasszemblálás (`0x007fb228-0x007fb4af`) | megerősített |
| húzás-sáv (`timeline`, `sliderthumb`) | diszasszembly `0x007fdd00` (38.2.23 §3) | megerősített |
| dátumcsúszka-leképezés | NINCS MEG | nyitott |

**Nyitott - következő Ghidra-körök.**

- `Ghidra-kör kell: 0x005e6710 - a függvénymutató-hivatkozásai (vtable, parancstábla), és a 0x0097fc30 hívóig vezető lánc; az Időrend-pumpa és az időtúllépése [blokkoló]`
- `Ghidra-kör kell: 0x007fd120, 0x007fd150 - a left és right overlay műveleteinek törzse [blokkoló]`
- `Ghidra-kör kell: 0x007fdd00 - a sliderthumb húzásának hatása: csúszka-hely -> dátum vagy képindex [blokkoló]`
- `Ghidra-kör kell: 0x007fbab0 - a kártya x-pozíciójának képlete (this+0x50, this+0x54, this+0x58) [blokkoló a rajzoláshoz]`
- `Ghidra-kör kell: 0x007fa7f0, 0x00802c60 - a [this+0x2e8] objektum osztálya és a startbutton visszahívás célja [blokkoló]`
- `Ghidra-kör kell: 0x007fd770 - a 0x007fd800 találati ágának visszatérése [nem blokkoló]`
- `Ghidra-kör kell: 0x0074cf40, 0x009829f0, 0x0097d370 - a 0x00982270 zárolása és a törlés tömörítési módja [nem blokkoló]`
- `Ghidra-kör kell: 0x007fe15f - a 0x007fde80 második 0x007fda80 hívóhelyének ága [nem blokkoló]`
- `Ghidra-kör kell: 0x007fb820 - a kilépési ág törzse (Escape) [nem blokkoló]`
- `Ghidra-kör kell: [this+0x3fd] írói (teljes .text pásztázás, paszta.py) [nem blokkoló]`

**Nyitott kérdések mérlege (38.2.22).** `Nyitott kérdések: 11 nyílt · 9 lezárva · 5 blokkolt (a blokkolók a Ghidra-listában)`

- **LEZÁRVA:** (a) a három függvény nem hurok; (b) a `0x00802630` léptetés-törzse; (c) a nem nulla visszatérés `3`, a hívónál `-1`; (d) a bejegyzés-lista sorrendje; (e) a `0x007fd800` téglalap-találata; (f) a `0x0049f5c0` = `fabs`; (g) a `0x007fda80` négy téglalapja és az `1000000`; (h) az overlay → `X` leképezés; (i) Időrend módban a lista vége nem lép ki.
- **NYITVA:** a pumpa-hívó és az időtúllépés; a léptetési ütem; a `[this+0x3fd]` írója; a `0x007fd8c0` visszatérésének jelentése; a `+0` mező jelentése és a `0x007fd770`; a `0x007fd8c0` összehasonlító slotja (feltételes); a `timelinedot`, `mouse`, `rollovermouse`, `overlay` és listaikon kattintása; a dátumcsúszka-leképezés; az `[this+0x2e8]` osztálya; a felső mező skálázása.

**A #5401 „Kész, ha” pontjai (5. kör).** (1) Képlánc: változatlan. (2) Átmenet és ütem: részben. A lista-végi viselkedés és a nem nulla visszatérés igazolt; a pumpa-hívó és az ütem **NINCS MEG**. (3) Vezérlők: a négy találati overlay (`startbutton`, `exit`, `right`, `left`) műveletei igazoltak; a csúszka és a többi overlay műveletei **NINCS MEG**. (4) Diavetítés és visszatérés: változatlan.

**Fejlesztési következmény.** Terméki kódot nem írtunk. A léptetési ütem továbbra sem implementálható: hiányzik a pumpa-hívó, az időtúllépés és a `Preferences\SlideshowEffectTime` felhasználói érték. Az Időrend lista-vége viselkedése igazolt (nincs kilépés), a négy gomb műveleti leképezése igazolt, a dátumcsúszka leképezése nem.

#### 38.2.23 Az Időrend bináris feltárása, 6. kör: pumpa-lánc, `left` és `right`, csúszka, kártya-görbe, `startbutton`, kilépés (#5401, 2026-10-20)

**Kérdés és hatókör.** Hat kérdés a `2026-10-20-idorend-6.txt` nyolc címéről: (1) `0x005e6710`; (2) `0x007fd120` és `0x007fd150`; (3) `0x007fdd00`; (4) `0x007fbab0`; (5) `0x00802c60` és a `[this+0x2e8]` objektum; (6) `0x007fb820` és `0x007fd770`. A 38.2.22 kísérő címei közül a `0x007fd8c0` és a `0x009e6010` is kellett. Terméki kódot nem írtunk.

**Bemenet és módszer.** Diszasszembly a `pe_dis.cdis` (capstone) segítségével. Az ideiglenes mentések a `.bt/` alá kerültek, a kör végén törölve. Index: `functions`, `xrefs` (függvényszintű hívások), `data_symbols`, `string_xrefs`. A vtáblák bejegyzéseit közvetlenül a `Picasa3.exe` bájtjaiból olvastam. Minden konstansnál ellenőriztem a betöltés méretét (`fld qword` = f64, `fld dword` = f32). Futásfelvétel és QEMU-futtatás nem volt.

**1. `0x005e6710`: az Időrend-pumpa és az időtúllépés**

- **Azonosítás (megerősített).** A `0x005e6710` a `CThumbUI::vftable` 12. bejegyzése: `0x00c9052c` + 0x30 = `0x00c9055c`, ez a `DATA` hivatkozás. A bájtokból olvasva a slot értéke `0x005e6710`.
- **Mit csinál (megerősített).** A főablak billentyű- és parancs-előszűrője. Visszatérése `1000000` (0xf4240: a hívó elnyeli) vagy `0xf4241` (továbbadja). Ágak: `WM_KEYDOWN` (`0x100`) `F2` (`0x71`): `0x0057d430`, `0x00407610`, majd `1000000`. `F3` (`0x72`): `0x009cd8a0`, `0xf4241`. `F4` (`0x73`): `0x009cd110` és a vtábla +0x78 hívása, `0xf4241` ha a feltétel teljesül. `F5` (`0x74`): `0x004a46e0`, `0x00579480(0,1)`, `[this+0xb0]+0x166` = 1, `0x0065b840`, a végén `0xf4241`. `F11` (`0x7a`): `0x00983fc0` (teljes képernyő). `F1` (`0x70`): `0x005d0cd0` vagy `0x009cd8a0`. `WM_SYSKEYDOWN` (`0x104`) `Enter` (`0x0d`), ha `[this+0xd29] == 0`: `0x005c9740`, `1000000`. `F12` (`0x7b`), és ha a `(param_2+0x10)` 4-es bitje be van állítva: `0x005e60d0` (billentyű-kapcsoló), a visszatérése a hívó értéke. Ezek az ágak csak akkor futnak, ha `0x0056c420`, `0x0056c110`, `0x00562d00`, `0x005f2650` és `0x0057c430(4)` mind 0-t ad.
- **Esc, Space és a nyilak nincsenek ebben a függvényben (megerősített).** Ezeket a `0x00801270` kezeli (5. pont).
- **Hívó és pumpa (megerősített, negatív).** A `0x005e6710` nem hívja a `0x0097fc30`-at, és a függvényszintű indexben nincs közvetlen hívója: a vtábla-bejegyzés az egyetlen belépési pont. Előre 12 szintig bejárva a 11 közvetlen pumpa-hívóból egyik sem ér el `0x005e6710`, `0x005e60d0`, `0x005e8a70`, `0x008037e0`, `0x007fda00`, `0x007fb820`, `0x00802630`, `0x00801270`, `0x007fa7f0`, `0x007fda80` vagy `0x007fde80` címet. A bejárt csúcsok száma 100 és 4910 között volt. Ez csak a közvetlen hívási élekre igaz: a vtábla-hívásokat az index nem látja, ezért nem zárja ki az utat.
- **Pumpa-lánc a `0x0097fc30`-ig: NINCS MEG.** Ghidra-kör kell: `0x005e6710` hívóhelye, vagyis a `CThumbUI` vtábla +0x30 hívása (`call [reg+0x30]`) a `0x0097fc30` hívóinak láncában. [blokkolt]
- **Időtúllépés: NINCS MEG.** A pumpa-hívók 1, 5 vagy 10 ms-os túllépést adnak (38.2.22 §1), de az Időrend alatt futó hívó nincs azonosítva. Ugyanez a Ghidra-kör. [blokkolt]
- **Léptetési ütem: NINCS MEG.** Az ütemet a pumpa hívója és a `Preferences\SlideshowEffectTime` együtt adja (38.2.21 §1, 38.2.22 §2). Pumpa nélkül nem mérhető. [blokkolt]

**2. `0x007fd120` (`left`) és `0x007fd150` (`right`)**

- **Művelet (megerősített).** `left` = `0x007fd0c0(+S, 2,0)`, `right` = `0x007fd0c0(-S, 2,0)`, ahol S = `[this+0x30]` (f64, f32-re konvertálva), a 2,0 pedig f32 az `0xcf3a48` címen (`fld dword`). A `right` az előjelet a `fchs` utasítással adja. Hívóhely: `0x007fdcda` (`left`) és `0x007fdc4e` (`right`), mindkettő a `0x007fda80`-ban.
- **Mit csinál a `0x007fd0c0` (94 bájt, megerősített).** Az alap B: ha `[this+0x4c] >> 1` nulla, akkor `[this+0x40]` (f64). Egyébként az utolsó rekord `+0x10` mezője: rekordlista `[this+0x48]`, rekordméret 0x28, n = `[this+0x4c] >> 1`. Utána v = `0x009a5210()` (eltelt idő, lásd a helyesbítést), és egy négy dupla szerkezet készül: vtábla `0x0072df60`, B, B+dx, v, v+dy. Ezután `call 0x009e6010`, az EAX-ban a szerkezet címével. A `0x007fd0c0` `xor eax, eax`-szal tér vissza.
- **Mit léptet: JAVÍTVA (38.2.24 §1).** A `0x0072df60` nem vtábla, hanem a rekord `easing`-függvénye; a `0x009e6010` a 40 bájtos rekord hozzáfűzése. A B az animátor kurzora, nem kép vagy dátum. Bizonyított: B-t S-sel tolja el, a második koordinátát a `dy` értékkel (2,0 vagy 4,0) növeli.
- **Mennyit (részben).** A lépték S = `[this+0x30]`; a dy 2,0 a `left` és a `right` hívásban. S írója NINCS MEG (4. pont), a dy jelentése NINCS MEG.
- **Új, mért: a nyíl-billentyűk is ide jutnak.** A `0x00801270` WM_KEYDOWN ágán: `0x25` és `0x26` a `0x008014bc` ágra ugrik, onnan `0x008011b0` hívódik, amely `0x007fd0c0`-t hív. `0x27` és `0x28` a `0x008014ac` ágra ugrik, onnan `0x00801210`, amely szintén `0x007fd0c0`-t hív. **LEZÁRVA (38.2.24 §1):** `0x25` és `0x26` +S-et, `0x27` és `0x28` -S-et ad (`0x008012bf`-`0x008012d9`).

**3. `0x007fdd00`: a `sliderthumb` húzása (megerősített, diszasszembly `0x007fdd00`-`0x007fde73`)**

- **Befogás.** x a [L, L+W] közé szorítva. L = `[this+0x6d8]` (a `timeline` sáv bal széle), W = `[this+0x6c8]` (a sáv szélessége), egész számok f32-re konvertálva.
- **Normált pozíció.** t = (x - L) / W (f32 osztás).
- **Keresés.** Ha `[this+0x38c] >> 1` legalább 1, n = `[this+0x38c] >> 1`, és minden i < n-re d_i = |A[i] / A[n-1] - t|, ahol A = `[this+0x388]` (f64 tömb). Kezdeti küszöb 1e7 (f64 `0xcf3e88` = 10000000,0). i* = az első i, amelyre d_i szigorúan kisebb az addigi minimumnál.
- **Kimenet.** `[this+0x514]` = i*. `[this+0x510]` = a rekord `+0` mezője, ha i* < `[this+0x3ac] >> 1` (rekordlista `[this+0x3a8]`, rekordméret 0xf8), egyébként 0.
- **A gomb helye.** `[this+0x728]` = trunc(x_c - (floor(SW/2) + 3)), ahol x_c a befogott x, SW = `[this+0x718]` a gomb szélessége. `[this+0x72c]` (felső szél) változatlan marad. A csonkolást a `0x00c29990` végzi (lent).
- **Dátum vagy képindex?** A leképezés sorszámot ad (i*): a csúszka helyéhez a normált A[i]/A[n-1] sor legközelebbi tagját rendeli. Hogy A dátumsor-e (és így a csúszka dátumot ad), **NINCS MEG**, mert `[this+0x388]` írója nincs nyomon követve. Ghidra-kör kell: `[this+0x388]` és `[this+0x38c]` írói, teljes pásztázással (`paszta.py`). [blokkolt]
- **A `0x00c29990` (28 bájt).** Ha `[0xda1428]` nem nulla: `cvttsd2si` (csonkolás). Ha nulla: x87 ág (`fistp` és javítás), amely csak akkor csonkol, ha az FPU kerekítési módja csonkoló. A fájlban a jelző értéke 0, írója NINCS MEG. [blokkolt, csak a csonkolás részleteihez]

**4. `0x007fbab0` (kártya-görbe) és `0x007fd8c0` (a 0,666-hoz legközelebbi kártya)**

*Görbe (megerősített).* Négy pont az objektum mezőin (k = 0..3):
- X_k: `+0x50`, `+0x5c`, `+0x68`, `+0x74`; Y_k: `+0x54`, `+0x60`, `+0x6c`, `+0x78`; W_k: `+0x58`, `+0x64`, `+0x70`, `+0x7c`.
- Bernstein-súlyok t-ből: B0 = (1-t)^3, B1 = 3t(1-t)^2, B2 = 3t^2(1-t), B3 = t^3.
- Konstansok (mind f64, `fld qword`): 3,0 (`0xcf39f8`), 2,0 (`0xc7d9d0`), 0,5 (`0xc72150`), és az 1,0 `fld1`-gyel.
- Képlet: N_x = Σ B_k·X_k, N_y = Σ B_k·Y_k, D = Σ B_k·W_k. x_out = 0,5 + 0,5·(2·N_x - 1)/D; y_out = 0,5 + 0,5·(2·N_y - 1)/D; w_out = 1/D. A kimenet három f32 az EAX-ban adott pufferbe: x, y, w.
- Ellenőrzés: a konstansok, a `fdivr`, az `fld1` és a 0,5-ös szorzás-összeadás a diszasszemblálásban megvan. A teljes x87 műveleti sorrend végigkövetése nem készült el.

*Mezők írói: NINCS MEG.* A `0x007fa7f0` konstruktor `ebp`-n át nem ír a `+0x18`…`+0x7c` mezőkre (csak a `+0x48` vtábla-mutatót). A `0x007fbab0` hívói: `0x007fbce0` (`0x007fbd3a`), `0x007fc010` (`0x007fc100`), `0x007fd8c0` (`0x007fd91c`). Ghidra-kör kell: a három hívó `this`-e, és a `+0x50`…`+0x7c`, `+0x20`, `+0x30` mezők írói. [blokkolt]

*Legközelebbi kártya (`0x007fd8c0`, 304 bájt, megerősített).*
- Kezdeti küszöb: 1000000,0 (f32 `0xcf4900`).
- Ciklus i = 0..n-1, n = `[this+0xb4] >> 1`. t_i = i·S + O, ahol S = `[this+0x30]`, O = `[this+0x20]` (f64). Hívja a `0x007fbab0`-t t_i-vel, majd d_i = |x_out - 0,666|. A 0,666 f64 az `0xcf4860` címen (0,6660000085830688).
- Az első legkisebb d_i nyer (szigorú `<`). Az eredmény `[this+0]` = i*. A kimeneti mutató (első argumentum) a rekord `+0` mezőjét kapja (rekordlista `[this+0xb0]`, rekordméret 0xf8).
- A minimum-tároló a verem E0+0xc helyén van; a dekompiláció és a diszasszembly egyezik.

*Visszatérési érték (feltételes).* Ha |[this+0x18]| > 0,01·S (f64 `0xcf40b8` = 0,01), `al` = 0. Egyébként n2 = `[this+0x4c] >> 1`: n2 > 1 esetén 0; n2 = 0 esetén 1; n2 = 1 esetén, a = a rekord `+0x18`, b = a rekord `+0x20`: ha a = b, 1; egyébként (v - a)/(b - a) > 1,0 esetén 1, különben 0; v = `0x009a5210()`. A jelentése **NINCS MEG**.

*A 0,666 szerepe.* A ciklus azt a kártyát választja, amelynek görbe-x-e (x_out) a legközelebb van 0,666-hoz. Hogy ez az aktuális kártya-e, **NINCS MEG** (a `0x00801cb0` és `0x00801cd8` hívók nincsenek visszafejtve). [blokkolt]

**5. `0x00802c60`, `[this+0x2e8]`, és a `startbutton` visszahívása**

- **`0x00802c60` (297 bájt, megerősített).** A `OneUpUI` konstruktora (vtábla `0x00cbd5c4`). Paraméterei: az új objektum, `param_2` = `this` (a `+0x25c` mezőbe), `param_3` = `[this+0x2e8]` (a `+0x260` mezőbe). Az objektum 0x268 bájt: foglalás `0x0097c5d0`, nullázás `0xbf37c0` (`0x007fae32`-`0x007fae39`). A visszatérés `[this+0x2dc]`-be kerül (`0x007fae55`). Ez 38.2.21 §4-gyel egyezik.
- **`[this+0x2e8]` = `[X+0x8]` (megerősített).** A `0x007fa7f0` `mov edi, eax` sora az X-et veszi fel, és a `this`-t `mov ebp, [esp+0x34]`-gyel az új objektumból. X a `0x008037e0` (qshow-építő) `edi`-je, amelyet a `0x00803920` előtt `mov eax, edi` ad át. Hogy ez melyik objektum, **NINCS MEG**.
- **Osztály: NINCS MEG.** A `0x008037e0` egyetlen közvetlen hívója a `0x005e8a70` (`CThumbUI::MakeTimeline`, 38.2.22 §1), ezért X feltehetően a `MakeTimeline` tulajdonosa, de ez feltételes. Ghidra-kör kell: `0x008037e0` `edi`-forrása és `[X+0x8]` osztálya. [blokkolt]
- **A `startbutton` sorrendje (megerősített).** A `0x007fda80` `0x007fdb0a`-es hívása a `0x007fb820` (kilépési ág, 6. pont). Utána, ha `[this+0x2e8]` nem nulla: `mov ecx, [this+0x2e8]`, `mov eax, [edx+0x18]`, `call eax` (`0x007fdb3d`). Ez a vtábla +0x18 slotját hívja `(-1, azonosító)` argumentumokkal. Az azonosító `[[this+0x3ec] + [this+0x3f8]·4]` (38.2.22 §5, ebben a körben nem mértem újra).
- **A vtábla +0x18 célja: RÉSZBEN JAVÍTVA (38.2.24 §4).** A `OneUpUI` vtábla 6. slotja a `0x0097b5e0`: `add ecx, 0x28`, `push ecx`, `call [0xc4055c]`. Ha a `[this+0x2e8]` objektum ugyanabból az alaposztályból való, ugyanez a `thunk`; ezt nem igazoltam. **JAVÍTVA (38.2.24 §4):** a `[0xc4055c]` a KERNEL32 `EnterCriticalSection` IAT-rekesze (a PE-importtáblából; az index `imports.address` oszlopa a név RVA-ja, nem a rekesz címe). Így a thunk `EnterCriticalSection(this+0x28)`. Az X osztálya továbbra is nyitott, ezért a `startbutton` célja NINCS MEG (38.2.24 §4).
- **A diavetítés-indítási feltevés nem támogatott.** A gomb a kilépési ágat futtatja előbb, és csak utána értesíti a forrást `(-1, azonosító)`-val. Ez inkább „bezár, és az azonosítót visszaadja" mintát mutat. A forrás válaszának megfejtése nyitott.

**6. `0x007fb820` (kilépési ág) és `0x007fd770` (találati ág)**

- **`0x007fb820` (459 bájt, megerősített lépések).** ECX = `this`.
  1. `[this+0x3bf] = 1`.
  2. Ha `[this+0x3bb] == 0`:
     - `[this+0x3be] = 0`; `0x008001c0(this, this+0x46c, -1, -1, -1, -1)` (**MEGERŐSÍTVE, 38.2.30 §1:** a hívóhely `0x007fb86b`, az argumentumok igazoltak; a hatás a 0x008001c0 belsejéből RÉSZBEN, lásd 38.2.30); `[this+0x3b8] = 0`; `0x009ad280(this+0x46c)` (NINCS MEG).
     - Ha `[this+0x49c] == 0`: `0x009a8d80(...)`, különben `0x009a8ca0(...)` (NINCS MEG).
     - `QueryPerformanceCounter` → `[this+0x520]` (f64, a kezdő idő).
     - `old` = `0x004019b0([this+0x760])`: a `Preferences\SlideshowEffectTime` értéke. Majd `0x00401900([this+0x760], 2)`: a 2 íródik a registry-be és a gyorsítótárba (`[this+0x76c]`).
     - Várakozás: eltelt idő = (QPC - [this+0x520]) × (1/QPF), és küszöb = `0x004019b0([this+0x760])` × 0,6 (f64 `0xcf3a70`; negatív értéknél +2^32). Amíg thr > elapsed: `0x00801f50(this)` (NINCS MEG), majd újra.
     - `0x00401900([this+0x760], old)`: visszaállítás.
  3. Ha `vt+0x24(this)` nem nulla, annak az eredményén `vt+0x14(0,0)` hívódik. Ha nulla, és a `[this+0x2dc]` (`OneUpUI`) vt+0x24 hívása nem nulla, azon hívódik `vt+0x14(0,0)`. Egyébként visszatérés 0. A `vt+0x14` célja NINCS MEG.
  4. Visszatérés 0.
- **A várakozás értéke: 2 × 0,6 = 1,2 s (a kódútra megerősített).** A 2 kiírása után a `0x004019b0` a registry-ből olvas; ha az sikeres, 2-t kapunk, ha nem, a gyorsítótárban maradt 2 az érték. Ha a registry-írás hibázik, de a kiolvasás sikerül, a régi érték × 0,6 lenne. Futásidejű ágat nem mértem: NINCS MEG.
- **Az Escape-ág (megerősített).** A `0x00801270` (`OneUpUI` billentyű-kezelője) WM_KEYDOWN ágán (`0x0080129e`): `cmp al, 0x1b` (`0x008012a7`), `jne 0x008012bf`, különben `mov ecx, ebx` és `call 0x007fb820` (`0x008012b1`). Escape tehát közvetlenül ide vezet. A `0x007fb820` többi hívója: `0x007fdb0a` és `0x007fdbc2` (`0x007fda80`), `0x007fe171` és `0x007fe43c` (`0x007fde80`), `0x008005bb`, `0x008005e1`, `0x008007fe` (`0x008001c0`), `0x008027c8` (`0x00802630`).
- **`0x007fd770` (129 bájt, megerősített).** Argumentum: i. x = ([this+0x8] - (i·S + O)) - (B - v'), ahol v' = `0x009e5e70(0x009a5210())`, B mint a 2. pontban; dy = `+4,0` (f32 `0xc7e4a4`). Hívja a `0x007fd0c0`-t. **Visszatérés: 0**, mert a `0x007fd0c0` `xor eax, eax`-szal tér vissza, és a `0x007fd770` `ret 4` előtt az EAX-t nem írja. A dekompiláció `void`-ja ezt nem mutatja.
- A találati ág (`0x007fd800`) így 0-t ad, és a hívó (`0x007fde80`) nullának látja: ekkor az `[esp+0x18]` (a rekord `+0` mezője) folytatódik (38.2.22 §3). A `0x202` (felengedés) `0x007fd770(this+0x514)` hívása a húzás végén ugyanide visz (38.2.21 §3).

**Helyesbítések**

1. **38.2.22 §3, `0x007fd770`:** a „visszatérése NINCS MEG" **LEZÁRVA**: 0 (6. pont).
2. **38.2.22 §3, `0x009a5210`:** az „időablak-ellenőrzés" **TÉVES**. A `0x009a5210` eltelt idő: `QueryPerformanceCounter` (`call [0xc40298]`), a cache `[0xd678e8]` = 1/QPF (a `0x007fb820` is ezt használja). Az időablak-vizsgálat a `0x007fd8c0` belsejében van (4. pont).
3. **38.2.22 §3, legkisebb-kereső eltérés:** **LEZÁRVA**. A minimum-tároló a verem E0+0xc helyén van, a dekompiláció helyes.
4. **38.2.22 §5, húzás-sáv és csúszka:** a „feltételes" **MEGERŐSÍTETT**. A csúszka-gomb képlete (`[this+0x728]`) **LEZÁRVA** (3. pont). A dátum-leképezés **RÉSZBEN**: a csúszka x → rekordsorszám (i*) igazolt; a dátum jelentése NINCS MEG.
5. **38.2.18 és 38.2.22 (Escape):** az Escape-kilépés `0x007fb820`-ra megerősítve; az út közvetlen, a `0x00801270`-ból (5. pont).
6. **38.2.23 §2 (`0x009e6010`, `0x0072df60`):** JAVÍTVA: a `0x0072df60` `easing`-függvény, nem vtábla (38.2.24 §1).
7. **38.2.23 §2 (nyíl-billentyűk dx-előjele):** LEZÁRVA: `0x25`/`0x26` +S, `0x27`/`0x28` -S (38.2.24 §1).
8. **38.2.23 §5 (`[0xc4055c]`):** JAVÍTVA: KERNEL32 `EnterCriticalSection`, a „nincs import-név" állítás téves volt (38.2.24 §4). Az index `imports.address` oszlopa a név relatív címét (`RVA`) adja, nem a rekesz virtuális címét: rekesz-címhez a PE-importtáblát kell olvasni.

**Bizonyítottsági fok (38.2.23)**

| állítás | bizonyíték | fok |
|---|---|---|
| `0x005e6710` = `CThumbUI::vftable` +0x30 | vtábla-bájtok `0x00c9055c`; DATA-él | megerősített |
| `0x005e6710` ágai és visszatérése | dekompiláció és kapcsoló-ellenőrzés; Esc, Space, nyíl nincs | megerősített |
| pumpa-lánc a `0x0097fc30`-ig | index, 12 szint, 11 hívó: negatív; a vtábla-hívás nem látszik | NINCS MEG |
| `left` = +S, `right` = -S, dy = 2,0 | `fld qword [eax+0x30]`, `fchs`, `fld dword [0xcf3a48]` | megerősített |
| `0x007fd0c0` alap B és a négy dupla szerkezet | dekompiláció és diszasszembly `0x007fd0c0`-`0x007fd11b` | megerősített |
| `0x009e6010` szemantika | NINCS MEG | nyitott |
| csúszka: befogás, i*, `[this+0x728]` | diszasszembly `0x007fdd00`-`0x007fde73` | megerősített |
| csúszka: dátum vagy sorszám | `[this+0x388]` írói NINCS MEG | nyitott |
| `0x00c29990` ágai | diszasszembly `0x00c29990`, `0x00c299c6` | megerősített (a jelző írója NINCS MEG) |
| kártya-görbe képlete és konstansai | diszasszembly `0x007fbab0` (`fld1`, 2,0, 0,5, 3,0) | megerősített |
| görbe-mezők írói | a konstruktor nem írja; a többi NINCS MEG | nyitott |
| `0x007fd8c0`: i*, 1e6, 0,666 | diszasszembly `0x007fd8c0`-`0x007fd9ed` | megerősített |
| `0x007fd8c0` visszatérési érték | diszasszembly; jelentése NINCS MEG | feltételes |
| `0x00802c60` = OneUpUI, `[this+0x2dc]`, 0x268 | vtábla `0x00cbd5c4`; `0x007fae32`-`0x007fae55` | megerősített |
| `[this+0x2e8]` = `[X+0x8]` | `0x007fa7f0` `mov edi, eax`, `mov edx, [edi+8]` | megerősített |
| `[this+0x2e8]` osztálya | NINCS MEG | nyitott |
| `startbutton` sorrendje | `0x007fdb0a`, `0x007fdb3d` | megerősített |
| `[0xc4055c]` célja | NINCS MEG | nyitott |
| Escape közvetlen út | `0x00801270` `0x008012a7`-`0x008012b1` | megerősített |
| kilépési ág lépései | diszasszembly `0x007fb820`-`0x007fb9ea` | megerősített (az ismeretlen hívások NINCS MEG) |
| várakozás 1,2 s | `mov [esp+0x10], 2` és a `0x004019b0` olvasás | megerősített a kódútra; futásidőben feltételes |
| `0x007fd770` visszatérése 0 | `ret 4`, `xor eax, eax` a `0x007fd0c0`-ban | megerősített |

**Nyitott kérdések mérlege (38.2.23)**

Nyitott kérdések: 0 nyílt · 14 lezárva · 12 blokkolt · 0 hatókörön kívül · 0 csak nyitva.

A 38.2.24 mérlege a 38.2.24 végén van; a fenti tételek egy részét az ottani helyesbítések lezárják (6-8. pont a 38.2.23 helyesbítései között).

- **Lezárva (14):** (L1) `left` és `right` előjele és dy = 2,0; (L2) a nyíl-billentyűk a `0x007fd0c0`-ra; (L3) csúszka: befogás, i* és a gomb képlete; (L4) `0x00c29990` ágai; (L5) kártya-görbe képlete és konstansai; (L6) `0x007fd8c0` min-kereső és az eltérés; (L7) `0x00802c60` = OneUpUI, 0x268 bájt; (L8) `startbutton` sorrendje; (L9) Escape közvetlen út; (L10) kilépési ág lépéssora; (L11) 1,2 s várakozás a kódúton; (L12) `0x007fd770` visszatérése 0; (L13) `0x009a5210` javítása; (L14) pumpa-hívó negatív index-keresése 12 szinten (az index korlátaival).
- **Blokkolt (12):** (B1) pumpa-hívó és időtúllépés; (B2) léptetési ütem; (B3) `0x009e6010` és `0x0072df60`; (B4) S és O írói; (B5) `[this+0x388]` írói és a dátum jelentése; (B6) `[0xda1428]` írója; (B7) görbe-mezők írói; (B8) `0x007fd8c0` visszatérési értéke és a 0,666 szerepe; (B9) `[X+0x8]` osztálya és X; (B10) `[0xc4055c]` célja; (B11) kilépési ág ismeretlen hívásai; (B12) registry-írás sikertelenségének ága (futásidő).

**Amit KIZÁRTAM**

- A `0x005e6710` nem a pumpa; a pumpa a `0x0097fc30`, és a `0x005e6710` nem hív pumpát.
- A `left` nem `-S`-t ad: a `left` `+S`, a `right` `-S`.
- A `0x007fd770` nem ad nem-nulla visszatérést: mindig 0.
- A `0x009a5210` nem időablak-ellenőrzés: eltelt idő (QPC).
- Az Escape nem a `0x00802630` listavégi ágán megy; a `0x00801270` közvetlenül hívja a `0x007fb820`-t.
- A `startbutton` sorrendjében a diavetítés-indítás nem támogatott (lásd 5. pont).

**Következő Ghidra-címek**

- `Ghidra-kör kell: 0x005e6710 hívóhelye - a CThumbUI vtábla +0x30 hívása (call [reg+0x30]) a 0x0097fc30 hívóiban (0x0040e410, 0x005ffc30, 0x006f9cc0, 0x006fe630, 0x009d4d10, 0x004051b0, 0x0059e920, 0x007420f0, 0x007422d0, 0x0094aa00, 0x0094ace0); az Időrend-pumpa és időtúllépése [blokkolt]`
- `Ghidra-kör kell: 0x009e6010 és a 0x0072df60 vtábla - mit léptet a négy dupla szerkezet (B, B+dx, v, v+dy) [blokkolt]`
- `Ghidra-kör kell: [this+0x30] és [this+0x20] írói - a kártya-lépték (S) és eltolás (O) forrása [blokkolt]`
- `Ghidra-kör kell: [this+0x388] és [this+0x38c] írói - a csúszka-tömb: dátum vagy sorszám [blokkolt]`
- `Ghidra-kör kell: 0x007fbce0, 0x007fc010, 0x007fd8c0 this-hívói és a 0x007fbab0 +0x50..+0x7c mezőinek írói [blokkolt]`
- `Ghidra-kör kell: 0x008037e0 edi-forrása (X) és [X+0x8] osztálya [blokkolt]`
- `Ghidra-kör kell: 0x00c4055c - a 0x0097b5e0 thunk célja, a startbutton visszahívás végpontja [blokkolt]`
- `Ghidra-kör kell: 0x008001c0, 0x009ad280, 0x009a8d80, 0x009a8ca0, 0x00801f50 és a vt+0x24 / vt+0x14 célja - a kilépési ág lépései [blokkolt]`
- `Ghidra-kör kell: 0x007fd8c0 visszatérési értéke és a 0x00801cb0, 0x00801cd8 hívók [blokkolt]`
- `Ghidra-kör kell: [0xda1428] írója (az x87 vagy cvttsd2si ág) [blokkolt, csak a csonkolás részleteihez]`
- `Mérés kell (futásidő, nem Ghidra): a Preferences\SlideshowEffectTime írása sikeres-e a tulajdonos gépén (registry-próba) [blokkolt, az 1,2 s állításhoz]`

#### 38.2.24 Az Időrend bináris feltárása, 7. kör: animátor-rekord, nyíl-billentyűk, kártya-elrendezés, léptetés, `startbutton` (#5401, 2026-10-21)

**Kérdés és hatókör.** Négy kérdés a `2026-10-21-idorend-7.txt` nyolc címéről: (1) `0x009e6010` és `0x0072df60`: az animátor, a `left`/`right` és a nyíl-billentyűk; (2) `0x007fbce0`, `0x007fc010`, `0x008001c0`: a kártya-görbe mezői, az elrendezés és az `A` tömb; (3) `0x00801cb0` és `0x00801f50`: a körönkénti frissítés és az automatikus léptetés; (4) `0x0097b5e0`: a `startbutton` visszahívása. Terméki kódot nem írtunk.

**Bemenet és módszer.** Diszasszembly a `pe_dis.cdis` (capstone) segítségével; a függvényméretek az index `functions` táblájából valók. A `0x0072df60` nincs az indexben (a 7. Ghidra-futás hozta létre), ezért a diszasszembly a forrás. A PE-importtáblát közvetlenül a `Picasa3.exe` bájtjaiból olvastam (`FirstThunk` és ILT). Futásidejű próba és új Ghidra-futás nem volt. Az ideiglenes fájlok a `.bt/` alatt voltak, a kör végén törölve.

**Javítások a korábbi szakaszokban (a 38.2.23-ban is jelölve).**
1. A `0x0072df60` nem vtábla, hanem a rekord `easing`-függvénye (megerősített).
2. A `[0xc4055c]` nem „import-név nélküli" slot: a `KERNEL32` `EnterCriticalSection` rekesze.
3. A nyíl-billentyűk dx-előjele mérve: `0x25` és `0x26` +S, `0x27` és `0x28` -S.
4. Eszköz-tanulság: az index `imports.address` oszlopa a név relatív címét adja (`EnterCriticalSection`: `0x00921b04`), nem a rekesz virtuális címét (`0x00c4055c`). Rekesz-címhez a PE-importtáblát kell olvasni.

**1. Animátor: `0x009e6010`, `0x0072df60`, `left`/`right`, nyíl-billentyűk**

- **A rekord (megerősített).** A `0x007fd0c0` (94 bájt, `ret 8`) a veremben 40 bájtos rekordot épít, és a `0x009e6010`-zal (`call` a `0x007fd110`-nál) hozzáfűzi az animátor tömbjéhez. Az animátor a P objektumban van (P = `this+0x2f8`, a `0x007fd0c0` a P+0x38 alrészt használja): darabszám `[P+0x4c]>>1`, tömb `[P+0x48]`, gyorsítótárazott pozíció `[P+0x40]` (f64). A rekord mezői a verem-címekből: +0 függvénymutató (`0x0072df60`), +8 B (kezdőpozíció), +0x10 B+dx (végpozíció), +0x18 v (kezdő idő), +0x20 v+dy (végidő).
- **`0x009e6010` (236 bájt, megerősített).** Hozzáfűzés: 10 dword (40 bájt) másolása. A tömb kapacitása duplázódik 1 MiB-ig (`0x100000` bájt), azután 1024 rekordonként nő. Siker: 0; sikertelen lefoglalás: 4.
- **Easing: `0x0072df60` (megerősített, a `0x0072df60`-`0x0072e047` tartomány).** Bemenet u (f32). Ha u >= 1, az eredmény 1; ha u <= 0, 0. Különben y = 8·u (f64 `0xc7ea10` = 8,0), és:
  - ha y < 1: g(y) = y - 1 + E(-y);
  - ha y >= 1: g(y) = a + (1 - a)·(1 - E(-(y - 1))), ahol a = E(-1) (f32 `0xcf3ed0` = -1,0).

  Az eredmény K·g(y). E = `0x0040eac0`, amely a `0x00c29c6c` CRT-ugrót hívja (lásd B8). K = f64 `0xd337a8`, kezdetben 1,0 (őrszem): ha 1,0, a `0x009e5ac0` (96 bájt) beállítja K = 1 / g(8) értékre (a diszasszemblált `fdiv`). A g(8) számértéke a fenti konstansokból adódik; futtatott mérés nincs.
- **Folytonosság (erős érv, nem azonosítás).** g(1-) = E(-1) = a = g(1+). A deriváltak 1 - E(-1) és 1 - a, ezek egyeznek. Ez exp-re teljesül, más E-re általában nem (lásd B8).
- **Pozíció és Δ (megerősített).** A `0x009e5e70` (285 bájt): `pos(t) = B0 + Σ_j ease(u_j)·dx_j`, ahol u_j = (t' - v_j)/(end_j - v_j), dx_j = (B_j+dx_j) - B_j, t' = t + 0,02 (f64 `0xcf48a8` = 0,02), és B0 az első rekord B-je. Üres tömbnél a gyorsítótár az érték. A gyorsítótár `[P+0x40]` (`0x009e5f74`, `0x009e5eed`).
- **`0x009e5f90` (74 bájt, megerősített).** A visszatérés Δ = pos(t) - az előző gyorsítótár-érték, vagyis a kurzor előjeles elmozdulása az előző kiértékelés óta. Első híváskor a gyorsítótár az első rekord B-je.
- **`left` és `right` (megerősített).** `0x007fd120` = `0x007fd0c0(+S, 2,0)`, `0x007fd150` = `0x007fd0c0(-S, 2,0)`. S = `[P+0x30]` (f64, f32-re konvertálva), 2,0 = f32 `0xcf3a48`.
- **Nyíl-billentyűk (megerősített).** A `0x00801270` `WM_KEYDOWN` ága: `cmp al, 0x25` és `0x26` → `je 0x8014bc` → `0x8011b0` (`call 0x7fd0c0`, +S, 2,0); `cmp al, 0x27` és `0x28` → `je 0x8014ac` → `0x801210` (`fchs`, -S, 2,0). Mindkettő csak akkor animál, ha `[OneUp+0x3b8] != 0`; egyébként a `0x802980`/`0x802ae0` (a `0x8011b0`-ból), illetve a `0x8029f0`/`0x802a90` (a `0x801210`-ből) ágak futnak (NINCS MEG, mit csinálnak).
- **Időtartam (megerősített).** Nyíl és `left`/`right`: 2,0 s. Kattintás (`0x007fd770`, 129 bájt): dy = 4,0 (f32 `0xc7e4a4`). Az időegység a másodperc: `0x009a5210` = `QPC` · (1/`QPF`), a gyorsítótár `[0xd678e8]` (a `0x009a51b0` tölti ki `QueryPerformanceFrequency`-vel).
- **Mit mozgat (megerősített).** A `[P+0x40]` kurzort: ±S értékkel 2,0 s alatt, a fenti görbével. A kártyákat ennek Δ-ja tolja el (2. pont).
- **Mit jelent S (megerősített).** S a paraméter-lépköz a kártyák között: `t_i = i·S + O` (`0x007fc010`, `0x007fd8c0`, `0x007fd770`). Egy nyíl-lépés tehát egy kártyányi eltolás. S írója NINCS MEG (B1).

**2. Kártya-görbe, elrendezés, `0x007fbce0`, `0x007fc010`, `0x008001c0`, `A`**

- **Görbe `0x007fbab0` (559 bájt).** Bemenet t (f32), ECX = P. Olvassa P+0x50+12k (X_k), P+0x54+12k (Y_k), P+0x58+12k (W_k), k = 0..3 (`0x007fbab7`), Bernstein-súlyok, konstansok 3,0 / 2,0 / 0,5 / 1,0. Kimenet (x, y, w) az EAX-ban kapott pufferbe; az utolsó írás `0x007fbcaf` (`fstp dword [eax]`), a `ret 4` a `0x007fbcdc`-nél. A 38.2.23 §4 képlete a konstansokra és a fő lépésekre igaz (erős); a teljes x87-sorrend nincs végigkövetve.
- **P+0x20 és P+0x18 írói (megerősített, `0x007fc010`, 1191 bájt).** O = P+0x20: `0x007fc045` (`fst qword [ebp+0x20]`: O ← Δ + v + O régi), `0x007fc071` (felső korlát: O ← [P+8]), `0x007fc07e` (alsó korlát: O ← [P+8] - (n-1)·S). v = P+0x18: `0x007fc09e` (`fstp qword [ebp+0x18]`: v ← 0,95·v; f64 `0xcf40b0` = 0,95). Egy képkockán a sorrend: O ← Δ + v + O, korlátok, v ← 0,95·v.
- **Az S értéket a `0x007fc010` csak olvassa** (`[P+0x30]`); a többi írót lásd B1.
- **P+0x50..0x7c írói (NINCS MEG).** A `0x007fc010` ezeket nem írja: a `[esp+0x50]`…`[esp+0x68]` írások a verem helyi változói. Ghidra-kör kell (B2).
- **`0x008001c0` (megerősített, a dekompilált törzs alapján).** A `OneUpUI` renderelő függvénye. A saját zárolási mezőit írja (`[OneUp+0x20]` tulajdonos szál, `[OneUp+0x24]` beágyazás-számláló) és a `[OneUp+0x519]` jelzőt. P-mezőt nem ír. Figyelem: itt a `+0x20` a OneUp mezője, nem P+0x20. **JAVÍTVA (38.2.30 §4):** a renderer nem a kártya-rekordokat (`+0x2ec`, 0xf8 bájt) rajzolja: a törzsében nincs `+0x2ec`-es olvasás. A bemenete a `this+0x3c4` vagy a `this+0x46c` képpuffer (38.2.30 §1).
- **Kártya-elrendezés (megerősített).** Minden i < n = `[P+0xb4]>>1` kártyára:
  - t_i = i·S + O, és (x, y, w) = görbe(t_i);
  - eltolás (x·W_r, y·H_r), ahol W_r = R[2] - R[0], H_r = R[3] - R[1], és R = `[OneUp+0x2c8]` (a `0x00801cb0` adja át); az R-hez viszonyított kezdőpont a mátrix-láncból nincs igazolva;
  - lépték = w · Z, Z = `[P+0x28]` (f64);
  - átlátszóság: a kártya-rekord +0xa0 mezője = `ROUND`((1 - f(z))·256), z = max(0, (1/w - 1)/9); f64 `0xcf3ef8` = 9,0, f64 `0xcf39d8` = 256,0; f = `0x005568e0` (**LEZÁRVA, 38.2.25 M1:** `pow(z, 1,5)`);
  - látható lista: w > 0,1 (f64 `0xc7dd30` = 0,1); az indexek a `[P+0x80]` tömbben, darabszám `[P+0x84]>>1`; a rendezést a `0x00604480` végzi (NINCS MEG, B10).
- **Az elrendezés index-lineáris (megerősített).** A kártyák egyenlő t-lépésre állnak egymástól, i szerint. A dátum csak az `A` tömbön keresztül léphetne be (lásd alább).
- **`0x007fbce0` (166 bájt, megerősített).** t_i = i/10000 - 1 (f64 `0xcf42a8` = 10000,0), i = 0..19999 (`cmp esi, 0x4e20`), vagyis t ∈ [-1, 1) 0,0001-es lépéssel. Minden t_i-re hívja a `0x007fbab0`-t, és a kimeneti x-et veti össze 0,666-tal (f64 `0xcf4860`). A legkisebb |x - 0,666| adja t*-ot (az első i, szigorú `<` összehasonlítással). Visszatérés: t* (f32). Hívója a `0x007fbd90` (`0x007fbe74`); hogy mit kezd t*-gal, NINCS MEG (B12).
- **`A = [OneUp+0x388]` (NINCS MEG).** Olvasója a `0x007fdd00` (38.2.23 §3). Írói nincsenek nyomon követve, ezért a dátum vagy index kérdés nyitott (B3).

**3. Körönkénti frissítés és automatikus léptetés: `0x00801cb0`, `0x00801f50`, `0x00802060`, `0x00802630`**

- **`0x00802060` (198 bájt, megerősített ágak).** A körönkénti pumpa; `this` = OneUp. Első lépése `[0x3fc] = 1`. Ágak:
  1. `[0x3bb] != 0`: a `0x802121`-es ág (NINCS MEG, nem Időrend-frissítés).
  2. `[0x3b8] != 0` (animált mód): `call 0x801cb0` (`0x802087`). Utána, ha `[0x3c1] != 0`, léptetés (`0x802630`); különben `0x801f50` (`0x802110`).
  3. `[0x3b8] == 0`: ha `[0x518] != 0`, léptetés. Különben `elapsed` = `0x9a51b0([0x520])` (másodperc a `[0x520]` óta), `pref` = `0x4019b0([0x760])` (a `Preferences\SlideshowEffectTime` egész értéke, másodpercben); ha `elapsed > pref`, léptetés; ha `[0x3c1] != 0`, léptetés; különben `0x801f50`.
- **`0x00801cb0` (64 bájt, megerősített).** (1) `0x007fc010(P, &[OneUp+0x2c8])`: a kártya-elrendezés. (2) Ha `[OneUp+0x429] == 0` és a `0x007fd8c0(P, &[OneUp+0x510])` AL = 1, akkor `0x008018a0` fut (ECX = OneUp, EAX = `[OneUp+0x510]`). Az AL = 1 a 38.2.23 szerinti nyugalom-feltétel (feltételes jelentés).
- **`0x008018a0` (1029 bájt).** Belépéskor, ha `[OneUp+0x50c] == EAX`, visszatér (`0x801ca3`). Különben eltárolja az új értéket, és frissíti a nézetet. A hívott `0x004133e0`, `0x004b0190` és `0x0097caf0` szerepe NINCS MEG (B10).
- **`0x007fd8c0` (304 bájt, megerősített).** Kimenet: `[OneUp+0x510]`. AL = 1, ha a kiértékelés nyugalmat lát (38.2.23 szerint, feltételes).
- **`0x00801f50` (261 bájt, a hívások megerősítve).** Ha `[this+0x50]` nem nulla, `QPC`; `vt+0x40` **hívás** (JAVÍTVA, 38.2.29 §3: nem csak ellenőrzés; a `call eax` a `0x00800a30`-t hívja, ECX = `this`); ha `[this+0x3ba] != 0`: `GetClientRect` a `vt+0x24()` objektum `+0x6c` HWND-jén, `0x009b49c0(&rect)` (elrendezés), `vt+0x24(-1,-1,-1,-1)`, `0x009aa670`, `0x00800950(&rect)`. Különben `0x00aa6fb0` és `0x00aa6b70`. Hívói: `0x00802110` (a körönkénti pumpa) és `0x007fb981` (a kilépés 1,2 s-os várakozása). Vagyis képernyő-frissítés; a részletek NINCS MEG (B10).
- **Automatikus léptetés: `0x00802630` (500 bájt, megerősített lépések).** (a) Zárolás: `vt+0x18`, ha `[this+0xc] == 0`, különben `EnterCriticalSection(this+0x28)`. (b) Ismételt belépés: `GetCurrentThreadId` (import `0xc40284`) összevetése a `[this+0x20]`-szal. Ha ugyanaz a szál, `[this+0x24]` nő, és nincs új zárolás. Különben `[this+0x20]` = a szál, `[this+0x24]` = 0. (c) `[this+0x3f4]` += 1; a lista végén `[this+0x3fd]` dönt a körforgásról (0 esetén a `0x802765` ág). (d) Feloldás (`vt+0x1c`, illetve `LeaveCriticalSection(this+0x28)`), de csak ha a számláló 0. (e) Hívja a `0x00802230`-at (NINCS MEG, B5). (f) Ismétel, amíg a `0x00802230` nem nullát ad, és `[this+0x3f0] >> 1` elem van.
- **Az időzítő (megerősített tény, nyitott kérdés).** ~~A `[0x520]` kezdőidőt a `0x007fb820` írja (38.2.23 §6), a `0x00802630` és a `0x00802060` nem.~~ **JAVÍTVA (38.2.25, 1. javítás):** a `0x00802060` is ír rá (`0x00802108`, sikeres léptetés után, `[0x518] = 0`-val); a `0x00802630` nem. Az összes író: `0x007faa2b`, `0x007fb8db`, `0x00801f30`, `0x00802108`, `0x008025cf`, `0x00802ad4`, `0x00802b33`, `0x00803150`. Ha a léptetés után nincs újraindítás, az `elapsed > pref` feltétel minden képkockán igaz lenne. Hogy ez hol áll le, NINCS MEG (B5).

**4. `0x0097b5e0` és a `startbutton` visszahívása**

- **`0x0097b5e0` (11 bájt, megerősített).** `add ecx, 0x28`; `push ecx`; `call dword ptr [0xc4055c]`; `ret`. A `[0xc4055c]` a `KERNEL32` `EnterCriticalSection` IAT-rekesze: a PE-importtáblában a `FirstThunk` rekesze ezen a virtuális címen van, és az ILT-bejegyzése ugyanazon az indexen a `EnterCriticalSection` nevet adja. Tehát a thunk `EnterCriticalSection(this+0x28)`, vagyis zárolás. A `0x00802630` ugyanezt a rekeszt hívja (`[0xc4055c]`), a `0x008001c0` pedig az `EnterCriticalSection`-t (a 7. futás szerint).
- **A visszahívás (megerősített, `0x007fdb0a`-`0x007fdb47`).** `call 0x007fb820` (a kilépési ág, 38.2.23 §6). Azután, ha `[this+0x2e8] = X` nem nulla: id = `[[this+0x3ec] + [this+0x3f8]·4]`, ha `[this+0x3f8] >= 0`, különben 0; `push id`; `push -1`; `call [vt(X)+0x18]` (ECX = X); a függvény `0xf4240` (1000000) értékkel tér vissza.
- **Ami NEM igazolt.** X osztálya NINCS MEG (38.2.23 B9), ezért a `vt(X)+0x18` célja sem igazolt. A `0x0097b5e0` csak akkor a célja, ha X vtáblája a OneUpUI-é. A visszahívás nem old fel: ebben az ágban nincs `vt+0x1c` vagy `LeaveCriticalSection` hívás. A `(-1, id)` argumentumokat a thunk nem olvassa; a verem takarítását a hívó végzi (`add esp, 0x14`, `0x007fdb44`).
- **Kimondva:** a `startbutton` visszahívás célja NINCS MEG. Két bináris tény van: (i) az aktuális elem azonosítóját adja át X-nek, (ii) X `vt+0x18` slotját hívja, és nem old fel. Ghidra-kör kell: X osztálya és `vt(X)+0x18` célja (B7).

**Bizonyítottsági fok (38.2.24)**

| állítás | bizonyíték | fok |
|---|---|---|
| 40 bájtos rekord, mezők +0/+8/+0x10/+0x18/+0x20 | `0x007fd0c0`: `0x007fd0e6`-`0x007fd10c` | megerősített |
| `0x009e6010` = hozzáfűzés | diszasszembly és dekompiláció, 236 bájt | megerősített |
| `0x0072df60` = `easing`, nem vtábla | diszasszembly `0x0072df60`-`0x0072e047` | megerősített |
| `easing` konstansok: C1 = 8,0, C2 = -1,0, K = 1 / g(8) | `0xc7ea10`, `0xcf3ed0`, `0xd337a8`, init `0x009e5ac0` | megerősített (a K számértéke futtatás nélkül) |
| E = exp | folytonosság y = 1-nél; a `0x00c29c6c` CRT-ugró | erős, nincs azonosítva (B8) |
| pos(t) és Δ | `0x009e5e70`, `0x009e5f90` | megerősített |
| `left`/`right` = +S/-S, dy = 2,0 | `0x007fd120`, `0x007fd150` | megerősített |
| nyíl: 0x25/0x26 +S, 0x27/0x28 -S | `0x008012bf`-`0x008012d9`, `0x008011b0`, `0x00801210` | megerősített |
| dy = 2,0 (nyíl), 4,0 (kattintás) | f32 `0xcf3a48`, `0xc7e4a4` | megerősített |
| S = P+0x30: olvasás | `0x008011b0`, `0x00801210`, `0x007fd770`, `0x007fc010` | olvasás megerősített, író NINCS MEG |
| O (P+0x20) és v (P+0x18) írói | `0x007fc045`, `0x007fc071`, `0x007fc07e`, `0x007fc09e` | megerősített |
| t_i = i·S + O, index-lineáris elrendezés | `0x007fc010`, `0x007fd8c0`, `0x007fd770` | megerősített |
| görbe `0x007fbab0` | 38.2.23 §4 (konstansok megerősítve) | erős |
| `0x007fbce0`: t_i = i/10000 - 1, 20000 minta | diszasszembly, f64 `0xcf42a8` = 10000 | megerősített |
| `0x00802060` ágai, `0x00801cb0` folyamata | diszasszembly `0x00802060`-`0x008020ed`, `0x00801cb0` | megerősített |
| léptetési jelzők (`[0x518]`, `[0x3c1]`) jelentése | az ágak megvannak, a jelentés nincs | feltételes / NINCS MEG |
| `[0xc4055c]` = `EnterCriticalSection` | PE-importtábla, `FirstThunk` | megerősített |
| `startbutton` célja | X osztálya nincs igazolva | nyitott |

**Nyitott kérdések mérlege (38.2.24)**

Lezárva (LEZÁRVA):
- (L1) `left`/`right` = +S/-S, dy = 2,0.
- (L2) Nyíl-billentyűk iránya (0x25/0x26 +S, 0x27/0x28 -S).
- (L3) 40 bájtos rekord, `0x009e6010` hozzáfűzés.
- (L4) `0x0072df60` `easing`, a konstansok és a K-init képlete.
- (L5) pos(t), Δ és a 0,02 s-os eltolás.
- (L6) Időtartam (2,0 s / 4,0 s) és az időegység (másodperc).
- (L7) O és v írói a `0x007fc010`-ban; a `0x007fc010` nem ír S-t.
- (L8) t_i = i·S + O, index-lineáris elrendezés.
- (L9) `0x007fbce0` keresés (t* = argmin |x - 0,666|).
- (L10) `0x00801cb0` és a `0x007fd8c0` AL-feltétele mint hívási lánc.
- (L11) `0x00802060` ágai.
- (L12) `0x0097b5e0` = `EnterCriticalSection(this+0x28)`; `[0xc4055c]` azonosítva.
- (L13) `0x00802630` zárolási, számlálós és léptetési lépései (a `0x00802230` és az időzítő kivételével).
- (L14) Kattintás `0x007fd770`: dy = 4,0.

Blokkolt (BLOKKOLT, Ghidra-kör vagy mérés kell):
- (B1) S = `[P+0x30]` írói. **RÉSZBEN LEZÁRVA (38.2.25, M7):** a konstruktor (`0x007fb9f0`) 0,05 állandót ír; a többi író osztálya NINCS MEG.
- (B2) P+0x50..0x7c írói. **RÉSZBEN LEZÁRVA (38.2.25, M8):** a konstruktor nullákat ír, a `0x007fbd90` a `runtime\bezier.txt` fájlból tölti; az osztályonkénti írók NINCS MEG.
- (B3) `A = [OneUp+0x388]` írói, és hogy dátum-e vagy index. **RÉSZBEN (38.2.25, R3):** az Időrend-tartományban nincs író; a tartalom NINCS MEG.
- ~~(B4) `0x005568e0`: az átlátszóság görbéje.~~ **LEZÁRVA (38.2.25, M1):** `pow(z, 1,5)`.
- (B5) `0x00802230` (a léptetés hatása) és az időzítő újraindítási helye (`[0x520]`). **RÉSZBEN LEZÁRVA (38.2.25, M6):** az újraindítás a `0x00802108`-ban van.
- (B6) `[0x3b8]`, `[0x3bb]`, `[0x3c1]`, `[0x3fd]`, `[0x518]` jelzők jelentése és írói.
- (B7) X = `[OneUp+0x2e8]` osztálya és `vt(X)+0x18` célja (`startbutton`).
- ~~(B8) E = `0x00c29c6c` azonosítása (exp?).~~ **LEZÁRVA (38.2.25, M2):** `exp`.
- ~~(B9) `0x009e5b20` nem nulla ága: a `0x009e5e70` ilyenkor a visszatérési egész értéket adja pozícióként (`fild`); ennek jelentése NINCS MEG.~~ **LEZÁRVA (38.2.25, M4):** a nem nulla érték a 4 (lefoglalási hiba); a `0x009e5e70` ezt 4,0 pozícióként adja vissza.
- (B10) `0x008018a0` nézetfrissítése, `0x00604480` rendezése és a `0x00801f50` rajzolási lépései. **RÉSZBEN (38.2.25, M5):** a `0x00604480` kulcs szerint (w, növekvő) rendez.
- (B11) v = P+0x18 többi írója (húzás vagy sodródás kezelője).
- ~~(B12) `0x007fbd90`: mit kezd a t*-gal.~~ **LEZÁRVA (38.2.25, M3):** a `P+0x8` és a `P+0x20` kapja.
- (B13) Mérés kell: a 2,0 s-os léptetés és a 0,02 s-os eltolás valós időzítése az eredeti Picasán (Colab-felmérő, nem Ghidra).

**Nyitott kérdések: 0 nyílt · 14 lezárva · 13 blokkolt · 0 hatókörön kívül · 0 csak nyitva.**

**Amit KIZÁRTAM**

- A `0x0072df60` nem vtábla.
- A `[0xc4055c]` nem import-név nélküli: `KERNEL32` `EnterCriticalSection`.
- A `left` nem -S: a `left` +S (ugyanígy a 38.2.23 L1 pontja).
- A kártya-elrendezés nem dátumsor-alapú a `t_i = i·S + O` képlet szerint: i szerint lineáris.
- A `0x009a51b0` nem sima időolvasó: a visszatérése (`QPC` - *arg) / `QPF`, az argumentum a kivonandó kezdőidő.
- A `0x007fc010` nem ír P+0x30-ra és P+0x50..0x7c-re.
- A `0x008001c0` nem ír P-mezőt.

**Következő Ghidra-címek**

- `Ghidra-kör kell: [P+0x30] (S, P = OneUp+0x2f8) írói, teljes .text pásztázás `paszta.py`-val [blokkolt]`
- `Ghidra-kör kell: P+0x50..0x7c (görbe-vezérlőpontok) írói [blokkolt]`
- `Ghidra-kör kell: [OneUp+0x388] (A) és [OneUp+0x38c] írói, dátum vagy index [blokkolt]`
- `Ghidra-kör kell: 0x005568e0 (átlátszóság görbéje, z = (1/w - 1)/9) [blokkolt]`
- `Ghidra-kör kell: 0x00c29c6c azonosítása (exp-e; CRT-ugrók: 0x00c2a190, 0x00c2a48e, 0x00c2a661) [blokkolt]`
- `Ghidra-kör kell: 0x00802230 (a léptetés hatása) és [OneUp+0x3f4] / [OneUp+0x3f8] szerepe [blokkolt]`
- `Ghidra-kör kell: [OneUp+0x518], [OneUp+0x3c1], [OneUp+0x3fd], [OneUp+0x520] írói (a léptetés feltétele és az időzítő újraindítása) [blokkolt]`
- Ghidra-kör kell: X = `[OneUp+0x2e8]` osztálya és `vt(X)+0x18` célja (`startbutton`) [blokkolt]
- `Ghidra-kör kell: 0x009e5b20 nem nulla visszatérési ága (a kiértékelő egész értéket ad vissza) [blokkolt]`
- `Ghidra-kör kell: 0x007fbd90 (t* felhasználása) [blokkolt]`
- `Ghidra-kör kell: P+0x18 (v) további írói (húzás vagy sodródás kezelője) [blokkolt]`
- `Ghidra-kör kell: 0x008018a0 nézetfrissítése (0x004133e0, 0x004b0190, 0x0097caf0), 0x00604480 rendezés, 0x00801f50 rajzolási lépései [blokkolt]`
- `Mérés kell (futásidő, nem Ghidra): a 2,0 s-os léptetés és a 0,02 s-os eltolás valós időzítése az eredeti Picasán (Colab-felmérő) [blokkolt]`

#### 38.2.25 Az Időrend bináris feltárása, 8. kör: átlátszóság, exp, t*, a visszaadott 4, a fókusz-csere, a mezőírók (#5401, 2026-10-21)

**Kérdés és hatókör.** Négy kérdés a `2026-10-21-idorend-8.txt` hat címéről, plusz a mezőírók teljes `.text`-pásztázása. (1) `0x005568e0` és `0x00c29c6c`: a kártyák átlátszóságának görbéje, és hogy az `exp`-e a CRT-ugró célja. (2) `0x007fbd90`: a t* felhasználása, és a `0x009e5b20` nem nulla ága. (3) `0x008018a0` és `0x00604480`: a fókuszált kártya cseréje, és a kártyák rendezése. (4) A `P+0x30` (S), a `P+0x50..0x7c` (vezérlőpontok) és az `A` tömb (`[OneUp+0x388]`, `[OneUp+0x38c]`) írói. Terméki kódot nem írtunk.

**Bemenet és módszer.** Diszasszembly a `pe_dis.cdis` (capstone) segítségével, konstansok az `f32` és `f64` olvasóval, függvényméretek és hívóélek az index `functions` és `xrefs` tábláiból. A mezőírók pásztázása darabolt (`paszta.utasitasok`), memória-kapuval fut az egész `.text`-en, 56 másodperc alatt. Csak a `[reg+disp]` memória-operandusokat nézi, a verem (`esp`) elérését kihagyja. Ghidra-futás nem volt. Az ideiglenes fájlok a `.bt/` alatt voltak, a kör végén törölve.

**Javítások a korábbi szakaszokban (a 38.2.24-ben is jelölve).**
1. **Téves volt (38.2.24 §3):** a `0x00802060` nem ír `[0x520]`-at. Pedig ír: a `0x00802108` (`fstp qword [esi+0x520]`) a `0x00802060` ágában van. Ha a léptetés (`0x00802630`) nullát ad vissza, a függvény a `0x008020f7`-`0x00802108` között új időpontot olvas, és azt `[0x520]`-ba írja, `[0x518] = 0` mellett. Az időzítő újraindítása tehát megvan (B5 része).
2. Lezárás, nem javítás: a 38.2.24 nyitott E-jelölése (`0x0040eac0`, `0x00c29c6c`) és az `f(z)` (`0x005568e0`) lezárult (1. kérdés).

**1. Átlátszóság és exp (`0x005568e0`, `0x00c29c6c`)**

- **`0x005568e0` (32 bájt, megerősített): kétargumentumos `pow` burkoló.** Két verem-argumentumot tölt az `x87` verembe (`fld dword [ebp+8]`, majd `fld dword [ebp+0xc]`), és a `0x00c0b410`-et hívja. A `0x00c0b410` (84 bájt) a `0x00c0b46d` magot hívja (78 bájt). A mag `fyl2x`-szel számol (y·log2 x), és a második (y) operandus előjelét és végtelen-ágát vizsgálja. Ez a CRT `pow` szokásos alakja.
- **A hívó: `z` és `1,5`.** A `0x007fc010` (hívás a `0x007fc40f`-nél) az első argumentumnak `z`-t, a másodiknak `1,5`-öt ad. A `z = max(0; (1/w - 1)/9)` a `0x007fc3c8`-`0x007fc3f1` között számolódik: `fdiv qword [0xcf3ef8]` (9,0), az `fldz`/`fcom` ág a negatív értéket nullára vágja. A kitevő `fld dword [0xcf3ec4]` = 1,5 (f32). Tehát **f(z) = z^1,5**.
- **Alfa (megerősített).** `0x007fc41f`-`0x007fc439`: `alfa = fistp(256 · (1 - f(z)))` (`fmul qword [0xcf39d8]` = 256,0), az eredmény a kártya-rekord `+0xa0` mezőjébe kerül (`mov [esi+0xa0], eax`). Ha w ≥ 1, akkor z = 0 és alfa = 256 (teljesen látható). Ha w = 0,1, akkor z = 1 és alfa = 0. A látható küszöb (`fcomp qword [0xc7dd30]` = 0,1, `0x007fc119`) egybeesik az alfa-nulla határral.
- **A w forrása (megerősített).** A görbe harmadik kimenete (`0x007fc10e`-`0x007fc111`: `[esp+0x30]`). Ugyanez a w adja a lépték-szorzót is (`lépték = w · Z`).
- **`0x00c29c6c` = `exp` (megerősített a konstansokból).**
  - `0x0040eac0` (29 bájt): f32 burkoló (`fld dword [ebp+8]`, `call 0x00c29c6c`, az eredmény visszatér).
  - `0x00c29c6c` (69 bájt): ha `[0xda1424] != 0`, és az `MXCSR` és az `x87` vezérlőszó kivétel-maszkja teljes, a gyors ág a `0x00c2a190` (24 bájt) → `0x00c2a1ae` (639 bájt, `SSE2` mag). Különben a `__cintrindisp1` (`0x00c2a48e`, 61 bájt) ág, amely a `0x00c2a51a`-t hívja (327 bájt, állapot- és hibaellenőrzés). A `0x00c2a48e` nem tartalmaz számítást.
  - A mag konstansai: `0xcf5a40` = 1,5·2^52 (kerekítő-tolóérték); `0xcf5a60` = 92,33248261689366 (= 64/ln 2); `0xcf5a70` = 0,010830424696223417 (= ln 2/64, felső rész); `0xcf5a80` = 2,572804622327669e-14 (ln 2/64, alsó rész); `0xcf5a90`, `0xcf5a98`, `0xcf5aa0`, `0xcf5aa8`: 0,008332168, 0,166666667, 0,041666721 és 0,4999999999995663, vagyis a Taylor-sor együtthatói 1/120, 1/6, 1/24 és 1/2 közelében.
  - Ezek `exp(x)` = 2^(k/64)·e^r redukcióra utalnak. A `0x00c29c6c` ezért `exp`.

**2. t*, a vezérlőpontok forrása, és a nem nulla visszatérés**

- **`0x007fbd90` (330 bájt, megerősített).** Hívója a `0x007fb9f0` konstruktor (`0x007fbaa2`). Megnyitja a `runtime\bezier.txt` fájlt (`0x0099d0c0`, a `ytIO.cpp` fájlkezelője; a sztring a függvény sztring-hivatkozása). Ha a megnyitás sikerül, 4-szer olvas `"%f %f %f\n"` alakban (`fscanf`): X_k = `P+0x50+12k`, Y_k = `P+0x54+12k`, W_k = `P+0x58+12k`, k = 0..3. Ezután `t* = 0x007fbce0()`, és `P+0x8 = t*` (f32), `P+0x20 = t*` (f64). Ha a megnyitás nem sikerül, az olvasás és a t*-beállítás kimarad; a vezérlőpontok a konstruktor nulláin maradnak.
- **t* definíciója (megerősített, `0x007fbce0`, 166 bájt).** `t_i = i/10000 - 1` (i = 0..19999, `cmp esi, 0x4e20`; az 1,0 a `0xc7e328`-ban van). Minden t_i-re hívja a `0x007fbab0` görbét, és `|x(t_i) - 0,666|` (`0xcf4860`) minimumát keresi. A kezdő legjobb távolság 1 000 000 (`0xcf3dc0`). A szigorú `<` miatt az első minimum nyer. Visszatérés: t* (f32).
- **A t* felhasználása (megerősített).** t* az a görbe-paraméter, ahol a kártya x-koordinátája a legközelebb van 0,666-hoz. `P+0x20` (O, a kártya-eltolás) kezdőértéke t*. `P+0x8` a felső korlát: `0x007fc071`, `O ← [P+8]`; az alsó korlát `0x007fc07e`: `O ← [P+8] - (n-1)·S`. Ez a 38.2.24 képlete.
- **A `0x009e5b20` nem nulla ága (megerősített, 753 bájt).** A függvény a rekord-listát tömöríti. Ha nincs mit tömöríteni (`t < rekord[0].end`, vagy nincs lejárt rekord), 0-val tér vissza (`0x009e5b52`, `0x009e5df1`). Ha van lejárt rekord, új tömbbe másolja azokat, ahol `t < end`, és mindig az utolsót; a sikeres másolás is 0-val tér vissza. A **nem nulla** érték csak a 4, a `mov eax, 4` (`0x009e5d57`, `0x009e5d70`), vagyis a lefoglalás-hiba ága.
  - **A hívó `0x009e5e70` (285 bájt)** (hívás a `0x009e5ea0`-nál) a nem nulla értéket `fild dword [esp+0xc]`-vel veszi át (`0x009e5ead`), és **4,0-t ad vissza pozícióként** (`ret 8`, `0x009e5eb6`). A pozíció-számítás ilyenkor nem fut le. Ez a bináris viselkedése; hogy szándékos-e, NINCS MEG.

**3. A fókuszált kártya cseréje (`0x008018a0`, `0x00604480`)**

- **`0x008018a0` (1029 bájt, megerősített).** Ha `[OneUp+0x50c]` már egyezik az EAX-ban kapott értékkel, visszatér. Különben:
  1. `[OneUp+0x50c] = EAX` (`0x008018b8`): a kijelölt kártya indexe (PONTOSÍTVA, 38.2.35 §5 és 38.2.36 §7: az „index” megnevezés nem igazolt, a kulcs típusa NINCS MEG). A hívók: `0x00801ce5` (a `0x00801cb0`-ból; EAX = `[OneUp+0x510]`, a `0x007fd8c0` kimenete), `0x007fe33e`, `0x00803953`.
  2. `0x004133e0` (→ `0x0097adb0`, 86 bájt), majd `0x004b0190(új index)` (499 bájt; zárolás, két vtábla-hívás, `call eax` és `call edx`; a célok NINCS MEG).
  3. A régi `[OneUp+0x3ec]` lista felszabadítása (`0x0097caf0`), majd új lista építése a forrás-listából (`local_64`), a `local_5c` jelzőivel szűrve. Az eredmény a `[OneUp+0x3ec]` mutató és a `[OneUp+0x3f0] >> 1` darab (`0x008018fa`-`0x00801bc4`).
  4. `[OneUp+0x51a] = 1` (`0x00801c19`): a frissítés-jelző. Olvasója a `0x007fb560` (a `0x007fb540` függvényben).
  5. `0x008014d0` (967 bájt): négyszer `_rand`-ot hív, a `[OneUp+0x3ec]` listát olvassa (`0x00801570`), és a `0x00803c10`, `0x007fa5b0`, `0x009a8bc0` függvényeket hívja.
  6. `0x00413490` (139 bájt): `CloseHandle` és `DeleteCriticalSection` hívás (felszabadító ág).
- **Mit vált a kártyacsere (kép, gyűjtemény, dátumfelirat).** NINCS MEG. A bináris állapot: az index (`[OneUp+0x50c]`) és a lista (`[OneUp+0x3ec]`) átíródik, a frissítés-jelző beáll, és a `0x008014d0` lefut. Az index olvasói: `0x008018a0` (összehasonlítás) és `0x00801cf0` (`0x00801d8e`: kimeneti mutatón adja vissza; hívója NINCS MEG). Hogy a három látható rész közül melyiket frissíti, a `0x008014d0` és a `0x004b0190` célja dönti el.
- **`0x00604480` (464 bájt, megerősített): helyben, stabil, alulról felfelé összefésülő rendezés.** A `0x00604660` (135 bájt) egy menetnyi összefésülést végzi. A rendezett tömb a `[P+0x80]` (darab: `[P+0x84] >> 1`), a kulcs a `0x007fc010` helyi f32 tömbje (`[esp+0x20]`, a w-értékek, `0x007fc253`). Növekvő sorrend: a kisebb kulcs kerül elé, az egyenlők megtartják a sorrendjüket (`key[a] <= key[b]`). Visszatérés: 0, lefoglalási hibánál 4. A hívó `0x007fc48a` a visszatérést nem nézi; a kulcs-tömböt utána szabadítja fel (`0x007fc4a0`-`0x007fc4a9`).
  - A 11 hívó közül az Időrend-tartományban csak a `0x007fc48a` van.
  - A rajzoló ciklus iránya (`0x00801f50`) nincs olvasva: a rajzolási sorrend NINCS MEG.

**4. Mezőírók: teljes `.text`-pásztázás**

A pásztázás a `[reg+disp]` alakokat látja. Az Időrend-tartomány `0x007f0000`-`0x0080ffff`. A mutatón át írt mezők (`fscanf` argumentuma, `rep movsd`, `memcpy`) nem látszanak.

| mező | írók a tartományban | megállapítás |
|---|---|---|
| S = `P+0x30` (f64) | `0x007fba9a` (`0x007fb9f0`, konstruktor: `fstp qword [esi+0x30]`), továbbá `0x00809a26` (`0x00809a10`), `0x00809cb3` (`0x00809c50`) és `0x00809037` (`0x00808fc0`, `[reg+0x328]`) | a konstruktor értéke `fld qword [0xcf4e30]` = 0,04999999888241291 (a 0,05 f32-es kerekítése). S tehát állandó, nem számolt. A három másik író osztálya NINCS MEG. **JAVÍTVA (38.2.26, 4. szakasz):** a `0x00809a26` ideiglenes objektumot ír (nem P); a `0x00809037` a gazda `+0x328` mezőjét írja, a gazda a hívó `this`-e, és nincs igazolva, hogy OneUp; a `0x00809cb3` nyitott. |
| vezérlőpontok `P+0x50..0x7c` | konstruktor `0x007fb9f0` (`0x007fba06`-`0x007fba28`): nullák (`fldz`). Betöltés: `0x007fbd90` (`fscanf`, mutatón át). Más osztályok ugyanezeket a displacementeket írják (például `0x007fa3d0`, `0x007f7250`, `0x0080f380`). | forrás: a `runtime\bezier.txt` (4 sor, 3 szám). Az osztályonkénti írók NINCS MEG. |
| `A` = `[OneUp+0x388]`, `[OneUp+0x38c]` | az Időrend-tartományban **nincs író**. Olvasók: `0x007fdd00` (`0x007fdd7b`-`0x007fdda3`) és `0x007ffc90` (`0x007ffd6d`-`0x007ffe57`). A tartományon kívül mintegy 60 író, köztük `0x00818eb0` (`0x00818ed1`-`0x00818f08`). | a 0x388 mutató és a 0x38c darab (×2 jelzővel) egy tömböt ír le. A `0x00818eb0` vtáblája `0xcbdde4`, a `OneUpUI` vtáblája `0xcbd5c4`: más osztály. A tartalom dátum vagy index: **NINCS MEG**. Hívója: `0x006214e0`, amely maga is ír `[ebp+0x388]`-at (`0x00621b03`, `0x00621b31`, `0x00621ba9`). **JAVÍTVA (38.2.26, 2. szakasz):** a `0x00818eb0` írásai a friss `ytFlyingNode` objektumon vannak (`0x0062177b`: `mov edi, eax`), nem a OneUp-on; a (mutató, darab) pár nem létezik. A `0x006214e0` a `[p+0x388]`-ba a kártya SORSZÁMÁT írja (p osztálya NINCS MEG), a `[+0x38c]`-be nem ír. |

**Nyitott kérdések mérlege (38.2.25)**

Lezárva:
- (M1) `0x005568e0` = `pow` (z^1,5) (B4).
- (M2) `0x0040eac0` = `exp`; a `0x00c29c6c` `exp`-ugró (B8).
- (M3) t* definíciója és felhasználása: `P+0x8`, `P+0x20` (B12).
- (M4) `0x009e5b20` nem nulla ága: 4, és a `0x009e5e70` 4,0-t ad (B9).
- (M5) A `0x00604480` rendezés kulcsa w, növekvő, helyben (B10 része).
- (M6) `[0x520]` írói, és az újraindítás helye: `0x00802108` (B5 része).
- (M7) S = `0x007fb9f0` konstansa: 0,05 (B1 része).
- (M8) A vezérlőpontok forrása: a `runtime\bezier.txt` fájl (B2 része).

Részben:
- (R1) B1: S három másik írójának (`0x00809a26`, `0x00809cb3`, `0x00809037`) osztálya. **RÉSZBEN (38.2.26, 4. szakasz):** a `0x00809a26` ideiglenes objektum, nem P; a `0x00809037` gazdájának osztálya NINCS MEG.
- (R2) B2: a `P+0x50..0x7c` írók osztályai.
- (R3) B3: az A-író (`0x00818eb0`) és a forrás (`0x006214e0`) ismert; a tartalom nincs. **LEZÁRVA (38.2.26, 2. szakasz):** a tartalom sorszám; a `0x00818eb0` `ytFlyingNode`-ot ír.

Blokkolt:
- (B3) Az A tartalma: dátum vagy index.
- (B6) `[0x3b8]`, `[0x3bb]`, `[0x3c1]`, `[0x3fd]`, `[0x518]` jelentése. Írók a pásztázás szerint: `[0x3c1]` és `[0x3fd]` csak a `0x007fa7f0` konstruktorban, `[0x3b8]` a `0x007fa7f0`, `0x007fb820`, `0x007fda00`, `0x007fde80` és `0x00803110` függvényekben.
- (B7) X osztálya és `vt(X)+0x18` célja (`startbutton`).
- (B10) `0x008014d0`, `0x004b0190` és a `0x00801f50` rajzolási lépései.
- (B11) v = P+0x18 többi írója. Ebben a körben nincs vizsgálva.
- (B13) Mérés kell (futásidő).
- (N1) A fókusz-csere fogyasztója: kép, gyűjtemény vagy dátumfelirat. NINCS MEG. **RÉSZBEN (38.2.26, 1. szakasz):** a `[OneUp+0x2ec]` rekord-tömböt írja (0xf8 bájt); a három látható rész azonosítása NINCS MEG.

**Nyitott kérdések: 0 nyílt · 8 lezárva · 3 részben · 7 blokkolt · 0 hatókörön kívül · 0 csak nyitva.**

**Amit KIZÁRTAM**

- A `0x00c29c6c` nem `log` és nem `pow`: a konstansok (64/ln 2, ln 2/64, a polinom) `exp`-re utalnak.
- A `0x005568e0` nem `exp(z)`: a második argumentum a kitevő (1,5).
- A `0x009e5b20` nem nulla ága nem számít pozíciót: a visszatérési értéke a lefoglalási hibakód (4).
- Az S (`P+0x30`) nem a `0x007fc010`-ban íródik, és nem számolt érték: a konstruktor állandója.
- A `[OneUp+0x388]` nem íródik az Időrend-tartományban. A mutatón át írt eseteket nem zártam ki.

**Következő Ghidra-címek**

- `Ghidra-kör kell: 0x008014d0 - mit rajzol vagy frissít a [OneUp+0x3ec] listából (a fókusz-csere kimenete: kép, gyűjtemény vagy dátumfelirat) [blokkoló]`
- `Ghidra-kör kell: 0x004b0190 - a két vtábla-hívás (call eax, call edx) célja, és a forrás-lista (local_64, local_5c) eredete [blokkoló]`
- ~~`Ghidra-kör kell: 0x006214e0 - a 0x00818eb0-nek átadott (mutató, darab) pár forrása, vagyis mi az [OneUp+0x388]/[0x38c] tartalma (dátum vagy index) [blokkoló]`~~ **JAVÍTVA (38.2.26, 2. szakasz):** nincs (mutató, darab) pár; `[p+0x388]` a sorszám. Hátra van: `p` osztálya (38.2.26 következő Ghidra-címei).
- ~~`Ghidra-kör kell: 0x00818eb0 (vtábla 0xcbdde4) - melyik osztály, és azonos-e az OneUp objektummal [blokkoló]`~~ **LEZÁRVA (38.2.26, 2. szakasz):** `ytFlyingNode`, nem a OneUp.
- `Ghidra-kör kell: 0x00808fc0, 0x00809a10, 0x00809c50 - melyik osztály írja a P+0x30 és a P+0x50..0x6d mezőit [blokkoló]` **RÉSZBEN (38.2.26, 4. szakasz):** a `0x00809a10` ideiglenes objektumot ír (nem P); a `0x00808fc0` gazdája a hívó `this`-e; a `0x00809c50` nyitott.
- `Ghidra-kör kell: 0x007fb9f0 hívója (0x007fa7f0) - mi állítja be az esi-t, vagyis melyik objektum a P [nem blokkolja a fő utat]`
- `Ghidra-kör kell: 0x007f9a40 és 0x00802e20 - a P+0x58..0x80 írásainak forrás- és cél-objektuma [nem blokkolja a fő utat]`
- `Ghidra-kör kell: 0x00802630 visszatérési értékének jelentése, és az időzítő-újraindítás (0x00802108) feltétele [nem blokkolja a fő utat]`
- `Ghidra-kör kell: 0x0099d0c0 és 0x00980ec0 - a runtime\bezier.txt útvonal alap-könyvtára [nem blokkolja a fő utat]`

#### 38.2.26 Az Időrend bináris feltárása, 9. kör: a fókuszcsere, a `0x388` tartalma, a kártyák forrása, az S-írók (#5401, 2026-10-21)

**Kérdés és hatókör.** Négy kérdés a `2026-10-21-idorend-9.txt` nyolc címéről. (1) `0x008014d0` és `0x004b0190`: mi frissül a `[OneUp+0x3ec]` listából a fókuszcsere után, és mire kellenek a négy `_rand`-hívás. (2) `0x006214e0` és `0x00818eb0`: mi van az `[OneUp+0x388]` és a `[0x38c]` mezőben, és honnan jön a (mutató, darab) pár. (3) `0x00802e20` és `0x007f9a40`: hogyan épülnek a kártyák, melyik gyűjteményből és milyen sorrendben. (4) `0x00808fc0` és `0x00809a10`: az S (`P+0x30`) további írói, és melyik osztály. Terméki kódot nem írtunk.

**Módszer.** A Ghidra-C-kódot és a hívóéleket a bemeneti fájl adja. A diszasszembly a `pe_dis.cdis` (capstone) segítségével készült, függvényenként: a capstone az első érvénytelen bájtnál megáll: a `0x007f0000`-tól indított egyben olvasás 5326 utasítás után leállt, ezért függvényenként olvastunk. Konstansok az `f32`/`f64` olvasóval. A függvénylista és a hívóélek az index `functions` és `xrefs` tábláiból jöttek. Ghidra-futás nem volt. Ideiglenes fájlok a `.bt/` alatt voltak, a kör végén törölve.

**Javítások a korábbi szakaszokban** (a 38.2.25-ben is jelölve):
1. **A `[OneUp+0x388]` írója nem a `0x00818eb0`.** A 38.2.25 §4 szerint a `0x00818eb0` írja a `[OneUp+0x388]` és `[0x38c]` mezőket. Ez téves. A `0x006214e0` a `0x0062177b`-ben (`mov edi, eax`) a `0x0097c5d0(0x398)` friss blokkját teszi az `EDI`-be, és a `0x0062178d`-es hívás ehhez a blokkhoz tartozik. A `0x00818eb0` mezőit a friss `ytFlyingNode` kapja (vtábla `0xcbdde4`).
2. **Az `A` tömb (mutató, darab) párja nem igazolt.** A 38.2.25 ezt feltételezte. Ezen az úton nincs ilyen pár (2. szakasz).
3. **S-írók.** A 38.2.25 §4 három S-írót sorolt fel: `0x00809a26`, `0x00809037`, `0x00809cb3`. A `0x00809a26` ideiglenes objektumot ír, nem P-t. A `0x00809037` a gazda `+0x328` mezőjét írja (4. szakasz). A `0x00809cb3` nyitott.

**1. A fókuszcsere: `0x008014d0`, `0x004b0190`**

Hívóélek: a `0x008014d0` hívója a `0x008018a0` (`0x00801c95`) és a `0x008037e0` (`0x008039d1`). A `0x008018a0` a fókuszcsere: beállítja az `[OneUp+0x50c]` kulcsot (**PONTOSÍTVA, 38.2.35 §5:** nem igazolt, hogy index), újraépíti a `[OneUp+0x3ec]` listát (írások `0x00801907`-`0x00801b9c`), majd `[OneUp+0x51a] = 1`-et állít (`0x00801c19`). A `0x008014d0` ez után fut.

- **A `[OneUp+0x3ec]` lista nem frissül a `0x008014d0`-ban.** A függvény csak olvassa (`0x00801570`: `mov esi, [edi+0x3ec]`). A lista írói: a `0x008018a0` (újraépítés) és a `0x007fb5a0`. A `0x007fb5a0` a törlési út része: a `0x007fae90` hívja, ami egy törlő metódus (adat-hivatkozás: `0x00cbd66c`). Nullázza a `[+0x3ec]`, `[+0x2ec]` mezőket, a `[+0x2f0]` jelzőit maszkolja, és a `0x0097d370`-et hívja. Ezért nem frissítő.
- **Az elemek egész azonosítók.** A `0x008018a0` C-kódjában a `[OneUp+0x3ec]` elemei `uint` értékek, és a szűrő bájt-tömbje (`local_5c`) ugyanezzel az azonosítóval indexel. Az elem tehát nem objektum-mutató. Hogy ez kép-, gyűjtemény- vagy dátumfelirat-azonosító, NINCS MEG: a `local_64` forrása a `0x008018a0` C-kódjában nem látszik.
- **Mit csinál a `0x008014d0`.** Minden elemre (`0x00801523`-`0x0080157a`) hívja az `[OneUp+0x2e4]` objektum vtábla-első metódusát: `(azonosító, &info, 1)`. Az `info` egy 0x28 bájtos verem-struktúra (**JAVÍTVA, 38.2.38 §6**: a korábbi 0x24 téves volt). Ezután egy 0xf8 bájtos kártya-rekordot állít össze a `0x007fa5b0` konstruktorral (az első dword `-1`, `+0xa0 = 0x100`, `+0xa4 = 1,0`, `+0xc8 = 1`), beírja a négy `_rand`-értéket, és a `0x00803b50` másolóval a `[OneUp+0x2ec]` tömb végére teszi (`0x008017f3`). A darabszám `[OneUp+0x2f0] >> 1`. Ha a `[+0x2f0]` bit 0 jelzője be van állítva, nincs új elem.
- **Ami frissül:** a `[OneUp+0x2ec]` rekord-tömb (0xf8 bájtos rekordok). A `[OneUp+0x3ec]` nem. Hogy a három látható rész (kép, gyűjtemény, dátumfelirat) közül melyiket frissíti, NINCS MEG: a `[OneUp+0x2e4]` objektum osztálya és a metódusa nincs megmérve. Az `[OneUp+0x2e4]` értéke a `0x007fa7f0` konstruktorban a C-kód szerint `*(in_EAX+0x10)`, ahol az `in_EAX` a `0x008037e0` paraméter-struktúrája (`0x00803920`: `mov eax, edi`, `call 0x7fa7f0`).
- **A négy `_rand`-hívás.** Minden kártya-rekordhoz két kezdő pozíció és két elmozdulás-tényező jön. Az `r` a `_rand` értéke `[0,1)`-re normálva. A rekord-mezők a `0x803b50` másolásának sorrendjében (`+0xcc..+0xd8`):

  | rekord-mező | képlet | tartomány |
  |---|---|---|
  | `+0xcc` | r(D) - 0,5 | [-0,5; 0,5) |
  | `+0xd0` | r(C) - 0,5 | [-0,5; 0,5) |
  | `+0xd4` | (r(B) - 0,5) · 0,15 | [-0,075; 0,075) |
  | `+0xd8` | (-r(A) + e) · 0,15, ahol e = 0,5, ha `[OneUp+0x3bc]` nem nulla, különben 0 | legfeljebb 0,15 abszolút értékben |

  Az `r(A)`-`r(D)` a négy `_rand`-hívás sorrendje. A `[OneUp+0x3bc]` jelzőt a függvény olvassa (`0x008015cb`), de a jelentése NINCS MEG. A `0x007fe600` írja a `+0xcc` és `+0xd0` mezőket: `+0xcc` nő a `+0xd4` tényezővel, `+0xd0` a `+0xd8` tényezővel egy léptetési lépésben (`0x007fe650`-`0x007fe6fc`), és visszafogás (`fcom`) követi. Vagyis a négy érték közül kettő a kezdő pozíció, kettő a léptetésenkénti elmozdulás. **JAVÍTVA (38.2.27 §2):** az `a` és `b` tényezők a kártya sebességei, és a `0x007fe600` minden lépésben kis véletlen értékkel módosítja őket. A visszafogás 0 és 1 közé von vissza.
- **`0x004b0190`.** Az `in_EAX` `+0xc4` objektumát zárolja (kritikus szakasz, vagy vtábla-zárolás a `+0x74` jelzőtől függően). Majd az `+0x48` objektum vtábla `+0x2c` metódusát hívja az új indexszel (`param_1`). Ezután a hívó `ESI` objektumába (`unaff_ESI`) tizennyolc mutatót köt: `+0x68 = in_EAX+0x29c`, `+0xa4 = in_EAX+0x2a4`, és hat pár az `[in_EAX+0x2a8]`, `[+0x2ac]`, `[+0x2b0]`, `[+0x2b8]`, `[+0x2b4]`, `[+0x2bc]` objektumok `+0xcc`/`+0xd4` mezőire (`+0x6c..+0x7c`, `+0x84` és `+0xa0..+0xb4`, `+0xbc`), továbbá két pár az `[+0x2c8]` és `[+0x2d0]` objektumok `+4`/`+0x10` mezőire. Visszatérés 0, vagy -1, ha az `unaff_ESI+0x5c` vagy `+0x64` nulla. A függvény nem ír sem `[OneUp+0x3ec]`-be, sem rekord-tömbbe. A kötés célja és az `in_EAX` osztálya NINCS MEG.

**2. `[OneUp+0x388]` és `[0x38c]`; a (mutató, darab) pár (`0x006214e0`, `0x00818eb0`)**

- **A `0x006214e0` első paramétere (`p`).** A verem első paramétere (`0x006214e8`: `mov ebp, [esp+0x174]`). A `0x00623d49` hívóban az `EBX`. A `0x0061edc5` hívóban a vizsgált ablakban nem látszik. **JAVÍTVA (38.2.27 §3):** a `p` osztálya `MakeMoviePanel`, nem OneUp. A korábbi állítás téves volt.
- **`p+0x388` a kiválasztott kártya SORSZÁMA.** **JAVÍTVA (38.2.27 §3):** a `p` `MakeMoviePanel`, így ez a film-sáv (`filmstrip`) kiválasztott elemének sorszáma, nem az Időrend-kártyáé. Bizonyítékok: (a) írások: `0x00621b03` (`mov [ebp+0x388], edi`), `0x00621b31` (`mov [ebp+0x388], eax`), `0x00621ba9` (`-1`, ha nincs elem). (b) A kód a darabszámhoz köti: `FUN_00610b90()` (az elemek száma) mínusz egy a felső korlát (a bemeneti C-kód 636-651. sora). (c) Az olvasott forrás, `[p+0x298]+0x380` (`0x0062156a`), szintén index. Dátum-művelet a függvényben nincs.
- **`p+0x38c` a `0x006214e0`-ban nem íródik** (asm: nulla találat). A OneUp kódtartományában (`0x007f0000`-`0x0080ffff`) sincs író, csak olvasó (`0x007fdd00`, `0x007ffc90`). A (mutató, darab) pár hipotézise ezért nem igazolt.
- **A `0x00818eb0` bemenete két `f32` (x, y).** A `0x006214e0` a `&local_164` címet adja (`0x00621784`-`0x00621788`: `lea edx, [esp+0x14]`, `push edx`). A `0x00818eb0` az `EDI`-n át a friss blokkba írja: `[+0x388] = x`, `[+0x38c] = y`, `[+0x390] = x`, `[+0x394] = y` (a C-kódban `unaff_EDI[0xe2..0xe5]`). A kezdő és a cél pont tehát egyezik. Utána `0x009debd0(x, y)`. A friss blokk `ytFlyingNode`, vtábla `0xcbdde4` (rtti-index).
- **Dátumcsúszka: NINCS MEG.** A `0x006214e0`-ban nincs csúszka-kezelés (a csúszka a `0x00a52890`-ben van, 38.2.6). Hogy a `[+0x388]` sorszám hogyan képezi le a csúszkát, nincs megmérve.

**3. Az Időrend építése: `0x00802e20`, `0x007f9a40`**

**JAVÍTVA (38.2.29 §2):** a `0x007f9a40` nem Időrend-kártyát épít, hanem csillag-jelző képelemet (`stars/yes` vagy `stars/no` képpel), és ezt a `0x005e81e0` hozza létre. Az Időrend-kártyák (0xf8 bájtos rekordok) a fenti 1. pont szerint a `0x008014d0`-ból jönnek. A címet követő leírás (a konstruktor és a véletlen paraméterek) a csillag-jelző képelemre vonatkozik.

- **`0x007f9a40` a kártya-objektum konstruktora.** A hívó `0x005e81e0`: `0x005e8437`-nél `0x0097c5d0(0x37c)` foglal, `0x005e8469`-nél `mov esi, eax`, `0x005e846b`-nél `call 0x7f9a40`. A vtábla `ytAnimSprite::vftable` (`0x00cbd2a4`). Az `EDI` a hívó verem-struktúrája (`lea edi, [esp+0x28]`, `0x005e8465`), NEM a `OneUp+0x2f8` P.
- **Kezdő pozíció.** `[+0x144] = (EDI+8) · 0,5`, `[+0x148] = (EDI+0xc) · 0,5`, az előjel-javítás `2^32`-vel (`0xcf3ac0`). Ez minden kártyán ugyanaz: a közös kiindulópont a hívó struktúrájából jön.
- **A `DAT_00d676c8` számláló az ÉLŐ kártyák száma, nem sorszám.** `+ 1` a `0x007f9a62`-ben (C-kód), `- 1` a `0x007fa212`-ben (a `ytAnimSprite` `0x007f9cd0` metódusában). Olvasói: `0x007f9b16`, `0x007f9b42`. Az index xrefs-ében nincs adat-hivatkozás, ezért a teljes `.text` pásztázásból jön (függvényenként).
- **Véletlen paraméterek** (`r` a `[0,1)`-re normált véletlen, `n` a számláló a `+1` után): `[+0x35c] = (r-1) · 0,4 + 0,3`, `[+0x360] = ((r-1) - 0,5) · 0,3`, `[+0x364]` = a `[1,2)` tartományú érték, `[+0x368] = (r-1) - 0,5`, `[+0x36c] = n · (r-1) · 0,03`, `[+0x370] = 2π · (r-1)`, `[+0x374] = (r-1) · 0,1`. A `[+0x354] = -1,0` (f32, `0xcf3ed0`), a `[+0x358]` a hívott `param_2` (forrás-objektum).
- **Gyanú, nem bizonyított.** A `0x005e8443`-`0x005e8464` sorban a hívó az f32 értéket (1,0, vagy `0xcf3a70` = 0,6) a verem első paraméterébe teszi. A hívó a `[esp+0x50]`-et bájtként ellenőrzi, majd a paraméter-összeállításkor dword-ként olvassa, ami a Ghidra C-kódjával nem egyeztethető össze biztosan. A `0x007f9a40` a paramétert bájtként tárolja (`[ESI+0xde]`). Hogy ez tényleges típuseltérés-e, NINCS MEG.
- **A sorrend.** *(JAVÍTVA, 38.2.28 §2: nincs 0xc8 bájtos ciklus. A `0x005e8283` `add esi, 0xc8` vtábla-eltolás, nem rekordméret. A kártya-objektum hívásonként legfeljebb egyszer készül, ciklus nélkül.)* A kártyák létrehozási sorrendje a `0x005e81e0` hívásainak sorrendje. A kártya-hívás a `0x005e8330`-`0x005e84d7` blokkban van, a belépés feltételei között szerepel a `0x009c2fc0` visszatérése (`[eax+0x20c]`, `[eax+0x213]` jelzők). A két szakasz viszonya és a megjelenítési sorrend (a `0x009df290` hívás után) NINCS MEG.
- **Gyűjtemény (album, mappa): NINCS MEG.** A 38.2.18 szerinti `CThumbUI+0x2c0` kollekciós állítást ebben a körben nem mértük újra.
- **`0x00802e20`.** Ha `DAT_00d67914` nem nulla, az aktív objektum a `0x009c2fc0` visszatérése, különben nulla. A `0x00c07db2` argumentumai RTTI-típusleírók (`ytDrawNode`, `ytBicubicNode`), ez dinamikus cast. Sikeres cast után nullázza a `+0x36c..+0x378` és `+0x358` mezőket, a `+8` mezőt `|= 7`-tel jelöli, és meghívja a `0x00a54b70(param_1, 1, 1, 0, 1, -1, -1, -1, -1)`-et. A cél objektum `ytBicubicNode`; ebben a függvényben nincs sorrendi művelet. Hívói: `0x008036b9` és `0x00803723` (`0x008032e0`). A `param_1` tartalma NINCS MEG.

**4. S (`P+0x30`) írói (`0x00808fc0`, `0x00809a10`)**

- **P és S.** `P = OneUp+0x2f8`: a `0x007fa7f0` `lea esi, [ebp+0x2f8]` (`0x007fa84a`), majd `call 0x007fb9f0` (`0x007fa850`). Így `S = P+0x30 = OneUp+0x328`.
- **`0x00809a10`** (`ytUIEvent` konstruktor, vtábla `ytUIEvent::vftable`). A `+0x30` és `+0x34` írás (`0x00809a26`, `0x00809a29`) az `EAX` objektumba megy. A két hívó ideiglenes objektumot ad: `0x0080c24a` előtt `lea eax, [esp+0x18]` (`0x0080c241`), `0x00a54089` előtt `lea eax, [esp+0x98]` (`0x00a5407f`). **Nem S-író.**
- **`0x00808fc0`** (`CAutoCompleteListBox` konstruktor). A `0x00809037` írás `[edx+0x328]`-ba megy, ahol `edx = [this+0x1c]` (a gazda), és az érték `[this+0x24]` (ha nulla, `0x18`, `0x00809028`). A gazda a hívó saját `this`-e: `0x0040e7b0` (`mov eax, ebx`, `0x0040e862`), `0x0060e260` (`mov eax, esi`, `0x0060e27e`), `0x00640670` (`mov eax, ebp`, `0x00640b4d`), `0x006464a0` (`mov eax, ebp`, `0x0064698e`), `0x0064a680` (`mov eax, ebp`, `0x0064aae2`). Egyik hívó sincs a `0x007f0000`-`0x0080ffff` tartományban. S-írás csak akkor volna, ha a gazda OneUp, és ezt nem láttuk. **Nem igazolt S-író.**
- **`0x00809cb3`** (`0x00809c50`): NINCS MEG, ebben a körben nem vizsgáltuk.
- **Osztály összefoglalva:** a P+0x30 írója a P konstruktora (`0x007fb9f0`, 0,05). A többi mért író közül a `0x00809a10` nem P-író. A `0x00808fc0` nem igazoltan P-író. A `0x00809c50`-t nem néztük meg.

**Mérleg (38.2.26).** Nyitott kérdések: 1 nyílt · 5 lezárva · 4 blokkolt · 0 hatókörön kívül · 5 részben.

- lezárva: a `0x008014d0` nem írja a `[OneUp+0x3ec]`-et; `[+0x388]` sorszám; nincs (mutató, darab) pár; `P = OneUp+0x2f8`, `S = OneUp+0x328`; a `0x00809a10` nem S-író.
- részben: a négy `_rand` szerepe; a `0x004b0190` kötései; a sorrend (a hívási sorrend igazolt, a forrás nem); a `0x00802e20` szerepe; a `0x00808fc0` gazdája.
- blokkolt: a rekord-elem típusa (kép, gyűjtemény, dátumfelirat); a `p` osztálya; a dátumcsúszka; a gyűjtemény forrása.
- nyílt: a `0x00809c50` (S harmadik írója).

**Amit KIZÁRTAM**
- A `[OneUp+0x388]` sorszám, nem (mutató, darab) pár. *(JAVÍTVA 38.2.27: a `p+0x388` a `MakeMoviePanel` film-sávjáé, nem a OneUp-é.)*
- A `0x00818eb0` nem a OneUp mezőit írja, hanem a friss `ytFlyingNode`-ét.
- A `0x007fb5a0` nem frissíti a `[OneUp+0x3ec]` listát: a törlési út része.
- A `DAT_00d676c8` nem a kártyák sorszáma; az élő kártyák számát követi.
- A `0x00809a10` nem írja a P-t: ideiglenes objektum mezőit nullázza.
- A `0x007f9a40` `EDI`-je nem a `OneUp+0x2f8` P; a hívó verem-struktúrája.
- A `0x00809037` csak akkor S-író, ha a gazda OneUp. A hívók ezt nem mutatják.

**Következő Ghidra-címek**
- ~~`Ghidra-kör kell: 0x006223b0 és 0x0061df10 - a 0x006214e0 első paraméterének (p) eredete és osztálya, vagyis hogy p a OneUp-e [blokkoló]`~~ **LEZÁRVA (38.2.27 §3):** `p` a `MakeMoviePanel`.
- `Ghidra-kör kell: 0x008018a0 - a local_64 forrás-lista eredete (a [OneUp+0x3ec] elemei uint azonosítók: melyik gyűjteményből) [blokkoló]`
- `Ghidra-kör kell: 0x008037e0 - a paraméter-struktúra (EDI) eredete, és a +0x10 objektum osztálya ([OneUp+0x2e4], a vtábla-első hívás célja) [blokkoló]`
- ~~`Ghidra-kör kell: 0x005e81e0 - a 0xc8 bájtos elemek forrása (0x005e8283), a 0x009c2fc0 visszatérésének jelentése, és a gyűjtemény (album, mappa) azonosítása [blokkoló]`~~ **RÉSZBEN LEZÁRVA (38.2.27 §1):** a visszatérés megvan. A 0xc8-as „ciklus” vtábla-eltolás volt, nem rekordméret (JAVÍTVA, 38.2.28 §2). A gyűjtemény-azonosítás a 0x00506400 és 0x00475250 körét kérte (38.2.28 §1).
- ~~`Ghidra-kör kell: 0x007fe600 - a két tényező (a, b) forrása és a visszafogás határai a kártya-rekord léptetésében [nem blokkolja a fő utat]`~~ **RÉSZBEN LEZÁRVA (38.2.27 §2):** a bolyongás és a visszafogás megvan; a kezdőérték a 0x008014d0-ból jön (még nincs újramérve).
- `Ghidra-kör kell: 0x004b0190 - az in_EAX (+0xc4, +0x2a8..+0x2d0) és az unaff_ESI objektum osztálya, és a kötések célja [nem blokkolja a fő utat]`
- `Ghidra-kör kell: 0x0040e7b0, 0x0060e260, 0x00640670, 0x006464a0, 0x0064a680 - a CAutoCompleteListBox gazdájának osztálya (a hívó this-e) [nem blokkolja a fő utat]`
- `Ghidra-kör kell: 0x00809c50 - a P+0x30 (S) harmadik írója (0x00809cb3): melyik osztály [nem blokkolja a fő utat]`
- `Ghidra-kör kell: 0x005e8443 - a 0x007f9a40 első paraméterének típusa (f32 vagy bájt), és a hívó paraméter-összeállítása [nem blokkolja a fő utat]`

#### 38.2.27 Az Időrend bináris feltárása, 10. kör: a kártya-forrás, a mozgás képlete, és a `MakeMoviePanel` (#5401, 2026-10-21)

**Kérdés és hatókör.** Három kérdés a `2026-10-21-idorend-10.txt` nyolc címéről. (1) `0x005e81e0` és `0x009c2fc0`: honnan épül egy kártya, milyen sorrendben, és mi a `0x009c2fc0` visszatérése. (2) `0x007fe600`: a kártyák mozgása a négy véletlen mezővel, képlet konstansokkal. (3) `0x0061df10`, `0x006223b0`, `0x0060e260`, `0x00640670`, `0x006464a0`: melyik osztály írja a `[p+0x388]` kiválasztott sorszámot, és mi vezet a dátumcsúszkához. Terméki kódot nem írtunk.

**Módszer.** A szövegben a `(bemeneti fájl N-M)` hivatkozások a `2026-10-21-idorend-10.txt` sorai. A bemeneti Ghidra-C három helyen téves típust mutat, ezért a döntő részeket diszasszemblálás igazolta (`pe_dis.cdis`, `capstone`). A konstansokat `pe_dis.read` nyers bájtokból olvastuk; a `_DAT_` nevek típusát az utasítás döntötte el (`fld qword` = `f64`, `fld dword` = `f32`). A hívóéleket az index `xrefs` táblája, a vtábla-bejegyzéseket az `rtti` tábla metódus-listája adta. A sztring-kulcsokat a hívó EDX-ében lévő címről olvastuk ki. Ghidra-futás nem volt. Ideiglenes fájl nem keletkezett.

**Javítások a korábbi szakaszokban** (a 38.2.26-ban is jelölve):
1. **A `p` nem `OneUp`, hanem `MakeMoviePanel`.** A 38.2.26 §2 ezt feltételezte. A `0x006214e0` két közvetlen hívója a `0x0061df10` és a `0x006223b0`, és mindkettő a `MakeMoviePanel::vftable` virtuális metódusa (§3). A `[+0x388]` tehát a `MakeMoviePanel` mezője: a film-sáv (`filmstrip`) kiválasztott elemének sorszáma.
2. **Az `a` és `b` tényezők változnak.** A 38.2.26 §1 nyitva hagyta, mi a két tényező. Az utasítások szerint a `0x007fe600` minden lépésben módosítja őket (§2).
3. **A kártya-objektum nem ciklusban készül (JAVÍTVA, 38.2.28 §2).** A 38.2.26 §3 szerint a kártyák sorrendje a ciklus sorrendje. Ez téves: nincs 0xc8 bájtos ciklus. A kártya-objektum hívásonként legfeljebb egyszer készül.

**1. kérdés: a kártyák forrása és a `0x009c2fc0` visszatérése** (JAVÍTVA, 38.2.29 §1-2: az `L` nem kártyalista, és a `0x005e81e0` kártyája csillag-jelző képelem, nem gyűjtemény-kártya.)

*A `0x009c2fc0` visszatérése: LEZÁRVA.* A függvény a `DAT_00d67914` globális tábla sztring-kulcsú keresése. Ha a tábla nulla, vagy a kulcs nincs benne, a visszatérés 0 (bemeneti fájl 1798-1826). Találatkor a csomópont `+0x8` mezőjét adja vissza; a `+0x0` mező a következő csomópont. A kulcs-előkészítést (`0x00985ff0`), a kulcs-összehasonlítást (`0x006f9890`) és a hash-indexet (`0x00409df0`) nem néztük meg: NINCS MEG.

*A `0x005e81e0` kulcsai: LEZÁRVA.* A `0x009c2fc0`-hívások EDX-ében sztring-cím van: `0xc88a2c` = `editpanel/preview` (`0x005e8303` és `0x005e8330`), `0xc8ec30` = `editpanel/previewclip2` (`0x005e848f`). A tábla kulcsai vezérlő-útvonalak; ugyanebben a névtérben van a `peoplepanel/header_editbox` (`0x00640d6e`). A tábla feltöltője NINCS MEG (Ghidra-kör kell: `0x00d67914` feltöltője).

*A `0x005e81e0` lépései: LEZÁRVA.*
1. `0x005c76b0(0,0,1,1)` (`0x005e8205`): nem nulla visszatérésnél kilép.
2. `0x00506400` **nem tölti** a `L` listát (JAVÍTVA, 38.2.28 §1). A `*(this+0x2bc) + 0xf8` objektum `this`-ével helyben átírja az `L` már meglévő azonosítóit (`0x005e823d`). Minden hívásban lefut.
3. Mód-2 ágban (`bl = 2`, `0x005e8242`): ciklus az `L` 4 bájtos azonosítóin (`0x005e8260`-`0x005e82b2`). **JAVÍTVA (38.2.28 §2):** nincs 0xc8 bájtos rekord. Az `add esi, 0xc8` (`0x005e8283`) vtábla-eltolás. Azonosítónként két virtuális hívás ugyanazon a beágyazott objektumon: `vt[0xcc]`, majd `vt[0xc8]`.
4. Más módban (`0x005e82d3`): `0x00475250` (`0x005e82e7`), az EDX-ben a `]star` sztring címe (`0xc811d4`). Hogy ez melyik argumentum, és mit jelent a `]star`, NINCS MEG.
5. Kártya-ág: a `0x0097c5d0(0x37c)` foglalás (`0x005e8437`), a konstruktor `0x007f9a40` (`0x005e846b`), utána `0x009df290` (`0x005e8478`). Ez a ciklusok után van.

*Kártya-kapuk: LEZÁRVA.* A kártya-ág három feltételtől függ. (0) A helyi `iStack_24` jelző nem nulla (bemeneti fájl 117; **PONTOSÍTVA, 38.2.29 §2**: ez a jelző az `editpanel/preview` megléte és a `+0x20c` bájt nulla volta, asm `0x005e8313`-`0x005e831a`; a második lekérdezés, `0x005e8325`-`0x005e8349`, ugyanezt kilépési gátként ellenőrzi). (a) A `this+0x3280` objektum (ha az nulla, akkor a `this+0x327c`) `+0x213` bájtja nulla, és a `+0x244` mező nem nulla (bemeneti fájl 117-134). (b) A kártya flagját a `*(this+0x2bc) + 0x48` objektum `+0xcc` vtábla-metódusa adja a `*(this+0xe64)` értékkel (bemeneti fájl 96-102). A flag szerint a konstruktor skálája 1,0 (flag nem nulla), vagy 0,6 (flag nulla, `0xcf3a70`; bemeneti fájl 137-142).

*A `0x009c2fc0`-es második kapu: LEZÁRVA.* Ha az `editpanel/preview` vezérlő `+0x20c` bájtja nulla, a flag szerint egy 64 bites számlálót növel: `0xd35938` (flag nulla) vagy `0xd35918` (flag nem nulla), a párját a `+0x4` cím (`0x005e84bb`-`0x005e84c1`; bemeneti fájl 148-162). Hogy a számláló mit mér, NINCS MEG.

*A kártyák sorrendje: NINCS MEG.* Hívásonként legfeljebb egy kártya készül, a sorrend tehát a hívások sorrendje. Hogy a megjelenítésben hogyan rendeződnek (a `0x009df290` után), NINCS MEG.

*A hívók: LEZÁRVA.* A `0x005e81e0` hívói: `0x005d9cc0` (`0x005db0c5`), `0x005e60d0` (`0x005e6587`) és `0x00760240` (`0x007606fd`). A `0x005e60d0` a 38.2.5-38.2.7 szerint a `qshow`-kör része.

*Gyűjtemény (album, mappa, dátum-csoport): NINCS MEG.* A `L` listát a `0x00506400` tölti, a kódja nincs a bemenetben. A `]star` csillagozott gyűjteményre utalhat, de ez nincs igazolva. A 38.2.18 szerinti `CThumbUI+0x2c0` állítást ebben a körben nem mértük újra.

**2. kérdés: a `0x007fe600` mozgása**

*Az időtényező: LEZÁRVA.* `T` a `0x009a51b0` visszatérése, másodpercben: `T = (QPC_most - QPC_utolsó) · c`. `QPC_utolsó` a `this+0x528` mező (`f64`), `c` a `[0xd678e8]` mező: a gyakoriság reciproka, az első híváskor számolva (`0x009a51d7`-`0x009a51ec`). `QPC_most` a `QueryPerformanceCounter` importtal jön (`0xc40298`). A `0x007fe600` végén (`0x007fe7b0`-`0x007fe7b6`) a `QPC_most` kerül a `+0x528`-ba. A `T` float32-ként jön vissza a hívónak (`0x007fe616`). A `this+0x528` kezdőértéke: NINCS MEG.

*A ciklus: LEZÁRVA.* Ha `[this+0x2f0] & 0xfffffffe` nem nulla, `n = [this+0x2f0] >> 1` rekord fut (`0x007fe626`, `0x007fe795`-`0x007fe799`). A rekordok 0xf8 bájtosak, a tömb a `[this+0x2ec]`-ből indul. Rekordonként: `P` = `+0xcc`, `Q` = `+0xd0`, `a` = `+0xd4`, `b` = `+0xd8`.

Lépések az asm-sorrendben (`0x007fe63a`-`0x007fe799`):
1. `P' = P + T·a` és `Q' = Q + T·b` (`f32`; `0x007fe650`-`0x007fe696`).
2. Ha `P' < 0`: `P = P' + 1,0`. Ha `Q' < 0`: `Q = Q' + 1,0` (`0x007fe6a7`, `0x007fe6be`).
3. Ha `P > 1,0`: `P = P - 1,0`. Ha `Q > 1,0`: `Q = Q - 1,0` (`0x007fe6db`, `0x007fe6f6`).
4. `a = a + (0,001·u1 - 0,0005)`, ahol `u1` az első `_rand` (`0x007fe713`).
5. `b = b + (0,001·u2 - 0,0005)`, ahol `u2` a második `_rand` (`0x007fe753`).

*A véletlen tag: LEZÁRVA, a tartomány részben.* `u = r/32768`, ahol `r` a `_rand` értéke. Az asm `(r + 0x3f8000) << 8` bitmintát ad (`0x007fe718`-`0x007fe71d`), amelyet `fld dword` float-ként olvas: `1 + r/32768`. Ebből kivonja az `1,0`-t (`0x007fe728`). A képlet `r ≤ 32767` esetén igaz. A `_rand` tartományát a bemenet nem mutatja: a 0..32767 az MSVC-szokás, de NINCS MEG igazolva.

*Konstansok (bináris).*

| konstans | cím | érték | bizonyíték |
|---|---|---|---|
| 1,0 | `0xc7e328` | `f64` 1,0 (bájtok `000000000000f03f`) | bináris (0x00c7e328) |
| 0,001 | `0xcf3db0` | `f64` 0,001 (`fca9f1d24d62503f`) | bináris (0x00cf3db0) |
| 0,0005 | `0xcf4858` | `f64` 0,0005 (`fca9f1d24d62403f`) | bináris (0x00cf4858) |
| 1/gyakoriság | `0xd678e8` | `f64`, futás közben számolt | bináris (0x009a51d7-0x009a51ec) |

*Mit jelent: LEZÁRVA (képlet), a jelentés részben.* `P` és `Q` a kártya 0 és 1 közötti helye, amely körbefordul. A visszafogás csak egyszeri ±1 lépés, nem modulo: ha `|T·a|` nagyobb 1-nél, a `P` kívül maradhat a [0,1] sávon. `a` és `b` a sebesség, egység másodpercenként. A bolyongás rekordonként, híváskor egyszer fut, függetlenül `T`-től: a lépés egy híváson belül ±0,0005, nem másodpercenként. Az `a` és `b` nincs határolva.

*Kezdőértékek: NINCS MEG a jelen körben.* Az `a` és `b` kezdőértékét a `0x008014d0` állítja be; a 38.2.26 §1 képletét nem mértük újra.

*A hívó: a gyakoriság NINCS MEG.* A `0x007fe600` egyetlen hívója a `0x007fe7c0` (`0x007fe7e9`). Hogy milyen gyakran fut, NINCS MEG.

**3. kérdés: a `p` osztálya, a `[p+0x388]` írói, és a dátumcsúszka**

*A `p` osztálya: LEZÁRVA, `MakeMoviePanel`.*
- A `MakeMoviePanel::vftable` a `0x00c9d86c` címen van (`rtti`), 45 bejegyzéssel (`0x00c9d86c`-`0x00c9d920`).
- A `0x006223b0` a 28. bejegyzés (`0x00c9d86c + 0x70 = 0x00c9d8dc`, DATA-hivatkozás ugyanitt), a `0x0061df10` a 31. (`+0x7c = 0x00c9d8e8`).
- A `0x006214e0` hívói az `xrefs` szerint: `0x0061df10` (a hívás `0x0061edc5`) és `0x006223b0` (`0x00623d49`). Más hívó és DATA-hivatkozás nincs.
- A `0x006214e0` első paramétere (`[esp+0x174]`, `0x006214e8`) a hívó `this`-e.

*A `[p+0x388]` írói: LEZÁRVA.*
- `0x006214e0`: `0x00621b03` (`mov [ebp+0x388], edi`), `0x00621b31` (`mov [ebp+0x388], eax`), `0x00621ba9` (`-1`).
- `0x006223b0`, film-sáv ág: `0x006232e1` (`mov [ebx+0x388], eax`), csak ha a visszatérés nem `-1` (`0x006232dc`-`0x006232df`). A film-sáv objektumot a `[p+0x298]` mutató adja (`0x006232b9`, `mov ecx, [ebx+0x298]`).

*A sorszám jelentése: LEZÁRVA, film-sáv.* A `0x006223b0` sztring-ágai: `filmstripmove` (bemeneti fájl 6158, 6171), `filmstripselmove` (6662, 6675), `filmstripinsert` (6320, 6358), `filmstripdeletesel` (6514-6563) és más `filmstrip*` ágak. Ezek a `makemoviepanel/...` vezérlő-névtérbe tartoznak. A `0x0061df10` a `0x00610b90` elemszámot használja felső korlátként (bemeneti fájl 3490-3494).

*A `0x005b8d50`: LEZÁRVA (képlet).* A film-sáv objektum `+0x388` és `+0x46c` mezőjét összegzi, és a `+0x44c >> 1` elemszámmal korlátozza. Üres listánál `-1`-et ad, és nem ír. A korlátozás előjel nélküli összehasonlítás (`cmp eax, ecx`, `jbe`; `0x005b8d6f`-`0x005b8d71`): ha az összeg negatív, az utolsó elemre (elemszám - 1) esik, nem a nullára. A `+0x46c` forrása NINCS MEG.

*A dátumcsúszka: NINCS MEG.* A `0x006214e0` nem csúszka-kezelő (38.2.26 §2). A film-sáv indexe nem dátum, hanem a `MakeMoviePanel` diasorszáma. Az Időrend csúszkájának kötése a `0x00a52890` útján (38.2.6) van, és az `OneUp`-oldali kötést nem láttuk.

*A `0x00640670` és a `0x006464a0` a láncban: NINCS MEG.*
- `0x00640670` a `PeoplePanel`-hez tartozik: a `peoplepanel/header_editbox` kulcs (`0x00640d6e`) és a `0x0063f970` hívó, amely a `PeoplePanel::vftable` 31. bejegyzése (`0x00ca1654` tábla), az `editpanel/faces_button` kulccsal (`0x0063f9f3`). A dátumcsúszkáig vezető lánc nincs igazolva.
- `0x00641000` hívja a `0x0060e260`-at (`0x00641491`). A `0x0060e260` `this`-e az ESI, és `0x0097c5d0(0x28)`-ból `CAutoCompleteListBox`-ot (`0x00808fc0`) készít. A `0x00641000` osztálya NINCS MEG.
- `0x006464a0` hívója a `0x00646d70` (`0x00646e87`); nincs vtábla-bejegyzés, és nincs `0x009c2fc0`-kulcs-hívás benne. A `0x00646d70` osztálya NINCS MEG.

*Az Időrend `[OneUp+0x388]` írója: NINCS MEG.* A 38.2.26 §2 forrás-állítása (`0x006214e0`) téves. A 38.2.26 szerinti tartományon kívüli írók közül egyet sem kötöttünk az Időrend-objektumhoz.

**Mérleg (38.2.27).** Nyitott kérdések: 8 nyílt · 11 lezárva · 0 blokkolt · 0 hatókörön kívül · 2 csak nyitva (saját, a kör nem zárta le, a munkasorba kerül).

- lezárva: a `0x009c2fc0` visszatérése; a `0x005e81e0` kulcsai, lépései és kártya-kapui; a hívói; a `T` képlete; a bolyongás és a visszafogás; a `p` osztálya; a `[p+0x388]` írói; a sorszám jelentése; a `0x005b8d50` képlete.
- nyílt (örökölt, a munkasorba): gyűjtemény-forrás (`0x00506400`, `0x00475250`); a kártyák sorrendje (`0x009df290`); az `a`/`b` kezdőértéke (`0x008014d0`); a dátumcsúszka-lánc; a `0x00640670`/`0x006464a0` szerepe; az `OneUp` `[+0x388]` írója.
- nyílt (saját, ebben a körben nem zárható): a `this+0x528` kezdőértéke (a konstruktor nincs a bemenetben); a `+0x46c` forrása (a `0x005b8d50` összegzett mezője).

**Amit KIZÁRTAM**
- A `p` nem a `OneUp`: `MakeMoviePanel`.
- A `0x006214e0` nem írja az Időrend `[OneUp+0x388]`-át.
- A `0x00640670` nincs a `MakeMoviePanel` vtáblában (`rtti`), és a `PeoplePanel` kulcsait használja.
- A `0x009c2fc0` nem épít kártya-listát: név szerinti vezérlőkeresés.
- A `0x007fe600` `T`-je nem képkocka-szám: másodperc.
- A `+0xd4` és `+0xd8` nem állandó: bolyong.
- A `0x007fe600`-ban nincs egész-konverzió: az asm lebegőpontos (a Ghidra-C `(DWORD)` téves).
- A `0x006223b0` sorszám-ága nem float: egész-összehasonlítás `-1`-gyel (a Ghidra-C `(float)` téves).

**Következő Ghidra-címek**
- `Ghidra-kör kell: 0x00506400 és 0x00475250 - a kártya-lista (L) forrása: album, mappa, dátum-csoport vagy csillagozott gyűjtemény; a 0x475250 első argumentuma és a ]star jelentése [blokkoló a gyűjtemény-kérdésnél]`
- `Ghidra-kör kell: 0x009df290 - a kártya-objektum befűzése (0x005e8478 után): a megjelenítési sorrend [blokkoló a sorrend-kérdésnél]`
- `Ghidra-kör kell: 0x00d67914 feltöltője - a DAT_00d67914 név-szerinti tábla regisztrálója (editpanel/preview, editpanel/previewclip2) [nem blokkoló]`
- `Ghidra-kör kell: 0x007fe7c0 - a 0x007fe600 hívója: a frissítés gyakorisága, és a this+0x528 kezdőértékének írója (a konstruktor címe) [nem blokkoló]`
- `Ghidra-kör kell: 0x00a52890 - az Időrend csúszkájának értékkötése az OneUp-oldalon (már kérve): a [OneUp+0x388] írója [blokkoló a dátumkérdésnél]`
- `Ghidra-kör kell: 0x0061b460 és a film-sáv objektum +0x46c mezőjének írói (a 0x005b8d50 összegzett mezője) [nem blokkoló a dátumnál]`
- `Ghidra-kör kell: 0x00641000 - a 0x0060e260 hívójának osztálya (0x00641491) [nem blokkoló]`
- `Ghidra-kör kell: 0x00646d70 - a 0x006464a0 hívójának osztálya és a dátumcsúszkához vezető kapcsolata [nem blokkoló]`

#### 38.2.28 Az Időrend bináris feltárása, 11. kör: az `L` forrása, a befűzés, a frissítési lánc és a bemenet (#5401, 2026-10-21)

**Kérdés és hatókör.** Négy kérdés a `2026-10-21-idorend-11.txt` öt címéről (`0x00506400`, `0x00475250`, `0x009df290`, `0x007fe7c0`, `0x007ffc90`), és a 38.2.27 „Következő Ghidra-címek” listájának ezekhez tartozó pontjai. (1) Honnan jön a kártyák listája (`L`), melyik gyűjtemény, milyen sorrendben, és mit jelent a `]star`. (2) Mi a megjelenítési sorrend a kártyák létrehozása után. (3) A `0x007fe600` mozgás-frissítés hívási üteme. (4) Mit olvas a `0x007ffc90`: csúszkát vagy kártya-indexet, és van-e dátum-leképezés.

**Módszer.** A bemeneti C-kód adta a vázat. A döntő lépéseket diszasszemblálás igazolta (`pe_dis.cdis`), a konstansokat `pe_dis.f32` és `pe_dis.f64` olvasta. A hívóéleket a bináris-index `xrefs` táblája és a bemeneti `HÍVÓK` listák adták. Figyelem: az `xrefs` `from_address` mezője a hívó függvény belépési címe, nem a hívóhely. A hívóhelyet a `HÍVÓK` lista és a diszasszemblálás adta. A közvetett hívást abszolút mutatók bináris-pásztázása mutatta ki. Ghidra-futás nem volt. Ideiglenes fájl a `.bt/` alatt keletkezett, a kör végén törölve.

**Javítások a korábbi szakaszokban** (a helyeken is jelölve):
1. **A `0x00506400` nem tölti az `L` listát** (38.2.27 §1, 2. pont). Helyben átírja az `L` már meglévő azonosítóit. Minden azonosítóhoz a `*(this+0x2bc)+0xf8` objektum `+0x3f0` táblájában (`+0x3f4` a darabszám) keresi a csomópontot. Ha a tábla eleme nulla, a `+0x3f8` csomópontot használja. Ha a csomópont `+0x18` mezője `0x3e9`, az azonosító helyére a csomópont `+0x20` mezője kerül. A sorrend nem változik. Bizonyíték: `0x00506400` C-kód, és asm (`0x00506402`-`0x00506453`).
2. **Nincs 0xc8 bájtos rekord-ciklus** (38.2.27 §1, 3. pont; 38.2.27 „Javítások” 3. pontja; 38.2.26 „A sorrend” és 3. pontja). A mód-2 ág az `L` 4 bájtos azonosítóin lép (`ebx` 0-tól `n-1`-ig, `0x005e8260`-`0x005e82b2`). Az `add esi, 0xc8` (`0x005e8283`) vtábla-eltolás. A `0x005e826a` a `*(this+0x2bc)+0x48` beágyazott objektum (`O`) vtábla-mutatóját tölti be. Azonosítónként két virtuális hívás `O`-n: `vt[0xcc]` (`(azonosító, 1)`, logikai eredmény), majd `vt[0xc8]` (`(azonosító, az előző ellentéte)`). A második hívás nem nulla eredménye kilépteti a ciklust.
3. **A kártya-objektum nem ciklusban készül** (38.2.26 §3 és 38.2.27 „Javítások” 3. pontja). A `0x005e8430`-`0x005e8482` ágban, hívásonként legfeljebb egyszer készül.

**1. kérdés: az `L` forrása, a gyűjtemény és a sorrend** (JAVÍTVA, 38.2.29 §1: az `L` legfeljebb egy azonosító, `[this+0xe68]`; a „kártyák listája” feltevés téves.)

*Az `L` nullázása és a `0x005c76b0` hívása: LEZÁRVA (asm).* A `0x005e81e0` a kimeneti `L`-t (`[esp+0x18]` a mutató, `[esp+0x1c]` a darabszám) nullázza (`0x005e81fd`-`0x005e8201`), majd `0x005c76b0`-nak adja (`0x005e8205`, EAX = `L`, argumentumok `0,0,1,1`). Nem nulla visszatérésnél kilép (`0x005e820c`-`0x005e820e`). Nulla visszatérésnél a `0x005e823d`-nél a `0x00506400` következik.

*Az `L` tartalma: NINCS MEG.* A `0x005c76b0` (asm `0x005c76b0`-`0x005c7758`) a régi puffert felszabadítja, a darabszámot nullázza (`0x005c76bb`-`0x005c76d1`), majd az argumentumok és a `this` mezői szerint ágazik:
- Ha az első argumentum nulla (a `0x005e81e0` hívása ilyen), az ág a `0x005c76fd`-nál folytatódik. Ha a `[this+0xeac]` objektum nem nulla, és `[[this+0xeac]+0x3c9]` nem nulla, a kimenetet annak `vt[0xdc]` hívása adja (`0x005c7710`-`0x005c771f`). Különben a `[this+0xea8]` és a `0x007166c0` hívás (`0x005c7743`).
- Ha az első argumentum nem nulla, és `[this+0xea4]` nem nulla, a `0x005c7ef0` hívás következik (`0x005c76eb`).
- A bináris-index szerint a `0x005c76b0` közvetlenül hívja a `0x005c7830`-at.
- A `0x005c7830` a `0x00506400`-at és a `0x009c2fc0`-t hívja. Sztring-hivatkozásai: `Preferences`, `editpanel/preview`, `PeopleAlbumUseFaceSrc`. Ez beállítás-olvasásra utal, a gyűjteményt nem igazolja.
Hogy melyik ág fut a `0x005e81e0` hívásában, és mit tölt a `0x005c7830`, a `0x007166c0` és a `vt[0xdc]`: NINCS MEG.

*Mód 2 (`bl = 2`): LEZÁRVA (asm).* Az `L` azonosítóin növekvő indexszel megy (`0x005e8260`-`0x005e82b2`). Az első nem nulla eredménynél kilép, és felszabadítja az `L`-t (`0x005e82b6`-`0x005e82c4`). A sorrend az `L` sorrendje.

*A `]star` ág (mód nem 2): LEZÁRVA (hívás).* A `0x005e82d3`-`0x005e82e7` a `0x00475250`-t hívja. EDX = `0xc811d4`, a bájtok szerint `]star\0`. A stack-argumentumok: `*(this+0x2bc)`, `&L`, a mód-bájt (`bl`), és `1`. A `0x00475250` a `*(this+0x2bc)+0x68` táblában keresi a kulcsot. Mód-bájt nulla esetén a `0x004da1d0`, különben a `0x004d9aa0` hívódik, mindkettő `&L`-t kap kimenetként. Nem nulla visszatérésnél a `0x005e81e0` kilép (`0x005e82ee`-`0x005e82f0`). A két keresőfüggvény belseje és a `this+0x68` tábla tartalma: NINCS MEG. A `]star` csillagozott gyűjteményre utalhat, de ez nincs igazolva.

*A gyűjtemény (album, mappa, dátum-csoport, csillagos): NINCS MEG.* Mód 2-ben az `L` a `0x005c76b0` kimenete. Más módban a `]star` tábla eleme. Egyik sem igazolt gyűjtemény.

*A sorrend: RÉSZBEN.* A `0x00506400` nem változtatja az elemek sorrendjét. Mód 2-ben a vtábla-hívások az `L` sorrendjében futnak. Az `L` kezdeti sorrendje a `0x005c76b0`-tól függ: NINCS MEG.

**2. kérdés: a `0x009df290`, a befűzés és a megjelenítési sorrend**

*A `0x009df290` nem rendez: LEZÁRVA (C és asm).* Az EDI kártyát (`0x005e8478`-ban hívják) az ESI tároló pointertömbjének végére fűzi. A tömb a `+0x198`-ban van, a darabszám a `+0x19c` mezőben, `>>1` értékkel (a legkisebb bit jelző; `0x009df2bd`-`0x009df2cb`). Befűzéskor a kártya `+0x244` mezője a tároló lesz, a `+0x213` bájt nulla lesz, a `+0x8` mező alsó három bitje pedig 1 lesz (C-kód). Ha a kártya már ugyanabban a tárolóban van (`+0x213` nulla, `+0x244` egyezik), nem fűzi be újra (`0x009df2ac`-`0x009df2ae`). Ha a tömb bővítése nem sikerül, 4-et ad vissza.

*A tároló kiválasztása: LEZÁRVA (asm).* A `0x009df290` ESI-je a `0x005e8424`-ben betöltött `[X+0x244]`. Itt `X` a `this+0x3280` (ha nulla, a `this+0x327c`). Ha `X+0x213` nem nulla, nincs befűzés (`0x005e842c`-`0x005e8430`). Ez megerősíti a 38.2.27 „Kártya-kapuk” (a) pontját.

*Egy kártya hívásonként, ciklus nélkül: LEZÁRVA (asm).* `0x005e8437` (`0x0097c5d0(0x37c)`), `0x005e846b` (konstruktor `0x007f9a40`), `0x005e8478` (`0x009df290`). A három hívás egyszer fut egymás után.

*A kártyák sorrendje: LEZÁRVA.* A befűzés sorrendje a `0x005e81e0` hívásainak sorrendje. A hívók: `0x005d9cc0` (`0x005db0c5`), `0x005e60d0` (`0x005e6587`), `0x00760240` (`0x007606fd`).

*A megjelenítési sorrend a befűzés után: NINCS MEG.* A `0x009df290` nem rendez, a tároló `+0x198` tömbjét olvasó függvény pedig nincs a bemenetben.

*Az Időrend-oldali lista (`0x007fe7c0`): ellentmondás, NINCS MEG.* A `0x007fe7c0` a `0x00604480`-at hívja (stdcall, `ret 4`, `0x006044d8`) egy négymezős struktúrával (`0x007fe921`-`0x007fe93a`). `P+0` a lista mutatója, `P+4` a darabszám bájtban, `P+8` az alternatív lista, `P+0xc` a kulcs-tömb holdere. A `P+0`, `P+4` és `P+8` a hívás előtt nullát kap. A függvényben más írás ezekre nincs. A `0x00604480` ezért nem rendez (`1 < n` nem teljesül). A kirajzoló ciklus (`0x007fe966`-`0x007fe979`) a `P+4`-et olvassa darabszámnak: nulla, tehát nulla iteráció. Ez ellentmond annak, hogy a függvény kártyákat rajzol. Vagy a dekompilált és az asm-olvasat hiányos, vagy a lista más úton kerül a `P`-be: NINCS MEG.

**3. kérdés: a `0x007fe600` hívási üteme: RÉSZBEN**

*A `0x007fe600` feltétele: LEZÁRVA (asm).* A `0x007fe7c0` a `0x007fe7cf`-`0x007fe7e1` ágon hívja (`0x007fe7e9`), ha `[this+0x3bc]` vagy `[this+0x3bd]` nem nulla. Ha mindkettő nulla, a függvény a `0x007fee5f`-re ugrik. Hívásonként legfeljebb egyszer fut.

*A `0x007fe7c0` hívója: LEZÁRVA (index és HÍVÓK).* Egyetlen hívóhely: `0x007ffc9d` a `0x007ffc90`-ben, feltétel nélkül (ez a függvény első hívása).

*A `0x007ffc90` hívója: LEZÁRVA (index és HÍVÓK).* Két hívóhely a `0x00800a30`-ban: `0x00800d46` és `0x00801003`. A `0x00800a30` `this`-e (EBP) azonos a `0x007ffc90` `in_EAX`-ével: `mov eax, ebp` (`0x00800d33`, `0x00800ff0`).

*A `0x00800a30` hívója: NINCS MEG (közvetett hívás).* A bináris-index szerint nincs közvetlen CALL-hívója. Egyetlen abszolút mutató mutat rá a bináris `0x00cbd6ac` címén, és ez igazított cím. Ez a `QDrawable::vftable` (`0x00cbd66c`, rtti) 16. bejegyzése (0-tól számolva). A hívási ütem tehát egy `QDrawable`-típusú objektum vtábla-hívásától függ. Hogy ki hívja, és milyen gyakran: **JAVÍTVA (38.2.29 §3):** a közvetlen vtábla-hívó a `0x00801f50` (`call eax`, `0x00801f76`), a pumpából (`0x00802060`). A pumpát a `vt[0x60]` (`0x00803ab0`) hívja; annak hívói: NINCS MEG.

*A két hívóhely feltétele: RÉSZBEN.* A `0x00800d46` a `0x00800cc5`-`0x00800ccb` ágon fut, ha `[this+0x3b8]` nem nulla (`bl` ekkor nulla, `0x00800c22`). Ha nulla, a `0x008010c7`-re ugrik. A `0x00801003` a `0x00800eaa`-`0x00800ec7` ágon fut. Ehhez `[this+0x3b8]`, `[this+0x44c]` és `[this+0x474]` mind nem nulla. A hívóhely a `0x00800ed8`-`0x00800f19` ciklus törzsén kívül van (a ciklus a `0x00800f19`-nél zárul). A teljes útvonal: NINCS MEG.

*A `0x007fe600` hívási üteme: NINCS MEG.* Hívásonként egyszer fut, feltétel szerint. Az ütemet a `0x00800a30` hívója adja (lásd fent).

**4. kérdés: mit olvas a `0x007ffc90`, és van-e dátum-leképezés: RÉSZBEN**

*A bemenete: idő-alapú, nem kártya-index: LEZÁRVA (asm).* A `0x00800a30` a két hívóhelyen `trunc(256 · v)` értéket ad át. A szorzó `0xcf39d8` = 256,0 (`0x00800d1b`). A csonkolás a `fistp` (`0x00800d39`) és a `or eax, 0xc00` (`0x00800d2a`) miatt. A `v` a `0x009a51b0` visszatérése: a `this+0x430` QPC-kezdőértéktől (`lea esi, [ebp+0x430]`, `0x00800cd3`) eltelt másodperc. A `0x009a51b0` `(QPC most - *arg) · (1/QPF)` értéket ad (asm `0x009a51b0`-`0x009a51fe`). A `v` nullára vágódik, ha negatív (`0x00800cfe`-`0x00800d0f`). Az első eltelt-idő értékét `1,0`-hoz hasonlítja (`0xc79c88`, f32). Ha kisebb, a második hívás értékét használja (`0x00800cf9`). Ha nem kisebb (`0x00800cf6` `jp` ugrás), a `0x00800d17` a `[esp+0x14]` mezőt olvassa, amelyet ez az ág nem írt: NINCS MEG.
A csúszka-kezelő (`0x00a52890`, 38.2.6) nem hívja a `0x007ffc90`-et. A közvetlen hívók listája csak a `0x00800a30`.

*Mit olvas a `0x007ffc90`: LEZÁRVA (C).*
1. A nyers bemenetet (`iVar2`) adja tovább: `0x007fd180`-nak (`in_EAX+0x2f8`), `0x007fee70`-nek, `0x007fe540`-nek (négyszer), és a `0x009ab690`-nak a `+0x6c0`, `+0x6e8` és `+0x710` vezérlőkre.
2. Százalékot számol: `(bemenet · 100) >> 8`. Ezt a `0x009ab690` kapja a `+0x620` és `+0x5f8` vezérlőre.
3. Olvassa az `A` tömböt: az Időrend `+0x388` f64 tömbjét, darabszám `+0x38c >> 1`. Az elemek hányadosa az utolsó elemmel: `A[i] / A[n-1]`.
4. Olvassa a `+0x6cc`, `+0x6dc` és `+0x6f4` egész-mezőket (elrendezés).
Nem olvas kártya-indexet. A 0xf8 bájtos rekordokat (`+0x2ec`) nem éri el, és a bemenetével nem indexel. A három hívott függvény (`0x007fd180`, `0x007fee70`, `0x007fe540`) belseje és a `0x009ab690` szerepe: NINCS MEG.

*Dátum-leképezés a `0x007ffc90`-ben: LEZÁRVA, nincs.* A függvény nem alakít dátumot csúszkaértékké. Az `A` hányadosait csak egymással hasonlítja. Az egyenlő egymás utáni hányadosok futamot alkotnak (a futam hosszát a C-kódban a `param_1` tartja). A kezdeti összehasonlító érték `0xcf3f58` = -1,0. A futamhossz nulla, egy vagy három esetén a `+0x700` és `+0x704` mezőt írja, és a `0x009ab690` a nyers bemenettel hívódik. A `+0x704` eltolása 0, 7 vagy 14 (`local_24`). Kettes és négynél nagyobb futamnál nincs írás. Ez csoport-jelölés, nem csúszka-leképezés.

*A `+0x700` írása: RÉSZBEN.* A `0x00c29990` (asm `0x00c29990`-`0x00c299aa`): ha `[0xda1428]` nem nulla, az FPU veremtetejének (`st0`) csonkolt egész értéke (`cvttsd2si`, `0x00c299a5`). A másik ág (`0x00c299c6`) célja, és az `st0` forrása a hívóban: NINCS MEG.

*Az `A` tartalma (dátum vagy sorszám): NINCS MEG.* Az Időrend-tartományban nincs írója (38.2.25). A 38.2.23 szerint a `0x007fdd00` a csúszka-tört `t`-hez a legközelebbi `A[i]/A[n-1]` tagot keresi. Ez sorszámot ad. Hogy `A` dátumsor-e: nincs igazolva.

**Mérleg (38.2.28).** Nyitott kérdések: 9 nyílt (8 blokkolt, 1 nem blokkoló) · 13 lezárva · 0 hatókörön kívül · 0 csak nyitva.
- Lezárva: az `L` nullázása és a `0x005c76b0` hívása; a mód-2 sorrend; a `]star` hívás formája; a `0x00506400` működése; a `0x009df290` befűzése (nincs rendezés); a tároló kiválasztása; egy kártya hívásonként; a kártyák sorrendje = a hívások sorrendje; a `0x007fe600` feltétele; a `0x007fe7c0` és a `0x007ffc90` hívója; a `0x007ffc90` olvasási készlete; a dátum-leképezés hiánya a `0x007ffc90`-ben.
- Blokkolt: az `L` tartalma; a gyűjtemény; a `]star` kulcs jelentése; a megjelenítési sorrend; az Időrend-lista ellentmondása; a `0x00800a30` hívója és üteme; a bemenet 1,0-os ága; az `A` tartalma. A `0x009ab690` és a három társ szerepe is ide tartozik a kártya-index kérdéshez.

**Amit KIZÁRTAM**
- A `0x00506400` nem tölti az `L`-t, helyben ír.
- A `0x009df290` nem rendez, és a tároló `+0x198` tömbjén kívül nem ír.
- A `0x007ffc90` nem kártya-indexet olvas. Nem éri el a `+0x2ec` rekordokat.
- A `0x007ffc90` bemenete nem a `0x007fe600` `T`-je. A `0x00800a30` a `this+0x430`-tól számol, a `0x007fe600` a `this+0x528`-tól.
- A `0x00800a30` nem közvetlen CALL-célpont, hanem a `QDrawable` vtábla 16. eleme.
- A `0x007ffc90` közvetlen hívója nem a csúszka-kezelő (`0x00a52890`).
- A `]star` nem igazolt csillagos gyűjtemény.

**Következő Ghidra-címek**
- `Ghidra-kör kell: 0x005c76b0 - az L-építő teljes C-kódja: a nulla első argumentum ágának [this+0xeac] vt[0xdc] hívása, a 0x007166c0 és a 0x005c7830 célja, és mi kerül L-be. [blokkoló a gyűjteménykérdésnél]`
- `Ghidra-kör kell: 0x004da1d0 és 0x004d9aa0 - a ]star kulcs keresése a *(this+0x2bc)+0x68 táblában, és az L-kimenet tartalma. [blokkoló a gyűjteménykérdésnél]`
- `Ghidra-kör kell: 0x007fe7c0 - a 0x00604480 rendező-listájának (P+0, P+4) írója: hol töltődik a lista, és miért nulla a hívás előtt. [blokkoló a megjelenítési sorrendnél]`
- `Ghidra-kör kell: a tároló-objektum (this+0x3280, illetve this+0x327c) +0x198 mezőjének olvasói: a kártyák megjelenítési sorrendje a 0x009df290 után. [blokkoló a sorrend-kérdésnél]`
- `Ghidra-kör kell: a QDrawable::vftable (0x00cbd66c) 16. slotja (0x00cbd6ac): a vtábla-hívóhelyek, az osztály, amelyik hívja, és a hívási ütem; a 0x00800d46 és 0x00801003 teljes útvonala. [blokkoló a hívási ütemnél]`
- `Ghidra-kör kell: 0x00800a30 - a this+0x430 QPC-kezdőértékének írói, és a 0x00800d17 [esp+0x14] ága (a 1,0-nál nem kisebb eset). [blokkoló a bemenet-kérdésnél]`
- `Ghidra-kör kell: 0x009ab690, 0x007fd180, 0x007fee70 és 0x007fe540 - a nyers bemenet szerepe ezekben: kártya-index, csúszka vagy más. [blokkoló a kártya-index kérdésnél]`
- `Ghidra-kör kell: az OneUp +0x388 (A) írói - dátum vagy sorszám (38.2.25 és 38.2.27 szerint az Időrend-tartományban nincs író). [blokkoló a dátumkérdésnél]`
- `Ghidra-kör kell: 0x00c299c6 - a 0x00c29990 másik ága, és az st0 forrása a 0x007ffc90 hívásakor. [nem blokkoló]`

#### 38.2.29 Az Időrend bináris feltárása, 12. kör: az `L` tartalma, a csillag-jelző sprite és a QDrawable-hívási lánc (#5401, 2026-10-21)

**Kérdés és hatókör.** Három kérdés a `2026-10-21-idorend-12.txt` hat címéről: (1) `0x005c76b0`, `0x004da1d0`, `0x004d9aa0`: honnan jön az `L` lista, melyik gyűjteményből, és milyen sorrendben. (2) `0x005d9cc0`, `0x005e60d0`: a `0x005e81e0` hívói, és mikor, hányszor épül kártya. (3) `0x00800a30`: a `QDrawable` 16. bejegyzése, mit rajzol egy képkockában, és mi az ütem. A bemenet a 38.2.28 „Következő Ghidra-címek” listájából készült.

**Módszer.** A bemeneti Ghidra-C adta a vázat. A döntő ágakat diszasszembly igazolta (`pe_dis.cdis`, a `Picasa3.exe` bájtjaiból). A vtábla-bejegyzéseket a nyers bájtokból és a bináris-index `functions` táblájából ellenőriztem. A hívóéleket az `xrefs` tábla adta, de ennek `from_address` mezője a hívó függvény belépési címe, nem a hívóhely; a hívóhelyet ezért mindig a diszasszemblálás igazolta. A vtábla-hívásokat (`mov reg,[reg+0x40]` vagy `[reg+0x60]`, utána `call reg`) bájt-pásztázással kerestem a `.text`-ben. Ghidra-futás nem volt. A munkafában nem keletkezett ideiglenes fájl.

**Javítások a korábbi szakaszokban** (a helyeken is jelölve):
1. **Az `L` nem a kártyák listája** (38.2.27 §1, 38.2.28 §1). Az `L` legfeljebb egy azonosítót tartalmaz: `[this+0xe68]`-t. A kártya-ág nem olvassa az `L`-t.
2. **A `0x005e81e0` kártyája csillag-jelző sprite**, nem gyűjtemény-kártya (38.2.26 §3, 38.2.27 §1). A képe `stars/yes` vagy `stars/no`. Az Időrend-kártyák (0xf8 bájtos rekordok, 38.2.26 §1) más úton épülnek.
3. **A kártya-ág (0) gátja pontosítva** (38.2.27 §1). A jelző az `editpanel/preview` megléte és a `+0x20c` nulla volta; a második lekérdezés kilépési gátként ugyanezt ellenőrzi.
4. **A `0x00801f50` „vt+0x40 ellenőrzés”** (38.2.24 §3) valójában vtábla-hívás, a `0x00800a30` hívója (38.2.28 §3).
5. **A `0x007ffc90` bemenete csonkolt, nem kerekített** (38.2.28 §4). A `fistp` a `0xc00` vezérlőszóval csonkol. A Ghidra-C `ROUND`-ot mutat, ez téves. (Megerősítve.)

**1. kérdés: az `L` forrása, a gyűjtemény és a sorrend**

*Az `L` kezdete: LEZÁRVA (asm).* A `0x005e81e0` a verem `[esp+0x28]`-as helyén nullázza az `L`-t (`0x005e81fd`-`0x005e8201`), majd a `0x005c76b0`-t hívja a `(0, 0, 1, 1)` argumentumokkal (`0x005e8205`). A `0x005c76b0` a régi puffert felszabadítja, a darabszámot nullázza (`0x005c76bb`-`0x005c76d1`).

*Az `L` feltöltése: LEZÁRVA (asm).* Az első argumentum nulla, ezért az ág `0x005c76fd`-nél folytatódik. Két korai kilépés van, mindkettő üres `L`-lel:
- Ha `[this+0xeac]` nem nulla, és `[[this+0xeac]+0x3c9]` nem nulla, a kimenet a `vt[0xdc]` visszatérése (`0x005c7710`-`0x005c771f`).
- Ha `0x007166c0(this+0xea8, flag)` nem nulla, a kimenet ez (`0x005c7743`-`0x005c774a`).

Egyébként, ha `[this+0xe64] != -1` és az `L` bit-0 jelzője nulla, az `L`-be egy elem kerül: `[this+0xe68]` (`0x005c775d`-`0x005c77f3`). Ez az egyetlen írás az `L`-be ezen az úton. Eredmény: az `L` üres, vagy egyetlen eleme `[this+0xe68]`.

*A `0x00506400` nem bővíti az `L`-t: LEZÁRVA (asm).* A `0x005e823d`-nál a `0x005e81e0` a `[this+0x2bc]+0xf8` objektumon hívja, az `L` címével. A ciklus minden elemre megnézi a `[this+0x3f0]` táblát (`0x00506460`-`0x00506496`). Ha a csomópont `+0x18` mezője `0x3e9`, az elem a csomópont `+0x20` mezője lesz. Új elem nem keletkezik, a darabszám nem változik.

*A mód-elágazás: LEZÁRVA (asm).*
- Mód 2 (`cmp bl, 2`, `0x005e8242`): az `L` elemein a `[this+0x2bc]+0x48` beágyazott objektum `vt[0xcc]`, majd `vt[0xc8]` hívása következik (`0x005e8260`-`0x005e82b2`). Az első nem nulla eredménynél a függvény kilép.
- Más mód (`0x005e82d3`): a `0x00475250` hívása a `]star` kulccsal (`0xc811d4`), az `&L`-lel és a mód-bájttal.
- A `0x00475250` mód = 0 esetén a `0x004da1d0`-t hívja (kivonás), különben a `0x004d9aa0`-t (hozzáadás). Mindkettő a `[this+0x2bc]+0x68` névtáblán dolgozik (`0x00475285`-`0x004752ea`).

*A két névtábla-függvény: C-kód, asm nincs ellenőrizve.* A `0x004d9aa0` az `L` elemeit a névhez tartozó vektor végére fűzi, és ha a név még nincs a táblában, létrehozza. A `0x004da1d0` ugyanezt a vektort szűri: kiveszi belőle az `L`-ben szereplő azonosítókat.

*A gyűjtemény: NINCS MEG.* Az `L` egy azonosító vagy üres. A `]star` névtábla igazoltan a mód-nem-2 ág célja. A kulcs neve és a `stars/yes` / `stars/no` képválasztás (2. kérdés) csillag-állapotra utal. Hogy az azonosító album, mappa, dátum-csoport vagy kijelölés-elem: NINCS MEG. A `[this+0xe68]` jelentése is NINCS MEG. A `picasa-gyorsbillentyuk.md` szerint a `[this+0xe64]` a jelenlegi kép indexe; ezt ebben a körben nem mértük újra.

*A sorrend: LEZÁRVA, nincs értelme.* Legfeljebb egy elem van, ezért dátum-, név- vagy létrehozás-sorrend nem jelenik meg.

*Ellentmondás egy másik spec-ben.* A `docs/specs/picasa-gyorsbillentyuk.md` `Ctrl+8` sora szerint a kijelölt képek `]star` állapotát váltja. Ez az út nem igazolja: az `L` legfeljebb egy azonosítót kap. A többképes kijelölés forrása NINCS MEG. A sort a gyorsbillentyű-spec következő körében kell javítani; ebben a körben nem nyúltam hozzá.

**2. kérdés: a hívók, és mikor épül kártya**

*Hívók: LEZÁRVA (asm), egy NINCS MEG.*
- `0x005db0c5` (a `0x005d9cc0`-ben): a `thumbui/startoggle` nevű parancs ága (bemeneti C-kód 2876. sor). A mód-bájt a parancsobjektum `+0x24` mutatójának `+0x359` bájtja (`0x005db0ae`-`0x005db0c3`). Ez a csillag-váltás parancsa.
- `0x005e6587` (a `0x005e60d0`-ban): `push 2`, a billentyűkezelő `WM_KEYDOWN` ágának `case 0x38` ága (bemeneti C-kód 3633. sor; asm `0x005e6584`-`0x005e6587`). A gyorsbillentyű-spec szerint ez `Ctrl+8`.
- `0x007606fd` (a `0x00760240`-ben): **JAVÍTVA (38.2.30 §3):** a hívóhely megvan. Az `editoneup/star` ágban van: `call 0x005e81e0` a gomb `+0x359` bájtjával (asm `0x007606f4`-`0x007606fd`). Korábban NINCS MEG volt, mert nem volt mérve.

*Hányszor épül kártya: LEZÁRVA (asm), hívásonként legfeljebb egy.* A kártya-ág (`0x005e8432`-`0x005e8478`) egyenes kódú, nincs benne ciklus. A kártya-objektum 0x37c bájt (`0x0097c5d0`), konstruktora `0x007f9a40`, befűzése a `0x009df290` hívással a tárolóba (`0x005e8478`). Egy hívás tehát legfeljebb egy kártyát tesz be.

*Mikor épül: LEZÁRVA (asm).* A kártya-ág csak akkor fut, ha a hívás nem lépett ki korábban (a `0x005c76b0`, a mód-2 ciklus és a `0x00475250` nulla eredményt adott), és teljesülnek ezek:
1. `[0xd67914]` nem nulla, az `editpanel/preview` vezérlő (`0x009c2fc0`) megvan, és a `+0x20c` bájtja nulla (`0x005e8325`-`0x005e8349`). Ez a fő gát.
2. A `0x00410fa0` hívás, a `stars/yes` vagy `stars/no` sztringgel az EDX-ben, nem nulla eredményt ad (`0x005e83e4`-`0x005e83f5`). A `0x00410fa0` belseje nincs mérve.
3. A tároló `X` (`[this+0x3280]`, ha az nulla, `[this+0x327c]`) nem nulla, a `[X+0x213]` bájt nulla, és `[X+0x244]` nem nulla (`0x005e83fb`-`0x005e842e`).

*A kártya képe és mérete: LEZÁRVA (asm).* A jelző (`bl`) a `[this+0x2bc]+0x48` objektum `vt[0xcc]` hívásának eredménye, a `[this+0xe64]` értékkel (`0x005e8377`-`0x005e8390`). Igaz esetén `stars/yes` (`0xc97860`), hamis esetén `stars/no` (`0xc9786c`) (`0x005e83d6`-`0x005e83df`). A skála igaz esetén 1,0, hamis esetén 0,6 (`0xcf3a70`, `0x005e8443`-`0x005e8454`). A `vt[0xcc]` a csillagozási lépés után fut, de hogy ugyanazt az állapotot látja-e, mint a `]star` tábla: NINCS MEG.

*Egy kártya = egy gyűjtemény? Nem igazolt.* A kártya-konstruktor nem kap `L`-t, csak a skálát és a jelző bájtot (`0x005e8464`-`0x005e846b`). A kép csillag-állapotot jelez, nem gyűjteményt.

**3. kérdés: a `0x00800a30`**

*Hol van: LEZÁRVA (bájtok, index).* A `QDrawable::vftable` (`0x00cbd66c`, `rtti`) 16. bejegyzése (`0x00cbd6ac` = `0x00800a30`). A vtábla-mutatót az `0x007fa7f0` konstruktor írja (`0x007fa804`, `mov [ebp], 0xcbd66c`). A 38.2.26 szerint ez az Időrend (`OneUp`) konstruktora, tehát `0x00800a30` az Időrend-objektum saját vtábla-bejegyzése, `+0x40` eltolással.

*Ki hívja a `vt[0x40]`-et: LEZÁRVA (asm).* A `0x00801f50` `0x00801f5a`-`0x00801f76`: ha `[this+0x50]` nem nulla, a `QueryPerformanceCounter` után `mov eax,[[this]+0x40]`, majd `call eax` (ECX = `this`). A `this` az Időrend-objektum (a `[this+0x50]`, `[this+0x3ba]` mezők alapján). Ugyanebben a tartományban öt másik `+0x40`-es hívóhely van (`0x00807d3b`, `0x00807d8b`, `0x00809be7`, `0x0080c4fe`, `0x0080df11`); ezek objektuma nincs mérve, és hogy a `0x00809be7` a `0x00800a30`-t éri-e el: NINCS MEG.

*A pumpa: LEZÁRVA (asm, index).* A `0x00801f50` hívója a `0x00802060` (pumpa), a `0x00802110`-nál. A pumpát a `0x00803ab0` hívja, és ez a `ytCallback<QDrawable>::vftable` 1. slotja (`0x00cbd6cc`; a korábbi „`vt[0x60]`” jelölés **JAVÍTVA**, 38.2.31 §1). A `0x008037e0` (az Időrend felépítője) a pumpát a `0x008039f6`-nál hívja; ciklusban való futását nem mértük.

*A `vt[0x60]` hívói: NINCS MEG.* A `.text`-ben 31 közvetett `+0x60`-as hívóhely van (bájt-pásztázás). Az Időrend-objektumon hívó közülük nincs azonosítva. **JAVÍTVA (38.2.31 §1):** a közülük egyik sem a `0x00803ab0`-hoz tartozik; a callback a `+0x4` slotján át hívódik. Ez adja a frissítés ütemét.

*Mit rajzol: RÉSZBEN.* A `0x00800a30` a `[this+0x3ba]` jelzőtől függően két ágon fut (C-kód, az asm a hívásokat igazolja):
- `[this+0x3ba] != 0`: a `0x00aa6f40` után a renderer, a `0x008001c0` (OneUpUI, 38.2.24), `(this, this+0x3c4, -1, -1, -1, -1)` argumentumokkal (`0x00800c1b`).
- `[this+0x3ba] == 0`: a `0x00aa7250` hívása; ha nem nulla, a jelző 1 lesz, és a függvény kilép. Különben a `0x007fd3c0`, `0x009b8ef0` és `0x007fd380` hívás után téglalap-lista (`local_10`) épül, és a renderer ezekre fut. Ha `[this+0x3b8] == 0`, a renderer a teljes ablakot kapja.
- Időlépés, ha `[this+0x3b8] != 0`: a `0x009a51b0` adja az eltelt időt a `this+0x430` kezdőértéktől, másodpercben. Az első mintát 1,0-hoz hasonlítja; ha kisebb, a második mintát használja, különben `t` = 1,0. Ezután `0x007ffc90(trunc(256·t))` (asm `0x00800d2a`-`0x00800d39`). A 38.2.28 szerinti lánc: a `0x007fe7c0` és a `0x007fe600` mozgatja a kártya-rekordok (0xf8 bájt) `+0xcc` és `+0xd0` mezőit, ha `[this+0x3bc]` vagy `[this+0x3bd]` nem nulla.

*Kártyák, csúszka, gombok.* Kártyák: a pozíciók frissülnek (`0x007fe600`), de hogy a renderer (`0x008001c0`) melyik rekordot rajzolja, nincs mérve: NINCS MEG. **JAVÍTVA (38.2.30 §4):** a `0x008001c0` nem olvas kártya-rekordot (`+0x2ec`), tehát a kérdés nem ott van; a rekordok fogyasztója NINCS MEG. Csúszka: NINCS MEG, melyik vezérlő. (A `0x007ffc90` a `0x009ab690` hívással ír vezérlőértéket a `+0x620` és a `+0x5f8` mezőkön, de a vezérlő azonosítása nincs.) Gombok: NINCS MEG.

*Frissítés üteme: RÉSZBEN.* Egy rajzolási lépés a `0x00801f50` egy hívása, feltétele `[this+0x50] != 0`. A pumpa (`0x00802060`) a `0x00801f50`-t a `0x00802110`-nál hívja; az összes ágat ebben a körben nem mértük újra. A pumpát a `vt[0x60]` hívása indítja. Ennek hívóit nem azonosítottuk, ezért a másodperces ütem: NINCS MEG.

**Amit KIZÁRTAM**
- Az `L` nem kártyalista, és a `0x00506400` nem ad hozzá elemet.
- A kártya nem gyűjtemény-kártya, hanem csillag-jelző sprite.
- A `0x00800a30` nem közvetlen CALL-célpont: vtábla-bejegyzés, hívója a `0x00801f50`.
- A `0x00803ab0` (`vt[0x60]`) és a `0x00800a30` (`vt[0x40]`) különböző bejegyzések.
- A Ghidra-C `ROUND` a `0x00800a30`-ban nem egyezik az asm-mal: az `fistp` csonkol.

**Mérleg (38.2.29).** Nyitott kérdések: 11 nyílt · 13 lezárva · 0 hatókörön kívül · 0 csak nyitva.
- Lezárva: az `L` kezdete; az `L` egyetlen eleme; a `0x00506400` nem bővít; a mód-elágazás; a sorrend; a két ismert hívóhely (`0x005db0c5`, `0x005e6587`); a darabszám (legfeljebb egy); a kártya-gátak; a kártya képe (`stars/yes|no`, skála); a `0x00800a30` vtábla-helye; a közvetlen vtábla-hívóhely (`0x00801f50`); a pumpa-lánc (`0x00802060`, `0x00803ab0`).
- Nyitva: a `]star` névtábla tartalma; a gyűjtemény; a `[this+0xe68]` jelentése; a `vt[0xc8]` és `vt[0xcc]` célja; a `0x00760240` hívója; a kártya és a gyűjtemény kapcsolata; a `vt[0x60]` hívói; a renderer tartalma; a csúszka vezérlője; a gombok; a `0x00809be7` hívása.

**Következő Ghidra-címek**
- `Ghidra-kör kell: 0x005c76b0 - a vt[0xdc] célja ([this+0xeac] objektum, flag 0x3c9), a 0x007166c0 célja és a 0x005c7830 célja. [blokkoló a gyűjtemény-kérdésnél]`
- `Ghidra-kör kell: this+0xe68 írói és jelentése (a 0x005e8a70 és a konstruktor környéke). [blokkoló a gyűjtemény-kérdésnél]`
- `Ghidra-kör kell: 0x004d9aa0 és 0x004da1d0 asm - a ]star vektor elemeinek formája (azonosító vagy csomópont), és a névtábla írói. [blokkoló a gyűjtemény-kérdésnél]`
- `Ghidra-kör kell: a [this+0x2bc]+0x48 objektum osztálya, a vt[0xc8] és vt[0xcc] célja (csillag-állapot olvasása és írása). [blokkoló a mód-2 kérdésnél]`
- `Ghidra-kör kell: 0x00410fa0 és 0x007f9a40 - a stars/yes és stars/no kép betöltése és megjelenítése. [nem blokkoló]`
- ~~`Ghidra-kör kell: 0x00760240 és 0x007606fd - a harmadik hívó: mód és feltételek. [nem blokkoló]`~~ **LEZÁRVA (38.2.30 §3):** a `0x007606fd` az `editoneup/star` ágban van; az indítás (`0x005de8e0`) része nyitott: lásd a 38.2.30 listáját.
- `Ghidra-kör kell: a 31 közvetett `+0x60`-as hívóhely (38.2.29) közül azok, amelyek az Időrend-objektumon hívnak. **JAVÍTVA (38.2.31 §1):** a `0x00803ab0`-hoz nem tartoznak. [blokkoló a frissítés-ütemnél]`
- `Ghidra-kör kell: 0x008001c0 belseje - mit rajzol a téglalap-listára és a teljes ablakra (kártyák, csúszka, gombok). [blokkoló a rajzolás-kérdésnél]` **RÉSZBEN LEZÁRVA (38.2.30 §1):** a képmásoló ág és a hívóhelyek megvannak; a kártya, csúszka és gomb kérdés nyitott.
- `Ghidra-kör kell: a 0x009ab690 hívásainak célja a +0x620 és +0x5f8 mezőn: melyik vezérlő a csúszka. [blokkoló a csúszka-kérdésnél]`
- `Ghidra-kör kell: 0x00809b40 - a this osztálya, és hogy a 0x00809be7 vt+0x40 hívása a 0x00800a30-t éri-e el. [nem blokkoló]`
- `Ghidra-kör kell: 0x00506400 - a 0x3e9 csomópontok +0x20 mezőjének írói, és a [this+0x3f0] táblát feltöltő függvény. [nem blokkoló]`

#### 38.2.30 Az Időrend bináris feltárása, 13. kör: a képkocka-rajzoló hívóhelyei, a pumpa-belépő, az `editoneup/star` ága (#5401, 2026-10-21)

**Kérdés és hatókör.** Négy kérdés a `2026-10-21-idorend-13.txt` négy címéről, a 38.2.29 „Következő Ghidra-címek” listájából: (1) `0x008001c0`: mit rajzol egy képkockában, és milyen sorrendben. (2) `0x00803ab0`: a pumpa-belépő (`vt[0x60]`) hívásai egy körben. (3) `0x00760240` és a `0x007606fd` hívóhely: mi indítja, és van-e köze az Időrendhez. (4) A 38.2.24-38.2.28 kártya-állításainak összevetése a `0x008001c0` olvasásával. A bemenetben a `0x007606fd` és a `0x00760240` blokkja bájtra azonos (a `diff` üres): a `0x007606fd` a `0x00760240` belsejében van, nem külön függvény.

**Módszer.** A bemeneti C-kód adta a vázat. A hívóhelyek argumentumait, a döntő ágakat és a `0x00803ab0` / `0x00802060` vezérlési szerkezetét a `pe_dis.cdis` diszasszemblálása igazolta a `Picasa3.exe` bájtjaiból. Ghidra-futás nem volt. Ideiglenes fájl nem keletkezett.

**Javítások a korábbi szakaszokban** (a helyeken is jelölve):
1. **38.2.29 §2, `0x007606fd`: JAVÍTVA.** Korábban NINCS MEG volt, mert nem volt mérve. Most megvan: az `editoneup/star` ágban van (3. kérdés).
2. **38.2.24 §2 és 38.2.29 §3, kártya-rajzolás: JAVÍTVA** (4. kérdés). A `0x008001c0` nem a 0xf8 bájtos kártya-rekordokat (`+0x2ec`) rajzolja, hanem egy képpuffert.
3. **38.2.23 §6, `0x008001c0(this, this+0x46c, -1, -1, -1, -1)`: MEGERŐSÍTVE.** A hívóhely (`0x007fb86b`) és az argumentumok igazoltak.

**1. kérdés: a `0x008001c0` (OneUpUI képkocka-rajzoló)**

*Hívóhelyek (LEZÁRVA, asm).* A `this` a OneUp-objektum. A hat hívóhely és a második argumentum (`param_2`):

| hívóhely | hívó | `param_2` | 3-6. argumentum | ág |
|---|---|---|---|---|
| `0x00800c1b` | `0x00800a30` | `this+0x3c4` | `-1` négyszer | `[this+0x3ba] != 0`, teljes képkocka |
| `0x00800f04` | `0x00800a30` | `this+0x3c4` | a téglalap-lista mezői, ciklusban | téglalap-ág, `[this+0x3b8] != 0` |
| `0x00801079` | `0x00800a30` | `0` | `-1` négyszer | téglalap-ág, `[this+0x3b8] == 0`, teljes ablak |
| `0x007fb86b` | `0x007fb820` (kilépési ág) | `this+0x46c` | `-1` négyszer | teljes képkocka |
| `0x00802ab6` | `0x00802a90` | `this+0x46c` | `-1` négyszer | teljes képkocka |
| `0x00802b06` | `0x00802ae0` | `this+0x46c` | `-1` négyszer | teljes képkocka |

A `0x00802a90` és a `0x00802ae0` szerepe NINCS MEG. A `[this+0x3b8]` ágat a `0x00800eaa`-`0x00800eb1` pár (`cmp`, `je`) dönti el: nulla esetén a `0x00801079` hívás következik.

*A `param_2 ≠ 0` ág sorrendje (LEZÁRVA, C-kód és asm).* Az első öt hívóhely ezt futtatja. Egy hívásban:
1. Ha mind a négy utolsó argumentum `-1`, a téglalap a teljes méret (`[this+0x474]`, `[this+0x478]`, kezdőpont 0).
2. Zárolás: a `GetCurrentThreadId` értékét a `[this+0x20]` tulajdonos szálhoz hasonlítja. Ha más szál tartja, `EnterCriticalSection(this+0x28)`, vagy vtábla-zárolás a `[this+0xc]` jelzőtől függően. Ezután `[this+0x20]` a szál és `[this+0x24]` 0; különben `[this+0x24]` nő.
3. Időarány `t`: ha `FUN_004019b0()` nulla, `t = 1,0`. Különben az eltelt idő (`FUN_009a51b0`, kezdete `[this+0x520]`) osztva a `FUN_004019b0` értékével.
4. A `Preferences\SimpleSlideshow` beállítás olvasása adja az ágjelzőt (`cVar3`).
5. `cVar3 == 0`: `t` legfeljebb 1. Egyébként nemlineáris görbe (`FUN_0040eac0`, `FUN_009e5ac0`; belsejük NINCS MEG).
6. Alfa: `a = ROUND(256·t)`. A `[this+0x519]` jelző 1, ha `a < 256`, különben 0, és az alfa a nyers 256 (a Ghidra-C szerint `3.58732e-43` bitminta).
7. Rajzolás. `cVar3 == 0`: `FUN_007fff30(t, &a)`, majd `FUN_00aa6180(a, param_2, this+0x444, this+0x46c, this+0x4bc, this+0x4e4, -1 négyszer)`: négy tömbös `quad`-blit (a tömbök tartalma NINCS MEG). `cVar3 != 0`: sorról sorra `FUN_009dc040(a, param_2 sora, this+0x454 + this+0x448·sor, this+0x47c + this+0x470·sor, darab)`: keverés két síkba. A `param_2` képpuffer: a pixelcím `+0x10`, a sor-lépés `+4` (pixelben).
8. Zárolás feloldása, visszatérés 0.

*A `param_2 = 0` ág (`0x00801079`, a jelzőágak).* Nincs képmásolás. Három jelző dönt: `[this+0x294]` (bitek), `[this+0x298]` (`fourcc`), `[this+0x29c]` (mód).
- Ha nincs `0x40` bit, vagy a mód 0: ha nincs `0x4` bit vagy a mód 0, `FUN_007fb820()`. Ha nincs `0x4` bit, vagy a `fourcc` nem `YUY2`, nem `UYVY`, újra `FUN_007fb820()`. Különben `YUV`-sáv: `FUN_009bd150`, a `SimpleSlideshow` olvasás, `FUN_009dc040` vagy `FUN_009dd4f0`, vagy `FUN_00737120`, `FUN_00737210`, `FUN_007383b0`, és `FUN_0097caf0`.
- Ha van `0x40` bit és a mód ≠ 0: mód `0x10` esetén `FUN_009dc1c0(...)`; mód `0x20` esetén `FUN_007fa280()`, majd `FUN_00aa6180` vagy `FUN_009dc4b0`, és `FUN_009a8bc0`; más mód esetén `FUN_007fb820()`.
- A `FUN_007fb820` a 38.2.23 §6 szerint a kilépési ág. Hogy ezekből a jelző-ágakból a renderer kilépést indít-e: NINCS MEG (a kilépés teste `[this+0x3bb] == 0` feltételhez kötött).
- Kártyák, `timeline`, `timelinedot`, `sliderthumb`, gombok: NINCS MEG. A hívott `FUN_009dc1c0`, `FUN_007fa280`, `FUN_009dc4b0` és `FUN_00737210` belseje nincs mérve.

*Mit rajzol, összegezve.*
- (a) Egy képkockában a `0x008001c0` egy képpuffert rajzol: a `this+0x3c4` vagy a `this+0x46c` alatti `bitmap`-objektumot, `256·t` alfával. Ez képkocka-keverés, nem kártya-rajzolás.
- (b) Név szerint nem rajzol kártyát, `timeline`-t, `timelinedot`-ot, `sliderthumb`-ot vagy gombot. A törzsben nincs sztring, és a `+0x2ec` hivatkozás 0 darab.
- (c) A kártyák képe és felirata: NINCS MEG. Nem igazolt, hogy bélyegkép vagy gyűjtemény-borító, és az sem, hogy dátum vagy gyűjteménynév.
- (d) Sorrend a hívón belül (`0x00800a30`): a `[this+0x3ba] != 0` ágban `0x00aa6f40` (`0x00800bf5`), majd `0x008001c0` (`0x00800c1b`). A téglalap-ágban (38.2.29 §3 szerint a téglalap-lista után) `0x008001c0` a `0x00800f04`-nél fut; ha `[this+0x3b8] == 0`, a `0x00801079`-nél, a teljes ablakra.

**2. kérdés: a `0x00803ab0` (pumpa-belépő, a `ytCallback<QDrawable>` 1. slotja)** (LEZÁRVA, asm; a korábbi „`vt[0x60]`” jelölés **JAVÍTVA**, 38.2.31 §1)

Egy hívásban, sorrendben:
1. `[this+8]` nulla: visszatérés `-1` (`0x00803abc`-`0x00803ac0`). Nincs további hívás.
2. `call` `QueryPerformanceCounter` (`0x00803ac7`, IAT-rekesz `0xc40298`).
3. Az időbélyeg `fild` és `fstp qword` párral a `[this+0x18]`-ba (`0x00803acd`-`0x00803ad4`).
4. `EAX` = `[this+8]` (a OneUp-objektum). Ha `[EAX+0x3bf]` nem nulla: visszatérés `-1` (`0x00803aec`).
5. Különben `call 0x00802060` `EAX`-szel (`0x00803ae0`). A belépő a pumpa eredményét adja vissza (`ret 8`).

Külső hívás tehát kettő van: `QueryPerformanceCounter` és `0x00802060`. A `this` EAX-ben megy át, és ezt a `QPC`-hívás után töltik be, így a `QPC` nem írja felül.

*A `0x00802060` (pumpa) ágai egy körben (asm, LEZÁRVA):*
- `[this+0x3bb]` nem nulla: visszatérés `1`-gyel (`0x00802078`). Előtte `[this+0x3fc] = 1` (`0x00802072`).
- `[this+0x3b8]` nem nulla: `call 0x00801cb0` (`0x00802087`). Ha utána is nem nulla, az időellenőrzés kimarad, és csak a `[this+0x3c1]` dönt.
- `[this+0x518]` nem nulla: léptetés azonnal, időellenőrzés nélkül (`0x0080209c`).
- Különben: `call 0x009a51b0` (az eltelt idő a `[this+0x520]` kezdettől, `0x008020a5`), majd `call 0x004019b0` (küszöb a `[this+0x760]`-ból, `0x008020b4`), és összevetés. Esedékes esetén léptetés.
- A léptetés, `call 0x00802630` (`0x008020e1`), fut, ha `[this+0x518]` nem nulla, vagy az időellenőrzés szerint esedékes, vagy `[this+0x3c1]` nem nulla (`0x008020d6`-`0x008020dd`). Nem nulla eredménye: `-1` (`0x008020ea`).
- Nulla eredménynél `call` `QueryPerformanceCounter` (`0x008020f7`), `[this+0x520]` = most, `[this+0x518] = 0`.
- `call 0x00801f50` (rajzolási lépés, `0x00802110`) fut, ha nincs nem nulla léptetés. Utána `[this+0x3fc] = 0`, visszatérés `-2` (`0xfffffffe`).

**3. kérdés: a `0x00760240` és a `0x007606fd`** (hívóhely LEZÁRVA, indítás RÉSZBEN)

*A `0x007606fd` (LEZÁRVA, asm).* `0x007606f4`: `movzx edx, byte [eax+0x359]`; `push edx`; `push ebp` (a `this`); `call 0x005e81e0` (`0x007606fd`). Az ágat a C-kód szerint a `0x009cd060(0, ytDrawNode, ytButtonNode, 0)` keresés és a `0x00c07db2` átalakítás előzi meg; nulla eredménynél a visszatérés `1000000`. A hívás tehát a gomb-objektum `+0x359` bájtjával fut, az `editoneup/star` ágban.

*A `0x005e81e0` hívóhelyei (LEZÁRVA).* Három van: `0x005db0c5` (a `0x005d9cc0`-ban, `thumbui/startoggle`), `0x005e6587` (a `0x005e60d0`-ban, a `WM_KEYDOWN` `0x38` ága, Ctrl+8), és `0x007606fd` (a `0x00760240`-ben, `editoneup/star`).

*A `0x00760240` (parancsnév-lánc LEZÁRVA, az indítás RÉSZBEN).*
- Parancsnév-lánc, sorrendben: `exit`, `plusone`, `minusone`, `auto`, `auto2`, `prev`, `next`, `rotateleft`, `rotateright`, `star`, `captionbutton`. Ágak: `exit` → `FUN_0075de50`; `plusone` és `minusone` → `FUN_0075f960(this, …)`; `auto` és `auto2` → léptetés-indítás (`QPC` a `[this+0x3338]`-ba, `[this+0x3370] = [this+0xe64]`); `prev` és `next` → `FUN_0075fac0`; `rotateleft` és `rotateright` → `FUN_005eef30(this, 0x10e)`, illetve `0x5a`; `star` → a `0x007606fd` hívás; `captionbutton` → `FUN_00a54b70`.
- Belépési pont: a `0x005e0090` hívás a `0x005de8e0` függvényből (asm `0x005e008f`-`0x005e0090`). Az argumentum `[esp+0x10]` (a `this`), a parancsnév a `[esp+0x14]`-ben van. A hívás csak akkor fut, ha `call 0x00987030` (a `0xc96b74` objektumon, `0x005e007e`) nem nullát ad (`0x005e0083`-`0x005e0089`).
- Hogy a `0x005de8e0`-t ki hívja: NINCS MEG. Az indexben nincs közvetlen hívója (38.2.22), tehát függvénymutatón vagy vtáblán át indul. **RÉSZBEN JAVÍTVA (38.2.31 §4):** a `0x005de8e0` a `CThumbUI::vftable` (`0x00c9052c`) `+0x58` slotja, a DATA-hivatkozás `0x00c90584` ennek a címe; a közvetlen hívó még NINCS MEG.
- Köze az Időrendhez: **LEZÁRVA (38.2.31 §4):** a parancsnév-láncban nincs `timeline`, közvetlen parancs-kapcsolat nincs. Az 54.4 szakasz szerint az `editoneup/` névtér az egyképes nézeté. A `0x00760240` `this`-e CThumbUI (**JAVÍTVA, 38.2.31 §4**), és a `0x005e81e0` három hívóhelye három különböző helyről jön (bélyegkép-nézet, főablak Ctrl+8, egyképes nézet).

**4. kérdés: a 38.2.24-38.2.28 kártya-állításai** (JAVÍTVA)

*Mérés (LEZÁRVA).* A `0x008001c0` 0x760 bájtos törzsében 0 `+0x2ec` hivatkozás van. A törzs ezeket a mezőket érinti: `+0x20`, `+0x24`, `+0xc`, `+0x28`, `+0x294`, `+0x298`, `+0x29c`, `+0x3c4`, `+0x444`, `+0x448`, `+0x454`, `+0x46c`, `+0x470`, `+0x474`, `+0x478`, `+0x47c`, `+0x4bc`, `+0x4e4`, `+0x519`, `+0x520`.

*Ítélet: JAVÍTVA.* A 38.2.24 §2 kártya-elrendezése és a 38.2.29 §3 „Kártyák” sora úgy kezelte a `0x008001c0`-t, mintha az a `+0x2ec` kártya-rekordokat rajzolná. Nem ez a helyzet: a renderer képpuffert rajzol, és nem olvas kártya-rekordot. A rekordok írói (38.2.26 §1, `0x008014d0`) és mozgatói (38.2.27, `0x007fe600` ciklusa) mérve maradnak. A rekordok fogyasztója NINCS MEG.

**Nyitott kérdések mérlege (38.2.30): 10 lezárva · 7 blokkolt · 3 nem blokkoló · 0 hatókörön kívül · 0 csak nyitva.**
- Lezárva: a hat hívóhely és az argumentumaik; a `param_2 ≠ 0` ág sorrendje; a `0x00803ab0` hívásai; a `0x00802060` ágai; a `0x007606fd` hívóhelye; a `0x005e81e0` három hívóhelye; a `0x00760240` parancsnév-lánca és a `0x005e0090` hívóhely; a `[this+0x3b8]` ág; a renderer `+0x2ec`-mentessége (JAVÍTVA).

**Következő Ghidra-címek**
- `Ghidra-kör kell: 0x00aa5fb0, és a 0x00aa6180 asm-ja a 3-6. paraméter olvasására - a négy tömb forrása (38.2.31 §2). [blokkoló a képkocka-tartalomnál]`
- `Ghidra-kör kell: 0x009a8a30, 0x009a8ad0 és 0x009a8bc0 - a 0x20-as mód segédeinek tartalma (38.2.31 §3; a 0x007fa280, 0x009dc1c0, 0x009dc4b0 és 0x00737210 jelző-ágai LEZÁRVA). [blokkoló a 0x20-as mód kérdésnél]`
- `Ghidra-kör kell: a `this+0x50` objektum vtábla `+0x14` slotjának célja (a 0x007fb820 végén hívott cím; a kilépés célja). **RÉSZBEN JAVÍTVA (38.2.31 §3):** a 0x007fb820 végén van vt+0x14(0,0) hívás, a renderer 0x008005bb, 0x008005e1, 0x008007fe ágai ezt érik el. [blokkoló a kilépésnél]`
- `Ghidra-kör kell: 0x00802a90 és 0x00802ae0 - a két hívó függvény szerepe, és miért a this+0x46c képet kérik. [nem blokkoló]`
- `Ghidra-kör kell: 0x00801cb0 - a [this+0x3b8] ágának célja (a 0x00802060 hívja). [nem blokkoló]`
- `Ghidra-kör kell: 0x00af45f0 - a CThumbUI vtábla `+0x58` egyetlen közvetlen hívóhelyének objektum-osztálya; a 0x005de8e0 vtábla-slot már azonosítva (38.2.31 §4). [blokkoló az indítás kérdésnél]`
- `Ghidra-kör kell: 0x00760240 - a [this+0x3338], [this+0x3370], [this+0xe64] és [this+0x27c] mezők írói (a `this` CThumbUI, 38.2.31 §4). [nem blokkoló: a parancsnév-lánc nem tartalmaz timeline-t]`
- `Ghidra-kör kell: 0x00800950 és 0x009aa670 - a 0x00801f50 rajzolási ágának belseje (38.2.31 §1): a kártya-rajzoló. [blokkoló a kártya-kérdésnél]`
- `Ghidra-kör kell: 0x0040eac0 és 0x009e5ac0 - a nemlineáris átmeneti görbe. [nem blokkoló]`
- `Ghidra-kör kell: a 31 közvetett `+0x60`-as hívóhely (38.2.29) melyik objektumon hívnak; a `0x00803ab0`-hoz nem kötődnek (38.2.31 §1). [blokkoló a frissítés-ütemnél]`

**Amit KIZÁRTAM**
- A `0x008001c0` nem rajzol kártya-rekordot: `+0x2ec` hivatkozás 0 darab.
- A `0x00803ab0` a `QPC`-n és a `0x00802060`-on kívül mást nem hív.
- A `0x00803ab0` `this`-e EAX-ben megy át, nem az ECX-ben, amelyet a `QPC` felülírhatna.
- A `0x007606fd` nem külön függvény: a `0x00760240` belsejében van.

#### 38.2.31 Az Időrend bináris feltárása, 14. kör: a kártya-rajzoló, a keverő síkjai, a jelző-ágak, a CThumbUI-slot és a hiány (#5401, 2026-10-21)

**Kérdés és hatókör.** Öt kérdés a `2026-10-21-idorend-14.txt` tíz címéről, a 38.2.30 „Következő Ghidra-címek” listájából: `0x00801f50`, `0x00aa6180`, `0x009dc040`, `0x007fa280`, `0x009dc1c0`, `0x009dc4b0`, `0x00737210`, `0x007fb820`, `0x005de8e0`, `0x00760240`. A bemeneti C-kód adta a vázat. A döntő állításokat a `Picasa3.exe` asm-je, a bináris-index és a nyers bájtok igazolták. Ghidra-futás nem volt.

**Módszer.**
- `pe_dis.cdis`: asm a `0x00800520`-`0x00800549`, `0x0080051f`-`0x00800525` és `0x007fb930`-`0x007fb9e3` tartományokban (hívási argumentumok, a végső hívássor).
- Bináris-index (`rtti`, `data_symbols`, `xrefs`, `functions`): vtábla-slotok és hivatkozások.
- Nyers bájtok: `0x00c7c828` (a 16 bites maszk), `0x00d695d4` (a `DAT_00d695d4` kezdőértéke a fájlban), `0x00cf3a70`, `0x00cf3ac0`, `0x00cf3a08` (f64).
- Bájt-pásztázás a `.text` nyers tartalmán (Python `re`): a CThumbUI `+0x58` slot hívóhelyei (4. kérdés).
- Ideiglenes fájlok a `.bt/` alatt, a kör végén törölve.

**Javítások a korábbi szakaszokban** (a helyeken is jelölve):
1. **A `vt[0x60]` jelölés JAVÍTVA** (38.2.29 pumpa-bekezdés és Ghidra-lista, 38.2.30 §2 címe). A `0x00803ab0` nem a `vt[0x60]`-on van. A `0x00cbd6cc` a `ytCallback<QDrawable>::vftable` (`0x00cbd6c8`) 1. slotja, vagyis `+0x4`. A `QDrawable::vftable` (`0x00cbd66c`) RTTI-listája 18 bejegyzésű (72 bájt), a `0x00cbd66c + 0x60` tehát nem ennek a táblának a slotja. A három nézeti vtábla (`CThumbUI`, `OneUpUI`, `CTransTimeline::UI`) `+0x60` slotja mind `0x00a56470`. A 38.2.21 §4 szerinti `mov eax,[edx+4]; call eax` a helyes leírás. A 38.2.29 „31 `+0x60`-as hívóhelye” ezért nem a `0x00803ab0`-hoz tartozik.
2. **A `0x005de8e0` hívója RÉSZBEN JAVÍTVA** (38.2.30 §3). A vtábla-slot most azonosítva: `CThumbUI` `+0x58`. A közvetlen hívó még NINCS MEG.
3. **A `0x00760240` `this`-e JAVÍTVA** (38.2.30 §3): CThumbUI.
4. **„Köze az Időrendhez: NEM igazolt” LEZÁRVA** (38.2.30 §3): a parancsnév-láncban nincs `timeline`.
5. **A `0x007fb820` „kilépési hurok” neve JAVÍTVA** (38.2.30 §3 és Ghidra-lista). A függvény képkocka-renderelést és várakozást végez, majd a végén ugyanazt a vt-hívássort futtatja, mint a `oneup/exit` ág. Lásd 3. kérdés.
6. **A `0x00aa6180` négy tömbje** (38.2.30 §1): a hívási sorrend MEGERŐSÍTVE (asm), a szerepük NINCS MEG (lásd 2. kérdés).

**1. kérdés: a `0x00801f50` valódi kártya-rajzoló-e? NEM (LEZÁRVA).**

*Mit csinál* (LEZÁRVA, 14. bemenet 1-69. sor). Ha `[this+0x50] != 0`:
1. QPC.
2. Ha a `vt+0x40` hívás nulla, és `[this+0x3ba] != 0`: a `vt+0x24` objektum `+0x6c` HWND-jének kliensterülete (`GetClientRect`) adja a téglalapot. `FUN_009b49c0` ebből és a `this+0x3cc`, `this+0x3d0` mezőkből számol; kimenete `this+0x3dc` és `this+0x3e0`.
3. `vt+0x24(-1, -1, -1, -1)`, majd `FUN_009aa670(this+0x3c4, -1, -1, -1, -1)` és `FUN_00800950(&téglalap)`.
4. Egyébként `FUN_00aa6fb0()` és `FUN_00aa6b70()`.

*Kártya-rekord: NEM.* A C-törzsben nincs `+0x2ec` mező, és nincs sztring. A függvény a `+0x50`, `+0x3ba`, `+0x3c4`, `+0x3cc`, `+0x3d0`, `+0x3dc`, `+0x3e0` mezőket érinti, a `+0x6c` mezőt a `vt+0x24` objektumon.

*Hívóhelyek* (LEZÁRVA, index és 14. bemenet). `0x007fb981` (a `0x007fb820`-ban) és `0x00802110` (a `0x00802060` pumpában, a rajzolási lépés).

*`timeline`, `timelinedot`, `sliderthumb`, gombok: NEM ebben a függvényben* (LEZÁRVA, nincs névsztring). A 38.2.1 szerint az overlay-rétegeket a `0x007fb210` tölti be. Rajzolásuk NINCS MEG.

*Ami nincs meg:* a kártya képe, felirata, kerete és sorrendje a `0x00800950` vagy a `0x009aa670` láncában lehet. Ghidra-kör kell: `0x00800950` és `0x009aa670`.

**2. kérdés: a `0x00aa6180` és a `0x009dc040` síkjai, a négy tömb és az alfa** (a képlet LEZÁRVA, a tömbök szerepe NINCS MEG).

*0x009dc040* (LEZÁRVA). Paraméterek: `param_1` = alfa `a`, `param_2` = cél (32 bites sorok), `param_3` = `p3`, `param_4` = `p4`, `param_5` = pixelszám. Ha `a ≠ 0`, `s = a - 1`, különben `s = 0`.
- A `0x00c7c828` nyers bájtjai `ff 00 ff 00 ff 00 ff 00`, little-endian qword: `0x00ff00ff00ff00ff`. A 16 bites sávok maszkja tehát `0x00ff`. A súlyok: `255 - s = 256 - a` és `s = a - 1`.
- A `DAT_00d695d4` fájlbeli kezdőértéke `05`, nem nulla, ezért az else-ág fut: `p3` súlya `256 - a`, `p4` súlya `a - 1`. A másik ág a két súlyt felcseréli. A 14. bemenetben a flagnek nincs írója, csak olvasata; az írók NINCS MEG.
- Csatornánként `(p3·(256-a) + p4·(a-1)) >> 8`, a telítés 0..255-re szorít. Egy lépésben két pixel (64 bit).
- A páratlan utolsó pixel skalár ága `p3 + ((p4-p3)·s >> 8)`. Ez a párhuzamos rész második formájával egyezik, de más a kerekítése. A különbség nagyságát nem mértük.
- A függvény csak `param_2`-be ír. `a = 256` esetén a kimenet `p4`, `a = 1` esetén `p3`. Az `a` tehát a `p4` súlya, körülbelül `(a-1)/256`.

*0x00aa6180* (szerkezet LEZÁRVA, a hívási sorrend asm-ből). A `0x008001c0` `0x00800541`-es hívása tíz argumentumot ad át (asm; a `0x00800899`-es hívás is `add esp,0x28`-cal takarít, a részletét nem néztük végig):
1. `a` (alfa);
2. a cél-bitmap (`+4` a sor-lépés pixelben, `+8` a szélesség, `+0x10` a pixelcím);
3. `this+0x444`;
4. `this+0x46c`;
5. `this+0x4bc`;
6. `this+0x4e4` (asm: `0x0080051f` `lea edx,[ebp+0x4e4]`, `0x00800525` `push edx`);
7-10. négy `-1` (a C szerint `x0`, `y0`, `x1`, `y1`).

Ha `a ≠ 0`, soronként két temp-sor készül (`FUN_00aa5fb0(temp1, n, x0)` és `FUN_00aa5fb0(temp2, n, x0, y)`), majd `0x009dc040(a, cél+x0, temp1+x0, temp2+x0, n)`. Ha `a = 0`, a `FUN_00aa5fb0` másol.

*A négy tömb: NINCS MEG.* A `0x00aa6180` Ghidra-C a 3-6. paramétert nem olvassa; csak az `param_1`, `param_2` és a 7-10. szerepel. A temp-sorokat a `FUN_00aa5fb0` tölti, és annak forrása NINCS MEG. Ghidra-kör kell: `0x00aa5fb0`, és a `0x00aa6180` asm-ja a 3-6. paraméter (`+0xc`-`+0x18`) olvasására.

*Célsík* (LEZÁRVA). A `0x008001c0` `param_2`-je. A `0x007fb820` hívásában `this+0x46c` (`piVar5 = param_1 + 0x11b`, és `0x11b·4 = 0x46c`); a `0x00800a30` hívásában a 38.2.30 táblázata szerint `this+0x3c4`.

*Alfa.* `a = ROUND(256·t)` (38.2.30 §1), így `t` az átmenet előrehaladása `p3`-ról `p4`-re.

*Páratlan pixel iránya: NINCS MEG (asm kell).* A C szerint a `0x009dc040` utolsó pixele a párhuzamos else-ággal egyezik. A `0x009dc1c0` és a `0x009dc4b0` utolsó pixele viszont ellentétes a saját párhuzamos ágával. Ezt asm-ban kell ellenőrizni. Ghidra-kör kell: a két függvény utolsó pixel ágának asm-ja.

**3. kérdés: a jelző-ágak tartalma, és indít-e kilépést a renderer** (a függvények LEZÁRVA; a kilépés RÉSZBEN LEZÁRVA).

| függvény | tartalom (C, LEZÁRVA) | kilépés |
|---|---|---|
| `0x007fa280` | Ha `[this+0x23c] & 0x40` és `[this+0x244] == 0x20`: `0x009a8ad0([+0x214], [+0x1f8])`, majd visszatér. Különben az `EDI` mutatta struktúrát nullázza (`+0`, `+0x16`, `+0x18`, `+0x1c`, `+0x24`, `+4`, `+8`, `+0xc`; `+0x14` = 1; `+0x20` = -1), és hívja a `0x009a8a30()`-t. Hívói: `0x0080080e` (`0x008001c0`), `0x007fa339` (`FUN_007fa300`). | nem |
| `0x009dc1c0` | 565-ös (RGB565) sávos keverés. `param_6` súlya `255-s`, `param_7` súlya `s`. Kimenet `param_2`, sor-lépés `param_3` bájt, szélesség `param_4`, sorok `param_5`. Nincs DAT-flag. Hívó: `0x008008d7` (`0x008001c0`, a 38.2.30 szerinti 0x10-es ág). | nem |
| `0x009dc4b0` | 32 bites keverés metszéssel. Cél `param_2`, forrás `ESI` és `EDI` (regiszteres bemenet, a hívó értéke NINCS MEG). A DAT-flag a párhuzamos részt nem változtatja, mindkét ág azonos. Hívók: `0x00800830` (`0x008001c0`), `0x0076c5e7` (`FUN_0076c570`), `0x00a560be` (`FUN_00a54b70`), `0x00bd0aaa` (`FUN_00bd0700`). | nem |
| `0x00737210` | `a ≠ 0`: két temp-sor a `[ESI+8]` és `[ESI+0x10]` síkokból (`FUN_00aa5fb0`), majd `0x009dc040(a, cél, sík1, sík2, [ESI])`. `a = 0`: `FUN_00aa5fb0` másolás. Hívók: `0x00737f43` (`FUN_007376a0`), `0x00800784` (`0x008001c0`). | nem |
| `0x007fb820` | Lásd lent. | RÉSZBEN: a végén `vt+0x14(0,0)` |

*0x007fb820* (LEZÁRVA, C és asm `0x007fb930`-`0x007fb9e3`).
1. `[this+0x3bf] = 1`.
2. Ha `[this+0x3bb] == 0`: `[this+0x3be] = 0`; a renderer `0x008001c0(this, this+0x46c, -1 x4)`; ha `[this+0x3b8] != 0`, nullázza; `0x009ad280(this+0x46c)`; ha `[this+0x49c] == 0`, `0x009a8d80(this+0x46c, -1 x4)`, különben `0x009a8ca0(this+0x46c)`. QPC-t ír a `[this+0x520]`-ba. `r = 0x004019b0()`. Várakozó ciklus: amíg `r · 0,6 > t` (`0x00cf3a70` = 0,6; `t` az eltelt idő másodpercben, a QPC-ből), hívja a `0x00801f50`-t. A hívottak között nincs várakozó API (`Sleep`). Végül `0x00401900`.
3. A `[this+0x3bb]` értékétől függetlenül: `vt+0x24` a `this`-en (`0x007fb99f`). Ha nulla, a `this+0x2dc` objektum `vt+0x24` hívása (`0x007fb9ac`); ha ez is nulla, `return 0`. Egyébként a `vt+0x24` hívások (`0x007fb9bf`, `0x007fb9d2`) után a végső `vt+0x14(0, 0)` (`0x007fb9df`, `call eax`).
4. Visszatérési érték mindig `0`.

*Kilépés? RÉSZBEN LEZÁRVA.* A `0x007fb820` nem hív zárófüggvényt. A harmadik lépés hívássora (`vt+0x24` a `this`-en, majd `vt+0x14(0,0)`) a 38.2.1 leírása szerint azonos a `oneup/exit` ágéval (`0x008032e0`). Ez LEZÁRVA a sorrend azonosságára. A `vt+0x14` célja, és hogy ez bezárja-e a nézetet, NINCS MEG. Ghidra-kör kell: a `this+0x50` objektum vtábla `+0x14` slotjának célja.

A renderer jelző-ágaiból (`0x008005bb`, `0x008005e1`, `0x008007fe`) ez a végső hívássor fut, ha a `0x007fb820` belép. A pumpa léptetése (`0x008027c8`) is hívja. A 38.2.30 „kilépési hurok” elnevezése ezért félrevezető: a függvény képkocka-várakozás és egy végső vt-hívás.

**4. kérdés: ki indítja az `editoneup/` parancsokat, és mi a `this` típusa** (RÉSZBEN LEZÁRVA).

*A `0x005de8e0` vtábla-slot* (LEZÁRVA). A `CThumbUI::vftable` (`0x00c9052c`, 40 bejegyzés) 22. slotja (`+0x58`) `0x005de8e0`. A bináris-index DATA-hivatkozása `0x00c90584` = `0x00c9052c + 0x58`. Az RTTI-listázott vtáblák közül ez az egyetlen, amelyik `0x005de8e0`-t tartalmaz. Az `OneUpUI::vftable` (`0x00cbd5c4`) `+0x58` slotja `0x008032e0`, a `CTransTimeline::UI::vftable` (`0x00cbdcec`) `+0x58` slotja `0x005baa00`. Tehát `0x005de8e0` a `CThumbUI` virtuális metódusa.

*A `0x005de8e0` hívási lánca* (LEZÁRVA, C). A `*(param_2+0x20) == 0x8000004` (parancs-esemény) ágban: `FUN_009cd040()`, majd a `FUN_00987030(0)` kapuk sora. A kapu nem nulla eredménye után hívja a `0x00760240`-t (asm: `0x005e0090`), az `editoneup/` parancs nevével. A kapuk tartalma NINCS MEG.

*Ki hívja a CThumbUI `+0x58` slotját?* (NINCS MEG.) A `.text` bájt-pásztázása (`0x00401000`-tól, a nyers fájlon) három mintát talált:
- Közvetlen `call [reg+0x58]` (`ff 5x 58`): 1 találat, `0x00af472f` (`ff 51 58`, `call [ecx+0x58]`), a `FUN_00af45f0`-ban (534 bájt). Az `ECX` a `[esp+0x24]`-ből jön. A függvény QPC-jellegű időszámítást végez (`fild`, `fdiv` a `0x00cf3a08` = 100,0 értékkel). Az objektum osztálya NINCS MEG.
- `call [esp+0x58]` (`ff 54 24 58`): 3 találat, nem vtábla-hívás; kizárva.
- `mov reg,[reg+0x58]`, utána `call reg` (`8b 4x 58` és `ff dx`, 8 bájton belül): 56 találat. Bármelyik vtáblát jelölhetik; az osztályuk NINCS MEG.

A pásztázás találatlista, nem kizárás: a vtábla-hívás más kódolással is készülhet. Ghidra-kör kell: `0x00af45f0`, és a 56 betöltés-hívóhely osztálya.

*A `0x00760240` `this`-e* (LEZÁRVA). A `0x00760240` egyetlen hívója a `0x005e0090` (a `0x005de8e0`-ban), és a `this` a `0x005de8e0` `this`-e. Ez a slot a CThumbUI-é, tehát a `this` CThumbUI-objektum. Egy RTTI-n kívüli, CThumbUI-ból örökölt osztály ugyanezt a slotot kaphatja; ezt nem zártuk ki.

*Egyképes nézet vagy Időrend?* (LEZÁRVA: nem Időrend-elosztó.) A parancsnév-lánc 11 nevet tartalmaz, mindegyik `editoneup/` előtagú: `exit`, `plusone`, `minusone`, `auto`, `auto2`, `prev`, `next`, `rotateleft`, `rotateright`, `star`, `captionbutton` (14. bemenet, 2899-3464. sor). `timeline` nincs köztük. A `this` tehát nem a OneUpUI, hanem a CThumbUI (rácsnézet). Az `editoneup/` névtér az egyképes nézet parancsait hordozza, de a címzett a rács-osztály.

*Időrend-kapcsolat* (LEZÁRVA: nincs közvetlen parancs-kapcsolat). A 38.2.1 szerint a `CThumbUI::MakeTimeline` (`0x005e943d`) indítja az Időrendet; ez a CThumbUI és az Időrend közötti út. A `0x005de8e0` → `0x00760240` lánc viszont nem ad Időrend-parancsot.

*Megfigyelés* (NEM igazolt). A CThumbUI és az OneUpUI is a `+0x58` slotot foglalja (`0x005de8e0`, `0x008032e0`). Ez közös eseménykezelő-slotra utalhat; ezt nem igazoltuk.

**5. kérdés: mennyi hiányzik az Időrend teljes viselkedéséhez?**

Tételes lista, mindegyik LEZÁRVA vagy NINCS MEG.

1. Kártyák rajzolása (kép, felirat, keret, sorrend): **NINCS MEG.** A `0x00800950` és `0x009aa670` nem kártya-rajzoló; lásd 38.2.32. A valódi rekordfogyasztó és a képpuffer felépítése nyitott.
2. A kártya-rekord (`+0x2ec`, 0xf8 bájt) fogyasztója a `0x00800950` és `0x009aa670` közvetlen láncában: **LEZÁRVA.** Egyik függvény sem olvassa a rekordot; globálisan a rekordfogyasztó továbbra is NINCS MEG.
3. Az `overlay`-rétegek (`timeline`, `timelinedot`, `sliderthumb`, `startbutton`, `left`, `right`) tényleges rajzolási sorrendje: **NINCS MEG.** A geometria és a részleges eseményút a 38.2.32-ben van; a `0x007fb210` csak felépíti az objektumokat.
4. A `quad`-blit forrásai (`this+0x444`, `+0x46c`, `+0x4bc`, `+0x4e4`): **LEZÁRVA a közvetlen szerepükre.** A `0x00aa6180` két forrásleíróként és két affin transzformációként adja tovább őket a `0x00aa5fb0`-nek; a mezők korábbi írói NINCS MEG.
5. A keverő képlete (`0x009dc040`, `0x009dc4b0`, `0x009dc1c0`, `0x00737210`: súlyok, maszk, kerekítés, telítés): **LEZÁRVA.**
6. A páratlan utolsó pixel iránya a `0x009dc1c0` és a `0x009dc4b0` ágában: **NINCS MEG.** Ghidra-kör kell: a két függvény utolsó pixel ágának asm-ja.
7. A `DAT_00d695d4` írói: **NINCS MEG.** Ghidra-kör kell: a `0x00d695d4` írásának keresése (DATA-hivatkozások és bájt-pásztázás).
8. A 0x20-as mód hívott segédei (`0x009a8a30`, `0x009a8ad0`, `0x009a8bc0`): **NINCS MEG.** Ghidra-kör kell: ezek törzse.
9. A YUV-sáv forrás-síkjainak feltöltése (`[ESI+8]`, `[ESI+0x10]`): **NINCS MEG.** Ghidra-kör kell: `0x00737120`, `0x007383b0`, `0x009bd150`, `0x009dd4f0`, `0x0097caf0`.
10. A nemlineáris átmeneti görbe: **LEZÁRVA.** A képlet és a normalizáló konstans forrásai a 38.2.24 és 38.2.32 szakaszban vannak.
11. A frissítési ütem: a `0x004019b0` visszatérési értékének mértékegysége, és a `0x00802630` léptetés tartalma: **LEZÁRVA erre a két kérdésre.** A mértékegység másodperc; a pontos `callback`-ütem külön nyitott kérdés.
12. Az időküszöb konstansai: `0x00cf3a70` = 0,6 és `0x00cf3ac0` = 2^32 (negatív korrekció): **LEZÁRVA.**
13. A csúszka (`sliderthumb`) húzása és dátumhoz kötése: **NINCS MEG.** Az x-koordinátából választott sorszám pontos képlete a 38.2.32-ben van; az `A` tömb jelentése és írói nyitottak. A `0x00a52890` örökölt eseménykezelő nem azonosítja a dátumforrást.
14. Az Időrend `prev`, `next` és `timeline` gombjainak törzse (`0x00802980`, `0x008029f0`, `0x007fda00`, `0x00802230`): **LEZÁRVA.** Az `editoneup/*` parancsok nem az Időrend vezérlői; azok feltárása külön kérdés, nem része ennek a jegynek.
15. Billentyűk az Időrend alatt, a OneUpUI útja: **LEZÁRVA** (38.2.1: a `WM_KEYDOWN` és `WM_KEYUP` virtuális metódusa nem ad műveletet).
16. Billentyűk a főablakban: **NINCS MEG.** Ghidra-kör kell: `0x005e60d0` (globális billentyűkezelő) és `0x005e6587`.
17. A kilépés célja (`vt+0x14(0, 0)`) és a visszatérési nézet: **NINCS MEG.** Ghidra-kör kell: a `this+0x50` objektum vtábla `+0x14` slotjának célja.
18. Az `editoneup/` parancsokat indító hívó (a CThumbUI `+0x58` hívója): **NINCS MEG.** Ghidra-kör kell: `0x00af45f0` és a 56 betöltés-hívóhely.
19. A kártya-animátor mozgása (38.2.24-38.2.28 állításai): **LEZÁRVA a binárisból levezetett pálya és időfüggés szintjén.** A korábbi szakaszokban rögzített képletek, címek és konstansok, valamint a görbe-wrapper újraellenőrzése a 38.2.32-ben található. A tényleges rajzolt kártyához tartozó rekordfogyasztó és ablakkoordináta továbbra is NINCS MEG.
20. A pumpa `+0x60`-as hívóhelyei (38.2.29, 31 pásztázási találat): **NINCS MEG.** Ghidra-kör kell: `0x008037e0` és a `0x00cbd6c8` `callback`-vtábla útja, melyik objektum regisztrálja a `qshow` pumpát.

**Mérleg a 15. kör után:** 20 tétel · 9 lezárva (2., 4., 5., 10., 11., 12., 14., 15., 19.) · 11 nincs meg.

**Amit KIZÁRTAM**
- A `0x00801f50` nem kártya-rajzoló (nincs `+0x2ec`, nincs sztring).
- A `0x007fa280`, `0x009dc1c0`, `0x009dc4b0` és `0x00737210` nem hív kilépő rutint.
- A `0x005de8e0` nem az egyképes nézet (OneUpUI) slotja: a OneUpUI `+0x58` slotja a `0x008032e0`.
- A `0x00760240` nem Időrend-elosztó: nincs `timeline` a parancsnév-láncban.
- A `0x00803ab0` nem a QDrawable `+0x60` slotja.

**Következő Ghidra-címek**
- `Ghidra-kör kell: 0x009aa720 és 0x008001c0 - a `bitmap`-puffert összeállító hívási út, melyik +0x2ec rekordot olvassa, és a kép/felirat/keret forrása. [blokkoló a kártya-kérdésnél]`
- `Ghidra-kör kell: 0x00802230 és 0x008037e0 - a [this+0x3ec] lista szolgáltatójának típusa, az Időrend képhalmaza, gyűjteménye, elemszáma és sorrendje. [blokkoló a forráshalmaznál]`
- `Ghidra-kör kell: 0x008001c0 és 0x00aa6180 - honnan kapja a két képforrás-leírót és a két transzformációt, mely kód írja a négy mezőt. [blokkoló a quad-forrás eredeténél]`
- `Ghidra-kör kell: 0x009dc1c0 és 0x009dc4b0 utolsó pixel ága (asm), és a 0x00d695d4 írói. [nem blokkoló a szerkezetnél, a pontos képhez kell]`
- `Ghidra-kör kell: 0x009a8a30, 0x009a8ad0, 0x009a8bc0, 0x009a8ca0, 0x009a8d80, 0x009ad280 - a 0x20-as mód és a 0x007fb820 keretének segédei. [blokkoló a 0x20-as mód kérdésnél]`
- `Ghidra-kör kell: 0x00737120, 0x007383b0, 0x009bd150, 0x009dd4f0, 0x0097caf0 - a YUV-sáv síkjainak forrása. [nem blokkoló]`
- `Ghidra-kör kell: 0x00af45f0 - a CThumbUI +0x58 egyetlen közvetlen hívóhelyének objektum-osztálya ([ecx] forrása), és a 56 betöltés-hívóhely osztálya. [blokkoló az editoneup-indító kérdésnél]`
- `Ghidra-kör kell: 0x007fb820 és 0x008032e0 - a this+0x50 objektum +0x14 vtábla-slotjának célja, valamint a visszatérési nézet. [blokkoló a kilépésnél]`
- `Ghidra-kör kell: 0x00a42c20, 0x009a9c90 és 0x00a3f490 - az overlay-rétegek tényleges rajzolási sorrendje és a rétegekhez kötött eseménycélok. [blokkoló a teljes overlay-viselkedésnél]`
- `Ghidra-kör kell: 0x007fde80 és 0x007fda80 - a listaikon és a timelinedot eseményútja, valamint a hat találati cél és a callbackek teljes összerendelése. [blokkoló a vezérlők teljes feltárásánál]`
- `Ghidra-kör kell: 0x007fdd00 és 0x008001c0 - a slider ordinalitása ismert, de az A tömb írói, jelentése és dátumkapcsolata nem. Az írókat paszta.py-val is meg kell keresni. [blokkoló a dátum-leképezésnél]`
- `Ghidra-kör kell: 0x008037e0, 0x00802060 és 0x007fb540 - a másodperces küszöb ismert, a tényleges callback-ütem és a léptetés pontossága nem. [blokkoló a lejátszási ütemnél]`
- `Ghidra-kör kell: 0x00802c20, 0x00aa6f40, 0x007fb820 és a this+0x50 objektum vtábla +0x14 célja - a szóköz, az indítógomb, a diavetítésbe lépés és az Időrendbe visszatérés összekötése. [blokkoló a diavetítés-visszatérésnél]`
- `Ghidra-kör kell: 0x005e60d0 - a főablak billentyűágai, köztük a qshow alatti globális szóköz, nyilak és listaikon viselkedése. [blokkoló a főablak-billentyűknél]`
- `Ghidra-kör kell: 0x0075de50, 0x0075f960, 0x0075fac0, 0x005eef30, 0x00a54b70, 0x005e81e0 - az editoneup/ parancsok törzse (nem Időrend, de a 0x00760240 lánc célja). [nem blokkoló az Időrendhez]`

#### 38.2.32 Az Időrend bináris feltárása, 15. kör: quad-források, ütemezés, vezérlők és nyitott pontok (#5401, 2026-10-21)

**Hatókör.** Ez a kör a `2026-10-21-idorend-15.txt` címeket vizsgálta. A `0x00800950` és `0x009aa670` a `0x00801f50` hívási útján van, de nem bizonyult kártya-rajzolónak. A `0x00aa6180`, `0x00aa5fb0`, `0x004019b0`, `0x00802630`, `0x00802980`, `0x008029f0`, `0x007fda00`, `0x00802230`, `0x0040eac0` és `0x00a52890` útjait a bemeneti dekompiláció és a helyi diszasszembly összevetésével vizsgáltam. A `CTransTimeline` projektosztály nem azonos a `qshow` kártya-animátorával; a `qshow` átmeneti görbéje a `0x0072df60` függvényben van.

**Módszer és bizonyítottság.** A bemeneti Ghidra-kimenet állításait ott ellenőriztem utasításszinten, ahol a hívási cím, az argumentum vagy a konstans döntő volt (`pe_dis.cdis`). A második, ettől független ellenőrzési út a hivatkozási lánc, a `RTTI`/import-adat, a hívott függvény adat-hozzáférése, illetve az erőforráscsomag geometriája volt. Ghidra-futás nem volt. A teljes `.text` pásztázást nem ismételtem meg; negatív globális állítást az index hiánya alapján nem teszek.

**1. Kártya-rajzolás és a `+0x2ec` rekord**

*A `0x00800950` nem rajzol kártyát: LEZÁRVA.* Hívója a `0x00801f50` (`0x0080202d`). Négy téglalapot kér a `0x009b4f10` függvénytől; ha a kapott téglalap nem üres és `[this+0x50]` nem nulla, a `GetStockObject(4)` eredményét adja a `FillRect`-nek, majd elengedi a `DC`-t. A függvényben nincs kép-, felirat- vagy `+0x2ec` rekordolvasás.

*A `0x009aa670` nem választ kártyát: LEZÁRVA.* Előbb a `0x009aab60` eredményét ellenőrzi; ha az nem 3, a `this+0x6c` `HWND`-jén `DC`-t kér, a kapott négy kép/terület argumentumot a `0x009aa720`-nek adja, majd elengedi a `DC`-t. A `0x009aa720` `bitmap`-et rajzol a neki átadott leírókból. Sem a függvényhívás, sem a hívott függvény nem kap kártyarekord-mutatót. Ez kizárja a korábbi feltételezést, hogy e két cím valamelyike maga a kártya-rajzoló. A rekord globális olvasóját és a képpuffer forrását nem azonosítottam.

**2. `overlay`-rétegek és vezérlők**

*A `0x007fb210` réteg-építő, nem rajzoló: LEZÁRVA.* A `0x008037e0` hívja. A rétegek objektumait a `0x00410fa0` tölti be. A `left`, `right`, `mouse`, `rollovermouse`, `exit`, `timeline`, `timelinedot`, `sliderthumb` és `startbutton` struktúrájának `x`-koordinátáját `_DAT_00d34040`-nel skálázza; az `y`-koordinátát nem írja át. Ez önmagában nem adja meg az ablak tényleges pixelkoordinátáit és a rajzolás sorrendjét.

*A rajzcsomag koordinátái: feltételes.* A `runtime/respack.yt` rétegrekordjai 640 x 480 tervezővászonhoz tartozó téglalapokat adnak. A releváns erőforrások és rekordcímek: `timeline` (`0x248b99`, `(197,461)-(442,468)`), `timelinedot` (`0x248a97`, `(215,462)-(222,470)`), `sliderthumb` (`0x248be7`, `(260,457)-(285,480)`), `startbutton` (`0x27f126`, `(298,404)-(341,432)`), `exit` (`0x27ca41`, `(8,404)-(51,432)`), `left` (`0x27da50`, `(243,405)-(274,436)`), `right` (`0x27e5d4`, `(366,405)-(397,436)`). A `#timelinedot` külön kép (`0x24898b`, `(215,459)-(222,470)`). A koordinátákat az erőforrásrekord és a 38.2.22-ben rögzített vászonértelmezés adja; ezek nem futásidejű képernyőmérések.

*Kattintási célok: részben lezárva.* A `0x007fde80` eseményút és a `0x007fda80` találati vizsgálat négy `overlay`-objektumra vezet: `startbutton` a `0x007fb820` kilépési/átadási ágra; `exit` szintén a `0x007fb820`-re; `right` a `0x007fd150`-re; `left` a `0x007fd120`-ra. A `sliderthumb` húzása külön ágon megy. A `timeline`-pont képe és a listagomb eseménycélja nincs összekötve az eseményelosztóval. A `startbutton` utáni vtábla-hívás címzettje és szerepe, valamint a kilépés célablaka nyitott.

*A csúszka: feltételes.* A `0x007fdd00` a `timeline` bal szélét `[this+0x6d8]`, szélességét `[this+0x6c8]`, az egér `x`-koordinátáját és a fogantyú szélességét `[this+0x718]` használja. Az `x`-et a sávra szorítja, `t=(x-L)/W` normált értéket számol, majd ha `n=[this+0x38c]>>1` legalább 1, az `A[i]/A[n-1]` értékekhez legközelebbi sorszámot választja. Az első szigorúan kisebb távolság nyer; a kezdeti minimum `10000000` (`0xcf3e88`). `[this+0x514]` lesz a választott sorszám; `[this+0x510]` az ugyanilyen sorszámú rekord `+0` mezője, ha van ilyen rekord. A fogantyú `x`-helye `trunc(x-(floor(SW/2)+3))`, felső széle változatlan. A számítás pontos, de az `A` tartalma nincs meg, ezért a dátum-hozzárendelés nem állítható.

**3. Quad-blit bemenetek**

*A párosítás: LEZÁRVA.* A `0x008001c0` a `0x00aa6180`-nak átadja a négy mezőt. A `0x00aa6180` közvetlen hívási sora két `0x00aa5fb0`-hívás párját igazolja:

| mező | binárisból olvasott szerep |
|---|---|
| `this+0x444` | az első forrásleíró |
| `this+0x4bc` | az első forrás transzformációja |
| `this+0x46c` | a második forrásleíró |
| `this+0x4e4` | a második forrás transzformációja |

Az első hívás az `0x00aa5fb0`-nek a `+0x444` és `+0x4bc` párost adja; a második a `+0x46c` és `+0x4e4` párost. A `0x00aa5fb0` a forrásleíró szélességét, magasságát, pixelcímét és az affin mátrix hat `f32` tagját olvassa, és belőlük ideiglenes sort számol. A két forrásleíró és transzformáció korábbi írói NINCS MEG.

**4. Léptetés, időegység és átmeneti görbe**

*A `0x004019b0` értéke másodperc: LEZÁRVA.* A getter a `qshow` `[this+0x760]` beállításából, a `Preferences\SlideshowEffectTime` `registry` értékből tér vissza. A `0x00802060` a `QPC`-különbséget `QPF`-fel másodpercre alakítja és ehhez a küszöbhöz hasonlítja. Ez küszöb, nem bizonyított fix periódus. A pumpa `0x007fb540` ciklusának 50 ms-os alvása legfeljebb 20 frissítést ad másodpercenként, ha be van állítva a frissítési jelző. A jelző beállításának üteme, így a tényleges automatikus léptetés `callback`-üteme NINCS MEG.

*A `0x00802630` léptetése: LEZÁRVA a vezérlési útvonalra.* A darabszámot `[this+0x3f0]`, az indexet `[this+0x3f4]` tartalmazza. Üres listán lezárja a kiegészítő objektumokat és visszatér. A lista végén vagy a `0x007fb820` kilépési/átadási ágat hívja, vagy a `0x007fda00`-val az indexet nullázza, a `[this+0x3b9]` és `[this+0x3fd]` jelzőktől függően. Egyébként eggyel növeli az indexet és `0x00802230(this,0)`-t hív. A `0x00802230` az indexelt azonosítót veszi a `[this+0x3ec]` listából, új véletlen helyeltolást állít elő, a forrásobjektum megfelelő virtuális ágán kér képet/tartalmat, újrarajzolja a puffert, és `QPC`-időt ment. A lista szolgáltatójának típusa, a tényleges képforrás, a felirat és a rajzolt helyzet leképezése NINCS MEG.

*Az `easing`-képlet: LEZÁRVA a `qshow` kártyagörbére.* A `0x0040eac0` `f32` argumentumot ad át a `0x00c29c6c` `CRT`-célpontnak, és `f32` eredményt ad vissza. A `0x0072df60` ezt exponenciális függvényként használja. `0 < u < 1` esetén `y=8u`, `a=exp(-1)` és:

```text
g(y) = y - 1 + exp(-y)                         ha y < 1
g(y) = a + (1 - a) * (1 - exp(-(y - 1)))       ha y >= 1
E(u) = K * g(y)
K = 1 / g(8)
```

`u <= 0` esetén az eredmény 0, `u >= 1` esetén 1. Az `8` konstans f64 a `0xc7ea10` címen, az `1` f64 a `0xc7e328` címen, az `-1` f32 a `0xcf3ed0` címen, a `-7` f32 a `0xcf4740` címen található. A `0x009e5ac0` `exp(-1)` és `exp(-7)` alapján számolja ki és gyorsítótárazza a `K` értéket a `0xd337a8` f64 mezőbe. A korábbi 38.2.24 képletét a wrapper és a normalizáló törzs külön asm-ellenőrzése megerősíti. A teljes képernyőn mért mozgáshoz nem készült felvétel.

*A pálya és az időfüggés: binárisból rögzítve, a 38.2.24 alapján.* Az animátor pozíciója `pos(t)=B0+sum(E(u_j)*dx_j)`, ahol `u_j=(t'-v_j)/(end_j-v_j)` és `t'=t+0.02` (`0xcf48a8`). A kártyák paramétere `t_i=i*S+O`; a görbe kimenete `(x,y,w)`, a lépték `w*Z`, ahol `Z=[P+0x28]`. A képernyőeltolás a `[OneUp+0x2c8]` téglalap szélességével és magasságával skálázza az `x` és `y` értéket. Az alfa `ROUND((1-pow(z,1.5))*256)`, ahol `z=max(0,(1/w-1)/9)`; a `9`, `256` és `w>0.1` konstansok címei `0xcf3ef8`, `0xcf39d8`, `0xc7dd30`, a kitevőfüggvény címe `0x005568e0`. A kártyarekord képforrása, az affine mátrixokból adódó elforgatás és a képernyőn mért kezdőpont NINCS MEG. A pálya számítása és az `A` csúszka adatforrása külön mechanizmus.

**5. Prev, next, timeline, szóköz és kilépés**

*`prev` és `next`: LEZÁRVA.* A `0x00802980` csökkenti a `[this+0x3f4]` indexet, a `0x008029f0` növeli. Mindkettő frissíti a képet a `0x00802830` és `0x00a54b70` útján. `next` a felső határ alatti elemen a `[this+0x2e8]` objektum vtábla `+0xc` slotját is meghívja az aktuális listaazonosítóval. A szolgáltató pontos típusa NINCS MEG.

*`timeline`: LEZÁRVA.* A `0x007fda00` előfeltétele `[this+0x2d8] != 0` és `[this+0x538] != 0`. A jelenlegi indexet legalább nullára igazítja, rögzíti a QPC-t, meghívja a `0x00802230(this,1)` függvényt, majd beállítja a timeline-állapotjelzőket. A `0x00802630` ugyanennek a függvénynek a `0` jelzőjű ágát használja automatikus léptetéskor.

*Billentyűk és szóköz: RÉSZBEN LEZÁRVA.* A `0x00801270` `WM_KEYDOWN` ága a bal/fel billentyűt a `0x008011b0`-hoz, a jobb/le billentyűt a `0x00801210`-hez irányítja. Mozgás közben ezek a `0x007fd0c0` animációs lépést használják; álló helyzetben a `0x00802980` vagy a `0x008029f0` indexléptetés fut. A szóköz lenyomásakor a `[this+0x3bb]` szünetjelzőt váltja a `0x00801130`-on át; folytatáskor a `0x00803110` az aktuális indexet megtartva azonnali léptetést jelöl. A közvetlen kódútból nem következik, hogy ez új teljes képernyős diavetítés-ablakot nyit. A 38.2.17-ben rögzített `job-220` megfigyelés teljes képernyős bemutatóról szólt, de a nyers mérőcsomag nem található a megadott helyi archívumban, ezért ezt ebben a körben nem tudtam újra ellenőrizni. Az ablakba való visszatérés és a listaikonhoz kötött gombcél NINCS MEG.

**6. Ellentmondáspróba és korlátok**

Megpróbáltam cáfolni, hogy a `0x00800950` vagy a `0x009aa670` olvassa a kártyarekordot. A hívási láncban ezek `RECT`/`bitmap` bemenetet kapnak; az első `FillRect`-et végez, a második a `bitmap`-et továbbadja a `0x009aa720`-nek, és a dekompilált mezőhasználatban nincs `+0x2ec`. A próbát ugyanazzal a mércével ellenőriztem a közvetlen diszasszembly hívási argumentumokon és a hívott függvény adat-hozzáférésén. Ez lezárja a két megadott függvény állítását, de nem bizonyítja, hogy a teljes `.text` más pontján nincs rekordolvasó.

`QEMU`-próba és `Wine`-felvétel nem készült. A helyi program `PE32` `Windows` `GUI` bináris, csak a `qemu-i386` `Linux` felhasználói módú futtató érhető el; `qemu-system-i386` és `Wine` nem található. A mérőcsomag archívumában a `job-220` keresése nem adott találatot.

**A 38.2.31 hiánylistájának 15. köre történeti állapot.** A 16. kör az alábbi tételes listával frissíti mind a húsz pontot. A régi lista megmarad, hogy a korábbi kör megállapításai visszakereshetők legyenek.

**A 38.2.31 nyitott pontjainak 16. kör utáni állapota.**

1. **NINCS MEG.** A képek forráshalmaza, csoportosítása, elemszáma és rendezési mezője. A `[this+0x3ec]`, `[this+0x3f0]`, `[this+0x3f4]` mezők használata ismert, a szolgáltató típusa és adata nem. Lásd 38.2.33/1.
2. **LEZÁRVA a megnevezett közvetlen láncra.** A `0x00800950` és `0x009aa670` nem olvassa a `+0x2ec` rekordot. A teljes bináris rekordfogyasztója **NINCS MEG**. Lásd 38.2.33/2.
3. **NINCS MEG.** A rétegek tényleges kirajzolási sorrendje. A `0x00a42c20`, `0x009a9c90` és `0x00a3f490` nem sorrend-kezelő, hanem általános kép-újramintavételező út. Lásd 38.2.33/3.
4. **LEZÁRVA a közvetlen szerepükre.** A négy `quad`-mező párosítása ismert, korábbi íróik nem. Lásd 38.2.32/3.
5. **LEZÁRVA.** A keverő képlete a korábbi szakaszban rögzített. Lásd a 38.2.31 listáját.
6. **NINCS MEG.** A két keverő páratlan utolsó pixel ága. Következő címek: `0x009dc1c0`, `0x009dc4b0`.
7. **NINCS MEG.** A `DAT_00d695d4` írói. Következő cím: `0x00d695d4` adat-hivatkozási vizsgálata.
8. **NINCS MEG.** A `0x20` mód segédei. Következő címek: `0x009a8a30`, `0x009a8ad0`, `0x009a8bc0`.
9. **NINCS MEG.** A `YUV` forrássíkjainak feltöltése. Következő címek: `0x00737120`, `0x007383b0`, `0x009bd150`, `0x009dd4f0`, `0x0097caf0`.
10. **LEZÁRVA.** A görbe képlete binárisból, a kimeneti minták pedig `qemu-i386` futással ellenőrzöttek. Lásd 38.2.33/7.
11. **LEZÁRVA az időegységre és a léptetési útvonalra.** A tényleges automatikus léptetés periódusa és a `callback` üteme **NINCS MEG**. Lásd 38.2.33/5.
12. **LEZÁRVA.** A `0.6` és `2^32` küszöbök forrásai rögzítettek. Lásd a 38.2.31 listáját.
13. **NINCS MEG.** Az `A` tömb írói és a dátum-hozzárendelés. A legközelebbi sorszám kiválasztásának útja ismert. Következő címek: `0x007fdd00`, `0x008001c0` és az `A` tömb teljes bináris írókeresése.
14. **LEZÁRVA.** A `prev`, `next` és `timeline` parancs közvetlen útjai ismertek. Lásd 38.2.32/5 és 38.2.33/4.
15. **LEZÁRVA a `qshow` billentyűútjára.** A szóköz, a nyilak és az Escape közvetlen ágai ismertek. A főablak globális billentyűútja a 16. pontban nyitott. Lásd 38.2.33/6.
16. **NINCS MEG.** A főablak globális billentyűi és a listaikon célja. Következő címek: `0x005e60d0`, `0x005e6710`, a `0x005c9740` Enter-ág és a listaikon eseménycélja.
17. **NINCS MEG.** A teljes képernyős mód bizonyítása és a kilépés utáni nézet. Új út: `0x00802c20` -> `0x009833a0`; a virtuális hívások céljai továbbra is nyitottak. Lásd 38.2.33/6.
18. **NINCS MEG, nem blokkoló az Időrendhez.** Az `editoneup` hívó osztálya. Következő cím: `0x00af45f0` és az 56 hívóhely.
19. **LEZÁRVA a binárisból levezetett pályára és görbére.** Az eredeti kód `qemu-i386` futása a görbe értékeit ellenőrizte. A kártya forrása és képernyőn mért mozgása **NINCS MEG**. Lásd 38.2.33/7.
20. **LEZÁRVA a `qshow` callback létrehozására és regisztrációjára.** A `0x007fae76` a `0x00803b00` konstruktorral létrehozott objektumot `1` jelzővel a `0x0097d150`-nek adja. Az ütemező meghívási periódusa **NINCS MEG**. Lásd 38.2.33/5.

**Mérleg a 16. kör után:** 20 tétel, 10 lezárva a megadott szűk kérdésre, 10 nyitott. A lezárás több pontnál nem jelenti a teljes viselkedés lezárását: a fenti tételekben külön megneveztem a nyitva maradó részfeladatot.

#### 38.2.33 Az Időrend bináris feltárása, 16. kör: forráslánc, vezérlők, `callback` és visszatérés (#5401, 2026-10-21)

**Hatókör és módszer.** A kör a `2026-10-21-idorend-16.txt` helyi dekompilációs jegyzet címhelyeit, az eredeti `Picasa3.exe` függvényeit és a bináris indexet használta. Az utasításokat a helyi `pe_dis` eszköz olvasta. A teljes `.text` címhivatkozás-keresése a `paszta.memoria_kapu()` hívással indult; egy korábbi, `detail=False` próbálkozás operandus-lekérdezési hibával leállt, ezért nem szolgált leletként. A helyes pásztázás eredményei lent szerepelnek. Az eredeti program egy teljes ablakos futása nem történt meg.

**1. A képhalmaz, elemszám és sorrend: NINCS MEG.** A `0x008037e0` létrehozza a `qshow` nézetet és elindítja az `overlay`-ek építését. A `[this+0x3ec]` indexelt azonosítólistát, a `[this+0x3f0]` mezőt (HELYESBÍTVE, 38.2.34 §1: nem sima elemszám, a 0. bit jelző, az elemszám `[this+0x3f0] >> 1`), a `[this+0x3f4]` aktuális indexet tartja; a `0x00802230` a listából az aktuális azonosítóval kér tartalmat. A `0x008014d0` `0xf8` bájtos rekordot épít. E címek egyike sem állapítja meg, melyik album vagy mappa szolgáltat, hány kép kerül bele futáskor, illetve milyen dátummező szerint rendez. A szolgáltató típusa, az egyes rekordok és az `A` csúszkatömb jelentése továbbra is **NINCS MEG**. Következő célzott vizsgálat: `0x008037e0`, `0x00802230`, `0x008014d0`, valamint a `[this+0x3ec]` és `+0x2ec` mezők írói.

**2. A kártya képe, felirata és kerete: NINCS MEG.** A `0x009aa720` a neki átadott `bitmap` leíróból választ `GDI` objektumot, majd `BitBlt` hívást végez. A közvetlen hívó `0x009aa670` képleírókat és téglalapokat ad át, nem a `+0x2ec` kártyarekord címét. A `0x00800950` `FillRect`-tel kitölt egy téglalapot. Így e lánc nem azonosítja a kártya képének, feliratának vagy keretének forrását. A `+0x2ec` rekordot olvasó teljes binárisbeli függvény **NINCS MEG**. Következő vizsgálat: a rekord címének és a `bitmap` leíró előállításának hívói, különösen `0x008014d0`, `0x008001c0` és a rajzolási út.

**3. Az `overlay`-rétegek sorrendje: NINCS MEG.** A korábbi jelöltek, `0x00a42c20`, `0x009a9c90` és `0x00a3f490`, általános `ytResampler` útba tartoznak. A függvénytörzsek képméreteket, forráspuffereket és transzformációkat kezelnek; ez nem ad rétegsorrendet. A `0x007fb210` az `overlay`-objektumokat felépíti és erőforrásokat tölt be, de a tényleges rajzolási sorrend címét nem azonosítottam. Cáfoló ellenőrzésként a jelölt függvények törzsét és hivatkozási környezetét vizsgáltam: a rajzolási sorrend hipotézisét a `resampler` adatkezelés cáfolja. Ez a próba nem bizonyítja, hogy másik függvényben nincs sorrendkezelés. Következő vizsgálat: `0x007fb210`, `0x008001c0`, `0x00800a30` és a rétegkirajzoló bejárása.

**4. Vezérlők.** A `0x007fde80` a `qshow` egéreseményeit osztályozza, a `0x007fda80` négy találati téglalapot vizsgál. A két első `hitbox` a `0x007fb820` ágra, a jobbra és balra eső `hitbox` a `0x007fd150`, illetve `0x007fd120` léptetőre vezet. A hozzájuk tartozó `startbutton` és `exit` erőforrás-nevek szerinti párosítás a rekordgeometrián alapul. **LEZÁRVA (38.2.35 §4):** a téglalapok mezői az overlay-objektum `+0x08`, `+0x0c`, `+0x18` és `+0x1c` mezőivel esnek egybe, a nevek a 38.2.22 §5 leképezéséből jönnek. A névvel ellátott `oneup/timeline` parancs a `0x008032e0` diszpécserből a `0x007fda00` ágra vezet; ez nem bizonyítja, hogy a `timelinedot` képe ugyanazt az eseményt váltja ki. A listaikon eseménycélja, a pont kattintási célja és a billentyűvel való aktiválásuk **NINCS MEG**. A `0x007fdd00` a csúszka vízszintes helyéből az `A` tömb értékeihez legközelebbi sorszámot választja, de az értékek dátumjelentése és írói **NINCS MEG**.

**5. Automatikus léptetés és `callback`.** A `0x007fae76` egy 0x28 bájtos objektumot hoz létre, meghívja rá a `0x00803b00` konstruktort, majd az objektumot és az `1` jelzőt átadja a `0x0097d150` regisztrációs útnak. A konstruktor a `0x00803b0f` ponton ideiglenesen az alap `ytCallBase` `vtable`-t állítja be, majd a `0x00803b3d` ponton a `ytCallback<QDrawable>` `vtable`-t (`0x00cbd6c8`). Ennek metódustáblájában a `0x00803ab0` szerepel. A `0x0097d150` az `1` jelzőnél a `callback`-objektumot a globális listába helyezi. Ez lezárja, melyik objektum regisztrálódik.

A `0x007fb540` `worker` ciklusában a `0x007fb578` utasítás `Sleep(0x32)` hívást készít elő. Ez 50 ms alvási argumentum, nem a képléptetés periódusa. A ciklus csak a jelző beállásakor hívja a `0x00802230(this,1)` függvényt. A `0x00803ab0` `callback` `QPC` időt kér, és a `0x00802060` küszöbvizsgálatához vezet. A `0x004019b0` által szolgáltatott `Preferences\SlideshowEffectTime` érték másodpercben van, de ez a küszöb nem bizonyítja, hogy a `callback` vagy a léptetés milyen gyakran fut. A tényleges periódus **NINCS MEG**. Következő vizsgálat: a `0x0097fc30` pump hívója, a `callback`-lista végigjárása, valamint a `0x007fb540` jelzőjének beállítói.

**6. Szóköz, bemutatóba lépés és kilépés.** A `0x00801270` `WM_KEYDOWN` ága az `Escape` `0x1b` billentyűt a `0x007fb820` ágra küldi. A szóköz `0x20` a `[this+0x3bb]` állapotot váltja a `0x00801130`-on át; a folytató `0x00803110` időadatot rögzít, majd ugyanezt az állapotváltást és az aktuális indexet használja. Bekapcsoláskor a `0x00801130` meghívja a `0x00802c20`-at, majd a `[this+0x3ba]` állapottól függően a `0x00aa6f40`-et. A `0x00aa6f40` közvetlenül nem nyit teljes képernyős ablakot, így a teljes képernyős bemutató célja ebből az útból nem következik. A bal egérgomb `0x201` lenyomása is ide vezet, ha `[this+0x3b8]` nulla. A `0x008032e0` `oneup/auto` és `oneup/auto2` parancsa a `0x00803110`-et hívja. A `oneup/timeline` külön a `0x007fda00` inicializáló ágat hívja; a dupla kattintás `0x203` vagy `0x204` ugyanezt az ágat éri el, ha `[this+0x3b8]` nulla.

A bal és fel nyíl a `0x008011b0` léptető útjára, a jobb és le nyíl a `0x00801210` útjára vezet (`0x00801270`). A mozgásban lévő kártya az animációs léptetést, az álló nézet az előző vagy következő indexet használja; lásd 38.2.32/5. Ez a `qshow` saját billentyűútja, nem a főablak globális billentyűkezelője.

A `0x008032e0` `oneup/exit` ága először a fogadó objektum `vtable` `+0x24` helyét hívja, majd a kapott objektum `vtable` `+0x14` helyét két nulla argumentummal. Az `Escape` útja a `0x007fb820` függvényen át ugyancsak virtuális híváshoz jut. A célfüggvényeket a vizsgált címek nem oldják fel. A teljes képernyős ablakmód, a kilépés utáni célablak és az Időrendbe visszaállított index vagy nézet **NINCS MEG**. A `0x009833a0` a `0x00802c20` egyik ágán szerepel; a virtuális `+0x28` hívás címzettjét és jelentését külön fel kell oldani. A `0x00aa6f40` önmagában nem teljes képernyős ablaknyitó, közvetlenül csak lebegőpontos környezeti segédműveletet és egy virtuális `+0x84` hívást tartalmaz.

**7. Pálya, méret, átlátszóság és görbe.** A binárisból levezetett pálya és időfüggés a 38.2.32-ben szereplő képletekkel változatlan: `pos(t)=B0+sum(E(u_j)*dx_j)`, ahol `u_j=(t'-v_j)/(end_j-v_j)`, `t'=t+0.02`, a kártya paramétere `t_i=i*S+O`, a görbe kimenete `(x,y,w)`, a méret `w*Z`, az `alpha=ROUND((1-pow(z,1.5))*256)`, ahol `z=max(0,(1/w-1)/9)`. A képletek útja a `0x0072df60`, a `0x009e5ac0` és a 38.2.32-ben felsorolt konstanscímek. A képernyőn mért kezdőhely, a kártyarekordhoz kötött forrás, valamint az `affine` mátrixból eredő forgatás **NINCS MEG**.

A `0x0072df60` görbéjét az eredeti bináris `qemu-i386` futtatásával külön is mértem. A `0x009e5ac0` normalizáló függvény ugyanabban a mérésben adta a `K=1.00057676899` értéket. A mért bemenet és kimenet:

| `u` bemenet | `E(u)` kimenet | forrás |
|---:|---:|---|
| `0.0` | `0.0` | mérés (`qemu-i386`, `0x0072df60`) |
| `-0.25` | `0.0` | mérés (`qemu-i386`, `0x0072df60`) |
| `0.125` | `0.368091643` | mérés (`qemu-i386`, `0x0072df60`) |
| `0.25` | `0.76789844` | mérés (`qemu-i386`, `0x0072df60`) |
| `0.5` | `0.969087183` | mérés (`qemu-i386`, `0x0072df60`) |
| `0.75` | `0.996315122` | mérés (`qemu-i386`, `0x0072df60`) |
| `0.875` | `0.999008954` | mérés (`qemu-i386`, `0x0072df60`) |
| `1.0` | `1.0` | mérés (`qemu-i386`, `0x0072df60`) |

Ez az izolált függvénymérés nem futtatja a `qshow` ablakot. `Wine`-felvétel és sűrű képkockasorozat nem áll rendelkezésre, a mérőadat-archívumban a korábbi `job-220` képek sem voltak meg.

**Bizonyítottsági fok.** A 16. kör összesített foka **feltételes**, mert a képek forráshalmaza, a kártyafogyasztó, az `overlay`-sorrend, a tényleges léptetési periódus és a visszatérési ablak nyitott. A `callback`-regisztrációt két külön bizonyíték egyezteti: az utasításszintű objektum-létrehozási és regisztrációs út (`0x007fae76`, `0x00803b00`, `0x0097d150`), valamint a teljes `.text` pásztázásban talált `vtable`-beállítás (`0x00803b3d`) és az `RTTI` metódustáblája (`0x00cbd6c8`, `0x00803ab0`). A görbe képletének kimenetét a diszasszemblálás és a bináris kóddal végzett `qemu-i386` mérés egymástól függetlenül ellenőrzi. Ezek a megerősített részleletek nem zárják le a nyitott funkciókat.

**Cáfoló kísérlet.** Azt vizsgáltam, hogy a `0x00a42c20`, `0x009a9c90` vagy `0x00a3f490` kódja rendezi-e az `overlay`-rétegeket. A függvények képpuffer-, képméret- és transzformációs műveleteket végeznek; nem olvasnak `overlay`-listát vagy rétegsorszámot. A hivatkozási környezet és a függvénytörzsek ugyanazt mutatják, ezért a konkrét címekre vonatkozó állítást az ellenőrzés megerősíti: ezek nem az `overlay`-sorrend meghatározói. Globális negatív állítást ebből nem teszek.

**A következő, blokkoló `Ghidra`-kérdések.**

- ~~`Ghidra-kör kell: 0x00802230 - a lista szolgáltatójának típusa, forráshalmaza, elemszáma és rendezési mezője [blokkoló]`~~ **NINCS MEG (38.2.34 §1):** a darabszám, az index és az azonosító-mező megvan; a két objektum osztálya és a lista forrása nincs meg. `Ghidra-kör kell: 0x008018a0 - a [this+0x3ec] lista forrása, belső QPC-ciklusa és rendezése (teljes C-kód); 0x00802230-ban a [this+0x2e0] és [this+0x2e4] objektumok osztálya [blokkoló]`
- ~~`Ghidra-kör kell: 0x008014d0, 0x008001c0, 0x009aa720 - ki olvassa a +0x2ec rekordot, és honnan jön a kártya képe, felirata, kerete [blokkoló]`~~ **NINCS MEG (38.2.34 §2):** a `+0x2ec` írója a `0x008014d0`; a `0x008001c0` nem olvassa (CÁFOLVA). `Ghidra-kör kell: teljes .text pásztázás a [reg+0x2ec] olvasóira (0xf8-as léptetéssel); 0x009aa720 és a bitmap-leíró előállítása (0x008014d0 apLStack_f8, 0x00a6aa00) [blokkoló]`
- ~~`Ghidra-kör kell: 0x007fb210 - az overlay-objektumok tényleges kirajzolási sorrendje [blokkoló]`~~ **NINCS MEG (38.2.34 §3):** a `0x007fb210` építési sorrendet ad, nem rajzolásit. `Ghidra-kör kell: 0x00aa6180 - a négy tömb (this+0x111, +0x11b, +0x12f, +0x139) rajzolási sorrendje; 0x00410fa0 - a kilenc overlay-objektum neve a +0x530, +0x558, +0x5a8, +0x5d0, +0x580, +0x6c0, +0x6e8, +0x710, +0x738 mezőkön [blokkoló]`
- ~~`Ghidra-kör kell: 0x007fde80 - a timelinedot és a listaikon pontos egér- és billentyűútja [blokkoló]`~~ **NINCS MEG (38.2.34 §4):** a timelinedot és a listaikon nincs a négy téglalapban kötve. `Ghidra-kör kell: 0x007fde80 és 0x007fda80 - a timelinedot és a listaikon egér- és billentyűútja, a négy téglalap törzse [blokkoló]`
- ~~`Ghidra-kör kell: 0x007fdd00 - az A tömb írói, dátumjelentése és a csúszkához kötése [blokkoló]`~~ **NINCS MEG (38.2.34 §4):** a csúszka `x` -> index leképezése megvan (`[this+0x514]`, `[this+0x510]`, a `[this+0x3a8]` tömb rekordja). Az `A` írói és a dátumjelentés nincs meg. `Ghidra-kör kell: teljes .text pásztázás a [this+0x388], [this+0x38c], [this+0x3a8] és [this+0x3ac] íróira [blokkoló]`
- ~~`Ghidra-kör kell: 0x0097fc30, 0x007fb540, 0x00803ab0 - a callback-pumpa periódusa és a qshow automatikus léptetésének pontos üteme [blokkoló]`~~ **NINCS MEG (38.2.34 §5):** a léptetés üteme `[this+0x3c1] == 0` esetén T másodperc (LEZÁRVA); a callback-regisztráció és a pumpa szabályai megvannak. Nincs meg a `0x0097fc30` `param_1` értéke, a `0x3c1` ág ütemének írói és a worker `0x007fb540` viszonya. `Ghidra-kör kell: 0x0097fc30 hívója a qshow alatt és a param_1 értéke; 0x007fb540 - a worker indítója és viszonya a 0x00802630 léptetéséhez; teljes .text pásztázás a [this+0x3c1] és [this+0x3bb] íróira [blokkoló]`
- ~~`Ghidra-kör kell: 0x00802c20, 0x009833a0, 0x00aa6f40 - a teljes képernyős bemutató célja és az Időrendbe visszatérés [blokkoló]`~~ **NINCS MEG (38.2.34 §6):** a `0x009833a0` törzse megvan (objektumcsere, `vt+0x28`, `0x00983430`). A cél és az EDI forrása nincs meg. `Ghidra-kör kell: 0x00802c20 - az EDI forrása a 0x009833a0 hívásakor; 0x00983430 törzse; a vt+0x28 célja [blokkoló]`
- ~~`Ghidra-kör kell: 0x008032e0, 0x007fb820 - az exit vtable +0x24 és +0x14 hívásainak célja, a visszatérési nézet és index [blokkoló]`~~ **NINCS MEG (38.2.34 §6):** a kilépés sorrendje megvan (`0,6·T` várakozás, `vt+0x24`, majd `vt+0x14(0,0)`, a `[this+0x2dc]` tartalékkal). A két célobjektum osztálya nincs meg. `Ghidra-kör kell: a qshow nézet vtáblája (0x007fa7f0 konstruktora), a vt+0x24 és vt+0x14 célja, a [this+0x2dc] objektum vtábla-célja [blokkoló]`
- ~~`Ghidra-kör kell: 0x005e60d0, 0x005e6710 - a főablak globális Space, nyíl és listaikon billentyűútja [blokkoló]`~~ **NINCS MEG (38.2.34 §6):** a `0x005e6710` switchében nincs Space, Escape és nyíl. A listaikon billentyűútja és a `0x005e60d0` törzse nincs meg. `Ghidra-kör kell: 0x005e60d0 - a Space, Escape és nyíl kizárása a teljes ágon; a listaikon billentyűútja [blokkoló]`

`Ghidra`-kört igényelnek még a 38.2.31 nyitott, nem Időrend-specifikus tételei: `0x009dc1c0`, `0x009dc4b0`, `0x00d695d4`, `0x009a8a30`, `0x009a8ad0`, `0x009a8bc0`, `0x00737120`, `0x007383b0`, `0x009bd150`, `0x009dd4f0`, `0x0097caf0`, továbbá a nem blokkoló `0x00af45f0`.

#### 38.2.34 Az Időrend bináris feltárása, 17. kör: a lista és a kártyák, a léptetés üteme, a pumpa, a kilépés (#5401, 2026-10-21)

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-17.txt` volt: a `0x00802230`, `0x008014d0`, `0x008001c0`, `0x007fb210`, `0x007fdd00`, `0x0097fc30`, `0x009833a0`, `0x007fb820`, `0x005e6710`, `0x007fd150`, `0x007fd120` és `0x00803ab0` dekompilált törzsei és hívólistái. Ezeket a `pe_dis` diszasszemblálással ellenőriztem: a léptetési láncot (`0x00802060`, `0x008020f2`, `0x00802630`), a callback-konstruktort (`0x00803b00`), a regisztrációt (`0x007fae40`), a qshow-építőt (`0x008037e0`), a lista-írót (`0x008018a0`) és a callback vtábla +4 slotját (`0x00cbd6cc` = `0x00803ab0`). A konstansokat `f32` és `f64` olvasással mértem. Az atlasz (`atlasz_keres.py`) lefutott a fenti címekre; a `0x009833a0` a lapokon nincs említve. Nem olvastam újra: a `0x009aa720`, `0x007fde80`, `0x007fda80`, `0x007fd0c0`, `0x00801f50`, `0x00983430`, `0x0097d150`, `0x009a51b0`, `0x00aa6180` és `0x007fb540` törzsét, továbbá a `0x00802c20`, `0x00801130` és `0x00801270` hívóhelyeit. Az eredeti Picasa ablakának futtatása nem történt meg.

A dekompilált törzsekben a `param_1[N]` a `this` mezője `N*4` bájt eltolással. Ebben a szakaszban `[this+0xNN]` alakban írom. A „C-sor" a bemeneti fájl sorszáma, a „cím" a bináris virtuális címe.

**1. A képhalmaz: NINCS MEG (a forrás hiányzik, a szerkezet megvan).**

- Az azonosítólista a `[this+0x3ec]`, az aktuális index a `[this+0x3f4]`. A `0x00802230` a 90. C-sorban a `[this+0x3ec] + [this+0x3f4]*4` címről olvassa az azonosítót. Megerősített.
- A `[this+0x3f0]` nem sima elemszám (HELYESBÍTVE, lásd 38.2.33 §1): a 0. bit jelző, az elemszám `[this+0x3f0] >> 1`. Bizonyíték: a `0x00802230` 85. C-sora (`(uint)param_1[0xfc] >> 1 <= param_1[0xfd]`, ekkor `return 4`), és a `0x008014d0` 367. C-sora (`local_138 < [this+0x3f0] >> 1`). Megerősített.
- A listát a `0x008018a0` írja. Megerősített írások: `[this+0x3f4] := 0` (cím `0x0080190d`, a nulla az `ebx`-ben van, `0x008018eb`), `[this+0x3f0] &= 1` (`0x008018fa`), a lista-mutató újraállítása (`0x00801907`, `0x00801b77`), a darabszám beírása (`0x00801bc4`), és a kártyaépítés hívása (`0x00801c95`, a cél `0x008014d0`). A hívói a 38.2.21 szerint `0x008037e0` (`0x00803953`), `0x007fde80` (`0x007fe33e`) és `0x00801cb0` (`0x00801ce5`); ezeket most nem mértem újra.
- ~~A `0x008018a0` belső ciklusa QPC-időzített és több vtábla-hívást tartalmaz.~~ **HELYESBÍTVE (38.2.35 §1):** nincs QPC. A `0x008018a0` IAT-hívásai a `0xc4055c`, `0xc402a8` és `0xc40284` címen vannak, a QPC IAT-címe (`0xc40298`) nincs közöttük (diszasszemblálás). A vtábla-hívások zárolást végeznek. A ciklus másol, nem rendez; a forrás-gyűjtemény NINCS MEG.
- Az azonosítót két objektum kapja (megerősített slot-hívások):
  - `[this+0x2e4]` vtábla 0. slot, `(id, &rekord, 1)`, a kártyaépítésben (`0x008014d0`, C-sor 269-270);
  - `[this+0x2e0]` vtábla +4 slot, `(id, &rekord, &t)`, a normál átmenetben (`0x00802230`, C-sor 126);
  - `[this+0x2e4]` vtábla +8 slot, `(id, &rekord, 2277)`, a `[this+0x3c1]` jelzős ágban (`0x00802230`, C-sor 136). A 2277 a `0x00d35808` f32 konstans (2276,556) ROUND-ja; a dekompilátor nem adja meg a konstans típusát.
- NINCS MEG: a két objektum osztálya, és az azonosítók forrása (melyik gyűjtemény, album, mappa vagy dátumcsoport). Ghidra-kör kell: `0x008018a0` teljes C-kódja.

**2. A kártya képe, felirata, kerete: NINCS MEG.**

- A `0x008014d0` építi a `[this+0x2ec]` kártyatömböt. Rekordonként 0xf8 bájt. A tömb konstruktora a `0x007fa5b0` (C-sor 321: `FUN_004010e0(0xf8, FUN_007fa5b0)`). A darabszám `[this+0x2f0] >> 1`. Megerősített.
- A `[this+0x2f0]` 0. bitje tiltó jelző: ha 1, a ciklus nem ír rekordot (C-sor 287), a kezdeti nullázás (C-sor 251) pedig csak a számlálót törli, a bitet megtartja. Megerősített.
- A régi tömböt a `0x00803c10` szabadítja fel (C-sor 248-249). Az elemeket a `0x00803b50` másolja (C-sor 328, 341). A hivatkozásszámlálóval kezelt objektumot a `0x0097caf0` engedi el (C-sor 350, 358). Megerősített.
- **Olvasó:** a bemeneti C-kódban a `[this+0x2ec]` mezőt csak a `0x008014d0` olvassa és írja. A `0x008001c0` törzsében nincs `0x2ec` eltolás; a fájlban az egyetlen előfordulások a 248-341. C-sorok, mind a `0x008014d0`-ban. Ezért a 38.2.33 §2-ben és a kör bemenetében feltételezett olvasói szerep a `0x008001c0`-ra CÁFOLVA. A `[this+0x2ec]` olvasóit a teljes `.text` pásztázása adja meg.
- A `0x007fdd00` egy másik, 0xf8-as tömböt olvas: `[this+0x3a8] + i*0xf8` alakban (darabszám `[this+0x3ac] >> 1`), és a rekordcímet a `[this+0x510]` mezőbe írja (C-sor 783-789). Ez nem a `[this+0x2ec]` tömb. Megerősített.
- A kártyaépítés véletlen számokat használ (`0x008014d0`, C-sor 276-285; szorzók: `0x00c72150` = 0,5 és `0x00cf3fd0` = 0,15). Az eredményeket helyi változókba írja (`fStack_28`, `fStack_24`, `fStack_30`, `fStack_2c`). Hogy a rekordba kerülnek-e, a törzsből nem látszik: NINCS MEG.
- NINCS MEG: a kártya képe, felirata és kerete. A `0x009aa720` törzse ebben a körben nincs újramérve; a 38.2.33 §2 állítása (`BitBlt` a `bitmap` leíróból, közvetlen hívó `0x009aa670`) változatlanul feltételes. Ghidra-kör kell: `0x009aa720`, `0x007fa5b0` és `0x00a6aa00`.

**Az átmenet véletlen eltolása (HELYESBÍTVE, 38.2.62).** A `0x00802230` az előző eltolást a `[this+0x408]`/`[this+0x40c]` mezőbe másolja (`0x008022c3`-`0x008022d5`), majd két `rand()`-ot hív: az első (`r1`, `0x008022db`) a `y`, a második (`r2`, `0x008022f2`) az `x` értéke. A bitekből képzett float `u = 1 + r/32768`, nem `[0,1)`-beli `u`; ezért az előző `(u-1)` negatív előjelű értelmezése téves volt. A helyes képletet, a konstansokat és a vezérelt QEMU-ellenőrzést a 38.2.62 §1 rögzíti. A régi negatív tartományállítás visszavonva.

**3. Az overlay-rétegek sorrendje: NINCS MEG.**

- A `0x007fb210` az overlay-objektumokat építi. Kilenc `0x00410fa0` hívás fut a `[this+0x530]`, `[this+0x558]`, `[this+0x5a8]`, `[this+0x5d0]`, `[this+0x580]`, `[this+0x6c0]`, `[this+0x6e8]`, `[this+0x710]` és `[this+0x738]` címeken. Ezután a `0x009a9c90` (`[this+0x648]`), a `0x00a3f490`, a `0x00a42c20`, majd a `0x009dc000` és a `0x00425160` hívás következik. Ez ÉPÍTÉSI sorrend, nem rajzolási sorrend. Megerősített.
- A `0x007fb210` tizenkét pozíciós mezőjét `ROUND(v * 1,0)` alakban írja át (a szorzó a `0x00d34040` f32 1,0). A layout-skála tehát ebben a futtatható képben 1,0. Megerősített.
- A rajzoló a `0x008001c0`. A négy tömböt a `0x00aa6180` kapja a 3-6. paraméterben, a két hívóhelyen (`0x00800541`, `0x00800899`). A bájt-eltolásuk **0x444, 0x46c, 0x4bc, 0x4e4**: a korábbi `[this+0x111]` … `[this+0x139]` a dekompiláló dword-indexe volt (**HELYESBÍTVE, 38.2.35 §3**). A `0x00aa6180` dekompilált törzse nem olvassa a 3-6. paramétert, ezért a sorrend nem a törzsben látszik: NINCS MEG. Ghidra-kör kell: `0x00aa5fb0` és a `0x00aa6180` asm-je.
- Cáfoló ellenőrzés: a `0x007fb210` törzse nem ad rajzolási sorrendet, csak építést és skálát. Ez nem zárja ki, hogy a hívott függvényekben van sorrend.

**4. Timelinedot és listaikon kattintási célja: NINCS MEG.**

- A csúszka (`0x007fdd00`). Az `x` koordinátát a `[this+0x6d8]` és a `[this+0x6d8] + [this+0x6c8]` közé szorítja. A `t = (x - lo) / (hi - lo)` arányhoz a normált `A[i] / A[n-1]` értékek legközelebbi tagját keresi. Az `A` a `[this+0x388]` mutató által mutatott double-tömb, `n = [this+0x38c] >> 1`, a kezdeti minimum a `0x00cf3e88` (f64 10^7). Eredmény: `[this+0x514] := i`, és `[this+0x510] := [this+0x3a8] + i*0xf8`, ha `i < [this+0x3ac] >> 1`, különben 0. Megerősített. A `[this+0x728]` mezőt a `0x00c29990` visszatérése kapja (a törzse nincs megnézve).
- A léptetők: a `0x007fd150` a `0x007fd0c0(-S, 2,0)`, a `0x007fd120` a `0x007fd0c0(+S, 2,0)` hívást végzi, ahol `S = (double)[this+0x30]` és a `2,0` a `0x00cf3a48` (f32). Megerősített hívási forma. A `0x007fd0c0` törzse NINCS MEG.
- A négy találati téglalapot a `0x007fda80` vizsgálja (38.2.22 szerint). Ennek törzse ebben a bemenetben nincs. A 38.2.33 §4 szerint az első két téglalap a `0x007fb820` ágra megy. Ha a `startbutton` is ebbe tartozik, akkor a bemutató indítása és a kilépés ugyanazt az ágat járja. Ezt a `0x007fda80` törzse dönti el: NINCS MEG.
- A `timelinedot` és a listaikon a bemenetben egyik téglalaphoz sincs kötve. A kattintási cél NINCS MEG. Ghidra-kör kell: `0x007fde80` és `0x007fda80`.

**5. Automatikus léptetés és callback: a léptetés üteme LEZÁRVA, a pumpa és a `0x3c1` ág NINCS MEG.**

*5.1 A regisztráció (megerősített).*

- A `0x007fae40` blokk (a `0x007fa7f0` függvényen belül): `push 0x28`, az objektum a `0x00c0769f` foglalóval (cím `0x007fae5b`), `push ebp` (a tulajdonos a nézet), `call 0x00803b00` (cím `0x007fae6a`), majd `push 1`, `push eax`, `call 0x0097d150` (cím `0x007fae76`). A regisztráció jelzője 1. Ugyanebben a blokkban a `[this+0x2dc]` mezőt a `0x00802c60` eredménye tölti (38.2.21 szerint OneUpUI).
- A `0x00803b00` konstruktor: a vtábla előbb `0x00c804c4` (alap `ytCallBase`), majd `0x00cbd6c8` (`ytCallback<QDrawable>`). A `[obj+0x8]` a tulajdonos. A `[obj+0x10]` és a `[obj+0x18]` QPC-érték (double). A `[obj+0x20] := 0`: ez a periódus ezredmásodpercben.
- A `0x00cbd6c8` vtábla +4 slotja `0x00803ab0` (olvasva: `0x00cbd6cc` tartalma `0x00803ab0`).
- A `0x00803ab0`: `[obj+0x18] := most` (QPC). Ha a `[tulajdonos+0x3bf]` nulla, visszatér a `0x00802060` értékével, különben `-1`-et ad.
- A `[this+0x3bf]` bájt, a lezárást jelzi: a `0x007fb820` elején 1 lesz.

*5.2 A pumpa, `0x0097fc30` (megerősített).*

- `param_1` a `MsgWaitForMultipleObjects` időtúllépése ezredmásodpercben (C-sor 1136-1139). `param_2` a futásjelző bájt: `*param_2 == 0` esetén a pumpa kilép.
- Minden körben: QPC, üzenetciklus `PeekMessageA`, 10 ms-os kerettel (`0x00cf40b8` = 0,01, C-sor 938). Utána a callback-lista.
- Egy callback akkor fut, ha `[obj+0x20] <= (most - [obj+0x18]) * 1000` (`0x00cf3e10` = 1000,0).
- Hívás: `vt+4((most - [obj+0x10]) * freq)`. Visszatérés: `-2` a callback-kör megszakítása; `-1` a callback eltávolítása; `0` nincs várakozás; `>= 0` új periódus lesz (`[obj+0x20]`).
- Várakozás (`MsgWaitForMultipleObjects`, `param_1` ezredmásodpercig) csak akkor van, ha a kör rövidebb 5 ezredmásodpercnél (`0x00cf4b50` f32 = 0,005), és nincs 0 visszatérés.
- `WM_CLOSE` (0x10) ág (C-sor 912-925): beágyazott pumpában (`DAT_00d678a4 > 1`), ha a címzett a látható `DAT_00d6784c` ablak, és a `GetWindowLongA(hwnd, -0x15)` objektum `+0x80` mezője nem nulla, akkor `0x00983140(obj, 0)` és 0xf4242 visszatérés. `WM_QUIT` (0x12) 0-val tér vissza (C-sor 943).

*5.3 A léptetési döntés, `0x00802060` (diszasszemblált, megerősített).*

1. `[this+0x3bb] != 0` (a szóköz-állapot): visszatér 1-gyel. A periódus így 1 ms lesz, léptetés nincs.
2. `[this+0x3b8] != 0`: a `0x00801cb0` hívása (törzse nincs megnézve). Ha utána is nem nulla, az időzített lépés kimarad.
3. `[this+0x518] != 0`: lépés.
4. `elapsed = (most - [this+0x520]) / freq` (a `0x009a51b0` hívásával). `T` a `0x004019b0` visszatérése a `[this+0x760]` objektumról, előjel nélkül (negatívnál `+2^32`). Ha `elapsed > T`, lépés. Ha nem, a `[this+0x3c1]` jelző: nem nulla esetén lépés, különben `0x00801f50` hívása és `-2`.
5. A lépés a `0x00802630`. Nem nulla visszatérésnél `-1` (a callback törlődik). Nulla visszatérésnél: `[this+0x518] := 0`, `[this+0x520] := most`, `0x00801f50` hívása, `-2`.

*5.4 A léptetés törzse (megerősített).* A `0x00802630` a `0x00802230(this, 0)` hívást végzi (`push ebx`, `push esi`, `call 0x00802230` a `0x008026e7`-`0x008026e9` címeken; az `ebx` nulla, `xor ebx, ebx` a `0x00802638`-ban). A nulla második argumentum miatt a `0x00802230` nem hívja a `0x00802180`-t (CarefulEnhance), mert az csak nem nulla argumentumnál fut. A `0x00802230(this, 1)` a 38.2.33 szerint a `0x007fb540` workeré: ez egy másik út.

*5.5 Az ütem (a binárisból következik).*

- **A léptetés üteme `[this+0x3c1] == 0` esetén: T másodpercenként egy lépés.** Az utolsó átmenet kezdete (`[this+0x520]`) óta eltelt időnek meg kell haladnia T-t. Az átmenet is T ideig tart: a `0x008001c0` a haladást `elapsed / T`-ként számolja, 1-re vágva. Az egység másodperc a 38.2.33 szerint; a `0x009a51b0` törzsét nem néztem meg, ezért ez feltételes.
- A `Preferences\SimpleSlideshow` értéke (`0x00407a20`, `0x004019b0`) dönti el a görbét: nulla esetén lineáris, nem nulla esetén a görbe 1,5-szeres és 8-szoros skálán van, `0x0040eac0` hívásokkal (ennek törzse NINCS MEG).
- Ha `T = 0`, minden pumpa-körben lépés lenne. Ez a binárisból következik, nem mért.
- A pumpa-kör: a callback minden körben fut (a periódus 0, a `-2` nem módosítja). A várakozás a `param_1` ezredmásodperces időtúllépés, és csak akkor van, ha a kör rövidebb 5 ezredmásodpercnél. **A `param_1` értéke NINCS MEG**: a qshow alatt futó hívót nem azonosítottam.
- **A `[this+0x3c1] != 0` ágban nincs időfeltétel:** ha a `[this+0x3bb]` és a `[this+0x3b8]` ágak nem zárják ki, a lépés minden callback-híváskor megtörténik. Ennek az ütemét a `0x3c1` íróinak ismerete dönti el: NINCS MEG.
- A `0x008037e0` a `0x007fa7f0` hívása után (`0x00803920`) a `0x00802060`-t közvetlenül is hívja (`0x008039f6`): az első ellenőrzés nem vár a pumpára.

**6. Szóköz, teljes képernyős bemutató és kilépés: NINCS MEG (a törzsek megvannak, a célok nincsenek).**

- **Szóköz.** Megerősített: a `[this+0x3bb]` nem nulla értéke mellett a callback 1-et ad, léptetés nincs (5.3 1. pont). A váltót (`0x00801130`) a 38.2.33 szerint a szóköz hívja; ezt ebben a körben nem mértem újra.
- **Teljes képernyős váltás.** A `0x009833a0` törzse megerősített (C-sor 1176-1191): a `[this+0x64]` mezőben tárolt objektumot cseréli az EDI-ben kapott újra. A régi objektum `vt+0x28(0)`, az újé `vt+0x28()` hívást kap, a `[this+0x3b]` bájt nullázódik, majd a `0x00983430` hívódik, és annak nem nulla visszatérését továbbadja. A 38.2.22 §1 szerint a `0x00983430` a teljes képernyős váltás; ennek törzse nincs újramérve. A hívó `0x00802c20`: az EDI forrása és a vt+0x28 célja NINCS MEG.
- **Kilépés.** A `0x007fb820` törzse megerősített, a cél NINCS MEG:
  1. `[this+0x3bf] := 1` (C-sor 1235). A callback ezt olvassa, és `-1`-et ad.
  2. Ha `[this+0x3bb] == 0` (C-sor 1236): a `0x008001c0` kirajzolja a képet (a `this+0x46c` képpufferrel), `[this+0x520] := most` (C-sor 1250-1251), majd addig vár, amíg `elapsed < 0,6·T` (C-sor 1272, a `0x00cf3a70` = 0,6 f64). A várakozó ciklusban a `0x00801f50` fut.
  3. A `this->vt[+0x24]()` hívás, kétszer (teszt és érték). Ha nem nulla, ez a célobjektum. Ha nulla, a `[this+0x2dc]` (38.2.21 szerint OneUpUI) `vt[+0x24]()` hívása a célobjektum. Ha az is nulla, nincs kilépési hívás (C-sor 1278-1288).
  4. A célobjektum `vt[+0x14](0, 0)` hívása (C-sor 1292).

  Tehát a kilépés előtt `0,6·T` másodperc várakozás van. A célobjektum osztálya és a `vt+0x24` / `vt+0x14` slot célja NINCS MEG.
- **Főablak (`0x005e6710`, megerősített switch).** A `WM_KEYDOWN` (`0x100`) ágban a kezelt billentyűk: F1 (`0x70`), F2 (`0x71`), F3 (`0x72`), F4 (`0x73`), F5 (`0x74`), F11 (`0x7a`), és F12 (`0x7b`, ez a `0x005e60d0` ágra ugrik). A `Space` (`0x20`), az `Escape` (`0x1b`) és a nyilak (`0x25`-`0x28`) nincsenek a switchben. A `0x104` (rendszerbillentyű) és az `Enter` (`0xd`) páros a `0x005c9740` ágat hívja. A `0x005e60d0` törzsét nem néztem meg újra; a 38.2.8 szerint (nem újramérve) ott sincs `Space`, `Escape` és nyíl. A `Shift` állapotát a `GetAsyncKeyState(0x10)` értékéből a `[this+0xcea]` bájttal veti össze; ennek írója NINCS MEG.

**7. A 38.2.33 nyitott listájának állapota.** A tételeket a 38.2.33 listájában egyenként átírtam. A részletes, kérdésenkénti mérleg:

| # | kérdés | állapot | hol |
|---|---|---|---|
| K1 | `0x00802230`: a szolgáltató osztálya és a lista forrása | NINCS MEG (38.2.35 §1, §5: a lista nem a `0x00802230`-tól jön) | §1 |
| K2 | `0x00802230`: darabszám, index, azonosító-mező | LEZÁRVA | §1 |
| K3 | `[this+0x2ec]`: írók (`0x008014d0`) | LEZÁRVA | §2 |
| K4 | `[this+0x2ec]`: olvasók (teljes `.text` pásztázás) | NINCS MEG (38.2.35 §2: a pásztázás nincs elvégezve) | §2 |
| K5 | kártya képe, felirata, kerete (`0x009aa720`) | NINCS MEG (38.2.35 §2: nincs felirat; a keret csak a `Debug Blt` ágban van) | §2 |
| K6 | overlay-rétegek rajzolási sorrendje | NINCS MEG (38.2.35 §3: a két ág szerkezete LEZÁRVA, a sorrend nincs) | §3 |
| K7 | timelinedot és listaikon kattintási célja | NINCS MEG (38.2.35 §4: a négy téglalap LEZÁRVA, a timelinedot nincs benne) | §4 |
| K8 | csúszka: `x` -> legközelebbi `A` index | LEZÁRVA | §4 |
| K9 | `A` tömb írói és dátumjelentése | NINCS MEG | §4 |
| K10 | léptetés üteme (`[this+0x3c1] == 0`) | LEZÁRVA | §5 |
| K11 | `[this+0x3c1]` ág ütemének írói; `0x0097fc30` `param_1`; worker `0x007fb540` | NINCS MEG (a worker hívási feltétele LEZÁRVA, 38.2.35 §5; az indító és a többi nincs) | §5 |
| K12 | teljes képernyős váltás célja (`0x00802c20` EDI, `0x00983430`) | NINCS MEG | §6 |
| K13 | kilépés: `0,6·T` várakozás és a `vt+0x14` lánc | LEZÁRVA | §6 |
| K14 | kilépés célobjektuma (`vt+0x24`, `[this+0x2dc]`) | NINCS MEG | §6 |
| K15 | főablak: Space, Escape, nyíl kizárása | LEZÁRVA | §6 |
| K16 | főablak: listaikon billentyűútja, `0x005e60d0` | NINCS MEG | §6 |

**Új Ghidra-körök (a blokkoló tételekhez):**

Állapot a 38.2.35 után (LEZÁRVA vagy NINCS MEG):

- `Ghidra-kör kell: 0x008018a0 - a [this+0x3ec] lista forrása (a local_64 írója), a belső ciklus QPC-je, a rendezés [blokkoló]` **NINCS MEG (38.2.35 §1):** a QPC-ág CÁFOLVA, a rendezés LEZÁRVA, a forrás nincs meg.
- `Ghidra-kör kell: 0x00802230 - a [this+0x2e0] és [this+0x2e4] objektumok osztálya és vtábla-célja (+0, +4, +8 slot) [blokkoló]` **NINCS MEG.**
- `Ghidra-kör kell: teljes .text pásztázás a [reg+0x2ec] olvasóira (0xf8-as léptetéssel), és a 0x00803c10 törzse [blokkoló]` **NINCS MEG.** A `0x007fa5b0` törzse LEZÁRVA (38.2.35 §2).
- `Ghidra-kör kell: 0x009aa720 és a bitmap-leíró előállítása (0x008014d0 apLStack_f8 eleme, 0x00a6aa00) [blokkoló]` **NINCS MEG.** A `0x009aa720` törzse LEZÁRVA (másolás, nincs felirat, a keret csak a `Debug Blt` ágban van); az `apLStack_f8[0]` írója nincs meg.
- `Ghidra-kör kell: 0x00aa6180 - a négy tömb (this+0x444, +0x46c, +0x4bc, +0x4e4) rajzolási sorrendje és tartalma [blokkoló]` **NINCS MEG (38.2.35 §3).** Az offsetek javítva; a két ág LEZÁRVA.
- `Ghidra-kör kell: 0x00410fa0 - a kilenc overlay-objektum neve a +0x530, +0x558, +0x5a8, +0x5d0, +0x580, +0x6c0, +0x6e8, +0x710, +0x738 mezőkön [blokkoló]` **LEZÁRVA (38.2.22 §5).** A nevek és a mezők leképezése megvan.
- `Ghidra-kör kell: 0x007fde80 és 0x007fda80 - a timelinedot és a listaikon egér- és billentyűútja, a négy téglalap törzse, a startbutton ága [blokkoló]` **NINCS MEG.** A `0x007fda80` négy téglalapja és a `startbutton` ága LEZÁRVA (38.2.35 §4); a `0x007fde80` nincs dekompilálva.
- `Ghidra-kör kell: teljes .text pásztázás a [this+0x388], [this+0x38c], [this+0x3a8] és [this+0x3ac] íróira [blokkoló]` **NINCS MEG.**
- `Ghidra-kör kell: 0x0097fc30 hívója a qshow alatt, és a param_1 értéke ezredmásodpercben [blokkoló]` **NINCS MEG.**
- `Ghidra-kör kell: teljes .text pásztázás a [this+0x3c1] és [this+0x3bb] íróira, és 0x00801cb0 törzse [blokkoló]` **NINCS MEG.** A `0x00801cb0` törzse még nincs dekompilálva (38.2.35 új Ghidra-köre).
- `Ghidra-kör kell: 0x007fb540 - a worker indítója és viszonya a 0x00802630 léptetéséhez [blokkoló]` **NINCS MEG.** A `0x00802230(this, 1)` hívás feltétele LEZÁRVA (38.2.35 §5: a `[this+0x51a]` jelző).
- `Ghidra-kör kell: 0x00802c20 - az EDI forrása a 0x009833a0 hívásakor; 0x00983430 törzse; a vt+0x28 célja [blokkoló]` **NINCS MEG.**
- `Ghidra-kör kell: a qshow nézet vtáblája (0x007fa7f0 konstruktora), a vt+0x24 és vt+0x14 célja, és a [this+0x2dc] objektum vtábla-célja [blokkoló]` **NINCS MEG.**
- `Ghidra-kör kell: 0x005e60d0 - a Space, Escape és nyíl kizárása a teljes ágon; a listaikon billentyűútja [blokkoló]` **NINCS MEG.**
- `Ghidra-kör kell: 0x0097d150 - a callback-regisztráció lista-útja [nem blokkoló]` **NINCS MEG.**
- `Ghidra-kör kell: 0x009a51b0 - az eltelt idő egysége (másodperc-e) [nem blokkoló]` **NINCS MEG.**
- `Ghidra-kör kell: 0x0040eac0 - a görbe 1,5-ös ágának függvénye [nem blokkoló]` **NINCS MEG.**
- `Ghidra-kör kell: 0x00801f50 - a rajzolási lépés törzse [nem blokkoló]` **NINCS MEG.**
- Új tételek a 38.2.35 végén: `0x007fde80`, `0x00801cb0`, a `0x008018a0` hívóhelyeinek verem-előkészítése, `0x004b0190`, `0x009c4440`, `0x00801cf0`.

**Bizonyítottsági fok.**

- **Megerősített:** a dekompilált törzsek és a diszasszemblált részletek, minden megnevezett címmel: a kártyarekord-építés, a kezdőpont-véletlen, a callback-konstruktor és -regisztráció, a pumpa-szabályok, a léptetési döntés, a kilépési sorrend, a főablak switch-ága, a csúszka leképezése.
- **Feltételes:** a `T` egysége (másodperc, a 38.2.33 szerint); a `0x00802230` slotjainak célja (a hívás megvan, az osztály nincs); a 38.2.8 és 38.2.22 átvett állításai.
- **NINCS MEG:** a lista forrása, a kártyakép, az overlay-rajzsorrend, a timelinedot kattintása, az `A` tömb írói, a `param_1` ütem, a `0x3c1` ág, a teljes képernyős cél, a kilépés célobjektuma.

**Cáfoló kísérlet.**

1. „A `[this+0x2ec]` olvasója a `0x008001c0`." CÁFOLVA: a törzsében nincs `0x2ec` eltolás.
2. „A léptetés a pumpa ütemétől függ." CÁFOLVA a `[this+0x3c1] == 0` ágra: a `0x00802060` `elapsed > T` feltétele dönt. A `0x3c1 != 0` ágra nem cáfolható, ott nincs időfeltétel.
3. „A `0x007fb210` adja az overlay-sorrendet." CÁFOLVA a törzse alapján: építést és skálát tartalmaz, rajzolást nem.
4. „A `0x00802230` a CarefulEnhance-t minden lépésnél hívja." CÁFOLVA: a léptetés törzse `0x00802230(this, 0)`-t hív, és ez nem hívja a `0x00802180`-t.

**Nyitott kérdések mérlege (38.2.34):** a fenti K1-K16 tábla szerint, `Nyitott kérdések a 38.2.35 után: 6 lezárva · 10 NINCS MEG · 0 nyílt`. A NINCS MEG tételek gépi úton (Ghidra-körrel vagy pásztázással) dönthetők el, tulajdonosi döntés nem kell hozzájuk. A `picasapy-agent` munkasorát (`memory/nyitott-kerdesek-sor.md`) ebben a körben nem frissítettem; ezt a hívónak kell átvezetnie.

#### 38.2.35 Az Időrend bináris feltárása, 18. kör: a képhalmaz, a kártya, a rétegek, a találatok és a lista hívói (#5401, 2026-10-21)

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-18.txt` volt: a `0x008018a0`, `0x00aa6180`, `0x00410fa0`, `0x009aa720`, `0x007fa5b0`, `0x00a6aa00`, `0x007fda80`, `0x007fb540` és `0x007fda00` dekompilált törzsei és hívólistái. Kiegészítette a `2026-10-21-idorend-17.txt` (a `0x00802230` és a `0x008014d0` törzse és hívólistái), a `pe_dis` diszasszemblálása (a `0x008018a0` IAT-hívásai és a `0x007fda00` QPC-hívása), valamint a 38.2.22, 38.2.25, 38.2.30 és 38.2.31 szakasz korábbi mérései. A `0x007fde80` és a `0x00801cb0` törzse nincs beolvasva, ezért a hozzájuk tartozó kérdések NINCS MEG-ek. Az eredeti Picasa ablakát nem futtattuk.

A dekompilált törzsekben a `param_1[N]` a `this` mezője `N*4` bájt eltolással. Ebben a szakaszban a [this+0xNN] bájt-eltolás.

**Korlát.** A dekompiláló több helyi változót olvas úgy, hogy a törzs nem írja őket: a `0x008018a0`-ban a `local_64`, a `local_5c`, a `local_c8`, a `local_bc` és a `local_a0`, a `0x00aa6180`-ban a 3-6. paraméter. A dekompiláló feladta a verem-követést (`Unable to track spacebase fully for stack`). **HELYESBÍTVE (38.2.37 §6):** ezek nem a hívó által a veremben előkészített értékek. A `0x008018a0`-nak nincs stack-argumentuma, és a három hívóhely (`0x007fe33e`, `0x00801ce5`, `0x00803953`) nem tesz verembe argumentumot. A `local_64` a `[esp+0x80]`, a `local_5c` a `[esp+0x88]` helyen van; forrásuk a 38.2.37 §3-ban.

**1. A képhalmaz forrása: az osztályok NINCS MEG, a szerkezet és a szűrés LEZÁRVA.**

A `0x008018a0` két külső objektumot olvas. A kérdés két forrás-objektumát ezekre értelmezem. A `[this+0x2e0]` és a `[this+0x2e4]` objektumok (38.2.34 §1) nem ennek a függvénynek az objektumai: a kártyaépítő (`0x008014d0`) és a léptető (`0x00802230`) használja őket.

- `local_64`: azonosító-tömb. Az adatmutató a +0 mezőben van, a darabszám a +4 mező `>> 1` részében, a 0. bit jelző. Ez ugyanaz a szerkezet, mint a lista `[this+0x3ec]` és `[this+0x3f0]` párja. **LEZÁRVA.**
- `local_5c`: szűrő bájt-tömb. Egy azonosító kimarad, ha a tömb azonosító-indexű bájtja nem nulla. Ha nincs szűrő, vagy az azonosító a tömbön kívül esik, az azonosító bekerül. **LEZÁRVA.**
- A lista sorrendje a forrás sorrendje. A függvény nem rendez: 0-tól a darabszámig sorban ír. **LEZÁRVA.**
- **NINCS MEG:** a két objektum osztálya, és hogy a `local_64` gyűjtemény, album, mappa vagy dátumcsoport-e. A `0x004b0190(kulcs)` hívásnak van mellékhatása (zárolás, két vtábla-hívás), de nincs megmérve, hogy ez állítja-e be a `local_64`-et. **HELYESBÍTVE (38.2.37 §6):** a három hívóhelynél nincs verem-előkészítés (asm-ellenőrizve). A `local_5c` forrása `P+0x29c` (38.2.37 §3). **Ghidra-kör kell:** a `[P+0xc4]+0x48` objektum vt+0x2c célja (a `0x004b01f2` hívása), amely a `local_64`-et tölti.
- Jelölt, nem igazolt: a 38.2.18 `CThumbUI+0x2c0` kollekciója. Ehhez a `local_64`-hez nincs bizonyíték.

**2. A kártya képe, felirata, kerete: a kép és a felirat NINCS MEG, a keret csak a hibakeresési ágban van.**

- **A kártyarekord alapállapota (LEZÁRVA, `0x007fa5b0`).** A rekord 0xf8 bájtos. A `0x007fa5b0` a [+0x00] mezőt `-1`-re, a [+0xa0] mezőt `256`-ra állítja. A [+0xa4], [+0xb4] és [+0xc4] mezők értéke 1,0 (f32). A [+0xa8], [+0xac], [+0xb0], [+0xb8], [+0xbc] és [+0xc0] mezők nullák, a [+0xcc]-tól [+0xe8]-ig minden mező nulla, a [+0xc8] bájt pedig 1. Az 1,0-s mezők egy egységmátrix átlóját adják. Hogy ez affin mátrix, az jelölt (38.2.33 §7). A [+0xcc] és a [+0xd0] mezőt a 38.2.28 szerint a mozgatás írja.
- **A kártyaépítés feltétele (LEZÁRVA, `0x008014d0`).** A ciklus csak akkor fut, ha a `[this+0x3bc]` vagy a `[this+0x3bd]` bájt nem nulla, és van elem. Elemenként a `[this+0x2e4]` objektum 0. slotja `(azonosító, &rekord, 1)` alakban tölt ki egy 0x28 bájtos helyi rekordot. Ezután jön a `0x007fa5b0`, majd a `0x00a6aa00(apLStack_f8, -1, -1, -1, -1)`.
- **A teljes kép másolása (LEZÁRVA, `0x00a6aa00`).** A -1 négy érték azt jelenti, hogy a teljes területet kell rajzolni. A szélesség és a magasság a célobjektum [+0x8] és [+0xc] mezőiből jön, az eltolás nulla. A függvény a `0x009a8a30`, `0x009aabf0`, `0x009a8bc0` és `0x00a6a880` hívottjait használja, ezek törzse nincs beolvasva.
- **A képforrás (NINCS MEG).** Az `apLStack_f8[0]` egy hivatkozásszámlált objektum (`InterlockedDecrement`, a `0x0097caf0` engedi el). A `0x008014d0` törzsében csak olvasás és nullázás van, írás nincs, tehát az objektumot a `0x00a6aa00` vagy a hívottjai hozzák létre. Hogy melyik kép ez, nincs meg.
- **A `0x009aa720` nem a kártya-hívó (LEZÁRVA a közvetlen hívásra).** A `0x008014d0` hívólistáján nincs `0x009aa720`. A `0x009aa720` egy általános másoló: a leíró `+0x18` (x), `+0x1c` (y) és `+0x24` (`HBITMAP`) mezői alapján `BitBlt`-tel másol. A kártyarekordot nem olvassa.
- **A felirat (NINCS MEG).** A három törzsben (`0x009aa720`, `0x00a6aa00`, `0x008014d0`) nincs közvetlen szövegrajzoló import (`TextOut`, `DrawText`, `ExtTextOut`). A `0x00410fa0` a C-sztringet a `0x00985ff0`-val másolja, majd a `0x009c4440`-et hívja, ennek törzse nincs beolvasva. A `0x00410fa0` 141 hívóhelye sztring-literált ad át (az overlay-neveket, a `stars/yes` és a `stars/no` nevet), ez név szerinti betöltőre utal. Ez feltételes. A kártya felirata ezen az úton nincs igazolva.
- **A keret.** **LEZÁRVA a hibakeresési ágra:** a `0x009aa720` egyetlen `Rectangle` hívása a `Preferences\Debug Blt` kapcsolótól függ (`DAT_00d6fc4e`). Ha be van kapcsolva, a másolt téglalap köré 2 pixeles, véletlen színű, `PS_INSIDEFRAME` (stílus 6) tollal, `NULL_BRUSH` (az 5-ös beépített ecset) kitöltéssel keretet rajzol, és 10 ms-ot alszik. A kapcsolót 100 hívásonként olvassa (`_DAT_00d47088`). **NINCS MEG:** a kártya normál keretének forrása.
- **Közös őr.** A `0x009aa720` és a `0x00aa6180` a `0x009aab60` eredményét nézi, és 3 esetén kilép. A `0x009aa670` ugyanezt teszi (38.2.30). A 3-as érték jelentése NINCS MEG.

**3. Az overlay-rétegek: a két ág szerkezete LEZÁRVA, a négy tömb tartalma és a rétegsorrend NINCS MEG.**

A `0x00aa6180` első paramétere `a`, az alfa. A hívó (`0x008001c0`) a `0x007fff30`-ból kapja (38.2.30 §7). Az ág az `a` értékétől függ:

- `a = 0`: soronként egyetlen `0x00aa5fb0` hívás (három argumentum: a sor mutatója, a szélesség és az `x0`). A sort közvetlenül a célképbe másolja.
- `a ≠ 0`: soronként két verem-puffer készül, `local_c` és `local_10`, mindegyik a célkép szélességével. A `local_c`-t a `0x00aa5fb0` három argumentumos hívása tölti, a `local_10`-et ugyanaz a hívás, de negyedik argumentummal, a sor-indexszel. Ezután a `0x009dc040(a, a cél sora, local_c, local_10, szélesség)` keveri a kettőt, a három mutató az `x0` eltolással szerepel.

A célkép leírója: a `[param_2+0x10]` a pixelcím, a `[param_2+0x4]` a sor-lépés pixelben, a `[param_2+0x8]` a szélesség (38.2.30 §7).

- **A négy tömb.** A 3-6. paraméter bájt-eltolásai `0x444`, `0x46c`, `0x4bc` és `0x4e4` (38.2.31 §2, asm). A 38.2.34 §3 ezeket `[this+0x111]`, `[this+0x11b]`, `[this+0x12f]` és `[this+0x139]` alakban írta. Ez a dekompiláló dword-indexe volt, **HELYESBÍTVE (38.2.35 §3, és a 38.2.34 §3)**. A `0x00aa6180` C-törzse nem olvassa a 3-6. paramétert. A 38.2.31 §4 szerint két forrásleíró és két affin transzformáció megy a `0x00aa5fb0`-nek. Hogy melyik tömb melyik, **NINCS MEG**.
- **Rétegsorrend (NINCS MEG).** A `0x00aa6180` egyetlen képpuffert tölt, és nem ad sorrendet. A rétegek sorrendjét a hívó `0x008001c0` adja a két hívóhelyén (`0x00800541`, `0x00800899`) és a `cVar3` ágon. Ennek törzse ebben a körben nincs beolvasva.
- **Általános segéd.** A `0x00aa6180` négy hívója közül kettő (`0x0076e770`, `0x0076e880`) nem a `0x008001c0`-ból hívja. Ez a függvény nem qshow-specifikus.

**4. A négy találati téglalap, a timelinedot és a listaikon kattintása.**

A `0x007fda80` négy téglalapot vizsgál. Ha a `[this+0x3b8]` nulla, a függvény azonnal `0xf4241`-et ad. A téglalapok mezői az overlay-objektum `+0x08` (szél), `+0x0c` (magasság), `+0x18` (bal) és `+0x1c` (felső) mezői. A pontvizsgálat `a < b != (a == b)` alakja `a <= b`-vel egyenértékű, NaN esetén hamis. **LEZÁRVA.**

| sorrend | overlay | X | téglalap mezői (bal, felső, szél, magasság) | művelet | visszatérés |
|---|---|---|---|---|---|
| A | `startbutton` | `0x738` | `+0x750`, `+0x754`, `+0x740`, `+0x744` | `0x007fb820`, majd ha `[this+0x2e8]` nem nulla, a vtábla `+0x18` hívása `(-1, azonosító)` | `1000000` |
| B | `exit` | `0x580` | `+0x598`, `+0x59c`, `+0x588`, `+0x58c` | `0x007fb820` | `1000000` |
| C | `right` | `0x558` | `+0x570`, `+0x574`, `+0x560`, `+0x564` | `0x007fd150` (`-S`) | `1000000` |
| D | `left` | `0x530` | `+0x548`, `+0x54c`, `+0x538`, `+0x53c` | `0x007fd120` (`+S`) | `1000000` |
| - | - | - | nincs találat | - | `0xf4241` |

- **LEZÁRVA:** a táblázat megegyezik a 38.2.22 §4 táblázatával. Az `A` és a `B` ugyanazt az ágat hívja (`0x007fb820`), vagyis a `startbutton` és az `exit` a kilépési ágon megy. Az egyetlen különbség, hogy az `A` értesíti a `[this+0x2e8]` objektumot. Ez megerősíti a 38.2.33 §4 feltevését.
- **LEZÁRVA:** a téglalapok és az overlay-nevek összerendelése a 38.2.22 §5 leképezéséből jön, a mezők egybeesnek.
- **Irány:** a `0x007fd150` a `0x007fd0c0(-S, 2,0)`, a `0x007fd120` a `0x007fd0c0(+S, 2,0)` hívás (38.2.34 §4). A jobbra eső `right` overlay a `-S`-t hívja. A `0x007fd0c0` előjel-szemantikája NINCS MEG, ezért az nem dől el, hogy az irány előre vagy hátra lépteti-e az időt.
- **NINCS MEG: a `timelinedot` és a listaikon.** Egyik téglalapban sincs. A `0x007fda80`-t a `0x007fde80` hívja (`0x007fe15f`, `0x007fe1fd`). Ugyanez a `0x007fde80` hívja a `0x007fda00`-t (`0x007fe158`) és a `0x008018a0`-t (`0x007fe33e`). A `timelinedot` (`0x6e8`) és a listaikon kattintási útja tehát a `0x007fde80`-ban van, amelyet nem dekompiláltunk. **Ghidra-kör kell:** `0x007fde80`.
- **NINCS MEG:** a `[this+0x2e8]` objektum osztálya és a vtábla `+0x18` célja.

**5. A `0x00802230` hívói, és mikor épül újra a lista.**

- **A `0x00802230` hívói (LEZÁRVA, a 17. kör hívólistája):** `0x007fb540` (a `worker`, a `0x007fb56c` helyen, argumentum 1), `0x007fda00` (`0x007fda4f`, argumentum 1), `0x00801130` (`0x00801178`, argumentum 0, a szóköz-váltó), `0x00801cf0` (`0x00801d05`, argumentum 0) és `0x00802630` (`0x008026e9`, a léptetés, argumentum `ebx`).
- **A `0x00802230` nem épít listát (LEZÁRVA).** A közvetlen hívólistáján nincs `0x008018a0` és `0x008014d0`. Az azonosítót a `[this+0x3ec] + [this+0x3f4]*4` címről olvassa (38.2.34 §1).
- **A `worker` csak a jelzőre hív (LEZÁRVA).** A `0x007fb540` ciklusa 50 ezredmásodpercenként ellenőrzi a `[this+0x51a]` jelzőt. Ha az 1, meghívja a `0x00802230(this, 1)`-et, és nullázza a jelzőt. A jelzőt a `0x008018a0` állítja be a lista újraépítése után. Más író **NINCS MEG** (teljes `.text` pásztázás kell).
- **A `0x007fda00` (Időrend-indítás) nem épít listát (LEZÁRVA).** A közvetlen hívólistáján nincs `0x008018a0`. Indítás előtt ellenőrzi a `[this+0x2d8]` bájtot és a bal overlay szélességét (`[this+0x538]`). Ha a `[this+0x3f4]` negatív, nullát ír bele. Ezután `0x0097e510(0)` (az egérmutató-számláló, 38.2.10), `[this+0x3be] = 1`, a `QueryPerformanceCounter` időbélyege a `[this+0x430]` mezőbe, `0x00802230(this, 1)`, majd `[this+0x3ba] = 0`, `[this+0x3bb] = 0`, `[this+0x3b8] = 1` és `[this+0x3b9] = 1`.
- **Mikor épül újra a lista.** A `0x008018a0` csak akkor épít, ha az EAX-ban kapott kulcs eltér a `[this+0x50c]` mezőtől. Hívói: `0x00801cb0` (`0x00801ce5`, EAX = `[this+0x510]`, 38.2.25 szerint), `0x007fde80` (`0x007fe33e`) és `0x008037e0` (`0x00803953`). Az EAX értéke a két utóbbi hívóhelyen **NINCS MEG**. Időrend módban az út: a `0x00802060` hívja a `0x00801cb0`-t, ha `[this+0x3b8] != 0` (38.2.22 §3).
- **A kulcs típusa (PONTOSÍTVA).** A „kijelölt kártya indexe” megnevezés nem igazolt. A csúszka (`0x007fdd00`) a `[this+0x510]` mezőbe a rekord +0 mezőjének értékét írja, nem a címét: `*([this+0x3a8] + i*0xf8)` (a 17. kör C-kódjának 785-786. sora), az `i` indexet pedig a `[this+0x514]` mezőbe. **HELYESBÍTVE (38.2.37 §6):** a kulcs rekord +0 mező. Ugyanezt írja a `0x007fd8c0` (38.2.37 §2) és a `0x007fd800` kimenete (38.2.37 §1).

**6. Helyesbítések a korábbi szakaszokban.** Ezek a helyükön, `HELYESBÍTVE` vagy `PONTOSÍTVA` jelöléssel szerepelnek:

- 38.2.34 §1: a `0x008018a0` nem QPC-időzített. Az IAT-hívásai a `0xc4055c`, `0xc402a8` és `0xc40284` címen vannak, a QPC IAT-címe (`0xc40298`) nincs közöttük. Ez a `pe_dis` diszasszemblálásából igazolt. A rendezés nincs, a forrás-gyűjtemény NINCS MEG.
- 38.2.34 §3 és a 38.2.34 Ghidra-listájának 5. tétele: a négy tömb bájt-eltolása `0x444`, `0x46c`, `0x4bc`, `0x4e4`, nem dword-index. A C-törzs nem olvassa a 3-6. paramétert.
- 38.2.25 §1 (a `0x008018a0` 1. lépése) és 38.2.26 §1: a „kijelölt kártya indexe” pontosítva, a kulcs típusa NINCS MEG.
- 38.2.33 §4: a `startbutton`-`exit` párosítás feltételes volt, most LEZÁRVA.

**Bizonyítottsági fok.**

- **Megerősített, címmel:** a `0x008018a0` szerkezete és kulcs-ellenőrzése; a `0x007fa5b0` alapértékei; a `0x009aa720` másolása és a hibakeresési keret; a `0x00aa6180` két ága és az `a` alfa; a `0x007fda80` négy téglalapja és visszatérési értékei; a `0x007fb540` és a `0x007fda00` hívásai; a `0x00802230` hívólistája.
- **Feltételes:** a `0x00a6aa00` szerepe a kártyában; a `0x00410fa0` név szerinti betöltő volta; a `-S` és a `+S` irány.
- **NINCS MEG:** a két forrás-objektum osztálya; a kártya képe és felirata; a kártya normál keretének forrása; a négy tömb tartalma és a rétegsorrend; a `timelinedot` és a listaikon kattintása; a kulcs típusa és az EAX-értéke a két hívóhelyen; a `[this+0x51a]` többi írója.

**Cáfoló kísérlet.**

1. „A `0x008018a0` QPC-időzített.” **CÁFOLVA** a hívólistával és az IAT-címekkel.
2. „A `0x00802230` építi a listát.” **CÁFOLVA:** a hívólistáján nincs `0x008018a0`.
3. „A `0x00aa6180` törzse olvassa a négy tömböt.” **CÁFOLVA:** a dekompilált törzs nem olvassa a 3-6. paramétert.
4. „A `[this+0x50c]` kártya indexe.” **NEM IGAZOLT:** a csúszka rekordcímet ír a `[this+0x510]`-be, és a `0x00801cb0` ebből a mezőből veszi az EAX-kulcsot (38.2.25 szerint).
5. „A `startbutton` külön indítási ág.” **CÁFOLVA:** az `A` és a `B` ugyanazt az ágat (`0x007fb820`) hívja.
6. „A `0x009aa720` rajzolja a kártyát.” **CÁFOLVA** a közvetlen hívólistával: a `0x008014d0` nem hívja.

**Nyitott kérdések mérlege (38.2.35).** Lezárva: a négy téglalap és a `startbutton` ága; a `0x008018a0` szerkezete és a rendezés; a `0x00802230` nem épít listát; a `worker` és a `0x007fda00` hívása; a keret hibakeresési ága; a kártyarekord alapértékei; a `0x00aa6180` két ága. Nincs meg: a forrás-objektumok osztálya; a kártya képe és felirata; a négy tömb tartalma és a rétegsorrend; a `timelinedot` és a listaikon kattintása; a kulcs típusa és forrása.

**Új Ghidra-körök (38.2.35).**

- `Ghidra-kör kell: 0x007fde80 - a timelinedot és a listaikon kattintási és billentyűútja; hívóhelyek: 0x007fe15f, 0x007fe1fd, 0x007fe158, 0x007fe33e [blokkoló]`
- `Ghidra-kör kell: 0x00801cb0 - az EAX-kulcs forrása (a [this+0x510] tartalma: rekordcím vagy rekord-mező), és a 0x008018a0 hívás feltétele [blokkoló]`
- `Ghidra-kör kell: a 0x007fe33e, 0x00803953 és 0x00801ce5 körüli verem-előkészítés: a local_64 és a local_5c forrása, és az EAX értéke [blokkoló]`
- `Ghidra-kör kell: 0x004b0190 - a két vtábla-hívás (call eax, call edx) célja, és hogy beállít-e forrást [blokkoló]`
- `Ghidra-kör kell: 0x00aa5fb0 és a 0x00aa6180 asm-je - a 3-6. paraméter (0x444, 0x46c, 0x4bc, 0x4e4) olvasása és a négy tömb szerepe [blokkoló]`
- `Ghidra-kör kell: 0x009a8a30, 0x009aabf0, 0x009a8bc0 és 0x00a6a880 - az apLStack_f8[0] kép-objektum írója [blokkoló a kártya képénél]`
- `Ghidra-kör kell: 0x009c4440 - a 0x00410fa0 belső hívása: sztring-kulcsú keresés-e [nem blokkoló]`
- `Ghidra-kör kell: 0x00801cf0 - a 0x00802230 hívója (0x00801d05), a törzse [nem blokkoló]`

#### 38.2.36 Az Időrend bináris feltárása, 19. kör: kattintási út, lista-kulcsok, vtábla-hívások és kép-írók (#5401, 2026-10-21)

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-19.txt` (Ghidra-dekompilálás) volt: a `0x007fde80`, `0x00801cb0`, `0x004b0190`, `0x00aa5fb0`, `0x009a8a30`, `0x009aabf0`, `0x009a8bc0`, `0x00a6a880`, `0x00803c10`, `0x00802c20`, `0x00983430`, `0x005e60d0` és `0x007fa7f0` törzsei és hívólistái. A hívóhelyeket diszasszembly ellenőrizte (`pe_dis.cdis`): `0x007fe150`-`0x007fe360`, `0x00801130`-`0x00801180`, `0x00801cb0`-`0x00801cef`, `0x00803920`-`0x00803983`, `0x008018a0`-`0x008018f0`, a `0x004b0190` teljes hívás-listája, és a `0x00aa6180` három hívóhelye (`0x00aa61d0`-`0x00aa6250`).

A 38.2.35 (18. kör) nincs ezen az ágon, a `research/5401-haiku18` ágon van (commit `5b8293977`). Ezért a 38.2.35 nyitott listáját a §6 frissíti. A 38.2.35 szövegének átvezetése a másik ágon történik (§7).

Eltérés a dekompiláció és a kód között: a `0x004b0190` `call edx` hívása (`0x004b01f2`) két argumentumot kap (kulcs és ESI-leíró), a dekompiláló csak egyet mutat. A kódot a diszasszembly alapján kell olvasni.

**1. A timelinedot és a listaikon kattintási útja (`0x007fde80`).**

A bal gombos (`0x201`) ág Időrend-módban (`[this+0x3b8] != 0`) három lépésből áll, ebben a sorrendben:

1. `0x007fda80`, a négy találati téglalap. A `startbutton` (X `0x738`) és az `exit` (X `0x580`) a `0x007fb820` ágra megy, a `right` (X `0x558`) a `0x007fd150`-re, a `left` (X `0x530`) a `0x007fd120`-ra. Találat esetén a függvény `1000000`-t ad, és a 2. és 3. lépés nem fut (`0x007fe202`-`0x007fe207`).
2. A sáv-ág. A `timeline` (X `0x6c0`; bal `[+0x6d8]`, felső `[+0x6dc]`, szél `[+0x6c8]`, magasság `[+0x6cc]`) és a `sliderthumb` (X `0x710`; bal `[+0x728]`, felső `[+0x72c]`, szél `[+0x718]`, magasság `[+0x71c]`) téglalapjából a befoglaló téglalap lesz, ha mindkettő nem üres. Ha az első üres, a második lesz a téglalap. Ha az egér benne van (bal ≤ x < jobb, felső ≤ y < alsó), `[this+0x429] = 1` és `0x007fdd00(x, y)` hívás (`0x007fe30d`-`0x007fe314`). Ha nincs benne, `[this+0x428] = 1` (`0x007fe31b`).
3. `0x007fd800([this+0x2f8], &[this+0x420], &kimenet)` (`0x007fe32f`). Ha `0`-t ad (`0x007fe334`-`0x007fe336`), a `0x008018a0` fut, EAX = `kimenet` (`0x007fe338`-`0x007fe33e`).

- **Timelinedot (X `0x6e8`): NINCS MEG.** A `0x007fde80` törzse a `0x6c8`-`0x72c` mezőket olvassa, a `0x6e8`-at nem. A `0x007fda80` négy téglalapja sem tartalmazza. Ez a függvény tehát nem adja a timelinedot kattintási útját.
- **Listaikon: NINCS MEG.** A `0x007fde80`-ban nincs listaikon-téglalap. A lista-újraépítés kattintási útja a 3. lépés: bal gombos kattintás, amely nem esik a négy találatra, és a `0x007fd800` nullát ad (a sáv-ág után is lefut). A `0x007fd800` törzse nincs ebben a körben.
- **Dupla kattintás (`0x203`, dekompiláció szerint, az asm nincs ellenőrizve).** A négy találat után `0x007fb820` hívódik, majd ha `[this+0x2e8] != 0`: `vt+0x18(-1, id)`, ahol `id = [[this+0x3ec] + [this+0x3f8]*4]`, ha `[this+0x3f8] >= 0`, különben `0`. Ez a kiválasztott listaelem átadása a `[this+0x2e8]` objektumnak; a `vt+0x18` célja NINCS MEG. Hogy a listaikon ez-e, NINCS MEG.

**2. A lista-újraépítés kulcsa (`0x008018a0`).**

| hívóhely | EAX-kulcs | feltétel | a kulcs típusa |
|---|---|---|---|
| `0x007fe33e` (`0x007fde80`, 1. lépés 3. pontja) | a `0x007fd800` kimeneti dword-je (`[esp+0x18]`) | a `0x007fd800` 0-t ad | NINCS MEG |
| `0x00801ce5` (`0x00801cb0`) | `[this+0x510]` | `[this+0x429] == 0`, és a `0x007fd8c0` (EAX = `this+0x2f8`, argumentum = `&[this+0x510]`) nem nulla (`0x00801cc6`-`0x00801cdf`) | NINCS MEG; a `0x007fd8c0` írhatja |
| `0x00803953` (`0x008037e0`) | `0` (`0x0080394f`) | `([X+0x18]+4) & 0xfffffffe == 0`, ahol X a `0x008037e0` edi-je (`0x00803946`-`0x0080394d`) | konstans 0 |

- A három hívóhely egyike sem tesz argumentumot a verembe a `call` előtt. A 38.2.35 §1-2 „hívó által verembe előkészített értékek” állítása ezért nem igazolt (§7).
- A `0x008018a0` belépése: `cmp [this+0x50c], eax` és `je` (`0x008018ac`-`0x008018b2`): ha a kulcs egyezik a tárolttal, visszatér. Különben `[this+0x50c] := EAX` (`0x008018b8`), `push [this+0x50c]` (`0x008018c7`-`0x008018cd`), majd EAX = `[this+0x2f4]`, ESI = `esp+0x20`, és `call 0x004b0190` (`0x008018d4`-`0x008018e0`). A kulcs tehát két helyen szerepel: egyezés-ellenőrzés, és a `0x004b0190` argumentuma (§3).
- A kulcs típusát a `0x007fd800` és a `0x007fd8c0` kimenete dönti el. Ezek törzse nincs ebben a körben.

**3. A `0x004b0190` vtábla-hívásai, és a forrás beállítása.**

A `0x004b0190` EAX-ban a `this` (a `[this+0x2f4]` objektum), ESI-ben a hívó leírója, az első argumentum a kulcs. Az `L` jelöli a `[EAX+0xc4]` objektumot. Az indirekt hívások:

- `0x004b01d1` `call eax`: `vt+0x18` az `[L+0x68]` objektumon, zárolásként. Csak ha `[L+0x74] == 0`. Egyébként `EnterCriticalSection(L+0x90)` (`0x004b01c1`).
- `0x004b01f2` `call edx`: `vt+0x2c` az `[L+0x48]` objektumon (ECX = `L+0x48`), argumentumai `(kulcs, ESI)`. Ez a forrás-lekérdezés, a kimenet az ESI-leírókba megy. A hívás után a törzs `ESI+0x5c` és `ESI+0x64` értékét nézi: ha valamelyik nulla, a függvény -1-gyel tér vissza (dekompiláció).
- A `0x004b0190` maga 18 mutatót köt az ESI-be. Például `ESI+0x68 := this+0x29c` (`0x004b01fa`), `ESI+0xa4 := this+0x2a4` (`0x004b0203`). A többi a `[this+0x2a8]`, `[this+0x2ac]`, `[this+0x2b0]`, `[this+0x2b4]`, `[this+0x2b8]`, `[this+0x2bc]`, `[this+0x2c8]` és `[this+0x2d0]` objektumok `+0x04`, `+0xcc`, `+0xd4` és `+0x10` mezőire mutat (dekompiláció).
- Kilépés: `vt+0x1c` az `[L+0x68]` objektumon (`0x004b0328`, `0x004b0378`, `call eax`), vagy `LeaveCriticalSection` (`0x004b0312`, `0x004b0361`), ha `[L+0x74] != 0`.

Válasz:
- **A két vtábla-hívás célja.** `call eax` (`0x004b01d1`): zárolás (`vt+0x18`), kilépéskor feloldás (`vt+0x1c`). `call edx` (`0x004b01f2`): a forrás lekérdezése a kulccsal, a kimenet az ESI-leíróba.
- **Beállít-e forrást?** Igen. A `call edx` tölti az ESI-leírót, a `0x004b0190` pedig a 18 mutatót köti.
- **NINCS MEG:** az `L` és az `[L+0x48]` objektum osztálya, és a `vt+0x2c` célja. Ezt a két objektum konstruktora adja.

**3b. A `0x00aa5fb0` paraméterei, és a `0x00aa6180` 3-6. argumentuma.**

- A `0x00aa5fb0` `__thiscall`: ECX és négy verem-argumentum. **Nincs 6. paramétere.** Az ECX a forrás-leíró `S`; `param_2` a célsor pixelcíme; `param_3` a pixelek száma; `param_4` az x0; `param_5` a sorindex. EAX a 2×3 affin mátrix (6 f32): forrás-x = m0·x + m1·y + m2, forrás-y = m3·x + m4·y + m5, ahol (x, y) a célpixel koordinátája + 0,5. A függvénynek nincs belső hívása.
- A `0x00aa6180` három hívása (`0x00aa6203`, `0x00aa6214`, `0x00aa6226`):
  - 1. és 2. hívás: ECX = `arg3` (`[ebp+0x10]`, `0x00aa61f5`), EAX = `arg5` (`[ebp+0x18]`, `0x00aa6200`).
  - 3. hívás: ECX = `arg4` (`[ebp+0x14]`, `0x00aa6223`), EAX = `arg6` (`[ebp+0x1c]`, `0x00aa621c`).
  - A `0x00aa6180` 3-6. argumentuma tehát: `S1` (arg3), `S2` (arg4), `M1` (arg5), `M2` (arg6). A hívó (`0x008001c0`, 38.2.31 §2) ezeket a `this+0x444`, `+0x46c`, `+0x4bc` és `+0x4e4` címeken adja át. Az arg2 (`[ebp+0xc]`) a célkép: `[+0x04]` sorlépés, `[+0x10]` pixelcím (`0x00aa61e4`, `0x00aa61e7`).
- **M1 és M2 egységmátrix a konstruktorban (megerősített).** A `0x007fa7f0` a `this+0x4bc`-tól `1,0 / 0 / 0 / 0 / 1,0 / 0` értékeket ír (`m0 = m4 = 1`), ugyanígy a `this+0x4e4`-től. A kép kezdetben nem torzított.
- **S1 és S2 leíró-típusa: NINCS MEG.** A `0x00aa5fb0` a forrás `+0x08` mezőjét sorlépésnek, `+0x0c`-t magasságnak, `+0x10`-et pixelcímnek olvassa. A `0x009aabf0` a `+0x04`-et sorlépésnek, `+0x08`-at szélességnek, `+0x18`/`+0x1c`-et origónak olvassa. A `this+0x444` objektum konstruktora nincs mérve, ezért nem dől el, melyik olvasat érvényes.

**4. A kártya kép-objektumának írói.**

A kép-leíró (ImgDesc, 0x28 bájt) mezői az írók alapján: `+0x00` hivatkozásszámlált puffer-mutató, `+0x04` sorlépés, `+0x08` szélesség, `+0x0c` magasság, `+0x10` pixelcím, `+0x14` rövid típusmező, `+0x18`/`+0x1c` origó, `+0x24` HBITMAP. (A `0x00aa6180` célképe is ilyen: `+0x04` és `+0x10`.)

| függvény | mit ír | a kártya-leíró írója? |
|---|---|---|
| `0x009a8a30` | `+0x24 := 0`. Ha `+0x08` vagy `+0x0c` legalább `0x80000000`, `+0x04`, `+0x08`, `+0x0c := 0`. Ha valamelyik nulla, `+0x10 := 0`, vége. Különben `0x009a9b30` (foglalás); hiba esetén `+0x04`, `+0x08`, `+0x0c := 0`. | IGEN, leíró-író (megerősített). |
| `0x009a8bc0` | A `*esi` hivatkozásszámlált puffer csökkentése (`InterlockedDecrement`); 0-nál `0x0097caf0`, és `*esi := 0`. Ha (`+0x14 != 0` és `+0x10 != 0`) vagy `+0x24 != 0`: a `DAT_00d678f8` csökken 1-gyel, a `DAT_00d678e4` csökken `4 · +0x0c · +0x08`-cal. Ha `+0x14 == 1` és `+0x10 != 0`: `0x0097caf0(+0x10)`, `+0x14 := 0`. Utána `+0x08`, `+0x0c`, `+0x10`, `+0x14`, `+0x16` nulla; `+0x24` nem nulla esetén `DeleteObject`, majd nulla. | IGEN, felszabadító-író (megerősített). |
| `0x009aabf0` | Nem a leírót írja, hanem a célkép pixeleit: `param_1` (`+0x10` cím, `+0x04` sorlépés) `[param_2, param_4)` × `[param_3, param_5)` tartományába másol a forrásból (EDI: `+0x10`, `+0x04`, `+0x18`, `+0x1c`), soronként `memcpy`-vel. Előbb `0x009aaae0()`: ha `3`, nincs másolás. | NEM a leíró, pixel-író. Hogy a kártya pixeleit írja-e, NINCS MEG (hívója `0x00a6ab2b`, a `0x00a6aa00` törzse nincs ebben a körben). |
| `0x00a6a880` | A `this` `+0x0c` mezője alapján `+0x90`-et állítja, `+0x30`-tól a `+0x94`/`+0x98` méretből (szélesség, magasság) szintenkénti eltolás-táblát ír. A `+0x2c` puffert `0x0097c810`-zal foglalja újra, és nullázza. | NEM. A `this` más objektum (szint-puffer), nem a `+0x08`/`+0x0c` leíró. Hívója `0x00a6aa00` (`0x00a6aa82`); a `this` azonossága NINCS MEG. |

- A `0x007fa7f0` konstruktor 18 alkalommal hívja a `0x009a8a30`-t. A dekompilált törzsben minden hívás előtt négy nulla-írás van, köztük a `+0x08` és `+0x0c`, tehát a 18 kép-leíró üresen indul, és a foglalás ekkor nem fut le.
- **NINCS MEG:** a `0x009a9b30` (a foglaló) törzse, és hogy a `0x00a6aa00` `this`-e melyik kép-leíró.

**5. Az öt további függvény szerepe az Időrendben.**

- **`0x00803c10`** (`FUN_00401110(0xf8, 0x007fd090)`, majd `_free(this-4)`): a 0xf8-as kártya-rekordok tömbjének (`[this+0x2ec]`) lebontása és felszabadítása. Hívói: `0x008014d0` (`0x008014e5`), `0x007faeb0` (`0x007faee3`), `0x007fb5a0` (`0x007fb7da`), `0x007fc7c0` (`0x007fc7d8`). Időrendben a régi kártyatömböt szabadítja fel a `0x008014d0` újraépítése előtt. Az elemdestruktor (`0x007fd090`) NINCS MEG.
- **`0x00802c20`** (hívója `0x00801130`, `0x00801159`): a szünet-ág. A `0x00801130` a szóköz kapcsolója (és a mód-0 kattintásé): átváltja `[this+0x3bb]`-t, és ha az új érték 1, meghívja a `0x00802c20`-t (`0x00801155`-`0x00801159`). A törzs: ha `[this+0x3f4] < 0`, nullázza. Hívja a `0x00802830()`-t. Ha annak eredménye nulla és `[this+0x50] != 0`, a `0x009833a0()` eredményét adja, különben a `0x00802830` eredményét, illetve nulla esetén `-1`-et. A `0x00802830` és a `0x009833a0` belseje NINCS MEG.
- **`0x00983430`** (hívói `0x008037e0`, `0x00803983`): az ablakobjektum (`[this+0x50]`) méret-értesítése. `GetClientRect(hWnd)`, hWnd = `[obj+0x6c]`, majd `0x00983a60(szél, magasság)`. Ha a kliensterület nem üres és `[obj+0x64] != 0`, `vt+0x20(-1, -1, -1, -1)` a `[obj+0x64]` objektumon. Időrendben az ablak megnyitásakor egyszeri méret-szinkron és teljes-terület frissítés. A `vt+0x20` célja NINCS MEG.
- **`0x005e60d0`** (hívója `0x005e6710`, `0x005e69cf`): a főablak billentyű-kapcsolója. Az Időrend-belépés a `0x34` (`4`) és a `0x35` (`5`) ág: `0x005e8a70(this, 0)`, illetve `0x005e8a70(this, 1)` (1 = Időrend mód), mindkettő csak `0x005696c0(this) == 0` esetén. Nincs ága a szóköznek (`0x20`), az Escape-nek (`0x1B`), a nyilaknak (`0x25`-`0x28`), a PgUp/PgDn/End/Home billentyűknek (`0x21`-`0x24`). Ezeket a qshow saját billentyű-ága kezeli (38.2.8, 38.2.20). A `0x34`/`0x35` ágon nincs Ctrl-ellenőrzés. A kulcs-átalakítás (`0x005c5f90`, `0x005c5fc0`) NINCS MEG.
- **`0x007fa7f0`** (hívója `0x008037e0`, `0x00803920`, EAX = X, a `0x008037e0` edi-je): az Időrend-objektum konstruktora (QDrawable-származék). Beállítja a vtáblát, a 18 kép-leírót (`0x009a8a30`), az M1 és M2 egységmátrixot (§3b), négy QPC-időbélyeget, és olvassa a `Preferences\SlideshowEffectTime`, `LoopSlideshow` és `PlayMP3Tracks` kulcsokat. Kezdeti állapot: `[this+0x3b8] = 0` (mód 0), `[this+0x3c1] := *X`. A `[X+0x18]` gyűjteményt `0x00891110` másolja. A `0x008037e0` a `0x00803953`-ban ezt a gyűjteményt vizsgálja (§2).

**6. A 38.2.35 nyitott listájának állapota (frissítve).**

| 38.2.35 tétel | új állapot | hol |
|---|---|---|
| 1. `0x007fde80`: timelinedot és listaikon kattintása [blokkoló] | RÉSZBEN LEZÁRVA: a kattintási út megvan. Timelinedot: NINCS MEG. Listaikon: NINCS MEG | §1 |
| 2. `0x00801cb0`: az EAX-kulcs forrása és a `0x008018a0` feltétele [blokkoló] | LEZÁRVA a forrás és a feltétel. A kulcs típusa: NINCS MEG | §2 |
| 3. `0x007fe33e`, `0x00803953`, `0x00801ce5`: verem-előkészítés, `local_64`, `local_5c`, EAX [blokkoló] | LEZÁRVA: nincs verem-előkészítés, az EAX-források megvannak. A `local_64`/`local_5c` eredete NINCS MEG (feltételes: a `0x004b0190` ESI-kötése) | §2, §3 |
| 4. `0x004b0190`: a két vtábla-hívás célja és a forrás beállítása [blokkoló] | LEZÁRVA a szerep és a beállítás. A `vt+0x2c` célja NINCS MEG | §3 |
| 5. `0x00aa5fb0` és `0x00aa6180`: 3-6. paraméter, a négy tömb szerepe [blokkoló] | LEZÁRVA a paraméterek. Az S1, S2 típusa NINCS MEG | §3b |
| 6. `0x009a8a30`, `0x009aabf0`, `0x009a8bc0`, `0x00a6a880`: kép-írók [blokkoló a kártya képénél] | RÉSZBEN LEZÁRVA: a leíró-írók azonosítva. A kártya-kép forrása NINCS MEG | §4 |
| 7. `0x009c4440`: a `0x00410fa0` belső hívása [nem blokkoló] | NYITVA (nem volt a bemenetben) | - |
| 8. `0x00801cf0`: a `0x00802230` hívója [nem blokkoló] | NYITVA (nem volt a bemenetben) | - |

**Új Ghidra-körök (38.2.36).**

- `Ghidra-kör kell: 0x007fd800 - a [this+0x2f8] találat-kereső: visszatérési érték, és a harmadik (kimeneti) paraméter típusa és értéke 0 esetén [blokkoló]`
- `Ghidra-kör kell: 0x007fd8c0 - a [this+0x510] írója és a visszatérési bool jelentése [blokkoló]`
- `Ghidra-kör kell: 0x008018a0 teljes törzse - az esp+0x20 ESI-leíró mezőinek olvasata, és a local_64, local_5c helye a keretben [blokkoló]`
- `Ghidra-kör kell: a [[this+0x2f4]+0xc4] objektum konstruktora - a vt+0x18, vt+0x1c és vt+0x2c célja [blokkoló]`
- `Ghidra-kör kell: 0x009a9b30 - a kép-foglaló (0x009a8a30 hívja) [blokkoló a kártya-képnél]`
- `Ghidra-kör kell: 0x00a6aa00 - a this-e, és a 0x00a6a880 és 0x009aabf0 hívási sorrendje [blokkoló a kártya-képnél]`
- `Ghidra-kör kell: 0x009aaae0 - a 0x009aabf0 őre (3 = nincs másolás) [nem blokkoló]`
- `Ghidra-kör kell: 0x007fd090 - a kártya-rekord elemdestruktora (0x00803c10) [nem blokkoló]`
- `Ghidra-kör kell: 0x00802830 és 0x009833a0 - a szünet-ág (0x00802c20) visszatérési értékei [nem blokkoló]`
- `Ghidra-kör kell: 0x005696c0, 0x005c5f90, 0x005c5fc0 - a 4/5 billentyű gate és a kulcs-átalakítás (0x005e60d0) [nem blokkoló]`
- `Ghidra-kör kell: a this+0x444 objektum konstruktora - az S1 típusa és a 0x00aa5fb0 leíró-olvasata [nem blokkoló]`

> **FRISSÍTVE (38.2.37 §7):** a fenti Ghidra-körök állapota a 38.2.37 §7 táblázatában van; a címek érvényesek.

**7. Helyesbítések.**

- **38.2.25 §1** (`0x008018b8` sora): a „kijelölt kártya indexe” megnevezés NEM IGAZOLT. PONTOSÍTVA (38.2.36 §2), a kulcs típusa NINCS MEG.
- **38.2.35 §1-2** (másik ágon, `research/5401-haiku18`): a „hívó által a veremben előkészített értékek” állítás HELYESBÍTVE. A három hívóhelynek nincs `push`-a (§2). A `local_*` értékek valószínűleg a `0x008018a0` saját keretében vannak, és a `0x004b0190` vt+0x2c hívása tölti őket (§3, feltételes). Ezt a 38.2.35 szövegében is át kell vezetni, amikor az ág beolvad.
- **38.2.31 §2 és 38.2.35 §3** (`0x444`, `0x46c`, `0x4bc`, `0x4e4`): megerősítve, nem javítás. A négy argumentum két forrás-leíró (ECX) és két affin mátrix (EAX), lásd §3b.
- **Dekompiláció** (nem a kód hibája): a `0x004b0190` `vt+0x2c` hívásából a dekompiláló egy argumentumot mutat. A `0x007fe33e` hívását argumentum nélkülinek mutatja (38.2.20 is jelezte).

**8. Bizonyítottsági fok, cáfoló kísérlet, mérleg.**

- **Megerősített, címmel:** a `0x007fda80` négy téglalapja és a sáv-ág; a `0x007fe33e`, `0x00801ce5`, `0x00803953` EAX-forrásai; a `0x008018a0` belépése; a `0x004b0190` indirekt hívásai (`0x004b01d1`, `0x004b01f2`, `0x004b0328`, `0x004b0378`); a `0x00aa5fb0` szignatúrája és a `0x00aa6180` három hívása; a `0x007fa7f0` 18 `0x009a8a30` hívása és az M1/M2 egységmátrix; a `0x009a8a30`, `0x009a8bc0`, `0x009aabf0`, `0x00a6a880` törzsei; a `0x00801130` szünet-ága.
- **Feltételes:** a `local_*` helye a `0x008018a0` keretében (§7); a `0x009aabf0` kártya-pixelekre való használata; a `0x00aa6180` hívójának argumentum-címei (38.2.31 §2 szerint).
- **Cáfoló kísérlet:**
  1. „A `0x007fde80` timelinedot-téglalapot vizsgál.” CÁFOLVA: a törzsben nincs `0x6e8` mező.
  2. „A `0x008018a0` kulcsát a hívó verembe teszi.” CÁFOLVA: a három hívóhelyen nincs `push`.
  3. „A `0x00aa5fb0`-nak 6. paramétere van.” CÁFOLVA: ECX és négy verem-argumentum.
  4. „A `0x00802c20` a léptetés.” CÁFOLVA: szünet-ág. A léptetést a `0x00802060` végzi.
  5. „A `0x00801ce5` EAX-ja a `0x007fd8c0` kimenete.” NEM IGAZOLT: a `0x007fd8c0` megkapja a `&[this+0x510]` címet, de az írását nem láttam.
- **Nyitott kérdések mérlege (38.2.36):** 28 tétel: `5 nyílt` (nem blokkoló NINCS MEG) · `16 lezárva` · `5 blokkolt` (a timelinedot, a listaikon, a kulcs típusa, a `vt+0x2c` célja, a kártya-kép forrása) · `2 hatókörön kívül` · `0 csak nyitva`. A BLOKKOLT tételek gépi úton (Ghidra-körrel vagy pásztázással) dönthetők el. A `picasapy-agent` munkasorát ebben a körben nem frissítettem, ezt a hívónak kell átvezetnie.

#### 38.2.37 Az Időrend bináris feltárása, 20. kör: a kulcs, a kártya-keresés, a lista forrása, a léptető-jelzők és a nyitott lista (#5401, 2026-10-21)

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-20.txt` (Ghidra-dekompilálás) volt: a `0x007fd800`, `0x007fd8c0`, `0x008018a0` (teljes törzs), `0x009a9b30`, `0x00a6aa00`, `0x009aaae0`, `0x007fd090`, `0x00802830`, `0x009833a0`, `0x009c4440` és `0x00801cf0` törzse és hívólistái. A kulcs útjához beolvastam a 15-19. kör `0x007fde80`, `0x007fdd00`, `0x00801cb0`, `0x00802c20`, `0x008014d0`, `0x007fa5b0`, `0x007fa7f0` és `0x004b0190` dekompilálását. A hívóhelyeket és a döntő ágakat `pe_dis.py` diszasszemblálta. A konstansokat a `Picasa3.exe` fájlból olvastam ki VA alapján (ImageBase `0x400000`, a repo kutatási másolatából). A cím-atlasz (`atlasz_keres.py`) lefutott: a `0x007fd800`, `0x007fd8c0`, `0x008018a0`, `0x00801cf0` és `0x009a9b30` már szerepel a specekben; a `0x00a6aa00`, `0x007fd090`, `0x00802830`, `0x009833a0` és `0x009c4440` új terület.

**Bizonyítási terv (számozva, a kör elején).** (1) Atlasz: kész. (2) A hívóhelyek verem-állapota és a stack-argumentumok asm-ellenőrzése. (3) A kulcs írói: `0x007fd800`, `0x007fd8c0`, `0x007fdd00`. (4) A `0x008018a0` lista-forrásai és a helyi változók helye a keretben. (5) A konstansok kiolvasása a fájlból. (6) A többi függvény szerepe. Kódot nem módosítottam, ezért CI-őr nem futott.

**Konstansok (a Picasa3.exe fájlból, VA alapján).**
- `0xcf4900`: f32 `1000000.0` (nyers bájtok `00247449`). A legközelebbi-kártya keresés kezdeti minimuma.
- `0xcf4860`: f64 `0,6660000085830688` (nyers `00000040df4fe53f`). A `0x007fd8c0` ezt vonja ki (`~0,666`).
- `0xcf3ac0`: f64 `4294967296.0` (2^32). A negatív index korrekciója.
- `0xcf40b8`: f64 `0,01`. A lépésköz-szorzó a `0x007fd8c0`-ban.
- `0xc7e328`: f64 `1,0` (az asm `fcomp qword`-del olvassa).

**1. A találat-kereső (0x007fd800): a kimenet a találati rekord +0 mezője; a keresés téglalapokat vizsgál.**
- **Hívó és konvenció (LEZÁRVA, asm).** A `0x007fde80` a `0x007fe32f`-nél három stack-argumentumot tol: `[this+0x2f8]` (az `ECX`-ből), a pontmutató (`EBX = this+0x420`, `lea ebx,[edi+0x420]` a `0x007fe2bf`-nél, `push ebx` a `0x007fe327`-nél) és a kimeneti cím (`&kimenet`). A `0x007fd800` `ret 0xc`-vel takarít (`0x007fd88c`, `0x007fd8b2`). A `0x007fe334`-nél `test eax,eax`, majd `jne 0x7fe35d`: a `0x008018a0` csak 0 visszatérésnél fut, és ekkor `ECX = edi`, `EAX = [esp+0x18]` (a kimenet).
- **Keresés (LEZÁRVA, dekompiláció).** A `[obj+0x80]` index-listán megy végig, darabszám `[obj+0x84] >> 1`, ahol `obj = this+0x2f8`. Az `i`-edik rekord címe `[obj+0xb0] + i*0xf8`. Ez a `[this+0x3a8]` tömb (`this+0x2f8+0xb0 = this+0x3a8`, a darabszám `this+0x3ac`). A rekord `+0xdc`, `+0xe0`, `+0xe4`, `+0xe8` mezői (egész, f32-ként hasonlítva) bal, felső, jobb és alsó határt adnak. Találat: `bal <= x < jobb` és `felső <= y < alsó`, ahol `(x, y)` a `[this+0x420]`, `[this+0x424]` pár. A `0x007fa5b0` ezeket nullázza, így üres rekord nem talál.
- **A kimeneti kulcs típusa (LEZÁRVA).** Találatnál `*kimenet := rekord +0 mező` (4 bájt). Ez nem a rekord címe (`base + i*0xf8`), és nem az `i` index. Ugyanezt a mezőt írja a `0x007fd8c0` (§2) és a `0x007fdd00` (§6) is, tehát a `[this+0x510]` kulcs is ez.
- **Visszatérés (RÉSZBEN LEZÁRVA).** Találatnál a `0x007fd770(i)` értéke (dekompiláció, a hívás `0x007fd8a9`-nél), nincs találatnál `0xffffffff`. ~~A `0x007fd770` értéke és jelentése **NINCS MEG**: az asm a `[esi+0x38]` objektum double-mezőiből számol, a törzs teljes egészében nincs meg. Ghidra-kör kell: `0x007fd770 - a találat-ág visszatérési értéke, amelytől függ, fut-e a 0x008018a0 [blokkoló]`.~~ **LEZÁRVA (38.2.38 §1):** találatnál a visszatérés 0, és a 0x008018a0 csak ettől fut.
- **A rekord +0 mező írója (BLOKKOLT).** A `0x007fa5b0` az alapértéket `-1`-re állítja (asm: a `0x00801580` hívás, `ECX = esp+0x50`). A `0x008014d0` törzsében más, a rekordot érintő írás nincs. Megfigyelés: a helyi `(id, &helyi, 1)` struktúra (`esp+0x2c`, 0x28 bájt) és a rekord (`esp+0x50`) 4 bájtban átfedhet (a helyi `+0x24` mezője és a rekord `+0` mezője). Ghidra-kör kell: `0x00803b50 - a rekord-másoló, a +0 és a +0x30 mező írója [blokkoló]` és a `[this+0x2e4]` objektum vtábla `+0x00` célja [blokkoló, lásd §4]. **RÉSZBEN LEZÁRVA (38.2.38 §2):** a 0x008014d0 rekordjain a +0 értéke `-1` (a 0x007fa5b0 írja, és a 0x008014d0 törzsében nincs más írás); a +0x30 és a 0x007fc7c0 út NINCS MEG.

**2. A `[this+0x510]` írója (0x007fd8c0): a legközelebbi kártya rekord +0 mezőjét írja.**
- **Hívó (LEZÁRVA, asm).** A `0x00801cb0`-ban `0x00801cc6`: `cmp byte [esi+0x429], 0`, `jne 0x801cea`, tehát csak akkor, ha `[this+0x429] == 0`. A `[this+0x429]`-et a `0x007fe30d` állítja 1-re, ha az egér a sávban van; ilyenkor a `0x007fdd00` már beállította a kulcsot (§6). Utána `lea edi,[esi+0x510]`, `push edi`, `mov eax, ebx` (`EBX = this+0x2f8`), `call 0x7fd8c0` (`0x00801cd8`). A `0x007fd8c0` `ret 4`-gyel takarít (`0x007fd9d8`, `0x007fd9e4`).
- **Mit ír (LEZÁRVA, asm + dekompiláció).** Először `[obj+0] := 0` (`0x007fd8d9`). Ha `[obj+0xb4] >> 1 == 0` (`0x007fd8d0`-`0x007fd8df`, `je 0x7fd9dd`), nincs más írás. Különben a ciklus `i = 0 .. darab-1`:
  - `x_i = i * [obj+0x30] + [obj+0x20]` (double; negatív `i`-nél `+2^32`);
  - `d_i = |FUN_007fbab0(x_i) - 0,666|` (a `0x0049f5c0` `fabs`, asm-ellenőrizve);
  - a szigorúan kisebb `d_i` megtartása, a kezdeti minimum `1000000.0`; a nyertes indexe `[obj+0] := i*` (`0x007fd950`).
  Ezután `[this+0x510] := rekord[i*] +0 mező` (dekompiláció).
- **Mikor ad nem nullát (LEZÁRVA a gépi részre, a második lista RÉSZBEN NINCS MEG).** A visszatérési érték nem nulla, ha (a) a darab nem nulla, (b) `|[obj+0x18]| <= 0,01 * [obj+0x30]`, és (c) a második lista (`[obj+0x4c] >> 1`) darabszáma 0; vagy 1, és `[obj+0x48]` elemének `+0x18` és `+0x20` mezői egyenlők; vagy `v > 1,0`, ahol `v = (FUN_009a5210() - a) / (b - a)`, `a = [[obj+0x48]+0x18]`, `b = [[obj+0x48]+0x20]`. Ha a darab 1 vagy több, és `v <= 1,0`, a visszatérés 0. A `0x009a5210` értéke és a második lista jelentése **NINCS MEG**. Ghidra-kör kell: `0x009a5210 - a visszatérési bool feltétele [blokkoló]`. **PONTOSÍTVA (38.2.38 §3):** a bool teljes feltétele mérve; csak a `0x009a5210` értéke NINCS MEG.
- **A kulcs felhasználása (LEZÁRVA, asm).** A `0x00801ce1`: `mov eax,[edi]` (ez a `[this+0x510]`), `mov ecx,esi`, `call 0x8018a0` (`0x00801ce5`). A `[this+0x510]` tehát a `0x008018a0` kulcsa.
- **A `FUN_007fbab0` kimenete (BLOKKOLT).** Az asm-ben a hívás után a `0x007fd921` az `[esp+0x14]`-et olvassa; a hívó `EAX`-ja `esp+0x18`-ra mutat. **JAVÍTVA (38.2.38 §3):** a `0x007fbab0` törzse a `[EAX]`, `[EAX+4]`, `[EAX+8]` címekre ír, így a kimeneti cím nem feltevés. ~~Ghidra-kör kell: `0x007fbab0 - a teljes törzs, a kimeneti cím és a [ECX+0x50], [ECX+0x54], [ECX+0x58] jelentése [blokkoló a legközelebbi kártyánál]`.~~ **LEZÁRVA.**

**3. A `0x008018a0` törzse: hogyan épül a lista, és mi a `local_64` és a `local_5c`.**
- **Belépés (LEZÁRVA, asm).** `ECX = this`, `EAX = kulcs`. A törzs `sub esp,0xd4` és négy `push` után egyetlen `[esp+0xe8]` fölötti címet sem olvas, tehát nincs stack-argumentuma. `ret` (`0x00801caf`) argumentum nélkül.
- **Kulcs-kapu (LEZÁRVA, asm `0x008018ac`-`0x008018b8`).** `cmp [this+0x50c], eax`, `je 0x801ca3` (egyezésnél kilép). Különben `[this+0x50c] := kulcs`.
- **A `[this+0x50c]` kezdeti értéke (LEZÁRVA, dekompiláció).** A `0x007fa7f0` konstruktor `[this+0x50c] := *(X+4)`, ahol `X` a konstruktor `EAX`-ja (a `0x008037e0` adja).
- **Forrás-lekérdezés (LEZÁRVA, asm `0x008018d4`-`0x008018e0`).** `ESI = esp+0x20`, `EAX = P = [this+0x2f4]`, `push kulcs`, `call 0x4b0190`.
- **`local_64` (a helye LEZÁRVA, az írója BLOKKOLT).** A `[esp+0x80]`, azaz `ESI+0x64` (a lista fogantyúja; **JAVÍTVA 38.2.43 §1.3**: a korábbi `ESI+0x60` és `[esp+0x84]` téves volt). Darabszám: a fogantyú `+4` mezőjének `>> 1` értéke. A `0x004b0190` törzsében nincs `[esi+0x60]`-ba írás (asm, a teljes függvényen). A `0x004b01f2` `call edx` (a `[L+0x48]` objektum vt+0x2c, argumentumok `(kulcs, ESI)`, `L = [P+0xc4]`) után a `0x004b02d4` és a `0x004b02df` az `[esi+0x5c]` és `[esi+0x64]` nullázottságát nézi, hiba esetén `-1`. Ezért a `local_64` írója a vt+0x2c célja, az ESI-n át. **NINCS MEG:** a vt+0x2c célja és az `[L+0x48]` objektum konstruktora (lásd a §7 Ghidra-listát). **PONTOSÍTVA (38.2.38 §4):** a 0x004b0190 törzsében nincs közvetlen írás az ESI+0x60-0x67 tartományba; a vt+0x2c hívás (kulcs, ESI) kapja az ESI-t.
- **`local_5c` (LEZÁRVA).** A `[esp+0x88]`, azaz `ESI+0x68`. A `0x004b01f4` `lea eax,[edi+0x29c]` (itt `edi = P`), a `0x004b01fa` `mov [esi+0x68], eax`. Tehát `local_5c = P+0x29c`: a szűrő bájt-tömb (adat `+0`, darab `+4 >> 1`). Olvasás: `0x00801af0`-`0x00801b12` (asm): `mov eax,[esp+0x88]`, `cmp byte [adat + id], 0`; `id >= darab` esetén nincs szűrés.
- **A lista építése (LEZÁRVA, dekompiláció + asm-jelek).**
  1. `[this+0x3f0] &= 1` (`0x8018fa`): a darabszám nullázódik, a 0. bit (zár) megmarad. A régi lista felszabadítása `0x0097caf0`-nal (`0x8018f2`). `[this+0x3ec] := 0` (`0x801907`), `[this+0x3f4] := 0` (`0x80190d`).
  2. Ciklus a `local_64` elemein (`cc = 0 .. darab-1`, `id = local_64.adat[cc]`). Az `id` akkor kerül a listába, ha (a) `local_5c` nulla, vagy `id >= local_5c` darab, vagy `local_5c.adat[id] == 0`; és (b) a `[this+0x3f0]` 0. bitje nulla (`0x801b18`-`0x801b21`, `test cl,1; jne`). A tömb kapacitása duplázódik, a darab nő (a 0. bit megmarad).
  3. Vége: `[this+0x51a] := 1` (dekompiláció; ezt olvassa a `worker`, 38.2.35 §5), majd `0x008014d0()` (kártya-építés, 38.2.36 §4) és `0x00413490()`.
  - Zár: a törzs `GetCurrentThreadId` alapú, rekurzív zárat használ: `[this+0x20]` a tulajdonos-szál, `[this+0x24]` a rekurziószám, `[this+0x28]` a kritikus szakasz (dekompiláció). Ez védi a lista írását.
- **Összefoglalva.** A lista a `local_64` (forrás-azonosítók) elemeiből épül, a `P+0x29c` bájt-tömb szerint szűrve, és csak akkor, ha a `[this+0x3f0]` 0. bitje nulla. A `0x008018a0` nem rendez.

**4. A kártya képe: `0x009a9b30`, `0x00a6aa00`, `0x009aaae0`.**
- **`0x009a9b30` (kép-foglaló, LEZÁRVA, dekompiláció).** Általános, nem Időrend-specifikus foglaló. A leíró (ESI) `+0x08` szélesség, `+0x0c` magasság, `+0x14` típus. Ha a típus `1`, nyers foglalás (`0x0097c5d0`); különben `CreateDIBSection`, 32 bites, felülről lefelé (`biHeight = -h`). Kimenet: `+0x10` pixel-mutató, `+0x24` HBITMAP. Korlát: szélesség és magasság legfeljebb `0xffff`, és `w*h <= 0x3fffffff`. Tizenegy hívóhelye van (például `0x004655da`, a `0x00608da0` három hívása, `0x008ed730`), tehát nem a kártyához tartozik. A `DAT_00d67900` bájtokban mért korlátjának tartalma **NINCS MEG** (futásidejű változó). Ghidra-kör kell: `DAT_00d67900 - írói [nem blokkoló]`.
- **`0x00a6aa00` (kép-másoló, LEZÁRVA, asm-hívás + dekompiláció).** `EAX = S` (forrás), stack: `T` (céltárgy, `esp+0x64`) és négy `-1`. Ha mind a négy `-1`, a teljes forrás másolandó: `0x009a8ca0(T+4)`, a méret `T+0x94`, `T+0x98`. Ezután `0x00a6a880` (ellenőrzés), `T+0xc == 0` esetén helyi leíró, `T+0x90 == 0` esetén `0x009a8a30` (leíró-init), különben a `T+0x94`, `T+0x98`, `T+0x2c`, `T+0x30` adatokból. Utána `0x009aabf0` (pixel-másolás), `0x009a8bc0` (a helyi leíró felszabadítása), `0x00a6ab50`. Visszatérés 0, vagy 4.
- **Hívóhely (LEZÁRVA, asm `0x008015a3`-`0x008015a8`).** `T = esp+0x64`, `EAX = S = esp+0x3c`. **JAVÍTVA (38.2.38 §6):** az `S` a helyi, 0x28 bájtos struktúra kezdete (`rekord-0x28`), nem a `+0x10` eleme. A `[this+0x2e4]` objektum vt+0 hívása (`(id, &helyi, 1)`, `0x00801580` előtt) tölti. **A kép forrása RÉSZBEN (38.2.38 §2, §6):** az `S` az info-puffer kezdete; a `[this+0x2e4]` objektum vt+0 célja NINCS MEG. Ghidra-kör kell: `[this+0x2e4] objektum vtábla +0x00 célja - a kártya képének és id-jának forrása [blokkoló]`.
- **`0x009aabf0` (szerep LEZÁRVA).** A célképet a `[param_2, param_4) x [param_3, param_5)` tartományban, soronként `memcpy`-vel tölti a forrásból. Előbb a `0x009aaae0` metszetet kéri; `3` esetén nincs másolás.
- **`0x009aaae0` (LEZÁRVA, dekompiláció).** Téglalap-metszet. Ha `R1` mind `-1`, visszatér `3`-mal. Különben `R2 := R2 ∩ R1` (bal és felső: max; jobb és alsó: min), és `0`-t ad, ha a metszet nem üres (`bal < jobb` és `felső < alsó`), különben `3`-at. A `0x009aab60`, amelyet ez hív, `3`-at ad, ha nincs vágás; a feltétele **LEZÁRVA (38.2.38 §5)**: a vágott téglalap üres, ha bal >= jobb vagy felső >= alsó.
- **Felirat (BLOKKOLT).** A kártya-útvonalon (`0x008014d0`, `0x00a6aa00`, `0x009aabf0`) nincs szövegrajzoló hívás. A `"HelveticaNeue MediumCond"` csak a `0x00801cf0`-ban van (§5). A kártya feliratának forrása **NINCS MEG**.

**5. A `0x007fd090`, `0x00802830`, `0x009833a0`, `0x009c4440`, `0x00801cf0`: szerepük.**
- **`0x007fd090` (kártya-rekord destruktor, LEZÁRVA a szerepre).** A `0x00401110` (`0xf8` lépés, tömb-törlés) és a `0x00803c10` hívja; a `0x008014d0` is hivatkozza. Lépései (asm-ellenőrizve): `call 0xa6a830` (ECX = rekord); `[rekord+0x30] := 0` (`0x7fd099`); majd az `[rekord+0x30]` azonnal visszatöltve, és `je 0x7fd0b0` (`0x7fd0a5`). Az ugrás mindig megtörténik, tehát a `0x97caf0` hívás (`0x7fd0a8`) ebben a függvényben nem fut le. Végül `0x009a8bc0` `ESI = rekord+8`-cal (a leíró felszabadítása).
  **BINÁRIS TÉNY:** a `+0x30` mutató felszabadítása elmarad. **NINCS MEG:** a `+0x30` mutató tartalma a törlés előtt (ha nem nulla, szivárgás). Ghidra-kör kell: `0x00803b50 - a +0x30 mező írója [blokkoló]` és `0x00a6a830 - mit csinál az ECX-ként kapott rekorddal [nem blokkoló]`.
- **`0x00802830` (szerep LEZÁRVA, a vezérlők neveit az asm adja).** Hívói: `0x00802c20` (szünet-ág), `0x00802980`, `0x008029f0`. Lépései (dekompiláció + asm):
  1. `[this+0x3f0] >> 1 == 0` esetén `4`.
  2. `[this+0x3f4]` a `[0, darab-1]` tartományba szorul.
  3. A `DAT_00d67914` globális nem nulla esetén négy nevesített vezérlő állapot-bájtja (`+0x20e`) íródik. Az asm szerint a név az `EDX`-ben jön a `0x009c2fc0` hívás előtt: `oneup/prev` (`0x00cbd43c`, `0x00802882`), `oneup/next` (`0x00cbd448`, `0x008028be`), `oneup/rotateleft` (`0x00cbd454`, `0x0080290d`), `oneup/rotateright` (`0x00cbd468`, `0x00802935`).
     Az állapot: `prev` = (`[this+0x3f4] == 0`); `next` = (`[this+0x3f4] == darab-1`); `rotateleft` és `rotateright` = (a `vt+0x10` eredménye == 0). A `vt+0x10` a `[this+0x2e8]` objektumon fut, az aktuális elemre (`[[this+0x3ec] + [this+0x3f4]*4]`). Hogy a bájt 1 értéke "letiltva", **FELTÉTELES**: a mezőnév nincs a binárisban.
     Ha az érték változik, a `+8` mező `|= 2` (dekompiláció).
  4. Visszatérés: `0x00802ec0([this+0x2e0])` eredménye.
  Ebből: a szünet-ág ugyanazokat az `oneup` vezérlőket frissíti, mint az egy-kép nézet. **NINCS MEG:** a `0x009c2fc0` belseje, a `0x00802ec0` és a `DAT_00d67914` tartalma. Ghidra-kör kell: `0x009c2fc0`, `0x00802ec0`, `DAT_00d67914` [nem blokkoló].
- **`0x009833a0` (LEZÁRVA, asm + dekompiláció).** Hívója a `0x00802c20` (`0x00802c48`-`0x00802c50`): `ESI = [this+0x50]` (az ablak-objektum), `EDI = [this+0x2dc]` (az új nézet-objektum). A függvény: ha `[ESI+0x64] != EDI`, akkor `[ESI+0x3b] := 0`; a régi objektumon `vt+0x28(0)`; `[ESI+0x64] := EDI`; ha `EDI != 0`, `vt+0x28()` az újon, majd `0x00983430(ESI)` (méret-értesítés, 38.2.36 §5). A visszatérés a `0x00983430` eredménye, ha nem nulla, különben 0. Szerepe: az ablak nézet-hivatkozását cseréli, és átméretezést kér.
- **`0x009c4440` (RÉSZBEN LEZÁRVA).** 2377 bájtos függvény, 15 hívóhellyel (a `0x00410fa0`-ban a `0x00410fd2`, és további 14). Sztringjei: `zip://` (`0x009c44d4`, `mov ecx,0xcb1f84`) és `%s.psd` (`0x009c45fe`, `push 0xcd9cec`). **FELTÉTELES:** útvonal- vagy fájlnév-előállító, amely zip-előtagot és PSD-kiterjesztést kezel. **NINCS MEG:** a pontos feladat és az Időrendhez való kapcsolat (Időrend-specifikus ágat nem találtam). Ghidra-kör kell: `0x009c4440 - a teljes törzs és a 0x00410fa0 hívó [nem blokkoló]`.
- **`0x00801cf0` (lépés LEZÁRVA, a rajzolás RÉSZBEN).** Hívói: `0x00803110` (`0x00803127`) és `0x008037e0` (`0x008039fe`). Lépései (dekompiláció): (1) `[this+0x3be] := 0`; (2) `0x00802230(this)` nem nulla visszatérésnél `4`; (3) rajzoló-hívások a `[this+0x46c]` célon (`0x009a9550`, `0x00aa40a0`, `0x009acb60(..., 0xa0000000)`, `0x009dc000`); (4) `vt+0x18` a `[L+0x48]` objektumon, argumentumok `(this+0x50c, &nulla)`; (5) betűkészlet: `"HelveticaNeue MediumCond"` (`0x00a48e10` készlet-objektum, `vt+0x30` kétszer, `vt+0x2c` egyszer); (6) `QueryPerformanceCounter` eredménye `[this+0x520]`-ba (double), `[this+0x518] := 0`, `[this+0x3f4] -= 1`. Szerep (FELTÉTELES): a `[this+0x50c]` kulcs szerinti kijelzés, az időbélyeg rögzítése, és a léptetési index visszalépése. **NINCS MEG:** a `0x009a9550`, `0x00aa40a0`, `0x009acb60`, `0x009dc000`, `0x00a48e10` belseje és a vt-célok. Ghidra-kör kell: `0x00a48e10 - a betűkészlet-gyár és a vt+0x2c/+0x30 célja [nem blokkoló]`.

**6. Helyesbítések.**
- **38.2.35 §1-2 (verem-előkészítés): HELYESBÍTVE.** A három hívóhely nem tesz verembe argumentumot. `0x007fe33e`: a `0x007fd800` `ret 0xc`-je takarítja a három argumentumot (`ECX = edi`, `EAX = [esp+0x18]`). `0x00801ce5`: a `push edi`-t a `0x007fd8c0` `ret 4`-je veszi vissza (`ECX = esi`, `EAX = [edi]`). `0x00803953`: `xor eax,eax`, `ECX = esi`, nincs push. A `0x008018a0` nem olvas stack-argumentumot (§3). A `local_64` és a `local_5c` a `0x008018a0` saját keretében van (`[esp+0x80]`, `[esp+0x88]`).
- **38.2.35 §5 (a csúszka rekordcímet ír): HELYESBÍTVE.** A `0x007fdd00` a rekord +0 mező ÉRTÉKÉT írja a `[this+0x510]`-be, és az `i` indexet a `[this+0x514]`-be (dekompiláció: `*(i*0xf8 + [this+0x3a8])`). A `0x007fdd00`-t a `0x007fde80` hívja (`0x007fe314`, és `0x007fdfb2`). Így mindhárom író (`0x007fdd00`, `0x007fd8c0`, `0x007fd800`) ugyanazt a mezőt használja: a rekord +0 mezőt.
- **38.2.25 §1 és 38.2.36 §2 ("kijelölt kártya indexe"): PONTOSÍTVA.** A `[this+0x514]` az index (a csúszka írja); a `[this+0x510]` a kulcs (a rekord +0 mező).
- **38.2.36 §3 (ESI+0x68 := this+0x29c): PONTOSÍTVA.** A `0x004b0190` `this`-e a `P = [this+0x2f4]` objektum, tehát `P+0x29c`, nem a `0x008018a0` `this`-ének mezője.

**7. A 38.2.36 nyitott listájának állapota (frissítve).**

| 38.2.36 tétel | új állapot | hol |
|---|---|---|
| `0x007fd800` kimenet és visszatérés | LEZÁRVA (38.2.38 §1): a kimenet a rekord +0 mező; visszatérés: találatnál `0`, nincs találatnál `-1` | §1 |
| `0x007fd8c0` író és visszatérési bool | LEZÁRVA (38.2.38 §3): a legközelebbi kártya rekord +0 mezője; a bool a `0x009a5210`-től függ: NINCS MEG | §2 |
| `0x008018a0` teljes törzs, `local_64`, `local_5c` | LEZÁRVA a helyük és a `local_5c` forrása (`P+0x29c`); NINCS MEG a `local_64` írója: a 0x004b0190 nem írja közvetlenül, a vt+0x2c célja NINCS MEG (38.2.38 §4) | §3 |
| `[[this+0x2f4]+0xc4]` konstruktora (vt+0x18, +0x1c, +0x2c) | NINCS MEG: Ghidra-kör kell | §3 |
| `0x009a9b30` kép-foglaló | LEZÁRVA (általános foglaló) | §4 |
| `0x00a6aa00` kép-másoló, a `this` | LEZÁRVA: `S = EAX` (`esp+0x3c`), `T = esp+0x64`; a hívási sorrend a dekompiláció szerint | §4 |
| `0x009aaae0` őre | LEZÁRVA: `3` = nincs másolás (metszet) | §4 |
| `0x007fd090` elemdestruktor | LEZÁRVA a szerepe; BINÁRIS TÉNY: a `+0x30` felszabadítása elmarad. NINCS MEG: a `+0x30` tartalma | §5 |
| `0x00802830` és `0x009833a0` | LEZÁRVA a szerepük; NINCS MEG: `0x009c2fc0`, `0x00802ec0` | §5 |
| `0x005696c0`, `0x005c5f90`, `0x005c5fc0` | NINCS MEG: nem volt a bemenetben. Ghidra-kör kell (változatlan) | - |

A 38.2.36 §6 blokkolt tételei:

| tétel | új állapot | hol |
|---|---|---|
| timelinedot (`0x6e8`) és listaikon | NINCS MEG: ebben a körben nem vizsgáltam. Ghidra-kör kell: `0x007fde80` 0x6e8-at olvasó és író ágai | - |
| a kulcs típusa | LEZÁRVA: rekord +0 mező (4 bájt). A 0x008014d0 rekordjain az érték `-1` (38.2.38 §2); a 0x007fc7c0 út NINCS MEG | §1, §2, §6 |
| `vt+0x2c` célja | NINCS MEG: Ghidra-kör kell: `0x004b01f2` (38.2.38 §9) | §3 |
| a kártya-kép forrása | RÉSZBEN: az info-puffer (`S`, rekord-0x28); a `[this+0x2e4]` objektum vt+0 célja NINCS MEG (38.2.38 §2, §6) | §4 |

**Frissítve (38.2.38 §7-§9):** a fenti táblák állapotai a 21. körben érvényesek. Az új Ghidra-címek: 0x007fc7c0, 0x00a6a7d0, a 0x008014d0 vt+0 hívása (0x00801523-0x0080157a), 0x004b01f2, 0x009a5210, és a 0x009aaae0 hívóhelyei. Részletek a 38.2.38 §9-ben.

**8. Cáfoló kísérlet.**
1. "A `0x007fd800` a rekord címét adja ki." CÁFOLVA: a kimenet a rekord +0 mező (`*param_3 = *(base + i*0xf8)`).
2. "A `0x007fd8c0` a rekord címét írja a `[this+0x510]`-be." CÁFOLVA: a cím helyett a rekord +0 mezőjének értékét írja.
3. "A `0x008018a0` verem-argumentumot kap." CÁFOLVA: nincs `[esp+0xe8]` fölötti hivatkozás; a hívóhelyek nem tesznek verembe.
4. "A `0x007fdd00` rekordcímet ír." CÁFOLVA: a cím helyett a mező értékét írja, és a `[this+0x514]` kapja az indexet.
5. "A `0x00802830` egyetlen bájtot írna háromszor." CÁFOLVA: négy név (prev, next, rotateleft, rotateright), négy külön vezérlő.
6. "A `0x007fd090` felszabadítja a `+0x30` mutatót." CÁFOLVA: az asm szerint a `0x97caf0` nem fut le.
7. "A `[this+0x50c]` kezdeti értéke 0." CÁFOLVA: a `0x007fa7f0` `*(X+4)`-et tölt bele.

**9. Nyitott kérdések mérlege (38.2.37).** Nyitott kérdések: 0 nyílt · 24 lezárva · 15 blokkolt · 0 hatókörön kívül · 0 csak nyitva. A 15 blokkolt tétel mind gépi úton dönthető (Ghidra-kör, lásd a §10 listát), tulajdonosra egyik sem vár.

**10. A következő Ghidra-körök (38.2.37).**
- ~~`Ghidra-kör kell: 0x007fd770 - a találat-ág visszatérési értéke, amelytől függ, fut-e a 0x008018a0 [blokkoló]`~~ **LEZÁRVA (38.2.38 §1).**
- `Ghidra-kör kell: 0x00803b50 - a rekord-másoló; a rekord +0 és +0x30 mezőjének írója [blokkoló]`
- `Ghidra-kör kell: [this+0x2e4] objektum vtábla +0x00 célja - a kártya képének és azonosítójának forrása; a helyi (esp+0x2c) és a rekord (esp+0x50) átfedése [blokkoló]`
- `Ghidra-kör kell: [P+0xc4]+0x48 objektum konstruktora és vtábla +0x18, +0x2c célja - a local_64 forrása [blokkoló]`
- ~~`Ghidra-kör kell: 0x007fbab0 - a teljes törzs, a kimeneti cím és [ECX+0x50/0x54/0x58] jelentése [blokkoló]`~~ **LEZÁRVA (38.2.38 §3).**
- `Ghidra-kör kell: 0x009a5210 - a visszatérési bool feltétele és a második lista jelentése [blokkoló]`
- `Ghidra-kör kell: 0x007fde80 - a 0x6e8 (timelinedot) és a listaikon ágai [blokkoló, 38.2.36 §6 szerint]`
- `Ghidra-kör kell: 0x00a6a830 - mit csinál az ECX-ként kapott rekorddal (a 0x007fd090 első hívása) [nem blokkoló]`
- `Ghidra-kör kell: 0x009c2fc0, 0x00802ec0, DAT_00d67914 - az oneup vezérlők névfeloldása és állapota [nem blokkoló]`
- `Ghidra-kör kell: 0x009c4440 - a teljes törzs és a 0x00410fa0 hívó [nem blokkoló]`
- `Ghidra-kör kell: 0x009a9550, 0x00aa40a0, 0x009acb60, 0x009dc000, 0x00a48e10 - a 0x00801cf0 rajzolóhívásai és a betűkészlet-gyár [nem blokkoló]`
- `Ghidra-kör kell: DAT_00d67900 - a kép-foglaló bájtokban mért korlátjának írói` ; ~~0x009aab60 - a 3-as visszatérés feltétele~~ **LEZÁRVA (38.2.38 §5).**
- `Ghidra-kör kell: 0x005696c0, 0x005c5f90, 0x005c5fc0 és a this+0x444 konstruktora [nem blokkoló, 38.2.36 szerint]`

#### 38.2.38 Az Időrend bináris feltárása, 21. kör: a találat visszatérése, a rekord +0 mezője, a legközelebbi kártya, a kulcsos hívás és a 3-as ág (#5401, 2026-10-21)

**Hatókör és módszer.** Az öt kért cím a `2026-10-21-idorend-21.txt` dekompilálásából való. A hívóláncot a korábbi körök dekompilálásai adják: `2026-10-21-idorend-20.txt` (0x007fd800, 0x007fd8c0, 0x009aaae0), `2026-10-21-idorend-9.txt` (a 0x008014d0 törzse) és `2026-10-21-idorend-18.txt` (0x007fa5b0). A döntő ágakat `pe_dis` diszasszemblálta. A `cdis` bájtszámot kap, nem utasításszámot. A konstansokat a `Picasa3.exe` fájlból olvastam ki VA alapján. Ahol a Ghidra C és az asm eltér, az asm számít. Kódot nem módosítottam, ezért CI-őr nem futott. Ideiglenes fájl nem készült.

**Konstansok (`Picasa3.exe`, VA alapján).** A típus a betöltő utasításból látszik (`fld qword` vagy `fld dword`).
- `0xcf4900`: f32 `1000000.0`. A legközelebbi-kártya keresés kezdeti minimuma (0x007fd8c3).
- `0xcf4860`: f64 `0.666`. A célérték (0x007fd926).
- `0xcf40b8`: f64 `0.01` (0x007fd984).
- `0xcf3ac0`: f64 `4294967296.0` (2^32), a negatív index korrekciója (0x007fd8fe).
- `0xc7e328`: f64 `1.0` (0x007fd9c4).
- `0xcf39f8`: f64 `3.0`, a Bernstein-együtthatók szorzója (0x007fbb3c).
- `0xc7d9d0`: f64 `2.0` (0x007fbc7d).
- `0xc72150`: f64 `0.5` (0x007fbca3).

**1. 0x007fd770: a találat visszatérése (LEZÁRVA).**
- Találatnál a 0x007fd800 a `0x007fd770(i)` visszatérését adja tovább (`0x007fd8a9`, utána `ret 0xc` a `0x007fd8b2`-nél). Nincs találatnál `-1` (`0x007fd885`: `or eax, 0xffffffff`).
- A 0x007fd770 C-kódja `void`, de az asm végén `call 0x7fd0c0` (`0x007fd7e5`), utána `pop edi`, `add esp, 0xc`, `ret 4` (`0x007fd7ea`-`0x007fd7ee`). Az EAX-ot tehát a 0x007fd0c0 hagyja maga után.
- A 0x007fd0c0 egyetlen kilépése a `ret 8` (`0x007fd11b`), előtte `xor eax, eax` áll (`0x007fd115`). Így a 0x007fd770 visszatérése **0**, és ez a találat ága.
- **A lista-újraépítés (0x008018a0) ettől függ.** A 0x007fde80-ban `test eax, eax` (`0x007fe334`), `jne 0x7fe35d` (`0x007fe336`). Ha a visszatérés nem 0, a hívás kimarad. Tehát **találatnál lefut, nincs találatnál nem fut.** A hívás argumentuma az `[esp+0x18]` kimenet (a találat kulcsa), ECX a `this` (`0x007fe338`-`0x007fe33e`).
- A 0x007fd770 számítása (a 0x007fd0c0-nak átadott érték) a visszatérést nem befolyásolja.

**Találat-feltétel (0x007fd800, asm).** A pont (x, y) az `ebx` által mutatott két f32 (`[ebx]`, `[ebx+4]`). A rekord határai egész mezők: bal `+0xdc`, felső `+0xe0`, jobb `+0xe4`, alsó `+0xe8`. Találat: bal <= x, x < jobb, felső <= y, y < alsó (`0x007fd838`-`0x007fd879`). Az indexlista sorrendjében az első találat nyer. Találatnál `*kimenet := rekord +0` (`0x007fd89f`-`0x007fd8a7`).

**2. 0x00803b50: a rekord +0 mezőjének forrása (RÉSZBEN LEZÁRVA).**
- A 0x00803b50 másoló. Nem ad új értéket, csak átmásolja a forrás rekordot. A dekompiláció szerint: `*dst = *src` (+0); `FUN_00a6a7d0(dst+4)` (JAVÍTVA 38.2.39 §1: a +4 alobjektum másolása, EAX = a forrás +4 mezője, nem „forrás nélkül"); a `+0xa0`, a `+0xa4`-`+0xcb`, a `+0xcc`-`+0xeb` és az `+0xf0`-`+0xf7` másolása. Nem másolódik: a `+0xec`-`+0xef`. (JAVÍTVA 38.2.39 §1: a `+0x4`-`+0x9f` is másolódik, a 0x00a6a7d0-on át.)
- Hívói a 0x008014d0-ban: `0x0080178d` (a régi tömb elemeinek másolása növeléskor) és `0x008017f3` (az új rekord másolása a tömb végére). A 0x007fc7c0-ban is hívódik (`0x007fcd9d`, `0x007fce84`). Azt a függvényt nem néztük meg (lásd §9).
- A `0x008017f3` forrása a helyi rekord: `lea eax, [esp+0x50]` (`0x008017ed`), majd `push eax` (forrás) és `push ecx` (cél: `[this+0x2ec] + darab*0xf8`). A helyi rekordot a `0x00801580` előtt a 0x007fa5b0 konstruktor építi: `lea ecx, [esp+0x50]` (`0x0080157c`), `call 0x7fa5b0`.
- A 0x007fa5b0 utolsó írása a +0 mezőre: `mov dword ptr [esi], 0xffffffff` (`0x007fa63c`), utána `ret` (`0x007fa645`). A helyi rekord +0 értéke tehát `-1`.
- A 0x008014d0 dekompilált törzsében a helyi rekordra más írás nincs. A rekordra írás a `+0x98`, `+0x9c` (0 értékkel, 9.txt 161-162. sor) és a `+0xcc`-`+0xd8` (P, Q, a, b) mezőkön van. A `+0x30` (`iStack_cc`) a másolás után olvasódik és felszabadul, majd a ciklus végén 0-ra íródik (9.txt 158-172. sor). A `0x00a6aa00` célja `T = esp+0x64` (`0x0080159f`), ami a rekord +4 címe, ezért a +0-t nem írja. Az esp-relatív teljes asm-átvizsgálás nem készült.
- **Következtetés.** A 0x008014d0 által épített rekordok +0 mezője **-1**. Nem azonosító, nem dátum, nem index. Az azonosító a `[this+0x3ec]` listából jön (`local_138` indexszel), és a `[this+0x2e4]` objektum vt+0 hívásába megy az info-pufferbe (`0x00801523`-`0x0080157a`). Az info a kép forrása (lásd §6). A kulcs tehát ezeken a kártyákon nem azonosít. Ez a következtetés két feltételen áll: az info-kitöltő nem ír a rekord +0 mezőjére (lásd §9), és a 0x007fc7c0 út sem ír másik értéket (JAVÍTVA 38.2.39 §1: a 0x007fc7c0 ír, a listakulcsot. A `-1` csak a 0x008014d0 tömbjére igaz.).
- A tömbbeli rekord +0x30 mezőjének írója (JAVÍTVA 38.2.39 §2): a 0x00803b50 másolja a 0x00a6a7d0-on át (a cél +0x30-át a forrás értéke írja felül), a konstruktor nullázza. Közvetlen író a 0x008014d0 törzsében nincs. A 0x00a6aa00 alias-írása NINCS MEG (38.2.39 U1).

**3. 0x007fbab0: a Bézier-kimenet és a legközelebbi kártya (LEZÁRVA).**
- A 0x007fbab0 egy racionális köbös Bézier-pontot számol. Bemenet: t (f32, veremben), `this` = ECX, a kontrollpontok a `this`-ből. A függvénynek egyetlen kilépése van (`0x007fbcdc`, `ret 4`). Kimenet: három f32 az EAX mutatta címen: `[EAX]` = out0, `[EAX+4]` = out1, `[EAX+8]` = out2 (a Ghidra C szerint).
- Kontrollpontok (x, y, w): P0 = (`+0x50`, `+0x54`, `+0x58`), P1 = (`+0x5c`, `+0x60`, `+0x64`), P2 = (`+0x68`, `+0x6c`, `+0x70`), P3 = (`+0x74`, `+0x78`, `+0x7c`).
- Bernstein-együtthatók t-ből: b0 = (1-t)^3, b1 = 3(1-t)^2 t, b2 = 3(1-t) t^2, b3 = t^3.
- N = b0·x0 + b1·x1 + b2·x2 + b3·x3, M = ugyanez az y-okkal, D = b0·w0 + b1·w1 + b2·w2 + b3·w3. A Ghidra C szerint a számláló nem szorzódik súllyal.
- out0 = (N - 0.5) / D + 0.5; out1 = (M - 0.5) / D + 0.5; out2 = 1 / D.
- Ha minden súly 1, akkor D = 1, és (out0, out1) a görbe pontja. Ez algebrai következmény, nem mérés.
- **A legközelebbi kártya (0x007fd8c0).** A `this` az obj (`this+0x2f8`). A kimenet mutatója a 0x00801cb0 szerint a `this+0x510` (38.2.37 §2).
  1. `[obj+0] := 0` (`0x007fd8d9`). Ha N = `[obj+0xb4] >> 1` nulla, a függvény 0-val kilép, és nem ír kulcsot (`0x007fd9dd`).
  2. Minden i = 0..N-1 esetén: t_i = i·`[obj+0x30]` + `[obj+0x20]` (f64; i < 0 esetén +2^32). out0_i a 0x007fbab0(t_i) kimenete, d_i = |out0_i - 0.666| (`0x0049f5c0` az abszolút érték függvénye).
  3. Ha d_i < min (a kezdeti min 1000000.0), akkor min := d_i és `[obj+0] := i`. Az első legkisebb nyer (szigorú `<`, `0x007fd943`-`0x007fd950`).
  4. Kimenet: `*kimenet := rekord[i*] +0` (`0x007fd967`-`0x007fd97a`). A §2 szerint ez `-1` a 0x008014d0 rekordjain. **(JAVÍTVA 38.2.39 §1: a rekordtömb az `obj+0xb0`, vagyis T+0x3a8, és ezt a 0x007fc7c0 építi. Ezen a +0 a listakulcs, nem `-1`.)**
  5. Visszatérési érték (AL, `0x007fd97c`-`0x007fd9e9`): 0, ha nem teljesül |`[obj+0x18]`| <= 0.01·`[obj+0x30]` (`0x007fd981`-`0x007fd991`). Különben legyen c = `[obj+0x4c] >> 1`, X = `[obj+0x48]`, a = X+0x18, b = X+0x20. Ha c >= 2, az érték 0. Ha c = 0, az érték 1. Ha c = 1, az érték 1, ha a = b, vagy ha v > 1.0, ahol v = (0x009a5210() - a) / (b - a). Egyébként 0.
  - A `0x009a5210` értéke LEZÁRVA (38.2.39 §5): az első hívás óta eltelt másodperc.
- Pontosítás: a „legközelebbi kártya" nem térbeli távolság. d_i a görbe x-kimenetének távolsága a 0.666 célértéktől. A t_i a kártya indexéből (i) jön.

**4. 0x004b0190: a kulcsos hívás mellékhatásai (RÉSZBEN LEZÁRVA).**
- `L = [P+0xc4]` (P a belépéskor az EAX). Rekurzív zár a `GetCurrentThreadId` alapján: `[L+0x88]` a tulajdonos szál, `[L+0x8c]` a beágyazási számláló. Zárás: ha `[L+0x74]` nulla, a `[L+0x68]` objektum vt+0x18 hívása (`0x004b01c9`-`0x004b01d1`), különben `EnterCriticalSection(L+0x90)` (`0x004b01c1`). Oldás a legkülső szinten: vt+0x1c, vagy `LeaveCriticalSection`. Beágyazott hívásnál csak a számláló változik.
- Hívás: `call [vt+0x2c]` a `[L+0x48]` objektumon. ECX = L+0x48 (`0x004b01e9`). Verem: `push esi` (a kimeneti struktúra), `push eax` (a kulcs), `call edx` (`0x004b01f0`-`0x004b01f2`). A dekompilált C csak a kulcsot mutatja, az asm szerint két argumentum van: (kulcs, ESI).
- A hívás után beállítja az ESI mutatóit a P objektum mezőiből: `+0x68 := P+0x29c` (`0x004b01fa`), `+0x6c` (`0x004b021a`), és további mutatók az ESI+0x6c-+0xc0 tartományban (a P+0x2a4 … P+0x2d0 mezőkből).
- Ellenőrzés: ha `[ESI+0x5c]` vagy `[ESI+0x64]` nulla, a visszatérés -1, különben 0. A legkülső hívás a visszatérés előtt oldja a zárat; beágyazott hívásnál csak a számláló csökken.
- Az ESI+0x60-0x67 (a local_64) közvetlen írása nincs a függvényben: a +0x50-+0x6f tartományban csak `+0x68` és `+0x6c` íródik. A local_64-et tehát nem ez a függvény írja közvetlenül. A lehetséges író a vt+0x2c célja, mert ESI-t kap. Ennek célja **NINCS MEG** (§9).

**5. 0x009aab60: a 3-as visszatérés feltétele (LEZÁRVA).**
- Bemenet: EAX = R, a vágandó téglalap (`[R]` bal, `[R+4]` felső, `[R+8]` jobb, `[R+0xc]` alsó). ECX = a korlát-téglalap: R_k = `[ECX+8]` (jobb korlát), B_k = `[ECX+0xc]` (alsó korlát).
- 1. ág: ha R mind a négy mezője -1 (`0x009aab66`-`0x009aab78`), R := (0, 0, R_k, B_k).
- 2. ág (különben): bal := max(bal, 0), felső := max(felső, 0), jobb := min(jobb, R_k), alsó := min(alsó, B_k). A dekompiláció szerint; az asm `setl` ága a negatív bal értéket nullázza.
- Visszatérés: **0**, ha bal < jobb ÉS felső < alsó (előjeles összehasonlítás), különben **3**. Asm: `jge` (`0x009aabd1`) és `jl` (`0x009aabd9`) a 3-as ágra, `mov eax, 3` (`0x009aabdb`); a 0 ág `xor eax, eax` (`0x009aabe4`).
- A vágott R-be íródik vissza (`0x009aabc9`).
- A 0x009aaae0 (hívás: `0x009aab06`): ha az első téglalap (EDI) mind -1, a 0x009aaae0 eleve 3-at ad (`0x009aaafb`). Különben az ESI téglalapot vágja a 0x009aab60, és ha az eredmény nem 3, az ESI-t metszi az EDI-vel (max/min). 0-t ad, ha a metszet nem üres, különben 3.
- A 0x009aab60-nak 18 hívóhelye van. A feltétel mindenhol ugyanaz, a korlát (ECX) hívóhelyenként más lehet. A 0x009aaae0 nem állítja be az ECX-et (`0x009aaae0`-`0x009aab06`), ezért a korlát forrása a hívóban van: NINCS MEG (§9).

**6. Helyesbítések a korábbi szakaszokban.**
- **38.2.26 §1 (JAVÍTVA):** az `info` 0x28 bájtos, nem 0x24 bájtos. A dekompilált helyi változók szerint a struktúra `-0x124`-től `-0xfc`-ig tart, és a rekord (`-0xfc`) közvetlenül utána kezdődik.
- **38.2.37 §4, az `S` mutató (JAVÍTVA):** a `push eax` (`0x008015a3`) után számolt `esp+0x3c` a helyi struktúra kezdete (`rekord-0x28`), nem a `+0x10` eleme. A `T = esp+0x64` a push előtt számolt érték, vagyis a rekord +4 címe.
- **38.2.37 §1 és §2 (LEZÁRVA):** a 0x007fd770 visszatérése 0 (§1). A 0x007fbab0 kimenete nem címfeltevés: a törzs a `[EAX]`, `[EAX+4]`, `[EAX+8]` címekre ír (§3). A `d_i` a kimenet 0. elemétől vett távolság (out0).
- **38.2.37 §3 (MEGERŐSÍTVE):** a vt+0x2c argumentumai (kulcs, ESI) helyesek. A dekompilált C ezt nem mutatja.
- **38.2.37 §4 (LEZÁRVA):** a 0x009aab60 feltétele kész (§5).
- **A kulcs típusa (PONTOSÍTVA):** a típus (rekord +0, 4 bájt) helyes. Az értéke a 0x008014d0 rekordjain `-1` (§2).

**7. A 38.2.37 §7 állapotváltozásai.**

| tétel | régi állapot | új állapot |
|---|---|---|
| `0x007fd800` visszatérés | RÉSZBEN | LEZÁRVA: találatnál 0, nincs találatnál -1 (§1) |
| `0x007fd770` értéke | NINCS MEG | LEZÁRVA: 0 (§1) |
| `0x007fd8c0` bool | RÉSZBEN | LEZÁRVA, kivéve a `0x009a5210` értékét: NINCS MEG (§3) |
| `0x007fbab0` kimenete | BLOKKOLT | LEZÁRVA: `[EAX]`, `[EAX+4]`, `[EAX+8]` (§3) |
| `0x009aab60` feltétele | NINCS MEG | LEZÁRVA (§5) |
| rekord +0 írója | BLOKKOLT | RÉSZBEN: a 0x008014d0 rekordjain `-1` (§2); a 0x007fc7c0 és a +0x30 NINCS MEG |
| `local_64` írója | BLOKKOLT | RÉSZBEN: a 0x004b0190 nem írja közvetlenül; a vt+0x2c célja NINCS MEG (§4) |
| kártya-kép forrása | NINCS MEG | RÉSZBEN: az info-puffer (`S`, rekord-0x28); az info kitöltőjének célja NINCS MEG (§2, §6) |
| `timelinedot` | NINCS MEG | változatlan |

**8. Nyitott kérdések mérlege (38.2.38).** 0 nyílt · 3 lezárva (Q1, Q3, Q5) · 2 részben (Q2, Q4) · 5 blokkolt (§9, az első öt tétel) · 1 nem blokkoló (§9, a hatodik tétel) · 0 hatókörön kívül · 0 csak nyitva.

**9. A következő Ghidra-körök (38.2.38).** A 38.2.37 §10 többi tétele változatlan. **Állapot: a 38.2.39 §7 táblázata frissíti ezt a listát.**
- `Ghidra-kör kell: 0x007fc7c0 - a második rekordépítő: a 0x007fa5b0 utáni +0 írások, és melyik [this+0x2ec] tömböt tölti. [blokkoló: a -1 általánosításához]`
- `Ghidra-kör kell: 0x00a6a7d0 - a +4 alobjektum felépítése: ír-e a +0x30 mezőbe (a 0x00803b50 nem másolja a +0x30-at). [blokkoló]`
- `Ghidra-kör kell: 0x008014d0 vt+0 hívása (0x00801523-0x0080157a) - a [this+0x2e4] objektum vt+0 célja; ír-e az info (rekord-0x28 és rekord között) végén túl a rekord +0 mezőjébe. [blokkoló a -1 következtetéshez]`
- `Ghidra-kör kell: 0x004b01f2 - az indirekt vt+0x2c hívás célja, az [L+0x48] objektum vtábla-címe és konstruktora; ír-e ESI+0x60-0x67-be. [blokkoló]`
- `Ghidra-kör kell: 0x009a5210 - a visszatérési érték v, amelytől a 0x007fd8c0 c = 1 ága függ. [blokkoló]`
- `Ghidra-kör kell: 0x009aaae0 hívóhelyei (16 db) - melyik hívó adja az ECX korlát-téglalapját a 0x009aab60-nak. [nem blokkoló]`

#### 38.2.39 Az Időrend bináris feltárása, 22. kör: a kulcs a rekordban, a két vt+0 hívás, a +0x30 mező, a kép másolása, az idő és a konstruktor (#5401, 2026-10-21)

**Hatókör és módszer.** A hat kért cím a `2026-10-21-idorend-22.txt` dekompilálásából való. A hívóláncot és a döntő ágakat `pe_dis` (`cdis`) diszasszemblálta. A hívóhelyeket a bináris index `xrefs` táblája adta, és bájt-szintű `e8` kereséssel ellenőriztem. Az indexben két hívóhely a hívó függvény belépési címét mutatja, nem a hívó utasítást: a `0x008037e0` valódi hívója `0x005e9787` (az index `0x005e8a70`-et ír), a `0x007fd8c0` valódi hívója `0x00801cd8` (az index `0x00801cb0`-at ír). Ez a bináris-index csapdái között már leírt tanulság, most újra láttam. Kódot nem módosítottam, ezért CI-őr nem futott. Ideiglenes fájl nem készült.

**Fogalmak.**
- **Rekord**: 0xf8 (248) bájtos elem. Két tömbben van:
  - **T+0x2ec tömb** (darabszám: T+0x2f0). A 0x008014d0 építi.
  - **T+0x3a8 tömb** (darabszám: T+0x3ac). A 0x007fc7c0 építi. Ez az `obj+0xb0` tömb, mert `obj = T+0x2f8`.
- **T**: az Időrend-objektum, 0x890 bájt. A 0x008037e0 foglalja (0x008038fb-0x00803905: `push 0x890`, `call 0x97c5d0`). Vtáblája `0xcbd66c` (a 0x007fa7f0 írja, 0x007fa804).
- **Kép-alobjektum**: a rekord +0x04-től +0x9f-ig tartó 0x9c bájt. A 0x00a6a7d0 másolja.
- **Info-puffer**: 0x28 bájt, közvetlenül a rekord előtt (rekord-0x28). A 0x008014d0 veremében az info címe a 0x0080156b `lea esi,[esp+0x2c]` (a `push 1` után), a rekordé a 0x0080157c `lea ecx,[esp+0x50]`. A különbség 0x28.

**Helyesbítések a korábbi szakaszokban (JAVÍTVA).**
- **38.2.38 §2**: a 0x00803b50 a +0x4-+0x9f mezőt is másolja. A 0x00803b65 (`lea eax,[ebp+4]`) és a 0x00803b68 (`push ecx`, ecx = a cél +4) után a 0x00803b69 `call 0x00a6a7d0` a forrás +4 alobjektumából másol a cél +4 alobjektumába. A „forrás nélkül" leírás téves volt.
- **38.2.38 §2 és §3**: a `-1` következtetés csak a T+0x2ec tömbre (0x008014d0) igaz. A legközelebbi kártya keresése (0x007fd8c0) a T+0x3a8 tömbön dolgozik, és ott a +0 a listakulcs (§1).
- **38.2.38 §2**: a +0x30 írója nem NINCS MEG: a másolás és a konstruktor írja, lásd §2b.
- **38.2.38 §3**: a 0x009a5210 értéke nem NINCS MEG, lásd §5.

**1. 0x007fc7c0: a második rekordépítő (LEZÁRVA).**

Igen, a 0x007fc7c0 ír a rekord +0 mezőjébe, és ez a listakulcs. Tehát a kulcs nem mindig `-1`.

- A `this` a T+0x2f8 (0x007fc7ca `mov edi,eax`; a hívó 0x008039bf `lea eax,[esi+0x2f8]`, majd 0x008039c5 `call 0x7fc7c0`). A tömb a `[this+0xb0]`, vagyis T+0x3a8. Csak ez a hívóhely hívja (bájt-keresés).
- A helyi rekordot a 0x007fa5b0 konstruktor építi (0x007fcc6e `lea ecx,[esp+0x70]`, 0x007fcc72 `call 0x7fa5b0`). A konstruktor a +0 mezőbe -1-et ír.
- A 0x007fcc77 `mov edx,[ebx+esi*4]` a kulcsot tölti az `edx`-be. A kulcs a `local_158[iVar8]` elem, vagyis az első ciklusban a 0x004ae4e0 kimenetéből gyűjtött azonosító.
- A 0x007fcca0 `mov [esp+0x84],edx` a kulcsot a rekord +0 mezőjére írja (E a függvény belépéskori esp-je; ekkor esp = E-0x14, a cím E+0x70). Ez felülírja a konstruktor -1-jét.
- A tömbbe másolás: 0x007fce7e-0x007fce84 (`lea edx,[esp+0x70]`, `push edx`, `push eax`, `call 0x803b50`). A tömb elemének +0 mezője tehát a kulcs.
- A kép forrása ennél a hívónál a 0x004ae430 kimenete (a helyi `out` a `lea eax,[esp+0x44]`, vagyis E+0x30). **JAVÍTVA (38.2.40 §4):** a `lea eax,[esp+0x44]` (0x007fcc9c) a 0x00a6aa00 this-je (EAX), és nincs igazolva, hogy a 0x004ae430 kimenete. NINCS MEG. A 0x00a6aa00 hívás (0x007fcca7) után, ha a visszatérés nem nulla (0x007fccac-0x007fccb0), a függvény azonnal visszatér ezzel az értékkel. A hívó (0x008039c5) a visszatérést nem vizsgálja.

**Mit jelent ez?** A legközelebbi kártya kulcsa (a 0x007fd8c0 `*kimenet := rekord+0` lépése) a T+0x3a8 tömb +0 mezője, tehát a listakulcs. A `-1` csak a T+0x2ec tömbön (0x008014d0) igaz.

**2. 0x008014d0: a vt+0 hívás és a +0x30 mező (RÉSZBEN: a cél NINCS MEG).**

**2a. A vt+0 hívás (0x00801523-0x0080157a).**
- Ha `[T+0x2e4]` nulla, a hívás kimarad: 0x00801523 `cmp [edi+0x2e4],ebp` (EBP = 0 a 0x008014de `xor ebp,ebp` óta), 0x0080155d `je 0x80157c`.
- `obj2 = [T+0x2e4]` (0x0080155f). A vtábla `[obj2]` (0x00801565). A célcím a vtábla 0. slotja, vagyis `[vtábla+0]` (0x00801567). A hívás `call edx` (0x0080157a), ECX = obj2.
- Argumentumok: a kulcs (`[T+0x3ec][i]`, 0x00801570-0x00801576), az info-puffer címe, és 1.
- A visszatérési értéket a hívó nem használja.
- A hívó után nincs `add esp`, ezért a 12 bájt argumentum takarítását a hívott félnek kell végeznie. Ezt a hívott törzs nem igazolja, a kódalakból következtetek rá.
- Az obj2 eredete: a 0x007fa7f0 konstruktor a bemeneti blokk +0x10 mezőjét írja T+0x2e4-be (0x007fa81b-0x007fa81e). A bemeneti blokk a 0x005e8a70 veremében van (0x005e9782 `lea ecx,[esp+0x64]`). A +0x10 mezőt a 0x005e9750 (`mov [esp+0x74],esi`) vagy a 0x005e974a (`mov [esp+0x74],eax`, előtte `add eax,0x4c`) írja. Melyik ág fut, az a 0x005e9745 `je` előtti flagtől függ. **LEZÁRVA (38.2.40 §3):** a 0x005e9745 `je` a 0x005e9750-re ugrik, ha `M = [CThumbUI+0x2bc] = 0`; ekkor 0 íródik. Egyébként a 0x005e974a írja M+0x4c-t.
- A vt+0 az info-puffer címét kapja argumentumként. A 0x00a6aa00 ezt az info-puffert használja: a `this` az info-puffer (0x008015a4 `lea eax,[esp+0x3c]`, 0x008015a8 `call 0x00a6aa00`), és a 0x00a6aa00 az info +0x8 és +0xc mezőjét olvassa. Mindkettőnek pozitívnak kell lennie, különben a visszatérés 4 (0x00a6aa1b-0x00a6aa27).
- **A cél: NINCS MEG.** Az obj2 osztályát és a vtábla 0. slotját nem azonosítottam. Ghidra-kör kell: U2.

**2b. A +0x30 mező írója (LEZÁRVA a másolási és a konstruktor-útra).**
- A konstruktorban a 0x007fa5b0 a 0x00512390-et hívja, EDI = rekord+4 mellett (0x007fa5b4, 0x007fa5b7). A 0x005123c5 `mov [edi+0x2c],esi` nullázza a rekord +0x30 mezőt. ESI = 0, mert a 0x00512394 `xor esi,esi` óta nem változott (a 0x009a8a30 hívás push/pop-olja az esi-t).
- A másolásban (0x00803b50 → 0x00a6a7d0): a cél +0x30 mezőjét a 0x00a6a830 előbb felszabadítja és nullázza (0x00a6a853-0x00a6a863). Utána a 0x00a6a7d0 a forrás értékét másolja (0x00a6a81f `rep movsd`). A cél +0x30 tehát a forrás +0x30 értékét kapja.
- A 0x008014d0 törzsében a helyi rekord +0x30 mezőjére egyetlen közvetlen írás van: a ciklus végi nullázás (dekompilált sor: `iStack_cc = 0`). Ez nullát ír.
- A 0x00a6aa00 csak olvassa a +0x2c és +0x30 mezőket (0x00a6aaf2-0x00a6aaf5). A törzsben `[reg+0x2c]` alakú írás nincs.
- Ezért a +0x30 0 marad. Ez az állítás a 0x00a6aa00 alias-írásától függ, ezt az U1 tétel zárná le.

**3. 0x00a6a7d0: szerep a kép útjában (LEZÁRVA).**

- A függvény a kép-alobjektum (0x9c bájt) másoló-értékadása: `cél := forrás`. EAX = a forrás (this), a veremben a cél címe. A rekordmásolóban (0x00803b50) a forrás a forrásrekord +4 mezője, a cél a célrekord +4 mezője.
- Lépései (0x00a6a7d0-0x00a6a821):
  1. Azonos cím esetén nincs teendő (0x00a6a7da).
  2. A cél régi tartalmát a 0x00a6a830 szabadítja fel és nullázza: a cél első mezőjét (számláló-blokk mutató) és a +0x2c mezőt (a rekord +0x30). A hívás előtt az `esi` a cél (0x00a6a7de-0x00a6a7e0).
  3. A forrás első mezője: ha 0, a 0x0097c5d0(4) új, 4 bájtos blokkot foglal, a forrásba írja, és a számlálót 2-re állítja (0x00a6a7e5-0x00a6a801). Ha nem 0, `InterlockedIncrement` (0x00a6a803-0x00a6a804). Így a két példány **ugyanazt a számláló-blokkot osztja meg**.
  4. A 0x009a8ca0 a forrás rekord+8 belső objektumából a cél rekord+8 objektumába másol (0x00a6a80d-0x00a6a811).
  5. A forrás 0x27 dword-jét (0x9c bájt) a célba másolja (0x00a6a818-0x00a6a81f, `rep movsd`). Ez a 4. lépés eredményét felülírja.
- Szerep: a számláló-blokkot megosztja. A 0x9c bájt többi részét nyers másolattal viszi át, számlálás nélkül. A pixelpuffer (a mutatók mögött) sorsa NINCS MEG.
- Hol van a kép útjában: a 0x00803b50 minden tömbbeli rekordmásolása ezen megy át. A kép-alobjektumot a 0x00a6aa00 tölti (0x008015a8 a 0x008014d0-ban, 0x007fcca7 a 0x007fc7c0-ban). A másolat és az eredeti ugyanazt a számláló-blokkot mutatja.

**4. 0x004b01f2 (a 0x004b0190 zárt hívása): vt+0x2c (RÉSZBEN: a cél NINCS MEG).**

- `L = [P+0xc4]` (0x004b01dd `mov eax,[edi+0xc4]`). `edx = [L+0x48]` (0x004b01e3): az objektum vtáblája, mert az objektum a `L+0x48` címen áll. `edx = [edx+0x2c]` (0x004b01e6): ez a vtábla 11. slotja. `ECX = L+0x48` (0x004b01e9): az objektum címe, vagyis a `this`. A veremben ESI (0x004b01f0 `push esi`) és a kulcs (0x004b01f1 `push eax`), majd `call edx` (0x004b01f2).
- **A cél NINCS MEG.** A vtábla címét nem azonosítottam, mert az L konstruktora hiányzik. Ghidra-kör kell: U3.
- ESI+0x60-0x67 (a `local_64`): a 0x004b0190 törzsében nincs közvetlen írás. A 499 bájtos törzs utasításait diszasszemblálva átnéztem. Az ESI+0x60-0x67 tartományba eső hivatkozás egyetlen van: a 0x004b02df `cmp dword ptr [esi+0x64],edi`, ez olvasás. A lehetséges író a 11. slot hívott függvénye, de annak törzse nem ismert. **NINCS MEG.**

**5. 0x009a5210: az idő (LEZÁRVA).**

- A visszatérési érték az x87 ST(0)-ban, 80 bites lebegőpontos szám: `(QPC_most - QPC_első) * (1/QPF)`, vagyis másodperc. A QPC és a QPF a Windows nagy felbontású órája (a hívott Win32 függvények: `QueryPerformanceCounter`, `QueryPerformanceFrequency`).
- Az „első" a folyamat első 0x009a5210-hívása: a `_DAT_00d678f0` globális nulla-ellenőrzése (dekompilált C: `if (_DAT_00d678f0 == 0.0)`). Ezért az első hívás értéke közel 0. A frekvencia reciproka a `_DAT_00d678e8` globálisban van, az első hívás állítja be.
- A 0x007fd8c0 döntése (asm):
  - Kapu (0x007fd98c-0x007fd991): ha `|[obj+0x18]| > 0.01*[obj+0x30]`, a függvény 0-val tér vissza, és nem hívja a 0x009a5210-et. Különben a hívás fut (0x007fd993).
  - c = `[obj+0x4c] >> 1` (0x007fd998-0x007fd99d). c >= 2: 0. c = 0: 1 (0x007fd9a4-0x007fd9e7).
  - c = 1: X = `[obj+0x48]`, a = `[X+0x18]`, b = `[X+0x20]`. Ha a = b (0x007fd9ac-0x007fd9b4): 1. Különben v = (t - a) / (b - a), ahol t a 0x009a5210 visszatérése (0x007fd9b6-0x007fd9c2). Az eredmény 1, ha v > 1.0 (0x007fd9c4-0x007fd9cf, a 1.0 a `[0xc7e328]`). Különben 0.
- Vagyis a 0x009a5210 a t időt adja. A c = 1 ágban ebből lesz a v arány, amely azt mutatja, hol tart az eltelt idő a [a, b] intervallumban.

**6. 0x007fa5b0: a rekord-konstruktor mezőkiosztása (LEZÁRVA az írt mezőkre).**

A konstruktor a 0x00512390-et (a +4 alobjektum alapkonstruktora) és a 0x009a8a30-at (a rekord +8 belső objektumának konstruktora) hívja. Ezek és a saját írásai:

| rekord-offset | érték a konstruktor után | író címe |
|---|---|---|
| +0x00 | -1 (0xffffffff) | 0x007fa63c |
| +0x04 | 0 (a számláló-blokk mutató) | 0x00512396 |
| +0x08 | 0 | 0x00512398 |
| +0x0c | 0 | 0x005123b4 |
| +0x10 | 0 | 0x005123b7 |
| +0x14 | 0 | 0x005123ba |
| +0x18 | 0 | 0x005123bd, 0x009a8a6b |
| +0x1c | word 1 | 0x0051239a |
| +0x1e | word 0 | 0x005123a0 |
| +0x20 | 0 | 0x005123a4 |
| +0x24 | 0 | 0x005123a7 |
| +0x28 | -1 | 0x005123aa |
| +0x2c | 0 | 0x005123b1, 0x009a8a4d |
| +0x30 | 0 | 0x005123c5 |
| +0x94 | 0 | 0x005123c8 |
| +0x98 | 0 | 0x005123d4 |
| +0x9c | 0 | 0x005123ce |
| +0xa0 | 0x100 | 0x007fa632 |
| +0xa4 | 1.0 (f32) | 0x007fa5be |
| +0xa8 | 0.0 (f32) | 0x007fa5cf |
| +0xac | 0.0 (f32) | 0x007fa5d6 |
| +0xb0 | 0.0 (f32) | 0x007fa5dc |
| +0xb4 | 1.0 (f32) | 0x007fa5f6 |
| +0xb8 | 0.0 (f32) | 0x007fa5e2 |
| +0xbc | 0.0 (f32) | 0x007fa5e8 |
| +0xc0 | 0.0 (f32) | 0x007fa5ee |
| +0xc4 | 1.0 (f32) | 0x007fa5fc |
| +0xc8 | bájt 1 | 0x007fa5c4 |
| +0xcc | 0.0 (f32) | 0x007fa602 |
| +0xd0 | 0.0 (f32) | 0x007fa608 |
| +0xd4 | 0.0 (f32) | 0x007fa60e |
| +0xd8 | 0.0 (f32) | 0x007fa614 |
| +0xdc | 0 | 0x007fa61a |
| +0xe0 | 0 | 0x007fa620 |
| +0xe4 | 0 | 0x007fa626 |
| +0xe8 | 0 | 0x007fa62c |

- Nem íródik a konstruktorban: +0x34-+0x8f, +0xec-+0xf7, és a +0x94-+0x9f közötti bájtok nagy része (csak a +0x94, +0x98, +0x9c dword-ök vannak nullázva). Ezek jelentése **NINCS MEG**.
- A 0x00803b50 másolja a +0xf0-+0xf7 mezőt (0x00803bef-0x00803bf6, `fld/fstp qword`), tehát a nem inicializált értéket is átviszi. A +0xec-+0xef nem másolódik.

**7. A 38.2.38 nyitott listájának állapota (§9) és az új Ghidra-címek.**

| 38.2.38 §9 tétel | állapot | mit mutat |
|---|---|---|
| 0x007fc7c0: második rekordépítő, +0 írás | LEZÁRVA (§1) | ír: a listakulcs (0x007fcca0, 0x007fce84). A tömb: T+0x3a8. |
| 0x00a6a7d0: +4 alobjektum, a +0x30 írója | LEZÁRVA a másolási útra (§2b, §3) | a +0x30-at a másolás írja a forrásból. Az alias-írás a 0x00a6aa00-ban: U1. |
| 0x008014d0 vt+0 hívás: cél és túlírás | BLOKKOLT (§2a) | a cél obj2 vtáblájának 0. slotja, obj2 = T+0x2e4. Az obj2 osztálya NINCS MEG: U2. |
| 0x004b01f2: vt+0x2c cél, local_64 | BLOKKOLT (§4) | a cél a `[L+0x48]` vtáblájának 11. slotja. A vtábla NINCS MEG: U3. |
| 0x009a5210: visszatérési érték | LEZÁRVA (§5) | eltelt másodperc az első hívás óta |
| 0x009aaae0 hívóhelyei (16 db) | NINCS MEG, nem blokkoló | ebben a körben nem néztem meg: U6 |

**Új Ghidra-körök (38.2.39):**
- `Ghidra-kör kell: 0x005e9750 (FUN_005e8a70) - az ESI értéke és a 0x005e9745 előtti flagforrás; az obj2 osztálya és a vt+0 célja. [blokkoló: 0x008014d0 vt+0 cél]` (U2) **ÁLLAPOT (38.2.40 §3): RÉSZBEN LEZÁRVA** (az ág és az obj2 = M+0x4c kész; az M osztálya és a vt+0 cél NINCS MEG).
- `Ghidra-kör kell: 0x004b01e3 - az [L+0x48] objektum konstruktora (a vtábla címe) és a vt+0x2c cél. [blokkoló: 0x004b01f2 cél és local_64]` (U3) **ÁLLAPOT (38.2.40 §1): NINCS MEG** (a vtábla-cím és a 11. slot célja nincs meg).
- `Ghidra-kör kell: 0x0080157a (a vt+0 hívott függvénye, az U2 után) - ír-e az info-puffer (rekord-0x28) végén túl a rekord +0 mezőre. [blokkoló: a -1 túlírási kérdés]` (U4) **ÁLLAPOT (38.2.40 §2): NINCS MEG** (a geometria LEZÁRVA, a hívott törzs nincs meg).
- `Ghidra-kör kell: 0x00a6aa00 - a teljes törzs, különösen a kép-alobjektum írói és a rekord +0x30. [nem blokkoló, de a +0x30 = 0 állítás feltétele]` (U1) **ÁLLAPOT (38.2.40): NINCS MEG** (ebben a körben nem vizsgáltam).
- `Ghidra-kör kell: 0x008014d0 T+0x2ec tömbjének olvasói. [nem blokkoló]` (U5) **ÁLLAPOT (38.2.40): NINCS MEG** (nem vizsgáltam).
- `Ghidra-kör kell: 0x009aaae0 hívóhelyei (16 db). [nem blokkoló]` (U6) **ÁLLAPOT (38.2.40): NINCS MEG** (nem vizsgáltam).

**Amit KIZÁRTAM (megdőlt állítások).**
- „A kulcs mindig `-1`”: megdőlt a legközelebbi kártyára (T+0x3a8 tömb).
- „A 0x00803b50 nem másolja a +0x4-+0x9f mezőt”: megdőlt.
- „A 0x00a6a7d0 forrás nélkül épít”: megdőlt.
- „A 0x009a5210 értéke NINCS MEG”: megdőlt, LEZÁRVA.

**Nyitott kérdések mérlege (38.2.39).** 3 blokkolt (vt+0 cél, vt+0x2c cél, local_64) · 3 nem blokkoló NINCS MEG (U1, U5, U6) · 5 lezárva (§1, a +0x30 másolási útja, §3, §5, §6 az írt mezőkre) · 0 csak nyitva.

**Frissítve (38.2.40):** a fenti U-tételek állapotát a tételek mellé írtam. A teljes, frissített lista és az új Ghidra-címek (U7-U9) a 38.2.40 §6 táblájában vannak.

#### 38.2.40 Az Időrend bináris feltárása, 23. kör: a vt+0 hívás objektuma, az L-vtábla, a kulcs forrása és a kártya-újraépítés (#5401, 2026-10-21)

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-23.txt` volt, öt címmel: `0x004b01e3`, `0x0080157a`, `0x005e8a70`, `0x005e9750` és `0x007fcca0`. A `0x005e8a70` és a `0x005e9750` ugyanazt a `FUN_005e8a70` törzset adja két dumpban, új C-sor nélkül, ezért az ágat a diszasszembly döntötte el. Az asm-ellenőrzés `pe_dis.cdis`-szel történt, legfeljebb 0x140 bájtos darabokban. A hívóhelyeket az index `xrefs` táblája adta. Ez függvényszintű: a hívó függvény belépési címét adja, nem a hívó utasítást (a korábban leírt csapda). A vtábla-kereséshez a `.text` bájtjait néztem 1 MiB-os darabokban, capstone nélkül. Kódot nem módosítottam, ezért CI-őr nem futott. Ideiglenes fájl nem készült.

**Bizonyítottsági fok.** Az asm-ből igazolt állítások erősek. A visszatérési takarításra épülő állítás feltételes (lásd §2).

**Fogalmak.**
- **M** = `[CThumbUI+0x2bc]`. Az `ebx` a `CThumbUI` this-je (0x005e8a7d `mov ebx,[ebp+8]`), 0x005e970d `mov eax,[ebx+0x2bc]`.
- **obj2** = `T+0x2e4`. Értéke `M+0x4c`, ha M nem nulla, különben 0 (§3).
- **L** = `[P+0xc4]`, ahol P a 0x004b0190 belépési EAX-a (0x004b0193 `mov edi,eax`, 0x004b0195 `mov ebp,[edi+0xc4]`).
- **X** = `L+0x48`, a vt-hívás objektuma (0x004b01e3).
- **W** = `L+0x68`, a zár-objektum (0x004b019b `add ebp,0x68`). A zárolás a vt+0x18 (0x004b01c9-0x004b01d1).

**1. 0x004b01e3: az X vtábla és a 11. slot (NINCS MEG: a vtábla-cím és a slot célja).**

Igazolt (asm):
- 0x004b01dd `mov eax,[edi+0xc4]`: EAX = L.
- 0x004b01e3 `mov edx,[eax+0x48]`: EDX = az X vtáblája.
- 0x004b01e6 `mov edx,[edx+0x2c]`: a 0x2c / 4 = 11. slot (0-tól számozva).
- 0x004b01e9 `lea ecx,[eax+0x48]`: ECX = X.
- 0x004b01f0 `push esi`, 0x004b01f1 `push eax` (a kulcs), 0x004b01f2 `call edx`. A hívás után nincs `add esp` (0x004b01f4 a `lea eax,[edi+0x29c]`), tehát a két argumentum takarítását a hívottnak kell végeznie.

NINCS MEG:
- **Vtábla-cím.** A 2856 rtti-vtábla címét a `.text`-ben `c7 [40-47] 48 imm32` alakú írásokra kerestem: 163 találat. Ezek közül 6 írásnál ugyanabban az ablakban a `+0x68` mezőre is vtábla-cím íródik. Ezek a `CollaborativeUpload` és az `LHUpload` feltöltő osztályok, nem L-konstruktorok. L konstruktora más módon íródhat (külön hívott konstruktor), ezt nem találtam meg.
- **A 11. slot célja.** A hívott kapja a kulcsot és az ESI-t. A törzsét nem láttam. A 0x004b0190 a hívás után ESI+0x5c és ESI+0x64 értékét nézi (a bemeneti fájl 115. sora). A local_64 (ESI+0x60) írója nincs megmérve.

Ghidra-kör kell: `0x004b0190 - a P osztálya és a [P+0xc4] = L írója; az [L+0x48] objektum konstruktora (vtábla-cím); a 11. slot (vt+0x2c) célja [blokkoló: local_64, 0x004b01f2 cél]` (U3).

**2. 0x0080157a: túlír-e az info-puffer végén (NINCS MEG; a geometria LEZÁRVA).**

Igazolt (asm, 0x00801523-0x0080157c):
- Az info-puffer 0x28 bájtos. A 0x00801529-0x00801555 utasításai az `esp0+0x28`-tól `esp0+0x4f`-ig terjedő részt töltik ki (`esp0` a `push 1` előtti esp). Az írt eltolások: `+0x28`, `+0x2c`, `+0x30`, `+0x34`, `+0x38`, `+0x40`, `+0x44`, `+0x4c` dword 0; `+0x3c` és `+0x3e` word; `+0x48` dword `-1`.
- Az info címe `esp0+0x28` (0x0080156b `lea esi,[esp+0x2c]`, a push 1 után).
- A rekord címe `esp0+0x50` (0x0080157c `lea ecx,[esp+0x50]`). Az info vége és a rekord eleje egybeesik.
- A rekordot a `0x007fa5b0` a hívás után építi (a bemeneti fájl 228. sora). A hívás pillanatában a `esp0+0x50` még nem rekord.

Feltételes:
- A rekord `esp0+0x50` csak akkor, ha a hívott `ret 0xc`-cel tér vissza. A hívó nem takarít (0x0080157a `call edx`, utána közvetlenül 0x0080157c). A hívott `ret` értékét nem néztem. Ha az más, a rekord címe is más.

NINCS MEG:
- Túlír-e a hívott az info végén. Ehhez a hívott vt+0 célja kell (§3). Ghidra-kör kell: `0x008014d0 - a vt+0 hívott függvénye (U2 után), ír-e az esp0+0x50 fölé` (U4).

**3. 0x005e8a70 és 0x005e9750: az obj2 forrása (LEZÁRVA a forrás és az ág; NINCS MEG az osztály és a vt+0 cél).**

Igazolt (asm):
- 0x005e970d `mov eax,[ebx+0x2bc]`: EAX = M.
- 0x005e9717 `xor esi,esi`, 0x005e9719 `cmp eax,esi`. A 0x005e971b-0x005e9741 közti utasítások (lea, mov) nem írnak flaget.
- 0x005e9745 `je 0x5e9750`.
- M = 0 ág: 0x005e9750 `mov [esp+0x74],esi`, tehát block+0x10 = 0.
- M ≠ 0 ág: 0x005e9747 `add eax,0x4c`, 0x005e974a `mov [esp+0x74],eax`, tehát block+0x10 = M+0x4c.
- A block címe `esp+0x64`: 0x005e9782 `lea ecx,[esp+0x64]`, 0x005e9786 `push ecx`, 0x005e9787 `call 0x8037e0`.
- A T konstruktora (0x007fa7f0) a block+0x10-et T+0x2e4-be írja: 0x007fa81b `mov ecx,[edi+0x10]`, 0x007fa81e `mov [ebp+0x2e4],ecx`. Az EDI a block (0x007fa7fb `mov edi,eax`).
- Ezért obj2 = T+0x2e4 = M+0x4c, vagy 0, ha M = 0.
- Ha obj2 = 0, a vt+0 hívás kimarad: 0x00801523 `cmp [edi+0x2e4],ebp`, 0x0080155d `je 0x80157c`. Az EBP = 0 a 0x008014de `xor ebp,ebp` óta. Az EBP írását a 0x00801500-0x00801523 szakaszban asm-ben átnéztem, a 0x008014e0-0x008014ff szakaszt nem.

NINCS MEG:
- M osztálya, és az M+0x4c objektum vt+0 célja. Ghidra-kör kell: `0x005e8a70 - M = [CThumbUI+0x2bc] írója és osztálya (a CThumbUI konstruktora); az [M+0x4c] objektum vt+0 célja` (U2).

**4. 0x007fcca0: a kulcs forrása (LEZÁRVA a forrás és a feltétel; NINCS MEG a jelentés).**

Igazolt:
- 0x007fcc77 `mov edx,[ebx+esi*4]`: a kulcs a kulcs-tömbből jön (EBX a tömb).
- 0x007fcca0 `mov [esp+0x84],edx`: a kulcs a rekord +0 mezőjébe kerül. A rekord az 0x007fcc6e `lea ecx,[esp+0x70]` címe (a `sub esp,0x10` és a `push eax` után az esp+0x84 ugyanez a cím).
- A kulcs-tömböt a 0x007fc7c0 első ciklusa építi: `FUN_004ae4e0(i, &out)` (a bemeneti fájl 1688. sora).
- 0x004ae4e0 (asm 0x004ae4e0-0x004ae541): EAX = a lista, az első stack-argumentum az index, a második a kimeneti rekord. Az elem 56 bájtos. A tömb `[lista+0x158]`, a darabszám `[lista+0x15c] >> 1` (0x004ae52b-0x004ae531).
- A másoló 0x004ae600-ban (asm): a kimenet +0x14 mezője az elem +0x14 mezőjéből jön (0x004ae694 `mov edx,[esi+0x14]`, 0x004ae697 `mov [ebx+0x14],edx`). A +0x18 bájt (0x004ae69a) és a +0x30 típus (0x004ae6ca, 0x004ae6cf) is átmásolódik.
- A gyűjtés feltétele (a bemeneti fájl 1689. sora): elem +0x30 = 1 és elem +0x18 bájt = 0. Ezt az asm-ben nem néztem át.
- A spec szerint (ui-audit-mainwindow.md, a nextalbum-keresés, 1473. sor) az 1-es típus album-találat, az 5/6/7 fejléc.

Tehát a kulcs az 1-es típusú, +0x18 = 0 jelzőjű sorok +0x14 mezője a sorlistában.

NINCS MEG:
- A +0x14 jelentése: azonosító, dátum vagy index. A +0x14 írói nincsenek megnézve. **JAVÍTVA (38.2.41 §1):** az író a `0x004a0773`, az érték a hívó második argumentuma. A 0x004a0720 (feltehetően a sorrekord konstruktora) első része (0x004a0720-0x004a076d) a +0x0-+0x9 bájtokat, a +0xc sztringet és a +0x10 mezőt írja. A +0x14 írása ebben a részben nincs. Ghidra-kör kell: `0x004a0720 - a törzs második fele (0x004a076d után) és a 0x004b2ab4 hívóhely - a sorrekord +0x14 írója` (U7).

**5. A kártya-lista újraépítése (NINCS MEG: a kulcs típusa és a kattintási ág nélkül nem írható le).**

Igazolt (index xrefs, függvényszint):
- A 0x008014d0 hívói: 0x008037e0 (az Időrend indulása, 0x008039d1) és 0x008018a0 (a fókuszcsere, 0x00801c95).
- A 0x008018a0 hívói: 0x007fde80 (az egér-kezelő, a 38.2.36 §1 szerint), 0x00801cb0 (**JAVÍTVA, 38.2.41 §3:** a léptetési pumpa hívója) és 0x008037e0.
- A kártyák kulcsa a `[T+0x3ec]` listából jön (asm 0x00801570 `mov esi,[edi+0x3ec]`, 0x00801576 `mov eax,[esi+eax*4]`). Ennek írója a 0x008018a0 (a 38.2.34 szerint; ebben a körben nem néztem).

NINCS MEG:
- Melyik kattintás után fut. A 0x007fde80 ága, amely a 0x008018a0-t hívja, nincs ellenőrizve. A 38.2.36 §1 állítása (bal gomb a négy téglalapon kívül) feltételes marad.
- Melyik képhalmazra. A kulcs típusa nem dőlt el (§4), ezért a felhasználói mondat nem írható le.

Ghidra-kör kell: `0x007fde80 - a 0x008018a0 hívás feltétele (melyik kattintás ág), és a 0x00801cb0 azonosítása` (U9).

**6. A 38.2.39 nyitott listája frissítve (38.2.40).**

| tétel | állapot | mit mutat | Ghidra-cím |
|---|---|---|---|
| U1, 0x00a6aa00 teljes törzs | NINCS MEG, ebben a körben nem vizsgáltam | - | 0x00a6aa00 |
| U2, obj2 osztálya és vt+0 célja | RÉSZBEN LEZÁRVA: forrás és ág (§3); osztály és cél NINCS MEG | obj2 = M+0x4c, vagy 0 | 0x005e8a70 (M olvasója; JAVÍTVA 38.2.43 §4: nem ír M-be), M+0x4c vt+0 |
| U3, L+0x48 vtábla és 11. slot | NINCS MEG (§1) | - | 0x004b0190 P osztálya, L+0x48 konstruktora |
| U4, 0x0080157a túlírás | NINCS MEG; geometria LEZÁRVA (§2) | a rekord címe a `ret 0xc` feltevéstől függ | 0x008014d0 vt+0 hívott függvénye |
| U5, T+0x2ec olvasói | NINCS MEG, nem vizsgáltam | - | 0x008014d0 T+0x2ec olvasói |
| U6, 0x009aaae0 hívóhelyei | NINCS MEG, nem vizsgáltam | - | 0x009aaae0 |
| U7, sorrekord +0x14 írója | NINCS MEG (§4) | 0x004a0720 második fele, 0x004b2ab4 | 0x004a0720 (0x004a076d után) |
| U8, P' = [T+0x3a4] és írója | NINCS MEG | a 0x007fc7c0 P'-t listaként használja (a bemeneti fájl 1680. sora) | 0x008037e0, 0x007fa7f0 (T+0x3a4 írói, nincs nézve) |
| U9, 0x008018a0 kattintási ága | NINCS MEG (§5) | 0x007fde80 és 0x00801cb0 | 0x007fde80, 0x00801cb0 |

**Helyesbítések (JAVÍTVA ebben a körben).**
- 38.2.39 §2a, az obj2 eredete: az ág kérdése LEZÁRVA (§3). A `je` akkor ugrik a 0x005e9750-re, ha M = 0. Ekkor 0 íródik.
- 38.2.39 §1, a kép forrása: a `lea eax,[esp+0x44]` (0x007fcc9c) a 0x00a6aa00 this-je, és nincs igazolva, hogy a 0x004ae430 kimenete. NINCS MEG.

**Amit KIZÁRTAM.**
- „A vt+0 hívás mindig lefut”: CÁFOLVA. Ha M = 0, a hívás kimarad (§3).
- „A 0x005e9750 az M ≠ 0 ág”: CÁFOLVA. A 0x005e9750 az M = 0 ág.

**Nyitott kérdések mérlege (38.2.40).** 9 tétel NINCS MEG (U1-U9, §6). Mindegyik mellett Ghidra-cím áll. Becsült érték nincs.

**Frissítve (38.2.41 §4):** 7 tétel NINCS MEG (U1-U6, U8), U7 LEZÁRVA, U9 LEZÁRVA. Az új tételek (U10-U15) és a Ghidra-címeik a 38.2.41 §4 táblázatában vannak.

#### 38.2.41 Az Időrend bináris feltárása, 24. kör: a sorrekord +0x14 írója, a kattintási út, a 0x00801cb0 és a lista kulcsa (#5401, 2026-10-21)

**Válasz röviden.**
1. A sorrekord `+0x14` mezőjét a `0x004a0773` írja. Az értéke a hívó második argumentuma. Az 1-es típusú sorban ez az `i` sorszám, a `[L+0x138]` tábla egy sorának indexe. Nem kép-azonosító és nem dátum. Az, hogy a sor album vagy mappa, **NINCS MEG**.
2. A `0x008018a0` (a fókusz váltása) bal gombos kattintásra fut Időrend módban, ha a pont egy kártya téglalapjába esik, és nem a négy overlay egyikébe. A négy overlay két gomb (`startbutton`, `exit`) és két nyíl (`left`, `right`), ezekre nem fut le.
3. A `0x00801cb0` nem kattintási függvény. A léptetési pumpa hívja minden körben, és ő is válthat fókuszt.
4. Hogy a kattintás után melyik képhalmaz jelenik meg: **NINCS MEG**. Lásd a „A felhasználó szemével” szakaszt a végén.

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-24.txt` volt, három címmel: `0x004a0720`, `0x007fde80` és `0x00801cb0`. A hívóhelyeket az index `xrefs` táblája és a `pe_dis.cdis` adta. A dekompiláció csak kiindulópont volt, a döntő lépéseket asm-ben néztem meg. Kódot nem módosítottam, ezért CI-őr nem futott. Ideiglenes fájl nem keletkezett, a `.bt/` nem jött létre.

**Bizonyítottsági fok.** Az asm-ből igazolt állítások erősek. Ami korábbi körből származik, azt `(korábban igazolt: 38.2.x)` jelöli. Ami csak dekompilációból látszik, azt külön írom.

**Fogalmak.**
- **L** = a lista objektum. A `0x004b8470` belépésekor az EAX (`0x004b8477 mov edi,eax`). Ez ugyanaz a lista, amelynek sorai a `[L+0x158]` tömbben vannak (korábban igazolt: 38.2.40 §4).
- **i** = egy sor sorszáma az `[L+0x138]` táblában. A sorok 36 bájtosak, a típus a sor `+0xc` mezőjében van. A darabszám `[L+0x13c] >> 1` (`0x004b29e0-0x004b29e6`).
- **rec** = egy kártya-rekord, 0xf8 bájtos. A `[this+0x2f8]` alobjektum `+0xb0` tömbjében van (`0x007fd800`).

**1. A sorrekord +0x14 mezője (Q1).**

Igazolt:
- **Az író:** `0x004a0773 mov [esi+0x14],edx`. Az EDX értéke a `0x004a0761 mov edx,[esp+0x14]` után a hívó második argumentuma (param_2). A `0x004a07d5 ret 0x10` miatt a hívott takarít, a hívó nem.
- **Az argumentumok sorrendje:** a hívó az utolsónak tolt értéket adja az első argumentumnak. A `0x004a078d mov [esi+0x30],edx` a típust írja (az első argumentumot). A második argumentum az utolsó előtt tolt érték.
- **A 12 hívóhely:**

| hívóhely | a hívóhely függvénye | típus (+0x30) | +0x14 (a 2. argumentum) |
|---|---|---|---|
| `0x004b1acb` | `0x004b1a90` | 8 | `-1` (konstans) |
| `0x004b1eac` | `0x004b1c80` | 5 | `[ebp]` (`0x004b1e99`) |
| `0x004b22ce` | `0x004b1c80` | 2 | `0` |
| `0x004b2ab4` | `0x004b29d0` | 1 | EDI = `i` (lásd lent) |
| `0x004b2f9a` | `0x004b2e10` | 3 | EBP (NINCS MEG) |
| `0x004b3281` | `0x004b2e10` | EBP (NINCS MEG) | `[esp+0x6c]` (NINCS MEG) |
| `0x004b35a2` | `0x004b34a0` | 2 | `0` |
| `0x004b3886` | `0x004b3770` | 2 | EBX (NINCS MEG) |
| `0x004b3b50` | `0x004b3770` | 2 | EBX (NINCS MEG) |
| `0x004b3f4b` | `0x004b3770` | 2 | `1` |
| `0x004b7f17` | `0x004b7f00` | 9 | `-1` |
| `0x004b81fd` | `0x004b80d0` | 2 | EBP (NINCS MEG) |

- **Az 1-es típusú sor útja** (ez a lista kulcsa):
  - A `0x004b8470` ciklusa `esi` 0-tól fut a `([L+0x14c] >> 1) - 1` értékig (`0x004b858c`, `0x004b85cd-0x004b85da`). Ha `[L+0x9d] != 0`, a `0x004461a0(i)` szűrőnek igaznak kell lennie (`0x004b85a0-0x004b85bf`).
  - A hívott sorszám `i = [[L+0x148] + esi*4]` (`0x004b85a6-0x004b85ac`). A hívás előtt `EAX = i` (`0x004b85c6`), a ctx-mutató a verem tetején van (`0x004b85c1-0x004b85c5`).
  - A `0x004b29d0` belépésekor `EDI = EAX = i` (`0x004b29db`). A ctx+0x48 mező az L (`0x004b851b mov [esp+0x60],edi` miatt).
  - Ha `i <= [L+0x13c] >> 1` (`0x004b29ea jbe`), a `[L+0x138] + 36*i + 0xc` mezőt nézi. Ha ez 2, folytat. Különben `1000000` a visszatérés (`0x004b29f0-0x004b29fe`, `0x004b2a1a`).
  - A folytatásban `ESI = 0` (`0x004b2a0a xor esi,esi`). A `0x004b2ab4` hívásban: param_1 = 1, param_2 = EDI = `i`, param_3 = ESI = 0 (+0x18).
- **Eredmény:** az 1-es típusú sorban `+0x14 = i` és `+0x18 = 0`. Feltétel: a közbülső hívások nem írják az ESI-t. Ezt a szokásos konvencióból feltételezem. A `0x0044ddd0`, `0x004a8c60`, `0x00448a10`, `0x004b3770` és a vt+0x18 hívás törzsét nem néztem végig.
- **A kulcstömb:** a `0x004ae4e0` a sor `+0x14`-ét a kimenet `+0x14`-ébe másolja (korábban igazolt: 38.2.40 §4). A `0x007fc7c0` gyűjti, a hívója a `0x008037e0`, az Időrend indulása (xref). A kimeneti rekord az `esp+0x30` címen van, ezt a `[esp+0x60]` (+0x30) és a `[esp+0x48]` (+0x18) ellenőrzés megerősíti. A gyűjtés feltétele: +0x30 = 1 (`0x007fc8c8`) és +0x18 = 0 (`0x007fc8d3`). Ha igaz, a `[esp+0x44]` (a kimenet +0x14) bekerül a kulcstömbbe (`0x007fc955-0x007fc966`).
- **Mit jelent az `i`:** nem kép-azonosító és nem dátum. A `0x004b29d0` 36 bájtos sorként címzi (`0x004b29f6-0x004b29f9`). Hogy a tábla sora album vagy mappa, **NINCS MEG**.

NINCS MEG:
- Az `[L+0x148]` írói és a `0x004b8470` hívója. Ezek adják az `i` értékeket. Ghidra-kör kell: `0x004b8ee0 - a 0x004b8470 hívója és az [L+0x148] írói (U10)`.
- Az `[L+0x138]` tábla tulajdonosa és a `+0xc == 2` jelentése. Azt is el kell dönteni, hogy az `i == darab` eset valóban olvas-e (a `jbe` miatt). Ghidra-kör kell: `0x004b29d0 - az L osztálya, a sor típusmezőjének jelentése, a darabszám-határ (U11)`.
- Az EBP és az EBX forrása a többi hívóhelyen. Ghidra-kör kell: `0x004b2e10, 0x004b3770, 0x004b80d0 - a hívott függvények EBP és EBX forrása (U12)`.

**2. A kattintási út (Q2).**

Igazolt a `0x007fde80` (a QDrawable egérkezelője) bal gomb lenyomás (0x201) ágában:
1. `[this+0x3b8] == 0` (nincs Időrend mód): `0x00801130`, és kilépés (`0x007fe1e6-0x007fe1f6`, korábban igazolt: 38.2.22 §4). A `0x008018a0` tehát csak Időrend módban fut.
2. `0x007fda80`, a négy overlay. Találatnál `1000000` és kilépés (`0x007fe1fd-0x007fe207`). A négy overlay: `startbutton` (X = 0x738), `exit` (0x580), `right` (0x558, `0x007fd150`), `left` (0x530, `0x007fd120`). Korábban igazolt: 38.2.22 §4.
3. Húzás-jelzők: `[this+0x429]` vagy `[this+0x428]` lesz 1 (`0x007fe2ff-0x007fe31b`). Mindkét ág a `0x007fe322`-re fut, tehát a csúszka-húzás is idáig jut.
4. `0x007fd800(this+0x2f8, this+0x420, &out)` (`0x007fe32f`). A kurzor alatti rekordot keresi: a `[this+0x2f8]` alobjektum indexlistáján megy végig, és a rekord téglalapját nézi (`+0xdc`, `+0xe0`, `+0xe4`, `+0xe8`). Nincs találat: `-1`. Találatnál a kimenetre a rekord `+0` mezője kerül, a visszatérés a `0x007fd770(i)` értéke, ami 0 (korábban igazolt: 38.2.23 §6, 38.2.38 §1).
5. `test eax,eax` és `jne 0x007fe35d` (`0x007fe334-0x007fe336`). Ha 0: `EAX = [esp+0x18]` (a rekord `+0` mezője), `ECX = this`, `call 0x008018a0` (`0x007fe338-0x007fe33e`).
- A `0x007fd770(i)` a `0x007fd0c0`-t hívja, amelyet a nyíl-billentyűk is használnak (korábban igazolt: 38.2.23 §6).
- A `0x007fe346` utáni `0x203` ellenőrzés az üzenet mezőjét olvassa újra. Normál úton 0x201 van benne, ezért nem fut le (korábban igazolt: 38.2.21, lezárva (e) pont).

Ebből a kérdésre adott válasz:
- **Kártya:** igen. Bal gomb, Időrend mód, nem overlay, és a pont egy rekord téglalapjában van.
- **Háttér** (nincs rekord): nem, mert a `0x007fd800` `-1`-et ad.
- **Léptető nyilak** (`left`, `right`): nem. Az overlay-ág `1000000`-rel előbb kilép.
- **`startbutton` és `exit`:** nem, ezek is overlay-ok.
- **Csúszka-húzás:** ugyanazon az úton fut. A `0x008018a0` csak akkor hívódik, ha a pont egy rekord téglalapjában van. Hogy a csúszka és a kártyasor téglalapjai átfedhetnek-e, **NINCS MEG** (asm-vizsgálat kell).

Dekompiláció alapján (asm nincs ellenőrizve): dupla gomb (0x203) és jobb gomb (0x204) esetén nem a `0x008018a0` fut. Időrend módban a `0x007fda80` után `0x007fb820` (kilépés) fut, majd a `[this+0x2e8]` objektum vt+0x18 hívása `(-1, azonosító)` argumentumokkal. Az azonosító `[[this+0x3ec] + [this+0x3f8]*4]`. A `startbutton` ugyanezt a kilépés-és-hívás utat járja (korábban igazolt: 38.2.22 §4).

**3. A 0x00801cb0 (Q3).**

Igazolt:
- Egyetlen hívóhelye a `0x00802087` címen van, a `0x00802060` függvényben (xref és asm).
- A `0x00802060` akkor hívja, ha `[this+0x3bb] == 0` és `[this+0x3b8] != 0` (`0x00802066`, `0x00802078`, `0x0080207e-0x00802085`, `0x00802087`).
- A törzs (dekompiláció): `0x007fc010(this+0x2f8, this+0x2c8)`. Ha `[this+0x429] == 0` és `0x007fd8c0(this+0x510) != 0`, akkor `0x008018a0` fut, EAX = `[this+0x510]` (korábban igazolt: 38.2.21 §2, `0x00801ce1-0x00801ce5`).
- A `0x007fde80` hívottjai között nincs `0x00801cb0`. Tehát nem a kattintási úton van.

Szerepe: a léptetési pumpa minden körében (Időrend módban) a 0,666 konstanshoz legközelebbi kártyát keresi (`0x007fd8c0`, korábban igazolt: 38.2.22 §3). Ha ez változott, a `0x008018a0` fókuszt vált. Tehát két út vezet a fókusz-váltáshoz: a kattintás (`0x007fde80`) és a pumpa (`0x00801cb0`).

NINCS MEG: a `0x007fc010` törzse (az elrendezés frissítése). Ghidra-kör kell: `0x007fc010 - mit frissít a [this+0x2f8] alobjektumban (U13)`. **Új állapot (38.2.42 §3):** RÉSZBEN LEZÁRVA; a maradék: `0x007fbab0`, `0x005568e0`, `0x007fa650`, `0x00604480`.

**4. A 38.2.40 nyitott listája (Q5).**

| tétel | állapot (38.2.41) | mit mutat | Ghidra-cím |
|---|---|---|---|
| U1, 0x00a6aa00 teljes törzs | NINCS MEG (változatlan) | - | `0x00a6aa00` |
| U2, obj2 osztálya és vt+0 célja | RÉSZBEN LEZÁRVA (változatlan) | obj2 = M+0x4c, vagy 0 | `0x005e8a70` (M olvasója; JAVÍTVA 38.2.43 §4: nem ír M-be), M+0x4c vt+0 |
| U3, L+0x48 vtábla és 11. slot | NINCS MEG (változatlan) | - | `0x004b0190` P osztálya, L+0x48 konstruktora |
| U4, 0x0080157a túlírás | NINCS MEG (változatlan) | a rekord címe a `ret 0xc` feltevéstől függ | `0x008014d0` vt+0 hívott függvénye |
| U5, T+0x2ec olvasói | NINCS MEG (változatlan) | - | `0x008014d0` T+0x2ec olvasói |
| U6, 0x009aaae0 hívóhelyei | NINCS MEG (változatlan) | - | `0x009aaae0` |
| U7, sorrekord +0x14 írója | **LEZÁRVA (§1)** | írója `0x004a0773`; értéke a hívó 2. argumentuma; az 1-es típusnál `i` | - |
| U8, P' = [T+0x3a4] és írója | NINCS MEG (változatlan; új: a `0x007fc7c0` hívója a `0x008037e0`) | - | `0x008037e0`, `0x007fa7f0` (T+0x3a4 írói) |
| U9, 0x008018a0 kattintási ága | **LEZÁRVA (§2, §3)** | kártya-találat, Időrend, bal gomb, nem overlay; a `0x00801cb0` a pumpa-hívó | - |
| U10 (új) | NINCS MEG | az `i` értékek forrása: az `[L+0x148]` írói | `0x004b8ee0` (hívó), `0x004b8470` |
| U11 (új) | NINCS MEG | az `[L+0x138]` tábla tulajdonosa, a `+0xc == 2` jelentése, a `jbe` határ | `0x004b29d0`, `0x004b8ee0` (az L osztálya) |
| U12 (új) | NINCS MEG | a hívott függvények EBP/EBX forrása a +0x14 értéknél; a `0x004b3281` típusa lehet 1 | `0x004b2e10`, `0x004b3770`, `0x004b80d0` |
| U13 (új) | **JAVÍTVA (38.2.42 §3):** a `0x007fc010` NEM írja a rekord `+0` mezőjét (a régi `0x007fc010` hivatkozás téves). A `0x008018a0` `local_64` forrása a `0x004b0190` kimenete (38.2.42 §5). A rekord `+0` írója: `0x007fcca0` (38.2.40 §4), a kattintási rekordé NINCS MEG. | `0x007fcca0`, `0x004b0190`, `0x007fc010` (nem ír `+0`-t) |
| U14 (új) | NINCS MEG (a 38.2.25 óta nyitott) | a `0x008014d0` törzse: mit rajzol a `[OneUp+0x3ec]` listából | `0x008014d0` |
| U15 (új) | NINCS MEG | a `[this+0x2e8]` objektum osztálya és vt+0x18 célja (startbutton, dupla kattintás) | `0x007fa7f0` (3. paraméter), az objektum vt+0x18 célja |

**Helyesbítések (38.2.41).**
- A 38.2.22 §3 összefoglaló sorában a `0x007fd770` visszatérése még NINCS MEG volt. A 38.2.23 §6 és a 38.2.38 §1 már lezárta (0). A sort javítottam.
- A 38.2.40 §4 szerint a +0x14 írói nincsenek megnézve. Most megnéztem (§1).
- A 38.2.40 §5 szerint a 0x00801cb0 nincs azonosítva. Most azonosítottam (§3).

**Amit KIZÁRTAM.**
- „A `+0x14` kép-azonosító vagy dátum”: CÁFOLVA. A `0x004b29d0` 36 bájtos táblasor címzésére használja.
- „A `0x00801cb0` a kattintási úton van”: CÁFOLVA. A `0x007fde80` hívottjai között nincs.
- „A `0x008018a0` csak egérkattintásra fut”: CÁFOLVA. A pumpa is hívja.
- „Minden 1-es típusú sor `+0x18` mezője 0”: nem általánosítható. A `0x004b2ab4` ágban igaz, de a `0x004b3281` típusa EBP, ezért ott más is lehet (U12).

**Nyitott kérdések mérlege (38.2.41).** 6 új tétel (U10-U15). A 38.2.40 listájából 7 tétel NINCS MEG (U1-U6, U8), U7 és U9 LEZÁRVA. Mindegyik mellett Ghidra-cím áll. Becsült érték nincs.

**Frissítve (38.2.42 §6):** U7 és U9 LEZÁRVA (változatlan). RÉSZBEN LEZÁRVA: U2, U10, U11, U13 (és JAVÍTVA, lásd a táblázat U13 sorát), U14. NINCS MEG: U1, U3 (bővült), U4, U5, U6, U8, U12, U15, és az új U16-U21. A részletek és a Ghidra-címek a 38.2.42 §6 táblázatában vannak.

#### A felhasználó szemével

Nem dőlt el, melyik képhalmaz jelenik meg. Ami igazolt:
- Kártyára bal gombbal kattintva a sor a kattintott kártya felé mozdul (`0x007fd770` → `0x007fd0c0`). A program a kártya `+0` mezőjét teszi meg kijelölt kulcsnak (`0x008018a0`), és újrarajzolja a nézetet (`0x008014d0`).
- A kulcsok a lista sorainak sorszámai (`i`). Az Időrend indulásakor ezekből gyűjtött kulcstömb épül (`0x007fc7c0`).
- Dupla vagy jobb gombra (csak dekompiláció szerint) az Időrend kilép (`0x007fb820`), és a visszahívás a legutoljára mutatott kulcsot kapja.

Hiányzó címek: `0x008014d0` (mit rajzol a kulcs alapján) és `0x007fa7f0` (a rekord `+0` mezőjének írója, vagyis hogy a kártya kulcsa melyik sorhoz tartozik).

**Frissítve (38.2.42 §4 és §5):** a `0x008014d0` nem rajzol közvetlenül; kulcsonként kártya-rekordot épít a `[this+0x2ec]` tömbbe. A kattintás után a kulcslistát a `0x004b0190` adja, nem a `0x007fa7f0`. A melyik-képhalmaz kérdés továbbra is NINCS MEG (lásd a 38.2.42 szakasz végét).

#### 38.2.42 Az Időrend bináris feltárása, 25. kör: a lista rendezése, a `jbe` határ, a kártya-építő és a kattintási kulcs (#5401, 2026-10-21)

**Válasz röviden.**
1. **Q1, a lista.** A `0x004b8ee0` tölti a `[L+0x148]` listát. A listába az `i` sorszám kerül, és csak azoké a soroké, amelyeknek a `+0xc` mezője nem nulla. Ezután a `0x004baaa0` rendezi a listát a `0x004a7890` összehasonlítóval. A rendezés kulcsa NINCS MEG. A `+0xc` mező forrása, vagyis a sortábla írója, szintén NINCS MEG.
2. **Q2, az L és a `jbe`.** L a `0x004b8ee0` és a `0x004b8470` tagfüggvényeinek this-je. Neve és vtáblája NINCS MEG. A `+0xc == 2` kapu megvan, a 2-es érték jelentése NINCS MEG. A `jbe` miatt az `i == darab` eset tényleg olvas: a tábla logikai végén túli elemet nézi. Hogy ez előfordul-e, NINCS MEG.
3. **Q3, a `0x007fc010` és a `0x008014d0`.** A `0x007fc010` a `[this+0x2f8]` alobjektum sebességét és görgetési állását írja, a látható elemek listáját, és minden elem alfa- és mátrixmezőit. A `0x008014d0` nem rajzol: a kulcslistából kulcsonként egy kártya-rekordot épít a `[this+0x2ec]` tömbbe. Hogy ki rajzolja ezt a tömböt, NINCS MEG.
4. **Q4, a felhasználó szemével.** Nem dől el: melyik képhalmaz jelenik meg, NINCS MEG. Lásd a szakasz végét.
5. **Q5.** A 38.2.41 nyitott listája frissítve (§6). A 38.2.41 U13 sorát javítottam, mert a `0x007fc010` nem írja a rekord `+0` mezőjét.

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-25.txt` volt, négy címmel: `0x004b8ee0`, `0x004b29d0`, `0x007fc010`, `0x008014d0`. Az asm-ellenőrzés `pe_dis.cdis`-szel történt. Kiterjedt a `0x004baaa0` és a `0x009a8bc0` teljes törzsére, a `0x008018a0` belépésére és a K listát író utasításaira (index-keresés alapján), valamint a `0x004a7890` és a `0x004b8470` elejére. A hívóhelyeket az index `xrefs` táblája adta, ez csak a direkt hívásokat látja, a vtábla-hívásokat nem. A konstansokat a bináris nyers bájtjaiból olvastam ki. Kódot nem módosítottam, ezért CI-őr nem futott.

**Bizonyítottsági fok.** Az asm-ből igazolt állítások erősek. Ami csak a dekompilációból látszik, azt külön jelölöm.

**Fogalmak (új).**
- **L**: a `0x004b8ee0` és a `0x004b8470` belépési EAX-a (`0x004b8eed`, `0x004b8477`). Lista: `[L+0x148]` (mutató), darab: `[L+0x14c] >> 1`, a bit 0 külön jelző (`[L+0x14c] & 1`). Sortábla: `[L+0x138]`, 36 bájtos sorok, darab: `[L+0x13c] >> 1`.
- **P**: `[OneUp+0x2f4]`. A `0x004b0190` hívásakor EAX = P (`0x008018ce`, a hívás `0x008018e0`). `L = [P+0xc4]` (38.2.40 §0).
- **K**: `[OneUp+0x3ec]`, a kulcslista. Darab: `[OneUp+0x3f0] >> 1`.
- **C**: `[OneUp+0x2ec]`, a kártya-rekordok tömbje, rekordonként 0xf8 bájt. Darab: `[OneUp+0x2f0] >> 1`.
- **S**: `[OneUp+0x2f8]`, az alobjektum. A rekordtömbje `[S+0xb0]`, darab: `[S+0xb4] >> 1`.

**1. Az i-lista (Q1).**

Igazolt (asm):
- Az írás helye: `0x004b90b4 mov [eax+edx*4], edi`. Az `edi` a ciklusváltozó, vagyis a sor sorszáma (`i`). A ciklus `0`-tól `darab - 1`-ig megy (`0x004b90d0`, `0x004b90da`).
- A sort csak akkor írja a listába, ha a `+0xc` mezője nem nulla (`0x004b9028`, `0x004b902d`), és a bit 0 nulla (`0x004b9036`, `0x004b9039`). Ha a bit 1, a lista üres marad.
- A darab eggyel nő (`0x004b90c7`). A `0x004b86d0(i)` hívás minden nem nulla sorra megtörténik, a bit 0 értékétől függetlenül (`0x004b90cb`).
- A lista minden híváskor újraépül. A régi puffer felszabadul, a mutató nullázódik (`0x004b9003`, `0x004b9013`), majd új puffer készül (`0x004b908c`).
- Ha a darab nulla, a függvény a `0x004b8f58` ágon visszatér. Ekkor nem építi újra a listát, és nem hívja a `0x004b8470`-et (`0x004b8f35`-`0x004b8f8b`).
- A listaépítés után, feltétel nélkül, a `0x004baaa0` fut (`0x004b916b`). Előtte, ha `[L+0xdc] == 2`, a `0x004b8d00(L)` hívódik (`0x004b90e4`-`0x004b90ee`). Utána a `0x004b8470` következik (`0x004b9192`).
- A `0x004baaa0` a listán dolgozik. A forrás `[[esi+8]]`, ahol `[esi+8]` a `&L+0x148` (`0x004baaf9`-`0x004bab02`). A darab `[L+0x14c] >> 1` (`0x004baabf`-`0x004baac7`). Egy memóriafoglaló hívással (`0x0097c5d0`, `darab * 4` bájt) segédpuffert kér (`0x004baada`), és egy alulról felfelé haladó összefésüléses rendezést futtat. Az összehasonlító a `0x004a7890(a, b, L)` (`0x004bab9f`). A segédpuffert a végén felszabadítja (`0x0097caf0`, `0x004bac72`). A túlélő puffer a lista lehet: a hívó nem tárol el visszatérési értéket, a `[L+0x148]` mutatót pedig ebben a kötegben nem láttam felülírni. Ez erős, de a végső pufferről a paritás-ág végigkövetése nélkül állítom.
- A rendezés kulcsa a `0x004a7890` törzsében van, és az a globális `DAT_00d67678` értékétől függ. A hívó (`0x004b9150`) állítja be az `esp+0x28` objektumra bizonyos feltétel mellett, és `0x004b9176`-ban nullázza. Nulla globálisnál a `0x004a7890` másik ágra megy (`0x004a78a7`). A kulcs törzse NINCS MEG.

Következtetés:
- A listába azoknak a soroknak az `i` sorszáma kerül, amelyeknek a `+0xc` mezője nem nulla, feltéve hogy a bit 0 nulla.
- A sorrend a rendezés kulcsától függ. Ezt nem igazoltam, ezért az index-sorrend nem állítható.
- A 38.2.41 §1 kérdésére (ki adja az `i` értékeket): a `0x004b8ee0` ciklusának változója.
- A `+0xc` mező a `[L+0x138]` sortáblából jön. A tábla írói NINCS MEG.
- A bit 0 írója NINCS MEG. A `0x004b8ee0` csak megőrzi (`0x004b900b`).

**2. Az L osztálya, a `+0xc == 2` kapu és a `jbe` (Q2).**

- **L osztálya**: NINCS MEG (a név és a vtábla-cím). Igazolt, hogy L a `0x004b8ee0` és a `0x004b8470` tagfüggvényeinek this-je. A `0x004b8ee0` L vtábla-slotjait hívja: `vt+0x18` a zároláshoz (`0x004b8f18`), `vt+0x1c` a feloldáshoz (`0x004b8f7b`, `0x004b91e1`). Ha `L+0xc` nulla, a vtábla-zár megy, különben a kritikus szakasz `L+0x28` (`0x004b8f04`).
- **A `0x004b29d0` kapuja (`+0xc == 2`)**: a belépési EAX az `i` (`0x004b29db`). A `ctx` a verem argumentuma, `L = [ctx+0x48]` (`0x004b29d5`-`0x004b29e0`).
  - Ha `i <= darab` (`0x004b29e8`, `0x004b29ea jbe`), akkor `bl` azt adja, hogy a `[L+0x138] + 36*i + 0xc` mező értéke 2-e (`0x004b29f0`-`0x004b29fe`). Különben `bl = 0`.
  - A `0x0044ddd0(ctx+0x4c, i, &out)` hívás (`0x004b2a11`) a kapu ELŐTT fut, a sor típusától függetlenül.
  - `bl = 0` esetén a visszatérés `1000000` (`0x004b2a1a`).
  - A kapu tényét az asm igazolja. A 2-es típus jelentése NINCS MEG.
- **A `jbe` határ (`i == darab`)**: igen, olvas. A `jbe` egyenlőségnél is ugrik, ezért `i == darab` esetén a `[L+0x138] + 36*darab + 0xc` címről olvas (`0x004b29f9`). Ez a sor a tábla logikai végén túl van. Hogy a puffer kapacitása elég-e, és mi a tartalma, NINCS MEG: a tábla növelő kódja nincs a kötegben. Ha a `[L+0x138]` mutató NULL és `darab = 0`, a cím `0xc` lenne. Ennek előfordulása NINCS MEG.
- **Előfordul-e `i == darab`**: csak akkor, ha a darab (`[L+0x13c]`) a listaépítés után, a `0x004b8470` hívása előtt csökken. Az út közben ezek futnak: `0x004b86d0` (a listaépítés alatt), `0x004b8d00`, `0x004a6dc0`, `0x004baaa0`, `0x004a7010`. Nem zárható ki, hogy valamelyik írja az `[L+0x13c]` mezőt. Ez NINCS MEG.

**3. A `0x007fc010` (Q3, első fele).**

Hívó: `0x00801cb0` (`0x00801cc1`). A hívás `0x007fc010(S, this+0x2c8)`. A `this+0x2c8` a téglalap, a második argumentum. Asm-ben igazolt írások és számítások:
- **a)** `S+0x18` (double, sebesség): `× 0.95` (`0x007fc085` `fld`, `0x007fc08a` `fmul` a `0x00cf40b0` double-lel, amely 0.95, `0x007fc09e` `fstp`).
- **b)** `S+0x20` (double, görgetési állás): `S+0x20 += S+0x18`, majd hozzáadja a `0x009e5f90(0x009a5210())` lánc értékét (`0x007fc01b`, `0x007fc029`, `0x007fc02e`-`0x007fc039`). Utána a `[S+8, S+8 - (n-1) × S+0x30]` tartományba szorítja (`0x007fc045`-`0x007fc07e`). Itt `n = [S+0xb4] >> 1` (`0x007fc031`-`0x007fc037`). Az `n = 0` esetre a `0x00cf3ac0` (2^32) korrekció szolgál (`0x007fc055`).
  - A `0x009a5210` és a `0x009e5f90` függvények törzse NINCS MEG. A C kód szerint a láncuk értékét adja a görgetéshez.
- **c)** `S+0x80` (lista) és `S+0x84` (darab, bit 0 jelzővel): azoknak az elemeknek az indexe, amelyeknek `z > 0.1`. A 0.1 a `0x00c7dd30` double (`0x007fc119`, lebegőpontos összehasonlítás). A lista foglalása és felszabadítása: `0x007fc17e`, `0x007fc191`. A lista-írás C alapján igazolt, asm-ben nincs végigellenőrizve.
- **d)** Minden elemre (`i = 0..n-1`, a rekord `[S+0xb0] + i * 0xf8`):
  - Az elem `(x, y, z)` értéke a `0x007fbab0` visszatérése (`0x007fc100`). Forrása NINCS MEG.
  - `rec+0xa0` (int, alfa): `round((1 - E(d, 1.5)) * 256)`. Asm: `d = (1/z - 1) / 9` (`0x007fc3d4`, lebegőpontos osztás a `0x00cf3ef8` double-lel, amely 9.0; 0 alá nem engedve, C). Az `1.5` a `0x00cf3ec4` float (`0x007fc3f3` fld). Az `E` a `0x005568e0` hívás (`0x007fc40f`). A `256` a `0x00cf39d8` double (`0x007fc423` fmul), a kerekítés `fistp` (`0x007fc431`), a tárolás `0x007fc439`. Az `E` törzse NINCS MEG.
  - `rec+0xa4` ... `rec+0xcc`: 3×3 mátrix. Asm: `0x007fc27d lea eax,[eax+edx+0xa4]`; a tíz dword másolása C alapján. A tartalma C szerint: skála `z * S+0x28`, eltolás a `this+0x2c8` téglalap szélességével és magasságával.
  - `0x007fa650(rec)` hívás (`0x007fc44b`). Törzse NINCS MEG.
- **e)** A ciklus után `0x00604480` (`0x007fc48a`). Törzse NINCS MEG.

Nem ír: a rekord `+0` mezőjét. (Lásd a §7 kizártakat.)

**4. A `0x008014d0` (Q3, második fele).**

- Hívók: `0x008018a0` (`0x00801c95`) és `0x008037e0` (`0x008039d1`). A `this` a belépéskor az EDI (`0x008014d0` első utasítása: `mov ecx,[edi+0x2ec]`).
- Bemenet: a K kulcslista (`0x00801570` `mov esi,[edi+0x3ec]`, `0x00801576` `mov eax,[esi+eax*4]`), darab `[this+0x3f0] >> 1` (`0x0080150f`).
- Elő-takarítás: ha a C tömb nem nulla, `0x00803c10` fut (`0x008014e5`), majd `[this+0x2f0] &= 1` és `[this+0x2ec] = 0` (`0x008014ea`, `0x008014f1`).
- Minden kulcsra:
  1. Ha `[this+0x2e4]` (az obj2) nem nulla: `obj2.vt[0](k, &info, 1)` (`0x0080155f`-`0x0080157a`). A hívó három argumentumot tesz a verembe, és nem takarít (nincs `add esp`). Ezért a hívottnak 0xc bájtot kell kiengednie, különben a verem romlana. Ez szerződés; a törzs NINCS MEG.
  2. `0x007fa5b0` építi a kártya-rekordot (`0x00801580`).
  3. `0x00a6aa00(-1, -1, -1, -1)` (`0x008015a8`): egy referencia-számlált temp objektum.
  4. Négy `rand` hívás (`0x008015ad`, `0x008015be`, `0x00801633`, `0x00801644`), a kártya kis eltolásához.
  5. A rekord bekerül a C tömbbe: `0x00803b50` másolás (`0x0080178d`, `0x008017f3`), a tömb növelése `0x00c0769f` (`0x0080173b`) és `0x004010e0` (`0x0080175a`) hívással.
  6. A temp objektum felszabadítása: `InterlockedDecrement` (`0x0080181a`), majd `0x009a8bc0` (`0x00801862`, `0x0080186b`).
- A `this`-re írt mezők: `+0x2ec` és `+0x2f0` (asm: `0x008014f1`, `0x008017c7`, `0x0080180b`). Más írás nincs.
- **Nem rajzol.** A direkt hívások között nincs rajzoló. A `0x009a8bc0` egy képpufferszerű temp objektumot szabadít fel: a `[esi+8] * [esi+0xc] * 4` bájtot visszaadja a memória-számlálónak (`0x009a8bf4`-`0x009a8c0d`). Ez erős. Az `obj2.vt[0]` célja indirekt hívás, ezért nem zárható ki, hogy rajzol-e (U2).
- **Kapcsolat a kattintással**: a 38.2.41 §2 szerint a kattintás kártya-keresése a `0x007fd800` hívással az `S+0xb0` rekordjain megy. A `0x008014d0` a C tömböt építi. Hogy a kettő ugyanaz-e, vagyis hogy a C tömb másolódik-e az `S+0xb0` tömbbe, NINCS MEG (U5).

**5. A kattintás láncolata (kiegészíti a 38.2.41 §2-t).**
- `0x008018a0`: `__fastcall`, `ECX` = this, `EAX` = az új kulcs. Ha `[this+0x50c]` már egyenlő az `EAX`-szel, a függvény a `0x00801ca3`-ra ugrik (`0x008018ac`, `0x008018b2`). Különben `[this+0x50c] = EAX` (`0x008018b8`).
- Új kulcslista: `0x004b0190` hívás `EAX = [this+0x2f4]` és a kulcs argumentummal. A kimenet az `esp+0x20` objektumba kerül (`0x008018ce`-`0x008018e0`). A régi K felszabadul, és az új K a `0x00801b77` íráskor kerül a `[this+0x3ec]` mezőbe.
- Ez megerősíti a 38.2.40 §5 állítását: a K írója a `0x008018a0`. Egyben bővíti a 38.2.41 U3 sorát: a `0x004b0190` nem csak a P osztálya, a kattintási kulcslista forrása is.
- A függvény végén `0x008014d0` (`0x00801c95`), utána `0x00413490` (`0x00801c9e`). A `0x00413490` törzse LEZÁRVA (38.2.43 §2: destruktor-lánc).

**6. A 38.2.41 nyitott listájának frissítése (Q5).**

| tétel | állapot (38.2.42) | mit mutat | Ghidra-cím |
|---|---|---|---|
| U1, 0x00a6aa00 teljes törzs | NINCS MEG (változatlan) | a `0x008014d0` hívja `(-1, -1, -1, -1)` argumentumokkal; referencia-számlált temp objektum | `0x00a6aa00` |
| U2, obj2 osztálya és vt+0 célja | RÉSZBEN LEZÁRVA: a hívás módja megvan (§4), a cél NINCS MEG | a kártya-adat visszahívása | `0x005e8a70` (M olvasója; JAVÍTVA 38.2.43 §4), M+0x4c vt+0 |
| U3, L+0x48 vtábla, 11. slot, P osztálya | RÉSZBEN (38.2.44 §1), BŐVÜLT (38.2.43 §1.2, §6 U22): a kulcslistát a vt+0x2c hívás tölti; a cél NINCS MEG | P = `[OneUp+0x2f4]`, L = `[P+0xc4]`; vt-jelölt: `0x00c81fa4` (CThumbDB; JAVÍTVA 38.2.44 §1.3), slot 11 = `0x004406f0` (igazolt) | `0x004b0190` (törzs), `0x004b01f2` (call edx) |
| U4, 0x0080157a túlírás | NINCS MEG: a hívó nem takarít, a hívottnak 0xc bájtot kell kiengednie (szerződés, §4) | a vt+0 törzse dönt | `0x008014d0` vt+0 célja (U2) |
| U5, T+0x2ec olvasói | NINCS MEG: a `0x008014d0` írja a C tömböt | a rajzoló, és a C és az `S+0xb0` kapcsolata | a `[this+0x2ec]` olvasói: pásztázás |
| U6, 0x009aaae0 hívóhelyei | NINCS MEG (változatlan) | - | `0x009aaae0` (xrefs) |
| U7, sorrekord +0x14 írója | LEZÁRVA (38.2.41 §1) | - | - |
| U8, P' = [T+0x3a4] és írója | NINCS MEG (változatlan) | - | `0x007fa7f0` (T+0x3a4 írója) |
| U9, 0x008018a0 kattintási ága | LEZÁRVA (38.2.41 §2-3) | - | - |
| U10, a 0x004b8470 hívója és az [L+0x148] írói | RÉSZBEN LEZÁRVA: hívó a `0x004b8ee0` (`0x004b9192`), írója a `0x004b8ee0`, és a `0x004baaa0` rendezi (§1) | a rendezés kulcsa és a `0x004b8d00` (L-et kap) nyitott | `0x004a7890` (U16), `0x004b8d00` (U17) |
| U11, L osztálya, +0xc == 2, jbe | RÉSZBEN LEZÁRVA: L a `0x004b8ee0` és `0x004b8470` this-je, a `jbe` olvas `i == darab`-nál (§2) | L neve és vtáblája, a 2-es típus jelentése, a sortábla írói | L konstruktora (U3); `0x004b86d0` (darab-írás?); a sortábla írói: pásztázás |
| U12, EBP/EBX forrása a hívottakban | NINCS MEG (változatlan; most nem vizsgáltam) | - | `0x004b2e10`, `0x004b3770`, `0x004b80d0` |
| U13, 0x007fc010 | JAVÍTVA és RÉSZBEN LEZÁRVA (§3): nem írja a rekord `+0` mezőt; a többi írás megvan | az elem `(x, y, z)` és az E görbe NINCS MEG | `0x007fbab0`, `0x005568e0`, `0x007fa650`, `0x00604480` (U18, U19) |
| U14, 0x008014d0 törzse | RÉSZBEN LEZÁRVA (§4): nincs rajzoló hívás, a C tömböt épít K-ból | a C olvasója NINCS MEG (U5) | U5, `0x007fa5b0` (U20) |
| U15, startbutton vt+0x18 | NINCS MEG (változatlan) | - | `0x007fa7f0` (3. paraméter), a vt+0x18 célja |
| U16 (új), a rendezés kulcsa | RÉSZBEN LEZÁRVA (38.2.43 §3): a sorrend megvan, a forrásai NINCS MEG | a `0x004a7890` összehasonlító; a `DAT_00d67678` globálist a hívó (`0x004b9150`) állítja | `0x004a7890`, `0x004b9150` |
| U17 (új), 0x004b8d00 | NINCS MEG | L-et kap (az `[L+0xdc] == 2` ág); ír-e `[L+0x13c]`-t vagy `[L+0x148]`-at | `0x004b8d00` |
| U18 (új), az E görbe | NINCS MEG | az `E(d, 1.5)` függvény, amely az alfát adja | `0x005568e0` |
| U19 (új), rekord-utólag és ciklus-utáni lépés | NINCS MEG | a `0x007fa650` a rekord utólagos lépése, a `0x00604480` a ciklus utáni lépés | `0x007fa650`, `0x00604480` |
| U20 (új), kártya-rekord építése | NINCS MEG | a `0x007fa5b0` az obj2 kimenetéből építi a rekordot | `0x007fa5b0` |
| U21 (új), a kattintás környéke | LEZÁRVA (38.2.43 §2): a `0x004133e0` a `CSlice` konstruktora, a `0x00413490` a destruktor-lánc (`esp+0x1c` = O1). A kulcslista tartalma a U22 | `0x004133e0`, `0x00413490` |

Helyesbítés (38.2.42): a 38.2.41 U13 sora téves volt (a `0x007fc010` nem ír rekord `+0`-t). A 38.2.41 §3 NINCS MEG tétele a `0x007fc010` törzséről most részben lezárva. A 38.2.41 U3 sora bővült (a `0x004b0190` a kulcslistát adja a kattintáskor).

**7. Amit KIZÁRTAM.**
- „A `0x007fc010` írja a rekord `+0` mezőjét”: CÁFOLVA. Az asm-ben az írásai: `S+0x18`, `S+0x20`, `S+0x80`, `S+0x84`, `rec+0xa0`, `rec+0xa4`-től a mátrix.
- „A `0x008014d0` a K-ból rajzol”: CÁFOLVA, nincs direkt rajzoló hívás. Az `obj2.vt[0]` célja nyitott (U2).
- „Az i-lista sorrendje a sorindex-sorrend”: NEM IGAZOLT, mert a `0x004baaa0` rendez.
- „A `jbe` nem olvas `i == darab`-nál”: CÁFOLVA (`0x004b29ea`).
- „A `0x008018a0` nem írja a K listát”: CÁFOLVA. A 38.2.40 §5 állítása helyes (`0x00801907`, `0x00801b77`).
- „A `0x004b8470` hívója csak a `0x004b8ee0`”: igaz a direkt hívásokra (index és asm), de az index nem lát vtábla-hívást, ezt nem zártam ki.

**Nyitott kérdések mérlege (38.2.42).** 21 tétel: a 38.2.41 listája (U1-U15) és az új U16-U21. LEZÁRVA: 2 (U7, U9). RÉSZBEN LEZÁRVA: 5 (U2, U10, U11, U13, U14). NINCS MEG: 14, mindegyik mellett Ghidra-cím vagy konkrét pásztázási út. Blokkolt: 0. Hatókörön kívül: 0. Cím és pásztázási út nélkül: 0. Az U16-U21 hat tétel új ebben a körben, ezeket a következő körben le kell zárni.

#### A felhasználó szemével

Kattintáskor a kártya kulcsa lesz a kijelölt kulcs, és a program új kulcslistát kér a P-objektumtól. Minden kulcshoz új kártyát épít, az adatát a kulcs szerinti visszahívás adja.

Hogy egy kulcs melyik képeket jelenti (albumot vagy mappát), nem derült ki, ezért melyik képhalmaz jelenik meg: NINCS MEG.

Hiányzó címek: `0x004b0190` (ez adja az új kulcslistát), `0x005e8a70` és az `M+0x4c` vt+0 (ez tölti ki a kártya adatát), `0x007fa5b0` (a kártya-rekord építése), és a `[this+0x2ec]` olvasója (U5), amely a kártyákat megjeleníti.

#### 38.2.43 Az Időrend bináris feltárása, 26. kör: a kulcslista, a `CSlice`, a rendezés és a felhasználó szemével (#5401, 2026-10-21)

**Válasz röviden.**
1. **Q1, a kulcslista.** A kattintás (`0x008018a0`) az új kulcsot a `[this+0x50c]` mezőbe írja, és egy üres `CSlice` objektumot épít (`esp+0x1c`). A `0x004b0190` ezt a kulcsot és ezt az objektumot kapja. A `0x004b0190` zárolja a `[P+0xc4]` objektumot (L), majd meghívja az `[L+0x48]` objektum vt+0x2c metódusát (kulcs, ESI). **A listát ez a metódus tölti, a célja NINCS MEG.** Hogy a lista melyik képhalmazt jelenti, NINCS MEG.
2. **Q1b, az albumrendezés.** Ugyanaz a minta: a `0x004133e0` épít `CSlice` objektumot, a `0x004b0190` tölti (`album-sorrend.md` 110. sor). A szerep (kulcs, amelyből `CSlice` lista lesz) egyezik. A rendezés nem: az album a kereső-index sorrendjét használja, rendezés nélkül. Az Időrend a `0x004baaa0`-val rendez. A két spec a betöltő vt-slotjáról sem ért egyet (§1.4).
3. **Q2.** A `0x004133e0` a `CSlice` üres konstruktora. A `0x00413490` a `CSlice` destruktor-lánca (`CSlice`, ytBaseThread, IShouldExit).
4. **Q3, a rendezés kulcsa.** Nem egyetlen kulcs van, hanem egy sorrend: (a) bájt-jelző, (b) a sor neve (kis-nagybetű nem számít), (c) egy szám, amelynek a jelentése a `[L+0xd8]` módtól függ, (d) a második név, (e) csökkenő sorrend, ha `[L+0x165]` nem nulla. Az index nem kulcs: egyenlő kulcsnál 0-t ad. A dátum-jelleg RÉSZBEN igazolt (38.2.44 §3). A `0x005e8a70` az M objektumot (`[this+0x2bc]`) olvassa, közvetlen írást nem találtam benne. A 38.2.40-42 "M írója" állítása téves (javítva).
5. **Q4.** Melyik képhalmaz jelenik meg: NINCS MEG. Lásd a szakasz végét és §6.
6. **Q5.** A 38.2.42 nyitott listája frissítve (§7).

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-26.txt` volt (öt cím: `0x004b0190`, `0x004a7890`, `0x004133e0`, `0x00413490`, `0x005e8a70`). Az asm-ellenőrzés `pe_dis.cdis`-szel történt: a kattintási belépés (`0x008018a0`), a `0x004b0190` hívásai és visszatérései, és a `0x005e8a70` teljes törzsének bájt-keresése (30000 bájt). A vtábla-slotokat `pe_dis.read`-del olvastam. A "sor" számok a `2026-10-21-idorend-26.txt` bemeneti fájl sorai. Kódot nem módosítottam, ezért CI-őr nem futott. Ideiglenes fájl nem készült, `.bt/` nincs.

**Bizonyítottsági fok.** Az asm-ből igazolt állítás erős. Ami csak a dekompilációból jön, azt jelölöm: "(dekompiláció)".

**§1. Q1: a kattintás és a kulcslista (asm).**

**§1.1 A kattintási belépés (`0x008018a0`, asm).**
- `0x008018ac`-`0x008018b8`: ha `[this+0x50c]` már az új kulcs, ugrás `0x00801ca3`-ra. Különben `[this+0x50c] := kulcs`.
- `0x008018be`-`0x008018c2`: `lea eax,[esp+0x1c]`, majd `call 0x4133e0`. Az O1 = `esp+0x1c` objektum egy `CSlice`, amelyet a ktor épít.
- `0x008018c7`-`0x008018cd`: `push [this+0x50c]`, a kulcs argumentumként.
- `0x008018ce`-`0x008018e0`: `EAX = P = [this+0x2f4]`, `ESI = esp+0x20` (ez O1), `call 0x4b0190`.
- A `0x004b0190` minden visszatérése `ret 4`. A hívott takarítja le a kulcs argumentumot, így a verem a hívás után visszaáll. Ezért O1 = `esp0+0x1c`, ahol `esp0` a hívás előtti verem-mutató.
- `0x008018e5`: a hívó nem nézi a `0x004b0190` visszatérési értékét. Azonnal a K-listát olvassa (`[this+0x3ec]`).

**§1.2 A `0x004b0190` (dekompiláció 62-145. sor; a hívások asm-ben igazolva).**
- Zár: `L = [P+0xc4]`. Ha `L+0x74` nulla, a `[L+0x68]` vtábla `+0x18` zárat hív (`0x004b01d1`), különben `EnterCriticalSection(L+0x90)`. A végén a zár feloldódik.
- A hívás: `call edx` (`0x004b01f2`), az `[L+0x48]` objektum vt+0x2c metódusa, két argumentummal: a kulcs és az ESI (O1). Ezt a 38.2.40 §4 asm-ben már igazolta.
- A 18 mutatót (O1+0x68 ... O1+0xc0) a P sub-objektumaira köti (például `P+0x29c`, `P+0x2a4`, `[P+0x2a8]+0xcc`).
- Visszatérés: `-1`, ha O1+0x5c vagy O1+0x64 nulla. Különben `0` (dekompiláció, 115-144. sor).

**§1.3 A lista fogantyúja és darabszáma (asm).**
- A lista fogantyúja (handle) `[esp+0x80]`, vagyis O1+0x64. `0x00801952`: `cmp [esp+0x80], 0`. Ha nulla, a lista üres, és a kód kihagyja a másolást.
- A darabszám: `0x008019b9` `mov ecx,[esp+0x80]`, `0x008019c0` `mov esi,[ecx+4]`, `0x008019c3` `shr esi,1`. Tehát a darabszám a fogantyú `+4` mezőjének `>> 1` értéke.
- A 38.2.37 szakasz (5843. sor) ezt tévesen írta: `ESI+0x60` és `[esp+0x84]`. Javítva.

**§1.4 Mit tölt a vt+0x2c, és mi a jelölt?**
- A vt+0x2c célja NINCS MEG, mert az `[L+0x48]` objektum osztálya ismeretlen.
- Jelölt: az `album-sorrend.md` 2.1 szerint a `CThumbDB` (vtábla `0x00c81fa4`; **JAVÍTVA 38.2.44 §1.3**: nem IThumbDB) +0x2c slotja a `0x004406f0`. A bináris olvasás ezt megerősíti: a `0x00c81fa4+0x2c` cím tartalma `0x004406f0`. Ha `[L+0x48]` ez a vtábla, a cél `0x004406f0`. Ez NINCS MEG, mert nem igazoltam, hogy `[L+0x48]` ez a vtábla (38.2.44 §1.4).
- A `0x004b0190` nem az IThumbDB slotját hívja, hanem az `[L+0x48]` objektum slotját. Az `album-sorrend.md` 110. sora ezt közvetlen slot-hívásnak írja le. Ez pontatlan. Az album-sorrend spec-et nem módosítottam.

**§1.5 A K-lista és a kártyák.**
- `0x008018e5`-`0x0080190d`: a régi K felszabadul (`0x0097caf0`), `[this+0x3f0] &= 1`, `[this+0x3ec] := 0`, `[this+0x3f4] := 0`.
- A másolás a `0x0097c810` (realloc) hívással és a `0x00801b77` tárolással igazolt. Az elemek másolásának törzse NINCS MEG (lásd §6, U26).
- Utána a `0x008014d0` építi a kártyákat (38.2.42 §4).

**§2. Q2: a `0x004133e0` és a `0x00413490` (dekompiláció).**
- **`0x004133e0`** (916-956. sor): `FUN_0097adb0(0)` (ős-konstruktor), `*this = CSlice::vftable` (az `album-sorrend.md` 2.1 szerint `0x00c81e94`). Nullázza a mezőket `+0x48`-tól `+0xc0`-ig, a bájt-jelzőket (`+0x94`, `+0x95`) is. Tehát O1 üres objektum.
- **`0x00413490`** (1229-1259. sor): a destruktor-lánc `CSlice` → `ytBaseThread` → `IShouldExit` sorrendben (a vtábla-visszaállítások sorrendje ezt mutatja). Felszabadítja a `+0x54` és a `+0x4c` fogantyút (`0x0097caf0`). A `+0x94` jelzőtől függően hívja a `0x006cb680`-t. A `+0x5` bájt és a `+0x1c` mező alapján hívja a `0x0097b210`-t és a `0x0097b420(0)`-t. Végül `DeleteCriticalSection(+0x28)` és `CloseHandle(+0x40)`.
- A `+0x60` (szó) és a `+0x64` (lista) mezőket a destruktor nem szabadítja fel. Ez arra utal, hogy nézetek, nem saját tömbök. Az `album-sorrend.md` 2.1 is így írja le a `slice+0x60`-at és a `slice+0x64`-et.

**§3. Q3: a rendezés kulcsa (`0x004a7890`, dekompiláció 165-768. sor).**
- A rendezést a `0x004baaa0` végzi, összefésüléses módszerrel (38.2.42 §1). Az összehasonlító `param_1`-je a rendező objektum (`L`), mert a törzs `L+0xd8`, `L+0xdc` és `L+0x165` mezőit olvassa.
- **Fő ág** (ha nincs mindkét sornak üres neve):
  1. Bájt-jelző: a `DAT_00d67678` globális objektum `+8` táblájának két bájtja (199-246. sor). A kisebb előre megy.
  2. A sor neve: a `FUN_004a71e0()` két eredménye karakterláncként. Kis-nagybetű nem számít (`'@' < c < '['` esetén `+0x20`). Ha különböznek, ez dönt (247-305. sor).
  3. Módtól függő szám (475-595. sor): `L+0xd8 == 0`: a `ctx+0x18` tábla `+0x60 + 8i` helyén lévő double. `== 4`: a `0x004502e0` által adott double. `== 1`: a `0x004ae0d0` float10 értéke. `== 5`: a `0x004507e0` által adott 64 bites pár.
  4. A második név: a `ctx+0xc` tábla karakterláncai (530-600. sor).
  5. Csökkenő sorrend: ha `[L+0x165] != 0`, a sorrend megfordul (602-605. sor).
- **Ág, ha mindkét sornak üres a neve** (337-471. sor): négy `FUN_00987030` hívás (mit adnak, NINCS MEG). Itt jön a kijelölt sor (`[L+0xc4]+0x2960` szerinti sor), és a rang-tömb (`L+0xdc == 2`: `L+0x438`; `== 1`: `L+0x428`).
- Egyenlő kulcsnál a törzs 0-t ad (436. sor). Az index nem kulcs.
- **Dátum?** A 3. pont double-je a 0. módban van. Hogy ez dátum-e, RÉSZBEN igazolt (38.2.44 §3.7): a 0. mód felületi neve `datesort`, de a `ctx+0x18` tábla tartalma és forrása NINCS MEG.

**§4. Q3 második fele: a `0x005e8a70` és az M objektum.**
- M = `[this+0x2bc]` (dekompiláció: `param_1[0xaf]`). Asm: a törzsben 47 előfordulás van `[reg+0x2bc]` alakban; a látott példák mind olvasások. Dword-írás `[reg+0x2bc]`-re: 0 találat (disasm-szűrés).
- Asm-ben igazolt írások a törzsben: `mov byte ptr [ecx+0x35c], 0` (`0x005e8ce2`) és `fstp dword ptr [ecx+0x3a4]` (`0x005e8d1f`). A dekompiláció szerint ezek a `[this+0x327c]` objektumra (`param_1[0xc9f]`) mennek, nem M-re. Hogy az `ecx` tényleg ez, nem igazoltam.
- **Ellentmondás.** A dekompiláció szerint M+0x64c := 3 és M+0x650 := 1 (1569-1570. sor), és M+0x4c vt+8 hívás (1436. sor). Az asm bájt-keresésben a `0x64c` és a `0x650` eltolás NEM található (0 találat 30000 bájtban). Ezért az M+0x64c és M+0x650 írás NINCS MEG. Ghidra-ellenőrzés kell (lásd §6, U27).
- **Következtetés.** A `0x005e8a70` M-et olvas. Közvetlen írást M mezőibe asm-ben nem igazoltam. A 38.2.40-42 "M írója" jelölés ezért téves (javítva). Az M+0x4c vt+8 hívás célja NINCS MEG.

**§5. A kulcslista tartalma és a képhalmaz.**
- Ami megvan (asm): a kulcs bekerül `[this+0x50c]`-be, a lista O1+0x64 fogantyúba kerül, a darabszám a fogantyú `+4` mezője, a lista K-ba másolódik (`[this+0x3ec]`, darab: `[this+0x3f0] >> 1`), és a `0x008014d0` kártyákat épít belőle.
- Ami NINCS MEG: a lista tartalma (a vt+0x2c célja), és hogy melyik képhalmazt jelenti.

**§6. Hiányzó címek (következő Ghidra-kör).**
- **U22** (RÉSZBEN, 38.2.44 §1): a `0x004b0190` vt+0x2c célja (`call edx` a `0x004b01f2`-nél). Kezdőpont: az `[L+0x48]` objektum osztálya és az `L = [P+0xc4]` konstruktora. Ha az osztály CThumbDB (vtábla `0x00c81fa4`; JAVÍTVA 38.2.44 §1.3), a cél `0x004406f0` (az `album-sorrend.md` 2.1 szerint, bináris olvasással igazolva a slotot, a hozzárendelés nincs).
- **U23** (a törzs LEZÁRVA, a forrás U30; 38.2.44 §2): a `0x004a71e0` (a sor neve): törzse és forrása.
- **U24**: a `0x004502e0`, `0x004ae0d0`, `0x004507e0`: a mód szerinti számok forrása és jelentése (dátum-e) (RÉSZBEN, 38.2.44 §3).
- **U25**: a `0x00987030`: a négy hívás a két üres-név ágban.
- **U26**: a `0x00801915`-`0x00801bc4` közötti K-másolás törzse: honnan veszi az elemeket.
- **U27**: a `0x005e8a70` 1552-1570. sorának (dekompiláció) M+0x64c és M+0x650 írása: asm-ellenőrzés vagy cáfolat.

**§7. A 38.2.42 nyitott listája a 38.2.43 után.**
A 38.2.42 listája 21 tételből állt. Most: **LEZÁRVA 3** (U7, U9, U21). **RÉSZBEN LEZÁRVA 6** (U2, U10, U11, U13, U14, U16). **NINCS MEG 12** (U1, U3, U4, U5, U6, U8, U12, U15, U17, U18, U19, U20).
A 38.2.43 új tételei: U22-U27, mind NINCS MEG. A nyitott lista így 27 tétel: LEZÁRVA 3, RÉSZBEN 6, NINCS MEG 18.
**Frissítve (38.2.44 §6):** 34 tétel: LEZÁRVA 4, RÉSZBEN 9, NINCS MEG 21 (az új tételek: U28-U34).
A 38.2.42 táblájában a U2, U3, U16 és U21 sor, valamint a §5 mondat a 38.2.43 szerint frissítve (jelölve).

**Helyesbítések a korábbi szakaszokban.**
1. 38.2.37 (5843. sor): a lista fogantyúja `ESI+0x64` (nem `ESI+0x60`), a darabszám a fogantyú `+4` mezőjének `>> 1` értéke (nem `[esp+0x84]`).
2. 38.2.40 (6274. sor), 38.2.41 (6386. sor) és 38.2.42 (6520. sor): a U2 sorban "0x005e8a70 (M írója)" helyett "M olvasója". A 0x005e8a70 nem ír M-be (§4).
3. 38.2.42 §5: a `0x00413490` törzse LEZÁRVA (§2).
4. 38.2.42 U21 sor: LEZÁRVA (§2).
5. Az `album-sorrend.md` 110. sora ("0x004b0190 tölti (IThumbDB+0x2c)") pontatlan (§1.4). Ezt a dokumentumot ebben a körben nem módosítottam.

**Nyitott kérdések mérlege (38.2.43).** Q1: részben (a lista töltője NINCS MEG). Q2: LEZÁRVA. Q3: részben (a sorrend megvan, a forrásai NINCS MEG). Q4: NINCS MEG. Q5: kész.

#### A felhasználó szemével

Kattintáskor a program eltárolja az új kulcsot, és egy új, üres `CSlice` objektumot épít. Ezt egy hívás tölti fel a kulcshoz tartozó listával (a hívás célja NINCS MEG), majd a lista K-ba másolódik, és belőle épülnek a kártyák (`0x008014d0`).

Hogy a lista mely képeket jelenti (album, mappa, dátumtartomány vagy az egész könyvtár), NINCS MEG. Ezért azt sem tudjuk megmondani, melyik képhalmaz jelenik meg. Hiányzó címek: `0x004b0190` vt+0x2c célja (U22), a `0x004a71e0` (U23), a K-másolás törzse (`0x00801915`-`0x00801bc4`, U26), és a `[this+0x2ec]` olvasója (U5), amely a kártyákat megjeleníti.

#### 38.2.44 Az Időrend bináris feltárása, 27. kör: a vt+0x2c cél, a sor neve, a mód-számok és a felhasználó szemével (#5401, 2026-10-21)

**Válasz röviden.**
1. **Q1, a vt+0x2c cél (U22): RÉSZBEN.** A `0x004b01f2` hívás célja az `[L+0x48]` vtábla +0x2c slotja. Ha ez a `0x00c81fa4` vtábla, a cél `0x004406f0`, és ez igazolt. A vtábla nevét javítottam: a RTTI szerint `CThumbDB`, nem `IThumbDB`. Az `[L+0x48]` vtáblája és az L osztálya NINCS MEG.
2. **Q2, a sor neve (U23): a törzs LEZÁRVA.** A `0x004a71e0` a sor indexéből két tábla-lépéssel egy cellát ad, a cella egy név-objektumra mutat. A két tábla feltöltése (a forrás) NINCS MEG (U30).
3. **Q3, a mód-számok (U24): RÉSZBEN.** A 4. és az 1. mód minden elemre egy dátumot olvas: FILETIME, helyi idő, OLE-dátum (double, egység: nap). Az 5. mód a rekordok `+0x14` mezőinek összege (egység: bájt). A 0. mód egy double-tábla (`G+0x18`), a tartalma NINCS MEG. Az összesítők NINCS MEG.
4. **Q4, a felhasználó szemével: RÉSZBEN.** A kattintás a kulcs listáját tölti be, és ebből épülnek a kártyák. Hogy az elemek képek-e, és melyik képhalmaz jelenik meg, NINCS MEG (§4).
5. **Q5, a 38.2.43 listája: frissítve (§6).** 34 tétel: LEZÁRVA 4, RÉSZBEN 9, NINCS MEG 21.

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-27.txt` volt, öt címmel: `0x004406f0`, `0x004a71e0`, `0x004502e0`, `0x004ae0d0`, `0x004507e0`. Az asm-ellenőrzés `pe_dis.cdis`-szel történt. A bináris indexből az `rtti`, `functions`, `imports` és `xrefs` táblát olvastam. A PE-fájl bájtjaiból az IAT-slotokat és a vtábla-címek kódbeli íróit néztem. Ideiglenes fájl a `.bt/` alatt volt (`vt_irok.py`), a kör végén törölve. Kódot nem módosítottam, ezért CI-őr nem futott.

**Bizonyítottsági fok.** Az asm-ből és a bináris indexből igazolt állítás erős. A dekompilációból jövő állítást jelölöm.

**§1. Q1: a vt+0x2c cél (U22).**

**§1.1 A hívás (asm, 38.2.40 §1 megerősítve).** A `0x004b01dd`-`0x004b01f2` utasítások: `EAX = L`, `EDX = [L+0x48]` (a vtábla), `EDX = [EDX+0x2c]` (a 11. slot), `ECX = L+0x48`. A verembe előbb az ESI (az O1 kimenet) kerül, utána a kulcs, majd `call edx`. A hívott takarítja a két argumentumot. A `0x00450bd0` ugyanezt a mintát használja (`0x00450bf0`-`0x00450c0e`), itt `ECX = Z+0x48`, ahol `Z = [L+0xc4]` (§3).

**§1.2 A slot értéke (igazolt).**
- Az `rtti` tábla szerint a `0x00c81fa4` vtábla neve `CThumbDB::vftable`, 64 slot. A +0x2c slot értéke `0x004406f0`.
- A Ghidra-hivatkozás: a `0x004406f0`-ra egyetlen hivatkozás van, a `0x00c81fd0` adat-cím, ami `0x00c81fa4 + 0x2c`.

**§1.3 Név-javítás (JAVÍTVA).** A 38.2.42 U3 sorában, a 38.2.43 §1.4-ben és §6 U22-ben a `0x00c81fa4` vtáblát `IThumbDB`-nek írtam, az `album-sorrend.md` 2.1 szakasza nyomán. Ez téves:
- Az `IThumbDB::vftable` címe `0x00c82544`. Ennek +0x2c slotja `0x00c07709`, nem `0x004406f0`.
- A `0x00c81fa4` a `CThumbDB` vtáblája (RTTI). Az `album-sorrend.md` 2.1 szakaszát ebben a körben nem módosítottam, de a névhibát ott is javítani kell.

**§1.4 Az [L+0x48] osztálya (NINCS MEG).**
- A `0x00c81fa4` címet két kódhely írja a `[reg+0x48]` mezőbe: `0x00415804` (a `0x00415790` függvényben) és `0x0041777f` (a `0x00417770` függvényben).
- A `0x00415790` a RTTI nevei alapján a `CThumbDB` teljes objektum konstruktora. Előbb az `IThumbDB` alobjektum vtáblája áll a +0x48 mezőben (`0x004157bd`: `0x00c82544`), utána a `CThumbDB` vtáblái (`0x00415804`-`0x00415835`).
- Hívói: `0x00402f90` (hívás: `0x00402fd3`; az eredményt `[ebx+0x1034]` kapja: `0x00402fdc`), `0x00467ca0` (`0x00467d1b`), és `0x0053fe30` (`0x0053ff35`). A két utóbbi a veremben lévő objektumot építi.
- Az L (= `[P+0xc4]`) írója nincs megtalálva. A `0x00402f90` a `[ebx+0x1034]` mezőt írja, nem `[P+0xc4]`-et. Ezért az, hogy L a `0x00415790` példánya, NINCS MEG.
- Ghidra-kör kell: `0x00402f90` (a `[ebx+0x1034]` objektum és a P/L kapcsolata), és a `[P+0xc4]` íróinak keresése (U3, U29).

**§1.5 A kulcs és a kimenet (dekompiláció, `0x004406f0`).**
- Bemenet: a kulcs (`param_2`) és a kimeneti objektum O1 (`param_3`). A `0xffffffff` kulcs eredménye -1.
- A kulcshoz tartozó bejegyzést a `[this+0xb00]` táblából veszi. Ha a kulcs kívül esik, vagy nincs tábla, a `[this+0xb04]` mező a bejegyzés. A bejegyzés hivatkozásszámlált objektum (`InterlockedIncrement`).
- A bejegyzés tartalmát a `0x004dca40(bejegyzés+4, O1)` tölti ki. Ennek törzse NINCS MEG (U28). ⚠️ **HELYESBÍTVE (38.2.45 §1.1):** a `0x004dca40` nem tölt ki bejegyzést. A nevet keresi a `CIndexer` táblában, és találatnál három mezőt ír az O1 objektumba.
- Ezért az, hogy a bejegyzés képeket vagy albumokat sorol-e, NINCS MEG.

**§2. Q2: a sor neve (U23).**

**§2.1 A hívás (asm).** A `0x004a7890` összehasonlítóban két hívás van:
- `0x004a796d`: `EAX = EDI = [esp+0x34]` (a dekompilált első sor, `param_2`), `call 0x004a71e0`.
- `0x004a7976`: `EAX = EBX` (a dekompilált második sor, `param_3`), `call 0x004a71e0`.
A függvény a sor indexét EAX-ban kapja.

**§2.2 A törzs (dekompiláció, 75 bájt).** `G` a `DAT_00d67678` globális objektum, `i` a sor indexe.
1. `A = [G+0x1c]`. Ha `i` kisebb az `A` tábla darabszámánál (a tábla `[A+0x58]`, darab: `[[A+0x58]+0x4c] >> 1`), a cella címe `[[A+0x58]+0x48] + 4*i`. Különben a cella `A+0x5c`.
2. `j = *cella`. Ha `j` kisebb a `B` tábla darabszámánál (`B = [G+4]`, tábla `[B+0x58]`), a visszatérés `[[B+0x58]+0x48] + 4*j`. Különben a visszatérés `G+4+0x5c`.
A visszatérés tehát egy cella címe. A cella tartalma egy név-objektum címe, a név a `+4` mezőtől van. Ha a cella 0, a név üres. Ezt igazolja a `0x004a7890` összehasonlítása (`*piVar9 + 4`).

**§2.3 A forrás (részben).**
- A `G` közvetlen hivatkozásait kimerítő `imm32`-kereséssel néztem. Írója a `0x004b94a0`: `0x004b9735`, `mov [0x00d67678], eax`. Olvasói a `0x004a71e2`, `0x004a789b`, `0x004a7e78`, `0x004a7eed`, `0x004a7f5b`, `0x004b9152`, `0x004b9178`, és a `0x004b94a0` belsejében a `0x004b9755` hely.
- Az `A`, a `B` és a többi tábla (`G+0x18`, `G+8`, `G+0xc`) feltöltése NINCS MEG. A `0x004b94a0` törzse nincs dekompilálva (U30).

**§3. Q3: a mód-számok (U24).**

**§3.1 A mód-ág (dekompiláció, 475-605. sor; a hívások asm-ben).** A `0x004a7890` a `L+0xd8` értéke szerint ágazik. Mindegyik ág az összehasonlított sorokra (`i`) ad egy-egy értéket. A `G+0x18` a 38.2.43 `ctx+0x18` tábla.

| mód (`L+0xd8`) | hívás (asm-ben igazolt) | érték | egység | dátum? |
|---|---|---|---|---|
| 0 | `G+0x18` double-tábla `[i]` (belső mező `+0x60`, dekompiláció) | double | NINCS MEG | a felületi neve `datesort` (68.1); a tartalma NINCS MEG |
| 4 | `0x004502e0(Z, i, &ki)` (asm: `0x004a7e2f`, `0x004a7e41`) | double (OLE-dátum) | nap | igen, elemenként (§3.4) |
| 1 | `0x004ae0d0(i)` → `0x00450bd0(Z, i, &ki)` (asm: `0x004a7e8d`, `0x004a7e9a`) | float10 | NINCS MEG (az összesítés) | igen, elemenként (`0x00450f67`); a felületi neve „legutóbbi változtatás" (`0x005cbc2d`, 68.1) |
| 5 | `0x004507e0(Z, i, &ki)` (asm: `0x004a7f0f`, `0x004a7f21`) | 64 bites összeg | bájt | nem (§3.5) |

`Z = [L+0xc4]`: asm: `0x004a7e2f` (`mov eax,[edi+0xc4]`), `0x004a7e41` (`mov edx,[edi+0xc4]`), `0x004a7f14` (`mov eax,[edi+0xc4]`), és a `0x004ae0d0` (`mov eax,[edx+0xc4]`, EDX = L).

**§3.2 A közös hívás.** A 4., az 1. és az 5. mód ugyanazt a hívást végzi: a `[Z+0x48]` vtábla +0x2c slotját, kulcsnak a sor indexével (`i`), és egy kimeneti objektummal (O1). A `0x00450bd0`-ban ezt az asm igazolja (`lea ecx,[esi+0x48]`, ESI = Z). A `0x004502e0`-ban és a `0x004507e0`-ban a dekompiláció szerint `param_1 + 9` (double-indexben), illetve `param_1[0x12]`, azaz +0x48. Ezért a három mód lista-forrása ugyanaz, mint a kattintásé (§1).

**§3.3 A lista elemei (asm).** A lista elemei a `Z+0x4e8` rekord-tábla indexei: `0x00450618` `mov eax,[ecx+0x4e8]`, `0x004505cc` `mov edi,[ecx+edx*4]` (az elem), `0x0045061e` `lea eax,[eax+edi*4]`. Ha a tábla bejegyzése 0, az alapértelmezett rekord `Z+0x4f0`.

**§3.4 A dátum: `0x0098b650` (asm, 87 bájt).** Bemenet: EAX = a rekord +4 címe (`0x00450636` `add eax,4`, `0x00450639` `call 0x0098b650`). A függvény a 64 bites FILETIME-ot olvassa (`[eax]` és `[eax+4]`).
- Ha mindkét dword 0, vagy az API-hívás sikertelen, a visszatérés `949998.0` (a `0x00c7ccf8` konstans).
- Egyébként: `FileTimeToSystemTime` (IAT `0x00c403f0`), majd `SystemTimeToTzSpecificLocalTime` NULL időzónával (IAT `0x00c403e8`), majd egy ordinális import (IAT `0x00c405c8`, sorszám 184). Ez a helyi SYSTEMTIME-ot double-lé alakítja. A bináris index a 184. sorszámot OLEAUT32-höz rendeli, az IAT-blokk tulajdonosát nem ellenőriztem.
- Tehát egy elem értéke a helyi idő szerinti OLE-dátum, egysége nap. A `949998.0` azt jelenti, hogy nincs dátum. Növekvő rendezésnél a sor a végére kerül.

**§3.5 A méret (asm).** Az 5. mód (`0x004507e0`) a lista elemeinek rekordjaiban a `+0x14` (32 bites) mezőt összegzi, 64 bites értékbe. Egység: bájt. A felület „méret" módja (`0x005cc703`, 68.1) ugyanezt a sorrendet adja, és a 36.4 szakasz is bájtösszegként írja le.

**§3.6 Az összesítők (NINCS MEG).**
- A 4. mód `0x00450100` összesítője (478 bájt, dekompiláció nincs). Az asm-ben `cmp ebx,3` és `cmp ebx,4` ágak vannak. A statisztika neve (medián, minimum vagy más) NINCS MEG (U31).
- Az 1. mód: a `0x00450bd0` belső ága (1783 bájt). A `0x00450f67`-es `0x0098b650` hívás után további hívások (`0x00c07681`, `0x00c0769f`) és egy `fadd` jön. A végső képlet NINCS MEG (U32).

**§3.7 A 0. mód.** A `G+0x18` double-tábla `[i]` eleme. A tábla forrása NINCS MEG (U30 a `G`-re). A felületi név `thumbui/datesort` (68.1, a `0x005db26f` hívó, mód 0). A 0. mód tehát a „dátum" felirathoz tartozik, de a tábla tartalma nincs igazolva.

**§3.8 Az Időrend módja (NINCS MEG).** Az Időrend sorrendjéhez használt `L+0xd8` érték nincs megállapítva (U33). A kimerítő `c7 8x d8 00 00 00 imm32` keresés 16 találatot adott. Az 1, 2 és 3 értékű írások a `0x0054bad0` függvényben vannak (`0x0054bbc4`, `0x0054bb76`, `0x0054bb95`). ⚠️ **HELYESBÍTVE (38.2.45 §3):** ezek nem mód-írások, hanem egy lejátszási eseményhurok állapotkódjai (EC_COMPLETE, EC_USERABORT, EC_ERRORABORT). A `0x0054bad0` több különböző objektumon fut. A 0 értékű írások a `0x0054c4b0`, `0x006d2180`, `0x007f9090`, `0x00827120` és `0x009ba4d0` függvényekben vannak. Melyik sorrendező objektumhoz tartoznak, NINCS MEG. A register-író a `0x004b07c0` (68.1). A 4. mód csak a nyers registry-értéken át érhető el (68.1, 68.2).

**§4. A felhasználó szemével (Q4): RÉSZBEN.** Ez a rész a 38.2.43 „A felhasználó szemével" részét váltja.
1. A kattintás (`0x008018a0`) a kattintott elem kulcsát a `[this+0x50c]` mezőbe írja. A `0x004b0190` a kulcshoz tartozó listát tölti be (§1).
2. A listát a K lista veszi át (`[this+0x3ec]`, darab: `[this+0x3f0] >> 1`, 38.2.43 §1.5). A másolás törzse NINCS MEG (U26).
3. A `0x008014d0` kulcsonként egy kártya-rekordot épít (38.2.42 §4). A kártya adatát az `obj2.vt[0]` hívás adja (`M+0x4c`, U2).
4. A sorok sorrendjét a §3 szerinti mód adja. Az Időrend módja NINCS MEG (U33).

A felhasználó ezt látja: a sorok név szerint (kis-nagybetű nem számít) és a beállított mód szerint vannak sorba rendezve. Kattintásra a kattintott kulcshoz tartozó elemek kártyái jelennek meg. Hogy ezek az elemek képek-e vagy albumok, és hogy a kártya pontosan mit mutat, NINCS MEG.

Hiányzó címek a következő körhöz: `0x004dca40` (U28: a bejegyzés tartalma), `0x00402f90` és a `[P+0xc4]` írója (U29: L osztálya), `0x004b94a0` (U30: a G tábláinak feltöltése), `0x00450100` és a `0x00450bd0` belső ága (U31, U32: összesítők), `0x0054bad0` és társai (U33: az Időrend módja), `0x008014d0` és az `obj2.vt[0]` célja (U2, U20), a K-másolás törzse (U26).

**§5. Helyesbítések a korábbi szakaszokban (JAVÍTVA).**
1. A 38.2.42 U3 sora, a 38.2.43 §1.4 és a §6 U22: a `0x00c81fa4` vtábla neve `CThumbDB`, nem `IThumbDB`. Az `IThumbDB::vftable` (`0x00c82544`) slot 11 értéke `0x00c07709`. (§1.3)
2. A 38.2.43 §3 („A dátum-jelleg NINCS MEG"): részben igazolt. A 4. és az 1. mód elemenként OLE-dátumot olvas, az 5. mód bájtösszeget ad. A 0. mód tartalma NINCS MEG. (§3)
3. A 38.2.43 §1.4 „a lista album-token alapú" állítása nem igazolt. Törölve; a helyén a §1.4 áll.

**§6. A 38.2.43 nyitott listájának frissítése (Q5).** A 38.2.43 listája 27 tételből állt. Most 34 tétel van: LEZÁRVA 4, RÉSZBEN 9, NINCS MEG 21.

| tétel | állapot (38.2.44) | mit mutat | Ghidra-cím |
|---|---|---|---|
| U1 | NINCS MEG (változatlan) | 0x00a6aa00 teljes törzs | `0x00a6aa00` |
| U2 | RÉSZBEN (változatlan) | obj2 osztálya, vt+0 cél | `0x005e8a70`, `M+0x4c` vt+0 |
| U3 | RÉSZBEN (BŐVÜLT, §1) | a `0x00c81fa4` vtábla slot 11 = `0x004406f0` igazolt; L osztálya NINCS MEG | `0x00402f90`, `[P+0xc4]` írója (U29) |
| U4 | NINCS MEG (változatlan) | `0x008014d0` vt+0 hívott függvénye | `0x008014d0` |
| U5 | NINCS MEG (változatlan) | `[this+0x2ec]` olvasói | pásztázás |
| U6 | NINCS MEG (változatlan) | `0x009aaae0` hívóhelyei | `0x009aaae0` |
| U7 | LEZÁRVA (38.2.41 §1) | sorrekord +0x14 írója | - |
| U8 | NINCS MEG (változatlan) | `P' = [T+0x3a4]` írója | `0x007fa7f0` |
| U9 | LEZÁRVA (38.2.41 §2-3) | kattintási ág | - |
| U10 | RÉSZBEN (változatlan) | a `0x004b8470` hívója és az `[L+0x148]` írói | `0x004b8ee0` |
| U11 | RÉSZBEN (változatlan) | L osztálya, `+0xc == 2`, `jbe` | `0x004b29d0` |
| U12 | NINCS MEG (változatlan) | EBP/EBX forrása a hívottakban | `0x004b2e10`, `0x004b3770`, `0x004b80d0` |
| U13 | RÉSZBEN (változatlan) | `0x007fc010` | `0x007fc010` |
| U14 | RÉSZBEN (változatlan) | `0x008014d0` törzse | `0x008014d0` |
| U15 | NINCS MEG (változatlan) | startbutton vt+0x18 | `0x007fa7f0` |
| U16 | RÉSZBEN (BŐVÜLT, §3) | a 4., 1. és 5. mód forrása igazolt; a 0. mód tábla NINCS MEG | `0x004a7890`, `0x004b9150`, `0x004b94a0` |
| U17 | NINCS MEG (változatlan) | `0x004b8d00` | `0x004b8d00` |
| U18 | NINCS MEG (változatlan) | az `E` görbe | `0x005568e0` |
| U19 | NINCS MEG (változatlan) | rekord-utólagos és ciklus-utáni lépés | `0x007fa650`, `0x00604480` |
| U20 | NINCS MEG (változatlan) | kártya-rekord építése | `0x007fa5b0` |
| U21 | LEZÁRVA (38.2.43 §2) | a `CSlice` konstruktor és a destruktor-lánc | `0x004133e0`, `0x00413490` |
| U22 | RÉSZBEN (§1) | a cél `0x004406f0`, ha az X vtáblája `0x00c81fa4`; az X azonosítása NINCS MEG | `0x00402f90` (U29) |
| U23 | LEZÁRVA a törzs (§2); a forrás U30 | a sor neve: két tábla-lépés, a cella egy név-objektumra mutat | `0x004a71e0` |
| U24 | RÉSZBEN (§3) | a 4. és az 1. mód dátum, az 5. bájt; a 0. mód NINCS MEG | `0x00450100`, `0x00450bd0` (U31, U32) |
| U25 | NINCS MEG (változatlan) | a négy `0x00987030` hívás a két üres-név ágban | `0x00987030` |
| U26 | NINCS MEG (változatlan) | K-másolás törzse | `0x00801915`-`0x00801bc4` |
| U27 | NINCS MEG (változatlan) | `M+0x64c` és `M+0x650` írása | `0x005e8a70` |
| U28 (új) | NINCS MEG | a `0x004406f0` kulcs-bejegyzésének tartalma (`0x004dca40` törzse) | `0x004dca40` |
| U29 (új) | NINCS MEG | a `[ebx+0x1034]` objektum és az `[P+0xc4]` (L) írója; L osztálya | `0x00402f90`, `0x00467ca0`, `0x0053fe30` |
| U30 (új) | NINCS MEG | a `G` (`0x00d67678`) tábláinak feltöltése | `0x004b94a0` |
| U31 (új) | NINCS MEG | a 4. mód összesítője (`n = 3` és `n = 4` ágak) | `0x00450100` |
| U32 (új) | NINCS MEG | az 1. mód összesítője | `0x00450bd0` belső ága |
| U33 (új) | NINCS MEG | az Időrend `L+0xd8` értéke, és a hozzá tartozó író | `0x0054bad0` (1, 2, 3), `0x00827120`, `0x009ba4d0` és a többi |
| U34 (új) | NINCS MEG | az OLEAUT32 184. sorszám neve; Windows-os `oleaut32.dll` kell, ez nem Ghidra-kör | IAT `0x00c405c8` |

**§7. Nyitott kérdések mérlege (38.2.44).** Q1: RÉSZBEN. A cél igazolt, ha az X vtáblája `0x00c81fa4`. Az X azonosítása NINCS MEG. Q2: a törzs LEZÁRVA, a forrás NINCS MEG. Q3: RÉSZBEN. A 4., az 1. és az 5. mód típusa igazolt, az összesítők és a 0. mód tartalma NINCS MEG. Q4: RÉSZBEN. A lista és a kártya-keletkezés igazolt, az elemek jelentése NINCS MEG. Q5: kész.

**§8. Amit KIZÁRTAM.**
- „Az `IThumbDB` vtábla slot 11 a `0x004406f0`": CÁFOLVA. Az `IThumbDB::vftable` slot 11 értéke `0x00c07709`.
- „Az `[L+0x48]` objektum `IThumbDB`": CÁFOLVA a RTTI szerint. A `0x00c81fa4` vtábla `CThumbDB`.

**§9. Frissítés (38.2.45): a 38.2.44 nyitott listája.** A lista 40 tétel: a 34 régi (U1-U34) és hat új (U35-U40). A változásokat a 38.2.45 §1-§5 indokolja. **Ezt a listát a 38.2.46 §9 váltja fel (29. kör).**

| tétel | állapot (38.2.45 után) | mit mutat | Ghidra-cím |
|---|---|---|---|
| U1 | NINCS MEG (változatlan) | 0x00a6aa00 teljes törzs | `0x00a6aa00` |
| U2 | RÉSZBEN (változatlan) | obj2 osztálya, vt+0 cél | `0x005e8a70`, `M+0x4c` vt+0 |
| U3 | RÉSZBEN (38.2.45 §2) | L osztálya és írója; a `[X+0x1034]` írója LEZÁRVA | U36 |
| U4 | NINCS MEG (változatlan) | `0x008014d0` vt+0 hívott függvénye | `0x008014d0` |
| U5 | NINCS MEG (változatlan) | `[this+0x2ec]` olvasói | pásztázás |
| U6 | NINCS MEG (változatlan) | `0x009aaae0` hívóhelyei | `0x009aaae0` |
| U7 | LEZÁRVA (38.2.41 §1) | sorrekord +0x14 írója | - |
| U8 | NINCS MEG (változatlan) | `P' = [T+0x3a4]` írója | `0x007fa7f0` |
| U9 | LEZÁRVA (38.2.41 §2-3) | kattintási ág | - |
| U10 | RÉSZBEN (változatlan) | a `0x004b8470` hívója és az `[L+0x148]` írói | `0x004b8ee0` |
| U11 | RÉSZBEN (változatlan) | L osztálya, `+0xc == 2`, `jbe` | `0x004b29d0` |
| U12 | NINCS MEG (változatlan) | EBP/EBX forrása a hívottakban | `0x004b2e10`, `0x004b3770`, `0x004b80d0` |
| U13 | RÉSZBEN (változatlan) | `0x007fc010` | `0x007fc010` |
| U14 | RÉSZBEN (változatlan) | `0x008014d0` törzse | `0x008014d0` |
| U15 | NINCS MEG (változatlan) | startbutton vt+0x18 | `0x007fa7f0` |
| U16 | RÉSZBEN (38.2.45 §4) | a szűrő és a rendező szerepe igazolt; a G-táblák feltöltése NINCS MEG | `0x004b94a0` (kész), U37, U38 |
| U17 | NINCS MEG (változatlan) | `0x004b8d00` | `0x004b8d00` |
| U18 | NINCS MEG (változatlan) | az `E` görbe | `0x005568e0` |
| U19 | NINCS MEG (változatlan) | rekord-utólagos és ciklus-utáni lépés | `0x007fa650`, `0x00604480` |
| U20 | NINCS MEG (változatlan) | kártya-rekord építése | `0x007fa5b0` |
| U21 | LEZÁRVA (38.2.43 §2) | a `CSlice` konstruktor és a destruktor-lánc | `0x004133e0`, `0x00413490` |
| U22 | RÉSZBEN (38.2.45 §1.2) | a `0x004406f0` `this`-e `L+0x48`, a keresőobjektum `L+0x68`; a `[L+0x48]` vtábla `0x00c81fa4` még nincs újra igazolva | `0x00402f90` (U29) |
| U23 | LEZÁRVA a törzs (38.2.44 §2); a forrás U30 | a sor neve: két tábla-lépés, a cella egy név-objektumra mutat | `0x004a71e0` |
| U24 | RÉSZBEN (38.2.44 §3) | a 4. és az 1. mód dátum, az 5. bájt; a 0. mód NINCS MEG | `0x00450100`, `0x00450bd0` (U31, U32) |
| U25 | NINCS MEG (változatlan) | a négy `0x00987030` hívás a két üres-név ágban | `0x00987030` |
| U26 | NINCS MEG (változatlan) | K-másolás törzse | `0x00801915`-`0x00801bc4` |
| U27 | NINCS MEG (változatlan) | `M+0x64c` és `M+0x650` írása | `0x005e8a70` |
| U28 | LEZÁRVA (38.2.45 §1) | a kulcs NÉV: a tömbindex után a `0x004dca40` név szerinti keresése | `0x004dca40`, `0x004406f0` (kész) |
| U29 | RÉSZBEN (38.2.45 §2) | a `[X+0x1034]` CThumbDB írója (`0x00402f90`) LEZÁRVA; L írója U36 | `0x00402f90` (kész), `0x00415790` |
| U30 | RÉSZBEN (38.2.45 §4) | a G-szerep LEZÁRVA; a táblák feltöltése NINCS MEG | `0x004b94a0` (kész), U37, U38 |
| U31 | RÉSZBEN (38.2.45 §5) | a dekompilált algoritmus megvan; a jelentés és a bemenet NINCS MEG | `0x00450100` (kész), U39 |
| U32 | NINCS MEG (változatlan) | az 1. mód összesítője | `0x00450bd0` belső ága |
| U33 | RÉSZBEN (38.2.45 §3) | az 1, 2, 3 írások CÁFOLVA mint mód; az Időrend `L+0xd8` értéke NINCS MEG | `0x0054c4b0` hívóhelyei, U36 |
| U34 | NINCS MEG (változatlan) | az OLEAUT32 184. sorszám neve (Windows-os `oleaut32.dll` kell) | IAT `0x00c405c8` |
| U35 (új) | RÉSZBEN (38.2.45 §1.4) | a név forrása: a regisztráló a rekord `[ebx+5]` szövegmezőjét viszi; a 0xc80d68 literál tartalma és az `ebx` rekord típusa NINCS MEG | adat-olvasás `0x00c80d68`; `0x00985ff0`, `0x004941f0` |
| U36 (új) | NINCS MEG | `L = [P+0xc4]` írói; a `P` a `0x008018a0` `this+0x2f4` mezője | pásztázás a `+0xc4` írásaira; `[this+0x2f4]` írói |
| U37 (új) | NINCS MEG; ⚠️ **HELYESBÍTVE (38.2.46 §2.1):** a `0x004a6dc0` zároló, nem feltöltő | a G-táblák (`[G+0x1c]`, `[G+0x18]`, `[G+0xc]`) feltöltése a `0x004b94a0` 637. sora előtt | `0x004a6dc0` (zároló) |
| U38 (új) | NINCS MEG | a `0x004baaa0` rendező törzse (a `0x004b94a0` 665. sora) | `0x004baaa0` |
| U39 (új) | NINCS MEG | a `0x00450100` bemenete: a `0x004502e0` helyi objektumának tartalma; a `0x0049cd60` sorrendje | `0x0049cd60`, `0x004502e0` |
| U40 (új) | NINCS MEG | a keresőlista elemei (képek vagy albumok) és az író | `0x004db4f0`, `0x004db720` (az album-sorrend.md 2.1 szerint, a kötegen kívül) |

**Nyitott kérdések mérlege (38.2.45):** 40 tétel · 5 lezárva · 14 részben · 21 nincs meg.

#### 38.2.45 Az Időrend bináris feltárása, 28. kör: a kulcs neve, a névkereső, az `L+0xd8` írói és az összesítők (#5401, 2026-10-21)

**Válasz röviden.**
1. **Q1, a kulcs (U28): LEZÁRVA.** A kulcs NÉV. A kattintott elem kulcsa egy index a névtömbbe (`L+0xb48`). Az ott talált szöveget a `0x004dca40` keresi meg a `CIndexer` táblában (`L+0x68`), `_stricmp` összehasonlítással. Név-fajta: az album-rekord szövegmezője (U35, részben). Hogy mely képek tartoznak hozzá: **NINCS MEG** (U40).
2. **Q2, a `0x00402f90` (U29): RÉSZBEN.** Ez a függvény hozza létre a `[X+0x1034]` adatbázist (CThumbDB). Az `L = [P+0xc4]` íróját nem találtam meg: a függvény nem ír `+0xc4`-et (U36).
3. **Q2b, a `0x0054bad0` (U33): RÉSZBEN, az 1, 2, 3 írások CÁFOLVA mint mód.** Ez egy lejátszási eseményhurok, az 1, 2, 3 értékek eseménykódok. Az Időrend módja az `L+0xd8`-ban: **NINCS MEG**.
4. **Q3, a `0x004b94a0` (U30): RÉSZBEN.** A sorokat szűri, a `0x004baaa0`-val rendezi, és a rendezett sorindexeket adja a kimenetbe. A G-táblák feltöltése (U37): **NINCS MEG**.
5. **Q3b, a `0x00450100` (U31): RÉSZBEN.** Dekompiláció szerint az első legalább egy napos dátumugrás előtti dátumot adja vissza. A bemenete és a jelentése: **NINCS MEG** (U39).
6. **Q4, a felhasználó szemével:** az útvonal LEZÁRVA, a képhalmaz **NINCS MEG** (§6).
7. **Q5, a 38.2.44 listája:** frissítve a 38.2.44 §9-ben: 5 lezárva, 14 részben, 21 nincs meg.

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-28.txt` öt címe: `0x004dca40`, `0x00402f90`, `0x0054bad0`, `0x004b94a0`, `0x00450100`. Asm-ellenőrzés `pe_dis.cdis`-szel: a `0x004dca40` eleje és a hash-hívás; a `0x004406f0` hívóhelye (`0x004408ef`) és alapértelmezett ága (`0x004407b6`); a `0x0054bad0` öt hívóhelye; a `0x004502e0` hívóhelye (`0x0045070e`); a regisztráló (`0x004158d5`-`0x004158f4`). Csak dekompilációból igazolt: a `0x00402f90` és a `0x004b94a0` törzse, a `0x00450100` farok-ciklusa, a `0x0049cd60` és a `0x004a6dc0` (utóbbi a kötegen kívül). A sorszámok (637., 660-735., 665. sor) a bemeneti `2026-10-21-idorend-28.txt` fájl sorai. A `pe_dis.cdis(cím, N)` második paramétere bájtszám, nem utasításszám. A kezdőcímet utasítás-határra kell igazítani, különben hamis utasítás-sorokat ad. Ideiglenes fájl nem készült, `.bt/` nem jött létre. Kódot nem módosítottam, ezért CI-őr nem futott.

**Bizonyítottsági fok.** Az asm-ből igazolt állítás erős. A dekompilációból jövő állítást jelölöm.

**§1. Q1: a kulcs (U28).**

**§1.1 A névkereső (`0x004dca40`, asm).** A `this` (EAX) a hívóhelyen `S+0x20`, ahol `S = L+0x48` (lásd §1.2). Ezért a keresőobjektum `L+0x68`. Ez egyezik az album-sorrend.md 2.1 szakaszának „db+0x68” jelölésével, ha `db = L`. A függvény:
- nullázza az `O1+0x5c` és az `O1+0x64` mezőt (`0x004dca56`-`0x004dca5a`);
- zárolja az `O1+0x28` kritikus szakaszt, majd a keresőobjektum zárját (lock-minta: tulajdonos-szál a `+0x20`, számláló a `+0x24`, kritikus szakasz a `+0x28`);
- a vödör indexe `H(név) mod [this+0x58]`. A `0x004de1a0` hívásakor `EAX = &név` (`0x004dcab6`: `lea eax,[esp+0x18]`), a veremben a modulus `[this+0x58]` (`0x004dcab5`: `push ecx`). A dekompilált törzs ezt nem mutatja, mert az EAX-ban átadott bemenetet nem írja ki. Az első olvasat, hogy a vödör csak a tábla mezőjétől függ, téves. A `0x004de1a0` sztring-hash; a ciklus törzsét nem olvastam végig;
- a vödör feje `[[this+0x60] + index*4]` (`0x004dcabf`);
- a lánc: `[csomópont+0]` a következő elem, `[csomópont+4]` a kulcs-sztring mutatója. A `call 0x00bf697a` (`_stricmp`) hasonlítja: `_stricmp(csomópont.kulcs, név)` (`0x004dcacf`);
- találatnál `O1+0x5c = this`, `O1+0x60 = &csomópont[1]` (a kulcs mezője), `O1+0x64 = &csomópont[2]` (az érték mezője) (`0x004dcb05`-`0x004dcb21`);
- visszatérési érték mindig 0 (`ret 8`, `0x004dcb02`).

**§1.2 A kulcs útja a `0x004406f0`-ban (asm).** A függvény `this`-e `S = L+0x48`, mert az `ECX` belépéskor ez (`0x00440702`: `mov esi,ecx`; 38.2.44 §1.1).
- `key == -1` esetén -1 (`0x00440704`);
- a keresőobjektum zárja: `S+0x20` (`0x0044070a`-`0x00440748`). Ezután a második objektum (`S+0xaa8`, azaz `L+0xaf0`) zárja (`0x00440753`-`0x00440794`);
- a bejegyzés-tömb: `[S+0xaa8+0x58]` (azaz `L+0xb48`), darabszám `[obj+0x4c] >> 1`, adatmutató `[obj+0x48]`. Ha `key < darabszám`, a cella `adat + key*4`. Különben a cella `S+0xb04` (azaz `L+0xb4c`, az alapértelmezett bejegyzés) (`0x004407a1`-`0x004407b9`; `0x004407b6`: `lea edx,[esi+0x5c]`);
- ha a cella mutatója 0, vagy a `bejegyzés+4` sztring üres, nincs keresés (`0x004407c1`, `0x0044081a`);
- a keresés: `0x004dca40(név = bejegyzés+4, O1)`, `EAX = S+0x20` (`0x004408ed`-`0x004408ef`).

**§1.3 Ebből a kulcs NÉV (U28, LEZÁRVA).** A kulcs egész szám, az `L+0xb48` tömb indexe. A tömb elemei bejegyzések, ezek `+4` mezője a név (sztring). A név keresése a `CIndexer` táblában (`L+0x68`) történik. A kattintás oldalán a kulcs forrása (`[this+0x50c]`, 38.2.43 §1.1) nincs újra mérve. Ez a kör csak azt mérte, hogy a `0x004406f0` tömbindexként használja.

**§1.4 Melyik név (részben, U35).** A regisztráló (`0x004158d5`-`0x004158f4`, a `0x00415790` CThumbDB konstruktor belsejében):
- `push 0xc80d68` (literál), `lea eax,[ebx+5]` (az `ebx` rekord szövegmezője), `call 0x00985ff0` (sztring-építés);
- `lea eax,[ebp+0xaf0]` (`EAX = L+0xaf0`), a verembe a sztring és `L+0x988`, `call 0x004941f0` (a név felvétele).
- Az album-sorrend.md 2.1 szerint ez az album-rekord token-je. A 0xc80d68 literál tartalma és az `ebx` rekord típusa ebben a körben nem lett kiolvasva. Ezért: az album-token a valószínű név-fajta. A címke- vagy mappa-ág: **NINCS MEG**.

**§1.5 Mely képek: NINCS MEG (U40).** A találati lista a csomópont harmadik mezőjénél van: `O1+0x64` a lista fejléce, `[fejléc+0]` az adatmutató, `[fejléc+4] >> 1` a darabszám (38.2.43 §1.3; ezt nem mértem újra). Az elemek típusa, és az a függvény, amely a névhez elemeket ír, nincs a kötegben.

**§2. Q2: a `0x00402f90` (U29).**
- Dekompilációból (a hívás és a tárolás címe 38.2.44 §1.4 szerint, ezt ebben a körben nem mértem újra): `[X+0x1034] = 0x00415790(...)`, azaz CThumbDB objektum (0x34b0 bájt). Az `X` a függvény `this`-e (`EBX`).
- A függvény további objektumokat hoz létre: `[X+0x1030]` (0x448 bájt), `[X+0x1038]`, `[X+0x1040]` (0x560 bájt), `[X+0x1044]` (`FolderCache`, és `DAT_00d67690`), `[X+0x103c]` (`DBLoader`, 0x8c bájt).
- Feltölti az album-csoportokat. Név szerint (`0x00985ff0` sztring, `0x00451a80` felvétel): „From Hello”, „Downloaded Albums”, „Web Albums”, „Recent Activity”. Kóddal (`0x004527d0`): „Labels” (100), „Projects (internal)” (90), „Folders on Disk” (20), „Web Albums” (9), „Web Drive” (8), „Exported Pictures” (7), „Other Stuff” (6), „Hidden Folders” (1). Dekompiláció.
- A `0x0041ee10(db, "#db3\\", ...)` hívás a `#db3\` útvonallal. Ha nem nulla, a `0x00402d60` következik. Célja NINCS MEG.
- Nem ír `+0xc4`-et (a törzsben nincs ilyen írás, dekompiláció). `L` írója (`[P+0xc4]`): **NINCS MEG** (U36).

**§3. Q2b: a `0x0054bad0` (U33).**
- A `this` az EAX. A törzs a `[this+0x5c]` objektum vt+0x20 hívásával kér eseményt (négy argumentum: esemény-kód, két paraméter, időtúllépés 0). Az eredményt a `[this+0xd8]` mezőbe írja (dekompiláció).
- `1` esetén visszatér `0xf4242`-vel. `2` esetén lezárás (vt+0x20 a `this`-en). `3` esetén `EC_ERRORABORT %x` hibanapló, és visszatér 0 (dekompiláció).
- A `0x008295ba` hívóhely a `0xf4242` értéket figyeli: `cmp ebx,0xf4242` a `0x008295ac` címen, `je` a `0x008295b2` címen (asm). Ez az eseményhurok-értelmezéssel egyezik.
- A vt+0x20 négy argumentumos hívása és az `EC_ERRORABORT` szöveg a DirectShow `IMediaEvent::GetEvent` mintáját mutatja. Az eseménykódok a DirectShow SDK szerint: 1 = EC_COMPLETE, 2 = EC_USERABORT, 3 = EC_ERRORABORT. Ezek nem a binárisból olvasott értékek.
- Hívóhelyek és `this`-ük (asm): `0x00467b06` (veremobjektum, `lea eax,[esp+0xd8]`); `0x0054b063` és `0x0054b079` (`mov eax,esi`, a `0x0054b010` `esi`-je); `0x0054c4bd` (`mov eax,esi`, a `0x0054c4b0` `esi`-je; ez előtte `[esi+0xd8] = 0`-t ír); `0x008295ba` (`lea eax,[edi+0x90]`).
- Következtetés: az 1, 2, 3 írások nem az Időrend módjai. ⚠️ **HELYESBÍTVE:** 38.2.44 §3.8.
- Az `L+0xd8` Időrend-módja: **NINCS MEG** (U33). Hogy az `L` a fenti hívók közül valamelyik `this`-e, nem igazolt.

**§4. Q3: a `0x004b94a0` (U30).**
- A `this` a `P`, a zár a `+0x20` mezőn van, `L = [P+0xc4]` (dekompiláció).
- Ha `L == 0`, visszatér 4-gyel (dekompiláció).
- A sorok darabszáma `FUN_0045fbe0()`. Soronként: `FUN_004461a0(sor)` (szűrő), majd `(L+0x48 vt+0x28)(sor, &kimenet)`, és a `0` értékű visszatérés az elfogadás. Ezután `FUN_00987030(0)` a második feltétel. Az elfogadott sor indexe a helyi listába kerül (`local_3c`).
- Ellenőrzés: három tábla darabszáma (`[iStack_4+0x58]`, `[iStack_8+0x58]`, `[iStack_14+0x58]`) legalább a sorok száma. A törzsben ezek a helyi változók nincsenek beállítva, a dekompiláció ezt nem tudja. A feltöltő a `0x004a6dc0` (637. sor) lehet. Ez **NINCS MEG** (U37).
- Sikeres ellenőrzésnél `DAT_00d67678 = &local_20` (`G`), a `0x004baaa0` rendez, a kimeneti lista a rendezett sorindexeket kapja, és visszatér 0 (dekompiláció, 660-735. sor).
- Sikertelen ellenőrzésnél -1 (`0xffffffff`).
- A rendező összehasonlító (`0x004a7890`, 38.2.43 §3) kulcsa: bájt-jelző (`G+8`), a sor neve (`0x004a71e0`, kis-nagybetű nem számít), a módfüggő szám (`L+0xd8`), a második név, és a csökkenő sorrend (`L+0x165`).
- U30 RÉSZBEN: a szerep igazolt; a G-táblák feltöltése **NINCS MEG** (U37, U38).

**§5. Q3b: a `0x00450100` (U31).**
- Dekompiláció: `param_1` egy dátum-tömb tulajdonosa (`*param_1` a double-tömb). A `0x0049cd60(&local_14)` a rendezett sorindex-listát adja (`local_14` mutató, a darabszám `local_c` vagy `local_10`).
- A ciklus a rendezett lista végétől visszafelé halad. Ha két egymás utáni dátum különbsége legalább 1 (1 nap, OLE-dátum), a visszatérés az előző dátum. Ha nincs ilyen ugrás, a visszatérés az utolsó vizsgált dátum.
- A farok-ciklus (`0 < iVar6`) a 0. pozíciót nem vizsgálja (dekompiláció, asm nincs).
- Hívóhely: `0x0045070e`, a `0x004502e0`-ban. Az argumentum egy verembeli helyi objektum (`lea edx,[esp+0x10]`, `push edx`, asm). Hogy ez a teljes lista-e, és mi van benne: **NINCS MEG** (U39).
- A 4. mód soronkénti értéke (`0x004502e0`, 38.2.44 §3.1): hogy minden sorra ugyanez az összesítő jön-e: **NINCS MEG** (U39).

**§6. Q4: a felhasználó szemével.** Az útvonal igazolt:
1. A kattintás a kulcsot a `[this+0x50c]` mezőbe írja (38.2.43 §1.1).
2. A `0x004b0190` zárolja `L`-t, és meghívja az `L+0x48` (CThumbDB) vt+0x2c slotját: `0x004406f0` (38.2.44 §1).
3. A kulcs a `L+0xb48` névtömb indexe; a név a bejegyzés `+4` sztringje (§1.2).
4. A név szerint keres a `L+0x68` táblában (`0x004dca40`, §1.1).
5. A találati lista a csomópontban van (§1.5).
6. A K-másolás (`0x00801915`-`0x00801bc4`, U26), majd a kártyák (`0x008014d0`, U4, U14, U20).

Egyszerű mondatok: Kattintáskor a program a kattintott elem kulcsát a névtömb indexének veszi, és kivesz belőle egy nevet. Ezt a nevet a keresőtáblában megkeresi, és a találathoz tartozó lista elemeiből épül a kártyasor. Hogy ezek az elemek képek, albumok vagy más elemek, és melyik képhalmaz jelenik meg: **NINCS MEG**.

Hiányzó címek: `0x00801915`-`0x00801bc4` (U26); a keresőlista elemeinek írója (U40; az album-sorrend.md 2.1 szerint `0x004db4f0` írja és `0x004db720` olvassa, ez a kötegen kívül van); `0x008014d0` és az `obj2.vt[0]` célja (U4, U20).

**§7. Amit KIZÁRTAM (38.2.45).**
- „A `0x004dca40` tölti ki a bejegyzést” (38.2.44 §1.5): **CÁFOLVA**. A függvény keres.
- „A `0x004dca40` vödörválasztása csak a tábla mezőjétől függ” (a dekompilált olvasat): **CÁFOLVA**. Az EAX-ban a név van (§1.1).
- „Az 1, 2, 3 írások az Időrend módjai” (38.2.44 §3.8): **CÁFOLVA** (§3).
- „A `0x00450100` a teljes listát összegzi”: **NEM IGAZOLT** (§5).

**§8. Ghidra-címek a következő körhöz.**
- `0x004a6dc0` (U37): a G-táblák feltöltése, a `0x004b94a0` 637. sora. ⚠️ **HELYESBÍTVE (38.2.46 §2.1):** ez zároló, nem feltöltő.
- `0x004baaa0` (U38): a rendező törzse, a `0x004b94a0` 665. sora.
- `0x0049cd60` és `0x004502e0` (U39): a rendezett sorindex-lista szolgáltatója, és a helyi dátum-objektum feltöltése a `0x0045070e` hívás előtt.
- `0x00801915`-`0x00801bc4` (U26): a K-másolás törzse.
- `0x004db4f0`, `0x004db720` (U40): a keresőlista írója és olvasója (az album-sorrend.md 2.1 szerint).
- A `0x0054c4b0` hívóhelyei (U33): melyik objektum `this`-e, és van-e köze az `L`-hez.
- `[P+0xc4]` íróinak pásztázása, `P = [this+0x2f4]` a `0x008018a0` kattintásban (U36).
- A `0xc80d68` literál tartalma: adat-olvasás, nem Ghidra (U35).

**Helyesbítések a korábbi szakaszokban (38.2.45).**
1. 38.2.44 §1.5: a „0x004dca40 tölti ki a bejegyzést” mondat téves, javítva (§1.1).
2. 38.2.44 §3.8: az 1, 2, 3 értékű írások nem mód-írások, javítva (§3).

#### 38.2.46 Az Időrend bináris feltárása, 29. kör: a név-tábla, a rendezők, a mód-író és a sor-érték (#5401, 2026-10-21)

**Válasz röviden.**
1. **Q1, a név-tábla és a képhalmaz (U40): RÉSZBEN.** A név-tábla egy `CIndexer` (`L+0x68`). A `0x004db4f0` a `wordhash.dat` fájlba menti, a `0x004db720` onnan tölti be. A listák elemei 4 bájtos egész azonosítók. A binárisban három kulcs-előtag van: `]album:`, `]facealbum:%d` és `]expeople:%d`. Ez albumokra és személyekre utal. Hogy egy bejegyzéshez mely képek tartoznak: **NINCS MEG**. Ghidra-kör kell: `0x004db180` és `0x004db300` (a lista-író függvények).
2. **Q2, a G-táblák (U37): a feltételezés CÁFOLVA.** A `0x004a6dc0` nem tölt fel táblát, hanem zárol: az `L` objektumot és hét alobjektumát. A G-táblák feltöltése: **NINCS MEG**. Ghidra-kör kell: a `0x004b94a0` 637. sorának előtti hívások.
   **Q2b, a rendezés (U38): LEZÁRVA.** A `0x004baaa0` egyesítő rendezés 4 bájtos elemekre. A kulcsot a `0x004a7890` hasonlító adja.
3. **Q3, a 4. mód bemenete (U39): RÉSZBEN.** A `0x0049cd60` növekvő rendezés egy index-listán, dupla kulcs szerint. A `0x004502e0` soronként: a sor listájának minden eleméhez egy FILETIME-ot vesz, azt OLE-dátummá alakítja (`0x0098b650`), és a dátumok tömbjét a `0x00450100` összesítőnek adja. Ennek kimenete a sor értéke. A sor-objektum azonossága (`L`?): **NINCS MEG**.
4. **Q4, a mód-érték (`L+0xd8`, U33): RÉSZBEN.** A mód-értéket a `0x004b07c0` írja: `[objektum+0xd8] = edx`, `[objektum+0x165] = cl`. Két hívója van: `0x005d9cc0` (mód 2 és mód 0, fix számmal) és `0x005d30f0` (az `edx` forrása: **NINCS MEG**). A `0x0054c4b0` nem mód-író, saját eseménykódot ír. Hogy a mód-író objektum az `L`: **NINCS MEG** (U36).
5. **Q5, a felhasználó szemével: NINCS MEG.** Ezért nincs ilyen szakasz. Hiányzó cím: a képhalmaz (`0x004db180`, `0x004db300`) és a kártyák másolása (`0x00801915`-`0x00801bc4`, U26).

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-29.txt` hét címe: `0x004a6dc0`, `0x004baaa0`, `0x0049cd60`, `0x004502e0`, `0x0054c4b0`, `0x004db4f0`, `0x004db720`. Az asm a `pe_dis.cdis`-szel készült. A hívókat, a stringeket, a vtáblát és a függvényméreteket a bináris index adta. Az index a hívásokat függvény-szinten adja, ezért a hívóhelyeket asm-ben kerestem meg. A vtábla-hívások nem látszanak az indexből. Ideiglenes fájl nem készült, a `.bt/` nem jött létre. Kódot nem módosítottam, ezért a CI-őrök nem futottak.

**Bizonyítottsági fok.** Az asm-ből igazolt állítás erős. A dekompilációból jövő állítást jelölöm. A `0x00c7ccf8` konstans értékét olvasással ellenőriztem.

**§1. Q1: a név-tábla és a képhalmaz (U40).**

**§1.1 A tábla és a mentés.**
- A `CIndexer::vftable` a `0x00c85fc4` címen hat slotot tartalmaz (`data_symbols`: `pointer[6]`). A slotok: `0x004de190`, `0x004db4f0`, `0x004db720`, `0x00a4a070`, `0x00a4a080`, `0x00a4a090` (`rtti`). A `0x00c85fc8` és a `0x00c85fcc` adat-hivatkozásai a `0x004db4f0`-ra és a `0x004db720`-ra mutatnak. Így a `0x004db4f0` a vt+0x04, a `0x004db720` a vt+0x08 slot.
- `0x004db4f0` (553 bájt, mentés, dekompiláció). Megnyitja a `wordhash.dat` fájlt (`0x009917f0`), kiír egy 4 bájtos értéket (`_DAT_00d678e0`), majd a `this+0xc` szótárat a `0x00704500` írja ki. A zárolása a 38.2.45-ben leírt mintát követi (tulajdonos-szál, számláló, kritikus szakasz).
- `0x004db720` (449 bájt, betöltés, dekompiláció). A `this+0xc` szótárat a `0x007046e0` olvassa be. Három hibaüzenete van: `Inconsistent dictionary.PoolSize()`, `wordhash.dat file: excess data`, `wordhash.dat: incorrect entity count`. Ellenőrzi, hogy a `this+0x20` értéke `0x10000`, és hogy a fájlban megadott darabszám legalább a legnagyobb listaelem + 1. Ebből következik: a listák elemei egész azonosítók, a fájl pedig tárolja az azonosítók darabszámát.

**§1.2 A kulcs és az előtagok.**
- A `0x004dca40` keresőt az indexben 17 függvény hívja. Köztük a `0x004406f0` (a kulcs útja, 38.2.45 §1.2), és a CIndexer két belső függvénye: `0x004db180` (378 bájt) és `0x004db300` (487 bájt).
- Kulcs-előtagok a bináris stringjeiben:
  - `]album:` (`0x00c811c4`): hívói `0x0041c340`, `0x00440bc0`, `0x004a51f0`, `0x004aca00`, `0x004b94a0`.
  - `]facealbum:%d` (`0x00c810b4`): hívói `0x00419d10`, `0x0047d2b0`, `0x0055d120`.
  - `]expeople:%d`: hívói `0x00449a30` és `0x0048c570`.
  - A `0x004a7890` és a `0x004b94a0` a `]album` és a `]facealbum` szöveget is használja.
- Az album-kulcs jelenléte igazolt. Hogy az előtag a kulcsba íródik, vagy csak vizsgálatra szolgál: **NINCS MEG**.

**§1.3 A név forrása (U35).**
- A `0x00c80d68` címen a `token` szó áll (`string_xrefs`; hívói `0x00415790`, `0x009788a0`, `0x00978e40`). A `0x00415790` (CThumbDB konstruktor) ezt tolja a verembe, utána a rekord `+5` szövegmezőjét (`lea eax,[ebx+5]`), majd a `0x00985ff0` sztring-építést hívja. Az eredményt a `0x004941f0` veszi fel az `L+0xaf0` objektumba (38.2.45 §1.4).
- Az album-sorrend.md szerint ez az album-rekord token-je. A rekord típusa és a `+5` mező tartalma: **NINCS MEG**.

**§1.4 Mely képek (U40).**
- Az elemek egész azonosítók. Hogy képek vagy albumok azonosítói: **NINCS MEG**.
- Ghidra-kör kell: `0x004db180` (hívói: `0x00449a00`, `0x00449a30`, `0x00474630`, `0x004755d0`, `0x00483cb0`) és `0x004db300` (hívói: `0x0048c570`, `0x007d6db0`). Mindkettő hívja a `0x004dca40`-et. ⚠️ **HELYESBÍTVE (38.2.47 §1):** egyik sem ír listába. A `0x004db180` csak olvas, a `0x004db300` kimásolja a listát. Melyik függvény ír azonosítót a listába, és milyen azonosítót: **NINCS MEG** (U42, U40).

**§2. Q2: a G-táblák (U37) és a rendezés (U38).**

**§2.1 A `0x004a6dc0` zároló (U37).**
- Hívóhelyek: `0x004b8ee0` (`0x004b90fd`) és `0x004b94a0` (`0x004b96cd`). Mindkettő előtt `mov eax,[esi+0xc4]` áll (`0x004b96c3`, `0x004b90f3`). Mindkét hívásban a `this` tehát a `[objektum+0xc4]`. A `0x004b94a0`-ban a `P` az objektum, így a `this` ott az `L = [P+0xc4]`.
- A függvény egy nyolc mutatós őr-struktúrát tölt ki, és zárolja a mutatott objektumokat: `L`, `L+0x8c8`, `L+0x928`, `L+0xbb0`, `L+0xb50`, `L+0xc10`, `L+0xc78`, `L+0xaf0`. A dekompilátum `int*` számolásban adja a mezőket. A bájt-címek: `0x232` = `+0x8c8`, `0x24a` = `+0x928`, `0x2d4` = `+0xb50`, `0x2ec` = `+0xbb0`, `700` = `+0xaf0`, `0x304` = `+0xc10`, `0x31e` = `+0xc78`.
- Minden zárolás ugyanazt a mintát követi: tulajdonos-szál a `+0x20`, számláló a `+0x24`, kritikus szakasz a `+0x28` mezőben. A törzsében nincs adatírás, csak zárolás (dekompiláció). Ez zároló, nem feltöltő.
- A G-táblák feltöltője: **NINCS MEG**. Ghidra-kör kell: a `0x004b94a0` 637. sorának hívásai, és az `L+0x8c8`, `L+0x928`, `L+0xb50`, `L+0xbb0`, `L+0xc10`, `L+0xc78` objektumok írói.

**§2.2 A `0x004baaa0` rendezés (U38).**
- Egyesítő rendezés (alulról felfelé). Az elemek 4 bájtos értékek, a darabszám a lista méretének fele. Előtte egy ellenőrző hívás fut (`0x004bb0e0`).
- Két elemet így hasonlít: `0x004a7890(param_1[3], második, első)`. Ha az eredmény negatív, a két elem cserélődik. Az egyesítést a `0x004bb040` végzi, a foglalás a `0x0097c5d0`, a felszabadítás a `0x0097caf0`.
- Hívói: `0x004b8ee0` (`0x004b916b`) és `0x004b94a0` (`0x004b974a`).
- Mi szerint rendez: a `0x004a7890` kulcsa szerint (38.2.43 §3, ebben a körben nem mérve): bájt-jelző (`G+8`), a sor neve (`0x004a71e0`), a mód-szám (`L+0xd8`), a második név, és a csökkenő jelző (`L+0x165`). ⚠️ **PONTOSÍTVA (38.2.47 névhasználat):** itt az `L` a rendező objektum (`obj`), a 38.2.44 jelölése.
- LEZÁRVA: a rendező törzse és a hasonlító szerepe igazolt. A kulcs tartalma a 38.2.43-ból van.

**§3. Q3: a 4. mód bemenete (U39).**

**§3.1 A `0x0049cd60` rendező.**
- Dekompiláció alapján: alulról felfelé egyesítő rendezés 4 bájtos indexekre. A kulcs egy dupla-tömb: `*(double*)(*(int*)param_1[3] + index*8)`. Növekvő sorrend. Egyenlő kulcsnál a régi sorrend marad (stabil).
- 14 hívóhely: `0x00450122` (a `0x00450100`-ban), `0x007fc4f2` (a `0x007fc4c0`-ban), 8 hely a `0x0088ed40`-ban, 4 hely a `0x00894d50`-ben.

**§3.2 A `0x004502e0` soronkénti érték.**
- Az első paraméter (`param_1`, a belépéskor `[esp+0xf4]`) egy objektum, és az eredmény ide íródik: `*param_1` (dekompiláció). Az objektum `+0x48` címén beágyazott CThumbDB van, mert az asm ott látja a vtábla-mutatót.
- Első lépés (asm: `0x00450305`-`0x00450312`): a CThumbDB vt+0x2c hívása a sor kulcsával. Ez a `0x004406f0` (38.2.44 §1). Ez adja a sor listáját, a darabszám a méret fele.
- Második lépés, ciklus minden elemre (asm: `0x00450618`-`0x00450639`). A ciklus indexe az `edi` regiszterben van (a hurok elejét nem néztem végig).
  - `eax = [objektum+0x4e8] + 4*edi` (a tömb megfelelő eleme),
  - ha ez a mutató nulla, `eax = objektum+0x4f0`, különben `eax` maga a mutató,
  - `eax += 4`, majd `call 0x0098b650`.
  Vagyis a FILETIME a rekord `+4` mezőjéből jön, vagy a fix `objektum+0x4f4` mezőből, ha a mutató nulla.
- Harmadik lépés: a `0x0098b650` (87 bájt) FILETIME-ot alakít át. Először egy két paraméteres Windows-hívás (`0x00c403f0`) helyi FILETIME-ot ír, majd egy három paraméteres hívás (`0x00c403e8`), végül a `0x00c405c8` import ad egy double-t. Az alakja (SYSTEMTIME és double kimenet) OLE-dátum átalakítóra utal, a neve U34. Ha a FILETIME mindkét szava nulla, a visszatérés a `0x00c7ccf8` címen álló double: olvasva **949998.0**. Hogy ez mit jelent: **NINCS MEG**.
- Negyedik lépés: a dátumok tömbje a `0x00450100` bemenete (`lea edx,[esp+0x10]` a `0x00450709` címen). A `[esp+0x10]` a mutató, a `[esp+0x14]` a méret (a darabszám kétszerese). A `0x00450100` kimenete a sor értéke (`0x0045071a`).
- Hívók: a `0x004a7890` két helyről hívja (`0x004a7e3c`, `0x004a7e4e`), vagyis a hasonlító két sorra külön kiszámolja az értéket.

**§3.3 Mi NINCS MEG (U39).**
- A `0x004a7890` által átadott objektum azonossága (az `L`?): **NINCS MEG**.
- A `[objektum+0x4e8]` tömb írója és a `[objektum+0x4f4]` alapértelmezett FILETIME írója: **NINCS MEG**.
- A `0x00c403f0`, `0x00c403e8` importok neve: az index nem adja, **NINCS MEG**.
- A `0x00450100` összesítő neve (medián, minimum vagy más): **NINCS MEG** (U31).

**§4. Q4: a mód-író, a hívói és az `L+0xd8` (U33).**

**§4.1 A `0x004b07c0` mód-író** (75 bájt, `ret 4`, asm).
- Bemenet: az első verembeli argumentum az objektum (`[esp+4]`). A `edx` a mód, a `cl` a csökkenő jelző. Mindkettőt a hívó adja.
- Lépések: ha az `[objektum+0xd8]` és az `[objektum+0x165]` már egyezik a bemenettel, a visszatérés `0xf4242` (nincs változás). Különben `[objektum+0x165] = cl`, majd `[objektum+0xd8] = edx` (`0x004b07e2`). Ha a `[0xd67668]` globális objektum `+0x102c` mezője nem nulla, meghívja a `0x006dc4c0`-t (neve és hatása: **NINCS MEG**).
- Tehát az `L+0xd8` mód-értéke és az `L+0x165` csökkenő jelzője ettől a függvénytől jön, ha a mutatott objektum az `L`. Ez egyezik a 38.2.43 §3 szerinti hasonlító kulcsával. ⚠️ **PONTOSÍTVA (38.2.47 §3):** a mód értékét nem a `0x004b07c0` számolja. A hívó parancs-ága adja konstansként (`0x005cb990`: 0, 1, 2, 3, 5; a 6. ágban a régi mód marad, az irány fordul meg).
- A 38.2.44 §3.8 már „register-íróként" nevezte meg. Most az asm mutatja, hogy mindkét mezőt ő írja.

**§4.2 A hívók.**
- `0x005d9cc0` (7153 bájt, a `thumbui/...` parancsok kezelője). Két hívóhely: `0x005db20c` (előtte `mov edx, 2`, azaz mód 2) és `0x005db26f` (előtte `xor edx, edx`, azaz mód 0). A `cl` a `[objektum+0x165]`-ből jön, az objektum a `[ebx+0x2c0]`. A két hívóhely előtt egy táblabejárás áll (`cmp eax, 0xc96600`, illetve `cmp eax, 0xc96614`). A tábla tartalma: **NINCS MEG**.
- `0x005d30f0` (171 bájt). Ha a `[edi+0xea0]` nulla, a visszatérés `4`. Különben a `[edi+0x24c]` számláló nő, a `[edi+0x250]` nullázódik, és a `0x004b07c0` hívódik a `[edi+0x2c0]` objektummal. Az `edx` és a `cl` ebben a részben nincs beállítva, a hívótól jön. Hívója az indexben: `0x005cb990`. Az `edx` forrása: **NINCS MEG**.

**§4.3 Amit kizártam a mód-írásról.**
- `0x0054c4b0` (`[esi+0xd8] = 0`, majd a `0x0054bad0` eseményhurok): a saját objektumának eseménykódja. Hívói: `0x0054c540` (`0x0054c59b`) és `0x00465fd0` (`0x00465fd3`). Nem mód-író.
- `0x006d2180` (5188 bájt): a `+0xd8` mezőbe a foglalás (`0x0097c810`) és a felszabadítás (`0x0097caf0`) eredménye kerül. Ez puffer-mutató, nem mód.
- A `mov [reg+0xd8], reg` bájt-keresés 132 találatot adott. Ebből sok hamis (rossz igazítás, SIB-bájtok). Ezeket nem néztem végig, ezért más íróról nincs döntés.

**§4.4 Az `[X+0x2c0]` és az `L`.** A `0x005d9cc0` és a `0x005d30f0` mód-hívása a `[X+0x2c0]` objektumot adja. ⚠️ **PONTOSÍTVA (38.2.47 §3.5):** a 38.2.44 `L` a mód-tartó (`obj`), a 38.2.46 `L` a CThumbDB-tartó (`[obj+0xc4]`). Hogy az `[X+0x2c0]` azonos-e a mód-tartóval: **NINCS MEG** (U36, U43). Ghidra-kör kell: a `0x005d9cc0` eleje (az `ebx` beállítása), a `0x005cb990` (az `edx` forrása), és a `[P+0xc4]` és a `[X+0x2c0]` összevetése.

**§5. Q5: a felhasználó szemével.** Nincs ilyen szakasz, mert a kérdés nem dőlt el. Hiányzó cím:
- a képhalmaz írója: `0x004db180` és `0x004db300` (U40),
- a kártyák másolása: `0x00801915`-`0x00801bc4` (U26),
- a G-tábla feltöltője: a `0x004b94a0` 637. sora előtt (U37).

Ami már áll: a kattintás a kulcsot a név-táblából keresi ki (38.2.45 §6), és a találat egész azonosítók listája. Hogy ezek képek vagy albumok azonosítói: **NINCS MEG**.

**§6. Helyesbítések a korábbi szakaszokban.**
1. A 38.2.45 §8 és a 38.2.44 §9 U37 sora azt írta, hogy a `0x004a6dc0` a G-táblák feltöltése. Ez téves: zároló (§2.1). ⚠️ HELYESBÍTVE a két helyen.

**§7. Amit KIZÁRTAM (38.2.46).**
- „A `0x004a6dc0` tölti a G-táblákat”: **CÁFOLVA** (§2.1).
- „A `0x0054c4b0` vagy a `0x0054bad0` írja az Időrend módját”: **CÁFOLVA** (§4.3).
- „A `0x006d2180` írja a `+0xd8` mód-mezőt”: **CÁFOLVA** (§4.3, puffer).
- „A `0x0049cd60` a 4. mód összesítője”: **CÁFOLVA**, ez rendező (§3.1).

**§8. Ghidra-címek a következő körhöz.**
- `0x004db180` és `0x004db300` (U40): a `0x004dca40` két belső hívója. ⚠️ **HELYESBÍTVE (38.2.47 §1):** nem írnak listát, ezért ez a cím nem lista-író. Lásd U42.
- `0x00449a00`, `0x00449a30`, `0x00474630`, `0x004755d0`, `0x00483cb0`, `0x0048c570`, `0x007d6db0`: a két belső függvény hívói. Ezek adják be az azonosítókat.
- `0x0041c340` (U40, U35): a `]album:` és a `]album` szövegek egyik hívója.
- `L+0x8c8`, `L+0x928`, `L+0xb50`, `L+0xbb0`, `L+0xc10`, `L+0xc78` (U37): a G-táblák feltöltője, a `0x004b94a0` 637. sora előtt.
- `0x00c7ccf8` (949998.0): a nulla FILETIME jelentése (U39).
- `0x00450100` (U31): a statisztika neve.
- `0x005cb990` (U33): a `0x005d30f0` hívója, az `edx` forrása.
- `0x005d9cc0` eleje (U36): az `ebx` és a `+0x2c0` mező azonossága az `L`-lel.
- `0x006dc4c0` (U33): a mód-író frissítése.
- `0x0054c540` (U33): a `0x0054c4b0` `esi` objektumának azonossága. Ez nem mód-író, csak a kontextus kell hozzá.

**§9. Nyitott lista (38.2.46), a 38.2.44 §9 helyett.**

Nyitott kérdések mérlege (38.2.46): 40 tétel · 6 lezárva · 16 részben · 18 nincs meg.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U1 | NINCS MEG (változatlan) | a `0x00a6aa00` teljes törzse | `0x00a6aa00` |
| U2 | RÉSZBEN (változatlan) | az obj2 osztálya és a vt+0 cél | `0x005e8a70`, `M+0x4c` vt+0 |
| U3 | RÉSZBEN (változatlan) | az `L` osztálya és írója még nincs igazolva | `0x00402f90` (kész), U36 |
| U4 | NINCS MEG (változatlan) | a `0x008014d0` vt+0 hívott függvénye | `0x008014d0` |
| U5 | NINCS MEG (változatlan) | a `[this+0x2ec]` olvasói | pásztázás |
| U6 | NINCS MEG (változatlan) | a `0x009aaae0` hívóhelyei | `0x009aaae0` |
| U7 | LEZÁRVA (38.2.41 §1) | a sorrekord `+0x14` írója | - |
| U8 | NINCS MEG (változatlan) | a `P' = [T+0x3a4]` írója | `0x007fa7f0` |
| U9 | LEZÁRVA (38.2.41 §2-3) | a kattintási ág | - |
| U10 | RÉSZBEN (változatlan) | a `0x004b8470` hívója és az `[L+0x148]` írói | `0x004b8ee0` |
| U11 | RÉSZBEN (változatlan) | az `L` osztálya, `+0xc == 2`, `jbe` | `0x004b29d0` |
| U12 | NINCS MEG (változatlan) | az EBP/EBX forrása a hívottakban | `0x004b2e10`, `0x004b3770`, `0x004b80d0` |
| U13 | RÉSZBEN (változatlan) | a `0x007fc010` | `0x007fc010` |
| U14 | RÉSZBEN (változatlan) | a `0x008014d0` törzse | `0x008014d0` |
| U15 | NINCS MEG (változatlan) | a startbutton vt+0x18 | `0x007fa7f0` |
| U16 | RÉSZBEN (38.2.46 §2.2, §3.1) | a rendezők és a szűrő szerepe igazolt; a G-táblák feltöltése NINCS MEG | `0x004b94a0`, `0x004baaa0`, `0x0049cd60`, U37 |
| U17 | NINCS MEG (változatlan) | a `0x004b8d00` | `0x004b8d00` |
| U18 | NINCS MEG (változatlan) | az `E` görbe | `0x005568e0` |
| U19 | NINCS MEG (változatlan) | a rekord-utólagos és a ciklus-utáni lépés | `0x007fa650`, `0x00604480` |
| U20 | NINCS MEG (változatlan) | a kártya-rekord építése | `0x007fa5b0` |
| U21 | LEZÁRVA (38.2.43 §2) | a `CSlice` konstruktor és a destruktor-lánc | `0x004133e0`, `0x00413490` |
| U22 | RÉSZBEN (38.2.45 §1.2) | a `0x004406f0` a vt+0x2c cél; a `[L+0x48]` vtábla `0x00c81fa4`-e még nincs újra igazolva | `0x00402f90`, U36 |
| U23 | LEZÁRVA a törzs (38.2.44 §2); a forrás U30 | a sor neve: két tábla-lépés, a cella név-objektumra mutat | `0x004a71e0` |
| U24 | RÉSZBEN (38.2.46 §3.2) | a 4. mód soronkénti értéke igazolt (FILETIME, OLE-dátum, `0x00450100`); az 1. és a 0. mód NINCS MEG | `0x004502e0`, `0x00450bd0` (U32) |
| U25 | NINCS MEG (változatlan) | a négy `0x00987030` hívás a két üres-név ágban | `0x00987030` |
| U26 | NINCS MEG (változatlan) | a K-másolás törzse | `0x00801915`-`0x00801bc4` |
| U27 | NINCS MEG (változatlan) | az `M+0x64c` és `M+0x650` írása | `0x005e8a70` |
| U28 | LEZÁRVA (38.2.45 §1) | a kulcs NÉV: a tömbindex után a `0x004dca40` név szerinti keresése | `0x004dca40`, `0x004406f0` |
| U29 | RÉSZBEN (38.2.45 §2) | a `[X+0x1034]` CThumbDB írója LEZÁRVA; az `L` írója U36 | `0x00402f90`, U36 |
| U30 | RÉSZBEN (38.2.45 §4) | a G-szerep LEZÁRVA; a táblák feltöltése NINCS MEG | `0x004b94a0`, U37 |
| U31 | RÉSZBEN (38.2.46 §3.2) | a bemenet igazolt (`0x004502e0`); a statisztika neve NINCS MEG | `0x00450100` |
| U32 | NINCS MEG (változatlan) | az 1. mód összesítője | `0x00450bd0` belső ága |
| U33 | RÉSZBEN (38.2.46 §4) | a mód-író a `0x004b07c0` (`edx` = mód); hívói `0x005d9cc0` (2 és 0) és `0x005d30f0` (az `edx` forrása NINCS MEG); az objektum azonossága U36 | `0x004b07c0`, `0x005cb990` |
| U34 | NINCS MEG (változatlan) | az OLEAUT32 184. sorszám neve (Windows-os `oleaut32.dll` kell) | IAT `0x00c405c8` |
| U35 | RÉSZBEN (38.2.46 §1.3) | a literál szövege `token`; a rekord `+5` mezőjének típusa és a név tartalma NINCS MEG | `0x00415790`, `0x00985ff0`, `0x004941f0` |
| U36 | NINCS MEG | az `L = [P+0xc4]` írói, és hogy a mód-író `[X+0x2c0]` objektuma az `L` | pásztázás; `0x005d9cc0` eleje; `0x005cb990` |
| U37 | NINCS MEG (feltételezés CÁFOLVA, 38.2.46 §2.1) | a G-táblák feltöltője; a `0x004a6dc0` zároló | `0x004b94a0` (637. sor előtt), `L+0x8c8`, `L+0x928`, `L+0xb50`, `L+0xbb0`, `L+0xc10`, `L+0xc78` |
| U38 | LEZÁRVA (38.2.46 §2.2) | egyesítő rendezés 4 bájtos elemekre; a kulcsot a `0x004a7890` hasonlító adja | `0x004baaa0`, `0x004a7890` |
| U39 | RÉSZBEN (38.2.46 §3) | a `0x0049cd60` rendező és a `0x004502e0` soronkénti érték igazolt; a sor-objektum és a `[obj+0x4e8]` tömb írója NINCS MEG | `0x0049cd60`, `0x004502e0`, `0x00c7ccf8` |
| U40 | RÉSZBEN (38.2.46 §1) | a név-tábla `CIndexer`, a fájl `wordhash.dat`, az elemek egész azonosítók, az előtagok `]album:`, `]facealbum:%d`, `]expeople:%d`; a képhalmaz NINCS MEG | `0x004db180`, `0x004db300` |

A 38.2.44 §9 listáját ez a lista váltja fel.

#### 38.2.47 Az Időrend bináris feltárása, 30. kör: a név-tábla olvasói, a rendező kulcsai, a mód-tartó és a listaírók (#5401, 2026-10-21)

**Válasz röviden.**
1. **Q1, melyik ír azonosítót a listába (U40): NINCS MEG; az olvasók igazoltak.** A `0x004db180` nem ír listát. Egy listában keres egy értéket, és 1 vagy 0 a visszatérési érték (§1.1). A `0x004db300` nem ír azonosítót. Kimásolja a kulcs listáját a hívó listájába (§1.3). Az azonosítókat író függvény a kötegben nincs meg. Az azonosító fajtája (kép, album vagy személy): **NINCS MEG**. Ghidra-kör kell: `0x0048c570` (a listaelemek forrása) és a `0x004da1d0` hívói (U42).
2. **Q2, a hasonlító (`0x004a7890`): LEZÁRVA a hívás módja és a kulcssorrend.** Az `obj` a `[P1+0xc]`, ahol `P1` a `0x004baaa0` első argumentuma (§2.1). A kulcsok: bájt-jelző, sor neve, mód, második név, irány (§2.3). Mindkét sor üres-név ágban más kulcsok vannak: fajta, aktív sor, két tömb (§2.3). Két mód jelentése NINCS MEG (U44).
3. **Q3, az `[X+0x2c0]` és a mód forrása (U36, U33): RÉSZBEN.** Az `[X+0x2c0]` tartja a mód- és irány-mezőt (`0x004b07c0` írja). A mód értéke parancs-ágankénti konstans: 0, 1, 2, 3 vagy 5. A 6. ágban a régi mód marad, az irány megfordul (§3.3). Az `[X+0x2c0]` a CThumbDB-tartó `L`? **Nem**, ha az a rendező (`obj`), mert a CThumbDB-tartó `[obj+0xc4]`, tehát másik objektum. Azonos-e az `[X+0x2c0]` a rendezővel: **NINCS MEG** (U43).
4. **Q4, a felhasználó szemével: NINCS MEG.** A Q1 nem dőlt el. Hiányzó címek: `0x0048c570`, `0x00484820` és a `0x004da1d0` hívói (lásd a szakasz végét).
5. **Q5, nyitott lista:** §9. 45 tétel: 6 lezárva, 19 részben, 20 nincs meg. Új tételek: U41-U45.

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-30.txt` hét címe: `0x004db180`, `0x004db300`, `0x004a7890`, `0x005cb990`, `0x005d9cc0`, `0x00449a00`, `0x0048c570`. A hívóláncok: `0x00484820`, `0x004b94a0`, `0x004b8ee0`, `0x006dc4c0`, `0x004b07c0`, `0x005d30f0`, `0x004da1d0`, `0x004930c0`, `0x00891110`, `0x006cae50`, `0x00a59000`, `0x004db8f0`. Az asm a `pe_dis.cdis`-szel készült. A hívókat és a stringeket a bináris index adta. A vtábla-hívások nem látszanak az indexből, ezért a hívóhelyeket asm-ben néztem meg. Ideiglenes fájl a `.bt/` alatt volt, a kör végén törölve. Kódot nem módosítottam, ezért a CI-őrök nem futottak. Commit, push, PR és jegy nincs.

**Bizonyítottsági fok.** Az asm-ből igazolt állítás erős. A dekompilációból jövő állítást jelölöm.

**Névhasználat.** A 38.2.44 és 38.2.46 szakasz ugyanazt a betűt két dologra használta. Ebben a szakaszban így nevezem:
- `obj`: a rendező objektum. A `0x004a7890` első argumentuma. A mód (`obj+0xd8`) és az irány (`obj+0x165`) rajta van. A 38.2.44 ezt hívta `L`-nek.
- `O`: a `[X+0x2c0]` objektum. A `0x004b07c0` ezt írja.
- `CT`: a CThumbDB-tartó, `[obj+0xc4]`. A `0x004502e0` és a `0x004507e0` ezt kapja. A 38.2.46 ezt hívta `L`-nek.
- `G`: a globális rendező-kontextus, `[0xd67678]`. A `G+8` bájt-tábla, `G+0xc` a nevek, `G+0x18` a dupla értékek, `G+0x1c` a sorok tábla.
- `V`: `[[0xd67668]+0x102c]`. A `0x004b07c0` és a `0x006dc4c0` ezt használja.
- `X`: a `0x005cb990` `ebx`-je (a belépéskor az `ecx`), és a `0x005d9cc0` első stack-argumentuma.

#### §1 Q1: a név-tábla olvasói és az írók

**§1.1 `0x004db180` (378 bájt, olvasó).** Két stack-argumentuma van. Az első az érték (`[ebp+8]`), a második a kulcs neve (`[ebp+0xc]`). Az `EAX` a CIndexer. A törzs:
- zárolja a CIndexer-t (a 38.2.45 mintája);
- `0x004dca40(név, O1)` keresi a kulcsot (`0x004db1e5`);
- ha van találat (`O1+0x5c` és `O1+0x64` nem nulla), `0x006cae50`-et hívja az `O1` objektumon (`0x004db23f`, az `EAX = O1` a `lea eax,[esp+0x14]` után, `0x004db23b`), az értékkel;
- a visszatérés `al`: 1, ha az érték benne van a listában, különben 0.

A függvény nem módosítja a listát. Csak a zárolás mezőit írja (`+0x20`, `+0x24`, `+0x28`).

**§1.2 `0x006cae50` (205 bájt, zárolt lista-keresés).** Ha `[O1+0x64] == 0` (`0x006cae57`), a visszatérés 0. Különben zárolja az `O1`-et, meghívja a `0x00a59000`-t (§1.2a), majd feloldja. A visszatérés a bájt-jelző.

**§1.2a `0x00a59000` (68 bájt, lineáris keresés).** A lista az `EDX`-ben van. Darabszám `[EDX+4]>>1`, az elemek 4 bájtosak, a tömb `[EDX+0]`. Ha az érték megvan, az indexét egy helyi változóba írja, és a bájt-jelzőt 1-re állítja. Különben 0 (`0x00a5901a`-`0x00a59038`).

**§1.3 `0x004db300` (487 bájt, másoló).** Két stack-argumentuma van:
- az első egy cella-mutató. Ha `*cella` nem nulla, a név `[*cella]+4`, különben 0 (`0x004db377`-`0x004db38b`);
- a második a kimeneti lista (`ebp`). A régi tartalmát felszabadítja (`0x0097caf0`), a méret mezőt pedig nullázza (`0x004db353`-`0x004db36b`).

Ezután `0x004dca40` keres. Találatnál `0x00891110(dst = kimenet, src = O1+0x64)` másol (`0x004db434`-`0x004db43b`).

**§1.4 `0x00891110` (407 bájt, lista-másolás).** `dst = src`. A darabszám `[src+4]>>1`. A cél tömböt `0x0097c810` foglalja (darab x 4 bájt), a méret mezőt pedig darab x 2 és az alacsony bit adja. Végül `0x00bf2350` (memcpy-szerű) másolja az elemeket (`0x00891287`-`0x00891293`).

**§1.5 Hívók.**
- `0x00449a00` (39 bájt, `__thiscall`, `ret 4`). A kulcs a `[ECX+0x2e94]+4` (ha a mutató nem nulla, különben 0). `EAX = ECX+0x68` (a CIndexer). Meghívja a `0x004db180(érték, kulcs)`-t, és a visszatérést `setne`-vel adja. Vagyis: benne van-e az érték a `[ECX+0x2e94]` bejegyzés nevű listájában (`0x00449a11`-`0x00449a24`). Hívója: `0x00484820` (`0x00484bc3`). Az érték a `0x00484820` tömbjének eleme (`mov edx,[esi+ebp*4]`, `0x00484bbd`). A tömb forrása: NINCS MEG (U41).
- `0x0048c570` (7277 bájt, dekompiláció, a 6516-6649. sor). Az `i` ciklusváltozó 0-tól a darabszám-1-ig megy. A kulcs `"]expeople:%d"`, a `%d` az `i` (`0x0040eab0`, 6524. sor). Ezután `0x004db300(&local_108, &local_104)` másolja a kulcs listáját (6527. sor). Ha az üres, a ciklus lépést ugrik. Különben a `puVar1` listából kiszűri azokat az elemeket, amelyeket `0x004930c0` az ECX-ben lévő listában talál (6533-6548. sor). A 6608. sorban `(*(param_1+0x48)+0x2c)(i, local_c8)` hívás van (vtábla-hívás, a cél NINCS MEG; a 38.2.44 szerint a CThumbDB vt+0x2c a `0x004406f0`).
- A 38.2.46 szerinti másik hívó, `0x007d6db0` (`0x007d792e`), nincs végigolvasva.

**§1.6 `0x004930c0` (52 bájt, benne-van-e).** `bool benne(ECX lista, *érték)`. Lineáris keresés `[ECX]` tömbjében, darabszám `[ECX+4]>>1` (`0x004930c0`-`0x004930e5`). A `0x0048c570` ezt a szűrést végzi. Az ECX-ben lévő lista forrása: NINCS MEG.

**§1.7 Az író jelöltje: `0x004da1d0` (1090 bájt, 26 hívó).** Név szerint keres (`0x004de1a0` a hash, a modulus `[this+0x58]`, a vödör `[this+0x60]`, `0x00bf697a` = `_stricmp` a `[csomópont+4]`-en; `0x004da262`-`0x004da29f`). Találatnál a lista méretét a kért darabszámra állítja: `0x0097c810` foglal, `0x0097caf0` szabadít, és a méret mezőt frissíti (`0x004da41f`-`0x004da58c`). Ha a verem egyik argumentuma nem nulla, értesíti a figyelőket (`0x004db8f0`, `0x004da5a1`). ⚠️ **HELYESBÍTVE (38.2.48 §1.2):** a találatnál a régi lista elemeit is végigjárja, és átmásolja azokat, amelyek nincsenek a kapott listában. Az új elemeket a hívó írja (38.2.48 §1.3). Az írók: RÉSZBEN (U42). A nem-találat ágát nem olvastam végig.

**§1.8 `0x004db8f0` (75 bájt, értesítő).** Növeli a `[this+0x4c]` számlálót, a `[this+0x50]`-et 1-re állítja, és a `[this+0x84]` tömb minden tagjának virtuális hívást küld (`0x004db8f0`-`0x004db938`). Nem lista-író.

**§1.9 Az identitás (kép, album vagy személy): NINCS MEG.** Két jel van, de egyik sem dönt:
- A `]expeople:%d` kulcsban a `%d` a `0x0048c570` ciklus sorszáma (`local_10c`, 6517. és 6524. sor). A személy-kulcs tehát sorszámmal épül, és nem a személy nevével.
- A `0x0048c570` a 4 bájtos elemeket a `0x004930c0`-val hasonlítja össze. Ebből a típus nem következik.

Ghidra-kör kell: `0x0048c570` 5298-5350. sor (a `local_128` lista és a `local_124` darabszám forrása) és a 6608. sor vt+0x2c célja.

#### §2 Q2: a hasonlító (`0x004a7890`)

**§2.1 Az `obj` hívása (LEZÁRVA).** A `0x004a7890` (2618 bájt) stack-argumentumai: `[esp+4]` az `obj`, `[esp+8]` és `[esp+0xc]` a két sor indexe (`0x004a78a3`: `mov edi,[esp+0x2c]`, a belépési állapotban ez az első argumentum). Hívói:
- `0x004baaa0`, `0x004bab4f` és `0x004bab9f` (mindkettőben `push [edi]`, `push [edi+4]`, `push [P1+0xc]`), ahol `P1` a `0x004baaa0` első argumentuma (`0x004bab45`-`0x004bab4e`);
- `0x004bb040`, `0x004bb06a`.

A `P1`-et a rendezés két belépési pontja állítja össze. A `[P1+0xc]` a hívó `ESI`-je:
- `0x004b94a0`: `[P1+0xc]` = `ESI` (`0x004b9742`), `ESI` = a belépési `EAX` (`mov esi,eax`, `0x004b94b5`). ⚠️ **HELYESBÍTVE (38.2.48 §2.6):** ez téves. A `mov` egy IAT-hívás (`call [0xc40284]`, `0x004b94af`) után áll, ezért az ESI a hívás visszatérése. A `P1` a `0x004b9728`-ban épül.
- `0x004b8ee0`: `[P1+0xc]` = `ESI` (`0x004b9163`), `ESI` = a belépési `EAX` (`mov esi,eax`, `0x004b8eed`).

**§2.2 A globális kontextus (G).** A rendezés előtt a `[0xd67678]` (G) a hívó verem-struktúrájára mutat:
- `0x004b94a0`: `mov [0xd67678],eax` (`0x004b9735`), a fő ágban, a `0x004b9722` ugrás után;
- `0x004b8ee0`: `mov [0xd67678],edx` (`0x004b9150`), csak ha `ebx <= eax` (`0x004b914a` ugrás).

A G tartalmát a hívó tölti fel. A feltöltés helye: `0x004b94a0` a `0x004b9735` előtt, `0x004b8ee0` a `0x004b9150` előtt. Részletek: NINCS MEG (U37).

**§2.3 A rendezés hívási lánca.** A `0x004b07c0` (mód-író) az `O`-n állítja a módot, majd `0x006dc4c0(V, 1)`-et hív (`0x004b0803`). A `0x006dc4c0` (1227 bájt) `EBP = V` (`mov ebp,[esp+0x68]`, `0x006dc4c5`), és `EAX = [V+0x2c0]` után `0x004b8ee0`-t hívja (`0x006dc626`-`0x006dc62c`). Tehát a `0x004b8ee0` `this`-e, és így `obj` is, ebben a láncban `[V+0x2c0]`. A `0x004b94a0` hívóinak `this`-e (`0x0056c5a0`, `0x005fe130`): a `0x005fe130` esetén LEZÁRVA (O = `[X+0x2c0]`, 38.2.48 §4), a `0x0056c5a0` esetén NINCS MEG (U51).

**§2.4 A kulcssorrend (G != 0 ág, a normál út).** A hasonlító sorokat ez a sorrend szerint rendezi:
1. **Bájt-jelző.** A `G+8` tábla adott sor-indexén (`0x004a78b0`-`0x004a78e4`, 277-309. sor). Növekvő. Ha eltér, ez dönt.
2. **Sor neve.** A `0x004a71e0` mindkét sorra (a név a `+4` mezőben). Kis-nagybetű nem számít (csak az ASCII A-Z). Ha eltér, ez dönt (323-370. sor). Az irányát ebben a körben nem mértem meg (a két `0x004a71e0` hívás argumentum-sorrendje nincs igazolva).
3. **Mód, `obj+0xd8` (538-597. sor).**
   - 0: a `G+0x18` tábla dupla értékei. Növekvő. Ha eltér, ez dönt.
   - 4: `0x004502e0(CT, sor, &érték)`. A 38.2.46 §3.2 szerinti dátum. Dupla összehasonlítás.
   - 1: a `0x004ae0d0` float10 értéke. ⚠️ **HELYESBÍTVE (38.2.48 §2.6):** nem argumentum nélkül hívódik. ECX a sor indexe, EDX a rendező. A dupla tartalma: U32. A kulcs mechanikája: RÉSZBEN (U44, 38.2.48 §2).
   - 5: `0x004507e0(CT, sor, &érték)`, 64 bites összeg (a rekord `+0x14` mezőjének összege). RÉSZBEN (U44, 38.2.48 §2.3).
   - 2 és 3: nincs külön ág. Ezeknél a sorrend a 4. pontra esik.
4. **Második név.** A `G+0xc` tábla neve, ASCII, kis-nagybetű nem számít (598-669. sor). Az irányát ebben a körben nem mértem meg.
5. **Irány, `obj+0x165`.** Ha 0, az eredmény változatlan, különben előjelet vált (670. sor). Az 1. és 5. mód ágában is van irányfordítás (580-595. sor).

**§2.5 Az üres-név ág.** Ha mindkét sornak nincs neve (`bVar20 && bVar21`, 405. sor), más kulcsok jönnek. Ez a `0x004a7ad4`-`0x004a7b2b` környékén van.
- `0x00987030(sor, ']album')` és `0x00987030(sor, ']facealbum')` (`mov ecx, 0xc811cc` és `mov ecx, 0xc818b8`, `0x004a7ad4`, `0x004a7b0d`): fajta-teszt. Törzse LEZÁRVA (U25, 38.2.48 §3).
- Az aktív sor: `[CT+0x2960]`, ha egyik sor egyezik vele, az elsőbbséget kap (460. sor).
- `[obj+0xdc]` 1 vagy 2: a `+0x428` vagy a `+0x438` tömb numerikus értéke (473-491. sor, asm: `0x004a7c77`, `0x004a7c82`, `0x004a7ca9`).
- Utána a második név.

**§2.6 Ami NINCS MEG a hasonlítóban.** A `G == 0` ág (`0x004a78a7` `je` után, `0x004a8052`): ott a sorokat a `0x00453da0` adja a `[obj+0xc4]`-ből. Törzse nincs végigolvasva. A `0x004ae0d0` és a `0x004507e0` jelentése (U44). A `G+0x18` tábla forrása (U24).

#### §3 Q3: a mód-író, a mód forrása, és az `L` kérdés

**§3.1 `0x004b07c0` (75 bájt, mód-író).** Az első argumentum az `O`. Ha `[O+0xd8] == edx` és `[O+0x165] == cl`, a visszatérés `0xf4242` (`0x004b07c4`-`0x004b07d9`), és nincs átrendezés. Különben `[O+0x165] = cl`, majd `[O+0xd8] = edx` (`0x004b07dc`-`0x004b07e2`). Ezután `V = [[0xd67668]+0x102c]` (`0x004b07e8`-`0x004b07f7`). Ha `V` vagy `[0xd67668]` nulla, a visszatérés 0. Különben `0x006dc4c0(V, 1)` (`0x004b0800`-`0x004b0803`).

**§3.2 `0x005d30f0` (171 bájt).** `EDI = X`. Ha `[X+0xea0]` nulla, a visszatérés 4. Különben `[X+0x24c]` nő, `[X+0x250]` nullázódik, és `0x004b07c0([X+0x2c0])` (`0x005d3127`). Hívója: `0x005cb990`, 6 helyen.

**§3.3 A mód forrása (`0x005cb990`, 8291 bájt).** Az `ebx = ecx` (`0x005cb9aa`), vagyis `X` a belépéskor az `ECX`. A 6 hívóhelyen `edi = ebx` (`mov edi,ebx`), tehát a `this` az `X`. Az `O = [X+0x2c0]` minden ágban `mov ...,[ebx+0x2c0]`:

| hívóhely | edx (mód) | cl (irány) | megjegyzés |
|---|---|---|---|
| `0x005cbbfa` | 0 (`xor edx,edx`, `0x005cbbf6`) | `[O+0x165]` | konstans |
| `0x005cbc17` | 2 (`0x005cbc10`) | `[O+0x165]` | konstans |
| `0x005cbc34` | 1 (`0x005cbc2d`) | `[O+0x165]` | konstans |
| `0x005cc70a` | 5 (`0x005cc703`) | `[O+0x165]` | konstans |
| `0x005cd5f9` | 3 (`0x005cd5f2`) | `[O+0x165]` | konstans |
| `0x005cd61e` | `[O+0xd8]` (`0x005cd60f`, változatlan) | `!([O+0x165])` (`0x005cd617`, `sete`) | a régi mód marad, az irány megfordul |

Vagyis a mód értéke nem számolódik. Parancs-ágankénti konstans, a 6. ágban pedig az aktuális mód. Hogy melyik parancsazonosító melyik ágra fut: NINCS MEG (U33). A `0x005cb990` közvetlen hívóját a bináris index nem mutatja (táblás hívás).

**§3.4 `0x005d9cc0` (7153 bájt).** Az `ebx` az első stack-argumentum (`mov ebx,[esp+0x14]`, `0x005d9ccc`), vagyis `X`. Két közvetlen hívás van `0x004b07c0`-ra:
- `0x005db20c`: `edx = 2` (`0x005db207`), `cl = [O+0x165]`, `O = [ebx+0x2c0]` (`0x005db1fa`);
- `0x005db26f`: `edx = 0` (`0x005db26d`), `cl = [O+0x165]`, ugyanígy.

A hívója a `0x005de8e0` (az index szerint).

**§3.5 Az `L` kérdés (U36).** Az `[X+0x2c0]` az `O`. Az `O` és az `obj` ugyanazt a mezőt tartja: `+0xd8` (mód) és `+0x165` (irány). Ha `X = V`, akkor `O = obj` (ezt a 38.2.44 `L`-nek hívta), és a mód-tartó az `O`. A CThumbDB-tartó (38.2.46 szerinti `L`) a `[obj+0xc4]`, mert ezt kapja a `0x004502e0` és a `0x004507e0` (`0x004a7890` 565. és 586. sor). Ez nem a mód-tartó. Tehát:
- a kérdésre, hogy az `[X+0x2c0]` a CThumbDB-tartó `L`-e: **nem**, ha `O = obj`;
- a kérdésre, hogy az `[X+0x2c0]` a mód-tartó `L`-e: **igen**, ha `X = V`;
- az `X = V` feltétel: **NINCS MEG** (U43). Ghidra-kör kell: a `0x005cb990` `ECX`-e a hívásnál (táblás hívó), és a `[0xd67668]` írói.

#### §4 Helyesbítések a korábbi szakaszokban

1. **38.2.46 §1.4, §8, U40 (lista-író).** ⚠️ HELYESBÍTVE: a `0x004db180` és a `0x004db300` nem ír listát (§1.1, §1.3). Ezek olvasó és másoló függvények. Az író keresése: U42.
2. **38.2.46 §4.4 (`L = [P+0xc4]`).** ⚠️ PONTOSÍTVA (§3.5): a spec két `L`-t használt. A 38.2.44 `L` a mód-tartó (`obj`), a 38.2.46 `L` a CThumbDB-tartó (`[obj+0xc4]`).
3. **38.2.46 §4.1 és 38.2.46 §2.2 (mód az `L+0xd8`-ban).** ⚠️ PONTOSÍTVA: a mód-mező az `O`/`obj` `+0xd8` mezője. A mód értékét parancs-ág adja (§3.3). A 38.2.46 §2.2 `L` a 38.2.44 jelölése (`obj`).
4. **38.2.46 §2.1 (G-táblák).** Kiegészítés: a G egy veremszerkezet, amit a hívó állít be (§2.2). A táblák tartalma NINCS MEG (U37).
5. **38.2.46 §1.2 (`]album`, `]facealbum` a 0x004a7890-ban).** Megerősítve: a `mov ecx, 0xc811cc` és `mov ecx, 0xc818b8` sorok a `0x004a7ad4`, `0x004a7b0d` címeken vannak (§2.5).

#### §5 Amit KIZÁRTAM (38.2.47)

- „A `0x004db180` vagy a `0x004db300` ír a listába”: **CÁFOLVA** (§1.1, §1.3).
- „A `0x004a7890` a módot a `G`-ből olvassa”: **CÁFOLVA**. A mód `obj+0xd8`-ból jön, a `G` a táblákat adja (§2.4).
- „A mód értéke a `0x004b07c0`-ban számolódik”: **CÁFOLVA**. A `0x004b07c0` csak tárolja (§3.1), a értéket a hívó parancs-ága adja (§3.3).
- „Az `[X+0x2c0]` a CThumbDB-tartó”: **CÁFOLVA** feltéve, hogy `O = obj`. A CThumbDB-tartó az `[obj+0xc4]` (§3.5).

#### §6 Ghidra-címek a következő körhöz

- `0x00484820` (U41): a 2740 bájtos függvény eleje, ahol a `[esi+ebp*4]` tömb épül.
- `0x0048c570` (U42): az 5298-5350. sor (`local_128`, `local_124`), a 6533-6548. sor (az ECX a `0x004930c0` előtt), és a 6608. sor (vtábla-cél).
- `0x004da1d0` hívói (26 db), különösen `0x00456610`, `0x00448560`, `0x00439a80` (U42): melyik ír elemet.
- `0x005cb990` hívója és a belépési `ECX` (U43). A táblás hívás forrása.
- `[0xd67668]` írói (`mov [0xd67668],reg` alakok) (U43).
- `0x004ae0d0` és `0x004507e0` (U44): a mód-1 és a mód-5 törzse.
- `0x0056c5a0` és `0x005fe130` (U45): a `0x004b94a0` hívásának `EAX`-e.
- `0x00987030` (U25): a fajta-teszt törzse.

**A felhasználó szemével**

Az első kérdés nem dőlt el. A név-tábla olvasói igazoltak, de a listába írt azonosítók írója és fajtája nincs meg. Ezért nincs két-három mondatos összefoglaló. Hiányzó címek: `0x0048c570` (a listaelemek írója), `0x00484820` (a bemeneti tömb), és a `0x004da1d0` hívóinak egyike (az elem-író).

#### §9 Nyitott lista (38.2.47, felülírva: lásd 38.2.48 §9)

Nyitott kérdések mérlege (38.2.47): 45 tétel · 6 lezárva · 19 részben · 20 nincs meg.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U1 | NINCS MEG (változatlan) | a `0x00a6aa00` teljes törzse | `0x00a6aa00` |
| U2 | RÉSZBEN (változatlan) | az obj2 osztálya és a vt+0 cél | `0x005e8a70`, `M+0x4c` vt+0 |
| U3 | RÉSZBEN | a mód-tartó (`obj`, névhasználat) igazolt; az `L` osztálya a 38.2.46 szerint NINCS MEG | `0x004a7890`, `0x004baaa0` |
| U4 | NINCS MEG (változatlan) | a `0x008014d0` vt+0 hívott függvénye | `0x008014d0` |
| U5 | NINCS MEG (változatlan) | a `[this+0x2ec]` olvasói | pásztázás |
| U6 | NINCS MEG (változatlan) | a `0x009aaae0` hívóhelyei | `0x009aaae0` |
| U7 | LEZÁRVA (38.2.41 §1) | a sorrekord `+0x14` írója | - |
| U8 | NINCS MEG (változatlan) | a `P' = [T+0x3a4]` írója | `0x007fa7f0` |
| U9 | LEZÁRVA (38.2.41 §2-3) | a kattintási ág | - |
| U10 | RÉSZBEN (változatlan) | a `0x004b8470` hívója és az `[L+0x148]` írói | `0x004b8ee0` |
| U11 | RÉSZBEN (változatlan) | az `L` osztálya, `+0xc == 2`, `jbe` | `0x004b29d0` |
| U12 | NINCS MEG (változatlan) | az EBP/EBX forrása a hívottakban | `0x004b2e10`, `0x004b3770`, `0x004b80d0` |
| U13 | RÉSZBEN (változatlan) | a `0x007fc010` | `0x007fc010` |
| U14 | RÉSZBEN (változatlan) | a `0x008014d0` törzse | `0x008014d0` |
| U15 | NINCS MEG (változatlan) | a startbutton vt+0x18 | `0x007fa7f0` |
| U16 | RÉSZBEN (38.2.47 §2.4) | a rendező kulcssorrendje igazolt; a G-táblák feltöltése U37 | `0x004a7890`, `0x004baaa0` |
| U17 | NINCS MEG (változatlan) | a `0x004b8d00` | `0x004b8d00` |
| U18 | NINCS MEG (változatlan) | az `E` görbe | `0x005568e0` |
| U19 | NINCS MEG (változatlan) | a rekord-utólagos és a ciklus-utáni lépés | `0x007fa650`, `0x00604480` |
| U20 | NINCS MEG (változatlan) | a kártya-rekord építése | `0x007fa5b0` |
| U21 | LEZÁRVA (38.2.43 §2) | a CSlice konstruktor és a destruktor-lánc | `0x004133e0`, `0x00413490` |
| U22 | RÉSZBEN (változatlan) | a `0x004406f0` a vt+0x2c cél; a `[L+0x48]` vtábla újra nincs igazolva | `0x00402f90`, U36 |
| U23 | LEZÁRVA a törzs (38.2.44 §2) | a sor neve | `0x004a71e0` |
| U24 | RÉSZBEN (38.2.47 §2.4) | a 4. mód igazolt; a 0. mód a `G+0x18` dupla táblája (a tábla forrása NINCS MEG); az 1. mód U44 | `0x004502e0`, `0x004a7890` |
| U25 | RÉSZBEN (38.2.47 §2.5) | az üres-név ág fajta-tesztje (`]album`, `]facealbum`) igazolt; a `0x00987030` törzse NINCS MEG | `0x00987030`, `0x004a7ad4` |
| U26 | NINCS MEG (változatlan) | a K-másolás törzse | `0x00801915`-`0x00801bc4` |
| U27 | NINCS MEG (változatlan) | az `M+0x64c` és `M+0x650` írása | `0x005e8a70` |
| U28 | LEZÁRVA (38.2.45 §1) | a kulcs NÉV | `0x004dca40`, `0x004406f0` |
| U29 | RÉSZBEN (38.2.45 §2) | a `[X+0x1034]` CThumbDB írója LEZÁRVA; az `L` írója U36 | `0x00402f90`, U36 |
| U30 | RÉSZBEN (38.2.45 §4) | a G-szerep LEZÁRVA; a táblák feltöltése U37 | `0x004b94a0`, U37 |
| U31 | RÉSZBEN (38.2.46 §3.2) | a bemenet igazolt; a statisztika neve NINCS MEG | `0x00450100` |
| U32 | NINCS MEG (változatlan) | az 1. mód összesítője | `0x00450bd0` belső ága |
| U33 | RÉSZBEN (38.2.47 §3.3) | a mód forrása parancs-ágankénti konstans (0, 1, 2, 3, 5); a 6. ág megfordítja az irányt; a parancsazonosító és az ág párosítása NINCS MEG | `0x005cb990` (6 hely), `0x005d9cc0` (2 hely), `0x004b07c0` |
| U34 | NINCS MEG (változatlan) | az OLEAUT32 184. sorszám neve | IAT `0x00c405c8` |
| U35 | RÉSZBEN (38.2.46 §1.3) | a literál szövege `token`; a rekord `+5` mezőjének tartalma NINCS MEG | `0x00415790`, `0x00985ff0`, `0x004941f0` |
| U36 | RÉSZBEN (38.2.47 §3.5) | az `[X+0x2c0]` a mód-tartó (ha `X = V`); a CThumbDB-tartó az `[obj+0xc4]`; az `X = V` NINCS MEG (U43) | `0x004b07c0`, `0x005d30f0`, `0x004502e0` |
| U37 | RÉSZBEN (38.2.47 §2.2) | a G-veremszerkezetet a hívó állítja be (`0x004b9735`, `0x004b9150`); a tartalmának feltöltése NINCS MEG | `0x004b94a0`, `0x004b8ee0` |
| U38 | LEZÁRVA (38.2.46 §2.2; a sorrend 38.2.47 §2.4) | egyesítő rendezés; a kulcsot a `0x004a7890` adja | `0x004baaa0`, `0x004a7890` |
| U39 | RÉSZBEN (38.2.47 §2.1) | az `obj` a hívó `this`-e; a `0x004b8ee0` `this`-e `[V+0x2c0]`; a `0x004b94a0` `this`-e NINCS MEG (U45) | `0x004b8ee0`, `0x006dc4c0` |
| U40 | RÉSZBEN (38.2.47 §1) | a név-tábla olvasói igazoltak (`0x004db180`, `0x004db300`, `0x00449a00`); az író és az elemek fajtája NINCS MEG | `0x004db180`, `0x004db300`, `0x00449a00` |
| U41 | NINCS MEG (új) | a `0x00484820` tömbje, amelynek elemeit a `0x00449a00` vizsgálja | `0x00484820` (`0x00484bbd`) |
| U42 | NINCS MEG (új) | a név-tábla listaelemeinek írója; a `0x004da1d0` csak darabszámot állít, a `0x0048c570` szűr; az elemek forrása NINCS MEG | `0x0048c570`, `0x004da1d0` |
| U43 | NINCS MEG (új) | az `X` (a `0x005cb990` `ebx`-je) azonos-e a `V = [[0xd67668]+0x102c]`-vel | `0x005cb9aa`, `0x004b07e8`, `0x006dc4c0` |
| U44 | NINCS MEG (új) | a `0x004ae0d0` (mód 1, argumentum nélkül hívva) és a `0x004507e0` (mód 5) jelentése | `0x004ae0d0`, `0x004507e0` |
| U45 | NINCS MEG (új) | a `0x004b94a0` `this`-e a hívóiban (a rendező objektum ezen az úton) | `0x0056c5a0`, `0x005fe130` |

#### 38.2.48 Az Időrend bináris feltárása, 31. kör: a név-tábla írói, a két rendező-kulcs, a fajta-teszt és a listaépítő (#5401, 2026-10-21)

**Válasz röviden.**
1. **Q1, a név-tábla listái (U41, U42): RÉSZBEN.** A `0x00484820` nem tölt névtáblát. Csak olvassa a listát a `0x00449a00` hívásával. A `0x00484820` által a `0x00449a00`-nak adott tömböt a `0x00506830` építi, a törzse **NINCS MEG** (U46). A névtábla listáit a `0x00456610` (`]star` és `]hidden` kulcs) és a `0x00448560` (a tulajdonos objektum `+0x2e9c` mezőjében álló név) tölti. Az elemet mindkét helyen a hívó adja: a második verem-argumentum (`param_3`). Hogy ez kép, album vagy személy: **NINCS MEG** (U49, U50).
2. **Q2, az 1. és az 5. mód (U44): RÉSZBEN.** Mindkét mód a saját kulcsát hasonlítja össze. Az 5. mód kulcsa a sor elemeinek `+0x14` mezőjéből képzett 64 bites összeg. Az 1. mód kulcsa a `0x00450bd0` által adott dupla érték. Ennek a tartalma **NINCS MEG** (U32). Egyenlőségnél mindkét módban a következő kulcs dönt. A rendező `+0x165` bájtja megfordítja az irányt.
3. **Q3, a `0x00987030` törzse (U25): LEZÁRVA.** A függvény azt adja vissza, hogy a sor szövege a kapott szöveggel kezdődik-e. Az ASCII kis- és nagybetűt nem különbözteti meg. A `0x004a7890` ezzel keresi a `]album` és a `]facealbum` szöveget.
4. **Q4, a `0x005fe130` (U45): LEZÁRVA a hívó felől.** A `0x005fe130` egyetlen verem-argumentumot kap, X-et. A `0x004b94a0`-t `O = [X+0x2c0]` argumentummal hívja. A `0x0056c5a0` hívója: **NINCS MEG** (U51).
5. **A felhasználó szemével:** nincs két-három mondatos összefoglaló, mert a kérdés (mi a listaelem) nem dőlt el. A hiányzó címek a szakasz végén vannak.

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-31.txt` hét címe (`0x00484820`, `0x004ae0d0`, `0x004507e0`, `0x00987030`, `0x005fe130`, `0x00456610`, `0x00448560`). A korábbi körök dekompilátumai közül a `0x004da1d0` a `-12.txt`-ben, a `0x004b94a0` hívói a `-28.txt`-ben, a `0x00449a00` a `-30.txt`-ben. Az asm `pe_dis.cdis`-szel készült. Ennek a második paramétere **bájt**, nem utasításszám. A hívóhelyeket nyers bájtos kereséssel is megnéztem (E8 rel32 célcím). Kódot nem módosítottam, ezért a CI-őrök nem futottak. Ideiglenes fájl nem készült. Commit, push, PR, jegy és cron nincs.

**Bizonyítottsági fok.** Az asm-ből igazolt állítás erős, a címét mindenhol megadom. A dekompilátumból jövő állítást **(dekompilátum)** jelölöm.

**Névhasználat.** `owner`: a `0x00448560` és a `0x00456610` első verem-argumentuma (`param_2`), a tulajdonos objektum. A névtábla a `owner+0x68`-on van (`0x00448560`, `0x00456610`). `X`, `O`, `CT`, `obj` a 38.2.47 szerint értendő. A `]star` és a `]hidden` szöveg a binárisban áll. Jelentésük (csillagozott, rejtett) csak a szövegből sejthető, a felülettel való kapcsolatuk **NINCS MEG**.

##### §1 Q1: a név-tábla írói (U41, U42)

**§1.1 A `0x00484820` nem író (U41).**
- A HÍVOTTAK lista (42 db, dekompilátum) nem tartalmazza a `0x004da1d0`, a `0x00448560` és a `0x00456610` címet. Közvetlenül tehát nem ír névtáblát. A `0x00446610` törzsét nem néztem meg, a `0x00484820` dekompilátumának 204. sorában hívja. Ha az közvetve ír, ez az állítás csak a közvetlen hívásokra igaz.
- A bemeneti tömb építése: a `0x00484a70` így hívja a `0x00506830`-at. `lea eax,[esp+0x34]`, `push eax` (a kimeneti pár címe), `push ebp` (az első verem-argumentum, a dekompilátumban `local_dc`), `lea eax,[ebx+0xf8]` (EAX a `0x00506830` objektuma), `call 0x506830` (`0x00484a5c`-`0x00484a70`). A kimeneti tömb dekompilátum szerinti neve `iStack_d0`, darabszáma `uStack_cc >> 1`.
- Az elemek olvasása: `0x00484bbd`: `mov edx,[esi+ebp*4]`, `push edx`, `mov ecx,ebx`, `call 0x449a00` (`0x00484bc3`). Minden elemre a `0x00449a00` fut, ECX a tulajdonos (`ebx`).
- A második `0x00506830`-hívás (`0x00485692`) már a `0x00484820` függvényen kívül esik (a függvény 2740 bájt).
- A `0x00506830` törzse: **NINCS MEG** (U46). Ghidra-kör kell: `0x00506830 - a kimeneti pár feltöltése (verem 2), az index (verem 1; ⚠️ JAVÍTVA 38.2.49 §7: nem kulcs) és az objektum (EAX = [ebx+0xf8]) szerepe. [blokkoló]`

**§1.2 A `0x004da1d0` (a név-tábla írója és olvasója, verifikált).**
- EAX = a név-objektum. `[EAX]` a szöveg pufferének mutatója, a szöveg a puffer `+4` címén van (asm és dekompilátum egyezik, `0x004489e6`, `0x00458d17`).
- Verem 1: `owner+0x68`, a névtábla (hash-tábla). Verem 2: a lista párja (mutató és méret-mező). Verem 3: 1 vagy 2 (a hívóknál).
- Üres név (nincs puffer, vagy az első karakter nulla): 0, nincs írás (dekompilátum, file 12).
- Keresés: `0x004de1a0` a hash, a vödörben `__stricmp` (kis- és nagybetű nem számít).
- Találatnál a régi lista elemeit végigjárja. A kapott listában szereplőket kihagyja, a többit átmásolja (`*(... + local_c*4) = ...`, dekompilátum). Az új elemek beírásának ágát nem olvastam végig.
- ⚠️ **HELYESBÍTVE** a 38.2.47 §1.7 „csak darabszámot állít” állítása: a függvény a régi elemeket is írja.

**§1.3 Az írók (U42).**

| hívóhely | név | lista | azonosító |
|---|---|---|---|
| `0x00448560`, hívás `0x004489e6` | `[owner+0x2e9c]` objektum (`lea eax,[esi+0x2e9c]`, `0x004489dc`). Futás közben áll be, nem literál. | egy elem: `[param_3]` (`0x004489c6`-`0x004489ce`) | `param_3`, a sor sorszáma. Ez a 8 bájtos sor-érték tábla indexe (`[owner+0x1d38]+0x48`, alapértéke `owner+0x1d40`). |
| `0x00456610`, hívás `0x00458d17` | `]star` (literál `0xc811d4`). A `0x00985ff0` építi a veremben (`push 0xc811d4` a `0x00458cf4`-nél, hívás `0x00458d02`). | `iStack_174`, elem: `param_3` (dekompilátum) | `param_3`, a második verem-argumentum |
| `0x00456610`, hívás `0x00458f13` | `]hidden` (literál `0xc811f4`, hossz 7: `mov eax,7`, `0x00458ef5`). Hívás `0x00458efe`. | `iStack_16c`, elem: `param_3` (dekompilátum, 3642. sor) | `param_3` |
| `0x00456610`, hívás `0x0045a8b8` | `]star` (literál a `0x0045a87d` környékén) | `0x00493050(&param_3)` (⚠️ JAVÍTVA 38.2.49 §7: nem ad vissza értéket, a listát az ESI-ben építi; `push edx`, `call 0x493050`, `0x0045a89e`-`0x0045a8a6`) | **LEZÁRVA** (38.2.49 §1.1, U47) |
| `0x00456610`, a `0x00458aeb` ág | `]star` (literál `0xc811d4`), majd `0x004d9aa0` hívás (nem `0x004da1d0`) | `iStack_164`, elem: `param_3` (dekompilátum) | **NINCS MEG** a `0x004d9aa0` törzse (U52) |

- A `0x00448560` feltétele (dekompilátum, 5515-5528. sor). Ha a jelző (`param_4`) nulla, nincs lista-írás. Ha nem nulla, és az új érték 0 vagy 1, a sor bekerül a listába, feltéve hogy a régi érték nem 0 vagy 1. Ha az új érték más, a `0x004d9570(owner+0x68, param_3, 0)` törli a sort. A lista tehát a 0 vagy 1 értékű sorokat tartja (dekompilátum, a jelentés nincs megnevezve).
- A literál-szövegek a binárisban (nyers bájtok): `0xc811cc` = `]album`, `0xc811d4` = `]star`, `0xc811dc` = `]screensaver`, `0xc811ec` = `]geo`, `0xc811f4` = `]hidden`.

**§1.4 Ami nincs meg.**
- Az elemek fajtája (kép, album, személy). A `param_3` forrása a `0x00456610` hat hívójánál (U49) és a `0x00448560` nyolc hívójánál (U50). A `0x00493050` törzse (U47).
- A `[owner+0x2e9c]` és a `[owner+0x2e94]` név viszonya és írói (U48). A `0x00449a00` a `[owner+0x2e94]` mutatót használja, a `0x00448560` a `owner+0x2e9c` objektumot. Hogy ugyanaz a név-e, **NINCS MEG**.

##### §2 Q2: az 1. és az 5. mód (U44)

**§2.1 A hívás (asm, verifikált).**
- `0x004a7e80`: `cmp dword ptr [edi+0xd8], 1` (`83 bf d8 00 00 00 01`). Ha nem 1, a `jne` a `0x004a7ef5`-re ugrik, ahol az 5. mód ellenőrzése van (`cmp [edi+0xd8], 5`, `0x004a7ef5`).
- Az 1. mód: `mov ecx,ebx`, `mov edx,edi`, `call 0x4ae0d0` (`0x004a7e8d`). Majd `mov ecx,esi`, `mov edx,edi`, `call 0x4ae0d0` (`0x004a7e9a`). EBX és ESI a két sor, EDI a rendező.
- Az 5. mód: `mov eax,[edi+0xc4]`, `lea ecx,[esp+0x18]`, `push ecx`, `push ebx`, `push eax`, `call 0x4507e0` (`0x004a7f0f`). Majd ugyanez `lea edx,[esp+0x20]` és `push esi` párral (`0x004a7f21`).

**§2.2 Az 1. mód kulcsa (`0x004ae0d0`, verifikált).**
- `lea eax,[esp]`, `push eax` (a kimeneti dupla címe). `mov eax,[edx+0xc4]` (EAX = Z = a rendező `+0xc4` mezője). `push ecx` (a sor indexe). `call 0x450bd0` (`0x004ae0de`). Majd `fld qword ptr [esp]`. A visszatérés tehát a `0x00450bd0` által a kimeneti helyre írt dupla.
- A `0x00450bd0` törzse: **NINCS MEG** (U32).

**§2.3 Az 5. mód kulcsa (`0x004507e0`, verifikált).**
- Argumentumok: 1. verem-argumentum CT (`mov ecx,[esp+0xe4]`, `0x00450801`). 2. a sor indexe. 3. a kimeneti 64 bites pár (`mov eax,[esp+0xdc]`, `0x004507e6`). A pár nullázása: `0x004507f3`-`0x004507f5`.
- A sor elemeinek listáját a `CT+0x48` alobjektum vtábla `+0x2c` slotja adja (`0x00450808`-`0x00450826`, a `this` a `CT+0x48`). A 38.2.44 szerint ez a `0x004406f0`. Ezt most nem mértem újra.
- Minden elemre: a rekord a `[CT+0x4e8]` táblából jön, az elem értéke az indexe. Ha ez a mutató nulla, a `CT+0x4f0` alapértelmezett rekord helyettesíti (dekompilátum). A `+0x14` 32 bites mezőt olvassa (`mov edx,[eax+0x14]`, `0x00450b1d`), és a 64 bites kimenethez adja: `add [arg3],edx` (`0x00450b27`), `adc [arg3+4],0` (`0x00450b2d`).
- ⚠️ A dekompilátum ezt az összeget a `param_1`-nek (CT) írja. Az asm szerint a harmadik argumentumba (a kimenetbe) megy. Ez a dekompilátum hibája.
- A `+0x14` mező egysége: bájt. Ezt a 38.2.44 §3.5 adja az előző körből, most nem mértem újra.

**§2.4 Az összehasonlítás és az irány (asm, verifikált, mindkét módnál).**
- 1. mód: `fucom st(1)` a két dupla között (`0x004a7e9f`-`0x004a7ea5`). Egyenlőségnél a `0x004a7eeb` ágra megy, onnan a következő kulcs (`0x004a7f5f`).
- 5. mód: az első sor összege a `[esp+0x18]`-ban (alacsony szó `eax`, magas szó `edx`), a másodiké a `[esp+0x20]`-ban (alacsony szó `ecx`, magas szó `esi`). Előjel nélküli összehasonlítás: előbb a magas szó, aztán az alacsony (`0x004a7f26`-`0x004a7f54`). Egyenlőségnél a `0x004a7f59` ág, a következő kulcs.
- Kilépések, mindkét módban azonosak:
  - első < második: `0x004a7dee` (5. mód), `0x004a7eb9` (1. mód). Visszatérés: `+1`, ha `[obj+0x165] = 0`, különben `-1`.
  - első > második: `0x004a7e07` (5. mód), `0x004a7ed2` (1. mód). Visszatérés: `+1`, ha `[obj+0x165] ≠ 0`, különben `-1`.

**§2.5 Mit jelent a két kulcs.**
- 1. mód (`ID_VIEWBYRECENT`, a felületi felirat „legutóbbi változtatás”, 68.1 szerint): a dupla kulcs. A dupla jelentése: U32.
- 5. mód (`ID_VIEWBYSIZE`, a felületi felirat „méret”): a sor elemeinek `+0x14` mezőjének összege. Az egység bájt (38.2.44 §3.5).

**§2.6 ⚠️ Helyesbítések a 38.2.47-ben.**
- A 38.2.47 §2.4 (3. pont, 1. mód) „argumentum nélkül hívja” állítása téves. ECX a sor indexe, EDX a rendező (`0x004a7e89`-`0x004a7e8d`).
- A 38.2.47 §2.1 az `ESI` belépési EAX-ről szóló állítása téves a `0x004b94a0`-ra. Az `mov esi,eax` (`0x004b94b5`) az IAT-hívás (`call [0xc40284]`, `0x004b94af`) után áll. A `0x004b8ee0`-ra (`0x004b8eed`) az állítás igaz, ott a `mov` az IAT-hívás előtt áll.

##### §3 Q3: a `0x00987030` törzse (U25)

**§3.1 A hívóhelyek (asm, verifikált).**
- `0x004a7ad2`: `push 0`. `0x004a7ad4`: `mov ecx,0xc811cc` (`]album`). `0x004a7ad9`: `mov eax,edi` (az első sor). `0x004a7adb`: `call 0x987030`. Majd `0x004a7ae2`-`0x004a7aeb`: ugyanez `mov eax,esi`-vel (a második sor).
- `0x004a7b0b`-`0x004a7b24`: ugyanez `mov ecx,0xc818b8` (`]facealbum`) literállal.

**§3.2 A törzs (dekompilátum, a konvenció asm-ben ellenőrizve).**
- EAX = a sor objektuma. `[EAX]` a szöveg puffere, a szöveg a `+4` címen van.
- ECX = a keresett szöveg. A verem-jelző (`param_2`) 0 esetén az ASCII A-Z betűket kisbetűként kezeli.
- Visszatérés: 1, ha a keresett szöveg a sor szövegének **előtagja**. A sor szövege lehet hosszabb is. Egyébként 0.
- Üres keresett szöveg: 0. Ha a sor puffere nulla, a visszatérés 1 csak akkor, ha a keresett szöveg is nulla.

**§3.3 Következmény.** A `0x004a7890` a BL (első sor) és az AL (második sor) jelzővel dönti el, hogy a sor szövege `]album`- vagy `]facealbum`-kezdetű-e. Hogy ez melyik elemfajtát (kép, album, személy) jelöli, **NINCS MEG**. Ehhez a `0x004a7890` további ágait kell olvasni.

##### §4 Q4: a `0x005fe130` és a `0x004b94a0` (U45)

**§4.1 A hívási lánc (asm, verifikált).**
- `0x005d9ccc`: `mov ebx,[esp+0x14]`. Ez a `0x005d9cc0` első verem-argumentuma, X.
- `0x005da889`: `push ebx`. `0x005da88a`: `call 0x5fe130`. A `0x005fe130` egyetlen hívóhelye ez (HÍVÓK lista).
- `0x005fe130`: `push ebp`, `mov ebp,esp`. `0x005fe13c`: `mov edi,[ebp+8]` (EDI = X). `0x005fe13f`: `mov ecx,[edi+0x2c0]` (ECX = O = `[X+0x2c0]`). Majd `push 0`, `lea eax,[esp+0x14]`, `push eax`, `push ecx`, `call 0x4b94a0` (`0x005fe156`).
- A `0x004b94a0` első verem-argumentuma: `mov edi,[esp+0x54]` (`0x004b94ab`). Ez a `0x005fe130` által átadott O.

**§4.2 Az eredmény.** A `0x005fe130`-nak nincs `this`-e. Egyetlen verem-argumentuma van (X). A `0x004b94a0` első (rendező) argumentuma: O = `[X+0x2c0]`. X a `0x005d9cc0` első argumentuma, és ez a `0x004b07c0` (mód-író) hívójának is ugyanaz a `[X+0x2c0]` objektuma (38.2.47 §3.4).

**§4.3 Ami nincs meg.** A `0x0056c5a0` (a második hívó, `0x0056d2b6`) első verem-argumentuma: **NINCS MEG** (U51). Ghidra-kör kell: `0x0056c5a0 - az első verem-argumentum (a 0x0056d2b6 előtti push-ok). [nem blokkolja a fő utat]`

##### §5 Amit KIZÁRTAM (38.2.48)

- „A `0x00484820` tölti a névtáblát”: **CÁFOLVA** (HÍVOTTAK lista, §1.1).
- „A `0x004da1d0` csak darabszámot állít”: **CÁFOLVA** (§1.2).
- „A `0x004ae0d0` argumentum nélkül hívódik”: **CÁFOLVA** (§2.6).
- „A `0x004b94a0` ESI-je a belépési EAX”: **CÁFOLVA** a `0x004b94a0`-ra (§2.6). A `0x004b8ee0`-ra igaz.
- „A `0x004507e0` a CT mezőjébe összegez”: **CÁFOLVA** (§2.3). A kimenet a harmadik argumentum.
- „A `0x005fe130`-nak `this`-e van”: **CÁFOLVA** (§4.2). Verem-argumentuma van.

##### §6 Ghidra-címek a következő körhöz

- `0x00506830` (U46): törzs, a kimeneti pár és a `this` (`[ebx+0xf8]`).
- `0x00493050` (U47): a `]star` második ágának listaforrása, argumentum `&param_3`.
- `0x004d9aa0` (U52): a `]star` második ága (`0x00458aeb`).
- A `0x00456610` hívói (U49): `0x00468108` (`0x00467ca0`), `0x0047c5fc` (`0x0047c560`), `0x0047c815` (`0x0047c780`), `0x00540568` (`0x0053fe30`), `0x0055eef4` és `0x0055ef45` (`0x0055ece0`). Mindegyiknél a második verem-argumentum forrása.
- A `0x00448560` hívói (U50): `0x00426bfb` (`0x00425f60`), `0x0046d622` (`0x00467ca0`), `0x0047e8ad` és `0x0047e908` (`0x0047e470`), `0x0047fcaa` (`0x0047e930`), `0x00480155` és `0x0048352f` (`0x00480040`), `0x0057dd86` (`0x0057daa0`).
- `0x0056c5a0` (U51): az első verem-argumentum a `0x0056d2b6` előtt.
- A `[owner+0x2e9c]` és a `[owner+0x2e94]` írói (U48): pásztázás kell, a `mov [reg+0x2e9c]` és `mov [reg+0x2e94]` alakokra.
- `0x00450bd0` belső ága (U32), változatlan.

##### §7 Nyitott lista (38.2.48 §9)

Nyitott kérdések mérlege (38.2.48): 52 tétel · 7 lezárva · 22 részben · 23 nincs meg.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U1 | NINCS MEG (változatlan) | a `0x00a6aa00` teljes törzse | `0x00a6aa00` |
| U2 | RÉSZBEN (változatlan) | az obj2 osztálya és a vt+0 cél | `0x005e8a70`, `M+0x4c` vt+0 |
| U3 | RÉSZBEN | a mód-tartó (`obj`, névhasználat) igazolt; az `L` osztálya a 38.2.46 szerint NINCS MEG | `0x004a7890`, `0x004baaa0` |
| U4 | NINCS MEG (változatlan) | a `0x008014d0` vt+0 hívott függvénye | `0x008014d0` |
| U5 | NINCS MEG (változatlan) | a `[this+0x2ec]` olvasói | pásztázás |
| U6 | NINCS MEG (változatlan) | a `0x009aaae0` hívóhelyei | `0x009aaae0` |
| U7 | LEZÁRVA (38.2.41 §1) | a sorrekord `+0x14` írója | - |
| U8 | NINCS MEG (változatlan) | a `P' = [T+0x3a4]` írója | `0x007fa7f0` |
| U9 | LEZÁRVA (38.2.41 §2-3) | a kattintási ág | - |
| U10 | RÉSZBEN (változatlan) | a `0x004b8470` hívója és az `[L+0x148]` írói | `0x004b8ee0` |
| U11 | RÉSZBEN (változatlan) | az `L` osztálya, `+0xc == 2`, `jbe` | `0x004b29d0` |
| U12 | NINCS MEG (változatlan) | az EBP/EBX forrása a hívottakban | `0x004b2e10`, `0x004b3770`, `0x004b80d0` |
| U13 | RÉSZBEN (változatlan) | a `0x007fc010` | `0x007fc010` |
| U14 | RÉSZBEN (változatlan) | a `0x008014d0` törzse | `0x008014d0` |
| U15 | NINCS MEG (változatlan) | a startbutton vt+0x18 | `0x007fa7f0` |
| U16 | RÉSZBEN (38.2.47 §2.4) | a rendező kulcssorrendje igazolt; a G-táblák feltöltése U37 | `0x004a7890`, `0x004baaa0` |
| U17 | NINCS MEG (változatlan) | a `0x004b8d00` | `0x004b8d00` |
| U18 | NINCS MEG (változatlan) | az `E` görbe | `0x005568e0` |
| U19 | NINCS MEG (változatlan) | a rekord-utólagos és a ciklus-utáni lépés | `0x007fa650`, `0x00604480` |
| U20 | NINCS MEG (változatlan) | a kártya-rekord építése | `0x007fa5b0` |
| U21 | LEZÁRVA (38.2.43 §2) | a CSlice konstruktor és a destruktor-lánc | `0x004133e0`, `0x00413490` |
| U22 | RÉSZBEN (változatlan) | a `0x004406f0` a vt+0x2c cél; a `[L+0x48]` vtábla újra nincs igazolva | `0x00402f90`, U36 |
| U23 | LEZÁRVA a törzs (38.2.44 §2) | a sor neve | `0x004a71e0` |
| U24 | RÉSZBEN (38.2.48 §2) | a 4. mód igazolt; az 1. mód kulcsa a `0x00450bd0` dupla (U32); a 0. mód a `G+0x18` tábla (forrása NINCS MEG) | `0x004502e0`, `0x004ae0d0`, `0x004a7890` |
| U25 | LEZÁRVA (38.2.48 §3) | a `0x00987030` törzse: a sor szövege a keresett szöveggel kezdődik-e (ASCII, kis- és nagybetű nem számít) | `0x00987030`, `0x004a7ad4` |
| U26 | NINCS MEG (változatlan) | a K-másolás törzse | `0x00801915`-`0x00801bc4` |
| U27 | NINCS MEG (változatlan) | az `M+0x64c` és `M+0x650` írása | `0x005e8a70` |
| U28 | LEZÁRVA (38.2.45 §1) | a kulcs NÉV | `0x004dca40`, `0x004406f0` |
| U29 | RÉSZBEN (38.2.45 §2) | a `[X+0x1034]` CThumbDB írója LEZÁRVA; az `L` írója U36 | `0x00402f90`, U36 |
| U30 | RÉSZBEN (38.2.45 §4) | a G-szerep LEZÁRVA; a táblák feltöltése U37 | `0x004b94a0`, U37 |
| U31 | RÉSZBEN (38.2.46 §3.2) | a bemenet igazolt; a statisztika neve NINCS MEG | `0x00450100` |
| U32 | NINCS MEG (változatlan) | az 1. mód összesítője (a `0x00450bd0` dupla tartalma) | `0x00450bd0` belső ága |
| U33 | RÉSZBEN (38.2.47 §3.3) | a mód forrása parancs-ágankénti konstans (0, 1, 2, 3, 5); a 6. ág megfordítja az irányt; a parancsazonosító és az ág párosítása NINCS MEG | `0x005cb990` (6 hely), `0x005d9cc0` (2 hely), `0x004b07c0` |
| U34 | NINCS MEG (változatlan) | az OLEAUT32 184. sorszám neve | IAT `0x00c405c8` |
| U35 | RÉSZBEN (38.2.46 §1.3) | a literál szövege `token`; a rekord `+5` mezőjének tartalma NINCS MEG | `0x00415790`, `0x00985ff0`, `0x004941f0` |
| U36 | RÉSZBEN (38.2.47 §3.5) | az `[X+0x2c0]` a mód-tartó (ha `X = V`); a CThumbDB-tartó az `[obj+0xc4]`; az `X = V` NINCS MEG (U43) | `0x004b07c0`, `0x005d30f0`, `0x004502e0` |
| U37 | RÉSZBEN (38.2.47 §2.2) | a G-veremszerkezetet a hívó állítja be (`0x004b9735`, `0x004b9150`); a tartalmának feltöltése NINCS MEG | `0x004b94a0`, `0x004b8ee0` |
| U38 | LEZÁRVA (38.2.46 §2.2; a sorrend 38.2.47 §2.4) | egyesítő rendezés; a kulcsot a `0x004a7890` adja | `0x004baaa0`, `0x004a7890` |
| U39 | RÉSZBEN (38.2.47 §2.1) | az `obj` a hívó `this`-e; a `0x004b8ee0` `this`-e `[V+0x2c0]`; a `0x004b94a0` első argumentuma O = `[X+0x2c0]` (38.2.48 §4) | `0x004b8ee0`, `0x006dc4c0`, `0x005fe130` |
| U40 | RÉSZBEN (38.2.48 §1.3) | a név-tábla írói igazoltak (`0x00456610` négy helyen, `0x00448560` egy helyen); az elemek fajtája és az azonosító forrása NINCS MEG (U49, U50) | `0x00456610`, `0x00448560`, `0x004da1d0` |
| U41 | RÉSZBEN (38.2.48 §1.1) | a `0x00484820` nem író; a `0x00449a00` bemenetét a `0x00506830` építi (U46) | `0x00484820`, `0x00484bbd` |
| U42 | RÉSZBEN (38.2.48 §1.3) | az írók megvannak; az azonosító (`param_3`) forrása NINCS MEG | `0x00456610`, `0x00448560` |
| U43 | NINCS MEG (változatlan) | az `X` azonos-e a `V = [[0xd67668]+0x102c]`-vel | `0x005cb9aa`, `0x004b07e8`, `0x006dc4c0` |
| U44 | RÉSZBEN (38.2.48 §2) | mindkét kulcs mechanikája LEZÁRVA (ECX és EDX, FPU-összehasonlítás, 64 bites összeg, irány); a dupla tartalma U32; a `+0x14` egysége az előző körből | `0x004ae0d0`, `0x004507e0` |
| U45 | RÉSZBEN (38.2.48 §4) | a `0x005fe130` hívója LEZÁRVA (O = `[X+0x2c0]`); a `0x0056c5a0` NINCS MEG (U51) | `0x005fe130`, `0x0056c5a0` |
| U46 (új) | NINCS MEG | a `0x00506830` törzse: a `0x00449a00` bemeneti tömbjének és darabszámának építője | `0x00506830`, `0x00484a70` |
| U47 (új) | NINCS MEG | a `0x00493050` törzse (a `]star` második ág, argumentum `&param_3`) | `0x00493050`, `0x0045a8a6` |
| U48 (új) | NINCS MEG | a `[owner+0x2e9c]` és a `[owner+0x2e94]` név írói, és a viszonyuk | `0x004489dc`, `0x00449a00` |
| U49 (új) | NINCS MEG | a `0x00456610` hívóinak második verem-argumentuma (`param_3`) | `0x00468108`, `0x0047c5fc`, `0x0047c815`, `0x00540568`, `0x0055eef4`, `0x0055ef45` |
| U50 (új) | NINCS MEG | a `0x00448560` hívóinak `param_1` és `param_3` forrása | `0x00426bfb`, `0x0046d622`, `0x0047e8ad`, `0x0047e908`, `0x0047fcaa`, `0x00480155`, `0x0048352f`, `0x0057dd86` |
| U51 (új) | NINCS MEG | a `0x0056c5a0` első verem-argumentuma (a `0x004b94a0` hívója) | `0x0056d2b6`, `0x0056c5a0` |
| U52 (új) | NINCS MEG | a `0x004d9aa0` törzse (a `]star` második ága, `0x00458aeb`) | `0x004d9aa0`, `0x00458aeb` |

**A felhasználó szemével**

Nincs két-három mondatos összefoglaló, mert az első kérdés nem dőlt el. A névtábla két kulcsának (`]star`, `]hidden`) írói megvannak, de a listákba került azonosító fajtája NINCS MEG. Hiányzó címek: `0x00506830` (a `0x00484820` tömbje), `0x00493050` (a `0x00456610` `]star` második ágának listája), és a `0x00456610` hívóinak második argumentuma (`0x00468108`, `0x0047c5fc`, `0x0047c815`, `0x00540568`, `0x0055eef4`, `0x0055ef45`).

#### 38.2.49 Az Időrend bináris feltárása, 32. kör: a név-tábla elemei, a 0x4d9aa0, a 0x450bd0 és a 0x56c5a0 hívása (#5401, 2026-10-21)

**Válasz röviden.**
1. **Q1, az elem fajtája (U46, U47, U49, U50): NINCS MEG.** A két fő hívóúton (0x467ca0 és 0x425f60) a 0x448560 `param_4` jelzője 0, és ilyenkor a függvény a lista-írás előtt visszatér. Tehát ezen az úton nem kerül elem a `[owner+0x2e9c]` listába. A 0x467ca0 egyetlen 0x456610-hívása (0x468108) a `param_3`-at a 0x4e5740 visszatérési értékéből kapja. Hogy ez kép, album vagy személy: NINCS MEG.
2. **Q2, a 0x4d9aa0 törzse (U52): LEZÁRVA.** Egy név alá fűzi a kapott egész számokat. Ha a név még nincs a táblában, új rekordot hoz létre.
3. **Q3, az 1. mód dupla (U32): RÉSZBEN.** A sor elemeinek 64 bites rekord-mezőjéből a legnagyobbat veszi, és azt dupla számként adja vissza. A 64 bites érték jelentése NINCS MEG.
4. **Q4, a 0x56c5a0 első verem-argumentuma a 0x4b94a0 hívásakor (U51): LEZÁRVA.** A 0x4b94a0 első verem-argumentuma `[X+0x2c0]`, ahol X a 0x56c5a0 első argumentuma. Ez a 0x005fe130 (U45) hívásával egyezik.
5. **A felhasználó szemével:** nincs két-három mondatos összefoglaló, mert Q1 nem dőlt el. A hiányzó címek az §5-ben vannak.

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-32.txt` hét címe (0x00506830, 0x00493050, 0x004d9aa0, 0x00450bd0, 0x0056c5a0, 0x00467ca0, 0x00425f60). A 0x00448560 és a 0x00456610 fejléce a `2026-10-21-idorend-31.txt`-ben van. Az asm `pe_dis.cdis`-szel készült. A második paraméter bájt, nem utasításszám (38.2.48). A hívóhelyek verem-argumentumait a push-sorrendből számoltam. A Ghidra-hívások a `this` (ECX) argumentumot nem írják ki, ezért a kiírt argumentumok a verem-argumentumok. Kódot nem módosítottam, ezért a CI-őrök nem futottak. Ideiglenes fájl nem készült, a `.bt/` nem kellett. Commit, push, PR, jegy, címke és cron nincs.

**Bizonyítottsági fok.** Az asm-ből igazolt állítás erős, a címét megadom. A dekompilátumból jövő állítást **(dekompilátum)** jelölöm. Ha a kettő eltér, az asm az irányadó.

**Névhasználat.** `owner`: a 0x00448560 és a 0x00456610 első verem-argumentuma (`param_2`). `X`: a 0x0056c5a0 első argumentuma (`param_1`). `Z`: a rendező `+0xc4` mezője (38.2.48 §2.2). `uVar17` és `local_4`: a 0x467ca0 belső indexe, lásd §1.4.

##### §1 Q1: az elem fajtája (U46, U47, U49, U50)

**§1.1 A 0x00493050 (U47): LEZÁRVA.**
- Törzs (dekompilátum, a fő lépések asm-mel egyeznek): a lista-objektum (ESI) első két szava nulla lesz. A `FUN_0097c810(0,4)` egy 4 bájtos blokkot ad. Ha ez sikerül, a blokk első helyére `*param_1` kerül, a darabszám 1 lesz. Ez egyelemű lista. Az elem a verem-argumentum által mutatott szó.
- Visszatérési érték: nincs (`void`). A 38.2.48 §1.3 táblájának „visszatérése" szava téves, ezt javítottam (§7).
- Hívók: 19 hely. A 0x00456610 `]star` második ágában a hívás (0x0045a8a6) `param_1 = &param_3`. Ebből az következik, hogy a `]star` második ágának listaeleme a 0x00456610 `param_3`-a.

**§1.2 A 0x00506830 (U46): RÉSZBEN, ⚠️ LEZÁRVA a 38.2.50 §1-ben.**
- Belépés: EAX = objektum. A 0x484a70-ben ez `lea eax,[ebx+0xf8]` (cím, nem a tárolt érték; ⚠️ JAVÍTVA 38.2.50 §7), a 0x467ca0-ban helyi objektum. Két verem-argumentum van: az első (`[esp+4]`) az index (`param_1`), a második (`[esp+8]`) a kimeneti pár címe. A `ret 8` (asm: 0x005068cb, 0x005068ec, 0x005068ff, 0x00506923) ezt igazolja. A 0x484a5c-0x484a61 push-sorrend: előbb a pár címe (`lea eax,[esp+0x34]`), utána az index (`push ebp`).
- A törzs (dekompilátum): ha az index kisebb, mint `[obj+0x3f4]>>1`, akkor az elem a `[obj+0x3f0]` tömb megfelelő mutatója. Ha ez nulla, az alapértelmezett elem `obj+0x3f8`. Erre a `FUN_00891110(elem+0x24)` hívás fut. Egyébként nem hív. Zárolás: kritikus szakasz, vagy a `vt+0x18`, illetve a `vt+0x1c` ág, ha az `obj+0xc` bájt nulla. A visszatérési érték 0 vagy 4.
- Ami nincs meg: a második verem-argumentum (a kimeneti pár) tartalmát a dekompilátum nem használja. ⚠️ LEZÁRVA (38.2.50 §1): a `0x00891110` a kimeneti pár címét kapja EAX-ben, és oda másolja a listát. Ghidra-kör kell: `0x00891110 - az első argumentum és az írás; 0x00506830 - a második verem-argumentum (esp+8) használata a törzsben. [blokkoló a 0x484820 tömbjénél]`

**§1.3 Az elem a 0x00456610 hívóiban (U49): RÉSZBEN.**
- A 0x467ca0 hívása, cím 0x00468108 (asm, verifikált 0x004680de-0x00468108):
  - `lea ecx,[esp+0x3e0]; push ecx; mov eax,esi; call 0x4e5740` (0x004680de-0x004680e8). Az eredmény EAX-ben, és `puVar10`-ként megy tovább (`mov [esp+0x10],eax`, 0x004680f1).
  - A hívás csak akkor fut, ha `[esp+0x48] = 0` (`uStack_7e78 == 0`): `cmp dword ptr [esp+0x48],ebp; jne 0x46810d` (0x004680ed-0x004680f5).
  - A verem-argumentumok belépési sorrendben: `param_2` = `&abStack_7bd8` (a tulajdonos, helyi objektum), `param_3` = `puVar10` (EAX), `param_4` = 3, `param_5` = 0, `param_6` = 0. A `xor ecx,ecx` (0x00468104) miatt ECX = 0 (a `this` itt nulla).
- Tehát ennél a hívásnál a lista-elem (`param_3`) a 0x004e5740 visszatérési értéke. Hogy ez kép, album vagy személy: NINCS MEG.
- A többi hívó (0x0047c5fc, 0x0047c815, 0x00540568, 0x0055eef4, 0x0055ef45): NINCS MEG ebben a körben.

**§1.4 A 0x00448560 hívói a két fő útban (U50): RÉSZBEN.**
A két hívásnál a `param_4` 0. Ez a döntő.

- (a) A 0x00467ca0 hívása, cím 0x0046d622 (asm, verifikált 0x0046d5b8-0x0046d622):
  - Verem-argumentumok: `push ebp` (param_4), `push ebx` (param_3), `push edi` (param_2). Ebből `param_2` = EDI = `pbStack_7ea4` (a tulajdonos), `param_3` = EBX = `uVar17`, `param_4` = EBP = 0.
  - `ebp` nulla: `xor ebp,ebp` (0x0046d4f6), azután nincs `ebp`-író a lineáris kódban 0x0046d622-ig. Elágazási útvonalakat nem vizsgáltam.
  - ECX = a `param_1` (this): egy 4 szavas helyi szerkezet, amelyet a négy `mov [esp+0xd4..0xe0],ebp` nullázott. A 0x448560 ezt rectként olvassa (dekompilátum: `*param_1`, `param_1[1..3]`, sorok 5306-5332 a `-31.txt`-ben).
  - `uVar17` = a `[esp+0x7ebc]` szó (`mov ebx,[esp+0x7ebc]`, 0x0046d59a). ⚠️ KÉTSÉGES (38.2.50 §5). Az EBX ezután nem változik, amíg a `push ebx` (0x0046d5bb) nem viszi a verembe. Közben van egy `call 0x4613c0` (0x0046d5a7). Azt nem néztem meg, hogy a hívott függvény megőrzi-e az EBX-et. Ez a 0x467ca0 belső ciklusának indexe. A Ghidra a `local_4` nevet adja neki. A ciklus a `[pbVar15+0x1bb8]` objektum bájt-tömbjét járja be (darabszám `+0x4c>>1`, adat `+0x48`), a dekompilátum 5885-6092. sorai szerint (dekompilátum).
  - A 0x448560 belsejében: a `FUN_00447800(owner, index, uVar5)` hívás abban az ágban van, amely a `param_4 == 0` vizsgálat előtt következik (dekompilátum, `-31.txt` 5511-5512. sor). Ha `param_4 == 0`, a függvény 0-val tér vissza, és nem ír a `[owner+0x2e9c]` listába.
  - Tehát ezen az úton az index csak a `FUN_00447800`-nak megy át. A `FUN_00447800` törzse: NINCS MEG.
- (b) A 0x00425f60 hívása, cím 0x00426bfb (asm, verifikált 0x00426bc0-0x00426bfb):
  - `xor eax,eax` (0x00426bcf), utána `push eax` (0x00426bd1): `param_4` = 0.
  - Verem-argumentumok: `push eax`, `push esi`, `push ebx`. Ebből `param_2` = EBX (Ghidra: `piVar25`, a tulajdonos), `param_3` = ESI = `[ebp+0xc]`, azaz a 0x425f60 második argumentuma. Ezt a 0x467ca0 a 0x0046d5bd hívásban `uVar17`-ként adja át.
  - ECX = a helyi szerkezet, négy szó: {0, 0, 0, 1} (`mov [esp+0xc8],1`, 0x00426bf0).
  - A jelző 0, tehát ez az út sem ír listát.
- (c) Ami nincs meg: a többi hívó (0x0047e8ad, 0x0047e908, 0x0047fcaa, 0x00480155, 0x0048352f, 0x0057dd86). Ezeknél a `param_1`, a `param_3` és a `param_4` forrása NINCS MEG. Lehet köztük 1 értékű `param_4`, ott volna lista-írás.

**§1.5 Ami nincs meg, összegyűjtve (Q1 válasza).**
- Az elem fajtája (kép, album, személy): NINCS MEG.
- Igazolt: a 0x467ca0 és a 0x425f60 útjában a 0x448560 nem ír listát, mert `param_4` = 0. A 0x456610 hívás (0x468108) elemét a 0x004e5740 adja.
- Ghidra-kör kell: `0x004e5740 - a visszatérési érték (puVar10) és az auStack_7ae0 kimenet; az EAX-ben kapott objektum (ESI, lea esi,[esp+0x29c]). [blokkoló Q1-nél]`
- Ghidra-kör kell: `0x00447800 - a (owner, index, uVar5) hívás hatása. [blokkoló a személy-kérdésnél: ebből látszik, mihez tartozik az index]`
- Ghidra-kör kell: `0x00467ca0 - a [esp+0x7ebc] szó írói. Statikus keresésben nincs közvetlen írás (34 előfordulás, mind olvasás, cmp vagy lea). A Ghidra ugyanezt a nevet adja a biztonsági sütinek (`DAT_00d24004 ^ ...`) is, ezért az író nem egyértelmű. [blokkoló: az index eredete]`

##### §2 Q2: a 0x004d9aa0 törzse (U52): LEZÁRVA (dekompilátum)

- Bemenet: EAX = a név-objektum (`[EAX]` a puffer, a szöveg `+4`-nél). `param_1` = a név-tábla. A 38.2.48 szerint ez `owner+0x68`, a hívóhelyet (0x00458aeb) most nem néztem meg. `param_2` = a lista-pár (adat-mutató, darabszám<<1 | jelző). `param_3` = jelző: ha nem nulla, minden elemre hívja a `FUN_00a59000`-t. `param_4` = jelző: ha nem nulla, és volt elem, a `FUN_004db8f0(rekord, param_4)` hívás fut.
- Lépések:
  1. Üres név (nincs puffer, vagy az első karakter nulla): visszatér 0-val, nincs írás.
  2. A tábla zárolása (kritikus szakasz, vagy `vt+0x18`).
  3. Keresés: a vödröt a `FUN_004de1a0` adja, a láncban `__stricmp` (kis- és nagybetű nem számít).
  4. Találat: `FUN_0074cf40()`. Ha ez nem nulla, a függvény azzal tér vissza, és nem fűz. Ha nulla, a meglevő rekordhoz fűz.
  5. Nincs találat: `FUN_00411150` készíti a név-objektumot (0 esetén -1-gyel tér vissza). Új csomópont: +0 lánc, +4 név, +8 adat-mutató, +0xc darabszám<<1 | jelző. A csomópontot a vödör elejére teszi, a tábla elemszáma nő.
  6. Fűzés, minden `param_2`-beli `e` elemre: (a) ha `param_3` nem nulla, `FUN_00a59000(&e, &local_18)`; (b) `e` a rekord listájának végére kerül, ha a jelző bit nulla; a kapacitást kettes hatványonként növeli (`FUN_0097c810`, `FUN_0097caf0`); (c) `param_1[0x1e] = max(param_1[0x1e], e+1)`.
- Duplikáció-szűrés nincs: az új elemeket nem hasonlítja a régiekhez. A régi elemeket nem írja át. (Ez különbözik a 38.2.48 §1.2-ben leírt 0x004da1d0-tól.)
- Ami nincs meg: a `param_1[0x1e]` szerepe (az `e+1` maximuma), a `FUN_0074cf40` feltétele, a `FUN_00a59000` és a `FUN_004db8f0` törzse. Ezek nem a fő kérdés részei, ezért nem vettem fel külön tételként.

##### §3 Q3: az 1. mód dupla, a 0x00450bd0 (U32): RÉSZBEN (dekompilátum)

- Hívás: a 0x004ae0d0-ból (0x004ae0de). Az első verem-argumentum (`param_1`) a sor indexe, a második (`param_2`) a kimeneti dupla címe (a push-sorrend: előbb a cím, utána az index). `Z` = EAX = `[rendező+0xc4]`.
- Lépések:
  1. `*param_2 = 0`.
  2. A `[Z+0x48]` alobjektum `vt+0x2c` hívása (38.2.44 szerint ez a 0x004406f0) visszaadja a sor elemeinek listáját. A lista darabszáma `[+4]>>1`, adata `[+0]`. Hiba esetén a hibakóddal tér vissza.
  3. Gyorsítótár: a `[Z+0x2eb8]` tömb 16 bájtos elemekből áll (kulcs dword a +0-n, dupla a +8-on). Darabszám `[Z+0x2ebc]>>1`. Ha a sor indexénél a kulcs (a `FUN_006c9d60` eredménye) egyezik, a gyorsítótárban levő dupla a kimenet, és nincs újraszámítás.
  4. Számítás: minden `e` listaelemre a rekord `[Z+0x4e8][e]`, vagy ha ez nulla, a `Z+0x4f0` alapértelmezett rekord. A rekord +4 mezője az alsó szó, a +8 mezője a felső szó egy 64 bites értékben. A függvény a legnagyobbat tartja meg: előbb a felső szó, aztán az alsó szó szerint.
  5. A legnagyobb érték után a `FUN_0098b650` egy x87-es értéket ad vissza. Ezt a dekompilátum dupla számként írja a kimenetbe és a gyorsítótárba. Hogy a `FUN_0098b650` pontosan mit csinál a 64 bites értékkel: NINCS MEG.
- Ami nincs meg:
  - A 64 bites érték jelentése. A `[Z+0x4e8]` rekord írója kell. A mód neve („legutóbbi változtatás") erre utal, de ez nincs igazolva.
  - A `FUN_0098b650` törzse (64 bites érték → dupla átalakítás). Ghidra-kör kell: `0x0098b650`.
  - A `FUN_006c9d60` törzse, azaz a gyorsítótár kulcsa. Ghidra-kör kell: `0x006c9d60`.
  - A `vt+0x2c` listája, azaz hogy a sor mely elemei kerülnek bele. A 38.2.44 szerint ez a 0x004406f0, most nem néztem újra.

##### §4 Q4: a 0x0056c5a0 első verem-argumentuma a 0x004b94a0 hívásakor (U51): LEZÁRVA

- A hívás (asm, verifikált 0x0056d299-0x0056d2b6): `mov esi,[esp+0xd8]` (0x0056d299), `mov ecx,[esi+0x2c0]` (0x0056d2a0), `push 1` (0x0056d2a6), `lea eax,[esp+0x40]; push eax` (0x0056d2a8-0x0056d2ac), `push ecx` (0x0056d2ad), `call 0x4b94a0` (0x0056d2b6).
- Tehát a 0x4b94a0 első verem-argumentuma `[ESI+0x2c0]`. A második az `&uStack_a8` (a helyi szám), a harmadik 1.
- ESI = X = a 0x0056c5a0 első argumentuma. Igazolás: a prológus (`sub esp,0xc4`, négy `push`) után az `[esp+0xd8]` a `param_1`. Ezt az `mov eax,[esp+0xd8]` (0x0056c5bd) és az utána következő `cmp dword ptr [eax+0x34a4],0` (0x0056c5c4) mutatja. A 0x0056c5bd és a 0x0056d299 között gépi kereséssel nincs `push` és `pop`. Csak `add esp` takarítás van hívások után. Ezért az `[esp+0xd8]` ugyanaz a szó.
- A Ghidra `local_c` nevet ad az ESI-nek. A dekompilátum ezt a változót sehol nem értékeli, de ugyanarra az objektumra utal, mint a `param_1`.
- Ezzel a 0x005fe130 hívása (U45) is zárul: O = `[X+0x2c0]` a 0x004b94a0 mindkét hívójánál.
- Ami nincs meg: X forrása a 0x0056c5a0 két hívójánál (0x0056f418 a 0x0056e1c0-ban, 0x005e7c99 a 0x005e7c20-ban). Ez nem a fő kérdés, ezért nem vettem fel külön tételként.

##### §5 A felhasználó szemével

Nincs két-három mondatos összefoglaló, mert Q1 nem dőlt el. Hiányzó címek:
- `0x004e5740`: a 0x468108 hívás elemének forrása (U49).
- `0x00447800`: a 0x448560 flag-0 ágában hívott függvény. Ebből derülhet ki, hogy a 0x448560 indexe személy-e vagy kép (U50).
- `0x00467ca0` `[esp+0x7ebc]` írói: az index eredete (U49, U50).
- `0x00891110` és a `0x00506830` kimeneti párja (U46).

##### §6 Ghidra-címek a következő körhöz

- `0x004e5740` (U49, blokkoló): visszatérési érték és az `auStack_7ae0` kimenet; az EAX-ben kapott objektum (ESI = `esp+0x29c`).
- `0x00447800` (U50): mit ír a (owner, index, uVar5) hívás.
- `0x00467ca0` `[esp+0x7ebc]` írói (U49, U50): a ciklusindex eredete, és a `[pbVar15+0x1bb8]` objektum osztálya.
- `0x0047c560`, `0x0047c780`, `0x0053fe30`, `0x0055ece0` (U49): a többi 0x456610-hívó `param_3` forrása.
- `0x0047e470`, `0x0047e930`, `0x00480040`, `0x0057daa0` (U50): a többi 0x448560-hívó `param_1`, `param_3` és `param_4` forrása.
- `0x00891110` (U46): LEZÁRVA (38.2.50 §1).
- `0x0098b650`, `0x006c9d60` (U32): 64 bites → dupla átalakítás; a gyorsítótár kulcsa.
- `0x0056f418`, `0x005e7c99` (U51 mellett): X forrása.

##### §7 Javítások a 38.2.48-ban (⚠️ JAVÍTVA)

- 38.2.48 §1.1 („a kulcs (verem 1)"): JAVÍTVA. A verem 1 index, nem kulcs. A `ret 8` és a push-sorrend ezt mutatja (§1.2).
- 38.2.48 §1.3 táblája, 0x0045a8b8 sor („`0x00493050(&param_3)` visszatérése"): JAVÍTVA. A 0x00493050 nem ad vissza értéket (`void`), a listát az ESI-ben építi (§1.1).
- 38.2.48 §4.3 („a 0x0056c5a0 első verem-argumentuma: NINCS MEG"): LEZÁRVA (§4).
- 38.2.48 §2.2 és §7 (U32 „NINCS MEG"): RÉSZBEN (§3).
- 38.2.48 §7 (U47 „NINCS MEG"): LEZÁRVA (§1.1).
- Más állítást ebben a körben nem találtam tévesnek. A 38.2.48 §1.3-ban a 0x00448560 `param_4`-feltétele (0 esetén nincs lista-írás) megerősítést kapott (§1.4).

##### §8 Amit KIZÁRTAM

- „A 0x00493050 visszatérési értéket ad": CÁFOLVA, `void`.
- „A 0x00448560 hívóinál a `param_3` a lista-írásba kerül a 0x467ca0-ban": CÁFOLVA. A `param_4` 0, tehát nincs lista-írás.
- „A 0x00506830 első verem-argumentuma a kulcs": CÁFOLVA. Az index.
- „A 0x004d9aa0 a régi elemeket írja át": CÁFOLVA. Csak a bemeneti lista elemeit fűzi.
- „Az 1. mód dupla a legutóbbi változtatás időpontja": NINCS MEG. A név sugallja, de nem igazolt.

##### §9 Nyitott lista (38.2.49 §9, felülírva: lásd 38.2.50 §9)

Nyitott kérdések mérlege (38.2.49): 52 tétel · 11 lezárva · 25 részben · 16 nincs meg.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U1 | NINCS MEG (változatlan) | a `0x00a6aa00` teljes törzse | `0x00a6aa00` |
| U2 | RÉSZBEN (változatlan) | az obj2 osztálya és a vt+0 cél | `0x005e8a70`, `M+0x4c` vt+0 |
| U3 | RÉSZBEN (változatlan) | a mód-tartó (`obj`, névhasználat) igazolt; az `L` osztálya NINCS MEG | `0x004a7890`, `0x004baaa0` |
| U4 | NINCS MEG (változatlan) | a `0x008014d0` vt+0 hívott függvénye | `0x008014d0` |
| U5 | NINCS MEG (változatlan) | a `[this+0x2ec]` olvasói | pásztázás |
| U6 | NINCS MEG (változatlan) | a `0x009aaae0` hívóhelyei | `0x009aaae0` |
| U7 | LEZÁRVA (38.2.41 §1) | a sorrekord `+0x14` írója | - |
| U8 | NINCS MEG (változatlan) | a `P' = [T+0x3a4]` írója | `0x007fa7f0` |
| U9 | LEZÁRVA (38.2.41 §2-3) | a kattintási ág | - |
| U10 | RÉSZBEN (változatlan) | a `0x004b8470` hívója és az `[L+0x148]` írói | `0x004b8ee0` |
| U11 | RÉSZBEN (változatlan) | az `L` osztálya, `+0xc == 2`, `jbe` | `0x004b29d0` |
| U12 | NINCS MEG (változatlan) | az EBP/EBX forrása a hívottakban | `0x004b2e10`, `0x004b3770`, `0x004b80d0` |
| U13 | RÉSZBEN (változatlan) | a `0x007fc010` | `0x007fc010` |
| U14 | RÉSZBEN (változatlan) | a `0x008014d0` törzse | `0x008014d0` |
| U15 | NINCS MEG (változatlan) | a startbutton vt+0x18 | `0x007fa7f0` |
| U16 | RÉSZBEN (változatlan) | a rendező kulcssorrendje igazolt; a G-táblák feltöltése U37 | `0x004a7890`, `0x004baaa0` |
| U17 | NINCS MEG (változatlan) | a `0x004b8d00` | `0x004b8d00` |
| U18 | NINCS MEG (változatlan) | az `E` görbe | `0x005568e0` |
| U19 | NINCS MEG (változatlan) | a rekord-utólagos és a ciklus-utáni lépés | `0x007fa650`, `0x00604480` |
| U20 | NINCS MEG (változatlan) | a kártya-rekord építése | `0x007fa5b0` |
| U21 | LEZÁRVA (38.2.43 §2) | a CSlice konstruktor és a destruktor-lánc | `0x004133e0`, `0x00413490` |
| U22 | RÉSZBEN (változatlan) | a `0x004406f0` a vt+0x2c cél; a `[L+0x48]` vtábla újra nincs igazolva | `0x00402f90`, U36 |
| U23 | LEZÁRVA a törzs (38.2.44 §2) | a sor neve | `0x004a71e0` |
| U24 | RÉSZBEN (38.2.48 §2) | a 4. mód igazolt; az 1. mód dupla a `0x00450bd0` (U32); a 0. mód a `G+0x18` tábla (forrása NINCS MEG) | `0x004502e0`, `0x004ae0d0`, `0x004a7890` |
| U25 | LEZÁRVA (38.2.48 §3) | a `0x00987030` törzse | `0x00987030`, `0x004a7ad4` |
| U26 | NINCS MEG (változatlan) | a K-másolás törzse | `0x00801915`-`0x00801bc4` |
| U27 | NINCS MEG (változatlan) | az `M+0x64c` és `M+0x650` írása | `0x005e8a70` |
| U28 | LEZÁRVA (38.2.45 §1) | a kulcs NÉV | `0x004dca40`, `0x004406f0` |
| U29 | RÉSZBEN (38.2.45 §2) | a `[X+0x1034]` CThumbDB írója LEZÁRVA; az `L` írója U36 | `0x00402f90`, U36 |
| U30 | RÉSZBEN (38.2.45 §4) | a G-szerep LEZÁRVA; a táblák feltöltése U37 | `0x004b94a0`, U37 |
| U31 | RÉSZBEN (38.2.46 §3.2) | a bemenet igazolt; a statisztika neve NINCS MEG | `0x00450100` |
| U32 | RÉSZBEN (38.2.49 §3, új) | a `0x00450bd0` 64 bites maximum-számítása igazolt; a 64 bites érték jelentése, a `0x0098b650` és a `0x006c9d60` NINCS MEG | `0x00450bd0`, `0x0098b650`, `0x006c9d60` |
| U33 | RÉSZBEN (38.2.47 §3.3) | a mód forrása parancs-ágankénti konstans; a parancsazonosító és az ág párosítása NINCS MEG | `0x005cb990`, `0x005d9cc0`, `0x004b07c0` |
| U34 | NINCS MEG (változatlan) | az OLEAUT32 184. sorszám neve | IAT `0x00c405c8` |
| U35 | RÉSZBEN (38.2.46 §1.3) | a literál szövege `token`; a rekord `+5` mezőjének tartalma NINCS MEG | `0x00415790`, `0x00985ff0`, `0x004941f0` |
| U36 | RÉSZBEN (38.2.47 §3.5) | az `[X+0x2c0]` a mód-tartó (ha `X = V`); az `X = V` NINCS MEG (U43) | `0x004b07c0`, `0x005d30f0`, `0x004502e0` |
| U37 | RÉSZBEN (38.2.47 §2.2) | a G-veremszerkezetet a hívó állítja be; a tartalmának feltöltése NINCS MEG | `0x004b94a0`, `0x004b8ee0` |
| U38 | LEZÁRVA (38.2.46 §2.2) | egyesítő rendezés; a kulcsot a `0x004a7890` adja | `0x004baaa0`, `0x004a7890` |
| U39 | RÉSZBEN (38.2.47 §2.1) | az `obj` a hívó `this`-e; a `0x004b94a0` első argumentuma O = `[X+0x2c0]` (38.2.49 §4) | `0x004b8ee0`, `0x006dc4c0`, `0x005fe130` |
| U40 | RÉSZBEN (38.2.48 §1.3) | a név-tábla írói igazoltak; az elemek fajtája NINCS MEG (U49, U50) | `0x00456610`, `0x00448560`, `0x004da1d0` |
| U41 | RÉSZBEN (38.2.48 §1.1) | a `0x00484820` nem író; a bemeneti tömböt a `0x00506830` építi (U46) | `0x00484820`, `0x00484bbd` |
| U42 | RÉSZBEN (38.2.48 §1.3) | az írók megvannak; az azonosító (`param_3`) forrása a 0x467ca0 és a 0x425f60 útjában az index, de a fajtája NINCS MEG | `0x00456610`, `0x00448560` |
| U43 | NINCS MEG (változatlan) | az `X` azonos-e a `V = [[0xd67668]+0x102c]`-vel | `0x005cb9aa`, `0x004b07e8`, `0x006dc4c0` |
| U44 | RÉSZBEN (38.2.48 §2) | mindkét kulcs mechanikája LEZÁRVA; a dupla tartalma U32 | `0x004ae0d0`, `0x004507e0` |
| U45 | LEZÁRVA (38.2.49 §4) | a `0x005fe130` hívója és a `0x0056c5a0` első verem-argumentuma: O = `[X+0x2c0]`; X forrása nincs felvéve külön | `0x005fe130`, `0x0056c5a0` |
| U46 | RÉSZBEN (38.2.49 §1.2, új állapot) | a törzs igazolt (index, zárolás, `FUN_00891110`, `ret 8`); a kimeneti pár tartalma és a `0x00891110` NINCS MEG | `0x00506830`, `0x00484a70`, `0x00891110` |
| U47 | LEZÁRVA (38.2.49 §1.1) | a `0x00493050` egyelemű listát épít (`*param_1`), `void` | `0x00493050`, `0x0045a8a6` |
| U48 | NINCS MEG (változatlan) | a `[owner+0x2e9c]` és a `[owner+0x2e94]` név írói, és a viszonyuk | `0x004489dc`, `0x00449a00` |
| U49 | RÉSZBEN (38.2.49 §1.3, új állapot) | a `0x468108` elemének forrása a `0x004e5740` visszatérése; a többi hívó és a fajta NINCS MEG | `0x00468108`, `0x004e5740`, `0x0047c5fc`, `0x0047c815`, `0x00540568`, `0x0055eef4`, `0x0055ef45` |
| U50 | RÉSZBEN (38.2.49 §1.4, új állapot) | a 0x425f60 és a 0x467ca0 útja igazolt: a `param_4` 0, nincs lista-írás; a többi hívó NINCS MEG | `0x00426bfb`, `0x0046d622`, `0x0047e8ad`, `0x0047e908`, `0x0047fcaa`, `0x00480155`, `0x0048352f`, `0x0057dd86` |
| U51 | LEZÁRVA (38.2.49 §4) | a `0x004b94a0` első verem-argumentuma `[X+0x2c0]`, X a `0x0056c5a0` első argumentuma | `0x0056d2b6`, `0x0056c5a0` |
| U52 | LEZÁRVA (38.2.49 §2) | a `0x004d9aa0` törzse: név alá fűzés, új rekord, `param_1[0x1e]` maximum | `0x004d9aa0`, `0x00458aeb` |

**A felhasználó szemével**

Nincs két-három mondatos összefoglaló, mert Q1 nem dőlt el. A hiányzó címek: `0x004e5740` (a 0x468108 elemének forrása), `0x00447800` (a 0x448560 flag-0 ágának hívott függvénye) és a `0x00467ca0` `[esp+0x7ebc]` írói.

#### 38.2.50 Az Időrend bináris feltárása, 33. kör: a kimeneti pár, a `]star` lista és a verem-keret (#5401, 2026-10-21)

**Válasz röviden.**
1. **Q1, a `0x00506830` (U46): LEZÁRVA.** A törzs igazolt. A második verem-argumentum (`[esp+8]`) a kimeneti pár címe. Ha az index a darabszámon belül van, a `0x00891110` átmásolja a listát a párba. A `this` nem a `[ebx+0xf8]` tartalma, hanem a cím: `lea eax,[ebx+0xf8]`. A `0x00891110` az első argumentumába nem ír, azt csak olvassa.
2. **Q2, a listába kerülő azonosító (U47, U52): LEZÁRVA.** A `0x00493050` és a `0x004d9aa0` bemenő listájába a `0x00456610` `param_3`-a kerül (`[ebp+0xc]`). Ezt mindkét `]star`-ágban az asm igazolja. Hogy ez kép, album vagy személy: NINCS MEG.
3. **Q3, a `0x004e5740` (U49): RÉSZBEN.** A visszatérési érték az EAX, vagyis a `0x004e5070` eredménye. A kimenet a konténerbe kerül: a visszatérési index helyére a `[elem+0x18]` érték megy. ⚠️ JAVÍTVA (38.2.51 §5): a visszatérési index a `0x004e5070` eredménye (LEZÁRVA); a `0x00467ca0` verem-kerete a 38.2.51 §1-2 szerint oldódott meg.
4. **Q4, a `0x00447800` (U50): RÉSZBEN.** A hívás `(owner, index, flag)` alakú. A függvény az owner tábláját írja. A tábla bővítésekor az új helyeket egyforma értékkel tölti fel. Abból, hogy az index melyik elemhez tartozik, nem látszik semmi: NINCS MEG.
5. **A felhasználó szemével:** nincs két-három mondatos összefoglaló, mert a fő kérdés nem dőlt el. A hiányzó címek a §6-ban vannak.

**Hatókör és módszer.** A bemenet a `2026-10-21-idorend-33.txt` hat címe (`0x00506830`, `0x00493050`, `0x004d9aa0`, `0x004e5740`, `0x00447800`, `0x00891110`). A hívóhelyeket és a közvetlen segédfüggvényeket a `pe_dis.cdis` adta (a második paraméter bájt). A Ghidra nem mutatja a verem-argumentumokat és a `this`-t, ezért a hívási konvenciót az asm-ből számoltam. Kódot nem módosítottam, ezért a CI-őrök nem futottak. Az ideiglenes fájl a `.bt/` alatt volt, a kör végén törölve. Commit, push, PR, jegy, címke és cron nincs.

**Bizonyítottsági fok.** Az asm-ből igazolt állítás erős, a címét megadom. A dekompilátumból jövő állítást **(dekompilátum)** jelölöm. Ha a kettő eltér, az asm az irányadó.

**Névhasználat.** `owner`: a `0x00448560` hívásában az EDI (`push edi`, `0x0044866b`). `index`: az ECX, a `[esp+0x30]`-ból (`0x00448665`). `flag`: az AL (`push eax`, `0x00448669`). `konténer`: a `0x004e5740` első verem-argumentuma, a `0x00467ca0`-ban `esp+0x3e0` (ez az `auStack_7ae0`). `elem`: a `0x004e5740` EAX-ben kapott objektuma, a `0x00467ca0`-ban `esp+0x29c`.

##### §1 Q1: a `0x00506830` (U46): LEZÁRVA

- **Belépés.** EAX = a `this`. Két verem-argumentum van: `[esp+4]` az index, `[esp+8]` a kimeneti pár címe. Az indexet a `0x506839` tölti be, a pár címét a `0x5068a4`. A `ret 8` a `0x5068cb`, `0x5068ec`, `0x5068ff` és `0x506923` címeken van.
- **A `this` a hívóban.** A `0x484a62` sorban `lea eax,[ebx+0xf8]` áll. Ez a cím, nem a tárolt érték. A 38.2.49 §1.2 ezt tévesen `[ebx+0xf8]`-nak írta. ⚠️ JAVÍTVA (§7).
- **A kimeneti pár a hívóban.** A hívó keretében `esp+0x34` (`0x484a5c`). A hívás után (`0x484a7b`) a `lea ecx,[esp+0x34]` ezt használja tovább.
- **Index a darabszámon kívül.** Ha az index nagyobb vagy egyenlő a darabszámmal (`[this+0x3f4]>>1`, `0x506881`-`0x506885`), nincs másolás. A visszatérési érték 4 (`0x506919`). (Dekompilátum: 65-86. sor.)
- **Index a darabszámon belül.** Az elem a `[this+0x3f0][index]`, ha ez nem nulla. Ha nulla, az alapértelmezett elem a `this+0x3f8`. A forrás az elem `+0x24` mezője (`0x5068a0`). Ezt a verembe tolja (`0x5068a3`). Az EAX a kimeneti pár címe (`0x5068a4`), majd jön a `call 0x891110` (`0x5068a8`). A visszatérési érték 0 (`0x5068c4`).
- **A `0x00891110` nem az első argumentumába ír.** Az EAX a cél, vagyis a kimeneti pár. Az első verem-argumentum (`mov ebp,[esp+0x14]`, `0x891115`) a forrás. A függvény a célt írja: a puffert és a darabszámot. A forrást csak olvassa. A másolás `_memcpy(cél, forrás, darabszám*4)` (dekompilátum: 1175. sor). A `ret 4` a `0x891163`-on van. Az első argumentumába tehát nem ír.
- **Mit jelent a másolt lista.** A forrás 4 bájtos tételekből áll. Hogy ezek mit azonosítanak, NINCS MEG. Ghidra-kör: §6, `0x00449a00`.

##### §2 Q2: a `0x00493050` és a `0x004d9aa0` (U47, U52): LEZÁRVA az elem azonosítója

- **A `0x00493050` (U47).** `void`, a kilépés `ret 4` (`0x493092`). Egy verem-argumentum van, a `*param_1` érték. Az ESI-ben lévő pár darabszáma 1 lesz, ha a foglalás (`0x0097c810`) sikerül. Ez egyelemű lista (dekompilátum: 115-130. sor).
- **A `]star`-ág a `0x0045a87d`-nál.** Ott a `lea edx,[ebp+0xc]` (`0x45a89b`) után `push edx` (`0x45a89e`) és `call 0x493050` (`0x45a8a6`) áll. Az `ebp` a `0x00456610` keretének alapja. `[ebp+8]` a tulajdonos, `[ebp+0xc]` pedig a `0x00456610` `param_3`-a. A listába tehát ez az érték kerül. A hívás után a `call 0x4da1d0` (`0x45a8b8`) következik. Ennek a bemenetét nem követtem végig.
- **A `]star`-ág a `0x00458aeb`-nél (U52).** A hívó pár az `[esp+0x5c]` (adat) és az `[esp+0x60]` (darabszám<<1 | jelző). A `mov edx,[ebp+0xc]` (`0x458ad8`) és a `mov [esi+eax],edx` (`0x458ae4`) együtt azt jelenti: ha a puffer nem nulla, a `param_3` bekerül a listába, és a darabszám nő (`0x458ae7`).
- **A hívás.** A `0x458b0e`-`0x458b1d` sorokban: `push 2`, `push 1`, `lea eax,[esp+0x64]` (a pár címe), `push ecx` (az ECX = `[ebp+8]+0x68`, vagyis a név-tábla), majd az EAX = EDI, a `]star` név-objektum (ezt a `0x985ff0` építi). A `push 2` és a `push 1` a `0x004d9aa0` negyedik és harmadik argumentuma. Az asm igazolja a sorrendet.
- **Mit csinál a `0x004d9aa0` a párral.** (Dekompilátum: 185-410. sor.) Minden elemet a név rekordjának a végére fűz. A harmadik argumentum (az értéke 1) miatt minden elemre meghívja a `0x00a59000`-t. A negyedik argumentum (az értéke 2) miatt, ha volt elem, meghívja a `0x004db8f0`-t. A duplikációt nem szűri.
- **Mi a listaelem.** A `0x00456610` hívóiban más forrásból jön. A `0x468108`-nál, vagyis a `0x467ca0` útján, a `0x004e5740` visszatérési indexe (§3). A többi hívó forrása NINCS MEG (U49).
- **Fajta.** NINCS MEG. A név (`]star`) csillagra utalhat, de ez nincs igazolva.

##### §3 Q3: a `0x004e5740` (U49): RÉSZBEN

- **Hívás (`0x004680de`-`0x004680e8`).** `lea ecx,[esp+0x3e0]`, `push ecx` (a konténer), `mov eax,esi` (az elem), `call 0x4e5740`.
- **Argumentumok.** EAX = az elem (`0x4e5747`). Egy verem-argumentum van: a konténer (`mov ebp,[esp+0x2c]`, `0x4e574f`). A kilépés `ret 4` (`0x4e588f`).
- **Visszatérési érték.** A `0x4e5740` a `0x004e5070` eredményét adja vissza. A hívás a `0x4e578f`-nél van, a `mov edi,eax` a `0x4e5794`-nél (dekompilátum: 463. és 585. sor). A `0x4e5070` egy verem-argumentumot kap, az elemet (`push esi`, `0x4e578c`). A konténert EDI-ben kapja (`mov edi,ebp`, `0x4e578d`). A kilépése `ret 4` (`0x4e5205`). A hívó a 0xffffffff értéket "nincs" jelként kezeli (dekompilátum: 484. sor). Hogy a `0x4e5070` mikor ad -1-et, NINCS MEG. Egy kilépési ág látszik, a `sub eax,1` (`0x4e5200`).
- **Kimenet a konténerbe (`auStack_7ae0`).** A konténer `+0x480` objektumának tömbjébe, a visszatérési index helyére, a `[elem+0x18]` érték kerül (`mov ecx,[esi+0x18]`, `0x4e57b7`; dekompilátum: 487. és 558. sor). Emellett a `[konténer+0x4d4]` eggyel nő (`0x4e57a8`). Végül a `0x004ed450` hívódik (`0x4e579d`), a konténer `this`-ével és a visszatérési indexszel.
- **Az `auStack_7ae0` azonosítása.** A Ghidra-nevekből: `uStack_7e78` = `[esp+0x48]` a `0x4680ed`-nél, és `auStack_7ae0` = `[esp+0x3e0]` a `0x4680de`-nél. Ha a Ghidra-nevek a belépési esp-hez képest vannak (ezt feltételezem), mindkettő esp = E-0x7ec0. Ez egyezik. Az esp levezetése az §5-ben van, és az nincs eldöntve.
- **Nyitva.** (a) A `0x4e5070` minden kilépési ága, a -1 útja is. (b) ⚠️ JAVÍTVA (38.2.51 §4): a `0x4e5070` és a `0x506830` indexe ugyanazt a szerkezetet (`+0x3f0`) használja, de két külön objektumon, NEM ugyanaz a tábla. (c) A `[elem+0x18]` íróját megtaláltuk (`0x0040f9de`, 38.2.51 §3); a jelentése NINCS MEG (38.2.51 §5, U53).

##### §4 Q4: a `0x00447800` (U50): RÉSZBEN

- **Hívás (`0x00448640`-`0x0044866c`).** `push eax` (`0x448669`, a flag), `push ecx` (`0x44866a`, az index a `[esp+0x30]`-ból), `push edi` (`0x44866b`, az owner), `call 0x447800`. A flag 1, ha az ECX nagyobb, mint 0, vagy az EBX legalább 1. Különben 0 (`0x448656`-`0x448663`).
- **A hívott argumentumai.** A `0x447807` sorban `cmp byte ptr [esp+0x2c],0` áll. Ez a flag (a belépési esp + 0xc). Az owner a belépési esp + 4, az index a belépési esp + 8.
- **Mit ír (dekompilátum: 628-838. sor).**
  1. Ha a flag nem nulla, zárat vesz (`FUN_00985ff0`, `FUN_00401000`).
  2. Zárolja az owner táblájának szálát (`owner+0x1e28`, `+0x1e14`, `+0x1e30`).
  3. A tábla a `*(owner+0x1e60)` objektum. Darabszáma `[+0x4c]>>1`, adata `[+0x48]`.
  4. Ha az index a darabszámon belül van, és az ott álló elem érvényes, nincs írás. Csak a `FUN_005c2100()` hívódik, utána a `FUN_006a2a60`. Ha az elem nem érvényes, a függvény csak a zárakat oldja, és kilép.
  5. Ha az index a darabszám fölött van, a tömböt `index+1`-re nagyobbítja. Az új helyeket az `owner+0x1e64` mutatóval tölti fel, és a hivatkozásszámot növeli (`InterlockedIncrement`). Utána `FUN_006a2a60` hívódik.
  6. Ha az index -1, a függvény kilép, és nem ír.
- **Mihez tartozik az index?** Ebből NEM látszik. Az index a tábla pozíciója. Az új helyek mind ugyanazt az `owner+0x1e64` értéket kapják, tehát az index nem kap saját értéket. A hivatkozásszámos minta (`InterlockedIncrement`, a 0x7f-es határ) a `0x004d9aa0` név-objektumaival egyezik (dekompilátum). Ez csak minta, a típus nincs igazolva. Hogy a tábla melyik gyűjteményhez tartozik: NINCS MEG. Az `index` forrása (`uVar17`) az §5.

##### §5 A verem-keret és az index forrása: ellentmondás **⚠️ JAVÍTVA, LEZÁRVA (38.2.51 §1-2)**

- **Prológus.** `mov eax,0x7ea8` és `call 0x00bf6b80` (`0x467ca0`-`0x467ca5`): verem-foglalás. A rutin neve nincs megnézve. Utána a biztonsági süti: `mov eax,[0xd24004]`, `xor eax,esp`, `mov [esp+0x7ea4],eax` (`0x467caa`-`0x467cb1`). Ha a foglalás után az esp E-0x7ea8, a süti az E-4 címen van.
- **Pushok.** Négy push (`0x467cbf`-`0x467cc8`: ebx, ebp, esi, edi). Utána `push ebp` (`0x467cd8`) és `push 1` (`0x467cdb`). A `mov ebx,[esp+0x7eb0]` (`0x467cc0`) a belépési első argumentumot (E+4) tölti az EBX-be, ha az esp ekkor E-0x7eac.
- **Két lehetőség.** (A) A `0x4680de`-nál az esp E-0x7ec0. Ekkor a Ghidra-nevek egyeznek, de a `[esp+0x7ebc]` = E-4, vagyis a süti helye. Ebben az esetben a 38.2.49 §1.4 `uVar17 = [esp+0x7ebc]` állítása téves. (B) A törzsben az esp E-0x7eb8. Ekkor a `[esp+0x7ebc]` = E+4, vagyis az első argumentum, és a Ghidra-nevek 8 bájttal tévednek.
- **Nincs eldöntve.** A pushokat lineárisan összeadtam, de nem kaptam megbízható eredményt. A hívások és az elágazások miatt a pushok nem maradnak egyensúlyban. Például a `0x46d59a`-nál a számláló -1104-et adott, ami nem jelent valódi esp-t. Ezért NINCS MEG, melyik lehetőség áll. Ghidra-kör kell: a `0x00467ca0` prológusa, és az esp értéke a `0x46d59a` előtt.
- **Következmény.** A 38.2.49 §1.4 `uVar17` állítása KÉTSÉGES. A U49 és a U50 index-eredete blokkolt.

##### §6 Ghidra-címek a következő körhöz

Blokkolók a fő kérdésre (az elem fajtája):
- `0x00467ca0`: (a) a prológus `0x467ca0`-`0x467cdb`, a süti és az első argumentum helye; (b) az `[esp+0x7ebc]` forrása, és az esp a `0x46d59a` előtt (§5); (c) az `esp+0x29c` elem felépítése. A törzsben csak a `0x4680ca` `lea esi,[esp+0x29c]` hivatkozik rá. A `+0x18` mező írója is kell.
- `0x004e5070`: a verem-argumentum (az elem) használata, a visszatérési érték minden kilépési ága, és hogy a `+0x3f0` indexe azonos-e a `0x506830` indexével (§3).
- `0x00449a00`: a `0x506830` kimeneti párjának (a másolt 4 bájtos lista) felhasználása (lásd U41).

Nem blokkolók, de a U50-hez kellenek:
- `0x005c2100`: a `0x447800` belső ágának (az index a tábla határán belül) törzse.
- `0x004ed450`: a `0x004e5740` által hívott függvény, a konténer `this`-ével.
- `0x004da1d0`: a `0x45a8b8`-ban hívott függvény, a `0x493050` listájának fogadója.

##### §7 Javítások a korábbi szakaszokban (⚠️ JAVÍTVA)

- 38.2.49 §1.2: a `this` nem `[ebx+0xf8]`, hanem `lea eax,[ebx+0xf8]`, vagyis cím. ⚠️ JAVÍTVA.
- 38.2.49 §1.2: a kimeneti pár tartalma NINCS MEG volt. Most LEZÁRVA: a `0x00891110` célja.
- 38.2.49 §1.4: az `uVar17 = [esp+0x7ebc]` állítás **⚠️ JAVÍTVA (38.2.51 §2)**: az asm-olvasás helyes, de az első verem-argumentumot olvassa, nem ciklusindexet.
- 38.2.49 §6: a `0x00891110` LEZÁRVA (§1).

##### §8 Amit KIZÁRTAM

- „A `0x00891110` az első argumentumába ír”: CÁFOLVA. A forrást csak olvassa (§1).
- „A `this` a `[ebx+0xf8]` tartalma”: CÁFOLVA. Ez a cím (§1).
- „A `0x00447800` index-függő azonosítót ír a táblába”: CÁFOLVA. Minden új hely ugyanazt az `owner+0x1e64` értéket kapja (§4).
- „A `[esp+0x7ebc]` a ciklusindex”: **⚠️ CÁFOLVA (38.2.51 §2):** az első verem-argumentum (`E+4`), nem ciklusindex.

##### §9 Nyitott lista (38.2.50 §9; felülírta: 38.2.51 §9)

Nyitott kérdések mérlege (38.2.50): 52 tétel · 12 lezárva · 24 részben · 16 nincs meg. Az előző mérleg (38.2.49): 52 · 11 · 25 · 16. Változás: U46 RÉSZBEN → LEZÁRVA. A 38.2.49 §9 tábla felülíródott.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U1 | NINCS MEG (változatlan) | a `0x00a6aa00` teljes törzse | `0x00a6aa00` |
| U2 | RÉSZBEN (változatlan) | az obj2 osztálya és a vt+0 cél | `0x005e8a70`, `M+0x4c` vt+0 |
| U3 | RÉSZBEN (változatlan) | a mód-tartó (`obj`, névhasználat) igazolt; az `L` osztálya NINCS MEG | `0x004a7890`, `0x004baaa0` |
| U4 | NINCS MEG (változatlan) | a `0x008014d0` vt+0 hívott függvénye | `0x008014d0` |
| U5 | NINCS MEG (változatlan) | a `[this+0x2ec]` olvasói | pásztázás |
| U6 | NINCS MEG (változatlan) | a `0x009aaae0` hívóhelyei | `0x009aaae0` |
| U7 | LEZÁRVA (38.2.41 §1) | a sorrekord `+0x14` írója | - |
| U8 | NINCS MEG (változatlan) | a `P' = [T+0x3a4]` írója | `0x007fa7f0` |
| U9 | LEZÁRVA (38.2.41 §2-3) | a kattintási ág | - |
| U10 | RÉSZBEN (változatlan) | a `0x004b8470` hívója és az `[L+0x148]` írói | `0x004b8ee0` |
| U11 | RÉSZBEN (változatlan) | az `L` osztálya, `+0xc == 2`, `jbe` | `0x004b29d0` |
| U12 | NINCS MEG (változatlan) | az EBP/EBX forrása a hívottakban | `0x004b2e10`, `0x004b3770`, `0x004b80d0` |
| U13 | RÉSZBEN (változatlan) | a `0x007fc010` | `0x007fc010` |
| U14 | RÉSZBEN (változatlan) | a `0x008014d0` törzse | `0x008014d0` |
| U15 | NINCS MEG (változatlan) | a startbutton vt+0x18 | `0x007fa7f0` |
| U16 | RÉSZBEN (változatlan) | a rendező kulcssorrendje igazolt; a G-táblák feltöltése U37 | `0x004a7890`, `0x004baaa0` |
| U17 | NINCS MEG (változatlan) | a `0x004b8d00` | `0x004b8d00` |
| U18 | NINCS MEG (változatlan) | az `E` görbe | `0x005568e0` |
| U19 | NINCS MEG (változatlan) | a rekord-utólagos és a ciklus-utáni lépés | `0x007fa650`, `0x00604480` |
| U20 | NINCS MEG (változatlan) | a kártya-rekord építése | `0x007fa5b0` |
| U21 | LEZÁRVA (38.2.43 §2) | a CSlice konstruktor és a destruktor-lánc | `0x004133e0`, `0x00413490` |
| U22 | RÉSZBEN (változatlan) | a `0x004406f0` a vt+0x2c cél; a `[L+0x48]` vtábla újra nincs igazolva | `0x00402f90`, U36 |
| U23 | LEZÁRVA a törzs (38.2.44 §2) | a sor neve | `0x004a71e0` |
| U24 | RÉSZBEN (38.2.48 §2) | a 4. mód igazolt; az 1. mód dupla a `0x00450bd0` (U32); a 0. mód a `G+0x18` tábla (forrása NINCS MEG) | `0x004502e0`, `0x004ae0d0`, `0x004a7890` |
| U25 | LEZÁRVA (38.2.48 §3) | a `0x00987030` törzse | `0x00987030`, `0x004a7ad4` |
| U26 | NINCS MEG (változatlan) | a K-másolás törzse | `0x00801915`-`0x00801bc4` |
| U27 | NINCS MEG (változatlan) | az `M+0x64c` és `M+0x650` írása | `0x005e8a70` |
| U28 | LEZÁRVA (38.2.45 §1) | a kulcs NÉV | `0x004dca40`, `0x004406f0` |
| U29 | RÉSZBEN (38.2.45 §2) | a `[X+0x1034]` CThumbDB írója LEZÁRVA; az `L` írója U36 | `0x00402f90`, U36 |
| U30 | RÉSZBEN (38.2.45 §4) | a G-szerep LEZÁRVA; a táblák feltöltése U37 | `0x004b94a0`, U37 |
| U31 | RÉSZBEN (38.2.46 §3.2) | a bemenet igazolt; a statisztika neve NINCS MEG | `0x00450100` |
| U32 | RÉSZBEN (38.2.49 §3, új) | a `0x00450bd0` 64 bites maximum-számítása igazolt; a 64 bites érték jelentése, a `0x0098b650` és a `0x006c9d60` NINCS MEG | `0x00450bd0`, `0x0098b650`, `0x006c9d60` |
| U33 | RÉSZBEN (38.2.47 §3.3) | a mód forrása parancs-ágankénti konstans; a parancsazonosító és az ág párosítása NINCS MEG | `0x005cb990`, `0x005d9cc0`, `0x004b07c0` |
| U34 | NINCS MEG (változatlan) | az OLEAUT32 184. sorszám neve | IAT `0x00c405c8` |
| U35 | RÉSZBEN (38.2.46 §1.3) | a literál szövege `token`; a rekord `+5` mezőjének tartalma NINCS MEG | `0x00415790`, `0x00985ff0`, `0x004941f0` |
| U36 | RÉSZBEN (38.2.47 §3.5) | az `[X+0x2c0]` a mód-tartó (ha `X = V`); az `X = V` NINCS MEG (U43) | `0x004b07c0`, `0x005d30f0`, `0x004502e0` |
| U37 | RÉSZBEN (38.2.47 §2.2) | a G-veremszerkezetet a hívó állítja be; a tartalmának feltöltése NINCS MEG | `0x004b94a0`, `0x004b8ee0` |
| U38 | LEZÁRVA (38.2.46 §2.2) | egyesítő rendezés; a kulcsot a `0x004a7890` adja | `0x004baaa0`, `0x004a7890` |
| U39 | RÉSZBEN (38.2.47 §2.1) | az `obj` a hívó `this`-e; a `0x004b94a0` első argumentuma O = `[X+0x2c0]` (38.2.49 §4) | `0x004b8ee0`, `0x006dc4c0`, `0x005fe130` |
| U40 | RÉSZBEN (38.2.48 §1.3) | a név-tábla írói igazoltak; az elemek fajtája NINCS MEG (U49, U50) | `0x00456610`, `0x00448560`, `0x004da1d0` |
| U41 | RÉSZBEN (38.2.48 §1.1) | a `0x00484820` nem író; a bemeneti tömböt a `0x00506830` építi (U46) | `0x00484820`, `0x00484bbd` |
| U42 | RÉSZBEN (38.2.48 §1.3) | az írók megvannak; az azonosító (`param_3`) forrása a 0x467ca0 és a 0x425f60 útjában az index, de a fajtája NINCS MEG | `0x00456610`, `0x00448560` |
| U43 | NINCS MEG (változatlan) | az `X` azonos-e a `V = [[0xd67668]+0x102c]`-vel | `0x005cb9aa`, `0x004b07e8`, `0x006dc4c0` |
| U44 | RÉSZBEN (38.2.48 §2) | mindkét kulcs mechanikája LEZÁRVA; a dupla tartalma U32 | `0x004ae0d0`, `0x004507e0` |
| U45 | LEZÁRVA (38.2.49 §4) | a `0x005fe130` hívója és a `0x0056c5a0` első verem-argumentuma: O = `[X+0x2c0]`; X forrása nincs felvéve külön | `0x005fe130`, `0x0056c5a0` |
| U46 | LEZÁRVA (38.2.50 §1) | a törzs, a kimeneti pár és a `this` igazolt; a `0x00891110` a célba ír, a forrást csak olvassa | `0x00506830`, `0x00484a70`, `0x00484a5c`, `0x00891110` |
| U47 | LEZÁRVA (38.2.50 §2) | a lista elemének azonosítója a `0x00456610` `param_3`-a; a fajta NINCS MEG (U42) | `0x00493050`, `0x0045a8a6`, `0x0045a89b` |
| U48 | NINCS MEG (változatlan) | a `[owner+0x2e9c]` és a `[owner+0x2e94]` név írói, és a viszonyuk | `0x004489dc`, `0x00449a00` |
| U49 | RÉSZBEN (38.2.50 §3, új állapot) | visszatérés: a `0x004e5070` eredménye; a kimenet: a tábla indexhelyére a `[elem+0x18]` kerül; az index forrása KÉTSÉGES (38.2.50 §5) | `0x00468108`, `0x004e5740`, `0x004e5070`, `0x00467ca0`, `0x0047c5fc`, `0x0047c815`, `0x00540568`, `0x0055eef4`, `0x0055ef45` |
| U50 | RÉSZBEN (38.2.50 §4, új állapot) | hívás: owner=EDI, index=ECX, flag=AL; írás: új helyek az `owner+0x1e64` értékével; az index jelentése NINCS MEG | `0x00448640`, `0x00447800`, `0x005c2100`, `0x0047e8ad`, `0x0047e908`, `0x0047fcaa`, `0x00480155`, `0x0048352f`, `0x0057dd86` |
| U51 | LEZÁRVA (38.2.49 §4) | a `0x004b94a0` első verem-argumentuma `[X+0x2c0]`, X a `0x0056c5a0` első argumentuma | `0x0056d2b6`, `0x0056c5a0` |
| U52 | LEZÁRVA (38.2.50 §2) | a bemenő lista eleme a `0x00456610` `param_3`-a (asm); a fajta NINCS MEG | `0x004d9aa0`, `0x00458aeb`, `0x00458ad8`, `0x00458ae4` |

**A felhasználó szemével**

Nincs két-három mondatos összefoglaló, mert a fő kérdés (az elem fajtája) nem dőlt el. A hiányzó címek: `0x00467ca0` (az index forrása és a `+0x18` mező írója), `0x004e5070` (a visszatérési érték) és `0x00449a00` (a másolt lista használata).

#### 38.2.51 Az Időrend bináris feltárása, 34. kör: a verem-alap, az elem `+0x18` mezője és a két tábla (#5401, 2026-10-22)

**Kérdés és hatókör.** A 38.2.50 nyitott tételei: a `0x00467ca0` prológusa és az elem (1), a `0x004e5070` argumentuma, ágai és indexe (2), a `0x00449a00` (3) és a U50 három függvénye (4). A fő kérdés az elem fajtája (kép, album, személy). Bemenet: a `2026-10-21-idorend-34.txt` hat címe, a 38.2.50 §6 és §9 lista. Kódot nem módosítottunk, ezért a CI-őrök nem futottak.

**Válasz röviden.**
1. **Q1, a prológus és a verem-alap: LEZÁRVA.** A törzs verem-alapja `E-0x7eb8` (E: a belépési esp), nem `E-0x7ec0`. A prológus két push-a (0 és 1) a `0x00467cec` hívás argumentuma: a `0x004e47d0` (`ret 8`) felveszi őket. A záró kód (`0x0046d72e`) ezt igazolja (§1).
2. **Q1, az `[esp+0x7ebc]` forrása: LEZÁRVA.** Ez az `E+4`, a függvény első verem-argumentuma. A törzs nem írja, a hat hívó utolsó push-ként adja. Nem ciklusindex, és nem a `0x004e5070` eredménye (§2).
3. **Q1, az elem és a `+0x18` írója: RÉSZBEN.** Az elem `E-0x7c24`-en kezdődik, 0x144 bájt. A `+0x18` mezőt a `0x0040f980` konstruktor írja (`0x0040f9de`). Az érték a `0x004680be`-nél push-olt `eax`: `2`, ha az `arg2` nem nulla. Nulla `arg2` esetén a `0x00a4c140` visszatérési értéke, ami NINCS MEG (§3).
4. **Q2, a `0x004e5070`: LEZÁRVA.** Az elem egyetlen használata a `0x00509350` hívás, amely az elemből másolja a rekordot. Három visszatérési ág van. A `+0x3f0` index NEM azonos a `0x00506830` indexével: a szerkezet azonos, de más objektumon van (§4).
5. **Q2 folytatás: a `+0x18` útja.** A `0x004e5740` az értéket a konténer `+0x480` objektumának `T2` táblájába írja, a `0x004e5070` indexe szerinti helyre (§5). Hogy a `T2` olvasója mit tesz a számmal: NINCS MEG (U53).
6. **Q3, a `0x00449a00`: RÉSZBEN.** A függvény nem a `0x00506830` párját kapja, hanem a `0x00484bbd` ciklus egy tételét. A tételt a `0x004db180` dolgozza fel, a `this+0x68` objektum zárja alatt. A lista és a pár kapcsolata NINCS MEG (U41, §5).
7. **Q4, U50: RÉSZBEN.** A `0x004ed450` a konténert zárolja, és a `+0x54` alobjektum vtábla 8. slotját hívja az indexszel. A `0x005c2100` szöveg-értékadás. A `0x004da1d0` NINCS MEG (§5).
8. **Q5, a fő kérdés (az elem fajtája): NINCS MEG.** A `+0x18` értéke nincs jelentéshez kötve. A hiányzó címek a §6-ban, a U53 és U54 tételen. A „felhasználó szemével” rész a végén.

**Hatókör és módszer.** Két eszköz: a `pe_dis.cdis` diszasszemblálás és a bemeneti Ghidra-dekompilátum. A verem-kérdéshez új módszert használtunk: a `0x00467ca0` CFG-jén propagáltuk az esp E-hez képesti eltolását (ideiglenes szkript a `.bt/` alatt, a kör végén törölve). Minden utasításhoz kiszámoltuk a mélységet. Hívásnál a hívott függvény `ret N` értékét adtuk hozzá. A közvetlen hívottak `ret` értékét a kódjukból olvastuk ki. Az IAT- és vtábla-hívásnál (nincs közvetlen cél) a közvetlenül előtte álló push-ok számát vettük, stdcall-feltevéssel. Ezek a helyek másodlagosak. A `0x00467ca0` és a `0x0046a80d` között a propagálás ütközésmentes. Az eredményt a záró kóddal (`0x0046d72e`) ellenőriztük.

**Bizonyítottsági fok (38.2.51).**

| állítás | bizonyíték | fok |
|---|---|---|
| a törzs alapja `E-0x7eb8` | `0x004e47d0` `ret 8` (a `0x00467cec` hívásnál); záró kód `0x0046d72e`-`0x0046d746` | megerősített (asm) |
| a függvény `ret 0xc`, három verem-argumentum | `0x0046d746` (`ret 0xc`) | megerősített |
| `[esp+0x7ebc]` = `E+4` | mélység-követés; nincs írás `E+0`-`E+0x10` területre | megerősített (asm) |
| a hat hívó utolsó push-a az index | diszasszembly, hívóhelyek (§2 táblája) | megerősített |
| az elem `E-0x7c24`, a `+0x18` írója `0x0040f9de` | `lea` a `0x004680ca`, `call 0x0040f980` (ret 8) | megerősített |
| az `eax = 2` ág feltételei | ugrások `0x00468081`, `0x00468092`, `0x0046809d` | megerősített (asm) |
| a `0x00a4c140` visszatérési értéke | nem vizsgáltuk a visszatérést (**⚠️ JAVÍTVA, 38.2.52 §2**) | **LEZÁRVA** (kiterjesztés-tábla) |
| a `0x004e5070` három visszatérési ága | diszasszembly és dekompilátum | megerősített |
| a `0x004e5070` és a `0x00506830` objektuma különbözik | `0x00506830` `this` = `lea eax,[ebx+0xf8]` (38.2.50 §1); a konténer a `0x00467ca0` verem-objektuma | megerősített |
| `T2[index]` írása | `0x004e5a13`-`0x004e5a26` | megerősített (asm) |
| a `T2` olvasói | nem vizsgáltuk | NINCS MEG |
| a `0x00449a00` egy tételt kap | `0x00484bc3` hívás, `[esi+ebp*4]` | megerősített (hívóhely) |
| a lista és a pár kapcsolata | nem követtük vissza a `0x00484bbd` `esi`-t | NINCS MEG |

##### §1 Q1: a prológus és a verem-alap (LEZÁRVA)

- `0x00467ca0`: `mov eax,0x7ea8`, `call 0x00bf6b80` (`__alloca_probe`): az esp `E-0x7ea8`.
- A süti: `mov [esp+0x7ea4],eax` (`0x00467cb1`), azaz `E-4`.
- Négy push (`0x00467cbf`-`0x00467cc9`): ebx, ebp, esi, edi. Az esp `E-0x7eb8`. A mentett regiszterek helye: ebx `E-0x7eac`, ebp `E-0x7eb0`, esi `E-0x7eb4`, edi `E-0x7eb8`.
- `xor ebp,ebp` (`0x00467cd6`), majd `push ebp` (`0x00467cd8`, értéke 0) és `push 1` (`0x00467cdb`). Ezután `call 0x004e47d0` (`0x00467cec`). A `0x004e47d0` `ret 8`-cal tér vissza, tehát ez a két push az argumentuma. A hívás után az esp `E-0x7eb8`.
- A hívás előtti írások (`0x00467cdd`, `0x00467ce1`, `0x00467ce5`) `E-0x7ec0` mellett történnek. A dekompilátum `local_7e9c = param_2` sora ezt megerősíti.

Az `E-0x7eb8` bizonyítékai:
- a. A záró kód (`0x0046d72e`): `mov ecx,[esp+0x7eb4]` (a süti `E-4`), majd négy pop (`0x0046d735`-`0x0046d738`: edi, esi, ebp, ebx), `add esp,0x7ea8`, `ret 0xc`. A süti csak akkor van `[esp+0x7eb4]`-en, ha az esp `E-0x7eb8`, és a négy pop a prológus mentett regisztereit olvassa vissza.
- b. A `0x00467d94`-`0x00467d98` ágban egy második `push ebp; push ebp; call 0x004e47d0` után `jmp 0x0046d72c` következik. Ez is `E-0x7eb8`-cal érkezik a záró kódba.
- c. A Ghidra-nevek egy része `E-0x7eb8`-hoz illik (például `local_7e90` és `local_7e60`, mindkettő a hívás utáni írás), más része `E-0x7ec0`-hoz (§7).

Következmény: a függvény `ret 0xc`-vel tér vissza, tehát három verem-argumentuma van. Ezek `E+4` (arg1), `E+8` (arg2) és `E+0xc` (arg3). A Ghidra-szignatúra csak kettőt mutat.

##### §2 Q1: az `[esp+0x7ebc]` forrása (LEZÁRVA)

- A törzs ezt olvassa a `0x00468171` (`cmp ecx,[esp+0x7ebc]`) és a `0x0046817d` címen, és további negyven helyen. A `0x0046810d` után `esi = this+0x16b8`, a `[esi+0x58]` tábla (`[this+0x1710]`) darabszáma `[+0x4c]>>1`, adata `[+0x48]`. Ha az index kisebb a darabszámnál (`0x00468178`), a `0x0046818e` hívás a `0x005c2100`-zal másolja az elemet a `[esp+0x124]` helyre.
- Az index címe `E-0x7eb8+0x7ebc = E+4`, az első verem-argumentum.
- Írás a `E+0`-`E+0x10` területre a törzsben: nincs. A törzs 330 feloldott írását ellenőriztük, egy sem esik ide.
- A hat hívóhely. Az arg1 az utolsó push, az arg2 az előtte lévő push:

| hívóhely | hívó függvény | arg1 (az index) | arg2 |
|---|---|---|---|
| `0x0046584d` | `0x00465710` | `ebp` | `eax` (`&[esp+0x14]`) |
| `0x00539b0a` | `0x00539020` | `edx` (a `[eax]` a `0x00539afe`-nél) | `0` |
| `0x0053b0c5` | `0x0053a790` | `ecx` | `0` (`ebp`) |
| `0x006b1d6f` | `0x006b1d20` | `ebp` | `esi` |
| `0x006b3d21` | `0x006b39b0` | `eax` | `esi+0x34` |
| `0x00803dfb` | `0x00803d40` | `esi` | `ebx+0x8c` |

- Következtetés: az index a hívó által adott szám. Hogy a hívóban az `ebp`, `ecx`, `eax`, `esi` vagy `edx` mit jelent, NINCS MEG, a hívó-láncot nem követtük vissza.

##### §3 Q1: az elem és a `+0x18` mező írója (RÉSZBEN)

- Az elem: `lea esi,[esp+0x29c]` (`0x004680ca`). Az esp itt `E-0x7ec0`, így az elem `E-0x7c24`-en kezdődik, 0x144 bájt hosszú. A `0x004e5740` ezt az `esi`-t kapja (`0x004680e8`).
- A törzsben a `lea` mutatók közül kettő (`0x00467d13`, `0x00467d5e`) az elem `+0x54` alobjektumára mutat. Ezt a `0x00415790` (ret 8) és a `0x00417770` építi. Ez nem a `+0x18` mező.
- A `+0x18` írója: `0x0040f980` (ret 8), `0x0040f9de`: `mov [esi+0x18],ecx`. ESI = az elem, az `lea` óta nem változott. ECX = az első verem-argumentum (a `[esp+8]` a push után), vagyis a `0x004680be`-nél push-olt `eax`. A `+0x14` mező a második argumentumot kapja, az 1-et (`push 1`, `0x004680bc`).
- A `0x0040f980` többi írása: `+0` = a `[E-0x28a8]` mutató (a `0x004680c3` `lea`-ja), `+0x04` és `+0x0c` = a `[edi]` (nulla), `+0x08` és `+0x10` = a `[edi+4]` (nulla), `+0x14` = 1, `+0x18` = az `eax`, `+0x1c` = 0, `+0x1d` = 1, `+0x1e` = 0 (szó), `+0x20` = -1, `+0x24` = 0, `+0x28` = 0.
- Az `eax` értéke a `0x004680be`-nél:
  - Ha az `arg2` (a `0x00467ccc`-ben másolt E+8, `[esp+0x48]`) nem nulla, a `0x0046809d` (`cmp esi,ebp`) után az ág a `0x004680bc`-re ugrik, és az `eax` = **2** (`mov eax,2`, `0x00468083`). Ehhez az is kell, hogy `ebx = 0` (`0x00468081`) és a `[esp+0x1b]` bájt nulla (`0x00468092`).
  - Ha az `arg2` nulla, az `eax` a `0x00a4c140` visszatérési értéke (`0x004680b3`, bemenet `[E-0x28a8]+4`, vagy 0). **⚠️ JAVÍTVA (38.2.52 §2):** a visszatérési érték LEZÁRVA. A `P+4` szöveg fájlkiterjesztésének kódja a `0x00d33418` táblából; üres bemenetnél 0, egyezés nélkül `-1`.
- Az `arg2` a `0x00539b0a` és a `0x0053b0c5` hívóban nulla, ezek tehát a második ágon futnak. A többi hívóban az `arg2` a táblában szereplő regiszter értéke. Ezt nem követtük vissza.
- Mit jelent a `2`: **⚠️ PONTOSÍTVA (38.2.52 §2, §4):** a `2` a `.jpg` kódja a `0x00d33418` táblában, tehát fájltípus-kód, nem kép-, album- vagy személy-jelölés. A `+0x18` később a `0x00509350` (rekordba másolás, §4) és a `0x004e5740` (`T2` tábla, §5) lépésben szerepel, de egyik sem mondja meg, hogy a szám kép-, album- vagy személy-tételt jelöl. **⚠️ KÉTSÉGES (38.2.54 §3):** a `0x006a2a60` figyelő-ágán ugyanezt az értéket a `0x004936c0` karakterláncként hasítja. Ez nem fér össze a fájltípus-olvasattal, amíg nem tudjuk, lefut-e ez az ág.
- **⚠️ JAVÍTVA (38.2.52 §3):** a `0x0046a8a2` a `0x0046808c` `jne` célja (ha `ebx != 0`), a `0x0046a8ad` a `0x00468097` `jne` célja (ha `cStack_7ea5 != 0`). Ezek NEM elem-építő ágak: egyik sem ír `+0x18`-at, mindkettő a `0x0046a80d` közös folytatásba fut. A `0x00468081` és a `0x00468092` csak `cmp` utasítás.

##### §4 Q2: a `0x004e5070` (LEZÁRVA)

- Belépés: ⚠️ JAVÍTVA (38.2.53 §1): a verem-argumentum a KONTÉNER (`mov ebp,[esp+0x2c]`, `0x004e574f`), az elem az EAX (`mov esi,eax`, `0x004e5747`). Az eredeti állítás (az elem a verem-argumentum) téves volt.
- Az elem használata: egyetlen helyen, a beszúrás végén. `call 0x00509350` (`0x004e51f1`), ESI = az új rekord. A `0x00509350` az első argumentumot (EBX = `[esp+0xc]`, az elem) másolja a rekordba: `[esi+0x20] ← [ebx+0x20]`, `[esi+0x18] ← [ebx+0x18]`, és a többi mezőt (`+0x04`-`+0x14`, a bájtok `+0x1c`-`+0x1e`). Az elem tehát bemenet, a `0x00509350` nem írja.
- Visszatérési ágak (a `+0x3f4` mező 0. bitje a jelző, a többi bit a darabszám):
  - a. A jelző 1: nincs beszúrás. A visszatérés `darabszám-1`, üres táblánál `-1`.
  - b. A jelző 0, és a tábla a növelés után nem nulla: a `table[darabszám]` helyre új, 0x2c bájtos rekord kerül (a `+0x424` foglaló, ha az üres, akkor `0x0097c5d0`). A mezők nullázódnak: `+0x20 = -1`, `+0x1c = 0`, `+0x1d = 0`, `+0x1e = 0xffff`. Utána a `0x00509350` másolás. A visszatérés a régi darabszám, vagyis az új rekord indexe.
  - c. A jelző 0, de a tábla nulla (a növelés nem sikerült vagy nulla kapacitás): nincs beszúrás, a visszatérés `darabszám-1`.
- Kapacitás: kis darabszámnál a kapacitás kettő-hatványonként duplázódik (`0x0097c810`, realloc), nagy darabszámnál 0x400-as lépésekben nő. Nulla kapacitásnál a `0x0097caf0` szabadít.
- A `0x00509350` hívás a (b) ágban mindig megtörténik: a rekord hiányában az `iVar5` a `+0x3f8` címre esik vissza, ami nem nulla. Ez kódolvasás, futtatással nem próbáltuk.
- Index-azonosság a `0x00506830` indexével: a két függvény szerkezete azonos (`+0x3f0` tábla, `+0x3f4` darabszám és jelző, `+0x3f8` alapelem), de más objektumon dolgoznak.
  - `0x004e5070`: EDI = a `0x00467ca0` verem-konténere, `[esp+0x3e0]` (`0x004680de`-nél `E-0x7ad8`).
  - `0x00506830`: `this` = `lea eax,[ebx+0xf8]` (38.2.50 §1), vagyis a hívó (`0x00484a62`) objektumának belseje.
  - Két külön tábla, két külön index-tér. NEM azonos.

##### §5 Q3, Q4 és a `T2` tábla (U41, U50, U53)

- A `0x004e5740` érték-ága: `ebx = [konténer+0x480]` (`0x004e57a2`). A `0x004e57b7` `mov ecx,[esi+0x18]` veszi az elem `+0x18` mezőjét. Ezután az `ebx` objektum zárja (`[ebx+0x20]` tulajdonos, `[ebx+0x24]` számláló, `[ebx+0x28]` CRITICAL_SECTION), majd a `0x004e5a13` ág.
  - `0x004e5a13`: `eax = [esi+0x48]` (a `T2 = [ebx+0x58]` adata), `ecx = [esp+0x18]` (az érték). Ha `T2[index]` nem egyezik vele, a `0x004e5a26` `mov [eax],ecx` az értéket a `T2[index]` helyre írja. Utána `call 0x006a2a60` a `[ebx+0x50]+0x4c` objektumon (a tábla jelzője).
  - Ha az index nagyobb vagy egyenlő a darabszámmal (`0x004e581b`, `0x004e5821`), a `T2` nő (`0x004e5892`).
- A `0x004e5740` visszatérése az index: `0x004e5886` `mov eax,edi`, és az `edi` a `0x004e585b`-nél `[esp+0x14]`, ami a `0x004e5070` eredménye (`0x004e5794`). Ez LEZÁRVA.
- A `0x004ed450` (`ret 4`, hívás `0x004e579d`): `eax` = a konténer, az index az argumentum. Zárolja a konténert, majd `call [edx+8]` a `[esi+0x54]` alobjektumon, az indexszel. A konténer értesítése az új indexről. A `[esi+0x54]` osztálya és a vtábla 8. célja NINCS MEG.
- Mit olvas a `T2`: NINCS MEG (U53). Az érték tehát a `T2`-be kerül, de nem tudjuk, ki és mire használja.
- **Q3, a `0x00449a00` (U41).** `ret 4`, `this` = ECX (a `0x00484bc1` `mov ecx,ebx`). Egy verem-argumentum: a `0x00484bbd` ciklus `[esi+ebp*4]` tétele. A függvény: `eax = [this+0x2e94]` (ha nem nulla, `+4`, egyébként 0), push eax (név), push tétel, `eax = this+0x68`, `call 0x004db180`, `setne al`. A `0x004db180` a `this+0x68` objektumot zárolja (ESI = EAX, `[esi+0x20]`, `[esi+0x24]`, `[esi+0x28]`). A `[esi+0xc]` jelző alapján vagy az EnterCriticalSection hívódik, vagy a `[edx+0x18]` vtábla-hívás. A bool eredmény jelentése NINCS MEG. A `0x00506830` párja nem ez a bemenet: a `0x00484bbd` ciklus `esi`-je nincs visszakövetve, ezért a kapcsolat NINCS MEG.
- **Q4, U50.**
  - `0x004ed450` (ret 4): lásd fent.
  - `0x005c2100` (ret 0): `edi = eax` (cél), `esi` (forrás). Ha a két mutató különbözik, a `0x00401000` kiadja a régit, átveszi az újat, és a hivatkozásszámláló mintáját (`cmp ecx,0x80`) követi. Szöveg-érték másolása, megerősítve a `0x0046818e` hívóhelyről.
  - `0x004da1d0` (ret 0xc): NINCS MEG. Csak az első sorokat néztük (`[edi]` null-ellenőrzés, `[eax+4]` teszt). A 38.2.50 §2 szerinti fogadó, nem a fő kérdés útja.

##### §6 Ghidra-címek a következő körhöz

Blokkolók a fő kérdésre (az elem fajtája):
- `0x004e5a13` és a `T2` olvasói: a `[konténer+0x480]` objektum osztálya, és a `[obj+0x58]` tábla olvasói (U53). Ghidra-kör kell: a `0x004e5740` `ebp+0x480` objektumának osztálya, és a `[obj+0x58]` olvasói.
- **⚠️ JAVÍTVA (38.2.52 §2):** a `0x00a4c140` visszatérési értéke a törzsből olvasható (0, táblaérték vagy `-1`), a `0x00a4c6a0` a kiterjesztés-kereső. A `0x00a4c1ad` ágcímet ebben a körben nem ellenőriztük, a 38.2.51 nem igazolta.
- **⚠️ JAVÍTVA (38.2.52 §3):** a `0x0046a8a2` és a `0x0046a8ad` NEM elem-építő ágak. A `+0x18` írója a `0x004680d9` hívás, a törzsben más `0x0040f980` hívás nincs.

Nem blokkolók:
- `0x00484820`: az `esi` forrása a `0x00484bbd` ciklus előtt, és hogy a lista a `0x00506830` párja-e (U41).
- `0x004db180`: a `this+0x68` objektum osztálya és a `[edx+0x18]` vtábla-cél (U41).
- `0x004ed450`: a `[esi+0x54]` objektum osztálya és a vtábla 8. slotjának célja (U50).
- `0x004da1d0`: a fogadó teljes törzse (U47, U52; nem a fő kérdés útja).

##### §7 Javítások a korábbi szakaszokban (⚠️ JAVÍTVA)

- 38.2.50 §5 (A/B ellentmondás): **LEZÁRVA**. A (B) eset igaz: a törzs `E-0x7eb8`-on fut. Az (A) eset hamis, mert a `0x004e47d0` felveszi a két prológus-push-t.
- 38.2.50 §8 („a `[esp+0x7ebc]` a ciklusindex”): **JAVÍTVA**. Az `E+4`, az első verem-argumentum (§2).
- 38.2.50 §3 (b): **JAVÍTVA**. Két külön objektum, NEM ugyanaz a tábla (§4).
- 38.2.50 §3 (c): a `+0x18` írója megvan (`0x0040f980`, §3). A jelentése NINCS MEG.
- 38.2.50 §3 („a kimenet a konténerbe kerül”): **pontosítva**. A `[konténer+0x480]` objektum `T2` táblájának `index` eleme kapja, nem közvetlenül a konténer (§5).
- 38.2.49 §1.4 (`uVar17 = [esp+0x7ebc]`): a kiolvasás helyes, de az „index” nem ciklusindex, hanem az első verem-argumentum (§2).
- A Ghidra-nevek a `0x00467ca0` törzsében NEM egységesek. A `local_4` az indexet nevezi, pedig `E+4`. A `uStack_7e78` és a `local_7e70` nevek egy része `E-0x7eb8`-hoz, más része `E-0x7ec0`-hoz illik. A Ghidra-szignatúra (`param_3`, `param_4`) nem mutatja az `E+0xc` argumentumot. **Ezért a verem-slotot ettől fogva nem a Ghidra-névből azonosítjuk, hanem a mélység-követéssel.** A 38.2.45-38.2.50 szakaszok Ghidra-neveit ezzel a megszorítással kell olvasni.

##### §8 Amit KIZÁRTAM

- „Az index a `0x004e5070` visszatérési indexe”: **CÁFOLVA** (§2). Az index a hívó argumentuma.
- „A `[esp+0x7ebc]` ciklusindex”: **CÁFOLVA** (§2).
- „A `0x004e5070` és a `0x00506830` ugyanazt a táblát olvassa”: **CÁFOLVA** (§4). Két külön objektum.
- „A `[elem+0x18]` a `0x00509350`-ben íródik”: **CÁFOLVA**. A `0x00509350` olvassa az elemet, és a rekordba másol (§4).
- „A `0x00449a00` a `0x00506830` párját kapja”: **CÁFOLVA**. Egy tételt kap (§5).
- „A `0x004e5740` visszatérése a `+0x18` érték”: **CÁFOLVA**. A visszatérése az index (§5).

##### §9 Nyitott lista (38.2.51 §9)

Nyitott kérdések mérlege (38.2.51): 54 tétel · 12 lezárva · 24 részben · 18 nincs meg. Az előző mérleg (38.2.50): 52 · 12 · 24 · 16. Új tétel: U53 és U54 (mindkettő NINCS MEG, mindkettő a fő kérdést blokkolja). Állapotváltozás nincs, de az U41, U49 és U50 szövege frissült. A 38.2.50 §9 tábla felülíródott.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U1 | NINCS MEG (változatlan) | a `0x00a6aa00` teljes törzse | `0x00a6aa00` |
| U2 | RÉSZBEN (változatlan) | az obj2 osztálya és a vt+0 cél | `0x005e8a70`, `M+0x4c` vt+0 |
| U3 | RÉSZBEN (változatlan) | a mód-tartó (`obj`, névhasználat) igazolt; az `L` osztálya NINCS MEG | `0x004a7890`, `0x004baaa0` |
| U4 | NINCS MEG (változatlan) | a `0x008014d0` vt+0 hívott függvénye | `0x008014d0` |
| U5 | NINCS MEG (változatlan) | a `[this+0x2ec]` olvasói | pásztázás |
| U6 | NINCS MEG (változatlan) | a `0x009aaae0` hívóhelyei | `0x009aaae0` |
| U7 | LEZÁRVA (38.2.41 §1) | a sorrekord `+0x14` írója | - |
| U8 | NINCS MEG (változatlan) | a `P' = [T+0x3a4]` írója | `0x007fa7f0` |
| U9 | LEZÁRVA (38.2.41 §2-3) | a kattintási ág | - |
| U10 | RÉSZBEN (változatlan) | a `0x004b8470` hívója és az `[L+0x148]` írói | `0x004b8ee0` |
| U11 | RÉSZBEN (változatlan) | az `L` osztálya, `+0xc == 2`, `jbe` | `0x004b29d0` |
| U12 | NINCS MEG (változatlan) | az EBP/EBX forrása a hívottakban | `0x004b2e10`, `0x004b3770`, `0x004b80d0` |
| U13 | RÉSZBEN (változatlan) | a `0x007fc010` | `0x007fc010` |
| U14 | RÉSZBEN (változatlan) | a `0x008014d0` törzse | `0x008014d0` |
| U15 | NINCS MEG (változatlan) | a startbutton vt+0x18 | `0x007fa7f0` |
| U16 | RÉSZBEN (változatlan) | a rendező kulcssorrendje igazolt; a G-táblák feltöltése U37 | `0x004a7890`, `0x004baaa0` |
| U17 | NINCS MEG (változatlan) | a `0x004b8d00` | `0x004b8d00` |
| U18 | NINCS MEG (változatlan) | az `E` görbe | `0x005568e0` |
| U19 | NINCS MEG (változatlan) | a rekord-utólagos és a ciklus-utáni lépés | `0x007fa650`, `0x00604480` |
| U20 | NINCS MEG (változatlan) | a kártya-rekord építése | `0x007fa5b0` |
| U21 | LEZÁRVA (38.2.43 §2) | a CSlice konstruktor és a destruktor-lánc | `0x004133e0`, `0x00413490` |
| U22 | RÉSZBEN (változatlan) | a `0x004406f0` a vt+0x2c cél; a `[L+0x48]` vtábla újra nincs igazolva | `0x00402f90`, U36 |
| U23 | LEZÁRVA a törzs (38.2.44 §2) | a sor neve | `0x004a71e0` |
| U24 | RÉSZBEN (38.2.48 §2) | a 4. mód igazolt; az 1. mód dupla a `0x00450bd0` (U32); a 0. mód a `G+0x18` tábla (forrása NINCS MEG) | `0x004502e0`, `0x004ae0d0`, `0x004a7890` |
| U25 | LEZÁRVA (38.2.48 §3) | a `0x00987030` törzse | `0x00987030`, `0x004a7ad4` |
| U26 | NINCS MEG (változatlan) | a K-másolás törzse | `0x00801915`-`0x00801bc4` |
| U27 | NINCS MEG (változatlan) | az `M+0x64c` és `M+0x650` írása | `0x005e8a70` |
| U28 | LEZÁRVA (38.2.45 §1) | a kulcs NÉV | `0x004dca40`, `0x004406f0` |
| U29 | RÉSZBEN (38.2.45 §2) | a `[X+0x1034]` CThumbDB írója LEZÁRVA; az `L` írója U36 | `0x00402f90`, U36 |
| U30 | RÉSZBEN (38.2.45 §4) | a G-szerep LEZÁRVA; a táblák feltöltése U37 | `0x004b94a0`, U37 |
| U31 | RÉSZBEN (38.2.46 §3.2) | a bemenet igazolt; a statisztika neve NINCS MEG | `0x00450100` |
| U32 | RÉSZBEN (38.2.49 §3, új) | a `0x00450bd0` 64 bites maximum-számítása igazolt; a 64 bites érték jelentése, a `0x0098b650` és a `0x006c9d60` NINCS MEG | `0x00450bd0`, `0x0098b650`, `0x006c9d60` |
| U33 | RÉSZBEN (38.2.47 §3.3) | a mód forrása parancs-ágankénti konstans; a parancsazonosító és az ág párosítása NINCS MEG | `0x005cb990`, `0x005d9cc0`, `0x004b07c0` |
| U34 | NINCS MEG (változatlan) | az OLEAUT32 184. sorszám neve | IAT `0x00c405c8` |
| U35 | RÉSZBEN (38.2.46 §1.3) | a literál szövege `token`; a rekord `+5` mezőjének tartalma NINCS MEG | `0x00415790`, `0x00985ff0`, `0x004941f0` |
| U36 | RÉSZBEN (38.2.47 §3.5) | az `[X+0x2c0]` a mód-tartó (ha `X = V`); az `X = V` NINCS MEG (U43) | `0x004b07c0`, `0x005d30f0`, `0x004502e0` |
| U37 | RÉSZBEN (38.2.47 §2.2) | a G-veremszerkezetet a hívó állítja be; a tartalmának feltöltése NINCS MEG | `0x004b94a0`, `0x004b8ee0` |
| U38 | LEZÁRVA (38.2.46 §2.2) | egyesítő rendezés; a kulcsot a `0x004a7890` adja | `0x004baaa0`, `0x004a7890` |
| U39 | RÉSZBEN (38.2.47 §2.1) | az `obj` a hívó `this`-e; a `0x004b94a0` első argumentuma O = `[X+0x2c0]` (38.2.49 §4) | `0x004b8ee0`, `0x006dc4c0`, `0x005fe130` |
| U40 | RÉSZBEN (38.2.48 §1.3) | a név-tábla írói igazoltak; az elemek fajtája NINCS MEG (U49, U50) | `0x00456610`, `0x00448560`, `0x004da1d0` |
| U41 | RÉSZBEN (38.2.51 §5) | a `0x00449a00` egy tételt kap, nem a párt; a `0x004db180` a `this+0x68` objektumot zárolja; a lista és a pár kapcsolata NINCS MEG (a `0x00484820` `esi`-forrása) | `0x00449a00`, `0x004db180`, `0x00484bbd`, `0x00484820` |
| U42 | RÉSZBEN (38.2.48 §1.3) | az írók megvannak; az azonosító (`param_3`) forrása a 0x467ca0 és a 0x425f60 útjában az index, de a fajtája NINCS MEG | `0x00456610`, `0x00448560` |
| U43 | NINCS MEG (változatlan) | az `X` azonos-e a `V = [[0xd67668]+0x102c]`-vel | `0x005cb9aa`, `0x004b07e8`, `0x006dc4c0` |
| U44 | RÉSZBEN (38.2.48 §2) | mindkét kulcs mechanikája LEZÁRVA; a dupla tartalma U32 | `0x004ae0d0`, `0x004507e0` |
| U45 | LEZÁRVA (38.2.49 §4) | a `0x005fe130` hívója és a `0x0056c5a0` első verem-argumentuma: O = `[X+0x2c0]`; X forrása nincs felvéve külön | `0x005fe130`, `0x0056c5a0` |
| U46 | LEZÁRVA (38.2.50 §1) | a törzs, a kimeneti pár és a `this` igazolt; a `0x00891110` a célba ír, a forrást csak olvassa | `0x00506830`, `0x00484a70`, `0x00484a5c`, `0x00891110` |
| U47 | LEZÁRVA (38.2.50 §2) | a lista elemének azonosítója a `0x00456610` `param_3`-a; a fajta NINCS MEG (U42) | `0x00493050`, `0x0045a8a6`, `0x0045a89b` |
| U48 | NINCS MEG (változatlan) | a `[owner+0x2e9c]` és a `[owner+0x2e94]` név írói, és a viszonyuk | `0x004489dc`, `0x00449a00` |
| U49 | RÉSZBEN (38.2.51 §4-5) | visszatérés és index LEZÁRVA (a `0x004e5070` három ága; a `0x004e5740` az indexszel tér vissza); a `+0x18` kimenete a `T2[index]` (`0x004e5a13`); a `T2` olvasója NINCS MEG (U53) | `0x004e5740`, `0x004e5070`, `0x004e5a13` |
| U50 | RÉSZBEN (38.2.51 §5) | `0x004ed450` = konténer-zár és vt+8 hívás az indexszel; `0x005c2100` = szöveg-értékadás; `0x004da1d0` NINCS MEG | `0x004ed450`, `0x005c2100`, `0x004da1d0` |
| U51 | LEZÁRVA (38.2.49 §4) | a `0x004b94a0` első verem-argumentuma `[X+0x2c0]`, X a `0x0056c5a0` első argumentuma | `0x0056d2b6`, `0x0056c5a0` |
| U52 | LEZÁRVA (38.2.50 §2) | a bemenő lista eleme a `0x00456610` `param_3`-a (asm); a fajta NINCS MEG | `0x004d9aa0`, `0x00458aeb`, `0x00458ad8`, `0x00458ae4` |
| U53 | NINCS MEG (új, 38.2.51 §5; blokkolja a fő kérdést; az ÍRÓ LEZÁRVA, 38.2.52 §1) | a `[konténer+0x480]` `T2` tábla olvasói: ki olvassa a `+0x58` mezőt, és mit csinál a számmal | `0x004e5a13`, `0x004e5740` |
| U54 | RÉSZBEN (38.2.52 §2-3; új a 38.2.51 §3-ban) | a `0x00a4c140` eredménye (`arg2 = 0`) LEZÁRVA; a `0x0046a8a2` és a `0x0046a8ad` NEM elem-építő ágak; a `P` forrása (a `0x00462ba0` kimenete) NINCS MEG; a `0x00a4c140` további hívóhelyei nincsenek követve | `0x00462ba0`, `0x00467fc7`, `0x0046aadf`, `0x0046aded`, `0x0046b1f3` |

**A felhasználó szemével**

Nincs két-három mondatos összefoglaló, mert a fő kérdés (az elem fajtája) nem dőlt el. Ami már áll: a verembe épített elem `+0x18` mezőjébe a törzs vagy a `2` számot, vagy egy visszatérési értéket ír, és ez a szám a rekord mellé kerül. Hogy ez kép, album vagy személy, azt három hiányzó cím dönti el: `0x004e5a13` (ki olvassa a `T2` táblát), `0x00a4c140` (az `arg2 = 0` ág értéke), és `0x0046a8a2`, `0x0046a8ad` (a másik két elem-építő ág).

#### 38.2.52 Az Időrend bináris feltárása, 35. kör: a T2 írója, a fájlkiterjesztés-tábla és a két cím, ami nem elem-építő (#5401, 2026-10-22)

**Kérdés és hatókör.** A 38.2.51 három kérdése: (1) a `0x004e5a13`: ki olvassa a `T2` táblát, és mit kezd az elemmel; (2) a `0x00a4c140` `arg2 = 0` ága; (3) a `0x0046a8a2` és a `0x0046a8ad`: mit ír az elem `+0x18` mezőjébe. Bemenet: `2026-10-22-idorend-35.txt` (a három cím dekompilátuma és hívólistái), a 38.2.51 §6 és §9 lista, és a bináris: diszasszemblálás (`pe_dis.cdis`), valamint a `0x00d33418` tábla közvetlen olvasása. Kódot nem módosítottunk, a CI-őrök nem futottak. Ideiglenes fájl nem készült.

**Válasz röviden.**
1. **Q1, a `0x004e5a13` (T2): a cím a T2 ÍRÓJA, nem olvasója. A T2 olvasója NINCS MEG.** A `0x004e5740` az elem `+0x18` értékét a `[konténer+0x480]` objektum `T2` táblájába (`+0x58`) írja, a `0x004e5070` által adott rekord-index helyére (§1). A bemenetben nincs a `T2` olvasója.
2. **Q2, a `0x00a4c140` `arg2 = 0` ága: LEZÁRVA.** Az érték egy szöveg fájlkiterjesztésének kódja a `0x00d33418` táblából (73 sor, például `.jpg` = 2, `.mp4` = 9, `.webp` = 31). Üres bemenetnél 0, egyezés nélkül `-1` (§2).
3. **Q3, a `0x0046a8a2` és a `0x0046a8ad`: NEM elem-építő ágak.** Az egyik a hibás keresés kilépése, a másik a `cStack_7ea5` jelző szerinti ág. Egyik sem ír `+0x18`-at. A `0x0040f980` (a `+0x18` írója) a `0x00467ca0` törzsében egyetlen helyen hívódik: `0x004680d9` (§3).
4. **A fő kérdés (az elem fajtája): NINCS MEG.** A `+0x18` mező fájltípus-kódot kap (§4), a kép, album vagy személy eldöntése a `T2` olvasóján múlik.

**Hatókör és módszer.** A dekompilátumból olvastuk a logikát, az elágazási és belépési pontokat a `pe_dis.cdis` gépi kódjával ellenőriztük. A `0x00467ca0` teljes gépi kódját (`0x00467ca0`-`0x0046d750`) egyszer végigszkenneltük a hívásokra és a célcímekre. A kiterjesztés-táblát közvetlenül a bináris `0x00d33418` címéről olvastuk (8 bájt soronként: szövegmutató és kód). Ideiglenes fájl nem készült.

##### §1 Q1: a `0x004e5a13`, a T2 írója (LEZÁRVA: író; U53 NINCS MEG: olvasó)

- A cím a `FUN_004e5740` belsejében van. A bemenet szerinti hívói: `0x004680e8` (`0x00467ca0`), `0x005054b2` (`0x00505030`), `0x0053ff8f` (`0x0053fe30`). A `0x0053fe30` a `0x00a4c140`-et is hívja, a `0x0053ff5a` címen, a `0x004e5740` hívása előtt. Ez a `0x00467ca0` mintája, a `0x0053fe30` törzsét nem néztük meg.
- Bemenet (asm): az elem az EAX-ban van (`0x004680e6`: `mov eax,esi`), a konténer verem-argumentum (`0x004e574f`: `mov ebp,[esp+0x2c]`).
- Lépések (a Ghidra-kimenet, asm-mal egyeztetve):
  1. `uVar6 = FUN_004e5070(elem)`: a rekord-index. Ha `-1`, nincs írás.
  2. `piVar2 = [konténer+0x480]`, `T2 = [piVar2+0x58]` (⚠️ JAVÍTVA, 38.2.53 §7: a `T2` a `piVar2+0x58` mezőben álló mutató által mutatott tábla-objektum, nem a mező címe; a `0x004e59f0` `mov eax,[ebx+0x58]` betöltése ezt mutatja). Ha bármelyik nulla, nincs írás.
  3. Ha az index kisebb a `T2` darabszámánál (`[T2+0x4c] >> 1`), és a régi érték más, akkor `T2[index] = elem+0x18`, majd jelzés a `[piVar2+0x50]+0x4c` objektumon (`0x006a2a60`).
  4. Ha az index nagyobb vagy egyenlő a darabszámmal, a `T2` nő. Az új helyek a `[piVar2+0x5c]` értéket kapják, az index helyére az elem `+0x18` értéke kerül.
- A `T2` olvasása a függvényen belül csak a 3. lépés egyezés-vizsgálata.
- **U53 (NINCS MEG):** a `T2` olvasói. A bemenet nem tartalmazza őket. Ghidra-kör kell: a `[konténer+0x480]` objektum osztálya és a `+0x58` mező olvasói. A `[piVar2+0x50]+0x4c` jelzés figyelője lehet az olvasó, de ez nincs igazolva. ⚠️ PONTOSÍTVA (38.2.53 §1, §7): a `0x00505030` konténere a saját argumentuma; a `0x0053fe30` konténere egy verembeli helyi objektum, és a hívás után saját T2-ágat is futtat.

##### §2 Q2: a `0x00a4c140` `arg2 = 0` ága (LEZÁRVA)

- Hívóhely: `0x004680b3` (asm, `0x004680a1`-`0x004680b3`). Ha `arg2 = 0` (az `esi` nulla, `0x0046809d`), a `P = [E-0x28a8]` mutató (a törzsben `[esp+0x5610]`) alapján az EDX = `P+4`, ha `P` nem nulla, egyébként 0.
- A `P` forrása: a `[esp+0x5610]` objektum a `0x00467e99`-`0x00467f8e` blokkban épül. A szöveg a `0x00462ba0` kimenetéből jön, az `arg2 = 0` ágon a `0x00467fc7` hívással. A másolási lépéseket nem követtük végig. Hogy a szöveg fájlnév, útvonal vagy más, **NINCS MEG**. Ghidra-kör kell (§6).
- A `0x00a4c140` (dekompilátum és asm):
  1. Ha a bemenet nulla vagy üres, a visszatérés 0.
  2. Különben a `0x00a4c6a0` a szöveg utolsó `.` karakterétől a végéig tartó részt adja. Ha nincs pont, az egész szöveget. (Az asm hátulról keres pontot.)
  3. Ezt a részt a `0x00d33418` tábla soraival hasonlítja `__strnicmp`-pel, a saját hosszán. Az első egyező sor értékét adja.
  4. Egyezés nélkül `0xffffffff` (-1).
- **Előtag-egyezés:** a hasonlítás a bemeneti rész hosszáig megy, nem a tábla-bejegyzés hosszáig. Ezért a rövidebb rész is egyezik a hosszabb bejegyzés elejével. Példa: `.j` -> 2 (a `.jpg` kódja). Ponttal nem kezdődő szöveg nem egyezik, mert a tábla kulcsai mind ponttal kezdődnek.
- A tábla (a `0x00d33418` binárisból olvasva, 73 bejegyzés, az utolsó után nulla mutató):

| kód | kiterjesztések |
|---|---|
| 2 | `.jpg` `.jpe` `.jpeg` |
| 3 | `.gif` |
| 6 | `.bmp` |
| 7 | `.psd` |
| 8 | `.avi` `.divx` |
| 9 | `.mov` `.mp4` `.3gp` `.3g2` `.m4v` |
| 10 | `.mpg` `.mpeg` `.ty` `.mts` `.m2t` `.m2ts` `.mmv` `.mkv` `.mod` `.tod` `.tp` `.ts` `.m2v` |
| 11 | `.wmv` |
| 12 | `.asf` |
| 13 | `.tif` `.tiff` |
| 14 | `.png` |
| 15 | `.mp3` |
| 18 | 27 RAW-kiterjesztés (`.raw`, `.crw`, `.cr2`, `.nef`, `.dng` és a többi) |
| 21 | `.url` |
| 22 | `.tga` |
| 27 | `.txt` |
| 28 | `.cpp` `.h` `.htm` `.html` `.css` `.js` `.py` `.rc` |
| 29 | `.ogg` `.ogv` |
| 31 | `.webp` |

- Fordított keresés: a `0x00a4c6e0` a kódból a kiterjesztés szövegét adja (asm; a hívóit nem néztük). A `0x00467ca0` törzsében külön ág van a 31-es kódra (dekompilátum: `iStack_7d0c == 0x1f` -> `.webp`), ez ugyanazt a kódkészletet mutatja.

##### §3 Q3: a `0x0046a8a2` és a `0x0046a8ad` (NEM elem-építő ágak; U54 javítva)

- A `0x0046808c` `jne 0x46a8a2` ugrás akkor fut, ha `ebx != 0`. Ez a dekompilátumban `iVar9 != 0`: a `0x00462ba0`, `0x00463270` és `0x009998c0` hívások egyike hibázott, vagy a `0x0046807c` `mov ebx,9` hibakód áll be. A `0x0046a8a2` (asm): `cmp byte [esp+0x1b],0`, `je 0x46a80d`. Ha a jelző nem nulla, a folytatás a `0x0046a8ad`.
- A `0x00468097` `jne 0x46a8ad` ugrás akkor fut, ha `cStack_7ea5 != 0`. Ez a `0x00472850` jelzője, a dekompilátumban csak `arg2 = 0` és `param_3 != 0` esetén számolják.
- A `0x0046a8ad` (asm): `mov ecx,[esp+0x1c]`, `mov [esp+0x7c],ecx`, `jmp 0x46a80d`. A `[esp+0x7c]` cél nem esik a `+0x18` elem területére (`E-0x7c24` és `E-0x7ae0` között).
- A `0x0046a80d` a közös folytatás: a `0x00462ba0` újrahívása (`0x0046a82a`), és a további ágak. Nem a `+0x18` írója.
- A `+0x18` írója a `0x0040f9de` (a `0x0040f980` konstruktor). A `0x00467ca0` teljes gépi kódjában a `0x0040f980` egyetlen hívása a `0x004680d9`.
- Az `arg2 != 0` ágon (`0x0046809d`: `jne 0x4680bc`) az `eax` a `2`-es értéken marad (`0x00468083`), és ezt írja a konstruktor.

##### §4 A `+0x18` értéke, összesítve

| ág | `+0x18` értéke | honnan |
|---|---|---|
| `arg2 != 0` | `2` (a `.jpg` kódja) | `0x00468083`, `0x0046809d` |
| `arg2 = 0`, `P` nulla vagy üres | `0` | `0x00a4c140` 1. lépés |
| `arg2 = 0`, a kiterjesztés szerepel a táblában | a kód (2, 3, 6 ... 31) | `0x00a4c140` 3. lépés |
| `arg2 = 0`, nincs egyezés | `-1` | `0x00a4c140` 4. lépés |

- Ezek mind fájltípus-kódok vagy jelzők. ⚠️ FELTÉTELESSÉ VÁLT (38.2.55 §4): a `+0x18` egész kódként csak akkor olvasható, ha a T2 egész típusú tömb; `char const*` tömbnél címként olvasódna. A táblában csak fájlkiterjesztések vannak, album vagy személy név szerint nincs köztük. Ez nem zárja ki, hogy a `T2` olvasója a kódból mást csinál. Az olvasót nem láttuk (U53).
- Az `arg2 = 0` ágon a `0x00456610` is hívódik a 3-as konstanssal (dekompilátum: `FUN_00456610(abStack_7bd8, puVar10, 3, 0, 0)`). Ez a 38.2.51 U42 tételéhez tartozik, és lehetséges másik út a fő kérdéshez.

##### §5 Bizonyítottsági fok (38.2.52)

| állítás | bizonyíték | fok |
|---|---|---|
| a `0x004e5a13` a `0x004e5740` belsejében van, a T2 írója | dekompilátum; a `0x004e5740` belépése asm | megerősített |
| a T2-írás feltételei (index, nulla-ellenőrzés, jelzés) | dekompilátum | megerősített (dekompilátum) |
| a T2 olvasói | nincsenek a bemenetben | NINCS MEG |
| `arg2 != 0` esetén `+0x18 = 2` | `0x00468083`, `0x0046809d`, `0x004680bc` | megerősített (asm) |
| `esi = arg2` a `0x0046809d`-ben | `0x00467cb8` (E+8 olvasás), `0x00467ccc`, `0x00467e6d` | megerősített (asm) |
| `arg2 = 0` esetén a `P+4` kiterjesztés-kódja a `0x00a4c140` értéke | asm `0x004680a1`-`0x004680b3`; `0x00a4c140` dekompilátum; `0x00a4c6a0` asm | megerősített |
| a 73 soros tábla és a kódok | a `0x00d33418` binárisból olvasva | megerősített (bináris) |
| üres bemenet -> 0, egyezés nélkül -> -1 | dekompilátum | megerősített |
| a `.webp` = 31 egyezik a `0x00467ca0` 31-es ágával | tábla + dekompilátum | megerősített |
| `0x0046a8a2`: `iVar9 != 0` kilépés | `0x0046808c` `jne` | megerősített (asm) |
| `0x0046a8ad`: `cStack_7ea5 != 0` ág, nem ír `+0x18`-at | `0x00468097` `jne`; `0x0046a8ad` asm | megerősített |
| a `0x0040f980` egyetlen hívása a `0x00467ca0`-ban | a teljes törzs gépi kódjának szkennelése | megerősített |
| `P` forrása a `0x00462ba0` kimenete | `0x00467fc7` hívás; a másolás nincs végigkövetve | RÉSZBEN |
| a `0x00456610` 3-as argumentuma az `arg2 = 0` ágon | dekompilátum | megerősített (dekompilátum) |

##### §6 Ghidra-címek a következő körhöz

Blokkolók a fő kérdésre:
- `0x004e5a13` olvasói (U53): Ghidra-kör kell: a `0x004e5740` `[konténer+0x480]` objektumának osztálya és a `+0x58` (T2) mező olvasói. Ehhez a `0x00505030` (`0x005054b2`) és a `0x0053fe30` (`0x0053ff8f`) konténere is kell.
- `P` forrása (U54): Ghidra-kör kell: a `0x00462ba0` kimenete és a `param_3` (E+0xc) a hívóhelyeken (`0x00467f38`, `0x00467fc7`), és a `0x00467e99`-`0x00467f8e` másolási lánc (`0x00991f00`, `0x00985af0`).
- A `0x00a4c140` további hívóhelyei a `0x00467ca0`-ban (`0x0046aadf`, `0x0046aded`, `0x0046b1f3`): Ghidra-kör kell: mit csinálnak az eredménnyel. A törzsben a `0x0040f980` csak a `0x004680d9`-nél hívódik.

Másik út a fő kérdéshez:
- `0x00456610` 3-as argumentuma (U42): Ghidra-kör kell: a `0x00456610` törzse, és az, hogy a 3-as konstans mit jelent az `arg2 = 0` ágon.

Lezárt, nem kell tovább:
- `0x0046a8a2`, `0x0046a8ad`: nem elem-építő ágak.
- `0x00a4c140`: a törzs lezárva. `0x00a4c6a0`: asm-mal megerősítve.

##### §7 Javítások a korábbi szakaszokban (38.2.51)

- §3, a `0x00a4c140` visszatérési értéke (NINCS MEG): **⚠️ JAVÍTVA**, LEZÁRVA (§2).
- §3, „Mit jelent a `2`” (NINCS MEG): **⚠️ PONTOSÍTVA**: a `2` a `.jpg` kódja (§2, §4).
- §3, „Két további ág” (a `0x00468081` és a `0x00468092` ugrásai): **⚠️ JAVÍTVA**: az ugrások a `0x0046808c` és a `0x00468097`, a céljaik nem elem-építő ágak (§3).
- §6 és §9 (U54: az elem-építő ág, és a `0x00a4c1ad` ágcím): **⚠️ JAVÍTVA** (§2, §3). A `0x00a4c1ad` ágcímet ebben a körben nem ellenőriztük.
- §9, U54: NINCS MEG -> RÉSZBEN.
- §9, U53: a szövege pontosítva. Az író LEZÁRVA (§1), az olvasó NINCS MEG.

##### §8 Amit KIZÁRTAM

- „A `0x0046a8a2` és a `0x0046a8ad` más elem-építést jelent”: CÁFOLVA (§3).
- „A `0x00a4c140` visszatérése kép-, album- vagy személy-jelölés”: CÁFOLVA, fájlkiterjesztés-kód (§2).
- „A `+0x18` több helyen íródik a `0x00467ca0`-ban”: CÁFOLVA, egy hívás van (§3).
- „A `T2` olvasóját ez a kör megtalálta”: nem állítjuk. NINCS MEG (U53).

##### §9 Nyitott lista (38.2.52 §9, felülírva: lásd 38.2.53 §9)

Nyitott kérdések mérlege (38.2.52): 54 tétel · 12 lezárva · 25 részben · 17 nincs meg. Az előző mérleg (38.2.51): 54 · 12 · 24 · 18. Változás: U54 NINCS MEG -> RÉSZBEN. Új tétel nincs.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U1 | NINCS MEG (változatlan) | a `0x00a6aa00` teljes törzse | `0x00a6aa00` |
| U2 | RÉSZBEN (változatlan) | az obj2 osztálya és a vt+0 cél | `0x005e8a70`, `M+0x4c` vt+0 |
| U3 | RÉSZBEN (változatlan) | a mód-tartó igazolt; az `L` osztálya NINCS MEG | `0x004a7890`, `0x004baaa0` |
| U4 | NINCS MEG (változatlan) | a `0x008014d0` vt+0 hívott függvénye | `0x008014d0` |
| U5 | NINCS MEG (változatlan) | a `[this+0x2ec]` olvasói | pásztázás |
| U6 | NINCS MEG (változatlan) | a `0x009aaae0` hívóhelyei | `0x009aaae0` |
| U7 | LEZÁRVA (38.2.41 §1) | a sorrekord `+0x14` írója | - |
| U8 | NINCS MEG (változatlan) | a `P' = [T+0x3a4]` írója | `0x007fa7f0` |
| U9 | LEZÁRVA (38.2.41 §2-3) | a kattintási ág | - |
| U10 | RÉSZBEN (változatlan) | a `0x004b8470` hívója és az `[L+0x148]` írói | `0x004b8ee0` |
| U11 | RÉSZBEN (változatlan) | az `L` osztálya, `+0xc == 2`, `jbe` | `0x004b29d0` |
| U12 | NINCS MEG (változatlan) | az EBP/EBX forrása a hívottakban | `0x004b2e10`, `0x004b3770`, `0x004b80d0` |
| U13 | RÉSZBEN (változatlan) | a `0x007fc010` | `0x007fc010` |
| U14 | RÉSZBEN (változatlan) | a `0x008014d0` törzse | `0x008014d0` |
| U15 | NINCS MEG (változatlan) | a startbutton vt+0x18 | `0x007fa7f0` |
| U16 | RÉSZBEN (változatlan) | a rendező kulcssorrendje igazolt; a G-táblák feltöltése U37 | `0x004a7890`, `0x004baaa0` |
| U17 | NINCS MEG (változatlan) | a `0x004b8d00` | `0x004b8d00` |
| U18 | NINCS MEG (változatlan) | az `E` görbe | `0x005568e0` |
| U19 | NINCS MEG (változatlan) | a rekord-utólagos és a ciklus-utáni lépés | `0x007fa650`, `0x00604480` |
| U20 | NINCS MEG (változatlan) | a kártya-rekord építése | `0x007fa5b0` |
| U21 | LEZÁRVA (38.2.43 §2) | a CSlice konstruktor és a destruktor-lánc | `0x004133e0`, `0x00413490` |
| U22 | RÉSZBEN (változatlan) | a `0x004406f0` a vt+0x2c cél | `0x00402f90`, U36 |
| U23 | LEZÁRVA (38.2.44 §2) | a sor neve | `0x004a71e0` |
| U24 | RÉSZBEN (38.2.48 §2) | a 4. mód igazolt; az 1. mód dupla a `0x00450bd0` (U32); a 0. mód forrása NINCS MEG | `0x004502e0`, `0x004ae0d0`, `0x004a7890` |
| U25 | LEZÁRVA (38.2.48 §3) | a `0x00987030` törzse | `0x00987030`, `0x004a7ad4` |
| U26 | NINCS MEG (változatlan) | a K-másolás törzse | `0x00801915`-`0x00801bc4` |
| U27 | NINCS MEG (változatlan) | az `M+0x64c` és `M+0x650` írása | `0x005e8a70` |
| U28 | LEZÁRVA (38.2.45 §1) | a kulcs NÉV | `0x004dca40`, `0x004406f0` |
| U29 | RÉSZBEN (38.2.45 §2) | a `[X+0x1034]` CThumbDB írója LEZÁRVA; az `L` írója U36 | `0x00402f90`, U36 |
| U30 | RÉSZBEN (38.2.45 §4) | a G-szerep LEZÁRVA; a táblák feltöltése U37 | `0x004b94a0`, U37 |
| U31 | RÉSZBEN (38.2.46 §3.2) | a bemenet igazolt; a statisztika neve NINCS MEG | `0x00450100` |
| U32 | RÉSZBEN (38.2.49 §3) | a `0x00450bd0` 64 bites maximum-számítása igazolt; a jelentés NINCS MEG | `0x00450bd0`, `0x0098b650`, `0x006c9d60` |
| U33 | RÉSZBEN (38.2.47 §3.3) | a mód forrása parancs-ágankénti konstans; a párosítás NINCS MEG | `0x005cb990`, `0x005d9cc0`, `0x004b07c0` |
| U34 | NINCS MEG (változatlan) | az OLEAUT32 184. sorszám neve | IAT `0x00c405c8` |
| U35 | RÉSZBEN (38.2.46 §1.3) | a literál szövege `token`; a rekord `+5` mezője NINCS MEG | `0x00415790`, `0x00985ff0`, `0x004941f0` |
| U36 | RÉSZBEN (38.2.47 §3.5) | az `[X+0x2c0]` a mód-tartó (ha `X = V`); az `X = V` NINCS MEG (U43) | `0x004b07c0`, `0x005d30f0`, `0x004502e0` |
| U37 | RÉSZBEN (38.2.47 §2.2) | a G-veremszerkezetet a hívó állítja be; a tartalmának feltöltése NINCS MEG | `0x004b94a0`, `0x004b8ee0` |
| U38 | LEZÁRVA (38.2.46 §2.2) | egyesítő rendezés; a kulcsot a `0x004a7890` adja | `0x004baaa0`, `0x004a7890` |
| U39 | RÉSZBEN (38.2.47 §2.1) | az `obj` a hívó `this`-e | `0x004b8ee0`, `0x006dc4c0`, `0x005fe130` |
| U40 | RÉSZBEN (38.2.48 §1.3) | a név-tábla írói igazoltak; az elemek fajtája NINCS MEG (U49, U50) | `0x00456610`, `0x00448560`, `0x004da1d0` |
| U41 | RÉSZBEN (38.2.51 §5) | a `0x00449a00` egy tételt kap, nem a párt; a lista és a pár kapcsolata NINCS MEG | `0x00449a00`, `0x004db180`, `0x00484bbd`, `0x00484820` |
| U42 | RÉSZBEN (38.2.48 §1.3) | az írók megvannak; a `param_3` forrása az index, a fajtája NINCS MEG; a `0x00456610` 3-as argumentuma új nyom (38.2.52 §4) | `0x00456610`, `0x00448560` |
| U43 | NINCS MEG (változatlan) | az `X` azonos-e a `V = [[0xd67668]+0x102c]`-vel | `0x005cb9aa`, `0x004b07e8`, `0x006dc4c0` |
| U44 | RÉSZBEN (38.2.48 §2) | mindkét kulcs mechanikája LEZÁRVA; a dupla tartalma U32 | `0x004ae0d0`, `0x004507e0` |
| U45 | LEZÁRVA (38.2.49 §4) | a `0x005fe130` hívója és a `0x0056c5a0` első argumentuma | `0x005fe130`, `0x0056c5a0` |
| U46 | LEZÁRVA (38.2.50 §1) | a törzs, a kimeneti pár és a `this` igazolt | `0x00506830`, `0x00484a70`, `0x00484a5c`, `0x00891110` |
| U47 | LEZÁRVA (38.2.50 §2) | a lista elemének azonosítója a `0x00456610` `param_3`-a; a fajta NINCS MEG (U42) | `0x00493050`, `0x0045a8a6`, `0x0045a89b` |
| U48 | NINCS MEG (változatlan) | a `[owner+0x2e9c]` és a `[owner+0x2e94]` név írói | `0x004489dc`, `0x00449a00` |
| U49 | RÉSZBEN (38.2.52 §1) | visszatérés és index LEZÁRVA; a `+0x18` a `T2[index]`-be kerül (`0x004e5a13`, LEZÁRVA); a `T2` olvasója NINCS MEG (U53) | `0x004e5740`, `0x004e5070`, `0x004e5a13` |
| U50 | RÉSZBEN (38.2.51 §5) | `0x004ed450` = konténer-zár és vt+8 hívás az indexszel; `0x005c2100` = szöveg-értékadás; `0x004da1d0` NINCS MEG | `0x004ed450`, `0x005c2100`, `0x004da1d0` |
| U51 | LEZÁRVA (38.2.49 §4) | a `0x004b94a0` első verem-argumentuma `[X+0x2c0]` | `0x0056d2b6`, `0x0056c5a0` |
| U52 | LEZÁRVA (38.2.50 §2) | a bemenő lista eleme a `0x00456610` `param_3`-a; a fajta NINCS MEG | `0x004d9aa0`, `0x00458aeb`, `0x00458ad8`, `0x00458ae4` |
| U53 | NINCS MEG (38.2.52 §1: az ÍRÓ LEZÁRVA) | a `T2` olvasói: ki olvassa a `+0x58` mezőt, és mit csinál a számmal | `0x004e5a13`, `0x004e5740` |
| U54 | RÉSZBEN (38.2.52 §2-3) | a `0x00a4c140` eredménye (`arg2 = 0`) LEZÁRVA; a `0x0046a8a2` és a `0x0046a8ad` NEM elem-építő; a `P` forrása NINCS MEG | `0x00462ba0`, `0x00467fc7`, `0x0046aadf`, `0x0046aded`, `0x0046b1f3` |

A felhasználó szemével

Ezen az úton még nem dől el, hogy a tétel kép, album vagy személy. A `+0x18` mező fájltípus-kódot tárol (például `.jpg` = 2, `.mp4` = 9), és nem tudjuk, mit csinál vele a `T2` olvasója. Ezen az úton tehát nem dönthető el: a `T2` olvasóinak megkeresése kell, Ghidra-körben (U53).

#### 38.2.53 Az Időrend bináris feltárása, 36. kör: a T2 olvasói, a két új író, a jelzés figyelője (#5401, 2026-10-22)

**Kérdés és hatókör.** A 38.2.52 §9 fő kérdése (U53): ki olvassa a `T2` táblát (a `[konténer+0x480]` objektum `+0x58` mutatója), és mit kezd az elem `+0x18` fájltípus-kódjával. A kör kizárólag ezt vizsgálta, új nyitott tétel nem került fel. Bemenet: `2026-10-22-idorend-36.txt` (a `0x00505030`, a `0x0053fe30` és a `0x006a2a60` dekompilátuma és hívólistái), a 38.2.52 §6 és §9 lista, és a bináris: diszasszemblálás (`pe_dis.cdis`), a teljes `.text` mintás pásztázása (`paszta.utasitasok`, szöveges mezőkkel), az index `functions` és `rtti` táblája. Kódot nem módosítottunk, a CI-őrök nem futottak. Ideiglenes fájl nem készült.

**Válasz röviden.**
1. **Q1, a két új író.** A konténer és az elem LEZÁRVA. A vtábla-azonosság NINCS MEG. A `0x00505030` a `0x004e5740`-et hívja, a konténer a saját argumentuma. A `0x0053fe30` ugyanezt hívja egy verembeli helyi objektummal, és a hívás után saját T2-ágat futtat, amelynek a táblája nincs igazolva.
2. **Q2, a jelzés figyelője.** ⚠️ JAVÍTVA (38.2.54 §2): a `0x006a2a60` olvassa és írja a T2 adattömbjét, mert a T2 a figyelő belsejében van (`+0xa4`). A figyelő a `[piVar2+0x54]` objektum. Az osztálya NINCS MEG.
3. **Q3, a T2 olvasói.** RÉSZBEN. Kilenc metódus olvassa a T2 mutatóját, és többnyire konstansokat ír a táblába. Két függvény (`0x00467ca0`, `0x0046d7d0`) indexszel olvassa a T2 adatát, határ-ellenőrzéssel.
4. **A fő kérdés (kép, album vagy személy).** NINCS MEG. A két adatolvasó felhasználását a dekompilátum további része mutatná.

##### §1 Q1: a két új író

- **`0x00505030`.** Az argumentum (`param_1`) az `EBX`-be kerül (`mov ebx,[esp+0x2d98]`, `0x00505049`). A hívóhely: `push ebx` (`0x005054a3`), `lea eax,[esp+0xd8]` (`0x005054a4`), `call 0x004e5740` (`0x005054b2`). A konténer tehát a függvény argumentuma, az elem a helyi `[esp+0xd8]` rekord. A törzsben nincs `+0x58` vagy `+0x4c` hozzáférés, a T2-írást a `0x004e5740` végzi.
- **`0x0053fe30`.** A hívóhely a `0x0053ff8f`. A `lea edx,[esp+0x3c8]` és a `push edx` (`0x0053ff85`, `0x0053ff8c`) adja a konténert, vagyis a verembe tolt helyi objektumot. A `mov eax,esi` (`0x0053ff8d`, az `esi` a `lea [esp+0x88]`) az elemet adja. A dekompilátum ezt `FUN_004e5740(auStack_5c60)` alakban mutatja. A visszatérési érték a rekord-index (`uVar8`). A bemeneti fájl 1055-1104. sorában a `0x0053fe30` saját ágat futtat: az `iStack_4890` táblát a T2 mintájára használja (`+0x48` adat, `+0x4c` darabszám), és a jelzést a `0x0054053a`, `0x00540a8c`, `0x00540d23` hívásokkal küldi.
- **Két hiány az `iStack_4890` ágánál.** Az `iStack_4890`, `iStack_4898` és `iStack_4648` értékadásai a dekompilátumban nincsenek meg, csak a deklaráció van. Ezért nem igazolt, hogy az `iStack_4890` a `[konténer+0x480]+0x58`. Az ágban a táblaelemeket szövegként hasonlítja (`(byte)*puVar18`), ami nem illik a `0x004e5740` egész-kódos írásához. A tábla azonossága NINCS MEG. Ghidra-kör kell: a `0x0053fe30` `iStack_4890` és `iStack_4898` értékadásai.
- **A vtábla-azonosság (Q1 második fele): NINCS MEG.** A két hívóhely konténerének vtábla-címét ezekben a függvényekben nem látjuk. A `0x004e41f0` konstruktor a `[ebp+0]` mezőbe előbb `0xc86c44`-et, utána `0xc86be0`-t ír (`0x004e420b`, `0x004e423e`), és a `[ebp+0x480]` mezőt az `EBX`-szel tölti (`0x004e4586`). Az `EBX` értékét nem igazoltuk. Azt sem tudjuk, hogy ez a konstruktor építi-e a két hívóhely konténerét. ⚠️ JAVÍTVA (38.2.54 §3): az `rtti` táblában van sor: `0x00c86be0` = `ytDirScanner::vftable`, `0x00c86c44` = `ytBaseThreadPausable::vftable`, így az osztálynév LEZÁRVA.
- **A `0x004e5740` belépése.** A verem-argumentum a konténer (`mov ebp,[esp+0x2c]`, `0x004e574f`), az elem az `EAX` (`mov esi,eax`, `0x004e5747`). Ez javítja a 38.2.51 szakaszt, lásd §7.

##### §2 Q2: a jelzés figyelője

- **Hívóhely.** A `0x004e5a09` a `0x004e5740` belsejében van. Előtte a `0x004e59fd`-`0x004e5a06` sorban: `mov ecx,[ebx+0x50]`, `add ecx,0x4c`, `push ecx`, `mov esi,[ebx+0x54]` (`0x004e5a00`), `mov edi,edx`. A `0x0053fe30` hívóhelyei közül a `0x0054053a`-t néztük meg: itt `esi = [esp+0x1798]`, a verem-argumentum `[esp+0x1790]+0x4c`. A másik két hívóhelyet (`0x00540a8c`, `0x00540d23`) gépi kódban nem néztük.
- **A verem-argumentum** a `[piVar2+0x50]+0x4c` cím. Ez egy rekord: a dword-ját a `0x006a2a60` növeli, a bájtját 1-re állítja (`*param_1 += 1`, `param_1[1] = 1`).
- **A figyelő: `ESI` = `[piVar2+0x54]`**, az `EDI` a rekord-index. Az osztálya NINCS MEG. Ghidra-kör kell: a `[piVar2+0x54]` objektum konstruktora.
- **A `0x006a2a60` törzse** a figyelő saját mezőit használja: a `[ESI+0x328]` típuskódot (`cmp [esi+0x328], 0x13320006`, `0x006a2a6b`), az `[ESI+0xec]` mutatótömböt az `EDI` indexszel, a `[ESI+0x32c]` objektum vtábla-hívását (slot +8), a `FUN_004936c0(ESI+0x5c, ...)` és a `FUN_009bbb70` hívást. A T2 mezői (`+0x48`, `+0x4c`) nincsenek a törzsben, ez azonban félrevezető: ⚠️ JAVÍTVA (38.2.54 §2): a T2 adattömbje a figyelő `+0xec` mezőjén van, és a törzs ezt olvassa és írja.
- A `0x13320006` típuskód `push`-ként a `0x00499550` törzsében van (`0x00499569`). Hogy ez a figyelő konstruktora-e: NINCS MEG.

##### §3 Q3: a T2 olvasói (mintás pásztázás, a teljes `.text`)

A pásztázás négy mintát futtatott, a 2 884 879 utasításon:

- **(a)** `[X+0x58]` mutató-betöltés, amelyet `[R+0x48]` vagy `[R+0x4c]` követ 8 utasításon belül: 656 találat. Ez túl általános, sok osztály használ `+0x58` mutatót, ezért önmagában nem bizonyíték.
- **(b)** `[X+0x480]` hozzáférés: 16 betöltés és 13 írás (⚠️ PONTOSÍTVA, 38.2.56 §2: a dword-írás a hét függvényben tíz, a 13-as szám nem reprodukálható). Az írók: `0x00466700`, `0x004e41f0`, `0x00612ae0`, `0x0067df90`, `0x0067e6a0`, `0x0068c880`, `0x0068eea0`. A betöltők: `0x004e5210`, `0x004e5740`, `0x004e5a80`, `0x004eec80`, `0x004ef040`, `0x004f3510`, `0x004f46b0`, `0x004fcc50`, `0x00506790`, `0x00507590`, `0x0054f520`.
- **(c)** `[X+0x58]` olvasás a (b) betöltőiben (a `[esp+...]` verem-hozzáféréseket kihagyva): kilenc függvényben, köztük a `0x004e5740`: `0x004e5210`, `0x004e5740`, `0x004e5a80`, `0x004eec80`, `0x004ef040`, `0x004f3510`, `0x004f46b0`, `0x004fcc50`, `0x00507590`. A `0x00506790` és a `0x0054f520` nem olvassa a `+0x58` mezőt.
- **(d)** Indexelt adatolvasás a (a) mintából, `[R+0x48]` után `mov r,[D+i*4]` alakban: négy találat, két függvényben. A `0x00467ca0`-ban (`0x0046ba81`, `0x0046bafe`) és a `0x0046d7d0`-ban (`0x0047054b`, `0x004705dc`).

**A kilenc függvény a T2 mutatón keresztül:**

- **Írás konstanssal vagy elemmel:** `0x004e5210`: `T2[idx] = 1` (`0x004e565a`). `0x004eec80`: `T2[idx] = 4` (`0x004eee90`). `0x004f3510`: `T2[idx] = 1` (`0x004f41aa`). `0x00507590`: `T2[idx] = 0x3e9` (`0x00507a9b`). `0x004e5740`: `T2[idx] = elem+0x18` (`0x004e59fa`).
- **Csak mutató-betöltés és NULL-ellenőrzés:** `0x004e5a80`, `0x004ef040`, `0x004f46b0`, `0x004fcc50`. Ezeknél a további teendőt nem néztük. ⚠️ JAVÍTVA (38.2.58 §7): a `0x004ef040` nem csak betölt, hanem `elem+0x18 = arg3`-at ír (`0x004ef302`). A `0x004f46b0` (`0x004f4f24`) a T2 darabszámát olvassa ciklus-határként (`shr edi,1`). A `0x004e5a80` `0x004e5f8b`-es olvasójának alapja (`eax`) nincs igazolva.
- Az egyetlen indexelt betöltés a kilenc függvényben a `0x004f3510`-ben van (`0x004f3f3b`), de az láncolt-lista tömböt érint (`mov ecx,[eax+edi*4]`, majd `mov [eax+edi*4],esi`), nem a T2-t.

**Az indexelt adatolvasók (d):**

- `0x00467ca0`: `mov eax,[esi+0x58]` (`0x0046ba66`), majd a darabszám-ellenőrzés `cmp ecx,[esp+0x7ebc]` (`0x0046ba6e`). Ha az index a tartományon belül van, `mov ebp,[edx+eax*4]` (`0x0046ba81`), különben `mov ebp,[esi+0x5c]` (`0x0046ba86`). A második olvasó (`0x0046bae8`-`0x0046bafe`) ugyanígy működik, `mov edi,[eax+ecx*4]`-gyel.
- `0x0046d7d0`: `mov eax,[edi+0x58]` (`0x0047053c`), ellenőrzés `cmp ecx,esi` (`0x00470544`). Ha az index a tartományon belül van, `mov eax,[edx+esi*4]` (`0x0047054b`), és `mov [esp+0x68],eax` (`0x0047054e`). Különben `mov ecx,[edi+0x5c]` (`0x00470554`). A második olvasó (`0x004705cd`-`0x004705dc`) ugyanígy működik.
- Az alapérték (`[X+0x5c]`) ugyanaz a mező, amelyet a `0x004e5740` a bővítő ágban használ: `mov edi,[ebx+0x5c]` (`0x004e59e3`), és ezzel tölti ki az új helyeket (`0x004e59e6`).

##### §4 Mit kezdenek a `+0x18` kóddal

- **Írják:** a `0x004e5740` a `T2[idx]`-be az elem `+0x18` értékét írja (`0x004e59fa`, ha a régi érték más, lásd 38.2.52 §1). Más függvények konstansokat írnak ugyanabba a táblába (1, 4, 0x3e9), tehát a `+0x18` érték felülíródhat.
- **Olvassák:** két függvény (`0x00467ca0`, `0x0046d7d0`) indexszel olvassa a T2-t. ⚠️ PONTOSÍTVA (38.2.54 §3): a harmadik olvasó a `0x006a2a60` (a figyelő `+0xec` mezőjén). A `0x00467ca0` a `0x004680e8`-nál hívja a `0x004e5740`-et (38.2.52 §1). Tehát ugyanabban a függvényben van az írás és az olvasás, a T2 körforgása a `0x00467ca0`-ban zárul.
- **Mire használják a betöltött értéket: NINCS MEG.** A `0x00467ca0` az `EBP`-be tölti (`0x0046ba81`), majd a `0x0046ba89`-nél `lea eax,[esp+0x70]` és `call 0x0041edb0` következik, a betöltött érték ebben a néhány utasításban nem szerepel. A `0x0046d7d0` a `[esp+0x68]` helyre írja, a további használatát nem követtük. Ghidra-kör kell: `0x00467ca0` és `0x0046d7d0` dekompilátuma. ⚠️ PONTOSÍTVA (38.2.54 §1, §3): a `0x00467ca0` értéke nulla-tesztben szerepel (`0x0046bb36`-`0x0046bb3c`), a `0x0046d7d0` értékei a `0x009b93f0` argumentumai.

##### §5 Bizonyítottsági fok (38.2.53)

| állítás | bizonyíték | fok |
|---|---|---|
| a `0x00505030` konténere a függvény argumentuma (`EBX`), az elem a `[esp+0xd8]` rekord | asm `0x00505049`, `0x005054a3`, `0x005054a4`, `0x005054b2` | megerősített |
| a `0x0053fe30` a `0x004e5740`-et a `[esp+0x3c8]` konténerrel és a `[esp+0x88]` elemmel hívja | asm `0x0053ff71`, `0x0053ff85`, `0x0053ff8c`, `0x0053ff8d`, `0x0053ff8f` | megerősített |
| a `0x0053fe30` a hívás után saját T2-ágat futtat (`iStack_4890`, jelzéssel) | dekompilátum, a bemenet 1055-1104. sora | erős; a tábla azonossága NINCS MEG |
| az `iStack_4890` a `[konténer+0x480]+0x58` | nincs értékadás a dekompilátumban | NINCS MEG. Ghidra-kör kell: `0x0053fe30` (`iStack_4890` és `iStack_4898` értékadásai) |
| a `0x006a2a60` figyelője a `[piVar2+0x54]` objektum | asm `0x004e5a00` (`mov esi,[ebx+0x54]`), `0x004e5a07` | megerősített (a `0x004e5740` hívóhelye) |
| a `0x006a2a60` nem olvassa a T2 `+0x48`, `+0x4c` mezőit | dekompilátum és asm | megerősített, de nem zárja ki az olvasást: a T2 adattömbje a figyelő `+0xec` mezőjén van (38.2.54 §2) |
| a figyelő osztálya | nincs adat | NINCS MEG. Ghidra-kör kell: `0x00499550` (`0x00499569`) környezete és a konstruktor |
| a konténer-konstruktor (`0x004e41f0`) vtábla-címei `0xc86c44`, majd `0xc86be0` | asm `0x004e420b`, `0x004e423e` | megerősített; ⚠️ JAVÍTVA (38.2.54 §3): az osztálynév `ytDirScanner` (rtti-sor) |
| kilenc metódus olvassa a T2 mutatót | mintás pásztázás a teljes `.text`-en, a (b) betöltők törzsében | megerősített; a teljesség NINCS MEG (csak a `[X+0x58]` minta) |
| két függvény indexszel olvassa a T2 adatát | mintás pásztázás, asm `0x0046ba81`, `0x0046bafe`, `0x0047054b`, `0x004705dc` | megerősített |
| a betöltött érték felhasználása | ⚠️ PONTOSÍTVA (38.2.54 §1, §3): a `0x00467ca0` nulla-tesztben, a `0x0046d7d0` szélességként és magasságként (`0x009b93f0`) használja | RÉSZBEN |

##### §6 Ghidra-címek a következő körhöz

- `0x00467ca0`: a `0x0046ba81` (`EBP`) és a `0x0046bafe` (`EDI`) után a betöltött érték felhasználása. A `[esp+0x70]` rekord és a `0x0041edb0` hívás szerepe. ⚠️ FRISSÍTVE: 38.2.54 §1 és §6.
- `0x0046d7d0`: a `[esp+0x68]` (`0x0047054e`) és a `[esp+0x3c]` (`0x004705df`) felhasználása. A `0x0046d7d0` hívóinak listája. ⚠️ FRISSÍTVE: 38.2.54 §2 és §6.
- `0x0053fe30`: az `iStack_4890`, `iStack_4898`, `iStack_4648` és a `[esp+0x1790]`, `[esp+0x1798]` értékadásai, amelyeket a dekompilátum nem mutat. Ghidra-kör kell, vagy a gépi kód a `0x0053fe30` és a `0x0054053a` között.
- `0x004e41f0`: ⚠️ LEZÁRVA (38.2.54 §3): a konténer osztálya `ytDirScanner` (`0x00c86be0`), az ősi vtábla `ytBaseThreadPausable` (`0x00c86c44`).
- `0x00499550`: a `push 0x13320006` környezete (`0x00499569`), vagyis a figyelő osztálya. Ghidra-kör kell.

##### §7 Javítások a korábbi szakaszokban

- **38.2.52 §1, „T2 = piVar2+0x58”:** ⚠️ JAVÍTVA. A `T2` nem a `piVar2+0x58` cím, hanem az a tábla-objektum, amelyre a `[piVar2+0x58]` mutat. A bizonyíték: `0x004e59f0` (`mov eax,[ebx+0x58]`, `mov ecx,[eax+0x48]`), és a 38.2.51 §5 `eax = [esi+0x48]` lépése.
- **38.2.52 §1, „a másik két író konténerét meg kell nézni”:** ⚠️ PONTOSÍTVA. A `0x00505030` csak meghívja a `0x004e5740`-et, a konténere a saját argumentuma (§1). A `0x0053fe30` a hívás után beágyazott T2-ágat futtat, a tábla azonossága NINCS MEG (§1).
- **38.2.51, a `0x004e5740` „Belépés” sora:** ⚠️ JAVÍTVA. Az egy verem-argumentum a konténer (`[esp+0x2c]`), az elem az `EAX`. A korábbi „az elem a verem-argumentum” állítás téves volt.
- **38.2.52 §9 lista:** felülírva a 38.2.53 §9 által.

##### §8 Amit KIZÁRTAM

- „A `0x006a2a60` olvassa a T2-t”: ⚠️ JAVÍTVA (38.2.54 §2): igaz. A törzs a figyelő `+0xec` mezőjén át olvassa és írja a T2 adattömbjét, a korábbi „nem olvassa” kizárás téves.
- „A `0x00505030` külön T2-írást végez”: CÁFOLVA. A törzsben nincs `+0x58` vagy `+0x4c` hozzáférés, az írást a `0x004e5740` végzi (§1).
- „A T2-nek nincs indexelt adatolvasója”: CÁFOLVA. Két függvény olvassa indexszel (§3, (d)).
- „A kilenc metódus valamelyike fájltípus-kódot olvas indexszel”: CÁFOLVA, mintára. A kilenc függvényben az indexelt betöltés csak a `0x004f3510` láncolt-lista tömbjét érinti (§3).
- „A `+0x18` kód kép, album vagy személy”: NYITVA marad. A tábla és a két olvasó nem igazolja (§4).

##### §9 Nyitott lista (38.2.53 §9, felülírva: lásd 38.2.54 §9)

Új nyitott tétel nincs. Két tétel változott, a többi a 38.2.52 §9 szerint marad.

Nyitott kérdések mérlege (38.2.53): 54 tétel · 12 lezárva · 26 részben · 16 nincs meg. Az előző mérleg (38.2.52): 54 · 12 · 25 · 17. Változás: U53 NINCS MEG -> RÉSZBEN.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U49 | RÉSZBEN (38.2.53 §3-§4) | visszatérés és index LEZÁRVA; a `+0x18` a `T2[index]`-be kerül (`0x004e59fa`); a T2 olvasói megvannak (U53), a betöltött érték felhasználása NINCS MEG | `0x004e5740`, `0x00467ca0`, `0x0046d7d0` |
| U53 | RÉSZBEN (38.2.53 §2-§5) | a T2 olvasói: kilenc metódus a mutatót (főleg írással), két függvény indexszel az adatot; a betöltött érték felhasználása NINCS MEG; a `0x0053fe30` T2-ágának tábla-azonossága NINCS MEG; a figyelő (`[piVar2+0x54]`) osztálya NINCS MEG | `0x00467ca0` (`0x0046ba81`), `0x0046d7d0` (`0x0047054b`), `0x0053fe30`, `0x006a2a60` |

**A felhasználó szemével**

Ezen az úton még nem dől el, hogy a tétel kép, album vagy személy. Eldönthető, mert a két indexelt adatolvasó (`0x00467ca0`, `0x0046d7d0`) felhasználása lépésről lépésre követhető, de ehhez Ghidra-dekompilátum kell, ezért az irány nyitva marad.

#### 38.2.54 Az Időrend bináris feltárása, 37. kör: a T2 olvasói, a figyelő és a `+0x18` kód (#5401, 2026-10-22)

**Kérdés és hatókör.** A 38.2.53 §6 és §9 szerinti fő kérdés (U53): ki olvassa a `T2` táblát, és mit kezd az elem `+0x18` fájltípus-kódjával. A kör a 0x00467ca0, a 0x0046d7d0, a 0x004e41f0 és a 0x00499550 kérdéseit vizsgálta, és minden állítást a gépi kódból is ellenőrzött. Bemenet: `2026-10-22-idorend-37.txt` (a 0x0046d7d0, a 0x004e41f0 és a 0x00499550 dekompilátuma), a 38.2.53 §6 és §9 lista, és a bináris: diszasszemblálás (`pe_dis.cdis`, a második paraméter bájt, nem utasítás), az index `functions`, `rtti` és `data_symbols` táblája, és a `0x13320006` konstans mintás keresése a `.text`-ben. Új nyitott tétel nem került fel. Kódot nem módosítottunk, a CI-őrök nem futottak. Ideiglenes fájl nem készült.

**Válasz röviden.**
1. **Q1, a 0x00467ca0.** A két betöltött érték (`EBP`, `EDI`) két T2-elem, vagy az alapérték. A függvény csak nulla-tesztben használja őket (`0x0046bb36`-`0x0046bb3c`). Ha egyik sem nulla, a `0x0046bb42` ágra megy, ahol a `vt+0xd0` hívás az indexszel fut. Az értékük ezen az ágon nem jut tovább. A `[esp+0x70]` rekord egy zárolt szakasz őre, a `0x0041edb0` ennek a feloldója. LEZÁRVA a nulla-teszt szintjén.
2. **Q2, a 0x0046d7d0.** A `[esp+0x68]` és a `[esp+0x3c]` két T2-elem (vagy az alapérték). Ezeket a `0x009b93f0` kapja argumentumként: `ESI` a szélesség, `EDI` a magasság. A `[esp+0x68]` egy másik táblába is visszaíródik (`0x00470efd`). A hívóhelyek négyen vannak, három függvényben. RÉSZBEN: a felhasználás megvan, de a tábla azonossága a 0x004e5740 íróéval NINCS MEG.
3. **Q3, a konténer és a figyelő.** A 0x004e41f0 konténer osztálya `ytDirScanner` (a végleges vtábla `0x00c86be0`, az ősi `0x00c86c44` a `ytBaseThreadPausable`). A 0x00499550 figyelőjét a `0x006a41e0` gyár adja, típuskóddal `0x13320006`. A figyelő osztálya ⚠️ PONTOSÍTVA (38.2.55 §1): nincs saját vtáblája. A T2 a figyelő belsejében van (`+0xa4`, csak a `0x13320006` teremtőre igaz), ezért a `0x006a2a60` a T2 adattömbjét (`+0xec`) olvassa és írja. Ez JAVÍTÁS (§7).
4. **A fő kérdés (kép, album vagy személy).** NINCS MEG. A három olvasó egyike sem ad albumra vagy személyre utaló jelet. Két ellentmondás maradt: a 0x0046d7d0 a T2-értéket szélességként kezeli, a 0x006a2a60 ágán pedig a T2-értéket karakterláncként hasítja a `0x004936c0`. Mindkettő a `+0x18` fájltípus-olvasat ellen szól, ha az ágak lefutnak és a táblák azonosak. Ezt nem igazoltuk.

##### §1 Q1: a 0x00467ca0, az EBP és az EDI

Az asm sorrendje a két betöltés körül:

- **`0x0046ba66`-`0x0046ba86` (EBP).** `esi` a függvény `this`-jének `+0x1598` mezője (a dekompilátum `pbVar15 + 0x1598`), így `T2a = [esi+0x58]`. Ha a `T2a` nulla, vagy `[T2a+0x4c]>>1` nem nagyobb az `idx`-nél, `EBP = [esi+0x5c]` (`0x0046ba86`). Különben `EBP = [T2a+0x48][idx]` (`0x0046ba81`). Az `idx` a `[esp+0x7ebc]` slot.
- **`0x0046ba89`-`0x0046baa7` (őr).** `lea eax,[esp+0x70]` és `call 0x0041edb0` (`0x0046ba8d`): az előző őr feloldása. Utána `edi = [esp+0x1c]+0x15f8` (`0x0046ba96`), és az új őr: `[esp+0x70] = edi+0x28` (zár), `[esp+0x74] = edi` (tulajdonos) (`0x0046ba9f`-`0x0046baa3`). Végül `call [0xc40284]` (`0x0046baa7`).
- **`0x0046bae2`-`0x0046bafe` (EDI).** `T2b = [edi+0x58]` (`0x0046bae8`), vagyis `[this+0x1650]`. Ha nem nulla, és a darabszám nagyobb az indexnél, `EDI = [T2b+0x48][idx]` (`0x0046bafe`). Különben `EDI = [edi+0x5c]` (`0x0046bb03`).
- **`0x0046bb06`-`0x0046bb27`.** Az őr feloldása (`0x0041edb0`), majd `esi = idx`, `ebx = [esp+0x1c]`, és `call 0x0042c830` (eredmény: `al`).
- **`0x0046bb2c`-`0x0046bb3c` (a döntés).** `test al,al` és `jne 0x46bb42` (`0x0046bb2e`); `cmp [esp+0x27],al` és `jne 0x46bb42` (`0x0046bb34`); `test ebp,ebp` és `jne 0x46bb42` (`0x0046bb38`); `test edi,edi` és `je 0x46cccb` (`0x0046bb3c`). Az `EBP` és az `EDI` tehát csak nulla-tesztben szerepel.
- **A `0x0046bb42` ága.** A `vt+0xd0` hívás (`[ebx+0x48]` vtábla) az `idx`-szel és két kimeneti szóval (`[esp+0x260]`, `[esp+0x268]`). Az `EBP` és az `EDI` ezen nem argumentum. A dekompilátum szerint a következő `FUN_00506830` hívás is az `idx`-et kapja.

A függvény többi része nincs végigkövetve, ezért az „nem jut tovább” állítás a linéáris asm-ra szól.

##### §2 Q2: a 0x0046d7d0, a `[esp+0x68]` és a `[esp+0x3c]`

- **A két T2 tábla.** `X = [esp+0x14]+0x13b0` (`0x0047021e`, `lea edi,[ebx+0x13b0]`, a `ebx = [esp+0x14]` a `0x004701a0`-nál). Így `T2a = [X+0x58]` = `[[esp+0x14]+0x1408]`. `Y = [esp+0x14]+0x1410` (`0x00470280`, `add ebx,0x1410`), és `T2b = [Y+0x58]` = `[[esp+0x14]+0x1468]`. Az `[esp+0x14]` slot a törzsben többször átíródik (`0x0046dd63`, `0x0046e1f3`), ezért nem igazoltuk, hogy ez a hívó első argumentuma.
- **Az index.** `idx = *param_2`: a `[esp+0x2c]` a `param_2` mutatója (`0x004704b3`), a `mov esi,[esi]` pedig az értéket olvassa (`0x00470538`).
- **`V68` (`[esp+0x68]`).** `T2a[idx]`, ha `idx < [T2a+0x4c]>>1`; különben `[X+0x5c]` (`0x00470554`). Tárolás: `mov [esp+0x68],eax` (`0x0047054e`), illetve a másik ágon `0x00470557`.
- **`V3c` (`[esp+0x3c]`).** `T2b[idx]`, ha `idx < [T2b+0x4c]>>1`; különben `[Y+0x5c]` (`0x004705e5`). Tárolás: `mov [esp+0x3c],eax` (`0x004705df`), illetve `0x004705e8`.
- **Felhasználás 1: a `0x009b93f0` (szélesség és magasság).** `0x00470639`: `ebx = V68`. `0x0047064c`: `edi = V3c`. `0x00470650`: `esi = ebx`. `0x00470656`: `call 0x009b93f0`, `EAX = &[esp+0x74]` (négy szavas téglalap). A hívott függvény: ha a négy szó nulla, azonnal visszatér (`0x009b9406`). Egyébként a téglalap szavait a `w/65535` és a `h/65535` arányokkal szorozza (a 65535.0 a `0xcf3b78`-on áll), egész számmá alakítja, és `[0, w-1]`, illetve `[0, h-1]` közé szorítja. Ezért az `ESI` és az `EDI` a cél szélessége és magassága. A Ghidra-dekompilátum ezt nem mutatja (`FUN_009b93f0()`, üres argumentumlista).
- **Felhasználás 2: a `0x009b9290`.** `0x0047075c`-`0x0047076a`: `push V68`, `edx = V3c`, `eax = esi`, `call 0x009b9290`, majd `call 0x009b9150`. A `0x009b9290` elején ugyanazok a nulla-ellenőrzések vannak. A teljes törzset nem követtük.
- **Felhasználás 3: visszaírás más helyre.** A `0x00470ee3`-`0x00470efd` ágban: `eax = [esp+0x14]`, `ecx = [eax+0x1408]` (T2a objektum), `edx = [ecx+0x48]` (T2a adattömb), `ecx = V68` (`0x00470ef0`), `edi = [esp+0xc]` (`0x00470ef4`), és `[edx+edi*4] = ecx` (`0x00470efd`). A `0x00470f09`-`0x00470f1a` ágban a V68 a `[esi+0x48][edi]` helyre íródik, ha eltér (`0x00470f10`-`0x00470f1a`). Az index és a tábla itt nincs teljesen követve.
- **A `[esp+0x3c]` többi olvasása.** `0x00470674`, `0x004706a8`, `0x00471180`, `0x00471195`, és a `0x0046f296`-`0x0046f723` sor. Nincs végigkövetve.
- **Hívóhelyek (4 hely, 3 függvény).** `0x0053b961` és `0x0053bba7` a `FUN_0053b2e0`-ban (az első argumentum `[ebp+0x2bc]`, illetve `[ecx+0x2bc]`); `0x005f3e96` a `FUN_005f3e10`-ben (`[edi+0x2bc]`); `0x006abc48` a `FUN_006abae0`-ban (`[esi+0xc]`). A második argumentum mindegyiknél a hívó helyi rekordja (`lea`). A táblák tulajdonosát, vagyis az első argumentum objektumát nem azonosítottuk.

##### §3 Q3: a konténer, a figyelő és az ellentmondás

- **A konténer (`0x004e41f0`).** A `this` (`ebp`) vtábla-írásai: `[ebp] = 0xc86c44` (`0x004e420b`), majd `[ebp] = 0xc86be0` (`0x004e423e`); `[ebp+0x54] = 0xc86c14` (`0x004e4245`); `[ebp+0x58] = 0xc86c28` (`0x004e424c`). Az `rtti` táblában az `0xc86be0` = `ytDirScanner::vftable`, az `0xc86c44` = `ytBaseThreadPausable::vftable`, és az `0xc86c14`, `0xc86c28` szintén `ytDirScanner::vftable` (másodlagos vtábla). A `[ebp+0x480] = EBX = 0` (`0x004e4586`, az `EBX` nullázása `0x004e4204`). A konténer osztálya tehát `ytDirScanner`. LEZÁRVA.
- **A figyelő létrehozása (`0x00499550`).** `ESI` a tulajdonos objektum (a hívó a `0x00493d9f`, a `0x00493d40`-ben; az objektumát nem azonosítottuk). A `0x00499550` a `0x006a41e0` gyárat hívja: `(tulajdonos = [esi+0x50], méret = [esi+0x4c]+4 vagy 0, típus = 0x13320006, kimenet = &out, 1)` (`0x00499570`). Ha a visszatérés 0: `[esi+0x54] = out` (`0x0049957e`), és ha `out != 0`: `[esi+0x58] = out+0xa4` (`0x00499588`). A T2 mutató tehát a figyelő belsejébe mutat. Ez addig igaz, amíg más kód nem írja át a `[esi+0x58]` mezőt (ezt nem néztük végig).
- **A típus és az osztály.** A `0x13320006` konstans a `.text`-ben csak kétszer fordul elő: `0x00499569` (push, a gyári hívásban) és `0x006a2a71` (`cmp [esi+0x328]`). A `0x006a41e0` törzsében nincs `+0x328` írás, tehát a típus paraméteren át jut a létrehozott objektumba. ⚠️ PONTOSÍTVA (38.2.55 §1): a `+0x328` írója a `0x006d1740`. A figyelő osztálya: nincs saját vtáblája.
- **A figyelő kezelője (`0x006a2a60`).** Hívóhely: `0x004e5a09`, a `0x004e5740` belsejében (`ESI = [ebx+0x54]`, `EDI = idx`, a rekord `[ebx+0x50]+0x4c`). A törzs: (a) ha `EDI != -1`, és `[esi+0x328] == 0x13320006`, és `[esi+0xec][edi] != 0`, akkor `[esi+0xec][edi] = 0x004936c0(&[esi+0x5c], [esi+0xec][edi])` (`0x006a2a84`-`0x006a2a94`); (b) a `[esi+0x32c]` objektum vtábla-slot +8 hívása az `EDI`-vel (`0x006a2aa7`-`0x006a2aad`); (c) a rekord számlálójának növelése. A `[esi+0xec]` a T2 adattömbje, mert `T2.+0x48 = figyelő+0xa4+0x48 = figyelő+0xec`. ⚠️ Ez a 38.2.53 §2 javítása.
- **A `0x004936c0`.** Az első argumentum (`&[esi+0x5c]`) egy hash-tábla (bucket-tömb a `+0x20` mezőn). A második argumentumot (a T2 értékét) NUL-végű karakterláncként olvassa: bájtonként hash-t számol (kezdőérték `0x12345678`, `shl 5`, `shr 2`, összeadás), majd bucket-keresést végez. A visszatérési érték: ⚠️ PONTOSÍTVA (38.2.55 §2), a kulcshoz tartozó érték, nem index.
- **Az ellentmondás.** ⚠️ FELTÉTELESSÉ (38.2.55 §4): csak akkor áll, ha a T2 `char const*` tömb. A `0x004e5740` a `T2[idx]`-be az `elem+0x18` értéket írja (`0x004e57b7`-`0x004e57bd`: `ecx = [esi+0x18]`, `[esp+0x18] = ecx`; majd `0x004e59fa`). Közvetlenül utána hívja a `0x006a2a60`-at. Ha a figyelő típusa `0x13320006`, és az érték nem nulla, a `0x004936c0` ezt az értéket karakterláncként olvassa. Ha az érték 2 (a `.jpg` kód), a 2-es címről olvasna. Ez nem fér össze a 38.2.52 §2 fájltípus-olvasatával, hacsak az ág nem inaktív ezeknél az elemeknél, vagy a `+0x18` nem egész kód. Melyik igaz: NINCS MEG.

##### §4 Q4: a fő kérdés (kép, album vagy személy)

NINCS MEG. A három olvasó: (1) a 0x0046d7d0 a két értéket szélességként és magasságként kezeli; (2) a 0x00467ca0 nulla-tesztként; (3) a 0x006a2a60 karakterlánc-kulcsként (ha az ág fut). Egyik sem ad albumra vagy személyre utaló jelet. A 0x0046d7d0 táblájának azonossága a 0x004e5740 táblájával szintén nincs igazolva.

**A felhasználó szemével**

Ezt az irányt nem kell lezárni: a `0x006a41e0` gyár és a figyelő konstruktora (a `+0x328` mező írója) dönti el, hogy a `+0x18` érték eljut-e a `0x004936c0` karakterlánc-ágra, vagyis melyik olvasat igaz.

##### §5 Bizonyítottsági fok (38.2.54)

| állítás | bizonyíték | fok |
|---|---|---|
| a 0x00467ca0 EBP és EDI értéke csak nulla-teszt a `0x0046bb42` ágon | asm `0x0046bb2c`-`0x0046bb3c` | megerősített (linéáris asm; a függvény többi része nincs végigkövetve) |
| a `0x0041edb0` a `[esp+0x70]` őr feloldója | asm `0x0041edb0`-`0x0041edc2`, `0x0046ba8d`, `0x0046bb0a` | megerősített (a teljes törzs nincs végigolvasva) |
| a 0x0046d7d0 V68 és V3c értéke a `0x009b93f0` ESI és EDI argumentuma | asm `0x00470639`-`0x00470656`; `0x009b93f0` (`0x009b9406`, `0x009b9478`-`0x009b94df`, `0xcf3b78`) | megerősített |
| a `0x009b93f0` ESI és EDI: szélesség és magasság | asm: `lea ecx,[esi-1]`, `lea ecx,[edi-1]`, a 65535.0 osztás | erős (a képméret-olvasat nincs igazolva) |
| a 0x0046d7d0 T2 objektumai: `[X+0x58]`, `[Y+0x58]` | asm `0x0047021e`, `0x00470280`, `0x0047053c`, `0x004705c5` | megerősített; a `[esp+0x14]` forrása NINCS MEG |
| a 0x0046d7d0 négy hívóhelye és az első argumentum | asm `0x0053b961`, `0x0053bba7`, `0x005f3e96`, `0x006abc48` | megerősített |
| a konténer osztálya `ytDirScanner` | asm `0x004e420b`, `0x004e423e`, `0x004e4245`, `0x004e424c`; rtti-sorok | LEZÁRVA |
| a figyelő T2 mutatója a figyelő `+0xa4` mezője | asm `0x00499583`, `0x00499588` | megerősített (a tulajdonos identitása és a más írók nincsenek kimerítve) |
| a `0x006a2a60` olvassa és írja a T2 adattömbjét (`+0xec`) | asm `0x006a2a77`-`0x006a2a94` | megerősített |
| a figyelő osztálya | nincs adat | NINCS MEG. Ghidra-kör kell: `0x006a41e0` és a figyelő konstruktora |
| a `0x004936c0` a második argumentumot karakterláncként olvassa | asm `0x004936d1`-`0x004936fb` | megerősített (a visszatérés jelentése NINCS MEG) |
| a `+0x18` érték eljut-e a `0x004936c0`-ig | nincs igazolva: a figyelő `+0x328` típusának írója nincs megtalálva | NINCS MEG |
| a 0x0046d7d0 T2 tábla azonos-e a 0x004e5740 T2-jével | nincs igazolva (a mezőcímek eltérnek: `+0x1408`, `+0x1468`, illetve `[konténer+0x480]`) | NINCS MEG |

##### §6 Ghidra-címek a következő körhöz

- `0x006a41e0`: a gyár. Hogyan választ a típuskód (`0x13320006`) alapján, és hogyan jut a típus a létrehozott objektum `+0x328` mezőjébe. Ghidra-kör kell.
- A figyelő konstruktora: címe NINCS MEG; a `0x006a41e0` hívja, és a `+0x328` mezőt írja. ⚠️ PONTOSÍTVA (38.2.55 §1): a gyár nem hív konstruktort, a `+0x328` írója a `0x006d1740`.
- `0x004936c0`: a visszatérési érték és a második argumentum (karakterlánc) jelentése, és a hívóhelyei (a `0x006a2a84` és más). Ghidra-kör kell.
- `0x009b93f0`: a dekompilátum nem mutat regiszter-argumentumot. A szignatúrát kézzel kell megadni: `ESI = szélesség`, `EDI = magasság`, `EAX = téglalap*`. Ghidra-kör kell.
- `0x009b9290`: a `0x00470763` hívás célja. Ghidra-kör kell.
- `0x00493d40`: az `ESI` tulajdonos azonosítása (a `[esi+0x54]` és `[esi+0x58]` mezők objektuma). ⚠️ PONTOSÍTVA (38.2.55 §3): vtábla slot +0x18 metódus; a példány azonosítása NINCS MEG.
- `0x0046d7d0`: a `[esp+0x14]` slot forrása és a `[esp+0x3c]` további olvasói (`0x0046f296`, `0x00471180`, `0x00471195`). Asm-kör elég.
- `0x00467ca0`: a `0x0046bb42` ág utáni teljes függvényrész, ha a döntés-ág tartalma kell. Ghidra-kör kell, nem sürgős.

##### §7 Javítások a korábbi szakaszokban

- **38.2.53 §1, „Az `rtti` táblában ezekre a címekre nincs sor”:** ⚠️ JAVÍTVA (38.2.54 §3). Van sor: `0x00c86be0` = `ytDirScanner::vftable`, `0x00c86c44` = `ytBaseThreadPausable::vftable`. Az osztálynév LEZÁRVA.
- **38.2.53 §2 és §8, „a `0x006a2a60` nem olvassa a T2-t”:** ⚠️ JAVÍTVA (38.2.54 §2). A figyelő `+0xec` mezője a T2 adattömbje, mert `T2 = figyelő+0xa4` (`0x00499588`). A `0x006a2a60` olvassa és írja.
- **38.2.53 §3 (d), „két függvény indexszel olvassa”:** ⚠️ PONTOSÍTVA: a `0x006a2a60` is indexszel olvassa (`[esi+0xec][edi]`), a minta nem látta, mert ez a mező nem a T2 nevén van címezve.
- **38.2.53 §4, „a betöltött érték … nem szerepel”:** ⚠️ PONTOSÍTVA (38.2.54 §1, §2). A `0x00467ca0` értéke nulla-tesztben szerepel (`0x0046bb36`-`0x0046bb3c`). A `0x0046d7d0` értéke a `0x009b93f0` argumentuma.
- **38.2.53 §5 és §6, a `0x004e41f0` osztálynév:** ⚠️ JAVÍTVA: LEZÁRVA (`ytDirScanner`).
- **38.2.52 §2, a `2` fájltípus-olvasata:** ⚠️ KÉTSÉGES (38.2.54 §3). A `0x006a2a60` ága a T2 értéket karakterláncként hasítja. Ez ellentmond az olvasatnak, amíg az ág lefutását és a `+0x328` típus írását nem tisztáztuk.

##### §8 Amit KIZÁRTAM

- „A `0x00467ca0` EBP vagy EDI értéke tovább megy a `0x0046bb42` ágon”: CÁFOLVA az asm-ban: csak nulla-teszt.
- „A `0x0046d7d0` `[esp+0x68]` és `[esp+0x3c]` nem kerül tovább”: CÁFOLVA: a `0x009b93f0` és a `0x009b9290` argumentuma, és a `0x00470efd` visszaírás.
- „A `0x006a2a60` nem olvassa a T2-t”: CÁFOLVA (§3).
- „A `0x13320006` a `0x00499550` konstruktora”: KIZÁRVA: a `0x00499550` nem a figyelő konstruktora, a konstanst a gyárnak adja át.
- „A 0x0046d7d0 T2-ja azonos a 0x004e5740 T2-jével”: NEM IGAZOLT (és nem is kizárt): a mezőcímek eltérnek.

##### §9 Nyitott lista (38.2.54 §9, felülírva: lásd 38.2.55 §9)

Új nyitott tétel nincs. Két tétel szövege változott, az állapotuk nem. A többi tétel a 38.2.52 §9 szerint marad.

Nyitott kérdések mérlege (38.2.54): 54 tétel · 12 lezárva · 26 részben · 16 nincs meg. Az előző mérleg (38.2.53): 54 · 12 · 26 · 16. Változás: nincs állapotváltozás.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U49 | RÉSZBEN (38.2.54 §1-§3) | visszatérés és index LEZÁRVA; a `+0x18` a `T2[index]`-be kerül (`0x004e59fa`); a `0x00467ca0` nulla-tesztben, a `0x0046d7d0` méretként használja az értéket; hogy a `+0x18` eljut-e a `0x004936c0` ágig: NINCS MEG | `0x004e5740`, `0x00467ca0`, `0x0046d7d0`, `0x006a2a60` |
| U53 | RÉSZBEN (38.2.54 §1-§4) | a T2 olvasói: `0x0046d7d0` (méret), `0x00467ca0` (nulla-teszt), `0x006a2a60` (a figyelőn át, karakterlánc-ágon); a fő kérdés NINCS MEG; a figyelő osztálya NINCS MEG; a `0x0046d7d0` tábla azonossága NINCS MEG | `0x00467ca0`, `0x0046d7d0`, `0x0053fe30`, `0x006a2a60`, `0x006a41e0` |

#### 38.2.55 Az Időrend bináris feltárása, 38. kör: a típusos tömbök, a T2 és a fő kérdés (#5401, 2026-10-22)

**Kérdés és hatókör.** A 38.2.54 §6 és §9 szerinti kérdések: (1) a `0x006a41e0` gyár, (2) a `0x004936c0`, (3) a `0x00493d40` tulajdonosa, (4) a fő kérdés (U53): ki olvassa a `T2` táblát, és mit kezd a `+0x18` fájltípus-kóddal. Bemenet: `2026-10-22-idorend-38.txt` (a három függvény dekompilátuma), a 38.2.54 §6 és §9 lista, és a bináris: `pe_dis.cdis` (asm), az index `functions`, `rtti` és `data_symbols` táblája, valamint bájt-szintű pásztázás (E8 hívások, a `+0x328` mezőre írás, vtábla-címek). Kódot nem módosítottunk, a CI-őrök nem futottak (nincs kódváltozás). Ideiglenes fájl nem készült.

**Válasz röviden.**
1. **Q1, a gyár: a típus-ág LEZÁRVA, a konstruktor-hívás helye NINCS MEG.** A gyár nem választ konstruktort a típuskód alapján. A típust a `0x006d1740` írja a figyelő `+0x328` mezőjébe, és ugyanez a függvény ugrótáblával kiválasztja a típusnak megfelelő tömb helyét (§1). A típusos tömböket a `0x006d1050` építi a foglalás után (a törzse első felében hat vtábla-írás látszik). A `0x00493ce0` (`CColumn<char const*>`) konstruktornak egyetlen E8 hívója van, a `0x00412b19`, és az a `0x004127c0` függvényben van: ott egy `CPooledStringColumn` ágyazódik a `+0x8b8` mezőbe. Ez nem a gyár útja.
2. **Q2, a `0x004936c0`: a visszatérés és a karakterlánc-argumentum LEZÁRVA.** Szótár-keresés: a második argumentum NUL-végű karakterlánc (a kulcs), a visszatérés a kulcshoz tartozó érték, nem index. Új kulcsnál az érték a `0x00411150` visszatérése, ennek jelentése NINCS MEG. Hívóhelyek: `0x00437454` (`FUN_00437380`), `0x006a2a89` (`FUN_006a2a60`, a figyelő kezelője), `0x006d1d7b` (`FUN_006d1a80`), `0x006d350b` (`FUN_006d2180`).
3. **Q3, a `0x00493d40`: a tulajdonos a T2-t tartó objektum: IGEN.** A függvényt nincs E8 hívás: a `0x00c82424` (`CPooledStringColumn`) és a `0x00c8245c` (`CColumn<char const*,1,322043910>`) vtábla slot +0x18 mezője mutat rá (a `0x00c8243c` és a `0x00c82474` adat-hivatkozások). A `this` mezői: `+0x50` a zárolt tároló, `+0x54` a figyelő, `+0x58` a T2 (a függvény a T2-t is zárolja, `0x00493ddf`). Hogy melyik példányról van szó, NINCS MEG.
4. **A fő kérdés (U53): RÉSZBEN, az irány NEM zárható le.** Az eddigi olvasat („a `+0x18` fájltípus-kód, 2 = `.jpg`") csak akkor áll, ha az Időrend elemeinek T2 tömbje egész számokat tárol. Ha `char const*` tömb lenne, a `0x006a2a60` a 2-es értéket címként olvasná (§4). Az Időrend oszlopának típusa NINCS MEG.

##### §1 Q1: a gyár, a típus-ág és a tömbök

- **Új elem útja** (a név nincs a listában). `0x006a432c`: a `0x006a85c0` foglal 0x334 bájtot (`push 0x334`, `call 0x97c5d0`). A figyelő `+0x10` mezője `0x1331ffff` (alapérték), a `+0x32c` nulla, a `+0x0` egy bájt, nulla. Nincs vtábla-mező a figyelőn. A `0x006d1050` a `figyelő+0x14` címen építi a tömböket. `0x006a453d`: `0x006a6ff0(típus, figyelő)`, két stack-argumentum (`ret 8`). Beírja: `[figyelő+0x10] = típus`, `[figyelő+0x8] = 2`, a nevet a `0x00985ff0` másolja a `+0xc` mezőbe. `0x006a7074`: `eax = figyelő+0x14`, `ecx = típus`, `call 0x006d1740`.
- **Régi elem útja** (a név már a listában van). A `0x006a442e` hívás (`0x006d1740`) csak akkor fut, ha a figyelő `+0x10` vagy `+0x328` mezője nem egyezik a kért típussal. Utána `0x006a2a30` következik. A bemeneti regiszterek ezen a hívóhelyen nincsenek végigkövetve.
- **`0x006d1740`** (asm, 144 bájt): `mov [eax+0x314], ecx`, azaz a figyelő `+0x328` mezője = típus. Ezután, ha `típus - 0x13320000` legfeljebb 7, a ugrótábla (`0x006d17d0`, 8 bejegyzés) a figyelő `+0x324` mezőjébe a típusnak megfelelő tömb címét írja. A cél `figyelő+0x14+X`, és az `X` típusonként más (lásd a táblát).
- **A nyolc típus** (a ugrótábla, a teremtők és az rtti-nevek egyeztetve):

| típuskód | oszlop-osztály (rtti) | teremtő (a hívó slot +0x18 metódus) | T2 = figyelő+ | ugrótábla X |
|---|---|---|---|---|
| `0x13320000` | `CColumn<ytString,0,322043904>` | `0x00499590` (hívó `0x00494b2f`, `FUN_00494ad0`) | `+0xf4` | `+0xe0` |
| `0x13320001` | `CColumn<unsigned_long,1,322043905>` | `0x004995d0` (hívó `0x0049527f`, `FUN_00495220`) | `+0x194` | `+0x180` |
| `0x13320002` | `CColumn<double,1,322043906>` | `0x00499650` (hívó `0x00495def`, `FUN_00495d90`) | `+0x234` | `+0x220` |
| `0x13320003` | `CColumn<signed_char,1,322043907>` | `0x004996d0` (hívó `0x004960df`, `FUN_00496080`) | `+0x2d4` | `+0x2c0` |
| `0x13320004` | `CColumn<unsigned___int64,1,322043908>` | `0x00499610` (hívó `0x00495c3f`, `FUN_00495be0`) | `+0x284` | `+0x270` |
| `0x13320005` | `CColumn<unsigned_short,1,322043909>` | `0x00499710` (hívó `0x0049628f`, `FUN_00496230`) | `+0x144` | `+0x130` |
| `0x13320006` | `CColumn<char_const*,1,322043910>` | `0x00499550` (hívó `0x00493d9f`, `FUN_00493d40`) | `+0xa4` | `+0x90` |
| `0x13320007` | `CColumn<int,1,322043911>` | `0x00499690` (hívó `0x00495f7f`, `FUN_00495f20`) | `+0x1e4` | `+0x1d0` |

A táblában a `322043910` decimális szám egyezik a `0x13320006` típuskóddal (`0x13320000 + 6`). A teremtő eltolása (`add eax, T2`) minden sorban `0x14` plusz a ugrótábla `X` értéke.

- **A tömbök építése** (`0x006d1050`, a `0x006a85c0` hívja `figyelő+0x14`-re). `+0x14`: vtábla `0x00ca87f0` (`CGenericArray`). `+0x5c`: a `0x00493660` hívás építi (a törzse NINCS MEG); ez a tábla a `0x004936c0` szótára. `+0xa4`: vtábla `0x00ca8814` (`ytArray<char_const*,1,ytBaseThread>`), ez a T2 a `char const*` oszlopnál. `+0x144`: `0x00ca87cc`. `+0x194`: `0x00c81d90`. `+0x1e4`: `0x00ca8838`. Az utolsó három neve nincs ellenőrizve.
- **A figyelőnek nincs saját vtáblája.** A foglalás a `+0x0` mezőbe bájtot ír (`mov byte [esi], 0`), a vtáblák csak a tömbökön vannak. Ezért a „figyelő osztálya" NINCS MEG a vtábla-értelemben. A figyelő egy rekord, a típusos tömbök vtáblával rendelkeznek.
- **A zárolás.** A T2 zárolása (`0x00493d40`, `0x00493ddf`) ugyanazt a zár-mintát használja, mint a gyár: a tulajdonos szál (`+0x20`), az ismétlésszám (`+0x24`) és a kritikus szakasz (`+0x28`). A rtti-névben a `ytBaseThread` sablon-paraméter valószínűleg a zár típusa (ezt nem ellenőriztük végig).

##### §2 Q2: a `0x004936c0` szótára

- **Szerkezet** (`this` = a figyelő `+0x5c` mezője, egy IRowHash-alapú szótár; a rtti-ban a `0x00c7f620` vtábla az IRowHash-é). `+0x18`: értéktömb (32 bites). `+0x1c >> 1`: darabszám. `+0x20`: megfigyelő, ha nem nulla, a vtábla slot +8 hívás a darabszámmal, majd `0x009bbb70`. `+0x38`/`+0x3c` és `+0x40`/`+0x44`: két kulcs-tábla (`uint`, illetve `ushort` tömb).
- **Kulcs.** NUL-végű karakterlánc (`0x004936d1`-`0x004936fb`). Hash: kezdőérték `0x12345678`, bájtonként `uVar = uVar ^ (uVar*0x20 + (uVar>>2) + char)`.
- **Találat.** A kulcs-táblákban keresés. Egyezésnél `return` a `+0x18` tömb megfelelő eleme (`0x00493819`).
- **Nincs találat.** `0x00985ff0(kulcs)` (a jelentése NINCS MEG), majd `0x00411150(&tmp)` érték. Az érték a `+0x18` tömb végére kerül, a darabszám nő, és az értékkel tér vissza.
- **A T2 és a szótár kapcsolata** (`0x006a2a60`, `0x006a2a6b`-`0x006a2a94`): ha `[esi+0x328] == 0x13320006`, az érték nem nulla, akkor `[esi+0xec][edi] = 0x004936c0(&[esi+0x5c], [esi+0xec][edi])`. Vagyis a `char const*` oszlop T2 elemei karakterlánc-kulcsok, és a visszatérés a szótár-érték.

##### §3 Q3: a `0x00493d40` tulajdonosa

- **Hívás.** Nincs E8 hívóhely. A `0x00c82424` (`CPooledStringColumn`) és a `0x00c8245c` (`CColumn<char const*,1,322043910>`) vtábla slot +0x18 mezője (6. slot) mutatja. A nyolc slot +0x18 metódus azonos méretű (254 bájt). A `0x00494ad0`-ban látszik a `[this+0x54] == 0` ellenőrzés, a többit nem néztük végig; mindegyik a saját teremtőjét hívja (§1 táblázat).
- **A `this` mezői.** Ghidra szerint `__fastcall` (ECX). `+0x50`: a zárolt tároló (a gyár ebbe a tárolóba ír). `+0x54`: a figyelő. `+0x58`: a T2, a figyelő `+0xa4` (vagy a típusnak megfelelő) eltolásán.
- **Igen.** A `this` az a példány, amely a T2-t a `+0x58` mezőben tartja, és a függvény a T2-t is zárolja (`0x00493ddf`).
- **Nincs igazolva.** Melyik példány (melyik oszlop) a `this`. Az egyetlen beágyazás, amelyet láttunk, a `0x004127c0` függvényben van (`+0x8b8`, vtábla `0x00c82424`); hogy ez az Időrend oszlopa, NINCS MEG.

##### §4 Q4: a fő kérdés (U53) és az állapot a 36. kör óta

- **Állapotváltozás.** A 36. körben (38.2.53) volt utoljára változás: U53 NINCS MEG → RÉSZBEN. A 37. körben (38.2.54) nem volt változás. Ebben a körben lezárult a típus-tábla és a teremtők (§1), de a fő kérdés állapota nem változott: RÉSZBEN, nyitva.
- **Az ellentmondás pontosan.** A T2 elemei a típustól függően más jelentésűek. Ha a T2 `char const*` tömb (`0x13320006`), a `0x006a2a60` a `+0x18` értéket (a `.jpg` kódja 2) címként olvasná (`0x004936d1`). Ez összeomlást okozna. A valódi programon ezt nem mértük, ezért ez következtetés, nem mérés. Ha a T2 egész típusú (például `0x13320007` `int`, vagy `0x13320001` `unsigned long`), a `+0x18` egész kód marad, és a `0x006a2a60` ága nem fut le, mert a `+0x328` ellenőrzés hamis. Tehát a 38.2.52 §4 „fájltípus-kód" olvasata csak egész típusú T2 mellett áll.
- **A döntő cím.** Az Időrend oszlopa az `X = [konténer+0x480]` objektum. A konténer a `0x004e41f0` ytDirScanner, a `+0x480` mezőt a konstruktora nullázza. A `+0x480` íróit a 38.2.52 §3 (b) sorolja: `0x00466700`, `0x00612ae0`, `0x0067df90`, `0x0067e6a0`, `0x0068c880`, `0x0068eea0`. Ezek vtábla-írásai: `0x00466700` → `0x00c82e7c` (rtti: `ytDSMovieWriter`), `0x00612ae0` → `0x00c9be14` (rtti-név nincs), `0x0067df90` → `0x00ca6a4c` (rtti: `NewBkDialog`), `0x0068c880` → `0x00ca7d0c` (az rtti-név nem egyértelmű). A `0x0067e6a0` és a `0x0068eea0` törzsében nincs vtábla-írás. A névvel rendelkező vtáblák közül egyik sem oszlop-vtábla (a `0x00c9be14` neve nincs), ezért X oszlop-osztálya nem ebből az írásból adódik. Hogy X-et honnan kapja (építés vagy másolás), NINCS MEG.
- ⚠️ VISSZAVONVA (38.2.56 §1): ez a javasolt út nem indítható, mert a hat író egyike sem ír X-et.
- **Javasolt út az U53 helyett (eredeti, 38.2.55).** Az irányt nem kell lezárni, mert a döntő lépés még nincs megnézve. A fő kérdést a T2 olvasói helyett az X típusa dönti el. Lépések: (a) a hat író közül melyik adja X-et, és honnan kapja a mutatót; (b) X vtábla-címéből a slot +0x18 metódus, és a §1 táblázat szerint a típus. Ha a hat író egyike sem ad oszlop-vtáblát, akkor X más úton épül, és a következő lépés az X-et átadó hívóhely.

##### §5 Bizonyítottsági fok (38.2.55)

| állítás | bizonyíték | fok |
|---|---|---|
| a `0x006d1740` írja a figyelő `+0x328` mezőt a típussal | asm `0x006d1740` (`mov [eax+0x314], ecx`); hívóhelyek `0x006a7074`, `0x006a442e` | megerősített |
| a ugrótábla nyolc célja és a tömb-eltolások | asm: a `0x006d17d0` tábla nyolc bejegyzése, `0x006d1758`-`0x006d17c1` | megerősített |
| a nyolc teremtő eltolása (`+0xf4` … `+0x1e4`) és a típuskódok | asm `0x00499550`-`0x00499710` (`add eax, X`, `push` típuskód) | megerősített |
| a teremtő → slot +0x18 metódus → típus | E8 hívóhelyek (nyolc), a függvény-határok az indexből (254 bájt) | megerősített |
| a típusnevek (`CColumn<…,322043904…911>`) | rtti-nevek; `322043910` = `0x13320006` | megerősített |
| a figyelőnek nincs vtáblája | `0x006a85c0`: `mov byte [esi], 0`; `0x006a2e70`: bájt-másolás | megerősített (asm) |
| a `+0x14` és `+0xa4` vtábla-címei | asm `0x006d1050`; rtti: `0x00ca8814` = `ytArray<char_const*,1,ytBaseThread>` | megerősített (csak `0x00ca8814` van névvel) |
| `0x00ca87cc`, `0x00c81d90`, `0x00ca8838` neve | nincs ellenőrizve | NINCS MEG |
| a `0x004936c0` visszatérése a kulcs értéke | dekompilátum; asm `0x00493819` | megerősített |
| a `0x004936c0` kulcsa NUL-végű karakterlánc | asm `0x004936d1`-`0x004936fb` | megerősített |
| új kulcs értéke a `0x00411150` visszatérése | dekompilátum | megerősített (a `0x00411150` jelentése NINCS MEG) |
| a `0x00493d40` a slot +0x18 metódus (két vtábla) | rtti-sorok; `data_symbols` `0x00c8243c`, `0x00c82474` | megerősített |
| a `0x00493d40` példányának azonossága | nincs igazolva | NINCS MEG |
| a `+0x18` egész kódként olvasódik, ha a T2 nem `char const*` | `0x006a2a60`: `cmp [esi+0x328], 0x13320006` | FELTÉTELES (§4) |
| X oszlop típusa | nincs igazolva | NINCS MEG |

##### §6 Ghidra-címek a következő körhöz

- ⚠️ LEZÁRVA (38.2.56 §1): a `0x00466700`, `0x00612ae0`, `0x0067df90`, `0x0068c880`, `0x0067e6a0`, `0x0068eea0` nem ír X-et a konténerbe. Mind a saját `this`-ébe ír, Ghidra-kör nem kell.
- `0x00493660`: a `figyelő+0x5c` tábla építője. Ghidra-kör kell, nem sürgős.
- `0x006d1050`: a törzs második fele (a `+0x1e4` fölötti tömbök vtábla-címei, és a `0x00ca87cc`, `0x00c81d90`, `0x00ca8838` nevei). Asm-kör elég.
- `0x00411150`: az új kulcs értéke. Ghidra-kör kell.
- `0x00985ff0`: a kulcs másolása. Ghidra-kör kell (a `0x006a41e0`, a `0x004936c0` és a `0x006a6ff0` is hívja).
- `0x004127c0`: a `CPooledStringColumn` beágyazója (`+0x8b8`): ki hozza létre, és melyik tulajdonos. Ghidra-kör kell.
- `0x00493d40` példánya: a vtábla-hívás forrása (a `this`-t adó hívóhely). Ghidra-kör kell.
- `0x006a442e` (a `0x006d1740` hívás a régi-elem ágon): a bemeneti regiszterek. Asm-kör elég.

##### §7 Javítások a korábbi szakaszokban

- **38.2.52 §4, „a `+0x18` fájltípus-kód (2 = `.jpg`)":** ⚠️ FELTÉTELESSÉ VÁLT (38.2.55 §4): egész kódként csak egész típusú T2 mellett olvasható.
- **38.2.54 §3, „A figyelő osztálya NINCS MEG":** ⚠️ PONTOSÍTVA (38.2.55 §1): a figyelőnek nincs vtáblája, a tömbök vtáblával rendelkeznek. A T2 eltolása csak a `0x13320006` teremtőre `+0xa4`; típusonként más (§1 táblázat).
- **38.2.54 §3, „a visszatérési érték pontos jelentése NINCS MEG":** ⚠️ PONTOSÍTVA (38.2.55 §2): a kulcshoz tartozó érték, nem index.
- **38.2.54 §3, „az ellentmondás":** ⚠️ FELTÉTELESSÉ (38.2.55 §4): csak akkor áll, ha a T2 `char const*` tömb.
- **38.2.54 §6, a `0x006a41e0` és a figyelő konstruktora:** ⚠️ PONTOSÍTVA (38.2.55 §1): a gyár nem hív konstruktort, a `+0x328` írója a `0x006d1740`.
- **38.2.54 §6, a `0x00493d40` tulajdonosa:** ⚠️ PONTOSÍTVA (38.2.55 §3): vtábla slot +0x18 metódus; a példány azonosítása NINCS MEG.
- **38.2.55 §4, „Javasolt út az U53 helyett”:** ⚠️ VISSZAVONVA (38.2.56 §1): a hat író egyike sem ír X-et, az (a) és (b) lépés nem indítható.
- **38.2.55 §4, a „38.2.52 §3 (b)” hivatkozás:** ⚠️ JAVÍTVA (38.2.56 §7): a helyes forrás a 38.2.53 §3 (b).
- **38.2.55 §6, a hat író Ghidra-tétele:** ⚠️ LEZÁRVA (38.2.56 §1).
- **38.2.53 §3 (b), „13 írás”:** ⚠️ PONTOSÍTVA (38.2.56 §2): a dword-írás tíz a hét függvényben, a teljes `.text`-ben egy verem-írás is van. A 13-as szám nem egyezik egyik számlálási móddal sem. A betöltés-szám (16) egyezik.

##### §8 Amit KIZÁRTAM

- „A gyár törzse írja a `+0x328` mezőt": CÁFOLVA: a `0x006d1740` írja.
- „A T2 mindig a figyelő `+0xa4` mezője": CÁFOLVA: az eltolás típusonként más (§1).
- „A `0x00493ce0` konstruktor a gyárból hívódik": CÁFOLVA: egyetlen E8 hívója a `0x00412b19`.
- „A figyelő a `0x00493ce0` típusa": KIZÁRVA: a figyelőnek nincs vtáblája.
- „A `0x00493d40` `this`-je a figyelő": CÁFOLVA: a `this` a T2-t tartó oszlop, a figyelő a `+0x54` mezőben van.

##### §9 Nyitott lista (38.2.55 §9)

Új nyitott tétel nincs. Két tétel szövege változott, az állapotuk RÉSZBEN marad. A többi tétel a 38.2.52 §9 szerint marad (felülírva: 38.2.53 §9 és 38.2.54 §9).

Nyitott kérdések mérlege (38.2.55): 54 tétel · 12 lezárva · 26 részben · 16 nincs meg. Az előző mérleg (38.2.54): 54 · 12 · 26 · 16. Változás: nincs állapotváltozás.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U49 | RÉSZBEN (38.2.55 §1-§2) | visszatérés és index LEZÁRVA; a `+0x18` a `T2[index]`-be kerül (`0x004e59fa`); a `0x00467ca0` nulla-tesztben, a `0x0046d7d0` méretként használja az értéket; hogy a `+0x18` egész kód vagy karakterlánc, az X típusától függ (NINCS MEG) | `0x004e5740`, `0x00467ca0`, `0x0046d7d0`, `0x006a2a60` |
| U53 | RÉSZBEN (38.2.55 §1-§4) | a típusos tömbök eltolása LEZÁRVA (§1 táblázat); a T2 olvasói: `0x0046d7d0`, `0x00467ca0`, `0x006a2a60`; a fő kérdés NINCS MEG; X típusa NINCS MEG (hat író, §4) | `0x00466700`, `0x00612ae0`, `0x0067df90`, `0x0068c880`, `0x0067e6a0`, `0x0068eea0`, `0x00493d40` |

**A felhasználó szemével**

Ezen a körön nem derült ki, hogy az Időrend képeket, albumokat vagy személyeket mutat: a vizsgált olvasók közül egyik sem ad erre jelet.
Viszont az derült ki, hogy a `+0x18` érték jelentése attól függ, milyen típusú tömbbe kerül, és az Időrend tömbjének típusa még nincs megállapítva.
Az irányt NEM zárjuk le: a döntés az Időrend oszlopának típusán múlik (§4 és §6).

#### 38.2.56 Az Időrend bináris feltárása, 39. kör: a hat író, a konténer X-mezője és az Időrend-lánc (#5401, 2026-10-22)

**Kérdés és hatókör.** A 38.2.55 §4 és §6 szerinti kérdések (U53): (1) melyik író írja az X objektumot a `[konténer+0x480]` mezőbe, és honnan kapja a mutatót; (2) X vtábla-címe és a `+0x18` slot típusa; (3) ha egyik író sem ad oszlop-vtáblát, az X-et átadó hívóhely; (4) a fő kérdés állapota és a „felhasználó szemével”; (5) a nyitott lista és a Ghidra-címek frissítése. Bemenet: `2026-10-22-idorend-39.txt` (a hat író dekompilátuma és hívólistái), a 38.2.55 §4 és §6, és a bináris: `pe_dis.cdis` (asm), `paszta.utasitasok()` (a teljes `.text` pásztázása) és az index `functions` és `xrefs` táblái. Kódot nem módosítottunk, a CI-őrök nem futottak. A pásztázási kimenetek a munkamenet scratchpad-jében voltak (nem a `.bt/` alatt), a kör végén törölve.

**Válasz röviden.**
1. **Q1, melyik író írja X-et: NINCS MEG. A hat író egyike sem ír X-et a konténerbe.** Mind a hat a saját `this`-ébe ír: a négy konstruktor nullát, a `0x0067e6a0` egész téglalap-koordinátát, a `0x0068eea0` opció-értéket (§1). A konténer konstruktora (`0x004e41f0`) is nullát ír: az `EBX` a `0x004e4204`-ben nulla lesz, és a `0x004e4586`-os írásig nem változik (§3). Honnan kapja a mutatót: NINCS MEG.
2. **Q2, X vtábla és típus: NINCS MEG.** Nincs X-író, ezért nincs X vtábla, és nincs `+0x18` slot, amelyet a 38.2.55 §1 táblázatával össze lehetne vetni.
3. **Q3, az X-et átadó hívóhely: NINCS MEG.** A teljes `.text` `+0x480` címzései között nincs nem-nulla objektum-írás a konténer mezőjére (§2). Ez nem zárja ki a belső mutatón vagy másolással át történő írást, mert az index és a pásztázás ezeket nem látja.
4. **Fő kérdés (U53): RÉSZBEN marad, és a 38.2.55 §4 útja ZÁRVA.** Az U53 utolsó állapotváltozása a 36. körben volt (NINCS MEG → RÉSZBEN). A 36-39. kör óta a státusz nem változott, de az út igen: a 39. kör elvetette a 38.2.55 §4 útját. Az irányt nem kell lezárni, mert van egy mért lánc (§4): az Időrend belépőjétől a figyelő-kezelőig (`0x005e8d9d` → `0x006a2a60`). A döntő cím a `0x006a6647` hívóhely `this`-e, vagyis a figyelő. Ennek a `+0x328` típusmezőjét a `0x006d1740` írja (38.2.55 §1). Hogy melyik típus, NINCS MEG.

##### §1 Q1: a hat író törzse

| író | a `+0x480`-ba kerülő érték | a `this` | ítélet |
|---|---|---|---|
| `0x00466700` | `[edi+0x480] = ebx`, az `EBX` nulla (`xor ebx, ebx` a `0x00466710`-ben) | a `ytDSMovieWriter` konstruktor saját objektuma (`*edi = ytDSMovieWriter::vftable`) | nulla, saját objektum |
| `0x00612ae0` | `[ebp+0x480] = ebx`, az `EBX` nulla (`0x00612b1b`) | a `MakeMoviePanel` konstruktor saját objektuma | nulla, saját objektum |
| `0x0067df90` | `[ebp+0x480] = edi`, az `EDI` nulla (`xor edi, edi` a `0x0067dfcb`-ben) | a `CTextCaptionNode` konstruktor saját objektuma (`[ebp] = 0xca6c64`) | nulla, saját objektum |
| `0x0068c880` | `[ebp+0x480] = ebx`, az `EBX` nulla (`0x0068c888`) | a `PrepareCollection` konstruktor saját objektuma | nulla, saját objektum |
| `0x0067e6a0` | egész szám, négy írás: `0x0067e888`, `0x0067e8c8`, `0x0067e8f6`, `0x0067e92a` (az utolsó `add`) | virtuális metódus; a Ghidra-köteg szerint adat-hivatkozás a `0x00ca6c84`-re, ami a `0x00ca6c64` (`CTextCaptionNode`) vtábla +0x20 mezője | téglalap alsó széle, nem objektum-mutató |
| `0x0068eea0` | opció-érték: `[edx+0x480] = ecx` (`0x0068efe8`); a dekompilátum szerint az `option_manifest` nevű opció | virtuális metódus; adat-hivatkozás `0x00ca7c74` és `0x00ca7dac`; az osztálya NINCS MEG | opció-érték, nem objektum-mutató |

- A négy konstruktor a saját vtábla-mezőjét írja először (`[this] = vtábla`), tehát a `this` az épülő objektum. A konténer vtábla-mezője (`0xc86be0`, 38.2.54 §3) csak a `0x004e41f0`-ban íródik. Egyik konstruktor sem a konténerre ír.
- A két virtuális metódus a saját osztályának példányán dolgozik, és nem a konténeren. A `0x0067e6a0` a `CTextCaptionNode` vtábla slotja, a `0x0068eea0` vtábla-hivatkozásai más osztályt jeleznek.
- A 38.2.53 §3 (b) hét írója közül a dword-írás a hat íróban és a konténer konstruktorában van (§2). A hét függvényen kívül egyetlen dword-írás van, a `0x0069394c` verem-írás (`FUN_00692640`). Ez helyi változó, nem objektum mezője.

##### §2 A teljes `.text` pásztázása (`+0x480` címzés)

Módszer: `paszta.utasitasok(detail=False)` végigment a teljes `.text`-en (utasítás-szinten, darabolva). Szűrés: a memória-operandusban (`[...]`) szerepel a `0x480`. Találat: 115 utasítás. A szűrés ismételhető.

- **Dword-írás (`mov` vagy `add dword ptr [... + 0x480]`): 11 hely.** Tíz a hét függvényben (`0x00466aaf`, `0x004e4586`, `0x00612bc4`, `0x0067e01f`, `0x0067e888`, `0x0067e8c8`, `0x0067e8f6`, `0x0067e92a`, `0x0068ca3c`, `0x0068efe8`), és egy verem-írás (`0x0069394c`, `FUN_00692640`, `[esp+0x480]`).
- **Dword-betöltés, nem verem: 16 hely.** Tizennégy a 11 olvasó függvényben (`0x004e5210`, `0x004e5740`, `0x004e5a80`, `0x004eec80`, `0x004ef040`, `0x004f3510`, `0x004f46b0`, `0x004fcc50`, `0x00506790`, `0x00507590`, `0x0054f520`), kettő a `0x0067e6a0` téglalap-olvasása (`0x0067e8d1`, `0x0067e962`). A 38.2.53 §3 (b) 16-os betöltés-száma egyezik.
- **Qword-írás: 1 hely.** `0x005b8aa2`, a `FUN_005b8a70` konstruktorában, a saját `+0x480` mezőjére (nulla). A `0x005143dc` `fstp qword` a `+0x478`-ra ír, 8 bájtot, tehát nem fedi a `+0x480`-at.
- **Bájt-írás: 5 hely** (`0x0051480e`, `0x0051af6b`, `0x0051b09d`, `0x0051b173`, `0x0076e1b9`). **Szó-írás: 40 hely** (`0x008c1a52`-től `0x008cdf6a`-ig). Ezek más struktúrák mezői. A konténer `+0x480` mezője dword-mutató: a betöltött értéket objektumként használják (38.2.53 §3).
- **Címképzés `lea`: 3 hely.** `0x00693932` (`lea edi, [esp+0x480]`, verem-helyi objektum a `FUN_00692640`-ben), `0x00b81bd4` és `0x00b81e44` (`lea esi, [ebx+0x480]`). A `0x00b81bd4` függvény nincs a függvénytáblában; a törzs `mov byte ptr [esi+k], bl` írásokkal bájtos táblát tölt, nyolc, 16 bájtos sorral. Ez nem mutató-írás.
- **Címképzés `add`: 3 hely.** `0x00ad848d` (`FUN_00ad8400`), `0x00ade3d6` (`FUN_00ade290`), `0x00aebc42` (`FUN_00aebb30`). Mindegyik a 0x80 bájtos belső blokkok sorának folytatása: a sor `+0x180`-tól `+0x400`-ig tart egy másik objektumban. Az `FUN_00ade290`-ben az `eax` egy frissen lefoglalt, 0x500 bájtos blokk (a `call` eredménye), és a sor ebben van.
- **Következtetés.** A konténer konstruktora a `+0x47c`, `+0x478`, `+0x494`, `+0x498` és `+0x49c` mezőket is írja (`0x004e4580`, `0x004e44ec`, `0x004e4592`, `0x004e458c`, `0x004e4598`). A `+0x480` ezért nem lehet 0x80 bájtos belső blokk, és a három `add` nem a konténer címét adja.
- **Nem vizsgált formák.** A pásztázás nem látja a `rep movs`/`stos` típusú másolást, a vtábla-hívások mögött rejtett írást és a mutató változóba másolását. A „nincs más írás” állítás ezért a közvetlen `+0x480` címzésekre vonatkozik.

##### §3 A konténer-konstruktor és a létrehozója

- `0x004e41f0` (ytDirScanner, vtábla `0xc86be0`): `xor ebx, ebx` a `0x004e4204`-ben. Az `EBX` ezután a `0x004e4586`-os írásig nulla marad: a köztes hívások az `EBX`-et megőrzik, és más utasítás nem írja. Ezért a konstruktor végén `[ebp+0x480] = 0`, vagyis a konténer X-je létrehozáskor NULL.
- A konstruktornak az index szerint egyetlen hívója van: `0x00415790` (`FUN_00415790`, 7851 bájt). Ezt a hívóhelyet a diszasszemblálás nem ellenőrizte, csak az index `xrefs` táblája adja.
- A `0x00415790` hívói az index szerint: `0x00402f90`, `0x00467ca0`, `0x0053fe30`.
- Az X nem-nulla értékének forrása: NINCS MEG. Ghidra-kör kell: `0x00415790` - a konténer létrehozása, és van-e későbbi mutató-átadás a `+0x480` mezőnek (§6).

##### §4 Az Időrend-lánc: új, mért út a fő kérdéshez

A lánc a Nézet ▸ Időrend belépőjéből, a `0x005e8a70`-ből indul (`0x9ccc` azonosító, 38.2.8). A lépéseket asm-ben ellenőriztük:

| # | hívóhely | hívott | megjegyzés |
|---|---|---|---|
| 1 | `0x005e8d9d` a `0x005e8a70`-ben | `0x00566270` | az `EBX` a `0x005e8d9b`-ben EAX-ba kerül |
| 2 | `0x005662db` a `0x00566270`-ban | `0x0045ff60` | |
| 3 | `0x0045ffe9` a `0x0045ff60`-ban | `0x0069f710` | |
| 4 | `0x0069f7b9` a `0x0069f710`-ben | `0x006a63f0` | |
| 5 | `0x006a6647` a `0x006a63f0`-ban | `0x006a2a60` | a figyelő kezelője (38.2.53 §3): a `[esi+0x328]` típust és a `[esi+0xec]` tömböt olvassa |

Feltételek:
- A `0x005e8d9d` hívás a mód-1 ágon fut. A `0x005e8b06`-`0x005e8b0a` (`cmp byte ptr [ebp+0xc], 0` és `jne 0x005e8d5d`) a mód-1 esetet a `0x005e8d5d` blokkra viszi. Ott a `0x005e8d89`-es ellenőrzés után a hívás csak akkor következik, ha `[ebx+0x3094]` nem nulla (⚠️ PONTOSÍTVA, 38.2.57 §7: a `ja` előjel nélküli ugrás, nem „nagyobb nullánál”), vagy `[ebx+0x30a0]` nem nulla (`0x005e8d89`-`0x005e8d99`).
- Ez a két mező értéke az Időrend-hívás előtt NINCS MEG.
- ⚠️ JAVÍTVA (38.2.57 §7): nem második ág, hanem egyenes kód a `0x005662db` hívás után, feltétel nélkül. Itt: `0x005662eb` hívja a `0x005931c0`-t, az `0x0059321d` a `0x00595db0`-t, az `0x00595f3c` a `0x00425f60`-t. A `0x00425f60` a `0x004264d9` vagy `0x00426cac` helyen a `0x004ef040`-et, a `0x00426d33` helyen a `0x004eec80`-t hívja. Ez a két függvény T2-olvasó és -író (38.2.53 §3). A `0x00425f60` `this`-e NINCS MEG.
- A `0x005cb990` kapcsolóban a `0x005cd9e1` hívja a `0x0053a790`-t. Ez a `0x9ce4`-`0x9ceb` azonosítók blokkjában van, nem a `0x9ccc`-ében (`0x005cbbe0`). Az index szerint a `0x0053a790` hívja a `0x00467ca0` T2-olvasót. Ez tehát nem az Időrend-ág, és a `0x00467ca0` hívás csak az indexből ismert.
- Negatív állítás (például „az Időrend más T2-olvasót nem ér el”) NEM igazolt: az index a vtábla-hívásokat nem látja, és a keresés mélysége korlátos.

##### §5 Döntő cím: az irányt nem kell lezárni

A döntő lépés a figyelő-kezelő `this`-e. A `0x006a6647`-nél álló objektum a figyelő. Ennek a `+0x328` típusmezőjét a `0x006d1740` írja, a típust pedig a gyár-hívás adja (38.2.55 §1). A típustól függ, mit jelent a `+0x18` érték:
- ha a típus `0x13320006` (karakterlánc-oszlop), a `+0x18` érték kulcs a szótárban (38.2.55 §2);
- ha egész típus, a `+0x18` egész kód marad (38.2.55 §4).

⚠️ JAVÍTVA (38.2.57 §1): az Időrend figyelőjének típusa `0x13320000`, a `0x006a63f0` törzsében rögzített literálból (`push 0x13320000`, `0x006a6451`). A `0x0069f710` `this`-e nem adódik tovább (38.2.57 §2).

##### §6 Ghidra-címek a következő körhöz (felülírva: lásd 38.2.57 §6)

Új, a fő kérdéshez:
- `0x006a63f0`: a `this` a `0x006a6647` hívás előtt (a figyelő). Ghidra-kör kell, asm-szint is elég lehet. [blokkoló] ⚠️ LEZÁRVA (38.2.57 §1).
- `0x0069f710`: a `this` a `0x0069f7b9` hívás előtt. Ghidra-kör kell. [blokkoló] ⚠️ LEZÁRVA (38.2.57 §2).
- `0x005e8a70`: a `[ebx+0x3094]` és a `[ebx+0x30a0]` mezők írói (az Időrend-nézet állapota). Ghidra-kör kell. [blokkoló] ⚠️ LEZÁRVA a lista (38.2.57 §3); az értékek NINCS MEG.
- `0x00425f60`: a második ág `this`-e (a `0x00595db0` hívja). Ghidra-kör kell. [nem blokkolja a fő utat] ⚠️ JAVÍTVA (38.2.57 §4): a B ágon blokkoló.
- `0x00415790`: a `ytDirScanner` létrehozója; van-e eltolás nélküli mutató-átadás a `+0x480` mezőnek. Ghidra-kör kell. [nem blokkolja a fő utat]
- `0x00b81bd4`: a bájtos tábla-kitöltő függvény, nincs a függvénytáblában. Csak akkor kell, ha a `[ebx+0x480]` tábla az Időrendhez köthető. [nem blokkolja]

Lezárva (38.2.56 §1): `0x00466700`, `0x00612ae0`, `0x0067df90`, `0x0068c880`, `0x0067e6a0`, `0x0068eea0`. Nem X-írók, nincs Ghidra-kör.

Maradó (38.2.55 §6): `0x00493660`, `0x006d1050` (az asm-kör elég), `0x00411150`, `0x00985ff0`, `0x004127c0`, `0x00493d40` példánya, `0x006a442e` (az asm-kör elég).

##### §7 Javítások a korábbi szakaszokban

- **38.2.55 §4, „Javasolt út az U53 helyett”:** ⚠️ VISSZAVONVA (38.2.56 §1): a hat író egyike sem ír X-et, az (a) és (b) lépés nem indítható.
- **38.2.55 §4, a „38.2.52 §3 (b)” hivatkozás:** ⚠️ JAVÍTVA: a helyes forrás a 38.2.53 §3 (b).
- **38.2.55 §6, a hat író Ghidra-tétele:** ⚠️ LEZÁRVA (38.2.56 §1).
- **38.2.53 §3 (b), „13 írás”:** ⚠️ PONTOSÍTVA (38.2.56 §2): a dword-írás tíz a hét függvényben, a teljes `.text`-ben egy verem-írás is van. A 13-as szám nem egyezik egyik számlálási móddal sem. A betöltés-szám (16) egyezik.

##### §8 Amit KIZÁRTAM

- „A hat író egyike X-et ír a konténerbe”: CÁFOLVA (§1).
- „A konténer `+0x480`-át a konstruktor X-szel tölti”: CÁFOLVA (`EBX` nulla, §3).
- „A `0x00b81bd4` és a `0x00b81e44` címképzése X-re mutat”: CÁFOLVA (bájtos tábla, §2).
- „A három `add 0x480` a konténert érinti”: CÁFOLVA (belső blokkok, §2).
- „A `0x0053a790` → `0x00467ca0` lánc az Időrend-ág”: CÁFOLVA (`0x9ce4`-`0x9ceb` blokk, §4).
- „Az Időrend más T2-olvasót nem ér el”: NEM ZÁRHATÓ (nincs negatív bizonyíték, §4).

##### §9 Nyitott lista (38.2.56 §9, felülírva: lásd 38.2.57 §9)

Új nyitott tétel nincs. A U49 és a U53 szövege változott, állapotuk RÉSZBEN marad.

Nyitott kérdések mérlege (38.2.56): 54 tétel · 12 lezárva · 26 részben · 16 nincs meg. Az előző mérleg (38.2.55) ugyanez. Változás a számokban: nincs. Változás a tartalomban: a 38.2.55 §4 útja negatív lett, az Időrend-lánc új bizonyíték.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U49 | RÉSZBEN (változatlan) | a `+0x18` a `T2[index]`-be kerül (`0x004e59fa`), de a `0x004e5740` csak nem-nulla X mellett ír; az X forrása NINCS MEG (§3) | `0x004e5740`, `0x00467ca0`, `0x0046d7d0`, `0x006a2a60` |
| U53 | RÉSZBEN (változatlan) | a hat-író út ZÁRVA (§1); mért lánc az Időrend-belépőtől a figyelő-kezelőig (§4); döntő cím: a `0x006a6647` `this`-e (§5) | `0x005e8d9d`, `0x00566270`, `0x0045ff60`, `0x0069f710`, `0x006a63f0`, `0x006a6647`, `0x006a2a60` |

**A felhasználó szemével**

Ebben a körben sem derült ki, hogy az Időrend képeket, albumokat vagy személyeket mutat. Azt viszont megmértük, hogy a menüből induló lánc a figyelő kezelőjéhez fut, és ott dől el, mit jelent az elem fájltípus-kódja. Ezért az irányt nem zárjuk le: a következő lépés az, hogy kiderüljön, melyik figyelő kapja az Időrendnél a saját típusát.

#### 38.2.57 Az Időrend bináris feltárása, 40. kör: a figyelő típusa, a két `this` és az X-írók (#5401, 2026-10-22)

**Kérdés és hatókör.** A 38.2.56 §6 három blokkoló címe és a fő kérdés (U53): (1) a `0x006a63f0` `this`-e a `0x006a6647` hívás előtt, és milyen típust kap a figyelő az Időrendnél; (2) a `0x0069f710` `this`-e a `0x0069f7b9` hívás előtt; (3) a `[X+0x3094]` és a `[X+0x30a0]` mezők írói, ahol X a `0x005e8a70` `this`-e; (4) a fő kérdés állapota. Bemenet: `2026-10-22-idorend-40.txt` (a három dekompilátum és hívólistájuk), a 38.2.56 §4-§6, és a bináris: `pe_dis.cdis` (asm), a teljes `.text` mintás pásztázása (`paszta.utasitasok`, a `+ 0x3094]` és a `+ 0x30a0]` memória-operandusra szűrve), és az index `functions` és `xrefs` táblája. Kódot nem módosítottunk, a CI-őrök nem futottak (nincs kódváltozás). Ideiglenes fájl nem keletkezett.

**Válasz röviden.**

1. **Q1, a `0x006a63f0` `this`-e a `0x006a6647` előtt: a figyelő (ESI), típusa `0x13320000`.** A `this` (`P+0xf20`) a tároló. A figyelő ettől külön objektum: a `0x006a41e0` gyár keresi vagy létrehozza, kulcsa a `redo` nevű karakterlánc. A gyár hívásában a típus literál: `push 0x13320000` (`0x006a6451`). Az Időrend-ág figyelője tehát `CColumn<ytString,0,322043904>` típusú, nem `0x13320006` (`char const*`). A `0x006a2a60` `[esi+0x328] == 0x13320006` ellenőrzése (`0x006a2a6b`) hamis, a szótár-ág (`0x004936c0`) nem fut.
2. **Q2, a `0x0069f710` `this`-e a `0x0069f7b9` előtt: nem adódik tovább.** A `this` belépéskor EAX-ben van, a törzs ESI-be menti (`0x0069f71c`). Ez a zárolt `M+0x2fd4` objektum. A `0x0069f7b9` hívás nem kap regiszter-`this`-t: az első verem-argumentum `[M+0x31f8]+0xf20`, vagyis a `0x006a63f0` `this`-e `P+0xf20`, ahol `P = [M+0x31f8]` és `M = [X+0x2bc]`.
3. **Q3, `[X+0x3094]` és `[X+0x30a0]` írói: öt függvény, tizenkét írás.** `+0x3094`: nyolc írás (`0x005643e0`, `0x005931c0`, `0x00593880`, `0x00594170`). `+0x30a0`: négy írás (`0x005643e0`, `0x00593450`, `0x00593880`, `0x00594170`). Az értékek jelentése NINCS MEG. Az írók közül csak a `0x005931c0` fut a `0x005e8a70` láncában (`0x005662eb`), és az X-et kapja `this`-ként.
4. **Fő kérdés (U53): RÉSZBEN marad, de az A ágon a fájltípus-kód nem jut el.** A 36-39. kör óta ez az első állapotváltozás. Az Időrend-láncnak két ága van. Az A ág (`0x00566270` → `0x0045ff60` → `0x0069f710` → `0x006a63f0`) az `M` objektumot (`[X+0x2bc]`) használja, és a `redo` nevű ytString oszlop egy sorába ír szöveget. A saját törzseiben nincs elem-`+0x18` olvasás. Az A ág T2-olvasója a `0x006a63f0` (a sor összehasonlítása). A B ág (`0x005931c0` → `0x00595db0` → `0x00425f60`) hívása ugyanezt a mezőt olvassa, ha az `ebp` X. A B ág T2-olvasóit még nem néztük meg.
5. **Az irányt nem kell lezárni.** A B ágon a `0x00425f60` és a `0x00595db0` `this`-e dönti el, hogy olvas-e T2-t, és melyiket.

##### §1 Q1: a figyelő, a típus és a sor

Belépés: `stdcall`, `ret 0x10`. Verem-argumentumok: `[ebp+8]` a `this` (`P+0xf20`), `[ebp+0xc]` a kulcs (`0xc814b4`), `[ebp+0x10]` a sor (`param_3`), `[ebp+0x14]` a szöveg.

- **A gyár hívása** (`0x006a6447`-`0x006a645c`): verem: `push 1` (létrehozás), a `local_14` címe, `push 0x13320000`, a kulcs, a `this`. A `0x006a41e0` `ret 0x14`-gyel veszi vissza az öt argumentumot.
- **A figyelő**: a `local_14` a `[esp+0x14]`-ben van. Betöltése a `0x006a64bd`-ban, újratöltése a `0x006a663f`-ben (`mov esi,[esp+0x14]`). A verem egyensúlya igazolt: a `0x006a70e0` `ret 8`, a `0x006a2a60` `ret 4`, a `0x00985ff0` `ret 4`, a `0x006a41e0` `ret 0x14`. Ezért az ESI a `0x006a6647` előtt is a figyelő.
- **A T2** a figyelő `+0xf4` mezője (`0x006a652d`: `add esi,0xf4`). Ez egyezik a 38.2.55 §1 táblájával: a `0x13320000` teremtője (`0x00499590`) a T2-t `+0xf4`-re teszi. Az adat a `[T2+0x48]` (`0x006a6578`), az elem a `[adat + sor*4]`.
- **A hívás** (`0x006a6647`): `this` = ESI = a figyelő; EDI = `[ebp+0x10]` = a sor (`0x006a663c`); verem-argumentum a `this+0x4c` (`lea ecx,[ebx+0x4c]`, `0x006a6643`), vagyis a `P+0xf6c` rekord.
- **A típus** `0x13320000`. A `0x006a2a60` a `0x13320006` ágat (`0x006a2a6b`-`0x006a2a94`) kihagyja, a `0x004936c0` szótár nem fut, és a `+0x18` nem kerül kulcsként a szótárba. A `0x006a2a60` csak a `[esi+0x32c]` megfigyelőt értesíti (`vt+8`, majd `0x009bbb70`).
- **A kulcs**: a `0xc814b4` NUL-végű karakterlánca `redo` (a bináris olvasata). A jelentése NINCS MEG. A gyár a nevet a figyelő `+0xc` mezőjébe másolja (38.2.55 §1).
- **Minden hívó**: a `0x13320000` literál a törzsben van, ezért a `0x006a63f0` minden hívója ezt a típust kapja. Az index szerint 15 hívó van, a Ghidra-dumpban 19. A kulcs és a sor hívónként más lehet; ezt nem néztük végig.
- **Az írás**: ha a sor szövege eltér, a `0x00985ff0` másolja a szöveget, a `0x005c2100` szöveg-értékadást végez (38.2.51 §5), majd a `0x006a2a60` jelez. Ha egyezik, nincs írás és nincs jelzés (`0x006a6650`).

##### §2 Q2: a `0x0069f710` `this`-e

- **Belépés**: a `this` EAX-ben érkezik, és `mov esi,eax` menti (`0x0069f71c`). A hívó `0x0045ff60` a `0x0045ffe7`-ben `mov eax,edi`-vel adja, ahol `edi = M+0x2fd4` (a `0x0045ffc7` `lea`-ja).
- **Verem-argumentumok** (a `0x0045ffd4`-`0x0045ffe6` blokkban): A1 = `M+0x31f4` (`lea edx,[ebp+0x31f4]`), A2 = `[M+0x32c8]` (a sor), A3 = `0xc814b4` (a kulcs).
- **A hívás előtt** (`0x0069f7a9`-`0x0069f7b9`): `ecx` a szöveg (negyedik argumentum), `ebx` = A2, `ebp` = A3, `eax = [A1+4]+0xf20`. Az `eax` lesz az első argumentum, vagyis a `0x006a63f0` `this`-e.
- **Következtetés**: az ESI (`M+0x2fd4`) a `0x0069f710` saját zárolásának objektuma, és a `0x009079b0` (szöveg-kiolvasás) verem-argumentumként kapja (`push esi`, `0x0069f777`). A `0x006a63f0` ezt nem kapja. A Ghidra-dekompilátum `in_EAX`-ként mutatja a `this`-t, ez a belépési állapot helyes.

##### §3 Q3: a `[X+0x3094]` és a `[X+0x30a0]` írói

**Módszer.** `paszta.utasitasok(detail=False)` a teljes `.text`-en, 2884879 utasítás. Találat: `+0x3094` 127, `+0x30a0` 44. Írásnak számít, ha a memória-operandus az első operandus, és az utasítás neve nem `cmp`, `test`, `push`, `call`, `jmp`, `lea` vagy `bt`. Ebből írás: `+0x3094` nyolc, `+0x30a0` négy.

| író | mező (bázisregiszter) | írt érték | címek | hívó |
|---|---|---|---|---|
| `0x005643e0` (konstruktor) | `+0x3094` (ebp), `+0x30a0` (ebp) | `ebx` | `0x00564c92`, `0x00564c98` | index: `0x004039f0` |
| `0x005931c0` | `+0x3094` (ebx = X) | nulla | `0x00593352`, `0x0059341d` | asm: `0x00566270` (`0x005662eb`) |
| `0x00593450` | `+0x30a0` (ebp) | `eax` | `0x005934b9` | index: `0x00593880` |
| `0x00593880` | `+0x3094` (ebx 3×, ebp 1×), `+0x30a0` (ebx 1×) | `ebp` (négy esetből három, és a `+0x30a0`), `eax` (`0x00593fc9`) | `0x00593cf7`, `0x00593d03`, `0x00593d1d`, `0x00593fc9`, `0x00593d5c` | index: `0x00566a70` |
| `0x00594170` | `+0x3094` (ebx), `+0x30a0` (ebx) | nulla | `0x005941c8`, `0x005941ac` | index: `0x00576a20` |

- **X azonossága.** A `0x005e8a70` `this`-e (X) `[X+0x3094]` és `[X+0x30a0]` mezőit a `0x005e8d89`-`0x005e8d99` ellenőrzi, és a `0x00566270` hívás csak nem nulla értéknél történik. Ez a két mező kapuja az Időrend-láncnak.
- **A `0x005931c0` X-et kap**: `push esi` a `0x005662e0`-ban, a `this` a `[ebp+8]` (`0x005931f3`), tehát X. A `[X+0x3094]` nem nulla esetén a `0x005931c0` hívja a `0x00595db0`-t, X-szel (`0x0059320f`-`0x0059321d`). A nullázó írások (`0x00593352`, `0x0059341d`) a `0x00592f30` hívás után vannak; ez a régi értéket kapja (`push ecx`, `0x0059333b`). Az elágazást nem követtük végig.
- **Az egyéb írók `this`-e NINCS MEG.** Hívóikat az index adja, asm-ben nem ellenőriztük.
- **A `0x005643e0` konstruktor** a `0x004039f0`-ból hívódik, és egy 0x3710 bájtos objektumot épít (a spec korábbi szakasza). Hogy ez az objektum X-e, NINCS MEG: a `0x004039f0` `this`-e kell.
- **Korlát**: a mintás pásztázás nem látja a `rep movs`/`stos` típusú másolást, a vtábla mögötti írást és a mutató-másolást. A „nincs más író” állítás csak a közvetlen `+0x3094`/`+0x30a0` címzésre áll.

##### §4 Fő kérdés (U53): az A és a B ág

**Állapot.** A 36-39. körben nem volt változás. Most az A ágon a figyelő típusa rögzített, és a fájltípus-kód ezen az ágon nem jut el a szótárba.

- **A ág** (`0x005e8d9d` → `0x00566270` → `0x005662db` → `0x0045ff60` → `0x0069f710` → `0x006a63f0` → `0x006a2a60`):
  - figyelő: `0x13320000` (ytString), kulcs `redo`, T2 = a figyelő `+0xf4` mezője;
  - T2 olvasója: a `0x006a63f0` (a sor elemét betölti és összehasonlítja, `0x006a6578`-`0x006a6581`); írója a `0x005c2100` (38.2.51 §5);
  - elem `+0x18`: a négy saját törzsben (`0x0045ff60`, `0x0069f710`, `0x006a63f0`, `0x006a2a60`) nincs olvasás. A `[..+0x18]` találatok verem-helyi (`[esp+0x18]`) vagy vtábla-slot (`[edx+0x18]`) címek;
  - a hívott törzsek (`0x00454770`, `0x009079b0`, `0x00906cf0`, `0x006a41e0`, `0x006a70e0`): mintás átnézés szerint ugyanez a kép, kivéve egy `lea eax,[ebx+0x18]`-t (`0x006a442b`, a `0x006a41e0` gyárban), amelynek sorsa NINCS MEG. A `0x006a70e0` (3871 bájt) törzse nincs végigolvasva;
  - ⇒ **ZÁRVA** a fájltípus-kódra a saját törzsek alapján; a hívott törzsekre korlát van (§6).
- **B ág** (`0x005662eb` → `0x005931c0` → `0x00595db0` → `0x00425f60` → `0x004eec80` vagy `0x004ef040`):
  - a `0x005931c0` a `[X+0x3094] != 0` esetén hívja a `0x00595db0`-t X-szel;
  - a `0x00595db0` a `0x00595f3c`-ben hívja a `0x00425f60`-t; az argumentumai `[ebp+0x2bc]` (M, ha az `ebp` X) és `[ebp+0x309c]`;
  - a `0x00425f60` index-hívói: `0x00595db0`, `0x00467ca0`, `0x0046d7d0` (az utóbbi kettő T2-olvasó, 38.2.53 §3);
  - a `0x004eec80` és a `0x004ef040` T2-betöltők (38.2.53 §3 (b)); az index szerint mindkettőt a `0x00425f60` hívja. ⚠️ JAVÍTVA (38.2.59 §7): ez tévedés, a `0x004eec80`-nak három hívója van (`0x00425cc0`, `0x00425f60`, `0x00505030`). ⚠️ PONTOSÍTVA (38.2.58 §4, §7): a `0x004eec80` T2-t ír (`T2[idx] = 4`) és a `+0x18`-at osztályozza; a `0x004ef040` a `+0x18`-at írja. A hívási helyek: `0x00426d33`, illetve `0x004264d9` és `0x00426cac`.
  - NINCS MEG: a `0x00425f60` és a `0x00595db0` `this`-e, és hogy a B ág melyik T2-t olvassa. ⚠️ FRISSÍTVE (38.2.58 §2, §4): a `0x00595db0` `this`-e X (egy argumentum), a B ág T2-olvasója a `0x004eec80`; a hívás feltételei NINCS MEG.

**Döntés.** Az irányt nem kell lezárni. A B ágon a `0x00425f60` és a `0x00595db0` `this`-e dönti el, hogy a fájltípus-kód olvasódik-e ott. A 38.2.56 §6 `0x00425f60` tétele (nem blokkoló) ezzel blokkoló lett.

##### §5 Bizonyítottsági fok (38.2.57)

| állítás | bizonyíték | fok |
|---|---|---|
| a `0x006a6647` hívás ESI-je a figyelő | asm `0x006a663f`, `0x006a64bd`; verem-egyensúly: `0x006a41e0` `ret 0x14`, `0x006a70e0` `ret 8`, `0x00985ff0` `ret 4`, `0x006a2a60` `ret 4` | megerősített |
| a figyelő típusa `0x13320000` | asm `0x006a6451` (`push 0x13320000`), `0x006a645c` (a gyár hívása); egyezik a 38.2.55 §1 táblával (`+0xf4`, teremtő `0x00499590`) | megerősített |
| a T2 a figyelő `+0xf4` mezője | asm `0x006a652d` (`add esi,0xf4`) | megerősített |
| a sor az EDI, a rekord a `this+0x4c` | asm `0x006a663c`, `0x006a6643`-`0x006a6647` | megerősített |
| a `0x006a2a60` a `0x13320006` ágat nem futtatja | asm `0x006a2a6b`-`0x006a2a75` | megerősített |
| a kulcs `redo` | asm `0x0045ffda` (`push 0xc814b4`); a bináris olvasata: `redo`, NUL-végű | megerősített (jelentése NINCS MEG) |
| `M = [X+0x2bc]` | asm `0x005662d4`-`0x005662da` | megerősített |
| a `0x0069f710` regiszter-`this`-e nem adódik tovább | asm `0x0069f71c`, `0x0069f7a9`-`0x0069f7b9` | megerősített |
| a `0x006a63f0` `this`-e `P+0xf20` | asm `0x0069f7ad`-`0x0069f7b2`; `0x0045ffe0` (`lea edx,[ebp+0x31f4]`) | megerősített (a `P` osztálya NINCS MEG) |
| a `0x006a63f0` minden hívója `0x13320000` | literál a törzsben; index 15 hívó, Ghidra 19 | megerősített |
| a `+0x3094`/`+0x30a0` írói: öt függvény, 12 írás | teljes `.text` mintás pásztázás, közvetlen címzés | megerősített; `rep movs`, vtábla mögötti és mutató-másolás nem látszik |
| a `0x005931c0` `this`-e X | asm `0x005931f3`, `0x005662e0` | megerősített |
| a `0x005931c0` `[X+0x3094] != 0` esetén hívja a `0x00595db0`-t | asm `0x0059320f`-`0x0059321d` | megerősített |
| a többi író hívói (`0x00566a70`, `0x00576a20`, `0x004039f0`) | index `xrefs` | csak index (hiányos lehet) |
| X azonossága a `0x005643e0` objektummal | nincs igazolva | NINCS MEG |
| a `0x006a442b` `lea`-jának sorsa | nincs végigolvasva | NINCS MEG |
| az A ág elem-`+0x18`-mentes | saját törzsek asm-ben; hívott törzsek mintásan | részben (korlátos) |
| a B ág T2-olvasói | a `0x00425f60` és a `0x00595db0` nincs elolvasva | NINCS MEG |

##### §6 Ghidra-címek a következő körhöz

**Lezárva ebben a körben:** `0x006a63f0` (this, típus, sor; §1), `0x0069f710` (this; §2), `0x005e8a70` (írólista; §3, az értékek NINCS MEG).

**Új vagy pontosított, a B ághoz:**
- `0x00425f60`: `this` és a hat argumentum. [blokkoló, B ág] ⚠️ PONTOSÍTVA (38.2.58 §1): hat verem-argumentum, nincs ECX-es `this`.
- `0x00595db0`: a `this` (X) és a T2-olvasás a `0x00425f60` előtt. [blokkoló, B ág]
- `0x004eec80`, `0x004ef040`: melyik T2 (`X+0x480` vagy más). [a B ág végén kell]

**Az A ág zárásához:**
- `0x00454770`: a `0x006a63f0` előtti hívás (`P`, sor, kulcs, szöveg); a törzse nincs végigolvasva.
- `0x006a41e0`: a `0x006a442b` `lea eax,[ebx+0x18]` címének sorsa.
- `0x006a70e0` (3871 bájt): a törzse nincs végigolvasva; a `0x006a64c6`-ban hívódik. ⚠️ LEZÁRVA (38.2.58 §3).

**Nem blokkolja:**
- `0x004039f0`: a 0x3710 bájtos objektum `this`-e (X azonossága).
- `0x00593880`, `0x00594170`: a `this` és a hívók (`0x00566a70`, `0x00576a20`).
- `0x009079b0`: a kiírt szöveg forrása (`M+0x2fd4`).
- `0x00592f30`: a régi `+0x3094` értéket kapja.

**Maradó, változatlan (38.2.56 §6):** `0x00415790`, `0x00b81bd4`, `0x00493660`, `0x006d1050`, `0x00411150`, `0x00985ff0`, `0x004127c0`, `0x00493d40` példánya, `0x006a442e`.

##### §7 Javítások a korábbi szakaszokban

- **38.2.56 §4, „Második ág ugyanabból a `0x00566270`-ból"**: ⚠️ JAVÍTVA. Nem második ág: a `0x005662db` és a `0x005662eb` hívás között nincs elágazás. A `0x005931c0` hívása feltétel nélküli, a `0x00595db0` hívása a `0x005931c0`-ben feltételes (`[X+0x3094] != 0`).
- **38.2.56 §4, a `0x005e8d89` feltétele**: ⚠️ PONTOSÍTVA. A `0x005e8d90` `ja` ugrás előjel nélküli, a feltétel tehát „nem nulla”, nem „nagyobb nullánál”.
- **38.2.56 §5, a figyelő típusa**: ⚠️ JAVÍTVA (38.2.57 §1). A típus `0x13320000`, a `0x006a63f0` törzsében rögzített literál.
- **38.2.56 §6, `0x0069f710`**: ⚠️ LEZÁRVA (38.2.57 §2). A `this` belépéskor EAX (`in_EAX`), a törzs ESI-be menti, és a `0x009079b0` verem-argumentumként kapja.
- **38.2.56 §6, `0x00425f60`**: ⚠️ JAVÍTVA (38.2.57 §4). Blokkoló, a B ág miatt.

##### §8 Amit KIZÁRTAM

- „A figyelő típusa `0x13320006` az Időrend-ágon": CÁFOLVA (`push 0x13320000`, `0x006a6451`).
- „A `0x0069f710` `this`-e a `0x006a63f0` `this`-e": CÁFOLVA (verem-argumentum, §2).
- „A `0x005662eb` a `0x005931c0`-t második ágon hívja": CÁFOLVA (§7).
- „A `+0x3094` egyetlen írója a `0x005931c0`": CÁFOLVA (öt függvény, §3).
- „Az index hívólistája teljes": CÁFOLVA. A `0x006a63f0`-hoz 15 index-hívó van, a Ghidra-dumpban 19. A `0x0069f710`-hoz 8, illetve 11. A `0x005e8a70`-hez 4, illetve 7. Negatív állítást csak asm-pásztázásra lehet alapozni.
- „Az A ág elem-`+0x18`-mentes": NEM ZÁRHATÓ teljesen, mert a hívott törzsek egy része nincs végigolvasva (§4).
- „A `0x006a2a60` az A ágon a szótárat hívja": CÁFOLVA (`0x006a2a6b`).

##### §9 Nyitott lista (38.2.57 §9, felülírva: lásd 38.2.58 §9)

Nyitott kérdések mérlege (38.2.57): 54 tétel · 12 lezárva · 26 részben · 16 nincs meg. Az előző (38.2.56) ugyanez. Új tétel nincs. Változás a tartalomban: U49 és U53 szövege.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U49 | RÉSZBEN (szöveg pontosítva, 38.2.57 §4) | a `+0x18` az X-láncban a `T2[index]`-be kerül (`0x004e59fa`); az A ágon nem jut be. Az X forrása NINCS MEG | `0x004e5740`, `0x00467ca0`, `0x0046d7d0`, `0x006a2a60` |
| U53 | RÉSZBEN (38.2.57 §4) | A ág: figyelő `0x13320000`, kulcs `redo`, a `+0x18` nem jut a szótár-ágra, a T2 olvasója a `0x006a63f0`. B ág (`0x005931c0` → `0x00595db0` → `0x00425f60` → `0x004eec80` / `0x004ef040`): nincs megnézve, blokkoló | `0x005931c0`, `0x00595db0`, `0x00425f60`, `0x004eec80`, `0x004ef040`, `0x006a63f0` |

**A felhasználó szemével**

Ebből még nem derül ki, hogy az Időrend képeket, albumokat vagy személyeket mutat. Az A ág egy szöveget ír egy `redo` nevű oszlopba, nem a fájltípus-kódot. Az irányt nem zárjuk le: a B ágon a `0x00425f60` dönti el, hogy a fájltípus-kódot olvassa-e valaki.

#### 38.2.58 Az Időrend bináris feltárása, 41. kör: a B ág olvasója, az elem fájltípus-kódja és a figyelő (#5401, 2026-10-22)

**Kérdés és hatókör.** A 38.2.57 §6 három blokkoló címe és a fő kérdés (U53): (1) a `0x00425f60` olvassa-e az elem `+0x18` fájltípus-kódját; (2) a `0x00595db0` `this`-e (X), és van-e T2-olvasás a `0x00425f60` hívása előtt; (3) a `0x006a70e0` törzse és a `redo` kulcs szerepe; (4) a fő kérdés állapota. Bemenet: `2026-10-22-idorend-41.txt` (a három dekompilátum és a hívólistáik), a 38.2.57 §4-§6, a gépi kód a `pe_dis.cdis`-szel, a függvényméretek az index `functions` táblájából, és a 38.2.52 §2 kiterjesztés-táblája. Kódot nem módosítottunk, a CI-őrök nem futottak (nincs kódváltozás). Ideiglenes fájl a `.bt/` alá került, a kör végén törölve.

**Jelölések.** `A` a `0x004eec80` és a `0x004ef040` első argumentuma (a `0x00425f60` verem-változója, `[esp+0x80]`). `C` az `A+0x480` mező. `T2` a `C+0x58` mező: egész tömb, az adata `+0x48`, a kapacitás-mezője `+0x4c`. `E` az elem: az `A+0x3f0` mutató-tömb `idx` rekeszének rekordja, ha a rekesz nem nulla; különben az `A+0x3f8` tartalék rekord. `S` az a kódhalmaz, amelyre a `0x004eec80` jelzőt állít (§4).

**Válasz röviden.**

1. **Q1, a `0x00425f60`: közvetlenül nem, közvetve igen.** A saját törzsében nincs elem-`+0x18` olvasás. A függvény meghívja a `0x004eec80`-at (`0x00426d33`), amely olvassa és átírja az elem `+0x18` mezőjét, és a `0x004ef040`-et (`0x004264d9`, `0x00426cac`), amely `+0x18`-ba ír.
2. **Q2, a `0x00595db0`: nincs T2-olvasás a hívás előtt.** X az egyetlen argumentum. A törzsben nincs T2-mezőre címzés. A hívás előtt az `M` vtábla +0x24 hívása és a `0x006bb1d0` hívás van, ezek törzse NINCS MEG.
3. **Q3, a `0x006a70e0`: végig olvasva, a `0x13320000` ágra.** Nem ír értéket, csak a sor-indexet ellenőrzi, szükség esetén bővíti a tömböt, és megjelöli a tulajdonost. A `redo` kulcs nem jut be a függvénybe.
4. **Fő kérdés (U53): RÉSZBEN marad, de a B ágon van mért olvasó.** A `0x004eec80` olvassa a `+0x18` kódot, az `S` kódokra jelzőt állít, és a `+0x18` mezőt `4`-re írja. Hogy ez mikor fut, azt három feltétel dönti el; ezek és az `A` azonosítása NINCS MEG. ⚠️ PONTOSÍTVA (38.2.59 §1): a három feltétel asm-szinten ismert, az `A` azonosítva (`P+0xf8`); a feltételek bemenetei NINCS MEG.

##### §1 Q1: a `0x00425f60` és az elem `+0x18`

- **Belépés.** `stdcall`, `ret 0x18`: hat verem-argumentum. A `[ebp+8]` az első (a dekompilátumban `param_1`, a tároló), a `[ebp+0xc]` az `idx`. Nincs ECX-es `this`. ⚠️ PONTOSÍTVA a 38.2.57 §6-ban: hat verem-argumentum, nem „this és hat argumentum”.
- **Saját törzs.** A `+0x18` operandus 11 előfordulása (`0x00426394`-`0x00428be9`). Két verem-helyi (`cmp byte ptr [ebp+0x18]`). Kilenc vtábla-hívás: egy objektum vtábla 6-os slotját hívja (`mov edx,[eax+0x18]`, majd `call edx`). Elem-olvasás nincs.
- **Hívott `0x004eec80`, `0x00426d33`.** Argumentumok: `push edi` (idx), `push edx` (az `edx` a `[esp+0x80]`, vagyis az `A`).
- **Hívott `0x004ef040`, `0x004264d9` és `0x00426cac`.** A harmadik argumentum az érték. Az első helyen `eax`, a másodikon `esi`. A másodiknál `esi = 0x18`, ha a `byte ptr [eax+4]` nem nulla (`0x00426c93`); egyébként az `esi` előző értéke, ez NINCS MEG.
- **Az `A` írói.** A `[esp+0x80]` (a dekompilátumban `local_1800`) két helyen változik: `0x00428382` (a `0x009d61e0` hívás a címét kapja) és `0x004289af` (`fistp`, egész szám). Melyik az utolsó írás a `0x00426d33` előtt: NINCS MEG. ⚠️ JAVÍTVA (38.2.59 §1): egyik író sincs a `0x00426d2a` úton, az `A` a prológus értéke (`P+0xf8`).

##### §2 Q2: a `0x00595db0`

- **Belépés.** `stdcall`, `ret 4`: egy argumentum, X.
- **Kapu** (dekompilátum): `[X+0x3094] != 0` és `[X+0x309c] != -1`. A gépi kód kapuját nem néztük végig.
- **Hívás** (`0x00595f3c`): a `call 0x425f60` előtt `push 1`, háromszor `push ebx` (a dekompilátum szerint `ebx = 0`), `push [X+0x309c]`, `push [X+0x2bc]`. Vagyis `(M, idx, 0, 0, 0, 1)`, ahol `M = [X+0x2bc]`.
- **T2-olvasás a hívás előtt: nincs.** A törzsben nincs T2-mezőre címzés. A dekompilátum szerint a `[X+0x3094]` objektum `+0xc8` és `+0xcc` mezőit olvassa; ezek méretek, nem T2. A `0x00425f60` előtt két hívás van: az `M` vtábla +0x24 slotja (`idx, 0, 0` argumentumokkal), és a `0x006bb1d0(M+0x3200, ...)`. Mindkettő törzse NINCS MEG.

##### §3 Q3: a `0x006a70e0`

- **Hívó.** A `0x006a64c6` (a `0x006a63f0` A ágában): `push esi` (a figyelő F), `push ebx` (a tároló P), `eax = [ebp+0x10]` (a sor). `ret 8`. A `redo` kulcs nincs a két argumentum között.
- **Ág.** `switch([F+0x328])`. A `0x006a63f0` a figyelőt a `0x13320000` típussal kéri (38.2.57 §1), tehát ez az ág fut, ha a figyelő ezzel a típussal jött létre. Ha ugyanezt a kulcsot más hívó más típussal hozta létre, más ág fut; a gyár (`0x006a41e0`) kulcs-ellenőrzése NINCS MEG.
- **A `0x13320000` ág lépései.**
  1. Ha `sor < FUN_006a2930(F+0x14)`, a függvény `return 0`-val kilép (a `FUN_006a2930` jelentése NINCS MEG).
  2. Zárolás a `F+0xf4` burkolón.
  3. Ha `sor >= kapacitás` (`F+0x140 >> 1`): a tömb (`F+0x13c`) bővítése, a régi rekeszek átmásolása, a ytString referenciaszám növelése. Ha a foglalás nulla, `return 4`.
  4. Feloldás, majd megjelölés: `F+0x4` nő, `[F] = 1`, `P+0x4c` nő, `P+0x50 = 1`, `return 0`.
- Az új rekeszek nullázását ebben az ágban nem láttam (a `0x13320007` ágban van nullázó ciklus). A szöveget a hívó `0x006a63f0` írja a hívás után (38.2.56 §5).
- **A többi ág.** A `0x13320001`-`0x13320005`, a `0x13320007` és az alapág (`return 3`) nem Időrend-ág. ⚠️ LEZÁRVA (38.2.57 §6): a törzs ezen az ágon végigolvasva.

##### §4 Fő kérdés (U53)

- **Állapot.** RÉSZBEN, nyitva. A 36-41. körben ez az első mért olvasó a B ágon; a 38.2.57 §4 ezt még nem tudta.
- **A ág (változatlan).** `0x00566270` → `0x0045ff60` → `0x0069f710` → `0x006a63f0` → `0x006a70e0` (§3). A `+0x18` ezen az ágon nem olvasódik (38.2.57 §4).
- **B ág, a lánc.** `0x005662eb` → `0x005931c0` → `0x00595db0` → `0x00425f60` → (feltételesen) `0x004eec80` vagy `0x004ef040`.
  - A `0x00425f60` elején a dekompilátum szerint `FUN_004edf60()` visszatérését és a `local_1778` mutatót vizsgálja; ha a feltétel nem teljesül, a függvény azonnal visszatér. A `0x004edf60` jelentése NINCS MEG.
  - A `0x004eec80` hívása (`0x00426d33`) akkor fut, ha (a) a dekompilátum szerint `pcStack_1844 != 0` vagy `cStack_158c == 0`, és (b) gépi kódban ellenőrizve: a `[esp+0xdc]` vagy a `[esp+0xe0]` kisebb kettőnél, vagy a `pcVar27` nem nulla (`0x00426cfd`-`0x00426d28`). A `pcVar27` a `pcStack_1844`, vagy 3, ha a `p_Stack_15cc` vagy a `p_Stack_15c8` kisebb kettőnél. A `pcStack_1844` a `0x005b1570` visszatérése. ⚠️ PONTOSÍTVA (38.2.59 §2): az EAX a kilépéskor ágtól függ. A `[esp+0xdc]` és a `[esp+0xe0]` a `local_17ac` méret-struktúrából jön, amelyet az `M+0x58` vtábla +4 hívása tölt (dekompilátum). Az (a) és a (b) bemenete NINCS MEG. ⚠️ PONTOSÍTVA (38.2.59 §1): a két kapu asm-szinten ismert, a bemenetek továbbra is NINCS MEG.
  - A `0x004ef040` két hívásának feltétele NINCS MEG.
- **A `0x004eec80` két része.**
  1. T2 rész, ha `T2 != 0` és `idx != -1`. Ha az `idx` a kapacitáson belül van, és `T2[idx] != 4`: `T2[idx] = 4`, majd a figyelő értesítése (`0x006a2a60`, `0x004eeeb9`-`0x004eeebc`). Ha nincs elég kapacitás: a T2 bővítése, az új rekeszek kitöltése `[C+0x5c]`-vel, majd `T2[idx] = 4` (`0x004eee90`) és értesítés. Hogy mire használják a T2-t: NINCS MEG.
  2. Elem rész, a T2 résztől függetlenül, ha `idx` kisebb, mint `[A+0x3f4] >> 1`: az `E` kiválasztása, az `E+0x18` olvasása. Ha a kód az `S`-ben van, `A+0x4dd = 1`. Majd `E+0x18 = 4`, `E+0x1c = 0` (bájt), `A+0x5c` nő, `A+0x60 = 1` (`0x004eef34`-`0x004eef86`).
- **Az `S` kódhalmaz.** `2`, `3`, `6`-`18`, `21`-`24`, `26`, `27`-`29`, `31`, `1001`. Nincs benne: `0`, `1`, `4`, `5`, `19`, `20`, `25`, `30`, a `-1`, és a 32-nél nagyobb kódok, az `1001` kivételével. A 38.2.52 §2 táblájából ezek neve látszik: `2` `.jpg`, `3` `.gif`, `6` `.bmp`, `8` `.avi`, `9` `.mov` és `.mp4`, `14` `.png`, `15` `.mp3`, `18` RAW, `21` `.url`, `22` `.tga`, `27` `.txt`, `28` kódfájlok, `29` `.ogg` és `.ogv`, `31` `.webp`. A többi kód nevét ebben a körben nem néztük meg. Az `1001` a `0x00507590` által írt érték (38.2.53 §3); a neve NINCS MEG.
- **Döntés.** Az irányt nem zárjuk le. A B ágon a `0x004eec80` olvassa és írja a `+0x18` kódot, de a hívás feltételei és az `A` azonosítása még hiányzik. A döntő címek: `0x004edf60` (kapu), `0x005b1570` (a `pcStack_1844`), és a `0x00428382`, `0x004289af` (az `A` írói). Az `A+0x4dd` jelző olvasóit is meg kell keresni; a felhasználói hatás ebből derül ki.

##### §5 Bizonyítottsági fok (38.2.58)

| állítás | bizonyíték | fok |
|---|---|---|
| a `0x00425f60` stdcall, hat verem-argumentum | gépi kód `0x00425f60`-`0x00425f89`, `ret 0x18` | megerősített |
| a `0x00425f60` törzsében nincs elem-`+0x18` olvasás | a `+0x18]` alakú címzések szkennelése: 11 találat, 9 vtábla-hívás, 2 verem-helyi | megerősített |
| a `0x00425f60` hívja a `0x004eec80`-at a `0x00426d33`-nál | gépi kód: `push edi`, `push edx`, `call 0x4eec80` | megerősített |
| a `0x004eec80` stdcall, `ret 8`, első argumentuma `A` | gépi kód `0x004eec80`-`0x004eec8c`: `ebx = [esp+0x1c]` a belépés után | megerősített |
| a `0x004eec80` olvassa az `E+0x18`-at | gépi kód `0x004eef34` (`mov eax,[ecx+0x18]`) | megerősített |
| a `0x004eec80` jelzőt állít az `S` kódokra | gépi kód `0x004eef37`-`0x004eef6e` (az elágazások) | megerősített |
| a `0x004eec80` `E+0x18 = 4`-et és `E+0x1c = 0`-t ír | gépi kód `0x004eef77`, `0x004eef7e` | megerősített |
| a `0x004eec80` `T2[idx] = 4`-et ír és értesít | gépi kód `0x004eeea0`-`0x004eeebc`, `0x004eee90` | megerősített |
| a `0x004ef040` `E+0x18 = arg3`-at ír | gépi kód `0x004ef2fe`-`0x004ef305` | megerősített |
| a `0x00595db0` hívása: `(M, idx, 0, 0, 0, 1)` | gépi kód `0x00595f24`-`0x00595f3c` | megerősített |
| a `0x00595db0` törzsében nincs T2-olvasás | gépi kód és dekompilátum | megerősített; a `vt[+0x24]` célja NINCS MEG |
| a `0x006a70e0` két verem-argumentumú, az index EAX-ben | gépi kód `0x006a64bd`-`0x006a64c6`, `ret 8` | megerősített |
| a `0x006a70e0` nem kap `redo` kulcsot | a hívó két argumentumot tol (`0x006a64c4`-`0x006a64c5`) | megerősített |
| a `0x006a70e0` `0x13320000` ága nem ír értéket | dekompilátum, a teljes ág olvasása | megerősített |
| az `A` azonossága (`[esp+0x80]`) | ⚠️ JAVÍTVA (38.2.59 §1): a két író nincs a `0x00426d2a` úton; a prológus értéke `P+0xf8` | megerősített |
| a `0x004eec80` hívásának feltétele | gépi kód `0x00426cfd`-`0x00426d28`; a kapu többi része dekompilátum | részben (a bemenetek NINCS MEG) |
| a `0x004ef040` két hívásának értéke | gépi kód `0x004264d9`, `0x00426cac` | részben (a második érték NINCS MEG) |
| a `+0x18` írói teljes listája | közvetlen címzés pásztázása | részben (a `rep movs` és a mutató-másolás nem látszik) |

##### §6 Ghidra-címek a következő körhöz (felülírva: lásd 38.2.59 §6)

**Blokkoló (B ág):**
- `0x004edf60`: a `0x00425f60` belépési kapuja (visszatérés és `local_1778` teszt). [blokkoló]
- `0x005b1570`: a `pcStack_1844` értéke (a `0xf4242` és a nulla teszt). [blokkoló]
- `0x00428382` (a `0x009d61e0` hívás) és `0x004289af`: az `A` (`[esp+0x80]`) írói; melyik az utolsó a `0x00426d33` előtt. [blokkoló]
- Az `M` vtábla +0x24 slotjának és az `M+0x58` objektum vtábla +4 slotjának célja. Az `M` vtábla-címe NINCS MEG, így a célok törzse sem. [blokkoló]
- Az `A+0x4dd` olvasói (xref, a jelzőt használó függvény): ebből derül ki a felhasználói hatás. [blokkoló a fő kérdésre]

**Nem blokkoló:**
- `0x006a2a60`: a T2-változás értesítésének célja (38.2.54 §2 szerint a figyelő).
- `0x006a2930`: a `F+0x14` darabszám jelentése.
- `0x006a41e0`: a gyár kulcs-ellenőrzése.
- `0x004ef040` két hívási helyének feltétele: `0x004264d9`, `0x00426cac`.

**Maradó, változatlan (38.2.56 §6):** `0x00593880`, `0x00594170`, `0x009079b0`, `0x00592f30`, `0x00415790`, `0x00b81bd4`, `0x00493660`, `0x006d1050`, `0x00411150`, `0x00985ff0`, `0x004127c0`, `0x00493d40`, `0x006a442e`.

##### §7 Javítások a korábbi szakaszokban

- **38.2.53 §3 (c):** a „csak mutató-betöltés és NULL-ellenőrzés” a `0x004ef040`-ra. ⚠️ JAVÍTVA: a `0x004ef040` `E+0x18 = arg3`-at ír (`0x004ef302`), és növeli az `A+0x5c` számlálót, állítja az `A+0x60` jelzőt.
- **38.2.57 §4:** „a `0x004eec80` és a `0x004ef040` T2-betöltők”. ⚠️ PONTOSÍTVA: a `0x004eec80` T2-t ír és `+0x18`-at olvas; a `0x004ef040` `+0x18`-at ír.
- **38.2.57 §4, a B ág T2-olvasója.** ⚠️ FRISSÍTVE: a B ág olvasója a `0x004eec80` (§4 itt).
- **38.2.57 §6, `0x00425f60`: „this és a hat argumentum”.** ⚠️ PONTOSÍTVA: hat verem-argumentum, nincs ECX-es `this`.
- **38.2.57 §6, `0x006a70e0`: „törzse nincs végigolvasva”.** ⚠️ LEZÁRVA (§3).
- **38.2.56 §6, `0x00425f60` blokkoló.** ⚠️ RÉSZBEN: a hívó és a hívott `0x004eec80` ismert, a feltételek nem (§1, §4).

##### §8 Amit KIZÁRTAM

- „A `0x00425f60` olvassa az elem `+0x18`-at”: CÁFOLVA a saját törzsében (§1). Közvetve igen (`0x004eec80`).
- „A `0x00595db0` T2-t olvas a `0x00425f60` hívása előtt”: CÁFOLVA a törzsben (§2).
- „A `0x004ef040` csak betölt”: CÁFOLVA (`0x004ef302`).
- „A `0x006a70e0`-nak van `redo` argumentuma”: CÁFOLVA (két verem-argumentum).
- „A `0x006a70e0` értéket ír a sorba”: CÁFOLVA (nincs értéket hordozó argumentum; a szöveget a hívó írja).
- „A `0x004eec80` csak T2-t ír”: CÁFOLVA (az elem `+0x18`-at is olvassa és írja).
- „A `+0x18` íróinak listája teljes”: NEM ZÁRHATÓ (a pásztázás csak a közvetlen címzést látja; a `rep movs` és a mutató-másolás nem).

##### §9 Nyitott lista (38.2.58 §9, felülírva: lásd 38.2.59 §9)

Nyitott kérdések mérlege (38.2.58): 54 tétel · 12 lezárva · 26 részben · 16 nincs meg. Az előző (38.2.57): ugyanez. Új tétel nincs. Változás a tartalomban: U49 és U53.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U49 | RÉSZBEN (38.2.58 §1, §4) | visszatérés és index LEZÁRVA; a `+0x18` a `0x004e5740`-ben a `T2[index]`-be kerül; a `0x004eec80` és a `0x004ef040` is olvassa vagy írja a `+0x18`-at. Hogy az `A` az Időrend elemeit tartalmazza-e: NINCS MEG | `0x004e5740`, `0x004eec80`, `0x004ef040`, `0x00467ca0`, `0x0046d7d0` |
| U53 | RÉSZBEN (38.2.58 §4) | B ág: a `0x00425f60` a `0x00426d33`-nál hívja a `0x004eec80`-at (`T2[idx] = 4`, az elem `+0x18`-ának osztályozása és `4`-re írása); a feltételek és az `A` azonosítása NINCS MEG; A ág: változatlan | `0x004eec80`, `0x004edf60`, `0x005b1570`, `0x00428382`, `0x004289af` |

**A felhasználó szemével**

Ha a rutin lefut, a B ágon minden vizsgált tételnél megnézi a fájltípust, a legtöbb ismert kép-, videó-, hang- és szöveges típusra jelzőt állít, majd a tételt `4`-es kódra írja át. Hogy ez a képernyőn mit jelent, és hogy a rutin az Időrendnél egyáltalán lefut-e, még nincs megmérve, ezért az irányt nem zárjuk le.

#### 38.2.59 Az Időrend bináris feltárása, 42. kör: a `0x004eec80` feltételei, első argumentuma és a jelző (#5401, 2026-10-22)

**Kérdés és hatókör.** A 38.2.58 §6 címei és a fő kérdés (U53): (1) mikor fut le a `0x004eec80`, és mi az első argumentuma; (2) hívja-e a `0x004edf60` vagy a `0x005b1570` a `0x004eec80`-at, és milyen argumentummal; (3) a `+0x4dd` jelző olvasói és hatásuk. Bemenet: `2026-10-22-idorend-42.txt` (a három dekompilátum és a hívólistáik), a 41. kör `0x00425f60` dekompilátuma (`2026-10-22-idorend-41.txt`), a 38.2.58 §4 és §6, és a bináris: `pe_dis.cdis` (asm), a `.text` teljes pásztázása (`paszta.utasitasok`, a `+ 0x4dd]` és a `+ 0x4de]` operandusra szűrve), az index `functions` és `xrefs` táblája, valamint egy vezérlésgráf-bejárás a `0x00425f60` törzsében. Kódot nem módosítottunk, a CI-őrök nem futottak (nincs kódváltozás). A bejáró szkript a scratchpadban volt, a kör végén törölve.

**Válasz röviden.**

1. **Q1: a `0x004eec80` három feltétele asm-szinten áll, az első argumentum azonosítva.** A hívás a `0x00425f60`-ban van (`0x00426d33`). Akkor fut, ha (1) a `0x005b1570` visszatérése nem `0xf4242`, és a `cStack_1586` nulla; (2) a `pcStack_1844` nem nulla, vagy a `cStack_158c` nulla; (3) a `[esp+0xdc]` vagy a `[esp+0xe0]` kisebb kettőnél, vagy a `pcVar27` nem nulla. Az első argumentum `P+0xf8`, ahol `P` a `0x00425f60` első argumentuma. A B ágon `P = [X+0x2bc]`, tehát az első argumentum `[X+0x2bc]+0xf8`. A második argumentum az `idx`.
2. **Q2: nem.** A `0x004edf60` és a `0x005b1570` egyike sem hívja a `0x004eec80`-at. A `0x004edf60` első argumentuma ugyanez a `P+0xf8`.
3. **Q3: egy olvasó van.** A teljes `.text`-ben a `+0x4dd` jelzőt a `0x004fbb30` olvassa. Ha nem nulla, a függvény a tárolt elemek vtábla `+8` slotját hívja, utána `+0x4de = 1`, `+0x4dd = 0`, és meghívja a `0x00411cf0`-at. A jelzőt tizenegy függvény írja.
4. **Fő kérdés (U53): RÉSZBEN marad, nem zárjuk le most.** A hívás feltételei és az első argumentum mért. A három állapotmező (`pcStack_1844`, `cStack_158c`, `cStack_1586`) és a méret-mezők (`[esp+0xdc]`, `[esp+0xe0]`, `[esp+0x2b4]`, `[esp+0x2b8]`) forrása NINCS MEG. A felhasználói hatás nincs megmérve (§4). ⚠️ PONTOSÍTVA (38.2.60 §3): a `pcStack_1844`-nek négy írója van; a `cStack_158c`-nek és a `cStack_1586`-nak nincs közvetlen írója. ⚠️ FRISSÍTVE (38.2.60 §4): LEZÁRVA.

##### §1 Q1: a hívás, az első argumentum és a három feltétel

**A hívóhely.** `0x00426d2a`-`0x00426d33` (asm): `mov edx, [esp+0x80]`, `push edi`, `push edx`, `call 0x4eec80`. Stdcall, `ret 8`. Az első argumentum (`A`) a `[esp+0x80]`, a második (`idx`) az `edi`. Az `edi` a `0x426474` `mov edi, esi` miatt az `esi`, az `esi` utolsó írása a `0x4263ba` `mov esi, [ebp+0xc]`, tehát a `0x00425f60` második argumentuma.

**Az első argumentum: `A = P+0xf8`.**
- A prológusban (`0x425f94`-`0x425f9b`): `lea eax, [ebx+0xf8]`, ahol `ebx = [ebp+8] = P`. Ezután `push ecx`, majd `mov [esp+0x84], eax`. A három belépési push után a törzs bázisa `B`, így a `[esp+0x84]` a `B+0x80`, vagyis a `[esp+0x80]`.
- A törzsben a `[esp+0x80]` két helyen íródik: `0x42837a` (`lea ecx, [esp+0x80]`, a címét a `0x9d61e0` hívás kapja) és `0x4289af` (`fistp dword ptr [esp+0x80]`, az `[esp+0xc8]` kerekítése). A visszafelé vezérlésgráf-bejárás a `0x426d2a`-tól a `0x425f60` belépéséig 360 csomópontot ér el, és sem a két író, sem más írás nincs közöttük. A prológus `0x425f9b`-es tárolása az egyetlen író az úton. A `0x425f60` és a `0x425f9b` között nincs ugrás, tehát ez a tárolás minden úton lefut: az `A` a `P+0xf8` ezen a hívóhelyen.
- Ellenőrzés a Ghidra-névadással: a dekompilátum `local_1800` neve és az asm `[esp+0x80]` összege `0x1880`. Ugyanez a pár: `uStack_17a4`/`[esp+0xdc]`, `p_Stack_15cc`/`[esp+0x2b4]`, `cStack_158c`/`[esp+0x2f4]`, `pcStack_1844`/`[esp+0x3c]`. A dekompilátum a 280. sorban (`local_1800 = param_1 + 0x3e`) és a 945. sorban (a `0x4289af` fistp-je) írja a változót. A 945. sor nincs az úton.
- **A B ágon.** A `0x00595f3c` hívásban (38.2.58 §2) az első argumentum `[X+0x2bc]` (`M`), a második `[X+0x309c]`. Tehát `A = [X+0x2bc]+0xf8`.

**A hívás előtti kapuk (a `0x00425f60` törzsében).**
- `0x426013`-`0x426015`: a `0x004edf60` visszatérése (EAX) nem nulla, kilépés (`EAX = 2`). A `0x004edf60`-t a `0x42600e`-nál hívja; a két stack-argumentum `A` (`P+0xf8`) és a kimeneti rekord (`B+0x108`), az `in_EAX` az `idx`.
- `0x426062`-`0x42607f`: a `[esp+0x108]` mutató nulla, vagy a mutatott dword `& 0xffffff00` nulla, vagy a `+4` bájt nulla: kilépés.
- `0x426081`-`0x426089`: a rekord típusa (`[esp+0x120]`, a `+0x18` mező másolata) 4: kilépés a `0x426d69`-en (dekompilátum: `0x00412790`). A `0x4eec80` a tétel típusát 4-re írja (38.2.58 §4), tehát a következő `0x425f60`-futás ezt a tételt kihagyja.

**A három feltétel, amely a hívást eldönti.** A `0x426d33` hívás csak akkor fut, ha mind a három igaz:

1. **Nincs korai kilépés a `0x005b1570` után.** `pcStack_1844 != 0xf4242` (`0x426571`-`0x426576`), és `cStack_1586 == 0` (`0x4265d1`-`0x4265d9`). Ha a `cStack_1586` nem nulla, a `0x4265e2` a `0x425cc0`-t hívja, lásd §7.
2. **Első kapu.** `pcStack_1844 != 0`, vagy `cStack_158c == 0` (`0x42663f`-`0x426647`: `test eax, eax`, `jne 0x426cf8`, majd `cmp byte ptr [esp+0x2f4], al`, `je 0x426cf8`; az `al` itt nulla, mert a `jne` nem ugrott). Ha egyik sem igaz, a `0x426654` ágon nincs hívás.
3. **Második kapu.** `[esp+0xdc] < 2` vagy `[esp+0xe0] < 2` vagy `pcVar27 != 0` (`0x426d14`-`0x426d28`). A `pcVar27` (az EAX) 3, ha `[esp+0x2b4] < 2` vagy `[esp+0x2b8] < 2` (`0x426cfd`-`0x426d0f`), egyébként a `pcStack_1844`. Ha egyik sem igaz, a `0x426d7a` ágon megy tovább.

##### §2 Q2: a `0x004edf60` és a `0x005b1570`

- **A `0x004edf60` nem hívja a `0x004eec80`-at.** A `0x004eec80` index-hívóinak listájában (`0x425cc0`, `0x425f60`, `0x505030`) nincs benne, és a `0x004edf60` dekompilált hívottjai között sincs a `0x004eec80`. Feladata a tétel rekordjának kiolvasása: az `A` az első, a kimeneti rekord a második argumentum, az `idx` az EAX-ben. A típus a rekord `+0x18` mezőjében van.
- **A `0x005b1570` nem hívja a `0x004eec80`-at** (ugyanez a két bizonyíték). A `0x00425f60` a `0x4264b1`-nél hívja: `this` = `B+0x1f8` (a `lea ecx, [esp+0x200]` két push után áll, a törzs bázisához képest `B-8+0x200`), első argumentum a fájlnév (`[esp+0x38]`, a rekord `+4` mezője), második a típus-kimenet (`[esp+0x70]`). Ez a rutin számolja a típus-kódot. A `[esp+0x70]` lesz a `0x4264d9`-es `0x004ef040` hívás harmadik argumentuma, vagyis a tétel `+0x18` mezőjébe íródik.
- **Pontosítás a `0x005b1570` visszatérésére (38.2.58 §4).** A dekompilátum `void`-nak mutatja, de a hívó az EAX-et használja. A közös kilépés (`0x5b1b3a`) előtt az EAX ágtól függ: `0x5b1988`: `0xf4242`; `0x5b19bf`: a `local_a4c` állapotkód (az `0x5acf40` hívás után); `0x5b19b3`: a `0x5b1460` visszatérése (nincs mérve); `0x5b1b1c`: 2; `0x5b1b38`: 0. Tehát a `pcStack_1844` a legtöbb ágon állapotkód, de nem mindenütt.

##### §3 Q3: a `+0x4dd` jelző írói, olvasója és hatása

**Közvetlen `+ 0x4dd]` címzés a teljes `.text`-ben (2 884 879 utasítás), 15 találat:**

| cím | függvény | művelet |
|---|---|---|
| `0x004e4504` | `FUN_004e41f0` | `mov byte ptr [ebp+0x4dd], bl` (az érték NINCS MEG) |
| `0x004e823d` | `FUN_004e80d0` | `= 1` |
| `0x004e9325` | `FUN_004e91f0` | `= 1` |
| `0x004e942c`, `0x004e993d`, `0x004e9a1c` | `FUN_004e9400` | `= 1` (három hely) |
| `0x004eb378` | `FUN_004ea360` | `= 1` |
| `0x004ec048` | `FUN_004ebff0` | `= 1` |
| `0x004eef70` | `FUN_004eec80` | `= 1` (az `S` halmaz tétele, 38.2.58 §4) |
| `0x004f8ea6` | `FUN_004f8ae0` | `= 1` |
| `0x004f97a0` | `FUN_004f9450` | `= 1` |
| `0x004f98fe` | `FUN_004f97f0` | `= 1` |
| `0x004fbac7` | `FUN_004fb9c0` | `= 1` |
| `0x004fbb79` | `FUN_004fbb30` | `= 0` (a kiürítés) |
| `0x004fbb30` | `FUN_004fbb30` | `cmp byte ptr [esi+0x4dd], 0` (az egyetlen olvasó) |

**Mit csinál a `0x004fbb30`, ha a jelző be van állítva** (asm `0x4fbb30`-`0x4fbb89`):
1. Ha `[esi+0x4dd] == 0`: visszatér (`0x4fbb85`).
2. Ha nem nulla, és `[esi+0x488]` legalább kettő (`test ..., 0xfffffffe`): végigmegy az `i < [esi+0x488] >> 1` elemen. Minden elemre: `obj = [[esi+0x484] + i*4]`, és az `obj` vtábla `+8` slotját hívja, `this` az `obj`, argumentum `esi`.
3. Utána `[esi+0x4de] = 1`, `[esi+0x4dd] = 0`, és `call 0x00411cf0` (172 bájt, a célja NINCS MEG). ⚠️ LEZÁRVA (38.2.60 §2): zár, puffer ürítése, elengedés.

**A hívói.** Az index szerint hét hívó van: `0x004e91f0`, `0x004e9400` (három hely), `0x004ea360`, `0x004ebff0`, `0x004f8ae0`, `0x004f9450`, `0x004fb9c0`. Mind a hét szintén ír a jelzőbe (a táblázat szerint). A `0x004fbb30` nem állítja be az `esi`-t, a hívó adja. Hogy a hívó `esi`-je az `A`-e, NINCS MEG.

**A `+0x4de` jelző.** Két cím van a `.text`-ben: `0x004e450a` (`mov byte ptr [ebp+0x4de], bl`, a `FUN_004e41f0`-ban) és `0x004fbb72` (`= 1`, a `0x004fbb30`-ban). Közvetlen címzésű olvasót nem találtunk.

##### §4 Fő kérdés (U53) és a döntés

**Állapot: RÉSZBEN marad.** Mért: a három feltétel (§1), az `A` azonossága (§1), a két további hívóhely (`0x425cc0`, `0x505030`, §7), és a jelző egy olvasója (§3). NINCS MEG: a `pcStack_1844`, a `cStack_158c`, a `cStack_1586`, a `[esp+0xdc]`, a `[esp+0xe0]`, a `[esp+0x2b4]` és a `[esp+0x2b8]` értéke. A törzsben ezekre nincs közvetlen `[esp+X]` írás, tehát vagy mutatón át íródnak, vagy más úton kapják; ezt nem néztük meg.

**Döntés: nem zárjuk le most.** A három állapotmező forrása egy Ghidra-körrel lekérdezhető (§6), és a jelző olvasója már mért. ⚠️ FRISSÍTVE (38.2.60 §4): az U53 LEZÁRVA. A következő kör feladata egyetlen kérdés: honnan jönnek a három állapotmező. Ha ezt a következő kör sem nevezi meg, U53 lezárandó, és ezek maradnak NINCS MEG: a három állapotmező és a méret-mezők forrása, a `0x004fbb30` hívóinak `esi`-je, a `0x004fbb30` vtábla-hívásainak célja, és a `0x00411cf0` hatása.

**A felhasználó szemével**

Ebből még nem derül ki, mit lát a felhasználó az Időrendben. Ha a jelző be van állítva, a Picasa a tárolt elemeken vtábla-hívásokat végez, és ezek képernyőn látható hatása még nincs megmérve. A tétel típusa közben 4-re áll, így a következő feldolgozásnál kimarad; hogy ez mit jelent a képen, szintén nincs megmérve.

##### §5 Bizonyítottsági fok (38.2.59)

| állítás | bizonyíték | fok |
|---|---|---|
| a hívás első argumentuma `[esp+0x80]`, második `edi` (`idx`) | asm `0x426474`, `0x426d2a`-`0x426d33`, `0x4263ba` | megerősített |
| `A = P+0xf8`, és nincs más író a hívás előtt | asm `0x425f94`-`0x425f9b`; ősök-bejárás (360 csomópont); dekompilátum 280. és 945. sor | megerősített (a bejárás nem követi a push-eltolású írásokat a teljes törzsben; a `[esp+0x6c]`-`[esp+0x9c]` tartományt ellenőriztük) |
| a három feltétel címei és ágai | asm `0x426571`, `0x4265d1`, `0x42663f`-`0x426649`, `0x426cfd`-`0x426d28` | megerősített |
| a `[esp+0xdc]`, `[esp+0xe0]`, `[esp+0x2b4]`, `[esp+0x2b8]`, `[esp+0x2f4]`, `[esp+0x2fa]` írói | nincs közvetlen `[esp+X]` írás a törzsben | NINCS MEG (mutatón át íródhatnak) |
| a `0x004edf60` és a `0x005b1570` nem hívja a `0x004eec80`-at | index `xrefs`; dekompilátum hívottjai | megerősített |
| a `0x005b1570` EAX-e a kilépéskor ágtól függ | asm `0x5b1988`, `0x5b19b3`, `0x5b19bf`, `0x5b1b1c`, `0x5b1b38` | megerősített |
| a `0x004eec80` hívóhelye három | index `xrefs` | megerősített |
| a `+0x4dd` olvasója egy | teljes `.text` pásztázás `+ 0x4dd]` címzésre | megerősített (csak közvetlen címzés) |
| a `0x004fbb30` hatása: vtábla-hívás, majd `+0x4de`, `+0x4dd` és `0x411cf0` | asm `0x4fbb30`-`0x4fbb89` | megerősített; a hívott célok NINCS MEG |
| a `0x425cc0` és a `0x505030` hívási feltétele | asm részben | részben (a vtábla-hívások eredménye NINCS MEG) |
| a felhasználó által látott hatás | nincs | NINCS MEG |

##### §6 Ghidra-címek a következő körhöz (felülírja a 38.2.58 §6-ot; felülírva: lásd 38.2.60 §6)

**Blokkoló (U53):**
- `0x005b1570`: a `this` (`B+0x1f8`) és a visszatérési állapot. A `cStack_158c` és a `cStack_1586`, valamint a `p_Stack_15cc`/`p_Stack_15c8` mutatóforrása, ha a `this`-ből jön. [blokkoló]
- Az `M+0x58` objektum vtábla `+4` célja: ez tölti a `[esp+0xdc]` és `[esp+0xe0]` méret-struktúrát (38.2.58 §4). [blokkoló]
- `0x004fbb30` hívói: `0x004e91f0`, `0x004e9400`, `0x004ea360`, `0x004ebff0`, `0x004f8ae0`, `0x004f9450`, `0x004fb9c0`. Az `esi` értéke (az `A`-e?). [blokkoló a jelző hatásához] ⚠️ LEZÁRVA (38.2.60 §1): az esi-értékek megvannak; az `A`=R kérdés NINCS MEG.
- `0x004fbb30` vtábla `+8` célja (a gyerek-elemek) és `0x00411cf0`. [blokkoló a felhasználói kérdésre]

**Nem blokkoló:**
- `0x00425cc0` (a `0x425db5`-nél hívja a `0x4eec80`-at): a belépés mért (EAX ∈ {`0xf462d`, `0xf462e`, `3`}), a vtábla-hívások és a `0x425d83`-`0x425da1` importhívások eredménye nincs végigolvasva.
- `0x00505030` (a `0x505123`-nál hívja): `A` az első argumentum (nincs `+0xf8`), `idx` a `0x4efa20` kimenete (`[esp+0x50]`). Kapu: a `0x4019b0` eredménye nulla (`0x505110`) és `idx != -1` (`0x505118`). A `0x4efa20` és a `0x4019b0` törzse nincs végigolvasva.
- `0x004e41f0`: a `bl` érték forrása (`0x4e4504`, `0x4e450a`).

##### §7 Javítások a korábbi szakaszokban

- **38.2.57 §4 és 38.2.58 §4: „az index szerint mindkettőt a `0x00425f60` hívja”.** ⚠️ JAVÍTVA: a `0x004eec80` hívóinak index-listája három függvény: `0x00425cc0` (`0x425db5`), `0x00425f60` (`0x426d33`) és `0x00505030` (`0x505123`). A `0x004ef040` hívói: a `0x00425f60` két helyen (`0x4264d9`, `0x426cac`), továbbá `0x0053ca40`, `0x0053de70` és `0x0053e8d0`.
- **38.2.58 §1, „Az `A` írói”, és §5, „az `A` azonossága”.** ⚠️ JAVÍTVA: egyik író sincs a `0x426d2a` úton (§1), az `A` a `P+0xf8`.
- **38.2.58 §4, a `pcStack_1844` és a három feltétel.** ⚠️ PONTOSÍTVA: a visszatérés ágtól függ (§2), a feltételek asm-szinten ismertek (§1).
- **Kiegészítés (nem javítás):** a `cStack_1586 != 0` ágon a `0x00425f60` a `0x425cc0`-t hívja (`0x4265e2`), amely a `0x425db5`-nél a `0x4eec80`-at. Az `A` itt is `P+0xf8` (a `0x425cc0` első argumentuma a `P`), az `idx` a `0x425cc0` `this`-e (az `edi`). Ezt a 38.2.58 §4 nem említette.

##### §8 Amit KIZÁRTAM

- „A `0x004eec80` csak a `0x00425f60`-ból hívódik”: CÁFOLVA (három hívó, §7).
- „A `0x004edf60` vagy a `0x005b1570` hívja a `0x004eec80`-at”: CÁFOLVA (§2).
- „Az `A`-t a `0x42837a` vagy a `0x4289af` írja a `0x426d2a` előtt”: CÁFOLVA (§1; a bejárásban egyik sincs).
- „A `0x005b1570` EAX-e mindig a státuszkód”: CÁFOLVA (§2).
- „A `+0x4dd` jelzőnek több olvasója van”: a közvetlen címzésű pásztázás szerint CÁFOLVA. Mutatón át olvasás nem zárható ki.
- „A `+0x4de` jelzőt olvassa valaki”: NEGATÍV a közvetlen címzésű pásztázás szerint (nincs olvasó).

##### §9 Nyitott lista (38.2.59 §9, felülírva: lásd 38.2.60 §9)

Nyitott kérdések mérlege (38.2.59): 54 tétel · 12 lezárva · 26 részben · 16 nincs meg. Az előző (38.2.58) ugyanez. Új tétel nincs. Változás a tartalomban: U49 és U53 szövege.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U49 | RÉSZBEN (38.2.58 §1, §4) | a `+0x18` a `0x004e5740`-ben a `T2[index]`-be kerül; a `0x004eec80` és a `0x004ef040` olvassa vagy írja a `+0x18`-at; az `A` = `P+0xf8` (38.2.59 §1). Hogy az `A` az Időrend elemeit tartalmazza-e: NINCS MEG | `0x004e5740`, `0x004eec80`, `0x004ef040`, `0x00467ca0`, `0x0046d7d0` |
| U53 | RÉSZBEN (38.2.59 §1-§4) | a hívás három feltétele asm-szinten áll; `A = P+0xf8` (B ágon `[X+0x2bc]+0xf8`); a három állapotmező és a méret-mezők forrása NINCS MEG; a két további hívóhely (`0x425cc0`, `0x505030`) részben mért; a jelző egy olvasója mért, a hatása NINCS MEG | `0x005b1570`, `0x004edf60`, `0x004fbb30`, `0x00425cc0`, `0x00505030`, `0x00411cf0` |

#### 38.2.60 Az Időrend bináris feltárása, 43. kör: a `0x004fbb30` hívói, a `0x00411cf0` és az U53 lezárása (#5401, 2026-10-22)

**Kérdés és hatókör.** A 38.2.59 §6 blokkoló címei (`0x004fbb30`, `0x00411cf0`, `0x004f8ae0`, `0x004e91f0`) és az U53 lezárása. Bemenet: `2026-10-22-idorend-43.txt` (a négy dekompilátum és a hívólistáik), a 38.2.59 §1-§9, és a bináris: `pe_dis.cdis` (gépi kód), az index `functions`, `xrefs` és `rtti` táblája. Kódot nem módosítottunk, a CI-őrök nem futottak (nincs kódváltozás). Ideiglenes fájl nem keletkezett: a vizsgálat `python -c` hívásokkal futott.

**Válasz röviden.**

1. **Q1, a hívók ESI-je.** A `0x004fbb30`-at kilenc hívóhelyről hívják, hét függvényből. A kilenc helyen az ESI belső forrása (regiszter vagy verem-argumentum) megvan. Az objektum a `0x004ebff0` `this`-ére (R) vezethető vissza a `0x004e9400`-ból induló láncon (T = R). A `0x004f9450` és a `0x004fb9c0` hívóhelyeinek objektuma NINCS MEG, mert a hívóikat nem követtük vissza (§1). A 38.2.59 három állapotmezője (`pcStack_1844`, `cStack_158c`, `cStack_1586`) NEM a `0x004fbb30` mezői: ezek a `0x00425f60` veremében vannak. A `0x004fbb30` saját mezői a `+0x4dd` (indító jelző), a `+0x4de` (kész jelző) és a `+0x488` (darabszám).
2. **Q2, a `0x00411cf0`.** Zárat vesz az EAX-ban kapott objektumon, kiüríti a pufferét, majd elengedi a zárat. Az állapotjelzőkkel (`+0x4dd`, `+0x4de`) nincs köze (§2).
3. **Q3, döntés: az U53 LEZÁRVA, „a binárisból statikusan nem dönthető el”.** A három állapotmező forrása nincs meg (§3, §4). A `pcStack_1844` írója megvan, de az értéke ágtól függ. A `cStack_158c` és a `cStack_1586` írója nincs meg. A felhasználói hatás ezért nincs leírva; a §4 mondja meg, milyen élő felvétel döntené el.
4. **Q4, a nyitott lista.** Az U53 RÉSZBEN-ből LEZÁRVA lett. Új Ghidra-cím nincs, mert a forrás nincs meg (§6, §9).

##### §1 Q1: a `0x004fbb30` kilenc hívóhelye és az ESI

A kilenc hívóhely hét függvényben van. A `0x004fbb30` a hívás elején ellenőrzi a `+0x4dd` jelzőt: ha nulla, azonnal visszatér. Ha nem nulla, a tételek vtábla +8 metódusát hívja, majd a `+0x4de` jelzőt 1-re, a `+0x4dd` jelzőt 0-ra állítja, és meghívja a `0x00411cf0`-at.

| hívóhely | hívó függvény | az ESI a hívásnál | honnan jön | objektum |
|---|---|---|---|---|
| `0x004e93dc` | `0x004e91f0` | a belépéskori EAX (`0x004e91f8`: `mov esi, eax`; az ESI később nem íródik) | a `0x004e9400` adja: a `0x004e9442` és a `0x004e9970` előtt EAX = EDI | T |
| `0x004e9433` | `0x004e9400` | EDI (`0x004e942a`: `mov esi, edi`) | az EDI a belépéskori EAX (`0x004e9409`: `mov edi, eax`) | T |
| `0x004e9762` | `0x004e9400` | EDI (`0x004e9760`: `mov esi, edi`) | ugyanaz | T |
| `0x004e994b` | `0x004e9400` | EDI (`0x004e9949`: `mov esi, edi`) | ugyanaz | T |
| `0x004ebce8` | `0x004ea360` | EBX (`0x004ebce6`: `mov esi, ebx`). Az EBX a `0x004ebc77`-ben töltődik újra a `[esp+0x24]` helyről, ahová a belépéskor az 1. verem-argumentum került (`0x004ea38a`) | a `0x004e9400` tolja: `push edi` (`0x004e9674`), tehát az 1. argumentum T | T |
| `0x004ec04f` | `0x004ebff0` | ECX a belépéskor (`0x004ec011`: `mov esi, ecx`) | a gyökér: az indexben nincs közvetlen hívója | R |
| `0x004f8ead` | `0x004f8ae0` | EBP (`0x004f8ea4`: `mov esi, ebp`). Az EBP az 1. verem-argumentum (`0x004f8b2d`) | a `0x004e80d0`-ból (`push ebp`), ahol az EBP a `0x004e80d0` 1. argumentuma, és a `0x004e9400` ezt `push edi`-vel adja (EDI = T). A `0x004f8ef0`-ból (`push edi`), ahol az EDI a belépéskori EAX, és a `0x004e91f0` és a `0x004e9400` ezt T-vel hívja | T a `0x004e91f0` és a `0x004e9400` láncán |
| `0x004f97a7` | `0x004f9450` | EBX (`0x004f979e`: `mov esi, ebx`). Az EBX az 1. verem-argumentum (`0x004f9454`) | NINCS MEG: a hívók argumentuma nincs visszakövetve | NINCS MEG |
| `0x004fbace` | `0x004fb9c0` | EDI (`0x004fbac5`: `mov esi, edi`). Az EDI a belépéskori EAX (`0x004fb9c5`) | NINCS MEG: az index a `0x005cf5b0`-t adja hívónak, a hívóhelyét nem néztük meg | NINCS MEG |

- **A T és az R ugyanaz az objektum.** A `0x004ebff0` a `0x004ec573`-ban `mov eax, esi` után hívja a `0x004e9400`-at, és az ESI itt R (a `0x004ebff0` `this`-e). Tehát a `0x004e9400` `this`-e (T) R. A `0x004e9400`-ból induló hívások (`0x004e91f0`, `0x004ea360`, `0x004e80d0`, `0x004f8ef0`) T-t adnak tovább.
- **R osztálya.** A `0x004ebff0` az RTTI-tábla szerint a `ytDirScanner::vftable` (VA `0x00c86be0`) 2. slotja, és a `ytDirScannerWindows::vftable` (VA `0x00ca81f8`) 2. slotja is. Tehát R egy könyvtár-letapogató példány (ytDirScanner, vagy annak Windows-leszármazottja). A `0x004f8ae0` is könyvtárakat jár be: meghajtó-betűből épít útvonalat, és `GetDriveTypeA`-t hív.
- **Az A = R kérdés.** A `0x00425f60` az A = P+0xf8 objektumot adja a `0x004eec80`-nak (38.2.59 §1). Az A és a letapogató-lánc is a `+0x3f0` és `+0x3f8` tételtömböt használja. Mindkét lánc a `+0x4dd` jelzőt használja: a `0x004eec80` A+0x4dd-et állít, a `0x004fbb30` R+0x4dd-et olvas. Hogy A és R ugyanaz a példány, NINCS MEG.

##### §2 Q2: a `0x00411cf0`

- **Mit csinál.** Az EAX-ban kapott objektumot (O) veszi (`0x00411cf0`-`0x00411d9b`):
  1. Zárat vesz a tulajdonos szálon. A `GetCurrentThreadId` eredményét az O+0x20 mezővel veti össze, a számlálót az O+0x24 tartja. Ha a zár nincs ennél a szálnál, az O+0xc bájt szerint kritikus szakaszt (O+0x28) vagy a vtábla +0x18 hívását használja.
  2. Ha O+0x470 nem nulla, a `0x0097caf0`-nak adja át. Ez felszabadítás jellegű hívás; a törzsét nem néztük meg.
  3. Az O+0x474 mező csak a 0. bitjét tartja meg. Az O+0x470 és az O+0x478 nulla lesz.
  4. Elengedi a zárat. Rekurziónál csak a számlálót csökkenti. Egyébként O+0x20 = 0, és a kritikus szakaszt vagy a vtábla +0x1c hívását használja.
- **Hol hívják.** Négy hívóhely van az index szerint: `0x004fbb80` (a `0x004fbb30` végén), `0x00412403` (a `0x00412400`-ban), `0x0046e056` (a `0x0046d7d0`-ban), `0x004fdc16` (a `0x004fd1c0`-ban). A `0x004fbb80`-nál EAX = ESI = O (`0x004fbb70`: `mov eax, esi`), tehát a `0x004fbb30` objektuma.
- **Kapcsolat az állapotmezőkkel: nincs.** A `0x00411cf0` az O+0x20, O+0x24, O+0xc, O+0x28, O+0x470, O+0x474 és O+0x478 mezőket írja vagy olvassa. A `+0x4dd` és a `+0x4de` jelzőket nem. A `0x004fbb30` ezeket a hívás előtt állítja be (`+0x4de = 1`, `+0x4dd = 0`), és a `0x00411cf0` nem írja felül őket. A 38.2.59 három állapotmezőjéhez semmi köze nincs.
- **Ugyanaz a zárszerkezet.** A `0x004f8ae0` saját zárkódja ugyanezeket a mezőket használja (O+0x20, O+0x24, O+0xc, O+0x28). A két függvény tehát ugyanarra a zárszerkezetre épül. Ez nem bizonyítja, hogy ugyanaz az osztály.

##### §3 Q1 folytatása: a három állapotmező forrása (38.2.59 §4)

A három állapotmező a `0x00425f60` veremében van. A `0x004fbb30` nem olvassa őket.

| mező | verem-hely (`0x00425f60`) | közvetlen írók | olvasók | forrás |
|---|---|---|---|---|
| `pcStack_1844` | `[esp+0x3c]` | `0x004264b6` (`mov [esp+0x3c], eax`, a `0x005b1570` hívása után); `0x0042693a` (`mov [esp+0x3c], edx`); `0x00426e12` (`mov [esp+0x3c], eax`); `0x00426e62`: `lea edx, [esp+0x3c]`, mutatóként átadva a `0x004d8da0`-nak (írja-e, nincs megnézve) | legalább nyolc hely, például `0x00426497`, `0x0042656d`, `0x004265db`, `0x004269a4` | RÉSZBEN. A `0x004264b6` írás mért: a `0x005b1570` EAX-e. Ez ágtól függően tér vissza: `0xf4242`, a `0x005acf40` állapotkódja (`local_a4c`), a `0x005b1460` visszatérése (nincs mérve), `2`, vagy `0`. A három másik író értéke NINCS MEG. |
| `cStack_158c` | `[esp+0x2f4]` | nincs közvetlen író | `0x00426647` (`cmp byte ptr [esp+0x2f4], al`) | NINCS MEG |
| `cStack_1586` | `[esp+0x2fa]` | nincs közvetlen író | `0x004265d1` (`cmp byte ptr [esp+0x2fa], 0`) | NINCS MEG |

- **A két bájt környéke.** A `0x004264aa`-ben `lea ecx, [esp+0x200]` adja a `0x005b1570` `this`-ét. Ez a `0x00425f60` törzsében a `+0x1f8` offsetű objektum. Ebben a `cStack_158c` a `+0xfc`, a `cStack_1586` a `+0x102` bájt. A `0x005b1570` törzse (`mov ebx, ecx` a `0x005b15b4`-ben, tehát a `this` EBX-ben) az `[ebx+0xfd]` és az `[ebx+0x101]` bájtot olvassa. A `+0xfc` és a `+0x102` nem szerepel a `0x005b1570` olvasásai között. A `0x00425f60` a hívás előtt az `[esp+0x2f5]` és az `[esp+0x2f6]` bájtot írja (`0x00426383`, `0x004263a8`, `0x004263b2`, `0x004263d4`). Ezek a szomszédos mezők, nem a két állapotbájt.
- **A `0x004efa20` nem írja a két bájtot.** A `0x00426525`-`0x00426536` hívásban a `0x004efa20`-nak két verem-argumentum jut: az 1. `&[esp+0x2f0]` (a függvény csak a benne lévő mutatót olvassa), a 2. `&[esp+0x38]` (ide írja az `idx`-et: `mov [edx], eax`). A `0x004ed7d0`-t, amit a `0x004efa20` hív, nem néztük meg.
- **Állapot.** A `pcStack_1844` írója megvan, de az értéke nincs. A `cStack_158c` és a `cStack_1586` írója nincs megnevezve.

##### §4 Döntés: az U53 LEZÁRVA

A 38.2.59 §4 szerint az U53 akkor lezárandó, ha a három állapotmező forrása nincs meg. Nincs meg. Ezért az U53 lezárva: **a binárisból statikusan nem dönthető el.**

A `pcStack_1844` írója megvan (a `0x005b1570` EAX-e), de az értéke ágtól függ, és két ág (a `0x005acf40` állapotkódja és a `0x005b1460` visszatérése) nincs mérve. A `cStack_158c` és a `cStack_1586` írója nincs meg. A `0x004eec80` hívási feltételei (38.2.59 §1) mind a három állapotmezőre épülnek, ezért azok sem dönthetők el.

Ezért nincs „A felhasználó szemével” szakasz: a forrás nincs meg, a felhasználói hatás nem vezethető le.

**NINCS MEG (az U53 lezárásakor):**
- `pcStack_1844`: a `0x005acf40` állapotkódja (`local_a4c`), a `0x005b1460` visszatérése, és a három másik író értéke (`0x0042693a`, `0x00426e12`, és a `0x00426e62`-ben `lea`-val mutatóként átadott `0x004d8da0` hívás, ha ír rá).
- `cStack_158c` és `cStack_1586`: az írójuk. A `0x005b1570` `this`-ében a `+0xfc` és a `+0x102` mezők írói, és a `0x005b1570` hívott függvényei (`0x005acf40`, `0x005b1460`), ha `this`-en át írnak.
- Az `M+0x58` objektum vtábla +4 célja, és a `[esp+0xdc]`, `[esp+0xe0]`, `[esp+0x2b4]`, `[esp+0x2b8]` méret-mezők forrása.
- A `0x004fbb30` vtábla +8 célja (a tételek metódusa), és ennek a hatása.
- Az A (`P+0xf8`) és az R (a letapogató-példány) azonossága (§1).
- A `0x004ebff0` (R-et adó) hívója: az indexben nincs közvetlen hívó.

**Mi dönthetné el élőben.** A `+0x4dd` jelzőn átírt tételek (kód 4) látható hatását nem a belső mezők mutatják meg, hanem egy élő Picasa 3.9 példány. Ehhez egy mappa kell, amely kép, videó, hang, szöveges fájl és `.url` fájlt tartalmaz. Az Időrend nézetet először egy elemmel, majd legalább két, vegyes típusú elemmel kell megnyitni. Rögzítendő: az Időrend képernyőképe, a látható elemek száma és típusa, a mappa fájllistája, és az, hogy az elemek a nézetben megjelennek-e. Ezt két helyen lehet futtatni: a Colab-os Picasa-végrehajtón (`tipus:behavior`, csak a tulajdonos `jovahagyva` címkéjével), vagy a tulajdonos Windows-gépén. A Colab-útvonalat nem mértük, nem tudjuk, hogy a Wine alatti Picasa kirajzolja-e az Időrend nézetet, ezért a Windows-gép a biztosabb út.

##### §5 Bizonyítottsági fok (38.2.60)

| állítás | bizonyíték | fok |
|---|---|---|
| a `0x004fbb30`-at kilenc hívóhelyről, hét függvényből hívják | index `xrefs` és a dekompilátum hívólistája | megerősített |
| az ESI belső forrása a kilenc hívóhelyen | gépi kód: a belépési regiszter vagy az 1. verem-argumentum visszakövetése | megerősített |
| a `0x004e9400`-ból induló láncon az objektum T | gépi kód `0x004e9409`, `0x004e9674`, `0x004e9442`, `0x004e9970` | megerősített |
| a `0x004ebff0` `this`-e (R) a `0x004e9400` `this`-e (T) | gépi kód `0x004ec011`, `0x004ec571`-`0x004ec573` | megerősített |
| a `0x004ebff0` a `ytDirScanner` vtábla 2. slotja | RTTI-tábla (`rtti.csv`), a `0x00c86be0` és `0x00ca81f8` vtábla, a vtábla-scan két találata | megerősített |
| a `0x004ebff0`-nak nincs közvetlen hívója az indexben | index `xrefs` | megerősített (vtábla-hívás nincs kizárva) |
| a `0x00411cf0` zárat vesz, puffert ürít, elenged | gépi kód `0x00411cf0`-`0x00411d9b` | megerősített |
| a `0x00411cf0` nem írja a `+0x4dd` és `+0x4de` mezőt | gépi kód: az írt mezők listája | megerősített |
| a `0x005b1570` `this`-e a `[esp+0x200]`, azaz `+0x1f8` | gépi kód `0x004264aa`, `0x005b15b4` | megerősített |
| a `0x00425f60` három állapotmezőjének írói | a teljes `0x00425f60` közvetlen `[esp+X]` és `lea` szkennelése | részben (mutatón át íródás nincs zárva) |
| a `0x004efa20` nem írja a `cStack_158c`-t és a `cStack_1586`-ot | gépi kód `0x00426525`-`0x00426536` és a `0x004efa20` törzse | megerősített a közvetlen írásokra; a `0x004ed7d0` nincs megnézve |
| az A = R azonosság | nincs | NINCS MEG |
| a felhasználói hatás | nincs | NINCS MEG |

##### §6 Ghidra-címek a következő körhöz

Nincs új Ghidra-cím. A 38.2.59 §6 szerint Ghidra-címet csak akkor adunk, ha a forrás megvan és csak egy részlet hiányzik. Itt a forrás nincs meg, az U53 lezárva. A 38.2.59 §6 címeinek állapota:
- `0x004fbb30` hívói: LEZÁRVA (§1). Az ESI-források megvannak.
- `0x00411cf0`: LEZÁRVA (§2).
- `0x005b1570` (`local_a4c` és a `0x005b1460` ágak): NINCS MEG, nem kérjük, mert az U53 lezárva.
- `0x004fbb30` vtábla +8 célja: NINCS MEG, nem kérjük.
- `M+0x58` vtábla +4 célja: NINCS MEG, nem kérjük.

##### §7 Javítások a korábbi szakaszokban

- **38.2.59 §3 (a `0x00411cf0` „a célja NINCS MEG”).** ⚠️ LEZÁRVA (§2): zár, puffer ürítése, elengedés.
- **38.2.59 §6 (a `0x004fbb30` hívóinak esi-je, „az A-e?”).** ⚠️ LEZÁRVA (§1): az esi-értékek megvannak. Az A = R kérdés nincs igazolva.
- **38.2.59 §4 és §9 (a három állapotmező forrása NINCS MEG).** ⚠️ PONTOSÍTVA (§3): a `pcStack_1844`-nek négy írója van, a `0x005b1570` EAX-e az egyik. A `cStack_158c` és a `cStack_1586` közvetlen írója nincs a törzsekben.

##### §8 Amit KIZÁRTAM

- „A `0x004fbb30` olvassa a 38.2.59 három állapotmezőjét”: CÁFOLVA. A törzse csak a `+0x484`, `+0x488`, `+0x4dd` és `+0x4de` mezőt használja az `esi`-n.
- „A `0x00411cf0`-nak köze van a `+0x4dd` vagy `+0x4de` jelzőhöz”: CÁFOLVA (§2).
- „A `0x004efa20` írja a `cStack_158c`-t vagy a `cStack_1586`-ot”: CÁFOLVA a közvetlen írásokra (§3). A `0x004ed7d0`-t nem néztük meg.
- „A `0x004fbb30` esi-je A”: NEM IGAZOLT, és az A = R sem zárt ki.
- „A `0x004ebff0` nincs vtáblában”: CÁFOLVA, a `ytDirScanner` és a `ytDirScannerWindows` vtáblája is tartalmazza (§1).
- „A `0x004ea360` 1. argumentuma minden hívásban T”: csak a `0x004e9400`-ból induló hívásra igazoltuk.

##### §9 Nyitott lista (38.2.60 §9)

Nyitott kérdések mérlege (38.2.60): 54 tétel · 13 lezárva · 25 részben · 16 nincs meg. Az előző (38.2.59): 54 · 12 · 26 · 16. Változás: az U53 RÉSZBEN-ből LEZÁRVA lett. Az U49 szövege nem változott.

| U | állapot | mit mond most | cím |
|---|---|---|---|
| U53 | LEZÁRVA (38.2.60 §4): a binárisból statikusan nem dönthető el | a három állapotmező forrása nincs meg: a `pcStack_1844` írója megvan, de az értéke ágtól függ (a `0x005acf40` és a `0x005b1460` nincs mérve); a `cStack_158c` és a `cStack_1586` írója nincs meg. A `0x004fbb30` a `+0x4dd` jelzőn dolgozik a `0x004ebff0` (ytDirScanner) példányán; az A = R azonosság NINCS MEG. A felhasználói hatás NINCS MEG: élő felvétel kell (§4) | `0x005b1570`, `0x005acf40`, `0x005b1460`, `0x004ebff0`, `0x004fbb30` (vtábla +8) |

#### 38.2.61 A Ghidra-kimenet ellenőrzése és a kártyagörbe QEMU-mérése (#5401, 2026-10-22)

**Hatókör.** A `referencia/ghidra/2026-10-22-ghidra-sor-197-200.txt` `0x005e81e0` kimenetének ellenőrzése, valamint a qshow-kártyagörbe (`0x007fbab0`) számszerű futtatásos kontrollja. A mérő-archívumban nincs `timeline`, `idorend`, `qshow`, `job-102` vagy `job-217` tag; ebből nem következik, hogy ilyen mérés sehol nincs. A próba csak a Picasa 3.7 helyi `runtime/bezier.txt` fájlját és a `Picasa3.exe` függvényét használta. Az ideiglenes ELF a munkafa `.bt/` könyvtárában készült, majd a mérés után törölve lett. Terméki kód nem változott.

**1. A `0x005e81e0` nem az Időrend animátora - megerősített.**

- **A út - utasításszintű olvasás.** A függvény 802 bájt. A `0x005e82e2`-`0x005e82e7` a `0xc811d4` (`"]star"`) kulccsal hívja a `0x00475250`-et; a `0x005e83d8`-`0x005e83e9` a `stars/yes` (`0xc97860`) vagy `stars/no` (`0xc9786c`) erőforrást választja, majd a `0x00410fa0`-nak adja. A célfüggvény diszasszemblálása ezeket a címeket és ágakat közvetlenül igazolja.
- **B út - független Ghidra-kimenet és hívóellenőrzés.** A friss Ghidra-kimenet három közvetlen hívót sorol fel: `0x005d9cc0`, `0x005e60d0`, `0x00760240`. Az index `xrefs` táblája ugyanezt a hívófüggvény-készletet adja; a hívóhelyeket külön diszasszemblálás ellenőrizte: `0x005db0c5` a `thumbui/startoggle` ágban, `0x005e6587` a billentyűkezelő `push 2` ágában, `0x007606fd` pedig az `editoneup/star` ágban van. A Ghidra-kimenet és az utasításolvasat tehát egyezik: ez a függvény csillagállapotot kezel és csillagjelzőt készít.
- **Cáfoló kísérlet.** Megpróbáltam cáfolni azt a besorolást, hogy a `0x005e81e0` csillagjelző-függvény, és helyette az Időrend animátorának tekinteni. A közvetlen hívók három csillag-műveleti ág; a függvény saját kulcsa `]star`, a kirajzolt erőforrása `stars/yes` vagy `stars/no`. A cáfolat nem állt meg. Ez kizárja, hogy a `0x005e81e0` maga legyen a kártya-animátor vagy kártyaforrás; az Időrend magasabb szintű útjából való minden közvetett kapcsolatot nem minősíti.
- **Bizonyítottsági fok: megerősített** erre az egy besorolásra, mert a Ghidra dekompilációja és a független utasításszintű út/hívóellenőrzés egybeesik. A kimenet nem ad új választ az Időrend négy teljes kutatási pontjára.

**2. A `0x007fbab0` racionális köbös Bézier-görbéje - megerősített az itt mért bemenettel.**

Az `0x007fbd90` négy `"%f %f %f\n"` rekordot olvas a `runtime\bezier.txt` fájlból a `P+0x50..0x7c` mezőkbe (38.2.25 §2). A helyi Picasa 3.7 fájl első négy, aktív rekordja - az ezt követő `#` sorok nem kerülnek beolvasásra - pontosan:

| pont | x | y | súly | forrás |
|---|---:|---:|---:|---|
| P0 | -3 | -3 | 10 | mérés (a helyi `runtime/bezier.txt` pontos tartalma) |
| P1 | -1 | -0.5 | 4 | mérés (a helyi `runtime/bezier.txt` pontos tartalma) |
| P2 | -0.3 | 0.9 | 0.6 | mérés (a helyi `runtime/bezier.txt` pontos tartalma) |
| P3 | 0.9 | 0.75 | 1.1 | mérés (a helyi `runtime/bezier.txt` pontos tartalma) |

**A út - bináris.** A `0x007fbab0` diszasszemblye a négy pont x/y mezőiből Bernstein-számlálókat, a súlymezőkből nevezőt képez; a végső osztás és középre tolás az `0x007fbc6f`-`0x007fbcaf` tartományban történik. Képlete a 38.2.38 §3 szerint: `b0=(1-t)^3`, `b1=3(1-t)^2t`, `b2=3(1-t)t^2`, `b3=t^3`; `D=Σ bi·wi`; `x=(Σbi·xi-0.5)/D+0.5`, `y=(Σbi·yi-0.5)/D+0.5`, `z=1/D`. A kód a számlálóban nem szorozza az x/y koordinátákat a súlyokkal.

**B út - QEMU-futtatás az eredeti gépi kódon.** A `qemu-i386` alatt a `0x007fbab0` függvényt hívtam meg a fenti négy ponttal és `t` f32 bemenetekkel. A három f32 kimenet egyezik a képlet külön kiszámított eredményével az f32 kerekítés pontosságáig:

| t bemenet | kimenet (x, y, z; QEMU f32) | nyers kimeneti bájtok | forrás |
|---:|---|---|---|
| 0 | (0.150000006, 0.150000006, 0.100000001) | `9a99193e 9a99193e cdcccc3d` | mérés (`qemu-i386`, `0x007fbab0`) |
| 0.5 | (0.0983935595, 0.297188729, 0.321285158) | `9082c93d 1f29983e 7d7fa43e` | mérés (`qemu-i386`, `0x007fbab0`) |
| 1 | (0.863636315, 0.727272749, 0.909090877) | `45175d3f 8c2e3a3f 2eba683f` | mérés (`qemu-i386`, `0x007fbab0`) |

**Cáfoló kísérlet.** A szokásos racionális Bézier-alakból kiinduló, súlyozott `Σbi·wi·xi` / `Σbi·wi` számlálót ellenőriztem a `t=0.5` mintán. Az így kapott x/y nem egyezik a natív függvény QEMU-kimenetével; a súlyozatlan `Σbi·xi` / `Σbi·yi` számláló egyezik. Ez a cáfoló is teljesítette ugyanazt a mércét: a bemenet ugyanaz a négy pontos fájlsor, a döntő kimenet a bináris függvényé.

**Bizonyítottsági fok: megerősített** a `0x007fbab0` képletére és a táblázatban szereplő helyi vezérlőpontokra. Ez nem zárja le a teljes Időrend-mozgást: a kártyák forrása és sorrendje, a képkockánkénti helyzet/átlátszóság összekötése, a teljes időzítési görbe, a rétegsorrend és a háttér viselkedése továbbra is külön kérdés.

**Hatás a #5401 „Kész, ha” pontjaira:** (1) forráshalmaz és sorrend - nincs új lezárás; (2) mozgás - a kártyagörbe képlete és a helyi vezérlőpontok számszerű QEMU-kontrollja megvan, a teljes animáció nem; (3) vezérlők - ez a kör nem zárta a `timelinedot`, dátumcsúszka, automatikus léptetés és billentyűk teljes működését; (4) diavetítésbe lépés és visszatérés - ez a kör nem zárta le.

#### 38.2.62 Az Időrend véletlen eltolásának helyesbítése és a képkocka-transzformáció QEMU-mérése (#5401, 2026-10-22)

**Hatókör és módszer.** A `0x00802230` véletlen eltolásának és előzőérték-másolásának, továbbá a `0x007fff30` képkocka-transzformációjának és alfa-kimenetének vizsgálata. Az utasításokat a helyi `Picasa3.exe`-ből olvastam; a struktúratag-találatokat a teljes `.text`-en a kötelező `paszta.memoria_kapu()` után futó `paszta.py`-pásztázás adta. Mindkét függvényt az eredeti gépi kódon futtattam `qemu-i386` alatt. A próbák kézzel felépített `this`-állapotot és vezérelt `rand()`-visszatérést használtak; a nem célzott segédfüggvényekhez a QEMU-harness stubbokat adott. Ez nem qshow-felvétel, és nem igazolja a normál futás teljes objektumforrását. Az ideiglenes fájlok a munkafa `.bt/` könyvtárában készültek.

##### §1 A `0x00802230` véletlen eltolása pozitív

**A út - bináris utasítások.** A függvény két `rand()`-hívása `0x008022db` és `0x008022f2`; a második visszatérését a `0x008022f7`-`0x008022ff`, az elsőét a `0x008022e0`-`0x008022eb` bitművelete alakítja float-bitté. Az `(r + 0x3f8000) << 8` eredménye `0x3f800000 + r·256`, amely floatként `1 + r/32768`, pontosan ábrázolható. A `0x00802306`-tól az x-ág ezt 1-ből kivonja; a `0x00802353`-tól a y-ág ugyanezt teszi. A méretelőjel-korrekció az x-ágban `0x00802332`-`0x0080233b`, a y-ágban `0x00802376`-`0x0080237f`; az új `[this+0x400]`/`[this+0x404]` mezőbe írás a `0x00802391`/`0x008023a1` címeken történik. Az előző értékek másolása `0x008022c3`-`0x008022d5`.

Legyen `c = 0,1499999761581421` (f64, `0x00cf4320`), `W = [this+0x474]`, `H = [this+0x478]`, és `W'`, illetve `H'` az adott 32 bites méret, negatív előjelnél `2^32` hozzáadásával (`0x00cf39e4`, `0x00cf3ac0`). `r1` az első, `r2` a második `rand()`-érték:

- `x = fl32(c · W' · r2 / 32768)`;
- `y = fl32(c · 0,5 · H' · r1 / 32768)` (`0,5`: f64 `0x00c72150`).

Nemnegatív méretek és 0…32767 közötti `rand()`-érték mellett `0 ≤ x < c·W` és `0 ≤ y < 0,5·c·H`. A `0,5` és `c` szorzó, a méretelőjel-korrekció és a tárolási címek közvetlenül a bináris utasításaiból olvashatók. Hogy W és H képméret vagy kártyaméret, ebből nem következik.

**B út - QEMU az eredeti `0x00802230` gépi kódján.** `W=640`, `H=480`, előző eltolás `(0,25; -0,125)` mellett a `rand()`-ot a felsorolt értékekre vezéreltem. A függvény két hívást végzett; az új mezők és az elmentett előző értékek:

| `r1` (y), `r2` (x) | új `(x,y)` a binárisban | előző érték utána | forrás |
|---:|---:|---:|---|
| 0, 0 | (0; 0) | (0,25; -0,125) | mérés (`qemu-i386`, `0x00802230`) |
| 32767, 32767 | (95,9970550537; 35,9988975525) | (0,25; -0,125) | mérés (`qemu-i386`, `0x00802230`) |
| 16384, 32767 | (95,9970550537; 17,9999961853) | (0,25; -0,125) | mérés (`qemu-i386`, `0x00802230`) |

**A két út és a cáfoló próba.** Az utasításszintű bitminta-levezetés pozitív `r/32768` szorzót ad; ettől függetlenül a QEMU az eredeti függvényben, rögzített bemenetekkel pozitív `(95,9970550537; 35,9988975525)` eltolást mért a maximális `rand()`-értéknél. A régi `u-1` képlet ezt negatív előjelűnek jósolná, ezért a próba megcáfolja a 38.2.34 korábbi előjelét. A QEMU a célfüggvény eredeti bájtjait futtatta; a `rand()` bemenetet és a méretmezőket rögzítettem, majd a visszatérő mezőket olvastam ki. A próba nem általánosítható a teljes qshow-futásra vagy a véletlen seedre.

##### §2 A `0x007fff30` transzformációi és alfája

**A út - bináris utasítások és mezőpásztázás.** A teljes `.text`-pásztázás a `0x00802230` írásait mutatja: a jelenlegi eltolás a `[this+0x400]`/`[this+0x404]`, az előző a `[this+0x408]`/`[this+0x40c]` mező. A `0x007fff30` közvetlenül mind a négyet olvassa (`0x007fffeb`, `0x007fffff`, `0x00800023`, `0x00800038`). A konstansok a `0x00cf4848` (f64 `1,1`), `0x00cf4850` (f64 `0,17647055523618382`), `0x00cf39f8` (`3`), `0x00c7d9d0` (`2`) és `0x00c72150` (`0,5`) címeken vannak. A `0x00800095` és `0x008000d7` tíz dword-ot másol a transzformációs rekordokba (`this+0x4e4`, illetve `this+0x4bc`); a további mezőírások a léptéket és eltolást tárolják. A `this+0x3f4 == 0` ágon (`0x0080015d`-`0x00800199`) a `this+0x4bc` rekord identitásmátrixra áll.

`0 ≤ t ≤ 1` esetén, a normál `SimpleSlideshow == 0` rajzolási ágban, az utasítássor a következő leképezéseket valósítja meg (az x87-köztes műveletek és a f32 mezőírás kerekítése a bináris számítás része):

- `g(v) = 1 / (1,1 + 0,17647055523618382 · v³ / 8)`;
- `p_c(t) = t² · (3 - t) / 4`, `p_p(t) = 1 - ((1 - t)² · (1 + t/2)) / 2`;
- `this+0x4e4` (jelenlegi eltolás): skála `g(t)`, `tx = 1 + p_c(t)·[this+0x400]`, `ty = 1 + p_c(t)·[this+0x404]`;
- `this+0x4bc` (előző eltolás): skála `g(t+1)`, `tx = 1 + p_p(t)·[this+0x408]`, `ty = 1 + p_p(t)·[this+0x40c]`; ha `[this+0x3f4] == 0`, ezt a rekordot a függvény identitásra cseréli.

Mindkét rekord 2D, tengelypárhuzamos affin mátrix: a két átlóelem azonos skála, a forgatási/keresztirányú elemek 0, a homogén jobb alsó elem 1. Ez a helper kimenete; a tömbök képforrása és a két transzformáció vásznon látható szerepe ettől még nincs azonosítva.

**A két bemenet kapcsolása (`0x008001c0` → `0x00aa6180`, diszasszembly).** A hívó a `this+0x444` és `this+0x4bc` párt, majd a `this+0x46c` és `this+0x4e4` párt adja át (`0x008001c0`, 38.2.30 §1). A `0x00aa6180` első párját a `0x00aa5fb0`-nak adja; ha az alfa nem nulla, ugyanígy előállítja a második párt is, majd a két köztes képpufferrel és az alfával a `0x009dc040`-et hívja (`0x00aa61fd`-`0x00aa6245`). Alfa nulla esetén a második pár és ez a kétpufferes ág kimarad. Ezzel a descriptor-transzformáció párosítás és az alfa szerinti kétbemenetű út megvan; hogy a descriptorok milyen képeket tartalmaznak és a vásznon melyik rétegként jelennek meg, **NINCS MEG**.

Az alfa-kimeneti mutatót a `0x00800057` nullázza. A `0x00800110`-`0x00800153` a `0xcf4840` f32 küszöböt (`0,6800000071525574`) vizsgálja, majd a `0xcf39d8` f64 `256`-tal szoroz, a `0xcf4830` f64 `0,3199999928474426`-tal oszt, és a `0xc00` kerekítési módot állítja a `fistp` művelethez. A helper kimenete: ha `t > 0,6800000071525574`, `trunc_toward_zero(256·(t-0,6800000071525574)/0,3199999928474426)`, különben 0. A helper nem vágja 256-ra az értéket; a `0x008001c0` egyszerű ágában a hívó `t` értéke legfeljebb 1 (`SimpleSlideshow == 0`, 38.2.30 §1).

**B út - QEMU az eredeti `0x007fff30` gépi kódján.** A kézzel beállított `this`-állapotban a jelenlegi eltolás `(0,25; -0,125)`, az előző `(-0,5; 0,25)` volt. A táblázat a kimeneti rekordok `(skála; tx; ty)` mezőit adja. Az `index=0` az identitáságat aktiválja az előző rekordhoz; `index=1` meghagyja az előző eltolás transzformációját.

| `t` | index | `this+0x4bc` előző rekord | `this+0x4e4` jelenlegi rekord | alfa | forrás |
|---:|---:|---|---|---:|---|
| 0 | 0 | (1; 0; 0) | (0,909090877; 1; 1) | 0 | mérés (`qemu-i386`, `0x007fff30`) |
| 0 | 1 | (0,891218841; 0,75; 1,125) | (0,909090877; 1; 1) | 0 | mérés (`qemu-i386`, `0x007fff30`) |
| 0,5 | 0 | (1; 0; 0) | (0,906817794; 1,0390625; 0,98046875) | 0 | mérés (`qemu-i386`, `0x007fff30`) |
| 0,5 | 1 | (0,851463497; 0,578125; 1,2109375) | (0,906817794; 1,0390625; 0,98046875) | 0 | mérés (`qemu-i386`, `0x007fff30`) |
| 0,75 | 1 | (0,820868850; 0,521484375; 1,23925781) | (0,901464462; 1,07910156; 0,960449219) | 55 | mérés (`qemu-i386`, `0x007fff30`) |
| 1 | 1 | (0,783410192; 0,5; 1,25) | (0,891218841; 1,125; 0,9375) | 256 | mérés (`qemu-i386`, `0x007fff30`) |
| 1,1 | 1 | - | - | 336 | mérés (`qemu-i386`, `0x007fff30`) |

Az alfa-határ körüli további QEMU-próbák: `t=0,6799999475`, `0,6800000072` és `0,6800000668` mind 0-t adott; `t=0,68359375` 2-t, `0,9999999404` 255-öt. Az 1,1-es bemenet nem normál hívóoldali tartomány, csak azt mutatja, hogy a helper maga nem korlátozza az alfát.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a `+0x4bc` rekord az előző, a `+0x4e4` pedig a jelenlegi eltolást használja. `t=0,5`-nél külön-külön nulláztam az előző és a jelenlegi eltolást: az előző nulla kizárólag a `+0x4bc` transzlációját vitte `(1,1)`-re, a jelenlegi nulla kizárólag a `+0x4e4` transzlációját. A próba nem cáfolta a mező-hozzárendelést. Az eredeti bináris függvény azonos bemeneti állapota mellett csak az egyik eltolást változtattam, majd a kimeneti rekordokat olvastam ki.

**Bizonyítottsági fok és határ.** A `0x00802230` eltolásképlete és előzőérték-másolása, továbbá a `0x007fff30` két transzformációjának mező-hozzárendelése és alfa-leképezése itt **megerősített**: az utasításszintű út és az eredeti gépi kód vezérelt QEMU-kimenete egyezik; a régi negatív előjel ellen külön cáfoló próba futott. Ez nem azonosítja a képlánc forrását és sorrendjét, a két transzformáció képforrását/vizuális sorrendjét, a kártya- és háttérrajzolást, az összes `SimpleSlideshow` ágat, a csúszkát vagy a diavetítésből visszatérő állapotot. A #5401 teljes státusza továbbra is **nyitott**.

**A #5401 „Kész, ha” pontjai.** (1) Képlánc, forráshalmaz, rendezés és gyűjteményenkénti elemszám: ⛔ a lista mezői megvannak, a provider/kollekció és sorrend nem (`0x004039f0`, `0x008018a0`). (2) Átmenet pálya, képméret, forgatás, alfa, időzítés és háttér/kártyarajz: ⛔ a véletlen eltolás, a helper két affin kimenete és a helper alfa-képlete megerősített, de a képforrások, vizuális összekötés, teljes időgörbe és rajzolási rétegek nyitottak; qshow-képkocka-felvétel nem készült. (3) Vezérlők, dátumcsúszka, automatikus lépés, szóköz és nyilak: ⛔ a teljes működés továbbra sincs meg. (4) Diavetítésbe lépés és a pontos visszatérési kép/gyűjtemény: ⛔ nyitott.

**Nyitott.**

- `Ghidra-kör kell: 0x004039f0 - a CThumbUI konstruktor +0x2bc szolgáltatójának konkrét osztálya, forráskollekciója és upstream sorrendje [blokkoló]`
- `Ghidra-kör kell: 0x008018a0 - a [this+0x3ec] lista forrása, rendezési mezője és gyűjteményenkénti elemlistája [blokkoló]`
- `Ghidra-kör kell: 0x00aa6180 - a 0x009dc040 alfa-keverő hívás pontos képpuffer- és rétegszemantikája [blokkoló]`
- `Ghidra-kör kell: 0x00aa5fb0 - a this+0x444 és this+0x46c descriptorok képi forrása és a kártya/háttér tartalma [blokkoló]`
- `Ghidra-kör kell: 0x00a52890 - a timelinedot, sliderthumb, startbutton, exit és listaikon teljes eseményútja, a csúszka leképezésével [blokkoló]`
- `Ghidra-kör kell: 0x005e60d0 - a szóköz, nyíl, Home/End és Escape qshow alatti billentyűútja [blokkoló]`
- A Space/Auto Play statikus, állapotfüggő módváltási útját a 38.2.64 és a 38.2.65 bontja ki; a futásidejű előfeltétel és a visszatérő gyűjtemény/képpozíció mérésként nyitott.
- `Ghidra-kör kell: 0x008032e0 - az Exit célja és a visszatérő gyűjtemény/képpozíció [blokkoló]`

**Új kutatási jegyjavaslat.** Nincs; a nyitva maradt kérdések a #5401 elfogadási pontjaihoz tartoznak, nem külön feladatok.

#### 38.2.63 A qshow billentyűútja, a listaépítés és a csúszka indexleképezése (#5401, 2026-10-22)

**Hatókör és módszer.** A nyolc, a 38.2.62 végén felsorolt cím Ghidra-kimenete elkészült (belső Ghidra-referencia, 2026-10-22, sor 202-209). A döntő ágakat külön, függvényenkénti `annot_disasm.py` diszasszemblálás ellenőrizte az eredeti `Picasa3.exe`-ből. A `CThumbUI+0x2c0` és a qshow `+0x388` mező közvetlen íróit célzott, darabolt `paszta.py` `.text`-pásztázás kereste; a `paszta.memoria_kapu()` a pásztázás előtt lefutott. A mérőadat-archívumban nem volt Időrend/qshow-felvételhez tartozó tag, ezért ebben a körben futás közbeni képkockafelvétel és QEMU-mérés nem készült. A régi Ghidra-kéréslista aktuális állapota: a célfüggvények dekompilálása elkészült; a maradék kérdések e szakasz Nyitott listájában vannak.

##### §1 A képlánc bemenetének egy része és a sorrend

**A út - utasítások és adatfolyam.** A `0x004039f0` `0x3710` bájtos `CThumbUI`-objektumot foglal, majd a `0x005643e0` konstruktornak a hívó `[X+0x1030]` és `[X+0x1038]` mezőjét adja át (`0x00403d9e`-`0x00403db8`; Ghidra-kimenet: `2026-10-22-ghidra-sor-202-209.txt`, `0x004039f0`). A konstruktor a `[this]` mezőbe a `0x00c9052c` `CThumbUI::vftable`-t, továbbá a `+0x2bc`, `+0x2c0` és `+0x2c4` mezőbe kapott értékeket írja (`0x00564507`, `0x005644fa`, `0x00564616`, `0x0056461c`). A külön `[X+0x1034]` mezőt a `0x00402f90` a `0x00415790` eredményével tölti (`0x00402fd3`-`0x00402fdc`); ez nem a `0x004039f0` konstruktorának átadott két mező egyike.

**B út - független RTTI/vtable-ellenőrzés.** Az index `rtti` táblája a `0x00c9052c` címet `CThumbUI::vftable`-ként, a `0x00c81f78` címet `CThumbDB::vftable`-ként azonosítja. Ettől független gépikód-út, hogy a `0x00415790` konstruktor a `[this]` mezőbe a `0x00c81f78` vtable-címet írja (`0x004157fd`), a `0x00562cc0` thunk pedig a `CThumbUI+0x2bc` objektum vtable `+0x20` helyére továbbít. Ezek együtt azonosítják a `+0x2bc` szolgáltató osztályát `CThumbDB`-ként; ez az objektum nem azonos a qshow `+0x2c0` bemeneti mezőjével.

A qshow bemeneti lánca külön követhető. A `0x005e8a70` a `0x005e96d9` címen a `CThumbUI+0x2c0` értékét az átadott paraméterrekord `+0x14` mezőjébe írja; a `0x008037e0` ezt a rekordot továbbadja a `0x007fa7f0` oneup-konstruktornak, amely a paraméter `+0x14` mezőjét a saját `+0x2f4` mezőjébe másolja (`0x007fa83b`-`0x007fa83e`). A `0x008018a0` ezt a `[this+0x2f4]` bemenetet adja át a `0x004b0190`-nek. **Független út:** a `0x005e9434` ugyanezt a `CThumbUI+0x2c0` mezőt adja át a `0x004a0980` elemszám-kérőnek; a `0x005e9490` indexhurok ezután a `CThumbUI` vtable `+0x90` metódusát hívja, a `0x00562cc0` thunk pedig a külön `CThumbUI+0x2bc` `CThumbDB` objektum vtable `+0x20` helyére továbbít. Az első, közvetlen descriptor-átadási lánc egy útból ismert (**feltételes**); a második, ettől külön count/index út megerősíti, hogy a `+0x2c0` mezőt ugyanebben a MakeTimeline ágban is használják. Ez nem bizonyítja, hogy a count/index hurok kimenete azonos a qshow descriptor-listájával. A `+0x2c0` mögötti kollekció típusa, album-/mappa-tagsága és elemlistája nincs meg.

**Pontosítás a 38.2.6/38.2.8 korábbi olvasatához.** A `0x005e96eb` külön a `[CThumbUI+0xeac]` értékét tölti a hívó paraméterrekord `+4` mezőjébe (`0x005e96fc`-`0x005e9709`). A oneup-konstruktor ezt a másik argumentumot a `0x007fb9f0`-nek adja át, amely a `[oneup+0x2f8]+4`, vagyis `oneup+0x2fc` mezőbe másolja (`0x007fa844`-`0x007fa850`, `0x007fb9f3`). Ez külön adat a közvetlen descriptor-bemenettől (`CThumbUI+0x2c0` → `oneup+0x2f4`); önmagában nem bizonyítja, hogy szűrő, és a régi `[this+0xeac]` köztes lista qshow-descriptorral való kapcsolata nincs meg.

A `0x008018a0` a `0x004b0190` által kapott descriptor elemszámát `[descriptor+4] >> 1` alakban olvassa, majd a descriptor 0-tól növelt indexével járja be. A bejárás a `+0x3ec` tömbbe fűzi az elfogadott pointereket, és a jelző alapján kizárt elemeket kihagyja (`0x00801964`-`0x00801bd5`). Ebben az építőhurokban nem látható komparátorhívás: az átadott descriptor sorrendjét követi. A `0x004b0190`-et kiszolgáló objektum osztálya és a descriptor upstream rendezése nincs meg; a gyűjteményenkénti elemszám és képlista sem következik ebből.

##### §2 A qshow billentyűi és az automatikus lejátszás hívásútja

A `0x008037e0` állítja elő a qshow `QDrawable` objektumát, és a `0x007fa7f0`-nel hozza létre az oneup-objektumot. A `0x007fa7f0` a `0x00cbd66c` (`QDrawable::vftable`) vtable-t állítja be; ennek indexelt metóduslistájában a `+0x30` slot címe `0x00801270`. Ez és a közvetlen utasításolvasás egymástól függetlenül köti a `0x00801270`-et a qshow billentyűkezelőjéhez.

A `0x00801270` csak `WM_KEYDOWN` (`0x100`) üzenetet dolgoz fel; a nulla és `WM_CHAR` (`0x102`) üzenet visszatér. A billentyűágak:

| Billentyű | Bináris hívásút | Pontos határ |
|---|---|---|
| Escape (`0x1b`) | `0x00801270` → `0x007fb820` | A jelenlegi objektum vtable `+0x24` getterét hívja; a qshow-építő által beállított cél a `qshow` nevű `ytWindow` gazdaablak (`0x00982bf0`, vtable `0x00cd87fc`), ennek `+0x14` slotja `0x00983270`, amelyet `(0,0)` argumentummal hív (`0x007fb998`-`0x007fb9df`). A gazdaablak-metódus végső navigációs hatása és a visszaállított nézet/pozíció nyitott. |
| Bal (`0x25`) / fel (`0x26`) | `0x00801270` → belső ág `0x008014bc` → `0x008011b0` | Timeline módban a `0x007fd0c0`-t hívja a `[this+0x2f8]+0x30` értékével és a bináris `0x00cf3a48` címen tárolt `2.0f` értékkel. Ez az argumentumirány; a látható képek térbeli iránya a `0x007fd0c0` teljes állapota nélkül nincs meg. Timeline módon kívül, ha `[this+0x3bb] != 0`, a `0x00802980` előző-eleme út fut; egyébként a `0x00802ae0` hívódik. |
| Jobb (`0x27`) / le (`0x28`) | `0x00801270` → belső ág `0x008014ac` → `0x00801210` | Timeline módban a `0x007fd0c0` hívás ugyanazt a mezőt adja át, de `-2.0f` argumentummal. Timeline módon kívül, ha `[this+0x3bb] != 0`, a `0x008029f0` következő-eleme út fut; egyébként a `0x00802a90` hívódik. |
| Szóköz (`0x20`) | Ha `[this+0x3bb] != 0`, a `0x00803110` hívódik `[this+0x2dc]` argumentummal; ha nulla, a `0x00801130` hívódik. A külön Ctrl-ág `[this+0x3ba]=1`-et ír és `0xf4240`-t ad vissza. | A módváltás állapotfüggő: a `+0x3bb != 0` ág a 0-s diavetítési módba állít; a nulla ág csak a `+0x3bb` állapotkezelőjét hívja. Részletek és a két bináris út: 38.2.65. A visszatérési nézet és index nyitott. |

A handler további ágakat is tartalmaz a `0`-`9` és a Ctrl+`F`/`B`/`O` billentyűkre; ezek pontos felhasználói jelentése ebben a körben nincs feltárva. Home/End (`0x23`/`0x24`) explicit ága nincs.

A `0x008032e0` név szerinti eseménykezelőjében a `oneup/auto` és `oneup/auto2` a `0x00803110`-et hívja; a `oneup/timeline` a `0x00802be0`-t, majd a `0x007fda00`-t. A `oneup/exit` a tulajdonos vtable-jának `+0x24` függvényétől kért objektum vtable-jának `+0x14` függvényét hívja két nulla argumentummal. A `0x008037e0` a `0x00982bf0`-gel létrehozott `qshow` gazdaablakot (RTTI-adatszimbólum: `ytWindow::vftable`, `0x00cd87fc`) a oneup `+0x50` mezőjébe állítja (`0x00803977`-`0x0080397f`, setter: `0x007fa480`); a `ytWindow` vtable `+0x14` slotja a `0x00983270`. Az Escape `0x007fb820` és a gomb Exit útja így ehhez a gazdaablak-metódushoz jut `(0,0)` argumentummal (`0x007fb998`-`0x007fb9df`, `0x0080355d`-`0x00803573`). A visszatérő objektum azonosított, de a gazdaablak-metódus végső navigációs hatása és a folytatási nézet/pozíció nyitott. Az `overlays/startbutton` név azonossága a `oneup/auto` eseménnyel nincs bizonyítva. A `0x007fb210` az `overlays/timeline`, `overlays/timelinedot` és `overlays/sliderthumb` elemeket kéri le; ez az elemneveket és létrehozásukat igazolja.

A qshow egérkezelője a `0x007fde80`. Timeline módban bal gomb lenyomásakor (`WM_LBUTTONDOWN=0x201`) a vezérlő téglalapjai alapján állítja a `[this+0x429]` húzásjelzőt vagy a `[this+0x428]` másik sávjelzőt. A húzáság azonnal meghívja a `0x007fdd00` csúszka-leképezőt; húzás közbeni egérmozgás ugyancsak oda jut. Egérfelengedéskor (`WM_LBUTTONUP=0x202`) a húzáság a `0x007fd770`-nek adja át a `[this+0x514]` indexet, majd törli a két jelzőt. A sávjelző további hatása és a `0x007fd770` felhasználói jelentése nincs teljesen azonosítva. A `0x007fb210` az `overlays/timeline`, `overlays/timelinedot` és `overlays/sliderthumb` elemeket kéri le; a `timelinedot`, `startbutton` és listaikon teljes kattintási/húzási működése továbbra sem következik az elemnevekből.

Az automatikus léptetés küszöbe korábban megerősítve lett: a `0x00802060` a QPC-ből számolt eltelt másodpercet a `Preferences\SlideshowEffectTime` egész másodpercben megadott `T` értékével hasonlítja össze, és a túllépéskor léptető utat hív. A callback frissítési periódusa és az aktív futásidejű `T` nincs meg; a pumpa 50 ms-os alvása legfeljebb 20 frissítést/másodpercet ad, ha a jelző be van állítva. A `T` küszöb ezért nem azonos a bizonyított, állandó automatikus léptetési ütemmel (38.2.34 §1, §3; 38.2.34 §5 cáfoló ellenőrzése).

##### §3 A dátumcsúszka képernyőkoordináta-leképezése

A `0x007fdd00` az egér x koordinátáját a `[this+0x6d8]` és `[this+0x6d8]+[this+0x6c8]` közötti szakaszra korlátozza, majd `t=(x-lo)/(hi-lo)` normalizált értéket képez. Az `A` tömb `[this+0x388]`, az elemszám `[this+0x38c]>>1`; minden indexnél az `A[i]/A[n-1]` arányt hasonlítja `t`-hez, és a legkisebb abszolút eltérésű indexet választja. A feltétel szigorú `<`, így azonos eltérésnél az első talált index marad. A választott index a `[this+0x514]` mezőbe kerül; az indexelt elem pointere a `[this+0x3a8]+i*0xf8` címről lesz kiválasztva, ha `i < [this+0x3ac]>>1`, különben a kijelölt pointer nulla. A thumb x koordinátáját a `0x00c29990` helper eredménye és a `[this+0x728]` mező alapján frissíti, az y-t a `[this+0x72c]` mezőről állítja vissza.

**Korlát.** Az `A` tömb elemeinek jelentése nincs meg; a kód önmagában nem bizonyítja, hogy azok dátumok, Unix-idők vagy más időkoordináták. Ezért a képernyő x → normalizált arány → tömbindex leképezés pontos, a dátumérték leképezése és az eredeti adatmező nincs meg. A `0x00c29990` helper teljes kerekítési viselkedése sincs e körben feloldva.

##### §4 Bizonyíték, független utak és cáfoló kísérlet

| Állítás | Forrás |
|---|---|
| A `CThumbUI+0x2bc` mezőbe tett objektum `CThumbDB`; ez különbözik a qshow inputjától. | bináris (`0x004039f0`, `0x005643e0`, `0x00415790`) + RTTI (`0x00c9052c`, `0x00c81f78`) |
| A qshow bemeneti pointerlánca a `CThumbUI+0x2c0` mezőtől oneup `+0x2f4`-ig és a descriptor-szolgáltatóig. | bináris (`0x005e96d9`, `0x008037e0`, `0x007fa7f0`, `0x008018a0`) - feltételes, egy közvetlen adatút |
| A MakeTimeline count/index út a `CThumbUI+0x2c0` mezőt használja; az elemkérő vtable-hívás külön `+0x2bc` szolgáltatóhoz jut. | bináris (`0x005e9434`, `0x005e9490`, `0x00562cc0`) + RTTI (`0x00c81f78`) |
| Az `0x008018a0` a kapott descriptor elemeit sorrendben appendeli a `+0x3ec` tömbbe, jelző alapján kihagyva egyes elemeket; a forráskollekció jelentése és upstream rendezése nincs azonosítva. | bináris (`0x008018a0`, `0x004b0190`) |
| A `0x00801270` a QDrawable qshow-objektum billentyűkezelő-helye; Escape, nyilak és szóköz közvetlen híváságai a táblázat szerintiek. | bináris (`0x00801270`, `0x007fa7f0`) + RTTI (`0x00cbd66c`) |
| A csúszka x→index képlete, a kiválasztott mezők és a szigorú tie-kezelés. | bináris (`0x007fdd00`) |
| A csúszka húzás- és felengedési útja a qshow egérkezelőjéből a leképezőig, majd a `0x007fd770`-ig. | bináris (`0x007fde80`, `0x007fdd00`, `0x007fd770`) |
| A gomb Exit és Escape visszatérő objektuma a `0x00982bf0` által létrehozott `qshow` `ytWindow` host; oneup `+0x50` → host `vtable+0x14` (`0x00983270`). | bináris, két külön Exit/Escape hívásút (`0x008037e0`, `0x00982bf0`, `0x007fa480`, `0x007fb820`, `0x008032e0`, `0x00983270`) + RTTI/vtable (`0x00cd87fc`) |
| A `+0x2c0` és `+0x388` mezők közvetlen íróinak célzott keresése nem kötötte az összes azonos offset-találatot a qshow/QDrawable osztályhoz. | bináris (`paszta.py` `.text`-pásztázás; `paszta.memoria_kapu()` volt az első művelet) |
| Az `A` tömb dátumjelentése, a teljes gyűjteményi forrás és a konkrét elemkészlet. | NINCS MEG |
| A teljes képkockánkénti pálya, a rétegek/képtartalom, a `timelinedot`/listaikon teljes vezérlése, valamint a qshow host metódusának végső navigációs hatása és a visszaállított nézet/index. | NINCS MEG |
| E körbeli futásidejű qshow-képkocka-felvétel vagy QEMU-kimenet. | NINCS MEG |

**A két független út.** A út: `0x005e96d9` → qshow argumentum `+0x14` → oneup `+0x2f4` → `0x004b0190`; ez egy közvetlen pointerlánc, ezért önmagában **feltételes**. B út: a `0x005e9434` a `CThumbUI+0x2c0` értékével kér elemszámot a `0x004a0980`-től, majd a `0x005e9490` indexel, és a CThumbUI vtable `+0x90` metódusán, illetve a `0x00562cc0` thunkon át a külön `CThumbUI+0x2bc`/`CThumbDB` providerhez jut. Ez külön megerősíti, hogy ugyanaz a mező a MakeTimeline count/index útban is szerepel, de nem bizonyítja a két hurok kimenetének azonosságát vagy a kollekció album-/mappa-jelentését. Az Exit-gomb és Escape külön hívásútja egyaránt a `qshow` gazdaablak `+0x14` slotjához jut; RTTI/vtable-adat azonosítja a gazdaablakot `ytWindow`-ként. A QDrawable helybesorolást a konstruktor/vtable-adat és a billentyűkezelő utasításai támasztják alá. A billentyű-, egér- és csúszka-utasítássorok felhasználói hatása továbbra is **feltételes**; a teljes animáció vizuális hatása nincs meg.

**Cáfoló kísérlet.** Azt a feltevést próbáltam cáfolni, hogy a főablak `0x005e60d0` kezelője maga a qshow billentyűkezelője, és hogy a nyilak minden állapotban közvetlenül előző/következő képet léptetnek. A `0x00801270` közvetlen diszasszemblálása a `WM_KEYDOWN` ágat és a timeline módú `0x007fd0c0` hívást mutatja; a QDrawable vtable `0x00cbd66c` metóduslistája a `0x00801270`-et a `+0x30` eseményhelyre teszi. A `0x005e60d0` Ghidra-kimenete külön főablak-kezelő. A próba megcáfolja mindkét feltevést; a címosztályozást az assembly és az attól független RTTI/vtable út egyaránt alátámasztja.

**Bizonyítottsági fok.** A teljes #5401 **nyitott**. A `CThumbUI+0x2bc` mezőbe tett objektum `CThumbDB` osztálya, a gomb Exit/Escape célobjektuma (`qshow` `ytWindow`) és a QDrawable billentyűkezelő-helyének besorolása **megerősített** (külön vtable/callback-út + RTTI/vtable-adat). A qshow közvetlen bemeneti pointerlánca (`CThumbUI+0x2c0` → oneup `+0x2f4`) egy közvetlen statikus adatútból ismert, ezért **feltételes**; a `+0x2c0` mögötti kollekció szemantikája **nyitott**. A közvetlenül olvasható billentyű-, egér- és csúszka-utasítássorok felhasználói hatása **feltételes**, mert hiányzik a gyűjteményt megnevező út és a vizuális mérés. A §38.2.34 automatikus léptetési `T` küszöbe ismert, a tényleges periódus nem; a §38.2.61-62 mozgás-részletei nem zárják le a teljes, képkockánkénti animációt.

##### §5 A #5401 „Kész, ha” pontjainak állapota

1. ⛔ **Képlánc, forráshalmaz, sorrend, gyűjteményenkénti darabszám és elemlista:** a qshow közvetlen pointerlánca a `CThumbUI+0x2c0` mezőtől indul (feltételes, egy bináris út); ettől külön a MakeTimeline count/index út is olvassa ezt a mezőt, az elemkérő pedig a `+0x2bc` `CThumbDB` providert hívja. A `+0x2c0` kollekciószemantikája, a konkrét tagok és darabszámok NINCS MEG (`0x005e96d9`, `0x005e9434`, `0x005e9490`, `0x008018a0`).
2. ⛔ **Pálya, méret, forgatás, alfa, időzítés, háttér és kártyarajz:** a 38.2.34, 38.2.61 és 38.2.62 igazolt részképletei mellett hiányzik a teljes képkocka → transzformáció → rajzréteg lánc és az élő képkockafelvétel. E körben nem állítok teljes mozgásképletet.
3. ⛔ **Vezérlők:** a billentyűágak, csúszka húzás/felengedés útja és normalizált indexképlete részben megvan; a dátumtömb jelentése, a `timelinedot`, `startbutton`, listaikon és automatikus lépés tényleges periódusa nyitott. Az Exit/Escape a qshow `ytWindow` host `0x00983270` metódusához jut; a végső navigációs hatás nincs meg.
4. ⛔ **Diavetítésbe lépés és kilépés:** a Space két állapotágát és a `+0x3b8=0` átmenetet a 38.2.65 részletezi; a futásidejű előfeltétel és az Escape utáni gyűjtemény/index nyitott. Az automatikus léptetés `T` másodperces küszöbe ismert; az Exit/Escape célobjektuma a qshow `ytWindow` host, de a gazdaablak-metódusának végső képernyője és a tényleges callback-periódus nincs bizonyítva.

##### §6 Nyitott

- A `CThumbUI+0x2c0` mező egy CThumbUI-adatútban olvasott; a `0x005643e0` konstruktor `[this+0x2c0]` mezőjébe az EAX-ben kapott értéket írja (`0x005644fa`), a `0x004039f0` pedig a konstruktor `+0x2c0` argumentumát a hívó `[X+0x1038]` mezőjéből adja. A teljes `.text` offset-pásztázás sok más osztálybeli `+0x2c0` találatot is ad, ezért a konkrét írók osztályhoz kötése nélkül azok nem nevezhetők meg. Nyitott: a `[X+0x1038]` érték forrása és a kollekciójelentés; megszerzés: az `0x004039f0` szülőobjektumának azonosítása és a `[X+0x1038]` mezőíróinak `paszta.py`-jal, `memoria_kapu()` elsőként történő célzott pásztázása.
- A `0x004b0190` dekompilálása elkészült; nyitott a `[source+0xc4]+0x48` objektum konkrét osztálya, a vtable `+0x2c` célja és a descriptor upstream sorrendje. Megszerzés: az objektumot előállító konstruktor vagy producer vtable-írását kell azonosítani; csak a célcím ismeretében dönthető el, kell-e új Ghidra-kör.
- A qshow `+0x388` pointer közvetlen íróját a `paszta.py` teljes `.text` pásztázása nem rendelte hozzá a QDrawable osztályhoz; ugyanaz az eltolás más osztályokban is előfordul. Az `A[i]`/`A[n-1]` értékek időbeli jelentése NINCS MEG. Megszerzés: a QDrawable vtable ismert metódusainak célzott ellenőrzése, majd a talált segéd- vagy helyfoglaló út `+0x388`-ra író kódjának osztályhoz kötése.
- A `0x007fd0c0`, `0x00802ae0`, `0x00802a90` és `0x007fde80` dekompilálása elkészült; a `+0x2f8` átmenetobjektum látható eredménye, a nem timeline bal/jobb ág felhasználói jelentése, a `+0x428` sávjelző és az overlay-nevek egér-hit-testhez kötése továbbra is nyitott.
- A gomb Exit és Escape visszatérő objektuma a qshow `ytWindow` host; a `+0x14` metódus `0x00983270` végső navigációs hatása és a visszaállított nézet/index NINCS MEG.
- A `0x00983270` dekompilálása elkészült: a nulla paraméterű ág WM_CLOSE-t kér a qshow `+0x6c` HWND-jére, a másik ág az aktuális szál ablakait járja be. A képernyőn megjelenő visszatérési állapotot és a megőrzött kollekció/indexet csak futás közbeni, előtte-utána felvétel dönti el.
- Futás közbeni megerősítés: qshow Exit/Escape előtt és után rögzíteni a megjelenő ablakot, kollekciót és elemindexet; ez a `0x00983270` statikus olvasatát ellenőrzi.
- A `0x009dc040` dekompilálása és QEMU-ellenőrzése elkészült (38.2.64); nyitott a hívók képpuffer- és rétegszemantikája, valamint a `0x008001c0` → `0x00aa6180` rétegsorrend.
- A `0x00802ae0` és `0x00802a90` közvetlen mezőhatása a 38.2.66-ben rögzítve; hogy a pufferürítés és az `+0x3f4` változása milyen felhasználói eredményt ad, NINCS MEG.
- A `0x007fde80` koordináta-, egérüzenet- és flag-ágai a 38.2.66-ben rögzítve; a `+0x428`/`+0x429` vezérlők `timelinedot`/`sliderthumb` nevű overlayhez rendelése és a listaikon hit-testje NINCS MEG.
- QEMU-val számszerűen vezérelt qshow-futás és sűrű, igazoló Wine-képkocka-felvétel NINCS MEG; megszerzéséhez a forráskollekciót és az aktív lejátszási állapotot rögzítve kell futtatni.

**Új kutatási jegyjavaslat.** Nincs; mindegyik nyitott tétel a #5401 négy elfogadási pontjához tartozik.

#### 38.2.64 A Space/Auto objektumváltása, kilépés és alfa-keverés (#5401, 2026-10-22)

**Hatókör és módszer.** A `0x00801130`, `0x00803110`, `0x00802be0`, `0x00983270` és `0x00982fa0` függvényeket az eredeti PE-ből annotált helyi diszasszemblálással ellenőriztem; a SQLite-index függvényméreteit használtam. A `0x00801130` és `0x00983270` Ghidra-kimenetét külön összevetettem az utasításokkal. A `0x00983430` (qshow-host méretező/frissítő út) és a `0x008032e0` név szerinti Auto/Auto2 ágának meglévő dekompilálását szintén felhasználtam. A 202-209 és 210-216 Ghidra-kör a korábbi címkérések dekompilálását elvégezte; a mostani nyitott pontokhoz új, ismert függvényhatárú Ghidra-cím nem szükséges. QEMU-mérés a `0x009dc040` alfa-keverőn készült az eredeti gépi kódon; a próba-bemenetek és kimenetek lent. Wine/qshow élő felvétel ebben a körben nem készült; a korábbi job-220 felvétel nyers képei nem voltak a helyi mérőadat-archívumban.

##### §1 Space és Auto: pontos állapot- és objektumút

`0x00801270` a szóköz-ágban a `[this+0x3bb]` állapottól függően hívja a `0x00803110`-et vagy a `0x00801130`-at. A `0x00803110` az átadott oneup-objektum `[+0x25c]` belső objektumán dolgozik: ha `[+0x3be] != 0`, előbb `0x00801cf0`-et hív; beállítja `[+0x518]=1`-et, QPC-értéket ír `[+0x520]`-ba, majd nullázza `[+0x3b8]`-at és `[+0x428]`-at. Ezután meghívja a `0x00801130`-at a belső objektumon. Ha a oneup `[+0x50]` hostmezője nem nulla, a `0x00802be0`-nek a hostot és a `[+0x25c]` belső objektumot adja át.

A `0x00802be0` a host `[+0x64]` aktív objektumát cseréli: a korábbi objektum vtable `+0x28` metódusát null argumentummal hívja, beírja az új pointert, majd annak vtable `+0x28` metódusát a host pointerével hívja. Ezután `0x00983430`-at hívja. Az utóbbi a `[host+0x6c]` HWND kliensméretét kéri le, `0x00983a60`-on át méretet közöl, és teljes frissítést kér az aktív objektumtól. A közvetlen út tehát hoston belüli objektumváltás és újraméretezés/újrarajzolás; a `0x00803110` törzsében nincs közvetlen ablaklétrehozó API-hívás.

A `0x00801130` a `[this+0x3bb]` logikai értékét megfordítja, majd átadja a `0x0097e510`-nek. Ha az új érték nulla, `0x00802230(this,0)`-at és a `0x009aabf0(this+0x444,-1,-1,-1,-1)` útvonalat hívja; ha nem nulla, `0x00802c20`-at hív, és `[this+0x3ba]==0` esetén a `0x00aa6f40`-hez jut. A `0x008032e0` név szerinti eseménykezelőjében mind a `oneup/auto`, mind a `oneup/auto2` a `0x00803110`-et hívja. Ezért a `0x00803110` önmagában nem kizárólag a Timeline→diavetítés billentyűparancs: a statikus kód több bemenetről is eléri.

**A futásfelvétel határa.** A 38.2.17 § job-220 feljegyzése szóköz után a kártya gyűjteményének teljes képernyős diavetítését, majd Escape után a főablak megjelenését írja le (képkockaszámokkal). A nyers képkockák ebben a munkamenetben nem elérhetők, ezért ezt korábbi, nem újramért mérési bizonyítékként tartom nyilván. A statikus `0x00803110` út nem adja meg a visszatérő gyűjteményt vagy képpozíciót.

##### §2 Kilépés a qshow gazdaablakból

Az Escape út (`0x007fb820`) és a név szerinti `oneup/exit` ág (`0x008032e0`) külön hívási útból a oneup `[+0x50]` mezőjének vtable `+0x14` metódusát hívja. A `0x008037e0` ezt a mezőt a `0x00982bf0` által létrehozott `qshow` `ytWindow` hosttal tölti fel; a host vtable `+0x14` célja `0x00983270`.

A `0x00983270` nulla első paraméterénél a `[this+0x6c]` HWND-re `PostMessageA(hwnd, WM_CLOSE=0x10, 0, 0)`-t küld, ha a `DAT_00d67858` globális értéke nem pozitív. Pozitív értéknél `GetCurrentThreadId()` + `EnumThreadWindows()` út fut a `0x00982fa0` callbackkel, és beállítja a `DAT_00d6784b` jelzőt. A függvény tehát bezárási/ablak-enumerációs út, nem olyan helyi index-visszaállítás, amelyből a folytatási gyűjtemény vagy kép megnevezhető lenne.

##### §3 Alfa-keverő: számszerű, QEMU-val ellenőrzött képlet

Az `0x009dc040` az alfa egész értékét előbb `a0=max(a-1,0)` alakra csökkenti, a kiegészítő súlyt `255-a0`-ként képezi, majd a két forráscsatorna súlyozott összegét 8 bittel jobbra tolja. `a` 0 és 256 közötti egész tesztértékekre, csatornánként `O=floor((a0·X+(255-a0)·Y)/256)`. A `DAT_00d695d4` kapcsoló a tesztelt ágakban az `X` és `Y` forrást felcseréli. A leolvasott bináris utasítások és az eredeti függvény QEMU-kimenete egyezik. Példamérés két BGRA pixelre (a két forrás bájtjai `20,40,60,80,100,120,140,160` és `220,200,180,160,140,120,100,80`):

| `DAT_00d695d4` | `a` | QEMU-kimeneti bájtok |
|---:|---:|---|
| 0 | 0, 1 | `219,199,179,159,139,119,99,79` |
| 0 | 128 | `119,119,119,119,119,119,119,119` |
| 0 | 255 | `20,40,60,80,99,119,139,159` |
| 0 | 256 | `19,39,59,79,99,119,139,159` |
| 1 | 0 | `19,39,59,79,99,119,139,159` |
| 1 | 128 | `119,119,119,119,119,119,119,119` |
| 1 | 255 | `218,198,178,159,139,119,99,80` |
| 1 | 256 | `219,199,179,159,139,119,99,79` |

Ez a keverő műveletét és a forrásirány kapcsolását igazolja a fenti bemeneteken; a hívók által átadott alfa-tartományt, a tényleges qshow-pufferek szerepét és a háttér/kártya rétegsorrendet nem azonosítja (`0x00aa6180`, `0x008001c0`).

##### §4 Két út, cáfoló ellenőrzés és bizonyítottság

**A út: utasítás- és hívási lánc.** A `0x00801270` → `0x00803110`/`0x00801130` ág, a `0x00803110` → `0x00801130`/`0x00802be0` hívások, a host `+0x64` objektumcseréje, valamint a `0x00983270` WM_CLOSE-ág az annotált diszasszemblálásból követhető. A qshow host vtable `+0x14` célját az `0x008037e0` konstrukciós útja és a host vtable adata köti `0x00983270`-hez.

**B út: független ellenőrzés.** A `0x008032e0` név szerinti Auto/Auto2 összehasonlító ágai a `0x00803110`-hez vezetnek; ettől függetlenül az Escape-út és az Exit-gomb útja külön-külön a oneup `[+0x50]` gazdaablak-objektum `vtable+0x14` célját hívja. A qshow felépítője ugyanebbe a `[+0x50]` mezőbe írja a `qshow` `ytWindow` hostot. Ezek a statikus utak a hoston belüli objektumváltással és bezárási kéréssel egyeznek. A teljes képernyős megjelenést és főablakba visszatérést a korábbi job-220 felvétel külön, futásidejű útként rögzíti, de a nyers kép hiánya miatt most nem auditálható újra.

**Cáfoló kísérlet.** Azt az olvasatot próbáltam cáfolni, hogy a `0x00803110` maga új Win32-ablakot hoz létre. A teljes 107 bájtos függvényt diszasszembláltam: ablaklétrehozó API-hívás nincs benne; az utolsó út a `[+0x50]` host és a `[+0x25c]` tartalomobjektum `0x00802be0`-n keresztüli cseréje. Ezt függetlenül a `0x00983430` törzse is alátámasztja: a függvény HWND-kliensméretet kér le, méretez, majd újrarajzolást kér. A cáfoló próba azt a túl erős állítást igazolja, hogy a `0x00803110` közvetlen ablaklétrehozó; nem cáfolja, hogy a host új tartalomobjektuma vizuálisan diavetítésként jelenik meg.

**Bizonyítottsági fok.** A qshow `ytWindow` host és a `vtable+0x14` → `0x00983270` kilépési út **megerősített**: a hostot a konstrukciós/vtable-adat azonosítja, és az Escape, illetve az Exit külön hívási útja is ezt a slotot éri el. A `0x00803110` belső mezőmódosításai és hívássorrendje **feltételes** (egy közvetlen függvényút); az Auto/Auto2 külön név szerinti hívói ezt a függvényválasztást, a korábbi job-220 felvétel pedig csak a látható átmenet feljegyzett eredményét támasztja alá. Az alfa-keverő képlete a megadott QEMU-bemeneteken **megerősített** (utasítások + eredeti gépi kód mért kimenete). A Space utáni teljes képernyős diavetítés és Escape utáni főablak a korábbi job-220 feljegyzés alapján **feltételes** ebben a munkamenetben, mert a nyers képkockák hiányoznak. A teljes #5401 **nyitott**: a forráshalmaz és rendezés, teljes képkockánkénti pálya/rajz, vezérlők dátumjelentése és periódusa, valamint a visszatérő képpozíció továbbra sincs lezárva.

##### §5 A PicasaPy jelenlegi Időrendje és fejlesztési határ

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A `0x005e8a70` Időrend útja oneup/qshow bemutatót épít; Space a `0x00801270` állapotágán és a `0x00803110` host-objektumváltásán át jut a külön tartalomobjektumig. A gyűjtemény és a mozgás teljes képlete nyitott. | A `TimelineController.reload()` az index összes nem rejtett fotóját kéri le; a `picasapy.timeline.build_periods()` EXIF `taken_at`/befagyasztott fájlidő szerint év-hónapra csoportosít; a `TimelineView.qml` görgethető bélyegképrácsot rajzol, kattintásra a fő nézőt nyitja. Forrás: `src/picasapy/app/timeline_controller.py`, `src/picasapy/timeline.py`, `src/picasapy/app/qml/PicasaPy/TimelineView.qml`. | A #5377 teljes animált bemutatójának fejlesztői specifikációját csak a képlista, rendezés, mozgás/rajzréteg, vezérlők és visszatérési állapot lezárása után lehet pontosan megadni; a mostani bizonyíték nem ad becslésmentes, teljes implementációs listát. |

**Nyitott kérdések mérlege (38.2.64).** A Space/Auto és Exit statikus útja, valamint az alfa-keverő számszerű művelete már dokumentált. Nyitva marad a #5401 mind a négy elfogadási pontja: teljes képlánc; a képátmenet és rétegek teljes időfüggése; a timelinedot/startbutton/listaikon és dátumcsúszka tényleges jelentése, illetve autoplay periódusa; valamint a teljes képernyős diavetítésből visszaálló gyűjtemény és képpozíció.

#### 38.2.65 A szóköz állapotfüggő ága és a `+0x3b8=0` mezőírás (#5401, 2026-10-22)

**Hatókör.** Ez a szakasz a 38.2.63 szóköz-sorát pontosítja. Statikusan bizonyítható, hogy a szóköz nem minden állapotban ugyanazt a hívásutat hajtja végre. A `0x00803110` a `[edi+0x25c]` objektum `+0x3b8` mezőjét nullára írja; a 38.2.21 §4 Ghidra-eredménye azonosítja `edi`-t OneUpUI-ként, és `[edi+0x25c] = this` kapcsolatot rögzít, tehát az írás a qshow aktuális objektumán történik. A futásidejű kezdőállapotot és a kilépés utáni nézetet ez a kör nem mérte meg.

##### §1 A billentyűág és az állapotmódosítás

A `0x00801270` csak `WM_KEYDOWN` (`0x100`) esetén jut a billentyűágakhoz (`0x00801299`). A szóköz (`0x20`) vizsgálata a `0x008012df` címen történik. A külön Ctrl-ág után a `0x00801310` a `[this+0x3bb]` bájtot ellenőrzi:

- Ha a bájt nem nulla, a kezelő a `[this+0x2dc]` mezőt átadva meghívja a `0x00803110`-et (`0x00801310`-`0x0080131f`). A hívott függvény a `[oneup+0x25c]` állapoton: `esi`: ellenőrzi a `+0x3be` jelzőt; nem nulla értéknél előbb a `0x00801cf0`-et hívja. Ezután `+0x518=1`-et ír, lekéri a QPC-t, `+0x3b8=0`-t és `+0x428=0`-t ír, az időbélyeget `+0x520`-ba teszi, majd újrahívja a `0x00801130`-at (`0x0080311d`-`0x0080315c`).
- Ha a bájt nulla, a billentyűkezelő közvetlenül a `0x00801130`-at hívja (`0x00801332`-`0x00801334`), a `0x00803110` kihagyásával. A `0x00801130` a `+0x3bb` értékét nullára/nem nullára billenti, de a függvényben nincs `+0x3b8`-írás; ezért ez az ág önmagában nem bizonyít módváltást.

A frissen indított Időrendben a `0x007fda00` `[this+0x3bb]=0`-t állít be (38.2.9). A külön Ctrl-ágon kívüli **első Space** ezért a `0x00801130`-ra jut, és a `sete` művelet 1-re billenti a jelzőt; maga ez a függvény nem írja a `+0x3b8` mezőt. A `0x00802060` nem léptet, amikor a `+0x3bb` nem nulla (38.2.34). Ha a jelző a következő billentyűig nem változik, a **következő Space** a `0x00803110`-et hívja: ez a qshow `[this+0x3b8]` mezőjét nullázza, majd a `0x00801130` a `+0x3bb`-t ismét nullára billenti. A qshow-építő nulla módága a `0x00801cf0` diavetítési út. Az első Space által meghívott `0x00802c20` és `0x00aa6f40` belső/indirekt mellékhatásai nincsenek teljesen feltárva, ezért nem állítható, hogy kizárólag a második Space okoz minden látható módváltozást. Ez a statikus hívássor, nem futás közbeni képkocka-megfigyelés.

##### §2 A 0-s mód azonosítása és a független hívóút

A qshow-építő `0x008037e0` a paraméterrekord `+1` bájtja alapján választ: nulla esetén a `0x00801cf0`-et hívja (`0x008039de`-`0x008039fe`); nem nulla esetén a `0x007fda00`-t (`0x008039e2`-`0x008039e7`). A 38.2.9 szerint a `0x007fda00` a qshow saját `this+0x3b8` mezőjére `1`-et ír. A 38.2.21 §4 a `0x00803110` bemeneti objektumláncában `[edi+0x25c] = this`-t igazolja, ezért a Space-ág nullázása ugyanazon qshow-állapotmezőt éri el. A konstruktor nulla paraméterágának célfüggvénye a `0x00801cf0` diavetítési út; a nem nulla ága indítja az Időrend-módot.

**Független hívóút:** a `0x008032e0` név szerinti `oneup/auto` és `oneup/auto2` eseményágai külön-külön hívják a `0x00803110`-et (`0x00803486`, `0x008034c5`). Ez a billentyűkezelőtől független UI-belépési pont ugyanazt a módváltó rutint használja; a qshow-építő külön módválasztó ága a rutin által beállított nulla értéket a diavetítési úthoz köti.

Az átmenet nem bizonyít új ablak létrehozását: a `0x00803110` az állapotmezőket módosítja, és csak akkor hívja a `0x00802be0`-t, ha a oneup `+0x50` hostmezője nem nulla (`0x00803161`-`0x0080316e`). A korábbi job-220 feljegyzés szóközre teljes képernyős diavetítést ír, de az eredeti képkockasorozat és a `+0x3bb` kezdőértéke nem áll rendelkezésre; ez a megfigyelés itt nem függetlenül reprodukált mérés.

##### §3 Index és visszatérés

A `0x00803110` közvetlenül nem írja a `[state+0x3f4]` indexet. Ha a belépéskor `[state+0x3be] != 0`, az előtte meghívott `0x00801cf0` a `0x00801f25` címen eggyel csökkenti a `+0x3f4` értéket. A függvényútból ezért csak az állítható, hogy az index közvetlen írása hiányzik, de a feltételes előhívás módosíthatja; a tényleges kezdő index, a kilépéskori visszatérő elem és nézet **NINCS MEG**. A job-220 korábbi „visszatér a főablakba” megjegyzése nem azonosítja, hogy onnan az Időrend folytatódik-e.

##### §4 Bizonyíték, független utak és cáfoló kísérlet

| Állítás | Forrás |
|---|---|
| Szóközre a `[this+0x3bb] != 0` ág a `0x00803110`-et, a nulla ág közvetlenül a `0x00801130`-at hívja. | bináris (`0x00801270`, `0x00801310`-`0x00801334`) |
| A `0x00803110` a `+0x3b8` módmezőt nullára állítja; a feltételes előhívás `0x00801cf0`. | bináris (`0x00803110`, `0x0080311d`-`0x0080315c`) |
| A qshow módjelző bájt nulla értéke a `0x00801cf0`-hez, nem nulla értéke az Időrend `0x007fda00` útjához vezet. | bináris (`0x008037e0`, `0x008039de`-`0x008039fe`; 38.2.9) |
| Időrend-indításkor `[this+0x3bb]=0`; a nem nulla jelző mellett a `0x00802060` nem léptet. | bináris (`0x007fda00`; `0x00802060`; 38.2.9, 38.2.34) |
| A `oneup/auto` és `oneup/auto2` a billentyűúttól függetlenül ugyanazt a `0x00803110` rutint hívja. | bináris (`0x008032e0`, `0x00803486`, `0x008034c5`) |
| A `+0x3bb` nulla ágának `0x00801130` hívása nem ír `+0x3b8`-at. | bináris (`0x00801130`) |
| Az első flag-billentő ág helperlánca: `0x00801130` → `0x00802c20` és feltételesen `0x00aa6f40`; az utóbbi vtable `+0x84` hívást, a `0x00802c20` feltételesen `0x009833a0` host/callback útvonalat tartalmaz. | bináris (`0x00801130`, `0x00802c20`, `0x00aa6f40`, `0x009833a0`); az indirekt callbackek qshow-módra gyakorolt hatása NINCS MEG |
| A `+0x3f4` index csak a feltételes `0x00801cf0` előhívásban csökken; a visszatérési index/nézet. | bináris (`0x00801cf0`, `0x00801f25`); a futásidejű visszatérés NINCS MEG |
| A korábbi job-220 futásban a szóközt diavetítésbe lépésként jegyezték fel. | mérés (`job-220`; nyers képkockák és állapotbájt nélkül, nem reprodukált) |

**A két független út.** A út: a `0x00801270` billentyűágának nyers utasításolvasása és a `0x00803110` törzse megadja a feltételt, a `+0x3b8=0` írást és a flag visszabillentését (a `[edi+0x25c]=this` objektumkapcsolatot a 38.2.21 §4 dekompilációja adja). B út: a külön `0x008037e0` qshow-építő módjelző bájtja nulla esetén a `0x00801cf0` diavetítési ágat, nem nulla esetén a `0x007fda00` Időrend-indítást hívja; ez utóbbi a saját `[this+0x3b8]=1` és `[this+0x3bb]=0` mezőket állítja be (38.2.9). A két kódút ugyanazon qshow-objektum `+0x3b8` mezőjének 0-s diavetítési és 1-es Időrend-állapotát adja. A külön `0x008032e0` `oneup/auto`/`auto2` felületi ág ugyancsak a `0x00803110`-et hívja.

**Cáfoló kísérlet.** Azt a tág feltevést vizsgáltam, hogy a szóköz minden állapotból közvetlenül meghívja a módváltó rutint. Frissen indított Időrendnél a `0x007fda00` `[this+0x3bb]=0`-t állít be, ezért a Ctrl-ágon kívüli Space-re a `0x00801270` közvetlenül a `0x00801130`-at hívja; ez a közvetlen hívás nem a `0x00803110`. A feltevés, hogy minden Space ugyanarra a módváltó hívásra jut, cáfolva. Az `0x00801130` további helperjeinek indirekt, látható hatása ettől még külön nyitott.

**Bizonyítottsági fok: megerősített, szűk statikus hívásállításra.** A qshow `[+0x3bb] != 0` állapotában a Space a `0x00803110`-et hívja, amely a qshow `[+0x3b8]` mezőjét nullázza; a külön qshow-építő nulla módága a `0x00801cf0` diavetítési út. Friss Időrend-indításnál a flag 0-ról indul és a közvetlen első Space a `0x00801130`-at választja. Az első Space helperjeinek indirekt hatása, a futó állapot és a képkockákon látható váltás, valamint az Escape utáni visszatérés **nyitott**. QEMU- vagy új Wine-felvétel ebben a körben nem készült.

##### §5 A #5401 „Kész, ha” pontjainak frissítése

1. ⛔ **Képlánc és forráshalmaz:** ez a vizsgálat nem változtat a 38.2.63 nyitott megállapításain.
2. ⛔ **Teljes pálya és rajzolás:** a Space módágának feltárása nem egészíti ki a teljes képkockánkénti mozgást vagy a rétegrajzolást.
3. ⛔ **Vezérlők:** a szóköz egyik feltételes ága megvan; a dátumcsúszka, a `timelinedot`, a `startbutton`, a listaikon és az automatikus léptetés élő üteme továbbra is hiányos.
4. ⛔ **Diavetítésbe lépés és kilépés:** statikusan megerősített, hogy `+0x3bb != 0` esetén Space a módot nullázó `0x00803110`-et hívja; friss Időrend-indításnál a közvetlen első Space a flag-billentő ágat választja. Az első ág helperjeinek esetleges látható hatása, az élő előfeltétel, a képkockaeredmény, az Escape utáni nézet és a folytatási index nincs mérve.

##### §6 Nyitott

- Futásidejű mérés szükséges a szóköz előtt a `[this+0x3bb]`, a `[edi+0x25c]+0x3be` érték, utána a látható mód és `+0x3f4` index rögzítésére; a mérésen a `0x00801270` → `0x00803110` statikus út ellenőrizhető.
- Ghidra-kör kell: 0x00aa6f40: az `[esi+0x26c]` objektum vtable `+0x84` callback célja, és módosítja-e a qshow `+0x3b8`/`+0x3bb` mezőit az első Space flag-billentő ágában [blokkoló]
- A `0x009833a0` gazdaablak-callback út és a két `+0x28` cél a 38.2.67-ben fel van tárva; a közvetett segédfüggvény-hatásra nyitott címeket ott sorolja a Ghidra-várólista (`0x00aa6f40`, `0x00a56800`, `0x00a5e850`).
- A `0x00983270` gazdaablak-metódus statikus kilépési callbackje a 38.2.68-ban pontosított; hogy Escape után az Időrend melyik gyűjteménnyel és elemmel folytatódik, **NINCS MEG**.
- QEMU-val számszerűen vezérelt futás és sűrű Wine-képkocka-sorozat nem készült.

**Új kutatási jegyjavaslat.** Nincs; ezek továbbra is a #5401 elfogadási pontjai.

#### 38.2.66 Egérkoordináták, húzásjelzők és módfüggő nyílágak (#5401, 2026-10-22)

**Hatókör.** A `0x007fde80` egérkezelő már meglévő Ghidra-kimenetét az eredeti bináris függvényenkénti diszasszemblyével vetettem össze; a billentyűburkolókat és a két nem-automatikus háttérágat is közvetlenül olvastam. A vezérlőnevek és a látható eredmény futásidejű hozzárendelése ettől még nincs meg.

##### §1 Egérkoordináta és Timeline-módbeli húzás

A `0x007fde80` az esemény `x/y` koordinátáját a host kliensméretéből és a qshow `[+0x2c8,+0x2d0] × [+0x2cc,+0x2d4]` belső téglalapjából skálázza:

```text
x' = x_event * (([this+0x2d0] - [this+0x2c8]) / (client.right - client.left))
y' = y_event * (([this+0x2d4] - [this+0x2cc]) / (client.bottom - client.top))
```

Timeline állapotban (`[this+0x3b8] != 0`) balgomb-lenyomáskor (`WM_LBUTTONDOWN=0x201`) a `[this+0x6d8]`, `[this+0x6dc]`, `[this+0x6c8]`, `[this+0x6cc]`, `[this+0x718]`, `[this+0x728]`, `[this+0x71c]`, `[this+0x72c]` mezőkből ellenőrzési téglalapot képez. Az eredmény szerint a `[this+0x429]` húzásjelzőt állítja be és meghívja a `0x007fdd00` leképezőt, vagy a `[this+0x428]` jelzőt állítja be. Húzás közbeni egérmozgás (`WM_MOUSEMOVE=0x200`) a `+0x429` esetén ismét a `0x007fdd00`-hoz jut; a `+0x428` esetén a `[this+0x310]` értékét módosítja a kurzor x-eltéréséből és a `0x00cf3fa8`/`0x00cf3fb0` konstansokból.

Egérfelengedéskor (`WM_LBUTTONUP=0x202`) a `+0x429` ág a `[this+0x514]` értéket átadja a `0x007fd770`-nek, majd mindkét húzásjelzőt törli (`0x007fde80`, `0x007fe1a4`-`0x007fe1cf`). Az offset- és hívásút bizonyított; a `+0x428`/`+0x429` jelzők `timelinedot`/`sliderthumb` nevű overlayekhez rendelése, valamint a `+0x310` mező látható szerepe **NINCS MEG**.

Ugyanebben a kezelőben a `0x203` vagy `0x204` egérüzenet `[this+0x3b8]==0` esetén a `0x007fda00` módváltót hívja; nem nulla állapotban a `0x007fda80`-at, majd a feltétel sikerén a `0x007fb820`-at és opcionálisan a `[this+0x2e8]` objektum vtable `+0x18` slotját hívja. Ebből a vezérlőn végrehajtott gépi hívásút állítható, de az overlay neve és a felhasználó által látott eredmény nincs bizonyítva.

##### §2 A nyilak a qshow állapotától függnek

Bal/fel esetén a `0x008011b0`, jobb/le esetén a `0x00801210` fut. Mindkettő előbb a `[this+0x3b8]`-at vizsgálja:

| Állapot | Bal/fel | Jobb/le | Közvetlenül bizonyított hatás |
|---|---|---|---|
| `+0x3b8 != 0` | `0x007fd0c0` a `+0x2f8` alobjektum `[+0x30]` mezőjével és `+2.0f` irányargumentummal | `0x007fd0c0` ugyanazzal a mezővel, `-2.0f` irányargumentummal | Az Időrend-ág a két irányt eltérő előjellel adja át; a képernyőn látható irány és képpozíció a teljes `0x007fd0c0` állapot nélkül nem nevezhető meg. |
| `+0x3b8 == 0`, `+0x3bb != 0` | `0x00802980` | `0x008029f0` | Az előző/következő elem hívásútja (38.2.63). |
| `+0x3b8 == 0`, `+0x3bb == 0` | `0x00802ae0` | `0x00802a90` | Mindkettő a `0x008001c0`-t hívja a `+0x46c` pufferrel, majd `+0x518=1`-et és QPC-időt ír `+0x520`-ba. Csak a bal/fel ág csökkenti a `+0x3f4` mezőt kettővel, és negatív eredménynél `-1`-re állítja. A különbség felhasználói jelentése nincs meg. |

##### §3 Bizonyíték, utak és cáfoló kísérlet

| Állítás | Forrás |
|---|---|
| Klienskoordináta skálázása a qshow belső téglalapjára. | bináris (`0x007fde80`, `0x007fdefe`-`0x007fdf5f`) |
| `+0x429` húzás → `0x007fdd00`; felengedéskor `+0x514` → `0x007fd770`; mindkét jelző törlése. | bináris (`0x007fde80`, `0x007fdfaa`-`0x007fdfb2`, `0x007fe1a4`-`0x007fe1cf`) |
| Bal egérgomb `+0x428` ágának `[+0x310]` módosítása. | bináris (`0x007fde80`, `0x007fdf6c`-`0x007fdf9b`) |
| A négy nyílbillentyű-út `+0x3b8`/`+0x3bb` feltételei és célhívásai. | bináris (`0x008011b0`, `0x00801210`) |
| Nem-automatikus bal/fel ág `+0x3f4 -= 2`, ha nulla alá csúszik `-1`; jobb/le ágban nincs közvetlen `+0x3f4` írás. | bináris (`0x00802ae0`, `0x00802a90`) |
| Az overlayek név szerinti azonosítása és húzás közbeni felhasználói látvány. | NINCS MEG |

**A két kódút.** A út: `0x007fde80` eseményágai közvetlenül kezelik a koordinátát, a jelzőket és a `0x007fdd00`/`0x007fd770` hívásokat. B út: a `0x00801270` billentyűkezelő a nyilakat a külön `0x008011b0`/`0x00801210` wrapperekhez irányítja, amelyek eltérő `[+0x3b8]` és `[+0x3bb]` állapotokban külön függvényeket hívnak; a `0x00802ae0`/`0x00802a90` utasításolvasása ellenőrzi a mezőmódosítás különbségét. Ezek a statikus hívás- és mezőállítások egyeznek; a vezérlőnevek és látható hatás **feltételes**, mert élő UI-mérés nem készült.

**Cáfoló kísérlet.** Azt a feltevést próbáltam cáfolni, hogy a nyilak minden állapotban ugyanazt az Időrend-mozgatást végzik. A wrapperek utasításszintű ágai különválasztják a `+0x3b8 != 0` Időrend-ágat a nulla módtól; utóbbiban a `+0x3bb` újabb elágazást ad, és a `+0x3bb==0` bal/fel út `+0x3f4` mezőt módosít. A minden állapotra vonatkozó feltevés cáfolva. A cáfoló ellenőrzés külön elolvasta a két célfüggvényt: `0x00802ae0` írja a `+0x3f4`-et, `0x00802a90` nem. Ez a felhasználói látványt nem azonosítja.

**Bizonyítottsági fok: feltételes.** A mód- és jelzőfüggő gépi híváságakat az utasítások rögzítik; a teljes egérvezérlő név szerinti kötése, az `+0x310` szemantikája, a `+0x3f4` felhasználói hatása és a látható mozgás futásidejű megerősítése hiányzik.

**A #5401 „Kész, ha” állapota.** A 3. pont (vezérlők) részben teljesült: a koordináta-skálázás, az egér húzás/felengedés hívásútja és a mód-/jelzőfüggő nyílágak statikusan le vannak írva. A `timelinedot`, `sliderthumb`, `startbutton`, listaikon, dátumtömb, automatikus léptetés üteme és a teljes felhasználói működés továbbra is nyitott. A 1., 2. és 4. pontot ez a rész nem zárja le.

##### §4 Nyitott

- Mérés szükséges annak megállapításához, hogy a `+0x428`/`+0x429` jelzők és a `[this+0x310]` melyik képernyőelemhez, illetve milyen látható változáshoz tartoznak.
- A `0x007fd770` indexmódosító hatása és a `+0x514` érték jelentése futás közben nincs megmérve.
- A qshow módjelző, a nyílbillentyűk útja és a húzás viselkedésének QEMU-/Wine-ellenőrzése nem készült.

**Új kutatási jegyjavaslat.** Nincs; ezek továbbra is a #5401 vezérlő-elfogadási pontjához tartoznak.

#### 38.2.67 Az első Space-ág aktív objektumcseréje és callbackjei (#5401, 2026-10-22)

**Hatókör.** A 38.2.65-ben nyitva maradt `0x009833a0` host-callback út céljait az eredeti PE vtable-adataival és a callbackek helyi diszasszemblyével ellenőriztem. Ez a kör a statikus objektumcserét zárja le; a látható diavetítést és az Escape utáni folytatási pozíciót nem méri.

##### §1 A qshow és a OneUpUI közti hostcsere

A friss Időrendben a `[this+0x3bb]` nulla (`0x007fda00`, 38.2.9). A `0x00801130` ezt 1-re állítja (`0x00801134`-`0x0080113f`), majd a `0x00802c20`-at hívja (`0x00801157`-`0x00801159`). A `0x00802c20` a negatív `[this+0x3f4]` értéket nullázza, meghívja a `0x00802830`-at, és ha az nulla eredményt ad, valamint a `[this+0x50]` hostmező nem nulla, a `[this+0x2dc]` objektumot adja át a `0x009833a0`-nak gazdaablak-váltásra (`0x00802c20`, `0x00802c2e`-`0x00802c50`). A feltételes `0x00aa6f40` hívás a hostcsere után következik (`0x00801167`-`0x0080116a`).

A `[this+0x2dc]` objektum a `0x00802c60` konstruktor által létrehozott `OneUpUI` (mérete `0x268`, vtable `0x00cbd5c4`); a konstruktora `[OneUpUI+0x25c] = QDrawable` kapcsolatot ír (`0x007fae32`-`0x007fae55`, `0x00802c60`, 38.2.21 §4). A qshow maga a `QDrawable` (`0x00cbd66c`, 38.2.15 §2).

A hostcsere feltétele a `0x00802830` visszatérése. Ez a `[qshow+0x3f0] >> 1` elemszámot ellenőrzi: nulla elemszámnál `4`-et ad; különben a `[qshow+0x3f4]` kijelölt indexet `[0, darab-1]` közé szorítja, az aktuális `[qshow+0x3ec + index*4]` listaelem mutatóját átadja a `0x00802ec0`-nak, majd annak eredményét adja vissza (`0x00802830`, `0x00802831`-`0x00802845`, `0x00802846`-`0x0080286a`, `0x00802954`-`0x0080297b`). A `0x00802ec0` ezt a mutatót az `OneUpUI+0x258` mezőbe írja (`0x00802ec0`, `0x00802ecb`); a OneUpUI felépítésének hibájára `4`, sikerére `0` a visszatérés. Ezért a `0x00802c20` csak nem üres listánál, sikeres OneUpUI-felépítésnél és nem nulla gazdaablak-mutatónál hívja a `0x009833a0`-at. A qshow-listaelem → `OneUpUI+0x258` adatfolyam egy statikus úton **feltételesen** igazolt; hogy a descriptor pontosan milyen képfájlt/puffert jelenít meg, **NINCS MEG**.

A `0x009833a0` a host `[+0x64]` aktív objektumát a kapott mutatóra állítja, a régi és az új objektum vtable `+0x28` slotját hívja, majd `0x00983430`-at futtatja (`0x009833a0`, `0x00983430`). Így a feltételek teljesülésekor az aktív qshow gazdaablak-tartalom a qshow `QDrawable` objektumáról a hozzá tartozó `OneUpUI` objektumra vált.

##### §2 A vtable-callbackek céljai

| Objektum | Vtable slot | Cél a PE-ben | Közvetlen mezőhatás |
|---|---:|---:|---|
| `QDrawable` | `+0x28`, slotcím `0x00cbd694` | `0x007fa480` | A `+0x50` mezőbe írja a kapott szülőablakot; nem nulla szülőnél a `0x00aa67f0`-et is hívja. |
| `OneUpUI` | `+0x28`, slotcím `0x00cbd5ec` | `0x00a6cd00` | A `+0x50` mezőbe írja a kapott szülőablakot. |

A vtable-slot értékeit az eredeti PE nyers bájtjaiból `pefile`-lal olvastam ki, és egyeznek a bináris-index RTTI-adatával (`QDrawable::vftable` `0x00cbd66c`; `OneUpUI::vftable` `0x00cbd5c4`). A két callback diszasszemblye közvetlenül ellenőrzi a fenti mezőírásokat (`0x007fa480`, `0x00a6cd00`). A host `0x00983430` méret-/újrarajzolási útja mindkét vtable `+0x20` slotjának közös `0x00a6cd10` célját éri el; ez a szülő HWND méretét olvassa, majd az objektum `+0x38` slotját hívja. A `OneUpUI` `+0x38` célja `0x00a56800`.

A `0x00801130` ezen az ágon az `ESI`-t a qshow `+0x58` címére állítja, majd a `0x00aa6f40`-et hívja. Ez a függvény a lebegőpontos vezérlőszót elmenti; ha `[qshow+0x2c4]` és `[qshow+0x2bc]` is nem nulla, a `[qshow+0x2c4]` objektum vtable `+0x84` slotját hívja ezekkel az argumentumokkal: `(objektum, 0, qshow+0x2bc, 0, 0x200, 0)`. Negatív visszatéréskor `4`, különben `0` a függvény eredménye; mindkét ág visszaállítja a mentett lebegőpontos vezérlőszót (`0x00aa6f40`, `0x00801130`). A függvény saját törzse nem írja a qshow `+0x3b8`/`+0x3bb` mezőit, de a virtuális cél és a két pointer futásidejű értéke nincs meg.

##### §3 Független utak, cáfoló kísérlet és bizonyítottság

**A út - vezérlési út.** A `0x00801130` állapotírása és hívása, a `0x00802c20` feltételes gazdaablak-váltása, valamint a `0x009833a0` `[host+0x64]` pointerírása megadja az aktív objektum cseréjét. A `0x007fa7f0`/`0x00802c60` konstruktori útja azonosítja a régi `QDrawable` és az új `OneUpUI` objektumot.

**B út - PE-adat és külön callback-olvasat.** Az eredeti PE vtable két nyers `+0x28` bejegyzése `0x007fa480` és `0x00a6cd00`; a hozzájuk tartozó külön diszasszembly a szülőmutató `+0x50` írását mutatja. A `0x009833a0` közvetlen utasításai ugyanazt a két slotot hívják a régi, illetve az új host-objektumon. A két út a callback-célban és az objektumcserében egyezik.

**Cáfoló kísérlet.** Azt a szűk állítást próbáltam cáfolni, hogy a `0x009833a0` callback maga törli a qshow `+0x3b8` vagy `+0x3bb` módmezőjét. A teljes 55 bájtos függvényben a közvetlen írások a host `[+0x3b]` és `[+0x64]` mezőit érik; a két `+0x28` cél a saját objektum `[+0x50]` mezőjét írja. A nyers PE helyértékek és a két callback diszasszemblye ezt külön úton ellenőrzi, ezért a közvetlen mezőtörlési feltevés cáfolva. Ez nem zárja ki a `0x00aa67f0`, a `0x00a56800` vagy a `0x00aa6f40` út esetleges közvetett hatását; ezek felhasználói és állapotbeli hatása továbbra sincs meg.

**Bizonyítottsági fok.** **Megerősített** a feltételes host-objektumcserére és a két `+0x28` callback céljára: a híváslánc, az eredeti PE vtable-adat és a célfüggvények utasításai egyeznek. **Feltételes** a qshow-listaelem `OneUpUI+0x258` mezőbe kötése: egyetlen statikus adatút támasztja alá. A látható „diavetítés” megnevezés és a ténylegesen megjelenő kép **NINCS MEG**; ehhez futó qshow-mérés kell.

**A #5401 „Kész, ha” állapota.** (1) ⛔ A forráshalmaz, sorrend, gyűjteményenkénti darabszám és képlista változatlanul nyitott. (2) ⛔ A teljes képkockánkénti pálya, rétegsorrend és háttérrajz nyitott. (3) ⛔ A Space egyik állapotágának objektumcseréje ismert; a vezérlők, dátumtömb és automatikus lépés teljes működése nyitott. (4) ⛔ A Space sikeres első ága statikusan a `QDrawable` → `OneUpUI` gazdaablak-cseréhez vezet; az élő diavetítés, Escape utáni nézet és folytatási kép/index nincs mérve.

**Nyitott.**

- Ghidra-kör kell: 0x00aa6f40: a [qshow+0x2c4] objektum vtable `+0x84` céljának osztálya/hatása, a [qshow+0x2bc] argumentum forrása, és érinti-e a `+0x3b8`/`+0x3bb` állapotot [blokkoló]
- Ghidra-kör kell: 0x00a56800: a OneUpUI vtable `+0x38` célfüggvény teljes viselkedése, a belső callbackek és a qshow-állapotra gyakorolt hatás [blokkoló]
- Ghidra-kör kell: 0x00a5e850: a `0x00802ec0` hívási útjában betöltött szerepe; az `+0x3b8` mező, valamint a `0xa5d6b0`/`0xa5db30` hívások hatása, és hogy ezek kapcsolják-e a kiválasztott listaelemet a OneUpUI megjelenítéséhez [blokkoló]
- Élő qshow-mérés kell a tényleges képtartalom, a teljes képernyős diavetítés és az Escape utáni gyűjtemény/kép-index rögzítésére.

**Új kutatási jegyjavaslat.** Nincs; ezek továbbra is a #5401 elfogadási pontjai.

#### 38.2.68 Az `EnumThreadWindows` kilépési callbackje: a `ytWindow` ág kihagyása (#5401, 2026-10-22)

**Hatókör.** A 38.2.64 kilépési útját pontosítja a `0x00983270` és a callback `0x00982fa0` helyi diszasszemblye. A híváságak statikusak; a ténylegesen kiválasztott HWND és az Időrendbe való visszatérés nincs megmérve.

A `0x00983270(this, 0)` először a `[0x00d67858]` értékét vizsgálja. Ha kisebb mint 1, `PostMessageA(this+0x6c, 0x10, 0, 0)`-t hív, majd visszatér. Egyébként `[0x00d6784b]=1` után az aktuális szál ablakain futtatja a `0x00982fa0` callbacket, `lParam=0` értékkel (`0x00983270`, `0x0098328b`-`0x009832c4`; a `0x10` üzenet a WM_CLOSE értéke).

A callback a `GetWindow(hwnd, 4)` eredményét kéri le (`0x00982fa0`, `0x00982fa7`-`0x00982fae`; USER32 IAT `0x00c406f4`). Nulla eredménynél 1-et ad vissza. Nem nulla eredménynél az eredményt a callback `lParam`-jával veti össze; ha az nulla, a célértéket `[0x00d6784c]`-ből veszi. Eltéréskor szintén 1 a visszatérés. Egyezéskor a `GetClassNameA` eredményét a `0x00c7f35c` címen levő `ytWindow` literállal hasonlítja össze: egyezéskor 1-et ad vissza, eltéréskor `SendMessageA(hwnd, 0x10, 0, 0)`-t hív, majd 0-val tér vissza (`0x00982fa0`, `0x00982fc9`-`0x0098307f`; USER32 IAT: `GetClassNameA` `0x00c40800`, `SendMessageA` `0x00c40884`). A kód tehát ezen az enumerációs ágon nem küld közvetlenül WM_CLOSE-t a `ytWindow` nevű osztályú ablaknak. A `[0x00d6784c]` futásidejű értéke és az érintett ablakazonosság **NINCS MEG**.

**Két út és cáfoló kísérlet.** A út: a `0x00982fa0` utasításai megadják a visszatérési ágakat, az összehasonlított literált és az üzenetküldés helyét. B út: a `0x00983270` Ghidra-dekompilátuma külön megerősíti az aktuális szál ablakainak enumerálását, a callback címét és a nulla `lParam`-ot; a PE importtáblája a három USER32 IAT-helyet, a sztringadat pedig a `ytWindow` literált erősíti meg. B részleges ellenőrzés, nem ad önálló második levezetést a callback minden ágára, ezért a teljes callback-viselkedés bizonyítottsági foka **feltételes**.

Cáfoló kísérletként azt vizsgáltam, hogy a callback az egyező `ytWindow` osztályú ablaknak küldi-e a WM_CLOSE-t. A feltételezett ágat a `0x00983031`-`0x0098305b` literál-összehasonlítás és visszatérés cáfolja: az egyezés 1-et ad; az üzenetküldés a `0x00983064`-`0x0098307f` eltérési ágon van. A literál címét és az IAT-célokat a PE adatai külön ellenőrzik. Ez csak a callback ezen útját cáfolja, nem zárja ki, hogy más útvonalon a qshow bezáródjon.

**A #5401 „Kész, ha” állapota.** (1) ⛔ A forráshalmaz, sorrend és képlista nyitott. (2) ⛔ A teljes képkockamozgás és rétegrajzolás nyitott. (3) ⛔ A vezérlők teljes működése nyitott. (4) ⛔ Az egyik `param2=0` kilépési ág statikus callback-viselkedése pontosabb lett; a tényleges bezárás, az Escape utáni nézet és a folytatási kép/index továbbra sincs igazolva.

**Nyitott.** A `[0x00d6784c]` futásidejű értéke, az enumerált ablakok közül ténylegesen érintett HWND, a küszöb alatti `PostMessageA` ág felhasználói hatása, valamint az Időrendből való visszatérés és a folytatási index **NINCS MEG**. A szükséges további bizonyíték a futó qshow sűrű képkocka- és ablakállapot-felvétele; új Ghidra-kör ebből a callbackből nem szükséges.

**Új kutatási jegyjavaslat.** Nincs; a nyitott futásidejű kérdések a #5401 elfogadási pontjai.

#### 38.2.69 A `CThumbUI+0x2c0` objektuma `CAlbumState` (#5401, 2026-10-22)

**Hatókör.** Ez a kör a `CThumbUI+0x2c0` mező típusát azonosítja, és elválasztja a `+0x2bc` `CThumbDB` szolgáltatótól. A CAlbumState mögötti konkrét képhalmazt, annak rendezését és a qshow descriptor-sorozatához való viszonyát nem állapítja meg.

**A út - hívó és argumentum-adatfolyam.** A `0x004051b0` ugyanazt az `ESI` objektumot adja át a `0x00402f90`-nek (`0x004058ee`-`0x004058ef`), majd a `0x004039f0`-nek (`0x0040590d`-`0x0040590e`). A `0x00402f90` a `[X+0x1030]` hiányakor `0x448` bájtot foglal, meghívja a `0x004a1560` konstruktort, és annak eredményét a `[X+0x1030]` mezőbe írja (`0x00402fe2`-`0x00403016`). A `0x004039f0` a `0x005643e0` hívása előtt az `[X+0x1030]` értékét a verembe teszi a `0x00403da4`, `0x00403db4`-`0x00403db8` utasításokkal. A konstruktor `0x005643e0` a második stack-argumentumot a `[this+0x2c0]` mezőbe, a harmadik argumentumot a `[this+0x2c4]` mezőbe írja (`0x005644dd`-`0x005644fa`, `0x0056461c`). Az első argumentumot külön az `EAX`-ből a `[this+0x2bc]` mezőbe teszi (`0x005643f0`, `0x00564616`). A stack-eltolás feloldását a konstruktorban meghívott `0x00a518b0` `ret 4` utasítása (`0x00a51bb2`) ellenőrzi: az előtte betett nulla argumentumot a hívott rutin takarítja le, így a `[esp+0x68]` a `0x004039f0` második argumentumára, azaz `[X+0x1030]`-ra mutat.

**B út - típusazonosítás.** A `0x004a1560` konstruktor a `[this]` mezőbe `0x00c8368c`-t írja (`0x004a1588`). Az eredeti bináris RTTI-/vtable-indexe ezt a címet `CAlbumState::vftable`-ként nevezi meg. Ez az A út pointerláncától független típusbizonyíték: a `CThumbUI+0x2c0` tehát `CAlbumState` objektumra mutat. A `[X+0x1034]` mező külön, a `0x00415790` konstruktorral jön létre, és a `0x00402fdc` címen kerül eltárolásra; a korábbi 38.2.63 szerint ebből lesz a külön `CThumbUI+0x2bc` `CThumbDB` szolgáltató.

A `0x004a0980` a `CThumbUI::MakeTimeline`-ből kapott `CAlbumState` pointerrel fut (`0x005e9434`), és a `[state+0x13c] >> 1` értéket adja vissza (`0x004a09c5`-`0x004a09e9`, illetve `0x004a0a01`-`0x004a0a15`). Ez a MakeTimeline ciklusának számbeli felső határát adja, de önmagában nem nevezi meg az elemeket vagy a mező szemantikáját. A konstruktor `Preferences\datesort`, `Preferences\peoplesort` és `Preferences\albumlistflip` kulcsokat is olvas (`0x004a195f`-`0x004a1a1d`); a binárisban eddig nincs bizonyíték arra, hogy ezek közül melyik, vagy bármelyik, a qshow képeinek sorrendjét állítaná.

**Cáfoló kísérlet.** Azt az egyszerűsítő feltevést próbáltam cáfolni, hogy a `CAlbumState` azonosítása önmagában azt jelenti: a qshow ennek dátum szerint rendezett albumlistáját jeleníti meg. A számlálóút a CAlbumState `+0x13c` mezőjéből ad eredményt (`0x004a0980`); az indexelt elemkérés viszont a `CThumbUI+0x2bc` külön `CThumbDB` objektumának `+0x20` virtuális helyére jut (`0x00562cc0`). A `CThumbDB::vftable` `0x00c81f78` nyers PE-bejegyzésének `+0x20` célja `0x00423300`. Ez a külön számláló- és elemszolgáltató út cáfolja, hogy a két objektum szerepét egyetlen „albumlista” mezőként lehetne leírni; a CAlbumState és a qshow tényleges képsorrendje közti kapcsolatot viszont nem cáfolja és nem is bizonyítja. A vtable-célt a nyers PE-ből, az osztályneveket az index RTTI-táblájából külön ellenőriztem.

**Bizonyíték és bizonyítottsági fok.**

| Állítás | Forrás |
|---|---|
| A `CThumbUI+0x2c0` pointere a hívó `[X+0x1030]` mezőjéből származik. | bináris (`0x004051b0`, `0x00402f90`, `0x004039f0`, `0x005643e0`, `0x00a518b0`) |
| A `[X+0x1030]` objektum `CAlbumState`. | bináris (`0x004a1560`, vtable-írás `0x004a1588`) + RTTI (`0x00c8368c`) |
| A `CThumbUI+0x2bc` mező külön `CThumbDB` szolgáltató; annak vtable `+0x20` célja `0x00423300`. | bináris (`0x00402f90`, `0x00415790`, `0x00562cc0`) + RTTI/PE (`0x00c81f78`) |
| A MakeTimeline számlálóút a `[CAlbumState+0x13c] >> 1` értéket kapja. | bináris (`0x005e9434`, `0x004a0980`) |
| A dátum-/emberrendezési beállítások bizonyítják a qshow képsorrendjét. | NINCS MEG |
| A CAlbumState elemlistája, a qshow descriptor-sorozat és a tényleges képek azonossága. | NINCS MEG |

**A két független út.** A út: ugyanaz a hívóobjektum megy át a `0x00402f90` és a `0x004039f0` útvonalon; `+0x1030` a CAlbumState-konstruktorból származik, és a CThumbUI-konstruktor második argumentumaként a `+0x2c0` mezőbe kerül. B út: a CAlbumState-konstruktor elsődleges vtable-írását (`0x004a1588`) az eredeti bináris RTTI-je `CAlbumState`-ként nevezi meg. A pointerlánc és a típus egyezik; a forráshalmaz és a rendezés nem következik belőlük.

**A #5401 „Kész, ha” pontjai.** (1) ⛔ Részben előrehaladt: a `+0x2c0` osztálya és a számláló mező kifejezése ismert; a forráshalmaz, az upstream sorrend, a konkrét képek és a képszám szemantikája nyitott. (2) ⛔ A teljes képkockánkénti pálya, időgörbe és rajzolási rétegek nyitottak. (3) ⛔ A vezérlők teljes működése és a dátumcsúszka leképezése nyitott. (4) ⛔ A diavetítésbe lépés utáni visszatérési nézet és képpozíció nyitott.

**Nyitott.**

- Ghidra-kör kell: 0x004a1560 - a `CAlbumState+0x13c` mező írója/forrása, a kategóriaelemek és a rendezési mezők közti kapcsolat, valamint hogy ezek határozzák-e meg a MakeTimeline elemszámát vagy sorrendjét [blokkoló]
- Ghidra-kör kell: 0x00423300 - a `CThumbDB` vtable `+0x20` indexelt elemszolgáltatójának pontos képforrása, sorrendje és kimenete [blokkoló]
- Ghidra-kör kell: 0x004b0190 - a qshow descriptor-sorozat forrása és rendezése, valamint kapcsolata a `CAlbumState`/`CThumbDB` útvonallal [blokkoló]
- A dátumcsúszka, `timelinedot`, `sliderthumb`, automatikus léptetés üteme, teljes animáció és Space/Escape utáni folytatási pozíció továbbra is a #5401 nyitott kérdése.

**Új kutatási jegyjavaslat.** Nincs; a fenti kérdések a #5401 négy elfogadási pontjához tartoznak.

#### 38.2.70 A rétegelt gombok kattintási területe, a hívási út és a CThumbDB következő szintje (#5401, 2026-10-22)

**Hatókör.** A qshow overlay-konstruktorát (`0x007fb210`) az eredeti PE utasításaival vetettem össze a találati kezelő (`0x007fda80`) és a hívott átmenet-segédek helyi diszasszemblyével. A statikus erőforrás→objektummező→híváslánc megvan a négy találati gombnál; a callback felhasználói hatása, a teljes képsorrend és a látható mozgásirány nem következik ebből.

**Overlay és találati út.** A `0x007fda80` csak akkor vizsgálja a négy találati téglalapot, ha `[qshow+0x3b8] != 0`. A bemeneti pont a `0x007fde80` által belső qshow-koordinátává alakított `[+0x420,+0x424]`. A `0x007fda80` összehasonlításai az x-tengelyen `X+0x18 <= x < X+0x18+(X+0x08)`, az y-tengelyen `X+0x1c <= y < X+0x1c+(X+0x0c)` tartományt vizsgálják (például startbutton: `+0x750 <= x < +0x750 + +0x740`, `+0x754 <= y < +0x754 + +0x744`; `0x007fda90`-`0x007fdb06`). Eszerint az overlay objektum-alapjához képest `+0x18` az x-kezdőpont, `+0x1c` az y-kezdőpont, `+0x08` az x-kiterjedés és `+0x0c` az y-kiterjedés. Az alsó szélek benne vannak, a felsők kívül esnek a találaton; ez az x87 összehasonlítási sorrendjéből és az utána következő feltételes ugrásokból adódik.

| Erőforrás (`0x007fb210`) | objektum-alap | találati téglalap | találatkor futó bináris út |
|---|---:|---|---|
| `overlays/startbutton` | `qshow+0x738` | bal `+0x750`, felső `+0x754`, szélesség `+0x740`, magasság `+0x744` | `0x007fb820`, majd ha `[qshow+0x2e8] != 0`, annak vtable `+0x18` slotja; a veremargumentumok `-1`, majd az aktuális `[qshow+0x3ec + qshow+0x3f8*4]` elem, negatív indexnél `0` (`0x007fdb08`-`0x007fdb3d`). |
| `overlays/exit` | `qshow+0x580` | bal `+0x598`, felső `+0x59c`, szélesség `+0x588`, magasság `+0x58c` | `0x007fb820` (`0x007fdbc0`-`0x007fdbc2`). |
| `overlays/right` | `qshow+0x558` | bal `+0x570`, felső `+0x574`, szélesség `+0x560`, magasság `+0x564` | `0x007fd150`; a segéd a `[qshow+0x328]` érték ellentettjét és a bináris `0x00cf3a48` címen levő `2.0f` értéket adja a `0x007fd0c0`-nak (`0x007fdc48`, `0x007fd150`-`0x007fd16e`). |
| `overlays/left` | `qshow+0x530` | bal `+0x548`, felső `+0x54c`, szélesség `+0x538`, magasság `+0x53c` | `0x007fd120`; a segéd a `[qshow+0x328]` értéket és a bináris `0x00cf3a48` címen levő `2.0f` értéket adja a `0x007fd0c0`-nak (`0x007fdcd4`, `0x007fd120`-`0x007fd13c`). |

A `0x007fd0c0` mindkét irányból hívja a `0x009a5210` időfüggvényt, majd a `0x009e6010` tárolófrissítőt. A bal/jobb ág átadott előjele bizonyított; hogy ez a kártyák látható mozgásában melyik képernyőirányt jelenti, **NINCS MEG**. A `startbutton` a `0x007fb820` kilépési útját is meghívja, utána pedig az `[qshow+0x2e8]` érték vtable `+0x18` slotját. A `CThumbUI::MakeTimeline` (`0x005e8a70`) a bemeneti struktúra `+8` mezőjét a `CThumbUI+0x27c` alobjektum címével tölti (`0x005e971b`-`0x005e973d`). A qshow építője ezt a struktúrát adja át a qshow-konstruktornak (`0x008037e0`, `0x008038d2`, `0x0080391e`-`0x00803920`); a konstruktor a `+8` értéket a `[qshow+0x2e8]` mezőbe másolja (`0x007fa7f0`), majd ugyanezt az értéket harmadik paraméterként átadja a `OneUpUI` konstruktorának (`0x00802c60`), amely saját `+0x260` mezőjében tárolja. A `CThumbUI+0x27c` alobjektum osztálya/vtáblája és a vtable `+0x18` célfüggvénye **NINCS MEG**. Ez a statikus adatút önmagában nem bizonyítja, hogy a gomb ugyanazt teszi, mint a szóköz vagy a OneUpUI `auto` parancsa.

A `timeline` (`qshow+0x6c0`) és a `sliderthumb` (`qshow+0x710`) téglalapja az egérkezelőben külön húzási útra jut (`0x007fde80` → `0x007fdd00`, felengedéskor `0x007fd770`; 38.2.63 és 38.2.66). A `0x007fda80` négyes találati listájában nincs `timelinedot` (`qshow+0x6e8`) ág. A `timelinedot`, a listaikon és az ismeretlen `[qshow+0x2e8]` callback eredménye továbbra is **NINCS MEG**.

**A képhalmaz szolgáltatója: további helyi adatút, eredmény nélkül.** A `CThumbDB::vftable` nyers PE `+0x20` slotja `0x00423300` (38.2.69). E függvény `0x0042336c`-`0x00423385` között a saját `+0x48` alobjektumának vtable `+0x2c` slotját hívja. A `0x00415790` konstruktor `0x00415804` utasítása ezt a mezőt `0x00c81fa4`-re állítja; az eredeti PE vtable e címének `+0x2c` slotja `0x004406f0`. A `0x00423300` további útja a `0x00423500`-hoz jut (`0x004236dd`-`0x004236ef`). A `0x00423500` helyi diszasszemblye (632 bájt) megerősíti a `+0x48` alobjektum `+0x2c` virtuális hívását (`0x00423521`-`0x00423538`); az egyik ága meghívja a `0x00423780`-at (`0x004236dd`-`0x004236ef`), és e hívás nulla visszatérésekor a `0x006c9d60` és `0x004115c0` következik (`0x004236fa`-`0x00423715`). A `0x00423780` helyi diszasszemblye indexelt tömbön jár végig (`[arg+4] >> 1`, `0x00423780`-`0x00423862`) és `0x28` bájtos cellákkal növeli a segédpuffert (`0x004238cd`-`0x00423968`). E mezők és rekordok szemantikája, a forráskollekció és a rendezési kulcs **NINCS MEG**. A `0x004406f0` a hívott objektumhoz képest `+0xaa8`-at hozzáad (`0x00440753`), majd az így elért `this+0xb00` listamezőt használja indexeléshez (`0x00440797`-`0x004407b4`), és karakterlánc-feldolgozó segédeket hív (`0x004407dd`-`0x00440817`). Ez nem azonosítja a qshow-ban megjelenített képeket. A CAlbumState számlálóútja (`0x004a0980`) és ez az indexelt CThumbDB-szolgáltató ezért továbbra sem egyesíthető bizonyított képlánccá.

**A két független út.** A út: a `0x007fb210` az overlay erőforrásneveket a qshow mezőeltolásaihoz rendeli. B út: a külön `0x007fda80` találati függvény alsó határként használja az `X+0x18`/`X+0x1c` értéket, ezekhez adja az `X+0x08`/`X+0x0c` kiterjedést, és az így képzett téglalapokhoz közvetlen hívásokat rendeli. A nyers mezőeltolásokat és az eseménycélokat e két út egyezése rögzíti; a respack külön jegyzéke megerősíti a `left`, `right`, `exit`, `timeline`, `timelinedot`, `sliderthumb` és `startbutton` erőforrásneveket, a `0x007fde80` pedig külön húzási útban kezeli a timeline és sliderthumb mezőket. Az overlayek felhasználó által látott következménye, a forráshalmaz és az animációs irány nem következik a két útból.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy az `overlays/startbutton` közvetlenül az `auto`/szóköz út szinonimája. A startbutton hit találatkor `0x007fb820`-at és az `[qshow+0x2e8]` vtable `+0x18` hívását futtatja (`0x007fda80`); a qshow billentyű/Auto ág ezzel szemben a `0x00803110` útvonalon módosítja a `[qshow+0x3bb]` jelzőt (38.2.65-67). A két közvetlen hívási út eltér, ezért a közvetlen azonosság cáfolt. A `[qshow+0x2e8]` callback esetleges közvetett autoplay-hatása nyitott marad. Külön cáfoló körben azt is ellenőriztem, hogy a betöltési operandusok sorrendjéből adódó fordított címkézés (`+0x08/+0x0c` = kezdőkoordináta, `+0x18/+0x1c` = kiterjedés) helyes lehet-e. A friss, vak diszasszemblálási ellenőrzés a `fild`/`fcompp` veremrendet és a feltételes ugrásokat végigkövetve ezt cáfolta: a kód az `X+0x18`/`X+0x1c` alsó határt hasonlítja a koordinátával, majd hozzáadja az `X+0x08`/`X+0x0c` kiterjedést; az eredmény `[alsó, felső)`.

**Bizonyítottsági fok.** **Megerősített** a négy erőforrás mezőeltolása, a félig nyitott találati tartománya és közvetlen hívási útja: az overlay-konstruktor, a találati függvény, a cél-segédek utasításai és a vak, független diszasszemblálási ellenőrzés egyezik; az erőforrásjegyzék külön ellenőrzi a neveket. **Feltételes** a startbutton callback felhasználói jelentése és a bal/jobb átadott előjel képernyőn látható iránya. **Nyitott** a CThumbDB-adat útja, az időrendi képlista, a timelinedot és a listaikon működése.

**A #5401 „Kész, ha” pontjai.** (1) ⛔ A CAlbumState számlálási és CThumbDB indexelt szolgáltatói útja szűkebb lett, de a forráshalmaz, rendezés, képek és darabszámok nyitottak. (2) ⛔ Az előző körök kártyagörbe- és képkocka-transzformációs eredményei részlegesek; a teljes mozgáspálya, időgörbe, háttér és rétegsorrend nyitott. (3) ⛔ A bal/jobb/exit/startbutton statikus hívásai, valamint a slider húzási útja pontosabb; a dátumleképezés, timelinedot, listaikon, callback-hatás és autoplay teljes működése nyitott. (4) ⛔ A Space objektumváltásának statikus ága ismert (38.2.67), de a tényleges diavetítés, kilépés utáni nézet és visszaállított képindex nincs megmérve.

**Nyitott.**

- `Ghidra-kör kell: 0x00423500 - a CThumbDB indexelt lekérdezésének nemnulla útja; a már meglévő 0x00423300 és 0x004406f0 dekompilációval együtt az elemrekord, a forráskollekció és a qshow képlánc upstream sorrendjének azonosítása [blokkoló]`
- `Ghidra-kör kell: 0x00423780 - a CThumbDB lekérdezésből kapott indexelt rekordok mezői, a 0x28 bájtos segédrekord szerepe és kapcsolata a qshow képhalmazával [blokkoló]`
- `Ghidra-kör kell: 0x006c9d60 - a CThumbDB fallback ág által előállított érték jelentése és az 0x004115c0 felé továbbított rekord kapcsolata a qshow-listához [blokkoló]`
- `Ghidra-kör kell: 0x005e8a70, 0x008037e0 - a CThumbUI+0x27c címen lévő alobjektum osztálya/vtáblája, a vtable +0x18 callback célfüggvénye és felhasználói hatása [blokkoló]`
- A `timelinedot`, listaikon, dátumcsúszka-leképezés, teljes képkockánkénti pálya és a futás közbeni képsorrend továbbra is nyitott; utóbbiakhoz a futó qshow mérési felvétele szükséges.

**Új kutatási jegyjavaslat.** Nincs; a nyitott pontok mind a #5401 elfogadási feltételeihez tartoznak.
