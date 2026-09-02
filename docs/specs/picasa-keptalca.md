# A Képtálca (Picture Tray / „Selection") — MŰKÖDÉS-spec

*Kutatói kör: 2026-08-24. Jegy: **#455** (a Klipek fül, **#1153**, erre épül).*

A Picasa alsó sávjának bal oldalán ülő **gyűjtő-munkaterület**. Belső neve
**`scratch`**, a felületen megjelenő felirata **„Selection"**. Ez a lap a
**működést** írja le; a látvány a `design-guide.md`-ben van.

---

## 1. ⭐ A LEGFONTOSABB LELET: a tálca NEM MARAD MEG újraindítás után

Három független ellenőrzés, mind negatív:

| amit kerestem | hol | eredmény |
|---|---|---|
| `]scratch` (vagy bármi tálca-szerű) token | a felhasználó **valódi** `albumdata_token.pmp`-ja, **2371 sor** | **nincs.** Pontosan **hét** nem-`]album:` token létezik: `]star`, `]screensaver`, `]updated`, `]history:email`, `]history:upload`, `]unknownface`, `]search` |
| tálca-fájl | a valódi `Picasa2` profilmappa | **nincs** — csak `cache`, `db3`, `ioqueue`, `runtime`, `tmp` és két naplófájl |
| `Preferences\…` kulcs | a bináris teljes sztringtára | **nincs** tálca/hold/scratch témájú kulcs |

> ⛔ **A tálca tartalma memóriában él, és a program bezárásával elvész.**
> Ha a PicasaPy megőrizné, az **eltérés** lenne, nem javítás.

*Bizonyítottsági fok: **erős**. A hét token felsorolása és a profilmappa
tartalma megerősített (mért), a „nincs máshol" negatívum a sztringtár
teljességén áll.*

---

## 2. A vezérlők — és amiben a #455 leírása PONTATLAN

A `.tre` szerint a tálca **négy** vezérlőt hordoz. **A gombokon NINCS
felirat**: a `.tre`-ben a `#Label` sorok **ki vannak kommentezve**, tehát
ikon + súgóbuborék az egész.

| elem | `.tre` azonosító | felirat | súgó (EN) | súgó (HU) |
|---|---|---|---|---|
| a sáv címkéje | `thumbui/scratchlabel` | **„Selection"** (`Text`, 14-es font, középre) | — | — |
| megtartás | `thumbui/scratchhold` | **nincs** (kikommentezve) | *Hold selected items* | — |
| ürítés | `thumbui/scratchclear` | **nincs** (kikommentezve) | *Clear items from the selection* | — |
| albumhoz adás | `thumbui/addtobuttcon` | **nincs** (kikommentezve) | *Add selected items to an Album* | — |

⚠️ A **#455 „Kijelölés megtartása" / „Kijelölés eltávolítása" gombfeliratot**
említ. Ezek **nem gombfeliratok**, hanem a `Tray` **helyi menü** két
parancsának feliratai (ld. 3.).

### 2.1 Geometria — kényszerekből, nem respackből

A tálca dobozát a `.tre` kényszerei adják (a respackben csak az **ikonok**
vannak: `scratchhold_icon` 468 b, `scratchclear_icon` 593 b,
`addto_arrow` 53 b, `#holdadorner` 438 b):

```
thumbui/scratchback : thumbui/basecontrolset   m_offsetB
    XConstraint 0, 0,    5        ; balról 5 px
    XConstraint 1, .365, -15      ; az alsó sáv szélességének 36,5%-áig, −15 px
thumbui/scratch     : thumbui/scratchback      ; a bélyegkép-sáv
    XConstraint 0,0,5 · XConstraint 1,1,-50    ; jobbról 50 px HELY A KÉT GOMBNAK
    YConstraint 0,0,5 · YConstraint 1,1,-5
thumbui/scratchhold , thumbui/scratchclear : thumbui/scratchback
    m_buttontypecolor · m_offsetRT             ; jobb-felső horgony
thumbui/scratchpadbase : thumbui/scratchback   m_offsetLRB
thumbui/scratchlabel   : thumbui/scratchpadbase  m_displayfont14 · m_centerXY
```

⇒ **A tálca az alsó sáv bal 36,5%-át foglalja el**, és a jobb szélén 50 px
van fenntartva a két ikongombnak.

---

## 3. A `Tray` helyi menü — ~~PONTOSAN két parancs~~ **NYOLC SOR** (helyesbítve 2026-09-01)

⚠️ **Ez a szakasz korábban téves következtetést vont le.** Igaz, hogy a `Tray::`
névtérben **pontosan két** parancsazonosító van — de a tálca helyi menüje ettől
még **nyolc soros**: a másik öt tétel **más névterekből** öröklődik ide. A
névtér-számlálásból nem következik a menü hossza.

