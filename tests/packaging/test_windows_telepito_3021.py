"""#3021: a windowsos telepítő EGY értelmezőt válasszon, és azt használja.

## A jelentés

A tulajdonos: *„Korábban készült egy indító .exe ikonnal Windows-ra. Na,
az már nem működik."*

## Az ellentmondás, amit a sablon mutatott

A `pip install` KÉT értelmezőt próbált (`py -3.12`, majd tartalékként
`py -3`), a parancsikon útvonalait viszont **csak a 3.12-től** kérdezte
meg, tartalék nélkül. Ha a gépen már nincs 3.12 (például 3.13-ra
frissült), a telepítés a tartalék ágon SIKERÜL, a parancsikon viszont
elmarad vagy a régi `Scripts` mappára mutat — pontosan a „korábban
működött, most nem".

Ez a próba azt tartja fenn, hogy a két lépés **ugyanazt** az értelmezőt
használja.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_SABLON = (
    Path(__file__).resolve().parents[2]
    / "packaging" / "windows" / "install.bat.template"
)


@pytest.fixture(scope="module")
def sablon() -> str:
    return _SABLON.read_text(encoding="utf-8", errors="replace")


class TestAzErtelmezo:
    def test_a_sablon_letezik(self, sablon):
        assert "picasapy" in sablon

    def test_NINCS_beegetett_verzio_a_hivasokban(self, sablon):
        """Se a pip, se a parancsikon ne kérjen NÉV SZERINT 3.12-t."""
        beegetett = [
            sor.strip()
            for sor in sablon.splitlines()
            if re.search(r"py\s+-3\.\d+", sor) and not sor.strip().startswith("rem")
        ]
        assert not beegetett, (
            "beégetett Python-verzió a hívásokban — egy frissítés után a "
            f"parancsikon elmarad: {beegetett}"
        )

    def test_EGY_valtozo_viszi_az_ertelmezot(self, sablon):
        assert "PYCMD" in sablon, "nincs közös értelmező-változó"
        hasznalat = sablon.count("!PYCMD!") + sablon.count("%PYCMD%")
        assert hasznalat >= 4, (
            f"az értelmező-változót csak {hasznalat} helyen használjuk — "
            "a pip, a Scripts-útvonal és az ikon-útvonal mind kell"
        )

    def test_a_parancsikon_es_a_pip_UGYANAZT_hasznalja(self, sablon):
        """A hiba magja: a két lépés külön döntött."""
        pip_sorok = [s for s in sablon.splitlines() if "-m pip install" in s]
        ikon_sorok = [
            s for s in sablon.splitlines()
            if not s.strip().startswith(("rem", "echo"))
            and ("sysconfig" in s or "find_spec" in s)
        ]
        assert pip_sorok and ikon_sorok
        for sor in pip_sorok + ikon_sorok:
            assert "PYCMD" in sor, f"nem a közös értelmezőt hívja: {sor.strip()}"


class TestAParancsikon:
    def test_MINDEN_telepiteskor_ujrairodik(self, sablon):
        """Python-frissítés után a régi parancsikon rossz helyre mutatna."""
        assert "CreateShortcut" in sablon
        assert "$s.Save()" in sablon

    def test_a_kudarc_NEM_nema(self, sablon):
        assert "FIGYELEM" in sablon, "a sikertelen parancsikon némán elveszne"

    def test_az_IKON_utvonal_kulon_megy(self, sablon):
        """#67: a taskbar-ikon csak explicit `IconLocation`-nal jó."""
        assert "IconLocation" in sablon
