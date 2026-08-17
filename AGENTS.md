# PicasaPy

A Google **Picasa** fotókezelő és képszerkesztő teljes újraírása Pythonban
(PySide6/Qt 6 + QML, GPL-3.0). A projekt nyilvános dokumentációja a `docs/`
alatt: formátum-specifikációk (`docs/specs/`), döntések (`docs/decisions/`),
mérések (`docs/benchmarks/`), kutatási terv és napló.

## 🔐 ELSŐ LÉPÉS — a fejlesztői kontextus külön, privát repóban van

A munkavégzésre vonatkozó szabályok (memória, munkaprotokoll, tanulságok,
skillek) **nem ebben a repóban** élnek, hanem a privát
**`sanchomuzax/picasapy-agent`** repóban. Enélkül „vakon" dolgozol.

**Kötelező, még az első fájlmódosítás előtt:**

1. Ha a klón nincs meg (a `.codex/hooks/session-start.sh` figyelmeztet rá),
   felhős sessionben:
   - `add_repo` a `sanchomuzax/picasapy-agent`-re,
   - `git clone https://github.com/sanchomuzax/picasapy-agent /workspace/picasapy-agent`,
   - `register_repo_root` ugyanerre az útvonalra — ettől a szabálykönyv
     magától betöltődik a következő körben.
   Helyi gépen a cél `~/picasapy-agent`.
2. Olvasd el az ottani `memory/00-index.md`-t és a feladathoz tartozó
   memória-lapokat (feladatvállalás előtt a `PROTOKOLL.md`-t is).

Az ottani `AGENTS.md` — ha a klón a helyén van — automatikusan betöltődik:

@/workspace/picasapy-agent/AGENTS.md
@~/picasapy-agent/AGENTS.md

## 🗣️ Nyelv: a felhasználóval MINDIG magyarul

Minden chat-válasz, kérdés és összefoglaló magyarul. A felhasználó **nem
programozó és nem ért a git/GitHub kezeléséhez** — soha ne kérd meg
git-/GitHub-műveletre, és ne tegyél fel fejlesztői eldöntendő kérdéseket:
hozz józan alapértelmezett döntést, és utólag foglald össze egy mondatban.
(Részletek a privát repó `AGENTS.md`-jében.)

## ⚠️ Párhuzamos sessionök

Ebből a mappából több Codex-session fut egyszerre. Fájlmódosítás előtt
`git status -sb` — nem tiszta main esetén tilos a fájlokhoz nyúlni;
issue-feladathoz külön `git worktree` kötelező. A foglalási kapu és a
PR-protokoll a privát repó `PROTOKOLL.md`-jében.

## Fejlesztés

- Python 3.12+, PySide6 (Qt 6) + QML, OpenCV a képfeldolgozáshoz.
- Adattárolás: `.picasa.ini` (igazságforrás, round-trip) + SQLite index.
- Teszt: `python scripts/run_tests.py` (a sima `pytest` az egész készletre
  Qt/GIL-deadlockba futhat). Lint: `ruff check src/ tests/ scripts/`.
- Környezet: a csomaglisták egyetlen helyen élnek (`pyproject.toml`,
  `packaging/qt-runtime-deps.txt`); a CI és a session-hook egyaránt a
  `scripts/print_dependencies.py`-n át telepít — tételes listát sehova ne írj.
- Közreműködés: `CONTRIBUTING.md`.
