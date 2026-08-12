# Picasa 3.9 bináris string-bányászat — eredmények

Forrás: eredeti Picasa 3.9 programmappa (`Picasa3.exe`, `npPicasa3.dll`,
`PicasaPhotoViewer.exe`, `qtsupport.dll`). Módszer: `strings -n 6` (ASCII) +
`strings -el -n 6` (UTF-16) minden fájlra, majd egy kiegészítő
`strings -n 2` menet a `Picasa3.exe`-n, mert a rövid (2–4 karakteres) szűrő-
azonosítók (`bw`, `sat`, `fill`, `tint`, `warm`, `glow`) a 6-os
minimumhosszal kiestek.

A `Picasa3.exe` **belső literál-táblái** (a `.rdata`-ban egymás mellett
sorakozó stringek) rendkívül informatívak: ezek nem UI-szövegek, hanem a
programban ténylegesen használt `.picasa.ini` kulcsnevek és szűrő-
azonosítók forráskód-szintű felsorolásai. A legfontosabb két tábla:

- **Szűrő-azonosító tábla** (a Creative Kit "4–5. fül" effektlistája,
  `Picasa3.exe` string-tartomány ~635100–635170, `-n 2` dump): innen jött a
  legtöbb új infó (lásd 1. pont).
- **Kép-/album-mezőnevek táblája** (`.picasa.ini` és a belső PMP-mezők közös
  eredete, string-tartomány ~630880–631220): innen jött a legtöbb új ini-kulcs
  (lásd 2. pont).
- **INI-író format-string blokk** (~638900 körül): `[encoding]`, `utf8=1`,
  `[Picasa]`, `name=%s`, `crop=rect64(%s)`, `star=yes`, `caption=%s`,
  `keywords=%s`, `IIDLIST_%s=%s` — ez a tényleges `WriteFile`-szerű kód
  formátumsztringje, tehát ez a legmegbízhatóbb forrás az írási formátumra.

---

## 1. SZŰRŐ/EFFEKT-LELTÁR

### A teljes belső effekt-azonosító tábla (egy tömbben található a `.exe`-ben)

```
Polaroid, MuseumMatte, DropShadow, RoundedEdges, Border, Comicize, Neon,
PencilSketch, FocalZoom, PicnikFocalPixelate, Pixelate, Matte, Vignette,
Soften, Boost, TwoTone, QuantizePalette, CrossProcess, NightVision, HeatMap,
Invert, Sixties, Orton, Cinemascope, HDR, Holga, Lomo, IR, radtint, dir_tint,
radsat, ansel, glow, glow2, radblur, sat, tint, PicnikTint, grain,
PicnikGrain, warm, sepia, unsharp, unsharp2
```

Ehhez külön csoportban (más rész, de szintén bare literál): `crop64`, `tilt`,
`bw`, `redo`, `enhance`, `autolight`, `autocolor`, `retouch`, `redeye=1;`,
`retouch=1;`, `picnik=1;`, `fill`, `finetune`, `finetune2`.

### (a) Az exe-ben megvan, de a spec (`filters-decoded.md` /
`picasa-ini-format.md`) NEM dokumentálja, vagy csak részben

