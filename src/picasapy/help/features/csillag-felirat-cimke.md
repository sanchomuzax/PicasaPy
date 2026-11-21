# Csillagok, feliratok, címkék

Mindhárom a `.picasa.ini` fájlba kerül a képek mellé, tehát a képfájlt
nem írja át — kivéve a feliratot, amit a JPEG-be is beleírunk (lásd
lentebb).

A program a régi, nagy kezdőbetűs **Picasa.ini** nevű fájlból is beolvassa a
csillagokat és a feliratokat, ha a mappában nincs `.picasa.ini`. Így a
nagyon régi Picasával készített mappák adatai sem vesznek el. Amikor egy
ilyen mappában először mentesz valamit, a program új `.picasa.ini`-t hoz
létre, és a régi fájl **minden bejegyzését átviszi** bele; a régi
**Picasa.ini**-hez nem nyúl. A biztonsági mentés, a módosított képek
eltett eredetijei és az áthelyező importálás is számol a régi fájl
adataival, tehát ezeknél sem vesznek el.

## Csillag

A csillag a gyors megjelölésre való. Csillagot adni és elvenni így tudsz:

- a képtálca **Csillag hozzáadása/eltávolítása** gombjával (a kijelölés
  minden képére hat, képenként: a csillagos kép elveszti a csillagát, a
  csillag nélküli megkapja),
- az **F4** billentyűvel, ami ugyanazt teszi, mint a tálca gombja (a
  könyvtárban és a nézőben is; ha a gomb szürke, az F4 sem csinál semmit),
- a könyvtárban a **Ctrl+8** billentyűvel is, ami ugyanezt teszi (a
  nézőben ez nem működik),
- diavetítés közben a vezérlősáv csillag-gombjával.

A csillagozott képeket a bal hasáb **Csillagozott képek** albuma
gyűjti össze, és az eszköztár csillag-szűrője is kiemeli őket. Ha ebben
az albumban egy képet törölsz, a program csak a **csillagot veszi le**
róla - maga a fájl a lemezen marad, és az album nézetéből tűnik el.
A **Szerkesztés ▸ Csillagozottak kijelölése** egy lépésben kijelöli az
összeset a jelenlegi nézetben.

## Képfelirat

A felirat a kép alá írt rövid szöveg. A nézőben a kép alján
végigfutó sávba kattintva írhatod be; ha még nincs felirat, a
„Készítsen képaláírást!" hívogat a sáv közepén. Enterrel mented, Esc-cel
eldobod, amit beírtál. Ha a sávon kívül kattintasz, vagy közben másik
képre lépsz, a beírt felirat akkor is elmentődik, mégpedig ahhoz a
képhez, amelyikhez írtad. Ha a szöveget nem változtattad meg, a program
nem írja újra a képet.

A sáv két végén egy-egy kis gomb áll:

- **balra** a **Képfelirat megjelenítése/elrejtése** kapcsoló: egy
  világos négyzet, benne két vonal, ha a sáv látszik, és üres, ha nem.
  Kikapcsolt sávnál is a helyén marad, tehát ezzel hozod vissza;
- **jobbra** a **Képfelirat törlése** gomb. Előbb rákérdez egy
  **Jóváhagyás** ablakban: „Biztosan törli a kép feliratát?" A
  **Képfelirat törlése** gomb törli a feliratot, a **Nem** (ezen áll a
  fókusz) meghagyja. Üres felirat mellett a gomb szürke.

A rácsban a **Nézet ▸ Indexkép felirata ▸ Képfelirat** beállítással
hozhatod elő az indexképek alá.

### Felirat másolása több képre

A **Szerkesztés ▸ Szöveg másolása** és **Szöveg beillesztése** parancs
nem a képfeliratot, hanem a **Szöveg** eszközzel a képre írt szöveget
másolja (lásd [A szerkesztő](szerkeszto.md)), ahogy az eredeti Picasában.
A képfeliratot menüből ma nem lehet egyszerre több képre átvinni: képenként
kell beírnod.

A feliratot a PicasaPy a JPEG-fájl IPTC-mezőjébe is beírja, így más
programok is látják. Ha a képfájl írásvédett, a felirat akkor is
megmarad a PicasaPy-ban, csak a fájlba nem kerül bele.

## Címkék

A címkék a jobb oldali **Címkék** panelen élnek. Megnyitás: **Nézet ▸
Címkék** vagy **Ctrl+T**, illetve a képtálca Címkék gombja. A **Nézet ▸
Címkék**, a Ctrl+T, a Ctrl+K és a tálca gombja is kapcsolóként működik:
ha a Címkék panel már nyitva van, újra választva bezárja. Ha Ctrl+T-vel
nyitod meg, a kurzor rögtön a címke beíró mezőjébe kerül, így azonnal
gépelhetsz. Amíg a kurzor a mezőben áll, a második Ctrl+T nem zárja be a
panelt; kattints előbb a képekre, utána a Ctrl+T ismét nyitja és zárja.

