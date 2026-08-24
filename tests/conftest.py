"""Gyökér-szintű őr: a teszt NEM nyúlhat a felhasználó VALÓDI mappáihoz (#1054).

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
