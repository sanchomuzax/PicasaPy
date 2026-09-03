"""#2083: a nagy-fájl őr foga és kapu-ellenőrzése.

Az eset: egy `git add -A` bevitt a munkafából 168 fájlt, **84 MB**-ot (a
tulajdonos Picasa-`db3` másolatát) egy PUBLIKUS repó PR-jébe. A beolvadást
csak véletlen akadályozta meg (a changelog-őr a bináris diffen elszállt).

A küszöb **mérésből** jön: a repóban 1 MB fölött EGYETLEN fájl van, és az
szándékos; a bevitt adathalmaz legnagyobb darabja 12 MB volt.

⚠️ Ez a fájl a KÉT irányt együtt méri: az őr megfogja a küszöb fölötti
újat, és NEM bünteti a kimondott kivételt.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

GYOKER = Path(__file__).resolve().parents[1]
OR = GYOKER / "scripts" / "nagy_fajl_or.py"


def _futtat() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(OR)],
        cwd=GYOKER,
        capture_output=True,
        text=True, encoding="utf-8",
        errors="replace",
    )


@pytest.fixture
def kovetett_proba():
    """Ideiglenes, INDEXBE VETT fájl — az őr a `git ls-files`-t nézi."""
    ut = GYOKER / "_proba_nagy_fajl_2083.bin"
    yield ut
    subprocess.run(["git", "rm", "-q", "--cached", "--ignore-unmatch", ut.name],
                   cwd=GYOKER, capture_output=True)
    ut.unlink(missing_ok=True)


def _indexbe(ut: Path) -> None:
    subprocess.run(["git", "add", "-f", ut.name], cwd=GYOKER, capture_output=True)


def test_a_mai_repo_TISZTA():
    """Enélkül minden más eset hamis: az őrnek a jelenlegi fán zöldnek kell
    lennie, különben nem a vetett hibát méri."""
    assert _futtat().returncode == 0


def test_a_KUSZOB_FOLOTTI_ujat_megfogja(kovetett_proba):
    """Fog: e nélkül a 84 MB-os eset némán átment volna."""
    kovetett_proba.write_bytes(b"\0" * 1_200_000)
    _indexbe(kovetett_proba)

    eredmeny = _futtat()

    assert eredmeny.returncode != 0, "az őr átengedte az 1,2 MB-os fájlt"
    assert kovetett_proba.name in eredmeny.stdout


def test_a_kuszob_ALATTIT_atengedi(kovetett_proba):
    """Kapu-ellenőrzés: a hétköznapi fájlt nem büntetheti."""
    kovetett_proba.write_bytes(b"\0" * 900_000)
    _indexbe(kovetett_proba)

    assert _futtat().returncode == 0


def test_a_NEM_KOVETETT_nagy_fajlt_figyelmen_kivul_hagyja(kovetett_proba):
    """A munkafában heverő nagy fájl önmagában nem hiba — a `temp_1645/` is
    hetekig ott állt `??` állapotban. Csak a VERZIÓKÖVETETT számít."""
    kovetett_proba.write_bytes(b"\0" * 2_000_000)  # NINCS `git add`

    assert _futtat().returncode == 0


class TestKivetelek:
    def test_a_kimondott_kivetel_ATMEGY(self):
        """A meglévő 5,2 MB-os infografika a repó szándékos része."""
        from importlib.util import module_from_spec, spec_from_file_location

        spec = spec_from_file_location("nagy_fajl_or", OR)
        modul = module_from_spec(spec)
        spec.loader.exec_module(modul)
        kivetel = "docs/assets/notebooklm-infografika.png"
        assert kivetel in modul.KIVETELEK
        assert (GYOKER / kivetel).stat().st_size > modul.KUSZOB
        assert _futtat().returncode == 0

    def test_MINDEN_kivetelhez_tartozik_INDOKLAS(self):
        """A kivétel nem kényelmi lehetőség: aki felvesz egyet, megmondja,
        miért van a repóban a helye."""
        from importlib.util import module_from_spec, spec_from_file_location

        spec = spec_from_file_location("nagy_fajl_or", OR)
        modul = module_from_spec(spec)
        spec.loader.exec_module(modul)
        for ut, indok in modul.KIVETELEK.items():
            assert indok.strip(), f"{ut}: üres indoklás"
            assert len(indok) > 20, f"{ut}: az indoklás túl szűkszavú"
