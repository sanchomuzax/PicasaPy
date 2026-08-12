# Az `imagedata` rekord — a Picasa belső kép-nyilvántartása

A `0x004127c0` függvény dekompilálásából (a `facerect`/`facerectdata` közös
írója). A függvény egy `"imagedata"` nevű rekordot sorosít, mezőnként
nevesítve.

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

**38 mező.** Ebből a `.picasa.ini`-ből ismert: `rotate`, `caption`,
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
