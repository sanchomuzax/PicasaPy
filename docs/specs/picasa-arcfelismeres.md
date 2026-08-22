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
| `eMenuTools::ID_TOOLS_DOWNLOAD_FACES` | **0x9e10** | Eszközök, idx 10 (`0xd6e918`) | *Download Name Tags from Picasa Web Albums* / **Névcímkék letöltése a Picasa Webalbumokból** |
| `eMenuTools::ID_WRITE_XMP_FACES` | **0x9e2a** | Eszközök ▸ **Experimental** almenü, utolsó elem (`0xd6e838`) | *Write faces to XMP…* / **Arcinformációk írása XMP-adatokba…** |
| `eMenuPicture::ID_PICTURE_RESET_FACES` | **0x9e11** | Kép menü, idx 8 (`0xd6e538`) | *Reset &Faces* / **Arcok alaphelyzetbe állítása** |
| `AlbumPhoto::ID_PICTURE_RESET_FACES` | **0x9e11** (ugyanaz) | **három** helyi menü: mappa-fotó, album-fotó, egyképes nézet | ugyanaz |
| `Album::ID_ALBUM_FILTERFACES` | **0x9e1c** | **két** helyi menü (mappa, album) — mindkettőben az **utolsó** tétel | *&Add name tags* / **Névcímkék hozzáadása** |
| `eMenuCreateMovie::ID_FACES` | **0x9d59** | Létrehozás ▸ Film almenü, idx 1 | *From Faces in Selection…* / **A kijelölésben lévő arcokból…** |
| `eMenuCreateMovie::ID_FACESRANDOM` | **0x9d5a** | ugyanott, idx 2 | *From People Albums…* / **Az Emberek albumból…** |
| `PplAlbumPhoto::ID_PEOPLEALBUMSNEW` | **0xa0cc** | Emberek-album fotó helyi menü, idx 1 | *Move to &New Person…* / **Áthelyezés új személyhez…** |
| `PplAlbumPhoto::ID_PEOPLEALBUMS` | **0xa0cd** | ugyanott, idx 2 | *&Move to People Album* / **Hozzáadás az Emberek albumhoz** |
| `PplAlbumPhoto::ID_SETPEOPLEALBUMCOVER` | **0x9e39** | ugyanott, idx 4 | *&Set as People Album Thumbnail* / **Beállítás az Emberek album indexképeként** |

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
| **B) `FRWriteFaceDataINI`** | `0x00484820` | `Preferences\FRWriteFaceDataINI`, **alapból 0** | `faces` + **`facedata`** + `backuphash` |

A **B) útvonal** a `0x00484dcf`-en olvassa a kapcsolót; ha nincs
bekapcsolva (`bl == 0`), a teljes arc-blokk **átugrik** a `0x00484f72`-re.
Ha be van kapcsolva, három kulcsot ír egymás után:

```asm
0x0048516d  push "faces"        -> 0x005ab210(szakasz, kulcs, érték)
0x004851ab  push "facedata"
0x0048521c  push "backuphash"
```

