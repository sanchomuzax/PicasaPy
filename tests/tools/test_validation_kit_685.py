"""A mérőszett-generátor őrei (#685).

A szett egyetlen célja, hogy a felhasználó EGY exportálásból megtudja, melyik
effekt működik. Ezért a legdrágább hiba nem a hiányzó eset, hanem a **rossz
lánc**: attól a Picasa némán nem csinál semmit, és azt tévesen „nem
működik"-nek olvasnánk. Ezek a tesztek pont ezt őrzik.
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


def _load_generator():
    path = REPO / "tools/golden/make_validation_kit.py"
    spec = importlib.util.spec_from_file_location("make_validation_kit", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def kit(tmp_path_factory):
    module = _load_generator()
    out = tmp_path_factory.mktemp("meroszett") / "kit"
    sys.argv = ["make_validation_kit.py", str(out)]
    assert module.main() == 0
    with (out / "fedettseg.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return out, rows, module


def test_minden_lanc_parszolhato(kit):
    _, rows, _ = kit
    for row in rows:
        parse_filters(row["lanc"])


def test_minden_sorhoz_van_kep_es_ini_bejegyzes(kit):
    out, rows, _ = kit
    ini = (out / ".picasa.ini").read_text(encoding="utf-8")
    for row in rows:
        assert (out / row["fajl"]).is_file(), row["fajl"]
        assert f"[{row['fajl']}]" in ini
        assert row["lanc"] in ini


def test_a_border_hat_parametert_kap_a_valodi_mintabol(kit):
    """A regiszter 4 csúszkát ismer, a valódi lánc 6 rekeszt hordoz.

    Ha ez elromlik, a Picasa a `Border`-t némán elejti, és hamis
    „nem működik" verdiktet kapunk.
    """
    _, rows, _ = kit
    border = [row for row in rows if row["effekt"] == "border"]
    assert border, "a Border kimaradt a szettből"
    for row in border:
        assert row["megbizhatosag"] == "mintabol"
        params = row["lanc"].split("=", 1)[1].rstrip(";").split(",")
        assert len(params) == 7, row["lanc"]  # flag + 6 rekesz
        assert params[4:6] == ["00000000", "00ffffff"]


def test_a_szinrekeszek_nem_kapnak_csuszkaerteket(kit):
    """Sablonból építve a hex rekeszek helyben maradnak, minden esetben."""
    _, rows, _ = kit
    for row in rows:
        if row["megbizhatosag"] != "mintabol":
            continue
        for param in row["lanc"].split("=", 1)[1].rstrip(";").split(","):
            if len(param) == 8 and all(c in "0123456789abcdef" for c in param):
                assert "." not in param


def test_a_picasa_sajat_irasmodjat_hasznaljuk(kit):
    _, rows, _ = kit
    wire = {row["effekt"]: row["picasa_nev"] for row in rows}
    assert wire["vignette"] == "Vignette"
    assert wire["picnikgrain"] == "PicnikGrain"
    assert wire["museummatte"] == "MuseumMatte"
    for row in rows:
        assert row["lanc"].startswith(f"{row['picasa_nev']}="), row["lanc"]


def test_a_tint_hex_par_benne_van(kit):
    """A #679 utolsó nyitott kérdése ugyanezzel az exporttal eldől."""
    _, rows, _ = kit
    pair = {row["eset"]: row for row in rows if row["effekt"] == "tint"}
    assert "hex4" in pair and "hex8" in pair
    assert pair["hex4"]["lanc"].endswith(",ffff;")
    assert pair["hex8"]["lanc"].endswith(",0000ffff;")
    # csak a hex jegyek számában térhetnek el
    assert (
        pair["hex4"]["lanc"].replace(",ffff;", "")
        == pair["hex8"]["lanc"].replace(",0000ffff;", "")
    )


def test_a_nem_renderelo_bejegyzesek_kimaradnak(kit):
    _, rows, module = kit
    keys = {row["effekt"] for row in rows}
    assert not (keys & module.SKIP)


def test_nincs_ketszer_ugyanaz_a_lanc(kit):
    _, rows, _ = kit
    chains = [row["lanc"] for row in rows]
    assert len(chains) == len(set(chains))