- Jelölj ki egy vagy több képet, majd a beíró mezőbe („Írjon be egy
  hozzáadandó címkét:") írd be a címkét, és nyomj Entert, vagy kattints
  a mező melletti **+** gombra (buboréksúgója: „Címke hozzáadása az
  aktuálisan kijelölt elemekhez"). A címke a kijelölés minden képére
  felkerül. **Vesszővel elválasztva** egyszerre több címkét is
  beírhatsz (például `nyár, tenger, család`); az üres részeket a program
  kihagyja. Ha valamelyik címkét nem sikerült felvenni, a többi akkor is
  felkerül, és a mező alatt ez a sor jelenik meg: „A beírt szöveg egy
  része nem adható hozzá címkeként." Ha a mező üres, vagy csak szóköz
  van benne, az Enter nem ír címkét, hanem egy súgóablak jelzi, hogy
  nincs beírt szöveg.
- A panelen látszik, mely címkék vannak a kijelölésen. A lista fölötti
  fejléc megmondja, mire vonatkozik: egyetlen kijelölt képnél a kép
  nevét írja (*kép.jpg címkéi:*), több képnél *Címkék az aktuális
  kijelölésben:*, ha pedig a megjelenített album **összes** képe ki van
  jelölve, *Címkék az aktuális kijelölésben (teljes album):*.
- A lista sorrendje az eredeti Picasáét követi: elöl az a címke áll,
  amelyik a kijelölésben a **legtöbb képen** szerepel. Az egyformán
  gyakori címkék **fordított névsorban** követik egymást (Z-től A felé).
- Egy címkére jobb gombbal kattintva három tételt kapsz, az eredeti
  Picasa sorrendjében: **A címke hozzáadása a teljes kijelölt részhez**,
  **Az ilyen címkével ellátott elemek keresése** és, egy elválasztó
  vonal után, **A címke eltávolítása**.
  A keresés a címkét beírja a felső keresőmezőbe, és rögtön a találatokat
  mutatja; a keresőmezőt törölve visszakapod a teljes nézetet.

### Sok képre egyszerre

Ha **30-nál több** képet jelöltél ki, a program címke hozzáadása előtt
rákérdez: „Meglehetősen nagy számú elemet jelölt ki. Biztosan az összes
(*N*) elemre alkalmazni szeretné ezt a címkét?" Az **OK** felrakja a
címkét a kijelölés minden képére, a **Mégse** nem címkéz semmit. A kérdés
a beíró mezőre, a gyorscímke-gombokra és a címke helyi menüjének
**A címke hozzáadása a teljes kijelölt részhez** tételére egyaránt érvényes. A kijelölést a
program a kérdés megjelenésekor rögzíti, tehát a döntésedig nem változhat
a cél. Ha vesszővel egyszerre több címkét írtál be, a kérdés
**címkénként** külön jelenik meg, így mindegyikről külön dönthetsz.

### Ha a kijelölésben írásvédett kép van

A címkék a kép melletti `.picasa.ini` fájlba kerülnek, tehát írásvédett
mappában nem lehet őket megváltoztatni. A panel **előre szól**, mielőtt
gépelni kezdenél: „A címkék nem módosíthatók, mert a kijelölésben
írásvédett elem van." Ilyenkor a beíró mező, a hozzáadás gomb és a
gyorscímke-gombok is szürkék.

**Egyetlen** írásvédett kép is elég a jelzéshez. Ha csak egy ilyen csúszott
a kijelölésbe, vedd ki, és a többire már megy a címkézés.

### Egy címke tartalmából album

Az **Eszközök ▸ Kísérleti ▸ Címke megjelenítése albumként…** paranccsal
egy címkéből **rendes album** lesz: beírod a címkét, és a program
albumba gyűjti az összes olyan képet, amin szerepel.

A címke egészben számít, tehát a „nyár" nem húzza be a „nyaralás"-t. Ha
egyetlen képen sincs ilyen címke, a program megmondja: „Egyetlen képen
sincs ez a címke."

Ez nem élő szűrő: a kész album onnantól önálló, és a bal hasábon marad.

### Gyorscímkék

A panel alján, a **Gyorscímkék:** felirat alatt tíz gomb van a
leggyakoribb címkéidnek. Egy gombra kattintva a címke azonnal felkerül a
kijelölésre.

A még üres gomb **?** jelet mutat. Ha rámutatsz, a buboréksúgója: „Ide
kattintva konfigurálhatja a gyorscímkéket"; ha rákattintasz, megnyílik
a **Gyorscímkék konfigurálása** párbeszéd, és semmi nem íródik a
képekre.

A gombok tartalmát a **Gyorscímkék konfigurálása** párbeszédben állítod
be; ezt a felirat melletti fogaskerék-gomb nyitja meg (buboréksúgója is
**Gyorscímkék konfigurálása**). Itt bekapcsolhatod, hogy a felső két gombot a program tartsa fenn a
legutóbb használt címkéknek: az új címke az első gombra kerül, az addigi
első a másodikra csúszik, az addigi második pedig kiesik. Ha olyan
címkét használsz, amely már a két gomb egyikén áll, a sorrend nem
változik. Itt a kis- és nagybetű számít: a `Nyár` és a `nyár` két
különböző címkének látszik. Egy gombbal fel is töltheted az üres
mezőket: ez egyszeri művelet, amely a könyvtárad címkéiből tölti ki a
még üres helyeket. Az eredeti Picasához hasonlóan a könyvtár első száz
különböző címkéjéből merít, és kihagyja azt a kettőt, amelyet a legutóbb
használtál. Ha a legutóbbiak fenntartása ki
van kapcsolva, a program a gyorscímkézést nem is jegyzi fel a
legutóbbiak közé: ha később bekapcsolod, a közben használt címkék nem
jelennek meg ott.
