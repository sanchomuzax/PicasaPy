# A Picasa metaadat-tulajdonságtáblája — a `BinaryMetadata` kulcstere

*Kelt: 2026-09-05 · jegy: #2375 (a #2304 mellékága) · forrás: Picasa 3.9.141.259*

A Picasa a kép metaadatait **egyetlen, egész számmal kulcsolt szótárba**
olvassa be (`BinaryMetadata`), és a program minden pontja — a beolvasó, a
webre töltés, a geocímke-olvasó — ebből a szótárból kérdez, EXIF- vagy
IPTC-szintaxis nélkül. Ez a lap megadja a **teljes kulcsteret**: melyik
szám melyik EXIF- vagy IPTC-mezőt jelenti.

Miért kellett: a #2304 kutatása kimutatta, hogy a `thumbindex` első
időbélyegét (a mappán belüli „Dátum" rendezés kulcsát) a beolvasó a
**`0x37`-es metaadat-tulajdonságból** tölti (`pmp-database.md` 10.3), de
hogy ez melyik dátummező, nem volt meg. Most megvan.

## 1. A szótár és a lekérdezői

| mi | cím |
|---|---|
| a szótár típusa (RTTI) | `BinaryMetadata` (típusleíró `0x00d402b4`); `ytVariantObject`-ből `dynamic_cast`-tal (`0x00639160` → `0x00c07db2`) |
| `GetString(kulcs)` | **`0x009f05c0`** — kulcs `edi`-ben, szótár `esi`-ben; hash-vödrök `[+0x18]`, modulus `[+0x10]`, csomópont: `next` `+0x00`, **kulcs `+0x08`**, érték `+0x10` |
| további lekérdezők, azonos alakkal | `0x009f0620`, `0x009f0690`, `0x009f0700` |
| „nincs ilyen kulcs" visszatérés | `9` (`0x009f05f0`, `0x009f0600`) |
| a szótár feltöltése a képfájlból | `0x00a34f20` + `0x00a357a0` (a `0x00a3xxxx` kép-metaadat modul) |
| forrásnév-sztring | `BinaryMetadata::GetString` (`0x00c8fd18` környéke) |

A `.text` teljes pásztázása szerint a négy lekérdezőnek **143 hívási helye**
van; ahol a kulcs közvetlen konstans, ott az alábbi táblákból olvasható ki.

## 2. ⭐ A KULCS = a tábla `id` mezője **+ 1**

A kulcstér **nem** azonos a táblák `id` mezőjével: minden kulcs **eggyel
nagyobb** (a `0` így „nincs tulajdonság"-ot jelent). Ez nem feltevés —
négy, egymástól független hívási hely dönti el, és a másik olvasat
mindegyiken értelmetlen:

| hívási hely | kulcsok | `+1` szerint | közvetlen olvasat szerint |
|---|---|---|---|
| `0x009f15e5`–`0x009f1606` (geocímke) | `0x8c`, majd `0x8d` **másik lekérdezőnek**, majd `0x8e` | GPS `0x0001` **GPSLatitudeRef** (ASCII 2) · GPS `0x0002` **GPSLatitude** (RATIONAL 3) · GPS `0x0003` **GPSLongitudeRef** (ASCII 2) — a szöveges kettő a `GetString`-en, a számsoros a `0x009f1250`-en | GPSLatitude-ot olvasna **szövegként**, a GPSLongitudeRef-et **számsorként** |
| `0x00794c44`, `0x00794c59` (`CPreparedDBImage`, webre töltés) | `0xa`, `0xb` egymás után, szövegként | `0x010f` **Make** + `0x0110` **Model** | `0x0110` Model + `0x0111` **StripOffsets** (LONG) szövegként |
| `0x00794c1d`, `0x00426b2e`, `0x00426f7d`, `0x0070e4a4` | `0x68` | `0xa420` **ImageUniqueID** (ASCII 33) | gyártói jegyzet `0x0001` (SHORT-tömb) szövegként |
| `0x009eb34b` | `0x1c` | `0x0132` **DateTime** (ASCII 20) | `0x013b` Artist |

*Bizonyítottsági fok: **megerősített**. A geocímke-hármas önmagában is
eldönti: a két ASCII-irányjelző a szöveges, a RATIONAL-hármas a számsoros
lekérdezőhöz megy — ez a `+1` olvasat mellett áll össze, a másik szerint
mindkettő rossz lekérdezőt kapna.*

## 3. A három kulcs, amiért a kutatás indult

| kulcs | mi ez | típus | hol használja a Picasa |
|---|---|---|---|
| **`0x37` (55)** | EXIF **`0x9003` DateTimeOriginal** (a felvétel ideje) | ASCII, 20 bájt | a beolvasó (`0x00427844`) → a `thumbindex` **1. időbélyege** ⇒ a mappán belüli „Dátum" rendezés kulcsa; a webre töltés (`0x00794c68`); `0x0070e459` |
| **`0x68` (104)** | EXIF **`0xa420` ImageUniqueID** | ASCII, 33 bájt | a beolvasó kétszer (`0x00426b2e`, `0x00426f7d`), a webre töltés, `0x0070e4a4` |
| **`0xe4` (228)** | **IPTC 2:120 Caption/Abstract** (a kép felirata) | 1…2000 bájt, ismételhető | a beolvasó (`0x00426ddd`), `0x005e7289` |

⇒ **A „Dátum" rendezés kulcsa az EXIF `DateTimeOriginal`** — nem a
`DateTimeDigitized` (`0x9004`), ami a szomszédos `id`-n ül és a `+1`
nélküli olvasat szerint jött volna ki.

### MIT AD MA — a mi kódunk (mérve)

| a Picasa kulcsa | mi ez | nálunk | fájl+sor |
|---|---|---|---|
| `0x37` | EXIF `0x9003` | **`_DATETIME_ORIGINAL_TAG = 36867`** (= `0x9003`) ✅ ugyanaz | `metadata/reader.py:41` |
| `0x68` | EXIF `0xa420` | **`_IMAGE_UNIQUE_ID_TAG = 42016`** (= `0xa420`) ✅ ugyanaz | `metadata/reader.py:59` |
| `0xe4` | IPTC 2:120 | **`_IPTC_CAPTION = (2, 120)`** ✅ ugyanaz | `metadata/reader.py:63` |
| `0xa` / `0xb` | EXIF `0x010f` / `0x0110` | `_MAKE_TAG = 271` / `_MODEL_TAG = 272` ✅ ugyanaz | `metadata/reader.py:42–43` |

⇒ **Termékteendő nincs.** A mi `taken_at`-ünk pontosan azt a mezőt olvassa,
amit az eredeti — a #2304 sorrend-eltérésének tehát **nem** a mezőválasztás
az oka (az ok a rögzítettség, ld. `pmp-database.md` 10.5).

## 4. A névtér-mező (`id` utáni második oszlop)

| érték | mi | bizonyíték |
|---:|---|---|
| 0 | IFD0 (TIFF alapcímkék) | a tartomány `0x0101`…`0x9286`, benne `0x0132` DateTime, `0x8769` ExifIFD-mutató, `0x8825` GPS-IFD-mutató |
| 1 | Exif IFD | `0x829a`…`0xa420` |
| 2 | **nincs egyetlen bejegyzése sem** | az `id` 103 → 104 átmenetnél a névtér 1-ről 3-ra ugrik |
| 3 | gyártói jegyzet — **Canon-minta** | `0x0006`/`0x0007`/`0x0009` ASCII, `0x0008`/`0x000c` LONG, `0x0095` ASCII ⇒ *feltételes* |
| 4 | gyártói jegyzet — **Nikon-minta** | `0x001d`/`0x00a0` ASCII, `0x0083`/`0x0098` , `0x00a7` LONG ⇒ *feltételes* |
| 5 | gyártói jegyzet — **Olympus-minta** | `0x2010`…`0x5000` almappa-mutatók ⇒ *feltételes* |
| 24 | GPS IFD | `0x0000` BYTE[4] verzió, `0x0001` ASCII[2], `0x0002` RATIONAL[3] … — szó szerint a GPS-IFD alakja |
| 25 | Interoperability IFD | `0x0001` ASCII, `0x0002` UNDEFINED[4], `0x1000`–`0x1002` |
| 26 | IFD1 (bélyegkép) | `0x0201`, `0x0202` |

## 5. ⚠️ Ütköző `id`-k az IPTC-táblában — ugyanaz a tulajdonság több forrásból

Az IPTC-tábla négy sora **nem** a saját sorszámát viseli, hanem egy már
használt `id`-t:

| IPTC | `id` | ugyanez az `id` az EXIF-táblában |
|---|---:|---|
| 2:60 (TimeCreated) | 55 | `0x9003` DateTimeOriginal |
| 2:62 (DigitalCreationDate) | 55 | ua. |
| 2:63 (DigitalCreationTime) | 56 | `0x9004` DateTimeDigitized |
| 2:65 (OriginatingProgram) | 56 | ua. |
| 2:85 (By-lineTitle) | 29 | `0x013c` HostComputer |
| 2:118 (Contact) | 40 | `0x83bb` IPTC-NAA |

⇒ **Ugyanaz a belső tulajdonság több forrásból is feltölthető** — az EXIF
és az IPTC ugyanabba a rekeszbe ír. Ez megmagyarázza, miért lehet egy
EXIF nélküli, de IPTC-vel ellátott képnek is „felvételi ideje" a Picasában.
*Bizonyítottsági fok: **erős** — a táblák tartalma mérve, de a beolvasási
sorrendet (ki írja felül kit) nem mértük ki.*

## 6. A TELJES tábla

**Az `id`-t a bináris adja, a kulcs = `id + 1` (2. szakasz). Az EXIF- és
IPTC-mezőnevek a nyilvános szabványból valók, nem a binárisból** — a
binárisból a **címszám** jön.

### 6.1 EXIF/TIFF-tábla — 176 bejegyzés, `0x00c782f0`-től, 28 bájtos rekordok

Rekord: `id` `+0x00` · névtér `+0x04` · EXIF-cím `+0x08` · típus `+0x0c` ·
`+0x10` · darabszám `+0x14` (`0xffffffff` = változó) · `+0x18`.

| kulcs | `id` | névtér | EXIF-cím | típus | darab | cím |
|---:|---:|---|---:|---|---:|---|
| **1** (`0x01`) | 0 | IFD0 (TIFF) | `0x0101` | LONG | 1 | `0x00c782f0` |
| **2** (`0x02`) | 1 | IFD0 (TIFF) | `0x0102` | SHORT | 3 | `0x00c7830c` |
| **3** (`0x03`) | 2 | IFD0 (TIFF) | `0x0103` | SHORT | 1 | `0x00c78328` |
| **4** (`0x04`) | 3 | IFD0 (TIFF) | `0x0106` | SHORT | 1 | `0x00c78344` |
| **5** (`0x05`) | 4 | IFD0 (TIFF) | `0x0107` | SHORT | 1 | `0x00c78360` |
| **6** (`0x06`) | 5 | IFD0 (TIFF) | `0x0108` | SHORT | 1 | `0x00c7837c` |
| **7** (`0x07`) | 6 | IFD0 (TIFF) | `0x0109` | SHORT | 1 | `0x00c78398` |
| **8** (`0x08`) | 7 | IFD0 (TIFF) | `0x010a` | SHORT | 1 | `0x00c783b4` |
| **9** (`0x09`) | 8 | IFD0 (TIFF) | `0x010e` | ASCII | — | `0x00c783d0` |
| **10** (`0x0a`) | 9 | IFD0 (TIFF) | `0x010f` | ASCII | — | `0x00c783ec` |
| **11** (`0x0b`) | 10 | IFD0 (TIFF) | `0x0110` | ASCII | — | `0x00c78408` |
| **12** (`0x0c`) | 11 | IFD0 (TIFF) | `0x0111` | LONG | — | `0x00c78424` |
| **13** (`0x0d`) | 12 | IFD0 (TIFF) | `0x0112` | SHORT | 1 | `0x00c78440` |
| **14** (`0x0e`) | 13 | IFD0 (TIFF) | `0x0115` | SHORT | 1 | `0x00c7845c` |
| **15** (`0x0f`) | 14 | IFD0 (TIFF) | `0x0116` | LONG | 1 | `0x00c78478` |
| **16** (`0x10`) | 15 | IFD0 (TIFF) | `0x0117` | LONG | — | `0x00c78494` |
| **17** (`0x11`) | 16 | IFD0 (TIFF) | `0x0118` | SHORT | 1 | `0x00c784b0` |
| **18** (`0x12`) | 17 | IFD0 (TIFF) | `0x0119` | SHORT | 1 | `0x00c784cc` |
| **19** (`0x13`) | 18 | IFD0 (TIFF) | `0x011a` | RATIONAL | 1 | `0x00c784e8` |
| **20** (`0x14`) | 19 | IFD0 (TIFF) | `0x011b` | RATIONAL | 1 | `0x00c78504` |
| **21** (`0x15`) | 20 | IFD0 (TIFF) | `0x011c` | SHORT | 1 | `0x00c78520` |
| **22** (`0x16`) | 21 | IFD0 (TIFF) | `0x0120` | LONG | — | `0x00c7853c` |
| **23** (`0x17`) | 22 | IFD0 (TIFF) | `0x0121` | LONG | — | `0x00c78558` |
| **24** (`0x18`) | 23 | IFD0 (TIFF) | `0x0122` | SHORT | 1 | `0x00c78574` |
| **25** (`0x19`) | 24 | IFD0 (TIFF) | `0x0123` | SHORT | — | `0x00c78590` |
| **26** (`0x1a`) | 25 | IFD0 (TIFF) | `0x0128` | SHORT | 1 | `0x00c785ac` |
| **27** (`0x1b`) | 26 | IFD0 (TIFF) | `0x0131` | ASCII | — | `0x00c785c8` |
| **28** (`0x1c`) | 27 | IFD0 (TIFF) | `0x0132` | ASCII | 20 | `0x00c785e4` |
| **29** (`0x1d`) | 28 | IFD0 (TIFF) | `0x013b` | ASCII | — | `0x00c78600` |
| **30** (`0x1e`) | 29 | IFD0 (TIFF) | `0x013c` | ASCII | — | `0x00c7861c` |
| **31** (`0x1f`) | 30 | IFD0 (TIFF) | `0x013e` | RATIONAL | 2 | `0x00c78638` |
| **32** (`0x20`) | 31 | IFD0 (TIFF) | `0x013f` | RATIONAL | 6 | `0x00c78654` |
| **33** (`0x21`) | 32 | IFD0 (TIFF) | `0x0140` | SHORT | — | `0x00c78670` |
| **34** (`0x22`) | 33 | IFD0 (TIFF) | `0x0152` | SHORT | — | `0x00c7868c` |
| **35** (`0x23`) | 34 | IFD0 (TIFF) | `0x0211` | RATIONAL | 3 | `0x00c786a8` |
| **36** (`0x24`) | 35 | IFD0 (TIFF) | `0x0212` | SHORT | 2 | `0x00c786c4` |
| **37** (`0x25`) | 36 | IFD0 (TIFF) | `0x0213` | SHORT | 1 | `0x00c786e0` |
| **38** (`0x26`) | 37 | IFD0 (TIFF) | `0x0214` | RATIONAL | 6 | `0x00c786fc` |
| **39** (`0x27`) | 38 | IFD0 (TIFF) | `0x02bc` | UNDEFINED | — | `0x00c78718` |
| **40** (`0x28`) | 39 | IFD0 (TIFF) | `0x8298` | ASCII | — | `0x00c78734` |
| **41** (`0x29`) | 40 | IFD0 (TIFF) | `0x83bb` | UNDEFINED | — | `0x00c78750` |
| **42** (`0x2a`) | 41 | IFD0 (TIFF) | `0x8649` | UNDEFINED | — | `0x00c7876c` |
| **43** (`0x2b`) | 42 | IFD0 (TIFF) | `0x8769` | LONG | 1 | `0x00c78788` |
| **44** (`0x2c`) | 43 | IFD0 (TIFF) | `0x8773` | UNDEFINED | — | `0x00c787a4` |
| **45** (`0x2d`) | 44 | IFD0 (TIFF) | `0x8825` | LONG | 1 | `0x00c787c0` |
| **46** (`0x2e`) | 45 | IFD0 (TIFF) | `0x9286` | ASCII | — | `0x00c787dc` |
| **47** (`0x2f`) | 46 | Exif IFD | `0x829a` | RATIONAL | 1 | `0x00c787f8` |
| **48** (`0x30`) | 47 | Exif IFD | `0x829d` | RATIONAL | 1 | `0x00c78814` |
| **49** (`0x31`) | 48 | Exif IFD | `0x8822` | SHORT | 1 | `0x00c78830` |
| **50** (`0x32`) | 49 | Exif IFD | `0x8824` | ASCII | — | `0x00c7884c` |
| **51** (`0x33`) | 50 | Exif IFD | `0x8827` | SHORT | — | `0x00c78868` |
| **52** (`0x34`) | 51 | Exif IFD | `0x8828` | UNDEFINED | 1 | `0x00c78884` |
| **53** (`0x35`) | 52 | Exif IFD | `0x882a` | SHORT | 1 | `0x00c788a0` |
| **54** (`0x36`) | 53 | Exif IFD | `0x9000` | UNDEFINED | 4 | `0x00c788bc` |
| **55** (`0x37`) | 54 | Exif IFD | `0x9003` | ASCII | 20 | `0x00c788d8` |
| **56** (`0x38`) | 55 | Exif IFD | `0x9004` | ASCII | 20 | `0x00c788f4` |
| **57** (`0x39`) | 56 | Exif IFD | `0x9101` | UNDEFINED | 1 | `0x00c78910` |
| **58** (`0x3a`) | 57 | Exif IFD | `0x9102` | RATIONAL | 1 | `0x00c7892c` |
| **59** (`0x3b`) | 58 | Exif IFD | `0x9201` | SRATIONAL | 1 | `0x00c78948` |
| **60** (`0x3c`) | 59 | Exif IFD | `0x9202` | RATIONAL | 1 | `0x00c78964` |
| **61** (`0x3d`) | 60 | Exif IFD | `0x9203` | SRATIONAL | 1 | `0x00c78980` |
| **62** (`0x3e`) | 61 | Exif IFD | `0x9204` | SRATIONAL | 1 | `0x00c7899c` |
| **63** (`0x3f`) | 62 | Exif IFD | `0x9205` | RATIONAL | 1 | `0x00c789b8` |
| **64** (`0x40`) | 63 | Exif IFD | `0x9206` | RATIONAL | 1 | `0x00c789d4` |
| **65** (`0x41`) | 64 | Exif IFD | `0x9207` | SHORT | 1 | `0x00c789f0` |
| **66** (`0x42`) | 65 | Exif IFD | `0x9208` | SHORT | 1 | `0x00c78a0c` |
| **67** (`0x43`) | 66 | Exif IFD | `0x9209` | SHORT | 1 | `0x00c78a28` |
| **68** (`0x44`) | 67 | Exif IFD | `0x920a` | RATIONAL | 1 | `0x00c78a44` |
| **69** (`0x45`) | 68 | Exif IFD | `0x9214` | SHORT | 4 | `0x00c78a60` |
| **70** (`0x46`) | 69 | Exif IFD | `0x927c` | UNDEFINED | — | `0x00c78a7c` |
| **71** (`0x47`) | 70 | Exif IFD | `0x9286` | UNDEFINED | — | `0x00c78a98` |
| **72** (`0x48`) | 71 | Exif IFD | `0x9290` | ASCII | — | `0x00c78ab4` |
| **73** (`0x49`) | 72 | Exif IFD | `0x9291` | ASCII | — | `0x00c78ad0` |
| **74** (`0x4a`) | 73 | Exif IFD | `0x9292` | ASCII | — | `0x00c78aec` |
| **75** (`0x4b`) | 74 | Exif IFD | `0xa000` | UNDEFINED | 1 | `0x00c78b08` |
| **76** (`0x4c`) | 75 | Exif IFD | `0xa001` | SHORT | 1 | `0x00c78b24` |
| **77** (`0x4d`) | 76 | Exif IFD | `0xa002` | LONG | 1 | `0x00c78b40` |
| **78** (`0x4e`) | 77 | Exif IFD | `0xa003` | LONG | 1 | `0x00c78b5c` |
| **79** (`0x4f`) | 78 | Exif IFD | `0xa004` | ASCII | 13 | `0x00c78b78` |
| **80** (`0x50`) | 79 | Exif IFD | `0xa005` | LONG | 1 | `0x00c78b94` |
| **81** (`0x51`) | 80 | Exif IFD | `0xa20b` | RATIONAL | 1 | `0x00c78bb0` |
| **82** (`0x52`) | 81 | Exif IFD | `0xa20c` | UNDEFINED | 1 | `0x00c78bcc` |
| **83** (`0x53`) | 82 | Exif IFD | `0xa20e` | RATIONAL | 1 | `0x00c78be8` |
| **84** (`0x54`) | 83 | Exif IFD | `0xa20f` | RATIONAL | 1 | `0x00c78c04` |
| **85** (`0x55`) | 84 | Exif IFD | `0xa210` | SHORT | 1 | `0x00c78c20` |
| **86** (`0x56`) | 85 | Exif IFD | `0xa214` | SHORT | 2 | `0x00c78c3c` |
| **87** (`0x57`) | 86 | Exif IFD | `0xa215` | RATIONAL | 1 | `0x00c78c58` |
| **88** (`0x58`) | 87 | Exif IFD | `0xa217` | SHORT | 1 | `0x00c78c74` |
| **89** (`0x59`) | 88 | Exif IFD | `0xa300` | UNDEFINED | 1 | `0x00c78c90` |
| **90** (`0x5a`) | 89 | Exif IFD | `0xa301` | UNDEFINED | 1 | `0x00c78cac` |
| **91** (`0x5b`) | 90 | Exif IFD | `0xa302` | UNDEFINED | 1 | `0x00c78cc8` |
| **92** (`0x5c`) | 91 | Exif IFD | `0xa401` | SHORT | 1 | `0x00c78ce4` |
| **93** (`0x5d`) | 92 | Exif IFD | `0xa402` | SHORT | 1 | `0x00c78d00` |
| **94** (`0x5e`) | 93 | Exif IFD | `0xa403` | SHORT | 1 | `0x00c78d1c` |
| **95** (`0x5f`) | 94 | Exif IFD | `0xa404` | RATIONAL | 1 | `0x00c78d38` |
| **96** (`0x60`) | 95 | Exif IFD | `0xa405` | SHORT | 1 | `0x00c78d54` |
| **97** (`0x61`) | 96 | Exif IFD | `0xa406` | SHORT | 1 | `0x00c78d70` |
| **98** (`0x62`) | 97 | Exif IFD | `0xa407` | SHORT | 1 | `0x00c78d8c` |
| **99** (`0x63`) | 98 | Exif IFD | `0xa408` | SHORT | 1 | `0x00c78da8` |
| **100** (`0x64`) | 99 | Exif IFD | `0xa409` | SHORT | 1 | `0x00c78dc4` |
| **101** (`0x65`) | 100 | Exif IFD | `0xa40a` | SHORT | 1 | `0x00c78de0` |
| **102** (`0x66`) | 101 | Exif IFD | `0xa40b` | UNDEFINED | 1 | `0x00c78dfc` |
| **103** (`0x67`) | 102 | Exif IFD | `0xa40c` | SHORT | 1 | `0x00c78e18` |
| **104** (`0x68`) | 103 | Exif IFD | `0xa420` | ASCII | 33 | `0x00c78e34` |
| **105** (`0x69`) | 104 | gyártói (Canon-minta) | `0x0001` | SHORT | — | `0x00c78e50` |
| **106** (`0x6a`) | 105 | gyártói (Canon-minta) | `0x0002` | SHORT | — | `0x00c78e6c` |
| **107** (`0x6b`) | 106 | gyártói (Canon-minta) | `0x0004` | SHORT | — | `0x00c78e88` |
| **108** (`0x6c`) | 107 | gyártói (Canon-minta) | `0x0006` | ASCII | — | `0x00c78ea4` |
| **109** (`0x6d`) | 108 | gyártói (Canon-minta) | `0x0007` | ASCII | — | `0x00c78ec0` |
| **110** (`0x6e`) | 109 | gyártói (Canon-minta) | `0x0008` | LONG | 1 | `0x00c78edc` |
| **111** (`0x6f`) | 110 | gyártói (Canon-minta) | `0x0009` | ASCII | — | `0x00c78ef8` |
| **112** (`0x70`) | 111 | gyártói (Canon-minta) | `0x000c` | LONG | 1 | `0x00c78f14` |
| **113** (`0x71`) | 112 | gyártói (Canon-minta) | `0x001e` | LONG | 1 | `0x00c78f30` |
| **114** (`0x72`) | 113 | gyártói (Canon-minta) | `0x0095` | ASCII | — | `0x00c78f4c` |
| **115** (`0x73`) | 114 | gyártói (Nikon-minta) | `0x0011` | LONG | 1 | `0x00c78f68` |
| **116** (`0x74`) | 115 | gyártói (Nikon-minta) | `0x001d` | ASCII | — | `0x00c78f84` |
| **117** (`0x75`) | 116 | gyártói (Nikon-minta) | `0x0083` | SHORT | 1 | `0x00c78fa0` |
| **118** (`0x76`) | 117 | gyártói (Nikon-minta) | `0x0098` | SHORT | 1 | `0x00c78fbc` |
| **119** (`0x77`) | 118 | gyártói (Nikon-minta) | `0x00a0` | ASCII | — | `0x00c78fd8` |
| **120** (`0x78`) | 119 | gyártói (Nikon-minta) | `0x00a7` | LONG | 1 | `0x00c78ff4` |
| **121** (`0x79`) | 120 | gyártói (Olympus-minta) | `0x2010` | LONG | 1 | `0x00c79010` |
| **122** (`0x7a`) | 121 | gyártói (Olympus-minta) | `0x2020` | LONG | 1 | `0x00c7902c` |
| **123** (`0x7b`) | 122 | gyártói (Olympus-minta) | `0x2030` | LONG | 1 | `0x00c79048` |
| **124** (`0x7c`) | 123 | gyártói (Olympus-minta) | `0x2031` | LONG | 1 | `0x00c79064` |
| **125** (`0x7d`) | 124 | gyártói (Olympus-minta) | `0x2040` | LONG | 1 | `0x00c79080` |
| **126** (`0x7e`) | 125 | gyártói (Olympus-minta) | `0x2050` | LONG | 1 | `0x00c7909c` |
| **127** (`0x7f`) | 126 | gyártói (Olympus-minta) | `0x2100` | LONG | 1 | `0x00c790b8` |
| **128** (`0x80`) | 127 | gyártói (Olympus-minta) | `0x2200` | LONG | 1 | `0x00c790d4` |
| **129** (`0x81`) | 128 | gyártói (Olympus-minta) | `0x2300` | LONG | 1 | `0x00c790f0` |
| **130** (`0x82`) | 129 | gyártói (Olympus-minta) | `0x2400` | LONG | 1 | `0x00c7910c` |
| **131** (`0x83`) | 130 | gyártói (Olympus-minta) | `0x2500` | LONG | 1 | `0x00c79128` |
| **132** (`0x84`) | 131 | gyártói (Olympus-minta) | `0x2600` | LONG | 1 | `0x00c79144` |
| **133** (`0x85`) | 132 | gyártói (Olympus-minta) | `0x2700` | LONG | 1 | `0x00c79160` |
| **134** (`0x86`) | 133 | gyártói (Olympus-minta) | `0x2800` | LONG | 1 | `0x00c7917c` |
| **135** (`0x87`) | 134 | gyártói (Olympus-minta) | `0x2900` | LONG | 1 | `0x00c79198` |
| **136** (`0x88`) | 135 | gyártói (Olympus-minta) | `0x3000` | LONG | 1 | `0x00c791b4` |
| **137** (`0x89`) | 136 | gyártói (Olympus-minta) | `0x4000` | LONG | 1 | `0x00c791d0` |
| **138** (`0x8a`) | 137 | gyártói (Olympus-minta) | `0x5000` | LONG | 1 | `0x00c791ec` |
| **139** (`0x8b`) | 138 | GPS IFD | `0x0000` | BYTE | 4 | `0x00c79208` |
| **140** (`0x8c`) | 139 | GPS IFD | `0x0001` | ASCII | 2 | `0x00c79224` |
| **141** (`0x8d`) | 140 | GPS IFD | `0x0002` | RATIONAL | 3 | `0x00c79240` |
| **142** (`0x8e`) | 141 | GPS IFD | `0x0003` | ASCII | 2 | `0x00c7925c` |
| **143** (`0x8f`) | 142 | GPS IFD | `0x0004` | RATIONAL | 3 | `0x00c79278` |
| **144** (`0x90`) | 143 | GPS IFD | `0x0005` | BYTE | 1 | `0x00c79294` |
| **145** (`0x91`) | 144 | GPS IFD | `0x0006` | RATIONAL | 1 | `0x00c792b0` |
| **146** (`0x92`) | 145 | GPS IFD | `0x0007` | RATIONAL | 3 | `0x00c792cc` |
| **147** (`0x93`) | 146 | GPS IFD | `0x0008` | ASCII | — | `0x00c792e8` |
| **148** (`0x94`) | 147 | GPS IFD | `0x0009` | ASCII | 2 | `0x00c79304` |
| **149** (`0x95`) | 148 | GPS IFD | `0x000a` | ASCII | 2 | `0x00c79320` |
| **150** (`0x96`) | 149 | GPS IFD | `0x000b` | RATIONAL | 1 | `0x00c7933c` |
| **151** (`0x97`) | 150 | GPS IFD | `0x000c` | ASCII | 2 | `0x00c79358` |
| **152** (`0x98`) | 151 | GPS IFD | `0x000d` | RATIONAL | 1 | `0x00c79374` |
| **153** (`0x99`) | 152 | GPS IFD | `0x000e` | ASCII | 2 | `0x00c79390` |
| **154** (`0x9a`) | 153 | GPS IFD | `0x000f` | RATIONAL | 1 | `0x00c793ac` |
| **155** (`0x9b`) | 154 | GPS IFD | `0x0010` | ASCII | 2 | `0x00c793c8` |
| **156** (`0x9c`) | 155 | GPS IFD | `0x0011` | RATIONAL | 1 | `0x00c793e4` |
| **157** (`0x9d`) | 156 | GPS IFD | `0x0012` | ASCII | — | `0x00c79400` |
| **158** (`0x9e`) | 157 | GPS IFD | `0x0013` | ASCII | 2 | `0x00c7941c` |
| **159** (`0x9f`) | 158 | GPS IFD | `0x0014` | RATIONAL | 3 | `0x00c79438` |
| **160** (`0xa0`) | 159 | GPS IFD | `0x0015` | ASCII | 2 | `0x00c79454` |
| **161** (`0xa1`) | 160 | GPS IFD | `0x0016` | RATIONAL | 3 | `0x00c79470` |
| **162** (`0xa2`) | 161 | GPS IFD | `0x0017` | ASCII | 2 | `0x00c7948c` |
| **163** (`0xa3`) | 162 | GPS IFD | `0x0018` | RATIONAL | 1 | `0x00c794a8` |
| **164** (`0xa4`) | 163 | GPS IFD | `0x0019` | ASCII | 2 | `0x00c794c4` |
| **165** (`0xa5`) | 164 | GPS IFD | `0x001a` | RATIONAL | 1 | `0x00c794e0` |
| **166** (`0xa6`) | 165 | GPS IFD | `0x001b` | UNDEFINED | — | `0x00c794fc` |
| **167** (`0xa7`) | 166 | GPS IFD | `0x001c` | UNDEFINED | — | `0x00c79518` |
| **168** (`0xa8`) | 167 | GPS IFD | `0x001d` | ASCII | 11 | `0x00c79534` |
| **169** (`0xa9`) | 168 | GPS IFD | `0x001e` | SHORT | 1 | `0x00c79550` |
| **170** (`0xaa`) | 169 | Interoperability IFD | `0x0001` | ASCII | — | `0x00c7956c` |
| **171** (`0xab`) | 170 | Interoperability IFD | `0x0002` | UNDEFINED | 4 | `0x00c79588` |
| **172** (`0xac`) | 171 | Interoperability IFD | `0x1000` | ASCII | — | `0x00c795a4` |
| **173** (`0xad`) | 172 | Interoperability IFD | `0x1001` | LONG | 1 | `0x00c795c0` |
| **174** (`0xae`) | 173 | Interoperability IFD | `0x1002` | LONG | 1 | `0x00c795dc` |
| **175** (`0xaf`) | 174 | IFD1 (bélyegkép) | `0x0201` | LONG | 1 | `0x00c795f8` |
| **176** (`0xb0`) | 175 | IFD1 (bélyegkép) | `0x0202` | LONG | 1 | `0x00c79614` |

### 6.2 IPTC-tábla — 55 bejegyzés, `0x00c77c24`-től, 20 bájtos rekordok

Rekord: `id` `+0x00` · IPTC-azonosító `+0x04` (kis-endián `02 <adathalmaz>`)
· minimális hossz `+0x08` · maximális hossz `+0x0c` · ismételhető `+0x10`.

*(A hosszkorlátok az IPTC IIM szabvány értékei — pl. 2:120 Caption/Abstract
maximuma 2000, 2:122 Writer/Editor maximuma 32 —, ami önmagában is
igazolja, hogy a `+0x04` mező IPTC-adathalmaz-szám.)*


| kulcs | `id` | IPTC | min | max | ismételhető | cím |
|---:|---:|---|---:|---:|:--:|---|
| **191** (`0xbf`) | 190 | 2:0 | 2 | 2 | nem | `0x00c77c24` |
| **192** (`0xc0`) | 191 | 2:3 | 3 | 67 | nem | `0x00c77c38` |
| **193** (`0xc1`) | 192 | 2:4 | 4 | 68 | nem | `0x00c77c4c` |
| **194** (`0xc2`) | 193 | 2:5 | 1 | 64 | igen | `0x00c77c60` |
| **195** (`0xc3`) | 194 | 2:7 | 1 | 64 | igen | `0x00c77c74` |
| **196** (`0xc4`) | 195 | 2:8 | 2 | 2 | igen | `0x00c77c88` |
| **197** (`0xc5`) | 196 | 2:10 | 1 | 1 | igen | `0x00c77c9c` |
| **198** (`0xc6`) | 197 | 2:12 | 13 | 236 | igen | `0x00c77cb0` |
| **199** (`0xc7`) | 198 | 2:15 | 1 | 3 | igen | `0x00c77cc4` |
| **200** (`0xc8`) | 199 | 2:20 | 1 | 32 | igen | `0x00c77cd8` |
| **201** (`0xc9`) | 200 | 2:22 | 1 | 32 | nem | `0x00c77cec` |
| **202** (`0xca`) | 201 | 2:25 | 1 | 64 | igen | `0x00c77d00` |
| **203** (`0xcb`) | 202 | 2:26 | 3 | 3 | nem | `0x00c77d14` |
| **204** (`0xcc`) | 203 | 2:27 | 1 | 64 | igen | `0x00c77d28` |
| **205** (`0xcd`) | 204 | 2:30 | 8 | 8 | nem | `0x00c77d3c` |
| **206** (`0xce`) | 205 | 2:35 | 11 | 11 | nem | `0x00c77d50` |
| **207** (`0xcf`) | 206 | 2:37 | 8 | 8 | nem | `0x00c77d64` |
| **208** (`0xd0`) | 207 | 2:38 | 11 | 11 | nem | `0x00c77d78` |
| **209** (`0xd1`) | 208 | 2:40 | 1 | 256 | igen | `0x00c77d8c` |
| **210** (`0xd2`) | 209 | 2:42 | 2 | 2 | nem | `0x00c77da0` |
| **211** (`0xd3`) | 210 | 2:45 | 1 | 10 | nem | `0x00c77db4` |
| **212** (`0xd4`) | 211 | 2:47 | 8 | 8 | nem | `0x00c77dc8` |
| **213** (`0xd5`) | 212 | 2:50 | 8 | 8 | nem | `0x00c77ddc` |
| **214** (`0xd6`) | 213 | 2:55 | 8 | 8 | nem | `0x00c77df0` |
| **56** (`0x38`) | 55 | 2:60 | 11 | 11 | nem | `0x00c77e04` |
| **56** (`0x38`) | 55 | 2:62 | 8 | 8 | nem | `0x00c77e18` |
| **57** (`0x39`) | 56 | 2:63 | 11 | 11 | nem | `0x00c77e2c` |
| **57** (`0x39`) | 56 | 2:65 | 1 | 32 | igen | `0x00c77e40` |
| **215** (`0xd7`) | 214 | 2:70 | 1 | 10 | nem | `0x00c77e54` |
| **216** (`0xd8`) | 215 | 2:75 | 1 | 1 | nem | `0x00c77e68` |
| **217** (`0xd9`) | 216 | 2:80 | 1 | 32 | igen | `0x00c77e7c` |
| **30** (`0x1e`) | 29 | 2:85 | 1 | 32 | igen | `0x00c77e90` |
| **218** (`0xda`) | 217 | 2:90 | 1 | 32 | igen | `0x00c77ea4` |
| **219** (`0xdb`) | 218 | 2:92 | 1 | 32 | igen | `0x00c77eb8` |
| **220** (`0xdc`) | 219 | 2:95 | 1 | 32 | igen | `0x00c77ecc` |
| **221** (`0xdd`) | 220 | 2:100 | 3 | 3 | igen | `0x00c77ee0` |
| **222** (`0xde`) | 221 | 2:101 | 1 | 64 | igen | `0x00c77ef4` |
| **223** (`0xdf`) | 222 | 2:103 | 1 | 32 | igen | `0x00c77f08` |
| **224** (`0xe0`) | 223 | 2:105 | 1 | 256 | igen | `0x00c77f1c` |
| **225** (`0xe1`) | 224 | 2:110 | 1 | 32 | igen | `0x00c77f30` |
| **226** (`0xe2`) | 225 | 2:115 | 1 | 32 | igen | `0x00c77f44` |
| **227** (`0xe3`) | 226 | 2:116 | 1 | 128 | igen | `0x00c77f58` |
| **41** (`0x29`) | 40 | 2:118 | 1 | 128 | igen | `0x00c77f6c` |
| **228** (`0xe4`) | 227 | 2:120 | 1 | 2000 | igen | `0x00c77f80` |
| **229** (`0xe5`) | 228 | 2:122 | 1 | 32 | igen | `0x00c77f94` |
| **230** (`0xe6`) | 229 | 2:125 | 7360 | 7360 | nem | `0x00c77fa8` |
| **231** (`0xe7`) | 230 | 2:127 | 1 | 65535 | nem | `0x00c77fbc` |
| **232** (`0xe8`) | 231 | 2:130 | 2 | 2 | nem | `0x00c77fd0` |
| **233** (`0xe9`) | 232 | 2:131 | 1 | 1 | nem | `0x00c77fe4` |
| **234** (`0xea`) | 233 | 2:135 | 2 | 3 | nem | `0x00c77ff8` |
| **235** (`0xeb`) | 234 | 2:150 | 2 | 2 | nem | `0x00c7800c` |
| **236** (`0xec`) | 235 | 2:151 | 6 | 6 | nem | `0x00c78020` |
| **237** (`0xed`) | 236 | 2:152 | 2 | 2 | nem | `0x00c78034` |
| **238** (`0xee`) | 237 | 2:153 | 6 | 6 | nem | `0x00c78048` |
| **239** (`0xef`) | 238 | 2:154 | 1 | 64 | nem | `0x00c7805c` |

## 7. Nyitott kérdések mérlege

`0 nyílt · 4 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| melyik mező a `0x37` (55) | **LEZÁRVA** — EXIF `0x9003` DateTimeOriginal (2., 3. szakasz) |
| melyik mező a `0x68` (104) és a `0xe4` (228) | **LEZÁRVA** — `0xa420` ImageUniqueID, illetve IPTC 2:120 Caption/Abstract |
| ugyanazt a mezőt olvassuk-e | **LEZÁRVA** — igen, mérve (`metadata/reader.py:41`, `:59`, `:63`) |
| mi a kulcstér egésze | **LEZÁRVA** — 176 EXIF + 55 IPTC bejegyzés, teljes egészében kiírva (6. szakasz) |
| a gyártói névterek (3/4/5) pontos gyártója | **HATÓKÖRÖN KÍVÜL** — a címminták alapján Canon/Nikon/Olympus, de a megerősítéshez a gyártói jegyzet-parszolót kellene kimérni, és a termékben gyártói jegyzetet nem olvasunk (a `metadata/reader.py` a szabványos EXIF/IPTC mezőkre szorítkozik) |

## 8. Amit KIZÁRTAM

- **Hogy a kulcs közvetlenül a tábla `id` mezője volna** (`+1` nélkül) — a
  2. szakasz négy hívási helye mindegyiken értelmetlen olvasatot adna.
- **Hogy a kulcsok EXIF-címszámok volnának** — a `DateTimeOriginal` EXIF
  száma `0x9003` = 36867, a kulcs `0x37` = 55.
- **Hogy az `id` a nyilvános EXIF-tagszám valamilyen tömörítése volna** —
  az `id` egyszerű, hézagmentes sorszám a tábla sorrendjében (0…175).
- **Hogy a `0xe4` az EXIF-táblában volna** — a tábla `id`-je 175-nél véget
  ér; a 228-as az IPTC-táblában van.

---

## 9. ⛳ Az OBJEKTÍV-tábla: KÉT tábla, KÉT rekordalak (2026-09-15, #3121)

*Forrás: `Picasa3.exe` 3.7 (10 160 456 bájt). A nevek szövegblokkja
`0x008da958`–`0x008dfd0c` (fájl-offszet; VA = `+0x400000`), a Nikon
mutató-tábla `0x00c7b230`–`0x00c7c5b0` (VA), a Canon-rekord példája
`0x00c79c9c` (VA). Minden szám bájtszintű pásztázásból.*

A #3121 első lépése a tábla **határainak és szerkezetének** kimérése volt —
a jegy törzsében álló `383` ugyanis a korábbi kör SZŰRŐJÉNEK a darabszáma
volt, nem a táblahossz.

### 9.1 A nevek szövegblokkja — 592 név, nem 383

| mérés | érték |
|---|---|
| tartomány (fájl-offszet) | `0x008da958` … `0x008dfd0c` |
| méret | **21 428 bájt** |
| nevek száma | **592** |
| igazítás | **4 bájtos**, NUL-lezárt, folytonos |
| a blokk ELŐTT | `.jpx` és függvénymutatók — más adat |
| a blokk UTÁN | `{%d bytes}`, `BinaryMetadata::GetString` |

Az első szó szerinti bontás megmutatja, mit hagyott ki a korábbi szűrő:

| kezdőszó | db |
|---|---:|
| `Canon` | 146 |
| `Sigma` | 139 |
| `AF` | 73 |
| `AF-S` | 65 |
| `Tamron` | 63 |
| `Tokina` | 35 |
| `AF-I` | 16 |
| `Carl` (Zeiss) | 9 |
| `Cosina` | 7 |
| `Nikkor` | 6 |
| `Voigtlander` | 6 |
| `IX-Nikkor` | 4 |

⇒ A gyártónévvel KEZDŐDŐ mintára szűrő kör a **Nikon** neveit veszítette el
(`AF`, `AF-S`, `AF-I`, `Nikkor`, `IX-Nikkor` = 164 név), plusz a Zeiss/Cosina/
Voigtländer sort. *(Ismétlődő tanulság: a gyártó-előtagos szűrő a
gyártófüggetlen névalakokat nem látja.)*

### 9.2 ⭐ A NIKON tábla: `{ név-mutató, 8 bájtos LensID }` — 12 bájt/rekord

> ⛔ **HELYESBÍTVE (2026-09-23, 9.13 A):** a rekord `{8 bájtos kulcs, név-mutató}`, a `0x00c7b228`-tól, **417** sor — az alábbi olvasat a kulcs ELŐTTI mutatót vette névnek, ezért a lenti példák neve a szomszéd sor kulcsához tartozik.

A `0x00c7b230`-tól `0x00c7c5b0`-ig **417 rekord**, mindegyik 12 bájt:

```c
struct NikonObjektiv {          // 12 bájt
    const char *nev;            // +0x00  mutató a szövegblokkba
    uint8_t     lens_id[8];     // +0x04  a Nikon 8 bájtos LensID-je
};
```

Példák (a `lens_id` bájtsorrendben):

| név | `lens_id` |
|---|---|
| `TC-20E [II] or Sigma APO Tele Converter 2x EX…` | `2D 1C 36 00 06 00 3C 34` |
| `Tamron SP AF 11-18mm f/4.5-5.6 Di II LD Asph…` | `37 1F 3C 00 06 00 30 30` |
| `Tokina AT-X 124 AF PRO DX (AF 12-24mm f/4)` | `A0 80 3E 00 02 00 3F 38` |
| `Sigma 4.5mm F2.8 EX DC HSM Circular Fisheye` | `80 5C 53 FE 06 84 24 24` |

Ez **pontosan a Nikon MakerNote `LensID` alakja** (nyolc bájt), tehát a
feloldás egyszerű kulcs-keresés.

### 9.3 ⭐ A CANON rekord MÁS: számmezőkkel

A `Canon EF 50mm f/1.8` nevére egyetlen mutató van (`0x00c79c9c`), és a
szomszédai **lebegőpontos számok**, nem azonosító-bájtok:

```
0x00c79c98  00000001
0x00c79c9c  00cdfcf8  -> "Canon EF 50mm f/1.8"
0x00c79ca0  42480000  = 50.0f      (gyújtótávolság)
0x00c79ca8  3fe66666  = 1.8f       (rekesz)
0x00c79c94  42380000  = 46.0f
```

⇒ A Canon-oldal **nem** azonosító → név leképezés, hanem a
**gyújtótávolság/rekesz** hármasból azonosít. A két tábla tehát **külön
szerkezet**, és az átvételnek is kettőnek kell lennie.

### 9.4 ⭐ A CANON rekord KIMÉRVE: 230 rekord, 24 bájt (2026-09-16)

*A 9.3 nyitott pontja lezárva. Módszer: a szövegblokkra mutató MINDEN 4
bájtos hivatkozás összegyűjtése a teljes fájlon (659 hely), majd a
lépésközük szerinti szakaszolás — a rekordméretet így nem becsülni kell,
hanem a hivatkozások rácsa adja.*

A hivatkozások **két** összefüggő futamot adnak, és a lépésköz mondja meg a
rekordalakot:

| futam (fájl-offszet) | rekord | lépésköz | tábla |
|---|---:|---:|---|
| `0x00879c9c` … `0x0087b214` | **230** | **24 bájt** | Canon |
| `0x0087b230` … `0x0087c5a4` | **416** | **12 bájt** | Nikon |

A Canon-rekord kiosztása (minden mező a fájlból olvasva):

```c
struct CanonObjektiv {          // 24 bájt
    const char *nev;            // +0x00  mutató a szövegblokkba
    float  gyujto_min;          // +0x04  mm
    float  gyujto_max;          // +0x08  mm — 0.0f a FIX objektíveknél
    float  rekesz_min;          // +0x0c  f/
    float  rekesz_max;          // +0x10  f/ — 0.0f az ÁLLANDÓ rekesznél
    uint32_t azonosito;         // +0x14  0…489, ISMÉTLŐDHET
};
```

Ellenőrzés (az első hat rekord, a float-ok visszaolvasva):

| `azonosító` | gyújtó | rekesz | név |
|---:|---|---|---|
| 2 | 50 mm | f/1.8 | `Canon EF 50mm f/1.8` |
| 3 | 28 mm | f/2.8 | `Canon EF 28mm f/2.8` |
| 4 | 135 mm | f/2.8 | `Canon EF 135mm f/2.8 Soft` |
| 4 | 35–105 mm | f/3.5–4.5 | `Canon EF 35-105mm f/3.5-4.5 or Sigma Lens` |
| 5 | 35–135 mm | f/4–5.6 | `Sigma UC Zoom 35-135mm f/4-5.6` |
| 6 | 35–70 mm | f/3.5–4.5 | `Canon EF 35-70mm f/3.5-4.5` |

⇒ **A Canon-ág IS azonosító-alapú**, a 9.3 óvatos olvasatával szemben: van
`azonosító` mező. A **gyújtótávolság/rekesz nem helyette, hanem MELLETTE**
áll — 24 azonosító **ismétlődik** (a leggyakoribb nyolcszor), és ott a
számnégyes választ a jelöltek közül. Ez pontosan az a szerkezet, amit a
Canon `LensType` dokumentált viselkedése is mutat (egy azonosító több
objektívet takarhat).

⛔ **Amit ez NEM állít:** hogy az `azonosító` bájtra egyezik a dokumentált
`LensType` értékkel. Négy próbából három `+1` eltolással illeszkedik
(2↔1, 3↔2, 4↔3), a negyedik (a `35-105mm`) nem — tehát az egyezést **nem
mondjuk ki**, és a mező jelentését a **beolvasó** fogja eldönteni (melyik
MakerNote-mezőt hasonlítja hozzá). Ez a jegy következő lépése.

### 9.5 Két HELYESBÍTÉS a 9.2-höz és 9.3-hoz

1. ~~**A Nikon tábla 416 rekord, nem 417.**~~ → **VISSZAVONVA (9.13 A): 417 rekord, `{kulcs, név}` alakban.** A `0x0087c5b0`-on álló hivatkozás
   NEM táblasor: utána közvetlenül az `ICC_PROFILE` sztring következik
   (`70 AA CD 00 | 49 43 43 5F 50 52 4F 46 49 4C 45 00`), tehát az egy magában
   álló mutató, nem `{név, 8 bájtos kulcs}` pár. Az utolsó valódi sor a
   `0x0087c5a4`.
2. **A `Canon`-kezdetű nevek száma 147, nem 146** — a szövegblokk NUL-ra
   bontva 592 nevet ad, ebből 147 kezdődik `Canon`-nal (a blokk utolsó neve
   épp a `Canon EF 50mm f/1.8`).

### 9.7 ⛳ MEGVAN A BEOLVASÓ — és ELTOLJA a 9.4 rekordkiosztását (2026-09-16)

*Forrás: `FUN_00a35a60` (800 b, a Canon-ág) és `FUN_00a35d80` (a Nikon-ág) — a
két tábla bázisára a teljes fájlon **pontosan egy-egy** hivatkozás van
(`0x00a35c79`, illetve `0x00a3636c`).*

⛔ **HELYESBÍTÉS a 9.4-hez.** A rekordot ott a NÉV-mutatótól számoltam, mert a
hivatkozások rácsa arra állt. A beolvasó viszont megmondja a valódi
rekordkezdetet: a ciklus a **`0x00c79c98`**-tól indexel, azaz **4 bájttal
korábbról**. A helyes kiosztás:

```c
struct CanonObjektiv {          // 24 bájt, kezdet: 0x00c79c98 (VA)
    uint32_t lens_type;         // +0x00  a Canon MakerNote LensType-ja
    const char *nev;            // +0x04  mutató a szövegblokkba
    float  gyujto_min;          // +0x08  mm
    float  gyujto_max;          // +0x0c  0.0f a FIX objektíveknél
    float  rekesz_min;          // +0x10  f/
    float  rekesz_max;          // +0x14  0.0f az ÁLLANDÓ rekesznél
};
```

⭐ **Ezzel az azonosító MEGEGYEZIK a dokumentált `LensType`-pal** — a 9.4
„három próbából +1 eltolás, a negyedik nem" bizonytalansága a saját 4 bájtos
csúszásom volt:

| `lens_type` | gyújtó | rekesz | név |
|---:|---|---|---|
| 1 | 50 mm | f/1.8 | `Canon EF 50mm f/1.8` |
| 2 | 28 mm | f/2.8 | `Canon EF 28mm f/2.8` |
| 3 | 135 mm | f/2.8 | `Canon EF 135mm f/2.8 Soft` |
| 4 | 35–105 mm | f/3.5–4.5 | `Canon EF 35-105mm f/3.5-4.5 or Sigma Lens` |
| 4 | 35–135 mm | f/4–5.6 | `Sigma UC Zoom 35-135mm f/4-5.6` |
| 5 | 35–70 mm | f/3.5–4.5 | `Canon EF 35-70mm f/3.5-4.5` |

A tábla **`lens_type` szerint rendezett** (1 … 489) — a beolvasó ki is
használja.

### 9.8 A keresés algoritmusa, utasításonként

```asm
0x00a35ba0  xor esi, esi                  ; rekord-index
0x00a35ba2  xor ecx, ecx                  ; bájt-eltolás
0x00a35ba4  mov eax, [ecx + 0xc79c98]     ; a rekord lens_type-ja
0x00a35baa  cmp eax, edi                  ; edi = a MakerNote LensType-ja
0x00a35bac  ja  <kilépés>                 ; RENDEZETT tábla: efölött nincs találat
0x00a35bb2  jne <következő rekord>
            ; csak EGYEZŐ azonosítónál: a négy float összevetése
0x00a35bb8  fld dword ptr [ecx + 0xc79ca0] ; gyujto_min
0x00a35bcc  sub eax, dword ptr [esp+0x28]  ; a BITMINTÁK egész különbsége
0x00a35bd5  cmp eax, 8 / jae <következő>   ; tűrés: 8 ULP
            ; … ugyanez a gyujto_max, rekesz_min, rekesz_max mezőre …
0x00a35c71  ; találat
0x00a35c73  lea edx, [esi + esi*2]
0x00a35c76  mov edx, dword ptr [edx*8 + 0xc79c9c]  ; a NÉV (index × 24)
0x00a35c4c  add ecx, 0x18 / add esi, 1
0x00a35c52  cmp ecx, 0x1590               ; 5520 = 230 × 24
```

Három dolgot mond ki:

1. ⭐ **A 230 × 24 méret a kódból is igazolt**: a ciklus felső korlátja
   `0x1590` = **5520** = 230 × 24. A 9.4 mérése (a hivatkozások rácsa) és ez
   független úton ugyanazt adja.
2. **A kulcs kettős**: elsődlegesen a `LensType`, és az azonosítón OSZTOZÓ
   rekordok közül a **gyújtótávolság/rekesz négyes** választ — ahogy a 9.4
   sejtette, most bizonyítva.
3. ⭐ **A float-egyezés nem pontos, hanem 8 ULP tűréssel megy**: a Picasa a két
   `float` **bitmintáját** vonja ki egymásból egészként, és az abszolút
   különbséget hasonlítja 8-hoz. Ez a mi átvételünkre is szabály — a `35.0f`-hez
   képest az EXIF-ből jövő `34.999996f` még találat.

⇒ **A jegy 2. „Kész, ha" pontja (a leképezés kulcsa) ezzel LEZÁRVA** mind a két
ágon: Nikon = 8 bájtos `LensID`, Canon = `LensType` + a négyes 8 ULP-s
egyezése.

### 9.6 Amit ez a jegynek ad

* A Nikon-ág **azonnal átvehető**: **416** `{8 bájtos kulcs → név}` pár.
* A Canon-ág **is átvehető**: 230 rekord, `{lens_type, gyújtó-tartomány,
  rekesz-tartomány → név}`; az azonosító ütközését a számnégyes oldja fel,
  **8 ULP tűréssel** (ld. 9.8).
* ⛔ A `383` szám a jegy törzsében **elavult**: a szövegblokk **592** nevet
  tartalmaz.

### 9.9 ⛳ MEGVAN A HÍVÓ: a gyártót a **Make** dönti el, a kulcsokat a saját szótár adja (2026-09-16, 315. kör, #3121)

*A 9.7/9.8 a két keresőt és az algoritmusát adta. Ez a szakasz a fölötte álló
elosztót méri ki: honnan jön a `LensType`, ki választ Canon és Nikon között,
és hova kerül az eredmény.*

#### A két kereső hívója: pontosan egy, és ugyanaz

| kereső | közvetlen hívás | 4 bájtos mutató rá |
|---|---|---:|
| `0x00a35a60` (Canon) | **`0x00a359bb`** | **0** |
| `0x00a35d80` (Nikon) | **`0x00a359dc`** | **0** |

Mindkettő ugyanabban a függvényben (`FUN_00a35940`, 283 b), és **egyik sem
érhető el függvénymutatón át** ⇒ az elosztó az EGYETLEN belépési pont.
*(Indextől független pásztázás a teljes `.text`-en: `e8`/`e9` relatív hívások
és nyers 4 bájtos mutatók.)*

#### Az elosztó menete

```
0x00a35951  esi = 0xff                     ; a szótár 255-ös kulcsa
0x00a3595a  div [ebp+0x10] / 0x00a35964    ; hasítás + láncbejárás: MÁR MEGVAN?
0x00a35981  edi = 0x0a                     ; a 10-es kulcs
0x00a35990  call 0x009f05c0                ;   -> a gyártó szövege
0x00a359a2  ecx = 0x00ce3c00 ('canon')     ; kis/nagybetű-független összevetés
0x00a359bb  call 0x00a35a60                ;   -> CANON-ág
0x00a359c4  ecx = 0x00ce3c08 ('nikon')
0x00a359dc  call 0x00a35d80                ;   -> NIKON-ág
0x00a35a10  push 0xff / call 0x0049c640    ; az eredmény VISSZA a szótárba
```

A kulcsokat a **saját 6.1 táblánk** nevezi meg (a kulcs = `id` + 1):

| kulcs | mi ez a 6.1 szerint | szerepe itt |
|---:|---|---|
| **10** (`0x0a`) | IFD0 `0x010f` — **Make** | ez dönti el a gyártót |
| **105** (`0x69`) | gyártói (Canon) `0x0001` — **CameraSettings** | a Canon-ág bemenete |
| **117** (`0x75`) | gyártói (Nikon) `0x0083` — **LensType** | a Nikon-ág bemenete |
| **118** (`0x76`) | gyártói (Nikon) `0x0098` — **LensData** | a Nikon-ág bemenete |
| **255** (`0xff`) | a 6.1 tábla 176 bejegyzésén **KÍVÜL** | a feloldott objektívnév — Picasa-belső, szintetikus kulcs |

⇒ **Nincs harmadik gyártói tábla.** Az elosztó két nevet ismer (`'canon'`,
`'nikon'`); a Sigma/Tamron/Tokina nevek NEM külön ágon jönnek, hanem a két
tábla soraiban állnak (idegen gyártós objektívek a Canon/Nikon bajonetthez).

#### A Canon-ág bemenete: a CameraSettings 22–27. eleme

A `0x00a35a67 push 0x69` → `0x009f0fd0` a 105-ös kulcs tömbjét adja; a
használt elemek (a bájteltolás 4-gyel osztva az elemindex):

| bájteltolás | elem | mire megy |
|---|---:|---|
| `+0x58` | **22** | a `LensType` — **ez a keresőkulcs** (`edi`) |
| `+0x5c` | 23 | → `gyújtó_max` |
| `+0x60` | 24 | → `gyújtó_min` |
| `+0x64` | 25 | a kettő **osztója** (`fdiv` `0x00a35aea`, `fdivrp` `0x00a35b0d`) |
| `+0x68` | 26 | → `rekesz_min` |
| `+0x6c` | 27 | → `rekesz_max` |

⭐ A 22-es elem a dokumentált Canon `CameraSettings`-ben is a `LensType`
helye — a bináris és a külső dokumentáció **függetlenül ugyanoda mutat**.

A két rekesz-érték átváltása (minden konstans a binárisból kiolvasva):

```
rekesz = 2 ^ (elem / 64)
```

`0x00cf3fc0` = **0,015625** (= 1/64), az alap `0x00c7d9d0` = **2,0**, a
hatványozó `0x00c0b410` (kétszer hívva, rekeszenként egyszer:
`0x00a35b40`, `0x00a35b74`). A `0x00cf3ac0` = 4294967296,0 az előjeles→
előjeltelen javítás (2³²), nem a képlet része.

**Méret-kapu:** a Canon-ág csak akkor fut tovább, ha a tömb mérete
(`(méret & ~1) > 0x36`) — `0x00a35a85`–`0x00a35a8f`.

*Forrás: `FUN_00a35940` (`0x00a35940`, 283 b) és `FUN_00a35a60` prológusa
(`0x00a35a67`–`0x00a35b7d`); a sztringek `0x00ce3c00` és `0x00ce3c08`; a
kulcsnevek a 6.1 tábla `0x00c783ec`, `0x00c78e50`, `0x00c78fa0`,
`0x00c78fbc` sorai.*

### 9.10 Amit ez a megvalósításnak ad

1. **A gyártót az EXIF `Make` (0x010f) dönti el**, kis/nagybetű-független
   összevetéssel, és **csak** a `canon`/`nikon` kezdetre van ág.
2. **Canon:** a `MakerNote 0x0001` (CameraSettings) tömbből a 22. elem a
   `LensType`, a 23–27. elemből jön a gyújtó- és rekesz-négyes
   (`gyújtó = elem / elem25`, `rekesz = 2^(elem/64)`), és ezt a négyest
   **8 ULP tűréssel** kell a táblához mérni (9.8).
3. **Nikon:** a `MakerNote 0x0083` (LensType) és `0x0098` (LensData) a
   bemenet — a 416 soros `{8 bájtos kulcs → név}` táblához (9.2).
4. Az eredmény a Picasa-belső **255-ös** kulcs alatt él; nálunk ez a
   tulajdonságok panel „Objektív" sora.

✅ ~~NYITVA: a `0x009f0fd0` elem-egysége~~ — **lezárva a 9.12-ben**: a
kimeneti vektor `+4` mezője **elemszám·2 | jelzőbit**, tehát a kapu
„legalább 28 elem".

### 9.11 ✅ ÁTVÉVE: a két tábla és a feloldó a termékben (2026-09-19, #3121)

A 9.1–9.10 mérése alapján a **táblák kinyerve**, a feloldó megvalósítva:

| mit | hol |
|---|---|
| a két tábla tartalma | `src/picasapy/metadata/objektiv_tabla.json` — 230 Canon + 417 Nikon rekord; a Nikon-rész a 9.13 A `{kulcs, név}` párosításával újraépítve (#3495) |
| a kinyerő | privát agent-repó: `eszkozok/meres/objektiv_tabla_kinyer.py` |
| a feloldó | `src/picasapy/metadata/objektiv.py` — `canon_objektiv`, `nikon_objektiv`, `objektiv_neve`; a Nikon-ág (9.13): `nikon_leiras` / `nikon_talalat` |
| az őr | `tests/metadata/test_objektiv_feloldas_3121.py` (17 próba) |

A megvalósítás a mérés két nem-kézenfekvő részletét is átveszi:

1. az **ismétlődő `LensType`** esetén a gyújtó/rekesz négyes választ;
2. a float-egyezés **8 ULP tűréssel** megy — az őr ellenpróbával méri, hogy a
   9. ULP már NEM találat.

⚠️ A Nikon-kulcs a táblában a **fájl bájtsorrendjében** áll
(`003E80A0383F0002`), nem DWORD-önként megfordítva — a kinyerő és a feloldó
ugyanezt az alakot használja, tehát a kettő nem csúszhat el. *(Az első ad-hoc
kiolvasás két 32 bites egészként írta ki, és attól megfordult a sorrend.)*

⬜ **Ami hátravan:** a kulcs KIOLVASÁSA a MakerNote-ból (a 9.10 szerinti
elemhelyek és képletek), majd a név a tulajdonságok panelre. A végső
elfogadáshoz **egy tükörreflexes gépből származó fájl** kell — a mai
tesztkészletben és a mintázott NAS-mappákban egyetlen MakerNote-os kép sincs
(mérve: 31 vizsgált fájl, nulla találat).

### 9.12 ⛳ A Canon-ág TELJES menete — a számítás, a tartalék-leírás és a panel sora (2026-09-22, #3121)

*Forrás: `FUN_00a35a60` `0x00a35a95`–`0x00a35d4e`, a formázó `0x00a36650`, a
lekérő `0x009f0fd0`, a név→kulcs leképező `0x006349fb`. A 9.9 a menetet
`…`-tal rövidítette; ez a szakasz utasításonként végigmegy rajta.*

#### A méret-kapu egysége (a 9.10 nyitott pontja)

A `0x009f0fd0` a kimeneti vektorba 4 bájtos elemeket másol
(`lea ecx,[ebx*4]` → `0x00bf2350`), a `+4` mezőbe pedig
`lea ecx,[edi+edi] / or ecx, jelző` kerül ⇒ **elemszám·2 | 1 bites jelző**. A
kapu (`and ecx,~1 / cmp ecx,0x36 / jbe`) tehát **elemszám > 27**, vagyis
pontosan annyi, amennyi a `+0x6c`-ig (27. elem) tartó olvasáshoz kell.

#### A négy szám — a rövidítés nélkül

| lépés | feltétel | érték |
|---|---|---|
| `A` (→ `gyujto_min`) | `e25 ≠ 0` és `e24 ≠ 0` | `e24 / e25` |
| `B` (→ `gyujto_max`) | `e25 ≠ 0`, `e23 ≠ 0` **és `e23 ≠ e24`** | `e23 / e25` |
| `D` (→ `rekesz_min`) | `e26 ≠ 0` | `2^(e26/64)` |
| `C` (→ `rekesz_max`) | `e27 ≠ 0` **és `e27 ≠ e26`** | `2^(e27/64)` |

Mindegyik `float`-ba tárolva (`fstp dword`), a kiinduló érték `0.0`. ⭐ A két
`≠` feltétel adja a táblában álló `0.0`-t: a fix objektívnél `e23 = e24`,
ezért `B = 0.0` — ugyanúgy, ahogy a 230 sorban a fix gyújtótávolság áll.

A tábla-keresés az x87-verem cseréiből kiolvasva `(A, B, D, C)` ↔
`(+0x08, +0x0c, +0x10, +0x14)` sorrendben megy, és **csak
`1 ≤ LensType ≤ 0xfffe`** esetén (`lea ecx,[edi-1] / cmp ecx,0xfffd / ja`).

#### ⭐ Nincs találat ⇒ TARTALÉK-LEÍRÁS, nem üres sor

Ha a keresés nem ad nevet (nincs sor, nem egyezik a négyes, üres a név, vagy
érvénytelen a `LensType`), a `0x00a35ce2` a `0x00a36650`-et hívja a négy
számmal. A formázó (a sztringek kiolvasva):

| rész | feltétel (8 ULP-vel 0.0 ellen) | formátum |
|---|---|---|
| gyújtó | `A ≠ 0`, `B ≠ 0` | `%d-%dmm` (`0x00ce3e38`) |
| gyújtó | `A ≠ 0`, `B = 0` | `%dmm` (`0x00ce3e40`) |
| elválasztó | a gyújtó-rész nem üres | egy szóköz (`push 0x20`) |
| rekesz | `D ≠ 0`, `C ≠ 0` | `f/%.2g-%.2g` (`0x00ce3e48`), a sorrend `D`, `C` |
| rekesz | `D ≠ 0`, `C = 0` | `f/%.2g` (`0x00ce3e54`) |

A gyújtótávolság **csonkolva** megy egészre (`0x00c29990`: `cvttsd2si`), tehát
`17,9 mm` → `17mm`.

⇒ **Következmény, számolva:** a tábla négyese csak akkor egyezik, ha a
`2^(e/64)` 8 ULP-n belül esik a táblabeli rekeszre. Egész `e`-re ez csak a
kettő hatványain teljesül (`e = 64` → 2,0; `128` → 4,0); a Canon f/1.8-a
(`e = 54`) `2^(54/64) = 1,795…`, ami a táblabeli `1.8f`-től több tízezer ULP.
Ilyenkor a panelen a tartalék-leírás jelenik meg (`50mm f/1.8`), nem a
táblanév.

#### A panel „Lens" sora = a 255-ös kulcs

A `runtime/properties.xml` `<Lens/>` eleme a név→kulcs leképezőben
(`0x006349fb`) a **`0xff`**-re fordul: a sor az elosztó eredményét mutatja. A
255-ös kulcs a `0x00a27546`-nál az `XMP::Lens` (`0x00ce3180`) névvel együtt
is előkerül (`push 0xff` → `0x009f1d60`); hogy ez az XMP olvasó vagy író
oldala, azt ez a kör NEM mérte ki (#3496). Az EXIF → **megválaszolva: 9.14** (felirat-azonosító; az XMP `aux:Lens` első nyer).
`LensModel` (`0xA434`) a 6.1 táblában **nincs** — a 3.7 nem olvassa.

#### Nálunk

| mit | hol |
|---|---|
| a `CameraSettings` kiolvasása (JPEG APP1 és TIFF-alapú nyers fájl) | `src/picasapy/metadata/makernote.py` |
| a négy szám, a keresés, a tartalék-leírás | `objektiv.canon_leiras` |
| a panel sora | `reader._objektiv` → `ExifDetails.lens` |
| az őr | `tests/metadata/test_canon_objektiv_makernote_3121.py` |

⚠️ **Kimondott eltérések:**

1. A sorrend nálunk **táblanév → EXIF `LensModel` → tartalék-leírás**. Az
   eredeti a `LensModel`-t nem ismeri, tehát nála a tartalék-leírás (vagy
   üres sor) állna; a mai, működő, pontosabb kijelzést nem vesszük el.
2. Sérült fájlban a `2^(e/64)` túlcsordulhat (`e ≥ 8192`); az x87 ilyenkor
   végtelent tárol. Nálunk is végtelen lesz (a tábla-összevetés így sem
   egyezik), de a tartalék-leírás ezt a részt **kihagyja** — az eredeti CRT
   olvashatatlan szöveget írna.
3. ⬜ Nyitva: a `0x009f0fd0` előjel nélkül (`movzx`) vagy előjelesen
   (`movsx`) terjeszti-e ki a 16 bites elemeket — nálunk előjel nélküli.
   Csak a `0xFFFF` („n/a") értékű mezőknél számít.

⬜ **Nincs benne:** a Nikon-ág (a `FUN_00a35d80` a `LensData` `0100`…`0204`
verziószövegeit vizsgálja, és a `0x00ce3c38`-nál a Nikon visszafejtő táblája
áll) — **#3495**; és az `XMP::Lens` szerepe — **#3496**.

### 9.13 ⛳ A Nikon-ág TELJES menete — és a 9.2 rekordolvasata EGY SORRAL ELCSÚSZOTT (2026-09-23, 349. kör, #3495)

*Forrás: a `0x00a35d80` (1892 b) teljes diszasszemblálása, a visszafejtő
`0x00a364f0`, a tartalék-formázó `0x00a36650`, a tábla közvetlen kiolvasása,
és kontrollként egy valódi `NIKON D100`-as JPEG (`/mnt/photo/2003/2003-01-more/DSC_0001.JPG`,
`LensData 0100`).*

#### A) ⛔ HELYESBÍTÉS: a rekord `{8 bájtos kulcs, név-mutató}`, és 417 soros

A kereső ciklus (`0x00a362a8`–`0x00a3635a`) az `edi = 0x00c7b228 + 12·i`
címen hasonlítja a kulcsot, és találatkor a nevet a
`[i·12 + 0x00c7b230]`-ból veszi (`0x00a36369`) — **a név a kulcs UTÁN, a
`+8`-on áll.** A 9.2 a kulcs ELŐTTI mutatót olvasta névnek, ezért minden név
a **szomszéd** sor kulcsához került. A ciklus felső határa `0x138c` = 5004 =
**417 · 12** (`0x00a36354`): a 0. sor a `00 00 00 00 00 00 00 01` →
„Manual Lens No CPU", a 416. a `FE 53 5C 80 24 24 84 06` → „Tamron SP AF
70-200mm f/2.8 Di LD (IF) Macro (A001)". A 9.5 „416, nem 417" helyesbítése
ugyanebből a félreolvasásból született, és **visszavonva**.

**Mérve:** a termék `objektiv_tabla.json` Nikon-részének 416 sorából **17**
áll a helyes párosítással is így; a többi egy sorral el van csúszva.

**Kontroll (D100):** a helyes párosítással a `56 3C 5C 8E 30 3C 1C 02`
kulcshoz (`0x00c7bf0c`, 275. sor) a **„Sigma 70-300mm F4-5.6 APO Macro Super
II"** tartozik — ugyanezt adja az exiftool és a digiKam adatbázisa. A mai
táblánk ugyanerre a kulcsra az előző sor nevét adja („AF Zoom-Micro Nikkor
70-180mm f/4.5-5.6D ED").

A helyes táblában **5 kulcs ismétlődik**; a ciklus az **első** találatnál
áll meg (`0x00a36347`), tehát ezeknél az első név érvényes:

| kulcs | az érvényes (első) név | a második, sosem látszó |
|---|---|---|
| `25 48 3C 5C 24 24 1B 02` | Tokina AT-X 270 AF PRO II (AF 28-70mm f/2.6-2.8) | Tokina AT-X 287 AF PRO SV |
| `2F 40 30 44 2C 34 29 02` | Tokina AF 235 II (AF 20-35mm f/3.5-4.5) | Tokina AF 193 |
| `2F 48 30 44 24 24 29 02` | AF Zoom-Nikkor 20-35mm f/2.8D IF | Tokina AT-X 235 AF PRO |
| `32 54 6A 6A 24 24 35 02` | AF Micro-Nikkor 105mm f/2.8D | Sigma Macro 105mm F2.8 EX DG |
| `7A 3C 1F 37 30 30 7E 06` | AF-S DX Zoom-Nikkor 12-24mm f/4G IF-ED | Tokina AT-X 124 AF PRO DX II |

A tábla az első bájt szerint rendezett, és a ciklus kilép, ha a táblabeli
első bájt nagyobb a keresettnél (`0x00a362b1`).

#### B) A kulcs összerakása

| `LensData` első 4 bájtja | a 7 bájt eltolása | visszafejtés | cím |
|---|---:|---|---|
| `0100` (`0x00cc7e74`) | 6 | nem | `0x00a35ecf` |
| `0101` (`0x00ce3c10`) | 0x0b | nem | `0x00a35f60` → `0x00a361d8` |
| `0201`, `0202`, `0203` | 0x0b | igen | → `0x00a361d6` |
| `0204` (`0x00ce3c30`) | 0x0c | igen | `0x00a3619b`–`0x00a361a0` |
| más | — | **üres** eredmény | `0x00a361a4` |

- a `LensData` hossza nagyobb kell legyen, mint `eltolás + 7`, különben üres
  (`0x00a361dd`–`0x00a361e6`);
- **kulcs = `LensData[eltolás … eltolás+6]` (7 bájt) + `LensType`**
  (`0x0083`, a 8. bájt; `0x00a362bd`–`0x00a36347`) — ugyanaz a sorrend, mint
  az exiftool `LensID`-jéé;
- a `LensType`-nak `1 … 0xFFFE` közé kell esnie, különben a táblát
  kihagyja és a tartalékra megy (`0x00a3627a`–`0x00a36292`).

**Kontroll:** a D100-as minta `LensData`-ja `30 31 30 30 11 56 | 56 3C 5C 8E
30 3C 1C | …`, `LensType = 2` ⇒ kulcs `56 3C 5C 8E 30 3C 1C 02`, bájtra az
exiftool `LensID -n` értéke.

#### C) A visszafejtés (`0x00a364f0`, a 4. bájttól)

Szerkezetében az exiftool Nikon-`Decrypt` eljárása: a sorozatszám a gyártói
szótár `0x74`-es eleméből, ha az nincs, a `0x78`-asból szövegként `atoi`-val
(`0x00bf6a2d`); ha egyik sincs, `"D50"`-nél (`0x00cccd68`) `0x22`, egyébként
`0x60` (`0x00a365b0`–`0x00a365d2`); a zárszámláló a szótár `0x0b` eleme, négy
bájtja XOR-olva (`0x00a365da`-tól); a helyettesítő tábla a `0x00ce3c38`-on.
⚠️ **Mintán NINCS mérve** — a gépen nincs `0201`+ `LensData`-s Nikon-kép
(a digiKam-adatbázis 15 Nikon-képe: 1 D100-as, a többi Coolpix). A szótár
`0x74`/`0x78`/`0x0b` elemének gyártói címkéje nincs külön kiolvasva.

#### D) A tartalék-leírás (nincs táblatalálat vagy a `LensType` érvénytelen)

`0x00a363c4` → `0x00a36650`, a 7 bájtos `p` mezőiből, `g(b) = 2^(b/24)`
(`0x00cf3ef0` = 24,0, `0x00c7d9d0` = 2,0, hatvány: `0x00c0b410`):

```
fmin = 5·g(p[2])   fmax = 5·g(p[3])        (0x00cf4618 = 5,0)
amin = g(p[4])     amax = g(p[5])
szöveg = "%d-%dmm" (fmin, fmax — _ftol, CSONKOL)  vagy "%dmm", ha fmax ≈ 0
       + " " + "f/%.2g-%.2g" (amin, amax)        vagy "f/%.2g", ha amax ≈ 0
```

(`0x00ce3e38` `%d-%dmm`, `0x00ce3e40` `%dmm`, `0x00ce3e48` `f/%.2g-%.2g`,
`0x00ce3e54` `f/%.2g`.) A „≈ 0" próba (bitminta, 8 ULP) kiszámolt értékre
sosem igaz (`g ≥ 1`), tehát a gyakorlatban **mindig** `A-Bmm f/X-Y` — azonos
rekesznél is kétszer írja (`f/2.8-2.8`). A D100-as mintán a tartalék
`71-302mm f/4-5.7` volna.

#### E) Amit ez a megvalósításnak ad — #3495

| | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| a Nikon-tábla | 417 sor, `{kulcs, név}` a `0x00c7b228`-tól | 416 sor, egy sorral elcsúszott párosítás (17/416 helyes) | a tábla újra-kinyerése a helyes párosítással |
| ismétlődő kulcs | az első nyer | a `dict` az utolsót tartja | első-nyer index |
| a Nikon-ág | a B)–D) menet | nincs bekötve | a Canon-ág mintájára |

*Bizonyítottsági fok: **megerősített** a rekordolvasatra, a 417 sorra, a
kulcs-összerakásra és a tartalékra (utasításszintű kiolvasás + a D100-as
kontroll); **erős** a visszafejtésre (az exiftool eljárásával azonos
szerkezet, mintán nem mérve).*

### 9.14 ⛳ Az XMP `aux:Lens` ELŐBB tölti a 255-ös kulcsot, mint a MakerNote-feloldás (2026-09-23, 350. kör, #3496)

*A 9.12 nyitva hagyta: a `0x00a27546` környéke (`XMP::Lens`, `push 0xff`)
XMP-olvasó vagy -író? Egyik sem — de a kérdés mögötti kérdésre (van-e XMP-
olvasó, és elsőbbséget kap-e) van válasz.*

#### A) A `0x00a27546` a panelsor FELIRATA, az `XMP::Lens` szövegtár-azonosító

A `FUN_00a00120(meta, kulcs, &feliratok, &értékek)` a Tulajdonságok panel
kulcsonkénti sorformázója: a két panelépítő (`FUN_006364c0` „PropertiesPanel",
`FUN_007e3210` „CPropertiesDlg") hívja ciklusban (`0x006365a8`–`0x006365d0`),
az ugrótáblája (`0x00a344b4`, 0…0x14e) minden kulcsnak saját ágat ad. A 255-ös
ág (`0x00a272fd`–`0x00a2755c`) a feliratot a `0x009ae560("Lens", "XMP::Lens")`
szövegtár-keresővel képzi (`0x00d4a654` a betöltött szövegtár; hiányzó
azonosítónál az alapszöveg), az értéket a `0x009f1d60(…, 0xff, &értékek)`-kel.
Az `XMP::Lens` tehát a **felirat azonosítója** — `stringres` 2479. sor:
`Lens` → **`Objektív`**; ugyanígy `EXIF::BitsPerSample` (2), `XMP::FlashCompensation`
(253), `XMP::LensID` (256). Az előtag az azonosító elnevezése, nem az érték
forrása.

#### B) Van XMP-OLVASÓ, és „első nyer" alapon tölti a 255-öt

| lépés | mit tesz | cím |
|---|---|---|
| `ytXMPReader` | RTTI-vtábla `0x00cef524`; az 5. rekesz a névtér → kezelő elosztó `0x00ba8dd0` (tábla `0x00d3b240`–`0x00d3b2bc`, kitöltés `0x00c3430a`–`0x00c343b9`) | a vtábla-írók `0x00ba76ca`, `0x00ba7a8c` |
| tulajdonságnév-kezelő | `FUN_00baaf90`: `strcmp(név, "Lens")` (`0x00bab5bd`), és ha a kért kulcsok maszkjában (`[esi+0x24]`) a 255 szerepel, `0x00ba9040(…, 0xff, érték)` | `0x00bab5bc`–`0x00bab5d3` |
| beszúrás | a kulcs-hash (`[obj+0x28]`) láncán keres; **ha a kulcs már megvan, nem ír felül**, csak hiányzó kulcsot szúr be (`0x0049d8d0`) | `0x00ba9048`–`0x00ba9089` |

A `"Lens"` sztringnek (`0x00c9fd6c`) a teljes `.text`-ben (bájtmintára,
indextől függetlenül) **négy** hivatkozása van: a `properties.xml`
név → kulcs leképezője (`0x006349fb`), a panelfelirat (`0x00a27527`), az
XMP-olvasó (`0x00bab5bd`) és az XMP-**író** (`0x00bae4d2`, lent).

#### C) A sorrend: az XMP-olvasás MEGELŐZI az objektív-elosztót

A két betöltő, amely mindkettőt hívja:

| betöltő | XMP-olvasás (`0x00ba7490`) | utófeldolgozás (`0x00a34b00`, benne az objektív-elosztó `0x00a35940`) |
|---|---|---|
| `0x00a4f840` | `0x00a4f8c1` | `0x00a4f8ed` |
| `0x009ea9c0` | `0x009eaa4f` | `0x009eab73` |

A `0x00a34b00` az objektív-elosztót **utolsó lépésként** hívja
(`0x00a34b42`), és az elosztó a 255-ös kulcsra „már megvan?" próbával kezd
(9.9, `0x00a35951`–`0x00a35964`). ⇒ **Ha a fájl XMP-jében van `aux:Lens`,
annak a szövege kerül a panelre, és a MakerNote-feloldás (Canon/Nikon)
kimarad.** Ha nincs, a MakerNote-ág tölti.

#### D) Az XMP-író (a kérdés másik fele)

A `0x00bae420` a 0xfc…0x103 kulcsokon megy végig: ha a kulcs be van
állítva (`0x009eee30` + `test [ecx+8]`), a `0x00bb0440(…, aux-névtér
0x00cef2e8, név, kulcs, 0)` a Picasa-tulajdonság értékét
(`0x009f0560(propset, kulcs)`, `0x00bb048b`) XMP-tulajdonságként beállítja
(`0x00bb0310` → `0x00bda060`, az XMP Toolkit beállítója). Ez a 255-öt
`aux:Lens`-ként **írja** (`0x00bae4b9`–`0x00bae4dd`); hogy mikor fut
(mentéskor/exportkor), ez a kör nem követte végig — a panel szempontjából
nincs jelentősége.

#### E) Mérve — a mai olvasónk

| minta | a fájlban | Picasa (a fenti lánc) | nálunk (`read_exif_details().lens`) |
|---|---|---|---|
| `951-kiemelesek-arnyekok-fel-allas/original.jpg` (D7000, Lightroom) | XMP `aux:Lens = 70.0-200.0 mm f/2.8`, MakerNote nincs | `70.0-200.0 mm f/2.8` | **`None`** |
| `/mnt/photo/2003/2003-01-more/DSC_0001.JPG` (D100) | MakerNote `0100`, XMP nincs | Sigma 70-300mm F4-5.6 APO Macro Super II (9.13) | **`None`** (#3495) |

⇒ Teendő: **#3496** — az `aux:Lens` beolvasása elsőként, utána a
MakerNote-ág.

*Bizonyítottsági fok: **megerősített** a felirat-azonosítóra, az olvasó
„első nyer" beszúrására és a két betöltő hívási sorrendjére; **erős**, hogy
a két betöltőben a `0x00ba7490` és a `0x00a34b00` ugyanazt a
tulajdonság-halmazt kapja (a regiszter-átadás nincs lépésenként követve), és
hogy a panel a szöveget változatlanul mutatja (a `0x009f1d60` szöveg-ágát
nem olvastam végig).*

## 10. ⛳ A határvonal EXIF/GPS-névregisztere — részlelet (2026-09-18, #3345)

A kutatási határvonal a `0x00bf697a`-ból elérhető feltáratlan
`0x00bab6e0`-t jelölte. Ez a `.text`-ben lévő `FUN_00bab6e0`, **4153 bájt**.
A bináris-index `string_xrefs` táblája ehhez a függvényhez **70 különböző
ASCII-sztringet** köt:

| csoport | darab | mért alak |
|---|---:|---|
| szabványos EXIF-név, GPS-előtag nélkül | **44** | `DateTimeOriginal`, `FNumber`, `ColorSpace`, `ImageUniqueID` … |
| GPS-előtagú név | **22** | `GPSLatitude`, `GPSAltitude`, `GPSDestDistance` … |
| nem egyértelműen EXIF/GPS-név | **4** | `Function`, `RedEyeMode`, `Return`, `Fired` |
| **összesen** | **70** | `string_xrefs`, `function_address = 0x00bab6e0` |

A sztringek első és utolsó indexelt RVA-ja `0x0089eff4`, illetve
`0x008ef3f0`. Ez a blokk ténylegesen EXIF/GPS-mezőneveket tartalmaz; a
névlista önmagában **nem** bizonyítja, hogy a Tulajdonságok-panel közvetlen
forrása.

### 10.1 A hívási lánc, amit az index ténylegesen lát

`0x00bab6e0` az index szerint nyolc belső segédfüggvényt és a
`__stricmp`-ként indexelt `0x00bf697a` rutint hívja:

| cím | méret (bájt) | `call_count` az xref-indexben |
|---|---:|---:|
| `0x009eee30` | 187 | 71 |
| `0x00ba9040` | 82 | 13 |
| `0x00ba90a0` | 106 | 24 |
| `0x00ba9170` | 175 | 22 |
| `0x00ba9220` | 147 | 3 |
| `0x00ba9500` | 504 | 3 |
| `0x00ba9930` | 2220 | 2 |
| `0x00baa1f0` | 690 | 4 |
| `0x00bf697a` (`__stricmp`) | 80 | 71 |

A `0x00ba9930` segédfüggvény az indexben egyszer meghívja a
`0x009f05c0` címet. Ez a lap 1. szakaszában már dokumentált
`BinaryMetadata::GetString` lekérdező címe. **A bizonyított állítás ennyi:**
a jelölt függvény hívási részgráfja eléri a belső metaadat-lekérdezőt; a
paraméterek és a mezőazonosító-képzés még nem olvasható ki az indexből.

### 10.2 Eredeti / nálunk / nyitva

| | Eredeti | Nálunk | Állapot |
|---|---|---|---|
| névkészlet | `0x00bab6e0`: 70 indexelt ASCII EXIF/GPS-név | `metadata/reader.py` és `app/formatting.py` a panel számára külön, szabványos EXIF-címkéket olvas | **bináris tény + saját kód mérve** |
| kapcsolat a belső kulcstérrel | a hívási lánc eléri a `BinaryMetadata::GetString` címet | a jelenlegi olvasó nem használ ilyen névregisztert | **a közös réteg erős jel, közvetlen leképezés NINCS MEG** |
| gazdag saját próba | — | szintetikus, 12 × 8-as EXIF-képen **23 panel-sor**, ebből **20 nem-üres** metaadatérték | **mérés**, nem bináris állítás |

**Ami NINCS MEG:** a 70 névhez tartozó pontos belső kulcs-/típus- és
értékleképezés, valamint annak bizonyítása, hogy a `0x00bab6e0` közvetlenül
a Tulajdonságok-panel regisztere volna. A helyi kutatási anyagban a Picasa3.exe
nem áll rendelkezésre célzott dekompilációhoz; a Codespace-eszköz előfeltétel-
ellenőrzése sikeres, de a bináris feltöltési útja ebben a körben nincs meg.
**Nem becsültünk.**

A következő gépi lépés: célzott dekompiláció a `0x00bab6e0` törzsére, a nyolc
segédfüggvény argumentum-/visszatérési szerződésére, majd kontrollként egy
ismert hosszú EXIF-mezőtáblás hívó összevetése. A #3345 nyitva marad.

## 11. Az XMP Core namespace-katalógus jelölt blokkja (2026-09-18, #3348)

A kutatási határvonal `0x00bdbe50` címen egy külön XMP-adatblokkot jelölt.
A kérdés az volt, hogy a blokk csak véletlenül együtt álló sztringeket tartalmaz-e,
vagy az eredeti XMP-olvasó/író réteghez tartozó névtér-katalógus része.

### Amit az index közvetlenül mér

| tétel | mért tény |
|---|---|
| függvény | `FUN_00bdbe50`, **1822 bájt**, RVA és fájloffset `0x007dbe50` |
| közvetlen hívó | `0x00bd9ae0` → `0x00bdbe50`, **1** indexelt hívás |
| közvetlen hívottak | **9** függvény; köztük `0x00be26d0` (**49** hívás) és `0x00c0769f` (**3** hívás) |
| sztringhivatkozás | **80** különböző sztring a `string_xrefs` táblában |
| namespace-URL | **48** `http…` sztring ugyanebben a függvényben |

A sztringek között közvetlenül ott van az `XMP Core 5.1.2`, az Adobe copyright,
a `Failure from XMPIterator::Initialize`, az `adobe:ns:meta/`, az RDF- és
Dublin Core-névtér, valamint az Adobe XAP/XMP, PDF/A, Photoshop, EXIF, TIFF,
PNG, JPEG, DICOM, IPTC és StockPhoto namespace-család több URI-ja. Ez a lista
a `string_xrefs` mérési eredménye; önmagában nem bizonyítja, hogy mind a 48
URI-t futásidőben regisztrálja.

Az RTTI-tábla ugyanebben a binárisban külön osztálycsaládot mutat:
`ytXMPReader::vftable` = `0x00cef524`, `ytXMPWriter::vftable` =
`0x00cef54c`, `XMP_NamespaceTable::vftable` = `0x00cf1a4c`,
`XMP_Node::vftable` = `0x00cf1a54`, `XMPMeta::vftable` = `0x00cf1a5c`.
Ez az XMP-namespace adatblokk és az XMP-típuscsalád közötti kapcsolatot erős
statikus jelként támasztja alá; a tényleges regisztráló hívás még nincs
utasításszinten kiolvasva.

### Eredeti / nálunk / teendő

| | Eredeti, indexből mérve | PicasaPy, forrásból mérve | Állapot |
|---|---|---|---|
| XMP-réteg jelenléte | XMP Core 5.1.2 sztring + külön `ytXMPReader`/`ytXMPWriter`/`XMPMeta` RTTI | `export/xmp.py` saját, determinisztikus XMP-builder és sidecar-író | **megerősített statikus kapcsolat** |
| névtérkészlet | `0x00bdbe50`: 80 sztring, ebből 48 URL | 9 saját URI-konstans (`RDF`, `DC`, `LR`, `MWG-RS`, `stArea`, `stDim`, `MP`, `MPRI`, `MPReg`) és az `adobe:ns:meta/` wrapper | a készletek nem azonosak; nincs átvezetési következtetés |
| regisztrációs szemantika | a 48 URL ugyanahhoz a függvényhez kötött; a közvetlen hívó és az XMP RTTI megvan | a saját exporter nem natív registryt használ | **NINCS MEG** a tényleges `RegisterNamespace`-szerű hívás és az URI→prefix párosítás |

**Bizonyítottsági fok: erős statikus lelet** az XMP Core/namespace-adatblokk
létezésére és a környező XMP-típuscsaládra. **NINCS MEG** a `0x00bdbe50`
utasításszintű szerepe, a regisztrációk sorrendje, az URI→prefix teljes
leképezése és az, hogy a 48 URL közül melyeket használja ténylegesen az olvasó
vagy az író.

A szükséges következő lépés a `Picasa3.exe` célzott dekompilációja a
`0x00bdbe50` és `0x00bd9ae0` címeken. A helyi kutatási anyagban az EXE nincs
jelen, ezért ezt a kört nem helyettesítettem becsléssel; a #3348 nyitva marad
és a hiányzó bináris miatt külső függőségre vár.

## 12. ⛳ A regisztrációs LÁNC megvan — 49 SDK-névtér + a Picasa NÉGY sajátja (2026-09-18, #3348)

*A 11. szakasz a `0x00bdbe50`-t „jelölt blokknak" nevezte, és a jegy azért
állt `blocked`-on, mert az előző (felhős) kör nem érte el a binárist. A
bináris helyben megvan (`research/copy_Picasa_3_7/Picasa3/Picasa3.exe`,
10 160 456 bájt), így a kérdés eldőlt.*

### A lánc

```
0x00ba7430  (91 b)   ← a Picasa saját belépési pontja
   ├── 0x00bb1d60 (71 b)  → 0x00bd9ae0 (88 b) → 0x00bdbe50 (1822 b)
   │                                              └── 49 × 0x00be26d0   (SDK-katalógus)
   └── 4 × 0x00bb1db0 (76 b) → 0x00bd9dd0 (182 b) → 0x00be26d0          (SAJÁT névterek)
```

A `0x00be26d0` (1297 b) a **regisztráló**: `this` egy névtér-tábla
(`lea ecx, [esp+0x1c]`), az argumentumai `(URI, prefix)` — a hívóhelyek
sorrendje `push prefix; push URI; call`, tehát a veremtetőn az URI áll,
azaz az **URI az első argumentum**. A táblának pontosan **két** hívója van:
a `0x00bdbe50` (49 hívás) és a `0x00bd9dd0` (1 hívás) — utóbbi a nyilvános
„regisztrálj egy névteret" API, amit a Picasa saját kódja használ.

### A) A 49 SDK-névtér (`0x00bdbe50`)

Az Adobe XMP-Core alapkatalógusa, sorrendben kiolvasva a törzsből:
`xml` · `rdf` · `dc` · `xmp` · `pdf` · `photoshop` · `album` · `exif` ·
`aux` · `tiff` · `png` · `jpeg` · `jp2k` · `crs` · `asf` · `wav` · `bmsp` ·
`creatorAtom` · `xmpRights` · `xmpMM` · `xmpBJ` · `xmpNote` · `xmpDM` ·
`xmpScript` · `bext` · `xmpT` · `xmpTPg` · `xmpG` · `xmpGImg` · `stFnt` ·
`stDim` · `stEvt` · `stRef` · `stVer` · `stJob` · `stMfs` · `xmpidq` ·
`Iptc4xmpCore` · `DICOM` · `pdfaSchema` · `pdfaProperty` · `pdfaType` ·
`pdfaField` · `pdfaid` · `pdfaExtension` · `pdfx` · `pdfxid` · `x` · `iX`.

⛔ **Ez a lista NEM a Picasa kimeneti sémája.** Az SDK inicializálása
regisztrálja mind a 49-et függetlenül attól, hogy a program ír-e belőlük
bármit — tehát egy névtér jelenléte itt **semmit nem bizonyít** a
`.jpg`-be írt XMP-ről. A 11. szakasz „48 namespace-URL" száma is
pontosítható: a párok száma **49**, a különbség az `x` → `adobe:ns:meta/`,
ami nem `http`-vel kezdődik, ezért az index URL-heurisztikája kihagyta.

### B) ⭐ A Picasa NÉGY saját névtere (`0x00ba7430`, négy hívás)

| # | prefix | URI | cím (prefix / URI) |
|---|---|---|---|
| 1 | `MP` | `http://ns.microsoft.com/photo/1.2/` | `0xcef370` / `0xcef374` |
| 2 | `Iptc4xmpExt` | `http://iptc.org/std/Iptc4xmpExt/2008-02-29/` | `0xcef398` / `0xcef228` |
| 3 | `stArea` | `http://ns.adobe.com/xmp/sType/Area#` | `0xcef3a4` / `0xcef170` |
| 4 | `mwg-rs` | `http://www.metadataworkinggroup.com/schemas/regions/` | `0xcef3ac` / `0xcef194` |

A négy prefix és a négy URI **egymás melletti, nullával zárt sztringként**
áll az adatszakaszban; a párosítás nem a szomszédságból, hanem a
hívóhelyek `push`/`mov ecx` operandusaiból jön.

⭐ **Kontroll:** a jól ismert kanonikus párosítások mind stimmelnek —
`dc` → `purl.org/dc/elements/1.1/`, `xmp` → `ns.adobe.com/xap/1.0/`,
`tiff` → `ns.adobe.com/tiff/1.0/`, `exif` → `ns.adobe.com/exif/1.0/`. Ha a
kiolvasás egy elemet elcsúsztatna, ez a négy azonnal hibásan jönne ki.
*(A terv egy másik kontrollt is előírt — hogy a prefixek `:`-re
végződnek —, az **megdőlt**: a prefixek kettőspont nélkül állnak. A
párosítás-kontroll ettől független, és áll.)*

### C) „eredeti / nálunk / teendő"

| névtér | eredeti | nálunk (`export/xmp.py`) |
|---|---|---|
| `mwg-rs` regions | **regisztrálva** (B/4) | megvan |
| `stArea` | **regisztrálva** (B/3) | megvan |
| `MP` (MicrosoftPhoto 1.2) | **regisztrálva** (B/1) | megvan |
| `MPRI`/`MPREG` (`…/1.2/t/RegionInfo#`, `…/1.2/t/Region#`) | a sztring MEGVAN (`0xcef210`, `0xcef1e4`), de a négy regisztráció nem ezeket adja | megvan |
| `Iptc4xmpExt` (IPTC Ext 2008-02-29) | **regisztrálva** (B/2) | **NINCS** |
| `stDim` | az SDK katalógusában (A) | megvan |
| `lr` (`http://ns.adobe.com/lightroom/1.0/`) | ⛔ **a teljes képfájlban NULLA előfordulás** | **írjuk** |

⛔ **A `lr:` névtér a mi hozzátoldásunk.** A `ns.adobe.com/lightroom`
minta a teljes 10 160 456 bájtos képfájlban **egyszer sem** szerepel — a
keresés bájtszintű, tehát az index lyukaitól független. Az eredeti Picasa
XMP-kimenete ezt a névteret nem ismeri. *(Fejlesztői teendő: **#3353**.)*

*Forrás: `0x00ba7430` (91 b), `0x00bb1db0` (76 b), `0x00bb1d60` (71 b),
`0x00bd9ae0` (88 b), `0x00bd9dd0` (182 b), `0x00bdbe50` (1822 b),
`0x00be26d0` (1297 b); a hívószámok a bináris index `xrefs` táblájából, a
sztringek `pe_dis.D`-ből kiolvasva.*

### D) ⭐ Mit ÍR KI valójában — a saját exportján mérve (2026-09-19, #3353)

A B) tábla `Iptc4xmpExt` sora önmagában félreérthető: a regisztráció mellé az
eredeti a **teljes IPTC Extension SÉMÁT** is bejegyzi — 21 tulajdonság
`_Bag`/`_Seq` típusjelzőkkel a `0xbafe00`–`0xbb0300` sávban (`AddlModelInfo`,
`ArtworkOrObject`, `OrganisationInImageCode`, `CVterm`, `LocationShown`,
`ModelAge`, `OrganisationInImageName`, `PersonInImage`, `DigImageGUID`,
`DigitalSourcefileType`, `DigitalSourceType`, `Event`, `IptcLastEdited`,
`MaxAvailHeight`, `MaxAvailWidth`, `Version`, `MinorModelAgeDisclosure`,
`ModelReleaseID`, `ModelReleaseStatus`, `PropertyReleaseID`,
`PropertyReleaseStatus`); a névtér URI-jára **23** hivatkozás van, és ezek
mind ebben a séma-blokkban, illetve a négyes regisztrációban állnak. A
tulajdonságnevek emellett két TÁBLÁBAN is szerepelnek: egy 24 bájt lépésközű
leíró-táblában (`0x634c3c`-től) és egy emberi felirat–tulajdonság párokat adó
táblában (`"Person Shown"` → `"XMP::PersonInImage"`, `0xce34c0`-től) — azaz az
OLVASÓ/megjelenítő oldalon.

⇒ **A regisztráció és a séma nem írás.** Amit a Picasa tényleg kiír, azt a
SAJÁT exportján mértük:

| forrás | a kiírt XMP névterei |
|---|---|
| `684-merokeszlet/export` (40 kép) | `xmp`, `exif`, `dc` — és semmi más |
| `3229-lanc-sorrend/export` (4 kép) | ugyanaz |

Mind a 44 képben **nulla** `Iptc4xmpExt`, `PersonInImage`, `mwg-rs`,
`MicrosoftPhoto` és `lightroom` előfordulás. A csomag tartalma:
`xmp:ModifyDate`, `exif:DateTimeOriginal`, `dc:creator` = „Picasa".

⚠️ **A negatív állítás HATÓKÖRE:** a mért exportokon nem volt **névvel
ellátott arc**, tehát a „`PersonInImage` megnevezett arc mellett" eset nincs
lefedve, és az `mwg-rs` hiánya sem jelenti, hogy arcos képnél is hiányozna (a
#1403 épp azt mérte ki, hogy arcokhoz az `mwg-rs`/`MP` megy). ~~A hiányzó mérés
jegye: **#3424**.~~ ⚠️ **LEZÁRVA a binárisból (2026-09-22), ld. az E) szakaszt:** a megnevezett arc NEM kerül `PersonInImage` alá.

*A `lr:` sorsa ezzel eldőlt: MARAD, tudatos, az eredetiben nem létező
kiegészítésként — a `export/xmp.py` névtér-listája ezt ki is mondja (#3353).*

### E) ⛳ A #3424 kérdése a BINÁRISBÓL: a megnevezett arc NEM kerül `PersonInImage` alá (2026-09-22, #3424)

*Forrás: indextől független bájtpásztázás a `PersonInImage` literál
(`0x00c9ff18`) minden 4 bájtos hivatkozására · az arcrégió-író
`0x00bb17e0` (1380 b) sztring-készlete · a három hivatkozó függvény
diszasszemblátuma.*

A D) szakasz a „névvel ellátott arc” esetet mérés híján nyitva hagyta, és
exportot kért. A kérdés azonban eldönthető a binárisból: egy XMP-tulajdonság
KIÍRÁSÁHOZ a tulajdonság nevét át kell adni az XMP-eszközkészletnek, tehát
az író kódnak hivatkoznia kell a literálra.

**A `PersonInImage` literálra PONTOSAN három hivatkozás van** a teljes
fájlban, és egyik sem író:

| hivatkozás | függvény | mit csinál |
|---|---|---|
| `0x00634d5c` | `0x00633210` (8048 b) | név → belső kulcs leképező `strcmp`-lánc: `PersonInImage` → **0x123** (`0x00634d6d`) |
| `0x00bad223` | `0x00bad070` (1274 b) | **olvasó** visszahívás: a beérkező tulajdonság nevét hasonlítja, egyezésnél a 0x123-as kulcs alá TÁROLJA az értéket (`0x00bad233` → `0x00ba9040`), a kulcsmaszk (`[esi+0x24]`) szerint |
| `0x00bb0039` | `0x00bafde0` (1322 b) | a séma-regisztráció (a D) szakasz 21 tulajdonsága) |

**Az arcrégiók írója** (`0x00bb17e0`) a teljes sztring-készlete szerint csak
ezt írja: `mwg-rs:Regions/mwg-rs:AppliedToDimensions` (`w`, `h`,
`unit = pixel`), `mwg-rs:Regions/mwg-rs:RegionList[last()]` alá `Name`,
`Type = Face` és `mwg-rs:Area` (`x`, `y`, `w`, `h`, `unit = normalized`),
valamint a Microsoft `RegionInfo`-t (`http://ns.microsoft.com/photo/1.2/`,
`0x00bb186b`). **`Iptc4xmpExt`-re és `PersonInImage`-re egyáltalán nem
hivatkozik.**

⛳ **Pozitív kontroll:** ugyanez a pásztázás a `mwg-rs:Regions/...` XPath
literálokra megtalálja az író hívóhelyeit (`0x00bb1b89`, `0x00bb1bb7`,
`0x00bb1bf1` …), tehát a módszer az írót látja, ha van.

⇒ **LEZÁRVA: a Picasa a megnevezett arc nevét a régió `Name` mezőjébe írja
(`mwg-rs` + `MP`), `PersonInImage`-t nem generál.** A `PersonInImage`-et
OLVASSA (0x123-as kulcs), ha a képben már benne van.

⚠️ **Hatókör:** ez az állítás a `PersonInImage` ELŐÁLLÍTÁSÁRÓL szól. Hogy egy
forrásképben MÁR meglévő `PersonInImage` a Picasa újraírása után megmarad-e
(az XMP-eszközkészlet a nem ismert tulajdonságokat általában megőrzi), azt ez
a kör nem vizsgálta — a mi exportunk nem ír vissza forrás-XMP-t, tehát a
termékre nincs hatása.

⛔ **Helyesbítés a D) szakaszhoz:** az ott „24 bájt lépésközű leíró-táblának”
nevezett `0x634c3c`-es sáv nem tábla, hanem **kód** — a `0x00633210`
`strcmp`-lánca, amelynek minden blokkja (`push név · push esi · call
0x00bf697a · add esp,8 · test · jne · mov eax,kulcs · ret`) pontosan 24
bájt. A „leíró-tábla” olvasat ezt a szabályos lépésközt értette félre.

**Nálunk:** az `export/xmp.py` `PersonInImage`-t nem ír, az arcneveket az
`mwg-rs`/`MP` régiókba teszi — ez **egyezik** az eredetivel. A kódban álló
„a negatív állítás hatóköre” megjegyzés (`export/xmp.py`, a névtér-lista
fölött) ezzel hatókör nélkül igaz; a pontosítása a #3424-en áll.

`Nyitott kérdések: 0 nyílt · 1 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 „csak nyitva”`
(hatókörön kívül: a meglévő `PersonInImage` megőrzése — a termékre nincs
hatása, 339. kör döntése).

## 13. ⛳ A `0x00bab6e0` szerepe MEGVAN: az EXIF/GPS sémaleíró, egy 14 rekeszes séma-tábla 6. rekesze (2026-09-19, #3345)

*A 10. szakasz a `0x00bab6e0`-t „részleletként" hagyta ott (70 indexelt
mezőnév, nyolc segédfüggvény). A törzs kiolvasásával a szerep és a
típusmodell is megvan.*

