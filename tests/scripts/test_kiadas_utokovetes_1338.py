"""A kiadás utókövetése: a verzióemelő PR beolvadása után AZONNAL kiad (#1338).

## A lelet

A verzióemelő PR-t az integrációs token olvasztja be, és a GitHub a saját
tokenjével keletkező pushra SZÁNDÉKOSAN nem indít workflow-t. A `release.yml`
így el sem indul: a `pyproject.toml` verziója felmegy, a Releases hasáb nem
követi. Mérve (2026-08-24): a `release.yml` NEGYVEN futásából egyetlen `push`
sem a verzióemelő PR beolvasztásából jött, és a nap tizennégy kiadását a
tulajdonos indította kézzel.

## Miért ez a megoldás

A `workflow_dispatch` a rekurzióvédelem DOKUMENTÁLT kivétele, és a repóban
MÉRT bizonyíték van rá, hogy működik: a 2026-08-24 20:03:36-os `release.yml`
futást a `github-actions[bot]` indította a kiadási őrből. Az utókövető
ugyanezt az utat használja — nem újat.

⚠️ A legfontosabb állítás ebben a fájlban a
`test_a_mar_kiadott_verziohoz_SOHA_nem_indit`: a kiadás VISSZAVONHATATLAN,
tehát az utókövető soha nem indíthat kiadást olyan verzióra, amihez már van.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import kiadas_utokovetes as ku  # noqa: E402

PYPROJECT = 'name = "picasapy"\nversion = "{v}"\n'


class _Gh:
    """`gh`/`git`-helyettes: verziósorozat a `main`-en, kiadáslista mellé.

    A `verziok` elemei egymás utáni köröket írnak le: az első hívás az
    elsőt adja, és így tovább — az utolsó ismétlődik. Így modellezhető,
    hogy a verzióemelő PR a harmadik kör közben olvad be.
    """

    def __init__(
        self,
        verziok: list[str],
        kiadott: set[str],
        *,
        verzio_hibak: int = 0,
        kiadas_valasz: tuple[int, str] | None = None,
        dispatch_kod: int = 0,
    ) -> None:
        self.verziok = verziok
        self.kiadott = kiadott
        self.hivasok: list[list[str]] = []
        self._verzio_index = 0
        self._verzio_hibak = verzio_hibak
        self._kiadas_valasz = kiadas_valasz
        self._dispatch_kod = dispatch_kod

    def __call__(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        self.hivasok.append(args)
        egyben = " ".join(args)

        if args[:2] == ["git", "fetch"]:
            return subprocess.CompletedProcess(args, 0, "", "")

        if args[:2] == ["git", "show"]:
            if self._verzio_hibak > 0:
                self._verzio_hibak -= 1
                return subprocess.CompletedProcess(args, 128, "", "fatal: bad object")
            index = min(self._verzio_index, len(self.verziok) - 1)
            self._verzio_index += 1
            return subprocess.CompletedProcess(
                args, 0, PYPROJECT.format(v=self.verziok[index]), ""
            )

        if "release view" in egyben:
            if self._kiadas_valasz is not None:
                return subprocess.CompletedProcess(
                    args, self._kiadas_valasz[0], "", self._kiadas_valasz[1]
                )
            cimke = args[args.index("view") + 1]
            van = cimke.removeprefix("v") in self.kiadott
            return subprocess.CompletedProcess(args, 0 if van else 1, "", "")

        if "workflow run" in egyben:
            return subprocess.CompletedProcess(args, self._dispatch_kod, "", "hiba")

        return subprocess.CompletedProcess(args, 0, "", "")

    @property
    def inditasok(self) -> list[list[str]]:
        return [h for h in self.hivasok if "workflow run" in " ".join(h)]


def _alvo() -> tuple[list[float], object]:
    naplo: list[float] = []
    return naplo, naplo.append


class TestVerzioAMainrol:
    def test_az_origin_main_bol_olvas_nem_a_munkafabol(self) -> None:
        """A futó munkafa a régi verziót mutatja — a beolvadást csak a
        friss `origin/main` látja."""
        gh = _Gh(["0.8.87"], {"0.8.87"})
        assert ku.fo_verzio(runner=gh) == "0.8.87"
        assert any(
            h[:2] == ["git", "fetch"] and h[-2:] == ["origin", "main"]
            for h in gh.hivasok
        ), "friss `fetch` nélkül a beolvadás nem látszana"
        assert any(
            h[:2] == ["git", "show"] and "origin/main:pyproject.toml" in h
            for h in gh.hivasok
        )

    def test_a_sikertelen_olvasas_NEM_verzio_hanem_tudatlansag(self) -> None:
        gh = _Gh(["0.8.87"], set(), verzio_hibak=1)
        assert ku.fo_verzio(runner=gh) is None


class TestUtokovetes:
    def test_a_beolvadas_utan_KIADAST_indit(self) -> None:
        """Két kör a régi verziót látja, a harmadikban beolvad az emelés."""
        gh = _Gh(["0.8.86", "0.8.86", "0.8.87"], {"0.8.86"})
        naplo, alvo = _alvo()
        assert ku.utokovet(repo="o/r", runner=gh, sleeper=alvo, korok=10) == 0
        assert gh.inditasok == [
            ["gh", "workflow", "run", "release.yml", "--repo", "o/r", "--ref", "main"]
        ]
        assert len(naplo) == 3, "a figyelés ALVÁSSAL kezd: induláskor a main még rendben"

    def test_a_mar_kiadott_verziohoz_SOHA_nem_indit(self) -> None:
        """⚠️ A kiadás visszavonhatatlan: több kiadás nem lehet, mint verzió."""
        gh = _Gh(["0.8.87"], {"0.8.87"})
        _, alvo = _alvo()
        assert ku.utokovet(repo="o/r", runner=gh, sleeper=alvo, korok=5) == 0
        assert gh.inditasok == []

    def test_EGYSZER_indit_akkor_is_ha_marad_ido(self) -> None:
        """A dispatch után nincs mit figyelni — a duplikált indítás két
        teljes kiadó futást vinne el ugyanarra a verzióra."""
        gh = _Gh(["0.8.87"], set())
        _, alvo = _alvo()
        assert ku.utokovet(repo="o/r", runner=gh, sleeper=alvo, korok=20) == 0
        assert len(gh.inditasok) == 1

    def test_az_atmeneti_hiba_NEM_szamit_hianyzo_kiadasnak(self) -> None:
        """A `gh` hibakódja nem különbözteti meg a „nincs ilyen"-t a „nem
        érhető el"-től — ugyanaz a csapda, mint az `ensure_release.py`-ban."""
        gh = _Gh(["0.8.87"], set(), kiadas_valasz=(1, "HTTP 503: no server"))
        _, alvo = _alvo()
        assert ku.utokovet(repo="o/r", runner=gh, sleeper=alvo, korok=3) == 0
        assert gh.inditasok == []

    def test_a_mereten_kivuli_varakozas_NEM_bukas(self) -> None:
        """A negyedórás kiadási őr a háló: az utókövető lejárta nem hiba."""
        gh = _Gh(["0.8.86"], {"0.8.86"})
        naplo, alvo = _alvo()
        assert ku.utokovet(repo="o/r", runner=gh, sleeper=alvo, korok=4) == 0
        assert len(naplo) == 4

    def test_a_dispatch_bukasa_HANGOS(self, capsys) -> None:
        gh = _Gh(["0.8.87"], set(), dispatch_kod=1)
        _, alvo = _alvo()
        assert ku.utokovet(repo="o/r", runner=gh, sleeper=alvo, korok=3) == 1
        assert "::error" in capsys.readouterr().out

    def test_a_nem_mérhető_verzio_nem_indit_kiadast(self) -> None:
        """Tudatlanságból kiadni tilos — a hiányzó kiadás pótolható, a
        fölösleges nem vonható vissza."""
        gh = _Gh(["0.8.87"], set(), verzio_hibak=99)
        _, alvo = _alvo()
        assert ku.utokovet(repo="o/r", runner=gh, sleeper=alvo, korok=3) == 0
        assert gh.inditasok == []


class TestParancssor:
    def test_a_repo_kotelezo(self) -> None:
        try:
            ku.main([])
        except SystemExit as kilepes:
            assert kilepes.code != 0
        else:  # pragma: no cover
            raise AssertionError("a --repo hiánya nem bukott el")
