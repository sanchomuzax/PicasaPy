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
job-177, job-179, job-180, job-183 és job-207 leírásai; a job-180, job-183 és job-207
képernyőképeit közvetlenül megnéztük. A job-208 (J1) és job-209 képkockáit nem
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
| „Learn more...” gomb az üdvözlőablakban | Az eredetiben a gomb alsó szélére kattintva (`job-175`), majd a közepére kattintva (`job-177`) a felvételen semmi nem változik: új ablak nem nyílik, az üdvözlőablak nyitva marad. `job-175` szerint 15 mp-ig a Picasán belül nem nyílik ablak. A Colab-gépen nincs böngésző, ezért a megnyitott cím a felvételből nem olvasható ki (`job-177`). | A PicasaPy-ban a gombnak most nincs kezelője (`job-175`). | Nyitott: a cím a binárisból olvasandó ki (19.1, 6. pont). A jegykommentek „5. kérdés” néven hivatkoznak rá, de a 19.1 listában az 5. pont a csempe-sorrend, ezért a címet új, 6. pontként vettük fel. Kész, ha a gomb kezelője és a megnyitott cím bináris címmel rögzítve van. |
| Csempék, mezők, X, méret és sorrend | Csoportosított nézetben álló arc-kivágások jelennek meg; a job-163 4. és 8. képe soronként öt csempét mutat, mindegyik alatt saját **„Add a name”** mezővel, a csempe jobb felső sarkában kis X-szel. A komment csak közelítő csempeméretet rögzít, ezért a pontos pixelméret **NINCS MEG**. A pontos arcbélyeg-sorrend és a felvételen látható csoporthatárok nincsenek leírva a kommentben: **NINCS MEG**. A job-208 (9. kép) ugyanazt az öt oszlopos elrendezést adja, hat egyarcú csoporttal; csoporthatár ilyen mintán nem látszik, ahhoz többarcú csoport kell (19.1, 5. pont). | A `face_scan_controller.py:812-858` az arc-csoportokat csoportazonosító szerint növekvően, a még nem csoportosított elemeket a végén adja vissza; összecsukva csak csoportonkénti előnézetet ad. A `UnnamedFacesView.qml:355-410` 194 × 198-as rácscellát és 146 × 172-es arckivágást állít be; a `UnnamedFacesView.qml:482-508` minden archoz saját, 172 px széles „Add a name” mezőt ad. A csempe X-e a `UnnamedFacesView.qml:417-440` sorokban van. | A csoportosított alapállapot és az egyedi mező/X felvétellel igazolt. Ne vegyük át a közelítő pixelméretet pontos adatként. A Picasa pontos csempesorrendjéhez és csoporthatáraihoz külön képkocka-leírás kell. |
| Fejlécmező és a csempe névmezője | A binárisban a **fejléc** `addname` parancsa a jobb fiók PeoplePaneljéhez jut (`0x00602970`), amely ott `headerautocomplete` és `header_editbox` mezőt hoz létre (`0x00640670`, `peoplepanel_text.tre`). Ez a panelmező útja. A Név nélküliek **csempéjének** saját „Add a name” mezője külön, élő úttal igazolt (`job-163`, 4. és 8. kép; `job-66`). | A Név nélküliek csempéjén saját `TextField` van (`UnnamedFacesView.qml:482-508`); a jobb oldali People panel sormezője külön komponens (`PeoplePanelRow.qml:149-166`). A job-167 útvonalon a csempe mezője Enterre mindig People ablakot kér (`Main.qml:3690-3692`; `PeoplePanel.qml:192-210`). A jobb fiók meglévő névre történő Enter-kezelése ettől eltér (#5199; `PeoplePanel.qml:192-205`). | A „névmező inline panelmező” állítás csak a fejléc `header_editbox` mezőjére vonatkozik; a Név nélküliek csempéjének saját mezője van. A két út ne legyen összemosva. |
| Új név, People ablak és tárolás | A csempe mezőjébe írt **„Teszt Elek”** után Enterre **„People”** ablak nyílik. A Search mezőbe a név előre be van írva és ki van jelölve; a névlista üres, a **„Delete Person”** és **„OK”** tiltott, a **„New Person”** aktív. Jobbra „Name:” és „Email(s):” mező, szürke „Sync Face Tags with Web Albums” jelölő és „Revert”; alul „Manage Online Contacts”, „Refresh Contacts”, „OK”, „Cancel” (`job-163`, 14-19. kép). Az új személy OK-ja után a bal sávban `People (2)`, `Unnamed (5)`, `Teszt Elek (1)` látszik (`job-167`, 18. kép). A `.picasa.ini`-ben `[Contacts2]` alatt `<azonosító>=Teszt Elek;;`, a fotó szakaszában `faces=rect64(…),<azonosító>` szerepel (`job-66`; `job-167`, 18. kép). A job-66 helyesbítése szerint ez is a csempe-mező útja. A job-213 (a futás végén) ugyanezt a szerkezetet mutatja két fotóval: a `[Contacts2]` alatt egy sor, `3c067b829137b19=Teszt Elek;;`, és mindkét fotó `faces=` sora ugyanarra az azonosítóra mutat. Az azonosító 15 jegyű (32. szakasz). | A csempe Enter-kezelője kiüríti a mezőt és jelzi a beírt arcot/nevet (`UnnamedFacesView.qml:501-508`); a `Main.qml:3690-3692` ezt People ablakra küldi. A `PeopleManagerDialog.qml:53-98` előtölti a Search mezőt, meglévő találatnál kiválasztja a kontaktot; a `PeopleManagerDialog.qml:146-170` kezeli a „New Person” műveletet; a `PeopleManagerDialog.qml:241-289, 299-380, 381-473, 485-510` adja az OK/Choose útját, a kereső/listát, a névjegymezőket és az alsó gombokat, majd menti és a kijelölt arcra alkalmazza. A `face_scan_controller.py:861-923` a sikeres arcot megnevezettként rögzíti, frissíti a mappát és az arcszámot; a `faces_helper.py:265-295` az érintett `.picasa.ini`-t írja. | Az új név útja és eredménye a job-163/167 felvételi jegyzeteiben szerepel. A `[Contacts2]` és `faces=` adatot a job-66 ugyanebből a csempe-mezőből mérte; ez nem másik felületi útvonal. |
| Meglévő név, javaslatlista, Choose és Escape | A mezőbe írt `Tes` alatt javaslatlista jelenik meg arcképpel és **„Teszt Elek”** névvel (`job-167`, 22. kép). A teljes név Enterre People ablakot nyit, a `Teszt Elek` személy kijelölve, „1 Photo in Picasa” adatsorral, **„Choose”** gombbal (`job-167`, 26-30. kép). A felvétel nem kattintott a Choose-ra, ezért az arc a Név nélküliek között maradt. Az ismeretlen `Valami` keresés üres listát és Name mezőt, tiltott OK-t ad; Escape bezárja az ablakot változtatás nélkül (`job-167`, 32-34. kép). | A csempe mező részleges szövegre a névjegyek között kis-nagybetűtől független részsztringet keres; a felugró listában kép és név jelenik meg (`UnnamedFacesView.qml:371-385, 512-589`). A csempe Enter útja meglévő névnél is People ablakot nyit, a meglévő kontakt kiválasztásával és **Choose** gombbal (#5192; `PeoplePanel.qml:192-210`; `PeopleManagerDialog.qml:82-93, 499-505`). A listabeli javaslat-elemre kattintáshoz nincs külön aktiváló kezelő a csempe popupjában (`UnnamedFacesView.qml:547-587`). | A javaslatlista, a People ablak, a Choose felirata és az ismeretlen névnél People Search Escape a job-167 felvételi jegyzetében szerepel. A javaslatelem kattintásának rögzítése nyitott. A Choose utáni állapot lezárva, lásd a következő sort (helyesbítve, job-179). |
| Choose után: a meglévő személyhez rendelés | A csempe-mezőbe írt meglévő név Enter után a People ablak nyílik, a meglévő személy kijelölve, a jóváhagyó gomb **„Choose”** (`job-167`, `job-179`). A Choose-ra kattintva az ablak bezárul, az arc a meglévő személyhez kerül: `Unnamed (5)` → `Unnamed (4)`, `Teszt Elek (1)` → `Teszt Elek (2)`. A `.picasa.ini`-ben egy `[Contacts2]`-bejegyzés marad, mindkét fotó `faces=` sora ugyanarra az azonosítóra mutat (`job-179`). | #5182 (0.9.123) óta a People ablak Choose-útját valódi kattintásos teszt fedi (d789d91de). | Zárva (`job-179`): nincs nyitott tétel. Referencia a megvalósításhoz: a két számláló-változás és a `.picasa.ini` egy `[Contacts2]`-bejegyzése. |
| Arc mellőzése az X-szel és a fejléc gombjával | A csempe X-ére kattintva **„Ignore People”** megerősítés jelenik meg, majd a **„Ignore Person”** jóváhagyása az arcot mellőzöttként menti: `faces=rect64(27c00680d8ffdb3f),ffffffffffffffff` (`job-64`; a megerősítés képkockája: „Colab EN 36”). Az eredeti fájlkimenet után a mellőzött arc a „Mellőzött emberek” albumba tartozik (15.3/b.1). A fejléc **„Ignore Selected”** gombja csak a kibontott nézetben látszik, kijelölés nélkül szürke (`job-183`, 10. kép). A megerősítő ablak (job-209, 10. kép): cím „Ignore People”; szöveg: „Are you sure you want to move this person to the ignored people album?”; jelölőnégyzet: „Don't ask again, always ignore”; gombok: „Ignore Person” (alapértelmezett) és „Cancel”. A mellőzés után (job-210, 13. kép) a bal sáv sora „Unnamed (5)”, a fejléc „5 Face(s)”, a mellőzött csempe eltűnik, a „Show ignored faces” gomb aktív lesz. A szöveg a binárisban is megvan (28.4/a). | A csempe X és a kibontott nézet fejlécének **„Ignore Selected”** gombja is megerősítést kér (`UnnamedFacesView.qml:417-440, 273-295, 849-909`), majd a FaceScanController mellőzött állapotba teszi az arcot (`face_scan_controller.py:1138-1166`). A csoportosított nézet fejlécében nincs „Ignore Selected” gomb (helyesbítve, job-183). A fejléc „Show ignored faces” gombja akkor aktív, ha van mellőzött arc (`UnnamedFacesView.qml:223-229`); a külön nézetben a „Stop ignoring” visszahozza a kijelölt arcokat (`Main.qml:3275-3280`; `UnnamedFacesView.qml:279-284, 924-949`). A megerősítő ablak szövege, jelölőnégyzete és gombfeliratai egyeznek az eredetivel (`UnnamedFacesView.qml:876-911`; `PeoplePanel.qml:447-473`). | Az X útját és a `.picasa.ini` eredményét a job-64 jegyzete rögzíti. A job-162/163 a kezdeti „Show ignored faces” gombot mutatja, job-163 4. képén szürkén. A megerősítő ablakot és a mellőzött állapotot a job-209/210 lépéssora írja le; a személyszintű mellőzés (N5) külön felvétel. |
| Mellőzött nézet és visszahozás | Az eredetiben a „Show ignored faces” után (job-210, 16. kép) a cím „Ignored people”, alatta „1 Face(s)”; a bal sáv sora „Ignored (1)”; a jobb felső gomb „Back to Unnamed”; az útmutató „Select someone you know and add a name.”; a csempén nincs X, de van „Add a name” mező. A leírás nem említ csempénkénti visszahozó gombot, és a „Back to Unnamed” utáni csempe neve nincs mérve. | A „Show ignored faces” és a „Back to Unnamed” felirata egyezik az eredetivel (`UnnamedFacesView.qml:225`, `:232`). Két eltérés a kódban: a bal sáv sora „Ignored people (N)” (`FolderPane.qml:744`), az eredetinél „Ignored (N)”; a mellőzött nézetben nincs „N Face(s)” sor, mert a `unnamedAlbumFaceCount` (`UnnamedFacesView.qml:249`) csak nem mellőzött módban látszik, az eredetinél „1 Face(s)”. A „Stop ignoring” (`UnnamedFacesView.qml:296`) a kijelölt arcokat hozza vissza; az eredetinél a megfelelő gomb nincs megmérve. | Kész, ha a bal sáv felirata és a darabszám-sor a job-210 szerint jelenik meg (képkocka-összevetéssel), és a visszahozás felvétele (a csempe neve a „Back to Unnamed” után) megvan. |

### 19.1 Nyitott kérdések és megszerzésük

1. **Javaslatelemre kattintás:** nyisd meg a Név nélküliek albumot; a kezdőképkockáról válassz egy csempe „Add a name” mezőt; `kattint [x,y]`, `gepel <meglévő név részlete>`, `var_ablak`; kattints a látható javaslat képére vagy nevére, majd `var_ablak`. Rögzítsd, megnyílik-e a People ablak, megváltozik-e az arc állapota és csökken-e a Név nélküliek száma.
2. **Choose utáni állapot** (lezárva, `job-179`): a csempe-mezőbe írt meglévő név után, a **Choose** gombra kattintva bezárul az ablak, az arc a meglévő személyhez kerül; a `.picasa.ini`-ben egy `[Contacts2]`-bejegyzés marad (lásd a táblázatot).
3. **Escape a csempe mezőjében:** új futásban kattints a csempe mezőjébe, gépelj egy még be nem fejezett nevet, majd `billentyu Escape`, `var_ablak`. Rögzítsd a mező tartalmát, a javaslatpopupot és az esetleges People ablakot.
4. **Ctrl/Shift/húzásos kijelölés** (a Ctrl+A-t a `job-180` már mutatta: mind a hat csempe kijelölve, 15. kép; a többi nyitott): külön futásban kattints egy csempére és rögzítsd az alapot; utána külön próbáld `billentyu Ctrl` + kattintás egy másik csempére, `billentyu Shift` + kattintás egy másik csempére, majd külön `huz [x1,y1] [x2,y2]` két csempe között. Mindegyik után `var_ablak`; a pontokat a ténylegesen kirajzolt képkockáról válaszd ki. Rögzítsd a kijelölt kereteket, a „No Selection”/kijelölésszámot és a tálcát.
5. **Picasa pontos csempe-sorrendje és csoporthatárai:** a job-163 leírása csak öt csempét soronként és hat arcot nevez meg. A job-208 (9. és 11. kép) az öt oszlopos csoportosított és az egy soros kibontott elrendezést adja, csoporthatárt nem, mert mind a hat csoport egyarcú. Hátra van: a csempék balról jobbra, fentről lefelé sorrendje (és a csoportcímkék, ha vannak) egy teljesen kirajzolt, csoportosított képkockán; a csoporthatár többarcú csoportot kíván (más mintakészlet); a pixelméret csak tényleges képkocka-mérés után rögzíthető.
6. **A „Learn more...” gomb címe:** a megnyitott cím a binárisból olvasandó ki, a `Label(instructionpanel/learn_more)` kezelőjéből (`job-175`). Rögzítsd a kezelő bináris címét és a megnyitott cím sztringjét. A felvételből nem olvasható ki (`job-177`). **Megválaszolva (2026-10-18, 28.2):** a kezelő `0x0074c760`, a cím `http://picasa.google.com/support/bin/answer.py?hl=%s&answer=156272` (`%s` = nyelvkód).

*Bizonyítottsági fok: **feltételes** (a jegyzetekben hivatkozott nyers képkockák ebben a munkamenetben nem voltak elérhetők) a Név nélküliek nézet címére, útmutatójára, fejlécgombjaira és alapállapotára (job-162; job-163, 4. és 8. kép); az első megnyitás üdvözlőablakára (job-162, 12. kép; a teljes szöveg job-207, 8. kép); a csempe saját mezőjére és az új név People-ablak útjára (job-163, 11-19. kép); a javaslat megjelenésére, a meglévő névhez tartozó Choose ablakra és a People ablak keresőmezőjében használt Escape-re (job-167, 22., 26-34. kép); a Choose utáni állapotra (job-179); a kibontott és a csoportosított nézet fejlécére és csempéire (job-180, job-183); az új név OK utáni állapotára és `.picasa.ini` soraira (job-66; job-167, 18. kép); valamint az X mellőzési útjára (job-64, „Colab EN 36”); a mellőzési megerősítő ablak szövegére, jelölőnégyzetére és gombjaira, a mellőzött nézet címére, darabszámára, feliratára és jobb felső gombjára (job-209, job-210); a kibontott és csoportosított nézet fejlécére és csempéire (job-208). **NINCS MEG:** a csempék pontos pixelmérete, sorrendje és csoporthatárai, a javaslatelem kattintása, a Ctrl/Shift/húzás kijelölési szabálya, és a mellőzött csempe visszahozása (a „Back to Unnamed” utáni csempe neve; külön felvétel). A „Learn more...” cím a 28.2 szerint megvan; a job-167 Escape-je a People ablak keresőmezőjében történt; a csempe-mező Escape-je nyitott (lásd a táblázatot).*

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

**Nyitott:** a javaslatok eredeti csempefelülete; a javaslat elvetésének és a `]expeople` tokennek a tartós hatása; a személy-album első megjelenített módja és a váltás élő hatása; a teljes személy-album összevonás; az import és mappafelvétel automatikus indítási pontja; a névvel címkézett képen talált új arc kezelése.

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
- **Cím (sablon):** `http://picasa.google.com/support/bin/answer.py?hl=%s&answer=156272`. A `%s` a nyelvkód. Ez a Picasa támogatási oldala, és a szolgáltatás megszűnt (`picasa-menu-parancsok-viselkedes.md` 6557), ezért a PicasaPy-ban nincs működő célja.
- **Nyelvkód forrása:** a `0x0098d380` (importjai: `GetLocaleInfoA`, `InterlockedIncrement`). A visszaesési érték a `0x00c7f979` cím; a tartalma nincs dekódolva. **FELTÉTELES:** a `GetLocaleInfoA` LCTYPE-konstansa nincs ellenőrizve.
- **NINCS MEG:** a `0x00981860` pontos megnyitó lépése (importjai `SearchPathA`, `GetLastError`; a belsejét nem követtem végig). A kezelő regisztrációja a parancstáblában: a `0x0074c760`-nak nincs direkt hívója az indexben; ez index-negatív, nem lelet.
- **Bizonyítottsági fok:** a kezelő és a sablon **megerősített** (A és B egyezik). A nyelvkód forrása és a megnyitás **feltételes**.

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
- Fejlesztési következmény: kódmódosítás nincs. A Learn more gomb a PicasaPy-ban nincs kezelve; a célja megszűnt szolgáltatás, így a gomb sorsa termékdöntés. A 19. szakasz két felirat-eltérése (a bal sáv sora és a mellőzött nézet darabszám-sora) javítási jelölt.

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
- Ghidra-kör kell: `0x007b81e0`, `0x007b9630`, `0x007ba060` - a Choose esemény callbackje, a `0x00586e20` elérésének útja és a kiírás pillanata [blokkoló]
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

- A `0x0068c030` (fájlíró, 22.5) hívása (`0x00697557`; C-dumpban az 1512-1513. sor) előtt `cmp byte ptr [esp+0x1b], 2` (`0x00697540`) áll: a hívás **csak** akkor fut, ha az állapotbájt 2.
- Az állapotbájt (C-ben `uStack_1608._3_1_`) írói a diszasszemblálásban:
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
- **A `0x0084dc30` két listája: részben (megerősített, HÍVÓK-fejléc).** A függvénynek egyetlen közvetlen hívója van: `0x006df399`, a `0x006df1f0`-ban. A két lista (`param_3`, `param_4`) forrása ez a hívó; a hívó törzse nincs olvasva: **NINCS MEG**.
- **A `vtbl+0x78` célja: NINCS MEG.** A hívás `(**(code **)(**(int **)(iVar4 + *param_3)) + 0x78)()` (C: 185. sor); a célt a listaelem osztályának vtáblája adja, és az osztály nincs azonosítva.
- **Bizonyítottsági fok.** A `0x005848b1` előtti elem-feltétel: **megerősített** (asm, egy út). A `(-1,-1)` elérés: **feltételes**. A listaforrás és a `vtbl+0x78` célja: **NINCS MEG**.
- **Cáfoló kísérlet.** Azt feltételeztem, hogy a `0x00584280` a `(-1,-1)` bejegyzésre is elágazik a véletlen kulcs felé: cáfolva az üres név kihagyásával, ha ugyanabban a listában van. A listaazonosság nem cáfolt.
- **Következő cím (c).** `0x006df1f0`: a `0x0084dc30` egyetlen közvetlen hívója; a `param_3`/`param_4` listák feltöltése és a listaelemek vtábla-osztálya (a `+0x78` slot célja). Blokkoló a `(-1,-1)` elérés és a `+0x78` cél eldöntéséhez.

## 35. #5185, negyedik kutatói kör: nyolcpontos eredeti/nálunk leltár (2026-10-19)

**Hatókör és forráskorlát.** Az „Eredeti” a #5185-ben megadott job-162/163/167/179/180/183/207/208/209/210/213 felvételi jegyzeteket, a helyi Picasa 3.9 binárist és a `.fen`/`.tre` erőforrásokat idézi. A képkocka-fájlok ebben a munkafában nincsenek, ezért a jegyzetben szereplő képet nem tudtam újraellenőrizni. A mérőadat-archívum célzott leltárában 15 ini-tag volt, de nem volt `[Contacts2]`, `faces=` sor, `contacts.xml`, db3 vagy #5185-képkocka. Ez a hozzáférési hiány, nem viselkedési negatív lelet. A „Nálunk” oszlop a munkafa 0.9.157-es forrásának olvasata; a PicasaPy nem futott, tehát élő UI-egyezést nem állít.

| Pont | Eredeti | Nálunk (forrásolvasat) | Teendő |
|---|---|---|---|
| **1. Név nélküliek sor, nézet, fejléc, csoport, bélyegek, kijelölés és tálca** | A bal sáv `Unnamed (6)` sorára a jobb oldal „Unnamed people”, „6 Face(s)” és útmutatósort mutat; a gombok „Expand groups” és „Show ignored faces” (job-162/163; job-207, 8. kép). Csoportosítva öt oszlop és csempénként `Add a name`/X látszik; kibontva egy sor, kisebb arcok, fejléc `Add a name`/`Ignore Selected`; visszaváltáskor a csempevezérlők visszajönnek (job-208, 9., 11., 13. kép). Kezdetben `No Selection` és üres tálca (job-162 jegyzet). A pontos eredeti csempeméret/sorrend/többarcú csoporthatár és a Ctrl/Shift/húzás tálcahatása **NINCS MEG**. | `UnnamedFacesView.qml` `grouped: true`-val és üres arc-kijelöléssel indul. A `toggleFace` egyesével kapcsol arcot a `selectedFaceIds`/`selectedCount` állapotban; a csempekattintás nem ad át Ctrl/Shift módot. A rács/csempe méret és a vezérlők a QML-ben rögzítettek; tálcával való futásidejű kapcsolatot nem mértem. | J2: alap kattintás, Ctrl, Shift és húzás; mindegyik után képernyőkép, kijelölésszám és tálcaállapot. A pontos csempeméret/sorrend teljesen látható képkockán mérendő; a csoporthatárhoz többarcú csoport kell. **Mért rész:** job-162/163/207/208. **NINCS MEG:** pontos pixelek és kijelölési szabály. |
| **2. Arc kijelölése és megnevezése; névmező, javaslatlista, Enter/OK és kimenet** | `Tes` begépelésekor arcképes „Teszt Elek” névjegy-kiegészítés jelenik meg (job-167, 22. kép). Teljes név+Enter új személynél a People ablak üres listával és `New Person` gombbal nyílik; meglévő személynél kijelöl és `Choose` gombot mutat (job-163, 14-19. kép; job-167, 26-30. kép). `Choose` után az arc a személyhez kerül és a két sorszám változik (job-179). Job-167 Escape-je az ismeretlen `Valami` keresés után a **People ablak Search mezőjében** történt; változtatás nélkül bezárta azt (32-34. kép). Csempe-Escape, javaslatelem kattintása, Ctrl/Shift/húzás **NINCS MEG**. | A csempe Entere és a névjegy-javaslat elemére kattintás egyaránt a `nameSubmitted(faceId, name)` jelre jut (`UnnamedFacesView.qml`, `submitName`); `Main.qml` ezt a `peoplePanel.nameFaceFromPanel(faceId, name, true)` útjára köti. A People Manager forrásában meglévő kontakt kijelölhető, a jóváhagyó felirata ilyen esetben `Choose`; forrásolvasat, nem PicasaPy-felvétel. | J2 kiegészítése: külön csempe-Escape, javaslatelem-kattintás és Enter; People ablakban `OK`, `Choose`, `Cancel` után képernyőkép és állapot. **Mért:** job-163/167/179. **Nyitott:** eredeti javaslatelem kattintása és csempe-Escape. A job-167 Escape-t ne idézzük csempe-mező bizonyítékaként. |
| **3. Arcfelismerési javaslat, elfogadás és elutasítás** | Az üdvözlőszöveg szerint névadás után hasonló arcok javasolhatók, és a személy-albumban fogadhatók el vagy utasíthatók el (job-207, 8. kép). A job-213 mintában nem jelent meg javaslat, mert mindkét hasonló arc megnevezett lett. A job-167 névjegy-kiegészítése nem arcfelismerési javaslat. A bináris vezérlő útja `0x0063f970` eseményelosztón át a `0x00646d70`/`0x00647020` kezelőkhöz vezet (26.3); a pontos esemény és tartós kimenet nyitott. | A PicasaPy a javasolt arcnevet a csempén és a People album sorában mutatja. Elfogadás az `assignNameToFaces` útján nevet rendel; elutasítás a PicasaPy SQLite-index javaslatmezőjét üríti (`face_scan_controller.py`, `acceptSuggestion`/`rejectSuggestion`). Ez forrásolvasat; Picasa db3-at nem ír. | J3: egy megnevezett személy és egy hasonló névtelen arc; külön profilban elfogadás és elutasítás, előtte/utána `.picasa.ini`, `contacts.xml`, db3, majd újraindítás. **Mért:** job-207 súgó. **NINCS MEG:** eredeti javaslatcsempe, kattintás és adatváltozás-összevetés. |
| **4. Mellőzés és visszahozás** | X kattintásra `Ignore People` megerősítés jelenik meg, szövege „Are you sure you want to move this person to the ignored people album?”, `Don't ask again, always ignore`, `Ignore Person` és `Cancel` (job-209, 10. kép; bináris szöveg `0x00c99830`). Jóváhagyás után az arc eltűnik, számláló csökken, `Show ignored faces` aktív (job-210, 13. kép). A mellőzött nézet címe `Ignored people`, bal sáv `Ignored (1)`, gombja `Back to Unnamed`; az ini az `ffffffffffffffff` azonosítót mutatja (job-210, 16. kép és kimenet). `Ignore Selected` megjelenik, de kattintása nincs mérve; a visszahozás utáni csempeállapot **NINCS MEG**. | A csempe-X és a `Ignore Selected` forrásból megerősítést kér; a FaceScanController menti a mellőzött állapotot. A PicasaPy-ban `Stop ignoring` út van, de élő UI-állapotot ebben a körben nem mértem. | J4 folytatása: kijelölt arccal kattints `Ignore Selected`-re; külön próbáld a személyszintű mellőzést; `Back to Unnamed` után rögzítsd a csempét és az INI/db3 diffet. **Mért:** X/megerősítés/ignored nézet/sentinel, job-209/210. **NINCS MEG:** fejlécgomb kimenete, személyszintű ág, visszahozás utáni állapot. |
| **5. Személy-album: arc/teljes kép, átnevezés, egyesítés, törlés** | A job-213 29. képe a `Teszt Elek (2)` album fejlécét, arc/teljes kép ikonokat, lejátszás/diavetítés/kollázs/film gombokat, szürke `Remove` gombot, arcbélyegeket és mappaképeket mutat; tálca `Album Selected - 2 photos`. Ikonra kattintás, átnevezés, összevonás és törlés eredménye nincs felvéve. A `PeopleAlbumUseFaceSrc` alapértéke 1 (`0x005e5290`), amelyet a `0x00767e50` `face_zoom` aktív módra képez le (35.2); a látható első képkocka nyitott. A PplAlbum menü építője `0x007359e0`; műveleteinek teljes fájlkimenete nyitott. | A LightboxHeader forrása arcra közelített/teljes kép módot vált; jelenlegi PicasaPy alapállapota teljes kép. People Manager név szerkesztést ad. Ez forrásolvasat, a felületet nem futtattam. | J5: első képkocka, mindkét zoomgomb, átnevezés, összevonás és törlés külön; minden lépés előtt/után ini, `contacts.xml`, db3 és újraindítási állapot. **Mért:** album nézete, job-213. **Feltételes:** bináris alapértelmezett leképezés, egy diszasszemblált út. **NINCS MEG:** kattintási és adatváltozási kimenetek. |
| **6. People Manager: elrendezés, kijelölés, mezők, OK/Mégse** | `contactmgr.fen` kétoszlopos People párbeszédet ír le Search mezővel, névjegylistával, Delete Person/New Person, Name/Email(s), Sync Face Tags, Revert, Manage Online Contacts, Refresh Contacts, OK/Cancel mezőkkel. Job-163 új névnél ezeket mutatja; job-167 meglévő személynél `Choose`-t. A lista egyszeres/többszörös kijelölése, Cancel gomb és módosított adat visszavonása **NINCS MEG**. Az Escape csak a job-167 Search mezőjében mért. | A `PeopleManagerDialog.qml` listája `currentIndex`-szel választ kontaktot. `OK` → `commitChanges`; `Cancel` → párbeszédzárás. A controller változásnál központi `contacts/contacts.xml`-t és mappánkénti ini-t ír (`people_controller.py`). Forrásolvasat. | J6: sor, Ctrl/Shift kijelölés; mezőmódosítás; OK, Cancel és Escape külön futásban, előtte/utána contacts/ini/db3 diff. **Mért:** erőforrás+job-163 elrendezés. **NINCS MEG:** kijelölési modell, Cancel hatása és adatváltozás-összevetés. |
| **7. `contacts.xml`, `[Contacts2]`, `faces=`, db3 olvasása/írása** | Job-213 végállapot: `[Contacts2]` `3c067b829137b19=Teszt Elek;;`, két `faces=rect64(...),3c067b829137b19` sor; az ID 15 hex jegyű. Mellőzött arc: `faces=rect64(...),ffffffffffffffff` (job-210). `%I64x` íróformátum: `0x00c82fcc` (32.3). `0x00587110` olvasó; `0x00586e20` kontakt-persistálási jelölt; `0x00484820` általános INI-írási lánc, de a `[Contacts2]` minden ágú írását és időzítését nem bizonyítja (30-32). Az eredeti profil `contacts.xml` és db3 műveleti időzítése **NINCS MEG**. | A PicasaPy központi `contacts/contacts.xml`-t használ; a `.picasa.ini` írása az `ini/` API-n keresztül történik; saját SQLite indexet ír, Picasa db3-at nem. People Manager mentéskor a contact controller írja a központi fájlt és az érintett mappák ini-jét. Forrásolvasat, nincs futásidejű diff. | J8: Picasa profil `contacts.xml`, `.picasa.ini`, db3 másolata művelet előtt, névadás/elfogadás/elutasítás/átnevezés/törlés után, bezáráskor és újraindítás után. **Mért:** INI-alak, job-210/213. **Bináris:** `0x00587110`, `0x00484820`, `0x00c82fcc`. **NINCS MEG:** eredeti fájlírás pillanata és db3/contacts.xml hatása. |
| **8. Arcfelismerés: mikor indul, mit hagy ki, küszöb** | `BgFaceDetectThread` default 1 (`0x0069fc00`); `FRAddSuggesetions` indításkapu `0x00414940`. A `FRSuggestionThreshold`/`FRSortThreshold` alapértéke 85, UI lépcsők: 50,55,60,65,70,75,80,85,90,95 (1.1-1.2). Az első scan pontos pillanata, az azonosított arccal rendelkező fotóban egy másik arc kihagyása és a Red.dll valódi felismerési határa **NINCS MEG** (20-21, 27-29). | A `FaceScanController` szinkronizálás után automatikus keresést indíthat; kihagyja a képet, ha bármely ini-arc azonosított, ha videó, ha az adott mtime/méret már vizsgálva volt, vagy a mappa kizárt. Forrásolvasat. | J7: első import/új mappa/új kép; névvel jelölt arc mellett másik arc; kizárt mappa; azonos képkészlet pontos küszöbállásokkal. A Red.dll küszöbét csak bináris cím/érték vagy pontos mérés igazolhatja. **Bináris:** fenti címek és 1.1-1.2. **NINCS MEG:** futásindítás, kihagyási eredmény, detektor döntési küszöbe. |

### 35.1 Bizonyítottsági fok, két út és cáfoló kör

A teljes #5185 állapota **nyitott**: mind a nyolc pont Eredeti/Nálunk/Teendő formában szerepel, de a táblában megnevezett részviselkedésekhez új eredeti felvétel vagy adatváltozás-összevetés kell. A „Nálunk” állítások forrásolvasatok, nem futásidejű mérések.

- **A út - eredeti felvételi jegyzetek:** job-162/163/167/179/180/183/207/208/209/210/213 a látható felületet és a job-210/213 INI-kimenetet írja le. A nyers képek/fájlok itt nem érhetők el.
- **B út - bináris és erőforrás:** `annot_disasm.py` olvasata adja a zoom defaultot (`0x005e5290`, `0x00767e50`); `contactmgr.fen` a párbeszéd elemeit; bináris sztring-xref a mellőzési megerősítés szövegét (`0x00c99830`). Az X-megerősítés képkockája és bináris sztringje egyezik, valamint a job-213 ID-alakja és a `%I64x` (`0x00c82fcc`) egyezik. Ezek csak a közös metszetükre két utat adnak.
- **Cáfoló: Escape.** A korábbi spec-mondat a csempe-Escape-et tulajdonította a job-167-nek. A lépéssor ellenőrzése szerint Escape az ismeretlen `Valami` keresés után, a People ablak Search mezőjében történt. A csempemező nem volt fókuszban; az állítás cáfolva, helyesbítve a 19.1-ben.
- **Cáfoló: javaslat azonosítása.** A job-167 `Tes` listája névjegy-kiegészítés; a job-207 útmutató az arcfelismerési javaslatot a személy-albumhoz köti. A job-213-ban javaslat nem volt, mert a hasonló arcok meg voltak nevezve. A kettőt nem azonosítottam.
- **Cáfoló: zoom.** A `picture_zoom` inverz ágát is ellenőriztem: `arg==0` aktiválja, míg `face_zoom` az argumentumot közvetlenül használja. Ez összhangban van az 1→face olvasattal, de ugyanazon diszasszemblálás része, ezért az alapértelmezett leképezés **feltételes**, nem megerősített.

### 35.2 A `PeopleAlbumUseFaceSrc` bináris leképezése

A `0x005e5290` a `Preferences\\PeopleAlbumUseFaceSrc` értékének 1 alapértéket ad (`0x005e52b5`), majd a `0x005e52f5` címen átadja a `0x00767e50` függvénynek. A `face_zoom` ág (`0x00767f54`-`0x00767fb0`) az argumentumot közvetlenül állítja be; a `picture_zoom` ág (`0x00767ec5`-`0x00767f36`) az argumentum ellentettjét. Ezért **az alapérték 1 → `face_zoom` aktív, `picture_zoom` inaktív**; a 0 az ellenkező módot választja.

**Fok: feltételes.** Egy diszasszemblált út olvassa a preferenciát és oldja fel az értékét; job-213 csak a két ikon jelenlétét rögzíti, kattintási hatást és első megjelenített képet nem. A cáfoló próba a másik ág olvasása volt; ez megerősíti az inverz logikát, de nem második független út. J5 első képkockája és mindkét gomb kattintása kell az élő megerősítéshez.

### 35.3 A #5185 „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték |
|---|---|---|
| 1. Név nélküliek nézet, fejléc, csoport, méret/sorrend, tálca/kijelölés | ⛔ Részben | Job-162/163/207/208: nézet, felirat, csoportváltás és üres kezdőtálca. Pontos pixelek/sorrend/csoporthatár és Ctrl/Shift/húzás tálcahatása nyitott. |
| 2. Arc kijelölése, névmező, javaslat, Enter/OK, cél/lista | ⛔ Részben | Job-163/167/179: mező, névjegy-kiegészítés, People/Choose és Choose utáni cél. Csempe Escape, popup kattintás, Ctrl/Shift/húzás nyitott. |
| 3. Arcfelismerési javaslat és elfogadás/elutasítás | ⛔ Részben | Job-207 útmutató; job-213-ban nem volt javaslat. UI és adatváltozás-összevetés nyitott. |
| 4. Mellőzés és visszahozás | ⛔ Részben | Job-209/210: X, megerősítés, ignored album és sentinel. Fejlécgomb és visszahozás utáni állapot nyitott. |
| 5. Személy-album műveletei | ⛔ Részben | Job-213: album és zoomikonok. Bináris default 1→face_zoom. Kattintási hatás/átnevezés/egyesítés/törlés nyitott. |
| 6. People Manager | ⛔ Részben | `contactmgr.fen` + job-163 elrendezése; job-167 Choose/Search Escape. Kijelölés és Cancel hatás nyitott. |
| 7. Névforrások/időzítés | ⛔ Részben | Job-210/213 INI-alak; bináris olvasó/író jelöltek. `contacts.xml`/db3 hatás és mentési pillanat nyitott. |
| 8. Felismerés indítása/kihagyások/küszöb | ⛔ Részben | Bináris kapcsolók és értékek (1.1-1.2, `0x0069fc00`, `0x00414940`). Élő indítás/kihagyás és Red.dll döntési küszöb nyitott. |

A pontok mind ki vannak mondva és minden nyitott részhez konkrét J2-J8 felvételi út tartozik; a kutatás az eredeti műveletek és fájlhatások hiánya miatt nem állít teljes viselkedési lezárást.

### 35.4 Jegytörzs-bővítés és fejlesztési következmény

**Beemelhető szöveg:** „A #5185 nyolc pontjának Eredeti / Nálunk / Teendő összevetése a `docs/specs/picasa-arcfelismeres.md` 35. szakaszában van. A PeopleAlbumUseFaceSrc default 1 a binárisban `face_zoom` aktív állapotot jelent (`0x005e5290` → `0x00767e50`; feltételes, az első élő képkocka még kell). A job-167 Escape a People ablak Search mezőjében történt, ezért a csempe Escape nyitott. A job-167 gépelt névlistája névjegy-kiegészítés, nem arcfelismerési javaslat. Az X-es mellőzés és az `ffffffffffffffff` ini-érték job-209/210 alapján megvan; a fejléc mellőzése/visszahozás, javaslatkimenetek és contacts.xml/db3 mentési időzítések J3/J4/J8-cal nyitottak.”

**Fejlesztési jelölt, élő megerősítés után:** a jelenlegi PicasaPy forrás teljes képet használ alapállapotként; a Picasa bináris alapértéke `face_zoom`. Ha J5 megerősíti az eredeti első képkockát, a fejlesztési feladat a PicasaPy személy-album alapmódjának és a két zoomgomb tartalmának egyeztetése. **Kész, ha:** eredeti és PicasaPy képkockán az alapmód és mindkét váltás egyezik, és a preferencia követi a mért visszatöltési viselkedést. A mostani adat ehhez még nem elég: preferencia-újratöltés és élő eredeti mód nyitott. A többi #5179-#5184 jegy cím/törzs-hozzárendelése ebben a helyi feladatban **NINCS MEG**; ne következtessünk rá a jegyszámokból.

### 35.5 Új kutatási jegyjavaslatok és nyitott pontok

Új külön kutatási jegy nem szükséges; a nyitott feladatok ugyanazon #5185/J2-J8 felvételi folytatásai:

- **J2:** arc-kijelölés, Ctrl/Shift/húzás és tálca; minden művelet után képkocka és állapotszöveg.
- **J3:** egy megnevezett személy és egy hasonló névtelen arc; javaslat felvétele, elfogadás és elutasítás külön profilban, fájlok előtte/utána/újraindítás után.
- **J4:** `Ignore Selected`, személyszintű mellőzés, `Back to Unnamed` utáni csempe és ini/db3 diff.
- **J5:** első személy-album képkocka, mindkét zoomgomb, átnevezés, összevonás, törlés és adatváltozás-összevetés.
- **J6:** People Manager kijelölés, OK, Cancel és Escape külön; contacts/ini/db3 állapot előtt/után.
- **J7:** import/új mappa/új kép indítása, megnevezett fotón másik arc, kizárt mappa és pontos küszöbállások; Red.dll paramétert becsülni tilos.
- **J8:** eredeti profil `contacts.xml`, `.picasa.ini` és db3 másolata minden művelet előtt, után, bezáráskor és újraindítás után.
