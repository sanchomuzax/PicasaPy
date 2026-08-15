"""A 2. kör őrei (#685): minden csoport EGYETLEN változót mozgat.

Az 1. körben a `Tint=`/`tint=` kísérlet azért nem döntött, mert egyszerre
változott a név ÉS a paraméterek. Ezek a tesztek pont ezt a hibát zárják ki:
ha egy csoportban két dolog is elmozdul, a mérés nem válasz, csak zaj.
"""
from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from picasapy.ini.filters import parse_filters  # noqa: E402


def _load():
    path = REPO / "tools/golden/make_validation_kit2.py"
    spec = importlib.util.spec_from_file_location("make_validation_kit2", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def kit(tmp_path_factory):
    module = _load()
    out = tmp_path_factory.mktemp("kit2") / "kit"
    sys.argv = ["make_validation_kit2.py", str(out)]
    assert module.main() == 0
    with (out / "fedettseg.csv").open(encoding="utf-8") as fh:
        return out, list(csv.DictReader(fh)), module


def test_minden_lanc_parszolhato(kit):
    _, rows, _ = kit
    for row in rows:
        parse_filters(row["lanc"])


def test_minden_kephez_van_ini_bejegyzes(kit):
    out, rows, _ = kit
    ini = (out / ".picasa.ini").read_text(encoding="utf-8")
    for row in rows:
        assert (out / row["fajl"]).is_file()
        assert f"[{row['fajl']}]" in ini


def test_a_nev_csoportban_csak_az_irasmod_valtozik(kit):
    """#689: a névcsoport csak akkor dönt, ha a paraméterek azonosak."""
    _, rows, _ = kit
    groups: dict[str, set[str]] = {}
    for row in rows:
        if row["csoport"] != "nev":
            continue
        name, _, params = row["lanc"].partition("=")
        groups.setdefault(name.casefold(), set()).add(params)
    for key, variants in groups.items():
        assert len(variants) == 1, f"{key}: eltérő paraméterek {variants}"


def test_a_tintszin_csoportban_csak_a_hex_valtozik(kit):
    """#679: a megőrzési érték nem mozdulhat, csak a színmező."""
    _, rows, _ = kit
    prefixes = set()
    for row in rows:
        if row["csoport"] != "tintszin":
            continue
        head, _, _ = row["lanc"].rstrip(";").rpartition(",")
        prefixes.add(head)
    assert prefixes == {"tint=1,79.842102"}


def test_az_auto_csoport_kap_javitando_kepet(kit):
    """Semleges képen az automatikák joggal tétlenek — az nem eredmény."""
    _, rows, module = kit
    auto = [row for row in rows if row["csoport"] == "auto"]
    assert auto
    assert any(row["alapkep"] == module.CAST for row in auto)
    assert any(row["alapkep"] == module.NEUTRAL for row in auto), "kontroll kell"


def test_a_ket_alapkep_ternyleg_kulonbozik(kit):
    import cv2
    import numpy as np

    out, rows, _ = kit
    by_chart = {}
    for row in rows:
        by_chart.setdefault(row["alapkep"], row["fajl"])
    assert len(by_chart) == 2
    images = [cv2.imread(str(out / name)) for name in by_chart.values()]
    assert np.abs(images[0].astype(int) - images[1].astype(int)).mean() > 10


def test_nincs_ketszer_ugyanaz_a_meres(kit):
    """Ugyanaz a lánc KÉT alapképen szándékos (kontroll) — ne tiltsuk le."""
    _, rows, _ = kit
    seen = set()
    for row in rows:
        key = (row["csoport"], row["lanc"], row["alapkep"])
        assert key not in seen, key
        seen.add(key)