| Talált azonosító | Kontextus a bináris tömbben | Megjegyzés |
|---|---|---|
| `RoundedEdges` | `Border`/`DropShadow` mellett | Önálló szűrő — a specben csak `Border` szerepel, ez talán a lekerekített sarok (esetleg `Border` egyik módja, esetleg önálló kulcs) |
| `Matte` | `MuseumMatte` és `Vignette` között | Külön azonosító `MuseumMatte`-tól — lehet a "Photo Matte" effekt önálló kulcsa |
| `NightVision` | `HeatMap`/`Invert` mellett | Teljesen hiányzik a specből (4. fül effektjei közül) |
| `radtint` | `dir_tint`/`radsat`/`radblur` mellett | Feltehetően a `dir_tint` radiális testvére (`rad`- előtag mint `radsat`, `radblur`) — a spec csak `dir_tint`-et ismeri |
| `grain` (v1) | közvetlenül `PicnikGrain` mellett, `tint`/`warm` társaságában | A spec csak `grain2`-t dokumentálja; ez az 1-es verzió (mint `unsharp`/`unsharp2`, `finetune`/`finetune2` minta) |
| `PicnikTint` / `PicnikGrain` | `tint`/`grain` mellett | Feltehetően korai/Picnik-korszakbeli belső alias — nem tudni, ír-e ilyen kulcsot valódi `.picasa.ini`-be, vagy csak UI-only |
| `PicnikFocalPixelate` | `FocalZoom`/`Pixelate` mellett | Hasonlóan bizonytalan eredetű, valószínűleg legacy alias |
| `picnik=1;` | `redeye=1;` / `retouch=1;` mellett, szintén `=1;` formátumban | **Új, eddig nem dokumentált filters-lánc-token** — lehet egy generikus jelző, ami akkor kerül a láncba, amikor bármilyen Creative Kit ("Picnik") effekt fut. Ellenőrzés célszerű valódi export-ini-kben. |

Ezek egyike sem ismert biztosan, hogy ténylegesen megjelenik-e élő
`.picasa.ini`-ben (lehet, hogy csak UI-menüpont-azonosítók) — de mivel
pontosan ugyanabban a tömbben és pontosan ugyanolyan alakban (nagybetűs
CamelCase vagy kisbetűs snake) szerepelnek, mint a már bizonyítottan
ini-kulcsként használt társaik (`Vignette`, `dir_tint`, `radsat`, `Border`,
`Boost` stb.), erős a gyanú, hogy ezek is valódi `filters=` tokenek.

### (b) A specben szereplő szűrők — MIND megtalálva az exe-ben (nincs elgépelés)

Ellenőrizve, egyenként, pontos (`-x`) egyezéssel: `crop64`, `tilt`, `redeye`,
`enhance`, `autolight`, `autocolor`, `retouch`, `finetune`, `finetune2`,
`unsharp`, `unsharp2`, `sepia`, `bw`, `warm`, `grain2`, `tint`, `sat`,
`radblur`, `glow2`, `glow` (v1 is!), `ansel`, `radsat`, `dir_tint`, `fill`,
`Vignette` (nagybetűs, ahogy a spec is jelzi), `Invert`, `Cinemascope`,
`Sixties`, `HeatMap`, `CrossProcess`, `QuantizePalette`, `TwoTone`, `Boost`,
`Soften`, `Pixelate`, `FocalZoom`, `PencilSketch`, `Neon`, `Comicize`,
`Border`, `DropShadow`, `MuseumMatte`, `Polaroid`, `IR`, `Lomo`, `Holga`,
`HDR`, `Orton`.

**Egyetlen elírás vagy hiányzó spec-tétel sem került elő ezen az oldalon** —
a specben lévő teljes effektlista helyesen van írva.

### Kisebb, de hasznos megerősítés

- A `filters-decoded.md` az 5. körben már külön mérte a `glow`-t (v1) a
  golden-verdikt táblában, de a `picasa-ini-format.md` fő táblázata csak
  `glow2`-t sorolja fel — az exe megerősíti, hogy `glow` (v1, param nélkül
  vagy más paraméterezéssel) önálló, létező token, érdemes felvenni a fő
  táblázatba is.

---

## 2. INI KULCS-LELTÁR

### `[encoding]` szekció — HIÁNYZIK A SPECBŐL (fontos találat)

Az író-kód format-string blokkjában szó szerint:

```
[encoding]
utf8=1
[Picasa]
name=%s
description=%s
location=%s
category=%s
date=%f
```

