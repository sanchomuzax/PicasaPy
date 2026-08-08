# Funkciótérkép és fázisterv

A Picasa funkcionalitása → PicasaPy megvalósítási fázisok.

## 1. fázis — MVP: kezelő + néző

- Mappa-figyelés (watched folders), háttér-scanner, soha nem blokkoló UI
  - abszolút útvonalak + útvonal-átíró logika (migráció más gépről)
  - `WatchedFolders.txt` / `FRExcludeFolders.txt` megfelelőségek — **kész
    (#145, pontosítva #449-ben):** kis-nagybetű-független konfigfájl-keresés
    (`picasapy.scanner.config_files.find_config_file`), mindkét fájl olvasása
    ÉS írása (`read/write_watched_folders`, `read/write_exclude_folders`).
    **Pontosítás (#449) — a Mappakezelőben a Picasa 3-ban NÉGY vezérlő volt,
    nem három:** a Scan Always/Scan Once/Remove from Picasa hármas mellett
    egy TŐLÜK FÜGGETLEN, negyedik kapcsoló (jelölőnégyzet, nem rádiógomb)
    zárja ki a mappát (és alfáit) az **arcfelismerésből** — ez a
    `FRExcludeFolders.txt`, ld. `pmp-database.md`. A kulcs KIZÁRÓLAG az
    arcfelismerést érinti, az általános indexelést NEM (a korábbi, itt
    dokumentált feltevés téves volt: a fájlt a PicasaPy korábban
    ténylegesen sehol nem is használta, csak olvasó függvényei léteztek,
    hívó nélkül). Kikapcsoláskor a Picasa megerősítést kér („Are you sure
    you want to remove all faces and name tags from excluded folders?");
    a PicasaPy ezt a szöveget megtartja, de mivel a projektben MÉG NINCS
    arcfelismerés-motor (3. fázis), a kapcsoló egyelőre csak a
    kizárási SZÁNDÉKOT rögzíti a Picasa-kompatibilis fájlban — tényleges
    arc-/névcímke-törlés nem történik, amíg az arcfelismerés meg nem
    érkezik (ld. `app/library_controller.py: setFaceDetectionEnabled`).
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
- Kollázs (kész, #29: képrács / kontaktmásolat / keretes mozaik / képhalom)
  és mozgófilm-export (kész, #29: MP4-diavetítés áttűnéssel)
- Diavetítés, export/átméretezés
- Geocímke: Helyek-panel térképpel, geo-szűrő, `geotag=` írás (kész, #30)
- Duplikátum-keresés
- (Később mérlegelendő: nyomtatás, képernyővédő, e-mail küldés — az eredeti
  Picasa funkciói, alacsony prioritás)

## Nem cél (legalábbis egyelőre)

- Picasa Web Albums / felhő-szinkron (a szolgáltatás halott; a `P2category`,
  `IIDLIST_*` kulcsokat csak megőrizzük)
- Windows/macOS csomagolás az 1. fázisban (Linux-first; a portolhatóság
  szempont a GUI-választásnál)
