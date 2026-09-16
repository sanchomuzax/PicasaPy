# Hova megy a QML-betöltés ~1250 ms-a? — két mérés, egy módszer kizárva (#3253)

**Gép:** RPi5, Python 3.13.5, Qt 6.8.2, 4 mag. **Mérés:** a program saját
indulási idővonala (`PICASAPY_STARTUP_TIMELINE=1`), meleg indulás, üres könyvtár.

## 1. A ~1250 ms tényleg a FA — nem a motor, nem az importok

A `Main.qml`-t lecseréltem egy csupasz `ApplicationWindow`-ra (egyetlen
`Theme`-hivatkozással, hogy a `PicasaPy` modul importja is megtörténjen), és
újramértem:

| változat | „QML betöltése (Main.qml)" |
|---|---:|
| a valódi fa | **~1276 ms** |
| **csupasz `ApplicationWindow`** | **24,5 ms** |

A motor létrehozása és az import-útvonalak külön szakaszban futnak (3–4 ms),
tehát a szakasz **egésze a fa példányosítása**. Ezt eddig nem mértük ki: a
#1612 a fordítás/példányosítás bontását adta, azt viszont nem, hogy a
példányosításból mennyi az ELEMEK létrehozása.

## 2. ⛔ A jegy javasolt módszere (időbélyeg a gyökér-gyermekeken) NEM működik

A `Main.qml` **62** gyökér-szintű gyermekébe beszúrtam egy nem rajzoló
jelölőt:

```qml
QtObject { Component.onCompleted: console.log("MARK|<név>|<sorszám>|" + Date.now()) }
```

A 62 jelölő **mind ugyanabba a ~15 ms-os ablakba** esett (a legnagyobb két
delta: `TrayBar` 10 ms, `MainToolbar` 5 ms, a többi 0):

```
jelek: 62 · a teljes jelölő-ablak: ~15 ms
```

**Miért:** a QML először **végig példányosítja** a fát, és a
`Component.onCompleted` visszahívások csak UTÁNA futnak le, egymás után,
gyorsan. A befejezési visszahívás tehát **semmilyen** per-elem létrehozási időt
nem hordoz — a jegy első „Kész, ha" pontja ebben a formában megvalósíthatatlan.

⚠️ A jelölők önmagukban nem drágák: a mért szakasz a jelölt fával is
1276 ms volt, tehát a mérés nem zavarta meg a mérendőt.

## 3. Ami ebből következik — a MEGMARADT módszerek

1. **Ablálás** (egy gyermeket kiveszünk, és mérjük a különbséget) — ez
   működik, de a gyermekekre mutató kötések miatt minden ablálás külön
   csonkolást kíván; a `PicasaMenuBar` például 2151 sor, és a `Main.qml`
   tizenöt tulajdonságot és jelet állít rajta.
2. **A Qt QML-profilere** (`-qmljsdebugger=file:…`) elemenkénti létrehozási
   időt ad — a nyomkövetés kiolvasásához viszont a `qmlprofiler` eszköz kell,
   ami **ezen a gépen nincs telepítve** (megnézve: sem `qmlprofiler`, sem
   `qmlprofiler6`).

⇒ A következő lépés vagy a `qmlprofiler` telepítése (egy csomag, és utána a
mérés elemenkénti és ismételhető), vagy célzott ablálás a három legnagyobb
izolált jelöltre (`PicasaMenuBar` 133,9 ms, `PhotoViewer` 103,8, `FolderPane`
76,9 — a #1612 izolált rangsorából, ami rangsornak jó, nyereségnek nem).

## Amit ez a lap NEM állít

Hogy melyik gyermek mennyibe kerül. Az 1. pont a szakasz EGÉSZÉT helyezi a
fára; a 2. pont egy módszert zár ki. A per-elem bontás nyitva marad.
