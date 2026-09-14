"""A CI-ben a gépen belüli teszt-párhuzamosság KI van kapcsolva (#2848).

## Miért kell erre őr

A `scripts/run_tests.py` `_PARHUZAM` alapértelmezése a HELYI gépre szól
(#1038: kettő szál, 1,51–1,56× gyorsulás). A CI viszont a #1262 óta
(2026-08-23) **ugyanezt a futtatót** hívja darabonként
(`teszt-darabok.yml` „Run tests" lépése), tehát a helyi alapértelmezés
minden bejelentés nélkül átszivárog a felhő-körbe.

Ez meg is történt: a 2026-09-10-i emelés (#1038) a CI-ben is kettő szálat
kapcsolt be, pedig a párhuzamos CI-t a #1044 visszavonása (#988) kifejezetten
megtiltotta, amíg a #988/#999 gyökérok nincs javítva. A futtató kommentje
ráadásul azt ÁLLÍTOTTA, hogy „a `ci.yml` nem ezt a futtatót használja" — a
hivatkozott sor a dokumentáció-őrök lépése, nem a tesztmátrix.

⚠️ A kapu SZÁNDÉKOSAN a futtatóban van, nem a munkafolyamat `env:`
blokkjában: a döntés ott éljen, ahol az indoklása is. (Melléklelet: a gépi
azonosság nem is tud a `.github/workflows/` alá írni — `workflows`
jogosultság nélkül a push elutasított —, tehát a YAML-ba tett kapu a gépi
körökből nem is volna karbantartható.)
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_FUTTATO = Path(__file__).resolve().parents[2] / "scripts" / "run_tests.py"


def _betolt():
    """A futtató modulként — a `main()` lefutása nélkül."""
    spec = importlib.util.spec_from_file_location("_rt_2848", _FUTTATO)
    assert spec and spec.loader
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_a_ci_sorosra_valt():
    """Kérés nélkül a CI-ben EGY szál, indoklással."""
    rt = _betolt()
    szam, indok = rt._dontsd_el_a_parhuzamot(None, 2, False, ci=True)
    assert szam == 1, "a CI-ben tilos a gépen belüli párhuzamosság (#2848)"
    assert "CI" in indok


def test_a_kifejezett_keres_a_CI_ben_is_nyer():
    """Aki explicit beállítja, tudja, mit csinál — a mérés így elvégezhető."""
    rt = _betolt()
    szam, indok = rt._dontsd_el_a_parhuzamot("4", 4, False, ci=True)
    assert szam == 4
    assert "kérésre" in indok


def test_helyben_marad_a_mert_alapertelmezes():
    """A #1038 kettős alapértelmezése a helyi gépen érintetlen."""
    rt = _betolt()
    szam, indok = rt._dontsd_el_a_parhuzamot(None, 2, False, ci=False)
    assert szam == 2
    assert indok == "alapértelmezés"


def test_a_masik_futas_tovabbra_is_sorosra_valt():
    """A #1037 védőhálója nem tűnt el az új ág mellett."""
    rt = _betolt()
    szam, indok = rt._dontsd_el_a_parhuzamot(None, 2, True, ci=False)
    assert szam == 1
    assert "MÁSIK" in indok


def test_a_darab_job_tovabbra_is_a_futtatot_hivja():
    """A kikötés CSAK akkor véd, ha a CI valóban a futtatón megy át.

    Ha a munkafolyamat egyszer visszatér a csupasz `pytest`-re, ez bukik, és
    akkor a futtatóba tett kapu is újragondolandó — nem marad hátra egy
    értelmét vesztett, hamis biztonságot adó őr.
    """
    yml = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "teszt-darabok.yml"
    ).read_text(encoding="utf-8")
    assert "scripts/run_tests.py --shard" in yml
