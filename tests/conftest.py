"""Gyökér-szintű őrök: a teszt nem nyúlhat a felhasználó VALÓDI mappáihoz
(#1054) és VALÓDI beállításaihoz (#2154).

A felismerő logika és az indoklás a `support/valodi_mappa_or.py`-ban él —
azért ott, hogy külön tesztelhető legyen (`tests/test_valodi_mappa_ore_1054.py`).

## Miért fixture és nem külön teszt

Külön teszt csak azt tudná megnézni, hogy ÉPPEN most mi van a mappában.
Ez a fixture MINDEN teszt köré odaáll, és megnevezi azt az egyet, amelyik
hozzányúlt — a szennyezést így ott fogjuk meg, ahol keletkezik.
"""

from __future__ import annotations

import pytest
from support.fixture_guards import user_folder_guard


@pytest.fixture(autouse=True)
def nem_szennyezi_a_felhasznaloi_mappat():
    """Elhasal, ha a teszt a valódi képmappában bármit létrehoz vagy módosít."""
    yield from user_folder_guard()


@pytest.fixture(scope="session", autouse=True)
def nem_nyul_a_valodi_beallitasokhoz(tmp_path_factory):
    """A `QSettings` alapértelmezett helye a teszt-futás idejére eldobható.

    Enélkül minden `QSettings("PicasaPy", "PicasaPy")` — és minden vezérlő,
    ami paraméter nélkül épül — a felhasználó ÉLES beállítás-fájlját
    (`~/.config/PicasaPy/PicasaPy.conf`) olvassa és írja. Két baj ebből:

    1. a tesztek eredménye **a gép állapotától függ** (a #2154 fejlesztése
       közben derült ki: a fanézet-tesztek elbuktak, mert a fejlesztő
       gépén be volt kapcsolva az „Egyszerűsített fanézet");
    2. a tesztfutás **átírhatja** a felhasználó beállításait.

    A `setPath` a natív (`.conf`) formátumra is átirányít, ezért a
    `QSettings()` minden alakja az ideiglenes mappába mutat.
    """
    from PySide6.QtCore import QSettings

    mappa = tmp_path_factory.mktemp("qsettings")
    eredeti = {}
    for formatum in (QSettings.Format.IniFormat, QSettings.Format.NativeFormat):
        for hatokor in (QSettings.Scope.UserScope, QSettings.Scope.SystemScope):
            QSettings.setPath(formatum, hatokor, str(mappa))
    yield
    # a helyreállítás szándékosan kimarad: a Qt nem ad visszakérdezést a
    # korábbi útvonalra, és a folyamat a futás végén megszűnik
    del eredeti


@pytest.fixture(autouse=True)
def tiszta_beallitasok(nem_nyul_a_valodi_beallitasokhoz):
    """Minden teszt ÜRES beállításokkal indul.

    A fenti átirányítás a felhasználót védi, de a tesztek egymástól nem
    izolálná: egy kapcsolót billentő teszt után a következő már a
    billentett értéket látná. A `#2154` fejlesztésekor pontosan ez
    bukott el — a „ne bocsáss jelet, ha nem változott" próbák elszálltak,
    mert egy korábbi teszt bekapcsolta ugyanazt a kapcsolót.

    ⚠️ MINDKÉT alakot üríteni kell. Tesztben a `QCoreApplication` szervezet-
    és alkalmazásneve üres, ezért a `QSettings()` egy MÁSIK fájlra mutat
    („Unknown Organization/…"), mint a `QSettings("PicasaPy", "PicasaPy")` —
    élesben a kettő ugyanaz, tesztben nem. A projekt mindkét alakot
    használja (`application.py` az elsőt, `controller.py` a másodikat).
    """
    from PySide6.QtCore import QSettings

    def _urit():
        QSettings().clear()
        QSettings("PicasaPy", "PicasaPy").clear()

    _urit()
    yield
    _urit()
