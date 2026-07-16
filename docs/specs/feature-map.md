# Funkciótérkép és fázisterv

A Picasa funkcionalitása → PicasaPy megvalósítási fázisok.

## 1. fázis — MVP: kezelő + néző

- Mappa-figyelés (watched folders), háttér-scanner, soha nem blokkoló UI
  - abszolút útvonalak + útvonal-átíró logika (migráció más gépről)
  - `WatchedFolders.txt` / `FRExcludeFolders.txt` megfelelőségek
- Villámgyors thumbnail-rács nagy (100k+ képes) könyvtárakra; thumbnail-cache
- Csillagozás, feliratok, kulcsszavak; virtuális albumok; keresés/szűrés
- Meglévő Picasa-könyvtár felismerése; **kétirányú** `.picasa.ini` írás/olvasás
  - star, caption, keywords, albums, faces, rotate olvasás/írás
  - `filters=` lánc megőrzése akkor is, amíg a renderelés nincs kész (round-trip)
- PMP/db3 **olvasás**: import meglévő telepítésből + `contacts.xml` (ha van)
  - csak-db-ben élő adatok mentése: képsorrend, ignorált arcok, videó-metaadat
  - **ISMÉTELHETŐ import** (7. rögzített döntés): a felhasználó a fejlesztés
    alatt tovább használja a Windows-os Picasát → a frissítés útja:
    a) `.picasa.ini`-k a fotómappák mellett (NAS) mindig frissek — a scanner
    ezekből folyamatosan szinkronizál; b) db3-only adatokhoz friss db3-másolat
    újraimportja path-remappel, ütközésnél az újabb nyer (mtime alapján)
- EXIF/IPTC/XMP olvasás; JPEG-nél IPTC caption/keywords írás (Picasa-viselkedés)

## 2. fázis — Szerkesztő

- Nem-destruktív pipeline: `filters=` lánc valós idejű alkalmazása
  - cél: **pixelhű** egyezés az eredeti Picasával (kétirányú kompat miatt kötelező)
  - GPU-alapú renderelés (shader-lánc, ping-pong textúrák) — RPi5-ön validálandó
- Eszközök: crop (rect64, folyamatos sorozat-vágás!), tilt, redeye,
  I'm Feeling Lucky (enhance), autolight/autocolor, retouch,
  finetune (fill light / highlights / shadows / színhőmérséklet), unsharp
- Effektek: sepia, bw, warm, grain2, tint, sat, radblur, glow2, ansel,
  radsat, dir_tint; text overlay
- „Mentés" viselkedés: renderelt kép az eredeti helyére, eredeti a
  `.picasaoriginals/`-ba; visszaállítás; `redo=` verem kezelése

## 3. fázis — Arcok és extrák

- Arcfelismerés + arccsoportosítás (lib kutatandó: OpenCV / dlib / InsightFace)
  - tárolás: `faces=rect64(...),contact_id` + Contacts (Picasa-kompatibilis)
  - export: XMP MWG-RS + `HierarchicalSubject` `people|Név`
- Kollázs, diavetítés, export/átméretezés, geotag-szerkesztés
- Duplikátum-keresés
- (Később mérlegelendő: nyomtatás, képernyővédő, e-mail küldés — az eredeti
  Picasa funkciói, alacsony prioritás)

## Nem cél (legalábbis egyelőre)

- Picasa Web Albums / felhő-szinkron (a szolgáltatás halott; a `P2category`,
  `IIDLIST_*` kulcsokat csak megőrizzük)
- Windows/macOS csomagolás az 1. fázisban (Linux-first; a portolhatóság
  szempont a GUI-választásnál)
