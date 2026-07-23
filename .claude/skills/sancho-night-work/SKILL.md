---
name: sancho-night-work
description: Éjszakai autonóm fejlesztés PicasaPy-n — vegyél le `ready` jegyeket és vidd őket teljesen végig (PR, zöld ubuntu-CI után merge, verzióemelés, jegyzárás), felügyelet nélkül, agresszív párhuzamosítással. Akkor hívd, ha a felhasználó éjszakai/felügyelet nélküli munkára ad ki jegyeket („éjszakai műszak", „dolgozz éjjel", „vegyél le jegyeket és vidd végig").
---

# Éjszakai autonóm munka (sancho-night-work)

A cél: **felügyelet nélkül** annyi `ready` jegyet végigvinni a teljes
életcikluson (PR → zöld ubuntu-CI → merge → verzióemelés → jegyzárás),
amennyit a keret enged. **Éjjel a felhasználó NEM elérhető** — ne tegyél fel
kérdést, hozz józan alapértelmezést és menj tovább.

## 1. Indulás (kötelező sorrend)

1. Olvasd el a `MEMORY.md`-t és a `CONTRIBUTING.md`-t — a felhalmozott
   szabályok ott vannak, és felülírják az általános szokásaidat.
2. Keretállás: `git -C /workspace/claude-usage-status pull --quiet &&
   python3 /workspace/claude-usage-status/budget_check.py --brief`. Ha nincs
   klón: `add_repo` a `sanchomuzax/claude-usage-status`-ra + klón. UNKNOWN /
   régi cache esetén pár percenként **magadtól** próbáld újra — sose várj a
   felhasználótól számot.

## 2. Feladatválasztás (KRITÉRIUM, nem konkrét jegyszámok)

A jegyeket mindig **frissen kérd le** (`list_issues` a `ready` címkére) —
ez a skill szándékosan NEM nevesít konkrét jegyet, mert azok elavulnak.
A szűrés kritériumai:

- **Vedd fel**, ha: `ready` címke ÉS felelős (assignee) nélküli ÉS a teljes
  hátralévő munkája a fejlesztői gépen, kód+teszt szinten elvégezhető.
- **Hagyd**, ha: `blocked`, vagy `sanchomuzax`-ra van osztva, vagy a hátralévő
  lépése a felhasználó gépét/kezét igényli — golden-mérés, Picasa-export,
  RPi5-futtatás, Windows-kézi-ellenőrzés, bármilyen „a felhasználó
  csinálja meg" lépés. Ezeket éjjel nem lehet befejezni.
- **Prioritás:** a P-címke sorrendje (P0→P4) és a milestone (V1 előbb) szerint
  válassz a felvehetők közül.
- Menet közben talált új feladatra **ne ugorj rá** — nyiss rá jegyet
  (P-címke + milestone, a MEMORY triage-szabályai szerint).

## 3. Párhuzamosság (AGRESSZÍV) és modellek

- Indíts **több párhuzamos agentet**, tényleg független feladatokra, mind
  saját `git worktree`-ben. Előre látható forró-fájl-ütközést (Main.qml,
  controller.py, schema.py, i18n, Theme.qml, pyproject) **szerializálj**.
- **Az agentek némán meghalhatnak** (bevált tapasztalat): ha egy worktree-ben
  ~10 percig nincs se fájl-mtime-változás, se futó python-processz, se
  beérkezett zárójelentés → `SendMessage`-dzsel pingeld/élesztsd újra az
  agentet (kérj állapotot + utasítsd lezárásra: teszt darabolva, commit,
  push, zárójelentés).
- **Modell-politika:** gépies/sablonos rész (teszt-átkötés, commit,
  PR-nyitás, átnevezés) → olcsó modell (haiku/sonnet), vagy a fő sessionben
  agent nélkül; architektúra-kritikus rész → a legerősebb modell.
  **Fable 5-öt SOHA ne használj.** Agent-indításnál MINDIG explicit modell.

## 4. Teljes önálló életciklus jegyenként

1. **Foglalás:** a jegyen `ready` le / `in-progress` fel + branch push
   (a branch a foglalási zár).
2. **Fejlesztés:** TDD (bukó teszt előbb), magyar kommentek/docstringek,
   immutabilitás, input-validáció, fájlok 800 sor alatt.
3. **Verzióemelés (kód-merge KÖTELEZŐ eleme):** pyproject.toml +
   `src/picasapy/__init__.py` + README badge/verzió + CHANGELOG-kiemelés —
   minden előfordulási helyen, patch-szint.
4. **PR → merge:** PR-nyitás; a mérce a **zöld ubuntu-CI**; utána **magad
   mergelsz**. Merge után: jegy zárása, `in-progress` le, és
   `get_release_by_tag`-gel ellenőrizd, hogy az új release publikálódott.
5. **Docs-only / triviális** változás → azonnali merge, verzióemelés és
   teszt-ceremónia nélkül.

## 5. CI-szabályok

- A mérce az **ubuntu-láb**. A windows-láb nem blokkol, de a bukását
  **vizsgáld meg és dokumentáld** a PR-ban (flaky-e vagy valódi).
- **Ismétlődő azonos bukás → TILOS rerun.** Gyökérok-javítás kell:
  determinisztikus szinkronpont / ésszerű tolerancia / dokumentált kizárás
  külön jeggyel. Rerun legfeljebb EGYSZER, kizárólag beragadt (hang/timeout)
  futásra.
- Teszt darabolva, timeouttal: `timeout 90 python3 -m pytest tests
  --ignore=tests/app -q` egyben; a `tests/app` fájlonként `timeout 60`-nal;
  beragadásnál AZONNAL lelőni, nem várni, nem ismételgetni ugyanazt.
- Beragadt CI-futást TILOS otthagyni: session végén ellenőrizd, hogy nincs
  20+ perce `in_progress` Actions-futás; ha van, cancel.

## 6. Keret és lezárás

- Használd ki a sessiont, de **STOP-verdikt közelében** hozd a futó munkát
  konzisztens állapotba, checkpointolj beszédes WIP-branchre, és állj meg —
  ne kezdj új jegyet, ne indíts új agentet.
- **Session végén kötelező:** (a) nincs beragadt Actions-futás; (b) rövid
  összefoglaló a felhasználónak — mely jegyek zárultak, mely PR-ek mergelődtek,
  milyen új release-ek készültek, mi maradt hátra, és **mi vár a felhasználó
  kézi lépésére** (Windows/Picasa/RPi).
