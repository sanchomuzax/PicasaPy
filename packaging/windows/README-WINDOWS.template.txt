PicasaPy __VERSION__ — Windows telepítési útmutató
====================================================

Ez a csomag NEM önálló .exe-t tartalmaz (ld. packaging/README.md a
döntés indoklásáért) — a PicasaPy Python-csomagként (.whl) települ, a
gépeden már meglévő (vagy most telepítendő) Python mellé.

Amit ehhez a mappa tartalmaz:
  - picasapy-__VERSION__-py3-none-any.whl   (a program maga)
  - install.bat                             (egykattintásos telepítő)
  - ez a fájl (README-WINDOWS.txt)

1. lépés — Python telepítése (ha még nincs)
--------------------------------------------
Töltsd le a Python 3.12 (vagy újabb) telepítőjét innen:
  https://www.python.org/downloads/windows/

Telepítéskor MINDENKÉPP pipáld be:
  [x] "Add python.exe to PATH"

2. lépés — PicasaPy telepítése
-------------------------------
Kattints duplán az install.bat fájlra ebben a mappában.
(Ha Windows figyelmeztetést ír ki „ismeretlen kiadó" miatt, válaszd a
"További információ" / "Futtatás mindenképp" lehetőséget — ez egy egyszerű
szövegfájl-szkript, nem futtatható program, tartalma bármikor
megnyitható/ellenőrizhető Jegyzettömbben.)

Ha inkább kézzel csinálnád, nyiss parancssort (cmd) ebben a mappában, és:
  py -3.12 -m pip install --upgrade pip
  py -3.12 -m pip install picasapy-__VERSION__-py3-none-any.whl

3. lépés — Indítás
-------------------
Egy ÚJ parancssor-ablakban (a telepítés után nyitottban lehet, hogy még
nem frissült a PATH):
  picasapy

Ha egy adott fotómappát szeretnél megnyitni:
  picasapy "C:\Users\Nev\Pictures\Nyaralas"

Mappa nélkül a program a korábban beállított figyelt mappákat nyitja meg
(a Picasa-paritású WatchedFolders.txt-ből).

Hibaelhárítás
-------------
- "'picasapy' is not recognized..." — zárd be és nyisd meg újra a
  parancssort (a PATH-frissítés csak új ablakban látszik), vagy jelentkezz
  ki/be Windowsból.
- Ha a "py" parancs nem ismert: a Python telepítőjét futtasd újra, és
  jelöld be az "Add python.exe to PATH" opciót (Modify/Repair móddal is
  pótolható telepítés után).
- Ez a build NEM lett Windowson kipróbálva automatikusan — ha valami nem
  működik, kérlek jelezd, hogy a következő verzióban javítható legyen.
