# Első lépések

## Mire van szükség

A PicasaPy Python 3.12 vagy újabb változatot igényel, és a Qt 6 grafikus
készletét használja. Linuxon és Windowson egyaránt fut; a fejlesztés
Linuxon folyik, a windowsos futtatás kísérleti.

### Linux (Debian, Raspberry Pi OS)

Rendszercsomagokból a legegyszerűbb:

```bash
sudo apt install \
  python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtqml \
  python3-pyside6.qtquick python3-pyside6.qtquickcontrols2 python3-pyside6.qtwidgets \
  python3-pyside6.qtmultimedia \
  python3-opencv python3-pil python3-piexif python3-watchdog \
  qml6-module-qtquick qml6-module-qtquick-controls \
  qml6-module-qtquick-layouts qml6-module-qtquick-templates qml6-module-qtquick-window \
  qml6-module-qtmultimedia
```

### Windows

```powershell
pip install PySide6 opencv-python pillow piexif watchdog
```

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
Súgó. A szürke tételek még nem működnek.

**Eszköztár** — bal oldalt az **Importálás** gomb és az új album gombja,
középen a szűrők (csillagozott képek, arcot tartalmazó képek, videók,
geocímkézett képek), jobbra a **Keresés** mező.

**Bal hasáb** — a mappák, albumok, gyűjtemények és projektek listája.
Innen választod ki, mit mutasson a rács.

**Rács** — a kiválasztott mappa vagy album indexképei. Egy képre kattintva
kijelölöd, duplán kattintva megnyitod a nézőben.

**Alsó sáv (képtálca)** — kék információs csík a kijelölésről, alatta a
tálca a kijelölt képekkel, és a műveletgombok: csillag, forgatás,
nagyítás, **Kollázs**, **Mozgófilm**, **Exportálás**, **Nyomtatás**,
**E-mail**.

**Jobb oldali fiók** — a Címkék, Emberek, Helyek és Tulajdonságok panel.
A Nézet menüből vagy a tálca gombjaival nyitható.

## Hova kerülnek az adataid

A PicasaPy **nem írja át a képeidet**. A szerkesztéseket, csillagokat és
feliratokat a képek mellé, a mappában lévő `.picasa.ini` fájlba menti —
ugyanabba, amit az eredeti Picasa is használ. Így a két program
párhuzamosan is használható ugyanazon a fotótáron.

A gyors kereséshez ezen kívül egy külön adatbázist és indexkép-gyorstárat
tart fenn; ezt bármikor újra fel lehet építeni. Részletek:
[Az adatbázis](features/adatbazis.md).