A `picasa-ini-format.md` **egyáltalán nem említi** a `[encoding]` szekciót,
pedig ez nyilvánvalóan az ini fájl egyik írt szekciója (`utf8=1` — jelzi,
hogy a fájl UTF-8 kódolású). Ezt fel kell venni a specbe, és a PicasaPy
írónak/olvasónak kezelnie kell (kompatibilitás miatt valószínűleg mindig ki
kell írni `utf8=1`-gyel, ha a fájl UTF-8).

### Kép-/album-mezőnevek táblája (belső mezőnév-tömb, valószínűleg PMP+ini közös eredet)

```
parent, filetype, fileflags, size, creation, modified, updated, width,
height, rotate, crop64, flipped, edit_width, edit_height, filters, text,
textactive, tags, edited, revertable, originslow, originfast, uid64,
aliasparents, colorspace, personalbumid, suggestionpersonalbumid,
facequality, facerect, deferredface, deferredregion, facerectdata,
personalbumrecs, personalbumrecvalues, personalbumrecs2,
personalbumrecvalues2, peoplealbumchecksum, tagdate, fdbhash, backuphash
```

majd egy másik közeli klaszterben:

```
keywords, star, yes, hidden, screensaver, geotag, faces, albumlist, moddate
```

A spec (`picasa-ini-format.md` `[<fájlnév.ext>]` táblázata) ezekből ismeri:
`star`, `caption`, `keywords`, `rotate`, `filters`, `redo`, `faces`,
`albums`, `crop`, `geotag`, `width`, `height`, `moddate`, `backuphash`,
`originhash`, `IIDLIST_<user>_lh`, `screensaver`, `text`, `textactive`.

**Hiányzik a specből** (valódi `.picasa.ini`-ben előfordulhatnak, vagy csak
belső PMP-mezők — ez a bináriból önmagában nem dönthető el biztosan):

| Kulcs | Megjegyzés |
|---|---|
| `hidden` | ugyanabban a klaszterben van, mint `star`/`screensaver`/`geotag` — valószínűleg valódi ini-kulcs ("elrejtett kép") |
| `albumlist` | az `albums` mellett, de attól eltérő névvel — tisztázandó, hogy ez ini-kulcs-e, vagy csak belső cache-mező |
| `flipped` | `rotate`/`crop64` mellett — a specben csak `rotate(N)` szerepel, `flipped` külön kulcsként/formátumként (`flipped(%d)` format-string is megvan) hiányzik |
| `edit_width`, `edit_height` | a `width`/`height` mellett — feltehetően a szerkesztett (crop utáni) méret cache-elése |
| `originslow`, `originfast` | `originhash` szomszédságában — kapcsolódhat a szerkesztési-lánc integritás-hasheléshez, de nem azonos az `originhash`-sal |
| `uid64` | webes egyedi azonosító, `IIDLIST_`-hez hasonló szerepű, de külön mező |
| `aliasparents` | tisztázatlan — talán duplikátum-/alias-kezelés |
| `colorspace` | RAW/színtér infó cache-elése |
| `personalbumid`, `suggestionpersonalbumid`, `personalbumrecs(2)`, `personalbumrecvalues(2)`, `peoplealbumchecksum` | arcfelismerés/„People"-albumok belső könyvelése — a 3. fázis (arcok) szempontjából releváns |
| `facequality`, `facerect`, `deferredface`, `deferredregion`, `facerectdata`, `tagdate`, `fdbhash` | arc-adatbázis mezők — a specben csak a `faces=` ini-kulcs van dokumentálva, ezek valószínűleg a `facetemplatesV2.db`/`.pmp` oldali belső mezők |
| `tags` | **közvetlenül a `textactive` után, `edited` előtt** — külön mező a `keywords`-től; lehet, hogy ez a PMP-oldali belső mezőnév ugyanarra az adatra, amit az ini `keywords=`-ként ír ki (kettős elnevezés) |
| `parent`, `filetype`, `fileflags`, `size`, `creation`, `modified`, `updated`, `edited`, `revertable` | döntően PMP/db3-oldali mezők (l. `pmp-database.md`), nem feltétlenül ini-kulcsok |

