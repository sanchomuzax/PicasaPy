# Közreműködés

Köszönjük az érdeklődést! A PicasaPy GPL-3.0 licencű, a fejlesztés a
`main` ágra érkező pull requesteken keresztül folyik.

## Fejlesztői környezet

```sh
# Python-csomagok: futásidejű + fejlesztői eszközök
python -m pip install $(python scripts/print_dependencies.py --all)

# Linuxon a Qt rendszer-libjei
sudo apt-get install -y $(python scripts/print_dependencies.py --apt)
```

A csomagok listáját **ne írd ki kézzel**: a Python-oldal igazságforrása a
`pyproject.toml`, a rendszercsomagoké a `packaging/qt-runtime-deps.txt`, és
minden telepítő (CI, session-hook, ez a leírás) ezeket kérdezi le. A listák
korábban négy helyen éltek párhuzamosan, és el is csúsztak egymástól; egy
őr-teszt (`tests/test_kornyezet_szinkron.py`) most már elkapja, ha valaki
tételes listát ír vissza valamelyik telepítőbe.

Fej nélküli (CI, konténer) környezetben: `export QT_QPA_PLATFORM=offscreen`.

## Tesztelés

```sh
python scripts/run_tests.py        # a TELJES készlet — push előtt kötelező
python scripts/run_tests.py --cov  # lefedettséggel
ruff check src/ tests/ scripts/    # lint
```

