"""A kiadás nem vár kézi indításra a verzióemelő PR beolvadása után (#1338).

## A lelet

A `release.yml` a `push: branches: [main]` eseményre indul, a verzióemelő
PR-t viszont az integrációs token olvasztja be — és a GitHub a saját
tokenjével keletkező pushra SZÁNDÉKOSAN nem indít workflow-t. Mérve
(2026-08-24): a `release.yml` negyven futásából egyetlen `push` sem a
verzióemelő PR beolvasztásából jött, a nap tizennégy kiadását a tulajdonos
indította kézzel, és a `github-actions[bot]` mindössze EGYSZER ért oda
előbb — a negyedórás kiadási őrből.

Ez a fájl a munkafolyamatok SZÖVEGÉRE néz; a hatást csak valódi
GitHub-futásban lehetne előidézni. A döntések MŰKÖDÉSÉT a
`tests/scripts/test_kiadas_utokovetes_1338.py` méri.
"""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

_MUNKAFOLYAMATOK = pathlib.Path(__file__).resolve().parents[1] / ".github" / "workflows"
RELEASE = _MUNKAFOLYAMATOK / "release.yml"
UTOKOVETO = _MUNKAFOLYAMATOK / "kiadas-utokoveto.yml"


@pytest.fixture(scope="module")
def release() -> dict:
    return yaml.safe_load(RELEASE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def utokoveto() -> dict:
    return yaml.safe_load(UTOKOVETO.read_text(encoding="utf-8"))


def _lepes(adat: dict, job: str, azonosito: str) -> str:
    for lepes in adat["jobs"][job]["steps"]:
        if lepes.get("id") == azonosito:
            return lepes["run"]
    raise AssertionError(f"nincs `{azonosito}` azonosítójú lépés")


class TestAtadasAKiadonak:
    def test_a_bump_lepes_elinditja_az_utokovetot(self, release: dict) -> None:
        """A verzióemelő PR nyitása és az utókövetés indítása EGY döntés:
        aki PR-t nyit, az tudja, hogy kiadás fog kelleni."""
        bump = _lepes(release, "release", "bump")
        assert "kiadas-utokoveto.yml" in bump

    def test_az_utokoveto_a_PR_nyitasa_UTAN_indul(self, release: dict) -> None:
        bump = _lepes(release, "release", "bump")
        assert bump.index("gh pr create") < bump.index("kiadas-utokoveto.yml")

    def test_az_utokoveto_indulasa_nem_lehet_fatalis(self, release: dict) -> None:
        """Ha az utókövető nem indul, a kiadó lépésnek akkor is le kell
        futnia — ugyanaz a szabály, mint a PR-nyitásnál."""
        bump = _lepes(release, "release", "bump")
        sor = next(s for s in bump.splitlines() if "kiadas-utokoveto.yml" in s)
        kovetkezo = bump[bump.index(sor) :]
        assert "||" in sor or kovetkezo.splitlines()[1].strip().startswith("||"), (
            "az utókövető indítása bukáskor megállítaná a kiadást"
        )


class TestUtokovetoMunkafolyamat:
    def test_letezik(self) -> None:
        assert UTOKOVETO.exists(), "nincs utókövető munkafolyamat"

    def test_csak_dispatchre_indul(self, utokoveto: dict) -> None:
        """⚠️ `push`-ra NEM: az utókövetőt a kiadó hívja, amikor tudja, hogy
        kiadás fog kelleni. Ütemezésre a negyedórás kiadási őr való."""
        # ⚠️ A YAML az `on:` kulcsot logikai igazzá alakítja — ez nem hiba.
        assert list(utokoveto[True]) == ["workflow_dispatch"]

    def test_van_joga_kiadast_inditani(self, utokoveto: dict) -> None:
        assert utokoveto["permissions"].get("actions") == "write"

    def test_NINCS_iras_joga(self, utokoveto: dict) -> None:
        """Az utókövető FIGYEL és INDÍT — maga semmit nem ír."""
        assert utokoveto["permissions"].get("contents") == "read"

    def test_sajat_konkurenciacsoport_van(self, utokoveto: dict) -> None:
        """⚠️ #1319: a `release.yml` zárját TILOS elfoglalni. Egy negyven
        percig figyelő futás ott minden kiadást sorba állítana."""
        assert utokoveto["concurrency"]["group"] != "release-${{ github.repository }}"
        assert "release-" not in utokoveto["concurrency"]["group"]

    def test_az_ujabb_figyelo_leviltja_a_regit(self, utokoveto: dict) -> None:
        """Egyszerre egy utókövető figyeljen: a legfrissebb emelés számít."""
        assert utokoveto["concurrency"]["cancel-in-progress"] is True

    def test_van_idokorlatja(self, utokoveto: dict) -> None:
        """Végtelenül figyelő futás nélkül is van háló (a kiadási őr)."""
        assert utokoveto["jobs"]["utokovetes"]["timeout-minutes"] > 0

    def test_a_szkriptet_hivja(self, utokoveto: dict) -> None:
        futasok = " ".join(
            lepes.get("run", "") for lepes in utokoveto["jobs"]["utokovetes"]["steps"]
        )
        assert "kiadas_utokovetes.py" in futasok

    def test_MAGA_nem_ad_ki_semmit(self) -> None:
        """⚠️ A kiadás visszavonhatatlan. Az utókövető csak a `release.yml`-t
        indítja el — az idempotens (`ensure_release.py` előbb megnézi, van-e
        már kiadás). Két helyen kiadni két helyen lehetne duplikálni."""
        szoveg = UTOKOVETO.read_text(encoding="utf-8")
        szkript = (
            pathlib.Path(__file__).resolve().parents[1]
            / "scripts"
            / "kiadas_utokovetes.py"
        ).read_text(encoding="utf-8")
        # A magyarázó szövegben szabad EMLÍTENI a kiadót; a tiltás a
        # tényleges HÍVÁSRA szól.
        assert "gh release create" not in szoveg
        assert "python3 scripts/ensure_release.py" not in szoveg
        assert '"release", "create"' not in szkript, "az utókövető maga hoz létre kiadást"
        assert "ensure_release.py" not in szkript.replace(
            "`ensure_release.py`", ""
        ).replace("az `ensure_release.py`", ""), "az utókövető futtatja a kiadót"


class TestAMeglevoVedelemMegmarad:
    """#1338 nem ronthatja el, amit a #1319 megoldott."""

    def test_a_kiadas_konkurenciazara_ep(self, release: dict) -> None:
        assert release["concurrency"]["group"]
        assert release["concurrency"]["cancel-in-progress"] is False

    def test_a_negyedoras_or_megmarad(self) -> None:
        orjarat = yaml.safe_load(
            (_MUNKAFOLYAMATOK / "kiadasi-or.yml").read_text(encoding="utf-8")
        )
        percek = orjarat[True]["schedule"][0]["cron"].split()[0]
        assert int(percek.removeprefix("*/")) <= 15
