# Kutatási terv — nyitott kérdések

Állapot: 2026-07-15. A formátum-specifikációk megvannak (`docs/specs/`);
az alábbiak igényelnek még kutatást/mérést a fejlesztés megkezdése előtt.

## 1. GUI toolkit benchmark — KÉSZ (2026-07-16) ✅

**Döntés: PySide6 (Qt 6) + QML** — ld. `docs/decisions/gui-toolkit.md` (ADR-001).

Lefolyás: telepíthetőségi előszűrő (mind a 3 jelölt OK) → 5000 elemes
thumbnail-rács demó mindhárom toolkittel valódi fotókon
(`tools/benchmarks/gui/`) → felhasználói értékelés a kijelzőn. Dear PyGui
kiesett (nincs virtualizáció, 3,5 s indulás); QML ≈ GTK4 érzésre — a döntést a
keresztplatform-terv, a GPU-pipeline és a csomagolhatóság vitte a Qt felé.

Későbbi finomítás (nem blokkoló): 50k–100k elemes rács-stresszteszt és
memóriamérés a valódi MVP-rácson; képváltási latencia mérés a viewerben.

## 2. Pixelhű szűrő-reprodukció (a legnagyobb kockázat)

A kétirányú ini-kompatibilitás miatt a `filters=` láncnak ugyanazt a képet kell
adnia, mint az eredeti Picasa — de az `enhance`, `autolight`, `autocolor`,
`finetune2` pontos algoritmusa nem publikus.

Terv:
1. Eredeti Picasa 3.9 futtatása Wine alatt (vagy Windows VM-ben)
2. Referencia-készlet: ~50 változatos tesztkép × minden szűrő × paraméter-rács
3. A Picasa renderelt kimenetének mentése → golden képek
4. Saját implementáció illesztése; elfogadás SSIM / ΔE metrikával (küszöb TBD)
5. `finetune2` 5. (ismeretlen) paraméterének feltérképezése méréssel

## 3. Teljesítmény-alapmérések (RPi5) — RÉSZBEN KÉSZ (2026-07-16)

- ~~pyvips vs Pillow vs OpenCV thumbnail-áteresztés~~ ✅ KÉSZ:
  `docs/benchmarks/rpi5-image-libs.md` — **OpenCV a scanner-jelölt**
  (83 kép/s @12MP, 4 szál; teljes 140k-s könyvtár ~15–30 perc).
  Szkript: `tools/benchmarks/bench_image_libs.py`.
- **NYITVA:** SQLite indexelési stratégia 100k+ képre; FTS a kereséshez
- **NYITVA:** inotify/watchdog skálázhatóság sok mappára
- **NYITVA:** pyvips újramérés VIPS_CONCURRENCY hangolással (alacsony prio)

## 4. Arcfelismerő stack (3. fázishoz)

- Jelöltek: OpenCV (YuNet), dlib, InsightFace/ArcFace ONNX runtime-mal
- Szempontok: RPi5 CPU/NPU-n futtathatóság, csoportosítási minőség, licenc
- Picasa-kompatibilis kimenet: rect64 + contact_id + contacts kezelés

## 5. PMP-import validálás — KÉSZ (2026-07-16) ✅

- ~~`vosbergw/picasa3meta` kód auditja~~ ✅: Python 2-only, nem felélesztendő —
  formátum-dokumentációként használjuk; a parsert magunk írjuk.
  Részletek: `docs/reference-repos-audit.md`.
- ~~Teszt valódi Picasa-könyvtárral~~ ✅: 2 GB-os valódi db3 a
  `research/testdata/db3` alatt (gitignore-olt; ~140k kép, 2 371 album).
  Mind az 54 PMP + thumbindex hibátlanul parseolható a spec szerint; tartalmi
  dekódolás (filters, crop64, variant-dátum, deferredregion) igazolt.
  Új formátum-tények átvezetve: `docs/specs/pmp-database.md` (validálási
  szakasz) és `picasa-ini-format.md` (új szűrők, előjeles floatok).
- **2026-07-16 kiegészítés:** a tesztkészlet már a teljes `Picasa2` +
  `Picasa2Albums` mappa (`research/testdata/`). `contacts.xml` **nem létezik**
  ebben a telepítésben (nincs contacts mappa) — az arcnevek a
  `deferredregion` oszlopban élnek tisztanévvel; az importnak ezt az esetet
  kezelnie kell (contacts.xml opcionális!). A `watchedfolders.txt` /
  `frexcludefolders.txt` élesben **kisbetűs** fájlnevű → kis-nagybetű-független
  keresés kell. Formátumuk igazolt: soronként abszolút Windows-útvonal, több
  meghajtóról is (`C:\`, `L:\`).
- **NYITVA (kis kockázat):** `facerect=0x1` szentinel jelentése.

## 6. Referencia-repók klónozása és audit — KÉSZ (2026-07-15)

Mind az 5 repó a `research/repos/` alatt; audit: `docs/reference-repos-audit.md`.
Fő eredmények: PMP-fejléc két független implementációból keresztvalidálva;
thumbindex.db arc-bejegyzés logika megértve; rect64 zfill(16) + EXIF-orientáció
spec-javítás. Licencek: PicasaDBReader MIT, a többi GPL-3.0.

**ÚJ NYITOTT DÖNTÉS → 7. pont.**

## 7. PicasaPy licenc-választás — KÉSZ (2026-07-16) ✅

**Döntés: GPL-3.0** (LICENSE a repo gyökerében). A felhasználó célja a szabad,
ingyenes megosztás — a GPL-3.0 ezt garantálja, és feloldja a blokkot: mostantól
mind a 4 GPL-es referencia-repóból (picasa3meta, picasa2digikam, picasa2xmp,
metaSave) szabadon portolható kód, attribúcióval.

## NotebookLM forrás

Notebook: „Picasa metaadatok és adatbázisok dekódolási útmutatója"
ID: `f70b0a1c-1ef2-4f72-98ae-2bb7e946ba1e` (30 forrás)
https://notebooklm.google.com/notebook/f70b0a1c-1ef2-4f72-98ae-2bb7e946ba1e