### `[Picasa]` szekció — verzió-kulcsok (hiányoznak a specből)

Külön klaszterben, `.picasa.ini`-hez közel:

```
P2category, contactsversion, frversion, gpsversion, colorspaceversion,
rawversion
```

A spec `[Picasa]`-táblázata csak `name`, `category`, `P2category`,
`<user>_lh`-t ismeri. A `contactsversion`/`frversion` (face-recognition
verzió?)/`gpsversion`/`colorspaceversion`/`rawversion` valószínűleg globális
verziószám-kulcsok (adatbázis-migrációhoz) — érdemes felvenni és
figyelmen kívül hagyni/megőrizni round-trip-ben, ha előfordulnak.

### `.album:<token>` szekció — megerősítve, nincs eltérés

A bináris tömb szó szerint: `.album:`, `token`, `name`, `description`,
`location`, `date`, `albums` — pontosan egyezik a specben leírt mezőkkel.

### `[Contacts2]` formátum — megerősítve

Az író-kód format-stringje `%s;%s;%s` (három mező pontosvesszővel), ami
összhangban van a spec `<person_id>=Név;;` alakjával (2. és 3. mező üresen
marad lokális kontaktnál). `[Contacts2]` és `Contacts2` szó szerint
megtalálható a `.exe`-ben, a `contacts.xml`-mezőkkel (`gphoto:personid2`,
`gphoto:fullname`, `gaia_id` stb.) együtt — ezek jó kiegészítés a
`pmp-database.md`-hez, ha az még nem fedi le.

### Videó-specifikus ini-kulcsok — hiányoznak a specből

```
moviestart=
movieend=
```

Feltehetően a `.picasa.ini`-ben videófájloknál a lejátszási/vágási pontokat
tárolják — nincs említve egyik specben sem.

### Író format-stringek (biztosan pontos szintaxis-referencia)

```
[%s]
%s=%s
[encoding]
utf8=1
[Picasa]
name=%s
description=%s
location=%s
category=%s
date=%f
flipped(0)
crop=rect64(%s)
%s=%d
star=yes
caption=%s
keywords=%s
IIDLIST_%s=%s
rotate(%d)
rotate(-1)
rotate(0)
rect64(
redeye=1;
retouch=1;
picnik=1;
filters=%s
```

Ezek szó szerinti egyezésben vannak a spec `crop=rect64(...)`, `rotate(N)`,
`star=yes`, `IIDLIST_<user>_lh` leírásaival — jó megerősítés, hogy a
PicasaPy jelenlegi feltételezései helyesek.

### Debug-webszerver mezőnevek (más elnevezés, ugyanaz az adat — csak érdekesség)

A beépített helyi "Picasa Debug" webszerver HTML-generáló format-stringjei
más neveket használnak, mint az ini: `filename=`, `origin=`, `cdate=%lf`,
`mdate=%lf`, `size=%d`, `rot=%d` (nem `rotate`), `flip=%d` (nem `flipped`),
`filters=%s`, `caption=%s`, `lat=%lf`, `long=%lf`, `uid64=`, `dbid=%s`,
`version=%d`. Ez megerősíti, hogy a belső (PMP) reprezentáció és az
`.picasa.ini` szóhasználata NEM mindig egyezik (pl. `rot`/`flip` vs.
`rotate`/`flipped`) — hasznos figyelmeztetés, ha valaki a bináris
mezőneveket közvetlenül próbálná ini-kulcsként értelmezni.

---

## 3. FÁJL-/DB-NEVEK

Az exe-ben szó szerint megtalálható fájl-/adatbázisnevek (csak azok,
amik ténylegesen előjönnek):

