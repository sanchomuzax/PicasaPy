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

1. Olvasd el a `memory/`-t és a `PROTOKOLL.md`-t (picasapy-agent repó) — a felhalmozott
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

## 6. NE ÁLLJ LE — az ébresztő-lánc (a legfontosabb szakasz)

⚠️ **Te nem futsz magadtól.** Csak akkor dolgozol, ha valami FELÉBRESZT: a
felhasználó üzenete, egy háttérfeladat/`Monitor` eseménye, vagy egy
ütemezett ébresztő. Ha egy kört összefoglalóval zársz, és közben nincs
semmi függőben, **megszűnsz létezni reggelig** — akkor is, ha van keret és
van jegy.

*Bizonyíték: 2026-08-18-án a műszak 02:49-kor megállt, a következő commit
08:37 volt. Nem a keret fogyott el (GO volt, heti 9%), és nem is fogytak
el a jegyek — egyszerűen nem maradt semmi, ami visszahívjon.*

### 6.1 A SZÍVVERÉS — a műszak első lépése

Még az első jegy felvétele ELŐTT hozz létre egy ismétlődő ébresztőt, ami
visszahív, akkor is, ha minden más elhal:

```
CronCreate(
  cron: "*/23 * * * *",          # ne kerek perc: a flotta ne torlódjon
  recurring: true,
  prompt: "sancho-night-work: folytatás. Ellenőrizd a keretet, a futó
           PR-eket és a ready listát, majd VEDD FEL a következő jegyet.
           Ha minden fut, haladj a jelenlegivel. Ne írj összefoglalót."
)
```

A cron **session-only** (a session végével elszáll) és 7 nap után lejár —
éjszakai műszakra bőven elég. `CronList`-tel ellenőrizd, hogy tényleg él.

### 6.2 A KÖR-VÉGI INVARIÁNS

**Minden kör végén legalább az egyiknek igaznak kell lennie:**

1. fut egy háttérfeladat vagy `Monitor`, ami értesíteni fog;
2. él a szívverés-cron;
3. tényleg megállunk (6.4 szerinti valódi stop-ok).

Ha egyik sem áll, **azonnal élesíts ébresztőt** — ne fejezd be a kört.

### 6.3 A BEFEJEZÉS NEM CÉL

Egy jegy lezárása **nem** műszak-vég. A merge/kiadás után a következő
művelet a **következő jegy felvétele**, nem az összefoglaló.

- Állapotot **röviden, menet közben** írj — ne „záró jelentést".
- A „minden lezárult, nincs beragadt futás" ellenőrzőlista a **valódi
  műszak-végé** (6.4), nem minden jegy végéé. Ha ezt körönként lefuttatod,
  a saját fejedben is lezárod a műszakot.

### 6.4 A VALÓDI stop-feltételek — ezeken KÍVÜL nincs megállás

Csak akkor állj le, ha:

- a keret **STOP**-ot vagy annak közelét mutatja;
- **nincs felvehető jegy** (ready, felelős nélkül, nem blocked) — ilyenkor
  előbb fusd végig a 6.5-öt, és csak utána állj meg;
- a felhasználó **kifejezetten** leállított;
- **reggel van** (a megbeszélt idő).

Ha megállsz: checkpoint beszédes WIP-ágra, `CronDelete` a szívverésre,
és a lezáró ellenőrzés (nincs beragadt Actions-futás) + összefoglaló.

### 6.5 HA ELFOGYNAK A JEGYEK — tartalék-sor, nem leállás

Sorrendben, amíg valamelyik ad munkát:

1. **`ready`-söprés:** a lista tételeit vesd össze a MAI kóddal — az
   elavult leletek zárhatók (egy nap alatt három ilyet találtunk).
2. **Elavult foglalások:** `in-progress` ág és PR nélkül → vissza `ready`-re.
3. **Teszt-adósság:** a legutóbbi javításokhoz hiányzó őr-tesztek.
4. **Flaky/lassú tesztek**, beragadt Actions-futások, elárvult worktree-k.
5. Csak ezután állj meg — és akkor is a 6.4 szerint.

## 7. Keret és lezárás

- Használd ki a sessiont, de **STOP-verdikt közelében** hozd a futó munkát
  konzisztens állapotba, checkpointolj beszédes WIP-branchre, és állj meg —
  ne kezdj új jegyet, ne indíts új agentet.
- **Session végén kötelező:** (a) nincs beragadt Actions-futás; (b) rövid
  összefoglaló a felhasználónak — mely jegyek zárultak, mely PR-ek mergelődtek,
  milyen új release-ek készültek, mi maradt hátra, és **mi vár a felhasználó
  kézi lépésére** (Windows/Picasa/RPi).
- **Ha a műszakban volt átnézési szakasz**, az összefoglaló tartalmazza a
  mérleg-sort is (`PROTOKOLL.md` → „Lelet-elszámolás"):
  `Leletek: L · J javítandó · E elvetve · H elhalasztva · D duplikátum · 0 besorolatlan`.
  Felügyelet nélküli műszakban ez a **legfontosabb** sor: reggel ebből derül
  ki, hogy az éjszaka talált-e valamit, vagy csak dolgozott.
- **Agentet indító műszakban** a `Brief-ellenőrzőlista: 2/2` sor is kötelező
  (forró fájl, explicit modell). A tesztfuttatót és a kiadás-tilalmat **hook**
  őrzi (`basetemp_kapu.py`, `release_kapu.py`) — azokat nem kell a briefbe
  írni, és felügyelet nélkül is fognak.
