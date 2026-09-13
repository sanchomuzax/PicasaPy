# Első lépések

## Mire van szükség

A PicasaPy Linuxon és Windowson egyaránt fut. Windowson a telepítő
mindent magával hoz; Linuxon Python 3.12 vagy újabb és a Qt 6 grafikus
készlete kell hozzá.

### Linux (Debian, Raspberry Pi OS)

Rendszercsomagokból a legegyszerűbb:

```bash
sudo apt install \
  python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtqml \
  python3-pyside6.qtquick python3-pyside6.qtquickcontrols2 python3-pyside6.qtwidgets \
  python3-pyside6.qtmultimedia python3-pyside6.qtprintsupport \
  python3-opencv python3-pil python3-piexif python3-watchdog \
  qml6-module-qtquick qml6-module-qtquick-controls \
  qml6-module-qtquick-layouts qml6-module-qtquick-templates qml6-module-qtquick-window \
  qml6-module-qtmultimedia \
  libegl1 libgl1 libxkbcommon0 libpulse0
```

A `python3-pyside6.qtprintsupport` csomag a **nyomtatáshoz** kell, és
csak akkor, ha a Qt-t a rendszer csomagjaiból telepíted (a `pip`-es
változat magával hozza). A négy `lib…` csomag a grafikus megjelenítéshez
és a hanghoz kell; asztali rendszeren általában már fent van.

### Windows

**A rendes út a telepítő.** Minden kiadáshoz készül egy
`PicasaPy-Setup-<verzió>.exe` fájl: letöltöd, elindítod, kész. **Pythont
nem kell telepítened** — a program mindent magával hoz. A telepítő Start
menü bejegyzést és — ha kéred — asztali ikont készít, és a Programok és
szolgáltatások alól ugyanúgy eltávolítható, mint bármelyik más program.
A telepítőt a projekt letöltési oldalán (Releases) találod.

Ha inkább a forrásból futtatnád, ahhoz Python 3.12 vagy újabb kell, és a
csomagok:

```powershell
pip install PySide6 opencv-python pillow piexif watchdog
```

A windowsos futtatás kísérleti: a fejlesztés Linuxon folyik.

## Indítás

A program indításakor megadhatod, melyik mappákat nézze:

```bash
./picasapy ~/Kepek
```

Windowson:

```powershell
python picasapy C:\Kepek
```

Mappa megadása nélkül is elindul; a figyelt mappákat utólag is fel tudod
venni (lásd [Mappakezelő](features/mappakezelo.md)).

A programnak nincs parancssori felülete a megnyitandó mappákon kívül —
minden művelet az ablakban érhető el.

## Az első indítás

Az első indításkor a PicasaPy megkérdezi, hol keressen képeket. Két
lehetőség közül választhatsz:

- **Csak a Dokumentumok, a Képek és az Asztal átnézése** — gyors, és a
  legtöbb embernek elég.
- **Az egész számítógép átnézése** — ha több lemezen, szétszórt
  mappákban tartod a képeket.

A keresés **soha nem mozgat és nem másol fájlokat**. Csak megnézi, mi hol
van.

Ha korábban használtál Picasát ezen a gépen, a PicasaPy felajánlja, hogy
**átveszi a beállításait**: a figyelt mappák listáját. Az **Átvétel**
gombbal elfogadod, a **Most nem** gombbal kihagyod.

Amíg az első átnézés fut, a program már használható — a képek fokozatosan
jelennek meg.

## A főablak részei

Felülről lefelé:

**Menüsor** — Fájl, Szerkesztés, Nézet, Mappa, Kép, Létrehozás, Eszközök,
Súgó. A szürke tételek még nem működnek. Bármikor **F1**-et nyomva
előjön ez a súgó (lásd [A beépített súgó](features/sugo.md)).

**Eszköztár** — bal oldalt az **Importálás** gomb, az új album gombja, a
két kis nézetváltó gomb és mellettük egy **▾** gomb, ami a mappanézet
beállításait nyitja le; középen a szűrők (csillagozott képek, arcot
tartalmazó képek, videók, geocímkézett képek), jobbra a **Keresés** mező.
Keskeny ablakban a kis gombok és a szűrők elrejtőznek; az **Importálás**
gomb és a **Keresés** mező marad. A menüsorból ilyenkor is minden
elérhető.

**Bal hasáb** — a mappák, albumok, gyűjtemények és projektek listája.
Innen választod ki, mit mutasson a rács.

**Rács** — a kiválasztott mappa vagy album indexképei. Egy képre kattintva
kijelölöd, duplán kattintva megnyitod a nézőben.

**Alsó sáv (képtálca)** — kék információs csík a kijelölésről, alatta a
tálca a kijelölt képekkel, és a műveletgombok: csillag, forgatás,
nagyító, indexkép-méret, **Kollázs**, **Mozgófilm**, **Exportálás**,
**Nyomtatás**, **E-mail**. A nézőben ugyanebben a sávban van a
nagyítás három vezérlője.

**Jobb oldali fiók** — a Címkék, Emberek, Helyek és Tulajdonságok panel.
A Nézet menüből, a tálca gombjaival vagy a **Ctrl+0** billentyűvel
nyitható, és **becsúszva** nyílik ki, illetve zárul be. Van egy negyedik
út is: a fiók bal széle mentén — csukott fiók esetén az ablak jobb szélén
— egy **nem látszó, keskeny sáv** húzódik, amire kattintva a fiók
ki-be billen. **Egy** fiók van, közös fejléccel: a fejléc közepén annak
a panelnek a neve áll, amelyik éppen látszik. Balra a **Váltás a kis és
a nagy oldalpanel közt** gomb: a fiók keskeny és széles állás közt vált.
Jobbra az **Oldalpanel bezárása** gomb.

## Hova kerülnek az adataid

A PicasaPy **nem írja át a képeidet**. A szerkesztéseket, csillagokat és
feliratokat a képek mellé, a mappában lévő `.picasa.ini` fájlba menti —
ugyanabba, amit az eredeti Picasa is használ. Így a két program
párhuzamosan is használható ugyanazon a fotótáron.

A gyors kereséshez ezen kívül egy külön adatbázist és indexkép-gyorstárat
tart fenn; ezt bármikor újra fel lehet építeni. Részletek:
[Az adatbázis](features/adatbazis.md).
