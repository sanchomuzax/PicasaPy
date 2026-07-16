# Benchmark: képfeldolgozó könyvtárak (RPi5) — research-plan #3

Dátum: 2026-07-16 · Gép: Raspberry Pi 5 (4×Cortex-A76, 16 GB RAM, NVMe) ·
Python 3.13.5 · Szkript: `tools/benchmarks/bench_image_libs.py`

Verziók: Pillow 12.3.0 · pyvips 3.1.1 (libvips 8.18, bundled binary) ·
OpenCV 5.0.0 (opencv-python-headless)

## Feladatok

1. **thumb256+enc** — JPEG dekód → 256 px thumbnail → JPEG enkód (q85).
   Ez a scanner/indexelő fő terhelése.
2. **view1600** — JPEG dekód → 1600 px nézőkép memóriába (viewer-útvonal).

Készletek: 100 valódi 1080p fotó (~0,7 MB) + 40 szintetikus 12 MP JPEG
(4624×2601, q92, valódi képekből felskálázva).

## Eredmények (kép/másodperc, nagyobb = jobb)

### 1080p készlet

| Lib | thumb 1 szál | thumb 4 szál | view 1 szál | view 4 szál |
|---|---|---|---|---|
| Pillow | 65,5 | 151,4 | 16,3 | 36,8 |
| pyvips | 35,6 | 73,8 | 18,1 | 23,8 |
| **OpenCV** | **106,7** | **312,3** | **64,9*** | **226,4*** |

### 12 MP készlet

| Lib | thumb 1 szál | thumb 4 szál | view 1 szál | view 4 szál |
|---|---|---|---|---|
| Pillow | 28,7 | 63,9 | 4,6 | 8,5 |
| pyvips | 23,8 | 53,7 | 4,4 | 7,0 |
| **OpenCV** | 28,4 | **83,1** | **14,6** | **25,3** |

## Módszertani megjegyzések (fontos!)

- Az OpenCV `IMREAD_REDUCED_COLOR_n` DCT-skálázott dekódot használ (mint a
  Pillow `draft()` és a pyvips shrink-on-load) — de fix 1/2..1/8 lépcsőkben.
  Az 1080p készleten a view1600 (*csillagozott*) értékek 960 px-es kimenetet
  adtak (cél alatti) → azok az értékek NEM összehasonlíthatók; a 12 MP-s
  számok korrektek.
- A pyvips-nek saját belső szálkezelése van; a 4 külső worker túliratkozást
  okozhat → a pyvips többszálú számai alulbecsülhetnek. Finomhangolás
  (VIPS_CONCURRENCY) későbbi körben.
- A GIL-viselkedés a lényegi különbség: az OpenCV műveletei teljesen elengedik
  a GIL-t → közel lineáris skálázódás 4 szálra.

## Következtetések

1. **Scanner/thumbnailer jelölt: OpenCV** — 12 MP-nél 83 kép/s (4 szál).
   A valódi, 140 758 bejegyzéses tesztkönyvtárunk (vegyes 1080p–12MP) teljes
   kezdeti indexelése így nagyságrendileg **~15–30 perc** az RPi5-ön — bőven
   elfogadható egyszeri műveletként.
2. **Pillow**: egyszálú thumb-ra meglepően jó (draft()), viewer-méretre gyenge.
   Egyszerűbb műveletekhez, kompatibilitási fallbacknek marad.
3. **pyvips**: itt nem hozta a papírformát; streaming/óriáskép esetekre még
   érdekes lehet, de az MVP-hez nem elsődleges.
4. A **viewer** útvonal döntése a GUI-választással együtt dől el (Qt saját
   képdekódere / QImage is játszik) — ld. GUI benchmark.

## GUI toolkit telepíthetőség (research-plan #1 előszűrő) — mind zöld ✅

| Toolkit | pip (aarch64, py3.13) | apt (Debian 13) |
|---|---|---|
| PySide6 | ✅ 6.11.1 hivatalos wheel | ✅ 6.8.2 |
| GTK4 + PyGObject | — | ✅ GTK 4.18, python3-gi 3.50 (telepítve) |
| Dear PyGui | ✅ 2.3.1 wheel | — |

Egyik jelölt sem esik ki telepíthetőség miatt. Következő lépés: interaktív
FPS-benchmark (thumbnail-rács demó mindhárom toolkittel), amit a felhasználó
a kijelzőn értékel.
