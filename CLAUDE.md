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

1. Ha a klón nincs meg, csatold és klónozd:
   `add_repo sanchomuzax/picasapy-agent`, majd
   `git clone <url> /workspace/picasapy-agent` (felhős session) vagy
   `~/picasapy-agent` (helyi gép). Felhős sessionben ezt a
   `.claude/hooks/session-start.sh` általában már elvégezte.
2. Olvasd el az ottani `CLAUDE.md`-t és `memory/00-index.md`-t
   (feladatvállalás előtt a `PROTOKOLL.md`-t is).

Az ottani `CLAUDE.md` — ha a klón a helyén van — automatikusan betöltődik:

@/workspace/picasapy-agent/CLAUDE.md
@~/picasapy-agent/CLAUDE.md

## 🗣️ Nyelv: a felhasználóval MINDIG magyarul

Minden chat-válasz, kérdés és összefoglaló magyarul. A felhasználó **nem
programozó és nem ért a git/GitHub kezeléséhez** — soha ne kérd meg
git-/GitHub-műveletre, és ne tegyél fel fejlesztői eldöntendő kérdéseket:
hozz józan alapértelmezett döntést, és utólag foglald össze egy mondatban.
(Részletek a privát repó `CLAUDE.md`-jében.)

## ⚠️ Párhuzamos sessionök

Ebből a mappából több Claude-session fut egyszerre. Fájlmódosítás előtt
`git status -sb` — nem tiszta main esetén tilos a fájlokhoz nyúlni;
issue-feladathoz külön `git worktree` kötelező. A foglalási kapu és a
PR-protokoll a privát repó `PROTOKOLL.md`-jében.

## Fejlesztés

- Python 3.12+, PySide6 (Qt 6) + QML, OpenCV a képfeldolgozáshoz.
- Adattárolás: `.picasa.ini` (igazságforrás, round-trip) + SQLite index.
- Teszt: `python scripts/run_tests.py` (a sima `pytest` az egész készletre
  Qt/GIL-deadlockba futhat). Lint: `ruff check src/ tests/`.
- Közreműködés: `CONTRIBUTING.md`.
