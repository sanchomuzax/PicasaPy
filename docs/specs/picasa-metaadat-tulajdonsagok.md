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

1. **A Nikon tábla 416 rekord, nem 417.** A `0x0087c5b0`-on álló hivatkozás
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

⚠️ **NYITVA:** a `0x009f0fd0` (a 105-ös tömb lekérője) **elem-egysége** —
a méret-kapu `0x36`-ja és a `+0x6c`-ig tartó olvasás csak akkor fér össze, ha
a méret nem bájtban értendő. A megszerzés útja: a `0x009f0fd0` törzse, és egy
MÁSIK, ismert hosszú tömbre adott hívása kontrollként.

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