```
.picasa.ini
Picasa.ini          (a régi, korai verziójú név — megerősítve)
.picasaoriginals
Originals
Modified
contacts.xml
backup.xml
albums.db
bigthumbs.db
distims.db
facetemplatesV2.db
facetemplates_0.db
facetemplates_index.db
index-thumbs.db
makemoviecache.db
previews.db
profilephotos.db
thumbindex.db
thumbindex.tid
thumbs.db
thumbs2.db
thumbs_index.db
watchedfolders.txt
repository.dat
usernames.dat
starlist.txt
saverlist.txt
badfiles.txt
```

Fontos: a `.pmp` kiterjesztés **szó szerint nem** fordul elő a
`Picasa3.exe`-ben stringként (a `pmp-database.md` ezt a nevet feltehetően a
közösségi visszafejtésekből — pl. `skisoo/PicasaDBReader` — vette át, nem a
bináris string-tábláiból). Ez nem ellentmondás, csak jelzi, hogy a `.pmp`
elnevezés nem Google-eredetű belső név, hanem a reverse-engineering
közösség konvenciója — érdemes ezt egy lábjegyzetben a `pmp-database.md`-ben
is rögzíteni, hogy ne tűnjön hivatalos Google-terminológiának.

Új, a `pmp-database.md`-ben eddig (ellenőrzés nélkül) nem szereplő nevek,
amik érdemesek egy pillantásra: `distims.db`, `index-thumbs.db`,
`makemoviecache.db`, `profilephotos.db`, `thumbindex.tid`, `thumbs_index.db`,
`repository.dat`, `usernames.dat`, `starlist.txt`, `saverlist.txt`,
`badfiles.txt`.

A belső PMP-oszlopnevek (a `.pmp`-fájlok nevei is ezek szoktak lenni):
`catdata`, `catpri`, `albumdata`, `imagedata`, `albumcontactids`,
`albumpeoplechecksum` — ezek is megerősítik a `pmp-database.md` leírását
(nincs ellentmondás).

---

## 4. REGISTRY/OPCIÓK — figyelemre méltó kulcsok

Csak a beszédesebbek, teljesség igénye nélkül:

- `SOFTWARE\Google\Picasa\Picasa2\Preferences\` — a beállítások gyökere
- `KeywordVersion`, `IDPersist`, `geoview`, `FixShortPathNames`,
  `AsynchronousPersist` — belső DB/perzisztencia-jelzők
- `DigicamPictureThreshold`, `DigicamPictureThreshold2` — automatikus
  fotó-import küszöbértékek
- `ConfirmThresholdCount` — "sok kép megnyitása" megerősítő párbeszéd
  küszöbe
- `autobacklight` (`editpanel/autobacklight`) — önálló effekt-gomb/opció,
  ami **nem** egyezik az `autolight`-tal. **#567-ben tisztázva:** a natív
  render callback (`0x8f7cc0`) ugyanazt a Derítőfény-magot (`0x90ac20`)
  hívja, mint a `backlight`/`fill`, **fix 0,25** argumentummal — tehát nem
  adaptív képelemzés, hanem rögzített 25%-os derítőfény („Increases ambient
  lighting by 25%.", a kikommentezett UI-súgó szerint)
- `Preferences\HotFolders`, `ID_FILE_HOTFOLDERS_m` — "figyelt mappák"
  (watched folders) beállításai
- `ShowHidden`, `usefileloadcache`, `disposepreviews`,
  `Do unreasonably slow consistency checks`, `BenchmarkDB` — fejlesztői/
  diagnosztikai kapcsolók
- `ioqueue\slingshot.ioq`, `ioqueue\filesafe.ioq`, `ioqueue\albumsafe.ioq` —
  belső I/O-sor fájlok (nem regisztri, de kapcsolódó belső mechanizmus)

---

## 5. URL/PROTOKOLL

A `picasa://` egyéni protokoll parancsai szó szerint megtalálhatók:

