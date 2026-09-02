# A Picasa 3 BEÉPÍTETT WEBSZERVERE — a működés

A Picasa 3 nem csak kliens: **saját HTTP-kiszolgálót futtat**, WebDAV-val,
HTTP Basic hitelesítéssel, RSS-hírcsatornákkal, hibakereső lapokkal és egy
LAN-os megosztás-funkcióval. Ez a lap ezt írja le.

**Miért fontos nekünk, ha nem építjük meg:** ez a Picasa **beérkező**
felülete — egy hallgatózó port. A lap célja kettős: rögzíteni, mit tudott az
eredeti, és **kimondani, hogy ezt szándékosan nem vesszük át** (→ **#2023**).

Bizonyíték-alap: `Picasa3.exe`, image base `0x00400000`. A teljes kiszolgáló
a `0x004c0000`–`0x004cf000` tartományban él.

---

## 1. Mi kapcsolja be, és mit enged

| beállítás (`Preferences\…`) | mit tesz | cím |
|---|---|---|
| `AllowRemoteWeb` | ha **nincs** bekapcsolva, a kiszolgáló **csak localhostot** szolgál ki: `„Not allowed, this server supports localhost only."` | `0x004cbc60` |
| `LANShareAlbums` | mely albumok látszanak a hálózaton | `0x004ca0c0`, `0x004ca5a0`, `0x004c3ce0` |
| `LANPassword` | a HTTP Basic jelszó; a **felhasználónév fixen `picasaserver`** | `0x004cce10` |
| `DAVSupport` | a WebDAV-igék (`OPTIONS`, `PROPFIND`) engedélyezése | `0x004cbc60` |
| `EnableTester` | a `/tester` hibakereső terület engedélyezése (`POST /tester` is ide tartozik) | `0x004cbc60`, `0x004cc300` |
| `UIProfiling` (bitmaszk, `0x1`) | a `/uidebug` lap rajzolási időmérése; a lap ki is írja: `„Enable UIProfiling=0x1 (pref) for UI profile."` | `0x004c8270`, `0x009dd800` |

**Hitelesítés:** hiányzó vagy rossz jelszónál `Unauthorized` +
`WWW-Authenticate: Basic realm="Picasa"` és a `„Please provide a valid
password"` törzs (`0x004cbc60`).

**Két terület (realm):** `/public` és `/tester` (`0x004cc300`). Az URL-alak
mindenütt `http://localhost:<port>/<terület>/…` (`0x004cd010`, `0x0073bd40`,
`0x00533de0`).

> **A port NINCS MÉRVE.** A címsablonokban `%d` áll, és a `ws2_32` hívások a
> binárisban **ordinál szerint** importálódnak, ezért az index nem adja meg a
> `bind` helyét. Amit tudunk: a **WebDAV-ág a 80-as portot igényli** — ha
> foglalt, a Picasa a `CThumbUI::DAVFail` üzenetet adja:
> *„This computer has another service running on port 80. Sorry, but this
> feature won't work."* (`0x005cb990`), és a megosztás Windowsból
> **`\\localhost\picasa`** alakban érhető el (ugyanott).

---

## 2. Mit hirdet magáról a hálózaton

A `0x00937800` egy regisztrációs/hirdetési rekordot állít össze:

```
server=picasa
computer=<gépnév>
user=<felhasználónév>
httpport=<port>
repl=1
dbid=<adatbázis-azonosító>
```

⚠️ Ez **gépnevet és bejelentkezett felhasználónevet** tesz a hálózatra. Ez
önmagában is elég ok arra, hogy a PicasaPy ne vegye át a funkciót változtatás
nélkül.

---

## 3. A végpontok — TELJES lista

A központi útválasztó (`0x004ca660`) a következő előtagokat ismeri:

| útvonal | mit ad | cím |
|---|---|---|
| `/albumlist` | album-keret (HTML) | `0x004ca660` |
| `/indexfeed` | index-hírcsatorna | `0x004ca660` |
| `/globalfeed` | a teljes gyűjtemény hírcsatornája | `0x004ca660`, `0x004c9bf0` |
| `/albumfeed` | egy album hírcsatornája (`/albumfeed%d`) | `0x004c1400` |
| `/album` | album-lap (`album%d.html`) | `0x004c5720` |
| `/search` | keresés (lapozható) | `0x004c4470` |
| `/msearch` | mobil keresés | `0x004ca660` |
| `/filesigs` | **fájl-metaadatok** `text/plain` alakban | `0x004c23e0` |
| `/albumsigs` | **album-metaadatok** `text/plain` alakban | `0x004c1e70`, `0x004c1f00` |
| `/ge?BBOX=<lat>,<lon>,<lat>,<lon>` | **KML** a Google Earth-nek | `0x004c4b30` |
| `/tags` | címkefelhő (`<span style='font-size:%d%%'>`) | `0x004c1b60` |
| `/decimate?ct=%d` | mintavételezett lista | `0x004c43d0` |
| `/albumdebug` | „Picasa Album Debug" lap | `0x004c3770` |
| `/dbdebug` | „Picasa %s Debug" — **adatbázis-böngésző** (`album` / `file` / `cat` tábla, szűrővel) | `0x004c2af0` |
| `/repost`, `/upload` | **beküldés** (POST) | `0x004ca830`, `0x004c6480` |
| `/uidebug` | a felület csomópontfája rajzolási időkkel | `0x004c8350`, `0x004c7b30` |
| `/focusalbum?album=%d` | album kijelölése a futó programban | `0x004c8350` |
| `/favicon.ico` | `image/x-icon`, a `runtime\favicon.ico`-ból | `0x004cbc60`, `0x004c08f0` |

**Kép-végpontok** (`0x004c9bf0`): `image/<id>.jpg?size=N` ·
`thumb/<id>.jpg?size=-N` · `sthumb/<id>.jpg?size=-N` · `original/<név>`.
A `size` **negatív** értéke a bélyegkép-ágat választja. További paraméterek:
`imgmax=`, `imgmax=%d`, `imgdl=1`.

**WebDAV** (`0x004cb5f0`, `0x004c8f80`): `OPTIONS` válasza
`DAV: 1 / MS-Author-Via: DAV / Allow: OPTIONS,GET,PROPFIND`, a `PROPFIND`
`Multi-Status` XML-t ad `D:response` · `D:href` · `D:propstat` · `D:prop` ·
`D:creationdate` · `D:getlastmodified` · `D:displayname` ·
`D:getcontentlength` · `D:ishidden` · `D:iscollection` · `D:resourcetype` ·
`D:collection` · `D:status` elemekkel. A megosztás gyökere `/picasa`; a
`0x004caa90` **két** nevet ismer: `picasa` és **`picasa@640`** (a 640
képpontos változat), és `desktop.ini`-t is kiszolgál.

---

## 4. A `text/plain` metaadat-alak — egy FÜGGETLEN mezőlista

Ez a lap legértékesebb része a PicasaPy szempontjából: a `/filesigs` és az
`/albumsigs` **soronként egy kulcs=érték** alakban adja ki ugyanazt az adatot,
amit a `.picasa.ini` és a PMP is tárol — csak **másik kódútvonalon**. Ezért
független megerősítése annak, hogy a Picasa mit tekint egy kép, illetve egy
album rekordjának.

**Album (`0x004c1e70`, `0x004c1f00`):**

```
dbid=%s
version=%d
used=%d
date=%f
description=%s
location=%s
name=%s
filename=%s
```

**Fájl (`0x004c23e0`):**

```
origin=…
filename=…
cdate=%lf
mdate=%lf
size=%d
rot=%d
flip=%d
filters=%s
caption=%s
lat=%lf
long=%lf
```

**Két megjegyzés, mérve:**

1. A `lat`/`long` itt **külön két mező**, míg a `.picasa.ini`-ben egyetlen
   `geotag=<lat>,<lon>` sor (ld. [`picasa-helyek-panel.md`](picasa-helyek-panel.md)).
   Ugyanaz az adat, két alak.
2. A **`flip`** mező a gyakorlatban **üres**: az `imagedata_flipped.pmp`
   a tulajdonos `arcok` adatbázisában **3 011 sorból 3 011-ben üres**, és a
   859 fájlos `.picasa.ini`-korpuszban **egyetlen** `flip=` vagy `flipped=`
   sor sincs. ⇒ *Negatív eredmény: a tükrözés-jelzőt nem kell megvalósítani,
   és nem kell keresni sem.*

---

## 5. A `picasa://` egyedi URL-séma — a MÁSIK beérkező felület

A kiszolgáló mellett a Picasa saját URL-sémát is regisztrál
(`0x004bc0c0`, `0x004bb760`):

| URL | mit tesz | cím |
|---|---|---|
| `picasa://showimg/?…` | kép megnyitása | `0x004bbed0`, `0x00702320` |
| `picasa://showimgtmp/?<id>` | ideiglenes kép megnyitása (a `/dbdebug` lap linkjei ilyenek) | `0x004bbaf0`, `0x007020a0` |
| `picasa://importbutton/?url=…` | **gomb-bővítmény importálása egy URL-ről** — a megerősítése: „Launch Picasa and import buttons?" | `0x004bbaf0`, `0x004bbed0` |
| `picasa://uploadtogoogle/?…` | feltöltés indítása | `0x004bbaf0`, `0x004bbed0` |
| `picasa://downloadfeed?url=…` | album letöltése egy hírcsatorna-URL-ről (az album-lap „Download album" hivatkozása) | `0x004c5720` |

Az `importbutton` ág **külső URL-ről tölt be bővítményt** — ezért van rá
megerősítő kérdés.

---

## 6. Bizonyítottsági fok és ami NINCS MEG

**Megerősített:** a beállítás-kulcsok és a hozzájuk tartozó viselkedés, a
végpontlista, a WebDAV-válaszok elemei, a hirdetési rekord mezői, a
`text/plain` mezőlisták, a `picasa://` séma műveletei — mind kiolvasott
sztringek a megnevezett függvényekben.

**NINCS MEG:**

- **a hallgatózó port száma** (a sablonokban `%d`; a `ws2_32` ordinál szerint
  importálódik, ezért az index nem adja meg a `bind` helyét). A 80-as port
  csak a **WebDAV**-ághoz kötött, mérve (`0x005cb990`).
  **HATÓKÖRÖN KÍVÜL** — a PicasaPy nem épít hallgatózó kiszolgálót
  (ld. **#2023**), így a szám semmilyen döntést nem befolyásol.
- **az egyes végpontok pontos válasz-sémája** a fenti kettőn túl. Ugyanezért
  hatókörön kívül.

## 7. Mit visz ebből a PicasaPy

**A kiszolgálót magát nem** — az indoklás és a döntés a **#2023** jegyben.
Amit átveszünk: a 4. szakasz mezőlistáit **keresztellenőrzésnek** a saját
adatmodellünkhöz, és a `flip` negatív eredményét.