A menü-leíró tábla a **`0x00732ee0`** címen épül fel (egyszeri init, a
`0xda038c` bitjével őrizve; a bejegyzések a `0xd6edc0`-tól). Hívó: **`0x005e7d10`**.
A tételek a felépítés sorrendjében:

| # | parancsazonosító (cím) | EN (cím) | HU |
|---|---|---|---|
| 1 | `AlbumPhoto::ID_PICTURE_VIEW` (`0xcadb44`) | *&View and Edit* (`0xc8d8b8`) | **&Megjelenítés és szerkesztés** |
| 2 | `Tray::ID_PICTURE_HOLDINPICTURETRAY` (`0xcae618`) | *&Hold Selection* (`0xcae63c`) | **Kijelölés &megtartása** |
| 3 | `Tray::ID_REMOVE_SELECTION` (`0xcae5e4`) | *&Remove Selection* (`0xcae600`) | **Kijelölés &eltávolítása** |
| 4 | `AlbumPhoto::ID_PICTURE_ROTATECLOCKWISE` (`0xcadf04`) | *R&otate Clockwise* (`0xc8d7c4`) | — |
| 5 | `AlbumPhoto::ID_PICTURE_ROTATECOUNTERCLOCKWISE` (`0xcadbc0`) | *Rotate &Counterclockwise* (`0xc8d778`) | — |
| 6 | `FolderPhotoWin::ID_FILE_LOCATEONDISK` (`0xcadd5c`) | *&Locate on Disk* (`0xc8c520`) | **&Keresés a lemezen** |
| 7 | — | **elválasztó** (`CMenuBar::Enter`, `0xc8c4e4`) | — |
| 8 | `AlbumPhotoWin::ID_PICTURE_PROPERTIES` (`0xcadedc`) | *Propert&ies* (`0xc8d800`) | **T&ulajdonságok** |

**Nyitva:** a 4./5. tétel közös másodlagos mutatója (`0xc8d794`) és a 6. tétel
1-es jelzőbitje — a jelentésük **NINCS MEG**; a menü megépítéséhez nem kell.

Jegy: **#1917** (nálunk ma két tétel van, és a 2. felirata is rossz).

---

## 4. A KÉT — egymástól különböző — ürítés-megerősítés

A #455 egyet említ; **kettő van**, más szöveggel és más gombokkal:

### 4.1 Teljes ürítés

| kulcs | EN | HU |
|---|---|---|
| `IDS_CLEARTRAY` | *This will clear your entire tray. Are you sure you want to do this?* | **Ezzel a művelettel a teljes tálcát kiüríti. Biztosan ezt szeretné tenni?** |
| `IDS_CLEARTRAY_YES_BUTTON` | *Clear Tray* | **Törlés a tálcáról** |

### 4.2 A RÉGÓTA tartott elemek ürítése

| kulcs | EN | HU |
|---|---|---|
| `il_ClearFromTray` | *Would you like to clear your old held items from the tray?* | **El szeretné távolítani a tálcán régóta tárolt elemeket?** |
| `il_ClearFromTrayYesButton` | *Clear Tray* | **Törlés a tálcáról** |
| `il_ClearFromTrayNoButton` | *Don't Clear* | **Törlés mellőzése** |