### A) Mi ez a függvény, és hogyan hívódik

⛔ Az xref-index szerint a függvénynek **nincs közvetlen hívója** — ez nem
azt jelenti, hogy halott: **függvénymutatóként** telepszik. A címét
(`0x00bab6e0`) a teljes képfájlban **pontosan egy** 4 bájtos konstans
tartalmazza, a `0x00c34339` címen, a `0x00c34300` (236 b) inicializálóban:

```
0x00c34338  mov eax, 0xbab6e0
0x00c3433d  mov dword ptr [0xd3b298], eax
```

Az inicializáló egy **14 rekeszes globális táblát** tölt fel `0xd3b248`-tól,
`0x10` bájtos lépésközzel. A rekeszek tartalma és — az egyes függvényekhez
kötött sztringkészletből azonosítva — a sémacsalád:

| rekesz | függvény | méret | nevek | mi ez (a sztringekből) |
|---|---|---:|---:|---|
| `0xd3b248` | `0x00bad700` | 87 b | 0 | *nincs név* |
| `0xd3b258` | `0x00baac00` | — | 0 | *nincs név* |
| `0xd3b268` | `0x00baad30` | 594 b | 10 | **XMP Basic** (`Rating`, `Advisory`, `BaseURL`, `Identifier`, …) |
| `0xd3b278` | `0x00baaf90` | 1385 b | 23 | **TIFF** (`Software`, `ImageWidth`, `BitsPerSample`, …) |
| `0xd3b288` | `0x00bab500` | — | 0 | *nincs név* |
| **`0xd3b298`** | **`0x00bab6e0`** | **4153 b** | **71** | **EXIF + GPS** ← ez a jegy tárgya |
| `0xd3b2a8` | `0x00bac720` | 851 b | 12 | **Dublin Core** (`description`, `title`, `subject`, …) |
| `0xd3b2b8` | `0x00baca80` | — | 0 | *nincs név* |
| `0xd3b2c8` | `0x00bacd50` | 796 b | 13 | **IPTC Core** (`CountryCode`, `IntellectualGenre`, `Scene`, …) |
| `0xd3b2d8` | `0x00bad070` | 1274 b | 21 | **IPTC Extension** (`AddlModelInfo`, `ArtworkOrObject`, …) |
| `0xd3b2e8` | `0x00bad570` | — | 0 | *nincs név* |
| `0xd3b2f8` | `0x00bad5a0` | — | 0 | *nincs név* |
| `0xd3b308` | `0x00bad610` | 234 b | 2 | **MWG-régiók** (`AppliedToDimensions`, `RegionList`) |
| `0xd3b318` | `0x00bad760` | 221 b | 0 | *nincs név* |

