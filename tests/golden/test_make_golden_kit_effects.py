"""A #190-es effekt-referencia-generátor (`tools/golden/make_golden_kit_effects.py`)
füstpróbája.

A valódi golden-kitek (`research/golden-kit*/`) a fejlesztői gépen élnek, a
repóban nincsenek — itt csak a szkript LOGIKÁJÁT ellenőrizzük szintetikus
bemenettel: minden effekthez létrejön-e a beszédes nevű referencia-kép, a
csúszkás effektek 2-3 változatot kapnak-e, és az UTMUTATO.md hiánytalanul
felsorolja-e mindet.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "tools"
    / "golden"
    / "make_golden_kit_effects.py"
)


def _load_module():
    """A tools/golden/make_golden_kit_effects.py betöltése fájlútvonalról
    (nincs a pythonpath-on — szándékosan eszköz, nem csomag)."""
    spec = importlib.util.spec_from_file_location(
        "make_golden_kit_effects", _MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("make_golden_kit_effects", module)
    spec.loader.exec_module(module)
    return module


mgke = _load_module()


@pytest.fixture
def fotok_dir(tmp_path: Path) -> Path:
    """Néhány szintetikus "fénykép" a pick_photos-nak (fényerő-szórással)."""
    d = tmp_path / "fotok"
    d.mkdir()
    rng = np.random.default_rng(7)
    for i in range(6):
        img = rng.integers(30 + i * 30, 200 + i * 5, (40, 60, 3), dtype=np.uint8)
        cv2.imwrite(str(d / f"photo_{i:02d}.jpg"), img)
    return d


def test_slugify_ekezet_nelkuli_fajlnev_biztos_szeletke() -> None:
    assert mgke.slugify("Lomo-szerű") == "lomoszeru"
    assert mgke.slugify("HDR-szerű") == "hdrszeru"
    assert mgke.slugify("60-as évek") == "60as_evek"
    assert mgke.slugify("Múzeumi matt") == "muzeumi_matt"


def test_effect_listak_a_jegyben_felsorolt_effekteket_tartalmazzak() -> None:
    nevek4 = [e.nev for e in mgke.EFFECTS_4]
    nevek5 = [e.nev for e in mgke.EFFECTS_5]
    assert nevek4 == [
        "Infravörös film", "Lomo-szerű", "Holga-szerű", "HDR-szerű",
        "Kinemaszkóp", "Orton-szerű", "60-as évek", "Színinvertálás",
        "Hőtérkép", "Áttűnés", "Poszterizálás", "Kéttónusú",
    ]
    assert nevek5 == [
        "Felpörgetés", "Lágyítás", "Képpontnagyítás", "Fókusznagyítás",
        "Ceruzarajz", "Neon", "Képregény", "Szegély", "Árnyékvetés",
        "Múzeumi matt", "Polaroid",
    ]


def test_csuszkas_effektek_2_vagy_3_beallitast_kapnak() -> None:
    for eff in [*mgke.EFFECTS_4, *mgke.EFFECTS_5]:
        assert 1 <= len(eff.beallitasok) <= 3
        assert len(set(eff.beallitasok)) == len(eff.beallitasok)


def test_kit_generalas_letrehozza_a_vart_mappaszerkezetet(
    tmp_path: Path, fotok_dir: Path
) -> None:
    out = tmp_path / "golden-kit-effects"
    argv = sys.argv
    sys.argv = ["make_golden_kit_effects.py", str(fotok_dir), str(out)]
    try:
        mgke.main()
    finally:
        sys.argv = argv

    assert (out / "UTMUTATO.md").exists()
    assert (out / "export").is_dir()
    assert (out / "00-base" / "chart_ramp.jpg").exists()
    assert (out / "00-base" / "photo00.jpg").exists()

    vart4 = sum(len(e.beallitasok) for e in mgke.EFFECTS_4)
    vart5 = sum(len(e.beallitasok) for e in mgke.EFFECTS_5)
    kepek4 = sorted((out / "effekt4").glob("*.jpg"))
    kepek5 = sorted((out / "effekt5").glob("*.jpg"))
    assert len(kepek4) == vart4
    assert len(kepek5) == vart5

    # minden fájl valódi, beolvasható kép
    for p in [*kepek4, *kepek5]:
        assert cv2.imread(str(p)) is not None

    # az UTMUTATO.md minden fájlnevet felsorol
    utmutato = (out / "UTMUTATO.md").read_text(encoding="utf-8")
    for p in [*kepek4, *kepek5]:
        assert p.name in utmutato


def test_kit_generalas_letezo_kimeneti_mappat_felulir(
    tmp_path: Path, fotok_dir: Path
) -> None:
    out = tmp_path / "golden-kit-effects"
    out.mkdir()
    (out / "regi-maradvany.txt").write_text("torlendo")

    argv = sys.argv
    sys.argv = ["make_golden_kit_effects.py", str(fotok_dir), str(out)]
    try:
        mgke.main()
    finally:
        sys.argv = argv

    assert not (out / "regi-maradvany.txt").exists()
    assert (out / "UTMUTATO.md").exists()
