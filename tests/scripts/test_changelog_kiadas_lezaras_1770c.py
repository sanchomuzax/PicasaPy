"""#1770, 3. réteg — a verzióemelő PR NEVEZZE MEG a szakaszát.

## A lelet

A #1770 első két rétege a szakasz CÍMÉT (`[Kiadatlan]` → `[Nem kiadott]`) és
a kiadási jegyzet tartalékát javította. A harmadik kár viszont megmaradt:

**a `[Nem kiadott]` szakaszt a mi menetünkben SOHA nem zárja le semmi.**

Az `auto_bump.py` `zard_le_a_changelogot` lépése csak akkor futna le, ha a
verziót az automatika emelné. Nálunk viszont minden kód-PR **kézzel** emel
(ez a 2026-07-19-i felhasználói utasítás), tehát az a lépés soha nem fut.

Következmény, MÉRVE: 2026-08-31 éjjel a v0.8.156 és a v0.8.157 kiadása után
is a `[Nem kiadott]` szakaszban maradt mindkét bejegyzés — a következő
kiadás jegyzete megismételte volna őket, a napló pedig újra elvesztette
volna a verzió-hozzárendelést. Pontosan az a hibaosztály, ami a jegyet
megnyitotta, csak eggyel odébb.

## Az őr

Ha egy PR **átírja a `pyproject.toml` verziósorát X-re**, akkor a
CHANGELOG-ban legyen `## [X]` szakasz. Ez determinisztikus: a beolvadáskor
a `release.yml` pontosan ezt az X-et adja ki, tehát ekkor kell megszületnie
a szakasznak — nem valamikor később, amikor már senki nem tudja, mi
melyik verzióban ment ki.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import changelog_or as cor  # noqa: E402

_DIFF_VERZIOEMELES = """\
diff --git a/pyproject.toml b/pyproject.toml
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -10,7 +10,7 @@
-version = "0.8.157"
+version = "0.8.158"
"""

_DIFF_BEJEGYZESSEL = """\
diff --git a/CHANGELOG.md b/CHANGELOG.md
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -6,6 +6,9 @@
+- **Valami javult (#1).** Egy mondat a felhasználónak.
"""


class TestAzEmeltVerzioKiolvasasa:
    def test_a_pluszos_verziosorbol(self) -> None:
        assert cor.emelt_verzio(_DIFF_VERZIOEMELES) == "0.8.158"

    def test_verzioemeles_nelkul_nincs(self) -> None:
        assert cor.emelt_verzio(_DIFF_BEJEGYZESSEL) is None

    def test_ures_diffbol_nincs(self) -> None:
        assert cor.emelt_verzio("") is None


class TestVanEHozzaSzakasz:
    _NAPLO = (
        "# Változásnapló\n\n## [Nem kiadott]\n\n"
        "## [0.8.157] – 2026-09-01\n\n- x\n"
    )

    def test_a_megnevezett_verziot_megtalalja(self) -> None:
        assert cor.van_verzio_szakasz(self._NAPLO, "0.8.157")

    def test_a_kiadatlan_szakasz_NEM_szamit_annak(self) -> None:
        assert not cor.van_verzio_szakasz(self._NAPLO, "0.8.158")

    def test_a_reszleges_egyezes_nem_teveszt_meg(self) -> None:
        """A `0.8.15` ne találjon rá a `0.8.157`-re."""
        assert not cor.van_verzio_szakasz(self._NAPLO, "0.8.15")


class TestAKorBukik:
    @staticmethod
    def _futtato(valaszok: dict[str, str]):
        def futtat(args: list[str]) -> "subprocess.CompletedProcess[str]":
            for kulcs, kimenet in valaszok.items():
                if kulcs in " ".join(args):
                    return subprocess.CompletedProcess(args, 0, kimenet, "")
            return subprocess.CompletedProcess(args, 0, "", "")

        return futtat

    def _naplo(self, tmp_path: Path, szoveg: str) -> Path:
        ut = tmp_path / "CHANGELOG.md"
        ut.write_text(szoveg, encoding="utf-8")
        return ut

    def test_lezaratlan_szakasszal_BUKIK(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """A ma esti eset: a bejegyzés a `[Nem kiadott]`-ban maradt."""
        naplo = self._naplo(
            tmp_path,
            "# Változásnapló\n\n## [Nem kiadott]\n\n- **Valami (#1).** Szöveg.\n",
        )
        kod = cor.main(
            ["--base", "a", "--head", "b", "--changelog", str(naplo)],
            runner=self._futtato({
                "--name-only": "src/picasapy/app/qml/Main.qml\n"
                               "pyproject.toml\nCHANGELOG.md\n",
                "-- pyproject.toml": _DIFF_VERZIOEMELES,
                "-- CHANGELOG.md": _DIFF_BEJEGYZESSEL,
            }),
        )
        assert kod == 1
        kimenet = capsys.readouterr().out
        assert "::error" in kimenet, "néma bukás — a naplóban elveszne"
        assert "0.8.158" in kimenet, "a hibaüzenet mondja meg, mit írjon"

    def test_megnevezett_szakasszal_ATMEGY(self, tmp_path: Path) -> None:
        naplo = self._naplo(
            tmp_path,
            "# Változásnapló\n\n## [Nem kiadott]\n\n"
            "## [0.8.158] – 2026-09-01\n\n- **Valami (#1).** Szöveg.\n",
        )
        kod = cor.main(
            ["--base", "a", "--head", "b", "--changelog", str(naplo)],
            runner=self._futtato({
                "--name-only": "src/picasapy/app/qml/Main.qml\n"
                               "pyproject.toml\nCHANGELOG.md\n",
                "-- pyproject.toml": _DIFF_VERZIOEMELES,
                "-- CHANGELOG.md": _DIFF_BEJEGYZESSEL,
            }),
        )
        assert kod == 0

    def test_verzioemeles_nelkuli_PR_t_nem_bant(self, tmp_path: Path) -> None:
        """Aki nem emel verziót, arra ez a szabály nem vonatkozik."""
        naplo = self._naplo(
            tmp_path,
            "# Változásnapló\n\n## [Nem kiadott]\n\n- **Valami (#1).** Szöveg.\n",
        )
        kod = cor.main(
            ["--base", "a", "--head", "b", "--changelog", str(naplo)],
            runner=self._futtato({
                "--name-only": "src/picasapy/app/qml/Main.qml\nCHANGELOG.md\n",
                "-- CHANGELOG.md": _DIFF_BEJEGYZESSEL,
            }),
        )
        assert kod == 0

    def test_a_csak_verziosort_iro_automatika_PR_je_atmegy(
        self, tmp_path: Path
    ) -> None:
        """Az `auto_bump` saját PR-je nem hoz emberi mondatot — nem is kell."""
        naplo = self._naplo(tmp_path, "# Változásnapló\n\n## [Nem kiadott]\n")
        kod = cor.main(
            ["--base", "a", "--head", "b", "--changelog", str(naplo)],
            runner=self._futtato({
                "--name-only": "pyproject.toml\n",
                "-- pyproject.toml": _DIFF_VERZIOEMELES,
            }),
        )
        assert kod == 0


class TestAzOrnekVanFoga:
    def test_a_mai_CHANGELOG_es_a_mai_verzio_egyezik(self) -> None:
        """Élő ellenőrzés a repón: a kiadott verziónak van szakasza.

        Ez az a mérés, ami hat napig némán hamis volt. Ha valaki verziót
        emel szakasz nélkül, ez bukik — akkor is, ha a PR-őr valamiért
        nem futott le."""
        gyoker = Path(__file__).resolve().parents[2]
        verzio = next(
            s.split('"')[1]
            for s in (gyoker / "pyproject.toml").read_text(
                encoding="utf-8"
            ).splitlines()
            if s.startswith("version")
        )
        naplo = (gyoker / "CHANGELOG.md").read_text(encoding="utf-8")
        assert cor.van_verzio_szakasz(naplo, verzio), (
            f"a pyproject verziója {verzio}, de a CHANGELOG-ban nincs "
            f"`## [{verzio}]` szakasz — a kiadási jegyzet nem találja meg "
            "a hozzá írt mondatokat (#1770)"
        )
