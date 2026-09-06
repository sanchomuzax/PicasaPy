# Az `imagedata` rekord — a Picasa belső kép-nyilvántartása

A `0x004127c0` függvényből. ⛔ **HELYESBÍTVE (2026-09-06):** ez a lap
eddig azt írta, hogy a `0x004127c0` a `facerect`/`facerectdata` **írója**, és
hogy a rekord **38** mezőből áll. **Mindkettő téves.** A függvény a gyűjtemény
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

**37 mező.** Ebből a `.picasa.ini`-ből ismert: `rotate`, `caption`,
`filters`, `backuphash`, `facerect`, `facerectdata`. A többi a **belső
adatbázisban** él.

## Amit ez újat mond

| mező | mire következtethetünk |
|---|---|
| `edit_width` / `edit_height` | a **szerkesztett** méret külön tárolva a fájl méretétől — a vágás/forgatás utáni állapot |
| `textactive` | a szöveg-eszköz aktív állapota külön jelző |
| `revertable` | van-e mihez visszatérni (a `.picasaoriginals` megléte) |
| `originslow` / `originfast` | **két különböző eredeti-hivatkozás** — feltehetően a teljes és a gyors (bélyegkép) forrás |
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

## Az eltolás-tábla — melyik mező hol ül a gyűjtemény-objektumban

Minden sor egy regisztráló blokk a `0x004127c0`-ban: `push <névsztring>` →
`lea eax, [esi + <eltolás>]` → a típusnak megfelelő `CColumn` konstruktor.

| eltolás | mező | | eltolás | mező |
|---:|---|---|---:|---|
| `0x016c` | `parent` | | `0xca0` | `personalbumid` |
| `0x022c` | `filetype` | | `0xd00` | `suggestionpersonalbumid` |
| `0x028c` | `fileflags` | | `0xd60` | `facequality` |
| `0x0358` | `creation` | | **`0xdc0`** | **`facerect`** |
| `0x03c0` | `modified` | | `0xe28` | `deferredface` |
| `0x0428` | `updated` | | `0xe88` | `deferredregion` |
| `0x0490` | `width` | | `0xee8` | `facerectdata` |
| `0x04f0` | `height` | | `0xf48` | `personalbumrecs` |
| `0x0550` | `rotate` | | `0xfa8` | `personalbumrecvalues` |
| `0x0618` | `flipped` | | `0x1008` | `personalbumrecs2` |
| `0x0678` | `edit_width` | | `0x1068` | `personalbumrecvalues2` |
| `0x06d8` | `edit_height` | | `0x10c8` | `peoplealbumchecksum` |
| `0x0738` | `caption` | | `0x1128` | `tagdate` |
| `0x0798` | `filters` | | `0x1190` | `fdbhash` |
| `0x0858` | `textactive` | | `0x11f0` | `backuphash` |
| `0x0918` | `edited` | | | |
| `0x0978` | `revertable` | | | |
| `0x09d8` | `originslow` | | | |
| `0x0a40` | `originfast` | | | |
| `0x0aa8` | `uid64` | | | |
| `0x0b10` | `aliasparents` | | | |
| `0x0c40` | `colorspace` | | | |

⛳ **Egybevág a `pmp-database.md`-vel:** ott a `width` `+0x490`, a `facerect`
`+0xdc0`, a `facerectdata` `+0xee8` — mindhárom **betű szerint** egyezik.

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
| **pontosan `1`** (alsó=1, felső=0) | `0x004466c0` | a kimeneti téglalapot **nullázza**, és a **`0xF4240` = 1 000 000** kódot adja vissza | `0x004466b4` `cmp eax,1`, `0x004466bc` `test ecx,ecx`, `0x004466eb` `mov eax,0xf4240` |
| **`0`** | `0x0044673a` | tartalék útra megy: `FUN_00448270` (négy argumentum) | `0x00446736` `or edx,ecx` + `jne` |
| **minden más** | `0x004467b2` | kicsomagolja a `rect64`-et, majd a **`width`** (`+0x13b0`) és a **`height`** (`+0x1410`) oszlopot is zárolja, és a `FUN_009b93f0`-nel képpontra váltja | `0x004467bf` `add esi,0x13b0`, `0x00446859` `add esi,0x1410`, `0x004468dd` |

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

### Ami NYITVA marad ebből (#2515)

**Hol íródik konkrétan az `1`?** A csomagoló (`FUN_009b9150`) nulla
téglalapból **nullát** ad, nem egyet, és bájtmintás keresés a
`mov dword ptr [reg],1` + `mov dword ptr [reg+4],0` párra a `.text`-ben
**nulla** találatot adott ⇒ az `1` regiszterből érkezik, egy másik íróból.
A tizenhét `+0x1ce0` hely közül még hét nincs végigolvasva
(`0x0046bda5`, `0x0047077a`, `0x0047b59a`, `0x0047d8be`, `0x0047f6b3`,
`0x00482a1e`, `0x0074866b`).

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
