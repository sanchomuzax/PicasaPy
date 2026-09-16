# A Kollázs-panel halasztása — MÉRT előtte/utána (#1612)

**Gép:** RPi5, Linux 6.18, Python 3.13.5, Qt 6.8.2, 4 mag.
**Mérőeszköz:** `scripts/indulas_meres.py --mappa-szam 0` (üres könyvtár), a
`PICASAPY_STARTUP_TIMELINE=1` idővonalával.
**Változás:** a `CollagePanel` a `Main.qml`-ben `Loader` mögé került; az első
megnyitásig nem jön létre, utána megmarad (`betoltve` ragadós).

## A mérés váltakozva futott

A gép négymagos és más munka is folyt rajta, ezért a két változatot
**felváltva** mértük (a nyers „előbb mind az alap, aztán mind az ág" sorrend a
terhelés lefutását is mérte volna):

| kör | változat | meleg „QML betöltése (Main.qml)" | teljes indulás | 1 perces terhelés |
|---|---|---:|---:|---:|
| 1 | alap (`origin/main`) | 2347,4 ms | 3307,1 ms | 2,28 |
| 1 | #1612 (Loader) | **1334,4 ms** | **2216,4 ms** | 2,17 |
| 2 | alap | 2143,6 ms | 3011,8 ms | 2,16 |
| 2 | #1612 (Loader) | **1288,3 ms** | **2786,9 ms** | 2,46 |

Egy korábbi, három futásos sorozat ugyanezt adta (alap 2078,4 ms meleg QML /
2972,0 ms összesen; ág 1133,3 / 2016,1).

⇒ **A QML-szakasz ~2150…2350 ms-ról ~1290…1330 ms-ra esik: −43%**, a teljes
indulás ~700…1000 ms-mal rövidebb.

## ⛔ A jegy előrejelzése ALULBECSÜLT — és tudjuk, miért

A jegy komponensenkénti mérése a `CollagePanel`-re **74,5 ms**-ot adott, és
ebből ~6%-os nyereséget várt. A valóság **~1000 ms**. Az eltérés nem hiba a
mai mérésben, hanem az izolált méréS korlátja, amit az akkori jegyzet ki is
mondott: az izolált szám **rangsornak** jó, abszolút költségnek nem. A
`CollagePanel` a valódi fában a teljes kollázs-részfát behúzza (lap, beállítás-
fül, helyi menük, véletlen-sor); az izolált futásban a kontextus-függő
gyermekek egy része **nem jött létre** (a 158 fájlból 27 nem volt izoláltan
példányosítható), tehát a költségük nem látszott.

**Tanulság a következő szeletnek:** a halasztás-jelöltek rangsorát az izolált
mérés adhatja, a NYERESÉGET viszont csak a valódi indulás mérése.

## A költség NEM tűnik el, hanem ÁTHELYEZŐDIK — ez is mérve

| művelet | alap | #1612 |
|---|---:|---:|
| a Kollázs lap ELSŐ megnyitása (a panel látható és van mérete) | 151 ms | **1098 ms** |

A második megnyitás mindkettőnél azonnali (a panel megmarad).

**Miért elfogadható a csere:** az indulási költséget MINDEN felhasználó
megfizeti minden indításnál, a kollázs-lapot viszont a legtöbb munkamenet meg
sem nyitja; aki megnyitja, az szándékos műveletre vár ~1 s-ot. Az eredeti
Picasa 0–2 s alatt indul — a jegy mércéje az indulás.

**Amit szándékosan NEM tettünk:** `Loader.asynchronous: true`. Az elrejtené a
várakozást, de a panel „később" jelenne meg, és a kollázs-próbák egy része
azonnali jelenlétet vár (`_elem`) — a kockázat nagyobb, mint a nyereség.

## Ami ebből a jegyből MEGMARAD

Az `EditorPanel` (izoláltan 76,8 ms, `PhotoViewer.qml`) ugyanilyen jelölt, de
**nem `Loader`-rel** oldható: a `PhotoViewer.qml`-ben **104** kötés hivatkozik
rá közvetlenül, tehát a halasztás ott a kötések null-biztossá tételét jelenti.
Más kockázati osztály, önálló szelet.