Az `on<Jelzés>` / `.connect()` fogadó nélkül maradt Qt-jelzéseket külön őr
figyeli — ez a hibaosztály háromszor ment ki kiadásba (#985, #989, #1001),
mindannyiszor zöld tesztek mellett:

```sh
python scripts/check_dead_signals.py         # ugyanaz, amit a CI futtat
python scripts/check_dead_signals.py --list  # a mai néma jelzések
```

Ha új néma jelzést jelez: **kösd be** (QML-kezelő vagy `.connect`), vagy
**töröld** a jelzést. A `scripts/dead_signals_baseline.txt` a bevezetéskori
állapotot rögzíti, tételes indoklással — az a lista csak **rövidülhet**.

A tesztkészletet **a `scripts/run_tests.py`-vel futtasd**, ne közvetlenül a
`pytest`-tel: a Qt/QML-tesztek egy processzben GIL-deadlockba ragadhatnak,
ezért a szkript darabolva futtat. Gyors, célzott ellenőrzéshez a nem-Qt rész
futtatható egyben: `pytest tests --ignore=tests/app -q`.

QML-viselkedés változásához funkcionális teszt kötelező (minta:
`tests/app/test_qml_functional.py`).

### A platformfüggő teszt MONDJA KI a platformját

Ha egy teszt állítása **egy platformra igaz**, a teszt mondja ki, melyikre
— ne hallgatólagosan feltételezze a fejlesztői gépet. Ez a hibaosztály
egyetlen napon **négyszer** vitt el egy-egy kört (#1076, #1182, #1206,
#1167): mindannyiszor a TERMÉK volt helyes, és a Windows-lábon a teszt
bukott el — a natív, helyes viselkedésen. A bukás ráadásul félrevezet: úgy
néz ki, mintha a helyes viselkedés lenne a hiba.

Ezért a platform-lekérdezés minden modulban egy **helyettesíthető
fogantyú**, mindig ugyanazon a néven:

```python
def _platform() -> str:
    # A futó platform — külön függvény, hogy a teszt helyettesíthesse.
    return sys.platform
```

A teszt ezt a fogantyút rögzíti:

```python
monkeypatch.setattr(modul, "_platform", lambda: "win32")
```

Három szabály, mindhármat őr figyeli (`tests/test_platform_seam_1217.py`):

1. **Elágazásban ne kérdezd közvetlenül a platformot.** Sem `sys.platform`,
   sem `os.name`, sem `platform.system()` — mindhárom ugyanaz a döntés,
   csak más szótárral. (Nevesített `platform=` paraméter is szabályos
   fogantyú; az `application.py` azt használja.)
2. **Egy fogantyú, egy név.** `_platform` — és a név ne jelentsen mást,
   modul-aliasnak sem használható.
3. **A teszt a fogantyút cserélje, ne a globális modult.** A
   `monkeypatch.setattr("…modul.sys.platform", "linux")` alak **nem** a
   modult módosítja: a `modul.sys` MAGA a globális `sys`, tehát a rögzítés
   a teszt teljes idejére minden más modulra is hat. Ez már okozott is
   elszabaduló hibát — ld. a `test_fileops_controller.py` `TestRevealPhoto`
   osztályának docstringjét.

⚠️ **A `skipif` nem helyettesíti a rögzítést**: a kihagyott teszt a másik
platformon nem mér semmit, a rögzített viszont **mindkét** CI-lábon fut, és
azt méri, amit állít. `skipif` ott indokolt, ahol a viselkedés tényleg a
valódi oprendszertől függ, nem egy helyettesíthető függvénytől (szimbolikus
link létrehozása, `chmod`-szemantika, `os.geteuid()`) — ilyenkor a `reason`
mondja meg, melyik oprendszer-képesség hiányzik.

## Kódstílus

- **TDD**: előbb a bukó teszt, utána a kód.
- Magyar kommentek és docstringek, a projekt eddigi konvenciója szerint.
- Immutabilitás; sok kicsi fájl (200–400 sor tipikus, 800 a felső határ).
- Színt csak a `Theme.qml` tokenjeiből használj — hardkódolt szín nem megy át.
- Commit-formátum: `feat|fix|docs|test|chore: leírás` (magyarul), a
  vonatkozó issue számával (`#N`).

## A jegy címe

A cím a jegy **legtartósabb** része: bekerül a commit-üzenetbe, a PR-címbe, a
változásnaplóba és — ami a legfontosabb — a **keresésbe**. Ezért leíró, és
csak leíró.

**A kívánt alak:** *[érintett funkció] + alany + állítmány, és látszódjon a
honnan-hová.*

| | |
|---|---|
| Hiba | „A Klipek fül a kollázs csomópontjait sorolja fel a mappa képei helyett" |
| Fejlesztés | „Az Exportálás mappába párbeszéd az eredeti Picasa elrendezését követi" |

- **Az érintett funkció neve nem díszítés.** Fél év múlva senki nem a jegy
  számára emlékszik, hanem a „kollázs" vagy a „hisztogram" szóra keres rá.
- **Állapot és prioritás nem megy a címbe** — arra címke van (`P0`–`P4`,
  `blocked`, `in-progress`, `ready`, `felhasználóra-vár`). A címke változik,
  a cím marad: a kettőt összekötni garantált elavulás.
- **A megoldás sem megy a címbe.** Az is vélemény, ami munka közben változik;
  a cím a *mit* rögzítse, ne a *hogyant*.
- **A semmitmondó cím sem jó.** A „Hisztogram" véleménymentes és
  használhatatlan — a cím legyen leíró ÉS konkrét.
- A `fix:`/`feat:` előtag a **commité és a PR-é**, nem a jegyé.

Ezt a `scripts/hooks/jegycim_or.py` be is tartatja: a jegynyitást
visszautasítja, ha a cím prioritást, állapotot, commit-előtagot vagy
nagybetűs nyomatékot hordoz. Az alany-állítmányt és a funkciónevet nem méri
— azt a hibaüzenet kéri, mert a téves blokk drágább, mint egy gyengébb cím.

## Pull request

- A `main` védett: csak PR-en át, zöld CI-val kerülhet bele kód. A mérce az
  **ubuntu** CI-láb; a Windows-láb kísérleti, nem blokkol.
- Egy PR egy témát vigyen, és hivatkozzon a hozzá tartozó issue-ra.
- A feladatlista a GitHub Issues; a felvehető jegyek címkéje `ready`.

## Igazságforrások

- Dizájn: `docs/specs/design-guide.md`. Az alkalmazás **mindig világos** —
  a sötét téma későbbi fázis.
- `.picasa.ini`-írás kizárólag a meglévő round-trip rétegen át
  (`picasapy.ini`), atomikus mentéssel és backuppal. Amit nem értünk
  értelmezetten, azt bitre pontosan meg kell őrizni.
- Formátum-specifikációk: `docs/specs/`.
