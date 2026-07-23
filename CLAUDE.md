# PicasaPy

## 👤 A FELHASZNÁLÓ — NEM fejlesztő, GitHubhoz NEM ért

A felhasználó **nem programozó** és **nem ért a GitHub/git kezeléséhez**.
Ezért:

- **SOHA ne kérd meg** git- vagy GitHub-művelet elvégzésére (branch, commit,
  push, merge, PR-nyitás/elfogadás, konfliktusfeloldás, settings — semmi).
  Ezeket **mindig te végzed el helyette**, önállóan, kérdés nélkül.
- **NE tegyél fel fejlesztői/technikai eldöntendő kérdéseket** (hook szinkron
  vagy aszinkron? melyik branch? nyissak PR-t?). Hozz **józan alapértelmezett
  döntést**, csináld meg, és **utólag egy mondatban** foglald össze, mit tettél.
- Kérdést csak akkor tegyél fel, ha a **termék viselkedéséről** van szó, amit
  csak a felhasználó tud eldönteni (pl. „melyik sarokban legyen a gomb?") — és
  azt is emberi nyelven, nem fejlesztői zsargonban.
- A teljes fejlesztői folyamat (kód, teszt, commit, push, és ha kell, PR) **a
  te dolgod**; a felhasználónak csak a kész eredményt és a döntéseit kell látnia.
- **Kérdezni és csevegni bármikor lehet PR nélkül.** Ha a felhasználó csak
  kérdez, ötletel, vagy beszélget (nincs konkrét fejlesztési feladat), akkor
  **CSAK válaszolj** — ne nyiss PR-t, ne committolj, ne pushölj, ne indíts
  branchet. A git/GitHub-folyamatot **kizárólag valódi kód-feladatnál** indítsd
  el; PR-t pedig továbbra is **csak akkor**, ha a felhasználó kifejezetten kéri.
  A beszélgetés önmagában soha nem kiváltó ok.

## 🗣️ NYELV — A felhasználóval MINDIG magyarul

Minden chat-válasz, kérdés és összefoglaló **magyarul** íródik a felhasználó
felé. (A kód, commit-üzenetek és PR-leírások a projekt eddigi konvencióját
követik.) Ez nem opcionális — a felhasználó anyanyelve a magyar.

## ⚠️ PÁRHUZAMOS SESSIONÖK — ELSŐ SZABÁLY, MINDEN MÁS ELŐTT

Ebből a mappából a felhasználó **több párhuzamos Claude-sessiont** indít.
Mielőtt BÁRMILYEN fájlt módosítanál:

1. `git status -sb` — ha a checkout nem tiszta main (másik session branché,
   commitolatlan módosítások), **TILOS a fájlokhoz nyúlni**.
2. Issue-feladathoz **kötelező a saját worktree**:
   `git worktree add ../PicasaPy-wt-<issueszám> -b fix/<szám>-nev origin/main`
   — és onnantól minden munka (szerkesztés, pytest, commit) OTT folyik.
3. A fő checkout az integrátor sessioné. Feladat-foglalás, forró fájlok,
   PR-protokoll: **CONTRIBUTING.md** (kötelező elolvasni feladatvállalás
   előtt). Feladatlista: GitHub Issues (`gh issue list --label ready`).
4. **FOGLALÁSI KAPU — kötelező sorrend, az ELSŐ kódmódosítás/commit ELŐTT**
   (ez blokkoló: amíg meg nem történt, TILOS a kódhoz nyúlni):
   a) olvasd el a **CONTRIBUTING.md**-t;
   b) a jegyen a címke `ready` **le**, `in-progress` **fel**;
   c) branch + push (ez a foglalási zár).
   **Lezáráskor** az `in-progress` címkét **le kell venni**. Ez nem
   „mutató a CONTRIBUTING felé", hanem kifejezett, kihagyhatatlan lépéssor —
   ha kimarad, a foglalás érvénytelen, és utólag azonnal pótolni kell.

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
3. **GUI toolkit: PySide6 (Qt 6) + QML** (2026-07-16, benchmark alapján) —
   ld. `docs/decisions/gui-toolkit.md`.
4. **MVP = kezelő + néző** (1. fázis); szerkesztő a 2., arcok a 3. fázis —
   ld. `docs/specs/feature-map.md`.
