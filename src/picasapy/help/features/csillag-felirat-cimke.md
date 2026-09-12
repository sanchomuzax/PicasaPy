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

A feliratot a PicasaPy a JPEG-fájl IPTC-mezőjébe is beírja, így más
programok is látják.

## Címkék

A címkék a jobb oldali **Címkék** panelen élnek. Megnyitás: **Nézet ▸
Címkék** vagy **Ctrl+T**, illetve a képtálca Címkék gombja. A Ctrl+T
nyitja és zárja is a panelt.

- Jelölj ki egy vagy több képet, majd az **Új címke…** mezőbe írd be a
  címkét és nyomj Entert. A címke a kijelölés minden képére felkerül.
- A panelen látszik, mely címkék vannak a kijelölésen. Egy címkére
  jobbgombbal kattintva: **Címke hozzáadása a teljes kijelöléshez**,
  **Így címkézett elemek keresése**, **Címke eltávolítása**.

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

A gombok tartalmát a **Gyorscímkék konfigurálása** párbeszédben állítod
be. Itt bekapcsolhatod, hogy a felső két gombot a program tartsa fenn a
legutóbb használt címkéknek, és egy gombbal fel is töltheted az üres
mezőket a gyakran használt címkéiddel.
