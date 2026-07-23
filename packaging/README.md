# PicasaPy — csomagolás (#4)

Ez a könyvtár a PicasaPy három telepítési módját fedi le:

1. **pip/pipx** — a `pyproject.toml` build-rendszere adja (nincs itt külön
   szkript, ld. lentebb).
2. **Debian-csomag (.deb)** RPi/Debian/Ubuntu célra — `build_deb.sh`.
3. **Windows-zip** — `build_windows_zip.sh`.

Egyik módszer sem igényel önálló `.exe`-t vagy embeddable Python-bundle-t
(pragmatikus MVP-döntés, ld. az egyes szakaszok indoklását) — mindegyik a
projekt `.whl`-jét telepíti a felhasználó gépén futó Python mellé.

A `pyproject.toml`-ban a build-rendszer és a `[project.scripts]` belépési
pont e feladat része (`picasapy` parancs → `picasapy.app.__main__:main`); a
`version` mezőhöz itt nem nyúltunk — azt az integrátor session emeli.

---

## 1. pip / pipx telepítés (Linux)

### Build

```sh
python3.12 -m pip install --upgrade pip build
python3.12 -m build --wheel          # dist/picasapy-<verzió>-py3-none-any.whl
python3.12 -m build --sdist          # dist/picasapy-<verzió>.tar.gz
```

A wheel tartalmazza a futáshoz szükséges nem-Python fájlokat is (QML,
ikonok, `.qm` fordítás) — ld. `pyproject.toml`
`[tool.setuptools.package-data]`.

### Telepítés

```sh
pip install dist/picasapy-<verzió>-py3-none-any.whl
# vagy elszigetelt környezetben:
pipx install dist/picasapy-<verzió>-py3-none-any.whl
```

A `picasapy` parancs ezután a `PATH`-on elérhető, és a futáshoz szükséges
függőségeket (PySide6, opencv-python-headless, pillow, piexif, watchdog)
pip/pipx automatikusan feltelepíti.

### Amit ténylegesen kipróbáltunk (2026-07-23, konténerben)

1. `python3.12 -m venv build-venv && build-venv/bin/pip install build`
2. `build-venv/bin/python3 -m build --wheel` → sikeres,
   `picasapy-0.4.35-py3-none-any.whl` (a `dist-info` tartalmazza a
   `[console_scripts] picasapy = picasapy.app.__main__:main` bejegyzést).
3. `python3.12 -m build --sdist` → sikeres, `.tar.gz` is legyártható.
4. Friss venv (`python3.12 -m venv install-venv`), majd
   `pip install picasapy-0.4.35-py3-none-any.whl` → az ÖSSZES függőség
   (PySide6, PySide6_Essentials/Addons, opencv-python-headless, numpy,
   pillow, piexif, watchdog) automatikusan feltelepült a PyPI-ról.
5. **Füstpróba** — mivel a PicasaPy egy GUI-alkalmazás (nincs saját
   `--help`/`--version` argumentum-feldolgozása, a parancssori argumentum
   fotómappa-gyökérként értelmeződik), a "füstpróba" itt azt jelentette,
   hogy a telepített `picasapy` parancsot **ténylegesen elindítottuk**
   headless módban, egy üres mappával, majd pár másodperc után
   megszakítottuk:

   ```sh
   export QT_QPA_PLATFORM=offscreen
   export XDG_DATA_HOME=/tmp/xdg-data XDG_CONFIG_HOME=/tmp/xdg-config XDG_CACHE_HOME=/tmp/xdg-cache
   timeout -s TERM 6 picasapy /tmp/ures-mappa
   ```

   Eredmény: a folyamatot a `timeout` várhatóan megszakította
   (kilépőkód 124 — ez NEM hiba, hanem a Qt-eseményhurok normál futása),
   **stdout/stderr üres volt** (nincs traceback, nincs import-hiba), és az
   `XDG_DATA_HOME/picasapy/index.db` + a `QLockFile` ténylegesen létrejött,
   a QML-fájlok lefordultak (`qmlcache/*.qmlc`) — ez igazolja, hogy a
   telepített csomag a teljes GUI-alkalmazást el tudta indítani headless
   környezetben is.
6. Emiatt **nem ütköztünk olyan headless korlátba**, ami miatt a
   füstpróbát dokumentálni kellene mint "nem próbálható ki" — a teljes
   indítási lánc (import → Qt-app → index → QML-betöltés) lefutott.

Korlát: nincs `picasapy --version` / `--help` parancssori kapcsoló (a
`run()`/`__main__.py` jelenlegi viselkedése szerint minden argumentum
fotómappa-gyökérként értelmeződik) — ezt **nem** módosítottuk, mert az
`src/picasapy/**` módosítása ehhez a feladathoz csak a
`__main__.py`-beli minimális `main()` belépőpontra volt engedélyezve.
Ha verzió-lekérdező kapcsoló kell, az külön issue.