⭐ **Ez keresztbe igazolja a #3348-at:** ott a Picasa négy saját XMP-névtere
`MP`, `Iptc4xmpExt`, `stArea`, `mwg-rs` volt — itt az `IPTC Extension` és az
`MWG-régiók` sémaleíró külön rekeszben ül. A két mérés egymástól
függetlenül készült.

### B) A 71 mezőnév → HÉT típuskezelő

A törzs `__stricmp` (a `0x00bf697a`, az indexben így nevesítve) hívásokkal
egyezteti a kért nevet, és a találat után **pontosan egy** kezelőt hív. A 71
egyeztetés és a hét kezelő hívásszáma **kiadja egymást** (24+22+13+4+3+3+2 =
71):

| kezelő | méret | nevek | a csoport tartalma |
|---|---:|---:|---|
| `0x00ba90a0` | 106 b | **24** | felsorolás/rövid egész: `ColorSpace`, `ExposureProgram`, `MeteringMode`, `LightSource`, `SensingMethod`, `WhiteBalance`, `Contrast`, `Saturation`, `Sharpness`, `FocalLengthIn35mmFilm`, `GPSAltitudeRef`, `GPSDifferential`, … |
| `0x00ba9170` | 175 b | **22** | racionális: `ExposureTime`, `FNumber`, `ApertureValue`, `FocalLength`, `FlashEnergy`, `DigitalZoomRatio`, `GPSAltitude`, `GPSSpeed`, `GPSTrack`, `GPSImgDirection`, … |
| `0x00ba9040` | 82 b | **13** | szöveg: `UserComment`, `RelatedSoundFile`, `ImageUniqueID`, `GPSSatellites`, `GPSStatus`, `GPSMapDatum`, és a `*Ref` mezők |
| `0x00baa1f0` | 690 b | **4** | **GPS-koordináta**: `GPSLatitude`, `GPSLongitude`, `GPSDestLatitude`, `GPSDestLongitude` |
| `0x00ba9500` | 504 b | **3** | rövid egészek tömbje: `ISOSpeedRatings`, `SubjectArea`, `SubjectLocation` |
| `0x00ba9220` | 147 b | **3** | a `Flash` bitmezői: `Fired`, `Function`, `RedEyeMode` *(a `Mode` és a `Return` a felsorolás-csoportban van)* |
| `0x00ba9930` | 2220 b | **2** | dátum-idő: `DateTimeOriginal`, `DateTimeDigitized` |

