"""#3449: a golden-generátor a PIPETTÁS effektek láncát nem csúsztatja el.

A regiszter a pipettát (`dropper`) is `has_puck=True`-ként viszi, mert a
felületen színpipetta van. A `chain_for` `has_puck` ága viszont az első két
numerikus helyre fókuszpontot (`0.5, 0.5`) írt, és a csúszkákat hátrébb
tolta — a 684-es kitben így a `finetune`, `finetune2`, `colorfix` és
`whitept` sorai nem a szándékolt csúszkaállást mérték (pl. `finetune2` alap:
`finetune2=1,0.5,0.5,0.5,00000000,0.24` a `0.5, 0.24, 0.24, 0.0` helyett).

A mezősorrend a `finetune`/`finetune2`-nél bizonyított (`picasa-ini-format.md`
143. és 257. sor). A `colorfix` és a `whitept` is pipettás, de a mezőszámuk a
spec szerint nem dönthető el, és nem renderelődnek — rájuk ez a próba nem
állít semmit.
"""

from __future__ import annotations

import csv
import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools" / "golden"))

from picasapy.ini.filters import parse_filters  # noqa: E402

PIPETTAS = ("finetune", "finetune2")
HEX_SLOT = re.compile(r"^[0-9a-fA-F]{8}$")


def _load_generator():
    path = REPO / "tools/golden/make_validation_kit.py"
    spec = importlib.util.spec_from_file_location("make_validation_kit_3449", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sorok(tmp_path_factory):
    module = _load_generator()
    out = tmp_path_factory.mktemp("meroszett3449") / "kit"
    sys.argv = ["make_validation_kit.py", str(out)]
    assert module.main() == 0
    with (out / "fedettseg.csv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _szamok(lanc: str) -> list[float]:
    """A lánc numerikus paraméterei az engedélyező `1` után, a nyolcjegyű
    színrekesz (pl. `00000000`) nélkül."""
    op = parse_filters(lanc)[0]
    return [float(p) for p in op.params[1:] if not HEX_SLOT.match(p)]


def _szandekolt(sor: dict) -> list[float]:
    return [float(r.split("=")[1]) for r in sor["csuszkak"].split(" | ") if r]


@pytest.mark.parametrize("effekt", PIPETTAS)
def test_a_pipettas_effekt_lanca_a_csuszkaallast_hordozza(sorok, effekt):
    sajat = [s for s in sorok if s["effekt"] == effekt]
    assert sajat, f"{effekt}: nincs sor a kitben"
    for sor in sajat:
        szamok = _szamok(sor["lanc"])
        vart = _szandekolt(sor)
        assert szamok[: len(vart)] == pytest.approx(vart), (sor["eset"], sor["lanc"])


def test_a_finetune2_harom_sora_a_jegy_szerint(sorok):
    """A jegy bizonyítéka: a szándékolt `Fill, Highlights, Shadows, Temp`."""
    vart = {
        "min": [0.0, 0.0, 0.0, -1.0],
        "alap": [0.5, 0.24, 0.24, 0.0],
        "max": [1.0, 0.48, 0.48, 1.0],
    }
    kapott = {s["eset"]: _szamok(s["lanc"]) for s in sorok if s["effekt"] == "finetune2"}
    for eset, szamok in vart.items():
        assert kapott[eset][:4] == pytest.approx(szamok), (eset, kapott[eset])


def test_a_valodi_fokuszpontos_effekt_marad_05_05(sorok):
    """A `radsat` fókuszpontja továbbra is az első két hely."""
    sajat = [s for s in sorok if s["effekt"] == "radsat"]
    assert sajat
    for sor in sajat:
        assert _szamok(sor["lanc"])[:2] == [0.5, 0.5], sor["lanc"]


@pytest.mark.parametrize("sorrend", ["a_pontos_elol", "a_pontos_hatul"])
def test_a_sablonvalasztas_nem_fugg_a_fajlsorrendtol(tmp_path, sorrend):
    """Azonos hosszú minták közül a tizedespontos (a Picasa írásmódja) nyer,
    akármelyik fájl kerül elő előbb. A CI-n egy egységteszt-sztring
    (`finetune=1,0.1,0,0,…`) nyert, és a 0,24-et egészre vágta."""
    module = _load_generator()
    pontos = "finetune=1,0.500000,0.000000,0.000000,00000000,0.000000;"
    egesz = "finetune=1,0.1,0,0,00000000,0.2;"
    elso, masodik = (pontos, egesz) if sorrend == "a_pontos_elol" else (egesz, pontos)
    mappa = tmp_path / "docs" / "specs"
    mappa.mkdir(parents=True)
    (mappa / "a.md").write_text(elso, encoding="utf-8")
    (mappa / "b.md").write_text(masodik, encoding="utf-8")
    sablon = module.harvest_templates(tmp_path)["finetune"]
    assert sablon == ["0.500000", "0.000000", "0.000000", "00000000", "0.000000"]