---

## 2. Debian-csomag (.deb)

### Miért nem "natív" python3-dpkg-függőség?

A PicasaPy nehéz, architektúra-függő függőségeket használ (PySide6,
OpenCV, numpy), amik Debian/RPi-n gyakran nincsenek (megfelelő verzióban)
apt-csomagként. A pragmatikus MVP-megoldás: a `.deb` a `picasapy` `.whl`-t
hordozza, telepítéskor pedig egy **dedikált virtuális környezetbe**
(`/opt/picasapy/venv`) telepíti a függőségeivel együtt a PyPI-ról — ehhez
telepítéskor internetkapcsolat kell.

### Build

```sh
./packaging/build_deb.sh
# kimenet: packaging/dist/picasapy_<verzió>_all.deb
```

A szkript saját, eldobható venv-ben építi a wheelt (a rendszer Pythonja
sok Debian/Ubuntu-n "externally managed", PEP 668), majd `dpkg-deb`-bel
csomagolja a wheelt + a desktop-fájlt (`debian/picasapy.desktop`) + az
ikont (`src/picasapy/app/assets/icon.png`) + a telepítő-szkripteket
(`debian/postinst`, `debian/postrm`).

### Telepítés

```sh
sudo apt install ./packaging/dist/picasapy_<verzió>_all.deb   # feloldja a függőségeket is
# vagy
sudo dpkg -i packaging/dist/picasapy_<verzió>_all.deb          # majd: sudo apt --fix-broken install
```

### Amit ténylegesen kipróbáltunk (2026-07-23, konténerben, Ubuntu 24.04)

1. `./packaging/build_deb.sh` → sikeres `.deb` (443 KB), `dpkg-deb --info`
   ellenőrizve (control-mezők, postinst/postrm jelen).
2. Első `dpkg -i` próba **elkapta**, hogy a `python3-venv` függőség
   hiányzott (`Depends` helyesen működött — dpkg megtagadta a
   konfigurálást, amíg nincs telepítve). `apt-get install -y ./…deb`-bel
   megismételve a hiányzó függőség automatikusan települt.
3. Ez felfedte egy **valódi hibát**: a `postinst` eredetileg a puszta
   `python3` parancsot hívta, ami ezen a rendszeren Python **3.11**-re
   mutat (nem 3.12+), így a venv-be telepítés
   `requires-python >=3.12` hibával elbukott. **Javítottuk**: a
   `postinst` mostantól explicit megkeresi a legújabb elérhető
   `python3.13`/`python3.12` végrehajtható fájlt, és csak Python 3.12+
   esetén hoz létre venv-et (különben érthető hibaüzenettel leáll).
4. `python3-venv` telepítése után **teljes, sikeres install**:
   `apt-get install -y ./picasapy_0.4.35_all.deb` → a `postinst` létrehozta
   a `/opt/picasapy/venv`-et **Python 3.13**-mal, telepítette a wheelt +
   az összes függőséget a PyPI-ról, és a `/usr/bin/picasapy` szimlinket.
5. **Füstpróba**: a telepített `picasapy` paranccsal ugyanazt a headless
   indítási tesztet futtattuk, mint a pip-es útnál (1. szakasz, 5. pont) —
   ugyanaz a siker: `index.db` létrejött, nincs hibakimenet.
6. Takarítás: `apt-get remove --purge -y picasapy` → a `postrm` eltávolította
   a `/opt/picasapy/venv`-et és a szimlinket; a rendszert az eredeti,
   picasapy-mentes állapotba állítottuk vissza.

**Ismert korlát**: a fenti próba `amd64` konténerben történt, nem a
célplatform (RPi5, `arm64`) hardveren — mivel a csomag `Architecture: all`
(tisztán Python, a bináris függőségeket a `pip install` tölti le a
megfelelő platform szerint telepítéskor), ez elvben nem jelent problémát,
de a **tényleges RPi5-ös első telepítés felhasználói kézi próbát igényel**
(a `pip`/PyPI-n elérhető `opencv-python-headless`/`PySide6` wheel-ek arm64
lefedettsége eltérhet az amd64-től).

---

## 3. Windows-zip

### Miért nem embeddable Python / .exe?

Egy önálló `.exe` (pl. PyInstaller/Nuitka) vagy embeddable-Python-bundle
buildelése és **tesztelése** Windows nélkül (ez a konténer Linux) nem
megbízható — a build maga is Windows-specifikus lépéseket igényelne
(DLL-ek, natív Qt-pluginok). A pragmatikus MVP-megoldás ezért: a `.whl`-t
egy kézi telepítési útmutatóval (`README-WINDOWS.txt`) és egy
egykattintásos `install.bat`-tal zip-eljük össze — a felhasználó a saját,
python.org-ról telepített Pythonja mellé telepíti.