```
picasa://
picasa://%s/
picasa://importbutton/?url=
picasa://showimg/?
picasa://showimgtmp/?
picasa://showimgtmp/?%d
picasa://uploadtogoogle
picasa://uploadtogoogle/?
```

Ezenkívül egy `lighthouse://` séma is van (`lighthouse://album/%s`,
`lighthouse://user`) — ez a Google szinkronizációs/upload alrendszer belső
neve ("Lighthouse"), eddig egyik specben sem szerepelt.

Egyik picasa.ini-specifikáció sem tárgyalja a `picasa://` protokollt — ez
jelenleg dokumentálatlan terület a PicasaPy specekben, de valószínűleg
alacsony prioritású (böngésző-plugin/webalbum-integráció, nem a
fájlformátum része).

---

## ELTÉRÉSEK a meglévő spechez képest (összefoglaló, cselekvésre kész)

1. **`[encoding]` szekció teljesen hiányzik a `picasa-ini-format.md`-ből.**
   Az exe bizonyítottan ír egy `[encoding]` szekciót `utf8=1` kulccsal. →
   **Fel kell venni a specbe**, és a PicasaPy-nak kezelnie (megőriznie,
   illetve UTF-8 fájlnál kiírnia) kell.
2. **Új, valószínűsíthetően valódi szűrő-azonosítók** a Creative Kit
   effekt-táblájában, amik nincsenek a `filters-decoded.md`-ben:
   `RoundedEdges`, `Matte`, `NightVision`, `radtint`, `grain` (v1, a
   `grain2` mellett), `picnik=1;` (önálló filters-token gyanúja). Ezeket
   érdemes egy jövő körben golden-exporttal tesztelni, hogy tényleg
   megjelennek-e élő `.picasa.ini`-ben.
3. **`glow` (v1) hiányzik a `picasa-ini-format.md` fő szűrőtáblájából**
   (csak a `glow2` szerepel ott) — pedig a `filters-decoded.md` már mérte,
   és az exe is önálló tokenként tartalmazza. → táblázat-kiegészítés.
4. **Új, dokumentálatlan `.picasa.ini` kép-kulcs-gyanúsak:** `hidden`,
   `flipped` (a `rotate(N)` mellett, külön `flipped(%d)` formátum-
   stringgel), `edit_width`, `edit_height`, `moviestart=`, `movieend=`.
   Ezek közül a `hidden` és a `flipped` a legvalószínűbb, hogy tényleg
   ini-kulcsként létezik (ugyanabban a klaszterben vannak, mint a már
   ismert `star`/`rotate`/`crop64`).
5. **`[Picasa]` szekció verzió-kulcsai hiányoznak a specből:**
   `contactsversion`, `frversion`, `gpsversion`, `colorspaceversion`,
   `rawversion` — javasolt felvenni "ismeretlen jelentésű, megőrzendő"
   jelzéssel.
6. **A `.pmp` kiterjesztés nem Google-eredetű belső elnevezés** — az exe-ben
   sehol nem fordul elő szó szerint; a `pmp-database.md`-ben érdemes
   lábjegyzetben jelezni, hogy ez közösségi (reverse-engineering)
   konvenció, nem hivatalos formátumnév.
7. **A specben szereplő teljes effekt- és ini-kulcs-lista NEM tartalmaz
   elgépelést** — minden ellenőrzött tétel pontosan (karakterre) egyezik az
   exe-ben talált stringgel. Ez megerősíti a meglévő kutatás
   megbízhatóságát.
8. Kisebb, inkább érdekesség: a beépített helyi debug-webszerver más
   mezőneveket használ (`rot`, `flip`, `cdate`, `mdate`) mint az ini
   (`rotate`, `flipped`, `creation`/`modified`) — nem ellentmondás, csak
   figyelmeztetés, hogy a belső PMP-terminológia és az ini-terminológia
   nem mindig azonos szóhasználatú.
