# Az arcfelismerés TELJES működése (2026-08-22)

A Picasa 3.9.141.259 arcfelismerő funkciójának feltárása. **Ez a lap a
MŰKÖDÉST írja le** — mi kapcsolja be, mit ír, hova, mikor, és mi történik a
meglévő adattal. A felület geometriája a lap végén, szándékosan utoljára áll
(a `picasapy-research` skill 2/b szakasza).

Minden cím a `Picasa3.exe` 3.9.141.259 betöltési címe (VA). Horgonyjegy:
**#26**.

> 🔒 **Adatvédelmi megjegyzés.** A mérés a tulajdonos valódi
> Picasa-adatbázisán készült, ami családtagok nevét tartalmazza. **Ez a
> repó publikus**, ezért a lap csak a **szerkezetet**, a darabszámokat és a
> szentinel-értékeket közli — konkrét személyneveket és a
> `contact_id → név` leképezést NEM. A mérés részletei a privát
> `picasapy-agent` repóban maradnak.

---

## 0. A funkció három, egymástól FÜGGETLEN rétege

Ezt fontos elöljáróban kimondani, mert a hibás mentális modell drága:

| réteg | mit csinál | ki kapcsolja |
|---|---|---|
| **1. detektálás** | megkeresi az arc-téglalapokat a képen | `BgFaceDetectThread` + mappánkénti kizárás |
| **2. csoportosítás + javaslat** | a hasonló arcokat egy csoportba teszi, és nevet javasol | `FRAddSuggesetions`, két küszöb |
| **3. nevesítés + kiírás** | a felhasználó nevet ad, ez fájlba/adatbázisba kerül | `PersistFaceToFile`, `FRWriteFaceDataINI` |

**A három réteg külön kapcsolható**, és a mért adat szerint a gyakorlatban
külön is fut: a tulajdonos adatbázisában van olyan képhalmaz, ami
**detektálva van, de nem nevesítve**, és van olyan, ami **nevesítve van** —
a kettő sorindex-tartománya **diszjunkt** (ld. 3.4).

---

## 1. MI AKTIVÁLJA — a belépési pontok

### 1.1 Beállítások (`Preferences\…`) — a motor kapcsolói

A beállítás-párbeszéd vezérlőneve és a mögötte lévő registry-kulcs
párosítása (`0x006e3990`, a mentő ág):

| vezérlő (`.tre` név) | `Preferences` kulcs | típus | alapérték | hol regisztrálva |
|---|---|---|---|---|
| `enablefacedetection` | **`BgFaceDetectThread`** | bool | **1** (BE) | `0x006e0ead` |
| `enablefacesuggestions` | **`FRAddSuggesetions`** ⚠️ | bool | **1** (BE) | `0x006e0ebd` |
| `persistfacetofile` | **`PersistFaceToFile`** | bool | **1** (BE) | olvasáskor `0x00485382` |
| `facethresh0` | **`FRSuggestionThreshold`** | int | **85** | `0x006e0eda` |
| `facethresh1` | **`FRSortThreshold`** | int | **85** | `0x006e0ee8` |
| — | **`FREnableUploads`** | bool | **1** (BE) | `0x006e0eca` |
| — | **`FRWriteFaceDataINI`** | bool | **0 (KI!)** | olvasáskor `0x00484de7` |

⚠️ **`FRAddSuggesetions` — a Google elgépelte** („Suggesetions"). A kulcs
NEVE hibás a binárisban; aki registry-kompatibilitást épít, ezt a hibás
alakot kell használnia.

⚠️ **`FRWriteFaceDataINI` alapértéke 0**, az összes többié 1. Ez a
legfontosabb kapcsoló a mi szempontunkból: **alapállapotban a Picasa NEM
ír arc-adatot a `.picasa.ini`-be** ezen az útvonalon (ld. 3.1 — a másik
útvonal viszont ír).

### 1.2 A két küszöb-legördülő teljes érték-létrája

Mindkettő **10 fokozatú legördülő**, és az ugrótáblákból (`0x006e56ec`,
`0x006e5714`) kiolvasva **mindkettő ugyanaz a létra**:

| index | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| **érték** | 50 | 55 | 60 | 65 | 70 | 75 | 80 | 85 | 90 | 95 |

Az alapérték **85** mindkettőnél, azaz a **7. index**.

*Bizonyítottsági fok: **megerősített** — az ugrótáblák nyers bájtjaiból
kiolvasva, nem a `cmp`-sorrendből következtetve.*

### 1.3 Menü- és felületi belépési pontok

A menürekord **20 bájt** fix lépésközzel: `+0x00` felirat, `+0x04`
gyorsbillentyű-szöveg, `+0x08` ikon/jelző, **`+0x0a` parancsazonosító**,
`+0x0c` almenü-tömb, `+0x10` almenü-elemszám. A csupa nulla rekord =
elválasztó vonal.

| kulcs | cmd | hol | felirat (EN / HU) |
|---|---|---|---|
| `eMenuTools::ID_TOOLS_DOWNLOAD_FACES` | **0x9e10** | Eszközök, idx 10 (`0xd6e918`) — ⛔ **de a menü megnyitásakor a Picasa maga TÖRLI** (`RemoveMenu`, `0x0056f69e`, feltétel nélkül; ld. `picasa-menu-parancsok-viselkedes.md` 36.1) | *Download Name Tags from Picasa Web Albums* / **Névcímkék letöltése a Picasa Webalbumokból** — a felhasználó soha nem látja |
| `eMenuTools::ID_WRITE_XMP_FACES` | **0x9e2a** | Eszközök ▸ **Experimental** almenü, utolsó elem (`0xd6e838`) | *Write faces to XMP…* / **Arcinformációk írása XMP-adatokba…** |
| `eMenuPicture::ID_PICTURE_RESET_FACES` | **0x9e11** | Kép menü, idx 8 (`0xd6e538`) | *Reset &Faces* / **Arcok alaphelyzetbe állítása** |
| `AlbumPhoto::ID_PICTURE_RESET_FACES` | **0x9e11** (ugyanaz) | **három** helyi menü: mappa-fotó, album-fotó, egyképes nézet | ugyanaz |
| `Album::ID_ALBUM_FILTERFACES` | **0x9e1c** | **két** helyi menü (mappa, album) — mindkettőben az **utolsó** tétel | *&Add name tags* / **Névcímkék hozzáadása** |
| `eMenuCreateMovie::ID_FACES` | **0x9d59** | Létrehozás ▸ Film almenü, idx 1 | *From Faces in Selection…* / **A kijelölésben lévő arcokból…** |
| `eMenuCreateMovie::ID_FACESRANDOM` | **0x9d5a** | ugyanott, idx 2 | *From People Albums…* / **Az Emberek albumból…** |
| `PplAlbumPhoto::ID_PEOPLEALBUMSNEW` | **0xa0cc** | Emberek-album fotó helyi menü, idx 1 | *Move to &New Person…* / **Áthelyezés új személyhez…** |
| `PplAlbumPhoto::ID_PEOPLEALBUMS` | **0xa0cd** | ugyanott, idx 2 | *&Move to People Album* / **Hozzáadás az Emberek albumhoz** |
| `PplAlbumPhoto::ID_SETPEOPLEALBUMCOVER` | **0x9e39** | ugyanott, idx 4 | *&Set as People Album Thumbnail* / **Beállítás az Emberek album indexképeként** |

**A két `Album::ID_ALBUM_FILTERFACES` helyi menübeli működése (#4535).** A
„Névcímkék hozzáadása” a jobbklikkelt **mappa közvetlen képein**, illetve az
album **adott tokenhez tartozó tagképein** indítja el a saját, háttérben futó
arckeresést. A már azonosított, korábban vizsgált vagy mappaszinten kizárt
képekre a szokásos keresési szabályok vonatkoznak; az új, névtelen találatok a
„Névtelenek” albumba kerülnek.

**Bináris bizonyíték és határa:** a mappa- és albummenü-építő (`0x007319f0`,
`0x00732160`) is a `0x9e1c` parancsot teszi a menü végére; a közös popup-út
(`0x005d3290`) a kiválasztott parancsazonosítót `WM_COMMAND`-ként továbbítja
(`0x005d43c5`). A statikus xref-vizsgálat a további műveletkezelőt nem
azonosította. A fenti hatókört ezért a #4535 jegyben megadott eredeti
viselkedés rögzíti; a bináris a két parancs belépési pontját erősíti meg, nem
a szűrés részleteit.

**Gyorsbillentyű: egyiknek sincs** — mind a tíz rekord `+0x04` mezője 0.
*(Menüszinten bizonyított. A program futásidőben `CreateAcceleratorTableA`-val
is épít gyorsítótáblát (`0x0092321a`); annak a tartalma nincs feltárva,
tehát „a menüben nincs gyorsbillentyű" a pontos állítás.)*

> ⚠️ **Az `ID_ALBUM_FILTERFACES` név MEGTÉVESZTŐ.** A felirata nem
> „szűrés", hanem **„Névcímkék hozzáadása"**. Az azonosító nevéből
> következtetni a funkcióra itt hibához vezetne.

**Mappánkénti kizárás:** a Mappakezelő `frexclude` kapcsolója
(`Face Detection On/Off` — *Arcfelismerés be-/kikapcsolva*) mappára és
alfáira kapcsolja ki a detektálást; a kizárás **öröklődik**. Teljes
levezetés: [`picasa-mappakezelo.md`](picasa-mappakezelo.md) 5.3/5.4.

---

## 2. MIT INDÍT EL — a háttérmotor

A detektáló motor konstruktora **`0x0069fc00`** (363 b):

```asm
0x0069fc19  mov  [esi], 0xca8078          ; vtábla
0x0069fc43  ; NYOLC alobjektum, egyenként 0x7c (124) bájt, +0x78-tól
0x0069fc78  push "BgFaceDetectThread"
0x0069fc99  mov  dword [esp+0x40], 1      ; alapérték = 1
0x0069fca1  call 0x00407a20               ; a szokásos Preferences-olvasó
0x0069fcb5  mov  byte [esi+0x74], al      ; a kapcsoló ide kerül
```

**Nyolc, egyenként 124 bájtos rekesz** épül fel a `+0x78` offszettől — a
detektáló munkasorának/példányainak a helye. A `BgFaceDetectThread`
kapcsoló a `+0x74` bájton él.

**Folyamatjelzés a felhasználó felé** (`stringres`, `CUnnamedProgress::*`):

```
%d Group(s), %d Face(s), %d to scan\n%s remaining
%d csoport, %d arc, %d vizsgálandó\n%s van hátra
```

Egyéb állapotüzenetek: *Scanning for faces…* (**Arcok keresése…**),
*Grouping faces, please wait…* (**Az arcok csoportosítása folyamatban van…**),
*Sorting face data, %.0f%%* (**Arcok adatainak rendezése, %.0f%%**),
*Looking for other people…* (**További személyek keresése…**).

---

## 3. MIT ÍR — a tárolók

Ez a szakasz a funkció **fele**, és eddig sehol nem volt leírva.

### 3.1 `.picasa.ini` — KÉT külön írási útvonal

| útvonal | függvény | kapu | mit ír |
|---|---|---|---|
| **A) általános metaadat-író** | `0x007d55f0` | — | `faces=` (a `[contacts2]` után) |
| **B) arcíró** | `0x00484820` | csak a `facedata`-hoz: `Preferences\FRWriteFaceDataINI`, alapból 0 | `faces` és `backuphash` mindig; **`facedata` csak bekapcsolva** |

A **B) útvonal** a `0x00484dcf`-en olvassa a kapcsolót. A helyesbített
ágvizsgálat szerint a `faces=` kulcs mindig kiíródik; a kapcsoló csak a
`facedata`-t kapuzza. A writer `backuphash`-t is ír:

```asm
0x0048516d  push "faces"        -> 0x005ab210(szakasz, kulcs, érték) ; mindig
0x004851ab  push "facedata"     ; csak FRWriteFaceDataINI esetén
0x0048521c  push "backuphash"   ; mindig
```

A `backuphash` képzése itt is a már ismert (#643) alak: a 64 bites érték
négy 16 bites szavának XOR-ja, `"%d"`-vel formázva
(`0x004851cf`–`0x004851f2`).

> ⭐ **ÚJ, eddig sehol nem dokumentált kulcs: `facedata`.** Sem a
> [`picasa-ini-format.md`](picasa-ini-format.md), sem a kódunk nem ismeri.
>
> **DE — mérve:** a 859 fájlos valódi `.picasa.ini`-korpuszban a `facedata`
> **0-szor** fordul elő (`faces=` 4973-szor, `backuphash` 14700-szor).
> Ez egybevág azzal, hogy a `facedata` kapcsolója alapból ki van kapcsolva.
>
> **Amit ez a megvalósításra jelent:** `facedata`-t **írni nem kell**; a
> round-trip parsernek viszont **meg kell őriznie**, ha valaha előfordul.

⛔ **HELYESBÍTVE (2026-10-01, #3793, erős): a `FRWriteFaceDataINI` kapcsoló csak a `facedata`-t kapuzza; a `faces=` mindig kiíródik, és az alábbi pozícióhű `0`-kitöltés a `facedata` értékét építi — ld. a 9/f szakaszt.**

**Az érték-összefűzés alakja** (`0x00484f28`–`0x00484f64`): pontosvesszővel
elválasztott, **pozícióhű** lista, ahol a hiányzó helyeket **`0`** tölti ki:

```
while (i < cél_index) { ha i != 0 -> ';';  '0';  i++ }
';' ;  <a tényleges érték>
```

**A `faces=` mért alakja** (859 fájlos korpusz):

```
faces=rect64(585b0668c1009d50),0
faces=rect64(24d60000786452fc),0;rect64(6f0c29a7af61863f),0
faces=rect64(4b332eb8747a7111),ffffffffffffffff;rect64(8785292cbb847c28),b720285ba3a656a7
```

#### Nálunk (mérve, `serialize_faces`, #3792 után)

A `faces=` sor a bejegyzéseket pontosvesszővel VÁLASZTJA EL, záró
pontosvesszőt a sor végére NEM tesz — ez egyezik a fenti mért alakkal. A
parser (`parse_faces`) visszafelé kompatibilis: a korábbi (hibás), záró
pontosvesszős íróink sorait is beolvassa.

⛔ **HELYESBÍTVE (2026-09-27, #3670, élő mérés — ld. 15.3/b.1): a `.picasa.ini`-ben a `ffffffffffffffff` a MELLŐZÖTT (Ignore) arc jele.** A felismert, de érintetlen névtelen arc egyáltalán nem kerül a fájlba. Az alábbi régi mondat a korpusz-eloszlásból következtetett, mérés nélkül:

~~⚠️ **`ffffffffffffffff` = „ismeretlen / nincs személyhez rendelve"**~~
szentinel, nem azonosító.

### 3.2 A képfájl maga — `PersistFaceToFile`

`0x004852e0` (734 b), a kapu a `0x00485382`-n, **alapérték 1 (BE)**.
Hibaágai szó szerint:

```
Face tag write failed for read only file: %s
Face tag write failed for: %s
```

Vagyis a **csak olvasható fájl külön, megnevezett hibaeset**. A menüből
külön is kérhető: *Write faces to XMP…* (`eMenuTools::ID_WRITE_XMP_FACES`).

A kiírás **kötegelt munkaként** fut, saját folyamatjelzéssel
(`0x006b9dd0`): `FaceTagJob::progress` / `::done` / `::cancelled` —
*Writing face tags* / *Done writing face tags* / *Cancelled writing face
tags*. Tehát **megszakítható**.

### 3.3 A `db3` PMP-oszlopok — KÉT valódi adatbázison mérve

⚠️ **Ezt a szakaszt 2026-08-22-én ÁTÍRTUK.** Az első mérés olyan
telepítésen készült, ahol a felhasználó **soha nem nevezett el arcokat**
(nulla `]facealbum:` token) — ott hat oszlop üres volt, és ebből egy téves
következtetés is született (ld. lent). A tulajdonos ezután adott egy
**második, e célra készített telepítést**, ahol az arcfelismerés
végigfutott és a személyek el vannak nevezve. Az alábbi tábla mindkettőt
mutatja.

| oszlop | típus | „A" telepítés (nincs névadás) | „B" telepítés (VAN névadás) |
|---|---|---|---|
| `imagedata_facerect` | u64 | 7 044 sor, **csak 0/1** | 4 344 sor, **629 VALÓDI rect64** + 2 575 × `1` + 1 140 × `0` |
| `imagedata_facerectdata` | str | 7 044 sor, **0 nem üres** | 4 344 sor, 2 565 × `"1"` + **valódi jellemzőpont-sztringek** |
| `imagedata_facequality` | u32 | — | 3 338 sor, **412 nem nulla, 403 különböző érték** |
| `imagedata_personalbumid` | u32 | **0 sor** | 3 338 sor, **115 nem nulla** |
| `imagedata_suggestionpersonalbumid` | u32 | **0 sor** | 3 337 sor, 1 nem nulla |
| `imagedata_peoplealbumchecksum` | u16 | **0 sor** | 19 636 sor, 301 nem nulla (mind `34`) |
| `imagedata_personalbumrecs` / `…recs2` | u32 | — | 3 337 / 3 163 sor, `0xFFFFFFFF` = „nincs" |
| `imagedata_personalbumrecvalues` / `…values2` | u32 | — | ugyanannyi sor, pontszám |
| `albumdata_albumcontactids` | u64 | **0 sor** | 118 sor, **pontosan 9 nem nulla** |
| `albumdata_albumpeoplechecksum` | u32 | **0 sor** | 118 sor, 8 nem nulla |
| `imagedata_deferredface` | str | 6 870 sor / 11 128 régió | 3 063 bájt |
| `imagedata_deferredregion` | str | 10 175 sor / 13 941 régió | — |
| `facetemplatesV2_0.db` | — | **4 bájt** (üres) | **430 132 bájt** + 40 076 B index |
| `facetags.txt` | — | 0 bájt | **0 bájt** (mindkettőben üres) |

> ⛔ **HELYESBÍTÉS a saját, ugyanaznap reggeli állításunkhoz.** Akkor ezt
> írtuk: *„a `facerect` KIZÁRÓLAG `0`-t és `1`-et vesz fel, egyetlen valódi
> rect64 sincs benne… fájlonkénti logikai jelző, nem geometria."*
> **Ez TÉVES.** A „B" telepítésben **629 valódi, geometriailag érvényes
> rect64** van benne (mind `L<R` és `T<B`). Az „A" telepítésben azért nem
> volt, mert ott **soha nem futott le a névadás**.
>
> **A helyes állítás:** a `facerect` **vegyes** oszlop — valódi rect64-et
> tárol ott, ahol megerősített arc-régió van, és `1`-et jelzőként ott, ahol
> a detektálás lefutott, de régió nem került be. Ugyanez igaz a
> `facerectdata`-ra (`"1"` jelző vagy valódi adat).
>
> **Két módszertani tanulság:**
> 1. Egy adatbázis „üres oszlopa" **nem bizonyít semmit az oszlop
>    szemantikájáról** — csak azt, hogy azt a funkciót nem használták.
> 2. A kontroll-mérésem (hány függvény hivatkozik az oszlop NEVÉRE) is
>    **megtévesztő volt**: a `deferredregion` is csak EGY függvényben
>    szerepel néven, mégis tele van adattal — az oszlopokat regisztráció
>    után **indexszel** érik el, nem néven. Ezt a mérést nem szabad
>    használhatóság bizonyítékaként használni.

### 3.4 A két „deferred" oszlop viszonya — a legértékesebb lelet

**1 588 sorban mindkét oszlopnak van értéke, és ott a `rect64`-ek bitre
azonosak.** Rect-kulcson párosítva **3 104 régió** fedi egymást, amiből
**3 047 (98,2 %) egyértelmű `contact_id → név` leképezést** ad.

Ebből három, egymástól független szerkezeti következtetés:

1. **`ffffffffffffffff` NEM személyazonosító.** 31 párosításban **hét
   különböző névvel** jön elő → „ismeretlen / nincs hozzárendelve"
   szentinel. Ez egyben a `deferredface` leggyakoribb értéke (2 289 régió).
2. **Ugyanaz a személy KÉT azonosítóval is szerepelhet** (mérve: két
   ilyen eset) → **duplikált kontakt** a felhasználó adatbázisában. Egy
   importálónak ezt kezelnie kell, nem hibaként.
3. **Egy azonosító KÉT névalakkal** (mérve: egy eset, ugyanannak a
   névnek a két sorrendje) → a kontaktot **átnevezték**, és a régi
   `deferredregion`-sztringek megőrizték a régi alakot.
   ⇒ **A `deferredregion` NEM íródik újra kontakt-átnevezéskor.**
   Importáláshoz tehát a **`deferredface` + kontakt-tábla a megbízhatóbb**,
   a `deferredregion` csak pillanatkép.

**A sorindex-tartományok DISZJUNKTAK:**

| halmaz | elemszám | sortartomány |
|---|---|---|
| `facerect == 1` | 6 064 | 7 … 6 098 |
| `deferredface` nem üres | 6 870 | 14 757 … 128 639 |
| `deferredregion` nem üres | 10 175 | 19 630 … 128 674 |

A `facerect==1` halmaz metszete a másik kettővel **nulla**. Vagyis a
„detektálva, de nem nevesítve" és a „nevesítve" **két külön, időben is
elkülönült korpusz** — nem ugyanazon képek két oszlopa.

### 3.4/b A SZEMÉLY-ALBUM MODELL — teljesen megfejtve (2026-08-22)

A „B" telepítésen a teljes lánc **9/9 pontos egyezéssel** kimérve:

```
]facealbum:<N>                       <- albumdata_token[N]   (N = a sor SAJÁT indexe)
albumdata_name[N]                    = a személy megjelenített neve
albumdata_albumcontactids[N]         = a kontakt 64 bites azonosítója (u64)
                                        ->  contacts.xml  <contact id="<hex>" …>
imagedata_personalbumid[képsor]      = N   (melyik személyhez tartozik a kép)
```

**A mérés:** a 118 albumsorból pontosan **9**-nek van nem nulla
`albumcontactids` értéke; ez a 9 sor a **109…117** indexen ül, a tokenjük
`]facealbum:109` … `]facealbum:117`, és mind a 9 azonosító **hexben
karakterre egyezik** a `contacts.xml` megfelelő `id=` mezőjével. Az
`imagedata_personalbumid` nem nulla értékei szintén **kizárólag 109…117**
— vagyis **albumsor-indexek**, nem önálló azonosítók.

⚠️ **A `contact_id` TELEPÍTÉSFÜGGŐ.** Ugyanaz a személy a két mért
telepítésben **más azonosítót** kapott. Az azonosító tehát **nem
hordozható** gépek között — importáláskor a **név** az egyeztetés alapja,
nem az id.

⚠️ **A `]facealbum:<N>` N-je az album SORINDEXE**, tehát szintén
telepítésfüggő, és újraindexeléskor elcsúszhat. Egy importáló ne tekintse
stabil kulcsnak.

### 3.4/c `facerectdata` — az arc JELLEMZŐPONTJAI (2026-08-22)

Az oszlop a legtöbb soron `"1"` jelzőt tárol, de ahol valódi adat van, ott
egy **emberi szemmel is olvasható, vesszővel tagolt** sztringet:

```
conf(0.652),pan(-3.963),leye(0.036,0.745),reye(0.084,0.746),mouth(0.056,0.790)
conf(0.588),pan(-9.550),leye(0.469,0.254),reye(0.555,0.250),mouth(0.507,0.340)
conf(0.098),pan(31.974),leye(0.528,0.284),reye(0.624,0.285),mouth(0.544,0.395)
```

| mező | jelentés | mért tartomány |
|---|---|---|
| `conf(f)` | a detektálás **megbízhatósága** | 0,098 … 0,652 |
| `pan(f)` | a fej **elfordulása**, előjeles | −9,55 … +31,97 |
| `leye(x,y)` | bal szem | relatív [0..1] képkoordináta |
| `reye(x,y)` | jobb szem | ugyanaz |
| `mouth(x,y)` | száj | ugyanaz |

*Bizonyítottsági fok: **megerősített** — a nyers oszlopértékek szó szerint
ezek. A `pan` mértékegysége (**fok**) a nagyságrendből következtetve
**erős**, nem megerősített.*

### 3.4/d `personalbumrecs` — a felismerési JAVASLAT és a pontszáma

Négy oszlop, két nemzedékben (a `2` utótag a `facetemplatesV2`-höz tartozik):

| oszlop | típus | tartalom |
|---|---|---|
| `personalbumrecs` / `…recs2` | u32 | a **javasolt** személy-album sorindexe; **`0xFFFFFFFF` = nincs javaslat** |
| `personalbumrecvalues` / `…values2` | u32 | a javaslat **pontszáma** (mért tartomány ≈ 5 100 … 6 300) |

A `recs` nem `-1` értékei ugyanabból a **109…117** tartományból valók, mint
a `personalbumid` — tehát ugyanaz az albumsor-index. A
`suggestionpersonalbumid` ennek a „megerősítésre váró" párja (a mintában
1 sor).

### 3.5 `contacts.xml`

A személynevek elsődleges forrása; a formátumot a
[`pmp-database.md`](pmp-database.md) „`contacts.xml`" szakasza írja le.

✅ **2026-08-22 óta MEGVAN** (a „B" telepítésben, 9 kontakttal). Az alak:

```xml
<contacts>
 <contact id="99b4c1ce30280815" name="&lt;Név&gt;"
          modified_time="2026-08-15T18:42:17+02:00" local_contact="1"/>
</contacts>
```

- `id` — 16 hex jegy, **ez egyezik** az `albumdata_albumcontactids` u64
  értékével (9/9 mérve, ld. 3.4/b);
- `local_contact="1"` — a kontakt **csak helyben** létezik, nincs
  Google-fiókhoz kötve;
- `modified_time` — ISO-8601, időzónával.

A `contact_id → név` leképezés innen **közvetlenül** olvasható; a 3.4
szerinti átfedéses levezetés csak akkor kell, ha ez a fájl hiányzik.

---

## 4. MIKOR — az érvényesülés pillanata

| művelet | mikor hat |
|---|---|
| detektálás | **háttérszálon**, folyamatosan (`BgFaceDetectThread`) |
| csoportosítás / javaslat | a detektálás után, saját folyamatjelzéssel |
| `.picasa.ini` írás (B útvonal) | `faces=` és `backuphash` mindig; `facedata` csak ha `FRWriteFaceDataINI` **be van kapcsolva** |
| képfájlba írás | `PersistFaceToFile` szerint, **kötegelt, megszakítható** munkaként |
| kontakt → ini sorrend | **előbb a `[contacts2]`**, és csak utána a `faces=` hivatkozás; ha a kontakt-írás hibázik, a `faces=` sor **sem** íródik ki (`0x007d55f0`) |

---

## 5. MI TÖRTÉNIK A MEGLÉVŐ ADATTAL — a három romboló művelet

Mindhárom **megerősítést kér**, és mindhárom szövege figyelmeztet arra,
hogy a **szinkronizált webalbumok névcímkéit is eltávolíthatja**.

| művelet | függvény | mit töröl |
|---|---|---|
| **`CThumbUI::RemoveAllFaceData`** | `0x006038b0` | **minden** arc-adat + minden személyi album, majd **teljes újrakeresés** |
| **`CThumbUI::ResetAllFaces`** | `0x00603a20` | **minden személyi album**, az arcok a **Név nélküliek** albumba kerülnek (az arcadat MEGMARAD) |
| **`CThumbUI::ResetAll`** | `0x00603bb0` | külön rákérdez: *„Szeretné eltávolítani az arcokkal kapcsolatos összes adatot az INI fájlokból?"* — a `faces` és `facedata` kulcsokat törli a `.picasa.ini`-kből |

Mindhárom elérhető a jobb fiók **Emberek** paneljéből
(`rightdrawerpanel/peoplepanel` → `peoplepanel/resetfaces`).

> ⭐ **REJTETT VISELKEDÉS: a menütétel MÓDOSÍTÓBILLENTYŰRE mást csinál.**
> Az „Arcok alaphelyzetbe állítása" (`0x9e11`) kezelője (`0x005cc83c`)
> **`GetAsyncKeyState`-tel** (`0x00c406f8`) megnézi, mi van lenyomva, és
> **háromfelé ágazik**:
>
> | lenyomva | mi történik |
> |---|---|
> | **Ctrl** | `0x006038b0` — **`RemoveAllFaceData`**: MINDEN arc-adat és személyi album törlése + teljes újrakeresés |
> | **Shift** | `0x00603a20` — **`ResetAllFaces`**: minden személyi album törlése, az arcok a „Név nélküliek" albumba |
> | semmi | `0x0057daa0` — csak a **kijelölés** arcainak alaphelyzetbe állítása |
>
> Mindkét romboló ág egy **belső kapcsolóhoz is kötött**
> (`byte [0xd67849] != 0`) — vagyis alapállapotban feltehetően rejtett,
> fejlesztői funkció. **Ugyanaz a menüpont tehát ártalmatlan és
> katasztrofális is lehet**, attól függően, mit tart lenyomva a
> felhasználó.

**A különbség lényege:** a `ResetAllFaces` a **neveket** dobja el, a
`RemoveAllFaceData` **magukat az arcokat is**.

---

## 6. MI FUT LE UTÁNA — a verzió-migráció

`0x00488880` (1 905 b), `CThumbDB::NeedFaceUpdate`. Két verziójelölőt tart
nyilván a `#contacts\` tárolóban:

| jelölő | elvárt érték |
|---|---|
| **`frversion`** | **`"1.5"`** |
| **`contactsversion`** | **`"1.0"`** |

Ha a tárolt érték eltér az elvárttól, a program felteszi a kérdést:

> *The face data needs to be updated. This will remove and rescan all of
> your faces.*
> **„Frissíteni kell az arcokkal kapcsolatos adatokat. Ez a művelet
> eltávolítja, majd újra beolvassa az összes arcot."**

⇒ **Egy importáló, ami `frversion`-t ír, `"1.5"`-öt írjon**, különben a
felhasználó Picasája teljes újraszkennelést fog kérni.

---

## 7. HIBAESETEK — amit a bináris megnevez

| eset | üzenet |
|---|---|
| csak olvasható fájl | *Face tag write failed for read only file: %s* |
| általános írási hiba | *Face tag write failed for: %s* |
| nincs arc a képen (útlevélkép-mód) | *Can't find any faces* — **Nem találhatók arcok** |
| több arc a képen | *There appear to be multiple faces.* — **Úgy tűnik, több arc van a képen.** |
| nincs webes névcímke-jog | `DownloadFacesNoFR` — hosszú, súgóra mutató üzenet |
| a kontakt-írás elbukott | *PersistContactToINI failed: err %d* → a `faces=` sem íródik |
| duplikált arc-művelet | *Duplicate face operation: photo_id=%llu, contact_id=%llu, rect=(%d,%d,%d,%d)* |
| a talált-személyek album törlése | *The found people album cannot be deleted.* — **A talált személyi album nem törölhető.** |

---

## 8. A BEÉPÍTETT, VÉDETT SZEMÉLYI ALBUM — EGY rekesz, KÉT token

⚠️ **Helyesbítés (2026-09-15, #3002).** A szakasz korábban „két beépített
albumot" írt. A `0x004ac650` diszasszemblálása és a valódi db3 mérése szerint
ez **egy** albumsor, amely **két token** közül az egyiket viseli — a
`]ignoreface` nem külön rekesz, hanem ugyanannak a rekesznek a másik
megjelenése. A részletes bizonyíték a 8/b pontban.

`0x004ac650` (456 b) hozza létre, album-tokennel:

| token | belső név | felirat (EN) | felirat (HU) | rendezőkulcs |
|---|---|---|---|---|
| **`]unknownface`** | `CThumbDB::unknownfacealbum` | *Unnamed* | **Név nélküliek** | `0x5f` = 95 |
| **`]ignoreface`** | `CThumbDB::ignorefacealbum` | *Ignored* | **Figyelmen kívül hagyva** | — |

Mindkettő a **`People`** kategóriába kerül (*Emberek*), és **nem
törölhető** (`CThumbUI::DeleteFacesAlbum`).

⚠️ **A „Név nélküliek" albumnak HÁROM felirata van**, állapottól függően:

| kulcs | HU felirat | mikor |
|---|---|---|
| `CThumbDB::unknownfacealbum` | **Név nélküliek** | nyugalmi állapot |
| `CThumbDB::unknownfacealbuminprogress` | **Személyek keresése** | miközben a keresés fut |
| `CAlbumLabel::Unnamed` | **Meg nem nevezett emberek** | a panel fejlécében |

A **nevesített** személyek albuma külön token: **`]facealbum:<id>`**.

### 8/b A két token EGY albumsoré — mért bizonyíték

**A binárisból** (`0x004ac650`, teljes törzs diszasszemblálva):

1. A függvény **előbb a `]unknownface`-t keresi, majd a `]ignoreface`-t**, és
   az albumot **csak akkor hozza létre, ha EGYIK SEM létezik**. Két külön
   rekesznél ez a feltétel értelmetlen volna: a másik megléte nem indokolná a
   kihagyást.
2. A megtalált (vagy létrehozott) **egyetlen** albumazonosítót a
   `[esi+0x16c]` tagba írja — nincs második tag a második albumnak.
3. Egy bool tag (`[esi+0x168]`) dönti el, hogy a rekesz a
   **`CThumbDB::unknownfacealbum` / „Unnamed"** vagy a
   **`CThumbDB::ignorefacealbum` / „Ignored"** feliratot és a hozzá tartozó
   tokent kapja-e. A függvény bemenő bool paramétere ezt a tagot **billenti**.
4. A `0x006030a0` ugyanezt az albumfejlécen mutatja: az
   `albumheader/%x/%d/showunknown` ↔ `albumheader/%x/%d/showignored` váltó
   cseréli a címet `CAlbumLabel::Unnamed` („Unnamed people") és
   `CAlbumLabel::Ignored` („Ignored people") között — **ugyanazon** a
   fejlécen. (Ugyanez a pár a 12. szakasz `unknownfaceheaderpanel`
   váltógombjainál.)

**A valódi db3-ból** (`research/testdata/Picasa2-arcok/Picasa2/db3`, a
tulajdonos erre készített telepítése, 144 `albumdata` sor, 3338 `imagedata`
sor):

| mérés | eredmény |
|---|---|
| `]ignoreface` token az `albumdata_token`-ben | **nincs egy sem** |
| `]unknownface` token | **egy** sor: `albumdata[2]`, neve „Név nélküliek" |
| egyéb `]`-tokenek | `]star`, `]updated`, `]screensaver`, `]search`, `]history:email`, `]history:upload` |
| `imagedata_personalbumid` nem nulla értékei | **115 db**, mind a `]facealbum:109…117` sorokra mutat (nevesített személyek) |
| ebből a `]unknownface`-re (2) mutató | **nulla** |

⇒ **A „Figyelmen kívül hagyva" rekesz tagsága a db3-ban nem létezik külön
adatként**, tehát a db3-importnak nincs mit átvennie hozzá. A rekesz a
futásidejű váltó egyik állása, nem tárolt fotóhalmaz. *(Ez a #3002 második
hátralévő pontjának a mért válasza — nem elmaradt munka, hanem negatív
lelet.)*

✅ **MEGVÁLASZOLVA (15.3/b.1, #3670):** az elvetett arc a `.picasa.ini` `faces=` sorában `ffffffffffffffff` személy-mezőt kap; token nincs. ~~⚠️ **Nyitva marad**, hova írja Picasa az egyedi arc „elvetve" állapotát.~~ A 9/b
pont ezt a `0x005c9b00`-ra alapozva a `.picasa.ini`-hez kötötte; ennek a
függvénynek a sztringkészlete viszont `.picasaoriginals`, `Deleting Files` és
`CThumbUI::DeleteProgress` tételeket is tartalmaz, tehát **legalábbis a
törlési ág is benne van**. A kulcs nevét egyik mérés sem adta meg — amíg nincs
meg, ne építsünk rá.

---

## 9. AZ EMBEREK PANEL — állapotok és feliratok

*Forrás: `editpanel.tre:935` (`editpanel/addfaceselection`) · `rightdrawerpanel.tre:48` (`rightdrawerpanel/peoplepanel`).*

*(Ez a szakasz szándékosan a működés UTÁN áll.)*

A panel `rightdrawerpanel/peoplepanel`, a csoport-rács `faceclusterpanel`,
soronként `faceclusterpanel_%d_addname` és `faceclusterpanel_%d_ignore`
vezérlőkkel.

| kulcs | HU felirat |
|---|---|
| `PeoplePanel::title` | **Emberek** |
| `PeoplePanel::Who` | **Ki látható ezeken a fotókon?** |
| `PeoplePanel::AddAName` | **Név hozzáadása** |
| `PeoplePanel::InThis` | **Ezen a fotón:** |
| `PeoplePanel::Known1` / `Known2` | **Szintén ezeken a fotókon:** / **Személyek ezeken a fotókon:** |
| `PeoplePanel::Unnamed` | **Név nélküli személycsoportok:** |
| `PeoplePanel::UnnamedCluster` | **Meg nem nevezett emberek ezeken a fotókon:** |
| `PeoplePanel::Cluster` | **%d fotó** |
| `PeoplePanel::SuggestionFmt` | **%s?** — a javaslat kérdőjellel |
| `PeoplePanel::Loading1` / `Loading2` | **Arcok betöltése a fájlhoz / %d fájlhoz…** |
| `PeoplePanel::SortingFaces` / `SortingData` | **Arcok rendezése… / Arcok adatainak rendezése, %.0f%%** |
| `PeoplePanel::Looking` | **További személyek keresése…** |
| `PeoplePanel::Unchecked` | **, %d ellenőrizetlen fájl.** |
| `PeopleAlbum::ConfirmText` | **Az egyezés megerősítéséhez kattintson a pipa, az elvetéshez pedig az „x" ikonra.** |
| `CFaceContact::SuggText1/2` | **1 javaslat / %d javaslat** |

**A „mellőzés" külön megerősítést kér**, saját „ne kérdezd többet"
jelölőnégyzettel:

| kulcs | HU |
|---|---|
| `PeoplePanel::ConfirmRemoveTitle` | **Személyek mellőzése** |
| `PeoplePanel::ConfirmRemoveMsg` | **Biztosan áthelyezi ezt a személyt a Mellőzött emberek albumba?** |
| `PeoplePanel::ConfirmRemoveYesButton` | **Személy mellőzése** |
| `PeoplePanel::ConfirmRemoveCheck` | **Ne kérdezzen újból, mindig hagyja figyelmen kívül** |

A képszerkesztőben az arc-átfedés a `faceoverlay/*` réteg
(`faceoverlay/label`, `faceoverlay/label_background`), a manuális
arc-hozzáadás az `editpanel/addfaceselection`, súgószövege:

> *Instructions: 1) Manipulate the rectangle to fit the face of the person
> you want to add…*

A rácsban a javaslat-jelvény az `adorners/suggestionfaceadorner`, a
listában az `adorners/listsuggestionfaceadorner`.

---

### 9/b ⛳ MIKOR melyik felirat — a `0x00647df0` döntési fája (2026-09-24, 356. kör, #3563; #4045 helyesbítve 2026-10-03)

*A 9. szakasz a feliratokat sorolja; ez azt, hogy a panel mikor melyiket
mutatja. Forrás: a `0x00647df0` (851 b) teljes törzse, a jelzők írói a
`0x0064c340` / `0x0064d0xx` frissítőben, és a `peoplepanel_text.tre`.*

**A kimenet két vezérlő** (a panelben név szerint keresve): a
`status_label` (`0x00ca10e0`) — a lista fölötti **fejléc** — és az
`instructions` (`0x00ca10f0`), amely a `peoplepanel_text.tre` öt
szövegváltozatából választ (`0x005123e0`: index a `+0x2fc` tömbbe):

| mód | `.tre` | magyar szöveg (`panel-feliratok-hu.tsv`) |
|---:|---|---|
| 0, 1 | `Text1`, `Text2` | „A Picasa a fotókeresés közben … automatikusan csoportosítja az arcokat. …” (az elnevezés útmutatója) |
| 2 | `Text3` | „A program még nem talált személyeket. …” |
| 3 | `Text4` | „Itt látható majd az aktuálisan kijelölt személlyel együtt megjelenő, megnevezett szereplők listája.” |
| 4 | `Text5` | „Itt jelenik meg a kijelölt fotókon szereplő személyek listája.” |

**A bemenetek** (a panel-objektum mezői):

| mező | jelentés | bizonyíték |
|---|---|---|
| 2. argumentum | **betöltés folyik** | a `Loading…`/`Looking…` ágak kapuja (`0x00647f93`, `0x00648070`) |
| `+0x348 >> 1` | a `+0x344` vektor **eredménysorainak száma** a szokásos Emberek-panel lekérdezésében (a gyűjtő csoportosított találatai; nem a kijelölt képek száma) | `0x00647f79`–`0x00647f84`; a normál frissítő `0x0064c227`-en hívja a gyűjtőt, majd `0x0064c23d`-nél a kérés `+0x18` kimenetét másolja a panel `+0x344` vektorába |
| `[panel+0x294]+0xdc >> 1` | a betöltési feliratban kiírt kijelölt fájlok száma | `0x00647fb1`–`0x00647fc7` (`"Loading %d files"` ág) |
| `+0x2ac` | **személy albuma van kiválasztva**: a jelenlegi album `albumcontactids` mezője nem nulla (`0x00448c90` → `0x00448fb0`), `setg` @ `0x0064d248` | ezt erősíti a 3-as mód szövege is |
| `+0x364` | a begyűjtés talált **megjeleníthető (megnevezett) személyt** — a gyűjtő `+0x11d` jelzőjéből másolva (`0x0064d7a9`), a gyűjtés indulása nullázza (`0x0063e032`) | **megerősítve a 9/c-ben:** a lekérdező `0x006c63d0` a kijelölt arcok `personalbumid`-jét gyűjti, és nem üres listánál `+0x4d = 1` (`0x006c6881`) |
| `+0x29c` | az **ellenőrizetlen** fájlok száma | `0x0064d1cb` (nullázás), `0x0064810b` (kiírás) |
| `editpanel/preview` látható | **egyképes szerkesztő** nézet | `0x00647f59`–`0x00647f73` |
| `+0x2ad`, `+0x2ae`, `+0x2af`, `+0x2b0` | a „Név nélküliek” album-mód jelzői (lent) | `0x0064c3d8`, `0x0064c50f`, `0x0064c4e6`, `0x0064c436` |

**A döntési fa** (a `+0x2ad` mód nélkül):

```
EGY EREDMÉNYSOROS ág — ha a szerkesztő előnézete látszik, VAGY
  (pontosan 1 eredménysor ÉS nem személy-album):
  betöltés            → „Arcok betöltése a fájlhoz...”            (Loading1)
  van személy (+364)  → „Ezen a fotón:”                            (InThis)
  van eredménysor     → „Ki látható ezeken a fotókon?”             (Who)
  különben            → instructions 4 („Itt jelenik meg …”)

NEM EGYSOROS ág — minden más eset (0 vagy legalább 2 eredménysor,
  illetve személy-album):
  betöltés            → személy-album ? „További személyek keresése...” (Looking)
                                      : „Arcok betöltése %d fájlhoz...” (Loading2)
  van személy (+364)  → személy-album ? „Szintén ezeken a fotókon:”     (Known1)
                                      : „Személyek ezeken a fotókon:”   (Known2)
  van eredménysor     → +2af ? „Meg nem nevezett emberek ezeken a fotókon:” (UnnamedCluster)
                             : „Név nélküli személycsoportok:”              (Unnamed)
  különben            → személy-album ? instructions 3 : instructions 4

UTÁNA mindig: ha +29c ≠ 0 ÉS nem személy-album → a fejléc mögé
  „, %d ellenőrizetlen fájl.” (Unchecked)
```

Címek: egysoros eredményág `0x00648070`–`0x006480cb`; többsoros/üres
eredményág `0x00647f93`–
`0x0064806e`; a kapu `0x00647f79`–`0x00647f8d`; az utótag `0x006480d7`–
`0x0064811c`. A fejléc a `status_label`-be kerül (`0x0064812d`,
`vtbl+0x14`).

**#4045 — a számláló eredete és a helyes ág-feltétel (2026-10-03).** A
`PeoplePanel::vftable` (`0x00ca1654`) RTTI-hez kötött `offset_map`-je és a
`paszta.py`-val végzett teljes `.text`-pásztázás ugyanazt a vektor-életciklust
mutatja. A `0x0064c340` normál módja meghívja a `0x0064bb70` frissítőt;
az `0x0064bb70` a kijelölt fájlokból készített kérést átadja a
`0x006c63d0` gyűjtőnek, majd a kérés `+0x18` eredményét másolja a panel
`+0x344` vektorába (`0x0064c227`–`0x0064c23d`). A gyűjtő a kérés `+8` / `+0x0c`
mezőjéből járja be a bemeneti fájlokat, az arc-rekordokat személyazonosító
szerint rendezi/csoportosítja (`0x006c6455`–`0x006c68a8`), és a
`+0x4d` jelzőt nem üres eredménynél állítja be (`0x006c687b`–`0x006c6881`).
Így a döntési kapu `+0x348 >> 1 == 1` feltétele **egy gyűjtő-eredménysort**
jelent. A két PeoplePanel-konstruktor (`0x0063e390`, `0x0063f200`) törzsében
nincs közvetlen `+0x344/+0x348` írás; a `0x0063f820` ürítő felszabadítja a
vektort, törli a méret felső részét a `+0x348` alacsony állapotbitjének
megtartásával, majd nullázza a mutatót (`0x0063f86a`–`0x0063f89a`). A
PeoplePanel virtuális frissítője (`0x0063f970`) a `0x00647270` sorszintű
kezelőt is meghívja; az a `+0x348 >> 1` értékkel határolja a sorkijelölést
(`0x0064727d`–`0x00647297`) és a meglévő eredményvektoron dolgozik. A teljes
`.text`-pásztázás másik találata, a `0x00645350`, ugyanezt az eredménysort
indexeli: a sorindex-argumentumot a panel `+0x348 >> 1` méretéhez hasonlítja
(`0x00645367`–`0x00645384`), majd a `+0x344` 8-bájtos sorvektorát építi újra
(`0x00645a12`–`0x00645ca3`). A hozzá tartozó `0x00649730` sorsegéd szintén a
`+0x348 >> 1` értékkel végez tartományellenőrzést (`0x00649730`–
`0x00649754`). A vektorméret írásakor az alacsony állapotbit megmarad, a
darabszámot pedig a felső bitek hordozzák (`0x00645b05`–`0x00645b0d`,
`0x00645c91`–`0x00645ca3`).

Hatókör: a `0x0064d660` alternatív, 3-as állapotú gyorsítótár-ág a
`[panel+0x294]+0xe8` vektort másolja a `+0x344`-be (`0x0064d737`–
`0x0064d765`); a `0x0064c340` Név nélküliek-album ága pedig másik
gyűjteményt épít ugyanebbe a mezőbe. Ezért a „gyűjtő eredménysorai” megnevezés
a normál, név szerinti lekérdezésre vonatkozik. A pásztázás azonos számbeli
eltolásra más osztályokban is talált hozzáférést; például a `0x00639440` /
`0x00639510` a `TagPanel::vftable` (`0x00ca0a24`) mezője, nem a PeoplePanelé.

**Független futtatásos ellenőrzés:** a `qemu-i386`-os próba a döntési blokkot
kézzel felépített panelobjektummal futtatta; a kijelölt fájlok száma /
eredménysorok száma mátrix kimenete `1/1 → InThis`, `1/2 → Known2`,
`2/1 → InThis`, `2/2 → Known2` (`SMSM`). Tehát több kijelölt képnél is az
„Ezen a fotón:” ág fut, ha egy eredménysor van; egy kijelölt képnél pedig a
többsoros ág fut, ha több eredménysor van. Ez a próba a bináris döntési
blokkot ellenőrzi, **nem** a teljes program felületét. A Colab-végrehajtón
kért, két képpel végzett élő UI-mérés **nincs meg**.

⇒ **A „Szintén ezeken a fotókon:” (Known1) a SZEMÉLY ALBUMÁNAK fejléce**:
ugyanaz a lista, amit máskor a „Személyek ezeken a fotókon:” vezet be — nem
egy második szakasz. Személy-albumban az egyképes „Ezen a fotón:” sem jelenik
meg (egy kijelölt képnél is a többképes ág fut), kivéve a szerkesztőben.

**A „Név nélküliek” album-mód** (`+0x2ad` igaz — a `0x00448a10` album-próba,
`0x0064c3c7`): `+0x2b0` ⇒ „Arcok adatainak rendezése...” (`status0`,
`0x00647ea9`); különben `+0x2ae` (a gyűjtemény listája üres, `0x0064c4fe`–
`0x0064c50f`) ⇒ üres fejléc és instructions 0/1 (`0x00431290` dönt,
`0x00647ee2`); különben 0 kép ⇒ instructions 2, majd a fenti fa. *Ennek a
módnak a pontos belépési feltétele (mit vizsgál a `0x00448a10`, ki állítja a
`+0x2b0`-t) az al-jegyé: **#3565**.*

#### Nálunk (forrásolvasással ellenőrizve, `PeoplePanel.qml`, #3566/#4045)

| helyzet | eredeti | nálunk |
|---|---|---|
| 1 kijelölt kép, pontosan 1 megnevezett eredménysor | „Ezen a fotón:” | ✅ `resultRowCount == 1` |
| több kijelölt kép, pontosan 1 megnevezett eredménysor | „Ezen a fotón:” | ✅ a megjelenő személy-sorok száma dönt, a képszám nem |
| 1 kijelölt kép, több megnevezett eredménysor | „Személyek ezeken a fotókon:” | ✅ a megjelenő személy-sorok száma dönt |
| több kijelölt kép, legalább 2 megnevezett eredménysor | „Személyek ezeken a fotókon:” | ✅ |
| személy albuma | **egyetlen** lista „Szintén ezeken a fotókon:” fejléccel (1 képnél is) | ✅ egy fejléc, egy lista: a kijelölt képek megnevezett emberei a nézett személy nélkül (#3678) |
| személy-album, a kijelölt képeken nincs más megnevezett személy | üres fejléc, instructions 3 (Text4) | ✅ üres fejléc és Text4 akkor is, ha a kijelölt képen csak a nézett személy szerepel (#3678) |
| egy kijelölt kép/arc, nincs megnevezett sor | „Ki látható ezeken a fotókon?” | ✅ a mért egysoros fejléc megmarad (#3566) |
| több kijelölt kép/arc, nincs megnevezett sor | „Név nélküli személycsoportok:” (a Névtelenek csoportosított nézetében „Meg nem nevezett emberek…”) | ✅ a helyi panel többes ága |
| van kijelölt kép, de a gyűjtő eredményvektora üres | instructions 4 (Text5) | ⚠️ a helyi panel a kijelölésszámot használja, ha nincs megnevezett sora; az eredeti gyűjtő ürességével való egyezés nyitott |
| betöltés közben | „Arcok betöltése…” / „További személyek keresése...” | ⛔ nincs: a `peopleOfRows` szinkron, nincs betöltési állapotunk |
| ellenőrizetlen fájlok | „, %d ellenőrizetlen fájl.” a fejléc mögött | ⛔ nincs: folyamatos háttér-arcellenőrzés híján nincs ilyen számunk |
| üres, nem személy-album | instructions 4 (Text5) | ✅ (#3566) |
| üres, személy-album | instructions 3 (Text4) | ✅ |
| „Név nélküliek” mód, 0 kijelölés | instructions 2 (Text3) | ✅ (#3566) |
| „Név nélküliek” mód, üres gyűjtemény | üres fejléc, instructions 0/1 (Text1/Text2) | ⛔ nincs: a két szöveg nincs meg nálunk; Text3 áll helyette |
| a szerkesztőben | mindig az egyképes ág; a nézett személy is szerepel | ✅ a néző panelje (`editorView`), szűrés nélkül (#3566, #3678) |
| névadás után, a panel sorában vagy a kép alatti mezőben | a fejléc „van személy” bemenete (`+0x364`) **nem frissül**: a szerkesztőben „Who is in these photos?” marad, amíg a panel teljes frissítése (pl. kijelölésváltás) le nem fut — **9/g** | ✅ #4812: a begépelt névadás nem frissíti a fejlécet; a sor élőben frissül |

*A #4045 „Nálunk” összevetése forrásolvasással és helyi QML-teszttel ellenőrzött;
az eredeti kétképes Colab-mérés továbbra sincs meg. A `Main.qml` normál
nézetben a kijelölt képek számát, a Névtelenek albumban a kijelölt arcok
számát adja a `selectionCount` mezőnek (`Main.qml:2950–2953`). A
`PeoplePanel.qml` a megnevezett sorok számát használja, ha azok vannak; ha
nincs megnevezett sora, a kijelölésszám őrzi az egyetlen névtelen esetek mért
„Who is in these photos?” fejlécét, illetve a többes ágat. A tesztmátrix
`1/1 → InThis`, `1/2 → Known2`, `2/1 → InThis`, `2/2 → Known2` kimenete
helyben, −5/0/+5 px ablakmagassággal ellenőrzött. A vegyes (megnevezett és
névtelen) találatok eredeti sorcsoportosításának és a kétképes Colab-esetnek
az élő ellenőrzése nyitott.*

*Bizonyítottsági fok: **megerősített** a döntési fára, a feliratokra, az öt
utasítás-módra, a személy-album jelzőre, a darabszámra és az ellenőrizetlen
utótagra (utasításszinten olvasva); a `+0x364` jelentése a 9/c-ben **megerősítve** (#3565).*

*A #4045 lelete: **megerősített** a `+0x348 >> 1` normál módú eredménysor-
jelentésére és a döntési kapura (utasításszintű írói adatfolyam + külön QEMU
ágmátrix). **Nyitott:** az eredeti Picasa felületén a kétképes/egyszemélyes
eset Colabos élő megfigyelése, valamint a vegyes névvel/név nélkül csoportok
számlálása.*

#### 9/c A két nyitott jelző kiolvasva (2026-09-24, 357. kör, #3565)

**A `+0x364` = a kijelölt arcok közül legalább egynek van személy-albuma.**
A panel frissítője (`0x0064bb70`) egy kérés-rekordot állít össze, és a
szinkron arc-lekérdezőnek adja (`0x006c63d0(&kérés, 0)`, `0x0064c227`); a
`+0x364` a rekord `+0x4d` bájtja (`[esp+0xad]` → `0x0064c272`). A lekérdező a
kijelölt képek × arcok kettős ciklusában (`0x006c6455`–`0x006c6870`) minden
arcra a `0x0044a6b0(adatbázis, sor, 0)`-t hívja: ez `0`-t ad, ha a sor
`filetype`-ja (`+0x114c` = az `imagedata` `+0x22c`) **nem** `0x3e9` = 1001
(arcsablon-bejegyzés, `picasa-mappakezelo.md`), különben a sor
**`personalbumid`** oszlopát (`+0x1bc0` = `imagedata +0xca0`; `1`-es
jelzővel a `suggestionpersonalbumid`-t, `+0x1c20`). A nem nulla értékeket
ismétlés nélkül gyűjti, és ha a lista nem üres, `mov byte [kérés+0x4d], 1`
(`0x006c6876`–`0x006c6881`). ⇒ A 9/b „erős” olvasata **megerősítve**.

**A „Név nélküliek” album-mód = a `]unknownface` VAGY a `]ignoreface` album.**
A `0x00448a10(album-gyűjtemény, album, jelző)` az album `+0xaf0` szöveges
oszlopát (a token) veti össze a gyűjtemény két tárolt tokenjével —
`+0x2e98` = `]unknownface`, `+0x2e94` = `]ignoreface` (beállítva
`0x00415e6e`, `0x00415e57`):

| token | jelző `0` | jelző `1` |
|---|---|---|
| `]unknownface` (Név nélküliek) | **igaz** | hamis |
| `]ignoreface` (Figyelmen kívül hagyva) | **igaz** | igaz |
| más | hamis | hamis |

(`0x00448a7b`–`0x00448c18`.) A panel a `0`-s jelzővel képzi a `+0x2ad`-t
(`0x0064c3c7`), az `1`-essel a `+0x36d = !…`-t (`0x0064c408`–`0x0064c422`,
tehát igaz a Név nélküliek albumon).

**A `+0x2b0` („Arcok adatainak rendezése...”) ebben a modulban nem áll 1-re.**
A `0x00630000`–`0x00660000` tartományban minden írása nulláz (`0x0063f320`
konstruktor, `0x0063f864`, `0x0064c436`), és szó-/duplaszó-írás vagy
`lea`-n át vett cím sem éri. *Hatókör:* a panelmodul; a teljes `.text`-ben a
`+0x2b0` eltolás más osztályokban is előfordul, azokat nem soroltam ide.

**A `+0x2ae` és a `+0x2af`** csak ebben a módban áll (`0x0064c4b5`–
`0x0064c50f`): ha a nézett gyűjtemény-csomópont `+0x3c9` jelzője be van
kapcsolva, `+0x2af = 1`, és `+0x2ae` = a csomópont listája üres. A `+0x3c9`-et
a `CAlbumSelectionNode` és a `CFoundFaceSelectionNode` vtáblájának
**50. rekesze** állítja (`0x0077fd20`, `0x007898b0`); ennek a rekesznek a
jelentése a **9/d**-ben: a csoportosított arcnézet (#3578).

*Bizonyítottsági fok: **megerősített** a `+0x364`-re és a
`0x00448a10`-re; a `+0x2b0`-ra negatív, a fenti hatókörrel.*

#### 9/d A „Név nélküliek” album csoportosítás-kapcsolója — ez dönt a két fejléc között (2026-09-25, 358. kör, #3578)

**A `+0x3c9` = csoportosított arcnézet.** A csomópont `+0x3c9` bájtját a
vtábla 50. rekesze (`0x0077fd20` / `0x007898b0`, `ret 8`, a 2. argumentum)
állítja; a hívója a `0x0074c200` (`0x0074c256`–`0x0074c266`:
`push (csoportosít ≠ 0)`, `push arg2`) — a `mov reg,[reg+0xc8]` + `call reg`
minta tíz előfordulása közül ez az egyetlen, amely két argumentumot ad át. Ez a függvény egyben
az album-fejléc utasítás-szövegét is választja (`0x0074c304` →
`0x00717810`):

| állapot | feltétel | fejléc-szöveg (`stringres`, magyar) |
|---|---|---|
| csoportosítva, a csoportosítás még fut | a csomópont `vtbl+0xb4` hamis | `CAlbumLabel::LoadingGrouped` — „Az arcok csoportosítása folyamatban van, kérjük, várjon...” |
| csoportosítva, Figyelmen kívül hagyva album | `+0x3c8`, `+0x3f0` és a `0x00783480` (a mellőzött-album próba) igaz | `CAlbumLabel::ToggleGroupIgnore` — „Jelöljön ki valakit, akit ismer, és adjon hozzá egy nevet.” |
| csoportosítva | különben | `CAlbumLabel::ToggleGrouped` — „Jelöljön ki valakit, akit ismer, és adjon hozzá egy nevet, vagy kattintson az "x" ikonra az adott személy mellőzéséhez.” |
| kibontva | | `CAlbumLabel::ToggleUnGrouped` — „Jelöljön ki valakit, akit ismer, és adjon hozzá egy nevet” |

(`0x0074c2c8`–`0x0074c2f9`.)

**Ki kapcsolja.** A fejléc parancskezelője (`0x0074cc00`) a vezérlő nevét a
`"cluster"`-rel veti össze (`0x0074cd50`–`0x0074cd8c`): **`cluster` ⇒
csoportosít**, minden más (a pár másik tagja, `showall`) ⇒ kibont. Az album
megnyitásakor a `0x0074cae0` **csoportosítva** indít (`push 1; push 1` @
`0x0074cbbb`, ugyanott a cím „Ignored people” / „Unnamed people”).

**A vezérlő egy váltógomb két arca** (`unknownfaceheaderpanel.tre`): a
`cluster` („Group by face” — „Csoportosítás arcok szerint”) és a `showall`
(„Expand groups” — „Csoportok részletes nézete”) ugyanabban a
`clustering_container`-ben ül, és egymást rejtik (`hidetarget` /
`showtarget`); a `cluster` kezdetben `m_hidden`. ⇒ Csoportosított állapotban
a „Csoportok részletes nézete” gomb látszik, kibontottban a „Csoportosítás
arcok szerint”.

⇒ **A 9/b fejléc-választója:** csoportosított nézetben „Meg nem nevezett
emberek ezeken a fotókon:” (`UnnamedCluster`), kibontottban „Név nélküli
személycsoportok:” (`Unnamed`).

#### Nálunk (mérve, `UnnamedFacesView.qml`)

| | eredeti | nálunk |
|---|---|---|
| a kapcsoló | **egy** váltógomb, két állapot (csoportosítva / kibontva) | ✅ egy váltógomb (`clusterToggleButton`), a felirat a másik állapotot nevezi meg (#3585) |
| kezdőállapot | csoportosítva | ✅ `grouped: true`, az album minden megnyitásakor újra csoportosítva |
| a fejléc-utasítás | a fenti négy szöveg | ✅ `unnamedInstructions`; a „várjon” a csoportosítás (lenyomat-számítás) futása alatt (#3585) |
| az Emberek-panel fejléce | az állapottól függ (fent) | ✅ a többképes ág két „Név nélküli…” fejléce (#3585); a fa többi ága is (#3566) |

Fejlesztés: **#3585** (a váltógomb és a fejléc-utasítás).

*Bizonyítottsági fok: **megerősített** — a beállító, egyetlen hívója, a
parancskezelő névösszevetése, a kezdőállapot és a `.tre` váltópár mind
utasítás-, illetve forrásszinten olvasva.*

#### 9/e A személy-album „Szintén ezeken a fotókon:” listája KIHAGYJA a nézett személyt (2026-10-01, #3678)

*Forrás: `0x0064c340` · `0x0064d197`–`0x0064d260` · `0x0063df90` (`0x0063e02c`) · `0x006c1ac0` (`0x006c1cfc`, `0x006c1d06`) · **`0x006c4630`** (`0x006c46f3`) · `0x0064d660` · `0x00647df0` — két egymástól független olvasat (lásd a bizonyítottsági fokot).*

**Kérdés (#3678):** a személy albumában a lista a kijelölt képek megnevezett embereit mutatja; szerepel-e benne maga a nézett személy is?

**Válasz — megerősített: NEM, a Picasa kihagyja.**

A lista rácsnézetben **nem** a 9/c-ben leírt általános lekérdezőből (`0x006c63d0`) jön, hanem egy külön, **személy-album-gyűjtőből**:

```
0x0064d197  call 0x57d500      ; az album személy-sorindexe: [[app+0xeac]+0x3c0], album híján -1
0x0064d1ab  call 0x448c90      ; nem személy-album → edi = 0 (0x0064d1b4 xor edi,edi)
0x0064d248  setg al / 0x0064d24b mov [ebx+0x2ac], al     ; a „személy-album” jelző (edi > 0)
0x0064d241  call 0x63df90      ; 4. argumentum = push edi → a kérés +0x44 mezője (0x0063e02c)
…háttérszál (0x006c7dd4) → 0x006c1ac0:
0x006c1cfc  cmp [edi+0x44], ebp   ; ha ≠ 0 és van kijelölés:
0x006c1d06  call 0x6c4630         ; a SZEMÉLY-ALBUM gyűjtője   (különben 0x006c1d32: 0x6c63d0, az általános)
```

A `0x006c4630` két ciklusa (a külső a kijelölt elemeken, a belső a hozzájuk tartozó kép arcain):

| cím | utasítás | mit hagy ki |
|---|---|---|
| `0x006c4662` | `call 0x44a6b0`, `je 0x6c49c8` | az elemet, ha nem arc-rekord (`filetype == 0x3e9`, ld. 9/c) |
| `0x006c46ce` | `cmp eax,[ecx+ebp*4]`, `je 0x6c4997` | a kijelölt arcot magát |
| `0x006c46e7` | `cmp ebp,ebx`, `je 0x6c4997` | a név nélküli arcot (`personalbumid` = 0) |
| **`0x006c46f3`** | **`cmp ebp, dword ptr [edi+0x44]`, `je 0x6c4997`** | **azt az arcot, amelynek `personalbumid`-je a NÉZETT album sorindexe** |
| `0x006c4705` | `call 0x4930c0`, `jne 0x6c4997` | az ismétlődést (egy személy a teljes kijelölésre legfeljebb egyszer) |

A felvett arcból egyelemű csoport lesz (`0x006c48c5`, `0x006c4974`), és `0x006c498d`-nél `mov byte [edi+0x4d], 1` jelzi, hogy van megjeleníthető megnevezett személy; a kitöltés `0x0064d660` (`0x0064d765`, `0x0064d77d`, `0x0064d7a9` → a panel `+0x344`, `+0x34c`, `+0x364` mezői), a sorokat a `0x0064ae90` építi, csoportonként egyet.

| helyzet (személy-album, rácsnézet) | mit mutat |
|---|---|
| a kijelölt képeken **csak a nézett személy** van | **nincs sor, `+0x364` = 0** → a fejléc **üres**, az `instructions` a **3-as** változat (`Text4`: „Itt látható majd az aktuálisan kijelölt személlyel együtt megjelenő, megnevezett szereplők listája.”); a „Szintén ezeken a fotókon:” **nem jelenik meg** üres listával (`0x00648032` → `0x00648057` → `mov eax,3` `0x00648069` → `0x005123e0`) |
| a nézett személy mellett **két másik megnevezett** személy | **két sor**, a nézett személy NINCS köztük, a fejléc „Szintén ezeken a fotókon:” (`0x00648017`); több kijelölt képnél a többi személy uniója, ismétlés nélkül |
| a **szerkesztő** nézete (előnézet látszik) | **MÁS ág**: a kérés `+0x44` mezője itt mindig 0 (`0x0064bc90`, `0x0064bca7`), a `0x006c63d0` és a `0x006c4a30` pedig nem is olvassa a `+0x44`-et ⇒ a nézett személy **benne van** az „Ezen a fotón:” listában (az egyképes ág: `0x00647f73` → `0x00648070`; a fejléc „Ezen a fotón:”, ha van megnevezett személy) |

⇒ A 9/c leírása a **szerkesztő** útját (általános lekérdező) írja le, nem a rácsnézetét: ott a nézett személy kihagyása a `0x006c4630`-ban él.

**Nálunk (mérve, olvasással — `origin/main`):** `PeoplePanel.qml:66` a `people` tulajdonság a `peopleHere`-t adja változtatás nélkül, a `peopleOfRows` (`people_controller.py:295`) pedig a kijelölt képek MINDEN megnevezett emberét számolja — a nézett személyt is. A `currentPerson` a fejléc-választásra megy (`personAlbum`), a lista szűrésére nem. ⇒ személy-albumban a nézett személy **szerepel** a listában; eltér az eredetitől.

**Teendő:** a `PeoplePanel.qml`-ben, ha `personAlbum && !editorView`, a `people` lista **hagyja ki** a `currentPerson` nevű (kis-nagybetű-tűrően összevetett) elemet; ha így a lista üres, az üres-lista ágat kell mutatni (`Text4`, üres fejléc), nem a „Szintén ezeken a fotókon:” fejlécet üres listával. A szerkesztőben (`editorView`) a szűrés NEM fut.

⭐ **#4045 eredménye — a 9/b kapuja a gyűjtő eredménysorait, nem a kijelölt képeket számolja.** A `+0x344` a normál lekérdezés csoportosított kimenete (`0x0064c227`–`0x0064c23d`), így a `+0x348 >> 1 == 1` feltétel egy eredménysor. A kijelölt fájlok külön száma a `[panel+0x294]+0xdc >> 1` mezőből kerül a Loading-feliratba (`0x00647fb1`–`0x00647fc7`). A kapu `0x00647f84`–`0x00647f8d` tehát **pontosan 1 eredménysor ÉS nem személy-album**; több kép egyetlen megnevezett eredménysorral is az „Ezen a fotón:” ágra jut, míg egy kép több eredménysorral a „Személyek ezeken a fotókon:” ágra. A QEMU-mátrix ezt a döntési blokkban ellenőrizte. Az eredeti felület két képpel végzett Colab-mérése **nincs meg**, ezért a jegy az élő megfigyelésig nyitva marad.

*Bizonyítottsági fok: **megerősített** — a kihagyó összehasonlítás (`0x006c46f3`), a kijelölt arc és a név nélküli arc kihagyása, az ismétlésszűrés, a `+0x44` útja az album sorindexétől a gyűjtőig, és a felirat-választó két ága utasításszinten olvasva, **két független olvasat egyezik** (a második a specek és a korábbi válasz nélkül, friss Opus-ügynök). **Erős:** a két képtípus táblázata (a kódútból olvasva, élő mérés nincs); hogy a `0x3e9` típus arc-rekordot jelent (következtetés: a rekord szülője a `+0x20`). **NINCS MÉRVE:** a sorok végső sorrendje (`0x0064ae90`), és élő felvétel a személy-album panelről (a Colab-végrehajtón egy névadás + személy-album lépéssor kell hozzá).*

#### 9/f A mellőzött arc a nézőben; a kézi hozzáadás; a személy-mező értékkészlete (2026-10-01, #3793)

*Forrás: élő mérés (eredeti angol Picasa 3.9.141, `picasa-colab-jobs` #72, #73, #74, #75; kulcsképek: `Colab EN 37 - Mellozott arc a nezoben.png`, `Colab EN 38 - Nem mellozott nev nelkuli arc a nezoben.png`) · `0x00483cb0` (`0x00483ff0`–`0x00484012`) · `0x0064c340` → `0x0064bb70` (`0x0064c227`) → `0x006c63d0` (`0x006c63fd`) · `0x00642c10` · `0x00641960` · `0x004841f0` (`0x004842c2`–`0x004842f9`) · `0x0049d560` · `0x0092c450` (`0x0092c476`) · `0x00484820` · `0x0049d390` · `0x007d55f0` · `0x00644900` · `0x006443e0` · `0x0064a410` — két egymástól független olvasat egyezik.*

**A kérdés (#3793):** mit mutat az eredeti nézője a mellőzött (`ffffffffffffffff`) arcon?

**Válasz — megerősített: SEMMIT.** A mellőzött arcnak a szerkesztőben **nincs kerete és nincs „Add a name” felirata**, és az Emberek panel sem sorolja fel.

| állapot (szerkesztő, Emberek panel nyitva) | mit látni | forrás |
|---|---|---|
| **mellőzött** arc (`portre_1_ff.jpg`, `faces=rect64(27c00680d8ffdb3f),ffffffffffffffff`) | a képen **nincs keret**, az arc helyére kattintva sem; **nincs „Type a name”**; a panel: „People who appear in the currently selected photos will be listed here.” (`Text5`) + „Add a person manually” | #72 `kepernyo__15`, `__17`; #75 `__19`, `__21`; `Colab EN 37` |
| **nem mellőzött névtelen** arc (`portre_2_szines.jpg`) | alapból nincs keret; az **arcra kattintva** keret + „Type a name” a kép alatt; a panelben arcbélyeg + „X” + „Add a name” mező, a fejléc „Who is in these photos?” | #73 `kepernyo__09`; #74 `__09`; `Colab EN 38` |

**A mechanizmus.** A néző NEM a `-1` azonosítót veti össze, hanem azt, tagja-e az arc a `]ignoreface` albumnak:
- az arc-lekérdező egyetlen arcforrása a `0x00483cb0` (a `0x006c63d0` hívja `0x006c63fd`-nál; a `0x00483cb0`-nak ez az egyetlen hívóhelye); `0x00483ff5 mov eax,[ebx+0x2e94]` (a `]ignoreface` token, `0x00c80e58`) → `0x0048400b call 0x4db180` (album-tagság) → `0x00484012 jne 0x484023`: **az album tagját nem másolja a listába**;
- az eredmény a panel `+0x344` listájába kerül (`0x0064c23d`); a keretrajzoló (`0x00642c10`, `faceoverlay/%d`) és a felirat (`0x00641960`, üres névnél „Add a name”, `0x00641a5e`) csak ebből a listából dolgozik ⇒ a mellőzött arcnak **nincs** keret-rétege és felirata;
- a `-1` összevetés csak az ini **betöltésekor** van (`0x004841f0`, `0x004842c2 and eax,ebp` / `cmp eax,-1`): ha az arcnak nincs személy-albuma, a `0x004842f9 call 0x4d9aa0` beteszi a `]ignoreface` albumba (`[db+0x2e94]`); az új arc előbb a `]unknownface`-be kerül (`0x0047fcc2`) — onnan a `]ignoreface`-be kerülés **nem** távolítja ki (erős).

**A személy-mező értékkészlete — betöltés és írás.**

| `faces=` személy-mező | betöltéskor | íráskor |
|---|---|---|
| 16 jegyű hexa | arc-rekord + kontakt (ha ismeretlen: „<Unknown Person>” kontakt jön létre); mindkét speciális albumból kikerül (`0x004844f0`) | megnevezett arc: `%I64x` (kisbetűs, nincs kitöltve, `0x0049d390`, `0x0049d493`) |
| **`ffffffffffffffff`** | arc-rekord → a **`]ignoreface`** albumba (`0x004842c2`–`0x004842f9`) ⇒ a nézőben nincs | **mellőzött** arc (`0x00484bc3 call 0x449a00` igaz → `push -1; push -1`, `0x00484bd0`) — az `ffff…` EGYETLEN forrása a mellőzés |
| **`0`** | **nem keletkezik arc**: a személy-mező olvasója (`0x0092c450`) a `"0"` sztringre `-1`-et ad (`0x0092c476 mov esi,0xc7fe6c`, `repe cmpsb`, `0x0092c4ba or eax,-1`), a bontó (`0x0049d560`, `0x0049d725`–`0x0049d72c`) a bejegyzést **a négyszöggel együtt eldobja** | a `0x00484820` **soha nem ír `0`-t**; a felismert, nem megnevezett, nem mellőzött arc **kimarad** a `faces=` sorból |

- A korpusz 696 darab `,0` értékének eredete a **Web Albums letöltés** metaadat-írója (`0x007d55f0`, hívója a „Web Albums”/`feed.rss` sztringet használja): az azonosító kezdőértéke 0 (`0x007d5a07`), csak nem üres név és `[arc+0x24] == 1` mellett oldódik fel (`0x007d5a37`–`0x007d5a62`), a rekord ettől függetlenül bekerül (`0x007d5b42`–`0x007d5c85`). A `0x00484820` és az export-író (`0x0068b320`, a `0x004855c0` hívja, `push 1`) `0`-t nem ír.
- A `faces=` formázónak (`0x0049d390`) pontosan három hívóhelye van (`0x00485061`, `0x0068ba9a`, `0x007d5d10`; indextől független pásztázás).

**A kézi hozzáadás („Add a person manually”) névtelen négyszöget NEM ment.** Az arcot a négyszögből és a kontakt-azonosítóból egyedül a `0x00644900` hozza létre (`0x00644b94 call 0x4841f0`; a `0x004841f0` hívói indextől függetlenül csak `0x0045b85c`, `0x0045ba5c`, `0x00644b94`), és csak **nem nulla kontakt-azonosítóval** hívódik (`0x00644671 or eax,ecx` / `0x00644673 je 0x6446e8`):
- **Escape:** a véglegesítő ág le sem fut (`0x0064455e cmp byte [ebp+0xc],bl` / `jne 0x644716`);
- **üres Enter / elvetett kontakt-párbeszéd:** a kontakt-azonosító 0 marad, `0x00644900` nem hívódik; a `peoplepanel/manual_cancel` kezelője (`0x0064a410`) csak a felületet állítja vissza (nincs adatbázis- vagy ini-hívás);
- **névvel** (Enter vagy az automatikus kiegészítésből választott név, `0x006441d4`/`0x006446cd`): `faces=rect64(…),<16 jegyű kontakt-azonosító>`, a kontakt a `[Contacts2]`-be kerül.
⇒ **Névtelen kézi négyszög a `.picasa.ini`-be nem kerülhet: se `0`, se `ffffffffffffffff`.**

**Nálunk (mérve, olvasással — `origin/main`):**
- `app/faces_helper.py:56` `facesFor`: **minden** `faces=` bejegyzést visszaad, az `ffffffffffffffff`-et is (üres névvel) ⇒ a `FacesOverlay.qml` mellőzött arcra is keretet és „Add a name” feliratot rajzol;
- `FacesHelper.addFace` / `renameFace` üres névnél a `UNIDENTIFIED_CONTACT = "ffffffffffffffff"` (`ini/faces.py:16`) azonosítót írja (`_resolve_contact_id`, `faces_helper.py:160`); a `FacesOverlay.qml:329`–`334` `commitEditor` üres névvel is hívja ⇒ a kézzel rajzolt, meg nem nevezett négyszög a Picasa szerint **mellőzött** arcként töltődik be;
- `Face.is_identified` (`ini/faces.py:28`) és a modul docstringje a régi, téves jelentésre épül („azonosítatlan arc contact_id-ja csupa `f`”);
- az arckeretek megjelenítésének módja nálunk (állandó keret vs. kattintásra) **nincs mérve**.

**Teendő:**
1. `facesFor` (a néző/szerkesztő arc-rétege): az `ffffffffffffffff` személy-mezőjű bejegyzést **hagyja ki** (nincs keret, nincs „Add a name”); a **`0`** személy-mezőjű bejegyzést se mutassa. A round-trip-hez a sorok a `.picasa.ini`-ben **érintetlenek** maradnak.
2. `commitEditor` / `addFace` / `renameFace`: **üres névnél ne írjon semmit** (a kézi négyszög névvel menthető); a `0`-t és az `ffffffffffffffff`-et se írja ki meg nem nevezett arcra. Az `renameFace` üres névvel (a név levétele) az eredetiben a bejegyzés **törlése**, nem `ffff…` (mért: `picasa-colab-jobs` #68, ld. a 15.3/b.1 táblát).
3. Az `ffffffffffffffff` írója **kizárólag** a mellőzés (`FaceScanController`, #3670); a `Face.is_identified` jelentése és a docstring helyesbítve.

⛔ **Helyesbítés a 3.1 és a 18.2 szakaszhoz (erős):** a `Preferences\FRWriteFaceDataINI` kapcsoló (`0x00484dcf`/`0x00484e1d`) csak a **`facedata`** kulcsot kapuzza; a `faces=` MINDEN esetben kiíródik (`0x0048516d`). A „pozícióhű `0`-kitöltés” (`0x00484f28`–`0x00484f64`, `push 0x30` `0x00484f38`) a `facedata` értékét építi, nem a `faces=`-t.

*Bizonyítottsági fok: **megerősített** — az élő mérés (a nézőben nincs keret/felirat a mellőzött arcon; a nem mellőzöttön van), a `]ignoreface`-szűrés (`0x00483ff0`), a személy-mező értékkészlete az írón és az olvasón, a kézi hozzáadás névtelen négyszögének nem-mentése; **két egymástól független olvasat egyezik** (az első a specekkel, a második a specek és az első válasz nélkül, friss Opus-ügynök). **Erős:** az `ffff` arc a `]unknownface`-ben is benne marad; a `FRWriteFaceDataINI` csak a `facedata`-t kapuzza (egy olvasat). **NINCS MÉRVE:** a mellőzött arc megjelenése a Névtelenek albumban/People-nézetben (`0x00474630`, `0x004755d0` a következő lépés); az arckeretek megjelenítési módja nálunk; a Colab-végrehajtó húzás-lépése nélkül kézi négyszög élőben nem rajzolható.*

#### 9/g Névadás után a fejléc „van személy” bemenete NEM frissül — a sor igen (2026-10-12, #4812)

*Forrás: élő mérés (eredeti angol Picasa 3.9, `picasa-colab-jobs` #113, `job-113` `kepernyo__07`–`__21`) · `0x006443e0` · `0x00644010` · `0x00645350` · `0x00642c10` (`0x00642c2a`) · `0x00647df0` · `0x0063f970` · `0x006022a0` · `0x005c78d0` · a `+0x364` írói a `0x00630000`–`0x00660000` tartományban (pásztázás).*

**Kérdés (#4812, a #4522 maradéka):** a 9/b fája szerint a szerkesztőben, megnevezett arcnál a fejléc „In this photo:”. A #113 felvételén viszont névadás után „Who is in these photos?” látszik. Melyik a helyes, és mikor vált a fejléc?

**Válasz — mindkettő, más-más időpontban.** A panel sorában vagy a kép alatti mezőben végzett névadás után az eredeti **újraszámolja** a fejlécet, de a „van megnevezett személy” jelzőt (`+0x364`, 9/c) **a névadás előtti értéken hagyja**. Ezért a szerkesztőben a fejléc „Who is in these photos?” marad, a sorban viszont már a név áll. Az „In this photo:” csak a panel következő **teljes frissítésekor** jelenik meg, például kijelölésváltáskor vagy a kép újranyitásakor.

**Az élő mérés (#113).** A szerkesztőben egy névtelen arc van. A panel sorában „Add a name” → „Teszt Elek” + Enter → People párbeszéd → New Person → OK. Mit mutatnak a képkockák:

| képkocka | sor | fejléc |
|---|---|---|
| `__07`–`__12` (névadás előtt) | arcbélyeg + „Add a name” | „Who is in these photos?” |
| `__15` (a párbeszéd nyitva) | üres mező | „Who is in these photos?” |
| `__19`, `__21` (OK után, további 5 + 3 mp várakozással) | **„Teszt Elek”** | **„Who is in these photos?”** |

**A mechanizmus.** A `0x006443e0` a panel szerkesztőmezőinek véglegesítője. Azt, hogy melyik mezőről van szó, a vezérlő neve dönti el:

| jelző | vezérlő | cím |
|---|---|---|
| `[esp+0xd]` | `peoplepanel/manual_add_editbox` | `0x0064442e` |
| `[esp+0xc]` | `peoplepanel/overlayeditbox` (a kép alatti „Type a name”) | `0x00644477` |
| `[esp+0xe]` | `peoplepanel/editbox` (a sor „Add a name” mezője) | `0x006444c0` |
| `[esp+0xf]` | `peoplepanel/header_editbox` | `0x00644509` |

A sor és a kép alatti mező útja:

```
0x0064460e  call 0x64d7d0          ; névfeloldás; ismeretlen névnél a kontakt-párbeszéd
                                   ;   ("contacts"/"search"/"fullname", 0x7b8f80); mégse → 0xf4241
0x00644615  jne 0x644708           ;   → nincs hozzárendelés (a takarító rész így is lefut)
0x006446f8  call 0x645350          ; (panel, [panel+0x374] = a szerkesztett sor, kontakt)
0x00644725  mov [esi+0x374], -1
0x00644774  call [vtbl+0x68]       ; listac_parent / overlay_parent elrejtése
0x00644798 / 0x006447b7  call 0x642c10   ; al = 0
0x00642c2a  call 0x647df0          ; (panel, 0) → a 9/b fája, „nem tölt”
```

A `0x00645350` (4419 bájt) a `+0x344`/`+0x348` sorvektort építi újra (9/b), a **`+0x364`-hez viszont nem nyúl**. A tartomány pásztázása szerint a `+0x364`-et csak három hely írja:

- `0x0064c272`: a `0x0064bb70` gyűjtője, amelyet csak a teljes frissítő (`0x0064c340`) hív;
- `0x0064c489`: nullázás a `0x0064c340`-ben;
- `0x0064d7a9`: a háttérgyűjtés eredményének átvétele (`0x0064d660`).

A `0x00647df0` tehát a régi `+0x364 = 0` értéket olvassa (`0x00648082`). A szerkesztőben az előnézet látszik, így az egysoros ág fut, és a sor megvan → **Who** (`0x00648070`–`0x006480cb`). Ez pontosan a #113 képe.

**Mikor frissül mégis.** A teljes frissítő (`0x0064c340` → `0x0064bb70` → `+0x364`) hívói:

| esemény | út |
|---|---|
| `peoplepanel/update` | `0x0063f970` (a PeoplePanel vtáblájának `0x00ca16d0` rekesze) → `0x0063fac8` (ha `[panel+0x20c] == 0`; különben a `0x0064c2e0` csak a `+0x2ad`-t állítja) |
| `peoplepanel/forceupdate` | ugyanott → `0x0063fb49` |
| a fenti kettő küldője | a `0x006022a0`, a **`selection_changed`** szórója a jobb oldali fiók paneljeinek (`0x006022e9`–`0x006022f0`); ezen kívül a `0x005796c0` (`il_RefreshThumbs`) és a `0x0074cc00` (a Névtelenek fejlécének parancskezelője, 9/d) |
| kézi hozzáadás névvel | `0x006446cd` `0x644900` → `0x006446d8` `0x64c340`; az automatikus kiegészítésből: `0x006441d4` → `0x006441dc` `0x6442f0` → `0x006443cd` `0x64c340` |
| név választása az automatikus kiegészítés listájából, a sorban | `0x00644010`, a `PeoplePanel::AutoCompleteProvider` vtábla (`0x00ca1774`) `0x00ca1778`-as bejegyzése: `0x00644203` `0x645350`, majd **csak akkor** `0x0064423c` `0x64c340`, ha a `0x005c78d0` igaz. Ez a `0x00448a10`-et hívja `0`-s jelzővel (9/c), tehát akkor igaz, ha a nézett album a **Név nélküliek vagy a Figyelmen kívül hagyva**. Különben `0x0064425f` `0x642c10` jön, vagyis ugyanaz az elavult jelző |

⇒ **A kép újranyitása után „In this photo:” áll.** Az újranyitás kijelölésváltás, ezért a teljes frissítés fut: a gyűjtő megtalálja a most már `personalbumid`-del bíró arcot (9/c), a `+0x364` 1 lesz, és a szerkesztő egysoros ága az InThis feliratot adja. A #4522 „In this photo:” tesztje (megnevezett arc, frissen betöltve) tehát ezt az állapotot írja le helyesen.

**Nálunk (forrásolvasással, `origin/main`).** A `PeoplePanel.qml` `baseHeaderText`-je a `hasPeople`-ből számol (`people.length > 0`). A `peopleHere` élő kötés: `(peopleFaceRevision, photos.revision, controller.peopleOfRows(…))` (`Main.qml:3799`, `PhotoViewer.qml:4889`). A `nameFaceFromPanel` → `assignNameToFace` → `assignNameToFaces` után az új sor azonnal megjelenik (#4522 tesztje), ezzel a `hasPeople` igaz lesz, és a fejléc **azonnal** „In this photo:”-ra vált. ⇒ **Eltért az eredetitől** (a `origin/main`-en); a javítás után a begépelt névadás nem frissíti a fejlécet (✅ #4812).

**✅ Megoldva (#4812):** a fejléc „van személy” bemenete pillanatkép. A begépelt névadás (a sor és a kép alatti mező) nem veszi fel újra, így a szerkesztőben „Who is in these photos?” marad; a panel sorai és a sorszám (`resultRowCount`) élőben frissülnek. Az elfogadott javaslat útja változatlan: a Név nélküliek albumban frissít.

*Bizonyítottsági fok: **megerősített**, hogy a sorban és a kép alatti mezőben végzett névadás a fejlécet elavult `+0x364`-gyel számolja újra. A véglegesítő útja és a `0x00642c10` → `0x00647df0` hívás utasításszinten olvasva; a `0x00645350` nem ír `+0x364`-et; az élő #113 felvétel egyezik. **Erős:** az újranyitás utáni „In this photo:”, mert a `selection_changed` → `peoplepanel/update` → `0x0064c340` út statikusan olvasva, élő felvétel nincs róla. **Hatókör:** a `+0x364` írói a `0x00630000`–`0x00660000` tartomány 410 indexelt függvényében pásztázva; a modulon kívüli, a panelmutatót argumentumként kapó író nincs kizárva. Az ellenőrzésre egy egylépéses Colab-felvétel elég: a #113 lépései után egy kép-váltás oda-vissza.*

---

## 10. Eredeti / nálunk / teendő

| # | | eredeti | nálunk | teendő |
|---|---|---|---|---|
| 1 | detektáló motor | háttérszál, 8 rekesz | **nincs** (3. fázis) | #26 |
| 2 | `faces=` olvasás/írás | `rect64(hex),<contact_id>` | a `zfill(16)` **már helyes** (`ini/rect64.py:35`) | ✅ **nincs teendő** — ld. 13/b |
| 3 | **`facedata` ini-kulcs** | írja, ha `FRWriteFaceDataINI` be | **nem ismertük**, de a round-trip **MEGŐRZI** (mérve) | ✅ **nincs teendő** — ld. 13/b |
| 4 | `deferredface` / `deferredregion` import | két külön oszlop, átfedéssel | **nincs importálva** | ebből jön a `contact_id → név` tábla |
| 5 | `facerect` értelmezése | **logikai jelző**, nem rect | a specünk „szentinel"-nek írta | helyesbítve (3.3) |
| 6 | `ffffffffffffffff` | a `.picasa.ini`-ben: **mellőzött arc** (mérve, 15.3/b.1) | — | ne személyként importáljuk; a „Mellőzött emberek” közé tartozik |
| 7 | duplikált kontakt | előfordul (mérve) | — | az importáló tűrje |
| 8 | **egy** beépített album, két tokennel | `]unknownface` ↔ `]ignoreface` váltó, **nem törölhető** | **nincs** | 8/b — a db3-ban nincs külön elvetett-tagság |
| 9 | két küszöb | 50–95, ötösével, alap 85 | **nincs** | ha lesz motorunk, ugyanez a létra |
| 10 | `frversion` | **`"1.5"`** | — | importáláskor ezt írjuk |

### 10/b. Az átvétel BELÉPÉSI PONTJA megvan (2026-09-19, #3132)

A 4. sor gépezete (`pmpimport/db3_atvetel.py` + `arcatvetel.py`) a #3002/#3184
óta kész és tesztelt, de a `src/` alól **semmi nem hívta** — az adat a
felhasználónál nem mozdult. A hiányzó rész nem fejlesztői részletkérdés volt,
hanem termékdöntés: mikor nyúljon a program a fotók mellé írt adatokhoz.

A tulajdonos 2026-09-18-án választott a három felkínált hely közül:

> `A menüpont (Eszközök ▸ Import a Picasából…)`

⇒ az átvétel **kérésre** fut, bármikor megismételhető, és a végén SZÁMOKAT ad:
hány mappát érintett, hány fotóra került kulcsszó / hely / név, és hányat
hagytunk ki azért, mert ott már állt adat („A" szabály — meglévőt nem írunk
felül).

⚠️ **SAJÁT funkció**: az eredetinek ilyen parancsa nincs és nem is lehet — ő
MAGA a db3 gazdája. A menütétel ezért a #1701 jelölését viseli (`sajat: true`),
és a mért menüszerkezet UTÁN, külön csoportban áll, hogy az eredeti sorrendjéből
semmit ne toljon el.

Kód: `app/picasa_import_controller.py`, `qml/PicasaPy/PicasaDataImportDialog.qml`.
Őrök: `tests/app/test_picasa_import_vezerlo_3132.py`,
`tests/app/qml_functional/test_import_menupont_3132.py`.

---

## 11. Bizonyítottsági fok

- **Megerősített:** a beállításkulcsok, alapértékek és a küszöb-létra
  (kód + ugrótábla-bájtok); a két ini-írási útvonal és a `FRWriteFaceDataINI`
  kapu; a három romboló művelet; a verzió-migráció; a beépített album
  tokene és feliratai; a PMP-oszlopok típusa, sorszáma és tartalma (élő
  adaton mérve); a `facedata` **nulla** korpusz-előfordulása.
- **Erős:** a `contact_id → név` leképezés levezetése a két deferred oszlop
  átfedéséből (3 047 egyértelmű eset, 98,2 %).
- **Feltételes:** hogy a `deferredregion` kizárólag a nevesített
  részhalmazt tartalmazza — 15 mért ellenpélda van (ld. 12).

---

## 12. Nyitott kérdések mérlege

| # | kérdés | állapot |
|---|---|---|
| 1 | A `facerect` `0x1` pontos jelentése | **LEZÁRVA (2026-08-22)** — a „B" telepítés megmutatta: az oszlop VEGYES, valódi rect64-et tárol megerősített régiónál, `1`-et jelzőként detektálás után (3.3). ~~BLOKKOLT~~ — az adat csak annyit bizonyít, hogy fájlonkénti logikai jelző; az írási hely a binárisban nincs feltárva. ⭐ **2026-09-06:** a folytatást elvittük a bájtszintű pásztázás határáig. A `0x004127c0` **nem** író, hanem a gyűjtemény **konstruktora** (`CColumn<unsigned___int64,1,322043908>`, vtábla `0x00c8230c`; a destruktor `0x00413020`), a `facerect` neve az egész binárisban **egyetlen** helyen áll (`0x00412d25`), és **öt** keresési utat kizártunk — a részletes lista és a MIÉRT a `picasa-imagedata-rekord.md` „Ki ÍRJA a `facerect`-et" szakaszában. ⭐ **2026-09-06 — A BINÁRIS IS MEGERŐSÍTETTE, és megvan az ÍRÓ.** A `FUN_00446610` **háromfelé** ágazik: `facerect == 1` → nulla téglalap + `0xF4240` visszatérési kód (`0x004466b4`, `0x004466eb`); `facerect == 0` → tartalék út (`FUN_00448270`); minden más → `rect64` kicsomagolás (`0x004467b2`) és képpontra váltás a `width`/`height` oszloppal. Ugyanez a küszöb (`> 1`) a `FUN_00446370` logikai tömbjében is (`0x0044657c`–`0x00446585`). Az ÍRÓ a **`FUN_00480040`** (`0x004810b3`/`0x004810bc`), és **csak NULLA értékre ír** (`0x00480de7`–`0x00480df1`) ⇒ a meglévő téglalapot és az `1`-es jelzőt nem írja felül. Részletek: `picasa-imagedata-rekord.md`. ⭐ **2026-09-06 — AZ `1` ÍRÓJA IS MEGVAN:** a `FUN_00446960(gazda, sorlista, bájt, jelző)` előjelesen 64 bitre kiterjesztve írja a bájtot a `facerect` sorába (`0x004473f1` `movsx`, `0x00447402` `cdq`, `0x00447403`/`0x0044740a`), és a hívója a **Mappakezelő** arcfelismerés-kapcsolója: `FUN_007c4df0` (`CFolderMgrDialog::confirmfrexclude`) → `FUN_005cef20` → `FUN_00491210`, ami `0x00491627`-nél **1**-gyel, `0x00491636`-nál **0**-val hív. ⇒ **a kizárt mappák képei kapják az `1`-et**, és mivel az író csak nulla értékre ír, ez **megvédi őket az újra-detektálástól**. A kérdés LEZÁRVA (#2515). |
| 2 | A `facerectdata` szerepe | **LEZÁRVA (2026-08-22)** — arc-JELLEMZŐPONTOK: `conf`, `pan`, `leye`, `reye`, `mouth` (3.4/c). ~~BLOKKOLT~~ — 0 nem üres sor, nincs mit mérni; élő, arc-sablonos adatbázis kellene. Jegy: **#1238** (`felhasználóra-vár`: nevesített arcokat tartalmazó `db3` másolat) |
| 3 | Az `albumcontactids` szemantikája | **LEZÁRVA (2026-08-22)** — album → kontakt-azonosító, 9/9 egyezés a `contacts.xml`-lel (3.4/b). A két `*checksum` **továbbra is BLOKKOLT** — a 14.2 szakasz rögzíti a mért értékeket, a kilenc megdőlt hipotézist és a folytatás pontos helyét. ~~BLOKKOLT~~ — mind 0 soros; ugyanaz a külső anyag kell. Jegy: **#1238** |
| 4 | A `deferredregion` a nevesített részhalmaz-e | **LEZÁRVA (nemleges)** — 15 mért ellenpélda cáfolja a tiszta részhalmaz-viszonyt; a lap 3.4 rögzíti feltételesként |
| 5 | A `contact_id` hash képzési szabálya | **HATÓKÖRÖN KÍVÜL** — és 2026-08-22 óta tárgytalan is: az azonosító **telepítésfüggő**, tehát importáláskor amúgy sem használható kulcsként; a **név** az egyeztetés alapja (3.4/b). — az importáláshoz nem kell: az azonosítót nem mi képezzük, hanem olvassuk. Ha valaha kell, a `contacts.xml` adja a leképezést |
| 6 | A `facedata` kulcs értékének pontos mezőszerkezete | **LEZÁRVA (tárgytalan)** — 0 korpusz-előfordulás, alapból kikapcsolt kapcsoló; a teendő a megőrzés, nem az értelmezés |
| 7 | A `0x9e1c` azonosító **ütközése**: ugyanez az érték a feltöltés-beállítások felugró menüjében is szerepel (`ImpULOpts::ID_ALLOW_COLLAB`, rekord `0xd6f334`) | **LEZÁRVA (nem a mi gondunk)** — más menücsalád, más szétosztó-hívó; nálunk a parancsazonosítókat nem globális névtérként vesszük át, hanem menünként. Ha valaki mégis globálisan egyedinek tekintené, előbb ellenőrizze, befut-e ez a felugró a `0x005cb990`-be |
| 8 | A `0xa0cd` (Hozzáadás az Emberek albumhoz) tényleges kezelője | **BLOKKOLT** — nincs saját ága a szétosztóban, az alapértelmezett ágra fut (`0x0069aeb0`), amiben egyetlen sztring sincs; futásidőben töltött almenü gyanúja. Jegy: **#1238** |
| 9 | A `CreateAcceleratorTableA` (`0x0092321a`) tartalma | **LEZÁRVA (2026-08-22, 14.1)** — egyetlen hívás, **egyelemű, csupa nulla** ACCEL, kizárólag az OLE helyben-aktiválás `OLEINPLACEFRAMEINFO`-jához. **Nincs alkalmazás-szintű gyorsítótábla.** |

```
Nyitott kérdések: 0 nyílt · 9 lezárva · 1 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

*(Tizenegy tétel. **2026-08-22-én a tulajdonos adott egy nevesített arcokat
tartalmazó adatbázist**, amivel az 1., 2. és 3. tétel LEZÁRULT. Ami maradt
blokkoltként: a két `*checksum` oszlop képzési szabálya és a
`CreateAcceleratorTableA` tartalma (8., 9.). „Csak nyitva" egy sincs.)*

---

## 13/b Két NEGATÍV eredmény a saját kódunkról — mérve, ne járjátok újra

A kör két olyan leletet talált, ami elsőre a mi kódunk hibájának látszott.
**Mindkettő megdőlt** — a kód már helyes. Ezt azért rögzítjük, hogy a
következő kör ne kezdje elölről:

1. **A `rect64` vezető nulláinak pótlása.** A mérés szerint a Picasa
   hexéből 8 jegyűig lekophat a vezető nulla. A mi dekóderünk
   (`src/picasapy/ini/rect64.py:35`) **már `zfill(16)`-ot végez**, és a
   modul docstringje ki is mondja, miért. **Nincs teendő.**

2. **A `facedata` kulcs megőrzése round-tripnél.** Lemérve a
   `document.py` API-ján:

   | eset | eredmény |
   |---|---|
   | érintetlen fájl újraszerializálása | **bájtra azonos** |
   | `facedata` megmarad érintetlenül | **igen** |
   | `facedata` megmarad EGY MÁSIK kulcs módosítása után is | **igen** |

   A dokumentum-réteg az ismeretlen kulcsokat általánosan megőrzi, tehát
   a `facedata` külön kezelést **nem igényel**. **Nincs teendő.**

---

## 13. Amit KIZÁRTAM

- Hogy a `facerect` valaha geometriát tárolna ebben a formátumban —
  **nem**: 7 044 sorban nulla darab harmadik érték.
- Hogy az arcfelismerés „nem futott le" a tesztkészletben — **nem**:
  13 941 nevesített régió van a `deferredregion`-ben.
- Hogy a `.picasa.ini` arc-írásának egyetlen útvonala volna — **nem**:
  kettő van, külön kapuval (3.1).
- Hogy a `facetemplatesV2` biometrikus sablon jelen volna a
  tesztkészletben — **nem**: 4 bájt, csak a magic.

---

## 14. A két maradék blokkolt tétel — LEZÁRVA és NEM ELDÖNTVE (2026-08-22)

### 14.1 ✅ A gyorsítótábla: NINCS alkalmazás-szintű gyorsbillentyű — bizonyítva

A korábbi állítás („a menüben nincs gyorsbillentyű, de a futásidejű
`CreateAcceleratorTableA` tartalma nincs feltárva") most **teljes** lett.

A binárisban **egyetlen** `CreateAcceleratorTableA` hívás van
(`0x0092321a`, IAT `0x00c406e4` — pefile-lal ellenőrizve), és a hívás
környezete szó szerint ez:

```asm
0x00923200  push 1                       ; cAccel = 1  (EGYETLEN bejegyzés)
0x00923202  lea  eax, [esp+0x10]
0x00923206  push eax                     ; lpaccl
0x00923207  mov  byte ptr [esp+0x14], 0  ; ACCEL.fVirt = 0
0x0092320c  mov  word ptr [esp+0x16], 0  ; ACCEL.key   = 0
0x00923213  mov  word ptr [esp+0x18], 0  ; ACCEL.cmd   = 0
0x0092321a  call dword ptr [0xc406e4]    ; CreateAcceleratorTableA
0x00923220  mov  [esi+0x98], eax
```

**A tábla egyetlen bejegyzése csupa nulla** — nincs benne billentyű és
nincs benne parancsazonosító.

**Miért létezik akkor egyáltalán?** A hívást követő blokk egy 20 bájtos
struktúrát tölt ki:

| eltolás | érték | `OLEINPLACEFRAMEINFO` mező |
|---|---|---|
| `+0x00` | `0x14` (= 20) | `cb` |
| `+0x04` | `(esi+0x6c >> 2) & 1` | `fMDIApp` |
| `+0x08` | **`GetParent(hwnd)`** (IAT `0x00c40804`) | `hwndFrame` |
| `+0x0c` | a most létrehozott `HACCEL` | `haccel` |
| `+0x10` | `haccel != 0 ? 1 : 0` | `cAccelEntries` |

Ez pontosan az **OLE helyben-aktiválás** (`IOleInPlaceSite::GetWindowContext`)
szerződése. A Windows itt **nem fogad el NULL-t**, ezért a program egy
üres, egyelemű táblát gyárt — kizárólag azért, hogy legyen érvényes
fogantyú a beágyazott (böngésző-)vezérlőnek.

> ✅ **A pontos, végleges állítás:** a Picasa **nem használ Win32
> gyorsítótáblát a menüparancsaihoz** — sem az arcfelismerés tíz
> menütételéhez, sem máshoz. A menüben látható gyorsbillentyűket (Ctrl+A
> stb.) a program a **saját billentyű-útján** dolgozza fel, nem
> `TranslateAccelerator`-ral. A 1.3 szakasz „egyiknek sincs
> gyorsbillentyűje" állítása tehát **mindkét szinten** igaz.

*Bizonyítottsági fok: **megerősített** — egyetlen hívási hely, szó szerint
olvasott argumentumok, pefile-lal feloldott import-nevek.*

### 14.2 ⛔ A két `*checksum` oszlop képlete — NEM DŐLT EL

**Nem találgatom meg.** Amit tudok, és amit próbáltam:

**A mért adat** (a „B" telepítés, 9 személy-album):

| album | tagok | `albumpeoplechecksum` |
|---|---|---|
| 109 | 32 | `0x8DAB10B8` |
| 110 | 42 | `0xDC7A570C` |
| 111 | 19 | `0x5CCEB284` |
| 112 | **1** | **`0x00000000`** |
| 113 | 2 | `0x00060B93` |
| 114 | 4 | `0x030331FE` |
| 115 | 7 | `0x98B4584D` |
| 116 | 2 | `0x00063CE2` |
| 117 | 6 | `0x9204CA91` |

**Egy szerkezeti megfigyelés, ami erős, de nem elég:** az érték
**nagysága együtt nő a taglétszámmal**, és az azonos taglétszámú albumok
felső bitjei is egyeznek (két 2-tagú album: `0x0006_0B93` és
`0x0006_3CE2`). Ez **akkumuláló, szorzás-összeadás típusú hash**-re vall,
ami 32 biten telítődik — de a szorzót 9 mintából nem lehet visszafejteni.
Az 1-tagú album `0` értéke ezzel nem magyarázható meg (vagy az első tag
hozzájárulása 0, vagy az érték „még nem számolt").

**Az `imagedata_peoplealbumchecksum`** (u16) a mintában **kizárólag `34`
(0x22)** értéket vesz fel, 301 soron — és ezek a sorok **alig fedik át**
(3/301) a `personalbumid != 0` sorokat. Egyetlen érték mellett a képlet
elvileg sem visszafejthető.

**Amit KIPRÓBÁLTAM (mind negatív, 0/9):** `crc32` az album `uid`-jén, a
néven, a `contact_id` little-endian bájtjain, a `contact_id` hex-alakján;
a `contact_id` alsó 32 bitje; a felső és alsó fele XOR-olva; `crc32` a
tag-sorindexek tömbjén; a tag-sorindexek összege; az MD5 első 32 bitje a
néven.

**Amit a kód felől kipróbáltam:** az oszlop-objektum eltolásait
(`albumdata+0x27b0`, `imagedata+0x10c8`) végigszkenneltem a teljes
`.text`-en. A találatok **kizárólag a regisztrációban és egy általános
gyorsítótár-karbantartó rutinban** vannak (`0x0048bd80`, `0x0048c100`,
`0x0048ef20`) — az író nincs köztük. **Kontroll-mérés:** a
`personalbumid`-ra (amiről *tudjuk*, hogy íródik) ugyanez a szken
**szintén csak a regisztrációt** adja. Vagyis az oszlopokat írásnál
**nem a `[db+eltolás]` úton érik el**, hanem regisztráció után kapott
indexszel — ezért ez a keresési út **elvileg sem vezethet** az íróhoz.

**Hol folytassa, aki nekiáll:** a `0x004127c0` / `0x00415790`
regisztrációk **sorrendjéből** kell kiszámolni az oszlop **indexét**, majd
a generikus oszlop-beállító (a `0x00494c50` / `0x004961b0` konstruktorok
párja) hívásait szűrni erre az indexre.

**Miért nem sürgős:** mindkét oszlop **származtatott, gyorsítótár-jellegű**
adat (a nevük is `checksum`), amit a Picasa maga újraszámol. Egy
importálónak **nem kell előállítania** — és a PicasaPy nem is ír
PMP-fájlt. A kérdés tehát **tudásbeli hiány, nem megvalósítási akadály**.

```
14. szakasz mérlege: 1 LEZÁRVA · 1 NEM ELDŐLT (a folytatás pontos helyével)
```

### 14.3 A #1238 LEZÁRVA — az adat, amit kért, már megvolt (2026-09-04)

A **#1238** jegy hat `db3`-oszlopot nevezett meg „értelmezhetetlenként", és
a tulajdonostól kérte egy végigfuttatott arcfelismerésű `db3` mappa
másolatát. **Az az adat 2026-08-22 óta megvan és fel van dolgozva** — ez a
14. szakasz és a „`peoplealbumchecksum` NEM checksum" szakasz épp abból
készült.

Egy 2026-09-04-i **független újramérés** (a tulajdonos 2026-08-22-i
adatmappa-mentése, saját `pmpimport` olvasónkkal) a lap számait
**változtatás nélkül** visszaadta:

| oszlop | mért |
|---|---|
| `albumdata_category` = **8** | **10 sor** = a személy-albumok; ebből **9** nevesített (van `albumcontactid`), a tizedik a névtelen-gyűjtő |
| `albumdata_albumcontactids` | 9 nem üres, u64 |
| `albumdata_albumpeoplechecksum` | 8 nem nulla (a 9-ből egy `0`) |
| `imagedata_personalbumid` | **115** nem nulla, értékkészlete a személy-albumok sorindexe |
| `imagedata_suggestionpersonalbumid` | **1** nem nulla |
| `imagedata_peoplealbumchecksum` | 301 nem üres, **mind ugyanaz az érték** |

⇒ A jegy **hatóköre teljesült**; ami marad, az kizárólag a **14.2 képlet-kérdése**,
és az ott van nyilvántartva, a folytatás pontos helyével. A jegy nyitva
hagyása félrevezette a kutatói kört: `ready` címkével a munkalistán állt,
miközben a kért anyag rég a birtokunkban volt.

*(Adatvédelem: a személy-albumok a tulajdonos családtagjainak nevét
viselik, és a `contactid`-k személyazonosítók — sem a nevek, sem az
azonosítók nem kerülnek erre a lapra.)*


## A `peoplealbumchecksum` NEM checksum — konstans arc-jelző (2026-08-24)

A #1238 három oszlopot nevezett meg értelmezhetetlenként. A
`research/testdata/Picasa2-arcok/Picasa2/db3/` (a nevesített arcokat
tartalmazó, **már a repóban lévő** adatbázis) egyiket eldönti.

### `imagedata_peoplealbumchecksum` — egyetlen érték: 34

| mérés | eredmény |
|---|---|
| sorok | 19 636 |
| nem nulla | **301** |
| **különböző nem-nulla érték** | **1 darab: `34` (`0x0022`)** |
| ebből `facerect`-tel rendelkező | **300 / 301** |
| a 115 `personalbumid`-os képből mennyi hordozza | **3** |

⇒ **Ez nem képenkénti ellenőrzőösszeg.** Egyetlen konstans, ami gyakorlatilag
azokon a képeken áll, amiknek **arckeretük** van — és **nem** azokon,
amiknek személy-albumuk. Állapot- vagy verziójelző, nem hash.

> A név megtévesztő. A `checksum` szó azt sugallja, hogy a személy-albumok
> tagságából képződik — a mérés szerint nem: a `personalbumid`-os képek
> **97%-án nincs** rajta.

### `albumdata_albumpeoplechecksum` — ⛔ EZ A SZAKASZ ELAVULT (a képlet MEGVAN, ld. 14.6)

> ⚠️ **Ne ez alapján dolgozz.** A 14.6 szakasz (2026-09-05, #2391) **megfejtette**
> a képletet, és a tulajdonos valódi katalógusán 9 albumból 8-on **bitre**
> egyezik: `acc = rol(acc, 7) XOR képindex`, két szűrővel. Az alábbi
> „nincs megfejtve" állítás 2026-09-05 óta **nem igaz**; a szakasz azért
> marad meg, mert a **három megdőlt hipotézise** továbbra is érvényes
> negatív lelet.

Kilenc nevesített személy-album (`]facealbum:109` … `]facealbum:117`),
nyolc nem nulla, egymástól független 32 bites érték.

**Három megdőlt hipotézis — hogy ne járjuk be újra:**

1. **„Az `albumcontactids`-ből képződik."** ❌ Mind a kilenc albumra
   kipróbálva az alsó 32 bit, a felső 32 bit és a kettő XOR-ja — **egyik sem**
   egyezik egyetlen albumnál sem.
2. **„A tagképek `peoplealbumchecksum`-jaiból halmozódik."** ❌ A vizsgált
   albumok minden tagképének `peoplealbumchecksum`-ja **0**, miközben az
   album-checksum nem nulla. (És a fenti mérés szerint az az oszlop amúgy is
   konstans.)
3. **„Egyszerű `a·K + b` a tagképek sorindexein."** ❌ A két 2 tagú albumra
   (`0x00060b93` és `0x00063ce2`) nincs olyan egész `K`, ami mindkettőt adná.

**Ami a következő lépés:** ⛔ **HELYESBÍTVE (2026-09-05, 14.4):** a korábbi
javaslat („a tagképek fájlazonosítói") **találgatás volt, adatoldalról**.
A 14.4 szakasz megmutatja, hogy a kérdés **kódoldalról** sokkal szűkebb: a
teljes binárisban **hat** hely nyúl a `albumpeoplechecksum` oszlophoz, és
közülük **egyetlen** írja.

### A többi oszlop állapota ugyanebben az adatbázisban

| oszlop | sorok | nem üres |
|---|---|---|
| `albumdata_albumcontactids` | 118 | 9 |
| `albumdata_albumpeoplechecksum` | 118 | 8 |
| `imagedata_personalbumid` | 3 338 | **115** |
| `imagedata_suggestionpersonalbumid` | 3 337 | **1** |
| `imagedata_facerectdata` | 4 344 | **2 977** |

*Bizonyítottsági fok: **megerősített** a `peoplealbumchecksum` konstans
voltára és az arckeret-korrelációra (valódi adaton mérve); **megerősített
negatívum** a három megdőlt hipotézisre. ⛔ **Az `albumpeoplechecksum`
képzési szabálya 2026-09-05 óta MEGVAN** (14.6) — a fenti „nyitva marad"
elavult.*

⚠️ **Adatvédelem:** a szóban forgó adatbázis valódi családi neveket
tartalmaz. A mérések ide csak **album-indexszel** kerülnek, névvel soha.

---

## 15. A SZEMÉLY-ALBUM FEJLÉCSÁVJA — a javaslat-munkafolyamat FELÜLETE (2026-09-03)

A lap eddig a **motort** és az **adatot** írta le (3–4. szakasz). A
felület, amin a felhasználó a javaslatokat jóváhagyja vagy elveti,
hiányzott. Ez a szakasz azt pótolja — a `faceheaderpanel` a személy-album
fejlécsávja, `unknownfaceheaderpanel` pedig az „Ismeretlen emberek"
albumé.

### 15.1 Miért nem találta eddig a lefedettségi mérés

A panel elemeire a kód **nem a `faceheaderpanel/…` teljes néven**
hivatkozik, hanem **puszta levélnéven** (`faceheaderpanel/confirmsug`, `faceheaderpanel/moresug`, …), és
a példányosításkor **dinamikusan generált** névteret használ:

| sablon | cím |
|---|---|
| `albumheader/%x/%d` | `0x0074ad40` |
| `albumheader/%x/%d/face_zoom` · `…/picture_zoom` | `0x00767e50` |
| `globalalbums%x/%d` | `0x0074ad40` |
| `albumheader_%d %x` | `0x0074ad40` |

⇒ A `string_xrefs`-ben **nulla** találat van `faceheaderpanel/`-re. A
panel-építő (`0x0074ad40`, 3938 b) három változat közül választ:
`headerpanel` · `faceheaderpanel` · `unknownfaceheaderpanel`.

### 15.2 A TELJES parancskészlet — a fejlécsáv elosztójából

A `0x005e0f70` (3930 b) `repe cmpsb`-vel veti össze a megnyomott elem
**levélnevét**, és **25 parancsot** ismer. A javaslat-munkafolyamathoz
tartozók vastagon.

A tábla ezért levélneveket sorol; a teljes név a fejlécsáv paneljéé —
`headerpanel/websync1`, `headerpanel/sync_options`,
`headerpanel/view_online` és így tovább (#2530). Ugyanez a három parancs a
`faceheaderpanel` és az `unknownfaceheaderpanel` változatban is így hívódik:
az elosztó a levélnevet nézi, nem a panelt.

| # | parancs | kezelő | cím az elosztóban |
|---:|---|---|---|
| 1 | `websync0` / `websync1` | `0x005e26a0` | `0x005e1026`, `0x005e105c` |
| 2 | `sync_options` | `0x005e26a0` | `0x005e1092` |
| 3 | `save_edits` | `0x0053a790` | `0x005e10e6` |
| 4 | `create_cd` | `0x009cd8a0` | `0x005e113a` |
| 5 | `create_movie` | `0x0057cb60` | `0x005e118a` |
| 6 | `create_collage` | `0x007463c0` | `0x005e120a` |
| 7 | `select_star` | `0x005e50c0` | `0x005e1271` |
| 8 | `pwa_button` | `0x00543ad0` | `0x005e12c0` |
| 9 | `face_zoom` / `picture_zoom` | `0x005e5290` | `0x005e1314`, `0x005e134b`, `0x005e1b56` |
| 10 | `showunknown` / `showignored` | `0x005e5110` | `0x005e1381`, `0x005e13b7` |
| 11 | `select_faces` | `0x005e5110` | `0x005e13ed` |
| 12 | `play` | `0x005e8a70` | `0x005e143c` |
| 13 | `share` | `0x0059e920` | `0x005e148d` |
| 14 | `view_online` | `0x005e0ef0` | `0x005e14df` |
| 15 | **`selectsug`** | `0x006024e0` | `0x005e1520` |
| 16 | **`moresug`** | **`0x00602890`** | `0x005e1570` |
| 17 | **`confirmsug`** | **`0x00602640`** | `0x005e15bf` |
| 18 | **`confirmsel`** | **`0x00602640`** ⛔ (helyesbítve, 18.1) | `0x005e160f` |
| 19 | **`ignore`** | **`0x005c9b00`** | `0x005e1645` |
| 20 | **`addname`** | **`0x00602970`** | `0x005e169a` |
| 21 | **`sug_filter`** | vtable-hívás | `0x005e16e9` |
| 22 | **`removesel`** | **`0x005c9b00`** | `0x005e177b` |
| 23 | `create_face_movie` | `0x00603660` | `0x005e17d0` |
| 24 | `set_thumbnail` | `0x00603660` | `0x005e180c` |
| 25 | `folderbutton` | `0x004adfe0` | `0x005e185b` |

**A táblában LEVÉLNÉV áll**, mert az elosztó is a levélnevet hasonlítja
(`repe cmpsb`), és ugyanaz a parancs a három fejléc-változat
(`headerpanel` · `faceheaderpanel` · `unknownfaceheaderpanel`) bármelyikéből
jöhet. A leltárban TELJES néven szereplő elemek, amelyeket ez a tábla leír:
`headerpanel/websync0`, `headerpanel/websync1`, `headerpanel/sync_options`,
`headerpanel/view_online`, `faceheaderpanel/moresug`.

### 15.3 MIT CSINÁLNAK — a három adat-válasz

#### a) „További javaslatok keresése" LEJJEBB VISZI A KÜSZÖBÖT

A `faceheaderpanel/moresug` kezelője (`0x00602890`, 216 b) beolvassa a beállítást és
számol:

```
0x006028be  mov  dword ptr [esp+0x18], 0x55   ; alapérték 85 (= a 1.2 pont FRSuggestionThreshold-ja)
0x006028c6  call 0x00407a20                   ; "Preferences" / "FRSuggestionThreshold"
0x006028cf  call 0x004019b0                   ; kiolvasás
0x0060293a  fdiv qword ptr [0xcf3a08]         ; ÷ 100.0
0x00602949  fsub qword ptr [0xc7dd30]         ; − 0.1
0x0060295b  call 0x0047baf0                   ; a keresés indítása ezzel az értékkel
```

⇒ **`küszöb = FRSuggestionThreshold / 100 − 0,1`**, alapértéken
**0,85 − 0,1 = 0,75**. A konstansok kiolvasva: `0x00cf3a08` = **100.0**,
`0x00c7dd30` = **0.1**, az alapérték **0x55 = 85**.

⛔ **A gomb NEM írja vissza a beállítást.** A `0x00602890`-ben **nincs**
`0x00401900` (a beállítás-író) hívás — mechanikusan ellenőrizve. Vagyis
ismételt megnyomás **ugyanazt** a 0,1-del csökkentett küszöböt használja,
nem visz egyre lejjebb.

#### b) Az ELVETÉS a `.picasa.ini`-be ír

> ⛔ **HELYESBÍTVE (18.1):** ez a pont eredetileg a `confirmsel`-t is ide sorolta.
> A `confirmsel` valójában a `0x00602640`-re megy (a `confirmsug`-gal közös
> kezelő, `push 0` / `push 1` különbséggel), és **az adatbázisba** ír — ld. 18.2.
> Az alábbi `.picasa.ini`-tábla az `ignore` és a `removesel` útja.

A `faceheaderpanel/ignore` és a `faceheaderpanel/removesel` **ugyanazt** a kezelőt hívja
(`0x005c9b00`, 5744 b), és annak sztringjei megnevezik a tárolót:

| sztring | mi |
|---|---|
| `.picasa.ini` | a célfájl |
| **`]ignoreface`** | az elvetett arc jelölése |
| **`]unknownface`** | az ismeretlen arc jelölése |
| `]search` | (ugyanennek a kezelőnek a másik ága) |

⇒ A javaslat elvetése **nem** az adatbázisban marad: a `.picasa.ini`
kapja meg — ugyanabban a rendszerben, amit a 3.1 pont ír le.

#### b.1 ⭐ MÉRVE: mit ír valójában a `.picasa.ini`-be (2026-09-27, 372. kör, #3670)

A fenti b) pont a `0x005c9b00` sztringkészletéből következtetett. **Ez két helyen téves:**
- a kezelő a `]ignoreface` / `]unknownface` tokent **nem írja**, csak összeveti a jelenlegi album tokenjével (`repe cmpsb`, `0x005c9c17`–`0x005c9c21`, `0x005c9f72`–`0x005c9f7e`);
- az arcot a „Figyelmen kívül hagyva” albumba sorolja át (`[db+0x2e94]`, `0x005c9f9e`–`0x005c9fb4`).

Az elosztó így hívja: `ignore` → `0x005c9b00(ui, 1, 1, 0)` (`0x005e1675`–`0x005e167c`), `removesel` → `0x005c9b00(ui, 0, 0, 0)` (`0x005e17ab`–`0x005e17b2`).

**Élő mérés az eredeti angol Picasa 3.9.141-en** (Colab-végrehajtó, picasa-colab-jobs #61–#68, `kimenet: picasa_ini`). A tesztmappa két valódi portrét tartalmaz, a Picasa 6 arcot talált:

| lépés | a mappa `.picasa.ini`-je utána | job |
|---|---|---|
| felismerés, érintetlenül | **nincs `.picasa.ini`** | #61 |
| az első arc „X”-e → *Ignore People* megerősítés → **Ignore Person** | `[portre_1_ff.jpg]` · `faces=rect64(27c00680d8ffdb3f),ffffffffffffffff` · `backuphash=49926` | #64 |
| (ellenpróba) egy másik arc elnevezése (*New Person*) | `[Contacts2]` · `bf1dfa69cbadd03d=<név>;;` · `[portre_2_szines.jpg]` · `faces=rect64(29402955d87fb57f),bf1dfa69cbadd03d` | #66 |
| (ellenpróba) ugyanennek az arcnak a **Remove**-ja a személy-albumból → vissza a névtelenek közé | a `faces=` sor **törlődik** (a szakasz csak `backuphash`-t tart) | #68 |

⇒ **A `faces=` személy-mezője a `.picasa.ini`-ben:**

| érték | jelentés |
|---|---|
| nincs `faces=` sor | névtelen (felismert, de nem mellőzött) arc; ezek csak az adatbázisban élnek |
| 16 jegyű azonosító | elnevezett arc; a név a `[Contacts2]` szakaszban |
| **`ffffffffffffffff`** | **mellőzött arc** („Mellőzött emberek” album) |

**`]ignoreface` token a fájlban nincs.** A korpusz 1 995 `ffff…`-értéke tehát a tulajdonos mellőzött arcai. A `0` (696×) eredetét ez a mérés nem érintette.

**A megerősítő kérdés** (kulcskép: `Colab EN 36 - Ignore People megerosites.png`):

| elem | angol | **hivatalos magyar** |
|---|---|---|
| cím (`PeoplePanel::ConfirmRemoveTitle`) | Ignore People | **Személyek mellőzése** |
| szöveg (`PeoplePanel::ConfirmRemoveMsg`) | Are you sure you want to move this person to the ignored people album? | **Biztosan áthelyezi ezt a személyt a Mellőzött emberek albumba?** |
| jelölő (`PeoplePanel::ConfirmRemoveCheck`) | Don't ask again, always ignore | **Ne kérdezzen újból, mindig hagyja figyelmen kívül** |
| gombok | Ignore Person · Cancel | **Személy mellőzése** · Mégse |

A felismert névtelen arcok albuma az első megnyitáskor egy „Welcome to the Unnamed people album!” tájékoztatót mutat. Ebből: „To ignore a person, click the 'X' button on the face thumbnail.”

*Bizonyítottsági fok: **megerősített**, élő méréssel és két ellenpróbával.* A bináris rész (az elosztó hívásai, a `0x005c9b00` összevetése és albumválasztása) utasításszinten olvasva.

#### c) A „Név hozzáadása" a jobb oldali fiókot nyitja

Az `faceheaderpanel/addname` kezelője (`0x00602970`, 147 b) két sztringet használ:
`rightdrawerpanel/peoplepanel` és a **`header_addname:%s`** parancs-token
⇒ a gomb az **Emberek panelt** nyitja meg, a nevet a tokenben átadva.

### 15.4 A feliratok — angol ÉS hivatalos magyar

| elem | típus | angol | **magyar** |
|---|---|---|---|
| `faceheaderpanel/confirmsug` | felirat | Confirm all | **Az összes jóváhagyása** |
| `faceheaderpanel/confirmsug` | súgó | Confirm all suggestions | **Az összes javaslat jóváhagyása** |
| `faceheaderpanel/confirmsel` | felirat | Confirm | **Jóváhagyás** |
| `faceheaderpanel/confirmsel` | súgó | Confirm selected suggestions | **Kijelölt javaslatok jóváhagyása** |
| `faceheaderpanel/removesel` | felirat | Remove | **Eltávolítás** |
| `faceheaderpanel/removesel` | súgó | Remove selected suggestions | **Kijelölt javaslatok törlése** |
| `faceheaderpanel/moresug` | felirat | Find more suggestions | **További javaslatok keresése** |
| `faceheaderpanel/sug_filter` | súgó | Show only suggestions (when toggled on) | **Csak a javaslatok megjelenítése (ha be van kapcsolva)** |
| `faceheaderpanel/sug_label` | szöveg | Suggestions: | **Javaslatok:** |
| `faceheaderpanel/face_zoom` | súgó | View zoomed in to the face | **Megjelenítés az arcra közelítve** |
| `faceheaderpanel/picture_zoom` | súgó | View zoomed out to the full picture | **Megjelenítés a teljes képre távolítva** |
| `faceheaderpanel/set_thumbnail` | súgó | Set as People Album Thumbnail | **Beállítás indexképként az Emberek albumban** |
| `faceheaderpanel/create_face_movie` | súgó | Create Face Movie | **Mozgófilm létrehozása arcokból** |
| `faceheaderpanel/create_movie` | súgó | Create Movie Presentation | **Mozgófilmes prezentáció létrehozása** |
| `faceheaderpanel/create_collage` | súgó | Create Photo Collage | **Fotókollázs készítése** |
| `faceheaderpanel/play` | súgó | Play Fullscreen Slideshow | **Diavetítés teljes képernyőn** |
| `faceheaderpanel/pwa_button` | súgó | Open PWA web page | **Picasa Webalbumok-beli weboldal megnyitása** |

Forrás — **sorszámmal, hogy a lefedettségi mérés is lássa**:
`faceheaderpaneltext.tre:44` (`faceheaderpanel/confirmsug` felirata),
`faceheaderpaneltext.tre:50` (`faceheaderpanel/removesel`),
`faceheaderpaneltext.tre:53` (`faceheaderpanel/moresug`),
`faceheaderpaneltext.tre:35` (`faceheaderpanel/sug_filter` súgója),
`faceheaderpaneltext.tre:68` (`faceheaderpanel/face_zoom`),
`faceheaderpaneltext.tre:74` (`faceheaderpanel/sug_label`);
a magyar alakok: `referencia/i18n-hu/faceheaderpaneltext.xml`.

**A munkafolyamat útmutató szövege** (`stringres-en-hu.tsv` 2072. sor):

| kulcs | angol | magyar |
|---|---|---|
| `PeopleAlbum::ConfirmText` | Press checkmark to confirm match, press "x" to ignore. | **Az egyezés megerősítéséhez kattintson a pipa, az elvetéshez pedig az "x" ikonra.** |

### 15.5 Geometria — `respack.yt`, a 532 × 90 vászonban

A `faceheaderpanel/docbounds` **532 × 90**; a `faceheaderpanel/headerbase` 532 × 86, alatta
egy 532 × 4 `faceheaderpanel/shadow`.

**Szerkezeti horgony** (a szülő-gyerek viszony, ahonnan a kényszerek jönnek):
`faceheaderpanel.tre:125` (`faceheaderpanel/face_zoom` a `zoom_container`-ben),
`faceheaderpanel.tre:136` (`faceheaderpanel/zoom_container`),
`faceheaderpanel.tre:169` (`faceheaderpanel/sug_filter`),
`faceheaderpanel.tre:181` (`faceheaderpanel/confirmsug`),
`faceheaderpanel.tre:190` (`faceheaderpanel/removesel`),
`faceheaderpanel.tre:194` (`faceheaderpanel/moresug`).

| elem | téglalap | méret |
|---|---|---|
| `faceheaderpanel/faceicon` (+ árnyék) | (12,8)–(71,79) | 59 × 71 |
| `faceheaderpanel/album_title` | (80,7)–(399,28) | 319 × 21 |
| `faceheaderpanel/album_title_clip` | (80,7)–(399,40) | 319 × 33 |
| `faceheaderpanel/zoom_container` | (457,4)–(527,25) | 70 × 21 |
| `faceheaderpanel/face_zoom` | (457,4)–(492,25) | **35 × 21** |
| `faceheaderpanel/picture_zoom` | (492,4)–(527,25) | **35 × 21** |
| `faceheaderpanel/zoom_label` | (189,25)–(527,38) | 338 × 13 |
| `faceheaderpanel/create_label` | (80,40)–(418,53) | 338 × 13 |
| `faceheaderpanel/sug_label` / `faceheaderpanel/sug_hottip` | (318,40)–(527,53) | 209 × 13 |
| `faceheaderpanel/selecthelp` | (357,41)–(527,54) | 170 × 13 |
| `faceheaderpanel/play` | (80,55)–(109,82) | 29 × 27 |
| `faceheaderpanel/dividers` | (111,61)–(112,78) | **1 × 17** |
| `faceheaderpanel/create_collage` | (115,55)–(144,82) | 29 × 27 |
| `faceheaderpanel/create_movie` | (147,55)–(176,82) | 29 × 27 |
| `faceheaderpanel/create_face_movie` | (179,55)–(208,82) | 29 × 27 |
| `faceheaderpanel/set_thumbnail` | (211,55)–(240,82) | 29 × 27 |
| `faceheaderpanel/pwa_button` | (243,55)–(272,82) | 29 × 27 |
| `faceheaderpanel/sug_filter` | (316,55)–(345,82) | 29 × 27 |
| **`faceheaderpanel/moresug`** | (348,55)–(527,82) | **179 × 27** |
| **`faceheaderpanel/confirmsug`** | (348,55)–(436,82) | **88 × 27** |
| **`faceheaderpanel/confirmsel`** | (348,55)–(436,82) | **88 × 27** |
| **`faceheaderpanel/removesel`** | (439,55)–(527,82) | **88 × 27** |

⇒ **A `faceheaderpanel/confirmsug` és a `faceheaderpanel/confirmsel` UGYANAZT a téglalapot foglalja el** —
váltakozó gomb: kijelölés nélkül „Az összes jóváhagyása", kijelöléssel
„Jóváhagyás". A `faceheaderpanel/moresug` a teljes maradék szélességet elfoglalja
(179 px), amikor nincs jóváhagyás-pár.

*(A `#`-előtagú rétegek — `#sug_filter_icon`, `#button: create_cd`,
`#button: select_star`, `#button: toggle_faces`, `#text(Select): select_label`,
`#button: sync_options`, `#text(xx photos edited): edit_count`,
`#button(save_edits): save_edits`, `#button(share): share`,
`#butlink(view_online): view_online`, `#superbutton(…selectsug): selectsug`,
`#text(Description): album_description`, `#title_fade0/1` — a
`picasa-respack-format.md` 2. pontja szerint **rétegtípus-jelölés**, nem
holt kód; a `#sug_filter_icon` teljes néven `faceheaderpanel/sug_filter_icon`
— a másik öt maradvány-név a `headerpanel.tre`-ből származik, nem ebből a
panelból.)*

### 15.6 Az „Ismeretlen emberek" TESTVÉRPANEL

Az `unknownfaceheaderpanel` ugyanabban a 532 × 90 vászonban él, de más a
gombkészlete. Szerkezeti horgony: `unknownfaceheaderpanel.tre:38`
(`unknownfaceheaderpanel/showignored`), `:43`
(`unknownfaceheaderpanel/showunknown`), `:53`
(`unknownfaceheaderpanel/ignore`), `:70`
(`unknownfaceheaderpanel/addname`), `:58`
(`unknownfaceheaderpanel/addname_instructions`).

| elem | téglalap | méret | szerep |
|---|---|---|---|
| `unknownfaceheaderpanel/showall` / `unknownfaceheaderpanel/cluster` | (278,14)–(398,41) | 120 × 27 | a `unknownfaceheaderpanel/clustering_container` váltógombjai |
| `unknownfaceheaderpanel/showunknown` / `unknownfaceheaderpanel/showignored` | (403,14)–(523,41) | 120 × 27 | a `unknownfaceheaderpanel/viewtype_container` váltógombjai |
| `unknownfaceheaderpanel/addname` | (235,60)–(398,80) | **163 × 20** | „Név hozzáadása" |
| `unknownfaceheaderpanel/ignore` | (403,56)–(523,83) | 120 × 27 | „Elvetés" |
| `unknownfaceheaderpanel/addname_instructions` | (52,42)–(523,55) | 471 × 13 | útmutató szöveg |
| `unknownfaceheaderpanel/info_text` | (12,57)–(297,78) | 285 × 21 | állapotszöveg |
| `unknownfaceheaderpanel/faceicon` | (11,12)–(47,48) | 36 × 36 | a kisebb arcikon |
| `unknownfaceheaderpanel/album_title` | (52,14)–(429,35) | 377 × 21 | — |

⇒ **Két váltógomb-pár egymás mellett**: a csoportosítás (`unknownfaceheaderpanel/showall` ↔
`unknownfaceheaderpanel/cluster`) és a nézet (`unknownfaceheaderpanel/showunknown` ↔ `unknownfaceheaderpanel/showignored`).

### 15.7 Eredeti / nálunk — MÉRVE

*Forrás: `faceheaderpanel.tre:185` (`faceheaderpanel/confirmsel`) · `faceheaderpanel.tre:181` (`faceheaderpanel/confirmsug`) · `faceheaderpanel.tre:125` (`faceheaderpanel/face_zoom`) — és további 4 elem ugyanott.*

| | eredeti | nálunk (mérve) |
|---|---|---|
| a fejlécsáv | **három** változat (`headerpanel`, `faceheaderpanel`, `unknownfaceheaderpanel`) | **egy**, általános: `LightboxHeader.qml` |
| gombok a fejlécen | 25 parancs (15.2) | **öt**: `headerPlayButton` (162), `headerSelectStarredButton` (177), `headerSaveEditsButton` (189), `headerCollageButton` (209), `headerUploadButton` (229) |
| javaslat-vezérlők | `faceheaderpanel/confirmsug`, `faceheaderpanel/confirmsel`, `faceheaderpanel/removesel`, `faceheaderpanel/moresug`, `faceheaderpanel/sug_filter`, `faceheaderpanel/selectsug`, `faceheaderpanel/addname`, `faceheaderpanel/ignore` | **hat megvan**: `confirmsug` és `confirmsel` ugyanazon a gombon váltakozva (`headerConfirmSuggestionsButton`; kijelölt javaslatnál a kijelöltekre), `removesel` (`headerRemoveSuggestionsButton`; kijelölt javaslatnál a kijelöltekre, különben mindre), `moresug` (`headerMoreSuggestionsButton`), `sug_filter` (`headerSuggestionFilterButton`), `selectsug` (`headerSelectSuggestionsButton`; a jelenlegi személy függő javaslatait tartalmazó képeket jelöli ki, #4588). **Nincs még:** `addname`, `ignore` |
| arc-nagyítás váltó | `faceheaderpanel/face_zoom` ↔ `faceheaderpanel/picture_zoom` | **megvan** (2026-09-26, #2187): `headerFaceZoomButton` ↔ `headerPictureZoomButton`, 2 × 35 × 21, a fejléc jobb felső sarkában; arc-módban a bélyegkép-URL `&fz=` keretet kap, és a szolgáltató négyzetesen, az arc kétszeresére vág (`app/arc_nagyitas_url.py`). ⚠️ Az eredeti ALAPÁLLÁSA nincs mérve — nálunk a teljes kép |
| a küszöb-lazítás | `FRSuggestionThreshold/100 − 0,1` | **megvan** — nálunk a LÉPCSŐ csökken tízzel (`FaceScanController.moreSuggestions`, #3237); a vezérlőt vettük át, nem a számot |

*(A `render/crop_suggest.py` a **vágási** javaslatoké — más funkció, nem
ez.)*

⇒ A javaslat-munkafolyamat felülete nálunk **teljesen hiányzik**, pedig az
adatréteg (`personalbumrecs`, `suggestionpersonalbumid` — 3.4/d) már
feltárva. Jegy: **#2187**.

*Bizonyítottsági fok: **megerősített*** — a parancskészlet az elosztó
`repe cmpsb` ágaiból, a küszöb-képlet három kiolvasott konstansból, a
tárolók a kezelők sztringjeiből, a geometria a `respack.yt`-ből, a magyar
feliratok az `i18n-hu`-ból.

---

## 16. A MOTOR KONFIGURÁCIÓJA: `plugins/red.cfg` — leltár és tulajdonosi döntés (#2239, 2026-09-04)

> **Tulajdonosi döntés (2026-09-04, a #2239-en):** *„A dokumentációban
> kerüljön rögzítésre a korábbi működés, és a majdani új, saját eljárás
> specifikáció készítésénél lehet figyelembe venni irányadónak. De ez ne
> kerüljön most is beépítésre."*
>
> ⇒ Ez a szakasz **tájékoztató, nem normatív**. A PicasaPy **nem olvassa**
> és nem is fogja olvasni ezt a fájlt; a leírás akkor lesz hasznos, amikor a
> saját arcfelismerőnk specifikációja készül.

### Mi ez a fájl

A `Picasa3/plugins/red.cfg` (**2,2 MB**) a `Red.dll` — az eredeti Picasa
arc- és vörösszem-motorjának — **betanított konfigurációja**: detektorok,
jellemzőkinyerők, modellek és küszöbök szerializált objektumfája.

⚠️ **A fájl a PARAMÉTEREKET tartalmazza, az ELJÁRÁST nem.** A felismerő
algoritmus a `Red.dll` kódjában van. Ezért a benne álló számok egy **másik**
eljárásban nem jelentik ugyanazt — ez a fő oka annak, hogy az átvétele nem
javasolt.

### A szerializálás formátuma — megfejtve

Minden objektum **hatbájtos fejléccel** kezdődik:

```
00  <len:1>  <ClassId: len bájt, little-endian>  00
```

A megfigyelt fájlban `len` mindig **3**. A fejléc után osztályfüggő
payload jön, a legtöbb osztálynál 4 bájtos verziószámmal indítva.

Négy tároló-osztály payloadja értelmezve:

| ClassId | osztály | payload |
|---|---|---|
| `0x15` | `ebs_ObjectList` | 4 bájt elemszám |
| `0x16` | `ebs_ObjectArr` | 4 bájt elemszám |
| `0x17` | `ebs_ObjectRef` | **1 bájt** hivatkozási index |
| `0x18` | `ebs_ObjectFRef` | 1 bájt |

A `ClassId → osztálynév → ősosztály` tábla a `Red.dll` regisztrációs
sorozatából olvasható ki (**550 osztály**).

### A leltár — mért számok

| | érték |
|---|---|
| objektum a fájlban | **19 525** |
| különböző osztály | **75** |
| `red.cfg` SHA-256 | `916d69fd…f51835` |

**Osztálycsaládok** (előtag szerint, objektumszámmal):

| előtag | objektum | osztály | mi ez |
|---|---:|---:|---|
| `ebs_` | 12 215 | 29 | alaptárolók (tömbök, hivatkozások, adathordozók) |
| `ets_` | 4 827 | 9 | mátrix/vektor típusok (`CompactVec`, `CompactMat`, `Float3DMat`…) |
| `vlf_` | 921 | 10 | **lokális jellemzők**: `AdvancedDetector`, `CompactRect/Quad/WaveFeature`, `AngleMap`, `PatchSize` |
| `vqc_` | 729 | 8 | **kvantálás és leképezés**: `Quantizer`, `L2NormVecMap`, `PrjVecMap`, `SubVecMap`, `Relator` |
| `egp_` | 561 | 2 | `SpatialGraph` + `SpatialNode` — térbeli gráf |
| `vfv_` | 242 | 2 | `AdvancedFvc`, `CueInfo` — jellemzővektor-készítés |
| `vde_` | 12 | 3 | `LocalPoseDetector`, `LocalDetectorSequence`, `LocalDetectorPrlArr` |
| `vfr_` | 7 | 6 | a **legfelső szint** (ld. lent) |
| `vrd_` | 6 | 5 | **vörösszem**: `RedEyeDetector`, `RedEyeCorrector`, `HistogramModel`, `GmmModel`, `Codebook` |
| `vpf_` | 5 | 1 | `EigenShapeMap` — alakmodell |

⭐ **Ebből az egyik legfontosabb megfigyelés:** a fájl **nem csak az
arcfelismerésé** — a `vrd_*` család a **vörösszem-javítás** detektorát és
korrektorát is tartalmazza, ugyanabban a konfigurációban.

### A legfelső szint — a feldolgozási lánc, fájlbeli sorrendben

| offszet | objektum | verzió |
|---|---|---|
| `0x7` | **`vfr_VdeFaceFinder`** — az arckereső belépési pontja | 201 |
| `0x21` | `vlf_AdvancedDetector` | 100 |
| `0x853ae` | **`vfr_VdeLandmarker`** — arcpont-kereső | 201 |
| `0x853ea` | `vde_LocalPoseDetector` + `vde_LocalDetectorSequence` | 100 |
| `0xabe46` | `vpf_EigenShapeMap` (összesen **5** példány) | 100 |
| `0xdefed` | **`vrd_RedEyeDetector`** + két `HistogramModel`, `GmmModel`, `Codebook` | 100 |
| `0xe0013` | **`vrd_RedEyeCorrector`** | 100 |
| `0x1734d3` | **`vfr_FeatureVectorCreatorArr`** — a jellemzővektor-készítők | 101 |
| `0x22b08a` | `vfr_SdkRelator` | 100 |
| `0x22d07e` | **`vfr_SowGrowStampClusterer`** — a „bélyeg"-klaszterező | 100 |
| `0x22d0a3` | `vfr_StdClusterRelator` | 100 |

### Az EGYETLEN kiolvasott paraméter-ötös

A `vfr_SowGrowStampClusterer` (`ClassId 0x401038`) payloadja a verzió után
**három float + két int**:

```
0,7   0,98   1,0   25 000 000   25 000 000
```

*(Kiolvasva a `0x22d07e` objektum törzséből; a mezők NEVE nincs megfejtve —
a két 25 milliós egész nagyságrendje memória- vagy elemkorlátra utal, de ezt
nem állítjuk.)*

### Amit NEM fejtettünk meg — és tudatosan nem is találgatunk

- a 75 osztályból **71** payload-sémája (a négy tároló-osztályon kívül);
- a modellobjektumok (súlyok, kaszkádok, kódkönyvek) belső szerkezete;
- a `SowGrowStampClusterer` öt paraméterének **jelentése**.

### A kutatási eszköz helye

A clean-room parser és a `ClassId`-tábla a **privát `picasapy-agent`
repóban** él (`eszkozok/redcfg/`), 17 egységteszttel és négypontos golden
kapuval. A termék-repóba nem kerül: nem termékkód.

*Bizonyítottsági fok: **megerősített** a formátumra, a leltár számaira, az
osztálycsaládokra, a lánc sorrendjére és a paraméter-ötös értékeire
(kiolvasva, golden kapuval rögzítve); **nem megfejtett** a payload-sémák
többsége és a paraméterek jelentése.*


## 14.4 Az `albumpeoplechecksum` ÍRÓJA — a keresési tér a teljes binárisról EGY függvényre szűkült (2026-09-05)

> **Bizalmi fok: megerősített** az oszlop memóriabeli helyére, a hat érintő
> helyre és az írás pontos utasítására; **a KÉPLET továbbra sincs meg.**

A 14.2 azt írta, hogy a folytatáshoz „az oszlop indexét a `0x004127c0` /
`0x00415790` regisztrációk sorrendjéből kell kiszámolni". A regisztrációt
elolvasva kiderült, hogy **nincs szükség indexre**: az oszlopok
**tagobjektumok fix eltolásokon**, tehát elég az eltolásra pásztázni.

### 14.4.1 Az oszlop memóriabeli helye

A `CThumbDB` konstruktora (`FUN_00415790`) **33 nevet** regisztrál, ebből az
`albumdata` tábláé sorrendben: `token · name · filename · date · category ·
unread · description · location · uid · hascollage · inisync · … ·
albumcontactids · albumpeoplechecksum`.

| oszlop | regisztráció | névhossz | a tagobjektum eltolása |
|---|---|---:|---|
| `albumcontactids` | `0x00415bbc` | `0x0f` = 15 ✓ | **`CThumbDB + 0x2748`** |
| **`albumpeoplechecksum`** | **`0x00415bcc`** | `0x13` = 19 ✓ | **`CThumbDB + 0x27b0`** |

*(A névhossz a `mov eax, <len>` közvetlen értékéből jön, és bájtra egyezik a
sztring hosszával — ez hitelesíti a párosítást.)*

### 14.4.2 ⛔ KIMERÍTŐ: hat hely nyúl az oszlophoz, EGY írja

A teljes `.text` pásztázása a `+0x27b0` eltolásra:

| cím | függvény | mit csinál |
|---|---|---|
| `0x00415be8` | `FUN_00415790` | a konstruktor — létrehozza |
| `0x00417fd5` | `FUN_00417770` (2624 b) | ua. tömbben a `+0x2748`-cal — életciklus |
| `0x0048be5d` | `FUN_0048bd80` (888 b) | egy érintés |
| `0x0048c18c` | `FUN_0048c100` (817 b) | egy érintés |
| **`0x0048f545`** | **`FUN_0048ef20` (5143 b)** | **OLVASÁS** — összeveti a tárolt értéket |
| **`0x0048f79d`** | **ua.** | **ÍRÁS** |

Összevetésül: az `albumcontactids` (`+0x2748`) **15** helyen, **12**
függvényben szerepel — a checksum-oszlop tehát nagyságrenddel szűkebb.

### 14.4.3 Az írás pontos utasításai

```
0x0048f79d  add ebx, 0x27b0          ; az oszlopobjektum
0x0048f7a3  call [0xc40284]          ; GetCurrentThreadId — a szokásos zár
…
0x0048f7f5  lea eax, [ebx + 0x5c]    ; a cella (vagy a tömbelem, 0x0048f7f0)
0x0048f7f8  mov ecx, [esp + 0x30]    ; ← AZ ÚJ ÉRTÉK
0x0048f7fc  cmp [eax], ecx
0x0048f7fe  je  0x0048f9ec           ; ha VÁLTOZATLAN → nem ír, nem piszkít
```

⇒ A checksum **csak akkor íródik, ha megváltozott** — összhangban azzal,
hogy származtatott, gyorsítótár-jellegű adat (14.2).

A `FUN_0048ef20` a `0x0048f68b`-en meghívja a `FUN_0048af60`-at (2188 b),
amelynek visszatérési kódját a `0` és a `0xf4242` ellen vizsgálja
(`0x0048f690`, `0x0048f694`) — ez a legvalószínűbb helye a tényleges
számításnak.

### 14.4.4 A KONKRÉT következő lépés (a 14.2-é helyett)

1. `FUN_0048ef20` (5143 b) — honnan kapja az `[esp+0x30]`-at a `0x0048f7f8`
   előtt. A függvény nagy, de a kérdés egyetlen veremrekeszre szűkült.
2. `FUN_0048af60` (2188 b) — a jelölt számoló; a `0xf4242` és a `0xf4241`
   (`0x0048f660`) állapotkódok is innen jönnek.
3. Ellenőrzés a meglévő adaton: a 14.2 kilenc albumának értéke a
   `research/testdata/Picasa2-arcok/` adatbázisban megvan, tehát a képlet
   **azonnal ellenőrizhető**, ha megvan.

⚠️ Ez **nem** dekompilációt igényel, csak a két függvény célzott olvasását.

### 14.4.5 Jegy

**#2391** — `ready` · `bináris-kutatható` · `P4` (a PicasaPy nem ír PMP-t, tehát ez tudásbeli hiány, nem megvalósítási akadály).

### 14.4.6 Mérleg (14.4)

`1 nyílt (ÖRÖKÖLT: a képlet) · 3 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| hol él az oszlop a memóriában | **LEZÁRVA** — `CThumbDB + 0x27b0` (14.4.1) |
| ki írja | **LEZÁRVA** — egyetlen hely: `0x0048f79d` a `FUN_0048ef20`-ban (14.4.2) |
| mikor ír | **LEZÁRVA** — csak változás esetén (`0x0048f7fe`) |
| **mi a KÉPLET** | **NYÍLT (örökölt, 2026-08-22 óta)** — de a keresési tér a teljes binárisról két függvényre szűkült (14.4.4) |

## 14.5 Az `albumpeoplechecksum` — KÉT jelölt kiesett, és megvan, HOL áll meg az olcsó ág (2026-09-05, #2391)

> **Bizalmi fok: megerősített** a két kizárásra és a megállási pont okára;
> **a képlet továbbra sincs meg.**

A 14.4 két jelöltet nevezett meg a számításra. **Mindkettő kiesett.**

### 14.5.1 ⛔ `FUN_0048af60` NEM a számoló — sztring/vektor-másoló

| megfigyelés | cím |
|---|---|
| **egyetlen** hívója van (`0x0048f68b`), tehát nem általános segéd | kimerítő `e8`-pásztázás |
| a törzse először a **`FUN_00448fb0`**-at hívja | `0x0048af7a` |
| a `FUN_00448fb0` a **generikus oszlopolvasó** (21 hívó), és az `albumcontactids` oszlopot (`+0x2748`) éri el | `0x00448fbc` |
| ha a kiolvasott 64 bites érték **nulla**, `9`-cel tér vissza | `0x0048af83`–`0x0048af98` |
| a maradék törzs **csomagolt hosszú sztring/vektor másolása** (`shr len,1`, `and [edi+4],1`, felszabadítás `0x0097caf0`-val) | `0x0048afa2`–`0x0048b113` |

⇒ Ez a függvény **beolvassa az album `albumcontactids` értékét és átmásolja**
— nem számol ellenőrzőösszeget.

### 14.5.2 ⛔ `FUN_0048bd80` NEM a számoló — felszabadító/átméretező ág

A `0x0048be5d` előtti utasítások a **vektort ürítik** (`0x0048be4a`
felszabadítás, `0x0048be52` a csomagolt hossz nullázása, `0x0048be56`
`[ebx+0x48] = 0`), és csak utána zárolja az oszlopot. Számítás nincs benne.

### 14.5.3 ⛔ ITT áll meg az olcsó ág — és pontosan miért

Az írás a `0x0048f7f8`-on lévő **veremrekeszből** veszi az értéket. A
`FUN_0048ef20` teljes törzsében a **nyers `[esp + 0x30]` alakra**
mindössze hét hivatkozás van:

| cím | mi |
|---|---|
| `0x0048f5b8`, `0x0048f7f8`, `0x0048f9b6` | **olvasás** (a checksum-ág) |
| `0x004900c9`, `0x00490281` | **írás** — de egy **16 bites tömbön** futó ciklusban (`0x0049026e`: `mov word ptr [edx+ecx*2], ax`), és a `0x00490272`/`0x0049027a`/`0x0049027f` szerint **ciklusszámláló**, nem checksum |
| `0x004900dc`, `0x00490272` | ua. ciklus olvasásai |

⇒ **A checksum-ág olvasásaihoz tartozó ÍRÁS nincs ugyanezen a nyers
eltoláson** — vagyis a két hely **eltérő `esp`-állapotban** van (élő
hívás-argumentum push-ok miatt). A veremrekesz azonosításához
**bázisblokkonkénti `esp`-követés** kell; a lineáris követés egy 5 143
bájtos, elágazásokkal teli törzsön nem megbízható.

> **Ez az a pont, ahol a drága ág (célzott dekompiláció) INDOKOLT** — és
> most **pontos kérdéssel**: *mi tölti fel a `0x0048f7f8`-on olvasott
> lokális rekeszt?* A dekompilátor a veremrekeszeket nevesíti, tehát ez neki
> egyetlen ránézés.

### 14.5.4 A contactid-hipotézis MÁSODSZOR is megdőlt — független adaton

A 14.2 kizárta, hogy a checksum az `albumcontactids`-ből képződne (alsó 32,
felső 32, XOR). Most a két oszlop **egymás mellé mérve**
(`research/testdata/Picasa2-arcok/Picasa2/db3/`, saját `pmpimport`
olvasónkkal, `albumcontactids` mezőtípus `0x4` = `uint64`,
`albumpeoplechecksum` `0x1` = `uint32`):

| album | tagok | `albumpeoplechecksum` |
|---:|---:|---|
| 109 | 32 | `0x8DAB10B8` |
| 110 | 42 | `0xDC7A570C` |
| 111 | 19 | `0x5CCEB284` |
| **112** | **1** | **`0x00000000`** |
| 113 | 2 | `0x00060B93` |
| 114 | 4 | `0x030331FE` |
| 115 | 7 | `0x98B4584D` |
| 116 | 2 | `0x00063CE2` |
| 117 | 6 | `0x9204CA91` |

A **112-es albumnak van** `albumcontactids` értéke (nem nulla, egyedi), a
checksumja mégis **0** ⇒ a checksum **nem függvénye a contactidnek**.
Ez a 14.2 kizárásának **független megerősítése**, más úton.

*(Adatvédelem: a contactid-értékek személyazonosítók, ezért nem kerülnek ki
erre a lapra — csak az album-index és a checksum.)*

### 14.5.5 ⚠️ CSAPDA a következő körnek: az „1 tag → 0" NEM törvény

Kézenfekvő a „egy tagnál nulla ⇒ a képlet párokból/különbségekből épül"
olvasat. **Ne építs rá.** Ugyanilyen jól magyarázza az adatot, hogy az
oszlop **még nincs kiszámolva** ezen az albumon: a 14.4.3 szerint az író
**csak változás esetén** ír (`0x0048f7fe`), tehát a `0` jelentheti azt is,
hogy „még sosem írták".

**A két olvasat közt az adat nem dönt** — ezért egyik sem használható
kiindulásnak. Aki a képletet illeszti, **hagyja ki a 112-es albumot**, vagy
mondja ki, melyik olvasattal dolgozik.

### 14.5.6 Mérleg (14.5)

`1 nyílt (ÖRÖKÖLT: a képlet) · 2 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| a `FUN_0048af60` a számoló-e | **LEZÁRVA — nem** (14.5.1) |
| a `FUN_0048bd80` a számoló-e | **LEZÁRVA — nem** (14.5.2) |
| **mi a KÉPLET** | **NYÍLT (örökölt)** — a következő lépés a `FUN_0048ef20` **célzott dekompilációja** azzal az egy kérdéssel, hogy mi tölti a `0x0048f7f8`-on olvasott rekeszt (14.5.3). Jegy: **#2391** |

## 14.6 ⭐ MEGVAN az `albumpeoplechecksum` KÉPLETE — és 9-ből 8 albumon MÉRVE egyezik (2026-09-05, #2391)

> **Bizalmi fok: megerősített.** A képlet a binárisból olvasva, és a
> tulajdonos valódi katalógusán **kilenc albumból nyolcon bitre egyezik**;
> a kilencedik eltérése megmagyarázva (lásd 14.6.4).

### 14.6.1 A képlet

```
acc = 0
minden i képindexre, NÖVEKVŐ sorrendben:
    ha  personalbumid[i] == <az album sorindexe>
    és  ( i >= len(facequality)  vagy  facequality[i] >= 5000 ):
            acc = rol(acc, 7) XOR i
albumpeoplechecksum = acc
```

A **hajtogatott érték maga a KÉPINDEX** — nem a `contactid`, nem a
személy azonosítója. Ez zárja le véglegesen a 14.2 és a 14.5 két
független kizárását.

### 14.6.2 A bizonyíték a binárisban

A számoló **`FUN_0048ec70`** (668 bájt, `ret 0x14` ⇒ öt verem-argumentum),
amelyet a `FUN_0048ef20` hív a `0x0048f1bf`-en. Az eredmény a **3.
argumentum**, kimenő mutatóként.

| lépés | cím | mit tesz |
|---|---|---|
| a kimenő rekesz nullázása | `0x0048ece3`–`0x0048ecea` | `mov dword ptr [edx], 0`, ahol `edx` = ARG3 |
| **1. szűrő** | `0x0048ed6e` | `cmp dword ptr [ebx + eax*4], ebp` — `ARG4[i] == ARG2` |
| tartomány-őr az 1. szűrőhöz | `0x0048ed61` | `i >= ARG4.méret` ⇒ kihagy |
| **2. szűrő (küszöb)** | `0x0048ed85` | `cmp dword ptr [ebx + eax*4], 0x1388` ⇒ **5000** |
| a 2. szűrő tartomány-őre | `0x0048ed7f` | ha `i >= ARG5.méret`, a küszöböt **át is ugorja** (nem szűr) |
| **a hajtogatás** | `0x0048ed95`–`0x0048eda6` | `mov ecx,[esp+0xec]` (ARG3) · `mov ebx,[ecx]` · **`rol ebx, 7`** · **`xor ebx, eax`** · `mov [ecx], ebx` |
| üres bemenetre | `0x0048ecc6`–`0x0048ece0` | `return 9` (a `0` marad) |

Az argumentumok azonosítása a `research/testdata/Picasa2-arcok` valódi
katalógusán ellenőrizve: **ARG2** = az album sorindexe, **ARG4** =
`imagedata_personalbumid`, **ARG5** = `imagedata_facequality`.

### 14.6.3 ⛳ Hogyan került elő — HORGONYOS veremszámolás, dekompiláció NÉLKÜL

A 114. kör azért állt meg, mert a `0x0048f7f8` rekeszének íróját **lineáris
`esp`-követéssel** kereste, és az elágazásos törzsön nulla írást adott.
A megoldás a **horgony**: a `[esp+0x150]` **ARG1-hivatkozás** tizenkét
helyen áll, mindenütt azonos szinten (`esp` = belépés − `0x14c`), és ez
kalibrálja az egész régiót. Ezzel a `0x0048f195`–`0x0048f1bf` blokk
push-onként visszaszámolható:

| cím | utasítás | szint | keret-eltolás |
|---|---|---|---|
| `0x0048f19f` | `lea edx, [esp + 0x38]` | `0x154` | **`0x30`** ⇒ **`&local_0x30`**, az ARG3 |
| `0x0048f1a5` | `mov [esp + 0x38], eax` | `0x15c` | `0x28` (a `0x0048f828`-on olvasott rekesz) |
| `0x0048f1ae` | `mov byte [esp + 0x33], 1` | `0x160` | `0x1f` (a `0x0048f5c0`-on törölt jelző) |
| `0x0048f1b3` | `mov [esp + 0x44], ebp` | `0x160` | `0x30` ⇒ a rekesz **nullázása** a hívás előtt |

A három egymástól független egyezés (`0x30`, `0x1f`, `0x28`) igazolja a
kalibrációt. **Célzott dekompilációra nem volt szükség.**

### 14.6.4 A MÉRÉS — a tulajdonos valódi katalógusán

Bemenet: `research/testdata/Picasa2-arcok/Picasa2/db3/`, a saját
`pmpimport` olvasónkkal. `personalbumid` és `facequality` egyaránt **3338**
soros; a személy-albumok sorindexe **109–117**.

| album | tagok | mért `albumpeoplechecksum` | a képlet (küszöbbel) | a képlet küszöb NÉLKÜL |
|---:|---:|---|---|---|
| 109 | 32 | `0x8DAB10B8` | **`0x8DAB10B8`** ✔ | `0xF822B336` |
| 110 | 42 | `0xDC7A570C` | **`0xDC7A570C`** ✔ | `0xDC7A570C` |
| 111 | 19 | `0x5CCEB284` | **`0x5CCEB284`** ✔ | `0x9DB5534B` |
| 112 | 1 | `0x00000000` | **`0x00000000`** ✔ | `0x00000C0D` |
| 113 | 2 | `0x00060B93` | **`0x00060B93`** ✔ | `0x00060B93` |
| 114 | 4 | `0x030331FE` | **`0x030331FE`** ✔ | `0x8198F380` |
| 115 | 7 | `0x98B4584D` | `0x98B7DFCC` ✘ | `0x98B7DFCC` |
| 116 | 2 | `0x00063CE2` | **`0x00063CE2`** ✔ | `0x00063CE2` |
| 117 | 6 | `0x9204CA91` | **`0x9204CA91`** ✔ | `0xE204AE41` |

**8 / 9 bitre egyezik.** A küszöb **nem elhagyható**: nélküle csak 3 album
egyezne.

**A 115-ös albumról, őszintén:** a mai hét képindexének **egyetlen
részhalmaza sem** adja a tárolt értéket (mind a 127 részhalmaz kipróbálva),
és egy elem elhagyása/hozzávétele, más küszöb, fordított sorrend és ±1
index-eltolás sem. ⇒ a tárolt érték **egy másik indexkészleten** készült,
tehát **elavult** (az író csak változáskor ír, `0x0048f7fe`; a sorindexek
pedig eltolódnak, ha a katalógusból sor törlődik). Ez **magyarázat, nem
mérés** — bizalmi fok: **erős**, nem megerősített.

### 14.6.5 ✅ A „1 tag → 0" CSAPDA FELOLDVA

A 14.5.5 figyelmeztetett, hogy a 112-es album `0`-ja jelentheti azt is,
hogy az oszlopot sosem írták. **Nem ez a helyzet.** A 112-es albumnak
egyetlen képe van (index **3085**), és annak `facequality` értéke **38** —
mélyen az **5000**-es küszöb alatt ⇒ a hajtogatás **üres**, az eredmény
**0**. A `0` tehát **kiszámolt, helyes érték**.

A kilenc albumban összesen **tíz** kép esik a küszöb alá (`facequality`
38 · 47 · 60 · 81 · 90 · 92 · 100 · 111 · 117 · 1716 · 3405), és épp ezek
kihagyása teszi a képletet egyezővé.

### 14.6.6 Nálunk (MÉRVE)

`grep -rn "albumpeoplechecksum\|peoplealbumchecksum" src/` → **0 találat**:
az oszlopot **nem olvassuk és nem számoljuk**. A PicasaPy nem ír PMP-t,
ezért ez **nem hiány** — a képlet értéke az, hogy egy importált katalógus
arc-adatai **ellenőrizhetővé** válnak. Jegy: **#2391** (lezárva).

### 14.6.7 Nyitott kérdések mérlege (14.6)

`0 nyílt · 3 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| **az `albumpeoplechecksum` képlete** | ✅ **LEZÁRVA** — `acc = rol(acc,7) ^ képindex`, két szűrővel; 8/9 albumon mérve |
| a „1 tag → 0" jelentése | ✅ **LEZÁRVA** — a küszöb alatti minőség miatt üres a hajtogatás (14.6.5) |
| a 115-ös album eltérése | ✅ **LEZÁRVA** — elavult tárolt érték; minden más magyarázat kipróbálva és kizárva (14.6.4) |

## 17. ⛳ ÖNHELYESBÍTÉS + a `0xa0cd` LEZÁRVA: nem parancs, hanem ALMENÜ-HORGONY (2026-09-11, 290. kör, #26)

A kör a **saját lapunk felmérésével** kezdett, és a lap **önmagával
ellentmondott**. Ez a szakasz feloldja, és lezárja az utolsó valóban nyitott
tételt is.

### 17.1 Három elavult hely — feloldva

| hol | mit állított | miért elavult |
|---|---|---|
| a `albumdata_albumpeoplechecksum` szakasz címe | „ez VALÓDI hash, és **NINCS megfejtve**" | a **14.6** (2026-09-05) megfejtette: `acc = rol(acc,7) XOR képindex`, 8/9 albumon bitre |
| ugyanott a bizonyítottsági sor | „a képzési szabálya **nyitva marad**" | ua. |
| a **12.** mérleg 3. tétele | „a két `*checksum` **továbbra is BLOKKOLT**", jegy **#1238** | a `peoplealbumchecksum` a 2026-08-24-i szakaszban (**konstans arc-jelző**, nem checksum), az `albumpeoplechecksum` a 14.6-ban lezárult; a **#1238 jegy pedig ZÁRVA** (`wontfix`, 2026-09-06) |

⇒ A 12. szakasz mérlege ezzel **`0 nyílt · 11 lezárva · 0 blokkolt ·
1 hatókörön kívül · 0 csak-nyitva`** (a 8. tételt ld. lent).

### 17.2 A `0xa0cd` („Hozzáadás az Emberek albumhoz") — LEZÁRVA

A 12. szakasz 8. tétele ezt írta: *„nincs saját ága a szétosztóban, az
alapértelmezett ágra fut, amiben egyetlen sztring sincs; **futásidőben
töltött almenü gyanúja**"*. A gyanú most **bizonyítás**.

**Kimerítő pásztázás a teljes `.text`-en** (`eszkozok/binaris/paszta.py`):
a `0xa0cd` **13** találatából **11 cím-egybeesés** (a `0x00a0cdXX`
utasításcímek és egy adatcím), tehát **pontosan KÉT** valódi előfordulás van:

| cím | utasítás | mi ez |
|---|---|---|
| `0x007356ee` | `mov word ptr [0xd6f8c2], 0xa0cd` | a **menürekord** azonosító-mezője |
| `0x0056d12d` | `push 0xa0cd` | az egyetlen kódbeli használat |

*Kontroll-pozitív:* a `0x9e11` („Arcok alaphelyzetbe") **25** előfordulást ad
ugyanezekkel az alakokkal (menürekord + szétosztó-push) ⇒ a minta nem vak.

**Mit csinál a `0x0056d12d` körüli blokk:**

```
0x0056d11a  call [0x00c408f0]        ; CreatePopupMenu  -> eax = ÚJ, ÜRES almenü
0x0056d137  mov [esp+0xa8], 0x30     ; MENUITEMINFO.cbSize = 48
0x0056d142  mov [esp+0xac], 4        ; MENUITEMINFO.fMask = MIIM_SUBMENU
0x0056d14d  mov [esp+0xbc], eax      ; MENUITEMINFO.hSubMenu = a fenti popup
0x0056d129  push ecx                 ; &MENUITEMINFO   (esp+0x98 … a struktúra)
0x0056d12c  push ebx (= 0)           ; fByPosition = FALSE  -> AZONOSÍTÓ szerint
0x0056d12d  push 0xa0cd              ; uItem
0x0056d132  push edx                 ; hMenu
0x0056d159  call [0x00d69584]        ; SetMenuItemInfo alakja
```

A `cbSize = 0x30` (48 = `sizeof(MENUITEMINFO)`), az `fMask = 4`
(`MIIM_SUBMENU`) és a `+0x14`-es `hSubMenu` mező együtt egyértelmű.

⇒ **A `0xa0cd` NEM parancs, hanem ALMENÜ-HORGONY.** A program futás közben
készít hozzá egy üres felugró menüt, és azt akasztja rá. Ezért **nincs saját
ága a szétosztóban**, és ezért üres az alapértelmezett ág: a tényleges
parancs az almenü **futásidőben betöltött** tételeiből jön (a személy-albumok
listája).

⚠️ **A hívott függvény NEVE olvasat, nem kiolvasott érték:** a `0x00d69584`
nem az importtáblában áll, hanem futásidőben feloldott mutató (a `user32`
közvetlen importjai közt `SetMenuItemInfo` nincs — `CreatePopupMenu`,
`CreateMenu`, `GetMenuItemInfoA`, `RemoveMenu`, `TrackPopupMenu(Ex)`,
`SetMenuInfo`, `SetMenuDefaultItem` viszont igen). Az **argumentum-alak**
viszont önmagában bizonyító erejű.

### 17.3 Mit jelent ez a #26-nak

A menütétel átvételekor **ne keress hozzá kezelőt** — nincs és nem is lesz.
A tétel egy **dinamikus lista** gazdája: a személy-albumokat kell alá
építeni, és a parancs onnan jön. Ez felületi (QML-)feladat, nem bináris
kérdés ⇒ a #26 bináris blokkolója **elfogyott**.

*Forrás: `0x0056d0fa`–`0x0056d159` (a blokk), `0x007356ee` (a menürekord),
`0x00c408f0` = `CreatePopupMenu`, `0x00d69584` (futásidejű mutató);
a pásztázás `eszkozok/binaris/paszta.py`, kontroll `0x9e11` = 25 találat.*

### 17.4 Nyitott kérdések mérlege (17.)

`0 nyílt · 4 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 „csak nyitva"`

| kérdés | állapot |
|---|---|
| a `albumpeoplechecksum` szakasz elavultsága | ✅ LEZÁRVA — feloldva (17.1) |
| a 12. mérleg „2 blokkolt checksum" tétele | ✅ LEZÁRVA — mindkettő megfejtve, a jegy zárva (17.1) |
| a `0xa0cd` tényleges kezelője | ✅ LEZÁRVA — **nincs**: almenü-horgony (17.2) |
| a #26 bináris blokkolója | ✅ LEZÁRVA — elfogyott; ami maradt, az felületi munka (17.3) |

## 18. ⛳ A javaslat JÓVÁHAGYÁSA: egy kezelő, egy logikai kapcsoló — és az adatbázisba ír (2026-09-15, 312. kör, #3177)

*A 15. szakasz a fejlécsáv parancskészletét adta, és az ELVETÉS tárolóját
(`.picasa.ini`, `]ignoreface`). A JÓVÁHAGYÁS tárolója sehol nem volt kimondva.
Ez a szakasz azt méri ki — és közben helyesbíti a 15. szakasz egy sorát.*

### 18.1 ⛔ ÖNHELYESBÍTÉS: a `confirmsel` NEM a törlés-kezelőhöz megy

A 15. szakasz táblája a `confirmsel`-t a `0x005c9b00` kezelőhöz rendelte, az
`ignore` és a `removesel` mellé. **Ez téves.** Az elosztóban a két megerősítő
parancs ugyanarra a kezelőre megy, egyetlen logikai argumentumban különböznek:

```
0x005e15bf  "confirmsug" névösszevetés  ->  0x005e15eb  push 1
0x005e160f  "confirmsel" névösszevetés  ->  0x005e163b  push 0
0x005e15ed  mov edi, [esp+0x18]
0x005e15f1  call 0x00602640              ; MINDKETTŐ ide
```

A `0x00602640` első elágazása épp ezt a kapcsolót olvassa
(`0x00602676 cmp byte [esp+0x24], 0`): igaz ágon az ÖSSZES javaslatot szedi
össze (`0x00891110` / `0x007164b0`), hamis ágon a KIJELÖLTEKET
(`0x007166c0`, `push 1`).

⇒ **„Az összes jóváhagyása" és a „Jóváhagyás" ugyanaz a művelet, két
hatókörrel** — ez egybevág a 15. szakasz geometriai leletével (a két gomb
ugyanazt a 88 × 27-es téglalapot foglalja el).

A `0x005c9b00` ezzel szemben a **törlés/eltávolítás** kezelője: a sztringjei
`Deleting Files`, `CThumbUI::DeleteProgress`, `.picasaoriginals`, `.mxf`,
`.cxf`, `.thm` a `]ignoreface` / `]unknownface` / `]search` mellett. Az
`ignore` és a `removesel` tehát helyesen kerül oda, a `confirmsel` nem.

*Forrás: `0x005e15bf`, `0x005e160f`, `0x005e15f1`, `0x00602676`; a
`0x005c9b00` sztringjei a függvény törzsében álló `.rdata`-mutatókból
(`0x005ca2ce`, `0x005ca368`, `0x005ca3b9`, `0x005ca59a`, `0x005ca6f2`,
`0x005ca869`).*

### 18.2 A jóváhagyás útja a tárolóig

```
0x00602640  confirmsug/confirmsel
  0x006026ba  ebx = [album+0x3c0]            ; az album azonosítója
  0x006026c0  eax = [panel+0x2bc]            ; az adatbázis-objektum
  0x006026d0  call 0x0044a930(db, &lista, albumid, &lista)
  0x0060272d  call 0x005c6500 -> 0x0047bf40 -> 0x0047baf0   ; újrakeresés
  0x00602786  call 0x004abc70([panel+0x2c0], …)             ; nézet-frissítés
  0x00602791  mov byte [[panel+0x2c0]+0x166], 1             ; piszkos-jelző
```

A `0x0044a930` **oszlop-beállító**: az objektum `[+0x48]` tömbjébe ír indexelve,
és minden írás után meghívja a `0x006a2a60` piszkos-jelzőt
(`0x0044acb4`+`0x0044acc6`, `0x0044aec3`+`0x0044aed1`, `0x0044b0fc`+`0x0044b10b`).
Ugyanez a függvény végigmegy a tétellistán, és fájlonként meghívja a
**`0x00484820`**-at:

```
0x0044b316  eax = lista[esi]
0x0044b31d  push 0 / push 1 / push eax / push ecx
0x0044b323  call 0x00484820
```

A `0x00484820` az arcadat-kiíró: a
`Preferences\FRWriteFaceDataINI` kulcsot olvassa (`0x00484dcf` a kulcsnév,
`0x00484de7` az **alapérték 0**). A `faces=` (`0x0048516d`) mindig kiíródik;
a kapcsoló csak a `facedata` (`0x004851ab`) kulcsot kapuzza. A writer
`backuphash`-t is ír (`0x0048521d`; a kapu helyesbítése: 9/f).

⇒ **A jóváhagyás elsődlegesen az adatbázisba ír** (oszlop-tömb + piszkos-jelző),
és a `.picasa.ini`-be is írhat `faces=` adatot; a `facedata` alapból kimarad.
Mellőzéskor a `.picasa.ini` `faces=` személymezője
`ffffffffffffffff`; a `]ignoreface` állapotot a `CThumbDB` különleges
albumtagsága jelzi, nem az ini-be írt token (15.3/b.1).

**Termékre:** önmagában az, hogy jóváhagyáskor `faces=` kerül a
`.picasa.ini`-be, nem eltérés az eredetitől; a `0x00484820` ezt a kulcsot is
kiírja. Az eltérést a konkrét érték és a `facedata` viselkedése alapján kell
megnevezni.

### 18.3 Melléklelet: a PMP-oszlopok NEVE → TAGELTOLÁS, mind a 44

A `0x004127c0` regisztráló minden oszlopnevet egy fix tagváltozóhoz köt
(`push <név>` … `lea eax, [esi + eltolás]` … `call <regisztráló>`). A
személy-albumhoz tartozó rész:

| oszlopnév | tageltolás |
|---|---|
| `personalbumid` | `esi+0xca0` |
| `suggestionpersonalbumid` | `esi+0xd00` |
| `facequality` | `esi+0xd60` |
| `facerect` | `esi+0xdc0` |
| `deferredface` | `esi+0xe28` |
| `deferredregion` | `esi+0xe88` |
| `facerectdata` | `esi+0xee8` |
| `personalbumrecs` | `esi+0xf48` |
| `personalbumrecvalues` | `esi+0xfa8` |
| `personalbumrecs2` | `esi+0x1008` |
| `personalbumrecvalues2` | `esi+0x1068` |
| `peoplealbumchecksum` | `esi+0x10c8` |
| `tagdate` | `esi+0x1128` |
| `fdbhash` | `esi+0x1190` |
| `backuphash` | `esi+0x11f0` |

**Határ-kontroll:** a regisztráló az utolsó oszlop után a `[esi+0x1250]`-be ír
(`0x00412f19`), és visszatér — tehát a tábla a `0x11f0`-es `backuphash`-sel
zárul, összesen **44** `lea esi+…` regisztrációval.

*Forrás: `0x004127c0` (1893 b), a párok a `push <sztringcím>` → következő
`lea eax, [esi + N]` mintából.*

### 18.4 Ami NYITVA marad

**Melyik oszlopot írja pontosan a jóváhagyás.** A `0x0044a930` a
`0x1bc0` / `0x1c18` / `0x2048` / `0x20a0` eltolású tagokon dolgozik, azok
viszont a fenti táblán KÍVÜL esnek (a tábla `0x11f0`-nél véget ér) ⇒ a
`0x0044a930` egy MÁSIK, nagyobb objektumot kezel, nem közvetlenül ezt a
sorosztályt. A megszerzés útja: a `[panel+0x2bc]` objektum osztályának RTTI-je,
majd a `0x1bc0`–`0x20a0` tartomány tagjainak regisztrálója — ugyanazzal a
`push <név>` → `lea` mintával, amely a 18.3-at adta.

### 18.5 Nyitott kérdések mérlege (18.)

`1 nyílt · 2 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 „csak nyitva”`
(nyílt: a 18.4; lezárva: a jóváhagyás kezelője és a tárolójának fajtája.)

## 19. #5185, második kör: élő felvétel a Név nélküliek csempe-mezőjéről

**Hatókör:** a jegy Név nélküliek-albumra kattintási és névadási útja, a már
létező job-64 és job-66 eredményekkel együtt. A táblázat az eredeti Picasa
3.9-et a felvételekből írja le; a „Nálunk” oszlop a v0.9.118-as forráskódot
rögzíti; ahol a cella a #5182 (0.9.123) vagy a #5214 (0.9.124) utáni állapotot
nevez meg, ezt jelzi. A felvételre hivatkozó állításoknál a job- és képkocka-
azonosító közvetlenül jelzi a bizonyítékot.

**Források:** a korábban feldolgozott bináris- és `.tre`-eredmények, valamint
a `picasa-colab-jobs` job-64, job-66, job-162, job-163, job-167, job-175,
job-177, job-179, job-180 és job-183 leírásai; a job-180 és job-183
képernyőképeit közvetlenül megnéztük.
A job-66 a Név nélküliek csempe-mezőjének útja: nem külön névadási felület.

| Téma | Eredeti | Nálunk | Teendő, kész ha |
|---|---|---|---|
| Bal oldali sor, nézet és kezdőállapot | A bal sáv sorának felirata **„Unnamed (6)”**. Kattintásra a jobb oldalon az **„Unnamed people”** cím és személy-ikon, alatta **„6 Face(s)”**, majd az útmutató jelenik meg: „Select someone you know and add a name, or click the 'x' to ignore that person.” Jobbra az **„Expand groups”** és **„Show ignored faces”** gomb látszik; a nézet csoportosítva indul. Az alsó állapot **„No Selection”**, a tálca üres. A job-163 felvételén a bezárás után ez az állapot marad (`job-162`; `job-163`, 4. és 8. kép). | A `FolderPane.qml:587-630` a People gyűjtemény alatt, a személyek elé teszi az „Unnamed (N)” sort; beolvasás alatt is látszik, a számlálóba beleszámít (#5190). Kattintáskor a `Main.qml:3267-3271` törli a fotók kijelölését, `unnamed` módra vált, és a `Main.qml:3675-3692` helyén megjeleníti az `UnnamedFacesView`-t (#5183). A nézetfejléce a `UnnamedFacesView.qml:104-114, 165-229` sorokban készül; induláskor `grouped: true` és üres arc-kijelölés (`UnnamedFacesView.qml:29-52, 127-138`). | A fő nézet és az üres kezdőkijelölés felvétellel rögzítve. A Picasa tálca és a „No Selection” állapotát a job-162 leírása igazolja; a PicasaPy a fotó- és arc-kijelölést is üresen kezdi. |
| Nézet két módja: csoportosítva és kibontva | Csoportosítva (alapállapot): a váltógomb **„Expand groups”**, az útmutató „Select someone you know and add a name, or click the 'x' to ignore that person.”, a csempéken saját **„Add a name”** mező és X, a fejlécben nincs névmező. Ez kijelöléstől függetlenül így van: kijelölés nélkül, egy csempe kijelölésével és Ctrl+A után is (`job-180`, 6., 10. és 15. kép; Ctrl+A után mind a hat csempe kijelölve). Kibontva („Expand groups” után): a váltógomb **„Group by face”**, az útmutató „Select someone you know and add a name”, a csempéken nincs saját mező és X; a fejléc „6 Face(s)” sorában jobbra **„Add a name”** mező és **„Ignore Selected”** gomb van, kijelölés nélkül szürke (`job-183`, 10. kép; kijelöléssel, Ctrl+A után a gomb sötét, a mező fehér, 15. kép). | #5214 (0.9.124) óta így (f99e7a1eb): a kibontott nézet fejlécében van a névmező és az Ignore Selected gomb; a csoportosítottban nincs. | Kész, ha a két nézet a `job-180` és `job-183` lépéssorával felvett állapotot mutatja (kijelölés nélkül és Ctrl+A után, képkocka-összevetéssel). |
| Első megnyitás üdvözlőablaka | Első alkalommal sötét, modális ablak takarja a nézetet. Cím: **„Welcome to the Unnamed people album!”**; a job-162 12. képéhez tartozó komment teljes szövege: „As Picasa scans your photos, the faces it finds are automatically grouped for easy naming.” / „Things to know:” / „To identify a person, click 'Add a name', then type in the person's name and press Enter. A new People album will be created each time you name someone for the first time.” / „(TIP: Sign in with your Google Account …)” / „To ignore a person, click the 'X' button on the face thumbnail.” / „Suggestions: After you name someone, Picasa may suggest more matching faces …” / „Click 'Learn More' for information about this feature.” Gombok: **„Learn more...”**, **„Close”**. A `…` a komment rövidítése, a hiányzó szöveget nem egészítjük ki. | A `UnnamedFacesView.qml:116-138, 742-829` első megnyitáskor, csak a Név nélküliek módjában mutat modális ablakot; bezáráskor a `FaceScanController` megjegyzi a megjelenítést (`face_scan_controller.py:200, 802-810`). A jelenlegi ablak szövege és gombjai a `UnnamedFacesView.qml:767-829` sorokban vannak. | A kezdőablak és a job-162-n leírt tartalom megerősített, élő felvétellel. Az eredeti kommentben `…`-tal rövidített mondatrészek pontos Picasa-szövege nem állapítható meg ebből a forrásból. |
| „Learn more...” gomb az üdvözlőablakban | Az eredetiben a gomb alsó szélére kattintva (`job-175`), majd a közepére kattintva (`job-177`) a felvételen semmi nem változik: új ablak nem nyílik, az üdvözlőablak nyitva marad. `job-175` szerint 15 mp-ig a Picasán belül nem nyílik ablak. A Colab-gépen nincs böngésző, ezért a megnyitott cím a felvételből nem olvasható ki (`job-177`). | A PicasaPy-ban a gombnak most nincs kezelője (`job-175`). | Nyitott: a cím a binárisból olvasandó ki (19.1, 6. pont). A jegykommentek „5. kérdés” néven hivatkoznak rá, de a 19.1 listában az 5. pont a csempe-sorrend, ezért a címet új, 6. pontként vettük fel. Kész, ha a gomb kezelője és a megnyitott cím bináris címmel rögzítve van. |
| Csempék, mezők, X, méret és sorrend | Csoportosított nézetben álló arc-kivágások jelennek meg; a job-163 4. és 8. képe soronként öt csempét mutat, mindegyik alatt saját **„Add a name”** mezővel, a csempe jobb felső sarkában kis X-szel. A komment csak közelítő csempeméretet rögzít, ezért a pontos pixelméret **NINCS MEG**. A pontos arcbélyeg-sorrend és a felvételen látható csoporthatárok nincsenek leírva a kommentben: **NINCS MEG**. | A `face_scan_controller.py:812-858` az arc-csoportokat csoportazonosító szerint növekvően, a még nem csoportosított elemeket a végén adja vissza; összecsukva csak csoportonkénti előnézetet ad. A `UnnamedFacesView.qml:355-410` 194 × 198-as rácscellát és 146 × 172-es arckivágást állít be; a `UnnamedFacesView.qml:482-508` minden archoz saját, 172 px széles „Add a name” mezőt ad. A csempe X-e a `UnnamedFacesView.qml:417-440` sorokban van. | A csoportosított alapállapot és az egyedi mező/X felvétellel igazolt. Ne vegyük át a közelítő pixelméretet pontos adatként. A Picasa pontos csempesorrendjéhez és csoporthatáraihoz külön képkocka-leírás kell. |
| Fejlécmező és a csempe névmezője | A binárisban a **fejléc** `addname` parancsa a jobb fiók PeoplePaneljéhez jut (`0x00602970`), amely ott `headerautocomplete` és `header_editbox` mezőt hoz létre (`0x00640670`, `peoplepanel_text.tre`). Ez a panelmező útja. A Név nélküliek **csempéjének** saját „Add a name” mezője külön, élő úttal igazolt (`job-163`, 4. és 8. kép; `job-66`). | A Név nélküliek csempéjén saját `TextField` van (`UnnamedFacesView.qml:482-508`); a jobb oldali People panel sormezője külön komponens (`PeoplePanelRow.qml:149-166`). A job-167 útvonalon a csempe mezője Enterre mindig People ablakot kér (`Main.qml:3690-3692`; `PeoplePanel.qml:192-210`). A jobb fiók meglévő névre történő Enter-kezelése ettől eltér (#5199; `PeoplePanel.qml:192-205`). | A „névmező inline panelmező” állítás csak a fejléc `header_editbox` mezőjére vonatkozik; a Név nélküliek csempéjének saját mezője van. A két út ne legyen összemosva. |
| Új név, People ablak és tárolás | A csempe mezőjébe írt **„Teszt Elek”** után Enterre **„People”** ablak nyílik. A Search mezőbe a név előre be van írva és ki van jelölve; a névlista üres, a **„Delete Person”** és **„OK”** tiltott, a **„New Person”** aktív. Jobbra „Name:” és „Email(s):” mező, szürke „Sync Face Tags with Web Albums” jelölő és „Revert”; alul „Manage Online Contacts”, „Refresh Contacts”, „OK”, „Cancel” (`job-163`, 14-19. kép). Az új személy OK-ja után a bal sávban `People (2)`, `Unnamed (5)`, `Teszt Elek (1)` látszik (`job-167`, 18. kép). A `.picasa.ini`-ben `[Contacts2]` alatt `<azonosító>=Teszt Elek;;`, a fotó szakaszában `faces=rect64(…),<azonosító>` szerepel (`job-66`; `job-167`, 18. kép). A job-66 helyesbítése szerint ez is a csempe-mező útja. | A csempe Enter-kezelője kiüríti a mezőt és jelzi a beírt arcot/nevet (`UnnamedFacesView.qml:501-508`); a `Main.qml:3690-3692` ezt People ablakra küldi. A `PeopleManagerDialog.qml:53-98` előtölti a Search mezőt, meglévő találatnál kiválasztja a kontaktot; a `PeopleManagerDialog.qml:146-170` kezeli a „New Person” műveletet; a `PeopleManagerDialog.qml:241-289, 299-380, 381-473, 485-510` adja az OK/Choose útját, a kereső/listát, a névjegymezőket és az alsó gombokat, majd menti és a kijelölt arcra alkalmazza. A `face_scan_controller.py:861-923` a sikeres arcot megnevezettként rögzíti, frissíti a mappát és az arcszámot; a `faces_helper.py:265-295` az érintett `.picasa.ini`-t írja. | Az új név útja és eredménye megerősített, élő felvétellel. A `[Contacts2]` és `faces=` adatot a job-66 ugyanebből a csempe-mezőből mérte; ez nem másik felületi útvonal. |
| Meglévő név, javaslatlista, Choose és Escape | A mezőbe írt `Tes` alatt javaslatlista jelenik meg arcképpel és **„Teszt Elek”** névvel (`job-167`, 22. kép). A teljes név Enterre People ablakot nyit, a `Teszt Elek` személy kijelölve, „1 Photo in Picasa” adatsorral, **„Choose”** gombbal (`job-167`, 26-30. kép). A felvétel nem kattintott a Choose-ra, ezért az arc a Név nélküliek között maradt. Az ismeretlen `Valami` keresés üres listát és Name mezőt, tiltott OK-t ad; Escape bezárja az ablakot változtatás nélkül (`job-167`, 32-34. kép). | A csempe mező részleges szövegre a névjegyek között kis-nagybetűtől független részsztringet keres; a felugró listában kép és név jelenik meg (`UnnamedFacesView.qml:371-385, 512-589`). A csempe Enter útja meglévő névnél is People ablakot nyit, a meglévő kontakt kiválasztásával és **Choose** gombbal (#5192; `PeoplePanel.qml:192-210`; `PeopleManagerDialog.qml:82-93, 499-505`). A listabeli javaslat-elemre kattintáshoz nincs külön aktiváló kezelő a csempe popupjában (`UnnamedFacesView.qml:547-587`). | A javaslat megjelenése, People ablak, Choose felirata és az ismeretlen névnél Escape útja élő felvétellel igazolt. A javaslatelem kattintásának rögzítése nyitott. A Choose utáni állapot lezárva, lásd a következő sort (helyesbítve, job-179). |
| Choose után: a meglévő személyhez rendelés | A csempe-mezőbe írt meglévő név Enter után a People ablak nyílik, a meglévő személy kijelölve, a jóváhagyó gomb **„Choose”** (`job-167`, `job-179`). A Choose-ra kattintva az ablak bezárul, az arc a meglévő személyhez kerül: `Unnamed (5)` → `Unnamed (4)`, `Teszt Elek (1)` → `Teszt Elek (2)`. A `.picasa.ini`-ben egy `[Contacts2]`-bejegyzés marad, mindkét fotó `faces=` sora ugyanarra az azonosítóra mutat (`job-179`). | #5182 (0.9.123) óta a People ablak Choose-útját valódi kattintásos teszt fedi (d789d91de). | Zárva (`job-179`): nincs nyitott tétel. Referencia a megvalósításhoz: a két számláló-változás és a `.picasa.ini` egy `[Contacts2]`-bejegyzése. |

| Arc mellőzése az X-szel és a fejléc gombjával | A csempe X-ére kattintva **„Ignore People”** megerősítés jelenik meg, majd a **„Ignore Person”** jóváhagyása az arcot mellőzöttként menti: `faces=rect64(27c00680d8ffdb3f),ffffffffffffffff` (`job-64`; a megerősítés képkockája: „Colab EN 36”). Az eredeti fájlkimenet után a mellőzött arc a „Mellőzött emberek” albumba tartozik (15.3/b.1). A fejléc **„Ignore Selected”** gombja csak a kibontott nézetben látszik, kijelölés nélkül szürke (`job-183`, 10. kép). | A csempe X és a kibontott nézet fejlécének **„Ignore Selected”** gombja is megerősítést kér (`UnnamedFacesView.qml:417-440, 273-295, 849-909`), majd a FaceScanController mellőzött állapotba teszi az arcot (`face_scan_controller.py:1138-1166`). A csoportosított nézet fejlécében nincs „Ignore Selected” gomb (helyesbítve, job-183). A fejléc „Show ignored faces” gombja akkor aktív, ha van mellőzött arc (`UnnamedFacesView.qml:223-229`); a külön nézetben a „Stop ignoring” visszahozza a kijelölt arcokat (`Main.qml:3275-3280`; `UnnamedFacesView.qml:279-284, 924-949`). | Az X útja és a `.picasa.ini` eredménye a job-64-gyel megerősített. A job-162/163 a kezdeti „Show ignored faces” gombot mutatja, job-163 4. képén szürkén. |

### 19.1 Nyitott kérdések és megszerzésük

1. **Javaslatelemre kattintás:** nyisd meg a Név nélküliek albumot; a kezdőképkockáról válassz egy csempe „Add a name” mezőt; `kattint [x,y]`, `gepel <meglévő név részlete>`, `var_ablak`; kattints a látható javaslat képére vagy nevére, majd `var_ablak`. Rögzítsd, megnyílik-e a People ablak, megváltozik-e az arc állapota és csökken-e a Név nélküliek száma.
2. **Choose utáni állapot** (lezárva, `job-179`): a csempe-mezőbe írt meglévő név után, a **Choose** gombra kattintva bezárul az ablak, az arc a meglévő személyhez kerül; a `.picasa.ini`-ben egy `[Contacts2]`-bejegyzés marad (lásd a táblázatot).
3. **Escape a csempe mezőjében:** új futásban kattints a csempe mezőjébe, gépelj egy még be nem fejezett nevet, majd `billentyu Escape`, `var_ablak`. Rögzítsd a mező tartalmát, a javaslatpopupot és az esetleges People ablakot.
4. **Ctrl/Shift/húzásos kijelölés** (a Ctrl+A-t a `job-180` már mutatta: mind a hat csempe kijelölve, 15. kép; a többi nyitott): külön futásban kattints egy csempére és rögzítsd az alapot; utána külön próbáld `billentyu Ctrl` + kattintás egy másik csempére, `billentyu Shift` + kattintás egy másik csempére, majd külön `huz [x1,y1] [x2,y2]` két csempe között. Mindegyik után `var_ablak`; a pontokat a ténylegesen kirajzolt képkockáról válaszd ki. Rögzítsd a kijelölt kereteket, a „No Selection”/kijelölésszámot és a tálcát.
5. **Picasa pontos csempe-sorrendje és csoporthatárai:** a job-163 leírása csak öt csempét soronként és hat arcot nevez meg, a pontos pixelméretet, sorrendet és csoporthatárokat nem. A job-163 folytatásában kattints az „Expand groups” gombra, majd `var_ablak`; a teljesen kirajzolt képkockán írd le a csoportcímkéket és a csempék balról jobbra, fentről lefelé sorrendjét. Pixelméretet csak tényleges képkocka-mérés után rögzíts.
6. **A „Learn more...” gomb címe:** a megnyitott cím a binárisból olvasandó ki, a `Label(instructionpanel/learn_more)` kezelőjéből (`job-175`). Rögzítsd a kezelő bináris címét és a megnyitott cím sztringjét. A felvételből nem olvasható ki (`job-177`).

*Bizonyítottsági fok: **megerősített, élő méréssel** a Név nélküliek nézet címére, útmutatójára, fejlécgombjaira és alapállapotára (job-162; job-163, 4. és 8. kép); az első megnyitás üdvözlőablakára (job-162, 12. kép); a csempe saját mezőjére és az új név People-ablak útjára (job-163, 11-19. kép); a javaslat megjelenésére, a meglévő névhez tartozó Choose ablakra és az Escape-re (job-167, 22., 26-34. kép); a Choose utáni állapotra (job-179); a kibontott és a csoportosított nézet fejlécére és csempéire (job-180, job-183); az új név OK utáni állapotára és `.picasa.ini` soraira (job-66; job-167, 18. kép); valamint az X mellőzési útjára (job-64, „Colab EN 36”). **NINCS MEG:** a kommentben rövidített üdvözlőszöveg teljes Picasa-változata, a csempék pontos pixelmérete/sorrendje/csoporthatárai, a javaslatelem kattintása, a csempe-mező Escape-je, a „Learn more...” gomb megnyitott címe (job-175, job-177) és a Ctrl/Shift/húzás kijelölési szabálya.*

**Helyesbítés:** a korábbi „Név nélküliek névmezője inline panelmező” következtetés kizárólag a jobb fiók fejlécmezőjére (`header_editbox`) vonatkozik. A Név nélküliek csempéjének külön „Add a name” mezőjét a job-163 és a job-66 mutatja; a job-66 nem másik felületi útvonal.

## 20. #5184: a személykezelés bináris oldalának eredménye (2026-10-17, 2. kör)

**Hatókör:** a jegy N1, N3, N5, N6, N7 bináris oldala, valamint a felvételes N4 és N8. Az öt dekompilált függvény a `referencia/ghidra/2026-10-17-szemelykezeles.txt` fájlban van: `0x0048ef20`, `0x007ba820`, `0x00584cc0`, `0x00647270`, `0x006470d0`. A többi címet diszasszemblálás (`annot_disasm.py`) és a bináris-index élei (`xrefs`, `string_xrefs`) adják. **Az index csak a közvetlen hívásokat látja**, a vtable-hívásokat nem; a negatív állítások erre a korlátra épülnek.

**Jelölés:** `bináris 0x…` = a címen olvasott kód · `Ghidra` = a dekompilált kimenet · `index` = a bináris-index éle · `disasm` = a kód helyi diszasszemblálása · `felvétel (job-N)` = a Colab-végrehajtó leírása · `NINCS MEG` = nem szerezhető meg eddig.

### 20.0 Mérleg

| Pont | Eredmény röviden | Állapot |
|---|---|---|
| N1 | A sorba állító útban nincs név-feltétel a 0x0048ef20 és a 0x0048af60 olvasatában; a gyűjtést a 0x0048bae0 és a 0x006b6a50 lookup dönti el, ennek név-feltétele NINCS MEG (21.3). | BLOKKOLT |
| N3 | A gyári küszöbök megvannak (21.1): 0,85 (FRSuggestionThreshold), 0,90 (FRSuggestionSingleThreshold, a detektáló kód nem olvassa), 0,85 (FRSortThreshold), 0,50 (FRRecommendIncludeLimit). A bemeneti méret (960 px) és a felismerési arány: NINCS MEG (21.2). | BLOKKOLT |
| N4 | A nézőben alapból nincs keret és név a megnevezett arcon (felvétel). | LEZÁRVA |
| N5 | A kijelölt arc és a csempe mellőzése az ini-íróhoz vezet (megerősítve). A személyszintű út NINCS MEG: a sztringek a 0x005fdc30 és a 0x00640340 függvényhez tartoznak, a hívásaik vtable-on át mennek (21.4). | BLOKKOLT |
| N6 | A törlés a memóriabeli kötést bontja (0x007ba820 → 0x005836f0, 0x00584cc0; 21.5). A [Contacts2] írója (0x00586e20) nem a törlési út közvetlen hívottja; a lemezre írás és az arcok sorsa NINCS MEG. | BLOKKOLT |
| N7 | Név nélküliek: többes kijelölés (megerősítve). Személykezelő: a törlés egy sort céloz; a lista kijelölési módja NINCS MEG. | BLOKKOLT |
| N8 | A referencia-felvétel a job-186; a leírása nem állt rendelkezésre, ezért itt nincs szöveg. | BLOKKOLT |

Nyitott kérdések: 0 nyílt · 1 lezárva · 6 blokkolt · 0 hatókörön kívül · 0 „csak nyitva”

> **3. kör (2026-10-17):** az N1, N3, N5 és N6 pontok bővített eredménye a 21. szakaszban van, a fenti tábla ahhoz igazodik. A 20.1-20.8 szöveg a 2. kör állapota; a 21. szakasz helyesbíti.

### 20.1 N1: már megnevezett kép és a sorba állítás

1. **A sorba állítás menete (Ghidra, disasm).** A `0x0048ef20` képenként dönt. A `0x0048ec70` a kulcshoz tartozó, küszöb feletti arcok indexeiből ellenőrző összeget képez (`bináris 0x0048ed57-0x0048eda6`: `rol 7`, `xor`), és a `0x0048ef20` ezt a tárolt értékkel veti össze (`Ghidra`, a 242. sor: `uStack_11c == *puVar5`). Egyezés esetén a kép kimarad.
2. **Nincs név-feltétel a két függvényben.** Az egyetlen összehasonlítás az arc-tábla értékét a kép kulcsával veti össze (`bináris 0x0048ed67-0x0048ed71`). A második tábla értékét 5000-es (`0x1388`) küszöbbel nézi (`bináris 0x0048ed85-0x0048ed8c`).
3. **Feltételes:** a kulcs jelentése (kép- vagy személyazonosító) a hívóban nincs igazolva. Ha személyazonosító volna, az összeg a személy arcainak halmaza lenne, és az állítás gyengülne.
4. **A mi oldalunk (kódolvasat, NEM futtatva):** `src/picasapy/app/face_scan_controller.py:470-474` (a 2. körben írt 466-476 pontatlan volt). A fotó kimarad, ha az ini-ben van azonosított arc (`is_identified`). Ez név-alapú kihagyás, az eredeti sorba állítójában nincs meg.
5. **Nyitott:** talál-e az eredeti további arcot a névvel rendelkező képen. Ehhez a detektor utáni feldolgozás (`0x0048e1f0` után, `0x0048af60`) és egy Colab-mérés kell. NINCS MEG.

### 20.2 N3: a detektor paraméterei

- A `0x0048ef20` float-argumentuma nulla esetén a `this+0x3498` mezőt használja (`Ghidra`, 651-652. sor). Az egyik közvetlen hívó, a `0x00414940`, nullát ad át (`bináris 0x00414a8f`: `fldz`, hívás `0x00414a9e`). Ezen az úton a küszöb tehát a `this+0x3498` tárolt értéke. **A `this+0x3498` gyári értéke 0,85; írói: `0x0048aab0` és `0x00415790` (21.1).**
- A detektor-hívás helye a `0x0048e1f0` (912 bájt); ez a kép-futtató, nem igazolt, hogy maga a detektor. A float ott a negyedik argumentum (`bináris 0x0048e939`, `0x0048e93f`). A függvényben nincs közvetlen 960-as vagy 0,9-es állandó (`disasm`). A detektor belső paraméterezése indirekt vtable-hívásokon át történik (`bináris 0x0048e242`, `0x0048e2f1`); a hívott célok: NINCS MEG.
- A `this+0x2e10` detektor-objektumot a `0x0045f0c0` tölti be a `plugins/red.cfg` fájlból (16. szakasz). A betöltött mezők: NINCS MEG.
- A `0x1388` (5000) a `0x0048ec70` második tábláján szűr; a tábla jelentése (pontszám?) nincs igazolva, és nem a detektor küszöbe. A 3.4/d szakasz mért tartománya (≈5100-6300) összefér vele, de a tábla és a mért oszlop megfeleltetése nincs igazolva.
- **Az eredeti felismerési aránya: NINCS MEG.** Csak mért adat adhatja; a Colab-végrehajtó felvétele kell.

### 20.3 N5: mellőzés (kijelölt arc, csempe, személy)

**Kijelölt arc (`0x006470d0`, Ghidra, index).** A kijelölés listáját a `+0xeac` alobjektum vtable-hívása adja (`+0xd8` slot). A `0x0044a6b0` teszt nullától eltérő értéke 1000000 hibával megszakítja a műveletet, és ekkor nincs írás. Egyébként az album-műveletek futnak (`0x004d9aa0` a 0 és a 2 jelzővel, `0x004da1d0` a 2 jelzővel), majd **minden kijelölt arcra `0x00484820(rekord, arc, 1, 0)` hívódik** (`Ghidra`; index: direkt él). **Megerősített:** a kijelölt arc mellőzése az ini-írót hívja, és a mért kimenet (job-64: `faces=rect64(…),ffffffffffffffff`) ugyanezt mutatja.

**Helyesbítés:** az előző körben a `0x006470d0` a `CThumbDB` `+0x2e94` és `+0x2e98` mezőit hívta. A dekompilált kód szerint az album-műveletek a `*(DAT_00d67668+0x1034)+0x68` táblán futnak. A `]ignoreface` sztringet a `0x004ac650` használja (`index`), nem a `0x006470d0`. A `+0x2e94` és `+0x2e98` megfeleltetés NINCS igazolva.

**Csempe (`0x00647270`).** A csempe mellőzése közvetve eléri az ini-írót: a `0x00647270` a `0x00449090`-t hívja (`Ghidra`, index), a `0x00449090` pedig a `0x00484820`-t (`index`; `disasm`: `bináris 0x004498f3`, argumentumok: az arc, a `1` és a `0`). A `0x00449090` hívása feltételes: a `0x0044a6b0` teszt nullától eltér, és a `param_3` jelző nem nulla. Ha a `param_3` nulla, és a teszt nem nulla, a függvény 1000000 hibával tér vissza. **Feltételes:** a `0x00449090` belső feltétele NINCS dekompilálva.

**Személyszintű mellőzés: NINCS MEG.** A „move this person to the ignored people album” sztring (`0x00c99830`) a `0x005fdc30` és a `0x00640340` függvényekhez tartozik (`index`). Egyik sincs dekompilálva, ezért nem tudjuk, melyik tárolót írja.

### 20.4 N6: a személy törlése

**A törlési kezelő (`0x007ba820`, Ghidra).**
- Egy aktív sort céloz: a sor indexe a `+0x13c` mezőben van, a `0xffffffff` jelentése „nincs kijelölés”. Rendezett listánál az indexet a `+0x100` tömbön át kell feloldani.
- Megerősítés: a `ContactManagerDlg::ConfirmDelete` párbeszéd. A „ne figyelmeztess” beállítás a `Preferences` csoportban van.
- Sorrend: `0x005836f0` (feltételes: a sor jelzőbitje 1 (`bVar1 & 1`), a kollekció létezik, és `(jelző & 6) != 4`), majd `0x00584cc0(azonosító)`, majd a sor eltávolítása a felületi listából (`0x007b5ad0`, nincs dekompilálva), végül a sor-jelző tömb eltolása bájtonként.

**A `0x00584cc0` (Ghidra).** Zárolás után megkeresi az elemet (`0x00588210`), törli a csomópont `+0x38` mezőjének 0. bitjét, majd meghívja a `0x00587b90`-t. Ezt csak a `0x00584cc0` hívja (`index`). Ha az nem sikerül, a `0x0058dde0` következik.

**A [Contacts2] írója (`0x00586e20`).** A törlési út egyik függvénye sem hívja közvetlenül (`index`, direkt élek). Közvetlen hívói: `0x00484820` (az arc-író; `disasm`: `bináris 0x00485118`, a kollekció a `this+0x2c5c` mezőből jön), `0x0068ac20` és `0x007d55f0`. A törlés tehát a memóriabeli listát frissíti. A lemezre írás későbbi mentésben vagy az arc-íróhoz kötve történik; ez utóbbi még nincs vizsgálva. **Feltételes.**

**Az arcok sorsa: NINCS MEG.** A `0x005836f0` (2332 bájt) a törlés feltételes ágában fut, de nincs dekompilálva, ezért nem tudjuk, mit csinál az arcokkal. Direkt élei között nincs az arc-író (`0x00484820`).

### 20.5 N7: kijelölési modell

- **Név nélküliek (megerősítve):** a mellőzési út (`0x006470d0`) egy listát dolgoz fel, amelynek hossza a vtable-hívásból jön (`Ghidra`), és minden elemen végigmegy. A felvétel (job-180, Ctrl+A után hat csempe) ezzel egyezik.
- **Személykezelő:** a törlési kezelő (`0x007ba820`) egyetlen sort olvas (`+0x13c`). A lista kijelölési módja (egy vagy több) a `contactmgr.fen` fájlból vagy a lista-vezérlő jelzőjéből dönthető el. Ezt nem olvastam: **NINCS MEG.**

### 20.6 N4 és N8: felvételek

- **N4 (job-187): LEZÁRVA.** A megnevezett arcon a nézőben alapból nincs keret és nincs név. Ez felvételi eredmény: a képkockát nem néztem meg, az összefoglalót a jegy adja. Nálunk nem mérve.
- **N8 (job-186): BLOKKOLT.** A People Manager leírása nem állt rendelkezésre, ezért szöveg nincs. A mérce a job-186 kimenete; a leírást a jegy kommentjéből kell ide másolni.

### 20.7 Ghidra-kör kérések

> **3. kör:** a 0x0045f0c0, 0x0048af60, 0x005836f0, 0x00587b90 és 0x0058dde0 kérdése lezárult (21.7). A többi kérés nyitott; a 21.6 szerinti köteg váltja le.

Ghidra-kör kell: 0x0048e1f0 - a detektor vtable-hívásainak (`call eax`, `0x0048e242`, `0x0048e2f1`) célja: milyen bemeneti képméretet, pontszámküszöböt és minimális arcméretet kap, és honnan (a `this+0x2e10` objektum mezőiből vagy a kapott float-ból)? [blokkoló]

Ghidra-kör kell: 0x0045f0c0 - a `red.cfg` betöltője milyen detektor-paramétereket állít be a `this+0x2e10` objektumra, és hol íródik a `this+0x3498` küszöb? [blokkoló]

Ghidra-kör kell: 0x0048af60 - a sorba állítás `param_5 == 0` ága mit csinál a detektor eredményével, és hogyan viszonyul a 0x0048e1f0 hívásához? [blokkoló]

Ghidra-kör kell: 0x005836f0 - a Delete Person arc-ága mit csinál a törölt személy arcaival (`faces=` törlés, átnevezés vagy mellőzés)? [blokkoló]

Ghidra-kör kell: 0x00587b90 és 0x0058dde0 - a memória-listából törlésen túl írnak-e a [Contacts2]-be? Ha nem, a 0x0068ac20 és a 0x007d55f0 mikor és milyen mentési úton hívja a 0x00586e20-t? [blokkoló]

Ghidra-kör kell: 0x0044a6b0 - mit tesztel a visszatérési értéke, és mit jelent a csempe-ág (0x00647270) és a kijelölt arc ága (0x006470d0) elágazása? [blokkoló]

Ghidra-kör kell: 0x005fdc30 és 0x00640340 - a személyszintű mellőzés („move this person to the ignored people album”) melyik tárolót írja? [blokkoló]

### 20.8 A #5184 mérlege

**Bizonyítottsági fok: feltételes.** Megerősített: az N5 szűk állítása (a kijelölt arc mellőzése az ini-írót hívja, a mért kimenet `ffff…`) és az N7 Név nélküliek többes kijelölése. Feltételes: az N1 név-független sorba állítása (a kulcs jelentése és a detektor utáni ág nincs igazolva), az N6 törlési útja (a [Contacts2] írása későbbi mentésen vagy az arc-íróhoz kötve történik), és a csempe-ág (a `0x00449090` belső feltétele). NINCS MEG: az N3 detektor-paraméterei és az eredeti felismerési aránya, az N5 személyszintű útja, az N6 arc-sorsa, az N7 Személykezelő kijelölési módja, az N8 leírása.

**Cáfoló kísérletek.** (a) N1: a két függvényben kerestem név- vagy kontakt-összehasonlítást; nincs. Ez a negatív állítás csak a két függvény teljes kódjára szól, a hívóit nem olvastam végig. (b) N5: a kijelölt arc ágában az író minden elemre fut, de csak akkor, ha a `0x0044a6b0` teszt nullát ad; nullától eltérő értéknél a függvény írás nélkül tér vissza (1000000). (c) N6: a törlési út direkt élei nem tartalmazzák a [Contacts2] írót; ez index-negatív, a vtable-hívásokat nem zárja ki.

### 20.9 Nyitott kérdések mérlege (20.)

Nyitott kérdések: 0 nyílt · 1 lezárva · 6 blokkolt · 0 hatókörön kívül · 0 „csak nyitva”. A blokkolt tételek mindegyike Ghidra-kört vagy Colab-felvételt igényel; egyiknek sincs tulajdonosi döntésre vagy gépre szüksége.

## 21. #5184, harmadik kör: N1, N3, N5 és N6 (2026-10-17)

**Hatókör:** a 20. szakasz N1, N3, N5 és N6 pontja, valamint a 20.7 Ghidra-kérései. Források: a két dekompilált kimenet (`referencia/ghidra/2026-10-17-szemelykezeles.txt`, `…-2.txt`), a bináris-index (`functions`, `xrefs`, `string_xrefs`), a helyi diszasszemblálás (`annot_disasm.py`), és egy teljes `.text`-pásztázás (`paszta.py`, 2 884 879 utasítás, `memoria_kapu()` első lépésként). A pásztázás a tároló-utasításokat kereste a `+0x3498`, `+0x349c`, `+0x34a0`, `+0x34a4` és `+0x34a8` eltolásra, írásra és olvasásra egyaránt. A `plugins/red.cfg`-t nem olvastuk ki: mezőnevek nélkül (16. szakasz) nem ad szemantikát.

**Jelölés:** ugyanaz, mint a 20. szakaszban.

### 21.1 N3: a gyári küszöbök (megerősített gyári értékek)

A `0x0048aab0` (986 bájt) a `Preferences` csoport öt kulcsát olvassa, mindegyiket alapértékkel. Az olvasott egész értéket a függvény `/ 100` skálázza. Az osztó a `0x00cf3a08` duplapontos állandó, amelynek értéke `100.0` (`bináris 0x00cf3a08`, bájtok `0000000000005940`).

| Preferences-kulcs | alapérték (bináris) | normált érték | célmező | felhasználás |
|---|---|---|---|---|
| `FRSuggestionThreshold` | 85 (`0x0048aabc`: `mov ebp, 0x55`) | **0,85** | `this+0x3498` | a `0x0048ef20` olvassa (`0x0048fad3`; Ghidra `…szemelykezeles.txt` 651-652. sor) |
| `FRSuggestionSingleThreshold` | 90 (`0x0048ac6f`: `0x5a`) | **0,90** | `this+0x349c` | csak a `0x0048aab0` és a `0x00415790` éri el (teljes `.text`) |
| `FRSortThreshold` | 85 (`0x0048acda`: az `ebp` még `0x55`) | **0,85** | `this+0x34a0` | csak a `0x0048aab0` éri el |
| `FRRecommendIncludeLimit` | 50 (`0x0048ad46`: `0x32`) | **0,50** | `this+0x34a4` | a `0x0048e1f0` olvassa (`0x0048e252`), float-ként, a pontszámmal összevetve (`0x0048e33e`) |
| `FRRecommendShowLimit` | 70 (`0x0048ae2c`: `0x46`) | NINCS MEG | a beolvasott érték helyi változóba kerül (`0x0048ae05`) | NINCS MEG |

**Két független út a 0,85-re.** (A) A beolvasó: 85 / 100 = 0,85 (fenti sor). (B) Az inicializáló `0x00415790` a `[ebp+0x3498]` mezőt a `0x00c7dd24` float-állandóból tölti (`bináris 0x00415f71`), és az állandó értéke `0,8500000238` (bájtok `9a99593f`). A két út ugyanazt adja, de különböző forrásból: egy alapérték és egy osztó, illetve egy kész literál.

**Caveat:** a `0x00415790` és a `0x0048aab0` ugyanazon `this` mezőit írja, de az eltolás egyezésén túl ez nincs igazolva; más osztály is lehet.

**Bizonyítottsági fok (gyári értékek):** megerősített (két bináris út). **Nincs megerősítve:** a felhasználó tényleges beállítása, mert a `Preferences` tároló nincs a bizonyítékban; a futó érték NINCS MEG.

**Amit NEM állít ez:** a `FRSuggestionThreshold` neve javaslat-küszöb. Nincs igazolva, hogy a 0,85 a detektálást vagy a felismerést szabályozza; a `0x0048ef20` olvasása csak a kód olvasata.

### 21.2 N3: a 960 px, a pontszám-skála és a felismerési arány: NINCS MEG

- **960 px:** a `0x0048e1f0`-ban és a beolvasóban nincs 960-as állandó (`disasm`, 20.2). A képet a detektorhoz a `0x0048e5da` köti (1613 bájt; hívja a `0x0048bae0`-t és a `0x0048e1f0`-t). Ennek kimenete nincs dekompilálva: Ghidra-kör kell (21.6).
- **Pontszám-skála:** a `0x0048e1f0` a 0,50 küszöböt float-ként veti össze a detektor pontszámával (`0x0048e33e`: `fld`, `fcomp st(1)`). A detektor kimenetének egysége nincs igazolva. A Ghidra-kimenet `(DWORD)` konverziója ezen a ponton félrevezető: a diszasszembly szerint a küszöb float marad (`[esp+0x20]`).
- **Nem egyenértékű mennyiségek:** a mi 0,9-esünk (`src/picasapy/faces/detector.py:42`, `_DEFAULT_SCORE_THRESHOLD = 0.9`) a YuNet detektor pontszám-küszöbe. Az eredeti 0,85 és 0,90 Preferences-kulcsok, és más mennyiségnek számítanak. **Nem állítjuk egyenlőnek.** A PMP-pontszámmal (3.4/d, ≈5100-6300) sincs megfeleltetés.
- **Felismerési arány (az eredetié):** csak felvétellel vagy mérőadattal adható meg (Colab-felvétel vagy mérés); NINCS MEG.

**Bizonyítottsági fok:** a gyári értékek megerősítettek (21.1); a 960 px, a pontszám-skála és a felismerési arány NINCS MEG.

### 21.3 N1: a sorba állítás név-feltétele: feltételes, a döntő lookup nincs olvasva

Az eredeti lánc, a kód szerint:

1. **`0x0048ef20`** képenként (`…szemelykezeles.txt` 188-242. sor): a `0x0048ec70` a kép küszöb feletti arcainak indexeiből ellenőrző összeget képez. Ha az egyezik a `0x2808`-as tábla tárolt értékével (242. sor), a kép kimarad. **Nincs név-feltétel.**
2. **`(char)param_5 == 0` ág** (`…szemelykezeles.txt` 404-407. sor): a `0x0048af60` gyűjt. Minden jelölt képre meghívja a `0x0048bae0`-t (`…-2.txt` 459. sor); a 0-val visszatérő képek bekerülnek a listába (462. sor).
3. **Küszöb:** a detektor csak legalább **151** jelölttel fut. `(unaff_EDI[1] & 0xfffffffe) < 0x12d` esetén a `0x0048af60` 0-val tér vissza (`…-2.txt` 559. sor). A detektor eredménye legfeljebb **150** elem (`local_14[4] = 0x96`, 651. sor).
4. **`0x0048bae0`** (650 bájt, `bináris`): ha a táblában már van érték, 0-val tér vissza. Különben a `0x006b6a50` lookupot hívja (1885 bájt), és csak annak sikere esetén ad 0-t. **A `0x006b6a50` név-feltétele NINCS MEG:** a diszasszemblálásban nincs `cmpsb`, és nincs sztring-hivatkozás, de sok közvetett hívás van (`call edi`, `call eax`, `call edx`, IAT-hívás), ezért a diszasszemblálás nem dönt.

**A mi oldalunk (kódolvasat, NEM futtatva):** `src/picasapy/app/face_scan_controller.py:470-474`: `any(face.is_identified …)` esetén a fotó kimarad. Ez név-alapú kihagyás; az eredeti 1. pontja szerint a sorba állító nem így dönt.

**Cáfoló kísérlet:** a `0x0048ef20`, a `0x0048ec70` és a `0x0048af60` olvasatában nincs névhez kötött összehasonlítás. Ez a negatív állítás **csak erre a három függvényre** szól, a `0x006b6a50`-ra nem.

**Bizonyítottsági fok:** feltételes. Ha a `0x006b6a50` nem név alapján zár ki, a mi `is_identified` kihagyásunk eltér az eredetitől, és a fejlesztés (a névvel rendelkező fotó is bekerül a detektálásba) jegybe való. Ha név alapján zár ki, a mi viselkedésünk megfelel az eredetinek.

### 21.4 N5: a személyszintű mellőzés: NINCS MEG

- **Kijelölt arc** (`0x006470d0` → `0x00484820`, index-él, ini-író): megerősített (20.3).
- **Csempe** (`0x00647270` → `0x00449090` → `0x00484820`): feltételes. A `0x00449090` belső feltétele és a `0x0044a6b0` visszatérési értéke NINCS MEG.
- **Személyszintű:** a `Are you sure you want to move this person to the ignored people album`, az `Ignore Person` és az `Ignore People` sztring (`bináris 0x00c99830`, `0x00c8f2b8`, `0x00c991c0`) a `0x005fdc30` (1117 bájt) és a `0x00640340` (806 bájt) függvényhez tartozik (`string_xrefs`). Közvetlen hívottjaik az indexben: 3, illetve 10. Egyik sem hívja a `0x00484820`-t vagy a `0x005836f0`-t. **Ez nem negatív bizonyíték:** az index nem látja a vtable-hívásokat, és a két függvény sok közvetett hívást tartalmaz.

**Bizonyítottsági fok:** NINCS MEG a személyszintű út. Ghidra-kör kell (21.6).

### 21.5 N6: a törlés memóriabeli kötése megerősített; a lemezre írás NINCS MEG

A törlési kezelő (`0x007ba820`, `…szemelykezeles.txt` 1276-1292. sor):

- Ha a kijelölt sor jelzőbájtjának 0. bitje be van állítva (`(bVar1 & 1) != 0`), és `(bVar1 & 6) != 4`, a kezelő:
  1. a személy-objektum vtable `+0x68` hívásával (`*piStack_17c + 0x68`) megkapja a név-objektumot;
  2. meghívja a **`0x005836f0`**-t a személy 64 bites kulcsával és a név-objektummal;
  3. majd meghívja a **`0x00584cc0`**-t a személy kulcsával (1292. sor).
- A **`0x00584cc0`** (489 bájt) megkeresi az elemet (`0x00588210`), törli a csomópont `+0x38` 0. bitjét, és meghívja a **`0x00587b90`**-t (a név-arc láncok kivétele, `…-2.txt` 1158-1416. sor). A **`0x0058dde0`** a figyelők értesítése a 64 bites kulccsal (`…-2.txt` 1419-1468. sor); a 20.4 szerint ez a sikertelen ág.
- A **`0x005836f0`** (2332 bájt, `…-2.txt` 741-1155. sor) a 64 bites kulcsot a név táblájából kiveszi, és a csomópontot a szabad-listára (`+0x10`) fűzi vissza. Hatása az arc-listákra feltételes: a `param_6` puffer szerepe nincs igazolva.

A **`[Contacts2]`** sztring két függvényben van (`string_xrefs`): a **`0x00586e20`** (752 bájt, az író) és a `0x00587110` (1202 bájt, hívója a `0x0045a9d0`). A `0x00586e20` közvetlen hívói az indexben: `0x00484820` (arc-író), `0x0068ac20` (← `0x0068c030` ← `0x006956d0`, `0x0069b240`) és `0x007d55f0` (← `0x00687ec0`, `0x007f7660`, `0x007db8d0` ← `0x006f2530`).

A törlési út Ghidra-hívottjai (`0x00584cc0`, 11 db) között nincs `0x00586e20`. Ez direkt hívási negatív, a vtable-hívásokat nem zárja ki.

**Bizonyítottsági fok:** a memóriabeli kötés bontása feltételes: egy út (a dekompilált törlési kezelő és a `0x00584cc0`), az index hívási élei megegyeznek vele, de ugyanabból a kódból származnak, ezért nem független megerősítés. **NINCS MEG:** (a) a törölt személy arcainak `faces=` sora a lemezen megmarad-e; (b) a `[Contacts2]` törlése mikor íródik ki, azaz a `0x0068c030` vagy a `0x007d55f0` hívóláncának melyik tagja fut a törlés után.

### 21.6 A Ghidra-köteg (a 3. kör után nyitott)

- `Ghidra-kör kell: 0x006b6a50 - a 0x0048bae0 lookupja: név vagy személy alapján zár-e ki képet, és mit ad vissza 0 esetén? [blokkoló, N1]`
- `Ghidra-kör kell: 0x0048e5da - a kép-futtató: honnan jön a detektor bemeneti képmérete (megfelel-e a 960 px-nek), milyen sorrendben hívja a 0x0048bae0-t és a 0x0048e1f0-t, és melyik osztály a param_9 (vtable +0x2c)? [blokkoló, N3]`
- `Ghidra-kör kell: 0x00640340 - a személyszintű mellőzés (move this person to the ignored people album) vtable-hívásainak célja: melyik tárolót írja? [blokkoló, N5]`
- `Ghidra-kör kell: 0x005fdc30 - ugyanez a több-személyes ágra (move the %d selected people to the ignored people album). [blokkoló, N5]`
- `Ghidra-kör kell: 0x0068c030 - a mentési út: a 0x006956d0, 0x0069b240, 0x00687ec0 és 0x007f7660 közül melyik fut a személy törlése után, és ír-e faces= és [Contacts2] sorokat? [blokkoló, N6]`
- `Ghidra-kör kell: 0x0044a6b0 - a visszatérési érték és a csempe-ág (0x00647270) elágazása. [nem blokkoló, N5 csempe-ág]`

### 21.7 Lezárások és helyesbítés a 20. szakaszhoz

- **Helyesbítés (20.2):** a `0x0048e242` nem a detektor vtable-hívása. A `[edx+0x18]` hívás a `this+0x28c0` zárolása (`…-2.txt` 39. sor). A detektor hívása a `param_9` objektum `+0x2c` slotja (`…-2.txt` 78. sor); a `param_9` osztálya NINCS MEG.
- **`0x0045f0c0`** (red.cfg betöltő): lezárva részben. Nem írja a `this+0x3498`-at (teljes `.text`-pásztázás: az írói a `0x00415790` és a `0x0048aab0`). A `this+0x2e10` detektor-objektumot tölti, és a `this+0x2e14`-et 1-re állítja (`…-2.txt` 263-264. sor). A `Preferences\FRTemplateChecking` kulcsot olvassa (254. sor). A betöltött paraméterek mezőnevek nélkül NINCS MEG.
- **`0x0048af60`, `param_5 == 0` ág:** lezárva (21.3).
- **`0x005836f0`, `0x00587b90`, `0x0058dde0`:** lezárva (21.5).
- **`0x0044a6b0`:** NINCS MEG (nincs dekompilálva).

### 21.8 Mérleg (3. kör)

Nyitott kérdések: 0 nyílt · 1 lezárva (N4) · 6 blokkolt (N1, N3, N5, N6, N7, N8) · 0 hatókörön kívül · 0 „csak nyitva”. Megerősített: N3 gyári küszöbök (21.1). Feltételes: N1 (21.3), az N5 csempe-ág (21.4) és az N6 memóriabeli kötés (21.5). A blokkolt tételek mindegyike Ghidra-kört vagy felvételt igényel; tulajdonosi döntést egyik sem.

**Fejlesztési lista: nincs.** Az N1 eltérése csak a `0x006b6a50` olvasata után dől el. Az N3 küszöbök és a mi 0,9-esünk nem egyenértékű mennyiségek, ezért nincs bizonyított hibás viselkedés nálunk.

## 22. #5184, negyedik kör: a Ghidra-köteg C-kódja (2026-10-17)

**Hatókör:** a 21.6 kérdései (N1, N3, N5, N6, és a csempe-ág a `0x0044a6b0`-val), a 21.6 után nyitott új címek, és a 20. szakasz N-pontjainak új állapota. Az N4 lezárt, az N7 és az N8 nem változott.

**Forrás:** `referencia/ghidra/2026-10-17-szemelykezeles-3.txt` (a továbbiakban `-3`). A kódkörnyezethez kellett még a `2026-10-17-szemelykezeles-2.txt` (`-2`: `0x0048e1f0`, `0x0048af60`) és a `2026-10-17-szemelykezeles.txt` (`-1`: `0x0048ef20`, `0x007ba820`, `0x00647270`, `0x006470d0`). A sorszámok ezeknek a fájloknak a sorait jelölik. A `0x0048e590`, `0x0048bae0`, `0x0063f970`, `0x0068ac20`, `0x00586e20`, `0x006956d0`, `0x0069b240` és `0x007b99a0` egyik fájlban sincs meg.

**Jelölés:** ugyanaz, mint a 20. szakaszban. `in_stack_…`: a Ghidra stack-argumentuma, a hívó adja. `LAB_…`: ugrási címke a kódban.

**Röviden:**
- A 960 px nincs a `0x0048e5da` kódjában. Ez a függvény a `0x0048e590` folytatása. A bemeneti képméret forrása a `0x0048e590` vagy a detektor-objektum lehet; ez nincs olvasva.
- A `0x006b6a50` nem néz nevet. A kizárás a hívó visszatérési értékén múlik, a hívó (`0x0048bae0`) nincs a körben.
- A személyszintű tároló-írás nincs a `0x00640340` és a `0x005fdc30` kódjában.
- A `[Contacts2]` sort a `0x0068c030` láncán át írhatja, de hogy a törlés után fut-e, nincs meg.

### 22.1 N1: a 0x006b6a50 (lookup) nem név-alapú

- **Mit csinál (-3, 34-332. sor).** Indexszel olvas: a `param_2` indexű rekordot (hosszát a `param_1[0x19]` táblából, eltolását a `param_1[0x17]` táblából veszi) a `param_3` objektum +4 mezőjű pufferébe másolja (121., 316. sor).
- **Mit ad vissza.** 0: a rekord kiolvasva; nulla hosszú rekordnál is 0 (132-145. sor). 3: az index a tábla végén van (80-93. sor). 2: belső állapot-ellenőrzés (65-79. sor), jelentése NINCS MEG. 0xffffffff: nincs fájl-objektum, és a rekord nem üres (147-161. sor). Más nem nulla érték a hívott függvények (0x009bd220, 0x0099dd50) hibakódja; ezeket nem olvastuk.
- **Név vagy személy alapján zár-e ki?** A saját kódjában nem. Nincs string-összehasonlító hívás a hívottjai között (csak `_memcpy` és `ReadFile`), a 21.3 diszasszemblálásában pedig nincs `cmpsb`. A kizárás ebből a függvényből nem jön, csak a visszatérési értékből.
- **Hívók.** 13 hívója van (-3, 4-16. sor), köztük a `0x0048bae0` (`0x0048bcd5`). A többit nem olvastuk. A hívólista általános olvasóra utal, de ezt nem bizonyítja.
- **Hol dől el a kizárás.** A `0x0048e5da` (-3, 508-537. sor) a `0x0048bae0` visszatérésével dönt. 0 esetén a kép bekerül a gyűjtőbe (540-562. sor), nem nulla esetén kimarad (525-537. sor). A már kitöltött slotú képet a `0x0048bae0` nélkül is a gyűjtőbe teszi (539-562. sor). A kulcs jelentése (kép- vagy személyazonosító) NINCS MEG, ezért az sem dől el, hogy a sikeres lookup ág az ismert vagy az új képekre vonatkozik.
- **Állapot: BLOKKOLT (marad).** A lookup kódszinten nem név-alapú (megerősítve, 22.7). Az eredeti kizárás döntését a `0x0048bae0` adja, ezért a mi `is_identified` kihagyásunk (`src/picasapy/app/face_scan_controller.py:470-474`) eltérése nincs eldöntve.

### 22.2 N3: a 960 px nincs a 0x0048e5da kódjában

- **A 0x0048e5da a 0x0048e590 folytatása.** A `0x0048e590` feltételes ugrással lép bele (-3, 338. sor). Az ESI (`this`), az EBP (képlista) és az EBX (egy `int*`) belépési állapotát, valamint a stack-argumentumokat a `0x0048e590` adja (363-366. sor). A `0x0048e590` hívója a `0x0048ef20` (-1, 879. sor), nyolc argumentummal.
- **Képméret.** A `0x0048e5da`-ban nincs képméret. A 960 (`0x3c0`) konstans sincs a -3 és a -2 kódjában. A -1 fájl egyetlen `0x3c0`-ja (2104. sor) mezőeltolás (`+0x3c0`).
- **Mit kap a detektor (`0x0048e1f0`, -2, 16-115. sor).** Bejegyzésenként hívja a `param_9` +0x2c slotját (78. sor). A kérés: [5] a `this+0x2908` tábla 8 bájtos bejegyzésének mutatója (71-74. sor), [4] a pontszám-puffer kódolt darabszáma (76. sor), [3] a pontszám-puffer. A hívás után a [0] találatszámot és a [3] pontszámokat olvassa (82-85. sor). Képméret egyik mezőben sincs.
- **A param_9.** A `0x0048e5da`-ban stack-argumentum (`in_stack_0000001c`, -3, 567. sor), a `0x0048e590` adja. Az osztálya NINCS MEG.
- **Sorrend.** Ugyanarra a képre a `0x0048bae0` (ha a slot nulla) a `0x0048e1f0` előtt fut. A `0x0048e5da` a kulcslistán (`in_stack_0000005c`) visszafelé halad (477-603. sor). A találatot az `in_stack_00000034` tömbbe fűzi (562. sor). Ha a köteg eléri a határt (`in_stack_00000038 >> 1`), hívja a `0x0048e1f0`-t (564-567. sor), a ciklus után a maradékra egyszer (605-611. sor). A `0x0048e1f0`-nak viszont az `in_stack_00000058` listát adja. Hogy a két tömb hogyan függ össze, NINCS MEG.
- **Pontszám.** A `0x0048e1f0` a `this+0x34a4` mezőt (0,50, FRRecommendIncludeLimit) szűrőküszöbként használja (-2, 50. és 86. sor). A Ghidra `(DWORD)` alakja félrevezető, a 21.2 szerint az összehasonlítás float. A `param_4` a hívótól jön (`in_stack_00000060`). Ha ez a 0,85 (`this+0x3498`), a 104. sor egy FUN_00446610-hívást indít, ezt nem olvastuk.
- **Állapot: BLOKKOLT (marad).** Megerősítve: a detektor bejegyzésenként hívódik (-2, a 55-115. sor ciklusában). Nincs megerősítve: a detektor bemeneti mérete, a 960 px, és a param_9 osztálya.

### 22.3 N5, személyszintű és többszemélyes ág: a tároló-írás nincs ebben a két függvényben

- **0x00640340 (-3, 655-801. sor): megerősítő párbeszéd, nem ír tárolót.** Ha a `Preferences\DoNotConfirmPeopleRemove` igaz, párbeszéd nélkül 0-t ad (692-699. sor). Különben öt erőforrás-kulccsal (`PeoplePanel::ConfirmRemove*`, `il_Cancel`) üzenetablakot épít (703-777. sor). A párbeszéd eredménye (FUN_009bab50) nem nulla: 0xf4242 (778-788. sor). Nulla: FUN_009baae0 és FUN_00401900 után 0 (790-800. sor). Közvetlen tároló-íráshívás nincs. Az ismeretlen hívottjai (0x00401900, 0x009baae0, 0x0051a120) miatt ez csak a közvetlen kódra szól. Hívója a 0x0063f970, két helyen (657-659. sor).
- **0x005fdc30 (-3, 804-1009. sor): szövegválasztó, nem ír tárolót.** Paraméterei: darabszám (`param_1`), név (`param_2`), és az EDI-ben a fajta (0-3). Az EDI=3 címe `DeleteMessage::IgnorePeopleTitle` (847. sor). Névtelen hívásnál a darabszám dönt az egyes és a többes ág között: 1 alatt `RemoveSingleUnknown` (928-930. sor), 2 vagy több alatt `RemoveMultipleUnknown`, a darabszámmal (`FUN_0040eab0(…, param_1)`, 973-981. sor).
- **Egy- és többszemélyes ág.** A darabszám-választás csak névtelen hívásnál érvényes. Névvel megadva (`param_2 ≠ 0`) az EDI=3 a `DeleteFolderWarnPC` ágra esik (867-888. sor). Ez mappa-figyelmeztetés kulcsa, nem személyi.
- **Szöveg és kulcs.** A C-kód csak kulcsneveket ad. A szöveg (a 21.6 „move the %d selected people…” idézete) a sztringtáblából jön. A kulcs és a szöveg összekötését a C-kód nem mutatja.
- **Hívók.** A 0x005fdc30-at a 0x005c9930 (0x005c9a42), a 0x005c9b00 (0x005ca1e1) és a 0x005edef0 (0x005ee072) hívja (-3, 807-809. sor). Melyik hívja EDI=3-mal, és mit ír az igen után: NINCS MEG.
- **Az elágazás.** A 0x0063f970 a 0x00640340-et hívja (0x0063fd96, 0x0063fff2), a csempe-ágat a 0x00647270-nel (0x0063fda9), a kijelölt arc ágát a 0x006470d0-nal (0x0063fffe) (-1, 1550. és 2126. sor). A hívási címek szerint a megerősítés mindkét ág hívása előtt áll. A 0x0063f970 törzsét nem olvastuk.
- **Állapot: BLOKKOLT (marad).** A személyszintű tároló-írás NINCS MEG. Ehhez a 0x0063f970 és a 0x005edef0 kell.

### 22.4 N5 csempe-ág és a 0x0044a6b0 (a 21.6 utolsó tétele)

- **A 0x0044a6b0 visszatérése (-3, 1176-1264. sor).** Az indexhez tartozó állapotot (a `this+0x11a4` táblából, vagy a `this+0x11a8` alapértékből) 0x3E9 (1001) értékkel veti össze (1233. sor). Ha nem egyezik, 0. Ha egyezik, a `param_3` szerinti tábla értékét adja: `param_3 = 0` esetén a `this+0x1bc0` táblából, nem nulla esetén a `this+0x1c20` táblából (1236-1239. sor). Nem nulla visszatérés tehát: az állapot 1001, és a kiválasztott tábla értéke nem nulla. Az 1001 és a két tábla jelentése NINCS MEG (nincs mezőnév).
- **Hívói.** 18 hívója van (-3, 1179-1196. sor), köztük az arc-író `0x00484820` (`0x00484b10`), a `0x00647270` és a `0x006470d0`. Az arc-író maga is futtatja a tesztet.
- **Csempe-ág (0x00647270, -1, 1579-1672. sor).**
  - Ha a `bVar14` igaz (`param_3 = 0`, és a `0x2ad`/`0x2af` jelzők így állnak; 1607-1609. sor), a lista üres (1614-1631. sor), a ciklus nem fut, és nincs 0x0044a6b0-teszt.
  - Egyébként a lista a `param_2` indexű csempe elemét tartalmazza, és a ciklus elemenként két tesztet futtat:
    1. `0x0044a6b0(…, elem, 0)` (1636. sor): nem nulla és `param_3 = 0` esetén 1000000-val megszakít (1638-1643. sor). Nem nulla és `param_3 ≠ 0` esetén a 0x00449090 és a 0x0045ecf0 hívása (1650-1653. sor).
    2. `0x0044a6b0(…, elem, 1)` (1658. sor): nem nulla esetén a 0x00449090 és a 0x0045ecf0 hívása (1665-1668. sor), **a `param_3`-tól függetlenül**.
- **Kijelölt arc (0x006470d0, -1, 2138-2227. sor).** Csak a lista első elemét teszteli (`*local_8`, a 0 jelzővel hívott tábla, 2177. sor). Nem nulla esetén 1000000 (2182. sor). Utána az album-műveletek (2190., 2197. sor), majd minden elemre a `0x00484820` (2204-2205. sor).
- **A két ág különbsége (a 21.6 kérdése).** A csempe-ág mindkét táblát minden elemre teszteli. A kijelölt ág egy táblát, és csak az első elemet teszteli, az írást viszont minden elemre elvégzi. A `param_3` a csempe-ágban csak az első tesztben számít. A hívó (`0x0063f970`) értékét nem látjuk.
- **Helyesbítés a 20.3-hoz.** A 20.3 szerint a 0x00449090 csak akkor hívódik, ha a teszt nem nulla és a `param_3` nem nulla. Ez az első tesztre igaz. A második tesztnél a 0x00449090 a `param_3`-tól függetlenül hívódik. A 20.3 ezen a ponton pontatlan volt.
- **Állapot: N5 BLOKKOLT (marad).** A 21.6 csempe-ág kérdésére megvan a válasz a visszatérésre és az ágkülönbségre. NINCS MEG: a `param_3` hívói értéke, az 1001 jelentése, és a 0x00449090 belső feltétele.

### 22.5 N6: a 0x0068c030 fájlíró; a `[Contacts2]` a láncon át jön; a mentés kiváltója NINCS MEG

- **A 0x0068c030 (-3, 1012-1174. sor).** Megnyitja a `param_1[1]` útvonalú fájlt (1052-1060. sor; a megnyitó `DAT_00d69520`). Ír: a fejlécet (`*param_1`), majd a pároknak (`param_1[4][i]`, `param_1[6][i]`) mindkettőt, ha nem üres (1082-1137. sor), végül a 0x0068ac20 szövegét (1138-1154. sor). Ha a fájl nem volt rejtett, rejtetté teszi (1161-1165. sor).
- **Hibaág.** Üres fejlécnél nincs írás, és a megnyitott fogó nincs lezárva (1171-1172. sor).
- **Literálok.** A 0x0068c030-ban nincs `faces=` és nincs `[Contacts2]`. A szöveg a bemeneti tömbökből és a 0x0068ac20-ból jön.
- **`[Contacts2]`.** A 0x0068c030 hívja a 0x0068ac20-t (1138. sor, C-kód). Az index szerint a 0x0068ac20 hívja a 0x00586e20-t, amely a `[Contacts2]` sztringet tartalmazza (21.5). Az első él C-kód, a második csak index. Ha a 0x0068ac20 szövege a 0x00586e20 kimenete, a 0x0068c030 futásakor a `[Contacts2]` sor íródik. Ezt nem láttuk.
- **`faces=`.** NINCS MEG. A forrás lehet a 0x0068c030 hívójának tömbje, a 0x0068ac20 vagy a 0x00586e20.
- **Hívók.** A 0x0068c030-at közvetlenül a 0x006956d0 (0x00697557) és a 0x0069b240 (0x0069b9fc) hívja (-3, 1015-1016. sor). A 0x00687ec0 és a 0x007f7660 nem közvetlen hívók (ez direkt hívási negatív, a vtable-hívást nem zárja ki). A 0x007d55f0-on át (21.5) a másik `[Contacts2]`-láncban vannak.
- **A törlési út (0x007ba820, -1, 1045-1073. sor).** Közvetlen hívottjai között nincs a 0x0068c030, a 0x0068ac20, a 0x006956d0, a 0x0069b240, a 0x007d55f0 és a 0x00586e20. Hívója a 0x007b99a0 (1047. sor, `0x007b9b72`). A törlés utáni mentés tehát a 0x007b99a0-ban, vagy a közvetett hívottakban (0x00586a60, 0x007b5ad0; nincs olvasva) lehet.
- **Csonkítás.** A közvetlen hívottak között nincs csonkító hívás. A `DAT_00d69520` azonosítása dönti el, hogy egy rövidebb mentés után marad-e régi tartalom a fájl végén.
- **Állapot: BLOKKOLT (marad).**

### 22.6 Ghidra-kör kérések

- `Ghidra-kör kell: 0x0048bae0 - a 0x006b6a50 hívója (0x0048bcd5): mit ad kulcsnak (kép- vagy személyazonosító), és mit jelent a 0 visszatérés a 0x0048e5da és a 0x0048af60 számára? [blokkoló, N1]`
- `Ghidra-kör kell: 0x0048e590 - a 0x0048e5da belépési állapota (ESI, EBP, EBX, stack-argumentumok): honnan jön a param_9 detektor-objektum, van-e képméret, és hogyan kapcsolódik az in_stack_00000034 az in_stack_00000058 listához? [blokkoló, N3]`
- `Ghidra-kör kell: 0x0063f970 - a 0x00640340, a 0x00647270 (param_3) és a 0x006470d0 hívója: mit ír az igen-ág, és melyik tárolót? [blokkoló, N5]`
- `Ghidra-kör kell: 0x005edef0 - a 0x005fdc30 hívója (0x005ee072), EDI = 3 ág: mit ír a megerősítés után? (A 0x005c9930 és a 0x005c9b00 ugyanez a kérdés.) [blokkoló, N5]`
- `Ghidra-kör kell: 0x007b99a0 - a törlési kezelő (0x007ba820) hívója (0x007b9b72): a törlés után hívja-e a 0x0068c030-at, a 0x006956d0-t, a 0x0069b240-et vagy a 0x007d55f0-t? [blokkoló, N6]`
- `Ghidra-kör kell: 0x006956d0 - a 0x0068c030 hívója (0x00697557): mikor fut, és ír-e faces= és [Contacts2] sorokat? [blokkoló, N6]`
- `Ghidra-kör kell: 0x0069b240 - a 0x0068c030 másik hívója (0x0069b9fc): ugyanez a kérdés. [blokkoló, N6]`
- `Ghidra-kör kell: 0x0068ac20 - a 0x0068c030 farokszövege: hívja-e a 0x00586e20-t, és mit ad vissza? [blokkoló, N6]`
- `Ghidra-kör kell: 0x00586e20 - a [Contacts2] író: honnan veszi a sorokat, és ír-e faces= sort? [blokkoló, N6]`
- `Ghidra-kör kell: DAT_00d69520 - a 0x0068c030 megnyitója: melyik függvény, és csonkít-e a megnyitás? [blokkoló, N6]`
- `Ghidra-kör kell: 0x00449090 - a belső feltétele (a csempe-ág írója; a 20.3 nyitott pontja). [nem blokkoló, N5 csempe-ág]`

### 22.7 Bizonyítottsági fok és cáfoló kísérletek

**Megerősített (két út: C-kód és a korábbi diszasszembly vagy index):**
- (a) A 0x006b6a50 saját kódjában nincs név- vagy személy-összehasonlítás (C-kód, és a 21.3 diszasszemblálása).
- (b) A 960 (`0x3c0`) konstans nincs a 0x0048e5da és a 0x0048e1f0 kódjában (C-kód, és a 21.2 diszasszemblálása).
- (c) A 0x00640340 közvetlen kódja nem ír tárolót (C-kód, és a 21.4 index a közvetlen hívottakra). A vtable-hívásokat nem zárja ki.

**Feltételes (egy út, vagy egy út és index):**
- A 0x0048e5da kötegelési sorrendje (C-kód, -2 és -3).
- A csempe-ág két tesztje és az 1000000-ág (C-kód, -1). A 20.3 korábbi olvasata ugyanebből a Ghidra-kimenetből jött, ezért nem független.
- A kijelölt ág csak az első elemre teszteli a 0x0044a6b0-t (C-kód).
- A törlési kezelő nem hívja közvetlenül a mentést (a C-kód HÍVOTTAK-listája).
- A `[Contacts2]`-lánc: C-kód (0x0068c030 → 0x0068ac20) és index (0x0068ac20 → 0x00586e20).

**NINCS MEG:** a 0x0048e5da kulcsa és a két tömb kapcsolata; a bemeneti képméret; a személyszintű tároló-írás; a `param_3` hívói értéke; az 1001 jelentése; a `faces=` forrása; a mentés kiváltója; a fájl csonkítása.

**Cáfoló kísérletek:**
- (a) N1: azt állítottam, hogy a 0x006b6a50 nem név-alapú. A hívottjai (0x006b61b0, 0x006b6a30, 0x006b71b0, 0x0049ffc0, 0x0099dd50, 0x009bd220) nincsenek olvasva, ezért a negatív állítás csak a saját kódjára szól.
- (b) N3: azt állítottam, hogy a detektor bejegyzésenként hívódik, nem köteg-szinten. A 0x0048e1f0 detektor-hívása (-2, 78. sor) a 55-115. sor ciklusában van. Az állítás megáll.
- (c) N5: a kézenfekvő olvasatot (1000000 minden kijelölt elemre) ellenőriztem. A 2177. sor csak `*local_8`-t teszteli, ezért az olvasat nem áll meg.
- (d) N6: azt állítottam volna, hogy a törlés közvetlenül menti a fájlt. A 0x007ba820 közvetlen hívottjai között nincs mentés, ezért ez az állítás nem áll meg. A közvetett út nincs kizárva.

### 22.8 A 20. szakasz N-pontjainak új állapota

| Pont | Állapot | Mi változott |
|---|---|---|
| N1 | BLOKKOLT | A lookup (0x006b6a50) kódszinten nem név-alapú. A kizárás a 0x0048bae0-ban van, az nincs a körben. |
| N3 | BLOKKOLT | A 960 px nincs a 0x0048e5da és a 0x0048e1f0 kódjában. A bemeneti méret forrása a 0x0048e590 vagy a detektor-objektum lehet; ezek nincsenek olvasva. |
| N4 | LEZÁRVA | Változatlan. |
| N5 | BLOKKOLT | A csempe- és a kijelölt ág tesztjei pontosítva (22.4). A 0x00640340 és a 0x005fdc30 nem ír tárolót. A személyszintű írás nincs ebben a két függvényben; a hívóik nincsenek olvasva. |
| N6 | BLOKKOLT | A 0x0068c030 a fájlíró. A `[Contacts2]` az index szerint a 0x0068ac20 láncon át írható. A `faces=` forrása és a mentés kiváltója NINCS MEG. |
| N7 | BLOKKOLT | Változatlan. |
| N8 | BLOKKOLT | Változatlan. |

Nyitott kérdések: 0 nyílt · 1 lezárva · 6 blokkolt · 0 hatókörön kívül · 0 „csak nyitva”.

### 22.9 Fejlesztési következmény

Egyik N-pont sem zárult le, ezért nincs eltérés a mai viselkedéstől. A 21.8 „Fejlesztési lista: nincs” állítás érvényben marad.

### 22.10 Mérleg (4. kör)

Megerősített (két út): 3 tétel (22.7 a-c). Feltételes: 5 tétel (22.7). NINCS MEG: a 22.7 listája. A blokkolt tételek mindegyike Ghidra-kört igényel: 10 blokkoló és 1 nem blokkoló kérés (22.6). Tulajdonosi döntést egyik sem igényel.

## 23. #5184, ötödik kör: a hívók C-kódja (2026-10-17)

**Hatókör:** a 22.6 kérdései: N1, N3, N5 (kijelölt, csempe és személyszintű ág), N6, és a csempe-ág írója (0x00449090, a 22.6 nem blokkoló pontja). A tíz cím: `0x0048bae0`, `0x0048e590`, `0x0063f970`, `0x005edef0`, `0x007b99a0`, `0x006956d0`, `0x0069b240`, `0x0068ac20`, `0x00586e20`, `0x00449090`.

**Forrás:** `~/picasapy-agent/referencia/ghidra/2026-10-17-szemelykezeles-4.txt` (a továbbiakban `-4`, 4 228 sor, tíz `==== CÍM … ====` szakasz). Két helyen nyúltam vissza az `…szemelykezeles.txt` (`-1`) fájlhoz: a 0x00449090 hívási argumentumai a 0x00647270 C-jében (1650. és 1665. sor), és a 0x0048e590 hívója, a 0x0048ef20 (44., 142. és 654. sor).

**Utak:** a Ghidra-C (`-1`, `-2`, `-3`, `-4`) egy eszköz, ezért egy Ghidra-olvasat egy útnak számít. Független második út: a diszasszembly (`annot_disasm.py`) és a bináris-index (`xrefs`, `string_xrefs`, HÍVÓK és HÍVOTTAK). Jelölés: ugyanaz, mint a 20. szakaszban. `DATA` = a hívó egy függvénytáblából (parancs-elosztó) hívja.

### 23.1 N1: a kizárás értékalapú, nem név-alapú (0x0048bae0, 0x0048e590)

- **A 0x0048bae0 (-4, 1-134. sor).** A kulcs (`param_1`) táblaindex. A `this+0x28b8` tábla legalább kulcs + 0x4000 elemes lesz (40-110. sor). Ha a tábla bejegyzése nem nulla, azt adja vissza (34-36. sor). Különben a `0x006b6a50(kulcs, &local_c, 0)` lookup dönt (120. sor).
- **Visszatérés.** 0 csak akkor, ha a lookup 0-t ad ÉS `local_c != 0.0` (121-126. sor). Minden más eset 9 (131. sor). A -1 kulcs 9-et ad (30-31. sor), a túlméret vagy a foglalási hiba 4-et (49., 112. sor).
- **A visszaírt érték C szerint mindig 0.** A `local_8` csak egyszer kap értéket (118. sor), és nincs hívás, amely a címét kapja. Ezért a `*param_2` és a tábla bejegyzése 0 lesz (123-124. sor), és a cache-találat sosem következik be. Ez lehet valódi működés, de lehet a dekompiláló hibája is: a lookup kimenete a `local_c`, nem a `local_8`. A C ebből nem dönt.
- **A 0x0048e590 (-4, 135-431. sor)** minden kulcsra hívja a 0x0048bae0-t (293. sor). **0 esetén a kulcs bekerül a köteg-tömbbe** (294-308. sor, majd 325-345. sor). **Nem nulla esetén kimarad** (310-322. sor, majd a ciklus folytatódik).
- **A kulcs jelentése: NINCS MEG.** A C-ben csak táblaindex. Hogy kép- vagy személyazonosító-e, a hívókból nem derül ki.
- **Hívók (index).** A 0x0048bae0 három élt kap: 0x0048af60 (0048b18a), **0x0048b840 (0048ba44, a spec eddig nem nevezte meg)**, és a 0x0048e5da (0048e83e). A 0x0048e5da a 0x0048e590 törzsében van, az index ezt külön függvénynek nevezi.
- **Állapot: BLOKKOLT (marad).** A 0x0048bae0 és a 0x0048e590 C-jében nincs név- vagy személy-összehasonlítás. Ha a kizárásnak van név-feltétele, az a 0x006b6a50 rekordjában van. Azt nem olvastuk (a 21.6 kérése nyitott).

### 23.2 N3: a detektor-objektum `this+0x2e10`; a 960 px nincs a hívási láncban

- **A detektor-objektum (C).** A 0x0048e590 a 168-172. sorban tölti a `this+0x2e10` mezőt: ha a `this+0x2e14` bájt nulla, vagy a mező nulla, hívja a 0x0045f0c0-t. A 0x0048e1f0 kilencedik argumentuma ez a mező (`local_30`, 347-348. sor és 390-391. sor). Ez megadja a param_9 forrását (21.7). Ha a mező nulla, a függvény `0xffffffff`-et ad (173-174. sor).
- **A detektor osztálya és vtable-je: NINCS MEG.** A +0x2c slot célja ezen múlik.
- **A 0x0048e1f0 negyedik argumentuma (C).** A 0x0048e590 ötödik argumentuma, a `local_120` (-1, 142. és 654. sor). A 654. sor szerint ez a 0x0048ef20 float-argumentuma, nulla esetén a `this+0x3498` (0,85). A 142. sor szerint a kulcsok száma. Mindkettő küszöb vagy darabszám, nem képméret. Hogy melyik fut le a 879. sor előtt, a kódból ebben a körben nem dől el teljesen.
- **A köteg (C).** A kulcs a köteg 0x24 bájtos elemének 0. mezőjébe kerül (`*puVar7 = param_4[0][i]`, 276. sor). A detektor a köteget (`aiStack_24`) és a darabszám-mutatót kapja (`aiStack_24 + 2`), nem a teljes kulcslistát (347, 390. sor). A köteg határa `aiStack_24[4] >> 1` (346. és 390. sor). Az `aiStack_24[4]` mezőt a függvény nem állítja be, csak olvassa és maszkolja (414. sor). A határ forrása: NINCS MEG.
- **A 960 px.** A tíz C-ben nincs 960 (`0x3c0`). A 0x0048e590 `param_3` és `param_8` argumentuma mutató: `&local_118` (a lista címe) és `&local_d4`. A 0x0048ef20 harmadik argumentumából (`param_3`) egyelemű lista épülhet a `local_118`-ba (137. sor). Ez lista, nem méret. A 0x0048e590 argumentumai közül tehát egyik sem képméret.
- **Állapot: BLOKKOLT (marad).** Új: a param_9 forrása, a negyedik argumentum forrása és a köteg-logika. Hiányzik: a detektor bemeneti képmérete és a `this+0x2e10` osztálya.

### 23.3 N5 csempe-ág és az igen-ág (0x0063f970, 0x00449090)

- **A 0x0063f970 (-4, 434-1075. sor)** parancs-elosztó (HÍVÓK: `00ca16d0 DATA`). A parancs-sztringek alapján ágazik. A mellőzésnek két ága van:
  1. **Csempe-ág (745-754. sor).** Az `FUN_00986120(local_c, 7)` blokkban a 0x0049ff60 adja az indexet. Ha az index a listán belül van, ÉS `0x00640340() == 0`, hívja: `0x00647270(this, index, (char)this[0xdb])`. A `this[0xdb]` a `this+0x36c` bájtja, ez a 0x00647270 `param_3`-a. Az írója NINCS MEG.
  2. **Kijelölt arc (824-849. sor).** A `0x11`-es blokk a 0x004a0d40 objektum `+0xeac` alobjektumának listájából (`+0x500`) veszi az elemet. A `"ignore"` parancsra, és `0x00640340() == 0` esetén hívja a `0x006470d0(this)`-t (839-842. sor).
- **A 0x00640340 feltétele.** A 0x0063f970 csak 0-nál hajt végre. A 0 jelentését a 22.3 -3 olvasata adja (nincs párbeszéd, vagy a párbeszéd eredménye nulla). A FUN_009bab50 jelentése NINCS MEG, ezért az „igen" és a „nem" szó itt feltételes.
- **A 0x0063f970 nem hívja a személy-utat.** A HÍVOTTAK-listában nincs 0x005fdc30, 0x005c9b00 és 0x00449090, és a C-ben sincs ilyen hívás. A vtable-hívásokat az index nem látja.
- **A 0x00449090 (-4, 3789-4226. sor).** Paraméterei: `(this, kulcslista, param_3, param_4, param_5)`. A csempe-ágban (-1, 1650. és 1665. sor) mindkét hívás `param_4 = 0`, `param_5 = 1` értékkel fut. Az első hívás csak `param_3 != 0` esetén van (-1). Írásai:
  - (a) két kulcs-indexelt memóriabeli lista (`this+0x1c18`, `this+0x1c78`) elemét módosítja, törléssel vagy új értékkel (3852-4170. sor);
  - (b) mindig: `FUN_004d9aa0(this+0x68, kulcslista, 0, 2)` (4217. sor), vagyis album-művelet;
  - (c) `param_5 != 0` esetén minden kulcsra: `FUN_00484820(this, kulcs, 1, 0)` (4211-4215. sor). Ez az arc-író (20.3), vagyis az ini-írás;
  - (d) `param_4 != 0` esetén a kulcsok a `local_8` listába gyűlnek (4131. sor), és a végén a `]expeople:%d` kulcsú albumba íródnak (4218-4221. sor). A `%d` a `param_3`. **A csempe-ág ezt nem éri el**, mert `param_4 = 0`.
- **A 0x00449090 nem hívja a 0x0044a6b0-t.** Az ellenőrzés a hívóban van (0x00647270). A 0x00449090 belső írásai attól függetlenek.
- **Állapot (csempe).** A 0x00449090 belső feltétele most megvan a C-ben: az ini-írás `param_5`-tól, a személy-album `param_4`-től függ. A 20.3 és a 22.6 nyitott pontja ezzel lezárva. A 0x0044a6b0 visszatérésének 1001-je továbbra is NINCS MEG.

### 23.4 N5 személyszintű ág: a 0x005edef0 mappa-törlés; a jelölt a 0x005c9b00

- **A 0x005edef0 (-4, 1077-1225. sor) mappa-törlés,** nem személy-mellőzés. A hibaágban az `IDS_CANT_DELETE_FOLDER` sztring áll (1197. sor). A 0x005fdc30 hívás (1160. sor) C-argumentumai: darabszám (`aiStack_f8[3] >> 1`), név (`&stack0xfffffefc`), `1`, és három kimeneti puffer. Az EDI (fajta) a C-ben nem látszik, ezért a 22.3 és a 22.6 szerinti „EDI = 3" nincs igazolva.
- **Mit ír a megerősítés után.** A `FUN_005fd670` nem nulla visszatérése után: a `0x0097e4c0` hívás, a `_DAT_00d6793c` számláló, ha `cStack_d0` igaz, a `*(*(this+0x2bc)+0x48)` objektum vtable `+0x8c` slotja (1171-1172. sor), és a fő lépés: `0x00440af0(*(this+0x2bc), kulcs, aiStack_f8)` (1181. sor). Hogy a 0x00440af0 melyik tárolót írja, NINCS MEG.
- **Személy-jelölt: a 0x005c9b00.** A 0x005fdc30 hívói a 22.3 szerint: 0x005c9930 (005c9a42), 0x005c9b00 (005ca1e1) és 0x005edef0 (005ee072). A 15. szakasz szerint a fejlécsáv `ignore` parancsa a 0x005c9b00-t hívja (`ui, 1, 1, 0`). A 0x005c9b00 hívja a 0x00449090-t is (005c9ef6). Ha `param_4 = 1`-gyel hívja, a `]expeople:%d` album a személyszintű tároló jelöltje. A C-ben ez nincs megnézve: NINCS MEG.
- **A `]expeople` kulcs nem bizonyítja**, hogy ez a „Mellőzött emberek" album. A kulcsot a C adja, a szöveget nem.
- **Egy- és többszemélyes ág: NINCS MEG.** A 0x005fdc30 nincs a tíz címben.
- **Állapot: BLOKKOLT (marad).** Kizárva: a 0x0063f970 és a 0x005edef0 mint személy-út.

### 23.5 N6: a törlés nem ment közvetlenül; a mentési lánc részben C-ben; a [Contacts2] nincs igazolva

- **A 0x007b99a0 (-4, 1228-1600. sor)** parancs-elosztó (HÍVÓK: `00cb7b9c DATA`). A `delete` ág (1403-1406. sor) a 0x007ba820-t hívja, és **azonnal visszatér**. Nincs mentési hívás a törlés után. Az `ok` ág (1297-1308. sor) a 0x007bb660-ot, a 0x007baf50-t és a 0x008d2720-t hívja. Az `online` ág (1467-1534. sor) előbb a 0x007bb660-ot hívja, majd a `PersistBeforeSync` kérdés után a 0x007baf50-t.
- **A 0x006956d0 (-4, 1602-3182. sor).** A 0x0068c030 hívása a 3113-3114. sorban van. Csak akkor fut, ha a helyi állapot 2. Az állapot 1, ha `param_3[0x40] != 0` és a `param_3[0x15]` bájt nem nulla (1789-1791. sor). Az 1-es állapotú ciklusban a 0x0068ac80 hívódik, és az állapot 2 lesz (2711-2720. sor). A hívója a 0x006952e0 (00695609, index; C nincs).
- **A 0x0069b240 (-4, 3185-3632. sor).** Ugyanez a gépezet. Az állapot a `param_3[0x40]` bájtja a belépéskor (3282. sor). A 0x0068ac80 a 3529-3538. sorban, a 0x0068c030 a 3597-3598. sorban van. A hívója a 0x00692210 (006922f8, index; C nincs).
- **A 0x0068ac20 (-4, 3635-3665. sor).** A `while (iVar3 != 0)` ciklus a dekompilált C-ben nem fut: `iVar3` 0 marad (3656. sor), és a 0x0069ceb0 visszatérése nincs bekötve. A függvény a `this+0x2c` címet adja vissza (3663. sor). Az index szerint a 0x0068ac20 mégis hívja a 0x00586e20-t (0068ac5a). A hívás tehát a kódban van, de a feltétele NINCS MEG.
- **A 0x00586e20 (-4, 3667-3753. sor).** Csak akkor épít `Contacts2` sztringet, ha `param_4 != 0`, a 64 bites kulcs nem nulla, és nem `0xffffffff` (3747-3749. sor). A sztring ideiglenes, és azonnal felszabadul. Nincs írás, és nincs `faces=` sor a függvényben. HÍVÓK: 0x00484820 (00485118), 0x0068ac20 (0068ac5a), 0x007d55f0 (007d5ca6). Az arc-író, a 0x00484820 is hívja ezt (index-él).
- **`faces=` és [Contacts2].** A tíz függvényben nincs `faces=` literál. Forrása NINCS MEG. A `[Contacts2]` kiírásának módja NINCS MEG; a hívás megvan (index).
- **A mentés kiváltója: NINCS MEG.** A törlés után a 0x007b99a0 nem ment. A lehetséges mentési lánc: az `ok` vagy `online` ág (0x007bb660, 0x007baf50), majd 0x006952e0 vagy 0x00692210, majd 0x006956d0 vagy 0x0069b240, végül 0x0068c030. Hiányzik a 0x007baf50, a 0x007bb660, a 0x006952e0 és a 0x00692210 C-je.
- **Állapot: BLOKKOLT (marad).**

### 23.6 Ghidra-kör kérések (új)

- `Ghidra-kör kell: 0x006b6a50 - a rekord-olvasó: a kulcs (táblaindex) melyik rekordot olvassa, és a `local_c` float mit jelent? A 21.6 kérése változatlanul nyitott. [blokkoló, N1]`
- `Ghidra-kör kell: 0x0048b840 - a 0x0048bae0 harmadik hívója (0048ba44): neki is gyűjtés-e a 0 visszatérés, mint a 0x0048e590-ben? [blokkoló, N1]`
- `Ghidra-kör kell: 0x0045f0c0 - a this+0x2e10 objektum példányosítása: melyik osztály, és mi a vtable-je (a +0x2c slot célja)? [blokkoló, N3]`
- `Ghidra-kör kell: 0x00640340 és FUN_009bab50 - a 0 visszatérés "nincs párbeszéd" vagy "megerősítve"? A 0x0063f970 csak 0-nál hajt végre, ezért az igen-ág ettől függ. [blokkoló, N5]`
- `Ghidra-kör kell: 0x005c9b00 - a fejlécsáv "ignore" kezelője (0x005e1645): hívja-e a 0x00449090-t `param_4 = 1` értékkel, és mi az EDI a 0x005fdc30 hívásában? [blokkoló, N5]`
- `Ghidra-kör kell: 0x005c9930 - a 0x005fdc30 másik hívója: ugyanez a kérdés. [blokkoló, N5]`
- `Ghidra-kör kell: 0x007baf50 és 0x007bb660 - az "ok" és az "online" mentési lépése: hívja-e a 0x006952e0-t vagy a 0x00692210-t, és ír-e a lemezre? [blokkoló, N6]`
- `Ghidra-kör kell: 0x006952e0 - a 0x006956d0 hívója (00695609): mikor fut, és hívódik-e a törlés után? [blokkoló, N6]`
- `Ghidra-kör kell: 0x00692210 - a 0x0069b240 hívója (006922f8): ugyanez a kérdés. [blokkoló, N6]`
- `Ghidra-kör kell: 0x0068ac80 - az 1-es állapotú első lépés (0x006956d0: 2719. sor; 0x0069b240: 3537. sor): mit ír, és van-e benne `faces=` sor? [blokkoló, N6]`
- `Ghidra-kör kell: 0x0069ceb0 - a 0x0068ac20 listajárója: mit ad vissza, és ezért fut-e a ciklus (3659. sor)? [blokkoló, N6]`
- `Ghidra-kör kell: 0x00440af0 - a mappa-törlés (0x005edef0) fő lépése: melyik tárolót írja? [nem blokkoló, N5 mappa-ág]`

A 22.6 többi kérése változatlan. A 0x0068c030 (`DAT_00d69520` megnyitó) a -3 fájlban van, és ebben a körben nem olvastam.

### 23.7 Bizonyítottsági fok és cáfoló kísérletek

**Megerősített (C-kód és független második út: diszasszembly vagy index):**
- (a) A 0x0063f970 csempe- és kijelölt-ága a `0x00640340() == 0` feltételhez van kötve (C -4; index: a 0x0063f970 élei a 0x00640340, a 0x00647270 és a 0x006470d0 felé).
- (b) A 0x007b99a0 `delete` ága a 0x007ba820-t hívja, mentési hívás nélkül (C -4; index: a 0x007b99a0 HÍVOTTAK-listájában a 0x007ba820 van, a 0x0068c030 nincs).
- (c) A 0x0068c030 két hívója a 0x006956d0 és a 0x0069b240 (C -4; index: mindkét HÍVOTTAK-lista tartalmazza).
- (d) A 0x00449090 csempe-hívásaiban `param_5 = 1` van, és az ini-író (0x00484820) hívása megvan (C -1 és -4; index: a 0x00449090 HÍVOTTAK-listájában a 0x00484820 szerepel).
- (e) A 960 nincs a 0x0048e590 C-jében (C -4), és nincs a 0x0048e1f0 diszasszembly-jében (21.2).

**Feltételes (egy út, vagy több Ghidra-C):**
- N1: a kizárás értékalapú (C -4; a 22.1 -3 olvasata ugyanaz az eszköz).
- N3: a param_9 a `this+0x2e10` (C -4 és a 21.7 -2 olvasata).
- N5 csempe: a `param_4 = 0` a csempe-hívásokban (C -1 és -4).
- N5 személy: a 0x0063f970 nem hívja a személy-utat (C; az index csak a direkt éleket látja).
- N5 mappa: a 0x005edef0 mappa-törlés (az `IDS_CANT_DELETE_FOLDER` sztring; függvénynév nincs).
- N6: a 0x006956d0 és a 0x0069b240 állapotgépe (C).
- N6: a 0x0068ac20 hívás megvan az indexben, de a ciklusa a C-ben nem fut (C-ellentmondás; a dekompiláló hibája lehet).

**NINCS MEG:** a kulcs jelentése (N1); a 0x006b6a50 rekord-tartalma; a bemeneti képméret forrása (N3); a 0x0045f0c0 osztálya és vtable-je (N3); a 0x00640340 és a FUN_009bab50 0-jának jelentése (N5); a személyszintű tároló és az egy- és többszemélyes ág (N5); az EDI a 0x005edef0 hívásában (N5); a 0x0044a6b0 1001-je (N5); a `faces=` sor forrása (N6); a mentés kiváltója (N6); a [Contacts2] tényleges kiírása (N6).

**Cáfoló kísérletek:**
- (a) N1: kerestem név- vagy személy-összehasonlítást a 0x0048bae0 és a 0x0048e590 C-jében: nincs. A negatív állítás e két függvényre szól, a 0x006b6a50-ra nem.
- (b) N6: a 22.5 feltevése, hogy a törlés a 0x007b99a0-ban menthet, a `delete` ágra nem áll: az a 0x007ba820 után azonnal visszatér.
- (c) N5 csempe: a 0x00449090-ban nincs 0x0044a6b0 hívás. A 0x0044a6b0 teszt tehát a hívóban gátol, a 0x00449090 belső írásait nem.
- (d) N5 személy: a 0x0063f970 nem hívja a 0x005fdc30-at, a 0x005c9b00-t és a 0x00449090-t sem. A személy-út más belépésből indul.
- (e) N3: a 960 nincs a C-ben, és az öt argumentum egyike sem méret. Ettől még a méret lehet a 0x0048e1f0 belsejében vagy a detektor-objektumban; ezt nem zártam ki.

**Módszertani megjegyzés.** A 0x0048e590 HÍVOTTAK-listája valószínűleg csak az első blokkot fedi: a HÍVÓK-lista szerint a 0x0048bae0 hívását az index a 0x0048e5da alá sorolja. A 0x0048e590 többi hívását (0x0048b840, 0x0048e1f0) ezért a C-ből olvastam, nem a listából.

### 23.8 A 20. szakasz N-pontjainak új állapota

| Pont | Állapot | Mi változott |
|---|---|---|
| N1 | BLOKKOLT | A kizárás a 0x0048bae0-ban és a 0x0048e590-ben értékalapú (0 = gyűjtés, nem nulla = kimarad). Név-feltétel a két függvényben nincs. A rekord-tartalom a 0x006b6a50-ban van. |
| N3 | BLOKKOLT | A detektor-objektum a `this+0x2e10`. A 960 nincs a hívási láncban. A bemeneti méret forrása NINCS MEG. |
| N4 | LEZÁRVA | Változatlan. |
| N5 | BLOKKOLT | Csempe: a 0x00449090 belső feltétele megvan; az ini-írás `param_5 = 1`-gyel fut. Személy: a 0x0063f970 és a 0x005edef0 nem a személy-út; a jelölt a 0x005c9b00. |
| N6 | BLOKKOLT | A törlés (a 0x007b99a0 `delete` ága) nem ment közvetlenül. A mentési lánc részben C-ben van. A [Contacts2] és a `faces=` forrása nincs igazolva. |
| N7 | BLOKKOLT | Változatlan. |
| N8 | BLOKKOLT | Változatlan. |

Nyitott kérdések: 0 nyílt · 1 lezárva · 6 blokkolt · 0 hatókörön kívül · 0 „csak nyitva".

### 23.9 Fejlesztési következmény

Egyik N-pont sem zárult le, ezért nincs bizonyított eltérés. A `src/picasapy/app/face_scan_controller.py:470-474` név-alapú kihagyása (N1) nyitott: a 0x0048bae0 C-jében nincs név-összehasonlítás, de a kizárás tartalmát a 0x006b6a50 adja. A 21.8 „Fejlesztési lista: nincs" állítás érvényben marad.

### 23.10 Mérleg (5. kör)

Megerősített: 5 tétel (23.7 a-e). Feltételes: 7 tétel (23.7). NINCS MEG: a 23.7 listája. Blokkoló kérés: 11 (23.6), nem blokkoló: 1 (23.6). Tulajdonosi döntést egyik sem igényel.

## 24. #5184, hatodik kör (2026-10-17)

**Hatókör:** a 23.6 kérdései. A tíz cím a `-5` fájlban van. A 23.6 két címe (0x00640340, 0x006b6a50) a `-3` fájlban van (22. szakasz). A többi címet (0x007bb660, 0x008d2720 és társai) a dumpok nem tartalmazzák.

**Forrás:** `~/picasapy-agent/referencia/ghidra/2026-10-17-szemelykezeles-5.txt` (a továbbiakban `-5`, 2 389 sor). Visszaolvastam a `2026-10-17-szemelykezeles-4.txt` (`-4`) 0x00449090 végét (4206-4221. sor) és a 0x0048e590 két hívását (178. és 293. sor), a `…-3.txt` (`-3`) DoNotConfirmPeopleRemove ágát (692. sor), és az `…szemelykezeles.txt` (`-1`) két 0x00449090-hívását (1650. és 1665. sor).

**Utak:** a Ghidra-C egy út. A második út a bináris-index: a `-5` fejlécében a HÍVÓK és HÍVOTTAK listák. A diszasszemblálást ebben a körben nem néztem.

**Jelölés:** ugyanaz, mint a 20. szakaszban. `idx` = a kiválasztott elem indexe, `lista` = a kulcslista.

### 24.1 N1: a kizárás nem név-alapú a vizsgált függvényekben; a döntő lookup nincs eldöntve

- **0x0048b840 (`-5`, 181-338. sor), a kötegelt változat.** A 0x0048bae0-t minden elemre hívja (319. sor), de a visszatérését nem olvassa. A 0x0048bae0 a kimeneti tömb (a hívó EDI-jében érkezik) megfelelő elemébe ír; a 23.1 szerint ez az érték mindig 0. A saját visszatérése 0 vagy 0xf4242, a `*param_3` jelzőtől függően (320. és 336. sor). Nem nulla jelzőnél a ciklus megszakad.
- **Válasz a 23.6 kérdésére: nem.** A 0x0048b840 nem gyűjt. A 0-ra gyűjtés a 0x0048e590 saját ciklusában van (`-4`, 293-308. sor, a 23.1 szerint). A 0x0048e590 mindkét hívást tartalmazza (178. és 293. sor). Hogy melyik fut melyik esetben, ebben a körben nem néztem meg.
- **0x006b6a50 (`-3`, a 22.1 szerint):** indexszel olvas rekordot, és nincs benne név-összehasonlítás. A `local_c` float jelentése NINCS MEG. A 13 hívója nincs olvasva (21.6, nyitott).
- **Állapot (N1): BLOKKOLT.** A 24.7 szerint a következő Ghidra-kör csak hívókat adna, ezért itt a felvétel dönt.

### 24.2 N3: a detektor-objektum létrejön; az osztálya és a vtable-je NINCS MEG

- **0x0045f0c0 (`-5`, 45-179. sor).** Ha a `this+0x2e10` nulla (115. sor), lefoglal 0xb0 bájtot (116. sor), és a `FUN_006ccbb0()` adja az objektumot (121. sor). A `plugins` útvonalat a `FUN_00408390("plugins")` állítja be (123. sor). Az objektum vtable-jének 0. slotja két kimeneti pufferrel fut (144. sor). A `Preferences\FRTemplateChecking` kulcsot olvassa (149. sor). Ha az init 0-t adott, a vtable `+0x34` slotját hívja (156. sor). Végül a `this+0x2e10` mezőbe teszi az objektumot, a `this+0x2e14` mezőt 1-re állítja (158-159. sor).
- **Válasz a 23.6 kérdésére:** a példányosítás a `FUN_0097c5d0(0xb0)` és a `FUN_006ccbb0()`. Az osztály és a vtable NINCS MEG; a vtable a konstruktorban van. A `+0x2c` slot ebben a függvényben nem hívódik. A `this+0x3498` nem íródik itt (21.7). A `red.cfg` név nincs a C-ben.
- **Állapot (N3): BLOKKOLT.** Az osztály és a vtable a `FUN_006ccbb0`-ban, illetve onnan hívott kódban van.

### 24.3 N5: a személy-tároló; a 0x00449090 `param_4 = 1` hívása megvan; a predikátum NINCS MEG

- **0x005c9b00 (`-5`, 431-1467. sor), a fejlécsáv-mellőzés.** A 23.4 szerint az `ignore` parancs hívja. A függvény három ágat tartalmaz:
  1. **Üres kijelölés (1246-1253. sor).** Ha a kijelölési lista (`this+0xea8`) `+0x330` mezője üres, és a `FUN_004aca00(idx)` nulla, a `+0xec` slot hívódik (`this+700+0x48` objektum, `idx`). Ebben az ágban nincs 0x00449090- és nincs 0x005fdc30-hívás. A `+0xec` slot célja NINCS MEG. A `+0x330` üresség-jelzése a `>> 1` és `& 1` minta alapján következtetés, nem igazolt. Az 1246. sor feltétele szerint a `uStack_1f74` ebben az ágban 0 marad.
  2. **Nem üres kijelölés (1254-1333. sor).** Ha a `param_3 != 0`, először a `0x005c9930`-at hívja, `param_5 = 1` és `param_4 = idx` értékkel (1263. sor). Utána a `FUN_005fd670` megerősítést kér (1264. sor). Ha nem erősíti meg, az ág kilép (1265-1270. sor).
  3. **Tároló-ág (1284-1315. sor).** Ez a `param_3`-tól független, a nem üres ág végén fut. Ha a `FUN_00448c90(this+700)` nem nulla, **0x00449090(this+700, lista, idx, 1, 1)** fut (1314. sor). Ha nulla, és a `FUN_00448a10(this+700, idx, 0)` nem nulla, a `FUN_004d9aa0(this+0x68, lista, 0, 2)` album-művelet fut (1308. sor). Ha egyik sem, ezen az ágon nincs külön írás.
- **A 0x00449090 `param_4 = 1` hívása** (C: `-5` 1314. sor; index: a 0x005c9b00 HÍVOTTAK-listájában a 0x00449090 szerepel). A `-4` 0x00449090 végén (4211-4221. sor) két írás van:
  - `param_5 != 0` esetén minden kulcsra `FUN_00484820(this, kulcs, 1, 0)`, vagyis az arc-író (az ini-írás);
  - `param_4 != 0` és a gyűjtött lista nem üres esetén a gyűjtött kulcsok a `]expeople:%d` kulcsú albumba íródnak. A `%d` a `param_3`, vagyis az index. A gyűjtés feltétele a ciklusban van (3852-4170. sor), ezt nem néztem végig.
- **Más `param_4 = 1` hívás a dumpokban nincs.** A két csempe-hívás (`-1`, 1650. és 1665. sor) `uVar3` értéke 0, tehát `param_4 = 0`.
- **Egy- és többszemélyes ág.** A C szerint a személy-tároló-írást nem a darabszám, hanem a `FUN_00448c90` predikátum dönti el. Egy kijelölt és több kijelölt személy ugyanazon az ágon fut, ha a kijelölés nem üres. A darabszám a 0x005fdc30 szövegét választja (névtelen hívásnál, 22.3). A 653. sor darabszám-argumentuma (`uStack_1f74 >> 1`) a C-ben 0-ból jön, ezért ebből a többes-ágra nem következtetek.
- **0x005c9930 (`-5`, 340-430. sor), `param_5 = 1` esetén.** Először a `FUN_00448c90` és a `FUN_00448a10` predikátumot nézi (370-381. sor). Ha az egyik nem nulla, nem ír (383. sor). Ha mindkettő nulla, a `this+700+0x48` objektum `+0x9c` slotját (`param_4`, rekord) és a `this+0x2c0+0x4c` objektum `+4` slotját hívja (391-395. sor). A 0x00484820 közvetlenül nincs benne; a vtable-célok NINCS MEG. A 0x005fdc30 hívása (405. sor) hat argumentummal fut; az EDI nincs a C-ben.
- **0x00440af0 (`-5`, 1-44. sor), a mappa-törlés fő lépése (a 23.4 kérdése).** A `param_1+0x48` objektum `+0x2c` slotjától a kulcs útvonalát kéri (28. sor), beolvassa a `Preferences\ShowHidden` kulcsot (34. sor), majd a `FUN_004019b0` és a `FUN_006ca8c0` hívásait (36-37. sor). A C-ben nincs ini- vagy album-írás. A két hívott függvény célja NINCS MEG.
- **Állapot (N5):**
  - kijelölt arc (0x006470d0): változatlan (20.3);
  - csempe (0x00647270): változatlan (23.7);
  - **személy: BLOKKOLT.** A tároló (a `]expeople:%d` album és az ini-írás) a C-ben megvan, de a 0x00448c90 jelentése nincs;
  - **egyszemélyes ág: BLOKKOLT.** A `+0xec` slot célja nincs meg;
  - az EDI a 0x005fdc30 hívásában disasm-kérdés, nem Ghidra.

### 24.4 N5: a megerősítés 0-ja (0x00640340)

- **0x00640340 (`-3`, a 22.3 szerint).** Ha a `Preferences\DoNotConfirmPeopleRemove` igaz (692. sor), párbeszéd nélkül 0-t ad. Különben párbeszédet épít. A `FUN_009bab50` eredményétől függ: nem nulla eredménynél 0xf4242, nulla eredménynél a `FUN_009baae0` és a `FUN_00401900` után 0.
- **Válasz a 23.6 kérdésére:** a 0 jelentése: vagy nincs kérdés, vagy a párbeszéd nem szakította meg a műveletet. A 0xf4242 megszakítási kód a dumpokban (a 0x0048b840 és a 0x00692210 is ezt adja megszakításkor). A gomb-sorrend (melyik gomb a „igen”) és a `FUN_009bab50` belseje NINCS MEG.
- **Állapot:** a 0x0063f970 csak 0-nál hajt végre (23.3). Az igen-ág feltétele tehát a „nem szakította meg”. Hogy ez az „igen” gomb, azt a `FUN_009bab50` dönti el.

### 24.5 N6: a mentési lánc; a 0x006952e0 → 0x006956d0 kapcsolat megerősített; a trigger NINCS MEG

- **0x007baf50 (`-5`, 2154-2387. sor), az ok és az online ág közös része.** A 0x00584010-et hívja a `this+0xd4+0x2c5c` gyűjteménnyel (2346. sor), majd a kijelölt elemeket a 0x005849d0-val törli (2365. sor). Hiba esetén a `ContactManagerDlg::UpdateFailed` üzenetet mutatja (2349-2356. sor). **Nem hív** 0x006952e0-t, 0x00692210-t és 0x0068c030-t (HÍVOTTAK-lista). A lemezre írás a 0x00584010-ban lehet; ez NINCS MEG. Az `iStack_28` a C-ben nincs beállítva (2194. és 2346. sor), ezért a 0x00584010 második argumentumáról nem döntök.
- **0x007bb660:** NINCS MEG a dumpokban. Az ok és az online ág is ezt hívja a 0x007baf50 előtt (23.5).
- **0x006952e0 (`-5`, 1876-2085. sor), a mentés-sor.** A bemeneti elemet a `+0x1b0` tömbbe fűzi (`+0x1b4` számlálóval). Ha a `+0x47c` nem nulla, és az elem `+0x54` bájtja nulla, a 0x0068c5c0-t hívja (2042-2043. sor). Ezután a `+0x8c` táblában törli az adott indexű bejegyzést, és **mindig** hívja a 0x006956d0-t (2055. sor; a hívási cím 00695609). Ez válasz a 23.6 kérdésére: a 0x006956d0 hívója a 0x006952e0.
  - **Hívója: 0x006980a0 (006980c3), csak index.** A 0x006980a0 C-je nincs a körben. A „mikor fut" és a „hívódik-e törlés után" kérdés ezen múlik.
- **0x00692210 (`-5`, 1801-1875. sor), a sor-futtató.** A `+0x1b0` tömb minden elemére: megszakítás-ellenőrzés (a `+8` objektum `+4` slotja), majd 0x0068c5c0 (1838. sor), opcionálisan két segédhívás a `+0x438` mezőre, végül 0x0069b240 (1865. sor). Megszakításkor 0xf4242-t ad (1834. sor).
  - **Hívói: két DATA-hivatkozás (00ca7cc0, 00ca7df8).** Egy parancs-táblából indul. A tábla tulajdonosa NINCS MEG, ezért a „mikor fut" kérdés nyitott.
- **0x0068ac80 (`-5`, 1468-1800. sor), a rekord szövege.** A `name=%s`, a `description=%s` (ha nem üres), a `location=%s` (ha nem üres), a `category=%s` és a `date=%f` sorokat írja (1614-1624. sor). Utána a `FUN_006a3b80` (a `this+0x988` alobjektumon) listájának `%s=%s` sorait írja (1627-1636. sor). **A `faces=` nincs literálként a függvényben.** A kulcs a listából jöhet; a lista forrása NINCS MEG.
- **0x0069ceb0 (`-5`, 2086-2153. sor), a listajáró.** Nem hív semmit és nem ír. Visszatérése 1, ha van következő elem (az `in_EAX[2]` be van állítva), 0, ha vége. A 0x0068ac20 ciklusában (`-4`, 3659. sor) a visszatérést a C nem köti be, ezért a ciklus futása C-ből nem dönthető el.
- **`faces=` és `[Contacts2]` összesítve.** A `faces=` szöveg egyik dumpban sincs literálként. A `[Contacts2]` csak a 0x00586e20 `FUN_00985ff0("Contacts2")` hívásában van (`-4`, 3748. sor), és a 0x00586e20 csak `param_4 != 0` esetén épít sztringet (23.5).
- **Állapot (N6): BLOKKOLT.** Megerősített: a törlési út (0x007ba820 és 0x007baf50) közvetlenül nem ment, és a 0x006952e0 → 0x006956d0 → 0x0068c030 lánc. NINCS MEG: a mentés kiváltója (0x006980a0 és a DATA-tábla), a 0x007bb660 és a `faces=` forrása.

### 24.6 Ghidra-kör kérések (új)

- `Ghidra-kör kell: 0x007bb660 - az ok és az online ág közös lépése (a 0x007baf50 előtt): hívja-e a 0x006952e0-t vagy a 0x00692210-t, és ír-e lemezre? [blokkoló, N6]`
- `Ghidra-kör kell: 0x008d2720 - az ok ág 0x007baf50 utáni hívása: mentés-e (0x006952e0, 0x00692210)? [blokkoló, N6]`
- `Ghidra-kör kell: 0x00584010 - a 0x007baf50 gyűjtemény-frissítője: ír-e fájlba, és mit csinál a this+0xd4+0x2c5c gyűjteménnyel? [blokkoló, N6]`
- `Ghidra-kör kell: 0x006a3b80 - a 0x0068ac80 kulcs=érték listájának forrása (this+0x988): honnan jön a faces= kulcs? [blokkoló, N6]`
- `Ghidra-kör kell: 0x00448c90 - a személy-predikátum (0x005c9b00 1284. sor, 0x005c9930 370. sor): mit olvas, és mit jelent a nem nulla érték? [blokkoló, N5]`
- `Ghidra-kör kell: 0x009bab50 - a 0x00640340 párbeszéd-eredménye: a nulla az igen vagy a nem gomb? [blokkoló, N5]`
- `Ghidra-kör kell: 0x006ccbb0 - a this+0x2e10 detektor-objektum konstruktora: melyik osztály, és melyik vtable-t írja az első mezőbe? [blokkoló, N3]`
- `Ghidra-kör kell: 0x006ca8c0 - a 0x00440af0 ShowHidden-ágának hívott függvénye: mit csinál a kimeneti pufferekkel? [nem blokkoló, N5 mappa-ág]`

Diszasszemblálás kell (nem Ghidra): a 0x0068ac20 ciklus-tesztje (0068ac41-0068ac62 között), és a 0x005fdc30 hívások EDI-je (`-5` 405. és 653. sor). Ezeket az `annot_disasm.py` dönti el, nem a Ghidra.

### 24.7 Következtetés: a felvétel dönt, nem a következő Ghidra-kör

- **N1.** A következő kör a 0x006b6a50 13 hívóját kérné. Ezek a lookup hívói, nem a kizárás mechanizmusa, ezért ebből nem lesz eldöntés. **Döntő felvétel:** ugyanabban a mappában két fotó. A) egy arc, név nélkül. B) egy arc, amelynek nevet adunk. Javaslat-futás (felismerés) a név adása előtt és után. Ha a B fotó a jelöltek között marad, a név-alapú kihagyásunk (`src/picasapy/app/face_scan_controller.py:470-474`) eltér az eredetitől. Ha kiesik, a kizárás névhez vagy korábbi feldolgozáshoz köthető. A kettőt a B2 futás választja szét: ugyanaz a fotó, név nélkül, de már egyszer feldolgozva.
- **N3 (960 px).** Ha a 0x006ccbb0 is megvan, a méretezés a detektor belsejében lehet, egy újabb hívási szinten. **Döntő felvétel:** ugyanaz az egy arcos kép 640, 800, 960, 1280 és 1600 px hosszú élre méretezve, az arc pixelmérete állandó. Ha a detektor 960 px-re méretez, a 960 fölötti képeken a találati arány csökken, a 960 alattiakon nem változik. Ez a jóslat a 960 px mellett szól, ha teljesül, és ellene, ha nem.
- **N6 (a trigger).** A következő kör a 0x006980a0-t és a DATA-tábla tulajdonosát kérné. Ezek a parancs-szint hívói, nem a mentés-lépés. **Döntő felvétel:** egy megnevezett személy törlése, majd a `.picasa.ini` és a `[Contacts2]` tartalmának összevetése két időpontban: a törlés után azonnal, és a Picasa bezárása után. Ha a `faces=` sor azonnal változik, a mentés a törlési ágból indul (ezt a 24.6 Ghidra-kérések ellenőrzik). Ha csak bezáráskor, a mentés a parancs-szinten van.
- **N5 (személy).** Felvételt most nem kérek. A 0x00448c90 egyetlen predikátum, a 24.6 kérése elég lehet. Ha a predikátum nem egyszerű, a felvétel: egy megnevezett személy és egy név nélküli arc mellőzése, majd a `.picasa.ini` `faces=` sorainak és a Picasa albumlistájának összevetése.
- **Tulajdonosi döntés:** a felvétel a Colab-végrehajtón fut. A viselkedés-típusú feladat a tulajdonos `jovahagyva` címkéjét kéri. Ezt a tulajdonos dönti el.

### 24.8 Bizonyítottsági fok és cáfoló kísérletek

**Megerősített (két út: C és index):**
- (a) A 0x005c9b00 hívja a 0x00449090-t (C: 1314. sor; index: HÍVOTTAK-lista).
- (b) A 0x006952e0 hívja a 0x006956d0-t (C: 2055. sor; index: 00695609).
- (c) A 0x007baf50 nem hív 0x006952e0-t, 0x00692210-t és 0x0068c030-t (C és index: HÍVOTTAK-lista; csak a közvetlen hívásokra).
- (d) A 0x0069ceb0 nem hív és nem ír (C: nincs hívás; index: HÍVOTTAK = 0).

**Feltételes (egy út, vagy C-keresés):**
- (e) A 0x0048b840 nem gyűjt (C: 319. sor).
- (f) A 0x005c9b00 `param_4 = 1` értéke (C); a dumpokban más `param_4 = 1` hívás nincs.
- (g) A 0x00448c90 személy-predikátum (a hívás-helyből következtetett szerep; a belseje nincs).
- (h) A 0x0068ac20 ciklusa (C-ellentmondás: a visszatérés nincs bekötve).
- (i) A 0x00440af0 nem ír ini-t és albumot (C; a két hívott függvény nincs a körben).
- (j) A `faces=` nincs literálként (C-keresés a dumpokban).

**NINCS MEG:**
- a 0x006b6a50 kulcsának jelentése és a `local_c` float (N1);
- a 0x0045f0c0 osztálya és vtable-je (N3);
- a 0x00448c90, a 0x00448a10 és a 0x004aca00 jelentése (N5);
- a `+0xec` slot célja (N5);
- a 0x005fdc30 EDI-je (N5);
- a `FUN_009bab50` gomb-sorrendje (N5);
- a 0x007bb660 és a 0x008d2720 (N6);
- a 0x006980a0 és a DATA-tábla (N6);
- a `faces=` forrása és a `[Contacts2]` kiírásának módja (N6);
- a 0x0068ac20 ciklusa (N6).

**Cáfoló kísérletek:**
- (a) N5 személy: a 0x00449090 `param_4 = 1` hívását kerestem a dumpokban. Egy van (0x005c9b00). Ez a dumpokra szól, nem a teljes binárisra.
- (b) N5 személy: ha a 0x00448c90 személyre nulla, a 0x00449090 nem fut. Ezt a predikátum belseje nélkül nem zárom ki.
- (c) N6: a törlési út (0x007ba820, 0x007baf50) nem hív mentést közvetlenül. Ez csak a közvetlen hívásokra áll. A 0x007bb660 és a 0x008d2720 nincs olvasva.
- (d) N1: a 0x0048b840 nem gyűjt. Ez a negatív állítás a 0x0048b840 kódjára szól; a gyűjtő-ág a 0x0048e590-ben van.
- (e) N6 `faces=`: a dumpokban nincs literál. A lista forrása (0x006a3b80) nincs olvasva, ezért a sor létezését ez nem zárja ki.

### 24.9 A 20. szakasz N-pontjainak új állapota

| Pont | Állapot | Mi változott |
|---|---|---|
| N1 | BLOKKOLT | A 0x0048b840 nem gyűjt. A kizárás a 0x0048e590 0-ágán és a döntő lookup rekordján múlik. Következő lépés: felvétel (24.7). |
| N3 | BLOKKOLT | A 0x0045f0c0 létrehozza a detektor-objektumot (0xb0 bájt, a `FUN_006ccbb0`). Osztály, vtable és 960 px: NINCS MEG. |
| N4 | LEZÁRVA | Változatlan. |
| N5 | BLOKKOLT | A személy-ágban a 0x00449090 `param_4 = 1` hívása (0x005c9b00, 1314. sor) a `]expeople:%d` albumba és az ini-írásba megy. A 0x00448c90 predikátum jelentése NINCS MEG. Az egyszemélyes ág `+0xec` slotja NINCS MEG. A 0x00640340 igen-ága a 0 jelentésétől függ (24.4). |
| N6 | BLOKKOLT | A mentési lánc megerősített: 0x006952e0 → 0x006956d0 → 0x0068c030. A 0x007baf50 nem ment. A mentés kiváltója (0x006980a0, DATA-tábla) és a `faces=` forrása NINCS MEG. |
| N7 | BLOKKOLT | Változatlan (ez a kör nem érintette). |
| N8 | BLOKKOLT | Változatlan. |

Nyitott kérdések: 0 nyílt · 1 lezárva · 6 blokkolt · 0 hatókörön kívül · 0 „csak nyitva".

### 24.10 Fejlesztési következmény

Nincs lezárt N-pont, ezért nincs bizonyított eltérés. A 21.8 és a 23.9 „fejlesztési lista: nincs" állítása érvényben marad. Az N1 kérdése (`face_scan_controller.py:470-474`) nyitott; a 24.7 felvétele dönti el.

### 24.11 Mérleg (6. kör)

Megerősített: 4 tétel (24.8 a-d). Feltételes: 6 tétel (24.8 e-j). NINCS MEG: 10 csoport (24.8). Blokkoló Ghidra-kérés: 7 (24.6), nem blokkoló: 1 (24.6). Felvétel dönt: N1, N3 (960 px) és N6 (trigger); N5 a 0x00448c90 után. A felvétel tulajdonosi jóváhagyást kér.

## 25. #5184, hetedik kör (2026-10-17)

**Hatókör:** a 24.6 nyolc címe (`0x007bb660`, `0x008d2720`, `0x00584010`, `0x006a3b80`, `0x00448c90`, `0x009bab50`, `0x006ccbb0`, `0x006ca8c0`). Mind a nyolcra van válasz. Az N1, N3, N5 és N6 pontokra következő döntés a 25.10 szakaszban van.

**Forrás:** `referencia/ghidra/2026-10-17-szemelykezeles-6.txt` (a továbbiakban `-6`, 1 117 sor, nyolc `==== CÍM … ====` szakasz). Visszaolvastam: `referencia/ghidra/2026-10-17-szemelykezeles-5.txt` (`-5`) 2211., 2336., 2346., 2383-2384. sora (a 0x007baf50 hívási argumentumai), és `referencia/binary-index/rtti.csv` (a `CNevenVision::vftable` táblája, 961. sor). A red.cfg betöltéséhez a `referencia/research-2026-08-13-red-pipeline.md` 44-49. sorát olvastam. A 0x00640340 olvasata a `-3` dumpból jön (22.3).

**Jelölés:** ugyanaz, mint a 20. szakaszban. `index` = a bináris-index fejléce (HÍVÓK, HÍVOTTAK) vagy a `rtti.csv`. `C` = a `-6` dekompilált kódja. `egy út` = egy eszköz (Ghidra) egy kimenete.

### 25.1 N6: 0x007bb660, az ok és az online ág közös lépése

- **Mit csinál (C, 36-322. sor).** Csak a `param_1+0x158` mező 2 vagy 3 értékénél fut (80-82. sor). A `this+0xd4+0x2c5c` gyűjteményt használja (199. sor). A 3-as ágban a 0x00585ad0-val duplikáció-keresést futtat (199-202. sor). Találatnál a 0x0058ff00-t és a 0x007b7f00-t hívja (206-208. sor), és az üzenetek közül egyet mutat (`DupContact`, `DupNameMsg`, `DupEmailMsg`, `DupFoundTitle`). Utána a 0x009bab50 párbeszédet futtat (285. sor).
- **Hívja-e a 0x006952e0-t vagy a 0x00692210-t?** **Nem.** Egyik sincs a C-törzsben, és a HÍVOTTAK-listában (index) sincs.
- **Ír-e lemezre?** Közvetlenül nem. A C-ben és a HÍVOTTAK-listában nincs fájl-API. A 0x00585ad0, a 0x0058ff00 és a 0x007b7f00 belsejét nem olvastuk: **NINCS MEG**, hogy írnak-e.

### 25.2 N6: 0x008d2720, az ok ágban a 0x007baf50 után

- **Mit csinál (C, 363-378. sor).** Két mezőt állít be (`param_1[0x25]` és `[0x26]`, azaz +0x94 és +0x98) az argumentumaiból. Értéke 0 esetén a +0x164, majd a +0x15c slotot hívja. Értéke 1 esetén a +0x168, majd a +0x15c slotot hívja. Közvetlen hívottja nincs (HÍVOTTAK: 0, index).
- **Mentés-e (0x006952e0, 0x00692210)?** **Nem közvetlenül.** Mentés csak a vtable-célokban lehet (+0x15c, +0x164, +0x168). Ezek nincsenek a körben: **NINCS MEG**.

### 25.3 N6: 0x00584010, a 0x007baf50 gyűjtemény-frissítője

- **Argumentumai (`-5`, 2211., 2346. sor).**
  1. `*(this+0xd4)+0x2c5c` (uVar3). Ugyanez a gyűjtemény megy a 0x00585ad0-nak is a 0x007bb660-ban. Ez a válasz a 24.5 kérdésére: a gyűjtemény az **első** argumentum, nem a harmadik.
  2. `iStack_28`: interfész-mutató. A 0x007baf50 a végén felszabadítja (`-5`, 2383-2384. sor). A látott C-ben nincs beállítva.
  3. `&puStack_14`: a 0x007baf50 által épített rekordtömb. Az elemek 0x30 bájtosak, az elején 64 bites kulccsal.
  4. `&puStack_1c`: elemenkénti állapot-bájt (`-5`, 2336. sor: `bVar2 >> 1 & 3`).
- **Mit csinál (C, 400-514. sor).** (1) Minden rekordra meghívja a 0x005875d0-t 3-as móddal, a kulccsal és az 1. argumentummal. Hibánál megáll. (2) Ha a 2. és a 4. argumentum nem nulla, a 2. argumentum vtable-jén kér egy listát. Az állapot-bájt nem 2 elemeire meghívja a 0x005836f0-t (21.5 szerint a név-tábla kivétele).
- **Ír-e lemezre?** A C-törzsben nincs fájl-API, és a HÍVOTTAK-listában sincs. Ha ír, az a 0x005875d0, a 0x005836f0 vagy a 2. argumentum vtable-hívásai belsejében van: **NINCS MEG**.
- **Mentés-hívás** (0x006952e0, 0x00692210) a hívottak között **nincs**.

### 25.4 N6: 0x006a3b80, a faces= kulcs forrása

- **Mit csinál (C, 599-755. sor).** Egy láncolt listán (`param_1[0x16]`) keres. A csomópont nevének utolsó N karakterét hasonlítja a keresett névhez, kisbetű-érzéketlenül (667-669. sor). N a keresett név hossza. Találatnál a csomópont típusától függ a folytatás: vagy értéket ad (677. sor), vagy a `param_3` indexű elemet írja ki. A 0x13320004 típusnál ez 64 bites szám `%I64u` alakban (729-732. sor). A lista végén 0-t ad (645. sor).
- **Van-e benne `faces=` literál?** **Nincs.** A függvény csak keres és formáz. A neveket a listából olvassa.
- **Honnan jön a `faces=` kulcs?** **NINCS MEG.** A listát töltő kód nincs a körben. A 0x006a3b80-at a 0x0068ac80 (0068af54) és a 0x0068b320 (0068b93a) hívja (index). A listát töltő függvény címe nincs meg. Ehhez a `this+0x988` mező írói kellenek (index, nem Ghidra).

### 25.5 N5: 0x00448c90, a személy-predikátum

- **Mit olvas (C, 807-821. sor).** Egy 64 bites értéket kér a 0x00448fb0-tól (local_8, local_4). Ez az egyetlen közvetlen hívottja.
- **Mit jelent a nem nulla érték?** A visszatérés 1, ha a 0x00448fb0 0-t adott és a 64 bites érték nem nulla (817-818. sor). Egyébként a 0x00448fb0 visszatérését adja `& 0xffffff00`-val (820. sor). Ezért a nem nulla eredmény kétféle lehet: (a) a 64 bites érték nem nulla, vagy (b) a 0x00448fb0 magas bitekben hibakódot adott (pl. 0xf4242 esetén 0xf4200). A 0xff alatti hibakódok (pl. 2) 0-t adnak.
- **A 64 bites érték jelentése** (személy-azonosító-e): **NINCS MEG**, mert a 0x00448fb0 nincs a körben.
- **Hívók** (index): 42, köztük a 0x005c9b00 három helyen és a 0x005c9930 egy helyen (24.3, 24.6).

### 25.6 N5: 0x009bab50, a megerősítő párbeszéd visszatérése

- **Mit ad (C, 880-916. sor).** A párbeszéd eredményét (vtable +0x158) képezi le: 0 → 0, 2 → 1, más nem nulla → 2 (907-915. sor). Ha a gombcsoport hiányzik, 2-t ad (898-900. sor). Ha a `param_1[0x36]` nem nulla, a gombcsoport +0x88 mezőjét 1-re vagy 2-re állítja (889-906. sor).
- **Melyik gomb a 0?** **NINCS MEG.** A gombazonosítók a vtable +0x158 hívásban és a gombcsoportban vannak.
- **A 0 jelentése két hívónál ellentétes:**
  - a 0x00640340 (a törlés-megerősítés, 22.3): 0 esetén a művelet fut tovább, és 0-val tér vissza. Nem nulla esetén 0xf4242-t ad, és a törlés nem fut.
  - a 0x007bb660 (a duplikáció-kérdés, 285-306. sor): nem nulla esetén meghívja a FUN_007bb370-et, és annak eredményével tér vissza. 0 esetén a FUN_007bb370 nem fut, és 0-val tér vissza.
  Tehát a 0 nem állandó jelentésű. A leképezés a dialógus-objektumtól függ.

### 25.7 N3: 0x006ccbb0 és a detektor-objektum

- **Mit csinál (C, 927-943. sor).** Az EDI-ben kapott objektum első mezőjébe a `CNevenVision::vftable` címet írja (932. sor). A második mezőt nullázza, a 0x0097adb0-t kétszer hívja, a többi mezőt nullázza.
- **Hívó.** A 0x0045f0c0 hívja (HÍVÓK: 0045f143). A 24.2 szerint (`-5`, 115-159. sor) ez a this+0x2e10 mezőbe kerülő objektum. A 0x0048e590 (`-4`, 168-172. sor) ebből a mezőből adja a 0x0048e1f0 kilencedik argumentumát (23.2).
- **Osztály:** `CNevenVision`. Ez **feltételes**: az EDI-átadást a 0x0045f143 hívásnál nem néztük meg diszasszemblálással.
- **Vtable (index).** A `rtti.csv` szerint a `CNevenVision::vftable` (0x00ca8754) 25 bejegyzésű. A +0x2c slot (a 0x0048e1f0 hívja, 22.2) **0x006cde50**. A +0x34 slot 0x006cdf30. Ez index-adat, C-ben nincs megerősítve.
- **A Red.dll.** A `research-2026-08-13-red-pipeline.md` (44-49. sor) szerint a CNevenVision a Red.dll betöltője: a 0x006cc9e0 a LoadLibraryA után a `REDENTRY` exportot hívja. A jegyzet a megállapítást megerősítettnek jelöli. A detektor tehát valószínűleg a Red.dll-ben van. Ehhez a körben nincs Ghidra-dump.
- **960 px:** **NINCS MEG.** A 0x006cde50 olvasata után derül ki, hogy a méretezés a fő binárisban van-e, vagy a Red.dll-ben.

### 25.8 N5: 0x006ca8c0, a mappa-ág kimeneti pufferei (nem blokkoló)

- **Mit csinál (C, 982-1115. sor).** A kritikus szakasz zárolása után: ha a `param_1[0x19]` lista nulla, 4-gyel tér vissza (1012-1025. sor).
- Ha a `param_2` vagy a `param_3` 0 (1026. sor), a kimeneti tömböt (ESI) újraépíti. A lista elemeinek 4 bájtos értékeit másolja bele. A `param_2 = 0` esetén a `param_1[0x1b]` táblában, a `param_3 = 0` esetén a `param_1[0x1f]` táblában nem nulla bájtú elemeket kihagyja (1036-1057. sor). A tömb kapacitását duplázza (1061-1074. sor). A régi tömböt a 0x0097caf0-val szabadítja fel, vagy a 0x0097c810-zel méretezi át.
- Ha mindkét argumentum nem nulla: a 0x00891110-t hívja a listán (1102. sor). Ennek C-je nincs a körben.
- A 0x00440af0 hívja (24.3).
- **Ír-e lemezre vagy az ini-be?** **Nem.** Csak memóriában dolgozik. Fájl- vagy ini-hívás nincs.

### 25.9 Ghidra-kör kérések (új)

- **Válasz (#5184, 0x006cde50, CNevenVision +0x2c slot):**
  - **Slot:** egyetlen hivatkozása van, DATA-hivatkozás a `0x00ca8780` címről (dump 4. sor). A rtti.csv szerinti `0x00ca8754` vtábla +0x2c helye ez, tehát a slot ezt a függvényt tartalmazza.
  - **960 és méretezés: a függvényben nincs.** Nincs `0x3c0` konstans, nincs szorzás vagy osztás (dump 8-36. sor). A méret a bemeneti képfejlécből jön (`fejléc[1] >> 1`, dump 27. sor), futásidejű érték, nem konstans.
  - **Továbbadás:** ha a bemeneti ellenőrzés teljesül (dump 19-23. sor), a függvény a `DAT_00d35e44` globális mutató által mutatott objektum +0x44 vtábla-metódusát hívja. Argumentumai a this+0x8-tól a this+0x1c-ig tartó hat mező és az öt szavas rekord címe (dump 28-31. sor). Visszatérés: 0, ha a hívott 0-t adott, egyébként 0xFFFFFFFF; a védelmi ágon is 0xFFFFFFFF (dump 32, 35. sor).
  - **Nem dönti el:** hogy a `DAT_00d35e44` célja a Red.dll-beli objektum-e. A 25.7 a Red.dll-t a 0x006cc9e0 betöltőhöz köti, de ez a dump ezt nem igazolja.
  - **Bizonyítottsági fok:** megerősített a slot-hozzárendelés (DATA-hivatkozás és rtti.csv). Feltételes a 960 és a méretezés hiánya (a C-törzs teljes olvasata, egy út). NINCS MEG a célobjektum.
  - **Következő bináris lépés:** a `0x00d35e44` címre hivatkozó írók megkeresése (index, adat-hivatkozás), majd a célobjektum +0x44 slot-függvényének dekompilálása (Ghidra).
- **Válasz (#5184, 0x00448fb0, a 0x00448c90 64 bites kimenete):**
  - **A kulcs táblaindex, nem azonosító.** A bemenet `param_1` index. Ha az index a this+0x27a0 mezőben lévő objektum `+0x4c >> 1` darabszámán belül van, a kimenet a `+0x48` tömb `param_1`-edik 8 bájtos eleme (dump 90-96. sor).
  - **Visszatérési kód:** 0, ha az index a táblán belül van; 4, ha kívül. Ekkor a kimenet a this+0x27a8 és this+0x27ac alapértelmezett 64 bites érték (dump 98-101. sor).
  - **A nulla és a nem nulla jelentése: NINCS MEG.** A tábla tartalmát ez a függvény csak olvassa. Hogy a 8 bájtos elemek személy-azonosítók-e, azt a tábla íróiból lehetne megtudni, az írók nincsenek a dumpban.
  - **Hívó:** a 0x00448cac a 0x00448c90-ben (dump 44. sor). Ez megerősíti a 25.5 leírását.
  - **Bizonyítottsági fok:** megerősített a mechanizmus (C-törzs és HÍVÓK-fejléc). NINCS MEG a kimenet tartalmi jelentése.
  - **Következő bináris lépés:** a this+0x27a0 objektum +0x48 tömbjének és a this+0x27a8 alapértelmezett értékének írói (mezőhivatkozás index, majd a konstruktor dekompilálása).
- **Válasz (#5184, 0x00448a10, a második predikátum):**
  - **Mit olvas:**
    1. a **slotot**: ha a `param_2` index a `param_1+0xb48` objektum `+0x48` tömbjének tartományában van, a tömb `param_2`-edik 4 bájtos eleme, különben a `param_1+0xb4c` mező (dump 189-195. sor);
    2. a **slot-rekordot**: az első dword azonosító, érvényes, ha legalább 0x100; a `+4` mezőben NUL-ig tartó sztring (dump 203-209. sor);
    3. két **referencia-sztringet**: K1 a `param_1+0x2e98`, K2 a `param_1+0x2e94` rekord `+4` mezőjéből (dump 196-201, 257-262. sor). Hiányzó vagy üres rekord üres sztringnek számít.
  - **Mit ad vissza:** ha a slot neve egyezik K1-gyel, vagy mindkettő üres, a visszatérés `param_3 == 0` (dump 238-240. sor). Ha nem, de K2-vel egyezik, vagy mindkettő üres, 1 (dump 316-329. sor). Egyébként 0 (dump 299-313. sor). A sztringek összehasonlítása bájtonként történik; kisbetű-átalakítás a dumpban nincs (dump 220-234. sor).
  - **Hívók:** a 0x005c9930 (0x005c9971 címen) és a 0x005c9b00 (0x005c9ce9, 0x005c9f09, 0x005ca046 címen), dump 120-123. sor. A `param_2` értéke ezeknél a hívásoknál **NINCS MEG**, mert a hívók törzse nincs a dumpban.
  - **Bizonyítottsági fok:** megerősített a mechanizmus (C-törzs és HÍVÓK-fejléc). NINCS MEG: K1 és K2 jelentése, a slot-tábla tartalma, a hívók `param_2` értéke.
  - **Következő bináris lépés:** a 0x005c9930 és a 0x005c9b00 dekompilálása a fenti hívások körül (a `param_2` forrása), valamint a `param_1+0x2e94`, `+0x2e98` és `+0xb48` mezők íróinak megkeresése.
- **Válasz (#5184, 0x004aca00, az üres kijelölés ága):**
  - **Közvetlenül nem olvas kijelölést.** A this+0xc4 mutató által mutatott A objektum +0x48 címén kezdődő beágyazott objektum vtábla +0x28 metódusát hívja a `param_1` argumentummal (dump 370. sor). Ennek visszatérését nem használja.
  - **A visszatérés `FUN_00401000()` eredményének maszkolt értéke:** `eredmény & 0xFFFFFF00` (dump 371-372. sor). 0, ha az eredmény 256-nál kisebb.
  - **Hívók:** a 0x005c9b00 két hívása, 0x005c9da6 és 0x005c9ff5 (dump 345-346. sor).
  - **A HÍVOTTAK-listán van, a C-törzsben nincs:** `FUN_00987030` (dump 355. sor). A Ghidra a 0x004aca34, 0x004aca3a, 0x004aca4e és 0x004aca66 blokkokat elérhetetlennek törölte (dump 358-361. sor), a hívás ezekben lehet. Nem bizonyított.
  - **Bizonyítottsági fok:** megerősített, hogy a visszatérés a `FUN_00401000` maszkolt eredménye, és hogy a függvény közvetlenül nem olvas kijelölést (C-törzs és HÍVOTTAK-fejléc). NINCS MEG: hogy a `FUN_00401000` vagy a vtábla-metódus vizsgál-e kijelölést, vagyis a predikátum tényleges jelentése. Ebből a függvényből az „üres kijelölés" jelleg nem igazolható.
  - **Következő bináris lépés:** `FUN_00401000` dekompilálása; az A+0x48 beágyazott objektum típusának és +0x28 slotjának meghatározása (index, vtábla); a 0x004aca34-0x004aca66 tartomány diszasszemblálása (`pe_dis`), hogy kiderüljön, hívja-e a `FUN_00987030`-t.
- **Válasz (#5184, 0x005875d0, a 0x00584010 hívása, 3-as mód):**
  - **Közvetlen fájl-írás: nincs.** A törzsben és a HÍVOTTAK-listán (17 tétel, dump 386-403. sor) nincs fájl-API. A lista 13 belső függvényt és 4 külső hívást tartalmaz (kritikus szakasz, szálazonosító, `__aullrem`).
  - **Közvetett író lehetséges, nem bizonyított:**
    - `FUN_0058dd00`: csak kulcsos ágon, ha a 2-es mód-bit be van állítva és a beszúrás sikerült vagy a rekord változott (dump 612-613, 622-624, 646-648. sor);
    - `FUN_00927530`: kulcsos ágon, meglévő rekordnál (dump 617. sor);
    - `FUN_005836f0`: ha a `param_7` nem nulla (dump 642-645. sor).
    Törzsük nincs a dumpban. **NINCS MEG**, hogy írnak-e fájlba, és melyikbe.
  - **A mód bitjei (C-törzs):** az 1-es bit a `param_1+0x13c` bájtot 1-re állítja (dump 472-474, 609-611, 619-621. sor). A 2-es bit a `FUN_0058dd00` hívást engedélyezi kulcsos ágon (dump 612-613, 622-624, 646-648. sor). A 4-es és 8-as bit a `FUN_00927530` 3. és 4. argumentuma (dump 617. sor).
  - **Mód 3 (1 + 2):** kulcs 0, vagy mindkét szava 0xFFFFFFFF esetén (dump 436, 440. sor) csak a `param_1+0x13c` bájt áll 1-re, `FUN_0058dd00` nem hívódik. Kulcsos ágon a beszúrás vagy módosítás után a bájt 1-re áll, és `FUN_0058dd00` hívódik.
  - **A „3-as mód" nincs igazolva:** a 0x00584010 hívás (005840b8, dump 381. sor) argumentumértéke nincs a dumpban.
  - **Memóriában írt rész (C-törzs):** a `param_1` objektum hash-táblája: darabszám `+0xcc`, bucket-szám `+0xd0`, csomópont-készlet `+0xd4`, bucket-tábla `+0xd8`. A bucket-index a 64 bites kulcs maradéka a bucket-számmal osztva (`__aullrem`, dump 488-490, 559. sor).
  - **Bizonyítottsági fok:** megerősített, hogy a törzs közvetlenül nem ír fájlba (C-törzs és HÍVOTTAK-fejléc). Feltételes a bitek és a műveletek leképezése (egy út: C-törzs). NINCS MEG: a közvetett írás, a mód értéke a hívásban, a `+0x13c` bájt olvasói.
  - **Következő bináris lépés:** `FUN_0058dd00` és `FUN_00927530` dekompilálása (a mód-3 kulcsos ágának mellékhatása); a `param_1+0x13c` bájt olvasóinak megkeresése (index, mezőhivatkozás); a 0x00584010 dekompilálása a 005840b8 körül (a mód argumentuma).

Diszasszemblálás kell (nem Ghidra): a 0x0045f143 előtt az EDI értéke, vagyis a this+0x2e10 objektum-e (25.7). A 24.6 két diszasszemblálási kérése (a 0x0068ac20 ciklusa és a 0x005fdc30 EDI-je) nyitott: ebben a dumpban nincs rájuk adat. A `this+0x988` mező írói a 25.4 faces= kérdéséhez kellenek (bináris-index).

### 25.10 Következtetés: a felvétel dönt

Az új kérések többsége hívott, nem hívó (25.9). Ezek egy lépésben dönthetnek. A hívó-irányú kérések (N1 és N6) nem zárnak: a következő kör újabb hívókat kérne. Ott a felvétel dönt. A felvétel a Colab-végrehajtón fut. A viselkedés-típusú feladat a tulajdonos `jovahagyva` címkéjét kéri (24.7). Ezt a tulajdonos dönti el.

**N1 (felvétel).** A 24.6-ban és a 25.9-ben nincs N1-kérdés. A 0x006b6a50 rekordolvasó 13 hívójának olvasása nem zár: újabb hívó-kör kellene (24.7). A B2-felvétel (24.7) érvényes. Három kimenetet különböztet meg:
- B kiesik, B2 marad: a kizárás név-alapú. A mi kódunk (`src/picasapy/app/face_scan_controller.py:470-474`) egyezik.
- B2 is kiesik: a kizárás a feldolgozottságtól függ, nem a névtől. A mi kódunk eltér.
- B marad: az eredeti nem zárja ki a nevezett képet. A mi kódunk eltér.

**N3 (960 px, felvétel).** A 24.7 jóslatát ez a kör pontosítja. A 24.7 szerint a kép méretét úgy változtatnánk, hogy az arc aránya állandó. Ez a terv nem dönt: ha a detektor 960 px-re skáláz, a skálázás után a bemenet azonos lenne, és a találati arány nem változna. Pontosított terv: az arcot kivágjuk, üres háttérbe illesztjük, és a kép teljes hosszát változtatjuk: 640, 800, 960, 1280 és 1600 px. Ha a találati arány a 960 px körül változik, a detektor a bemenet méretét használja. Ha nem változik, a 960 nem a bemeneti méret.

**N6 (trigger, felvétel).** A 0x007bb660, a 0x008d2720, a 0x00584010 és a 0x007baf50 nem hív mentési láncot közvetlenül. A törlés (0x007ba820) után a 0x007b99a0 visszatér (23.5). A mentés kiváltója a 0x006980a0 vagy a 0x00692210 parancs-tábláiból jön. Ezeknek a hívóit újabb hívó-kör kérné, ezért a felvétel dönt (24.7 terve). Egy megnevezett személyt törlünk. Utána összevetjük a `.picasa.ini` és a `[Contacts2]` tartalmát két időpontban: a törlés után azonnal, és a Picasa bezárása után.
- Ha a `faces=` sor azonnal változik, a mentés a törlési ágból vagy annak közeli hívóiból indul.
- Ha csak bezáráskor változik, a mentés a parancs-szinten van.
A felvétel a `faces=` forrását nem dönti el, csak a mentés időzítését.

**N5 (személy, felvétel).** A 0x00448fb0 (25.9) dönti el a predikátum jelentését. Ha az nem dönt, a felvétel: egy megnevezett személy mellőzése, és egy név nélküli arc mellőzése. Mindkettő után a `.picasa.ini` `faces=` sorait és a Picasa albumlistáját (a `]expeople:%d` album neve) vetjük össze. A megerősítő párbeszéd mindkét gombjával külön próba kell. Így dől el a 0 jelentése (25.6).

### 25.11 A 20. szakasz N-pontjainak új állapota

| Pont | Állapot | Mi változott |
|---|---|---|
| N1 | BLOKKOLT | Nincs új adat. A döntés a B2-felvételre vár (25.10). |
| N3 | BLOKKOLT | A detektor osztálya CNevenVision (feltételes). A +0x2c slot: 0x006cde50 (index). A 960 px: NINCS MEG, a Red.dll-ben lehet. |
| N4 | LEZÁRVA | Változatlan. |
| N5 | BLOKKOLT | A 0x00448c90 olvasata megvan. A jelentés a 0x00448fb0-tól függ. A 0 jelentése a 0x009bab50 két hívójánál ellentétes. |
| N6 | BLOKKOLT | Az ok és az online ág sem hív mentést közvetlenül. A `faces=` forrása és a mentés kiváltója NINCS MEG. |
| N7 | BLOKKOLT | Változatlan. |
| N8 | BLOKKOLT | Változatlan. |

Nyitott kérdések: 0 nyílt · 1 lezárva · 6 blokkolt · 0 hatókörön kívül · 0 „csak nyitva".

### 25.12 Bizonyítottsági fok és cáfoló kísérletek

**Megerősített (két út: a C-törzs és az index vagy más forrás):**
- (a) A 0x007bb660, a 0x008d2720 és a 0x00584010 nem hívja közvetlenül a 0x006952e0-t vagy a 0x00692210-t (C-törzs és index-fejléc).
- (b) A 0x00584010 C-törzsében és HÍVOTTAK-listájában nincs fájl-API (C-törzs és index-fejléc).
- (c) A 0x006ccbb0 a `CNevenVision::vftable` címet írja az első mezőbe (C-törzs és `rtti.csv`).

**Feltételes (egy út, vagy két hívó ugyanazon az eszközön):**
- (d) A 0x007baf50 első argumentuma a `this+0xd4+0x2c5c` (`-5` C, egy út).
- (e) A this+0x2e10 objektum CNevenVision (C: 0x0045f0c0 és 0x0048e590). Az EDI-átadás nincs diszasszemblálással ellenőrizve.
- (f) A +0x2c slot célja 0x006cde50 (csak index).
- (g) A 0x006a3b80-ban nincs `faces=` literál (C-törzs, egy út).
- (h) A 0x00448c90 visszatérésének olvasata (C-törzs; a 0x00448fb0 az egyetlen közvetlen hívottja, index).
- (i) A 0x009bab50 0-jelentése nem állandó (két hívó, egy eszköz).
- (j) A 0x008d2720 vtable-célja nincs olvasva. A mentés kizárása csak a közvetlen hívásokra áll.
- (k) A mentés kiváltója a DATA-táblákban van (csak index).

**NINCS MEG:**
- a 0x00448fb0, a 0x00448a10 és a 0x004aca00 jelentése (N5);
- a +0xec slot célja (N5);
- a 0x005875d0 és a 0x005836f0 fájl-írása (N6);
- a 0x00585ad0, a 0x0058ff00 és a 0x007b7f00 szemantikája (N6);
- a `faces=` forrása, vagyis a 0x006a3b80 listáját töltő kód címe (N6);
- a 960 px helye: a fő binárisban vagy a Red.dll-ben (N3);
- a dialógus 0 gombja (N5);
- a 0x006b6a50 rekordolvasójának jelentése (N1);
- a 0x0045f0c0 EDI-átadása a 0x006ccbb0 előtt (N3).

**Cáfoló kísérletek:**
- (a) N6 mentés: a 0x008d2720 vtable-hívásai mentést indíthatnak. Ezt nem zártam ki. A negatív állítás a közvetlen hívásokra szól.
- (b) N5 „nulla = igen": ugyanaz a 0 a 0x007bb660-ban a FUN_007bb370-et kihagyja. A 0 tehát nem általános „igen".
- (c) N3 osztály: ha a 0x0045f0c0 a 0x006ccbb0 után más vtable-t írna a this+0x2e10-be, az osztály eltérne. A 24.2 olvasatában ilyen írás nem szerepel, de a teljes 0x0045f0c0-t nem néztem végig.
- (d) N3 960 px: a 0x0048e590 C-jében nincs 960 (23.2). Ez a fő binárisra szól, a Red.dll-re nem.
- (e) N6 `faces=` literál: a 0x006a3b80-ban nincs literál. A kulcs a listából jöhet, ezt nem zártam ki.

### 25.13 Fejlesztési következmény

Nincs lezárt N-pont, ezért nincs bizonyított eltérés, és nincs fejlesztési lista. A `src/picasapy/app/face_scan_controller.py:470-474` név-alapú kihagyása (N1) nyitott. A B2-felvétel dönt. A 21.8, 23.9 és 24.10 szerinti „fejlesztési lista: nincs” érvényben marad.

### 25.14 Mérleg (7. kör)

Megerősített: 3 tétel (25.12 a-c). Feltételes: 8 tétel (25.12 d-k). NINCS MEG: 9 tétel (25.12). Blokkoló Ghidra-kérés: 4 (25.9), nem blokkoló: 1 (25.9). Felvétel dönt: N1, N3 (960 px) és N6 (trigger). N5 a 0x00448fb0 után, különben felvétel. Tulajdonosi döntés: a Colab-felvétel jóváhagyása (`jovahagyva` címke).

## 26. #5185: javaslatok, személy-album és az arcfelismerés indítása (2026-10-17)

**Hatókör:** a #5185 3., 5. és 8. pontja. A javaslatfejléc ismert parancsait és a jóváhagyás adatútját a 15. és 18. szakasz írja le. Ez a kör a javaslatok felületi helyét, a személy-album műveleteit és az indítási kapukat egészíti ki.

**Jelölés:** a PicasaPy oszlop forrásolvasat, nem futtatott viselkedés. A „megerősített” csak két egymástól független út egyezésekor áll.

| Pont | Eredeti | Nálunk | Teendő |
|---|---|---|---|
| 3.1 Név nélküliek és névjavaslat | Az unknownfaceheaderpanel.tre csoportosítási, mellőzési és névhozzáadási vezérlőket sorol fel, javaslatgombot nem. A peoplepanel_text.tre szerint névadás után a személy albumát kell megnyitni a találatok elfogadásához vagy elutasításához. A job-167-ben gépelt névrészletre megjelenő arckép és név névjegy-kiegészítés. Ez önmagában nem arcfelismerési javaslat. **Fok: megerősített** a súgó és a faceheaderpanel erőforrástérképe alapján. A javaslat csempén való megjelenése nincs mérve. | Az UnnamedFacesView.qml kártya- és csempe-során javasolt név, kérdőjel és pipa jelenik meg (444-489, 699-745). A jobb oldali PeoplePanelRow külön pipát és X-et ad. A csempe sarkának X-e mellőzés, nem javaslatelutasítás. **Forrásolvasat.** | Az eredeti Név nélküliek csempéjét külön felvételen kell ellenőrizni. Rögzítsük a javasolt nevet és az esetleges elfogadó vagy elutasító gombot. A job-167 névjegy-kiegészítést ne azonosítsuk a felismerési találattal. |
| 3.2 Személy-album elfogadás és elvetés | A faceheaderpanel.tre tartalmazza a confirmsug, confirmsel, removesel, selectsug és sug_filter vezérlőket. A confirmsug és confirmsel kezelője a 0x00602640. A 18.2 szerint ez db3-oszlopot frissít, piszkos jelzőt állít, majd a 0x00484820 íróval faces= adatot írhat. A FRWriteFaceDataINI csak a facedata kulcsot kapuzza. A [Contacts2] frissítése elfogadáskor nincs mérve. A removesel a 0x005c9b00-ra megy, de az elvetés utáni fájl- és db3-állapot nincs mérve. **Fok: feltételes** az adatírásra, egy bináris út alapján. | A LightboxHeader az összes vagy kijelölt javaslat elfogadását és elvetését adja. A Main.qml a FaceScanControllerhez köti. Elfogadáskor az assignNameToFaces a FacesHelper.addFace útján ír [Contacts2] és faces= adatot, majd SQLite-indexet frissít. Elvetéskor a removePersonSuggestions a javasolt nevet törli az SQLite-indexből, az arc névtelen marad. Picasa db3-at nem írunk. **Forrásolvasat.** | Az eredeti Remove selected suggestions után külön mérjük a .picasa.ini, a contacts.xml és a db3 állapotát, azonnal és újraindítás után. Az elfogadást és az elvetést külön profilpéldányon rögzítsük. |
| 3.3 Jobb oldali Emberek panel | A peoplepanel.tre a suggestion_yes és suggestion_no elemeket rejtettként deklarálja. A 0x00648f20 dinamikusan felépíti őket. A 0x0063f970 eseményelosztó 8-as és 14-es eseményhelye a 0x00646d70 és 0x00647020 függvényt hívja. A 0x00647020 létrehozza a `]expeople:%d` tokent, a 0x004d9aa0 függvényt 2-es móddal hívja, törli a függő javaslat sort és frissít. A vezérlő és az eseményhely közti kapcsolat, valamint a tartós adatírás nincs teljesen igazolva. **Fok: feltételes.** | A PeoplePanelRow a javasolt nevet, pipát és X-et mutatja. A pipa az acceptSuggestion útján nevet ír az arcra. Az X a rejectSuggestion útján csak az SQLite javaslatmezőt törli. **Forrásolvasat.** | Ghidra-kör vagy célzott Colab-felvétel kell a két vezérlő pontos eseménykapcsolatához és az adatváltozásokhoz. A `]expeople` tokent ne nevezzük .picasa.ini kulcsnak. A mostani bináris vizsgálat csak a token képzését mutatja. |
| 5.1 Személy-album és arc/teljes kép váltás | A súgó a személy-albumot nevezi meg a javaslatok nézeteként. A faceheaderpanel a névhez tartozó album fejlécsávja. A face_zoom és picture_zoom súgója arcra közelített, illetve teljes képes nézetet nevez meg. A 0x005e5290 a Preferences/PeopleAlbumUseFaceSrc értéket 1 alapértékkel olvassa, a 0x00767e50 pedig a gombok állapotát állítja. A váltó két független bináris és erőforrás útja egyezik. Az első megnyitás képe nincs felvétellel igazolva. **Fok: megerősített** a váltó létezésére, nyitott az első megjelenített módra. | A LightboxFeed személynév alapján állítja be a személy-albumot. A LightboxHeader faceZoom állapota arcra vágott és teljes képes módot vált (208-245); a PeopleController tárolja. Az alapállapot a PicasaPy forrásában teljes kép. **Forrásolvasat.** | Colab-felvételen kattintsunk egy személy sorára. Rögzítsük a fejlécet, a képek tartalmát és a kiválasztott gombot. Kattintsunk mindkét módra, váltsunk másik albumra, majd térjünk vissza. |
| 5.2 Átnevezés | A személy-album helyi menüjében Edit People Album... parancs van (0x9c69, építő: 0x007359e0). A contactmgr nyelvi erőforrás Name mezőt és OK gombot tartalmaz. A ContactManagerDlg::DupNameMsg azonos nevű személyre figyelmeztet. A menü, a párbeszéd és a mentési út teljes kapcsolata, továbbá a contacts.xml, [Contacts2], faces= és db3 változása nincs mérve. **Fok: feltételes.** | Az Edit People Album megnyitja a People Manager párbeszédet a kiválasztott személlyel. A PeopleController átírja a központi contacts.xml-t és az érintett mappák [Contacts2] sorait; az arcazonosítókat megőrzi. **Forrásolvasat.** | Nevezzünk át egy albumot. Hasonlítsuk össze a contacts.xml, az érintett ini-k és a db3 állapotát mentés előtt, utána és újraindítás után. |
| 5.3 Két személy összevonása | A személy-album menüben nincs összevonási tétel. A képenkénti PplAlbumPhoto menüben van Move to People Album (0xa0cd) dinamikus almenü és Move to New Person (0xa0cc). A 17. szakasz szerint a 0xa0cd almenühorgony, a benne levő személylista futásidőben épül fel. Ez nem bizonyítja, hogy minden forrásalbum-kép áthelyezése törli vagy összevonja az üres albumot. **Fok: megerősített** a két menüút létezésére, nyitott a teljes album összevonására. | A PicasaPy képmenüje meglévő személyhez rendelhet kijelölt arcot. A People Managerben nincs külön összevonási művelet. A kijelölt képek átrendelése nem bizonyít teljes album-összevonást. **Forrásolvasat.** | Két, külön képekkel rendelkező albumon jelöljük ki az egyik összes képét, majd a Move to People Album almenüben válasszuk a másik személyt. Rögzítsük, eltűnik-e az üres album, és mi változik a contacts.xml, [Contacts2], faces= és db3 állományokban. |
| 5.4 Törlés | A személy-album menü Delete People Album tétele a 0x9d44 parancs (építő: 0x007359e0). A People Manager Delete Person gombjához a 0x007ba820 törlési kezelő és ContactManagerDlg::ConfirmDelete tartozik. A 21.5 szerint a memóriabeli kapcsolat bontása látszik, a lemezre írás és a címkézett arcok sorsa nyitott. **Fok: feltételes.** | A People album Delete megerősítést mutat, majd a savePeopleManagerChanges törlési útját hívja. Ez kezeli a központi névjegyet, a mappák [Contacts2] sorait és a hozzájuk tartozó faces= hivatkozásokat. **Forrásolvasat.** | Külön vizsgáljuk az album helyi menüjét és a People Manager Delete Person gombját. Rögzítsük a megerősítést, az arcok sorsát és az adatfájlokat törlés után, majd a program bezárása után. |
| 8.1 Automatikus és kézi indítás | A 0x0069fc00 konstruktor a BgFaceDetectThread kapcsolót 1 alapértékkel olvassa. A peoplepanel_text.tre szerint a Picasa fényképtár-olvasás közben arcokat keres. Ez két független út az automatikus háttérmotor meglétére. A mappa- és album-helyi Névcímkék hozzáadása a 0x9e1c parancs; a #4535 mérése szerint a célmappa közvetlen képein vagy az album tagképein indít keresést. Külön Find Faces parancs nincs az ismert Tools menüben. **Fok: megerősített** a háttérmotorra és a kézi helyi menüre. Az import és az új mappa felvételének pontos indítási pillanata nincs mérve. | A controller.syncFinished jelzése a FaceScanController.scanNewFaces metódust hívja. Az automatikus út a beállítástól és a futó kereséstől függ. Kézzel a teljes könyvtár, egy mappa vagy egy album vizsgálható a scanForFaces, scanFolder és scanAlbum metódussal. **Forrásolvasat.** | Új Picasa-profilon külön mérjük az első importot, az új mappa felvételét, a meglévő mappába tett új képet és a helyi Névcímkék hozzáadása parancsot. Rögzítsük a folyamatjelzést és az album darabszámát az indítás előtt és után. |
| 8.2 Kihagyások | A Mappakezelő `frexclude` kapcsolója és öröklött kizárása az 1.3. szakaszban dokumentált. A korábban vizsgált kép kihagyásának útja a 20.1-ben szerepel. A névvel címkézett képen talált további arcok feltétele a 21.3-ban nyitott maradt. Ezt a kört nem ismétlem. | A FaceScanController mtime/méret alapján átugorja a már vizsgált képet. Az `is_identified` vizsgálat névvel jelölt fotókat zár ki. **Forrásolvasat.** | Eredeti Colab-próba kell ismert névvel címkézett képpel, ugyanazon képen levő másik arccal, kizárási beállítással kizárt mappával, kizárt szülő alatti gyermekmappával, módosítatlan és megváltoztatott képpel. Az új találatokat és újraindítás utáni állapotot külön rögzítsük. |

### 26.1 Bizonyítottsági fok

**Megerősített:** a személy-album a javaslatok felületi helye; a face/picture váltó létezik; az automatikus háttérmotor alapból engedélyezett; a mappa- és album-helyi Névcímkék hozzáadása út kézi keresést indít. Ezeknél két független út egyezik, vagy a bináris vizsgálat és a rögzített mérés együtt áll rendelkezésre.

**Feltételes:** a jobb oldali People panel két gombjának pontos kezelője; a javaslat elfogadásakor a [Contacts2] frissítés; az album átnevezésének és törlésének eredeti mentési útja.

**Nyitott:** a javaslatok eredeti csempefelülete; a javaslat elvetésének és a `]expeople` tokennek a tartós hatása; a személy-album alap zoommódja; a teljes személy-album összevonás; az import és mappafelvétel automatikus indítási pontja; a névvel címkézett képen talált új arc kezelése.

### 26.2 Cáfoló kör

Megpróbáltam cáfolni azt a feltevést, hogy a Név nélküliek csempéjének X-e javaslatelutasítás. A job-162/163 üdvözlőszövege az X-et mellőzésre köti, az unknownfaceheaderpanel.tre az ignore gombot deklarálja, míg a javaslat súgója a személy-albumot nevezi meg. A job-167 név alatti listája névjegy-kiegészítésként viselkedik. Az ellenpróbák nem támasztják alá az X és a javaslatelutasítás azonosságát.

Az automatikus személy-összevonás feltételezését is ellenőriztem. A PplAlbum menü teljes listájában nincs összevonási tétel, a PplAlbumPhoto menü viszont képek személyek közti mozgatását kínálja. A ContactManagerDlg duplikált névre figyelmeztet, de nem ír összevonásról. Ez cáfolja a külön menüparancs feltételezését, de nem dönti el, hogy az összes kép mozgatása eltünteti-e a forrásalbumot.

### 26.3 Nyitott kérdések és megszerzésük

- **Válasz (#5185, 0x00646d70, a suggestion_yes eseményhely):**
  - **Eseményhely:** egyetlen hívója a 0x0063fd3c, a `FUN_0063f970` elosztóban (dump 655-656. sor). Hogy ez-e a suggestion_yes, azt az elosztó esetértéke dönti el; az esetérték a dumpban nincs. **NINCS MEG** a konkrét eseményazonosító.
  - **Mit csinál (C-törzs, dump 680-722. sor):**
    1. ha az index a `this+0x348 >> 1` darabszámon kívül esik: 9;
    2. kulcs: a `[this+0x344]` lista `param_1`-edik 8 bájtos elemének első mutatója által mutatott rekord első dword-je (dump 691. sor);
    3. `FUN_0044a6b0` keresés a kulccsal, a `*(DAT_00d67668+0x1034)` objektumon (dump 691. sor);
    4. **találatnál** (dump 700-721. sor): az A = `*(DAT_00d67668+0x102c)` objektum +0x24c és +0x250 mezőit nullázza (dump 707-712. sor); majd az `A+0x2a4` címen beágyazott objektum vtábla +0x44 metódusát hívja a találati értékkel és az 1, 0, 1 argumentumokkal; végül `FUN_0052e8a0`; visszatérés 1000000 (0xF4240);
    5. **találat nélkül** (dump 693-699. sor): `FUN_006464a0`; ha ez nem nulla, a visszatérés 0; különben a `this+0x374` mezőbe írja a `param_1` indexet, és 1000000-t ad vissza.
  - **Kijelölt arc:** a `this+0x374` mezőbe a `param_1` index kerül, és csak a találat-nélküli ágon, ha `FUN_006464a0` 0-t adott (C-törzs). Hogy ez a kijelölt arc, az a dumpból nem látszik. A találatnál hívott vtábla-metódus törzse **NINCS MEG**.
  - **db3 és ini írók:** közvetlen fájl-API nincs sem a törzsben, sem a HÍVOTTAK-listán (dump 657-664. sor). Közvetett írók lehetnek: `FUN_0044a6b0`, `FUN_006464a0`, `FUN_0052e8a0`, `FUN_009d2b40`, `FUN_006433a0` és a vtábla-metódus; törzsük nincs a dumpban. **NINCS MEG.** A `FUN_0097caf0` és a `FUN_00a58fc0` csak a HÍVOTTAK-listán szerepel (dump 662, 664. sor), a C-törzsben nincs; a Ghidra a 0x00646e6e, 0x00646db8 és 0x00646ea0 blokkokat elérhetetlennek törölte (dump 667-669. sor).
  - **Bizonyítottsági fok:** megerősített: egy hívó, és nincs közvetlen fájl-API (C-törzs és HÍVOTTAK-fejléc). Feltételes: a `this+0x374` írás és az elágazás (egy út: C-törzs). NINCS MEG: az eseményazonosító, a találati ág vtábla-metódusa, a db3 és ini írók.
  - **Következő bináris lépés:** a 0x0063f970 dekompilálása a 0x0063fd3c körül (az esetérték); `FUN_0044a6b0` és `FUN_006464a0` dekompilálása; a `DAT_00d67668` íróinak megkeresése; az `A+0x2a4` beágyazott objektum vtábla +0x44 célja; a `FUN_0097caf0` és `FUN_00a58fc0` hívásainak diszasszemblálása a törölt blokkok tartományában.
- **Válasz (#5185, 0x00647020, a suggestion_no eseményhely):**
  - **Eseményhely:** egyetlen hívója a 0x0063fe57, a `FUN_0063f970` elosztóban (dump 728-729. sor). Az esetérték **NINCS MEG** a dumpból.
  - **Mit csinál (C-törzs, dump 744-761. sor):**
    1. ha az index a `+0x358 >> 1` darabszámon kívül esik: 9;
    2. ha az index kisebb a `+0x348 >> 1` darabszámnál: a `FUN_0040eab0` hívást a `]expeople:%d` formátumsztringgel és a `+0x354` lista (4 bájtos elemek) `param_2`-edik elemének értékével végzi; majd `FUN_004d9aa0`-t hív a `*(DAT_00d67668+0x1034)+0x68` címre, a `+0x344` lista `param_2`-edik 8 bájtos elemének címével, 0 és 2 argumentummal; végül `FUN_00401000`-t (dump 747-757. sor);
    3. a 2. pont feltételétől függetlenül: a `+0x354` lista `param_2`-edik eleme `0xFFFFFFFF` lesz, és `FUN_0064ae90(this, 0)` fut; visszatérés 0 (dump 759-761. sor).
  - **A token:** a formázás a törlés előtt történik (dump 755. és 759. sor), tehát a formázott érték a régi. A formázott szöveg célpufferét a C-törzs nem mutatja: a hívás nem ad át kimeneti címet. **NINCS MEG**, hová kerül a token. `FUN_004d9aa0` nem a tokent, hanem a 8 bájtos bejegyzés címét kapja.
  - **Tartós mentés:** közvetlen fájl-API nincs a törzsben és a HÍVOTTAK-listán (dump 730-734. sor). Közvetett út lehet a `FUN_004d9aa0` és a `FUN_0064ae90`; törzsük nincs a dumpban. **NINCS MEG.**
  - **Bizonyítottsági fok:** megerősített: egy hívó, és nincs közvetlen fájl-API (C-törzs és HÍVOTTAK-fejléc). Feltételes: a formázás-törlés sorrend és a `0xFFFFFFFF` írás (egy út: C-törzs). NINCS MEG: a token jelentése és fogyasztója, a tartós mentési út, az esetérték.
  - **Következő bináris lépés:** `FUN_004d9aa0` (2-es mód) és `FUN_0064ae90` dekompilálása; `FUN_0040eab0` célpufferének megállapítása; a `]expeople:` sztring szövegtári keresztreferenciájának lekérdezése (index), hogy kiderüljön, melyik függvény fogyasztja a tokent; a 0x0063f970 esetértéke a 0x0063fe57 körül.
- Colab-lépéssor: egy névvel ellátott személy után várjunk arctalálat-javaslatot; nyissuk meg a személy-albumot; rögzítsük a javaslat nevét, a kijelölést és az összes vezérlőt; külön futásban fogadjuk el, majd utasítsuk el a javaslatot; minden lépés előtt és után mentsük a .picasa.ini, contacts.xml és db3 állapotát.
- Colab-lépéssor: hozzunk létre két, külön képekkel rendelkező személyt; kattintsunk az első bal oldali sorára; mérjük meg a két zoomállapotot; nevezzük át; ezután jelöljük ki az első album összes képét és próbáljuk a Move to People Album almenüvel a másikhoz rendelni; végül töröljük külön a forrás és cél albumot. Rögzítsük a megerősítéseket, az üres album sorsát és az adatfájlok változását.
- Colab-lépéssor: üres Picasa-profilban importáljunk egy fotót; figyeljük az első keresést; adjunk hozzá új mappát, majd abba új fotót; ismételjük meg kizárt mappával, kizárt almappával és már megnevezett arcot tartalmazó képpel; végül futtassuk a mappa- és album-helyi Névcímkék hozzáadása parancsot.

**A #5185 e három pontja ezen a körön nem zárható le teljesen.** A PicasaPy közvetlen csempe-javaslata és az eredeti személy-album súgója közti eltérés további eredeti felvételt igényel. Fejlesztési lista csak a fenti mérések után adható.
