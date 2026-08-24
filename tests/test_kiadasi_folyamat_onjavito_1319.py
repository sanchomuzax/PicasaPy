"""A kiadási folyamat ÖNJAVÍTÓ — nem egy figyelmes műszakon múlik (#1319).

## A lelet

A #1318-as verzióemelő PR-t egy olyan beolvasztás szülte, ami mindössze két
`docs/specs/` fájlt módosított: kiadni nem volt mit, a PR mégis ott ült
nyitva, ellenőrzés nélkül (a bot-PR-en a GitHub szándékosan nem indít
workflow-t, #1190). Két hiba egyszerre:

1. az automatika VAKON emelt — nem nézte, érinti-e a változás a programot;
2. utána NEM volt, aki elrendezze a félbemaradt PR-t.

Ez a fájl a munkafolyamatok SZÖVEGÉRE néz — a hatást csak valódi
GitHub-futásban lehetne előidézni, a szabály viszont statikusan kimondható.
Ugyanaz az elv, mint a `test_kiadas_jelzi_a_jovahagyast_1204.py`-nál. A
döntések MŰKÖDÉSÉT a `tests/scripts/test_kiadas_szukseges_1319.py` és a
`tests/scripts/test_kiadas_or_1319.py` méri.
"""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

_MUNKAFOLYAMATOK = pathlib.Path(__file__).resolve().parents[1] / ".github" / "workflows"
RELEASE = _MUNKAFOLYAMATOK / "release.yml"
OR = _MUNKAFOLYAMATOK / "kiadasi-or.yml"


@pytest.fixture(scope="module")
def release() -> dict:
    return yaml.safe_load(RELEASE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def orjarat() -> dict:
    return yaml.safe_load(OR.read_text(encoding="utf-8"))


def _lepes(adat: dict, job: str, azonosito: str) -> str:
    for lepes in adat["jobs"][job]["steps"]:
        if lepes.get("id") == azonosito:
            return lepes["run"]
    raise AssertionError(f"nincs `{azonosito}` azonosítójú lépés")


class TestFeltetelesVerzioemeles:
    def test_a_bump_lepes_megkerdezi_kell_e_kiadas(self, release: dict) -> None:
        """A #1318 gyökere: a döntés hiánya."""
        assert "kiadas_szukseges.py" in _lepes(release, "release", "bump")

    def test_a_nem_valasz_MEGALLITJA_az_emelest(self, release: dict) -> None:
        bump = _lepes(release, "release", "bump")
        sorok = bump.splitlines()
        dontes = next(i for i, s in enumerate(sorok) if "kiadas_szukseges.py" in s)
        kovetkezo = "\n".join(sorok[dontes:])
        assert '!= "igen"' in kovetkezo and "exit 0" in kovetkezo, (
            "a döntés kimenetére nincs kilépő ág — az emelés attól még megtörténne"
        )

    def test_az_auto_bump_a_dontes_UTAN_fut(self, release: dict) -> None:
        bump = _lepes(release, "release", "bump")
        assert bump.index("kiadas_szukseges.py") < bump.index("auto_bump.py")


class TestKonkurenciazar:
    def test_a_kiadas_nem_futhat_ketszer_egyszerre(self, release: dict) -> None:
        """Két gyors merge két verzióemelő PR-t szülne ugyanarra."""
        assert release["concurrency"]["group"]

    def test_a_futo_kiadast_TILOS_megszakitani(self, release: dict) -> None:
        """Félbehagyva a Releases hasáb maradna lemaradva."""
        assert release["concurrency"]["cancel-in-progress"] is False


class TestKiadasiOr:
    def test_a_kiadas_vegen_is_lefut_az_or(self, release: dict) -> None:
        """A gyors út: ne kelljen megvárni a következő ütemezett futást."""
        futasok = " ".join(
            lepes.get("run", "") for lepes in release["jobs"]["release"]["steps"]
        )
        assert "kiadas_or.py" in futasok

    def test_az_or_utemezetten_is_jar(self, orjarat: dict) -> None:
        # ⚠️ A YAML az `on:` kulcsot logikai igazzá alakítja — ez nem hiba.
        assert orjarat[True]["schedule"], "nincs ütemezés — az őr csak kézre indulna"

    def test_az_utemezes_negyedorankent_jar(self, orjarat: dict) -> None:
        percek = orjarat[True]["schedule"][0]["cron"].split()[0]
        assert percek.startswith("*/"), f"nem gyakori ütemezés: {percek}"
        assert int(percek.removeprefix("*/")) <= 15

    def test_az_or_kezzel_is_inditható(self, orjarat: dict) -> None:
        assert "workflow_dispatch" in orjarat[True]

    def test_az_ornek_van_joga_CI_t_inditani(self, orjarat: dict) -> None:
        """`gh workflow run` — enélkül a bot-PR ellenőrzés nélkül marad."""
        assert orjarat["permissions"].get("actions") == "write"

    def test_az_ornek_van_joga_issue_t_nyitni(self, orjarat: dict) -> None:
        """A néma bukás pontosan az a hiba, amit orvosolunk."""
        assert orjarat["permissions"].get("issues") == "write"

    def test_ket_orfutas_nem_dolgozik_egyszerre(self, orjarat: dict) -> None:
        assert orjarat["concurrency"]["group"]
        assert orjarat["concurrency"]["cancel-in-progress"] is False
