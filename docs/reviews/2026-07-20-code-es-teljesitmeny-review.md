# Code + teljesítmény review és spec-lefedettség — 2026-07-20

Átfogó felülvizsgálat a kutatási/MVP-fázis „racionalizálási” köréhez. Négy
párhuzamos vizsgálat futott: mag-könyvtárak (ini/pmp/metadata/index/scanner/
thumbs/fileops/export), app+GUI réteg (app/, qml/, edit/, render/),
teljesítmény (RPi5 + NAS fókusz), spec-lefedettség (docs/specs/ vs kód).
A findingok jegyekbe kerültek: **#128–#152** (25 új jegy), plusz megjegyzés
a #1-en. Ez a dokumentum a tartós összefoglaló és a priorizálási javaslat.

## Összkép

A kódbázis állapota **jó**: a `.picasa.ini` round-trip réteg (a projekt
legkritikusabb invariánsa) byte-pontos, jól átgondolt és alaposan tesztelt;
a render-réteg számai egyeznek a golden-mérésekkel; az SQLite-alapok
(WAL, migrációk, FTS5) rendben vannak; 900+ teszt fut zölden ~30 mp alatt.
Kritikus, adatvesztő hibát a magrétegben a review nem talált.

A két legfontosabb rendszerszintű megállapítás:

1. **A GUI-szál túlterhelt.** Több művelet (csillagozás, felirat, keresés,
   élő előnézet, EXIF-panel) szinkron fájl-I/O-t vagy nehéz számítást futtat
   a fő szálon — NAS-on és RPi5-ön ez már a mostani feature-setnél fagyásokat
   okoz. (#138, #140, #141)
2. **A frissítési stratégia „mindent újra” elvű.** Minden változásnál teljes
   mappa-resync + teljes feed-újratöltés + modell-reset fut, a sync pedig
   változatlan fájlokra is ír (FTS-churn, flash-kopás). Skálázódásnál (50k+
   fotó) ez lesz a fal. (#139, #142, #143)

## Legsúlyosabb hibák (P1)

| Jegy | Mi ez |
|---|---|
| #128 | Memóriaszivárgás a nézőben: minden átlapozott kép dekódolt formában a memóriában marad → RPi5-ön OOM-kockázat |
| #129 | IPTC-írás: nincs fsync az eredeti fotófájl cseréje előtt (crash = csonka eredeti), jogvesztés NAS-on, ismeretlen IPTC-mezők eldobása (round-trip-elv sérül) |

## Fontosabb hibák (P2)

- **#130** crop64-lánc kaszkád-vágása — a saját spec (filters-decoded
  „KRITIKUS javítás”) ellenében; valódi Picasa-fájlokon rossz kivágás.
- **#131** A döntés-csúszka nullázza a mentett tilt-et.
- **#132** Üresen elérhető gyökér (lecsatolt NAS-mount) törli az indexet.
- **#133** Legacy (CP1250) ini-k: mentési crash ékezetes szövegnél,
  U+0085-fantomszekció, mojibake.
- **#134** Egy óriáskép (DecompressionBomb) megakasztja a teljes syncet.
- **#135** Háttér-sync mellékhatások: 5 percenkénti görgetés-visszaugrás +
  sor-index alapú kijelölés elcsúszása (rossz képre mehet művelet).
- **#136** Export: EXIF/IPTC-vesztés, felesleges újrakódolás, néma hiba,
  a szerkesztések nem égnek bele.
- **#137** Nincs ini-ütközésdetektálás a párhuzamosan futó Picasa ellen
  (lost update — spec írási szabály 5.).

## Teljesítmény — mi fáj MOST

1. **#138** Kereső-javaslatok: minden leütésnél az ÖSSZES .picasa.ini
   beolvasása a NAS-ról — és az eredmény el is dobódik (a leggyorsabban
   javítható, legnagyobb hatású tétel). + keresés-debounce.
2. **#140** Élő előnézet: teljes 2560 px-es float64-lánc a GUI-szálon minden
   csúszka-eseményre (prefix-cache, kicsinyített interaktív render, float32/LUT).
3. **#139** Sync FTS-churn: változatlan fájlokra is UPDATE + FTS-újraírás
   minden syncnél (flash-kopás RPi5-ön).
4. **#141** Csillag/felirat/forgatás: NAS-fsync + teljes mappa-resync +
   teljes feed-újratöltés a GUI-szálon kattintásonként.

## Teljesítmény — mi fáj SKÁLÁZÓDÁSNÁL

5. **#142** A rács csoporton belül nem virtualizál (3000 képes mappa = 3000
   élő delegate + thumbnail-vihar); teljes all_photos-újratöltés minden
   frissítésnél. DoD-ben a 100k-s stresszmérés (research-plan 1.).
