# Közreműködés

Köszönjük az érdeklődést! A PicasaPy GPL-3.0 licencű, a fejlesztés a
`main` ágra érkező pull requesteken keresztül folyik.

## Fejlesztői környezet

```sh
python -m pip install PySide6 opencv-python-headless pillow piexif watchdog pytest pytest-cov
```

Linuxon a Qt-hez kellenek még: `libegl1`, `libgl1`, `libxkbcommon0`.
Fej nélküli (CI, konténer) környezetben: `export QT_QPA_PLATFORM=offscreen`.

## Tesztelés

```sh
python scripts/run_tests.py        # a TELJES készlet — push előtt kötelező
python scripts/run_tests.py --cov  # lefedettséggel
ruff check src/ tests/             # lint
```

A tesztkészletet **a `scripts/run_tests.py`-vel futtasd**, ne közvetlenül a
`pytest`-tel: a Qt/QML-tesztek egy processzben GIL-deadlockba ragadhatnak,
ezért a szkript darabolva futtat. Gyors, célzott ellenőrzéshez a nem-Qt rész
futtatható egyben: `pytest tests --ignore=tests/app -q`.

QML-viselkedés változásához funkcionális teszt kötelező (minta:
`tests/app/test_qml_functional.py`).

## Kódstílus

- **TDD**: előbb a bukó teszt, utána a kód.
- Magyar kommentek és docstringek, a projekt eddigi konvenciója szerint.
- Immutabilitás; sok kicsi fájl (200–400 sor tipikus, 800 a felső határ).
- Színt csak a `Theme.qml` tokenjeiből használj — hardkódolt szín nem megy át.
- Commit-formátum: `feat|fix|docs|test|chore: leírás` (magyarul), a
  vonatkozó issue számával (`#N`).

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
