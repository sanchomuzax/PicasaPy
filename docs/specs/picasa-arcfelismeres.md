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
> | **Ctrl** | `0x006038b0` - **`RemoveAllFaceData`**: MINDEN arc-adat és személyi album törlése + teljes újrakeresés |
> | **Shift** | `0x00603a20` - **`ResetAllFaces`**: minden személyi album törlése, az arcok a „Név nélküliek" albumba |
> | semmi | `0x0057daa0` - csak a **kijelölés** arcainak alaphelyzetbe állítása |
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

*Forrás: `0x0064c340` · `0x0064d197`-`0x0064d260` · `0x0063df90` (`0x0063e02c`) · `0x006c1ac0` (`0x006c1cfc`, `0x006c1d06`) · **`0x006c4630`** (`0x006c46f3`) · `0x0064d660` · `0x00647df0` - két egymástól független olvasat (lásd a bizonyítottsági fokot).*

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

*Forrás: élő mérés (eredeti angol Picasa 3.9.141, `picasa-colab-jobs` #72, #73, #74, #75; kulcsképek: `Colab EN 37 - Mellozott arc a nezoben.png`, `Colab EN 38 - Nem mellozott nev nelkuli arc a nezoben.png`) · `0x00483cb0` (`0x00483ff0`-`0x00484012`) · `0x0064c340` → `0x0064bb70` (`0x0064c227`) → `0x006c63d0` (`0x006c63fd`) · `0x00642c10` · `0x00641960` · `0x004841f0` (`0x004842c2`-`0x004842f9`) · `0x0049d560` · `0x0092c450` (`0x0092c476`) · `0x00484820` · `0x0049d390` · `0x007d55f0` · `0x00644900` · `0x006443e0` · `0x0064a410` - két egymástól független olvasat egyezik.*

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
(`0x0092321a`, IAT `0x00c406e4` - pefile-lal ellenőrizve), és a hívás
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
job-177, job-179, job-180, job-183 és job-207 leírásai; a job-180, job-183 és job-207
képernyőképeit közvetlenül megnéztük. A `Colab EN 36 - Ignore People megerosites.png` képet is közvetlenül ellenőriztük; a privát `referencia/kepek-leltar.md` 112. sor az eredeti Picasa 3.9.141, Wine, 1280×1024, Colab #63 képkockájaként azonosítja. Ez a külön kép az Ignore People modált és a mögötte látható rácsot mutatja; nem a job-64 ini-kimenetének képkockája. A kép helyi forrásútja `(helyi út) EN 36 - Ignore People megerosites.png`, SHA-256: `f7f31fb496ce72ea815204dbd9f101bcbd80ae12fc3617f08d1172f71c6b44b6`. A job-208 (J1) és job-209 képkockáit nem
néztük meg. A munkafában kapott `j4_*.png` képeket a job-210-hez, a
`kepernyo__29.png` képet a job-213 29. képéhez tartozóként közvetlenül
megnéztük; a hozzárendelés a feladatleírásból származik. Más képkockákról itt
nem teszünk állítást. A job-66 a Név nélküliek csempe-mezőjének útja: nem
külön névadási felület.

| Téma | Eredeti | Nálunk | Teendő, kész ha |
|---|---|---|---|
| Bal oldali sor, nézet és kezdőállapot | A bal sáv sorának felirata **„Unnamed (6)”**. Kattintásra a jobb oldalon az **„Unnamed people”** cím és személy-ikon, alatta **„6 Face(s)”**, majd az útmutató jelenik meg: „Select someone you know and add a name, or click the 'x' to ignore that person.” Jobbra az **„Expand groups”** és **„Show ignored faces”** gomb látszik; a nézet csoportosítva indul. A job-207 (8. kép) felvételén a fejléc: „Unnamed people”, alatta „6 Face(s)”, jobbra „Expand groups” és „Show ignored faces”, mindkettő az üdvözlőablak mögött halványan. Az alsó állapot **„No Selection”**, a tálca üres. A job-163 felvételén a bezárás után ez az állapot marad (`job-162`; `job-163`, 4. és 8. kép). | A `FolderPane.qml:587-630` a People gyűjtemény alatt, a személyek elé teszi az „Unnamed (N)” sort; beolvasás alatt is látszik, a számlálóba beleszámít (#5190). Kattintáskor a `Main.qml:3267-3271` törli a fotók kijelölését, `unnamed` módra vált, és a `Main.qml:3675-3692` helyén megjeleníti az `UnnamedFacesView`-t (#5183). A nézetfejléce a `UnnamedFacesView.qml:104-114, 165-229` sorokban készül; induláskor `grouped: true` és üres arc-kijelölés (`UnnamedFacesView.qml:29-52, 127-138`). | A fő nézet és az üres kezdőkijelölés felvétellel rögzítve. A Picasa tálca és a „No Selection” állapotát a job-162 leírása igazolja; a PicasaPy a fotó- és arc-kijelölést is üresen kezdi. |
| Nézet két módja: csoportosítva és kibontva | Csoportosítva (alapállapot): a váltógomb **„Expand groups”**, az útmutató „Select someone you know and add a name, or click the 'x' to ignore that person.”, a csempéken saját **„Add a name”** mező és X, a fejlécben nincs névmező. Ez kijelöléstől függetlenül így van: kijelölés nélkül, egy csempe kijelölésével és Ctrl+A után is (`job-180`, 6., 10. és 15. kép; Ctrl+A után mind a hat csempe kijelölve). Kibontva („Expand groups” után): a váltógomb **„Group by face”**, az útmutató „Select someone you know and add a name”, a csempéken nincs saját mező és X; a fejléc „6 Face(s)” sorában jobbra **„Add a name”** mező és **„Ignore Selected”** gomb van, kijelölés nélkül szürke (`job-183`, 10. kép; kijelöléssel, Ctrl+A után a gomb sötét, a mező fehér, 15. kép). A job-208 (9., 11. és 13. kép) ugyanezt a két nézetet adja a J1 lépéssorával (Expand groups, majd Group by face): csoportosítva öt oszlopban állnak a csempék, a fejlécben „Expand groups” (aktív) és „Show ignored faces” (szürke); kibontva egy sorban, kisebb csempékkel, csempén X és saját névmező nélkül, a fejlécben „Add a name” mező és „Ignore Selected” gomb (mindkettő szürke, kijelölés nélkül); a második kattintás után a csoportosított nézet változatlanul visszaáll. | #5214 (0.9.124) óta így (f99e7a1eb): a kibontott nézet fejlécében van a névmező és az Ignore Selected gomb; a csoportosítottban nincs. A fejléc elemeinek kódhelye: a váltógomb felirata a `UnnamedFacesView.qml:212`, az „Ignore Selected” gomb a `UnnamedFacesView.qml:305` sorban van; a job-208 elemlistája ezzel egyezik (pixelre nem vetettük össze). | Kész, ha a két nézet a `job-180` és `job-183` lépéssorával felvett állapotot mutatja (kijelölés nélkül és Ctrl+A után, képkocka-összevetéssel). |
| Első megnyitás üdvözlőablaka | Első alkalommal sötét, modális ablak takarja a nézetet. Cím: **„Welcome to the Unnamed people album!”**; a teljes szöveg job-207 (8. kép) alapján, szó szerint: „As Picasa scans your photos, the faces it finds are automatically grouped for easy naming.” / „Things to know:” / „To identify a person, click 'Add a name', then type in the person's name and press Enter. A new People album will be created each time you name someone for the first time.” / „(TIP: Sign in with your Google Account to gain access to all of your Google Account contacts while naming.)” / „To ignore a person, click the 'X' button on the face thumbnail.” / „Suggestions: After you name someone, Picasa may suggest more matching faces for that person. Click on a person's album to view and confirm (or reject) any suggestions.” / „Click 'Learn More' for information about this feature.” Gombok: **„Learn more...”**, **„Close”**. A job-162 kommentjének `…` rövidítéseit a job-207 képe pótolja. | A `UnnamedFacesView.qml:116-138, 742-829` első megnyitáskor, csak a Név nélküliek módjában mutat modális ablakot; bezáráskor a `FaceScanController` megjegyzi a megjelenítést (`face_scan_controller.py:200, 802-810`). A jelenlegi ablak szövege és gombjai a `UnnamedFacesView.qml:767-829` sorokban vannak. | A kezdőablakot a job-162 és a job-207 (8. kép) felvételi jegyzetei írják le; a job-207 a teljes szöveget adja, a komment `…` rövidítéseit pótolva. |
| „Learn more...” gomb az üdvözlőablakban | A job-175/177 felvételén a Picasán belül nem látszik változás, az üdvözlőablak nyitva marad; a Colab-gépen nincs böngésző, ezért a külső megnyitás eredménye nem látható. A bináris `0x0074c760` kezelője a `http://picasa.google.com/support/bin/answer.py?hl=%s&answer=156272` címsablont a `0x00981860` indító rutinjának adja át (28.2); `%s` a futáskor kapott nyelvkód. A bináris a megnyitás kezdeményezését bizonyítja, a sikeres oldalbetöltést nem. | Ebben a munkafában a `pyproject.toml` verziója 0.9.169. A `UnnamedFacesView.qml:133-137` állítja elő a címet, a `:866` pedig a `Qt.openUrlExternally(root.learnMoreUrl())` kezelőt futtatja. Ez forrásolvasat; a PicasaPy-beli kattintást és böngészőeredményt ebben a körben nem futtattuk. | A korábbi „nincs kezelője” állítás téves volt: a job-175/177 az eredeti Picasát mérte, nem a PicasaPy-t. Binárisan megvan a cél és a megnyitási kísérlet; a sikeres megjelenítés nincs mérve. PicasaPy-forrásban a kezelő megvan; élő külső megnyitás nincs mérve. |
| Csempék, mezők, X, méret és sorrend | Csoportosított nézetben álló arc-kivágások jelennek meg; a job-163 4. és 8. képe soronként öt csempét mutat, mindegyik alatt saját **„Add a name”** mezővel, a csempe jobb felső sarkában kis X-szel. A közvetlenül megnyitott `Colab EN 36 - Ignore People megerosites.png` (#63, 1280×1024) képkocka tényleges pixelszámlálása szerint az első sor öt `Add a name` mezőjének zárt befoglaló téglalapja: x=268-439, 462-633, 656-827, 850-1021, 1044-1215 és y=367-386; mindegyik 172×20 px. A második sor első mezője x=268-439, y=581-600, szintén 172×20 px. A hat megjelenített arcképkeret zárt koordinátájú téglalapja: (282-425,195-366), (476-619,195-366), (670-813,195-366), (876-996,195-366), (1067-1192,195-366), (282-425,409-580); rendre 144×172, 144×172, 144×172, 121×172, 126×172, 144×172 px. Ez a képkockán látható viewport mérete, nem a forrásképek vagy a belső arckivágások natív mérete, és más felbontás skálázását nem bizonyítja. A képkockán a vizuális sorrend balról jobbra, majd következő sor; tartós rendezési kulcs nem ismert. A képkocka az `Ignore People` modált mutatja. A job-208 (9. kép) ugyanazt az öt oszlopos elrendezést adja, hat egyarcú csoporttal; csoporthatár ilyen mintán nem látszik, ahhoz többarcú csoport kell (19.1, 5. pont). | A `face_scan_controller.py:812-858` az arc-csoportokat csoportazonosító szerint növekvően, a még nem csoportosított elemeket a végén adja vissza; összecsukva csak csoportonkénti előnézetet ad. A `UnnamedFacesView.qml:355-410` 194 × 198-as rácscellát és 146 × 172-es arckivágást állít be; a `UnnamedFacesView.qml:482-508` minden archoz saját, 172 px széles „Add a name” mezőt ad. A csempe X-e a `UnnamedFacesView.qml:417-440` sorokban van. | A csoportosított alapállapot és az egyedi mező/X felvétellel igazolt. A `Colab EN 36` (#63) képkockája pontosan méri a mezőket és az ezen a képkockán megjelenő látható arcképkereteket; a kép saját méretét és a skálázást nem. Nem dönti el a tartós rendezést vagy a csoporthatárokat. Ezekhez stabil azonosítójú, teljesen látható, többarcú mintán készült felvétel kell. |
| Fejlécmező és a csempe névmezője | A binárisban a **fejléc** `addname` parancsa a jobb fiók PeoplePaneljéhez jut (`0x00602970`), amely ott `headerautocomplete` és `header_editbox` mezőt hoz létre (`0x00640670`, `peoplepanel_text.tre`). Ez a panelmező útja. A Név nélküliek **csempéjének** saját „Add a name” mezője külön, élő úttal igazolt (`job-163`, 4. és 8. kép; `job-66`). | A Név nélküliek csempéjén saját `TextField` van (`UnnamedFacesView.qml:482-508`); a jobb oldali People panel sormezője külön komponens (`PeoplePanelRow.qml:149-166`). A job-167 útvonalon a csempe mezője Enterre mindig People ablakot kér (`Main.qml:3690-3692`; `PeoplePanel.qml:192-210`). A jobb fiók meglévő névre történő Enter-kezelése ettől eltér (#5199; `PeoplePanel.qml:192-205`). | A „névmező inline panelmező” állítás csak a fejléc `header_editbox` mezőjére vonatkozik; a Név nélküliek csempéjének saját mezője van. A két út ne legyen összemosva. |
| Új név, People ablak és tárolás | A csempe mezőjébe írt **„Teszt Elek”** után Enterre **„People”** ablak nyílik. A Search mezőbe a név előre be van írva és ki van jelölve; a névlista üres, a **„Delete Person”** és **„OK”** tiltott, a **„New Person”** aktív. Jobbra „Name:” és „Email(s):” mező, szürke „Sync Face Tags with Web Albums” jelölő és „Revert”; alul „Manage Online Contacts”, „Refresh Contacts”, „OK”, „Cancel” (`job-163`, 14-19. kép). Az új személy OK-ja után a bal sávban `People (2)`, `Unnamed (5)`, `Teszt Elek (1)` látszik (`job-167`, 18. kép). A `.picasa.ini`-ben `[Contacts2]` alatt `<azonosító>=Teszt Elek;;`, a fotó szakaszában `faces=rect64(…),<azonosító>` szerepel (`job-66`; `job-167`, 18. kép). A job-66 helyesbítése szerint ez is a csempe-mező útja. A job-213 (a futás végén) ugyanezt a szerkezetet mutatja két fotóval: a `[Contacts2]` alatt egy sor, `3c067b829137b19=Teszt Elek;;`, és mindkét fotó `faces=` sora ugyanarra az azonosítóra mutat. Az azonosító 15 jegyű (32. szakasz). | A csempe Enter-kezelője kiüríti a mezőt és jelzi a beírt arcot/nevet (`UnnamedFacesView.qml:501-508`); a `Main.qml:3690-3692` ezt People ablakra küldi. A `PeopleManagerDialog.qml:53-98` előtölti a Search mezőt, meglévő találatnál kiválasztja a kontaktot; a `PeopleManagerDialog.qml:146-170` kezeli a „New Person” műveletet; a `PeopleManagerDialog.qml:241-289, 299-380, 381-473, 485-510` adja az OK/Choose útját, a kereső/listát, a névjegymezőket és az alsó gombokat, majd menti és a kijelölt arcra alkalmazza. A `face_scan_controller.py:861-923` a sikeres arcot megnevezettként rögzíti, frissíti a mappát és az arcszámot; a `faces_helper.py:265-295` az érintett `.picasa.ini`-t írja. | Az új név útja és eredménye a job-163/167 felvételi jegyzeteiben szerepel. A `[Contacts2]` és `faces=` adatot a job-66 ugyanebből a csempe-mezőből mérte; ez nem másik felületi útvonal. |
| Meglévő név, javaslatlista, Choose és Escape | A mezőbe írt `Tes` alatt javaslatlista jelenik meg arcképpel és **„Teszt Elek”** névvel (`job-167`, 22. kép). A teljes név Enterre People ablakot nyit, a `Teszt Elek` személy kijelölve, „1 Photo in Picasa” adatsorral, **„Choose”** gombbal (`job-167`, 26-30. kép). A felvétel nem kattintott a Choose-ra, ezért az arc a Név nélküliek között maradt. Az ismeretlen `Valami` keresés üres listát és Name mezőt, tiltott OK-t ad; Escape bezárja az ablakot változtatás nélkül (`job-167`, 32-34. kép). | A csempe mező részleges szövegre a névjegyek között kis-nagybetűtől független részsztringet keres; a felugró listában kép és név jelenik meg (`UnnamedFacesView.qml:371-385, 512-589`). A csempe Enter útja meglévő névnél is People ablakot nyit, a meglévő kontakt kiválasztásával és **Choose** gombbal (#5192; `PeoplePanel.qml:192-210`; `PeopleManagerDialog.qml:82-93, 499-505`). **Javítva (2026-10-21, #5437):** a javaslat-elemre kattintás van. A `UnnamedFacesView.qml:650-652` `MouseArea`-ja a `submitName(personName)`-et hívja (#5285), tehát ugyanazt az utat, mint az Enter. A korábbi „nincs aktiváló kezelő” állítás a régebbi sorokra (547-587) vonatkozott; a kattintás élő viselkedése még nincs mérve. | A javaslatlista, a People ablak, a Choose felirata és az ismeretlen névnél People Search Escape a job-167 felvételi jegyzetében szerepel. A javaslatelem kattintásának kódja megvan (lásd fent); az élő kattintás mérése nyitott. A Choose utáni állapot lezárva, lásd a következő sort (helyesbítve, job-179). |
| Choose után: a meglévő személyhez rendelés | A csempe-mezőbe írt meglévő név Enter után a People ablak nyílik, a meglévő személy kijelölve, a jóváhagyó gomb **„Choose”** (`job-167`, `job-179`). A Choose-ra kattintva az ablak bezárul, az arc a meglévő személyhez kerül: `Unnamed (5)` → `Unnamed (4)`, `Teszt Elek (1)` → `Teszt Elek (2)`. A `.picasa.ini`-ben egy `[Contacts2]`-bejegyzés marad, mindkét fotó `faces=` sora ugyanarra az azonosítóra mutat (`job-179`). | #5182 (0.9.123) óta a People ablak Choose-útját valódi kattintásos teszt fedi (d789d91de). | Zárva (`job-179`): nincs nyitott tétel. Referencia a megvalósításhoz: a két számláló-változás és a `.picasa.ini` egy `[Contacts2]`-bejegyzése. |
| Arc mellőzése az X-szel és a fejléc gombjával | A csempe X-ére kattintva **„Ignore People”** megerősítés jelenik meg, majd a **„Ignore Person”** jóváhagyása az arcot mellőzöttként menti: `faces=rect64(27c00680d8ffdb3f),ffffffffffffffff` (a `faces=…ffffffffffffffff` kimenet mérése: job-64; a megerősítő ablak külön képkockája: `Colab EN 36`, Colab #63, a leltár 112. sora). Az eredeti fájlkimenet után a mellőzött arc a „Mellőzött emberek” albumba tartozik (15.3/b.1). A fejléc **„Ignore Selected”** gombja csak a kibontott nézetben látszik, kijelölés nélkül szürke (`job-183`, 10. kép). A megerősítő ablak (job-209, 10. kép): cím „Ignore People”; szöveg: „Are you sure you want to move this person to the ignored people album?”; jelölőnégyzet: „Don't ask again, always ignore”; gombok: „Ignore Person” (alapértelmezett) és „Cancel”. A mellőzés után (job-210, 13. kép) a bal sáv sora „Unnamed (5)”, a fejléc „5 Face(s)”, a mellőzött csempe eltűnik, a „Show ignored faces” gomb aktív lesz. A szöveg a binárisban is megvan (28.4/a). | A csempe X és a kibontott nézet fejlécének **„Ignore Selected”** gombja is megerősítést kér (`UnnamedFacesView.qml:417-440, 273-295, 849-909`), majd a FaceScanController mellőzött állapotba teszi az arcot (`face_scan_controller.py:1138-1166`). A csoportosított nézet fejlécében nincs „Ignore Selected” gomb (helyesbítve, job-183). A fejléc „Show ignored faces” gombja akkor aktív, ha van mellőzött arc (`UnnamedFacesView.qml:223-229`); a külön nézetben a „Stop ignoring” visszahozza a kijelölt arcokat (`Main.qml:3275-3280`; `UnnamedFacesView.qml:279-284, 924-949`). A megerősítő ablak szövege, jelölőnégyzete és gombfeliratai egyeznek az eredetivel (`UnnamedFacesView.qml:876-911`; `PeoplePanel.qml:447-473`). | Az X útját és a `.picasa.ini` eredményét a job-64 jegyzete rögzíti. A job-162/163 a kezdeti „Show ignored faces” gombot mutatja, job-163 4. képén szürkén. A megerősítő ablakot és a mellőzött állapotot a job-209/210 lépéssora írja le; a személyszintű mellőzés (N5) külön felvétel. |
| Mellőzött nézet és visszahozás | Az eredetiben a „Show ignored faces” után (job-210, 16. kép) a cím „Ignored people”, alatta „1 Face(s)”; a bal sáv sora „Ignored (1)”; a jobb felső gomb „Back to Unnamed”; az útmutató „Select someone you know and add a name.”; a csempén nincs X, de van „Add a name” mező. A leírás nem említ csempénkénti visszahozó gombot, és a „Back to Unnamed” utáni csempe neve nincs mérve. | A „Show ignored faces” és a „Back to Unnamed” felirata egyezik az eredetivel (`UnnamedFacesView.qml:225`, `:232`). Két eltérés a kódban: a bal sáv sora „Ignored people (N)” (`FolderPane.qml:744`), az eredetinél „Ignored (N)”; a mellőzött nézetben nincs „N Face(s)” sor, mert a `unnamedAlbumFaceCount` (`UnnamedFacesView.qml:249`) csak nem mellőzött módban látszik, az eredetinél „1 Face(s)”. A „Stop ignoring” (`UnnamedFacesView.qml:296`) a kijelölt arcokat hozza vissza; az eredetinél a megfelelő gomb nincs megmérve. | Kész, ha a bal sáv felirata és a darabszám-sor a job-210 szerint jelenik meg (képkocka-összevetéssel), és a visszahozás felvétele (a csempe neve a „Back to Unnamed” után) megvan. |

### 19.1 Nyitott kérdések és megszerzésük

1. **Javaslatelemre kattintás** (a kód megvan: `UnnamedFacesView.qml:650-652`, #5285; a mérés nyitott): nyisd meg a Név nélküliek albumot; a kezdőképkockáról válassz egy csempe „Add a name” mezőt; `kattint [x,y]`, `gepel <meglévő név részlete>`, `var_ablak`; kattints a látható javaslat képére vagy nevére, majd `var_ablak`. Rögzítsd, megnyílik-e a People ablak, megváltozik-e az arc állapota és csökken-e a Név nélküliek száma.
2. **Choose utáni állapot** (lezárva, `job-179`): a csempe-mezőbe írt meglévő név után, a **Choose** gombra kattintva bezárul az ablak, az arc a meglévő személyhez kerül; a `.picasa.ini`-ben egy `[Contacts2]`-bejegyzés marad (lásd a táblázatot).
3. **Escape a csempe mezőjében:** új futásban kattints a csempe mezőjébe, gépelj egy még be nem fejezett nevet, majd `billentyu Escape`, `var_ablak`. Rögzítsd a mező tartalmát, a javaslatpopupot és az esetleges People ablakot.
4. **Ctrl/Shift/húzásos kijelölés** (a Ctrl+A-t a `job-180` már mutatta: mind a hat csempe kijelölve, 15. kép; a többi nyitott): külön futásban kattints egy csempére és rögzítsd az alapot; utána külön próbáld `billentyu Ctrl` + kattintás egy másik csempére, `billentyu Shift` + kattintás egy másik csempére, majd külön `huz [x1,y1] [x2,y2]` két csempe között. Mindegyik után `var_ablak`; a pontokat a ténylegesen kirajzolt képkockáról válaszd ki. Rögzítsd a kijelölt kereteket, a „No Selection”/kijelölésszámot és a tálcát.
5. **Picasa pontos csempe-sorrendje és csoporthatárai:** a job-163 leírása öt csempét soronként és hat arcot nevez meg. A job-208 (9. és 11. kép) az öt oszlopos csoportosított és az egy soros kibontott elrendezést adja, csoporthatárt nem, mert mind a hat csoport egyarcú. A közvetlenül megnyitott `Colab EN 36` (#63, 1280×1024) képkockán a megjelenített arcképkeretek zárt pixelkoordinátákkal mérhetők: `(282-425,195-366)` = 144×172, `(476-619,195-366)` = 144×172, `(670-813,195-366)` = 144×172, `(876-996,195-366)` = 121×172, `(1067-1192,195-366)` = 126×172, a második sorban pedig `(282-425,409-580)` = 144×172 px. Ez a hat kép e képkockán látható viewportja, nem az eredeti képfájl vagy a belső arckivágás forrásmérete; a képernyőn látható sorrend balról jobbra, majd a következő sor. A tartós rendezési kulcs, a csoportcímkék és a többarcú csoporthatár nyitott; utóbbihoz más mintakészlet kell.
6. **A „Learn more...” gomb címe:** **bináris úton megválaszolva (28.2):** a kezelő `0x0074c760`, a sablon `http://picasa.google.com/support/bin/answer.py?hl=%s&answer=156272` (`%s` = futáskor feloldott nyelvkód); a kezelő ezt a `0x00981860` indító rutinjának adja át. A job-175/177 nem mutat külső böngészőablakot, mert a Colab-gépen nincs böngésző. A bináris a megnyitás kezdeményezését bizonyítja, a sikeres weboldalbetöltést nem. A PicasaPy jelenlegi forrásában van URL-építő és `Qt.openUrlExternally` kezelő (`UnnamedFacesView.qml:133-137, 866`); helyi futásidejű eredményt nem mértünk.

*Bizonyítottsági fok: **feltételes** (a job-jegyzetekből átvett képkockák többségének nyers fájlja ebben a munkamenetben nem volt elérhető; kivétel a közvetlenül megnyitott `Colab EN 36` PNG, Colab #63, `kepek-leltar.md`:112) a Név nélküliek nézet címére, útmutatójára, fejlécgombjaira és alapállapotára (job-162; job-163, 4. és 8. kép); az első megnyitás üdvözlőablakára (job-162, 12. kép; a teljes szöveg job-207, 8. kép); a csempe saját mezőjére és az új név People-ablak útjára (job-163, 11-19. kép); a javaslat megjelenésére, a meglévő névhez tartozó Choose ablakra és a People ablak keresőmezőjében használt Escape-re (job-167, 22., 26-34. kép); a Choose utáni állapotra (job-179); a kibontott és a csoportosított nézet fejlécére és csempéire (job-180, job-183); az új név OK utáni állapotára és `.picasa.ini` soraira (job-66; job-167, 18. kép); valamint a csempe-X megerősítő ablakára és a mögötte látható 5+1 rácsra (`Colab EN 36`, Colab #63, leltár `112`; a job-64 külön az ini-kimenetet adja); a mellőzési megerősítő ablak szövegére, jelölőnégyzetére és gombjaira, a mellőzött nézet címére, darabszámára, feliratára és jobb felső gombjára (job-209, job-210); a kibontott és csoportosított nézet fejlécére és csempéire (job-208). A `Colab EN 36` képkockán közvetlen pixelmérésből megvan a hat megjelenített arcképkeret zárt határa és mérete (19.1, 5. pont); ez nem adja meg más felbontások skálázását vagy a tartós rendezési szabályt. **NINCS MEG:** a javaslatelem kattintása, a Ctrl/Shift/húzás kijelölési szabálya, a többarcú csoporthatár és a mellőzött csempe visszahozása (a „Back to Unnamed” utáni csempe neve; külön felvétel). A „Learn more...” cím a 28.2 szerint megvan; a job-167 Escape-je a People ablak keresőmezőjében történt; a csempe-mező Escape-je nyitott (lásd a táblázatot).*

**Helyesbítés:** a korábbi „Név nélküliek névmezője inline panelmező” következtetés kizárólag a jobb fiók fejlécmezőjére (`header_editbox`) vonatkozik. A Név nélküliek csempéjének külön „Add a name” mezőjét a job-163 és a job-66 mutatja; a job-66 nem másik felületi útvonal.

### 19.2 #5337: a bal oldali People-lista és a `peoplepanel.tre` külön felület

**Következtetés.** A `peoplepanel.tre` nem a bal sáv albumlistáját írja le:
az eredeti `rightdrawerpanel/peoplepanel` gyermeke (`rightdrawerpanel.tre:48-53`),
és a jelenlegi `PeoplePanel.qml` is kifejezetten a jobb oldali fiók Emberek-panelje
(5-10. sor). A bal oldali People gyűjtemény a `FolderPane.qml` része; az eredeti
`thumbui.tre` itt csak a `people_toggle` kapcsolót rögzíti (279-281. sor), a
listát nem. Ez a hatókör-eltérés a `peoplepanel.tre` és a megadott felvételek
közti látszólagos ellentmondást feloldja.

**Módszer és forrásjelölés.** A `.tre`-sorok, szülők, horgonyok és módváltások
az eredeti `peoplepanel.tre` 8-82. soraiból valók. A méretek és tervezői
téglalapok a `Picasa3.exe` `runtime/respack.yt` rekordjai; az alábbi táblában
szereplő rekordeltolások decimális fájleltolások. A tervezői téglalap nem írja
felül a `.tre` horgonyát. A `m_hidden` makró kezdeti `setvisible 0` állapotot
ad (`macros.tre:112-113`). A szövegkulcsok a `peoplepanel_text.tre`-ből valók.
Az `.eredeti5337` bemeneti fájlok egyeznek a privát referencia-korpusz azonos
fájljaival. A „NINCS MEG” azt jelenti, hogy a megnevezett forrásból az érték
nem szerezhető meg.

| Eredeti (`peoplepanel.tre`, szöveg és erőforrás) | Nálunk (`PeoplePanel.qml`, `FolderPane.qml`) | Teendő |
|---|---|---|
| `base`: szülő `root`, `m_scaleXY`; `rect: base` = (0,0)-(276,360), 276x360, respack 2623621. A kezdeti láthatóságot a `.tre` nem adja meg. | A `PeoplePanel.qml` gyökérpanelje adja a jobb oldali panelt. A bal oldali lista külön `FolderPane.qml`-rész. | A bal sávhoz nem cél: másik panel gyökere. A jobb panel teljes méret-összevetése külön feladat. |
| `status_label`: szülő `base`, `m_displayfont14`, `m_offsetLT`; 213x14, respack 2624781; `Label peoplepanel/status_label` = „Select a folder to display faces” (`peoplepanel_text.tre:4-5`). A kezdeti láthatóságot és a módváltást a `.tre` nem adja meg. | `PeoplePanel.qml:281-289`, azonos felirat, feltételesen látszik `needsFolderSelection` esetén. | A felirat egyezik; a kezdeti és módváltási láthatóságot a jobb fiókról készült egyező felvétel nélkül NINCS MEG. |
| `instructions`: szülő `peoplelist`; bal+16, jobb-16, felül 0, alul-16; 221x86, respack 2623655. `Text1` és `Text2` teljes üdvözlőszöveg, `Text3` üres Név nélküliek, `Text4` név szerinti album, `Text5` kijelölt fotók (`peoplepanel_text.tre:16-29`). A kezdeti láthatóságot és a módváltást a `.tre` nem adja meg. | `PeoplePanel.qml:340-386` egy `peoplePanelEmptyText` objektummal választja az állapotok szövegét. A teljes első szövegben „PicasaPy” áll, az eredetiben „Picasa”. | A szöveg- és állapotválasztás itt különbözik a horgonyvizsgálattól; a jobb panel módváltásának és horgonyának teljes összevetése a javasolt R2/R3 fejlesztői jegy része. |
| `peoplelist`: szülő `base`, `m_offsetT`, `m_scaleX`, alsó korlát `PEOPLELISTBOTTOM=0`; 260x322, respack 2623638. Kezdeti láthatóságot a `.tre` nem jelöl; a `manual_add` elrejti, a `manual_cancel` újra megjeleníti. | `PeoplePanel.qml:299-338` két `Repeater`-rel jeleníti meg a személyeket és az itt előforduló névtelen arcokat, `PeoplePanelRow.qml` soraival. | Szemantikai megfelelés van, de külön listakeret és `.tre`-horgony nincs; a jobb panel R2/R3 összevetése külön jegy. |
| `manual_add`: szülő `base`, középre, alul-4, kezdetben rejtett; 259x21, respack 2623672. „Add a person manually” (`peoplepanel_text.tre:10-11`); kattintás megjeleníti a `manual_frame`-et, elrejti a `status_label`, `peoplelist` és saját magát, megjeleníti az `editpanel/addfaceselection`-t (`peoplepanel.tre:24-32`). | `PeoplePanel.qml:390-399`, mérete 259x21 és középre igazított, de `visible: !manualAddActive`, tehát a forrásban a kezdeti rejtett állapot nem jelenik meg közvetlenül. | A láthatóság eltérését jobb fiókban kell ellenőrizni; külön R2/R3 fejlesztői jegy. |
| `manual_frame`: szülő `base`, felül+32, alul-32, bal+16, jobb-16, kezdetben rejtett; 239x145, respack 2623689. | `PeoplePanel.qml:402-412` ugyanezt a tervezői méretet és kezdő koordinátát használja (`x=18`, `y=105`), láthatósága `manualAddActive`-től függ. | A fix koordinátás QML-elhelyezés és a `.tre` peremhorgonyzás nem azonos; külön R2/R3 fejlesztői jegy. |
| `manual_instructions`: szülő `manual_frame`, bal+12, jobb-12, felül+12; 221x86, respack 2623706. A saját kezdeti láthatóságát a `.tre` nem adja meg; a szülőkeret kezdetben rejtett. | `PeoplePanel.qml:413-431`, a QML koordinátái a kereten belül `x=9`, `y=6`, mérete 221x86. | Bizonyított forráseltérés: `.tre` horgonya +12/+12, QML koordinátája 9/6. Külön R2/R3 fejlesztői jegy; a mérőfelvétel tisztázza a futásidejű eredetit. |
| `manual_cancel`: szülő `manual_frame`, középre, `YConstraint 0,0,285`; a Cancel felirat (`peoplepanel_text.tre:13-14`), 98x28, respack 2623723. Kezdetben a rejtett szülővel rejtett; a gomb elrejti a keretet és az `editpanel/addfaceselection`-t, visszakapcsolja a `status_label`, `peoplelist` és `manual_add` elemeket, Escape-kezelő is van (`peoplepanel.tre:38-46`). | `PeoplePanel.qml:433-441`, 98x28-as Cancel gomb a kereten belül, `x=71`, `y=105`. | A `.tre` függőleges korlátja és a QML koordinátája eltér; a felvételek nem mutatnak jobb fiókot. Külön R2/R3 fejlesztői jegy. |
| `cancel_icon`: szülő `manual_cancel`, `m_offsetRT`; 15x15, respack 2623740. Kezdetben a szülővel rejtett. | A jelenlegi Cancel gomb szöveges, külön ikonobjektum nem szerepel a `PeoplePanel.qml`-ben. | Bizonyított szerkezeti eltérés; külön R2/R3 fejlesztői jegy. |
| `ignore-label`: szülő `ignore`, `m_buttonfontC`; feliratkulcs „Ignore” (`peoplepanel_text.tre:7-8`); saját respack-méret NINCS MEG, külön réteg-rect nincs. A `.tre` nem ad meg saját láthatóságot; kezdetben rejtett szülő alatt van. | `PeoplePanelRow.qml:239-271` az X vezérlőt „Ignore person” buboréksúgóval mutatja, külön „Ignore” feliratobjektum nélkül. | A szöveges gyermek és X-vezérlő megfeleltetése nyitott. A méret megszerzési útja: eredeti jobb fiók felvétele azonosított skálán, a szülővel együtt. |
| `ignore`: szülő `base`, `m_offsetLT`, `m_buttontypecolor`, kezdetben rejtett; 163x17, respack 2624730. Későbbi megjelenítési feltétele NINCS MEG a `.tre`-ből. | `PeoplePanelRow.qml:239-271` 13x13-as X-et tesz az arckép jobb felső sarkára; az elem látható, csak a kattintás tiltott megnevezett sornál. | Eltér a szülő, méret és kezdeti láthatóság; külön R2/R3 fejlesztői jegy. |
| `addname`: szülő `base`, `m_buttontypecolor`, `m_offsetLB`, kezdetben rejtett; 163x20, respack 2624713; szövege „Add a name” (`peoplepanel_text.tre:1-2`). Későbbi megjelenítési feltétele NINCS MEG a `.tre`-ből. | `PeoplePanelRow.qml:149-167` az arcnév mezőt a soron belül mutatja, 22 magas `TextField`-ként, névtelen arcnál. | Szülő, méret, vezérlőtípus és kezdeti láthatóság eltér; külön R2/R3 fejlesztői jegy. |
| `suggestion_yes` és `suggestion_no`: mindkettő szülő `base`, `m_offsetLB`, kezdetben rejtett; 27x22, respack 2624747 és 2624764. Későbbi megjelenítési feltétel NINCS MEG a `.tre`-ből. | `PeoplePanelRow.qml:169-223` azonos 27x22-es gombokat rajzol a soron; csak névtelen arcnál és nem üres javaslatnál látszanak. | A méret egyezik, a szülő/horgony eltér; az eredeti megjelenítési feltétel NINCS MEG a `.tre`-ből. Külön R2/R3 fejlesztői jegy. |

#### A bal oldali People gyűjtemény a felvételeken

Az alábbiak nem `peoplepanel.tre`-elemek. A `j4_ignored_nezet.png`,
`j4_megerosites.png`, `j4_mellozes_utan.png` és `kepernyo__29.png` képeken
látható bal lista a `FolderPane.qml` megfelelője. A képfájlokat 1280x1024
felbontásban kaptuk. A képernyőpixelek és a Qt logikai mértékegységek közti
skálázás NINCS MEG, ezért a két oszlop méretadata nem tekinthető közvetlenül
azonos egységű összevetésnek.

| Eredeti (felvétel) | Nálunk (`FolderPane.qml`) | Teendő |
|---|---|---|
| People fejléc: `People (1)` a job-210-hez adott Ignored képen, `People (2)` a job-213 29. képén. | 592-603. sor: a fejléc `peopleModel.length` + a látható Név nélküliek sor számát mutatja; a `ignoredFaceCount` nincs beleszámítva. | A job-210 Ignored állapotában a látható `Ignored (1)` sor mellett `People (1)` látszik. A jelenlegi képlet ezt a sort nem számolja; külön fejlesztői jegy. |
| Név nélküliek sor: `Unnamed (6)` a job-210-hez adott megerősítési képen, `Unnamed (4)` a job-213 képen. Kijelölt sáv pixelmérése: 40 képpont magas. | 605-654. sor: `Unnamed (N)`, látható, ha a gyűjtemény nyitott és van arc vagy keresés folyik; QML-sor 22 logikai egység, ikon 18x18. | A felirat és a feltételes megjelenés egyezik. Méretpontos eltérés a DPR/Qt-skála mérése nélkül NINCS MEG. |
| Személy-sor: `Teszt Elek (2)` a job-213 29. képen; kijelölt sor pixelmérése 38 képpont. | 656-719. sor: `modelData.name (count)`, QML-sor 22 logikai egység, név nélküli bélyeg 10x10, képbélyeg 18x18. | A mért pixel és a QML-logikai méret közti átváltás NINCS MEG; egyező felbontású PicasaPy-kép kell az összehasonlításhoz. |
| Mellőzött sor: `Ignored (1)` a job-210-hez adott Ignored képen; kijelölt sáv pixelmérése 40 képpont, People fejlécszám 1. | 721-766. sor: `Ignored people (N)`, QML-sor 22 logikai egység; a számláló nem része a People fejléc képletének. | Két közvetlen eltérés: a felirat és a csoportdarabszám. Külön fejlesztői jegy, az Eredeti sort és kész feltételeket lásd a javasolt törzsben. |

**Két független út és cáfolás.** A út: a teljes `peoplepanel.tre` leltára,
a szülőlánc a `rightdrawerpanel.tre`-ben, valamint a `thumbui.tre` kapcsolója
elkülöníti a jobb oldali fiókot a bal lista-vezérlőjétől. B út: a megadott
képek bal sávja, a `FolderPane.qml` saját People-gyűjteménye és a
`ui-lefedettseg.md` `peoplepanel`/`thumbui` sora ugyanazt a különválasztást
mutatja. A két út egyezik. Cáfoló feltevésként azt vizsgáltuk, hogy a bal
oldali `Unnamed`, `Ignored` és személy sorok a `.tre` elemei. A 14 elemű
`.tre` leltárban nincs ilyen sor vagy feliratkulcs, a szülője a jobb fiók,
a képek pedig a bal oldali albumlistát mutatják; a feltevés megbukott.
Ellenőrzésként a respack `peoplepanel` rétege (offset 3095476) és a bal
oldali `thumbui/people_toggle` (`thumbui.tre:279-281`) is más-más felületet
azonosít. A cáfolatot ugyanezzel a forráskritériummal ellenőriztük.

**Fejlesztési következmény.** A `.tre`-ből hiányzó bal oldali listát nem
szabad belőle rekonstruálni. A bal lista két igazolt eltérése a `FolderPane`
felirata és számlálója; a jobb oldali panel strukturális eltérései külön
R2/R3 feladatot igényelnek, mert a rendelkezésre álló felvételek nem mutatják
azt a panelt.

### 19.3 #5336: a Név nélküliek fejlécének TRE-összevetése

**Kérdés:** a `unknownfaceheaderpanel.tre` minden deklarációja, annak szülője,
horgonyzása, mérete, kezdő láthatósága és módváltása megfelel-e a mai
`UnnamedFacesView.qml` fejlécének, valamint a rendelkezésre álló eredeti
felvételeknek.

**Források és korlátok:** a munkafa `.eredeti5336/unknownfaceheaderpanel.tre`,
`unknownfaceheaderpaneltext.tre` és `macros.tre` fájljai; a Picasa3.exe
`runtime/respack.yt` erőforráscsomagja; a helyi
`.eredeti5336/j1_csoportositott.png`, `j1_kibontott.png`, `j4_megerosites.png`,
`j4_ignored_nezet.png` és `j4_mellozes_utan.png` képek; a
`src/picasapy/app/qml/PicasaPy/UnnamedFacesView.qml` és `Main.qml`.
Mind az öt helyi PNG 1280×1024 képpontos. Külön `job-207` nevű kép nincs a
munkafában. A 19. szakasz korábbi felvétel-leírása a job-207 8. képét
ismerteti, de ebben a körben azt a képet nem lehetett újra megvizsgálni.
Ezért a `j1` és `j4` fájlnevek alapján megfigyelt állapotokat külön jelölöm,
nem tulajdonítok nekik bizonyítatlan job-azonosítót. A 19. szakasz korábbi
leírása a job-208-at J1-hez, a job-209/210-et J4-hez rendeli; a helyi
fájlnevek ezt önmagukban nem bizonyítják.

Az eredeti recteket a `respack.yt` rétegfejléceiből olvastam ki. A méret a
rect két végpontjának különbsége. A `m_offsetLT` a bal és felső eltolást,
`m_offsetRT` a jobb és felső eltolást tartja meg; `m_scaleX` a két vízszintes
szélt, `m_offsetT` a felső szélt köti a szülőhöz; `m_hidden` a kezdeti
láthatóságot nullára állítja (`macros.tre:21-23, 50-51, 63-65, 93-95,
112-113`). A táblázat eredeti rectjei a 532×90-es erőforrás-vászon
koordinátái, nem állítások a QML képpontjairól.
Az `m_fakehidden` makró a `macros.tre`-ben definiált, de a vizsgált panel
18 deklarációja közül egyik sem használja.

A munkafa `HEAD` értéke `78c862ed` (#5333/#5334), és egy commit-tal
lemarad a helyi `origin/main` `2f2561cb5` állapotától. Ez utóbbi a #5328/#5335
végleges commitja, közvetlenül a HEAD után. A korábbi `8a637ac0` #5328
ág-commit külön ágon maradt, és nem őse sem a HEAD-nek, sem az `origin/main`
végleges commitjának. A „Nálunk” összevetés az `origin/main` QML-jét
használja, mert az tartalmazza a kérésben megnevezett #5328-at. A munkafa
QML-je még a régebbi állapot, ezért nem módosítottam, és a specben ezt a
forráseltérést külön rögzítem.

| Eredeti | Nálunk (`UnnamedFacesView.qml`) | Teendő |
|---|---|---|
| `album_title`, TRE:5-8. Szülő `album_title_clip`, `m_offsetLT`; `Property fontname Georgia`, `Property fontsize 24`; kezdetben látható. Respack `0x0033c77f`, rect `(52,14)-(429,35)`, 377×21. A text TRE nem ad hozzá feliratkulcsot. | `unnamedAlbumTitle`, az `unnamedTitleBlock` `RowLayout` gyermeke, QML:190-196; explicit szélesség/magasság nincs. „Unnamed people” vagy „Ignored people”; 18 px a `Theme.fontSize + 6` alapján, explicit betűcsalád nincs. | **D1 fejlesztői jegyjavaslat, a cím tipográfiájának egyeztetése.** Eredeti: `unknownfaceheaderpanel.tre:5-8`, respack `0x0033c77f`. Nálunk a család nincs megadva, a méret 18 px. Teendő: a cím betűcsaládját és mért megjelenő méretét a Picasa felvételével összevetni; eltérés esetén egyeztetni. Kész, ha az eredeti és a PicasaPy képkockáján a cím rectje, sortörése és betűképe dokumentáltan összevethető. |
| `album_title_clip`, TRE:10-13. Szülő `headerbase`, `m_offsetLT`, aktív `XConstraint 1,1,-90`; a `#XConstraint 0,0,16` megjegyzés, nem aktív; kezdetben látható. Respack `0x0033c76e`, `(52,13)-(440,45)`, 388×32. | A cím `Text` közvetlenül az `unnamedTitleBlock` `RowLayout`-jában van, QML:176-197; explicit `clip` vagy `elide` nincs. | A D1 fejlesztői jegyjavaslat része. Eredeti: `unknownfaceheaderpanel.tre:10-13`, respack `0x0033c76e`. Kész, ha hosszú címnél a vágási határ is képkockán ellenőrzött, és a QML-ben az eredeti működéssel egyező viselkedés van, vagy dokumentáltan eltérő termékdöntés születik. |
| `faceicon`, TRE:15-16. Szülő `headerbase`, `m_offsetLT`; kezdetben látható. Respack `0x0033b209`, `(11,12)-(47,48)`, 36×36. | `unnamedTitleIcon`, QML:182-189, az `unnamedTitleBlock` `RowLayout` első gyermeke, 36×36; forrása `icons/person-silhouette.svg`. | A méret és a cím melletti szerep megfelel. A Qt-erőforrás és a Picasa réteg azonossága nem követelmény ebben a szülő/horgony összevetésben; képi azonosságról nincs mérés, ezért erre nincs fejlesztői teendő. |
| `info_text`, TRE:18-19. Szülő `headerbase`, `m_offsetLT`; kezdetben látható. Respack `0x0033c74c`, `(12,57)-(297,78)`, 285×21. A text TRE-ben nincs hozzá feliratkulcs. | `unnamedAlbumFaceCount`, az `origin/main` QML:241-259 sorai szerint az `unnamedFaceRow` `RowLayout` gyermeke; bal margója -16, függőleges igazítása középre; 12 px betűméretet kér (`Theme.buttonLabelSize`); explicit szélessége és magassága nincs. A munkafa HEAD-jében még 10 px szerepel. | **Mérés nyitott.** A TRE nem ad a `info_text`-hez szövegkulcsot vagy betűméretet. A j1 képek az arcszámlálót mutatják, de a jelenlegi QML kimenetéről nincs azonos méretű felvétel. A doboz- és betűméretet csak két összevethető képkocka pontos mérése döntheti el. |
| `cluster`, TRE:24-28. Szülő `clustering_container`, `m_offsetLT`; kezdetben rejtett; `hidetarget` saját maga, `showtarget` `showall`. Respack `0x0033aeb2`, `(278,14)-(398,41)`, 120×27. Textkulcs: `unknownfaceheaderpanel/cluster`, „Group by face”. | A `clusterToggleButton`, az `origin/main` QML:199-209 soraiban a fejléc `RowLayout` gyermeke, `PicasaButton`, 120×27 és 12 px; kibontva „Group by face” feliratú. | **Nem cél azonos natív elemfa.** A QML egy gombbal valósítja meg a két feliratú váltást. A QML és a TRE deklarált mérete egyezik; a j1 csoportosított/kibontott képek a feliratot és állapotot támasztják alá. A külön TRE-gyerek helyett egy Qt-gomb használata önmagában nem eltérés. |
| `showall`, TRE:30-33. Szülő `clustering_container`, `m_offsetLT`; kezdetben látható; `hidetarget` saját maga, `showtarget` `cluster`. Respack `0x0033aea1`, ugyanaz a `(278,14)-(398,41)`, 120×27 rect. Textkulcs: `unknownfaceheaderpanel/showall`, „Expand groups”. | Ugyanaz a `clusterToggleButton`, az `origin/main` QML:199-209 soraiban; csoportosítva „Expand groups” feliratú. Kezdő mód `grouped: true`, QML:27. | **Nem cél azonos natív elemfa.** A kezdeti „Expand groups” felirat és a kibontott mód „Group by face” felirata a `j1_csoportositott.png` és `j1_kibontott.png` képeken látszik. Az állapotváltó szerkezetet a TRE, a QML és a képek egymástól függetlenül támasztják alá. |
| `clustering_container`, TRE:35-36. Szülő `headerbase`, `m_offsetRT`; kezdetben látható. Respack `0x0033ae90`, `(278,14)-(398,41)`, 120×27. | Nincs külön név szerinti Qt-konténer; maga a gomb a fejléc `RowLayout`-jának gyermeke, a kitöltő `Item` után, QML:170-209. | **Nem cél a szülő objektum azonossága.** A QML `RowLayout` a gyermekek sorrendjét és helyét adja, a gomb mérete és a két állapot felirata megegyezik a mért eredeti réteggel. A pontos képernyő-koordináta egyezése nincs QML-képkockán mérve. |
| `showignored`, TRE:38-41. Szülő `viewtype_container`, `m_offsetLT`; kezdetben látható; önmagát rejti, `showunknown`-t mutatja. Respack `0x0033ae7f`, `(403,14)-(523,41)`, 120×27. Textkulcs: `unknownfaceheaderpanel/showignored`, „Show ignored faces”. | `unknownfaceheaderpanel/showignored`, az `origin/main` QML:216-224 soraiban a `unknownFaceViewTypeContainer` gyermeke, `PicasaButton`, 12 px; nem Mellőzött módban látszik, `hasIgnoredFaces` hamis értékénél letiltott. | A két mód közti láthatóság egyezik a j1 és j4 képekkel. A TRE nem deklarál letiltást; a QML `hasIgnoredFaces` feltétele erre külön szabály. A j1 képen a gomb szürke, a `j4_mellozes_utan.png` képen aktív. Ez a letiltási feltétel nem része a kért TRE-horgony, méret és módonkénti láthatósági összevetésnek, ezért ebben a feladatban nem cél. |
| `showunknown`, TRE:43-47. Szülő `viewtype_container`, `m_offsetLT`; kezdetben rejtett; önmagát rejti, `showignored`-t mutatja. Respack `0x0033ae6e`, ugyanaz a `(403,14)-(523,41)`, 120×27 rect. Textkulcs: `unknownfaceheaderpanel/showunknown`, „Back to Unnamed”. | `unknownfaceheaderpanel/showunknown`, az `origin/main` QML:225-232 soraiban ugyanabban a 120×27-es konténerben, `PicasaButton`, 12 px; csak `ignoredMode` esetén látható. | A kezdő rejtettség és a mellőzött mód láthatósága egyezik a j1 és `j4_ignored_nezet.png` képekkel. Nincs további teendő ehhez a sorhoz. |
| `viewtype_container`, TRE:49-50. Szülő `headerbase`, `m_offsetRT`; kezdetben látható. Respack `0x0033ae5d`, `(403,14)-(523,41)`, 120×27. | `unknownFaceViewTypeContainer`, a fejléc `RowLayout` gyermeke, QML:211-233, 120×27; a két gomb `anchors.fill`-lel ugyanazt a rectet tölti ki. | **Nem cél a natív szülőazonosság.** A két gyermek a megfelelő módokban ugyanazon méretű helyen jelenik meg; a QML-konténer megfelelteti a TRE konténer szerepét. |
| `ignore`, TRE:53-56. Szülő `headerbase`, `m_offsetRT`; kezdetben rejtett; `SharedHandler` a `hottip_label`-hez. Respack `0x0033b03b`, `(403,56)-(523,83)`, 120×27. Textkulcs: `unknownfaceheaderpanel/ignore`, „Ignore Selected”; tooltip: „Ignore all of the selected faces”. | `ignoreFacesButton`, az `origin/main` QML:302-315 soraiban az `unnamedFaceRow` `RowLayout` gyermeke, középre igazítva; `PicasaButton`, 120×27, 12 px; csak kibontott Név nélküliek módban látható. A tooltip szövege megvan. A munkafa HEAD-jében még a #5328 előtti egyszerű `Button` van. | **Nincs fejlesztői teendő az `origin/main` állapotán.** Eredeti: `unknownfaceheaderpanel.tre:53-56`, respack `0x0033b03b`, 120×27. A #5328/#5335 QML sora `PicasaButton`, 120×27 és 12 px; ez a deklarált méretet egyezteti. A munkafa kódja elmaradt ettől az `origin/main` állapottól. |
| `addname_instructions`, TRE:58-63. Szülő `headerbase`, `m_offsetLT`, `m_displayfont12`, kezdetben rejtett, aktív `XConstraint 1,1,-16`, `textwrap 0`. Respack `0x0033b0a9`, `(52,42)-(523,55)`, 471×13. A text TRE-ben nincs feliratkulcs. | A `unnamedInstructions`, QML:336-346, mindig látszik és a `root.instructionText` szöveget adja. A QML gyökér `ColumnLayout`-jának eleme, nem a fejlécé. | **Nem azonosított közvetlen pár, nincs eldöntött eltérés.** A Picasa3.exe diszasszemblálása `0x0074c8f0` címen az `instructionpanel/body` elemet is hivatkozza; a látható útmutató külön paneltartalom lehet. A `j1` képek látható útmutatója nem bizonyítja, hogy a TRE-ben rejtett `addname_instructions` vált láthatóvá. Kész fejlesztői teendő csak az elem és a külön útmutató-panel kapcsolatának bináris vagy felvételes bizonyítása után adható. |
| `hottip_label`, TRE:65-68. Szülő `headerbase`, `m_offsetRT`, `m_displayfont12`, jobbra igazított; kezdetben látható, nincs rejtést beállító makró. Respack `0x0033c75d`, `(210,42)-(523,55)`, 313×13. A text TRE-ben nincs közvetlen label szöveg. | Külön QML `Text` nincs. Az Ignore gombhoz van `ToolTip`; a névmezőhöz az `origin/main` QML-ben nincs tooltip. QML:266-284, 302-315. | **D2 fejlesztői jegyjavaslat, tooltip-kötés összevetése.** Eredeti: `unknownfaceheaderpanel.tre:56,65-68,74` és text TRE:18-25. Nálunk csak az Ignore tooltipje van kifejezetten a gombhoz kötve. Kész, ha a Picasa hover-felvételén az `addname` és `ignore` tooltipje, a megjelenési helyük és a QML viselkedése össze van vetve; csak a mért eltérést kell javítani. |
| `addname`, TRE:70-74. Szülő `headerbase`, kezdetben rejtett, `m_offsetRT`, `m_buttontypecolor`, `SharedHandler` a `hottip_label`-hez. Respack `0x0033b098`, `(235,60)-(398,80)`, 163×20. Textkulcs: `unknownfaceheaderpanel/addname`, „Add a name”; tooltip: `Assign a name to all of the selected faces`. | `unnamedNameField`, az `unnamedFaceRow` `RowLayout` gyermeke, QML:269-284; függőlegesen középre igazított `TextField`, 162×20; kibontott Név nélküliek módban látszik, placeholder „Add a name”. Nincs tooltip a mezőn. | **D2 fejlesztői jegyjavaslat, méret és tooltip felmérése.** Eredeti: `unknownfaceheaderpanel.tre:70-74`, respack `0x0033b098`, 163×20. Nálunk a deklarált szélesség 162 px, a tooltip hiányzik a mezőről, és a vezérlő Qt `TextField`. Kész, ha az eredeti kibontott képkocka alapján a szélesség és hover-viselkedés pontosan össze van mérve, és az eltérés javítva vagy a Qt-s szövegmezőre vonatkozó döntés indoklással dokumentálva van. |
| `shadow`, TRE:79-81. Szülő `headerbase`, `m_scaleX`, `m_offsetT`; kezdetben látható. Respack `0x0033958e`, `(0,86)-(532,90)`, 532×4, áttetsző árnyékréteg. | Nincs külön `shadow` nevű elem a fejléc QML-jében; a nézetet tartalmazó `Main.qml` `Rectangle`-je a `Theme.contentPanel` színű, QML:3595; ez világos témában `#ffffff`, sötétben `#2e2e2e` (`Theme.qml:61`). | **D3 fejlesztői jegyjavaslat, fejléc felületének összevetése.** Eredeti: `unknownfaceheaderpanel.tre:79-81`, respack `0x0033958e`. Nálunk nincs külön 4 px-es fejlécárnyék. Kész, ha a Picasa és a QML fejléc határát képkockán összevetették, és az árnyék jelenlétéről vagy szándékos elhagyásáról dokumentált döntés született. |
| `headerbase0`, TRE:83-85. Szülő `root`, `m_scaleX`, `m_offsetT`; kezdetben látható. Respack `0x0033957d`, `(0,0)-(532,86)`, 532×86, kitöltése `#eaeaea`. | Nincs azonos nevű QML elem. A gazda `Main.qml` tartalom-`Rectangle`-je a `Theme.contentPanel` színű, QML:3595; ez világos témában `#ffffff`, sötétben `#2e2e2e` (`Theme.qml:61`). | **D3 fejlesztői jegyjavaslat, háttérszín egyeztetése.** Eredeti: `unknownfaceheaderpanel.tre:83-85`, respack `0x0033957d`. A QML gazda sötét témában `#2e2e2e`, világosban `#ffffff`. Kész, ha a felületi tartomány két képkockáján a háttér összehasonlított, és a színeltérés javítva vagy tudatos termékdöntésként rögzítve van. |
| `headerbase1`, TRE:87-90. Szülő `root`, `m_scaleX`, `m_offsetT`; `m_hidden`, kezdetben rejtett. Respack `0x0033956c`, `(0,0)-(532,86)`, 532×86, kitöltése `#f8f8f8`. | Nincs vele azonos nevű vagy dokumentált alternatív `headerbase1` QML-állapot. | **Nem cél a rejtett alternatív erőforrásréteg átvétele**, mert az eredeti TRE is kezdetben elrejti, és a vizsgált j1/j4 felvételek nem mutatnak külön kapcsolást. Más mód aktiválását ez a kör nem vizsgálta. |
| `headerbase`, TRE:92-94. Szülő `root`, `m_scaleX`, `m_offsetT`; látható, átlátszó szerkezeti réteg. Respack `0x0033955b`, `(0,0)-(532,86)`, 532×86. | Nincs azonos nevű QML-csomópont. A gyökér `ColumnLayout` és a cím `RowLayout` adja a Qt szerkezeti elrendezést, QML:170-197. | **Nem cél a natív csomópontfa másolása.** A Qt elrendezési objektumok a viselkedési szerepet veszik át. A QML és a Picasa képernyő-koordinátájának pixelpontos egyezése külön mérés nélkül nem állítható. |

#### 19.3.1 Módonkénti láthatóság és a felvételek viszonya

| Mód | A TRE-ből várt állapot | Helyi eredeti kép | Jelenlegi QML |
|---|---|---|---|
| Kezdő, csoportosított Név nélküliek | `showall` látható, `cluster` rejtett; `showignored` látható, `showunknown` rejtett; `ignore` és `addname` rejtett. | `j1_csoportositott.png`: „Expand groups”, „Show ignored faces”; a két fejlécművelet rejtett. | `grouped: true`; azonos feliratok és láthatóság. |
| Kibontott Név nélküliek | A `cluster` váltásával a csoportgomb vált feliratot. A `ignore` és `addname` kezdő rejtett állapotból való megjelenítését a vizsgált TRE deklaráció nem tartalmazza. | `j1_kibontott.png`: „Group by face”, látható névmező és „Ignore Selected”. | `!ignoredMode && !grouped` feltétellel a két vezérlő látható. Ez a felvétel és a QML állapot között egyezik, de a váltást ez a TRE-részlet nem magyarázza. |
| Mellőzött nézet | `showunknown` váltógomb látható, `showignored` rejtett; `cluster`/`showall` váltó továbbra is deklarált. | `j4_ignored_nezet.png`: „Ignored people”, „Back to Unnamed”; az útmutató látható. | `ignoredMode` megfordítja a két nézetváltó gomb láthatóságát. |
| Mellőzés után visszatért Név nélküliek | A mellőzött arc kiesése önmagában nem TRE-módváltó szabály. | `j4_mellozes_utan.png`: az arcszám 6-ról 5-re változik, „Show ignored faces” aktív. | A `hasIgnoredFaces` állapot aktiválja a gombot. |

**A TRE és a képek közti kimondandó eltérés:** a `j1_kibontott.png` képen a
`addname` és az „Ignore Selected” látszik, a TRE viszont mindkettőt
kezdetben rejti, és ehhez a két elemhez nem ad `showtarget` vagy
`hidetarget` deklarációt. Ez nem cáfolja a képen látott kibontott állapotot,
de a bemásolt TRE önmagában nem magyarázza a vezérlők előhozását. A QML
explicit mód-feltételei ezt a láthatóságot megvalósítják. A látható útmutató
nem bizonyítja a TRE-ben rejtett `addname_instructions` megjelenését: a
bináris diszasszemblálás `0x0074c8f0` az `instructionpanel/body` nevet is
használja. A `hottip_label` hover nélküli képeken nem ítélhető meg.

#### 19.3.2 Bizonyítottság, független utak és cáfoló kör

**Bizonyítottsági fok: feltételes az egész összevetésre.** A TRE-sorok,
makrók, QML-tulajdonságok és erőforrás-rectek pontosan kiolvashatók. A két
váltópár állapotát a TRE és a QML mellett a j1/j4 képek is alátámasztják.
Az egész panel pixelpontos egyezése azonban nincs mérve PicasaPy-képkockán,
a job-207 kép nincs helyben, és a HEAD nem tartalmazza a #5328 változásait.

**A két független út:**

- **A út, deklaráció és kód:** kézzel feloldott TRE és `macros.tre`, a
  `respack.yt` rect-rétegei, majd az `origin/main` #5328 utáni QML-jének közvetlen olvasása.
  Ez megerősíti a deklarált szülőket, horgonyokat, méreteket, kezdeti
  rejtettséget, feliratokat és a QML-ben kifejezett mód-feltételeket.
- **B út, a forrástól független felvétel:** a helyi j1/j4 képeken külön
  ellenőriztem a két váltópár feliratait, helyét és a rejtett, illetve látható
  vezérlőket. A képek megerősítik a két mód váltását, de nem mérik a QML
  renderét, és nem mutatnak tooltipet.
- **Egyezés:** a csoportosítási és nézetváltó feliratok, az alternáló
  láthatóság, valamint a kibontott fejléc két művelete egyezik. A TRE a két
  művelet váltásának okát nem deklarálja; ez a rész feltételes marad.

**Cáfoló kísérlet:** a cáfolandó állítás az volt, hogy a `cluster/showall` és
a `showignored/showunknown` négy különböző, egymástól eltérő helyű gomb.
Megpróbáltam ezt a TRE show/hide céljaival, a `respack.yt` rect-rétegeivel és
a j1/j4 képekkel megcáfolni. A cáfolat sikerült: a két pár külön helyet foglal
el, de mindkét pár tagjai páronként ugyanazon 120×27 recten váltanak. A
következtetést ugyanazzal a mércével ellenőriztem: TRE-állapot és cél,
erőforrás-réteg rectje, valamint a képeken olvasható felirat. Mindhárom út
ugyanazt mutatja.

#### 19.3.3 A #5336 „Kész, ha” pontjai

1. **A TRE minden eleme táblázatban van:** ✅ mind a 18 deklaráció külön sor,
   a szülővel, horgony/makró feloldással, respack recttel és mérettel,
   kezdeti láthatósággal, szövegkulccsal, QML-megfelelővel és teendővel.
2. **Minden eltérés indokoltan nem cél vagy fejlesztői jegyjavaslat:** ✅ a
   natív csomópontfa eltérései indokoltan nem célok; a cím, tooltip, árnyék
   és háttér vizuális eltérései a D1-D3 fejlesztői jegyjavaslatokban szerepelnek; a #5328 a gombméretet már
   egyezteti az `origin/main` forrásában az eredeti TRE-sorral. Az útmutató
   közvetlen megfelelése és a számláló pontos renderelt mérete nyitott,
   mivel nincs döntő bizonyíték.
3. **A felvétel és a TRE ellentmondása kimondva:** ✅ a kibontott képen
   látható `addname` és `ignore` vezérlő kezdő rejtettsége és hiányzó TRE
   váltódeklarációja rögzítve. A külön útmutatópanelt és a hover nélküli
   tooltipet nem állítottam bizonyítatlan ellentmondásnak.

#### 19.3.4 Javasolt fejlesztői jegyek

Ezek jegytörzs-javaslatok, nem létrehozott GitHub-jegyek. A pixeleltérések
igazítását csak összevethető felvételek után javaslom.

**D1. Cím betűképe és vágása**

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `unknownfaceheaderpanel.tre:5-13`, `album_title` és `album_title_clip`, Georgia 24, cím rect 377×21, klip 388×32. | `UnnamedFacesView.qml:190-196`, alap betűcsalád, 18 px, explicit klip nincs. | Két azonos méretű nézetképen mérni a cím betűképét, rectjét és a hosszú cím vágását; csak a mért eltérést igazítani. |

**Kész, ha:** a csoportosított, kibontott és mellőzött állapot címének
rectje, betűképe és hosszú címnél a vágási határ összevethető képkockán van
mérve, az eltérés pedig javítva vagy indokoltan dokumentálva.

**D2. Névmező és tooltip**

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `unknownfaceheaderpanel.tre:65-74`, `hottip_label`, `addname`, `ignore`; respack `addname` `0x0033b098`, 163×20. A text TRE az `addname` tooltipjét is megadja. | A `TextField` 162×20, saját tooltip nélkül; külön `hottip_label` nincs. Az Ignore gomb tooltip-szövege a QML-ben megvan. | Az eredeti felvételen a két fejlécvezérlő hover-szövegét, helyét és a mező méretét mérni; a mért eltéréshez igazítani vagy a Qt-s szövegmezőről dokumentált döntést rögzíteni. |

**Kész, ha:** az `addname` és `ignore` hover-viselkedése, a mező pontos
szélessége és a tooltip helye képkockán össze van vetve, a döntés és az
esetleges javítás rögzítve.

**D3. Fejléc háttér és árnyék**

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `unknownfaceheaderpanel.tre:79-94`, `shadow`, `headerbase0`, `headerbase1`, `headerbase`; respack 532×4-es árnyék, 532×86-os rétegek, a látható háttér `#eaeaea`. | Nincs külön shadow vagy base réteg a QML-ben; a gazda tartalomfelület a `Theme.contentPanel` színt használja, világos témában `#ffffff`, sötétben `#2e2e2e`. | A Picasa és a QML fejléc határát összevetni; a mért háttér- vagy árnyékkülönbséget javítani, vagy az elhagyást tudatos döntésként dokumentálni. |

**Kész, ha:** a fejléc teljes háttérhatára és árnyéka összevethető
képkockán van mérve, és mindkettő egyező vagy indokoltan eltérő.

#### 19.3.5 Nyitott kérdések

- A `job-207` 8. képének helyi másolata hiányzik; a korábbi leírás megvan, de
  az eredeti kép újbóli vizsgálata `NINCS MEG`.
- A `hottip_label` és az `addname` tooltipjének tényleges megjelenési
  állapota hover-felvételen nincs mérve.
- Az eredeti TRE által nem deklarált `addname` és `ignore` módváltás
  forrása nincs meg. A `0x00749ba0` függvény diszasszemblálása önmagában nem
  oldja fel az állapotmezők és az indirekt hívások szerepét. A célzott kérés:
  `Ghidra-kör kell: 0x00749ba0 - mely állapotfeltételek mutatják vagy rejtik az addname és ignore elemeket a csoportosított, kibontott és mellőzött módban, és melyik vezérlő váltja ezeket [blokkoló]`.
- A PicasaPy aktuális renderelt fejlécének képkockája hiányzik, így az
  erőforrás-rectek és a QML-képpontok pixelpontos összevetése `NINCS MEG`.

### 19.4 #5343: a fejléc `addname` és `ignore` elemének állapotfeltételei (2026-10-19, 11. Ghidra-kör)

**Kérdés.** Mely állapotok mutatják vagy rejtik a fejléc `addname` („Név hozzáadása”) és `ignore` („Kijelöltek mellőzése”) elemét csoportosított, kibontott és mellőzött módban, és melyik vezérlő váltja őket? Forrás: a `0x00749ba0` C-törzse (`.ghidra11/2026-10-19-ghidra-11.txt`, 1-759. sor), a bináris-index `string_xrefs` táblája, és a `referencia/tre-eroforrasok/unknownfaceheaderpanel.tre`.

**A TRE-összevetés.** A fejléc elemeinek kezdeti láthatósága és váltópárja a TRE-ben:

| elem | kezdeti láthatóság | váltópár | TRE-sor |
|---|---|---|---|
| `cluster` („Csoportosítás arcok szerint”) | rejtett | `showall` ↔ `cluster` | 24-28 |
| `showall` („Csoportok részletes nézete”) | látszik | `showall` ↔ `cluster` | 30-33 |
| `showignored` („Mellőzött arcok megjelenítése”) | látszik | `showignored` ↔ `showunknown` | 38-41 |
| `showunknown` („Vissza ide: Név nélküliek”) | rejtett | `showunknown` ↔ `showignored` | 43-47 |
| `ignore` („Kijelöltek mellőzése”) | rejtett | nincs pár | 53-56 |
| `addname` („Név hozzáadása”) | rejtett | nincs pár | 70-74 |
| `addname_instructions` | rejtett | nincs pár | 58-63 |

A csoportosító váltógomb (`cluster` / `showall`) és a nézetváltó (`showignored` / `showunknown`) a saját párját kapcsolja. Az `addname` és az `ignore` nincs párban: a láthatóságukat a kódnak kell állítania.

**Kulcsok a binárisban.** A `string_xrefs` szerint a `0x00749ba0` hivatkozza a `showignored` (`0x00c96f28`), a `showunknown` (`0x00c96f1c`), az `ignore` (`0x00c96f8c`) és az `addname` (`0x00c96f94`) kulcsot. A `cluster` és a `showall` kulcsot a `0x0074cc00` (a fejléc parancskezelője, 9/d), a `clustering_container`-t a `0x0074c8f0` hivatkozza. A csoportosítás kapcsolóját tehát a `0x0074cc00` kezeli, nem a `0x00749ba0`.

**Mikor éri el a `0x00749ba0` az `addname` / `ignore` ágat.** A mód (`this+0x298`, értékei 0, 1, 2, 3; a dumpban nincs elnevezés) akkor 2, és a `0x00448a10(gyűjtemény, album, 0)` igaz. Ez utóbbi a `]unknownface` vagy `]ignoreface` albumra (9/c) igaz. Ekkor a függvény:
- az `ignore` kulcsot keresi (C: 139-149. sor), a találatot felszabadítja;
- az `addname` kulccsal hívja a `this+0x2b4` objektum `vtbl+0xf0` slotját (C: 151-154. sor);
- a `showignored` ágon a 0x20 bájtos objektum `+0x1c` jelzőjét 1-re állítja (C: 136-140. sor), és a `0x00748cc0`-t hívja;
- a `showunknown` ágon a `CShowUnamedDBVis` objektumot építi (C: 208-241. sor).

Ha a mód 2, de az album nem `]unknownface` és nem `]ignoreface`, a függvény az `addname` és az `ignore` kulcsot nem érinti (a `LAB_00749f64` ág). Ha a mód 0 vagy 1, a függvényben nincs `addname` vagy `ignore` kulcs. A csoportosítás kulcsa (`cluster`) ebben a függvényben egyáltalán nincs jelen, ezért a csoportosítás-függést ez a függvény nem dönti el.

**Állapottábla.**

| állapot | váltógomb | nézetváltó | `addname` | `ignore` | fok |
|---|---|---|---|---|---|
| csoportosított | `showall` látszik, `cluster` rejtett | `showignored` látszik | TRE szerint rejtett; a kódos láthatóság NINCS MEG | TRE szerint rejtett; a kódos láthatóság NINCS MEG | a váltópár **megerősített** (TRE); a két mező láthatósága **NINCS MEG** |
| kibontott | `cluster` látszik, `showall` rejtett | `showignored` látszik | látszik: a fejlécben „Add a name” mező van, a csempéken nincs (job-183, 10. kép) | látszik, kijelölés nélkül szürke („Ignore Selected”) | **megerősített** élő felvétellel; a bináris oka **NINCS MEG** |
| mellőzött | a csoportosító gomb állapota a felvételen nem látszik | `showignored` rejtett, `showunknown` látszik („Vissza ide: Név nélküliek”); a `]ignoreface` albumban, 2-es módban a `0x00749ba0` `addname` / `ignore` ága fut | a felvételen (job-210, 16. kép) a fejlécben nem szerepel | a felvételen (job-210) nincs „Ignore Selected” | a látszás **feltételes**; a `vtbl+0xf0` hatása **NINCS MEG** |

Megjegyzés: a kibontott nézet állapota a `cluster` / `showall` pár kapcsolójától függ, a mellőzött nézeté a `showignored` / `showunknown` párétól. Az `addname` és az `ignore` kódos láthatóságát a fenti két pár közül egyik sem vezérli bizonyítottan.

**Bizonyítottsági fok.** A váltópárok és a kezdeti láthatóság: **megerősített** (TRE-sorok, `string_xrefs`). Az `addname` / `ignore` ág feltétele (mód 2 és `]unknownface` / `]ignoreface`): **feltételes** (a kulcshívás a dumpban van, a hatása nincs). A kibontott nézetben látszásuk: **megerősített** élő felvétellel, oka **NINCS MEG**.

**Két független út.** A: a TRE-sorok (fájl). B: a bináris-index `string_xrefs` (a `0x00749ba0` kulcsai) és a dump C-törzse. Mindkettő ugyanazt a párt és ugyanazt a két kulcsot adja (`showignored` / `showunknown`, `addname` / `ignore`). A két út egyezik a névről; a láthatóság hatására csak a felvétel válaszol.

**Cáfoló kísérlet.** Azt vizsgáltam, hogy a `0x00749ba0` vezérli-e a `]unknownface` album csoportosított nézetének `addname` / `ignore` elemét. A C-ben a kulcs csak a 2-es módú ágban van, a 0 és 1 módban nincs. A csoportosítás kulcsa (`cluster`) a függvényben nincs jelen, ezért a csoportosítás-függést a cáfolat nem bizonyította, csak azt, hogy a függvény nem ezt dönti el.

**Jegytörzs-hatás.** Fejlesztési teendő a bizonyított részből nem következik: a TRE-párok és a kezdeti láthatóság a 19. szakasz táblája szerint már egyeznek a `UnnamedFacesView.qml` állapotaival. A `addname` / `ignore` kódos láthatósága nyitott, ezért a „Kész, ha” lista nem írható elő belőle.

**Megjegyzés a 12. szakasz táblájához.** Az `ignore` elem szövege az 1655. sor táblájában „Elvetés”, a magyar szótár (`referencia/i18n/hu/unknownfaceheaderpaneltext.xml`) viszont „Kijelöltek mellőzése”. A felirat forrását egy külön jegyben kell eldönteni; ezt a lapot nem módosítottam.

**Nyitott.**

**12. kör (2026-10-19, #5343): a `0x0074cc00` és a `0x00749ba0` válasza (részben).**

- **`0x0074cc00` (516 bájt, C).** A fejléc parancskezelője nem állít `addname` vagy `ignore` elemet. A `cluster` parancsnál `FUN_0074c200(1, 0)` hívódik, a `showall` parancsnál `FUN_0074c200(0, 0)` (a flag a parancs szövegének `cluster`-összevetése). A `moresug` parancs a `this+0x2dc` objektum `+0x24` bájtját nullázza. A `cluster` és a `showall` után a függvény a `ytDrawNode` (RTTI-cast a `0x00c07db2`-vel) `vtbl+0x7c` slotját hívja a `peoplepanel/update` eseménnyel. Az `addname` és az `ignore` láthatóságát tehát a `0x0074c200` vagy a `vtbl+0x7c` célja állíthatja; egyik sincs dekompilálva, így a láthatóság NINCS MEG.
- **`0x00749ba0`, 2-es módú ág.** A `0x00c96f94` literál (a `.rdata`-ban az `addname` sztring, ellenőrizve) az argumentum a `this+0x2b4` objektum `vtbl+0xf0` (60. slot) hívásában (C: a `FUN_00a697b0` és a `(**(code**)(**(int**)(param_1+0x2b4)+0xf0))` sor). A slot célja az objektum osztályától függ, a `this+0x2b4` írása ebben a függvényben nincs, így a show/hide/enable jelentés NINCS MEG. A `0x00748cc0` visszatérése a `0x20` bájtos objektum mutatója, amelynek `+0x1c` jelzőjét a `0x00749ba0` 1-re állítja (C: `iVar5 = FUN_00748cc0(param_1); *(iVar5+0x1c) = 1`); a `0x00748cc0` törzse NINCS MEG.
- **Bizonyítottsági fok.** A `cluster`/`showall` flag-hozzárendelés: **feltételes** (C; a két kulcs jelenlétét a `string_xrefs` megerősíti). A `moresug` ág: **feltételes** (C). A `vtbl+0xf0` célja: **NINCS MEG**.

**13. kör (2026-10-20, #5343): a `0x0074c200` törzse megválaszolva; az `addname`/`ignore` láthatóságát ez a törzs NEM állítja.** A `0x0074c200` (461 bájt; C: `.ghidra/2026-10-20-ghidra-13.txt` 236-321. sor; asm: `annot_disasm.py`) állapotváltó a `CAlbumLabel` sávon. A `this+0x2b4` objektumon `+0xc8` vtábla-hívással állítja a csoportosítást (`param_2`, `param_1 != 0`), a `+0x2c8` módmezőt a `+0x3dc` (csoportosított) vagy a `+0x3e0` (csoportosítatlan) értékből írja, és a sáv szövegét négy állapot közül választja (az asm sztring-annotációja adja a párokat, a `src/picasapy/app/i18n/*.ts` ugyanezeket tartalmazza):
  - `param_1 == 0`: `CAlbumLabel::ToggleUnGrouped` (`0xcb1360`), szöveg: „Select someone you know and add a name” (`0xcb1338`).
  - `param_1 != 0`, a `+0xb4` vtábla-hívás 0: `CAlbumLabel::LoadingGrouped` (`0xcb131c`), szöveg: „Grouping faces, please wait...” (`0xcb12fc`).
  - `param_1 != 0`, és `[+0x3c8] != 0`, `[+0x3f0] != 0`, `FUN_00783480([+0x3c0]) != 0` (asm `0x0074c2a6`-`0x0074c2c6`): `CAlbumLabel::ToggleGroupIgnore` (`0xcb1270`), szöveg: „Select someone you know and add a name.” (`0xcb1248`).
  - egyébként: `CAlbumLabel::ToggleGrouped` (`0xcb12e0`), szöveg: „Select someone you know and add a name, or click the "x" to ignore that person.” (`0xcb1290`).
  A címkeszöveget a `0x009ae560` (feltételezett fordítófüggvény: kulcs és alapszöveg) és a `0x00717810` adja; a láthatóságot a hívott `0x00717810`, `0x00781680`, `0x007800b0` és a `+0xc8`/`+0xd0` vtábla-hívások végzik, ezek nincsenek dekompilálva.
  - **Bizonyítottsági fok:** a négy állapot és feltételeik: **megerősített** (C és asm: két út). Az `addname`/`ignore` elemek láthatósága: **NINCS MEG**.
  - **15. kör (2026-10-20): a `0x00717810` láthatósági kapuja megvan; a végleges láthatóság nincs.** Forrás: `.ghidra/2026-10-20-ghidra-15.txt` (125-232. sor, C). A függvény a `this+0x2bc` (`param_1[700]`) csomópontot építi vagy frissíti. Ha nincs csomópont, 0x350 bájtos objektumot foglal (`0x0097c5d0`) és konstruál (`0x00856060`), majd három `0x00409ea0` + `0x009df010`/`0x009df060` hívással állít be valamit (a célját nem azonosítottam). Ha van csomópont, a `0x00c07db2` dinamikus castot végez `ytTextNode`-ból `CTextEditNode`-ba (RTTI-leíró címek a C-ben). A `0x008564f0` hívásának kapufeltétele mindkét ágban ugyanaz: a `*param_3` rekord nem nulla, a rekord első dword-jének felső 24 bitje nem nulla, és a `+0x4` bájt nem nulla. A `param_4` nem nulla esetén a csomópont `+0x339` bájtja 1. **Nem ad:** a `0x008564f0` maga (a láthatóság végrehajtása) és a `*param_3` rekord típusa. Ezért az `addname`/`ignore` végleges láthatósága **NINCS MEG**. Bizonyítottsági fok: a kapufeltétel **megerősített** (C, egy út); a végrehajtás **nyitott**. Ghidra-kör kell: 0x008564f0 - a `CTextEditNode` láthatóság- vagy engedélyezés-művelete, és a `*param_3` rekord típusa (`0x0074ad40` hívója) [blokkoló a végleges kapuhoz]
**13. kör (2026-10-20): a `0x00748cc0` megválaszolva.** A 0x20 bájtos objektum a `CIgnoreButtonDBVis` (vtábla: `0x00cb1800`, a `data_symbols` szerint is). A konstruktor a hívó által adott `ESI`-be építi az objektumot, és `mov eax, esi` / `ret 8` lezárással az `EAX`-ben adja vissza (a C `void`-nak mutatja, ez hiányzik belőle; asm: `annot_disasm.py`, 96 bájt). Mezők: `[+0x10]` = a `this` (az `EAX` belépéskor, a szülő), `[+0x4]` = a szülő `+0x58` alobjektuma (vagy 0), `[+0x14]` = a `param_2` sztring (ha az első bájt < 0x80, `InterlockedIncrement`), `[+0x18]` = a `param_1`, `[+0x1c]` = 0 bájt. A törzs nem ír `this+0x2b4`-et, ezért a `+0x2b4` objektum osztályát nem határozza meg. A `0x00401000` segédhívás (a törzs végén) nincs dekompilálva. **Bizonyítottsági fok:** a mezők, a vtábla és a visszatérés: **megerősített** (C és asm). Az `addname`/`ignore` kulcs: nincs a törzsben.
  - **Ghidra-kör kell: 0x00749ba0 - a 2-es módú ágban a `this+0x2b4` objektum osztálya és `vtbl+0xf0` (60. slot) célja az `addname` kulccsal: show, hide vagy engedélyezés; a `+0x2b4` objektum konstruktora / írója [blokkoló]** (A `+0x2b4` osztályának első jelei a `0x0074c200` vtábla-hívásai: `+0xb4`, `+0xc8`, `+0xd0`, `+0xdc`, és a mezők `+0x3c8`, `+0x3c9`, `+0x3c0`, `+0x3dc`, `+0x3e0`, `+0x3f0`; a konkrét osztály NINCS MEG.) → **megválaszolva a 15. körben, lásd lent.**

**15. kör (2026-10-20, #5343): a 2-es ág és a `this+0x2b4` osztálya, megválaszolva; a láthatóság NEM dőlt el.** Forrás: utasításszintű olvasat (`annot_disasm.py`) a `0x00749ba0` (3897 bájt), a `0x0074ad40` (3938), a `0x00746ef0` (303), a `0x0077fd80` (414), a `0x00789820` (143), a `0x00789b70` (79) és a `0x0078b750` (519) címen; a vtábla-slotok a PE-képből (`pe_dis.read`), a típusnevek a TypeDescriptor-ból; a bináris-index `functions`, `rtti` és `xrefs` táblája; és egy `paszta.py`-os pásztázás a teljes `.text`-re (2 884 879 utasítás, csúcs RSS 49 MiB) a `0x00cbdec4`/`0x00cb166c` vtábla-immediate-ekre, a `[reg+0x2b4]` célú írásokra és a `[reg+0x528]` operandusokra.

- **A 2-es ág feltétele (megerősített, asm).** `mov eax, [ebp+0x298]`, `cmp eax, 2`, `jne 0x00749f64` (0x00749c6f-0x00749c84). Utána `call 0x00448a10` a `[esi+0x2bc]`, `[ebp+0x2a0]` és `0` argumentumokkal, majd `test al, al`, `je 0x00749f64` (0x00749c8a-0x00749ca0). A `0x00448a10` az album-ellenőrzés (19.4 szerint a `]unknownface` / `]ignoreface` album); ezt most nem olvastam újra.

- **Az `addname` hívás (megerősített, asm).** A `0x00749d28` a `"addname"` (`0x00c96f94`) karakterláncot a `[esp+0x1c]` slotba építi (a `0x00a697b0` out-paramétere). A `0x00749d39-0x00749d4c` a `[ebp+0x2b4]` objektum vtábla-slotját (`+0xf0`, 60. slot) hívja, az argumentum a `[esp+0x1c]` címe. A `0x00749d4e` ugyanezt a slotot olvassa vissza, és ha nem nulla, a `0x009cd110` névkeresés kulcsa a karakterlánc `+4` mezője (0x00749d52-0x00749d5d).

- **A `this+0x2b4` osztálya: `CAlbumSelectionNode`, vagy annak leszármazottja (megerősített, két út).** A fejléc (`this`) a `0x00746ef0` konstruktor vtáblája (`0x00cb166c`, `CAlbumLabel::vftable`). A `+0x2b4` mezőt a `0x0074ad40` állítja be, két ágon:
  - **A ág:** `call 0x00c07db2` a `[0, 0x00d3db90, 0x00d3b8a0, 0, eax]` argumentumokkal (0x0074af79-0x0074af88), azaz `dynamic_cast<CAlbumSelectionNode*>(ytDrawNode*)`. Az `eax` a `0x009c2fc0` (kereső) visszatérési értéke (0x0074af53, 0x0074af70). A tárolás `mov [ebx+0x2b4], edi` (0x0074b033), csak nem nulla cast esetén (0x0074b01a-0x0074b01c). A típusnevek a PE-ből: `0x00d3db90` = `.?AVCAlbumSelectionNode@@`, `0x00d3b8a0` = `.?AVytDrawNode@@`.
  - **B ág** (ha az A cast nulla): a `[esp+0x13]` jelzőtől függ. Nulla jelzőnél a `0x0077fd80` építi a 0x520 bájtos objektumot, vtáblája `0x00cb46f4` (`CAlbumSelectionNode::vftable`, `mov [esi], 0xcb46f4` a 0x0077fd9f-en). Nem nulla jelző és nem nulla `esi` argumentum esetén a `0x00789820` építi a 0x540 bájtos objektumot: ez előbb meghívja a `0x0077fd80`-t, majd a vtáblát `0x00cb483c`-re írja (`CFoundFaceSelectionNode::vftable`, 0x00789834), és a `+0x528`-at `edi`-re állítja (0x0078986b).

- **A 60. slot célja a két típuson (megerősített, asm, a PE-ből olvasott vtábla).** `CAlbumSelectionNode` (`0x00cb46f4`), 60. slot = `0x005baa00`: `xor eax, eax` / `ret 4`, üres stub, a karakterláncot nem tárolja. `CFoundFaceSelectionNode` (`0x00cb483c`), 60. slot = `0x00789b70`: a `this+0x528`-at összeveti a `*arg` karakterlánc-mutatóval, ha más, a régit felszabadítja, az újat tárolja (`mov [edi], eax`), kezeli a hivatkozásszámlálót, és `0`-val tér vissza. Tehát ez a névmutató beállítója (`"addname"`), nem láthatósági kapcsoló.

- **Ki olvassa a `+0x528` névmutatót (megerősített, asm).** A `0x0078b750` (519 bájt) a `[edi+0x528]`-at olvassa (0x0078b8c9), érvényességet ellenőriz (`[eax]` hivatkozásszámláló-bájt, `[eax+4]` első karakter), majd egy `[edx+0x78]` vtábla-hívással tovább. A `0x0078b750` nem a `CFoundFaceSelectionNode` vtáblájának slotja, a hívóját nem követtem. A láthatóság döntése ott vagy a `0x008564f0`-ban (a 15. kör 0x00717810 tétele) van: NINCS MEG.

- **Bizonyítottsági fok.** A 2-es ág feltétele, az `addname` slot-hívás és a 60. slot két célja: **megerősített** (asm, két út: az utasítások és a PE-ből olvasott vtábla). A `this+0x2b4` osztályának két lehetősége (`CAlbumSelectionNode`, `CFoundFaceSelectionNode`): **megerősített**. Az, hogy futásidőben melyik fut, a jelzőtől és a `0x009c2fc0` eredményétől függ: **feltételes**. A láthatóság: **NINCS MEG**.

- **Cáfoló kísérlet.** (1) Azt állítottam, hogy az `addname` slot láthatóságot kapcsol. Cáfolva: a statikus `CAlbumSelectionNode` slotja no-op, a `CFoundFaceSelectionNode` slotja csak a névmutatót írja. (2) Azt állítottam, hogy a `+0x2b4` egyetlen osztály. Cáfolva: a `0x0074ad40` két konstruktort épít (`0x0077fd80`, `0x00789820`), és két vtáblát ír. (3) Azt állítottam, hogy más konstruktor nincs. Ezt nem igazoltam: a `0xcb46f4` és `0xcb483c` vtábla-immediate pásztázását nem futtattam, a két konstruktort a `0x0074ad40` ágaiból ismertem.

- **Következő cím (c).** `0x0078b750`: a `+0x528` névmutató olvasója és az `addname` láthatóság (vagy annak hiánya) legközelebbi döntési pontja; ennek hívóját kell megnevezni. A 15. kör korábbi tétele (`0x008564f0`) nyitott marad.

#### 19.4/b 16. kör (2026-10-20, #5343): a három címre válasz; a `0x0078b750` NEM láthatóság

*Forrás:* `.ghidra/2026-10-20-ghidra-16.txt` (C: `0x008564f0`, `0x0074ad40`); `.ghidra/2026-10-20-ghidra-15.txt` (C: `0x00717810`); `.ghidra/2026-10-20-ghidra-17.txt` (C: `0x0078b750`, 1200-1309. sor). Ez a szakasz felülírja a 19.4 végi „Következő cím (c)” sort.

- **`0x008564f0`: szövegbeállító, nem láthatóság vagy engedélyezés (megerősített, C, egy út).** A `this` `+0x330` bájtját nullázza, a `+0x320` dword-öt `-1`-re állítja. Ha az EAX-ben kapott szövegmutató nem üres (fejléc-ellenőrzés, első bájt nem nulla), a szöveget másolja (`FUN_009869a0`, `FUN_00989f80`, `FUN_005c2100`), különben `+0x32c = 0`. Végül `FUN_00856610(this, 0)`. Hívói a `0x00717810`-ben (`0x007179c5`, `0x00717a10`) és a `0x00856ec0`-ban vannak.
- **A láthatóság-kapu a `0x00717810`-ben van, nem ebben.** A `0x00717810` létrehozó ágában a `param_4 != 0` esetén `+0x339 = 1`-et ír a szövegcsomópontba; ennek jelentése NINCS MEG.
- **A `0x0074ad40` `*param_3` rekordja: hivatkozásszámlálós karakterlánc (megerősített, C, két hely).** A `0x00717810` a `*param_3` mutatót sztringként kezeli: nem nulla, `*puVar3 & 0xffffff00` nem nulla, és `puVar3[1]` első bájt nem nulla; csak ekkor hívja a `0x008564f0`-t. A `0x0074ad40` ezt a `0x009ae560("PeopleAlbum::ConfirmText", 1)` eredményeként adja át. Tehát a `*param_3` nem csomópont, hanem a `PeopleAlbum::ConfirmText` megerősítő szövege. Bizonyítottság: **feltételes** (a két hely egy forrás C-jéből származik; asm-összevetés nincs).
- **`0x0078b750`: nem vezérli sem az `addname`, sem az `ignore` láthatóságát (megerősített, C, egy út).** A `this+0x528` mezőt (`param_1[0x14a]`) csak érvényességi ellenőrzésre használja (fejléc nem nulla, első bájt nem nulla). A függvény a gyermekelemek közül választ célelemet: a `+0x5a` nem nulla elemeket kihagyja, a kiválasztottra `+0x5d = 1`-et és `+0x59 = 1`-et ír; visszatérése `1000000` (név-ág) vagy `0xf4241` (nincs találat). A `+0x5a` jelentése (rejtett-e) ebből nem derül ki: **feltételes**.
- **Hívója: NINCS MEG.** A `0x00cb4928` adatcím egy vtábla-slotban szerepel (DATA-xref), közvetlen `call` nincs; a vtábla osztálya nincs megnevezve.
- **Cáfoló kísérlet.** (1) Azt feltételeztem, hogy a `0x008564f0` láthatóságot ír: cáfolva, a `+0x330`, `+0x320` és `+0x32c` szöveg-állapot. (2) Azt, hogy a `0x0078b750` a `+0x528`-ból vezérli a láthatóságot: cáfolva, a mező csak érvényességi feltétel.
- **Következő cím (c).** A `addname`/`ignore` állapotfeltétele nyitott. A `0x0078b750` vtábla-hívóját (a `0x00cb4928` slotot) kell azonosítani, és a `0x00717810` `+0x339` jelentését. Blokkoló a fejléc-elemek láthatóságához.

### 19.5 #5185, a csempe névmezője és a `Choose` felirat ága (2026-10-20)

*Forrás:* a Picasa 3.9 `runtime/respack.yt` célzott `.tre`-olvasata (`tre:unknownfaceheaderpanel`, `tre:unknownfaceheaderpaneltext`, `tre:peoplepanel_text`), a teljes `.tre`-névindex keresése; `annot_disasm.py` a `Picasa3.exe` `0x00787dd0` (5279 bájt), `0x007b81e0` (1232 bájt) és `0x007b7910` (500 bájt) függvényein; a `functions`, `string_xrefs`, `rtti` és `xrefs` index; a job-163, job-167 és job-179 átadott felvételi jegyzetei.

**A két „Add a name” mező külön vezérlő.** Az `unknownfaceheaderpanel.tre:70` a fejléc `unknownfaceheaderpanel/addname` elemét definiálja, és `m_hidden`-nel indul; az `unknownfaceheaderpaneltext.tre` felirata „Add a name”, az eszköztippje `Assign a name to all of the selected faces`. Ez a kibontott nézet fejlécmezője, nem az arc-csempék mezője (job-208, 11. kép). A csempemező dinamikus: a `0x00787dd0` `0x00788010`-től a `superbutton(outline_button_text_center, addname): addname-%x` sablont építi, a `0x00788048`-nál a `CAlbumSelectionNode::addname` (`0x00cb4640`) lokalizációs kulcshoz az „Add a name” (`0x00ca0f80`) feliratot rendeli, a `0x00788603`-nál pedig a `faceclusterpanel_%d_addname` (`0x00cb4660`) elemazonosítót formázza. A `faceclusterpanel` azonosító a teljes `respack.yt` `.tre`-korpuszban nem szerepel; a vezérlőt a kód hozza létre. Ez egyezik a job-163/job-66 által mért, csempénkénti mezővel. A fejlécmező és a csempemező útját nem szabad összemosni.

**A People ablak gombfelirata.** A `0x007b81e0` a `[ebp+0x15c]` bájt ellenőrzése után a `this+0x150/+0x154` értékpárt a `[esp+0x20]/[esp+0x24]` párral hasonlítja össze (`0x007b8501`-`0x007b8519`). Egyezéskor a `ContactManagerDlg::OK` kulccsal (`0x00cb7258`) „OK” szöveget (`0x00c86b74`) állít be (`0x007b851b`-`0x007b8537`); eltéréskor a `ContactManagerDlg::Choose` kulcsot (`0x00cb7278`) és a „Choose” szöveget (`0x00cb7270`) állítja be a `0x007b853b`-`0x007b8557` ágon. A job-167 meglévő személyre `Choose` feliratot mér; a job-163 új személynél a People ablak üres találati listájában a „New Person” gombot méri; a job-179 a `Choose` utáni arc-hozzárendelést és számlálóváltozást rögzíti. A felvétel és a bináris feliratág ezen a ponton egyezik.

**A határ, amit ez nem old fel.** A `0x007b81e0` a párbeszéd gombfeliratának kiválasztója, nem bizonyítottan a csempe Enter-kezelője. A `0x00787dd0` a csempevezérlőt létrehozza, de a most követett diszasszemblálásból nem bizonyítható, hogy az Enter, a névjegy-kiegészítő elemére kattintás és a People ablak megnyitása melyik köztes callbacken jut el a ContactManagerhez. Az `xrefs` negatív eredményéből erre nem következtetek. **NINCS MEG:** a csempe Enter-eseményének pontos dispatch-célja; a javaslatelemre kattintás útja; a csempemező Escape-ágának hatása. Megszerzésük: a job-164 folytatásában külön lépésként kattintás a javaslatra és Escape a csempemezőben; binárisan pedig célzott Ghidra-kör a dinamikus `faceclusterpanel_%d_addname` callback és a `ContactManagerDlg` megnyitó út összekötésére.

**Bizonyítottsági fok.** A csempemező dinamikus azonosítója és felirata **megerősített**: az utasításszintű létrehozás egyezik a csempe mezőjét mutató felvétellel, és a teljes `.tre`-korpusz a fejléc külön mezőjét azonosítja. A meglévő személyhez tartozó „Choose” feliratága **megerősített**: a bináris ág és a job-167 képkockaleírása egyezik; a job-179 külön felvétel igazolja az ág utáni hozzárendelést. A csempe Enter callbackje és a javaslatelem kattintása **nyitott**.

**Cáfoló kísérlet.** Azt a könnyen adódó feltevést próbáltam cáfolni, hogy a csempe „Add a name” mezője az `unknownfaceheaderpanel/addname`. A cáfolat sikerült: a `.tre`-elem rejtett, a fejlécben az összes kijelölt arcra vonatkozó eszköztippje van, míg a csempemező külön, `faceclusterpanel_%d_addname` néven, a `0x00787dd0`-ben jön létre; a job-208 kibontott nézete a fejlécmezőt, a job-163 pedig a csempe alatti mezőket külön mutatja. A két forrás ugyanazzal a bizonyítási mércével egyezik.

**Válasz (2026-10-20): a csempe névmezője és a `Choose`-ág útja.** Csak binárisból igazolt részek:

- **Névmező.** A `0x00787dd0` soronként hozza létre a csempe-vezérlőket: `faceclusterpanel_%d_addname` (`0x00cb4660`, ez a névmező), és ha a `this+0x518` bájt nem nulla, `faceclusterpanel_%d_ignore` (`0x00cb46d0`). Mindkét sztring csak ebben a függvényben hivatkozik (`string_xrefs`). A vezérlő osztálya (`FUN_00a63c80`) NINCS MEG.
- **Helyi diszasszemblálásos keresztellenőrzés.** Az `annot_disasm.py 0x00787dd0 5279` ugyanazt a külön csempevezérlőt adja: `0x00788011` a csempe `superbutton(..., addname): addname-%x` sablonját használja, `0x00788604`-nél a `faceclusterpanel_%d_addname` azonosító kerül a létrehozó hívásba, `0x0078804d` pedig az `Add a name` feliratot állítja be. Az adatbázis `string_xrefs` táblájában ez az azonosító csak a `0x00787dd0`-ra mutat. Ez a csempemezőt a fejléc `header_editbox` útjától különíti el; az Enter callback célját nem oldja fel.
- **`Choose`-ág.** A `Choose` (`0x00cb7270`) és a `ContactManagerDlg::Choose` (`0x00cb7278`) sztringet csak a `0x007b81e0` használja, a `0x00787dd0` nem. A közvetlen hívási élek szerint a `0x00787dd0`-ból lefelé 3 szinten (146 függvény) és a `0x007b81e0`-ba felfelé 4 szinten (12 függvény) nincs átfedés. Az összekötés tehát vtábla- vagy callback-hívás.
- **Enter és javaslat-kattintás.** NINCS MEG. A dekompilált törzsből nem olvasható ki a kezelő célfüggvénye: a `FUN_009ccdf0`, `FUN_009df290` és `FUN_0077fad0` hívások célja nincs dekompilálva.

Ghidra-kör kell: 0x007853e0 - a `0x00787dd0` közvetlen hívója (a hívója `0x00783de0`): melyik vezérlőhöz köti a csempelistát, és hol van az Enter-callback [blokkoló]
Ghidra-kör kell: 0x007899e0 - a `0x00787dd0` második hívója; az indexben nincs közvetlen hívója (vtábla?): ki hívja és mikor [blokkoló]
Ghidra-kör kell: 0x007b81e0 hívói (`0x007b7b10`, `0x007b9630`, `0x007ba060`) - melyik ág vezet a `Choose`-hoz a csempéből [blokkoló]

### 19.6 #5185, 2026-10-22: a csempe-mező billentyűkezelője, a Choose-felirat feltétele és a People-megnyitás útja

> ⚠️ **Helyesbítve a 19.7-ben** (2026-10-22, második kör): (1) a `0x00a644bb` nem Escape-ág, hanem a közös „nincs kezelve” kilépés; (2) a `[this+0x35a]` nem a javaslatlista nyitott állapota, hanem a csempe tulajdonsága; (3) a `0x00809360` nem nulla `param_2` ágai elfogadó rutint hívnak, de a csempe-popup bekötése nyitott; (4) a `0x0085a1a0` nem a People-ablak. A többi állítás érvényben marad, a NINCS MEG pontokat a 19.7 viszi tovább.

*Forrás:* `Picasa3.exe` (SHA-256 `644b7bec…ddc96`, egyezik az index `meta.json`-jával; image base `0x00400000`). Az index `functions`, `rtti` (a vtábla-slotok a `kind` oszlopban) és `xrefs` táblái. Ghidra-dumpok: `2026-10-20-arc-5185.txt` (`0x00787dd0`), `2026-10-20-ghidra-13.txt` (`0x00783de0`), `2026-10-21-koteg-1021b.txt` (`0x007853e0`, `0x007899e0`), `2026-10-21-people-szuro.txt` (`0x0071f740`, `0x00720dd0`), `2026-10-21-people-dlg.txt` (`0x0085a1a0`), `2026-10-20-ghidra-22.txt` (`0x007b81e0`). Helyi diszasszemblálás (`annot_disasm.py`) a `0x00a63c80`, `0x00a62970`, `0x00a64050`, `0x00a65170`, `0x007b81e0` és `0x007b8f80` függvényeken, valamint a People-dialógus függvényeinek íráskeresése. Ez a szakasz a 19.5 és a 35.9 nyitott pontjait viszi tovább: a `0x007853e0`, `0x007899e0` és `0x007b81e0` hívóit és törzsét a 2026-10-20/21-es dumpok már tartalmazzák, ezért ezekre most nincs újabb Ghidra-kérés.

**Jelölések.** „Megerősített”: két független úton (utasításszintű olvasat és RTTI/dump) egyezik. „Erős”: egy út bizonyított, a második csak a viselkedési konvencióra illeszkedik. „Feltételes”: egy út. „NINCS MEG”: a dumpokban és a diszasszemblálásban nincs meg; mellette a kérendő Ghidra-cím.

#### A 2026-10-17-es négy kérdés állapota

| Kérdés | Válasz a binárisból | Bizonyítottsági fok |
|---|---|---|
| 1. Melyik kezelő fut a csempe mezőn? | Osztály: `ytButtonNode::vftable` (`0x00ce4874`). Billentyűkezelő-jelölt: a vtábla `+0x74` slotja, `0x00a64050`. | osztály: megerősített; billentyűkezelés: erős (a hívó nincs megerősítve) |
| 2. Enterre mi dönti el a People-ablak nyílását? | A Choose-felirat feltétele (`0x007b84ee`-`0x007b8557`) megerősített. Az Enter-ág döntési pontja (`0x00a64050`, commit-ág `0x00a64633`) megerősített, de a People-megnyitóig vezető út NINCS MEG. | Choose-feltétel: megerősített; Enter-út: NINCS MEG |
| 3. Javaslatlista, és a javaslatra kattintás ablak nélkül ad-e nevet? | A billentyűk konvenciója és az elfogadó rutin (`0x00a54b70`) a CAutoCompleteListBox-szal egyezik. A csempe popup-osztálya és a kattintás útja NINCS MEG. | feltételes; kattintás: NINCS MEG |
| 4. Escape a csempe mezőjében | Ha a `[this+0x384]` Escape-re van állítva, commit. Ha a lista nyitva van, a szülő kapja. Egyébként a `0x00a644bb` ág: NINCS MEG. | részben megerősített; a hatás: NINCS MEG |

#### 1. A csempe-mező osztálya és billentyűkezelője

- **Létrehozás.** A `0x00787dd0` a csempelista ciklusában (C-dump, 478-482. sor) hívja a `FUN_00a63c80()`-t, majd a `faceclusterpanel_%d_addname` sablont formázza a `0x0040eab0` burkolón át, és a `0x009ccdf0`, `0x009df290` hívás után a mutatót a `this+0x4f0` tömbbe írja. Az ignore-vezérlő (`faceclusterpanel_%d_ignore`, 594. sor) a `this+0x518` jelzőtől függ. **Megerősített** (dump és utasítás).
- **Objektum.** A `0x00a63c80` 0x3f8 bájtot foglal (`0x0097c5d0`), és meghívja a `0x00a62970` konstruktort. Utána a forrásobjektum alobjektumait másolja (`0x264`, `0x28c`, `0x2b4` eltolás). A `0x00a62970`-ben a vtábla-írás: `mov dword ptr [esi], 0xce4874` (`0x00a62982`), a `0x009dd800` hívás után. A másoló forrás-sablonja (az `eax` a hívásnál) **NINCS MEG**.
- **Osztály.** Az RTTI szerint a `0x00ce4874` az `ytButtonNode::vftable`, 31 slottal. **Megerősített** (utasítás és RTTI). Két lehetséges azonosítás kizárható: a csempe mezője nem `CAutoCompleteEditBox` (ennek vtáblái `0x00c9bc5c` körül vannak), és nem a jobb fiók fejlécmezője (`header_editbox`, `0x00640670`, 19.4), mert a létrehozójuk más függvény. A végleges osztályt egy leszármazott konstruktor felülírhatná; ezt nem vizsgáltam, ezért az osztály-állítás a vtábla-írásra támaszkodik.
- **Billentyűkezelő-jelölt.** A `ytButtonNode` vtáblájának `+0x74` slotja: `0x00a64050` (1639 bájt). Összehasonlítások: Escape `0x00a645ed` (`cmp ebx, 0x1b`), Enter `0x00a64625` (`cmp ebx, 0xd`), Space `0x00a6462a` (`cmp ebx, 0x20`). Visszatérési kód: `0xf4240` = kezelve (`0x00a64690`), `0xf4241` = nincs kezelve, a szülő kapja (`0x00a64613`). Ez a konvenció egyezik a CAutoCompleteListBox billentyűkezelőjével (`0x00809050`, 38.9). **Erős**: a kezelő szerepe a konvencióból és a billentyűkódokból következik; hogy a vtábla `+0x74` slotját valóban ez hívja, az nincs megerősítve.
- **Hívó.** Ki hívja a `+0x74` slotot: **NINCS MEG** (közvetett, vtábla-hívás; az index nem látja).

#### 2. Enter: a commit-ág és a People-megnyitó

- **Elágazás a lista állapotától.** A `[this+0x35a]` jelző (következtetés: a javaslatlista nyitva van) befolyásolja az Enter kezelését:
  - `[this+0x35a] != 0`: Enter nem commit, a kezelő `0xf4241`-et ad vissza (a szülő kapja, `0x00a6460a`-`0x00a64613`).
  - `[this+0x35a] == 0`: Enter (`0x0d`) commit-ág (`0x00a64625`, `0x00a64633`).
- **Commit-ág (megerősített utasítás).** `0x00a63a90(1)` hívása; `[this+0x368] := 0x100` (`0x00a6463e`); `0x009df260(this)` hívása, az „aktuális elem” lekérdezése (38.9). Ha az eredmény nem nulla, a `0x00a54b70(elem)` hívódik (elfogadás, ugyanaz a rutin, mint a CAutoCompleteListBox Enter-ágában). Végül a `[vtábla+0x78]` slot (`0x00a65170`) hívódik `(0, 1)` argumentumokkal, és a kezelő `0xf4240`-et ad vissza.
- **A People-megnyitó.** A `0x0085a1a0` (264 bájt) a `/c/ui/ContactManager` erőforrást tölti be a `0x0085a120` (119 bájt) hívásával. Indexelt egyetlen hívója a `0x00720dd0` (`0x00720e01`), a `0x00720dd0` pedig a `0x0071f740` felugró menü kezelőjének `0x9e16` parancs-ágából hívódik (`0x0071fa50`). A `0x0071f740` (CreatePopupMenu, DestroyMenu, a `0x00a6b090` által visszaadott parancsazonosító) hívói: `0x0051ab50` és `0x007ab710`. **Következtetés:** a `0x9e16` parancs a felugró menü ága, nem a csempéé. A parancs felirata NINCS MEG (a `felulet-terkep/menuk.json`-ban nincs).
- **Cáfoló kör (csak közvetlen hívások).** A `0x00a64050`, `0x00a54b70`, `0x00a63a90`, `0x009df260` és `0x00a65170` közvetlen hívásai között nincs `0x0085a1a0`, `0x0085a120`, `0x00720dd0`, `0x0071f740`, `0x007b81e0`, `0x007b9630`, `0x007bb660` és `0x007baf50`. Az egyetlen ismétlődő célpont a `0x009e3c70` (háromszor hívódik, nem People-cím; a szerepe NINCS MEG). A közvetett hívás (`call eax`, `call edx`, vtábla) ezzel nem zárható ki. **Eredmény:** a csempe Enter-útja a People-ablakig nem direkt hívásokon megy, vagy közvetett hívással. Melyik, az NINCS MEG.

#### 3. A Choose-felirat feltétele (`0x007b81e0`, megerősített)

Az utasításrészlet (`0x007b84ee`-`0x007b8557`):

1. `0x007b84ee`: `ebx` = a `[vtábla+0xa0]` hívás eredménye (az `ok` vezérlő keresése). Ha `ebx == esi` (az `esi` nulla: `xor esi, esi` a `0x007b824d` és `0x007b8280` címen), a `0x007b84f4` `je` a `0x007b85bc`-re ugrik, nincs feliratcsere.
2. `0x007b84fa`: `[this+0x15c] == 0` esetén `0x007b8559`-re ugrik, nincs feliratcsere (a felirat marad).
3. `[this+0x15c] != 0` esetén: ha `[this+0x150] == [esp+0x20]` és `[this+0x154] == [esp+0x24]`, a `ContactManagerDlg::OK` kulcs (`0x00cb7258`) és az „OK” szöveg (`0x00c86b74`) jön (`0x007b851b`-`0x007b8539`). Különben a `ContactManagerDlg::Choose` kulcs (`0x00cb7278`) és a „Choose” szöveg (`0x00cb7270`) (`0x007b853b`-`0x007b8557`).

**A feltétel írói.** A `[this+0x15c]`, `[this+0x150]` és `[this+0x154]` a vizsgált függvényekben csak a `0x007b8f80` inicializálásban íródik (`0x007b9025`-`0x007b9037`, `ebx` nullázva a `0x007b8fa7`-ben). A People-dialógus többi függvényében (`0x007b9630`, `0x007ba4f0`, `0x007b99a0`, `0x007bb660`, `0x007baf50`, `0x007b9f20`, `0x007b93c0`, `0x007ba820`, `0x007b7910`, `0x007b86b0`, `0x007b8d20`, `0x007ba060`, `0x007b7f00`, `0x007b7b10`, `0x007b81e0`) és a megnyitóban (`0x0085a1a0`, `0x0085a120`) nincs írás. A `0x007b9f20` és a `0x007b93c0` csak olvassa a `[0x15c]`-t, és paraméterként adja tovább a `0x007ba060`-nak. **NINCS MEG**, melyik kód állítja nem-nullára a `[this+0x15c]`-t, és mi adja a név-mutatókat.

**Következmény (következtetés).** A vizsgált kódban az OK-felirat csak akkor jelenik meg, ha a név-mutató egybeesik a `0x007b8f80` által nullázott értékkel. A Choose-felirat csak akkor, ha a jelző nem nulla. A „csak a név dönt” olvasat tehát cáfolt: a döntést a jelző kapuzza.

#### 4. Escape a csempe mezőjében

- `[this+0x384] == 0x1b` (Escape) esetén az eredmény `eax = 1` (`0x00a645f2`-`0x00a645fa`), és ez commit (`0x00a64621`-`0x00a64623`, illetve `0x00a64608`-`0x00a6460c`). **Megerősített** utasítás, de a `[this+0x384]` írója NINCS MEG.
- Ha az Escape nem egyezik (`eax = 0`), és `[this+0x35a] != 0` (lista nyitva): `0xf4241`, a szülő kapja (`0x00a64613`). A szülő reakciója NINCS MEG.
- Ha az Escape nem egyezik és `[this+0x35a] == 0`: a `0x00a644bb` ágba fut (`0x00a6462d`). Ez az ág **NINCS MEG** (nincs dumpolva, a törzsét nem vizsgáltam).
- Következmény: az „elveti-e a gépelést, visszaállítja-e az Add a name feliratot” kérdés NINCS MEG. A felvétel (J11) dönti el.

#### 5. Javaslatlista és kattintás

- **Közös elfogadó rutin.** A `0x00a54b70` (6375 bájt) a `0x00a64050` commit-ágából és a CAutoCompleteListBox VK_RETURN-ágából (`0x00809050`, 38.9) is hívódik, ugyanazzal az aktuális elemmel (`0x009df260`). Ez a hívási mintával összeegyeztethető a közös automatikus kiegészítés használatával, de **nem bizonyítja**, hogy a csempe popup `CAutoCompleteListBox`; a popup-osztály **NINCS MEG** (38.17).
- **Kattintás (a 19.6 olvasata, a 19.7-ben javítva).** A régi „nem elfogadás” következtetés hibás volt. A `0x00809360` `param_2 == 0` ága nem hívja az elfogadót, a két `param_2 != 0` ág viszont a `0x00a54b70`-et hívja. A `param_2` egérindex-szemantikája és a csempe popupjához való bekötése **NINCS MEG**; a csempe javaslatra kattintás végső eredményét Colab J11/J2-vel kell mérni (19.7, 35.13).

#### Cáfoló kísérletek

1. „A csempe mezője `CAutoCompleteEditBox`” → **cáfolva**: a konstruktor vtáblája `ytButtonNode` (`0x00ce4874`), nem a `CAutoCompleteEditBox` vtáblája.
2. „Az Enter közvetlenül a `0x00720dd0`-t hívja” → **cáfolva** a közvetlen hívásokra: a `0x00720dd0` csak a `0x0071f740` `0x9e16` ágából érhető el (az index szerint). A közvetett hívás nincs kizárva.
3. „A Choose-felirat csak a névtől függ” → **cáfolva**: a `[this+0x15c]` jelző kapuzza a felirat-cserét (`0x007b84fa`).
4. „A `0x0071c380` a csempe ága” → **nem igazolt**: a `0x00783de0` 5-6-os módban a `0x007853e0`-t hívja, és csak egyéb módban a `0x0071c380`-t. A mód jelentése (csoportosított vagy kibontott nézet) NINCS MEG.

#### A két független út

- **Csempe-osztály (2 út).** A: a `0x00a62970` utasítása (`mov [esi], 0xce4874`), és a `0x00a63c80` konstruktorhívás. B: az RTTI-tábla (`ytButtonNode::vftable`, `0x00ce4874`). Egyeznek.
- **Choose-feltétel (2 út).** A: a `0x007b81e0` utasításolvasata (`0x007b84ee`-`0x007b8557`). B: a Ghidra-dump C-kódja (`2026-10-20-ghidra-22.txt`, `param_1[0x57]` és a két név-mutató). Egyeznek.
- **Billentyűkonvenció (2 út).** A: a `0x00a64050` utasításai (`0xf4240`/`0xf4241`). B: a CAutoCompleteListBox dumpja és utasítás-olvasata (`0x00809050`, 38.9). Egyeznek a konvencióban, de ez nem bizonyítja, hogy a `+0x74` slotot ez hívja.

#### Bizonyítottsági fok és mérleg

- **Megerősített:** a csempe-mező osztálya és létrehozása; a `0x00783de0` és a `0x007899e0` vtábla-hívása (CAlbumSelectionNode és CFoundFaceSelectionNode `+0x78`, CFoundFaceSelectionNode `+0xe8`); a Choose-feltétel utasításszinten; a People-megnyitó csak a `0x0071f740` menü-ágából érhető el (index szerint).
- **Erős:** a `+0x74` slot billentyűkezelő-szerepe.
- **NINCS MEG:** az Enter és a javaslat-kattintás teljes útja a People-ablakig; az Escape viselkedése (`0x00a644bb`); a `[this+0x15c]` írója; a csempe popup-osztálya.

#### Ghidra-kör kérések (egységes alakban)

Ghidra-kör kell: 0x00a64050 - a csempe billentyűkezelőjének teljes C-törzse: a `0x00a644bb` (Escape, lista nélkül) ága, és a `[this+0x35a]` és `[this+0x384]` írói [blokkoló: Q4]
Ghidra-kör kell: 0x00a54b70 - az elfogadó rutin (6375 bájt): a közvetett hívásai (`call eax`, `call edx`), és eléri-e a `0x0085a1a0` People-megnyitót vagy a `0x007b9630` szűrő-ágat [blokkoló: Q2, Q3]
Ghidra-kör kell: 0x00a65170 - a `[vtábla+0x78]` értesítés (337 bájt): a közvetett hívásainak célja, és a szülő-ág [blokkoló: Q2]
Megválaszolva (2026-10-22, 19.7): `0x00809360` `param_2 == 0` nem hív elfogadót, mindkét `param_2 != 0` ág a `0x00a54b70`-et hívja. A csempe popup bekötése és a felhasználói kattintás végső hatása Colab J11/J2-felvételt igényel; új Ghidra-kérés ehhez a bináris ágelágazáshoz nem kell.
Ghidra-kör kell: 0x0085a120 - a People-dialógus megnyitásának hívási környezete, és ki állítja a `[this+0x15c]`-t nem-nullára [blokkoló: Q2]
Ghidra-kör kell: 0x0078ae90 - a `0x007899e0` újraépítési feltétele (a csempe-lista frissítése) [nem blokkoló]
Ghidra-kör kell: 0x009df260 - az „aktuális elem” lekérdezése (28 bájt) [nem blokkoló]

#### Colab-lépéssor (a NINCS MEG pontokra)

A lépések az előző J-tételek mintáját követik (`picasa-colab-jobs`, job-164 folytatása). Mindegyiknél képkocka, a bal oldali `Unnamed (N)` és `Teszt Elek (M)` számlálók, és a `.picasa.ini` `[Contacts2]` és `faces=` sorai a művelet előtt és után.

- **J9 (Enter lista nélkül, új név):** a csempe mezőjébe egy még nem létező nevet gépelni (lista nem jelenik meg), Enter. Mérendő: megjelenik-e a People-ablak, és melyik felirat áll az OK-gombon (OK vagy Choose).
- **J10 (Enter lista nyitva):** meglévő név (`Teszt Elek`) részszövegét gépelni, vár a javaslatlista, Enter. Mérendő: a listaelemet fogadja-e el, vagy a beírt szöveget küldi-e tovább; megnyílik-e a People-ablak.
- **J11 (javaslatra kattintás):** ugyanaz, de a javaslatsorra kattintva. Mérendő: ablak nélkül nevet ad-e (a `faces=` sor változik), vagy megnyílik a People-ablak.
- **J12 (Escape két állapotban):** (a) lista nyitva, gépelt szöveggel, Escape; (b) lista zárva, gépelt szöveggel, Escape. Mérendő: visszaáll-e az „Add a name” felirat, elvetődik-e a gépelés, és változik-e a `.picasa.ini`.

Ha ezek a felvételek megvannak, a 19.6 NINCS MEG pontjai a J9-J12 képkockáival és a `.picasa.ini`-diffekkel zárhatók.

#### Nyitott kérdések mérlege (19.6 történeti állapota; a Q3-at később a 19.7 pontosította)

- **LEZÁRVA (3):** (1) a csempe-mező osztálya és létrehozása; (2) a Choose-felirat feltétele; (3) a csempe Enter-útjának közvetlen hívásaiban nincs People-megnyitó (negatív, csak a közvetlen hívásokra; a közvetett hívás nincs kizárva).
- **BLOKKOLT (6):** (4) az Enter döntési pontja: a `+0x74` slot hívója és a közvetett People-megnyitó (`0x00a54b70`, `0x00a65170`, `0x0085a120` kérések); (5) az Escape `0x00a644bb` ága (`0x00a64050` kérés); (6) a javaslat-kattintás (`0x00809360` kérés, J11); (7) a `[this+0x15c]` írója (`0x0085a120` kérés); (8) a `0x0078ae90` hover-feltétel (nem dönti el az 1-4. pontot); (9) a `0x009df260` (kis kérés, nem dönti el az 1-4. pontot). A blokkoltak gépi úton (Ghidra vagy Colab-felvétel) dönthetők el; a Ghidra-kéréseket a hívó várólistára teszi.
- **HATÓKÖRÖN KÍVÜL:** 0.

Nyitott kérdések: 0 nyílt · 3 lezárva · 6 blokkolt · 0 hatókörön kívül · 0 „csak nyitva”

### 19.7 #5185, 2026-10-22, második kör: az Escape, a kattintás, az Enter-út és a `[this+0x15c]` írói

*Forrás:* `Picasa3.exe` (image base `0x00400000`); a bináris-index `functions`, `xrefs` (csak `call` élek) és `rtti` (vtábla-slotok) táblái; helyi diszasszemblálás (`annot_disasm.py`) a `0x00a64050`, `0x00a65170`, `0x00a54b70`, `0x00a62970`, `0x00a63c80`, `0x00809050`, `0x00809360`, `0x0085a1a0`, `0x007b81e0`, `0x007b8f80`, `0x007b9240` és `0x009df260` függvényen; a 2026-10-22-es Ghidra-kiírás C-törzsei (`referencia/ghidra/2026-10-22-ghidra-sor-220-226.txt`); és két teljes `.text`-pásztázás (`paszta.py`, 2 884 879 utasítás, index-független): az egyik a `+0x15c`, `+0x384`, `+0x35a`, `+0x359`, `+0x366` és `+0x368` írásait, a másik a `+0x140`-`+0x154` hozzáféréseit gyűjtötte. A „Q2” (Enter-út a People-ablakig), „Q3” (javaslat-kattintás) és „Q4” (Escape és a csempe-állapot) jelöléseket a 19.6 kérés-soraiból vettem át; a spec nem definiálja őket.

**Jelölések:** ugyanazok, mint a 19.6-ban.

#### A. Helyesbítések a 19.6-hoz

| A 19.6 állítása | Mit mutat a bináris | Hol |
|---|---|---|
| a `0x00a644bb` az Escape-ága | általános „nincs kezelve, a szülő kapja” kilépés: `mov eax, 0xf4241`, `ret 0xc`; nincs külön Escape-ág | `0x00a644b9`-`0x00a644c6` |
| a `[this+0x35a]` a javaslatlista nyitott állapota | tulajdonság: a konstruktor nullázza, a gyári `0x00a63c80` a sablonjáról másolja; a nyitott állapot nem ez | `0x00a62b41`, `0x00a63cfd`-`0x00a63d04` |
| a `0x00809360` egérútja nem elfogadás | a `param_2 == 0` ág nem hív elfogadást; mindkét `param_2 != 0` ág a `0x00a54b70`-et hívja | `0x00809373`-`0x00809384`, `0x008093ef`, `0x00809521` |
| a People-megnyitó a `0x0085a1a0`, a `0x0085a120` a `/c/ui/ContactManager` erőforrást tölti be | a `0x0085a1a0` 0x150 bájtos kupac-objektumot foglal (`push 0x150`, `call 0x97c5d0`, 0x150 bájt `memset`); a People-ablak (`ContactManagerDlg`) `+0x15c` mezőt használ, legalább 0x15d bájtos; a `0x0085a120` (Ghidra-C) „ContactManagerDlg::GoogleContacts” nevű 800×600-as ablakot hoz létre, ContactsBrowser-vtáblákkal (feltételesen az online-névjegyek böngészője) | `0x0085a1a6`-`0x0085a1ad`, `0x0085a1c7`, `0x007b84fa` |

#### B. Escape (Q4): a csempe nem fogyasztja, a szülő reakciója NINCS MEG

- **Eseménykapu** (megerősített, `0x00a645a7`-`0x00a645e4`): a kezelő csak akkor dolgoz fel billentyűt, ha az esemény `[+0x64]` jelzőjében a `0x10` bit áll, vagy ha a jelzők `0xe` maszkja nulla és a billentyűkód egyezik a `[this+0x384]`-gyel. Egyébként `0xf4241` (a szülő kapja).
- **`[this+0x384]` állandóan 0** (megerősített): az osztályban egyetlen írója a konstruktor (`0x00a62b5f`; `xor ebx, ebx` a `0x00a62988`-nál). A teljes `.text`-pásztázás 28 közvetlen `+0x384`-írást talált 25 függvényben. Ezek egyike sem a ytButtonNode vtábla-tagja, és egyik sincs a hét csempe-kezelő (`0x00a64050`, `0x00a65170`, `0x00a54b70`, `0x00809360`, `0x00809050`, `0x009df260`, `0x009e3c70`) közvetlen hívási zárlatában (278 függvény). Lea-alias írás a pásztázással nem zárható ki.
- **Következmény:** az „Escape-páros” ág (`eax = 1`, `0x00a645f2`-`0x00a645fa`) sosem igaz, a `0x00a64633` commit-ág Escape-re nem fut. Escape-re a csempe mindkét állapotban `0xf4241`-et ad.
- **Enter (0x0d):** `[this+0x35a] == 0` esetén commit (`0x00a64625`); `[this+0x35a] != 0` esetén `0xf4241`, a szülő kapja. **Szóköz (0x20):** commit mindkét esetben (`0x00a6462a`, `0x00a6460e`).
- **Az „Add a name” felirat visszaállítása és a gépelt szöveg elvetése NINCS MEG:** ez a szülő kezelőjétől függ. A `0xf4241` a csempe `+0x74` slotját hívó közvetett hívótól jön; a hívó nincs azonosítva. Belépési pont jelöltje: a `0x00608c00` ugró-thunk és a `0x00ce48e8` vtábla-hivatkozás.

*Bizonyítottsági fok:* a kapu és a három kimenet **megerősített** (utasításolvasat és a Ghidra-C `case 0x17` ága, két út); a `[this+0x384] = 0` **megerősített** (konstruktor-érték és teljes pásztázás).

#### C. Enter-út a People-ablakig (Q2): a közvetlen hívási zárlat nem ér oda; a vtábla-élek jelöltek

- **A commit-ág** (megerősített, utasítás és C): `[this+0x368] := 0x100` (`0x00a6463e`); `elem := 0x009df260(this)` (`0x00a64678`); ha `elem ≠ 0`, `0x00a54b70(elem, …)` (`0x00a6467e`); majd a `[vtábla+0x78](0, 1)` hívás, ami a `0x00a65170` (`0x00a64683`-`0x00a6468e`); visszatérés `0xf4240`.
- **A `0x009df260`** (megerősített, utasítás és C; `0x009df260`-`0x009df285`): a `[+0x244]` láncon felfelé keresi az első olyan csomópontot, amelynek `[+0x213]` jelzője nem nulla, és ennek a **szülőjét** adja vissza; ha nincs ilyen, nullát. Az „elem” tehát nem a csempe.
- **`0x00a54b70`** (6375 B): az első argumentum (az elem) az `esi`-ben van (`0x00a54b81`). 22 egyedi közvetlen hívott, egyik sem People-kapcsolt. Közvetett hívások az elem vtábla `+0x18`, `+0x1c`, `+0x24`, `+0x3c` és `+0x60` slotjain. Az elem osztálya **NINCS MEG**.
- **`0x00a65170`** (337 B): 8 közvetlen hívott, egyik sem People-kapcsolt. Közvetett hívások: a csempe `+0x04` (0x009d79f0) és `+0x08` (0x009d7a00) slotja, valamint a szülő `ytButtContainer` `+0x78` slotja (0x00aa11c0).
- **Közvetlen hívási zárlat** (index; megerősített korlátként): 14 belépési pont (a csempe-kezelők `0x00a64050`, `0x00a65170`, `0x00a54b70`, `0x00809360`, `0x00809050`, `0x009e3c70`, `0x009df260`, `0x00a652d0`, és a szülő-oldali `0x00783de0`, `0x007899e0`, `0x007853e0`, `0x00787dd0`, `0x0071c380`, `0x00aa11c0`) zárlata 589 függvény, 12 szintig bejárva. Ebben nincs: `0x0085a1a0`, `0x00720dd0`, `0x0071f740`, `0x0051ab50`, `0x007ab710`, `0x007b81e0`, `0x007b9240`, `0x007b8f80`, `0x005e9e80`, `0x005ff8c0`, `0x0064d7d0`, `0x006db730`. **Pozitív kontroll:** a `0x0051ab50` → `0x0071f740` → `0x00720dd0` → `0x0085a1a0` lánc (3 szint) ugyanezzel a zárlat-kóddal megtalálható. Az index csak közvetlen `call` éleket tartalmaz; a vtábla- és visszahívás-élek hiányoznak. ⇒ a csempe közvetlen hívásai nem vezetnek a People-ablakig.
- **Jelölt vtábla-élek** (a láncok megerősítve, a csatlakozás a csempéhez nincs):
  - a `PeoplePanel::AutoCompleteProvider` vtábla (`0x00ca1774`) `+0x04` slotja: `0x00644010` → `0x0064d7d0` (név-megnyitó) → `0x007b9240`;
  - ugyanennek az osztálynak a `0x00ca1780` vtáblája `+0x10` slotja: `0x0063e370` → `0x006443e0` → `0x0064d7d0`;
  - a `ListboxACParentHandler` vtábla (`0x00ca17dc`) `+0x0c` slotja: `0x0063eb20` → `0x00641850` → `0x006443e0` → `0x0064d7d0`.
- **Feltételes mechanizmus:** a `[this+0x35a] = 1` jelzőt a `ytSuperButtonCreator` vtábla `+0x0c` slotja (`0x00a69f50`) írja. Ha a név-csempék prototípusai ilyenek, az Enter mindig a szülőhöz megy (`0xf4241`). A szülő lehet az AC-tulajdonos (`ListboxACParentHandler` vagy `PeoplePanel::AutoCompleteProvider`); ha van kijelölt javaslat, az elfogadás a `0x00a54b70`, ha nincs, az AC-tulajdonos a név-megnyitóig juthat. A szülő → AC-tulajdonos él **NINCS MEG**.
- **Tény a felvételből:** a picasa-colab-jobs job-163 szerint az új név Enter után a People-ablak nyílt, tehát az út létezik; a statikus zárlatból hiányzik.

*Bizonyítottsági fok:* a commit-ág és a `0x009df260` **megerősített**; a közvetlen zárlat (és a pozitív kontroll) **megerősített** index-korlátozással; a vtábla-láncok **megerősítettek** a saját szakaszukban, a csatlakozás a csempéhez **NINCS MEG**.

#### D. Javaslatra kattintás (Q3): elfogadás, a név-írás helye NINCS MEG

- **A `0x00809360`** a `CAutoCompleteListBox` vtábla `+0x14` slotja (RTTI, megerősített). A `param_2 == 0` ág (`call edx`, majd `ret 4`) nem hívja a `0x00a54b70` elfogadó rutint. Mindkét `param_2 != 0` ág meghívja (`0x008093ef`, `0x00809521`; a Ghidra-C azonos). A paramétert nem bizonyított azonosítani egérkattintási indexszel, és nincs meg, hogy a csempe popupja ezt a vezérlőt használja; ezért csak az állítható, hogy e függvény nem nulla paraméterrel elfogadó rutint hív, nem pedig az, hogy a csempe-kattintás eredménye bizonyított.
- **A VK_RETURN ág** (`0x00809050`, `CAutoCompleteListBox` `+0x24`): a `0x009df260` után a `0x00a54b70`-et hívja (`0x008090c0`, `0x00809211`); közvetett hívása nincs.
- **Ablak nélkül nevet ad-e?** A `0x00a54b70` közvetlen hívásai között nincs People-megnyitó. A név-írás helye (az elem osztálya és a `+0x18`, `+0x1c`, `+0x24`, `+0x3c`, `+0x60` vtábla-célok) **NINCS MEG**. Megszerzés: a J11 felvétel (`faces=` sor diffje) és a `0x00a54b70` elem-osztályának azonosítása.

#### E. `[this+0x15c]` írói: a nem-nulla író a `0x007b9240`; a többi író osztálya NINCS MEG

- **Olvasó:** a `0x007b81e0` (`ebp` = az objektum), **bájt-méretű**: `cmp byte ptr [ebp+0x15c], 0` (`0x007b84fa`, `0x007b856f`). A 19.6 „`[this+0x15c] != 0`” jelölése bájtra vonatkozik.
- **Nulla író:** a `0x007b8f80` (konstruktor, 671 B): `mov byte ptr [esi+0x15c], bl` (`0x007b9037`), és `bl = 0` (`xor ebx, ebx`, `0x007b8fa7`). Megerősített.
- **Nem-nulla író:** a `0x007b9240` (187 B): `mov byte ptr [esi+0x15c], 1` (`0x007b924e`). Ugyanebben a függvényben a `+0x148`, `+0x14c`, `+0x150` és `+0x154` mezőket a `0x005863f0` eredményéből tölti (`0x007b92c5`-`0x007b92e8`). Megerősített (utasításszint).
- **Közvetlen hívók:** a `0x007b9240` ← `0x005e9e80`, `0x0064d7d0`, `0x006db730`; a `0x007b8f80` ← `0x005e9e80`, `0x005ff8c0`, `0x0064d7d0`, `0x006db730`.
- **A People-ablak (`ContactManagerDlg`) létrehozói** verem-objektumot használnak (`lea eax, [esp+X]` a `call 0x007b8f80` előtt): `0x005ff8c0` (105 B, csak konstruktor), `0x005e9e80` (1436 B; sztringek: „People”, „FRSelectNewPeopleAlbum”, „Preferences”, „]expeople:%d”), `0x0064d7d0` (230 B), `0x006db730` (1322 B). Hívóik: `0x005cb990` (8291 B; `peoplepanel/*` sztringek) → `0x005ff8c0`; `0x005e39a0`, `0x005e9890` → `0x005e9e80`; `0x00644010`, `0x006443e0` → `0x0064d7d0`; `0x006dc030` → `0x006db730`.
- **„Csak ez a két író”: NINCS MEG.** A teljes `.text`-ben 46 objektum-relatív (nem `esp`-alapú) `+0x15c`-írás van. Egyik sem a `ContactManagerDlg` vtábla-tagja vagy annak közvetlen hívottja; ez a mérés a `0x007b8f80`-at és a `0x007b9240`-et sem találja, mert azok nem vtábla-tagok. A 46 függvény osztálya NINCS MEG. A `+0x140`-`+0x154` mezőkkel való együttes előfordulás nem választ szét (24 függvény érinti mindkettőt). Nincs bizonyíték arra, hogy egyik a People-objektumra ír, de nem is zárható ki.
- **A Choose-feltétel** (a 19.6 szerint; újra ellenőrizve): `[this+0x15c] == 0` esetén nincs felirat-csere; különben `[+0x150] == [esp+0x20]` és `[+0x154] == [esp+0x24]` esetén „OK”, egyébként „Choose” (`0x007b853b`-`0x007b8557`). A „Choose” tehát csak a `0x007b9240` jelző után jelenhet meg.

*Bizonyítottsági fok:* a két ismert író **megerősített** (utasítás és teljes pásztázás, két út); a „csak ez a két író” állítás **NINCS MEG**.

#### F. Cáfoló kísérletek

1. „A `0x00a644bb` Escape-ág.” Cáfolva: az oda ugró ágak mind a közös `0xf4241` kilépés.
2. „Az Escape-páros commit elérhető.” Cáfolva: `[this+0x384]` állandóan 0 (konstruktor-érték és pásztázás; a pásztázás a közvetlen eltolás-írást fogja).
3. „A csempe Enter-útja közvetlen hívással eléri a People-ablakot.” Cáfolva a közvetlen zárlatban, pozitív kontrollal ellenőrizve. A job-163 felvétel szerint az út létezik, tehát a hiány a vtábla-élekben van.
4. „A `0x0085a1a0` a People-ablak.” Cáfolva: 0x150 bájtos kupac-objektum, a People-ablak `+0x15c`-ig terjedő mezőt használ.
5. „A `[this+0x15c]` egyetlen írója a `0x007b8f80`.” Cáfolva: a `0x007b9240` nem-nulla írása.
6. „A `[this+0x35a]` a javaslatlista nyitott állapota.” Cáfolva: a konstruktor nullázza, a gyári függvény másolja. A prototípus-azonosítás (`[this+0x508]`, `[this+0x50c]`) feltételes.
7. „A kattintás csak kijelöl.” Cáfolva: mindkét ág hívja a `0x00a54b70`-et.

#### G. Ghidra-kör kérések (egységes alakban)

Ghidra-kör kell: 0x0063eb20 - a `ListboxACParentHandler` vtábla (0x00ca17dc) `+0x0c` célja: a 0x00641850 és 0x006443e0 láncon át a 0x0064d7d0 név-megnyitóig; ki hívja ezt a slotot a csempe-listából [blokkoló: Q2]
Ghidra-kör kell: 0x00644010 - a `PeoplePanel::AutoCompleteProvider` vtábla (0x00ca1774) `+0x04` célja: a 0x0064d7d0 hívásának feltétele és a kiváltó Enter-ág [blokkoló: Q2]
Ghidra-kör kell: 0x0063e370 - a `PeoplePanel::AutoCompleteProvider` vtábla (0x00ca1780) `+0x10` célja, és a 0x006443e0 hívásának feltétele [blokkoló: Q2]
Ghidra-kör kell: 0x005cb990 - a 0x005ff8c0 (ContactManagerDlg konstruktor) hívója: a `peoplepanel/header_editbox` és a `peoplepanel/manual_add_editbox` kezelőjéből vezet-e út ide [blokkoló: Q2]
Ghidra-kör kell: 0x00a54b70 - az első argumentum (elem) osztálya, és a `[esi]+0x18`, `+0x1c`, `+0x24`, `+0x3c`, `+0x60` vtábla-hívások célja: ír-e nevet ablak nélkül [blokkoló: Q3]
Ghidra-kör kell: 0x00608c00 - a csempe `+0x74` slotjának (0x00a64050) hívója: a `0xf4241`-et kapó szülő kezelője [blokkoló: Q4]

Nem blokkoló, a 19.6 listájából örökölt: `0x0078ae90` (a csempe-lista újraépítési feltétele) - a dump megvan, a kör nem dolgozta fel.

#### H. Colab-lépéssor (a fennmaradó NINCS MEG pontokra)

- **J9** (új név, Enter): megvan, a job-163: a People-ablak nyílt.
- **J10** (lista nyitva, meglévő név, Enter): mérendő, fogadja-e el a listaelemet, vagy nyílik-e a People-ablak; `.picasa.ini` diff.
- **J11** (lista nyitva, kattintás a javaslat sorára): mérendő, változik-e a `faces=` sor ablak nélkül, vagy nyílik-e a People-ablak.
- **J12** (a) lista nyitva, gépelt szöveg, Escape; (b) lista zárva, gépelt szöveg, Escape: mérendő, visszaáll-e az „Add a name” felirat, elvetődik-e a gépelés, és változik-e a `.picasa.ini`.

Minden lépésnél: képkocka, a bal sávi számlálók (`Unnamed (N)`, `Teszt Elek (M)`) és a `.picasa.ini` sorai a művelet előtt és után.

#### I. Mérleg

Nyitott kérdések: 0 nyílt · 7 lezárva · 4 blokkolt · 0 hatókörön kívül · 0 „csak nyitva”

- **LEZÁRVA (7):** (1) a `0x00a644bb` nem Escape-ág; (2) a csempe Escape-re nem fogyasztja a billentyűt (`0xf4241`); (3) `[this+0x384]` állandóan 0; (4) a kattintás elfogad (`0x00a54b70`); (5) a `0x0085a1a0` nem a People-ablak; (6) a `[this+0x15c]` nulla írója a `0x007b8f80`, nem-nulla írója a `0x007b9240`; (7) a `[this+0x35a]` tulajdonság, nem állapot.
- **BLOKKOLT (4):** (1) az Enter-út a People-ablakig (vtábla-él, jelöltek a C szakaszban); (2) a javaslat-kattintás név-írása ablak nélkül (az elem osztálya); (3) az Escape hatása (a szülő kezelője); (4) a `[this+0x15c]` többi 46 írójának osztálya.
- **HATÓKÖRÖN KÍVÜL:** 0.

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

**Válasz [részben]:** a detektor-hívás nem a 0x0048e242-ben van (az a `this+0x28c0` zárolása, 21.7). A bejegyzésenként futó hívás a `param_9` objektum `+0x2c` slotja (`-2` 78. sor). A `param_9` a 0x0045f0c0 által betöltött `this+0x2e10` objektum (`-4` 168-172. sor; osztály: feltételes, 25.7). A pontszámküszöb a `this+0x34a4` (0,50, float-ként hasonlítva, 21.2; a `-2` 50. és 86. sora `(DWORD)` alakban mutatja, ezt a diszasszembly korrigálja). Képméret-paraméter a hívás adatai között nincs. Minimális arcméret-paraméter a függvényben nincs. A `+0x2c` slot célja a 0x006cde50 (27. szakasz, 25.9). **Hiányzik:** a `DAT_00d35e44` objektum `+0x44` slotjának törzse.

**Válasz [részben]:** a 0x0045f0c0 nem állítja be a detektor paramétereit. Ha a `this+0x2e10` nulla, lefoglal 0xb0 bájtot, és a `FUN_006ccbb0()` adja az objektumot (`-5` 115-121. sor). Beállítja a `plugins` útvonalat, meghívja az objektum vtable 0. slotját két kimeneti pufferrel, olvassa a `Preferences\FRTemplateChecking` kulcsot, és a `this+0x2e14`-et 1-re állítja (`-5` 144-159. sor; 24.2). A `this+0x3498` nem íródik itt (21.7). A red.cfg mezőinek jelentése NINCS MEG (16. szakasz). **Hiányzik:** a 0. slot és a `+0x34` slot törzse (a `this+0x2e10` init-ja).

**Válasz [részben]:** a `param_5 == 0` ág (`-2` 404-407. sor) minden jelölt képre meghívja a 0x0048bae0-t, és a 0 visszatérésű képeket gyűjti (21.3). Ha a jelöltek száma 151 alatt van, a függvény 0-val tér vissza (`-2` 559. sor). A 0x0048af60 **nem hívja közvetlenül** a 0x0048e1f0-t (a hívottjai között nincs, `-2` 286-300. sor). Mindkettőt a 0x0048ef20 hívja (`-1` 407. és 879. sor). A két függvény közti adatút nincs végigolvasva. **Hiányzik:** a 0x0048ef20 hívási sorrendje a 407. és a 879. sor között.

**Válasz [részben]:** a 0x005836f0 a 64 bites személykulcsot kiveszi a név-táblából, a csomópontot pedig a szabad-listára (`+0x10`) fűzi vissza (21.5, `-2` 741-1155. sor). A függvényben nincs `faces=` és nincs `[Contacts2]` literál, és nincs fájl-API (a dumpok egyetlen fájlírója a 0x0068c030). A törölt személy arcaira gyakorolt hatás (`faces=` törlés, átnevezés vagy mellőzés) NINCS MEG: a `param_6` puffer szerepe nincs igazolva. **Hiányzik:** a `param_6` puffer írói és olvasói.

**Válasz [megválaszolva, dump-korlátozott]:** a 0x00587b90 a név-arc láncokat veszi ki (`-2` 1158-1416. sor), a 0x0058dde0 a figyelőket értesíti a 64 bites kulccsal (`-2` 1419-1468. sor). Egyik sem ír `[Contacts2]`-t: a `Contacts2` sztring a dumpokban egyetlen helyen van, a 0x00586e20-ban (`-4` 3748. sor). **Korrekció:** a 0x00586e20 sem író (27.1). A `[Contacts2]` tényleges kiírója NINCS MEG (N6).

**Válasz [részben]:** a visszatérés 0, ha az index állapota (a `this+0x11a4` tábla, alapértéke a `this+0x11a8`) nem 0x3E9 (1001). Egyezésnél a `param_3` szerinti tábla értékét adja: `param_3 = 0` esetén a `this+0x1bc0`-ból, különben a `this+0x1c20`-ból (22.4, `-3` 1233-1239. sor). A csempe-ágban (0x00647270) mindkét teszt fut, a kijelölt ágban (0x006470d0) csak az első elemen (22.4). **Hiányzik:** az 1001 jelentése (a `this+0x11a4` írói) és a két tábla tartalma.

**Válasz [részben]:** egyik függvény sem ír tárolót a saját törzsében (22.3). A 0x00640340 megerősítő párbeszéd (a 0 jelentése: 24.4). A 0x005fdc30 szövegválasztó: névtelen hívásnál a darabszám dönt (1 alatt `RemoveSingleUnknown`, 2 vagy több alatt `RemoveMultipleUnknown`). A „move this person" út tárolója NINCS MEG: a 0x0063f970, amely a 0x00640340-et hívja, csak a 0x00647270 és a 0x006470d0 ágat hívja (23.3), és nem hívja a 0x005fdc30-at, a 0x005c9b00-t és a 0x00449090-t (23.7 d). A fejlécsáv „ignore" útja (0x005c9b00) a `]expeople:%d` albumba és az ini-be ír (24.3, `-4` 4211-4221. sor). **Hiányzik:** a 0x005fdc30 EDI-je a hívásokban (disasm, nem Ghidra).

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

- **Válasz [részben]:** a 0x006b6a50 indexszel olvas rekordot, és a kódjában nincs név- vagy személy-összehasonlítás (22.1). Visszatérési kódok: 0 (kiolvasva), 3 (az index a tábla végén), 2 (belső állapot), 0xffffffff (nincs fájl-objektum). A 0x0048bae0 csak a visszatérés nullára vizsgálatát használja (`-4` 118-131. sor). Hogy a kizárás név alapú-e, a hívóban dől el. **Hiányzik:** a 13 hívó (22.1) és a kulcs jelentése; döntő a B2 felvétel (24.7).
- **Válasz [részben]:** a 960 (`0x3c0`) nincs a 0x0048e5da kódjában, sem a 0x0048e590 C-jében (22.2, 23.2). A detektor-bemenet méretének forrása szűkül: a 0x006cde50 (a `param_9` +0x2c slotja, 25.9) a `this+0x2908` tábla bejegyzésének második dword-jének felét (`>> 1`) csomagolja a kimenő rekordba (25.9, a 0x006cde50 törzse, `-7`). A tábla írója NINCS MEG. Sorrend: képenként először a 0x0048bae0 fut (0 esetén a köteg-tömbbe kerül), a köteg határán és a maradékra a 0x0048e1f0 (22.2). **Hiányzik:** a `this+0x2908` tábla írója.
- **Válasz [megválaszolva]:** a 0x00640340 hívottjai (`FUN_009bab50`, `FUN_009baae0`, `FUN_00401900`) párbeszéd-műveletek (`-3` 655-801. sor). Tárolót nem írnak (22.3). A 0 jelentése: nincs párbeszéd, vagy a párbeszéd nem szakította meg (24.4). A részletek a 20.7 utolsó pontjának válaszában vannak.
- **Válasz [részben]:** a darabszám-választás csak névtelen hívásnál érvényes: 2 vagy több személy esetén a `RemoveMultipleUnknown` szövegkulcs fut, a darabszámmal (`FUN_0040eab0`, `-3` 973-981. sor; 22.3). A szöveg a sztringtáblából jön, a kulcs és a szöveg összekötését a C nem mutatja. A többes ág tároló-írása ebben a függvényben NINCS MEG (a törzsében nincs írás). **Hiányzik:** az EDI a hívásokban (disasm).
- **Válasz [részben]:** a 0x0068c030 közvetlen hívói a 0x006956d0 (`0x00697557`) és a 0x0069b240 (`0x0069b9fc`). A 0x00687ec0 és a 0x007f7660 nem közvetlen hívók (22.5). A törlés `delete` ága (0x007b99a0 → 0x007ba820) egyiket sem hívja (23.5). A `faces=` literál a 0x0068c030-ban nincs (22.5). A fájlt `(*DAT_00d69520)(path, 0xC0000000, 3, 0, 4)` hívással nyitja, OPEN_ALWAYS módban, csonkítás nélkül (27.2 c). **Hiányzik:** a mentést indító hívólánc (0x006980a0, a 0x00692210 DATA-táblái); ettől dől el, hogy a törlés után fut-e (24.5).
- **Válasz [megválaszolva]:** a csempe-ág (0x00647270) a `0x0044a6b0`-t két tesztben hívja (`-1` 1636. és 1658. sor), és mindkettőben a 0x00449090-t is (22.4, 23.3). A visszatérés 1001-jének jelentése NINCS MEG (lásd a 20.7 0x0044a6b0 pontját).

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

- **Válasz [részben]:** a kulcs (`param_1`) táblaindex. A 0 visszatérés akkor van, ha a 0x006b6a50 lookup 0-t ad ÉS a `local_c != 0.0`. Minden más eset 9 (23.1, `-4` 118-131. sor). A kulcs kép- vagy személyazonosító-jellege NINCS MEG. A 0x0048e5da és a 0x0048af60 a 0-t gyűjtésként, a nem nullát kizárásként kezeli (23.1). **Megjegyzés:** a C szerint a visszaírt érték mindig 0, így a cache-találat sosem következik be; ez a dekompiláló hibája is lehet (23.1).
- **Válasz [részben]:** a 0x0048e590 belépési állapotát (ESI = `this`, EBP = képlista, EBX = `int*`, stack-argumentumok) a hívója, a 0x0048ef20 adja nyolc argumentummal (`-1` 879. sor; 22.2). A `param_9` a `this+0x2e10` mező (`local_30`, 23.2), amelyet a 0x0045f0c0 tölt be (25.7). Képméret nincs az argumentumok között (23.2). Az `in_stack_00000034` és az `in_stack_00000058` kapcsolata NINCS MEG: a találatok az egyik tömbbe kerülnek, a detektor a másikat kapja (22.2). **Hiányzik:** a két tömb kezelésének olvasata a 0x0048e590 törzsében.
- **Válasz [részben]:** a 0x0063f970 parancs-elosztó (HÍVÓK: DATA `00ca16d0`). A csempe-ágat (`0x00647270(this, index, this[0xdb])`) és a kijelölt-ágat (`0x006470d0(this)`) csak akkor hívja, ha a `0x00640340()` 0-t ad (23.3, `-4` 745-754. és 824-849. sor). Az igen-ág írása az ini-íróba, a 0x00484820-ba fut: a csempe-ágon a 0x00449090 `param_5 = 1`-gyel, a kijelölt ágon minden kijelölt arcra (20.3, 23.3). **Hiányzik:** a `this[0xdb]` (`this+0x36c`) írója.
- **Válasz [részben]:** a 0x005edef0 mappa-törlés (`IDS_CANT_DELETE_FOLDER`, `-4` 1197. sor; 23.4), nem személy-mellőzés. A megerősítés után a fő lépés a `0x00440af0(*(this+0x2bc), kulcs, aiStack_f8)` (`-4` 1181. sor). A 0x00440af0 C-törzsében nincs ini- vagy album-írás (24.3). Az „EDI = 3" nincs igazolva (23.4). **Hiányzik:** a 0x004019b0 törzse (a 0x00440af0 hívottja) és a 0x005fdc30 hívás EDI-je (disasm).
- **Válasz [megválaszolva]:** nem. A 0x007b99a0 `delete` ága a 0x007ba820-t hívja, és azonnal visszatér (`-4` 1403-1406. sor; 23.5). A 0x0068c030, a 0x006956d0, a 0x0069b240 és a 0x007d55f0 nincs a `delete` ágban (23.7 b). A mentési hívások az `ok` és az `online` ágban vannak (0x007bb660, 0x007baf50, 0x008d2720; 23.5).
- **Válasz [részben]:** a 0x0068c030 hívása a 0x006956d0-ban a 3113-3114. sorban van, és csak akkor fut, ha a helyi állapot 2 (23.5). Az 1-es állapot első lépése a 0x0068ac80 (24.5). A 0x006956d0-t a 0x006952e0 hívja mindig (`-5` 2055. sor; 24.5), a 0x006952e0 hívója a 0x006980a0 (index). **Hiányzik:** a 0x006980a0 törzse, ettől dől el, hogy a törlés után fut-e. A fájlírás a 0x0068c030-ban van (WriteFile, `-3` 1077-1149. sor).
- **Válasz [részben]:** ugyanez a gépezet (23.5): az állapotot a `param_3[0x40]` bájt adja, a 0x0068c030 a 3597-3598. sorban hívódik. A hívója a 0x00692210 (`006922f8`, index; 24.5), amelyet két DATA-hivatkozás (`00ca7cc0`, `00ca7df8`) hív egy parancs-táblából. **Hiányzik:** a tábla tulajdonosa; ettől dől el, hogy mikor fut (24.5).
- **Válasz [részben]:** a 0x0068ac20 hívja a 0x00586e20-t, de a hívás a diszasszemblálásban van (`0068ac5a`, index). A C-ben a `while (iVar3 != 0)` ciklus nem fut, mert az `iVar3` 0 marad, és a 0x0069ceb0 visszatérése nincs bekötve (23.5). A függvény a `this+0x2c` címet adja vissza (`-4` 3663. sor). A 0x00586e20 nem ír: visszatérése mindig 0xffffffff (27.1). **Hiányzik:** a ciklusteszt (`0068ac41-0068ac62`, disasm, nem Ghidra).
- **Válasz [megválaszolva, korrekcióval]:** a 0x00586e20 nem `[Contacts2]`-író. Ha `param_4 != 0`, a kulcs nem nulla és nem 0xffffffff, meghívja a `FUN_00985ff0("Contacts2")`-t és a `FUN_00401000()`-t, majd mindig 0xffffffff-et ad vissza (`-4` 3667-3753. sor). Nincs fájl-API és nincs `faces=` literál (27.1). A korábbi „azonnal felszabadul" megfogalmazás nem igazolt. A `[Contacts2]` tényleges kiírója NINCS MEG; a hívói a 0x00484820, a 0x0068ac20 és a 0x007d55f0 (23.5).
- **Válasz [megválaszolva, feltételes azonosítás]:** a 0x0068c030 a fájlt `(*DAT_00d69520)(path, 0xC0000000, 3, 0, 4)` hívással nyitja (`-3` 1060. sor). Az öt argumentum a Win32 CreateFile szignatúrájával egyezik (GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, nincs biztonsági attribútum, OPEN_ALWAYS = 4), a hibaág az 0xffffffff értéket vizsgálja. Ez egy út (C-mintázat), az index-író nincs végigjárva. **Csonkítás: nem.** OPEN_ALWAYS nem csonkít, és a 0x0068c030 törzsében nincs SetEndOfFile vagy SetFilePointer, csak WriteFile (`-3` 1077-1149. sor). Ha a hívóban sincs csonkítás, rövidebb mentés után régi fájlvég maradhat.
- **Válasz [megválaszolva]:** a belső feltétel megvan (23.3): az ini-írás (0x00484820) a `param_5`-tól, a személy-album (`]expeople:%d`) a `param_4`-től függ. A csempe-ágban `param_4 = 0`, `param_5 = 1`, vagyis ini-írás és a 0x004d9aa0-val album-művelet, személy-album nélkül. A 0x0044a6b0 teszt a hívóban van, nem a 0x00449090-ben (23.7 c).

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

- **Válasz [részben]:** a 0x0048bae0 a `local_c`-t kimenő float-ként adja (`&local_c`), és csak a `!= 0.0` összehasonlítását olvassa (23.1). A 0x006b6a50 kulcsa táblaindex (22.1). A `local_c` jelentése NINCS MEG. **Hiányzik:** a 13 hívó (22.1), amelyekből a kulcs és a float jelentése kiolvasható; ez a 24.7 B2 felvétel dönt.
- **Válasz [megválaszolva]:** nem gyűjt. A 0x0048b840 minden elemre hívja a 0x0048bae0-t, de a visszatérését nem olvassa (`-5` 319. sor). A saját visszatérése 0 vagy 0xf4242, a `*param_3` jelzőtől függően (`-5` 320-336. sor; 24.1). A gyűjtés a 0x0048e590 0-ágában van (23.1).
- **Válasz [részben]:** a `this+0x2e10` objektumot a 0x006ccbb0 (`FUN_006ccbb0`) példányosítja (24.2). Ez az első mezőbe a `CNevenVision::vftable` (`0x00ca8754`) címet írja (`-6` 932. sor; 25.7). A rtti.csv szerint a vtábla +0x2c slotja a 0x006cde50 (DATA-hivatkozás: `0x00ca8780`). **Feltételes:** az EDI-átadás a 0x0045f143 hívásnál nincs diszasszemblálva (25.7). A +0x34 slot célja NINCS MEG (lásd a 20.7 0x0045f0c0 pontját).
- **Válasz [részben]:** a 0 a 0x00640340-ben „nincs párbeszéd, vagy nem szakította meg" (24.4). A FUN_009bab50 a párbeszéd eredményét képezi le: 0 → 0, 2 → 1, más nem nulla → 2 (25.6). Hogy a 0 melyik gomb (igen vagy nem), a gombazonosítókból dől el: NINCS MEG. A 0 jelentése nem állandó: a 0x007bb660 duplikáció-kérdésénél a 0 másként hat (25.6). **Hiányzik:** a gombazonosítók forrása (a dialóg-objektum vtable +0x158 hívása).
- **Válasz [megválaszolva, EDI a disasm-kérdés]:** igen. A 0x005c9b00 a nem üres kijelölés ágában, ha `param_3 != 0`, először a 0x005c9930-at hívja (`param_5 = 1`). A megerősítés után, ha a `0x00448c90` nem nulla, a `0x00449090(this+700, lista, idx, 1, 1)` fut (`-5` 1254-1314. sor; 24.3). Az „ignore" kezelő (0x005e1645) hívási élét a 15. szakasz adja (index), ezt ebben a körben nem olvastam újra. Az EDI a 0x005fdc30 hívásában (`0x005ca1e1`) NINCS MEG (disasm).
- **Válasz [részben]:** `param_5 = 1` esetén a 0x00448c90 és a 0x00448a10 predikátumot nézi (`-5` 370-381. sor), és csak ha mindkettő nulla, hív (`-5` 391-395. sor; 24.3). A 0x005fdc30-at a 405. sorban hat argumentummal hívja. Az EDI nincs a C-ben (disasm-kérdés). A 0x00484820 közvetlenül nincs benne (24.3). **Hiányzik:** a vtable-célok (`this+700+0x48` objektum +0x9c slot, `this+0x2c0+0x4c` objektum +4 slot) és az EDI.
- **Válasz [megválaszolva, a C-ben]:** egyik sem hív 0x006952e0-t, 0x00692210-t vagy 0x0068c030-t (HÍVOTTAK-lista; 24.5, 25.1). A 0x007baf50 a 0x00584010-et hívja a gyűjteménnyel (`this+0xd4+0x2c5c`), majd a kijelölt elemeket a 0x005849d0-val törli (24.5). A 0x007bb660 gyűjteménye ugyanez (25.1). Fájl-API a C-ben nincs. **Hiányzik:** a 0x00584010 közvetett írói (25.3) és a 0x007bb660 hívottjai (0x00585ad0, 0x0058ff00, 0x007b7f00).
- **Válasz [részben]:** a 0x006952e0 a bemeneti elemet a `+0x1b0` tömbbe fűzi, és feltétel nélkül hívja a 0x006956d0-t (`-5` 2055. sor; 24.5). A hívója a 0x006980a0 (`006980c3`, index). **Hiányzik:** a 0x006980a0 törzse: ettől dől el, hogy a személy törlése után hívódik-e a 0x006952e0 (a törlési ág nem hívja közvetlenül, 23.5).
- **Válasz [részben]:** a 0x00692210 a `+0x1b0` tömb minden elemére hívja a 0x0068c5c0-t, majd a 0x0069b240-et (`-5` 1801-1875. sor; 24.5). Hívói két DATA-hivatkozás (`00ca7cc0`, `00ca7df8`), egy parancs-táblából. **Hiányzik:** a tábla tulajdonosa; ettől dől el, hogy mikor fut (24.5).
- **Válasz [megválaszolva]:** a rekord szövegét írja: `name=%s`, `description=%s` (ha nem üres), `location=%s` (ha nem üres), `category=%s` és `date=%f` sorokat (`-5` 1614-1624. sor), majd a `FUN_006a3b80` listájának `%s=%s` sorait (1627-1636. sor; 24.5). `faces=` literál nincs (25.4). A kulcs a listából jön, amelynek forrása NINCS MEG (25.4).
- **Válasz [részben]:** nem hív és nem ír. Visszatérése 1, ha van következő elem, 0, ha vége (`-5` 2086-2153. sor; 24.5). A 0x0068ac20 ciklusában (`-4` 3659. sor) a visszatérést a C nem köti be, ezért a ciklus futása C-ből nem dönthető el (23.5). **Hiányzik:** a ciklusteszt diszasszemblálása (`0068ac41-0068ac62`, nem Ghidra).
- **Válasz [részben]:** a 0x00440af0 a kulcs útvonalát kéri a `+0x2c` slotról, beolvassa a `Preferences\ShowHidden` kulcsot, majd a 0x004019b0 és a 0x006ca8c0 hívásait végzi (`-5` 1-44. sor; 24.3). A C-ben ini- vagy album-írás nincs. A 0x006ca8c0 csak memóriát épít (25.8). **Hiányzik:** a 0x004019b0 törzse; ettől dől el, melyik tárolót írja a mappa-törlés (NINCS MEG). Nem blokkoló.

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

- **Válasz [részben]:** a 0x007bb660 csak a `param_1+0x158` 2 vagy 3 értékénél fut. A 3-as ágban duplikáció-keresés (0x00585ad0), találatnál 0x0058ff00 és 0x007b7f00 hívás, majd párbeszéd (0x009bab50) (25.1). Nem hívja a 0x006952e0-t és a 0x00692210-t (C-törzs és HÍVOTTAK). Lemezre írás a C-ben nincs. **Hiányzik:** a 0x00585ad0, a 0x0058ff00 és a 0x007b7f00 törzse (ettől dől el, hogy írnak-e).
- **Válasz [részben]:** a 0x008d2720 két mezőt állít be (`param_1[0x25]`, `[0x26]`). 0 esetén a +0x164, 1 esetén a +0x168 slotot hívja, utána mindkét esetben a +0x15c slotot (25.2). Mentés-hívás a közvetlen hívottjai között nincs. **Hiányzik:** a +0x15c, +0x164 és +0x168 slotok célja.
- **Válasz [részben]:** a 0x00584010 első argumentuma a `*(this+0xd4)+0x2c5c` gyűjtemény (25.3). A C-törzsben és a HÍVOTTAK-listában nincs fájl-API (`-6` 400-514. sor). A 0x005875d0-t a rekordokra hívja, a 3-as móddal (a hívás mód-argumentuma nincs a dumpban, 25.9), és közvetett írói lehetnek a 0x0058dd00, a 0x00927530 és a 0x005836f0 (25.9). **Hiányzik:** a 0x0058dd00, a 0x00927530 és a 0x005836f0 törzse; ettől dől el, hogy a 0x00584010 ír-e lemezre.
- **Válasz [részben]:** a 0x006a3b80 láncolt listán keres, és a csomópont típusától függő értéket ad (25.4). `faces=` literál nincs a függvényben. **Hiányzik:** a `faces=` kulcsot ténylegesen töltő függvény: a `this+0x988` mező írói (index, nem Ghidra), a 0x0068ac80 (0068af54) és a 0x0068b320 (0068b93a) hívóin át.
- **Válasz [részben]:** a 0x00448c90 egy 64 bites értéket kér a 0x00448fb0-tól, és 1-et ad, ha az nulla, a 64 bites érték pedig nem nulla. Egyébként a 0x00448fb0 visszatérését adja (`& 0xffffff00`, 25.5). Predikátumként hívja a 0x005c9b00 (1284. sor) és a 0x005c9930 (370. sor). **Hiányzik:** a 0x00448fb0 tábla-írói (a `this+0x27a0` objektum +0x48 tömbje), mert a 64 bites érték jelentése ettől függ (25.9).
- **Válasz [részben]:** a dialóg-eredmény leképezése: 0 → 0, 2 → 1, más nem nulla → 2 (25.6, `-6` 880-916. sor). A gombazonosítók a vtable +0x158 hívásban és a gombcsoportban vannak, ezért a nulla melyik gomb: NINCS MEG. A 0 jelentése a két hívónál ellentétes (25.6). **Hiányzik:** a gombazonosítók és a dialóg-objektum vtable +0x158 célja.
- **Válasz [megválaszolva, az osztály feltételes]:** az EDI-ben kapott objektum első mezőjébe a `CNevenVision::vftable` címet írja (`-6` 927-943. sor, 932. sor). A második mezőt nullázza, a 0x0097adb0-t kétszer hívja (25.7). A hívója a 0x0045f0c0 (`0045f143`). **Feltételes:** az EDI-átadás a 0x0045f143 előtt nincs diszasszemblálva (25.7); ezt a disasm-kérdés dönti el.
- **Válasz [megválaszolva]:** a kritikus szakasz zárolása után a kimeneti tömböket memóriában építi újra. Fájl- vagy ini-hívás nincs (`-6` 982-1115. sor; 25.8). Nem blokkoló; a 0x00440af0 ShowHidden-ágának hívottja (24.3).

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
| 3.3 Jobb oldali Emberek panel | A peoplepanel.tre a suggestion_yes és suggestion_no elemeket rejtettként deklarálja; a 0x00648f20 dinamikusan felépíti őket. A `0x0063f970` parancs-előtagjai a `suggestion_yes:` parancsot a `0x00646ec0`-hoz, a `suggestion_no:` parancsot a `0x00647020`-hoz irányítják; az `addname:` út a 0x00646d70-ra fut (26.3). A 0x00647020 létrehozza a `]expeople:%d` tokent, a 0x004d9aa0-t 2-es móddal hívja, majd frissít. **Megerősített** a parancs-kezelő hozzárendelése két bináris/index út alapján; a javaslat UI-kattintása, végső adatváltozása és tartós írása **NINCS MEG**. | A PeoplePanelRow a javasolt nevet, pipát és X-et mutatja. A pipa az acceptSuggestion útján nevet ír az arcra; az X az SQLite-javaslatmezőt üríti. Forrásolvasat. | Célzott Colab-felvétel kell a javaslat tényleges megjelenéséhez, a kattintásokhoz és az adatfájlok előtte/utána állapotához. A ]expeople token nem bizonyított .picasa.ini-kulcs. |
| 5.1 Személy-album és arc/teljes kép váltás | A súgó a személy-albumot nevezi meg a javaslatok nézeteként. A faceheaderpanel a névhez tartozó album fejlécsávja. A face_zoom és picture_zoom súgója arcra közelített, illetve teljes képes nézetet nevez meg. A 0x005e5290 a Preferences/PeopleAlbumUseFaceSrc értéket 1 alapértékkel olvassa, a 0x00767e50 pedig a gombok állapotát állítja. A váltó két független bináris és erőforrás útja egyezik. Az első megnyitás képe nincs felvétellel igazolva. **Fok: megerősített** a váltó létezésére, nyitott az első megjelenített módra. | A LightboxFeed személynév alapján állítja be a személy-albumot. A LightboxHeader faceZoom állapota arcra vágott és teljes képes módot vált (208-245); a PeopleController tárolja. Az alapállapot a PicasaPy forrásában teljes kép. **Forrásolvasat.** | Colab-felvételen kattintsunk egy személy sorára. Rögzítsük a fejlécet, a képek tartalmát és a kiválasztott gombot. Kattintsunk mindkét módra, váltsunk másik albumra, majd térjünk vissza. |
| 5.2 Átnevezés | A személy-album helyi menüjében Edit People Album... parancs van (0x9c69, építő: 0x007359e0). A contactmgr nyelvi erőforrás Name mezőt és OK gombot tartalmaz. A ContactManagerDlg::DupNameMsg azonos nevű személyre figyelmeztet. A menü, a párbeszéd és a mentési út teljes kapcsolata, továbbá a contacts.xml, [Contacts2], faces= és db3 változása nincs mérve. **Fok: feltételes.** | Az Edit People Album megnyitja a People Manager párbeszédet a kiválasztott személlyel. A PeopleController átírja a központi contacts.xml-t és az érintett mappák [Contacts2] sorait; az arcazonosítókat megőrzi. **Forrásolvasat.** | Nevezzünk át egy albumot. Hasonlítsuk össze a contacts.xml, az érintett ini-k és a db3 állapotát mentés előtt, utána és újraindítás után. |
| 5.3 Két személy összevonása | A személy-album menüben nincs összevonási tétel. A képenkénti PplAlbumPhoto menüben van Move to People Album (0xa0cd) dinamikus almenü és Move to New Person (0xa0cc). A 17. szakasz szerint a 0xa0cd almenühorgony, a benne levő személylista futásidőben épül fel. Ez nem bizonyítja, hogy minden forrásalbum-kép áthelyezése törli vagy összevonja az üres albumot. **Fok: megerősített** a két menüút létezésére, nyitott a teljes album összevonására. | A PicasaPy képmenüje meglévő személyhez rendelhet kijelölt arcot. A People Managerben nincs külön összevonási művelet. A kijelölt képek átrendelése nem bizonyít teljes album-összevonást. **Forrásolvasat.** | Két, külön képekkel rendelkező albumon jelöljük ki az egyik összes képét, majd a Move to People Album almenüben válasszuk a másik személyt. Rögzítsük, eltűnik-e az üres album, és mi változik a contacts.xml, [Contacts2], faces= és db3 állományokban. |
| 5.4 Törlés | A személy-album menü Delete People Album tétele a 0x9d44 parancs (építő: 0x007359e0). A People Manager Delete Person gombjához a 0x007ba820 törlési kezelő és ContactManagerDlg::ConfirmDelete tartozik. A 21.5 szerint a memóriabeli kapcsolat bontása látszik, a lemezre írás és a címkézett arcok sorsa nyitott. **Fok: feltételes.** | A People album Delete megerősítést mutat, majd a savePeopleManagerChanges törlési útját hívja. Ez kezeli a központi névjegyet, a mappák [Contacts2] sorait és a hozzájuk tartozó faces= hivatkozásokat. **Forrásolvasat.** | Külön vizsgáljuk az album helyi menüjét és a People Manager Delete Person gombját. Rögzítsük a megerősítést, az arcok sorsát és az adatfájlokat törlés után, majd a program bezárása után. |
| 8.1 Automatikus és kézi indítás | A 0x0069fc00 konstruktor a BgFaceDetectThread kapcsolót 1 alapértékkel olvassa. A peoplepanel_text.tre szerint a Picasa fényképtár-olvasás közben arcokat keres. Ez két független út az automatikus háttérmotor meglétére. A mappa- és album-helyi Névcímkék hozzáadása a 0x9e1c parancs; a #4535 mérése szerint a célmappa közvetlen képein vagy az album tagképein indít keresést. Külön Find Faces parancs nincs az ismert Tools menüben. **Fok: megerősített** a háttérmotorra és a kézi helyi menüre. Az import és az új mappa felvételének pontos indítási pillanata nincs mérve. | A controller.syncFinished jelzése a FaceScanController.scanNewFaces metódust hívja. Az automatikus út a beállítástól és a futó kereséstől függ. Kézzel a teljes könyvtár, egy mappa vagy egy album vizsgálható a scanForFaces, scanFolder és scanAlbum metódussal. **Forrásolvasat.** | Új Picasa-profilon külön mérjük az első importot, az új mappa felvételét, a meglévő mappába tett új képet és a helyi Névcímkék hozzáadása parancsot. Rögzítsük a folyamatjelzést és az album darabszámát az indítás előtt és után. |
| 8.2 Kihagyások | A Mappakezelő `frexclude` kapcsolója és öröklött kizárása az 1.3. szakaszban dokumentált. A korábban vizsgált kép kihagyásának útja a 20.1-ben szerepel. A névvel címkézett képen talált további arcok feltétele a 21.3-ban nyitott maradt. Ezt a kört nem ismétlem. | A FaceScanController mtime/méret alapján átugorja a már vizsgált képet. Az `is_identified` vizsgálat névvel jelölt fotókat zár ki. **Forrásolvasat.** | Eredeti Colab-próba kell ismert névvel címkézett képpel, ugyanazon képen levő másik arccal, kizárási beállítással kizárt mappával, kizárt szülő alatti gyermekmappával, módosítatlan és megváltoztatott képpel. Az új találatokat és újraindítás utáni állapotot külön rögzítsük. |

### 26.1 Bizonyítottsági fok

**Megerősített:** a személy-album a javaslatok felületi helye; a face/picture váltó létezik; az automatikus háttérmotor alapból engedélyezett; a mappa- és album-helyi Névcímkék hozzáadása út kézi keresést indít. Ezeknél két független út egyezik, vagy a bináris vizsgálat és a rögzített mérés együtt áll rendelkezésre.

**Megerősített:** a suggestion_yes és suggestion_no parancs-kezelők hozzárendelése a 0x0063f970 → 0x00646ec0/0x00647020 útvonalon, a független index- és vezérlőnév-ellenőrzéssel egyezően (26.3). **Nyitott:** az elfogadás/elutasítás tartós fájlhatása; az album átnevezésének és törlésének bináris mentési útja.

**Nyitott:** a javaslatok eredeti csempefelülete; a javaslat elvetésének és a `]expeople` tokennek a tartós hatása; a személy-album első megjelenített módja és a váltás élő hatása; a teljes személy-album összevonás; az import és mappafelvétel automatikus indítási pontja; a névvel címkézett képen talált új arc kezelése.

### 26.2 Cáfoló kör

Megpróbáltam cáfolni azt a feltevést, hogy a Név nélküliek csempéjének X-e javaslatelutasítás. A job-162/163 üdvözlőszövege az X-et mellőzésre köti, az unknownfaceheaderpanel.tre az ignore gombot deklarálja, míg a javaslat súgója a személy-albumot nevezi meg. A job-167 név alatti listája névjegy-kiegészítésként viselkedik. Az ellenpróbák nem támasztják alá az X és a javaslatelutasítás azonosságát.

Az automatikus személy-összevonás feltételezését is ellenőriztem. A PplAlbum menü teljes listájában nincs összevonási tétel, a PplAlbumPhoto menü viszont képek személyek közti mozgatását kínálja. A ContactManagerDlg duplikált névre figyelmeztet, de nem ír összevonásról. Ez cáfolja a külön menüparancs feltételezését, de nem dönti el, hogy az összes kép mozgatása eltünteti-e a forrásalbumot.

### 26.3 Javaslatparancsok útja és a még nyitott kimenet (2026-10-21)

A korábbi változat tévesen a 0x00646d70 függvényt nevezte a suggestion_yes kezelőjének. A függvény a csempe addname útjához tartozik. Az utasításszintű diszasszembly a 0x0063f970 eseményelosztóban a parancsnév-prefixet és a hívást is megmutatja:

| Parancs-előtag | Elosztóág | Hívott kezelő | Mit bizonyít |
|---|---|---|---|
| addname: | 0x0063fd03 | 0x00646d70, hívás: 0x0063fd3c | A csempe névhozzárendelési útja |
| suggestion_yes: | 0x0063fdc7 | 0x00646ec0, hívás: 0x0063fdff | Az igenlő javaslatparancs kezelője |
| suggestion_no: | 0x0063fe1d | 0x00647020, hívás: 0x0063fe57 | Az elutasító javaslatparancs kezelője |

**Bizonyítottsági fok: megerősített a parancs-hozzárendelésre.** A diszasszembly (A út) összevetése az index xrefs/string_xrefs tábláival (B út) ugyanazokat a hívási éleket és a parancsneveket adja. A második, független adatútban a 0x00648f20 a peoplepanel/suggestion_yes:%d és peoplepanel/suggestion_no:%d vezérlőneveket építi fel; ezek a 0x0063f970-ben vizsgált prefixekkel egyeznek. Numerikus eseményazonosító **NINCS MEG**; a vizsgált ágak szöveges parancs-előtagok alapján választanak.

- **0x00646d70, addname:** a törzs a 0x0044a6b0 névjegy-keresést végzi, ezért a korábban ehhez a címhez kötött suggestion_yes viselkedési leírás visszavonva. A korábbi dumpból levezetett javaslat-elfogadási következtetések nem bizonyítékok.
- **0x00646ec0, suggestion_yes:** a kezelő a javaslatlistához tartozó indexet és azonosítót olvassa; további ellenőrzések után a 0x00787270 függvényt hívja. Ez a hívási út azonosítja a kezelőt, de önmagában nem bizonyítja az elfogadás végső adatváltozását. A hívott lánc tartós .picasa.ini, contacts.xml vagy db3 hatása **NINCS MEG**.
- **0x00647020, suggestion_no:** a 0x0040eab0-val képezi a ]expeople:%d token szövegét, a 0x004d9aa0-t 2-es móddal hívja, a javaslatlista elemét 0xffffffff értékre állítja, majd frissít. A token tartós tárolási hatása és a visszautasítás utáni ini/db3 állapot **NINCS MEG**; a token nem nevezhető .picasa.ini-kulcsnak.
- **Felvételi folytatás:** egy megnevezett személyhez hasonló, névtelen arccal kell felvenni a személy-album javaslatcsempéjét. Külön profilpéldányban rögzítendő a javaslat elfogadása és elutasítása; mindkét művelet előtt, után, bezáráskor és újraindítás után mentsük a .picasa.ini, contacts.xml és db3 állapotát. Nyers felvétel helyi hiányában a korábban dokumentált job-207/213 jegyzetek nem bizonyítják a javaslat tényleges megjelenését vagy kattintási eredményét.

Egyéb, ehhez a jegyhez tartozó nyitott felvételi utak:
- **Személy-album:** job-213 alapján a nézet és a két mód ikonja látszik; a váltás, átnevezés és teljes albumok összevonásának eredeti kimenete külön felvételt igényel. A törlési kimenet dokumentálva van a 37.10. szakaszban.
- **Arcfelismerés:** üres Picasa-profilban első keresés, új mappa/új kép, kizárt mappa és névvel ellátott arccal közös képen talált másik arc; minden állapotnál pontos fájldiff. A beállítási küszöbök nem azonosíthatók a Red.dll valódi döntési küszöbével.

## 27. #5184, nyolcadik kör: a Ghidra-kérések lezárása a dumpokból (2026-10-18)

**Hatókör:** mind a 44 „Ghidra-kör kell:" sor (20.7, 21.6, 22.6, 23.6, 24.6). A sorok helyén most a válasz áll, az állapot a szöveg elején van. A forrás a dekompilálások (`.ghidra5184/`: `…szemelykezeles.txt` és `-2` … `-7`; a munkafában, nem a változtatások része), a bináris-index (HÍVÓK, HÍVOTTAK, `string_xrefs`), és a 2026-10-18-i `-7` dump. Diszasszemblálást ebben a körben nem futtattam, ezért a disasm-kérdések nyitva maradnak (27.4).

**Ellenőrzés (ebben a körben, a dumpokból):**
- a 0x0048e1f0 teljes C-törzse (`-2` 1-149. sor);
- a 0x0048af60 hívottjai (`-2` 286-300. sor) és a 0x0048ef20 hívási helyei (`-1` 407. és 879. sor);
- a 0x0068c030 nyitása (`-3` 1060. sor) és a törzs fájl-API hívásai;
- a 0x00586e20 teljes törzse (`-4` 3667-3753. sor);
- az összes dump fájl-API hívásai: a WriteFile-hívások mind a 0x0068c030 törzsében vannak (`-3` 1077, 1106, 1130, 1149. sor); CreateFile, SetEndOfFile és DeleteFile nincs a dumpokban. A nyitás a `DAT_00d69520` függvénymutatón át történik.

### 27.1 Mit zárt le ez a kör

- **Korrekció (N6):** a 0x00586e20 NEM `[Contacts2]`-író. **Helyesbítve (2026-10-18, 28.3/a):** a diszasszemblálás szerint a törzs 24 hívást tartalmaz; a „nem író” és a „mindig -1” olvasat nincs igazolva. A 21.5 és a 22.5 szakasz ezt a függvényt `[Contacts2]`-írónak nevezte; a 23.5 már írás nélkülinek olvasta. A törzse csak a `FUN_00985ff0("Contacts2")` és a `FUN_00401000()` hívást tartalmazza, és mindig 0xffffffff-et ad vissza (`-4` 3667-3753. sor). A 23.5 „azonnal felszabadul" megfogalmazása nem igazolt. A két hívott segédfüggvény (`FUN_00985ff0`, `FUN_00401000`) belsejét nem olvastam, ezért a közvetett írás nincs kizárva. A `[Contacts2]` kiírója NINCS MEG.
- **Szűkült (N3):** a detektor-bemenet méretének forrása a 0x006cde50 (a `param_9` +0x2c slotja) szerint a `this+0x2908` tábla bejegyzésének második dword-je (`>> 1`). A 960 px nincs a kódban. A tábla írója NINCS MEG.
- **Megerősített (N3):** a 0x0048e1f0 küszöbe a `this+0x34a4` (0,50), float-ként hasonlítva. A C-alak `(DWORD)` félrevezető; a 27.2 (a) pont szerint a float-olvasat áll.
- **Megerősített (N6):** a 0x0068c030 törzse nem csonkít: `OPEN_ALWAYS` módban nyit, a törzsében nincs SetEndOfFile vagy SetFilePointer.
- **Dump-korlátozott, megerősített:** a dumpokban a fájlírás (WriteFile) egyedül a 0x0068c030-ban van.

### 27.2 Cáfoló kísérletek

- **(a) N3 küszöb:** a `(DWORD)` alak szerint a `(float)(DWORD)0,5` 0,0 lenne, és minden pozitív pontszám átmenne a szűrőn. A diszasszembly (21.2, `fcomp st(1)`) szerint a küszöb float marad. A C-alak tehát a dekompiláló hibás típusolvasata; a float-olvasat marad.
- **(b) N6 [Contacts2]:** ha a 0x00586e20 író volna, a törzsében fájl-API vagy WriteFile lenne. Nincs. A WriteFile-hívások a dumpokban csak a 0x0068c030-ban vannak. A cáfolat a dumpokra szól, a teljes binárisra nem.
- **(c) N6 csonkítás:** a 0x0068c030 nyitási módját és a WriteFile-hívásait néztem; csonkítás nincs. A cáfolat a 0x0068c030-ra szól. A hívóban (0x006956d0, 0x0069b240) lehet csonkítás, azt nem olvastam.
- **(d) N3 osztály:** ha a 0x0045f0c0 a 0x006ccbb0 után más vtable-t írna a `this+0x2e10`-be, az osztály eltérne. A 24.2 olvasatában ilyen írás nincs; ezt most nem ellenőriztem újra.

### 27.3 A 44 kérés állapota

- **Megválaszolva:** 13 (a válasz a dumpból kiolvasható; a `[megválaszolva]` tag).
- **Részben:** 31 (a válasz egy része a dumpból jön, a `Hiányzik:` mondat nevezi meg a hiányzó törzset vagy adatot).
- A 27.4 lista a `Hiányzik:` mondatokból áll össze, nem új állítás.

### 27.4 A következő Ghidra-köteg (pontosítva: a hiányzó törzsek)

1. `0x006980a0` - a 0x006952e0 hívója; ettől dől el, hogy a személy törlése után mentés fut-e (N6). **→ 29.2: vtábla-slot (+0x70); a hívók és a mentés-trigger NINCS MEG.**
2. `0x004019b0` - a 0x00440af0 hívottja; a mappa-törlés tárolója (N5 mappa-ág). **→ 29.3: registry-olvasó, nem tároló; a tároló NINCS MEG.**
3. `0x00585ad0`, `0x0058ff00`, `0x007b7f00` - a 0x007bb660 hívottjai (N6).
4. `0x0058dd00`, `0x00927530`, `0x005836f0` - a 0x005875d0 közvetett írói (N6, a 0x00584010 mentése).
5. `0x00448fb0` és a `this+0x27a0` tábla írói - a 64 bites érték jelentése (N5, személy-predikátum). **→ 29.3: a tábla-írók és a jelentés NINCS MEG.**
6. `0x009bab50` vtable +0x158 célja - a gombazonosítók (N5, a 0 jelentése).
7. A `DAT_00d35e44` objektum +0x44 slotja (a 0x006cde50 hívja) - a 960 px helye, a Red.dll-e (N3). **→ 29.4: a Red.dll `REDENTRY`-objektuma; NINCS MEG (29.7).**
8. A 0x0045f0c0 init-jának 0. és +0x34 slotja - a red.cfg mezői (N3).
9. A `this+0x2908` tábla írói (index, adat-hivatkozás) - a detektor-bemenet mérete (N3). **→ 29.4: közvetlen író nincs; NINCS MEG.**
10. A 0x006b6a50 13 hívója - a kulcs jelentése (N1; a B2 felvétel dönt).
11. A `this+0x988` mező írói és a `faces=` lista töltője (N6; index).
12. A `00ca7cc0` és a `00ca7df8` DATA-hivatkozások parancs-tábla-tulajdonosa - a 0x00692210 hívási ideje (N6). **→ 29.2: vtábla-slot (PrepareCollection, AlignedImageCollection); a hívási idő NINCS MEG.**

**Disasm-kérdések (nem Ghidra):** a 0x0045f143 előtti EDI (N3); a 0x005fdc30 hívásainak EDI-je (`0x005ee072`, `0x005c9a42`, `0x005ca1e1`, N5); a 0x0068ac20 ciklusának tesztje (`0068ac41-0068ac62`, N6); a 0x0068ac20 és a 0x00586e20 hívás feltétele (`0068ac5a`, N6).

### 27.5 Állapot (N1-N8)

Az előző körök táblái (20.0, 22.8, 23.8, 24.9, 25.11) ehhez igazodnak; ahol eltérnek, ez a táblázat érvényes. A 29.6 tábla (2026-10-18) ezt a táblázatot frissíti. A `[Contacts2]` íróról szóló korábbi állítás (21.5, 22.5) érvénytelen (27.1).

| Pont | Állapot | Mi változott |
|---|---|---|
| N1 | BLOKKOLT | Változatlan. A 0x0048bae0 kizárása értékalapú (0 = gyűjtés, minden más = kimarad; `-4` 118-131. sor). A 0x006b6a50 kimenő float (`local_c`) jelentése NINCS MEG; a 13 hívó nincs olvasva. Döntő: B2 felvétel (24.7). |
| N3 | BLOKKOLT | Szűkült: a bemeneti méret forrása a 0x006cde50 szerint a `this+0x2908` tábla bejegyzése (`>> 1`); a tábla írója NINCS MEG. A 960 px nincs a 0x0048e590, a 0x0048e5da, a 0x0048e1f0 és a 0x006cde50 törzsében. A küszöb `this+0x34a4` (0,50, float). A `param_9` osztálya CNevenVision (feltételes). |
| N4 | LEZÁRVA | Változatlan. |
| N5 | BLOKKOLT | A fejlécsáv „ignore" útja (0x005c9b00 → 0x00449090, `param_4 = 1`) a `]expeople:%d` albumba és az ini-be ír (24.3). A „move this person" út tárolója NINCS MEG (a 0x0063f970 nem hívja a 0x005c9b00-t). Az igen-ág feltétele a 0x00640340 0-ja; a gombazonosítók NINCS MEG. A 0x00448c90 predikátum a 0x00448fb0-t olvassa. |
| N6 | BLOKKOLT | Korrekció: a 0x00586e20 nem író. A `[Contacts2]` kiírója NINCS MEG. A 0x0068c030 az egyetlen dumpolt fájlíró; OPEN_ALWAYS, nem csonkít. A mentés kiváltója NINCS MEG (0x006980a0, DATA-táblák). |
| N7 | BLOKKOLT | Változatlan. |
| N8 | BLOKKOLT | Változatlan. |

Nyitott kérdések: 0 nyílt · 1 lezárva (N4) · 6 blokkolt · 0 hatókörön kívül · 0 „csak nyitva".

### 27.6 Bizonyítottsági fok

**Megerősített:**
- (a) a 0x0048e1f0 küszöbe a `this+0x34a4` (C-alak és diszasszembly: 21.2, 27.2 a pont);
- (b) a dumpokban a fájlírás (WriteFile) egyedül a 0x0068c030-ban van (grep és a törzsek olvasata; dump-korlátozott);
- (c) a 0x00586e20 nem ír fájlt közvetlenül, visszatérése mindig 0xffffffff (a teljes törzs olvasata; a két segédfüggvény belsejét nem néztem).

**Feltételes:** a 0x006cde50 a `param_9` +0x2c slotja (DATA-hivatkozás és rtti.csv); a `param_9` = CNevenVision (az EDI-átadás nincs disasmmal ellenőrizve); a `DAT_00d69520` CreateFile-szerű wrapper (a szignatúra alapján, egy út); a 0x0048af60 nem hívja közvetlenül a 0x0048e1f0-t (egy eszköz).

**NINCS MEG:** a `this+0x2908` és a `this+0x11a4` tábla írói; a 960 px helye; a gombazonosítók; a mentés-trigger (0x006980a0); a `[Contacts2]` kiírója; az 1001 jelentése; az EDI-k.

### 27.7 Fejlesztési következmény

**Nincs fejlesztési lista.** Az N-pontok egyike sem zárult le úgy, hogy eltérést mutatna a mi kódunktól. A 21.8, 23.9, 24.10 és 25.13 „fejlesztési lista: nincs" állítása érvényben marad. A `src/picasapy/app/face_scan_controller.py:470-474` név-alapú kihagyása (N1) nyitott; a B2 felvétel dönt (24.7). Jegytörzs-javaslat: nincs.

### 27.8 Mérleg (8. kör)

Megerősített: 3 tétel (27.6 a-c). Feltételes: 4 tétel (27.6). NINCS MEG: a 27.6 listája. Ghidra-kérés: 44 (20.7, 21.6, 22.6, 23.6, 24.6): 13 megválaszolva, 31 részben (a `Hiányzik:` nevezi meg a hiányzó törzset). Disasm-kérdés: 4 (27.4), nem Ghidra. Tulajdonosi döntés: nincs; a felvétel (B2, B, N6-trigger) a Colab-végrehajtón dönt, a jóváhagyás a tulajdonosé (`jovahagyva`).

## 28. #5185 leltár, 2026-10-18

**Hatókör:** a #5185 jegy 8 pontja, és a „Learn more...” cím (a kutatói feladat 4. pontja). A jegy szövegét közvetlenül nem értük el; a pontok a kutatói brief felsorolásából valók. Forrás: a 3-27. szakasz, a bináris-index (`functions`, `xrefs`, `string_xrefs`), a `picasa-fen-dialogs.md` 4.1 szakasza (`contactmgr.fen`), és a helyi diszasszemblálás (`annot_disasm.py`).

**Jelölés:** KÉSZ = az eredeti és a nálunk oldal is megvan és igazolt. RÉSZBEN = a pont egy része igazolt, a táblázat mondja meg, mi hiányzik. NINCS = nincs adat.

### 28.1 Leltártábla

| pont | állapot | szakasz | hiányzó elem | a megszerzés útja |
|---|---|---|---|---|
| 1. Bal sáv „Név nélküliek” sora: nézet, fejléc, gombok, csoportosítás, méret, sorrend, tálca, kijelölés | RÉSZBEN | 19 (1-6. sor), 9/d, 15.6 | csempék pontos mérete, sorrendje, csoporthatárai (NINCS MEG; az üdvözlőablak a csempék egy részét takarja a job-207 képen); a tálca és a kijelölésszámláló viselkedése Ctrl/Shift/húzás után | Colab-felvétel (28.5, J0-J2). A J0 (job-207, 8. kép) megadta a fejlécet, az öt oszlopos elrendezést és az üdvözlőablak teljes szövegét. Bináris: a felirat-erőforrás nem nyers sztring az EXE-ben (28.6/c) |
| 2. Arc kijelölése és megnevezése: Ctrl, Shift, húzás, névmező, javaslatok, Enter/OK után | RÉSZBEN | 19 (névadás, javaslatlista, Choose), 19.1 4. pont, 9/f, 15.3/c | a Ctrl/Shift/húzás szabálya (csak a Ctrl+A van felvéve, job-180; J2 nincs indítva); a Személykezelő kijelölési módja (N7, NINCS MEG). Megvan: két arc megnevezése a „Teszt Elek” névre és a `.picasa.ini` eredménye (job-213) | Colab-felvétel (J2). Bináris: a `contactmgr.fen` lista-eleme nem adja meg a kijelölési módot |
| 3. Javaslatok: megjelenés, elfogadás, elutasítás | RÉSZBEN | 15.2, 15.3/a, 18, 26.1, 26.3 | az eredeti javaslat-csempe felülete (NINCS MEG); a `suggestion_yes`/`suggestion_no` eseményazonosító és a db3/ini-írók (NINCS MEG); az elutasítás tartós hatása | Colab-felvétel (J3). Bináris: a 26.3 szerinti lépések (0x0063f970 esetérték) |
| 4. Mellőzés: X, fejléc gombja, megerősítés, hová kerül, visszahozás | RÉSZBEN | 19 („Arc mellőzése” sor), 15.3/b.1, 9/e, 9/f, 20.3 | a személyszintű mellőzés írása (N5, NINCS MEG); a „Back to Unnamed” utáni csempe neve (NINCS MEG); az eredeti csempénkénti visszahozó felirata (a job-210 leírása nem említi; nálunk „Stop ignoring”) | Colab-felvétel (J4): job-209/210 megvan (megerősítő ablak, mellőzött nézet, `.picasa.ini` sor); a visszahozás lépése nincs. Bináris: 28.4/a (a 0x005fdc30 hívói) |
| 5. Személy-album: arc/teljes kép, átnevezés, egyesítés, törlés | RÉSZBEN | 26 (5.1-5.4), 8, 21.5, 25, 27.5 | megvan (job-213): a személyalbum nézete és a „Remove” gomb helye. A bináris `PeopleAlbumUseFaceSrc=1` alapértéke a `face_zoom` módot választja (28.4/b, 35.2); a legelső élő képkocka és a váltás hatása még nincs rögzítve. Hiányzik az átnevezés, a teljes album-összevonás, a „Remove” funkciója és a törlés lemezre írása (N6, NINCS MEG) | Colab-felvétel (J5): job-213 a nézetet adta; a váltás, az átnevezés és a törlés még nincs. Bináris: 28.3/d (mentés-kezelő), 28.4/b |
| 6. Személykezelő párbeszéd: elrendezés, kijelölés, mezők, OK/Mégse | RÉSZBEN | 19 („Új név, People ablak” sor), 20.5, `picasa-fen-dialogs.md` 4.1 | az elrendezés és a mezők KÉSZ (két független út: a fen-erőforrás és a job-163 képkockái); a kijelölési mód és a Mégse adatbeli hatása nincs felvéve. A job-167 Escape-je a People ablak keresőmezőjéből zárta be a párbeszédet változtatás nélkül, nem a Mégse gombot és nem a csempe-mezőt. | Colab-felvétel (J6). A fen nem adja meg a listakijelölés módját |
| 7. Névforrások: contacts.xml, [Contacts2], faces=, db3: mikor íródik és olvasódik | RÉSZBEN | 3.1, 3.3, 3.4, 3.5, 4, 22.5, 27.1, 28.3 | a `[Contacts2]` és a `faces=` mért alakja megvan (job-213, a futás végi állapot: 15 jegyű azonosító, `<név>;;`), a kiírás időpontja nincs; a [Contacts2] kiírója (NINCS MEG; két jelölt, 28.3/b); a mentés kiváltója (NINCS MEG, 28.3/d); a contacts.xml olvasásának időpontja (NINCS MEG) | Felvétel: job-213 (futás végi `.picasa.ini`). Bináris: 28.3 (index és disasm). Ghidra-kör a 28.7 szerint |
| 8. Arcfelismerés: mikor fut, mit hagy ki, küszöb | RÉSZBEN | 1.1, 1.2, 1.3, 2, 4, 21.1, 21.2, 26 (8.1-8.2), 27 (N3) | a 960 px bemeneti méret (NINCS MEG); az eredeti felismerési arány (NINCS MEG); az mtime/méret-átugrás és a névvel jelölt kép kihagyása (forrásolvasat, feltételes) | Colab-felvétel (J7). Bináris: a red.cfg mezői (16. szakasz, NINCS MEG) |
| Learn more: a „Learn more...” gomb címe (feladat 4. pont) | KÉSZ | 28.2, és a 19.1 6. pontja | nincs | Bináris: a 0x0074c760 kezelő (disasm és sztring-xref) |

### 28.2 Learn more: a kezelő és a cím (bináris)

- **Kezelő:** `0x0074c760` (283 bájt). Két független úton azonosítva:
  - **(A) diszasszemblálás.** A `learn_more` azonosító 11 bájtos összehasonlítása (`repe cmpsb`, `0x0074c785`-`0x0074c791`) adja az ágat. Egyezésnél a kezelő a nyelvkódot a `0x0098d380` függvénytől kéri (`0x0074c7f6`), a sablont a `0x0040eab0` formázza (`0x0074c822`), majd a `0x00981860`-t hívja a címmel (`0x0074c83c`). Egyezés nélkül a `0x00a6a4f0`-ra adja át (`0x0074c86d`).
  - **(B) sztring-xref.** A `learn_more` (`0x00cb155c`) és a cím-sablon (`0x00cb1568`) is csak a `0x0074c760`-ban hivatkozott (`string_xrefs`); a cím-sablonra más függvény nem hivatkozik. A pontos `learn_more` azonosító csak itt szerepel; a `CUploadDialog:learn_more` (`0x007aa080`) más, a feltöltő-párbeszéd azonosítója.
- **Cím (sablon):** `http://picasa.google.com/support/bin/answer.py?hl=%s&answer=156272`. A `%s` a futáskor feloldott nyelvkód (a `0x0098d380` útja alább). A `0x0074c83c` a formázott URL-t és nullás második argumentumot adja át a `0x00981860`-nak. Ennek célzott diszasszemblálása megmutatja a Windows böngészőparancs feloldását, az `iexplore.exe` tartalékágat, az `"open"` igét (`0x00981a3b`) és az indítóhívást (`0x00981a41`). Ez az indítási kísérlet bináris bizonyítéka; hogy az adott gépen ténylegesen elindul-e a böngésző és betöltődik-e az oldal, futásidejű mérés nélkül **NINCS MEG**.
- **Nyelvkód forrása:** a `0x0098d380` (importjai: `GetLocaleInfoA`, `InterlockedIncrement`). A visszaesési érték a `0x00c7f979` cím; a tartalma nincs dekódolva. **FELTÉTELES:** a `GetLocaleInfoA` LCTYPE-konstansa nincs ellenőrizve.
- **NINCS MEG:** az adott Colab-futás nyelvkódja/böngészője és a weboldal tényleges betöltődése. A kezelő regisztrációja a parancstáblában: a `0x0074c760`-nak nincs direkt hívója az indexben; ez index-negatív, nem lelet.
- **Bizonyítottsági fok:** a kezelő, a sablon és a cím indító rutinba továbbítása **megerősített** (utasításszintű diszasszemblálás és külön sztring-xref út egyezik a kezelő/sablon azonosításánál). Az indító rutin Windows-böngésző indítására irányuló ága diszasszemblyvel azonosított; a futásidejű böngészőindítás és oldalbetöltés **NINCS MEG**. A nyelvkód tényleges értéke az adott futásban **NINCS MEG**.

### 28.3 N6: a [Contacts2] jelöltek és a fájlírás lánca

- **a) A 27.1 helyesbítése (feltételes, nem lezárt).** A 27.1 szerint a `0x00586e20` csak a `FUN_00985ff0("Contacts2")` és a `FUN_00401000()` hívást tartalmazza, és mindig `0xffffffff`-et ad vissza. A diszasszemblálás (752 bájt) ezt nem igazolja: **24 hívást** találtam benne, köztük indirekt `call edx`-et (`0x00586ebb`, `0x005870de`), és két `ret 0x10` záródást (`0x00586edc`, `0x0058710d`). A „nem író” olvasat tehát nincs igazolva; a `0x00586e20` kiírója nyitott.
- **b) A két jelölt.** A `Contacts2` sztring (`0x00c9105c`) két függvényben hivatkozott:
  - `0x00586e20`: hívói `0x00484820` (az arc-író), `0x0068ac20` és `0x007d55f0` (a „PersistContactToINI failed: err %d” hibaüzenet helye).
  - `0x00587110` (1202 bájt): egyetlen hívója a `0x0045a9d0` (4358 bájt), amely a `.picasa.ini` sztringet használja; ennek hívója a `0x0047e470`. A `0x00587110` hívásai (disasm): `0x00985ff0` (a „Contacts2” kulcs), `0x0040eab0` (formázás), `0x005875d0` (kétszer), `0x00586040`, `0x00588210`, és kritikus szakasz (indirekt hívások). Fájl-API közvetlenül nincs.
- **c) A fájlírás.** A `0x0068c030` a dumpolt egyetlen fájlíró (27.1). Közvetlen hívói: `0x006956d0` és `0x0069b240`. Ezek hívói: a `0x006952e0` (egyetlen hívója a `0x006980a0`), illetve a `0x00692210` (nincs direkt hívója). Visszafelé, a direkt hívásokon 8 ugrásig, a két `[Contacts2]` jelölt és a `0x0045a9d0`, `0x007d55f0`, `0x00484820`, `0x0068ac20` NEM éri el a `0x0068c030`-at. Ez **index-negatív**: vtable-hívásokat nem lát, ezért a közvetett írást nem zárja ki.
- **d) A mentés-kezelő (`0x006980a0`).** A 89 bájtos függvény a gyűjtemény `[esi+0x5c] >> 1` elemén végigmegy, és mindegyikre meghívja a `0x006952e0`-t (`0x006980c3`). Ha ez nullától eltérő értéket ad, a függvény azt adja vissza. Egyébként, ha `[esi+0x458]` nem nulla, meghívja a `0x006976f0`-t, végül a `[esi+0x88]` bájtra 1-et ír (disasm, `0x006980a0`-`0x006980f6`). Sem direkt hívója, sem adat-hivatkozása nincs az indexben: vtable-on vagy regisztrált táblán át hívódik. **NINCS MEG:** ki hívja és mikor (ld. 28.7).
- **Állapot:** a [Contacts2] kiírója **NINCS MEG**. A két jelölt memóriabeli módosítását a diszasszemblálás valószínűsíti; a lemezre írás útja nincs igazolva.

### 28.4 Az N5, a személy-album és a N7 új bináris adatai

- **a) Személyszintű mellőzés (N5).** A megerősítő szöveg („Are you sure you want to move this person to the ignored people album?”, `0x00c99830`) hivatkozói: `0x005fdc30` és `0x00640340`. A `0x005fdc30` hívói: `0x005c9930`, `0x005c9b00` (a fejlécsáv `ignore`/`removesel` kezelője, 15.2 szerint) és `0x005edef0`. A `0x00640340` egyetlen hívója a `0x0063f970`. A tényleges írás helye **NINCS MEG**. A job-209 felvétel ugyanezt a szöveget mutatja a képernyőn (19. szakasz), tehát a binárisbeli szöveg a felvételen is látszik.
- **b) Az alap zoommód (5.1).** A `0x005e5290` (116 bájt; hívója a `0x005e0f70`, a fejlécsáv elosztója) a `Preferences\PeopleAlbumUseFaceSrc` kulcsot olvassa, alapértéke **1** (`mov dword ptr [esp+0x40], 1` a `0x005e52b5`-nél). A kulcs kiolvasása után a `0x00767e50`-t hívja `[edx+0xea0]` objektummal és az `ebx` argumentummal (`0x005e52f5`). A `0x00767e50` belső ágai alapján az 1 a `face_zoom` módot kapcsolja be, a 0 a `picture_zoom` módot; az első megnyitás élő állapota ettől még felvételre vár.
- **c) Kijelölési mód (N7).** A `contactmgr.fen` lista-eleme (`list name="contacts"`) nem adja meg a kijelölési módot; a Személykezelő kijelölési módja **NINCS MEG**.

### 28.5 Colab-feladatjavaslatok (a J0 és J1 lefutott: job-207, job-208; J3, J4, J5 részben: job-209/210, job-213)

**Előfeltétel:** a mért felvételi koordináták nincsenek meg (a spec-ben és a helyi memóriában sincs). Ezért a J0 felmérő kép kell elsőnek; a többi lépés a J0 koordinátáit használja. A lépések menüútvonallal vagy felirattal is megadhatók, a koordináta csak ahol mért.

**Állapot (2026-10-18):** a J0 kész (job-207). A J1 kész (job-208): a csoportosított és a kibontott nézet megvan, a csempesorrend és a pixelméret nincs. A J4 részben (job-209/210): a megerősítő ablak, a mellőzött nézet és a `.picasa.ini` sor megvan; a visszahozás lépése (a „Back to Unnamed” és az utána következő állapot) nincs. A J3 részben (job-213): két arc megnevezése megvan, javaslat nem jelent meg, mert mindkét azonos arcú kép megnevezett lett; a javaslathoz egy harmadik, meg nem nevezett, hasonló arc kell. A J5 részben (job-213): a személyalbum nézete megvan; a zoommód-váltás, az átnevezés és a törlés nincs. A J2, J6, J7 és J8 nincs indítva.

```json
[
  {"id": "J0", "pont": "1", "cel": "felmérő kép: a Név nélküliek nézet mért koordinátái", "elofeltetel": "nincs",
   "lepesek": [{"muvelet": "kattint", "cel": "bal sáv, Unnamed (N) sor"}, {"muvelet": "varakozas", "ms": 5000}, {"muvelet": "kepernyokep", "nev": "j0-teljes"}],
   "kimenetek": ["kepernyokep"], "megfigyelni": ["csempék helye és mérete", "Expand groups gomb helye", "fejléc és tálca állapota"], "koordinata": "NINCS MERT, ez a futás adja"},
  {"id": "J1", "pont": "1", "cel": "csoportosítás és csempesorrend", "elofeltetel": "J0",
   "lepesek": [{"muvelet": "kattint", "cel": "fejléc: Expand groups"}, {"muvelet": "varakozas", "ms": 3000}, {"muvelet": "kepernyokep", "nev": "j1-kibontott"}, {"muvelet": "kattint", "cel": "fejléc: Group by face"}, {"muvelet": "kepernyokep", "nev": "j1-csoportosított"}],
   "kimenetek": ["kepernyokep (2 db)", "allapot"], "megfigyelni": ["csoportcímkék és csempesorrend, balról jobbra és fentről lefelé", "csoporthatárok", "csempe-pixelméret csak mért képen"]},
  {"id": "J2", "pont": "2", "cel": "kijelölési modell: Ctrl, Shift, húzás", "elofeltetel": "J0",
   "lepesek": [{"muvelet": "kattint", "cel": "A csempe (J0 koordináta)"}, {"muvelet": "billentyu", "cel": "Ctrl", "kattint": "B csempe"}, {"muvelet": "kepernyokep", "nev": "j2-ctrl"}, {"muvelet": "billentyu", "cel": "Shift", "kattint": "C csempe"}, {"muvelet": "kepernyokep", "nev": "j2-shift"}, {"muvelet": "huz", "cel": "D csempe -> E csempe"}, {"muvelet": "kepernyokep", "nev": "j2-huzas"}],
   "kimenetek": ["kepernyokep (3 db)", "allapot (kijelölésszám, tálca)"], "megfigyelni": ["kijelölt keretek", "No Selection felirat", "Add a name mező aktivitása"]},
  {"id": "J3", "pont": "3", "cel": "javaslat: megjelenés, elfogadás, elutasítás (két külön profilpéldányon)", "elofeltetel": "J0; egy névvel ellátott személy",
   "lepesek": [{"muvelet": "varakozas", "cel": "javaslat megjelenése"}, {"muvelet": "kepernyokep", "nev": "j3-javaslat"}, {"muvelet": "kattint", "cel": "javaslat elfogadása (1. futás)"}, {"muvelet": "allapot"}, {"muvelet": "picasa_ini"}, {"muvelet": "kattint", "cel": "javaslat elutasítása (2. futás, új profil)"}, {"muvelet": "allapot"}, {"muvelet": "picasa_ini"}],
   "kimenetek": ["kepernyokep", "picasa_ini (előtte és utána)", "contacts.xml", "db3 másolat", "allapot"], "megfigyelni": ["javaslat-csempe eredeti felülete", "Unnamed (N) számláló", "faces= sor változása"]},
  {"id": "J4", "pont": "4", "cel": "mellőzés: X, fejléc gomb, megerősítés, visszahozás", "elofeltetel": "J0",
   "lepesek": [{"muvelet": "kattint", "cel": "csempe X"}, {"muvelet": "kepernyokep", "nev": "j4-megerosites"}, {"muvelet": "kattint", "cel": "Ignore Person"}, {"muvelet": "allapot"}, {"muvelet": "picasa_ini"}, {"muvelet": "kattint", "cel": "fejléc: Show ignored faces"}, {"muvelet": "kepernyokep", "nev": "j4-mellozott"}, {"muvelet": "kattint", "cel": "csempe: Stop ignoring"}, {"muvelet": "picasa_ini"}],
   "kimenetek": ["kepernyokep (3 db)", "picasa_ini (3 állapot)", "allapot"], "megfigyelni": ["a megerősítő szöveg pontos alakja", "hová kerül a mellőzött arc (Mellőzött emberek album)", "visszahozás után a faces= sor"]},
  {"id": "J5", "pont": "5", "cel": "személy-album: arc/teljes kép, átnevezés, törlés", "elofeltetel": "egy névvel ellátott személy",
   "lepesek": [{"muvelet": "kattint", "cel": "bal sáv, személy sora"}, {"muvelet": "kepernyokep", "nev": "j5-fejlec"}, {"muvelet": "kattint", "cel": "face_zoom, majd picture_zoom"}, {"muvelet": "kepernyokep", "nev": "j5-mod-a"}, {"muvelet": "kepernyokep", "nev": "j5-mod-b"}, {"muvelet": "menu", "cel": "Edit People Album...", "adat": "uj nev"}, {"muvelet": "allapot"}, {"muvelet": "contacts.xml"}, {"muvelet": "menu", "cel": "Delete People Album"}, {"muvelet": "kepernyokep", "nev": "j5-megerosites"}, {"muvelet": "allapot"}, {"muvelet": "bezaras_ujrainditas"}, {"muvelet": "allapot"}],
   "kimenetek": ["kepernyokep (4 db)", "contacts.xml", "picasa_ini", "db3 másolat", "allapot"], "megfigyelni": ["a zoommód első megnyitáskor", "a megerősítő szöveg", "az arcok sorsa törlés után és újraindítás után"]},
  {"id": "J6", "pont": "6", "cel": "Személykezelő párbeszéd: kijelölés, mezők, OK és Mégse", "elofeltetel": "J0",
   "lepesek": [{"muvelet": "menu", "cel": "Személykezelő megnyitása"}, {"muvelet": "kepernyokep", "nev": "j6-elrendezes"}, {"muvelet": "kattint", "cel": "lista 1. sor"}, {"muvelet": "billentyu", "cel": "Ctrl", "kattint": "lista 2. sor"}, {"muvelet": "kepernyokep", "nev": "j6-kijeloles"}, {"muvelet": "kattint", "cel": "Cancel (Mégse)"}, {"muvelet": "allapot"}, {"muvelet": "menu", "cel": "Személykezelő újra"}, {"muvelet": "billentyu", "cel": "Escape"}, {"muvelet": "allapot"}],
   "kimenetek": ["kepernyokep (2 db)", "allapot", "contacts.xml (Mégse előtt és után)"], "megfigyelni": ["többes kijelölés engedélyezett-e", "Delete Person állapota", "a Mégse és az Escape hatása"]},
  {"id": "J7", "pont": "8", "cel": "arcfelismerés: indítás, kihagyás, küszöb", "elofeltetel": "üres Picasa-profil",
   "lepesek": [{"muvelet": "import", "cel": "egy mappa, egy kép"}, {"muvelet": "varakozas", "ms": 60000}, {"muvelet": "kepernyokep", "nev": "j7-folyamat"}, {"muvelet": "allapot"}, {"muvelet": "picasa_ini"}, {"muvelet": "import", "cel": "új kép a mappába"}, {"muvelet": "varakozas", "ms": 60000}, {"muvelet": "allapot"}, {"muvelet": "mappa", "cel": "Face Detection Off"}, {"muvelet": "import", "cel": "új kép a kizárt mappába"}, {"muvelet": "allapot"}, {"muvelet": "kuszob", "ertek": 50}, {"muvelet": "allapot"}, {"muvelet": "kuszob", "ertek": 95}, {"muvelet": "allapot"}],
   "kimenetek": ["kepernyokep", "picasa_ini", "allapot (arcszám, javaslatszám)"], "megfigyelni": ["a keresés indulási pillanata", "a kizárt mappa képeinek sorsa", "a küszöb hatása ugyanazon képkészleten"]},
  {"id": "J8", "pont": "7", "cel": "mentés-diff: mikor íródik a [Contacts2], faces= és db3", "elofeltetel": "J3-J7 futásai",
   "lepesek": [{"muvelet": "masolat", "cel": "picasa_ini, contacts.xml, db3 (sha256)"}, {"muvelet": "futtat", "cel": "a J3-J7 lépés"}, {"muvelet": "masolat", "cel": "ugyanaz, utána"}, {"muvelet": "bezaras"}, {"muvelet": "masolat", "cel": "ugyanaz, bezárás után"}],
   "kimenetek": ["három állapot-másolat és diff"], "megfigyelni": ["mely lépés írja a [Contacts2] sort lemezre", "a mentés a lépés után vagy bezáráskor történik-e"]}
]
```

Az `muvelet` mezők értékei: `kattint`, `billentyu`, `gepel`, `huz`, `menu`, `import`, `mappa`, `kuszob`, `kepernyokep`, `allapot`, `picasa_ini`, `contacts.xml`, `masolat`, `varakozas`, `bezaras`, `bezaras_ujrainditas`. A `huz` a húzást jelöli (kezdő és záró csempe), a `varakozas` ezredmásodpercben adott várakozás.

### 28.6 Bizonyítottsági fok és cáfoló kísérletek

- **Megerősített:** a `learn_more` kezelő és a cím-sablon (28.2, A és B).
- **Feltételes:** a nyelvkód forrása (28.2); a `0x00586e20` kiírója (28.3/a); a `0x00587110` szerepe (28.3/b); a `PeopleAlbumUseFaceSrc=1` → `face_zoom` diszasszemblált leképezése (35.2; feltételes, az első élő képkocka nyitott).
- **NINCS MEG:** a [Contacts2] lemezre írásának útja; a mentés-kezelő hívója (28.3/d); a 960 px; az eredeti felismerési arány; a személyszintű mellőzés írása; a Személykezelő kijelölési módja; a felirat-szövegek a helyi bináris alapján.
- **Cáfoló kísérletek:**
  - (a) Learn more: ha a `0x0074c760` nem volna a kezelő, a `learn_more` azonosító és a cím másik függvényben lenne. Az indexben mindkettő kizárólag ott van, a cáfolat nem sikerült.
  - (b) [Contacts2]: a 27.1 „nem író” állítását diszasszemblálással próbáltam cáfolni. Sikerült: a 27.1 olvasata (két hívás, mindig -1) nem áll, a `0x00586e20` kiírója nyitott.
  - (c) Felirat-szövegek: nyers keresés az EXE-ben, ASCII és UTF-16LE kódolásban: „As Picasa scans”, „Welcome to the Unnamed”, „Expand groups”, „Group by face”, „Show ignored faces”, „Stop ignoring”, „Ignore Selected” mind 0 találat. A helyi másolatban csak két `.tre` van. A szövegek forrása a jegy képernyőképe és a job-leírás marad.
  - (d) Index-negatív: a `0x0068c030` visszafelé-bejárása vtable-hívásokat nem lát, ezért a „nem éri el” állítás csak a direkt hívási gráfra igaz.

### 28.7 Ghidra-kör kérések (új, a 28.3 nyitott pontjai)

Ghidra-kör kell: 0x00586e20 - a teljes törzs: melyik hívás ír a `Contacts2` szakaszba, és a sikeres ág 0-t vagy -1-et ad-e vissza [blokkoló]
Válasz [megválaszolva, a C-ben]: a `0x00587110` **olvasó**, nem a `[Contacts2]` írója; a `0x005875d0` memóriabeli beszúrás, fájl-API nélkül (30.4).
Ghidra-kör kell: 0x0045a9d0 - a `.picasa.ini` mappafüggvény: mikor és hová írja a [Contacts2] sort, és hívja-e közvetve a 0x0068c030-at [blokkoló]
Ghidra-kör kell: 0x00692210 - honnan hívódik (tábla vagy vtable), és mikor fut a 0x0069b240 mentés [nem blokkoló]

Megválaszolva diszasszemblálással (35.2): `0x00767e50`, `face_zoom`-ra az argumentum közvetlenül, `picture_zoom`-ra az ellentettje.

### 28.8 Mérleg (2026-10-18)

- Leltár: 8 pont, mind RÉSZBEN; a Learn more KÉSZ.
- Új bináris eredmény: a Learn more kezelő és címe (megerősített); a [Contacts2] két jelölt (feltételes); a mentés-kezelő (0x006980a0) leírása; a `PeopleAlbumUseFaceSrc=1` → `face_zoom` mód leképezése diszasszemblálva; az első élő képkocka nyitott.
- Helyesbítés: a 27.1 „nem író” olvasata nem áll (28.3/a).
- Colab-javaslat: J0-J8 (28.5); a J0 és a J1 lefutott (job-207, job-208), a J3, J4 és J5 részben (job-209/210, job-213), a J2, J6, J7 és J8 nincs indítva.
- Fejlesztési következmény: a Learn more gomb PicasaPy-kezelőjét a jelenlegi forrás tartalmazza (lásd 19. szakasz); futásidejű külső megnyitást nem ellenőriztünk. A 19. szakasz két felirat-eltérése (a bal sáv sora és a mellőzött nézet darabszám-sora) javítási jelölt.

## 29. #5184, kilencedik kör: a 2026-10-18-i Ghidra-dump hat címe (2026-10-18)

**Hatókör:** a 27.4 lista 1., 2., 5., 7., 9. és 12. tétele. A forrás a `.ghidra8/2026-10-18-szemelykezeles-8-panzoom.txt` (a munkafában, a változtatások között nincs), kiegészítve a Picasa3.exe helyi diszasszemblálásával (`annot_disasm.py`, `find_data_refs.py`, `offset_map.py`), a `paszta.py` darabolt pásztázásával és a bináris-indexszel. A kérés a 29.3 és 29.4 szakaszokra hivatkozott; ilyen szakasz a lapon nem volt (a lap a 27.8-ig terjedt), ezért ez a kör hozta létre a 29. szakaszt (a 28. a #5185 leltára). A 0x008037e0 a #5225 kérdése: a `picasa-create-features.md` 4.5 szakaszában van.

### 29.1 Mit adott a dump

Hat cím: `0x008037e0` (#5225, lásd ott), `0x006980a0`, `0x004019b0`, `0x006cde50`, `0x00448fb0`, `0x00692210`. Mind a hat törzse olvasható, de a hívott függvények egy része nincs a dumpban (köztük a `0x006952e0`, a `0x006976f0`, a `0x00440af0`, a `0x009a4b20` és a `0x009a4a10`). Ezeknél a válasz csak részleges, a hiányzó törzs nevesítve van (29.7).

### 29.2 N6: `0x006980a0` és `0x00692210` (27.4 tétel 1 és 12)

**A C-törzsek.** `0x006980a0` a `this+0x5c >> 1` darabszámig hívja a `0x006952e0`-t (`this` és a sorszám argumentum), az első nem nulla eredménynél visszatér; ha nincs ilyen, és `this+0x458 != 0`, hívja a `0x006976f0`-t; végül `this+0x88 = 1` és 0 a visszatérés. A `0x00692210` a `this+0x1b4 >> 1` elemen megy végig: minden elemre hívja a `0x0068c5c0`-t, `this+0x438` esetén zárolt részt futtat, és minden elemre a `0x0069b240`-t; a `this+8` objektum +4 slotja a megszakítást figyeli (`0xf4242` a visszatérés).

**A két cím nem parancstábla, hanem vtábla-cella.** A kérés „parancstábla"-nak nevezte a `00ca7cc0` és `00ca7df8` címeket. Ezek a DATA-hivatkozások két RTTI-vtábla +0x6c és +0x70 slotjai:

| cella (DATA-hivatkozás) | vtábla (RTTI) | slot | függvény |
|---|---|---|---|
| `0x00ca7cc0` | `PrepareCollection::vftable` (`0x00ca7c54`) | +0x6c | `0x00692210` |
| `0x00ca7cc4` | ugyanaz | +0x70 | `0x006980a0` |
| `0x00ca7df8` | `AlignedImageCollection::vftable` (`0x00ca7d8c`) | +0x6c | `0x00692210` |
| `0x00ca7dfc` | ugyanaz | +0x70 | `0x006980a0` |

**Két független út.** A: az index DATA-hivatkozásai (a négy cella). B: az RTTI-vtábla kezdőcíme, a PE nyers értéke a cellában, és a vtábla határa: a következő RTTI-vtábla címe mindkét esetben 0xb8 bájttal később van (`0x00ca7d0c`, illetve `0x00ca7e44`), így a +0x6c és +0x70 slot mindkét vtáblán belül esik. Egyezik: a két út ugyanazt a négy cellát adja.

**Cáfoló kísérlet.** Határ nélküli, 256 slotos vtábla-keresésre a két cím 68 találatot ad 21 vtábla-kezdetnél (például `ytICollection` +0x2a4, `ytIBitmap` +0x2bc, `ytIPicasaApp` +0x1ec, `ytIPlugin` +0x2d8). A találatok közül csak négy esik a saját vtábla határán belülre: a két fenti vtábla +0x6c és +0x70 slotja. A többi 64 a következő RTTI-vtábla címén túl van, tehát a szomszédos memória átfedése, nem slot. A `PrepareCollection` +0x1a4 (`0x00ca7df8`) is kívül esik, ezért a `00ca7df8` az `AlignedImageCollection` +0x6c slotja.

**Hívók és hívás ideje: NINCS MEG.** Mindkét függvény virtuális slot, a hívóhelyek indirekt `call` (`call [reg+0x6c]`, `call [reg+0x70]`). A törlési út négy függvényében (`0x007ba820`, `0x007bb660`, `0x00584cc0`, `0x005836f0`) nincs olyan hívás, amelyről bizonyítható, hogy a két slotot hívja. A `0x005836f0`-ban a `[esi+0x6c]` egy kulcsként megy a `0x00409df0`-nak (mező, nem vtábla-hívás). A hívók típusa Ghidra-kör (29.7).

**N6 mentés-kérdés: NINCS MEG.** Abból, amit a dump ad, nem dől el, fut-e mentés a személy törlése után: a `0x006980a0` feltételes (a `0x006952e0` eredményétől és a `this+0x458`-tól függ), a `0x006952e0` törzse pedig nincs a dumpban. A `[Contacts2]` kiírója továbbra is NINCS MEG (a 27.1 korrekciója marad: a `0x00586e20` nem író).

### 29.3 N5: `0x004019b0` és `0x00448fb0` (27.4 tétel 2 és 5)

**`0x004019b0` egy Windows-registry beállítás-olvasó, nem tároló.** A C-törzs: `in_EAX` objektum `[0]` gyökérkulccsal és `[1]+4` útvonallal nyit (`0x009a4890`, előbb `0xf003f`, sikertelenségre `0x20019`), a `0x009a4b20`-nak az `in_EAX+3` címet adja át, az eredmény `in_EAX[3]`, a `RegCloseKey` zárja. A HÍVOTTAK között nincs `RegSetValue`, `RegCreateKey` vagy más író hívás. Második út: a `0x008037e0` ugyanezt a hívást használja a `FUN_00407a20(local_1c, "Preferences", "BigSlideshow2")` után (`0x0080381e`), tehát a `Preferences\BigSlideshow2` beállítást olvassa.

**Feltételes:** a `0x009a4b20` és a `0x009a4a10` törzse nincs olvasva, így az „csak olvas" állítás ezek hiányában nem teljes.

**A mappa-törlés tárolója: NINCS MEG.** A `0x00440af0` a `0x004019b0`-t a `0x00440b64`-ben hívja. A `0x00440af0` törzse nincs a dumpban, ezért nem dől el, mit olvas és hová ír a mappa-törlés. A `0x004019b0` maga nem tárolja a törlést (a beállítás-olvasó).

**`0x00448fb0` (N5, személy-predikátum).** A C-törzs: `this` zárolása (a `this+0x2754` jelzőtől függően a `this+0x2748` objektum +0x18 slotja, vagy a `this+0x2770` kritikus szakasz), rekurzió-számláló (`this+0x2768` tulajdonos-szál, `this+0x276c` darabszám). Tábla: a `this+0x27a0` mutató egy fejléc, `+0x4c >> 1` a darabszám, `+0x48` a 8 bájtos elemek. Ha az index a darabszámon belül van, az elem adja a visszatérési értéket, 0 kóddal; különben a `this+0x27a8` és `+0x27ac` alapérték, 4 kóddal.

**Megerősített:** a disasm `add esi, 0x2748` (`0x00448fbc`) után `esi = this+0x2748`, tehát a `this+0x27a0` a `[esi+0x58]` mező. Ezért a közvetlen `0x27a0`-os eltolás-keresés üres eredményt ad (a kereső nem látja a bázis-eltolt hozzáférést).

**A 64 bites érték jelentése: NINCS MEG.** A visszatérés a tábla eleme (index szerint), azonosító-e, nem dől el (a 25.5 szerinti „táblaindex" olvasat marad feltételes).

**A tábla írói: NINCS MEG.** A `this` osztálya nincs azonosítva: a `0x00448fb0`, a `0x0048e1f0`, a `0x0048ef20` és a `0x0048af60` egyik vtáblában sincs (a 256 slotos keresés nulla találatot ad), tehát nem virtuális tagok, és a vtáblából nem következtethető a típus.

### 29.4 N3: `0x006cde50`, a `DAT_00d35e44` és a `this+0x2908` (27.4 tétel 7 és 9)

**A `DAT_00d35e44` nem a Picasa3.exe-ben születik.**
- A `.data`-ban a `DAT_00d35e44` és a `DAT_00d35e48` nyers értéke 0 (PE nyers bájtok).
- A `.text`-ben a `DAT_00d35e44` 71 hivatkozása mind olvasás (`mov reg,[abs]`, `cmp [abs],imm`, `cmp [abs],reg`, `A1` moffs-alak). Írás nincs (`find_data_refs.py` és bájt-osztályozás).
- A `0x006ccd90` (a Red.dll betöltője) akkor tölt, ha `DAT_00d35e48` vagy `DAT_00d35e44` nulla: `push 0xd35e40` (egy struktúra címe), majd `call 0x006cc9e0`.
- A `0x006cc9e0` (210 bájt): `LoadLibrary` (`call [0xc402b8]`), `GetProcAddress` a `REDENTRY` sztringgel (`0xca8718`), a modul-mutató a struktúra +8 mezőjébe (`mov [esi+8], eax`, azaz `DAT_00d35e48`). Majd `lea ecx,[esi+4]` (`0x006cca6a`), `push ecx`, `push 1`, `call eax` (`0x006cca70`): a `DAT_00d35e44` a `REDENTRY` kimeneti mutatója.

Tehát a `0x006cde50` +0x44 hívása egy Red.dll-beli objektumon fut; a `DAT_00d35e44` nulla esetén a `0x006cde50` -1-et ad, és a +0x44 hívás nem fut.

**Két független út:** A: a `0x006cc9e0` diszasszemblálása (a `REDENTRY` hívás stack-argumentumai). B: a 71 olvasás, a nulla nyers érték, és a `0x006ccd90` ellenőrzési sorrendje. Egyeznek.

**Feltételes:** hogy a `REDENTRY` valóban a `DAT_00d35e44`-be ír (a Red.dll belsejét nem néztem).

**Cáfoló kísérlet.** A `0x00d35e40` (a struktúra) hivatkozásai: a `0x006ccdf2` (push), a `0x00c36711` (adat-jellegű, nincs függvényben), és a `0x00c36717` (`mov dword [0x00d35e40], imm`). Az utolsó a struktúra +0 mezőjét írja, nem a +4-et, és nincs függvényhez rendelve; nem cáfolja az írást, hanem megerősíti, hogy a struktúrának más mezői is vannak.

**A +0x44 célja: NINCS MEG.** A cél a Red.dll-beli objektum vtáblájában van. A Red.dll a kutatási másolatban megvan (`plugins/Red.dll`), de nincs a bináris-indexben, és ebben a körben nem vizsgáltam. Ez a 960 px kérdéssel együtt a Red.dll-re irányít (29.7).

**A `this+0x2908` írói: a `0x0048ef20`-ban van bázis-eltolt író (33.2); a közvetlen eltolású keresés 0-t adott, és ez téves volt.** A teljes `.text` darabolt pásztázása (`paszta.py`, 12 s) a `[reg+0x2908]` alakot két függvényben találja, mindkettőben olvasásként: `0x0048e1f0` (`mov edx, [ebp+0x2908]`, `0x0048e2b1`) és `0x0048ef20` (`[edi+0x2908]` a `0x0048f4d2`-nél, `[ecx+0x2908]` a `0x0048f6f1`-nél). Író 0. Ez csak a közvetlen eltolásra igaz; a bázis-eltolt írás (mint a `0x00448fb0`-ban az `add esi, 0x2748`) nem zárható ki.

**A detektor-bemenet mérete: NINCS MEG.** A `0x006cde50` méret-ágának forrása (`this+0x2908 >> 1`) a 27.x szerint marad, a tábla írója nincs. A 960 px nincs a Picasa3.exe C-kódjában (27.2), a Red.dll-ben lehet.

### 29.5 Ellenőrzések és eltérések

- **A „0x00586e20: 24 hívás" nem reprodukálható.** A teljes `.text` pásztázása 3 közvetlen `call`-t talál (`0x00485118`, `0x0068ac5a`, `0x007d5ca6`), az index szintén 3-at ad. A 24 a kérés szerint egy 29.3 szakaszban volt, amely a lapon nincs; ezért nem tudtam hozzá igazodni.
- A 0x0068ac20 hívja a 0x00586e20-t (`0x0068ac5a`), ez egybevág a 27.x szöveggel.

### 29.6 Állapot (N1-N8) a 29. kör után

Ez a tábla a 27.5 helyett érvényes.

| Pont | Állapot | Mi változott |
|---|---|---|
| N1 | BLOKKOLT | Változatlan (27.5). |
| N3 | BLOKKOLT | Új blokkoló: a `DAT_00d35e44` a Red.dll `REDENTRY`-objektuma (29.4). A +0x44 célja és a 960 px a Red.dll-ben van. A `this+0x2908` írói: nincs közvetlen író. |
| N4 | LEZÁRVA | Változatlan. |
| N5 | BLOKKOLT | A `0x004019b0` registry-olvasó, nem a mappa-törlés tárolója (29.3). A `0x00448fb0` tábla-írói és a 64 bites érték jelentése: NINCS MEG. |
| N6 | BLOKKOLT | A `0x006980a0` és `0x00692210` a `PrepareCollection` és `AlignedImageCollection` +0x70/+0x6c slotja (29.2, nem parancstábla). A hívók és a hívás ideje: NINCS MEG. A `[Contacts2]` kiírója: NINCS MEG. |
| N7 | BLOKKOLT | Változatlan. |
| N8 | BLOKKOLT | Változatlan. |

Nyitott kérdések: 0 nyílt · 1 lezárva (N4) · 6 blokkolt · 0 hatókörön kívül · 0 „csak nyitva".

### 29.7 Ghidra-kör kérések (a 27.4 maradéka, egységes alakban)

- Válasz [részben, 30.1-30.2]: a `0x006952e0` nem ír fájlt (fájl-API nincs a törzsében), feltétel nélkül hívja a `0x006956d0`-t; a `0x006976f0` hívási feltétele `this+0x458 != 0` (a hívó `0x006980a0` C-je). A [Contacts2] kiírója NINCS MEG (30.5).
- Ghidra-kör kell: `0x00692210` és `0x006980a0` hívóhelyei a `PrepareCollection` és `AlignedImageCollection` objektumokon (+0x6c / +0x70 slot): a hívó függvények típusa és a hívás ideje a törlési úton belül [blokkoló]
- Válasz [részben, 30.3]: a `0x0048ef20`-ban nincs `this+0x2748` hivatkozás, tehát az írói ezen a függvényen kívül vannak; a `this` osztálya NINCS MEG; a `0x0048ef20` `this+0x2908` íróiról a C és a diszasszemblálás ellentmond egymásnak (nyitott). A `0x00448fb0` és a `0x0048e1f0` törzse ebben a körben nincs vizsgálva.
- Ghidra-kör kell: `plugins/Red.dll` `REDENTRY` belépés: a `DAT_00d35e44`-be írt objektum vtáblája és annak +0x44 célja, valamint a 960 px helye (N3); a Red.dll nincs az indexben [blokkoló]

### 29.8 Bizonyítottsági fok és cáfoló kísérletek

**Megerősített:**
- (a) `0x00692210` és `0x006980a0` a `PrepareCollection` és `AlignedImageCollection` +0x6c / +0x70 slotja (29.2: A és B út).
- (b) `0x004019b0` beállítás-olvasó (Windows-registry): A: a C-törzs; B: a `0x008037e0` hívóhelye.
- (c) `0x00448fb0`: `esi = this+0x2748` a `0x00448fbc` után (disasm).
- (d) A `DAT_00d35e44` nem íródik a Picasa3.exe közvetlen címzésével: 71 olvasás, 0 írás, nulla nyers érték (29.4).

**Feltételes:**
- (e) `DAT_00d35e44` a `REDENTRY` kimeneti mutatója (a Red.dll belsejét nem néztem).
- (f) `0x006980a0` a `0x006952e0` eredményétől függ (a `0x006952e0` törzse nincs).
- (g) `0x004019b0` csak olvas (`0x009a4b20`, `0x009a4a10` nincs olvasva).

**Cáfoló kísérletek:**
- (a) ellen: a határ nélküli vtábla-keresés 21 vtábla-kezdetnél ad találatot, de a határon belüli találat csak a két valódi vtábla 4 cellája (29.2).
- (b) ellen: a közvetlen hívottak között nincs író API (`RegSetValue`, `RegCreateKey`), de a `0x009a4b20` belsejében lehet.
- (d) ellen: a `0x00d35e40` struktúra +0 mezőjét író `0x00c36717` nem a +4 mező.
- a `this+0x2908` íróira: a bázis-eltolt írás nincs kizárva.

**NINCS MEG:** a `0x006952e0` és `0x006976f0` törzse; a hívók típusa (`0x00692210`, `0x006980a0`); a `this` osztálya; a `0x00448fb0` tábla-írói és a 64 bites érték jelentése; a Red.dll +0x44 célja; a 960 px helye; a `[Contacts2]` kiírója.

### 29.9 Fejlesztési következmény

Nincs fejlesztési lista: az N-pontok egyike sem zárult le úgy, hogy eltérést mutatna a mi kódunktól. A 27.7 állítása érvényben marad. Jegytörzs-javaslat: nincs. Az új Red.dll-es blokkoló (N3) nem változtatja a felvételi tervet: a Colab-felvétel dönt (24.7).

## 30. #5184 és #5185, tizedik kör: a `ghidra-9` dump válaszai (2026-10-18)

**Hatókör:** a 28.7 `0x00587110` sora és a 29.7 `0x006952e0`, `0x006976f0`, `0x0048ef20` sorai. Forrás: a `.ghidra9/2026-10-18-ghidra-9.txt` (a munkafában, nem a változtatások része), kiegészítve a `referencia/ghidra/` helyi dumpokkal (`2026-10-18-szemelykezeles-8-panzoom.txt` a `0x006980a0` törzséhez, `2026-10-18-szemelykezeles-7.txt` a `0x005875d0` törzséhez) és a Picasa3.exe helyi diszasszemblálásával (`annot_disasm.py`).

### 30.1 `0x006952e0`: memóriabeli mentési sor, nem fájlíró

- A törzsében nincs fájl-API: a 19 hívott között nincs `CreateFile`, `WriteFile` és `0x0068c030`. Egyetlen hívója a `0x006980a0` (`006980c3`).
- A törzs: (1) új, 0x118 bájtos elemet foglal (`FUN_0097c5d0`, `FUN_0068c320`), és a `param_2` indexszel a `this+0x58` és `this+0x60` tömbökből tölti ki; (2) a `this+0x454` 16 dword-ös blokkját átmásolja az elemre (`+0xd8`); (3) az elemet a `this+0x1b0` tömbbe fűzi (`+0x1b4` számlálóval); (4) ha `this+0x47c != 0` és az elem `+0x54` bájtja nulla, meghívja a `0x0068c5c0`-t (C: 793. sor); (5) a `this+0x8c` táblában törli a bejegyzést; (6) **feltétel nélkül** meghívja a `0x006956d0`-t (C: 806. sor).
- A fájlírás tehát a `0x006956d0`-n át lehetséges. Ennek törzse nincs a dumpban; a korábbi dumpból ismert lánc (24.5): `0x006956d0` → `0x0068c030` (WriteFile). Ezt ebben a körben nem olvastam újra.

### 30.2 `0x006976f0` és a hívási feltétele (`this+0x458`)

- A hívója a `0x006980a0` (`006980e2`). Ennek törzse a `2026-10-18-szemelykezeles-8-panzoom.txt` 173-206. sorában van: ciklus a `this+0x5c >> 1` elemen a `0x006952e0`-val, az első nem nulla eredménynél visszatér; utána `if (*(int *)(param_1 + 0x458) != 0) FUN_006976f0(param_1);`, végül `this+0x88 = 1`.
- A hívási feltétel tehát `this+0x458 != 0` (C, a hívó törzséből).
- A `0x006976f0` maga nem olvassa a `this+0x458`-at (C: 837-1352. sor, nincs hivatkozás). Az `this+0x1b0` tömböt (`param_1[0x6c]`) és a `this+0x1b4` számlálót (`param_1[0x6d]`) járja be, és a `this+0x8` objektum zárját használja (`+0x14`, `+0x28`, `+0x2c`, `+0x30`). Fájl-API nincs a hívottjai között: ez frissítő menet, nem író.

### 30.3 `0x0048ef20`: a `this` osztálya és a `this+0x2748`

- A `this+0x2748` mezőre a függvényben nincs hivatkozás (a diszasszemblálásban nincs `0x2748`, `0x27a0`, `0x27a8`, `0x27ac` eltolás). Az írói tehát a függvényen kívül vannak; a 29.3 szerinti `0x00448fb0` bázis-eltolt `add esi, 0x2748` a jelölt.
- A `this` osztálya NINCS MEG: a függvény 15 indirekt hívást tartalmaz (`call [reg+...]`), a vtábla-azonosítás nem történt meg.
- **Ellentmondás feloldva (33.2):** a C-ben látható `this+0x2908` írások az asm-ben **bázis-eltolt** alakban vannak: a `0x0048f4d8` `add edi, 0x28c0` után a `0x0048f4ff` `mov [edi+0x48], ebx` a `this+0x2908` mezőt írja. A `[reg+0x2908]` alakú keresés ezt nem látja, ezért a 29.4 „író 0" állítása hibás (javítva a 29.4-ben).

### 30.4 `0x00587110`: a `[Contacts2]` olvasója, nem írója

- A függvény a `.ini` bejegyzést **olvassa vissza**. Sztringjei: „Restoring contact, %llx, from .ini file: id=%llx, ...", „Ignoring .ini contact, %llx, found matching contact, %llx, already in manager.", „Cannot restore .ini entry for contact, %llx, unexpected number of tokens in string." (C, 4050-4250. sor).
- A kulcs a 64 bites azonosító hexadecimális alakja (`FUN_0040eab0("%I64x", param_2, param_3)`), a szakasz neve `"Contacts2"` (`FUN_00985ff0`). Az értéket a `FUN_0099ac80` adja (ini-olvasás, törzse nincs a dumpban, feltételes), majd a `FUN_00988580` vesszőre (`DAT_00c81320`) bontja; pontosan hat tokent vár (`(local_a4 & 0xfffffffe) == 6`).
- Hat token esetén duplikáció-ellenőrzés (`FUN_00586040`), zár, `FUN_00588210`, majd `FUN_005875d0` (beszúrás a memóriába). Fájl-API nincs a törzsben.
- Egyetlen hívója a `0x0045a9d0` (`0045ba28`), a `.picasa.ini` mappafüggvény (28.3/b). Annak viselkedését ebben a körben nem vizsgáltam, ezért a betöltési szerep feltételes.
- **A `0x005875d0`:** memóriabeli beszúrás. A `this+0x13c` bájtot 1-re állítja (piszkos jelző; a C-ben `param_1 + 0x4f`, mutató-indexelés), és a `this+0xcc` és `+0xd0` mezőkhöz nyúl (C-ben `param_1[0x33]`, `param_1[0x34]`; `FUN_0058f5a0`, `FUN_0058f640`, `FUN_0058f910`). A 17 hívottja között nincs fájl-API (a teljes lista ellenőrizve), és a törzsben nincs `0x0068c030`-hívás.

### 30.5 Állapot

- A `[Contacts2]` kiírója: **NINCS MEG**. A `0x00586e20` kiírói jelöltsége (28.3/a) nyitott marad.
- N6 (29.6): a `0x006952e0` nem író. A fájlírás a `0x006956d0` → `0x0068c030` láncon át lehetséges (korábbi dump). A mentés kiváltója, a `0x006980a0` hívója NINCS MEG.
- Blokkolt pontok: N3, N5, N6, N7, N8 változatlanul blokkolt.

### 30.6 Bizonyítottsági fok és cáfoló kísérletek

- **Megerősített:** a `0x006952e0` fájl-API-mentessége (a teljes HÍVOTTAK-lista és a C); a `0x006976f0` hívási feltétele (`this+0x458 != 0`; a hívó C-je, és a `0x006976f0` nem olvassa a mezőt); a `0x00587110` olvasó jellege (a C-sztringek és a hívott-lista egyezik: a törzsben nincs íráshoz tartozó hívás).
- **Feltételes:** a `FUN_0099ac80` olvasó jellege (törzse nincs a dumpban, a név és a használat alapján); a `0x006956d0` → `0x0068c030` lánc (korábbi dump, 24.5).
- **Nyitott:** a `0x0048ef20` `this`-osztálya; a `this+0x2908` íróinak C és asm ellentmondása.
- **Cáfoló kísérlet (a `0x00587110` íróként):** ha írna, a törzsében vagy a közvetlen hívottjai között fájl-API vagy `0x0068c030` lenne. Sem a C hívott-listájában, sem a diszasszemblálásban nincs ilyen (28.3/b összevetve). A cáfolat sikeres.
- **Cáfoló kísérlet (a `0x006952e0` íróként):** a törzsben nincs fájl-API, ezért a közvetlen írás kizárva. A `0x006956d0`-n át lehetséges írás nyitott.

### 30.7 Fejlesztési következmény

- Kódmódosítás nem következik: a `[Contacts2]` kiírása továbbra is blokkolt, a személykezelés felvételi terve (24.7) változatlan. Jegytörzs-javaslat: nincs.

## 31. #5184, tizedik kör: a Contacts2 írási lánc teljes .text-pásztázása (2026-10-18)

### 31.1 A pásztázás eredménye

A `paszta.py` teljes `.text`-utasításpásztázása a `memoria_kapu()` hívásával indult, még az utasítások bejárása előtt. A PE-ben **2 884 879 utasítás** volt; a mért csúcsmemória **107,8 MiB**. A Contacts2 cím `0x00c9105c`, a `.picasa.ini` cím `0x00c80a6c`. Az importtáblában nincs `WritePrivateProfileStringA/W`; a `WriteFile` IAT-cím `0x00c40240`.

A közvetlen `WriteFile` hívások **20 utasításhelyen, 10 függvényben** vannak: `0x0068c030` (4), `0x0092d6d0` (3), `0x0099d950`, `0x0099df20`, `0x0099df60`, `0x0099dfa0`, `0x009e9290`, `0x009e93d0`, `0x00aab5c0` (egyenként 1), valamint `0x00c0ec24` (6). Ez a teljes írólista; a korábbi „a `0x0068c030` az egyetlen fájlíró” megállapítás csak a korábbi, kisebb dump hatókörére volt igaz.

### 31.2 A jelöltek és az INI-kiíró lánc

- **`0x00587110` a Contacts2 olvasó útja.** A Ghidra C-törzs a `Contacts2` szekcióból keres, majd az azonosítót `%I64x` formában állítja elő és nevet, e-mailt olvas vissza. A hívója `0x0045a9d0`, amely a `.picasa.ini`-t kezeli; annak hívója `0x0047e470`. A `0x0045a9d0` útja eléri az általános INI-véglegesítőt, de ez önmagában nem bizonyítja, hogy az olvasási művelet új Contacts2-adatot ír.
- **`0x00586e20` a névjegy-tárolás jelöltje, közvetlen fájlírása nincs igazolva.** A teljes pásztázás három közvetlen hívót talált: `0x00484820`, `0x0068ac20`, `0x007d55f0`. Az utóbbi a `0x007d5ca6` helyen hívja, majd a nem nulla hibakódnál a `PersistContactToINI failed: err %d` szöveget adja át. A `0x00586e20` Ghidra-dumpja sok elérhetetlen blokk eltávolítására figyelmeztet, ezért az egyszerűsített C-törzs nem dönti el a belső módosítást. A teljes `.text`-pásztázás nem talált benne közvetlen fájl-API-hívást.
- **A legerősebb lemezre író út a `0x00484820` környezetében van.** A függvény a `0x004849a7` helyen a `.picasa.ini` útvonalat adja át a `0x00410610`-nek, a `0x00485118` helyen hívja a `0x00586e20`-t, majd a `faces`, `facedata` és `backuphash` kulcsok frissítése után a `0x00410770`-t hívja (`0x00485256`, `0x004852b0`). A közvetlen hívási lánc innen `0x00410770` -> `0x009bef50` -> `0x009bd640` -> `0x0099dfa0`. A `0x009bd640` a `[%s]\n%s=%s\n` és `%s=%s\n` INI-formátumokat használja; a `0x0099dfa0` a teljes pásztázásban `WriteFile`-hívó. Ez a lánc alátámasztja az arcadatot kezelő művelet és az általános INI-kiírás kapcsolatát, de a dump nem bizonyítja, hogy minden `0x00586e20` hívás után kiírás történik, vagy hogy a `0x00586e20` maga állítja elő a Contacts2 sort.

## 32. #5184, N6: Contacts2 mentés, Choose és azonosító

### 32.1 Író és mentési lánc

**Feltételes eredmény:** a `0x00586e20` a kontaktszintű INI-persistálás segédjének legerősebb jelöltje. A lemezre író általános végpont a `0x0099dfa0` `WriteFile`-hívó; a Contacts2-t is érintő arcadatút a `0x00484820`-on keresztül jut el az INI-véglegesítőhöz. A `0x00587110` olvasó, ezért nem a Contacts2-sor írója. A pontos, Contacts2-bejegyzést memóriában előállító függvény és annak feltételes ágai **NINCS MEG**.

### 32.2 A kiváltó esemény

**Mérés:** a hívó által rögzített job-179 megfigyelés szerint a `[Contacts2]` bejegyzés a Személykezelő **Choose** művelete után megjelenik a `.picasa.ini`-ben. Ez a felvétel a felhasználói eseményhez köti a megjelenést, de a fájldiff és az ablakbezárás időzítése nincs a mérőcsomagban, ezért azt nem dönti el, hogy a kiírás a kattintás kezelőjében vagy a művelet utáni lezáráskor fut.

A `Choose` feliratot tartalmazó kezelő `0x007b81e0`; közvetlenül nem hívja a `0x00586e20`-t. A közvetlen hívásgráf nem mutatja meg, hogy a két műveletet indirekt callback köti-e össze.

### 32.3 A contact ID alakja és a PicasaPy jelenlegi útja

Az eredeti két olvasási/persistálási kódrészletben a formátumsztring `%I64x` (`0x00c82fcc`): 64 bites, kisbetűs hexadecimális alak, **kitöltő nulla és minimális szélesség nélkül**. Ez legfeljebb 16 hexadecimális jegyet jelent, de az eredeti azonosító-előállító nem került elő; a minden esetben pontosan 16 jegyű eredeti kulcs **NINCS MEG**. A `meroadat.tar` archívumban átnézett `.picasa.ini` példák között nem volt `[Contacts2]` szakasz, így a job-179 nyers kulcsértéke a helyi mérőadatból nem ellenőrizhető.

**PicasaPy most:** a közös `generate_contact_id()` nem nulla 64 bites véletlen értéket ír ki `format(n, "x")` alakban; a `people_controller.py`, `faces_helper.py` és `pmpimport/arcatvetel.py` ezt használja. A `[Contacts2]` kulcs és a `faces=` hivatkozás ugyanazt a kisbetűs, kitöltés nélküli azonosítót kapja. A már meglévő azonosítók (köztük a 16 jegyű, vezető nullás alakok) megmaradnak. A központi `contacts.xml` egyesítője és írója 1-16 jegyű hexadecimális ID-t fogad el, hogy a rövidebb új kulcsot is tárolhassa.

**Felvétel (job-213, 2026-10-18):** a futás végi `.picasa.ini` `[Contacts2]` kulcsa `3c067b829137b19`, vagyis 15 kisbetűs hexadecimális jegy, vezető nulla nélkül. Ez a binárisból olvasott, kitöltés nélküli `%I64x` alakot erősíti meg, két független úton (bináris és felvétel): egy 16 jegyre kitöltött formátum sosem adna 15 jegyet. Egyetlen minta a kitöltés hiányát mutatja, a tartományt nem.

### 32.4 Független utak és cáfoló kísérlet

- **A út:** a teljes utasításpásztázás és a hívóhelyek szerint a `0x00484820` ugyanabban a műveletben hívja a `0x00586e20`-t, módosítja az arcadat-kulcsokat, majd eléri az INI-szerializálót és a `WriteFile`-hívót.
- **B út:** a `0x007d55f0` hívóhelyén a `0x00586e20` hibakódját a `PersistContactToINI failed` üzenettel naplózza; ettől függetlenül a `0x00587110` C-törzse olvasási műveletként azonosítja a másik Contacts2-jelöltet.
- **Egyezés:** mindkét út a `0x00586e20`-t a kontakt-INI művelethez köti, és kizárja, hogy a `0x00587110` legyen az író. A konkrét Contacts2-sormódosítást és a Choose callbacket egyik sem bizonyítja.
- **Cáfoló kísérlet:** azt az állítást ellenőriztem, hogy a `0x00586e20` maga a közvetlen fájlíró. A teljes IAT-célpásztázás nem talált közvetlen fájl-API-hívást benne, miközben a `WriteFile`-hívók külön listában azonosíthatók. Ez cáfolja a közvetlen író értelmezést, de az indirekt, segédhíváson át történő adatfrissítést nem zárja ki. Azt az állítást is cáfoltam, hogy az eredeti formátum garantálja a 16 jegyet: a `%I64x` formátumsztringben nincs szélességkitöltés.

**Bizonyítottsági fok:** a hívási útvonal és a felhasználói esemény kapcsolata **feltételes**. N6 egészének állapota **BLOKKOLT**: a pontos Contacts2-mutációs függvény, a Choose callback és a személytörlés utáni kiírás időzítése nyitott.

### 32.5 Nyitott Ghidra-kérdések

- Ghidra-kör kell: `0x00586e20` - melyik belső ág módosítja a Contacts2 adatot, és milyen feltétellel hívja vagy ütemezi az INI-véglegesítést [blokkoló]
- **Megválaszolva (23. kör, 37. szakasz):** a `0x007b9630` és a `0x007ba060` mindketten hívja a `0x007b81e0` Choose-kezelőt. A `[Contacts2]` kiírásának időzítése futásidejű adat: Colab-felvétel javasolt (37.4), a statikus hívási út a 24. körben (37.6): a `0x007b9f20` a Névjegyek frissítése ága, nem a személytörlés útja; a törlés útja feltehetően a `0x007b93c0` (37.6)
- **Válasz [részben] (#5184, 2026-10-18, 11. kör):** a `0x00586540` nem állítja elő a contact ID-t, hanem keres. A `this+0x38` alatti térképobjektumból (`0x0058fc40`) a kulcs hash-értéke (`0x00409df0`) szerint kiválasztott láncolt listát járja végig, és az első, `0x006f9890` egyezés-ellenőrzésen átmenő elem `+0x10` és `+0x14` dword-jét másolja a `param_4`-be (a C-dumpban: `*param_4 = puVar3[4]; param_4[1] = puVar3[5];`). A visszaadott alak tehát **8 bájt** (két dword): ez a memóriabeli találat mérete. A második ág (`0x00586a60`, bemenete a `puVar3[4]`, `puVar3[5]`) állítja elő a jelölt azonosítót, és a `param_3` karakterláncával hasonlít össze, 2 bájtonként (széles karakter, valószínűleg UTF-16). Bizonyítottsági fok: **feltételes** (egy út: a C-törzs). Az „eredeti tárolt alak szélessége" **NINCS MEG**: a 8 bájt a memória-elem mérete; az INI-ben tárolt alak külön kérdés (a `%I64x` formátum 16 hexa-jegy, 30.4).
  - Ghidra-kör kell: `0x00586a60` - a contact ID-jelölt előállítása a `puVar3[4]`, `puVar3[5]` bemenetből, és a `param_2` kulcs alakja [blokkoló]

### 32.6 A #5184 „Kész, ha” pontjainak állapota

| Pont | Állapot | Bizonyíték |
|---|---|---|
| N1, névvel jelölt képen további ismeretlen arc | ⛔ BLOKKOLT | A 29.6 szerinti felismerés utáni ág és Colab-mérés nyitott. |
| N3, eredeti felismerési arány és küszöb | ⛔ BLOKKOLT | A 29.4 szerint a 960 px helye a Red.dll-ben nyitott; arányra nincs mérés. |
| N4, név és keret alapállapota | ✅ LEZÁRVA | A job-187 mérés: névvel jelölt arcon alapból sem keret, sem név nem látható (20. szakasz). |
| N5, személyszintű mellőzés | ⛔ BLOKKOLT | A 28.4/a szerinti tényleges írási hely nyitott. |
| N6, személytörlés és Contacts2 mentés | ⛔ RÉSZBEN | A Choose utáni megjelenés mért, a kontakttároló útvonal részben feltárt; a pontos callback, mutáció és törlési mentés nyitott (29.2, 31.). |
| N7, kijelölési modell | ⛔ BLOKKOLT | A `contactmgr.fen` lista-erőforrása nem dönti el az egyes vagy többes kijelölést (28.4/c). |
| N8, People Manager referencia-kép | ✅ LEZÁRVA | A job-186 24. képe a 631 x 351-es People ablakot és a vezérlőket rögzíti; a mérési leírást a jegy tartalmazza. |

Nincs új fejlesztői lista: a PicasaPy jelenlegi 16 jegyű azonosítója és INI API-n át történő mentése nem bizonyítottan tér el az eredetitől. N6 lezárásához a fenti három célzott Ghidra-kérdés és a Choose előtti/utáni fájldiff szükséges.

## 33. #5184, tizenegyedik kör: `0x006956d0` állapotgépe, a `this+0x2908` alias-írója és a `0x00586540` (2026-10-18)

**Forrás:** a `.ghidra10/2026-10-18-ghidra-10.txt` (C-dump: `0x006956d0`, `0x00430610`, `0x0048ef20`, `0x00586540`), kiegészítve a Picasa3.exe capstone-diszasszemblálásával (`annot_disasm.py`). A diszasszemblált kimenet nem került a repóba.

### 33.1 `0x006956d0` → `0x0068c030`: a kapu és az állapotbájt

- A `0x0068c030` (fájlíró, 22.5) hívása (`0x00697557`; C-dumpban az 1512-1513. sor) előtt `cmp byte ptr [esp+0x1b], 2` (`0x00697540`) áll: a hívás **csak** akkor fut, ha az állapotjelző bájt 2.
- Az állapotjelző bájt (C-ben `uStack_1608._3_1_`) írói a diszasszemblálásban:
  - `0x00695737` = 1 és `0x0069573e` = 0 (a C 189-192. sora, a `param_3[0x40]` ágon);
  - `0x00696d36` = 2: az 1-es ágban, a `0x0068ac80` hívás (`0x00696d31`) után; ez a C-dumpban nem látszik;
  - a `0x00506270` táblakeresés (`0x00695a52`), amely a `this+0x3f0` tábla bejegyzésének `+0x20` mezőjét írja `*arg`-ba, ha a bejegyzés típusa `0x3e9`; egyébként az elem nyers értéke marad.
- Az 1-es ág feltétele: `[esp+0x1b] == 1` és `[ebx+0x100] != 0` (`0x00696cf5-0x00696d0e`). A spec 23.5/24.5 állítása (a `0x0068c030` csak a 2-es állapotnál fut, az 1-es első lépése a `0x0068ac80`) így **megerősítve**: a C-dump és a diszasszembly egyezik.
- **Feltételes:** a „mikor" pontos feltétele, mert a `0x00696d3b` és a `0x00697540` közti vezérlési út nincs végigkövetve, és a `this+0x3f0` tábla feltöltése sincs megnézve.

### 33.2 `0x0048ef20`: a `this+0x2908` írója bázis-eltolt

- A `0x0048f4cb` ágban: `mov edi, [esp+0x150]` (a `this`), `mov ecx, [edi+0x2908]` (`0x0048f4d2`), `add edi, 0x28c0` (`0x0048f4d8`), majd `mov [edi+0x48], ebx` (`0x0048f4ff`). Mivel `edi = this+0x28c0`, a tárolás a `this+0x2908` mezőt írja (`0x28c0 + 0x48 = 0x2908`). A C-ben ez a `*(float **)(param_1 + 0x2908) = pfVar18;` megfelelője.
- Az igazolt író tehát megvan. A többi C-beli író (`0x0048f282`, `0x0048f35f`, `0x0048f395`, `0x0048f84f`, `0x0048f886`, mind `[ebp+0x48]` vagy `[esi+0x48]`) ugyanezt az eltolást használja, de az alap-regiszterük forrását **nem követtem végig**.
- A `this+0x28c0` alobjektum zárral védett tömb: a `+0x20` (`this+0x28e0`) tulajdonos-szál, a `+0x24` (`this+0x28e4`) rekurzió-szám, a `+0xc` CS-jelző és a `+0x28` CRITICAL_SECTION. Ez a `0x00506270` zármintájával egyezik; a `+0x48` a tömbmutató (`this+0x2908`), a `+0x4c` a darabszám-jelző (`this+0x290c`).
- **A `this` osztálya: NINCS MEG.** A `0x0048ef20` nem konstruktor (nincs vtábla-írás a törzsében). A vtáblát a hívóknál kell keresni: `0x00414940`, `0x0047b020`, `0x00536a90`, `0x005c6500`.

### 33.3 `0x00586540`

- A válasz a 32.5 alatt van (részben: a 8 bájtos találat-alak megvan, az ID-előállítás a `0x00586a60`-ban van).

### 33.4 Cáfoló kísérletek

- **33.1 cáfolata:** kerestem olyan írót, amely az 1-es ágban a `[esp+0x1b]`-et 2-n kívül más értékre állítja: nincs (a 0/1 írók a 189-192. sor ágában vannak). A `0x00506270` nem ad 2-t, ha a bejegyzés típusa nem `0x3e9`.
- **Nyitott ellenpélda:** ha egy nyers elem felső bájtja 2 (az elem ≥ `0x02000000`), a sikertelen `0x00506270`-keresés után is 2 marad a bájtban, és a `0x0068c030` lefut. Az elemek forrása nincs megnézve, ezt nem zártam ki.
- **33.2 cáfolata:** a `[reg+0x2908]` alakú keresés nulla írót adott; a `[edi+0x48]` alakú tárolás ezt a nullát cáfolja. Más íróhelyet nem kerestem.

### 33.5 Bizonyítottsági fok

- `0x006956d0` → `0x0068c030` hívási kapu (`[esp+0x1b] == 2`): **megerősített** (C-dump és capstone-diszasszembly).
- Az 1-es → 2-es átmenet a `0x0068ac80` után: **megerősített** (asm); a C-dumpban nincs.
- A „mikor" (melyik elem vagy tábla-bejegyzés éri el a 2-t): **feltételes**.
- `this+0x2908` íróinak C és asm egyeztetése: **megerősített** a `0x0048f4ff` íróra; a többi alias nincs végigkövetve.
- A `this` osztálya: **NINCS MEG**.

### 33.6 Nyitott Ghidra-kérdések

- Ghidra-kör kell: a `this+0x3f0` tábla bejegyzéseinek írói (a `0x00506270` olvassa: a `0x3e9` típus és a `+0x20` érték forrása); a 2-es állapot innen jön [blokkoló]
- Ghidra-kör kell: a `0x0048ef20` egyik hívójának (`0x00414940`, `0x0047b020`, `0x00536a90`, `0x005c6500`) törzse: melyik objektum-osztály `this`-e a `0x0048ef20` bemenete, és hol van a vtábla-írás [blokkoló]

## 34. #5184, 11. Ghidra-kör: a contact ID-jelölt, a `this+0x3f0` tábla és a felvétel-kapu (2026-10-19)

**Hatókör:** a 32.5 szakasz `0x00586540` sora és a három új cím: `0x00586a60`, `0x00506270`, `0x00414940`. Forrás: a 11. dump (`.ghidra11/2026-10-19-ghidra-11.txt`, 1307-1618. sor), a bináris-index hívólistái és `string_xrefs` táblája. Diszasszemblálás ehhez a három címhez nem készült.

### 34.1 `0x00586a60`: kulcsellenőrző és továbbadó, nem előállító

A függvény `uint FUN_00586a60(uint param_1, uint param_2, int *param_3, int param_4)`. A `this` a regiszteren érkezik (C: `in_EAX`). Sorrend:
1. `puVar1 = *param_3` nem nulla; `(*puVar1 & 0xffffff00) != 0`; `(char)puVar1[1] != 0`. Ha nem teljesül, a visszatérés `0xffffffff`.
2. A kulcs `(param_1, param_2)`: nem lehet mindkettő nulla, és `(param_1 & param_2) != 0xffffffff` (vagyis nem mindkét dword `-1`). Ha nem teljesül, `0xffffffff`.
3. A `this` zárja alatt (tulajdonos `+0x20`, rekurzió `+0x24`, jelző `+0xc`, kritikus szakasz `+0x28`) hívja a `0x00588290(this, param_1, param_2)`-t.
4. Nem nulla eredmény: `param_4 != 0` esetén `0x0057fb50`, a visszatérés `0`. Nulla eredmény: a visszatérés `9`.

Következmény:
- **Az előállítás nem ebben a függvényben van.** A `puVar3[4]`-et és a `puVar3[5]`-öt nem olvassa; a `*param_3` objektumból csak az első két mezőt nézi (`+0x0`, `+0x4`). A `puVar3[4]`, `puVar3[5]` → kulcs leképezés a hívóban (`0x00586540`, a `0x00586794` hívás előtt) vagy a `0x00588290` törzsében van. **NINCS MEG** a dumpban.
- **A kulcs alakja:** 64 bites, két dword (`param_1`, `param_2`); a `(0, 0)` és a `(-1, -1)` pár nem érvényes. A 16 jegyű alak (32.3) nincs a formátumsztringből garantálva (a `%I64x`-nek nincs szélességkitöltése); a két dword sorrendje (melyik az alacsony rész) **NINCS MEG** ebből a törzsből.
- Visszatérési kódok: `0` (a `0x00588290` sikeres), `9` (sikertelen), `0xffffffff` (érvénytelen objektum vagy kulcs).

*Bizonyítottsági fok:* **megerősített** az ellenőrzési sorrend és a három visszatérési kód (C-törzs). **NINCS MEG** az előállított jelölt és a két dword sorrendje.

Megválaszolva részben (12. kör): a `0x00588290` NEM állít elő contact ID-jelöltet, hanem 64 bites kulcs KERESŐJE. A `(param_4 | param_5) != 0` és a `(param_4 & param_5) != 0xFFFFFFFF` ellenőrzés (az `-1` érvénytelen kulcs) után a `FUN_0058fc40(param_3+0xe0, param_2)` al-táblát kéri (nem dekompilált), a bucket-indexet a `__aullrem(param_4, param_5, [al-tábla+0x1c], 0)` adja (64 bites modulo), a láncban a `puVar2[2] == param_4 && puVar2[3] == param_5` összevetés dönt, és a találat `puVar2+2` (a tárolt kulcs címe), különben 0. A jelölt előállítása a négy hívó egyikében van (`0x0058470f`, `0x00584b8e`, `0x00585c9c`, `0x00586aef`), ezek törzse nincs dekompilálva. **Bizonyítottsági fok:** a keresés logikája **feltételes** (C, egy út); a jelölt előállítása **NINCS MEG**. Megválaszolva részben (13. kör, 34.7): a `0x00584280` nem állít elő kulcsot, hanem fogyasztja. A kulcs-tömb a `0x0084d090` hívásában a `[edi+0x10]` mező. Ghidra-kör kell: 0x0084d090 - az `[edi+0x10]` 64 bites kulcs-tömb írója, és a `0x00584b00`, `0x00585ad0` hívóinak kulcsa [blokkoló]
Megválaszolva részben (12. kör): a `0x00586794` `call 0x00586a60` (diszasszembly; az index `0x00586540` → `0x00586a60` éle is ezt adja). Argumentumai a C szerint: `puVar3[4]`, `puVar3[5]` (a `this+0x38` táblából a `FUN_0058fc40(this+0x38, param_2)` által adott al-tábla `+0x30` hash-mezővel indexelt láncának csomópontja: a 64 bites kulcs), `param_2` (a kulcs-sztring mutatója, a hívó 2. argumentuma), és `local_34` (kimeneti; a `0x0058677c`-`0x00586790` sorok nullázzák). A `param_3` a második objektum (`*param_3` a sztring, `param_3[9] >> 1` a darabszám). A push-sorok ellenőrzése diszasszembly-munka, nem Ghidra-kör. **Bizonyítottsági fok:** a hívás **megerősített** (asm és index); az argumentumok forrása **feltételes** (C). Ghidra-kör kell: a `0x00586540` hívásának C-je már megvan; a `param_3` objektum forrása a `0x00586540` nyolc hívójában (0x00586175, 0x00586946, 0x00586a05, 0x0058764a, 0x007d5ac7, 0x0084ceff, 0x0084d023, 0x0084edc4) [nem blokkoló]

### 34.2 `0x00506270`: a `this+0x3f0` tábla olvasója

`int FUN_00506270(uint *param_1)`: a `this` a `EAX`; a bemenet a `*param_1` index. A `this` zárja alatt:
1. Ha `index >= ([this+0x3f4] >> 1)`, a visszatérés `4`. (A darabszámot `>> 1`-gyel olvassa, ahogy a `0x0042c830` és a `0x00429dc0` listáinál.)
2. Az elem a `this+0x3f0` tábla `[index]` mezője; ha nulla, az alap-rekord a `this+0x3f8`.
3. Ha az elem `+0x18` mezője `0x3e9` (1001, arcsablon-bejegyzés, 9/c), a `*param_1` a rekord `+0x20` mezője, a visszatérés `0`.
4. Egyébként a visszatérés `9`.

- **Írói: NINCS MEG.** A függvény csak olvas: a `this+0x3f0`, `+0x3f4`, `+0x3f8` mezőkre nincs értékadás. Az írók a dumpon kívül vannak. Keresésük a `this+0x3f0` eltolásra `find_members.py`-val lehetséges, de teljes `.text`-pásztázás csak a `paszta.py`-n át megy (SKILL 2/a); ezt a körben nem futtattam.
- **A „2-es állapot” nem ennek a függvénynek a visszatérése.** A kódok 0, 4, 9. A 2 forrása a hívóban vagy a rekord más mezőjében van; **NINCS MEG**.

*Bizonyítottsági fok:* **megerősített** a három visszatérési kód és a `0x3e9` / `+0x20` olvasat (C-törzs). **NINCS MEG** az írók és a 2-es állapot forrása.

Ghidra-kör kell: 0x00506270 - a 42 hívó közül melyik olvassa a `this+0x3f0` táblát, és melyik ad 2-es állapotot a 0 / 4 / 9 kódok mellé [blokkoló]

### 34.3 `0x00414940`: a `FRAddSuggesetions` beállítással kapuzott indító

`int FUN_00414940(int param_1)`. A `this` a regiszteren (`ESI`) érkezik (C: `unaff_ESI`); a típusa a dumpban nincs meg. A lépések:
1. A `this+0x34a9` jelző 1: visszatérés `0xf4241` (1000001). Különben 1-re állítja.
2. Ha az argumentum alsó bájtja 0 (nem kényszerített hívás): tovább csak akkor megy, ha `DAT_00d67849 != 0`, `this+0x2db0 == 0` és `FUN_009a51b0(this+0x2810) >= 15.0`. A `15.0` a `0x00c7d9d8` double-értéke (a PE `.rdata`-ból olvasva). Ha nem, `this+0x34a9 = 0`, visszatérés `0xf4241`.
3. Beállítás olvasása: `Preferences` / `FRAddSuggesetions` (a kulcs neve a binárisban elírt, a sztring a `0x00c81b7c`) a `0x004019b0`-lal. Ha hamis: `this+0x2810` = most, `this+0x34a9 = 0`, visszatérés `0`.
4. Ha igaz: ha `DAT_00d4a62c != 0` és a `0x009a7fe0` már foglalt állapotot ad (nem nulla és `*local_24 != 0`), visszatérés `0xf4242` (1000002). Különben `0x0048ef20(this, &param_1, 0, 0, 0, 0)`, majd `this+0x2810` = most, visszatérés `0`.

Hívói (a dump fejléce): `0x0047b020` (a `0x0047b189` helyen), `0x006a10b0` (a `0x006a12fa` és `0x006a1332` helyen). Ezek törzse nincs a dumpban.

- **A `this` osztálya: NINCS MEG.** Ebben a függvényben nincs vtábla-írás; a típus a hívókból vagy a konstruktorból jön.
- **A `0x0048ef20` hívásának feltétele:** a 3. és a 4. lépés; vagyis a `FRAddSuggesetions` igaz, a 15.0 küszöb teljesül (vagy kényszerített hívás), és a szálfoglalás nem ütközik.
- **Mértékegység:** a `0x009a51b0` visszatérési egysége **NINCS MEG**; a 15.0 csak azt mondja, hogy a két QPC-mintából számolt érték ezzel vethető össze.

*Bizonyítottsági fok:* **megerősített** az 1-4. lépés (C-törzs; a kulcs a `string_xrefs`-ben is megvan). **NINCS MEG** a `this` típusa és a 15.0 mértékegysége.

Megválaszolva részben (12. kör): a `0x00414940` hívói az index szerint `0x0047b020` (1 hívás) és `0x006a10b0` (2 hívás). A `0x0047b189` a `push 1` (`0x0047b187`) után hívja a `0x00414940`-t (diszasszembly), és ez a `in_EAX[2] == 0` ágon fut (C). A `this` a belépéskor EAX-ben van (C: `in_EAX`); hogy ESI-be hova kerül, a függvény elejét nem ellenőriztem. A `this` típusa NINCS MEG: a `0x0047b020` egyetlen hívója a `0x004987c0` (`0x00498933`). **Bizonyítottsági fok:** a hívó és az argumentum: **megerősített** (asm és index); a `this` típusa: **NINCS MEG**. Megválaszolva részben (13. kör, 34.7): a `0x0047b020` `this`-e a `0x004987c0` `0x00498933` hívásában `EAX = [esi+0x6c] + 4`, ahol az `esi` a worker (`0x004987c0` `this`-e, `mov esi, ecx` a belépésnél). A `[worker+0x6c]` objektum típusa NINCS MEG. Ghidra-kör kell: 0x0047bc80 - a worker `+0x6c` mezőjének létrehozója és típusa (a `0x0047bc80` három `0x004987c0` hívása) [blokkoló]
Ghidra-kör kell: 0x006a10b0 - a két hívó (`0x006a12fa`, `0x006a1332`): azonos osztály-e a `this`, és hol van a vtábla-írás [blokkoló]
Ghidra-kör kell: 0x009a51b0 - a visszatérési érték egysége (másodperc vagy tick) [nem blokkoló]

### 34.4 A 32.5 `0x00586540` sora

Részben válaszolt: a `0x00586a60` a `0x00586540` hívottja (`0x00586794`), így a jelölt-kiválasztás a `0x00586540` és a `0x00588290` törzsében van. Mindkét törzs hiányzik a dumpból, ezért a sor `[blokkoló]` marad, a hiányzó törzsek megnevezésével (33.1).

### 34.5 Bizonyítottsági fok és cáfoló kísérletek

- **Cáfoló (34.1):** azt állítottam, hogy a `0x00586a60` állítja elő a jelöltet. A C szerint csak ellenőriz és továbbad. **Cáfolva** a dump alapján; a `0x00588290` belső előállítása nincs kizárva.
- **Cáfoló (34.2):** azt állítottam, hogy a `0x00506270` ír a táblába. Nincs C-értékadás a `this+0x3f0`-ra. **Cáfolva** a dump alapján (olvasó).
- **Cáfoló (34.3):** azt állítottam, hogy a `0x00414940` vtábla-írást végez a `this`-en. A C-ben nincs. **Cáfolva** a dump alapján; a hívók nincsenek a dumpban.

### 34.6 Ghidra-kör kérések egy helyen

- Megválaszolva részben (12. kör): a `0x00588290` NEM állít elő contact ID-jelöltet, hanem 64 bites kulcs KERESŐJE. A `(param_4 | param_5) != 0` és a `(param_4 & param_5) != 0xFFFFFFFF` ellenőrzés (az `-1` érvénytelen kulcs) után a `FUN_0058fc40(param_3+0xe0, param_2)` al-táblát kéri (nem dekompilált), a bucket-indexet a `__aullrem(param_4, param_5, [al-tábla+0x1c], 0)` adja (64 bites modulo), a láncban a `puVar2[2] == param_4 && puVar2[3] == param_5` összevetés dönt, és a találat `puVar2+2` (a tárolt kulcs címe), különben 0. A jelölt előállítása a négy hívó egyikében van (`0x0058470f`, `0x00584b8e`, `0x00585c9c`, `0x00586aef`), ezek törzse nincs dekompilálva. **Bizonyítottsági fok:** a keresés logikája **feltételes** (C, egy út); a jelölt előállítása **NINCS MEG**. Megválaszolva részben (13. kör, 34.7): a `0x00584280` nem állít elő kulcsot, hanem fogyasztja. A kulcs-tömb a `0x0084d090` hívásában a `[edi+0x10]` mező. Ghidra-kör kell: 0x0084d090 - az `[edi+0x10]` 64 bites kulcs-tömb írója, és a `0x00584b00`, `0x00585ad0` hívóinak kulcsa [blokkoló]
- Megválaszolva részben (12. kör): a `0x00586794` `call 0x00586a60` (diszasszembly; az index `0x00586540` → `0x00586a60` éle is ezt adja). Argumentumai a C szerint: `puVar3[4]`, `puVar3[5]` (a `this+0x38` táblából a `FUN_0058fc40(this+0x38, param_2)` által adott al-tábla `+0x30` hash-mezővel indexelt láncának csomópontja: a 64 bites kulcs), `param_2` (a kulcs-sztring mutatója, a hívó 2. argumentuma), és `local_34` (kimeneti; a `0x0058677c`-`0x00586790` sorok nullázzák). A `param_3` a második objektum (`*param_3` a sztring, `param_3[9] >> 1` a darabszám). A push-sorok ellenőrzése diszasszembly-munka, nem Ghidra-kör. **Bizonyítottsági fok:** a hívás **megerősített** (asm és index); az argumentumok forrása **feltételes** (C). Ghidra-kör kell: a `0x00586540` hívásának C-je már megvan; a `param_3` objektum forrása a `0x00586540` nyolc hívójában (0x00586175, 0x00586946, 0x00586a05, 0x0058764a, 0x007d5ac7, 0x0084ceff, 0x0084d023, 0x0084edc4) [nem blokkoló]
- Ghidra-kör kell: 0x00506270 - a 42 hívó közül melyik olvassa a `this+0x3f0` táblát, és melyik ad 2-es állapotot a 0 / 4 / 9 kódok mellé [blokkoló]
- Megválaszolva részben (12. kör): a `0x00414940` hívói az index szerint `0x0047b020` (1 hívás) és `0x006a10b0` (2 hívás). A `0x0047b189` a `push 1` (`0x0047b187`) után hívja a `0x00414940`-t (diszasszembly), és ez a `in_EAX[2] == 0` ágon fut (C). A `this` a belépéskor EAX-ben van (C: `in_EAX`); hogy ESI-be hova kerül, a függvény elejét nem ellenőriztem. A `this` típusa NINCS MEG: a `0x0047b020` egyetlen hívója a `0x004987c0` (`0x00498933`). **Bizonyítottsági fok:** a hívó és az argumentum: **megerősített** (asm és index); a `this` típusa: **NINCS MEG**. Megválaszolva részben (13. kör, 34.7): a `0x0047b020` `this`-e a `0x004987c0` `0x00498933` hívásában `EAX = [esi+0x6c] + 4`, ahol az `esi` a worker (`0x004987c0` `this`-e, `mov esi, ecx` a belépésnél). A `[worker+0x6c]` objektum típusa NINCS MEG. Ghidra-kör kell: 0x0047bc80 - a worker `+0x6c` mezőjének létrehozója és típusa (a `0x0047bc80` három `0x004987c0` hívása) [blokkoló]
- Ghidra-kör kell: 0x006a10b0 - a két hívó (`0x006a12fa`, `0x006a1332`): azonos osztály-e a `this`, és hol van a vtábla-írás [blokkoló]
- Ghidra-kör kell: 0x009a51b0 - a visszatérési érték egysége (másodperc vagy tick) [nem blokkoló]


### 34.7 13. kör (2026-10-20): a `0x00584280` és a `0x004987c0` (#5184)

*Forrás:* `.ghidra/2026-10-20-ghidra-13.txt` (C: 365-761. sor a `0x00584280`-ra, 762-965. sor a `0x004987c0`-ra; a munkafában, nem a változtatások között), `annot_disasm.py` (`0x004987c0`, 789 bájt; `0x0047b020`, 379 bájt; `0x0084d090`, 2958 bájt, a hívóhely `0x0084d798`).

- **`0x00584280`: a 64 bites kulcs fogyasztója, nem előállítója (megerősített: C és asm).** A `param_1` 8 bájtos elemek tömbje (`*param_1`, darabszám: `param_1[1] >> 1`); egy elem egy 64 bites kulcs: `[i*8]` az alacsony, `[i*8+4]` a magas dword (C: 417-424. és 617-621. sor). A kulcsot a `FUN_00588210` (helyi kontakt keresése; nincs találat esetén a C: `"Failed to find local contact with id %llx. Giving up."`) és a `FUN_00588290` használja. Az asm szerint a hívó a `0x0084d798` előtt `[edi+0x10]`-et tesz az első argumentumba (`0x0084d785`-`0x0084d78f`). A kulcs előállítása tehát ezen a függvényen kívül van.
- **`0x004987c0`: a `0x0047b020` `this`-ének regiszter-értéke (megerősített: asm, egy út; a típus NINCS MEG).** A függvény munkasor-hurok: a `this+0x16` láncolt sorból vesz ki elemet (`this+0x15` a darabszám), eseményekkel (`this+0x1c`-`0x1e`) és kritikus szakasszal (`this+0x28`). Az elemenkénti `0x0047b020` hívás előtt `EAX = [esi+0x6c] + 4` (`0x00498930`-`0x00498933`), ahol az `esi` a worker (`mov esi, ecx` a `0x004987cc`-ben). A `0x0047b020` `this`-e tehát a worker `+0x6c` objektumának `+4` alobjektuma. A `0x004987c0` vtábla-slotként is elérhető (`0x00c82fa0` DATA-hivatkozás; a vtábla osztálya NINCS MEG).
- **Bizonyítottsági fok.** A `0x00584280` fogyasztói szerepe: **megerősített** (C és asm: két út). A `0x0047b020` `this`-ének regisztere: **megerősített** (asm, egy út; a C nem mutatja az argumentumot). A `[worker+0x6c]` objektum típusa: **NINCS MEG**.
- **Cáfoló kísérlet.** Azt feltételeztem, hogy a `0x00584280` maga állítja elő a kulcsot: cáfolva, a C-ben a két dword csak olvasás (`*param_1 + i*8`), a `0x00588210` és a `0x00588290` csak keres. Azt is feltételeztem, hogy a `0x0047b020` `this`-e maga a worker: cáfolva, az asm `+0x6c+4`-et ad.
- **Lezárás.** Nem zárható le ebben a körben. A kulcs-tömb írója a `0x0084d090` (2958 bájt; a `[edi+0x10]` mező feltöltése). A worker `+0x6c` objektumának létrehozója a `0x0047bc80` (362 bájt, három `0x004987c0` hívással). Ezek a következő célzott Ghidra-kör tárgyai, a 34.6 listáján felül.

### 34.8 15. kör (2026-10-20, #5184): a `0x0047bc80` nem a `+0x6c` objektum létrehozója

- **Mit csinál (megerősített, C, egy út; asm nincs):** rekurzív zár. Ha a `vtbl+4` ellenőrzés nem áll le, `WaitForMultipleObjects`-et hív a `param_1[0x20]+0x640` kettős handle-tömbön, majd `0x0047b4d0`-t (ha nem nulla, azt a kódot adja vissza). Ezután a tulajdonos szálat (`param_1[8]`, azaz `+0x20`) és a rekurziószámlálót (`param_1[9]`, `+0x24`) kezeli. A zárat `EnterCriticalSection(param_1+10)`-zel (`+0x28`) vagy a `vtbl+0x18` hívással veszi, kilépéskor `LeaveCriticalSection`-nel vagy `vtbl+0x1c`-vel engedi el. Sikeres zárnál a `0x004987c0` eredményét adja vissza, egyébként `1000000`.
- **Hívója:** a `0x00c82f78` adatreferencia, tehát vtábla-slot, nem közvetlen `call`. Ennek a vtáblának az osztálya NINCS MEG.
- **Következmény:** a `+0x6c` objektum létrehozójának kérdésére ez a függvény NEM válasz. Zárkezelő, nem konstruktor.
- **Nyitott:** a `+0x6c` mező írói (pásztázás `paszta.py`-val, mint a `+0x37c` esetében) és a `0x00c82f78` vtábla osztálya. A `0x0084d090` kulcs-író (34.1-34.7) továbbra is nyitott, lásd a 34.9-et.

### 34.9 15. kör (2026-10-20, #5184): a `0x0084d090` nem állít elő kulcsot; a véletlen kulcs a `0x005875d0` hívásában van

*Forrás:* utasításszintű olvasat (`annot_disasm.py`) a `0x0084d090` (2958 bájt), a `0x00588050` (444), a `0x005875d0` (1463) és a `0x00584280` (1859) címen; a `.ghidra/2026-10-20-ghidra-15.txt` C-törzse a `0x0084d090`-re (992-1617. sor); a bináris-index `functions`, `xrefs` és `imports` táblája; az IAT-hívások nevei a Ghidra-fejlécből.

- **Mit csinál a `0x0084d090` (megerősített, asm és C).** Két objektumlistát kap (a C szerint `param_2` és `param_3`), és a listaelemek `vtbl+0x78` slotját hívja (`mov edx, [edx+0x78]`, `call edx`, 0x0084d10b-0x0084d117). A kimenet egy adat-pufferre mutat (`[esp+0x3c]`), a darabszám-tag a `[esp+0x40]`. Az elemek 0x20 bájtosak; a 64 bites kulcs a `+0x10` (alacsony) és `+0x14` (magas) dword (`mov ebp, [esi+eax+0x10]`, `mov ebx, [esi+eax+0x14]`, 0x0084d130-0x0084d138). A `(0,0)` kulcsot kihagyja (`mov eax, ebp`, `or eax, ebx`, `je 0x0084d43a`, 0x0084d13c-0x0084d140). A többi kulcsot a `0x00586a60` ellenőrzi (a `(-1,-1)` érvénytelen, lásd 34.1), majd egy hash-halmazba (`this+0x34`-`0x40`) kerül; a vödör indexe `__aullrem(kulcs, [this+0x38])`. A második szakaszban a halmazt a `0x0069ceb0` bejáró függvénnyel végigjárja, a kulcsokat 8 bájtos elemekként tömbbe másolja (C: `node+8`, `node+0xc`), és ezt adja a `0x00584280`-nak (`call 0x00584280` a `0x0084d798`-nál).

- **Honnan jönnek a kulcsok: a bemeneti objektumoktól, nem a függvénytől (megerősített, asm).** A közvetlen hívottak között nincs véletlen-, idő- vagy számlálóforrás: a `call` lista (asm) egyezik a Ghidra-listával. A hívottak: `0x00586a60`, `0x0084f160`, `0x0058f910`, `0x0069ceb0`, `0x00584280`, memóriakezelők, és két IAT-hívás (`call dword ptr [0x00c40558]` / `[0x00c40560]`, a Ghidra-fejléc szerint `InterlockedDecrement` / `InterlockedIncrement`, hivatkozásszámlálás). Három vtábla-hívás van (`vtbl+0x68`, `+0x78`, `+0x10`); ezek céljait nem vizsgáltam, ezért a "nincs véletlen" állítás csak a közvetlen hívásokra áll.

- **Hol van a véletlen kulcs (megerősített, asm, egy út).** A `0x00588050`: `CryptAcquireContextA` (a `0xd67924`-be gyorsítótárazott `hProv`, `PROV_RSA_FULL`, `CRYPT_VERIFYCONTEXT`), majd `CryptGenRandom(hProv, 8, buf)` (0x00588089-0x005880a0). A 8 bájt adja a 64 bites kulcsot; érvényes, ha nem nulla és nem `(-1,-1)` (0x005880b3-0x005880c8). A `0x005875d0` hívja (0x005876c0), a 0x0058764f-0x00587675 ágon, ha a kimeneti kulcs nulla vagy `(-1,-1)` (feltételes: a belépő ág feltételét részben követtem). A `0x00584280` hívja a `0x005875d0`-t (0x005848b1), a tömbelem `[esi]`, `[esi+4]` kulcsával és 7-es, illetve 0-s jelzőkkel.

- **Hash, számláló, időbélyeg: nem az előállítás.** A `0x0084d090` vödör-indexe és a láncolás tárolás, nem kulcs-generálás. Időforrás (`GetTickCount`, `QueryPerformanceCounter`, `timeGetTime`, `GetSystemTime*`) a közvetlen hívottak között nincs.

- **Hatás a jelenlegi kulcs-tömbre (feltételes).** A `(0,0)` kulcs nincs a tömbben. A `(-1,-1)` viszont bekerülhet: a `0x00586a60` nem nulla visszatérése esetén a C `else` ága (1190-1224. sor) string nélkül is beteszi a halmazba. Hogy ez eléri-e a `0x00584280` véletlen-ágát (`0x005848b1`), a `0x00584280` feltételének elolvasásától függ: NINCS MEG.

- **Bizonyítottsági fok.** A bemeneti forrás (`vtbl+0x78`, a `+0x10`/`+0x14` kulcsmezők), a `(0,0)` kihagyás és a hash-tárolás: **megerősített** (asm és C, két út). A véletlen kulcs a `0x00588050`-ban: **megerősített** (asm, egy út). A véletlen ág elérése a `0x0084d090` tömbjéből: **feltételes**. A `vtbl+0x78` osztálya és a két lista forrása: **NINCS MEG**.

- **Cáfoló kísérlet.** (1) Azt állítottam, hogy a `0x0084d090` számlálóval állítja elő a kulcsot. Cáfolva: a számláló csak a tömb indexe, a kulcs a `vtbl+0x78` kimenetéből jön. (2) Azt állítottam, hogy a véletlen kulcs a `0x0084d090`-ból ered. Cáfolva a közvetlen hívás-listán (nincs RNG-hívás); a `0x00584280`-on át még nem zártam le, ezért feltételes. (3) Azt állítottam, hogy a `(0,0)` kulcs bekerül a halmazba. Cáfolva (`je 0x0084d43a`).

- **Következő cím (c).** `0x0084dc30`: a `0x0084d090` egyetlen hívója (0x0084dcfc), amely a két objektumlistát adja; ebből derül ki a `vtbl+0x78` osztálya és a 0x20-as rekordok kulcsának eredete. Másodsorban a `0x00584280` 13. dumpbeli C-je (365-761. sor), a `0x005848b1`-et megelőző feltétel miatt.

### 34.10 16. kör (2026-10-20, #5184): a `0x005848b1` előtti feltétel; a `0x0084dc30` listaforrása részben

*Forrás:* `annot_disasm.py` a `0x00584280` (1859 bájt) címen, a `0x005848b1` körüli sorok; `.ghidra/2026-10-20-ghidra-13.txt` (C: 306-345. sor a `0x00584280` relatív számozásával); `.ghidra/2026-10-20-ghidra-17.txt` (C és HÍVÓK-fejléc: `0x0084dc30`).

- **A `0x005848b1` (`call 0x5875d0`) elé eső feltétel (megerősített, asm, egy út).** A `0x00584280` ciklusában a `[esp+0x34]`-en át elérhető lista `[edx+eax]` eleme (`ecx`) csak akkor vezet a véletlen-ágra, ha: a mutató nem nulla (`0x0058488b`), a fejléc `[eax] & 0xffffff00` nem nulla (`0x0058488f`), és `[eax+4]` első bájt nem nulla (`0x00584897`). Bármelyik hiánya a `0x005848bb`-re ugrik, a véletlen ág kihagyásával. Tehát a véletlen kulcs-ág csak **nem üres nevű** elemre fut. A C-ben a `FUN_005875d0` hívás (345. sor) a `iVar16 == 0` ágon belül van; az elem-feltétel asm-ből igazolt.
- **A `(-1,-1)` elérés (feltételes).** A 34.9 szerint a `(-1,-1)` kulcs string nélkül is bekerülhet a halmazba. Ha ugyanabba a listába kerül, amelyet a fenti ciklus bejár, az üres név miatt kihagyódik, és nem éri el a véletlen ágat. A listaazonosság NINCS MEG.
- **A `0x0084dc30` két listája: részben (megerősített, HÍVÓK-fejléc).** A függvénynek egyetlen közvetlen hívója van: `0x006df399`, a `0x006df1f0`-ban. A két lista (`param_3`, `param_4`) forrása ez a hívó; a hívó törzse nincs olvasva: **NINCS MEG** (17. kör: megválaszolva, lásd 34.11; a `param_4` nem lista, hanem a `this`).
- **A `vtbl+0x78` célja: megválaszolva (17. kör, 34.11): `0x007954e0`, `CPreparedDBImage::vftable`.** A hívás `(**(code **)(**(int **)(iVar4 + *param_3)) + 0x78)()` (C: 185. sor); a célt a listaelem osztályának vtáblája adja, és az osztály nincs azonosítva.
- **Bizonyítottsági fok.** A `0x005848b1` előtti elem-feltétel: **megerősített** (asm, egy út). A `(-1,-1)` elérés: **feltételes**. A listaforrás és a `vtbl+0x78` célja: **NINCS MEG**.
- **Cáfoló kísérlet.** Azt feltételeztem, hogy a `0x00584280` a `(-1,-1)` bejegyzésre is elágazik a véletlen kulcs felé: cáfolva az üres név kihagyásával, ha ugyanabban a listában van. A listaazonosság nem cáfolt.
- **Következő cím (c).** `0x006df1f0`: megválaszolva a 17. körben (34.11). A `(-1,-1)` elérés futásidejű adat, ezért Colab-felvétel javasolt a (c) helyett.

### 34.11 17. kör (2026-10-20, #5184): a `0x006df1f0` listái, a `vtbl+0x78` célja és a `(-1,-1)` elérés

*Forrás:* `annot_disasm.py` a `0x006df1f0` (605 bájt), a `0x006dfdd0` (467), a `0x00599450` (340), a `0x00432100` (365), a `0x006df4a0` és a `0x006dfb20` hívóhelyei körül; a `0x0084dc30` C-je a `.ghidra/2026-10-20-ghidra-17.txt` 37-383. során; a `0x007954e0` (67 bájt) és a `0x00599020` (7 bájt) a PE-fájl bájtjaiból, diszasszemblálással ellenőrizve; a bináris-index `rtti` táblájának `CPreparedDBImage::vftable` sora.

- **A `0x0084dc30` argumentumai (megerősített, asm).** A `0x006df399`-es hívás stdcall, négy argumentummal: a kimeneti struktúra (`[esp+0x44]`), a `0x006df1f0` második argumentuma (`esi`), az `aiStack_78` két dword-ös lista (`[esp+0x24]`), és a `this` (`ebp`). A 34.10 „`param_3`, `param_4` listák” állítása pontatlan: a `param_4` nem lista, hanem a `this`, amelyen a `vtbl+4` lemondás-ellenőrzés fut (nem nulla eredménynél a `0xf4242` kódot adja vissza). A `param_3` egy `[mutató, darabszám|jelző]` pár (C: `param_3[1] & 0xfffffffe`).
- **A két lista forrása.** (1) A `param_3` (`aiStack_78`) nem a hívótól jön, hanem a `0x006dfdd0` építi. A bemenő lista minden eleméhez új, 0x138 bájtos objektumot foglal (`0x0097c5d0`) és konstruál (`0x00599450`) a ciklus minden körében (`0x006dfe24`-`0x006dfe3e`). A kulcsot a `0x00432100` kimenetéből írja a `+0x10`/`+0x14` mezőbe, ha a hívás eredménye 0 (`0x006dfec9`-`0x006dfedc`), az objektum mutatóját pedig a kimeneti tömb végéhez fűzi (`0x006dff57`). (2) A bemenő lista (a `0x006df1f0` harmadik argumentuma) és a `param_2` a két hívóból jön: a `0x006dfb20` (`0x006dfd76`) saját lokálisait adja, a bemenő listának az `[esp+0x18]`-at (a `0x006dfcc8`-ban `ebx`-et ír bele), a `param_2`-nek az `[esp+0xf8]`-at. A `0x006df4a0` (`0x006df862`) saját verem-argumentumait (`[esp+0x170]`, `[esp+0x16c]`) továbbítja. Az `[esp+0x18]` feltöltése (`0x006dfbe1`, `0x006dfc7a`) és a `0x006df4a0` saját hívója nincs végigolvasva.
- **A `vtbl+0x78` célja (megerősített: RTTI, PE-bájtok, asm).** Az `aiStack_78` elemei `CPreparedDBImage` objektumok: a konstruktor egyetlen vtábla-írása `mov dword ptr [eax], 0xc93044` (`0x00599454`), az RTTI szerint a `0x00c93044` a `CPreparedDBImage::vftable`. A 30. slot (`+0x78`) a PE-fájlból olvasva `0x007954e0` (`FUN_007954e0`, 67 bájt). Ez nem kulcsot állít elő: nem nulla kimeneti mutatónál meghívja a `0x006f9080`-t a `this+0x100` alobjektummal, majd az öt dword-öt (`this+0x108`-`+0x118`) a kimeneti rekord `+0x8`-`+0x18` mezőibe másolja, és 0-t ad vissza; nulla mutatónál `-1`-et (`0x007954e9`). A `vtbl+0x10` (a kulcs-olvasó) a `0x00599020`: `(this+0x10, this+0x14)`.
- **A `(-1,-1)` elérése (NINCS MEG a binárisból).** A kulcs a `[this+0x10]`-be csak akkor kerül, ha a `0x00432100` 0-val tér vissza (`0x006dfec9`-`0x006dfedc`). A `0x00432100` egy 8 bájtos azonosító-listát járja be (a listát a `[[ecx+0x48]+0xb4]` függvénymutató hívása adja), minden elemet `%I64u` alakú szöveggé formáz (`0x0040eab0`), és a `0x0040ecd0`-val keres. A `-1` eredménynél a `bl` jelzőt 0-ra állítja (nincs találat); egyébként a 0x130 bájtos rekord címét számolja (`0x0043218e`-`0x00432196`), a `0x005a4f10`-nek adja át, és `bl = 1`. Hogy a `(-1,-1)` bekerül-e a listába, az a tárolt kontaktadatok (futásidejű adat) függvénye. Az INI `ffffffffffffffff` értéke (job-210) a mellőzött arcok azonosítója; a 34.10 szerint a véletlen-ág csak nem üres nevű elemre fut.
- **Bizonyítottsági fok.** A hívási argumentumok: **megerősített** (asm és C, két út). A `param_3` építése a `0x006dfdd0`-ban: **megerősített** (asm, a C egyezik). A `vtbl+0x78` és a `vtbl+0x10` célja: **megerősített** (RTTI, PE-bájtok és diszasszembly: három út). A bemenő lista és a `param_2` eredete a két hívóban: **feltételes** (egy szintig olvasva). A `(-1,-1)` elérése: **NINCS MEG** (futásidejű, tárolt adat).
- **Cáfoló kísérlet.** (1) Azt feltételeztem, hogy a `param_4` lista: cáfolva (`vtbl+4` lemondás-ellenőrzés, a `0xf4242` visszatérési kód). (2) Azt feltételeztem, hogy a `vtbl+0x78` kulcsot állít elő: cáfolva (a `this+0x100`-ból másol, a kulcs a `+0x10`-ből jön). (3) Azt feltételeztem, hogy az `aiStack_78` a hívó listája: cáfolva, a `0x006dfdd0` elemenként új objektumot hoz létre.
- **A `(-1,-1)` a felvételből: a mellőzött arc kulcsa (megerősített, felvétel).** A picasa-colab-jobs job-210 (az arc mellőzése a csempe X gombjával, majd Ignore Person) után a `.picasa.ini`: `[portre_1_ff.jpg]` `faces=rect64(27c00680d8ffdb3f),ffffffffffffffff`, `[Contacts2]` szakasz nélkül. A mellőzött arc tehát a 64 bites `-1` kulcsot kapja, névjegy nélkül; ez a binárisban a `(-1,-1)` kulcs.
- **Lezárás.** A `(-1,-1)` kérdést a job-210 eldöntötte (fent); Colab-felvétel ehhez nem kell. A J4 felvétel (#5185, 35.5) bővítendő: a mellőzés előtti és utáni `.picasa.ini` `[Contacts2]` és `faces=` sora kell két arccal (egy névtelen és egy nevezett, mellőzött arc). Ebből látszik, van-e név a mellőzött elemhez, és így fut-e a véletlen-ág (`0x005848b1`). A binárisban maradó nyitott rész: a `0x00432100` kimenő kulcsának forrása (a 0x130 bájtos rekord melyik mezője). Ez másodlagos, nem blokkoló.

## 35. #5185, negyedik kutatói kör és 2026-10-21-i korrekció: nyolcpontos leltár

**Hatókör és forráskorlát.** Az „Eredeti” a #5185-ben megadott job-162/163/167/175/177/179/180/183/207/208/209/210/213 felvételi jegyzeteket, a helyi Picasa 3.9 binárist és a `.fen`/`.tre` erőforrásokat idézi. A bináris verzióadata `FileVersion=3.9.141.259`, `ProductVersion=3.9.141` (bináris, a PE `VERSIONINFO` erőforrása). A hivatkozott job-162/163/167/175/177/179/180/183/207/208/209/210/213 képkockafájlok többsége ebben a munkamenetben nem volt elérhető, ezért a hozzájuk tartozó jegyzeteket nem tudtam képről újraellenőrizni. Közvetlenül megnyitott kivétel a `Colab EN 36 - Ignore People megerosites.png`: a leltár 112. sora Colab #63-ként azonosítja; ez az X-megerősítést és a mögöttes rácsot bizonyítja, nem a job-64 ini-kimenetét vagy a job-209/210 utáni állapotot. A `Colab EN 23 - People Manager.png` képet is közvetlenül megnyitottam: a privát leltár 76. sora szerint az eredeti angol 3.9.141, Wine, 1280×1024, Colab #22 képkockája; a People ablak üres listájú elrendezését és a látható vezérlőket mutatja, de nem a kijelölési modellt vagy az OK/Mégse utáni adatállapotot. A mérőadat-archívum korábbi leltározása nem talált #5185-höz tartozó konkrét profilt vagy felvételt. A 2026-10-22-i névjegyzék-ellenőrzésben az archívum 944 tagból állt; `5185`, a megadott job-azonosítók, `contacts.xml`, `.db3`, illetve `colab`/`face`/`unnamed`/`people` nevű képkocka fájlnév szerinti találata 0 volt. Ez csak a tagok neve szerinti ellenőrzés: tartalmat nem bontottam ki, és semmit nem tettem a `.bt` alá. Az archívumleltár hiánya hozzáférési korlát, nem viselkedési negatív lelet. A 35.6 szakasz „Nálunk” oszlopa a 2026-10-21-i, 0.9.179-es forrás-pillanatkép; a jelenlegi munkafa 0.9.185-ös állapotát a 35.7 szakasz ellenőrzi. A PicasaPy-t ebben a körben nem futtattam, tehát élő UI-egyezést vagy külső böngészőeredményt nem állítok.

| Pont | Eredeti | Nálunk (0.9.179-es forrás-pillanatkép) | Teendő |
|---|---|---|---|
| **1. Név nélküliek sor, nézet, fejléc, csoport, bélyegek, kijelölés és tálca** | A bal sáv `Unnamed (6)` sorára a jobb oldal „Unnamed people”, „6 Face(s)” és útmutatósort mutat; a gombok „Expand groups” és „Show ignored faces” (job-162/163; job-207, 8. kép). Csoportosítva öt oszlop és csempénként `Add a name`/X látszik; kibontva egy sor, kisebb arcok, fejléc `Add a name`/`Ignore Selected`; visszaváltáskor a csempevezérlők visszajönnek (job-208, 9., 11., 13. kép). Kezdetben `No Selection` és üres tálca (job-162 jegyzet). A közvetlenül megnyitott Colab #63, 1280×1024 képkockáján a névmezők 172×20 px-esek; a hat megjelenített arcképkeret 144×172, 144×172, 144×172, 121×172, 126×172 és 144×172 px (pontos koordináták: 19.1, 5. pont). Ez a képkocka 5+1 rácselrendezést mutat; az arckivágások más felbontáson mért mérete, a tartós rendezési kulcs, a többarcú csoporthatár és a Ctrl/Shift/húzás tálcahatása **NINCS MEG**. | A forrásolvasat szerint `UnnamedFacesView.qml` `grouped: true`-val és üres arc-kijelöléssel indul; a `toggleFace` egyesével kapcsol arcot a `selectedFaceIds`/`selectedCount` állapotban, Ctrl/Shift módot a csempekattintás nem ad át. A rács/csempe méret és a vezérlők a QML-ben rögzítettek. A 0.9.159 óta a `Main.qml` külön `personAlbumLayout` feltételt használ, így a Név nélküliek nézete nem örökli az előző személyalbum nulla margóját (#5364, `Main.qml`). Tálcával való futásidejű kapcsolatot nem mértem. | J2: alap kattintás, Ctrl, Shift és húzás; mindegyik után képernyőkép, kijelölésszám és tálcaállapot. A mért Colab #63 képkocka 1280×1024-es, a névmezők és a hat látható képkeret méretét rögzíti (19.1). A tartós rendezési kulcshoz, a többarcú csoporthatárhoz és a kijelölési szabályhoz új felvétel kell. **Mért rész:** job-162/163/207/208, és a #63 képkocka. **NINCS MEG:** tartós sorrend, csoporthatár és kijelölési szabály. |
| **2. Arc kijelölése és megnevezése; névmező, javaslatlista, Enter/OK és kimenet** | `Tes` begépelésekor arcképes „Teszt Elek” névjegy-kiegészítés jelenik meg (job-167, 22. kép). Teljes név+Enter új személynél a People ablak üres listával és `New Person` gombbal nyílik; meglévő személynél kijelöl és `Choose` gombot mutat (job-163, 14-19. kép; job-167, 26-30. kép). `Choose` után az arc a személyhez kerül és a két sorszám változik (job-179). Job-167 Escape-je az ismeretlen `Valami` keresés után a **People ablak Search mezőjében** történt; változtatás nélkül bezárta azt (32-34. kép). A csempe-Escape szülői hatása és a javaslatra kattintás utáni név-/párbeszéd-/arcállapot **NINCS MEG**; a 19.7 csak a `CAutoCompleteListBox` nem nulla `param_2` ágának elfogadó rutinját azonosítja (`0x00809360` → `0x00a54b70`), a csempe-popup bekötése nyitott. Ctrl/Shift/húzás **NINCS MEG**. | A munkafa 0.9.179-ös forrásában a Név nélküliek nézet megnyitásakor betöltődik a névjegy-cache (`UnnamedFacesView.qml:82-85, 144-159`; `PeopleMixin.nameSuggestions`, `people_controller.py:200-231`), gépeléskor pedig a részszövegre illő névjegyekből képet és nevet mutató lista szűrődik (`UnnamedFacesView.qml:560-588, 664-698`). Enter és a javaslatsorra kattintás ugyanazt a `submitName` → `nameSubmitted` utat használja (`UnnamedFacesView.qml:448-462, 580-588, 691-698`); a `Main.qml:3867-3869` a `nameFaceFromPanel(..., true)` hívására köti, amely meglévő névnél is People ablakot nyit (`PeoplePanel.qml:192-208`). A „Choose” gomb meglévő személynél a forrásban kijelölt kontaktot jelzi. **Forrásolvasat, nem futásidejű PicasaPy-mérés.** | J2 kiegészítése: külön csempe-Escape, javaslatelem-kattintás és Enter; People ablakban `OK`, `Choose`, `Cancel` után képernyőkép és állapot. **Mért:** job-163/167/179. **Nyitott:** az eredeti Picasa javaslatelem-kattintása és csempe-Escape. A job-167 Escape-t ne idézzük csempe-mező bizonyítékaként; a PicasaPy 0.9.179-ös forrásútja önmagában nem bizonyít eredeti-egyezést. |
| **3. Arcfelismerési javaslat, elfogadás és elutasítás** | A súgó szerint névadás után hasonló arcok javasolhatók, a személy-albumban fogadhatók el vagy utasíthatók el (job-207, 8. kép). A job-213 mintában nem jelent meg arcfelismerési javaslat, mert mindkét hasonló arcú fotó meg volt nevezve. A job-167 `Tes` listája névjegy-kiegészítés, nem arcfelismerési javaslat; a `PeoplePanel::AutoCompleteProvider` lekérdezése a `0x00643940`, nem üres szövegnél a `0x007b4990`-en keres, a jelöltek forrása a `0x00491980` (38.9), összhangban a job-167, 22. kép megfigyelésével. A személy-album javaslatparancsai ettől külön: addname: → `0x00646d70`, suggestion_yes: → `0x00646ec0`, suggestion_no: → `0x00647020`, a `0x0063f970` elosztón át (26.3). A tényleges javaslatfelület, az elfogadás/elutasítás kattintási eredménye és tartós kimenete **NINCS MEG**. | A PicasaPy a javasolt arcnevet a csempén és a People album sorában mutatja. Elfogadás az assignNameToFaces útján nevet rendel; elutasítás a PicasaPy SQLite-index javaslatmezőjét üríti (face_scan_controller.py, acceptSuggestion/rejectSuggestion). Forrásolvasat, nem futásidejű összevetés. | J3: egy névvel ellátott személy és hasonló névtelen arc; a javaslat megjelenése, elfogadása és elutasítása külön profilban; .picasa.ini, contacts.xml és db3 előtte/utána/újraindítás után. **Nyitott:** eredeti javaslatcsempe, kattintási eredmény, tartós fájlhatás. |
| **4. Mellőzés és visszahozás** | A csempe X-jére megjelenő megerősítő ablak címe **„Ignore People”**; szövege: „Are you sure you want to move this person to the ignored people album?”; jelölőnégyzete „Don't ask again, always ignore”; gombjai **Ignore Person** (alapértelmezett) és **Cancel** (job-209, 10. kép). Jóváhagyás után a mellőzött csempe eltűnik, „Unnamed (5)” és „5 Face(s)” marad, a „Show ignored faces” aktívvá válik (job-210, 13. kép). A mellőzött nézetben a cím „Ignored people”, a bal oldali sor „Ignored (1)”, a fejléc „1 Face(s)” és „Back to Unnamed”; az útmutató „Select someone you know and add a name.”, a csempén nincs X, de van „Add a name” mező (job-210, 16. kép). Az ini-kimenet `faces=rect64(27c00680d8ffdb3f),ffffffffffffffff`, `[Contacts2]` bejegyzés nélkül (job-210). A megerősítés szövegét a bináris `0x00c99830` is tartalmazza; az X-képkocka külön forrása a `Colab EN 36` PNG (Colab #63, leltár 112. sor; 28.4/a, 19. szakasz). A job-222 személyalbum-menüjében és job-226 People párbeszédében személyszintű Ignore nem szerepel. A fejléc Ignore Selected kimenete és Back to Unnamed utáni állapot **NINCS MEG**. | A jelenlegi 0.9.179-ös forrásban a bal oldali sor `Ignored (N)` (`FolderPane.qml:749`), a mellőzött nézet pedig megjeleníti az `N Face(s)` sort (`UnnamedFacesView.qml:281-305`); a feliratok egyeznek a job-210 jegyzeteivel. A csempe-X és az Ignore Selected útját is kezeli a forrás. Ez forrásolvasat, nem élő PicasaPy-mérés. A 19. szakaszban leírt `Ignored people (N)`/hiányzó darabszám az akkori 0.9.118-as kódállapot volt. | J4: mérjük az Ignore Selected gombot kijelölt arccal, majd a mellőzött nézetből Back to Unnamed után a csempét és az ini/db3 diffet. Személyszintű Ignore a két dokumentált eredeti belépési pontban nem található; ott megvalósítandó eltérés nincs. |
| **5. Személy-album: arc/teljes kép, átnevezés, egyesítés, törlés** | A job-213 29. képkockájáról adott felvételi jegyzet szerint a bal sávban a „Teszt Elek (2)” személyalbum kijelölt, az „Unnamed (4)” sor is látszik. A fejlécben az arc és teljes kép váltóikonok mellett a **Remove** gomb szürke; alatta két arc-csempe, majd a „PicasaTeszt” mappa összes képe jelenik meg. Az állapotsor „2 pictures”, a tálca „Album Selected - 2 photos” (job-213, 29. kép; a nyers képkockát ebben a körben nem tudtam újraellenőrizni). A job-222/223/224 jegyzet szerint a Delete People Album megerősítő ablak alapértelmezett gombja Cancel; Delete Album után az érintett képek `faces=` sora eltűnik, a `[Contacts2]` bejegyzés megmarad, és db3-adatok változnak (37.10). A zoomgombok kattintási hatása, az átnevezés és a teljes album-összevonás eredménye **NINCS MEG**. | A LightboxHeader forrása arcra közelített/teljes kép módot vált; a forrásolvasat szerint az alapállapot teljes kép. A 0.9.166-os törlési út a PicasaPy-ban arcokat töröl, a névjegyet megtartja (people_controller.py, FolderPane.qml; #5393); élő UI-összevetés nem történt. | J5: mérjük az első megjelenített módot, mindkét zoomgombot, átnevezést és két személy teljes albumának összevonását. A törlés fájlhatása már dokumentált (37.10); csak a korábban nem mért felületi és összevonási viselkedést kell felvenni. |
| **6. People Manager: elrendezés, kijelölés, mezők, OK/Mégse** | A job-163 új név esetén kétoszlopos People ablakot mutat: a Search előre kitöltött és kijelölt, a lista üres, a Delete Person és az OK tiltott, a New Person aktív; jobbra Name és Email(s), szürke Sync Face Tags with Web Albums és Revert; alul Manage Online Contacts, Refresh Contacts és Cancel látható (job-163, 14-19. kép). Meglévő személy kiválasztásakor a keresőben a név látszik, a lista kijelöli a kontaktot, a jobb oldalon „1 Photo in Picasa”, a jóváhagyó gomb **Choose** (job-167, 26-30. kép). A meglévő személyre vonatkozó ablak további elemeit a job-226 jegyzet írja le: Search/lista, Delete Person/New Person, Name/Email(s), szinkronjelölő, Revert, Manage Online Contacts, Refresh Contacts, OK/Cancel (37.11). A kijelölési modell **NINCS MEG**. A bináris `cancel` ág a `0x007b99a0` dispatcherben a `0x007b9a57` parancs-összevetés után közvetlenül a `0x008d2720` bezárást hívja (`0x007b9a90`); ebben az ágban nincs validálás vagy mentés (`0x007bb660`, `0x007baf50`), 38.8. Módosított mezőkkel végzett Cancel utáni profilállapotot nem mértünk. | A PeopleManagerDialog forrása currentIndex-szel választ kontaktot; OK commitChanges, Cancel párbeszédzárás. Forrásolvasat, nem eredeti futásmérés. | J6: jelöljünk ki személyt, módosítsunk mezőt, majd külön profilban OK, Cancel és Escape; előtte/utána contacts.xml, ini és db3. A párbeszéd elrendezése, új/meglévő név nyitási állapota és a bináris Cancel-dispatch felvéve; a többes kijelölés és a módosított érték tényleges Cancel utáni profilállapota nyitott. |
| **7. contacts.xml, [Contacts2], faces=, db3 olvasása/írása** | Job-213 jegyzete: [Contacts2] ID=Teszt Elek;; és faces=rect64(...),ID; a mért azonosító `3c067b829137b19`, 15 kisbetűs hexajegy, vezető nulla nélkül. Job-210: mellőzött arc jelölőértéke `ffffffffffffffff`. A job-224 jegyzet szerint albumtörlés után a faces= sorok eltűnnek, [Contacts2] megmarad, és db3-adatok változnak (37.10). A bináris `%I64x` formátumsztring `0x00c82fcc`-nél nincs szélességkitöltéssel ellátva. A `0x00587110` a `[Contacts2]` sort három mezőből állítja vissza és `Restoring contact ... from .ini file` üzenetet hív; a `0x00586e20` `Contacts2`-bejegyzést épít, `Persisting contact to INI` üzenettel (`0x00587110`, `0x00586e20`, 32.1-32.4). A `contacts.xml` olvasó útja `0x00581920` → `0x00991650` → `0x00991490`; az utolsó `GENERIC_READ`/`OPEN_EXISTING` paraméterekkel nyit (35.10). A `0x00580110` `wt` módban `contacts.xml`-t ír; a `0x00586bd0` piszkos ágából, a `0x0041ba40` `#contacts\` útján hívódik. A `0x0066f2b0` külön Backup-paneles `contacts.xml` → `backup.xml` másolás. A People Manager műveletenkénti kiváltó/időzítés **NINCS MEG**. | A PicasaPy központi `contacts/contacts.xml`-t és az ini API-t használ; saját SQLite-indexet ír, Picasa db3-at nem. A jelenlegi 0.9.179-ös forrásban a `generate_contact_id()` nem nulla 64 bites értéket `format(value, "x")` alakban ír ki (`src/picasapy/ini/contacts.py:32-38`), kitöltő nulla nélkül; ez formátum szerint egyezik a binárissal és a job-213 mintájával. Forrásolvasat, nincs futásidejű diff. | J8: névadás, elfogadás/elutasítás, átnevezés és törlés előtt/után, bezáráskor és újraindítás után mentsük a profil contacts.xml, ini és db3 állapotát. **Dokumentált:** ini-alak és törlési kimenet; a frissen generált azonosítók formázása egyezik. **NINCS MEG:** melyik People Manager művelet mikor írja a `contacts.xml`-t, és mi a teljes műveleti fájl-diff (J8, 35.10). |
| **8. Arcfelismerés: mikor indul, mit hagy ki, küszöb** | A BgFaceDetectThread alapértéke 1 (0x0069fc00); az FRAddSuggesetions kapcsoló olvasása 0x00414940. A FRSuggestionThreshold/FRSortThreshold beállítás alapértéke 85, a felületi lépcsők 50-95 között ötpontos lépésben (1.1-1.2). A `FRRecommendIncludeLimit` 0,50-es gyári értéke a `0x0048e1f0`-ban külön ajánlásba-vételi szűrő, nem a Red.dll belső detektálási küszöbe (35.10). A Red.dll `0x10001570` hívó csak státuszkódot ellenőriz, a `0x100057c0` pontszámot külön kimeneti tömbbe írja (35.11). Az első scan pontos indítása és a névvel ellátott képen talált másik arc kimenete **NINCS MEG**. | A FaceScanController forrása leírt automatikus keresési és kihagyási feltételeket; ez forrásolvasat, nem eredeti viselkedésmérés. | J7: első import, új mappa/új kép, kizárt mappa és névvel ellátott arcot tartalmazó kép; rögzítsük a keresés idejét és pontos adatváltozását. A Red.dll belső küszöböt becslés nélkül, bináris címmel vagy pontos méréssel kell megállapítani; a 0,50 külön ajánlási szűrő. |

### 35.1 Bizonyítottsági fok, két út és cáfoló kör

A teljes #5185 állapota **nyitott**: mind a nyolc pont Eredeti/Nálunk/Teendő formában szerepel, de a táblában megnevezett részviselkedésekhez új eredeti felvétel vagy adatváltozás-összevetés kell. A „Nálunk” állítások forrásolvasatok, nem futásidejű mérések.

- **A út - eredeti felvételi jegyzetek és közvetlen képkocka:** job-162/163/167/175/177/179/180/183/207/208/209/210/213 a látható felületet és a job-210/213 INI-kimenetet írja le. A `Colab EN 36` PNG-t közvetlenül megnyitottuk; a rajta látható hat arcképkeret pixeleit közvetlenül megszámoltuk, a névmezőkkel együtt (19.1). Ez egy képkockára érvényes, feltételes mérés, nem bizonyít skálázást vagy tartós sorrendet. A `Colab EN 23 - People Manager.png` szintén közvetlenül ellenőrzött kép (Colab #22, leltár 76. sor): az üres listájú People ablak látható vezérlőit igazolja, kijelölési vagy mentési viselkedést nem. A többi, későbbi job-162-213 felvétel képfájljai itt nem érhetők el. A job-175/177 a „Learn more...” gomb után a Picasán belüli látható változás hiányát méri; böngésző nélkül nem cáfolja, hogy külső megnyitási kísérlet történt.
- **B út - bináris és erőforrás:** `annot_disasm.py` olvasata adja a zoom defaultot (`0x005e5290`, `0x00767e50`); a `runtime/contactmgr.fen:1-80` a People ablak vezérlőit írja le; bináris sztring-xref a mellőzési megerősítés szövegét (`0x00c99830`). A People Manager képkocka és a `.fen` a Search/lista, két hasáb és alsó gombsor látható elrendezésén egyezik; a `.fen` opcionális azonosító-csoportjainak láthatósága nem következik ebből a képből. Az X-megerősítés közvetlen képe (`Colab EN 36`, Colab #63, leltár 112. sor) egyezik a bináris sztringgel (`0x00c99830`); a job-64 ini-kimenete külön felvétel. A job-213 ID-alakja és a `%I64x` (`0x00c82fcc`) is egyezik. A 35.10 célzott utánkövetése azonosítja a contacts.xml olvasó- és íróútját, és elkülöníti a Backup-paneles másolatot; a People Managerhez kötött írási eseményt még nem oldja fel. Ezek csak a közös metszetükre adnak két utat.
- **A 2. pont kétutas részeredménye (19.5, 19.7, 35.13):** a job-163/167/179 jegyzetek és a `0x00787dd0`/`0x007b81e0` utasításolvasata egyezik a csempemező feliratánál és a meglévő személy `Choose` ágánál. A `CAutoCompleteListBox` `0x00809360` függvényében a `param_2 != 0` ágak elfogadó rutint hívnak (`0x00a54b70`); ezt a nyers diszasszemblálás, Ghidra-C és RTTI slot-azonosítás egymástól függetlenül alátámasztja. A `param_2` egér-eseményhez tartozó jelentése és a csempe-popup bekötése nincs meg, ezért a csempe-kattintás végeredménye továbbra is nyitott. A csempe Escape-re nem fogyasztja az eseményt (`0xf4241`); a szülő reakciója nyitott.
- **Javaslatkezelő-hozzárendelés, két független út:** A út: a 0x0063f970 utasításai a suggestion_yes: prefixet a 0x00646ec0-hoz, a suggestion_no: prefixet a 0x00647020-hoz küldik; az addname: a 0x00646d70-hoz fut. B út: az index xrefs/string_xrefs ugyanezeket az éleket és prefixeket mutatja, a 0x00648f20 pedig a peoplepanel/suggestion_yes:%d és peoplepanel/suggestion_no:%d vezérlőneveket építi. A két út egyezik.
- **Cáfoló és cáfoló-ellenőrzés:** a korábbi hipotézis szerint 0x00646d70 volt a suggestion_yes kezelő. Ezt cáfolja a diszasszemblyben látható addname: ág és a suggestion_yes: ág külön hívása. A cáfolatot az indexből és a 0x00648f20 vezérlőneveiből függetlenül ellenőriztem; azok is a 0x00646ec0 hozzárendelést adják. Nincs ellentmondó második út. A téves, 0x00646d70 testéből levezetett elfogadási állításokat a 26.3 szakasz visszavonja.
- **Cáfoló: PicasaPy Learn more-kezelő.** A korábbi spec-állítást („a PicasaPy-ban nincs kezelője”) a helyi forrás ellenőrzése cáfolta: ebben a munkafában a `UnnamedFacesView.qml:133-137` felépíti a címet, a `:866` a `Qt.openUrlExternally`-t hívja. A job-175/177 az eredeti Picasát mérte, így abból a PicasaPy kezelőjére következtetni hibás volt. A forrás megléte nem bizonyítja, hogy futáskor a külső böngésző megnyílik vagy betölti az oldalt.
- **Cáfoló: Escape.** A korábbi spec-mondat a csempe-Escape-et tulajdonította a job-167-nek. A lépéssor ellenőrzése szerint Escape az ismeretlen `Valami` keresés után, a People ablak Search mezőjében történt. A csempemező nem volt fókuszban; az állítás cáfolva, helyesbítve a 19.1-ben.
- **Cáfoló: a People ablak Cancel-je az OK-val ment-e.** A hipotézis az volt, hogy a Cancel az OK ágon keresztül is menthet. A `0x007b99a0` diszasszemblálásában a `cancel` összevetés (`0x007b9a57`) közvetlenül a bezárást hívja (`0x007b9a90` → `0x008d2720`); a validáló `0x007bb660` és a mentő `0x007baf50` csak az `ok` ágban van. A dispatcher címét a `string_xrefs` is a `cancel` parancshoz köti. A job-167 People-ablak Escape-je változtatás nélküli zárást mutat, de nem történt szerkesztés és nem a Cancel gombot kattintotta; ezért a módosított profil állapotára nincs független mérés. A bináris út állítása feltételes marad, amíg J6 nem hasonlítja össze a fájlokat.
- **Cáfoló: a két „javaslat” azonosítása.** A út: a job-167, 22. kép jegyzete szerint a `Tes` beírásakor arcképes „Teszt Elek” névjegy-kiegészítés jelenik meg; a job-207 útmutató külön az arcfelismerés utáni hasonlóarc-javaslatot a személy-albumhoz köti, a job-213-ban pedig ez nem jelent meg, mert a hasonló arcú képek meg voltak nevezve. B út: a bináris `PeoplePanel::AutoCompleteProvider` útja (`0x00643940` → `0x007b4990` → `0x00491980`, 38.9) a gépelt szöveghez névjegy-listát készít. A két út egyezik abban, hogy a `Tes` lista névjegy-kiegészítés; a valódi arcfelismerési javaslat megjelenése és elfogadási/elutasítási kimenete nyitott.
- **Cáfoló: rögzített, 16 jegyű PicasaPy kontaktazonosító.** A job-213 komment régebbi állítása szerint a PicasaPy 16 jegyet ír; a jelenlegi 0.9.179-ös forrásban a `generate_contact_id()` `format(value, "x")`-et használ (`src/picasapy/ini/contacts.py:32-38`), tehát nem tölt balról nullákkal. A bináris formátumsztring `0x00c82fcc`-nél `%I64x`, a job-213 konkrét kimenete pedig 15 jegy; a két, egymástól független eredeti bizonyíték egyezik, a jelenlegi forrás formázása is megfelel. Az ID-előállítási algoritmus egyezését ez nem állítja.
- **Cáfoló: zoom.** A `picture_zoom` inverz ágát is ellenőriztem: `arg==0` aktiválja, míg `face_zoom` az argumentumot közvetlenül használja. Ez összhangban van az 1→face olvasattal, de ugyanazon diszasszemblálás része, ezért az alapértelmezett leképezés **feltételes**, nem megerősített.

### 35.2 A `PeopleAlbumUseFaceSrc` bináris leképezése

A `0x005e5290` a `Preferences\\PeopleAlbumUseFaceSrc` értékének 1 alapértéket ad (`0x005e52b5`), majd a `0x005e52f5` címen átadja a `0x00767e50` függvénynek. A `face_zoom` ág (`0x00767f54`-`0x00767fb0`) az argumentumot közvetlenül állítja be; a `picture_zoom` ág (`0x00767ec5`-`0x00767f36`) az argumentum ellentettjét. Ezért **az alapérték 1 → `face_zoom` aktív, `picture_zoom` inaktív**; a 0 az ellenkező módot választja.

**Fok: feltételes.** Egy diszasszemblált út olvassa a preferenciát és oldja fel az értékét; job-213 csak a két ikon jelenlétét rögzíti, kattintási hatást és első megjelenített képet nem. A cáfoló próba a másik ág olvasása volt; ez megerősíti az inverz logikát, de nem második független út. J5 első képkockája és mindkét gomb kattintása kell az élő megerősítéshez.

### 35.3 A #5185 „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték |
|---|---|---|
| 1. Név nélküliek nézet, fejléc, csoport, méret/sorrend, tálca/kijelölés | ⛔ Részben | Job-162/163/207/208: nézet, felirat, csoportváltás és üres kezdőtálca. Colab #63, `Colab EN 36`: a névmezők 172×20 px-esek; a hat látható arcképkeret mérete képkockához kötve megvan (19.1, 5. pont). Más felbontás skálázása, stabil sorrend/csoporthatár és Ctrl/Shift/húzás tálcahatása nyitott. |
| 2. Arc kijelölése, névmező, javaslat, Enter/OK, cél/lista | ⛔ Részben | Job-163/167/179 és `0x00787dd0`, `0x007b81e0`: csempe-mező, People/Choose és névjegy-kiegészítés. A felhasználói Enter-viselkedés mért: új névnél a People ablak nyílik meg (job-163, 11-19. kép); meglévő névnél a People ablak a `Choose` gombbal nyílik meg (job-167, 22., 26-30. kép), majd a `Choose` hozzárendeli az arcot a személyhez (job-179). A bináris eseményút részlete nyitott: a `CAutoCompleteListBox` `param_2 != 0` ágai az elfogadó rutint hívják (`0x00809360` → `0x00a54b70`), de a csempe-popup bekötése és a javaslatelem elfogadása utáni állapot nincs felmérve (19.7). Escape-re a csempe visszaadja az eseményt (`0x00a644bb` → `0xf4241`; `[this+0x384]` nulla); a szülő viselkedése és a mező visszaállítása nyitott. A névablak nélküli javaslat-elfogadás tartós arc-hozzárendelése, valamint a Ctrl/Shift/húzás kijelölési szabálya nyitott.
| 3. Arcfelismerési javaslat és elfogadás/elutasítás | ⛔ Részben | Job-207 súgó; job-213-ban nem volt javaslat. A bináris parancs-hozzárendelés megerősített: addname → 0x00646d70, yes → 0x00646ec0, no → 0x00647020 (26.3). A javaslat UI-ja és tartós elfogadási/elutasítási kimenete nyitott. |
| 4. Mellőzés és visszahozás | ⛔ Részben | Job-209/210: X, megerősítés, ignored nézet, `ffffffffffffffff` sentinel; a vizsgált People Manager/személyalbum felületeken a job-222..226 szerint nincs személyszintű Ignore (37.11). A kibontott Név nélküliek fejlécének `Ignore Selected` művelete és a `Back to Unnamed` utáni állapot nyitott. |
| 5. Személy-album műveletei | ⛔ Részben | Job-213 nézet és zoomikonok; job-222/223/224 jegyzet a törlés megerősítését és ini/db3 hatását dokumentálja (37.10). Zoomkattintás, átnevezés és teljes album-összevonás nyitott. |
| 6. People Manager | ⛔ Részben | `runtime/contactmgr.fen:1-80`, job-163/226 jegyzetek és a közvetlenül ellenőrzött `Colab EN 23 - People Manager.png` (Colab #22, 1280×1024): balra Search/lista/Delete Person/New Person, jobbra Name/Email(s)/Sync/Revert, alul Manage Online Contacts/Refresh Contacts/OK/Cancel. A `cancel` bináris útvonal validálás/mentés nélkül bezár. A `0x007b9630` aktuális kijelölt indexet tárol, a `0x007ba820` törlési útja ezt használja; a `.fen` nem ad kijelölési módot, így a Ctrl/Shift többszörös kijelölés, a módosított mezők tartós hatása és az OK utáni mentés nyitott (47.1, 48.3). |
| 7. Névforrások/időzítés | ⛔ Részben | Job-210/213: ini-alak; job-224: `faces=` törlése, `[Contacts2]` megmarad és db3 változik. A `.picasa.ini` `[Contacts2]` visszaállító útja `0x0045a9d0` → `0x00587110`. A `contacts.xml` és `backup.xml` külön beolvasási útja `0x00581920`-ban: elemzőhívások `0x00581a24` és `0x00581b6a`; sikeres backup-beolvasás után `contacts.xml` helyreállító írás `0x00581bcb` (35.10). A normál íróút `+0x13c` jelzőt vizsgálja (`0x00586bd0` → `0x00580110`), míg a betöltő a `+0x13d` bájtot állít. People OK a kontaktot memóriában frissíti és piszkos jelzőt állít (`0x007baf50` → `0x005849d0`; 35.12); a PicasaPy 0.9.187 forrásban a `contacts.xml` mentés a párbeszéd commit-hívásában történik (35.14). Az eredeti lemezre írás pontos ideje és a teljes műveleti ini/db3 diff J8-cal nyitott.
| 8. Felismerés indítása/kihagyások/küszöb | ⛔ Részben | A 0,50-es `FRRecommendIncludeLimit` külön ajánlásba-vételi szűrő (35.10), nem Red.dll-detektorküszöb. A `0x100057c0` pontszámokat gyűjt, a `0x10001570` státuszkódot kezel. A `vfr_SdkRelator` `+0x40` slotja a `0x100a3a50` átirányítóhoz vezet, amely a belső objektum `+0x40` virtuális slotjára ugrik; a `vfr_FusedRelator::sim` (`0x100a8240`) csak jelölt. A helyi Red.dll ugyanabban a könyvtárfában van, mint a 3.9.141.259-es `Picasa3.exe`, de az index riportja 3.7-es forrást nevez meg, és a DLL-nek nincs PE verzió-erőforrása; a pontos párosítás nyitott. A helyi függvényben a `vqc_Relator::sim` (`0x10100a10`) véges pontszámot 0 és 1 közé korlátoz (feltételes olvasat), de a futásidejű kötés és az elfogadási küszöb ettől nem ismert (52.5). A 3.9-es Red.dll-azonosság, a végső küszöb, a bemeneti képméret, valamint az eredeti indítás/kihagyás továbbra is nyitott. A PicasaPy 0.9.187 forrása YuNet 0,9 alapértéket, 960 px-es maximumot és azonosított arcot tartalmazó fotó kihagyását mutatja; ezek forrásolvasatok, nem futásidejű mérések (35.14). A döntő azonosított/névtelen kontroll J7. |

A pontok mind ki vannak mondva és minden nyitott részhez konkrét J2-J8 felvételi út tartozik; a kutatás az eredeti műveletek és fájlhatások hiánya miatt nem állít teljes viselkedési lezárást.

### 35.4 Jegytörzs-bővítés és fejlesztési következmény

**Beemelhető szöveg:** „A #5185 nyolc pontjának Eredeti / Nálunk / Teendő összevetése a `docs/specs/picasa-arcfelismeres.md` 35. szakaszában van. A Név nélküliek csempemezője a binárisban dinamikusan létrehozott `faceclusterpanel_%d_addname` vezérlő (`0x00787dd0`); különáll a fejléc `unknownfaceheaderpanel/addname` elemétől. A People ablak meglévő személy esetén `Choose` feliratra váltó ága a `0x007b81e0`-ben van, és egyezik a job-167/179 felvételekkel. A csempe Escape-et a billentyűkezelő nem fogyasztja (`0x00a644bb` közös `0xf4241` kilépés; `[this+0x384]` állandóan 0), a `CAutoCompleteListBox` nem nulla `param_2` ága pedig az elfogadó rutint hívja (`0x00809360` → `0x00a54b70`; 19.7), de a csempe-popup bekötése és végállapota nyitott. A névablak nélküli arc-hozzárendelés és a csempe Enter People-ablakig tartó útja nyitott. A job-167 Escape a People ablak Search mezőjében történt, nem a csempe mezőjében. A PeopleAlbumUseFaceSrc default 1 a binárisban `face_zoom` aktív állapotot jelent (`0x005e5290` → `0x00767e50`; feltételes, az első élő képkocka még kell). A job-167 gépelt névlistája névjegy-kiegészítés, nem arcfelismerési javaslat. A PicasaPy 0.9.179-ös forrása a csempe névjegy-cache-ből ad képes javaslatlistát, és a sorra kattintást ugyanarra a People ablakot nyitó útra köti, mint az Enter (`UnnamedFacesView.qml:448-453, 560-588, 664-698`; `Main.qml:3867-3869`; `PeoplePanel.qml:196-210`); ez forrásolvasat; a 19.7 szerinti bináris egérút elfogadást hív, de a névablak nélküli végső arc-hozzárendelés élő kimenete nyitott. A javaslatparancsok helyes bináris hozzárendelése addname → 0x00646d70, suggestion_yes → 0x00646ec0, suggestion_no → 0x00647020; elfogadás/elutasítás tartós kimenete nyitott. Az X-es mellőzés és az ffffffffffffffff ini-érték job-209/210 alapján dokumentált; a fejléc mellőzése és a visszahozás utáni állapot nyitott. A job-222/224 jegyzet törléskori ini/db3-hatást dokumentál; contacts.xml és műveleti mentési időzítések J8-cal nyitottak.”

**Fejlesztési jelölt, élő megerősítés után:** a jelenlegi PicasaPy forrás teljes képet használ alapállapotként; a Picasa bináris alapértéke `face_zoom`. Ha J5 megerősíti az eredeti első képkockát, a fejlesztési feladat a PicasaPy személy-album alapmódjának és a két zoomgomb tartalmának egyeztetése. **Kész, ha:** eredeti és PicasaPy képkockán az alapmód és mindkét váltás egyezik, és a preferencia követi a mért visszatöltési viselkedést. A mostani adat ehhez még nem elég: preferencia-újratöltés és élő eredeti mód nyitott. A többi #5179-#5184 jegy cím/törzs-hozzárendelése ebben a helyi feladatban **NINCS MEG**; ne következtessünk rá a jegyszámokból.

**Kiegészítés a névjavaslat- és névforrás-részekhez:** a `Tes` mező alatti arcképes lista a névjegy-kiegészítő (`0x00643940` → `0x007b4990` → `0x00491980`, 38.9), nem az arcfelismerés által ajánlott új arcok listája. A `contacts.xml`/`.picasa.ini`/db3 időzítés továbbra is J8 felvételt igényel. Az eredeti `%I64x` alak és a PicasaPy jelenlegi, kitöltés nélküli `format(value, "x")` alak egyezik; a névjegy-azonosító formázásában nincs fejlesztendő eltérés. A nyitott #5179-#5184 jegyek tartalmát e munkamenet nem tudta átírni, mert a GitHub nem volt elérhető, és a helyi feladatanyag nem tartalmazta a jegyek törzsét.

**Pontosítás a 3.9-es jegytörzshöz:** a helyi Red.dll a 3.9.141.259-es `Picasa3.exe` könyvtárfájában található, de a Red-index átadási riportja Picasa 3.7-es forrást ír, a DLL PE verzió-erőforrása hiányzik. A pontos 3.9-es párosítás nyitott; a `vqc_Relator::sim` leletét nem szabad a 3.9 végső felismerési küszöbeként átvenni. A verzióazonosságot tiszta 3.9-es telepítőből vagy az eredeti Colab-példányból származó DLL hash-ével kell feloldani; az indítási/kihagyási szabályokhoz és a fájlhatásokhoz továbbra is J7/J8 kell. A nyitott #5179-#5184 jegyek helyi törzse nem áll rendelkezésre, ezért a kutatókör nem rendelt a nyolcpontos leltárból kitalált fejlesztési listát az egyes jegyszámokhoz.

### 35.5 Új kutatási jegyjavaslatok és nyitott pontok

Új külön kutatási jegy nem szükséges; a nyitott feladatok ugyanazon #5185/J2-J8 felvételi folytatásai:

- **J2:** arc-kijelölés, Ctrl/Shift/húzás és tálca; minden művelet után képkocka és állapotszöveg. A job-164 folytatásában külön próbáld a csempe névmezőjében a javaslatelemre kattintást, majd fókuszált mezőben az Escape-et; ments képkockát és az arc/lista állapotát. A Colab #63 képkockán a névmező 172×20 px, a hat képkeret zárt határa és mérete a 19.1, 5. pontban szerepel. A tartós sorrendhez, többarcú csoporthatárhoz és más felbontás skálázásához új, stabil azonosítójú mintafelvétel kell. A pontos Enter/javaslat callback-lánchoz célzott Ghidra-kör: `0x00787dd0`.
- **J3:** egy megnevezett személy és egy hasonló névtelen arc; javaslat felvétele, elfogadás és elutasítás külön profilban, fájlok előtte/utána/újraindítás után.
- **J4:** kijelölt arccal `Ignore Selected`, majd a mellőzött nézetben `Back to Unnamed`; csempeállapot és ini/db3 diff. Személyszintű Ignore nincs a dokumentált job-222/job-226 belépési pontokon.
- **J5:** első személy-album képkocka, mindkét zoomgomb, átnevezés, összevonás, törlés és adatváltozás-összevetés.
- **J6:** People Manager kijelölés, OK, Cancel és Escape külön; contacts/ini/db3 állapot előtt/után.
- **J7:** import/új mappa/új kép indítása, megnevezett fotón másik arc, kizárt mappa és pontos küszöbállások; Red.dll paramétert becsülni tilos.
- **J8:** eredeti profil `contacts.xml`, `.picasa.ini` és db3 másolata minden művelet előtt, után, bezáráskor és újraindítás után.

### 35.6 2026-10-21-i forrásellenőrzés: PicasaPy 0.9.179 és a People párbeszéd

**Forrásállapot.** A `pyproject.toml:13` szerint a 2026-10-21-i pillanatkép PicasaPy 0.9.179 volt. Az alábbi „Nálunk” részletek az akkori forráskód olvasatából származnak; a PicasaPy-t abban a körben nem futtattam, ezért ezeket nem tekintettem élő felületi mérésnek. A jelenlegi, 0.9.185-ös forrásauditot a 35.7 tartalmazza.

| Rész | Eredeti | Nálunk (0.9.179 forrás) | Teendő / nyitott |
|---|---|---|---|
| Név nélküliek csemperács és arcmező | Job-208: csoportosítva öt oszlop; kibontva egy sor, kisebb csempék és a fejlécmező. A job-163/207 jegyzetek adják a feliratokat és útmutatót. | `UnnamedFacesView.qml:34` alapból `grouped: true`; `:418-420` a csoportosított és kibontott módhoz külön rácscella-méreteket ad; `:472-487` a képcsempe méretét mód szerint váltja; `:560-588` névmezőt csak csoportosított módban jelenít meg. Ezek forrásdeklarációk; a PicasaPy ténylegesen kirajzolt méretét ebben a körben nem mértem. A `:489-492` kattintó csak a `toggleFace(faceId)` hívást adja át, módosítóbillentyűt nem. | Eredeti arckivágás-méret, stabil csoporthatár/sorrend és Ctrl/Shift/húzás tálcahatása továbbra is J2 felvételt igényel. |
| Gépelési javaslat és Enter | Job-167: a `Tes` alatt névjegykép + „Teszt Elek”; a teljes név+Enter People ablakot nyit, meglévő személyre `Choose` gombbal. | `people_controller.py:200-229` a névjegy-cache előkészítése és szűrése; `UnnamedFacesView.qml:448-462, 560-588` Enterre kiválasztott javaslatot vagy beírt nevet küld; `:664-698` a sor képet/nevet mutat, kattintásra ugyanazt a `submitName`-et hívja. `Main.qml:3867-3869` `nameFaceFromPanel(..., true)`-t ad át, amely meglévő névnél is a People ablakra irányít (`PeoplePanel.qml:196-210`). Ez forrásállapot, az eredeti javaslatsorra kattintás eredménye nyitott. | J2-ben külön mérendő az eredeti javaslatsorra kattintás és csempe-Escape. A job-167 Escape-je a People ablak Search mezőjére vonatkozott. |
| People párbeszéd szerkezete és mentése | A `runtime/contactmgr.fen:1-80` balra Search/lista/Delete Person/New Person, jobbra névjegymezők és alul online/refresh/OK/Cancel gombokat definiál. A közvetlenül megnyitott `Colab EN 23 - People Manager.png` (Colab #22, 1280×1024) ugyanezeket a látható elemeket igazolja az üres listájú állapotban. Job-163 és job-226 más állapotokat ír le; a `.fen` opcionális azonosító-csoportjainak láthatósága nem következik ebből a képkockából. | A `PeopleManagerDialog.qml:91-136` újranyitáskor keres, és pontos névegyezésnél kiválaszt; `:442-480` egy aktuális sort kezel; `:335-408` mentéskor validál, változásokat ír, majd arcot rendel; `:605-629` a `Choose`/`OK` címkét és a Cancel gombot köti. A PicasaPy Cancel gomb `manager.close()`-t hív, a forrás mentési útja külön `commitChanges`. | Eredeti listakijelölés (egyes/többes), a `.fen` opcionális mezők tényleges láthatósága és Cancel utáni profilállapot J6-ban ellenőrizendő. A bináris `0x007b99a0` Cancel-ágáról lásd 38.8: bezárás, validálás és mentés nélkül; a tartós adatállapot külön felvétellel zárható le. |

**2026-10-22-i képkocka-ellenőrzés, független út és cáfoló próba.** A `.fen` vezérlőleltárát a job-163/226 képernyőjegyzetekkel és a közvetlenül ellenőrzött `Colab EN 23 - People Manager.png` képkockával vetettem össze: a Search/lista, a két hasáb, a Name/Email(s), valamint az alsó gombsor egyezik; az azonosító-mezőcsoportok láthatóságát viszont egyik felvétel sem bizonyítja. Ez cáfolja azt a tágabb állítást, hogy a `.fen` összes mezője mindenkor látható a People ablakban. A névmező-út külön kétutas eredménye (job-163/167/179 és `0x00787dd0`/`0x007b81e0`) a 35.1-ben marad; az eredeti popup-kattintás és csempe-Escape nem zárult le.

**Névforrások állapota nem változott.** Job-210/213/224 és a 32.1-32.4 szakasz az `.picasa.ini` arc-/Contacts2-alakját, illetve a törléskori db3-hatást dokumentálja. A `contacts.xml` beolvasási/írási időzítése és a `0x00586e20` közvetlen fájlíró szerepe továbbra is **NINCS MEG**; a `0x00586e20`-at csak jelölt mentési segédként szabad idézni.

### 35.7 2026-10-22-i forrásaudit: PicasaPy 0.9.185, és a csempe-névkiegészítés bináris határa

**Forrásállapot.** `pyproject.toml:13` = `0.9.185`. A helyi eredeti `Picasa3.exe` SHA-256: `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`, image base `0x00400000`; az index eredetadata egyezik. A „Nálunk” oszlop alább kizárólag a helyi forrás statikus olvasata, nem futásidejű UI-mérés. Az eredeti felvételi állítások a 35. táblázat megfelelő pontjában maradnak; ahol nincs mérés, a Teendő oszlop fenntartja a konkrét megszerzési utat.

| Pont | Eredeti (mért jegyzet / bináris) | Nálunk (0.9.185 forrásolvasat) | Teendő / nyitott |
|---|---|---|---|
| **1. Név nélküliek nézet, kijelölés és tálca** | Job-162/163/207/208: `Unnamed people`, `N Face(s)`, csoportosított öt oszlop, Expand groups / Show ignored faces; kibontva kisebb csempék és fejlécmező; induláskor `No Selection`, üres tálca (35. pont 1.). | A bal sori kattintás törli a keresőt és a fotókijelölést, `unnamed` módot állít és megnyitja a nézetet (`Main.qml:3425-3429`; a fotókijelölés forrása `:886-889`). A `UnnamedFacesView` láthatóságakor csoportosított módot állít és újratölt (`UnnamedFacesView.qml:145-160`); mód- és csoportváltáskor üríti az arc-kijelölést (`:150-155`). Tálcaürítés ebben a hívási láncban nincs dokumentálva. | A PicasaPy tálcájának megnyitáskori állapota futásidejű próbát igényel. Az eredeti Ctrl/Shift/húzás, tartós sorrend és csoporthatár továbbra is J2 (35.5). |
| **2. Arcnév, gépelési javaslat és People ablak** | Job-163/167/179: csempemező; névjegykép + név gépelés közbeni listában; Enterre People ablak, meglévő névnél `Choose`; választás után arc hozzárendelődik (35. pont 2.). A `0x00809360` nem nulla `param_2` ágán elfogadó rutin fut (`0x00a54b70`), de a csempe-popup vezérlőbekötése nem bizonyított. A kattintás utáni név-/párbeszéd-/arcállapot és a csempe-Escape szülői reakciója továbbra is **NINCS MEG**. | A csempe-javaslat névjegy-cache-ből szűrődik, és a sor képet/nevet jelenít meg (`people_controller.py:200-229`, `UnnamedFacesView.qml:429-462, 611-698`). Enter és sorra kattintás ugyanazt a `submitName` jelet küldi (`:580-588, 691-698`); a Main ezt `nameFaceFromPanel(..., true)`-re köti (`Main.qml:3867-3869`), ezért a PicasaPy útja mindkét esetben People ablakot nyit (`PeoplePanel.qml:192-210`). OK-kor a párbeszéd menti a névjegy-változásokat, majd a kiválasztott személyhez rendeli a függő arcot (`PeopleManagerDialog.qml:335-408, 617-623`). | A job-164 lépéseivel az eredeti javaslatelem-kattintás utáni képkockát, listát és `faces=`/`[Contacts2]` diffet, valamint a fókuszált csempemező Escape utáni feliratát és tartalmát kell rögzíteni. A vezérlő-bekötéshez lásd 38.17 és 35.13; a `param_2` szemantikáját nem szabad indexnek nevezni bizonyíték nélkül. |
| **3. Arcfelismerési javaslatok** | A súgó (job-207) szerint névadás után hasonló arc javasolható; elfogadás/elutasítás a személy albumában. Az eredeti tényleges javaslatcsempe és adatváltozása **NINCS MEG** (35. pont 3.). | A pipa a `suggested_name` értékkel elnevezi az arcot; az elutasítás az SQLite-index javaslatmezőjét üríti (`face_scan_controller.py:1022-1050`; a felületkötések `PeoplePanel.qml:150-166`). | J3: hasonló, névtelen arcot tartalmazó kontrollfotó kell, az eredeti UI-művelettel és `.picasa.ini`/`contacts.xml`/db3 előtte-utána állapottal. A PicasaPy saját SQLite-indexe nem Picasa db3. |
| **4. Mellőzés és visszahozás** | Job-209/210: csempe-X megerősítése, `Ignored people`, `Back to Unnamed`, `ffffffffffffffff` ini-érték (35. pont 4.). Fejléc `Ignore Selected` és visszahozás utáni eredeti állapot **NINCS MEG**. | A mellőzött sor `Ignored (N)` (`FolderPane.qml:749-753`); a nézet a `Show ignored faces`/`Back to Unnamed` parancsot váltja (`UnnamedFacesView.qml:261-276`), és az ignorált módban a visszaállító műveletet kínálja (`:349-355`). A kibontott nézet fejlécmezője és `Ignore Selected` gombja csak kijelöléskor/nézetmódban jelenik meg (`:318-370`). | J4: eredeti fejlécgomb kijelölt arccal, majd Back to Unnamed; képkocka, ini/db3 és sorszám a művelet előtt/után. |
| **5. Személy-album** | Job-213: arc- és teljeskép-váltó, Remove; az első mód, átnevezés, egyesítés eredménye részben nyitott (35. pont 5.). | A fejléc alapértéke `faceZoom: false`, a két gomb `headerFaceZoomButton` / `headerPictureZoomButton` ezt váltja (`LightboxHeader.qml:94-98, 239-280`), így forrás szerint teljes kép az alapnézet. A kontaktkezelő `update`, `delete`, `remove_album` műveletet fogad (`people_controller.py:375-405`); külön egyesítési műveletet ez a commit-út nem tartalmaz. | Eredeti módváltás, átnevezés, két személy teljes összevonása: job-213 folytatása, a két ini és db3 állapot rögzítésével. A PicasaPy statikus forrása nem zárja az eredeti kérdést. |
| **6. People Manager** | Job-163/167/226 és `runtime/contactmgr.fen`: elrendezés, mezők, `OK`/`Choose`/`Cancel` (35. pont 6.). A többes kijelölés és módosított mezők utáni eredeti Cancel-adatállapot **NINCS MEG**. | A dialógus 632×372-es QML Dialog, Search és egy `currentIndex`/`selectedKey` kontakt-sor állapottal; új névnél előtölti a keresést, pontos egyezésnél kiválaszt (`PeopleManagerDialog.qml:7-29, 91-134, 149-164, 445-479`). OK `commitChanges(false)`-t hív, Cancel csak bezárja a dialógust (`:617-628`). Ez forrásmodell, nem élő PicasaPy-kijelölés. | J6: eredeti Ctrl-kijelölés, módosítás utáni Cancel és Escape; profilfájlok előtte/utána. A bináris Cancel pontos ágát lásd 38.8. |
| **7. Névforrások** | Job-210/213/224, `0x00587110`, `0x00586e20`, `0x00c82fcc`: `[Contacts2]`, `faces=`, mellőző sentinel, ID-formátum és db3-hatás részei dokumentáltak; a 35.10 azonosítja a `contacts.xml` olvasó- és írófüggvényeket, de a People Manager műveleti időzítése továbbra is **NINCS MEG**. | A PicasaPy `contacts.py` olvassa a `[Contacts2]` hárommezős értékét és az új ID-t nem nulla 64 bitből, vezető nulla nélkül hexázza; `ensure_contact` `név;;` értéket ír (`ini/contacts.py:32-37, 48-68, 81-94`). A People Manager a központi `contacts/contacts.xml`-t menti, az érintett mappák ini-jét frissíti; a PicasaPy saját SQLite-indexet használ, nem Picasa db3-at (`people_controller.py:370-405, 499-540`). | A névadás/Choose, javaslat, átnevezés és törlés előtti/utáni `contacts.xml`/db3 diff, bezáráskor és újraindítás után: J8 (35.10). |
| **8. Arcfelismerés** | Eredeti indítási esemény, kihagyási feltételek és Red.dll belső küszöb **NINCS MEG**. A `FRRecommendIncludeLimit=0,50` külön, binárisan igazolt ajánlásba-vételi szűrő (35.10). | A PicasaPy automatikus scan kapcsoló alapértéke bekapcsolt; `scanNewFaces` a könyvtárszinkronhoz kötött (`face_scan_controller.py:290-305, 775-784`). Kihagyja a tiltott mappát, videót, változatlanul már vizsgált fájlt és az ini-ben azonosított arcú fotót (`:474-496`). Saját YuNet út: max. 960 px, score `0.9`, NMS `0.3`, top-k `5000` (`faces/detector.py:40-49, 178-210`); ez nem bizonyít eredeti küszöböt vagy viselkedési egyezést. | J7: eredeti első import/új fotó/tiltott mappa/névvel címkézett fotó, pontos profil-diff és célzott Red.dll feltárás; becslés nélkül. |

**Bináris kiegészítés és az névkiegészítő-állítás cáfolata.** A `0x006436b0` a `PeoplePanel::AutoCompleteProvider` `0x00ca1740` elsődleges vtáblájának `+0x2c` slotja (RTTI és a binárisbeli pointer külön adatútja). A függvény a kijelölt 8 bájtos rekord-azonosítót a `0x0044d650`-nek adja; az utóbbi a `0x005863f0` kontaktrekord-lekérdezés után sztringet hash-el (`0x0044d5b0`), majd a kontextus `+0x24d4` tárolójával hasonlít (`0x004972b0`), és logikai értéket ad vissza. Ez névkiegészítő elemhez tartozó predikátum; a vizsgált két függvényben nincs arc-hozzárendelés és People ablak nyitás. Ezért a 38.9-ben korábban szereplő „valószínűleg ez az elfogadás útja” következtetés visszavonva: a függvénypár nem bizonyítja, hogy a `faceclusterpanel_%d_addname` csempemező popupja ezt a callbacket használja.

**A két független út.** A: a helyi diszasszemblálásban a `0x006436b0` az ID-párt adja át, a `0x0044d650` pedig rekordot keres, hash-t számol, összehasonlít és logikai eredményt ad. B: az RTTI/vtábla-pointer a címet az `AutoCompleteProvider` osztályhoz rendeli; a külön xref-hálózat megmutatja a `0x0044d650` másik hívóit, amelyek az `AL` értéket logikai predikátumként fogyasztják, utána külön ággal folytatva. Egyezésük csak a callback általános szerepére vonatkozik, nem a csempe konkrét bekötésére.

**People OK/Mégse utasításszintű ellenőrzése.** A `0x007b99a0` `ok` ága a `0x007bb660` validálást, majd a `0x007baf50` mentést hívja; csak mindkét sikeres eredmény után jut a `0x008d2720` bezáró segédhez (`0x007b9a08`, `0x007b9a1a`, `0x007b9a2e`). A `cancel` ág közvetlenül a `0x008d2720`-hez jut (`0x007b9a90`), itt a validáló és mentő hívás nincs jelen. Az OK második bezáróargumentuma konstans nulla, a Cancelé a bemeneti `[EBP+0xc]`; ezért a Cancel-ágra nem szabad rögzített eredménykódot állítani. Ez az ág nem bizonyítja, hogy a dialógus korábbi, külön műveletből eredő mentéseket visszavon.

**Cáfoló kísérlet.** Azt a korábbi feltevést próbáltam igazolni, hogy a `0x006436b0 → 0x0044d650` egy névkiegészítő sor elfogadásakor arcot rendel, illetve People ablakot nyit. Cáfoló ellenőrzésként a két függvényen kívüli `0x005bd7e0` és `0x0044d7e0` hívó utáni utasításokat néztem meg: mindkettő az `AL` értéket logikai feltételként használja, és külön vezérlési ágon folytatja a munkát. Az RTTI a vtable-szerepet külön megerősíti. A „callback nem arc-hozzárendelő művelet” állítás megáll; a „csempe-callback nincs használva” negatív következtetés nem állítható, mert indirekt vtable-hívás lehet. A csempe-popup pontos bekötése blokkoló Ghidra-kérdés marad.

**Bizonyítottsági fok.** A 35. pont nyolc eredeti viselkedéscsoportja továbbra is **nyitott**, mert a felvételi jegyzetek egy része nem ellenőrizhető vissza nyers képkockából, és a kiemelt javaslat-/tárolási kérdésekhez új mérés kell. A 0.9.185-ös QML/Python útvonalak statikus forrásolvasata **feltételes**; élő UI-egyezést nem mértem. Az névkiegészítő predikátum általános szerepe **megerősített** (utasításszintű diszasszemblálás, RTTI/vtábla és külön xref-hívók). Az OK/Cancel ágak sorrendje **feltételes** (utasításszintű olvasat; a string-xref és a job-167/179 jegyzet csak a parancsnevet, illetve a megfigyelt Choose/Escape felületi kimenetet támasztja alá). A csempe popup konkrét bekötése és a módosítás utáni Cancel teljes profilállapota **NINCS MEG**.

**A „Kész, ha” pontok állapota (a 35. pont 8 sora szerint):**

1. **Részben dokumentált, lezáratlan:** job-162/163/207/208; Ctrl/Shift/húzás, tartós sorrend, csoporthatár és tálca-viselkedés nyitott.
2. **Részben dokumentált, lezáratlan:** job-163/167/179; csempe Escape és javaslatsor-kattintás nyitott; a mostani bináris kör szűkítette a popup-kötés kérdését.
3. **Részben dokumentált, lezáratlan:** job-207/213; eredeti javaslat elfogadása/elutasítása és tárolási hatása nyitott.
4. **Részben dokumentált, lezáratlan:** job-209/210; fejléc `Ignore Selected` és visszahozás utáni eredeti állapot nyitott.
5. **Részben dokumentált, lezáratlan:** job-213; személynév átnevezés, album-egyesítés és a váltó tényleges első állapota nyitott.
6. **Részben dokumentált, lezáratlan:** job-163/167/226 és `0x007b99a0`; többes kijelölés, szerkesztett Cancel utáni adatállapot nyitott.
7. **Részben dokumentált, lezáratlan:** job-210/213/224 és bináris címek; contacts.xml/db3 műveleti olvasás/írás és időzítés nyitott.
8. **Részben dokumentált, lezáratlan:** PicasaPy saját scan-forrása pontos; az eredeti indítás, kihagyások és Red.dll-küszöb nyitott.

Az eredeti felvételi állítások és a forrásaudit így mind a nyolc pontnál elkülönülnek, de a #5185 teljes „Kész, ha” feltétele - minden eredeti állítás visszakereshető képkocka/bináris cím és a nyitottak konkrét felvételi útja - **még nem teljesült**.

### 35.8 Jegytörzsbe emelhető frissítés és további munka

**Javasolt #5185 jegytörzs-szöveg:** „A nyolcpontos Eredeti / Nálunk / Teendő spec a `docs/specs/picasa-arcfelismeres.md` 35. szakaszában van; a 35.7 a PicasaPy 0.9.185 aktuális statikus forrását auditálja, a 35. pont korábbi eredeti-felvételi adatait pontos címekhez köti. Az eredeti csempe-névkiegészítés kattintása, csempe-Escape, javaslat-elfogadás/elutasítás, fejlécbeli mellőzés, személyalbum átnevezés/egyesítés, People Manager kijelölés/Cancel utáni profilállapot és a pontos fájl-időzítés továbbra is nyitott; a bináris szerint az OK ág módosított sort ment a memóriabeli névjegykezelőbe, majd piszkos jelzőt állít (`0x007baf50` → `0x005849d0`), míg a `contacts.xml` írója külön, piszkos jelzőt ellenőrző útvonalon fut (`0x0041ba40` → `0x00586bd0` → `0x00580110`; 35.12). A tényleges fájlírás ideje, a `.picasa.ini`/db3 diff, az eredeti scan-indítás/kihagyás és a Red.dll belső küszöbe nyitott; a 0,50-es FRRecommendIncludeLimit külön ajánlásba-vételi szűrő, a `0x10001570` pedig státuszkódot ellenőriz (35.10-35.12). A `0x006436b0 → 0x0044d650` általános névkiegészítő predikátum; nem bizonyít arc-hozzárendelést vagy People ablak nyitást. A `0x007b99a0` OK ága validál és ment, a Cancel ág közvetlenül a közös bezáró hívást kéri, de a teljes profil-visszaállítás nem igazolt. Következő lépés: a J2/J3/J4/J5/J6/J7/J8 célzott Colab-felvételei és a még nyitott csempe-Enter virtuális élek célzott Ghidra-köre (§19.7/G); a `0x007853e0`/`0x007899e0` törzse és hívói már feldolgozva.”

**A #5179-#5184 GitHub-jegyek átírása:** ebben a helyi kutatói munkamenetben a GitHub nem volt elérhető, ezért az egyedi jegytörzseket nem írtam át; a szükséges eredeti viselkedési különbségek és forrásbizonyítékok a fenti táblákban, illetve az 1-8. pont teendőiben szerepelnek. A nyitott eredeti mérések a #5185-höz tartoznak, nem indokolnak új, külön témájú kutatási jegyet.

### 35.9 Nyitott és megszerzési út

**A korábbi `0x007853e0`/`0x007899e0` bontás lezárva:** a csempe-Enter nyitott szolgáltató- és szülőkezelő vtábla-élei, a People-megnyitóig tartó feltétel és az ablak nélküli névírás kérdése a 19.7/G célzott Ghidra-kéréseiben szerepel (`0x0063eb20`, `0x00644010`, `0x0063e370`, `0x005cb990`, `0x00a54b70`, `0x00608c00`).

- **Colab, job-164 folytatás:** a már létező személy csempe-javaslatára kattintás; külön Enter a csempe mezőjében; külön Escape a csempe mezőjében. Mindegyiknél képkocka, bal oldali számlálók és `.picasa.ini` előtte/utána.
- **Colab J2/J3/J4:** csoportosítási határ és rendezés; Ctrl/Shift/húzás; javaslat elfogadása/elutasítása; fejléc `Ignore Selected`; Ignored → Back to Unnamed. Képkocka és profil-diff minden művelet előtt/után.
- **Colab J5/J6/J8:** személyalbum első zoomállapota, átnevezés és két album egyesítése; People Manager Ctrl-kijelölés, módosított mező utáni Cancel/Escape; `contacts.xml`, `.picasa.ini`, db3 profil-diff bezáráskor és újraindítás után.
- **Colab J7:** eredeti első import/új fájl/új mappa, kizárt mappa, már névvel ellátott arcot tartalmazó fotó; állítsd vissza az eredeti Red.dll hívásláncát a pontszámig és végső döntésig. A `FRSuggestionThreshold`/`FRSortThreshold` Preferences értékei és a külön `FRRecommendIncludeLimit=0,50` szűrő nem adják meg a Red.dll belső detektálási küszöbét.

Ghidra-kör kell: 0x100057c0: a [param_3+8]+0x74 objektum vtable +0x40 callbackjének tényleges célja és saját döntési ága; a 0x10001570 állapotkód-ellenőrzése megvan (35.11) [blokkoló]

### 35.10 2026-10-22-i célzott bináris utánkövetés: contacts.xml és pontszámküszöb

**Keret.** A helyi Picasa3.exe 0x00400000 image base-ű, 3.9.141.259-es binárisán célzott, utasításszintű olvasás készült; a Ghidra-dump a 0x00580110, 0x00581920 és 0x0066f2b0 törzsét is tartalmazza. Colab-felvétel és profilfájl-diff ebben a körben nem készült.

#### contacts.xml: olvasó és író út

- **Olvasás.** A `0x00581920` két külön fájlnevet állít elő. Először a `0x00c90e74` (`contacts.xml`) címet használja útvonalépítéshez (`0x00581975` → `0x009a37b0`), majd a `0x00992ed0` feltétel igaz ágában a `0x00991650` parser-wrappert hívja (`0x00581a09`-`0x00581a24`). A függvény ezután a `0x00c90e94` (`backup.xml`) címből épít külön útvonalat (`0x00581ab4` → `0x009a37b0`), és a második feltétel igaz ágában ismét a parser-wrappert hívja (`0x00581b4f`-`0x00581b6a`). A `0x00991650` közvetlenül meghívja a `0x00991490`-et (`0x0099166e`). Ez utóbbi a kapott útvonallal a `0x00d69520` közvetett címen keresztül hív fájlmegnyitó jellegű rutint; a paraméterek GENERIC_READ=0x80000000, megosztás 1, OPEN_EXISTING=3, FILE_ATTRIBUTE_NORMAL=0x80, a hibás handle -1 (`0x009914b1`-`0x009914cb`). A pontos import/célfüggvény neve **NINCS MEG**, de a read-only megnyitási szándék és a parserbe vezető hívás megvan. A `backup.xml` parserének sikeres visszatérése után a függvény a beolvasott tartalommal frissít, majd meghívja a `contacts.xml` írót (`0x00581b74`-`0x00581bcb`); ezt a helyreállítási ágat nem szabad a két beolvasási út összevonásaként leírni.
- **Betöltési hívási környezet.** Az indexelt egyetlen közvetlen hívó a 0x00586d00, amely a 0x00581920 után állítja a [ebp+0x13d] bájtot (0x00586db3-0x00586dba). A 0x00586d00-t a 0x0041ee10 hívja (0x0041f974); a 0x0041ee10 közvetlen hívója az index szerint a 0x00402f90. Ez betöltési/kezelő-előkészítési hívási láncot mutat, de a felhasználói művelethez kötött pontos időpontot önmagában nem.
- **Kiírás.** A 0x00580110 XML-fa gyökerét contacts néven építi fel, és névjegyrekordokat ír a fába (például contact, id, modified_time, emailN, local_contact, subject, person_id2, focus_ids, sync_enabled, hidden_contact; 0x00580187-0x005809e6). A függvény a contacts.xml útvonalat állítja elő (0x00580a2c-0x00580a35), majd a 0x009c15a0 írósegédet hívja (0x00580a47). Az írósegéd wt módot ad át a megnyitónak (0x009c15b7-0x009c15db), majd a 0x00c07a30 fwrite rutinon keresztül ír (0x009c15f2-0x009c15f7). **A contacts.xml tényleges kiírási útja tehát megvan.**
- **Mikor hívódik az író.** A 0x00581920 a 0x00580110-et a sikeres backup.xml-visszaállítási ágban hívja (0x00581bcb). A másik ismert hívó a 0x00586bd0: csak a [edi+0x13c] jelző nem nulla ágában hívja a kiírót (0x00586c31-0x00586c49). Ezt a függvényt a 0x0041ba40 hívja a #contacts\ útvonal elkészítése után (0x0041bb58-0x0041bb7c). A piszkos jelző beállítása és az, hogy a People Manager melyik művelete éri el ezt az ágat, **NINCS MEG**.
- **Cáfolt hamis nyom.** A 0x0066f2b0 nem a People Manager elsődleges mentési útja: az index egyetlen közvetlen hívóként a 0x0066f470-et mutatja; ez a függvény il_BurnPanel::bkfolder, Backup, option_inifile és option_manifest erőforrásokkal dolgozik. A 0x0066f2b0 a contacts.xml forrásból backup.xml célba másolását kéri a vtable +0x2c slotján. Ez külön biztonsági mentési út.

| Névforrás-állítás | Forrás |
|---|---|
| A contacts.xml és backup.xml külön útvonalból induló parserhívása | bináris (`0x00581975`-`0x00581a24`, `0x00581ab4`-`0x00581b6a`; string-xref: `0x00c90e74`, `0x00c90e94`) |
| Sikeres backup.xml-beolvasás utáni contacts.xml-helyreállító írás | bináris (`0x00581b74`-`0x00581bcb`, `0x00580110`) |
| Read-only megnyitási paraméterek | bináris (0x009914b1-0x009914cb); a közvetett cél neve **NINCS MEG** |
| contacts.xml XML-kiíró út, wt mód és fwrite | bináris (0x00580110, 0x009c15a0, 0x00c07a30) |
| Piszkos jelzőhöz kötött #contacts\ kiírási ág | bináris (0x0041ba40, 0x00586bd0) |
| People Manager műveletenkénti írási időpont és .picasa.ini/db3 diff | NINCS MEG; Colab J8 |

**A két független út.** A út: a `0x00581920` nyers, célzott diszasszemblálása külön mutatja a `contacts.xml`-hez tartozó parserhívást (`0x00581a24`) és a `backup.xml`-hez tartozót (`0x00581b6a`), majd a backup-ág utáni íróhívást (`0x00581bcb`). B út: a Ghidra C-kimenet ugyanezt a vezérlési sorrendet adja, az index string-xrefje pedig a két fájlnevet ugyanahhoz a `0x00581920`-hoz köti (`contacts.xml`: `0x00c90e74`; `backup.xml`: `0x00c90e94`); a writer külön útját a `0x00580110` → `0x009c15a0` → `fwrite` utasításai támasztják alá. A két út egyezik. Az indexelt hívásgráf a betöltő útvonalat a `0x00586d00`-hoz köti, a másik íróhívót a `0x0041ba40` `#contacts\` útjába; a független `0x0066f470` hívó és BurnPanel-erőforrások a `0x0066f2b0` másolását a Backup felülethez kötik. A fájlútvonalak megerősítettek, a People Manager eseményideje továbbra is **NINCS MEG**.

#### Arcfelismerés: Red.dll pontszám és a Picasa utólagos szűrője

A Red.dll 0x100057c0 a callback-pontszámok közül a maximumot választja, és nem tartalmazza a végső küszöb-összehasonlítást (43.2-43.3). A Picasa3.exe 0x0048e1f0 ezután a visszaadott pontszámokat a this+0x34a4 mezővel veti össze (0x0048e252, 0x0048e33e); a mező kulcsa FRRecommendIncludeLimit, bináris gyári értéke 50/100 = 0,50 (21.1). A küszöb alatti pontszám kihagyódik a jelöltajánlási útból, a határérték átmegy. Ez az ajánlásba-vétel szűrője, nem a Red.dll bizonyított detektálási küszöbe; a futó profilban ténylegesen beállított érték **NINCS MEG**. A FRSuggestionSingleThreshold=0,90 külön Preferences-mező, és nem helyettesítheti a Red.dll küszöb bizonyítékát.

**Cáfoló kísérlet és ellenőrzés.** Azt az olvasatot próbáltam cáfolni, hogy a `0x00581920` mindkét parserhívása a `contacts.xml`-re vonatkozik. A nyers utasítások az első hívás előtt a `0x00c90e74` (`contacts.xml`), a második út építésekor a `0x00c90e94` (`backup.xml`) címet mutatják; az index string-xrefje mindkét konstans `0x00581920`-hoz tartozását igazolja. Az olvasat cáfolt, a két fájlút külön van dokumentálva. Azt is megpróbáltam a `0x0066f2b0`-t a People Manager mentésének nevezni, mert contacts.xml sztringet használ. Ez nem áll meg: az indexelt közvetlen hívás a Backup-panel kódjából érkezik, a függvény forrásként contacts.xml-t és célként backup.xml-t ad át a másolási slotnak. Az xref és az utasítások/erőforrások külön ellenőrzése ugyanazt az eredményt adja. Azt is megpróbáltam igazolni, hogy a `0,90` a Red.dll elfogadási küszöbe; a Red rutin csak pontszámot választ, a Picasa-hívóban pedig a külön FRRecommendIncludeLimit mező, alapértéke `0,50`, kerül összevetésre. Ez cáfolja a `0,90`-es Preferences-érték azonosítását, de nem zárja ki, hogy a nem vizsgált belső callback vagy más ág saját küszöböt használ.

**Bizonyítottság.** A contacts.xml- és backup.xml-olvasási utak elkülönítése, a contacts.xml-helyreállító íróút, valamint a Backup-panel külön másolási útja **megerősített**: külön utasításszintű fájlmegnyitás/kiírás és független hívásgráf/erőforrás-út támasztja alá őket. Az FRRecommendIncludeLimit gyári 0,50 értékének alkalmazása az ajánlásba-vételi szűrőben **feltételes**: a bináris mező-hozzárendelése és összehasonlítása ismert, de a jelenlegi felhasználói beállítás és a pontszámskála nem. Az összes #5185-pontra vonatkozó bizonyítottsági fok továbbra is **nyitott**.

**Következő mérés.** J8-ban külön profilpéldányon másold ki a contacts.xml, az érintett .picasa.ini-k és a db3 állapotát név létrehozása, meglévő személyhez rendelés, javaslat elfogadása/elutasítása, átnevezés és törlés előtt, közvetlenül OK/Choose után, az alkalmazás bezárásakor, majd újraindítás után. Jegyezd fel a contacts.xml időbélyegét és tartalmát is. J7-ben rögzítsd a tényleges Preferences-értékeket és a névvel ellátott, többarcú fotó kimenetét; a Red.dll belső küszöbéhez a 0x100057c0 által hívott virtuális callback célzott feltárása kell.

### 35.11 2026-10-22-i Red.dll utánkövetés: a `0x10001570` állapotkódot kezel

**Keret.** A célzott Ghidra-kimenet a `0x10001570` hívót (`2026-10-22-ghidra-sor-198-hivo.txt`) és a `0x100057c0` rutint (`2026-10-22-ghidra-sor-158-198.txt`) tartalmazza. Ezeket külön ellenőriztem az eredeti `Red.dll` ismert VA-tartományainak nyers x86 diszasszemblálásával. Teljes `.text`-pásztázás nem történt.

- **A wrapper (`0x10001570`).** Meghívja a `0x100057c0`-t (`0x100015a2`), majd az `EAX` értékét teszteli (`test eax,eax`, `0x100015aa`). Nulla esetén a sikerágon nullával tér vissza (`0x100015ac`, `0x100015b9`-`0x100015bb`); nem nulla esetén a `0x10001000` segédfüggvényt hívja, majd `0xffffffff`-et ad vissza (`0x100015ae`-`0x100015b6`); a nem nulla státuszt tehát nem továbbítja változatlanul. Lebegőpontos eredményt nem hasonlít küszöbhöz.
- **A hívott rutin (`0x100057c0`).** Jelöltenként a 0,0 kezdőértékhez képest a `vtable+0x40` indirekt callback eredményéből maximumot választ (`0x10005847`-`0x10005880`) és a pontszámot a kimeneti tömbbe írja (`0x100058d2`-`0x100058d8`). Sikeres bejáráskor `EAX=0`-val tér vissza (`0x100058e3`-`0x100058f6`); hibás bemenetnél `EAX=1`-gyel (`0x100058f7`-`0x1000590d`). A pontszám tehát a kimeneti tömbbe kerül, a wrapper által tesztelt `EAX` pedig az állapotkód.
- **Ami ebből nem következik.** A wrapperben és a pontszámokat összegyűjtő `0x100057c0`-ban nincs végső elfogadási küszöb. A `vtable+0x40` callback tényleges célja, annak saját döntési ága, a Red tényleges képbemeneti mérete, valamint a rögzített mintán mért felismerési arány **NINCS MEG**. A Picasa `0x0048e1f0` későbbi `FRRecommendIncludeLimit=0,50` összehasonlítása továbbra is az ajánlásba-vételi szűrő, nem a Red belső detektorküszöbének bizonyítéka.

| Állítás | Forrás | Bizonyítottság |
|---|---|---|
| `0x10001570` a `0x100057c0` eredményét státuszkódként teszteli, nem pontszámként | bináris (`0x100015a2`, `0x100015aa`-`0x100015bb`; Ghidra C és nyers diszasszemblálás) | megerősített |
| `0x100057c0` a callback-pontszámok maximumát a kimeneti tömbbe írja; a függvény státuszkódot ad vissza | bináris (`0x10005847`-`0x10005880`, `0x100058d2`-`0x100058f6`; Ghidra C és nyers diszasszemblálás) | megerősített |
| Red.dll belső detektorküszöb, callback-cél, tényleges bemeneti méret, felismerési arány | NINCS MEG | nyitott; a callback céljának feltárása és kontrollált Colab-mérés kell |

**A két független út.** A út: a Ghidra C-kimenet a `0x10001570` állapotágát, a `0x100057c0` külön kimeneti tömbjét és a 0/1 visszatérési értékét mutatja. B út: a `Red.dll` címtartományra szűkített, nyers Capstone-diszasszemblálása és a friss ellenőrző kör külön `llvm-objdump`-olvasata a wrapper `test eax,eax` elágazását, valamint a belső függvény kimeneti tömbbe írását adja; egyik sem a Ghidra-szövegből indul ki. A két út egyezik abban, hogy a wrapper nem küszöböz, hanem a belső függvény állapotát kezeli. A két út ugyanazt a binárist elemzi, de eltérő elemzési módszerrel; a `0x100057c0` indirekt callbackjének meg nem vizsgált célját egyik sem fedi le.

**Cáfoló kísérlet és ellenőrzés.** Azt próbáltam cáfolni, hogy a `0x10001570` az `EAX`-ban visszaadott lebegőpontos pontszámot a detektor küszöbéhez hasonlítja. A burkoló függvény teljes, címtartományra szűkített utasítássorában az `EAX`-ra csak `test` és nulla/nem nulla ág szerepel; nincs lebegőpontos összehasonlítás, a `0x100057c0` pedig a pontszámokat külön kimeneti tömbbe írja, miközben 0/1 státuszt ad vissza. A Ghidra C-kimenete ettől függetlenül ugyanezt a státuszágat és kimeneti tömböt mutatja. A friss, külön `llvm-objdump`-alapú ellenőrző kör sem talált ellenpéldát, és megerősítette a státuszágat. Ez nem cáfolja, hogy a meg nem nevezett callback vagy egy további Red-ág saját küszöböt alkalmaz.

**Következtetés.** A `0x10001570`-re vonatkozó állítás **megerősített**. A teljes arcfelismerési küszöb és a felismerési viselkedés továbbra is **nyitott**; a 35.3 nyolcpontos táblázatának 8. pontja ezért változatlanul J7 felvételt és a callback útjának célzott feltárását igényli.

### 35.12 2026-10-22-i utánkövetés: People Manager-módosítás és contacts.xml írás

**Hatókör.** A helyi Picasa 3.9.141.259 bináris People Manager-mentési és `contacts.xml`-író útját vizsgáltam a `2026-10-21-people-szuro.txt`, `2026-10-22-ghidra-sor-197-200.txt`, `2026-10-22-ghidra-sor-231-235.txt`, `2026-10-18-ghidra-9.txt`, `2026-10-18-szemelykezeles-7.txt` és `2026-10-17-szemelykezeles-2.txt` Ghidra-kimenetekkel, valamint célzott x86 diszasszemblálással. Futó Picasa-mérés és profilfájl-diff ebben a körben nem készült.

- **People OK, memóriabeli frissítés.** A `0x007b99a0` OK ága előbb a `0x007bb660` validálást, majd a `0x007baf50` mentést hívja (0x007b9a08, 0x007b9a1a). A mentő a módosított kontakt-soroknál a `0x005849d0`-t hívja. A `0x005849d0` frissítési ágában a névjegyobjektum `+0x38` jelzőjének első bitje és a kezelő `+0x13c` piszkos jelzője 1-re áll (0x00584a98-0x00584aa0). Ez a lánc a People OK művelet után memóriabeli módosítást és későbbi mentésre jelölést bizonyít.
- **`.picasa.ini` `[Contacts2]` visszaállítása és jelzők.** A `0x0045a9d0` a `.picasa.ini` útvonalat állítja elő (`0x0045b969-0x0045b975`), majd a nem mellőzött arcazonosítókra a `0x00587110`-et hívja (`0x0045ba28`). A `0x00587110` a `Contacts2` szakaszt és a `%I64x` kulcsot keresi (`0x00587154-0x00587182`), és a visszaállítást a `0x005875d0`-hez adja (`0x00587345`, `0x005873fc`; a függvény naplóüzenete: „Restoring contact ... from .ini file”). Ebből a `.picasa.ini`-beli névjegyek beolvasási útja megerősített. A két `0x005875d0` hívás változásjelző-argumentuma nulla (`0x00587339`, `0x005873f0`), de a rutin a `0x005836f0`-t is továbbhívja; annak adatváltozásos ága a kezelő `+0x13c` jelzőjét állítja (`0x00583c30-0x00583c3f`). Ezért a visszaállítás maga is elérheti a későbbi `contacts.xml`-kiírást kiváltó piszkos állapotot, ha a kontaktadat változik; a konkrét fájlhatás és időpont futásidejű diff nélkül **NINCS MEG**.
- **A betöltőjelző nem a kiíró piszkos jelzője.** A `0x00586d00` a `0x00581920` visszatérése után a `[ebp+0x13d]` bájtot állítja (`0x00586dba`). A `0x00586bd0` a `[edi+0x13c]` bájtot vizsgálja a `0x00580110` hívása előtt, majd sikeres írás után törli (`0x00586c31-0x00586c49`, `0x00586c9c`). A két eltérő eltolású bájt ezért nem azonos jelző. A `paszta.py`-val végzett teljes `.text`-átvizsgálás külön `+0x13c` és `+0x13d` hivatkozásokat is talált; a passz csak az eltolások elkülönülését erősíti meg, nem nevezi meg minden használatuk jelentését.
- **contacts.xml kiírás.** A `0x0041ba40` `this+0x2c5c` mezőjének nem nulla ágában állítja elő a `#contacts\` útvonalat, majd hívja a `0x00586bd0`-t (0x0041bb4f-0x0041bb7c). A `0x00586bd0` a kezelő `+0x13c` jelzőjét ellenőrzi, és csak nem nulla értéknél hívja a `0x00580110` írót (0x00586c31-0x00586c49); siker után törli a jelzőt (0x00586c9c). A `0x00580110` tényleges XML-kiírása a 35.10-ben dokumentált.
- **Hívási környezet.** Az index hat közvetlen `0x0041ba40`-hívót ad. A `0x00577a60` a `#db3\` útvonalat adja át, a visszatérés után pedig `IDS_DB_SAVED` értesítést állít elő (`0x00577a83`-`0x00577ae3`); ennek hívói `0x005cb990` és `0x005e60d0`. A `0x0041b020` külön, `Always Compact` beállítást is tartalmazó útján `#db3\` mellett hívja a közös rutint (`0x0041b28a`-`0x0041b29c`). Ez azt bizonyítja, hogy a közös rutint adatbázis-mentési értesítést adó és `Always Compact` ágat tartalmazó kód is eléri; a contacts-írás ezen belül továbbra is a `this+0x2c5c` és a piszkosjelző-feltételtől függ. A People OK utáni pontos eseményt ez nem nevezi meg.
- **Ami nem dőlt el.** A vizsgált bináris út nem nevezi meg, melyik felhasználói vagy életciklus-esemény hívja meg a `0x0041ba40`-et a People OK után, ezért nem állítom, hogy az írás OK-kor, bezáráskor vagy kilépéskor történik. NINCS MEG a fájlrendszeri időpont, valamint az OK/Choose, Cancel, bezárás és újraindítás közötti `contacts.xml`, `.picasa.ini` és db3 előtte/utána diff. A `0x00581920` sikeres backup.xml-visszaállítási ága külön a `0x00580110` írót hívja (0x00581bcb; 35.10); ez nem bizonyít People Manager-műveletet.

| Állítás | Forrás | Bizonyítottság |
|---|---|---|
| People OK validál, majd a módosított kontaktok mentési rutinját hívja | bináris (`0x007b99a0`, `0x007bb660`, `0x007baf50`; Ghidra-kimenet és utasításszintű út) | megerősített |
| A módosított kontakt kezelője piszkos jelzőt kap | bináris (`0x005849d0`, `0x00584a98`-`0x00584aa0`; Ghidra-kimenet és nyers diszasszemblálás) | megerősített |
| `.picasa.ini` `[Contacts2]` beolvasási út | bináris (`0x0045a9d0`, `0x00587110`, `0x005875d0`; Ghidra C, annotált diszasszemblálás és független string-/hívás-xref) | megerősített |
| A `contacts.xml` betöltésjelzője (`+0x13d`) és kiírási piszkos jelzője (`+0x13c`) eltérő bájt | bináris (`0x00586d00`, `0x00586bd0`; annotált diszasszemblálás és teljes `.text`-passz a `paszta.py`-val) | megerősített az eltolásokra; a mezők tágabb szemantikája feltételes |
| A piszkos jelzőhöz kötött út külön hívja a contacts.xml írót | bináris (`0x0041ba40`, `0x00586bd0`, `0x00580110`; utasítások és független indexelt hívókapcsolat) | megerősített |
| A közös persistence-rutint a `Database Saved` jelzésű és az `Always Compact` út is eléri | bináris (`0x00577a60`, `0x0041b020`; string-xref, hívó-xref, célzott diszasszemblálás) | megerősített az adott kódutakra |
| A People OK vagy `[Contacts2]`-visszaállítás után mikor változik lemezen a contacts.xml, és mit ír a művelet az ini/db3 fájlokba | NINCS MEG; Colab J8 profil-diff | nyitott |
| A Red.dll belső detektálási küszöbe és a `0x100057c0` callback tényleges célja | NINCS MEG; célzott callback-feltárás és J7 kontrollmérés | nyitott |

**A két független út.** A út: a Ghidra-függvénykimenet megmutatja a `.picasa.ini` `[Contacts2]` visszaállítását (`0x0045a9d0` → `0x00587110` → `0x005875d0`), a People OK → validálás/mentés → módosított sor → `0x005849d0` láncot, és a `0x00586bd0` jelzővizsgálatát. B út: a `annot_disasm.py` címtartományhoz kötött utasításai és az index külön string-/hívás-xrefje igazolja a `.picasa.ini` / `Contacts2` útvonalat; a teljes `.text`-passz (`paszta.py`, `memoria_kapu()` első műveletként) és a célzott nyers diszasszemblálás egymástól függetlenül mutatja, hogy a betöltő `+0x13d`-t, a kiíró pedig `+0x13c`-t használ. A két út egyezik. Az utasítás- és xref-adat a fájlútvonalakat rögzíti, de futásidejű fájlváltozási időpontot egyik sem ad.

**Cáfoló kísérlet és ellenőrzés.** Azt a feltevést próbáltam igazolni, hogy a People Manager OK közvetlenül kiírja a `contacts.xml`-t. Az OK mentési lánc utasításait követve a módosított sor a `0x005849d0`-hez jut, amely a memóriabeli jelzőket állítja; a vizsgált közvetlen OK-láncban nincs `0x00580110`-hívás. A kiíró külön `0x0041ba40` → `0x00586bd0` útját a jelzővizsgálat és a hívókapcsolatok is igazolják. Ez cáfolja a közvetlen OK-hívásláncban történő írást, de nem bizonyítja, hogy nincs más, az OK-val egyidejű esemény; a tényleges fájl-időzítés J8-cal nyitott.

Második cáfoló próbaként azt vizsgáltam, hogy a `contacts.xml` beolvasása utáni `+0x13d` bájt azonos-e a kiíró `+0x13c` piszkos jelzőjével. Az `annot_disasm.py` a `0x00586d00`-ban `+0x13d` írást, a `0x00586bd0`-ban `+0x13c` ellenőrzést/ürítést mutat; a `paszta.py`-passz mindkét eltolásra külön hivatkozásokat talált. Az azonosság feltevése így cáfolt, és a cáfolatot a két konkrét használat, valamint a teljes passz is ellenőrzi. A két bájt további szemantikája nyitott.

**A nyolc „Kész, ha” pont állapota.** Az 1-6. pont közül továbbra is csak a korábban megadott részeredmények állnak: mindegyikhez maradt fel nem mért eredeti művelet vagy profilhatás, ezért ⛔ részben. **7. Névforrások/időzítés: ⛔ részben**: a bináris contacts.xml olvasó-/íróút és a People OK piszkos jelzője megvan; a pontos lemezre írási idő, ini/db3 diff és a PicasaPy-eltérés még nincs lezárva (35.10, 35.12; J8). **8. Arcfelismerés: ⛔ részben**: a `0x10001570` státuszkód-kezelése és a `0x100057c0` pontszámgyűjtése megerősített (35.11), de a belső küszöb/callback, scan-indítás és kihagyás, valamint az eredeti felismerési eredmény nyitott (J7). A teljes jegy ezért továbbra is **nyitott**; a 35.3-ban szereplő nyolc pont mindegyike nincs teljesen igazolva.

**Következő lépések.** J8-ban külön eredeti profilpéldányon mentsd ki a `contacts.xml`, érintett `.picasa.ini` és db3 állapotát a People OK/Choose/Cancel előtt és után, alkalmazásbezáráskor, majd újraindítás után; rögzítsd a fájl-időbélyegeket is. J7-ben a `0x100057c0` által hívott virtuális `+0x40` callback célját kell feltárni, majd kontrollált arckészleten mérni. A `FRRecommendIncludeLimit=0,50` ettől elkülönülő ajánlásba-vételi szűrő marad.

### 35.13 2026-10-22-i célzott korrekció: a csempe automatikus kiegészítése és az Escape

**Hatókör.** A PicasaPy aktuális forrásverziója `0.9.187` (`pyproject.toml:13`). E körben csak a #5185 2. pont csempe-javaslat/Enter/Escape útját ellenőriztem újra; a forrásolvasat nem futásidejű PicasaPy-mérés. Az eredeti bináris állítások a 19.7-ben vannak részletesen, ez a szakasz az esemény- és vezérlőhatárt tisztázza.

| Eredeti | Nálunk (0.9.187 forrásolvasat) | Teendő |
|---|---|---|
| A `0x00809360` (`CAutoCompleteListBox` RTTI-vtábla `+0x14` slot) `param_2 == 0` ágán nincs elfogadó hívás; mindkét nem nulla `param_2` ág a `0x00a54b70` rutint hívja. A `param_2` jelentése nem bizonyított egérindexként, és a csempe popupjának ehhez a vezérlőhöz kapcsolása **NINCS MEG**. Csempe-Escape-re a `ytButtonNode` visszaadja a `0xf4241` „nem kezeltem” értéket; a szülő hatása nyitott (19.7). | A `UnnamedFacesView.qml:429-462, 611-698` névjegy-cache-ből képes/neves javaslatlistát készít; a sor kattintása a `submitName`-et hívja, akárcsak az Enter (`:580-588, 691-698`). A `Main.qml:3867-3869` mindkét jelet `nameFaceFromPanel(..., true)`-re köti, a `PeoplePanel.qml:196-210` pedig függő arcot rögzít és a People párbeszédet nyitja. Ez kizárólag jelenlegi PicasaPy-forrásút, nem az eredeti viselkedésre vonatkozó mérés. A csempemező `Keys.onPressed` kódja csak a fel/le nyilat kezeli (`UnnamedFacesView.qml:589-607`); a forrásból a fókusz utáni Escape-visszaállítás sem állapítható meg. | J2/job-164: a csempe javaslatsorra kattintás után rögzíts képkockát, `Unnamed`/személy sorszámot, People-ablakot, és hasonlítsd össze az érintett `[Contacts2]`/`faces=` sorokat. Külön fókuszált mezőben írd be a `Tes` előtagot, majd Escape; jegyezd fel, visszajön-e az `Add a name`, marad-e szöveg, változik-e a lista. Az Entert, a javaslatsorra kattintást és Escape-et külön lépésként mentsd. |

**A két független út.** A út: a `0x00809360` nyers utasításai a nullás és nem nulla `param_2` ágakat, valamint a `0x00a54b70` hívásait mutatják; a `0x00a645a7`-`0x00a64633` billentyűút Escape-kimenetét is utasításszinten követtem. B út: a 2026-10-22-i Ghidra-C ugyanazokat a `param_2` ágakat és hívásokat adja, az RTTI pedig a `0x00809360`-at a `CAutoCompleteListBox` `+0x14` slotjához köti; a 19.7 teljes `paszta.py`-passza és konstruktor-olvasata külön igazolja, hogy a csempe `[this+0x384]` Escape-értéke nulla. A bináris utak a vezérlő szintű ágelágazásban egyeznek, de egyik sem bizonyítja, hogy a csempe popup ezt a listavezérlőt használja.

**Cáfoló kísérlet és ellenőrzés.** Azt próbáltam cáfolni, hogy a `0x00809360` minden egérágon elfogad. A `param_2 == 0` ágon csak a bázisosztály `+0x08` slot fut, míg az elfogadó rutin csak a két nem nulla ágon jelenik meg; a Ghidra-C és az RTTI-azonosítás ezt külön ellenőrzi. Ez cáfolja a „minden kattintás elfogad” megfogalmazást. A másik feltevés, hogy a job-167 Escape a csempemezőt vizsgálta, a feladatban átadott lépéssor alapján cáfolt: az Escape a People ablak Search mezőjében történt. A csempe-mező szülőjének viselkedéséről egyik cáfoló próba sem ad adatot.

**Bizonyítottság.** A függvényágak és a `CAutoCompleteListBox` slotjainak kapcsolata **megerősített** (utasításolvasat + Ghidra-C/RTTI). Az eredeti csempe-popup bekötése, a javaslatra kattintás utáni arc-hozzárendelés/párbeszéd/listaállapot és a csempe-Escape szülői hatása **nyitott**; ezekhez Colab-felvétel kell.

### 35.14 2026-10-23-i utánkövetés: a mentési határ és a Red relációs objektum visszahívása

**Hatókör.** A 35.10-35.12 nyitott kérdéseit ellenőriztem újra a helyi Picasa 3.9.141.259 és Red.dll binárison, a 2026-10-22-i Ghidra-kimenetekkel, a 2026-10-23-i `2026-10-23-ghidra-sor-265-red.txt` kimenettel, a Red.dll célzott Capstone-dekódolásával és a Red RTTI-indexével. A `red.cfg`-t a csak olvasó parserrel vizsgáltam; a parser mindkét bemenet ismert SHA-256-át átengedte. Az aktuális munkafa forrásverziója 0.9.187 (`pyproject.toml:13`). Futó Picasa/PicasaPy és Colab-profilmérés most sem volt, ezért tényleges fájl-időbélyeget vagy élő UI-viselkedést nem állítok.

#### 7. Névforrások: mit ír le a bináris és mikor?

| Eredeti | Nálunk (0.9.187, forrásolvasat) | Teendő |
|---|---|---|
| A People Manager OK útja (`0x007b99a0` → validálás `0x007bb660` → mentés `0x007baf50`) a módosított névjegyet a memóriában frissíti; a `0x005849d0` beállítja a névjegy és a kezelő piszkos jelzőjét. A tényleges `contacts.xml` író a külön `0x0041ba40` → `0x00586bd0` útban fut; a második csak a `+0x13c` jelző beállított állapotában hívja a `0x00580110` írót. A `0x0041ba40` People OK utáni pontos eseménye és a fájl lemezre kerülésének ideje **NINCS MEG** (35.10, 35.12). | A `PeopleManagerDialog.qml:335-394` a commit során meghívja a `savePeopleManagerChanges`-t. A `people_controller.py:375-500` a módosult központi névjegyeket ugyanebben a hívásban `save_contacts_xml`-lel írja; a mappánkénti `.picasa.ini` frissítést később az `update_document` végzi (`:572`). Ez forrásolvasat, nem PicasaPy-futásmérés. | J8: külön eredeti profilban hasonlítsd össze a `contacts.xml`, az érintett `.picasa.ini`-k és a db3 tartalmát/időbélyegét OK/Choose, módosított mező utáni Cancel, párbeszédbezárás, alkalmazásbezárás és újraindítás előtt/után. Csak a mérés után dönthető el, hogy a PicasaPy az eredetihez képest túl korán vagy más fájlba ír-e. |

**A lehetséges azonnali írás cáfolata és határa.** A közvetlen People OK hívásláncban az utolsó bizonyított tárolási művelet a piszkos jelző beállítása a `0x005849d0`-ben; a `0x00580110` írót a külön `0x0041ba40`/`0x00586bd0` ág hívja. A Ghidra-híváslánc és a célzott utasításolvasat egyezik ebben. Ez cáfolja, hogy az OK-kezelő közvetlenül meghívja a központi XML-írót; **nem** zárja ki, hogy ugyanabban a felhasználói műveletben egy másik esemény vagy későbbi életciklus-hívás elindítja a mentést. Az utóbbihoz fájlrendszeri mérés kell.

#### 8. Arcfelismerés: a Red.dll callback második virtuális lépcsője

- A `0x100057c0` leírópáronként a `vtable+0x40` művelet pontszámai közül a maximumot írja a kimeneti tömbbe (`0x10005847`-`0x10005880`, `0x100058d2`-`0x100058d8`). A `0x10001570` a visszatérési `EAX` státuszkódot teszteli (`0x100015aa`), nem a float-pontszámot. Ezekben a két függvényben nincs végső küszöb-összehasonlítás; ez csak erre a két kódrészre vonatkozó negatív állítás.
- A Red RTTI-indexben a `vfr_SdkRelator::vftable` címe `0x101c656c`; a `+0x40` slotja `0x100a3a50`. A Ghidra C-kimenet és a közvetlen utasításolvasat szerint a `0x100a3a50` a `[ecx+0x10]` mezőre lép, majd annak `vtable+0x40` címére ugrik (`0x100a3a50`-`0x100a3a58`). A 2026-10-23-i Ghidra-kimenet egyetlen adathivatkozást sorol fel (`0x101c65ac`), közvetlen hívót nem, és a közvetett ugrás célját nem tudja visszanyerni; ezért ez egy további dinamikus virtuális hívás, nem küszöb-összehasonlítás, és a célosztály továbbra sem azonosított. **Utólagos pontosítás (52.5):** a helyi, hash-azonosított Red.dll+`red.cfg` párban a cél `vqc_Relator`; ez nem igazolja a 3.9-es futásidejű DLL-azonosságot, és nem adja meg a végső detektorküszöböt.
- Független osztály- és slotjelölt: a `vfr_FusedRelator::vftable` címe `0x101c7214`; a nyers `+0x40` bejegyzés `0x101c7254` értéke `0x100a8240`. Az indexelt sztring-xref a `0x101c70b0` literált a `0x100a8240` függvényhez köti: `virtual float vfr_FusedRelator::sim(const uint32* arr1A, int32 arr1SizeA, const uint32* arr2A, int32 arr2SizeA) const`. Ez azt bizonyítja, hogy a FusedRelator egyik `+0x40` megvalósítása tömbök hasonlósági pontszámát adja vissza; **nem** bizonyítja, hogy a `0x100a3a50` által futásidőben elért `[this+0x10]` objektum ilyen típusú. A `red.cfg` statikus leltára tartalmaz `vfr_SdkRelator` gyökeret (`0x22b08a` fájloffset), de a parser a modellobjektumok belső sémáját nem fejti vissza. Így a tényleges objektumpéldány, a dinamikus hívás célja és a végső küszöb **NINCS MEG**; a konfigurációban szereplő osztály önmagában nem bizonyítja, hogy ez az adott hívás objektuma.
- A Picasa EXE `FRRecommendIncludeLimit=0,50` összehasonlítása az ajánlási út szűrője (35.10), nem a `0x100057c0`-ban vagy `0x10001570`-ben mért detektorküszöb. A `red.cfg` `vfr_SowGrowStampClusterer` rekordjának `0.7` eleme (`0x22d07e` fájloffset) szintén nem azonosítható a keresett végső küszöbként: a parser csak a rekord osztályát és nyers payloadját azonosítja, a modellmezők szemantikáját nem.

| Eredeti | Nálunk (0.9.187, forrásolvasat) | Teendő |
|---|---|---|
| A `FRRecommendIncludeLimit=0,50` Picasa-oldali ajánlásba-vételi határ (35.10); ez nem a Red belső arcdetektálási küszöbe. A Red végső küszöbe, a scan indítási feltétele és a névvel jelölt fotó kihagyása **NINCS MEG**. | A YuNet-detektor alapértéke 0,9, a legnagyobb detektálási méret 960 px (`faces/detector.py:42,49`). A kereső kihagyja azt a képet, amelynek `.picasa.ini`-adata már azonosított arcot tartalmaz (`face_scan_controller.py:490-495, 1563-1568`). Ezek forrásállítások, nem futásidejű mérések. | J7: ugyanazon címkézett fotón külön próba név nélküli, már megnevezett és megnevezett + további névtelen arccal; mérd a scan indítását, a jelölteket és a fájl-/adatbázis-diffet. A Red callback küszöbéhez a fenti célzott Ghidra-kör szükséges. |

| Állítás | Forrás | Fok |
|---|---|---|
| A `0x100057c0` maximum pontszámot gyűjt; a `0x10001570` státuszt kezel | bináris (`0x100057c0`, `0x10001570`; Ghidra-C és célzott Capstone) | megerősített, a két függvényre korlátozva |
| `vfr_SdkRelator` `+0x40` slotja a dinamikus második lépcsőt megvalósító `0x100a3a50` átirányító függvény | bináris (`0x101c656c` RTTI-slot; `0x100a3a50`-`0x100a3a58` utasítások) | megerősített a slotra és a átirányító függvényre; futásidejű példány-hozzárendelés nyitott |
| `vfr_FusedRelator` `+0x40` megvalósításának szignatúrája `virtual float ...::sim(array, size, array, size)` | bináris (`0x101c7214` RTTI-vtábla, `0x101c7254` nyers slotérték, `0x101c70b0` a szignatúra-sztringre mutató hivatkozás → `0x100a8240`) | megerősített a slot-cél és a szignatúra azonosítására; a `vfr_SdkRelator` belső objektumához való futásidejű kötés NINCS MEG |
| Red.dll teljes felismerési küszöbe, a callback végső célja és a névvel jelölt fotó kihagyási szabálya | **NINCS MEG**; célzott Ghidra-kör és J7 Colab-felvétel kell | nyitott |

**A két független út.** A út: a Ghidra-kimenet a `0x100057c0` maximumképzését és a `0x10001570` státuszágát mutatja; ugyanebben a körben a `0x100a3a50` dekompilált törzse közvetett `+0x40` hívásként jelenik meg. B út: a célzott nyers Capstone-dekódolás a `0x100057c0`, `0x10001570` és `0x100a3a50` utasításait külön ellenőrzi; a Red.dll RTTI-index és a nyers vtable-adatok pedig egyeznek a `vfr_SdkRelator` átirányító slotjánál. A belső cél jelöltjére külön ellenőrző út a `vfr_FusedRelator` nyers `+0x40` slotja (`0x101c7254` → `0x100a8240`) és a függvényt azonosító a szignatúra-sztringre mutató hivatkozás (`0x101c70b0`). Ezek az utak egyeznek abban, hogy a vizsgált `0x100a3a50` csak közvetett virtuális továbbítást végez; **nem** bizonyítják, hogy a FusedRelator a tényleges futásidejű cél. A tényleges objektumpéldányt vagy annak küszöbét egyik út sem fedi fel.

**Cáfoló kísérlet és ellenőrzés.** A `0,50` Picasa-ajánlási határt, a `0,90` Preferences-értéket és a `red.cfg` `0,70` Stamp-rekordját próbáltam a keresett Red-végküszöbként azonosítani. A két Red-függvényben a float pontszám csak a kimeneti tömbbe kerül; a wrapper az `EAX` státuszt vizsgálja. A `0,50` külön Picasa-ajánlási szűrő, a `0,70` rekord pedig `vfr_SowGrowStampClusterer`-hez tartozik, ismeretlen modellmező-szemantikával. Külön cáfoló próbával azt is ellenőriztem, hogy a `vfr_FusedRelator` `+0x40` `sim` metódusa-e a futásidejű cél: a `0x100a3a50` csak a `[this+0x10]` objektum virtuális slotjára ugrik, a `red.cfg` parser nem adja meg ennek az objektumnak a típusát, ezért a hozzárendelést visszautasítottam mint nem bizonyítottat. A nyers `0x101c7254` slotérték és a `0x101c70b0` a szignatúra-sztringre mutató hivatkozás ellenőrzése a FusedRelator-metódus azonosítását alátámasztja, de a konkrét objektumkapcsolatot nem. Így a FusedRelator továbbra is csak runtime-céljelölt; a végső küszöböt nem ez az adat adja meg.

**Bizonyítottság és következő lépés.** A két vizsgált Red-függvény működése, valamint a `vfr_SdkRelator` vtable-slotjának átirányító függvénye **megerősített**. A teljes arcfelismerési küszöb, a callback tényleges példánya/célja és a Picasa-szkennelés futási/kihagyási feltétele **nyitott**; a teljes #5185 ezért **nyitott** marad. Nincs bizonyított PicasaPy-eltérés, amely önmagában kódmódosítást indokolna.

**Nyitott.**

- Ghidra-kör kell: 0x100a3a50: milyen konstruktor/bekötés állítja elő a `[this+0x10]` objektumot; mi a második `vtable+0x40` konkrét célosztálya és függvénye (különösen a `vfr_FusedRelator::sim`, `0x100a8240` jelölt); hol történik a pontszám végső küszöb-összehasonlítása? [blokkoló]
- J7 Colab-felvétel kell: azonos, címkézett képeken a keresés indítási pontja, névvel ellátott fotó kihagyása és az eredeti jelöltlista; rögzítsd a futó Preferences-értékeket is.
- J8 Colab-felvétel kell: `contacts.xml`, érintett `.picasa.ini`-k és db3 előtte/utána tartalma és időbélyege People OK/Choose, Cancel, bezárás és újraindítás után.

## 36. #5184, helyi Codex-kutatói kör: N1-N8 végállapot és Red.dll-cél (2026-10-20)

**Hatókör:** a jegy teljes kérdéslistájának összefoglalása a jelenlegi spec, a munkafa forrása, a helyi Picasa3.exe/Red.dll és a feladatban átadott job-186/job-187 leírásai alapján. A GitHubot nem használtam. A nyers job-186/job-187 képkockák és az eredeti futtatási profil nincsenek a munkafában vagy a célzottan leltározott mérőadat-archívumban, ezért a Colab-leírásokat nem állítom újraellenőrzött képi mérésnek.

### 36.1 A „Kész, ha” pontjai

| Pont | Állapot | Eredmény és bizonyíték |
|---|---|---|
| **N1** - talál-e további ismeretlen arcot egy névvel jelölt fotón | ⛔ **BLOKKOLT** | Az eredeti futás kimenete **NINCS MEG**. A vizsgált, sorba állító kód nem hasonlít nevet, de a felismerés utáni út tovább szűrhet (`0x0048ef20`, `0x0048af60`; 20-24. szakasz). A PicasaPy forrása kihagyja azt a fotót, amelynek ini-adatai között már azonosított arc van (`src/picasapy/app/face_scan_controller.py:470-475`). Döntő mérés: J7 B2 kontroll, azonos képet név nélkül már egyszer feldolgozva, majd névvel és második ismeretlen arccal. |
| **N3** - eredeti arány/küszöb a 960 px-es, 0,9-es YuNethez képest | ⛔ **BLOKKOLT** | Eredeti felismerési arány és 960 px-es bemeneti méret: **NINCS MEG**. A Preferences bináris alapértékei: `FRSuggestionThreshold=0,85` (`0x0048aabc`), `FRSuggestionSingleThreshold=0,90` (`0x0048ac6f`), `FRSortThreshold=0,85` (`0x0048acda`), `FRRecommendIncludeLimit=0,50` (`0x0048ad46`); az utóbbi a kép-futtató ajánlásba vételi szűrője, amely `0,50` floatot hasonlít (`0x0048e1f0`, `0x0048e33e`), nem bizonyított Red.dll-detektor-küszöb. Ezek neve és szerepe alapján sem igazolt, hogy azonos skálán vannak a feladatban megadott YuNet `0,9`-cel. A Picasa3.exe `0x006cde50` a Red.dll objektum `+0x44` slotját hívja (29.4); a Red.dll PE-táblája a `REDENTRY` exportot `0x10001930`-ra (RVA `0x00001930`) teszi. Az export a `0x1021ae7c` objektumot adja; annak vtable-je `0x101aadc4`, a `+0x44` bejegyzés `0x10001570`, amely a `0x100057c0` belső függvényhez delegál. Ez a híd megerősíti a hívási célt, de a Red.dll belső méretezési és döntési küszöbét, valamint az eredeti arányt nem. |
| **N4** - látszik-e alapból keret és név | ✅ **LEZÁRVA** | A job-187 átadott mérése szerint a megnevezett arcon alapból sem keret, sem név nem látszik. A PicasaPy nézőjében `facesVisible: false`, és a mentett régiók megjelenítése ehhez kötött (`PhotoViewer.qml:354, 3643-3658`; `FacesOverlay.qml:20-22, 78-106`), tehát a két oldal egyezik. A nyers job-187 kép helyben nem érhető el; a mérési állítás forrása a feladatban átadott jegyzet. |
| **N5** - személyszintű mellőzés útja és hatása az arcokra | ⛔ **BLOKKOLT** | A binárisban a megerősítő szöveg „move this person to the ignored people album” (`0x00c99830`), de a személyszintű művelet tárolóírása és az érintett arcok `faces=`-hatása **NINCS MEG**. A fejlécsáv `ignore` útjának (`0x005c9b00` → `0x00449090`) eredményét nem szabad automatikusan azonosítani ezzel a személykezelő-művelettel (24.3, 28.4/a). |
| **N6** - személy törlése és az arcok hatása | ⛔ **BLOKKOLT** | A `0x007ba820` a megerősítés után egy aktív sort kezel; feltételesen hívja a `0x005836f0`-t, majd a `0x00584cc0`-t, végül eltávolítja a sort a felületi listából (20.4). A `[Contacts2]` tartós írásának időzítése és a törölt személyhez tartozó `faces=` sorok sorsa **NINCS MEG** (32.6). |
| **N7** - egy vagy több kijelölés | ⛔ **RÉSZBEN BLOKKOLT** | A Név nélküliek többes kijelölése megerősített: a job-180 Ctrl+A után hat arcot jelölt ki, és a bináris kijelölt-listát jár be (20.5). A Személykezelő egyszeres/többszörös modellje **NINCS MEG**: a `contactmgr.fen` listaeleme nem ad kijelölési módot, a job-186 egy kiválasztott sort mutat; egyik sem próbálja ki a második sor Ctrl-kattintását. A döntő, kockázatmentes J6 próba: sor 1, majd Ctrl+kattintás a 2. sorra, képkocka és Delete Person állapotának rögzítése. |
| **N8** - referencia-képernyőkép a Személykezelőről | ✅ **LEZÁRVA** | A feladatban átadott job-186, 24. kép leírása rögzíti a 631×351 People ablakot: balra üres Search mező, egyedüli és kijelölt „Teszt Elek” sor, Delete Person/New Person; jobbra arckép, „1 Photo in Picasa”, Name/Email(s), szürke Sync Face Tags/Revert; alul szürke Manage Online Contacts/Refresh Contacts, OK és Cancel. A `.fen` erőforrás és a régebbi helyi People-képkocka az elrendezést/vezérlőket külön is alátámasztja, de az utóbbi üres listás, ezért nem bizonyítja az aktív sor vagy méret részletét. A job-186 nyers képkocka helyben nincs. |

### 36.2 Bizonyítottsági fok, két út és cáfoló kör

**Összesített fok: feltételes.** N4 és N8 lezárható a megadott mérési jegyzetekkel. A Red.dll `+0x44` célja cím szerint feltárt, de N3 lényege (eredeti méret, detektálási küszöb és arány) nyitott. N1, N5, N6 és a N7 Személykezelő-ága szintén nyitott; ezért a jegy „Kész, ha” feltételei nem teljesültek.

- **A út - bináris és erőforrás:** a Picasa3.exe `0x006cde50` hívása a Red.dll `+0x44` slotjára, a Red.dll export/vtable PE-adatai és a `0x10001570` diszasszemblálása azonos hívási célt ad. A `contactmgr.fen` csak a lista-vezérlőt írja le; kijelölési mód nincs benne.
- **B út - felvételi jegyzet és külön réteg:** a job-187 N4-leírását a PicasaPy QML alapállapotával vetettem össze; a job-186 N8-leírásának vezérlőit a `.fen` és a másik állapotú helyi képkocka ellenőrzi. Egyezés csak a megfigyelt N4 alapállapotára és az N8 elrendezési elemeire áll; a felvételek képi részleteit nem ellenőriztem újra.
- **Cáfoló próba (N3):** megpróbáltam igazolni, hogy a gyári `0,90` az eredeti arcdetektor küszöbe. A `FRSuggestionSingleThreshold` 90-es gyári értékét a `0x0048ac6f` olvassa, míg a kép-futtató a `FRRecommendIncludeLimit` mezőt (`0,50`) hasonlítja (`0x0048e33e`). Ez megcáfolja a `0,90 = YuNet score threshold` azonosságot, de nem adja meg a Red.dll saját döntési skáláját. A cáfolat ugyanazon bináris bizonyítékrenddel ellenőrzött; az eredeti skála továbbra is **NINCS MEG**.
- **Cáfoló próba (N7):** ellenőriztem azt a következtetést, hogy a `0x007ba820` egy aktív sort olvas, tehát a lista szükségképpen egyszeres kijelölésű. A job-186 egy sora, a törlési kezelő egy sorra épülő útja és a `contactmgr.fen` hiányzó módjelzője nem zárja ki, hogy Ctrl-kattintáskor több sor kijelölhető legyen. A hipotézis nem áll meg: N7 nyitva marad.
- **Cáfoló próba (N1):** a sorba állító függvényekben kerestem név-összehasonlítást; a vizsgált út nem ad ilyet. Ez nem cáfolja, hogy a felismerés utáni lépés szűrhet, tehát az eredeti runtime kimenet nélkül nem zárja le N1-et.

### 36.3 Eredeti / nálunk / teendő

| Kérdés | Eredeti | Nálunk | Teendő |
|---|---|---|---|
| N1 | NINCS MEG, hogy névvel jelölt fotón talál-e másik arcot. | A forrás a már azonosított arcot tartalmazó fotót kihagyja (`face_scan_controller.py:470-475`). | J7 B2 kontroll. Csak igazolt eredeti eltérés után készüljön fejlesztői lista. |
| N3 | A Preferences értékek és a Picasa EXE `0,50` szűrője binárisból megvan; a Red.dll tényleges méretezése, belső küszöbe és felismerési aránya NINCS MEG. | A feladatban megadott és a forrásban rögzített referencia a YuNet 960 px / 0,9 (`detector.py:42,49`); ez nem igazoltan azonos skálájú az eredeti értékekkel. | J7: kontrollált méret- és küszöbpróba, azonos képkészlettel és eredménylistával; a Red.dll függvénylánc célzott Ghidra-köre. |
| N4 | Alapból nincs keret és név (job-187 jegyzet). | A mentett arcok láthatósága alapból ki van kapcsolva. | Nincs igazolt eltérés, nincs fejlesztői feladat. |
| N5 | A személyszintű írás és az arcokra gyakorolt hatás NINCS MEG. | Az eredeti művelettel való élő összevetést nem végeztem el. | J4: személyszintű Ignore Person előtt/után `faces=`, `[Contacts2]`, ignored album; külön a névtelen és nevezett arc. |
| N6 | A sor eltávolításának memóriabeli útja ismert; tartós mentés és arc-hatás NINCS MEG. | Az eredeti viselkedéssel való élő összevetés nincs megmérve. | J5/J8: Delete Person előtt/után és bezárás/újraindítás után `.picasa.ini`, `contacts.xml`, db3 diff. |
| N7 | A Név nélküliek többes kijelölése megvan; People Manager kijelölése NINCS MEG. | QML-forrás szerint egy `currentIndex`-et választ; PicasaPy futásidejű összevetés nem készült. | J6 Ctrl-kattintásos sorpróba, majd kijelölés és Delete Person állapota. |
| N8 | A job-186 referencia leírása megvan; a nyers képkocka helyben nincs. | Kód- és élő képernyő-összevetés nem készült ebben a körben. | A referenciát a People Manager vizuális auditjának mércéjeként kell használni; eltérésből külön UI-fejlesztési jegy csak képi összevetés után adható. |

**Fejlesztési következmény:** jelenleg nincs olyan N-pont, ahol a mért eredeti viselkedés igazolt eltérést mutatna a PicasaPy-tól. Ezért nincs Codex-kész fejlesztői lista és nem javaslok kódmódosító jegyet. A következő munkák bizonyítékgyűjtések: J4, J5/J8, J6 és J7/B2. Nincs új, külön kutatási jegy; ezek a #5184 nyitott részei.

### 36.4 Nyitott

**Ghidra-kör kell:** 0x100057c0 - a Red.dll `REDENTRY` `+0x44` hívási láncában a detektor tényleges bemeneti mérete, pontszám-skálája és döntési küszöbe [blokkoló]

**22. kör, N5 (`0x00448fb0`): a függvény olvasó, a tábla írói és a 64 bites érték jelentése NINCS MEG.** A C-törzs (`.ghidra/2026-10-20-ghidra-22.txt`, 1-66. sor) zárolja a `this` objektumot (a `this+0x2768` tulajdonos-szál, a `this+0x276c` számláló, a `this+0x2754` jelző szerint a `this+0x2748` objektum `+0x18` slotja vagy a `this+0x2770` kritikus szakasz). Utána a `this+0x27a0` fejlécből (`+0x4c >> 1` darabszám, `+0x48` 8 bájtos elemek) a `param_1`-edik elemet adja a `param_2`-be, és 0-t ad vissza. Ha az index kívül van, a `this+0x27a8` és `+0x27ac` alapértéket adja, és 4-et.
- **Bizonyítottsági fok.** A törzs: **megerősített** (C, egy út). A tábla írói és a jelentés: **NINCS MEG**. A törzsben nincs írás a táblába, tehát a predikátum tábla-írója nem ez a függvény (cáfoló kísérlet, megerősített).
- **Lezárás (N5): (c), Ghidra-cím nélkül.** A közvetlen `0x27a0` keresés üres, mert a függvény bázis-eltolt hozzáférést használ (`esi = this+0x2748`), az írók ugyanígy érhetők el. A következő lépés a `[esi+0x58]` alakú írók pásztázása a teljes `.text`-ben, `paszta.py` kapuval (`memoria_kapu()` első művelet). Ha a személy-predikátum futásidejű listából jön, az N5 Colab-méréssel dől el. [blokkoló]

**22. kör, N6 (`0x0045a9d0`): a `.picasa.ini` ág és a hívási lánc feltárva; a `[Contacts2]` írója nincs meg.** A C-törzs (`.ghidra/2026-10-20-ghidra-22.txt`, 67-897. sor; a `.picasa.ini` ág a 680-730. sor). Ha a `this+0x2c5c` (a `0x00587110` első argumentuma, jelentése NINCS MEG) nem nulla, a `FUN_00410610` a `.picasa.ini` nevet állítja elő, és a 8 bájtos elemeket sorban a `FUN_00587110`-nek adja. Az a pár kimarad, amelynek mindkét dword-je `0xffffffff`. A 30. szakasz szerint a `0x00587110` olvasó, nem a kiíró. A törzs `-1`-gyel térhet vissza, ha a `FUN_004edf60(this+0xf8, ...)` nem nulla, vagy a `cStack_77` nulla.
- **Hívási lánc (megerősített, C, egy út).** A `0x0045a9d0` hívottjai között nincs `0x0068c030` (a HÍVOTTAK fejléc), tehát ez a függvény közvetlenül nem ír az INI-be. Egyetlen hívója a `0x0047e77e` (a `0x0047e470`-ben).
- **Bizonyítottsági fok.** A hívottak listája és a `.picasa.ini` ág: **megerősített**. A kiíró és a szakasznév (`[Contacts2]`): **NINCS MEG**. Az időzítés: **NINCS MEG** (a hívó nincs dekompilálva). A 8 bájtos elemek forrása: **NINCS MEG**; alakjuk megegyezik a `0x00448fb0` 64 bites elemeivel, ez azonos listát nem bizonyít.
- **Cáfoló kísérlet.** Feltételeztem, hogy ez az ág írja a `[Contacts2]` szakaszt: cáfolva (olvasó hívás, a `0x0068c030` nincs a hívottak között).
- **Lezárás (N6): (c).** A 2026-10-20-i bináris körben a `0x0047e470` és a `0x006956d0` kérdésére válasz született, lásd alább. A maradó Ghidra-címek a szakasz végén vannak.

**Válasz (2026-10-20): a `0x0047e470` hívási lánca és a mentés.**
- **Hívási lánc.** A `0x0045a9d0` egyetlen hívója a `0x0047e470` (hívási hely: `0x0047e77e`). A `0x0047e470` egyetlen hívója a `0x006a10b0` (`0x006a12da`). A `0x006a10b0`-t a `0x006a1350` hívja három helyen (`0x006a14cd`, `0x006a193c`, `0x006a1972`), és a `0x006a1350`-nek nincs közvetlen hívója az indexben.
- **Korrekció.** A korábbi `0x006a12fa` és `0x006a1332` címek nem a `0x006a10b0` hívói: a `0x006a10b0` belsejében lévő `call 0x00414940` helyek.
- **Mentés.** A mentő `0x0069b240` közvetlen hívója csak a `0x00692210`, aminek nincs közvetlen hívója. A `0x0047e470` és a `0x0045a9d0` hívottjai között nincs `0x0069b240`. Mikor fut a mentés: NINCS MEG.
- **Személytörlés után.** A törlési függvények (`0x007ba820`, `0x007b9630`, `0x007ba060`) lefelé 6 szinten sem érik el a `0x0047e470`-t és a `0x0045a9d0`-t. A `0x0047e470` felfelé bejárása a `0x006a1350`-nál áll meg, mert az nem hívott. A törlés utáni futás tehát közvetett hívásra épül: NINCS MEG.

**Válasz (2026-10-20): a `0x006956d0` és a `Contacts2`.** Részben igen: a hívási lánc eljut a `Contacts2` sztringig. Hogy a `0x00586e20` ténylegesen kiírja-e a szakaszt, még nyitott.
- `0x006956d0` a `0x0068c030`-at csak akkor hívja (`0x00697557`), ha a `[esp+0x1b]` bájt 2 (`cmp byte ptr [esp + 0x1b], 2`, `0x00697540`). A 2-es értéket a `0x00696d36` írja, a `0x0068ac80` hívás után, a `cmp al, 1` (`0x00696d0e`) ágon. Az `al` bemenete NINCS MEG.
- `0x0068c030` (654 bájt) az INI-fájlt IAT-hívással nyitja (`push 0xc0000000`, `0x0068c060`-`0x0068c068`). A bejegyzés-ciklus után (a visszaugrás `0x0068c212`-nél van) hívja a `0x0068ac20`-at (`0x0068c225`).
- A `0x0068ac20` hívja a `0x00586e20`-at (`0x0068ac5a`), a `0x00586e20` pedig a `Contacts2` sztringet tolja (`push 0xc9105c`, `0x00586e52`).
- A `0x0069b240` mentés is hívja a `0x0068c030`-at, tehát a mentés is ide jut.
- A `0x006956d0` törzsében magában nincs `Contacts2` sztring (`string_xrefs`).
- **Nyitott:** a `0x00586e20` belső ága. Hogy a sorokat kiírja-e, vagy csak nevet állít elő és olvas, NINCS MEG. Ez összhangban van a 28.3/a helyesbítéssel: a 27.1 "nem író" olvasata nem áll.

Ghidra-kör kell: 0x00586e20 - a `Contacts2` tolása után a `0x00985ff0`, `0x0040eef0`, `0x005863f0` és a `call edx` ág: mit ír a fájlba [blokkoló]
Ghidra-kör kell: 0x0068ac20 - a `0x0069ceb0` két hívása és a `0x00586e20` hívás feltétele (szakasz-fejléc vagy sorok) [blokkoló]
Ghidra-kör kell: 0x006a1350 - ki hívja közvetve (vtábla-slot vagy táblázat), és a három hívási hely (`0x006a14cd`, `0x006a193c`, `0x006a1972`) mikor fut: betöltés, mentés vagy törlés után [blokkoló]
Ghidra-kör eredménye (2026-10-21): a `0x00692210` az `AlignedImageCollection` és a `PrepareCollection` vtable-jének közös 27. slotja; a People Manager `Delete Person` utáni közvetett futása NINCS MEG. Lásd a 41. szakaszt. Következő cél: a `0x00584cc0` és `0x005836f0` törlés utáni virtuális hívási útja.

**22. kör, N6 (`0x007b81e0`, a Choose-callback): nem ír közvetlenül a `Contacts2`-be.** A törzs (`.ghidra/2026-10-20-ghidra-22.txt`, 898-1152. sor): ha a `param_1[0x57]` jelző be van kapcsolva, és a kiválasztott név mutatói (`param_1[0x54]`, `param_1[0x55]`) egyeznek a tároltakkal, a `ContactManagerDlg::OK` kulcs szövegét, különben a `ContactManagerDlg::Choose` kulcs szövegét adja a `piVar7` objektum `+0x68` slotjának. **Javítva (2026-10-21, #5437):** ez nem naplóüzenet, hanem az OK-gomb feliratának beállítása (38.7 szakasz). A törzsben nincs `0x00586e20` és nincs `0x00587110` hívás.
- **Bizonyítottsági fok.** A közvetlen hívási lista: **megerősített** (C). A `+0x68` slot célja és a hívottak (`0x00588460`, `0x005c2100`, `0x005c7620`, `0x007b8d20`) szerepe: **NINCS MEG**. A közvetett írás kizárva nincs.
- **Lezárás (N6): (c).** Következő Ghidra-címek: `0x00586e20` (a 27. szakasz szerint nem a `Contacts2` írója; a kiíró kérdése ezért a `0x006956d0` láncon marad) és a két hívó, `0x007b9630` és `0x007ba060`, amelyek a Choose-ágat kiváltják [blokkoló]. (Frissítés, 23. kör: a két hívó megvan, lásd a 37. szakaszt.)
- **Kész, ha (#5184, N5 és N6).** ⛔ Nem teljesül: N5 és N6 továbbra is nyitott; a feltárt részek (olvasó, hívási lánc, Choose-ág) a spec-lapon vannak, az eltéréshez nincs mért különbség, ezért nincs fejlesztői lista.

**Colab-mérés kell:** J7 B2 (N1); Red.dll összehasonlító próba és eredménylista (N3); személyszintű Ignore Person ini- és album-összevetés (N5); törlés utáni, bezárás utáni és újraindítás utáni mentés összevetése (N6); J6 Ctrl-kijelölés (N7). A mérőadat-archívum célzott taglistájában ehhez a feladathoz nem volt mérési csomag, ezért nem bontottam ki és nem hoztam létre ideiglenes `.bt` fájlt.

## 37. #5184, 23. kör (2026-10-20): a Choose-hívók, az INI-kiírás időzítése és a Colab-javaslat

**Hatókör:** az N6 második fele: a `0x007b9630` és a `0x007ba060` (a Choose-ág két hívója), és hogy a `[Contacts2]` mikor íródik törlés után. Forrás: `.ghidra/2026-10-20-ghidra-23.txt` (C, 1191-1687. sor). Diszasszembly ehhez nem készült.

### 37.1 A két függvény (C, megerősített)

- `0x007b9630` (`thiscall`; `param_1` a személykezelő állapota, `param_2` a vezérlő nevének sztringje, `param_3` az értékforrás objektum, vtábla-hívással olvasott értékkel). A kulcsnév szerint ágazik: `contacts`, `fullname`, `emails`, `sync`, `search`. A `contacts` ágban a kijelölt sor (`param_1+0x80`) frissül, a `search` ágban a `0x007b7f00` hívódik (a szűrés szó nem bizonyított). Az ágak végén közös záró rész van: a kijelölt sor jelző bájtja (`this+0x78` + index) `|= 1`, a vezérlő szövege frissül. Mindkét ágban hívja a `0x007b81e0`-t (Choose).
- `0x007ba060` (`0x007ba060(char param_1)`): listaújraépítés. Várakozik a `DAT_00d689cc` eseményre (5000 ms), nullázza a jelzőtömböt (`_memset`), visszaállítja a kijelölést a függőben tartott kulcspárral (`this+0x148`, `+0x14c` → `this+0x13c`), végül hívja a `0x007b81e0`-t. INI-író hívás nincs benne.
- Hívóik: a `0x007b9630` egyetlen hivatkozása adatreferencia (`0x00cb7bd4`, visszahívás-tábla). A `0x007ba060`-t a `0x007b93c0` (`0x007b95ff`) és a `0x007b9f20` (`0x007b9fdb`) hívja.

### 37.2 Bizonyítottsági fok

- Mindkét függvény hívja a `0x007b81e0`-t (Choose): **megerősített** (C, 1422., 1453. és 1664. sor).
- A `0x007b9630` visszahívás-táblából hívódik (`0x00cb7bd4`): **megerősített** (index). A tábla tulajdonosa: **NINCS MEG**.
- A `[Contacts2]` kiírásának pillanata (törlés, Choose vagy bezárás): **NINCS MEG**. Futásidejű adat.

### 37.3 Cáfoló kísérlet

- Feltételeztem, hogy a `0x007b9630` vagy a `0x007ba060` közvetlenül írja a `[Contacts2]`-t: cáfolva a közvetlen hívási listán (nincs `0x00586e20`, `0x0068c030`, `0x0069b240`, `0x0045a9d0`). A vtábla-hívások (`+0x18`, `+0x48`, `+0xf8`) célja nincs megnevezve, ezért a közvetett írás nem zárható ki teljesen.

### 37.4 Lezárás (N6 időzítés): Colab-felvétel

Az időzítés futásidejű adat, a binárisból nem dönthető el. Javasolt felvétel (a `behavior` típusú feladatot a tulajdonos `jovahagyva` címkéjével lehet indítani):

1. Új, üres mappa két képpel, az egyik a „Teszt Elek” személlyel (a job-186/187 mappája: `PicasaTeszt`).
2. A `.picasa.ini` másolata az első lépés előtt, és másodpercenként összevetés a fájllal.
3. Eszközök ▸ Személykezelő: a személy kijelölése, majd a Choose művelet. Az összevetés rögzíti, megjelenik-e azonnal a `[Contacts2]` sor.
4. „Delete Person”: összevetés újra; majd a Személykezelő bezárása (OK), és az összevetés újra.
5. Eredmény: három időpont (Choose, törlés, bezárás), ahol a `[Contacts2]` sor megjelenik vagy eltűnik. Ez dönti el az N6 időzítését.

A (c) lépés helyett ez a felvétel javasolt, mert a kérdés futásidejű. A statikus rész (a két hívó) nem blokkoló.

### 37.5 Kész, ha (#5184, N6 időzítés)

- ⛔ Nem teljesül: az időzítés (törlés, Choose vagy bezárás) nincs mérve. A hívási út részben feltárt (37.1), a kiírás pillanata nyitott.

**Megválaszolva (24. kör, 37.6):** a `0x007b9f20` nem a személytörlés útja, lásd 37.6.

### 37.6 24. kör (2026-10-20, #5184): a `0x007b9f20` nem a személytörlés útja

**Kérdés.** A `0x007ba060` egyik hívója (`0x007b9fdb`, a `0x007b9f20`-ban): a személytörlés után fut-e a lista-újraépítés, és hívja-e a `0x0045a9d0`-t (N6).

**Forrás.** `.ghidra/2026-10-20-ghidra-24.txt` (C, a `0x007b9f20` törzse); `.ghidra/2026-10-20-ghidra-23.txt` (a `0x007ba060` fejléce és törzse); a bináris-index HÍVÓK- és HÍVOTTAK-listái; a PE-olvasat: a `0x00cb7ba8` címen a dword `0x007b9f20`.

**Mit csinál a `0x007b9f20`.**
1. A `0x00985ff0("refresh_contacts")` sztringgel indul.
2. A `0x009b37a0` eredménye `-1`, és a `0x007a4770` eredménye `0`, akkor a jelző magas bájtja 1.
3. Ha a jelző 1: a `this+0x68` objektum `+0x54` slotját hívja 0-val, újra a `refresh_contacts` sztringgel, a `this` `+0x114` slotját, majd `0x007ba060((char)this[0x57])`-t.

Ez a „Névjegyek frissítése” (Refresh Contacts) ág, nem törlés. A `0x0045a9d0` nincs a törzsben.

**A `0x007ba060`.** Két hívója van: `0x007b93c0` (`0x007b95ff`) és `0x007b9f20` (`0x007b9fdb`). A törzse (C, 37.1): várakozik a `DAT_00d689cc` eseményre, nullázza a jelzőtömböt, visszaállítja a kijelölést, és hívja a `0x007b81e0` Choose-t. A lista-újraépítés tehát ebben a függvényben van, nem a hívóban.

**Hívja-e a `0x0045a9d0`-t?** A `0x007ba060` és a `0x007b9f20` HÍVOTTAK-listájában (index) nincs `0x0045a9d0`. Ez az indexből származó negatív állítás: a közvetlen `call` kizárható, a vtábla-hívás nem zárható ki (az index azt nem látja), és a `0x007b81e0` vagy a `0x007b44e0` közvetett útja sincs kizárva.

**Bizonyítottsági fok.**
- A `0x007b9f20` ágai és a `refresh_contacts` sztring: **megerősített** (C, egy út).
- Hogy ez nem a törlés útja: **feltételes** (a sztring és a hívásláncok alapján; a `0x00cb7ba8` tábla tulajdonos-osztálya NINCS MEG).
- A `0x0045a9d0` hívása: **NINCS MEG** (közvetett út nincs kizárva).

**Cáfoló kísérletek.**
1. „A `0x007b9f20` a törlés után fut”: a sztring és az ág alapján nem igazolódik; ez feltételes állítás.
2. „A `0x007ba060` közvetlenül hívja a `0x0045a9d0`-t”: az index szerint nem, vtábla-hívásra nem zárható ki.

**Lezárás (#5184, 24. kör): (c).** A személytörlés útja feltehetően a `0x007b93c0` (a `0x007ba060` másik hívója); ez nincs a dumpban. Az időzítés (37.4) továbbra is Colab-felvétel. Következő Ghidra-cím:

### 37.7 25. kör (2026-10-20, #5184): a `0x007b93c0` a Névjegyek frissítése, a törlés a `0x007b99a0` `delete` ága

**Kérdés.** A 37.6 kérdése: a `0x007b93c0` a személytörlés útja-e; fut-e utána lista-újraépítés; hívja-e a `0x0045a9d0`-t (N6).

**Forrás.** `.ghidra/2026-10-20-ghidra-25.txt` (C, a `0x007b93c0` törzse); `.ghidra/2026-10-20-ghidra-23.txt` (a `0x007ba060` törzse); `referencia/ghidra/2026-10-17-szemelykezeles-4.txt` (a `0x007b99a0` C-törzse); a bináris-index `functions`, `xrefs`, `string_xrefs`, `rtti` és `data_symbols` táblája.

**1. A `0x007b93c0` a Névjegyek frissítése, nem a törlés (megerősített).**
- Vtábla: a 25. dump DATA-hivatkozása `0x00cb7a7c`; ez a `ContactManagerDlg::vftable` (`0x00cb7a54`) 10. slotja (`0x28`). Az index rtti-listája is ezt mutatja.
- Sztring (index `string_xrefs`): a `refresh_contacts` a `0x007b93c0`, a `0x007b99a0` és a `0x007b9f20` törzsében van; a `delete` csak a `0x007b81e0` és a `0x007b99a0` törzsében. A `0x007b93c0`-ban nincs `delete`.
- Lista-újraépítés: `0x007b93c0` → `0x007ba060` (hívóhely `0x007b95ff`). Ez ugyanaz a lista-újraépítő, amelyet a 37.6 `0x007b9f20` ága hív. A `0x007ba060` közvetlen hívottjai között nincs `0x0045a9d0`, a `0x007b93c0` közvetlen hívottjai között sincs.

**2. A törlés útja: a `0x007b99a0` `delete` ága (megerősített, C).** A `0x007b99a0` a `ContactManagerDlg` vtábla 82. slotja (DATA-hivatkozás `0x00cb7b9c`; `0x00cb7b9c - 0x00cb7a54 = 0x148`; az index rtti-listája csak 64 elemet tart, ezért a slotot a címből számoltam). A parancs-sztring (`param_2+0x40`) `delete` összevetése után közvetlenül meghívja a `0x007ba820`-t, és visszatér. Az ágban más hívás nincs.
- A `0x007ba820` közvetlen hívottjai (index, 25 cím): `0x005836f0` és `0x00584cc0` (a memóriabeli kötés bontása, 21.5), `0x0051a120`, `0x009ae560` (6×), `0x00926c20` stb. Köztük nincs `0x007ba060` és nincs `0x0045a9d0`. A `0x007ba820` egyetlen hívója a `0x007b99a0`.

**3. Bejárás az indexben (feltételes).** A `0x007ba820`-ból három szintig 147 függvény érhető el; ezek között nincs `0x007ba060` és `0x0045a9d0`. A `0x007b93c0`-ból a `0x007ba060` egy szinten van, a `0x0045a9d0` három szinten sincs. A vtábla-hívásokat az index nem látja, ezért a negatív állítás csak a közvetlen hívási szintre áll.

**Válasz a kérdésre.**
- A személytörlés után a `0x007b99a0` a `delete` ágban közvetlenül visszatér: lista-újraépítés a törlés ágában nincs (megerősített).
- A `0x0045a9d0` nincs a törlés közvetlen hívási láncában (feltételes).
- Ha a törlés után lista-újraépítés fut, az a `0x007b99a0` hívójának (a parancs-szétosztónak) az ágában lehet. Ennek hívója nincs az indexben.

**Index-ellenőrzés (eltérés, nincs eldöntve).** A `0x0045a9d0` közvetlen hívóinak egyetlen `call` éle van az indexben: a `0x0047e470` (amelyet a `0x006a10b0` hív). A 21.5 szakasz szerinti `0x00587110` → `0x0045a9d0` hívás nincs meg az indexben: a `0x00587110`-nek 16 hívása van, egyik sem a `0x0045a9d0`. A 21.5 állítást újra kell nézni.

**Cáfoló kísérletek.** (1) „A `0x007b93c0` a személytörlés": cáfolva, nincs `delete` sztring és nincs `0x007ba820`-hívás benne. (2) „A törlés után a `0x007ba060` fut": cáfolva a közvetlen hívási szinten. (3) „A `0x007b93c0` hívja a `0x0045a9d0`-t": cáfolva az indexben (nincs él, három szinten sem).

**Bizonyítottsági fok.** A `0x007b93c0` a Névjegyek frissítése: megerősített (vtábla-slot és sztring-hivatkozás). A törlési ág hívásai: megerősített (C). A lista-újraépítés hiánya a törlés után és a `0x0045a9d0` hiánya: feltételes.

**Lezárás (N6, 25. kör): (c).** A kérdés a `0x007b99a0` hívójáig vezet. A 26. körben a hívó azonosítva (`0x007b9ff0`), a törlés utáni lista-újraépítés nincs benne; a `0x007b9ff0` közvetett hívója NINCS MEG (lásd 37.8).

### 37.8 26. kör (2026-10-20, #5184): a törlés hívója a `0x007b9ff0`, a törlés után nincs lista-újraépítés benne

**Kérdés.** A 37.7 N6 pontja: a törlés utáni lista-újraépítés útja. A 37.7 feltevése: a hívó a `call [reg+0x148]` parancs-szétosztó.

**Pásztázás (bináris, megerősített).** A 4.7/c szerinti `.bt/pasztazas.py` menettel. `call dword ptr [reg+0x148]`: **0 találat**. `mov reg, dword ptr [obj+0x148]` + `call reg`: **3 találat**: `0x007ba056` (a `0x007b9ff0`-ban), `0x008d580f` (a `0x008d57c0`-ban), `0x008df00d` (a `0x008def90`-ban). A `+0x190` (vtábla-slot 100) forma: **0 találat**.

**1. A `0x007ba056` a törlés hívója (megerősített).** A `0x007b9ff0` (111 bájt) a `ContactManagerDlg` vtábla 100. slotja (`0x00cb7be4`, PE-olvasat: `0x007b9ff0`). Asm: `0x007ba049 mov eax,[esi]`, `0x007ba04b mov edx,[eax+0x148]`, `0x007ba051 push 0`, `0x007ba053 push ebx`, `0x007ba054 mov ecx,esi`, `0x007ba056 call edx`. A vtábla `+0x148` slotja (`0x00cb7b9c`) `0x007b99a0`-t tartalmaz (PE-olvasat). Tehát a hívás a `ContactManagerDlg`-objektumon a `0x007b99a0`-t (`delete` ág) éri el, ha az objektum osztálya a `ContactManagerDlg`, és nem írja felül a slotot.

**2. A törlés után nincs lista-újraépítés a `0x007b9ff0`-ban (asm, megerősített).** A `0x007ba056` `call edx` után a `0x007ba058`-tól csak az epilógus jön (`pop edi; pop esi; pop ebx; pop ecx; ret 8`). A `0x007b99a0` törlési ága (37.7) a `0x007ba820`-t hívja, és visszatér.

**3. A `0x007b9ff0` hívója nem látszik közvetlen hívásban (feltételes).** Az index `xrefs` táblájában nincs közvetlen `call` a `0x007b9ff0`-ra; a pásztázás a `+0x190` vtábla-hívást sem találja. A hívó tehát közvetett (vtábla vagy általános útválasztó).

**4. A másik két `+0x148`-hívás** (`0x008d580f`, `0x008df00d`) nem a `ContactManagerDlg` tartományában van; osztályukat nem vizsgáltam (NINCS MEG).

**Korrekció a 37.7-hez.** A 37.7 feltételezte, hogy a `call [reg+0x148]` parancs-szétosztó. Ez nem igaz: a `0x007ba056` egy metódus (`0x007b9ff0`, vtábla-slot 100) belsejében van, nem szétosztóban.

**Cáfoló kísérletek.**
1. „A törlés hívója a parancs-szétosztó": cáfolva (1. pont).
2. „A törlés után a `0x007b9ff0` frissíti a listát": cáfolva (2. pont, asm).
3. „A `0x0045a9d0` a törlés hívási láncában van": nem vizsgáltam újra ebben a körben; a 37.7 feltételes állítása változatlan.

**Bizonyítottsági fok.** Az 1. és 2. pont: megerősített (két út: a vtábla PE-olvasata és az asm). A 3. pont: feltételes. A `0x007b9ff0` közvetett hívójának azonosítása: NINCS MEG.

**Lezárás (N6, 26. kör): (c).** A törlés utáni lista-újraépítés nincs a törlési ágban, és nincs a `0x007b9ff0`-ban. A kérdés a `0x007b9ff0` hívójáig vezet (a `ContactManagerDlg` vtábla 100. slotjáig). Ghidra-kör kell: a `0x007b9ff0` közvetett hívója (a vtábla-slot 100 használója). A pásztázás nem találja, mert nincs közvetlen `+0x190` hívás; cím még nincs. A következő lépés a generikus útválasztók és a `0x00cb7be4` vtábla-bejegyzés környezetének vizsgálata [blokkoló]

### 37.9 27. kör (2026-10-20, #5184, a 22. Ghidra-kör): a `0x00448fb0` táblája az `albumcontactids` oszlop betöltött tömbje; a tábla-író a `0x00499610` (N5)

**Kérdés.** Ki írja a `0x00448fb0` olvasó táblát (`this+0x27a0` = `[esi+0x58]`, `esi = this+0x2748`), mit tartalmaz a 64 bites elem, és mi váltja ki. Ez az N5 (személyszintű mellőzés) kérdése.

**Módszer.** A `paszta.py` darabolt pásztázása a teljes `.text`-re (2 884 879 utasítás, `0x00401000` .. `0x00c3f15b`), szöveges dekódolással (`detail=False`), memóriakapuval. A pásztázás nyers rekordjai ideiglenesek voltak, nincsenek a repóban.

**Kontrollok (pozitív ismert minták, mindkettő átment).**
- K1: a `0x00448fb0` közvetlen hívóhelyei pontosan a Ghidra-kör 21 címe (`0x0041a24b` … `0x007a5eaa`).
- K2: a `0x00448fb0` törzsében (a mért méret 186 bájt) megvan a fejléc-mutató olvasása `mov eax, dword ptr [esi + 0x58]` (`0x00449009`), a `+0x4c` és `+0x48` olvasás (`0x00449010`, `0x0044901d`), és az alapérték olvasása `mov ecx, dword ptr [esi + 0x60]` (`0x00449044`), `mov edx, dword ptr [esi + 0x64]` (`0x0044904a`).

**A bázis (megerősített).** `add esi, 0x2748` a `0x00448fbc`-ben. A `+0x27a0` mezőre (`this`-relatív) a teljes `.text`-ben nincs íráshely, két olvasás van (`mov eax, dword ptr [edi + 0x27a0]`, `0x0043a4d3` és `0x0043a4e6`, a `0x00439a80`-ban), és egy `lea` (`0x0043a501`, `+0x27a8`). A `+0x27ac`-re nincs találat. A tábla-író tehát a bázis-eltolt `[reg+0x58]` alakban kereshető.

**A tábla-író (megerősített, két független út).**
- **A út (a betöltés kódja).** A `0x00495be0` (a `0xc8230c` vtábla 6-os slotja, a bináris olvasata) `cmp dword ptr [esi + 0x54], 0` után, ha a mező nulla, meghívja a `0x00499610`-t (`0x00495c3f`). A `0x00499610` (63 bájt): `push 0x13320004` (`0x00499629`), `call 0x006a41e0` (`0x00499630`), `mov dword ptr [esi + 0x54], eax` (`0x0049963e`), `add eax, 0x284` (`0x00499643`), `mov dword ptr [esi + 0x58], eax` (`0x00499648`). Az `0x00499648` a `0x00499610` egyetlen `[esi+0x58]`-író utasítása; a `0x00499610` hívója (index) egyedül a `0x00495be0`.
- **B út (a konstruktor és az oszlopnév).** A `0x00415790` (`CThumbDB` konstruktora, spec 1828. sor) `lea eax, [ebp + 0x2748]` (`0x00415bbc`) után `call 0x00495360`-at hív. A `0x00495360` `mov dword ptr [esi + 0x4c], eax` (név), `mov dword ptr [esi + 0x50], edx` (szülő) írást végez, a név sztringje a `push 0xc80e34` (`0x00415b9b`), amely `.rdata`-ban `albumcontactids`. Ugyanitt `mov dword ptr [esi + 0x58], edi` (`0x004953a6`) előtt `xor edi, edi` áll, tehát a konstruktor nullára állítja a táblamutatót és az alapértéket.
- A két út független: A a futásidejű betöltést írja le, B a konstruktor nevét és a `.rdata` sztringet.

**Mi van a táblában.** A `0x006a41e0` a `(szülő, név, 0x13320004, &kimenet, 1)` hívásra ad egy fogantyút; a tábla a fogantyú `+0x284` mezője. Az oszlop neve `albumcontactids`. Az elem 64 bites (`uint64`): a mért típuskód `0x4` (spec 14.5.4), a `0x13320004` alsó szava `0x0004`, ami ezzel egyezik; a felső szó jelentése NINCS MEG. A spec 3.4/b mérése szerint az oszlop az albumsor-indexhez (`]facealbum:N`) rendelt kontakt-azonosító, a 118 sorból 9 nem nulla, és mind a 9 hexben egyezik a `contacts.xml` `id=` mezőjével. **A 64 bites érték tehát személy kontakt-azonosító, nem mellőzési lista.**

**Az olvasó szerepe.** A `0x00448c90` hívja a `0x00448fb0`-t (`0x00448cac`); ez a spec 649. sorában leírt „személy albuma van kiválasztva” predikátum forrása: nem nulla `albumcontactids` = személy-album.

**Mi váltja ki.** A lusta betöltés az első olvasáskor fut: a `0x00448fb0` (Ghidra-kör 22, C-törzs) a `[this+0x2754] == 0` ágon hívja a `(this+0x2748)+0x18` vtábla-slotot, a `0x00495be0` pedig csak akkor hívja a `0x00499610`-t, ha `[sub+0x54] == 0`. A `0x00495be0` nem ír vissza; a lemezre írás útja NINCS MEG.

**Személyszintű mellőzés (N5): NINCS MEG a hatása; a tábla nem a mellőzési lista.**
- A `0x005fdc30` és a `0x00640340` (az „Ignore Person” sztringek függvényei, 21.4) az indexben nem hívja a láncot (`0x00448fb0`, `0x00495be0`, `0x00499610`, `0x006a41e0`), és nincs bennük `[reg+0x58]` íráshely (a `.bt` pásztázás szerint). Ez index-szintű negatív állítás: a vtábla-hívásokat az index nem látja, ezért **feltételes**.
- A `[reg+0x58]` alakú írások teljes listája a `.text`-ben 1861 találat; a bázis nélküli íráshelyek kizárása NEM történt meg. Az „egyetlen tábla-író” állítás csak a `this+0x2748` bázisra és a konstruktor-láncra igaz.

**Cáfoló kísérletek.**
1. „A tábla-író a `0x00448fb0` törzsében van”: cáfolva; a törzs csak olvas (K2).
2. „A tábla a személyszintű mellőzés listája”: cáfolva az oszlopnévvel (`albumcontactids`, B út) és a mért kontakt-azonosító-egyezéssel (9/9).
3. „Az Ignore Person írja a táblát”: feltételes cáfolás (index-szintű, lásd fent); vtábla-hívás nem zárható ki.

**Bizonyítottsági fok.**
- A `this+0x27a0` = `albumcontactids` tábla: **megerősített** (A és B út).
- A tábla-író `0x00499648` és a betöltési lánc (`0x00495be0` → `0x00499610` → `0x006a41e0`): **megerősített** (asm; a vtábla-olvasat a binárisból).
- Az elem típusa (`uint64`) és jelentése (kontakt-azonosító): **megerősített**, mérés (spec 3.4/b, 14.5.4) és a `0x13320004` alsó szava.
- A `0x006a41e0` belseje (fájlból tölt-e, visszaír-e): **NINCS MEG**.
- A mellőzés hatása a táblára: **NINCS MEG**.

**Kész, ha (#5184, N5).** ⛔ Nem teljesül: a tábla azonosítva, a mellőzés és a hatása nyitott.

**Lezárás (c).** Következő Ghidra-cím:

**Válasz (2026-10-20): a `(szülő, név, 0x13320004, &kimenet, 1)` lookup három kérdése.** A 37.9/b részletei (a betöltő-lánc és a fájlnév) binárisban megerősítve; az alábbi kiegészítésekkel:

1. **Fájlból tölt-e (pmp).** Igen, de csak a bit 0-s csomópontokon. A találati ágon a bit 0 esetén a `0x006a7090` fut, és ha `[esi+8] == 1`, hívja a `0x006a2cd0`-t (`0x006a7094`). A `0x006a2cd0` a `pmp` sztringgel (`0x00ca80f4`) és a `%s_%s.%s` formátummal (`0x00ca80f8`) nevet állít össze, és fájlt nyit. A `string_xrefs` nem listázza a három betűs `pmp` sztringet, ezért a sztring-keresés üres eredményt adna; a címet diszasszemblálásból és a `pe_dis.read` olvasásából igazoltam. Az 1-es állapot kiosztója: NINCS MEG (37.9/b).
2. **Visszaírás a `+0x284` táblába.** A `0x006a41e0`-ben nincs `0x284` (diszasszemblálás: 0 találat). A `+0x284` a lookup által visszaadott rekordon belül van. A `0x00499610` a rekord mutatóját (`[esi+0x54]`) és a `rekord+0x284` címet (`[esi+0x58]`) tárolja, írás a rekordba nincs. **Javítás, 2026-10-21:** a másik hívó, a `0x006a5590`, a `0x13320004` kulcs alatt kéri le a rekordot (`0x006a55fc`), majd a `rekord+0x284` objektumot zárolja. A törzs a `rekord+0x2cc` vektor `in_EAX` indexű, 8 bájtos elemébe írja a `param_3` és `param_4` értéket, majd a `0x006a2a60`-nal érvényteleníti a gyorsítótárat (`0x006a56f5`-`0x006a5705`). Tehát a `0x006a5590` adatmezőket is ír, nem csak zármezőket.
3. **Ugyanazt az oszlopot írja-e a mellőzés.** NINCS MEG. **Javítás, 2026-10-21:** a `0x0056c5a0` csak a helyi menüt állítja össze; az `ID_IGNOREPEOPLE` parancsazonosítója `0x9c9a`. A `0x005cb990` diszpécser ugrótáblája a `0x9c9a` parancsot a `0x005c9b00` kezelőhöz irányítja (`0x005cdb8c`, `0x005cd9fc`, `0x005cbaef`-`0x005cbb14`). Ez a kezelő a `0x006a0d30` vektormásoló segédet hívja. A `0x006a5590`-hez vezető kapcsolat és a mellőzés által írt `0x1332000x` kulcs nincs bizonyítva; a virtuális hívások miatt a közvetlen hívási index hiánya önmagában nem kizárás. Lásd a 41. szakaszt.

2026-10-21-i állapot: a `0x00495be0` betöltési útja és a `0x006a5590` adatírása a 41. szakaszban lezárva. Az Ignore Person adatkulcsa ott nyitott marad; a következő cél a `0x006a0d30` által használt vektor tárolási útja.

**Lezárva (2026-10-21, 42.4):** a `0x00495be0` a `CColumn<unsigned___int64,1,322043908>::vftable` 6. slotja (`0x00c8230c`, slotcím `0x00c82324`). Ha a `param_1+0x54` még nulla, zárolás alatt meghívja a `0x00499610`-t (`0x00495c3f`); ez a lusta oszlop-lookup kiváltója. Ez önmagában nem jelenti, hogy minden esetben fájlt olvas: a `.pmp` betöltés továbbra is a 37.9/b-ben leírt rekordállapottól függ.

**Visszavonva a #5184 szempontjából (2026-10-21, 42.4):** a `0x0056c5a0` a `ID_IGNOREPEOPLE` feliratot és menüpont-állapotot kezeli, nem bizonyított kattintáskezelő. A `0x1332000x` írókulcs **NINCS MEG**; az N5-öt lezáró felvétel szerint a People Managerben és a személyalbum menüjében nincs személyszintű mellőzés, ezért ez a kulcs nem szükséges az N5 válaszához. Nem állítom, hogy a függvényben látható minden közvetett ág írói lánca ismert.
Ghidra-kör kell: 0x006a5590 zárblokkja (`0x006a5691`-`0x006a572a`): a `+0x284` objektum adatmezőinek írója [nem blokkoló]

**Colab-javaslat (futásidejű adat, a `behavior` feladathoz a tulajdonos `jovahagyva` címkéje kell).**
1. Új, üres mappa két képpel; az egyik a „Teszt Elek” személyhez tartozik (`PicasaTeszt`).
2. Az első lépés előtt másolat a `.picasa.ini`-ról és az `albumdata_albumcontactids` (db3/pmp) fájlról.
3. A személy-album `]facealbum:N` sorának `albumcontactids` mezőjét rögzíteni (nem nulla = személy-album).
4. Eszközök ▸ Személykezelő: mellőzés (Ignore Person) egy külön futásban, majd a két fájl bájt-diffje és a sor újraolvasása.
5. Eredmény: ha az `albumcontactids` nullázódik vagy átmozdul, a mellőzés a személy-album predikátumot (`0x00448c90`) érinti; ha nem, a mellőzés a tábla más írójában van.

**Nálunk (`src/`, greppel, 2026-10-20).** Az `albumcontactids` név 0 találat a `src/` alatt. Fejlesztési lista a 4. lépés eredménye nélkül nem készülhet.

**Módosított fájlok.** `docs/specs/picasa-arcfelismeres.md` (37.9); `docs/specs/00-index.md` (egy mondat a fájl sorában). A munkafa `.bt/` mappájában ideiglenes elemzőszkriptek és a rekordok (nem törölve).

### 37.9/b 28. kör (2026-10-20, #5184): a `0x006a41e0` C-je és a pmp-olvasó (`0x006a2cd0`) megvan; a fájl-betöltés rekord-állapottól függ; a mellőzés írója NINCS MEG (c)

**Kérdés.** A 37.9 lezárása: (1) a `(szülő, név, 0x13320004, &kimenet, 1)` hívás fájlból tölt-e; (2) van-e visszaírási út a `+0x284` táblába; (3) a személyszintű mellőzés írja-e ugyanazt az `albumcontactids` oszlopot.

**A hívás (megerősített, asm).** A `0x00499610` argumentumai fordított sorrendben: `push 1` (`0x00499622`, ötödik), a helyi kimenet címe (`lea ecx,[esp+4]`, `push ecx`, negyedik), `push 0x13320004` (`0x00499629`, harmadik), a név (`[esi+0x4c]+4`, vagy 0, második), a szülő (`[esi+0x50]`, első). A visszatérési érték csak a státusz (`test eax,eax`, `0x00499635`). Sikernél a kimenet kerül `[esi+0x54]`-be (`0x0049963e`), és `+0x284` kerül `[esi+0x58]`-ba (`0x00499648`). A 37.9 leírása ezen a ponton helyes.

**A `0x006a41e0` C-je (megerősített, `.ghidra/2026-10-20-ghidra-13.txt`).** A függvény maga nem nyit fájlt. Három kimenete van:
- **Találat** (a név egyezik a szülő `+0x58` listájának egy csomópontjával): a kimenet a csomópont `+0x04` mezőjére mutat. Ha a csomópont `+0x08` bájtjának bit 0-ja be van állítva, meghívja a `0x006a7090`-t (betöltés, lásd lent). Ha a tárolt típus (`+0x10`) eltér a kéréstől, a `0x006a2a30` felszabadítja a `+0x32c` puffert, és a rekord állapota 2 lesz.
- **Nincs találat, `param_5 = 1`, és a `0x006a84e0` (tiszta-név predikátum) 0**: a `0x006a85c0` lefoglal egy 0x334 bájtos rekordot, beláncolja a szülő `+0x54` listájába, majd a `0x006a6ff0` állapotát 2-re állítja (`mov dword ptr [ebx+8], 2`, `0x006a7004`). **A frissen létrehozott rekord tehát nem tölt fájlból.**
- Egyéb esetben 9 (nem található).

**A fájl-olvasó (megerősített, asm, `0x006a2cd0`, 413 bájt).** A `"%s_%s.%s"` formátumszöveggel (`sprintf`) `<szülő+0x60>_<kulcs>.pmp` nevet képez (`0x006a2d01`-`0x006a2d09`), megnyitja (`0x00991870`), a `+0x10` mezőbe 4 bájtot olvas, majd a `+0x08` mezőbe 4 bájtot, végül a törzset a `0x006d1e40`-nel a `+0x14` tagba tölti. Hibaüzenetei a `.\thumblab\CPropertyMap.cpp` forrásfájlra hivatkoznak. Ha a fájl nincs meg, a visszatérés 2 (`0x006a2d56`).

**Mikor fut a betöltés.** A `0x006a2cd0`-t a `0x006a7090` hívja, és csak ha a rekord `+0x08` mezője 1 (`cmp dword ptr [esi+8], 1`, `0x006a7094`). A `0x006a7090`-t a `0x006a41e0` találati ága hívja bit 0 esetén. A `0x006a41e0` által létrehozott rekord `+0x08` mezője 2, tehát **a frissen létrehozott `albumcontactids` rekord nem olvas fájlt**. Fájlt csak az a rekord olvas be, amely állapot 1-gyel maradt: az xref-index szerint a `0x006a85c0`-t a `0x006a68b0` is hívja, de a `0x006a6ff0`-t nem, tehát az ott létrehozott rekord állapot 1 marad. Hogy az `albumcontactids` rekordot melyik út hozza létre először: **NINCS MEG** (a `0x006a68b0` hívási lánca nincs végigkövetve). A `0x006a7090`-nak 10 hívóhelye van, tehát általános betöltő-ellenőrzés, nem N5-specifikus.

**Visszaírási út a `+0x284` táblába (1. kérdés második fele).** A `0x006a41e0`, a `0x006a85c0`, a `0x006a6ff0` és a `0x006a2cd0` nem ír `+0x284`-et. A fájl törzse a `+0x14` tagba olvasódik (`0x006d1e40`). A `+0x284` tábla írója: **NINCS MEG**.

**Mellőzés (3. kérdés).** A `0x006a41e0` közvetlen hívói (a Ghidra-kör HÍVÓK-listája): a nyolc csomagoló (`0x00499550`-`0x00499710`) és nyolc további hely (`0x006a4670`, `0x006a46c0`, `0x006a5060`, `0x006a5590`, `0x006a5a60`, `0x006a5c60`, `0x006a61f0`, `0x006a63f0`). A `0x005fdc30` és a `0x00640340` közöttük nincs. Vtábla-hívás nem látszik, ezért ez feltételes. Az `src/picasapy/pmpimport/arcatvetel.py` az ini `ffffffffffffffff` értékét mellőzésnek veszi (arc-szint, rect64 mező), de nem bizonyított, hogy a személyszintű albumoszlopban is ez a szentinel.

**Bizonyítottsági fok.**
- A hívás alakja és a rekord-állapot logika: **megerősített** (a `0x006a41e0` C-je, és a `0x006a6ff0`, `0x006a7090`, `0x006a2cd0` asm: a C és az asm egymástól független út).
- A fájlnév (`<szülő+0x60>_<kulcs>.pmp`) és a fájl-olvasó: **megerősített** (asm és a beépített formátumszöveg); egyezik a `src/picasapy/pmpimport/table.py` `<tábla>_<oszlop>.pmp` konvenciójával. A `+0x60` sztring szerepe a szülőhöz: **feltételes** (a `0x006a7090` `edx`-ét a `0x006a41e0` hívásában nem követtem végig a gépi kódban).
- A `+0x284` írója és a mellőzés hatása: **NINCS MEG**.

**Kész, ha (#5184, N5).** ⛔ Nem teljesül: a fájl-olvasás és a rekord-állapot tisztázva, a tábla írója és a mellőzés hatása nyitott.

**Lezárás (c).** Nem zárható. Megnevezett következő lépések:
1. **Bináris, Ghidra nélkül:** a `0x006a68b0` hívási lánca (ki hozza létre az állapot-1 rekordot), mert ettől függ, hogy az első lookup beolvas-e fájlt. Asm-szinten elvégezhető.
2. **Colab-felvétel** (futásidejű adat; a `behavior` feladathoz a tulajdonos `jovahagyva` címkéje kell):
   a. Új, üres mappa két képpel; az egyik a „Teszt Elek” személyhez tartozik.
   b. Másolat a `.picasa.ini`-ról és a `<prefix>_albumcontactids.pmp` fájlról (a prefix a `+0x60` sztring; a db3 mappa neve várható, nincs megerősítve).
   c. Személyszintű mellőzés (Ignore Person) egyetlen futásban, majd a két fájl bájt-diffje. Külön figyelni, megjelenik-e `ffffffffffffffff` a `.pmp`-ben és a `.picasa.ini` `rect64` mezőiben.
   d. Ha a `.pmp` nem változik, a mellőzés nem ezt az oszlopot írja, és a tábla-író más úton van (ekkor a `0x006a41e0` nem a kulcs).

**Jegytörzs-javaslat (N5).**
- **Eredeti:** a `0x006a41e0` (lookup) fájlt csak a `0x006a2cd0` olvas, `<szülő+0x60>_<kulcs>.pmp` néven, és csak állapot-1 rekordon. A személyszintű mellőzés hatása az `albumcontactids` oszlopra: NINCS MEG.
- **Nálunk (`src/`, greppel, 2026-10-20):** az `albumcontactids` név 0 találat a `src/` és a `tests/` alatt. A `.pmp` olvasó: `src/picasapy/pmpimport/table.py`. A mellőzés: `src/picasapy/pmpimport/arcatvetel.py` az `ffffffffffffffff`-et arc-szintű mellőzésként kezeli; személyszintű oszlopra nincs szabály.
- **Teendő:** nincs fejlesztési teendő a Colab-diff előtt. Utána: ha a `.pmp` változik, a mellőzés írási helyét a `pmpimport` modulba kell bekötni.
- **Kész, ha:** a Colab-diff megmutatja, melyik fájl és melyik bájt változik személyszintű mellőzésnél, és a `src/` ehhez igazodik.

**Módosított fájlok (28. kör).** `docs/specs/picasa-arcfelismeres.md` (ez a 37.9/b szakasz); `docs/specs/00-index.md` (a sor elején egy 28. kör-előtag). Kódhoz (`src/`, `tests/`) nem nyúltam.

### 37.10 Felvétel (2026-10-20, #5184 N5 és N6): a személyalbum menüje és a „Delete People Album” hatása

*Forrás:* picasa-colab-jobs job-222 (előtte), job-223 (a megerősítő ablak), job-224 (utána); Picasa 3.9, alapállapot, két arc a „Teszt Elek” névhez (a job-213 lépései szerint).

- **A személyalbum jobb gombos menüje** (job-222, 31. kép): Edit People Album..., Select All, Clear Selection, Invert Selection, Refresh Thumbnails, Sort Album By, Delete People Album. **Személyszintű mellőzés (Ignore) ebben a menüben nincs**; az N5 mellőzése tehát nem innen érhető el.
- **A megerősítő ablak** (job-223, 33. kép): címe „Remove People”, szövege `Are you sure you want to delete the people album "Teszt Elek"?`, alatta a `Delete tagged faces from synced Picasa Web albums, too` jelölőnégyzet (üres), gombok: Delete Album és Cancel; **az alapértelmezett a Cancel** (a job-223 Return-je nem törölt).
- **Az N6 válasza: a törlés hatása a fájlokra** (job-222 és job-224 `.picasa.ini`): a törlés után mindkét képnél **eltűnik a `faces=` sor**, tehát az arc-régió is törlődik, nem névtelen lesz. A **`[Contacts2]` sor megmarad** (`<azonosító>=Teszt Elek;;`). Az adatbázisban (`db3`) az `albumdata_albumcontactids`, `albumdata_date`, `albumdata_inisync`, `albumdata_token`, `albumdata_uid`, `imagedata_backuphash` oszlop és a `facetemplatesV2_0.db` változik (md5 szerint).
- **Bizonyítottsági fok:** megerősített (felvétel, két független futás: a job-223 Cancel-lel változatlan, a job-224 Delete Album-mal változott). Az időzítés: a változás a megerősítés után 8 másodpercen belül a fájlban van.
- **Nálunk:** a megerősítő ablak más (cím, gombok, jelölőnégyzet), és a törlés a `[Contacts2]` sort is törli. A megvalósítás: #5391.
- **Lezárás (N6): (a)**, a #5391 fejlesztési jeggyel. Az N5 (személyszintű mellőzés) ebből a menüből nem érhető el; a belépési pontja a Személykezelő (Eszközök ▸ Személykezelő) felvételével keresendő.

### 37.11 Felvétel (2026-10-20, #5184 N5): a People párbeszédablak, és nincs személyszintű mellőzés

*Forrás:* picasa-colab-jobs job-225 (az Eszközök menü), job-226 (Eszközök ▸ People Manager); Picasa 3.9, alapállapot, egy „Teszt Elek” személy két arccal.

- **Az Eszközök menü** (job-225, 31. kép): Folder Manager..., Upload Manager... (szürke), People Manager..., Configure Photo Viewer... (szürke), Configure Screensaver... (szürke), Back Up Pictures..., Batch Upload..., Adjust Date and Time..., Upload ▸, Geotag ▸, Experimental ▸, Configure Buttons..., Options....
- **A People párbeszédablak** (job-226, 34. kép): címe „People”; bal oldalon `Search:` mező és a személyek listája (itt egy sor: „Teszt Elek”), alatta a **Delete Person** és **New Person** gomb; jobb oldalon a kijelölt személy arcképe, „2 Photos in Picasa”, `Name:` és `Email(s):` mező, a „Sync Face Tags with Web Albums” jelölőnégyzet (szürke) és a **Revert** gomb (szürke); alul **Manage Online Contacts** (szürke), **Refresh Contacts** (szürke), **OK** és **Cancel**.
- **Az N5 válasza:** személyszintű mellőzés (Ignore) **sem a személyalbum menüjében (37.10), sem a People párbeszédablakban nincs**. A Picasa 3.9-ben a mellőzés arcszintű: a csempe X gombja és a kibontott nézet „Ignore Selected” gombja (job-209, job-210, job-218), az arc kulcsa `ffffffffffffffff` lesz (34.11). Az `albumcontactids` tábla (37.9) a személyalbumok névjegy-hozzárendelése, nem mellőzési lista.
- **Bizonyítottsági fok:** megerősített (felvétel: mindkét menü és a párbeszédablak teljes tartalma látszik).
- **Lezárás (N5): (b)** lezárható: nincs személyszintű mellőzés, tehát nincs megvalósítandó eltérés; az arcszintű mellőzés a PicasaPy-ban az eredeti szerint működik (`face_ignore_ini.py`, `ffffffffffffffff`).

## People ablak és névjavaslat: teljes viselkedés binárisból (#5437)

**Hatókör és források.** Ez a szakasz a People ablakot (`contactmgr.fen`, `ContactManagerDlg`), a csempe névjavaslatát (`PeoplePanel::AutoCompleteProvider`) és a névjegytárat (`ContactManager`) írja le. Forrás: `referencia/ghidra/2026-10-21-people-dlg.txt` (a `0x007b7910`, `0x007ba4f0`, `0x007b86b0`, `0x007b8f80`, `0x007b8d20`, `0x007b7f00`, `0x007cfae0`, `0x0085a1a0` blokkjai); `2026-10-21-ac-gyors.txt` (a `0x00643940`, `0x00643580`, `0x00643720`, `0x006437b0`, `0x006436b0`, `0x007bdb00`, `0x007b7580`, `0x00589640`, `0x00589760`, `0x0058aaf0`, `0x0058ad60`, `0x0058af90`, `0x00809050`, `0x00809280` blokkjai); a korábbi dumpok: `2026-10-17-szemelykezeles-6.txt` (`0x007bb660`), `2026-10-17-szemelykezeles-4.txt` (`0x007b99a0`), `2026-10-17-szemelykezeles-5.txt` (`0x007baf50`, csak a hívási lista és a sztringek), `2026-10-20-ghidra-22.txt` (`0x007b81e0`), `2026-10-20-ghidra-23.txt` (`0x007b9630`), `2026-10-21-koteg-1021b.txt` (`0x007b7b10`), és az index (`functions`, `xrefs`, `string_xrefs`, `rtti`). A feladatban megnevezett `~/Documents/PicasaPy/.ghidra/` könyvtár nincs meg; a dumpok a `~/picasapy-agent/referencia/ghidra/` alatt vannak. A `2026-10-21-autocomplete.txt` ugyanott megtalálható; a célvezérlőhöz való kötését a 38.17 dolgozza fel.

**Jelölések.** „Binárisból”: C-dumpban vagy az indexben látszik, a cím mellett. „Következtetés”: a hívási mintából vagy a sztringből következik, nem a függvény nevéből. „NINCS MEG”: a dumpokban nincs meg; mellette a Ghidra-cím, amelyet kérni kell.

### 38.1 Az ablak felépítése és az állapotgép

- **Vezérlők (binárisból).** A `0x007b8f80` betölti a `contactmgr` erőforrást (`FUN_0060dc30("contactmgr")`), és értékfigyelőt köt öt vezérlőre: `contacts` (lista), `fullname`, `emails`, `search` és `sync`. A `sync` sztring nincs az indexben; a `count` (`0x00cb71dc`) és a `gplus` (`0x00cb71ec`) közti helyről következtetve `sync` (következtetés).
- **Állapot (binárisból).** A `this+0x158` mező (dumpban `param_1[0x56]`). Értékei: `0` = nincs munkamenet (a `0x007b9630` azonnal visszatér); `1` = böngészés; `2` = meglévő személy módosítva; `3` = új személy (a `0x007ba4f0` írja). A validálás (`0x007bb660`) a `2` és `3` értéknél dolgozik. A `contacts` ág (a lista kijelölés-változása) validál, ha az állapot nem `1`, majd `1`-re állít. A mezőmódosítás `1`-ről `2`-re lép (a `0x007b9630` végén).
- **Kijelölt sor (binárisból).** A `this+0x13c` (dumpban `param_1[0x4f]`), kezdeti értéke `-1` (`0x007b8f80`). A `contacts` ág a lista kijelölt indexét egyetlen értékként olvassa (vtábla `+0xc`). Ez erős jel az egyes kijelölés mellett, de a többes kijelölést nem zárja ki: N7 nyitva marad.
- **Sortömb (binárisból).** A rekord 0x30 bájtos; a tömb `this+0xe0`, a darabszám `this+0xe4`. Szűrt nézet: a leképezés `this+0x100`, a darabszáma `this+0x104`, a szűrés jelzője `this+0x114`. Sor-jelzőbájtok: `this+0x134`. Kiválasztott név mutatói: `this+0x150` és `this+0x154`. Választás-mód jelző: `this+0x15c`. A `0x007b8f80` `0`-ra állítja; a dumpokban más író nincs (**NINCS MEG**: a `1`-re állító kód).

### 38.2 A sor felirata (`0x007b7910`)

Binárisból:
- **Csillag-előtag.** A `* ` jel akkor jelenik meg, ha a sor jelzőbájtjának 0. bitje (`this+0x134`) be van kapcsolva, és a sor nem üres új sor. Üres új sor: nulla azonosító, nincs név, és a 0x20-as mező nulla. A bitet a mezőmódosítás állítja (a `0x007b9630` végén, `|= 1`). Jelentése „módosított, mentetlen” (következtetés).
- **Név.** Ha mindkét névrész nem üres: `%s, %s`. Ha csak az egyik: az. A két rész forrása a `0x007b5600` (145 bájt, nincs dumpolva): **NINCS MEG**, melyik a vezetéknév.
- **Üres név.** Ha van azonosító, a felirat a `%I64x` alak (két dword, kisbetűs hexadecimális). Ha nincs azonosító, a `ContactManagerDlg::NewContact` kulcs szövege. Ez ugyanaz a `%I64x` formátum, amelyről a 32.3 szakasz írt.

### 38.3 Felépítés és szűrés gépeléskor

- **Újraépítés (`0x007b7f00`).** Minden sorra meghívja a `0x007b7910`-t, a kijelölt sort a régi kulcs alapján visszaállítja, majd a lista-vezérlőn a kijelölést (`+0x7c` slot) és egy rajzolás-jelzőt (`+0x10c`, `0` és `1`) hív. Következtetés: rajzolás tiltása és engedélyezése.
- **Szűrés gépeléskor (binárisból, `0x007b9630` `search` ága).** A `search` mező változása: először `0x007bb660` (validálás; 2. vagy 3. állapotban párbeszédet is dobhat), aztán `0x007b7f00` (újraépítés), végül `0x007b81e0` (gombállapot). A szűrés szabálya (kis- és nagybetű, ékezet, szóhatár) a `0x007b4990` és a `0x007b5260` törzsében van: **NINCS MEG** (Ghidra-kör: `0x007b4990`, `0x007b5260`).
- **Fájl-API a láncban.** A `0x007b7f00` közvetlen hívottjai között nincs fájl-API. A lista: `0x00401000`, `0x0052e490`, `0x007b4990`, `0x007b5260`, `0x007b7910`, `0x007b7b10`, `0x008e3710`, `0x0097caf0`, `0x00985a60`, `0x00985ff0`, `InterlockedIncrement`, `InterlockedDecrement`. A `0x007b4990` és a `0x007b5260` mélyebb lánca nem ismert: **NINCS MEG**, olvas-e lemezt.

### 38.4 Csempéből nyitás, előtöltés, New Person

- **Megnyitás.** A `0x0085a1a0` a `/c/ui/ContactManager` erőforrásból hozza létre a párbeszédet (a `0x0085a120` hívásával; a sztring `ContactManagerDlg::GoogleContacts`). Egyetlen hívója a `0x00720dd0` (index-xref). A csempe Enter-útja a `0x00720dd0`-ig: **NINCS MEG** (Ghidra-kör: a `0x00720dd0` hívója `0x0071f740`; a `0x00787dd0` (a csempe-kártya gombjainak és feliratainak építője, `Add a name`) hívói `0x007853e0` és `0x007899e0`; az Enter-cél azonosítása nyitott (19. szakasz, 5. pont)).
- **Előtöltés.** A Search mező előtöltését (a csempe szövege) a megnyitó útvonalon nem láttam: **NINCS MEG**. A 2026-10-17 job-167 felvétel szerint a mező előre ki van töltve és kijelölve (19. szakasz).
- **New Person (`0x007ba4f0`, binárisból).** Lépésről lépésre:
  1. Ha az állapot nem `1`, előbb `0x007bb660` (38.5).
  2. Az állapot `3`.
  3. A `search` mező szövege (`0xec` és `0x18` slot) a lekérdezés tárolójába (`this+0x140`) kerül.
  4. Új sor a sortömb végére: a jelzőtömb bővül, az új sor jelzőbitje `|= 1`, az állapotbit `0x2`, ha van név, különben `0x4`. A feltétel forrása a dekompilátorban elveszett (`piStack_4c`): **NINCS MEG** a pontos feltétel.
  5. A `ContactManagerDlg::NewContact` szöveg a `0x008e3710`-nek megy. Célja **NINCS MEG**.
  6. A kijelölés `0`, `this+0x13c = 0`, majd lista-újraépítés a `0x007b7f00`-val, lekérdezés nélkül (következtetés: a második argumentum `0`, tehát nincs szűrés; a dekompilátor `unaff_retaddr` értelmezése bizonytalan).
  7. Fókusz a `fullname` mezőre (`0xbc` slot; a slot neve **NINCS MEG**).
  - Hogy a `search` szövegből lesz-e az új sor neve, azt a `0x007b56a0` dönti el (**NINCS MEG**).

### 38.5 Validálás jóváhagyáskor és új személynél (`0x007bb660`)

Binárisból (`2026-10-17-szemelykezeles-6.txt`). Hívói: `0x007b9630` (2 hely), `0x007b99a0` (az `ok` parancs) és `0x007ba4f0` (New Person).
- **Nincs teendő:** ha az állapot nem `2` és nem `3`, a visszatérés `0`.
- **Üres név** (`2` vagy `3`, és nincs jelző): a doboz címe `ContactManagerDlg::InvalidContact`, gombja `ContactManagerDlg::Ok`, üzenete `ContactManagerDlg::EmptyContactMsg` (a szöveg: „Empty People are not allowed. Person will be reverted.”, a sztring-sorrendből következtetve). Utána `0x007bb370`, a visszatérés `0xf4242` (nem menthető). A sor visszaáll.
- **Hiányzó teljes név** (`2`): `ContactManagerDlg::EmptyFullNameMsg` (szöveg: „Unable to remove a Person's name. Change will be reverted.”, következtetés), modális doboz (`0x009ba4d0` és `0x009bab50`): cím `ContactManagerDlg::InvalidContact`, gomb `ContactManagerDlg::Ok` (a dekompilált hívásból a szerepek következtetettek), utána visszaállítás.
- **Új személy** (`3`): a `0x00585ad0` a gyűjteményben duplát keres. Találatnál a `0x0058ff00` kijelöli a találatot, a `0x007b7f00` a találatra szűr. Ezután:
  - e-mail egyezés: `ContactManagerDlg::DupEmailMsg` (`You already have a person with the email address '%s'…`, a teljes szöveg a sztringek indexéből);
  - név egyezés: `ContactManagerDlg::DupNameMsg` („You already have a person with the name '%s'. Are you sure you want to create a new person?”);
  - egyéb: `ContactManagerDlg::DupContact` (szöveg **NINCS MEG**).
  - Kérdés: cím `ContactManagerDlg::DupFoundTitle`, gombok `ContactManagerDlg::Yes` és `ContactManagerDlg::No` (modális). „Igen”: `0x007bb370` hívódik, a visszatérés az eredménye. „Nem”: nincs mentés, a visszatérés `0`.
- **Nincs duplikátum:** a visszatérés `0`, és a `0x007bb370` NEM hívódik meg. A mentés a hívóban van (**NINCS MEG** a hívó).

### 38.6 Név és e-mail szerkesztése

- **Rekord-frissítés (`0x007b8d20`).** Beírja a `fullname` és az `emails` szövegét a sor rekordjába (az e-mail a `+0x1c` mezőbe, a név másik mezőbe; a pontos név-mező **NINCS MEG**). A `+0x24` bájtot 1-re állítja. A `0x0098b6e0` 8 bájtos értékét a `+0x10` mezőbe írja (**NINCS MEG**, mi az: a törzs hiányzik).
- **`[0x15d]` jelző.** A `0x007b8d20`-ban `0`, ha az e-mail elemzése (`0x00939690`, törzse **NINCS MEG**) sikeres és a szöveg nem üres, különben `1`.
- **Ellentmondás (NINCS MEG).** A `0x007b81e0` akkor adja az `InvalidEmail` üzenetet, ha `[0x15d] == 0`. A két állítás együtt azt jelentené, hogy a helyes e-mail adja a hibát. A dumpok alapján nem dönthető el, melyik olvasat a helyes; a dekompilátor a feltétel ágait megfordíthatta.
- **Engedélyezés (következtetés).** A `0x007b81e0` a `fullname` és `emails` vezérlők engedélyezését a `0x00588460` eredményétől teszi függővé (**NINCS MEG** a függvény neve és törzse). A mintából: ha a `0x00588460` nem nulla, a két mező tiltott.
- **Megjelenés.** A `0x007b7b10` (`2026-10-21-koteg-1021b.txt`, a blokk a 679. sortól) a `fullname`, `emails` és `online_contact` mezőket tölti fel. A `thumb`, `count` és `gplus` részt a `0x007b86b0` állítja.

### 38.7 Gombállapotok, felirat, státusz (`0x007b81e0`)

Binárisból (`2026-10-20-ghidra-22.txt`, a `0x007b81e0` blokkja). Hívói: `0x007b7b10`, `0x007b9630` (2 hely), `0x007ba060`. Ez a függvény frissíti az egész felületet.
- **`delete`:** engedélyezett, ha van kijelölt sor (`cStack_14` jelző; forrása részben **NINCS MEG**).
- **`fullname`, `emails`:** a 38.6 szerint.
- **`revert`:** engedélyezett, ha a kijelölt sor 0. bitje be van kapcsolva (következtetés a `puStack_58 = flags & 1` értékadásból; a beállító slot neve **NINCS MEG**).
- **`sync`:** a sor állapotbitjeiből, az érték `(flags & 6) != 4` (következtetés az értelmezésről).
- **`count`:** láthatóság a `cStack_14` jelzőtől (a slot neve **NINCS MEG**).
- **`ok`:** a `DAT_00c9ad6c` vezérlő (a neve az indexben nincs; az OK-gomb a legvalószínűbb, következtetés). Engedélyezett, kivéve ha a kijelölt sor üres nevű és nincs jelzője (`bVar3`).
- **OK / Choose felirat.** Ha `[0x57]` (`this+0x15c`) be van kapcsolva ÉS a kijelölt név mutatói (`[0x54]`, `[0x55]`) egyeznek a tároltakkal, a felirat a `ContactManagerDlg::OK` szövege, különben a `ContactManagerDlg::Choose` szövege. A `[0x57]`, `[0x54]` és `[0x55]` írói a dumpokban **NINCS MEG** (csak a `0x007b8f80` nullázza őket). Ez blokkolja a Choose-szabály tesztelését.
- **Státusz.** A `status` címkét (`0xe8` slot) állítja. Az `InvalidFullName` és `InvalidEmail` szövegek ide mennek, ha az `unaff_BP` jelző be van kapcsolva; melyik hívó kapcsolja be: **NINCS MEG**.

### 38.8 Parancsok: OK, Mégse, Revert, Delete, Online, Refresh (`0x007b99a0`)

Binárisból (a parancsnevek a dispatcher sztring-összevetéséből):
- **`ok` (OK és Choose):** a dispatcher `0x007b9a03`-nál hívja a `0x007bb660`-at (validálás). Ha nem `0`, a párbeszéd marad nyitva. Utána `0x007baf50` (mentés; hibaüzenet `ContactManagerDlg::UpdateFailed`: „Failed to update person!”; a törzse nincs elemezve), majd bezárás: `0x008d2720(…, 0)`.
- **`cancel` (Mégse):** a parancs-összevetés a `0x007b9a57` címnél történik; az ág a `0x007b9a90` hívásnál közvetlenül a `0x008d2720` bezárást kéri. A második argumentum a hívótól érkező `[EBP+0xc]`, nem itt beégetett konstans. Ebben az ágban nincs validálás (`0x007bb660`) vagy mentés (`0x007baf50`). Ez csak az adott ág sorrendjét bizonyítja; a korábban végrehajtott külön mentésekről és a módosított mezők tényleges Cancel utáni profilállapotáról nincs mérés.
- **`create` (New Person):** `0x007ba4f0` (38.4).
- **`delete`:** `0x007ba820` (1826 bájt). Sztringek: `ContactManagerDlg::ConfirmDelete` (megerősítés), `ContactManagerDlg::DontWarn` („Don't warn me about this in the future”, a beállítás a `Preferences` csoportban), és az online-használat figyelmeztetése: `ContactManagerDlg::DeleteSubjectWarning` és a `…ES` változat (a törlés az online fotók címkéit lecsatolhatja). A figyelmeztetés feltétele **NINCS MEG** (a `0x007ba820` elágazásai nincsenek dumpolva).
- **`revert`:** `0x007bb370`. Szerepe **NINCS MEG**: a „will be reverted” üzenetek is ide mutatnak, de a `0x007bb370` a „Yes” ágban is hívódik (38.5), ezért nem egyértelmű, hogy visszaállítás.
- **`online` (Manage Online Contacts):** megnyitja a `https://www.google.com/contacts` címet. Ha van piszkos sor, előbb kérdés: `ContactMangerDlg::PersistBeforeSync` („Save changes?”, cím `…PersistBeforeSyncTitle`), gombok `ContactManagerDlg::Cancel` és `ContactManagerDlg::Ok` (`2026-10-17-szemelykezeles-4.txt`, az `online` ág).
- **`refresh_contacts`:** `0x007b9f20` (199 bájt; `2026-10-20-ghidra-24.txt`).

### 38.9 A csempe névjavaslata: lista, rajzolás, elfogadás

- **Vtábla (binárisból).** A `PeoplePanel::AutoCompleteProvider` vtáblája `0x00ca1740` (RTTI). A vtábla eltolásai (DATA-hivatkozásokból):
  - `+0x00` = `0x00643940`: lekérdezés. Bemenet: a gépelt szöveg. Kimenet: a találati tömb, 8 bájtos elemek (sztringmutató és jelzőbájt).
  - `+0x14` = `0x007bdb00`: a Google+-körök ajánlója felé ágazik (`0x007bdc40`, `0x007be010`). A sztringek (`Everyone in your circles`, `Visible to anyone on the web.`) alapján ez másik lista, nem a névjegytár (következtetés).
  - `+0x20` = `0x00643580`, `+0x24` = `0x00643720`, `+0x28` = `0x006437b0`, `+0x2c` = `0x006436b0`.
- **`0x00643940` (binárisból).**
  - Üres szöveg: a forrás az alkalmazás-objektum (`DAT_00d67668`, `+0x102c`) tagjaiból jön (`+0xeac`, `+0x2bc`). A forráslistát a `0x00491980` állítja elő (sztring: `FRAddSuggesetions`), a darabszámot a `0x007b53a0` ellenőrzi.
  - Nem üres szöveg: előbb `0x007b4990(szöveg)` (lekérdezés), majd ugyanaz a forrás.
  - **Korlát:** a `0x00643940` nem vág le; a kimenet darabszáma a forrás darabszáma. A forrás korlátja **NINCS MEG**.
  - **Sorrend:** a forrás sorrendjét másolja (`0x005c2020` ciklus). A forrás rendezése **NINCS MEG**.
  - Közvetlen hívottjai között nincs fájl-API (`0x00491980`, `0x007b4990`, `0x007b53a0`, `0x00448c90`, `0x007166c0`, `0x009c2fc0`, memória-műveletek). A mélyebb lánc **NINCS MEG**.
- **`0x006436b0` (`+0x2c`).** A `PeoplePanel::AutoCompleteProvider` vtáblájának RTTI/pointer által megerősített slotja. Az azonosító 8 bájtos rekordját a `0x0044d650`-nek adja át; a cél a névjegyrekordot lekéri, sztringet hash-el és az névkiegészítő környezet tárolójával hasonlít, majd logikai eredményt ad vissza (35.7). Ez **nem** bizonyít csempe-sorbeli elfogadást, arc-hozzárendelést vagy People ablak nyitást; a `faceclusterpanel_%d_addname` bekötése nyitott.
- **`0x006437b0` (`+0x28`).** Név alapján darabszámot számol (`*param_4`). Ha pontosan egy egyezés van, azt a `0x00585770` feloldja. Hívója **NINCS MEG** (a csempe Enter-útja?).
- **Popup billentyűi (`0x00809050`, `CAutoCompleteListBox`, vtábla `0x00cbd8ec`).**
  - `VK_DOWN` (0x28): a következő elem. Az utolsónál körbefut, ha a `+0x20` jelző be van kapcsolva; különben nincs kijelölés.
  - `VK_UP` (0x26): az előző elem; az elsőnél ugyanez fordítva.
  - `VK_RETURN` (0x0d): az aktuális elem (`0x009df260`) elfogadása (`0x00a54b70`).
  - Egyéb billentyű: `0xf4241`, nincs kezelve (a szülő kapja, például Escape).
  - Kijelölt elem: a 8 bájtos elem `+4` dword-jének 0. bitje (`|= 1`).
  - **Nyitott:** használja-e a csempe popupja ezt az osztályt (**NINCS MEG**).
- **Görgetés (`0x00809280`).** A popup görgetése `index × elemmagasság` (`param_1[9] * param_1[4]`), plusz a `+0xbc`/`+0xc0` eltolás.
- **Megjelenítés, elrejtés, kép.** A `CAutoCompleteListBox` általános kiválasztási és elrejtési útja megvan (`0x00809360`, `0x008095c0`); a találat kirajzolása és képe (arc vagy sziluett), valamint az, hogy a Név nélküliek csempemezője ezt az osztályt használja, **NINCS MEG** (38.17).

### 38.10 Korrekciók a korábbi szakaszokban (2026-10-21, #5437)

1. **36. szakasz, 22. kör (N6):** a `ContactManagerDlg::OK` és a `ContactManagerDlg::Choose` kulcs nem naplóüzenet, hanem az OK-gomb szövege (38.7). A „tárolt” név-mutatók (`[0x54]`, `[0x55]`) írói **NINCS MEG**. A hibás mondat a helyén javítva.
2. **19. szakasz, „Meglévő név, javaslatlista, Choose és Escape” sor:** a javaslat-elemre kattintás **megvan** a kódban (`UnnamedFacesView.qml:650-652`: `MouseArea` → `submitName(personName)`, #5285). A korábbi „nincs aktiváló kezelő” állítás a régebbi sorokra (547-587) vonatkozott. A hibás mondat a helyén javítva; az élő kattintás mérése nyitott.
3. **N7 (kijelölés):** erősödött, nem zárult. A `0x007b9630` `contacts` ága egyetlen indexet olvas (38.1). A többes kijelölés kizárásához a `0x007ba820` és a lista-vezérlő kijelölési módja kell (**NINCS MEG**).
4. **A 32., 35. és 37. szakasz állításai megmaradnak:** a `0x007b81e0` nem hív `0x00586e20`-t (a hívottjai között nincs), és a `0x007bb660` csak a `2` és `3` állapotban fut.

### 38.11 Ghidra-kérések (sorrendben)

1. `0x007b4990` (2252 bájt): a név-lekérdezés és szűrés törzse, a People-lista és a csempe-javaslat közös része. Ebből dől el a 38.3 és 38.9 egyezési szabálya. **[blokkoló: Q2]**
2. `0x007b5260` (315 bájt): a People-lista szűrő-predikátuma. **[blokkoló: szűrés]**
3. `0x00491980` (2139 bájt): az AC forráslista (`FRAddSuggesetions`). **[blokkoló: Q3]**
4. `0x007b53a0`, `0x00448c90`, `0x007166c0`: a `0x00643940` feltételei.
5. `0x007b5600` (145 bájt): a sor két névrészének forrása és sorrendje.
6. `0x007bb370` (734 bájt): a függő változás lezárása; a „Yes” ág, a `revert` és az üres név ág közös törzse.
7. `0x00585ad0` és `0x0058ff00`: a duplikátum-keresés és a találat kijelölése.
8. `0x00588460`: a `fullname` és `emails` engedélyezésének feltétele.
9. `0x0098b6e0`, `0x007b56a0`, `0x00939690`, `0x00585770`: a 8 bájtos érték forrása, a név-hozzáadás, az e-mail elemzés és a név-feloldás.
10. A `[0x54]`, `[0x55]`, `[0x57]` írói: a `0x00787dd0` (a csempe-kártya építője) hívói `0x007853e0` és `0x007899e0`; a `0x00720dd0` hívója `0x0071f740`.
11. A névjegytár háttere: `0x0058e750` (a `DownloadContacts` hívója), `0x0058a030` (1999 bájt) törzse, az `ytAsyncQueue<ContactManager::DownloadJob>` munkás-függvénye (vtábla `0x00c91614`), az `IContactManagerHandler` értesítő metódusai (vtábla `0x00c908b4`), és a `0x00589760` hívói.
12. `0x007baf50` (1031 bájt) törzse: a mentés írási útja a Contacts2 írásáig.
13. A `2026-10-21-autocomplete.txt` feldolgozva (38.17). Megvan az általános `CAutoCompleteListBox` kiválasztási és elrejtési útja; ez nem köti a listát a csempemezőhöz. A csempe vezérlőjének és callbackjének összekötése továbbra is a 10. tétel (`0x007853e0`, `0x007899e0`) és a `0x00787dd0` dinamikus vezérlőjének követése.
14. `0x0085a120` és `0x0071f740`: a People-ablak megnyitásának teljes útja.

### 38.12 A névjegytár: háttér, memória, értesítés (Q3)

- **Háttérsor (binárisból).** A `ContactManager` vtáblája `0x00c91564` (RTTI). Van letöltő-sora: `ytAsyncQueue<ContactManager::DownloadJob>` (vtábla `0x00c91614`), és megfigyelő-listája: `ytArray<IContactManagerHandler*, 1, ytBaseThread>` (vtábla `0x00c9163c`). Az interfész: `IContactManagerHandler` (vtábla `0x00c908b4`). Ezek szerint a letöltés háttérben, sorban fut, és az eredményt megfigyelők kapják. A szál indítása és az értesítés hívási helye **NINCS MEG**.
- **Letöltő-függvények.** A vtábla `+0x2c` (`0x0058aaf0`, „Downloading Focus Groups”) és `+0x30` (`0x0058ad60`, „Downloading Focus Contacts”) slotja. Mindkettő a `this+0x38` térképet használja (`0x0058fc40` a keresés). A feldolgozás naplója: „Processing Focus Contacts - %d found, updated %s” (`0x0058caa0`), „Processing Focus Groups - %d found, updated %s” (`0x0058b4e0`). A térkép a memóriában él; a lemezre mentés útja **NINCS MEG**.
- **Indítás.** A `DownloadContacts` (`0x0058a030`) hívója: `0x0058e750`. Mikor fut (indulás, időzítő, kérésre): **NINCS MEG**.
- **Gépeléskor (binárisból).** A 38.3 és 38.9 közvetlen hívottjai között nincs fájl-API. A `0x00643940` és a `0x007b7f00` mélyebb lánca **NINCS MEG** (`0x007b4990`, `0x007b5260`, `0x00491980`).
- **Online létrehozás (binárisból).** A vtábla `+0x24` slotja (`0x00589760`) „Create person contact: focus %s, result %d” naplóval hoz létre személyt a `Focus` (online) szolgáltatásban. Ha nem sikerül, 15 és 30 másodperc között várakozva újrapróbálkozik, legfeljebb négyszer (`_rand`, `(rand & 15) + 15` másodperc). Háttérszálú online művelet. Hogy a People OK-útja hívja-e: **NINCS MEG** (a `0x007bb660` hívottjai között nincs).

### 38.13 Összevetés a mi kódunkkal

| Téma | Eredeti (binárisból) | Nálunk | Teendő |
|---|---|---|---|
| Csempéből nyitás | `0x0085a1a0` tölti be a `/c/ui/ContactManager` erőforrást; hívó `0x00720dd0`; a csempe útja NINCS MEG | `UnnamedFacesView.qml` `submitName` → `root.nameSubmitted`; `Main.qml:3690-3692`; `PeopleManagerDialog.openForFace` | 38.11, 10. és 14. tétel |
| Előtöltés | NINCS MEG (megnyitó útvonal); job-167 szerint előtöltve és kijelölve | `beginSession`: `initialSearch` előtölti; egyező név kijelölése; egyébként nincs kijelölés | a kódban nincs teendő |
| Lista szűrése | `search` ág: `0x007bb660` → `0x007b7f00` → `0x007b81e0`; a szabály NINCS MEG | `filteredEntries`: a név részsztring, kis- és nagybetű független, ékezet-érzéketlenség nincs | a szabály a `0x007b4990` után |
| Sor-felirat | `* ` előtag módosított sornál; `%s, %s` vagy `%I64x` névtelennél | a név, `* ` nélkül | 9. teendő |
| New Person | validál, állapot `3`, a `search` szöveg a névnek megy (következtetés), kijelölés `0`, fókusz `fullname` | `addPerson`: draft sor a `searchField` szövegével, fókusz a `nameField`-re | 1. teendő (duplikátum) |
| Név szerkesztése | `0x007b8d20`: rekord-írás, módosított bit, újracímkézés | `_updateSelected`, csak a másolatban | nincs |
| E-mail | `emails`; engedélyezés a `0x00588460`-tól (NINCS MEG) | csak ha `localContactIds` nem üres | a `0x00588460` után |
| Duplikátum jóváhagyáskor | mód `3`: `DupNameMsg` / `DupEmailMsg`, Igen/Nem | nincs | 1. teendő |
| Üres név | `EmptyContactMsg`, visszaállítás | `canCommit()` hamis, az OK tiltott, nincs üzenet | 2. teendő |
| Mentési hiba | `Failed to update person!` | `savePeopleManagerChanges` hamis → csendes `return` | 3. teendő |
| Revert | `revert` → `0x007bb370` (szerep NINCS MEG); engedélyezés a módosított bitre | `revertSelected`; engedélyezve, ha van kijelölés | 4. teendő |
| Delete | `ConfirmDelete` + „Don't warn me” (Preferences) + online figyelmeztetés | azonnal törli a másolatból | 5. teendő |
| OK / Choose | ugyanaz a `ok` parancs; a felirat: `[0x57]` és név-egyezés; a felirat íróit NINCS MEG | `Choose`, ha arcmódban van kijelölt, nem új sor | 6. teendő |
| Mégse | bezárás, nincs validálás | `close()`, nincs kérdés | egyezik |
| Sync Face Tags | élő vezérlő, állapotbitek | tiltott | döntés (online funkció) |
| Manage Online / Refresh | URL-nyitás, mentés-kérdés; folyamatjelző | tiltott | döntés |
| Csempe-javaslat: lista | `0x00643940`, forrás `0x00491980`; nincs korlát; forrás-sorrend | `refreshNameSuggestions`: teljes lista, név szerint rendezve (`peopleManagerContacts`); nincs korlát; a popup 170 px magas | a korlát és a sorrend NINCS MEG |
| Csempe-javaslat: egyezés | NINCS MEG (`0x007b4990`) | részsztring, `toLocaleLowerCase` | a `0x007b4990` után |
| Csempe-javaslat: billentyűk | `0x00809050`: Fel/Le/Enter elfogadja a kijelöltet; körbefutás jelző | Enter a beírt szöveget küldi (`submitName(text)`); a listán nincs billentyűkezelés | 7. teendő |
| Csempe-javaslat: kattintás | `0x006436b0` → `0x0044d650` (célja NINCS MEG) | `MouseArea` → `submitName(personName)` (#5285) | élő mérés |
| Csempe-javaslat: kép | NINCS MEG | `thumbUrl` vagy `icons/person-silhouette.svg` | 13. Ghidra-tétel |
| Névjegytár betöltése | memória-tömb (`this+0x38`), háttérsor (`ytAsyncQueue`), online letöltés | `peopleManagerContacts()` minden hívásra megnyitja az adatbázist és minden mappa `.picasa.ini`-jét | 8. teendő |

### 38.14 Megvalósítás előtt: a teendők (sorrendben)

1. **Duplikátum új személynél:** név és e-mail egyezésnél Igen/Nem kérdés jóváhagyáskor (`PeopleManagerDialog.qml`, `commitChanges`). A szöveg a Picasa szövege, magyarul a `picasapy_hu.ts`-ben.
2. **Üres név:** üzenet és a sor visszaállítása (`EmptyContactMsg`), nem csak a tiltott OK.
3. **Mentési hiba:** a `savePeopleManagerChanges` hamis eredménye üzenetet adjon (`UpdateFailed` megfelelője), ne csendes visszatérés.
4. **Revert:** engedélyezés csak módosított sornál; a visszaállítás a mentett értékre. A `0x007bb370` szerepének tisztázása után.
5. **Delete:** megerősítő párbeszéd, „ne figyelmeztess” beállítás a PicasaPy beállításaiban. Az online figyelmeztetés feltétele NINCS MEG.
6. **OK / Choose felirat:** a binárisbeli szabály (`[0x57]` és név-egyezés) csak az írók azonosítása után változtatható. Addig marad a jelenlegi szabály.
7. **Billentyűk a javaslat-popupban:** Fel, Le és Enter (a kijelölt elem elfogadása). Előbb el kell dönteni, hogy a csempe popupja a `CAutoCompleteListBox` osztályt használja-e (NINCS MEG).
8. **Gyorsítótár (#5435 óta megvan):** a `peopleManagerContacts()` eredményét a `people_controller.py` tárolja, és csak mentéskor, frissítéskor vagy mappaváltozáskor számolja újra. A `refreshNameSuggestions` a tárolt listát olvassa. Indok: a bináris gépelési útja közvetlenül nem olvas fájlt, a mi kódunk minden gépelésnél megnyitja az adatbázist és minden `.picasa.ini`-t. (Mérés nincs; ez a kód-olvasásból adódó eltérés.)
9. **Sor-felirat:** a `* ` jel módosított sornál és a névtelen kontakt megjelenítése (`%I64x`) döntést kér. Nem tekintjük hibának.

**Mérés nélkül nem változtatandó:** a szűrési szabály, a sorrend és a korlát (38.11, 1-3. tétel).

### 38.15 Bizonyítottsági fok

- **Binárisból igazolt:** a vezérlők és a figyelők (38.1), a parancsok sorrendje (38.8), a validálás ágai (38.5), a sor-felirat fő szabálya (38.2), a csempe-lista vtábla-szerkezete és a popup billentyűi (38.9), a háttérsor vtábla-azonosítói (38.12).
- **Következtetés (hívási mintából):** a `* ` jel jelentése, a gombállapotok értelmezése, a `+0x10c` és `+0x7c` slotok szerepe, és hogy a `search` szövegből lesz az új név.
- **NINCS MEG:** a szűrési és egyezési szabály, a forráslista és a rendezés, a csempe-popup osztálya és képe, a Choose-szabály íróinak azonosítása, a névjegytár háttérszálának indítása, és a mentés lemezre írási útja.

### 38.16 Név-egyezés és rendezés (2026-10-21, #5437)

A következő két szabályt a `2026-10-21-people-egyezes.txt`,
`2026-10-21-people-egyezes2.txt`, `2026-10-21-people-szuro.txt` és
`2026-10-21-people-rang.txt` Ghidra-dumpok igazolják. Ez a pont a 38.11-ben
nyitva hagyott egyezést és rendezést pontosítja.

1. **Egyezési szabály.** A szöveg kisbetűs alakját kell összevetni. Az ASCII
   és a nem ASCII betűk kisbetűsödnek, de az ékezetek nem olvadnak össze:
   például az `é` nem egyezik az `e` betűvel. Szókarakter az ASCII betű,
   számjegy, kettőspont és minden nem ASCII karakter. Minden más ASCII
   karakter elválasztó, többek között a szóköz, kötőjel, pont, vessző,
   aposztróf és aláhúzásjel.

   Ha a gépelt keresés szavai `q[0..n-1]`, a név szavai pedig `w[0..m-1]`,
   akkor van egyezés, ha létezik olyan `i`, amelyre `q[0..n-2]` rendre pontosan
   megegyezik `w[i..i+n-2]` szavaival, és `q[n-1]` a következő névszó eleje.
   Egy keresőszó a név bármelyik szavának elejével egyezhet. Üres keresésnél
   minden név egyezik. Például a `ki` illeszkedik a `Kiss Anna` és az
   `Anna Kiss` névre, a `Nagykiss` névre nem; az `anna k` illeszkedik az
   `Anna Kiss` névre, a `kiss anna` nem; a `jean-p` illeszkedik a
   `Jean-Pierre` névre.

   A `people_name_matching.py` egyetlen tiszta Python-függvénye valósítja meg
   a szabályt. Ezt használja a csempe `nameSuggestions` javaslatlistája és a
   People ablak `filteredEntries` keresője is.

2. **Rendezés.** Nem üres keresésnél a rendezési kulcsok sorrendben:
   a még nem mentett, azonosító nélküli új személy; az a teljes név, amely a
   gépelt szöveggel kezdődik kisbetűs összevetésben; a névszavas egyezés; majd
   a döntetlen feloldása a név ASCII kisbetűs alakjával. A rendezés stabil.
   A binárisban látott két adatjelző (`0x007b4140`, `0x007b4120`) jelentése és
   a második lista névegyezése (`0x007b43e0`) nincs feltárva, ezért ezek nem
   részei a szabálynak. A szűrés után a névszavas egyezési kulcs minden
   megmaradó elemnél igaz.

   Üres keresésnél nincs új személy vagy prefix szerinti előresorolás; csak a
   név ASCII kisbetűs alakja dönt, stabil rendezéssel. Az ASCII kis-nagybetű
   különbségtől eltekintő összehasonlítás nem vonja össze az ékezeteket.

   A `CAutoCompleteListBox` `+0x20` jelzőjének értéke nincs megállapítva, ezért
   a javaslatlista Fel és Le billentyűje nem fut körbe. A kijelölt javaslat
   Enterrel fogadható el; kijelölés hiányában a mező gépelt szövege indul el.

### 38.17 A helyi autocomplete-dump: általános lista, csempe-kötés nélkül (2026-10-21)

**Forrás:** a privát referencia-repó `referencia/ghidra/2026-10-21-autocomplete.txt` fájlja; a bináris-index `rtti` táblája; helyi `annot_disasm.py` a `Picasa3.exe` `0x00809050` (482 bájt) és `0x00787dd0` (5279 bájt) függvényein.

- A `CAutoCompleteListBox::vftable` (`0x00cbd8ec`) RTTI-bejegyzése a `0x00809360`, `0x008095c0` és `0x00809050` címeket tartalmazza. A Ghidra-dumpban a `0x00809360` a lista kiválasztási indexét kezeli, a `0x008095c0` az elrejtési út. A `0x00809050` helyi diszasszemblálása a `VK_UP` (`0x26`), `VK_DOWN` (`0x28`) és `VK_RETURN` (`0x0d`) ágakat mutatja; a dump szerint Enterkor a kijelölt elemet adja át elfogadásra.
- A dumpban szintén szereplő `0x0063a5e0` a `TagPanel::vftable` (`0x00ca0a24`) RTTI-bejegyzésének egyik metódusa; a `0x0064f090` a `GeoPanel::vftable` (`0x00ca23c4`) metódusa. Mindkét függvény tartalmaz `CAutoCompleteListBox::show`/`hide` parancságat, de ezek a másik két panelhez tartoznak. A `0x0060f980` az `autocomplete::skipped`, `autocomplete::no_match` és `autocomplete::multi_match` üzenetekből hibajelentést készít az `AutocompleteErrorsDialog` számára; ez nem találatsor-rajzoló.
- **A két út egyezése:** A: a Ghidra C-dump a listbox kiválasztás/elrejtés és billentyűkezelési útját adja; B: az RTTI-adat a három címet a `CAutoCompleteListBox` vtable-jéhez rendeli, a helyi diszasszemblálás pedig megerősíti a billentyűkódokat. Ez az általános lista működését erősíti meg, nem a Név nélküliek csempemezőjének bekötését.
- **Cáfoló kísérlet:** azt a feltevést vizsgáltam, hogy a `show`/`hide` sztringek a csempe callbackjét bizonyítják. A címek RTTI-tulajdonosa `TagPanel`, illetve `GeoPanel`; ezért a sztringek önmagukban nem kötik ezeket a kezelőket a `faceclusterpanel_%d_addname` vezérlőhöz. Ugyanakkor az eredmény azt sem zárja ki, hogy a csempe ugyanazt az általános listbox-osztályt használja.
- **Bizonyítottsági fok:** az általános listboxhoz tartozó címek és billentyűágak **megerősítettek** (C-dump + RTTI + helyi asm). A csempemező konkrét popup-osztálya, sorra kattintásának célja, Escape-hatása és az arckép rajzolása **NINCS MEG**. Megszerzésükhöz célzott Ghidra-körben kövesd a `0x007853e0` és `0x007899e0` hívókat a `0x00787dd0`-től a vezérlő és a popup regisztrációjáig; a kattintás és Escape végső, látható hatását külön Colab-felvétellel kell mérni.

## 39. #5184, helyi Codex-kutatói kör (2026-10-21): N1, N3, N7 nyitva marad

**Keret.** Az eredeti Picasa helyi futtatója nem állt rendelkezésre (`wine` nincs), Colab-végrehajtó eszköz nem volt elérhető, ezért eredeti futásmérést nem végeztem. A mérőadat-archívumban nem volt a feladathoz tartozó csomag; nem bontottam ki, `.bt` ideiglenes fájl nem készült. GitHubot nem használtam.

### 39.1 N1: a helyi INI-korpusz nem válaszolja meg az eredeti felismerését

A `research/testdata` 71 `.picasa.ini` fájljának összesített feldolgozása 11 `faces` rekordot talált: 10 névvel ellátottat, 1 mellőzöttet, 0 `,0` rekordot. A privát helyi INI-korpusz pillanatképének aggregált feldolgozása 4 973 `faces=` sort, 8 713 rekordot, 6 022 névvel ellátott, 696 nullaazonosítós és 1 995 mellőzött rekordot talált; 361 sorban volt névvel ellátott és mellőzött arc együtt, névvel ellátott és nullaazonosítós arc együtt 0 sorban. **Forrás:** mérés (két helyi korpusz aggregált feldolgozása; személyes útvonalak és nevek nem kerültek a kimenetbe).

A nullaazonosítós `faces=...,0` bejegyzés nem arc: az eredeti `0`-olvasó `-1`-et ad (`0x0092c450`), a bontó pedig a bejegyzést a téglalappal együtt eldobja (`0x0049d560`). Az `ffffffffffffffff` a mellőzött arc értéke (`0x00484bc3`; §9/f). **Forrás:** bináris (Picasa3.exe, címek a táblában). Ezért a korpuszban talált vagy hiányzó nullaazonosítós sorból nem következik, hogy az eredeti talált-e ismeretlen arcot egy már megnevezett fotón. A PicasaPy ilyen, már azonosított arcot tartalmazó fotót kihagy a saját felismerésből (`src/picasapy/app/face_scan_controller.py:470-475`); ez csak a mi viselkedésünket igazolja.

### 39.2 N3: a Red.dll belső küszöbe és az eredeti felismerési arány NINCS MEG

A Red.dll-ben az alábbi pontos sztringek vannak: `MainSizeArr` (`0x101affbc`), `epi_CONFIDENCE` (`0x101b0130`), `soft confidence =` (`0x101b2638`), `object size ratio =` (`0x101b3250`). **Forrás:** bináris (Red.dll, megadott virtuális címeken kiolvasott sztringek). Ezek címkék, nem küszöbértékek; a `0x100057c0` belső útján lévő értékekhez és a tényleges döntési feltételhez nincs utasításszintű lelet.

A Preferences `FRSuggestionSingleThreshold=0,90` értéke (`0x0048ac6f`) nem bizonyítja, hogy a Red.dll detektorküszöbe is 0,90: a kép-futtató külön `FRRecommendIncludeLimit=0,50` szűrőt hasonlít (`0x0048e1f0`, `0x0048e33e`; §36.1). **Forrás:** bináris (Picasa3.exe, hivatkozott címek). Az eredeti és a PicasaPy felismerési aránya azonos, rögzített képkészleten mérve **NINCS MEG**.

### 39.3 N7: a People lista kijelölési módja nincs eldöntve

A `contactmgr.fen` `contacts` listája nem tartalmaz kijelölési módot; a `0x007b9630` ág egy kijelölt indexet olvas. **Forrás:** bináris (a People Manager erőforrása; Picasa3.exe `0x007b9630`). A job-186 felvétel egy kiválasztott személyt mutat, de nem próbál második sort Ctrl-kattintással hozzáadni. Ezért a többes kijelölést nem zárja ki; N7 nyitott.

### 39.4 A #5184-ben felsorolt pontok aktuális állapota

| Pont | Eredmény | Bizonyíték |
|---|---|---|
| N1 | ⛔ Nyitott | Az eredeti runtime-kimenet NINCS MEG; a helyi INI-adatok nem tárolják bizonyítóan az ismeretlen arcokat (§39.1). |
| N3 | ⛔ Nyitott | Az eredeti belső méretezési/döntési értékek és a pontos felismerési arány NINCS MEG (§39.2). |
| N4 | ✅ Lezárt | Job-187: névvel ellátott arcon alapból nincs keret és név. |
| N5 | ✅ Lezárt | Job-222..226, §§37.10-37.11: személyszintű mellőzés nincs; a mellőzés arcszintű. |
| N6 | ✅ Lezárt | Job-222/224, §37.10: a személy törlése eltávolítja a `faces=` sort, a `[Contacts2]` sort megtartja; a Cancel az alapértelmezett. Javítás: #5391. |
| N7 | ⛔ Nyitott | Job-186 csak egy sort mutat; a Ctrl-többes kijelölést nem tesztelte (§39.3). |
| N8 | ✅ Lezárt | Job-186: People Manager referenciafelvétele (631×351), lásd a jegyhez adott felvételi leírást. |

### 39.5 Két független út és cáfoló kísérletek

**Összesített bizonyítottsági fok: nyitott.** A helyi korpuszok aggregált mérése (A út) és az eredeti parser utasításszintű kezelése (`0x0092c450`, `0x0049d560`; B út) egymástól függetlenül mutatja, hogy az INI-korpusz nem használható az N1 bizonyítására; egyik sem mondja meg, mit ismert fel az eredeti futás. N3-nál a Preferences összehasonlító útja és a Red.dll sztringei külön forrásból származnak, de egyik sem ad belső küszöbértéket. N7-nél a bináris egy indexet olvasó ága és az erőforrás kijelölésimód-jelző nélküli listája nem bizonyítja a vezérlő többes kijelölési képességét.

- **Cáfoló kísérlet, N1:** próbáltam a nullaazonosítós `faces=...,0` adatot ismeretlen arcnak tekinteni. A §9/f parser-szabálya ezt cáfolja: a rekord nem kerül be arcként; a mért korpuszban nincs olyan sor, amely névvel ellátott és nullaazonosítós arcot együtt tartalmazna. Az ellenpróba ugyanazzal a mércével történt: az ini rekord nem az eredeti felismerési kimenet, N1 nyitva marad.
- **Cáfoló kísérlet, N3:** próbáltam a `FRSuggestionSingleThreshold=0,90` értéket az eredeti arcdetektor küszöbével azonosítani. A külön `FRRecommendIncludeLimit=0,50` összehasonlító út és a Red.dll belső címkéi nem kapcsolják a 0,90-et a detektor döntéséhez; az azonosság nem áll meg. Az ellenpróba sem adott belső pontszámot vagy küszöböt, ezért N3 nyitva marad.
- **Cáfoló kísérlet, N7:** az egyetlen indexet olvasó ág alapján felmerülhet az egyszeres kijelölés. Ellenőriztem az ellenpéldát: az erőforrás nem rögzít kijelölési módot, és nincs Ctrl-kattintásos felvétel. Így az egyszeres kijelölés következtetése nem igazolható; N7 nyitva marad.

### 39.6 Következő döntő mérés és jegyjavaslat

Az N1-hez rögzíteni kell egy fotót, amelyen egy arc már névvel szerepel és van mellette legalább egy külön, névhez nem rendelt arc; a felvétel mutassa az eredeti találatát és az előtte/utána állapotot. Az N3-hoz ettől különálló, előzetes arccímkéktől mentes, pontosan felsorolt képkészlet kell, képenkénti ellenőrzött arcjelölésekkel. Ugyanazokat a képeket kell feldolgoztatni az eredetivel és a PicasaPy YuNetjével a feladatban megadott 960 px / 0,9 beállítással; a nyers találatlistákból, csak a tényleges képkészlet nevezőjével számolható összehasonlító arány, extrapoláció nélkül. Az N7-hez legalább két személy sorát kell megjeleníteni, az első kijelölése után Ctrl-kattintással a másodikat is kijelölni, majd a lista és a Delete Person gomb állapotát rögzíteni; a törlést a felvételben Mégsével kell megszakítani.

**Fejlesztési következmény:** nincs igazolt eredeti/PicasaPy eltérés, ezért nincs kódmódosító fejlesztői lista vagy új fejlesztői jegy. Új kutatási jegy sem kell: az N1, N3 és N7 a #5184 nyitott részei maradnak.

**Nyitott:**
- `Ghidra-kör kell: 0x100057c0 - a Red.dll feldolgozó bemeneti mérete, confidence értéke és tényleges elfogadási küszöbe hogyan kerül felhasználásra a döntő ágban? [blokkoló]`
- Colab-felvétel kell az N1 és N3 tényleges felismerési kimenetéhez és az N7 Ctrl-többes kijelöléséhez.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (39. szakasz); `docs/specs/00-index.md` (#5184 aktuális állapotának rövid összefoglalója). Kódhoz és tesztekhez nem nyúltam.

## 40. #5184, helyi Codex-kutatói kör: a Red.dll döntési útja és N1/N3/N7 státusza (2026-10-21)

**Keret.** Az eredeti Picasa helyben nem futtatható (`wine` nincs), Colab-felvétel nem volt elérhető, ezért az eredeti program viselkedéséről nem készült új mérés. A mérőadat-archívum vizsgált taglistájában nem volt #5184-hez tartozó felvétel; nem bontottam ki semmit, ideiglenes fájl nem készült. A helyi bináris indexet, a meglévő Ghidra-leleteket és az eredeti Red.dll-t vizsgáltam. A teljes Red.dll `.text` pásztázása a `paszta.py` eszközén keresztül, `paszta.memoria_kapu()` első műveletként futott.

### 40.1 N1: a névvel megjelölt fotó további arca továbbra is eldöntetlen

**Bináris út.** A felismerési kapu `0x00414940` hívja a képenkénti útvonalat, `0x0048ef20`-at. A meglévő dekompilációban a képenkénti út az állapotot, gyorsítótárat és a detektálásból visszaadott jelölteket kezeli; benne nem látszik közvetlen személynév-összehasonlítás. A jelöltgyűjtés `0x0048af60` útján a `0x0048bae0` az indexkulcs rekordját ellenőrzi, nem kontaktnevet. A munkaszál kezelője `0x004987c0` a `0x0047b020`-at hívja; ez a munkatétel állapotától függően a felismerési kapuhoz vagy a képenkénti útvonalhoz jut. Ezekből nem következik, hogy a név szerinti kizárás nincs egy korábbi sor-összeállítóban vagy a meg nem értett munkatétel előállításakor.

**Független ellenőrzés.** A helyi INI-korpuszban előfordul névvel ellátott és mellőzött arcot együtt tartalmazó sor, de az INI a mentett arckijelölést írja le, nem az eredeti futás összes detektálását. A `,0` rekord nem bizonyít ismeretlen arcot: a `0x0092c450` olvasó és a `0x0049d560` bontó eldobja. A két út egyező eredménye: az elérhető statikus út és az INI-adat nem dönti el az N1-et.

**Cáfoló kísérlet.** Próbáltam a képenkénti útban olyan feltételt találni, amely a nevet vagy a névjegy azonosítóját vizsgálja. A `0x0048ef20` olvasata és a külön indexrekord-ellenőrzés (`0x0048bae0`) nem mutat ilyet. Ez a cáfoló ugyanazzal a mércével csak a megvizsgált függvényekre érvényes; a teljes felismerési sorra nem általánosítható.

**Eredmény: NEM DÖNTHETŐ EL.** Döntő felvétel: egy fotón egy már névhez rendelt és egy név nélküli arc, összevetve ugyanannak a fotónak a korábban nem feldolgozott, név nélküli kontrollállapotával; a felvétel rögzítse a detektált arcokat és az előtte/utána `faces=` adatot. A `0x004987c0` Ghidra-dekompilációja tisztázhatja a munkatétel kezelését, de a futásmérést nem helyettesíti.

### 40.2 N3: a Red.dll pontszámot ad vissza, a végső küszöb és méret nincs meg

**Bináris út.** A Picasa Red-hídja (`0x006cde50`) a vtable `+0x44` metódusát hívja; a Red.dll `0x10001570` belépője továbbadja a hívást a `0x100057c0` rutinnak. A `0x100057c0` bemeneteket ellenőriz, majd jelöltenként meghívja a kapott objektum vtable `+0x40` metódusát (`0x10005858` környéke), és az egy jelölthöz tartozó pontszámok maximumát teszi a kimenetbe. Ebben a rutinban nem látszik képméretezés vagy a végső elfogadást eldöntő küszöb-összehasonlítás. A callback célja és az azt meghívó konfigurációs út nincs meg, ezért a rutinból nem állapítható meg a detektor küszöbe.

**Független ellenőrzés.** A teljes Red.dll `.text` utasításszintű pásztázásában a `MainSizeArr` címkének egy, az `epi_CONFIDENCE` címkének két közvetlen hivatkozása van; ezek paraméternevek, nem értékek. A 960 decimális értéknek megfelelő `0x3c0` két találata pointer-eltolásként jelenik meg, nem képméretként. A 0,9 IEEE-754 értékének (`0x3f666666`) közvetlen utasításbeli előfordulása nulla. Ez a pásztázás az utasítások közvetlen értékeit fedi le; nem zár ki adatból, konfigurációból vagy futás közben feloldott callbackből származó értéket. A Picasa oldali `FRSuggestionSingleThreshold=0,90` (`0x0048ac6f`) és `FRRecommendIncludeLimit=0,50` (`0x0048e1f0`, összehasonlítás `0x0048e33e`) külön, javaslatszűrő értékek; egyik sem bizonyítja a Red detektorküszöbét. A két út egybehangzóan azt mutatja, hogy pontos Red-küszöb és bemeneti méret nincs meg.

**Cáfoló kísérlet.** Megvizsgáltam azt az ellenérvet, hogy a Picasa `0,90` beállítása a Red küszöbe, illetve hogy a Red `.text`-ben talált `0x3c0` a 960 képpontos célméret. Az első érték a Picasa oldali javaslatszűrőhöz tartozik; a két `0x3c0` találat pointer-eltolás. Az ellenpróba nem kapcsolja ezeket a Red döntéséhez, ezért az azonosság nem áll meg. A közvetlen találatok hiánya nem bizonyítja, hogy a méret vagy küszöb máshol sincs.

**Eredmény: NEM DÖNTHETŐ EL.** A felismerési arányhoz azonos, tételes képkészlet, képenként ellenőrzött arccímkék és mindkét program nyers találatai kellenek. A méret és a küszöb bináris úton való lezárásához a `0x100057c0` vtable `+0x40` callback tényleges célját és döntési ágát kell dekompilálni, majd a bemeneti méretet adó hívót azonosítani. A PicasaPy 960 px / 0,9 beállítása csak összehasonlítási alap, az eredeti Picasa értékének nem bizonyítéka.

### 40.3 N7: a Név nélküliek többes művelete igazolt, a People Manager modellje nyitott

**People Manager.** A `contactmgr.fen` `contacts` listája nem deklarál kijelölési módot. A `0x007b9630` a változáskezelésben egy aktuális indexet olvas, a `0x007ba820` törlési út pedig az aktuális személyen dolgozik. A job-186 felvétel egy személyt mutat. Ezek összeillenek az egyszeres kijelöléssel, de nem bizonyítják, hogy a vezérlő tiltja-e Ctrl/Shift többes kijelölést. Függetlenül nézve az erőforrás és az egy-indexes kódút sem ad többes kijelölésre tiltást, a job-186 pedig második sort nem próbál ki. A két út egyezik abban, hogy a kijelölési mód nem dőlt el.

**Név nélküliek.** A `0x006470d0` a kijelölt elemek listáján iterál; a job-180 felvételén Ctrl+A hat csempét jelölt ki. Ez igazolja, hogy a nézetben a többes kijelölés és több kijelölt elemre alkalmazott művelet létezik. A korábbi felvétel nem döntötte el a Ctrl-kattintás és Shift-kattintás pontos viselkedését.

**Cáfoló kísérlet.** A People Manager egy-indexes ágából egyszeres kijelölésre következtettem volna. Az erőforrás nem tartalmaz erre vonatkozó módjelzőt, a job-186 nem teszteli a második sort, így ezt a következtetést nem lehet igazolni. A Név nélküliek Ctrl+A felvétele ezzel szemben cáfolja azt az általános állítást, hogy minden arclista csak egy elemet enged kijelölni. Ugyanazt a mércét alkalmazva: a Név nélküliek többes kijelölése megerősített, a People Manageré nyitott.

**Eredmény.** A Név nélküliek: többes kijelölés igazolt (`0x006470d0`, job-180); a Ctrl/Shift részletek nyitottak. A People Manager: NEM DÖNTHETŐ EL; legalább két személyt kell megjeleníteni, a másodikra Ctrl-, majd külön Shift-kattintást végezni, és rögzíteni a kijelölést, a Delete Person gomb állapotát, majd a törlést Mégsével megszakítani.

### 40.4 A #5184 „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték |
|---|---|---|
| N1, névvel ellátott fotón további ismeretlen arc | ⛔ Nyitott | A `0x0047b020` munkatétel `+0x10` jelzője miatt a képenkénti út elmaradhat; hogy ez névvel jelölt fotót kizár-e, NINCS MEG; §41.1. |
| N3, eredeti felismerési arány, küszöb és méret | ⛔ Nyitott | A `0x100057c0` callback-pontszámokat rangsorol; a callback döntése, a bemeneti méret és a mérési arány NINCS MEG; §41.2. |
| N4, alapértelmezett keret és név | ✅ Lezárt | Job-187: a névvel ellátott arcon alapból nincs keret és név; §39. |
| N5, személyszintű mellőzés | ✅ Lezárt | Job-222..226 és §37.11: ilyen funkció nincs, a mellőzés arcszintű. |
| N6, személy törlése | ✅ Lezárt | Job-222/224 és §37.10: a `faces=` adat törlődik, a `[Contacts2]` sor megmarad, a Mégse az alapértelmezett; javítás #5391. |
| N7, kijelölési modell | ⚠️ Részben lezárt | Név nélküliek: többes kijelölés igazolt (`0x006470d0`, job-180). People Manager és a Ctrl/Shift részletek nyitottak; §40.3. |
| N8, People Manager referencia | ✅ Lezárt | Job-186: 631×351 referenciafelvétel és ablakleírás; §39. |

**Bizonyítottsági fok: nyitott.** Két egymástól független statikus/dinamikus út egyik nyitott pontra sem ad teljes választ. Ahol két út összevethető volt, az egyező eredmény a bizonyíték elégtelensége volt, nem az eredeti viselkedés eldöntése. Az Név nélküliek többes művelete megerősített, de nem zárja le a People Managerre és az egérmódosítókra vonatkozó N7-et.

**Fejlesztési következmény:** nincs bizonyított eltérés az eredeti Picasa és a PicasaPy között az N1, N3 vagy a People Manager N7 ponton, ezért fejlesztői jegy és kódlista nem indokolt. Új kutatási jegy sem szükséges: a megmaradt kérdések a #5184-ben vannak.

**Nyitott:**
- `Ghidra-kör kell: 0x100057c0 - a [param_3+8]+0x74 objektum vtable +0x40 callbackjének tényleges célja, a döntési küszöb és az azt beállító méret-adat útja; a Picasa3.exe hívó 0x006cde50 [blokkoló]`
- **A munkaszál útja részben feltárt (41.1):** a `0x004987c0` és `0x0047b020` C-dumpja megadja a sorba állítás és a képenkénti hívás útját, de a munkatétel `+0x10` jelzőbájtjának jelentése NINCS MEG. Az eredmény arról, hogy a már megnevezett fotón a futó eredeti talál-e további arcot, Colab-felvételt igényel.
- Colab-felvétel kell N1-hez, az eredeti felismerési arányhoz és mérethez, valamint a People Manager és Név nélküliek Ctrl/Shift viselkedéséhez.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (40. szakasz); `docs/specs/00-index.md` (#5184 friss állapota). Kódhoz és tesztekhez nem nyúltam.

## 41. #5185, 2026-10-21: a Ghidra-kérések részleges lezárása

**Hatókör.** A négy átadott dekompiláció és a helyi diszasszemblálás alapján a 37.9/b régi állításait javítom. A People Manager `Delete Person` útjának közvetett folytatása és az `Ignore Person` adatkulcsa továbbra sem dőlt el. Minden cím a Picasa3.exe 3.9.141.259 betöltési címe.

### 41.1 `0x00692210`: két gyűjteményosztály közös metódusa, a törlés utáni futás nyitott

`0x00692210` a `param_1+0x1b0` elemtömbjén iterál, majd elemről elemre a `0x0069b240` mentést hívja. A bináris RTTI két, azonos slotot tartalmazó vtable-t nevez meg: `AlignedImageCollection::vftable` (`0x00ca7d8c`) és `PrepareCollection::vftable` (`0x00ca7c54`). Mindkét vtable-ben a függvény a `+0x6c`, azaz 27-es indexű slotban áll (1-től számozva a 28. bejegyzés). Ez a kód tehát nem a `ContactManagerDlg` metódusa, hanem a két gyűjteményosztály közös művelete.

A People Manager `Delete Person` kezelője `0x007b99a0`-ból hívja a `0x007ba820`-at. A törlési ág a `0x005836f0` és a `0x00584cc0` segédeket hívja, majd eltávolítja az aktuális sort. A vizsgált statikus út közvetlenül nem hívja a `0x00692210`-et. A `0x005836f0` és `0x00584cc0` további virtuális hívásai nincsenek végigkövetve, ezért a későbbi, közvetett futás **NINCS MEG**.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `0x00692210` a `AlignedImageCollection` és a `PrepareCollection` közös vtable-slotja, `+0x6c` (index 27). A Delete Person közvetlen útja nem hívja; utólagos virtuális hívás nem kizárt. | Nincs azonos nevű gyűjteményosztály a People Manager útjában; a PicasaPy saját kontakt- és arcadat-szolgáltatásokat használ (`people_controller.py`, `face_scan_controller.py`). | A futás eldöntéséig nincs kódváltoztatás. Következő statikus cél a `0x00584cc0` és `0x005836f0` virtuális hívási útja; futásidejű állításhoz Delete Person utáni eredeti felvétel vagy trace kell. |

### 41.2 `albumcontactids`: első olvasáskor kérdezi le, a PMP-adatot csak meglévő, 1-es állapotú rekord olvassa be

A `0x00415790` konstruktorlánca a `0x00495360`-on keresztül `albumcontactids` nevű oszlopot hoz létre. A személyalbum-ág a `0x00448fb0`-ban olvassa ezt az oszlopot. Ha az oszlop kimeneti mutatója még null (`[this+0x2754] == 0`), a kód a virtuális `+0x18` sloton keresztül a `0x00495be0` betöltőhöz jut. Ez a `CColumn` metódus zárol, majd null kimenetnél meghívja a `0x00499610`-et. Az utóbbi `0x13320004` kulccsal kérdezi le a property rekordot (`0x00499629`), a kimeneti rekordot `[esi+0x54]`-be, a rekord `+0x284` címét `[esi+0x58]`-ba teszi (`0x0049963e`, `0x00499648`).

A PMP-fájl tényleges olvasása egy további, feltételes lépés: a `0x006a41e0` találati ága a bit 0 beállított rekordnál hívja a `0x006a7090`-et, amely `+0x08 == 1` esetén meghívja a `0x006a2cd0` olvasót. Az új rekord állapota 2, így az újonnan létrehozott rekord ezen az ágon nem olvas PMP-fájlt. Tehát a személyalbum adatútja a null első olvasásakor inicializálja az oszloplekérdezést; PMP-tartalom csak akkor töltődik, ha a megtalált rekord meglévő, 1-es állapotú.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `albumcontactids` lekérdezése a `0x00448fb0` személyalbum-út első oszlopolvasásakor indul; a `0x13320004` property PMP-tartalma a rekord állapotától függően töltődik (`0x00495be0`, `0x00499610`, `0x006a41e0`, `0x006a7090`, `0x006a2cd0`). | Az `albumcontactids` oszlopnévnek nincs közvetlen megfelelője a `src/picasapy/` alatt; a PicasaPy saját adatbázis-sémát és általános PMP-importert használ. Ez önmagában nem bizonyít felhasználói viselkedésbeli eltérést. | Nincs igazolt megvalósítási eltérés, ezért nincs teendő a kódban. |

### 41.3 `Ignore Person`: a menüparancs kezelője ismert, a `0x1332000x` kulcs nem

A `0x0056c5a0` helyi menü-összeállító a `0x13d` kontextuságban felveszi az `ID_IGNOREPEOPLE` parancsot (`0x0056c5a0`, a sztring feloldása és `0x00562930` menühozzáadás). A bináris ugrótábla a `0x9c9a` parancsot a `0x005cbaef` címre irányítja; ez a blokk a `0x005c9b00` kezelőt hívja (`0x005cbb14`). A kapcsolat két ellenőrizhető eleme: a menüépítő a `0x9c9a` parancsot engedélyezi, az ugrótábla `0x5cdb8c` bájtja a `0x5cd9fc` táblán keresztül a `0x5cbaef` célra mutat.

A `0x005c9b00` a `.picasa.ini` feldolgozó út része, és meghívja a `0x006a0d30` vektormásolót. A megvizsgált útból nem vezetett le `0x1332000x` kulcs. A `0x006a5590` más függvény, amely bizonyítottan `0x13320004` kulccsal dolgozik, de a `0x005c9b00`-ból hozzá vezető hívás nem igazolt. A `0x005c9b00` virtuális hívásai miatt nem állítom, hogy az útban sehol sincs további property írás.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Az `ID_IGNOREPEOPLE` a `0x9c9a` parancsazonosítón át a `0x005c9b00` kezelőhöz jut. Az általa írt PMP/property-kulcs **NINCS MEG**. Az arc-szintű `.picasa.ini` mellőzés mért jele `ffffffffffffffff` (job-210, 34.11). | A `PeoplePanel.qml` egy arcra hívja a `faceScanController.ignoreFaces` műveletet (`PeoplePanel.qml:230`, `face_scan_controller.py:1180`), amely ugyanezt a `ffffffffffffffff` arc-jelölőt írja a `.picasa.ini`-be. | A mért arc-szintű viselkedés egyezik; property-kulcs eltérés nem igazolt. Következő bináris cél: `0x006a0d30` vektorának eredete és hívóobjektuma, majd annak virtuális írója. |

### 41.4 `0x006a5590`: a `0x13320004` rekord 8 bájtos elempárjának írója

A `0x006a5590` a `0x006a41e0` lookupot `0x13320004` kulccsal hívja (`0x006a55fc`). A sikeres lookup után zárolja a rekord `+0x284` alobjektumát, majd a rekord `+0x2cc` tömbjének `in_EAX` indexű, 8 bájtos elemében összehasonlítja és szükség esetén beírja a `param_3` és `param_4` dword értékeket (`0x006a56f5`-`0x006a5705`). Eltérés esetén a `0x006a2a60` gyorsítótár-érvénytelenítőt hívja. A `+0x284` alobjektum `+0x20` és `+0x24` tagjai a szálazonosító és a zárszámláló; ezek csak a zárolás részei, nem a teljes művelet.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A `0x006a5590` a `0x13320004` property rekord `+0x2cc` tömbjének egy 64 bites elemét írja, index szerint. Közvetlen hívói: `0x00431570` és `0x00441ed0`. | A PicasaPy forrásban nincs közvetlen `albumcontactids` nevű tároló vagy ennek a PMP-rekordnak megfelelő adatmező; a PMP-t általános importkód olvassa. | Ez a belső adatmodell különbsége, megfigyelt felhasználói eltérés nélkül. Kódváltoztatás nem igazolt. |

### 41.5 Bizonyítottság, két út és cáfoló kör

**Összesített fok: feltételes.** A két gyűjteményosztály-slot, az `albumcontactids` első olvasási útja és a `0x006a5590` adatírása megerősített. A `Delete Person` utáni közvetett futás és az `Ignore Person` által írt property-kulcs nyitott, ezért a teljes kör nem tekinthető lezártnak.

- **A út, dekompiláció:** a `0x00692210`, `0x00495be0`, `0x0056c5a0` és `0x006a5590` C-törzsei, továbbá a törlési út `0x007ba820` -> `0x005836f0` -> `0x00584cc0` hívásai.
- **B út, bináris adatok és helyi diszasszemblálás:** a két RTTI-vtable `0x00692210`-slotja; a `0x00499610` `0x13320004` argumentuma és rekordmutatói; a `0x005cb990` ugrótáblája; a `0x006a5590` elempáríró utasításai. A loader-ágat a külön `0x006a41e0`, `0x006a7090` és `0x006a2cd0` kódjai egészítik ki. Az A és B út a lezárt részeken egyezik.
- **Cáfoló kísérlet:** próbáltam megcáfolni, hogy a `0x006a5590` a mellőzés írója. A `0x9c9a` parancs a diszpécserben a `0x005c9b00`-hoz jut, amelynek megfigyelt közvetlen segédje `0x006a0d30`; a `0x006a5590` közvetlen hívói a `0x00431570` és `0x00441ed0`. Ez a vizsgált statikus út nem igazolja a feltételezett kapcsolatot, de a virtuális hívások miatt nem cáfolja teljesen. Ugyanezzel a mércével a `0x13320004` Ignore Person-kulcs nyitva marad.

### 41.6 A kiegészítés „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték |
|---|---|---|
| 1. `0x00692210` objektuma és Delete Person utáni futása | ⚠️ Részben | Az objektumosztályok megerősítettek; a törlés utáni közvetett futás NINCS MEG (§41.1). |
| 2. Ki és mikor olvassa az `albumcontactids` táblát | ✅ | Első oszlopolvasás: `0x00448fb0` -> `0x00495be0` -> `0x00499610`; PMP-fájl csak meglévő, 1-es állapotú rekordnál (§41.2). |
| 3. Ignore Person által írt `0x1332000x` kulcs | ⛔ Nyitott | A menüparancs útja a `0x005c9b00`-ig bizonyított; a kulcs és a virtuális író NINCS MEG (§41.3). |
| 4. A `+0x284` objektum adatmezőinek írója | ✅ | `0x006a5590`, kulcs `0x13320004`, elemírás a rekord `+0x2cc` tömbjében (§41.4). |
| 5. PicasaPy-eltérés és teendő | ⚠️ Részben | Arc-szintű ignore jelölő egyezik a mért eredetivel; a People Manager törlés utáni hívási útja és az Ignore Person property-kulcsa nyitott, így ezek viselkedés-összevetése hiányos. |

**Nyitott:**
- `Ghidra-kör kell: 0x00584cc0 - a Delete Person utáni virtuális callbacklánc eléri-e a 0x00692210-et [blokkoló]`
- `Ghidra-kör kell: 0x006a0d30 - az Ignore Person út vektormásolójának tárolója, virtuális írója és esetleges 0x1332000x kulcsa [blokkoló]`
- Az Ignore Person kör Colab-felvétele a 0x9c9a parancs után a `.picasa.ini`, PMP és db3 változásával együtt kell, ha a bináris virtuális útja nem zárható le.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (37.9/b helyesbítés és 41. szakasz). Kódhoz és tesztekhez nem nyúltam.

## 42. #5184, helyi Codex-kutatói kör (2026-10-21): a munkatétel, a Red.dll és a kijelölés

**Keret.** A vizsgált Ghidra-bemenet: `/tmp/claude-1000/-home-sancho-Documents-PicasaPy/d86876a8-e263-4853-bac9-646a0ac9656a/scratchpad/2026-10-21-arc-5184.txt`, benne a `0x004987c0`, `0x0047b020`, `0x00495be0` és `0x0056c5a0` függvényekkel. A `Red.dll` helyben olvasható, ezért a `0x100057c0` célfüggvényt a helyi `pefile` és Capstone eszközzel, kizárólag a célcím környezetében diszasszembláltam. A mérőadat-archívum fájllistájában a `5184`, `5185`, `face`, `person`, `people` és megadott job-minták egyikére sem találtam illő nevet; nem bontottam ki semmit, `.bt` ideiglenes fájl nem készült. GitHubhoz, kódhoz és tesztekhez nem nyúltam.

### 42.1 ⚠️ N1: a munkatétel állapotjelzője és a tényleges arctalálat nyitott

**A munkasor útja.** A `0x004987c0` leemel egy sort a belső munkasorból, majd a `0x00498933` helyen meghívja a `0x0047b020`-t. A munkaszál-kezelőben nem látható név vagy kontakt-azonosító összehasonlítás. A `0x0047b020` a munkatétel nem-nullaságát és állapotmezőit ellenőrzi. Ha a bájt `+0x10` nem nulla, `0x0048bd80`-at hív és visszatér; a nulla ág továbblép a további kapukhoz. Az `+0x10` bájt jelentése és írója NINCS MEG. Az engedélyező `FRAddSuggesetions` ág a `0x0048ef20` képenkénti útvonalat hívja (`0x0047b149`). A teljes, 379 bájtos helyi diszasszemblálás megerősíti az állapotvizsgálatot, az ágakat és a `0x0048ef20` hívását. Forrás: a Ghidra-dump `0x004987c0` része, 22-203. sor; `0x0047b020` része, 222-291. sor; bináris `0x0047b020` `0x0047b020`-tól `0x0047b19a`-ig.

**Korlát.** A vizsgált kódban nincs közvetlen név- vagy kontakt-azonosító összehasonlítás, de az ismeretlen jelentésű `+0x10` jelző a `0x0048ef20` hívása előtt másik ágra visz. Ezért nem állapítható meg, hogy a már megnevezett fotót kizárja-e, és az sem, hogy a `0x0048ef20` eredménye új, név nélküli arcot tartalmaz-e. N1 végső válasza **NINCS MEG**. Döntő mérés: ugyanazon fotó, egy névhez rendelt arccal és egy külön név nélküli arccal; rögzíteni kell az eredeti találatot és az előtte/utána `faces=` sort, kontrollként ugyanazt a fotót korábbi arckijelölés nélkül is futtatva.

**Bizonyítottság.** A két vizsgált függvény vezérlési útja **feltételes**: a Ghidra C-dump és a helyi diszasszemblálás egyezik, de ugyanazt a bináris utat mutatja, tehát nem két független bizonyítás. Az `+0x10` írója, a jelző jelentése és az N1 runtime-eredménye **nyitott**.

### 42.2 ⚠️ N3: a Red.dll elérhető, a `0x100057c0` pontszám-rendező, nem a végső küszöb

**A Red.dll rutinja.** A DLL kép-alapcíme `0x10000000`; a `0x100057c0` a `.text` szakaszban van. A rutin két tömbön jár, jelöltenként meghívja a `[param_3+8]+0x74` objektum `vtable+0x40` slotját (`0x10005847`-`0x10005859`), a visszakapott lebegőpontos értékek közül a legnagyobbat választja, és azt a kimeneti tömbbe írja (`0x100058d2`-`0x100058d8`). A `0x100057c0`-tól `0x1000590d`-ig tartó vezérlési útban nincs olyan konstans-összehasonlítás, amely elfogadási küszöböt adna, és nincs képméretező művelet. Ez a rutin az értékeket rangsorolja; a detektor elfogadási döntését és bemeneti képméretét nem adja meg.

**Hívási lánc.** A Picasa3.exe `0x006cde50` a Red objektum `vtable+0x44` metódusát hívja (`0x006cdf03`-`0x006cdf06`). A Red.dll `0x101aadc4` vtable-jének `+0x44` bejegyzése `0x10001570`; ez a csomagoló a `0x100057c0`-t hívja (`0x100015a2`). A Picasa oldali hívó tehát azonosított, de a callback tényleges célja és az azt vezérlő méretadat forrása **NINCS MEG**.

**N3 eredmény.** Az eredeti felismerési küszöb, bemeneti méret és pontos felismerési arány **NINCS MEG**. A Picasa Preferences oldali `FRSuggestionSingleThreshold=0,90` (`0x0048ac6f`) nem azonosítható a Red callback küszöbével; a `FRRecommendIncludeLimit=0,50` (`0x0048ad46`, összehasonlítás a `0x0048e33e` helyen) külön ajánlás-szűrő. Arányhoz továbbra is azonos, tételes képkészlet és képenkénti nyers eredmény kell mindkét programból.

**Bizonyítottság.** A Red-rutin pontszámgyűjtő szerepe **megerősített**: az utasításszintű olvasatot a Picasa3.exe hívási útja és a Red vtable-bejegyzése támasztja alá. A N3 termékértékei ettől még **nyitottak**.

### 42.3 N7: a People Manager listájának kijelölési módja felvételt igényel

A `runtime/contactmgr.fen` `contacts` listája csak a nevet, szélességet, magasságot, függőleges görgetést, rejtett fejlécet és egy oszlopot deklarálja (`10-13. sor`). Nincs benne kijelölési módot megadó attribútum. Ez a a Picasa saját erőforrás-leírója, nem natív `LVS_SINGLESEL` bit, ezért a hiányzó attribútumból nem következtetek egyszeres kijelölésre. A job-186 24. képe egy kiválasztott személyt mutat, de nem próbál második sort kijelölni. **N7 People Manager ága NINCS MEG**; kell a felvétel legalább két személlyel, külön Ctrl-kattintással és külön Shift-kattintással, kijelölt sorokkal és a `Delete Person` állapotával. A törlést Mégsével kell megszakítani.

**Bizonyítottság.** A Név nélküliek többes kijelölése külön már igazolt (`0x006470d0`, job-180); ez nem dönti el a People Manager listáját. A People Managerre vonatkozó státusz **nyitott**.

### 42.4 A korábbi Ghidra-kérések lezárása és az N5 határa

- **`0x00495be0`: lezárva.** A Ghidra-dump 305-363. sora és a helyi diszasszemblálás egyezően mutatja, hogy a `param_1+0x54 == 0` feltétel alatt hívja a `0x00499610`-t (`0x00495c3f`). Az index RTTI-adata a `0x00495be0` címet a `CColumn<unsigned___int64,1,322043908>::vftable` (`0x00c8230c`) 6. slotjához rendeli; a hivatkozás `0x00c82324`. A hívás a `0x13320004` kulcsú oszlop lusta lekéréséhez tartozik, nem bizonyít minden esetben fájlolvasást. A 37.9/b-ben leírt rekordállapot szabály marad érvényben.
- **`0x0056c5a0`: a #5184 N5 kéréséből visszavonva, nem kulcsértékkel megválaszolva.** A Ghidra-dump 864-889. sora `ID_IGNOREPEOPLE` feliratot tölt be és menüpontokat engedélyez vagy tilt; ez menü-állapot frissítés, nem azonosított kattintáskezelő. Az N5 termékállítását a job-222..226 felvételei zárják le: a személyalbum menüjében és a People Managerben nincs személyszintű mellőzés, a mellőzés arcszintű. A `0x1332000x` írókulcs értéke továbbra is **NINCS MEG**, de az N5 lezárásához nem szükséges. A kódolt menüpont esetleges másik felülethez tartozó tárolási útja külön kérdés lenne, ezért nem nyitok hozzá új jegyet ebben a körben.

### 42.5 Bizonyítottsági fok, független utak és cáfoló próbák

**Összesített fok: nyitott.** A `0x00495be0` feltételes lookupja és a Red.dll `0x100057c0` pontszám-összesítő útja binárisból megvan. N1 teljes felismerési kimenete, N3 küszöbe/mérete/aránya és N7 People Manager kijelölési módja mérés nélkül nem dönthető el.

- **A út, N1:** a Ghidra C-dump `0x004987c0` és `0x0047b020` törzse megmutatja a munkasort, a `+0x10` jelző elágazását és a `0x0048ef20` hívást.
- **B út, N1:** a helyi diszasszemblálás megerősíti a `0x0047b020` állapotvizsgálatát és hívási sorrendjét. Ez ugyanannak a bináris kódnak más megjelenítése, nem független út. A két nézet egyezik a vezérlési folyamatról, de a jelző jelentéséről és az eredeti futás eredményéről nem ad bizonyítékot.
- **A út, N3:** a Red.dll `0x100057c0` helyi utasításai a callback pontszámok maximumát választják.
- **B út, N3:** a Red.dll `0x101aadc4` vtable-adat, `0x10001570` csomagoló és Picasa3.exe `0x006cde50` hívó egymástól külön PE-adatokkal és utasításokkal igazolja a hívási láncot. Egyik út sem ad küszöböt, méretet vagy felismerési arányt.
- **A út, `0x00495be0`:** a C-dump a null `+0x54` kaput és a `0x00499610` hívást mutatja.
- **B út, `0x00495be0`:** a teljes helyi diszasszemblálás ugyanezt a feltételt és hívási címet adja; az index RTTI-je a metódust a megfelelő `CColumn<unsigned___int64,1,322043908>` vtable-hez rendeli.

**Cáfoló kísérletek.**

1. **N1:** megpróbáltam a munkatétel útjából következtetni arra, hogy a névvel ellátott fotó mindig felismerésre kerül. A `+0x10` bájt nem nulla ága a `0x0048bd80` hívása után visszatér; a jelző jelentése és írója nincs meg. A biztos feldolgozásra vonatkozó következtetés nem áll meg. Az ellenőrzés azonos statikus útból származik, az eredeti runtime-kimenetet nem cáfolja.
2. **N3:** megpróbáltam a `0,90` Preferences értéket a Red küszöbével azonosítani. A Red rutin csak a callback értékeket rangsorolja, a Picasa `0,90` külön preferenciaágban olvasott érték; az azonosságot semmi nem támasztja alá. A `0x100057c0` kódjában nincs képméretet beállító ág sem.
3. **N7:** megpróbáltam a job-186 egy kiválasztott sorából egyszeres kijelölésre következtetni. A felvétel nem tesztel második sort, a `.fen` nem ad kijelölési módot; a feltevés nem igazolható.
4. **N5 / `0x0056c5a0`:** megpróbáltam ezt az állapotfrissítőt a `0x1332000x` oszlop írójának tekinteni. A C-dump csak a `ID_IGNOREPEOPLE` menüfelirat és állapot kezelését mutatja; a függvény nem adja meg a kattintáskezelőt vagy a tartós kulcsot. A job-222..226 mérések a #5184 N5 kérdését ettől függetlenül lezárják.

### 42.6 A #5184 „Kész, ha” pontjai és fejlesztési következmény

| Pont | Állapot | Bizonyíték |
|---|---|---|
| N1, névvel ellátott fotón új, ismeretlen arc | ⛔ Nyitott | A munkatétel `+0x10` jelzője megkerülheti a `0x0048ef20` hívást; a jelző jelentése és az eredeti futás eredménye NINCS MEG; kell a kontrollált Colab-felvétel. |
| N3, eredeti felismerési arány, küszöb és bemeneti méret | ⛔ Nyitott | A `0x100057c0` max pontszámot választ; a callback döntése, bemeneti mérete és mért aránya NINCS MEG. |
| N4, alapértelmezett keret és név | ✅ Lezárt | Job-187: a névvel ellátott arcon alapból nincs keret és név. |
| N5, személyszintű mellőzés | ✅ Lezárt | Job-222..226: nincs személyszintű mellőzés a vizsgált személyalbum- és People Manager felületen; az arc mellőzése a csempe művelete. |
| N6, személy törlése és az arcok | ✅ Lezárt | Job-222/224: a `faces=` adat törlődik, a `[Contacts2]` sort megtartja; a javítás a #5391-ben ment ki. |
| N7, kijelölési modell | ⛔ Részben nyitott | Név nélküliek: többes kijelölés igazolt (`0x006470d0`, job-180). People Manager: Ctrl/Shift felvétel kell. |
| N8, People Manager referencia | ✅ Lezárt | Job-186, 24. kép: a 631×351 ablak és vezérlői rögzítve. |

**Fejlesztési következmény.** N1, N3 és N7 esetén nincs mért eltérés az eredeti és a PicasaPy között, mert az eredeti viselkedés nincs teljesen megmérve. Ezért most nem indokolt fejlesztői jegy vagy `Eredeti / nálunk / teendő` kódlista. A következő lépések a #5184-hez tartozó Colab-felvételek; új kutatási jegy nem kell.

**Nyitott:**
- N1: `Ghidra-kör kell: 0x0047b020 - a munkatétel +0x10 állapotjelző bájt írójának azonosítása és jelentése; kizárhatja-e a névvel ellátott fotót a képenkénti felismerési útból? [blokkoló]`; továbbá Colab-felvétel névhez rendelt és név nélküli arccal ugyanazon fotón, kontrollfutással.
- N3: `Ghidra-kör kell: 0x100057c0 - a [param_3+8]+0x74 objektum vtable +0x40 callbackjének tényleges célja, az elfogadási küszöb és a bemeneti méretet adó út [blokkoló]`; továbbá összehasonlító Colab-futás tételes képkészleten.
- N7: Colab-felvétel legalább két személlyel, Ctrl- és Shift-kijelöléssel.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (a 37.9-es régi Ghidra-kérések státusza, a 40.4-es nyitott lista és az új 41. szakasz). Kódhoz és tesztekhez nem nyúltam.

## 43. #5184, helyi Codex-kutatói kör: N1 mezőíró és N3 virtuális pontszámfüggvény (2026-10-22)

**Keret.** Ez a kör csak a `0x0047b020` N1 útját és a Red.dll `0x100057c0` N3 útját vizsgálja. Ghidra és futó Colab-mérés nem állt rendelkezésre. A `docs/specs/binaris-regeszet-modszertan.md` szerinti cím-atlaszt, indexlekérdezést, célzott diszasszemblálást és a korlátos `paszta.py` pásztázást használtam. A binárisból kinyert sztringek és bájtok adatként kezelendők.

### 43.1 N1: a `0x0047b020` olvasó, nem a `+0x10` mező írója

**Közvetlen utasítások.** A bináris-index `functions` sora a `0x0047b020` címet a 379 bájtos `.text` függvény kezdeteként adja meg. A törzs a `0x0047b031` helyen összehasonlítja a `byte ptr [eax+0x10]` értékét nullával. A nulla ág a `0x0047b04a` címre megy tovább; a nem nulla ág a `0x0048bd80` hívása után a `0x0047b049` helyen visszatér. A későbbi felismerési út a nulla ágban hívja a `0x0048ef20` függvényt (`0x0047b149`). Ez a függvény az állapotjelző bájtot olvassa, nem írja.

**Írókeresés.** Az indexelt közvetlen hívási él `0x004987c0 -> 0x0047b020`. Az index nem bizonyítja, hogy nincs más, közvetett hívó vagy író. Ezért az egész Picasa3.exe `.text` szakaszt a `paszta.memoria_kapu()` első műveletként való meghívása után, `paszta.utasitasok()` darabokban adott utasításain kerestem. A szűrés az `+0x10` eltolású, egybájtos memóriaírásokat tartotta meg, és kizárta az `esp` vagy `ebp` bázist tartalmazó operand-alakokat. Eredmény: **139 utasításjelölt**. A találatok több eltérő függvénybeli mezőelrendezést tartalmaznak; a vizsgálatban egyetlen jelöltet sem tudtam bizonyítékkal a `0x0047b020` bemeneti objektumához kötni. A szűrés nem zárja ki a szélesebb írásokat, az `ebp`-bázisú mezőket vagy a más regiszteren át ugyanoda mutató címzést. Az író és a mező jelentése **NINCS MEG**. Ez nem annak bizonyítéka, hogy nincs író.

| Állítás vagy érték | Forrás |
|---|---|
| `0x0047b020`, RVA `0x0007b020`, fájloffset `0x0007b020`, méret 379 bájt | bináris (`functions`, `0x0047b020`) |
| `+0x10` byte összehasonlítása és a nulla/nem nulla ág | bináris (`0x0047b031`, `0x0047b035`, `0x0047b038`, `0x0047b049`) |
| 139, `esp`/`ebp` bázist kizáró, egybájtos `+0x10` írásjelölt; csúcs-RSS 97,6 MiB | mérés (`paszta.py`, teljes `.text`, `memoria_kapu()` után) |
| A munkatétel `+0x10` mezőjének írója és jelentése | NINCS MEG |
| A névvel megjelölt fotó tényleges új arctalálata | NINCS MEG |

### 43.2 N3: a `0x100057c0` pontszámot választ, a `+0x40` cél indirekt

**A célfüggvény utasításai.** A Red.dll `0x10000000` kép-alapcímű PE-képében a `0x100057c0` a `.text` szakaszban van. A függvény a `[param_3+8]+0x74` objektumot beolvassa (`0x10005809`-`0x1000580f`), majd a futó objektum vtable-jéből tölti be a `+0x40` címet (`0x10005843`-`0x10005847`) és indirekt módon hívja (`0x10005859`). A visszatérő lebegőpontos értékeket összeadja, az adott jelölthöz tartozó legnagyobbat tartja meg (`0x10005869`-`0x1000587b`), majd a kimeneti tömbbe írja (`0x100058d2`-`0x100058d8`). A függvényben nincs olyan konstans-összehasonlítás, amely az elfogadási küszöböt megadná, és nincs képméretet beállító utasítás. A vtable `+0x40` célja futás közben dől el, és itt **NINCS MEG**.

**A cím megkülönböztetése.** A korábban azonosított Red.dll vtable `0x101aadc4` adatában a `+0x40` bejegyzés `0x100014d0`, a `+0x44` bejegyzés `0x10001570`. A `0x10001570` csomagoló a `0x100015a2` helyen hívja a `0x100057c0` függvényt. Tehát a `0x100057c0` ennél a vtable-nél nem a `+0x40` slot célja. A `0x100057c0` belsejében látott, másik objektum `+0x40` slotjának tényleges célját ez az adat nem azonosítja.

| Állítás vagy érték | Forrás |
|---|---|
| Red.dll kép-alapcím `0x10000000`; a vizsgált kód `.text` szakaszban van | bináris (PE-fejlécek, `0x100057c0`) |
| A `[param_3+8]+0x74` objektum vtable `+0x40` slotjának indirekt hívása | bináris (`0x10005843`, `0x10005847`, `0x10005859`) |
| A `0x101aadc4` vtable `+0x40` értéke `0x100014d0`; `+0x44` értéke `0x10001570` | bináris (Red.dll adat, `0x101aadc4`) |
| A `0x10001570` csomagoló hívása a `0x100057c0` címre | bináris (`0x100015a2`) |
| A belső virtuális cél, a detektor küszöbe, a Red.dll tényleges bemeneti mérete és a felismerési arány | NINCS MEG |

### 43.3 Cáfoló kísérlet és bizonyítottság

**Cáfoló kísérlet, N1.** Azt próbáltam igazolni, hogy az `+0x10` eltolás egyedileg azonosítja a munkatétel állapotjelző bájtját. A teljes, memóriakapun át pásztázott `.text` 139 egybájtos írásjelöltet adott. Az eltolás önmagában nem különbözteti meg a munkatételt más objektumoktól, ezért egy jelöltet sem neveztem ki írónak. A számot a szűrőn át ellenőriztem, nem az index negatív eredményéből következtettem.

**Cáfoló kísérlet, N3.** Azt próbáltam igazolni, hogy a `0x100057c0` maga a vizsgált vtable `+0x40` célja és a végső küszöb helye. A nyers vtable-adat `+0x40 = 0x100014d0` értéket ad, míg `+0x44 = 0x10001570`; az utóbbi csomagoló hívja a `0x100057c0` függvényt. A `0x100057c0` közvetlen utasításai egy másik objektum `+0x40` slotjához indirekt hívnak és a visszakapott pontszámokból maximumot választanak. A cáfoló eredmény ellenőrizve van, de a belső slot célját és a másutt meghozott elfogadási döntést nem cáfolja.

**A és B út.** N1 esetén az A út a célfüggvény utasításszintű olvasata; a B út az indextől független, teljes `.text` pásztázás. Abban egyeznek, hogy az olvasó ágai ismertek, de a mező írója és jelentése nem köthető hozzá. N3 esetén az A út a `0x100057c0` pontszám- és kimeneti útja; a B út a vtable-adat és a `0x10001570` csomagoló külön olvasata. Ezek egyeznek abban, hogy a `0x100057c0` fölötti hívási híd megvan, de az általa használt belső virtuális cél és a végső küszöb nem.

**Összesített bizonyítottsági fok: nyitott.** N1 és N3 statikusan nem dönthető el ebből a két címútból. Nincs mérési adat az eredeti felismerési arányról, a Red.dll belső küszöbéről vagy bemeneti méretéről. Az N1/N3 eltérés a PicasaPy-hoz képest sem bizonyított, ezért fejlesztési eltérést nem javaslok.

### 43.4 A döntő Colab-felvételek és a „Kész, ha” pontok

- **N1:** tiszta tesztprofilban ugyanazt a két jól látható arcot tartalmazó fotót futtasd le egyszer úgy, hogy egyik arc sincs megnevezve, majd úgy, hogy az egyik arc ismert személyhez van rendelve. Mindkét futásról rögzítsd a Név nélküliek/javaslat felületet, a `faces=` sort és az érintett PMP-találatokat. Külön kontrollként ugyanazt a fotót változatlan név nélküli állapotú tesztprofilban is futtasd le. A kérdésre az ad választ, hogy a második arc a név hozzárendelése után is megjelenik-e.
- **N3, megfigyelt felismerési arány:** rögzített, tételes arckészleten, ugyanazon bemeneti képfájlokkal és ismert arc-címkékkel készíts képernyőképet és képenkénti eredménylistát az eredeti Picasáról, majd a PicasaPyról. Az arány pontos számlálásból származzon: helyesen megtalált arcok száma osztva a tesztkészlet igazolt arcainak számával. A futás során rögzítsd a forrásképek méretét és az összes javaslatot. A Red.dll belső bemeneti mérete csak akkor zárható le, ha azt a futó rendszer közvetlenül láthatóvá teszi; a forráskép mérete önmagában nem bizonyítja.
- **N3, belső küszöb:** a felületi felvétel önmagában nem ad Red.dll pontszámot. Ha a Colab-környezet nem teszi láthatóvá a callback nyers pontszámát és az elfogadás/elutasítás eredményét, a belső numerikus küszöb továbbra is **NINCS MEG**; annak statikus útja a belső vtable-cél és a döntő ág célzott dekompilálása.
- **Kész, ha:** N1-re a kétarcú, név előtti/utáni Colab-felvétel megadja a második arc eredményét; N3-ra a fagyasztott mintán mért arány és a rögzített forrásképméretek megvannak; a Red.dll tényleges bemeneti mérete és belső küszöbe csak akkor zárható le, ha közvetlenül megfigyelhető vagy binárisból kiolvasható. Addig mindkét statikus kérdés nyitott marad.

**Nyitott:**
- N1: a `+0x10` írója/jelentése és a már megnevezett fotón megjelenő második arc eredménye **NINCS MEG**; a döntő Colab-felvétel a kétarcú fotó, egy névhez rendelt arccal, plusz név nélküli kontroll.
- N3: a belső vtable-cél, az elfogadási küszöb, a Red.dll tényleges bemeneti mérete és az eredeti felismerési arány **NINCS MEG**; Colabban rögzített mintán kell mérni a megfigyelt arányt és a javaslatokat. Belső küszöböt csak a nyers pontszám és a döntő ág megfigyelése zár le.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (új 43. szakasz; a 42.1 és 42.2 csak ⚠️ jelölést kapott).

## 44. #5184, helyi Codex-kutatói kör: a Picasa javaslati küszöbe és a nyitott N-pontok (2026-10-22)

**Hatókör.** A szakasz a 43. szakasz N1/N3 eredményét frissíti a `0x0048aab0`, `0x0048e1f0` és `0x006cde50` utasításainak célzott olvasatával, továbbá összefoglalja a jegy hét pontjának állapotát. Ghidra-dekompilálás és futó Colab/Picasa mérés ebben a munkamenetben nem volt elérhető. A `0x0048aab0` és `0x0048e1f0` diszasszemblálását, valamint a korlátos teljes `.text` pásztázást a helyi eszközökkel végeztem; a pásztázás első művelete a `paszta.memoria_kapu()` volt.

### 44.1 N3: a `0.50` ismert Red-hasonlósági javaslati határ, nem a detektor küszöbe

A `0x0048aab0` beállításbetöltő a `FRRecommendIncludeLimit` kulcs alapértelmezett értékét `50`-re állítja (`0x0048aba9`), majd a `0x00cf3a08` címen tárolt `100.0` double konstanssal osztja, és az eredményt a `this+0x34a4` mezőbe teszi (`0x0048ad74`, `0x0048ad8c`-`0x0048ad98`). Az így kapott alapérték pontosan **`0.50`**. Mivel ez Preferences-beállítás, ez az alapérték; a felhasználói beállítás által felülírt futásidejű értéket nem mértem.

A különálló `0x0048e1f0` fogyasztó betölti ezt a mezőt, meghívja a `CNevenVision` `+0x2c` útját (`0x0048e2eb`-`0x0048e2f1`; a cél `0x006cde50`), majd a visszakapott Red-pontszámokat a mező értékével veti össze (`0x0048e330`-`0x0048e349`). A Red.dll `0x100057c0` útja a leírókhoz tartozó hasonlósági pontszámok maximumát adja vissza. Ezért a `0.50` a Red által visszaadott személy-/javaslati pontszám befogadási határa ezen a Picasa-ágon. Nem bizonyítja a Red arcdetektor belső confidence-küszöbét.

A `0x006cde50` híd a leíróból származó mezőket továbbítja; a függvényben nincs `960` képpontos konstans vagy képméretező művelet. Ez csak erről a függvényről állít valamit, nem zárja ki, hogy a méretet egy korábbi hívó vagy a Red.dll másik rétege módosítja. Az eredeti Red-bemenet tényleges képpontmérete, a detektor belső küszöbe és a rögzített készleten mért felismerési arány továbbra is **NINCS MEG**. A PicasaPy jelenlegi `960`-as méretkorlátja és `0.9`-es YuNet confidence értéke a forrásban (`src/picasapy/faces/detector.py:49`, `:42`) ellenőrizhető; a Picasa `0.50`-es hasonlósági határa másik feldolgozási szakaszban működik, ezért a két küszöb közvetlen számbeli összevetése nem érvényes.

| Állítás vagy érték | Forrás | Bizonyítottság |
|---|---|---|
| `FRRecommendIncludeLimit` alapértéke `50`; az osztó `100.0`; az eltárolt határ `0.50` | bináris (`0x00c81d04`, `0x0048aab0`, `0x0048aba9`, `0x00cf3a08`, `0x0048ad74`, `0x0048ad8c`) | megerősített |
| A `this+0x34a4` értékkel a Picasa a Red-visszatérési pontszámokat hasonlítja össze | bináris (`0x0048e1f0`, `0x0048e2eb`, `0x0048e330`-`0x0048e349`) | megerősített |
| A Red-visszatérési pontszám jelölőnként a mintákkal kapott hasonlóságok maximuma | bináris (`0x100057c0`; hívó: `0x10001570`) | megerősített a 43.2-ben dokumentált hatókörön belül |
| Eredeti arcdetektor confidence-küszöbe, Red tényleges képbemeneti mérete és felismerési aránya | NINCS MEG | nyitott |
| PicasaPy összehasonlító alapértékei: `960` px és `0.9` YuNet-score | mérés (forrásellenőrzés: `detector.py:49`, `:42`) | PicasaPy-forrásérték, nem eredeti Picasa-mérés |

### 44.2 N1: a mezőíró és a névvel jelölt fotó további arca továbbra is nyitott

A `0x0047b020` továbbra is a munkatétel `+0x10` bájtját olvassa, de a teljes `.text` indextől független, `paszta.py`-val végzett átvizsgálása nem kötötte egyik írásjelöltet sem ehhez az objektumhoz. A friss pásztázás **139** egybájtos, `+0x10` eltolású jelöltet adott az `esp`/`ebp` bázisú operandusalakok kizárásával. Ez a keresés nem fedi le a szélesebb írásokat és az összes lehetséges bázis- és álnévalakot; ezért nem bizonyítja, hogy nincs író. A mező írója, jelentése, valamint az, hogy az eredeti egy már megnevezett fotón felajánl-e másik, ismeretlen arcot, **NINCS MEG**.

| Állítás vagy érték | Forrás | Bizonyítottság |
|---|---|---|
| A munkatétel `+0x10` bájtját a `0x0047b020` olvassa | bináris (`0x0047b031`, `0x0047b035`, `0x0047b049`) | feltételes a mező jelentésére nézve |
| 139 egybájtos írásjelölt az `+0x10` eltolásra; `esp`/`ebp` bázis kizárva | mérés (`paszta.py`, teljes `.text`, `memoria_kapu()` után) | feltételes keresési eredmény; az író NINCS MEG |
| Névvel jelölt fotón további ismeretlen arc megjelenik-e | NINCS MEG | nyitott |

### 44.3 N7: a People Manager egy- vagy többes kijelölése felvételre vár

A `runtime/contactmgr.fen` listaelem-leírása nem ad meg kijelölési módot. A `0x007b9630` egy korábban vizsgált útja egy kijelölt indexet olvas; ez önmagában nem zárja ki, hogy a vezérlő Ctrl/Shift-tel több elemet is kijelölhessen. A job-186 egyetlen személyt tartalmazó ablakfelvétele sem dönti el a modellt. N7 **NINCS MEG**; a döntő felvétel két külön személy mellett: első sor kattintása, Ctrl+kattintás a másodikra, majd Shift+kattintás a másodikra, mindhárom állapotról képernyőkép és a kapcsolódó gombok állapotának rögzítése.

| Állítás vagy érték | Forrás | Bizonyítottság |
|---|---|---|
| A lista definíciójában nincs kijelölési mód megadva | mérés (az eredeti `runtime/contactmgr.fen` erőforrásának vizsgálata) | feltételes; a futásidejű viselkedést nem dönti el |
| Egy kijelölt index olvasása a vizsgált kezelőútban | bináris (`0x007b9630`) | feltételes a teljes lista kijelölési modelljére nézve |
| Ctrl-/Shift-többes kijelölés a People Managerben | NINCS MEG | nyitott |

### 44.4 A két független út és a cáfoló próbák

**N3, két út.** A út: a `0x0048aab0` beállító olvasata megadja az alapértéket (`50`), a `100.0` osztót és a `this+0x34a4` mezőbe írt `0.50`-et. B út: a külön `0x0048e1f0` fogyasztó ugyanezt a mezőt használja a `0x006cde50`/Red útból visszatérő pontszámok összevetéséhez. A két út egyezik: az eredetiben létezik egy pontos `0.50`-es Red-pontszám/javaslati határ. Ez nem a Red belső detektorküszöbének bizonyítéka.

**N1, két út.** A út a `0x0047b020` közvetlen utasításolvasata; B út a teljes `.text` pásztázása. Egyeznek abban, hogy a mező olvasása megvan, de az íróhoz és a mező jelentéséhez egyik sem ad bizonyítékot. N1 viselkedéséről csak az eredeti futás mérése dönt.

**Cáfoló kísérlet.** Megpróbáltam cáfolni azt az értelmezést, hogy a `0.50` ugyanazt méri, mint a PicasaPy YuNet `0.9` confidence küszöbe. A Red `0x100057c0` pontszámot állít elő, a Picasa külön `0x0048e1f0` ága pedig később hasonlítja ezt a pontszámot a `0.50`-hez; a `0x006cde50` híd utasításai sem tartalmaznak `960`-as méretbeállítást. A közvetlen egyenértékűség hipotézise nem áll meg: különböző feldolgozási szakaszok számairól van szó. Ez a cáfoló kör ugyanakkor nem azonosítja a Red belső confidence-küszöbét vagy a bemeneti méretet.

**N1 cáfoló kísérlet.** Azt próbáltam igazolni, hogy a `+0x10` eltolás egyedileg elvezet a munkatétel írójához. A teljes szakaszban talált 139 jelölt ezt cáfolta; egyiket sem lehetett bizonyítékkal a munkatétel objektumához rendelni. Az eredményt ugyanazzal a korláttal ellenőriztem, amellyel kerestem: egy- vagy szélesebb írások, `esp`/`ebp`-alapú címzés és regiszter-álnevek maradhatnak ki, ezért a keresés nem bizonyít íróhiányt.

**Összesített bizonyítottsági fok: nyitott.** A N3 `0.50`-es javaslati határa két független bináris út alapján megerősített részlelet. A jegy egésze nyitott, mert N1 viselkedése, N3 eredeti felismerési aránya/belső detektorküszöbe/bemeneti mérete és N7 kijelölési módja nincs megmérve.

### 44.5 A jegy „Kész, ha” pontjai

| Pont | Eredmény | Bizonyíték |
|---|---|---|
| N1: a névvel rendelkező fotón talál-e további ismeretlen arcot | ⛔ | NINCS MEG; eredeti Picasa-mérés kell két arccal, egy megnevezett arccal és név nélküli kontrollal. |
| N3: eredeti felismerési arány és küszöb a PicasaPy `960` px / `0.9` beállításához képest | ⛔ | A Picasa Red-javaslati határa `0.50` (bináris: `0x0048aab0`, `0x0048e1f0`), de ez nem a YuNet confidence megfelelője; a Red belső detektorküszöbe, tényleges bemeneti mérete és mért aránya NINCS MEG. |
| N4: alapból látszik-e a keret és név a megnevezett arcon | ✅ | Mérés (`job-187`): alapból nincs keret és név; az Emberek panel zárva. |
| N5: személyszintű mellőzés útja és hatása | ✅ | Mérések (`job-222..226`): nincs személyszintű mellőzés a People Managerben/személyalbumban; a mellőzés arcszintű. |
| N6: személytörlés útja és hatása az arcokra | ✅ | Mérések (`job-222..226`): a „Delete People Album” törli a `faces=` sorokat, a `[Contacts2]` sort megtartja, a Cancel az alapértelmezett; a javítás a #5391-gyel megvalósult. |
| N7: a People Manager kijelölési modellje | ⛔ | NINCS MEG; két személyes Ctrl-/Shift-kijelölési felvétel kell. |
| N8: referencia-képernyőkép a People Managerről | ✅ | Mérés (`job-186`, 24. kép): 631×351 px-es People ablak, személylista, adatmezők és gombok rögzítve. |

**Fejlesztési eltérés:** a rendelkezésre álló bizonyíték nem igazol eltérést a PicasaPy és az eredeti között N1, N3 vagy N7 esetén. A `0.50` és `0.9` eltérő jelentése önmagában nem fejlesztési hiba; fejlesztői jegyet ezért nem javaslok.

**Nyitott:** N1: a `+0x10` írója/jelentése és a név utáni további arctalálat; N3: a Red belső detektorküszöbe, képbemeneti mérete és a mért felismerési arány; N7: Ctrl-/Shift-kijelölés. A viselkedési és aránykérdésekhez az eredeti Picasa/Colab-felvétel a döntő; statikus eredményből nem becsülhetők.

- Ghidra-kör kell: `0x0047b020`: melyik író állítja a bemeneti munkatétel `+0x10` állapotjelző bájtját, és mit jelent az állapot?
- Ghidra-kör kell: `0x100057c0`: a `[param_3+8]+0x74` objektum `vtable+0x40` callbackjének tényleges célja, pontszám-skálája és döntési ága (a `0x10001570` állapotkód-ellenőrzése már megvan, 35.11) [blokkoló]
- Ghidra-kör kell: `0x006cde50`: a Red.dll-nek átadott képleíró méretmezője honnan származik és milyen egységű; történik-e ezen az adapterúton képméretezés?

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (új 44. szakasz: a `0.50`-es javaslati határ és N1/N3/N7 állapota).

## 45. #5184, helyi kutatói kör: a munkasor-csomópont, a két küszöb és a Red-belépések (2026-10-22)

**Hatókör.** A N1, N3 és N7 pont. A 43-44. szakasz Ghidra-kérései közül a `0x0047b020`, `0x0048ef20`, `0x006cde50` útját vizsgáltam. A `0x100057c0` és `0x10001570` C-kimenete a 2026-10-22-i privát Ghidra-köteg (`referencia/ghidra/2026-10-22-ghidra-sor-158-198*.txt`); a többi címet diszasszemblálással (`annot_disasm.py`) és korlátos `.text`-pásztázással (`paszta.py`, `memoria_kapu()` első műveletként) ellenőriztem. Futó Colab-mérés nem állt rendelkezésre.

### 45.1 Korrekció: a `worker+0x6c` nem létrehozott objektum, hanem a sorból kivett csomópont

A 34.7 és 34.8 szakasz a `0x0047b020` `this`-ét a `worker+0x6c` objektum `+4` alobjektumaként írja le, létrehozóját nyitva hagyva. A kód szerint a `0x004987c0` munkasor-hurok a sorból kivett csomópontot (C: `piVar1`) a worker `+0x6c` mezőjébe teszi (C: `param_1[0x1b] = piVar1`; asm: `0x0049886a`, `0x004989fe`, `mov [esi+0x6c], …`), majd a `0x0049892d`-`0x00498933` helyen `eax = [esi+0x6c] + 4` értékkel hívja a `0x0047b020`-t. Vagyis `X = [worker+0x6c]` a kivett csomópont, az item pedig `X+4`.

A munkatétel mezői `X`-re vetítve (így a 43.1 és 44.2 „+0x10 jelzője" az `X+0x14`):

| item-offszet | `X`-offszet | jelentés |
|---|---|---|
| `+0x0` | `X+0x4` | a felismerő `this` (a `0x0048ef20` első argumentuma) |
| `+0x8` | `X+0xc` | mód: nulla esetén `0x00414940(1)` |
| `+0xc` | `X+0x10` | küszöb (float): a `0x0048ef20` negyedik argumentuma |
| `+0x10` | `X+0x14` | jelzőbájt: nemnulla esetén nincs képenkénti felismerés |

Bizonyítottsági fok: **feltételes** (egy kódút; az asm és a dekompilált C ugyanezt adja, de ez nem két független út). A csomópont létrehozója és a jelzőbájt írója nincs megtalálva (45.7).

### 45.2 N1: a nemnulla jelző ága nem hívja a felismerőt

- `0x0047b031`-`0x0047b038` (asm): ha a `byte [item+0x10]` nem nulla, a függvény `0x0048bd80(this)` hívás után `0xf4240`-et ad vissza, és nem hívja a `0x0048ef20`-at.
- A `0x0048bd80` (888 bájt) közvetlen hívásai között nincs `0x0048ef20` (asm, a teljes függvény hívásai ellenőrizve; a közvetett `call eax` és `call edx` célok nem oldhatók fel). A törzs zárat (`this+0x2818`, `this+0x28c0`), időbélyeget (`this+0x2868`) és állapot-mezőket kezel. Ez összhangban van a 14.5.2 szakasz „felszabadító/átméretező ág" besorolásával, és nem felismerés.
- Nulla jelzőnél és nulla módnál: `0x0047b04f` → `0x0047b187`: `push 1; call 0x00414940`. Nem nulla módnál a `0x0048ef20` hívás a `0x0047b149`-nél.

Következtetés N1-re: a jelzővel megjelölt munkatétel nem fut képenkénti felismerésen. Hogy a névvel jelölt fotóra beáll-e a jelző, és a jelző mit jelent (névvel jelölt vagy már feldolgozott), **NINCS MEG**, mert a jelző írója nem azonosítható (45.7).

### 45.3 N3: a 0,85 és a 0,50 a hasonlósági skála küszöbei, nem a detektoré

- **Negyedik argumentum (asm, egy kódút):** `0x0047b055` `fld dword [eax+0xc]` (`X+0x10`), `0x0047b062` mentés a veremre, `0x0047b13f` `fstp dword [esp]` a negyedik argumentum helyére, `0x0047b149` `call 0x0048ef20`.
- **Nulla küszöb (asm):** a `0x0048ef20` `0x0048fabd`-`0x0048fad3` ágában `fucom` a nullával; ha az argumentum `0.0`, `fld dword [this+0x3498]` tölti be az értéket (alapérték 0,85, `FRSuggestionThreshold`), különben az argumentum marad. A `0x00414940` (21. szakasz) nulla értéket ad át, ott tehát 0,85 él.
- **0,50 (`this+0x34a4`, `FRRecommendIncludeLimit`), float-ként (asm):** `0x0048e252`-`0x0048e25a` `fld dword [ebp+0x34a4]` → `[esp+0x20]`; `0x0048e33e`-`0x0048e342` `fcomp st(1)` a pontszámmal. A C-dump `(DWORD)` konverziója a dekompiláló mellékterméke (a 21.2 és 27.2 szakasz is ezt állapította meg; most asm-mal ellenőrizve).
- **A pontszám forrása (feltételes):** a `0x0048e1f0` pontszámai a `param_9` `+0x2c` slot (`0x006cde50`) kimenetei. A `0x006cde50` a `REDENTRY` (`0x00d35e44`) `+0x44` slotját hívja (`0x10001570` → `0x100057c0`), amely leírónként a mintákkal vett legnagyobb hasonlóságot írja. Ez **leírók hasonlósága**, nem arcdetektálás. A 20-27. szakaszok „detektor-hívás" megnevezése ezért pontosítandó.

Következtetés N3-ra: az eredeti 0,85 (javaslati küszöb) és 0,50 (befogadási határ) a Red-hasonlósági skálán működik. A PicasaPy 0,9-es YuNet-konfidenciája a detektoré. A két szám összevetése nem érvényes. Az eredeti arcdetektor belső küszöbe és bemeneti mérete **NINCS MEG**.

### 45.4 Red.dll: a `+0x40` és `+0x44` belépés (asm)

- `REDENTRY` vtábla (`0x101aadc4`): `+0x40` = `0x100014d0`, `+0x44` = `0x10001570`.
- `0x100014d0` (csomagoló) → `0x10005610` (SEH-burkolt) → `0x10108d10`. A `0x10005610` a `[esi]`, `[esi+0x4]`, `[esi+0x8]`, `[esi+0x10]` mezőkkel és a `[ebp+0x1c]` argumentum `+0x18` címével hívja a `0x10108d10`-et; az eredményt `[esi+0x14]`-be írja. A `+0x40` slot NEM a detektor útja, hanem a klaszterező (`createClusterSubSet`), helyesbítve a 45.9 szakaszban. Picasa-oldali hívója nincs megtalálva.
- A `REDENTRY` globálist (`0x00d35e44`) 25 Picasa-függvény olvassa a `0x006cccd0`-`0x006cf970` tartományban (indextől független pásztázás). A `+0x40` hívót közvetett hívás miatt nem azonosítottam.
- A `0x006cde50` átadott méretmezője (a `param_2[5]` rekord második dword-je, `>> 1`) a `this+0x2908` tábla bejegyzése (25.9 és 27. szakasz); a tábla írója NINCS MEG.

### 45.5 N7: a lista definíciója nem ad kijelölési módot

`runtime/contactmgr.fen` (mért olvasat): `<list name="contacts" width="250" height="17li" scroll="v" header="hide">`, benne `<column width="fill"/>`. Kijelölési attribútum nincs; a döntés a kódban van (`0x007b9630`, 44.3), ezt ebben a körben nem követtem végig. A döntő felvétel a 44.3 szerinti két személyes Colab-mérés.

### 45.6 Mérőadat

A `~/.local/share/picasapy-meroadat/meroadat.tar` tagjainak `arc|face|szemel|people|person` szűrése csak `nev_*.jpg` exportokat ad; arcfelismerési mérőkészlet nincs benne. N3 saját oldali mért aránya ezért nem készült.

### 45.7 Nyitott, Ghidra-kérések

- Ghidra-kör kell: (cím NINCS MEG): a munkasor termelője, amely a csomópont `+0x4`, `+0x8`, `+0xc`, `+0x10` mezőit kitölti és a worker sorába (`worker+0x58` fej, `worker+0x68` farok) fűzi. A `0x004987c0` csak fogyasztó. [blokkoló N1]
- Ghidra-kör kell: 0x0048bae0: a `0x0048e5da` hívója; ha ez a képenkénti arcdetektor, a belső küszöb és a bemeneti méret. [blokkoló N3]
- Ghidra-kör kell: 0x10108d10 (Red.dll): a `[esi+0x0/0x4/0x8/0x10]` mezők értelme, és hol van a küszöb vagy a méret. [blokkoló N3]
- Ghidra-kör kell: 0x0048bd80: a nemnulla jelző ágának C-törzse (zár, időbélyeg, állapot). [nem blokkoló]

### 45.8 Állapot

| pont | állapot | mivel |
|---|---|---|
| N1 | BLOKKOLT | a jelző írója és jelentése NINCS MEG; Colab-kétarcú felvétel (43.4) és a termelő Ghidra-köre kell |
| N3 | BLOKKOLT, részben | a javaslati küszöb (0,85), a befogadási határ (0,50) és a hasonlósági jelleg megvan; a detektor-küszöb és a bemeneti méret NINCS MEG |
| N7 | BLOKKOLT | Colab-felvétel (44.3) |
| N4, N5, N6, N8 | LEZÁRVA | változatlan (36-37. szakasz) |

### 45.9 Helyesbítés: a REDENTRY `+0x40` klaszterező, nem detektor (megerősített)

A 45.4 szakasz „a `+0x40` valószínűleg a detektor útja" állítása téves. Két független úton ellenőriztem:

- **Út A (Ghidra C, a 2026-10-22-i köteg):** a `0x10108d10` törzsének hibaüzenet-literálja a függvény nevét adja: `uint32 vtk_Relator::createClusterSubSet( const void* const* templatePtrArrA, uint32 numberOfTemplatesA, uint32 maxSubSetSizeA, uint32* indexArrA ) const`. A törzs klaszter-részhalmazt állít elő, az index-tömböt (`param_5`) tölti, és a darabszámot adja vissza.
- **Út B (nem Ghidra, `pefile` és `capstone`):** a literál kezdő virtuális címe `0x101d5f28` (`.rdata`). Ez a cím négy utasítás immediate-operandusa a `0x10108d10` első 0x1200 bájtjában: `0x10108d4c` (`mov [ebp+0x60], 0x101d5f28`), `0x10108d7c`, `0x10108da3`, `0x10108dd7` (`push 0x101d5f28`).

**A lánc (asm):** a REDENTRY vtábla a `0x101aadc4`-en; a `+0x40` slot értéke `0x100014d0`. A `0x100014d0` a `0x10005610`-et hívja (`0x10001502`), a `0x10005610` pedig a `0x10108d10`-et (`0x10005665`). A `+0x44` slot (`0x10001570`) a `0x100057c0`-t hívja (`0x100015a2`): ez a 45.3 szerinti pontszám-út.

**Küszöb és méret a `0x10108d10`-ben:** a törzsben nincs lebegőpontos összehasonlítás, tehát küszöb nincs. A `param_4` változatlanul adódik tovább a `vtk_Relator` metódusának; a szignatúra sorrendje szerint ez a maximális részhalmaz-méret. A számítást a `vtk_Relator` objektum vtábla-hívása végzi (`vtábla +0x34`); ennek a modulnak a belső küszöbét nem vizsgáltam.

**Bizonyítottsági fok:** megerősített (a két út ugyanarra a törzsre mutat: a függvénynév és a literál-hivatkozás). **Cáfoló kísérlet:** ha a `+0x40` detektor volna, a törzsben képpufferen kellene dolgozni. A Ghidra-törzs bemenete mintatömb-mutató és index-tömb, képpuffer-művelet nincs benne. Ez gyenge cáfolat, mert a `vtk_Relator` objektum belsejét nem néztem meg.

### 45.10 N3: a detektor-jelölt a `vfr_VdeFaceFinder` (RTTI megerősített, vtábla feltételes)

- A `plugins/Red.dll`-ben megvan a `.?AVvfr_VdeFaceFinder@@` RTTI-név. Az x86 MSVC-séta (típusleíró → teljes objektumleíró → vtábla) három objektumleírót talál. A második vtáblája `0x101c867c`, első 16 slotja kódcímekre mutat (a teljes hosszt nem mértem). Az első találat „vtáblája" (`0x101c86f0`) slotjai nem kódcímek, ezért elvetve.
- **A Picasa-oldali belépés:** a `0x0048e590` (74 bájt) a `this+0x2e14` bájtot vizsgálja. Ha ez nulla, vagy a `this+0x2e10` mező (a detektor-objektum) nulla, a `0x0045f0c0`-t hívja (`0x0048e5b8`). Ha a `this+0x2e10` nem nulla, a `jne 0x0048e5da` (`0x0048e5cb`) a `0x0048e5da`-ra ugrik. A teljes `.text`-pásztázás (`paszta.py`, 2 884 879 utasítás, `memoria_kapu()` első lépés) szerint a `0x0048e5da` címére mutató utasítás a teljes `.text`-ben ez az egy.
- **Index-korlát:** az index `xrefs` táblája csak `call` éleket tartalmaz (78 901 sor, `kind = call`), ugróutasítás-élek nincsenek. Ezért a 45.7 kérdésére („a `0x0048e5da` hívója") az index nem ad választ; a korábbi index-negatív állítások (22-23. szakasz) erre a korlátra épültek. Itt a jne-él a bizonyíték.
- **A `0x0048e5da` (1613 bájt) hívásai:** közvetlen: `0x0048e1f0` (2 hívási hely, a pontszámoló, 45.3), `0x0048bae0` (indexelt gyorsítótár), `0x0048ec30` (7 hívási hely), `0x0048b840`, `0x004145a0`, `0x00407610`, `0x009a51b0`, `0x0097c810`, `0x0097caf0`. Közvetett: `call eax` (`0x0048e826`, `[vtábla+0x18]`), `call edx` (`0x0048e88a`, `0x0048e8ce`, `[vtábla+0x1c]`), és IAT-hívások (`0xc40284`, `0xc4055c`, `0xc402a8`). A `[edi+0x20]` (tulajdonos-azonosító), `[edi+0x24]` (mélység) és `[edi+0xc]` (jelzőbájt) mezők a `0x0048bd80` zárminta szerint zárkezelésre utalnak, nem detektálásra.
- **Következtetés:** a detektor-hívás nincs közvetlenül a `0x0048e5da` törzsében. Jelöltek: a `0x0048ec30` (a `0x0048e5da` hét hívási helye; a közvetett hívásait nem néztem végig), és a `vfr_VdeFaceFinder` vtábla egyik slotja.

**Bizonyítottsági fok:** feltételes. A `0x0048e590 → 0x0048e5da` kapcsolat megerősített (jne-asm és teljes pásztázás); a detektor-hívás helye NINCS MEG.

### 45.11 N3 mérleg: a detektor küszöbe és bemeneti mérete NINCS MEG

- A 960 px és a detektor belső küszöbe továbbra sincs igazolva. A 45.3 szerint a 0,85 és a 0,50 a Red-hasonlósági skála küszöbei; ezt ebben a körben semmi nem módosította.
- Mért felismerési arány: nincs (45.6: a mérőadatban nincs arcfelismerési mérőkészlet). NINCS MEG.
- Állapot: **BLOKKOLT**, Ghidra-kör kell (lásd lent).

**Ghidra-kör kérések (új, egységes alakban):**
- Ghidra-kör kell: 0x0048ec30 - a `0x0048e5da` hét hívási helyének célja; melyik közvetett (vtábla-) hívás hívja a detektor-objektum (`this+0x2e10`) metódusát, és a hívás körüli bemeneti méretezés és küszöb. [blokkoló N3]
- Ghidra-kör kell: Red.dll `0x101c867c` vtábla (`vfr_VdeFaceFinder`): melyik slot a detektálás belépési pontja, és benne a küszöb és a bemeneti méret. [blokkoló N3]
- Ghidra-kör kell: 0x0045f0c0 - a `this+0x2e10` objektum előállítása (hívás, ha a `this+0x2e14` bájt vagy a `this+0x2e10` mező nulla): a létrehozott objektum vtábla-címe és a konstruktor-paraméterei. [blokkoló N3]

### 45.12 N1: a munkatétel jelzője, a sortöltő és a producer-jelölt (feltételes)

- **Megerősített (Ghidra C és capstone asm egyezik):** a `0x0047b031`-`0x0047b049` tartományban nemnulla jelzőnél `call 0x0048bd80`, majd `mov eax, 0xf4240` és `ret`. A `0x0048ef20` ebben az ágban nincs. A `0x0048bd80` a korai kilépésben `0xf4242`-t ad vissza, de a hívó ezt eldobja: a visszatérés `0xf4240`.
- **Sorfűzés:** a `0x00498630` (105 bájt) a fejet (`0x0049865c`: `[esi+0x58] = edi`) és a farkat (`0x0049866a`: `[esi+0x68] = edi`) ugyanazzal a regiszterrel írja, vagyis üres sorba fűz. Az index szerint hívó függvénye egy: `0x0047bee0`.
- **Producer-jelölt: `0x0047bee0`** (feltételes). Az index 86 bájtnak írja, de a törzs csak a `0x0047c0d9`-nél ér `ret`-re, tehát a függvényhatár nem egyértelmű. A törzs hívja a `0x00498630`-at (`0x0047befd`), továbbá a `0x0047baf0`-t, a `0x00446200`-at, a `0x0047c320`-at és a `0x006a02e0`-at. A `0x0047bee0`-`0x0047c0d9` tartományban a csomópont `+0x4`...`+0x14` mezőire direkt írás nincs (szűrővel mérve). A `0x0047c024` a bemeneti rekord `+0xc` bájtját olvassa (`cmp byte ptr [esi+0xc], 0`).
- **Mezőíró-jelölt: `0x004985e0`** (36 bájt, `0x004985e0`-`0x00498603`): `[eax+0xc] = esi`, `[eax+0x10] = esi`, `[eax+0x14] = [ecx+0xc]`. Vagyis a csomópont `+0x14` mezője (az item `+0x10`) a forrásrekord `+0xc` bájtjából másolódik. Az index szerint hívói: `0x00425f60`, `0x0045a9d0`, `0x00484820`. A `0x0047bee0` nem hívja, tehát a két jelölt közötti kapcsolat nincs igazolva.
- **Ellentmondás a 45.1 táblával:** a `0x004985e0` a `+0xc` és `+0x10` mezőt ugyanabból a regiszterből (`esi`) írja. A 45.1 kiosztása (`+0x8` mód, `+0xc` küszöb, float) ezt nem fedi, ezért a 45.1 mezőkiosztása feltételes.
- **Nem vizsgált:** a `0x0047baf0`, `0x0047c320`, `0x00446200` és `0x006a02e0` `+0x14` írásai, valamint a sorfűzés (`0x0047befd`) és a mezőkitöltés sorrendje.

**Bizonyítottsági fok:** feltételes. A nemnulla ág viselkedése megerősített; a jelző írója NINCS MEG. **Cáfoló kísérlet:** a `0x0047bee0` nem írja közvetlenül a `+0x14`-et (szűrővel mérve). Ez a cáfoló a két jelöltet nem zárja ki: a jelző a hívott függvényekben vagy a `0x004985e0`-ban lehet.

**Ghidra-kör kérés (új):**
- Ghidra-kör kell: 0x0047bee0 - a munkatétel-termelő: a `0x0047baf0`, `0x0047c320` és `0x004985e0` `+0x14` írása, és a `0x004985e0` hívói (`0x00425f60`, `0x0045a9d0`, `0x00484820`) melyik rekordot adják át (a rekord `+0xc` bájtjának jelentése). [blokkoló N1]

### 45.13 N7: változatlan

Ebben a körben nem vizsgáltam. A 45.5 és a 44.3 állapota marad (BLOKKOLT, a két személyes Colab-felvétel a döntő).

### 45.14 Állapot, mérleg, „Kész, ha"

| pont | állapot | mivel |
|---|---|---|
| N1 | BLOKKOLT | a nemnulla ág megerősítve (45.12); a jelző írója NINCS MEG; jelöltek `0x0047bee0` (termelő) és `0x004985e0` (+0x14 írója), összekötés nincs; a döntő a kétarcú Colab-felvétel (43.4) |
| N3 | BLOKKOLT, részben | a Red-szint eldőlt: `+0x40` klaszterező (45.9), `+0x44` pontszám (45.3); a detektor-jelölt `vfr_VdeFaceFinder`, belépés és küszöb NINCS MEG (45.10-45.11) |
| N7 | BLOKKOLT | változatlan (45.5, 44.3) |
| N4, N5, N6, N8 | LEZÁRVA | változatlan (36-37. szakasz) |

**„Kész, ha" pontonként (45.9-45.14):** N1: ⛔ az írót nem találtuk; ✅ a nemnulla ág viselkedése. N3: ⛔ a detektor-küszöb és a méret NINCS MEG; ✅ a 0,85 és a 0,50 a Red-hasonlósági skála küszöbe, nem a detektoré (45.3). N7: ⛔.

**Megvalósítandó eltérés:** ebből a körből nincs. A detektor küszöbe és a 960 px-es méret ismeretlen, ezért a 0,9-es YuNet-beállítás összevetése továbbra sem érvényes (45.3). Új kutatási jegy javasolt a jelentésben.

**Nyitott kérdések mérlege (45.9-45.14):** 1 lezárva (helyesbítés: a 45.4 `+0x40` állítása) · 3 blokkolt (N1, N3, N7) · 0 hatókörön kívül · 0 csak nyitva.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (új 45. szakasz; a 34.7-34.8 csomópont-értelmezését a 45.1 helyesbíti; a 45.4 `+0x40` állítását a 45.9 helyesbíti; a 45.9-45.14 új); `docs/specs/00-index.md` (a lap sora).

### 45.15 Helyesbítés: a 0x0047bee0 nem termelő, hanem a munkasor-létrehozó (2026-10-22)

**Bizonyíték.** A 2026-10-22-i Ghidra-köteg (`referencia/ghidra/2026-10-22-ghidra-sor-227-229.txt`) és az asm (`annot_disasm.py`, `0x0047bee0`, 86 bájt) egyezik: a törzs `0x0047bee0`-`0x0047bf35`, a `ret` a `0x0047bf35`-nél van. A 45.12 szakasz „a törzs csak `0x0047c0d9`-nél ér `ret`-re" állítása lineáris diszasszemblálás volt, amely a függvényhatáron átlépett; a `0x0047c0d9` egy másik függvényé.

A törzs: ha `[edi+0x2a20]` nulla, lefoglal 0x84 bájtot (`0x0097c5d0`), a `0x00498630` üres sorba fűz, a vtábla `0x00c82f70` (RTTI: `CFaceDetector::Queue`), `[esi+0x80] = edi` (tulajdonos), `[esi+0x7c] = 0`. Ezután `[edi+0x2a20] = esi`, `0x0097b350(0, 1)`, végül a vtábla `+0xc` slotjának hívása `(-1, 0)` argumentumokkal. **Nem ír munkatételt.**

Hívói (xref): `0x00403640`, `0x004860e0`, `0x00487340`, `0x005cf5b0`.

**Bizonyítottsági fok:** megerősített (két út: Ghidra-C és asm egyezik).
**A 45.12 „Producer-jelölt: 0x0047bee0" ELVETVE.**

### 45.16 N1: a munkatétel jelzője a 0x004985e0 másolatából jön; a forrásrekord NINCS MEG

**Megerősített elrendezés** (asm, `0x004985e0`, 36 bájt): a célrekord (`eax`) `+0x0 = 0`, `+0x4 = 0`, `+0x8 = forrás+0x0`, `+0xc = forrás+0x4`, `+0x10 = forrás+0x8`, `+0x14 = forrás+0xc`, `+0x18 = 0`.

A célrekord az `X` csomópont; a 0x0047b020 `this`-e `X+4` (45.1). Így a 0x0047b031 `cmp byte ptr [item+0x10], 0` ellenőrzése az `X+0x14` bájtját olvassa, vagyis a másolat **forrás `+0xc` dword-jének alsó bájtját**. Ez a 45.12 táblázatának pontosítása: a `+0x14` írás helyes, a forrásmezők ott nem voltak pontosak.

| hívó (hívási hely) | a forrás `+0xc` (a jelző) honnan jön | állapot |
|---|---|---|
| `0x0045a9d0` (`0x0045b8e8`); egyetlen hívója `0x0047e470` | `[esp+0x44] ← ecx` a `0x0045b8ae` ágban; az ágba lépés feltétele: `[rekord] & 0xffffff00 != 0` és `byte [rekord+4] != 0` | az `ecx` értéke az ágba lépés útjától függ: NINCS MEG |
| `0x00484820` (`0x00484a57`); 11 hívója | a `[esi+0xd4]` virtuális hívás egyik kimeneti paramétere (`&[esp+0xcc]`) | az `esi` osztálya NINCS MEG. A `0x00484820` fájl-kiírási út (sztringjei: `.picasa.ini`, `faces`, `facedata`, `FRWriteFaceDataINI`), ezért nem bizonyított, hogy a munkasor rekordját adja |
| `0x00425f60` (`0x0042884d`) | NINCS MEG | nem vizsgált |

**Bizonyított lánc:** a munkatétel `this`-ét a `0x004987c0` munkasor-fogyasztó adja (a `0x0047b020` egyetlen hívója); a `0x004987c0` hívói a `0x0047bc80`-tól származnak (háromszor). A rekord termelője ezen a láncon NINCS MEG.

**A visszaállítás (`0x0048ec30`) nem a jelző írója.** A 57 bájtos függvény (a `0x0048e5da` hét hívásából) két mutatót (`+0x4`, `+0xc`) szabadít fel, a `+0x8` és `+0x10` dword-öket pedig `and ..., 1`-gyel csak a 0. bitre vágja. A jelző 0. bitje tehát a visszaállításon át megmarad. Hogy melyik rekordra vonatkozik, NINCS MEG (az `esi` forrását a `0x0048e5da`-ban nem követtem).

**Bizonyítottsági fok:** feltételes. A 0x0047bee0 kizárva (45.15); a 0x0048ec30 nem törli a bit 0-t, tehát nem a jelző írója.

### 45.17 N3: a detektor-objektum azonosítva, a Red-belépés mért; a kép-doboz hívása és a bemeneti méret NINCS MEG

**Az objektum.** `this+0x2e10` (a `0x0045f0c0` írja, `this+0x2e14 = 1`). Vtábla: `0x00ca8754` (a fájlból olvasva, pefile). Méret: 0xb0 bájt (`0x0097c5d0(0xb0)`). Létrehozó: `0x0045f0c0`, amelyet több hely hív (`0x0048e590`, `0x0045f2f0`, `0x0047a680`, `0x0047afc0`, `0x0048af60`, `0x0048c440`, `0x006c37c0`). A `0x0048e590` a `this+0x2e14` vagy `this+0x2e10` nullaságát vizsgálja; a hívója a `0x0048ef20`. Konstruktor: `0x006ccbb0` (58 bájt): vtábla, `+0x8`-`+0x1c` nulla, két alobjektum-inicializálás (`0x0097adb0`).

**Betöltés.** Slot 0: `0x006cccb0` (19 bájt, `call 0x6ccd90; ret 8`). A `0x006ccd90` (567 bájt) a `Red.dll` sztringet (`0x00ca8724`) tölti be, a REDENTRY-objektumot a `0x00d35e44` globálisban tartja, a `0x00d35e48` nem nulla értéke jelzi, hogy a betöltés megtörtént (`0x006ccdd0`-`0x006ccde0`). A REDENTRY vtábla slot 0 hívásának kimenete a `this+0x8`, bemenete az útvonal, vagy a `0x00c7f979` sztring. A `0x00d35e44` objektum vtáblája és a slot 0 célja NINCS MEG (Red-oldali).

**Konfiguráció.** Slot 0x34 (`0x006cdf30`, 95 bájt): a REDENTRY vtábla `+0x4c` slotjának hívása a `this+0x8`-`+0x1c` hat dword-jével és a `Preferences\FRTemplateChecking` értékével. A hívás feltétele (Ghidra-C, `0x0045f0c0`): a slot 0 visszatérése nulla.

**Pontszám (45.3, változatlan).** Slot 0x2c (`0x006cde50`) → REDENTRY `+0x44` → `0x10001570` → `0x100057c0`: jelöltleírónként a mintákkal vett legnagyobb hasonlóság. A küszöb a `this+0x34a4` = 0,50 (`0x0048e1f0`, 44.1).

**960 px.** A detektor-objektum 20 függvényében (slot `0x00`-`0x4c`, plusz `0x0048e1f0`, `0x0048e5da`) nincs `0x3c0` (960) immediate. Ez csak az immediate-kódolásra állít; a futásidejű méret a rekordból jöhet (45.4: `param_2[5] >> 1`), ezért nem zárható ki.

| állítás | forrás | bizonyítottság |
|---|---|---|
| detektor-objektum: vtábla `0x00ca8754`, 0xb0 bájt, a `0x0045f0c0` hozza létre, belépés a `0x0048e590`-ből | bináris (`0x0045f0c0`, `0x006ccbb0`, `0x0048ef20` → `0x0048e590` xref, vtábla-olvasás) | megerősített |
| Red-betöltés a `Red.dll` sztringgel és a REDENTRY-globálissal | bináris (`0x006ccd90`, sztring-xref) | megerősített |
| slot 0x34 → REDENTRY `+0x4c`, hat dword-os blokk és FRTemplateChecking-jelző | bináris (`0x006cdf30`, asm) | feltételes (egy út; a Red-oldali szignatúra NINCS MEG) |
| 960 px nincs immediate-ként a detektor-útban | bináris (immediate-keresés, 22 függvény) | feltételes (negatív, egy út) |
| a kép-doboz kereső Red-belépése, a bemeneti méret, a belső detektorküszöb, a mért felismerési arány | NINCS MEG | nyitott |

**Cáfoló kísérlet.** Azt próbáltam igazolni, hogy a `0x0048e5da` 960 px-re méretez. A `0x0048e5da`-ban és a `0x0048e1f0`-ben nincs `0x3c0` immediate. A cáfolat gyenge: a méret futásidőben a rekordból jöhet, ezt a diszasszembly nem látja.

**Nyitott pontok:** a kép-doboz hívás Red-belépése (REDENTRY-slot vagy a `vfr_VdeFaceFinder` vtábla), a bemeneti méret és a belső küszöb.

### 45.18 Ghidra-kör kérések (ebből a körből, sorrendben)

- Ghidra-kör kell: 0x0047e470 - a `0x0045a9d0` egyetlen hívója: melyik rekordból és melyik feltétellel adja a `0x0045b8ae` ág `ecx` értékét (a munkatétel jelzője, a másolat `src+0xc`). [blokkoló N1]
- Ghidra-kör kell: 0x0045a9d0 - a `0x0045b8ae` ágba lépés feltétele, és a `0x0049d560` célja a `0x0045b8e8` után (munkasor-beszúrás-e). [blokkoló N1]
- Ghidra-kör kell: 0x00484820 - az `esi` osztálya és a `[vtábla+0xd4]` célja (a kimeneti paraméter), csak ha a rekord a munkasorba jut (a `0x00506830` tároló-hívás célja). [blokkoló N1]
- Ghidra-kör kell: 0x006ccd90 - a REDENTRY vtábla slot 0 hívásának argumentumai, a `0x00c7f979` sztring és a `0x00d35e48` jelző szerepe. [blokkoló N3]
- Ghidra-kör kell: a REDENTRY (`0x00d35e44`) vtábla `+0x4c` célja és a kép-doboz kereső slot C-kódja, a bemeneti méret mezőjével. [blokkoló N3]
- Ghidra-kör kell: 0x0048b840 - a `0x0048e5da` első hívása: a kép-rekord méretének forrása. [blokkoló N3]

### 45.19 Állapot, mérleg, „Kész, ha"

| pont | állapot | mivel |
|---|---|---|
| N1 | BLOKKOLT | a jelző forrása megvan (45.16): a munkatétel `X+0x14` a `0x004985e0` másolat `src+0xc`-je; a forrásrekord termelője és belépési útja NINCS MEG; Ghidra-kérés 45.18 1-3. pont; a döntő a kétarcú Colab-felvétel (43.4) |
| N3 | BLOKKOLT, részben | a detektor-objektum, a betöltés és a konfiguráció megvan (45.17); a kép-doboz hívás, a bemeneti méret és a belső küszöb NINCS MEG (45.18 4-6. pont) |
| N7 | BLOKKOLT | változatlan (45.5, 44.3) |
| N4, N5, N6, N8 | LEZÁRVA | változatlan (36-37. szakasz) |

**„Kész, ha" pontonként (45.15-45.19):** N1: ⛔ az író nem található, a forrásrekord nincs azonosítva; ✅ a jelző útja a másolatig. N3: ⛔ a belső küszöb és a méret NINCS MEG; ✅ a detektor-objektum és a betöltés. N7: ⛔.

**Fejlesztési eltérés:** ebből a körből nincs bizonyított eltérés. A 0,9-es YuNet-beállítás és a 960 px-es méret összevetése továbbra sem érvényes (45.3). A Ghidra-kérések a hívó várólistájába mennek; új kutatási jegy nem szükséges.

**Nyitott kérdések mérlege (45.15-45.19):** 1 helyesbítés (45.12 „Producer-jelölt" ELVETVE) · 0 lezárva · 3 blokkolt (N1, N3, N7) · 0 hatókörön kívül · 0 csak nyitva.

**Módosított fájlok (45.15-45.19):** `docs/specs/picasa-arcfelismeres.md` (új 45.15-45.19 szakasz; a 45.12 „Producer-jelölt" állítását a 45.15 elveti); `docs/specs/00-index.md` (a lap sorában új bejegyzés).

### 45.20 N1: a jelző forrásrekordja, a termelői lánc és a munkasor-kapcsolat (2026-10-22, 231-235. köteg)

**Hatókör.** A 45.18 első három kérése (`0x0047e470`, `0x0045a9d0`, `0x00484820`) C-kódja a `referencia/ghidra/2026-10-22-ghidra-sor-231-235.txt` kötegből származik; a C-t az asm (`annot_disasm.py`, helyi capstone) ellenőrizte. A hívási térképet indextől független módon mértem: `paszta.memoria_kapu()`, majd egyetlen teljes `.text`-pásztázás (`paszta.utasitasok(detail=False)`, 2 884 879 utasítás), amely minden `call` és `j*` célt összevet a kért címekkel. A közvetett (vtábla- és regiszteres) hívásokat ez a térkép nem látja.

**Helyesbítés (45.16).** A 45.16 „a célrekord (`eax`) az `X` csomópont" állítása nincs igazolva. Az asm szerint a másolat célja a `0x0045a9d0` verem-rekordja (`[esp+0x70]`, hét dword), amelyet a `0x0049d560` első argumentumként kap (`0x0045b8f7`). A rekord `+0x4` mezőjét (`[esp+0x74]`) a `0x0045a9d0` darabszámként olvassa (`>> 1`). Hogy ez a rekord lesz-e a munkasor-csomópont `X`, azt a `0x0049d560` és a `0x004841f0` célja dönti el. Ez NINCS MEG (45.22).

**Megerősített: a forrásrekord `{0, 0, d8, d4}`.** Asm, a `0x0045a9d0`-ban:
- `0x0045b4b5`: `call 0x0042a440` (gyorsítótár-út, `param_3` nemnulla esetén). Ha `al = 0`, a `0x0045b4c8`-`0x0045b4e3` ágban a `this+0x48` alobjektum vtábla-slotja `+0xd4` hívódik: `ecx = this+0x48`, argumentumok: a kép-index, `&[esp+0x4c]` (d8) és `&[esp+0x50]` (d4).
- `0x0045b4e5`-`0x0045b4f9`: `edx = [esp+0x4c]` (d8), `ecx = [esp+0x50]` (d4). Mindkettő nem lehet nulla.
- `0x0045b8ae`-`0x0045b8e4`: a `{0, 0, d8, d4}` forrás `[esp+0x38]`-tól áll; a `0x0045b8e8` hívja a `0x004985e0`-t, a célja `[esp+0x70]`.
- `0x004985e0` (36 bájt): cél `+0x8 = forrás+0x0`, `+0xc = forrás+0x4`, `+0x10 = forrás+0x8`, `+0x14 = forrás+0xc`; a `+0x0`, `+0x4` és `+0x18` nulla.

Második előállító, ugyanaz a minta: a `0x00484820`-ban a `0x00484a0c`-`0x00484a2f` sorok `call eax`-ja a `[vtábla+0xd4]` hívás (`ecx = esi`, az alobjektum), argumentumok: a kép-index, `&[esp+0xdc]` (d8), `&[esp+0xcc]` (d4). A `0x00484a31`-`0x00484a57` sorokban ezek a `{0, 0, d8, d4}` rekordba kerülnek, majd `call 0x004985e0`.

**A jelző (megerősített elrendezés).** A munkatétel jelző bájtja (`X+0x14`, a `0x0047b020` szerint az `item+0x10`) a `d4` alsó bájtja. Mivel előtte a `d4 ≠ 0` kapu áll, a jelző csak akkor nulla, ha a `d4` a 256 többszöröse.

**Termelői lánc (direkt hívások, indextől független térkép):**

| cél | direkt hívási hely(ek) |
|---|---|
| `0x0047b020` (munkatétel-feldolgozó) | `0x00498933` (a `0x004987c0`-ban) |
| `0x0045a9d0` | `0x0047e77e` (a `0x0047e470`-ben) |
| `0x0047e470` | `0x006a12da` (a `0x006a10b0`-ban) |
| `0x004985e0` (másolat) | `0x0042884d` (a `0x00425f60`-ban), `0x0045b8e8` (a `0x0045a9d0`-ban), `0x00484a57` (a `0x00484820`-ban) |
| `0x0049d560` | `0x0045b8f7` (a `0x0045a9d0`-ban) |
| `0x0048e590` | `0x0049002a` (a `0x0048ef20`-ban) |

A `0x0047e470` `param_3` (`cVar2`) képzése csak C-szinten olvasott: a `0x0045a9d0` `param_3 = 0` esetén kötelezően a vtábla-hívást végzi, `param_3 = 1` esetén előbb a `0x0042a440` próbálkozik. Ennek asm-ellenőrzése nincs elvégezve.

**Feltételes: mit jelent a `d4`.** A `d4` a `+0xd4` metódus kimeneti paramétere. Az alobjektum osztálya és a slot célja NINCS MEG. Ha a `d4` a Picasa-vektor alakja (darabszám `<<1`, a 0. bit jelző, mint a `0x0048b840`-nél a `[rekord+4] >> 1`), akkor a jelző a darabszám és a jelzőbit együttes alsó bájtja. Ha csak a darabszám, akkor a képen lévő arcrekordok száma. A jelenlegi bizonyíték a két lehetőséget nem választja szét.

**Cáfoló kísérlet (15.2).** Azt próbáltam megcáfolni, hogy a `+0x14`-et csak a másolat írja. A direkt hívási térkép három másolási helyet ad, más direkt hívású író nincs. A cáfolat gyenge: vtábla- és regiszteres hívásokat a térkép nem lát, a `d4` jelentését pedig nem vizsgáltam.

**Mit mond ez N1-re.** A `0x0047b020` nemnulla ága (`0x0047b031`-`0x0047b049`, megerősített, 45.2) nem futtat képenkénti felismerést. Ez érvényes minden olyan képre, amelynek `d4 & 0xff ≠ 0`. Hogy ez a névvel rendelkező fotókra esik-e, attól függ, mit jelent a `d4`, és ez NINCS MEG. A munkatétel-út és a munkasor kapcsolata sincs lezárva.

**Bizonyítottsági fok.** A rekordelrendezés és a jelzőbájt forrása megerősített (asm, két előállító, egy másoló). A `d4` jelentése feltételes. A munkasor-kapcsolat NINCS MEG.

### 45.21 N3: a Red-betöltés argumentumai és a kép-rekord darabszáma (2026-10-22)

**Megerősített: a betöltő hívói és argumentumai.**
- A `0x006ccd90` három argumentumot kap (`ret 0xc`). Két hívója van: `0x00871e39` (a `0x00871d70`-ben, közvetlen) és `0x006cccbb` (a `0x006cccb0`-ban, amely a `0x00ca8754` detektor-vtábla 0. slotja, közvetve hívott).
- A `0x00871e39` hívás csak akkor fut le, ha a `0x00871d70` második argumentuma nulla (`cmp ebp, esi`, `jne 0x00871e4b` a `0x00871e28`-nál). Argumentumai: (1) a `this`, a hívó verem-objektuma (`[esp+0x98]`; a közvetlenül előtte `[esp+0x94]`-re írt vtábla `0x00ca8754`); (2) a hívó objektum `+0x54` mezőjének sztringadata, vagy üres sztring (`0x00c7f979`), ha nulla; (3) a `[0x00d689f0]` globális sztring és a `"plugins"` (`0x00c818c4`) összefűzése (a `0x00408390` hívás, a művelet nincs azonosítva).
- A `0x006ccd90` csak akkor tölti be a Red-motort (`0x006cc9e0(&0x00d35e40, útvonal)`), ha `[0x00d35e48] = 0` vagy `[0x00d35e44] = 0` (`0x006ccdd0`-`0x006ccde0`). Nemnulla visszatérés: `-1`.
- Sikeres ág: a REDENTRY-objektum (`[0x00d35e44]`) vtábla 0. slotja, `ecx = REDENTRY`, argumentumok: `this+8` (kimeneti fogantyú) és a 2. argumentum sztringadata (vagy `0x00c7f979`). A visszatérési érték `eax`.
- Hibaág (`eax = 0`, `0x006ccf34`): `this` vtábla `+0x10` slotja `(20.0, 10000.0)`, a `+0x14` slotja `(45.0)`. Ezek a `0x006cd070` (`"set range"`, `0x00ca872c`) és a `0x006cd0d0` (`"set roll"`, `0x00ca8738`) slotok. Mindkettő a REDENTRY-nek továbbít, és csak akkor, ha `[0x00d35e48] ≠ 0` és `[0x00d35e44] ≠ 0`; különben `-1`.
- Sikeres fogantyú esetén a 4. és az 5. slot nem hívódik.

**Megerősített konstansok** (`.rdata`, pefile): `0x00cf4974` = 20.0 (`0x41a00000`), `0x00cf4348` = 10000.0 (`0x461c4000`), `0x00cf4c38` = 45.0 (`0x42340000`). Sztringek: `"Red.dll"` `0x00ca8724`, `"plugins"` `0x00c818c4`, üres sztring `0x00c7f979`, `"set range"` `0x00ca872c`, `"set roll"` `0x00ca8738`.

**Mértékegység és szerep: NINCS MEG.** A két float a REDENTRY `set range` és `set roll` metódusának argumentuma. A Red-oldali egység és jelentés (arcméret-tartomány, pixel vagy más) nincs megnézve, ezért a 960 képpontos értékhez nem köthető.

**Cáfoló kísérlet.** Azt vizsgáltam, lehet-e a `set range` (20.0, 10000.0) a 960 px-es méret. Ebből a kötegből ez sem igazolható, sem cáfolható: a betöltő-ág nem tartalmaz 960-as immediate-t, de a Red-oldal `set range` implementációja nincs megvizsgálva, a futásidejű méret pedig a rekordból is jöhet.

**A kép-rekord darabszáma (megerősített a `0x0048e5da` oldalról).**
- `0x0048e590` (belépés): az 1. argumentum a `this` (`esi`), a 2. a megszakítási jelző (`ebx`), a 4. a kép-rekord (`ebp`). A `0x0048e5cb` `jne` ugyanezekkel az értékekkel ugrik a `0x0048e5da`-ra.
- `0x0048e5e9`: `call 0x0048b840` (`this`, rekord, jelző).
- `0x0048e617`: `mov esi, [ebp+4]` és `shr esi, 1`. A kép-rekord darabszáma: `[rekord+4] >> 1`.
- A rekord elemei dword-ök (`0x0048b840`: `[rekord+0] + i*4`), tehát a darabszám nem képpontméret.
- A rekordot a `0x0048ef20` építi (a `0x0049002a`-nál hívja a `0x0048e590`-t). A `0x0048ef20` C-kódja nincs a kötegben: NINCS MEG.

**Mit mond ez N3-ra.** A „kép-rekord mérete" a rekord darabszáma (dword-elemek), nem képpont. A 960 px-es méret ebből a láncból nem olvasható ki. A detektor bemeneti mérete és belső küszöbe továbbra is NINCS MEG (45.11, 45.17).

**Bizonyítottsági fok.** A betöltő argumentumai és a konstansok megerősítettek (asm, két hívó, `.rdata`). A `set range` és a `set roll` szerepe feltételes, csak a bináris sztringjeiből következik. A darabszám-képlet megerősített; a rekord eredete NINCS MEG.

### 45.22 Ghidra-kör kérések (új, sorrendben)

- Ghidra-kör kell: 0x0048ef20 - a `0x0048e590` 4. argumentumának (kép-rekord) összeállítása: melyik vektorból, milyen dword-elemekkel, és a `0x0047b149` hívás argumentumai. [blokkoló N3]
- Ghidra-kör kell: 0x006cc9e0 - a Red-betöltő: a `(&0x00d35e40, útvonal)` argumentumok értelme, és a `0x00d35e44` / `0x00d35e48` beállítása. [blokkoló N3]
- Ghidra-kör kell: REDENTRY (`0x00d35e44`) vtábla `+0x4c` célja és a kép-doboz kereső slot C-kódja (a 45.18 5. pontja, még nyitva). [blokkoló N3]
- Ghidra-kör kell: 0x0042a440 - a gyorsítótár-út: honnan adja a `d8` / `d4` párt (hívói: `0x0044844e`, `0x0045b4b5`). [blokkoló N1]
- Ghidra-kör kell: 0x006a10b0 - a `0x0047e470` hívója: a `this` osztálya, a `+0x48` alobjektum vtáblája, és a `+0xd4` slot célja a `d8` / `d4` kimenettel. [blokkoló N1]
- Ghidra-kör kell: 0x004841f0 - a `0x0045a9d0` által felépített rekord-vektor (`[esp+0x74]`, a `0x0045b8fc` körül) célja: munkasor-beszúrás vagy `.picasa.ini`-írás. [blokkoló N1]
- Ghidra-kör kell: 0x0049d560 - a hét dword-os célrekord beszúrása a vektorba: a második argumentum (`local_f4`) szerepe. [blokkoló N1]

### 45.23 Állapot, mérleg, „Kész, ha"

| pont | állapot | mivel |
|---|---|---|
| N1 | BLOKKOLT | a jelzőbájt forrása megerősített (45.20); a `d4` jelentése és a munkasor-kapcsolat NINCS MEG; Ghidra-kör a 45.22 szerint (0x004841f0, 0x0049d560, 0x0042a440, 0x006a10b0); a döntő a kétarcú Colab-felvétel (43.4) |
| N3 | BLOKKOLT, részben | a Red-betöltés argumentumai megerősítettek (45.21); a darabszám-képlet megerősített; a rekord eredete (0x0048ef20), a detektor bemeneti mérete és a 960 px NINCS MEG (45.22) |
| N7 | BLOKKOLT | változatlan (45.5, 44.3) |
| N4, N5, N6, N8 | LEZÁRVA | változatlan (36-37. szakasz) |

**A 45.18 kérései:** 1. (`0x0047e470`): a hívó és a `param_3` képzése C-szinten, asm nélkül; 2. (`0x0045a9d0`, `ecx`-ág): a `d4`, megerősített; 3. (`0x00484820`): a `+0xd4` slot célja NINCS MEG (45.22); 4. (`0x006ccd90`): lezárva (45.21); 5. (REDENTRY `+0x4c`): nyitva (45.22); 6. (`0x0048b840`): a darabszám-képlet lezárva, a rekord eredete nyitva (45.21).

**„Kész, ha" pontonként (45.20-45.21):** N1: ✅ a jelzőbájt forrása bináris címekkel (`0x0045b4e5`-`0x0045b8e8`, `0x00484a0c`-`0x00484a57`, `0x004985e0`); ⛔ a `d4` jelentése és a munkasor-kapcsolat. N3: ✅ a betöltő hívói és argumentumai (`0x00871e39`, `0x006ccd90`), a konstansok (`0x00cf4974`, `0x00cf4348`, `0x00cf4c38`) és a darabszám-képlet (`0x0048e617`); ⛔ a detektor bemeneti mérete és a 960 px. N7: ⛔ változatlan.

**Megvalósítandó eltérés:** ebből a körből nincs bizonyított eltérés. A jelzőbájt-szabály és a Red-konstansok ismertek, de a PicasaPy-oldali megfelelő változtatás egyike sincs igazolva. A 0,9-es YuNet-beállítás és a 960 px-es méret összevetése továbbra sem érvényes (45.3, 45.11).

**Nyitott kérdések mérlege (45.20-45.23):** 0 csak nyitva · 3 blokkolt (N1, N3, N7) · 0 hatókörön kívül · 0 lezárva új kérdésből. Helyesbítés: 1 (a 45.16 „célrekord = X" állítása, lásd 45.20).

**Módosított fájlok (45.20-45.23):** `docs/specs/picasa-arcfelismeres.md` (új 45.20-45.23 szakasz a 45. szakasz után; a 45.16 célrekord-állítása helyesbítve). A `docs/specs/00-index.md`-t nem módosítottam, azt a hívó vezeti.

## 46. #5184, helyi kutatói kör: az új Ghidra-köteg pontosít, de N1/N3/N7 nyitva marad (2026-10-22)

**Hatókör.** A 2026-10-22-i `ghidra-sor-241-246.txt` C-kódját (`0x0048ef20`, `0x006cc9e0`, `0x0042a440`, `0x006a10b0`, `0x004841f0`, `0x0049d560`) a bináris-index mérete alapján célzott helyi diszasszemblálással vetettem össze. A Red.dll `0x100057c0` és `0x10001570` dekompilált útját a helyi Capstone-kimenet ellenőrzi. Futó Picasa és új Colab-felvétel ebben a körben nem volt; a mérőadat-archívumban nincs ehhez a kérdéshez használható arckészlet. Kódhoz, tesztekhez, GitHubhoz és NAS-hoz nem nyúltam.

### 46.1 N1: két külön jelzőút, a névhez kötés továbbra sincs meg

- **A jelző, amely a `0x0047b020` útját kapuzza:** a helyi asm a `0x0047b031`-en az `[item+0x10]` bájtot ellenőrzi. Nem nulla értéknél a `0x0048bd80`-at hívja, majd a `0x0047b049`-en visszatér; ezen az ágon nincs `0x0048ef20` hívás. Nulla értéknél a későbbi kapuk után a `0x0047b149` hívja a `0x0048ef20`-at. Ez csak az adott worker útvonal viselkedését bizonyítja, a bájt név szerinti jelentését nem.
- **Másik, ettől különböző jelző a `0x0047e470`-ben:** a Ghidra C-kód a `0x004edf60`-nal töltött helyi rekord `+0x1d` bájtján vizsgálja a `0x02` bitet. Beállított bitnél korán kilép, így azon a híváson nem jut el a `0x0045a9d0`-ig. Ez nem azonos a `0x0047e470` később képzett `cVar2` értékkel, amelyet a `0x0045a9d0` kap; a két jelzőt és a `0x0047b020` `[item+0x10]` bájtját nem szabad egyetlen név- vagy arctulajdonságnak összevonni.
- **A munkasor-környezet:** a `0x006a10b0` egy sort vesz ki (`0x00506270`), majd az `unaff_EDI+0x14` objektummal a `0x0047e470`-et hívja. Ez megerősíti a worker-hívási kapcsolatot, de a sorrekordot nem kapcsolja össze névvel vagy kontaktazonosítóval.
- **A kimeneti rekord útja:** a `0x0042a440` egy ismeretlen `this+0x48` vtable `+0xd8` metódusát hívja, majd `.picasa.ini`-t nyitó és feldolgozó útvonalat használ; a `d8`/`d4` kimenetek szemantikája nincs meg. A `0x004841f0` C-törzse rekordvektoron jár, az `UnknownPerson` sztringre hivatkozik és több segédfüggvényt hív, de a vizsgált törzs nem nevezi meg a munkasor beszúrását. A `0x0049d560` sztringből rekordokat készít, de az `X` munkatétellel való azonosságot nem állapítja meg.

**N1 mérlege:** megerősített az adott bájt- és bitkapuk vezérlési hatása; **NINCS MEG**, hogy bármelyik a már megnevezett fotó/arc jelzője-e, és hogy a második, ismeretlen arcot az eredeti utána felajánlja-e. A döntő továbbra is ugyanannak a kétarcú fotónak a név előtti és név utáni eredeti Picasa-felvétele, név nélküli kontrollal (43.4).

### 46.2 N3: a `0x0048ef20` gyűjteményt állít elő; a Red callback pontszámot, nem detektorküszöböt ad

- **Picasa oldali bemenet:** a `0x0047b020` a munkatétel `+8` mezőjét adja át harmadik argumentumként, a `+0xc` mezőt pedig floatként a negyedik argumentumba. A `0x0048ef20` harmadik argumentuma nem nulla esetén egy négybájtos, egy elemes belső listát készít ebből az értékből; nulla esetén másik listát kér le. A `0x0048f039` a tárolt elemszámot egész `shr 1` utasítással állítja elő. A `0x0049002a` a `0x0048e590`-et hívja. Ez a rekord/lista útja, nem pixelpuffer vagy szélesség-magasság pár bizonyítéka. Az érték mezőjének személyes vagy képi jelentése ebből a törzsből nem következik.
- **A Red.dll oldali út:** a `0x100057c0` két rekordhalmazt jár be, a rekordok első DWORD-jából `>> 2` értéket ad a virtuális `+0x40` műveletnek, majd a belső ciklus legnagyobb float eredményét írja külső elemenként a kimeneti tömbbe (`0x10005869`-`0x10005888`, `0x100058d2`-`0x100058d8`). A `0x10001570` csak siker-/hibavisszatérést csomagol. A Red-függvényben nincs olyan bizonyíték, amely a belső arcdetektor küszöbét vagy a bemeneti kép méretét megadná.
- **A dekompiláló típuskorlátja:** a Red C-kimenet a `0x100057ed` nullával való összevetését float-összehasonlításként jeleníti meg. A tényleges utasítás `cmp dword ptr [ebp+0x1c], 0`; ezt a veremhelyet a `0x1000582e` később a maximumgyűjtés nullázására használja. A `0x0048ef20` elemszámát is floatként mutatja a C-kimenet, míg az asm `shr eax,1`-et hajt végre. A típusos szemantikát ezért az utasításokból kell megállapítani, nem a Ghidra által kiosztott C-típusból.

**N3 mérlege:** a `0,50` (FRRecommendIncludeLimit), illetve a `0,85` (FRSuggestionThreshold) a korábban azonosított hasonlósági/javaslati út értékei; ezek nem igazolják a Red detektorának küszöbét. Az eredeti belső detektorküszöb, bemeneti képméret és pontos felismerési arány **NINCS MEG**. A PicasaPy helyi forrásában deklarált `0,9` és `960 px` az eredeti Red-beállításokkal nem hasonlítható össze mérés nélkül. A szükséges arányméréshez tételes, címkézett, változatlan képkészleten kell mindkét program futását mérni (43.4; 45.6).

### 46.3 N7 és a már lezárt pontok

`contactmgr.fen` nem deklarál kijelölési módot, `0x007b9630` egy korábban vizsgált útja egy kijelölt indexet olvas, a job-186 felvétel pedig csak egy sort mutat. Ezek együtt sem bizonyítják, hogy Ctrl- vagy Shift-kattintással nem jelölhető ki több személy. **N7 NINCS MEG**; két személlyel kell rögzíteni az első kattintást, a Ctrl-kattintást és a Shift-kattintást, valamint a `Delete Person` gomb állapotát.

| jegypont | állapot | bizonyíték |
|---|---|---|
| N1: névvel rendelkező fotón további ismeretlen arc | ⛔ Nyitott | A worker-kapu binárisan ismert (`0x0047b020`), de a jelző és a név/arc kapcsolata, valamint a második arc eredménye NINCS MEG. |
| N3: eredeti arány, detektorküszöb és bemeneti méret | ⛔ Nyitott | Red-pontszámút bináris (`0x100057c0`, `0x10001570`); a három keresett eredeti érték NINCS MEG. |
| N4: a keret és név alapértelmezett láthatósága | ✅ Lezárt | Mérés (`job-187`): a megnevezett arcon alapból nincs keret és név. |
| N5: személyszintű mellőzés | ✅ Lezárt | Mérés (`job-222..226`): nincs személyszintű Ignore; a mellőzés arcszintű. |
| N6: személy törlése és hatása az arcokra | ✅ Lezárt | Mérés (`job-222/224`): a `faces=` sor törlődik, a `[Contacts2]` megmarad; a javítás #5391. |
| N7: People Manager kijelölési modellje | ⛔ Nyitott | Többes kijelölést próbáló, két személyes felvétel NINCS MEG. |
| N8: People Manager referencia-képernyőkép | ✅ Lezárt | Mérés (`job-186`, 24. kép): a 631×351 ablak és vezérlői rögzítve. |

### 46.4 Két független út, cáfoló próba és bizonyítottság

- **A út (N1):** a `0x0047b020` helyi utasításszintű olvasata megmutatja az `[item+0x10]` kaput és a `0x0048ef20` hívás előtti visszatérést. **B út:** a külön `0x006a10b0` → `0x0047e470` worker-lánc C-kódja megmutatja, hogy a munkasor-kivétel és a `0x0045a9d0` előtti másik két kapu külön út. A két út egyezik abban, hogy léteznek kapuk; egyik sem köti azokat bizonyítottan a névhez rendelt archoz.
- **A út (N3):** a Picasa `0x0048ef20` gyűjtemény-/hívási útja. **B út:** a Red.dll `0x100057c0` + `0x10001570` pontszám- és visszatérési útja. Külön modul- és hívási rétegből származnak; mindkettő összeegyeztethető a hasonlósági pontszám számításával, de egyik sem ad Red-detektorküszöböt, pixelméretet vagy mért arányt.
- **Cáfoló próba:** azt próbáltam igazolni, hogy a Red C-kódban megjelenő nullára vonatkozó feltétel a Red detektorküszöbe. A Capstone `0x100057ed`-nél egész DWORD-összehasonlítást mutat; a `0x1000582e` ugyanazt a veremhelyet a maximum pontszám nullázására írja. A Red callback további utasításai maximumot választanak és tömbbe írnak. A hipotézis nem áll meg. A cáfolót ugyanazon közvetlen utasításolvasattal ellenőriztem; a virtuális `+0x40` művelet matematikája ettől még külön ismeretlen.
- **Összesített bizonyítottsági fok: nyitott.** A kapuk, gyűjteményművelet és Red-pontszámút utasításszinten ellenőrzött. N1, N3 termékértékei és N7 kijelölési modellje nincsenek eldöntve; eltérés a PicasaPyhoz képest nem bizonyított.

### 46.5 A jegy „Kész, ha” pontjai, jegytörzs és további munka

**Pontonként:** N1 ⛔ (kétarcú név előtti/utáni mérés kell); N3 ⛔ (tételes, címkézett képkészleten pontos eredeti mérés, valamint a Red-detektor mérete és küszöbe kell); N4 ✅; N5 ✅; N6 ✅; N7 ⛔ (két személyes Ctrl/Shift-felvétel kell); N8 ✅. A jegy ezért **nem zárható le**.

**Javasolt jegytörzs-bővítés:** „A spec 46. szakasza rögzíti az új bináris kör eredményét. N4, N5, N6 és N8 bizonyítékkal lezárva; N1, N3 és N7 továbbra is nyitott. A `0x0047b020` jelzőág nem bizonyítja a név szerinti kizárást; a `0x100057c0` maximum-hasonlóságot ír, nem ad detektorküszöböt. Eltérés nincs bizonyítva, ezért jelenleg nincs megvalósítási jegy. A lezáráshoz N1 kétarcú név előtti/utáni felvétele, N3 fagyasztott mintán mért eredeti/PicasaPy arány, Red-küszöb és bemeneti méret, N7 pedig két személyes Ctrl/Shift-felvétel kell.”

**Fejlesztői lista:** nincs; az „Eredeti / nálunk / teendő” összevetéshez N1/N3/N7 eredeti mérései hiányoznak, bizonyított eltérés nincs.

**Új kutatási jegy:** nem javasolt; mindhárom hiányzó mérés a #5184 nyitott kérdése.

**Nyitott:**
- N1: kétarcú fotó, egyik arc megnevezése után a második arc Név nélküliek/javaslat eredményének rögzítése, előtte/utána `faces=` kontrollal.
- N3: azonos, címkézett képkészleten mért arány mindkét alkalmazásban; a Red belső küszöbe és bemeneti mérete. Ghidra-kör kell: 0x0048ec30 - a `0x0048e5da` közvetett hívásai közül a detektor célja, a beméretezés és küszöb [blokkoló N3]. Ghidra-kör kell: 0x101c867c - a `vfr_VdeFaceFinder` detektáló slotja, küszöbe és bemeneti mérete [blokkoló N3].
- N7: két személyes People Manager Ctrl-/Shift-kijelölési felvétel, a törlőgomb állapotával.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (új 46. szakasz; frissíti a #5184 pontonkénti állapotát). A `docs/specs/00-index.md`-t a hívó frissíti.

## 47. #5184, helyi utánkövetés: a People-lista egy aktuális indexet tart; a kijelölési modell nyitott (2026-10-22)

**Hatókör.** Célzott indexlekérdezés és utasításszintű diszasszemblálás a People Manager útján; a helyi `Red.dll` `vfr_VdeFaceFinder` vtáblájának és a `red.cfg`-nek ellenőrzése; a mérőadat-archívum `.picasa.ini` tagjainak bejárása. Teljes `.text`-pásztázás nem történt. A `red.cfg` elemzéséhez a meglévő, csak olvasó parser futott; sem az archívumból, sem máshonnan nem bontottam ki fájlt a `.bt` alá.

### 47.1 N7: a kezelő egy aktuális sort tárol, de a Ctrl/Shift-viselkedés nyitott

- Az eredeti `runtime/contactmgr.fen` a `contacts` elemet `<list>`-ként deklarálja; a listán nincs kijelölési módot vagy jelölőnégyzeteket megadó attribútum.
- A `ContactManagerDlg` konstruktorában a `0x007b900d` a `this+0x13c` mezőt `0xffffffff` kezdőértékre állítja. A `0x007b9630` `contacts` eseményágán a listakomponens `[vtable+0x0c]` metódusának visszatérését ebbe az egy skalármezőbe írja. A vtable-kapcsolat a konstruktor által a `this+0xbc` alobjektumba tett `0x00cb7bd0` táblával egyezik.
- A `0x007ba820` Delete Person útja ugyanezt az indexet ellenőrzi a listahosszal szemben, majd az indexelt sort dolgozza fel. Ez egyetlen aktuális sor kezelését bizonyítja.

| Állítás | Forrás | Bizonyítottság |
|---|---|---|
| A People Manager kezelőútja egy aktuális kiválasztott indexet tárol és használ | bináris (`0x007b900d`, `0x007b9630`, `0x007ba820`, `0x00cb7bd0`) | megerősített erre a belső állapotra |
| Ctrl/Shift-tel egyszerre több személy kijelölhető-e | NINCS MEG; a fenti getter többes kijelölésnél is visszaadhatja az aktuális sort | nyitott; két személyes felvétel kell |

**Cáfoló próba.** Azt próbáltam levezetni, hogy az egyetlen tárolt index bizonyítja az egyszeres kijelölést. A többes kijelölésű vezérlő is tarthat egy aktuális sort, ezért ez nem cáfolja a Ctrl/Shift-támogatást. Az eredeti listavezérlő tényleges módját továbbra is csak a két személyes felvétel dönti el.

### 47.2 N3: a `vfr_VdeFaceFinder` parancságának számai nem detektorküszöbök

- A `Red.dll` `0x101c867c` táblájának 28 egymást követő bejegyzése `.text`-címre mutat; az ezt követő dword `0x101fc5a8` nem kódcím. A `+0x5c` slot célja `0x100b07b0`.
- A `0x100b07b0` által használt `0x101c8608` diagnosztikai sztring a `vfr_VdeFaceFinder::execute` metódust nevezi meg. A kód a `0x101b2cd4` (`set range`), `0x101b3d2c` (`set roll`) és `0x101c54bc` (`set roll step range`) parancsokat kezeli. A `0x101e9308` címen olvasott `float32` érték 180,0; a kód a `set roll` ágon használja, így ez nem az arcdetektor küszöbének vagy bemeneti képméretének bizonyítéka.
- A golden kapun átment `esm_parse.py` a `red.cfg` SHA-256 értékét `916d69fd9a412ea937b49f3b0b1401076193dc9be096b3af71921aeba6f51835`-ként, a DLL-ét `da370693b59d89e7d48646d9617f5f595e371f8e1828cb1aa9f12530a17c8233`-ként adta. A gyökér `vfr_VdeFaceFinder` rekord offsetje `0x7`, verziója 201, de a parser a payload sémáját nem értelmezi. A parser által `vfr_SowGrowStampClusterer` osztályúként azonosított `0x22d07e` objektum float32 hármasa `0.699999988079071 / 0.9800000190734863 / 1.0` (nyers bájtok: `33 33 33 3f 48 e1 7a 3f 00 00 80 3f`); ez nem a detektor objektuma.

**Cáfoló próba.** A `0x100b07b0` slotot és a `red.cfg` ismert float32 paraméterhármasát próbáltam a detektorküszöb jelöltjeként igazolni. Az első parancsszövegei a roll/range ágakat azonosítják; a második hármas osztálya `vfr_SowGrowStampClusterer`. Mindkét jelöltet elvetettem N3 küszöbeként. A `vfr_VdeFaceFinder` payloadja, a belső detektorküszöb, a bemeneti képméret és a pontos arány **NINCS MEG**.

### 47.3 N1: az archívum nem tartalmazza a szükséges címkézett kontrollt

A `meroadat.tar` összes `.picasa.ini` tagját bejáró mérés `matching_ini_count 0` eredményt adott a `faces=` vagy `[Contacts2]` adatot tartalmazó fájlokra. Ez azt jelenti, hogy ebből az archívumból nem állítható össze név előtti/utáni, kétarcú kontrollmérés; önmagában nem állítja, hogy a többi archívumbeli képen nincs arc. N1 bináris jelzőútját a 45-46. szakaszok tárgyalják, a névhez kötést és az eredeti második arctalálatát ez a vizsgálat nem dönti el.

| Jegypont | Állapot e kör után | Bizonyíték |
|---|---|---|
| N1 | ⛔ Nyitott | archívum-mérés: 0 releváns `.picasa.ini`; név előtti/utáni eredeti Picasa-felvétel kell |
| N3 | ⛔ Nyitott | bináris (`0x101c867c`, `0x100b07b0`, `0x101c8608`); küszöb/méret NINCS MEG; páros mért arány nincs |
| N7 | ⛔ Nyitott | bináris (`0x007b9630`, `0x007ba820`): egy aktuális index; Ctrl/Shift-felvétel NINCS MEG |
| N4, N5, N6, N8 | ✅ Lezárt | a 46.3-ban hivatkozott felvételek és jegyjavítás |

**A két független út.** N7 A út: a `contactmgr.fen` listadefiníciója; B út: a `ContactManagerDlg` vtable-ja, a kijelölésváltozási kezelő és a törlési út utasításai. Ezek egyeznek abban, hogy a kezelő egy aktuális indexet használ; a többes kijelölést nem döntik el. N3 A út: a `0x101c867c` vtable-slot címe és a `0x100b07b0` kódja; B út: a metódusdiagnosztika/parancsszövegek és a `red.cfg` osztályozott rekordjai. Ezek egyeznek abban, hogy a vizsgált 180,0 és a Stamp-hármas nem a keresett detektorküszöb. Egyik pont teljes termékviselkedése sem zárható le két bizonyított úttal.

**Nyitott:**
- N1: kétarcú kép név előtti/utáni Picasa-felvétele `faces=` kontrollal; a munkasor jelzőjének személyhez kötése továbbra is nyitott.
- N3: Ghidra-kör kell: 0x101c867c - az aktív detektáló slot célja, a bemeneti képméret és a küszöb forrása [blokkoló N3]. Az arányhoz azonos, címkézett képkészlet kell mindkét programban.
- N7: két személyes People Manager felvétel: első sor, Ctrl+kattintás, Shift-kattintás és a Delete Person gomb állapota.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (új 47. szakasz: N1 mérőadat-leltár, N3 Red.dll/red.cfg utánkövetés, N7 kijelölőút pontosítása).

## 48. #5184, helyi utánkövetés: az N1 jelző írója és az N3 virtuális célja továbbra sem azonosítható (2026-10-23)

**Hatókör.** A Picasa3.exe teljes `.text` szakaszát a kötelező `paszta.py` úton, `paszta.memoria_kapu()` hívással pásztáztam; a helyi mérés 2 884 879 utasítást dolgozott fel. A Red.dll-ben csak célzott függvényeket és a `vfr_VdeFaceFinder` vtable-adatát olvastam. Futó Picasa/Colab UI-felvétel és új, címkézett arcmérés nem volt. Kódot, tesztet, hálózatot és NAS-t nem érintettem.

### 48.1 N1: az `[item+0x10]` kapu megvan, a névhez kötés nincs

- A `0x0047b020` utasításai az `[item+0x10]` bájtot vizsgálják. Nem nulla értéknél a `0x0048bd80` ágra mennek és visszatérnek; ezen az útvonalon nem hívják a `0x0048ef20`-at. Ez a kapu hatását bizonyítja, a bájt jelentését nem.
- A 45.20-ban feltárt másolási út szerint a munkasor `X+0x14` jelző bájtja a `{0,0,d8,d4}` forrásrekord `d4` alsó bájtjából jön (`0x004985e0`); a worker az `X+4` elem `+0x10` mezőjét olvassa. A megelőző `d4 != 0` kapu és a másolás megmagyarázza a bájt útját, de **nem** a `d4` jelentését.
- A `paszta.memoria_kapu()` után végzett teljes utasításvizsgálat a közvetlen `+0x10`/`+0x14` eltolású olvasásokat és írásokat kereste. A `+0x14` sok, egymástól független függvényben előfordul, ezért az eltolás önmagában nem azonosítja a munkatétel-mezőt vagy annak szemantikáját. A pásztázás nem köti össze a `d4` kimenetet a `faces=` rekorddal, a névvel vagy egy konkrét arccal; közvetett/vtable-írókat sem old fel.
- A PicasaPy forrása a már azonosított arcot tartalmazó képet kiveszi a saját új arcfelismerési sorából (`face_scan_controller.py`, `_build_pending`). **NINCS MEG**, hogy az eredeti ugyanilyen képen felkínál-e egy további, ismeretlen arcot. A `meroadat.tar` kontrollhiánya a 47.3-ban már mérve van; új megfelelő minta nem került elő.

**N1 mérlege:** a bájt másolási útja ismert, a `d4` szemantikája és a megnevezett fotóhoz kötése nyitott; a kért eredeti viselkedés ebből nem következik. Döntő bizonyíték: ugyanazon kétarcú fotó ellenőrzött eredeti Picasa-felvétele név nélkül, majd az egyik arc megnevezése után, a Név nélküliek listájával és a `faces=` állapot rögzítésével.

### 48.2 N3: a `vfr_VdeFaceFinder` `+0x40` slotja nem azonosítható a pontszámoló hívással

- A Red.dll RTTI-indexe a `0x101c867c` címet `vfr_VdeFaceFinder::vftable`-ként jelöli. A vtable fájlbeli dwordjai szerint a `+0x40` slot célja `0x10021ad0`, a `+0x5c` sloté `0x100b07b0`.
- A `0x10021ad0` helyi diszasszemblye a `[this+0x30]` mező és a bemeneti objektum `[+4]` mezője között a `0x10005e40` segédfüggvényt hívja. A segéd a régi/új objektum számlálóit módosítja, nulla számlálónál az objektum első virtuális metódusát hívja. A `0x10021ad0` törzsében nincs lebegőpontos pontszámítás.
- Ettől külön a `0x100057c0` a stack-paraméterláncból elért objektum vtable `+0x40` slotját hívja, és az így kapott float értékek maximumát írja a kimeneti tömbbe. A vtable-t az objektum `+0x74` mezőjéből olvassa; a statikus adatokból nincs igazolva, hogy ez a `vfr_VdeFaceFinder` példánya. Emiatt a `0x10021ad0` címet nem szabad a pontszámoló callback céljaként vagy a belső detektor azonosítójaként átvenni.
- A Picasa oldali `0x006cde50` Red-belépés egy hat DWORD-os blokkot továbbít; ezekből a diszasszembly nem állít elő bizonyított szélesség/magasság párt. A belső detektorküszöb, a bemeneti képméret és az eredeti felismerési arány **NINCS MEG**. A korábbi 0,50 és 0,85 hasonlósági/javaslati értékek nem ezek az értékek (45.3, 46.2).

| Állítás | Forrás | Bizonyítottság |
|---|---|---|
| `vfr_VdeFaceFinder` vtable `+0x40` célja | bináris (`Red.dll`, `0x101c867c` → `0x10021ad0`; RTTI-index és nyers vtable-adat) | feltételes a vtable-címre; nem bizonyítja az aktív példányt |
| `0x10021ad0` tag-/objektumkezelő út, nem látható pontszámítás | bináris (`0x10021ad0`, `0x10005e40`) | feltételes, utasításszintű olvasat |
| A `0x100057c0` által használt virtuális pontszámoló cél osztálya | NINCS MEG | nyitott |
| Eredeti detektorküszöb, bemeneti képméret és mért felismerési arány | NINCS MEG | nyitott; azonos, címkézett képkészleten kell mérni |

**Cáfoló kísérlet.** Megpróbáltam igazolni, hogy a `vfr_VdeFaceFinder` `+0x40` slotja a `0x100057c0` floatot visszaadó pontszámoló callbackja. A vtable adatából a cél `0x10021ad0`; annak és a `0x10005e40`-nek az utasításolvasata tag-/objektumkezelést mutat, nem pontszámítást, miközben a `0x100057c0` a virtuális hívás után floatot fogyaszt. A feltevést elvetettem. Ellenőrző út: az RTTI-index vtable-címe és a Red.dll nyers vtable-dwordja egyezik, a célfüggvény utasításai pedig közvetlenül visszaellenőrzik a hívott segédet. Ez a cáfolat csak a két `+0x40` cél azonosságát veti el; a Red detektorát nem azonosítja.

### 48.3 N7 és a lezárt pontok

Az eredeti `contactmgr.fen` továbbra sem deklarál kijelölési módot. A `0x007b9630` egy aktuális indexet tárol, a `0x007ba820` pedig ezt az indexet használja a `Delete Person` úton. A két forrás egyezik az aktuális sor kezelésében, de egyik sem zárja ki a Ctrl/Shift-tel történő többszörös kijelölést. **N7 nyitott**; két személyes felvétel kell az első kattintás, Ctrl-kattintás, Shift-kattintás és a törlőgomb állapotának rögzítésével.

N4, N5, N6 és N8 állapota változatlanul lezárt a korábban hivatkozott felvételekkel és a #5391 javítással (46.3, 47.3).

### 48.4 Két független út és bizonyítottság

- **N1, A út:** `0x0047b020` utasításai bizonyítják a nemnulla jelző korai visszatérését; a 45.20 két producerben és a másolóban mutatja a `d4` bájt útját. **B út:** a kapuzott, memóriakorlátos teljes `.text`-pásztázás megmutatja, hogy a mezőeltolás nem egyedi szerkezeti azonosító. Ezek nem adnak `d4`-jelentést vagy névkapcsolatot; a kért eredeti viselkedés nyitott.
- **N3, A út:** a `0x100057c0` callback dinamikus `+0x40` hívása és a lebegőpontos maximum kimenet. **B út:** a `0x101c867c` vtable-adat és a `0x10021ad0` utasításai. Ezek egyeznek abban, hogy a `vfr_VdeFaceFinder` slotcélját nem lehet a callback céljaként igazolni; a tényleges osztály/cél nyitott.
- **N7, A út:** a `contactmgr.fen` listadefiníciója. **B út:** a konstruktor, az eseménykezelő és a törlési út bináris olvasata. Ezek egyeznek az egy aktuális index kezelésében, de a kijelölési mód nem következik belőlük.

**Összesített bizonyítottsági fok: nyitott.** N1, N3 és N7 eredeti termékviselkedése nincs lezárva, ezért eltérés vagy fejlesztendő viselkedés nem bizonyított. A `picasapy-research` zárás előtti Opus-ügynökös, friss kontextusú újralevezetése ebben a helyi eszközkészletben nem volt elérhető; emiatt e kör egyetlen új állítása sem kap `megerősített` minősítést.

### 48.5 A jegy „Kész, ha” pontjai és következő lépés

| Jegypont | Állapot | Bizonyíték / szükséges felvétel |
|---|---|---|
| N1: névvel rendelkező fotón új, ismeretlen arc | ⛔ Nyitott | a jelzőmásolat útja ismert (`0x004985e0`); a `d4` jelentése, névkapcsolat és a második arc ajánlása NINCS MEG; ugyanazon kétarcú fotó név előtti/utáni eredeti felvétele kell |
| N3: eredeti felismerési arány, küszöb és bemeneti méret | ⛔ Nyitott | `0x100057c0` pontszám-út megvan; eredeti küszöb/méret NINCS MEG; páros mérés kell rögzített, címkézett képkészleten |
| N4: keret és név alapértelmezett láthatósága | ✅ Lezárt | mérés (`job-187`) |
| N5: személyszintű mellőzés | ✅ Lezárt | mérés (`job-222..226`): csak arcszintű mellőzés |
| N6: személy törlése és arcokra gyakorolt hatása | ✅ Lezárt | mérés (`job-222/224`), javítás (#5391) |
| N7: People Manager kijelölési modellje | ⛔ Nyitott | `contactmgr.fen` és bináris kezelőút megvan; két személyes Ctrl/Shift-felvétel kell |
| N8: referencia-képernyőkép | ✅ Lezárt | mérés (`job-186`, 24. kép) |

**Javasolt jegytörzs-bővítés:** „A spec 48. szakasza rögzíti a helyi utánkövetést. N4/N5/N6/N8 lezárt; N1/N3/N7 nyitott. A `0x0047b020` jelzőkapuja nem bizonyítja a név szerinti kizárást. A `vfr_VdeFaceFinder` `+0x40` célja `0x10021ad0`, ezért nem azonosítható a `0x100057c0` pontszámoló callbackjával. Eltérés a PicasaPyhoz képest nem bizonyított; megvalósítási jegy nem indokolt. A lezáráshoz N1 kétarcú név előtti/utáni felvétel, N3 azonos címkézett képkészleten mért pár, N7 két személyes Ctrl/Shift-felvétel kell.”

**Fejlesztői lista:** nincs bizonyított eltérés, ezért nincs `Eredeti / nálunk / teendő` implementációs lista. **Új kutatási jegy:** nem javasolt, mindhárom hiányzó eredmény a #5184 része.

**Nyitott:**
- Ghidra-kör kell: 0x00484820 - a `[vtable+0xd4]` kimeneti `d4` jelentése és kapcsolata a névvel rendelkező arccal [N1 bináris alút; a futásidejű döntést nem blokkolja].
- Ghidra-kör kell: 0x100057c0 - a stack-paraméterláncból elért objektum `+0x74` mezőjén át hívott vtable `+0x40` tényleges osztálya/célja, valamint a képméret és küszöb forrása [blokkoló N3 bináris alút].
- N1: kétarcú kontrollfotó név előtti/utáni eredeti Picasa-felvétellel.
- N3: azonos címkézett képkészlet mindkét programban, az eredeti detektorküszöb és bemeneti méret azonosításával.
- N7: két személyes People Manager Ctrl/Shift-felvétel a `Delete Person` állapotával.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (új 48. szakasz); `docs/specs/00-index.md` (a 48. szakasz állapot-összefoglalója).

## 49. #5184, helyi utánkövetés: a Red-hívó státuszt ad, a `0.50` javaslati küszöb a Picasa fogyasztójában van (2026-10-23)

**Hatókör.** A 2026-10-22-i Ghidra-kimenet (`referencia/ghidra/2026-10-22-ghidra-sor-198-hivo.txt`) és a Red.dll `0x10001570`, `0x100057c0`, valamint a Picasa3.exe `0x006cde50`, `0x0048e1f0` helyi, utasításszintű olvasatának összevetése. A mérőadat-archívum fájlneveit és a benne lévő `.picasa.ini`-ket csak olvastam; adatot nem bontottam ki, `.bt`-fájlt nem hoztam létre.

### 49.1 N3: a Red közvetlen hívója nem küszöböl; a `0.50` a Picasa javaslati összevetése

- A Ghidra-kimenet `0x10001570` függvénye meghívja a `0x100057c0`-t; nem nulla visszatéréskor hibajelzőt ad, siker esetén nullát ad vissza. A Red.dll helyi Capstone-olvasata ezt ellenőrzi: a `0x100015a2` hívás után `test eax` következik, a hibás ág `0xffffffff`-et, a sikerág nullát ad vissza (`0x100015aa`-`0x100015bb`). Ebben a wrapperben nincs lebegőpontos pontszámküszöb-összehasonlítás.
- A `0x100057c0` a virtuális `+0x40` hívás float-eredményei közül a legnagyobbat írja a kimeneti float-tömbbe (`0x10005847`-`0x10005859`, `0x10005869`-`0x10005888`, `0x100058d2`-`0x100058d8`). A hívott virtuális cél osztálya továbbra sincs meg.
- A Picasa fogyasztója külön függvény: `0x0048e1f0` a `this+0x34a4` mezőt tölti a küszöb helyére (`0x0048e252`-`0x0048e25a`), a `CNevenVision` `+0x2c` slotját hívja (`0x0048e2eb`-`0x0048e2f1`), majd a Red-pontszámot ezzel hasonlítja össze (`0x0048e330`-`0x0048e349`). A külön `0x0048aab0` beállító a `FRRecommendIncludeLimit` alapértékét `50`-re állítja, és `100.0`-val osztva a `this+0x34a4` mezőbe írja; így az alapérték pontosan `0.50` (44.1, 45.3).
- A `0x006cde50` a `CNevenVision::vftable` `+0x2c` slotja: a vtable címe `0x00ca8754`, az adattábla `0x00ca8780` helyén a `0x006cde50` címet tartalmazza. A függvény a Red `+0x44` slotját hívja, majd a státuszt logikai eredménnyé alakítja (`0x006cdf03`-`0x006cdf12`); nem itt történik a `0.50`-es pontszám-összevetés.

**Következtetés N3-ra.** Az eredeti `0.50`-es Red-pontszám/javaslat-befogadási határ megerősített, de nem a Red arcdetektor confidence-küszöbe, ezért közvetlenül nem hasonlítható a PicasaPy YuNet `0.9`-es score-küszöbéhez. A Red belső detektorküszöbe, tényleges képbemeneti mérete és az eredeti felismerési arány továbbra is **NINCS MEG**.

### 49.2 N1: a helyi mérőadat nem ad kétarcú, név előtti/utáni kontrollt

A `meroadat.tar` leltárában `900` JPG és `15` `.picasa.ini` szerepel. Mind a `15` INI-t tartalmi olvasással ellenőriztem: egyikben sincs `faces=`, `[Contacts2]`, `]facealbum:` vagy `ffffffffffffffff` marker. Ez a csomag nem ad névvel címkézett kontrollt; a képek arcairól vagy az eredeti Picasa találatairól nem állít semmit. A PicasaPy jelenlegi `_build_pending` útja kihagyja azt a fotót, amelynek INI-adataiban az `ini_faces_of()` legalább egy `is_identified` arcot ad (`src/picasapy/app/face_scan_controller.py:474-493`). Ez a saját viselkedés forrása, nem az eredeti viselkedés mérése.

**N1 mérlege:** az eredeti kétarcú kép név előtti és név utáni futása, a Név nélküliek lista és a `faces=` kontroll nélkül a kérdés nyitott. Az archívum nem tartalmaz ehhez mintát; az eredeti Picasa futásidejű döntését bináris mezőkapuból nem lehet megállapítani.

### 49.3 N7: a kódból továbbra sem következik a Ctrl/Shift-mód

Az eredeti `contactmgr.fen` csak egy `<list name="contacts">` elemet ír le kijelölési attribútum nélkül (10-13. sor). A kezelő a vizsgált útján egy aktuális indexet tárol (`0x007b9630`), a törlési út ezt az indexelt sort használja (`0x007ba820`); ez nem zárja ki, hogy a vezérlő külön többes kijelölést is támogasson. A PicasaPy QML egy `ListView.currentIndex`-et állít be kattintáskor (`src/picasapy/app/qml/PicasaPy/PeopleManagerDialog.qml:442-478`), de ez nem bizonyíték az eredeti modelljére. A job-186 felvétel egy kiválasztott sort mutat, többes kijelölést nem próbál.

**N7 mérlege:** két személyes eredeti felvétel kell: az első sor kijelölése, Ctrl+kattintás a második soron, Shift-kattintás a második soron, mindhárom állapotban a kijelölés és a `Delete Person` gomb rögzítésével. Az eredeti kijelölési modell **NINCS MEG**.

### 49.4 Két független út és cáfoló kísérlet

- **N3, A út:** a `0x0048aab0` beállító az alapértéket `50`-re állítja, és a `100.0` osztó után a `this+0x34a4` mezőbe írja. **B út:** a külön `0x0048e1f0` fogyasztó ugyanebből a mezőből veszi az összevetési értéket, és a `0x006cde50` Red-kimenetével hasonlítja össze. A két út egyezik: az alapérték `0.50` a hasonlósági javaslat ágáé; nem a detektor confidence-küszöbe. A `0x10001570` Ghidra-kódját a Red.dll Capstone-utasításai külön ellenőrzik, és mindkettő csak státusz-visszatérést mutat.
- **N1 és N7:** a bináris és erőforrásút csak a feldolgozási kapukat, illetve az aktuális listapozíciót mutatja; az archívum nem tartalmaz megfelelő arc-/név-mérőadatot, a helyi fájltárban nincs N1/N7 Colab-felvétel. Ezek az utak nem döntik el az eredeti futásidejű viselkedést.
- **Cáfoló kísérlet:** azt próbáltam igazolni, hogy a Ghidra-kötegben megadott közvetlen Red-hívó (`0x10001570`) végzi a pontszám-küszöb összevetését. A C-kimenet és a Capstone-utasítások szerint csak a `0x100057c0` visszatérési állapotát ellenőrzi. A cáfoló ellenőrzése ugyanazon mércével: a külön Picasa `0x0048e1f0` útban a float-pontszám és a `this+0x34a4` összevetése közvetlenül látható; az eredeti `0.50` érték forrása a külön `0x0048aab0` alapérték-beállító. A feltevés tehát csak a közvetlen Red-hívóra dőlt meg; a hasonlósági küszöb ettől még `0.50`, a detektor belső küszöbe pedig nyitott.

**Összesített bizonyítottsági fok: nyitott.** A `0.50` hasonlósági befogadási határ megerősített részlelet. N1, a Red arcdetektor belső küszöbe/bemeneti mérete/felismerési aránya és N7 eredeti kijelölési modellje nem dőlt el; eredeti futásmérés híján eltérés és fejlesztői teendő nem bizonyított.

### 49.5 A jegy „Kész, ha” pontjai

| Pont | Eredmény | Bizonyíték |
|---|---|---|
| N1: a névvel rendelkező fotón további ismeretlen arc | ⛔ Nyitott | Nincs azonos kétarcú fotón végzett eredeti előtte/utána mérés; a helyi INI-kből 0/15 ad arc- vagy névjegycímkét. |
| N3: eredeti felismerési arány, küszöb és bemeneti méret | ⛔ Nyitott | A `0.50` Red-hasonlósági befogadási határ binárisból megerősített (`0x0048aab0`, `0x0048e1f0`); a Red belső detektorküszöbe, képmérete és azonos készleten mért aránya NINCS MEG. |
| N4: keret és név alapértelmezett láthatósága | ✅ Lezárt | Mérés (`job-187`, 36.3). |
| N5: személyszintű mellőzés | ✅ Lezárt | Mérés (`job-222..226`, 37.11, 48.5). |
| N6: személy törlése és az arcokra gyakorolt hatása | ✅ Lezárt | Mérés (`job-222/224`), javítás #5391 (37.10, 48.5). |
| N7: People Manager kijelölési modellje | ⛔ Nyitott | Nincs két személyes eredeti Ctrl/Shift-felvétel; a fen és a bináris egy aktuális indexet igazol, nem a teljes kijelölési módot. |
| N8: referencia-képernyőkép | ✅ Lezárt | Mérés (`job-186`, 24. kép, 36.3). |

**Javasolt jegytörzs-bővítés:** „A spec 49. szakasza pontosítja a Red hívási utat. A `0x10001570` közvetlen hívó csak státuszt ad vissza; a `0.50` Red-hasonlósági javaslati határt a Picasa `0x0048e1f0` ága használja, ezért ez nem a YuNet `0.9` detektor-küszöbének megfelelője. N4/N5/N6/N8 lezárt. N1/N3/N7 nyitott, mert a szükséges eredeti Colab-mérések és a címkézett aránykészlet nincsenek meg. Eltérés nincs bizonyítva; megvalósítási jegy nem indokolt. Következő felvétel: N1 ugyanazon kétarcú kép név előtti/utáni állapota; N3 címkézett képkészlet mindkét programban, valamint a Red belső detektor-küszöbének és bemeneti méretének feltárása; N7 két személy Ctrl-/Shift-kijelölése és a törlőgomb állapota.”

**Fejlesztői lista:** nincs bizonyított eltérés. **Új kutatási jegy:** nem javasolt; a hiányzó felvételek a #5184 részei.

**Nyitott:**
- Ghidra-kör kell: 0x00484820: a `[vtable+0xd4]` kimeneti `d4` jelentése és kapcsolata a névvel rendelkező arccal [N1 bináris alút; a futásidejű döntést nem blokkolja].
- Ghidra-kör kell: 0x100057c0: a `[param_3+8]+0x74` objektum `vtable+0x40` callbackjének tényleges célosztálya és a visszaadott hasonlósági pontszám skálája [blokkoló N3 bináris alút].
- N1: kétarcú, név előtti/utáni eredeti Picasa-felvétel `faces=` kontrollal.
- N3: azonos címkézett képkészleten mért arány mindkét programban; Red belső detektorküszöb és bemeneti méret.
- N7: két személyes People Manager Ctrl/Shift-felvétel a `Delete Person` állapotával.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (új 49. szakasz: a `0x10001570` wrapper visszaellenőrzése, a `0.50` hasonlósági határ és N1/N3/N7 mérlegének pontosítása).

## 50. #5184, helyi bizonyíték- és mérőadat-ellenőrzés (2026-10-23)

Ez a kör a korábbi 48-49. szakasz N1/N3/N7 következtetéseit ellenőrizte újra a helyi bináris-index, a Picasa3.exe és Red.dll utasításai, a már rendelkezésre álló Ghidra-kimenet, a mérőadat-archívum, valamint a PicasaPy jelenlegi megvalósítása alapján. Az eredeti program futásidejű felvétele nem állt rendelkezésre.

### 50.1 Bizonyíték és eredmény kérdésenként

| Kérdés / állítás | Bizonyíték és forrás | Eredmény |
|---|---|---|
| N1: ad-e az eredeti további, ismeretlen arcot egy névvel rendelkező fotón? | A `0x0047b020` a munkatétel `[item+0x10]` bájtját vizsgálja (`0x0047b031`), nemnulla értéknél korán visszatér. A `0x004985e0` a forrásrekord `+0xc` dwordját a munkatétel `+0x14` helyére másolja. A flag névhez rendelése és a második arc ajánlása **NINCS MEG**. A mérőadat-archívumban **15** `.picasa.ini` egyikében sincs `faces=`, `[Contacts2]`, `]facealbum:` vagy `ffffffffffffffff` marker. | ⛔ Nyitott; ugyanazon kétarcú fotó eredeti, név előtti/utáni felvétele kell. |
| N1: mit bizonyít a PicasaPy kihagyási szabálya? | A `src/picasapy/app/face_scan_controller.py` munkasor-építője (474-495. sor) és futó munkásának kapuja (1563-1567. sor) egyaránt kihagyja azt a fotót, amelyhez már azonosított arc tartozik. Ez a PicasaPy saját viselkedését rögzíti; az eredetiét nem. | Nincs bizonyított eltérés az eredetihez képest. |
| N3: mi az eredeti pontos felismerési aránya, belső küszöbe és bemeneti mérete? | A `0x100057c0` Red.dll-függvény a virtuális `+0x40` hívások pontszámai közül a maximumot írja a kimeneti tömbbe; a közvetlen `0x10001570` hívó csak státuszt vizsgál. A callback tényleges célja, a belső detektorküszöb, a bemeneti méret és az azonos címkézett adaton mért arány **NINCS MEG**. A feladatban megadott PicasaPy-viszonyítás 960 px / 0.9 YuNet-beállítás; az eredeti megfelelői nem állapíthatók meg ebből. | ⛔ Nyitott; páros, címkézett mérés és a Red belső útjának feltárása kell. |
| N3: mire vonatkozik a bináris `0.50`? | A `0x0048aab0` beállító a `FRRecommendIncludeLimit` alapértékét 50-re teszi, majd a `0xcf3a08` helyen tárolt `100.0` értékkel osztja; a `0x0048e1f0` ugyanezt a mezőt használja a Red-pontszámmal való összevetésben. A `0x006cde50` vtable-slot a Red státuszát alakítja logikai eredménnyé. | A `0.50` pontos, binárisból származó ajánlás-befogadási határ, nem a Red belső detektorküszöbe. |
| N7: egy vagy több személy jelölhető ki a People Managerben? | A `contactmgr.fen` 10-13. sora nem deklarál kijelölési módot. A `0x007b9630` aktuális indexet tárol, a `0x007ba820` az indexelt sort használja a törléshez; ezek nem döntik el a Ctrl/Shift-működést. A helyi mérőadatban nem találtam People Manager-felvételt. | ⛔ Nyitott; két személyes kattintás/Ctrl-kattintás/Shift-kattintás felvétel kell. |
| N4/N5/N6/N8 | Korábbi, hivatkozott mérések: N4 `job-187`; N5 `job-222..226`; N6 `job-222/224` és #5391; N8 `job-186`, 24. kép. | ✅ Lezárt a 36.3, 37.10-37.11 és 48-49. szakasz szerint. |

Az archívum-leltár **900** JPG-t, **15** INI-t és **1** PNG-t mutatott. A PNG pontos mérete **358×121** pixel; képe magyar PicasaPy-exportablakot mutat **6** képpel és **1** exporthibával, így nem eredeti Picasa-felvétel, és nem használható N7 bizonyítékaként. A 15 INI markerellenőrzése nem ad személy-/arccímkét; a képek tartalmáról vagy eredeti felismerési eredményéről nem következtettem. Minden fenti darabszám és képméret forrása: `mérés (meroadat.tar leltára és a kibontott, ideiglenes fájlok tartalmi/képi vizsgálata)`.

### 50.2 Független utak és bizonyítottság

- **N3 `0.50`, A út:** a `0x0048aab0` alapérték-beállító, a `0xcf3a08` bináris double-konstans és a mezőbe írás adja a `50 / 100.0` értéket. **B út:** a külön `0x0048e1f0` fogyasztó ugyanazt a mezőt hasonlítja a Red-eredménnyel, a `0x006cde50` pedig a Red státusz-slotja. A két út egyezik abban, hogy ez az ajánlási ág határa. Ez a részállítás **megerősített**; nem zárja le N3 detektorküszöbét, méretét vagy arányát.
- **N1:** a bináris jelzőút (`0x0047b020`, `0x004985e0`) és a mérőadat-archívum tartalmi vizsgálata két külön forrástípus, de egyik sem mutatja az eredeti futásidejű ajánlást. E két út nem ad igen/nem választ.
- **N7:** a `contactmgr.fen` erőforrás és a bináris esemény-/törlési út egyezik az aktuális sor/index kezelésében, de egyik sem teszteli a Ctrl/Shift többes kijelölést.

**Összesített bizonyítottsági fok: nyitott.** A pontos `0.50` ajánlási határ részállítása megerősített; N1, N3 felismerési aránya/belső detektorküszöbe/bemeneti mérete és N7 kijelölési modellje nyitott. Eredeti termékviselkedésbeli eltérés nincs bizonyítva, így fejlesztői teendő sem következik.

### 50.3 Cáfoló kísérlet

Megpróbáltam a hiányzó arcjelölés egyik lehetséges magyarázatát alátámasztani: a `faces=` rekordban a `,0` érték talán egy névtelen arc kódja. A `0x0092c450` validáló út hiányzó/üres/értéktelen azonosítón hibával tér vissza; a `0x0049d560` csak sikeres validálás után fűzi hozzá a nyolc dwordos arcrekordot. A két külön függvény utasításait külön ellenőrizve ez a `,0`-értelmezés nem áll meg. A cáfoló ellenőrzése ugyanazzal a mércével történt; eredménye csak ezt a hamis nyomot zárja ki, N1 eredeti futásidejű válaszát nem adja meg.

N3-ra cáfoló feltevésként a `0.50` ajánlási határt és a PicasaPy `0.9` értékét próbáltam azonos jelentésű detektorküszöbnek tekinteni. A beállító és fogyasztó külön bináris útja, illetve a Red `0x10001570` státuszhívója ezt megcáfolja: a `0.50` a Picasa pontszám-alapú ajánlási ágáé. A cáfoló eredményét külön ellenőriztem a `0x0048e1f0` összehasonlítási és `0x0048aab0` beállítási útjával; a Red belső küszöbe ettől továbbra is **NINCS MEG**.

### 50.4 A jegy „Kész, ha” pontjai és következő lépés

| Jegypont | Állapot | Bizonyíték / szükséges lépés |
|---|---|---|
| N1: névvel rendelkező fotón további, ismeretlen arc | ⛔ Nyitott | A jelző kapuja ismert, jelentése nem; mérőadatban nincs kétarcú, név előtti/utáni eredeti kontroll. Készíts felvételt ugyanarról a kétarcú fotóról a név felvétele előtt és után, rögzítsd a Név nélküliek listáját és a `faces=` állapotot. |
| N3: felismerési arány és küszöb a 960 px / 0.9 YuNet-viszonyításhoz képest | ⛔ Nyitott | A bináris `0.50` ajánlási határ nem detektorküszöb. Mérj azonos, címkézett készletet mindkét programban; rögzítsd a Red tényleges bemeneti méretét és belső küszöbét is. |
| N4: keret és név alapértelmezett láthatósága | ✅ Lezárt | `mérés (job-187, 36.3)`. |
| N5: személyszintű mellőzés útja és hatása | ✅ Lezárt | `mérés (job-222..226, 37.11)`: ilyen személyszintű funkció nincs; a mellőzés arcszintű. |
| N6: személytörlés útja és hatása az arcokra | ✅ Lezárt | `mérés (job-222/224, 37.10)`; a javítás #5391-gyel kiment. |
| N7: People Manager és Név nélküliek kijelölési modellje | ⛔ Nyitott | A helyi lelet csak az aktuális sort igazolja. Rögzíts két névvel, majd első kattintás, Ctrl-kattintás és Shift-kattintás után a kijelölést és `Delete Person` állapotát; a törlést ne hagyd jóvá. |
| N8: People Manager referencia-képernyőkép | ✅ Lezárt | `mérés (job-186, 24. kép, 36.3)`. |

**Javasolt jegytörzs-bővítés:** „A spec 50. szakasza rögzíti a helyi keresztellenőrzést. A `0x0047b020`/`0x004985e0` jelzőút nem bizonyítja, hogy az eredeti kihagyja a névvel rendelkező képen maradó arcot; az archívum nem tartalmaz megfelelő kontrollt. A `0.50` a Picasa Red-pontszámú ajánlás-befogadási határa, nem a Red detektorküszöbe. N1, N3 (belső küszöb, méret, arány) és N7 nyitott; N4/N5/N6/N8 lezárt. Eredeti eltérés nincs bizonyítva, ezért fejlesztői feladat nem indokolt. Folytatás: N1 név előtti/utáni kétarcú eredeti felvétel; N3 azonos címkézett képkészlet és Red bemeneti paraméterei; N7 két személy Ctrl/Shift-kijelölésének felvétele.”

**Fejlesztői lista:** nincs bizonyított eltérés, így nincs `Eredeti / nálunk / teendő` implementációs lista. **Új kutatási jegy:** nem javasolt; a nyitott felvételek a #5184 részei.

**Nyitott:**
- Ghidra-kör kell: 0x00484820: a `[vtable+0xd4]` kimeneti `d4` jelentése és kapcsolata a névvel rendelkező arccal.
- Ghidra-kör kell: 0x100057c0: a dinamikus `vtable+0x40` callback tényleges célosztálya, a Red belső detektorküszöbe és a bemeneti képméret forrása [blokkoló].
- N1: kétarcú, név előtti/utáni eredeti Picasa-felvétel `faces=` kontrollal.
- N3: azonos címkézett képkészleten mért arány mindkét programban.
- N7: két személyes People Manager Ctrl/Shift-felvétel a `Delete Person` állapotával.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (új 50. szakasz: N1/N3/N7 helyi bizonyíték- és mérőadat-auditja, a `0.50` jelentésének megerősítése és a lezáró felvételek rögzítése).

## 51. #5184, helyi utánkövetés: a cache-segéd képadatokat olvas; N1 továbbra is nyitott (2026-10-23)

**Hatókör.** A 45.20-ban nyitva hagyott N1 `d4`-mezőútját szűkítettem a `0x0042a440` cache-segédjének vizsgálatával. Az index `functions` és `string_xrefs` tábláját kérdeztem le, majd a 652 bájtos `0x0042a570` teljes függvényt a helyi `annot_disasm.py`/Capstone úton olvastam. A `meroadat.tar` archívumból kizárólag a 15 `.picasa.ini` tagot bontottam ki ideiglenesen a `.bt` alá; képfájlt nem bontottam ki. Futó Picasa-felvétel, Colab-felvétel, kód- és tesztmódosítás nem történt.

### 51.1 N1: a cache-segéd ismert kulcsai geometriaiak, de a munkajelző jelentése nem következik

- A bináris-index a `0x0042a570` függvényméretét **652 bájtban** adja meg. A teljes utasításszintű olvasat a `0x0042a58f` körül a `width`, `0x0042a5e3` körül a `height`, `0x0042a649`-nél a `crop`, `0x0042a6b1`-nél a `rect64`/`rect64(%I64x)`, majd `0x0042a744`-nél a `rotate` kulcsot használja. A `rect64` szöveges értéket a `0x0042a6d8` `sscanf`-hívása olvassa.
- Az index `string_xrefs` rekordjai ugyanezeket a címeket rendelik a `0x0042a570` függvényhez: `width` (`0x00c80ac4`), `height` (`0x00c80acc`), `rotate` (`0x00c80ad4`), `rect64` (`0x00c81460`) és `rect64(%I64x)` (`0x00cd9554`). A `0x0042a440` dekompilált útja ezt a segédet `.picasa.ini`-objektummal hívja.
- Ez a lelet csak azt rögzíti, hogy a vizsgált cache-ágban ezek a képméret-, vágás- és forgatáskulcsok látszanak. Nem azonosítja a `0x0047b020` által vizsgált munkatétel `[item+0x10]` jelzőjének jelentését, a `d4` mező személyhez kötését vagy az új arc ajánlását. A másik előállító `vtable+0xd4` célja sem ismert. **N1 tehát nyitott**; a név előtti/utáni, azonos kétarcú fotón végzett eredeti Picasa-felvétel továbbra is a döntő mérés.
- A mérőadat-archívum célzott `.picasa.ini` vizsgálata: **15 fájl**, összesen **27 267 bájt**, `faces=`, `[Contacts2]`, `]facealbum:` vagy `ffffffffffffffff` mintára **0 találat**. Ez az archívumban nincs címkézett N1-kontrollra vonatkozó mérés; nem állít semmit az archívum JPG-inek arctartalmáról.

### 51.2 Két független út, cáfoló próba és bizonyítottság

- **A út:** az indexelt `string_xrefs` a `0x0042a570` függvényhez köti a fenti képadat-kulcsokat; a `functions` tábla a függvény pontos méretét adja.
- **B út:** a helyi Capstone-olvasat a teljes 652 bájtos függvényt végigkövetve ugyanazokat a kulcscímeket és a `rect64`-érték feldolgozását mutatja. A `0x0042a440` `.picasa.ini`-hívási környezete ettől külön ellenőrzi, hogy a segéd a cache-ágon fut.
- A két út egyezik abban, hogy a közvetlenül megfigyelt kulcsok képadat-geometriát írnak le. **A segéd kulcshasználatára vonatkozó részállítás megerősített; N1 teljes viselkedése nyitott**, mert ez nem köti össze a `d4` mezőt a névvel rendelkező arccal.
- **Cáfoló kísérlet:** azt próbáltam igazolni, hogy a `0x0042a570` közvetlenül a névvel rendelkező arcok `faces=` listáját olvassa. A teljes, indexben 652 bájtos függvényt és külön a sztring-xref rekordokat ellenőrizve csak a fenti `width`/`height`/`crop`/`rect64`/`rotate` kulcsokat találtam. Ezt a hipotézist ennél a segédnél elvetem. A cáfolatot ugyanazzal a mércével ellenőriztem; az eredmény **nem** zárja ki, hogy egy másik vtable-ág vagy későbbi feldolgozó arcadatot kezel.

### 51.3 A #5184 „Kész, ha” pontjai és következő lépés

| Jegypont | Állapot | Bizonyíték / hiányzó mérés |
|---|---|---|
| N1: névvel rendelkező fotón további ismeretlen arc | ⛔ Nyitott | A `0x0047b020` korai kapuja és a `0x0042a570` cache-kulcsai ismertek; a `d4` jelentése és az eredeti második arctalálata NINCS MEG. Azonos kétarcú fotó név előtti/utáni Picasa-felvétele kell, a Név nélküliek és a `faces=` állapot rögzítésével. |
| N3: eredeti felismerési arány, belső küszöb és bemeneti méret a 960 px / 0,9 YuNet-viszonyhoz képest | ⛔ Nyitott | A bináris `0,50` a Picasa Red-pontszámú javaslati határa (50. szakasz), nem a Red belső detektorküszöbe. A belső küszöb, bemeneti méret és azonos címkézett készleten mért arány NINCS MEG. |
| N4: keret és név alapértelmezett láthatósága | ✅ Lezárt | Mérés (`job-187`, 36.3). |
| N5: személyszintű mellőzés útja és hatása | ✅ Lezárt | Mérés (`job-222..226`, 37.11): csak arcszintű mellőzés. |
| N6: személy törlése és hatása az arcokra | ✅ Lezárt | Mérés (`job-222/224`, 37.10); a javítás #5391-gyel kiment. |
| N7: People Manager és Név nélküliek kijelölési modellje | ⛔ Részben nyitott | A Név nélküliek többes kijelölése megerősített: a job-180 Ctrl+A felvételén hat arc van kijelölve, a `0x006470d0` pedig a kijelölt elemeket járja (20.5, 36.1, 40.3). A People Manager Ctrl/Shift-modellje NINCS MEG: a `contactmgr.fen` nem ad kijelölési módot, a bináris egy aktuális indexet használ, a job-186 csak egy sort mutat; két személyes felvétel kell. |
| N8: People Manager referencia-képernyőkép | ✅ Lezárt | Mérés (`job-186`, 24. kép, 36.3). |

**Fejlesztési következmény:** nincs bizonyított eltérés a PicasaPy és az eredeti között, ezért megvalósítási jegy nem indokolt. Új kutatási jegy sem kell: N1, N3 és N7 hiányzó eredményei a #5184-ben maradnak.

**Nyitott:**
- Ghidra-kör kell: 0x0042a440: a `vtable+0xd4` célosztálya és a `d8`/`d4` kimeneti mezők jelentése, különösen a `d4` kapcsolatának tisztázása a `0x004985e0`-val másolt munkatételhez.
- Ghidra-kör kell: 0x100a3a50: a már dekompilált közvetítő hívási láncán keresztül azonosítsd, ki állítja be a `[this+0x10]` objektumot és mi az élő `+0x40` cél; kövesd tovább, hol hasonlítják az eredményt a detektor elfogadási határához (a `0x100a8240` jelöltben ez nem látható). [blokkoló]
- Ghidra-kör kell: 0x006cde50: a Red felé továbbított hat DWORD-os blokkban mely mezők adják a képméretet és a detektor képbemenetét?
- N1: azonos kétarcú fotó eredeti Picasa-felvétele a személy megnevezése előtt és után.
- N3: azonos címkézett képkészleten mindkét program mért aránya, valamint a Red tényleges mérete és küszöbe.
- N7: két személyes People Manager felvétel, a Ctrl/Shift-kijelölés és a `Delete Person` állapotának rögzítésével.

**A jelen kutatási kör módosításai:** `docs/specs/picasa-arcfelismeres.md` (az 51.3 N7-státusz pontosítása, új 51.4-51.5 leletek és a megmaradt kérdések); `docs/specs/00-index.md` (az 51.4-51.5 és N7 részállapotának összefoglalása).

### 51.4 N1: a `0x004985e0` rekordmásoló hívói nem azonosítják a `d4` jelentését

**Hatókör.** A bináris-index `functions` és `xrefs` táblájából ellenőriztem a `0x004985e0` méretét és közvetlen hívóit, majd a másolót és mindhárom indexelt hívóhelyet a helyi, célzott Capstone-olvasattal vetettem össze. A mérőarchívumból csak a 15 `.picasa.ini` tagot bontottam ki a `.bt/5184-codex/ini/` könyvtárba; JPG-t és képernyőképet nem bontottam ki.

- Az index a `0x004985e0` függvényt **36 bájtosként** tartja nyilván. Az utasításai a kimenet `+0x0` és `+0x4` dwordját nullázva, a bemenet `+0x0`, `+0x4`, `+0x8`, `+0xc` dwordját a kimenet `+0x8`, `+0xc`, `+0x10`, `+0x14` helyére másolják, majd a kimenet `+0x18` dwordját nullázzák (`0x004985e0`-`0x00498603`). A rutin nem értelmezi és nem teszteli a másolt `+0xc` értéket.
- Az index **három közvetlen hívóhelyet** ad; a célzott diszasszemblálás mindhárom `call 0x004985e0` utasítást visszaigazolja:

| Hívóhely | Hívófüggvény | Helyi támpont | Mit bizonyít |
|---|---|---|---|
| `0x0042884d` | `0x00425f60` | A függvény sztring-xrefjei között `geoview`, `moviestart`, `avgcolor`, `DigicamPictureThreshold` és `DigicamPictureThreshold2` is van. | A másoló ebben a hívóban általánosabb képadat-út része; ez a kontextus önmagában nem nevezi meg a `d4` mezőt. |
| `0x0045b8e8` | `0x0045a9d0` | A függvény a `.picasa.ini` sztringre hivatkozik; a másolt rekordot a `0x0049d560` kapja meg. | Az INI-olvasási útból érkező hívás megvan, de a rekord utolsó dwordjának szemantikája itt sem derül ki. |
| `0x00484a57` | `0x00484820` | A függvény sztring-xrefjei között `.picasa.ini`, `faces` és `FRWriteFaceDataINI` szerepel; a megelőző `0x00484a0c`-`0x00484a2f` virtuális `+0xd4` hívásból veszi a `d8`/`d4` kimeneteket. | A `faces`-írási kontextus igazolja, hogy ugyanaz a másoló arcadatos útban is szerepel; nem fejti meg, mit jelent a virtuális hívás `d4` kimenete. |

**Két független út.** **A út:** az SQLite-index mindhárom hívót a `0x004985e0`-hoz köti, a `0x00484820` string-xrefjei pedig az INI- és `faces`-írási kontextust jelzik. **B út:** a három hívó célzott utasításolvasatában külön-külön látható a `call 0x004985e0`, a rutin saját utasításai pedig a fenti négy dword másolását mutatják. A két út egyezik a hívási térképben és a másoló adatmozgató szerepében. A `d4` jelentésére nézve egyik sem döntő.

**Cáfoló kísérlet.** Azt próbáltam igazolni, hogy a `d4` egyszerűen az arcok száma, mert az egyik hívó a `faces`-írás útján van. A hipotézishez a másoló testében vagy a többi hívóban arc-darabszámot dekódoló műveletet kerestem. A `0x004985e0` csak dwordokat másol, és ugyanezt a másolót a `.picasa.ini`-olvasó, valamint a másik képadat-hívó is használja; ezért a darabszám-értelmezés **nem igazolt**. A cáfoló ellenőrzése ugyanazon index- és utasításszintű mércével történt. Ez nem zárja ki, hogy a `d4` egy másik, dinamikusan hívott függvényben kap jelentést.

**Mérőadat-ellenőrzés.** A korábban relevánsnak tekintett archívumtagokat újra kibontva **15** `.picasa.ini` összesen **27 267 bájt**; `faces=`, `[Contacts2]`, `]facealbum:` és `ffffffffffffffff` mintára **0** találat volt. Ez nem ad N1-hez címkézett kontrollt, és az archívum JPG-inek arctartalmáról nem következtettem.

**Eredmény N1-re.** Az `[item+0x10]` korai kapuja és a `d4` másolási útja dokumentált, de a `d4` jelentése és a névhez rendelt archoz való viszonya **NINCS MEG**. A már megnevezett képen felajánlott második arcot továbbra is csak ugyanazon kétarcú fotó név előtti/utáni eredeti Picasa-felvétele dönti el. N1 nyitott; eredeti/PicasaPy-eltérés és fejlesztői teendő nem bizonyított.

### 51.5 N3: a Red.dll köztes virtuális ugrása ellenőrizhető, a végső cél nem

**Helyi, célzott ellenőrzés.** A helyi Red.dll RTTI-vtáblájának `vfr_SdkRelator` `+0x40` bejegyzése a `0x101c65ac` címen a `0x100a3a50` címet tartalmazza. A függvény 10 bájtja (`0x100a3a50`-`0x100a3a59`) ezt a közvetett utat valósítja meg:

```asm
0x100a3a50  mov ecx, [ecx+0x10]
0x100a3a53  mov eax, [ecx]
0x100a3a55  mov eax, [eax+0x40]
0x100a3a58  jmp eax
```

A külön `vfr_FusedRelator` `+0x40` vtable-bejegyzése (`0x101c7254`) a `0x100a8240` címre mutat. Ez a helyi, nyers vtable-olvasat és a `0x100a3a50` utasításai együtt igazolják, hogy a `vfr_SdkRelator` átirányít a `[this+0x10]` objektum saját `+0x40` slotjára. **Nem igazolják**, hogy ez a dinamikus objektum `vfr_FusedRelator`, és nem mutatnak küszöb-összehasonlítást. A 35.14-ben rögzített RTTI- és szignatúra-út a `vfr_FusedRelator::sim` `0x100a8240` jelöltet azonosítja, de a futásidejű objektumhoz kötést nem.

**Meglévő Ghidra-kimenet.** A helyi `2026-10-23-ghidra-sor-265-red.txt` és `2026-10-23-sor-271-red.txt` azonos C-kifejezést rögzíti a `[param_1+0x10]` objektum `+0x40` slotjára történő dinamikus hívásról. Mindkét kimenet figyelmeztet, hogy a Ghidra nem állította helyre az ugrótáblát, és a közvetett ugrást hívásként kezelte. Ez kiegészítő egyezés a pointer-láncra; a két azonos jelentés nem két külön bizonyítási út, és az ugrás tényére a nyers utasítás (`jmp eax`) az irányadó.

**A `0x100a8240` jelölt célzott utasításolvasata.** A szignatúra-xref által `vfr_FusedRelator::sim`-ként azonosított belépési pontban a `0x100a8353`-`0x100a8364` és `0x100a83f2`-`0x100a8403` blokkok ismét `vtable+0x40` virtuális műveletet hívnak; a visszakapott float-értékeket a rutin eltárolja, illetve súlyozottan összesíti (`0x100a8366`-`0x100a839f`, `0x100a8427`-`0x100a847b`). A vizsgált kód a hosszakat hasonlítja, és float-értéket nullához viszonyít (`0x100a842d`); elfogadási ponthatár összehasonlítása **nem látható ebben a rutinban**. Ez nem zárja ki a hívóban vagy a dinamikus `+0x40` célban végzett küszöbölést, és nem kapcsolja a jelöltet a `vfr_SdkRelator` beágyazott példányához.

**Két független út.** **A út:** a Red.dll RTTI-adat és a korábban azonosított szignatúra-xref a `vfr_SdkRelator`/`vfr_FusedRelator` osztályneveket, valamint a `0x100a8240` `sim` jellegű jelöltjét adja (35.14). **B út:** a Red.dll nyers vtable-dwordjai (`0x101c65ac`, `0x101c7254`) és a frissen célzottan dekódolt `0x100a3a50` bájtok megmutatják az átirányítás pontos utasításait. A két út egyezik a dinamikus második lépcsőben; egyik sem bizonyítja a `[this+0x10]` példány típusát vagy a végső elfogadási küszöböt.

**Cáfoló kísérlet.** Azt próbáltam alátámasztani, hogy a dinamikus második cél biztosan `vfr_FusedRelator::sim` (`0x100a8240`). A `vfr_SdkRelator` slot közvetlen célja azonban a `0x100a3a50`, amely a `[this+0x10]` objektum slotját futásidőben olvassa, majd oda ugrik. A `vfr_FusedRelator` külön vtable-bejegyzése megadja a jelölt címét, de nem köti hozzá ezt a beágyazott objektumot; a hipotézis ezért nem igazolt. A cáfoló ellenőrzése ugyanazzal a mércével történt a nyers vtable-adatokon és a célfüggvény utasításain.

**N3 mérlege.** A PicasaPy YuNet-alapértéke a forrásban `0.9` (`src/picasapy/faces/detector.py:42`), a korlátozott detektálási méret `960` képpont (`:49`). Az eredeti Picasa `0.50` értéke a `FRRecommendIncludeLimit` javaslat-befogadási határa, nem bizonyított Red-detektorküszöb (49.1). A `0x100a8240` jelölt rutinban nincs látható végső elfogadási határ, így a keresést a dinamikus célra és a hívókra kell továbbvinni. **NINCS MEG:** a Red belső detektorküszöbe, a tényleges bemeneti képmérete és azonos címkézett képkészleten mért felismerési aránya. Az eredeti bináris címkéje a `0.50` javaslati határ; a YuNet `0.9`-cel való score-összehasonlítás ebből nem következik. A felismerési arányhoz mindkét program azonos, címkézett képkészletén végzett pontos mérés kell.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (51.4: az N1 rekordmásolójának három hívója; 51.5: a Red.dll dinamikus `+0x40` ugrásának helyi visszaellenőrzése; az 51.3 N7 mérlege külön rögzíti a Név nélküliek és a People Manager állapotát); `docs/specs/00-index.md` (az 51.4-51.5 lelet és az N7 részállapot összefoglalása).

### 51.6 N3: a `vfr_VdeFaceFinder` névvel ellátott érzékenység-beállítást továbbít, de a pontküszöb nyitott (2026-10-23)

**Célzott Red.dll-ellenőrzés.** A Red.dll bináris-indexének `rtti` és `string_xrefs` tábláiból, majd a DLL nyers vtable-adataiból ellenőriztem a `vfr_VdeFaceFinder` beállító ágát; a `0x100b07b0` és `0x100af210` függvényeket a teljes, indexelt függvényméretükben, célzott Capstone-diszasszemblálással olvastam. A Picasa futtatása és arányteszt nem történt.

- A Red.dll RTTI `vfr_VdeFaceFinder::vftable` bejegyzése (`0x101c867c`) a `+0x5c` slotban (`0x101c86d8`) a `0x100b07b0` címet tartalmazza. Az index `string_xrefs` táblája a `0x101c8664` `set sensitivity` sztringet ehhez a függvényhez rendeli.
- A `0x100b07b0` kódja a `set sensitivity` ágon a kapott floatot betölti (`0x100b0b04`), a `this+0x4c` objektum vtable-jának `+0x50` függvényét hívja (`0x100b0b01`-`0x100b0b0f`), és ezt a floatot argumentumként adja át. Ez a beállítási szerződés bizonyítja, hogy van névvel jelölt érzékenység-átadási út; **nem** bizonyítja, hogy az érték az arc-jelöltek elfogadási küszöbe.
- A `vde_Detector::vftable` nyers bejegyzése (`0x101ce0cc + 0x50`) a `0x10021af0` címet tartalmazza. A függvény bájtjai `32 c0 c2 04 00` (`xor al,al; ret 4`), tehát ez a bázis-vtáblahely hamis értéket ad vissza. A futásidejű `[this+0x4c]` gyermek pontos dinamikus osztálya és az esetleges felülírt metódus **NINCS MEG**.
- A `red.cfg` parser-ellenőrzése az első `vfr_VdeFaceFinder` objektumot a fájloffszeten `0x7` azonosította, de a parser az osztály payload-mezőit nem fejti vissza. A tényleges konfigurált érzékenységi érték és annak pontszámhoz való leképezése **NINCS MEG**.

**Ghidra-kimenet (2026-10-23).** A `2026-10-23-sor-276-red.txt` dekompilációja a `0x100af210` `inProcess` függvényben ellenőrzi, hogy a `this+0x4c` gyermek `vde_Detector` típusú-e, majd ezen a gyermek-vtáblán `+0x4c` műveletet hív. Ez egy második úton is ellenőrzi a gyermek feldolgozási útját, de nem azonosítja annak konkrét futásidejű osztályát, nem követi a `set sensitivity` ágon átadott float olvasó mezőjét, és nem mutatja meg, hol hasonlítják arc-pontszámhoz. A függvénytörzsben nem látható ilyen összevetés; ebből nem következik, hogy másik függvényben sincs.

**Két független út.** **A út:** a Red.dll indexének RTTI- és sztring-xref rekordjai, valamint az önálló nyers vtable-dword egyezően a `vfr_VdeFaceFinder` `set sensitivity` beállító függvényére mutatnak (`0x101c867c`, `0x101c8664`, `0x101c86d8`). **B út:** a `0x100b07b0` célzott utasításolvasata közvetlenül mutatja, hogy a megnevezett ág floatot továbbít a gyermek `+0x50` virtuális slotjára. A két út egyezik a beállítóút létezésében; egyik sem azonosít elfogadási küszöböt vagy pontszám-skálát. A teljes N3 ezért **nyitott**, a részállítás: hogy a beállítóút létezik: **megerősített**.

**Cáfoló kísérlet.** Azt próbáltam ellenőrizni, hogy a `0x100af210` `inProcess` függvényben megjelenő `0.0001` a felismerési pontszám küszöbe-e. A függvény a `0x100af4bc` környezetében `π` és `180.0` segítségével szögértékeket alakít, majd a kiszámolt abszolút eltérést hasonlítja a `0x101e94c0` double konstanshoz (`0.0001`, `0x100af585`). Ez a helyi, utasításszintű adatfolyam szög-eltéréshez köti a konstansot, nem az arcfelismerési pontszámhoz; a küszöb-hipotézist **nem támasztotta alá**. A cáfolót ugyanazon nyers konstans- és utasításolvasattal ellenőriztem. Ez nem bizonyítja, hogy máshol nincs pontküszöb.

### 51.7 A #5184 „Kész, ha” pontjai és a nyitott munkák

| Pont | Eredmény | Bizonyíték és forrás |
|---|---|---|
| N1: névvel rendelkező fotón további, ismeretlen arc | ⛔ Nyitott | Az `[item+0x10]` kapu és a `0x004985e0` rekordmásolási út dokumentált (51.4), de a jelző írója és a névvel jelölt archoz való kapcsolata **NINCS MEG**. A `.picasa.ini` mérőadat 15 fájljában nincs címkézett kontroll (`mérés: 15 fájl, 27 267 bájt, 0 arc/jelölés-minta`); ugyanazon kétarcú képről, név előtt és után kell eredeti felvétel. |
| N3: eredeti felismerési arány és küszöb a YuNet 960 px / 0,9 viszonyában | ⛔ Nyitott | A Red.dll `set sensitivity` float-átadási út binárisan azonosított (51.6), de az effektív érték, annak küszöb-jelentése, a bemeneti méret és az egyező címkézett adaton mért arány **NINCS MEG**. A `0.50` a `FRRecommendIncludeLimit` javaslati határ, nem a Red detektorküszöbe (49.1, 50.1). |
| N4: a keret és a név alapból látszik-e | ✅ Lezárt | Eredeti felvétel `job-187`: a megnevezett arcon alapból sem keret, sem név nem látszott (36.3). |
| N5: személyszintű mellőzés útja és hatása | ✅ Lezárt | Eredeti felvétel `job-222..226`: ilyen személyszintű funkció nincs a személyalbumban vagy a People Managerben; a mellőzés arcszintű (37.11, 48.5). |
| N6: személy törlése és hatása az arcokra | ✅ Lezárt | Eredeti felvétel `job-222/224`: a „Delete People Album” eltávolítja a `faces=` sorokat, megtartja `[Contacts2]`, a megerősítésben Cancel az alapértelmezett; javítás #5391 (37.10). |
| N7: People Manager és Név nélküliek kijelölési modellje | ⛔ Részben nyitott | A Név nélküliek Ctrl+A többes kijelölése felvétellel igazolt (`job-180`; 20.5, 36.1, 40.3). A People Manager egy kijelölt sort mutató `job-186` képe és az egy aktuális sort tároló bináris út nem dönti el a Ctrl/Shift többes kijelölést; két személyes felvétel kell (51.3, 51.5). |
| N8: referencia-képernyőkép a People Managerről | ✅ Lezárt | Eredeti felvétel `job-186`, 24. kép: 631×351-es People ablak egy kiválasztott „Teszt Elek” személlyel és a leírt mezőkkel (36.3). |

**Nyitott és szükséges következő lépések.** N1-hez a fenti kétarcú név előtti/utáni eredeti felvétel kell; N3-hoz ugyanazon címkézett képkészlet mérése mindkét programban, továbbá a Red konfigurált értékének és tényleges képméretének azonosítása; N7-hez két személyes People Manager felvétel kell első kattintás, Ctrl-kattintás és Shift-kattintás után. A meglévő `0x0047b020` Ghidra-kimenet csak olvassa az `in_EAX+0x10` jelzőt, a jelző írójára vonatkozó kérés már szerepel a 43.1-ben; a Red `0x10001570` kimenet pedig státuszt ellenőriz. A korábban kért Red-dekompiláció megérkezett, de a `0x100af210` kimenete nem nevezi meg a dinamikus gyermekosztályt, és nem követi a setter floatját. A külön, pontosított kérdés:

- `Ghidra-kör kell: 0x100af210: azonosítsa a this+0x4c vde_Detector gyermek konkrét futásidejű implementációját, és kövesse a 0x100b07b0 set sensitivity ágának +0x50 virtuális hívásán átadott floatot addig a mezőig vagy függvényig, ahol kiderül, arc-pontszám elfogadási küszöbe-e. A meglévő 2026-10-23 C-kimenet a gyermek +0x4c feldolgozóhívását mutatja, de a konkrét osztályt és a +0x50 érték fogyasztását nem. [blokkoló]`

**Fejlesztési következmény.** Eredeti/PicasaPy eltérés nincs bizonyítva, ezért megvalósítási jegy és `Eredeti / nálunk / teendő` kódlista nem indokolt. Új kutatási jegy sem szükséges: N1, N3 és N7 a #5184-en belüli, konkrét felvétellel eldönthető nyitott pontok.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (51.6: a Red.dll `set sensitivity` út és a 2026-10-23-i Ghidra-keresztellenőrzés; 51.7: a #5184 pontonkénti lezárási állapota, pontosított Ghidra-kérés és konkrét felvételek); `docs/specs/00-index.md` (a friss N3-lelet és N1/N3/N7 nyitott állapota).

### 51.8 #5185 Red.dll: a `StdClusterRelator` `+0x40` céljelöltjének ellenőrzése (2026-10-23)

**A vtáblák határa.** A Red-index `data_symbols` sora a `vfr_StdClusterRelator::vftable` táblát a `0x101c60ec` címen `pointer[14]` / 56 bájtként tartja nyilván; a hozzá tartozó RTTI-adat 14 célcímet sorol, az utolsó (`0x101c6120`) `0x100a1f20`. A nyers Red.dll ugyanezt adja: a 14. dword `0x100a1f20`, tehát a főtábla legutolsó bejegyzése a `+0x34` slot, `+0x40` slot nincs benne. A külön `vfr_StdClusterRelator` résztábla (`0x101c6128`) egyetlen dword (`0x100a1ed0`), így abban sincs `+0x40` bejegyzés. Ezzel szemben a `vfr_SdkRelator` főtábla (`0x101c656c`, `pointer[23]`) `+0x40` slotja `0x100a3a50`, a `vfr_FusedRelator` főtábláé (`0x101c7214`, `pointer[23]`) `0x100a8240`. A `0x100a3a50` utasításai a `[this+0x10]` objektum `+0x40` slotjára ugranak (51.5).

**A konfiguráció korlátja.** A golden kapun átment `esm_parse.py` a `red.cfg`-ben külön rekordként azonosítja a `vfr_SdkRelator`-t (`0x22b08a` fájloffset), a `vfr_SowGrowStampClusterer`-t (`0x22d07e`) és a `vfr_StdClusterRelator`-t (`0x22d0a3`). Az eszköz README-je és kódja szerint a parser csak az `ebs_ObjectRef`/`ObjectFRef`/`ObjectArr`/`ObjectList` payloadjait értelmezi; a többi osztály payloadja átlátszatlan. Ezért az osztályrekordok jelenléte és sorrendje nem bizonyítja, hogy a `StdClusterRelator` vagy a `FusedRelator` a `SdkRelator` `[this+0x10]` objektuma. A `red.cfg` belső objektumhivatkozása és a tényleges futásidejű cél **NINCS MEG**.

**Független utak.** **A út:** a Red-index `data_symbols` és `rtti` táblájának elemszámai/célcímei megadják a három főtábla slotjait. **B út:** a Red.dll nyers PE-adataiból kiolvasott dwordok ugyanazt a 14/1/23/23 elemszámot és a `0x100a3a50`/`0x100a8240` `+0x40` értékeket adják. Ettől külön, a `red.cfg` parseres leltára azonosítja a fenti három konfigurációs rekordot, de nem oldja fel azok belső kapcsolatát. Az index és a nyers DLL a slotok méretében egyezik; a parser nem tesz hozzá futásidejű objektumtípust.

**Cáfoló kísérlet.** Azt próbáltam alátámasztani, hogy a `vfr_StdClusterRelator` lehet a `0x100a3a50` közvetítőjének `+0x40` célja. A két RTTI-vel jelölt StdCluster-vtábla mérete ezt nem támasztja alá: a főtábla 14 bejegyzésig (`+0x34`), a másodlagos egy bejegyzésig tart. A számlálást a nyers PE-dwordokkal is ellenőriztem; az index és a nyers adat egyezik. Ez csak e két azonosított StdCluster-táblát zárja ki ilyen slotként, ismeretlen vagy más osztályú célt nem. A `vfr_FusedRelator` `+0x40` célja továbbra is jelölt, nem runtime-bizonyíték. A `0x100057c0`, `0x10001570` és `0x100a8240` vizsgált kódjában végső elfogadási küszöb nem látható; a tényleges második hívási cél és küszöb **NINCS MEG**.

**Bizonyítottság és következmény.** A négy vtábla elemszáma és a megnevezett slotértékek **megerősítettek** (Red-index + nyers PE). A StdCluster-jelölt kizárása csak a két azonosított StdCluster-vtáblára érvényes, az objektumkapcsolat feltáratlan. Ez a pontosítás nem zárja le a #5185 8. pontját: a Red.dll végső küszöbéhez a `0x100a3a50` hívási láncának célzott Ghidra-követése, a scan-indítás/kihagyás viselkedéséhez J7, a fájlírási időzítéshez J8 kell. Igazolt PicasaPy-eltérés vagy fejlesztői teendő nincs.

### 🔁 Független újralevezetés

- **Bíráló:** `red_independent_review` (friss kontextus, a kutató magyarázata nélkül)
- **Címek:** `0x100a3a50`, `0x101c656c`, `0x101c60ec`, `0x101c7214`, `0x100a8240`
- **Eredmény:** EGYEZIK
- **A bíráló tényei:** az SDK `+0x40` slotja a `0x100a3a50` átirányítóhoz vezet; az utasítások a `[this+0x10]` objektum saját `+0x40` slotjára ugranak. A `vfr_FusedRelator` `+0x40` slotja `0x100a8240`, de csak akkor tényleges cél, ha a belső objektum ezt a táblát használja. A StdClusterRelator táblái nem igazolják az SDK → StdCluster → Fused hívási sort. A vizsgált függvényekben végső elfogadási küszöb nem bizonyítható; hiányzik a runtime típus és a pontszámot felhasználó döntési hely.

## 52. #5185, a névforrások és a Red.dll-ág független helyi ellenőrzése (2026-10-23)

**Hatókör.** A `2026-10-22-ghidra-sor-197-200.txt`, `2026-10-22-ghidra-sor-198-hivo.txt` és `2026-10-22-ghidra-sor-252-red.txt` Ghidra-kimeneteket a helyi Picasa 3.9.141.259 bináris célzott Capstone-diszasszemblálásával és az index hívó-/sztring-hivatkozásaival vetettem össze. A Red.dll `0x100057c0` és `0x10001570` kódjához a meglévő Ghidra-kimenetet és a külön helyi utasításolvasatot ellenőriztem. Új Picasa/Colab futás és profilfájl-diff nem készült.

### 52.1 A 7. pont: névforrások és a `contacts.xml` mentési időpontja

- A `0x00581920` külön `contacts.xml` (`0x00c90e74`) és `backup.xml` (`0x00c90e94`) útvonalat nyit a parser számára (`0x00991650`); a sikeres `backup.xml`-helyreállítási ág meghívja a `0x00580110` XML-írót (`0x00581bcb`). A `0x00580110` `contacts` gyökeret és névjegymezőket állít elő, majd a `0x009c15a0` írósegéden át a `contacts.xml`-be ír. A címeknél látható fájlút és íróhívás megerősített; ez a helyreállítási ág önmagában nem azonosít felhasználói műveletet.
- A rendes `#contacts\` mentési út a `0x0041ba40` → `0x00586bd0` lánc. A `0x00586bd0` csak a `[edi+0x13c]` jelző beállított ágában hívja a `0x00580110`-et (`0x00586c31`-`0x00586c49`). A betöltési út külön: `0x0041ee10` → `0x00586d00` → `0x00581920`; a hívó a `+0x13d` bájtot állítja, ez nem bizonyítja a `+0x13c` írási jelzőt vagy egy People Manager-művelet időpontját.
- A `0x0066f2b0` külön másolási út: egyetlen indexelt közvetlen hívója a `0x0066f470`, amelynek hivatkozásai a Burn/Backup felülethez tartoznak. Ez nem bizonyíték a szokásos névjegy-mentés indítására.
- **NINCS MEG:** hogy névadás, People Manager OK/Cancel, javaslat elfogadása, törlés, alkalmazásbezárás vagy újraindítás pontosan mikor módosítja a `contacts.xml`-t, a `.picasa.ini`-t és a db3-at. A bináris hívási út nem helyettesíti a fájlrendszeri előtte/utána mérést; J8 szükséges.

### 52.2 A 8. pont: Red.dll pontszámút és a végső küszöb

- A Red.dll `0x100057c0` a bemeneti leírók és minták `vtable+0x40` hasonlósági értékei közül a legnagyobbat írja az eredménytömbbe. A `0x10001570` ennek a rutinnak a visszatérési státuszát ellenőrzi, nem a float-pontszámot. E két függvényben végső pontküszöb-összevetés nem látható.
- A `0x100a3a50` közvetítő a `[this+0x10]` objektum dinamikus `+0x40` slotjára ugrik. A slot tényleges célosztálya és a pontszám elfogadásának helye továbbra sincs feloldva; a `vfr_FusedRelator::sim` (`0x100a8240`) csak jelölt (51.5, 51.8). A Picasa EXE `FRRecommendIncludeLimit=0,50` összevetése (`0x0048e1f0`, `0x0048e33e`) külön, utólagos ajánlásba-vételi szűrő; nem a Red.dll detektorküszöbének bizonyítéka.
- A Red.dll `vfr_VdeFaceFinder` `set sensitivity` ága (`0x100b07b0`, a felirat xrefje `0x101c8664`) a kapott floatot a `this+0x4c` gyermek `+0x50` virtuális slotjának adja át (`0x100b0b01`-`0x100b0b0f`); a dinamikus cél és a float pontszámra gyakorolt hatása **NINCS MEG**. A `vfr_VdeFaceFinder::inProcess()` (`0x100af210`; Ghidra: `2026-10-23-sor-276-red.txt`) a gyermek detektor `+0x40` műveletét futtatja, és a `0x101e9400` π, illetve a `0x101e97f8` 180.0 konstansból számolt szögeltérést hasonlítja a `0x101e94c0` double értékhez (`0x100af4bc`-`0x100af585`). A Red.dll nyers bájtjai ezen a címen `2d 43 1c eb e2 36 1a 3f`; little-endian IEEE-754 binary64-ként `0x1.a36e2eb1c432dp-14` (rövid, oda-vissza kerekíthető alakja `0.0001`). Ez ebben a függvényben szögeltéréshez, nem arc-pontszámhoz tartozik. Ez a helyi függvényt vizsgálja, és nem zárja ki, hogy másik dinamikus cél vagy hívó pontküszöböt alkalmaz.
- **NINCS MEG:** a Red.dll végső felismerési küszöbe, a tényleges bemeneti képméret, valamint a felismerés indítási és kihagyási feltétele. A küszöb eldöntéséhez a dinamikus callback és pontszámfogyasztó döntési ágának célzott feltárása, az indításhoz/kihagyáshoz J7, az arányhoz azonos címkézett képkészleten végzett pontos mérés kell. Becsült szám nem adható át.
- **Ghidra-kör kell:** `0x100a3a50`: a meglévő 2026-10-23-i kimenet csak a `[this+0x10]` objektum dinamikus `+0x40` ugrását mutatja; a konfigurációs/építő útból azonosítsd az objektum tényleges vtable-jét és a pontszám elfogadását végző összevetést. A meglévő kimenet ezt a két új kérdést nem válaszolja meg. **[blokkoló]**

### 52.3 Független utak, cáfoló próba és bizonyítottság

- **A út:** a Ghidra C-kimenet (`0x00581920`, `0x00580110`, `0x100057c0`, `0x10001570`, `0x100af210`) megmutatja a fájlágakat, az XML-írót, a státusz-/pontszámkezelést, valamint azt, hogy a `0x101e94c0` érték az `inProcess()` szögeltérés-ágában szerepel.
- **B út:** a helyi, célzott Capstone-olvasat végigköveti a hívásokat és feltételeket; az indexelt hívó- és sztring-xrefek külön a `#contacts\` útvonalhoz kötik a `0x0041ba40`-et, valamint a `0x0066f2b0`-t a `0x0066f470` Backup-hívójához. A Red.dll nyers utasításai egyeznek a Ghidra-változattal: a `0x100057c0` pontszámot ír, a wrapper státuszt vizsgál; a PE-ben kiolvasott double bájtjai és a `0x100af585` `fcomp qword ptr [0x101e94c0]` utasítás függetlenül igazolja a szögeltérés-összevetést. A `0x100b07b0` célzott utasításolvasata külön igazolja, hogy a `set sensitivity` ág csak továbbítja a floatot a gyermek virtuális `+0x50` slotjára. A dokumentált részállítások így **megerősítettek**; az eredeti futási időzítés és a detektor elfogadási küszöbe **nyitott**.
- **Cáfoló kísérlet:** azt próbáltam igazolni, hogy a `0x0066f2b0` a People Manager rendes profilírója, mivel `contacts.xml`-t használ. A függvény forrásként a `contacts.xml`-t és célként a `backup.xml`-t adja át a másoló műveletnek; a hívója `0x0066f470`, a hívási környezet Backup/Burn-panel erőforrásokra mutat. A Ghidra-törzs és az ettől külön ellenőrzött hívó-/sztring-xref ugyanazt mutatja, ezért ezt a besorolást elvetem. Külön ellenőriztem azt a küszöbfeltevést is, hogy a `0x100057c0` vagy a `0x10001570` végezné a végső összevetést: a `0x100057c0` float-összevetése (`0x1000586c`) csak az aktuális legjobb jelöltet választja, a `0x10001570` pedig státuszt tesztel. A lehetséges `0.0001` küszöbjelöltet is megpróbáltam a felismerési küszöbbel azonosítani; a `0x100af210` π/180-alapú szögszámítása, abszolútérték-képzése és `0x100af585` összevetése ezt a feltevést cáfolja az adott függvényre nézve. Egyik vizsgált törzsben sincs igazolt végső felismerési küszöb. Ezek a függvényekre korlátozott eredmények, nem zárják ki a dinamikus callbackben vagy más pontszámfogyasztóban lévő küszöböt.

### 52.4 Független újralevezetés

- **Bíráló:** `independent_binary_review`, friss kontextussal, a következtetés előzetes közlése nélkül.
- **Ellenőrzés:** eredeti Picasa3.exe és Red.dll hash-e az index `meta.json` értékével egyezik; célzottan vizsgálta a `0x00580110`, `0x00581920`, `0x0041ba40`, `0x00586bd0`, `0x100057c0` és `0x10001570` címeket, teljes `.text`-pásztázás nélkül.
- **Eredmény:** a `contacts.xml` íróút, a piszkos jelző ága, a betöltési lánc és a Red wrapper/core szerepe **egyezik**. A bíráló jelezte, hogy a `0x100057c0` tartalmaz float-összevetést (`0x1000586c`); ez a legjobb jelölt frissítése, nem fix küszöb. A 52.3 cáfoló próbáját ennek megfelelően pontosítottam. A bíráló a `0x0066f2b0` másolási irányát önállóan nem állapította meg; a forrás/cél állítás a 35.10-ben hivatkozott korábbi Ghidra-törzsből származik.

**A #5185 „Kész, ha” állapota.** Az 1-6. pont továbbra is részleges a 35.3 táblázat nyitott felvételei szerint. A 7. pontban a bináris olvasó/író út és a külön Backup-másoló út dokumentált, de a műveletenkénti lemezre írás és a `.picasa.ini`/db3 diff nyitott (J8). A 8. pontban a pontszámgyűjtő és a wrapper szerepe dokumentált, de a Red.dll végső küszöbe, bemeneti mérete, scan-indítása és kihagyása nyitott (J7, célzott nyomkövetés a binárisban). Így mind a nyolc ponthoz van leírt eredmény vagy konkrét nyitott megszerzési út, de a teljes „Kész, ha” feltétel **nem teljesült**; bizonyított PicasaPy-eltérés és fejlesztői teendő nincs.

### 52.5 Red.dll-pontszám: a helyi komponens verzióazonosságának határa

**Bináris-azonosság.** A megadott `Picasa3.exe` fájlverziója `3.9.141.259`; a mellette levő `plugins/Red.dll` SHA-256-a `da370693b59d89e7d48646d9617f5f595e371f8e1828cb1aa9f12530a17c8233`, ami egyezik a Red-index `meta.json` értékével. Az index átadási riportja ugyanakkor a DLL forrását Picasa 3.7 telepítésként nevezi meg; a DLL-ben nincs PE verzió-erőforrás. A helyi útvonal tehát a 3.9-es EXE mappájához köti, a forrásriport viszont 3.7-et mond. A DLL pontos párosítása a 3.9-es binárissal **NINCS MEG**; az alábbi címleletet a helyi DLL-re, nem bizonyítottan a 3.9 runtime-ra értem.

| Állítás | Forrás | Fok |
|---|---|---|
| `vqc_Relator::sim(uint32*, int32, uint32*, int32)` címe a `vqc_Relator` vtable `+0x40` slotján `0x10100a10` | bináris (helyi Red.dll: `0x101d46f4` RTTI; nyers slot `0x101d4734`; szignatúra-xref `0x101d4578`) | megerősített a hash-azonosított helyi DLL-ben; 3.9-es eredetére nézve feltételes |
| A függvény a véges eredménypontszámot 0 és 1 közé korlátozza, majd floatként adja vissza | bináris (helyi Red.dll: `0x10100bba`/`0x10100bcd`; a `0x101ac268` és `0x101e92d8` operandusok nyers értéke rendre 1.0 és 0.0; visszatérés `0x10100bde`-`0x10100be6`) | feltételes: egy utasítási vezérlésút olvassa ki ezt a korlátozást; a független index/PE út a metódust és a konstansokat azonosítja, de a vezérlési jelentést önállóan nem állítja elő |
| A helyi `red.cfg` `vfr_SdkRelator` objektumának `+0x10`-es célja a beágyazott `vqc_Relator`; ennek `+0x40` slotja a `0x10100a10` `sim` függvényre mutat | bináris (helyi DLL: `0x100a3ca0`, `0x10063ec0`, `0x100a3a50`; `red.cfg`: `0x22b08a`-`0x22b0a1`; ClassId-regiszter és RTTI) | megerősített a helyi DLL+cfg párra; a 3.9-es futásidejű példányhoz feltételes |
| Ez a `vqc_Relator::sim` pontszám kerül-e a `vsi_FaceViewDetector::runOnOneWindow` `+0x1c` küszöb-összevetésébe, vagy mi a Red végső elfogadási feltétele | **NINCS MEG**; a `0x10103870` mezőútja és a `vqc_Relator` visszahívása közötti adatkapcsolat nincs végigkövetve | nyitott |
| A helyi DLL és a Picasa 3.9 runtime közötti pontos build-azonosság; a tényleges elfogadási küszöb, bemeneti képméret, indítás és kihagyási feltétel | **NINCS MEG**; a tiszta 3.9-es csomag vagy Colab-példány DLL-jének hash-összevetése, majd J7 mérés kell | nyitott |

**Utasítási út.** A `0x10100a10`-et a `vqc_Relator` vtable `+0x40` bejegyzése és az indexelt virtuális `sim` szignatúra azonosítja. A 601 bájtos függvény `fld1`/`fldz` értékeket készít, a köztes floatot a `0x101ac268` címen lévő 1.0 double-lal hasonlítja össze (`0x10100bba`), majd a kiválasztott floatot a `0x101e92d8` címen lévő 0.0 double-lal vizsgálja (`0x10100bcd`); a negatív véges értékhez a nulla-ágat választja, és a kiválasztott floatot adja vissza. Ez a `vqc_Relator` objektum pontszámának korlátozása, nem boolean elfogadás és nem bizonyítja a teljes arcdetektor küszöbét.

**A helyi `red.cfg` hivatkozás feloldása.** A `vfr_SdkRelator::vftable` `+0x40` slotja a `0x100a3a50` átirányítóra mutat; ez a `[ecx+0x10]` objektum `+0x40` virtuális slotjára ugrik (`0x100a3a50`-`0x100a3a58`). A `vfr_SdkRelator` `+0x0c` szerializálója (`0x100a3ca0`) az első `ebs_ObjectRef` mezőt a `this+8` címen adja át a `0x10063ec0`-nak. Ez utóbbi író ágában a `cmp [ebp+8],0` és `setne al` (`0x10063eda`-`0x10063ee0`) a célmutató nem-null voltát írja ki; a nem-null cél saját `+0x0c` szerializálója is meghívódik (`0x10063ee8`-`0x10063ef5`). A wrapperben tárolt cél ezért a `vfr_SdkRelator+0x10` tag.

A `red.cfg` bájtjai ezt a konkrét objektumpárt adják: a `0x22b08a` rekord `ClassId 0x00401036` (`vfr_SdkRelator`), verziója 100; az első `ebs_ObjectRef` fejléc a `0x22b094` címen, az utána következő `01` jelenlétjelző a `0x22b09a` címen áll; a beágyazott objektum a `0x22b09b` címen `ClassId 0x00423003` (`vqc_Relator`), verziója 102. A `vqc_Relator` vtable `+0x40` slotja (`0x101d4734`) a `0x10100a10` címre mutat. Ez a feloldás a hash-azonosított helyi Red.dll és red.cfg kapcsolatára bizonyított, nem a 3.9-es futásidejű DLL azonosságára, és nem köti ezt a pontszámot a külön `vsi_FaceViewDetector` rekord `+0x1c` mezőjéhez.

**A két független út.** **A út:** a célzott Capstone-diszasszemblálás végigköveti a `vfr_SdkRelator` első `ebs_ObjectRef`-mezőjét, a 0/1 jelenlétjelzőt, a nem-null cél szerializálását és a `+0x40` virtuális átirányítást. **B út:** a `red.cfg` nyers rekordhatárai és ClassId-regisztere egymástól külön azonosítja a `vfr_SdkRelator`-t, a `01` jelzőt és az utána beágyazott `vqc_Relator` objektumot; a Ghidra `ebs_ObjectRef::read` törzse a nullás jelzőnél kihagyja, nem-null jelzőnél a `0x100685a0` nested-object betöltőt hívja (`0x10063f30`). A Red RTTI-vtábla további, külön adatútja a `vqc_Relator +0x40` slotját a `0x10100a10`-hez köti. A két út a helyi DLL+cfg objektumkapcsolatában egyezik. A DLL 3.9-es runtime-hoz kötése egyik útból sem következik; a 0-1 pontszámkorlátozás értelmezése **feltételes**, mert a második út nem vezette le újra a függvény teljes feltételes vezérlési jelentését.

**Cáfoló kísérlet.** A 0.0/1.0 összevetéseket végső elfogadási határként próbáltam értelmezni. A diszasszemblálásban a feltételes ágak a két float-érték közül választanak, majd a függvény floatot ad vissza; a nyers PE-ben a konstansok pontosan 0.0 és 1.0. Ez cáfolja, hogy ezekben az utasításokban bool döntés történne, de a pontszám-korlátozás olvasata csak feltételes marad a második vezérlési út hiánya miatt. A DLL 3.9-es runtime-hoz tartozása nincs igazolva, ezért a cáfolat sem terjed ki a teljes 3.9-es felismerőre.

**Nyitott és megszerzési út.** Szerezd meg a Red.dll-t tiszta Picasa 3.9 csomagból vagy az eredeti Colab-példányból, majd hasonlítsd a SHA-256-át a helyi `da3706…c8233` fájlhoz. Egyezés esetén a helyi címek átvihetősége külön ellenőrizhető; eltérés esetén az új DLL-t kell indexelni és a megfelelő virtuális hívás/pontszám-fogyasztó ágát célzottan vizsgálni. A korábban kért `0x101044f0` Ghidra-kör lefutott (`2026-10-26-2026-10-26-ghidra-sor-282-304-red.txt`): megadja az ablakbejáró `0x10103870` detektorhívását és a jelöltek pontszám szerinti rangsorolását. A `2026-10-26-5185-red-weak.txt` és az 54.3/c további kimenetei a classifier-array általános ObjectRef-betöltését és a `vsi_WeakClassifier` `+0x1c` adatfolyam-mezőjét írják le. Ezek **nem** azonosítják a betöltött modellstream fájlját vagy floatját, és nem kötik a detektor rekord `+0x1c` mezőjét a `vfr_SdkRelator` → `vqc_Relator::sim` eredményéhez. A korábbi Ghidra-kérés tehát végrehajtva, a mezők közti kapcsolat nyitott; ugyanarra a címre új kérést nem adok. A ténylegesen betöltött DLL/hash, modellstream és effektív érték megszerzéséhez J7 futásidejű felvétel kell, a scan-indítással, a megnevezett arcot tartalmazó fotó kihagyásával, a bemeneti mérettel és a címkézett készleten mért eredménnyel együtt.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (35.3/8. pont és 35.4 jegytörzs-kiegészítés pontosítása, 52.5: a helyi Red.dll pontszámlelete és a verzióazonosság bizonyítékhatára); `docs/specs/00-index.md` (5185-ös nyitott állapot).

## 53. #5184, helyi Codex-kör: N1/N3/N7 futásidejű döntése nyitott (2026-10-23)

**Hatókör és korlát.** A helyi eredeti Picasa 3.7 bináris, a Picasa 3.9 indexei, a Red.dll, a `red.cfg`, a hozzáférhető mérőadat-archívum és a PicasaPy forrása alapján ellenőriztem az előző körök N1/N3/N7 nyitott pontjait. Az eredeti Picasa nem futott, Colab-felvétel nem készült: a helyi felmérő `gh api ... POST .../issues` hívással ad fel feladatot, GitHub-hozzáférés pedig ebben a munkamenetben kifejezetten tiltott. A teljes `.text`-pásztázást nem ismételtem meg.

### 53.1 N1: a névvel rendelkező képen maradó másik arcra nincs futásidejű adat

- A PicasaPy saját kódja a felismerésből kihagyja azt a fotót, amelyen már van megnevezett arc (`FaceScanController._build_pending`, `src/picasapy/app/face_scan_controller.py:474-496`). Ez a mi viselkedésünket írja le, az eredeti Picasáét nem.
- A `meroadat.tar` 944 tagjából célzottan csak a 15 `.picasa.ini` tagot bontottam ki; ezek összesen **27 267 bájtosak**. A `faces=`, `[Contacts2]`, `]facealbum:` és `ffffffffffffffff` jelölésekre **0** találat volt. A képállományok arctartalmáról ebből nem következtettem.
- A korábbi Picasa-diszasszemblálás (`0x004985e0`, `0x00484820`) a rekordmásolást és a `faces`-írói kontextust mutatta. Az új, `paszta.py`-val és `memoria_kapu()`-val indított teljes `.text`-pásztázás, majd a célzott követés a `0x0047b020` `+0x10` mezőjének íróját és fogyasztását is azonosította; a mező viszont feldolgozási sort vezérel, és nincs összekötve a fotó „már van megnevezett arc” állapotával. A friss független audit az `]unknownface` xrefeket is ellenőrizte; azok sem döntik el a névadás utáni állapotot.
- **A `+0x10` mező igazolt útja.** Fogyasztó felől a `0x004987c0` a sorcsomópont `+4` adatcímét adja a `0x0047b020`-nak (`0x0049892d`-`0x00498933`); a worker a `[adat+0x10]` bájtot vizsgálja (`0x0047b031`). Nem nulla értéknél meghívja a `0x0048bd80`-at (`0x0047b037`), majd `0x000f4240` értékkel tér vissza (`0x0047b03d`). Nulla értéknél a worker a szokásos feldolgozási ágon folytatja, többek közt a `FRAddSuggesetions` beállítást használva és a `0x0048ef20` felé haladva; ez az ág is `0x000f4240` visszatéréssel végződik. A `0x004987c0` mindkét kész státuszt kezeli és felszabadítja az elemet (`0x00498938`-`0x00498944`), ezért az elem felszabadítása önmagában nem jelenti, hogy a fotót kihagyták.
- A termelő felől a `0x0049de00` 24 bájtos munkasor-csomópontot foglal, és a forrás `+0x10` bájtját a csomópont adatának `+0x10` mezőjébe másolja. Két megfigyelt készítő közül a `0x0047b9f0` egyes értéket ír a forrás `+0x10` mezőjébe (`0x0047ba82`), a `0x0047baf0` pedig nullát (`0x0047bb7a`), mielőtt a `0x0049de00`-on át sorba állítaná az elemet. A fogyasztó és a két külön készítő ugyanarra a mezőre mutat: az érték a `0x0048bd80` tisztító/vezérlő útját választja el a rendes feldolgozási ágtól; mindkettő a munkasor elemének befejezett státuszával tér vissza. Az elem fotó- vagy névstátuszát ez nem bizonyítja.
- **Cáfoló kísérlet.** Megpróbáltam a nem nulla `+0x10` értéket a „névvel ellátott fotót hagyd ki” jelzőként értelmezni. A termelő→másoló út megerősítette, hogy a bájt valóban bejut a munkasor elemébe; a fogyasztó út viszont a nem nulla értéket a `0x0048bd80` tisztító/vezérlő ágára irányítja, míg a nulla érték folytatja a szokásos feldolgozást. A két ág azonos `0x000f4240` befejezett státusza és a munkasorból való közös felszabadítása cáfolja, hogy ez a bájt önmagában a fotó elhagyását jelezné. A névvel ellátott fotóhoz való tényleges kötése ettől még nyitott.
- **Eredmény:** N1 **nyitott**, PicasaPy-eltérés nem bizonyított. Döntő mérés: ugyanaz a legalább kétarcú kép eredeti Picasában a másik arc megnevezése előtt és után; mindkét állapotban rögzítendő a Név nélküliek nézet és a képen tárolt `faces=` adat.

### 53.2 N3: a Red végső küszöbe, bemeneti mérete és mért aránya továbbra sincs meg

- A PicasaPy forrásban a YuNet alap-küszöbe **0,9**, a detektálásra korlátozott leghosszabb oldal **960 képpont** (`src/picasapy/faces/detector.py`). Ezek a mi beállításaink, nem az eredeti Red-modell értékei.
- A `0,50` eredeti, binárisból kiolvasott érték továbbra is a `FRRecommendIncludeLimit` javaslat-befogadási határa (`0x0048aab0`, `0x0048e1f0`), nem bizonyíték a Red arcdetektor küszöbére (49.1).
- A célzott Red.dll-utasításolvasás pontosítja a korábbi eredményt: a `0x100057c0` a dinamikus `vtable+0x40` hívások visszatérő floatjai közül a futó maximumot tartja meg (`0x10005859`, `0x10005869`-`0x10005878`), majd a kimeneti tömbbe írja (`0x100058d2`-`0x100058d8`). A `0x10001570` a hívás státuszkódját kezeli (`0x100015a2`, `0x100015aa`-`0x100015bb`); e két függvényben nincs végső arcelutasítási küszöb-összevetés. A virtuális `+0x40` cél belső működése továbbra sem ismert.
- A korábbi Red.dll-olvasat (`0x100a8240`, `0x100af210`, `0x100b07b0`) pontszámgyűjtést és dinamikus érzékenység-átadási utat mutatott; nem azonosította a futásidejű osztályt, a beállított értéket vagy a Red detektor tényleges elfogadási határát.
- A friss, független címellenőrzés egy további Red-ágat azonosított: a `vsi_FaceViewDetector::runOnOneWindow` VA `0x10103870`, és a `0x10103c14` körüli kód az összegzett pontszámot egy objektum `+0x1c` mezőjével hasonlítja össze. A `vsi_WeakClassifier` `threshold =` mező szerializálása a `0x10107d70` címen látható (`threshold =` szöveg: `0x101d5800`). Ezek nem adják meg a futó Picasa által használt mező értékét, a Red tényleges bemeneti WxH-ját vagy az azonos címkézett képkészleten kapott arányt. A `red.cfg`-ellenőrző jelenlegi parsere az osztály-payloadot nem fejti vissza.
- **Eredmény:** N3 **nyitott**; a felismerési arány, a tényleges Red-bemeneti méret és az effektív elfogadási érték mind **NINCS MEG**. Döntő út: azonos címkézett képkészlet rögzített futtatása mindkét programban, a Red-nek átadott tényleges képméret és betöltött modellértékek egyidejű rögzítésével.

### 53.3 N7: a People Manager többes kijelölése nem dőlt el

- A `contactmgr.fen` `contacts` listája nem ad meg kijelölési módot. A job-186 People Manager-kép egyetlen kijelölt személyt mutat; egyik tény sem bizonyít egy- vagy többes kijelölést. A PicasaPy QML egy aktuális sort kezel, de ez csak a mi oldalunk viselkedése.
- A PicasaPy forrásában a People Manager `selectedKey` állapota egyetlen kulcs (`PeopleManagerDialog.qml:21`); a lista sora a `ListView.isCurrentItem` állapotot emeli ki, kattintáskor pedig a `currentIndex` értékét és a `selectContact(modelData)` hívást állítja (`:442-478`). A Név nélküliek nézete ettől különálló, többes arc-kijelölési modellt használ: a `selectedFaceIds` térkép egyenként kapcsolható, a `selectedCount` ebből számolódik (`UnnamedFacesView.qml:41-42, 88-96`), a csempekattintás ezt hívja (`:489-491`), a „Ignore Selected” pedig a kijelölt kulcsok listáját adja át (`:365-370`). Ez a mi forráskódunkat írja le; az eredeti People Manager kijelölési módját nem dönti el.
- A Név nélküliek nézet többes kijelölése külön bizonyított (`job-180`); ez nem bizonyítja, hogy a People Manager ugyanazt a modellt használja.
- **Cáfoló kísérlet:** a `Select All` címke hivatkozásait próbáltam a People Manager többes kijelölésének statikus bizonyítékaként használni. A független audit a `0x007325a0` és `0x007348f0` hivatkozókat Publish/Collage-környezethez, a `0x007331e0` címet pedig az `Address::ID_SELECTALL` szerkesztőmenühöz kötötte. A függvénykörnyezetek visszaellenőrzése ezt az érvet megcáfolta: ezek nem People Manager-bizonyítékok.
- **Eredmény:** N7 **részben nyitott**: a Név nélküliek többes kijelölése bizonyított, a People Manager Ctrl/Shift-módja **NINCS MEG**. Döntő mérés: két személy felvétele után képernyőkép az első sor kattintása, Ctrl+kattintás és Shift+kattintás után, hogy látható legyen, megmarad-e mindkét kijelölés.

### 53.4 Független utak és bizonyítottság

- **A út:** N1-nél fogyasztó felől a `0x004987c0` → `0x0047b020` → `0x0048bd80` út, valamint a két feldolgozási ág közös `0x000f4240` kész státuszának kezelése a munkasorban lett követve; N3/N7-nél a helyi Picasa/Red index `functions`, `xrefs`, `string_xrefs`, `rtti` rekordjai, a címre szűkített Capstone-olvasatok, a `red.cfg`-feldolgozás, a `contactmgr.fen` és a PicasaPy-forrás adja az ellenőrizhető adatot.
- **B út:** N1-nél termelő felől a `0x0047b9f0`/`0x0047baf0` jelzőírásai, a `0x0049de00` mezőmásolása és a `0x004987c0`-ból meghívott worker lettek egymástól függetlenül újra levezetve; a friss kontextusú bíráló ugyanerre a vezérlő ág és a rendes feldolgozás közötti különbségre jutott. N3/N7-nél a független bíráló a `]unknownface` xrefeket, a Red `0x10103870`/`0x10107d70` útját, a People Manager menühivatkozását és a félrevezető `Select All` hivatkozásokat ellenőrizte.
- **Egyezés:** az N1 két útja ugyanazt a munkasor-mezőt és ágkülönbséget mutatja; egyik sem kapcsolja a mezőt a névvel ellátott fotó állapotához. N1/N3/N7 esetén a binárisban talált nyomok nem helyettesítik a hiányzó eredeti Picasa-felvételt vagy címkézett aránymérést. Ezért ezek a kérdések **nyitottak**; viselkedési állításuk nem minősíthető megerősítettnek. A 0,50 javaslati határra, a PicasaPy 0,9/960 beállításaira és az N4/N5/N6/N8 korábbi felvételeire vonatkozó állítások saját forrásukkal külön alátámasztottak.

### 53.5 A #5184 „Kész, ha” pontjai

| Pont | Eredmény | Bizonyíték / hiányzó adat |
|---|---|---|
| N1: talál-e az eredeti további ismeretlen arcot névvel rendelkező fotón | ⛔ Nyitott | A `0x0047b020` `+0x10` mezője a munkasor különleges tisztító/vezérlő ágát választja el a rendes feldolgozástól (`0x0049892d`-`0x00498944`, `0x0047b031`-`0x0047b03d`, `0x0049de00`, `0x0047b9f0`, `0x0047baf0`); a névvel ellátott fotóval való kapcsolata és az eredeti Picasa név előtti/utáni, azonos kétarcú képen végzett felvétele **NINCS MEG**. A helyi archívum 15 INI-je nem tartalmaz arc-kontrollt. |
| N3: eredeti arány és Red-küszöb a YuNet 960 px / 0,9 viszonyában | ⛔ Nyitott | Effektív Red-érték, Red-bemeneti WxH és azonos címkézett adaton mért arány **NINCS MEG**; `0,50` csak a javaslati határ. |
| N4: keret és név alapértelmezett láthatósága | ✅ Lezárt | Eredeti felvétel `job-187` (36.3): a megnevezett arcon alapból egyik sem látszik. |
| N5: személyszintű mellőzés útja és hatása | ✅ Lezárt | Eredeti felvétel `job-222..226` (37.11): személyszintű mellőzés nincs, a mellőzés arcszintű. |
| N6: személy törlése és hatása az arcokra | ✅ Lezárt | Eredeti felvétel `job-222/224` (37.10); a javítás #5391-gyel kiment. |
| N7: People Manager és Név nélküliek kijelölési modellje | ⛔ Részben nyitott | Név nélküliek többes kijelölése `job-180`-nal igazolt; People Manager Ctrl/Shift-felvétele **NINCS MEG**. |
| N8: People Manager referencia-képernyőkép | ✅ Lezárt | Eredeti felvétel `job-186`, 24. kép (36.3). |

**Fejlesztési következmény.** Eredeti/PicasaPy-eltérés nem bizonyított, ezért kódmódosítási lista és fejlesztői jegy nem indokolt. Új kutatási jegy sem kell: a három nyitott pont a #5184-ben marad.

**Nyitott / következő megszerzési út:**
- N1: eredeti Picasa kétarcú fotóval, név előtti és név utáni képernyő- és `faces=`-felvétel.
- N3: ugyanazon címkézett adatkészlet Picasa/PicasaPy futtatása; a Red betöltött paramétereinek és tényleges bemeneti képméretének rögzítése.
- N3: Ghidra-kör kell: `0x10107d70`: a `vsi_WeakClassifier threshold` szerializáló és a `+0x1c` mező írói/betöltői útjának adatfolyamával döntse el, hogy a `0x10103870` `runOnOneWindow` által összehasonlított küszöb a `red.cfg`-ből betöltött `vsi_WeakClassifier` értéke-e, és honnan kapja az effektív értéket. A meglévő `0x10103870` dekompiláció csak a pontszám és a `+0x1c` mező összevetését mutatja, a mező forrását nem; `0x10107d70` Ghidra-kimenet nincs a helyi referencia-tárban. [blokkoló]
- N7: két személyes People Manager felvétel kattintás, Ctrl+kattintás és Shift+kattintás után.

### 53.6 2026-10-23-i célzott Red.dll- és PicasaPy-kijelölés-ellenőrzés

**Red.dll, közvetlen utasításolvasás.** A helyi `Red.dll`-ben a `0x100057c0` minden külső elemhez meghívja a virtuális `+0x40` metódust (`0x10005859`), a visszaadott floatot a futó legnagyobb floattal hasonlítja össze (`0x10005869`-`0x10005873`), és csak a nagyobb értékkel frissíti a maximumot (`0x10005875`-`0x10005878`). A maximum kerül az eredménytömbbe (`0x100058d2`-`0x100058d8`). A `0x100057c0` sikeres bemenetnél `EAX=0`-val, az őrfeltétel hibájánál `EAX=1`-gyel tér vissza (`0x100058e3`, `0x100058f7`). A `0x10001570` ezt a státuszt alakítja: nemnulla eredménynél hibaágra lép és `-1`-et ad (`0x100015aa`-`0x100015b6`), nullánál `0`-t (`0x100015b9`-`0x100015bb`). A wrapper nem hasonlítja össze az arcpontszámot elfogadási küszöbbel.

**Független keresztellenőrzés.** A Picasa3.exe `0x0048e1f0` javaslati útja külön összeveti a Red.dll-től kapott pontszámot a `FRRecommendIncludeLimit` mezővel (`0x0048e330`-`0x0048e349`; az alapérték `0,50`, lásd 44.1). Ez megerősíti, hogy az alkalmazás a Red eredményét hasonlósági pontszámként is fogyasztja, és a javaslat-befogadási határt egy későbbi Picasa-ág alkalmazza. Nem zárja ki, hogy az ismeretlen virtuális `+0x40` metódus vagy a Red másik rétege saját detektorküszöböt használ. A friss kontextusú, vak újralevezetés egyezett a fenti, szűk következtetéssel; a bíráló a `0x10005869`-`0x10005878`, `0x100058d2`-`0x100058f7` és `0x100015aa`-`0x100015bb` utasításokat olvasta. A 52.5-ben rögzített Red.dll-Picasa3.exe verziópárosítási bizonytalanság ettől nem oldódik fel.

**Cáfoló kísérlet.** Megpróbáltam a `0x10001570`-et végső elfogadó/elutasító döntésnek tekinteni. A Red.dll közvetlen diszasszemblálása a `0x100015a2` hívást, a `0x100015aa` státusztesztet, a hibaág `0xffffffff` értékét és a sikerág nullázását mutatja; a függvény nem vizsgál floatot. A vak újralevezetés ugyanezt adta. Ez megcáfolja a wrapperre vonatkozó küszöb-hipotézist, de nem cáfolja a virtuális `+0x40` célban vagy a Red másik rétegében lévő küszöb lehetőségét.

### 🔁 Független újralevezetés
- **bíráló:** `fresh_red_rederive` (friss kontextus, a kutató magyarázata nélkül)
- **cím:** `0x100057c0`
- **eredmény:** EGYEZIK
- **a bíráló tényei:** a visszaadott float a futó maximummal hasonlítódik össze, a nagyobb érték frissíti azt; a függvény 0/1 státuszt ad, a `0x10001570` pedig 0/-1 visszatérési értékre alakítja. A virtuális cél és annak esetleges belső küszöbe nem vezethető le ezekből a címekből.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (az 53.2 N3 és 53.3 N7 bizonyítékai pontosítva; új 53.6 Red.dll- és PicasaPy-utánkövetés, független újralevezetés és cáfoló próba).


### 53.7 N3: a Picasa3.exe `plugins/Red.dll` útja és a helyi DLL-verzió határa (2026-10-23)

**A fájlverzió és a loader.** A megadott `Picasa3.exe` PE `VS_FIXEDFILEINFO` rekordja a `0x009A88F8` fájloffseten `FileVersionMS=0x00030009`, `FileVersionLS=0x008D0103`; ez a fájlverzió `3.9.141.259`. Az EXE SHA-256-a egyezik a `picasa3-index.sqlite` `binary_sha256` értékével. Az EXE kódja a `0x00871d70` függvényben a `plugins` sztringet használja (`0x00c818c4`), és a `0x006ccd90` útján a `Red.dll` nevet (`0x00ca8724`) adja át a modulterhelőnek. A `0x006cc9e0` függvény `0x00c402b8` IAT-címen `LoadLibraryA`-t hív, a `0x00c40234` címen `GetProcAddress`-szel feloldja a `REDENTRY` belépőt (`0x00ca8718`), majd meghívja azt (`0x006cca70`).

**A betöltendő fájl azonosítása.** A helyi Picasa-példány `Picasa3/plugins/Red.dll` fájljának SHA-256-a `da370693b59d89e7d48646d9617f5f595e371f8e1828cb1aa9f12530a17c8233`, egyezik a Red-index `binary_sha256` értékével, és a fájl a `Picasa3.exe` `plugins` könyvtárában van. A DLL-ben nincs PE verzió-erőforrás; a helyi Red-index átadási lapja (14. sor) viszont azt mondja, hogy a forrása egy Picasa 3.7 telepítés `plugins/Red.dll` fájlja. Ezért megerősített, hogy a 3.9.141.259-es EXE loader-kódja `plugins/Red.dll` nevet céloz, és a hash-azonosított DLL ott van ezen a helyi példányon; **nem bizonyított**, hogy ez a tiszta Picasa 3.9 kiadás DLL-je vagy hogy futás közben ténylegesen ez töltődött be.

**Célzott Red.dll-utasításolvasat.** A Red-index szerint a `0x101050f0` függvény mérete 557 bájt, a `0x101044f0`-é 1832, a `0x10103870`-é 1078. A `0x101050f0` két helyről hívja a `0x101044f0`-et (`0x1010526e`, `0x101052a5`); az utóbbi a `0x10103870` `runOnOneWindow` rutint hívja (`0x10104753`). A `0x101044f0` a bemeneti objektum `[ebx+0xbc]` és `[ebx+0xc0]` mezőit használja a vizsgáló ciklus határaihoz. Ez a helyi DLL útját pontosítja, de nem köti a `runOnOneWindow` összevetésének `+0x1c` mezőjét a `red.cfg`-hez, nem adja meg az eredeti Picasa futásidejű bemeneti WxH-ját, és nem ad mért felismerési arányt.

**Két független út.** **A út:** a Picasa3.exe indexelt sztring-xrefjei és célzott Capstone-olvasata a `plugins` → `Red.dll` → `LoadLibraryA` → `GetProcAddress(REDENTRY)` láncot mutatja. **B út:** a PE verzió-erőforrása és az EXE-hash azonosítja a 3.9.141.259-es futtathatót; a külön Red.dll-hash és a Red-index egyezése azonosítja a vizsgált DLL-t, a fájlrendszer pedig a plugin-útvonalon találja. A két út az EXE betöltőútjának és a helyi fájl azonosságának állításában egyezik; a DLL tiszta 3.9-es csomagból származását egyik sem bizonyítja.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a helyi Red.dll csak név szerinti, nem használt adat lenne. A `0x006ccd90` → `0x006cc9e0` hívási út, az `imports` tábla `LoadLibraryA`-bejegyzése és a `REDENTRY` feloldása tényleges modulbetöltési utat igazol, ezért a holt-sztring hipotézis megdőlt. Ugyanezek a források nem cáfolják a 3.7-es eredetű DLL és a tiszta 3.9-es kiadás közötti verziókülönbséget; ezt a cáfolatot is ugyanazzal a mércével ellenőriztem.

**N3 eredménye.** A helyi EXE-loader és fájlút megerősített, a tiszta 3.9-es csomag DLL-azonossága feltételes marad. Az effektív Red-küszöb, a ténylegesen betöltött modellérték, a Picasa felé adott képméret és az azonos címkézett adaton mért felismerési arány továbbra is **NINCS MEG**. A `0x101044f0`-re vonatkozó, 54.2-ben rögzített Ghidra-kérdés továbbra is nyitott: a `0x10103870` által összevetett `+0x1c` mező beállításának adatútja, a `0x101050f0` hívási kontextusával együtt, nem vezethető vissza a `vfr_SdkRelator` → `vqc_Relator::sim` ponthoz a meglévő kimenetekből. Eltérés és fejlesztői teendő nem bizonyított.

## 54. #5185, 2026-10-23-24: a 7-8. pont célzott bináris-auditja

**Hatókör.** A helyi Picasa3.exe célzott utasításolvasatát a meglévő Ghidra-kimenetekkel és bináris-indexszel vetettem össze; a Red.dll-nél külön ellenőriztem a `vsi_FaceViewDetector` és a `vsi_WeakClassifier` mezőútját. A programot nem futtattam, új Colab-felvétel és profilfájl-diff nem készült. Teljes `.text`-pásztázás nem történt. **Mérés (a `meroadat.tar` célzott taglistája és a kibontott fájlok):** 15 `.picasa.ini` fájlban 0 `[Contacts2]` és 0 `faces=` adat; ez csak azt jelenti, hogy ebben az archívumban nincs J8-hoz használható műveleti kontroll, nem bizonyít eredeti viselkedést.

### 54.1 A 7. pont: a névforrások olvasó- és íróágai

| Állítás | Forrás | Bizonyítottság |
|---|---|---|
| A `contacts.xml` rendes betöltése a `0x0041ee10` → `0x00586d00` → `0x00581920` láncon jut a `contacts.xml`/`backup.xml` feldolgozó ágaihoz; a két fájlút konstansai `0x00c90e74` és `0x00c90e94`, a feldolgozó hívásai `0x00581a24` és `0x00581b6a`. | bináris (`0x00581920`, `0x00586d00`; Ghidra `2026-10-22-ghidra-sor-197-200.txt`; `string_xrefs`) | megerősített: Ghidra-törzs és célzott utasításolvasat/hívási térkép egyezik |
| Sikeres `backup.xml`-helyreállítás esetén a `0x00581920` a `0x00581bcb` helyen meghívja a `0x00580110` XML-írót; a rendes `contacts.xml` mentési lánc `0x0041ba40` → `0x00586bd0` → `0x00580110`. A `0x00586bd0` csak a `[edi+0x13c]` jelző beállított ágában hívja az írót (`0x00586c31`-`0x00586c49`). | bináris (`0x00581920`, `0x00580110`, `0x0041ba40`, `0x00586bd0`) | megerősített: a writer-hívások és a jelzőfeltétel mindkét olvasatban látszik |
| A normál betöltő a `+0x13d` bájtot állítja (`0x00586d00`); ez nem a mentőág `[edi+0x13c]` jelzője. A `0x0066f2b0` külön Backup-paneles `contacts.xml` → `backup.xml` másoló út, hívója a `0x0066f470`. | bináris (`0x00586d00`, `0x0066f2b0`, `0x0066f470`; `xrefs` és sztring-xref) | megerősített a két bájt és a másolási irány elkülönítésében; nem bizonyít műveleti időzítést |
| A `.picasa.ini` `[Contacts2]` olvasó útja `0x0045a9d0` → `0x00587110`; az írói oldalon a `0x006956d0`/`0x0068c030`/`0x0068ac20` lánc eléri a `0x00586e20`-at, amely előállítja a `Contacts2` bejegyzést. Hogy a belső ág pontosan mikor és milyen fájltartalmat ír, nyitott. | bináris (`0x0045a9d0`, `0x00587110`, `0x006956d0`, `0x0068c030`, `0x0068ac20`, `0x00586e20`; 36-37. szakasz) | feltételes a Contacts2-írási ág teljes jelentésére; a belső fájlíró-ág Ghidra-kérése már a 36. szakaszban szerepel |
| A `faces=` INI-alakot a job-210/213 felvételek rögzítik; a `0x00484820` arcíró útja és a `0x004985e0` rekordmásoló szerepe a 51.4-ben van. A job-224 szerint albumtörlés után a `faces=` sorok eltűnnek, a `[Contacts2]` megmarad, és a db3 változik. | mérés (`job-210`, `job-213`, `job-224`); bináris (`0x00484820`, `0x004985e0`) | megerősített a rögzített kimenetekre; a műveletenkénti írási időzítésre nem |
| Hogy névadás, javaslat-elfogadás/elutasítás, People Manager OK/Cancel, törlés, bezárás vagy újraindítás pontosan mikor írja a `contacts.xml`-t, `.picasa.ini`-t vagy db3-at, továbbá a db3 mely rekordjai változnak és mikor olvasódnak vissza. | NINCS MEG; konkrét megszerzés: J8, fájlmásolat és hash minden művelet előtt/után, bezárás után és újraindítás után | nyitott |

**A két független út.** **A út:** a Ghidra-kimenet a `contacts.xml`/`backup.xml` nyitásait, a feldolgozó és az író hívásait azonosítja (`0x00581920`, `0x00580110`). **B út:** a Picasa-index hívó- és sztring-xrefjei, valamint a célzott Capstone-utasításolvasat külön megerősíti a `0x0041ba40` → `0x00586bd0` normál mentési láncot, a `+0x13c` mentőkaput, a `+0x13d` betöltési jelzőt és a Backup-panel másoló ágát. A bináris útvonalak egyeznek; a konkrét felhasználói művelethez tartozó fájlírás időpontját egyik út sem méri meg.

**Cáfoló kísérlet.** Azt próbáltam alátámasztani, hogy a `0x0066f2b0` a People Manager rendes mentője, mert `contacts.xml`-t kezel. A saját kódja és egyetlen közvetlen hívója a `contacts.xml` → `backup.xml` másolást a Backup-panelhez köti, ezért ezt a besorolást elvetettem. Külön próbáltam a betöltéskor írt `+0x13d` bájtot a mentési kapunak tekinteni; a `0x00586bd0` közvetlenül a `+0x13c` bájtot teszteli. A két jelzőt nem azonosítottam. A cáfoló ellenőrzése az indexelt hívó-/sztring-xrefen és a címre szűrt utasításokon is végigment.

### 54.2 A 8. pont: a Red.dll `threshold` mezője és a nyitott effektív küszöb

| Állítás | Forrás | Bizonyítottság |
|---|---|---|
| A `vsi_FaceViewDetector::runOnOneWindow` pontszámot gyűjt, majd a szakaszhoz tartozó `+0x1c` lebegőpontos mezővel hasonlítja össze; a `0x10103c14`-`0x10103c17` út a sikertelen összevetésnél visszatér a függvényből. | bináris (`0x10103870`; Ghidra `2026-10-23-sor-279-281-red.txt`) | megerősített a függvénytörzs összehasonlítására |
| A helyi Red.dll `vsi_WeakClassifier` vtable-jének `+0x0c` slotja a `0x10107d70` függvényre mutat; a `threshold =` felirat xrefje `0x101d5800`. A függvény a `this+0x1c` floatot szerializálja; a `0x10107f20` másik osztálymetódus ugyanennek az eltolásnak a floatját olvassa vissza. | bináris (helyi Red.dll: `0x10107d70`, `0x10107f20`, `0x101d5800`; RTTI/vtable) | megerősített a helyi DLL mezőútjára, nem a `runOnOneWindow` rekordjával való azonosságra |
| A detektor rekordjának `+0x1c` mezője és a WeakClassifier `this+0x1c` `threshold` mezője azonos eltolású, de az osztály- és adatút-kapcsolat nincs igazolva. A helyi `vfr_SdkRelator` konfigurációs objektum első hivatkozása külön feloldódott `vqc_Relator`-ra; ez nem a `vsi_FaceViewDetector` rekordja. | bináris (`0x10103870`, `0x10107d70`, `0x10107f20`, `0x100a3ca0`, `0x100a3a50`); helyi `red.cfg` | a mezők közti kapcsolat nyitott; a helyi `vqc_Relator` objektumpár külön megerősített (52.5) |
| A helyi `red.cfg` `vfr_SdkRelator+0x10` célja a beágyazott `vqc_Relator`; annak `+0x40` virtuális slotja `0x10100a10` (`sim`). A `ref=1` érték jelenlétjelző, nem egyedi objektumazonosító. | bináris (`0x10063ec0`, `0x100a3ca0`, `0x100a3a50`; nyers `red.cfg` `0x22b08a`-`0x22b0a1`; `0x10063f30` Ghidra-olvasó; ClassId és RTTI) | megerősített a helyi DLL+cfg kapcsolatra; a 3.9-es runtime-ra feltételes |
| A Picasa EXE `FRRecommendIncludeLimit=0,50` értéke ajánlásba-vételi szűrő, a `FRSuggestionThreshold`/`FRSortThreshold` alapértéke 85 javaslat-/rendezési beállítás; egyik sem bizonyítja a Red detektor végső küszöbét. A helyi Red.dll `0x100057c0` függvénye az egyes rekordpárok pontszámai közül a maximumot választja és az eredménytömbbe írja; a `0x10001570` csak a függvény siker/hiba visszatérési státuszát vizsgálja, egyikben sincs elfogadási küszöb-összevetés. | bináris (`0x0048e1f0`, 1.1-1.2, `0x100057c0`, `0x10001570`; Ghidra `2026-10-22-ghidra-sor-158-198.txt`, `2026-10-22-ghidra-sor-198-hivo.txt`; célzott Capstone; Red-index xref; 35.10-35.11) | megerősített erre a helyi DLL-re: két külön utasításolvasat egyezik; a tiszta 3.9-es DLL azonosságára és a végső küszöbre nem bizonyíték |
| A Red.dll ténylegesen betöltött küszöbértéke, a 3.9-es programmal használt DLL azonos buildje, a felismerés indítási/kihagyási feltétele, bemeneti WxH-ja és címkézett készleten mért aránya. | NINCS MEG; Red.dll hash-ellenőrzés a tiszta 3.9-es/Colab-példánnyal és J7 rögzített képkészletes felvétel | nyitott |

**A két független út.** **A út:** a `0x100057c0` Ghidra-törzse, kiegészítve a címre szűrt Capstone-utasításokkal, a `0x10005859` virtuális `+0x40` hívás után a `0x1000586c` max-összevetést, a `0x10005875`-`0x10005878` maximumfrissítést, majd a `0x100058d2`-`0x100058d8` eredménykiírást mutatja; a `0x10001570` `0x100015aa`-nál a matcher státuszát teszteli, és `0`/`-1` státuszt ad vissza. **B út:** külön, vak `llvm-objdump` újraolvasás és a Red-index közvetlen hívó-xrefje ugyanezt adta: a matcher maximumot állít elő, egyetlen indexelt közvetlen hívója pedig csak a státuszt kezeli. A két út egyezik abban, hogy e két függvényben nincs végső pontszámküszöb. Ez csak a hash-azonosított, helyi Red.dll-re megerősített; a forrás-riport Picasa 3.7-et nevez meg, ezért a tiszta 3.9-es futásra nem általánosítható.

A `0x10103870` Ghidra-törzse továbbra is a detektor rekordjának `+0x1c` mezőjével való összevetést mutatja; a külön `vsi_WeakClassifier` szerializáló és olvasó (`0x10107d70`, `0x10107f20`) a saját `this+0x1c` float típusú mezőjét köti a `threshold =` felirathoz. A `red.cfg` nyers rekordhatárai, ClassId-regisztere és a `0x10063f30` Ghidra-olvasó a helyi `vfr_SdkRelator` → beágyazott `vqc_Relator` kapcsolatot támasztja alá, de **nem** kapcsolja a `vqc_Relator::sim` eredményét a `vsi_FaceViewDetector` `+0x1c` mezőjéhez. A helyi DLL eredetriportja Picasa 3.7-et nevez meg; a mellette található 3.9.141.259-es EXE önmagában nem bizonyítja, hogy a vizsgált DLL a tiszta 3.9-es futásban töltődött be (52.5).

**Cáfoló kísérlet.** Megpróbáltam a már ismert `0,50` értéket, a 85-ös javaslat-/rendezési alapértékeket, a `0.0001` értéket és a `vqc_Relator` 0-1 közé korlátozott pontszámát a detektor küszöbének tekinteni. A címek szerinti felhasználás ezt nem támasztja alá: a `0,50` az ajánlásba-vételhez tartozik (`0x0048e1f0`), a 85 a két UI-javaslat-beállításhoz, a `0.0001` szögeltéréshez (`0x100af585`), a 0-1 korlátozás pedig pontszám-visszaadás, nem elfogadó/elutasító határ (`0x10100a10`, 52.5). A 0x100057c0 maximumválasztásra vonatkozó következtetést cáfolni próbáltam úgy, hogy a matcher `+0x40` virtuális hívását küszöbtesztként, a `0x10001570` ágát pedig pontszám szerinti elutasításként értelmeztem; az utasítások szerint az előbbi minden jelöltre pontszámot kér, majd a jelenlegi maximumhoz hasonlít, az utóbbi pedig csak a matcher visszatérési státuszát ellenőrzi. A független `llvm-objdump` újraolvasás ugyanezt erősítette meg, ezért ez a cáfoló hipotézis nem állt meg. Külön cáfoló próbával a `red.cfg` `ref=1` értékét objektumazonosítónak vettem: a `0x10063ec0` író `cmp [ebp+8],0` + `setne` utasításai nem-null jelzőként kódolják, a `0x10063f30` Ghidra-olvasó pedig nem-null jelző esetén tölti be a beágyazott objektumot; a nyers rekordban közvetlenül ezután a beágyazott `vqc_Relator` ClassId áll. A bináris író, olvasó és a rekord bájtjainak külön ellenőrzése egyezően igazolja, hogy az 1 a célmutató jelenlétét jelöli, nem egyedi objektumazonosító. Ez nem köti a `vqc_Relator` pontszámát a detektor `+0x1c` mezőjéhez.

**A #5185 „Kész, ha” pontjai e kör után.**

| Pont | Eredmény | Bizonyíték / nyitott út |
|---|---|---|
| 1. Név nélküliek nézet, fejléc, csoport, bélyegek, tálca és kijelölés | ⛔ Részben | job-162/163/207/208 és a 35.3/1. pont; tartós sorrend, többarcú csoporthatár, Ctrl/Shift/húzás és tálcahatás további J2-felvételt igényel. |
| 2. Arc kijelölése, névmező, névjegyjavaslat, Enter/OK és kimenet | ⛔ Részben | job-163/167/179 és 35.3/2.; javaslatelem-kattintás és csempemező-Escape utáni eredeti állapot nyitott (J2). |
| 3. Arcfelismerési javaslat, elfogadás és elutasítás | ⛔ Részben | job-207 súgószövege; élő javaslat/elfogadás/elutasítás és tartós fájlkimenet nincs meg (J3). A névjegyek automatikus kiegészítése nem arcfelismerési javaslat. |
| 4. Mellőzés, megerősítés, mellőzöttek és visszahozás | ⛔ Részben | job-209/210 és 35.3/4.; csempe-X út rögzített, a fejléc `Ignore Selected` és `Back to Unnamed` utáni állapot J4-ben nyitott. |
| 5. Személy-album, nézetváltás, átnevezés, egyesítés, törlés | ⛔ Részben | job-213, job-222/224 és 35.3/5.; zoommód első állapota, átnevezés és teljes összevonás felvétele nyitott (J5). |
| 6. People Manager elrendezés, kijelölés, mezők, OK/Mégse | ⛔ Részben | job-163/167/226, job-186, `contactmgr.fen` és 35.3/6.; Ctrl/Shift és a módosított adatok tartós Cancel-hatása nyitott (J6). |
| 7. `contacts.xml`, `[Contacts2]`, `faces=`, db3 olvasása/írása | ⛔ Részben | A 54.1 és 35.3/7 dokumentálja az ismert olvasó-/íróágakat és mért ini/db3 kimeneteket; műveleti időzítés és teljes diff J8-cal nyitott. |
| 8. Arcfelismerés indítása, kihagyásai és küszöbe | ⛔ Részben | Az 52.5/54.2-54.3/c feloldja a helyi Red.dll `vqc_Relator` objektumpárt, az ablakbejáró hívási szerepét és a `vsi_WeakClassifier` streamelt mezőjét; a tényleges modellstream, a detektorrekord és az osztályozómező kapcsolata, a tiszta 3.9-es DLL-azonosság, a futásidejű érték, a bemeneti méret, indítás/kihagyás és mért arány J7-felvétellel nyitott. A `0x101044f0` korábbi Ghidra-köre lefutott; új, azonos című kérés nincs. |

**Következtetés és jegykezelés.** Mind a nyolc pontnál van hivatkozott felvétel vagy bináris eredmény, illetve konkrét nyitott megszerzési út, de a jegy teljes „Kész, ha” feltétele nem teljesült. PicasaPy-eltérésre nincs bizonyíték, ezért Codex-kész kódmódosítási lista nem indokolt. A #5179-#5184 jegytörzsek átírása ebben a munkamenetben nem történt meg; a GitHub-hozzáférés tiltott, a jegyek teljes törzse a megadott anyagban nincs benne. A nyitott felvételek a már meglévő J2-J8 feladatok; külön kutatási jegy csak akkor kell, ha a hívó a következő Ghidra-kört vagy tiszta 3.9-es DLL-hash beszerzését külön munkára bontja. A 52.5 régi `0x10063f30`-as objektumhivatkozás-kérdése megválaszolódott; a detektor `+0x1c` mező és a `vqc_Relator` pontszáma közti kapcsolat maradt nyitott.

**Nyitott / megszerzési út:** J2-J6: az előző táblázatban jelölt eredeti UI-lépések; J7: tiszta Picasa 3.9/Colab Red.dll hash, azonos címkézett képkészlet és tényleges bemeneti méret; J8: `contacts.xml`, `.picasa.ini`, db3 fájlállapot minden művelet előtt/után, bezáráskor és újraindítás után. A korábbi `0x101044f0`-ra kért Ghidra-kör a hívó/rangsorolási szerepet és a küszöbmező szemantikáját tisztázta (54.3/a); a gyűjtemény dinamikus elem-típusa és a stream fájlforrása ott maradt nyitott.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (52.5: a helyi `red.cfg` `vfr_SdkRelator` → `vqc_Relator` objektumkapcsolat feloldása; 54.2 és a 8. pont állapotának pontosítása, a küszöb adatút nyitott kérdése).

### 54.3 2026-10-26-i forrás-összevetés a 7-8. ponthoz: Eredeti | Nálunk | Teendő

**Hatókör.** Az eredeti Picasa 3.9-et ebben a körben nem futtattam, új Colab-felvétel és műveletenkénti profil-diff nem készült. Az eredeti oldalon a már rögzített bináris- és felvételi eredményeket egészítem ki a `0x00586e20` arcíró-hívási környezetével és a Red.dll összehasonlítás közvetlen utasításellenőrzésével. A „Nálunk” oszlop a munkafa `0.9.248` forrásolvasata (`pyproject.toml:13`), nem futásidejű mérés.

| Eredeti | Nálunk (`0.9.248`, forrásolvasat) | Teendő |
|---|---|---|
| **7. Névforrások:** a központi `contacts.xml` betöltő- és íróágai, valamint a `[Contacts2]` beolvasása a 54.1/35.10/35.12 szerint elkülönül. A `0x00484820` arcíró a `0x00586e20` segédet a `faces` kulcs összeállítása előtt hívja; a segéd `Contacts2` szakaszt kér, kontaktot keres, `%s;%s;%s` értéket formáz, majd virtuális metódust hív (`0x00586e52`, `0x00586e62`, `0x00587060`, `0x005870de`; `0x00484820`). A felvétel job-210/213 rögzíti a `[Contacts2]`/`faces=` alakot, job-224 pedig azt, hogy albumtörlés után a `faces=` sor eltűnt, a névjegy megmaradt és a db3 változott. A felhasználói művelethez tartozó tényleges fájlírási idő és a db3 érintett rekordjai **NINCS MEG**. | A `PeopleManagerDialog.qml` `commitChanges` útja előbb `savePeopleManagerChanges`-t hívja, majd függő arc esetén `assignNameToFaces`-t (`:335-408`). A controller változott központi névjegyeknél a saját profil `contacts.xml` fájlját menti (`people_controller.py:375-500`, `contacts_xml.py:143-146`), a helyi mappák ini-frissítése `update_document`-on fut (`people_controller.py:502-572`). Az új arc hozzárendelése `FacesHelper.addFace`-on keresztül oldja fel/hozza létre a helyi contact ID-t és írja a `faces=` párt (`face_scan_controller.py:917-985`, `faces_helper.py:183-202`). Ez különálló kódút a Picasa `contacts.xml`/db3 mentési útjától. | Eredeti J8: egy kontrollált profilban rögzítsd `contacts.xml`, `backup.xml`, érintett `.picasa.ini` és db3 SHA-256-át, időbélyegét és tartalmát közvetlenül névadás/Choose, javaslat elfogadás/elutasítás, People Manager OK/Cancel/törlés előtt és után, kilépéskor és újraindítás után. A `0x00586e20` virtuális célját/commit-határát csak akkor tekintsd fájlírónak, ha azt a célfüggvény vagy a fájldiff igazolja. |
| **8. Arcfelismerés:** a helyi Red.dll `vsi_FaceViewDetector::runOnOneWindow` útja az összegzett pontszámot a jelölt rekord `+0x1c` float mezőjéhez hasonlítja (`0x10103c14`-`0x10103c1e`, Ghidra `2026-10-23-sor-279-281-red.txt`; célzott Capstone). A mező futásidejű értéke, betöltési/config adatútja, a tiszta 3.9-es DLL azonossága, az indítás/kihagyás és a mért felismerési arány **NINCS MEG**. A `FRRecommendIncludeLimit=0,50` külön ajánlásba-vételi szűrő (35.10), nem igazolt Red-detektor-küszöb. A vizsgált EXE verzióadata `3.9.141.259`, a helyi Red.dll SHA-256-a `da370693b59d89e7d48646d9617f5f595e371f8e1828cb1aa9f12530a17c8233`; ez egyezik a Red-indexelt DLL-lel, amelynek forrás-riportja Picasa 3.7-et jelöl, ezért a 3.9-es runtime-ba betöltött DLL azonossága nem következik belőle. | Az automatikus scan a `syncFinished` után indul, ha a beállítás bekapcsolt (alapértéke igaz) és nincs aktív scan (`application.py:1779`; `face_scan_controller.py:291-305, 776-784`). Forrás szerint kihagyja a tiltott mappát, videót, azonos mtime/méretű már vizsgált fájlt és bármely képet, amelynek ini-jében megnevezett arc szerepel (`face_scan_controller.py:474-496, 1558-1582`). A saját YuNet-detektor kód szerinti alapértékei: score `0.9`, NMS `0.3`, top-k `5000`, maximális méret `960` (`src/picasapy/faces/detector.py:40-49, 181-183`). Ezek PicasaPy-forrásértékek; nem helyettesítik és skálájuk nem köthető az eredeti Red.dll mezőjéhez. | Eredeti J7: azonosított tiszta Picasa 3.9 futásból szerezd meg a ténylegesen betöltött Red.dll hashét; kontrollált, címkézett képkészleten rögzítsd az indítási eseményt, kihagyásokat, bemeneti méretet és eredményt. A `0x10103870` által használt rekord `+0x1c` mező tényleges adatútját és értékét kell azonosítani; addig ne adj meg numerikus eredeti küszöböt. |

**A két független út és a bizonyítottság.**

- **`0x00586e20` szerepe:** A út: a `2026-10-23-ghidra-sor-264-267.txt` `0x00484820` törzse a `0x00586e20` hívást a `faces` kulcs kezelése elé teszi. B út: az eredeti EXE célzott Capstone-olvasata ugyanezt a hívási helyet, a Picasa3.exe-binárisindex sztring-xrefjei pedig a `Contacts2` és `%s;%s;%s` konstansokat külön mutatják. Egyezésük a `Contacts2`-adat arcíró ágban történő előállítását/átadását támasztja alá. **Nem** azonosítják a virtuális metódus célját, és nem mutatnak műveleti fájl-flush időpontot. Az e körben újrafogalmazott szerep ezért **feltételes**.
- **Red.dll `+0x1c` összevetés:** A út: a `2026-10-23-sor-279-281-red.txt` Ghidra-törzse a `iVar5+0x1c` floatot a pontszámhoz hasonlítja. B út: a helyi DLL közvetlen Capstone-olvasata a `0x10103c14 fld dword ptr [ecx+0x1c]`, `0x10103c17 fcompp` és `0x10103c1e` feltételes ugrásokat mutatja; a Red-index függvényadata és hívási xrefje külön ellenőrizhető. Ezek egyeznek a helyi DLL utasításszintű működésében. A mező osztályazonossága és konfigurációs adatútja, a futásidejű érték, valamint a tiszta Picasa 3.9-es runtime-hoz tartozása **nyitott**; ezért az eredeti Picasa 3.9 effektív küszöbére nincs megerősített állítás.

**A mező adatútjának helyi diszasszembly-ellenőrzése.** A `0x101044f0` célzott Capstone-olvasatában a `0x1010455a` `[ebx+0x1c]` címét átadja a `0x10013c30` függvénynek; ugyanebben a függvényben a `0x10104b2c` `[ebp+0x1c]`-be ír. A hívó `0x101050f0` a `0x10105162` címen szintén olvas egy `[ecx+0x1c]` mezőt, majd két helyen hívja a `0x101044f0`-et. A `0x10013c30` törzse a saját bemenete `+0x4` és `+0x8` float mezőit olvassa, majd a `0x100489e0`-et hívja. Ez a diszasszembly önmagában nem azonosítja, hogy ezek közül bármelyik objektum megegyezik-e a `0x10103870` `iVar5` rekordjával. A 2026-10-26-i Ghidra-kimenet tisztázza a küszöbmező szerepét, de a dinamikus elem-típus és a teljes stream-adatút nyitott marad (54.3/a).

**A `0x101044f0` szerepének pontosítása.** A célzott `llvm-objdump`- és Capstone-olvasat, valamint a Red-index hívási xrefje egyezően mutatja, hogy a `0x101044f0` meghívja a `0x10103870` detektort (`0x10104753`), a visszaadott pontszámot korábbi jelöltekkel hasonlítja össze (`0x10104980`-`0x10104996`), majd a legjobbat rögzíti (`0x10104a60`). A `0x10104b2c` egy eredményrekord `+0x1c` mezőjébe ír; nincs adat arra, hogy ez az objektum azonos lenne a `0x10103870` által olvasott detektorküszöb-mezővel. Ezt az azonosságot nem feltételezem. Így a `0x101044f0` helyi szerepe **megerősített** rangsoroló/hívó út, de nem bizonyított küszöbmező-író. A 2026-10-26-i Ghidra-kimenet megerősíti a hívási és rangsorolási szerepet; a `+0x58` gyűjtemény dinamikus elemtípusát és a stream fájlforrását nem nevezi meg (54.3/a).

**Cáfoló kísérlet és ellenőrzése.** Megpróbáltam a `0x00586e20` „Unable to persist contact_id” naplószövegét és a `Contacts2` sztringet annak bizonyítékaként venni, hogy ez a függvény önmagában lemezre ír. A célzott Capstone-olvasatban a függvény névjegyet keres, `%s;%s;%s` értéket készít, majd nem feloldott virtuális célra ugrik; a `0x00484820` hívó ezt követően külön `faces` mezőt dolgoz fel. Ez a közvetlen fájlíró állítást **nem támasztja alá**, de a virtuális cél hiánya miatt közvetett írást nem is zár ki. A cáfoló eredményt a Ghidra-hívó törzsével és az indexelt hívás-/sztring-xrefekkel ellenőriztem; ezek a hívási sorrendet igazolják, a fájlrendszer-hatást nem. Korábban a `0,50` értéket is vizsgáltam Red-küszöbjelöltként; a `0x0048e1f0` használata ajánlásba-vételhez köti, ezért az a feltevés nem maradhat a detektor küszöbének bizonyítékaként (54.2).

**A #5185 „Kész, ha” 7-8. pontjának állapota.**

| Pont | Eredmény | Bizonyíték / következő adat |
|---|---|---|
| 7. `contacts.xml`, `[Contacts2]`, `faces=`, db3 olvasása/írása | ⛔ Részben | Az eredeti bináris út és a mért ini/db3 példák dokumentáltak; a műveleti írási idő és érintett db3 rekord nincs meg. J8 profil-diff kell. A PicasaPy `0.9.248` forrásút külön dokumentálva, de nem eredeti viselkedésmérés. |
| 8. Arcfelismerés: indítás, kihagyás, küszöb | ⛔ Részben | A 54.3/a szerint a helyi Red.dll `+0x1c` mezője küszöbszerepű, és a WeakClassifier `threshold` mezőjével egyező sémájú; a tényleges modellérték/streamforrás, a tiszta 3.9-es runtime DLL-hash, az eredeti indítás/kihagyás/bemenet/arány nincs meg. J7-mérés kell. |

**Következtetés.** A 7-8. pont eredeti viselkedése továbbra sincs teljesen meghatározva; a binárisból megállapítható kódút és a PicasaPy aktuális forrása közös, Eredeti | Nálunk | Teendő táblában szerepel. E kör alapján nincs bizonyított PicasaPy-eltérés, ezért kódmódosítási feladat nem indokolt. A helyi Red.dll-ben a detektor `+0x1c` mezőjének küszöbszerepe tisztázódott; a tényleges streamforrás és effektív érték, valamint e DLL tiszta Picasa 3.9-es jelenléte továbbra is **NINCS MEG** (54.3/a).

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (54.3: a 7-8. pont aktuális forrás-összevetése, bizonyítottsági fok, cáfoló próba és nyitott megszerzési út).

#### A Red.dll detektor `+0x1c` mezőjelöltjének íróútja (2026-10-26, statikus vizsgálat)

Az alábbi címek a helyi, SHA-256 `da370693b59d89e7d48646d9617f5f595e371f8e1828cb1aa9f12530a17c8233` értékű Red.dll-re vonatkoznak. A DLL forrás-riportja Picasa 3.7-et jelöl; a tiszta Picasa 3.9 futásba betöltött DLL azonossága nincs igazolva.

| Állítás | Forrás | Bizonyítottság |
|---|---|---|
| A `0x101033e0` factory a `0x0041a004` ClassId-ágban a `0x10107c00` konstruktort hívja; ez a `vsi_WeakClassifier` konstruktora. | bináris (`0x101033e0`, `0x10103408`-`0x10103417`, `0x101034a3`-`0x101034b1`, `0x10107c00`; Red-index RTTI és `classids.json`) | megerősített: a factory diszasszemblye, a vtable RTTI-neve és a ClassId-térkép egyezik |
| A konstruktor inicializálója a `0x10107be0` `fldz` utasítását a `0x10107be4` címen az objektum `+0x1c` mezőjébe írja; a `vsi_WeakClassifier` saját induló értéke ezért pontosan `0.0`. | bináris (`0x10107be0`-`0x10107be4`) | feltételes: egyetlen mezőíró utasításút közvetlen olvasata |
| A `0x10107f20` betöltő a `this+0x1c` címet a `0x1005bb50` helpernek adja; a helper négy bájtot olvas, floatként konvertál és a célra írja. A szerializáló `0x10107d70` ugyanezt a mezőt menti, debug-felirata `threshold =` (`0x101d5800`); a `0x10107ca0` másoló szintén továbbviszi a mezőt. | bináris (`0x10107f20`, `0x10107f87`-`0x10107f8c`, `0x1005bb50`, `0x1005bb68`, `0x1005bba0`, `0x10107d70`, `0x101d5800`, `0x10107ca0`, `0x10107cc8`-`0x10107ccb`; RTTI/vtable) | megerősített a `vsi_WeakClassifier` saját mezőútjára: diszasszembly és RTTI/vtable út egyezik |
| A `0x10103870` a `vsi_FaceViewDetector` `+0x58` gyűjteményéből vett elem `+0x1c` floatját küszöbként olvassa. A WeakClassifier loader ugyanezt a mezőt `threshold`-ként tölti; a gyűjtemény minden elemének dinamikus RTTI-típusa még nincs közvetlenül bizonyítva. | bináris (`0x10103870`, `0x10107f20`, `0x101d5150`, `0x101d5898`; Ghidra 2026-10-26; Capstone; string-xref) | megerősített a mező küszöbszemantikájára; feltételes az egyedi objektumtípus-kapcsolatra |
| Az effektív detektáláskor használt float, a betöltő stream fájl-/beállítás-forrása és az, hogy az érték `registry`, ini vagy más modelladat felől érkezik-e. A helyi `red.cfg` nyers adataiban a `0x0041a004` és `0x0041a005` ClassId rekordfejléce nem található. | NINCS MEG; `red.cfg` ellenőrzése: célzott nyers ClassId-keresés | nyitott; a `0.0` csak a konstruktor alapértéke, a stream felülírhatja |

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A helyi DLL `vsi_WeakClassifier` mezőjének pontos alapértéke `0.0`, de betöltéskor streamből olvasható float kerül a `+0x1c` mezőbe. Nem bizonyított, hogy ez a `0x10103870` által ténylegesen használt elem, így az effektív eredeti küszöb **NINCS MEG**. | A PicasaPy saját detektorértékei más kódútból származnak (54.3 táblázata); ezen a statikus körön nem hasonlítottam őket az eredeti streamértékhez. | Célzott Ghidra-dekompilálással kösd össze a FaceViewDetector `+0x4c` betöltött gyűjteményét a `0x10103870` elemével, majd kövesd a nested-object loader streamjét a konkrét modell-/konfigurációs forrásig. A tiszta Picasa 3.9-es futásban a betöltött Red.dll hashét és a streamből beolvasott floatot külön kell igazolni. |

**A két független út és bizonyítottság.** **A út:** a célzott Capstone-olvasat követi a ClassId factory → konstruktor → `+0x1c` default-zero írás, majd stream-loader → négybájtos lebegőpontos olvasás és a párhuzamos szerializáló/másoló útvonalat. **B út:** a Red-index RTTI/vtable és a `classids.json` külön köti a `0x10107c00`, `0x10107f20`, `0x10107d70`, `0x10107ca0` címeket a `vsi_WeakClassifier` osztályhoz, és a `0x0041a004` ClassId-hoz. Az utak egyeznek a jelölt osztály saját `+0x1c` mezőjéről; nem bizonyítják, hogy ez a `0x10103870` által használt rekord. A végső kapcsolat ezért **feltételes**, az effektív eredeti érték és forrás **nyitott**.

**Cáfoló kísérlet.** A „detektorküszöb állandóan `0.0`” hipotézist a `0x10107f20` stream-betöltő cáfolja: a `+0x1c` címre a `0x1005bb50` négy bájtos lebegőpontos értéket ír. Ezt az ellenirányú `0x10107d70` szerializáló, a `threshold =` sztring-xref és a `0x10107ca0` másoló ellenőrzése támasztja alá. A `red.cfg`-ben keresett ClassId-fejlécek hiánya nem bizonyítja, hogy a modell nincs máshol; ezért a fájlforrást nem következtettem ki.

**A korábbi Ghidra-kérdés állapota.** A `0x101044f0`, `0x10103870` és `0x10107f20` 2026-10-26-i Ghidra-kimenete tisztázza a küszöbmező szemantikáját és a WeakClassifier betöltőjét. A gyűjtemény dinamikus elemtípusa, a streamet szolgáltató fájl és az effektív érték nyitott marad; a pontos megszerzési út a 54.3/a-ban szerepel.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (54.3: a `vsi_WeakClassifier` `+0x1c` mezőjének inicializálója, a streamből betöltő függvénye és nyitott kapcsolata a detektor rekordjával).

#### 54.3/a A detektor `+0x1c` mezője és a stream forrása (2026-10-26, Ghidra 282-304)

**Hatókör.** Ez a kiegészítés a helyi, SHA-256 `da370693b59d89e7d48646d9617f5f595e371f8e1828cb1aa9f12530a17c8233` értékű Red.dll-re vonatkozik; a fájl forrás-riportja Picasa 3.7-et jelöl. Nem bizonyítja, hogy ez a DLL vagy ugyanez a modell tölti be a tiszta Picasa 3.9.

| Állítás | Bizonyíték | Bizonyítottság |
|---|---|---|
| A `0x101044f0` ablakbejáró meghívja a `0x10103870` detektort (`0x10104753`); az utóbbi járja be a detector `+0x58` gyűjteményét, és pontszámot ad vissza, amelyből a hívó külön a legnagyobbat tartja meg. Az itt `param_10+0x1c`-re írt eredményrekord-mező nem a detektor küszöbmezője. | bináris (`0x101044f0`, Ghidra `2026-10-26-2026-10-26-ghidra-sor-282-304-red.txt`; Red-index xref) | megerősített a hívási és rangsorolási szerepre |
| A `0x10103870` a `+0x58` gyűjtemény aktuális elemén számított részpontszámot hozzáadja a `local_1c` összeghez. Ha az elem `+0x18` mezője nemnegatív és az összeg kisebb az elem `+0x1c` floatjánál, elutasítja az ablakot. Ez a mező tehát az adott detektor-lépcső pontszámküszöbe. | bináris (`0x10103870`, Ghidra-kimenet; Capstone: `0x10103c14` `fld dword ptr [ecx+0x1c]`, `0x10103c17` `fcompp`, `0x10103c1e` ág) | megerősített a mező küszöbszerepére |
| A `0x10107f20` a Red-index `vsi_WeakClassifier::vftable` listájában szereplő betöltőmetódus. A `+0x1c` mező címét a `0x1005bb50` readernek adja; ez négy bájtot olvas, majd floatként tárol (`0x1005bb68`-`0x1005bba0`). A `threshold =` sztring xrefje a `0x10107f20`-ra mutat. A detektorban olvasott `+0x1c` mező szemantikája és a WeakClassifier `threshold` mezője egyezik; a Ghidra-kimenet nem nevezi meg közvetlenül a `+0x58` gyűjtemény minden elemének dinamikus típusát, ezért a konkrét objektumazonosság feltételes. | bináris (`0x10107f20`, `0x1005bb50`, `0x101d5898`, `0x101b70bc`; célzott Capstone; Red-index RTTI és string-xref) | megerősített a loader mezőútjára és a küszöbszemantikára; feltételes az összes gyűjteményelem konkrét RTTI-típusára |
| A `red.cfg`-ben a `vsi_WeakClassifier` (`ClassId 0x0041a004`, fejléc `00 03 04 a0 41 00`) és a `vsi_FaceViewDetector` (`ClassId 0x0041a005`, fejléc `00 03 05 a0 41 00`) objektumfejléce egyaránt 0 alkalommal fordul elő. A fájl SHA-256-a `916d69fd9a412ea937b49f3b0b1401076193dc9be096b3af71921aeba6f51835`. A helyi `Picasa3/plugins` alatt a célzott `.cfg`, `.model`, `.dat`, `.bin` és `.xml` fájlnév-lista csak ezt a `red.cfg`-t találta. Ez a helyi Picasa 3.7-es fájlra szól; önmagában nem zár ki másik modellformátumot, beágyazott adatot vagy másik kiadási fájlt. | mérés (a helyi `plugins/red.cfg` pontos fejlécbájt-keresése és célzott fájlnév-lista; ClassId-nevek: `eszkozok/redcfg/classids.csv:440-441`, `leltar.json`) | megerősített a vizsgált fájlra; nem teljes forrásazonosítás |
| A `vsi_WeakClassifier` konstruktor `+0x1c` alapértéke `0.0`, de a betöltő streamből felülírja; ez nem az effektív modellküszöb. A streamet szolgáltató fájl és a futásidőben beolvasott float helyi bizonyítékból **NINCS MEG**. | bináris (`0x10107be0`-`0x10107be4`, `0x10107f87`-`0x10107f8c`, `0x1005bb50`); hiányzó érték: `NINCS MEG` | megerősített, hogy a `0.0` csak kezdőérték; a stream forrása és effektív értéke nyitott |

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A helyi Red.dll detektor egy pontszámküszöböt olvas az osztályozó-rekord `+0x1c` mezőjéből; ez a `vsi_WeakClassifier::threshold`-sémának felel meg. A tényleges modellfájl és érték nem azonosított. | E körben PicasaPy-forrás vagy futásidejű küszöb nem lett újramérve; a korábban dokumentált YuNet-paraméterek nem az eredeti stream bizonyítékai. | Ne használd a konstruktor `0.0` értékét effektív küszöbként. A `0x10104290` betöltő/gyűjtemény elem-típusát és a `0x100685a0` ObjectRef adatfolyam-forrását kell követni, majd az azonosított Picasa 3.9-es modellből kiolvasni a floatot. |

**A két független út.** **A út:** a `0x10103870` Ghidra-törzse követi az elemenkénti részpontszámot, az összegzést és a `+0x1c` küszöbtesztet; a `0x101044f0` kimenete azonosítja a hívási ciklust és elkülöníti a legjobb eredmény rekordját. **B út:** a célzott Capstone-utasítások a `0x10103c14`-`0x10103c1e` mezőolvasást/float-összevetést, illetve a `0x10107f87`-`0x10107f8c` `this+0x1c` adatfolyam-olvasást mutatják; az RTTI/vtable és a `threshold =` xref a második mezőt a `vsi_WeakClassifier`-hez köti. Az utak egyeznek a küszöbszerepben. A gyűjtemény dinamikus elem-típusa és a stream fájlútja nem következik belőlük.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a detektor `+0x1c` mezője küszöb, és hogy a `vsi_WeakClassifier` streamje a helyi `red.cfg`-ből származik. Az első hipotézist a detektor ágának összehasonlítása és a WeakClassifier `threshold =`-ként szerializált, ugyanilyen eltolású floatmezője nem cáfolta; ezzel szemben a „küszöb mindig `0.0`” változatot a négybájtos streamolvasó megdönti. A `red.cfg`-re vonatkozó jelöltet a helyi fájl pontos ClassId-fejléc-keresése cáfolja: mindkét osztályból nulla fejléc van. Ez csak a vizsgált fájlt zárja ki, más modellforrást nem azonosít.

**A korábbi Ghidra-kérések státusza (2026-10-26).** A `0x10104290` a `classifier arr` mezőt és az array-tároló útját tisztázta; a `0x100685a0` a generikus `ObjectRef`-betöltési és stream-átadási határt. A bizonyíték és a korlátok a 54.3/c-ben vannak. A pontos modellfájl/stream és az effektív float továbbra is **NINCS MEG**; újabb Ghidra-kör ezekből a függvénytörzsekből önmagában nem indokolt.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (54.3/a: a `0x10103870` küszöb-mezőszemantikája; a `vsi_WeakClassifier` betöltőjével való kapcsolat; a helyi `red.cfg` negatív eredménye; az effektív érték és streamforrás nyitott státusza).

### 54.3/b A `Contacts2`-értéket előállító helper hívási útjai (2026-10-26, helyi diszasszembly)

**Hatókör és forrásazonosítás.** A vizsgált `Picasa3.exe` PE-verziója `3.9.141.259`, SHA-256-a `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`. Az index `functions` táblája adja a diszasszembly méreteit; a teljes függvénytörzsekre célzott `annot_disasm.py` olvasat készült, teljes `.text`-pásztázás nem.

| Állítás | Bizonyíték | Bizonyítottság |
|---|---|---|
| A `0x00586e20` helper megkeresi a `Contacts2` szakaszt (`0x00586e52`), a kontakt három mezőjéből `%s;%s;%s` értéket állít elő (`0x00587060`; sztringcím `0x00c91104`), „Persisting contact to INI…” naplót ad (`0x00586fa7`; sztringcím `0x00c910a8`), majd a negyedik argumentumból kapott objektum vtable-jének `+0x8` slotját hívja (`0x005870d2`-`0x005870de`). | bináris (`functions.size=752`; `annot_disasm.py` teljes törzs; pozitív `string_xrefs`) | megerősített a szakasz-/érték-előállításra és a virtuális átadásra; a lemezre írásra nem |
| A bináris index három közvetlen hívó-xrefet tart nyilván: `0x00484820`, `0x0068ac20`, `0x007d55f0`. A célzott diszasszemblyben a hívások rendre `0x00485118`, `0x0068ac5a`, `0x007d5ca6` címen állnak. | bináris (`xrefs`; `functions.size`: 2740, 86, 2681; célzott Capstone-olvasat) | megerősített a három indexelt közvetlen hívásra |
| A `0x007d55f0` arc-metaadatot dolgoz fel: az indexelt sztringjei közt szerepel a „Processing face…”, „Writing face string to INI…” és „PersistContactToINI failed…”; a `0x007d5ca6` hívás után `0x007d5cb2` ellenőrzi a visszatérési értéket, hiba esetén `0x007d5cbf` naplóz. A `0x00484820` ugyancsak `.picasa.ini`/`faces`/`FRWriteFaceDataINI` sztringekkel azonosított arc-INI-író útban hívja a helpert. | bináris (`string_xrefs`; Capstone `0x007d5ca6`-`0x007d5cc7`, `0x00485118`) | megerősített a két hívási környezetre |
| A `0x00586e20` törzsében nem azonosítható közvetlen Win32 fájlíró API-hívás; az adatátadás egy feloldatlan virtuális célra történik. A virtuális cél fájlíró volta és az, hogy az adatot azonnal, később vagy csak a profil mentésekor lemezre írja-e, nem következik a helperből. | bináris (`0x00586e20`, a teljes 752 bájtos törzs; virtuális hívás `0x005870de`) | megerősített az itt vizsgált törzs utasításszintű megfigyelésére; a virtuális cél és az időzítés nyitott |

**Eredeti | Nálunk | Teendő.**

| Eredeti | Nálunk (`0.9.248`, a 54.3-ban hivatkozott forrásolvasat) | Teendő |
|---|---|---|
| A kontaktadat `Contacts2`-értékké alakítása több hívási útból elérhető; az arc-feldolgozó és a `faces=` INI-író út is meghívja a segédet. A segéd virtuális callbacket hív, ezért a pontos tartós fájlírási pillanat **NINCS MEG**. | A People Manager központi `contacts.xml` mentése és a mappánkénti `.picasa.ini` frissítése külön PicasaPy-kódút; a forrásrészletek a 54.3 első táblázatában állnak. Ezt a kört nem mértem futásidőben. | J8 kontrollált eredeti Picasa-profil-diff: `contacts.xml`, `backup.xml`, érintett `.picasa.ini` és db3 fájl-hash/időbélyeg/tartalom műveletenként, bezáráskor és újraindítás után. A callback célját csak a vtable-tulajdonos és a `+0x8` slot célfüggvénye alapján nevezd meg; a naplóüzenet önmagában nem bizonyít lemezírást. |

**A két független út.** **A út:** az index `xrefs`- és `string_xrefs`-adata a helper közvetlen hívóit és a `Contacts2`/formátum/arc-feldolgozási szövegeket adja. **B út:** a négy függvény méretére korlátozott Capstone-olvasat megerősíti a helper szakasz- és érték-előállítását, a három közvetlen hívás pontos helyét, valamint a `0x007d55f0` státuszellenőrzését. A két út egyezik abban, hogy a helper kontaktadatot ad át több INI-hez kapcsolódó útból; egyik sem azonosítja a virtuális callback lemezre írásának pillanatát.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a „Persisting contact to INI” napló önmagában közvetlen fájlírást bizonyít. A helper teljes, indexméret szerinti törzsében az adatátadás `call edx` (`0x005870de`); a közvetlen Win32 fájlíró API-hívás nem azonosítható. Ezért a logszöveg nem bizonyít lemezre írást. A cáfolatot a három hívó külön diszasszemblálásával és az indexelt hívó-/sztring-xrefekkel ellenőriztem. A callback vagy egy meghívott helper közvetett, akár azonnali írása ettől még lehetséges, tehát a műveletenkénti időzítés nyitott marad.

**A #5185 „Kész, ha” pontjaihoz.** A 7. ponton belül ez a kör a `Contacts2`-érték előállításának és hívóinak statikus útját pontosította; a műveleti fájlírás és db3-változás ideje továbbra sincs meg, ezért a J8 feltétel nem teljesült. A 8. ponton nincs új lelet: a detektor effektív küszöbe továbbra is **NINCS MEG**, a 54.3/a megszerzési útja érvényes.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (54.3/b: a `0x00586e20` helper hívói, a virtuális átadás és a tartós írás nyitott határa).

### 54.3/c A FaceViewDetector `classifier arr` elemtípusa és a küszöb streamje (2026-10-26)

**Hatókör.** A Ghidra-kimenetet (`2026-10-26-5185-red-weak.txt`) a Red-index RTTI-/xref-adataival és a hash-azonosított helyi Red.dll célzott Capstone-diszasszemblyével vetettem össze. A DLL SHA-256-a `da370693b59d89e7d48646d9617f5f595e371f8e1828cb1aa9f12530a17c8233`; a Red-index riportja Picasa 3.7 telepítést jelöl forrásként. Ez a lelet ezért a vizsgált DLL-re közvetlenül igaz, tiszta Picasa 3.9-es DLL-re csak feltételesen vihető át.

| Állítás | Bizonyíték | Bizonyítottság |
|---|---|---|
| A `FaceViewDetector` mezője a `+0x4c`-nél kezdődő `classifier arr`; a `0x10104290` mezőcímkéje `0x101d50dc`-re hivatkozik, és az array objektum virtuális mentő/betöltő metódusát hívja. A `runOnOneWindow` (`0x10103870`) és az utána meghívott `0x10103670` az array elemeit a `this+0x58` tárolón át, 12 bájtos ObjectRef-elemként éri el; az objektumpointer minden esetben az elem `+8` mezőjéből jön. A `+0x58` tehát az array adatterülete, nem maga a mező kezdete. | bináris (`0x10104290`, `0x10103870`, `0x10103670`, `0x101d50dc`; Capstone; Red-index `rtti`, `string_xrefs`) | megerősített a mezőnévre, elrendezésre és hozzáférési útra |
| A Red `vsi_create` gyára (`0x101033e0`) a ClassId-ból `0x0041a001`-et von ki; a `0x0041a004`-es ág a `0x10107c00` konstruktort hívja. Ez `0x101d5898` vtable-t állít be, amelyet az RTTI `vsi_WeakClassifier`-ként nevez meg. A `classifier arr` elemeinek várt típusát a `vsi_WeakClassifier` adja; a tároló viszont ClassId-alapú ObjectRef-eket tart, ezért a konkrét futásidejű elemeket a betöltött modellstream példányadata dönti el. | bináris (`0x101033e0`, `0x10107c00`, `0x101d5898`); `classids.csv`; Red-index `rtti` | megerősített az ID→típus gyári leképezésre és a várt típusra; feltételes a tényleges streampéldány összes elemére |
| Az `ObjectRef::read(esm_InStream&)` (`0x10063f30`) a streamből kapott ClassId alapján az általános `0x100685a0` betöltőhöz jut. A `0x100685a0` a `0x100681e0` ObjectRef-inicializálót és a `0x10068380` `ObjectFRPtr::load(esm_InStream&)` streambetöltőt hívja. E függvények nem választanak fájlnevet; az `esm_InStream` forrását a fölérendelt hívó adja. | bináris (`0x10063f30`, `0x100685a0`, `0x100681e0`, `0x10068380`; Ghidra-kimenet és célzott Capstone) | megerősített a generikus streamhatárra; az upstream fájlra nem |
| A `vsi_WeakClassifier` loader (`0x10107f20`) a `this+0x1c` címét a `0x1005bb50` float-olvasónak adja (`0x10107f87`-`0x10107f8c`); a mentő `0x10107d70` ugyanazt a mezőt `threshold =` névvel szerializálja. A konstruktor `0.0` kezdőértéke (`0x10107be0`-`0x10107be4`) betöltéskor felülírható, tehát nem az effektív modellküszöb. | bináris (`0x10107f20`, `0x1005bb50`, `0x10107d70`, `0x101d5800`, `0x10107be0`) | megerősített a mező streamből olvasására; az effektív számértékre nem |
| A pontos fájl vagy modellstream, amelyből a FaceViewDetector `classifier arr`-ja ténylegesen feltöltődik, és a `+0x1c` mező futáskor betöltött floatja. | **NINCS MEG.** A Picasa3.exe a `red.cfg`-t hivatkozza (`0x0045f0c0`, `0x00803c80`), de a helyi `red.cfg`-ben a `0x0041a004` és `0x0041a005` objektumfejlécből 0 találat van. A Red.dll `0x10001170` sztringje (`RELprec_442.rlt;CNVprec_442.emd;vrd_104.cfg`) egy `0x10178d00` hívás argumentuma, de ez nem azonosítja a `classifier arr` betöltési útját; e három fájlnév a vizsgált Picasa3-fában nem található. | nyitott; a vizsgált fájlok pontos keresése nem azonosítja a tényleges streamet |

**Eredeti | Nálunk | Teendő.**

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A Red.dll `FaceViewDetector` `classifier arr`-ja ObjectRef-elemeket tartalmaz; a `vsi_WeakClassifier` objektum ClassId-ja `0x0041a004`, a modellstreamből olvasott küszöbmezője `+0x1c`. A konkrét Picasa 3.9 modellstream és annak floatértéke **NINCS MEG**. | A PicasaPy a `face_detection_yunet_2023mar.onnx` modellt használja, egy YuNet `score_threshold=0.9` paraméterrel (`src/picasapy/faces/detector.py:31,42,181,204-208`). Ez egy másik detektor egyetlen pontszámküszöbe; nem azonosítható a Red gyenge osztályozóinak külön streamelt küszöbmezőjével. | A `0.9` értéket ne használd a Red `+0x1c` mező helyettesítőjeként. E statikus bizonyíték nem indokol kódmódosítást; a számszerű paritás csak azonosított Picasa 3.9 Red.dll/model streamből kiolvasott értékkel állítható. |

**A két független út.** **A út:** a 2026-10-26-i Ghidra-dekompiláció a `0x10063f30` általános `ObjectRef::read`-jét, a `0x100685a0` stream-wrapperét és a `0x10104290` osztálymezőit mutatja; a méretre szabott Capstone-olvasat külön megerősíti a `+0x4c`/`+0x58` mezőkapcsolatot, az ObjectRef-elemeket, a ClassId-gyárat és a `+0x1c` float-olvasást. **B út:** a Red-index RTTI/vtable-adata a `0x10104290`-et a FaceViewDetectorhez, a `0x10107f20`/`0x101d5898`-at a WeakClassifierhez köti; a `classifier arr =` sztring-xref, a `classids.csv` és a konstruktor vtable-írása egyezően köti a `0x0041a004` ClassId-t a `vsi_WeakClassifier`-hez. Az utak egyeznek a szerkezeti következtetésben. A konkrét fájl, a betöltött stream ClassId-sorozata és az effektív float nincs ezekkel az utakkal megmérve.

**Cáfoló kísérlet.** Megpróbáltam cáfolni, hogy a `+0x58` maga a gyűjteményobjektum, illetve hogy a `0.0` konstruktorérték az effektív küszöb. A `0x10104290` a `+0x4c` mező objektumán hívja a mentő/betöltő slotot, míg a `0x10103670` és `0x10103870` a `+0x58` adatterületen járja az ObjectRef-eket; ez megcáfolja a két offset azonosítását. A `0x10107f20` `+0x1c` mezőt streamből olvassa a `0x1005bb50` helperrel, az ellenirányú szerializáló pedig `threshold =`-ként címkézi; ez megcáfolja, hogy a `0.0` szükségképpen betöltött érték. A forrásfájlt cáfoló `red.cfg` fejléc-keresés csak azt mutatja, hogy a két pontos bájtminta nincs ebben az egy fájlban; nem bizonyít másik fájlt, ezért nem használtam negatív bizonyítékként.

**Bizonyítottság és határ.** A helyi DLL-ben a mezőút, a gyári ClassId-leképezés és a streamelt `+0x1c` float-olvasás **megerősített**. Az, hogy a tényleges `classifier arr` minden runtime-eleme `vsi_WeakClassifier`, a stream példányadata nélkül **feltételes**; a pontos modellfájl és effektív számérték **NINCS MEG**. A vizsgált DLL eredetjelölése Picasa 3.7, ezért a tiszta Picasa 3.9-re való átvihetősége is **feltételes**. Új, e két függvényre irányuló Ghidra-kérés nem maradt; új kutatási irányt ez a kör nem indított.

**A #5185 „Kész, ha” 8. pontjához.** A Red.dll belső osztály-/mezőútja megvan; a tiszta 3.9-es DLL/model-azonosság, effektív küszöb, felismerésindítási/kihagyási feltétel, bemeneti méret és mért felismerési arány továbbra is nyitott. A 8. pont ezért részben teljesült, a jegy teljes feltétele nem.

**Módosított fájl:** `docs/specs/picasa-arcfelismeres.md` (54.3/a korábbi Ghidra-kéréseinek státusza; új 54.3/c a `classifier arr`, az ObjectRef-streamhatár, a WeakClassifier `+0x1c` mezője és a bizonyítottsági korlátok).

### 54.3/d A `+0x1c` összehasonlító szerepének és a J8 mérőadatának friss ellenőrzése (2026-10-27)

**Eredeti | Nálunk | Teendő.**

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A vizsgált Red.dll `vsi_FaceViewDetector::runOnOneWindow` útjában `0x10103940`-nél a `[ebp+0x58]` címből veszi a gyűjteményadatot; a `0x10103943` a `[base+edx+8]` elemből az aktuális 12 bájtos elem pointerét teszi `ecx`-be. Ez a pointer marad `ecx`, amikor `0x10103c14` a `[ecx+0x1c]` mezőt olvassa. A felhalmozott pontszám betöltése `0x10103c10`, az összehasonlítás `fcompp` (`0x10103c17`), a küszöb alatti ág az addigi elemszámot adja vissza (`0x10103c1e` → `0x10103c43`). A hívó `0x10104769` a visszatérő elemszámot a gyűjtemény teljes darabszámával veti össze, eltérésre a `0x1010476b` visszautasító ágra ugrik. Ez a mező a vizsgált DLL-ben az aktuális array-elem küszöb-összevetésében vesz részt. A mező betöltött számértéke és az, hogy ugyanez a DLL fut-e a tiszta Picasa 3.9-ben: **NINCS MEG**. | A PicasaPy YuNet-detektora `score_threshold=0.9` értéket használ; a `FRRecommendIncludeLimit=0,50` a Picasa külön ajánlási útjához tartozik. Egyik érték sem azonosítható a Red array-elemeinek `+0x1c` mezőjével. | Szerezz tiszta Picasa 3.9 futásból Red.dll-hash-t és a `classifier arr` tényleges streamjét, majd mérd ki a betöltött floatot. A `0.9` és `0,50` értéket ne használd az eredeti mező értékeként. |
| A `contacts.xml`, `.picasa.ini` és db3 műveletenkénti tartós írási időpontja a bináris helper útjából nem következik. | A `meroadat.tar` mind a 15 `.picasa.ini` tagjában (memóriában olvasva, kibontás nélkül) nincs `[Contacts2]`, `faces=`, `ffffffffffffffff` vagy `]facealbum:` jelölő; a taglistában `contacts.xml`, `backup.xml`, db3 és eredeti Picasa-profiltag sincs. Ez az archívum tartalmát írja le, nem az eredeti program viselkedését. | J8: eredeti Picasa-profilban rögzítsd a `contacts.xml`, `backup.xml`, érintett `.picasa.ini` és db3 állapotát névadás/Choose, javaslat elfogadása/elutasítása, mellőzés, személytörlés, kilépés és újraindítás előtt és után. |

**Két független út és bizonyítottság.** **A út:** a hash-azonos DLL célzott Capstone-olvasata a `0x10103940`/`0x10103943` címeken azonosítja az aktuális gyűjteményelemet; a `0x10103c14`-`0x10103c1e` mezőolvasatot/ágat és a hívó `0x10104769` teljes-darabszám-ellenőrzését követi. **B út:** a Ghidra-kimenet a `runOnOneWindow` és a visszaadott darabszám hívói összevetését azonosítja; a Red-index `classifier arr =` xrefje a `+0x4c` mezőhöz, a WeakClassifier gyártója/ClassId-térképe pedig a `vsi_WeakClassifier` típushoz kötődik. Külön mezőút: a `0x10107f20` a `+0x1c` mezőt 4 bájtos stream-olvasónak adja (`0x10107f87`-`0x10107f8c`; a helper: `0x1005bb66`-`0x1005bba0`), a `0x10107d70` szerializáló `threshold =` címkéje ugyanarra a mezőre hivatkozik. Az utak egyeznek a vizsgált DLL lokális array-elemének küszöbszerepében; a stream tényleges példánytípusa, a tiszta 3.9-es DLL-azonosság és a futásidejű érték továbbra sincs bizonyítva.

**Cáfoló kísérlet.** Megpróbáltam a `+0x1c` mezőt a FaceViewDetector saját, állandó mezőjeként értelmezni. A célzott utasításolvasatban az `ecx` a `+0x58` gyűjtemény aktuális elemére áll (`0x10103940`/`0x10103943`), és ezt a `0x10103c14`-ig nem írja felül; a `0x10104769` hívói összevetés pedig a visszaadott átment elemszámot a teljes darabszámmal ellenőrzi. Ez a detector-szintű mező hipotézisét megcáfolja a vizsgált DLL-re. A próbát a Ghidra hívói összevetésével, a `classifier arr =` xref-fel és a WeakClassifier `threshold =` szerializáló útjával ellenőriztem. Külön ellenőriztem a `0,50` `FRRecommendIncludeLimit` és a PicasaPy `0.9` értékét is: egyik sem azonosítható a Red-modell adatfolyamának mezőjével, de ebből nem következik, hogy a futásidejű érték számszerűen eltér tőlük.

**A #5185 „Kész, ha” 7-8. pontjához.** A 7. pont részleges marad: archívumunk nem tartalmazza az eredeti profilkontrollt, a műveletenkénti írási idő és a db3 rekordváltozás **NINCS MEG**; a megszerzés útja a fenti J8. A 8. pont részleges: a helyi DLL összehasonlító mezőjének szerepe megerősített, de a tiszta 3.9-es DLL/hash, a tényleges stream és float, valamint a scan indítása, kihagyásai, bemeneti mérete és mért eredménye **NINCS MEG**; ezekhez J7-es kontrollált eredeti futás és adatkinyerés szükséges. A fennmaradó kérdéshez új Ghidra-kör nem kell: a hiányzó bizonyíték futásidejű adat és profilfelvétel.

**Módosított fájl:** `docs/specs/picasa-arcfelismeres.md` (54.3/d: a gyűjteményelem pointerének és visszautasítási ágának közvetlen címzett útja, a parserrel ellenőrzött `red.cfg`-határ, az archívum kibontás nélküli ellenőrzése és a 7-8. pont nyitott mérései).

### 54.3/e 2026-10-28 - a `+0x1c` segédútja nem adja meg az effektív küszöböt

**Hatókör.** A hashazonos helyi Red.dll `0x10103670` függvényét a Red-indexben megadott 302 bájtos tartományon belül Capstone-nal és `llvm-objdump`-bal olvastam. A teljes `.text`-et nem pásztáztam. A helyi `Picasa3.exe` PE-verziója `3.9.141.259` (SHA-256: `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`); a mellette levő `plugins/Red.dll` SHA-256-a `da370693b59d89e7d48646d9617f5f595e371f8e1828cb1aa9f12530a17c8233`, azonos a Red-index `meta.json` hashével. A Red-index átadási riportja ezt a DLL-t helyi Picasa 3.7 telepítésből származóként azonosítja. A Picasa3.exe verziója és a DLL együttállása nem bizonyítja, hogy ez a DLL töltődött be egy tiszta Picasa 3.9 futásban; a Red.dll PE-erőforrásában nincs `VS_FIXEDFILEINFO`.

| Állítás | Bizonyíték | Bizonyítottság |
|---|---|---|
| A `0x10104290` a Red-index RTTI-jében a `vsi_FaceViewDetector` vtable egyik metódusa. A meglévő Ghidra-kimenet szerint a stream-kezelő függvény mindkét fő ágának végén meghívja a `0x10103670` segédet; ez a függvény a `+0x58` gyűjtemény elemeit járja be, és minden aktuális elem `+0x1c` floatját olvassa. | bináris (`0x10104290`, `0x10103670`; `2026-10-26-5185-red-weak.txt`; Red-index `rtti`, `functions`, `xrefs`) | megerősített a hashazonos DLL hívási és mező-hozzáférési útjára |
| A `0x10103670` az aktuális elem `+0x1c` értékét a `0x101e99d8` címen tárolt nyolc bájttal hasonlítja össze. A bájtok `00 3d 91 60 e4 58 e1 c3`, IEEE-754 binary64-ként `-1.0e19`. A segéd összehasonlításának szemantikai neve ebből nem állapítható meg. | bináris (`0x101036d8`-`0x101036e9`, `0x101e99d8`; Capstone és `llvm-objdump`; nyers konstans dekódolása) | feltételes: a két visszafejtő eszköz egyezik a helyi DLL utasításairól, de a segéd magas szintű célja nincs megfejtve |
| A `RELprec_442.rlt;CNVprec_442.emd;vrd_104.cfg` sztring (`0x101aad94`) `0x10001170`-ből a `0x10178d00` `_strncpy` függvénynek kerül átadásra másolásként (célpuffer, forrás-karakterlánc, hossz). Ez az út önmagában nem bizonyít fájlmegnyitást vagy `classifier arr` betöltést; a célpuffer későbbi felhasználása **NINCS MEG**. | bináris (`0x10001170`-`0x10001189`, `0x10178d00`; Red-index `string_xrefs`, `functions`, `xrefs`; Capstone és `llvm-objdump`) | megerősített a másolási hívásra; a későbbi felhasználás nyitott |
| A `0x10103870` detektor-útja a kiszámított pontszámot közvetlenül az aktuális gyűjteményelem `+0x1c` floatjához hasonlítja (`0x10103c10`-`0x10103c1e`). A `-1.0e19` konstans a külön `0x10103670` segédben áll; nem ez a `0x10103870` összehasonlítás operandusa, és nem mondja meg a streamből betöltött mező értékét. | bináris (`0x10103870`; Ghidra `2026-10-23-sor-279-281-red.txt` és `2026-10-26-2026-10-26-ghidra-sor-282-304-red.txt`; célzott Capstone; `0x10103670`) | megerősített a helyi DLL két külön operandusútjára; az effektív runtime érték nyitott |
| A J8 műveletenkénti `contacts.xml` / `.picasa.ini` / db3-diffhez az elérhető mérőarchívumban nincs eredeti profil. | mérés (`meroadat.tar`: 944 tag, 15 `.picasa.ini`; a taglistában nincs `contacts.xml`, `backup.xml`, db3 vagy eredeti Picasa-profil) | megerősített az archívum tartalmára, nem az eredeti Picasa viselkedésére |

**Eredeti | Nálunk | Teendő.**

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A hashazonos helyi Red.dll `runOnOneWindow` útja a gyűjteményelem(ek) `+0x1c` floatját használja küszöb-összevetéshez; a stream tényleges forrása, a betöltött floatértékek és a tiszta 3.9-es futásban betöltött DLL **NINCS MEG**. A külön segédben szereplő `-1.0e19` konstans nem azonos a detektor összehasonlító operandusával. | A PicasaPy forrásában a YuNet-detektor alapértelmezett `score_threshold` értéke `0.9` (`src/picasapy/faces/detector.py:42,181`); ez külön kódút, forrásolvasat, nem futásidejű mérés és nem helyettesíti a Red.dll mezőjét (54.3/c). | J7: tiszta Picasa 3.9 futásban rögzítsd a tényleges Red.dll hashét és a betöltött modellstreamet/floatértékeket, az indítási és kihagyási feltételekkel, bemeneti mérettel és címkézett képkészlet eredményével. J8: készíts kontrollált eredeti profilon fájl/hash/időbélyeg-diffet a felsorolt névadási, elfogadási/elutasítási, mellőzési, törlési, kilépési és újraindítási műveletekről. |

**A két független út és bizonyítottság.** **A út:** a célzott Capstone-olvasat a Red-indexből vett függvényméreten belül követi a `0x10103670` gyűjteménybejárását, a `+0x1c` olvasást és a `0x101e99d8` hivatkozást; a nyers nyolc bájt IEEE-754 dekódolása adja a konstans pontos értékét. **B út:** a külön `llvm-objdump`-olvasat ugyanezt az utasítássorozatot adja, a Ghidra-kimenet pedig a `0x10104290` stream-kezelő hívási helyét, a Red-index RTTI-je pedig annak `vsi_FaceViewDetector` besorolását ellenőrzi. A két út egyezik a helyi DLL statikus mezőútján; egyik sem azonosít futásidejű fájlforrást vagy betöltött küszöböt. A helyi DLL kódjának állítása megerősített, a tiszta Picasa 3.9 runtime-ra való átvitele és a numerikus küszöb nyitott.

**Cáfoló kísérlet.** Megpróbáltam a `0x101e99d8` `-1.0e19` konstansát az effektív arcfelismerési küszöbnek tekinteni. A `0x10103870` Ghidra- és utasításszintű olvasata a pontszámot az aktuális elem `+0x1c` mezőjéhez hasonlítja; a `-1.0e19` konstans egy külön, a `0x10104290` stream-kezelőből hívott `0x10103670` függvényben szerepel. Ez megcáfolja, hogy a konstans a `runOnOneWindow` közvetlen összehasonlító operandusa volna, de nem adja meg az elem betöltött értékét. A cáfolatot a két visszafejtő eszköz, a Ghidra-kimenet, az RTTI és az indexelt hívási kapcsolat egymástól külön ellenőrizte.

**A modellnév-sztring cáfoló ellenőrzése.** Azt próbáltam megcáfolni, hogy a `0x101aad94`-ben levő `RELprec_442.rlt;CNVprec_442.emd;vrd_104.cfg` sztring közvetlenül azonosítja a betöltött osztályozó-adatfolyamot. A `0x10001170` utasításai a sztringcímet a `0x10178d00` `_strncpy` függvénynek adják át másolásra; a Red-index sztring-xrefje ugyanezt a függvényt és a hívót köti össze. Ez cáfolja, hogy ez a hívás maga volna a fájlbetöltő, de nem zárja ki, hogy a másolt sztring később útvonal- vagy konfigurációs bemenetként szolgál. A célpuffer későbbi olvasója **NINCS MEG**.

**Nyitott.** A `+0x1c` mező tényleges értéke és az azt adó `esm_InStream` fájl-/modellforrása **NINCS MEG**. A meglévő `2026-10-26-5185-red-weak.txt` a `0x10104290` célfüggvény mező-loaderjeit mutatja, de az upstream virtuális hívót és a stream nyitását nem. A pontos következő dekompilálási kérdés:

`Ghidra-kör kell: 0x101d5160 - a vsi_FaceViewDetector vtable 0x10104290 célfüggvényére vezető virtuális hívó és az átadott esm_InStream fájl-/modellforrásának visszakövetése; a meglévő dump a célfüggvényt dekompilálja, a 0x101aad94 sztring útja pedig csak strncpy-másolásig ismert, a stream előállítóját egyik sem azonosítja. [blokkoló]`

J8-hoz az eredeti, vezérelt Colab-profilt kell felvenni; a most ellenőrzött `meroadat.tar` nem tartalmaz hozzá profilt. Így a #5185 7-8. pontja továbbra is részleges.

## 55. #5184, helyi Codex-kutatói kör: a helyi archívum nem dönt N1/N3/N7-ről (2026-10-26)

**Hatókör:** a mérőadat-archívum célzott ellenőrzése és az eddigi bináris-/Colab-leletek összevetése. Az eredeti Picasát ebben a körben nem futtattam; a helyi Wine futtató hiányzik. Az archívumból nem bontottam ki fotókat.

### 55.1 A célzott archívummérés

A `meroadat.tar` taglistája **944** tagot tartalmaz, köztük **15** `.picasa.ini`-t és **1** PNG-t. Csak ezt a 16 tagot bontottam ki a munkafa `.bt/5184-codex/` almappájába. A 15 INI mindegyikében **0** `faces=`, **0** `[Contacts2]`, **0** `]facealbum:` és **0** `ffffffffffffffff` jelölő van. A PNG **358×121 px**, és a képe a PicasaPy „Exportálás” hibaüzenet-ablaka; nem eredeti Picasa-felvétel. Forrás: mérés (`meroadat.tar` taglista, célzott kibontás, jelölőszámlálás, `file` és képi ellenőrzés). A helyi `wine` parancs nem található.

### 55.2 N1, N3 és N7 - eredmény és következő mérés

| Pont | Eredmény | Bizonyíték / mi döntheti el |
|---|---|---|
| N1 - további ismeretlen arc a névvel jelölt fotón | **NYITOTT; eltérés nem bizonyított.** | A `0x0047b020` munkatétel `+0x10` jelzőjének két ága nem köti a jelzőt a fotó névállapotához (53.1); az archívum nem tartalmaz arc-kontrollt. Döntő mérés: ugyanaz a legalább kétarcú eredeti fotó a név hozzárendelése előtt és után, a Név nélküliek listájával és a `faces=` kimenettel. |
| N3 - eredeti felismerési arány, küszöb és képméret | **NYITOTT; az eredeti értékek NINCSENEK MEG.** | A mi `960 px`/`0,9` beállításunk nem eredeti Picasa-adat. A bináris `0,50` értéke a `FRRecommendIncludeLimit` ajánlási határa (`0x0048aab0`, `0x0048e1f0`), nem igazolt Red-detektorküszöb. A Red `0x100057c0` pontszámmaximumot ír ki, a `0x10001570` státuszt kezel; a 53.2 és 54.2 szerinti effektív küszöb, bemeneti WxH és felismerési arány továbbra sincs meg. Döntő mérés: azonos címkézett képkészlet mindkét programban, a Red-nek átadott tényleges mérettel és képenkénti eredménnyel. |
| N7 - kijelölési modell | **Részben lezárt:** a Név nélküliek többes kijelölése igazolt; a People Manager Ctrl/Shift-módja **NYITOTT**. | A `job-180` hat arc Ctrl+A kijelölését mutatja; a `job-186` People Manager-képe egy kijelölt személyt mutat, ami nem dönti el a többes kijelölést (53.3). Döntő mérés: két személy után képkocka az első sor kattintásáról, Ctrl+kattintásról és Shift-kattintásról. |

### 55.3 Független utak és cáfoló próba

- **A út - bináris:** a munkasor és a Red.dll meglévő utasítás-/Ghidra-olvasatai a `picasa-arcfelismeres.md` 53-54. szakaszában vannak. A `0x006cde50` kimenete (20.7) nem azonosít konkrét képméret-argumentumot; a helyi Red.dll pontszám/státusz útja nem azonosít 3.9-es effektív küszöböt sem. Ezek az olvasatok a munkajelző ágát és az ajánlási határt rögzítik, de a kérdezett eredeti futásidejű döntést, képméretet és felismerési arányt nem adják meg.
- **B út - mérőadat:** az archívum taglistája, a 15 INI jelölővizsgálata és az egyetlen PNG képi ellenőrzése nem tartalmaz N1-hez vagy N7-hez eredeti Picasa-állapotot, N3-hoz pedig címkézett eredményeket. A két, egymástól különböző út egyezik abban, hogy N1/N3/N7 viselkedési kérdése helyben továbbra sem dőlt el; ez nem válasz az eredeti program viselkedésére.
- **Cáfoló próba:** megpróbáltam a `0,50` értéket N3 detektorküszöbeként használni. A `0x0048e1f0` fogyasztási útja a `FRRecommendIncludeLimit` mezőként kezeli, és a `0x100057c0`/`0x10001570` Red-út nem ad végső pontszámküszöböt (53.6). Ez cáfolja a `0,50 = Red-detektorküszöb` értelmezést; a Red effektív küszöbe ettől még nyitott.
- **Archívum-cáfolat:** az egyetlen PNG-t eredeti Picasa-felvételnek tekintő feltevést a kép tartalma cáfolja: PicasaPy-exporthiba látható rajta. A `358×121 px` fájlméret külön `file`-mérése is eltér az N8 referenciaként dokumentált `631×351 px` People ablaktól (36.3).

### 55.4 A többi kérdés és fejlesztési következmény

Az N4 eredménye változatlanul **nincs alapértelmezett keret vagy név** (`mérés (job-187)`, 36.3). N5: **nincs személyszintű Ignore; a mellőzés arcszintű** (`mérés (job-222..226)`, 37.10-37.11). N6: a „Delete People Album” után eltűnik a `faces=` sor, a `[Contacts2]` megmarad; a PicasaPy javítása a **#5391** (`mérés (job-222/224)`, 37.10). N8: a referencia a **job-186 24. képe**, a People ablak és egy kijelölt „Teszt Elek” sor (`mérés (job-186)`, 36.3). Ezeket ez a kör nem mérte újra.

**Összesített állapot:** N1, N3 és a People Manager N7-része nyitott; a teljes „Kész, ha” lista ezért nem teljes. Eredeti/PicasaPy-eltérés nincs bizonyítva, tehát nincs teendő a kódban és új fejlesztői jegy sem indokolt. Új kutatási jegy nem szükséges; a döntő lépések az eredeti Picasa futásidejű felvételei/mérései a fenti táblában.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (új 55. szakasz: célzott archívummérés, N1/N3/N7 aktuális állapota és megszerzési út); `docs/specs/00-index.md` (#5184 felvétele a kézzel karbantartott nyitott kérdések listájába).


## 56. #5184, helyi Codex-ellenőrzés: a munkasor-jelző nem bizonyít név szerinti kihagyást (2026-10-26)

**Hatókör.** A 55. szakasz után a N1 munkasor-jelzőjét két külön disassemblerrel, a bináris-index hívási xrefjeivel és az archivált mintával ellenőriztem; N3-hoz a helyi Red.dll küszöbmező-szerializáló útját olvastam újra. Eredeti Picasa-futtatás és People Manager Ctrl/Shift-felvétel nem készült.

### 56.1 N1: a munkasor +0x10 bájtja igazolt; a fotó névállapota nincs hozzákötve

| Állítás | Forrás | Eredmény |
|---|---|---|
| A 0x0047b9f0 az átadott rekord +0x10 bájtját 1-re állítja; a 0x0047baf0 a normál rekordot 0-val építi fel. | bináris (0x0047ba82, 0x0047bb7a) | megerősített: a Capstone-annotált és az llvm-objdump utasításolvasata egyezik |
| A 0x0049de00 a forrás +0x10 bájtját az új munkatétel +0x10 mezőjébe másolja; a 0x0047b020 ezt a mezőt vizsgálja. | bináris (0x0049de46-0x0049de49, 0x0047b031) | megerősített: két külön disassembler azonos eredménye |
| A 0x004987c0 a +0x6c sorfej +4 elemét adja át a 0x0047b020 workernek. | bináris (0x0049892d-0x00498933) | megerősített: az utasításolvasat és a picasa3-index xrefs hívókapcsolata egyezik |
| Nem nulla bitnél a worker a 0x0048bd80 hívása után kész-státusszal visszatér; nulla bitnél a rendes feldolgozási ág folytatódik. | bináris (0x0047b031-0x0047b049) | megerősített a worker vezérlési útjára; nem azonosítja a fotó névállapotát |
| A 0x004985e0 külön másolója forrás +0x08 dwordot ír a kimenet +0x10 dwordjára; ez átfed a worker által tesztelt byte-tal. | bináris (0x004985f3-0x004985f8); xref (0x00425f60, 0x0045a9d0, 0x00484820) | a másoló és a queue közti indirekt adatkapcsolat NINCS MEG; az eltérő közvetlen hívók önmagukban nem zárják ki |
| A jelző a névvel rendelkező fotón maradt másik arcot jelenti-e. | NINCS MEG | az eredeti kétarcú fotó név előtti/utáni futásidejű felvétele kell |

**Két független út.** **A út:** Capstone-annotált, címre szűrt disassembly a két producerben, a 0x0049de00 másolóban és a 0x0047b020 fogyasztóban. **B út:** az eredeti EXE ugyanazon utasításainak címre szűrt llvm-objdump olvasata, kiegészítve a külön SQLite-indexelt hívási xrefekkel. Egyeznek a bájt útján és ágviselkedésén; a fotó névállapotára nem adnak eredményt. A hívási kontextus szintén nem tesz a bitből névjelzőt: a 0x0047baf0 egyik hívója, a 0x00602890 a Preferences FRSuggestionThreshold kulcsot olvassa (alapérték: 0x55), majd ugyanazt a munkasor-producert hívja; a 0x00419150 pedig a #db3 adatbázis-út után hívja a 0x0047b9f0 egyes jelzőjű ágát.

**Cáfoló kísérlet és helyesbítés.** Először azt próbáltam igazolni, hogy a 0x004985e0 nem írhatja a worker +0x10 byte-ját, mert másik közvetlen hívási láncban van. A két disassembler ezt nem cáfolja: a 0x004985f3-0x004985f8 utasítások a forrás +0x08 dwordját a kimenet +0x10 dwordjára másolják, majd a 0x004985f9-0x004985fc a +0x0c → +0x14 dwordot. Az első másolás tehát átfed a worker által tesztelt byte-tal. Az index a 0x004985e0 közvetlen hívójaként 0x00425f60, 0x0045a9d0 és 0x00484820 címeket sorol; ezek egyikét sem köti közvetlen xref a 0x0047b9f0/0x0047baf0/0x0049de00/0x004987c0/0x0047b020 sorlánchoz. Az indirekt adatkapcsolat ettől még nincs kizárva. A korábbi „külön másoló, tehát nem lehet forrás” állítás nem állt meg teljesen; a kapcsolat **feltételes / NINCS MEG**, ezért N1 nyitott marad.

**N1 eredménye:** nyitott. A 0x0047b9f0 és 0x0047baf0 által közvetlenül előállított work-item flag útja és ágvezérlő szerepe igazolt; a 0x004985e0 külön másolójának kimenete átfed a vizsgált bájttal, de a munkasorhoz vezető adatkapcsolata nincs meg. Egyik út sem bizonyítja, hogy a bit a fotó névállapotát jelenti; az eredeti Picasa viselkedése név hozzárendelése előtt és után nincs megmérve.

### 56.2 N3: Red-küszöb, képméret és felismerési arány továbbra sincs

A PicasaPy saját forrása 960 px maximális detektálási méretet és 0,9 YuNet-küszöböt állít be (src/picasapy/faces/detector.py); ezek nem az eredeti Picasa értékei. A helyi EXE PE-verziója 3.9.141.259; a mellette levő Red.dll hash-e da370693b59d89e7d48646d9617f5f595e371f8e1828cb1aa9f12530a17c8233, de a DLL index-forrásjelentése Picasa 3.7-et nevez meg, és a DLL-ben nincs PE verzió-erőforrás. A tiszta Picasa 3.9 Red.dll-azonosság ezért NINCS MEG.

`Mérés (a helyi red.cfg SHA-256 értéke): 916d69fd9a412ea937b49f3b0b1401076193dc9be096b3af71921aeba6f51835.` Az `esm_parse.py` aranykapuja ezt a Red.dll hash-ével együtt elfogadta. Az eszköz README-je szerint a parser a konténereket értelmezi, a modellobjektumok belső payloadját nyersen hagyja, ezért ezzel a konfigurációval az effektív Red-detektorküszöb továbbra is NINCS MEG.

| Állítás | Forrás | Eredmény |
|---|---|---|
| A 0,50 érték a FRRecommendIncludeLimit downstream ajánlási határa, nem bizonyított Red-küszöb. | bináris (0x0048aab0, 0x0048e1f0; 49.1) | megerősített a Picasa EXE fogyasztóágára |
| A Red 0x100057c0 kimeneti pontszámmaximumot állít elő; a 0x10001570 hívó a matcher státuszát kezeli. | bináris (0x100057c0, 0x10001570; Ghidra 2026-10-22-ghidra-sor-158-198.txt és -198-hivo.txt; 54.2) | megerősített a helyi hash-azonosított DLL e két függvényére; nem általános állítás minden Red útvonalról |
| A WeakClassifier 0x10107d70 szerializáló útja a this+0x1c floatot küldi a threshold = konfigurációs mezőbe. | bináris (Red.dll 0x10107d70; llvm-objdump 0x10107dd8-0x10107de1; Ghidra 54.2) | megerősített a helyi DLL szerializáló ágára |
| A 0x10103870 által összevetett +0x1c mező azonos-e a WeakClassifier szerializált mezőjével, és mi az effektív futó érték. | NINCS MEG | a meglévő Ghidra-kérés 53.5-ben szerepel; a Red objektumok közti adatút-azonosság és runtime-érték nyitott |
| Az eredeti Red bemeneti WxH-ja és az eredeti felismerési arány ugyanazon címkézett képkészleten. | NINCS MEG | mindkét program futtatása és képenkénti eredményrögzítés kell |

**Két független út és cáfoló próba.** **A út:** a 0x0048e1f0 fogyasztó a 0,50 mezőt ajánlásba-vételi határként használja, a meglévő Red Ghidra-olvasatok pedig a 0x100057c0 maximum- és a 0x10001570 státusz-szerepét mutatják. **B út:** a helyi binárisok címre szűrt utasításolvasata és az indexelt fogyasztói/hívási adatok ugyanezt erősítik; az llvm-objdump újra megmutatja a Red 0x10107d70 konfigurációs mező-szerializálását. Megpróbáltam a 0,50 értéket Red detektorküszöbként értelmezni. A Picasa fogyasztója ajánlási határként azonosítja, a vizsgált Red matcher és közvetlen hívó pedig nem végez végső küszöb-összevetést. A két külön modul útja ellenőrzi a cáfolatot, de más, még nem vizsgált Red callback létezését nem zárja ki.

**N3 eredménye:** nyitott. Red effektív küszöb, tényleges bemeneti WxH és összehasonlítható felismerési arány NINCS MEG.

### 56.3 N7: a People Manager Ctrl/Shift-módja nyitott

A contactmgr.fen contacts listáján nincs kijelölési módot rögzítő attribútum; a 0x007b9630 handler egy aktuális sort tároló indexet frissít. A job-186 referencia egy személyt mutat kijelölve, de Ctrl/Shift-műveletet nem tartalmaz. A Név nélküliek többes kijelölését a job-180 felvétel igazolja, ez azonban nem bizonyítja a People Manager listájának kijelölési módját.

| Állítás | Forrás | Eredmény |
|---|---|---|
| Név nélküliek több arcának együttes kijelölése | mérés (job-180; 53.3) | megerősített a Név nélküliek nézetére |
| People Managerben több személy kijelölhető-e Ctrl/Shift használatával | NINCS MEG | két személyes eredeti Picasa-felvétel kell: sor-kattintás, Ctrl+kattintás, Shift-kattintás |

**N7 eredménye:** részben nyitott; a People Manager többes kijelölési modelljét futásidejű felvétel dönti el.

### 56.4 A többi „Kész, ha” pont változatlan

| Pont | Eredmény | Bizonyíték |
|---|---|---|
| N4 - keret és név alapértelmezett láthatósága | ✅ | mérés (job-187; 36.3): a megnevezett arcon alapból sem keret, sem név |
| N5 - személyszintű mellőzés | ✅ | mérés (job-222..226; 37.10-37.11): személyszintű Ignore nincs, a mellőzés arcszintű |
| N6 - személy törlése és az arcok hatása | ✅ | mérés (job-222/224; 37.10): a faces sorok törlődnek, a Contacts2 megmarad; a PicasaPy-javítás #5391 |
| N8 - People Manager referencia-kép | ✅ | mérés (job-186, 24. kép; 36.3) |

Ezeket a felvételeket nem ismételtem meg.

### 56.5 Független újralevezetés: a 0x004985e0 kimenete átfed a vizsgált bájttal

A friss kontextusú, specet nem látó bináris-újralevezetés egyezett a közvetlen work-item lánccal: a 0x0047b9f0/0x0047baf0 1/0 értéket állít elő, a 0x0049de00 byte-szinten másol, a 0x004987c0 pedig a 0x0047b020-nak adja át az elemet. A worker 0x0047b020 string-xrefjei a Preferences és FRAddSuggesetions beállításnevek; a +0x10=1 ág még e beállítás olvasása előtt tér vissza a 0x0048bd80 útvonalon. A 0x00419150 hívó a #db3 adatbázis- és időzítési út után hívja a 0x0047b9f0-t. Ezek nem mutatnak fotónév-olvasást.

A független újralevezetés helyesbítette a 0x004985e0 elvetését: ez a másoló a kimenet +0x10 dwordját is írja. Az indexelt közvetlen hívók külön útvonalat mutatnak, de nem zárják ki az indirekt adatfolyamot. Ezért a +0x10 forráskapcsolat az 56.1 táblázatban feltételesként marad; N1 névállapot-kérdése nyitott. A két út a munkasor-jelző ismert mechanikájában egyezik; a további másoló adatútjának teljességében eltérés marad.

### 56.6 A #5184 „Kész, ha” pontjai és következmény

| Kérdés | Állapot | Bizonyíték |
|---|---|---|
| N1: névvel rendelkező fotón talál-e az eredeti további ismeretlen arcot | ⛔ | a munkasor zászlóútja megvan, de névállapothoz nem kötött; eredeti kétarcú, név előtti/utáni felvétel kell |
| N3: felismerési arány és küszöb a 960 px / 0,9 PicasaPy-beállításhoz képest | ⛔ | eredeti Red effektív küszöb, bemeneti WxH és címkézett arány NINCS MEG |
| N4: alapértelmezett keret és név | ✅ | job-187 (36.3) |
| N5: személyszintű mellőzés | ✅ | job-222..226 (37.10-37.11) |
| N6: személy törlésének útja és hatása | ✅ | job-222/224 (37.10), javítás #5391 |
| N7: People Manager és Név nélküliek kijelölési modellje | ⛔ | Név nélküliek többes kijelölése job-180-nal igazolt; People Manager Ctrl/Shift-felvétel NINCS MEG |
| N8: People Manager referencia-kép | ✅ | job-186, 24. kép (36.3) |

**Következtetés és fejlesztési döntés:** N1, N3 és a People Manager N7-része nyitva marad; PicasaPy-eltérés nem bizonyított. Nincs megvalósításra indokolt fejlesztői lista vagy új kutatási kérdés. A feloldáshoz N1 név előtti/utáni kétarcú eredeti felvétel, N3 azonos címkézett képkészletű futtatás és Red WxH/küszöb-rögzítés, N7 pedig a People Manager kattintás/Ctrl/Shift képkockái kellenek. Az N3 meglévő Ghidra-kérése 53.5-ben marad nyitva; ezt ebben a körben nem duplikáltam.

**Kész jegytörzs-kiegészítés:** „A spec 56. szakasza rögzíti az új helyi ellenőrzést. N4, N5, N6 és N8 korábbi eredeti felvételekkel lezárt. N1 munkasor-jelzőjének útja ismert, de a fotó névállapotával való kapcsolata és a névvel ellátott kétarcú fotó eredménye nincs meg. N3 esetén a 0,50 ajánlási határ nem Red-küszöb; a Red effektív küszöbe, bemeneti WxH-ja és címkézett felismerési aránya nyitott. N7 People Manager Ctrl/Shift-kijelölése nyitott; a Név nélküliek többes kijelölését a job-180 igazolja. PicasaPy-eltérés nem bizonyított, ezért fejlesztői feladat nem indokolt. A lezáráshoz N1 név előtti/utáni kétarcú felvétel, N3 azonos címkézett adaton futtatás tényleges Red-bemeneti WxH-val és küszöbrögzítéssel, N7 pedig People Manager kattintás/Ctrl/Shift képkockák kellenek.”

**Új kutatási jegyjavaslat:** nincs; a még nyitott pontok ugyanennek a #5184 feladatnak a szükséges eredeti Picasa-felvételei.

**Módosított fájl:** docs/specs/picasa-arcfelismeres.md (56. szakasz: N1 zászlóút-korrekció és cáfolat, N3 helyi Red.dll-ellenőrzés, N7 runtime-nyitottság, pontról pontra a teljesültség).

## 57. #5184, 2026-10-27: az archívum ismételt leltára nem ad N1/N3/N7-kontrollt

**Hatókör.** A mérőarchívum taglistáját, a dokumentum- és INI-tagokat, az egyetlen PNG-t, valamint a korábban feltárt címek Ghidra-kimeneteit ellenőriztem. A JPG/RAW-képeket és a NAS-t nem olvastam; az eredeti Picasát nem futtattam, új Colab-feladatot nem adtam fel.

### 57.1 A mérőarchívum tartalma

| Állítás | Forrás | Eredmény |
|---|---|---|
| Az archívum 944 tagja 926 fájlra és 18 könyvtárra oszlik; a fájlok között 15 INI, 5 TXT, 4 CSV, 900 JPG, 1 PNG és 1 RAW van. | mérés (`meroadat.tar` teljes taglistája) | pontos tag- és kiterjesztésszám |
| A 15 INI-ben `faces=`, `[Contacts2]`, `]facealbum:` és `ffffffffffffffff` előfordulása egyaránt 0. | mérés (a 15 INI célzott kibontása és jelölőszámlálása) | nem található névvel/arcokkal rögzített Picasa-kontroll |
| Az 5 TXT és 4 CSV egyike sem tartalmaz arc-/személycímkézést; a CSV-k fejlécében effekt, fájl, lánc és csúszka-adatok állnak. | mérés (célzott TXT/CSV-sorvizsgálat) | nem található címkézett felismerési adatkészlet |
| Az egyetlen PNG mérete 358×121; egy PicasaPy „Exportálás” hibaablakot mutat. | mérés (PNG-fájlméret és képi ellenőrzés) | nem eredeti Picasa-felvétel, ezért N7-re nem kontroll |

**A JPG-kről nem következtetek arctartalomra.** Az archívumban lévő képek nem adnak címkézett, azonos Picasa/PicasaPy futtatásokhoz kötött eredményt; önmagukban nem használhatók N1 vagy N3 döntésére.

### 57.2 N1, N3 és N7 állapota

| Pont | Eredmény | Bizonyíték / hiányzó mérés |
|---|---|---|
| N1: a névvel rendelkező képen talál-e az eredeti további ismeretlen arcot | ⛔ Nyitott | A `0x0047b020` munkasor-jelző útja ismert (56.1), de a fotó névállapotához nincs kötve. Az archívum nem ad `faces=` kontrollt. Ugyanazon legalább kétarcú eredeti fotó név előtti és utáni felvétele kell, Név nélküliek-listával és INI-kimenettel. |
| N3: eredeti arány és Red-küszöb a 960 px / 0,9 YuNet-beállításhoz képest | ⛔ Nyitott | Az archívumban nincs címkézett mérőkészlet. A helyi Red.dll `+0x1c` mezőútja (54.3/c, 54.3/d) nem azonosítja a tiszta Picasa 3.9 tényleges DLL-jét, betöltött floatját, bemeneti WxH-ját vagy azonos címkézett mintán mért arányát. Ezekhez eredeti futás és azonos készletű PicasaPy-mérés kell. |
| N7: People Manager többes kijelölése | ⛔ Részben nyitott | A korábbi egy személyes People Manager-felvétel nem bizonyít Ctrl/Shift-viselkedést; az archívum egyetlen PNG-je PicasaPy-hibaablak. Két személyes eredeti felvétel kell a sima sor-kattintás, Ctrl+kattintás és Shift+kattintás után. A Név nélküliek `job-180` többes kijelölése ettől külön, lezárt viselkedés. |

**Két független út.** **A út:** a bináris és a már meglévő Ghidra-olvasatok az N1 munkasor-vezérlését, az N3 Red-pontszám/küszöb-mezők különbségét és az N7 aktuális sorindexét írják le; egyik sem rögzíti az eredeti program kérdezett, felhasználói futásidejű kimenetét. **B út:** a mérőarchívum INI-/CSV-/TXT-leltára és az egyetlen PNG közvetlen ellenőrzése nem tartalmazza a hiányzó név előtti/utáni kontrollt, címkézett összehasonlító készletet vagy két személyes kiválasztási sorozatot. Az utak abban egyeznek, hogy a helyi adatokkal egyik kérdezett viselkedés sem dőlt el.

**Cáfoló kísérlet.** Azt próbáltam megcáfolni, hogy az archívum alkalmatlan a nyitott pontok eldöntésére: végigszámoltam minden tagot, kibontottam az összes INI/TXT/CSV dokumentumot és az egyetlen PNG-t is. Az INI-jelölők mind 0-k, a dokumentumokban nincs felismerési címkézés, a PNG pedig PicasaPy hibaablak. Ez a próba nem talált felhasználható kontrollt. A 900 JPG-ről nem állítom, hogy arcmentesek; azt állítom, hogy nincs hozzájuk igazolt eredeti kimenet vagy címkézés.

**Ghidra-nyitott.** A korábbi §53.5 kérés `0x10107d70` címére a helyi Ghidra-tárban továbbra sincs kimenet; a `0x10103870` és a `0x10107f20` kimenete megvan, de külön kezeli a detektori összevetést és a `WeakClassifier` mezőjét. A megmaradt statikus kérdés: `Ghidra-kör kell: 0x10107d70 - állapítsa meg, hogy a FaceViewDetector által bejárt gyűjtemény `+0x1c` mezője valóban a vsi_WeakClassifier modellstreamből betöltött threshold mező-e, a betöltő út és a dinamikus elemtípus követésével.` Ez nem adja meg a futáskor ténylegesen használt értéket vagy a felismerési arányt; a #5184 N3 lezárásához a runtime-mérés ettől függetlenül szükséges. Azonos címre új kérést ebben a körben nem indítottam.

**Következtetés és megvalósítás.** N1, N3 és N7 People Manager-része nyitott; N4, N5, N6 és N8 az előző felvételekkel lezárt (56.4). Eredeti/PicasaPy-eltérés nincs bizonyítva, ezért fejlesztői teendő és új kutatási jegy nem indokolt. A feloldás a fenti három futásidejű felvétel/mérés; ez a session a GitHub-alapú Colab-feladatfeladást nem használta.

**Módosított fájl:** `docs/specs/picasa-arcfelismeres.md` (57. szakasz: a 2026-10-27-i, célzott archívum- és Ghidra-leltár, a három nyitott pont bizonyítékhatára és megszerzési út).

## 58. #5184 N7: a People Manager listája egyszeres kijelölésű (felvétel, 2026-10-27)

**Felvétel:** picasa-colab-jobs job-325 (az előző, job-227 nem mérte a kérdést: az első név utáni Enter az ismeretlen névre nyíló People névjegyablakot hozta fel, és a lépéssor abban ragadt). A javított lépéssor két arcot nevez el (`Teszt Elek`, `Masik Ember`) a New Person, majd OK úton, megnyitja az Eszközök ▸ People Manager ablakot, és a listán sorban: első sor kattintás, második sor Ctrl-kattintás, első sor kattintás, második sor Shift-kattintás.

**Eredmény (33-41. kép):**

| lépés | kijelölt sor |
|---|---|
| kattintás a `Masik Ember` sorra | `Masik Ember` |
| Ctrl-kattintás a `Teszt Elek` sorra | csak `Teszt Elek` (az első kijelölése megszűnik) |
| kattintás a `Masik Ember` sorra | `Masik Ember` |
| Shift-kattintás a `Teszt Elek` sorra | csak `Teszt Elek` |

A jobb oldali Name mező mindig az épp kijelölt személy nevét mutatja. **A People Manager listája egyszeres kijelölésű: a Ctrl és a Shift nem bővíti a kijelölést.** (A Név nélküliek nézet csempéinek többes kijelölése ettől független, azt a job-180 igazolja.)

**PicasaPy:** a `PeopleManagerDialog.qml` egyetlen kijelölt kulcsot tart (`selectedKey`), a lista `currentIndex`-szel jelöl; ez egyezik az eredetivel. **N7 lezárva, eltérés nincs.**

## 59. #5184, 2026-10-28: N1 és N3 továbbra is futásidejű mérésre vár

**Vizsgálati határ.** A helyi `meroadat.tar` fejléc-leltára 926 fájlt mutatott: 15 INI, 5 TXT, 4 CSV, 900 JPG, 1 PNG és 1 RAW. Csak a 24 INI/TXT/CSV dokumentumtagot bontottam ki a munkafa `.bt/5184-meroadat/` könyvtárába; a JPG-ket nem bontottam ki és nem néztem meg. A 15 INI-ben a `faces=`, `]facealbum:`, `ffffffffffffffff` és `[Contacts2]` jelölők előfordulása egyaránt 0. Az öt TXT-ben és négy CSV-ben nincs arc-/személy-/Red-/YuNet-címkézés. Két `felismeri` szövegtalálat a mérőképek szerkesztési beállításainak Picasa általi felismeréséről szól, nem arcfelismerésről. Ez az archívum címkézett kontroll hiányát igazolja, nem azt, hogy a képek arctalanok. NAS-t nem olvastam.

### 59.1 N1: a munkasor-jelző nem dönti el a fotó névállapotát

| Állítás | Forrás | Eredmény |
|---|---|---|
| A `0x0047b020` a munkatétel `+0x10` byte-ját teszteli; nem nulla értéknél a `0x0048bd80` után visszatér. | bináris (`0x0047b020`, célzott Capstone; indexelt hívó `0x004987c0`) | megerősített a munkafüggvény ágára |
| A `0x0049de00` a forrás `+0x10` byte-ját az új sorfej `+0x14` mezőjébe másolja; a sorfej `+0x04`-től induló munkatétel-adatához képest ez `+0x10`. | bináris (`0x0049de00`, célzott Capstone; indexelt hívók `0x0047b9f0`, `0x0047baf0`) | megerősített a másolási útjára |
| A `0x004985e0` a forrás `+0x08` dwordját a kimenet `+0x10` dwordjára másolja; ez átfed a worker által vizsgált byte-tal. Az indexelt közvetlen hívók `0x00425f60`, `0x0045a9d0`, `0x00484820`. | bináris (`0x004985e0`, célzott Capstone; `xrefs`) | megerősített az átfedésre; a queue-hoz vezető indirekt adatkapcsolat nincs meg |
| A jelző jelenti-e, hogy egy névvel ellátott fotón további ismeretlen arc maradt. | NINCS MEG | a kétarcú eredeti fotó név előtti és utáni futásidejű felvétele kell |

**N1 eredménye: nyitott.** A bináris ismert részútja a munkatétel flagjét és ágát mutatja, de a flag fotónévhez kötése nincs bizonyítva. A helyi archívum nem ad névvel/arcokkal rögzített kontrollt. A következő méréshez ugyanazt a legalább kétarcú képet kell az eredetiben felvenni egy arc elnevezése előtt és után, a Név nélküliek listájával és a `.picasa.ini` érintett szakaszával.

### 59.2 N3: az effektív Red-küszöb, bemeneti méret és összehasonlítható arány nincs meg

| Állítás | Forrás | Eredmény |
|---|---|---|
| A helyi `Picasa3.exe` PE-verziója `3.9.141.259`. | bináris (PE `VS_FIXEDFILEINFO`; SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`) | pontos helyi fájlazonosság |
| A mellette lévő `Red.dll` SHA-256-a `da370693b59d89e7d48646d9617f5f595e371f8e1828cb1aa9f12530a17c8233`; nincs PE fájlverzió-erőforrása, a meglévő forrásjelentése Picasa 3.7-et nevez meg. | bináris (`Red.dll`, PE + SHA-256; §54.2-54.3/c) | megerősített erre a helyi fájlra; nem bizonyítja a tiszta 3.9-es runtime DLL-jét |
| A `0x10103870` a classifier-array aktuális elemének `+0x1c` mezőjével vet össze; a `vsi_WeakClassifier` `0x10107f20` streamből olvassa a saját `+0x1c` floatját, a `0x10107d70` ezt a `0x101d5800` `threshold =` sztringgel szerializálja. A két adatút kapcsolata és a betöltött érték nincs meg. | bináris (`0x10103870`, `0x10107f20`, `0x10107d70`, `0x101d5800`; Capstone/Ghidra/llvm-objdump §54.2-54.3/d) | a helyi DLL mezőútjai megerősítettek; az objektum- és adatfolyam-kapcsolat és az érték nyitott |
| A helyi `red.cfg` SHA-256-a `916d69fd9a412ea937b49f3b0b1401076193dc9be096b3af71921aeba6f51835`; az ismert parser ebből nem állítja elő a keresett osztályozó-adatfolyam példányt. | bináris adatfájl (SHA-256; §54.3/c) | a helyi fájlazonosság megerősített; a tényleges Picasa 3.9 modellstream NINCS MEG |
| Az eredeti Red ténylegesen használt küszöbe, detektor-bemenetének WxH-ja és az azonos címkézett képkészleten mért felismerési aránya. | NINCS MEG | tiszta Picasa 3.9 futás, Red.dll-azonosság és képenként rögzített Picasa/PicasaPy eredmény kell |

A Picasa EXE `FRRecommendIncludeLimit=0,50` értéke a javaslatba-vételhez tartozik, nem bizonyított Red-detektorküszöb (§54.2). A PicasaPy `960 px / 0,9 YuNet` beállítása külön detektorhoz tartozik (§56.2); egyikből sem következtetek az eredeti küszöbére vagy felismerési arányára.

**N3 eredménye: nyitott.** A 2026-10-28-i helyi binárisazonosság- és célzott diszasszemblálás nem adja meg a runtime értéket vagy az arányt. A `0x006cde50` címre szűrt olvasata a képrekord méretmezőinek ellenőrzése után indirekt `[esi+0x44]` hívást ad át; Red-küszöböt vagy futásidejű eredményt ez a függvény nem szolgáltat.

### 59.3 Független utak és cáfoló kísérlet

**A út - bináris.** A Picasa EXE célzott Capstone-olvasata és az SQLite pozitív hívási xrefjei megerősítik az N1 munkasor-részutat; a Red.dll Ghidra-/Capstone-olvasatai azonosítják a helyi osztályozó-mező és a `threshold`-szerializálás külön útját. Egyik sem ad fotónév szerinti N1-viselkedést, tényleges 3.9-es Red-modellstreamet vagy címkézett arányt.

**B út - mérőadat.** Az archívum összes nem képi dokumentumtagjának közvetlen ellenőrzése nem talált arc-/személy-/detektor-címkézést, `faces=` sort vagy `[Contacts2]` kontrollt. Ez külön, futásidejű kimenetektől függetlenül igazolja, hogy a helyi mérőarchívum nem dönt N1/N3-ról. A két út abban egyezik, hogy a rendelkezésre álló helyi anyag nem határozza meg a kérdezett runtime eredményt; viselkedési eredményt egyikből sem állítok.

**Cáfoló kísérlet.** Megpróbáltam megcáfolni, hogy a helyi mérőadat nem tartalmaz megfelelő kontrollt: a tar összes INI/TXT/CSV tagját kibontottam a `.bt` alá, majd célzottan kerestem az arc/személy jelölőket és címkézést. A 15 INI négy jelölője 0 találatot adott; a TXT-kben talált két `felismeri` előfordulás teljes mondatát ellenőriztem, mindkettő szerkesztési beállítások mappamegnyitáskor történő Picasa-felismeréséről szólt, nem arcfelismerésről. A cáfoló eredményt ugyanazzal a mércével ellenőriztem a tagkiterjesztés-leltáron és az egyedi dokumentumtartalmakon. A JPG-ket nem vizsgáltam, ezért nem állítom, hogy azok arctalanok; címkézett eredeti/PicasaPy-kimenet nélkül viszont N3-arány nem számolható.

### 59.4 A #5184 „Kész, ha” pontjainak állapota

| Pont | Állapot | Bizonyíték |
|---|---|---|
| N1 - további ismeretlen arc megtalálása névvel ellátott fotón | ⛔ Nyitott | §59.1; eredeti kétarcú fotó név előtti/utáni felvétele hiányzik |
| N3 - eredeti felismerési arány és Red-küszöb a 960 px / 0,9 YuNet-beállításhoz képest | ⛔ Nyitott | §59.2; effektív Red-érték, bemeneti WxH és azonos címkézett mérés NINCS MEG |
| N4 - alapból látszó keret és név | ✅ | mérés (job-187; §36.3) |
| N5 - személyszintű mellőzés és hatása | ✅ | mérés (job-222..226; §37.10-37.11) |
| N6 - személy törlésének útja és hatása az arcokra | ✅ | mérés (job-222/224; §37.10); PicasaPy-javítás #5391 |
| N7 - People Manager/Név nélküliek kijelölési modellje | ✅ | People Manager egyszeres kijelölése (job-325; §58); Név nélküliek többes kijelölése (job-180; §53.3) |
| N8 - People Manager referencia-kép | ✅ | mérés (job-186, 24. kép; §36.3) |

**Következtetés és fejlesztési döntés.** N4-N8 mérési/bizonyítéki pontjai lezártak; N1 és N3 azért marad nyitva, mert a helyi bináris nem adja meg a futásidejű kimenetet, a helyi archívumban pedig nincs hozzá címkézett kontroll. PicasaPy-eltérés nincs bizonyítva, ezért most nincs indokolt fejlesztői lista és új kutatási jegy. N1-hez a kétarcú név előtti/utáni eredeti felvétel; N3-hoz tiszta Picasa 3.9 Red.dll-hash, az effektív streamelt küszöb és a detektor tényleges bemeneti mérete, valamint ugyanazon címkézett képkészlet képenkénti Picasa/PicasaPy eredménye szükséges.

**Meglévő, nem duplikált statikus nyitott tétel:** `Ghidra-kör kell: 0x10107d70 - a FaceViewDetector classifier-array aktuális elemének +0x1c mezőjét kösse a vsi_WeakClassifier modellstreamből betöltött threshold mezőhöz, a betöltő út és dinamikus elemtípus követésével [blokkoló]`. A feladat már az 57. szakaszban szerepel; új kört nem indítottam. Ez önmagában sem adja meg a futáskor használt értéket vagy a felismerési arányt.

**Módosított fájlok:** `docs/specs/picasa-arcfelismeres.md` (59. szakasz: N1/N3 helyi bizonyítékhatárai, független utak, cáfoló próba és pontonkénti állapot); `docs/specs/00-index.md` (#5184 nyitott pontjainak frissítése, N7 lezárásával).
