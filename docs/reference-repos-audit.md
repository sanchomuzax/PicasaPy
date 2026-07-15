# Referencia-repók audit (research-plan #5, #6)

Állapot: 2026-07-15. Az 5 repó a gitignore-olt `research/repos/` alá klónozva.

## Licenc-összefoglaló — KRITIKUS a kódátvételhez

| Repó | Licenc | Kód átvehető? |
|---|---|---|
| `skisoo/PicasaDBReader` (Java) | **MIT** | ✅ szabadon portolható (attribúcióval) |
| `vosbergw/picasa3meta` | GPL-3.0 (COPYING a csomagban) | ⚠️ csak ha a PicasaPy GPL-3.0 lesz |
| `vosbergw/metaSave` | GPL-3.0 | ⚠️ ugyanaz |
| `Philipp91/picasa2digikam` | GPL-3.0 | ⚠️ ugyanaz |
| `bufemc/picasa2xmp` | GPL-3.0 | ⚠️ ugyanaz |

**Következmény:** a *formátumtudás* nem szerzői jogvédett — a PMP-parsert saját
spec-jeinkből (docs/specs/) implementáljuk; kód-referenciának az MIT-licencű
PicasaDBReader használható. **Nyitott döntés: a PicasaPy saját licence** (ha
GPL-3.0-t választunk, a Python repókból is portolhatunk; ha MIT/Apache-t, akkor
csak a Java-ból + saját implementáció).

## picasa3meta audit (a "legjobb Python kiindulás" minősítés felülvizsgálata)

- **Python 2-only kód** (2012): `dict.has_key()`, `print` utasítások,
  bytes/str keverés a bináris olvasásban (`b == chr(0)` — Py3-on mindig False!),
  `except X, e` szintaxis, platformfüggő `array('L')` méret.
- Python 3.12 alatt **futtathatatlan**, a port a bináris olvasó részeknél
  gyakorlatilag újraírás.
- **Ítélet módosítva:** nem kód-kiindulás, hanem **formátum-dokumentáció**.
  A GPL miatt amúgy sem portolnánk vakon. A PMP-parsert nulláról írjuk meg
  a lenti, két független implementációból keresztvalidált spec alapján.

## Keresztvalidált PMP-formátum (pmpinfo.py ↔ PMPDB.java — egyezik ✅)

20 bájtos fejléc, little-endian:

| Offset | Méret | Érték |
|---|---|---|
| 0 | 4 | magic `0x3fcccccd` |
| 4 | 2 | mezőtípus (type1) |
| 6 | 2 | konstans `0x1332` |
| 8 | 4 | konstans `0x00000002` |
| 12 | 2 | mezőtípus ismétlés (= type1, ellenőrzés) |
| 14 | 2 | konstans `0x1332` |
| 16 | 4 | rekordszám (uint32) |

Mezőtípusok: `0x0`,`0x6` = null-terminált string (UTF-8); `0x1`,`0x7` = uint32;
`0x2` = double (dátumoszlopoknál **OLE variant time**: napok 1899-12-30-tól);
`0x3` = uint8; `0x4` = uint64; `0x5` = uint16.

`imagedata` ismert oszlopai (pmpinfo docstring): aliasparents, avgcolor,
backuphash, caption, colorspace, crop64, deferredface, edited, facequality,
facerect, facerectdata, fileflags, fileid, filetype, filters, flipped, geoview,
height, lat, long, onlinechecksum, originfast, originslow, peoplealbumchecksum,
personalbumid, personalbumrecs(2), personalbumrecvalues(2), redo, revertable,
rotate, suggestionpersonalbumid, suppress, tags, text, textactive, uid64,
width, `<user>_lhlist`.

## thumbindex.db formátum (thumbindex.py alapján)

- Fejléc: magic `0x40466666` (uint32) + bejegyzésszám (uint32).
- Bejegyzés: null- (vagy 0xff-) terminált név + **26 ismeretlen bájt** +
  uint32 szülőindex.
- Szülőindex `0xffffffff` = a bejegyzés maga könyvtár; a fájl teljes útvonala =
  `name[parentIndex] + name[i]`.
- **Üres nevű bejegyzés érvényes szülőindexszel = ARC-bejegyzés**: a szülőkép
  indexéhez tartozó arc-rekord (a PicasaFaces is erre épül). Üres név érvénytelen
  szülővel = törölt fájl (az index nem kerül újrafelhasználásra).

## picasa2digikam — modern minták (Python 3.10+)

- `rect64.py` + `rect64_test.py`: típusannotált, tesztelt dekóder. Két új
  formátum-tény, amit a spec-be átvezettünk:
  1. **A rect64 érték rövidülhet** — a Picasa elhagyja a vezető nullákat →
     dekódolás előtt `zfill(16)` kötelező.
  2. **EXIF-orientáció** (1/3/6/8) szerint a koordinátákat transzformálni kell
     megjelenítéskor/exportnál.
- `migrator.py`: contacts.xml előnyben az ini `[Contacts]`-szal szemben
  (pontosabb nevek); sérült ini-k kezelése figyelmeztetéssel.

## picasa2xmp / metaSave

- picasa2xmp: exiv2 + exiftool külső függőség; XMP MWG-RS sidecar generálás
  mintája (3. fázisban releváns). JPEG-nél az XMP a képbe megy, sidecar
  hivatalosan csak RAW-hoz — de digiKam/darktable JPEG-sidecart is olvas.
- metaSave: a picasa3meta példa-CLI-je; bejárási minta (photos fa → meta fa).

## Következő lépések

1. **PicasaPy licenc-döntés** (blokkolja: mennyit meríthetünk a GPL-kódból).
2. Saját `pmp` olvasó modul implementálása a fenti spec-ből (TDD-vel,
   golden-fájlokkal) — ehhez **kell egy valódi db3 tesztkészlet** (research-plan
   #5 nyitott kérdése: van-e régi Picasa-telepítésünk?).
3. rect64 dekóder: picasa2digikam tesztesetei mintaként (újraírva, nem másolva,
   amíg a licenc nincs eldöntve).
