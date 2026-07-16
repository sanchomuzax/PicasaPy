# PicasaPy

## Projekt célja

A Google **Picasa** képszerkesztő és fotókezelő szoftver teljes újraírása **Python** alapon. A Picasa-t a Google 2016-ban kivezette; a cél egy modern, nyílt, keresztplatformos utód létrehozása, amely megőrzi az eredeti szoftver erősségeit (gyors fotókezelés, nem-destruktív szerkesztés, arcfelismerés, albumkezelés).

## Jelenlegi fázis: KUTATÁS (research)

A formátum-kutatás első köre lezárult (2026-07-15), az eredmények a `docs/specs/`
alatt. A hátralévő kutatási feladatok: `docs/research-plan.md`.

Elsődleges tudásforrás: NotebookLM „Picasa metaadatok és adatbázisok dekódolási
útmutatója" notebook (ID: `f70b0a1c-1ef2-4f72-98ae-2bb7e946ba1e`, 30 forrás).

## Rögzített döntések (2026-07-15)

1. **Teljes kétirányú `.picasa.ini` kompatibilitás** — a PicasaPy ugyanazt a
   formátumot írja és olvassa, mint a Picasa 3.x (drop-in utód, párhuzamos
   használat lehetséges). Round-trip elv: amit nem értünk, változatlanul visszaírjuk.
2. **Linux-first** — fejlesztés RPi5-ön; Windows/macOS később.
3. **GUI toolkit: benchmark dönt** (PySide6/Qt a fő jelölt) — ld. research-plan.
4. **MVP = kezelő + néző** (1. fázis); szerkesztő a 2., arcok a 3. fázis —
   ld. `docs/specs/feature-map.md`.
5. PMP/db3 adatbázist **csak olvassuk** (import); saját index: SQLite.
6. **Licenc: GPL-3.0** (2026-07-16) — szabad megosztás; a GPL-es
   referencia-repókból portolható kód attribúcióval.

## Tech stack

- Nyelv: Python 3.12+
- GUI: TBD (benchmark alapján; fő jelölt PySide6)
- Képfeldolgozás: TBD (pyvips / Pillow-SIMD / OpenCV mérés alapján)
- Adattárolás: `.picasa.ini` (igazságforrás) + SQLite index + XMP export

## Dokumentumtérkép

- `docs/specs/picasa-ini-format.md` — ini szerkezet, filters mátrix, rect64
- `docs/specs/pmp-database.md` — db3/PMP/thumbindex, contacts.xml, import
- `docs/specs/feature-map.md` — funkciók fázisokra bontva
- `docs/specs/ux-principles.md` — a Picasa UX-alapelvei (minden UI-döntés mércéje)
- `docs/research-plan.md` — nyitott kutatási kérdések

## Fejlesztési elvek

A globális `~/.claude/rules/` szabályok érvényesek, kiemelten:

- **Immutability:** ne mutálj, hozz létre új objektumokat.
- **Sok kicsi fájl > kevés nagy fájl** (200–400 sor tipikus, 800 max).
- **TDD:** teszt előbb (RED → GREEN → REFACTOR), 80%+ lefedettség.
- **Input-validáció és átfogó hibakezelés** mindenhol.
- **Nincs hardkódolt titok, nincs `console.log`/nyomkövetés a kész kódban.**

## Fájlok

- `CLAUDE.md` — ez a fájl: projekt-kontextus és irányelvek.
- `MEMORY.md` — projekt-szintű memória-index (döntések, tanulságok, hivatkozások).
