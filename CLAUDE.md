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

1. Ha a klón nincs meg (a `.claude/hooks/session-start.sh` figyelmeztet rá),
   felhős sessionben:
   - `add_repo` a `sanchomuzax/picasapy-agent`-re,
   - `git clone https://github.com/sanchomuzax/picasapy-agent /workspace/picasapy-agent`,
   - `register_repo_root` ugyanerre az útvonalra — ettől a szabálykönyv
     magától betöltődik a következő körben.
   Helyi gépen a cél `~/picasapy-agent`.
2. Olvasd el az ottani `memory/00-index.md`-t és a feladathoz tartozó
   memória-lapokat (feladatvállalás előtt a `PROTOKOLL.md`-t is).

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

## 🗺️ Sávtérkép — párhuzamos munka és szerződések

Az alábbi sávok egymástól **függetlenül művelhetők** (mért importgráf,
2026-08-18); két párhuzamos jegy különböző sávban biztonságos, egy sávon belül
is az, ha nem ugyanazt a fájlt érintik.

| Sáv | Csomagok | Jelleg |
|---|---|---|
| render/effekt | `render/`, `color/` | 40+ effektfájl, egymástól függetlenek |
| adatréteg | `ini/`, `index/`, `metadata/`, `scanner/` | igazságforrás + index |
| ki/bemenet | `export/`, `webexport/`, `thumbs/`, `collage/`, `movie/`, `dedup/`, `fileops/`, `importsource/`, `pmpimport/`, `printing/`, `mailer/` | csővégek, egymást alig érintik |
| UI (**forró zóna**) | `app/` (68 py + 102 QML) | mindenre támaszkodik; itt ütköznek a jegyek |

**Keresztmetsző szerződések** — ha egy jegy ezek egyikét változtatja, az több
sávot érint, tehát NEM párhuzamosítható szabadon:

1. `.picasa.ini` formátum (round-trip; spec: `docs/specs/`) — `ini/` írja, 8 csomag olvassa.
2. SQLite indexséma (`index/`) — az `app/` és a `webexport/` épít rá.
3. Render-lánc regisztráció (`render/registry*.py`, `chain*.py`) — minden effekt ezen át kapcsolódik.
4. QML↔Python controller-határ (`app/*_controller.py` ↔ `app/qml/`) — a kötések mindkét oldalt egyszerre érintik.
5. `version.py` + CHANGELOG — kiadáskor, **csak az integrátor** nyúl hozzá.

**Mért forró fájlok** (6 hét, változásszám): `app/qml/Main.qml` (93),
`app/i18n/picasapy_hu.ts` (102, minden UI-szövegváltozás átfésüli),
`app/controller.py` (51), `qml/PicasaPy/qmldir` (55), `PhotoViewer.qml` (53),
`EditorPanel.qml` (46), `application.py` (41). Két jegy, amely ezek
bármelyikét érinti, **szerializálandó** (egy session vigye mindkettőt, vagy a
második a frissen mergelt main-re épüljön). Éjszakai jegyválasztásnál
lehetőleg különböző sávokból végy jegyeket.

## Fejlesztés

- Python 3.12+, PySide6 (Qt 6) + QML, OpenCV a képfeldolgozáshoz.
- Adattárolás: `.picasa.ini` (igazságforrás, round-trip) + SQLite index.
- Teszt: `python scripts/run_tests.py` (a sima `pytest` az egész készletre
  Qt/GIL-deadlockba futhat). Lint: `ruff check src/ tests/ scripts/`.
- Környezet: a csomaglisták egyetlen helyen élnek (`pyproject.toml`,
  `packaging/qt-runtime-deps.txt`); a CI és a session-hook egyaránt a
  `scripts/print_dependencies.py`-n át telepít — tételes listát sehova ne írj.
- Közreműködés: `CONTRIBUTING.md`.
