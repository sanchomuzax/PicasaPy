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

## ⛔ Ki ÍRJA a `facerect`-et — NYITVA, és pontosan tudjuk, MIÉRT

A kérdés (`picasa-arcfelismeres.md` 3.3, **#1238**): mi dönti el, hogy az
oszlopba valódi `rect64` kerül-e vagy `1`. Ez a kör **nem** válaszolta meg,
és az alábbi felsorolás azért van itt, hogy a következő kör ne járja újra:

**Amit kipróbáltam, és mit adott:**

1. **Sztring-xref a névre** — a `facerect` név az EGÉSZ binárisban
   **egyetlen** helyen fordul elő: a regisztrációban (`0x00412d25`, a
   sztring `0x00c80bb8`). Névre keresés tehát nincs a kódban.
2. **Eltolás-pásztázás (`[reg+0xdc0]`, ModRM `mod=10`, SIB és `ebp` kizárva)**
   — a `0xdc0` dword az egész `.text`-ben **9**-szer fordul elő; ebből az
   `imagedata`-gyűjteményre kettő vonatkozik: a konstruktor (`0x00412d3e`) és
   a destruktor (`0x0041309a`). A maradék hét más objektumon bájtműveletet
   végez (`0x0057c556`, `0x005df0bb`, `0x005dfa4d` `mov byte`/`cmp byte`),
   illetve idegen könyvtárban áll (`0x00b113d6`).
3. ⛔ **A 2. pont MÓDSZERE ÉRVÉNYTELEN — kontrollal mérve.** Ugyanezt a
   pásztázást lefuttattam olyan oszlopokra, amelyeket a Picasa 3.9 biztosan
   ír (`edited`, `revertable`, `edit_width`, `edit_height`, `textactive`):
   **mind az öt NULLA találatot adott.** Az ok a `0x007e3903`-nál olvasható:
   a bázis `[obj+0xc0] + 0xf20`, tehát a fordító a két konstanst
   **összevonhatja** — a mezőeltolás önmagában nem is jelenik meg a kódban.
   ⇒ *A „nincs eltolás-találat" ebben a rekordban NEM bizonyítja, hogy a
   mezőt senki nem írja.*
4. **Összevont eltolás (`0xf20 + 0xdc0 = 0x1ce0`)** — 17 találat, de
   **hamis pozitívak**: a `0x0047c247` és a `0x0047c323` helyen a
   `[edi+0x1ce0]` egy MÁSIK osztály zárja, a védett adat `[edi+0x2b20]` /
   `[edi+0x2b24]`. Az összevont keresés tehát nem szűr.
5. **A bázisképző idióma pásztázása** (`add r32, 0xf20` + rákövetkező
   `lea r,[r+eltolás]`) — az egész binárisban **47** `add r32,0xf20` hely
   van, és ebből mindössze **10** párosul oszlop-eltolással: nyolc a
   `CPropertiesDlg`-ben, egy a `filters`-re (`0x00846a88`), egy a
   `tagdate`-re (`0x0084ae7a`). A `facerect`-re **egy sem**.

⇒ **A bájtszintű pásztázás lehetőségei kimerültek**: a gyűjtemény bázisa
regiszterben/változóban él, az eltolások összevonva, tehát csak
**dekompilálás** (Ghidra, `picasa-x86-research`) tudja megmondani, melyik
függvény ír az oszlopba. A kérdés ezért **örökölt nyitott kérdés** marad a
**#1238**-on, immár a fenti öt kizárt úttal.

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
