"""#695: a szerkesztő MINDEN effektneve feloldható a kanonikus regiszterben.

Ha a felületre olyan effektnév kerül, amit a `filterdesc-registry.md` nem
ismer, akkor a `filters=` láncba egy olyan bejegyzés kerülne, amit az
eredeti Picasa NÉMÁN elejt (#685) — a felhasználó szerkesztése a windowsos
Picasában eltűnne. Ez a teszt ezt a rést zárja: az `edit_controller`
kézzel karbantartott `_EFFECT_INI_NAMES` táblájának egyeznie kell a
regiszterrel.
"""

import pytest

from picasapy.app.edit_controller import (
    _EFFECT_INI_NAMES,
    _EFFECT_NAMES,
    _LEGACY_EFFECT_NAMES,
    _ONE_SHOT_NAMES,
    _TOGGLE_NAMES,
)
from picasapy.ini.filter_registry import canonical_filter_name

_MINDEN_UI_NEV = tuple(
    sorted(
        set(_EFFECT_NAMES)
        | set(_LEGACY_EFFECT_NAMES)
        | set(_ONE_SHOT_NAMES)
        | set(_TOGGLE_NAMES)
    )
)


@pytest.mark.parametrize("kulcs", _MINDEN_UI_NEV)
def test_minden_ui_effekt_kanonikus_alakban_megy_az_iniben(kulcs):
    ini_nev = _EFFECT_INI_NAMES.get(kulcs, kulcs)
    kanonikus = canonical_filter_name(ini_nev)

    assert kanonikus is not None, (
        f"a(z) {kulcs!r} effekt {ini_nev!r} ini-neve nincs a regiszterben"
    )
    assert kanonikus == ini_nev, (
        f"a(z) {kulcs!r} effekt {ini_nev!r} alakban menne ki, a Picasa "
        f"viszont {kanonikus!r}-t vár"
    )


def test_a_kezi_tabla_minden_kulcsa_ismert_effekt():
    # A tábla ne hízzon holt bejegyzésekkel: amit leképez, azt a felület
    # tényleg használja.
    assert set(_EFFECT_INI_NAMES) <= set(_MINDEN_UI_NEV)