⭐ **Három független kontroll, mind teljesült:**

1. a négy koordináta-mező **ugyanahhoz** a kezelőhöz megy (`0x00baa1f0`),
   a két dátum pedig egy másikhoz (`0x00ba9930`) — elcsúszott párosítás
   ezen azonnal kiderülne;
2. a koordináta-kezelő a `0x00cf4020`-on álló `double` **60,0**-nal szoroz
   (`0x00baa3ff  fmul qword ptr [0xcf4020]`) ⇒ fok/perc/másodperc bontás,
   tehát tényleg koordináta;
3. az összehasonlító a `0x00bf697a`, amit az index **`__stricmp`**-ként
   nevesít ⇒ a névegyeztetés **kis-nagybetűre érzéketlen**.

📎 Pontosítás a 10. szakaszhoz: a mezőnevek száma a törzsből **71**
(mind különböző, ismétlés nélkül), nem 70 — az index ennél a függvénynél
eggyel kevesebbet kötött ide.

### C) A Tulajdonságok-panel NEM ebből a regiszterből olvas (2026-09-19, #3366)

A #3366 célzott köre ezt a kérdést **eldöntötte**: a panel és a 14 rekeszes
XMP-séma-tábla két külön réteg.

A `0x00ba8f80` (183 bájt) a név alapján választ a 14 rekesz között: a
`0xd3b240` névlistán `edi += 0x10` lépéssel halad, egyezéskor `esi <<= 4`,
majd a `[0xd3b248 + esi]` callbacket, a rekesz adatát és paraméterét tölti
be, végül indirektül hívja a callbacket (`0x00ba9000`–`0x00ba902a`). A
hívói `0x00ba8210` és `0x00ba8f30`; az előbbi az RTTI-ben a
`ytXMPReader::vftable` metódusa. Ez tehát az **XMP-beolvasó genericus
séma-diszpécsere**, nem a Tulajdonságok-panel olvasója.

