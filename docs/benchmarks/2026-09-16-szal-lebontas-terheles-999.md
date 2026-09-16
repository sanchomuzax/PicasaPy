# A háttérszálak lebontása terhelés alatt — a #999 zárómérése

**Dátum:** 2026-09-16 · **Jegy:** #999 (és a már lezárt #988) · **Gép:** RPi5,
négy mag, `main` @ `3ec1aa66`

## Mit kellett bizonyítani

A #999 három teendőt írt elő. Az első kettő korábbi körökben elkészült:

| teendő | hol készült el |
|---|---|
| a két eset (`BackgroundWorkerMixin` vs. `effect_thumbnails.py`) életciklusának összevetése | #1087 / #1112 — a válasz: **nem** ugyanaz volt (szál vs. `QThreadPool`), ezért a nyilvántartás mindkét fajtát fedi (`_ALL_WORKERS`, `_POOL_OWNERS`) |
| determinista bevárás ott, ahol a szálat indítjuk | `worker_thread.py`: folyamat-szintű nyilvántartás + `wait_for_all_background_workers`, ciklusban (#2721: a bevárás ALATT induló szál is beleszámít), a fixture a controllert le is zárja (#3042/#3043) |

A harmadik teendő **mérés**: a két érintett fájl **terhelés alatt** is
stabil-e. Ez a lap ezt a mérést rögzíti.

## A mérés menete

A #430 gyökérok-leírása szerint a versenyhelyzet ablakát a
**coverage-nyomkövetés** nagyságrendekkel kitágítja — ezért a terhelés két
formában ment:

1. a két fájl **egyidejűleg**, csupasz pytesttel (3 kör);
2. a két fájl **egyidejűleg**, `coverage run -p --source=src` alatt (3 kör).

Mindegyik részfutás memóriaplafon alatt (`MemoryMax=2400M`,
`MemorySwapMax=0`), külön `--basetemp`-pel, `-p no:randomly` mellett.

## Eredmény

| kör | `test_editor.py` | `test_collage_controller_943.py` |
|---|---|---|
| 1 (csupasz) | 38 passed, 58,9 s, kilépőkód 0 | 145 passed / 1 skipped, 19,3 s, 0 |
| 2 (csupasz) | 38 passed, 76,7 s, 0 | 145 passed / 1 skipped, 22,8 s, 0 |
| 3 (csupasz) | 38 passed, 67,4 s, 0 | 145 passed / 1 skipped, 27,1 s, 0 |
| 4 (coverage) | 38 passed, 75,6 s, 0 | 145 passed / 1 skipped, 24,7 s, 0 |
| 5 (coverage) | 38 passed, 78,3 s, 0 | 145 passed / 1 skipped, 20,6 s, 0 |
| 6 (coverage) | 38 passed, 88,6 s, 0 | 145 passed / 1 skipped, 21,5 s, 0 |

**Hat körből hatszor nulla kilépőkód**, egyetlen `exit -11` (SIGSEGV), `Fatal
Python error` vagy bukó teszt sem volt. A `lefedettseg.yml` legutóbbi három
futása (2026-09-05, 09-06, 09-13) szintén zöld — ez a CI oldali független
megerősítés, mert épp az a kör fut `--cov` alatt.

## Amit a mérés NEM bizonyít

Versenyhelyzet hiányát mérni elvileg nem lehet: hat zöld kör azt mondja, hogy
a tünet a javítás után **nem reprodukálható** ott, ahol előtte kétszer
reprodukálható volt (#992). A visszatérés elleni fogat nem ez a lap adja,
hanem a `tests/app/test_hatterszal_nyilvantartas_988.py` őrei — azok forrás-
szinten tiltják a kikerülési utat (szálindítás a mixinen kívül, `QThreadPool`
`register_pool_owner` nélkül) és a bevárás hamis verdiktjét.
