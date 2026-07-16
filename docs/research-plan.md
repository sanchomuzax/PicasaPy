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

Állapot (2026-07-16): **golden kit elkészült és átadva** — a felhasználó
Windows 10 + Picasa gépén fut le (Wine nem kell; a Pi ARM-os, az x86-os
Picasa ott nem futna).

1. ~~Golden kit~~ ✅: `tools/golden/make_golden_kit.py` →
   `research/golden-kit/` (238 tesztkép: 3 szintetikus chart + 6 valódi fotó,
   54 variáns 10 mappában, előre írt .picasa.ini-kkel; a valódi könyvtárból
   kinyert Vignette/glow/finetune paraméterekkel és 5 komplex lánccal).
   Zip: `research/golden-kit.zip` (83 MB). Útmutató: `OLVASS-EL.txt` a kitben.
2. ~~Golden exportok~~ ✅ (2026-07-16): mind a 10 mappa hiánytalanul
   visszaérkezett (`research/testdata/golden-kit-result/`).
3. ~~Elemzés 1. kör~~ ✅: **eredmények: `docs/specs/filters-decoded.md`** —
   crop renderelési szabály (crop= kulcs!), bw=Rec.601, finetune2 mind az
   5 paramétere azonosítva (p1=fill, p4=semleges szín, p5=színhő), fill
   LUT-család mérve, autolight/autocolor algoritmus-típus megerősítve.
   LUT-ok: `research/golden-analysis/luts.json`.
4. ~~Javító kör (crop)~~ ✅ (2026-07-16): fix-kit exportálva
   (`research/testdata/golden-kit-fix/`), crop-kerekítési szabály igazolva.
   **Picasa verzió: 3.9.141 Build 255.**
5. ~~2. elemzési kör~~ ✅: sepia/warm LUT-ok, grain2 sztochasztikus,
   sat gain-tábla, fill negatív eredmények (nem gamma / nem kompozíciós /
   nem mestergörbe-keverék) — ld. filters-decoded.md.
6. ~~3. kit-kör + elemzés~~ ✅ (2026-07-16): **autolight teljesen megfejtve**
   (globális min–max stretch), **enhance szerkezete megfejtve**
   (fixLUT∘stretch∘autocolor, reziduál mentve), **fill megoldva** (2D LUT,
   ±1,25/255), h/s/temp sweep LUT-ok mentve — ld. filters-decoded.md.
7. ~~4. kör~~ ✅ (2026-07-16): **tilt megfejtve** (θ=p·0,2 rad; autoskála
   cos θ+(W/H)sin θ), **unsharp v1=v2(0,6)**, USM-modell σ≈1,0/1,21·s,
   Vignette-maszk lemérve, autocolor csillapított lineáris WB (részleges).
8. **HÁTRAVAN a #2 lezárásához:** összehasonlító harness (PicasaPy render
   vs golden, SSIM/ΔE) — ez már a 2. fázis szerkesztő-implementációjával
   együtt készül; kis nyitott kérdések: filters-decoded.md „Nyitva" szakasz.
   **A szűrő-visszafejtés a gyakori szerkesztések 95%+-ára kész.**

## 3. Teljesítmény-alapmérések (RPi5) — KÉSZ ✅ (2026-07-16)

- ~~pyvips vs Pillow vs OpenCV~~ ✅: `docs/benchmarks/rpi5-image-libs.md` —
  **OpenCV a scanner-jelölt** (83 kép/s @12MP; 140k könyvtár ~15–30 perc).
- ~~SQLite + inotify~~ ✅: `docs/benchmarks/rpi5-sqlite-inotify.md` —
  133k valódi útvonal insert 1,06 s; FTS5 keresés 9 ms; 2 400 mappa watch
  55 ms, latencia <2 ms. Séma-elvek rögzítve (WAL, partial index, FTS5).
  **Fontos:** NAS-mounton inotify nem működik → periodikus rescan fallback.
- Nyitva (alacsony prio): pyvips újramérés VIPS_CONCURRENCY hangolással.

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