A `CPropertiesDlg` (`0x007e3210`, 7711 bájt) ezzel szemben az
`[obj+0xc0] + 0xf20` bázisból közvetlenül az `imagedata` CColumn-út mezőit
zárolja és olvassa (`0x007e3908`, `0x007e39bf`, `0x007e3a76`,
`0x007e3b2d`, `0x007e3be4`, `0x007e3c9d`, `0x007e3d9b`, `0x007e3e22`).
A teljes panel-függvény nyers kontrollja ezt adta:

| keresett cím | találat a `FUN_007e3210` teljes 7711 bájtjában |
|---|---:|
| `0xd3b248` — séma-tábla bázisa | **0** |
| `0x00ba8f80` — séma-diszpécser | **0** |
| `0x009f05c0` — `BinaryMetadata::GetString` | **0** |
| `0x00c80b84` — `personalbumid` panelkontroll | **1** |

**Válasz a #3366 címében feltett kérdésre:** a Tulajdonságok-panel a
14 rekeszes séma-táblából **egyetlen rekeszt sem olvas közvetlenül**. A panel
az `imagedata` belső rekordból olvas; a 14 rekeszes tábla az XMP-olvasó
réteghez tartozik. A termékben ezért nincs ehhez a kutatáshoz tartozó
rekeszbekötési teendő.

