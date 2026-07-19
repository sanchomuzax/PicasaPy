# PicasaPy — Memória-index

Projekt-szintű memória. Egy sor per bejegyzés: rövid horog + kontextus. A részletes döntéseket és tanulságokat ide, tömören.

## Projekt

- **Cél:** a Google Picasa képszerkesztő teljes újraírása Python alapon.
- **Fázis (2026-07-15):** formátum-kutatás 1. köre kész (`docs/specs/`); hátralévő kutatás: `docs/research-plan.md`. Kód még nincs.

## Döntések

- **2026-07-16: GUI = PySide6 (Qt 6) + QML** (ADR-001) — benchmark: DPG kiesett, QML≈GTK4 érzésre; a keresztplatform + GPU-pipeline döntött. Scanner-képfeldolgozás: OpenCV.

- **2026-07-16: Licenc = GPL-3.0** (LICENSE a gyökérben) — a cél a szabad megosztás; a 4 GPL-es referencia-repóból portolható kód attribúcióval.

- **2026-07-15:** Teljes kétirányú `.picasa.ini` kompatibilitás (drop-in utód); round-trip elv az ismeretlen mezőkre.
- **2026-07-15:** Linux-first (RPi5 fejlesztői környezet); Win/Mac később.
- **2026-07-15:** GUI toolkitet benchmark dönti el (fő jelölt: PySide6/Qt).
- **2026-07-15:** MVP = kezelő + néző; szerkesztő 2. fázis; arcok 3. fázis.
- **2026-07-15:** PMP/db3 csak olvasás (import); saját index SQLite.

## Munkafolyamat

- **2026-07-19: Beragadt CI-futást TILOS otthagyni (felhasználói utasítás).**
  A teszt-timeout szabály a GitHub Actionsre IS vonatkozik: a felhasználó nem
  látja és nem tudja leállítani a runnereken lógó futásokat. Minden session,
  amely pusholt/PR-t nyitott, a munkája végén KÖTELES ellenőrizni, hogy a
  CI-futásai lezárultak-e; a 20+ perce `in_progress` futást azonnal
  cancel-elni kell. (2026-07-19-en 19 otthagyott futás órákra megbénította
  a teljes Actions-sort és a release-automatikát.)