A `backuphash` képzése itt is a már ismert (#643) alak: a 64 bites érték
négy 16 bites szavának XOR-ja, `"%d"`-vel formázva
(`0x004851cf`–`0x004851f2`).

> ⭐ **ÚJ, eddig sehol nem dokumentált kulcs: `facedata`.** Sem a
> [`picasa-ini-format.md`](picasa-ini-format.md), sem a kódunk nem ismeri.
>
> **DE — mérve:** a 859 fájlos valódi `.picasa.ini`-korpuszban a `facedata`
> **0-szor** fordul elő (`faces=` 4973-szor, `backuphash` 14700-szor).
> Ez egybevág azzal, hogy a kapcsolója alapból ki van kapcsolva.
>
> **Amit ez a megvalósításra jelent:** `facedata`-t **írni nem kell**; a
> round-trip parsernek viszont **meg kell őriznie**, ha valaha előfordul.

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

⚠️ **`ffffffffffffffff` = „ismeretlen / nincs személyhez rendelve"**
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
| `.picasa.ini` írás (B útvonal) | csak ha `FRWriteFaceDataINI` **be van kapcsolva** |
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

## 8. A KÉT BEÉPÍTETT, VÉDETT SZEMÉLYI ALBUM

`0x004ac650` (456 b) hozza létre őket, album-tokennel:

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

---

## 9. AZ EMBEREK PANEL — állapotok és feliratok

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

## 10. Eredeti / nálunk / teendő

| # | | eredeti | nálunk | teendő |
|---|---|---|---|---|
| 1 | detektáló motor | háttérszál, 8 rekesz | **nincs** (3. fázis) | #26 |
| 2 | `faces=` olvasás/írás | `rect64(hex),<contact_id>` | a `zfill(16)` **már helyes** (`ini/rect64.py:35`) | ✅ **nincs teendő** — ld. 13/b |
| 3 | **`facedata` ini-kulcs** | írja, ha `FRWriteFaceDataINI` be | **nem ismertük**, de a round-trip **MEGŐRZI** (mérve) | ✅ **nincs teendő** — ld. 13/b |
| 4 | `deferredface` / `deferredregion` import | két külön oszlop, átfedéssel | **nincs importálva** | ebből jön a `contact_id → név` tábla |
| 5 | `facerect` értelmezése | **logikai jelző**, nem rect | a specünk „szentinel"-nek írta | helyesbítve (3.3) |
| 6 | `ffffffffffffffff` | „ismeretlen" szentinel | — | ne személyként importáljuk |
| 7 | duplikált kontakt | előfordul (mérve) | — | az importáló tűrje |
| 8 | két beépített album | `]unknownface`, `]ignoreface`, **nem törölhető** | **nincs** | #26 |
| 9 | két küszöb | 50–95, ötösével, alap 85 | **nincs** | ha lesz motorunk, ugyanez a létra |
| 10 | `frversion` | **`"1.5"`** | — | importáláskor ezt írjuk |

---

## 11. Bizonyítottsági fok

- **Megerősített:** a beállításkulcsok, alapértékek és a küszöb-létra
  (kód + ugrótábla-bájtok); a két ini-írási útvonal és a `FRWriteFaceDataINI`
  kapu; a három romboló művelet; a verzió-migráció; a két beépített album
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
| 1 | A `facerect` `0x1` pontos jelentése | **LEZÁRVA (2026-08-22)** — a „B" telepítés megmutatta: az oszlop VEGYES, valódi rect64-et tárol megerősített régiónál, `1`-et jelzőként detektálás után (3.3). ~~BLOKKOLT~~ — az adat csak annyit bizonyít, hogy fájlonkénti logikai jelző; az írási hely a binárisban nincs feltárva. Folytatás: a `facerect` oszlop íróhelye a `0x004127c0` regisztrációból. Jegy: **#1238** |
| 2 | A `facerectdata` szerepe | **LEZÁRVA (2026-08-22)** — arc-JELLEMZŐPONTOK: `conf`, `pan`, `leye`, `reye`, `mouth` (3.4/c). ~~BLOKKOLT~~ — 0 nem üres sor, nincs mit mérni; élő, arc-sablonos adatbázis kellene. Jegy: **#1238** (`felhasználóra-vár`: nevesített arcokat tartalmazó `db3` másolat) |
| 3 | Az `albumcontactids` szemantikája | **LEZÁRVA (2026-08-22)** — album → kontakt-azonosító, 9/9 egyezés a `contacts.xml`-lel (3.4/b). A két `*checksum` **továbbra is BLOKKOLT** (a `peoplealbumchecksum` egyetlen értéke `34`, az `albumpeoplechecksum` 8 szórt érték — a képzési szabály nem dőlt el). ~~BLOKKOLT~~ — mind 0 soros; ugyanaz a külső anyag kell. Jegy: **#1238** |
| 4 | A `deferredregion` a nevesített részhalmaz-e | **LEZÁRVA (nemleges)** — 15 mért ellenpélda cáfolja a tiszta részhalmaz-viszonyt; a lap 3.4 rögzíti feltételesként |
| 5 | A `contact_id` hash képzési szabálya | **HATÓKÖRÖN KÍVÜL** — és 2026-08-22 óta tárgytalan is: az azonosító **telepítésfüggő**, tehát importáláskor amúgy sem használható kulcsként; a **név** az egyeztetés alapja (3.4/b). — az importáláshoz nem kell: az azonosítót nem mi képezzük, hanem olvassuk. Ha valaha kell, a `contacts.xml` adja a leképezést |
| 6 | A `facedata` kulcs értékének pontos mezőszerkezete | **LEZÁRVA (tárgytalan)** — 0 korpusz-előfordulás, alapból kikapcsolt kapcsoló; a teendő a megőrzés, nem az értelmezés |
| 7 | A `0x9e1c` azonosító **ütközése**: ugyanez az érték a feltöltés-beállítások felugró menüjében is szerepel (`ImpULOpts::ID_ALLOW_COLLAB`, rekord `0xd6f334`) | **LEZÁRVA (nem a mi gondunk)** — más menücsalád, más szétosztó-hívó; nálunk a parancsazonosítókat nem globális névtérként vesszük át, hanem menünként. Ha valaki mégis globálisan egyedinek tekintené, előbb ellenőrizze, befut-e ez a felugró a `0x005cb990`-be |
| 8 | A `0xa0cd` (Hozzáadás az Emberek albumhoz) tényleges kezelője | **BLOKKOLT** — nincs saját ága a szétosztóban, az alapértelmezett ágra fut (`0x0069aeb0`), amiben egyetlen sztring sincs; futásidőben töltött almenü gyanúja. Jegy: **#1238** |
| 9 | A `CreateAcceleratorTableA` (`0x0092321a`) tartalma — van-e mégis gyorsbillentyű | **BLOKKOLT** — a függvény hívója relatív `call`-szkenneléssel nem került elő (valószínűleg vtáblán át hívódik). Jegy: **#1238** |

```
Nyitott kérdések: 0 nyílt · 8 lezárva · 2 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
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
