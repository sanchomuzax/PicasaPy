"""#2921 — a többlet-feliratok kézi besorolásának őre.

A `docs/specs/ui-tobblet-besorolas.tsv` sorolja a QML azon feliratait,
amelyeknek nincs szó szerinti párja az eredeti Picasa szövegtárában, öt
kategóriába (saját funkció · szükséges segédszöveg · valódi eltérés · a mérő
vakfoltja · bizonytalan). A lefedettségi lap ebből mutatja a besorolást.

A tábla kézzel gondozott, ezért két irányban csúszhat el némán:

1. elgépelt kategória — a lapgenerátor ugyan megáll rajta, de az csak a
   privát repóban fut;
2. **elavult sor** — a feliratot javították vagy törölték, a sor pedig
   ott maradt, és egy nem létező feliratról állít valamit.

Ez a fájl mindkettőt a publikus CI-n fogja meg.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

GYOKER = Path(__file__).resolve().parents[1]
TABLA = GYOKER / "docs" / "specs" / "ui-tobblet-besorolas.tsv"
QML = GYOKER / "src" / "picasapy" / "app" / "qml"

KATEGORIAK = {"sajat-funkcio", "segedszoveg", "elteres", "mero-vakfolt", "bizonytalan"}


def _sorok() -> list[dict[str, str]]:
    with TABLA.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def test_a_tabla_letezik_es_nem_ures():
    assert TABLA.is_file()
    assert len(_sorok()) > 100


def test_csak_ervenyes_kategoria():
    rossz = [(s["qml_fajl"], s["felirat"], s["kategoria"])
             for s in _sorok() if s["kategoria"] not in KATEGORIAK]
    assert not rossz, rossz


def test_nincs_ketszer_ugyanaz_a_sor():
    kulcsok = [(s["qml_fajl"], s["felirat"]) for s in _sorok()]
    assert len(kulcsok) == len(set(kulcsok))


def test_minden_sornak_van_indoka():
    ures = [(s["qml_fajl"], s["felirat"]) for s in _sorok() if not s["indok"].strip()]
    assert not ures, ures


def test_az_elteres_megnevezi_a_hivatalos_kulcsot():
    """Eltérést csak a hivatalos szöveg ismeretében lehet állítani."""
    hianyos = [(s["qml_fajl"], s["felirat"]) for s in _sorok()
               if s["kategoria"] == "elteres" and not s["hivatalos_kulcs"].strip()]
    assert not hianyos, hianyos


@pytest.mark.parametrize("sor", _sorok(), ids=lambda s: f"{s['qml_fajl']}:{s['felirat'][:30]}")
def test_a_felirat_ma_is_a_fajlban_all(sor):
    """Elavult sor: a felirat már nincs a QML-ben — töröld a táblából."""
    fajl = QML / sor["qml_fajl"]
    assert fajl.is_file(), f"nincs ilyen QML-fájl: {sor['qml_fajl']}"
    forras = fajl.read_text(encoding="utf-8")
    assert f'"{sor["felirat"]}"' in forras, (
        f"a(z) „{sor['felirat']}” felirat már nincs a {sor['qml_fajl']} fájlban"
    )
