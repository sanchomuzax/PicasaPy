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

## A jobb oldali fiók szerkesztés közben

A **Címkék**, **Emberek**, **Helyek** és **Tulajdonságok** panel a
szerkesztőben is megnyílik: a képtálca négy panelkapcsolójával, a
**Nézet** menüből, vagy a **Ctrl+0** billentyűvel. Így a szerkesztésből
kilépés nélkül tudsz címkézni, nevet adni egy arcnak vagy megnézni a
kép adatait.

> Korábban a négy gomb közül három csak benyomódott, de nem hozott elő
> semmit a nézőben — ez megjavult.

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

- **Képarány**: kézi vágás, a kép jelenlegi aránya, négyzet
  (CD-borító), a papírképek méretei centiméterben (5×8, 9×13, 10×15,
  13×18, 20×25), **A4** teljes oldal, valamint a képernyő-arányok:
  **4:3** (szabvány képernyő), **16:10** (széles monitor), **16:9**
  (HDTV) és **5:3** (széles digitális képkeret). Az **Egyéni méretarány
  hozzáadása…** paranccsal saját arányt vehetsz fel névvel,
  szélességgel és magassággal; a saját arányt később törölni is tudod.
- **Álló** / **Fekvő** — a keret elforgatása.
- **Forgatás** gomb — a képarány oldalainak cseréje.
- **Javasolt vágások** — a program kínál néhány kivágást: a részletre, a
  színre, a horizontra, illetve az arcokra komponálva és az arcokra
  szűkítve.
- **Előnézet** — megnézed, milyen lesz.
- **Alkalmaz** véglegesíti (nem-destruktívan), **Mégse** elveti,
  **Alaphelyzet** eldobja a már alkalmazott vágást.

### Arány kényszerítése húzás közben

Miközben **új keretet húzol**, a lenyomva tartott billentyű megköti a
keret oldalarányát:

| billentyű | milyen arányt ad |
|---|---|
| Shift | a fénykép saját aránya |
| Ctrl | ennél egyharmaddal szélesebb |
| Alt | ennél felével szélesebb |

Amit érdemes tudni:

- A **Shift nem négyzetet ad**, hanem a kép saját arányát — négyzetet
  csak négyzetes fényképen. Ezt az eredeti Picasa is így csinálta.
- Ha többet tartasz lenyomva, az **Alt üt mindent**, a **Ctrl** pedig a
  Shiftet.
- A kényszer **pillanatnyi**: amint felengeded a billentyűt, a keret
  húzás közben is azonnal szabaddá válik. Nem marad bekapcsolva.
- A vágónál a lenyomott billentyű a **Képarány** listából választott
  arányt is felülírja, amíg húzol. A kész keret utólagos méretezésekor
  viszont már nincs hatása — ott a listából választott arány szabályoz.

Ugyanez a három billentyű működik a **vörösszem** és az **arc-hozzáadás**
keretének húzásakor is.

## Vörösszem

Az **Automatikus** gomb magától megkeresi a vörös szemeket. Ha nem talál
semmit, kiírja: „Az automatika nem talált vörös szemet." Ha talált,
azt is jelzi.

Kézzel is jelölhetsz: húzz keretet a szem köré. Húzás közben a
**Shift**, a **Ctrl** és az **Alt** itt is megköti a keret arányát — ahogy
a vágásnál, a fentebbi „Arány kényszerítése húzás közben" szakasz szerint.
A panel számolja, hány területet jelöltél ki. A **Visszavonás** az utolsó
jelölést veszi vissza, az **Alaphelyzet** mindet.

Egyetlen keretet is kivehetsz: **kattints bele** — a panel is ezt írja
(„Megjegyzés: a keretbe kattintva visszavonhatja a változást"). Az egér
mutatója megváltozik a keret fölött, ebből látod, hogy odatalálsz. Ha két
keret átfedi egymást, a később felvett esik ki: azt látod felül.

Ez az **Alkalmazás** előtt működik. Utána a javítás már a képpontokban
van, és a keretek nem jönnek vissza.

Van egy kapcsoló, amivel a négyzetes körvonalak nélkül nézheted meg az
eredményt.

## Retusálás

Az **Ecset mérete** csúszkával állítod a folt méretét. Kattintással
jelölöd ki a javítandó területet; utána az egeret mozgatva előnézetben
látod, mivel pótolná a program, és egy újabb kattintás véglegesíti.
Nagyított képen a **Ctrl** lenyomva tartásával húzva pásztázhatsz. A
panel kiírja, hány foltot javítottál.
**Folt visszavonása** és **Folt újra** léptet a foltok között, az
**Alaphelyzet** mindet törli.

## Szöveg

Kattints a képre, ahova a szöveget szeretnéd, és gépeld be. Beállítható:

- **Betűtípus** és **betűméret**, valamint **félkövér**, **dőlt** és
  **aláhúzott** stílus,
- **igazítás** balra, középre, jobbra,
- **Szöveg színe** és **Körvonal színe**, **Körvonal vastagsága**,
- **Átlátszóság**,
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

A szerkesztő alatt a **hisztogram** mutatja a kép fényeloszlását, mellette
pedig a felvétel adatai: a fényképezőgép neve, a gyújtótávolság (és ennek
kisfilmre átszámított értéke), a záridő, a rekesz és az ISO-érzékenység.
Ha a fájlban nincs EXIF-információ, ezt írja: „Nincs elérhető EXIF-adat."

A vaku adata **nem** itt van, hanem a Tulajdonságok panelen — az eredeti
Picasában is ott volt.

## Visszavonás

A nézőben lévő **Visszavonás** és **Újra** gomb lépésenként veszi vissza,
illetve állítja helyre a szerkesztéseket. A **Kép ▸ Összes szerkesztés
visszavonása** egy lépésben törli az összes szerkesztést a kijelölt
képekről.