### D) A hét korábban névtelen rekesz feloldása

A `0x00c34300` inicializáló mind a 14 callbacket feltölti. A hét, korábban
sztring nélkül jelölt rekesz kezelője célzott diszasszemblálással azonosítható:

| rekesz | callback | binárisan kiolvasott kulcsok / szerep | fok |
|---|---|---|---|
| `0xd3b248` | `0x00bad700` | `w`, `h`; `stDim` méret-alstruktúra | erős |
| `0xd3b258` | `0x00baac00` | `Certificate`, `Marked`, `Owner`, `UsageTerms`, `WebStatement`; `xmpRights` | megerősített |
| `0xd3b288` | `0x00bab500` | `Firmware`, `FlashCompensation`, `ImageNumber`, `Lens`, `LensID`, `LensInfo`, `OwnerName`, `SerialNumber`; `aux` | megerősített |
| `0xd3b2b8` | `0x00baca80` | `AuthorsPosition`, `CaptionWriter`, `Category`, `City`, `Country`, `Credit`, `Headline`, `Instructions`, `Source`, `State`, `SupplementalCategory`, `TransmissionReference`; `photoshop` | megerősített |
| `0xd3b2e8` | `0x00bad570` | `Regions`; `MPRI` régió-konténer | erős |
| `0xd3b2f8` | `0x00bad5a0` | `Rectangle`, `PersonDisplayName`; `MPReg` régió-elem | megerősített |
| `0xd3b318` | `0x00bad760` | `x`, `y`, `w`, `h`, `d`; `stArea` terület-alstruktúra | megerősített |

