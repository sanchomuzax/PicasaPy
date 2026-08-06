# Projektfüggetlen tanulságok — tervezés, projektmenedzsment, fejlesztés

Ez a dokumentum a PicasaPy-projekt során felhalmozott, **platform- és
projektfüggetlen** tapasztalatokat gyűjti össze, hogy más projektekben is
felhasználhatók legyenek. A konkrét (Picasa-/Qt-specifikus) részletek a
`MEMORY.md`-ben és a `docs/` alatt maradnak — itt az általánosítható elv áll.

---

## 1. Tervezés és projektindítás

### 1.1 Kutatási fázis a kódolás előtt

Mielőtt egyetlen sor termékkód készülne, érdemes egy dedikált kutatási fázist
lefuttatni, amelynek **írott specifikációk** a kimenetei. A PicasaPy-nál ez a
formátum-kutatás volt; az elv bárhol érvényes, ahol meglévő rendszerhez,
formátumhoz vagy elváráshoz kell illeszkedni. Bevált eszköztár:

- **Tudásbázis-építés** (források összegyűjtése egy helyre, pl. NotebookLM) —
  a specifikációk első vázlatai ebből születnek.
- **Referencia-implementációk keresztauditja**: több független nyílt projekt
  kódját egymással validálni — egyetlen forrás tévedhet, három egybehangzó
  forrás már bizonyíték.
- **Valódi, nagy méretű adaton igazolás**: a specifikáció addig hipotézis,
  amíg éles adaton (nálunk 2 GB-os, 140 ezer képes adatbázison) nem futott
  hibátlanul.
- **Golden-master módszer nem publikus algoritmusokhoz**: ismert bemenetek →
  az eredeti rendszer kimenetei → a különbségből egzakt transzformáció.
  Ez az egyetlen megbízható út, ha a viselkedés nincs dokumentálva.
- **Mérésalapú technológiaválasztás**: a keretrendszer-/könyvtár-döntést
  (nálunk a GUI-toolkit) valódi, a célhardveren futó benchmark döntse el,
  ne vélemény vagy divat — és a döntés ADR-ben rögzüljön.

### 1.2 „Dokumentálatlan" ≠ megfejthetetlen

