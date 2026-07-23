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

- **2026-07-23: Ismétlődően bukó CI-teszt → ÚJRAFUTTATNI TILOS, stratégiát
  kell váltani (felhasználói utasítás, nyomatékkal).** Ha ugyanaz a
  teszt/fájl másodszor is ugyanúgy bukik (tipikusan a windows-lábon), a
  rerun pazarlás és zaj — helyette AZONNAL kódszintű beavatkozás kell:
  a teszt determinisztikussá tétele (szinkronpont: érték-stabilizálódás
  kivárása; ésszerű tolerancia), a gyökérok javítása, vagy dokumentált
  kizárás (`scripts/run_tests.py` Windows-kivétel, a #155 mintájára) —
  mindig külön jeggyel követve. Rerun legfeljebb EGYSZER indokolt, és
  kizárólag BERAGADT (hang/timeout) futásra — érték-eltéréses bukásra
  SOHA. (Példa: a TestArrowMinimalScroll windows-flaky → #261, a javítás
  a szinkronpont, nem az újrafuttatás.)

- **2026-07-23: Keretállás-lekérdezés — a session ÖNÁLLÓAN tartsa frissen,
  a felhasználót SOHA nem kell emlékeztetnie rá (felhasználói utasítás).**
  A rutin (a CLAUDE.md 💳 szekciója szerint): friss felhő-konténerben előbb
  `add_repo` a `sanchomuzax/claude-usage-status`-ra és klón a
  `/workspace/claude-usage-status`-ba, utána MINDIG
  `git -C /workspace/claude-usage-status pull --quiet && python3
  /workspace/claude-usage-status/budget_check.py --brief`.
  **Ha a verdikt UNKNOWN / a cache régi:** ez tipikusan csak annyit jelent,
  hogy a forrásgép még nem töltött fel friss pillanatképet (5 percenként
  frissül) — NE tekintsd tartós vakságnak és NE a felhasználótól várd a
  számot: dolgozz ideiglenesen CAUTION-szabályok szerint, és pár perc múlva,
  illetve minden fázisváltásnál ISMÉTELD a `git pull` + check párost, amíg
  friss adat nem jön. A felhasználót csak tartós (több próbálkozás utáni)
  vakság esetén kell megkérdezni a `/usage`-ről.

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
  ugyanazt a beragadó futást. KIEGÉSZÍTÉS (2026-07-19, felhasználói
  visszajelzés után): a felhő-konténerben a teljes készlet EGY processzben
  futtatva megbízhatóan beragad (Qt/GIL, #53-as osztály) — ott ALAPBÓL
  bontva kell futtatni: `tests --ignore=tests/app` egyben (~7 mp), a
  `tests/app` fájlonként `timeout 60`-nal. Ismerten halott tesztet
  (hiányzó rendszerfüggőség) TILOS újra és újra elindítani — helyette
  skip-elhetővé kell tenni (ld. `test_qml_video`:
  `importorskip(..., exc_type=ImportError)` a libpulse-hiányra).
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

- **2026-07-20: Modellköltség — alfolyamat SOSEM örökli némán a drága modellt
  (felhasználói utasítás, nyomatékkal).** Az agent alapból a session modelljét
  örökli; ha a session drágán (pl. a legerősebb modellen) fut, a spawnolt
  agentek — a tisztán gépies munka is (teszt-átkötés, commit, PR-nyitás, CI-
  figyelés) — szintén azon futnak, és pillanatok alatt elviszik a keretet.
  KÖTELEZŐ: agent-indításnál MINDIG explicit modellt megadni. **Gépies/sablonos
  részfeladat → olcsó modell** (haiku/sonnet), vagy egyszerűen a fő session-ben,
  agent nélkül elintézni; **csak az architektúra-kritikus rész → a legerősebb
  modell.** Ezt a felhasználónak NEM kell minden kérésnél megismételnie — ez az
  alapértelmezett. Vezérlő szavak a kérésben: „spórolj"/„sorban" = soros, olcsó;
  „gyorsan"/„párhuzamosan" = több agent (drágább). Alapból a takarékos-soros út.

- **2026-07-20: Költségtudatos orchestráció (felhasználói tanulság).** Sok apró,
  vagy egymással ütköző fájlt érintő fix esetén a párhuzamos worktree+agent
  overhead (5 worktree + 5 agent + integráció) drágább és kockázatosabb, mint a
  soros, egy-session-ös végigvitel. Párhuzamosítás CSAK nagy, tényleg független
  feladatokra. Előre látható forró-fájl-ütközést (pl. két jegy ugyanazt a fájlt)
  szerializálni kell: egy agent csinálja mindkettőt, vagy a második a friss
  main-re épül. A fő session az EGYETLEN CI-watchdog (az agentek PR után térjenek
  vissza, ne pörgessenek külön CI-hurkot). Az agent-önjelentésnek („kész, zöld")
  nem hiszünk: a fő session maga futtatja a teljes tesztet + nézi a CI-t, és csak
  zöld után mergel.

- **2026-07-20: Triviális változás → SEMMI teszt-ceremónia (felhasználói
  utasítás, nyomatékkal).** Kockázatmentes, a program futására nem ható
  változásnál — ékezet-/elgépelés-javítás, `MEMORY.md`/`docs/` vagy más szöveg
  módosítása, 1-2 pixeles UI-igazítás, komment/megjegyzés — TILOS: lokális
  pytest futtatása, a GitHub-CI-re várakozás, ütemezett wakeup vagy CI-figyelő
  hurok. A PR-t AZONNAL be kell olvasztani. (A GitHub-CI a repó `ci.yml` `on:`
  szabálya miatt magától elindul minden PR-en — ezt nem a session „futtatja",
  és a merge nem függ tőle: futó CI mellett is mergelhető.) Teljes tesztet és
  CI-verifikációt CSAK tényleges kód-/viselkedés-változásnál (futásra ható
  forrás) végzünk. Ha valaha zavaró, hogy a docs-only PR egyáltalán CI-t húz,
  az a `ci.yml`-be tett `paths-ignore: ['**.md', 'docs/**']` — de az CI-infra-
  módosítás, külön jegy/kérés kell hozzá.

- **2026-07-23: Assignee-konvenció — a jegy felelőse (assignee) = a FELHASZNÁLÓ
  lépésére vár.** Claude-nak nincs saját GitHub-fiókja (minden művelet a
  felhasználó fiókján át megy), ezért Claude nem lehet assignee. A jelölés:
  ha a jegy hátralévő lépése csak a felhasználó gépén/kezével végezhető el
  (Windows-ellenőrzés, golden-kit futtatás stb.), az assignee `sanchomuzax`;
  a felelős nélküli jegy Claude-ra vár (állapotát a `ready`/`in-progress`/
  `blocked` címkék viszik). Triage-nél ezt is karban kell tartani: ha a
  felhasználói lépés megtörtént és újra Claude-on a sor, az assignee-t le
  kell venni — és fordítva.

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

- **2026-07-21: Milestone-ok = fázisok, minden jegy kap egyet (mint a P-címke).**
  A repóban HÁROM GitHub-milestone él (mi hoztuk létre a kezdeti triage-nél),
  a `.picasa.ini`-fázismodell (CLAUDE.md 4. döntés) leképzése:
  - **milestone 1 = „V1 — Teljes kezelő + néző"** (MVP 1. fázis): böngészés,
    import, mappakezelő, keresés, címkék/gyorscímkék, albumok-nézet,
    diavetítés, fájlműveletek, néző, splash/indulás, teljesítmény-skálázódás,
    adatintegritás, csomagolás, valamint a magréteg/CI/infra-stabilitás.
  - **milestone 2 = „V2 — Szerkesztő"**: nem-destruktív szerkesztő, `filters=`
    renderelés, Gyakori javítások/Finomhangolás/Effektek, effekt-dekódolás,
    hisztogram (UI + skála-QA), retusálás/szöveg, mentés `.picasaoriginals`-szal,
    golden-harness, GPU-render.
  - **milestone 3 = „V3 — Arcok és extrák"**: arcfelismerés+Emberek, XMP-export,
    sötét téma, kollázs/film, geotag-térkép, duplikátum-kereső, nyomtatás/e-mail.
  **Automatikusan alkalmazandó**: új jegy triage-elésekor a P-címke MELLÉ tegyél
  milestone-t is (fenti besorolás szerint) — a felhasználónak ezt nem kell
  kérnie, és NEM szabad utólag „melyik milestone?"-t kérdezni; a fázismodell
  eldönti. **Eszköz-korlát:** a github MCP nem tud milestone-t listázni/létrehozni
  (`issue_write` csak `milestone`-SZÁMMAL sorol be: 1/2/3). Ha a számok kellenek,
  a `https://github.com/sanchomuzax/PicasaPy/milestones` oldal WebFetch-csel
  olvasható — de a fenti 1/2/3 fix.

## Tanulságok

- **2026-07-22 (módszertan — a hisztogram-saga): visszatérő hiba → tünet-foltozás
  TILOS; a valódi FUTÁSIDŐT diagnosztizáld bizonyítékkal, mielőtt kódot írsz.**
  Ha egy javítás nem tart, vagy a hiba a „javítás" után is jelentkezik (élesben,
  a felhasználó képén), NE patch-elj tovább vaktában: reprodukáld és a TÉNYLEGES
  futásidőt vizsgáld (pl. élő QML-kifejezés-kiértékelés a valódi appban).
  **„FALSE-GREEN" csapda:** az a teszt, ami csak azt nézi, hogy a kód LEFUTOTT-e
  (pl. `paintCount>0`), nem azt, hogy a KIMENET helyes-e, hamis zöld — UI/render-
  hibánál a megfigyelhető KIMENETET kell ellenőrizni, és a felhasználó éles gépes
  (Windows/RPi) képes visszajelzése a végső elfogadás. **Törékeny helyett
  robusztus:** időzítés-/scene-graph-függő megoldás (QML `Canvas`+`requestPaint`)
  helyett deklaratív, mindig-renderelő út (Rectangle-oszlopok). Konkrét eset: a
  hisztogram három „zöld" javítás (#25/#228) után is ÜRES maradt; a valódi ok
  (Python `tuple` QML-ben NEM tömb → `.length` undefined → a rajzoló minden
  csatornát kihagyott) csak élő futásidő-kiértékeléssel derült ki (#232). Adat
  QML-nek: **listát adj, ne tuple-t** (a tuple nem tömb QML-oldalon).

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
