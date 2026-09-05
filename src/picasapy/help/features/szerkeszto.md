# A szerkesztő és a hét fül

## Nem-destruktív szerkesztés

A PicasaPy **soha nem írja felül a képfájlodat magától**. A szerkesztések
utasításként kerülnek a mappa `.picasa.ini` fájljába, és a program
minden megjelenítésnél újraszámolja őket. Az eredeti fájl érintetlen
marad, amíg te magad nem mented ki (lásd [Mentés,
visszaállítás](mentes.md)).

## A szerkesztő megnyitása

Nyisd meg a képet a nézőben; a bal oldali panel a szerkesztő. Hét fül van
benne, balról jobbra:

| fül | mire való |
|---|---|
| **Gyakori javítások** | a leggyakoribb műveletek |
| **Finomhangolás** | fény és szín csúszkákkal |
| **Effektek** | az alap effektkészlet |
| **Kreatív** | további effektek |
| **Művészi** | hangulatos, erősebb effektek |
| **További effektek** | ami a motorban megvan, de az eredeti Picasa felületén nem volt |
| **Régi effektek** | régi Picasa-változatokból örökölt szűrők |

A 3–7. fül csempéin a **kék jelvény** az egykattintásos effekteket
jelöli — lásd [Effektek](effektek.md).

Az effektek részletes listája: [Effektek](effektek.md).

## Gyakori javítások

Kilenc gomb:

- **Vágás** — külön eszköz, lásd lentebb.
- **Kiegyenesítés** — a ferde horizont igazítása csúszkával.
- **Vörösszem** — a vörös szemek javítása.
- **Jó napom van** — egy kattintásos, általános javítás.
- **Automatikus kontraszt** — a fények és árnyékok automatikus
  kiegyenlítése.
- **Automatikus szín** — a színek automatikus semlegesítése.
- **Retusálás** — folt eltüntetése ecsettel.
- **Szöveg** — felirat írása a képre.
- **Derítőfény** — a sötét részek felderítése csúszkával.

## Vágás

A **Vágás** gomb átfedő vágókeretet nyit a képre. A keret sarkainál és
oldalainál fogva méretezhető, belül húzva mozgatható.

- **Képarány**: kézi vágás, négyzet, és egy csomó kész arány
  (10×15, levélpapír, A4, CD-borító, szabvány képernyő, széles vászon,
  digitális képkeret és társai). A **Egyéni méretarány hozzáadása…**
  paranccsal saját arányt vehetsz fel névvel, szélességgel és
  magassággal; a saját arányt később törölni is tudod.
- **Álló** / **Fekvő** — a keret elforgatása.
- **Forgatás** gomb — a képarány oldalainak cseréje.
- **Javasolt vágások** — a program kínál néhány kivágást: a részletre, a
  színre, a horizontra, illetve az arcokra komponálva és az arcokra
  szűkítve.
- **Előnézet** — megnézed, milyen lesz.
- **Alkalmaz** véglegesíti (nem-destruktívan), **Mégse** elveti,
  **Alaphelyzet** eldobja a már alkalmazott vágást.

## Vörösszem

Az **Automatikus** gomb magától megkeresi a vörös szemeket. Ha nem talál
semmit, kiírja: „Az automatika nem talált vörös szemet." Ha talált,
azt is jelzi.

Kézzel is jelölhetsz: húzz keretet a szem köré. A panel számolja, hány
területet jelöltél ki. A **Visszavonás** az utolsó jelölést veszi vissza,
az **Alaphelyzet** mindet.

Van egy kapcsoló, amivel a négyzetes körvonalak nélkül nézheted meg az
eredményt.

## Retusálás

Az **Ecset mérete** csúszkával állítod a folt méretét, majd a képre
kattintva tünteted el a hibát. A panel kiírja, hány foltot javítottál.
**Folt visszavonása** és **Folt újra** léptet a foltok között, az
**Alaphelyzet** mindet törli.

## Szöveg

Kattints a képre, ahova a szöveget szeretnéd, és gépeld be. Beállítható:

- **Betűtípus** és **betűméret**, valamint **félkövér**, **dőlt** és
  **aláhúzott** stílus,
- **igazítás** balra, középre, jobbra,
- **Szöveg színe** és **Körvonal színe**, **Körvonal vastagsága**,
- **Átlátszatlanság**,
- kapcsoló, amivel csak a körvonal látszik, kitöltés nélkül.

A **betűméret** az eredeti Picasa tizenhat méretéből választható:
8, 10, 12, 14, 16, 18, 20, 22, 26, 30, 36, 48, 60, 72, 84, 96 —
alapértelmezésben 12. A méret a **kép magasságához** igazodik, nem a
képernyőhöz: ugyanaz a felirat egy nagyobb képen is ugyanolyan arányú
marad. Ha a feliratot a fogantyújával méretezed át, a választó a
legközelebbi listaértéket mutatja.

A **Körvonal vastagsága** csúszka a legvékonyabb és a legvastagabb
körvonal között folyamatosan állítható; nullára húzva nincs körvonal.

A **Felirat átvétele** gomb a kép meglévő képfeliratát írja be szövegnek.
A **Minden meglévő szöveg törlése** letörli a képre írt szövegeket.

A beállítások a `.picasa.ini`-be kerülnek — a **betűtípus**, a
**betűméret**, a **félkövér** állás, a **körvonal vastagsága** és a
színek is —, tehát a felirat legközelebb is úgy néz ki, ahogy
beállítottad, és a windowsos Picasa is így látja.

> Korábban a program minden feliratot félkövérként mentett, a körvonal
> vastagsága pedig mindig elveszett. Mindkettő megjavult; a régebben
> mentett feliratokat érdemes egyszer ellenőrizni.

## Finomhangolás

Csúszkák: **Derítőfény**, **Kiemelések**, **Árnyékok**,
**Színhőmérséklet**. Emellett két egykattintásos javítás (megvilágítás és
szín), valamint az **Alapszínválasztás**: egy pipettával kijelölsz a
képen egy semleges szürke pontot, és a program ahhoz igazítja a színeket.

## Hisztogram

A szerkesztő alatt a **hisztogram** mutatja a kép fényeloszlását és a
fényképezőgép adatait. Ha a fájlban nincs EXIF-információ, ezt írja:
„Nincs elérhető EXIF-adat."

## Visszavonás

A nézőben lévő **Visszavonás** és **Újra** gomb lépésenként veszi vissza,
illetve állítja helyre a szerkesztéseket. A **Kép ▸ Összes szerkesztés
visszavonása** egy lépésben törli az összes szerkesztést a kijelölt
képekről.
