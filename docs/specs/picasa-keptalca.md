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

*Forrás: `thumbui.tre:337` (`thumbui/addtobuttcon`) · `thumbui.tre:326` (`thumbui/scratchclear`) · `thumbui.tre:317` (`thumbui/scratchhold`) — és további 1 elem ugyanott.*

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
képpont körbe).

> ⚠️ **A 59 NEM az osztásköz** (2026-09-05, #1504). A sor vízszintes
> léptetése a gomb **saját, kirajzolt szélessége (55)** — ld. lent, „A
> kimeneti sor LÉPTETÉSE". A `59 × 40` a cella-grafika (`docbounds`) mérete,
> nem a szomszéd gomb távolsága.

### A kimeneti sor LÉPTETÉSE — a `cellwidth` és a valódi lépés (2026-09-05, #1504)

A `#1345` a sor osztásközét a respack rétegfejlécéből (59) vezette le; a
`#1420` kirajzolt Picasa-képernyőképen **55**-öt mért (a három felirat közepe
867,5 · 922,5 · 977,5). **A képernyőkép nyer, és most már tudjuk, miért.**

**1. A konténer deklarál egy cellaméretet.** Az `outputlayout.tre`
utolsó blokkja — az egyetlen hely az EGÉSZ `.tre`-készletben, ahol ezek a
nevek előfordulnak:

```
outputlayout/overflowcontainer: root
m_offsetT
m_scaleX
Property cellwidth  50
Property cellheight 52
```

**2. A két nevet egyetlen függvény ismeri.** A `cellwidth`/`cellheight`
sztringre (`0x00c92150`, `0x00c9215c`) egyetlen hivatkozás van, a
`0x00597390` tulajdonság-beállítóban, amely a `center`-t is kezeli:

| tulajdonság | tagoffszet | tárolás |
|---|---|---|
| `center` | `+0x29c` | bájt (`0x00597482`) |
| **`cellwidth`** | **`+0x274`** | dword (`0x00597549`) |
| **`cellheight`** | **`+0x278`** | dword (`0x00597611`) |

**3. Az elrendező (`0x00597f80`) így használja** (`0x0059862c`):

```
mov eax, [ebx+0x274]        ; cellwidth
test eax, eax
je  <a gyerek SAJÁT szélessége>   ; 0x0059864a: a gyerek befoglalójából
fild …                            ; egyébként float(cellwidth)
```

**4. ⭐ De a KURZOR nem ezzel lép.** A ciklus végén
(`0x0059883e`–`0x00598863`):

```
mov ecx, [esp+0xc0]         ; a gyerek befoglalójának x1
sub ecx, [esp+0xb8]         ; − x0  ⇒ a gyerek TÉNYLEGES szélessége
fild dword ptr [esp+0x18]
fadd dword ptr [esp+0x30]   ; akkumulátor += ez a szélesség
fstp dword ptr [esp+0x30]
```

⇒ **A sor a gyerek elrendezés UTÁNI, tényleges szélességével lép tovább** —
és az a gomb saját respack-doboza: **55**. Ezért mér a képernyőkép 55-öt, és
ezért nincs hézag a gombok között.

**Bizonyítottsági fok:** *megerősített* a `.tre`-tulajdonságokra, a
tagoffszetekre és arra, hogy az akkumulátor a gyerek tényleges szélességét
adja hozzá (mind közvetlen kiolvasás). *Erős* arra, hogy emiatt 55 a lépés
(a gomb respack-doboza 55, és a kirajzolt kép is 55-öt ad). **NINCS
visszaolvasva:** pontosan melyik téglalapot kapja a gyerek a `cellwidth`
(50) értékből — a deklarált 50 a léptetésben nem jelenik meg.

⛔ **Amit ez KIZÁR:** a `59` mint osztásköz. A `59 × 40` a `docbounds`
cella-grafika mérete; a léptetéshez semmi köze. A PicasaPy `TrayBar.qml`
`actionCellWidth: 59` állandója (`:333`) ezért **4 képponttal szellősebb**
soronként — gombonként, összesen ~20 képponttal.
 Az elválasztó 2 képpont széles, 27 magas, a cellán belül
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
ha a tálca nem üres. *(Nálunk MA fordítva van: a felirat csak ÜRES tálcánál látszik, és a
bélyegképek FÖLÉ rajzolódik. Ez a pont korábban azt írta, hogy „a #1916
javítja” — a **#1916 lezárt**, és a négyzetes bélyegképekről szólt, nem
erről. A javítás jegye: **#2179**.)*

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

~~**Nyitva:** mi teszi a mappát a tálcára (a `Tray::` névtérben nincs rá parancs),
és a felirat pontos formátumsztringje — mindkettő **NINCS MEG**.~~

⇒ **MINDKETTŐ MEGVAN**, ld. a **20. pontot** — és ugyanott két állítás
helyesbítve is van ebből a szakaszból (a „kép-köteg ikon” valójában egyetlen
borítófotó, a felirat elválasztója pedig kis-, nem nagykötőjel).

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

---

## 19. A tálcának SAJÁT KIJELÖLÉSE van — és a keret színe MEGVAN (2026-09-02)

Ez a lap eddig a tálca **tartalmáról** és a **műveleteiről** szólt. Hiányzott
belőle a legalapvetőbb interakció: **a tálcán belül ki lehet jelölni egy-egy
képet**, és a parancsok arra vonatkoznak.

### 19.1 A bizonyíték

**A tulajdonos képernyőképe** (2026-09-02, futó Picasa 3): a tálcán három kép,
a **középső kijelölve**, kék kerettel. A skill szabálya szerint ez a
legerősebb bizonyíték.

**A bináris oldal ezt megmagyarázza:** a tálca **ugyanolyan
`CSelectionNode`**, mint a fotórács (13. szakasz: `[ebx+0xea4]`, és a rá futó
két számláló `0x00716cb0` / `0x00716d10`). A csomópont szerződése
([`picasa-eger-es-kijeloles.md`](picasa-eger-es-kijeloles.md) 4.):

| mező | mit tárol |
|---|---|
| `+0x32c` | az elemtömb |
| `+0x330 >> 1` | a darabszám |
| `[elem+0x59]` | **kijelölt** jelző |
| `[elem+0x5a]` | horgony / elnyomó jelző |
| `[elem+0x5b]` | fókusz jelző |

A tálca számlálója (`0x00716cb0`) épp az **elemenkénti** jelzőt olvassa:
`cmp byte ptr [ecx+0x5a], 0` → `jne <kihagy>`. ⇒ **elemenkénti állapot van a
tálcán belül** — nem a rács kijelölésének tükre.

Ezért van értelme a helyi menü **„Kijelölés eltávolítása"** tételének
(`Tray::ID_REMOVE_SELECTION`, `0xcae5e4`, felirat `0xcae600` — 3. és 12.
szakasz): az a **tálcán** kijelöltet veszi ki.

### 19.2 A kijelölés KERETE — `constants.ui`, nem a bináris

⛔ **Ez a szakasz egy ugyanaznapi SAJÁT TÉVEDÉST is helyesbít.** A #2039
nyitásakor a kör azt írta, hogy a keret színe „NINCS MÉRVE" és képernyőkép
kell hozzá. **Téves:** az érték egy sima szövegfájlban áll, a telepítőben.

```
runtime/constants.ui
;-----------------------------
; Selected thumbnail outline
; color1 = outside; color2 = inside
;-----------------------------
thumbsel_color1=#009EFF
thumbsel_color2=#FFFFFF
```

A **fájl saját megjegyzése** mondja meg a sorrendet: **kívül `#009EFF`**
(élénk azúr), **belül `#FFFFFF`** (fehér). A binárisban az egyetlen olvasójuk
a `0x007224f0` (2997 b), amit a `0x00718d80` hív.

**Nálunk ez a rácsban MÁR MEG VAN ÉPÍTVE** (#384, 2026-08-06):
`app/qml/PicasaPy/Theme.qml:64` (`thumbSelection`) és a
`ThumbDelegate.qml` `selectionOuter` / `selectionInner` rétege
(`:5`, `:118–125`). A `design-guide.md` 63. sora dokumentálja.

⇒ **A tálca ugyanezt vegye át**, ne kapjon saját stílust.

*Bizonyítottsági fok: **megerősített** a színekre (szó szerinti
konfigurációs érték, saját magyarázó megjegyzéssel) és **erős** arra, hogy a
tálcán belüli kijelölés létezik (képernyőkép + a `CSelectionNode`
elemenkénti jelzői).*

### 19.3 MÓDSZERTANI TANULSÁG — a `runtime/*.ui` is a bizonyítéklánc része

A kör azért minősítette tévesen „blokkoltnak" a kérdést, mert **kizárólag a
bináris felől** kereste (respack-réteg, sztringtár, sztring-xref), és ott nem
találta. A válasz egy **sima szöveges konfigurációs fájlban** volt, a
telepítő `runtime/` mappájában — és a saját `design-guide.md`-nk **egy hónapja
tartalmazta**.

⇒ **A `runtime/constants.ui` (és társai) a lánc ELEJÉRE tartozik**, a
`docs/specs` és a `referencia/` mellé. Ha egy szín, méret, betűméret vagy
térköz kell, **először ott nézd meg** — a Picasa a felület számadatainak egy
részét szándékosan kiszervezte szövegfájlba.

A `constants.ui` (1 723 bájt) témakörei: albumlista (sormagasság, behúzás,
kijelölés- és lebegtetés-színek **platformonként**), albumcímke (színek,
eltolások, betűk), album-elrendezés (`alayout_gutter=24`,
`alayout_thumbGutterX=12`, `alayout_thumbGutterY=22`, `Georgia` 20/14,
`#634B45`), a kijelölt indexkép kerete, és a webre töltés színe
(`publishtoweb_color=#0000FF`).

Jegy: **#2039**.

---

## 20. LEZÁRVA: a mappa-token TELJESEN feltárva — kiváltó, négy felirat, geometria, és a rács kizárása (2026-09-03, #1919)

A 17. pont három kérdést hagyott nyitva. **Mindhárom megvan**, és közben
két állítása helyesbítendő.

### 20.1 MI VÁLTJA KI — típusteszt, nem parancs (megerősített)

A tokent **nem parancs teszi a tálcára, hanem a kijelölés TÍPUSA**.

A `CThumbUI` „állítsd be az aktuális kijelölés-csomópontot” függvénye
`0x0056bc10` (945 b). A bejövő objektumon (`eax`) **dinamikus
típuskonverziót** végez:

```
0x0056bc43  push 0 ; push 0xd3db90 ; push 0xd3e720 ; push 0 ; push esi
0x0056bc52  call 0x00c07db2        ; __RTDynamicCast(inptr, 0, SrcType, TargetType, 0)
```

A két típusleíró a nevét is megadja (a `TypeDescriptor` +8-tól):

| cím | mangolt név | jelentés |
|---|---|---|
| `0x00d3e720` | `.?AVCSelectionNode@@` | a forrástípus: bármilyen kijelölés |
| `0x00d3db90` | `.?AVCAlbumSelectionNode@@` | **a céltípus: EGÉSZ mappa/album kijelölése** |

Ha a konverzió sikerül (és nem ugyanaz, mint eddig), a mutató a
`CThumbUI` `+0xeac` mezőjébe kerül, hivatkozásszámlálással:

```
0x0056bd43  mov dword ptr [edi + 0xeac], ebx
0x0056bd49  … call [ebx].vtbl+4          ; AddRef
```

⇒ A `+0xeac` **csak akkor nem null, ha a kijelölés egy egész
mappa/album**. Ez magyarázza a 17. pont megfigyelését, hogy a `Tray::`
névtérben nincs „mappa a tálcára” parancs: **nincs is ilyen parancs.**

### 20.2 A felirat NÉGY változatban áll elő — nem egyben

A rajzoló `0x0056ba10` (`CThumbUI::UpdateAlbumCover`, 498 b). A szöveget
egy háromhelyes formátumsztringből rakja össze
(`0x0056bb75`–`0x0056bb7d`, `call 0x0040eab0`, sorrend: formátum, `%s`,
`%d`, `%s`):

| lépés | cím | mit dönt el |
|---|---|---|
| van-e kijelölt mappa | `0x0056babc` (`[edi+0xeac]` null-teszt) | ha null → **„Nincs kijelölés”** |
| hány elem | `0x0056bacc` (`call 0x00716cb0`) | a `%d`; ha **0**, szintén „Nincs kijelölés” (`0x0056baed`) |
| mappa vagy album | `0x0056bae6` (`call 0x004461a0`) | az első `%s` |
| egyes vagy többes | `0x0056bb26` (`cmp ebp, 1`) | a második `%s` |

A teljes szótár (`referencia/stringres-en-hu.tsv` 759–764. sor):

| kulcs | angol | magyar | mikor |
|---|---|---|---|
| `CThumbUI::UpdateAlbumCover` | `%1$s - %2$d %3$s` | `%1$s - %2$d %3$s` | a keret |
| `CThumbUI::UpdateAlbumAlbum` | `Album Selected` | **Kiválasztott album** | `0x004461a0` ≠ 0 |
| `CThumbUI::UpdateAlbumFolder` | `Folder Selected` | **Kiválasztott mappa** | `0x004461a0` = 0 |
| `CThumbUI::UpdateAlbumphoto` | `photo` | **fotó** | darabszám = 1 |
| `CThumbUI::UpdateAlbumCoverphotos` | `photos` | **fotó** | darabszám ≠ 1 |
| `CThumbUI::UpdateAlbumCoverNoSel` | `No selection` | **Nincs kijelölés** | nincs mappa VAGY 0 elem |

A binárisba fordított angol alapértékek ugyanezek:
`0x00c8f070` = `%s - %d %s`, `0x00c8efd8` = `Album Selected`,
`0x00c8f004` = `Folder Selected`, `0x00c84c10` = `photo`,
`0x00c84c18` = `photos`, `0x00c8f0ac` = `No selection`.

> ⚠️ **Helyesbítés a 17. ponthoz és a #1919 törzséhez.** Ott
> „Kiválasztott mappa **–** 82 fotó” áll, **nagykötőjellel**. A mért
> formátum **kiskötőjelet** használ (`%s - %d %s`). A képernyőképről
> való leolvasás tévedett; a mért formátum a mérvadó.
>
> A magyar egyes és többes szám **azonos** („fotó”) — ez magyarul helyes
> (szám után egyes szám), nem szótárhiba.

### 20.3 A `0x004461a0` jelentése — független keresztellenőrzéssel

Ugyanez a függvény dönti el a **helyi menü címét** is, egy tőle független
helyen (`0x00537fb0`, `[esi+0xeac]` → `call 0x004461a0` a `0x00537fdc`-n):

| eredmény | menücím | kulcs |
|---|---|---|
| ≠ 0 | `&Album` | `ThumbUIOutput::AlbumMenu` |
| = 0 | `F&older` | `ThumbUIOutput::FolderMenu` |

⇒ `0x004461a0` = *„a kijelölés ALBUM-e (szemben a mappával)?”* — két
egymástól független felhasználási hely adja ugyanazt a jelentést.

### 20.4 ⛔ A token KIZÁRJA a bélyegkép-rácsot — a #1919 „Kész, ha” listája TÉVED

A #1919 kéri, hogy „a tálca **vegyesen** is tudjon képet és tokent
tartani”. **Ilyen állapot az eredetiben nincs.** Három független
bizonyíték:

1. **A token a teljes tálca-vásznat elfoglalja.** A `respack.yt`-ben a
   `scratch/album` téglalapja **bájtra azonos** a `scratch/docbounds`
   (dokumentumhatár) téglalapjával: mindkettő **(0,0)–(174,87)**.
2. **A tálca bélyegkép-területe épp ezt a vásznat mutatja.** A
   `thumbui/scratch` réteg fajtája a csomagban
   `layer:thumbui/clip(scratch): scratch` — vagyis egy **kivágás a
   `scratch` panelre**. Amit a token elfoglal, arra rács nem fér.
3. **Húsz felvétel, nulla vegyes eset.** A
   `research/Picasa3-also-talca-ikonok-viselkedese/` sorozatban pontosan
   **egy** felvételen látszik a token (`…214629.jpg`, akkor rács nélkül),
   a maradék tizenkilencen rács van, token nélkül.

⇒ A megvalósításban a tálca **VAGY** bélyegképeket mutat, **VAGY** egy
tokent. A #1919 vonatkozó „Kész, ha” pontját törölni kell.

### 20.5 Geometria — MÉRVE

*Forrás: `scratch.tre:36` (`scratch/album`) · `scratch.tre:10` (`scratch/albumcover`) · `scratch.tre:31` (`scratch/albumlabel`) — és további 2 elem ugyanott.*

**A csomagból** (tervezővászon-koordináták, `int16 x0,y0,x1,y1`):

| réteg | téglalap | méret | szín |
|---|---|---|---|
| `scratch/docbounds` | (0,0)–(174,87) | 174 × 87 | — |
| `scratch/album` | (0,0)–(174,87) | **174 × 87** | — |
| `scratch/albumsize` | (63,31)–(94,53) | 31 × 22 | — |
| `scratch/albumcover` | (63,31)–(94,53) | 31 × 22 | — |
| `scratch/albumlabel` | (45,30)–(165,52) | 120 × 22 | `#F5F5F5` |
| `scratch/highlight` | (45,36)–(165,52) | **120 × 16** | `#2E72A1`, **70%** |

A futásidejű elrendezést a `scratch.tre` kényszerei adják (17. pont): a
`albumsize` a `album` mind a négy oldalán 8 képpont behúzással, a borító
és a felirat egyaránt **középre**, a pirula a felirat körül −4/+4
vízszintesen és +1 függőlegesen, `round 2`, `predraw`.

**A képernyőn** (`…214629.jpg`, 1920×1080):

| mit | mért érték |
|---|---|
| kék pirula | x 251–392, y 979–995 → **142 × 17 px** |
| pirula színe | **RGB(107, 153, 186)** |
| borítófotó | x 309–337 → **29 px széles**, álló, vetett árnyékkal |

A pirula magassága (17) a vászonértékkel (16) egyezik ⇒ a token
**nincs felnagyítva**, a vászonegység itt képernyő-képpont. A pirula
**szélessége a szöveggel nő** (142 > 120), tehát a 120 vászonszélesség
helyőrző.

> ⚠️ **Helyesbítés a 17. ponthoz:** a borító **nem** „kép-köteg ikon”,
> hanem **egyetlen borítófotó** vetett árnyékkal, oldalarány-tartóan az
> `albumsize` dobozba illesztve (a réteg fajtája `bicubic`). A mappánként
> MENTETT borító tárolása a #2049 lelete (`albums.db`).

> **A pirula 70%-a önálló lelet:** a réteg fejlécének 8–9. bájtja
> **átlátszóság** (`uint16`, 256 = átlátszatlan), amit a kicsomagolónk ma
> eldob, és amit a `picasa-respack-format.md` tévesen ír le. Jegy:
> **#2178**. A 179/256 = 69,9% fehér fölött RGB(109,157,189)-et ad — a
> képernyőn mért (107,153,186) ettől csatornánként ≤4-gyel tér el.
### 20.6 ⛔ NEGATÍV: a `0x00d67914` NEM funkciókapcsoló

Az `UpdateAlbumCover` a `scratch/albumcover` feloldását egy globális
null-tesztre köti (`0x0056ba7b`: `cmp dword ptr [0xd67914], ebx`), és
ugyanez a teszt őrzi a `scratch/album` bekötését is (`0x00572b90`). Ez
**nem** azt jelenti, hogy a token funkciókapcsoló mögött van: a globális
egy **indulási szingleton mutatója**, amit a `0x009c3a20` állít elő
(`push 0x1c70` = 7280 bájt lefoglalása, majd `call 0x009c3050`
konstruktor). A teszt csak azt kérdezi, felépült-e már a yt felületmotor.

*Bizonyítottsági fok: 20.1–20.5 **megerősített**; 20.6 **megerősített**
(a foglalás és a konstruktorhívás a kódban áll).*

Jegyek: **#1919** (a token megvalósítása), **#2178** (respack-átlátszóság),
**#2179** (a „Kijelölés” vízjel).

---

## 21. A tálca alatti KIMENETI gombsor — `outputlayout`, és a hiányzó túlcsordulás-gomb (2026-09-03)

A 7. és a 11. pont a tálca **három** gombjáról szól (megtartás, ürítés,
albumhoz adás). A tálca **jobb oldalán** viszont van egy másik, önálló
gombsor: a kimeneti műveleteké (`outputlayout`) — nyomtatás, e-mail,
exportálás, kollázs, film. Ez a szakasz azt írja le.

### 21.1 A sor EGYETLEN cellasablonból épül

A `respack.yt` mért geometriája szerint az `outputlayout` **nem egy sáv,
hanem egy CELLA**: a `outputlayout/docbounds` **59 × 40**, és **mind a
kilenc gomb ugyanazt a téglalapot foglalja** — (2,2)–(57,38), azaz
**55 × 36**. A gombok tehát ugyanannak a cellának a **változatai**,
amiket a konténer példányosít:

| elem | téglalap | méret |
|---|---|---|
| `outputlayout/docbounds` | (0,0)–(59,40) | 59 × 40 |
| `outputlayout/overflowcontainer` *(típusa: `overflow:`)* | (0,0)–(59,40) | 59 × 40 |
| `outputlayout/pbutton` (nyomtatás) | (2,2)–(57,38) | **55 × 36** |
| `outputlayout/ebutton` (e-mail) | (2,2)–(57,38) | 55 × 36 |
| `outputlayout/folderbutton` (exportálás) | (2,2)–(57,38) | 55 × 36 |
| `outputlayout/orderbutton` (vásárlás) | (2,2)–(57,38) | 55 × 36 |
| `outputlayout/sharewith` (Hello) | (2,2)–(57,38) | 55 × 36 |
| `outputlayout/blogger` | (2,2)–(57,38) | 55 × 36 |
| `outputlayout/collage` | (2,2)–(57,38) | 55 × 36 |
| `outputlayout/makemovie` | (2,2)–(57,38) | 55 × 36 |
| **`outputlayout/morebutton`** *(típusa: `buttcon`)* | (2,2)–(57,38) | 55 × 36 |
| `outputlayout/separator` | (28,8)–(30,35) | **2 × 27** |

A **gazda** a főablakban: `thumbui/outputs`, típusa
`rect(0, outputlayout)` — **(373,480)–(797,509), 424 × 29**. Vagyis a
424 × 29-es sávban ismétlődik az `outputlayout` cella.

Az ikonok saját méretei: `pbutton_icon` 15 × 12, `ebutton_icon` 16 × 11,
`folderbutton_icon` 17 × 13, `orderbutton_icon` 13 × 11,
`sharewith_icon` 40 × 21, `blogger_icon` 17 × 19, `collage_icon` 16 × 15,
`movie_icon` 17 × 15, `export7_icon` 13 × 7, `default_icon` 16 × 15,
`earth_icon` 17 × 17.

Szerkezeti horgony: `outputlayout.tre` — minden gomb az
`outputlayout/overflowcontainer` gyereke, a konténer pedig a `root`-é
(`outputlayout.tre:1`–`:36`).

### 21.2 ⭐ A `morebutton` a TÚLCSORDULÁS-gomb — nálunk nincs

*Forrás: `outputlayout.tre:99` (`outputlayout/blogger`) · `outputlayout.tre:111` (`outputlayout/collage`) · `outputlayout.tre:51` (`outputlayout/ebutton`) — és további 6 elem ugyanott.*

| | angol | **magyar** |
|---|---|---|
| felirat | More... | **További lehetőségek...** |
| buboréksúgó | Click here for more options | **Kattintson ide a további opciókért** |

A konténer típusa a `respack.yt`-ben **`overflow:`** — ez az a
konténerfajta, ami a ki nem férő gyerekeket egy gomb mögé rejti; a
`morebutton` ennek a gombja (típusa `buttcon`, saját ikonja az
`export7_icon`, 13 × 7).

⇒ **A gombsor szélesség-érzékeny**: ha a 424 × 29-es sávba nem fér ki
minden 55 × 36-os cella, a maradék a „További lehetőségek…" mögé kerül.

**A többi gomb hivatalos magyar felirata és súgója** (forrás:
`referencia/i18n-hu/outputlayout_text.xml`, angol:
`referencia/tre-eroforrasok/outputlayout_text.tre`):

| elem | felirat | buboréksúgó |
|---|---|---|
| `outputlayout/pbutton` | **Nyomtatás** | A Fotótálcán található fotók nyomtatása |
| `outputlayout/ebutton` | **E-mail** | A Fotótálcán található fotókat elküldheti e-mailben |
| `outputlayout/folderbutton` | **Exportálás** | Átmásolja a Fotótálcán található fotókat egy a merevlemezen található mappába |
| `outputlayout/orderbutton` | **Vásárlás** | Rendeljen nyomatokat és egyéb termékeket kedvenc online szolgáltatójától |
| `outputlayout/collage` | **Kollázs** | Készítsen fotókollázst a kijelölt képekből |
| `outputlayout/makemovie` | **Mozgófilm** | Mozgófilmes prezentáció létrehozása a kijelölt elemek alapján |
| `outputlayout/sharewith` | **Hello** | A Fotótálcán található fotókat elküldheti a Hello programba |
| `outputlayout/blogger` | **Blogger** | Fotók feltöltése a Bloggerre |
| **`outputlayout/morebutton`** | **További lehetőségek...** | **Kattintson ide a további opciókért** |

*(A `sharewith` (Hello) és a `blogger` megszűnt Google-szolgáltatásokhoz
tartozik — hatókörön kívül, ugyanazon az alapon, mint a `publish` webes
ága.)*
### 21.3 Eredeti / nálunk — MÉRVE

| | eredeti | nálunk (mérve) |
|---|---|---|
| a cella mérete | **55 × 36**, a gazdasáv 424 × 29 | nem mérve — a gombok a `TrayBar.qml` sorában élnek |
| Nyomtatás · E-mail | `pbutton` · `ebutton` | megvan (`TrayBar.qml:62` környéke) |
| Exportálás | `folderbutton` | megvan (`TrayBar.qml:48`) |
| Kollázs · Film | `collage` · `makemovie` | megvan (`trayCollageButton`, `trayMovieButton`) |
| **túlcsordulás-gomb** | **`morebutton`**, „További lehetőségek…" | ⛔ **NINCS** — 0 találat `morebutton`/„további lehetőség"/overflow névre a `src/`-ben |
| Vásárlás · Hello · Blogger | `orderbutton` · `sharewith` · `blogger` | hatókörön kívül (megszűnt szolgáltatások) |

⇒ Nálunk a gombsor **nem kezeli a szűk helyet**: keskeny ablaknál a
gombok elfogynak vagy összenyomódnak, az eredeti viszont a maradékot a
„További lehetőségek…" mögé rejti. Jegy: **#2191**.

*Bizonyítottsági fok: **megerősített*** — a geometria a `respack.yt`-ből,
a konténer `overflow:` típusa ugyanonnan, a feliratok az `i18n-hu`-ból.

---

## 22. A „További lehetőségek…" gomb VISELKEDÉSE — kimérve (2026-09-04, #1672)

A 21. szakasz a `morebutton` **helyét és feliratát** adta meg. Ez a szakasz
azt, hogy **mit csinál** — a #1672 kifejezetten ezt kérte („a viselkedése
kimérve, mielőtt bekötjük — ne a feliratból következtessünk").

**A kattintás útja.** A felületi parancsdiszpécser (`0x005d9cc0`) az
elemnévre hasonlít, és a `outputlayout/morebutton` ágon **egyetlen**
függvényt hív:

```
0x005dad25  cmp ecx, 0x00c8f6dc          ; "outputlayout/morebutton"
0x005dad2b  sete cl
0x005dad33  call 0x005fe090              ; a kezelő
```

**A kezelő (`0x005fe090`, 150 b) két csomópontot ér el, névvel:**

```
0x005fe099  "outputlayout/morebutton"          -> a gomb csomópontja
0x005fe0c2  cmp byte ptr [eax + 0x359], 0      ; a gomb egy állapotbájtja
0x005fe0d3  sete al
0x005fe0dd  mov byte ptr [edx + 0x264], al     ; a főablak [+0xea0] objektumába, INVERTÁLVA

0x005fe0e5  "outputlayout/overflowcontainer"   -> a túlcsordulás-konténer
0x005fe110  mov dword ptr [eax + 0x268], 0xffffffff
0x005fe11f  call [vtbl + 0x38]                 ; a konténer 14. rése
```

⇒ **A gomb a `outputlayout/overflowcontainer` állapotát billenti**, és a
konténer saját metódusát hívja meg rá. A `.tre` szerint ebben a
konténerben ül a kimeneti sor **összes** gombja
(`separator`, `pbutton`, `ebutton`, `folderbutton`, `orderbutton`,
`sharewith`, `blogger`, `collage`, és maga a `morebutton` is —
`outputlayout.tre:30`–`136`).

⇒ **A „További lehetőségek…" tehát nem külön menüt nyit, hanem a
túlcsordulás-konténert nyitja/zárja** — pontosan azt, amit a hivatalos
buboréksúgó ígér („Kattintson ide a további opciókért"). A felirat és a
viselkedés **egybeesik**; a #1672 aggálya („ne a feliratból
következtessünk") itt megnyugtatóan zárul.

**Ami NINCS mérve:** mit csinál a konténer 14. rése (a `[+0x268] = −1`
beállítás után hívott metódus), és mi a `[+0x359]` állapotbájt pontos
jelentése a gombon. A **kötéshez** ez nem szükséges: a mi oldalunkon a
túlcsordulás-viselkedés a felületi keretrendszer dolga.

*Bizonyítottsági fok: **megerősített** a hívási láncra és a két érintett
csomópontra (kiolvasott utasítások, névvel); **nincs mérve** a konténer
metódusának tartalma.*
