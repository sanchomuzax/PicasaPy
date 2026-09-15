"""A busy-nyilvántartás `begin()`/`end()`-je TÚLÉLI a törölt jelzésforrást (#1457).

## A mérés, ami ezt kikényszerítette

A #3130 naplózó ága megmondta, MELYIK kivétel öli a folyamatot — eddig a
fatális abort elvitte magával a szövegét. A 2026-09-15-i CI-körökből
(`34927349614` ubuntu 3/4, és rajta kívül még tizenöt körben ugyanez):

```
7 passed in 1.54s
Exception in thread picasapy-sync-dirty:
Traceback (most recent call last):
  File ".../threading.py", line 1012, in run
    self._target(*self._args, **self._kwargs)
  File ".../picasapy/app/worker_thread.py", line 277, in _run
    registry.end()
  File ".../picasapy/app/busy_registry.py", line 115, in end
    self._endRequested.emit()
RuntimeError: Signal source has been deleted
```

## Amit ez kimond

1. a kivétel **nem** a munkafüggvényben keletkezik, hanem a `_run`
   `finally`-ágában — tehát a #3130 `try`/`except`-je **nem éri el**;
2. a `QObject` C++ oldala addigra megszűnt (a teszt-teardown lebontja a
   `QApplication`-t, ami minden gyermekét törli), a Python-példány viszont
   él (`reset_app_busy_registry` szándékosan tartja életben, #519/#430);
3. ilyenkor a `Signal.emit()` **`RuntimeError`-t dob**.

⇒ A javítás helye a FORRÁS: a `begin()`/`end()` a törölt jelzésforrást
nyugtázza és visszatér. Ez nem elnémítás — ha a C++ objektum megszűnt,
nincs többé felület, amit a jelzés frissíthetne; a számláló pedig a
példánnyal együtt szűnt meg.

⚠️ Ez a lap **nem** a `_run` `finally`-ágát javítja körbe-`try`-jal: az
elfedné a többi, valódi hibát is. A `begin()`/`end()` szerződése lesz
bővebb — kimondottan csak erre az egy, mért esetre.
"""

from __future__ import annotations

import pytest
import shiboken6

from picasapy.app.busy_registry import AppBusyRegistry


@pytest.fixture()
def torolt_regisztratum(qt_app):
    """Egy `AppBusyRegistry`, aminek a C++ oldalát eldobtuk — pontosan az
    az állapot, amibe a háttérszál a teszt-teardown után beleszalad."""
    registry = AppBusyRegistry()
    shiboken6.delete(registry)
    assert not shiboken6.isValid(registry), "a C++ oldalnak meg kell szűnnie"
    return registry


def test_end_torolt_forrason_nem_dob(torolt_regisztratum):
    """A mért összeomlás-lánc első láncszeme: `end()` a törölt forráson."""
    torolt_regisztratum.end()


def test_begin_torolt_forrason_nem_dob(torolt_regisztratum):
    """A párja: a `begin()` ugyanígy a `_beginRequested`-et emitálja."""
    torolt_regisztratum.begin()


def test_el_regisztratumon_tovabbra_is_szamol(qt_app):
    """Pozitív kontroll: a nyugtázás CSAK a törölt forrásra vonatkozik —
    az élő példány számlálója továbbra is működik."""
    registry = AppBusyRegistry()
    registry.begin()
    registry.begin()
    assert registry.activeCount == 2
    registry.end()
    assert registry.activeCount == 1
