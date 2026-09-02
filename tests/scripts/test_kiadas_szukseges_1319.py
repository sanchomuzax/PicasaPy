"""A feltételes verzióemelés döntése (#1319).

A #1318 azt mutatta meg, hogy a kiadási automatika VAKON emel: a main minden
pushja után emelt, ha a jelenlegi verzióhoz már volt kiadás — akkor is, ha a
beolvadt munka mindössze két `docs/specs/` fájl volt. A felesleges
verzióemelő PR aztán ott ült, mert kiadni sem volt mit.

A döntés SZÁNDÉKOSAN szkriptben él, nem a YAML-ben: a munkafolyamat-fájlba
írt shell-logikára nem lehet állítást írni (#896 tanulsága, ld.
`ensure_release.py`).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import kiadas_szukseges as ksz  # noqa: E402


def _futtato(kimenet: str, kod: int = 0):
    """Rögzített kimenetű `git`-helyettes — a valódi repó nélkül is mérhető."""

    def futtat(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, kod, kimenet, "")

    return futtat


class TestKiadasraErdemes:
    def test_a_1318_esete_csak_dokumentacio(self) -> None:
        """A #1318 valódi bemenete: két specifikációs fájl, semmi más."""
        assert not ksz.kiadasra_erdemes(
            [
                "docs/specs/00-index.md",
                "docs/specs/picasa-konyvtar-eszkoztar-viselkedes.md",
            ]
        )

    def test_forraskod_valtozas_kiadhato(self) -> None:
        assert ksz.kiadasra_erdemes(["src/picasapy/app/controller.py"])

    def test_kod_es_dokumentacio_egyutt_kiadhato(self) -> None:
        """Minden kódos PR hoz CHANGELOG-ot is — a kód dönt, nem a `.md`."""
        assert ksz.kiadasra_erdemes(["CHANGELOG.md", "src/picasapy/ini/writer.py"])

    @pytest.mark.parametrize(
        "fajl",
        [
            "tests/app/test_qml_functional.py",
            ".github/workflows/release.yml",
            "scripts/ensure_release.py",
            "docs/decisions/0012-valami.md",
            "README.md",
            ".claude/settings.json",
            "research/testdata/jegyzet.txt",
            # #1938: a `tools/` a golden-kit generátorok és mérőszkriptek
            # helye. A wheel CSAK a `src/` alól csomagol
            # (`[tool.setuptools.packages.find] where = ["src"]`), tehát
            # ezek ugyanúgy nem jutnak el a felhasználóhoz, mint a
            # `scripts/`. A lista mégis kihagyta őket, ezért a
            # CHANGELOG-őr egy kutatói eszköz bővítésére felhasználói
            # mondatot követelt — olyat, ami a naplóban hazugság lenne.
            "tools/golden/make_param_sweep.py",
            "tools/benchmarks/bench_image_libs.py",
        ],
    )
    def test_belso_karbantartas_nem_kiadhato(self, fajl: str) -> None:
        assert not ksz.kiadasra_erdemes([fajl])

    @pytest.mark.parametrize(
        "fajl",
        [
            "pyproject.toml",
            "src/picasapy/render/vivid.py",
            "packaging/qt-runtime-deps.txt",
            "src/picasapy/app/qml/Main.qml",
        ],
    )
    def test_a_programot_erinto_fajlok_kiadhatok(self, fajl: str) -> None:
        assert ksz.kiadasra_erdemes([fajl])

    def test_ismeretlen_utvonal_INKABB_kiadhato(self) -> None:
        """Alapértelmezés: ha nem ismerjük fel, kiadható.

        A tévedés két iránya nem egyforma súlyú: egy felesleges patch-kiadás
        olcsó, egy elmaradt kiadás viszont némán tartja vissza a javítást a
        felhasználótól."""
        assert ksz.kiadasra_erdemes(["valami/uj/mappa/fajl.py"])

    def test_ures_valtozas_nem_kiadhato(self) -> None:
        assert not ksz.kiadasra_erdemes([])

    def test_erdemi_fajlok_a_naplohoz(self) -> None:
        """A futás naplója mondja meg, MITŐL lett kiadható — enélkül a
        döntés visszakereshetetlen."""
        assert ksz.erdemi_fajlok(["README.md", "src/a.py", "docs/b.md"]) == ("src/a.py",)


class TestValtozasokAKetRefKozott:
    def test_a_git_diffet_kerdezi(self) -> None:
        hivasok: list[list[str]] = []

        def futtat(args: list[str]) -> subprocess.CompletedProcess[str]:
            hivasok.append(args)
            return subprocess.CompletedProcess(args, 0, "docs/a.md\nsrc/b.py\n", "")

        assert ksz.valtozott_fajlok("v0.8.69", "HEAD", runner=futtat) == (
            "docs/a.md",
            "src/b.py",
        )
        assert hivasok == [["git", "diff", "--name-only", "v0.8.69", "HEAD"]]

    def test_hianyzo_cimke_eseten_INKABB_kiadunk(self) -> None:
        """Ha az alap-ref nem létezik (törölt/hiányzó címke), nem tudunk
        dönteni — ilyenkor a kiadás felé tévedünk."""
        hibas = _futtato("", kod=128)
        assert ksz.valtozott_fajlok("v0.0.0", "HEAD", runner=hibas) is None
        assert ksz.kiadasra_erdemes(None)


class TestParancssor:
    def test_a_1318_esete_nemet_ir_ki(self, capsys: pytest.CaptureFixture[str]) -> None:
        kod = ksz.main(
            ["--base", "v0.8.69", "--head", "HEAD"],
            runner=_futtato("docs/specs/00-index.md\n"),
        )
        assert kod == 0
        assert capsys.readouterr().out.splitlines()[0] == "nem"

    def test_kodos_valtozas_igent_ir_ki(self, capsys: pytest.CaptureFixture[str]) -> None:
        kod = ksz.main(
            ["--base", "v0.8.69", "--head", "HEAD"],
            runner=_futtato("src/picasapy/app/controller.py\n"),
        )
        assert kod == 0
        assert capsys.readouterr().out.splitlines()[0] == "igen"