⇒ A 4.2 **nem** a Törlés gomb megerősítése, hanem egy külön, **felkínált**
takarítás („régóta tartott" elemekre). A kettőt nem szabad összevonni.

## 5. Az őrfeltétel üzenete

| kulcs | EN | HU |
|---|---|---|
| `IDS_MUST_SELECT` | *You must have images in the Picture Tray to do this.* | **A művelet elvégzéséhez a képtálcán elemeknek kell lenniük.** |

*(Ne keverjük össze a hasonló `IDS_MUSTHAVESELECTION` /
`IDS_NEEDS_SELECTION` üzenetekkel — azok a **kijelölésre** vonatkoznak, nem
a tálcára.)*

## 6. A jelvény a rácsban — LEZÁRVA: a `#holdadorner` az adorner-CSALÁD tagja (2026-09-01)

`thumbui/#holdadorner` — a respackben **438 bájtos** réteg, mérete a
rétegfejléc szerint **10×10** (x 87…97, y 450…460 a tervezővásznon). A `#`
előtag a Picasa erőforrás-nyelvében a **kompozit/overlay** elemeket jelöli.

**Mire való?** A sztring (`0x00cad36c`) **egyetlen** helyről hivatkozott:
**`0x007145c0`**, ami az **adorner-képek gyorsítótárának** egyszeri feltöltője
(0x1b8 bájtos szerkezet, globális a `0xd676c0`-on; hívó `0x00714990`). A
betöltési sorrend és az eltolások:

| eltolás | erőforrás | cím |
|---:|---|---|
| **+0x00** | **`thumbui/#holdadorner`** | `0x00cad36c` |
| +0x28 | `adorners/shortcut` | `0x00cad384` |
| +0x50 | `adorners/star` | `0x00c878ec` |
| +0x78 | `adorners/web` | `0x00cad398` |
| +0xa0 | `adorners/geo` | `0x00cad3b8` |
| +0xc8 | `adorners/sync` | `0x00cad3a8` |
| +0xf0 | `adorners/suppress` | `0x00cad3c8` |
| +0x118 | `adorners/dirty` | `0x00cad3dc` |
| +0x140 | `adorners/movie` | `0x00cad3ec` |
| +0x168 | `adorners/people` | `0x00cad3fc` |

⇒ **Jelvény, nem elrendezési elem** — ugyanabból a családból, mint a csillag,
a geocímke vagy az arcfelismerés jelvénye. A jelentése a névből és a
parancstáblából (3. szakasz, 2. tétel) egybehangzó: a **„Kijelölés
megtartása"** állapotot jelöli a bélyegképen.

**Nyitva:** a jelvény pontos sarka a cellán belül — **NINCS MEG**. Megszerzés:
felvétel a felhasználótól egy „megtartott" tálcáról, vagy a rajzoló függvény
dekompilálása.

Jegy: **#1918** (nálunk nulla találat a `holdadorner`-re).

---

## 7. ✅ IGAZOLVA: a tálca alatti gombsor sorrendje

A #455 sorrendje **helyes** — a respack deklarációs sorrendje megerősíti:

```
print → email → export → shop(order) → hello(sharewith) → blog → collage → movie → morebutton
```

> ⚠️ **NEGATÍV EREDMÉNY, hogy a következő kör ne járja be újra:** a
> `buttons/core-lh2.pbz` (ZIP-archívum, benne kilenc `.pbf` XML) `<placement>`
> számai **MÁS** sorrendet adnak (webupload 1.0, ebutton 2.0, pbutton 3.0,
> folderbutton 4.0, orderbutton 5.0, blogger 6.0, collage 7.0, sharewith 9.0).
> **Ez nem az alap-elrendezés**, hanem a bővíthető gombok beszúrási rendje —
> pontosan ahogy a #455 „Pontosítás" bekezdése mondja. A `.pbz` alapján
> **ne** írjuk át a sorrendet.

A `.pbf` formátum egyébként dokumentálásra érdemes: `<button id=… type="static|dynamic">`,
`<placement>`, `<label>`, `<icon name=… src="runtime"/>`, `<tooltip>` +
**19 nyelvi változat** (`tooltip_hu` nincs köztük).

## 8. `trayexec` — a műveletsor ADATVEZÉRELT

A `0x005dc890` függvény sztringkörnyezete egy **deklaratív akció-rendszert**
rajzol ki: `action`, `foreach`, `trayexec`, `export`, `export_message`,
`uploader`, `provider`, `hybrid`, `hybridalbum`, `geolocate`, `country`,
`internal`, valamint a `Preparing images…` és az
`ExecuteAction::defaultmsg` üzenet.

⇒ A tálca alatti gombok **nem külön-külön drótozott** kezelők: nevesített
akciókat futtatnak, és a **`trayexec`** a hatókör, ami azt jelenti, hogy az
akció **a tálca tartalmán** dolgozik. Ez egybevág a #455 3. teendőjével.

*Bizonyítottsági fok: **erős** (sztringkörnyezet); a dispécser utasításszintű
végigkövetése nem történt meg.*

## 9. ⛔ NEGATÍV: a `Tray contains:` NEM felhasználói felület

A `<p>Tray contains:</p>` sztring a `0x004c8350`-ben ül, együtt ezekkel:
`text/html`, `<body border=40px>`, `<style>button {…}</style>`, `/uidebug`,
`/focusalbum`, `%s/thumb/%s.jpg?size=-%d`, `<p>Album list:<p/>`.

⇒ Ez a Picasa **beépített HTTP-s hibakereső lapja** (`/uidebug`), ami a
tálca tartalmát bélyegképekként listázza. **Fejlesztői eszköz — nem kell
megépíteni.**

---

## 10. Ami NYITVA marad (örökölt, a #455-ből)

1. ~~A „Hold Selection" és az „Add to Picture Tray" viszonya.~~ —
   ✅ **LEZÁRVA 2026-08-24, ld. 12.**
2. ~~A tálca mint fogd-és-vidd FORRÁS az Intéző felé.~~ —
   ✅ **LEZÁRVA 2026-08-24, ld. 14.** — igen, forrás; a programban
   **pontosan három** húzási forrás van.
3. ~~Mi számít „régóta tartott" elemnek (a 4.2 küszöbe).~~ —
   ✅ **LEZÁRVA 2026-08-24, ld. 13.** — **nem idő-alapú**, hanem
   darabszám-növekedés.

---

## 11. A műveletsor gombjainak MÉRT geometriája (2026-08-24)

A `respack.yt` rétegfejléceiből (`int16 x0,y0,x1,y1`), minden gombra
**azonos**:

| elem | x0,y0 | x1,y1 | méret |
|---|---|---|---|
| a gomb **cellája** (`outputlayout/docbounds`, `overflow`) | 0, 0 | 59, 40 | **59 × 40** |
| a **gomb** maga — mind a kilencre azonos: `button(print)`, `(email)`, `(export)`, `(shop)`, `(hello)`, `(blog)`, `(collage)`, `(movie)`, `buttcon(morebutton)` | **2, 2** | 57, 38 | **55 × 36** |
| elválasztó (`separator`) | 28, 8 | 30, 35 | **2 × 27** |

⇒ **Minden művelet-gomb 55 × 36 képpont, egy 59 × 40-es cellában** (2
képpont körbe). Az elválasztó 2 képpont széles, 27 magas, a cellán belül
vízszintesen középen (28…30), felülről 8, alulról 5 képpont behúzással.

*Bizonyítottsági fok: **megerősített** — közvetlen rétegfejléc-olvasás.*

---

## 12. LEZÁRVA: a „Hold Selection" ÉS az „Add to Picture Tray" UGYANAZ (2026-08-24)

A 10.1 kérdés hamis előfeltevésen állt: **nincs két parancs.**

### A bizonyíték: egy parancs, két néven

A menüépítő (`0x00732f20` környéke) így hozza létre a rekordot:

```asm
0x00732f35  push 0xcae618        ; fordítási kulcs: "Tray::ID_PICTURE_HOLDINPICTURETRAY"
0x00732f3a  mov  eax, 0xcae63c   ; alapértelmezett angol felirat: "&Hold Selection"
0x00732f4c  mov  word ptr [0xd6edca], 0x9ca0
0x00732f55  call 0x9ae560        ; a honosított felirat lekérése
```

⇒ A **belső azonosító** `ID_PICTURE_HOLDINPICTURETRAY` („tartsd a
képtálcán"), a **felhasználónak mutatott felirat** pedig „&Hold
Selection" / **„Kijelölés &megtartása"**. Ez **egyetlen parancs**; az „Add
to Picture Tray" elnevezés sehol nem létezik a szövegtárban.

> Ez pontosan az a hibaosztály, amire a projekt szabálya figyelmeztet:
> **azonosítóból nem szabad jelentést állítani, ha van hozzá felirat.**
> Két néven futó egy parancsból lett két feltételezett parancs.

### Belépési pontok: PONTOSAN EGY menü

A második parancs közvetlenül utána épül, **ugyanabban a függvényben**:

```asm
0x00732f7f  push 0xcae5e4        ; "Tray::ID_REMOVE_SELECTION"
0x00732f84  mov  eax, 0xcae600   ; "&Remove Selection"
0x00732f9a  mov  word ptr [0xd6edde], 0x9cca
```

Nyers bájtkeresés a teljes állományon: a **`&Hold Selection`**
(`0xcae63c`) és a **`&Remove Selection`** (`0xcae600`) sztringcímére
**egyetlen-egy** hivatkozás van, mindkettőre. ⇒ **Egyik parancs sem
szerepel több menüben** — a `Tray` helyi menü az egyetlen belépési pont.

### ⚠️ NEGATÍV EREDMÉNY: a `+0x0a` mező itt NEM parancsazonosító

A menüformátum korábbi leírása szerint a 20 bájtos rekord `+0x0a` mezője a
parancsazonosító. **Ezekre a rekordokra ez nem áll:**

| hol | rekord | `+0x08` | `+0x0a` |
|---|---|---|---|
| `0x00732f4c` | `Tray::ID_PICTURE_HOLDINPICTURETRAY` / „&Hold Selection" | 0 | **`0x9ca0`** |
| `0x007307ff` | `AlbumPhoto::ID_LABELS` / **„&Add to Album"** | 4 | **`0x9ca0`** |
| `0x007310bf` | `AlbumPhoto::ID_LABELS` / „&Add to Album" | 4 | **`0x9ca0`** |

Két **különböző** parancs nem viselheti ugyanazt az azonosítót ⇒ a `0x9ca0`
itt **nem** parancsazonosító, hanem valami közös érték (menüstílus, csoport
vagy erőforrás-jelző). **A következő kör ne építsen rá.**

*Bizonyítottsági fok: **megerősített**, hogy egy parancsról van szó és hogy
egyetlen menüben ül (sztringcím-hivatkozás nyers bájtkereséssel, a teljes
állományon). **Megerősített negatívum**, hogy a `+0x0a` itt nem
parancsazonosító. **Nem tudjuk**, mi a `0x9ca0` jelentése — ez nem
blokkolja a megvalósítást.*

---

## 13. LEZÁRVA: a „régóta tartott elemek" NEM idő-alapú (2026-08-24)

A 4.2 párbeszéd (*„El szeretné távolítani a tálcán régóta tárolt
elemeket?"*) angol szövege (*old held items*) **kort** sugall. A kód
**darabszámot** hasonlít.

### A feltétel — `0x00571e50` (2352 b)

```asm
0x00571edc  mov  esi, [ebx + 0xea4]        ; a tálca CSelectionNode-ja
0x00571ee4  call 0x716cb0                  ; -> edi = a NEM KIZÁRT elemek száma
0x00571eef  call 0x716d10                  ; (al=1) -> eax
0x00571ef4  test eax, eax
0x00571ef6  jne  0x571f03
0x00571ef8  mov  byte ptr [ebx+0x3190], al ; nincs mit kérdezni -> jelző törlése
0x00571efe  jmp  <kilépés>

0x00571f03  cmp  edi, dword ptr [ebx+0x3194]   ; <<< A FELTÉTEL
0x00571f09  jbe  0x571f97                      ; ha NEM nőtt -> nincs kérdés
            … a párbeszéd felépítése (Don't Clear / Clear Tray) …

0x00571f97  mov  dword ptr [ebx+0x3194], edi   ; a küszöb FRISSÜL a mostani számra
0x00571f9d  mov  dword ptr [ebx+0x3198], eax
```

### A két számláló — a már ismert `CSelectionNode`-szerződésre épül

`0x00716cb0(node)` — 46 bájt, a **nem kizárt** elemeket számolja:

```asm
ecx = [node+0x330] >> 1        ; darabszám
edx = [node+0x32c]             ; elemtömb
… cmp byte ptr [ecx+0x5a], 0   ; a kizárás-jelző
    jne <kihagy>
    add eax, 1
```

Ez pontosan a lap többi helyén és a `picasa-eger-es-kijeloles.md`-ben
dokumentált szerződés (`+0x32c` tömb, `+0x330>>1` darab, `[elem+0x5a]`
kizárás).

`0x00716d10(al=1, node)` — 81 bájt, ugyanezen a listán jár végig egy globális
(`[0xd676c0]`) alapján; a visszatérése a `+0x3198` mezőbe kerül.

### A tálca három állapotmezője

| mező | mit tárol | ki írja |
|---|---|---|
| `+0x3190` | logikai: „van mit takarítani" | `0x005727e0`, `0x00571ef8` |
| **`+0x3194`** | **a legutóbb megjegyzett elemszám** (a küszöb) | `0x005727e0` (pillanatfelvétel), `0x00571f97` (frissítés) |
| `+0x3198` | a `0x716d10` legutóbbi eredménye | ugyanott |

A pillanatfelvételt a `0x005727e0` készíti:

```asm
0x005727e9  call 0x716cb0
0x005727ee  mov  [esi+0x3194], eax        ; a mostani darabszám lesz a küszöb
0x005727f8  call 0x716d10
0x005727ff  mov  [esi+0x3198], eax
0x00572808  mov  byte ptr [esi+0x3190], al
```

### ⇒ A szabály egy mondatban

> **A kérdés akkor jelenik meg, ha a tálca nem kizárt elemeinek száma
> NAGYOBB, mint a legutóbb megjegyzett szám.** „Régóta tartott" = ami már
> a növekedés előtt is bent volt. **Eltelt idő sehol nem szerepel** — nincs
> időbélyeg, nincs időzítő, nincs küszöb-konstans.

Ha nem nőtt a szám, a program **némán frissíti** a megjegyzett értéket, és
nem kérdez.

*Bizonyítottsági fok: **megerősített** — a feltétel, a két számláló és
mindhárom állapotmező írója diszasszemblálva; a `+0x3194`/`+0x3190`
eltolásokra nyers bájtkeresés adta ki az összes hozzáférést (8 és 7 hely).*

---

## 14. LEZÁRVA: a tálca húzási FORRÁS — és pontosan három ilyen van (2026-08-24)

### A gépezet

| elem | cím | bizonyíték |
|---|---|---|
| a húzás-forrás csomópont osztálya | **`ytDragNode`**, vtable `0x00ce5b9c` | RTTI |
| a `DoDragDrop` burok | `0x00aa1fb0` (700 b) | **a `ytDragNode` vtable 30. rekesze** — közvetlen hívója NINCS, csak ez a rekesz |
| a rendszer-híd | **`CSysDragDrop`**, vtable `0x00ce5c94` | RTTI; metódusai a `0x00aa2xxx` modulban |
| a héj-formátumok | `0x005378e0` | `Shell IDList Array`, `FileGroupDescriptor`, `FileContents`, `FileName`, `Preferred DropEffect`, `UniformResourceLocator`, `Net Resource`, `Embedded Object` |
| a `Dragnode` **csomópont-típus** neve | `0x004c7b30` típusnév-táblában | a `BG Node`, `Bitmap`, `Button`, `TextEdit`… mellett |

### A HÁROM húzási forrás — a konstruktor hívóiból

A `ytDragNode` konstruktora (`0x00aa1b90`, 179 b) a teljes `.text`-en
**pontosan három** helyről hívódik (nyers `E8`+rel32 keresés):

| hívás | befoglaló | mi ez |
|---|---|---|
| `0x005b97b5` | `0x005b9700` (1122 b) | **`filmeditstrip`** — a filmszerkesztő képsávja |
| `0x008607fc` | `0x008606d0` (778 b) | **`CollageNodeHandler`** — a kollázs csempéi |
| `0x0071ac84` | `0x0071abc0` (1008 b) | **a `CSelectionNode` modul** — vagyis **a kijelölés = a tálca** |

A harmadik azonosítása: a `0x0071xxxx` tartományban a `CSelectionNode`, a
`CAlbumSelectionNode` és a `CFoundFaceSelectionNode` vtáblái élnek, és
ugyanitt ül a tálca két számlálója is (`0x00716cb0`, `0x00716d10`, ld. 13.).

⇒ **A tálca (a kijelölés) húzási forrás.** Nem külön funkció: a
kijelölés-csomópont maga hozza létre a húzás-csomópontot.

### ⛔ Két megdőlt nyom — hogy ne járjuk be újra

1. **`ytSelectionDragHandler` / `SelectionDragCreator` / a `selectiondrag`
   kezelő NEM fotóhúzás.** A `.tre` dönti el: a `selectiondrag` kezelő az
   `editpanel/cropselection` (vágókeret), az `editpanel/addfaceselection`
   (arckeret) és a `nav/` (navigátor nézetkeret) elemeken ül — ez a
   **gumikeret** húzása egy képen belül. A név megtévesztő.
2. **A „Confirm Copy" / „Confirm Move" NEM az Intézőbe ejtés
   megerősítése.** A `0x005350b0` sztringkörnyezete:
   `CThumbUI::MoveFilesToAlbumFolder::1` és `::2`, `Copying file(s) to %s`,
   *„This folder already contains files with the same name. Would you like
   to rename or skip these files?"*, *„Are you sure you want to copy the
   file(s) to %s ?"* ⇒ ez a **belső, album-mappába** másolás/mozgatás
   megerősítése. A #455 leírása ezt tévesen az Intézőbe húzáshoz köti.

### ⛔ NEGATÍV: egyetlen erőforrás-elem sem `Dragnode` típusú

A `respack.yt` ~1700 rétegének **egyikén sem** `dragnode` a csomópont-típus
(a jelen lévő típusok: `text` 263, `superbutton` 259, `rect` 200,
`button` 145, `clip` 128, `docbounds` 99, `buttcon` 87, `static` 71 …).

⇒ A húzás-csomópontok **kódból jönnek létre**, nem az erőforrásfából. Aki a
`.tre`-ben keresi őket, nem fogja megtalálni.

*Bizonyítottsági fok: **megerősített** a gépezetre, a három hívási helyre
(nyers bájtkeresés a teljes `.text`-en) és a két megdőlt nyomra.
**Erős, nem megerősített**: hogy a harmadik hívó konkrétan a
`CSelectionNode`-hoz tartozik — ez RTTI-szomszédságon alapul, nem a
függvényre írt néven.*

---

## 15. LEZÁRVA: a bélyegképek NÉGYZETESEK és középre vágottak (2026-09-01)

**Forrás:** 20 felvétel az eredeti Picasa 3-ból,
`research/Picasa3-also-talca-ikonok-viselkedese/`, mind **1920×1080**, a kék
infó-csík mindenütt y 928…942. A csík **kiírja a tálca darabszámát** — ez
kalibrálja a mérést.

### 15.1 A cella négyzet — és a fotó középre VÁGVA

A `…214634.jpg` csíkfelirata a forrás méretét is kiírja: **816×1456 (álló,
0,560)**, a tálcabeli bélyegkép mégis **54×54**. Melyik művelet? Normalizált
keresztkorreláció a rácsbeli (arányhelyes) változat és a tálcabeli között:

| rácsbeli forrás | **középre VÁGÁS** | teljes NYÚJTÁS | aránytartó ILLESZTÉS |
|---|---:|---:|---:|
| 75×138 (0,543) | **+0,587** | +0,214 | +0,055 |
| 77×138 (0,558) | **+0,900** | +0,589 | +0,466 |
| 90×138 (0,652) | **+0,902** | +0,673 | +0,041 |

Háromból háromszor a vágás nyer. A 39 képes felvételen a rács vízszintesen és
függőlegesen is 30 px osztásközű, 28 px tartalommal — négyzetes.

### 15.2 A mért sorozat

A „soronkénti darab" összege **mind a 16 esetben egyezik a csík feliratával**.

| kép | sorok | cella (tartalom) | osztásköz | soronkénti |
|---:|---:|---:|---:|---|
| 3 | 1 | 54 | 57,00 | 3 |
| 6 | 1 | 54 | 57,20 | 6 |
| 10 | 1 | 54 | 57,00 | 10 |
| 11 | 1 | 54 | 56,00 | 11 |
| 12 | 1 | 48 | 51,00 | 12 |
| 14 | 1 | 42 | 44,00 | 14 |
| 15 | 1 | 38 | 39,93 | 15 |
| 16 | 1 | 35 | 37,00 | 16 |
| 17 | 1 | 33 | 35,00 | 17 |
| 18 | 1 | 33 | 33,94 | 18 |
| 19 | 1 | 29 | 31,00 | 19 |
| 27 | 2 | 28 | 29,94 | 19 + 8 |
| 39 | 2 | 28 | 30,00 | 20 + 19 |
| 49 | 2 | 22 | 24,00 | 25 + 24 |
| 67 | 3 | 18–19 | 21,00 | 29 + 29 + 9 |
| 82 | 3 | 18–19 | 21,00 | 29 + 29 + 24 |

**Mérés módja:** PIL; képpont-osztályozás „doboz-háttér / keret-árnyék /
fénykép-tartalom" (semleges-e az RGB és ≥150 a fényessége); sorsávok a
soronkénti tartalom-arányból, cellahatárok az oszloponkénti tartalom-arányból;
a törtpontosságú osztásköz `(utolsó − első tartalom-képpont + 1 −
cellaszélesség) / (darab − 1)`.

⚠️ **A küszöbös háttér-elkülönítés NEM működik** (a doboz keretét méri), és a
puszta szórás-profil a középre igazított „Kijelölés" feliratot is képnek nézi —
egy korábbi kör emiatt mért „15 képet" egy **egyképes** felvételen.

### 15.3 A vízszintes törvény IGAZOLVA a képernyőn

A `thumbui.tre` kényszerei (`scratchback` = `bal+5 … 0,365·szélesség−15`;
`scratch` = `scratchback` behúzva bal +5 / jobb −50 / fent +5 / lent −5)
1920-as ablakra `scratchback = [5 ; 685,8]` és `scratch = [10 ; 635,8]`.

Mérve: a doboz kerete **x 5** és **x 683**; az első cellahatár közepe **x 10,5**.
A 625,8 px hasznos szélesség a férőhelyet is megadja: `⌊625,8/30⌋ = 20` és
`⌊625,8/21⌋ = 29` — **pontosan a mért soronkénti maximumok**.

### 15.4 ⛔ NINCS MEG: a cellaméret pontos képlete

Kimerítő keresés a kézenfekvő modellre (*„a legnagyobb `s ≤ korlát`, amellyel
`⌈n / ⌊W/(s+rés)⌋⌉ · (s+rés) ≤ H`"*), `W = 560…720`, `H = 52…90`,
korlát `45…62`, rés `1…4`:

- **±1 tűréssel az osztásközre: 912 paraméterkészlet megy át** ⇒ a 16
  megfigyelés **nem határozza meg** a konstansokat;
- **pontos egyezéssel: 0 készlet** — és az osztásközök törtpontosságú mérése
  egészre jön ki, tehát ez **nem mérési hiba: a modell rossz.**

**Ezért képletet nem adunk át.** Megszerzés: a `scratch` panel elrendező
metódusának dekompilálása.

*Bizonyítottsági fok: **megerősített** a négyzetes cellára, a középre vágásra,
a 16 mért esetre és a vízszintes törvényre. A cellaméret-képlet: **NINCS MEG**.*

Jegy: **#1916**.

---

## 16. LEZÁRVA: a `scratch` a `scratchlabel` FÖLÖTT van (2026-09-01)

A `thumbui.tre` szülő-gyerek viszonya: `thumbui/scratchlabel` a
`scratchpadbase` gyereke; a `scratchpadbase` és a `thumbui/scratch` a
`scratchback` testvérei, és a `scratchpadbase` van **előbb** deklarálva.

**A döntő bizonyíték közvetlen megfigyelés:** a `…214851.jpg` felvételen a 6
bélyegkép **eltakarja a „Kijelölés" felirat bal részét**, és a felirat vége
(`…lés`) **kilóg a képek jobb oldalán**.

⇒ A bélyegképek a felirat **fölé** rajzolódnak, és a felirat **nem tűnik el**,
ha a tálca nem üres. *(Nálunk `visible: false` lesz — a #1916 javítja.)*

*Bizonyítottsági fok: **megerősített**.*

---

## 17. A tálca összecsukott MAPPA-TOKENT is tud tartani (2026-09-01)

A `…214629.jpg` felvételen a tálca nem bélyegképeket mutat, hanem **egyetlen
tokent**: kép-köteg ikont, rajta kék hátterű felirattal **„Kiválasztott mappa –
82 fotó"**. A rétegkészlet a `scratch.tre`-ben külön él:

```
scratch/album:      root                (m_scaleXY, m_hidden)
scratch/albumsize:  scratch/album       (mind a négy oldalon 8 px behúzás)
scratch/albumcover: scratch/albumsize   (m_centerXY, Property usealpha 1)
scratch/albumlabel: scratch/album       (m_centerXY, m_displayfont12)
scratch/highlight:  scratch/albumlabel  (−4/+4 vízszintesen, +1 függőlegesen,
                                         Property round 2, Property predraw 1)
```

A `scratch.tre` saját megjegyzése: *„I chose this dumb constraint because the
tray can get so small that there's no room for text"*.

**Nyitva:** mi teszi a mappát a tálcára (a `Tray::` névtérben nincs rá parancs),
és a felirat pontos formátumsztringje — mindkettő **NINCS MEG**.

Jegy: **#1919**.

---

## 18. MEGDŐLT: a „3 px a sorok közt, 0 a képek közt" (2026-09-02, #1933)

A #1914 a bélyegkép-rácsra **eltérő** vízszintes és függőleges rést kért:
*„a sorok közt 3 px rés, a képek közt 0"*. A #1933 ezt azzal vitte
blokkoltra, hogy **a forrásfelvétel nincs meg** a
`research/Picasa3-also-talca-ikonok-viselkedese/` mappában.

**Mindkét állítás megdőlt.**

### 18.1 A forrásfelvétel MEGVAN — és pontosan azt adja

A `…214733.jpg` kék csíkja kiírja: **„67 képek”** — ez a #1914 által
idézett 67 képes felvétel. A tálca sávjában soronkénti szórásprofillal
(PIL, `std > 25` az `x 12…600` sávon):

```
sorok:  y 956…974 (18) · rés 974…977 (3) · y 977…995 (18) · rés 995…998 (3) · y 998…1018
```

A #1914 idézete — *„3 px (y 974–976, 995–997)”* — **képpontra ez.** A
#1933 azért nem találta meg, mert **`std > 12`-vel mérte**: azzal a
küszöbbel a három sor egyetlen sávvá olvad össze.

**Küszöbfüggő mérésnél a negatív eredmény nem eredmény** — a küszöböt
addig kell szigorítani, amíg a szerkezet szét nem válik.

### 18.2 A rés MINDKÉT irányban UGYANANNYI

Detrendelt autokorreláció a sorsávok fényességprofilján (mozgóátlag
`k = 41` levonva, csúcskeresés 10…60 között) — az oszlop-osztásköz, és
mellette a sor-osztásköz ugyanabból a felvételből:

| felvétel | sorok | tartalom | **oszlop-osztásköz** | **sor-osztásköz** |
|---|---:|---:|---:|---:|
| `…214733` (67 kép) | 3 | 18 | **21** (AC 0,554 / 0,647) | **21** (956 → 977) |
| `…214725` (39 kép) | 2 | 28 | **30** (AC 0,264 / 0,322) | **30** (957 → 987) |
| `…214730` (49 kép) | 2 | 22 | **24** (AC 0,435) | **24** (963 → 987) |
| `…214707` (19 kép) | 1 | 29 | **31** (AC 0,277) | — |

⇒ **A cella négyzetes, és az osztásköz a két irányban azonos.** Ez
egybevág a 15.1-gyel (*„a 39 képes felvételen a rács vízszintesen és
függőlegesen is 30 px osztásközű, 28 px tartalommal"*) — a #1914
kérése ellentmondott a saját lapunk 15. szakaszának.

### 18.3 Következmény a megvalósításra — NINCS átépítés

A mai kód `spacing: 2` **mindkét irányban** (`TrayBar.qml:421`). Ez a
mért törvénnyel **szerkezetileg egyezik**: a `Flow` szétszedése külön
sor- és oszlopközre **nem kell.**

Ami marad: a rés a cellamérettel együtt változik — **2 képpont** a
22–29-es tartalomnál, **3 képpont** a 18-asnál. Hogy a rés a
cellaméret függvénye-e vagy a maradék elosztásából adódik, az a
**cellaméret-képlettel együtt** dől el (15.4, **#1916**) — külön nem
kutatható.

*Bizonyítottsági fok: **megerősített** a forrásfelvétel azonosítására és
a négyzetes osztásközre (négy felvétel, két független mérési móddal).*

Jegy: **#1933** (lezárva), **#1916** (a képlet).