Amit az első átvizsgálás „dokumentálatlan binárisként" zár le, arra érdemes
egy második, mély kört szánni: fejlécmezők értelmezése + egy olcsó
konzisztencia-ellenőrzés (pl. „a kifejtett adat mérete egyezik-e a fejlécben
állítottal") fél óra alatt 100%-os megfejtést adhat. Az olcsó, erős
visszaigazolást keresd — az önellenőrző dekóder többet ér száz feltételezésnél.

### 1.3 Referencia előbb, kód után

UI- vagy viselkedés-paritás kérdésében az **első lépés a referencia
beszerzése** (screenshot, eredeti forrás, mérés), nem a kódolás. A PicasaPy
nagy UI-auditja mutatta meg: referencia nélkül évekig észrevétlen maradt,
hogy a felület a valódinak csak a töredékét fedi. Kódból, specből, jó
szándékból ezt sosem találtuk volna ki.

### 1.4 Kompatibilitás: round-trip elv és hangos hiány

Idegen formátum kezelésénél két szabály:

- **Round-trip elv**: amit nem értünk, bitre pontosan őrizzük meg és írjuk
  vissza. Így a saját rendszer párhuzamosan használható az eredetivel.
- **Az „ismeretlen elem = néma kihagyás" hibatűrés elrejti a hiányt**: a
  felhasználó hiányos eredményt lát, és senki nem tudja, miért. Legalább
  egyszer, összesítve jelezni kell, mit nem tudunk feldolgozni.

### 1.5 Döntések és tudás rögzítése — kétszintű memória

- **Rögzített döntések** dátummal, indoklással, egy központi helyen
  (CLAUDE.md / ADR-ek) — a későbbi viták és újratárgyalások ellenszere.
- **Kétszintű tudástár**: ami *mindig, kérés nélkül* kell → a mindig betöltődő
  kontextusba (CLAUDE.md); a részletes tanulságok → külön memóriafájlba
  (MEMORY.md), amelyet minden munkamenet elején kötelező elolvasni. Enélkül a
  párhuzamos munkafolyamok újra elkövetik a régen megoldott hibákat.
- A tanulság-bejegyzés formátuma: dátum + rövid horog + kontextus + az
  általános szabály. A jó bejegyzés nem esetleírás, hanem **jövőbeli viselkedési
  szabály**.

### 1.6 Fázisolt terjedelem (MVP-fegyelem)

A teljes funkciólistát fázisokra kell bontani (nálunk V1 kezelő+néző,
V2 szerkesztő, V3 arcok), és a fázisokat a feladatkezelőben milestone-ként
leképezni. Minden új feladat születésekor azonnal fázisba sorolandó — így a
terjedelem-csúszás láthatóvá válik, és a „melyik fázis?" kérdést a modell
dönti el, nem eseti vita.

---

## 2. Projektmenedzsment

### 2.1 Egyetlen feladat-tábla, címke-alapú foglalási zár

Párhuzamos munkafolyamok (több fejlesztő vagy több agent) mellett:

- **Minden feladat egy jegy** (issue); állapotát címkék viszik:
  `ready` (felvehető) / `in-progress` (foglalt) / `blocked` (függőségre vár).
- **Foglalási kapu, kötelező sorrendben**: szabálykönyv elolvasása → címke
  átbillentése → branch létrehozása és felpusholása. **A branch létezése a
  zár** — aki frissít, látja, hogy a feladat foglalt.
- **Elárvulási szabály**: ha egy foglalt jegyen X napja nincs commit, bárki
  visszaállíthatja szabadra. Aki szünetel, proaktívan adja vissza a jegyet.
- Menet közben talált új feladatot **nem elkezdeni, hanem jegyre venni** —
  a terjedelem-fegyelem záloga.

### 2.2 Prioritás: súlyosság × kerülőút

Egyszerű, jól dönthető prioritási skála: minél nagyobb a kár és minél kevésbé
van kerülőút, annál előrébb (P0 adatvesztés/crash … P4 best-effort). Minden
jegy triage-elésekor **automatikusan** kap prioritást és fázis-besorolást —
ez nem külön kérésre történik, hanem a folyamat része.

### 2.3 Szerep-jelölések a jegyeken

Ha a folyamatban ember és automata is dolgozik, kelljen egyértelmű jelölés
arra, **kinek a lépésére vár** a jegy (nálunk: assignee = a felhasználó kezére
vár; felelős nélküli jegy az automatáé). A triage része ennek karbantartása is.

### 2.4 Forró fájlok és az integrátor-szerep

Párhuzamos fejlesztésnél a merge-konfliktusok néhány központi fájlban
születnek (bekötési pontok, séma, fordítások, dizájn-tokenek). Ezeket
**forró fájlként** kell listázni, és csak egyetlen kéz — az integrátor —
módosíthatja őket; a feature-ág az igényét a jegyben írja le. A modulok
felbontásával a forró-fájl-lista tudatosan szűkíthető.

### 2.5 A feladat a teljes körrel ér véget

A leggyakoribb folyamat-hiba: a munka „PR megnyitva" állapotban megáll.
Szabály: a vállaló viszi a jegyet a **teljes lezárásig** — zöld ellenőrzés →
merge → jegyzárás + címke-rendezés → verzióemelés → kiadás-ellenőrzés →
nincs beragadt futás. Egyetlen lépés sem maradhat „majd valaki szól" állapotban.
Hosszú, várakozós fázisokban is jár a rövid állapotjelzés: **a néma munka a
megrendelő felől nézve ottfelejtett munka.**

### 2.6 A haladás legyen látható a nem-fejlesztőnek

A megrendelő nem a commit-listát nézi, hanem egy számára érthető felületet
(nálunk: a GitHub Releases hasábot). Ezért minden érdemi változás járjon
**verzióemeléssel és kiadással** — a verzióemelés nélküli merge a megrendelő
számára láthatatlan, és joggal háborítja fel. Az automatikus kiadás-folyamat
(minden main-push után: ha az aktuális verzióhoz nincs release, készül) a
kézi mulasztást is kizárja.

### 2.7 Automatizált integrátor-kör

Ütemezett (óránkénti) automata kör, amely: átnézi a nyitott PR-eket, lokálisan
összefésüli a friss fő-ággal, teljes tesztet futtat, zöld esetén mergel és
zárja a jegyet, érdemi merge után verziót emel, takarít (elárvult foglalások,
árva branchek), és a végén rövid, emberi nyelvű összefoglalót küld. Így a kész
munka emberi beavatkozás nélkül is beér.

### 2.8 Költség- és erőforrás-tudatosság

- **Ne dolgozz vakon a kereted terhére**: az erőforrás-/költségállás legyen
  lekérdezhető, és nagy munka előtt kötelezően le is kérdezendő; a verdikt
  (GO/CAUTION/STOP) szabja meg a stílust.
- **Olcsó eszköz a gépies munkára, drága csak a kritikusra**: a delegált
  részfeladat soha ne örökölje némán a legdrágább erőforrást; sablonos munkát
  olcsó úton, vagy delegálás nélkül, helyben kell elvégezni.
- **Párhuzamosítás csak nagy, tényleg független feladatokra**: sok apró vagy
  ütköző feladatnál a párhuzamos infrastruktúra (több munkaterület + több
  végrehajtó + integráció) drágább és kockázatosabb, mint a soros végigvitel.
  Az előre látható ütközést szerializálni kell.
- **Az önjelentésnek nem hiszünk**: a „kész, zöld" jelentést a központi
  folyamat maga ellenőrzi (teszt + CI), és csak utána integrál.

### 2.9 Megbízható határidő-követés

A folyamaton belüli, „best-effort" emlékeztető nem elég kritikus határidőhöz
(kiadás-ellenőrzés, hosszú futás követése): **tartós, szerver-oldali,
újraindulást túlélő időzítő** kell, a belső ébresztő legfeljebb kiegészítő.
Aki vár valamire, az élesítsen időzítőt — a megrendelőnek soha ne kelljen
visszajönnie „Nos, mi van?" kérdéssel.

---

## 3. Fejlesztés és minőségbiztosítás

### 3.1 Alapelvek

- **TDD**: bukó teszt előbb (RED → GREEN → REFACTOR), magas lefedettség.
- **Sok kicsi fájl, kevés nagy** (200–400 sor tipikus, 800 max) — a kis
  fájl a párhuzamos munka és a code-review barátja is.
- **Immutabilitás**: új objektum a mutáció helyett.
- **Input-validáció és átfogó hibakezelés** mindenhol; nincs hardkódolt
  titok, nincs bent felejtett nyomkövetés.

### 3.2 A false-green csapda: a teszt a kimenetet mérje

Az a teszt, amely csak azt nézi, hogy a kód *lefutott* (pl. „a rajzoló
meghívódott"), nem azt, hogy a *kimenet helyes*, hamis zöldet ad. UI-/render-
hibánál a megfigyelhető kimenetet kell ellenőrizni, és a végső elfogadás a
valódi környezetben, valódi adaton történő ellenőrzés.

### 3.3 Bukó teszt ≠ automatikusan termékhiba

Mielőtt termékkódot javítanál egy bukó tesztre: **diagnosztizáld a tényleges
futásidőt bizonyítékkal** (kiíratás, élő kiértékelés). A teszt élhet elavult
feltételezéssel — ilyenkor a teszt javítandó. És fordítva: visszatérő hibánál
a tünet-foltozás tilos; ha egy javítás „nem tart", a gyökérokot kell élő
futásban megfogni, nem újabb foltot tenni rá.

### 3.4 Flaky teszt: az újrafuttatás nem stratégia

Ha ugyanaz a teszt másodszor is ugyanúgy bukik, a rerun pazarlás és zaj.
Három legitim út van: (1) a teszt determinisztikussá tétele (szinkronpont,
érték-stabilizálódás kivárása, ésszerű tolerancia), (2) a gyökérok javítása,
(3) dokumentált, jeggyel követett kizárás. Rerun legfeljebb egyszer, és
kizárólag *beragadt* (timeout-os) futásra — érték-eltérésre soha.

### 3.5 Őrök és assert-ek: az okra szűrj, ne a zajra

A „minden figyelmeztetés = hiba" típusú őr minden környezet-frissítésnél
hamis pirosat ad — épp az ellenkezőjét annak, amiért készült. A helyes szűrés
a jelenség **okára** szűkít (konkrét hibaminták), és az osztályozó külön,
önmagában tesztelhető modulba kerül, valódi üzenet-mintákkal mindkét oldalról.
Több platformra ható őrnél **egy platform zöldje nem bizonyíték** — a többi
láb eredményét meg kell várni a lezárás előtt.

### 3.6 Timeout mindenhol, beragadt futás lelövése

- Minden tesztfuttatás szigorú timeouttal fut; az első beragadásnál azonnali
  leállítás és a problémás rész izolált újrafuttatása — percekig várni vagy
  ugyanazt a beragadó futást ismételgetni tilos.
- Ismerten halott tesztet (hiányzó rendszerfüggőség) skip-elhetővé kell tenni,
  nem újra és újra elindítani.
- **CI-higiénia**: a beragadt távoli futás erőforrást foglal és lavinát okoz
  (nálunk 19 otthagyott futás órákra bénította a kiadás-automatikát). Aki
  pusholt, a munkája végén köteles meggyőződni róla, hogy a futásai
  lezárultak; a pipeline-ok kapjanak kötelező timeout-korlátot.
- Ha a teljes készlet egyben instabil, **darabolt futtató szkript** legyen a
  kanonikus út, és mindenki azt használja.

### 3.7 Arányos ceremónia: a triviális változás ne húzzon teljes kört

Kockázatmentes, a program futására nem ható változásnál (szövegjavítás,
dokumentáció, kozmetika) a teljes teszt-ceremónia és a CI-ra várakozás
pazarlás — az ilyen változás azonnal integrálható. Teljes verifikáció csak
tényleges viselkedés-változásnál jár. A ceremónia mértéke a kockázathoz
igazodjon, ne a folyamat-reflexhez.

### 3.8 A felhasználó gépe nem a CI

Felhasználónak szánt eszköznek a *valódi* környezetet kell tűrnie — csapdák,
amiket a fejlesztői/CI-környezet sosem fog meg: nem-ASCII útvonalak, felhő-
szinkronkliens által zárolt mappák, hiányzó „magától értetődő" bemenetek.
Szabályok: hangos hiba a néma elnyelés helyett; nem szabad a felhasználót
kerülőútra kényszeríteni („tedd máshová") — ott működjön, ahová ő teszi;
a javítást a felhasználó pontos esetére írt teszt kísérje; a hibaüzenet az ő
nyelvén szóljon és cselekvésre fordítható legyen.

### 3.9 „Kész" és „hiteles" nem ugyanaz

Ha egy funkció közelítésen alapul, azt ki kell mondani: a közelítő modell
dokumentációja jelezze, hogy közelítés, mi az alapja, és mi kalibrálja majd;
egy központi státusz-tábla (MÉRT / MÉRT-DE-ELTÉR / KÖZELÍTŐ / PONTOS) mutassa
az igazságot. Ez nem szégyen, hanem a bizalom feltétele — a megrendelő a saját
adatait nézi a rendszeren.

### 3.10 Témázhatóság és tokenek

A dizájn-token-készlet csak akkor ér valamit, ha **senki nem ír hardkódolt
értéket** — a tokenrendszer bevezetése olcsó, a szétszórt hardkódok felkutatása
a drága. Új felületen érték csak tokenből; ami szándékosan téma-független,
azt kommentben kell jelölni, hogy a következő átvilágítás ne cserélje le.

### 3.11 Opcionális függőség: izoláld

Nem garantált modult külön komponensbe, lusta betöltés mögé — a hiánya csak a
saját funkcióját vigye el (érthető hibaszöveggel), ne az egész felületet.
A rejtett/blokkolt komponens erőforrást se fogyasszon.

### 3.12 Külső szolgáltatás kiesése ne állítsa meg a munkát

Ha egy külső API tartósan hibázik, miközben minden más működik: a munka
folytatódjon a megkerülő úton (helyi verifikáció, a zár fenntartása, utólagos
pótlás), és a tény írásban rögzüljön. A kiesés nem indok a leállásra.

---

## 4. Együttműködés nem-fejlesztő megrendelővel

- **Minden technikai műveletet a fejlesztő/automata végez** — a megrendelőt
  soha nem szabad verziókezelési vagy infrastruktúra-lépésre kérni.
- **Kérdés csak termék-viselkedésről**, emberi nyelven („melyik sarokban
  legyen a gomb?") — technikai eldöntendőkben józan alapértelmezett döntés,
  utólagos egymondatos összefoglalóval.
- **A megrendelő anyanyelvén** folyik minden kommunikáció; a kód és a belső
  konvenciók a projekt nyelvét követik.
- **A megrendelő visszajelzése a legerősebb teszt**: a nagy hiányokat
  (UI-paritás, hiteltelen kalibráció, üres kimenet éles adaton) nála derülnek
  ki — a visszajelzést a folyamat kincsként kezelje, és tanulságként rögzítse.
