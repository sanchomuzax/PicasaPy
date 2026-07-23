# Hogyan készült a kutatás?

A PicasaPy nem „vaktában" indult: a fejlesztés első fázisa egy alapos
**formátum- és algoritmus-kutatás** volt (2026. július), amelynek célja a
Picasa 3.x belső működésének teljes megértése — enélkül a kétirányú
`.picasa.ini` kompatibilitás (a projekt 1. számú rögzített döntése) nem
volna teljesíthető.

## Az infografika

Az alábbi összefoglaló infografika a kutatás tudásbázisából készült, és két
fő területet mutat be: hogyan kezeli a Picasa a fotókat (adatbázis-alapú
indexelés, a rejtett `.picasa.ini` fájlok, adatbázis-helyreállítás), valamint
a képfeldolgozás alapjait (Gaussian/Median/Bilateral szűrők, 2D konvolúció):

<p align="center">
  <img src="assets/notebooklm-infografika.png" alt="Picasa és a Képkezelés Tudománya — összefoglaló infografika" width="900">
</p>

*Az infografika a Google NotebookLM-mel készült (2026-07-22), a kutatási
tudásbázis 30 forrásából.*

## A kutatás eszközei és menete

1. **NotebookLM tudásbázis.** A kutatás gerince a „Picasa metaadatok és
   adatbázisok dekódolási útmutatója" NotebookLM-notebook, 30 összegyűjtött
   forrással (formátum-leírások, fórum-archívumok, reverse-engineering
   dokumentumok). Ebből születtek a specifikációk első vázlatai — és ez az
   infografika is.

2. **Referencia-repók auditja.** Négy nyílt forráskódú projekt
   (PicasaDBReader, picasa3meta, picasa2digikam, picasa2xmp) kódját
   kereszt-validáltuk a formátumok megfejtéséhez —
   ld. [`reference-repos-audit.md`](reference-repos-audit.md).

3. **Valódi adatokon való igazolás.** A PMP/db3 és thumbindex specifikációt
   egy valódi, 2 GB-os Picasa-adatbázison (140 ezer kép) ellenőriztük —
   ld. [`specs/pmp-database.md`](specs/pmp-database.md).

4. **Golden-image módszer a szűrőkhöz.** A Picasa szerkesztő-algoritmusai
   (enhance, autolight, finetune2…) nem publikusak, ezért mérőképes
   „golden kit" készült: előre gyártott tesztképek + `.picasa.ini`-k, amiket
   egy eredeti Windows-os Picasa 3.9 exportált vissza — az összevetésből
   egzakt LUT-ok és transzformációk adódtak,
   ld. [`specs/filters-decoded.md`](specs/filters-decoded.md).

5. **GUI-benchmark.** A felület-technológiát mérés döntötte el (5000 elemes
   thumbnail-rács három toolkittel, RPi5-ön) —
   ld. [`decisions/gui-toolkit.md`](decisions/gui-toolkit.md) (ADR-001).

## A kutatás eredményei

- [`specs/picasa-ini-format.md`](specs/picasa-ini-format.md) — a `.picasa.ini` teljes szerkezete, filters-mátrix, rect64.
- [`specs/pmp-database.md`](specs/pmp-database.md) — db3/PMP/thumbindex formátum és import-terv.
- [`specs/filters-decoded.md`](specs/filters-decoded.md) — a szerkesztő-szűrők dekódolt algoritmusai.
- [`specs/feature-map.md`](specs/feature-map.md) — a funkciók fázisokra bontva (V1 kezelő+néző, V2 szerkesztő, V3 arcok).
- [`specs/ux-principles.md`](specs/ux-principles.md) — a Picasa UX-alapelvei.
- [`research-plan.md`](research-plan.md) — a nyitott kutatási kérdések és állapotuk.
