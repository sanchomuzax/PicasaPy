# Csillagok, feliratok, címkék

Mindhárom a `.picasa.ini` fájlba kerül a képek mellé, tehát a képfájlt
nem írja át — kivéve a feliratot, amit a JPEG-be is beleírunk (lásd
lentebb).

## Csillag

A csillag a gyors megjelölésre való. Csillagot adni és elvenni így tudsz:

- a képtálca **Csillag hozzáadása/eltávolítása** gombjával (a kijelölés
  minden képére hat),
- diavetítés közben a vezérlősáv csillag-gombjával.

A csillagozott képeket a bal hasáb **Csillagozott képek** albuma
gyűjti össze, és az eszköztár csillag-szűrője is kiemeli őket.
A **Szerkesztés ▸ Csillagozottak kijelölése** egy lépésben kijelöli az
összeset a jelenlegi nézetben.

## Képfelirat

A felirat a kép alá írt rövid szöveg. A nézőben a kép alján
végigfutó sávba kattintva írhatod be — ha még nincs felirat, a
„Készítsen képfeliratot!" hívogat a sáv közepén. Enterrel mented, Esc-cel
eldobod, amit beírtál.

A sáv két végén egy-egy kis gomb áll:

- **balra** a **Felirat megjelenítése/elrejtése** kapcsoló — egy
  világos négyzet, benne két vonal, ha a sáv látszik, és üres, ha nem.
  Kikapcsolt sávnál is a helyén marad, tehát ezzel hozod vissza;
- **jobbra** a **Felirat törlése** gomb, ami rákérdezés nélkül üríti a
  feliratot. Üres felirat mellett szürke.

A rácsban a **Nézet ▸ Indexkép felirata ▸ Képfelirat** beállítással
hozhatod elő az indexképek alá.

### Ugyanaz a felirat több képre

A **Szerkesztés ▸ Szöveg másolása** a kijelölt kép feliratát a vágólapra
teszi, a **Szerkesztés ▸ Szöveg beillesztése** pedig a vágólap szövegét
**minden kijelölt kép** feliratába beírja. Így egy feliratot végig lehet
vinni egy egész sorozaton.

Üres vágólappal a **Szöveg beillesztése** szürke, tehát nem tudja
véletlenül letörölni a meglévő feliratokat.

Ha a kijelölt képek közül **bármelyiken már van felirat**, a program
előbb rákérdez: „Biztosan lecseréli a jelenlegi képfeliratot a vágólap
tartalmára? (Ez a művelet nem vonható vissza)". A **Csere** gomb
beírja a vágólap szövegét minden kijelölt kép feliratába, a **Mégse**
semmit nem változtat. Ha egyik kijelölt képnek sincs még felirata, a
beillesztés kérdés nélkül lefut.

A feliratot a PicasaPy a JPEG-fájl IPTC-mezőjébe is beírja, így más
programok is látják.

## Címkék

A címkék a jobb oldali **Címkék** panelen élnek. Megnyitás: **Nézet ▸
Címkék** vagy **Ctrl+T**, illetve a képtálca Címkék gombja. A Ctrl+T
nyitja és zárja is a panelt.

- Jelölj ki egy vagy több képet, majd a beíró mezőbe („Írjon be egy
  hozzáadandó címkét:") írd be a címkét, és nyomj Entert. A címke a
  kijelölés minden képére felkerül.
- A panelen látszik, mely címkék vannak a kijelölésen. A lista fölötti
  fejléc megmondja, mire vonatkozik: egyetlen kijelölt képnél a kép
  nevét írja (*kép.jpg címkéi:*), több képnél *Címkék az aktuális
  kijelölésben:*, ha pedig a megjelenített album **összes** képe ki van
  jelölve, *Címkék az aktuális kijelölésben (teljes album):*. Egy címkére
  jobbgombbal kattintva: **Címke hozzáadása a teljes kijelöléshez**,
  **Így címkézett elemek keresése**, **Címke eltávolítása**.

### Sok képre egyszerre

Ha **30-nál több** képet jelöltél ki, a program címke hozzáadása előtt
rákérdez: „Meglehetősen nagy számú elemet jelölt ki. Biztosan az összes
(*N*) elemre alkalmazni szeretné ezt a címkét?" Az **OK** felrakja a
címkét a kijelölés minden képére, a **Mégse** nem címkéz semmit. A kérdés
a beíró mezőre, a gyorscímke-gombokra és a címke helyi menüjének
**Címke hozzáadása a teljes kijelöléshez** tételére egyaránt érvényes. A kijelölést a
program a kérdés megjelenésekor rögzíti, tehát a döntésedig nem változhat
a cél.

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

A panel alján tíz **Gyorscímke**-gomb van a leggyakoribb címkéidnek.
Egy gombra kattintva a címke azonnal felkerül a kijelölésre.

A még üres gomb **?** jelet mutat. Ha rámutatsz, a buboréksúgója: „Ide
kattintva konfigurálhatja a gyorscímkéket"; ha rákattintasz, egy
tájékoztató ablak elmondja, hogyan kerül címke a gombra, és semmi nem
íródik a képekre.

A gombok tartalmát a **Gyorscímkék konfigurálása** párbeszédben állítod
be. Itt bekapcsolhatod, hogy a felső két gombot a program tartsa fenn a
legutóbb használt címkéknek, és egy gombbal fel is töltheted az üres
mezőket a gyakran használt címkéiddel.