- **2026-07-19: Teszt-timeout KÖTELEZŐ, várakozás TILOS (felhasználói utasítás).**
  Az egészséges teljes tesztkészlet ~15–20 mp. MINDEN pytest-hívást szigorú
  `timeout`-tal kell futtatni (teljes készlet: max 60–90 mp), és az első
  beragadásnál AZONNAL le kell lőni + a flaky fájlt (`tests/app/
  test_qml_functional.py`, #53) kizárva újrafuttatni — soha nem szabad
  percekig várni egy beragadt futásra, és nem szabad többször újrapróbálni
  ugyanazt a beragadó futást.
- **2026-07-19: Kész munka AZONNAL a main-be (felhasználói utasítás).** Ha a
  feladat kész és a tesztek zöldek, a session maga nyissa meg ÉS mergelje a
  PR-t a main-be, külön kérés nélkül — a felhasználónak soha ne kelljen
  git/GitHub-műveletet kérnie vagy végeznie.

- **2026-07-19: Merge után a Releases hasábot ELLENŐRIZNI KELL (felhasználói
  utasítás).** A kiadás-automatika (release.yml) csak akkor fut le, ha az
  Actions-sor nem áll. Ha a legfrissebb release lemarad a pyproject
  verziójától: szinte biztos, hogy beragadt (#53-as deadlock-osztályú)
  `in_progress` CI-futások foglalják órák óta az összes runnert — ezeket
  cancel-elni kell (Actions → in_progress futások lelövése), utána a sorban
  álló release-futás magától pótolja a kiadást. Megelőzés: a ci.yml
  `timeout-minutes` korlátja. A merge-t végző session felelőssége, hogy a
  Releases hasáb ténylegesen beérje a main-t — nem elég az automatikára bízni.

- **2026-07-19: MINDEN kód-PR merge-e verzióemeléssel jár (felhasználói
  utasítás, nyomatékkal).** A release csak a pyproject.toml verzióemelésekor
  készül el — kód-változást tartalmazó PR-be ezért KÖTELEZŐ beletenni a
  patch-verzió emelését (vagy közvetlenül a merge után külön pótolni), majd
  szükség esetén a release.yml-t kézzel (workflow_dispatch) elindítani és
  `get_release_by_tag`-gel MEGGYŐZŐDNI róla, hogy az új vX.Y.Z release
  ténylegesen publikálódott. A felhasználó a Releases hasábból követi a
  fejlődést; verzióemelés nélküli merge számára láthatatlan, és joggal
  háborítja fel.

- **2026-07-18: Prioritási címkék kötelezők (P0–P4).** Minden jegy a típus/komponens/eszköz
  címkéi MELLÉ kapjon egy prioritási címkét. **Automatikusan alkalmazandó** — új jegy
  triage-elésekor vagy meglévő jegy áttekintésekor külön kérés nélkül is fel kell tenni
  a megfelelő P-címkét. A skála a **súlyosság + kerülőút megléte** mentén dönt (minél nagyobb
  a kár és minél kevésbé van workaround, annál előrébb):
  - **P0** Critical — adatvesztés, biztonsági hiba, crash loop.
  - **P1** High — fontos funkció törött, nincs kerülőút.
  - **P2** Medium — romlott működés, de van workaround.
  - **P3** Low — kozmetikai / nice-to-have.
  - **P4** Best-effort — ha egyszer sorra kerül.

## Tanulságok

- **2026-07-19 (#103 tesztelése):** videó-sort tartalmazó QML-teszt (rács
  vagy néző) **in-process TILOS** — a thumbnail-/média-szálak a következő
  engine-t GIL-deadlockba rántják (#53-as hibaosztály), a beragadás a
  RÁKÖVETKEZŐ tesztfájlban jelentkezik. Videós QML-ellenőrzés kizárólag a
  `tests/app/qml_video_probe.py` alprocesszes próbájába kerülhet
  (`os._exit`-tel zár, a leépítést az OS takarítja).

- **2026-07-16 (golden 3. kör):** autolight = globális min–max stretch (közös csatorna-transzform); enhance = fixLUT∘stretch∘autocolor (reziduál görbe mentve: `research/golden-analysis/enhance_residual.json`); fill = 2D LUT (±1,25/255). A te könyvtárad két leggyakoribb szerkesztése (enhance 7528×, autolight 4707×) ezzel reprodukálható.
- **2026-07-16 (golden 1. kör):** a crop rendereléséhez a külön `crop=rect64()` kulcs kell (a filters-beli crop64 csak történet!); bw=Rec.601; finetune2 paraméterei: fill/highlights/shadows/semleges-szín/színhő. Részletek: `docs/specs/filters-decoded.md`. A golden-módszer működik — a chartos kit + Picasa-export kombó egzakt LUT-okat ad.

- **2026-07-16 (teljes testdata):** a `contacts.xml` nem mindig létezik (a valós telepítésünkben sincs) → az importban opcionális; arcnevek a `deferredregion`-ből. A `watchedfolders.txt`/`frexcludefolders.txt` élesben kisbetűs → kis-nagybetű-független fájlkeresés.
- **2026-07-16 (db3 validálás):** a PMP/thumbindex spec valódi 2 GB-os adatbázison (140k kép) hibátlanul igazolt. Kulcs-újdonságok: arcadatok a `deferredregion` oszlopban (`rect64(hex),Név;` tisztanevekkel), új szűrők élesben (`fill`, `finetune` v1, `unsharp` v1, nagybetűs `Vignette`), előjeles floatok a tilt/finetune2-ben, sparse oszlopok + leghosszabb oszlop = thumbindex-hossz. Tesztadat: `research/testdata/db3` (gitignore-olt, személyes!).

- **2026-07-15 (repó-audit):** picasa3meta Python 2-only → nem kód-alap, csak formátum-doksi; PMP-fejléc keresztvalidálva (pmpinfo.py ↔ PMPDB.java); rect64 rövidülhet → `zfill(16)` kötelező + EXIF-orientáció kezelendő; thumbindex üres nevű bejegyzés = arc-rekord. Részletek: `docs/reference-repos-audit.md`.
- **Licenc-csapda:** a referencia-repók közül csak a PicasaDBReader MIT, a többi GPL-3.0 → PicasaPy licenc-döntés blokkoló a kódátvételhez (research-plan #7).

- A legnagyobb kockázat a **pixelhű szűrő-reprodukció** (enhance/finetune2 algoritmusa nem publikus) → golden-image validálás Wine-os Picasával (research-plan #2).
- A Picasa UX lelke: sorozat-vágás Enter-rel, I'm Feeling Lucky, észrevétlen eredeti-megőrzés (`.picasaoriginals/`).
- Csak a db-ben élő adatok (képsorrend, ignorált arcok) az importnál kritikusak — ini-ből nem pótolhatók.

## Hivatkozások

- NotebookLM: „Picasa metaadatok és adatbázisok dekódolási útmutatója" — ID `f70b0a1c-1ef2-4f72-98ae-2bb7e946ba1e` (30 forrás), https://notebooklm.google.com/notebook/f70b0a1c-1ef2-4f72-98ae-2bb7e946ba1e
- Referencia-repók: skisoo/PicasaDBReader (Java), vosbergw/picasa3meta + metaSave (Python), Philipp91/picasa2digikam (Python), bufemc/picasa2xmp (Python).
- Repó (publikus): https://github.com/sanchomuzax/PicasaPy
