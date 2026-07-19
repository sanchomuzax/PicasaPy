# Közreműködés — ember és agent egyaránt

Ez a szabálykönyv a párhuzamos (több session / több agent) fejlesztéshez
készült. Betartása kötelező — a cél, hogy a **main mindig zöld** legyen,
és két munkafolyam soha ne írja ugyanazt a fájlt.

## A feladat-tábla: GitHub Issues

- Minden feladat egy **issue**. Címkék: `ready` (felvehető),
  `in-progress` (foglalt), `blocked` (függőségre vár),
  `integration` (csak az integrátor session).
- **Foglalás** (ebben a sorrendben, a session legelején):
  1. `gh issue list --label ready` — mi szabad?
  2. `gh issue edit <N> --add-label in-progress --remove-label ready`
  3. Branch azonnal: `git switch -c feat/<N>-rovid-nev` és push `-u` —
     **a branch létezése a zár**; aki fetch után látja, tudja, hogy foglalt.
- **Elárvult foglalás**: ha egy `in-progress` issue branchén 3 napja nincs
  commit, kommenttel visszaállítható `ready`-re.
- Új, menet közben talált feladatot NE kezdj el — nyiss rá issue-t.

## Munkakörnyezet

- Több session ugyanazon a gépen: **kötelező a külön `git worktree`**
  branchenként — közös munkakönyvtáron tilos osztozni.
- Fejlesztési elvek: **TDD** (bukó teszt előbb), magyar kommentek/
  docstringek, immutabilitás, fájlok 800 sor alatt. QML-viselkedéshez
  funkcionális teszt kötelező (`tests/app/test_qml_functional.py` minta).
- Push előtt: `python3 -m pytest -q` — TELJES zöld, különben nincs push.

## Forró fájlok — csak az integrátor session módosíthatja

Ezekben születik minden merge-konfliktus, ezért feature-branchen **tilos**
hozzájuk nyúlni; az integrációs igényt az issue-ban kell leírni:

- `src/picasapy/app/controller.py` és `src/picasapy/app/qml/Main.qml`
  (bekötési pontok — az integrátor köti be a kész modult)
- `src/picasapy/index/schema.py` — **sémaverziót csak az integrátor
  oszt ki**; migráció-sorrend nem sérülhet
- `src/picasapy/app/i18n/*` — a lupdate az egész fájlt átírja; a
  fordítás-regen kizárólag az integrációs lépésben fut
- `src/picasapy/app/qml/PicasaPy/Theme.qml` és
  `docs/specs/design-guide.md` — dizájn-tokenek egy kézben

Új forrásszövegeket (qsTr) a feature-branch szabadon bevezethet — a
fordításukat az integrátor generálja le.

## Integráció

- A **main védett**: oda csak PR-en át, zöld CI-val kerülhet kód.
  A Windows CI-láb kísérleti (nem blokkol); a mérce az ubuntu-láb.
- A PR-t az integrátor session mergeli: ő oldja a konfliktusokat,
  futtatja az i18n-regent és a teljes tesztkészletet.
- **Release-kötelezettség (integrátor):** érdemi merge-ök után verzió-bump
  (minden előfordulási helyen). A tag + GitHub Release ezután **automatikus**
  (`.github/workflows/release.yml`): minden main-push után lefut, és ha a
  `pyproject.toml` verziójához még nincs kiadás, létrehozza — a Releases
  hasáb így soha nem maradhat le a main mögött, kézi lépés nélkül.
- Commit-formátum: `feat|fix|docs|test|chore: leírás` (magyarul),
  hivatkozás az issue-ra (`#N`).

## Dizájn és kompatibilitás

- Dizájn-igazságforrás: `docs/specs/design-guide.md` (kézikönyv-réteg >
  screenshot-réteg). Az app **mindig világos** — a sötét téma V3-feature.
- `.picasa.ini`-írás kizárólag a meglévő round-trip rétegen át
  (`picasapy.ini`), atomikus mentéssel és backuppal. Ami nem értelmezett,
  bitre pontosan megőrzendő.
