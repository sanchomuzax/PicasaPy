# Benchmark: SQLite index + inotify (RPi5) — research-plan #3 lezárása

Dátum: 2026-07-16 · Gép: RPi5 (4 mag, 16 GB, NVMe) · Python 3.13 ·
Szkript: `tools/benchmarks/bench_sqlite_inotify.py`

Adathalmaz: a **valódi** Picasa thumbindex 133 089 fájl-útvonala (nem
szintetikus), realisztikus csillag/caption/keyword eloszlással.

## SQLite (WAL, synchronous=NORMAL, FTS5)

| Művelet | Eredmény |
|---|---|
| 133 089 sor bulk-insert | **1,06 s** (125 ezer sor/s) |
| FTS5 index építés | 0,53 s |
| Mappa-lista (98 kép, indexelt) | 0,3 ms |
| Csillagozottak (2 832 db, partial index) | 13,8 ms |
| Szöveg-keresés LIKE (12 099 találat) | 47,6 ms |
| Szöveg-keresés **FTS5 MATCH** (ugyanaz) | **9,1 ms** (5×) |
| Lapozás (200/oldal, OFFSET 1000) | 0,2 ms |
| DB méret (140k kép, metaadatokkal) | 49 MB |

**Következtetés:** az SQLite bőven elég az MVP-nek — a teljes 140k-s könyvtár
újraindexelése ~2 s (a thumbnail-generálás dominál, nem a db). Séma-elvek:
WAL mód, `folder` index, partial index a csillagra, **FTS5** a
caption/keywords/név keresésre (LIKE helyett). Külső content-táblás FTS
működik, a méret-többlet elfogadható.

## inotify (watchdog lib)

| Mérés | Eredmény |
|---|---|
| 2 400 mappa rekurzív watch felállítása | **55 ms** |
| Esemény-latencia (fájl-létrehozás → callback) | medián 0,4 ms, max 1,9 ms |
| Rendszer-limit (`max_user_watches`) | 131 059 (a 2 344 valódi mappához bőven elég) |

**Következtetés:** a watchdog/inotify gond nélkül skálázódik a felhasználói
könyvtár méretére; a Picasa-féle „azonnal észreveszi az új képet" élmény
hozható. Megjegyzés: **NAS (SMB/NFS) mount-on az inotify nem kap eseményt**
távoli változásról → hálózati mappákra periodikus rescan kell fallbackként
(a Picasa is ezt csinálta a folyamatos háttér-pásztázással).

## #3 státusz: LEZÁRVA ✅

Mindhárom mérés kész: képfeldolgozó lib (OpenCV — ld. rpi5-image-libs.md),
SQLite-stratégia, inotify-skálázás. Nyitva maradt (alacsony prio, MVP után):
pyvips újramérés VIPS_CONCURRENCY hangolással.