A `mwg-rs` rekesz nem névtelen: a `0xd3b308` → `0x00bad610` kezelő a
`RegionList`, `AppliedToDimensions`, `Name` és `Area` kulcsokat kezeli, és
a `stArea` segédláncra támaszkodik. A `photoshop`, `aux`, `xmpRights` és
`stDim` jelenléte az Adobe XMP-Core regisztrációs katalógusával is egyezik;
az `MPRI`/`MPReg` kulcsok a Microsoft Photo 1.2 régióstruktúráját adják.

*Forrás: `0x00c34300` (236 b), `0x00ba8f80` (183 b), `0x00ba8210`
(2955 b), `0x00ba8f30` (78 b), a hét callback (`0x00bad700`,
`0x00baac00`, `0x00bab500`, `0x00baca80`, `0x00bad570`, `0x00bad5a0`,
`0x00bad760`), a `CPropertiesDlg` `0x007e3210` (7711 b), valamint a
kanonikus SQLite-index és a teljes PE nyers bájtpásztázása. A kezelők
kulcsai a célzott diszasszemblálásból; a kontrollok paraméterei a #3366
kutatási naplójában vannak.*

## 14. ⛳ A Tömörítés sor kód → szöveg táblája — 36 kód, és egy eltolás a 0/1-nél (2026-09-23, 351. kör, #3535)

