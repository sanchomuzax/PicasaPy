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

### `albumdata_albumpeoplechecksum` — ez VALÓDI hash, és NINCS megfejtve

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
negatívum** a három megdőlt hipotézisre. Az `albumpeoplechecksum` képzési
szabálya **nyitva marad**.*

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
levélnevét, és **25 parancsot** ismer. A javaslat-munkafolyamathoz
tartozók vastagon:

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
| 18 | **`confirmsel`** | **`0x005c9b00`** | `0x005e160f` |
| 19 | **`ignore`** | **`0x005c9b00`** | `0x005e1645` |
| 20 | **`addname`** | **`0x00602970`** | `0x005e169a` |
| 21 | **`sug_filter`** | vtable-hívás | `0x005e16e9` |
| 22 | **`removesel`** | **`0x005c9b00`** | `0x005e177b` |
| 23 | `create_face_movie` | `0x00603660` | `0x005e17d0` |
| 24 | `set_thumbnail` | `0x00603660` | `0x005e180c` |
| 25 | `folderbutton` | `0x004adfe0` | `0x005e185b` |

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

#### b) A jóváhagyás / elvetés a `.picasa.ini`-be ír

A `faceheaderpanel/confirmsel`, `faceheaderpanel/ignore` és `faceheaderpanel/removesel` **ugyanazt** a kezelőt hívja
(`0x005c9b00`, 5744 b), és annak sztringjei megnevezik a tárolót:

| sztring | mi |
|---|---|
| `.picasa.ini` | a célfájl |
| **`]ignoreface`** | az elvetett arc jelölése |
| **`]unknownface`** | az ismeretlen arc jelölése |
| `]search` | (ugyanennek a kezelőnek a másik ága) |

⇒ A javaslat elvetése **nem** az adatbázisban marad: a `.picasa.ini`
kapja meg — ugyanabban a rendszerben, amit a 3.1 pont ír le.

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
holt kód.)*

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
| javaslat-vezérlők | `faceheaderpanel/confirmsug`, `faceheaderpanel/confirmsel`, `faceheaderpanel/removesel`, `faceheaderpanel/moresug`, `faceheaderpanel/sug_filter`, `faceheaderpanel/selectsug`, `faceheaderpanel/addname`, `faceheaderpanel/ignore` | **egyik sincs** — 0 találat `confirmAll`/`moresug`/arc-javaslat névre a `src/`-ben |
| arc-nagyítás váltó | `faceheaderpanel/face_zoom` ↔ `faceheaderpanel/picture_zoom` | **nincs** |
| a küszöb-lazítás | `FRSuggestionThreshold/100 − 0,1` | **nincs** |

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