6. **#143** Scanner: fájlonkénti stat a NAS-on + 5 percenkénti teljes rescan
   → DirEntry-stat, mappa-mtime-alapú inkrementális rescan.
7. **#144** Thumbnail-pipeline egy szálon (a benchmark szerint 4 szálon ~3×);
   szűrt-thumb cache és cache-takarító hiányzik.

**Megtartandó jó minták:** WAL/NORMAL pragmák, mappánkénti sync-commit,
redukált JPEG-dekód, 2560 px-es sourceSize-plafon, LUT-alapú fill/enhance,
a thumbnail-provider kivétel-védelme, immutábilis EditSession + seedelt undo.

## Spec-lefedettség (hiányok, most jegyezve)

Az 1. fázis (MVP kezelő+néző) nagyrészt kész, sőt 3. fázisú tételek
(diavetítés, export) előre is készültek. Ami hiányzott és jegy nélkül állt:

- **#145** FRExcludeFolders.txt + kis-nagybetű-független konfigfájl-keresés
- **#146** Meglévő Picasa-telepítés automatikus felismerése (WatchedFolders-átvétel)
- **#147** faces= keretek megjelenítése a nézőben (olvasás-szint; felismerés → #26)
- **#148** Retusálás + szöveg-eszköz (tiltott gombok mögé; formátum-kutatással)
- **#149** Hiányzó szűrő-renderek: **Vignette** (élesben a 12. leggyakoribb!),
  glow2, tint, ansel, radblur, radsat, dir_tint
- **#152** Copy/Paste All Effects élesítése
- #1 kiegészítő megjegyzés: az importer még nem nyeri ki a képsorrendet,
  ignorált arcokat, videó-metaadatot (a jegy szövege fedi, a kód még nem)

Már jeggyel fedett hiányok (nem duplikáltuk): #1, #3, #4, #9, #20, #21, #22,
#23, #24, #25, #26, #27, #28, #29, #30, #31, #32, #115; hibák: #53, #67, #112.

## Racionalizálás / kódminőség

- **#150** `controller.py` (1214 sor) és `Main.qml` (1526 sor) felbontása a
  800 soros limit alá — mindkettő forró fájl, minden munka ezekben ütközik
  (integrátor-feladat).
- **#151** Magréteg kis javítások gyűjtő: trashinfo-sorrend, remap-casefold,
  thumbindex-határellenőrzés, watcher rejtett-gyökér szűrés, debounce-plafon,
  duplikált helperek (`_write_atomic` 4 változata — a közösítés a #129 része).

## Javasolt sorrend (priorizálási tanács)

1. **Gyors győzelmek (kicsi munka, nagy hatás):** #138 (javaslat-ág kihagyása
   + debounce), #134 (kivétel-elkapás), #139 (feltételes UPDATE), #128 (LRU).
2. **Adatbiztonság:** #129 (IPTC-írás), #132 (üres gyökér), #137 (lost update),
   #133 (legacy ini).
3. **Élmény:** #141 + #135 (kattintás-fagyás és görgetés-ugrás — együtt
   érdemes, mindkettő a frissítési stratégiát érinti), #140 (előnézet), #131.
4. **Kompatibilitás:** #130 (crop64), #136 (export), #149 (Vignette).
5. **Skálázódás (mérés után):** #142, #143, #144 — előbb a 100k-s
   stresszmérés (#142 DoD), hogy adat vezérelje.
6. **Folyamatosan:** #150 felbontás (integrátor, konfliktus-csökkentés).
