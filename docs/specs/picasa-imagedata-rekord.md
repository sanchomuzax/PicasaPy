# Az `imagedata` rekord — a Picasa belső kép-nyilvántartása

A `0x004127c0` függvényből. ⛔ **KÉTSZER HELYESBÍTVE (2026-09-06):** a lap
eredetileg azt írta, hogy a `0x004127c0` a `facerect`/`facerectdata` **írója**,
és hogy a rekord **38** mezős; egy köztes változat **37**-et írt. **Mindhárom
téves.** A helyes szám **44** — a 37-es mérés hét mezőt kihagyott, mert a
kiolvasó minta csak a `lea eax` alakot ismerte, miközben hét regisztráló blokk
`lea ecx`/`lea edx`/`lea edi`-t használ. A hét kimaradt mező: **`name`,
`size`, `crop64`, `text`, `tags`, `lat`, `long`** — és ezek nevét a
`string_xrefs` sem adta vissza, mert a sztringjük a `.rdata` másik szakaszán
áll; **közvetlen `.rdata`-olvasással** kerültek elő (`0x00c7fa20`,
`0x00c80a9c`, `0x00c80adc`, `0x00c80b0c`, `0x00c80b20`, `0x00c80b6c`,
`0x00c80b70`). A függvény a gyűjtemény
**konstruktora**: mezőnként egy `CColumn<…>` objektumot épít a névvel és a
típussal, és a gyűjtemény-objektum rögzített eltolására teszi (a párja a
**destruktor**, `0x00413020`, ami ugyanezeket az eltolásokat járja végig
fordított sorrendben). **Értéket nem ír.** A mezők száma **37** — a
regisztráló blokkok tételes kiolvasásával (lásd az eltolás-táblát).

## A teljes mezőlista, sorrendben

```
parent · filetype · fileflags · creation · modified · updated
width · height · rotate · flipped · edit_width · edit_height
caption · filters · textactive · edited · revertable
originslow · originfast · uid64 · aliasparents · colorspace
personalbumid · suggestionpersonalbumid · facequality
facerect · deferredface · deferredregion · facerectdata
personalbumrecs · personalbumrecvalues
personalbumrecs2 · personalbumrecvalues2 · peoplealbumchecksum
tagdate · fdbhash · backuphash
```

**44 mező.** Ebből a `.picasa.ini`-ből ismert: `rotate`, `caption`,
`filters`, `backuphash`, `facerect`, `facerectdata`. A többi a **belső
adatbázisban** él.

## Amit ez újat mond

