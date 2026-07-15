# PicasaPy

## Projekt célja

A Google **Picasa** képszerkesztő és fotókezelő szoftver teljes újraírása **Python** alapon. A Picasa-t a Google 2016-ban kivezette; a cél egy modern, nyílt, keresztplatformos utód létrehozása, amely megőrzi az eredeti szoftver erősségeit (gyors fotókezelés, nem-destruktív szerkesztés, arcfelismerés, albumkezelés).

## Jelenlegi fázis: KUTATÁS (research)

A fejlesztés még **nem** kezdődött el. Az első lépés a kutatás:

- Az eredeti Picasa funkcionalitásának feltérképezése (fő funkciók, UI, adatmodell — pl. `.picasa.ini`, `pmp`/db3 adatbázis-formátumok).
- Python GUI toolkit kiválasztása (pl. PyQt/PySide, Qt, egyéb).
- Kép-, EXIF- és RAW-feldolgozó könyvtárak felmérése (Pillow, rawpy, OpenCV stb.).
- Arcfelismerés / képfelismerés lehetőségeinek vizsgálata.
- Architektúra és MVP-scope meghatározása.

> **FONTOS:** Kutatást csak akkor kezdj, ha a felhasználó erre kifejezetten megkéri. Jelenleg csak az alapdokumentáció rögzítése a feladat.

## Tech stack

*Még nincs eldöntve — a kutatási fázis eredménye dönti el.*

- Nyelv: Python (verzió TBD, cél: 3.12+)
- GUI: TBD
- Képfeldolgozás: TBD
- Adattárolás: TBD

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