### Build

```sh
./packaging/build_windows_zip.sh
# kimenet: packaging/dist/picasapy-windows-<verzió>.zip
```

A zip tartalma:
- `picasapy-<verzió>-py3-none-any.whl`
- `install.bat` (egykattintásos telepítő — `pip install` a mellékelt
  wheel-re, `py -3.12` / `py -3` inditóval)
- `README-WINDOWS.txt` (magyar, lépésről lépésre — Python telepítése,
  `install.bat` futtatása vagy kézi `pip install`, indítás, hibaelhárítás)

### Amit ténylegesen kipróbáltunk (konténerben)

- A zip **buildelése** sikeres, a tartalma ellenőrizve (`unzip -l`), az
  `install.bat` CRLF sortöréssel készül (Windows-konvenció).
- Az `install.bat` **Windows alatti tényleges futtatása** — **felhasználói
  kézi próba szükséges**: ehhez Windows-gép kell, ami ebben a Linux-
  konténerben nem áll rendelkezésre. Javasolt manuális próba:
  1. Csomagold ki a zip-et egy tetszőleges mappába.
  2. Kattints duplán az `install.bat`-ra (vagy futtasd a
     `README-WINDOWS.txt`-ben leírt kézi `pip install` lépést).
  3. Új parancssorban: `picasapy` — induljon el az alkalmazás ablaka.
  4. Ha bármi elakad, a `README-WINDOWS.txt` hibaelhárítás szakasza segít
     (PATH-frissítés, `py` launcher hiánya stb.).

---

## 4. Release-workflow (`.github/workflows/package.yml`)

Külön workflow-fájl — a meglévő `release.yml`-hez **nem nyúltunk**. A
`release.yml` minden main-push után lefut, és ha a `pyproject.toml`
verziójához még nincs GitHub Release, létrehozza (`gh release create`,
alapból **publikált** release). A `package.yml` erre a
`release: published` eseményre iratkozik fel:

1. Kicsomagolja a repót, Python 3.12-t állít be.
2. `python -m build` → wheel + sdist a `dist/`-be.
3. `./packaging/build_deb.sh` → `.deb` a `packaging/dist/`-be.
4. `./packaging/build_windows_zip.sh` → Windows-zip a `packaging/dist/`-be.
5. `gh release upload <tag> …` — a négy artefaktumot feltölti az adott
   release-hez asset gyanánt.

Kézi újrafuttatás: `workflow_dispatch`, opcionális `tag` inputtal (arra az
esetre, ha a `release published` esemény lemaradt, vagy egy régebbi
release-hez kell utólag csomagot generálni).

**CI-realitás**: a `.deb`/zip build ubuntu-latest runneren pár másodperc
(tiszta Python-csomagolás, nincs fordítás) — ezért belefért a
release-workflow-ba, nem csak "ha reálisan megy" opcionális lépésként.

---

## Fájlok

```
packaging/
├── README.md                          — ez a fájl
├── .gitignore                         — .build/ és dist/ kizárása (build-artifact)
├── build_deb.sh                       — .deb build szkript
├── build_windows_zip.sh               — Windows-zip build szkript
├── debian/
│   ├── control.template               — dpkg control (__VERSION__ helyettesítve buildkor)
│   ├── picasapy.desktop               — desktop-entry (Exec=picasapy)
│   ├── postinst                       — venv létrehozása + wheel telepítése
│   └── postrm                         — venv + szimlink eltávolítása
└── windows/
    ├── install.bat.template           — egykattintásos telepítő (CRLF)
    └── README-WINDOWS.template.txt    — kézi telepítési útmutató (magyar)
```

## Ismert korlátok (összefoglalva)

- Nincs önálló `.exe`/embeddable-Python Windows-csomag — csak `.whl` +
  kézi/`.bat`-os `pip install`. Ha ez a jövőben nem elég (pl. a
  végfelhasználó ne kelljen Pythont telepítenie), az külön issue-ként
  bővíthető (PyInstaller/Nuitka Windows-runneren).
- A `.deb` telepítéskor internetkapcsolatot igényel (PyPI-ról húzza a
  függőségeket) — teljesen offline `.deb` (minden függőség bundle-özve)
  jelentősen nagyobb csomagméretet és bonyolultabb buildet jelentene.
- A `.deb` tényleges RPi5 (arm64) telepítése nincs kipróbálva ebben a
  (amd64) konténerben — felhasználói kézi próbát igényel.
- A Windows-zip tényleges Windows alatti kipróbálása felhasználói kézi
  próbát igényel (nincs Windows ebben a környezetben).
- Nincs `picasapy --version`/`--help` parancssori kapcsoló — a jelenlegi
  argumentum-feldolgozás minden argumentumot fotómappa-gyökérnek vesz.