5. PMP/db3 adatbázist **csak olvassuk** (import); saját index: SQLite.
6. **Licenc: GPL-3.0** (2026-07-16) — szabad megosztás; a GPL-es
   referencia-repókból portolható kód attribúcióval.
7. **Ismételhető migráció** (2026-07-16) — a felhasználó a fejlesztés alatt
   tovább használja a Windows-os Picasát; a PicasaPy importja ezért
   **bármikor újrafuttatható** kell legyen: a `.picasa.ini`-k (a fotómappák
   mellett, NAS-on) folyamatosan frissek, a db3-only adatok (képsorrend,
   ignorált arcok) friss db3-másolatból újraimportálhatók, path-remappel.

## Tech stack

- Nyelv: Python 3.12+
- GUI: **PySide6 (Qt 6) + QML** (ADR-001)
- Képfeldolgozás (scanner/thumbnail): **OpenCV** (benchmark:
  `docs/benchmarks/rpi5-image-libs.md`); viewer-dekód: Qt/QML natív
- Adattárolás: `.picasa.ini` (igazságforrás) + SQLite index + XMP export

## Dokumentumtérkép

- `docs/specs/picasa-ini-format.md` — ini szerkezet, filters mátrix, rect64
- `docs/specs/pmp-database.md` — db3/PMP/thumbindex, contacts.xml, import
- `docs/specs/feature-map.md` — funkciók fázisokra bontva
- `docs/specs/ux-principles.md` — a Picasa UX-alapelvei (minden UI-döntés mércéje)
- `docs/research-plan.md` — nyitott kutatási kérdések
- `docs/research-story.md` — hogyan készült a kutatás (módszertan + NotebookLM-infografika)

## Fejlesztési elvek

A globális `~/.claude/rules/` szabályok érvényesek, kiemelten:

- **Immutability:** ne mutálj, hozz létre új objektumokat.
- **Sok kicsi fájl > kevés nagy fájl** (200–400 sor tipikus, 800 max).
- **TDD:** teszt előbb (RED → GREEN → REFACTOR), 80%+ lefedettség.
- **Input-validáció és átfogó hibakezelés** mindenhol.
- **Nincs hardkódolt titok, nincs `console.log`/nyomkövetés a kész kódban.**

## 💳 Kredit-/keretállás — LEKÉRDEZHETŐ (ne dolgozz vakon!)

A Claude-előfizetés terhelése **megnézhető** — ne találgass, és ne hidd, hogy
nincs rá mód. Mielőtt nagy (pl. párhuzamos subagentes) munkába kezdesz:

```sh
git -C /workspace/claude-usage-status pull --quiet && \
python3 /workspace/claude-usage-status/budget_check.py --brief
```

Ha a klón nincs meg: `add_repo` a `sanchomuzax/claude-usage-status`-ra, majd
klónozd `/workspace/claude-usage-status`-ba. A kimenet forrást is jelez
(`live` / `CACHED Nm old`) és verdiktet ad: **GO / CAUTION / STOP / UNKNOWN**.
Mindig **előbb `git pull`, utána a check**. Verdikt-szabályok, a
`[conserve]`/`[greedy]` politika és a „mikor nézd" a repó
`ORCHESTRATOR_PROMPT.md`-jében — ez a kanonikus szabálykönyv.

## 🧠 Tartós tudás — SESSION ELEJÉN OLVASD EL a MEMORY.md-t

- **`CLAUDE.md`** (ez a fájl) minden session kontextusába **automatikusan**
  betöltődik — ide csak az kerül, amit MINDEN sessionnek kérés nélkül tudnia kell.
- **`MEMORY.md`** **NEM töltődik be magától** — ezért **session elején OLVASD EL**
  (döntések, munkafolyamat-szabályok, tanulságok). Enélkül a felhalmozott
  szabályokat (modellköltség, verzióemelés, milestone-ok, teszt-ceremónia,
  hisztogram-típusú tanulságok…) nem ismered, és „vakon" dolgozol — pont ez
  okozta már, hogy párhuzamos session-ök újra elkövettek régen megoldott hibákat.
- **Új tartós tudás elhelyezése:** a *mindig-kell, kérés nélkül* → CLAUDE.md; a
  *részletek/tanulságok* → MEMORY.md (a duplikációt kerüld).

## Fájlok

- `CLAUDE.md` — ez a fájl: projekt-kontextus és irányelvek.
- `MEMORY.md` — projekt-szintű memória-index (döntések, tanulságok, hivatkozások).
