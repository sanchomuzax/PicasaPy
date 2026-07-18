<p align="center">
  <img src="docs/assets/logo-card.svg" alt="PicasaPy logó" width="181">
</p>

<p align="center"><em>Google Picasa szellemében, modern Python/Qt alapokon.</em></p>

<p align="center">
  <a href="https://github.com/sanchomuzax/PicasaPy/actions/workflows/ci.yml"><img src="https://github.com/sanchomuzax/PicasaPy/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0-blue.svg" alt="License: GPL-3.0"></a>
  <img src="https://img.shields.io/badge/version-0.2.0-orange.svg" alt="Version 0.2.0">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue.svg" alt="Python 3.12+">
</p>

## About

PicasaPy is an open-source successor to **Google Picasa 3.x**, the photo manager and light editor that Google discontinued in 2016. It is written in Python with a PySide6 (Qt 6) / QML interface, and aims to be a drop-in replacement: it reads and writes the same `.picasa.ini` sidecar format Picasa 3.x used, so it can be used side-by-side with an existing Picasa photo library without breaking anything. Development is Linux-first (built and tested on a Raspberry Pi 5) and licensed under **GPL-3.0**. The project is in **early development** (0.1.x), well before a 1.0 release — expect rough edges and missing features.

---

## Mi ez?

A PicasaPy a **Google Picasa** fotókezelő és -szerkesztő program nyílt forráskódú újraírása Python nyelven. A Picasát a Google 2016-ban kivezette, de sokan a mai napig használják gyors böngészés, csillagozás, feliratozás és nem-destruktív szerkesztés miatt. A PicasaPy célja egy modern, keresztplatformos utód, amely **kétirányúan kompatibilis** a Picasa `.picasa.ini` formátumával — így a régi és az új szoftver párhuzamosan, ugyanazon a fotótáron használható.

## Fő képességek

A projekt jelenlegi (MVP, 1. fázis) állapotában a következők működnek:

- **`.picasa.ini` byte-egzakt round-trip parser** — amit a PicasaPy nem ismer fel egy `.picasa.ini` fájlban, azt változtatás nélkül visszaírja.
- **Mappa-bejárás (scanner)** a támogatott képformátumokra, watched-folders kezeléssel.
- **SQLite + FTS5 alapú index** a gyors kereséshez és szűréshez.
- **EXIF/IPTC metaadat-olvasás**, valamint **IPTC felirat (caption) írás** JPEG fájlokba.
- **Miniatűr-gyorsítótár (thumbnail cache)** OpenCV-vel.
- **PySide6/QML fő ablak**, Picasa-hű dizájnnal (rács nézet, csillagsáv, tálca).
- **Magyar lokalizáció.**
- **Egyképes néző (viewer)** léptetéssel.
- **Csillagozás, nem-destruktív forgatás, felirat-szerkesztés.**
- **Többes kijelölés, szűrés, keresés.**

Amit **még nem** tud: szerkesztő eszközök (2. fázis), arcfelismerés (3. fázis), PMP/db3 import (tervezett, de még nem implementált).

## Állapot

⚠️ **Korai fejlesztési fázisban** van (verzió: `0.2.0`), messze az 1.0-tól. Az aktuális cél az **MVP 1. fázis**: kezelő (böngészés, rendezés, csillagozás, szűrés) + néző. A formátum-kompatibilitás és az alapvető könyvtárkezelés már működik, de az API és a fájlformátum-részletek még változhatnak.

## Telepítés és futtatás Linuxon

Debian/Raspberry Pi OS (trixie) rendszercsomagokkal ajánlott, mert a PySide6 és az OpenCV apt-csomagjai jól működnek RPi5-ön:

```bash
sudo apt install \
  python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtqml \
  python3-pyside6.qtquick python3-pyside6.qtquickcontrols2 python3-pyside6.qtwidgets \
  python3-opencv python3-pil python3-piexif python3-watchdog \
  qml6-module-qtquick qml6-module-qtquick-controls \
  qml6-module-qtquick-layouts qml6-module-qtquick-templates qml6-module-qtquick-window

git clone https://github.com/sanchomuzax/PicasaPy.git
cd PicasaPy
./picasapy ~/Kepek
```

## Futtatás Windowson

Windows-os támogatás **kísérleti** — a fejlesztés Linuxon (RPi5) folyik, de a tesztkészletet a CI Windowson is futtatja.

1. Telepíts Python 3.12+-t a [python.org](https://www.python.org/) oldalról.
2. Telepítsd a függőségeket:

   ```powershell
   pip install PySide6 opencv-python pillow piexif watchdog
   ```
3. Klónozd a repót, majd indítsd:

   ```powershell
   git clone https://github.com/sanchomuzax/PicasaPy.git
   cd PicasaPy
   python picasapy C:\Kepek
   ```

## Tesztek futtatása

```bash
pip install pytest pytest-cov
python3 -m pytest
```

## Architektúra röviden

- `src/picasapy/ini/` — a `.picasa.ini` fájlformátum parsere és írója (round-trip elv).
- `src/picasapy/scanner/` — mappa-bejárás, figyelt mappák, támogatott fájltípusok.
- `src/picasapy/index/` — SQLite + FTS5 index, sémakezelés, szinkronizáció.
- `src/picasapy/metadata/` — EXIF/IPTC olvasás és IPTC felirat-írás.
- `src/picasapy/thumbs/` — miniatűr-gyorsítótár OpenCV-vel.
- `src/picasapy/app/` — PySide6/QML alkalmazás (kontroller, modellek, QML nézetek, lokalizáció).

## Kompatibilitás

- **`.picasa.ini`**: csillag, forgatás, felirat és szűrők (filters mátrix) round-trip olvasása és írása, Picasa 3.x formátumban.
- **IPTC felirat**: JPEG fájlokba beírt IPTC caption mező kezelése.
- **PMP/db3**: import a Picasa saját adatbázisából — **tervezett**, jelenleg még nincs implementálva.

## Verziózás

A projekt [Semantic Versioning](https://semver.org/)-t követ. A `0.x` verziók **instabilak**, a köztük lévő API- és formátum-változások nincsenek garantálva visszafelé kompatibilisnek. Lásd a [Releases](https://github.com/sanchomuzax/PicasaPy/releases) oldalt.

## Licenc

[GPL-3.0](LICENSE) — szabadon megosztható és módosítható; a GPL-es referencia-repókból portolt kódrészletek attribúcióval szerepelnek.

## Köszönet

Köszönet az eredeti **Google Picasa** csapatának a program megalkotásáért — a PicasaPy dizájn-referenciája a **Picasa 3.9**.
