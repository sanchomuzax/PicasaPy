# PicasaPy — Memória-index

Projekt-szintű memória. Egy sor per bejegyzés: rövid horog + kontextus. A részletes döntéseket és tanulságokat ide, tömören.

## Projekt

- **Cél:** a Google Picasa képszerkesztő teljes újraírása Python alapon.
- **Fázis (2026-07-15):** formátum-kutatás 1. köre kész (`docs/specs/`); hátralévő kutatás: `docs/research-plan.md`. Kód még nincs.

## Döntések

- **2026-07-15:** Teljes kétirányú `.picasa.ini` kompatibilitás (drop-in utód); round-trip elv az ismeretlen mezőkre.
- **2026-07-15:** Linux-first (RPi5 fejlesztői környezet); Win/Mac később.
- **2026-07-15:** GUI toolkitet benchmark dönti el (fő jelölt: PySide6/Qt).
- **2026-07-15:** MVP = kezelő + néző; szerkesztő 2. fázis; arcok 3. fázis.
- **2026-07-15:** PMP/db3 csak olvasás (import); saját index SQLite.

## Tanulságok

- A legnagyobb kockázat a **pixelhű szűrő-reprodukció** (enhance/finetune2 algoritmusa nem publikus) → golden-image validálás Wine-os Picasával (research-plan #2).
- A Picasa UX lelke: sorozat-vágás Enter-rel, I'm Feeling Lucky, észrevétlen eredeti-megőrzés (`.picasaoriginals/`).
- Csak a db-ben élő adatok (képsorrend, ignorált arcok) az importnál kritikusak — ini-ből nem pótolhatók.

## Hivatkozások

- NotebookLM: „Picasa metaadatok és adatbázisok dekódolási útmutatója" — ID `f70b0a1c-1ef2-4f72-98ae-2bb7e946ba1e` (30 forrás), https://notebooklm.google.com/notebook/f70b0a1c-1ef2-4f72-98ae-2bb7e946ba1e
- Referencia-repók: skisoo/PicasaDBReader (Java), vosbergw/picasa3meta + metaSave (Python), Philipp91/picasa2digikam (Python), bufemc/picasa2xmp (Python).
- Privát repó: https://github.com/sanchomuzax/PicasaPy