*Forrás: a `0x009f23a0` (1202 b) döntési fájának programmal végigjárt
kiolvasása 0…0xFFFF között, a hívó `0x009f4b69`–`0x009f4b87`, és a
`referencia/stringres-en-hu.tsv`.*

**Mi ez.** A Tulajdonságok panel „Compression” sorának érték-formázója. A
hívó a **3-as kulcsot** kéri le (`0x009f0620(3, …)`, `0x009f4b6d`) — a
`FUN_00a00120` sorformázó szerint ez az `EXIF::Compression` —, és az értéket
**változatlanul** adja át (`eax`, `0x009f4b7c` → `call 0x009f23a0`).

**A döntési fa.** `0…0x63`: bájttábla `0x009f2880` + ugrótábla `0x009f2854`;
`0x106`; `0x7ffe…0x80b3`: bájttábla `0x009f2920` + ugrótábla `0x009f28e4`;
`0x8765`; `0x8774…0x8799`: bájttábla `0x009f29ec` + ugrótábla `0x009f29d8`;
`0x879e`, `0x879f`, `0x87a0`, `0xfde8`, `0xffff` egyenként
(`0x009f23a0`–`0x009f2808`). Minden ág `0x009ae560(alapszöveg,
"EXIF::…")` — a szövegtár-kereső, hiányzó azonosítónál az alapszöveggel.
**Ismeretlen kódnál** a kimenet `sprintf("%ld", kód)` (`0x009f280a`–
`0x009f2816`, formátum `0x00c82fd8`).

| kód | hex | ág | szövegtár-azonosító | alapszöveg | magyar (`stringres`) |
|---:|---|---|---|---|---|
| 0 | `0x0000` | `0x9f23cb` | `EXIF::Uncompressed` | Uncompressed | Tömörítetlen |
| 1 | `0x0001` | `0x9f23f7` | `EXIF::CCITT1D` | CCITT 1D | CCITT 1D |
| 3 | `0x0003` | `0x9f2406` | `EXIF::T4/Group3Fax` | T4/Group 3 Fax | T4/Group 3 fax |
| 4 | `0x0004` | `0x9f2432` | `EXIF::T6/Group4Fax` | T6/Group 4 Fax | T6/Group 4 fax |
| 5 | `0x0005` | `0x9f2441` | `EXIF::LZW` | LZW | LZW |
| 6 | `0x0006` | `0x9f246d` | `EXIF::JPEGOldStyle` | JPEG (old-style) | JPEG (régi típusú) |
| 7 | `0x0007` | `0x9f247c` | `EXIF::JPEG` | JPEG | JPEG |
| 8 | `0x0008` | `0x9f24a8` | `EXIF::AdobeDeflate` | Adobe Deflate | Adobe Deflate |
| 9 | `0x0009` | `0x9f24b7` | `EXIF::JBIGB&W` | JBIG B&W | — |
| 10 | `0x000A` | `0x9f24e3` | `EXIF::JBIGColor` | JBIG Color | JBIG színes |
| 99 | `0x0063` | `0x9f247c` | `EXIF::JPEG` | JPEG | JPEG |
| 262 | `0x0106` | `0x9f24f2` | `EXIF::Kodak262` | Kodak 262 | Kodak 262 |
| 32766 | `0x7FFE` | `0x9f2532` | `EXIF::Next` | Next | Következő |
| 32767 | `0x7FFF` | `0x9f2541` | `EXIF::SonyARWCompressed` | Sony ARW Compressed | Sony ARW-tömörítésű |
| 32769 | `0x8001` | `0x9f256d` | `EXIF::EpsonERFCompressed` | Epson ERF Compressed | Epson ERF-tömörítésű |
| 32773 | `0x8005` | `0x9f257c` | `EXIF::PackBits` | PackBits | PackBits |
| 32809 | `0x8029` | `0x9f25a8` | `EXIF::Thunderscan` | Thunderscan | Thunderscan |
| 32867 | `0x8063` | `0x9f25b7` | `EXIF::KodakKDCCompressed` | Kodak KDC Compressed | Kodak KDC-tömörítésű |
| 32895 | `0x807F` | `0x9f25e3` | `EXIF::IT8CTPAD` | IT8CTPAD | IT8CTPAD |
| 32896 | `0x8080` | `0x9f25f2` | `EXIF::IT8LW` | IT8LW | IT8LW |
| 32897 | `0x8081` | `0x9f261e` | `EXIF::IT8MP` | IT8MP | IT8MP |
| 32898 | `0x8082` | `0x9f262d` | `EXIF::IT8BL` | IT8BL | IT8BL |
| 32908 | `0x808C` | `0x9f2659` | `EXIF::PixarFilm` | PixarFilm | PixarFilm |
| 32909 | `0x808D` | `0x9f2668` | `EXIF::PixarLog` | PixarLog | PixarLog |
| 32946 | `0x80B2` | `0x9f2694` | `EXIF::Deflate` | Deflate | Veszteség nélküli tömörítés |
| 32947 | `0x80B3` | `0x9f26a3` | `EXIF::DCS` | DCS | DCS |
| 34661 | `0x8765` | `0x9f26cf` | `EXIF::JBIG` | JBIG | JBIG |
| 34676 | `0x8774` | `0x9f270c` | `EXIF::SGILog` | SGILog | SGILog |
| 34677 | `0x8775` | `0x9f271b` | `EXIF::SGILog24` | SGILog24 | SGILog24 |
| 34712 | `0x8798` | `0x9f2747` | `EXIF::JPEG2000` | JPEG 2000 | JPEG 2000 |
| 34713 | `0x8799` | `0x9f2756` | `EXIF::NikonNEFCompressed` | Nikon NEF Compressed | Nikon NEF-tömörítésű |
| 34718 | `0x879E` | `0x9f2782` | `EXIF::MDIBinaryLevelCodec` | MDI Binary Level Codec | MDI bináris szintű kodek |
| 34719 | `0x879F` | `0x9f27d2` | `EXIF::MDIProgressiveTransformCodec` | MDI Progressive Transform Codec | MDI progresszív transzformációs kodek |
| 34720 | `0x87A0` | `0x9f27a9` | `EXIF::MDIVector` | MDI Vector | MDI-vektor |
| 65000 | `0xFDE8` | `0x9f27de` | `EXIF::KodakDCRCompressed` | Kodak DCR Compressed | Kodak DCR-tömörítésű |
| 65535 | `0xFFFF` | `0x9f2822` | `EXIF::PentaxPEFCompressed` | Pentax PEF Compressed | Pentax PEF-tömörítésű |

**⚠️ Az eltolás a 0/1-nél — az eredeti saját hibája.** A 3-as kódtól minden
ág a **nyers TIFF-kódot** használja (5 LZW, 6 régi JPEG, 7 JPEG, 8 Adobe
Deflate, 99 JPEG, 262 Kodak, 32773 PackBits, 34712 JPEG 2000 …), a tárolt
érték tehát nyers. A táblában viszont **0 → Uncompressed, 1 → CCITT 1D**,
a 2-es kódnak nincs ága; a TIFF-szabványban 1 = tömörítetlen, 2 = CCITT 1D.
⇒ Az eredeti Picasa egy tömörítetlen TIFF-re **„CCITT 1D”**-t ír, a valódi
CCITT 1D-re **„2”**-t. *(Erős: a tárolt értéket a tábla többi, szabványos
ága alapján vettem nyersnek; a 3-as kulcs EXIF-beolvasóját nem követtem.)*

**A `JBIGB&W`** azonosítónak nincs magyar szövege a szövegtárban ⇒ az
alapszöveg („JBIG B&W”) jelenik meg.

**Nálunk (mérve):** `metadata/reader.py:213`
`_COMPRESSIONS = {1: "Uncompressed", 6: "JPEG", 7: "JPEG", 8: "AdobeDeflate"}`
— 4 kód a 36-ból; a 6-os nálunk „JPEG”, az eredetiben „JPEG (régi típusú)”;
az 1-es nálunk „Tömörítetlen”, az eredetiben „CCITT 1D”; ismeretlen kódnál a
sor nálunk üres, az eredetiben a szám. Fejlesztés: **#3535**.

*Bizonyítottsági fok: **megerősített** a 36 soros táblára, az ismeretlen kód
kezelésére és a hívó kulcsára (minden ág programmal kiolvasva, 0 olvasatlan);
**erős** a 0/1-eltolás következményére (lásd fent).*

## 15. ⛳ A Fényforrás (`LightSource`) kód → szöveg táblája — és hogy a panel miért NEM mutatja (2026-09-24, 355. kör, #3557)

*Forrás: a `0x009f35d0` (1216 b) ugrótáblájának programmal végigjárt
kiolvasása, a hívó `0x009f65c0`, a sorformázó `0x00a00120` 66-os és 94-es
ága, a `properties.xml` név → kulcs leképezője (`0x00633210`) és a szállított
`runtime/properties.xml`. A módszer a 14. szakaszé.*

**Mi ez.** A `0x009f35d0` a **66-os kulcs** (`0x42`; a 6.1 tábla szerint az
EXIF `0x9208` **LightSource**, SHORT) értékformázója. A hívó
`0x009f0620(0x42, …)`-vel kéri le (`0x009f68bd`), és az értéket
változatlanul adja át (`0x009f68cc` → `call 0x009f35d0`). A sorformázó
`0x00a00120` 66-os ága (`0x00a0a9d9`, ugrótábla `0x00a344b4`) ide fut
(`0x00a0ac4f`–`0x00a0ac8f`); a **felirat** az `EXIF::LightSource` azonosító:
alapszöveg **„White Balance”**, magyarul **„Fehéregyensúly”**
(`0x00a0ac5a`).

**A tábla.** `0…0x18`: ugrótábla `0x009f3a90` (25 rekesz); `0xff` külön ág
(`0x009f3a48`); minden más kód — és a táblán belüli 5–8. és 16. rekesz — az
alapesetre fut: `sprintf("%ld", kód)` (`0x009f3a78`, formátum
`0x00c82fd8`). Minden ág `0x009ae560("EXIF::…", alapszöveg)`.

| kód | ág | szövegtár-azonosító | alapszöveg | magyar (`stringres`) | EXIF-szabvány |
|---:|---|---|---|---|---|
| 0 | `0x9f35f4` | `EXIF::Unknown` | Unknown | Ismeretlen | unknown |
| 1 | `0x9f362c` | `EXIF::Sunny` | Sunny | Napos | Daylight |
| 2 | `0x9f3664` | `EXIF::Fluorescent` | Fluorescent | Fluoreszkáló | Fluorescent |
| 3 | `0x9f369c` | `EXIF::Incandescent` | Incandescent | Fehéren izzó | Tungsten |
| 4 | `0x9f36d4` | `EXIF::Flash` | Flash | Vaku | Flash |
| 9 | `0x9f370c` | `EXIF::FineWeather` | Fine Weather | Szép idő | Fine weather |
| 10 | `0x9f3744` | `EXIF::Cloudy` | Cloudy | Felhős | Cloudy |
| 11 | `0x9f377c` | `EXIF::Shade` | Shade | Árnyék | Shade |
| 12 | `0x9f37b4` | `EXIF::DaylightFlourescent` | Daylight Flourescent | Nappali fénycső | Daylight fluorescent |
| 13 | `0x9f37ec` | `EXIF::DayWhiteFlourescent` | Day White Flourescent | Nappali fehér fénycső | Day white fluorescent |
| 14 | `0x9f3824` | `EXIF::CoolWhiteFlourescent` | Cool White Flourescent | Hideg fehér fénycső | Cool white fluorescent |
| 15 | `0x9f385c` | `EXIF::WhiteFlourescent` | White Flourescent | Fehér fénycső | White fluorescent |
| 17 | `0x9f3894` | `EXIF::StandardLightA` | Standard Light A | Normál fény A | Standard light A |
| 18 | `0x9f38cc` | `EXIF::StandardLightB` | Standard Light B | Normál fény B | Standard light B |
| 19 | `0x9f3904` | `EXIF::StandardLightC` | Standard Light C | Normál fény C | Standard light C |
| 20 | `0x9f393c` | `EXIF::D55` | D55 | D55 | D55 |
| 21 | `0x9f3974` | `EXIF::D65` | D65 | D65 | D65 |
| 22 | `0x9f39ac` | `EXIF::D75` | D75 | D75 | D75 |
| 23 | `0x9f39e4` | `EXIF::D50` | D50 | D50 | D50 |
| 24 | `0x9f3a18` | `EXIF::ISOStudioTungsten` | ISO Studio Tungsten | Szabványos volfrámszálas stúdiólámpa | ISO studio tungsten |
| 255 | `0x9f3a48` | `EXIF::Other` | Other | Egyéb | Other light source |

⇒ **Nincs eltolás** (szemben a 14. szakasz 0/1-hibájával): mind a 21 ág a
szabványos kódon ül. Két eltérés a szabványtól: a 16-os kód (*Warm white
fluorescent*, EXIF 2.3) **hiányzik** — rá a szám jelenik meg —, és az
alapszövegben a *Fluorescent* négy helyen **elgépelve** áll
(„Flourescent”; a magyar szöveget ez nem érinti).

### A panel NEM ezt a sort mutatja

A panel sorrendjét és tartalmát a `runtime/properties.xml` adja. Az
olvasója (`0x00637660`) az elemekből **(kulcs, rejtett)** párokat képez, és
belőlük **láncolt listát** fűz a panel-objektumban: kezdet `[+0x1a98]`,
kulcsonként 20 bájtos rekesz, előző `+0x74`, következő `+0x78`, rejtett
jelző `+0x7c` (`0x0063777b`–`0x006377bc`). A panel frissítője
(`0x00636f80`) előbb a `0x006364c0`-val **mind a 335 kulcs** értékét
begyűjti (`0x00636582`–`0x00636989`, a sorformázó `0x006365d0`-nál), de
kiírni **csak a láncon** halad (`0x006372f8`–`0x006374d3`: `[+0x1a98]`-tól a
`+0x78` mentén). ⇒ Ami nincs a `properties.xml`-ben, annak az értéke
begyűjtődik, de **sorként nem jelenik meg**.

A név → kulcs leképező
(`0x00633210`, `__stricmp`-láncolat) **mindkét nevet ismeri**:

| elem | kulcs | cím | értékformázó |
|---|---:|---|---|
| `LightSource` | **66** (`0x42`) | `0x00633855` | a fenti tábla (`0x009f35d0`) |
| `WhiteBalance` | **94** (`0x5e`) | `0x00633af5` | `0x009f3f00`: 0 → `EXIF::Auto` („Automatikus”), 1 → `EXIF::Manual` („Kézi”), más → `%ld` |

A szállított `properties.xml` (a 3.7-es és a telepítés-mentés példánya
bájtra azonos, md5 `e8d8020208f5…`) 44 eleméből (ebből 6 `hide="1"`) **csak `<WhiteBalance/>`**
szerepel, `<LightSource/>` **nincs**. Mindkét sor felirata ráadásul
„Fehéregyensúly” (`EXIF::LightSource` és `EXIF::WhiteBalance`, ugyanaz az
alapszöveg). ⇒ **Az eredeti Tulajdonságok panelen a „Fehéregyensúly” sor a
94-es kulcs (Automatikus/Kézi); a Fényforrás-tábla csak akkor látszana, ha
a `properties.xml`-be `<LightSource/>` kerülne.**

### Nálunk (mérve)

| | eredeti | nálunk |
|---|---|---|
| „Fehéregyensúly” sor forrása | 94-es kulcs = EXIF `0xa403` | `_WHITE_BALANCE_TAG = 41987` (`0xa403`, `metadata/reader.py:52`) ✅ |
| 0 / 1 | „Automatikus” / „Kézi” | `tr("Auto")` / `tr("Manual")` → „Automatikus” / „Kézi” (`formatting.py:457–461`) ✅ |
| ismeretlen kód | a **szám** (`%ld`) | a sor **eltűnik** (`reader.py:191–194`: csak 0/1-re ad értéket) |
| Fényforrás (`0x9208`) | a panel nem mutatja | nincs olvasó — **nem is kell** |

*Bizonyítottsági fok: **megerősített** a 21 soros táblára (minden ág
programmal kiolvasva, 0 olvasatlan), a 66-os és a 94-es kulcsra, a két
formázóra, a `properties.xml` tartalmára és arra, hogy a panel csak a
`properties.xml` láncán ír ki sort — mind utasításszinten olvasva.*