| mező | mire következtethetünk |
|---|---|
| `edit_width` / `edit_height` | a **szerkesztett** méret külön tárolva a fájl méretétől — a vágás/forgatás utáni állapot |
| `textactive` | a szöveg-eszköz aktív állapota külön jelző |
| `revertable` | van-e mihez visszatérni (a `.picasaoriginals` megléte) |
| `originslow` / `originfast` | ✅ **MEGFEJTVE** — két tartalomkulcs ugyanarra a fájlra: `originfast` = fej+farok MD5 (#1481), `originslow` = a TELJES fájl MD5-jének első 8 bájtja (#1482). A „bélyegkép-forrás” olvasat téves volt. A `.picasa.ini` `originhash` kulcsa épp e kettő szöveges összefűzése (#791) |
| `uid64` | 64 bites egyedi képazonosító |
| `aliasparents` | ugyanaz a kép több mappában (hivatkozás-szülők) |
| `colorspace` | a kép színtere külön mezőben (ld. az lcms-integrációt) |
| `facequality` | **arc-minőségi pontszám** — a Picasa értékelte a detektált arcokat |
| `deferredface` / `deferredregion` | **halasztott** arcfeldolgozás: a régió megvan, a felismerés még nem futott |
| `personalbumid` / `suggestionpersonalbumid` | a megerősített és a **javasolt** személy külön mezőben |
| `personalbumrecs` / `…values` / `…recs2` / `…values2` | **két generációnyi** felismerési eredmény, azonosító+érték párokban |
| `peoplealbumchecksum` | az Emberek-albumok állapotának ellenőrzőösszege |
| `tagdate` | a címkézés dátuma |
| `fdbhash` | az arc-adatbázis rekordjának hash-e |

A `deferredface`/`deferredregion` és a `suggestionpersonalbumid` együtt
megmagyarázza a felület viselkedését (#26): a program **elkülöníti** a
megtalált, de még nem azonosított arcot, a javasolt nevet és a megerősített
nevet.

## Az eltolás- és TÍPUS-tábla — mind a 44 mező (2026-09-06)

Minden sor egy regisztráló blokk a `0x004127c0`-ban:
`push <névsztring>` → `lea <reg>, [esi + <eltolás>]` → **a típusnak megfelelő
`CColumn` konstruktor**. A típus tehát nem következtetés: a hívott konstruktor
címe adja meg. ⚠️ A `lea` regisztere **nem** mindig `eax`.

| # | eltolás | mező | típuskód | C++ típus | importáljuk? |
|---:|---:|---|---:|---|---|
| 1 | `0x16c` | `parent` | **0x01** | `unsigned long` (u32) | — |
| 2 | `0x1cc` | `name` | **0x00** | `ytString` (sztring) | — |
| 3 | `0x22c` | `filetype` | **0x01** | `unsigned long` (u32) | — |
| 4 | `0x28c` | `fileflags` | **0x01** | `unsigned long` (u32) | — |
| 5 | `0x2f0` | `size` | **0x04** | `unsigned __int64` (u64) | — |
| 6 | `0x358` | `creation` | **0x02** | `double` (double) | — |
| 7 | `0x3c0` | `modified` | **0x02** | `double` (double) | — |
| 8 | `0x428` | `updated` | **0x02** | `double` (double) | — |
| 9 | `0x490` | `width` | **0x01** | `unsigned long` (u32) | — |
| 10 | `0x4f0` | `height` | **0x01** | `unsigned long` (u32) | — |
| 11 | `0x550` | `rotate` | **0x00** | `ytString` (sztring) | ✅ |
| 12 | `0x5b0` | `crop64` | **0x04** | `unsigned __int64` (u64) | ✅ |
| 13 | `0x618` | `flipped` | **0x00** | `ytString` (sztring) | — |
| 14 | `0x678` | `edit_width` | **0x07** | `int` (**előjeles** i32) | — |
| 15 | `0x6d8` | `edit_height` | **0x07** | `int` (**előjeles** i32) | — |
| 16 | `0x738` | `caption` | **0x00** | `ytString` (sztring) | ✅ |
| 17 | `0x798` | `filters` | **0x00** | `ytString` (sztring) | ✅ |
| 18 | `0x7f8` | `text` | **0x00** | `ytString` (sztring) | — |
| 19 | `0x858` | `textactive` | **0x03** | `signed char` (**előjeles** i8) | — |
| 20 | `0x8b8` | `tags` | **0x06** | `char const*` (sztring-mutató) | ✅ |
| 21 | `0x918` | `edited` | **0x03** | `signed char` (**előjeles** i8) | — |
| 22 | `0x978` | `revertable` | **0x03** | `signed char` (**előjeles** i8) | — |
| 23 | `0x9d8` | `originslow` | **0x04** | `unsigned __int64` (u64) | — |
| 24 | `0xa40` | `originfast` | **0x04** | `unsigned __int64` (u64) | — |
| 25 | `0xaa8` | `uid64` | **0x04** | `unsigned __int64` (u64) | — |
| 26 | `0xb10` | `aliasparents` | **0x01** | `unsigned long` (u32) | — |
| 27 | `0xb70` | `lat` | **0x02** | `double` (double) | ✅ |
| 28 | `0xbd8` | `long` | **0x02** | `double` (double) | ✅ |
| 29 | `0xc40` | `colorspace` | **0x03** | `signed char` (**előjeles** i8) | — |
| 30 | `0xca0` | `personalbumid` | **0x01** | `unsigned long` (u32) | — |
| 31 | `0xd00` | `suggestionpersonalbumid` | **0x01** | `unsigned long` (u32) | — |
| 32 | `0xd60` | `facequality` | **0x01** | `unsigned long` (u32) | — |
| 33 | `0xdc0` | `facerect` | **0x04** | `unsigned __int64` (u64) | — |
| 34 | `0xe28` | `deferredface` | **0x00** | `ytString` (sztring) | — |
| 35 | `0xe88` | `deferredregion` | **0x00** | `ytString` (sztring) | ✅ |
| 36 | `0xee8` | `facerectdata` | **0x00** | `ytString` (sztring) | — |
| 37 | `0xf48` | `personalbumrecs` | **0x01** | `unsigned long` (u32) | — |
| 38 | `0xfa8` | `personalbumrecvalues` | **0x01** | `unsigned long` (u32) | — |
| 39 | `0x1008` | `personalbumrecs2` | **0x01** | `unsigned long` (u32) | — |
| 40 | `0x1068` | `personalbumrecvalues2` | **0x01** | `unsigned long` (u32) | — |
| 41 | `0x10c8` | `peoplealbumchecksum` | **0x05** | `unsigned short` (u16) | — |
| 42 | `0x1128` | `tagdate` | **0x02** | `double` (double) | — |
| 43 | `0x1190` | `fdbhash` | **0x01** | `unsigned long` (u32) | — |
| 44 | `0x11f0` | `backuphash` | **0x05** | `unsigned short` (u16) | — |

**Az „importáljuk?" oszlop a MI kódunk mérése** (`pmpimport/importer.py:26`):
a 44-ből **kilencet** olvasunk (`caption`, `rotate`, `star`, `filters`,
`crop64`, `deferredregion`, `tags`, `lat`, `long`) — a `star` kivételével mind
szerepel a fenti listában.

⛳ **Egybevág a `pmp-database.md`-vel:** ott a `width` `+0x490`, a `facerect`
`+0xdc0`, a `facerectdata` `+0xee8` — mindhárom **betű szerint** egyezik.

### A nyolc konstruktor — innen jön a típus

| konstruktor | RTTI-osztály | 3. sablonparaméter | típuskód |
|---|---|---:|---:|
| `0x004941f0` | `CColumn<ytString,0,322043904>` | `0x13320000` | **0x00** |
| `0x00494c50` | `CColumn<unsigned_long,1,322043905>` | `0x13320001` | **0x01** |
| `0x00495d30` | `CColumn<double,1,322043906>` | `0x13320002` | **0x02** |
| `0x00496020` | `CColumn<signed_char,1,322043907>` | `0x13320003` | **0x03** |
| `0x00495360` | `CColumn<unsigned___int64,1,322043908>` | `0x13320004` | **0x04** |
| `0x004961b0` | `CColumn<unsigned_short,1,322043909>` | `0x13320005` | **0x05** |
| `0x00493ce0` | `CColumn<char_const*,1,322043910>` | `0x13320006` | **0x06** |
| `0x00495ec0` | `CColumn<int,1,322043911>` | `0x13320007` | **0x07** |

⇒ Mind a nyolc PMP-típuskód **C++ típusnévvel** azonosítva. Ez a
`pmp-database.md` típustáblájának (#2105) és az előjelesség-javításnak
(#2106) **teljes, független megerősítése** — most már nem csak három típusra,
hanem mind a nyolcra.

### Amit a típusok elárulnak

- **`rotate`, `flipped`, `caption`, `filters`, `text`, `deferredface`,
  `deferredregion`, `facerectdata`, `name` — mind SZTRING** (`ytString`),
  nem szám. A `rotate` tehát az adatbázisban is a `.picasa.ini`-beli
  `rotate(N)` alakot tartja, nem egy egészet.
- **`creation`, `modified`, `updated`, `tagdate`, `lat`, `long` — `double`.**
  Az első négy időbélyeg lebegőpontos, a `lat`/`long` pedig **fokban tárolt
  földrajzi koordináta**.
- **`edit_width` / `edit_height` — `int`, azaz ELŐJELES** (`0x07`). Pontosan
  az a két oszlop, amelyen a #2106 előjeles-olvasási hibája kiderült.
- **`textactive`, `edited`, `revertable`, `colorspace` — `signed char`**
  (`0x03`): logikai/kis egész jelzők.
- **`tags` az EGYETLEN `char const*` oszlop** (`0x06`) az egész rekordban.
- **`crop64` és `facerect` ugyanaz a típus** (u64) — és a `crop64` írója
  (`FUN_0047e930`) ugyanazt a `FUN_009b9150` csomagolót használja, tehát a
  **vágási téglalap bitszerkezete azonos az arc-téglalapéval**.

### ⛔ NEGATÍV: a `star` NEM regisztrált `imagedata` oszlop

A 44 regisztrált mező között **nincs `star`** — pedig a valódi
adatmappákban ott az `imagedata_star.pmp`. A Picasa 3.9 a csillagozást
**`starlist.txt`**-ből olvassa: a sztring (`0x00c81ad4`) az adatbázis-perzisztáló
két függvényében szerepel (`0x0041ba40`, `0x004a82d0`), a `saverlist.txt`
mellett.

⇒ **Az `imagedata_star.pmp` örökölt oszlop**: régebbi adatbázisokban ott van,
de a 3.9 nem regisztrálja. A `pmpimport/importer.py` **kétforrású** megoldása
(`starlist.txt` ÉS a `star` oszlop, `_read_starlist`) ezzel **igazolt** — nem
felesleges óvatosság.

## A mező TÍPUSÁT az RTTI mondja meg — és igazolja a PMP-típuskódokat

A `facerect` regisztrálója a `0x00495360` konstruktor, amely a
`0x00c8230c` vtáblát írja az objektumba. Az RTTI szerint ez:

```
CColumn<unsigned___int64,1,322043908>::vftable   0x00c8230c
```

A harmadik sablonparaméter **hexában olvasva** adja a jelentést, és a
szomszédos `CColumn` példányokkal együtt kirajzol egy táblát:

| RTTI-osztály | 3. paraméter | hexa | PMP-típuskód |
|---|---:|---|---:|
| `CColumn<ytString,0,322043904>` (`0x00c8229c`) | 322043904 | `0x13320000` | **0x00** — sztring |
| `CColumn<unsigned_long,1,322043905>` (`0x00c82344`) | 322043905 | `0x13320001` | **0x01** — u32 |
| `CColumn<double,1,322043906>` (`0x00c822d4`) | 322043906 | `0x13320002` | **0x02** — double |
| `CColumn<unsigned___int64,1,322043908>` (`0x00c8230c`) | 322043908 | `0x13320004` | **0x04** — u64 |

⇒ **A `0x1332` egy közös aláírás, az alsó bájt pedig PONTOSAN a
`.pmp` fájlfejléc típuskódja** — a `pmp-database.md` típustáblájának
(#2105) **független, bináris megerősítése**, most már nem a fájlokból
visszafejtve, hanem a C++ típusnévből.

⇒ A `facerect` tehát a binárisban is **u64** oszlop, nem jelző-bájt. Ez
összefér a mért adattal (`picasa-arcfelismeres.md` 3.3): az oszlop
**vegyes** — valódi `rect64`-et és `1`-et is tárol.

## Minden oszlopnak SAJÁT zárja van

A `CColumn` objektum első 0x50 bájtja fix (a `0x00495360` konstruktorból és
a `0x007e3908`-nál olvasható használatból):

| eltolás | mi | bizonyíték |
|---:|---|---|
| `+0x00` | vtábla (`0x00c8230c`) | `0x00495377` |
| `+0x0c` | „a zár inicializálva van" jelző | `0x007e3935` `cmp byte ptr [esi+0xc], 0` |
| `+0x20` | a zárat tartó **szál azonosítója** | `0x007e3924`; a `GetCurrentThreadId` az importtáblából (`0x00c40284`) |
| `+0x24` | rekurziószámláló | `0x007e392f` `add dword ptr [esi+0x24], 1` |
| `+0x28` | `CRITICAL_SECTION` (az `EnterCriticalSection` argumentuma, `0x00c4055c`) | `0x007e393b` |
| `+0x48` | második vtábla (`0x00c82330`) | `0x0049537d` |
| `+0x4c` | a mező **neve** (sztringmutató) | `0x00495388` |
| `+0x50` | a szülő gyűjtemény | `0x004953b0` |

⇒ **Oszloponként külön kritikus szakasz** — a Picasa a háttérszálas
beolvasás és a felület között oszlop-granularitáson zár, nem az egész
rekordon. (Megerősített; a `personalbumid` oszlop tényleges használatán
olvasva, `0x007e3908`–`0x007e394d`.)

## Ki OLVASSA: a Tulajdonságok párbeszéd

A `CPropertiesDlg` (`0x007e3210`) a `[obj+0xc0] + 0xf20` bázisból nyolc
`imagedata` oszlopot vesz elő, sorrendben:

| sorrend | cím | oszlop |
|---:|---|---|
| 1 | `0x007e3908` | `personalbumid` |
| 2 | `0x007e39bf` | `suggestionpersonalbumid` |
| 3 | `0x007e3a76` | `facequality` |
| 4 | `0x007e3b2d` | `personalbumrecs` |
| 5 | `0x007e3be4` | `personalbumrecvalues` |
| 6 | `0x007e3c9d` | `facerectdata` |
| 7 | `0x007e3d9b` | `width` |
| 8 | `0x007e3e22` | `height` |

⛔ **NEGATÍV, és beszédes:** ugyanez a függvény **NEM** veszi elő a
`facerect`, a `deferredface` és a `deferredregion` oszlopot — pedig a
szomszédjaikat mind kiírja. A párbeszéd sztringjei között ott a
`FaceInstanceID`, az `FRTemplateSize`, a `recpeoplealbumid`, a `recvalue` és
a `width=%d,height=%d,crop=%s,fr=%s` minta is.

## ✅ A `facerect` ÍRÓJA és a `0`/`1`/`rect64` háromfelé ágazás (2026-09-06, #2515)

⛔ **HELYESBÍTÉS az előző körre.** Ez a szakasz korábban azt írta, hogy „a
bájtszintű pásztázás lehetőségei kimerültek", és hogy az **összevont
eltolásra** (`0xf20 + 0xdc0 = 0x1ce0`) kapott 17 találat **hamis pozitív**.
**Mindkét állítás téves volt.** A `0x1ce0` az igazi cím: a gyűjtemény a
gazdaobjektum **`+0xf20`** eltolásán ül — ezt a gyűjtemény konstruktorának
egyetlen hívója mondja ki:

```
0x00415a9f  lea esi, [ebp + 0xf20]        ; ide épül az imagedata-gyűjtemény
0x00415aa6  call 0x4127c0                 ; a gyűjtemény konstruktora
```

⇒ a `facerect` oszlop a gazdához képest **`+0x1ce0`**, és a 17 találat
**mind valódi**. A két „hamis pozitívnak" mondott hely (`0x0047c247`,
`0x0047c323`) is a `facerect` oszlopot **zárolja** — csak utána a gazda egy
MÁSIK tagját (`+0x2b20`/`+0x2b24`) módosítja.

### A `CColumn` adattárolása — kiolvasva

| eltolás | mi | bizonyíték |
|---:|---|---|
| `+0x58` | az **adattömb-objektum** (üres oszlopnál `NULL`) | `0x00446257` |
| `+0x58 → +0x4c` | a sorok száma **kétszerese** (`shr 1` kell) | `0x00446265` |
| `+0x58 → +0x48` | maga az elemtömb | `0x0044626b` |
| elem-lépésköz | **8 bájt** u64-nél (`lea eax,[edx+ebp*8]`), **4** u32-nél (`lea eax,[eax+ecx*4]`) | `0x0044626e`, `0x004468c4` |
| `+0x60` (u64) / `+0x5c` (u32) | a beágyazott **alapérték**, ha nincs sor | `0x00446273`, `0x004468c9` |

### A `rect64` becsomagolása — `FUN_009b9150`, utasításonként

A csomagoló négy 16 bites mezőt fűz össze egyetlen 64 bites értékbe
(`edx:eax`), a bemenet egy négy `dword`-ös téglalap `ecx`-en:

```
u64 = (m0 << 48) | (m1 << 32) | (m2 << 16) | m3
      m0 = [ecx+0x00]  m1 = [ecx+0x04]  m2 = [ecx+0x08]  m3 = [ecx+0x0c]   (mind & 0xffff)
```

(`0x009b915a` `shld`, `0x009b9160` `shl 16`, `0x009b916f`, `0x009b917c`.)

A **kicsomagolás** a `0x004467b2`-nél betű szerint ennek az inverze:
`[ebp+0]=felső>>16`, `[ebp+4]=felső&0xffff`, `[ebp+8]=alsó>>16`,
`[ebp+12]=alsó&0xffff`. ⇒ **az oda-vissza út bitre zár.**

### ⭐ A HÁROM ÁG — mit jelent a `0`, az `1` és minden más

A `FUN_00446610` (a „kérd le a sor arc-téglalapját" függvény) a beolvasott
u64-et **háromfelé** ágaztatja:

| érték | ág | mit tesz | bizonyíték |
|---|---|---|---|
| **pontosan `1`** (alsó=1, felső=0) | `0x004466c0` | a kimeneti téglalapot **nullázza**, és a **`0xF4240`** kóddal tér vissza | `0x004466b4` `cmp eax,1`, `0x004466bc` `test ecx,ecx`, `0x004466eb` `mov eax,0xf4240` |
| **`0`** | `0x0044673a` | tartalék útra megy: `FUN_00448270` (négy argumentum) | `0x00446736` `or edx,ecx` + `jne` |
| **minden más** | `0x004467b2` | kicsomagolja a `rect64`-et, majd a **`width`** (`+0x13b0`) és a **`height`** (`+0x1410`) oszlopot is zárolja, és a `FUN_009b93f0`-nel képpontra váltja | `0x004467bf` `add esi,0x13b0`, `0x00446859` `add esi,0x1410`, `0x004468dd` |

> ⛔ **HELYESBÍTÉS (2026-09-06, késobbi kör):** ez a szakasz eredetileg úgy
> fogalmazott, hogy az `1` ág „**saját** visszatérési kóddal" tér vissza.
> **A `0xF4240` nem az ág sajátja:** a `mov eax, 0xF4240` a `.text`-ben
> **809** helyen szerepel (pl. a `makemoviepanel` `rewind` ága is,
> `0x0061e45a`) — ez a program **általános „kezeltem / rendben" kódja**.
> Az ág megkülönböztető jegye tehát **a nullázott téglalap**, nem a kód.

⇒ **A `0` és az `1` NEM geometria, hanem két KÜLÖNBÖZŐ jelző** — a `0`
tartalék-útra küld, az `1` viszont üres téglalapot ad **saját
visszatérési kóddal**. A `picasa-arcfelismeres.md` 3.3 mérése („vegyes
oszlop") ezzel a binárisból is igazolt.

**Harmadik, független megerősítés ugyanerre a küszöbre:** a `FUN_00446370`
soronként **logikai tömböt** épít, és a feltétele szó szerint
„`facerect > 1`":

```
0x0044657c  cmp dword ptr [eax + 4], 0    ; felső 32 bit
0x00446580  ja  0x446587                  ; > 0  → 1-et ír
0x00446582  cmp dword ptr [eax], 1        ; alsó 32 bit
0x00446585  jbe 0x44659b                  ; ≤ 1  → 0-t ír
0x00446589  mov dword ptr [ecx + edx*4], 1
0x00446594  mov dword ptr [eax + edx*4], 0
```

### ⭐ AZ ÍRÓ: `FUN_00480040`

A tényleges tárolás **két utasítás**:

```
0x00481093  mov ecx, [ebp + 0x48]         ; az oszlop elemtömbje
0x00481096  mov edx, [ecx + edi*8]        ; a sor jelenlegi értéke
0x00481099  lea eax, [ecx + edi*8]        ; a sor CÍME
0x004810a3  cmp edx, ecx                  ; egyezik az új alsó fele?
0x004810aa  cmp edx, [esp + 0xbc]         ; …és a felső?
0x004810b1  je  0x4810ce                  ; ha ugyanaz → NEM ír
0x004810b3  mov dword ptr [eax], ecx      ; ⇐ ALSÓ 32 BIT
0x004810bc  mov dword ptr [eax + 4], ecx  ; ⇐ FELSŐ 32 BIT
0x004810c9  call 0x6a2a60                 ; változás-értesítés a gyűjteménynek
```

Az érték útja: a négy `dword`-ös téglalap (`[esp+0x70…0x7c]`) →
`FUN_009b9290` (`0x00480e33`) → **`FUN_009b9150`** (`0x00480e3f`, a fenti
csomagoló) → `[esp+0xb8]`/`[esp+0xbc]` → a fenti két `mov`.

⛳ **A belépési feltétel — és ez a lényeg:** az író **csak akkor** ír, ha a
sor jelenlegi `facerect` értéke **NULLA**:

```
0x00480dcf  mov edi, [eax + ecx*8]        ; alsó
0x00480dd2  mov ebx, [eax + ecx*8 + 4]    ; felső
0x00480de7  test edi, edi
0x00480de9  jne 0x481386                  ; ha nem nulla → KIHAGYJA
0x00480def  test ebx, ebx
0x00480df1  jne 0x481386
```

⇒ **A már beírt téglalapot és az `1`-es jelzőt a program NEM írja felül.**
Ez magyarázza a mért megoszlást (`picasa-arcfelismeres.md` 3.3): a `0` a
„még nem dolgoztuk fel", az `1` a „feldolgoztuk, nincs használható
téglalap" — és egyik sem íródik újra.

### ✅ AZ `1` ÍRÓJA IS MEGVAN — és a felhasználói kiváltó okkal együtt (2026-09-06)

Az `1` **nem** a téglalap-csomagolóból jön (az nulla téglalapból nullát ad),
hanem egy külön **tömeges beállítóból**:

```
FUN_00446960(gazda, sorlista, BÁJT érték, jelző)
0x0044696b  lea ebx, [edi + 0xf20]        ; a gyűjtemény
0x004469b3  lea esi, [ebx + 0xdc0]        ; ⇒ a facerect oszlop
0x00447387  call 0x97c810                 ; a tömb újrafoglalása (realloc)
0x004473f1  movsx eax, byte ptr [esp+0x48]; a BÁJT argumentum, előjelesen
0x004473fc  mov ecx, [edi + 0x48]         ; az oszlop elemtömbje
0x004473ff  mov esi, [esi + ebp*4]        ; a sorindex a listából
0x00447402  cdq                           ; előjel-kiterjesztés → felső 32 bit
0x00447403  mov dword ptr [ecx + esi*8], eax        ; ⇐ ALSÓ 32 bit
0x0044740a  mov dword ptr [ecx + esi*8 + 4], edx    ; ⇐ FELSŐ 32 bit
```

⇒ **`érték = 1` esetén a tárolt u64 pontosan `1` lesz** — ez a hiányzó
láncszem.

**A hívó kimondja mindkét értéket, egymás után:**

```
0x0049161d  push 1
0x0049161f  push 1          ; ⇐ az ÉRTÉK: 1
0x00491621  lea ecx, [esp + 0x24]
0x00491625  push ecx        ; sorlista „A"
0x00491626  push esi        ; a gazdaobjektum
0x00491627  call 0x446960   ; ⇒ facerect := 1
0x0049162c  push 0
0x0049162e  push 0          ; ⇐ az ÉRTÉK: 0
0x00491630  lea edx, [esp + 0x1c]
0x00491634  push edx        ; sorlista „B"
0x00491635  push esi
0x00491636  call 0x446960   ; ⇒ facerect := 0
```

### ⭐ Mi váltja ki — a hívási lánc a FELHASZNÁLÓIG

| szint | cím | mi ez |
|---|---|---|
| 4 | `FUN_00446960` | a tömeges beállító (fent) |
| 3 | `FUN_00491210` | `0x00491627`-nél `1`-gyel, `0x00491636`-nál `0`-val hívja |
| 2 | `FUN_005cef20` | egyetlen hívó |
| 1 | `FUN_007c4df0` | **`CFolderMgrDialog`** — a függvény sztringjei: `"Are you sure you want to remove all faces and name tags from excluded folders?"` és `CFolderMgrDialog::confirmfrexclude` |

⇒ **Az `1`-es jelző a Mappakezelőből származik:** amikor a felhasználó egy
mappát kizár az arcfelismerésből, és a program megkérdezi, hogy
*„Biztosan eltávolítja az összes arcot és névcímkét a kizárt mappákból?"*,
az igenre az érintett sorok `facerect` mezője **`1`** lesz — a
„feldolgozva, szándékosan nincs téglalap" jelző —, egy másik sorlistáé pedig
**`0`**.

⛳ **Ez összeáll a `FUN_00480040` viselkedésével:** az író **csak nulla
értékre** ír, tehát az `1` **megvédi a képet az újra-detektálástól**. Pontosan
ezért kell külön jelző a `0` mellé.

**Bizalmi fok: megerősített** — minden lépés utasításonként olvasva. Amit
**NEM** mértem: hogy a `FUN_00491210` melyik sorlistát tölti fel melyik
szabály szerint (melyik kép kerül az „A", melyik a „B" listába).

### ⇒ Nálunk (MEGVALÓSÍTVA, 2026-09-08, #2519)

Az `1`-es jelző megfelelője a **`face_scan` tábla**
(`src/picasapy/index/faces_detected.py`, sémaverzió 18) — külön tábla, mert
nálunk a `photos` sor a fájl adata, ez pedig származtatott feldolgozási nyom:

| eredeti | nálunk |
|---|---|
| `facerect = 0` (még nem dolgoztuk fel) | nincs `face_scan` sor |
| `facerect = 1` (feldolgozva, nincs téglalap) | `face_scan.ok = 'kizarva'` |
| „lefutott a detektálás" (az eredetiben nincs külön értéke) | `face_scan.ok = 'detektalva'` a fájl `mtime_ns`/`size` azonosságával |
| az író csak nullára ír ⇒ az `1` véd | a `kizarva` jelölést a fájl változása SEM oldja fel |

Két eltérés, szándékosan:

1. **A `detektalva` jelölés a fájl AZONOSSÁGÁHOZ kötött** — a megváltozott
   képet újra megnézzük (az eredeti a `mtime`-ot itt nem használja). A
   `kizarva` viszont az eredetihez hasonlóan ragad.
2. **A `.picasa.ini` `faces=` / `[Contacts2]` sorait NEM töröljük**, pedig a
   megerősítő kérdés a névcímkékről is szól. Az a felhasználó saját,
   Picasában felvett adata; a mi származtatott találatainkat (`face` tábla)
   viszont a kizárás törli.

## A `filters=` lánc sorosítója — `0x00463fd0`

Ugyanez a kódterület kezeli a lánc szöveges alakját. A dekompilált kódban
közvetlenül olvasható formátumok:

| minta | mire |
|---|---|
| `rotate(%d)`, `rotate(0)`, `rotate(-1)` | forgatás |
| `rect64(%I64x)` | vágás — **olvasás `sscanf`-fel, írás `sprintf`-fel** |
| `redeye=1;` | vörösszem-jelző |
| `retouch=1;` | retus-jelző |
| `picnik=1;` | Kreatív készlet-jelző |
| `moviestart=`, `movieend=` | **videó vágópontok** |

### A `rect64` bitszerkezete

```c
_sprintf(dst, "rect64(%I64x)",
         y0 << 16 | x0 & 0xffff,      // alsó 32 bit
         y1 << 16 | x1 & 0xffff);     // felső 32 bit
```

Vagyis a 64 bites érték **négy darab 16 bites koordináta**, két 32 bites
szóba csomagolva, felső-alsó sorrendben. (A változónevek a dekompilált
kódban gépiek; a sorrend a `sprintf` argumentumaiból következik.)

### A videó vágópontok osztálya

A `moviestart=` / `movieend=` feldolgozása a **`CTimeFilter`** osztályhoz
kötődik:

```
FUN_009ae560("CTimeFilter::startname", ...)
FUN_009ae560("CTimeFilter::endname",  ...)
```

Vagyis a videó vágása a Picasában **ugyanabban a szerkesztési láncban** él,
mint a képi effektek, és külön osztály kezeli. Ez a #452-höz tartozik.
